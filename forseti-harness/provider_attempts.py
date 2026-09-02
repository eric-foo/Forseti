"""Immutable local storage for retryable JSON model-provider attempts.

This module performs filesystem bookkeeping only. It launches no model call and
interprets no evidence semantics; callers supply any stage-specific response
validator before canonical publication.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from jsonschema import SchemaError, ValidationError
from jsonschema.validators import validator_for

from harness_utils import hash_file, sha256_bytes


ResponseValidator = Callable[[dict[str, Any]], Mapping[str, Any]]


class ProviderAttemptRecoveryError(ValueError):
    """One immutable provider attempt is ineligible for timeout recovery."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Decode one JSON object without silently replacing an earlier decision."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _load_unique_object(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8-sig"),
            object_pairs_hook=unique_json_object,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", f"{label} is unusable: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", f"{label} must be one JSON object"
        )
    return value, raw


def _verified_timeout_candidate(
    *,
    attempt_dir: Path,
    response_schema_path: Path,
    validate_response: ResponseValidator,
) -> dict[str, Any]:
    """Read and validate one candidate without changing the attempt or publishing."""

    required = {
        name: attempt_dir / name
        for name in (
            "execution_started.json",
            "execution_receipt.json",
            "events.jsonl",
            "stderr.log",
        )
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise ProviderAttemptRecoveryError(
            "MISSING_EXECUTION_ARTIFACT", f"missing {', '.join(missing)}"
        )
    started, started_bytes = _load_unique_object(
        required["execution_started.json"], label="execution start receipt"
    )
    execution, execution_bytes = _load_unique_object(
        required["execution_receipt.json"], label="execution receipt"
    )
    if started.get("schema_version") != "forseti_provider_execution_started_v1":
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "unknown execution start receipt schema"
        )
    if execution.get("schema_version") != "forseti_provider_execution_receipt_v1":
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "unknown execution receipt schema"
        )
    if execution.get("outcome") != "TIMED_OUT":
        raise ProviderAttemptRecoveryError(
            "NOT_TIMED_OUT", "provider execution outcome is not TIMED_OUT"
        )
    if execution.get("acceptance_status") != "NOT_VALIDATED":
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID",
            "timed-out execution receipt must remain NOT_VALIDATED",
        )
    if not isinstance(execution.get("started_at"), str):
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "execution receipt lacks a string started_at"
        )
    try:
        datetime.strptime(execution["started_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "execution receipt started_at is not canonical UTC"
        ) from exc
    start_fields = (
        "command",
        "started_at",
        "timeout_seconds",
        "prompt_path",
        "prompt_sha256",
        "prompt_bytes",
        "response_schema_path",
        "response_schema_sha256",
    )
    if any(execution.get(field) != started.get(field) for field in start_fields):
        raise ProviderAttemptRecoveryError(
            "EXECUTION_START_MISMATCH", "execution receipt does not match its start receipt"
        )

    events_bytes = required["events.jsonl"].read_bytes()
    stderr_bytes = required["stderr.log"].read_bytes()
    bound_files: list[tuple[str, bytes, str | None]] = [
        ("events.jsonl", events_bytes, execution.get("events_sha256")),
        ("stderr.log", stderr_bytes, execution.get("stderr_sha256")),
    ]
    response_path = attempt_dir / "response.json"
    response_hash = execution.get("response_sha256")
    if response_path.exists() or response_hash is not None:
        if not response_path.is_file() or not isinstance(response_hash, str):
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", "response.json presence does not match the execution receipt"
            )
        preserved_response_bytes = response_path.read_bytes()
        bound_files.append(("response.json", preserved_response_bytes, response_hash))
        if execution.get("response_bytes") != len(preserved_response_bytes):
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", "response.json size changed after execution"
            )
    elif execution.get("response_bytes") != 0:
        raise ProviderAttemptRecoveryError(
            "HASH_DRIFT", "execution receipt records unbound response bytes"
        )
    for name, raw, expected_hash in bound_files:
        if not isinstance(expected_hash, str) or sha256_bytes(raw) != expected_hash:
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", f"provider execution output changed: {name}"
            )

    for label, path_field, hash_field, size_field in (
        ("prompt", "prompt_path", "prompt_sha256", "prompt_bytes"),
        ("response schema", "response_schema_path", "response_schema_sha256", None),
    ):
        source_value = execution.get(path_field)
        if not isinstance(source_value, str):
            raise ProviderAttemptRecoveryError(
                "EXECUTION_RECEIPT_INVALID", f"execution receipt lacks {label} path"
            )
        source = Path(source_value)
        if not source.is_file():
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", f"bound {label} changed after execution"
            )
        source_bytes = source.read_bytes()
        if sha256_bytes(source_bytes) != execution.get(hash_field):
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", f"bound {label} changed after execution"
            )
        if size_field is not None and len(source_bytes) != execution.get(size_field):
            raise ProviderAttemptRecoveryError(
                "HASH_DRIFT", f"bound {label} size changed after execution"
            )
    if not response_schema_path.is_file():
        raise ProviderAttemptRecoveryError(
            "HASH_DRIFT", "requested response schema does not exist"
        )
    schema_bytes = response_schema_path.read_bytes()
    schema_hash = sha256_bytes(schema_bytes)
    if schema_hash != execution.get("response_schema_sha256"):
        raise ProviderAttemptRecoveryError(
            "HASH_DRIFT", "requested response schema differs from the execution binding"
        )

    messages: list[str] = []
    try:
        event_text = events_bytes.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ProviderAttemptRecoveryError(
            "MALFORMED_EVENT_STREAM", "events.jsonl is not valid UTF-8"
        ) from exc
    for line_number, line in enumerate(event_text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line, object_pairs_hook=unique_json_object)
        except ValueError as exc:
            raise ProviderAttemptRecoveryError(
                "MALFORMED_EVENT_STREAM", f"invalid JSONL event at line {line_number}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise ProviderAttemptRecoveryError(
                "MALFORMED_EVENT_STREAM", f"event at line {line_number} is not an object"
            )
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
        ):
            text = item.get("text")
            if not isinstance(text, str):
                raise ProviderAttemptRecoveryError(
                    "MALFORMED_EVENT_STREAM", "completed agent_message lacks text"
                )
            messages.append(text)
    distinct_messages = list(dict.fromkeys(messages))
    if not distinct_messages:
        raise ProviderAttemptRecoveryError(
            "ZERO_AGENT_MESSAGES", "attempt contains no completed agent_message"
        )
    if len(distinct_messages) != 1:
        raise ProviderAttemptRecoveryError(
            "MULTIPLE_DISTINCT_AGENT_MESSAGES",
            f"attempt contains {len(distinct_messages)} distinct completed agent_message values",
        )
    response_bytes = distinct_messages[0].encode("utf-8")
    try:
        response = json.loads(
            distinct_messages[0], object_pairs_hook=unique_json_object
        )
    except ValueError as exc:
        raise ProviderAttemptRecoveryError(
            "MALFORMED_AGENT_MESSAGE_JSON", f"completed agent_message is not canonical JSON: {exc}"
        ) from exc
    if not isinstance(response, dict):
        raise ProviderAttemptRecoveryError(
            "MALFORMED_AGENT_MESSAGE_JSON", "completed agent_message must be one JSON object"
        )

    try:
        schema = json.loads(
            schema_bytes.decode("utf-8-sig"),
            object_pairs_hook=unique_json_object,
        )
        if not isinstance(schema, dict):
            raise ValueError("schema must be one JSON object")
        validator_type = validator_for(schema)
        validator_type.check_schema(schema)
        validator_type(schema).validate(response)
    except (OSError, UnicodeError, ValueError, SchemaError) as exc:
        raise ProviderAttemptRecoveryError(
            "RESPONSE_SCHEMA_INVALID", f"bound response schema is unusable: {exc}"
        ) from exc
    except ValidationError as exc:
        raise ProviderAttemptRecoveryError(
            "RESPONSE_SCHEMA_REJECTED", f"completed agent_message fails response schema: {exc.message}"
        ) from exc
    try:
        validation = dict(validate_response(response))
    except Exception as exc:
        raise ProviderAttemptRecoveryError(
            "NATIVE_VALIDATION_REJECTED", str(exc)
        ) from exc

    try:
        usage = _codex_usage_from_event_bytes(events_bytes)
    except ValueError:
        usage, usage_status = None, "UNOBSERVED"
    else:
        usage_status = "COMPLETED_TURN_REPORTED"
    if execution.get("usage") != usage:
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "execution receipt usage does not match its events"
        )
    expected_execution_usage_status = (
        "COMPLETED_TURN_REPORTED" if usage is not None else "UNOBSERVED_OR_INCOMPLETE"
    )
    if execution.get("usage_status") != expected_execution_usage_status:
        raise ProviderAttemptRecoveryError(
            "EXECUTION_RECEIPT_INVALID", "execution receipt usage status does not match its events"
        )
    return {
        "attempt_dir": str(attempt_dir),
        "attempt_id": attempt_dir.name,
        "started_at": execution["started_at"],
        "execution_started_sha256": sha256_bytes(started_bytes),
        "execution_receipt_sha256": sha256_bytes(execution_bytes),
        "events_sha256": sha256_bytes(events_bytes),
        "stderr_sha256": sha256_bytes(stderr_bytes),
        "response_schema_sha256": schema_hash,
        "agent_message_count": len(messages),
        "distinct_agent_message_count": len(distinct_messages),
        "identical_retransmission_count": len(messages) - 1,
        "response": response,
        "response_bytes": response_bytes,
        "recovered_response_sha256": sha256_bytes(response_bytes),
        "usage": usage,
        "usage_status": usage_status,
        "provider_attempt_acceptance_status": execution["acceptance_status"],
        "validation": validation,
    }


