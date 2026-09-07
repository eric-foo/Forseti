"""Accounting invariants and failure visibility at the operational boundary."""
import json
from pathlib import Path

import pytest

import harness_efficiency as efficiency


def test_openai_breakdowns_are_not_added_again():
    usage = efficiency.normalize_usage("openai_responses", {
        "input_tokens": 100, "input_tokens_details": {"cached_tokens": 70},
        "output_tokens": 40, "output_tokens_details": {"reasoning_tokens": 30},
        "total_tokens": 140, "request_body": "must never be copied",
    })
    assert usage["coverage"] == "complete"
    assert usage["total_tokens"] == 140
    assert usage["cached_input_tokens"] == 70
    assert usage["reasoning_output_tokens"] == 30
    assert "must never" not in json.dumps(usage)


def test_anthropic_adds_exclusive_cache_components_once():
    usage = efficiency.normalize_usage("anthropic_messages", {
        "input_tokens": 20, "cache_read_input_tokens": 70,
        "cache_creation_input_tokens": 10, "output_tokens": 40,
    })
    assert usage["input_tokens"] == 100
    assert usage["total_tokens"] == 140
    assert usage["coverage"] == "complete"


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": 1},
    {"input_tokens": True, "output_tokens": 2},
    {"input_tokens": -1, "output_tokens": 2},
    {"input_tokens": 2, "output_tokens": 3, "total_tokens": 6},
    {"input_tokens": 2, "output_tokens": 3, "cached_input_tokens": 4},
    {"input_tokens": 2, "output_tokens": 3, "reasoning_output_tokens": 4},
])
def test_missing_malformed_or_inconsistent_usage_never_means_zero(usage):
    normalized = efficiency.normalize_usage("codex_exec", usage)
    assert normalized["coverage"] == "unknown"
    assert normalized["total_tokens"] is None
    assert normalized["issues"]


def test_missing_breakdown_stays_unknown_without_losing_observed_total():
    usage = efficiency.normalize_usage("codex_exec", {"input_tokens": 2, "output_tokens": 3})
    assert usage["total_tokens"] == 5
    assert usage["cached_input_tokens"] is None
    assert usage["reasoning_output_tokens"] is None
    exclusive = efficiency.normalize_usage("anthropic_messages", {"input_tokens": 2, "output_tokens": 3})
    assert exclusive["total_tokens"] is None


def test_unknown_failed_attempt_prevents_successful_retry_hiding_spend():
    attempts = [
        {"outcome": "failed", "usage": efficiency.unknown_usage("provider_timeout")},
        {"outcome": "success", "usage": efficiency.normalize_usage("codex_exec", {
            "input_tokens": 10, "output_tokens": 2})},
    ]
    result = efficiency.aggregate_usage(attempts)
    assert result["total_tokens"] is None
    assert result["observed_totals"]["total_tokens"] == 12
    assert result["coverage"] == "unknown"


def test_full_operation_record_survives_fresh_read(tmp_path):
    with efficiency.RunMeasurement("fixture", "case-sha", {}, output_dir=tmp_path, revision="abc") as run:
        assert efficiency.current_measurement() is run
        with run.stage("work"):
            run.add_attempt("codex_exec", "configured", .01,
                efficiency.normalize_usage("codex_exec", {"input_tokens": 5, "output_tokens": 2}))
        run.set_quality("passed", "fixture_exact_output", "hash")
    assert efficiency.current_measurement() is None
    stored = json.loads(run.path.read_text())
    assert stored["outcome"] == "success"
    assert stored["quality"]["output_fingerprint"] == "hash"
    assert stored["usage"]["total_tokens"] == 7
    assert stored["elapsed_seconds"] >= stored["stages"]["work"] >= 0
    assert stored["started_at"] <= stored["ended_at"]


def test_product_failure_keeps_original_exception_and_failed_record(tmp_path):
    error = RuntimeError("product failed")
    with pytest.raises(RuntimeError) as caught:
        with efficiency.RunMeasurement("fixture", "case", {}, output_dir=tmp_path, revision="abc") as run:
            raise error
    assert caught.value is error
    assert json.loads(run.path.read_text())["outcome"] == "failed"
    assert efficiency.current_measurement() is None


@pytest.mark.parametrize("product_fails", [False, True])
def test_logging_failure_visible_without_changing_product_outcome(tmp_path, capsys, product_fails):
    target = tmp_path / "file"
    target.write_text("existing authored data")
    run = efficiency.RunMeasurement("fixture", "case", {}, output_dir=target, revision="abc")
    def execute():
        with run:
            if product_fails:
                raise LookupError("original")
        return "actual product success"
    if product_fails:
        with pytest.raises(LookupError, match="original"):
            execute()
    else:
        assert execute() == "actual product success"
    assert "efficiency measurement unavailable" in capsys.readouterr().err
    assert run.path is None and run.errors
    assert target.read_text() == "existing authored data"


def test_record_files_never_overwrite(tmp_path):
    record = {"run_id": "fixed"}
    path = efficiency.write_record(record, tmp_path)
    with pytest.raises(FileExistsError):
        efficiency.write_record(record, tmp_path)
    assert json.loads(path.read_text()) == record
