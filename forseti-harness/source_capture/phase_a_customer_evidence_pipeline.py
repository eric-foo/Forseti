"""Resumable Google-to-Reddit controller for consumer-brand Phase A CO3.

The controller deliberately owns no evidence judgment.  It pipelines successful
Google SERP packets into a run-level Reddit candidate frontier, applies only the
mechanical listing floor, accepts externally authored listing decisions, and
releases admitted exact threads to one source-native capture worker.
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Mapping, NoReturn, Sequence
from urllib.parse import parse_qs, quote_plus, urlsplit

from harness_utils import as_dict, hash_file, sha256_text, utc_now_z_microseconds
from runners.serp_egress_cadence import REST_EVERY, REST_SECONDS, cycle_for
from source_capture.google_serp_content import (
    GOOGLE_SERP_CONTENT_RECORD_VERSION,
    GoogleSerpContentAnomaly,
    build_google_serp_content_record,
)
from source_capture.google_serp_queue_runtime import (
    AUTOMATED_ROUTE,
    JOBS_VERSION,
    PERSISTENT_ROUTE,
    GoogleSerpQueueError,
    initialize_queue,
    inspect_queue,
    next_action,
    report_outcome,
)


CONFIG_VERSION = "phase_a_customer_evidence_pipeline_config_v1"
STATE_VERSION = "phase_a_customer_evidence_pipeline_state_v1"
EVENT_VERSION = "phase_a_customer_evidence_pipeline_event_v1"
DECISIONS_VERSION = "phase_a_customer_evidence_pipeline_decisions_v1"
FAMILY_MANIFEST_VERSION = "phase_a_customer_evidence_query_family_v1"
POLICY_VERSION = "reddit_listing_efficiency_v0"

MANDATORY_FAMILY_KINDS = (
    "balanced_axis_baseline",
    "behavior_consequence_displacement",
    "brandless_exact_product",
    "condition_post_use",
)
TERMINAL_CANDIDATE_STATES = {
    "mechanical_no",
    "adjudicated_no",
    "captured",
    "capture_failed",
    "capture_blocked",
}
SECRET_KEY_PARTS = (
    "password",
    "credential",
    "access_token",
    "refresh_token",
    "api_key",
    "cookie",
    "storage_state",
    "vpn_server",
    "exit_ip",
    "ip_address",
    "proxy_url",
)
REDDIT_HOSTS = {"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"}
REDDIT_THREAD_RE = re.compile(
    r"^/r/(?P<subreddit>[^/]+)/comments/(?P<thread_id>[a-z0-9]+)/(?P<slug>[^/?#]+)?/?$",
    re.IGNORECASE,
)


class PipelineError(ValueError):
    """Fail-visible configuration or state error."""


class PipelineBlocked(PipelineError):
    """Terminally honest runtime block requiring operator or owner action."""


@dataclass(frozen=True)
class CaptureResult:
    outcome: str
    packet_locator: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class PipelinePaths:
    root: Path
    config: Path
    state: Path
    events: Path
    google_jobs: Path
    google_state: Path
    google_owner_ping: Path
    google_packets: Path
    reddit_packets: Path


def pipeline_paths(run_root: Path) -> PipelinePaths:
    root = run_root.resolve()
    return PipelinePaths(
        root=root,
        config=root / "config.json",
        state=root / "state.json",
        events=root / "events.jsonl",
        google_jobs=root / "google" / "jobs.json",
        google_state=root / "google" / "queue_state.json",
        google_owner_ping=root / "google" / "OWNER_PING.json",
        google_packets=root / "google" / "packets",
        reddit_packets=root / "reddit" / "packets",
    )


def load_config(path: Path) -> dict[str, Any]:
    value = _read_json(path, label="pipeline config")
    _validate_config(value)
    return value


def initialize_pipeline(*, config_path: Path, run_root: Path) -> dict[str, Any]:
    config = load_config(config_path)
    paths = pipeline_paths(run_root)
    if paths.root.exists() and any(paths.root.iterdir()):
        raise PipelineError(f"run root must be absent or empty: {paths.root}")
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.google_packets.mkdir(parents=True, exist_ok=True)
    paths.reddit_packets.mkdir(parents=True, exist_ok=True)

    config_bytes = _json_bytes(config)
    paths.config.write_bytes(config_bytes)
    families = [dict(item) for item in config["query_families"]]
    jobs = [dict(job) for family in families for job in family["jobs"]]
    google_document = {
        "schema_version": JOBS_VERSION,
        "run_id": config["run_id"],
        "jobs": jobs,
    }
    paths.google_jobs.parent.mkdir(parents=True, exist_ok=True)
    paths.google_jobs.write_bytes(_json_bytes(google_document))
    google = config["google_route"]
    initialize_queue(
        jobs_path=paths.google_jobs,
        state_path=paths.google_state,
        owner_ping_path=paths.google_owner_ping,
        persistent_fallback_enabled=google["persistent_fallback_enabled"],
        dedicated_logged_out_cdp_ready=google["persistent_fallback_enabled"],
        operator_visible=google["persistent_fallback_enabled"],
        rung=google["cadence_rung"],
    )
    now = utc_now_z_microseconds()
    state = {
        "schema_version": STATE_VERSION,
        "config_sha256": sha256_text(config_bytes.decode("utf-8")),
        "run_id": config["run_id"],
        "commission_id": config["commission_id"],
        "subject_id": config["subject_id"],
        "status": "initialized",
        "created_at": now,
        "updated_at": now,
        "families": families,
        "candidates": {},
        "adjudication_batches": [],
        "reddit_queue": [],
        "in_flight": {"google": None, "reddit": None},
        "in_flight_inspections": {},
        "circuits": {
            "google": {"state": "closed"},
            "reddit": {
                "state": "closed",
                "cooldown_until": None,
                "total_challenges": 0,
                "consecutive_challenges": 0,
            },
        },
        "timing": {
            "co3_started_at": None,
            "google_intervals": [],
            "reddit_intervals": [],
            "co3_finished_at": None,
        },
        "terminal_reason": None,
    }
    _write_new_json(paths.state, state)
    _append_event(paths, state, "pipeline_initialized", {"family_count": len(families)})
    return state


def inspect_pipeline(*, run_root: Path) -> dict[str, Any]:
    paths = pipeline_paths(run_root)
    state = _load_state(paths)
    state["google_queue"] = inspect_queue(state_path=paths.google_state)
    state["metrics"] = timing_metrics(state)
    return state


def import_decisions(*, run_root: Path, decisions_path: Path) -> dict[str, Any]:
    paths = pipeline_paths(run_root)
    document = _read_json(decisions_path, label="listing decisions")
    if document.get("schema_version") != DECISIONS_VERSION:
        raise PipelineError(f"decisions schema_version must be {DECISIONS_VERSION}")
    decisions = document.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise PipelineError("decisions must be a non-empty list")
    if len(decisions) > 21:
        raise PipelineError("one imported decision batch may contain at most 21 rows")

    with _state_guard(paths):
        state = _load_state(paths)
        candidates = state["candidates"]
        imported: list[str] = []
        released: list[str] = []
        for raw in decisions:
            if not isinstance(raw, dict):
                raise PipelineError("every decision must be an object")
            candidate_id = _required_text(raw, "candidate_id")
            candidate = candidates.get(candidate_id)
            if not isinstance(candidate, dict):
                raise PipelineError(f"unknown candidate_id: {candidate_id}")
            if candidate["status"] not in {"adjudication_pending", "borderline_pending"}:
                raise PipelineError(
                    f"candidate {candidate_id} is not awaiting adjudication: {candidate['status']}"
                )
            _validate_listing_decision(raw, candidate)
            decision = dict(raw)
            decision["imported_at"] = utc_now_z_microseconds()
            candidate["listing_decision"] = decision
            imported.append(candidate_id)
            if raw["admission"] == "yes":
                candidate["status"] = "capture_pending"
                state["reddit_queue"].append(
                    {
                        "capture_id": _stable_id("capture", candidate_id),
                        "candidate_id": candidate_id,
                        "canonical_thread_id": candidate["canonical_thread_id"],
                        "url": candidate["canonical_url"],
                        "status": "pending",
                        "attempts": [],
                    }
                )
                released.append(candidate_id)
            elif raw["admission"] == "no":
                candidate["status"] = "adjudicated_no"
                candidate["terminal_reason"] = ";".join(raw["reason_codes"])
            else:
                candidate["status"] = "borderline_pending"
        _mark_decision_batches_imported(state, set(imported))
        _save_state(paths, state)
        _append_event(
            paths,
            state,
            "listing_decisions_imported",
            {"candidate_ids": imported, "capture_released_candidate_ids": released},
        )
    return inspect_pipeline(run_root=run_root)


def append_family(*, run_root: Path, manifest_path: Path) -> dict[str, Any]:
    paths = pipeline_paths(run_root)
    manifest = _read_json(manifest_path, label="query-family manifest")
    _validate_family(manifest, appended=True, repo_root=Path.cwd())
    with _state_guard(paths):
        state = _load_state(paths)
        if any(item["family_id"] == manifest["family_id"] for item in state["families"]):
            raise PipelineError(f"duplicate family_id: {manifest['family_id']}")
        existing_jobs = {
            job["job_id"] for family in state["families"] for job in family["jobs"]
        }
        duplicate = existing_jobs & {job["job_id"] for job in manifest["jobs"]}
        if duplicate:
            raise PipelineError(f"duplicate Google job IDs: {sorted(duplicate)}")
        if inspect_queue(state_path=paths.google_state).get("in_flight") is not None:
            raise PipelineError("cannot append a family while a Google job is in flight")
        state["families"].append(manifest)
        google_document = _read_json(paths.google_jobs, label="Google jobs")
        google_document["jobs"].extend(manifest["jobs"])
        _atomic_write_json(paths.google_jobs, google_document)
        google_state = inspect_queue(state_path=paths.google_state)
        google_state["jobs"].extend(manifest["jobs"])
        if google_state["status"] == "complete":
            google_state["status"] = "running"
        _atomic_write_json(paths.google_state, google_state)
        _save_state(paths, state)
        _append_event(
            paths,
            state,
            "query_family_appended",
            {"family_id": manifest["family_id"], "job_count": len(manifest["jobs"])},
        )
    return inspect_pipeline(run_root=run_root)


def run_pipeline(
    *,
    run_root: Path,
    capture: Callable[[str, Mapping[str, Any], Mapping[str, Any], Path], CaptureResult] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] | None = None,
    random_source: random.Random | None = None,
) -> dict[str, Any]:
    """Run exactly one controller process for this run root."""
    paths = pipeline_paths(run_root)
    with _process_run_guard(paths):
        return _run_pipeline_locked(
            run_root=run_root,
            capture=capture,
            sleep=sleep,
            now=now,
            random_source=random_source,
        )


def _run_pipeline_locked(
    *,
    run_root: Path,
    capture: Callable[[str, Mapping[str, Any], Mapping[str, Any], Path], CaptureResult] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] | None = None,
    random_source: random.Random | None = None,
) -> dict[str, Any]:
    """Run one Google worker and one Reddit worker until terminal or awaiting input."""
    paths = pipeline_paths(run_root)
    config = load_config(paths.config)
    if not _live_attestation_valid(config):
        with _state_guard(paths):
            state = _load_state(paths)
            state["status"] = "blocked"
            state["terminal_reason"] = "BLOCKED_ROTATING_IP_ATTESTATION_MISSING"
            _save_state(paths, state)
            _append_event(
                paths,
                state,
                "pipeline_blocked",
                {"reason": "BLOCKED_ROTATING_IP_ATTESTATION_MISSING"},
            )
        return inspect_pipeline(run_root=run_root)
    capture_func = capture or _execute_capture
    clock = now or (lambda: datetime.now(UTC))
    rng = random_source or random.SystemRandom()
    _reconcile_in_flight(paths)
    with _state_guard(paths):
        state = _load_state(paths)
        if state["status"] in {"owner_ping", "blocked", "complete"}:
            return inspect_pipeline(run_root=run_root)
        if state["timing"]["co3_started_at"] is None:
            state["timing"]["co3_started_at"] = _timestamp(clock())
        state["status"] = "running"
        _save_state(paths, state)

    stop = Event()
    errors: list[BaseException] = []

    def google_worker() -> None:
        try:
            _run_google_worker(paths, config, capture_func, stop, sleep, clock, rng)
        except BaseException as exc:  # preserve worker failure in controller state
            errors.append(exc)
            stop.set()

    def reddit_worker() -> None:
        try:
            _run_reddit_worker(paths, config, capture_func, stop, sleep, clock, rng)
        except BaseException as exc:  # preserve worker failure in controller state
            errors.append(exc)
            stop.set()

    threads = [Thread(target=google_worker, name="phase-a-google-worker"), Thread(target=reddit_worker, name="phase-a-reddit-worker")]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        stop.set()
        for thread in threads:
            thread.join(timeout=10)
        with _state_guard(paths):
            state = _load_state(paths)
            state["status"] = "interrupted_resumable"
            state["terminal_reason"] = "operator_interrupt"
            _save_state(paths, state)
            _append_event(paths, state, "pipeline_interrupted", {})
        return inspect_pipeline(run_root=run_root)

    if errors:
        with _state_guard(paths):
            state = _load_state(paths)
            state["status"] = "blocked"
            state["terminal_reason"] = f"worker_failure:{type(errors[0]).__name__}:{errors[0]}"
            _save_state(paths, state)
            _append_event(paths, state, "pipeline_blocked", {"reason": state["terminal_reason"]})
        if isinstance(errors[0], PipelineBlocked):
            return inspect_pipeline(run_root=run_root)
        raise errors[0]

    _settle_pipeline_status(paths, clock())
    return inspect_pipeline(run_root=run_root)


@contextmanager
def _process_run_guard(paths: PipelinePaths):
    """Hold an OS-backed lock for the whole two-worker controller lifetime."""
    lock_path = paths.root / "process.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            if os.fstat(fd).st_size == 0:
                os.write(fd, b"0")
                os.fsync(fd)
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise PipelineBlocked("BLOCKED_CONCURRENT_PIPELINE_PROCESS") from exc
            unlock = lambda: msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise PipelineBlocked("BLOCKED_CONCURRENT_PIPELINE_PROCESS") from exc
            unlock = lambda: fcntl.flock(fd, fcntl.LOCK_UN)
        try:
            yield
        finally:
            os.lseek(fd, 0, os.SEEK_SET)
            unlock()
    finally:
        os.close(fd)


def canonical_reddit_thread(url: str) -> dict[str, str] | None:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme not in {"http", "https"} or host not in REDDIT_HOSTS:
        return None
    match = REDDIT_THREAD_RE.fullmatch(parsed.path)
    if match is None:
        return None
    subreddit = match.group("subreddit")
    thread_id = match.group("thread_id").casefold()
    slug = match.group("slug") or "thread"
    return {
        "canonical_thread_id": thread_id,
        "canonical_url": f"https://old.reddit.com/r/{subreddit}/comments/{thread_id}/{slug}/",
        "subreddit": subreddit,
    }


def ingest_google_packet(
    *, state: dict[str, Any], job: Mapping[str, Any], packet_locator: Path
) -> list[str]:
    record = _load_google_content_record(packet_locator)
    if record.get("content_record_version") != GOOGLE_SERP_CONTENT_RECORD_VERSION:
        raise PipelineBlocked("Google packet lacks google_serp_content_v3")
    _validate_google_record_locale(record, job)
    discovered: list[str] = []
    for index, raw_row in enumerate(record.get("rows", [])):
        if not isinstance(raw_row, dict):
            continue
        url = raw_row.get("canonical_url")
        if not isinstance(url, str):
            continue
        canonical = canonical_reddit_thread(url)
        if canonical is None:
            continue
        candidate_id = _stable_id("candidate", canonical["canonical_thread_id"])
        candidate = state["candidates"].get(candidate_id)
        if candidate is None:
            count = _visible_comment_count(raw_row)
            if count is not None and count <= 3:
                status = "mechanical_no"
                terminal_reason = "visible_comments_0_3"
            elif count is None:
                status = "borderline_pending"
                terminal_reason = None
            else:
                status = "adjudication_pending"
                terminal_reason = None
            candidate = {
                "candidate_id": candidate_id,
                **canonical,
                "status": status,
                "terminal_reason": terminal_reason,
                "visible_comment_count": count,
                "discoveries": [],
                "listing_snapshot": {
                    "captured_at": utc_now_z_microseconds(),
                    "score": raw_row.get("score"),
                    "comments": count,
                    "row_sha256": sha256_text(json.dumps(raw_row, sort_keys=True)),
                },
                "listing_decision": None,
                "capture": None,
            }
            state["candidates"][candidate_id] = candidate
        candidate["discoveries"].append(
            {
                "job_id": job["job_id"],
                "family_id": job["family_id"],
                "family_kind": job["family_kind"],
                "result_row_index": index,
                "packet_locator": str(packet_locator.resolve()),
            }
        )
        discovered.append(candidate_id)
    return discovered


def timing_metrics(state: Mapping[str, Any]) -> dict[str, Any]:
    google = _interval_union(as_dict(state.get("timing")).get("google_intervals", []))
    reddit = _interval_union(as_dict(state.get("timing")).get("reddit_intervals", []))
    start_text = as_dict(state.get("timing")).get("co3_started_at")
    end_text = as_dict(state.get("timing")).get("co3_finished_at")
    if not isinstance(start_text, str) or not isinstance(end_text, str):
        return {
            "actual_co3_elapsed_seconds": None,
            "cross_host_overlap_seconds": _intersection_seconds(google, reddit),
            "serial_counterfactual_seconds": None,
            "reduction": None,
            "google_active_seconds": _total_seconds(google),
            "reddit_active_seconds": _total_seconds(reddit),
        }
    elapsed = (_parse_time(end_text) - _parse_time(start_text)).total_seconds()
    overlap = _intersection_seconds(google, reddit)
    serial = elapsed + overlap
    return {
        "actual_co3_elapsed_seconds": elapsed,
        "cross_host_overlap_seconds": overlap,
        "serial_counterfactual_seconds": serial,
        "reduction": 0.0 if serial <= 0 else 1.0 - elapsed / serial,
        "google_active_seconds": _total_seconds(google),
        "reddit_active_seconds": _total_seconds(reddit),
        "google_utilization": 0.0 if elapsed <= 0 else _total_seconds(google) / elapsed,
        "reddit_utilization": 0.0 if elapsed <= 0 else _total_seconds(reddit) / elapsed,
    }


def _run_google_worker(
    paths: PipelinePaths,
    config: Mapping[str, Any],
    capture: Callable[[str, Mapping[str, Any], Mapping[str, Any], Path], CaptureResult],
    stop: Event,
    sleep: Callable[[float], None],
    clock: Callable[[], datetime],
    rng: random.Random,
) -> None:
    completed_this_process = 0
    while not stop.is_set():
        action = next_action(state_path=paths.google_state, now=clock())
        status = action["status"]
        if status in {"complete", "failed", "owner_ping", "waiting_for_report"}:
            if status == "owner_ping":
                with _state_guard(paths):
                    state = _load_state(paths)
                    state["circuits"]["google"]["state"] = "owner_ping"
                    state["status"] = "owner_ping"
                    state["terminal_reason"] = "google_owner_ping"
                    _save_state(paths, state)
                stop.set()
            return
        if status == "cooldown":
            sleep(min(float(action["wait_seconds"]), 1.0))
            continue
        job = action["job"]
        output = paths.google_packets / job["job_id"]
        started = clock()
        with _state_guard(paths):
            state = _load_state(paths)
            state["in_flight"]["google"] = {
                "job_id": job["job_id"], "route": action["route"], "output": str(output),
                "started_at": _timestamp(started),
            }
            _save_state(paths, state)
        result = capture("google", action, config, output)
        finished = clock()
        outcome = result.outcome
        if outcome not in {"success", "blocked", "failed"}:
            raise PipelineError(f"unknown Google capture outcome: {outcome}")
        report_outcome(
            state_path=paths.google_state,
            job_id=job["job_id"],
            route=action["route"],
            outcome=outcome,
            packet_locator=result.packet_locator,
            now=finished,
        )
        with _state_guard(paths):
            state = _load_state(paths)
            state["timing"]["google_intervals"].append(
                {"start": _timestamp(started), "end": _timestamp(finished), "job_id": job["job_id"]}
            )
            state["in_flight"]["google"] = None
            if outcome == "success":
                discovered = ingest_google_packet(
                    state=state, job=job, packet_locator=Path(result.packet_locator or output)
                )
                _flush_full_adjudication_batches(state, family_id=job["family_id"])
                _append_event(paths, state, "google_job_succeeded", {"job_id": job["job_id"], "candidate_ids": discovered})
            else:
                _append_event(paths, state, f"google_job_{outcome}", {"job_id": job["job_id"], "detail": result.detail})
            if _family_terminal(paths, job["family_id"]):
                _flush_adjudication_batch(state, family_id=job["family_id"])
            _save_state(paths, state)
        if outcome != "success":
            continue
        completed_this_process += 1
        cadence = config["google_route"]
        delay = cycle_for(cadence["cadence_rung"]) + rng.uniform(
            cadence["jitter_seconds_min"], cadence["jitter_seconds_max"]
        )
        sleep(max(0.0, delay))
        if completed_this_process % REST_EVERY == 0:
            sleep(float(REST_SECONDS))


def _run_reddit_worker(
    paths: PipelinePaths,
    config: Mapping[str, Any],
    capture: Callable[[str, Mapping[str, Any], Mapping[str, Any], Path], CaptureResult],
    stop: Event,
    sleep: Callable[[float], None],
    clock: Callable[[], datetime],
    rng: random.Random,
) -> None:
    while not stop.is_set():
        with _state_guard(paths):
            state = _load_state(paths)
            circuit = state["circuits"]["reddit"]
            if circuit["state"] == "owner_ping":
                stop.set()
                return
            cooldown = circuit.get("cooldown_until")
            if isinstance(cooldown, str) and clock() < _parse_time(cooldown):
                wait = min((_parse_time(cooldown) - clock()).total_seconds(), 1.0)
                job = None
            else:
                if cooldown is not None:
                    circuit["state"] = "closed"
                    circuit["cooldown_until"] = None
                job = next((item for item in state["reddit_queue"] if item["status"] == "pending"), None)
                if job is not None:
                    job["status"] = "in_flight"
                    job["started_at"] = _timestamp(clock())
                    state["in_flight"]["reddit"] = {
                        "capture_id": job["capture_id"], "candidate_id": job["candidate_id"],
                        "output": str(paths.reddit_packets / job["capture_id"]), "started_at": job["started_at"],
                    }
                wait = 0.0
            google_terminal = inspect_queue(state_path=paths.google_state)["status"] in {"complete", "failed", "owner_ping"}
            if job is None and google_terminal:
                _save_state(paths, state)
                return
            _save_state(paths, state)
        if job is None:
            sleep(max(0.05, wait))
            continue
        output = paths.reddit_packets / job["capture_id"]
        started = clock()
        result = capture("reddit", job, config, output)
        finished = clock()
        with _state_guard(paths):
            state = _load_state(paths)
            live_job = next(item for item in state["reddit_queue"] if item["capture_id"] == job["capture_id"])
            candidate = state["candidates"][job["candidate_id"]]
            live_job["attempts"].append(
                {"started_at": _timestamp(started), "finished_at": _timestamp(finished), "outcome": result.outcome, "detail": result.detail, "packet_locator": result.packet_locator}
            )
            state["timing"]["reddit_intervals"].append(
                {"start": _timestamp(started), "end": _timestamp(finished), "capture_id": job["capture_id"]}
            )
            state["in_flight"]["reddit"] = None
            circuit = state["circuits"]["reddit"]
            if result.outcome == "success":
                live_job["status"] = "captured"
                candidate["status"] = "captured"
                candidate["capture"] = {"capture_id": job["capture_id"], "packet_locator": result.packet_locator, "captured_at": _timestamp(finished)}
                circuit["consecutive_challenges"] = 0
            elif result.outcome == "transport_interruption" and len(live_job["attempts"]) == 1:
                live_job["status"] = "pending"
            elif result.outcome == "challenge":
                live_job["status"] = "capture_blocked"
                candidate["status"] = "capture_blocked"
                candidate["terminal_reason"] = result.detail or "reddit_challenge"
                circuit["total_challenges"] += 1
                circuit["consecutive_challenges"] += 1
                if circuit["consecutive_challenges"] >= 2 or circuit["total_challenges"] >= 3:
                    circuit["state"] = "owner_ping"
                    state["status"] = "owner_ping"
                    state["terminal_reason"] = "reddit_challenge_ceiling"
                    stop.set()
                else:
                    circuit["state"] = "cooldown"
                    circuit["cooldown_until"] = _timestamp(
                        finished + timedelta(seconds=config["reddit_route"]["first_cooldown_seconds"])
                    )
            else:
                live_job["status"] = "capture_failed"
                candidate["status"] = "capture_failed"
                candidate["terminal_reason"] = result.detail or result.outcome
                circuit["consecutive_challenges"] = 0
            _save_state(paths, state)
            _append_event(paths, state, "reddit_capture_settled", {"capture_id": job["capture_id"], "outcome": result.outcome})
        if result.outcome == "success":
            sleep(rng.uniform(config["reddit_route"]["pacing_seconds_min"], config["reddit_route"]["pacing_seconds_max"]))


def _execute_capture(
    worker: str,
    action: Mapping[str, Any],
    config: Mapping[str, Any],
    output: Path,
) -> CaptureResult:
    output.parent.mkdir(parents=True, exist_ok=True)
    if worker == "google":
        job = action["job"]
        if action["route"] == AUTOMATED_ROUTE:
            command = [
                sys.executable, str(_harness_root() / "runners" / "run_source_capture_cloakbrowser_packet.py"),
                "--url", job["url"], "--source-family", "search_discovery",
                "--source-surface", "google_serp_us_parameterized",
                "--decision-question", config["decision_question"], "--output", str(output),
                "--retention-mode", "content", "--block-heavy-assets",
            ]
        else:
            route = config["google_route"]
            command = [
                sys.executable, str(_harness_root() / "runners" / "run_google_serp_persistent_fallback_packet.py"),
                "--url", job["url"], "--query", job["query"], "--job-id", job["job_id"],
                "--output", str(output), "--block-archive", str(output.parent / "blocks"),
                "--cdp-endpoint", route["persistent_cdp_endpoint"],
                "--persistent-tab-marker", route["persistent_tab_marker"],
                "--decision-question", config["decision_question"],
            ]
            if route.get("persistent_session_profile") is not None:
                command.extend(
                    ["--session-profile", route["persistent_session_profile"]]
                )
    else:
        route = config["reddit_route"]
        command = [
            sys.executable, str(_harness_root() / "runners" / "run_source_capture_realchrome_cdp_packet.py"),
            "--url", action["url"], "--source-family", "reddit",
            "--source-surface", "reddit_thread_old_reddit_realchrome_cdp",
            "--decision-question", config["decision_question"], "--output", str(output),
            "--cdp-endpoint", route["cdp_endpoint"], "--persistent-tab-marker", route["persistent_tab_marker"],
            "--scroll-step-px", "700", "--scroll-passes", "2",
        ]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(command, capture_output=True, text=True, creationflags=flags, check=False)
    detail = (completed.stderr or completed.stdout).strip()[-2000:]
    if completed.returncode == 0:
        access_block_reason = _packet_access_block_reason(output, worker=worker)
        if access_block_reason is not None:
            return CaptureResult(
                "blocked" if worker == "google" else "challenge",
                str(output.resolve()),
                access_block_reason,
            )
        return CaptureResult("success", str(output.resolve()), detail)
    lowered = detail.casefold()
    if any(marker in lowered for marker in ("captcha", "429", "unusual traffic", "access blocked", "challenge")):
        return CaptureResult("blocked" if worker == "google" else "challenge", str(output.resolve()) if output.exists() else None, detail)
    if worker == "reddit" and any(
        marker in lowered
        for marker in (
            "timeout",
            "connection reset",
            "econnrefused",
            "could not attach",
            "tunnel",
            "transport",
        )
    ):
        return CaptureResult("transport_interruption", str(output.resolve()) if output.exists() else None, detail)
    return CaptureResult("failed", str(output.resolve()) if output.exists() else None, detail)


def _validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != CONFIG_VERSION:
        raise PipelineError(f"config schema_version must be {CONFIG_VERSION}")
    _reject_secrets(config)
    for key in ("run_id", "commission_id", "subject_id", "decision_question", "artifact_root"):
        _required_text(config, key)
    if config.get("country") != "US" or config.get("language") != "en" or config.get("locale") != "en-US":
        raise PipelineError("Phase A dogfood locale must be country=US, language=en, locale=en-US")
    if not isinstance(config.get("rotating_ip_operator_enabled"), bool):
        raise PipelineError("rotating_ip_operator_enabled must be a boolean")
    attested_at = config.get("operator_attested_at")
    if config["rotating_ip_operator_enabled"] is True:
        _parse_time(_required_text(config, "operator_attested_at"))
    elif attested_at is not None:
        raise PipelineError("operator_attested_at must be null when Rotating IP is not attested")
    families = config.get("query_families")
    if not isinstance(families, list) or len(families) < 4:
        raise PipelineError("query_families must contain the four mandatory families")
    kinds = tuple(item.get("family_kind") for item in families[:4] if isinstance(item, dict))
    if kinds != MANDATORY_FAMILY_KINDS:
        raise PipelineError(f"first four family kinds must be {MANDATORY_FAMILY_KINDS}")
    seen_jobs: set[str] = set()
    for family in families:
        _validate_family(family, appended=False, repo_root=Path.cwd())
        for job in family["jobs"]:
            if job["job_id"] in seen_jobs:
                raise PipelineError(f"duplicate Google job ID: {job['job_id']}")
            seen_jobs.add(job["job_id"])
    google = as_dict(config.get("google_route"))
    if google.get("runner") != "cloakbrowser_google_serp_queue":
        raise PipelineError("google_route.runner must reuse cloakbrowser_google_serp_queue")
    if google.get("cadence_rung") != 8:
        raise PipelineError("Google must start at the existing 60/hour cadence rung 8")
    for key in ("jitter_seconds_min", "jitter_seconds_max"):
        if not isinstance(google.get(key), (int, float)):
            raise PipelineError(f"google_route.{key} must be numeric")
    reddit = as_dict(config.get("reddit_route"))
    if reddit.get("runner") != "realchrome_cdp_persistent_tab":
        raise PipelineError("reddit_route.runner must reuse realchrome_cdp_persistent_tab")
    if reddit.get("pacing_seconds_min") != 44 or reddit.get("pacing_seconds_max") != 61:
        raise PipelineError("Reddit pacing must be exactly the commissioned 44-61 seconds")
    if reddit.get("first_cooldown_seconds") != 1200:
        raise PipelineError("Reddit first cooldown must be 1200 seconds")
    reddit_endpoint = _loopback_cdp_endpoint(_required_text(reddit, "cdp_endpoint"))
    _required_text(reddit, "persistent_tab_marker")
    if google.get("persistent_fallback_enabled") is True:
        google_endpoint = _loopback_cdp_endpoint(_required_text(google, "persistent_cdp_endpoint"))
        _required_text(google, "persistent_tab_marker")
        if google.get("persistent_session_profile") is not None:
            _required_text(google, "persistent_session_profile")
        if google_endpoint == reddit_endpoint:
            raise PipelineError("BLOCKED_SHARED_CDP_CONCURRENCY: Google and Reddit endpoints must differ")


def _validate_family(family: Mapping[str, Any], *, appended: bool, repo_root: Path) -> None:
    if family.get("schema_version") != FAMILY_MANIFEST_VERSION:
        raise PipelineError(f"family schema_version must be {FAMILY_MANIFEST_VERSION}")
    _required_text(family, "family_id")
    _required_text(family, "family_kind")
    if not isinstance(family.get("axis_scope"), list) or not family["axis_scope"]:
        raise PipelineError("family axis_scope must be a non-empty list")
    _required_text(family, "rationale")
    jobs = family.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise PipelineError("family jobs must be a non-empty list")
    for job in jobs:
        if not isinstance(job, dict):
            raise PipelineError("every family job must be an object")
        _required_text(job, "job_id")
        query = _required_text(job, "query")
        _validate_google_job_url(_required_text(job, "url"), query)
        if job.get("family_id") != family["family_id"] or job.get("family_kind") != family["family_kind"]:
            raise PipelineError("every Google job must bind its immutable family ID and kind")
        job.setdefault("selected_type", "subject")
        job.setdefault("selected_name", "phase_a_subject")
        job.setdefault("shape", "phase_a_customer_evidence")
    if appended:
        receipt = as_dict(family.get("authorization_receipt"))
        path_text = _required_text(receipt, "path")
        expected = _required_text(receipt, "sha256").casefold()
        receipt_path = Path(path_text)
        if not receipt_path.is_absolute():
            receipt_path = repo_root / receipt_path
        if not receipt_path.is_file() or hash_file(receipt_path).casefold() != expected:
            raise PipelineError("appended family authorization receipt is missing or hash-mismatched")
        if receipt.get("axis_scope") != family["axis_scope"] or receipt.get("rationale") != family["rationale"]:
            raise PipelineError("appended family must preserve receipt axis_scope and rationale")


def _validate_listing_decision(decision: Mapping[str, Any], candidate: Mapping[str, Any]) -> None:
    if decision.get("policy_version") != POLICY_VERSION:
        raise PipelineError(f"policy_version must be {POLICY_VERSION}")
    if decision.get("admission") not in {"yes", "borderline", "no"}:
        raise PipelineError("admission must be yes, borderline, or no")
    if not isinstance(decision.get("reason_codes"), list) or not decision["reason_codes"]:
        raise PipelineError("reason_codes must be a non-empty list")
    if decision.get("priority_band") not in {"high", "normal", "suppressed"}:
        raise PipelineError("priority_band must be high, normal, or suppressed")
    if decision.get("thread_url") != candidate["canonical_url"]:
        raise PipelineError("decision thread_url must equal the canonical candidate URL")
    if not isinstance(decision.get("decision_frame"), str) or not decision["decision_frame"].strip():
        raise PipelineError("decision_frame is required")
    if decision["admission"] == "borderline" and decision["priority_band"] == "suppressed":
        raise PipelineError("borderline cannot be suppressed")
    if decision["admission"] == "no" and decision["priority_band"] != "suppressed":
        raise PipelineError("no decisions must use priority_band suppressed")


def _live_attestation_valid(config: Mapping[str, Any]) -> bool:
    if config.get("rotating_ip_operator_enabled") is not True:
        return False
    try:
        _parse_time(_required_text(config, "operator_attested_at"))
    except PipelineError:
        return False
    return (
        config.get("country") == "US"
        and config.get("language") == "en"
        and config.get("locale") == "en-US"
    )


def _reconcile_in_flight(paths: PipelinePaths) -> None:
    config = load_config(paths.config)
    with _state_guard(paths):
        state = _load_state(paths)
        reconciled_any = False

        def block_unknown(*, worker: str, claim_id: str) -> NoReturn:
            state["status"] = "blocked"
            state["terminal_reason"] = "BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"
            _save_state(paths, state)
            _append_event(
                paths,
                state,
                "in_flight_outcome_unknown",
                {"worker": worker, "claim_id": claim_id},
            )
            raise PipelineBlocked("BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN")

        queue_claim = inspect_queue(state_path=paths.google_state).get("in_flight")
        controller_claim = state.get("in_flight", {}).get("google")
        if isinstance(queue_claim, dict) and (
            not isinstance(controller_claim, dict)
            or controller_claim.get("job_id") != queue_claim.get("job_id")
        ):
            # A crash between the queue claim and the controller-state write
            # otherwise leaves Google waiting for a report while Reddit spins.
            block_unknown(
                worker="google",
                claim_id=str(queue_claim.get("job_id") or "unknown_google_claim"),
            )

        for worker, claim in state.get("in_flight", {}).items():
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("job_id") or claim.get("capture_id")
            if state["in_flight_inspections"].get(claim_id):
                raise PipelineBlocked("BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN")
            state["in_flight_inspections"][claim_id] = utc_now_z_microseconds()
            output = Path(_required_text(claim, "output"))
            terminal = _packet_terminal(output)
            if not terminal:
                block_unknown(worker=worker, claim_id=claim_id)
            if worker == "google":
                queue = inspect_queue(state_path=paths.google_state)
                queue_claim = queue.get("in_flight")
                if isinstance(queue_claim, dict) and queue_claim.get("job_id") == claim_id:
                    queue_route = queue_claim["route"]
                    report_outcome(
                        state_path=paths.google_state,
                        job_id=claim_id,
                        route=queue_route,
                        outcome="success",
                        packet_locator=str(output.resolve()),
                    )
                    queue = inspect_queue(state_path=paths.google_state)
                elif claim_id not in queue.get("completed_job_ids", []):
                    block_unknown(worker=worker, claim_id=claim_id)
                job = next(
                    (item for item in queue["jobs"] if item["job_id"] == claim_id),
                    None,
                )
                if not isinstance(job, dict):
                    block_unknown(worker=worker, claim_id=claim_id)
                ingest_google_packet(state=state, job=job, packet_locator=output)
                attempt = next(
                    (
                        item
                        for item in reversed(queue.get("attempt_history", []))
                        if item.get("job_id") == claim_id
                        and item.get("outcome") == "success"
                    ),
                    None,
                )
                if not isinstance(attempt, dict) or not isinstance(
                    attempt.get("reported_at"), str
                ):
                    block_unknown(worker=worker, claim_id=claim_id)
                if not any(
                    interval.get("job_id") == claim_id
                    for interval in state["timing"]["google_intervals"]
                ):
                    state["timing"]["google_intervals"].append(
                        {
                            "start": _required_text(claim, "started_at"),
                            "end": attempt["reported_at"],
                            "job_id": claim_id,
                        }
                    )
            elif worker == "reddit":
                live_job = next(
                    (
                        item
                        for item in state["reddit_queue"]
                        if item["capture_id"] == claim_id
                    ),
                    None,
                )
                if not isinstance(live_job, dict) or not any(output.rglob("manifest.json")):
                    block_unknown(worker=worker, claim_id=claim_id)
                candidate = state["candidates"].get(live_job["candidate_id"])
                if not isinstance(candidate, dict):
                    block_unknown(worker=worker, claim_id=claim_id)
                settled_at = utc_now_z_microseconds()
                access_block_reason = _packet_access_block_reason(
                    output, worker="reddit"
                )
                if access_block_reason is None:
                    live_job["status"] = "captured"
                    candidate["status"] = "captured"
                    candidate["capture"] = {
                        "capture_id": claim_id,
                        "packet_locator": str(output.resolve()),
                        "captured_at": settled_at,
                        "resume_inspected": True,
                    }
                else:
                    # A held packet that never reached its thread is a challenge,
                    # not evidence.  Resume applies the same verdict the live
                    # worker applies, so an interrupted run cannot bank what a
                    # completed run would have refused.
                    live_job["status"] = "capture_blocked"
                    live_job["attempts"].append(
                        {
                            "started_at": _required_text(claim, "started_at"),
                            "finished_at": settled_at,
                            "outcome": "challenge",
                            "detail": access_block_reason,
                            "packet_locator": str(output.resolve()),
                            "resume_inspected": True,
                        }
                    )
                    candidate["status"] = "capture_blocked"
                    candidate["terminal_reason"] = access_block_reason
                    circuit = state["circuits"]["reddit"]
                    circuit["total_challenges"] += 1
                    circuit["consecutive_challenges"] += 1
                    if (
                        circuit["consecutive_challenges"] >= 2
                        or circuit["total_challenges"] >= 3
                    ):
                        circuit["state"] = "owner_ping"
                        state["status"] = "owner_ping"
                        state["terminal_reason"] = "reddit_challenge_ceiling"
                    else:
                        circuit["state"] = "cooldown"
                        circuit["cooldown_until"] = _timestamp(
                            _parse_time(settled_at)
                            + timedelta(
                                seconds=config["reddit_route"][
                                    "first_cooldown_seconds"
                                ]
                            )
                        )
            else:
                block_unknown(worker=worker, claim_id=claim_id)
            state["in_flight"][worker] = None
            reconciled_any = True
            _append_event(
                paths,
                state,
                "in_flight_terminal_reconciled",
                {"worker": worker, "claim_id": claim_id},
            )
        if (
            reconciled_any
            and state.get("status") == "blocked"
            and str(state.get("terminal_reason", "")).startswith("worker_failure:")
        ):
            state["status"] = "interrupted_resumable"
            state["terminal_reason"] = None
        _save_state(paths, state)


def _settle_pipeline_status(paths: PipelinePaths, now: datetime) -> None:
    with _state_guard(paths):
        state = _load_state(paths)
        if state["status"] == "owner_ping":
            return
        google_status = inspect_queue(state_path=paths.google_state)["status"]
        unresolved = [c for c in state["candidates"].values() if c["status"] in {"adjudication_pending", "borderline_pending"}]
        reddit_pending = [j for j in state["reddit_queue"] if j["status"] in {"pending", "in_flight"}]
        if google_status == "complete" and not unresolved and not reddit_pending:
            state["status"] = "complete"
            state["timing"]["co3_finished_at"] = _timestamp(now)
        elif unresolved:
            state["status"] = "waiting_for_decisions"
        else:
            state["status"] = "resumable"
        _save_state(paths, state)


def _flush_adjudication_batch(state: dict[str, Any], *, family_id: str) -> None:
    already_batched = {candidate_id for batch in state["adjudication_batches"] for candidate_id in batch["candidate_ids"]}
    pending = [
        candidate_id for candidate_id, candidate in state["candidates"].items()
        if candidate["status"] in {"adjudication_pending", "borderline_pending"}
        and candidate_id not in already_batched
        and any(item["family_id"] == family_id for item in candidate["discoveries"])
    ]
    for index in range(0, len(pending), 21):
        ids = pending[index:index + 21]
        state["adjudication_batches"].append(
            {"batch_id": _stable_id("adjudication", family_id, str(len(state["adjudication_batches"]))), "family_id": family_id, "candidate_ids": ids, "status": "pending", "created_at": utc_now_z_microseconds()}
        )


def _flush_full_adjudication_batches(state: dict[str, Any], *, family_id: str) -> None:
    """Publish each full 21-row decision batch before its family terminates."""
    already_batched = {
        candidate_id
        for batch in state["adjudication_batches"]
        for candidate_id in batch["candidate_ids"]
    }
    pending = [
        candidate_id
        for candidate_id, candidate in state["candidates"].items()
        if candidate["status"] in {"adjudication_pending", "borderline_pending"}
        and candidate_id not in already_batched
        and any(item["family_id"] == family_id for item in candidate["discoveries"])
    ]
    while len(pending) >= 21:
        ids, pending = pending[:21], pending[21:]
        state["adjudication_batches"].append(
            {
                "batch_id": _stable_id(
                    "adjudication", family_id, str(len(state["adjudication_batches"]))
                ),
                "family_id": family_id,
                "candidate_ids": ids,
                "status": "pending",
                "created_at": utc_now_z_microseconds(),
            }
        )


def _mark_decision_batches_imported(state: dict[str, Any], imported: set[str]) -> None:
    for batch in state["adjudication_batches"]:
        if set(batch["candidate_ids"]).issubset(imported | {
            candidate_id for candidate_id in batch["candidate_ids"]
            if state["candidates"][candidate_id]["status"] not in {"adjudication_pending", "borderline_pending"}
        }):
            batch["status"] = "imported"


def _family_terminal(paths: PipelinePaths, family_id: str) -> bool:
    state = inspect_queue(state_path=paths.google_state)
    family_jobs = {job["job_id"] for job in state["jobs"] if job.get("family_id") == family_id}
    terminal = set(state["completed_job_ids"]) | set(state["failed_job_ids"])
    return bool(family_jobs) and family_jobs.issubset(terminal)


def _validate_google_record_locale(record: Mapping[str, Any], job: Mapping[str, Any]) -> None:
    for key in ("requested_url", "final_url"):
        url = record.get(key)
        if not isinstance(url, str):
            raise PipelineBlocked(f"Google content record missing {key}")
        _validate_google_job_url(url, job["query"])


def _validate_google_job_url(url: str, query: str) -> None:
    parsed = urlsplit(url)
    values = parse_qs(parsed.query)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() not in {"google.com", "www.google.com"}
        or parsed.path.rstrip("/") != "/search"
        or values.get("q") != [query]
        or values.get("hl") != ["en"]
        or values.get("gl") != ["us"]
        or values.get("pws") != ["0"]
    ):
        raise PipelineError("Google job URL must bind exact q plus hl=en, gl=us, pws=0")


def _visible_comment_count(row: Mapping[str, Any]) -> int | None:
    for value in (
        row.get("comments"),
        row.get("engagement_snippet"),
        as_dict(row.get("engagement")).get("comments"),
        as_dict(row.get("listing_snapshot")).get("comments"),
    ):
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
        if isinstance(value, str):
            match = re.search(r"\b([\d,]+)\+?\s+comments?\b", value, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))
    snippet = row.get("snippet")
    if isinstance(snippet, str):
        match = re.search(r"\b([\d,]+)\+?\s+comments?\b", snippet, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def _load_google_content_record(packet: Path) -> dict[str, Any]:
    """Load a native record or project a preserved RealChrome SERP packet.

    The automated Google runner writes ``content_record.json`` directly. The
    operator-visible persistent fallback intentionally preserves raw rendered
    artifacts instead. Both routes are first-class queue outcomes, so the
    controller must normalize the latter offline without another network hop.
    """
    record_path = _find_content_record(packet)
    if record_path is not None:
        return _read_json(record_path, label="Google SERP content record")

    if not packet.is_dir():
        raise PipelineBlocked(f"Google packet locator is not a directory: {packet}")
    manifest_path = _exactly_one(packet.rglob("manifest.json"), "packet manifest", packet)
    manifest = _read_json(manifest_path, label="Google packet manifest")
    if "google_serp" not in str(manifest.get("source_surface", "")):
        raise PipelineBlocked("persistent packet is not a Google SERP surface")
    raw = manifest_path.parent / "raw"
    dom_path = _exactly_one(raw.glob("*_realchrome_rendered_dom.html"), "rendered DOM", packet)
    text_path = _exactly_one(raw.glob("*_realchrome_visible_text.txt"), "visible text", packet)
    metadata_path = _exactly_one(raw.glob("*_realchrome_snapshot_metadata.json"), "snapshot metadata", packet)
    metadata = _read_json(metadata_path, label="RealChrome snapshot metadata")
    requested_url = metadata.get("requested_url")
    final_url = metadata.get("final_url")
    if not isinstance(requested_url, str) or not isinstance(final_url, str):
        raise PipelineBlocked("RealChrome snapshot metadata lacks requested/final URL")
    try:
        return build_google_serp_content_record(
            rendered_dom=dom_path.read_bytes(),
            visible_text=text_path.read_bytes(),
            requested_url=requested_url,
            final_url=final_url,
        )
    except GoogleSerpContentAnomaly as exc:
        raise PipelineBlocked(f"persistent Google packet cannot be normalized: {exc}") from exc


def _find_content_record(packet: Path) -> Path | None:
    if packet.is_file() and packet.name == "content_record.json":
        return packet
    matches = list(packet.rglob("content_record.json")) if packet.is_dir() else []
    if len(matches) > 1:
        raise PipelineBlocked(f"expected at most one Google content_record.json under {packet}, found {len(matches)}")
    return matches[0] if matches else None


def _exactly_one(paths: Any, label: str, packet: Path) -> Path:
    matches = list(paths)
    if len(matches) != 1:
        raise PipelineBlocked(
            f"expected exactly one {label} under {packet}, found {len(matches)}"
        )
    return matches[0]


def _packet_terminal(path: Path) -> bool:
    if not path.exists():
        return False
    return any(path.rglob("manifest.json")) or any(path.rglob("content_record.json"))


def _packet_access_block_reason(path: Path, *, worker: str = "reddit") -> str | None:
    """Read the runner's source-visible access verdict before banking success.

    A Reddit packet only earns capture-success credit when its own snapshot
    metadata proves the capture came to rest on the exact requested thread.  An
    absent, ambiguous, or unreadable access verdict is a block, never a silent
    success: the login wall that produced 27 false successes in the first live
    run reported ``access_blocked: false`` on a zero exit.
    """
    reddit_worker = worker == "reddit"
    if not path.is_dir():
        return "reddit_access_verdict_unavailable" if reddit_worker else None
    matches = list(path.rglob("*_realchrome_snapshot_metadata.json"))
    if len(matches) != 1:
        if not reddit_worker:
            return None
        return (
            "reddit_access_verdict_unavailable"
            if not matches
            else "reddit_access_verdict_ambiguous"
        )
    metadata = _read_json(matches[0], label="RealChrome snapshot metadata")
    if metadata.get("access_blocked") is True:
        # The runner's own explicit verdict is the most specific reason.
        reason = metadata.get("access_block_reason")
        return (
            reason
            if isinstance(reason, str) and reason.strip()
            else "realchrome_access_blocked"
        )
    if not reddit_worker:
        return None
    requested_url = metadata.get("requested_url")
    final_url = metadata.get("final_url")
    requested_thread = (
        canonical_reddit_thread(requested_url)
        if isinstance(requested_url, str)
        else None
    )
    if requested_thread is None or not isinstance(final_url, str):
        return "reddit_access_verdict_unavailable"
    final_thread = canonical_reddit_thread(final_url)
    if (
        final_thread is None
        or final_thread["canonical_thread_id"]
        != requested_thread["canonical_thread_id"]
    ):
        return "reddit_thread_not_reached"
    return None


def _loopback_cdp_endpoint(value: str) -> str:
    """Return the concurrency identity of a loopback CDP endpoint.

    ``localhost``, ``127.0.0.1``, and ``::1`` name one listener, and the scheme
    does not change which browser answers, so the identity is the port alone.
    Comparing raw text instead would let two workers drive one Chrome.
    """
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise PipelineError("browser CDP endpoints must be loopback-only")
    if parsed.port is None:
        raise PipelineError("browser CDP endpoint must declare a port")
    return f"loopback:{parsed.port}"


def _reject_secrets(value: Any, path: str = "config") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).casefold()
            if any(part in lowered for part in SECRET_KEY_PARTS):
                raise PipelineError(f"forbidden secret/network field: {path}.{key}")
            _reject_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", value) and "127.0.0.1" not in value:
            raise PipelineError(f"exact non-loopback IP is forbidden at {path}")


def _append_event(paths: PipelinePaths, state: Mapping[str, Any], event_type: str, detail: Mapping[str, Any]) -> None:
    event = {
        "schema_version": EVENT_VERSION,
        "event_id": _stable_id("event", state["run_id"], utc_now_z_microseconds(), event_type),
        "at": utc_now_z_microseconds(),
        "run_id": state["run_id"],
        "event_type": event_type,
        "detail": dict(detail),
    }
    _reject_secrets(event, path="event")
    with paths.events.open("ab") as handle:
        handle.write(_json_bytes(event, pretty=False))
        handle.flush()
        os.fsync(handle.fileno())


def _load_state(paths: PipelinePaths) -> dict[str, Any]:
    state = _read_json(paths.state, label="pipeline state")
    if state.get("schema_version") != STATE_VERSION:
        raise PipelineError(f"state schema_version must be {STATE_VERSION}")
    config_bytes = paths.config.read_bytes()
    if state.get("config_sha256") != sha256_text(config_bytes.decode("utf-8")):
        raise PipelineBlocked("pipeline config changed after init")
    return state


def _save_state(paths: PipelinePaths, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now_z_microseconds()
    _reject_secrets(state, path="state")
    _atomic_write_json(paths.state, state)


class _state_guard:
    def __init__(self, paths: PipelinePaths) -> None:
        self.path = paths.state.with_suffix(".lock")
        self.fd: int | None = None

    def __enter__(self) -> None:
        for _ in range(1000):
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode("ascii"))
                return
            except (FileExistsError, PermissionError):
                # On Windows a just-closed lock file can remain briefly
                # undeletable/open-denied to the other worker.  That is still
                # "lock held", not an authorization or state failure.
                time.sleep(0.01)
        raise PipelineBlocked(f"state lock unavailable: {self.path}")

    def __exit__(self, *_args: Any) -> None:
        if self.fd is not None:
            os.close(self.fd)
        self.path.unlink(missing_ok=True)


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PipelineError(f"{label} could not be read: {exc}") from exc
    if not isinstance(value, dict):
        raise PipelineError(f"{label} must be an object")
    return value


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise PipelineError(f"refusing to overwrite existing file: {path}") from exc


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("xb") as handle:
        handle.write(_json_bytes(value))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _json_bytes(value: Mapping[str, Any], *, pretty: bool = True) -> bytes:
    if pretty:
        text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    else:
        text = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    return text.encode("utf-8")


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PipelineError(f"{key} must be a non-empty string")
    return value.strip()


def _stable_id(kind: str, *parts: str) -> str:
    return f"{kind}_{sha256_text('|'.join(parts))[:20]}"


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PipelineError(f"invalid ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise PipelineError(f"timestamp must include timezone: {value}")
    return parsed.astimezone(UTC)


def _interval_union(raw: Any) -> list[tuple[datetime, datetime]]:
    intervals: list[tuple[datetime, datetime]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and isinstance(item.get("start"), str) and isinstance(item.get("end"), str):
                start, end = _parse_time(item["start"]), _parse_time(item["end"])
                if end >= start:
                    intervals.append((start, end))
    intervals.sort()
    merged: list[tuple[datetime, datetime]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _intersection_seconds(left: Sequence[tuple[datetime, datetime]], right: Sequence[tuple[datetime, datetime]]) -> float:
    total = 0.0
    i = j = 0
    while i < len(left) and j < len(right):
        start = max(left[i][0], right[j][0])
        end = min(left[i][1], right[j][1])
        if end > start:
            total += (end - start).total_seconds()
        if left[i][1] <= right[j][1]:
            i += 1
        else:
            j += 1
    return total


def _total_seconds(intervals: Sequence[tuple[datetime, datetime]]) -> float:
    return sum((end - start).total_seconds() for start, end in intervals)


def _harness_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_google_url(query: str) -> str:
    return "https://www.google.com/search?q=" + quote_plus(query) + "&hl=en&gl=us&pws=0"


__all__ = [
    "CONFIG_VERSION",
    "DECISIONS_VERSION",
    "FAMILY_MANIFEST_VERSION",
    "MANDATORY_FAMILY_KINDS",
    "CaptureResult",
    "PipelineBlocked",
    "PipelineError",
    "append_family",
    "build_google_url",
    "canonical_reddit_thread",
    "import_decisions",
    "ingest_google_packet",
    "initialize_pipeline",
    "inspect_pipeline",
    "load_config",
    "pipeline_paths",
    "run_pipeline",
    "timing_metrics",
]
