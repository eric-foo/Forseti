from __future__ import annotations

import json
from pathlib import Path

import pytest

from source_capture.reddit_thread_qualification import (
    RedditThreadQualificationFailure,
    build_reddit_thread_qualification,
)


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _content_packet(
    tmp_path: Path,
    *,
    slot_id: str,
    author: str,
    title: str,
    body: str,
    comments: list[dict[str, object]] | None = None,
) -> Path:
    packet = tmp_path / "packets" / slot_id
    _write_json(
        packet / "raw" / "01_content_record.json",
        {
            "record_kind": "reddit_thread_content_v0",
            "thread": {
                "thread_id": slot_id,
                "subreddit": "example",
                "title": title,
            },
            "post": {
                "author_state": author,
                "body_text": body,
                "score_state": "1",
            },
            "comments": comments or [],
            "counts": {
                "comments_parsed": len(comments or []),
                "observable_comment_nodes": len(comments or []),
            },
        },
    )
    return packet


def _selection_row(
    *,
    slot_id: str,
    title: str,
    comments: int,
    rank: int,
    subreddit: str = "example",
    score: int = 2,
) -> dict[str, object]:
    return {
        "slot_id": slot_id,
        "thread_url": f"https://old.reddit.com/r/{subreddit}/comments/{slot_id}/post/",
        "subreddit": subreddit,
        "title_or_none": title,
        "comments": comments,
        "score": score,
        "subreddit_rank_by_comments": rank,
        "subreddit_eligible_threads": 100,
    }


def _relevant_label(
    *,
    wedge_key: str,
    post_evidence: bool = True,
    evidence_comment_ids: list[str] | None = None,
    signal_kinds: list[str] | None = None,
    context_kinds: list[str] | None = None,
) -> dict[str, object]:
    return {
        "decision_relevant": True,
        "post_evidence": post_evidence,
        "wedge_key": wedge_key,
        "signal_kinds": signal_kinds or ["pain_failure"],
        "context_kinds": context_kinds or ["product"],
        "evidence_comment_ids": evidence_comment_ids or [],
    }


