from __future__ import annotations

import json
import random
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

import source_capture.tiktok.creator_onboarding as onboarding
from capture_spine.tiktok_creator_discovery_frontier.frontier_selector import (
    apply_tiktok_creator_onboarding_dedupe,
)
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    load_creator_frontier_dispositions,
    write_creator_frontier_dispositions,
)
from data_lake.root import DataLakeRoot
from runners import run_source_capture_tiktok_creator_onboarding as runner
from source_capture.adapters.browser_snapshot import (
    BrowserPageObservationSuccess,
    BrowserSnapshotFailure,
    BrowserSnapshotFailureKind,
    BrowserPageResponse,
)
from source_capture.activity_journal import (
    SourceCaptureActivityJournal,
    validate_source_capture_activity_jsonl,
)
from source_capture.auth_state import AuthenticatedSessionMode
from source_capture.session_profiles import (
    OWNER_HANDOFF_BEFORE_ACTION,
    SourceCaptureSessionProfile,
)
from source_capture.source_access_provenance import HarnessProxyProfilePosture
from source_capture.tiktok.creator_onboarding import (
    TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
    TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
    TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
    TIKTOK_ONBOARDING_SELECTION_JSON_NAME,
    TikTokCreatorMarketDeferred,
    TikTokCreatorOnboardingError,
    assess_tiktok_creator_market,
    build_tiktok_grid_window,
    is_tiktok_profile_item_list_url,
    run_tiktok_creator_onboarding,
)


def _response(items: list[dict[str, object]]) -> BrowserPageResponse:
    return BrowserPageResponse(
        requested_url="https://www.tiktok.com/api/post/item_list/?cursor=0",
        final_url="https://www.tiktok.com/api/post/item_list/?cursor=0",
        status=200,
        ok=True,
        body_text=json.dumps({"itemList": items}),
        response_headers={"content-type": "application/json"},
    )


def _item(video_id: str, views: int, likes: int) -> dict[str, object]:
    return {
        "id": video_id,
        "author": {"uniqueId": "creator"},
        "stats": {
            "playCount": views,
            "diggCount": likes,
            "commentCount": 0,
        },
    }


def _capture(
    *,
    ordered_ids: Sequence[str] = (),
    items: Sequence[dict[str, object]] = (),
    suggested: list[dict[str, object]] | None = None,
    dom_view_text_by_id: dict[str, str] | None = None,
    hydration_payload: dict[str, object] | None = None,
    profile_metric_dom: dict[str, object] | None = None,
    page_context_observations: list[dict[str, object]] | None = None,
    pointer_action_receipts: list[dict[str, object]] | None = None,
) -> BrowserPageObservationSuccess:
    # Immutable-tuple defaults keep the signature safe; convert to fresh lists
    # per call so downstream behavior matches the previous explicit [] kwargs.
    ordered_ids = list(ordered_ids)
    items = list(items)
    dom: dict[str, object]
    if suggested is not None:
        dom = {
            "suggested_accounts": suggested,
            "suggested_surface_detected": True,
            "suggested_surface_root_count": 1,
            "suggested_profile_anchor_count": len(suggested),
            "relationship_dialog_detected": True,
            "suggested_tab_detected": True,
            "suggested_route": "followers_dialog_suggested_tab",
        }
    else:
        dom = {
            "ordered_videos": [
                {
                    "video_id": video_id,
                    "video_url": f"https://www.tiktok.com/@creator/video/{video_id}",
                    "visible_in_viewport": True,
                    "view_count_text_or_none": (
                        (dom_view_text_by_id or {}).get(video_id)
                    ),
                    "grid_position": index,
                }
                for index, video_id in enumerate(ordered_ids, start=1)
            ],
            "hydration_json_text": (
                json.dumps(hydration_payload)
                if hydration_payload is not None
                else None
            ),
        }
        if profile_metric_dom is not None:
            dom["profile_metric_dom"] = profile_metric_dom
    return BrowserPageObservationSuccess(
        requested_url="https://www.tiktok.com/@creator",
        final_url="https://www.tiktok.com/@creator",
        title="creator",
        visible_text="",
        dom_observation=dom,
        responses=[] if suggested is not None else [_response(items)],
        metadata={
            "post_load_pointer_actions": list(pointer_action_receipts or []),
            "human_challenge_handoff_attempts": [],
            "capture_timestamp": "2026-07-14T10:00:00Z",
            "lazy_load_scroll_passes_executed": 2,
            "lazy_load_scroll_stop_reason": "response_target_reached",
            "lazy_load_response_stop_condition_configured": True,
            **(
                {
                    "page_interaction_context_observations": (
                        page_context_observations
                    )
                }
                if page_context_observations is not None
                else {}
            ),
        },
        warning_notes=[],
        limitation_notes=[],
    )


def _stable_grid_capture_sequence(
    capture: BrowserPageObservationSuccess,
) -> list[BrowserPageObservationSuccess]:
    dom = dict(capture.dom_observation)
    rows = list(dom.get("ordered_videos") or [])
    initial_dom = dict(dom)
    initial_dom["ordered_videos"] = rows[:-1]
    initial = replace(capture, dom_observation=initial_dom)
    return [initial, capture, capture, capture]


def _suggested_surface_closed_capture(
    *,
    clicked: bool = True,
    modal_open_after: bool = False,
    suggested_accounts_expanded_after: bool = False,
    body_scroll_locked_after: bool = False,
    blocking_modal_count_after: int = 0,
    action_name: str = "tiktok_relationship_dialog_close_v0",
) -> BrowserPageObservationSuccess:
    capture = _capture()
    metadata = dict(capture.metadata)
    metadata["post_load_pointer_actions"] = [
        {
            "action_name": action_name,
            "clicked": clicked,
            "target_found": clicked,
        }
    ]
    return replace(
        capture,
        dom_observation={
            "suggested_modal_open": modal_open_after,
            "suggested_modal_count": 1 if modal_open_after else 0,
            "suggested_accounts_expanded": suggested_accounts_expanded_after,
            "suggested_accounts_expanded_root_count": (
                1 if suggested_accounts_expanded_after else 0
            ),
            "body_scroll_locked": body_scroll_locked_after,
            "blocking_modal_count": blocking_modal_count_after,
            "grid_video_anchor_count": 4,
        },
        metadata=metadata,
    )


def _oldest_probe_capture(
    *,
    active: bool,
    latest_active: bool = False,
    items: Sequence[dict[str, object]] = (),
    control_present: bool = True,
    no_public_posts: bool = False,
    clicked: bool | None = None,
    action_name: str = "tiktok_profile_oldest_sort_v0",
) -> BrowserPageObservationSuccess:
    capture = _capture(items=items)
    dom_observation = {
        "sort_control_present": control_present,
        "oldest_control_present": control_present,
        "oldest_active": active,
        "latest_active": latest_active,
        "ordered_videos": [
            {
                "video_id": str(item["id"]),
                "video_url": f"https://www.tiktok.com/@creator/video/{item['id']}",
                "pinned_visible": index == 0,
            }
            for index, item in enumerate(items)
        ],
        "no_public_posts_visible": no_public_posts,
    }
    metadata = dict(capture.metadata)
    if clicked is not None:
        metadata["post_load_pointer_actions"] = [
            {
                "action_name": action_name,
                "target_found": clicked,
                "clicked": clicked,
                "observed_response_count_before": 0,
                "observed_response_count_after": len(capture.responses),
            }
        ]
    return replace(capture, dom_observation=dom_observation, metadata=metadata)


@dataclass
class _FakeEngine:
    outcomes: list[BrowserPageObservationSuccess]

    def __post_init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def capture_page_observation(self, **kwargs: object) -> BrowserPageObservationSuccess:
        self.calls.append(dict(kwargs))
        return self.outcomes.pop(0)


def _profile() -> SourceCaptureSessionProfile:
    return SourceCaptureSessionProfile(
        alias="chowdakr_sg_tiktok",
        platform="tiktok",
        state_label="chowdakr_sg_tiktok",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        required_harness_proxy_profile_posture=(
            HarnessProxyProfilePosture.NO_PROXY_PROFILE_LOADED
        ),
        browser_backend="chrome_cdp",
        challenge_policy=OWNER_HANDOFF_BEFORE_ACTION,
    )


def _capture_grid(tmp_path: Path, engine: object, **overrides: object):
    """Call capture_tiktok_creator_grid with the standard kwargs of this file."""
    kwargs: dict[str, object] = dict(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        window_size=30,
        timeout_seconds=10.0,
        settle_seconds=0.25,
        max_grid_scroll_passes=40,
        engine=engine,
    )
    kwargs.update(overrides)
    return onboarding.capture_tiktok_creator_grid(**kwargs)


def _run_onboarding(tmp_path: Path, engine: object, **overrides: object):
    """Call run_tiktok_creator_onboarding with the standard kwargs of this file.

    A fresh _profile() is constructed per invocation, matching the previous
    per-call-site construction.
    """
    kwargs: dict[str, object] = dict(
        creator_handle="creator",
        session_profile=_profile(),
        output_dir=tmp_path,
        auth_state_root=tmp_path,
        window_size=27,
        engine=engine,
    )
    kwargs.update(overrides)
    return run_tiktok_creator_onboarding(**kwargs)


