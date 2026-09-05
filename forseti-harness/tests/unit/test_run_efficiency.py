from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from harness_efficiency import make_record, write_record
from runners import run_efficiency as cli


def options(tmp_path):
    return ["measure", "--workflow", "complete-command", "--workload-id", "fixture-sha",
            "--output-dir", str(tmp_path / "records")]


def record(tmp_path):
    paths = list((tmp_path / "records").glob("*.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text())


def checker(tmp_path, code="raise SystemExit(0)"):
    script = tmp_path / "checker.py"
    script.write_text(code)
    manifest = tmp_path / "checker.json"
    manifest.write_text(json.dumps([sys.executable, str(script)]))
    return manifest


def test_plain_success_keeps_stdout_but_quality_and_tokens_unmeasured(tmp_path, capfd):
    assert cli.main(options(tmp_path) + ["--", sys.executable, "-c", "print('visible output')"]) == 0
    result = record(tmp_path)
    assert result["outcome"] == "success"
    assert result["quality"]["status"] == "unmeasured"
    assert result["usage"]["coverage"] == "unknown"
    assert result["usage"]["total_tokens"] is None
    assert "visible output" in capfd.readouterr().out


def test_independent_quality_command_controls_quality_and_is_timed(tmp_path):
    oracle = checker(tmp_path, "import time; time.sleep(0.03)")
    assert cli.main(options(tmp_path) + ["--quality-command", str(oracle), "--pair-id", "block-1",
                                       "--", sys.executable, "-c", "pass"]) == 0
    result = record(tmp_path)
    assert result["quality"]["status"] == "passed"
    assert result["quality"]["oracle"].startswith("sha256:")
    assert result["elapsed_seconds"] >= 0.03
    assert result["pair_id"] == "block-1"
    assert result["usage"]["total_tokens"] is None


def test_changed_checker_bytes_change_oracle_identity(tmp_path):
    path = tmp_path / "oracle.py"
    path.write_text("pass")
    before = cli._checker_identity([sys.executable, str(path)], tmp_path)
    path.write_text("raise SystemExit(1)")
    assert cli._checker_identity([sys.executable, str(path)], tmp_path) != before


def test_successful_exit_with_failed_quality_remains_failed(tmp_path):
    oracle = checker(tmp_path, "raise SystemExit(7)")
    assert cli.main(options(tmp_path) + ["--quality-command", str(oracle),
                                       "--", sys.executable, "-c", "pass"]) == 7
    result = record(tmp_path)
    assert result["outcome"] == "failed"
    assert result["quality"]["status"] == "failed"
    assert result["quality_return_code"] == 7


def test_command_failure_preserved_and_checker_not_run(tmp_path):
    sentinel = tmp_path / "unexpected"
    oracle = checker(tmp_path, f"from pathlib import Path; Path({str(sentinel)!r}).touch()")
    assert cli.main(options(tmp_path) + ["--quality-command", str(oracle),
                                       "--", sys.executable, "-c", "raise SystemExit(9)"]) == 9
    assert not sentinel.exists()
    assert record(tmp_path)["quality"]["status"] == "unmeasured"


def test_timeout_is_failure_and_records_unknown_coverage(tmp_path):
    assert cli.main(options(tmp_path) + ["--timeout-seconds", "0.05", "--", sys.executable,
                                       "-c", "import time; time.sleep(10)"]) == 124
    result = record(tmp_path)
    assert result["outcome"] == "failed"
    assert "command_timeout" in result["measurement_errors"]
    assert result["usage"]["coverage"] == "unknown"


def test_exact_stdin_avoids_shell_interpretation(tmp_path):
    prompt = tmp_path / "prompt.txt"
    content = "literal & | %PATH% $(not-a-command) `text`\n"
    prompt.write_text(content)
    target = tmp_path / "received.txt"
    code = "import sys; from pathlib import Path; Path(sys.argv[1]).write_text(sys.stdin.read())"
    assert cli.main(options(tmp_path) + ["--stdin-file", str(prompt), "--", sys.executable,
                                       "-c", code, str(target)]) == 0
    assert target.read_text() == content


def test_collector_child_gap_overrides_complete_attempts_and_raw_file_removed(tmp_path, monkeypatch, capsys):
    def execute(command, **kwargs):
        kwargs["stdout"].write((json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "final answer"}}) + "\n").encode())
        return 0, []
    paths = []
    def collect(path, **kwargs):
        assert kwargs["fresh_session"] is True
        assert path.exists()
        paths.append(path)
        return {"attempts": [{"usage": {"coverage": "complete", "input_tokens": 90,
                "output_tokens": 10, "total_tokens": 100, "issues": []}, "outcome": "success"}],
                "coverage": "unknown", "issues": ["child_usage_unknown"]}
    monkeypatch.setattr(cli, "_execute", execute)
    monkeypatch.setattr(cli, "collect_codex_exec", collect)
    assert cli.main(options(tmp_path) + ["--codex-json", "--", "codex.exe", "exec", "--json", "-"]) == 0
    result = record(tmp_path)
    assert result["usage"]["coverage"] == "unknown"
    assert "child_usage_unknown" in result["usage"]["issues"]
    assert result["collection"]["coverage"] == "unknown"
    assert not paths[0].exists()
    assert "final answer" in capsys.readouterr().out


