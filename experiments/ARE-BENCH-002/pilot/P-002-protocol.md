# ARE-BENCH-002 Pilot P-002 — 15-instance exploratory extension

Status: **protocol frozen; execution completed; results archived in P-002-report.md**  
Protocol: ARE-BENCH-002 v1.0  
Classification: **pilot / non-confirmatory**

## 1. Purpose

Extend the one-instance clean pilot to a small, predetermined sample across all three formula sizes. The purpose is to check whether the observations from the 50-variable instance recur at 100 and 150 variables, and to inspect paired per-formula outcomes before committing resources to the 90-instance confirmatory run.

This pilot is descriptive. It is not a hypothesis test and cannot establish a general solver advantage.

## 2. Frozen sample

Use the existing ARE-BENCH-002 generator without modification:

- Random 3-SAT, density 4.267.
- Variable counts: 50, 100, 150.
- Five instances per size, indices **0 through 4**.
- Exact seed rule: `seed = 20261126 + 1000*n_vars + index`.
- Expected seeds:
  - n=50: 20311126–20311130
  - n=100: 20361126–20361130
  - n=150: 20411126–20411130
- Same four configurations: A, B, C, D.
- Expected output: 15 formulas × 4 configurations = **60 result rows**.

This is a predetermined subset of the 90 formulas in the full ARE-BENCH-002 benchmark (the first five indices at each size). It is not an independent sample. When the full benchmark is later run, these formulas must remain in it; do not exclude them or pool pilot and confirmatory rows as separate independent observations.

## 3. Compute budget

- Aggregate search-node budget: **2,000 per formula/configuration**.
- A receives up to 2,000 nodes in its frequency engine.
- B/C/D receive up to 1,000 nodes in each of their two stages.
- The separate clean UNSAT verifier remains governed by the runner and is reported separately.
- Do not change the generator, seed schedule, configurations, or solver implementation during this pilot.

## 4. Execution

After pulling the commit that contains this file, confirm a clean tree and run:

```bash
git status --short
COMMIT=$(git rev-parse HEAD)

python -m are.benchmark \
  --git-commit "$COMMIT" \
  --sizes 50 100 150 \
  --limit-per-size 5 \
  --node-budget 2000 \
  --output results/ARE-BENCH-002-P-002.csv
```

The runner should create the CSV, manifest, JSONL checkpoint, and progress log. The manifest must report the exact HEAD and `git_dirty: false`. Expected rows: 60. The run should be complete with all four configurations for each of the 15 formula identities.

If interrupted, resume with the **identical** arguments and append `--resume`. Do not delete or edit the checkpoint to force completion.

## 5. Analysis plan

Report, without dropping UNKNOWN or disagreement rows:

1. Per-formula A/B/C/D statuses and aggregate decision nodes.
2. Paired differences in decision nodes for D−C, C−B, and D−A where both values are available.
3. Certified solved counts and UNKNOWN counts by configuration and variable size.
4. First- and second-engine node counts separately.
5. Clause receipt, deferred activation, and maximum active clause counts.
6. Verifier nodes separately from search decision nodes.
7. Wall-clock time as secondary, environment-dependent information.

Do not describe lower second-stage nodes as an overall speedup unless aggregate work also improves. Do not infer polynomial scaling or implications for P vs NP.

## 6. Interpretation boundary

P-002 is a small exploratory extension on 15 predetermined formulas. It can identify implementation issues and descriptive patterns only. Any apparent advantage must be evaluated on the complete frozen 90-instance protocol before stronger claims are considered.