def test_runner_defaults_cold_agents_to_retained_chrome_session_alias(tmp_path: Path) -> None:
    args = runner.build_parser().parse_args(
        [
            "--creator-handle",
            "creator",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert args.session_profile == "chowdakr_sg_tiktok"


@pytest.mark.parametrize(
    ("bio", "decision", "reason", "flags"),
    [
        (
            "Addicted to scents 🇹🇷",
            "deferred_non_us_market",
            "non_us_market",
            ["TR"],
        ),
        ("NYC fragrance reviews", "passed_no_non_us_evidence", None, []),
        ("Dallas - Perfume - Beauty", "passed_no_non_us_evidence", None, []),
        ("Fragrance reviews in English", "passed_no_non_us_evidence", None, []),
        ("", "passed_no_non_us_evidence", None, []),
        ("NYC 🇹🇷", "deferred_non_us_market", "non_us_market", ["TR"]),
        ("Fragrance reviews 🇺🇸", "passed_no_non_us_evidence", None, ["US"]),
    ],
)
def test_market_assessment_uses_only_explicit_profile_bio_evidence(
    bio: str,
    decision: str,
    reason: str | None,
    flags: list[str],
) -> None:
    result = assess_tiktok_creator_market(
        creator_handle="Creator",
        profile_bio_text_or_none=bio,
        profile_bio_status="captured",
    )

    assert result["decision"] == decision
    assert result["reason_code_or_none"] == reason
    assert result["evidence"]["country_flag_codes"] == flags
    assert "us_location_cues" not in result["evidence"]


def test_runner_builds_inspectable_market_defer_action() -> None:
    assessment = assess_tiktok_creator_market(
        creator_handle="arda.scents",
        profile_bio_text_or_none="Addicted to scents 🇹🇷",
        profile_bio_status="captured",
    )

    action = runner._market_defer_action(
        creator_handle="arda.scents", assessment=assessment
    )

    assert action["status"] == "deferred"
    assert action["reason_code"] == "non_us_market"
    assert action["reconsideration"] == "new_signal"
    assert "country_flags=TR" in action["note"]


def _promotion_document(
    *,
    handle: str,
    registry_action: str,
    decision_reason_code: str,
    decision_note: str,
) -> dict[str, object]:
    return {
        "tiktok_creator_promotion_decisions": {
            "schema_version": "tiktok_creator_promotion_decisions_v1",
            "decisions": [
                {
                    "handle": handle,
                    "registry_action": registry_action,
                    "decision_reason_code": decision_reason_code,
                    "decision_note": decision_note,
                }
            ],
        }
    }


def test_explicit_promotion_persists_frontier_and_replays_idempotently(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    note = (
        "policy=tiktok_fragrance_creator_promotion_policy_v3; "
        "decision=promote_now; quality=5.000000; quality_p25=4.71311400; "
        "reliable_weekly_reach=100000.000000; weekly_reach_p25=186641.046627; "
        "cleared=quality_p25; reconsider=none"
    )
    document = _promotion_document(
        handle="swole_fragrance",
        registry_action="promote_now",
        decision_reason_code="cleared_quality_p25",
        decision_note=note,
    )

    first = runner._write_promotion_frontier_disposition(
        data_root=root,
        document=document,
        creator_handle="@SWOLE_FRAGRANCE",
    )
    second = runner._write_promotion_frontier_disposition(
        data_root=root,
        document=document,
        creator_handle="swole_fragrance",
    )

    assert first["status"] == "written"
    assert second["status"] == "already_current"
    current = load_creator_frontier_dispositions(root)[
        "creator_frontier_disposition_current"
    ]["dispositions"]
    assert len(current) == 1
    assert current[0]["status"] == "eligible"
    assert current[0]["priority_or_none"] == "normal"
    assert current[0]["note_or_none"] == note


@pytest.mark.parametrize(
    ("reason", "frontier_reason"),
    [
        ("below_both_p25", "low_potential"),
        ("quality_unavailable_weekly_below_p25", "other"),
    ],
)
def test_nonpromotion_reason_maps_to_inspectable_frontier_defer(
    reason: str, frontier_reason: str
) -> None:
    action = runner._promotion_frontier_action(
        {
            "handle": "weakcreator",
            "registry_action": "do_not_promote",
            "decision_reason_code": reason,
            "decision_note": "policy=v2; decision=do_not_promote",
        }
    )

    assert action["status"] == "deferred"
    assert action["reason_code"] == frontier_reason
    assert action["reconsideration"] == "new_signal"
    assert action["note"] == "policy=v2; decision=do_not_promote"


def test_batch_promotion_without_explicit_handle_does_not_mutate_frontier(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    grid_dir = tmp_path / "grids"
    grid_dir.mkdir()
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    grid = {
        "creator_handle": "batchcreator",
        "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"},
        "items": [
            {
                "createTime": int(captured.timestamp() - age * 86400),
                "pinned_visible": False,
                "stats": {"playCount": 30000},
            }
            for age in (16, 20, 25)
        ],
    }
    (grid_dir / "batchcreator.grid.json").write_text(
        json.dumps(grid), encoding="utf-8"
    )

    output, _document = runner._write_promotion_decisions(
        grid_dir,
        tmp_path / "output",
        registry_document={"creator_profile_current_view": {"profiles": []}},
        frontier_dispositions=load_creator_frontier_dispositions(root),
        data_root=root,
        explicit_creator_handle=None,
    )

    assert output.is_file()
    assert load_creator_frontier_dispositions(root)[
        "creator_frontier_disposition_current"
    ]["dispositions"] == []


@pytest.mark.parametrize(
    ("status", "reason_code", "reconsideration"),
    [
        ("deferred", "owner_choice", "owner_reopen"),
        ("deferred", "non_us_market", "new_signal"),
        ("rejected", "owner_choice", None),
    ],
)
def test_promotion_refuses_to_supersede_owner_nonperformance_disposition(
    tmp_path: Path,
    status: str,
    reason_code: str,
    reconsideration: str | None,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    action: dict[str, object] = {
        "platform": "tiktok",
        "handle": "ownerheld",
        "status": status,
        "reason_code": reason_code,
        "note": "owner decision",
    }
    if reconsideration is not None:
        action["reconsideration"] = reconsideration
    write_creator_frontier_dispositions(data_root=root, actions=[action])
    document = _promotion_document(
        handle="ownerheld",
        registry_action="promote_now",
        decision_reason_code="cleared_both_p25",
        decision_note=(
            "policy=tiktok_fragrance_creator_promotion_policy_v3; "
            "decision=promote_now"
        ),
    )

    with pytest.raises(ValueError, match="refusing to supersede non-performance"):
        runner._write_promotion_frontier_disposition(
            data_root=root,
            document=document,
            creator_handle="ownerheld",
        )

    current = load_creator_frontier_dispositions(root)[
        "creator_frontier_disposition_current"
    ]["dispositions"]
    assert len(current) == 1
    assert current[0]["status"] == status
    assert current[0]["reason_code"] == reason_code


def test_promotion_refuses_to_override_compatibility_owner_disposition(
    tmp_path: Path,
) -> None:
    """The hardcoded owner disposition is live authority with no lake row yet.

    It reaches the decision row only as ``owner_onboarding_disposition_or_none``,
    so the lake-state guard alone cannot see it.
    """
    root = DataLakeRoot.for_test(tmp_path / "lake")
    document = apply_tiktok_creator_onboarding_dedupe(
        _promotion_document(
            handle="eddeparfum",
            registry_action="promote_now",
            decision_reason_code="cleared_both_p25",
            decision_note=(
                "policy=tiktok_fragrance_creator_promotion_policy_v3; "
                "decision=promote_now"
            ),
        ),
        registry_states={},
        frontier_dispositions=load_creator_frontier_dispositions(root),
    )
    row = document["tiktok_creator_promotion_decisions"]["decisions"][0]
    assert row["onboarding_queue_status"] == "owner_deferred"

    with pytest.raises(ValueError, match="compatibility owner disposition"):
        runner._write_promotion_frontier_disposition(
            data_root=root,
            document=document,
            creator_handle="eddeparfum",
        )

    assert (
        load_creator_frontier_dispositions(root)[
            "creator_frontier_disposition_current"
        ]["dispositions"]
        == []
    )


def test_onboarding_rejects_window_below_sufficient_dom_minimum(tmp_path: Path) -> None:
    with pytest.raises(TikTokCreatorOnboardingError, match="at least 27"):
        # Wrapper-bound auth_state_root (and engine=None, the SUT default) are
        # inert here: window_size is rejected before either is consumed.
        _run_onboarding(tmp_path, None, window_size=26)


def test_profile_item_list_predicate_is_exact_and_local() -> None:
    assert is_tiktok_profile_item_list_url(
        "https://www.tiktok.com/api/post/item_list/?cursor=30"
    )
    assert not is_tiktok_profile_item_list_url(
        "https://www.tiktok.com/api/repost/item_list/?cursor=30"
    )
    assert not is_tiktok_profile_item_list_url(
        "https://example.com/api/post/item_list/?cursor=30"
    )


def test_grid_window_preserves_source_visible_order_and_complete_metrics() -> None:
    capture = _capture(
        ordered_ids=["3", "1", "2", "4"],
        items=[
            _item("1", 100, 10),
            _item("2", 200, 20),
            _item("3", 300, 30),
            _item("4", 400, 40),
        ],
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=3,
    )

    assert [item["video_id"] for item in window["items"]] == ["3", "1", "2"]
    assert [item["stats"]["playCount"] for item in window["items"]] == [300, 100, 200]


def test_grid_window_required_engagement_fails_loudly_when_incomplete() -> None:
    capture = _capture(
        ordered_ids=["1", "2"],
        items=[
            {
                "id": "1",
                "author": {"uniqueId": "creator"},
                "stats": {"playCount": 100, "diggCount": 10},
            },
            {
                "id": "2",
                "author": {"uniqueId": "creator"},
                "stats": {"playCount": 200, "commentCount": 2},
            },
        ],
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="2 of 2 rows missing required fields",
    ):
        build_tiktok_grid_window(
            creator_handle="creator",
            capture=capture,
            window_size=2,
            required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
        )


def test_grid_window_captures_exact_profile_metrics_from_matching_hydration() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[_item("1", 100, 10)],
        hydration_payload={
            "__DEFAULT_SCOPE__": {
                "webapp.user-detail": {
                    "userInfo": {
                        "user": {"uniqueId": "Creator"},
                        "stats": {"followerCount": 12_345, "heartCount": 678_901},
                    }
                }
            }
        },
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=1,
    )

    assert window["profile_metric_capture_policy_version"] == "tiktok_profile_metric_capture_v0"
    assert window["profile_metrics"]["follower_count"]["exact_value_or_none"] == 12_345
    assert window["profile_metrics"]["profile_total_like_count"]["exact_value_or_none"] == 678_901
    assert all(
        cell["posture"] == "observed"
        for cell in window["profile_metrics"].values()
    )


def test_grid_window_uses_exact_dom_profile_counts_but_rejects_compact_text() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[_item("1", 100, 10)],
        profile_metric_dom={
            "follower_count": {
                "element_present": True,
                "raw_text_or_none": "12,345",
            },
            "profile_total_like_count": {
                "element_present": True,
                "raw_text_or_none": "1.2M",
            },
        },
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=1,
    )

    follower = window["profile_metrics"]["follower_count"]
    likes = window["profile_metrics"]["profile_total_like_count"]
    assert follower["posture"] == "observed"
    assert follower["exact_value_or_none"] == 12_345
    assert likes["posture"] == "unavailable_with_reason"
    assert likes["exact_value_or_none"] is None
    assert likes["raw_text_or_none"] == "1.2M"
    assert likes["reason_or_none"] == "profile_header_dom_compact_or_non_integer"


def test_grid_window_ignores_mismatched_profile_hydration_identity() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[_item("1", 100, 10)],
        hydration_payload={
            "userInfo": {
                "user": {"uniqueId": "other_creator"},
                "stats": {"followerCount": 999_999, "heartCount": 888_888},
            }
        },
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=1,
    )

    assert all(
        cell["posture"] == "unavailable_with_reason"
        for cell in window["profile_metrics"].values()
    )


def test_grid_acquisition_reveals_one_batch_then_requires_two_stable_dom_polls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial_ids = [str(index) for index in range(1, 14)]
    final_ids = [str(index) for index in range(1, 29)]
    captures = [
        _capture(
            ordered_ids=initial_ids,
            items=[],
            dom_view_text_by_id={video_id: "1K" for video_id in initial_ids},
        ),
        *[
            _capture(
                ordered_ids=final_ids,
                items=[],
                dom_view_text_by_id={video_id: "1K" for video_id in final_ids},
            )
            for _ in range(3)
        ],
    ]
    calls: list[dict[str, object]] = []

    def fake_fetch(**kwargs: object) -> BrowserPageObservationSuccess:
        calls.append(kwargs)
        return captures.pop(0)

    monkeypatch.setattr(onboarding, "fetch_browser_page_observation_capture", fake_fetch)

    capture = _capture_grid(tmp_path, object())

    assert isinstance(capture, BrowserPageObservationSuccess)
    assert len(calls) == 4
    assert calls[0]["post_load_pointer_actions"] == (
        onboarding.TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION,
    )
    assert calls[0]["post_load_wheel_action"] is None
    wheel = calls[1]["post_load_wheel_action"]
    assert wheel is not None
    assert wheel.action_name == "tiktok_grid_one_dom_batch_humanized_reveal_v0"
    assert wheel.viewport_fraction_min == 0.20
    assert wheel.viewport_fraction_max == 0.35
    assert wheel.target_selector == "a[href*='/video/13']"
    assert calls[2]["post_load_wheel_action"] is None
    assert calls[3]["post_load_wheel_action"] is None
    assert capture.metadata["grid_acquisition_initial_dom_video_count"] == 13
    assert capture.metadata["grid_acquisition_final_dom_video_count"] == 28
    assert capture.metadata["grid_acquisition_new_dom_video_count"] == 15
    assert capture.metadata["grid_acquisition_sufficient_dom_video_count"] == 27
    assert capture.metadata["grid_acquisition_initial_window_sufficient"] is False
    assert capture.metadata["grid_acquisition_wheel_burst_count"] == 1
    assert capture.metadata["grid_acquisition_passive_polls_executed"] == 2
    assert capture.metadata["grid_acquisition_consecutive_stable_polls"] == 2
    assert capture.metadata["lazy_load_scroll_passes_executed"] == 0


def test_browser_capture_structural_logout_is_systemic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = _capture()
    capture.metadata["pre_action_stop_attempts"] = [
        {
            "matched": True,
            "structural_rule_name": "tiktok_logged_out_session_v0",
            "stop_kind": "logged_out_session",
        }
    ]
    monkeypatch.setattr(
        onboarding,
        "_fetch_browser_page_observation_capture",
        lambda **_kwargs: capture,
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="logged_out_session"):
        onboarding.fetch_browser_page_observation_capture(url="https://example.test")


@pytest.mark.parametrize("clicked", [False, True])
def test_grid_acquisition_preserves_pointer_outcome_for_sufficient_initial_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clicked: bool,
) -> None:
    ids = [str(index) for index in range(1, 33)]
    initial = _capture(
        ordered_ids=ids,
        items=[],
        dom_view_text_by_id={video_id: "1K" for video_id in ids},
        page_context_observations=[
            {
                "sequence_index": 0,
                "action_kind": "pointer",
                "before_action_name": "tiktok_relationship_dialog_close_v0",
                "observation_status": "observed",
                "visibility_state_or_none": "hidden",
                "document_has_focus_or_none": False,
            }
        ],
        pointer_action_receipts=[
            {
                "action_name": "tiktok_relationship_dialog_close_v0",
                "target_found": clicked,
                "clicked": clicked,
            }
        ],
    )
    passive = _capture(
        ordered_ids=ids,
        items=[],
        dom_view_text_by_id={video_id: "1K" for video_id in ids},
    )
    captures = [initial, passive, passive]
    calls: list[dict[str, object]] = []

    def fake_fetch(**kwargs: object) -> BrowserPageObservationSuccess:
        calls.append(kwargs)
        return captures.pop(0)

    monkeypatch.setattr(onboarding, "fetch_browser_page_observation_capture", fake_fetch)

    capture = _capture_grid(tmp_path, object())

    assert isinstance(capture, BrowserPageObservationSuccess)
    assert len(calls) == 3
    assert all(call["post_load_wheel_action"] is None for call in calls)
    assert capture.metadata["grid_acquisition_initial_dom_video_count"] == 32
    assert capture.metadata["grid_acquisition_final_dom_video_count"] == 32
    assert capture.metadata["grid_acquisition_new_dom_video_count"] == 0
    assert capture.metadata["grid_acquisition_new_batch_observed"] is False
    assert capture.metadata["grid_acquisition_initial_window_sufficient"] is True
    assert capture.metadata["grid_acquisition_wheel_burst_count"] == 0
    assert capture.metadata["grid_acquisition_stop_reason"] == (
        "initial_sufficient_window_stabilized"
    )
    assert capture.metadata["grid_acquisition_pointer_action_receipts"] == [
        {
            "capture_index": 0,
            "action_name": "tiktok_relationship_dialog_close_v0",
            "target_found": clicked,
            "clicked": clicked,
        }
    ]
    assert capture.metadata["page_interaction_context_observations"][0][
        "capture_index"
    ] == 0
    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=30,
    )
    assert window["collection_receipt"]["pointer_action_receipts"] == (
        capture.metadata["grid_acquisition_pointer_action_receipts"]
    )


def test_grid_acquisition_reloads_same_profile_once_to_recover_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = [str(index) for index in range(1, 31)]
    initial = _capture(
        ordered_ids=ids,
        items=[],
        dom_view_text_by_id={video_id: "1K" for video_id in ids},
        page_context_observations=[
            {
                "sequence_index": 0,
                "action_kind": "navigation",
                "before_action_name": "page_navigation",
                "observation_status": "observed",
                "visibility_state_or_none": "visible",
                "document_has_focus_or_none": True,
            }
        ],
    )
    initial.metadata["same_url_navigation_suppression_count"] = 1
    exact_items = [
        {
            "id": video_id,
            "author": {"uniqueId": "creator"},
            "stats": {
                "playCount": index * 100,
                "diggCount": index * 10,
                "commentCount": index,
            },
        }
        for index, video_id in enumerate(ids, start=1)
    ]
    refreshed = _capture(
        ordered_ids=ids,
        items=exact_items[:19],
        dom_view_text_by_id={video_id: "1K" for video_id in ids},
        page_context_observations=[
            {
                "sequence_index": 0,
                "action_kind": "navigation",
                "before_action_name": "page_navigation",
                "observation_status": "observed",
                "visibility_state_or_none": "hidden",
                "document_has_focus_or_none": False,
            }
        ],
    )
    paginated = _capture(
        ordered_ids=ids,
        items=exact_items[19:],
        dom_view_text_by_id={video_id: "1K" for video_id in ids},
    )
    truncated_wheel = _capture(
        ordered_ids=ids[:19],
        items=[],
        dom_view_text_by_id={video_id: "1K" for video_id in ids[:19]},
    )
    shifted_ids = ids[11:]
    passive = _capture(
        ordered_ids=shifted_ids,
        items=[],
        dom_view_text_by_id={
            video_id: "1K" for video_id in shifted_ids
        },
    )
    captures = [
        initial,
        refreshed,
        truncated_wheel,
        paginated,
        passive,
        passive,
        passive,
    ]
    calls: list[dict[str, object]] = []

    def fake_fetch(**kwargs: object) -> BrowserPageObservationSuccess:
        calls.append(kwargs)
        return captures.pop(0)

    monkeypatch.setattr(onboarding, "fetch_browser_page_observation_capture", fake_fetch)

    capture = _capture_grid(
        tmp_path,
        object(),
        required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
    )

    assert isinstance(capture, BrowserPageObservationSuccess)
    assert [call["force_same_url_reload"] for call in calls] == [
        False,
        True,
        False,
        False,
        False,
        False,
        False,
    ]
    assert calls[2]["post_load_wheel_action"] is not None
    assert calls[3]["post_load_wheel_action"] is not None
    assert capture.metadata["grid_metric_reload_attempted"] is True
    assert capture.metadata["grid_metric_reload_recovered"] is True
    assert capture.metadata["grid_acquisition_wheel_burst_count"] == 2
    assert capture.metadata["grid_acquisition_initial_metrics_sufficient"] is False
    assert capture.metadata["grid_acquisition_final_metrics_sufficient"] is True
    assert capture.metadata["page_interaction_context_observations"] == [
        {
            "capture_index": 0,
            "sequence_index": 0,
            "action_kind": "navigation",
            "before_action_name": "page_navigation",
            "observation_status": "observed",
            "visibility_state_or_none": "visible",
            "document_has_focus_or_none": True,
        },
        {
            "capture_index": 1,
            "sequence_index": 0,
            "action_kind": "navigation",
            "before_action_name": "page_navigation",
            "observation_status": "observed",
            "visibility_state_or_none": "hidden",
            "document_has_focus_or_none": False,
        },
    ]
    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=30,
        required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
    )
    assert len(window["items"]) == 30
    assert all(
        set(TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS) <= set(item["stats"])
        for item in window["items"]
    )
    assert window["collection_receipt"]["metric_reload_attempted"] is True
    assert window["collection_receipt"]["metric_reload_recovered"] is True
    assert window["collection_receipt"]["page_interaction_context_observations"] == (
        capture.metadata["page_interaction_context_observations"]
    )


def test_grid_acquisition_rejects_a_new_batch_below_the_minimum_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial_ids = [str(index) for index in range(1, 14)]
    undersized_ids = [str(index) for index in range(1, 26)]
    captures = [
        _capture(
            ordered_ids=ids,
            items=[],
            dom_view_text_by_id={video_id: "1K" for video_id in ids},
        )
        for ids in (initial_ids, undersized_ids, undersized_ids, undersized_ids)
    ]

    monkeypatch.setattr(
        onboarding,
        "fetch_browser_page_observation_capture",
        lambda **_kwargs: captures.pop(0),
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="one grid DOM batch did not produce the minimum usable window",
    ):
        _capture_grid(tmp_path, object())


