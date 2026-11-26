# ARE-BENCH-001 — Implementation notes (prototype v0.1)

These notes pin down the first executable implementation. The frozen confirmatory protocol remains the authority for the eventual 90-instance, 100,000-node run.

## Engines and schedule

The first implementation uses a **sequential two-stage schedule**, not simultaneous parallel execution:

1. Engine A1 runs the frequency heuristic with half of the aggregate decision-node budget.
2. If A1 returns SAT or UNSAT, the run stops for that configuration.
3. If A1 returns UNKNOWN, the second engine runs the Jeroslow-Wang heuristic with the remaining half-budget.

This makes the first exchange experiment deterministic and avoids introducing concurrency/scheduling noise. True interleaved or parallel cooperation is a later protocol variant.

## Configuration definitions

- A: one frequency-heuristic engine with the full budget.
- B: frequency engine followed by Jeroslow-Wang, no clause exchange.
- C: same two-stage engines; all certified clauses from stage 1 are loaded before stage 2.
- D: same two-stage engines; the shortest 25% of certified clauses are loaded immediately. The rest are deferred and activated only when they become unit or conflicting under the receiver's current partial assignment.

The 25% threshold and shortest-clause ranking are fixed for this implementation. They are not tuned on confirmatory seeds.

## Soundness and certificates

Stage 1 learns a nogood only when a complete decision subtree is proved UNSAT. The nogood is the negation of the decisions defining that subtree. Every exported nogood is independently checked against the original formula under the negation of the nogood.

SAT models are checked against every original clause.

If stage 2 reports UNSAT after using imported clauses, a clean DPLL run on the original formula must independently produce a complete refutation tree. Its separate node count is recorded as certificate-verification work. If this verification does not complete, the benchmark status is UNKNOWN, not UNSAT.

## Metrics

`decision_nodes` is the aggregate across search engines and excludes the separate UNSAT certificate-verifier run. `certificate_verifier_nodes` reports that extra work. `learned_relevant` counts active learned clauses that are unit or conflicting at a visited state; it is a relevance proxy, not a count of clauses that necessarily caused propagation. `deferred_activated` counts deferred clauses activated by the lazy policy.

Elapsed time includes the configuration's search and certification work. Wall-clock measurements are secondary and environment-dependent.

## Known limitations

- This is a basic DPLL prototype, not CDCL, and does not implement watched literals or industrial preprocessing.
- The backward engine is currently represented by a complementary second search with model reconstruction; variable-elimination trace reconstruction is not yet integrated.
- Exchange is one-way in this staged implementation.
- The adaptive policy is deliberately simple.
- The prototype's results cannot establish a general speedup or a complexity-class result.


## Durable benchmark execution (runner revision)

The benchmark runner persists one JSONL result record after each configuration and calls fsync before refreshing derived outputs. The CSV and manifest are rewritten atomically from the checkpoint. The JSONL file is the source of truth for recovery.

- A run writes OUTPUT.csv, OUTPUT.manifest.json, OUTPUT.checkpoint.jsonl, and OUTPUT.log.
- The --resume option requires the same protocol, source commit, dirty-tree flag, sizes, instance count, configurations, and budgets. Every checkpoint row is revalidated against its deterministic seed and formula SHA-256 before reuse.
- Duplicate, unexpected, uncertified, or formula-mismatched checkpoint rows are rejected.
- The manifest distinguishes running from complete, records expected/completed result rows, exact invocation history, UTC timestamps, source revision, environment, and confirmatory eligibility.
- A full-shaped run from a dirty working tree is explicitly non-confirmatory. A complete run is not automatically evidence of a performance improvement.

Example recovery invocation (all original options must be retained):

    python -m are.benchmark --git-commit COMMIT_SHA --output results/ARE-BENCH-001.csv --resume
