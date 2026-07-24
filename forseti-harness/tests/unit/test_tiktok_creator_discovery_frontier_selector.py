from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from capture_spine.tiktok_creator_discovery_frontier import (
    LinkHubOutcome,
    RefreshOutcome,
    ScanReceipt,
    SuggestedAccountObservation,
    build_tiktok_creator_discovery_frontier_register,
)
from capture_spine.tiktok_creator_discovery_frontier import frontier_selector
from capture_spine.tiktok_creator_discovery_frontier.frontier_selector import (
    apply_tiktok_creator_onboarding_dedupe,
    build_tiktok_creator_promotion_decisions,
    promotion_decision_for_handle,
    rank_tiktok_creator_discovery_targets,
    summarize_tiktok_creator_discovery_overlap,
)


def _scan_receipt(root_handle: str) -> dict:
    safe_root = root_handle.replace(".", "_")
    return ScanReceipt(
        receipt_id=f"receipt_{safe_root}",
        run_id=f"run_{safe_root}",
        register_id=f"register_{safe_root}",
        root_seed={
            "platform": "tiktok",
            "handle": root_handle,
            "url": f"https://www.tiktok.com/@{root_handle}",
        },
        source_surface="tiktok_profile_suggested_accounts_existing_cloakbrowser_cdp",
        captured_at_utc="2026-07-09T10:00:00Z",
        method_mode="existing_cloakbrowser_cdp_dom_extraction",
        access_mode="owner_authorized_existing_session_screen_light_dom_read",
        extraction_method="dom_visible_suggested_account_cards",
        browser_session_label_or_none="cloakbrowser_existing_chowdakr",
        parent_grid_packet_id_or_none="01KXROOTGRIDPACKET",
        parent_grid_packet_path_or_none="F:/orca-data-lake/raw/root/01KXROOTGRIDPACKET",
        source_packet_id_or_none="01KXSUGGESTEDPACKET",
        source_packet_path_or_none="F:/orca-data-lake/raw/suggested/01KXSUGGESTEDPACKET",
        parent_profile_capture_status="tiktok_parent_profile_grid_packet_available",
        suggested_accounts_capture_status="tiktok_suggested_accounts_packet_available",
        link_hub_capture_status=LinkHubOutcome.CAPTURED,
        link_hub_url_or_none=f"https://linktr.ee/{safe_root}",
        browser_closed_by_runner=False,
        refresh_attempt_count=0,
        refresh_outcome=RefreshOutcome.NOT_NEEDED,
        pagination_bound=1,
        suggested_accounts_observed=3,
        candidate_profiles_opened=0,
        follow_unfollow_actions_taken=0,
        screenshots_emitted_to_chat=0,
        caps_applied={
            "root_profiles": 1,
            "suggested_accounts_observed": 3,
            "candidate_profiles_opened": 0,
            "screenshots_emitted_to_chat": 0,
        },
        stop_reason="bounded_suggested_accounts_observation_complete",
        exclusions=(
            "no_candidate_profile_open",
            "no_follow_unfollow_action",
            "no_metric_rollup",
            "no_registry_mutation",
            "no_screenshot_chat_output",
        ),
    ).to_dict()


def _register(root_handle: str, *suggested_accounts: SuggestedAccountObservation) -> dict:
    return build_tiktok_creator_discovery_frontier_register(
        scan_receipt=_scan_receipt(root_handle),
        suggested_accounts=suggested_accounts,
        prior_register_pointer=f"docs/review-inputs/{root_handle}.json#/tiktok_creator_discovery_frontier_register",
        accepted_residuals=("selector test register",),
    )


def _suggested(
    handle: str,
    display_name: str | None = None,
    observed_sections: tuple[str, ...] = ("suggested_accounts",),
) -> SuggestedAccountObservation:
    return SuggestedAccountObservation(
        handle=handle,
        display_name_or_none=display_name,
        observed_sections=observed_sections,
    )



def test_promotion_policy_excludes_pins_and_routes_middle_to_oldest() -> None:
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    def grid(handle: str, plays: int, pinned: int | None = None) -> dict:
        items = [{"createTime": int(captured.timestamp() - age * 86400), "pinned_visible": False, "stats": {"playCount": plays}} for age in (16, 20, 25)]
        if pinned:
            items.append({"createTime": int(captured.timestamp() - 18 * 86400), "pinned_visible": True, "stats": {"playCount": pinned}})
        return {"creator_handle": handle, "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"}, "items": items}
    document = build_tiktok_creator_promotion_decisions([grid("strong", 300000), grid("middle", 60000), grid("low", 1000, 9000000)])
    rows = {row["handle"]: row for row in document["tiktok_creator_promotion_decisions"]["decisions"]}
    assert rows["strong"]["registry_action"] == "promote_now"
    assert rows["middle"]["registry_action"] == "promote_now"
    assert rows["middle"]["decision_reason_code"] == "cleared_quality_p25"
    assert rows["middle"]["cleared_thresholds"] == ["quality_p25"]
    assert rows["low"]["reconsider_when_or_none"] == "new_signal_only"
    assert rows["low"]["decision_reason_code"] == "below_both_p25"
    assert rows["low"]["cleared_thresholds"] == []
    assert "decision=do_not_promote" in rows["low"]["decision_note"]
    assert "reconsider=new_signal" in rows["low"]["decision_note"]
    assert rows["low"]["unpinned_post_count"] == 3
    assert promotion_decision_for_handle(document, "@STRONG")["registry_action"] == "promote_now"