def test_grid_acquisition_adapts_until_first_new_batch_then_stops_wheeling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial_ids = [str(index) for index in range(1, 14)]
    final_ids = [str(index) for index in range(1, 29)]
    captures = [
        _capture(
            ordered_ids=ids,
            items=[],
            dom_view_text_by_id={video_id: "1K" for video_id in ids},
        )
        for ids in (initial_ids, initial_ids, final_ids, final_ids, final_ids)
    ]
    calls: list[dict[str, object]] = []

    def fake_fetch(**kwargs: object) -> BrowserPageObservationSuccess:
        calls.append(kwargs)
        return captures.pop(0)

    monkeypatch.setattr(onboarding, "fetch_browser_page_observation_capture", fake_fetch)

    capture = _capture_grid(tmp_path, object())

    assert isinstance(capture, BrowserPageObservationSuccess)
    assert capture.metadata["grid_acquisition_wheel_burst_count"] == 2
    assert capture.metadata["grid_acquisition_new_dom_video_count"] == 15
    assert calls[1]["post_load_wheel_action"] is not None
    assert calls[2]["post_load_wheel_action"] is not None
    assert calls[3]["post_load_wheel_action"] is None
    assert calls[4]["post_load_wheel_action"] is None


def test_grid_acquisition_fails_when_one_batch_never_stabilizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures = [
        _capture(
            ordered_ids=[str(index) for index in range(1, count + 1)],
            items=[],
            dom_view_text_by_id={str(index): "1K" for index in range(1, count + 1)},
        )
        for count in (10, 20, 21, 22, 23, 24)
    ]

    monkeypatch.setattr(
        onboarding,
        "fetch_browser_page_observation_capture",
        lambda **_kwargs: captures.pop(0),
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="did not stabilize"):
        _capture_grid(tmp_path, object())


def test_grid_acquisition_fails_instead_of_accepting_no_new_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = _capture(
        ordered_ids=[str(index) for index in range(1, 18)],
        items=[],
        dom_view_text_by_id={str(index): "1K" for index in range(1, 18)},
    )
    captures = [capture for _ in range(5)]
    monkeypatch.setattr(
        onboarding,
        "fetch_browser_page_observation_capture",
        lambda **_kwargs: captures.pop(0),
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="no new grid DOM batch"):
        _capture_grid(tmp_path, object())


def test_grid_window_uses_dom_compact_views_when_response_metrics_are_absent() -> None:
    capture = _capture(
        ordered_ids=["one", "two"],
        items=[],
        dom_view_text_by_id={"one": "31.8K", "two": "1.2M"},
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=2,
    )
    selection = onboarding.build_tiktok_grid_video_selection(
        window["items"],
        expected_item_count=2,
        selection_count=1,
    )

    assert [item["stats"]["playCount"] for item in window["items"]] == [31_800, 1_200_000]
    assert window["items"][0]["grid_view_count"] == {
        "raw_text_or_none": "31.8K",
        "parsed_approximate_count_or_none": 31_800,
        "source": "profile_grid_dom_view_count_footer",
        "source_display_precision": "rounded_compact",
        "used_for_play_count": True,
    }
    assert selection["selection_policy"]["required_metrics"] == ["playCount"]
    assert selection["selection_summary"]["selected_video_ids_in_reach_order"] == ["two"]


def test_grid_window_preserves_full_source_stats_and_zero_or_missing_ranking_metrics() -> None:
    capture = _capture(
        ordered_ids=["zero", "missing_like", "full"],
        items=[
            {
                "id": "zero",
                "author": {"uniqueId": "creator"},
                "stats": {
                    "playCount": 0,
                    "diggCount": 0,
                    "commentCount": 7,
                    "shareCount": 2,
                    "collectCount": 3,
                },
            },
            {
                "id": "missing_like",
                "author": {"uniqueId": "creator"},
                "stats": {"playCount": 42, "commentCount": 5},
            },
            {
                "id": "full",
                "author": {"uniqueId": "creator"},
                "stats": {
                    "playCount": 100,
                    "diggCount": 11,
                    "commentCount": 9,
                    "shareCount": 4,
                    "collectCount": 6,
                },
            },
        ],
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=3,
    )

    assert [item["video_id"] for item in window["items"]] == [
        "zero",
        "missing_like",
        "full",
    ]
    assert window["items"][0]["stats"] == {
        "playCount": 0,
        "diggCount": 0,
        "commentCount": 7,
        "shareCount": 2,
        "collectCount": 3,
    }
    assert window["items"][1]["stats"] == {
        "playCount": 42,
        "commentCount": 5,
    }
    assert window["items"][2]["stats"]["commentCount"] == 9


def test_grid_window_accepts_missing_author_with_exact_creator_url() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[{"id": "1", "stats": {"playCount": 100, "diggCount": 10}}],
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=1,
    )

    assert [item["video_id"] for item in window["items"]] == ["1"]


def test_grid_window_excludes_unrelated_handle_dom_url() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[_item("1", 100, 10)],
    )
    capture.dom_observation["ordered_videos"][0]["video_url"] = (
        "https://www.tiktok.com/@unrelated/video/1"
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="usable grid window"):
        build_tiktok_grid_window(
            creator_handle="creator",
            capture=capture,
            window_size=1,
        )


def test_grid_window_excludes_explicit_mismatched_payload_author() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[
            {
                "id": "1",
                "author": {"uniqueId": "unrelated"},
                "stats": {"playCount": 100, "diggCount": 10},
            }
        ],
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="usable grid window"):
        build_tiktok_grid_window(
            creator_handle="creator",
            capture=capture,
            window_size=1,
        )


def test_grid_window_does_not_count_nested_item_list_metric_node() -> None:
    creator_item = _item("1", 100, 10)
    creator_item["duetInfo"] = {
        "id": "999",
        "stats": {"playCount": 99999, "diggCount": 9999},
    }
    capture = _capture(
        ordered_ids=["1", "999"],
        items=[creator_item],
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="usable grid window"):
        build_tiktok_grid_window(
            creator_handle="creator",
            capture=capture,
            window_size=2,
        )


