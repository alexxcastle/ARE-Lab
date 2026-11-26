# Bidirectional ARE architecture (design)

## Components

### Forward engine
Applies sound formula transformations and/or DPLL search from the original CNF. Any variable elimination must retain enough information to reconstruct eliminated variables and must account for resolvent growth.

### Backward/complementary engine
The term "backward" describes reconstruction and search guided by partial assignments, elimination traces, and constraints received from the forward engine. It must not invent arbitrary predecessor formulas. It operates on states grounded in the original instance.

### Knowledge manager
Stores clauses with provenance and certification status. Only logically entailed clauses can enter the active shared database. It tracks origin engine, derivation, creation time, activity, transmission status, and use statistics.

### Adaptive controller
Schedules engines and chooses immediate versus deferred clause exchange. The policy is an experimental variable, not a correctness mechanism. Correctness must be independent of the policy.

## Soundness invariant

At every point, the active formula must be equisatisfiable with the original formula or be a strengthening by clauses proven to be logical consequences of the original formula. No heuristic score can authorize a clause.

## Important distinction

A failed bounded search does not prove a branch impossible. A blocking/nogood clause is sound only when the entire subspace it excludes has been exhaustively shown UNSAT, or when a formal proof derives it. Partial failures and timeouts must never be shared as learned clauses.

## Research status

This document specifies a design. It is not evidence that the architecture improves SAT solving or has polynomial complexity.
