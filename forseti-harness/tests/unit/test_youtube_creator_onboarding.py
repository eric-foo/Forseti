from __future__ import annotations

import json
from pathlib import Path

from capture_spine.creator_profile_current.registry_match_preflight import (
    RECEIPT_WRAPPER_KEY,
    build_creator_registry_match_preflight_receipt,
)
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    write_creator_frontier_dispositions,
)
from data_lake.canonical_json import canonical_record_bytes
from data_lake.creator_registry import (
    admit_youtube_creator_account,
    admit_youtube_creator_candidate,
    deterministic_platform_account_id,
    load_current_creator_profiles,
    load_current_creator_registry,
    migrate_legacy_registry,
)
from data_lake.root import DataLakeRoot
from runners.run_source_capture_youtube_creator_onboarding import (
    _parse_count,
    _parse_labeled_count,
    _parse_view_count,
    assessment_summary,
    build_youtube_frontier_candidates,
)
from source_capture.youtube_creator_assessment import (
    write_youtube_creator_assessment_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
LEGACY_ROOT = (
    REPO_ROOT
    / "forseti"
    / "product"
    / "spines"
    / "capture"
    / "core"
    / "source_families"
    / "social_media"
    / "creator_registry"
)


def _root(tmp_path: Path) -> DataLakeRoot:
    return DataLakeRoot.for_test(tmp_path / "forseti-data")


def _migrate(root: DataLakeRoot) -> None:
    migrate_legacy_registry(
        data_root=root,
        account_ledger_path=LEGACY_ROOT / "creator_public_handle_linkage_ledger_v0.json",
        registry_index_path=LEGACY_ROOT / "creator_registry_index_v0.json",
        profile_current_path=LEGACY_ROOT / "creator_profile_current_view_v0.json",
        dry_run=False,
    )


def _assessment() -> dict:
    return {
        "schema_version": "youtube_creator_assessment_v0",
        "captured_at_utc": "2026-07-30T12:00:00Z",
        "identity": {
            "channel_id": "UC" + "A" * 22,
            "handle": "drtest",
            "display_name": "Dr Test",
            "profile_url": "https://www.youtube.com/@drtest",
        },
        "identity_resolution": {
            "method": "youtube_channel_search_exact_display_name",
            "requested_display_name": "Dr Test",
            "observed_display_name": "Dr Test",
            "display_name_mismatch": False,
            "candidate_count": 1,
        },
        "session_posture": {
            "required": "logged_out_fresh_browser_context",
            "observed_logged_in": False,
            "context_reused": False,
            "stored_session_loaded": False,
        },
        "profile": {
            "subscriber_count_or_none": 100_000,
            "subscriber_count_text_or_none": "100K subscribers",
            "description_or_none": "Test channel",
            "surface_url": "https://www.youtube.com/@drtest/about",
        },
        "grids": {
            "long": {
                "format": "long",
                "surface_url": "https://www.youtube.com/@drtest/videos",
                "surface_attempted": True,
                "observed_video_count": 1,
                "videos": [
                    {
                        "video_id": "abcdefghijk",
                        "format": "long",
                        "title": "Is this worth it?",
                        "video_url": "https://www.youtube.com/watch?v=abcdefghijk",
                        "view_count_or_none": 10_000,
                        "view_count_text_or_none": "10K views",
                        "published_time_text_or_none": "1 day ago",
                    }
                ],
                "engagement_receipt": {
                    "format": "long",
                    "row_count": 1,
                    "view_count_rows": 1,
                    "median_view_count_or_none": 10_000,
                    "metric_scope": "same_format_observed_grid_rows_only",
                    "cross_format_average": False,
                },
            },
            "short": {
                "format": "short",
                "surface_url": "https://www.youtube.com/@drtest/shorts",
                "surface_attempted": True,
                "observed_video_count": 1,
                "videos": [
                    {
                        "video_id": "lmnopqrstuv",
                        "format": "short",
                        "title": "Quick test",
                        "video_url": "https://www.youtube.com/shorts/lmnopqrstuv",
                        "view_count_or_none": 100_000,
                        "view_count_text_or_none": "100K views",
                        "published_time_text_or_none": "2 days ago",
                    }
                ],
                "engagement_receipt": {
                    "format": "short",
                    "row_count": 1,
                    "view_count_rows": 1,
                    "median_view_count_or_none": 100_000,
                    "metric_scope": "same_format_observed_grid_rows_only",
                    "cross_format_average": False,
                },
            },
        },
        "selected_video_pages": [
            {
                "video_id": "abcdefghijk",
                "format": "long",
                "title": "Is this worth it?",
                "video_url": "https://www.youtube.com/watch?v=abcdefghijk",
                "engagement": {
                    "view_count_or_none": 10_000,
                    "like_count_or_none": 500,
                    "comment_count_or_none": 25,
                },
                "description_or_none": "@Goodal test",
                "transcript_triggered": True,
                "transcript_trigger": (
                    "same-format at_or_above_median views AND ambiguous_or_stance_title"
                ),
                "caption": {
                    "status": "captured_native_caption",
                    "text": "Test caption",
                    "language_code_or_none": "en",
                },
                "description_caption_mention_candidates": ["Goodal"],
            }
        ],
        "transcript_policy": {
            "captions_first": True,
            "asr_fallback": "route caption-absent triggered videos to run_asr_transcript_catchup",
            "trigger": "same-format at_or_above_median views AND ambiguous_or_stance_title",
            "blanket_capture": False,
        },
        "description_caption_mention_candidates": ["Goodal"],
        "limitations": ["bounded fixture"],
        "non_claims": ["observed counts only"],
    }


def test_count_parser_and_summary_keep_formats_separate() -> None:
    assert _parse_count("1.2M views") == 1_200_000
    assert _parse_count("45,678 views") == 45_678
    assert _parse_view_count("27 seconds") is None
    assert _parse_view_count("1.2M views") == 1_200_000
    assert _parse_labeled_count("like this video along with 4,555 other people", label="like") == 4555
    summary = assessment_summary(_assessment())
    assert summary["long_median_view_count_or_none"] == 10_000
    assert summary["short_median_view_count_or_none"] == 100_000
    assert "median_view_count" not in summary


def test_display_name_preflight_is_exact_and_platform_scoped() -> None:
    registry = {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_v0",
            "generated_at_utc": "2026-07-30T00:00:00Z",
            "counts": {"profiles_total": 1},
            "profiles": [
                {
                    "profile_subject_kind": "platform_account",
                    "profile_subject_id": "acct_youtube_existing",
                    "platform_accounts": [
                        {
                            "platform_account_id": "acct_youtube_existing",
                            "platform": "youtube",
                            "public_handle": "drtest",
                            "public_profile_url": "https://www.youtube.com/@drtest",
                            "platform_public_account_id_or_none": "UC" + "A" * 22,
                            "public_display_name_or_none": "Dr. Test",
                        }
                    ],
                }
            ],
        }
    }
    receipt = build_creator_registry_match_preflight_receipt(
        candidates=[
            {
                "candidate_id": "candidate",
                "platform": "youtube",
                "display_name_or_none": "Dr Test",
                "intended_action": "new_capture",
            }
        ],
        registry_document=registry,
        registry_source_pointer="fixture",
        registry_sha256="0" * 64,
        generated_at_utc="2026-07-30T01:00:00Z",
    )
    result = receipt[RECEIPT_WRAPPER_KEY]["results"][0]
    assert result["decision"] == "existing_match"
    assert result["can_start_new_capture"] is False
    assert result["matched_registry_profiles"][0]["match_reasons"] == [
        "same_platform_exact_display_name"
    ]