def test_market_gate_defers_after_same_read_and_before_grid_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    suggested = _capture(
        suggested=[
            {
                "handle": "adjacent",
                "profile_url": "https://www.tiktok.com/@adjacent",
                "display_text_or_none": "Adjacent",
            }
        ]
    )
    suggested.dom_observation.update(
        {
            "profile_bio_text_or_none": "Addicted to scents 🇹🇷",
            "profile_bio_element_detected": True,
        }
    )
    engine = _FakeEngine([suggested, _suggested_surface_closed_capture()])
    progress_events: list[tuple[str, dict[str, object]]] = []

    with pytest.raises(TikTokCreatorMarketDeferred) as exc_info:
        _run_onboarding(
            tmp_path,
            engine,
            enforce_us_market_gate=True,
            progress_fn=lambda event, fields: progress_events.append((event, fields)),
        )

    assert exc_info.value.assessment["reason_code_or_none"] == "non_us_market"
    assert len(engine.calls) == 2
    assert [event for event, _fields in progress_events] == [
        "collect_suggested_accounts",
        "close_suggested_surface",
        "market_gate",
    ]
    assert not (tmp_path / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME).exists()
    assert not (tmp_path / TIKTOK_ONBOARDING_SELECTION_JSON_NAME).exists()
    receipt = json.loads(
        (tmp_path / TIKTOK_ONBOARDING_RECEIPT_JSON_NAME).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "deferred"
    assert receipt["terminal_stage"] == "market_gate"
    assert receipt["window_size"] == 0
    assert receipt["selected_count"] == 0
    assert receipt["completed_deep_capture_count"] == 0
    assert receipt["market_assessment_or_none"]["evidence"][
        "country_flag_codes"
    ] == ["TR"]


def test_market_gate_reaches_grid_without_affirmative_us_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    suggested = _capture(suggested=[])
    suggested.dom_observation.update(
        {
            "profile_bio_text_or_none": "Fragrance reviews in English",
            "profile_bio_element_detected": True,
        }
    )
    engine = _FakeEngine([suggested, _suggested_surface_closed_capture()])
    progress_events: list[tuple[str, dict[str, object]]] = []

    def reached_grid(**_kwargs: object) -> object:
        raise RuntimeError("grid capture reached")

    monkeypatch.setattr(onboarding, "capture_tiktok_creator_grid", reached_grid)

    with pytest.raises(RuntimeError, match="grid capture reached"):
        _run_onboarding(
            tmp_path,
            engine,
            enforce_us_market_gate=True,
            progress_fn=lambda event, fields: progress_events.append((event, fields)),
        )

    assert [event for event, _fields in progress_events] == [
        "collect_suggested_accounts",
        "close_suggested_surface",
        "market_gate",
        "collect_grid",
    ]


def test_onboarding_writes_selection_before_same_engine_deep_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    suggested = _capture(
        suggested=[
            {
                "handle": "adjacent",
                "profile_url": "https://www.tiktok.com/@adjacent",
                "display_text_or_none": "Adjacent",
            }
        ],
    )
    suggested.dom_observation.update(
        {
            "profile_bio_text_or_none": "Budget fragrance reviews 🇬🇧",
            "profile_bio_element_detected": True,
        }
    )
    grid_items = [
        _item("1", 400, 20),
        _item("2", 300, 60),
        _item("3", 200, 10),
        _item("4", 100, 5),
    ] + [
        _item(str(video_id), 100 - video_id, 1)
        for video_id in range(5, 28)
    ]
    subtitle_url = "https://v16-webapp.tiktok.com/profile-grid-subtitle.webvtt"
    grid_items[0]["video"] = {
        "subtitleInfos": [
            {
                "Format": "webvtt",
                "LanguageCodeName": "eng-US",
                "Url": subtitle_url,
            }
        ]
    }
    grid = _capture(
        ordered_ids=[str(video_id) for video_id in range(1, 28)],
        items=grid_items,
    )
    engine = _FakeEngine(
        [
            suggested,
            _suggested_surface_closed_capture(),
            *_stable_grid_capture_sequence(grid),
            _oldest_probe_capture(active=False),
            _oldest_probe_capture(
                active=True,
                clicked=True,
                items=[
                    {**_item("90", 10, 1), "createTime": 1_600_000_100},
                    {**_item("80", 20, 2), "createTime": 1_500_000_000},
                ],
            ),
        ]
    )
    deep_calls: list[dict[str, object]] = []
    progress_events: list[tuple[str, dict[str, object]]] = []

    def deep_capture(**kwargs: object) -> dict[str, object]:
        deep_calls.append(dict(kwargs))
        assert kwargs["engine"] is engine
        assert (tmp_path / TIKTOK_ONBOARDING_SELECTION_JSON_NAME).is_file()
        sequence = kwargs["page_capture_sequence_fn"]
        sequence.receipt["status"] = "complete"
        sequence.receipt["selected_video_ids_in_capture_order"] = ["1", "2"]
        return {
            "grid_result": {"response_items": []},
            "cadence_result": {
                "requested_video_count": 2,
                "completed_count": 2,
                "results": [{"video_id": "1"}, {"video_id": "2"}],
                "failures": [],
            },
        }

    paths = _run_onboarding(
        tmp_path,
        engine,
        selection_count=2,
        deep_capture_fn=deep_capture,
        progress_fn=lambda event, fields: progress_events.append((event, fields)),
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        random_seed=7,
        sleep_fn=lambda _seconds: None,
    )

    assert len(engine.calls) == 8
    assert engine.calls[1]["dom_extract_arg"] == {"creator_handle": "creator"}
    assert [
        action.action_name for action in engine.calls[1]["post_load_pointer_actions"]
    ] == ["tiktok_relationship_dialog_close_v0"]
    assert engine.calls[2]["dom_extract_arg"] == {"creator_handle": "creator"}
    assert engine.calls[3]["post_load_wheel_action"].action_name == (
        "tiktok_grid_one_dom_batch_humanized_reveal_v0"
    )
    assert engine.calls[3]["post_load_wheel_action"].target_selector == (
        "a[href*='/video/26']"
    )
    assert engine.calls[4]["post_load_wheel_action"] is None
    assert engine.calls[5]["post_load_wheel_action"] is None
    assert len(deep_calls) == 1
    assert [event for event, _fields in progress_events] == [
        "collect_suggested_accounts",
        "close_suggested_surface",
        "collect_grid",
        "freeze_window",
        "select",
        "enter_grid_overlay_capture_sequence",
        "deep_capture",
        "observe_earliest_public_post",
        "capture_profile_link_hub",
        "close",
    ]
    assert progress_events[-4][1] == {"selected_count": 2}
    assert deep_calls[0]["video_urls"] == [
        "https://www.tiktok.com/@creator/video/1",
        "https://www.tiktok.com/@creator/video/2",
    ]
    assert "cloakbrowser_humanize" not in deep_calls[0]
    suggested_receipt = json.loads(
        paths.suggested_accounts_json_path.read_text(encoding="utf-8")
    )
    assert suggested_receipt["profile_bio_text_or_none"] == (
        "Budget fragrance reviews 🇬🇧"
    )
    assert suggested_receipt["profile_bio_status"] == "captured"
    receipt = json.loads(paths.onboarding_receipt_json_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "complete"
    assert receipt["session_profile"] == "chowdakr_sg_tiktok"
    assert receipt["window_size"] == 27
    assert receipt["selection_count"] == 2
    assert receipt["window_cap"] == 27
    assert receipt["suggested_accounts_status_or_none"] == "captured"
    assert receipt["suggested_surface_close_before_grid_or_none"]["status"] == "closed"
    assert receipt["suggested_surface_close_before_grid_or_none"]["close_clicked"] is True
    assert (
        receipt["suggested_surface_close_before_grid_or_none"][
            "suggested_modal_open_after"
        ]
        is False
    )
    assert receipt["completed_deep_capture_count"] == 2
    assert receipt["challenge_count"] == 0
    assert receipt["human_challenge_handoff_count"] == 0
    assert receipt["account_safety_stop"] is False
    assert receipt["initial_deep_capture_wait_or_none"]["planned_seconds"] == 0.0
    assert (
        receipt["initial_deep_capture_wait_or_none"]["cadence_plan"]["mode"]
        == "bounded_jitter"
    )
    activity_rows = validate_source_capture_activity_jsonl(
        paths.activity_journal_jsonl_path.read_bytes()
    )
    assert activity_rows[0]["event_type"] == "run_started"
    assert activity_rows[-1]["event_type"] == "terminal"
    assert activity_rows[-1]["status"] == "complete"
    assert [row["phase"] for row in receipt["phase_chronology"]] == [
        "onboarding_started",
        "grid_and_selection_complete",
        "first_deep_capture_released",
        "grid_overlay_deep_capture_sequence_completed",
        "deep_capture_completed",
        "earliest_public_post_observation_completed",
        "profile_link_hub_capture_completed",
    ]
    assert receipt["grid_deep_entry_or_none"]["status"] == "complete"
    assert receipt["grid_deep_entry_or_none"]["targeted_tile_scroll_performed"] is False
    assert receipt["grid_deep_entry_or_none"]["grid_pagination_input_method"] == (
        "cloakbrowser.human.scroll_to_element"
    )
    assert receipt["grid_deep_entry_or_none"]["retry_waits"] == []
    assert receipt["grid_deep_entry_or_none"]["direct_video_navigation_count"] == 0
    assert deep_calls[0]["capture_route"] == "grid_tile_overlay"
    assert callable(deep_calls[0]["page_capture_sequence_fn"])
    assert deep_calls[0]["profile_grid_subtitle_sources_by_video_id"] == {
        "1": {
            "id": "1",
            "video": {
                "subtitleInfos": [
                    {
                        "Format": "webvtt",
                        "LanguageCodeName": "eng-US",
                        "Url": subtitle_url,
                    }
                ]
            },
        }
    }
    assert subtitle_url not in (
        tmp_path / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME
    ).read_text(encoding="utf-8")
    assert subtitle_url not in (
        tmp_path / TIKTOK_ONBOARDING_SELECTION_JSON_NAME
    ).read_text(encoding="utf-8")
    grid_window = json.loads(
        (tmp_path / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME).read_text(encoding="utf-8")
    )
    assert grid_window["earliest_public_post_observation"]["published_at_utc"] == (
        "2017-07-14T02:40:00Z"
    )


def test_oldest_probe_chooses_minimum_exact_time_despite_pinned_disorder(
    tmp_path: Path,
) -> None:
    newer = {**_item("90", 10, 1), "createTime": 1_700_000_000}
    oldest = {**_item("80", 20, 2), "createTime": 1_500_000_000}
    engine = _FakeEngine(
        [
            _oldest_probe_capture(active=False),
            _oldest_probe_capture(active=True, items=[newer, oldest], clicked=True),
        ]
    )

    result = onboarding.capture_tiktok_earliest_public_post_observation(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=engine,
        utc_now_fn=lambda: datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert result["status"] == "observed"
    assert result["source_video_id"] == "80"
    assert result["published_at_utc"] == "2017-07-14T02:40:00Z"
    assert len(engine.calls) == 2


def test_oldest_probe_retries_once_when_clicked_state_does_not_activate(
    tmp_path: Path,
) -> None:
    oldest = {**_item("80", 20, 2), "createTime": 1_500_000_000}
    engine = _FakeEngine(
        [
            _oldest_probe_capture(active=False),
            _oldest_probe_capture(active=False, clicked=True, items=[oldest]),
            _oldest_probe_capture(active=True, clicked=True, items=[oldest]),
        ]
    )

    result = onboarding.capture_tiktok_earliest_public_post_observation(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=engine,
    )

    assert result["status"] == "observed"
    assert result["selection_attempt_count"] == 2
    assert len(engine.calls) == 3
    assert [
        action.action_name
        for action in engine.calls[-1]["post_load_pointer_actions"]
    ] == ["tiktok_profile_oldest_sort_v0"]


def test_oldest_probe_types_control_absence_without_click(tmp_path: Path) -> None:
    engine = _FakeEngine([_oldest_probe_capture(active=False, control_present=False)])

    result = onboarding.capture_tiktok_earliest_public_post_observation(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=engine,
    )

    assert result["status"] == "oldest_sort_not_exposed"
    assert result["published_at_utc"] is None
    assert len(engine.calls) == 1


def test_oldest_probe_types_verified_empty_profile(tmp_path: Path) -> None:
    engine = _FakeEngine(
        [
            _oldest_probe_capture(active=False),
            _oldest_probe_capture(active=True, no_public_posts=True, clicked=True),
        ]
    )

    result = onboarding.capture_tiktok_earliest_public_post_observation(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=engine,
    )

    assert result["status"] == "no_public_posts"
    assert len(engine.calls) == 2


@pytest.mark.parametrize("defect", ["selection", "identity"])
def test_oldest_probe_fails_closed_on_unverified_selection_or_identity(
    tmp_path: Path, defect: str
) -> None:
    wrong = {
        "id": "90",
        "author": {"uniqueId": "other" if defect == "identity" else "creator"},
        "stats": {"playCount": 1, "diggCount": 1, "commentCount": 0},
        "createTime": 1_700_000_000,
    }
    engine = _FakeEngine(
        [
            _oldest_probe_capture(active=False),
            _oldest_probe_capture(
                active=defect != "selection", items=[wrong], clicked=True
            ),
        ]
    )

    with pytest.raises(TikTokCreatorOnboardingError):
        onboarding.capture_tiktok_earliest_public_post_observation(
            profile_url="https://www.tiktok.com/@creator",
            creator_handle="creator",
            storage_state_path=tmp_path / "state.json",
            timeout_seconds=10,
            settle_seconds=0,
            engine=engine,
        )


def test_grid_overlay_sequence_waits_randomized_bounded_delay_then_retries(
    tmp_path: Path,
) -> None:
    not_ready = _clicked_capture("1", overlay_ready=False)
    engine = _FakeEngine(
        [
            _visible_tiles_capture("1"),
            not_ready,
            _closed_overlay_capture(),
            _visible_tiles_capture("1"),
            _clicked_capture("1"),
        ]
    )
    receipt = _grid_overlay_receipt()
    sleeps: list[float] = []
    monotonic_values = iter((100.0, 155.0))
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        sleep_fn=sleeps.append,
        monotonic_fn=lambda: next(monotonic_values),
    )

    chosen_url, capture = sequence(
        0, ["https://www.tiktok.com/@creator/video/1"]
    )

    assert chosen_url.endswith("/video/1")
    assert capture.dom_observation["video_overlay_detected"] is True
    assert sleeps == [55.0]
    assert receipt["retry_waits"] == [
        {
            "video_attempt_index": 0,
            "configured_range_seconds": {"min": 45.0, "max": 75.0},
            "planned_seconds": 55.0,
            "actual_seconds": 55.0,
            "observed_at_utc": "2026-07-14T10:00:00Z",
        }
    ]
    assert receipt["attempts"][0]["outcome"] == (
        "overlay_not_ready_or_identity_mismatch"
    )
    assert receipt["attempts"][1]["outcome"] == "overlay_ready"


def test_grid_entry_retry_delay_sampling_is_bounded_and_nondegenerate() -> None:
    samples = {
        onboarding._sample_browser_delay_seconds(
            onboarding.GRID_ENTRY_RETRY_DELAY_RANGE,
            rng=random.Random(seed),
        )
        for seed in range(20)
    }

    assert len(samples) > 1
    assert all(45.0 <= sample <= 75.0 for sample in samples)


def test_grid_overlay_sequence_accepts_visible_overlay_without_item_struct(
    tmp_path: Path,
) -> None:
    subtitle_url = "https://v16-webapp.tiktok.com/subtitle.webvtt"
    engine = _FakeEngine([_visible_tiles_capture("1"), _clicked_capture("1")])
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        profile_grid_subtitle_sources_by_video_id={
            "1": {
                "id": "1",
                "video": {"subtitleInfos": [{"Url": subtitle_url}]},
            }
        },
    )

    _chosen_url, capture = sequence(
        0, ["https://www.tiktok.com/@creator/video/1"]
    )

    assert capture.dom_observation["hydration_json_text"] is None
    assert receipt["attempts"][0]["item_struct_required"] is False
    assert receipt["attempts"][0]["outcome"] == "overlay_ready"
    assert receipt["status"] == "complete"
    response_predicate = engine.calls[1]["response_url_predicate"]
    assert response_predicate(subtitle_url) is True
    assert (
        response_predicate("https://v16-webapp.tiktok.com/other.webvtt") is False
    )


def test_grid_overlay_sequence_reuses_grid_observation_returned_by_overlay_close(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine([_closed_overlay_capture("1"), _clicked_capture("1")])
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
    )
    sequence.current_overlay_url = "https://www.tiktok.com/@creator/video/2"

    chosen_url, capture = sequence(
        1, ["https://www.tiktok.com/@creator/video/1"]
    )

    assert chosen_url.endswith("/video/1")
    assert capture.dom_observation["video_overlay_detected"] is True
    assert len(engine.calls) == 2
    assert engine.calls[0]["post_load_pointer_actions"] == (
        onboarding.TIKTOK_VIDEO_OVERLAY_CLOSE_ACTION,
    )
    assert engine.calls[1]["post_load_pointer_actions"][0].action_name == (
        "tiktok_visible_selected_grid_video_v0"
    )
    assert receipt["attempts"][0]["click_action_or_none"]["target_variant"] == (
        "media_link_surface"
    )


def test_grid_overlay_sequence_uses_logical_positions_and_targeted_human_scroll(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _visible_tiles_capture(visible_min=1, visible_max=3, scroll_y=0),
            _visible_tiles_capture(visible_min=4, visible_max=6, scroll_y=600),
            _visible_tiles_capture(
                "1", visible_min=7, visible_max=9, scroll_y=1200
            ),
            _clicked_capture("1"),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=2,
        selected_grid_position=9,
    )

    sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert receipt["grid_pagination_passes_executed"] == 2
    assert engine.calls[1]["post_load_action_script"] is None
    assert engine.calls[2]["post_load_action_script"] is None
    assert engine.calls[1]["post_load_wheel_action"].direction == "down"
    assert engine.calls[2]["post_load_wheel_action"].direction == "down"
    assert engine.calls[1]["post_load_wheel_action"].target_selector == (
        "a[href*='/video/1']"
    )
    assert engine.calls[2]["post_load_wheel_action"].target_selector == (
        "a[href*='/video/1']"
    )
    assert engine.calls[1]["post_load_wheel_action"].viewport_fraction_min == 0.20
    assert engine.calls[1]["post_load_wheel_action"].viewport_fraction_max == 0.35
    click_action = engine.calls[3]["post_load_pointer_actions"][0]
    assert click_action.candidate_selector == (
        "a[href*='/video/1'] .video-count"
    )
    assert click_action.text_markers == ("31.8k",)
    assert {
        variant.variant_name for variant in click_action.target_variants
    } == {"media_link_surface", "view_count_footer"}
    variants_by_name = {
        variant.variant_name: variant for variant in click_action.target_variants
    }
    assert (
        variants_by_name["media_link_surface"].candidate_selector
        == "a[href*='/video/1']"
    )
    assert (
        variants_by_name["media_link_surface"].target_fraction_x_min,
        variants_by_name["media_link_surface"].target_fraction_x_max,
        variants_by_name["media_link_surface"].target_fraction_y_min,
        variants_by_name["media_link_surface"].target_fraction_y_max,
    ) == (0.20, 0.80, 0.25, 0.70)
    assert (
        variants_by_name["view_count_footer"].candidate_selector
        == "a[href*='/video/1'] .video-count"
    )
    assert (
        variants_by_name["view_count_footer"].target_fraction_x_min,
        variants_by_name["view_count_footer"].target_fraction_x_max,
        variants_by_name["view_count_footer"].target_fraction_y_min,
        variants_by_name["view_count_footer"].target_fraction_y_max,
    ) == (0.15, 0.85, 0.25, 0.75)
    assert click_action.wait_after_range == onboarding.TIKTOK_STATE_WAIT_2500_DELAY_RANGE
    assert receipt["logical_grid_positions_remembered"] is True
    assert receipt["absolute_pixel_positions_cached"] is False
    assert [row["direction"] for row in receipt["grid_pagination_passes"]] == [
        "down",
        "down",
    ]
    assert receipt["targeted_tile_scroll_performed"] is True
    assert receipt["grid_pagination_input_method"] == (
        "cloakbrowser.human.scroll_to_element"
    )
    assert [
        row["target_video_id"] for row in receipt["grid_pagination_passes"]
    ] == ["1", "1"]
    # An advancing grid must not be misread as stalled: every wheel pass showed
    # fresh-state progress, so no no-progress stop is recorded.
    assert receipt["grid_pagination_stop_reason"] is None
    assert [
        row.get("progress_since_previous")
        for row in receipt["grid_pagination_passes"]
    ] == ["advanced", "selected_tile_visible"]
    assert "scrollIntoView" not in (
        onboarding.TIKTOK_VISIBLE_SELECTED_GRID_TILES_DOM_EXTRACT_SCRIPT
    )
    assert "if (!clickTargetVisible || !clickTargetText) continue;" in (
        onboarding.TIKTOK_VISIBLE_SELECTED_GRID_TILES_DOM_EXTRACT_SCRIPT
    )


def test_grid_overlay_sequence_wheels_up_for_earlier_logical_position(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _visible_tiles_capture(visible_min=7, visible_max=9, scroll_y=1200),
            _visible_tiles_capture(
                "1", visible_min=1, visible_max=3, scroll_y=500
            ),
            _clicked_capture("1"),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=1,
        selected_grid_position=1,
    )

    sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert engine.calls[1]["post_load_wheel_action"].direction == "up"
    assert engine.calls[1]["post_load_wheel_action"].target_selector == (
        "a[href*='/video/1']"
    )
    assert receipt["grid_pagination_passes"][0]["direction"] == "up"


def test_grid_overlay_sequence_fails_after_single_click_retry(tmp_path: Path) -> None:
    engine = _FakeEngine(
        [
            _visible_tiles_capture("1"),
            _clicked_capture("1", overlay_ready=False),
            _closed_overlay_capture(),
            _visible_tiles_capture(),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=0,
    )

    with pytest.raises(TikTokCreatorOnboardingError, match="after one bounded retry"):
        sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert receipt["status"] == "failed"
    assert len(receipt["attempts"]) == 1


def test_grid_overlay_sequence_stops_wheeling_on_short_grid_no_progress(
    tmp_path: Path,
) -> None:
    # Reproduces the observed short/non-expanded grid: every wheel pass returns
    # the same fresh state (scroll_y=0, unchanged logical range, unchanged
    # document height) and never exposes the selected tile. The sequence must
    # stop after a bounded number of no-value wheel passes and fail loudly,
    # instead of burning the full pagination budget, and must take no wait.
    short_grid = lambda: _visible_tiles_capture(
        visible_min=1, visible_max=11, scroll_y=0, document_height=1605
    )
    engine = _FakeEngine([short_grid() for _ in range(4)])
    receipt = _grid_overlay_receipt()
    sleeps: list[float] = []
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        sleep_fn=sleeps.append,
        pagination_pass_cap=10,
        selected_grid_position=17,
    )

    with pytest.raises(
        TikTokCreatorOnboardingError, match="bounded grid pagination exhausted"
    ):
        sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert sleeps == []
    assert receipt["status"] == "failed"
    assert receipt["grid_pagination_stop_reason"] == "no_progress_stall"
    # Stopped at the stall limit, far short of the pass cap of 10.
    assert receipt["grid_pagination_passes_executed"] == (
        onboarding.GRID_PAGINATION_NO_PROGRESS_STALL_LIMIT
    )
    passes = receipt["grid_pagination_passes"]
    assert [row["progress_since_previous"] for row in passes] == [
        "no_progress" for _ in passes
    ]
    assert passes[-1]["outcome"] == "no_progress_stall_budget_stopped"
    # Directionality is still derived from logical positions (17 is below 1..11).
    assert {row["direction"] for row in passes} == {"down"}


def test_grid_overlay_sequence_keeps_wheeling_while_grid_advances(
    tmp_path: Path,
) -> None:
    # A grid that advances each pass (fresh state changes) must not be misread as
    # stalled even past the stall limit; the sequence keeps paginating until the
    # selected tile is exposed, then clicks it.
    engine = _FakeEngine(
        [
            _visible_tiles_capture(visible_min=1, visible_max=3, scroll_y=0),
            _visible_tiles_capture(visible_min=4, visible_max=6, scroll_y=780),
            _visible_tiles_capture(visible_min=7, visible_max=9, scroll_y=1560),
            _visible_tiles_capture(visible_min=10, visible_max=12, scroll_y=2340),
            _visible_tiles_capture(
                "1", visible_min=13, visible_max=15, scroll_y=3120
            ),
            _clicked_capture("1"),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=6,
        selected_grid_position=15,
    )

    _chosen_url, capture = sequence(
        0, ["https://www.tiktok.com/@creator/video/1"]
    )

    assert capture.dom_observation["video_overlay_detected"] is True
    assert receipt["status"] == "complete"
    assert receipt["grid_pagination_stop_reason"] is None
    assert receipt["grid_pagination_passes_executed"] == 4
    assert [
        row["progress_since_previous"]
        for row in receipt["grid_pagination_passes"]
    ] == ["advanced", "advanced", "advanced", "selected_tile_visible"]


def test_grid_overlay_sequence_stops_when_frozen_window_identity_drifted(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _visible_tiles_capture(
                visible_min=1,
                visible_max=3,
                loaded_ids=("new-1", "new-2", "new-3"),
            )
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=10,
        selected_grid_position=3,
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="frozen grid window no longer matches the live grid identity",
    ):
        sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert receipt["grid_pagination_passes_executed"] == 0
    assert receipt["grid_pagination_stop_reason"] == (
        "frozen_window_identity_drift"
    )
    assert receipt["frozen_window_identity_drift_detected"] is True
    assert receipt["frozen_window_live_overlap_count_at_stop_or_none"] == 0
    assert receipt["loaded_grid_video_count_at_stop_or_none"] == 3


def test_grid_overlay_sequence_stops_on_non_consecutive_progress_cycle(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _visible_tiles_capture(
                visible_min=1, visible_max=3, scroll_y=0, document_height=3000
            ),
            _visible_tiles_capture(
                visible_min=4, visible_max=6, scroll_y=600, document_height=3000
            ),
            _visible_tiles_capture(
                visible_min=1, visible_max=3, scroll_y=0, document_height=3000
            ),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = _grid_overlay_sequence(
        tmp_path=tmp_path,
        engine=engine,
        receipt=receipt,
        pagination_pass_cap=10,
        selected_grid_position=9,
    )

    with pytest.raises(
        TikTokCreatorOnboardingError, match="bounded grid pagination exhausted"
    ):
        sequence(0, ["https://www.tiktok.com/@creator/video/1"])

    assert receipt["grid_pagination_passes_executed"] == 2
    assert receipt["grid_pagination_stop_reason"] == "progress_cycle"
    assert receipt["grid_pagination_passes"][-1]["progress_since_previous"] == (
        "progress_cycle"
    )
    assert receipt["grid_pagination_passes"][-1]["outcome"] == (
        "progress_cycle_budget_stopped"
    )


def test_grid_overlay_sequence_keeps_direction_when_pending_tile_is_in_range(
    tmp_path: Path,
) -> None:
    closed_at_370 = _visible_tiles_capture(
        visible_min=1, visible_max=32, scroll_y=370, document_height=2461
    )
    closed_at_370.metadata["post_load_pointer_actions"] = [
        {
            "action_name": "tiktok_video_overlay_close_v0",
            "target_found": True,
            "clicked": True,
            "move_steps": 6,
        }
    ]
    engine = _FakeEngine(
        [
            _visible_tiles_capture(
                visible_min=1, visible_max=22, scroll_y=0, document_height=2461
            ),
            _visible_tiles_capture(
                "1", visible_min=1, visible_max=32, scroll_y=370, document_height=2461
            ),
            _clicked_capture("1"),
            closed_at_370,
            _visible_tiles_capture(
                visible_min=1, visible_max=32, scroll_y=370, document_height=2461
            ),
            _visible_tiles_capture(
                "2", visible_min=10, visible_max=32, scroll_y=700, document_height=2461
            ),
            _clicked_capture("2"),
        ]
    )
    receipt = _grid_overlay_receipt()
    sequence = onboarding._GridOverlayCaptureSequence(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        selected_video_ids=["1", "2"],
        window_by_id={
            video_id: {
                "video_id": video_id,
                "video_url": f"https://www.tiktok.com/@creator/video/{video_id}",
                "visible_in_viewport": True,
                "grid_position": position,
                "views": 400,
                "likes": 20,
            }
            for video_id, position in (("1", 20), ("2", 24))
        },
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        pagination_pass_cap=2,
        engine=engine,
        rng=type("FirstChoice", (), {"choice": lambda _self, rows: rows[0]})(),
        sleep_fn=lambda _seconds: None,
        monotonic_fn=lambda: 0.0,
        utc_now_fn=lambda: datetime(2026, 7, 14, 10, 0, tzinfo=UTC),
        receipt=receipt,
    )

    sequence(
        0,
        [
            "https://www.tiktok.com/@creator/video/1",
            "https://www.tiktok.com/@creator/video/2",
        ],
    )
    sequence(1, ["https://www.tiktok.com/@creator/video/2"])

    wheel_directions = [
        call["post_load_wheel_action"].direction
        for call in engine.calls
        if call.get("post_load_wheel_action") is not None
    ]
    assert wheel_directions == ["down", "down"]
    assert receipt["grid_pagination_stop_reason"] is None
    assert receipt["status"] == "complete"


def test_grid_below_sufficient_window_fails_before_deep_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    engine = _FakeEngine(
        [
            _capture(suggested=[]),
            _suggested_surface_closed_capture(),
                *_stable_grid_capture_sequence(
                    _capture(
                        ordered_ids=["1"],
                        items=[
                            _item("1", 400, 20),
                        ],
                    )
                ),
        ]
    )
    deep_called = False

    def deep_capture(**_kwargs: object) -> dict[str, object]:
        nonlocal deep_called
        deep_called = True
        return {}

    with pytest.raises(TikTokCreatorOnboardingError, match="minimum usable window"):
        _run_onboarding(
            tmp_path,
            engine,
            selection_count=2,
            deep_capture_fn=deep_capture,
        )

    assert deep_called is False
    assert not (tmp_path / TIKTOK_ONBOARDING_SELECTION_JSON_NAME).exists()
    receipt = json.loads(
        (tmp_path / TIKTOK_ONBOARDING_RECEIPT_JSON_NAME).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "failed"
    assert receipt["terminal_stage"] == "collect_grid"
    assert receipt["error_or_none"].startswith("TikTokCreatorOnboardingError:")


def test_suggested_surface_must_close_before_grid_capture(tmp_path: Path) -> None:
    engine = _FakeEngine(
        [_suggested_surface_closed_capture(clicked=False, modal_open_after=True)]
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="suggested surface remained open before grid capture",
    ):
        onboarding._close_suggested_surface_before_grid(
            profile_url="https://www.tiktok.com/@creator",
            creator_handle="creator",
            suggested_status="captured",
            suggested_outer_ui_route="followers_dialog_suggested_tab",
            storage_state_path=tmp_path / "state.json",
            timeout_seconds=10.0,
            settle_seconds=0.0,
            engine=engine,
        )


def test_not_visible_suggested_surface_can_already_be_closed(tmp_path: Path) -> None:
    engine = _FakeEngine([_suggested_surface_closed_capture(clicked=False)])

    receipt = onboarding._close_suggested_surface_before_grid(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        suggested_status="not_visible",
        suggested_outer_ui_route="profile_suggested_accounts_view_all_fallback",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        engine=engine,
    )

    assert receipt["status"] == "already_closed"
    assert receipt["close_required"] is False
    assert receipt["suggested_modal_open_after"] is False
    assert engine.calls[0]["post_load_pointer_actions"] == ()


def test_fallback_suggested_surface_uses_exact_toggle_collapse(tmp_path: Path) -> None:
    engine = _FakeEngine(
        [
            _suggested_surface_closed_capture(
                action_name="tiktok_suggested_accounts_collapse_before_grid_v0"
            )
        ]
    )

    receipt = onboarding._close_suggested_surface_before_grid(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        suggested_status="captured",
        suggested_outer_ui_route="profile_suggested_accounts_view_all_fallback",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        engine=engine,
    )

    actions = engine.calls[0]["post_load_pointer_actions"]
    assert [action.action_name for action in actions] == [
        "tiktok_suggested_accounts_collapse_before_grid_v0"
    ]
    assert actions[0].candidate_selector == (
        "button[data-e2e='show-suggested-accounts']"
        "[aria-label='Suggested accounts']"
    )
    assert actions[0].visual_top_right_x_fallback is False
    assert actions[0].visual_x_geometric_fallback is False
    assert receipt["close_action_route"] == "suggested_accounts_toggle_collapse"
    assert receipt["suggested_accounts_expanded_after"] is False
    assert receipt["body_scroll_locked_after"] is False


def test_fallback_suggested_surface_must_be_collapsed_before_grid(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _suggested_surface_closed_capture(
                suggested_accounts_expanded_after=True,
                action_name="tiktok_suggested_accounts_collapse_before_grid_v0",
            )
        ]
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="suggested surface remained open before grid capture",
    ):
        onboarding._close_suggested_surface_before_grid(
            profile_url="https://www.tiktok.com/@creator",
            creator_handle="creator",
            suggested_status="captured",
            suggested_outer_ui_route="profile_suggested_accounts_view_all_fallback",
            storage_state_path=tmp_path / "state.json",
            timeout_seconds=10.0,
            settle_seconds=0.0,
            engine=engine,
        )


def test_suggested_close_fails_if_an_unrelated_modal_keeps_scroll_locked(
    tmp_path: Path,
) -> None:
    engine = _FakeEngine(
        [
            _suggested_surface_closed_capture(
                body_scroll_locked_after=True,
                blocking_modal_count_after=1,
            )
        ]
    )

    with pytest.raises(
        TikTokCreatorOnboardingError,
        match="suggested surface remained open before grid capture",
    ):
        onboarding._close_suggested_surface_before_grid(
            profile_url="https://www.tiktok.com/@creator",
            creator_handle="creator",
            suggested_status="captured",
            suggested_outer_ui_route="followers_dialog_suggested_tab",
            storage_state_path=tmp_path / "state.json",
            timeout_seconds=10.0,
            settle_seconds=0.0,
            engine=engine,
        )


def test_account_safety_stop_detection_reads_failure_triage_only() -> None:
    assert onboarding._has_account_safety_stop(
        {
            "failures": [
                {
                    "blocker_triage": {
                        "account_safety_stop": True,
                        "automatic_retry_allowed": False,
                    }
                }
            ]
        }
    ) is True
    assert onboarding._has_account_safety_stop(
        {"failures": [{"blocker_triage": {"challenge_kind": "captcha"}}]}
    ) is False


def test_onboarding_cli_emits_machine_readable_progress_and_blocker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner._emit_progress("collect_grid", {"window_cap": 30})
    runner._emit_blocker("CDP_UNREACHABLE", "preflight")

    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        runner.PROGRESS_PREFIX
        + '{"event": "collect_grid", "window_cap": 30}',
        runner.BLOCKER_PREFIX
        + '{"code": "CDP_UNREACHABLE", "phase": "preflight"}',
    ]


def test_onboarding_cli_emits_dedicated_account_safety_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )

    def account_safety_stop(**_kwargs: object) -> object:
        raise TikTokCreatorOnboardingError("account_safety_stop")

    monkeypatch.setattr(runner, "run_tiktok_creator_onboarding", account_safety_stop)

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )

    assert exc_info.value.code == 2
    assert runner.BLOCKER_PREFIX + (
        '{"code": "ACCOUNT_SAFETY_STOP", "phase": "deep_capture"}'
    ) in capsys.readouterr().out.splitlines()


