from __future__ import annotations

import pytest

from reports.phase_a_acquisition_yield import (
    AcquisitionYieldReportError,
    render_phase_a_acquisition_yield,
)


def _fixture() -> tuple[dict, dict, list[dict]]:
    ledger = {
        "families": {
            "external_context": {
                "units": [
                    {
                        "unit_id": "editorial-1",
                        "origin_id": "publisher-1",
                        "independence": "independent_origin",
                        "relationship": "apparently_independent",
                        "source_type": "consumer_editorial",
                    }
                ]
            },
            "retailer_reviews": {
                "corpora": [
                    {"corpus_id": "retailer-a"},
                    {"corpus_id": "retailer-b"},
                ]
            },
            "reddit_forum": {
                "threads": [
                    {"thread_id": "t1", "community_id": "beauty"},
                ]
            },
            "native_social": {
                "posts": [
                    {
                        "unit_id": "social-1",
                        "creator_id": "creator-1",
                        "independence": "independent_post",
                        "relationship": "apparently_independent",
                    },
                    {
                        "unit_id": "owned-1",
                        "creator_id": "brand",
                        "independence": "independent_post",
                        "relationship": "owned",
                    },
                ]
            },
        },
        "product_axes": [
            {
                "axis_id": "packaging",
                "label": "Packaging",
                "polarity": "pain",
                "strength": "recurring",
                "disposition": "material",
                "decision_maturity": "decision_mature",
                "closure_basis": "evidence_supported",
                "claim_ceiling": "strong_qualitative",
                "decision_frontier_family_ids": ["family-a", "family-b"],
                "support_refs": [
                    {"family": "reddit_forum", "unit_id": "t1"},
                    {"family": "native_social", "unit_id": "social-1"},
                    {"family": "external_context", "unit_id": "editorial-1"},
                ],
                "retailer_incidence": [
                    {
                        "corpus_id": "retailer-a",
                        "eligible_text_review_count": 10,
                        "axis_mention_count": 2,
                        "negative_choice_review_count": 1,
                        "positive_choice_review_count": 0,
                    },
                    {
                        "corpus_id": "retailer-b",
                        "eligible_text_review_count": 20,
                        "axis_mention_count": 3,
                        "negative_choice_review_count": 1,
                        "positive_choice_review_count": 1,
                    },
                ],
            }
        ],
        "reddit_candidate_frontier": {
            "discovery_jobs": [
                {
                    "job_id": "A-1",
                    "axis_id": "packaging",
                    "query": "subject packaging",
                    "artifact_ids": ["serp-a"],
                    "candidate_thread_ids": ["t1", "t2"],
                    "surfaced_thread_ids": ["t1", "t2"],
                },
                {
                    "job_id": "B-1",
                    "axis_id": "packaging",
                    "query": "subject packaging alternative",
                    "artifact_ids": ["serp-b"],
                    "candidate_thread_ids": ["t3"],
                    "surfaced_thread_ids": ["t1", "t3"],
                },
            ],
            "query_families": [
                {
                    "family_id": "family-a",
                    "family_kind": "balanced_axis_baseline",
                    "family_role": "mandatory_high_yield",
                    "scope_axis_ids": ["packaging"],
                    "job_ids": ["A-1"],
                },
                {
                    "family_id": "family-b",
                    "family_kind": "late_counterevidence_test",
                    "family_role": "continuation",
                    "scope_axis_ids": ["packaging"],
                    "job_ids": ["B-1"],
                },
            ],
            "candidates": [
                {
                    "thread_id": "t1",
                    "discovered_by_job_id": "A-1",
                    "terminal_state": "captured_used",
                },
                {
                    "thread_id": "t2",
                    "discovered_by_job_id": "A-1",
                    "terminal_state": "dominated",
                    "reason": "title-only noise",
                },
                {
                    "thread_id": "t3",
                    "discovered_by_job_id": "B-1",
                    "terminal_state": "captured_excluded",
                    "reason": "native body had no axis evidence",
                },
            ],
        },
        "closure": {
            "batches": [
                {
                    "query_family_id": "family-a",
                    "new_usable_reddit_threads": 1,
                    "material_additions": [
                        {
                            "kind": "behavior_consequence",
                            "axis_ids": ["packaging"],
                        }
                    ],
                },
                {
                    "query_family_id": "family-b",
                    "new_usable_reddit_threads": 0,
                    "material_additions": [],
                },
            ]
        },
    }
    coding = {
        "parsed_comment_count": 12,
        "rows": [
            {
                "thread_id": "t1",
                "comment_id": "c1",
                "axis_ids": ["packaging"],
                "contribution": "compares",
                "explicit_outcome": "returned_or_refunded",
                "alternative_brand": "Alternative",
            }
        ],
    }
    rounds = [
        {
            "round_id": "A",
            "purpose": "Broad packaging discovery",
            "launch_reason": "Open packaging seam",
            "distinction": "Broad failure language",
            "job_ids": ["A-1"],
        },
        {
            "round_id": "B",
            "purpose": "Comparison check",
            "launch_reason": "Round A added usable evidence",
            "distinction": "Alternative and comparison language",
            "job_ids": ["B-1"],
        },
    ]
    return ledger, coding, rounds


