"""Run ARE-BENCH-002 with unconditional second-engine execution for B/C/D."""
from __future__ import annotations
import argparse
import csv
import json
import platform
import subprocess
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


def _certify_engine_result(original, status, model, proof) -> bool:
    if status == "SAT":
        return model is not None and verify_sat(original, model)
    if status == "UNSAT":
        return verify_unsat_tree(original, proof)
    return False


def run_configuration(name: str, original, n_vars: int, total_budget: int = TOTAL_BUDGET) -> dict:
    """Run one benchmark configuration.

    For B/C/D the second (JW) engine is always started after the first engine
    terminates, whether the first engine returns SAT, UNSAT, or UNKNOWN. Each
    engine receives at most half of the aggregate search-node budget.
    """
    config_started = time.perf_counter()
    engine_budget = total_budget // 2
    certificate_budget = max(CERTIFICATE_BUDGET, total_budget * 20)

    if name == "A":
        engine, status, model, proof, engine_elapsed = _run_engine(
            original, n_vars, "frequency", total_budget)
        certified = _certify_engine_result(original, status, model, proof)
        stats = _merge_stats(engine.stats)
        result = _result(name, status if certified else "UNKNOWN", certified,
                         model if certified else None, stats,
                         time.perf_counter() - config_started, 0, 0,
                         "single frequency engine")
        result.update({
            "first_engine_status": status,
            "first_engine_certified": certified,
            "first_engine_nodes": engine.stats.nodes,
            "first_engine_elapsed_seconds": round(engine_elapsed, 6),
            "second_engine_ran": False,
            "second_engine_status": "NOT_RUN",
            "second_engine_certified": False,
            "second_engine_nodes": 0,
            "second_engine_elapsed_seconds": 0.0,
            "engine_disagreement": False,
            "learned_received_immediate": 0,
            "learned_received_deferred": 0,
        })
        return result

    if name not in {"B", "C", "D"}:
        raise ValueError(f"Unknown configuration: {name}")

    # Stage 1: frequency heuristic. Keep its learned clauses even if it solves.
    shared = KnowledgeBase()
    first, s1, m1, p1, first_elapsed = _run_engine(
        original, n_vars, "frequency", engine_budget, knowledge=shared)
    first_ok = _certify_engine_result(original, s1, m1, p1)

    # Export only nogoods whose certificates verify against the original CNF
    # under the negation of the learned clause.
    verified = [
        clause for clause in shared.clauses
        if verify_nogood_certificate(original, clause, shared.certificates[clause])
    ]

    if name == "B":
        receiving_kb, deferred, adaptive = KnowledgeBase(), [], False
        immediate_count, deferred_count = 0, 0
    elif name == "C":
        receiving_kb = KnowledgeBase()
        for clause in verified:
            receiving_kb.add(clause, shared.certificates[clause])
        deferred, adaptive = [], False
        immediate_count, deferred_count = len(verified), 0
    else:  # D
        ranked = sorted(verified, key=lambda clause: (len(clause), clause))
        immediate_n = int(len(ranked) * ADAPTIVE_IMMEDIATE_FRACTION)
        immediate, deferred = ranked[:immediate_n], ranked[immediate_n:]
        receiving_kb = KnowledgeBase()
        for clause in immediate:
            receiving_kb.add(clause, shared.certificates[clause])
        adaptive = True
        immediate_count, deferred_count = len(immediate), len(deferred)

    # Stage 2 is unconditional: JW runs even if stage 1 already solved the CNF.
    second, s2, m2, p2, second_elapsed = _run_engine(
        original, n_vars, "jw", engine_budget, knowledge=receiving_kb,
        deferred=deferred, adaptive=adaptive)
    second_ok = False
    verifier_nodes = 0
    if s2 == "SAT":
        second_ok = m2 is not None and verify_sat(original, m2)
    elif s2 == "UNSAT":
        # The stage-2 proof may depend on imported clauses; verify independently.
        verifier, verifier_status, _, verifier_proof, _ = _run_engine(
            original, n_vars, "frequency", certificate_budget)
        verifier_nodes = verifier.stats.nodes
        second_ok = (
            verifier_status == "UNSAT"
            and verify_unsat_tree(original, verifier_proof)
        )

    stats = _merge_stats(first.stats, second.stats)
    stats["learned_generated"] = first.stats.learned_generated + second.stats.learned_generated
    stats["learned_received"] = immediate_count + deferred_count
    stats["learned_certificates_verified"] = len(verified)

    disagreement = first_ok and second_ok and s1 != s2
    if disagreement:
        final, certified, chosen_model = "UNKNOWN", False, None
        outcome_note = "ERROR: independently certified engines disagree"
    elif first_ok:
        final, certified = s1, True
        chosen_model = m1 if s1 == "SAT" else None
        outcome_note = "overall result certified by first engine"
    elif second_ok:
        final, certified = s2, True
        chosen_model = m2 if s2 == "SAT" else None
        outcome_note = "overall result certified by second engine"
    else:
        final, certified, chosen_model = "UNKNOWN", False, None
        outcome_note = "neither engine produced a verified result"

    result = _result(
        name, final, certified, chosen_model, stats,
        time.perf_counter() - config_started, verifier_nodes, len(verified),
        f"frequency -> jw; exchange={name}; first={s1}; second={s2}; {outcome_note}",
    )
    result.update({
        "first_engine_status": s1,
        "first_engine_certified": first_ok,
        "first_engine_nodes": first.stats.nodes,
        "first_engine_elapsed_seconds": round(first_elapsed, 6),
        "second_engine_ran": True,
        "second_engine_status": s2,
        "second_engine_certified": second_ok,
        "second_engine_nodes": second.stats.nodes,
        "second_engine_elapsed_seconds": round(second_elapsed, 6),
        "engine_disagreement": disagreement,
        "learned_received_immediate": immediate_count,
        "learned_received_deferred": deferred_count,
    })
    return result




