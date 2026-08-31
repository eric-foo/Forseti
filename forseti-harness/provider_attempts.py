"""Immutable local storage for retryable JSON model-provider attempts.

This module performs filesystem bookkeeping only. It launches no model call and
interprets no evidence semantics; callers supply any stage-specific response
validator before canonical publication.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from harness_utils import hash_file, sha256_bytes


ResponseValidator = Callable[[dict[str, Any]], Mapping[str, Any]]


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
