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

Initial repository bootstrap. Previous conversational benchmark numbers are **withdrawn as unverified** and are not part of the evidence base. The first valid results will be produced by the committed benchmark implementation and stored with their exact software revision.

## Reproduce

The deterministic instance generator is implemented. Install the package and run the tests:\n\n\`\`\`bash\npython -m pip install -e '.[test]'\npytest\npython -m are.cli --n-vars 50 --index 0\n\`\`\`\n\nThe generator reports a stable SHA-256 for each formula. The solver configurations and proof-checked result pipeline are still pending. Do not infer solver performance from instance-generation tests.
