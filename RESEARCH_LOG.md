

## 2026-11-26 — ARE-BENCH-002 exploratory pilot P-002 completed

- Archived the first-five-per-size subset (n=50/100/150; 15 formulas; four configurations; 60 rows) under experiments/ARE-BENCH-002/pilot/.
- Run used the frozen ARE-BENCH-002 v1.0 protocol, 2,000 aggregate decision nodes per formula/configuration (1,000 per engine for B/C/D), with separate 2,000,000-node UNSAT verifier budget.
- Source revision: a2813143b666c5718deaed21612e4d02dcdb624b; manifest records clean source tree and matching HEAD. All 60 rows completed; checkpoint and CSV were cross-checked; no disagreements; second engine ran for every B/C/D row.
- Totals A/B/C/D: certified 8/15, 9/15, 10/15, 10/15; total search nodes 17,403 / 18,181 / 16,367 / 16,367.
- C and D had identical final outcomes on all 15 formulas and identical aggregate decision nodes. Paired D-C differences: 13 ties, one -5, one +5; mean 0.
- Mean maximum active clauses was 1,066.67 for C and 587.27 for D (about 44.9% lower for D). D received 7,204 deferred clauses and activated 13.
- All n=150 rows were UNKNOWN at the 2,000-node budget. UNKNOWN is budget exhaustion, not UNSAT.
- Interpretation: this pilot does not show a search-node advantage for D over C. It offers a descriptive signal of reduced active clause-database size. The sample is exploratory and overlaps with the first 15 formulas of the planned 90-formula benchmark; it is not independent or confirmatory.
- Full 90-formula ARE-BENCH-002 run at 100,000 nodes per formula/configuration remains pending. No conclusion about polynomial-time SAT or P vs NP is supported.
