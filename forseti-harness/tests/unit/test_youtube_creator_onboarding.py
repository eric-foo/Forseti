from __future__ import annotations

import json
from pathlib import Path

import pytest

import runners.run_source_capture_youtube_creator_onboarding as youtube_runner
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
    _capture_grid,
    _capture_selected_video,
    _display_name_matches,
    _normalized_name,
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


def _preflight_registry(display_name: str, *, platform: str = "youtube") -> dict:
    handle = "drtest" if platform == "youtube" else "someone"
    host = "www.youtube.com" if platform == "youtube" else "www.tiktok.com"
    return {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_v0",
            "generated_at_utc": "2026-07-30T00:00:00Z",
            "counts": {"profiles_total": 1},
            "profiles": [
                {
                    "profile_subject_kind": "platform_account",
                    "profile_subject_id": f"acct_{platform}_existing",
                    "platform_accounts": [
                        {
                            "platform_account_id": f"acct_{platform}_existing",
                            "platform": platform,
                            "public_handle": handle,
                            "public_profile_url": f"https://{host}/@{handle}",
                            "platform_public_account_id_or_none": "UC" + "A" * 22,
                            "public_display_name_or_none": display_name,
                        }
                    ],
                }
            ],
        }
    }


def _preflight(registry: dict, candidate: dict) -> dict:
    receipt = build_creator_registry_match_preflight_receipt(
        candidates=[candidate],
        registry_document=registry,
        registry_source_pointer="fixture",
        registry_sha256="0" * 64,
        generated_at_utc="2026-07-30T01:00:00Z",
    )
    return receipt[RECEIPT_WRAPPER_KEY]["results"][0]


def test_display_name_preflight_is_normalized_not_literal_and_platform_scoped() -> None:
    """Display-name matching ignores case/spacing/punctuation, so the emitted
    receipt must not claim literal-exactness, and a different name must not match."""
    candidate = {
        "candidate_id": "candidate",
        "platform": "youtube",
        "display_name_or_none": "Dr Test",
        "intended_action": "new_capture",
    }
    matched = _preflight(_preflight_registry("Dr. Test"), candidate)
    assert matched["decision"] == "existing_match"
    assert matched["can_start_new_capture"] is False
    assert matched["matched_registry_profiles"][0]["match_reasons"] == [
        "same_platform_normalized_display_name"
    ]

    unmatched = _preflight(_preflight_registry("Dr Testing"), candidate)
    assert unmatched["decision"] == "new_candidate"
    assert unmatched["can_start_new_capture"] is True

    other_platform = _preflight(
        _preflight_registry("Dr. Test", platform="tiktok"), candidate
    )
    assert other_platform["decision"] == "new_candidate"


def test_preflight_survives_non_latin_registry_display_names() -> None:
    """One CJK/Cyrillic/emoji registry display name must not break the shared
    discovery->capture turnstile for every candidate on every platform."""
    candidate = {
        "candidate_id": "tiktok-someone-else",
        "platform": "tiktok",
        "public_handle_or_none": "someoneelse",
        "intended_action": "new_capture",
    }
    for display_name in ("皮膚科医", "Дарья", "✨", "José"):
        result = _preflight(
            _preflight_registry(display_name, platform="tiktok"), candidate
        )
        assert result["decision"] == "new_candidate", display_name
        assert result["can_start_new_capture"] is True, display_name

    # A non-Latin name still carries a real display-name signal when it matches.
    matched = _preflight(
        _preflight_registry("皮膚科医", platform="tiktok"),
        {
            "candidate_id": "tiktok-cjk",
            "platform": "tiktok",
            "display_name_or_none": "皮膚科医",
            "intended_action": "new_capture",
        },
    )
    assert matched["decision"] == "existing_match"


