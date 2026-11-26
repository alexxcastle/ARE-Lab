"""Small CLI for inspecting frozen benchmark instances."""

from __future__ import annotations

import argparse
import json

from .instances import (
    INSTANCE_COUNTS,
    INSTANCES_PER_SIZE,
    formula_sha256,
    generate_benchmark_instance,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-vars", type=int, choices=INSTANCE_COUNTS, required=True)
    parser.add_argument("--index", type=int, choices=range(INSTANCES_PER_SIZE), required=True)
    parser.add_argument("--include-formula", action="store_true")
    args = parser.parse_args()

    seed, cnf = generate_benchmark_instance(args.n_vars, args.index)
    result = {
        "n_vars": args.n_vars,
        "index": args.index,
        "seed": seed,
        "n_clauses": len(cnf),
        "formula_sha256": formula_sha256(args.n_vars, cnf),
    }
    if args.include_formula:
        result["clauses"] = [list(clause) for clause in cnf]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
