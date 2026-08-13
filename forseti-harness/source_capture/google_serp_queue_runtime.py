"""Durable, fail-closed control state for Google SERP acquisition queues.

The controller does not capture pages.  It is the executable safety boundary
around whichever admitted primary or persistent-real-Chrome packet runner owns
the actual capture: claim one exact job, report its observed outcome, and never
receive another navigation action while a job is in flight or cooling down.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import get_ident
from typing import Any, Iterator, Mapping
from urllib.parse import parse_qs, urlparse

from runners.serp_egress_cadence import (
    IDLE_SECONDS_MAX,
    rung_after_block,
    should_ping_owner,
    write_owner_ping,
)
from source_capture.google_serp_queue_policy import evaluate_queue_job


JOBS_VERSION = "google_serp_queue_jobs_v1"
STATE_VERSION = "google_serp_queue_state_v1"
AUTOMATED_ROUTE = "primary_route"
PERSISTENT_ROUTE = "persistent_realchrome"
_WINDOWS_FILE_RETRY_ATTEMPTS = 10
_WINDOWS_FILE_RETRY_SECONDS = 0.01


class GoogleSerpQueueError(ValueError):
    pass


def initialize_queue(
    *,
    jobs_path: Path,
    state_path: Path,
    owner_ping_path: Path,
    persistent_fallback_enabled: bool,
    dedicated_logged_out_cdp_ready: bool,
    operator_visible: bool,
    rung: int = 0,
    jobs_since_rungup: int | None = None,
) -> dict[str, Any]:
    document = _read_json(jobs_path, label="jobs")
    if document.get("schema_version") != JOBS_VERSION:
        raise GoogleSerpQueueError(f"jobs schema_version must be {JOBS_VERSION}")
    run_id = _required_text(document, "run_id")
    raw_jobs = document.get("jobs")
    if not isinstance(raw_jobs, list) or not raw_jobs:
        raise GoogleSerpQueueError("jobs must be a non-empty list")
    jobs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_jobs:
        if not isinstance(raw, dict):
            raise GoogleSerpQueueError("every queue job must be an object")
        job = dict(raw)
        job_id = _required_text(job, "job_id")
        if job_id in seen:
            raise GoogleSerpQueueError(f"duplicate job_id: {job_id}")
        seen.add(job_id)
        query = _required_text(job, "query")
        url = _required_text(job, "url")
        _validate_google_url(url=url, query=query)
        eligibility = evaluate_queue_job(job)
        if not eligibility.eligible:
            raise GoogleSerpQueueError(
                f"queue job {job_id} is ineligible: {eligibility.reason}"
            )
        jobs.append(job)
    if not isinstance(rung, int) or isinstance(rung, bool) or rung < 0:
        raise GoogleSerpQueueError("rung must be a non-negative integer")
    if jobs_since_rungup is not None and (
        not isinstance(jobs_since_rungup, int)
        or isinstance(jobs_since_rungup, bool)
        or jobs_since_rungup < 0
    ):
        raise GoogleSerpQueueError(
            "jobs_since_rungup must be null or a non-negative integer"
        )
    state = {
        "schema_version": STATE_VERSION,
        "run_id": run_id,
        "status": "running",
        "jobs": jobs,
        "next_job_index": 0,
        "completed_job_ids": [],
        "failed_job_ids": [],
        "attempt_history": [],
        "held_job_id": None,
        "in_flight": None,
        "pending_route": None,
        "persistent_route_latched": False,
        "cooldown_until": None,
        "recovery_attempted_job_ids": [],
        "blocks_this_run": 0,
        "recent_outcomes": [],
        "rung": rung,
        "jobs_since_rungup": jobs_since_rungup,
        "capabilities": {
            "persistent_fallback_enabled": persistent_fallback_enabled,
            "dedicated_logged_out_cdp_ready": dedicated_logged_out_cdp_ready,
            "operator_visible": operator_visible,
            "cooldown_recovery_available": True,
        },
        "owner_ping_path": str(owner_ping_path.resolve()),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    _write_new_json(state_path, state)
    return state


def next_action(
    *,
    state_path: Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    observed_now = _utc(now)
    with _state_lock(state_path):
        state = _load_state(state_path)
        ping_path = Path(state["owner_ping_path"])
        if ping_path.exists() or state["status"] == "owner_ping":
            return _status_action(state, "owner_ping")
        if state["status"] == "complete":
            return _status_action(state, "complete")
        if state["status"] == "failed":
            return _status_action(state, "failed")
        if state["in_flight"] is not None:
            return {
                **_status_action(state, "waiting_for_report"),
                "in_flight": state["in_flight"],
            }

        pending_route = state.get("pending_route")
        if pending_route == PERSISTENT_ROUTE:
            return _claim_action(
                state_path=state_path,
                state=state,
                route=PERSISTENT_ROUTE,
                attempt_kind="persistent_fallback",
                now=observed_now,
            )

        cooldown_until = state.get("cooldown_until")
        if cooldown_until is not None:
            deadline = _parse_timestamp(cooldown_until)
            if observed_now < deadline:
                return {
                    **_status_action(state, "cooldown"),
                    "cooldown_until": cooldown_until,
                    "wait_seconds": max(
                        0, int((deadline - observed_now).total_seconds())
                    ),
                }
            job_id = state.get("held_job_id")
            if not isinstance(job_id, str):
                raise GoogleSerpQueueError(
                    "cooldown state is missing the exact held job"
                )
            attempted = set(state["recovery_attempted_job_ids"])
            if job_id in attempted:
                raise GoogleSerpQueueError(
                    f"recovery was already attempted for held job {job_id}"
                )
            state["recovery_attempted_job_ids"].append(job_id)
            state["cooldown_until"] = None
            return _claim_action(
                state_path=state_path,
                state=state,
                route=AUTOMATED_ROUTE,
                attempt_kind="cooldown_recovery",
                now=observed_now,
            )

        if state["next_job_index"] >= len(state["jobs"]):
            state["status"] = "complete"
            _atomic_write_json(state_path, state)
            return _status_action(state, "complete")
        # A transition to the operator-visible route is latched for the rest of
        # the run: the flag that produced the block is still live, so the next
        # job must not re-probe the automated route (serp_egress_cadence, F2b).
        latched = state.get("persistent_route_latched") is True
        return _claim_action(
            state_path=state_path,
            state=state,
            route=PERSISTENT_ROUTE if latched else AUTOMATED_ROUTE,
            attempt_kind="persistent_fallback" if latched else "initial",
            now=observed_now,
        )


def report_outcome(
    *,
    state_path: Path,
    job_id: str,
    route: str,
    outcome: str,
    packet_locator: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if outcome not in {"success", "blocked", "failed"}:
        raise GoogleSerpQueueError(
            "outcome must be success, blocked, or failed"
        )
    observed_now = _utc(now)
    with _state_lock(state_path):
        state = _load_state(state_path)
        in_flight = state.get("in_flight")
        if not isinstance(in_flight, dict):
            raise GoogleSerpQueueError("no queue job is in flight")
        if in_flight.get("job_id") != job_id or in_flight.get("route") != route:
            raise GoogleSerpQueueError(
                "reported job and route do not match the in-flight claim"
            )
        if outcome == "blocked" and route == PERSISTENT_ROUTE:
            raise GoogleSerpQueueError(
                "persistent_realchrome owns its block/ping/manual-clear loop; "
                "report only its terminal success or failure"
            )
        state["in_flight"] = None
        state["pending_route"] = None
        if packet_locator is not None:
            in_flight["packet_locator"] = packet_locator
        in_flight["outcome"] = outcome
        in_flight["reported_at"] = _timestamp(observed_now)
        state["attempt_history"].append(in_flight)

        if outcome == "success":
            state["completed_job_ids"].append(job_id)
            state["next_job_index"] += 1
            state["held_job_id"] = None
            state["cooldown_until"] = None
            state["recent_outcomes"].append("ok")
            state["jobs_since_rungup"] = _increment_optional(
                state.get("jobs_since_rungup")
            )
            state["status"] = (
                "complete"
                if state["next_job_index"] >= len(state["jobs"])
                else "running"
            )
            _atomic_write_json(state_path, state)
            return state

        if outcome == "failed":
            state["failed_job_ids"].append(job_id)
            state["held_job_id"] = job_id
            state["status"] = "failed"
            _atomic_write_json(state_path, state)
            return state

        state["blocks_this_run"] += 1
        state["recent_outcomes"].append("blocked")
        new_rung, stepped_down = rung_after_block(
            state["rung"], state.get("jobs_since_rungup")
        )
        state["rung"] = new_rung
        state["jobs_since_rungup"] = None
        state["held_job_id"] = job_id
        ping, consecutive = should_ping_owner(
            state["blocks_this_run"], state["recent_outcomes"]
        )
        if ping:
            reason = (
                "second consecutive automated-route block"
                if consecutive
                else "third automated-route block in this run"
            )
            # Load-bearing ordering: the durable ping exists before the queue
            # can be persisted as terminal. next_action also treats an existing
            # ping as terminal if the later state write is interrupted.
            write_owner_ping(
                state["owner_ping_path"],
                job_id=job_id,
                reason=reason,
                counts={
                    "ok": len(state["completed_job_ids"]),
                    "blocked": state["blocks_this_run"],
                    "failed": len(state["failed_job_ids"]),
                },
                timestamp=_timestamp(observed_now),
                extra={
                    "query": _job_by_id(state, job_id)["query"],
                    "rung": state["rung"],
                    "stepped_down_inside_probation": stepped_down,
                },
            )
            state["status"] = "owner_ping"
            _atomic_write_json(state_path, state)
            return state

        capabilities = state["capabilities"]
        fallback_ready = all(
            capabilities.get(key) is True
            for key in (
                "persistent_fallback_enabled",
                "dedicated_logged_out_cdp_ready",
                "operator_visible",
            )
        )
        if in_flight["attempt_kind"] == "initial" and fallback_ready:
            state["pending_route"] = PERSISTENT_ROUTE
            state["persistent_route_latched"] = True
            state["status"] = "running"
        else:
            state["cooldown_until"] = _timestamp(
                observed_now + timedelta(seconds=IDLE_SECONDS_MAX)
            )
            state["status"] = "cooldown"
        _atomic_write_json(state_path, state)
        return state


def inspect_queue(*, state_path: Path) -> dict[str, Any]:
    return _load_state(state_path)


def _claim_action(
    *,
    state_path: Path,
    state: dict[str, Any],
    route: str,
    attempt_kind: str,
    now: datetime,
) -> dict[str, Any]:
    job_id = state.get("held_job_id")
    if not isinstance(job_id, str):
        job = state["jobs"][state["next_job_index"]]
        job_id = job["job_id"]
        state["held_job_id"] = job_id
    else:
        job = _job_by_id(state, job_id)
    claim = {
        "job_id": job_id,
        "route": route,
        "attempt_kind": attempt_kind,
        "claimed_at": _timestamp(now),
    }
    state["in_flight"] = claim
    state["pending_route"] = None
    state["status"] = "running"
    _atomic_write_json(state_path, state)
    return {
        "status": "capture_ready",
        "run_id": state["run_id"],
        "job": job,
        "route": route,
        "attempt_kind": attempt_kind,
        "rung": state["rung"],
    }


def _status_action(state: Mapping[str, Any], status: str) -> dict[str, Any]:
    return {
        "status": status,
        "run_id": state["run_id"],
        "held_job_id": state.get("held_job_id"),
        "blocks_this_run": state["blocks_this_run"],
        "rung": state["rung"],
    }


def _job_by_id(state: Mapping[str, Any], job_id: str) -> dict[str, Any]:
    for job in state["jobs"]:
        if job["job_id"] == job_id:
            return job
    raise GoogleSerpQueueError(f"held job is missing from the queue: {job_id}")


def _validate_google_url(*, url: str, query: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() not in {
        "google.com",
        "www.google.com",
    }:
        raise GoogleSerpQueueError("queue job URL must be an https google.com URL")
    values = parse_qs(parsed.query).get("q", [])
    if len(values) != 1 or _normalize(values[0]) != _normalize(query):
        raise GoogleSerpQueueError(
            "queue job URL must carry exactly the declared held query"
        )


def _normalize(value: str) -> str:
    return " ".join(value.split()).casefold()


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GoogleSerpQueueError(f"{key} must be a non-empty string")
    return value.strip()


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    for attempt in range(_WINDOWS_FILE_RETRY_ATTEMPTS):
        try:
            text = path.read_text(encoding="utf-8")
            break
        except PermissionError as exc:
            if attempt + 1 == _WINDOWS_FILE_RETRY_ATTEMPTS:
                raise GoogleSerpQueueError(
                    f"{label} JSON could not be read: {exc}"
                ) from exc
            time.sleep(_WINDOWS_FILE_RETRY_SECONDS)
        except Exception as exc:
            raise GoogleSerpQueueError(f"{label} JSON could not be read: {exc}") from exc
    try:
        value = json.loads(text)
    except Exception as exc:
        raise GoogleSerpQueueError(f"{label} JSON could not be read: {exc}") from exc
    if not isinstance(value, dict):
        raise GoogleSerpQueueError(f"{label} JSON must be an object")
    return value


def _load_state(path: Path) -> dict[str, Any]:
    state = _read_json(path, label="queue state")
    if state.get("schema_version") != STATE_VERSION:
        raise GoogleSerpQueueError(
            f"queue state schema_version must be {STATE_VERSION}"
        )
    return state


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    encoded = _json_bytes(value)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise GoogleSerpQueueError(f"queue state already exists: {path}") from exc


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(
        f".{path.name}.tmp.{os.getpid()}.{get_ident()}"
    )
    try:
        with temporary.open("xb") as handle:
            handle.write(_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(_WINDOWS_FILE_RETRY_ATTEMPTS):
            try:
                os.replace(temporary, path)
                return
            except PermissionError:
                if attempt + 1 == _WINDOWS_FILE_RETRY_ATTEMPTS:
                    raise
                time.sleep(_WINDOWS_FILE_RETRY_SECONDS)
    finally:
        temporary.unlink(missing_ok=True)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


@contextmanager
def _state_lock(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_name(f"{state_path.name}.lock")
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise GoogleSerpQueueError(
            f"queue state is already controlled by another process: {lock_path}"
        ) from exc
    os.close(descriptor)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _utc(value: datetime | None) -> datetime:
    observed = value or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        raise GoogleSerpQueueError("timestamps must be timezone-aware")
    return observed.astimezone(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GoogleSerpQueueError(f"invalid queue timestamp: {value!r}") from exc
    return _utc(parsed)


def _increment_optional(value: Any) -> int | None:
    return value + 1 if isinstance(value, int) and not isinstance(value, bool) else None