def test_onboarding_cli_emits_systemic_logged_out_session_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )

    def logged_out_session(**_kwargs: object) -> object:
        raise TikTokCreatorOnboardingError("logged_out_session")

    monkeypatch.setattr(runner, "run_tiktok_creator_onboarding", logged_out_session)

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )

    assert exc_info.value.code == 2
    assert runner.BLOCKER_PREFIX + (
        '{"code": "LOGGED_OUT_SESSION", '
        '"phase": "authenticated_browser_session"}'
    ) in capsys.readouterr().out.splitlines()


def test_onboarding_cli_enforces_market_gate_for_new_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    paths = onboarding.TikTokCreatorProfileRefreshOutputPaths(
        grid_window_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        onboarding_receipt_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
    )
    paths.grid_window_json_path.write_text(
        json.dumps(
            {
                "creator_handle": "arda.scents",
                "profile_bio_status": "observed",
                "profile_bio_text_or_none": "Addicted to scents 🇹🇷",
            }
        ),
        encoding="utf-8",
    )
    paths.onboarding_receipt_json_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "capture_scope": "profile_refresh",
                "creator_handle": "arda.scents",
                "session_profile": "chowdakr_sg_tiktok",
                "window_size": 1,
                "selection_count": 0,
                "window_cap": 30,
                "selected_count": 0,
                "completed_deep_capture_count": 0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "new_candidate",
                "registry_onboarding_state": None,
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_onboarding",
        lambda **_kwargs: pytest.fail("new_capture must not invoke deep capture"),
    )
    monkeypatch.setattr(
        runner, "run_tiktok_creator_profile_refresh", lambda **_kwargs: paths
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "arda.scents",
                "--creator-intent",
                "new_capture",
                "--output-dir",
                str(output_dir),
            ]
        )

    assert exc_info.value.code == 2
    assert runner.BLOCKER_PREFIX + json.dumps(
        {
            "code": "CANDIDATE_MARKET_DEFERRED",
            "phase": "market_gate",
            "recovery": "reconsider after the explicit non-US profile signal changes",
        },
        sort_keys=True,
    ) in capsys.readouterr().out.splitlines()


def test_new_capture_is_assessment_only_and_admits_grid_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    paths = onboarding.TikTokCreatorProfileRefreshOutputPaths(
        grid_window_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        onboarding_receipt_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
    )
    grid_bytes = json.dumps(
        {
            "creator_handle": "new_creator",
            "profile_bio_status": "observed",
            "profile_bio_text_or_none": "Fragrance reviews",
        }
    ).encode()
    paths.grid_window_json_path.write_bytes(grid_bytes)
    paths.onboarding_receipt_json_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "capture_scope": "profile_refresh",
                "creator_handle": "new_creator",
                "session_profile": "chowdakr_sg_tiktok",
                "window_size": 12,
                "selection_count": 0,
                "window_cap": 30,
                "selected_count": 0,
                "completed_deep_capture_count": 0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            output_dir / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "new_candidate",
                "registry_onboarding_state": None,
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_onboarding",
        lambda **_kwargs: pytest.fail("new_capture must not invoke deep capture"),
    )
    monkeypatch.setattr(
        runner, "run_tiktok_creator_profile_refresh", lambda **_kwargs: paths
    )
    monkeypatch.setattr(
        runner,
        "write_tiktok_batch_packet",
        lambda **_kwargs: pytest.fail("new_capture must not write a deep batch packet"),
    )
    monkeypatch.setattr(
        runner,
        "prepare_onboarding",
        lambda **_kwargs: pytest.fail("new_capture must not prepare audience work"),
    )
    monkeypatch.setattr(
        runner,
        "enqueue_creator_audience_job",
        lambda **_kwargs: pytest.fail("new_capture must not enqueue audience work"),
    )
    admitted: dict[str, object] = {}

    def fake_grid_writer(**kwargs: object) -> tuple[int, str]:
        admitted.update(kwargs)
        return 0, str(tmp_path / "grid-packet")

    monkeypatch.setattr(runner, "write_tiktok_grid_packet", fake_grid_writer)

    assert (
        runner.main(
            [
                "--creator-handle",
                "new_creator",
                "--creator-intent",
                "new_capture",
                "--output-dir",
                str(output_dir),
                "--admit-output",
                str(tmp_path / "grid-packet"),
            ]
        )
        == 0
    )
    assert admitted["grid_window_json"] == grid_bytes
    assert admitted["decision_question"] == runner.PROFILE_REFRESH_DECISION_QUESTION
    summary_line = next(
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(runner.SUMMARY_PREFIX)
    )
    summary = json.loads(summary_line.removeprefix(runner.SUMMARY_PREFIX))
    assert summary["capture_scope"] == "candidate_assessment"
    assert summary["completed_deep_capture_count"] == 0
    assert summary["audience_queue_job_or_none"] is None


def test_new_capture_rejects_force_deep_recapture_before_browser_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "new_candidate",
                "registry_onboarding_state": None,
            },
        ),
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: pytest.fail("browser must not be probed"),
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_onboarding",
        lambda **_kwargs: pytest.fail("deep capture must not run"),
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "new_creator",
                "--creator-intent",
                "new_capture",
                "--output-dir",
                str(tmp_path / "out"),
                "--prior-capture-pointer",
                "01PRIOR",
                "--force-deep-recapture",
            ]
        )

    assert exc_info.value.code == 2
    assert (
        "new_capture is assessment-only and does not permit deep recapture"
        in capsys.readouterr().err
    )