def test_promotion_policy_emits_follower_observability_without_changing_action() -> None:
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    grid = {
        "creator_handle": "reachy",
        "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"},
        "profile_metrics": {
            "follower_count": {
                "exact_value_or_none": 50_000,
                "posture": "observed",
            },
        },
        "items": [
            {
                "createTime": int(captured.timestamp() - age * 86400),
                "pinned_visible": False,
                "stats": {"playCount": 300_000},
            }
            for age in (16, 20, 25)
        ],
    }

    document = build_tiktok_creator_promotion_decisions([grid])
    row = document["tiktok_creator_promotion_decisions"]["decisions"][0]

    assert row["registry_action"] == "promote_now"
    assert row["decision_reason_code"] == "cleared_both_p25"
    assert row["follower_count_or_none"] == 50_000
    assert row["follower_band"] == "50k_250k"
    assert row["reliable_weekly_reach_per_1k_followers_or_none"] == 9333.333333
    assert row["age_normalized_median_reach_per_follower_or_none"] == 6.0
    assert "followers=50000" in row["decision_note"]
    assert "follower_band=50k_250k" in row["decision_note"]
    assert "weekly_reach_per_1k_followers=9333.333333" in row["decision_note"]


def test_promotion_policy_missing_followers_are_unknown_and_nonblocking() -> None:
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    grid = {
        "creator_handle": "unknownfollowers",
        "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"},
        "profile_metrics": {
            "follower_count": {
                "exact_value_or_none": 0,
                "posture": "observed",
            },
        },
        "items": [
            {
                "createTime": int(captured.timestamp() - age * 86400),
                "pinned_visible": False,
                "stats": {"playCount": 300_000},
            }
            for age in (16, 20, 25)
        ],
    }

    document = build_tiktok_creator_promotion_decisions([grid])
    row = document["tiktok_creator_promotion_decisions"]["decisions"][0]

    assert row["registry_action"] == "promote_now"
    assert row["follower_count_or_none"] is None
    assert row["follower_band"] == "unknown"
    assert row["reliable_weekly_reach_per_1k_followers_or_none"] is None
    assert row["age_normalized_median_reach_per_follower_or_none"] is None
    assert "followers=unavailable" in row["decision_note"]
    assert "follower_band=unknown" in row["decision_note"]
    assert "weekly_reach_per_1k_followers=unavailable" in row["decision_note"]


@pytest.mark.parametrize(
    ("followers", "band"),
    [
        (9_999, "under_10k"),
        (10_000, "10k_50k"),
        (49_999, "10k_50k"),
        (50_000, "50k_250k"),
        (249_999, "50k_250k"),
        (250_000, "250k_plus"),
        (None, "unknown"),
    ],
)
def test_promotion_policy_follower_band_boundaries(
    followers: int | None, band: str
) -> None:
    assert frontier_selector._follower_band(followers) == band


@pytest.mark.parametrize(
    ("quality", "weekly", "action", "reason", "cleared"),
    [
        (
            4.713114,
            0.0,
            "promote_now",
            "cleared_quality_p25",
            ["quality_p25"],
        ),
        (
            0.0,
            186641.046627,
            "promote_now",
            "cleared_weekly_reach_p25",
            ["weekly_reach_p25"],
        ),
        (
            4.713114,
            186641.046627,
            "promote_now",
            "cleared_both_p25",
            ["quality_p25", "weekly_reach_p25"],
        ),
        (4.713113, 186641.046626, "do_not_promote", "below_both_p25", []),
        (
            None,
            186641.046626,
            "do_not_promote",
            "quality_unavailable_weekly_below_p25",
            [],
        ),
    ],
)
def test_promotion_policy_p25_boundaries_are_inclusive_and_compensatory(
    quality: float | None,
    weekly: float,
    action: str,
    reason: str,
    cleared: list[str],
) -> None:
    decision = frontier_selector._promotion_decision_fields(
        quality=quality,
        weekly_reach=weekly,
        followers=None,
        weekly_reach_per_1k_followers=None,
    )

    assert decision["registry_action"] == action
    assert decision["decision_reason_code"] == reason
    assert decision["cleared_thresholds"] == cleared
    assert "policy=tiktok_fragrance_creator_promotion_policy_v3" in decision["decision_note"]
    assert "quality_p25=4.71311400" in decision["decision_note"]
    assert "weekly_reach_p25=186641.046627" in decision["decision_note"]


