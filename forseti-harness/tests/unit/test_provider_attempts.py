from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from provider_attempts import publish_provider_attempt, reserve_provider_attempt


def _events(usage: dict[str, int]) -> str:
    return json.dumps({"type": "turn.completed", "usage": usage}) + "\n"


def test_provider_attempt_storage_is_stage_neutral_and_no_replace(tmp_path: Path) -> None:
    reserved = reserve_provider_attempt(
        attempt_root=tmp_path / "attempts", attempt_id="judge-angle-a-attempt-01"
    )
    attempt_dir = Path(reserved["attempt_dir"])
    response = {"surface": "compact", "axis_id": "scent_and_flavor"}
    (attempt_dir / "response.json").write_text(
        json.dumps(response), encoding="utf-8"
    )
    (attempt_dir / "events.jsonl").write_text(
        _events(
            {
                "input_tokens": 120,
                "cached_input_tokens": 40,
                "output_tokens": 25,
                "reasoning_output_tokens": 9,
            }
        ),
        encoding="utf-8",
    )

    published = publish_provider_attempt(
        attempt_dir=attempt_dir,
        response_dir=tmp_path / "responses",
        canonical_response_name="angle_a.json",
        usage_schema_version="test_provider_attempt_usage_v1",
        validate_response=lambda value: {"axis_id": value["axis_id"]},
    )

    assert reserved["model_api_calls"] == 0
    assert published["model_api_calls"] == 0
    assert published["axis_id"] == "scent_and_flavor"
    assert published["usage"]["cached_input_tokens"] == 40
    assert json.loads((attempt_dir / "usage.json").read_text(encoding="utf-8"))[
        "schema_version"
    ] == "test_provider_attempt_usage_v1"
    canonical = Path(published["response_path"])
    assert json.loads(canonical.read_text(encoding="utf-8")) == response

    retry = reserve_provider_attempt(
        attempt_root=tmp_path / "attempts", attempt_id="judge-angle-a-attempt-02"
    )
    retry_dir = Path(retry["attempt_dir"])
    (retry_dir / "response.json").write_text(json.dumps(response), encoding="utf-8")
    (retry_dir / "events.jsonl").write_text(
        _events(
            {
                "input_tokens": 1,
                "cached_input_tokens": 0,
                "output_tokens": 1,
                "reasoning_output_tokens": 0,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="refusing to overwrite existing response"):
        publish_provider_attempt(
            attempt_dir=retry_dir,
            response_dir=tmp_path / "responses",
            canonical_response_name="angle_a.json",
            usage_schema_version="test_provider_attempt_usage_v1",
        )
    assert (retry_dir / "response.json").is_file()
    assert (retry_dir / "events.jsonl").is_file()
    assert (retry_dir / "usage.json").is_file()


def _failed_publication(tmp_path: Path) -> tuple[dict, dict[str, bytes]]:
    reserved = reserve_provider_attempt(attempt_root=tmp_path / "attempts", attempt_id="finished-answer")
    folder = Path(reserved["attempt_dir"])
    payloads = {
        "response.json": b'{"evidence_id":"row-a","decision":"accept"}',
        "events.jsonl": _events({"input_tokens": 120, "cached_input_tokens": 40,
            "output_tokens": 25, "reasoning_output_tokens": 9}).encode(),
        "stderr.log": b"",
        "execution_started.json": b"{}",
    }
    receipt = {"outcome": "PROCESS_COMPLETED", **{
        field: hashlib.sha256(payloads[name]).hexdigest()
        for name, field in (("response.json", "response_sha256"),
            ("events.jsonl", "events_sha256"), ("stderr.log", "stderr_sha256"))}}
    payloads["execution_receipt.json"] = json.dumps(receipt).encode()
    for name, value in payloads.items():
        (folder / name).write_bytes(value)
    kwargs = dict(attempt_dir=folder, response_dir=tmp_path / "responses",
        canonical_response_name="answer.json", usage_schema_version="test_usage_v1")
    def reject(_value: dict) -> dict:
        raise ValueError("seeded validation failure")
    with pytest.raises(ValueError, match="seeded validation failure"):
        publish_provider_attempt(**kwargs, validate_response=reject)
    assert not (tmp_path / "responses/answer.json").exists()
    return kwargs, {path.name: path.read_bytes() for path in folder.iterdir()}


def test_publication_recovers_unchanged_usage_after_validation_failure(tmp_path: Path) -> None:
    kwargs, before = _failed_publication(tmp_path)
    published = publish_provider_attempt(**kwargs,
        validate_response=lambda value: {"evidence_id": value["evidence_id"]})
    assert published["evidence_id"] == "row-a"
    assert published["model_api_calls"] == 0
    assert Path(published["response_path"]).read_bytes() == before["response.json"]
    assert {path.name: path.read_bytes() for path in kwargs["attempt_dir"].iterdir()} == before
    with pytest.raises(ValueError, match="refusing to overwrite existing response"):
        publish_provider_attempt(**kwargs)
    assert Path(published["response_path"]).read_bytes() == before["response.json"]


@pytest.mark.parametrize("violation", ["receipt", "schema"])
def test_publication_recovery_never_restamps_conflicting_usage(tmp_path: Path, violation: str) -> None:
    kwargs, _ = _failed_publication(tmp_path)
    usage_path = kwargs["attempt_dir"] / "usage.json"
    if violation == "receipt":
        altered = json.loads(usage_path.read_text(encoding="utf-8"))
        altered["usage"]["input_tokens"] += 1
        usage_path.write_text(json.dumps(altered), encoding="utf-8")
    else:
        kwargs["usage_schema_version"] = "different_schema"
    before = usage_path.read_bytes()
    with pytest.raises(ValueError, match="existing usage receipt does not match"):
        publish_provider_attempt(**kwargs)
    assert usage_path.read_bytes() == before
    assert not (tmp_path / "responses/answer.json").exists()