def test_codex_launch_failure_stderr_remains_visible_without_persisted_raw_log(tmp_path, monkeypatch, capfd):
    execute = cli._execute
    def fixture_command(command, **kwargs):
        return execute([sys.executable, "-c",
                        "import sys; print('config.toml: invalid role configuration', file=sys.stderr); sys.exit(1)"],
                       **kwargs)
    monkeypatch.setattr(cli, "_execute", fixture_command)
    assert cli.main(options(tmp_path) + ["--codex-json", "--", "codex.exe", "exec", "--json", "-"]) == 1
    assert "config.toml: invalid role configuration" in capfd.readouterr().err
    result = record(tmp_path)
    assert result["outcome"] == "failed"
    assert result["usage"]["coverage"] == "unknown"
    assert "invalid role configuration" not in json.dumps(result)


@pytest.mark.parametrize("argv", [["codex.exe", "exec", "resume", "--json"],
                                  [sys.executable, "exec", "--json"],
                                  ["codex.exe", "exec", "-"]])
def test_codex_collection_requires_fresh_json_command(tmp_path, argv):
    assert cli.main(options(tmp_path) + ["--codex-json", "--", *argv]) == 2
    assert not (tmp_path / "records").exists()


@pytest.mark.parametrize("timeout", ["nan", "inf", "0", "-1"])
def test_invalid_timeout_rejected(tmp_path, timeout):
    assert cli.main(options(tmp_path) + ["--timeout-seconds", timeout, "--", sys.executable, "-c", "pass"]) == 2


