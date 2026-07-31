from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import utc_now_z
from runners.run_source_capture_http_packet import run_source_capture_http_packet
from source_capture import CaptureModeCategory


DEFAULT_MINIMUM_GAP_SECONDS = 90.0
MINIMUM_ALLOWED_GAP_SECONDS = 60.0
MAX_BATCH_JOBS = 10
STOPPED_EXIT_CODE = 3
_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class SameHostHttpJob:
    job_id: str
    url: str
    decision_question: str


def load_jobs(path: Path) -> list[SameHostHttpJob]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("job list must be a non-empty JSON list")
    if len(raw) > MAX_BATCH_JOBS:
        raise ValueError(f"job list may contain at most {MAX_BATCH_JOBS} jobs")

    jobs: list[SameHostHttpJob] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"job {index} must be a JSON object")
        allowed = {"job_id", "url", "decision_question"}
        unexpected = sorted(set(item) - allowed)
        if unexpected:
            raise ValueError(f"job {index} has unexpected fields: {', '.join(unexpected)}")
        try:
            jobs.append(
                SameHostHttpJob(
                    job_id=str(item["job_id"]),
                    url=str(item["url"]),
                    decision_question=str(item["decision_question"]),
                )
            )
        except KeyError as exc:
            raise ValueError(f"job {index} is missing {exc.args[0]}") from exc
    _validate_jobs(jobs)
    return jobs


def run_same_host_http_batch(
    *,
    jobs: Sequence[SameHostHttpJob],
    output_root: Path,
    source_family: str,
    source_surface: str,
    capture_context: str,
    minimum_gap_seconds: float = DEFAULT_MINIMUM_GAP_SECONDS,
    timeout_seconds: float = 20.0,
    max_bytes: int = 5_000_000,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, dict[str, object]]:
    _validate_jobs(jobs)
    if minimum_gap_seconds < MINIMUM_ALLOWED_GAP_SECONDS:
        raise ValueError(
            f"minimum_gap_seconds must be at least {MINIMUM_ALLOWED_GAP_SECONDS:g}"
        )
    if output_root.exists():
        raise ValueError(f"output root already exists: {output_root}")

    output_root.mkdir(parents=True)
    host = _normalized_host(jobs[0].url)
    attempts: list[dict[str, object]] = []
    stop_reason: str | None = None

    for index, job in enumerate(jobs):
        if index:
            sleep(minimum_gap_seconds)

        packet_directory = output_root / f"{index + 1:02d}_{job.job_id}_packet"
        started_at = utc_now_z()
        exit_code, message = run_source_capture_http_packet(
            url=job.url,
            source_family=source_family,
            source_surface=source_surface,
            decision_question=job.decision_question,
            output_directory=packet_directory,
            data_root=None,
            capture_context=capture_context,
            operator_category="same_host_http_batch_operator",
            capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
            session_id=None,
            actor_audience_context=None,
            visible_mode_changes=["same_host_serial_pacing_enforced"],
            source_publication_or_event=None,
            source_edit_or_version=None,
            cutoff_posture=None,
            recapture_time=None,
            re_capture_relationship=None,
            warnings=[],
            limitations=[],
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
            intended_cadence={
                "mode": "same_host_serial_minimum_gap",
                "minimum_gap_seconds": minimum_gap_seconds,
                "enforcement": "runner_sleep_after_previous_response_before_next_request",
            },
        )
        metadata = _read_http_metadata(packet_directory)
        status = metadata.get("status") if metadata is not None else None
        retry_after = metadata.get("retry_after") if metadata is not None else None
        body_classification = (
            metadata.get("body_classification") if metadata is not None else None
        )
        healthy = (
            exit_code == 0
            and isinstance(status, int)
            and 200 <= status < 300
            and body_classification == "content_unverified"
        )
        attempt = {
            "job_id": job.job_id,
            "url": job.url,
            "started_at": started_at,
            "finished_at": utc_now_z(),
            "packet_directory": str(packet_directory),
            "runner_exit_code": exit_code,
            "http_status": status,
            "retry_after": retry_after,
            "body_classification": body_classification,
            "result": "captured" if healthy else "stopped_on_failure",
            "message": message,
        }
        attempts.append(attempt)
        if not healthy:
            stop_reason = (
                f"job {job.job_id} failed or was refused"
                + (f" with HTTP {status}" if status is not None else " before a readable HTTP response")
            )
            break

    attempted_ids = {str(item["job_id"]) for item in attempts}
    unrun_jobs = [job.job_id for job in jobs if job.job_id not in attempted_ids]
    summary: dict[str, object] = {
        "schema_version": "forseti.same_host_http_batch.v1",
        "host": host,
        "minimum_gap_seconds": minimum_gap_seconds,
        "pacing_rule": "wait after each completed response before the next same-host request",
        "retry_policy": "no automatic retries",
        "planned_jobs": [job.job_id for job in jobs],
        "attempts": attempts,
        "unrun_jobs": unrun_jobs,
        "completed": stop_reason is None,
        "stop_reason": stop_reason,
    }
    (output_root / "same_host_http_batch_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return (0 if stop_reason is None else STOPPED_EXIT_CODE), summary


def _validate_jobs(jobs: Sequence[SameHostHttpJob]) -> None:
    if not jobs:
        raise ValueError("jobs must not be empty")
    if len(jobs) > MAX_BATCH_JOBS:
        raise ValueError(f"jobs may contain at most {MAX_BATCH_JOBS} entries")
    ids: set[str] = set()
    hosts: set[str] = set()
    for job in jobs:
        if not _JOB_ID_PATTERN.fullmatch(job.job_id):
            raise ValueError(f"invalid job_id: {job.job_id!r}")
        if job.job_id in ids:
            raise ValueError(f"duplicate job_id: {job.job_id}")
        ids.add(job.job_id)
        if not job.decision_question.strip():
            raise ValueError(f"decision_question is empty for {job.job_id}")
        hosts.add(_normalized_host(job.url))
    if len(hosts) != 1:
        raise ValueError("all jobs must use the same exact hostname")


def _normalized_host(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise ValueError(f"job URL must be an absolute HTTP(S) URL: {url!r}")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("job URLs must not contain credentials")
    return parsed.hostname.lower()


def _read_http_metadata(packet_directory: Path) -> dict[str, object] | None:
    matches = sorted(packet_directory.rglob("*_http_response_metadata.json"))
    if len(matches) != 1:
        return None
    value = json.loads(matches[0].read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture a small same-host Direct HTTP list serially, enforce a polite gap, "
            "and stop the queue on the first refusal or capture failure."
        )
    )
    parser.add_argument("--job-list", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-family", default="web_page")
    parser.add_argument("--source-surface", default="direct_http")
    parser.add_argument("--capture-context", default="bounded same-host Direct HTTP batch")
    parser.add_argument("--minimum-gap-seconds", type=float, default=DEFAULT_MINIMUM_GAP_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        jobs = load_jobs(args.job_list)
        exit_code, summary = run_same_host_http_batch(
            jobs=jobs,
            output_root=args.output_root,
            source_family=args.source_family,
            source_surface=args.source_surface,
            capture_context=args.capture_context,
            minimum_gap_seconds=args.minimum_gap_seconds,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(status=2, message=f"same-host Direct HTTP batch failed: {exc}\n")
    print("same_host_http_batch_summary_json=" + json.dumps(summary, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
