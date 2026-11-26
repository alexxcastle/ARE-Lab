# ARE research log

## 2026-11-26 — Repository bootstrap

- Created the ARE-Lab repository and established evidence/reproducibility rules.
- Defined the Bidirectional ARE concept: a forward reduction/search engine, a complementary search/reconstruction engine, and a coordinator/knowledge manager.
- Defined ARE-BENCH-001 as a fixed Random 3-SAT benchmark with 90 deterministic instances.
- Specified four comparison arms: single engine (A), independent pair (B), full certified clause exchange (C), adaptive immediate/deferred exchange (D).
- Status: protocol specified; implementation and valid benchmark execution pending.

### Evidence correction

Numerical benchmark claims previously discussed in conversation (including claimed 45-instance and 36-instance results) did not have retained executable code, seed lists, raw outputs, or verifiable run manifests. They are withdrawn and must not be cited as experimental evidence.

### Current hypothesis

H1: Under an equal aggregate decision-node budget, adaptive clause exchange (D) may reduce search work or increase the number of certified solved instances relative to full exchange (C).

H0 / null outcome: D does not improve on C, or any apparent benefit disappears under paired reproducible evaluation.

### Next steps

1. Implement deterministic instance generation and formula hashing.
2. Implement a sound baseline DPLL engine and correctness tests.
3. Add proof-safe learned-clause generation and validation.
4. Implement A/B/C/D wrappers with equal aggregate budgets.
5. Run smoke tests, then the frozen 90-instance benchmark.
6. Commit raw results and a run manifest; do not alter the protocol after seeing outcomes.
