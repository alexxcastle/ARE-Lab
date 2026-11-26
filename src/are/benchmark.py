"""Run the frozen ARE-BENCH-001 configurations A/B/C/D."""
from __future__ import annotations
import argparse
import csv
import json
import platform
import sys
import time
from pathlib import Path

from .instances import INSTANCE_COUNTS, INSTANCES_PER_SIZE, generate_benchmark_instance, formula_sha256
from .solver import DPLLEngine, KnowledgeBase, SearchStats, verify_nogood_certificate, verify_sat, verify_unsat_tree

TOTAL_BUDGET = 100_000
CERTIFICATE_BUDGET = 2_000_000
ADAPTIVE_IMMEDIATE_FRACTION = 0.25


def _merge_stats(*stats: SearchStats) -> dict:
    fields = ("nodes", "propagations", "conflicts", "learned_generated",
              "learned_received", "learned_used", "learned_relevant", "deferred_activated")
    out = {name: sum(getattr(s, name) for s in stats) for name in fields}
    out["max_active_clauses"] = max((s.max_active_clauses for s in stats), default=0)
    return out


def _run_engine(original, n_vars, heuristic, budget, knowledge=None, deferred=None, adaptive=False):
    engine = DPLLEngine(original, n_vars, heuristic=heuristic, node_budget=budget,
                        knowledge=knowledge, deferred=deferred, adaptive_deferred=adaptive)
    started = time.perf_counter()
    status, model, proof = engine.solve()
    return engine, status, model, proof, time.perf_counter() - started


def _result(name, status, certified, model, stats, elapsed, verifier_nodes, exported, note):
    return {
        "configuration": name, "status": status, "certified": bool(certified),
        "decision_nodes": stats.get("nodes", 0), "propagations": stats.get("propagations", 0),
        "conflicts": stats.get("conflicts", 0), "learned_generated": stats.get("learned_generated", 0),
        "learned_received": stats.get("learned_received", 0),
        "learned_relevant": stats.get("learned_relevant", 0),
        "learned_certificates_verified": stats.get("learned_certificates_verified", exported),
        "deferred_activated": stats.get("deferred_activated", 0),
        "max_active_clauses": stats.get("max_active_clauses", 0),
        "elapsed_seconds": round(elapsed, 6),
        "certificate_verifier_nodes": verifier_nodes, "note": note,
    }


