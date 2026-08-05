"""Bounded Reddit subreddit grid capture (radar lane, public dual-track route).

Captures ONE old Reddit listing page per named subreddit (the grid: the page
carries both the thread grid and the venue titlebox envelope) as a Source
Capture Packet with ``source_family="reddit_subreddit_grid"``, either into a
local output root or committed into the data lake (``--data-root``).

Owner contracts:
- forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_radar_grid_capture_maintenance_design_v0.md
- forseti/product/spines/capture/core/source_families/social_media/reddit/README.md (radar cadence + dual-track posture)

This runner performs one GET per subreddit per invocation with the shared
politeness cadence. It does not follow links, expand comments, capture
users/profiles, schedule itself, or claim ToS sufficiency; each run records
its source-policy posture receipt in the packet limitations.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import utc_now_z_microseconds
from runners._scaffold import exit_on_failure
from capture_spine.reddit_capture_cadence import (
    REDDIT_CADENCE_BASIS,
    REDDIT_CADENCE_MAX_GAP_SECONDS,
    REDDIT_CADENCE_MIN_GAP_SECONDS,
    REDDIT_CADENCE_MODE,
)
from capture_spine.reddit_subreddit_grid.grid_projection import (
    GRID_PROJECTION_PARSER_VERSION,
    build_grid_content_record,
    same_grid_listing_url,
)
from capture_spine.reddit_subreddit_grid.www_grid_projection import (
    WWW_GRID_PROJECTION_PARSER_VERSION,
    build_www_grid_content_record,
)
from runners.run_source_capture_http_packet import run_source_capture_http_packet
from source_capture.content_extraction import RenderedContentExtractionSpec
from source_capture import CaptureModeCategory
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
    ContentExtractionSpec,
)

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot

GRID_SOURCE_FAMILY = "reddit_subreddit_grid"
GRID_SOURCE_SURFACE = "old_reddit_direct_http"
WWW_GRID_SOURCE_SURFACE = "www_reddit_realchrome_cdp"
GRID_TRANSPORTS = ("old_http", "www_realchrome")
# Pacing is lane policy shared with the thread-dive runner; see
# capture_spine/reddit_capture_cadence.py for why cycle-and-jitter.
DEFAULT_CADENCE_MODE = REDDIT_CADENCE_MODE
DEFAULT_CADENCE_BASIS = REDDIT_CADENCE_BASIS
DEFAULT_CADENCE_MIN_GAP_SECONDS = REDDIT_CADENCE_MIN_GAP_SECONDS
DEFAULT_CADENCE_MAX_GAP_SECONDS = REDDIT_CADENCE_MAX_GAP_SECONDS
# Measured 2026-07-31: the www feed virtualizes, so scrolling UNLOADS the head.
# A tall viewport renders the head in one window instead (~102 rows, score floor
# 3), which is why depth comes from viewport height and never from scrolling.
WWW_VIEWPORT_WIDTH = 1280
WWW_VIEWPORT_HEIGHT = 20000
WWW_SETTLE_SECONDS = 15.0
# One marked tab is reused for the whole pass instead of opening and closing a
# tab per subreddit.  At roster size that is 91 tab churns in the operator's own
# browser, and a fresh tab per request is also a less natural session shape than
# one tab navigating between listings.
WWW_PERSISTENT_TAB_MARKER = "forseti-reddit-grid"
# A row is only usable once it carries the permalink the projection reads, so
# readiness is "at least one post WITH a permalink", not merely "a post element
# exists". That single selector covers both ways the 2026-07-31 pass failed:
# 4 subreddits snapshotted with no posts at all, and 4 with post elements whose
# attributes had not populated.
WWW_READY_SELECTOR = "shreddit-post[permalink]"
DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"
ALLOWED_LISTINGS = ("hot", "new", "top", "rising")
ALLOWED_TIME_WINDOWS = ("hour", "day", "week", "month", "year", "all")
DEFAULT_MAX_SUBREDDITS = 10
DEFAULT_DELAY_SECONDS = 30.0
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_BYTES = 5_000_000
# Content-mode is the standard fleet posture (storage-and-retention doctrine,
# 2026-07-17): derived record preserved, raw hashed then discarded. Raw and
# Raw remains the explicit operator-selected evidence posture.
DEFAULT_RETENTION_MODE = "content"

def check_grid_projection_anomaly(content_record: dict) -> str | None:
    """Name the projection anomaly this page exhibits, or None.

    An anomalous projection must not silently become the retained evidence:
    the caller raises, the capture falls back to raw preservation
    (``retention_outcome=raw_failure``), and the raw bytes stay auditable.
    Real listing pages carry data-timestamp on every row (measured 100/100,
    2026-07-22), so an all-None timestamp column means the parser broke, not
    the page.
    """
    grid_view = content_record.get("grid_view", {})
    rows = grid_view.get("thread_rows", [])
    if not rows:
        if grid_view.get("verified_empty_listing") is True:
            return None
        return "no_thread_rows"
    thing_count = grid_view.get("listing_thing_count_or_none")
    if thing_count is not None and thing_count != len(rows):
        return "thread_row_count_mismatch"
    if grid_view.get("listing_permalink_count_or_none") == 0:
        return "no_permalinks"
    if all(row.get("timestamp_utc_ms_or_none") is None for row in rows):
        return "no_timestamps"
    return None


class GridProjectionAnomalyError(ValueError):
    pass


def build_validated_grid_content_record(
    *,
    html_text: str,
    final_url: str,
    subreddit: str,
    listing_url: str,
) -> dict:
    """Build one record while preserving zero-row failure visibility."""
    record = build_grid_content_record(
        html_text=html_text,
        subreddit=subreddit,
        listing_url=listing_url,
    )
    if (
        record.get("grid_view", {}).get("verified_empty_listing") is True
        and not same_grid_listing_url(final_url, listing_url)
    ):
        raise GridProjectionAnomalyError(
            "grid projection anomaly [empty_listing_final_url_mismatch]: "
            "keeping raw for audit"
        )
    anomaly = check_grid_projection_anomaly(record)
    if anomaly is not None:
        raise GridProjectionAnomalyError(
            f"grid projection anomaly [{anomaly}]: keeping raw for audit"
        )
    return record


def build_validated_www_grid_content_record(
    *,
    rendered_dom: str,
    visible_text: str,
    final_url: str,
    subreddit: str,
    listing_url: str,
) -> dict:
    """Build one www record while preserving anomalous rendered source."""
    record = build_www_grid_content_record(
        rendered_dom=rendered_dom,
        visible_text=visible_text,
        subreddit=subreddit,
        listing_url=listing_url,
    )
    if (
        record.get("grid_view", {}).get("verified_empty_listing") is True
        and not same_grid_listing_url(final_url, listing_url)
    ):
        raise GridProjectionAnomalyError(
            "grid projection anomaly [empty_listing_final_url_mismatch]: "
            "keeping raw for audit"
        )
    anomaly = check_grid_projection_anomaly(record)
    if anomaly is not None:
        raise GridProjectionAnomalyError(
            f"grid projection anomaly [{anomaly}]: keeping raw for audit"
        )
    return record


def _paced_wait(
    *, planned: float, elapsed: float, basis: str, row: dict[str, Any]
) -> float:
    """Apply the shared cadence basis and record any overrun on the row."""
    wait, overrun = resolve_paced_wait(planned=planned, elapsed=elapsed, basis=basis)
    if overrun > 0:
        row["cadence_overrun_seconds"] = overrun
    return wait


def _rotating_raw_sample(names: Sequence[str], *, on_date: _dt.date) -> str:
    """Select one sample with a +1 weekly index across year boundaries."""
    ordered = sorted(names)
    monday = on_date - _dt.timedelta(days=on_date.weekday())
    return ordered[(monday.toordinal() // 7) % len(ordered)]


# States the decision predicate, not a description of the file. A re-check
# compared against a description escalates on any scope or wording drift; against
# the predicate it escalates only when the decision could change. Halt routing is
# owned by the radar design's policy gate.
SOURCE_POLICY_POSTURE_RECEIPT = (
    "source-policy posture: the subreddit listing surface this runner captures is "
    "robots-disallowed for us, and the owner accepted capturing it anyway as a bounded "
    "single-page pass under the measured-risk dual-track posture (Reddit lane README, "
    "2026-07-16). A broader or reworded disallow does not re-open that; halt only if the "
    "surface becomes allowed, a hard access gate appears, or the accepted bound is "
    "exceeded. Observed 2026-07-22: 'User-agent: * / Disallow: /' on www and old.reddit, "
    "user-agent-independent and byte-identical to an independent archive crawl. "
    "Not ToS sufficiency, not legal advice"
)


def build_www_grid_listing_url(
    *, subreddit: str, listing: str, time_window: str | None
) -> str:
    """Build one new-Reddit listing URL.

    No ``limit`` parameter exists here on purpose: www ignores it, and the
    rendered VIEWPORT is what bounds the page (a 1280x20000 window returns ~102
    rows). Accepting a limit would let an operator believe they had capped depth
    when nothing read the value.
    """
    name = _validate_subreddit(subreddit)
    if listing not in ALLOWED_LISTINGS:
        raise ValueError(f"listing must be one of {ALLOWED_LISTINGS}, got {listing!r}")
    url = f"https://www.reddit.com/r/{name}/{listing}/"
    if listing == "top":
        window = time_window or "day"
        if window not in ALLOWED_TIME_WINDOWS:
            raise ValueError(f"time window must be one of {ALLOWED_TIME_WINDOWS}, got {window!r}")
        url += f"?t={window}"
    elif time_window is not None:
        raise ValueError("time window applies only to the top listing")
    return url


def build_grid_listing_url(
    *, subreddit: str, listing: str, time_window: str | None, limit: int | None = None
) -> str:
    name = _validate_subreddit(subreddit)
    if listing not in ALLOWED_LISTINGS:
        raise ValueError(f"listing must be one of {ALLOWED_LISTINGS}, got {listing!r}")
    url = f"https://old.reddit.com/r/{name}/{listing}/"
    query: list[str] = []
    if listing == "top":
        window = time_window or "day"
        if window not in ALLOWED_TIME_WINDOWS:
            raise ValueError(f"time window must be one of {ALLOWED_TIME_WINDOWS}, got {window!r}")
        query.append(f"t={window}")
    elif time_window is not None:
        raise ValueError("time window applies only to the top listing")
    if limit is not None:
        # Old Reddit serves at most 100 rows per page; still one page per sub.
        if not 1 <= limit <= 100:
            raise ValueError(f"limit must be between 1 and 100, got {limit!r}")
        query.append(f"limit={limit}")
    if query:
        url += "?" + "&".join(query)
    return url


def _capture_www_grid(
    *,
    subreddit: str,
    url: str,
    decision_question: str,
    output_directory: Path | None,
    data_root: "DataLakeRoot | None",
    cdp_endpoint: str,
    keep_raw_audit_sample: bool,
    timeout_seconds: float,
    listing: str,
    time_window: str | None,
    cadence_plan: Any,
    index: int,
) -> tuple[int, str]:
    """Capture one www listing through the operator's real Chrome.

    Deliberately routed through the shared real-Chrome runner rather than a
    second orchestrator: the roster, cadence, batch summary, and duplicate
    checks above are transport-agnostic and stay single-homed.
    """
    from runners.run_source_capture_realchrome_cdp_packet import (
        run_source_capture_realchrome_cdp_packet,
    )
    from source_capture.rendered_retention import require_content_retention

    def _extract(rendered_dom: bytes, visible_text: bytes, _final_url: str) -> dict:
        return build_validated_www_grid_content_record(
            rendered_dom=rendered_dom.decode("utf-8", errors="replace"),
            visible_text=visible_text.decode("utf-8", errors="replace"),
            final_url=_final_url,
            subreddit=subreddit,
            listing_url=url,
        )

    spec = require_content_retention(
        RenderedContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version=WWW_GRID_PROJECTION_PARSER_VERSION,
            extractor=_extract,
        ),
        lane="reddit www grid capture",
    )
    return run_source_capture_realchrome_cdp_packet(
        url=url,
        source_family=GRID_SOURCE_FAMILY,
        source_surface=WWW_GRID_SOURCE_SURFACE,
        decision_question=decision_question,
        output_directory=output_directory,
        data_root=data_root,
        capture_context=(
            "bounded reddit subreddit grid pass over the www listing surface; one declared "
            "listing page per subreddit; no link following, comment expansion, user/profile "
            "capture, or self-scheduling"
        ),
        cdp_endpoint=cdp_endpoint,
        persistent_tab_marker=WWW_PERSISTENT_TAB_MARKER,
        ready_selector=WWW_READY_SELECTOR,
        viewport_width=WWW_VIEWPORT_WIDTH,
        viewport_height=WWW_VIEWPORT_HEIGHT,
        settle_seconds=WWW_SETTLE_SECONDS,
        timeout_seconds=timeout_seconds,
        content_extraction=spec,
        capture_screenshot=False,
        keep_raw_audit_sample=keep_raw_audit_sample,
        target_identity_check=lambda final_url: same_grid_listing_url(final_url, url),
        target_identity_description="same Reddit grid host, path, and query",
        limitations=[
            SOURCE_POLICY_POSTURE_RECEIPT,
            f"grid runner listing={listing} time_window={time_window or 'n/a'} transport=www_realchrome",
            f"grid runner cadence_mode={cadence_plan.mode}",
            f"grid runner planned_start_offset_seconds={cadence_plan.planned_offsets_seconds[index]}",
            "grid runner retry_count=0",
            "www depth is bounded by the rendered viewport, not by a listing limit",
        ],
    )


def run_reddit_grid_capture(
    *,
    subreddits: Sequence[str],
    listing: str,
    time_window: str | None,
    output_root: Path,
    decision_question: str,
    limit: int | None = None,
    data_root: "DataLakeRoot | None" = None,
    max_subreddits: int = DEFAULT_MAX_SUBREDDITS,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    cadence_mode: CadenceMode = DEFAULT_CADENCE_MODE,
    cadence_window_seconds: float | None = None,
    cadence_min_gap_seconds: float | None = DEFAULT_CADENCE_MIN_GAP_SECONDS,
    cadence_max_gap_seconds: float | None = DEFAULT_CADENCE_MAX_GAP_SECONDS,
    cadence_random_seed: int | None = None,
    requested_retention_mode: str = DEFAULT_RETENTION_MODE,
    transport: str = "old_http",
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
    cadence_basis: str = DEFAULT_CADENCE_BASIS,
) -> tuple[int, str]:
    if requested_retention_mode not in CAPTURE_RETENTION_MODES:
        raise ValueError(
            f"requested_retention_mode must be one of {CAPTURE_RETENTION_MODES}, "
            f"got {requested_retention_mode!r}"
        )
    if cadence_basis not in CADENCE_BASES:
        raise ValueError(f"cadence_basis must be one of {CADENCE_BASES}, got {cadence_basis!r}")
    if transport not in GRID_TRANSPORTS:
        raise ValueError(f"transport must be one of {GRID_TRANSPORTS}, got {transport!r}")
    if transport == "www_realchrome":
        # Never raw-only binds this lane, so a raw request is refused here rather
        # than quietly downgraded (weekly demand radar spec, owner 2026-07-31).
        if requested_retention_mode != "content":
            raise ValueError(
                "the www transport binds never-raw-only; "
                f"refusing retention mode {requested_retention_mode!r}"
            )
        if limit is not None:
            raise ValueError(
                "www ignores a listing limit; depth comes from the rendered "
                "viewport, so a limit here would be a cap that nothing enforces"
            )
    _validate_grid_inputs(
        subreddits=subreddits,
        output_root=output_root,
        max_subreddits=max_subreddits,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
    )
    names = [_validate_subreddit(name) for name in subreddits]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate subreddit value(s): {duplicates}")
    if transport == "www_realchrome":
        urls = [
            build_www_grid_listing_url(subreddit=name, listing=listing, time_window=time_window)
            for name in names
        ]
    else:
        urls = [
            build_grid_listing_url(
                subreddit=name, listing=listing, time_window=time_window, limit=limit
            )
            for name in names
        ]

    # Retention rule 1 (weekly demand radar spec): on a content-mode weekly
    # pass, one rotating subreddit keeps raw as the projection audit sample.
    # The absolute Monday index advances by one across year boundaries.
    raw_sample_subreddit: str | None = None
    if requested_retention_mode == "content" and listing == "top" and time_window == "week":
        raw_sample_subreddit = _rotating_raw_sample(
            names,
            on_date=_dt.datetime.now(_dt.timezone.utc).date(),
        )

    if cadence_mode == "bounded_jitter" and cadence_window_seconds is None:
        # Derivable; requiring it by hand only produces a launch failure or a
        # silently compressed range.
        cadence_window_seconds = resolve_cadence_window_seconds(
            slot_count=len(names), max_gap_seconds=cadence_max_gap_seconds
        )
    cadence_plan = build_cadence_plan(
        slot_count=len(names),
        mode=cadence_mode,
        delay_seconds=delay_seconds,
        window_seconds=cadence_window_seconds,
        min_gap_seconds=cadence_min_gap_seconds,
        max_gap_seconds=cadence_max_gap_seconds,
        random_seed=cadence_random_seed,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = output_root / "grid_batch_summary.json"
    if summary_path.exists():
        raise ValueError(f"grid batch summary already exists: {summary_path}")

    results: list[dict[str, Any]] = []
    for index, (name, url) in enumerate(zip(names, urls)):
        row: dict[str, Any] = {
            "subreddit": name,
            "listing_url": url,
            "capture_exit": None,
            "capture_message": None,
            "packet_path": None,
            "planned_start_offset_seconds": cadence_plan.planned_offsets_seconds[index],
            "capture_started_at": None,
            "capture_finished_at": None,
            "content_extraction_failed": False,
        }
        # Retention rule 2: an anomalous projection raises, so the capture
        # falls back to raw preservation instead of retaining broken evidence.
        def _extract(html_text: str, _final_url: str, _name: str = name, _url: str = url) -> dict:
            return build_validated_grid_content_record(
                html_text=html_text,
                final_url=_final_url,
                subreddit=_name,
                listing_url=_url,
            )

        if transport == "www_realchrome":
            # The audit sample keeps raw ALONGSIDE its content record rather
            # than instead of it.  A raw-only sample is what banked a login wall
            # and still exited 0 on 2026-07-30, because with no projection to
            # run there was nothing to fail.
            row["retention_mode"] = "content"
            row["raw_audit_sample"] = name == raw_sample_subreddit
            row["capture_started_at"] = utc_now_z_microseconds()
            capture_started_monotonic = time.monotonic()
            try:
                capture_exit, capture_message = _capture_www_grid(
                    subreddit=name,
                    url=url,
                    decision_question=decision_question,
                    output_directory=(
                        None if data_root is not None else output_root / f"{name}_grid_packet"
                    ),
                    data_root=data_root,
                    cdp_endpoint=cdp_endpoint,
                    keep_raw_audit_sample=name == raw_sample_subreddit,
                    timeout_seconds=timeout_seconds,
                    listing=listing,
                    time_window=time_window,
                    cadence_plan=cadence_plan,
                    index=index,
                )
                row["capture_exit"] = capture_exit
                row["capture_message"] = capture_message
                if capture_exit in (0, CONTENT_EXTRACTION_FAILED_EXIT_CODE):
                    row["packet_path"] = capture_message
                if capture_exit == CONTENT_EXTRACTION_FAILED_EXIT_CODE:
                    row["content_extraction_failed"] = True
            except Exception as exc:
                row["capture_exit"] = 2
                row["capture_message"] = f"{type(exc).__name__}: {exc}"
            row["capture_finished_at"] = utc_now_z_microseconds()
            elapsed = time.monotonic() - capture_started_monotonic
            row["capture_elapsed_seconds"] = round(elapsed, 3)
            results.append(row)
            if index < len(cadence_plan.planned_waits_seconds):
                wait_seconds = _paced_wait(
                    planned=cadence_plan.planned_waits_seconds[index],
                    elapsed=elapsed,
                    basis=cadence_basis,
                    row=row,
                )
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
            continue

        row_retention = (
            "raw" if name == raw_sample_subreddit else requested_retention_mode
        )
        row["retention_mode"] = row_retention
        extraction_spec = ContentExtractionSpec(
                requested_retention_mode=row_retention,
                extractor_version=GRID_PROJECTION_PARSER_VERSION,
                extractor=_extract,
                # The rotating raw sample exists to audit the projection, so it
                # must itself be checked: without this it is the one packet that
                # can bank a login wall and still report success.
                validate_in_raw_mode=True,
            )
        capture_started_monotonic = time.monotonic()
        try:
            row["capture_started_at"] = utc_now_z_microseconds()
            capture_exit, capture_message = run_source_capture_http_packet(
                url=url,
                source_family=GRID_SOURCE_FAMILY,
                source_surface=GRID_SOURCE_SURFACE,
                decision_question=decision_question,
                output_directory=None if data_root is not None else output_root / f"{name}_grid_packet",
                data_root=data_root,
                capture_context=(
                    "bounded reddit subreddit grid pass; one declared listing page per subreddit; "
                    "no link following, comment expansion, user/profile capture, or self-scheduling"
                ),
                operator_category="reddit_grid_capture_operator",
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
                    SOURCE_POLICY_POSTURE_RECEIPT,
                    f"grid runner listing={listing} time_window={time_window or 'n/a'}",
                    f"grid runner cadence_mode={cadence_plan.mode}",
                    f"grid runner planned_start_offset_seconds={cadence_plan.planned_offsets_seconds[index]}",
                    "grid runner retry_count=0",
                ],
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
                content_extraction=extraction_spec,
            )
            row["capture_exit"] = capture_exit
            row["capture_message"] = capture_message
            if capture_exit in (0, CONTENT_EXTRACTION_FAILED_EXIT_CODE):
                row["packet_path"] = capture_message
            if capture_exit == CONTENT_EXTRACTION_FAILED_EXIT_CODE:
                row["content_extraction_failed"] = True
        except Exception as exc:
            row["capture_exit"] = 2
            row["capture_message"] = f"{type(exc).__name__}: {exc}"
        finally:
            row["capture_finished_at"] = utc_now_z_microseconds()

        elapsed = time.monotonic() - capture_started_monotonic
        row["capture_elapsed_seconds"] = round(elapsed, 3)
        results.append(row)
        if index < len(cadence_plan.planned_waits_seconds):
            wait_seconds = _paced_wait(
                planned=cadence_plan.planned_waits_seconds[index],
                elapsed=elapsed,
                basis=cadence_basis,
                row=row,
            )
            if wait_seconds > 0:
                time.sleep(wait_seconds)

    summary = {
        "runner": "reddit_grid_capture",
        "method": (
            WWW_GRID_SOURCE_SURFACE if transport == "www_realchrome" else GRID_SOURCE_SURFACE
        ),
        "transport": transport,
        "cadence_basis": cadence_basis,
        "listing": listing,
        "time_window": time_window,
        "limit": limit,
        "requested_retention_mode": requested_retention_mode,
        "raw_sample_subreddit": raw_sample_subreddit,
        "content_extraction_failure_count": sum(
            1 for row in results if row["content_extraction_failed"]
        ),
        "lake_committed": data_root is not None,
        "source_policy_posture": SOURCE_POLICY_POSTURE_RECEIPT,
        "non_claims": [
            "not crawler",
            "not monitoring or self-scheduling",
            "not link following or comment expansion",
            "not user or profile capture",
            "not ToS sufficiency",
            "not demand proof or venue scoring",
        ],
        "cadence": cadence_plan.to_dict(),
        "max_subreddits": max_subreddits,
        "subreddit_count": len(names),
        "capture_success_count": sum(1 for row in results if row["capture_exit"] == 0),
        "results": results,
    }
    summary_path.write_text(
        f"{json.dumps(summary, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0, str(summary_path)


def _validate_subreddit(name: str) -> str:
    stripped = name.strip().lower().removeprefix("r/")
    if (
        not stripped
        or not stripped.isascii()
        or not stripped.replace("_", "").isalnum()
    ):
        raise ValueError(f"invalid subreddit name: {name!r}")
    return stripped


def _validate_grid_inputs(
    *,
    subreddits: Sequence[str],
    output_root: Path,
    max_subreddits: int,
    timeout_seconds: float,
    max_bytes: int,
) -> None:
    if not subreddits:
        raise ValueError("grid capture requires at least one subreddit")
    if max_subreddits <= 0:
        raise ValueError("max_subreddits must be greater than zero")
    if len(subreddits) > max_subreddits:
        raise ValueError(f"received {len(subreddits)} subreddit(s), above max_subreddits={max_subreddits}")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")
    if output_root.exists() and not output_root.is_dir():
        raise ValueError(f"output_root exists and is not a directory: {output_root}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture one old Reddit listing (grid) page per named subreddit as a "
            "reddit_subreddit_grid Source Capture Packet, locally or into the data lake."
        )
    )
    parser.add_argument("--subreddit", action="append", dest="subreddits", default=None)
    parser.add_argument(
        "--roster",
        action="store_true",
        help="Capture every subreddit the lake registry tracks (requires --data-root).",
    )
    parser.add_argument("--listing", choices=ALLOWED_LISTINGS, default="top")
    parser.add_argument(
        "--transport",
        choices=list(GRID_TRANSPORTS),
        default="old_http",
        help=(
            "old_http: direct HTTP against old.reddit (blocked for this client since "
            "2026-07-30). www_realchrome: operator real Chrome over CDP against www."
        ),
    )
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument(
        "--cadence-basis",
        choices=list(CADENCE_BASES),
        default=DEFAULT_CADENCE_BASIS,
        help=(
            "gap: cadence numbers are the wait BETWEEN captures, so the real "
            "request interval is the gap plus the capture duration. cycle: they "
            "are the target start-to-start interval and the capture duration is "
            "subtracted."
        ),
    )
    parser.add_argument("--time-window", choices=ALLOWED_TIME_WINDOWS, default=None)
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Rows per listing page (1-100); still one page per subreddit.",
    )
    parser.add_argument("--output-root", type=Path, required=True,
                        help="Local root for the grid batch summary (and packets when --data-root is not used).")
    parser.add_argument("--data-root", default=None,
                        help="Commit packets into the Forseti data lake at this root instead of --output-root.")
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--max-subreddits", type=int, default=DEFAULT_MAX_SUBREDDITS)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--cadence-mode",
        choices=["fixed", "bounded_jitter"],
        default=DEFAULT_CADENCE_MODE,
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
        "--retention-mode",
        choices=list(CAPTURE_RETENTION_MODES),
        default=DEFAULT_RETENTION_MODE,
        help=(
            "content (default): preserve the content record, hash then discard raw; "
            "raw: preserve the source response."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    with exit_on_failure(parser, runner_name="reddit grid capture"):
        data_root = None
        if args.data_root is not None:
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=args.data_root)
        if args.roster == bool(args.subreddits):
            raise ValueError("provide exactly one of --roster or --subreddit")
        subreddits = args.subreddits
        if args.roster:
            if data_root is None:
                raise ValueError("--roster reads the lake registry; --data-root is required")
            # capture_roster, not known_subreddits: retired rows keep their
            # history in the fold but must not cost a request per pass.
            from data_lake.reddit_subreddit_registry import capture_roster

            subreddits = capture_roster(data_root)
            if not subreddits:
                raise ValueError("--roster found no tracked subreddits in the lake registry")
        exit_code, message = run_reddit_grid_capture(
            subreddits=subreddits,
            listing=args.listing,
            time_window=args.time_window,
            limit=args.limit,
            output_root=args.output_root,
            data_root=data_root,
            decision_question=args.decision_question,
            max_subreddits=args.max_subreddits,
            delay_seconds=args.delay_seconds,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
            cadence_mode=args.cadence_mode,
            cadence_window_seconds=args.cadence_window_seconds,
            cadence_min_gap_seconds=args.cadence_min_gap_seconds,
            cadence_max_gap_seconds=args.cadence_max_gap_seconds,
            cadence_random_seed=args.cadence_random_seed,
            requested_retention_mode=args.retention_mode,
            transport=args.transport,
            cdp_endpoint=args.cdp_endpoint,
            cadence_basis=args.cadence_basis,
        )

    print(message)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
