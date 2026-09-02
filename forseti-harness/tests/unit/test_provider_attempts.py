from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from provider_attempts import publish_provider_attempt, reserve_provider_attempt
from provider_attempts import (
    ProviderAttemptRecoveryError,
    inspect_timed_out_provider_attempt,
    recover_timed_out_provider_attempt,
)


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


def _completed_attempt(tmp_path: Path, response: bytes) -> dict:
    reserved = reserve_provider_attempt(attempt_root=tmp_path / "attempts", attempt_id="finished-answer")
    folder = Path(reserved["attempt_dir"])
    payloads = {
        "response.json": response,
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
    return kwargs


def _failed_publication(tmp_path: Path) -> tuple[dict, dict[str, bytes]]:
    kwargs = _completed_attempt(tmp_path, b'{"evidence_id":"row-a","decision":"accept"}')
    folder = kwargs["attempt_dir"]
    def reject(_value: dict) -> dict:
        raise ValueError("seeded validation failure")
    with pytest.raises(ValueError, match="seeded validation failure"):
        publish_provider_attempt(**kwargs, validate_response=reject)
    assert not (tmp_path / "responses/answer.json").exists()
    return kwargs, {path.name: path.read_bytes() for path in folder.iterdir()}


@pytest.mark.parametrize("response, duplicate_key", [
    (b'{"batch_id":"wrong","batch_id":"expected"}', "batch_id"),
    (b'{"decisions_by_evidence_id":{"row-a":{"decision":"replace"},'
     b'"row-a":{"decision":"accept"}}}', "row-a"),
    (b'{"decisions_by_candidate_ref":{"unit-a":{},"unit-a":{}}}', "unit-a"),
    (b'{"semantic_nodes":[{"semantic_node_key":"n1","semantic_node_key":"n2"}]}',
     "semantic_node_key"),
    (b'{"assignments_by_original_label":{"scent":"g1","sc\\u0065nt":"g2"}}', "scent"),
])
def test_publication_rejects_duplicate_keys_before_callback(
    tmp_path: Path, response: bytes, duplicate_key: str,
) -> None:
    # Executor hashes are honestly bound to the malformed bytes: rejection must
    # be at decoding, not a stale receipt, schema, or downstream identity check.
    kwargs = _completed_attempt(tmp_path, response)
    folder = kwargs["attempt_dir"]
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    called = []
    def accept(value: dict) -> dict:
        called.append(value)
        return {"accepted": True}
    first_usage_bytes = None
    for validator in (accept, None):
        with pytest.raises(ValueError, match=f"duplicate JSON object key '{duplicate_key}'"):
            publish_provider_attempt(**kwargs, validate_response=validator)
        assert not called
        assert not (tmp_path / "responses/answer.json").exists()
        assert all((folder / name).read_bytes() == value for name, value in before.items())
        usage_bytes = (folder / "usage.json").read_bytes()
        assert json.loads(usage_bytes)["response_sha256"] == hashlib.sha256(response).hexdigest()
        if first_usage_bytes is None:
            first_usage_bytes = usage_bytes
        assert usage_bytes == first_usage_bytes


def test_publication_preserves_valid_keyed_response_bytes(tmp_path: Path) -> None:
    # Repeated field names in DIFFERENT objects are legal; source order, BOM,
    # and whitespace must survive publication unchanged.
    response = b'\xef\xbb\xbf{ "decisions_by_evidence_id": {"row-b": {"decision": "accept"}, "row-a": {"decision": "accept"}} }\n'
    kwargs = _completed_attempt(tmp_path, response)
    def check(value: dict) -> dict:
        assert list(value["decisions_by_evidence_id"]) == ["row-b", "row-a"]
        return {"validated_evidence_count": 2}
    published = publish_provider_attempt(**kwargs, validate_response=check)
    assert published["validated_evidence_count"] == 2
    assert Path(published["response_path"]).read_bytes() == response
    assert (kwargs["attempt_dir"] / "response.json").read_bytes() == response


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


def _timeout_attempt(
    tmp_path: Path,
    *,
    name: str,
    messages: list[str],
    started_at: str,
    schema_path: Path | None = None,
    outcome: str = "TIMED_OUT",
) -> tuple[Path, Path]:
    prompt = tmp_path / "prompt.md"
    if not prompt.exists():
        prompt.write_text("bound prompt", encoding="utf-8")
    schema_path = schema_path or tmp_path / "response.schema.json"
    if not schema_path.exists():
        schema_path.write_text(
            json.dumps(
                {
                    "type": "object",
                    "properties": {"answer": {"type": "integer"}},
                    "required": ["answer"],
                    "additionalProperties": False,
                }
            ),
            encoding="utf-8",
        )
    attempt = Path(
        reserve_provider_attempt(
            attempt_root=tmp_path / "timeout-attempts", attempt_id=name
        )["attempt_dir"]
    )
    events = b"".join(
        (
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": message},
                },
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        for message in messages
    )
    stderr = b"retrying sampling request (1/5)\n"
    start = {
        "schema_version": "forseti_provider_execution_started_v1",
        "command": ["codex", "exec"],
        "started_at": started_at,
        "timeout_seconds": 600,
        "prompt_path": str(prompt),
        "prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
        "prompt_bytes": prompt.stat().st_size,
        "response_schema_path": str(schema_path),
        "response_schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
    }
    (attempt / "execution_started.json").write_text(
        json.dumps(start), encoding="utf-8"
    )
    (attempt / "events.jsonl").write_bytes(events)
    (attempt / "stderr.log").write_bytes(stderr)
    receipt = {
        **start,
        "schema_version": "forseti_provider_execution_receipt_v1",
        "outcome": outcome,
        "acceptance_status": "NOT_VALIDATED",
        "events_sha256": hashlib.sha256(events).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "response_sha256": None,
        "response_bytes": 0,
        "usage": None,
        "usage_status": "UNOBSERVED_OR_INCOMPLETE",
    }
    (attempt / "execution_receipt.json").write_text(
        json.dumps(receipt), encoding="utf-8"
    )
    return attempt, schema_path


def test_timeout_recovery_selects_earliest_exact_message_and_preserves_sources(
    tmp_path: Path,
) -> None:
    later, schema = _timeout_attempt(
        tmp_path,
        name="attempt-002",
        messages=['{ "answer": 2 }'],
        started_at="2026-09-02T02:00:00.000000Z",
    )
    earlier, _ = _timeout_attempt(
        tmp_path,
        name="attempt-001",
        messages=['{ "answer": 1 }', '{ "answer": 1 }'],
        started_at="2026-09-02T01:00:00.000000Z",
        schema_path=schema,
    )
    before = {
        path: path.read_bytes()
        for attempt in (earlier, later)
        for path in attempt.iterdir()
    }
    seen: list[int] = []

    def native(response: dict) -> dict:
        seen.append(response["answer"])
        return {"native_answer": response["answer"]}

    result = recover_timed_out_provider_attempt(
        attempt_dirs=[later, earlier],
        response_schema_path=schema,
        recovery_dir=tmp_path / "recovery",
        validate_response=native,
    )
    assert seen == [2, 1]
    assert result["selected_attempt_id"] == "attempt-001"
    assert result["provider_attempt_outcome"] == "TIMED_OUT"
    assert result["provider_attempt_acceptance_status"] == "NOT_VALIDATED"
    assert result["provider_attempt_reclassified"] is False
    assert result["agent_message_count"] == 2
    assert result["distinct_agent_message_count"] == 1
    assert result["identical_retransmission_count"] == 1
    assert result["usage"] is None
    assert result["usage_status"] == "UNOBSERVED"
    assert result["validation"] == {"native_answer": 1}
    assert Path(result["response_path"]).read_bytes() == b'{ "answer": 1 }'
    durable = json.loads(Path(result["recovery_receipt_path"]).read_text())
    assert durable["selected_attempt_id"] == "attempt-001"
    assert durable["selection_rule"].startswith("earliest eligible attempt")
    assert all(path.read_bytes() == value for path, value in before.items())
    with pytest.raises(ValueError, match="refusing to overwrite existing recovery"):
        recover_timed_out_provider_attempt(
            attempt_dirs=[earlier],
            response_schema_path=schema,
            recovery_dir=tmp_path / "recovery",
            validate_response=native,
        )
    assert all(path.read_bytes() == value for path, value in before.items())


def test_timeout_recovery_rejects_nonfinite_json_constants(tmp_path: Path) -> None:
    schema = tmp_path / "nonfinite-response.schema.json"
    schema.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {"answer": {"type": "number"}},
                "required": ["answer"],
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    attempt, _ = _timeout_attempt(
        tmp_path,
        name="nonfinite",
        messages=['{"answer":NaN}'],
        started_at="2026-09-02T01:00:00.000000Z",
        schema_path=schema,
    )

    with pytest.raises(ProviderAttemptRecoveryError) as error:
        inspect_timed_out_provider_attempt(
            attempt_dir=attempt,
            response_schema_path=schema,
            validate_response=lambda value: {},
        )
    assert error.value.code == "MALFORMED_AGENT_MESSAGE_JSON"


def test_timeout_recovery_orders_whole_and_fractional_seconds(
    tmp_path: Path,
) -> None:
    later, schema = _timeout_attempt(
        tmp_path,
        name="fractional-later",
        messages=['{"answer":2}'],
        started_at="2026-09-02T01:00:00.500000Z",
    )
    earlier, _ = _timeout_attempt(
        tmp_path,
        name="whole-second-earlier",
        messages=['{"answer":1}'],
        started_at="2026-09-02T01:00:00Z",
        schema_path=schema,
    )

    result = recover_timed_out_provider_attempt(
        attempt_dirs=[later, earlier],
        response_schema_path=schema,
        recovery_dir=tmp_path / "whole-second-recovery",
        validate_response=lambda value: {"answer": value["answer"]},
    )
    assert result["selected_attempt_id"] == "whole-second-earlier"


def test_timeout_recovery_keeps_unicode_separator_inside_jsonl_string(
    tmp_path: Path,
) -> None:
    schema = tmp_path / "unicode-response.schema.json"
    schema.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {
                    "answer": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["answer", "note"],
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    message = '{"answer":1,"note":"left\u2028right"}'
    attempt, _ = _timeout_attempt(
        tmp_path,
        name="unicode-separator",
        messages=[message],
        started_at="2026-09-02T01:00:00.000000Z",
        schema_path=schema,
    )
    events_path = attempt / "events.jsonl"
    events = events_path.read_bytes().replace(b"\\u2028", "\u2028".encode("utf-8"))
    events_path.write_bytes(events)
    receipt_path = attempt / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["events_sha256"] = hashlib.sha256(events).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    result = inspect_timed_out_provider_attempt(
        attempt_dir=attempt,
        response_schema_path=schema,
        validate_response=lambda value: {"note": value["note"]},
    )
    assert result["validation"] == {"note": "left\u2028right"}


def test_timeout_recovery_rejects_each_bound_failure_at_its_intended_guard(
    tmp_path: Path,
) -> None:
    cases = [
        ("zero", [], "TIMED_OUT", lambda value: {}, "ZERO_AGENT_MESSAGES"),
        (
            "multiple",
            ['{"answer":1}', '{"answer":2}'],
            "TIMED_OUT",
            lambda value: {},
            "MULTIPLE_DISTINCT_AGENT_MESSAGES",
        ),
        (
            "malformed",
            ['{"answer":'],
            "TIMED_OUT",
            lambda value: {},
            "MALFORMED_AGENT_MESSAGE_JSON",
        ),
        (
            "schema",
            ['{"answer":"wrong"}'],
            "TIMED_OUT",
            lambda value: {},
            "RESPONSE_SCHEMA_REJECTED",
        ),
        (
            "native",
            ['{"answer":1}'],
            "TIMED_OUT",
            lambda value: (_ for _ in ()).throw(ValueError("native reject")),
            "NATIVE_VALIDATION_REJECTED",
        ),
        (
            "completed",
            ['{"answer":1}'],
            "PROCESS_COMPLETED",
            lambda value: {},
            "NOT_TIMED_OUT",
        ),
    ]
    schema: Path | None = None
    for index, (name, messages, outcome, native, expected_code) in enumerate(cases):
        attempt, schema = _timeout_attempt(
            tmp_path,
            name=name,
            messages=messages,
            started_at=f"2026-09-02T01:00:{index:02d}.000000Z",
            schema_path=schema,
            outcome=outcome,
        )
        with pytest.raises(ProviderAttemptRecoveryError) as error:
            inspect_timed_out_provider_attempt(
                attempt_dir=attempt,
                response_schema_path=schema,
                validate_response=native,
            )
        assert error.value.code == expected_code

    drifted, schema = _timeout_attempt(
        tmp_path,
        name="drifted",
        messages=['{"answer":1}'],
        started_at="2026-09-02T01:01:00.000000Z",
        schema_path=schema,
    )
    with (drifted / "events.jsonl").open("ab") as handle:
        handle.write(b"{}\n")
    with pytest.raises(ProviderAttemptRecoveryError) as error:
        inspect_timed_out_provider_attempt(
            attempt_dir=drifted,
            response_schema_path=schema,
            validate_response=lambda value: {},
        )
    assert error.value.code == "HASH_DRIFT"