def test_qualification_enforces_engagement_corroboration_and_deduplication(
    tmp_path: Path,
) -> None:
    rows = [
        _selection_row(slot_id="low", title="Brand switch", comments=0, rank=97),
        _selection_row(slot_id="stack_a", title="Dryness after cream", comments=1, rank=90),
        _selection_row(slot_id="stack_b", title="Cream caused flaking", comments=2, rank=85),
        _selection_row(
            slot_id="crosspost_a",
            title="Same complaint",
            comments=1,
            rank=90,
            subreddit="one",
        ),
        _selection_row(
            slot_id="crosspost_b",
            title="Same complaint",
            comments=1,
            rank=91,
            subreddit="two",
        ),
        _selection_row(
            slot_id="same_author_a",
            title="First distinct report",
            comments=1,
            rank=92,
            subreddit="one",
        ),
        _selection_row(
            slot_id="same_author_b",
            title="Second distinct report",
            comments=1,
            rank=93,
            subreddit="two",
        ),
        _selection_row(slot_id="priority", title="Popular concern", comments=20, rank=60),
        _selection_row(
            slot_id="score_priority",
            title="Highly upvoted concern",
            comments=0,
            rank=99,
            score=30,
        ),
        _selection_row(slot_id="critical", title="Formula question", comments=8, rank=52),
        _selection_row(slot_id="excluded", title="Store scam", comments=30, rank=20),
        _selection_row(slot_id="unknown", title="Unlabelled", comments=30, rank=10),
        _selection_row(slot_id="gap", title="Failed capture", comments=30, rank=10),
    ]
    packets = {
        "low": _content_packet(
            tmp_path,
            slot_id="low",
            author="single_user",
            title="Brand switch",
            body="One person reports a different result after switching brands.",
        ),
        "stack_a": _content_packet(
            tmp_path,
            slot_id="stack_a",
            author="first_user",
            title="Dryness after cream",
            body="This cream caused persistent dryness after three applications.",
        ),
        "stack_b": _content_packet(
            tmp_path,
            slot_id="stack_b",
            author="second_user",
            title="Cream caused flaking",
            body="A separate user reports flaking from the same product family.",
        ),
        "crosspost_a": _content_packet(
            tmp_path,
            slot_id="crosspost_a",
            author="reposter",
            title="Same complaint",
            body="The exact same complaint was copied across several communities.",
        ),
        "crosspost_b": _content_packet(
            tmp_path,
            slot_id="crosspost_b",
            author="second_reposter",
            title="Same complaint",
            body="The exact same complaint was copied across several communities.",
        ),
        "same_author_a": _content_packet(
            tmp_path,
            slot_id="same_author_a",
            author="single_reposter",
            title="First distinct report",
            body="This report describes one failure mode in enough detail to be distinct.",
        ),
        "same_author_b": _content_packet(
            tmp_path,
            slot_id="same_author_b",
            author="single_reposter",
            title="Second distinct report",
            body="This separate text describes another incident but comes from the same person.",
        ),
        "priority": _content_packet(
            tmp_path,
            slot_id="priority",
            author="priority_user",
            title="Popular concern",
            body="This concern has strong thread-level engagement but no declared corroborator.",
        ),
        "score_priority": _content_packet(
            tmp_path,
            slot_id="score_priority",
            author="score_priority_user",
            title="Highly upvoted concern",
            body="This concern has strong post voting but no comments or corroboration.",
        ),
        "critical": _content_packet(
            tmp_path,
            slot_id="critical",
            author="critical_user",
            title="Formula question",
            body="The product appears to have the same formula under new packaging.",
            comments=[
                {
                    "comment_id": "corroborates",
                    "author_state": "independent_user",
                    "body_text": "I independently compared both ingredient lists and found the same formula.",
                    "score_state": "15 points",
                    "depth": 0,
                }
            ],
        ),
        "excluded": _content_packet(
            tmp_path,
            slot_id="excluded",
            author="excluded_user",
            title="Store scam",
            body="This is explicitly outside the bound product decision question.",
        ),
        "unknown": _content_packet(
            tmp_path,
            slot_id="unknown",
            author="unknown_user",
            title="Unlabelled",
            body="No operator relevance judgment was supplied for this thread.",
        ),
    }
    batch_results = [
        {
            "slot_id": row["slot_id"],
            "url": row["thread_url"],
            "capture_exit": 0 if row["slot_id"] != "gap" else 2,
            "packet_dir": (
                str(packets[row["slot_id"]])
                if row["slot_id"] in packets
                else None
            ),
        }
        for row in rows
    ]
    selection_path = _write_json(tmp_path / "selection.json", {"rows": rows})
    batch_path = _write_json(
        tmp_path / "batch.json",
        {"runner": "reddit_old_http_batch", "results": batch_results},
    )
    labels_path = _write_json(
        tmp_path / "labels.json",
        {
            "decision_question": "Which beauty problems merit weekly priority?",
            "threads": {
                "low": _relevant_label(wedge_key="brand_switch"),
                "stack_a": _relevant_label(wedge_key="cream_dryness"),
                "stack_b": _relevant_label(wedge_key="cream_dryness"),
                "crosspost_a": _relevant_label(wedge_key="copied_claim"),
                "crosspost_b": _relevant_label(wedge_key="copied_claim"),
                "same_author_a": _relevant_label(wedge_key="same_author_claim"),
                "same_author_b": _relevant_label(wedge_key="same_author_claim"),
                "priority": _relevant_label(wedge_key="popular_concern"),
                "score_priority": _relevant_label(
                    wedge_key="highly_upvoted_concern"
                ),
                "critical": _relevant_label(
                    wedge_key="same_formula",
                    evidence_comment_ids=["corroborates"],
                ),
                "excluded": {
                    "decision_relevant": False,
                    "exclusion_reason": "outside_bound_question",
                },
            },
        },
    )

    artifact = build_reddit_thread_qualification(
        selection_path=selection_path,
        batch_summary_path=batch_path,
        labels_path=labels_path,
    )["reddit_thread_qualification"]
    tiers = {row["slot_id"]: row["qualification_tier"] for row in artifact["threads"]}

    assert tiers == {
        "low": "low_lead",
        "stack_a": "stacked_emerging_signal",
        "stack_b": "stacked_emerging_signal",
        "crosspost_a": "low_lead",
        "crosspost_b": "low_lead",
        "same_author_a": "low_lead",
        "same_author_b": "low_lead",
        "priority": "priority_signal",
        "score_priority": "priority_signal",
        "critical": "critical_signal",
        "excluded": "excluded_not_decision_relevant",
        "unknown": "needs_judgment",
        "gap": "access_or_processing_gap",
    }
    copied = next(row for row in artifact["threads"] if row["slot_id"] == "crosspost_a")
    assert copied["wedge_evidence"] == {
        "thread_count": 2,
        "evidence_bearing_thread_count": 2,
        "unique_post_author_count": 2,
        "near_duplicate_content_cluster_count": 1,
        "independent_thread_source_count": 1,
        "independent_evidence_commenter_count": 0,
        "independent_evidence_source_count": 1,
        "is_resonant": False,
    }
    same_author = next(
        row for row in artifact["threads"] if row["slot_id"] == "same_author_a"
    )
    assert same_author["wedge_evidence"]["unique_post_author_count"] == 1
    assert same_author["wedge_evidence"]["near_duplicate_content_cluster_count"] == 2
    assert same_author["wedge_evidence"]["independent_thread_source_count"] == 1
    assert artifact["counts"]["capture_gap_count"] == 1