def test_display_name_identity_match_fails_closed_without_a_comparable_form() -> None:
    """Two unrelated non-Latin names both normalize to '', so bare normalized
    equality would report an identity match between different creators."""
    assert _normalized_name("✨") == _normalized_name("🌟") == ""
    assert _display_name_matches("✨", "🌟") is False
    assert _display_name_matches("皮膚科医", "Dr Dray") is False
    assert _display_name_matches("皮膚科医", "皮膚科医") is True
    assert _display_name_matches("Дарья", "дарья") is True
    assert _display_name_matches("Дарья", "Мария") is False
    assert _display_name_matches("Dr. Dray", "dr dray") is True


def test_display_name_only_match_cannot_authorize_update_existing() -> None:
    registry = _preflight_registry("Dr. Test")
    display_only = _preflight(
        registry,
        {
            "candidate_id": "display-only-update",
            "platform": "youtube",
            "display_name_or_none": "Dr Test",
            "intended_action": "update_existing",
        },
    )
    assert display_only["decision"] == "existing_match"
    assert display_only["action_status"] == "blocked"
    assert display_only["action_blockers"] == [
        "display_name_only_match_insufficient_for_update"
    ]

    handle_bound = _preflight(
        registry,
        {
            "candidate_id": "handle-bound-update",
            "platform": "youtube",
            "display_name_or_none": "Dr Test",
            "public_handle_or_none": "drtest",
            "intended_action": "update_existing",
        },
    )
    assert handle_bound["decision"] == "existing_match"
    assert handle_bound["action_status"] == "allowed"
    assert "same_platform_public_handle" in handle_bound[
        "matched_registry_profiles"
    ][0]["match_reasons"]


