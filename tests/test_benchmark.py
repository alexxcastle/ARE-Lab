from are.benchmark import run_configuration


def test_all_configurations_return_certified_status_on_easy_sat():
    cnf = ((1, 2), (-1, 2), (1, -2))
    for config in "ABCD":
        result = run_configuration(config, cnf, 2, total_budget=100)
        assert result["status"] == "SAT" and result["certified"] is True


def test_all_configurations_certify_easy_unsat():
    cnf = ((1, 2), (-1, 2), (1, -2), (-1, -2))
    for config in "ABCD":
        result = run_configuration(config, cnf, 2, total_budget=100)
        assert result["status"] == "UNSAT" and result["certified"] is True
