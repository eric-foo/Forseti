from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_lake.canonical_json import canonical_record_bytes
from data_lake.creator_registry import deterministic_platform_account_id
from data_lake.root import DataLakeRoot
from judgment.creator_audience import build_capability_manifest
from runners.run_tiktok_creator_audience_triangulation import (
    submit_subscription_judgment,
)
from runners.run_youtube_creator_audience_triangulation import (
    _packet_map,
    prepare_youtube_subscription_judgment,
)
from runners.run_creator_registry_lake import main as registry_main
from source_capture.transcript import CaptionFetch, write_caption_packet
from source_capture.youtube_creator_assessment import (
    write_youtube_creator_assessment_packet,
)
from source_capture.youtube_watch_packet import (
    YoutubeWatchCommentPage,
    YoutubeWatchFetch,
    write_youtube_watch_packet,
)


_CHANNEL_ID = "UC" + "A" * 22
_VIDEO_ID = "abcdefghijk"


def _assessment() -> dict:
    grid_row = {
        "video_id": _VIDEO_ID,
        "format": "long",
        "title": "Is this worth it?",
        "video_url": f"https://www.youtube.com/watch?v={_VIDEO_ID}",
        "view_count_or_none": 10_000,
        "view_count_text_or_none": "10K views",
        "published_time_text_or_none": "1 day ago",
    }
    return {
        "schema_version": "youtube_creator_assessment_v0",
        "captured_at_utc": "2026-07-30T12:00:00Z",
        "identity": {
            "channel_id": _CHANNEL_ID,
            "handle": "drtest",
            "display_name": "Dr Test",
            "profile_url": "https://www.youtube.com/@drtest",
        },
        "session_posture": {
            "required": "logged_out_fresh_browser_context",
            "observed_logged_in": False,
            "context_reused": False,
            "stored_session_loaded": False,
        },
        "grids": {
            "long": {
                "format": "long",
                "surface_url": "https://www.youtube.com/@drtest/videos",
                "surface_attempted": True,
                "observed_video_count": 1,
                "videos": [grid_row],
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
                "observed_video_count": 0,
                "videos": [],
                "engagement_receipt": {
                    "format": "short",
                    "row_count": 0,
                    "view_count_rows": 0,
                    "median_view_count_or_none": None,
                    "metric_scope": "same_format_observed_grid_rows_only",
                    "cross_format_average": False,
                },
            },
        },
        "selected_video_pages": [
            {
                **grid_row,
                "engagement": {
                    "view_count_or_none": 10_000,
                    "like_count_or_none": 500,
                    "comment_count_or_none": 25,
                },
                "description_or_none": "Test description",
                "transcript_triggered": True,
                "transcript_trigger": "fixture trigger",
                "caption": None,
            }
        ],
    }


def _metric(value: int, source_path: str) -> dict:
    return {
        "posture": "observed",
        "value": value,
        "source_route": source_path.rsplit(".", 1)[0],
        "source_path": source_path,
        "artifact": "youtube_watch_capture.json",
    }


