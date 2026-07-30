"""Validate and preserve one logged-out YouTube creator assessment packet."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from source_capture.models import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map

SOURCE_SURFACE = "youtube_creator_assessment"
ASSESSMENT_JSON_NAME = "youtube_creator_assessment.json"
ASSESSMENT_SCHEMA_VERSION = "youtube_creator_assessment_v0"
CAPTURE_POLICY_VERSION = "youtube_creator_assessment_logged_out_dual_grid_v0"
YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS = (
    "observed counts only",
    "recurrence evidences reach, not independence or sponsorship",
    "not cross-format engagement comparison",
    "not a complete channel archive",
    "not blanket transcript capture",
    "not Creator Registry admission",
    "not audience Judgment",
    "not contact or outreach authorization",
)


def write_youtube_creator_assessment_packet(
    *,
    assessment_json: bytes,
    output_directory: Path | None = None,
    data_root: Any = None,
    decision_question: str = (
        "Does this public YouTube channel warrant owner-reviewed Creator Registry admission?"
    ),
) -> tuple[int, str]:
    """Write one validated assessment as a SourceCapturePacket."""
    assessment = _load_assessment(assessment_json)
    observed_at = _required_utc(assessment.get("captured_at_utc"), "captured_at_utc")
    identity = _mapping(assessment.get("identity"), "identity")
    channel_id = _required_text(identity.get("channel_id"), "identity.channel_id")
    if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        raise ValueError("YouTube assessment identity.channel_id is not canonical")
    handle = _required_text(identity.get("handle"), "identity.handle").lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", handle):
        raise ValueError("YouTube assessment identity.handle is not canonical")
    display_name = _required_text(identity.get("display_name"), "identity.display_name")
    profile_url = _required_text(identity.get("profile_url"), "identity.profile_url")
    parsed = urlparse(profile_url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() not in {"youtube.com", "www.youtube.com"}
        or parsed.path.rstrip("/").casefold() != f"/@{handle}".casefold()
    ):
        raise ValueError("YouTube assessment identity.profile_url must bind the observed handle")

    posture = _mapping(assessment.get("session_posture"), "session_posture")
    if (
        posture.get("required") != "logged_out_fresh_browser_context"
        or posture.get("observed_logged_in") is not False
        or posture.get("context_reused") is not False
    ):
        raise ValueError("YouTube assessment did not prove the required logged-out fresh context")

    grids = _mapping(assessment.get("grids"), "grids")
    expected_formats = {"long", "short"}
    if set(grids) != expected_formats:
        raise ValueError("YouTube assessment grids must contain exactly long and short")
    all_video_ids: set[str] = set()
    for format_name in sorted(expected_formats):
        grid = _mapping(grids[format_name], f"grids.{format_name}")
        rows = grid.get("videos")
        if not isinstance(rows, list):
            raise ValueError(f"YouTube assessment grids.{format_name}.videos must be a list")
        if grid.get("surface_attempted") is not True:
            raise ValueError(f"YouTube assessment {format_name} grid was not attempted")
        if grid.get("observed_video_count") != len(rows):
            raise ValueError(
                f"YouTube assessment grids.{format_name}.observed_video_count mismatches rows"
            )
        receipt = _mapping(grid.get("engagement_receipt"), f"grids.{format_name}.engagement_receipt")
        if receipt.get("format") != format_name or receipt.get("row_count") != len(rows):
            raise ValueError(f"YouTube assessment {format_name} engagement receipt is unbound")
        for index, raw_row in enumerate(rows):
            row = _mapping(raw_row, f"grids.{format_name}.videos[{index}]")
            if row.get("format") != format_name:
                raise ValueError("YouTube assessment video row format conflicts with its grid")
            video_id = _required_text(row.get("video_id"), "video_id")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                raise ValueError("YouTube assessment video_id is not canonical")
            if video_id in all_video_ids:
                raise ValueError("YouTube assessment contains a duplicate video_id")
            all_video_ids.add(video_id)
            view_count = row.get("view_count_or_none")
            if view_count is not None and (type(view_count) is not int or view_count < 0):
                raise ValueError("YouTube assessment view count must be a non-negative integer")

    forbidden_combined = {
        "combined_engagement",
        "combined_median_engagement",
        "all_format_average",
        "cross_format_average",
    }
    if forbidden_combined.intersection(assessment):
        raise ValueError("YouTube assessment must not collapse Shorts and long-form engagement")

    selected = assessment.get("selected_video_pages")
    if not isinstance(selected, list):
        raise ValueError("YouTube assessment selected_video_pages must be a list")
    for index, raw in enumerate(selected):
        row = _mapping(raw, f"selected_video_pages[{index}]")
        if row.get("format") not in expected_formats:
            raise ValueError("selected video page requires format=short|long")
        if row.get("engagement") is not None:
            engagement = _mapping(row["engagement"], "selected video engagement")
            for name in ("view_count_or_none", "like_count_or_none", "comment_count_or_none"):
                value = engagement.get(name)
                if value is not None and (type(value) is not int or value < 0):
                    raise ValueError(f"selected video {name} must be a non-negative integer")

    staged = [(ASSESSMENT_JSON_NAME, assessment_json)]
    file_id = staged_file_id_map(staged)[ASSESSMENT_JSON_NAME]
    timing = PacketTiming(
        source_publication_or_event=not_applicable(
            "a channel assessment is capture-time state, not one publication event"
        ),
        source_edit_or_version=not_applicable(
            "YouTube channel surfaces expose no source edit/version identifier"
        ),
        capture_time=known_fact(observed_at),
        recapture_time=not_applicable("no prior YouTube creator assessment was supplied"),
        cutoff_posture=not_applicable("cutoff posture does not apply to current channel assessment"),
    )
    access = known_fact(
        "public YouTube surfaces in one fresh logged-out browser context; no stored session"
    )
    archive = not_attempted("YouTube creator assessment does not query archive/history services")
    media = not_attempted("assessment preserves selected metadata and captions, not media bytes")
    slices = [
        SourceCaptureSlice(
            slice_id="youtube_creator_profile_01",
            locator=known_fact(profile_url),
            timing=timing,
            access_posture=access,
            archive_history_posture=archive,
            media_modality_posture=media,
            re_capture_relationship=not_applicable("first supplied assessment"),
            limitations=list(YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS),
            warning_notes=[],
            preserved_file_ids=[file_id],
        ),
        SourceCaptureSlice(
            slice_id="youtube_creator_uploads_grid_01",
            locator=known_fact(f"{profile_url}/videos"),
            timing=timing,
            access_posture=access,
            archive_history_posture=archive,
            media_modality_posture=media,
            re_capture_relationship=not_applicable("first supplied assessment"),
            limitations=list(YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS),
            warning_notes=[],
            preserved_file_ids=[file_id],
        ),
        SourceCaptureSlice(
            slice_id="youtube_creator_shorts_grid_01",
            locator=known_fact(f"{profile_url}/shorts"),
            timing=timing,
            access_posture=access,
            archive_history_posture=archive,
            media_modality_posture=media,
            re_capture_relationship=not_applicable("first supplied assessment"),
            limitations=list(YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS),
            warning_notes=[],
            preserved_file_ids=[file_id],
        ),
    ]
    result = stage_and_write_packet(
        output_directory=output_directory,
        data_root=data_root,
        staged_artifacts=staged,
        source_slices=slices,
        source_family="youtube",
        source_surface=SOURCE_SURFACE,
        source_locator=known_fact(profile_url),
        decision_question=decision_question,
        capture_context=(
            "YouTube creator assessment from profile/about, uploads, Shorts, and selected "
            "video/caption observables in one fresh logged-out browser context"
        ),
        actor_audience_context=not_applicable(
            "public creator/content object metrics only; no audience or person modeling"
        ),
        capture_mode=CaptureModeCategory.AUTOMATED_EXTRACTION,
        operator_category="youtube_creator_assessment_cli_operator",
        session_identity=None,
        visible_mode_changes=[
            CAPTURE_POLICY_VERSION,
            "format_axis=short|long;cross_format_average=forbidden",
            f"channel_id={channel_id}",
        ],
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access,
        archive_history_posture=archive,
        media_modality_posture=media,
        re_capture_relationship=not_applicable("first supplied assessment"),
        warnings=[],
        limitations=list(YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS),
        receipt_summary=(
            f"YouTube creator assessment for @{handle} ({display_name}); "
            f"long={grids['long']['observed_video_count']}, "
            f"short={grids['short']['observed_video_count']}."
        ),
        receipt_non_claims=list(YOUTUBE_CREATOR_ASSESSMENT_NON_CLAIMS),
    )
    return 0, result.output_directory


def _load_assessment(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"YouTube creator assessment is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != ASSESSMENT_SCHEMA_VERSION:
        raise ValueError("unsupported YouTube creator assessment schema")
    return value


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"YouTube assessment {field} must be an object")
    return value


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"YouTube assessment {field} is missing or blank")
    return value.strip()


def _required_utc(value: object, field: str) -> str:
    text = _required_text(value, field)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"YouTube assessment {field} must be UTC")
    return parsed.isoformat().replace("+00:00", "Z")
