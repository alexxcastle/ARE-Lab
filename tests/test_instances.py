from are.instances import (
    clause_count,
    formula_sha256,
    generate_benchmark_instance,
    generate_random_3sat,
    seed_for,
)


def test_frozen_clause_counts():
    assert clause_count(50) == 213
    assert clause_count(100) == 427
    assert clause_count(150) == 640


def test_seed_schedule():
    assert seed_for(50, 0) == 20261126 + 50000
    assert seed_for(150, 29) == 20261126 + 150000 + 29


def test_generation_is_deterministic():
    a = generate_random_3sat(50, 12345)
    b = generate_random_3sat(50, 12345)
    assert a == b
    assert formula_sha256(50, a) == formula_sha256(50, b)


def test_each_clause_has_three_distinct_variables():
    cnf = generate_random_3sat(50, 7)
    assert len(cnf) == 213
    for clause in cnf:
        assert len(clause) == 3
        assert len({abs(lit) for lit in clause}) == 3
        assert all(1 <= abs(lit) <= 50 for lit in clause)


def test_benchmark_instance_hash_is_stable():
    seed, cnf = generate_benchmark_instance(50, 0)
    assert seed == seed_for(50, 0)
    assert len(formula_sha256(50, cnf)) == 64