def test_report_recomputes_yield_and_does_not_credit_search_only_rows() -> None:
    ledger, coding, rounds = _fixture()

    report = render_phase_a_acquisition_yield(
        ledger=ledger, community_coding=coding, search_rounds=rounds
    )

    assert "1/2 (50.0%)" in report
    assert "0/1 (0.0%)" in report
    assert "| B | Round A added usable evidence" in report
    assert "| B | Round A added usable evidence | Alternative and comparison language | family-b | 1 jobs / 1 axes | 2 | 1 | 0 | 0 | 1 | 0 | 1 | 0/1 (0.0%) | 0 |" in report
    assert "| B-1 | packaging | subject packaging alternative | Comparison check |" in report
    assert "returned_or_refunded 1" in report
    assert "Alternative" in report
    assert "Only structured material additions reopen an affected axis" in report
    assert "family-a: usable 1, material 1" in report
    assert "family-b: usable 0, material 0" in report


def test_report_counts_repeat_sighting_without_inflating_sources() -> None:
    ledger, coding, rounds = _fixture()

    report = render_phase_a_acquisition_yield(
        ledger=ledger, community_coding=coding, search_rounds=rounds
    )

    assert "| B | Round A added usable evidence | Alternative and comparison language | family-b | 1 jobs / 1 axes | 2 | 1 | 0 | 0 | 1 | 0 | 1 | 0/1 (0.0%) | 0 |" in report
    assert report.count("1/2 (50.0%)") == 1


def test_report_fails_when_round_membership_is_ambiguous() -> None:
    ledger, coding, rounds = _fixture()
    rounds[1]["job_ids"] = ["A-1"]

    with pytest.raises(
        AcquisitionYieldReportError,
        match="search jobs assigned to multiple rounds",
    ):
        render_phase_a_acquisition_yield(
            ledger=ledger, community_coding=coding, search_rounds=rounds
        )


def test_report_fails_when_a_discovery_job_is_missing_from_rounds() -> None:
    ledger, coding, rounds = _fixture()
    rounds = [rounds[0]]

    with pytest.raises(
        AcquisitionYieldReportError,
        match="discovery jobs missing from search rounds",
    ):
        render_phase_a_acquisition_yield(
            ledger=ledger, community_coding=coding, search_rounds=rounds
        )


def test_report_fails_when_a_query_family_spans_rounds() -> None:
    ledger, coding, rounds = _fixture()
    frontier = ledger["reddit_candidate_frontier"]
    frontier["discovery_jobs"].append(
        {
            "job_id": "A-2",
            "axis_id": "packaging",
            "query": "subject packaging leak",
            "artifact_ids": ["serp-a2"],
            "candidate_thread_ids": [],
            "surfaced_thread_ids": [],
        }
    )
    next(
        family
        for family in frontier["query_families"]
        if family["family_id"] == "family-a"
    )["job_ids"].append("A-2")
    rounds[1]["job_ids"].append("A-2")

    with pytest.raises(
        AcquisitionYieldReportError,
        match="query family split across search rounds",
    ):
        render_phase_a_acquisition_yield(
            ledger=ledger, community_coding=coding, search_rounds=rounds
        )


def test_report_fails_on_retailer_denominator_drift() -> None:
    ledger, coding, rounds = _fixture()
    second_axis = dict(ledger["product_axes"][0])
    second_axis["axis_id"] = "value"
    second_axis["label"] = "Value"
    second_axis["retailer_incidence"] = [
        {
            **row,
            "eligible_text_review_count": 11
            if row["corpus_id"] == "retailer-a"
            else row["eligible_text_review_count"],
        }
        for row in second_axis["retailer_incidence"]
    ]
    ledger["product_axes"].append(second_axis)

    with pytest.raises(AcquisitionYieldReportError, match="retailer denominator drift"):
        render_phase_a_acquisition_yield(
            ledger=ledger, community_coding=coding, search_rounds=rounds
        )


def test_report_does_not_trust_captured_used_without_coding() -> None:
    ledger, coding, rounds = _fixture()
    coding["rows"] = []

    with pytest.raises(
        AcquisitionYieldReportError,
        match="captured_used candidate has no community coding row",
    ):
        render_phase_a_acquisition_yield(
            ledger=ledger, community_coding=coding, search_rounds=rounds
        )


def test_report_observes_decision_frontier_without_sealing() -> None:
    ledger, coding, rounds = _fixture()
    ledger["reddit_candidate_frontier"]["candidates"] = []
    for job in ledger["reddit_candidate_frontier"]["discovery_jobs"]:
        job["candidate_thread_ids"] = []
        job["surfaced_thread_ids"] = []
    ledger["closure"]["batches"][0]["new_usable_reddit_threads"] = 0
    ledger["closure"]["batches"][0]["material_additions"] = []

    report = render_phase_a_acquisition_yield(
        ledger=ledger, community_coding=coding, search_rounds=rounds
    )

    assert "family-a: usable 0, material 0" in report
    assert "family-b: usable 0, material 0" in report
    assert "Decision-frontier observation" in report
    assert "validator still owns the completion decision" in report
