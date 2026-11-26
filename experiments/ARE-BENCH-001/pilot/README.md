# Pilot P-001

- Type: exploratory pilot, not confirmatory.
- Code revision: `8483543691aca2d8fc490c1639620d1a14e26ab2`.
- Instances: n=100 (seed 20361126) and n=150 (seed 20411126).
- Aggregate search budget: 2,000 decision nodes per configuration; 1,000 per engine for B/C/D.
- Separate clean UNSAT certificate budget: 2,000,000 nodes.
- Full per-configuration results: [P-001.csv](P-001.csv).
- Environment and run metadata: [P-001.manifest.json](P-001.manifest.json).

## Observations

At n=100, B, C, and D all returned certified UNSAT. C and D both used 1,617 search nodes, while B used 1,851. D loaded 249 clauses immediately versus 996 for C and had a smaller maximum active clause database (676 versus 1,423), but did not reduce the decision-node count or elapsed time.

At n=150, all four configurations returned UNKNOWN at the 2,000-node budget except none: all A/B/C/D reached the limit. D activated four deferred clauses, but did not solve the instance or reduce decision nodes.

The pilot therefore shows no search-node advantage for adaptive exchange D over full exchange C. It suggests a possible active-database-size tradeoff, which needs evaluation across the full paired benchmark. Two instances are insufficient for statistical inference.
