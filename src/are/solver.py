"""Proof-aware DPLL prototype used by ARE-BENCH-001.

A learned nogood is exported only when its entire decision subtree has been
proved UNSAT. This is a research prototype, not an industrial SAT solver.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

Clause = tuple[int, ...]
CNF = tuple[Clause, ...]


def normalize_clause(clause: Iterable[int]) -> Clause:
    lits = set(clause)
    if any(-lit in lits for lit in lits):
        return tuple()
    return tuple(sorted(lits, key=lambda x: (abs(x), x < 0)))


def clause_status(clause: Clause, assignment: dict[int, bool]):
    remaining = []
    for lit in clause:
        var = abs(lit)
        if var not in assignment:
            remaining.append(lit)
        elif assignment[var] == (lit > 0):
            return True, []
    return False, remaining


def unit_propagate(clauses: list[Clause], assignment: dict[int, bool]):
    """Queue-based unit propagation with literal occurrence lists."""
    current = dict(assignment)
    remaining = [set() for _ in clauses]
    satisfied = [False] * len(clauses)
    occurrences: dict[int, list[int]] = {}
    queue: list[int] = []
    units: list[Clause] = []
    for i, clause in enumerate(clauses):
        rem, sat = set(), False
        for lit in clause:
            var = abs(lit)
            if var in current:
                if current[var] == (lit > 0):
                    sat = True
                    break
            else:
                rem.add(lit)
        if sat:
            satisfied[i] = True
            continue
        if not rem:
            return current, True, 0, units
        remaining[i] = rem
        for lit in rem:
            occurrences.setdefault(lit, []).append(i)
        if len(rem) == 1:
            unit = next(iter(rem))
            queue.append(unit)
            units.append((unit,))
    propagated, cursor = 0, 0
    while cursor < len(queue):
        lit = queue[cursor]
        cursor += 1
        var, value = abs(lit), lit > 0
        if var in current:
            if current[var] != value:
                return current, True, propagated, units
            continue
        current[var] = value
        propagated += 1
        for i in occurrences.get(lit, ()):
            satisfied[i] = True
        for i in occurrences.get(-lit, ()):
            if satisfied[i]:
                continue
            remaining[i].discard(-lit)
            if not remaining[i]:
                return current, True, propagated, units
            if len(remaining[i]) == 1:
                unit = next(iter(remaining[i]))
                queue.append(unit)
                units.append((unit,))
    return current, False, propagated, units


def choose_variable(clauses: list[Clause], assignment: dict[int, bool], heuristic: str) -> int:
    scores: dict[int, float] = {}
    for clause in clauses:
        sat, rem = clause_status(clause, assignment)
        if sat:
            continue
        weight = 2.0 ** (-len(rem)) if heuristic == "jw" else 1.0
        for lit in rem:
            scores[abs(lit)] = scores.get(abs(lit), 0.0) + weight
    if not scores:
        raise RuntimeError("No unresolved variable in a nonterminal state")
    return max(sorted(scores), key=lambda v: scores[v])


def all_satisfied(clauses: list[Clause], assignment: dict[int, bool]) -> bool:
    return all(clause_status(c, assignment)[0] for c in clauses)


@dataclass
class SearchStats:
    nodes: int = 0
    propagations: int = 0
    conflicts: int = 0
    learned_generated: int = 0
    learned_received: int = 0
    learned_used: int = 0
    learned_relevant: int = 0
    deferred_activated: int = 0
    max_active_clauses: int = 0


@dataclass
class KnowledgeBase:
    clauses: list[Clause] = field(default_factory=list)
    seen: set[Clause] = field(default_factory=set)
    certificates: dict[Clause, dict] = field(default_factory=dict)

    def add(self, clause: Clause, certificate: dict) -> bool:
        if clause in self.seen:
            return False
        self.seen.add(clause)
        self.clauses.append(clause)
        self.certificates[clause] = certificate
        return True


class DPLLEngine:
    def __init__(self, original: CNF, n_vars: int, heuristic: str = "frequency",
                 node_budget: int = 100_000, knowledge: KnowledgeBase | None = None,
                 deferred: list[Clause] | None = None, adaptive_deferred: bool = False):
        self.original = list(original)
        self.n_vars = n_vars
        self.heuristic = heuristic
        self.node_budget = node_budget
        self.knowledge = knowledge or KnowledgeBase()
        self.active = list(self.original) + list(self.knowledge.clauses)
        self.active_seen = set(self.active)
        self.learned_active = set(self.knowledge.clauses)
        self.deferred = list(deferred or [])
        self.adaptive_deferred = adaptive_deferred
        self.stats = SearchStats(learned_received=len(self.knowledge.clauses))
        self.proof: dict | None = None

    def _activate_relevant_deferred(self, assignment: dict[int, bool]) -> None:
        if not self.adaptive_deferred or not self.deferred:
            return
        keep = []
        for clause in self.deferred:
            sat, rem = clause_status(clause, assignment)
            if not sat and len(rem) <= 1:
                if clause not in self.active_seen:
                    self.active.append(clause)
                    self.active_seen.add(clause)
                    self.learned_active.add(clause)
                    self.stats.deferred_activated += 1
            else:
                keep.append(clause)
        self.deferred = keep

    def solve(self):
        status, assignment, proof = self._dfs({}, ())
        self.proof = proof
        if status == "SAT":
            model = {v: assignment.get(v, False) for v in range(1, self.n_vars + 1)}
            return status, model, None
        return status, None, proof

    def _dfs(self, assignment: dict[int, bool], decisions: tuple[int, ...]):
        if self.stats.nodes >= self.node_budget:
            return "UNKNOWN", None, None
        self.stats.nodes += 1
        self._activate_relevant_deferred(assignment)
        self.stats.max_active_clauses = max(self.stats.max_active_clauses, len(self.active))
        for clause in self.learned_active:
            sat, rem = clause_status(clause, assignment)
            if not sat and len(rem) <= 1:
                self.stats.learned_relevant += 1
        current, conflict, count, _ = unit_propagate(self.active, assignment)
        self.stats.propagations += count
        if conflict:
            self.stats.conflicts += 1
            proof = {"type": "conflict"}
            self._learn_nogood(decisions, proof)
            return "UNSAT", None, proof
        if all_satisfied(self.active, current):
            return "SAT", current, None

        var = choose_variable(self.active, current, self.heuristic)
        left = dict(current)
        left[var] = True
        ls, lm, lp = self._dfs(left, decisions + (var,))
        if ls == "SAT":
            return ls, lm, None
        if ls == "UNKNOWN":
            return ls, None, None
        right = dict(current)
        right[var] = False
        rs, rm, rp = self._dfs(right, decisions + (-var,))
        if rs == "SAT":
            return rs, rm, None
        if rs == "UNKNOWN":
            return rs, None, None
        proof = {"type": "branch", "var": var, "true": lp, "false": rp}
        self._learn_nogood(decisions, proof)
        return "UNSAT", None, proof

    def _learn_nogood(self, decisions: tuple[int, ...], proof: dict) -> None:
        clause = normalize_clause(-lit for lit in decisions)
        if self.knowledge.add(clause, proof):
            self.stats.learned_generated += 1


def verify_sat(original: CNF, model: dict[int, bool]) -> bool:
    return all(any(model[abs(l)] == (l > 0) for l in c) for c in original)


def verify_unsat_tree(original: CNF, proof: dict | None,
                      initial_assignment: dict[int, bool] | None = None) -> bool:
    """Check a full DPLL refutation tree against the original formula."""
    if proof is None:
        return False
    def check(node: dict, assignment: dict[int, bool]) -> bool:
        current, conflict, _, _ = unit_propagate(list(original), assignment)
        if node.get("type") == "conflict":
            return conflict
        if node.get("type") != "branch" or conflict:
            return False
        var = node.get("var")
        if not isinstance(var, int) or var in current:
            return False
        left, right = dict(current), dict(current)
        left[var], right[var] = True, False
        return check(node.get("true", {}), left) and check(node.get("false", {}), right)
    return check(proof, dict(initial_assignment or {}))


def verify_nogood_certificate(original: CNF, clause: Clause, certificate: dict) -> bool:
    """Check that the original formula is UNSAT under the negation of a learned clause."""
    assumptions = {abs(lit): (-lit > 0) for lit in clause}
    return verify_unsat_tree(original, certificate, assumptions)
