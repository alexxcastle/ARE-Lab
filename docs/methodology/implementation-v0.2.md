# ARE-BENCH-002 — Implementation notes (prototype v0.2)

These notes describe the implementation associated with the mandatory second-engine protocol. The frozen specification is experiments/ARE-BENCH-002/protocol.md.

## Engine schedule

The implementation is sequential, not concurrent:

1. Stage 1 runs the frequency heuristic with up to half of the aggregate decision-node budget.
2. Stage 2 always starts for configurations B/C/D, even when stage 1 has returned SAT or UNSAT.
3. Stage 2 runs a fresh Jeroslow-Wang search on the original CNF, with the clause-transfer policy defined by B, C, or D.
4. Each stage stops normally on a terminal SAT/UNSAT result or when its own budget is exhausted. Unused nodes are not transferred between stages.

This is an execution-policy change from ARE-BENCH-001. It is not a change to the formula generator or seed schedule.

## Configurations

- A: one frequency-heuristic engine with the full budget.
- B: frequency followed by Jeroslow-Wang, no clause exchange.
- C: frequency followed by Jeroslow-Wang; every independently verified stage-1 clause is loaded into stage 2.
- D: frequency followed by Jeroslow-Wang; the shortest 25% of verified clauses are loaded immediately, and the rest are held in the deferred archive for activation when unit or conflicting.

For D, the total received count includes both the immediate set and the deferred archive. The CSV reports immediate and deferred receipt separately, while deferred_activated records clauses actually activated during search.

## Per-engine outcomes and soundness

The CSV records each stage's raw status, certification, decision nodes, and elapsed time. A SAT model is checked against the original formula. Stage-1 UNSAT is checked using its proof tree against the original formula. Stage-2 UNSAT is independently re-proved by a clean DPLL run on the original formula because stage 2 may rely on imported clauses.

The configuration-level result is certified if at least one engine has a verified result, unless both engines independently certify contradictory outcomes. Such a disagreement is recorded as UNKNOWN with an explicit engine_disagreement flag; it must be investigated as a correctness failure.

All exchanged nogoods are independently checked against the original formula under the negation of the clause before transfer.

## Metrics

decision_nodes is the sum of search nodes from both stages for B/C/D and excludes the clean UNSAT verifier. The separate first_engine_nodes and second_engine_nodes fields make the work split visible. The verifier's nodes remain in certificate_verifier_nodes.

learned_received counts clauses delivered to the receiving stage, including D's deferred archive. learned_received_immediate and learned_received_deferred separate the two channels. learned_certificates_verified counts the verified exportable clauses. learned_relevant remains a relevance proxy, not proof that a clause caused a propagation.

## Tests and execution status

Regression tests assert that B/C/D start the second engine on both easy SAT and easy UNSAT formulas, including cases where stage 1 already returns a terminal result. The runner also rejects resumed B/C/D checkpoint rows that do not record a second-engine execution.

The source changes have been committed, but local tests and the new full benchmark must be run on the user's machine before any successful execution or scientific result is claimed.