def test_qualification_rejects_nonexistent_evidence_comment(tmp_path: Path) -> None:
    row = _selection_row(slot_id="thread", title="Question", comments=1, rank=90)
    packet = _content_packet(
        tmp_path,
        slot_id="thread",
        author="poster",
        title="Question",
        body="A sufficiently detailed post body for the qualification test.",
    )
    selection = _write_json(tmp_path / "selection.json", {"rows": [row]})
    batch = _write_json(
        tmp_path / "batch.json",
        {
            "runner": "reddit_old_http_batch",
            "results": [
                {
                    "slot_id": "thread",
                    "url": row["thread_url"],
                    "capture_exit": 0,
                    "packet_dir": str(packet),
                }
            ],
        },
    )
    labels = _write_json(
        tmp_path / "labels.json",
        {
            "decision_question": "Bound question",
            "threads": {
                "thread": {
                    **_relevant_label(wedge_key="wedge"),
                    "evidence_comment_ids": ["missing"],
                }
            },
        },
    )

    with pytest.raises(
        RedditThreadQualificationFailure,
        match="missing or ineligible evidence comment",
    ):
        build_reddit_thread_qualification(
            selection_path=selection,
            batch_summary_path=batch,
            labels_path=labels,
        )


def test_question_only_post_does_not_count_as_independent_evidence(
    tmp_path: Path,
) -> None:
    row = _selection_row(slot_id="question", title="Does this last?", comments=3, rank=90)
    packet = _content_packet(
        tmp_path,
        slot_id="question",
        author="shopper",
        title="Does this last?",
        body="I have not used this palette and want to know whether it lasts all day.",
        comments=[
            {
                "comment_id": "one_experience",
                "author_state": "one_user",
                "body_text": "I used this palette for a week and it faded before lunchtime every day.",
                "score_state": "0 points",
                "depth": 0,
            }
        ],
    )
    selection = _write_json(tmp_path / "selection.json", {"rows": [row]})
    batch = _write_json(
        tmp_path / "batch.json",
        {
            "runner": "reddit_old_http_batch",
            "results": [
                {
                    "slot_id": "question",
                    "url": row["thread_url"],
                    "capture_exit": 0,
                    "packet_dir": str(packet),
                }
            ],
        },
    )
    labels = _write_json(
        tmp_path / "labels.json",
        {
            "decision_question": "Bound question",
            "threads": {
                "question": {
                    **_relevant_label(
                        wedge_key="palette_longevity",
                        post_evidence=False,
                        evidence_comment_ids=["one_experience"],
                    ),
                }
            },
        },
    )

    artifact = build_reddit_thread_qualification(
        selection_path=selection,
        batch_summary_path=batch,
        labels_path=labels,
    )["reddit_thread_qualification"]
    result = artifact["threads"][0]

    assert result["qualification_tier"] == "low_lead"
    assert result["wedge_evidence"]["evidence_bearing_thread_count"] == 0
    assert result["wedge_evidence"]["independent_thread_source_count"] == 0
    assert result["wedge_evidence"]["independent_evidence_source_count"] == 1