def test_onboarding_cli_defaults_to_long_tail_profile() -> None:
    args = runner.build_parser().parse_args(
        [
            "--creator-handle",
            "creator",
            "--output-dir",
            "out",
        ]
    )

    assert args.window_size == 30
    assert args.creator_intent == "new_onboarding"
    assert not hasattr(args, "selection_fraction")
    assert args.cadence_min_gap_seconds is None
    assert args.cadence_max_gap_seconds is None


def test_onboarding_default_cadence_policy_is_five_twenty_with_five_percent_tail() -> None:
    policy = onboarding._resolve_onboarding_cadence_policy(
        min_gap_seconds=None,
        max_gap_seconds=None,
        window_seconds=None,
    )
    plan = policy.build_plan(slot_count=8, random_seed=11)

    assert plan.mode == "weighted_long_tail"
    assert plan.typical_min_gap_seconds == 5.0
    assert plan.typical_max_gap_seconds == 20.0
    assert plan.tail_min_gap_seconds == 20.0
    assert plan.tail_max_gap_seconds == 60.0
    assert plan.tail_probability == 0.05


def test_onboarding_cli_requires_cadence_override_pair() -> None:
    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                "out",
                "--cadence-min-gap-seconds",
                "5",
            ]
        )

    assert exc_info.value.code == 2


def test_new_onboarding_without_handle_selects_next_registry_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_document = {
        "creator_profile_current_view": {
            "profiles": [
                {
                    "profile_subject_id": "acct_tt_done",
                    "profile_subject_kind": "platform_account",
                    "onboarding": {"onboarding_state": "onboarded"},
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": "acct_tt_done",
                            "public_handle": "done_creator",
                            "public_profile_url": "https://www.tiktok.com/@done_creator",
                        }
                    ],
                },
                {
                    "profile_subject_id": "acct_tt_next",
                    "profile_subject_kind": "platform_account",
                    "onboarding": {"onboarding_state": "not_onboarded"},
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": "acct_tt_next",
                            "public_handle": "next_creator",
                            "public_profile_url": "https://www.tiktok.com/@next_creator",
                        }
                    ],
                },
            ]
        }
    }
    monkeypatch.setattr(
        runner,
        "load_creator_profile_current_view",
        lambda _path: registry_document,
    )

    handle, candidate = runner._resolve_creator_handle(
        creator_handle=None,
        creator_intent="new_onboarding",
        registry_path=tmp_path / "registry.json",
    )

    assert handle == "next_creator"
    assert candidate is not None
    assert candidate["platform_account_id"] == "acct_tt_next"


def test_new_onboarding_auto_selection_uses_registry_and_skips_frontier_blocked() -> None:
    registry_document = {
        "creator_profile_current_view": {
            "profiles": [
                {
                    "profile_subject_id": f"acct_{handle}",
                    "profile_subject_kind": "platform_account",
                    "onboarding": {"onboarding_state": "not_onboarded"},
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": f"acct_{handle}",
                            "public_handle": handle,
                            "public_profile_url": f"https://www.tiktok.com/@{handle}",
                        }
                    ],
                }
                for handle in ("blocked_creator", "ready_creator")
            ]
        }
    }
    frontier = {
        "creator_frontier_disposition_current": {
            "schema_version": "creator_frontier_disposition_current_v1",
            "dispositions": [
                {"public_handle": "blocked_creator", "status": "deferred"}
            ],
        }
    }

    handle, candidate = runner._resolve_creator_handle(
        creator_handle=None,
        creator_intent="new_onboarding",
        registry_document=registry_document,
        frontier_dispositions=frontier,
    )

    assert handle == "ready_creator"
    assert candidate["selection_policy"] == "sole_actionable_registry_not_onboarded_account"


def test_new_onboarding_auto_selection_skips_pending_audience_job() -> None:
    registry_document = {
        "creator_profile_current_view": {
            "profiles": [
                {
                    "profile_subject_id": f"acct_{handle}",
                    "profile_subject_kind": "platform_account",
                    "onboarding": {"onboarding_state": "not_onboarded"},
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": f"acct_{handle}",
                            "public_handle": handle,
                            "public_profile_url": f"https://www.tiktok.com/@{handle}",
                        }
                    ],
                }
                for handle in ("pending_creator", "ready_creator")
            ]
        }
    }

    handle, candidate = runner._resolve_creator_handle(
        creator_handle=None,
        creator_intent="new_onboarding",
        registry_document=registry_document,
        pending_profile_subject_ids={"acct_pending_creator"},
    )

    assert handle == "ready_creator"
    assert candidate["platform_account_id"] == "acct_ready_creator"


def test_onboarding_cli_rejects_window_below_sufficient_dom_minimum() -> None:
    with pytest.raises(SystemExit):
        runner.build_parser().parse_args(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                "out",
                "--window-size",
                "26",
            ]
        )


def test_onboarding_cli_admission_passes_full_grid_and_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "staging"
    output_dir.mkdir()
    paths = onboarding.TikTokCreatorOnboardingOutputPaths(
        suggested_accounts_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_SUGGESTED_JSON_NAME,
        grid_window_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        selection_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_SELECTION_JSON_NAME,
        live_grid_json_path=output_dir / onboarding.TIKTOK_LIVE_BATCH_GRID_JSON_NAME,
        live_cadence_json_path=output_dir
        / onboarding.TIKTOK_LIVE_BATCH_CADENCE_JSON_NAME,
        onboarding_receipt_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
        activity_journal_jsonl_path=output_dir / "source_capture_activity.jsonl",
    )
    paths.suggested_accounts_json_path.write_text("{}", encoding="utf-8")
    paths.grid_window_json_path.write_bytes(b'{"grid":"complete"}')
    paths.selection_json_path.write_bytes(b'{"selection":"bound"}')
    paths.live_grid_json_path.write_bytes(b'{"deep_grid":"selected"}')
    paths.live_cadence_json_path.write_bytes(b'{"cadence":"complete"}')
    paths.onboarding_receipt_json_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "creator_handle": "creator",
                "session_profile": "chowdakr_sg_tiktok",
                "window_size": 29,
                "selection_count": 8,
                "window_cap": 30,
                "selected_count": 8,
                "completed_deep_capture_count": 8,
                "suggested_accounts_status_or_none": "not_visible",
            }
        ),
        encoding="utf-8",
    )
    journal = SourceCaptureActivityJournal(
        paths.activity_journal_jsonl_path,
        run_kind="creator_onboarding",
        platform="tiktok",
    )
    journal.close(
        status="complete",
        terminal_phase="close",
        error_type_or_none=None,
    )
    preflight_path = output_dir / runner.REGISTRY_PREFLIGHT_JSON_NAME
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            preflight_path,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(runner, "resolve_session_profile", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )
    monkeypatch.setattr(runner, "run_tiktok_creator_onboarding", lambda **_kwargs: paths)

    def fake_writer(**kwargs: object) -> tuple[int, str]:
        captured.update(kwargs)
        return 0, str((tmp_path / "admitted").resolve())

    monkeypatch.setattr(runner, "write_tiktok_batch_packet", fake_writer)
    bundle_path = tmp_path / "audience_bundle.json"
    prompt_path = tmp_path / "audience_prompt.txt"
    bundle_path.write_text("{}", encoding="utf-8")
    prompt_path.write_text("prompt", encoding="utf-8")
    audience_queue: dict[str, object] = {}

    def fake_prepare(**kwargs: object) -> dict[str, object]:
        audience_queue["prepare"] = kwargs
        return {"bundle_out": str(bundle_path), "prompt_out": str(prompt_path)}

    def fake_enqueue(**kwargs: object) -> dict[str, object]:
        audience_queue["enqueue"] = kwargs
        return {"status": "enqueued", "job_id": "audience_job_001"}

    monkeypatch.setattr(runner, "_packet_capture_time", lambda *_args: "2026-07-21T00:00:00Z")
    monkeypatch.setattr(runner, "prepare_onboarding", fake_prepare)
    monkeypatch.setattr(runner, "enqueue_creator_audience_job", fake_enqueue)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    monkeypatch.setattr(
        runner,
        "load_current_registry_preflight_view",
        lambda _root: {
            "creator_profile_current_view": {
                "schema_version": "creator_profile_current_view_registry_preflight_v1",
                "generated_at_utc": "2026-07-21T00:00:00Z",
                "profiles": [],
            }
        },
    )
    monkeypatch.setattr(
        runner,
        "_write_suggested_frontier",
        lambda **_kwargs: str(tmp_path / "frontier.json"),
    )

    code = runner.main(
        [
            "--creator-handle",
            "creator",
            "--output-dir",
            str(output_dir),
            "--data-root",
            str(tmp_path / "lake"),
        ]
    )

    assert code == 0
    assert captured["grid_window_json"] == paths.grid_window_json_path.read_bytes()
    assert captured["selection_result_json"] == paths.selection_json_path.read_bytes()
    assert (
        captured["suggested_accounts_json"]
        == paths.suggested_accounts_json_path.read_bytes()
    )
    assert (
        captured["activity_journal_jsonl"]
        == paths.activity_journal_jsonl_path.read_bytes()
    )
    assert [row["role"] for row in captured["source_file_receipts"]] == [
        "grid_result_json",
        "cadence_result_json_1",
        "grid_window_json",
        "selection_result_json",
        "suggested_accounts_json",
        "source_capture_activity_jsonl",
    ]
    assert audience_queue["prepare"]["packet_id"] == "admitted"
    assert audience_queue["enqueue"]["bundle_path"] == bundle_path
    assert audience_queue["enqueue"]["prompt_path"] == prompt_path
    assert lake.root_uuid


def test_onboarding_cli_reuses_valid_prior_capture_without_deep_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_dir = tmp_path / "staging"
    output_dir.mkdir()
    paths = onboarding.TikTokCreatorProfileRefreshOutputPaths(
        grid_window_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        onboarding_receipt_json_path=output_dir
        / onboarding.TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
    )
    paths.grid_window_json_path.write_text('{"grid":"profile"}', encoding="utf-8")
    paths.onboarding_receipt_json_path.write_text(
        json.dumps(
            {
                "status": "complete",
                "capture_scope": "profile_refresh",
                "creator_handle": "creator",
                "session_profile": "chowdakr_sg_tiktok",
                "window_size": 1,
                "selection_count": 0,
                "window_cap": 30,
                "selected_count": 0,
                "completed_deep_capture_count": 0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            output_dir / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {"action_status": "allowed"},
        ),
    )
    monkeypatch.setattr(
        runner,
        "_validate_reusable_prior_capture",
        lambda **_kwargs: {
            "packet_id": "01PRIOR",
            "nonblank_top_level_comment_count": 148,
            "nonblank_transcript_cue_count": 361,
        },
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": True},
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_onboarding",
        lambda **_kwargs: pytest.fail("deep capture must not run"),
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_profile_refresh",
        lambda **_kwargs: paths,
    )
    admitted: dict[str, object] = {}

    def fake_grid_writer(**kwargs: object) -> tuple[int, str]:
        admitted.update(kwargs)
        return 0, str(tmp_path / "profile-packet")

    monkeypatch.setattr(runner, "write_tiktok_grid_packet", fake_grid_writer)

    assert (
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--creator-intent",
                "update_existing",
                "--output-dir",
                str(output_dir),
                "--prior-capture-pointer",
                "01PRIOR",
                "--admit-output",
                str(tmp_path / "profile-packet"),
            ]
        )
        == 0
    )
    assert admitted["grid_window_json"] == paths.grid_window_json_path.read_bytes()
    assert admitted["prior_capture_pointer"] == "01PRIOR"
    summary_line = next(
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(runner.SUMMARY_PREFIX)
    )
    summary = json.loads(summary_line.removeprefix(runner.SUMMARY_PREFIX))
    assert summary["capture_scope"] == "profile_refresh"
    assert summary["completed_deep_capture_count"] == 0
    assert summary["prior_capture_pointer_or_none"] == "01PRIOR"
    assert summary["profile_refresh_packet_or_none"].endswith("profile-packet")


def test_onboarding_cli_rejects_invalid_reuse_before_browser_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probed = False
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )

    def invalid_prior(**_kwargs: object) -> dict[str, object]:
        raise ValueError("prior capture is not reusable")

    def probe(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal probed
        probed = True
        return {"browser_available": True}

    monkeypatch.setattr(runner, "_validate_reusable_prior_capture", invalid_prior)
    monkeypatch.setattr(runner, "probe_local_cdp_endpoints", probe)

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                str(tmp_path / "out"),
                "--prior-capture-pointer",
                "01INVALID",
            ]
        )
    assert exc_info.value.code == 2
    assert probed is False


def test_onboarding_cli_reports_exact_cdp_recovery_without_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )
    monkeypatch.setattr(
        runner, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        runner, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: {"browser_available": False},
    )
    monkeypatch.setattr(
        runner,
        "run_tiktok_creator_onboarding",
        lambda **_kwargs: pytest.fail("capture must not run"),
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "creator",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    assert exc_info.value.code == 2
    assert runner.BLOCKER_PREFIX + json.dumps(
        {
            "code": "CDP_SESSION_UNAVAILABLE",
            "phase": "browser_preflight",
            "recovery": runner.CDP_RECOVERY,
        },
        sort_keys=True,
    ) in capsys.readouterr().out.splitlines()


@pytest.mark.parametrize(
    ("creator_handle", "captured_comment_count", "subtitle_cue_count", "error"),
    [
        ("other", 1, 1, "creator_handle does not match"),
        ("creator", 0, 1, "at least one captured comment"),
        ("creator", 1, 0, "at least one captured comment"),
    ],
)
def test_prior_capture_reuse_validation_fails_closed_on_wrong_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    creator_handle: str,
    captured_comment_count: int,
    subtitle_cue_count: int,
    error: str,
) -> None:
    monkeypatch.setattr(
        runner,
        "build_tiktok_batch_coverage_from_packet_directory",
        lambda _path: {
            "source_surface": runner.TIKTOK_BATCH_CAPTURE_SURFACE,
            "packet_id": "01PRIOR",
            "creator_handle": creator_handle,
            "coverage_rollup": {
                "nonblank_top_level_comment_count": captured_comment_count,
                "nonblank_transcript_cue_count": subtitle_cue_count,
            },
        },
    )

    with pytest.raises(ValueError, match=error):
        runner._validate_reusable_prior_capture(
            prior_capture_pointer=str(tmp_path / "prior"),
            creator_handle="creator",
            data_root=None,
        )


def test_prior_capture_reuse_validation_rejects_tombstone_before_packet_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TombstonedRoot:
        @staticmethod
        def tombstoned_packet_ids() -> set[str]:
            return {"01PRIOR"}

    monkeypatch.setattr(
        runner,
        "build_tiktok_batch_coverage_from_lake",
        lambda *_args: pytest.fail("tombstoned packet must not be read"),
    )

    with pytest.raises(ValueError, match="prior capture packet is tombstoned"):
        runner._validate_reusable_prior_capture(
            prior_capture_pointer="01PRIOR",
            creator_handle="creator",
            data_root=TombstonedRoot(),
        )


def test_profile_refresh_uses_only_profile_grid_and_writes_zero_deep_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    grid = _capture(
        ordered_ids=["1"],
        items=[_item("1", 300, 30)],
    )
    grid.dom_observation["profile_bio_text_or_none"] = "Exact bio"
    grid.dom_observation["profile_bio_element_detected"] = True
    engine = _FakeEngine([grid, grid, grid])

    paths = onboarding.run_tiktok_creator_profile_refresh(
        creator_handle="creator",
        session_profile=_profile(),
        output_dir=tmp_path,
        auth_state_root=tmp_path,
        window_size=27,
        engine=engine,
    )

    assert len(engine.calls) == 3
    assert {
        call["url"] for call in engine.calls
    } == {"https://www.tiktok.com/@creator"}
    assert all("/video/" not in str(call["url"]) for call in engine.calls)
    grid_window = json.loads(
        paths.grid_window_json_path.read_text(encoding="utf-8")
    )
    receipt = json.loads(
        paths.onboarding_receipt_json_path.read_text(encoding="utf-8")
    )
    assert grid_window["profile_bio_text_or_none"] == "Exact bio"
    assert receipt["capture_scope"] == "profile_refresh"
    assert receipt["selection_count"] == 0
    assert receipt["completed_deep_capture_count"] == 0