def test_promotion_policy_v3_calibration_is_bound_to_admitted_cohort() -> None:
    path = Path(frontier_selector.__file__).with_name(
        "tiktok_fragrance_creator_promotion_policy_v3_calibration.json"
    )
    raw = path.read_bytes()
    calibration = json.loads(raw)
    cohort = calibration["cohort"]
    policy = frontier_selector._PROMOTION_POLICY

    assert hashlib.sha256(raw).hexdigest() == policy["calibration_report_sha256"]
    canonical_cohort = json.dumps(
        cohort,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    assert (
        hashlib.sha256(canonical_cohort).hexdigest()
        == policy["calibration_source_set_sha256"]
        == calibration["source_set_sha256"]
    )
    assert len(cohort) == policy["calibration_cohort_size"] == 9
    assert {row["handle"] for row in cohort}.isdisjoint({"fragrancekyle"})

    qualities = [row["quality"] for row in cohort]
    weekly_reaches = [row["reliable_weekly_reach"] for row in cohort]
    assert frontier_selector._percentile(qualities, .25) == policy["quality_p25"]
    assert (
        frontier_selector._percentile(weekly_reaches, .25)
        == policy["weekly_reach_p25"]
    )

    replay = {
        row["handle"]: frontier_selector._promotion_decision_fields(
            quality=row["quality"],
            weekly_reach=row["reliable_weekly_reach"],
            followers=row["follower_count"],
            weekly_reach_per_1k_followers=(
                row["reliable_weekly_reach"] / (row["follower_count"] / 1000)
            ),
        )["registry_action"]
        for row in cohort
    }
    assert sum(action == "promote_now" for action in replay.values()) == 8
    assert replay["zergggfragrance"] == "do_not_promote"
    assert (
        frontier_selector._promotion_decision_fields(
            quality=0.260564,
            weekly_reach=16556.044349,
            followers=14500,
            weekly_reach_per_1k_followers=1141.796162,
        )["registry_action"]
        == "do_not_promote"
    )


def test_onboarding_dedupe_preserves_performance_and_removes_known_or_scanned() -> None:
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    grids = [
        {
            "creator_handle": handle,
            "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"},
            "items": [
                {
                    "createTime": int(captured.timestamp() - age * 86400),
                    "pinned_visible": False,
                    "stats": {"playCount": 300000},
                }
                for age in (16, 20, 25)
            ],
        }
        for handle in ("done", "scanned", "known", "fresh", "eddeparfum")
    ]
    document = apply_tiktok_creator_onboarding_dedupe(
        build_tiktok_creator_promotion_decisions(grids),
        registry_states={"done": "onboarded", "known": "not_onboarded"},
        frontier_registers=[_register("scanned", _suggested("other"))],
    )
    wrapper = document["tiktok_creator_promotion_decisions"]
    rows = {row["handle"]: row for row in wrapper["decisions"]}

    assert wrapper["counts"]["promote_now"] == 5
    assert wrapper["counts"]["actionable_promote_now"] == 1
    assert wrapper["counts"]["owner_deferred_promote_now"] == 1
    assert wrapper["actionable_promote_now_handles"] == ["known"]
    assert rows["done"]["onboarding_queue_status"] == "already_onboarded"
    assert rows["scanned"]["onboarding_queue_status"] == "already_scanned_frontier"
    assert rows["known"]["actionable_promote_now"] is True
    assert rows["fresh"]["onboarding_queue_status"] == "new_candidate"
    assert rows["fresh"]["actionable_promote_now"] is False
    assert rows["eddeparfum"]["onboarding_queue_status"] == "owner_deferred"
    assert rows["eddeparfum"]["owner_onboarding_disposition_or_none"] == {
        "action": "defer",
        "reason": "owner_observed_non_us",
        "recorded_on": "2026-07-22",
    }
    assert rows["eddeparfum"]["actionable_promote_now"] is False


