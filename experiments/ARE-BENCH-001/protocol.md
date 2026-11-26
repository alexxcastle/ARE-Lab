# ARE-BENCH-001 — Frozen benchmark protocol

Status: **protocol specified; execution pending**  
Protocol version: 1.0  
Problem family: random 3-SAT  
Primary question: does logically sound clause exchange between complementary DPLL search engines reduce total search work under a fixed aggregate node budget?

## 1. Instance generation

For each variable count n in {50, 100, 150}:

- Number of clauses: m = round(4.267 * n).
- Each clause contains exactly 3 distinct variables.
- Each variable's polarity is sampled independently and uniformly.
- Variable triples are sampled uniformly without replacement within each clause.
- Clauses are sampled independently **with replacement** across the formula; duplicate clauses are therefore possible.
- Literal order is canonicalized for serialization only; this does not change the formula.

This is the standard fixed-density random 3-SAT model used by this benchmark. It is not a claim that this density is maximally difficult for every finite n or generator.

## 2. Deterministic seeds

Use Python's `random.Random(seed)` and the committed generator. For each n and instance index i in 0..29:

`seed = 20261126 + 1000*n + i`

The complete seed list is also stored in `seeds.csv`. Never regenerate or silently replace an instance in a published run. Record the SHA-256 of each serialized formula in the results.

## 3. Configurations

All configurations must use the same propagation implementation, variable encoding, instance set, and aggregate decision-node budget.

- **A — Single engine:** one DPLL engine using the pre-registered primary branching heuristic.
- **B — Independent pair:** two engines with distinct pre-registered branching heuristics; they receive separate portions of the total budget and do not exchange learned clauses.
- **C — Full exchange:** same engines and budget split as B; every soundly derived learned clause is made available to the other engine.
- **D — Adaptive exchange:** same engines and total budget; a policy chooses which eligible learned clauses to transmit immediately. Non-transmitted clauses remain in a shared deferred archive and can be retrieved later.

The exact branching heuristics, budget allocation, and implementation version must be recorded in each run manifest before results are inspected. No tuning on the test seeds is permitted for the confirmatory run.

## 4. Work budget and stopping

The confirmatory implementation will use an aggregate budget of 100,000 DPLL decision nodes per formula, allocated as follows:

- A: 100,000 nodes.
- B/C/D: 50,000 nodes per engine (100,000 total).

A node is counted once when a branching decision is made. Propagation operations and clause checks are recorded separately. Wall-clock time is secondary because it is sensitive to runtime environment.

If the budget is exhausted without a verified result, report UNKNOWN. Do not label a budget-limited instance SAT or UNSAT.

## 5. Correctness

- SAT: independently evaluate the original formula under the returned complete assignment.
- UNSAT: require a checkable proof certificate from a proof-producing solver. Until proof logging and checking are implemented, report UNKNOWN for an UNSAT claim that lacks a certificate.
- Every learned clause must have a sound derivation from the original formula or previously certified clauses.
- A partial search failure or timeout is not a valid learned clause. A nogood may be learned only after the entire subspace it excludes has been exhaustively proved UNSAT.

## 6. Primary and secondary metrics

Primary:
- solved instances (SAT and certified UNSAT separately);
- decision nodes per instance;
- aggregate decision nodes.

Secondary:
- unit propagations;
- conflicts;
- learned clauses generated, transmitted, retrieved, and used;
- clause database size;
- wall-clock time and peak memory;
- UNKNOWN count.

Report paired per-instance differences and distributions (median, interquartile range, mean). Include confidence intervals where appropriate. Do not rely only on aggregate averages.

## 7. Reproducibility manifest

Each run must record:
- git commit SHA and dirty/clean status;
- Python and OS versions;
- exact command and configuration;
- benchmark protocol version;
- all instance seeds and formula SHA-256 hashes;
- total node budget and per-engine allocation;
- raw per-instance outcomes and counters;
- stdout/stderr and run timestamp.

## 8. Analysis plan

The primary comparison is D versus C (adaptive versus full exchange), followed by C versus B (full exchange versus independent search). A versus the two-engine configurations is contextual because their search strategies and resource allocations differ.

No post-hoc change to the benchmark, metric definitions, seed schedule, or budget is allowed for the confirmatory analysis. Any change creates a new protocol version and a separately labelled exploratory run.

## 9. Limitations

This benchmark is finite and exploratory. A performance improvement on these instances would not establish a general SAT speedup, a polynomial worst-case bound, or P = NP. A lack of improvement is also informative and must be reported.
