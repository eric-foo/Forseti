from __future__ import annotations

import json
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