def test_onboarding_dedupe_routes_current_frontier_and_registry_states() -> None:
    captured = datetime(2026, 7, 21, 12, tzinfo=UTC)
    grids = [
        {
            "creator_handle": handle,
            "collection_receipt": {"capture_timestamp": "2026-07-21T12:00:00Z"},
            "items": [
                {
                    "createTime": int(captured.timestamp() - age * 86400),
                    "pinned_visible": False,
                    "stats": {"playCount": 300000},
                }
                for age in (16, 20, 25)
            ],
        }
        for handle in ("eligible_absent", "deferred_registered", "rejected_absent")
    ]
    dispositions = {
        "creator_frontier_disposition_current": {
            "schema_version": "creator_frontier_disposition_current_v1",
            "dispositions": [
                {"public_handle": "eligible_absent", "status": "eligible"},
                {"public_handle": "deferred_registered", "status": "deferred"},
                {"public_handle": "rejected_absent", "status": "rejected"},
            ],
        }
    }

    document = apply_tiktok_creator_onboarding_dedupe(
        build_tiktok_creator_promotion_decisions(grids),
        registry_states={"deferred_registered": "not_onboarded"},
        frontier_dispositions=dispositions,
    )
    rows = {
        row["handle"]: row
        for row in document["tiktok_creator_promotion_decisions"]["decisions"]
    }

    assert rows["eligible_absent"]["onboarding_queue_status"] == "frontier_eligible_not_registered"
    assert rows["deferred_registered"]["onboarding_queue_status"] == "owner_deferred"
    assert rows["rejected_absent"]["onboarding_queue_status"] == "owner_rejected"
    assert not any(row["actionable_promote_now"] for row in rows.values())

    counts = document["tiktok_creator_promotion_decisions"]["counts"]
    assert counts["promote_now"] == 3
    assert counts["actionable_promote_now"] == 0
    assert counts["owner_deferred_promote_now"] == 1
    assert counts["owner_rejected_promote_now"] == 1
    assert counts["frontier_eligible_not_registered_promote_now"] == 1


def test_target_ranker_prioritizes_once_only_expanded_fragrance_over_repeated_hub() -> None:
    registers = [
        _register(
            "rootone",
            _suggested(
                "smallfrag",
                "Small Fragrance Reviews",
                ("profile_suggested_view_all",),
            ),
            _suggested("hugehub", "Huge Scent Hub"),
        ),
        _register("roottwo", _suggested("hugehub", "Huge Scent Hub")),
        _register("rootthree", _suggested("hugehub", "Huge Scent Hub")),
    ]

    ranked = rank_tiktok_creator_discovery_targets(registers)

    assert ranked[0]["handle"] == "smallfrag"
    assert ranked[0]["recommendation_tier"] == "prioritize"
    assert ranked[0]["prior_suggested_frequency"] == 1
    assert ranked[0]["is_expanded_tail_observed"] is True
    assert ranked[-1]["handle"] == "hugehub"
    assert ranked[-1]["recommendation_tier"] == "deprioritize_repeated_hub"
    assert ranked[-1]["prior_suggested_frequency"] == 3


def test_target_ranker_excludes_already_scanned_roots_by_default() -> None:
    registers = [
        _register("alreadyroot", _suggested("freshfrag", "Fresh Frag")),
        _register("otherroot", _suggested("alreadyroot", "Already Root")),
    ]

    handles = [item["handle"] for item in rank_tiktok_creator_discovery_targets(registers)]

    assert "freshfrag" in handles
    assert "alreadyroot" not in handles


def test_target_ranker_excludes_caller_supplied_already_scanned_handles() -> None:
    registers = [
        _register("rootone", _suggested("freshfrag", "Fresh Frag"), _suggested("seenalready")),
    ]

    handles = [
        item["handle"]
        for item in rank_tiktok_creator_discovery_targets(
            registers, already_scanned_handles=("SeenAlready",)
        )
    ]

    assert "freshfrag" in handles
    assert "seenalready" not in handles


def test_overlap_summary_splits_repeated_once_and_new_tail_candidates() -> None:
    prior_registers = [
        _register("rootone", _suggested("repeat2"), _suggested("once_now"), _suggested("oldonly")),
        _register("roottwo", _suggested("repeat2"), _suggested("oldtwo")),
    ]
    current_register = _register(
        "currentroot",
        _suggested("repeat2"),
        _suggested("once_now"),
        _suggested("brandnew", observed_sections=("profile_suggested_view_all",)),
    )

    summary = summarize_tiktok_creator_discovery_overlap(
        prior_registers=prior_registers,
        current_register=current_register,
    )

    assert summary["current_root_handle"] == "currentroot"
    assert summary["current_candidate_count"] == 3
    assert summary["seen_before_count"] == 2
    assert summary["not_seen_before_count"] == 1
    assert summary["repeated_prior_2plus"] == ["repeat2"]
    assert summary["prior_once_now_repeated"] == ["once_now"]
    assert summary["brand_new_tail"] == ["brandnew"]
    assert "overlap summary is not capture authorization" in summary["non_claims"]