def _git_metadata(exclude_paths: list[Path] | None = None) -> dict:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        status_command = ["git", "status", "--porcelain", "--untracked-files=all", "--", "."]
        for path in exclude_paths or []:
            try:
                relative = path.resolve().relative_to(Path.cwd().resolve())
            except ValueError:
                continue
            status_command.append(f":(exclude){relative.as_posix()}")
        dirty = bool(subprocess.run(
            status_command, capture_output=True, text=True, check=True
        ).stdout.strip())
        return {"git_head_detected": head, "git_dirty_detected": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"git_head_detected": None, "git_dirty_detected": None}


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temporary.replace(path)


def _write_csv_atomic(path: Path, fields: list[str], rows: list[dict]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temporary.replace(path)


def _load_checkpoint(path: Path) -> list[dict]:
    if not path.exists():
        return []
    # A process/power failure may leave only the final append incomplete.
    # Discard that unterminated tail; complete JSONL records remain authoritative.
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        last_newline = raw.rfind(b"\n")
        with path.open("r+b") as stream:
            stream.truncate(last_newline + 1 if last_newline >= 0 else 0)
            stream.flush()
            import os
            os.fsync(stream.fileno())
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Checkpoint JSONL corrupt at line {line_number}; preserve the file "
                    "and inspect it before resuming."
                ) from exc
            if not isinstance(row, dict):
                raise ValueError(f"Checkpoint line {line_number} is not a JSON object")
            rows.append(row)
    return rows