def test_resonance_is_bound_to_declared_evidence_source(tmp_path: Path) -> None:
    rows = [
        _selection_row(
            slot_id="popular_visual",
            title="Popular visual",
            comments=30,
            rank=80,
            score=600,
        ),
        _selection_row(
            slot_id="quiet_post_high_comment",
            title="What is this product like?",
            comments=1,
            rank=99,
            score=2,
        ),
    ]
    packets = {
        "popular_visual": _content_packet(
            tmp_path,
            slot_id="popular_visual",
            author="artist",
            title="Popular visual",
            body="A visual showcase without a textual product claim.",
            comments=[
                {
                    "comment_id": "buried_claim",
                    "author_state": "shopper",
                    "body_text": "The named polish chipped after one day on my nails.",
                    "score_state": "0 points",
                    "depth": 0,
                }
            ],
        ),
        "quiet_post_high_comment": _content_packet(
            tmp_path,
            slot_id="quiet_post_high_comment",
            author="questioner",
            title="What is this product like?",
            body="The poster asks a question and supplies no first-hand product evidence.",
            comments=[
                {
                    "comment_id": "high_point_claim",
                    "author_state": "experienced_user",
                    "body_text": "Davidoff Cool Water",
                    "score_state": "72 points",
                    "depth": 0,
                }
            ],
        ),
    }
    selection = _write_json(tmp_path / "selection.json", {"rows": rows})
    batch = _write_json(
        tmp_path / "batch.json",
        {
            "runner": "reddit_old_http_batch",
            "results": [
                {
                    "slot_id": row["slot_id"],
                    "url": row["thread_url"],
                    "capture_exit": 0,
                    "packet_dir": str(packets[row["slot_id"]]),
                }
                for row in rows
            ],
        },
    )
    labels = _write_json(
        tmp_path / "labels.json",
        {
            "decision_question": "Which concrete product experiences merit evidence?",
            "threads": {
                "popular_visual": _relevant_label(
                    wedge_key="polish_chipping",
                    post_evidence=False,
                    evidence_comment_ids=["buried_claim"],
                    signal_kinds=["pain_failure"],
                ),
                "quiet_post_high_comment": _relevant_label(
                    wedge_key="cool_water_positioning",
                    post_evidence=False,
                    evidence_comment_ids=["high_point_claim"],
                    signal_kinds=["praise_success", "comparison_choice"],
                    context_kinds=["brand", "product"],
                ),
            },
        },
    )

    artifact = build_reddit_thread_qualification(
        selection_path=selection,
        batch_summary_path=batch,
        labels_path=labels,
    )["reddit_thread_qualification"]
    by_slot = {row["slot_id"]: row for row in artifact["threads"]}

    assert by_slot["popular_visual"]["qualification_tier"] == "low_lead"
    assert by_slot["popular_visual"]["resonance"]["reasons"] == []
    assert (
        by_slot["quiet_post_high_comment"]["qualification_tier"]
        == "priority_signal"
    )
    assert by_slot["quiet_post_high_comment"]["resonance"]["reasons"] == [
        "evidence_comment_point_floor"
    ]
    assert by_slot["quiet_post_high_comment"]["evidence_comments"][
        "ids_by_points"
    ] == ["high_point_claim"]


def test_exclusion_requires_a_reason(tmp_path: Path) -> None:
    row = _selection_row(slot_id="thread", title="Visual only", comments=5, rank=80)
    packet = _content_packet(
        tmp_path,
        slot_id="thread",
        author="poster",
        title="Visual only",
        body="A visual-only post with no transferable claim in retained text.",
    )
    selection = _write_json(tmp_path / "selection.json", {"rows": [row]})
    batch = _write_json(
        tmp_path / "batch.json",
        {
            "runner": "reddit_old_http_batch",
            "results": [
                {
                    "slot_id": "thread",
                    "url": row["thread_url"],
                    "capture_exit": 0,
                    "packet_dir": str(packet),
                }
            ],
        },
    )
    labels = _write_json(
        tmp_path / "labels.json",
        {
            "decision_question": "Bound question",
            "threads": {"thread": {"decision_relevant": False}},
        },
    )

    with pytest.raises(
        RedditThreadQualificationFailure,
        match="must set one accepted exclusion_reason",
    ):
        build_reddit_thread_qualification(
            selection_path=selection,
            batch_summary_path=batch,
            labels_path=labels,
        )
