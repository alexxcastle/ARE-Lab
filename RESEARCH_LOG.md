# ARE research log

## 2026-11-26 — Repository bootstrap

- Created the ARE-Lab repository and established evidence/reproducibility rules.
- Defined the Bidirectional ARE concept: a forward reduction/search engine, a complementary search/reconstruction engine, and a coordinator/knowledge manager.
- Defined ARE-BENCH-001 as a fixed Random 3-SAT benchmark with 90 deterministic instances.
- Specified four comparison arms: single engine (A), independent pair (B), full certified clause exchange (C), adaptive immediate/deferred exchange (D).

### Evidence correction

Numerical benchmark claims previously discussed in conversation (including claimed 45-instance and 36-instance results) did not have retained executable code, seed lists, raw outputs, or verifiable run manifests. They are withdrawn and must not be cited as experimental evidence.

## 2026-11-26 — Prototype v0.1 implemented

- Implemented deterministic Random 3-SAT generation and SHA-256 formula identities.
- Implemented a queue-based unit-propagation DPLL engine with frequency and Jeroslow-Wang branching heuristics.
- Implemented proof-tree checking for UNSAT and direct model checking for SAT.
- Added certified decision-prefix nogoods: a nogood is retained only after its complete subtree is proved UNSAT; exported clauses are checked against the original formula under the negation of the clause.
- Implemented configurations A/B/C/D and a CSV/JSON-manifest benchmark runner.
- Added tests comparing 100 random small 3-SAT formulas against exhaustive truth-table evaluation.
- Local test result: **14 passed** (including 100 random small formulas checked against exhaustive truth tables).
- Implementation limitation: the current two-engine schedule is sequential and one-way (frequency first, Jeroslow-Wang second), not concurrent or fully bidirectional. The backward variable-elimination reconstruction component is not yet implemented.

## 2026-11-26 — Exploratory pilot P-001

Run manifest: `experiments/ARE-BENCH-001/pilot/P-001.manifest.json`  
Raw data: `experiments/ARE-BENCH-001/pilot/P-001.csv`  
Code revision: `8483543691aca2d8fc490c1639620d1a14e26ab2`

Protocol subset:
- n=100, seed 20361126, 427 clauses.
- n=150, seed 20411126, 640 clauses.
- Configurations A/B/C/D on identical instances.
- Aggregate search budget: 2,000 decision nodes per configuration; B/C/D allocate 1,000 to each engine.
- Separate UNSAT certificate-verifier budget: 2,000,000 nodes.
- This is a two-instance exploratory pilot, **not** the confirmatory benchmark.

### Results

| n | A | B | C | D |
|---:|---|---|---|---|
| 100 | UNKNOWN, 2000 nodes | certified UNSAT, 1851 | certified UNSAT, 1617 | certified UNSAT, 1617 |
| 150 | UNKNOWN, 2000 nodes | UNKNOWN, 2000 | UNKNOWN, 2000 | UNKNOWN, 2000 |

For n=100, C received 996 certified learned clauses; D received 249 immediately and activated no deferred clauses. C and D used the same number of search nodes. The maximum active clause database was 1423 for C and 676 for D.

For n=150, C received 983 clauses; D received 245 immediately and activated 4 deferred clauses. Both reached the 2,000-node budget without solving the instance. Maximum active clause counts were 1623 for C and 889 for D.

All reported UNSAT outcomes were independently certified by a clean DPLL proof run using 2615 additional verifier nodes. These verifier nodes are reported separately and are not included in the 2,000-node search budget.

### Interpretation

- This pilot does **not** show an adaptive-search advantage for D over full exchange C in decision nodes.
- D substantially reduced the number of clauses active in the receiving engine on these two instances.
- On n=100, the reduced active database did not reduce search nodes or observed elapsed time.
- On n=150, none of B/C/D solved the instance within the pilot budget.
- Two instances cannot support a statistical conclusion. These observations are descriptive only.

### Next steps

1. Optimize the DPLL implementation and profiling before the full 90-instance run.
2. Add stronger proof/lemma provenance tests and database-activation instrumentation.
3. Run the frozen benchmark with the prescribed 100,000-node budget and all 90 instances.
4. Compare D against C using paired per-instance differences; retain UNKNOWN outcomes and all raw data.
5. Only after this baseline, investigate interleaved two-way cooperation as a separately versioned experiment.

## Current hypothesis

H1: Under an equal aggregate decision-node budget, adaptive clause exchange (D) may reduce search work or increase certified solved instances relative to full exchange (C).

H0 / null outcome: D does not improve on C, or any apparent benefit disappears under paired reproducible evaluation.

No result so far establishes a general SAT speedup, a polynomial-time algorithm, or anything about P vs NP.


## 2026-11-26 — Durable and resumable benchmark runner

- Added an append-only JSONL checkpoint written and fsynced after each configuration result.
- CSV and manifest are regenerated atomically from the checkpoint, so an interrupted run can be resumed without rerunning completed configurations.
- Resume checks the frozen run settings and validates every completed row against the deterministic seed and formula SHA-256. Duplicate or unexpected rows are rejected.
- Added manifest run states, UTC timestamps, exact command history, source commit and dirty-tree marker, environment, expected/completed row counts, and confirmatory eligibility.
- Added a durable progress log and regression test covering a pilot run followed by a no-duplicate resume.
- This is an implementation change only; the ARE-BENCH-001 instance generator, seed schedule, configurations, and decision-node budgets remain unchanged.
- The new tests have been added to the repository but have **not yet been executed in this environment**. No confirmatory benchmark has been run.

- Follow-up hardening: the runner verifies the supplied commit against Git HEAD, detects dirty source trees automatically (excluding its own output artifacts), records each resume invocation, and safely discards only an unterminated final JSONL append after interruption.
