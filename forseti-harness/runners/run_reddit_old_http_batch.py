from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from textwrap import wrap
from typing import TYPE_CHECKING, Any, Sequence
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot

from harness_utils import utc_now_z_microseconds
from runners.run_source_capture_http_packet import run_source_capture_http_packet
from source_capture import CaptureModeCategory
from capture_spine.reddit_capture_cadence import (
    REDDIT_CADENCE_BASIS,
    REDDIT_CADENCE_MAX_GAP_SECONDS,
    REDDIT_CADENCE_MIN_GAP_SECONDS,
    REDDIT_CADENCE_MODE,
)
from source_capture.cadence import (
    CADENCE_BASES,
    CadenceMode,
    build_cadence_plan,
    resolve_cadence_window_seconds,
    resolve_paced_wait,
)
from source_capture.content_extraction import (
    CAPTURE_RETENTION_MODES,
    CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    CONTENT_RECORD_FILENAME,
    ContentExtractionSpec,
)
from source_capture.reddit_consolidation import (
    OLD_REDDIT_THREAD_PARSER_VERSION,
    WWW_REDDIT_THREAD_PARSER_VERSION,
    build_thread_content_record,
    build_www_thread_content_record,
)


OLD_HTTP_TRANSPORT = "old_http"
WWW_REALCHROME_TRANSPORT = "www_realchrome"
THREAD_TRANSPORTS = (OLD_HTTP_TRANSPORT, WWW_REALCHROME_TRANSPORT)

TRANSPORT_HOSTS = {
    OLD_HTTP_TRANSPORT: "old.reddit.com",
    WWW_REALCHROME_TRANSPORT: "www.reddit.com",
}
TRANSPORT_SOURCE_SURFACES = {
    OLD_HTTP_TRANSPORT: "old_reddit_direct_http",
    WWW_REALCHROME_TRANSPORT: "www_reddit_realchrome_cdp",
}

# Measured on r/Sephora thread 1v87d9j (198 declared comments, 2026-08-01):
# 35 comments on first paint, 119 after one expansion round, 152 after two,
# zero controls remaining. The bound is set well above the observed
# convergence so a larger thread is not silently truncated; when the bound
# does stop the loop the runner records that fact rather than implying the
# tree was exhausted.
WWW_EXPAND_CONTROL_PATTERN = r"more repl(?:y|ies)|more comments?|load more comments?"
WWW_EXPAND_CONTROL_SELECTOR = "shreddit-comment-tree button, shreddit-comment-tree a"
WWW_EXPAND_MAX_ROUNDS = 8
WWW_EXPAND_SETTLE_MS = 6000
WWW_READY_SELECTOR = "shreddit-comment"
WWW_VIEWPORT_WIDTH = 1280
WWW_VIEWPORT_HEIGHT = 20000
WWW_SETTLE_SECONDS = 12.0
WWW_PERSISTENT_TAB_MARKER = "forseti-reddit-thread"
DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9223"


class ThreadProjectionAnomalyError(ValueError):
    """A www thread rendered but its comment tree did not.

    Raised so the capture seam keeps the raw response as audit evidence
    instead of shipping a content record that states zero comments for a
    thread the page itself says has many.
    """


DEFAULT_DELAY_SECONDS = 30.0
DEFAULT_MAX_URLS = 10
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_BYTES = 5_000_000
ACCESS_DIAGNOSTIC_SCHEMA_VERSION = "reddit_block_shell_diagnostic_v1"
ACCESS_DIAGNOSTIC_DIRECTORY = "access_diagnostics"
# Content retention is the standard fleet posture: the thread record is
# extracted in flight and preserved in the packet; raw is hashed then
# discarded. Raw remains the explicit operator-selected evidence posture.
DEFAULT_RETENTION_MODE = "content"

# Circuit breaker, owner decision 2026-08-01. When the server refuses this
# many CONSECUTIVE navigations with an HTTP error (a confirmed refusal, not a
# timeout or local failure), the batch stops instead of marching the rest of
# the queue into the same rate-limit window: the 2026-08-01 leaderboard run
# spent 8 refused requests learning what the first 2 already said. Slots never
# attempted get no journal row, so a later --resume run picks up exactly
# there. 0 disables. This is a stop, not a retry: no request is reissued.
DEFAULT_REFUSAL_CIRCUIT_BREAKER = 3


@dataclass(frozen=True)
class BatchSlot:
    slot_id: str
    url: str