def _watch_fetch(*, channel_id: str = _CHANNEL_ID, comments: bool = True) -> YoutubeWatchFetch:
    comment_rows = (
        [
            {
                "comment_id": "comment-1",
                "author": "Viewer",
                "text": "The comparison made the trade-off clear.",
                "published_time": "1 day ago",
                "like_count": 3,
                "reply_count": 0,
                "source_page_number": 1,
                "source_order_in_page": 1,
                "source_order_global": 1,
            }
        ]
        if comments
        else []
    )
    packet = {
        "video_id": _VIDEO_ID,
        "watch_url": f"https://www.youtube.com/watch?v={_VIDEO_ID}",
        "canonical_url": f"https://www.youtube.com/watch?v={_VIDEO_ID}",
        "channel": {"channel_id": channel_id, "author": "Dr Test"},
        "metadata": {
            "title": "Is this worth it?",
            "length_seconds": 42,
            "publish_date": "2026-07-29",
        },
        "engagement": {
            "view_count": 10_000,
            "like_count": 500,
            "comment_sample_count": len(comment_rows),
            "total_comment_count": 25,
        },
        "availability": {
            "video_state": "playable",
            "comments_state": (
                "comments_sample_captured" if comments else "comments_not_exposed"
            ),
        },
        "metric_receipts": {
            "view_count": _metric(
                10_000, "ytInitialPlayerResponse.videoDetails.viewCount"
            ),
            "like_count": _metric(
                500, "ytInitialPlayerResponse.microformat.likeCount"
            ),
            "comment_sample_count": _metric(
                len(comment_rows), "youtubei_next.commentEntityPayload"
            ),
            "total_comment_count": _metric(
                25, "youtubei_next.commentsHeaderRenderer.countText"
            ),
        },
        "comments_posture": (
            "comments_sample_captured" if comments else "comments_not_exposed"
        ),
        "comment_capture_coverage": {
            "requested_page_limit": 1,
            "pages_fetched": 1,
            "selected_comment_count": len(comment_rows),
            "continuation_remaining_after_stop": False,
            "ordering_posture": "source_default_order_as_served",
        },
        "comments": comment_rows,
        "receipts": {
            "http_status": 200,
            "retrieval_time_utc": "2026-07-30T12:01:00Z",
            "auth": "logged_out",
            "js_executed": False,
        },
    }
    return YoutubeWatchFetch(
        video_id=_VIDEO_ID,
        raw_watch_html=b"<html>fixture</html>",
        packet=packet,
        comment_page_bodies=(
            YoutubeWatchCommentPage(
                filename="youtubei_next_page_01.json",
                raw_json_bytes=b'{"fixture":true}',
            ),
        ),
    )


def _caption() -> CaptionFetch:
    raw = json.dumps(
        {
            "events": [
                {
                    "tStartMs": 0,
                    "dDurationMs": 1200,
                    "segs": [{"utf8": "I compare both options side by side."}],
                }
            ]
        }
    ).encode("utf-8")
    return CaptionFetch(
        video_id=_VIDEO_ID,
        found=True,
        note="ok",
        lang="en",
        caption_kind="manual",
        json3_bytes=raw,
        flat_text="I compare both options side by side.",
        cue_count=1,
        title="Is this worth it?",
        channel_id=_CHANNEL_ID,
        publish_date_iso="2026-07-29",
        duration_s=42,
        tooling={"tool": "fixture"},
    )


def _captured_root(tmp_path: Path, *, channel_id: str = _CHANNEL_ID, comments: bool = True):
    root = DataLakeRoot.for_test(tmp_path / "lake")
    assessment_code, assessment_output = write_youtube_creator_assessment_packet(
        assessment_json=canonical_record_bytes(_assessment()),
        data_root=root,
    )
    assert assessment_code == 0
    assessment_packet_id = Path(assessment_output).name
    watch_code, _watch_output = write_youtube_watch_packet(
        _watch_fetch(channel_id=channel_id, comments=comments),
        data_root=root,
        decision_question="fixture comments",
        now_iso="2026-07-30T12:01:00Z",
    )
    assert watch_code == 0
    caption_code, _caption_output = write_caption_packet(
        _caption(),
        data_root=root,
        decision_question="fixture transcript",
        now_iso="2026-07-30T12:02:00Z",
    )
    assert caption_code == 0
    return root, assessment_packet_id


def _semantic_response(bundle: dict) -> dict:
    manifest = build_capability_manifest(bundle)
    content = next(
        alias
        for alias, row in manifest["evidence"].items()
        if row["kind"] == "creator_content"
    )
    comment = next(
        alias
        for alias, row in manifest["evidence"].items()
        if row["kind"] == "observed_comment"
    )
    point = {
        "statement": "Hire Dr Test when buyers need a difficult comparison made clear.",
        "claim_keys": ["decision"],
    }
    return {
        "schema_version": "creator_audience_semantic_response_v1",
        "generated_at": "2026-07-30T12:05:00Z",
        "claims": [
            {
                "claim_key": "decision",
                "axis": "purchase_decision_stage",
                "statement": "The comparison format resolves a concrete trade-off.",
                "commercial_implication": "Use Dr Test when buyers need decision clarity.",
                "relation": "agreement",
                "representative_evidence_aliases": [content, comment],
                "all_support_evidence_aliases": [content, comment],
                "counterevidence_aliases": [],
                "limitation": "The captured comments are not a platform census.",
                "engagement_salience_relied_on": False,
            }
        ],
        "creator_signal_projection": {
            "hire_verdict": point,
            "product_advantage": point,
            "creator_specific_execution": point,
            "observed_audience_response": point,
            "strongest_campaign_jobs": [point],
            "briefing_instructions": [point],
            "wrong_hire_boundary": point,
            "robustness_stamp": None,
        },
        "limitations": ["One selected video and a bounded comment sample."],
        "non_claims": ["not conversion evidence"],
        "actual_audience_demographics": "not_estimated",
    }


