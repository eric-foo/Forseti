"""Assess one YouTube creator from public logged-out surfaces.

The runner is deliberately assessment-first. It performs no Creator Registry
write; owner review of the packet precedes candidate/account admission.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import statistics
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture_spine.creator_profile_current.registry_match_preflight import (
    RECEIPT_WRAPPER_KEY,
    build_creator_registry_match_preflight_receipt,
    dump_creator_registry_match_preflight_receipt,
)
from data_lake.canonical_json import canonical_record_bytes
from data_lake.creator_registry import load_current_registry_preflight_view
from data_lake.root import DataLakeRoot
from source_capture.youtube_creator_assessment import (
    ASSESSMENT_SCHEMA_VERSION,
    write_youtube_creator_assessment_packet,
)

SUMMARY_PREFIX = "youtube_creator_onboarding_summary_json="
BLOCKER_PREFIX = "youtube_creator_onboarding_blocker_json="
REGISTRY_PREFLIGHT_JSON_NAME = "creator_registry_match_preflight.json"
FRONTIER_SCHEMA_VERSION = "youtube_creator_frontier_candidates_v0"
DEFAULT_DECISION_QUESTION = (
    "Does this public YouTube channel warrant owner-reviewed Creator Registry admission?"
)
_CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_HANDLE = re.compile(r"[A-Za-z0-9._-]{3,30}")
_AMBIGUOUS_TITLE = re.compile(
    r"\b(this|that|it|works?|worth it|love|hate|best|worst|avoid|warning|review|why)\b",
    re.IGNORECASE,
)
_COUNT = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*(?P<suffix>[KMB])?", re.IGNORECASE)


class YoutubeCreatorAssessmentError(RuntimeError):
    """Visible, fail-closed creator assessment failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Assess one YouTube creator in a fresh logged-out browser context, or export "
            "SERP-derived YouTube frontier candidates."
        )
    )
    parser.add_argument("--creator-display-name")
    parser.add_argument("--profile-url")
    parser.add_argument(
        "--evidence-video-url",
        help=(
            "Source-observed YouTube video URL attributed to the requested display name; "
            "used to resolve immutable channel identity without choosing among search-name collisions."
        ),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--data-root")
    parser.add_argument("--registry-view", type=Path)
    parser.add_argument("--browser-channel")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument("--grid-scroll-passes", type=int, default=3)
    parser.add_argument("--max-grid-rows", type=int, default=30)
    parser.add_argument("--selected-videos-per-format", type=int, default=3)
    parser.add_argument("--decision-question", default=DEFAULT_DECISION_QUESTION)
    parser.add_argument("--export-frontier", type=Path)
    parser.add_argument("--recurring-feed", type=Path)
    parser.add_argument("--suffix-extract-dir", type=Path)
    parser.add_argument("--suffix-quality", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.export_frontier is not None:
            if args.recurring_feed is None:
                raise ValueError("--export-frontier requires --recurring-feed")
            document = build_youtube_frontier_candidates(
                recurring_feed=_load_json(args.recurring_feed),
                suffix_extract_dir=args.suffix_extract_dir,
            )
            if args.suffix_quality is not None:
                expected = int(
                    _load_json(args.suffix_quality)["shapes"]["youtube_suffix"][
                        "creators_not_in_113_feed"
                    ]
                )
                observed = document["youtube_creator_frontier_candidates"]["counts"][
                    "suffix_feed_absent"
                ]
                if observed != expected:
                    raise YoutubeCreatorAssessmentError(
                        f"suffix candidate count mismatch: expected {expected}, observed {observed}"
                    )
            _write_json(args.export_frontier, document)
            print(
                SUMMARY_PREFIX
                + json.dumps(
                    {
                        "mode": "frontier_export",
                        "output": str(args.export_frontier),
                        **document["youtube_creator_frontier_candidates"]["counts"],
                    },
                    sort_keys=True,
                )
            )
            return 0

        if not args.creator_display_name or args.output_dir is None:
            raise ValueError("assessment requires --creator-display-name and --output-dir")
        if args.max_grid_rows <= 0 or args.selected_videos_per_format < 0:
            raise ValueError("grid/video bounds must be non-negative and max-grid-rows must be positive")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        registry_document, registry_pointer, registry_hash = _registry_preflight_source(
            data_root_value=args.data_root,
            registry_view=args.registry_view,
        )
        preflight = build_creator_registry_match_preflight_receipt(
            candidates=[
                {
                    "candidate_id": "youtube_display_name_" + _slug(args.creator_display_name),
                    "platform": "youtube",
                    "display_name_or_none": args.creator_display_name,
                    "public_profile_url_or_none": args.profile_url,
                    "intended_action": "new_capture",
                }
            ],
            registry_document=registry_document,
            registry_source_pointer=registry_pointer,
            registry_sha256=registry_hash,
            generated_at_utc=_utc_now(),
        )
        preflight_path = args.output_dir / REGISTRY_PREFLIGHT_JSON_NAME
        preflight_path.write_text(
            dump_creator_registry_match_preflight_receipt(preflight), encoding="utf-8"
        )
        result = preflight[RECEIPT_WRAPPER_KEY]["results"][0]
        if result.get("can_start_new_capture") is not True:
            raise YoutubeCreatorAssessmentError(
                "Creator Registry preflight blocked new capture: "
                + json.dumps(result, sort_keys=True)
            )

        assessment = capture_youtube_creator_assessment(
            creator_display_name=args.creator_display_name,
            profile_url=args.profile_url,
            evidence_video_url=args.evidence_video_url,
            browser_channel=args.browser_channel,
            headless=not args.headed,
            timeout_seconds=args.timeout_seconds,
            settle_seconds=args.settle_seconds,
            grid_scroll_passes=args.grid_scroll_passes,
            max_grid_rows=args.max_grid_rows,
            selected_videos_per_format=args.selected_videos_per_format,
        )
        assessment_bytes = canonical_record_bytes(assessment)
        assessment_path = args.output_dir / "assessment.json"
        assessment_path.write_bytes(assessment_bytes)
        packet_dir = args.output_dir / "source_capture_packet"
        exit_code, packet = write_youtube_creator_assessment_packet(
            assessment_json=assessment_bytes,
            output_directory=packet_dir,
            decision_question=args.decision_question,
        )
        if exit_code != 0:
            raise YoutubeCreatorAssessmentError(str(packet))
        summary = assessment_summary(assessment)
        summary.update(
            {
                "mode": "new_capture",
                "registry_preflight": str(preflight_path),
                "assessment_json": str(assessment_path),
                "packet": str(packet),
                "registry_mutated": False,
            }
        )
        print(SUMMARY_PREFIX + json.dumps(summary, sort_keys=True))
        return 0
    except (ValueError, OSError, YoutubeCreatorAssessmentError) as exc:
        print(
            BLOCKER_PREFIX
            + json.dumps(
                {"code": type(exc).__name__, "message": str(exc), "registry_mutated": False},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 3


def build_youtube_frontier_candidates(
    *, recurring_feed: Mapping[str, Any], suffix_extract_dir: Path | None
) -> dict[str, Any]:
    """Build display-name candidates without pretending they are resolved identities."""
    recurring: dict[str, dict[str, Any]] = {}
    creators = recurring_feed.get("creators")
    if not isinstance(creators, list):
        raise ValueError("recurring feed creators must be a list")
    all_feed_names = {
        _normalized_name(str(row.get("display_name")))
        for row in creators
        if isinstance(row, Mapping) and str(row.get("display_name") or "").strip()
    }
    for row in creators:
        if not isinstance(row, Mapping) or str(row.get("platform")).casefold() != "youtube":
            continue
        name = _required_text(row.get("display_name"), "recurring creator display_name")
        recurring[_normalized_name(name)] = {
            "candidate_id": "yt_serp_recurring_" + _stable_token(name),
            "platform": "youtube",
            "display_name": name,
            "profile_url_or_none": row.get("profile_url_or_none"),
            "subjects": sorted(str(value) for value in row.get("subjects", []) if str(value).strip()),
            "scope_or_none": row.get("scope"),
            "source_kind": "serp_recurring_2plus_subjects",
            "identity_state": "display_name_only_requires_assessment_resolution",
            "non_claims": ["not resolved channel identity", "not owner disposition"],
        }

    suffix: dict[str, dict[str, Any]] = {}
    if suffix_extract_dir is not None:
        if not suffix_extract_dir.is_dir():
            raise ValueError(f"suffix extract directory does not exist: {suffix_extract_dir}")
        evidence: dict[str, list[dict[str, str]]] = defaultdict(list)
        display_names: dict[str, str] = {}
        for path in sorted(suffix_extract_dir.glob("*.json"), key=lambda value: value.name):
            document = _load_json(path)
            query = str(document.get("requested_query") or "").strip()
            if not query.casefold().endswith(" youtube"):
                continue
            subject = query[: -len(" youtube")].strip()
            rows = document.get("rows")
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, Mapping) or str(row.get("platform")).casefold() != "youtube":
                    continue
                name = str(row.get("account_or_creator") or "").strip()
                if not name:
                    continue
                key = _normalized_name(name)
                if key in all_feed_names:
                    continue
                display_names.setdefault(key, name)
                evidence[key].append(
                    {
                        "subject": subject,
                        "source_file": path.name,
                        "source_url_or_none": str(row.get("canonical_url") or "") or None,
                    }
                )
        for key in sorted(evidence):
            name = display_names[key]
            suffix[key] = {
                "candidate_id": "yt_serp_suffix_" + _stable_token(name),
                "platform": "youtube",
                "display_name": name,
                "profile_url_or_none": None,
                "subjects": sorted({row["subject"] for row in evidence[key]}),
                "source_kind": "serp_youtube_suffix_feed_absent",
                "source_evidence": evidence[key],
                "identity_state": "display_name_only_requires_assessment_resolution",
                "non_claims": [
                    "not recurrence-qualified unless subjects contains 2plus values",
                    "not resolved channel identity",
                    "not owner disposition",
                ],
            }
    candidates = [recurring[key] for key in sorted(recurring)] + [
        suffix[key] for key in sorted(suffix)
    ]
    return {
        "youtube_creator_frontier_candidates": {
            "schema_version": FRONTIER_SCHEMA_VERSION,
            "generated_at_utc": _utc_now(),
            "counts": {
                "recurring_feed": len(recurring),
                "suffix_feed_absent": len(suffix),
                "total": len(candidates),
            },
            "candidates": candidates,
            "non_claims": [
                "display names are frontier inputs, not resolved YouTube identities",
                "frontier input is not an eligible/deferred/rejected owner disposition",
                "observed recurrence evidences reach, not independence or sponsorship",
            ],
        }
    }


def capture_youtube_creator_assessment(
    *,
    creator_display_name: str,
    profile_url: str | None,
    evidence_video_url: str | None,
    browser_channel: str | None,
    headless: bool,
    timeout_seconds: float,
    settle_seconds: float,
    grid_scroll_passes: int,
    max_grid_rows: int,
    selected_videos_per_format: int,
) -> dict[str, Any]:
    """Acquire one creator in exactly one fresh browser context."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise YoutubeCreatorAssessmentError(
            "Playwright is unavailable; install the harness browser extra"
        ) from exc

    timeout_ms = int(timeout_seconds * 1000)
    with sync_playwright() as playwright:
        launch_kwargs: dict[str, Any] = {"headless": headless}
        if browser_channel:
            launch_kwargs["channel"] = browser_channel
        browser = playwright.chromium.launch(**launch_kwargs)
        context = browser.new_context()
        try:
            page = context.new_page()
            identity, resolution = _resolve_channel(
                page,
                creator_display_name=creator_display_name,
                profile_url=profile_url,
                evidence_video_url=evidence_video_url,
                timeout_ms=timeout_ms,
                settle_seconds=settle_seconds,
            )
            _assert_logged_out(page)
            profile = _capture_profile(page, identity["profile_url"], timeout_ms, settle_seconds)
            grids = {
                "long": _capture_grid(
                    page,
                    url=f"{identity['profile_url']}/videos",
                    format_name="long",
                    timeout_ms=timeout_ms,
                    settle_seconds=settle_seconds,
                    scroll_passes=grid_scroll_passes,
                    max_rows=max_grid_rows,
                ),
                "short": _capture_grid(
                    page,
                    url=f"{identity['profile_url']}/shorts",
                    format_name="short",
                    timeout_ms=timeout_ms,
                    settle_seconds=settle_seconds,
                    scroll_passes=grid_scroll_passes,
                    max_rows=max_grid_rows,
                ),
            }
            selected = _select_video_rows(grids, selected_videos_per_format)
            selected_pages = [
                _capture_selected_video(page, row, timeout_ms=timeout_ms, settle_seconds=settle_seconds)
                for row in selected
            ]
            _assert_logged_out(page)
            return {
                "schema_version": ASSESSMENT_SCHEMA_VERSION,
                "captured_at_utc": _utc_now(),
                "identity": identity,
                "identity_resolution": resolution,
                "session_posture": {
                    "required": "logged_out_fresh_browser_context",
                    "observed_logged_in": False,
                    "context_reused": False,
                    "stored_session_loaded": False,
                },
                "profile": profile,
                "grids": grids,
                "selected_video_pages": selected_pages,
                "transcript_policy": {
                    "captions_first": True,
                    "asr_fallback": "route caption-absent triggered videos to run_asr_transcript_catchup",
                    "trigger": "same-format at_or_above_median views AND ambiguous_or_stance_title",
                    "blanket_capture": False,
                },
                "description_caption_mention_candidates": sorted(
                    {
                        mention
                        for row in selected_pages
                        for mention in row.get(
                            "description_caption_mention_candidates", []
                        )
                    },
                    key=str.casefold,
                ),
                "limitations": [
                    "grid rows are bounded by configured scroll passes and row cap",
                    "selected video pages are bounded per format",
                    "captions are fetched only for trigger-matching selected videos",
                    "counts and engagement are observed values, not platform-complete totals",
                ],
                "non_claims": [
                    "observed counts only",
                    "recurrence evidences reach, not independence or sponsorship",
                    "not cross-format engagement comparison",
                    "not Creator Registry admission",
                ],
            }
        finally:
            context.close()
            browser.close()


def _resolve_channel(
    page: Any,
    *,
    creator_display_name: str,
    profile_url: str | None,
    evidence_video_url: str | None,
    timeout_ms: int,
    settle_seconds: float,
) -> tuple[dict[str, str], dict[str, Any]]:
    if evidence_video_url:
        page.goto(evidence_video_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(int(settle_seconds * 1000))
        _assert_logged_out(page)
        player = page.evaluate("() => window.ytInitialPlayerResponse || null") or {}
        details = player.get("videoDetails") if isinstance(player, Mapping) else {}
        details = details if isinstance(details, Mapping) else {}
        channel_id = str(details.get("channelId") or "").strip()
        observed_display_name = str(details.get("author") or "").strip()
        initial = page.evaluate("() => window.ytInitialData || null")
        owner_renderers = _find_key(initial, "videoOwnerRenderer")
        owner = (
            owner_renderers[0]
            if owner_renderers and isinstance(owner_renderers[0], Mapping)
            else {}
        )
        handles = [
            str(value)[2:]
            for value in _find_key(owner, "canonicalBaseUrl")
            if str(value).startswith("/@") and _HANDLE.fullmatch(str(value)[2:])
        ]
        unique_handles = sorted(set(handles), key=str.casefold)
        if not _CHANNEL_ID.fullmatch(channel_id) or len(unique_handles) != 1:
            raise YoutubeCreatorAssessmentError(
                "evidence video did not expose one canonical channel id and handle"
            )
        handle = unique_handles[0]
        identity = {
            "channel_id": channel_id,
            "handle": handle,
            "display_name": observed_display_name,
            "profile_url": f"https://www.youtube.com/@{handle}",
        }
        page.goto(identity["profile_url"], wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(int(settle_seconds * 1000))
        _assert_logged_out(page)
        served = _channel_identity_from_page(page)
        if served["channel_id"] != channel_id:
            raise YoutubeCreatorAssessmentError(
                "evidence video and served channel identity disagree"
            )
        mismatch = _normalized_name(served["display_name"]) != _normalized_name(
            creator_display_name
        )
        if mismatch:
            raise YoutubeCreatorAssessmentError(
                "evidence video channel display name does not match the requested creator"
            )
        return served, {
            "method": "source_observed_video_channel_identity",
            "requested_display_name": creator_display_name,
            "observed_display_name": served["display_name"],
            "display_name_mismatch": False,
            "evidence_video_url": evidence_video_url,
            "candidate_count": 1,
        }

    if profile_url:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(int(settle_seconds * 1000))
        _assert_logged_out(page)
        candidate = _channel_identity_from_page(page)
        mismatch = _normalized_name(candidate["display_name"]) != _normalized_name(
            creator_display_name
        )
        return candidate, {
            "method": "owner_supplied_profile_url",
            "requested_display_name": creator_display_name,
            "observed_display_name": candidate["display_name"],
            "display_name_mismatch": mismatch,
            "candidate_count": 1,
        }

    search_url = (
        "https://www.youtube.com/results?search_query=" + quote_plus(creator_display_name)
        + "&sp=EgIQAg%253D%253D"
    )
    page.goto(search_url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(int(settle_seconds * 1000))
    _assert_logged_out(page)
    initial = page.evaluate("() => window.ytInitialData || null")
    renderers = _find_key(initial, "channelRenderer")
    candidates: list[dict[str, str]] = []
    for renderer in renderers:
        if not isinstance(renderer, Mapping):
            continue
        title = _runs_text(renderer.get("title"))
        channel_id = str(renderer.get("channelId") or "").strip()
        handle = _channel_handle(renderer)
        if title and _CHANNEL_ID.fullmatch(channel_id) and handle:
            candidates.append(
                {
                    "channel_id": channel_id,
                    "handle": handle,
                    "display_name": title,
                    "profile_url": f"https://www.youtube.com/@{handle}",
                }
            )
    exact = [
        row
        for row in candidates
        if _normalized_name(row["display_name"]) == _normalized_name(creator_display_name)
    ]
    unique = {row["channel_id"]: row for row in exact}
    if len(unique) != 1:
        raise YoutubeCreatorAssessmentError(
            "display-name resolution requires exactly one exact YouTube channel match; "
            f"found {len(unique)} exact among {len(candidates)} channel candidates; "
            f"exact_candidates={list(unique.values())}"
        )
    identity = next(iter(unique.values()))
    page.goto(identity["profile_url"], wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(int(settle_seconds * 1000))
    _assert_logged_out(page)
    observed = _channel_identity_from_page(page)
    if observed["channel_id"] != identity["channel_id"]:
        raise YoutubeCreatorAssessmentError("search result and served channel identity disagree")
    return observed, {
        "method": "youtube_channel_search_exact_display_name",
        "requested_display_name": creator_display_name,
        "observed_display_name": observed["display_name"],
        "display_name_mismatch": False,
        "candidate_count": len(candidates),
        "exact_match_count": 1,
    }


def _channel_identity_from_page(page: Any) -> dict[str, str]:
    initial = page.evaluate("() => window.ytInitialData || null")
    metadata_rows = _find_key(initial, "channelMetadataRenderer")
    metadata = metadata_rows[0] if metadata_rows and isinstance(metadata_rows[0], Mapping) else {}
    channel_id = str(metadata.get("externalId") or "").strip()
    display_name = str(metadata.get("title") or "").strip()
    vanity = str(metadata.get("vanityChannelUrl") or "").strip()
    handle = vanity.rstrip("/").rsplit("/@", 1)[-1] if "/@" in vanity else ""
    if not _CHANNEL_ID.fullmatch(channel_id) or not _HANDLE.fullmatch(handle) or not display_name:
        raise YoutubeCreatorAssessmentError(
            "served channel page did not expose canonical channel_id, handle, and display name"
        )
    return {
        "channel_id": channel_id,
        "handle": handle,
        "display_name": display_name,
        "profile_url": f"https://www.youtube.com/@{handle}",
    }


def _capture_profile(page: Any, profile_url: str, timeout_ms: int, settle_seconds: float) -> dict[str, Any]:
    page.goto(f"{profile_url}/about", wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(int(settle_seconds * 1000))
    _assert_logged_out(page)
    initial = page.evaluate("() => window.ytInitialData || null")
    header_renderers = (
        _find_key(initial, "pageHeaderRenderer")
        + _find_key(initial, "c4TabbedHeaderRenderer")
    )
    subscriber_texts = [
        text
        for renderer in header_renderers
        for value in _find_key(renderer, "subscriberCountText")
        if (text := _runs_text(value))
    ]
    if not subscriber_texts:
        subscriber_texts = [
            text
            for renderer in header_renderers
            if (text := _first_matching_text(renderer, pattern=r"\bsubscribers?\b"))
        ]
    if not subscriber_texts:
        subscriber_texts = [
            str(value).strip()
            for value in page.locator(
                "ytd-page-header-renderer #subscriber-count,"
                "ytd-c4-tabbed-header-renderer #subscriber-count"
            ).all_text_contents()
            if str(value).strip()
        ]
    subscriber_text = subscriber_texts[0] if subscriber_texts else None
    metadata_rows = _find_key(initial, "channelMetadataRenderer")
    metadata = metadata_rows[0] if metadata_rows and isinstance(metadata_rows[0], Mapping) else {}
    description_values = [
        text
        for field in ("description", "descriptionPreview")
        if (text := _runs_text(metadata.get(field)))
    ]
    return {
        "subscriber_count_or_none": _parse_count(subscriber_text),
        "subscriber_count_text_or_none": subscriber_text,
        "description_or_none": max(description_values, key=len) if description_values else None,
        "surface_url": f"{profile_url}/about",
    }


def _capture_grid(
    page: Any,
    *,
    url: str,
    format_name: str,
    timeout_ms: int,
    settle_seconds: float,
    scroll_passes: int,
    max_rows: int,
) -> dict[str, Any]:
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(int(settle_seconds * 1000))
    _assert_logged_out(page)
    for _ in range(max(0, scroll_passes)):
        page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
        page.wait_for_timeout(750)
    initial = page.evaluate("() => window.ytInitialData || null")
    rows_by_id: dict[str, dict[str, Any]] = {}
    for key in ("videoRenderer", "gridVideoRenderer", "reelItemRenderer", "shortsLockupViewModel"):
        for renderer in _find_key(initial, key):
            row = _video_row(renderer, format_name=format_name)
            if row is not None:
                rows_by_id.setdefault(row["video_id"], row)
    for row in _dom_grid_rows(page, format_name=format_name):
        rows_by_id.setdefault(row["video_id"], row)
    rows = list(rows_by_id.values())[:max_rows]
    views = [row["view_count_or_none"] for row in rows if row["view_count_or_none"] is not None]
    median = int(statistics.median(views)) if views else None
    return {
        "format": format_name,
        "surface_url": url,
        "surface_attempted": True,
        "observed_video_count": len(rows),
        "videos": rows,
        "engagement_receipt": {
            "format": format_name,
            "row_count": len(rows),
            "view_count_rows": len(views),
            "median_view_count_or_none": median,
            "metric_scope": "same_format_observed_grid_rows_only",
            "cross_format_average": False,
        },
    }


def _video_row(renderer: Any, *, format_name: str) -> dict[str, Any] | None:
    if not isinstance(renderer, Mapping):
        return None
    video_id = str(renderer.get("videoId") or "").strip()
    if not _VIDEO_ID.fullmatch(video_id):
        on_tap = renderer.get("onTap")
        command = on_tap.get("innertubeCommand") if isinstance(on_tap, Mapping) else {}
        reel = command.get("reelWatchEndpoint") if isinstance(command, Mapping) else {}
        video_id = str(reel.get("videoId") or "").strip() if isinstance(reel, Mapping) else ""
    if not _VIDEO_ID.fullmatch(video_id):
        return None
    title = (
        _runs_text(renderer.get("title"))
        or _runs_text(renderer.get("headline"))
        or _runs_text(renderer.get("overlayMetadata"))
        or str(renderer.get("accessibilityText") or "").strip()
    )
    view_text = (
        _runs_text(renderer.get("viewCountText"))
        or _runs_text(renderer.get("shortViewCountText"))
        or _first_view_text(renderer)
        or _first_accessibility_text(renderer, contains="view")
    )
    return {
        "video_id": video_id,
        "format": format_name,
        "title": title or "unknown",
        "video_url": (
            f"https://www.youtube.com/shorts/{video_id}"
            if format_name == "short"
            else f"https://www.youtube.com/watch?v={video_id}"
        ),
        "view_count_or_none": _parse_view_count(view_text),
        "view_count_text_or_none": view_text,
        "published_time_text_or_none": _runs_text(renderer.get("publishedTimeText")) or None,
    }


def _select_video_rows(grids: Mapping[str, Any], per_format: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for format_name in ("long", "short"):
        rows = list(grids[format_name]["videos"])
        rows.sort(
            key=lambda row: (
                row.get("view_count_or_none") is not None,
                row.get("view_count_or_none") or -1,
            ),
            reverse=True,
        )
        median = grids[format_name]["engagement_receipt"]["median_view_count_or_none"]
        selected.extend([{**row, "same_format_median_view_count_or_none": median} for row in rows[:per_format]])
    return selected


def _dom_grid_rows(page: Any, *, format_name: str) -> list[dict[str, Any]]:
    href_fragment = "/shorts/" if format_name == "short" else "/watch?v="
    rows = page.evaluate(
        """
        ({hrefFragment}) => Array.from(document.querySelectorAll(`a[href*="${hrefFragment}"]`))
          .map((anchor) => {
            const container = anchor.closest(
              "ytd-rich-item-renderer,ytd-grid-video-renderer,ytd-reel-item-renderer,"
              + "ytm-shorts-lockup-view-model,ytd-video-renderer"
            ) || anchor.parentElement;
            return {
              href: anchor.href || anchor.getAttribute("href") || "",
              title: anchor.getAttribute("title") || anchor.textContent || "",
              containerText: container ? container.textContent || "" : "",
            };
          })
        """,
        {"hrefFragment": href_fragment},
    )
    output: list[dict[str, Any]] = []
    for raw in rows if isinstance(rows, list) else []:
        if not isinstance(raw, Mapping):
            continue
        href = str(raw.get("href") or "")
        pattern = r"/shorts/([A-Za-z0-9_-]{11})" if format_name == "short" else r"[?&]v=([A-Za-z0-9_-]{11})"
        match = re.search(pattern, href)
        if not match:
            continue
        video_id = match.group(1)
        container_text = re.sub(r"\s+", " ", str(raw.get("containerText") or "")).strip()
        view_match = re.search(
            r"(\d+(?:[.,]\d+)?\s*[KMB]?)\s+views?\b",
            container_text,
            flags=re.IGNORECASE,
        )
        view_text = view_match.group(0) if view_match else None
        title = re.sub(r"\s+", " ", str(raw.get("title") or "")).strip()
        output.append(
            {
                "video_id": video_id,
                "format": format_name,
                "title": title or "unknown",
                "video_url": (
                    f"https://www.youtube.com/shorts/{video_id}"
                    if format_name == "short"
                    else f"https://www.youtube.com/watch?v={video_id}"
                ),
                "view_count_or_none": _parse_view_count(view_text),
                "view_count_text_or_none": view_text,
                "published_time_text_or_none": None,
            }
        )
    return output


def _capture_selected_video(
    page: Any, row: Mapping[str, Any], *, timeout_ms: int, settle_seconds: float
) -> dict[str, Any]:
    page.goto(str(row["video_url"]), wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(int(settle_seconds * 1000))
    _assert_logged_out(page)
    player = page.evaluate("() => window.ytInitialPlayerResponse || null") or {}
    initial = page.evaluate("() => window.ytInitialData || null") or {}
    details = player.get("videoDetails") if isinstance(player, Mapping) else {}
    details = details if isinstance(details, Mapping) else {}
    title = str(details.get("title") or row.get("title") or "unknown")
    view_count = _parse_count(str(details.get("viewCount") or "")) or row.get("view_count_or_none")
    like_text = _first_accessibility_text(initial, contains="like")
    comment_text = _first_accessibility_text(initial, contains="comment")
    description = str(details.get("shortDescription") or "").strip() or None
    median = row.get("same_format_median_view_count_or_none")
    trigger = bool(
        view_count is not None
        and median is not None
        and view_count >= median
        and (_AMBIGUOUS_TITLE.search(title) or len(title.split()) <= 6)
    )
    caption = _capture_caption(page, player) if trigger else None
    text_for_mentions = "\n".join(
        value
        for value in (
            description,
            caption.get("text") if isinstance(caption, Mapping) else None,
        )
        if value
    )
    return {
        "video_id": row["video_id"],
        "format": row["format"],
        "title": title,
        "video_url": row["video_url"],
        "engagement": {
            "view_count_or_none": view_count,
            "like_count_or_none": _parse_labeled_count(like_text, label="like"),
            "comment_count_or_none": _parse_labeled_count(comment_text, label="comment"),
        },
        "description_or_none": description,
        "transcript_triggered": trigger,
        "transcript_trigger": (
            "same-format at_or_above_median views AND ambiguous_or_stance_title"
            if trigger
            else "not_triggered"
        ),
        "caption": caption,
        "description_caption_mention_candidates": _extract_mentions(
            text_for_mentions
        ),
    }


def _capture_caption(page: Any, player: Mapping[str, Any]) -> dict[str, Any]:
    captions = player.get("captions")
    renderer = captions.get("playerCaptionsTracklistRenderer") if isinstance(captions, Mapping) else {}
    tracks = renderer.get("captionTracks") if isinstance(renderer, Mapping) else []
    if not isinstance(tracks, list) or not tracks:
        return {
            "status": "absent_route_to_asr",
            "text": None,
            "language_code_or_none": None,
        }
    track = next(
        (
            item
            for item in tracks
            if isinstance(item, Mapping) and str(item.get("languageCode")).casefold().startswith("en")
        ),
        tracks[0],
    )
    if not isinstance(track, Mapping) or not track.get("baseUrl"):
        return {"status": "invalid_track", "text": None, "language_code_or_none": None}
    separator = "&" if "?" in str(track["baseUrl"]) else "?"
    response = page.request.get(
        f"{track['baseUrl']}{separator}fmt=json3",
        timeout=30_000,
    )
    if not response.ok:
        return {
            "status": f"fetch_failed_http_{response.status}",
            "text": None,
            "language_code_or_none": track.get("languageCode"),
        }
    raw = response.text()
    text = ""
    try:
        json3 = json.loads(raw)
    except json.JSONDecodeError:
        json3 = None
    if isinstance(json3, Mapping):
        text = " ".join(
            str(segment.get("utf8") or "")
            for event in json3.get("events", [])
            if isinstance(event, Mapping)
            for segment in event.get("segs", [])
            if isinstance(segment, Mapping)
        )
    else:
        text = " ".join(
            html.unescape(re.sub(r"<[^>]+>", " ", match))
            for match in re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.DOTALL)
        )
    return {
        "status": "captured_native_caption" if text.strip() else "empty_native_caption",
        "text": re.sub(r"\s+", " ", text).strip() or None,
        "language_code_or_none": track.get("languageCode"),
    }


def assessment_summary(assessment: Mapping[str, Any]) -> dict[str, Any]:
    grids = assessment["grids"]
    transcripts = [
        row
        for row in assessment["selected_video_pages"]
        if isinstance(row.get("caption"), Mapping)
        and row["caption"].get("status") == "captured_native_caption"
    ]
    return {
        "creator": assessment["identity"]["display_name"],
        "channel_id": assessment["identity"]["channel_id"],
        "handle": assessment["identity"]["handle"],
        "subscriber_count_or_none": assessment["profile"]["subscriber_count_or_none"],
        "long_video_count": grids["long"]["observed_video_count"],
        "long_median_view_count_or_none": grids["long"]["engagement_receipt"][
            "median_view_count_or_none"
        ],
        "short_video_count": grids["short"]["observed_video_count"],
        "short_median_view_count_or_none": grids["short"]["engagement_receipt"][
            "median_view_count_or_none"
        ],
        "description_caption_mention_candidates": assessment[
            "description_caption_mention_candidates"
        ],
        "transcript_count": len(transcripts),
        "transcript_trigger": assessment["transcript_policy"]["trigger"],
    }


def _registry_preflight_source(
    *, data_root_value: str | None, registry_view: Path | None
) -> tuple[dict[str, Any], str, str]:
    if registry_view is not None:
        raw = registry_view.read_bytes()
        return _load_json(registry_view), str(registry_view), hashlib.sha256(raw).hexdigest()
    root = DataLakeRoot.resolve(explicit=data_root_value)
    document = load_current_registry_preflight_view(root)
    raw = canonical_record_bytes(document)
    return document, str(root.path / "creator_registry_current_view"), hashlib.sha256(raw).hexdigest()


def _assert_logged_out(page: Any) -> None:
    state = page.evaluate(
        "() => (window.ytcfg && typeof window.ytcfg.get === 'function') "
        "? window.ytcfg.get('LOGGED_IN') : null"
    )
    if state is not False:
        raise YoutubeCreatorAssessmentError(
            f"required logged-out YouTube posture was not observed (LOGGED_IN={state!r})"
        )


def _find_key(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, Mapping):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            found.extend(_find_key(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(_find_key(item, key))
    return found


def _runs_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, Mapping):
        return ""
    simple = value.get("simpleText")
    if isinstance(simple, str):
        return simple.strip()
    runs = value.get("runs")
    if isinstance(runs, list):
        return "".join(
            str(run.get("text") or "") for run in runs if isinstance(run, Mapping)
        ).strip()
    return ""


def _channel_handle(renderer: Mapping[str, Any]) -> str | None:
    for value in _find_key(renderer, "canonicalBaseUrl"):
        text = str(value)
        if text.startswith("/@") and _HANDLE.fullmatch(text[2:]):
            return text[2:]
    for value in _find_key(renderer, "vanityChannelUrl"):
        text = str(value)
        if "/@" in text:
            handle = text.rstrip("/").rsplit("/@", 1)[-1]
            if _HANDLE.fullmatch(handle):
                return handle
    return None


def _first_accessibility_text(value: Any, *, contains: str) -> str | None:
    for item in _find_key(value, "accessibilityData"):
        if isinstance(item, Mapping):
            label = str(item.get("label") or "").strip()
            if contains.casefold() in label.casefold():
                return label
    for item in _find_key(value, "accessibilityText"):
        label = str(item or "").strip()
        if contains.casefold() in label.casefold():
            return label
    return None


def _first_view_text(value: Any) -> str | None:
    if isinstance(value, str):
        match = re.search(
            r"\d+(?:[.,]\d+)?\s*[KMB]?\s+views?\b",
            value,
            flags=re.IGNORECASE,
        )
        return match.group(0) if match else None
    if isinstance(value, Mapping):
        rendered = _runs_text(value)
        if rendered:
            nested = _first_view_text(rendered)
            if nested:
                return nested
        for nested_value in value.values():
            nested = _first_view_text(nested_value)
            if nested:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _first_view_text(item)
            if nested:
                return nested
    return None


def _first_matching_text(value: Any, *, pattern: str) -> str | None:
    if isinstance(value, str):
        return value.strip() if re.search(pattern, value, flags=re.IGNORECASE) else None
    if isinstance(value, Mapping):
        rendered = _runs_text(value)
        if rendered and re.search(pattern, rendered, flags=re.IGNORECASE):
            return rendered
        for nested_value in value.values():
            nested = _first_matching_text(nested_value, pattern=pattern)
            if nested:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _first_matching_text(item, pattern=pattern)
            if nested:
                return nested
    return None


def _parse_count(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = value.replace(",", "")
    match = _COUNT.search(cleaned)
    if not match:
        return None
    number = float(match.group("number"))
    multiplier = {None: 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[
        (match.group("suffix") or "").upper() or None
    ]
    return int(number * multiplier)


def _parse_view_count(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(
        r"(\d+(?:[.,]\d+)?\s*[KMB]?)\s+views?\b",
        value,
        flags=re.IGNORECASE,
    )
    return _parse_count(match.group(1)) if match else None


def _parse_labeled_count(value: str | None, *, label: str) -> int | None:
    if not value:
        return None
    patterns = [
        rf"(\d+(?:[.,]\d+)?\s*[KMB]?)\s+{re.escape(label)}s?\b",
        r"(?:with|by)\s+(\d+(?:[.,]\d+)?\s*[KMB]?)\s+(?:other\s+)?(?:people|users)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return _parse_count(match.group(1))
    return None


def _extract_mentions(text: str) -> list[str]:
    return sorted(
        {
            match
            for match in re.findall(r"(?<!\w)[@#]([A-Za-z][A-Za-z0-9._-]{2,})", text)
            if match.casefold() not in {"youtube", "shorts"}
        },
        key=str.casefold,
    )


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _stable_token(value: str) -> str:
    return hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()[:16]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")[:60] or "creator"


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