def test_compare_returns_valid_observation_exit_for_unmeasured_and_preserves_order(tmp_path, capsys):
    paths = []
    for i in range(6):
        sample = make_record(workflow="test", workload_id="sha", configuration={"model": "same"},
                             revision="a" if i < 3 else "b", elapsed_seconds=100 if i < 3 else 80,
                             outcome="success", quality={"status": "passed", "oracle": "same"}, attempts=[])
        paths.append(str(write_record(sample, tmp_path)))
    assert cli.main(["compare", "--baseline", *paths[:3], "--candidate", *paths[3:]]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["overall"] == "unmeasured"
    assert result["metrics"]["elapsed_seconds"]["status"] == "improved"
    assert result["cases"][0]["run_pairs"][0][0] == Path(paths[0]).stem


def test_compare_malformed_json_returns_failure(tmp_path):
    invalid = tmp_path / "bad.json"
    invalid.write_text("not json")
    assert cli.main(["compare", "--baseline", str(invalid), "--candidate", str(invalid)]) == 2


def test_compare_output_never_overwrites_existing_file(tmp_path):
    record_path = tmp_path / "record.json"
    record_path.write_text("{}")
    output = tmp_path / "existing.json"
    output.write_text("preserve authored output")
    # Use valid empty comparisons directly to exercise exclusive output creation.
    from argparse import Namespace
    with pytest.raises(FileExistsError):
        cli._compare(Namespace(baseline=[], candidate=[], minimum_pairs=3, threshold=0.05, output=str(output)))
    assert output.read_text() == "preserve authored output"


def test_write_record_exclusive_existing_run_id(tmp_path):
    sample = {"run_id": "fixed", "schema_version": 1}
    path = write_record(sample, tmp_path)
    with pytest.raises(FileExistsError):
        write_record({**sample, "altered": True}, tmp_path)
    assert json.loads(path.read_text()) == sample


def test_desktop_import_keeps_observed_interval_and_unknown_child_coverage(tmp_path, monkeypatch):
    def collect(folder, thread, turn):
        assert (folder, thread, turn) == ("explicit-sessions", "root", "turn")
        return {"attempts": [{"usage": {"coverage": "complete", "input_tokens": 90,
                "output_tokens": 10, "total_tokens": 100, "issues": []}, "outcome": "success"}],
                "coverage": "unknown", "issues": ["child_scope_incomplete"], "elapsed_seconds": 123.5,
                "root_started_at": "start", "root_completed_at": "end"}
    monkeypatch.setattr(cli, "collect_desktop_task", collect)
    assert cli.main(["import-codex", "--sessions-dir", "explicit-sessions", "--thread-id", "root",
                     "--turn-id", "turn", "--workflow", "desktop", "--workload-id", "sha",
                     "--output-dir", str(tmp_path / "records")]) == 0
    result = record(tmp_path)
    assert result["elapsed_seconds"] == 123.5
    assert result["quality"]["status"] == "unmeasured"
    assert result["usage"]["coverage"] == "unknown"
    assert result["revision"] is None


def test_desktop_import_does_not_invent_missing_elapsed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: {
        "attempts": [], "coverage": "unknown", "issues": ["root_incomplete"], "elapsed_seconds": None})
    assert cli.main(["import-codex", "--sessions-dir", "explicit-sessions", "--thread-id", "root",
                     "--turn-id", "turn", "--workflow", "desktop", "--workload-id", "sha",
                     "--output-dir", str(tmp_path / "records")]) == 2
    assert not (tmp_path / "records").exists()
    assert "root_incomplete" in capsys.readouterr().out


def desktop_options(tmp_path):
    return ["import-codex", "--sessions-dir", "explicit-sessions", "--thread-id", "root",
            "--turn-id", "turn", "--workflow", "desktop", "--workload-id", "sha",
            "--output-dir", str(tmp_path / "records")]


def desktop_summary(model="observed-model"):
    return {"attempts": [{"usage": {"coverage": "complete", "input_tokens": 90,
            "output_tokens": 10, "total_tokens": 100, "issues": []}, "outcome": "success"}],
            "coverage": "complete", "issues": [], "elapsed_seconds": 123.5,
            "root_started_at": "historical-start", "root_completed_at": "historical-root-end",
            "workunit_completed_at": "historical-whole-workunit-end", "observed_models": [model]}


def test_posthoc_quality_timing_separate_from_historical_run_and_failed_retry_not_final_failure(tmp_path, monkeypatch):
    summary = desktop_summary()
    summary["attempts"][0]["outcome"] = "failed"
    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: summary)
    oracle = checker(tmp_path, "import time; time.sleep(0.04)")
    assert cli.main(desktop_options(tmp_path) + ["--quality-command", str(oracle), "--cwd", str(tmp_path)]) == 0
    result = record(tmp_path)
    assert result["quality"]["status"] == "passed"
    assert result["quality"]["oracle"].startswith("sha256:")
    assert result["outcome"] == "success"
    assert result["elapsed_seconds"] == 123.5
    assert result["validation_elapsed_seconds"] >= 0.04
    assert result["ended_at"] == "historical-whole-workunit-end"
    assert result["configuration"]["observed_models"] == ["observed-model"]