def run_configuration(name: str, original, n_vars: int, total_budget: int = TOTAL_BUDGET) -> dict:
    config_started = time.perf_counter()
    engine_budget = total_budget // 2
    certificate_budget = max(CERTIFICATE_BUDGET, total_budget * 20)

    if name == "A":
        engine, status, model, proof, _ = _run_engine(original, n_vars, "frequency", total_budget)
        stats = _merge_stats(engine.stats)
        certified = (model is not None and verify_sat(original, model)) if status == "SAT" else (
            verify_unsat_tree(original, proof) if status == "UNSAT" else False)
        return _result(name, status if certified else "UNKNOWN", certified, model, stats,
                       time.perf_counter() - config_started, 0, 0, "single frequency engine")

    # Deterministic two-stage schedule: frequency first, Jeroslow-Wang second.
    shared = KnowledgeBase()
    first, s1, m1, p1, _ = _run_engine(original, n_vars, "frequency", engine_budget, knowledge=shared)
    if s1 == "SAT":
        ok = m1 is not None and verify_sat(original, m1)
        return _result(name, "SAT" if ok else "UNKNOWN", ok, m1, _merge_stats(first.stats),
                       time.perf_counter() - config_started, 0, 0, "first engine solved")
    if s1 == "UNSAT":
        ok = verify_unsat_tree(original, p1)
        return _result(name, "UNSAT" if ok else "UNKNOWN", ok, None, _merge_stats(first.stats),
                       time.perf_counter() - config_started, 0, 0, "first engine refutation")

    # A clause is exportable only if its certificate proves original AND
    # negation(clause) UNSAT. No heuristic score can bypass this check.
    verified = [c for c in shared.clauses
                if verify_nogood_certificate(original, c, shared.certificates[c])]

    if name == "B":
        receiving_kb, deferred, adaptive = KnowledgeBase(), [], False
    elif name == "C":
        receiving_kb = KnowledgeBase()
        for c in verified:
            receiving_kb.add(c, shared.certificates[c])
        deferred, adaptive = [], False
    elif name == "D":
        ranked = sorted(verified, key=lambda c: (len(c), c))
        immediate_n = int(len(ranked) * ADAPTIVE_IMMEDIATE_FRACTION)
        immediate, deferred = ranked[:immediate_n], ranked[immediate_n:]
        receiving_kb = KnowledgeBase()
        for c in immediate:
            receiving_kb.add(c, shared.certificates[c])
        adaptive = True
    else:
        raise ValueError(f"Unknown configuration: {name}")

    second, s2, m2, p2, _ = _run_engine(
        original, n_vars, "jw", engine_budget, knowledge=receiving_kb,
        deferred=deferred, adaptive=adaptive)
    stats = _merge_stats(first.stats, second.stats)
    stats["learned_generated"] = first.stats.learned_generated + second.stats.learned_generated
    stats["learned_received"] = second.stats.learned_received
    stats["learned_certificates_verified"] = len(verified)

    verifier_nodes = 0
    if s2 == "SAT":
        ok = m2 is not None and verify_sat(original, m2)
        final = "SAT" if ok else "UNKNOWN"
    elif s2 == "UNSAT":
        # Independent proof run on original CNF; its work is reported separately.
        verifier, vs, _, vp, _ = _run_engine(
            original, n_vars, "frequency", certificate_budget)
        verifier_nodes = verifier.stats.nodes
        ok = vs == "UNSAT" and verify_unsat_tree(original, vp)
        final = "UNSAT" if ok else "UNKNOWN"
    else:
        final, ok = "UNKNOWN", False

    return _result(name, final, ok, m2 if final == "SAT" else None, stats,
                   time.perf_counter() - config_started, verifier_nodes, len(verified),
                   f"two-stage frequency -> jw; exchange={name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/ARE-BENCH-001.csv"))
    parser.add_argument("--limit-per-size", type=int, default=INSTANCES_PER_SIZE,
                        help="30 for confirmatory run; smaller values are pilots.")
    parser.add_argument("--configs", default="A,B,C,D")
    parser.add_argument("--git-commit", default="UNRECORDED")
    parser.add_argument("--sizes", type=int, nargs="+", choices=INSTANCE_COUNTS,
                        default=list(INSTANCE_COUNTS))
    parser.add_argument("--node-budget", type=int, default=TOTAL_BUDGET,
                        help="100000 for frozen protocol; other values are pilots.")
    args = parser.parse_args()
    if args.node_budget < 2:
        parser.error("--node-budget must be at least 2")
    if not 1 <= args.limit_per_size <= INSTANCES_PER_SIZE:
        parser.error("--limit-per-size must be between 1 and 30")
    configs = [x.strip() for x in args.configs.split(",") if x.strip()]
    if not configs or any(x not in {"A", "B", "C", "D"} for x in configs):
        parser.error("--configs must contain only A,B,C,D")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["n_vars", "instance_index", "seed", "formula_sha256", "configuration",
              "status", "certified", "decision_nodes", "propagations", "conflicts",
              "learned_generated", "learned_received", "learned_relevant",
              "learned_certificates_verified", "deferred_activated", "max_active_clauses",
              "elapsed_seconds", "certificate_verifier_nodes", "note"]
    rows, started = [], time.perf_counter()
    for n in args.sizes:
        for i in range(args.limit_per_size):
            seed, cnf = generate_benchmark_instance(n, i)
            digest = formula_sha256(n, cnf)
            for config in configs:
                result = run_configuration(config, cnf, n, total_budget=args.node_budget)
                rows.append({"n_vars": n, "instance_index": i, "seed": seed,
                             "formula_sha256": digest, **result})
                print(f"n={n} i={i:02d} {config}: {result['status']} "
                      f"nodes={result['decision_nodes']}", flush=True)

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "protocol": "ARE-BENCH-001", "protocol_version": "1.0",
        "git_commit": args.git_commit, "python_version": sys.version,
        "platform": platform.platform(), "configs": configs,
        "instances_per_size": args.limit_per_size, "sizes": args.sizes,
        "total_instances": len(args.sizes) * args.limit_per_size,
        "total_budget_per_instance": args.node_budget,
        "engine_budget": args.node_budget // 2,
        "certificate_budget_separate": max(CERTIFICATE_BUDGET, args.node_budget * 20),
        "adaptive_immediate_fraction": ADAPTIVE_IMMEDIATE_FRACTION,
        "output_csv": str(args.output), "elapsed_seconds": round(time.perf_counter() - started, 3),
        "status": "pilot" if (args.limit_per_size < INSTANCES_PER_SIZE or
                  args.node_budget != TOTAL_BUDGET or args.sizes != list(INSTANCE_COUNTS))
                  else "full-protocol-run",
    }
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} and {manifest_path}")


if __name__ == "__main__":
    main()