def test_grid_window_preserves_exact_profile_bio() -> None:
    capture = _capture(
        ordered_ids=["1"],
        items=[_item("1", 300, 30)],
    )
    capture.dom_observation["profile_bio_text_or_none"] = "  Exact bio 🇬🇧  "
    capture.dom_observation["profile_bio_element_detected"] = True

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=1,
    )

    assert window["profile_bio_text_or_none"] == "Exact bio 🇬🇧"
    assert window["profile_bio_status"] == "observed"


def test_grid_window_accepts_available_rows_below_cap() -> None:
    capture = _capture(
        ordered_ids=["1", "2", "3"],
        items=[
            _item("1", 300, 30),
            _item("2", 200, 20),
            _item("3", 100, 10),
        ],
    )

    window = build_tiktok_grid_window(
        creator_handle="creator",
        capture=capture,
        window_size=4,
        minimum_window_size=2,
    )

    assert window["window_size"] == 3
    assert window["window_cap"] == 4
    assert [item["video_id"] for item in window["items"]] == ["1", "2", "3"]


def test_suggested_receipt_preserves_profile_bio_and_clean_external_links() -> None:
    capture = _capture(suggested=[])
    capture.dom_observation["profile_bio_text_or_none"] = (
        "  Honest reviews • hidden gems 🇬🇧\nFragrance for less  "
    )
    capture.dom_observation["profile_bio_element_detected"] = True
    capture.dom_observation["profile_external_links"] = [
        {
            "url": "https://beacons.ai/topfrag",
            "host": "beacons.ai",
            "display_text_or_none": "My links",
        }
    ]

    receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=capture
    )

    assert receipt["profile_bio_status"] == "captured"
    assert receipt["profile_bio_text_or_none"] == (
        "Honest reviews • hidden gems 🇬🇧\nFragrance for less"
    )
    assert receipt["profile_external_links_status"] == "captured"
    assert receipt["profile_external_links"] == [
        {
            "url": "https://beacons.ai/topfrag",
            "host": "beacons.ai",
            "display_text_or_none": "My links",
        }
    ]
    assert receipt["outer_ui_route"] == "followers_dialog_suggested_tab"
    assert receipt["candidate_profiles_opened"] == 0
    assert receipt["account_mutations_taken"] == 0
    assert "internal CloakBrowser humanized pointer path" in receipt[
        "attempt_receipt"
    ]["outer_move_steps_semantics"]


def test_grid_profile_contract_finds_dom_hub_and_hydration_bio_link() -> None:
    script = onboarding.TIKTOK_PROFILE_GRID_DOM_EXTRACT_SCRIPT

    assert 'a[data-e2e="user-link"][href]' in script
    assert "bioLink.link || bioLink.url" in script
    assert "profile_hydration" in script
    assert "redirect_url" in script
    assert "linktr.ee" in script
    assert "link.me" in script


def test_grid_profile_hub_evidence_upgrades_suggested_receipt() -> None:
    suggested_receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator",
        capture=_capture(suggested=[]),
    )
    grid_capture = _capture(ordered_ids=["1"], items=[_item("1", 10, 1)])
    grid_capture.dom_observation["profile_external_links"] = [
        {
            "url": "https://linktr.ee/creator",
            "host": "linktr.ee",
            "display_text_or_none": "My links",
            "detection_source": "profile_hydration",
        }
    ]

    onboarding._merge_grid_profile_external_links(
        suggested_receipt=suggested_receipt,
        grid_capture=grid_capture,
    )

    assert suggested_receipt["profile_external_links_status"] == "captured"
    assert suggested_receipt["profile_external_links"] == [
        {
            "url": "https://linktr.ee/creator",
            "host": "linktr.ee",
            "display_text_or_none": "My links",
            "detection_source": "profile_hydration",
        }
    ]


def test_link_hub_direct_http_captures_json_ld_and_anchor_social_links(
    tmp_path: Path,
) -> None:
    body = b"""
    <html>
      <script type="application/ld+json">
        {"@type":"ProfilePage","sameAs":["https://www.instagram.com/creator/"]}
      </script>
      <a href="https://www.youtube.com/@creator?sub_confirmation=1">YouTube</a>
    </html>
    """

    def fetch(**kwargs: object) -> onboarding.DirectHttpCaptureSuccess:
        assert kwargs["url"] == "https://linktr.ee/creator"
        assert kwargs["max_bytes"] == onboarding.TIKTOK_LINK_HUB_CAPTURE_MAX_BYTES
        return onboarding.DirectHttpCaptureSuccess(
            requested_url=str(kwargs["url"]),
            final_url=str(kwargs["url"]),
            status=200,
            reason="OK",
            metadata={},
            body=body,
            warning_notes=[],
            limitation_notes=[],
        )

    observation = onboarding.capture_tiktok_profile_link_hub_observation(
        link_hub_url="https://linktr.ee/creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=_FakeEngine([]),
        fetch_fn=fetch,
        utc_now_fn=lambda: datetime(2026, 7, 23, tzinfo=UTC),
    )

    assert observation["status"] == "captured"
    assert observation["capture_method_or_none"] == "direct_http"
    assert observation["browser_fallback_attempt_or_none"] is None
    assert observation["outbound_social_links"] == [
        {
            "platform": "youtube",
            "url": "https://youtube.com/@creator",
            "source": "anchor",
        },
        {
            "platform": "instagram",
            "url": "https://instagram.com/creator/",
            "source": "json_ld_same_as",
        },
    ]
    assert observation["direct_http_attempt_or_none"]["body_sha256_or_none"].startswith(
        "sha256:"
    )


def test_link_hub_uses_temporary_browser_tab_when_http_has_no_social_links(
    tmp_path: Path,
) -> None:
    browser_capture = _capture()
    browser_capture = replace(
        browser_capture,
        requested_url="https://linktr.ee/creator",
        final_url="https://linktr.ee/creator",
        dom_observation={
            "anchors": [
                {"href": "https://www.tiktok.com/@creator"},
                {"href": "https://www.instagram.com/creator?igsh=tracking"},
            ],
            "json_ld_texts": [],
        },
    )

    class TemporaryEngine:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def capture_temporary_page_observation(
            self, **kwargs: object
        ) -> BrowserPageObservationSuccess:
            self.calls.append(dict(kwargs))
            return browser_capture

    engine = TemporaryEngine()

    observation = onboarding.capture_tiktok_profile_link_hub_observation(
        link_hub_url="https://linktr.ee/creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=engine,
        fetch_fn=lambda **_kwargs: onboarding.DirectHttpCaptureSuccess(
            requested_url="https://linktr.ee/creator",
            final_url="https://linktr.ee/creator",
            status=200,
            reason="OK",
            metadata={},
            body=b"<html><body>No server-rendered links</body></html>",
            warning_notes=[],
            limitation_notes=[],
        ),
    )

    assert observation["status"] == "captured"
    assert observation["capture_method_or_none"] == "browser_temporary_tab"
    assert observation["outbound_social_links"] == [
        {
            "platform": "tiktok",
            "url": "https://tiktok.com/@creator",
            "source": "anchor",
        },
        {
            "platform": "instagram",
            "url": "https://instagram.com/creator",
            "source": "anchor",
        },
    ]
    assert len(engine.calls) == 1
    assert engine.calls[0]["url"] == "https://linktr.ee/creator"


def test_link_hub_none_visible_performs_no_fetch(tmp_path: Path) -> None:
    fetched = False

    def fetch(**_kwargs: object) -> onboarding.DirectHttpCaptureResult:
        nonlocal fetched
        fetched = True
        raise AssertionError("none_visible must not fetch")

    observation = onboarding.capture_tiktok_profile_link_hub_observation(
        link_hub_url=None,
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10,
        settle_seconds=0,
        engine=_FakeEngine([]),
        fetch_fn=fetch,
    )

    assert observation["status"] == "none_visible"
    assert fetched is False


def test_tiktok_redirect_wrapper_normalizes_to_link_hub() -> None:
    wrapped = (
        "https://www.tiktok.com/link/v2?"
        "target=https%3A%2F%2Flinktr.ee%2Fcreator%3Futm_source%3Dtiktok"
    )

    assert onboarding._canonical_link_hub_url(wrapped) == (
        "https://linktr.ee/creator"
    )
    assert onboarding._canonical_link_hub_url("Link.me/SophieSnowScents") == (
        "https://link.me/SophieSnowScents"
    )


def test_suggested_dom_contract_targets_the_profile_surface_only() -> None:
    script = onboarding.TIKTOK_SUGGESTED_ACCOUNTS_DOM_EXTRACT_SCRIPT

    assert "exactSuggestedNodes" in script
    assert "text.includes('following')" in script
    assert "text.includes('followers')" in script
    assert "profileAnchors" in script
    assert "followers_dialog_suggested_tab" in script
    assert "suggested accounts" in (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_FALLBACK_DOM_EXTRACT_SCRIPT.lower()
    )
    assert '[data-e2e="user-bio"]' in script
    assert '[data-e2e="user-bio"]' in (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_FALLBACK_DOM_EXTRACT_SCRIPT
    )
    assert (
        onboarding.TIKTOK_FOLLOWERS_ACTION.action_name
        == "tiktok_creator_followers_count_v0"
    )
    assert (
        onboarding.TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION.action_name
        == "tiktok_relationship_dialog_suggested_tab_v0"
    )
    assert onboarding.TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION.text_markers == ()
    assert (
        onboarding.TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION.exact_text_markers
        == ("suggested",)
    )
    assert "[role='dialog'] *" in (
        onboarding.TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION.candidate_selector
    )
    assert "[aria-modal='true'] *" in (
        onboarding.TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION.candidate_selector
    )
    assert onboarding.TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION.text_markers == (
        "close",
    )
    assert onboarding.TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION.exact_text_markers == (
        "close",
        "x",
        "×",
    )
    assert "follow-popup-close" in (
        onboarding.TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION.candidate_selector
    )
    assert onboarding.TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION.visual_top_right_x_fallback is False
    assert (
        onboarding.TIKTOK_SUGGESTED_VIEW_ALL_ACTION.exact_text_markers
        == ("view all",)
    )
    assert (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.action_name
        == "tiktok_suggested_accounts_collapse_before_grid_v0"
    )
    assert (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.exact_text_markers
        == ("suggested accounts",)
    )
    assert (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.text_markers == ()
    )
    assert "show-suggested-accounts" in (
        onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.candidate_selector
    )
    assert onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.visual_top_right_x_fallback is False
    assert onboarding.TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION.visual_x_geometric_fallback is False
    assert "suggested_modal_open" in (
        onboarding.TIKTOK_SUGGESTED_SURFACE_CLOSED_DOM_EXTRACT_SCRIPT
    )
    assert "suggested_accounts_expanded" in (
        onboarding.TIKTOK_SUGGESTED_SURFACE_CLOSED_DOM_EXTRACT_SCRIPT
    )
    assert "body_scroll_locked" in (
        onboarding.TIKTOK_SUGGESTED_SURFACE_CLOSED_DOM_EXTRACT_SCRIPT
    )


def _clicked_capture(
    video_id: str, *, overlay_ready: bool = True
) -> BrowserPageObservationSuccess:
    capture = _capture()
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": overlay_ready,
            "visible_video_element_count": 1 if overlay_ready else 0,
            "overlay_video_id_or_none": video_id if overlay_ready else None,
            "overlay_creator_handle_or_none": "creator" if overlay_ready else None,
        }
    )
    object.__setattr__(
        capture,
        "final_url",
        f"https://www.tiktok.com/@creator/video/{video_id}",
    )
    capture.metadata["post_load_pointer_actions"] = [
        {
            "action_name": "tiktok_visible_selected_grid_video_v0",
            "target_found": True,
            "clicked": True,
            "target_variant": "media_link_surface",
            "move_steps": 8,
        }
    ]
    return capture


def _closed_overlay_capture(*video_ids: str) -> BrowserPageObservationSuccess:
    capture = _visible_tiles_capture(*video_ids)
    capture.metadata["post_load_pointer_actions"] = [
        {
            "action_name": "tiktok_video_overlay_close_v0",
            "target_found": True,
            "clicked": True,
            "move_steps": 6,
        }
    ]
    return capture


def _grid_overlay_receipt() -> dict[str, object]:
    return {
        "policy": "all_selected_via_visible_grid_tile_overlay_with_bounded_pagination",
        "deep_capture_route": "grid_tile_overlay",
        "direct_video_navigation_count": 0,
        "targeted_tile_scroll_performed": False,
        "grid_pagination_allowed": True,
        "grid_pagination_input_method": (
            "cloakbrowser.human.scroll_to_element"
        ),
        "logical_grid_positions_remembered": True,
        "absolute_pixel_positions_cached": False,
        "tile_click_target_policy": (
            "randomized_exact_video_media_link_or_view_count_footer"
        ),
        "hover_preview_body_click_allowed": False,
        "click_target_safe_inset_fraction": 0.15,
        "grid_pagination_pass_cap_per_lookup": 2,
        "grid_pagination_total_pass_cap": 2,
        "grid_pagination_passes_executed": 0,
        "grid_pagination_passes": [],
        "grid_pagination_stop_reason": None,
        "frozen_window_identity_drift_detected": False,
        "frozen_window_live_overlap_count_at_stop_or_none": None,
        "loaded_grid_video_count_at_stop_or_none": None,
        "attempts": [],
        "retry_waits": [],
        "status": "in_progress",
    }


def _grid_overlay_sequence(
    *,
    tmp_path: Path,
    engine: _FakeEngine,
    receipt: dict[str, object],
    sleep_fn=lambda _seconds: None,
    monotonic_fn=lambda: 0.0,
    pagination_pass_cap: int = 2,
    selected_grid_position: int = 1,
    rng: object | None = None,
    profile_grid_subtitle_sources_by_video_id: dict[str, dict[str, object]] | None = None,
) -> object:
    if rng is None:
        rng = type(
            "FirstChoice",
            (),
            {
                "choice": lambda _self, rows: rows[0],
                "randint": lambda _self, _low, _high: 55_000,
            },
        )()
    return onboarding._GridOverlayCaptureSequence(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        selected_video_ids=["1"],
        window_by_id={
            "1": {
                "video_id": "1",
                "video_url": "https://www.tiktok.com/@creator/video/1",
                "visible_in_viewport": True,
                "grid_position": selected_grid_position,
                "views": 400,
                "likes": 20,
            }
        },
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        pagination_pass_cap=pagination_pass_cap,
        engine=engine,
        rng=rng,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
        utc_now_fn=lambda: datetime(2026, 7, 14, 10, 0, tzinfo=UTC),
        receipt=receipt,
        profile_grid_subtitle_sources_by_video_id=(
            profile_grid_subtitle_sources_by_video_id
        ),
    )


