# ARE-BENCH-002 — Pilot P-002 results

**Classification:** exploratory pilot; non-confirmatory  
**Protocol:** ARE-BENCH-002 v1.0  
**Source revision:** a2813143b666c5718deaed21612e4d02dcdb624b  
**Run completed:** 2026-11-26  
**Environment:** macOS 26.4 arm64; Python 3.11.4

## Frozen run shape

- First 5 deterministic instances at each of n = 50, 100, 150 (15 formulas total).
- Four configurations A/B/C/D; 60 formula/configuration rows.
- Aggregate search budget: 2,000 decision nodes per formula/configuration.
- A uses one frequency engine; B/C/D allocate 1,000 nodes to each sequential engine.
- Separate UNSAT verifier budget: 2,000,000 nodes; verifier nodes are excluded from search decision_nodes.
- This is the first-five subset of the planned 90-formula confirmatory benchmark. These pilot rows are not an independent sample and must not be counted twice in later analyses.

## Integrity checks

- 60/60 expected result rows completed.
- 15 distinct formulas, each represented exactly once in A/B/C/D.
- Formula identities and seeds match the frozen schedule.
- Checkpoint JSONL and exported CSV contain the same 60 rows and matching field values.
- Manifest records source HEAD a2813143b666c5718deaed21612e4d02dcdb624b, clean source tree, and no resume.
- No engine disagreements; every B/C/D row ran its second engine.
- Run duration: 110.744 seconds.

## Results

| Configuration | SAT | UNSAT | UNKNOWN | Certified | Total decision nodes | Mean nodes/formula |
|---|---:|---:|---:|---:|---:|---:|
| A | 5 | 3 | 7 | 8/15 | 17,403 | 1,160.20 |
| B | 5 | 4 | 6 | 9/15 | 18,181 | 1,212.07 |
| C | 5 | 5 | 5 | 10/15 | 16,367 | 1,091.13 |
| D | 5 | 5 | 5 | 10/15 | 16,367 | 1,091.13 |

By size, all configurations certified all five n=50 formulas. At n=100, A/B/C/D certified 3/4/5/5 formulas respectively. At n=150, all 20 rows ended UNKNOWN at the 2,000-node aggregate budget.

### Paired comparison: D versus C

- Final outcomes were identical on all 15 formulas.
- Decision-node differences (D minus C): 13 ties, one D win by 5 nodes, one D loss by 5 nodes.
- Mean paired difference: 0 nodes; total nodes were exactly equal (16,367 each).
- Mean maximum active clauses: C = 1,066.67; D = 587.27, a reduction of approximately 44.9%.
- D received 2,396 clauses immediately and 7,204 as deferred; 13 deferred clauses were activated.

### Other observations

- C certified 10/15 formulas versus B 9/15 and A 8/15 in this small subset.
- C used 16,367 total search nodes versus B 18,181; descriptive only, not a statistical claim.
- Separate verifier work totalled 5,296 nodes for B and 7,897 each for C and D. These additional certification costs remain separate from search-node totals.

## Interpretation and limits

P-002 does not demonstrate a search-node advantage for adaptive exchange D over full exchange C. Their aggregate and paired search-node counts are equal, and their final outcomes match on every formula. The strongest descriptive signal is a smaller maximum active clause database for D (about 44.9% lower mean than C), while only 13 of 7,204 deferred clauses were activated.

The n=150 results are budget-censored: all configurations returned UNKNOWN on all five formulas. UNKNOWN means the configured search budget was exhausted without a certified result; it is not evidence of UNSAT.

This is a 15-formula exploratory subset, not the confirmatory 90-formula experiment. No inferential statistical conclusion, general SAT speedup, polynomial-time claim, or implication for P vs NP follows from these results.

## Next step

Retain this run unchanged as P-002. After checking out the exact current source revision, running the full test suite, and confirming a clean working tree, execute the frozen 90-formula ARE-BENCH-002 confirmatory run at 100,000 aggregate decision nodes per formula/configuration. Preserve P-002 rows in the eventual full dataset but do not treat overlapping pilot/full rows as independent observations.


## Archived artifact encoding

The four machine-readable run artifacts (CSV, manifest, progress log, and JSONL checkpoint) are stored alongside this report as gzip-compressed Base64 text files. This keeps the repository artifacts text-only while preserving the exact uploaded bytes. Restore any artifact on macOS/Linux with:

```sh
base64 -d P-002.csv.gz.b64 | gzip -dc > P-002.csv
base64 -d P-002.manifest.json.gz.b64 | gzip -dc > P-002.manifest.json
base64 -d P-002.log.gz.b64 | gzip -dc > P-002.log
base64 -d P-002.checkpoint.jsonl.gz.b64 | gzip -dc > P-002.checkpoint.jsonl
```