def _write_manifest(path: Path, manifest: dict) -> None:
    manifest["updated_at_utc"] = _utc_now()
    _atomic_write_text(path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ARE-BENCH-002 with both engines always executed and durable checkpoints."
    )
    parser.add_argument("--output", type=Path, default=Path("results/ARE-BENCH-002.csv"))
    parser.add_argument("--limit-per-size", type=int, default=INSTANCES_PER_SIZE,
                        help="30 for the full protocol; smaller values are pilots.")
    parser.add_argument("--configs", default="A,B,C,D")
    parser.add_argument("--git-commit", required=True,
                        help="Exact source commit SHA used for this run.")
    parser.add_argument("--git-dirty", action="store_true",
                        help="Mark the source tree as modified; run will not be confirmatory.")
    parser.add_argument("--sizes", type=int, nargs="+", choices=INSTANCE_COUNTS,
                        default=list(INSTANCE_COUNTS))
    parser.add_argument("--node-budget", type=int, default=TOTAL_BUDGET)
    parser.add_argument("--resume", action="store_true",
                        help="Resume from the matching .checkpoint.jsonl file.")
    args = parser.parse_args()
    if args.node_budget < 2:
        parser.error("--node-budget must be at least 2")
    if not 1 <= args.limit_per_size <= INSTANCES_PER_SIZE:
        parser.error("--limit-per-size must be between 1 and 30")
    configs = [x.strip() for x in args.configs.split(",") if x.strip()]
    if not configs or len(set(configs)) != len(configs) or any(
        x not in {"A", "B", "C", "D"} for x in configs
    ):
        parser.error("--configs must contain unique values from A,B,C,D")
    if not args.git_commit or args.git_commit == "UNRECORDED":
        parser.error("--git-commit must be the exact source commit SHA")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output.with_suffix(".manifest.json")
    checkpoint_path = args.output.with_suffix(".checkpoint.jsonl")
    log_path = args.output.with_suffix(".log")
    fields = ["n_vars", "instance_index", "seed", "formula_sha256", "configuration",
              "status", "certified", "decision_nodes", "propagations", "conflicts",
              "learned_generated", "learned_received", "learned_relevant",
              "learned_certificates_verified", "deferred_activated", "max_active_clauses",
              "elapsed_seconds", "certificate_verifier_nodes", "first_engine_status", "first_engine_certified",
              "first_engine_nodes", "first_engine_elapsed_seconds", "second_engine_ran",
              "second_engine_status", "second_engine_certified", "second_engine_nodes",
              "second_engine_elapsed_seconds", "engine_disagreement",
              "learned_received_immediate", "learned_received_deferred", "note"]
    sizes = list(args.sizes)
    expected = [
        (n, i, config)
        for n in sizes for i in range(args.limit_per_size) for config in configs
    ]
    output_artifacts = [args.output, manifest_path, checkpoint_path, log_path]
    output_artifacts.extend(path.with_name(path.name + ".tmp") for path in list(output_artifacts))
    git_info = _git_metadata(output_artifacts)
    if git_info["git_head_detected"] is not None and git_info["git_head_detected"] != args.git_commit:
        parser.error("--git-commit does not match the current Git HEAD")
    detected_dirty = git_info["git_dirty_detected"]
    effective_dirty = bool(args.git_dirty or detected_dirty is True)
    run_settings = {
        "protocol": "ARE-BENCH-002",
        "protocol_version": "1.0",
        "second_engine_policy": "always-start-after-stage-1-terminates-or-exhausts-budget",
        "git_commit": args.git_commit,
        "git_dirty": effective_dirty,
        **git_info,
        "configs": configs,
        "sizes": sizes,
        "instances_per_size": args.limit_per_size,
        "total_budget_per_instance": args.node_budget,
        "engine_budget": args.node_budget // 2,
        "certificate_budget_separate": max(CERTIFICATE_BUDGET, args.node_budget * 20),
        "adaptive_immediate_fraction": ADAPTIVE_IMMEDIATE_FRACTION,
    }
    full_shape = (
        sizes == list(INSTANCE_COUNTS)
        and args.limit_per_size == INSTANCES_PER_SIZE
        and configs == ["A", "B", "C", "D"]
        and args.node_budget == TOTAL_BUDGET
    )
    confirmatory_eligible = (
        full_shape and not effective_dirty
        and git_info["git_head_detected"] == args.git_commit
        and git_info["git_dirty_detected"] is False
    )
    if args.resume:
        if not checkpoint_path.exists() or not manifest_path.exists():
            parser.error("--resume requires an existing checkpoint and manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key, value in run_settings.items():
            if manifest.get(key) != value:
                parser.error(f"Cannot resume: setting {key!r} differs from saved run")
        rows = _load_checkpoint(checkpoint_path)
        if len(rows) > len(expected):
            parser.error("Checkpoint contains more rows than this run expects")
        seen = set()
        for row in rows:
            key = (int(row["n_vars"]), int(row["instance_index"]), row["configuration"])
            if key in seen or key not in expected:
                parser.error(f"Checkpoint contains duplicate or unexpected result key: {key}")
            n, i = key[0], key[1]
            seed, formula = generate_benchmark_instance(n, i)
            if row.get("seed") != seed or row.get("formula_sha256") != formula_sha256(n, formula):
                parser.error(f"Checkpoint instance identity mismatch for {key}")
            if row.get("status") not in {"SAT", "UNSAT", "UNKNOWN"}:
                parser.error(f"Checkpoint has invalid status for {key}")
            if bool(row.get("certified")) != (row.get("status") in {"SAT", "UNSAT"}):
                parser.error(f"Checkpoint certification/status mismatch for {key}")
            if key[2] in {"B", "C", "D"}:
                if row.get("second_engine_ran") is not True:
                    parser.error(f"Checkpoint row did not execute the second engine: {key}")
                if row.get("first_engine_status") not in {"SAT", "UNSAT", "UNKNOWN"}:
                    parser.error(f"Checkpoint has invalid first-engine status for {key}")
                if row.get("second_engine_status") not in {"SAT", "UNSAT", "UNKNOWN"}:
                    parser.error(f"Checkpoint has invalid second-engine status for {key}")
            elif row.get("second_engine_ran") is not False:
                parser.error(f"Single-engine configuration unexpectedly ran a second engine: {key}")
            seen.add(key)
        completed = seen
        manifest["resumed_at_utc"] = _utc_now()
        manifest["resume_count"] = int(manifest.get("resume_count", 0)) + 1
        manifest.setdefault("command_history", []).append({
            "at_utc": _utc_now(),
            "command": [sys.executable, "-m", "are.benchmark", *sys.argv[1:]],
        })
    else:
        if checkpoint_path.exists() or manifest_path.exists() or args.output.exists():
            parser.error("Output, manifest, or checkpoint already exists; use --resume or a new --output")
        rows = []
        completed = set()
        manifest = {
            **run_settings,
            "status": "running",
            "classification": "confirmatory-candidate" if confirmatory_eligible else "pilot/non-confirmatory",
            "confirmatory_eligible": confirmatory_eligible,
            "started_at_utc": _utc_now(),
            "command": [sys.executable, "-m", "are.benchmark", *sys.argv[1:]],
            "command_history": [{
                "at_utc": _utc_now(),
                "command": [sys.executable, "-m", "are.benchmark", *sys.argv[1:]],
            }],
            "python_version": sys.version,
            "platform": platform.platform(),
            "expected_result_rows": len(expected),
            "completed_result_rows": 0,
            "total_instances": len(sizes) * args.limit_per_size,
            "checkpoint_file": str(checkpoint_path),
            "output_csv": str(args.output),
            "log_file": str(log_path),
            "resume_count": 0,
        }
        _write_manifest(manifest_path, manifest)
        _write_csv_atomic(args.output, fields, rows)

    # Rebuild the human-readable CSV from the durable JSONL checkpoint on resume.
    _write_csv_atomic(args.output, fields, rows)
    _write_manifest(manifest_path, manifest)
    started = time.perf_counter()
    for n, i, config in expected:
        if (n, i, config) in completed:
            continue
        seed, cnf = generate_benchmark_instance(n, i)
        digest = formula_sha256(n, cnf)
        result = run_configuration(config, cnf, n, total_budget=args.node_budget)
        row = {"n_vars": n, "instance_index": i, "seed": seed,
               "formula_sha256": digest, **result}
        # JSONL is the durable source of truth. Flush it before updating CSV/manifest.
        with checkpoint_path.open("a", encoding="utf-8", newline="") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
            import os
            os.fsync(stream.fileno())
        rows.append(row)
        completed.add((n, i, config))
        _write_csv_atomic(args.output, fields, rows)
        manifest["completed_result_rows"] = len(rows)
        manifest["last_completed"] = {
            "n_vars": n, "instance_index": i, "configuration": config,
            "status": result["status"],
        }
        manifest["elapsed_seconds_this_session"] = round(time.perf_counter() - started, 3)
        _write_manifest(manifest_path, manifest)
        log_line = (
            f"{_utc_now()} n={n} i={i:02d} {config}: {result['status']} "
            f"nodes={result['decision_nodes']} ({len(rows)}/{len(expected)})\n"
        )
        with log_path.open("a", encoding="utf-8") as log_stream:
            log_stream.write(log_line)
            log_stream.flush()
            import os
            os.fsync(log_stream.fileno())
        print(log_line.rstrip(), flush=True)

    manifest["status"] = "complete"
    manifest["finished_at_utc"] = _utc_now()
    manifest["completed_result_rows"] = len(rows)
    manifest["elapsed_seconds_this_session"] = round(time.perf_counter() - started, 3)
    manifest["classification"] = (
        "confirmatory-run-complete" if confirmatory_eligible else "pilot/non-confirmatory"
    )
    _write_csv_atomic(args.output, fields, rows)
    _write_manifest(manifest_path, manifest)
    print(f"Completed {len(rows)} result rows. Wrote {args.output}, "
          f"{manifest_path}, and {checkpoint_path}")


if __name__ == "__main__":
    main()