def _visible_tiles_capture(
    *video_ids: str,
    visible_min: int | None = 1,
    visible_max: int | None = 3,
    scroll_y: int = 0,
    document_height: int | None = None,
    loaded_ids: tuple[str, ...] | None = None,
) -> BrowserPageObservationSuccess:
    capture = _capture()
    capture.dom_observation["visible_selected_tiles"] = [
        {
            "video_id": video_id,
            "video_url": f"https://www.tiktok.com/@creator/video/{video_id}",
            "grid_position": index,
            "click_target_kind": "link_routed_exact_video_semantic_targets",
            "click_target_text_or_none": "31.8K",
            "click_target_visible_in_viewport": True,
        }
        for index, video_id in enumerate(video_ids, start=1)
    ]
    capture.dom_observation["visible_grid_position_min_or_none"] = visible_min
    capture.dom_observation["visible_grid_position_max_or_none"] = visible_max
    capture.dom_observation["scroll_y"] = scroll_y
    capture.dom_observation["document_height"] = document_height
    if loaded_ids is not None:
        capture.dom_observation["loaded_grid_video_ids"] = list(loaded_ids)
    return capture


def test_failed_run_receipt_separates_overlay_capture_from_deep_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        onboarding,
        "validate_auth_state_provenance_requirement",
        lambda *_args, **_kwargs: state_path,
    )
    engine = _FakeEngine(
        [
            _capture(suggested=[]),
            _suggested_surface_closed_capture(),
                *_stable_grid_capture_sequence(
                    _capture(
                        ordered_ids=[str(video_id) for video_id in range(1, 28)],
                        items=[
                            _item(str(video_id), 1_000 - video_id, 1)
                            for video_id in range(1, 28)
                        ],
                    )
                ),
            _visible_tiles_capture("1"),
            _clicked_capture("1"),
        ]
    )

    def fail_after_first_overlay(**kwargs: object) -> dict[str, object]:
        sequence = kwargs["page_capture_sequence_fn"]
        sequence(0, kwargs["video_urls"])
        raise RuntimeError("deep capture interrupted after first overlay")

    with pytest.raises(RuntimeError, match="deep capture interrupted"):
        _run_onboarding(
            tmp_path,
            engine,
            selection_count=2,
            deep_capture_fn=fail_after_first_overlay,
            cadence_min_gap_seconds=0,
            cadence_max_gap_seconds=0,
            random_seed=7,
            sleep_fn=lambda _seconds: None,
        )

    receipt = json.loads(
        (tmp_path / TIKTOK_ONBOARDING_RECEIPT_JSON_NAME).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "failed"
    assert receipt["selected_video_ids_in_capture_order"] == ["1"]
    assert receipt["completed_grid_overlay_capture_count"] == 1
    assert receipt["completed_deep_capture_count"] == 0
    assert receipt["completed_deep_capture_count_source"] == "no_cadence_result"


def test_suggested_receipt_distinguishes_visible_empty_from_not_visible() -> None:
    visible = _capture(suggested=[])
    visible.dom_observation.update(
        {
            "suggested_surface_detected": True,
            "suggested_surface_root_count": 1,
            "suggested_profile_anchor_count": 0,
        }
    )
    not_visible = _capture(suggested=[])
    not_visible.dom_observation.update(
        {
            "suggested_surface_detected": False,
            "suggested_surface_root_count": 0,
            "relationship_dialog_detected": False,
            "suggested_tab_detected": False,
        }
    )

    visible_receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=visible
    )
    not_visible_receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=not_visible
    )

    assert visible_receipt["status"] == "visible_empty"
    assert visible_receipt["suggested_surface_root_count"] == 1
    assert not_visible_receipt["status"] == "not_visible"


def test_suggested_receipt_distinguishes_empty_bio_from_missing_bio() -> None:
    empty_bio = _capture(suggested=[])
    empty_bio.dom_observation.update(
        {
            "profile_bio_text_or_none": None,
            "profile_bio_element_detected": True,
        }
    )
    missing_bio = _capture(suggested=[])

    empty_receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=empty_bio
    )
    missing_receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=missing_bio
    )

    assert empty_receipt["profile_bio_text_or_none"] is None
    assert empty_receipt["profile_bio_status"] == "visible_empty"
    assert missing_receipt["profile_bio_text_or_none"] is None
    assert missing_receipt["profile_bio_status"] == "not_visible"


def test_suggested_capture_uses_profile_view_all_only_after_primary_not_visible(
    tmp_path: Path,
) -> None:
    primary_not_visible = _capture()
    primary_not_visible.dom_observation.update(
        {
            "profile_bio_text_or_none": "Profile bio from the primary route",
            "profile_bio_element_detected": True,
        }
    )
    fallback_captured = _capture(
        suggested=[
            {
                "handle": "fallback_creator",
                "profile_url": "https://www.tiktok.com/@fallback_creator",
            }
        ],
    )
    engine = _FakeEngine([primary_not_visible, fallback_captured])

    result = onboarding._capture_suggested_accounts(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        engine=engine,
    )

    assert isinstance(result, BrowserPageObservationSuccess)
    assert len(engine.calls) == 2
    assert [
        action.action_name for action in engine.calls[0]["post_load_pointer_actions"]
    ] == [
        "tiktok_creator_followers_count_v0",
        "tiktok_relationship_dialog_suggested_tab_v0",
    ]
    assert [
        action.action_name for action in engine.calls[1]["post_load_pointer_actions"]
    ] == [
        "tiktok_relationship_dialog_close_v0",
        "tiktok_suggested_accounts_view_all_v0",
    ]
    assert result.metadata["suggested_outer_ui_route"] == (
        "profile_suggested_accounts_view_all_fallback"
    )
    assert result.dom_observation["profile_bio_text_or_none"] == (
        "Profile bio from the primary route"
    )
    assert result.dom_observation["profile_bio_element_detected"] is True


def test_primary_bio_absence_does_not_overwrite_observed_fallback_bio(
    tmp_path: Path,
) -> None:
    primary_bio_absent = _capture()
    primary_bio_absent.dom_observation.update(
        {
            "profile_bio_text_or_none": None,
            "profile_bio_element_detected": True,
        }
    )
    fallback_bio_observed = _capture(
        suggested=[
            {
                "handle": "fallback_creator",
                "profile_url": "https://www.tiktok.com/@fallback_creator",
            }
        ],
    )
    fallback_bio_observed.dom_observation.update(
        {
            "profile_bio_text_or_none": "Budget fragrance reviews | daily uploads",
            "profile_bio_element_detected": True,
        }
    )
    engine = _FakeEngine([primary_bio_absent, fallback_bio_observed])

    result = onboarding._capture_suggested_accounts(
        profile_url="https://www.tiktok.com/@creator",
        creator_handle="creator",
        storage_state_path=tmp_path / "state.json",
        timeout_seconds=10.0,
        settle_seconds=0.0,
        engine=engine,
    )

    assert isinstance(result, BrowserPageObservationSuccess)
    receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator", capture=result
    )
    assert receipt["profile_bio_text_or_none"] == (
        "Budget fragrance reviews | daily uploads"
    )
    assert receipt["profile_bio_status"] == "captured"
    assert [row["handle"] for row in receipt["suggested_accounts"]] == [
        "fallback_creator"
    ]


def test_suggested_frontier_write_anchors_to_admitted_bronze_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suggested_path = tmp_path / "suggested.json"
    suggested_path.write_text(
        json.dumps(
            {
                "status": "captured",
                "creator_handle": "creator",
                "suggested_accounts": [
                    {
                        "handle": "freshfrag",
                        "profile_url": "https://www.tiktok.com/@freshfrag",
                        "display_text_or_none": "Fresh Frag",
                    }
                ],
                "profile_external_links": [
                    {"url": "https://linktr.ee/creator"}
                ],
                "outer_ui_route": "followers_dialog_suggested_tab_primary",
                "attempt_receipt": {
                    "capture_timestamp": "2026-07-14T10:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"frontier": "validated"}

    def fake_write(
        register: object,
        data_root: object,
        *,
        record_id: str,
    ) -> Path:
        captured["register"] = register
        captured["data_root"] = data_root
        captured["record_id"] = record_id
        path = tmp_path / "frontier.json"
        path.write_text("{}", encoding="utf-8")
        return path

    monkeypatch.setattr(
        runner, "build_tiktok_creator_discovery_frontier_register", fake_build
    )
    monkeypatch.setattr(
        runner, "write_tiktok_creator_discovery_frontier_register", fake_write
    )
    fake_root = object()
    admitted = Path("F:/forseti-data-lake/raw/abc/01KXPACKET")

    written = runner._write_suggested_frontier(
        creator_handle="@Creator",
        session_profile="chowdakr_sg_tiktok",
        suggested_receipt_path=suggested_path,
        admitted_path=admitted,
        data_root=fake_root,
    )

    assert written == str(tmp_path / "frontier.json")
    scan_receipt = captured["scan_receipt"]
    assert scan_receipt["parent_grid_packet_id_or_none"] == "01KXPACKET"
    assert scan_receipt["source_packet_id_or_none"] == "01KXPACKET"
    assert scan_receipt["link_hub_url_or_none"] == "https://linktr.ee/creator"
    assert captured["suggested_accounts"][0].handle == "freshfrag"
    assert captured["suggested_accounts"][0].observed_sections == (
        "followers_dialog_suggested_tab",
    )
    assert str(captured["prior_register_pointer"]).endswith(
        "/raw/04_tiktok_suggested_accounts_attempt.json"
    )

    monkeypatch.setattr(
        runner,
        "write_tiktok_creator_discovery_frontier_register",
        lambda *_args, **_kwargs: None,
    )
    with pytest.raises(RuntimeError, match="did not produce a frontier artifact"):
        runner._write_suggested_frontier(
            creator_handle="@Creator",
            session_profile="chowdakr_sg_tiktok",
            suggested_receipt_path=suggested_path,
            admitted_path=admitted,
            data_root=fake_root,
        )


@pytest.mark.parametrize(
    ("creator_intent", "expected_status", "expected_blocker"),
    [
        ("new_capture", "blocked", "new_capture_existing_match"),
        ("update_existing", "allowed", None),
        ("new_onboarding", "allowed", None),
    ],
)
def test_runner_registry_preflight_enforces_new_vs_existing_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    creator_intent: str,
    expected_status: str,
    expected_blocker: str | None,
) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    registry_document = {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_v0",
            "generated_at_utc": "2026-07-12T00:00:00Z",
            "counts": {"profiles_total": 1},
            "profiles": [
                {
                    "profile_subject_id": "creator_known_001",
                    "profile_subject_kind": "creator_record",
                    "onboarding": {
                        "onboarding_state": "not_onboarded",
                    },
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": "acct_tt_known_001",
                            "public_handle": "known_creator",
                            "public_profile_url": "https://www.tiktok.com/@known_creator",
                            "platform_public_account_id_or_none": None,
                            "public_display_name_or_none": "Known Creator",
                        }
                    ],
                }
            ],
        }
    }
    monkeypatch.setattr(
        runner, "load_creator_profile_current_view", lambda _path: registry_document
    )

    receipt_path, result = runner._write_creator_registry_preflight(
        creator_handle="known_creator",
        creator_intent=creator_intent,
        registry_path=registry_path,
        output_dir=tmp_path / "out",
    )

    assert receipt_path.is_file()
    assert result["decision"] == "existing_match"
    assert result["action_status"] == expected_status
    if expected_blocker is None:
        assert result["action_blockers"] == []
    else:
        assert expected_blocker in result["action_blockers"]
    assert result["registry_onboarding_state"] == "not_onboarded"


@pytest.mark.parametrize(
    ("creator_handle", "onboarding_state", "expected_message"),
    [
        (
            "known_creator",
            "onboarded",
            "new_onboarding requires onboarding_state=not_onboarded",
        ),
    ],
)
def test_new_onboarding_blocks_ineligible_creator_before_browser_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    creator_handle: str,
    onboarding_state: str,
    expected_message: str,
) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    registry_document = {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_v0",
            "generated_at_utc": "2026-07-12T00:00:00Z",
            "counts": {"profiles_total": 1},
            "profiles": [
                {
                    "profile_subject_id": "creator_known_001",
                    "profile_subject_kind": "creator_record",
                    "onboarding": {
                        "onboarding_state": onboarding_state,
                    },
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": "acct_tt_known_001",
                            "public_handle": "known_creator",
                            "public_profile_url": "https://www.tiktok.com/@known_creator",
                            "platform_public_account_id_or_none": None,
                            "public_display_name_or_none": "Known Creator",
                        }
                    ],
                }
            ],
        }
    }
    monkeypatch.setattr(
        runner, "load_creator_profile_current_view", lambda _path: registry_document
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: pytest.fail("browser probe must not run"),
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                creator_handle,
                "--creator-registry",
                str(registry_path),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )

    assert exc_info.value.code == 2
    assert expected_message in capsys.readouterr().err


def test_new_onboarding_queue_capacity_blocks_before_browser_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    registry_document = {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_registry_preflight_v1",
            "generated_at_utc": "2026-07-21T00:00:00Z",
            "profiles": [
                {
                    "profile_subject_id": "acct_tt_known_001",
                    "profile_subject_kind": "platform_account",
                    "onboarding": {"onboarding_state": "not_onboarded"},
                    "platform_accounts": [
                        {
                            "platform": "tiktok",
                            "platform_account_id": "acct_tt_known_001",
                            "public_handle": "known_creator",
                            "public_profile_url": "https://www.tiktok.com/@known_creator",
                        }
                    ],
                }
            ],
        }
    }
    monkeypatch.setattr(
        runner, "load_current_registry_preflight_view", lambda _root: registry_document
    )
    monkeypatch.setattr(
        runner, "load_tiktok_creator_discovery_frontier_registers", lambda _root: []
    )
    monkeypatch.setattr(
        runner, "load_creator_frontier_dispositions", lambda _root: None
    )
    monkeypatch.setattr(runner, "unfinished_profile_subject_ids", lambda _root: set())
    monkeypatch.setattr(
        runner,
        "_write_creator_registry_preflight",
        lambda **_kwargs: (
            tmp_path / runner.REGISTRY_PREFLIGHT_JSON_NAME,
            {
                "action_status": "allowed",
                "decision": "existing_match",
                "registry_onboarding_state": "not_onboarded",
            },
        ),
    )
    monkeypatch.setattr(
        runner,
        "assert_creator_audience_capacity",
        lambda _root: (_ for _ in ()).throw(
            runner.CreatorAudienceQueueError(
                "AUDIENCE_QUEUE_CAPACITY_REACHED: queued_plus_running=10 capacity=10"
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: pytest.fail("browser probe must not run"),
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "known_creator",
                "--output-dir",
                str(tmp_path / "out"),
                "--data-root",
                str(lake.path),
            ]
        )

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "AUDIENCE_QUEUE_CAPACITY_REACHED" in captured.out
    assert "queued_plus_running=10 capacity=10" in captured.err


def test_new_onboarding_rejects_genuinely_absent_account_before_browser_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    registry_document = {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_v0",
            "generated_at_utc": "2026-07-21T00:00:00Z",
            "profiles": [],
        }
    }
    monkeypatch.setattr(
        runner, "load_creator_profile_current_view", lambda _path: registry_document
    )
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda *_args, **_kwargs: pytest.fail("browser probe must not run"),
    )
    with pytest.raises(SystemExit) as exc_info:
        runner.main(
            [
                "--creator-handle",
                "missing_creator",
                "--creator-registry",
                str(registry_path),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    assert exc_info.value.code == 2
    assert "must be candidate-admitted first" in capsys.readouterr().err


def test_suggested_failure_receipt_carries_profile_evidence_failure_status() -> None:
    receipt = onboarding._build_suggested_accounts_receipt(
        creator_handle="creator",
        capture=BrowserSnapshotFailure(
            requested_url="https://www.tiktok.com/@creator",
            failure_kind=BrowserSnapshotFailureKind.TIMEOUT,
            message="timed out",
        ),
    )

    assert receipt["status"] == "failed"
    assert receipt["profile_bio_text_or_none"] is None
    assert receipt["profile_bio_status"] == "failed"
    assert receipt["profile_external_links"] == []
    assert receipt["profile_external_links_status"] == "failed"