def run_reddit_old_http_batch(
    *,
    slots: Sequence[BatchSlot],
    output_root: Path,
    decision_question: str,
    data_root: "DataLakeRoot | None" = None,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    max_urls: int = DEFAULT_MAX_URLS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    cadence_mode: CadenceMode = REDDIT_CADENCE_MODE,
    cadence_window_seconds: float | None = None,
    cadence_min_gap_seconds: float | None = REDDIT_CADENCE_MIN_GAP_SECONDS,
    cadence_max_gap_seconds: float | None = REDDIT_CADENCE_MAX_GAP_SECONDS,
    cadence_random_seed: int | None = None,
    cadence_basis: str = REDDIT_CADENCE_BASIS,
    requested_retention_mode: str = DEFAULT_RETENTION_MODE,
    transport: str = OLD_HTTP_TRANSPORT,
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
    keep_raw_audit_sample: bool = False,
    resume: bool = False,
    refusal_circuit_breaker: int = DEFAULT_REFUSAL_CIRCUIT_BREAKER,
) -> tuple[int, str]:
    if requested_retention_mode not in CAPTURE_RETENTION_MODES:
        raise ValueError(
            f"requested_retention_mode must be one of {CAPTURE_RETENTION_MODES}, "
            f"got {requested_retention_mode!r}"
        )
    if transport not in THREAD_TRANSPORTS:
        raise ValueError(f"transport must be one of {THREAD_TRANSPORTS}, got {transport!r}")
    if transport == WWW_REALCHROME_TRANSPORT and requested_retention_mode != "content":
        # The Reddit lane binds never-raw-only. A rendered thread page carries
        # session-shaped chrome that the content record deliberately drops, so
        # a raw-mode www capture would both retain more than the lane allows
        # and preserve nothing the deep read actually consumes.
        raise ValueError(
            "the www transport binds never-raw-only; "
            f"requested_retention_mode={requested_retention_mode!r} is refused"
        )
    _validate_batch_inputs(
        slots=slots,
        output_root=output_root,
        delay_seconds=delay_seconds,
        max_urls=max_urls,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        transport=transport,
    )
    summary_path = output_root / "batch_summary.json"
    if summary_path.exists() and not resume:
        raise ValueError(f"batch summary already exists: {summary_path}")

    # The summary alone is written at end-of-run, so an external kill --
    # session teardown, machine sleep, operator interrupt -- used to erase
    # every trace of a run whose packets were already safely in the lake.
    # Each slot's row is therefore journaled durably the moment the slot
    # finishes; the journal is also what makes a killed run resumable
    # without re-requesting threads Reddit already served.
    progress_path = output_root / "batch_progress.jsonl"
    carried_rows = _load_resume_rows(
        progress_path=progress_path, slots=slots, resume=resume
    )
    carried_slot_ids = {row["slot_id"] for row in carried_rows}
    pending_slots = [slot for slot in slots if slot.slot_id not in carried_slot_ids]
    if resume and not pending_slots:
        raise ValueError(
            f"nothing to resume: all {len(slots)} slot(s) already journaled in {progress_path}"
        )
    if summary_path.exists():
        # A circuit-breaker trip (or any partial run) writes an honest partial
        # summary; a valid resume must not be blocked by it, and must not erase
        # it. Validate the journal and prove work remains before moving it.
        superseded_count = len(list(output_root.glob("batch_summary.superseded_*.json")))
        summary_path.rename(
            output_root / f"batch_summary.superseded_{superseded_count + 1:02d}.json"
        )

    if cadence_mode == "bounded_jitter" and cadence_window_seconds is None:
        # Derivable from the slot count and the max gap; requiring it by hand
        # only ever produces a launch failure or a silently compressed range.
        cadence_window_seconds = resolve_cadence_window_seconds(
            slot_count=len(pending_slots), max_gap_seconds=cadence_max_gap_seconds
        )
    cadence_plan = build_cadence_plan(
        slot_count=len(pending_slots),
        mode=cadence_mode,
        delay_seconds=delay_seconds,
        window_seconds=cadence_window_seconds,
        min_gap_seconds=cadence_min_gap_seconds,
        max_gap_seconds=cadence_max_gap_seconds,
        random_seed=cadence_random_seed,
    )
    output_root.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = list(carried_rows)
    consecutive_refusals = 0
    breaker_tripped_after_slot: str | None = None
    slots_not_attempted: list[str] = []
    for index, slot in enumerate(pending_slots):
        packet_dir = None if data_root is not None else output_root / f"{slot.slot_id}_packet"
        row: dict[str, Any] = {
            "slot_id": slot.slot_id,
            "url": slot.url,
            "capture_exit": None,
            "capture_message": None,
            "packet_dir": str(packet_dir) if packet_dir is not None else None,
            "lake_committed": data_root is not None,
            "retry_count": 0,
            "planned_start_offset_seconds": cadence_plan.planned_offsets_seconds[index],
            "planned_wait_after_seconds": (
                cadence_plan.planned_waits_seconds[index]
                if index < len(cadence_plan.planned_waits_seconds)
                else None
            ),
            "capture_started_at": None,
            "capture_finished_at": None,
            "content_extraction_failed": False,
            "content_record_preserved": False,
            "navigation_http_status": None,
            "access_diagnostic_status": "not_applicable",
            "access_diagnostic_screenshot": None,
            "access_diagnostic_receipt": None,
            "access_diagnostic_error": None,
        }
        slot_is_navigation_refusal = False

        extraction_spec = ContentExtractionSpec(
            requested_retention_mode=requested_retention_mode,
            extractor_version=OLD_REDDIT_THREAD_PARSER_VERSION,
            extractor=lambda html_text, final_url: build_thread_content_record(
                html_text=html_text,
                source_url=final_url,
            ),
        )
        capture_started_monotonic = time.monotonic()
        try:
            row["capture_started_at"] = utc_now_z_microseconds()
            if transport == WWW_REALCHROME_TRANSPORT:
                capture_exit, capture_message = _capture_www_thread(
                    slot=slot,
                    decision_question=decision_question,
                    output_directory=packet_dir,
                    data_root=data_root,
                    cdp_endpoint=cdp_endpoint,
                    keep_raw_audit_sample=keep_raw_audit_sample,
                    timeout_seconds=timeout_seconds,
                    cadence_plan=cadence_plan,
                    index=index,
                )
            else:
                capture_exit, capture_message = run_source_capture_http_packet(
                    url=slot.url,
                    source_family="reddit_thread",
                    source_surface=TRANSPORT_SOURCE_SURFACES[OLD_HTTP_TRANSPORT],
                    decision_question=decision_question,
                    output_directory=packet_dir,
                    data_root=data_root,
                    capture_context=(
                        "bounded old Reddit direct HTTP calibration batch; exact supplied URL only; "
                        "no proxy, browser, crawler, retry, or link following"
                    ),
                    operator_category="reddit_old_http_batch_operator",
                    capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
                    session_id=None,
                    actor_audience_context=None,
                    visible_mode_changes=[],
                    source_publication_or_event=None,
                    source_edit_or_version=None,
                    cutoff_posture=None,
                    recapture_time=None,
                    re_capture_relationship=None,
                    warnings=[],
                    limitations=[
                        "batch runner accepts exact old.reddit.com URLs only",
                        f"batch runner cadence_mode={cadence_plan.mode}",
                        f"batch runner planned_start_offset_seconds={cadence_plan.planned_offsets_seconds[index]}",
                        "batch runner retry_count=0",
                    ],
                    timeout_seconds=timeout_seconds,
                    max_bytes=max_bytes,
                    content_extraction=extraction_spec,
                )
            row["capture_exit"] = capture_exit
            row["capture_message"] = capture_message
            if capture_exit == CONTENT_EXTRACTION_FAILED_EXIT_CODE:
                row["content_extraction_failed"] = True
            if capture_exit in (0, CONTENT_EXTRACTION_FAILED_EXIT_CODE) and packet_dir is None:
                # Lake commit: the runner returns the committed packet directory.
                packet_dir = Path(capture_message)
                row["packet_dir"] = str(packet_dir)
            if packet_dir is not None:
                row["content_record_preserved"] = _packet_preserves_content_record(packet_dir)
                if transport == WWW_REALCHROME_TRANSPORT:
                    navigation_status = _packet_navigation_http_status(packet_dir)
                    if navigation_status is not None:
                        row["navigation_http_status"] = navigation_status
                        slot_is_navigation_refusal = True
            if capture_exit == CONTENT_EXTRACTION_FAILED_EXIT_CODE and packet_dir is not None:
                try:
                    diagnostic = _preserve_block_shell_diagnostic(
                        packet_dir=packet_dir,
                        diagnostic_root=output_root / ACCESS_DIAGNOSTIC_DIRECTORY,
                        slot=slot,
                    )
                    if diagnostic is not None:
                        row["access_diagnostic_status"] = "preserved"
                        row["access_diagnostic_screenshot"] = diagnostic["screenshot_path"]
                        row["access_diagnostic_receipt"] = diagnostic["receipt_path"]
                except Exception as exc:
                    # The access failure remains the primary outcome. A failed
                    # derived diagnostic is separately visible and never turns
                    # the capture into success or triggers another request.
                    row["access_diagnostic_status"] = "failed"
                    row["access_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        except Exception as exc:
            row["capture_exit"] = 2
            row["capture_message"] = f"{type(exc).__name__}: {exc}"
            # A navigation HTTP refusal carries the refused status; keeping it
            # as a row field is what lets a later read distinguish a 429
            # throttling burst from a 5xx outage without the raw response.
            navigation_status = getattr(exc, "http_status", None)
            if isinstance(navigation_status, int):
                row["navigation_http_status"] = navigation_status
            # Only a typed server-side refusal feeds the circuit breaker;
            # timeouts and local failures never do.
            if hasattr(exc, "http_status"):
                slot_is_navigation_refusal = True
        finally:
            row["capture_finished_at"] = utc_now_z_microseconds()

        if slot_is_navigation_refusal:
            consecutive_refusals += 1
        else:
            consecutive_refusals = 0

        elapsed = time.monotonic() - capture_started_monotonic
        row["capture_elapsed_seconds"] = round(elapsed, 3)
        results.append(row)
        _append_progress_row(progress_path=progress_path, row=row)
        if refusal_circuit_breaker and consecutive_refusals >= refusal_circuit_breaker:
            breaker_tripped_after_slot = slot.slot_id
            slots_not_attempted = [s.slot_id for s in pending_slots[index + 1:]]
            break
        if index < len(cadence_plan.planned_waits_seconds):
            wait_seconds, overrun = resolve_paced_wait(
                planned=cadence_plan.planned_waits_seconds[index],
                elapsed=elapsed,
                basis=cadence_basis,
            )
            if overrun > 0:
                row["cadence_overrun_seconds"] = overrun
            if wait_seconds > 0:
                time.sleep(wait_seconds)

    summary = {
        "runner": "reddit_old_http_batch",
        "method": TRANSPORT_SOURCE_SURFACES[transport],
        "transport": transport,
        "requested_retention_mode": requested_retention_mode,
        "content_extraction_failure_count": sum(
            1 for row in results if row["content_extraction_failed"]
        ),
        "lake_committed": data_root is not None,
        # "not browser automation" holds only on the direct-HTTP transport. The
        # www transport drives the operator's real Chrome and clicks in-place
        # expansion controls, so keeping that claim here would be false.
        "non_claims": [
            "not crawler",
            "not source discovery",
            "not monitoring",
            "not proxy use",
            "not retry escalation",
            "not broad Reddit crawl",
            "not link following",
            *(
                ["not browser automation"]
                if transport == OLD_HTTP_TRANSPORT
                else [
                    "browser automation IS used: the operator's real Chrome renders the "
                    "thread and in-place comment expansion controls are clicked",
                    "not continuation-page fetch",
                ]
            ),
        ],
        "delay_seconds": cadence_plan.delay_seconds,
        "cadence": cadence_plan.to_dict(),
        "max_urls": max_urls,
        "url_count": len(slots),
        "resumed": resume,
        "carried_slot_count": len(carried_rows),
        "circuit_breaker": {
            "consecutive_refusal_threshold": refusal_circuit_breaker,
            "tripped": breaker_tripped_after_slot is not None,
            "tripped_after_slot": breaker_tripped_after_slot,
            "slots_not_attempted": slots_not_attempted,
        },
        "capture_success_count": sum(1 for row in results if row["capture_exit"] == 0),
        "access_diagnostic_count": sum(
            1 for row in results if row["access_diagnostic_status"] == "preserved"
        ),
        "access_diagnostic_failure_count": sum(
            1 for row in results if row["access_diagnostic_status"] == "failed"
        ),
        "results": results,
    }
    summary_path.write_text(
        f"{json.dumps(summary, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0, str(summary_path)


def build_validated_www_thread_content_record(
    *, html_text: str, source_url: str
) -> dict[str, Any]:
    """Build one www thread record, refusing a rendered-but-empty comment tree.

    A partial tree is expected and is recorded honestly by the projection --
    the deep tail sits behind nofollow continuation links this lane does not
    follow. A tree that declares comments and yields NONE is different in kind:
    it means the page served a shell, and projecting it would put a
    zero-comment record into the dive corpus for a thread that has hundreds.
    """
    record = build_www_thread_content_record(
        html_text=html_text, source_url=source_url
    )
    completeness = record["comment_completeness"]
    declared = completeness["declared_total_comments"]
    if record["counts"]["comments_parsed"] == 0 and (declared or 0) > 0:
        raise ThreadProjectionAnomalyError(
            "thread projection anomaly [declared_comments_none_rendered]: thread "
            f"declares {declared} comments and none rendered; keeping raw for audit"
        )
    return record


def _capture_www_thread(
    *,
    slot: BatchSlot,
    decision_question: str,
    output_directory: Path | None,
    data_root: "DataLakeRoot | None",
    cdp_endpoint: str,
    keep_raw_audit_sample: bool,
    timeout_seconds: float,
    cadence_plan: Any,
    index: int,
) -> tuple[int, str]:
    """Capture one www thread through the operator's real Chrome.

    Routed through the shared real-Chrome runner rather than a second
    orchestrator, so the slot list, cadence, summary, and validation above stay
    transport-agnostic and single-homed.
    """
    from runners.run_source_capture_realchrome_cdp_packet import (
        RenderedContentExtractionSpec,
        run_source_capture_realchrome_cdp_packet,
    )
    from source_capture.rendered_retention import require_content_retention

    def _extract(rendered_dom: bytes, _visible_text: bytes, final_url: str) -> dict:
        return build_validated_www_thread_content_record(
            html_text=rendered_dom.decode("utf-8", errors="replace"),
            source_url=final_url,
        )

    spec = require_content_retention(
        RenderedContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version=WWW_REDDIT_THREAD_PARSER_VERSION,
            extractor=_extract,
        ),
        lane="reddit www thread capture",
    )
    # The persistent capture tab lives in the operator's real Chrome, where a
    # human can navigate it mid-capture; the snapshot must be provably the
    # requested thread, not whatever page the tab held (21 wrong-page packets
    # committed as success on 2026-08-03 before this bind).  Compare parsed
    # host+thread identity so a lookalike path on another host cannot pass.
    return run_source_capture_realchrome_cdp_packet(
        url=slot.url,
        source_family="reddit_thread",
        source_surface=TRANSPORT_SOURCE_SURFACES[WWW_REALCHROME_TRANSPORT],
        decision_question=decision_question,
        output_directory=output_directory,
        data_root=data_root,
        capture_context=(
            "bounded reddit thread deep-read capture over the www surface; one declared "
            "thread page per slot; in-place comment expansion only, with no link "
            "following, continuation-page fetch, user/profile capture, or self-scheduling"
        ),
        cdp_endpoint=cdp_endpoint,
        persistent_tab_marker=WWW_PERSISTENT_TAB_MARKER,
        ready_selector=WWW_READY_SELECTOR,
        expand_control_pattern=WWW_EXPAND_CONTROL_PATTERN,
        expand_control_selector=WWW_EXPAND_CONTROL_SELECTOR,
        expand_max_rounds=WWW_EXPAND_MAX_ROUNDS,
        expand_settle_ms=WWW_EXPAND_SETTLE_MS,
        viewport_width=WWW_VIEWPORT_WIDTH,
        viewport_height=WWW_VIEWPORT_HEIGHT,
        settle_seconds=WWW_SETTLE_SECONDS,
        timeout_seconds=timeout_seconds,
        content_extraction=spec,
        capture_screenshot=False,
        keep_raw_audit_sample=keep_raw_audit_sample,
        target_identity_check=lambda final_url: _same_www_thread_identity(
            final_url, slot.url
        ),
        target_identity_description="same www.reddit.com thread id",
        limitations=[
            f"batch runner accepts exact {TRANSPORT_HOSTS[WWW_REALCHROME_TRANSPORT]} URLs only",
            f"batch runner cadence_mode={cadence_plan.mode}",
            f"batch runner planned_start_offset_seconds={cadence_plan.planned_offsets_seconds[index]}",
            "batch runner retry_count=0",
            "www comment depth is bounded by the in-place tree; continuation links are "
            "nofollow separate pages and are not followed",
        ],
    )


def _packet_preserves_content_record(packet_dir: Path) -> bool:
    def is_content_record(path: Path) -> bool:
        if path.name == CONTENT_RECORD_FILENAME:
            return True
        prefix, separator, suffix = path.name.partition("_")
        return bool(separator and prefix.isdigit() and suffix == CONTENT_RECORD_FILENAME)

    return (
        sum(
            1
            for path in packet_dir.rglob(f"*{CONTENT_RECORD_FILENAME}")
            if path.is_file() and is_content_record(path)
        )
        == 1
    )


def _same_www_thread_identity(actual_url: str, expected_url: str) -> bool:
    """Match one www Reddit thread by host and base-36 thread id."""
    actual = urlparse(actual_url)
    expected = urlparse(expected_url)
    expected_host = TRANSPORT_HOSTS[WWW_REALCHROME_TRANSPORT]
    if (
        actual.scheme.casefold() != "https"
        or expected.scheme.casefold() != "https"
        or actual.hostname != expected_host
        or expected.hostname != expected_host
    ):
        return False
    actual_match = re.search(r"/comments/([A-Za-z0-9]+)(?:/|$)", actual.path)
    expected_match = re.search(r"/comments/([A-Za-z0-9]+)(?:/|$)", expected.path)
    return bool(
        actual_match
        and expected_match
        and actual_match.group(1).casefold() == expected_match.group(1).casefold()
    )


def _packet_artifact(packet_dir: Path, filename: str) -> Path:
    matches = []
    for path in packet_dir.rglob(f"*{filename}"):
        if not path.is_file():
            continue
        prefix, separator, suffix = path.name.partition("_")
        if path.name == filename or (
            separator and prefix.isdigit() and suffix == filename
        ):
            matches.append(path)
    if len(matches) != 1:
        raise ValueError(
            f"packet must preserve exactly one {filename}, found {len(matches)}: "
            f"{packet_dir}"
        )
    return matches[0]


def _packet_navigation_http_status(packet_dir: Path) -> int | None:
    """Read a preserved non-success status from a real-Chrome packet.

    Retention renumbering stacks more than one numeric prefix on preserved
    filenames (a real raw-failure packet carries
    ``03_04_realchrome_snapshot_metadata.json``), so this match strips any
    number of ``NN_`` groups; _packet_artifact's single-prefix rule would
    silently never match a real packet here.
    """
    filename = "realchrome_snapshot_metadata.json"
    name_pattern = re.compile(rf"(?:\d+_)*{re.escape(filename)}\Z")
    matches = [
        path
        for path in packet_dir.rglob(f"*{filename}")
        if path.is_file() and name_pattern.fullmatch(path.name)
    ]
    if len(matches) != 1:
        return None
    try:
        metadata = json.loads(matches[0].read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    status = metadata.get("http_response_status")
    if type(status) is int and not 200 <= status < 300:
        return status
    return None


class _VisibleTextParser(HTMLParser):
    _IGNORED = frozenset({"script", "style", "noscript", "template"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in self._IGNORED:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in self._IGNORED and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data.strip():
            self.parts.append(data.strip())


def _visible_text(html_text: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html_text)
    parser.close()
    return " ".join(" ".join(parser.parts).split())


def _diagnostic_png(*, lines: list[str], output_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width = 1400
    margin = 48
    line_height = 28
    rendered_lines: list[str] = []
    for line in lines:
        rendered_lines.extend(wrap(line, width=100) or [""])
    height = max(520, min(1800, margin * 2 + line_height * (len(rendered_lines) + 1)))
    image = Image.new("RGB", (width, height), color=(248, 249, 251))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:  # Pillow < 10 compatibility for downstream operators.
        font = ImageFont.load_default()
    y = margin
    for line in rendered_lines:
        if y + line_height > height - margin:
            draw.text(
                (margin, y),
                "[diagnostic excerpt truncated]",
                fill=(145, 35, 35),
                font=font,
            )
            break
        draw.text((margin, y), line, fill=(24, 28, 36), font=font)
        y += line_height
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def _preserve_block_shell_diagnostic(
    *,
    packet_dir: Path,
    diagnostic_root: Path,
    slot: BatchSlot,
) -> dict[str, str] | None:
    metadata_path = _packet_artifact(packet_dir, "http_response_metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("body_classification") != "block_shell":
        return None

    body_path = _packet_artifact(packet_dir, "http_response_body.bin")
    body = body_path.read_bytes()
    body_sha256 = hashlib.sha256(body).hexdigest()
    html_text = body.decode("utf-8", errors="replace")
    visible_text = _visible_text(html_text)
    excerpt = visible_text[:8_000]

    screenshot_path = diagnostic_root / f"{slot.slot_id}_blocked_response.png"
    receipt_path = diagnostic_root / f"{slot.slot_id}_blocked_response.json"
    _diagnostic_png(
        lines=[
            "BLOCKED RESPONSE DIAGNOSTIC",
            "Derived from the exact preserved HTTP response bytes. No URL refetch, browser access, proxy, retry, or CAPTCHA interaction occurred.",
            f"slot: {slot.slot_id}",
            f"requested URL: {slot.url}",
            f"HTTP status: {metadata.get('status')}",
            f"classification: {metadata.get('body_classification')}",
            f"signal: {metadata.get('body_classification_signal')}",
            f"detail: {metadata.get('body_classification_detail')}",
            f"response SHA-256: {body_sha256}",
            "",
            "VISIBLE RESPONSE TEXT:",
            excerpt or "[no visible text extracted]",
        ],
        output_path=screenshot_path,
    )
    screenshot_sha256 = hashlib.sha256(screenshot_path.read_bytes()).hexdigest()
    receipt = {
        "schema_version": ACCESS_DIAGNOSTIC_SCHEMA_VERSION,
        "slot_id": slot.slot_id,
        "requested_url": slot.url,
        "packet_dir": str(packet_dir),
        "source_body_path": str(body_path),
        "source_body_sha256": body_sha256,
        "http_status": metadata.get("status"),
        "body_classification": metadata.get("body_classification"),
        "body_classification_signal": metadata.get("body_classification_signal"),
        "body_classification_detail": metadata.get("body_classification_detail"),
        "visible_text_excerpt": excerpt,
        "screenshot_path": str(screenshot_path),
        "screenshot_sha256": screenshot_sha256,
        "derivation": "exact_preserved_response_body_no_network_refetch",
        "non_claims": [
            "not a second Reddit request",
            "not browser access",
            "not CAPTCHA solving",
            "not a pixel-faithful browser rendering",
        ],
    }
    receipt_path.write_text(
        f"{json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)}\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "screenshot_path": str(screenshot_path),
        "receipt_path": str(receipt_path),
    }


def _append_progress_row(*, progress_path: Path, row: dict[str, Any]) -> None:
    with progress_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{json.dumps(row, sort_keys=True)}\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_resume_rows(
    *, progress_path: Path, slots: Sequence[BatchSlot], resume: bool
) -> list[dict[str, Any]]:
    """Load journaled rows for a resumed run; refuse ambiguous states loudly.

    A journaled slot counts as attempted regardless of its exit code: the
    batch contract is one request per thread with no retry escalation, so a
    resume never re-requests a slot that already reached Reddit. Only slots
    with no journal row at all -- never started, or killed mid-capture before
    the row was written -- are (re)run.
    """
    if not progress_path.exists():
        if resume:
            raise ValueError(f"--resume requested but no progress journal at {progress_path}")
        return []
    if not resume:
        raise ValueError(
            f"progress journal already exists: {progress_path}; a prior run was "
            "interrupted here. Pass --resume to continue it, or choose a fresh "
            "--output-root."
        )
    url_by_slot_id = {slot.slot_id: slot.url for slot in slots}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(
        progress_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        slot_id = row.get("slot_id")
        if slot_id not in url_by_slot_id:
            raise ValueError(
                f"progress journal line {line_number} names slot_id {slot_id!r} "
                "absent from the supplied URL list; refusing to resume a "
                "different batch in this output_root"
            )
        if row.get("url") != url_by_slot_id[slot_id]:
            raise ValueError(
                f"progress journal line {line_number} URL differs from the "
                f"supplied URL list for slot_id {slot_id!r}; refusing to resume "
                "a different batch in this output_root"
            )
        if slot_id in seen:
            raise ValueError(
                f"progress journal repeats slot_id {slot_id!r}; refusing ambiguous resume"
            )
        seen.add(slot_id)
        rows.append(row)
    return rows


def load_slots(path: Path, *, transport: str = OLD_HTTP_TRANSPORT) -> list[BatchSlot]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("URL list must be a JSON array")

    slots: list[BatchSlot] = []
    for index, item in enumerate(payload, start=1):
        if isinstance(item, str):
            slot_id = f"slot_{index:03d}"
            url = item
        elif isinstance(item, dict):
            raw_slot_id = item.get("slot_id") or item.get("id")
            raw_url = item.get("url")
            if not isinstance(raw_slot_id, str) or not raw_slot_id.strip():
                raise ValueError(f"URL list item {index} must include a non-empty slot_id")
            if not isinstance(raw_url, str) or not raw_url.strip():
                raise ValueError(f"URL list item {index} must include a non-empty url")
            slot_id = raw_slot_id.strip()
            url = raw_url.strip()
        else:
            raise ValueError(f"URL list item {index} must be a string or object")
        slots.append(
            BatchSlot(
                slot_id=_validate_slot_id(slot_id),
                url=_validate_thread_url(url, transport=transport),
            )
        )
    return slots


def _validate_batch_inputs(
    *,
    slots: Sequence[BatchSlot],
    output_root: Path,
    delay_seconds: float,
    max_urls: int,
    timeout_seconds: float,
    max_bytes: int,
    transport: str = OLD_HTTP_TRANSPORT,
) -> None:
    if not slots:
        raise ValueError("batch requires at least one URL")
    if max_urls <= 0:
        raise ValueError("max_urls must be greater than zero")
    if len(slots) > max_urls:
        raise ValueError(f"batch received {len(slots)} URL(s), above max_urls={max_urls}")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be zero or greater")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")
    if output_root.exists() and not output_root.is_dir():
        raise ValueError(f"output_root exists and is not a directory: {output_root}")
    slot_ids = [slot.slot_id for slot in slots]
    duplicates = sorted({slot_id for slot_id in slot_ids if slot_ids.count(slot_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate slot_id value(s): {duplicates}")
    # Enforce the exact-URL/old.reddit.com-only and safe-slot-id bounds at the
    # execution boundary, not only in load_slots. run_reddit_old_http_batch and
    # BatchSlot are an importable API: a caller that builds slots directly must
    # not be able to bypass the host bound or smuggle a path-traversal slot_id
    # into the per-slot packet/derived directory names.
    for slot in slots:
        _validate_slot_id(slot.slot_id)
        _validate_thread_url(slot.url, transport=transport)


def _validate_slot_id(slot_id: str) -> str:
    if not slot_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("slot_id may contain only letters, numbers, underscore, and hyphen")
    return slot_id


def _validate_thread_url(url: str, *, transport: str = OLD_HTTP_TRANSPORT) -> str:
    host = TRANSPORT_HOSTS[transport]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname != host:
        raise ValueError(f"batch accepts only absolute {host} URLs on transport {transport}")
    if "/comments/" not in parsed.path:
        raise ValueError("batch accepts only Reddit thread URLs containing /comments/")
    return parsed.geturl()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a polite bounded old Reddit direct-HTTP content-extraction batch for "
            "an explicit JSON list of exact thread URLs."
        )
    )
    parser.add_argument("--url-list", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--transport",
        choices=list(THREAD_TRANSPORTS),
        default=OLD_HTTP_TRANSPORT,
        help=(
            "old_http: direct HTTP against old.reddit.com. www_realchrome: render "
            "www.reddit.com in the operator's real Chrome over CDP and expand the "
            "in-place comment tree before projecting."
        ),
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument(
        "--keep-raw-audit-sample",
        action="store_true",
        help="www transport only: keep the rendered DOM alongside the content record.",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help=(
            "Commit packets into the Forseti data lake at this root instead of per-slot "
            "local packet directories; the batch summary stays "
            "under --output-root."
        ),
    )
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--max-urls", type=int, default=DEFAULT_MAX_URLS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--cadence-mode", choices=["fixed", "bounded_jitter"], default=REDDIT_CADENCE_MODE
    )
    parser.add_argument(
        "--cadence-basis",
        choices=list(CADENCE_BASES),
        default=REDDIT_CADENCE_BASIS,
        help=(
            "gap: the cadence numbers are the wait BETWEEN captures. cycle: they "
            "are the target start-to-start interval and the capture duration is "
            "subtracted."
        ),
    )
    parser.add_argument("--cadence-window-seconds", type=float, default=None)
    # Default to the lane constants, NOT None. argparse defaults win over the
    # function signature, so None here silently discarded the lane's 31-46s
    # band on every CLI run and made bounded_jitter fail closed for want of a
    # derivable window.
    parser.add_argument(
        "--cadence-min-gap-seconds", type=float, default=REDDIT_CADENCE_MIN_GAP_SECONDS
    )
    parser.add_argument(
        "--cadence-max-gap-seconds", type=float, default=REDDIT_CADENCE_MAX_GAP_SECONDS
    )
    parser.add_argument("--cadence-random-seed", type=int, default=None)
    parser.add_argument(
        "--refusal-circuit-breaker",
        type=int,
        default=DEFAULT_REFUSAL_CIRCUIT_BREAKER,
        help=(
            "Stop the batch after this many consecutive server-side HTTP "
            "refusals instead of marching into the rate-limit window; "
            "unattempted slots stay resumable. 0 disables."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Continue an interrupted run in the same --output-root: slots already "
            "journaled in batch_progress.jsonl are carried, not re-requested."
        ),
    )
    parser.add_argument(
        "--retention-mode",
        choices=list(CAPTURE_RETENTION_MODES),
        default=DEFAULT_RETENTION_MODE,
        help=(
            "content (default): extract the thread in flight, preserve the content record, "
            "and discard raw after hashing; raw: preserve the response."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        data_root = None
        if args.data_root is not None:
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=args.data_root)
        exit_code, message = run_reddit_old_http_batch(
            slots=load_slots(args.url_list, transport=args.transport),
            output_root=args.output_root,
            transport=args.transport,
            cdp_endpoint=args.cdp_endpoint,
            keep_raw_audit_sample=args.keep_raw_audit_sample,
            decision_question=args.decision_question,
            data_root=data_root,
            delay_seconds=args.delay_seconds,
            max_urls=args.max_urls,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
            cadence_mode=args.cadence_mode,
            cadence_basis=args.cadence_basis,
            cadence_window_seconds=args.cadence_window_seconds,
            cadence_min_gap_seconds=args.cadence_min_gap_seconds,
            cadence_max_gap_seconds=args.cadence_max_gap_seconds,
            cadence_random_seed=args.cadence_random_seed,
            requested_retention_mode=args.retention_mode,
            resume=args.resume,
            refusal_circuit_breaker=args.refusal_circuit_breaker,
        )
    except ValueError as exc:
        parser.exit(status=2, message=f"reddit old HTTP batch failed: {exc}\n")
    except Exception as exc:
        parser.exit(status=3, message=f"reddit old HTTP batch failed: {exc}\n")

    print(message)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
