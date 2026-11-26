# ARE-Lab

Research repository for the **Adaptive / Bidirectional Resolution Engine (ARE)**: an experimental SAT-solving architecture built around variable elimination, complementary search strategies, and exchange of logically certified learned clauses.

> **Scientific status:** exploratory software research. No claim of a polynomial-time SAT algorithm or a result about P vs NP is made.

## Research principles

1. Every reported result must be reproducible from committed code, configuration, and seeds.
2. A solver result is either SAT with a verified assignment, UNSAT with a checkable proof, or UNKNOWN. A timeout is never reported as UNSAT.
3. Learned clauses may be shared only when their entailment has been established by a sound derivation.
4. Benchmarks compare configurations on identical generated instances and equal total work budgets.
5. Negative and inconclusive results are retained.

## Current benchmark

See [ARE-BENCH-001](experiments/ARE-BENCH-001/protocol.md).

The fixed benchmark is Random 3-SAT at density alpha = 4.267, with 50, 100, and 150 variables, 30 instances per size (90 total). The instance generator and deterministic seed schedule are specified in the protocol. The benchmark is a controlled initial test, not a comprehensive evaluation of SAT solvers.

## Repository map

- `docs/architecture/`: architecture and design decisions.
- `docs/methodology/`: scientific and reporting standards.
- `experiments/`: frozen protocols, seeds, raw results, and reports.
- `src/are/`: implementation.
- `tests/`: unit and regression tests.

## Status

The deterministic instance generator and first proof-aware DPLL prototype are implemented. Install and test:

```bash
python -m pip install -e '.[test]'
pytest
python -m are.cli --n-vars 50 --index 0
```

Run a small **pilot** (not the confirmatory benchmark):

```bash
python -m are.benchmark --sizes 50 --limit-per-size 1 --node-budget 2000 --output results/pilot.csv
```

Run the frozen benchmark only with the default 100,000-node budget, all three sizes, and 30 instances per size:

```bash
python -m are.benchmark --git-commit <COMMIT_SHA> --output results/ARE-BENCH-001.csv
```

The runner records per-instance CSV data and a JSON manifest. The first implementation is sequential two-stage DPLL; see `docs/methodology/implementation-v0.1.md`. It is not yet a full CDCL solver or a concurrent bidirectional implementation.

## Evidence status

Previous conversational benchmark numbers are **withdrawn as unverified** and are not part of the evidence base. The first valid pilot data and subsequent confirmatory results must be committed with their exact software revision.
