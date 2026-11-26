from are.benchmark import run_configuration


def test_all_configurations_return_certified_status_on_easy_sat():
    cnf = ((1, 2), (-1, 2), (1, -2))
    for config in "ABCD":
        result = run_configuration(config, cnf, 2, total_budget=100)
        assert result["status"] == "SAT" and result["certified"] is True
        if config in "BCD":
            assert result["second_engine_ran"] is True
            assert result["first_engine_status"] == "SAT"
            assert result["second_engine_status"] == "SAT"
            assert result["first_engine_nodes"] > 0
            assert result["second_engine_nodes"] > 0


def test_all_configurations_certify_easy_unsat():
    cnf = ((1, 2), (-1, 2), (1, -2), (-1, -2))
    for config in "ABCD":
        result = run_configuration(config, cnf, 2, total_budget=100)
        assert result["status"] == "UNSAT" and result["certified"] is True
        if config in "BCD":
            assert result["second_engine_ran"] is True
            assert result["first_engine_status"] == "UNSAT"
            assert result["second_engine_status"] == "UNSAT"
            assert result["first_engine_nodes"] > 0
            assert result["second_engine_nodes"] > 0



def test_runner_checkpoints_and_resumes_without_duplicate_rows(tmp_path, monkeypatch):
    import csv
    import json
    import sys
    from are import benchmark

    def fake_run_configuration(name, cnf, n_vars, total_budget):
        return {
            "configuration": name, "status": "SAT", "certified": True,
            "decision_nodes": 1, "propagations": 0, "conflicts": 0,
            "learned_generated": 0, "learned_received": 0, "learned_relevant": 0,
            "learned_certificates_verified": 0, "deferred_activated": 0,
            "max_active_clauses": len(cnf), "elapsed_seconds": 0.001,
            "certificate_verifier_nodes": 0, "note": "test stub",
            "second_engine_ran": False,
        }

    monkeypatch.setattr(benchmark, "run_configuration", fake_run_configuration)
    monkeypatch.setattr(benchmark, "_git_metadata", lambda *_: {
        "git_head_detected": "test-commit", "git_dirty_detected": False
    })
    output = tmp_path / "pilot.csv"
    argv = [
        "are-benchmark", "--sizes", "50", "--limit-per-size", "1",
        "--configs", "A", "--node-budget", "100",
        "--git-commit", "test-commit", "--output", str(output),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    benchmark.main()

    checkpoint = output.with_suffix(".checkpoint.jsonl")
    manifest_path = output.with_suffix(".manifest.json")
    first_checkpoint = checkpoint.read_text(encoding="utf-8")
    assert len(first_checkpoint.splitlines()) == 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["completed_result_rows"] == 1
    assert manifest["classification"] == "pilot/non-confirmatory"

    monkeypatch.setattr(sys, "argv", argv + ["--resume"])
    benchmark.main()
    assert checkpoint.read_text(encoding="utf-8") == first_checkpoint
    with output.open(newline="", encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 1



def test_checkpoint_discards_only_an_unterminated_final_record(tmp_path):
    from are.benchmark import _load_checkpoint

    checkpoint = tmp_path / "run.checkpoint.jsonl"
    checkpoint.write_bytes(b'{"configuration":"A","status":"UNKNOWN","certified":false}\n{"partial":')
    rows = _load_checkpoint(checkpoint)
    assert rows == [{"configuration": "A", "status": "UNKNOWN", "certified": False}]
    assert checkpoint.read_bytes().endswith(b"\n")