def test_resolved_identity_preflight_blocks_renamed_existing_channel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = _preflight_registry("Old Channel Name")
    assessment = _assessment()
    assessment["identity"]["display_name"] = "New Channel Name"
    assessment["identity_resolution"]["requested_display_name"] = "New Channel Name"
    assessment["identity_resolution"]["observed_display_name"] = "New Channel Name"
    packet_write_called = False

    monkeypatch.setattr(
        youtube_runner,
        "_registry_preflight_source",
        lambda **_kwargs: (registry, "fixture", "0" * 64),
    )
    monkeypatch.setattr(
        youtube_runner,
        "capture_youtube_creator_assessment",
        lambda **_kwargs: assessment,
    )

    def _unexpected_packet_write(**_kwargs: object) -> tuple[int, str]:
        nonlocal packet_write_called
        packet_write_called = True
        return 0, "unexpected"

    monkeypatch.setattr(
        youtube_runner,
        "write_youtube_creator_assessment_packet",
        _unexpected_packet_write,
    )

    exit_code = youtube_runner.main(
        [
            "--creator-display-name",
            "New Channel Name",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 3
    assert packet_write_called is False
    assert not (tmp_path / "assessment.json").exists()
    resolved_receipt = json.loads(
        (tmp_path / youtube_runner.RESOLVED_REGISTRY_PREFLIGHT_JSON_NAME).read_text(
            encoding="utf-8"
        )
    )
    resolved_result = resolved_receipt[RECEIPT_WRAPPER_KEY]["results"][0]
    assert resolved_result["decision"] == "existing_match"
    assert "same_platform_public_handle" in resolved_result[
        "matched_registry_profiles"
    ][0]["match_reasons"]
    assert "resolved-identity preflight blocked packet write" in capsys.readouterr().err


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


def test_frontier_export_fails_closed_on_colliding_recurring_display_names() -> None:
    """counts.recurring_feed is quoted as 'all N rows' in durable consumer docs;
    a colliding normalized key must surface, not silently truncate the count."""
    feed = {
        "creators": [
            {"platform": "youtube", "display_name": "Dr. Dray", "subjects": ["a", "b"]},
            {"platform": "youtube", "display_name": "Dr Dray", "subjects": ["c", "d"]},
        ]
    }
    try:
        build_youtube_frontier_candidates(recurring_feed=feed, suffix_extract_dir=None)
    except ValueError as exc:
        assert "normalized display name" in str(exc)
    else:
        raise AssertionError("colliding recurring display names must fail closed")


class _FakeGridPage:
    """Minimal page double: only the calls _capture_grid actually makes."""

    def __init__(self, initial_data: dict) -> None:
        self._initial_data = initial_data

    def goto(self, url: str, **kwargs: object) -> None:
        return None

    def wait_for_timeout(self, milliseconds: int) -> None:
        return None

    def evaluate(self, script: str, arg: object = None) -> object:
        if "LOGGED_IN" in script:
            return False
        if "ytInitialData" in script:
            return self._initial_data
        if "querySelectorAll" in script:
            return []
        return None


def test_grid_capture_excludes_cross_format_renderers() -> None:
    """A Shorts shelf served inside the /videos surface must not enter the
    long-form grid: doing so labels a Short format='long' and contaminates the
    same-format median the Shorts/long-form axis exists to keep separate."""
    initial = {
        "contents": [
            {
                "gridVideoRenderer": {
                    "videoId": "longvideo01",
                    "title": {"simpleText": "Retinoid routine explained"},
                    "viewCountText": {"simpleText": "10K views"},
                }
            },
            {
                "reelItemRenderer": {
                    "videoId": "shortvideo1",
                    "headline": {"simpleText": "60 second tip"},
                    "viewCountText": {"simpleText": "900K views"},
                }
            },
        ]
    }
    long_grid = _capture_grid(
        _FakeGridPage(initial),
        url="https://www.youtube.com/@drtest/videos",
        format_name="long",
        timeout_ms=1000,
        settle_seconds=0.0,
        scroll_passes=0,
        max_rows=30,
    )
    assert [row["video_id"] for row in long_grid["videos"]] == ["longvideo01"]
    assert long_grid["observed_video_count"] == 1
    assert long_grid["engagement_receipt"]["median_view_count_or_none"] == 10_000

    short_grid = _capture_grid(
        _FakeGridPage(initial),
        url="https://www.youtube.com/@drtest/shorts",
        format_name="short",
        timeout_ms=1000,
        settle_seconds=0.0,
        scroll_passes=0,
        max_rows=30,
    )
    assert [row["video_id"] for row in short_grid["videos"]] == ["shortvideo1"]
    assert short_grid["engagement_receipt"]["median_view_count_or_none"] == 900_000


class _FakeSelectedVideoPage:
    def goto(self, url: str, **kwargs: object) -> None:
        return None

    def wait_for_timeout(self, milliseconds: int) -> None:
        return None

    def evaluate(self, script: str) -> object:
        if "LOGGED_IN" in script:
            return False
        if "ytInitialPlayerResponse" in script:
            return {
                "videoDetails": {
                    "title": "A deliberately long explanatory title",
                    "viewCount": "0",
                    "shortDescription": "",
                }
            }
        if "ytInitialData" in script:
            return {}
        return None


def test_selected_video_preserves_zero_view_count() -> None:
    captured = _capture_selected_video(
        _FakeSelectedVideoPage(),
        {
            "video_id": "abcdefghijk",
            "format": "long",
            "title": "A deliberately long explanatory title",
            "video_url": "https://www.youtube.com/watch?v=abcdefghijk",
            "view_count_or_none": 999,
            "same_format_median_view_count_or_none": 100,
        },
        timeout_ms=1000,
        settle_seconds=0.0,
    )
    assert captured["engagement"]["view_count_or_none"] == 0


def test_assessment_writer_requires_canonical_profile_url(tmp_path: Path) -> None:
    assessment = _assessment()
    assessment["identity"]["profile_url"] = "https://youtube.com/@drtest/"
    with pytest.raises(
        ValueError,
        match="identity.profile_url must bind the observed handle",
    ):
        write_youtube_creator_assessment_packet(
            assessment_json=canonical_record_bytes(assessment),
            output_directory=tmp_path,
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
