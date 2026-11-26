"""Deterministic Random 3-SAT instance generation for ARE-BENCH-001."""

from __future__ import annotations

import hashlib
import json
import random
from typing import TypeAlias

Clause: TypeAlias = tuple[int, int, int]
CNF: TypeAlias = tuple[Clause, ...]
BASE_SEED = 20_261_126
DENSITY = 4.267
INSTANCE_COUNTS = (50, 100, 150)
INSTANCES_PER_SIZE = 30


def seed_for(n_vars: int, index: int) -> int:
    """Return the frozen ARE-BENCH-001 seed for (n_vars, instance index)."""
    if n_vars not in INSTANCE_COUNTS:
        raise ValueError(f"n_vars must be one of {INSTANCE_COUNTS}")
    if not 0 <= index < INSTANCES_PER_SIZE:
        raise ValueError(f"index must be in [0, {INSTANCES_PER_SIZE})")
    return BASE_SEED + 1000 * n_vars + index


def clause_count(n_vars: int) -> int:
    if n_vars <= 0:
        raise ValueError("n_vars must be positive")
    # Python round uses ties-to-even; the selected values are not half-integers.
    return round(DENSITY * n_vars)


def generate_random_3sat(n_vars: int, seed: int) -> CNF:
    """Generate m random 3-clauses with distinct variables and random polarity.

    Clauses are sampled independently with replacement, as specified in the
    benchmark protocol. A literal is a signed 1-based variable index.
    """
    if n_vars < 3:
        raise ValueError("3-SAT requires at least three variables")
    rng = random.Random(seed)
    clauses: list[Clause] = []
    for _ in range(clause_count(n_vars)):
        variables = rng.sample(range(1, n_vars + 1), 3)
        literals = [v if rng.getrandbits(1) else -v for v in variables]
        clause = tuple(sorted(literals, key=lambda lit: (abs(lit), lit < 0)))
        clauses.append(clause)  # type: ignore[arg-type]
    return tuple(clauses)


def serialize_cnf(n_vars: int, cnf: CNF) -> bytes:
    """Stable JSON representation used for SHA-256 instance identity."""
    payload = {"n_vars": n_vars, "clauses": [list(c) for c in cnf]}
    return (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()


def formula_sha256(n_vars: int, cnf: CNF) -> str:
    return hashlib.sha256(serialize_cnf(n_vars, cnf)).hexdigest()


def generate_benchmark_instance(n_vars: int, index: int) -> tuple[int, CNF]:
    seed = seed_for(n_vars, index)
    return seed, generate_random_3sat(n_vars, seed)
