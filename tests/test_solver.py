from itertools import product
from are.solver import DPLLEngine, KnowledgeBase, verify_sat, verify_unsat_tree, verify_nogood_certificate


def brute_sat(cnf, n):
    for bits in product([False, True], repeat=n):
        model = {i + 1: bits[i] for i in range(n)}
        if all(any(model[abs(l)] == (l > 0) for l in c) for c in cnf):
            return model
    return None


def test_solver_sat_and_model_check():
    cnf = ((1, 2), (-1, 2), (1, -2))
    status, model, proof = DPLLEngine(cnf, 2, node_budget=100).solve()
    assert status == "SAT" and model is not None and verify_sat(cnf, model)
    assert proof is None


def test_solver_unsat_and_tree_certificate():
    cnf = ((1,), (-1,))
    kb = KnowledgeBase()
    status, model, proof = DPLLEngine(cnf, 1, knowledge=kb).solve()
    assert status == "UNSAT" and model is None
    assert verify_unsat_tree(cnf, proof)
    assert kb.clauses == [tuple()]


def test_learned_nogood_certificate():
    cnf = ((-1, 2), (-1, -2), (1, 3), (1, -3))
    kb = KnowledgeBase()
    status, _, _ = DPLLEngine(cnf, 3, knowledge=kb).solve()
    assert status == "UNSAT"
    for clause in kb.clauses:
        assert verify_nogood_certificate(cnf, clause, kb.certificates[clause])


def test_small_instances_match_bruteforce():
    formulas = [
        ((1, 2), (-1, 2), (1, -2)),
        ((1,), (-1,)),
        ((1, 2), (-1, 2), (1, -2), (-1, -2)),
        ((1, 2, 3), (-1, 2), (-2, 3), (-3,)),
    ]
    for cnf in formulas:
        n = max(abs(l) for c in cnf for l in c)
        expected = brute_sat(cnf, n)
        status, model, proof = DPLLEngine(cnf, n, node_budget=1000).solve()
        if expected is None:
            assert status == "UNSAT" and verify_unsat_tree(cnf, proof)
        else:
            assert status == "SAT" and model is not None and verify_sat(cnf, model)


def test_budget_limited_search_exports_only_certified_nogood():
    cnf = ((-1, 2), (-1, -2))
    kb = KnowledgeBase()
    status, _, _ = DPLLEngine(cnf, 2, node_budget=2, knowledge=kb).solve()
    assert status == "UNKNOWN"
    assert (-1,) in kb.clauses
    assert verify_nogood_certificate(cnf, (-1,), kb.certificates[(-1,)])


def test_bounded_run_never_calls_unknown_unsat():
    cnf = ((-1, 2), (-1, -2))
    status, model, proof = DPLLEngine(cnf, 2, node_budget=1).solve()
    assert status == "UNKNOWN" and model is None and proof is None


def test_random_small_3sat_matches_exhaustive_truth_table():
    import random
    rng = random.Random(90210)
    for _ in range(100):
        n = rng.choice([3, 4, 5])
        clauses = []
        for _ in range(rng.randint(1, 12)):
            variables = rng.sample(range(1, n + 1), 3)
            clauses.append(tuple(v if rng.getrandbits(1) else -v for v in variables))
        cnf = tuple(clauses)
        expected = brute_sat(cnf, n)
        status, model, proof = DPLLEngine(cnf, n, node_budget=10000).solve()
        if expected is None:
            assert status == "UNSAT" and verify_unsat_tree(cnf, proof)
        else:
            assert status == "SAT" and model is not None and verify_sat(cnf, model)