def test_failed_posthoc_quality_cannot_win_comparison(tmp_path, monkeypatch):
    from copy import deepcopy
    from reports.efficiency_compare import compare_runs

    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: desktop_summary())
    oracle = checker(tmp_path, "raise SystemExit(7)")
    assert cli.main(desktop_options(tmp_path) + ["--quality-command", str(oracle)]) == 7
    failed = record(tmp_path)
    assert failed["quality"]["status"] == "failed"
    assert failed["outcome"] == "failed"
    baseline, candidate = [], []
    for index in range(3):
        left, right = deepcopy(failed), deepcopy(failed)
        left.update(run_id=f"before-{index}", outcome="success", elapsed_seconds=200)
        left["quality"]["status"] = "passed"
        right.update(run_id=f"after-{index}")
        baseline.append(left)
        candidate.append(right)
    assert compare_runs(baseline, candidate)["overall"] == "inconclusive"


def test_different_source_models_block_same_caller_label_comparison(tmp_path, monkeypatch):
    from copy import deepcopy
    from reports.efficiency_compare import compare_runs

    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: desktop_summary("actual-expensive"))
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"model": "same-caller-label"}))
    assert cli.main(desktop_options(tmp_path) + ["--configuration", str(config)]) == 0
    first = record(tmp_path)
    baseline, candidate = [], []
    for index in range(3):
        left, right = deepcopy(first), deepcopy(first)
        left.update(run_id=f"before-{index}", elapsed_seconds=200)
        right.update(run_id=f"after-{index}", elapsed_seconds=100)
        left["quality"] = right["quality"] = {"status": "passed", "oracle": "same"}
        right["configuration"]["observed_models"] = ["actual-cheap"]
        baseline.append(left)
        candidate.append(right)
    assert compare_runs(baseline, candidate)["overall"] == "inconclusive"


def test_caller_cannot_overwrite_source_model_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: desktop_summary())
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"observed_models": ["pretend-model"]}))
    assert cli.main(desktop_options(tmp_path) + ["--configuration", str(config)]) == 2
    assert not (tmp_path / "records").exists()


def test_repository_size_cli_only_deltas_historical_logical_content(tmp_path, monkeypatch, capsys):
    from reports import efficiency_repository

    calls = []
    def size(repo, revision):
        calls.append((repo, revision))
        return {"revision": revision, "tracked_bytes": 100 if revision == "old" else 120,
                "tracked_file_count": 2 if revision == "old" else 3,
                "instruction_source_bytes": 10, "instruction_source_file_count": 1,
                "measurement_log_bytes": 500}
    monkeypatch.setattr(efficiency_repository, "repository_size", size)
    assert cli.main(["repo-size", "--repo", str(tmp_path), "--revision", "new", "--base", "old"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["delta"]["tracked_bytes"] == 20
    assert result["delta"]["tracked_file_count"] == 1
    assert "measurement_log_bytes" not in result["delta"]
    assert calls == [(tmp_path, "new"), (tmp_path, "old")]


def test_same_desktop_workunit_import_has_one_identity_across_directories_and_quality_checks(tmp_path, monkeypatch):
    from reports.efficiency_compare import compare_runs

    summary = desktop_summary()
    summary["attempts"][0]["response_id"] = "observed-response-1"
    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: summary)
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    assert cli.main(desktop_options(first_dir)) == 0
    oracle = checker(tmp_path)
    assert cli.main(desktop_options(second_dir) + ["--quality-command", str(oracle)]) == 0
    first, second = record(first_dir), record(second_dir)
    assert first["run_id"] == second["run_id"]
    assert second["attempts"][0]["response_id"] == "observed-response-1"
    with pytest.raises(ValueError, match="duplicate run_id"):
        compare_runs([first], [second])
    assert cli.main(desktop_options(first_dir)) == 2
    assert record(first_dir) == first


def test_explicit_failed_selected_turn_is_not_rescued_by_passing_posthoc_checker(tmp_path, monkeypatch):
    summary = desktop_summary()
    summary.update(coverage="unknown", issues=["selected_turn_failed_or_aborted"])
    monkeypatch.setattr(cli, "collect_desktop_task", lambda *args: summary)
    oracle = checker(tmp_path)
    assert cli.main(desktop_options(tmp_path) + ["--quality-command", str(oracle)]) == 1
    result = record(tmp_path)
    assert result["quality"]["status"] == "passed"
    assert result["quality_return_code"] == 0
    assert result["outcome"] == "failed"
    assert result["usage"]["coverage"] == "unknown"