def test_frontier_export_preserves_display_name_only_boundary(tmp_path: Path) -> None:
    recurring_feed = {
        "creators": [
            {
                "platform": "youtube",
                "display_name": "Dr Dray",
                "profile_url_or_none": None,
                "subjects": ["a", "b"],
                "scope": "bridging",
            }
        ]
    }
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "j0001.json").write_text(
        json.dumps(
            {
                "requested_query": "test serum youtube",
                "rows": [
                    {
                        "platform": "youtube",
                        "account_or_creator": "New Channel",
                        "canonical_url": "https://www.youtube.com/watch?v=abcdefghijk",
                    },
                    {
                        "platform": "youtube",
                        "account_or_creator": "Dr Dray",
                        "canonical_url": "https://www.youtube.com/watch?v=lmnopqrstuv",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    document = build_youtube_frontier_candidates(
        recurring_feed=recurring_feed, suffix_extract_dir=extracted
    )
    wrapper = document["youtube_creator_frontier_candidates"]
    assert wrapper["counts"] == {"recurring_feed": 1, "suffix_feed_absent": 1, "total": 2}
    assert all(
        row["identity_state"] == "display_name_only_requires_assessment_resolution"
        for row in wrapper["candidates"]
    )


def test_youtube_candidate_and_validated_admission_end_to_end(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _migrate(root)
    exit_code, output = write_youtube_creator_assessment_packet(
        assessment_json=canonical_record_bytes(_assessment()),
        data_root=root,
    )
    assert exit_code == 0
    packet_id = Path(output).name
    disposition_write = write_creator_frontier_dispositions(
        data_root=root,
        actions=[
            {
                "platform": "youtube",
                "handle": "drtest",
                "status": "eligible",
                "priority": "high",
                "reason_code": "owner_choice",
            }
        ],
        recorded_at="2026-07-30T12:01:00Z",
    )
    disposition = disposition_write["current"]["creator_frontier_disposition_current"][
        "dispositions"
    ][0]
    candidate = admit_youtube_creator_candidate(
        data_root=root,
        packet_id=packet_id,
        frontier_disposition_id=disposition["disposition_id"],
    )
    account_id = deterministic_platform_account_id("youtube", "UC" + "A" * 22)
    assert candidate["platform_account_id"] == account_id
    candidate_row = next(
        row
        for row in load_current_creator_registry(root)["creator_registry_index"][
            "platform_accounts"
        ]
        if row["platform_account_id"] == account_id
    )
    assert candidate_row["onboarding"]["onboarding_state"] == "not_onboarded"

    snapshot = {
        "schema_version": "creator_audience_triangulation_snapshot_v1",
        "snapshot_id": "cats_youtube_drtest",
        "profile_subject_kind": "platform_account",
        "profile_subject_id": account_id,
        "platform_account_id": account_id,
        "creator_id": "youtube:@drtest",
        "platform_scope": "youtube",
        "generated_at": "2026-07-30T12:05:00Z",
        "evidence_cutoff": "2026-07-30T12:00:00Z",
        "input_bundle_id": "caeb_youtube_drtest",
        "input_bundle_hash": "sha256:" + "1" * 64,
        "judgment_claim_set": {
            "claims": [],
            "agreements": [],
            "contradictions": [],
            "missing_evidence": [],
        },
        "creator_signal_projection": {},
        "actual_audience_demographics": "not_estimated",
        "limitations": ["synthetic test evidence"],
        "non_claims": ["not campaign performance"],
    }
    outcome = {
        "schema_version": "creator_audience_judgment_outcome_v1",
        "record_id": "cajo_youtube_drtest",
        "raw_anchor": packet_id,
        "status": "validated",
        "creator_id": "youtube:@drtest",
        "profile_subject_id": account_id,
        "bundle_id": snapshot["input_bundle_id"],
        "bundle_hash": snapshot["input_bundle_hash"],
        "snapshot_id_or_none": snapshot["snapshot_id"],
        "snapshot_or_none": snapshot,
    }
    outcome_path = root.append_record(
        subtree="derived",
        raw_anchor=packet_id,
        lane="creator_audience_judgment_outcome",
        record_id=outcome["record_id"],
        data=canonical_record_bytes(outcome),
    )
    admitted = admit_youtube_creator_account(
        data_root=root,
        packet_id=packet_id,
        judgment_outcome_path=outcome_path,
    )
    assert admitted["platform_account_id"] == account_id
    profile = next(
        row
        for row in load_current_creator_profiles(root)["creator_profile_public"]["profiles"]
        if row["profile_subject_id"] == account_id
    )
    assert profile["platform_accounts"][0]["platform"] == "youtube"
    assert profile["audience_triangulation"]["snapshot_id"] == "cats_youtube_drtest"