def test_youtube_prepare_and_submit_require_real_bound_evidence(tmp_path: Path) -> None:
    root, assessment_packet_id = _captured_root(tmp_path)
    bundle_path = tmp_path / "youtube.bundle.json"
    prompt_path = tmp_path / "youtube.prompt.txt"
    snapshot_path = tmp_path / "youtube.snapshot.json"
    account_id = deterministic_platform_account_id("youtube", _CHANNEL_ID)

    prepared = prepare_youtube_subscription_judgment(
        data_root=root,
        assessment_packet_id=assessment_packet_id,
        creator_id="youtube:@drtest",
        profile_subject_id=account_id,
        video_ids=[_VIDEO_ID],
        question="Who should hire Dr Test and why?",
        evidence_cutoff="2026-07-30T12:03:00Z",
        bundle_out=bundle_path,
        prompt_out=prompt_path,
    )

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert prepared["transcript_evidence_count"] == 1
    assert prepared["comment_evidence_count"] == 1
    assert bundle["platform_scope"] == "youtube"
    assert bundle["source_refs"]["youtube_channel_id"] == _CHANNEL_ID
    assert bundle["source_refs"]["watch_packets"][0]["source_sha256"].startswith(
        "sha256:"
    )
    assert bundle["source_refs"]["transcripts"][0]["source_sha256"].startswith(
        "sha256:"
    )
    assert "BEGIN_METHOD_DECK" in prompt_path.read_text(encoding="utf-8")

    response = json.dumps(_semantic_response(bundle)).encode("utf-8")
    submitted = submit_subscription_judgment(
        data_root=root,
        bundle_path=bundle_path,
        response_bytes=response,
        snapshot_out=snapshot_path,
    )
    assert submitted["status"] == "validated"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["platform_scope"] == "youtube"
    assert snapshot["judgment_claim_set"]["claims"][0]["source_item_ids"] == [
        _VIDEO_ID
    ]


def test_youtube_prepare_rejects_empty_comments_before_writing_outputs(
    tmp_path: Path,
) -> None:
    root, assessment_packet_id = _captured_root(tmp_path, comments=False)
    bundle_path = tmp_path / "empty.bundle.json"
    prompt_path = tmp_path / "empty.prompt.txt"

    with pytest.raises(ValueError, match="no captured comments"):
        prepare_youtube_subscription_judgment(
            data_root=root,
            assessment_packet_id=assessment_packet_id,
            creator_id="youtube:@drtest",
            profile_subject_id=deterministic_platform_account_id(
                "youtube", _CHANNEL_ID
            ),
            video_ids=[_VIDEO_ID],
            question="Who should hire Dr Test and why?",
            evidence_cutoff="2026-07-30T12:03:00Z",
            bundle_out=bundle_path,
            prompt_out=prompt_path,
        )
    assert not bundle_path.exists()
    assert not prompt_path.exists()


def test_youtube_prepare_rejects_cross_channel_watch_packet(tmp_path: Path) -> None:
    root, assessment_packet_id = _captured_root(
        tmp_path, channel_id="UC" + "B" * 22
    )

    with pytest.raises(ValueError, match="YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH"):
        prepare_youtube_subscription_judgment(
            data_root=root,
            assessment_packet_id=assessment_packet_id,
            creator_id="youtube:@drtest",
            profile_subject_id=deterministic_platform_account_id(
                "youtube", _CHANNEL_ID
            ),
            video_ids=[_VIDEO_ID],
            question="Who should hire Dr Test and why?",
            evidence_cutoff="2026-07-30T12:03:00Z",
            bundle_out=tmp_path / "mismatch.bundle.json",
            prompt_out=tmp_path / "mismatch.prompt.txt",
        )