def inspect_timed_out_provider_attempt(
    *,
    attempt_dir: Path,
    response_schema_path: Path,
    validate_response: ResponseValidator,
) -> dict[str, Any]:
    """Read-only eligibility check for one timed-out immutable attempt."""

    candidate = _verified_timeout_candidate(
        attempt_dir=attempt_dir,
        response_schema_path=response_schema_path,
        validate_response=validate_response,
    )
    return {
        key: value
        for key, value in candidate.items()
        if key not in {"response", "response_bytes"}
    }


def recover_timed_out_provider_attempt(
    *,
    attempt_dirs: Sequence[Path],
    response_schema_path: Path,
    recovery_dir: Path,
    validate_response: ResponseValidator,
) -> dict[str, Any]:
    """Publish the earliest eligible timeout message into one new recovery root."""

    if not attempt_dirs:
        raise ValueError("at least one provider attempt is required")
    if len({str(path.resolve()) for path in attempt_dirs}) != len(attempt_dirs):
        raise ValueError("provider attempt list contains a duplicate directory")
    considered: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    for attempt_dir in attempt_dirs:
        try:
            candidate = _verified_timeout_candidate(
                attempt_dir=attempt_dir,
                response_schema_path=response_schema_path,
                validate_response=validate_response,
            )
        except ProviderAttemptRecoveryError as exc:
            considered.append(
                {
                    "attempt_dir": str(attempt_dir),
                    "attempt_id": attempt_dir.name,
                    "eligibility": "REJECTED",
                    "rejection_code": exc.code,
                    "rejection": str(exc),
                }
            )
        else:
            eligible.append(candidate)
            considered.append(
                {
                    "attempt_dir": str(attempt_dir),
                    "attempt_id": attempt_dir.name,
                    "eligibility": "ELIGIBLE",
                    "started_at": candidate["started_at"],
                    "recovered_response_sha256": candidate["recovered_response_sha256"],
                }
            )
    if not eligible:
        causes = ", ".join(
            f"{row['attempt_id']}={row['rejection_code']}" for row in considered
        )
        raise ProviderAttemptRecoveryError(
            "NO_ELIGIBLE_ATTEMPT", causes or "no attempt was eligible"
        )
    selected = min(eligible, key=lambda row: (row["started_at"], row["attempt_dir"]))
    try:
        recovery_dir.mkdir(parents=True)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing recovery: {recovery_dir}") from exc
    response_path = recovery_dir / "response.json"
    receipt_path = recovery_dir / "recovery_receipt.json"
    _write_new(response_path, selected["response_bytes"])
    receipt = {
        "schema_version": "forseti_provider_timeout_recovery_receipt_v1",
        "status": "RECOVERED_COMPLETED_AGENT_MESSAGE",
        "provider_attempt_outcome": "TIMED_OUT",
        "provider_attempt_acceptance_status": selected[
            "provider_attempt_acceptance_status"
        ],
        "provider_attempt_reclassified": False,
        "selected_attempt_id": selected["attempt_id"],
        "selected_attempt_dir": selected["attempt_dir"],
        "selected_attempt_started_at": selected["started_at"],
        "execution_started_sha256": selected["execution_started_sha256"],
        "execution_receipt_sha256": selected["execution_receipt_sha256"],
        "events_sha256": selected["events_sha256"],
        "stderr_sha256": selected["stderr_sha256"],
        "response_schema_sha256": selected["response_schema_sha256"],
        "agent_message_count": selected["agent_message_count"],
        "distinct_agent_message_count": selected["distinct_agent_message_count"],
        "identical_retransmission_count": selected["identical_retransmission_count"],
        "recovered_response_sha256": selected["recovered_response_sha256"],
        "usage": selected["usage"],
        "usage_status": selected["usage_status"],
        "validation": selected["validation"],
        "selection_rule": "earliest eligible attempt by bound started_at; no semantic comparison",
        "considered_attempts": considered,
        "model_api_calls": 0,
    }
    _write_new(
        receipt_path,
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    return {
        **receipt,
        "response_path": str(response_path),
        "recovery_receipt_path": str(receipt_path),
    }


def reserve_provider_attempt(*, attempt_root: Path, attempt_id: str) -> dict[str, Any]:
    """Atomically reserve one attempt-unique directory before provider launch."""

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if (
        not attempt_id
        or len(attempt_id) > 128
        or attempt_id in {".", ".."}
        or any(character not in allowed for character in attempt_id)
    ):
        raise ValueError("attempt_id must be a safe nonempty filename component")
    attempt_root.mkdir(parents=True, exist_ok=True)
    attempt_dir = attempt_root / attempt_id
    try:
        attempt_dir.mkdir()
    except FileExistsError as exc:
        raise ValueError(f"refusing to reuse provider attempt: {attempt_dir}") from exc
    return {
        "attempt_id": attempt_id,
        "attempt_dir": str(attempt_dir),
        "response_path": str(attempt_dir / "response.json"),
        "events_path": str(attempt_dir / "events.jsonl"),
        "model_api_calls": 0,
    }


def codex_usage_from_events(events_path: Path) -> dict[str, int]:
    """Recover exact completed-turn token fields from one Codex JSONL stream."""

    return _codex_usage_from_event_bytes(events_path.read_bytes())


def _codex_usage_from_event_bytes(events: bytes) -> dict[str, int]:
    completed: list[Mapping[str, Any]] = []
    for line in events.decode("utf-8-sig").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, Mapping) and event.get("type") == "turn.completed":
            usage = event.get("usage")
            if isinstance(usage, Mapping):
                completed.append(usage)
    if len(completed) != 1:
        raise ValueError("attempt events must contain exactly one completed-turn usage")
    usage = completed[0]
    fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    if any(
        isinstance(usage.get(field), bool)
        or not isinstance(usage.get(field), int)
        or usage[field] < 0
        for field in fields
    ):
        raise ValueError("completed-turn usage is incomplete or invalid")
    if (
        usage["cached_input_tokens"] > usage["input_tokens"]
        or usage["reasoning_output_tokens"] > usage["output_tokens"]
    ):
        raise ValueError("completed-turn usage subsets are invalid")
    return {field: usage[field] for field in fields}


