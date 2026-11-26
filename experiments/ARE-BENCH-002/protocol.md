# ARE-BENCH-002 — Mandatory second-engine benchmark

Status: **new protocol; implementation committed; local tests pending**
Protocol version: 1.0
Supersedes ARE-BENCH-001 only for the new execution schedule; ARE-BENCH-001 remains an immutable historical baseline.

## 1. Research question

When the first frequency-heuristic engine has already returned a result, does still running a second Jeroslow-Wang engine change the measured outcomes or expose useful effects from certified clause exchange? The primary comparison remains D versus C, followed by C versus B.

This protocol specifically removes the early-stop behavior that prevented the second engine from running on the ARE-BENCH-001 confirmatory run.

## 2. Instances: unchanged from ARE-BENCH-001

The formula generator, density, sizes, and deterministic seeds are unchanged:

- Random 3-SAT at density 4.267.
- Variable counts: 50, 100, and 150.
- 30 formulas per size; 90 formula instances total.
- For each size n and index i in 0..29: seed = 20261126 + 1000*n + i.
- Clause count: round(4.267*n); three distinct variables per clause; independent random polarity; clauses sampled with replacement.
- Formula identity is recorded using SHA-256.

The same seed schedule means the new run can be paired formula-by-formula with ARE-BENCH-001. The protocol identifier and execution schedule are different, so the runs must not be pooled as if they were one experiment.

## 3. Configurations

All configurations use the same original formula and propagation implementation.

- **A — Single engine:** one frequency-heuristic DPLL engine, with up to the full 100,000-node budget.
- **B — Independent pair:** frequency first, then Jeroslow-Wang; no learned-clause exchange.
- **C — Full exchange:** same two engines; all stage-1 learned clauses with independently verified certificates are loaded into stage 2.
- **D — Adaptive exchange:** same two engines; the shortest 25% of verified clauses are loaded immediately. The remaining verified clauses enter a deferred archive and are activated only when they become unit or conflicting under the receiving engine's partial assignment.

### Mandatory execution rule

For every B/C/D formula, stage 2 **must be started**, regardless of whether stage 1 returned SAT, UNSAT, or UNKNOWN. Stage 2 searches the original CNF with the Jeroslow-Wang heuristic and only the clauses allowed by its configuration.

"Must be started" does not mean wasting nodes after a terminal result: each engine stops normally when it finds SAT, proves UNSAT, or exhausts its own budget. The purpose is to ensure that both engines actually execute and that the second engine's outcome and work are recorded.

The two stages are sequential, not parallel. Stage 2 is a fresh search; it does not inherit stage 1's partial assignment or decision stack.

## 4. Budgets

The aggregate search-node budget is at most 100,000 decisions per formula/configuration:

- A: up to 100,000 nodes in its single engine.
- B/C/D: up to 50,000 nodes in frequency stage 1 and up to 50,000 nodes in JW stage 2.

Unused nodes from an early-terminating stage are not transferred to the other stage. This fixed split is retained to keep the comparison deterministic and to avoid a post-hoc budget policy.

The separate clean UNSAT verifier has a budget of max(2,000,000, 20 × aggregate budget). Verifier nodes are reported separately and excluded from decision_nodes.

## 5. Correctness and combined outcomes

Each engine's outcome is recorded independently:

- SAT is certified by checking its complete model against the original CNF.
- Stage-1 UNSAT is certified by checking its proof tree against the original CNF.
- Stage-2 UNSAT is independently re-proved against the original CNF by a clean DPLL verifier, because the stage-2 search may have used imported clauses.
- UNKNOWN is never treated as a proof.

The configuration-level result is SAT or UNSAT if at least one engine has a valid certificate and there is no contradictory independently certified result. If both engines independently certify opposite outcomes, the row is recorded as UNKNOWN with engine_disagreement=true; this is a correctness alarm, not a normal solver outcome.

Every imported clause must pass the existing nogood-certificate check against the original formula. In D, deferred clauses count as received when placed in the archive; learned_received_immediate, learned_received_deferred, and deferred_activated distinguish receipt from activation.

## 6. Recorded metrics

The CSV records:

- Configuration-level certified status and aggregate search decision nodes.
- First- and second-engine raw status, certification, node count, elapsed time, and whether stage 2 ran.
- Total learned clauses generated, received, certificate-verified, and deferred clauses activated.
- Immediate and deferred clause receipt counts separately.
- Propagations, conflicts, maximum active clause count, and separate verifier nodes.

decision_nodes is the sum of stage-1 and stage-2 search nodes for B/C/D; it excludes clean verifier nodes. Wall-clock time is secondary and environment-dependent.

## 7. Reproducibility

The run uses the exact same 90 formulas as ARE-BENCH-001, but a new protocol identifier and source commit. The runner records the commit SHA, clean/dirty state, Python/OS, exact command, seeds and formula hashes, settings, progress checkpoint, CSV, manifest, and log.

A full-shape run is only eligible for confirmatory classification when run from a clean tree at the exact recorded commit. Eligibility is a procedural property, not evidence of a positive result.

## 8. Interpretation limits

This is a finite benchmark of a basic DPLL prototype. It cannot establish a general SAT speedup, a polynomial worst-case bound, or P = NP. Compare paired per-formula results, report UNKNOWN and disagreement rows, and retain all raw outputs.