def test_youtube_prepare_accepts_exact_packet_maps_without_lake_wide_discovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, assessment_packet_id = _captured_root(tmp_path)
    watch_packet_id = next(
        packet_id
        for packet_id in root.list_available(source_family="youtube")
        if root.load_raw_packet(packet_id).manifest.get("source_surface")
        == "youtube_watch_metadata_comments"
    )
    transcript_packet_id = next(
        packet_id
        for packet_id in root.list_available(source_family="youtube")
        if root.load_raw_packet(packet_id).manifest.get("source_surface")
        == "youtube_captions"
    )

    monkeypatch.setattr(
        "runners.run_youtube_creator_audience_triangulation.metadata_packet_for_video",
        lambda *_args, **_kwargs: pytest.fail("lake-wide watch discovery ran"),
    )
    monkeypatch.setattr(
        "runners.run_youtube_creator_audience_triangulation.transcript_sources_for_video",
        lambda *_args, **_kwargs: pytest.fail("lake-wide transcript discovery ran"),
    )

    prepared = prepare_youtube_subscription_judgment(
        data_root=root,
        assessment_packet_id=assessment_packet_id,
        creator_id="youtube:@drtest",
        profile_subject_id=deterministic_platform_account_id(
            "youtube", _CHANNEL_ID
        ),
        video_ids=[_VIDEO_ID],
        watch_packet_ids={_VIDEO_ID: watch_packet_id},
        transcript_packet_ids={_VIDEO_ID: transcript_packet_id},
        question="Who should hire Dr Test and why?",
        evidence_cutoff="2026-07-30T12:03:00Z",
        bundle_out=tmp_path / "exact.bundle.json",
        prompt_out=tmp_path / "exact.prompt.txt",
    )

    assert prepared["status"] == "SUBSCRIPTION_JUDGMENT_REQUIRED"


def test_youtube_exact_packet_maps_fail_closed_on_surface_coverage_and_duplicates(
    tmp_path: Path,
) -> None:
    root, assessment_packet_id = _captured_root(tmp_path)
    caption_packet_id = next(
        packet_id
        for packet_id in root.list_available(source_family="youtube")
        if root.load_raw_packet(packet_id).manifest.get("source_surface")
        == "youtube_captions"
    )
    account_id = deterministic_platform_account_id("youtube", _CHANNEL_ID)
    base = {
        "data_root": root,
        "assessment_packet_id": assessment_packet_id,
        "creator_id": "youtube:@drtest",
        "profile_subject_id": account_id,
        "question": "Who should hire Dr Test and why?",
        "evidence_cutoff": "2026-07-30T12:03:00Z",
        "bundle_out": tmp_path / "blocked.bundle.json",
        "prompt_out": tmp_path / "blocked.prompt.txt",
    }

    with pytest.raises(ValueError, match="watch packet .*unsupported source surface"):
        prepare_youtube_subscription_judgment(
            **base,
            video_ids=[_VIDEO_ID],
            watch_packet_ids={_VIDEO_ID: caption_packet_id},
        )
    with pytest.raises(ValueError, match="packet map must match selected video ids exactly"):
        prepare_youtube_subscription_judgment(
            **base,
            video_ids=[_VIDEO_ID],
            watch_packet_ids={},
        )
    with pytest.raises(ValueError, match="selected video ids must be unique"):
        prepare_youtube_subscription_judgment(
            **base,
            video_ids=[_VIDEO_ID, _VIDEO_ID],
        )
    assert _packet_map([f" {_VIDEO_ID} = packet_one "], option="--watch-packet") == {
        _VIDEO_ID: "packet_one"
    }
    with pytest.raises(ValueError, match="repeats video id"):
        _packet_map(
            [f"{_VIDEO_ID}=packet_one", f" {_VIDEO_ID} =packet_two"],
            option="--watch-packet",
        )
    assert not base["bundle_out"].exists()
    assert not base["prompt_out"].exists()