def publish_provider_attempt(
    *,
    attempt_dir: Path,
    response_dir: Path,
    canonical_response_name: str,
    usage_schema_version: str,
    validate_response: ResponseValidator | None = None,
) -> dict[str, Any]:
    """Preserve bound usage and publish validated response bytes without replace."""

    if (
        not canonical_response_name
        or Path(canonical_response_name).name != canonical_response_name
        or not canonical_response_name.endswith(".json")
    ):
        raise ValueError("canonical response name must be one JSON filename")
    response_path = attempt_dir / "response.json"
    events_path = attempt_dir / "events.jsonl"
    execution_path = attempt_dir / "execution_receipt.json"
    execution = None
    # Either executor record alone proves the attempt was executor-run, so losing
    # one marker cannot demote a failed attempt back to the historical path.
    if (attempt_dir / "execution_started.json").exists() or execution_path.exists():
        if not execution_path.is_file():
            raise ValueError("provider execution is unfinished; refusing publication")
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        if not isinstance(execution, dict):
            raise ValueError("provider execution receipt is unusable; refusing publication")
        if execution.get("outcome") != "PROCESS_COMPLETED":
            raise ValueError("provider execution did not complete successfully; refusing publication")
    if not response_path.is_file() or not events_path.is_file():
        raise ValueError("attempt must contain response.json and events.jsonl")
    # Bind receipt checks, accounting, validation, and publication to the same
    # bytes. A later source-file write must never substitute unvalidated output.
    response_bytes, events_bytes = response_path.read_bytes(), events_path.read_bytes()
    response_hash, events_hash = sha256_bytes(response_bytes), sha256_bytes(events_bytes)
    if execution is not None:
        stderr_path = attempt_dir / "stderr.log"
        for filename, field, actual in (
            ("response.json", "response_sha256", response_hash),
            ("events.jsonl", "events_sha256", events_hash),
            ("stderr.log", "stderr_sha256", hash_file(stderr_path) if stderr_path.is_file() else None),
        ):
            if actual is None or execution.get(field) != actual:
                raise ValueError(f"provider execution output changed: {filename}")
    usage = _codex_usage_from_event_bytes(events_bytes)
    usage_receipt = {
        "schema_version": usage_schema_version,
        "response_sha256": response_hash,
        "events_sha256": events_hash,
        "usage": usage,
    }
    usage_path = attempt_dir / "usage.json"
    usage_bytes = json.dumps(
        usage_receipt, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    # Validation may have failed after usage was preserved. Reuse only its
    # exact rederived bytes; never restamp a receipt or bypass canonical no-replace.
    if usage_path.exists():
        if usage_path.read_bytes() != usage_bytes:
            raise ValueError("existing usage receipt does not match this attempt")
    else:
        _write_new(usage_path, usage_bytes)
    response = json.loads(
        response_bytes.decode("utf-8-sig"), object_pairs_hook=unique_json_object
    )
    if not isinstance(response, dict):
        raise ValueError("provider response must be one JSON object")
    validation = dict(validate_response(response)) if validate_response else {}

    response_dir.mkdir(parents=True, exist_ok=True)
    target = response_dir / canonical_response_name
    staged = response_dir / (
        f".{canonical_response_name}.{response_hash}.json.tmp"
    )
    _write_new(staged, response_bytes)
    try:
        # The canonical hard link points at a disposable sibling copy, not at
        # the preserved attempt file, so later attempt inspection cannot mutate it.
        os.link(staged, target)
    except FileExistsError as exc:
        staged.unlink(missing_ok=True)
        raise ValueError(f"refusing to overwrite existing response: {target}") from exc
    except OSError as exc:
        staged.unlink(missing_ok=True)
        raise ValueError(
            f"atomic no-replace response publication failed: {target}"
        ) from exc
    try:
        staged.unlink()
    except OSError as exc:
        raise ValueError(
            "response final was published but staged-response cleanup failed: "
            f"{staged}"
        ) from exc
    return {
        **validation,
        "response_path": str(target),
        "attempt_dir": str(attempt_dir),
        "usage_receipt_path": str(attempt_dir / "usage.json"),
        "usage": usage,
        "model_api_calls": 0,
    }
