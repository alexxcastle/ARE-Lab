# Evidence and reporting policy

- Separate hypotheses, implementation facts, measured observations, and mathematical proofs.
- Never fabricate or estimate benchmark outputs.
- Preserve raw per-instance data, not just aggregate summaries.
- Pin code revision, configuration, seeds, environment, and budgets.
- Use paired comparisons on identical instances.
- Report SAT and certified UNSAT separately; UNKNOWN is a first-class outcome.
- Validate every SAT assignment against the original formula.
- Require checkable proof certificates for UNSAT.
- Keep exploratory tuning separate from confirmatory evaluation.
- Record negative results and protocol deviations.
- A finite benchmark cannot establish a worst-case complexity result or resolve P vs NP.