def test_youtube_asr_transcript_rejects_mismatched_metadata_channel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import runners.run_youtube_creator_audience_triangulation as judgment_runner

    asr_path = tmp_path / "asr.json"
    asr_path.write_text(
        json.dumps(
            {
                "video_id": _VIDEO_ID,
                "cues": [{"start_ms": 0, "end_ms": 1, "text": "fixture"}],
            }
        ),
        encoding="utf-8",
    )

    class _Root:
        def is_record_set_complete(self, **_kwargs) -> bool:
            return True

        def record_path(self, **_kwargs) -> Path:
            return asr_path

        @property
        def path(self) -> Path:
            return tmp_path

    monkeypatch.setattr(
        judgment_runner,
        "_selected_transcript_source",
        lambda *_args, **_kwargs: {
            "source_kind": "asr",
            "transcript_anchor": "pkt_audio",
            "asr_record_id": "asr_test",
        },
    )
    monkeypatch.setattr(
        judgment_runner,
        "_preserved_body",
        lambda *_args, **_kwargs: (
            json.dumps(
                {
                    "platform_video_id": _VIDEO_ID,
                    "channel_id": "UC" + "B" * 22,
                }
            ).encode("utf-8"),
            {"sha256": "0" * 64},
            "raw/fixture/capture_metadata.json",
        ),
    )

    with pytest.raises(ValueError, match="YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH"):
        judgment_runner._transcript_record(
            _Root(), video_id=_VIDEO_ID, channel_id=_CHANNEL_ID
        )


def test_youtube_assessment_rejects_selected_video_outside_observed_grids(
    tmp_path: Path,
) -> None:
    assessment = _assessment()
    assessment["selected_video_pages"][0]["video_id"] = "zzzzzzzzzzz"

    with pytest.raises(ValueError, match="present in the observed same-assessment grids"):
        write_youtube_creator_assessment_packet(
            assessment_json=canonical_record_bytes(assessment),
            output_directory=tmp_path / "assessment",
        )


def test_registry_cli_dispatches_youtube_frontier_and_admissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    observed: dict[str, object] = {}

    def _frontier(*, data_root, actions, recorded_at):
        observed["frontier"] = (data_root, actions, recorded_at)
        return {"status": "written"}

    def _candidate(*, data_root, packet_id, frontier_disposition_id):
        observed["candidate"] = (data_root, packet_id, frontier_disposition_id)
        return {"status": "admitted"}

    def _account(*, data_root, packet_id, judgment_outcome_path):
        observed["account"] = (data_root, packet_id, judgment_outcome_path)
        return {"status": "admitted"}

    import runners.run_creator_registry_lake as registry_runner

    monkeypatch.setattr(registry_runner, "write_creator_frontier_dispositions", _frontier)
    monkeypatch.setattr(registry_runner, "admit_youtube_creator_candidate", _candidate)
    monkeypatch.setattr(registry_runner, "admit_youtube_creator_account", _account)

    outcome = tmp_path / "outcome.json"
    outcome.write_text("{}", encoding="utf-8")
    assert registry_main([
        "frontier-disposition", "--data-root", str(root.path), "--platform", "youtube",
        "--handle", "DrTest", "--status", "eligible", "--priority", "high",
        "--reason-code", "owner_choice",
    ]) == 0
    capsys.readouterr()
    assert registry_main([
        "admit-youtube-candidate", "--data-root", str(root.path), "--packet-id", "pkt_test",
        "--frontier-disposition-id", "cfd_test",
    ]) == 0
    capsys.readouterr()
    assert registry_main([
        "admit-youtube", "--data-root", str(root.path), "--packet-id", "pkt_test",
        "--judgment-outcome", str(outcome),
    ]) == 0
    assert observed["frontier"][1][0]["platform"] == "youtube"
    assert observed["candidate"][1:] == ("pkt_test", "cfd_test")
    assert observed["account"][1:] == ("pkt_test", outcome)
