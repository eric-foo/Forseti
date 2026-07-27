from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


QUALIFICATION_SCHEMA_VERSION = "reddit_thread_qualification_v1"
RELATIVE_ENGAGEMENT_HEAD_FRACTION = 0.5
ABSOLUTE_COMMENT_RESONANCE_FLOOR = 15
ABSOLUTE_POST_SCORE_RESONANCE_FLOOR = 25
EVIDENCE_COMMENT_POINT_FLOOR = 5
NEAR_DUPLICATE_JACCARD_FLOOR = 0.9
SIGNAL_KINDS = {
    "pain_failure",
    "praise_success",
    "outcome_experience",
    "comparison_choice",
    "unmet_need",
}
CONTEXT_KINDS = {
    "brand",
    "product",
    "ingredient",
    "technique",
    "service",
    "retailer",
    "price_value",
    "variant_constraint",
    "use_condition",
}
EXCLUSION_REASONS = {
    "no_claim",
    "appearance_only",
    "transaction_only",
    "entertainment_only",
    "outside_bound_question",
}

NON_CLAIMS = [
    "not semantic problem discovery",
    "not automatic decision relevance",
    "not proof that a Reddit claim is true",
    "not proof of causation, prevalence, or commercial importance",
    "not source completeness proof",
    "not permission to count failed captures as low value",
]


class RedditThreadQualificationFailure(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def build_reddit_thread_qualification(
    *,
    selection_path: Path,
    batch_summary_path: Path,
    labels_path: Path,
) -> dict[str, Any]:
    selection = _read_object(selection_path, code="selection_invalid")
    batch = _read_object(batch_summary_path, code="batch_summary_invalid")
    labels_payload = _read_object(labels_path, code="labels_invalid")
    if batch.get("runner") != "reddit_old_http_batch":
        raise RedditThreadQualificationFailure(
            "wrong_batch_runner",
            "batch summary must come from reddit_old_http_batch",
        )

    decision_question = labels_payload.get("decision_question")
    if not isinstance(decision_question, str) or not decision_question.strip():
        raise RedditThreadQualificationFailure(
            "decision_question_missing",
            "labels must bind a non-empty decision_question",
        )
    labels = labels_payload.get("threads")
    if not isinstance(labels, dict):
        raise RedditThreadQualificationFailure(
            "thread_labels_missing",
            "labels.threads must be an object keyed by slot_id",
        )

    selection_rows = _selection_rows(selection)
    results = batch.get("results")
    if not isinstance(results, list):
        raise RedditThreadQualificationFailure(
            "batch_results_missing",
            "batch summary results must be an array",
        )
    result_by_slot = {
        row["slot_id"]: row
        for row in results
        if isinstance(row, dict) and isinstance(row.get("slot_id"), str)
    }
    if len(result_by_slot) != len(results):
        raise RedditThreadQualificationFailure(
            "batch_slot_id_invalid",
            "every batch result must have one unique string slot_id",
        )

    rows: list[dict[str, Any]] = []
    for selection_row in selection_rows:
        slot_id = selection_row["slot_id"]
        result = result_by_slot.get(slot_id)
        if result is None:
            raise RedditThreadQualificationFailure(
                "selection_batch_mismatch",
                f"selection slot is absent from batch results: {slot_id}",
            )
        content = _content_record(result)
        label = labels.get(slot_id)
        rows.append(
            _prepare_row(
                selection_row=selection_row,
                result=result,
                content=content,
                label=label,
            )
        )

    _apply_wedge_qualification(rows)
    counts = _counts(rows)
    return {
        "reddit_thread_qualification": {
            "schema_version": QUALIFICATION_SCHEMA_VERSION,
            "decision_question": decision_question.strip(),
            "policy": {
                "relative_engagement_head_fraction": RELATIVE_ENGAGEMENT_HEAD_FRACTION,
                "absolute_comment_resonance_floor": ABSOLUTE_COMMENT_RESONANCE_FLOOR,
                "absolute_post_score_resonance_floor": ABSOLUTE_POST_SCORE_RESONANCE_FLOOR,
                "evidence_comment_point_floor": EVIDENCE_COMMENT_POINT_FLOOR,
                "near_duplicate_jaccard_floor": NEAR_DUPLICATE_JACCARD_FLOOR,
                "qualification_order": [
                    "excluded_not_decision_relevant",
                    "needs_judgment",
                    "critical_signal",
                    "priority_signal",
                    "stacked_emerging_signal",
                    "low_lead",
                ],
                "critical_contract": [
                    "explicit decision_relevant=true",
                    "resonance belongs to the declared evidence source",
                    "at least two independent evidence sources after excluding question-only posts and applying author and near-duplicate deduplication",
                ],
                "signal_kinds": sorted(SIGNAL_KINDS),
                "context_kinds": sorted(CONTEXT_KINDS),
                "exclusion_reasons": sorted(EXCLUSION_REASONS),
            },
            "counts": counts,
            "threads": rows,
            "non_claims": NON_CLAIMS,
        }
    }


def _selection_rows(selection: dict[str, Any]) -> list[dict[str, Any]]:
    direct_rows = selection.get("rows")
    if isinstance(direct_rows, list):
        rows = [row for row in direct_rows if isinstance(row, dict)]
        if len(rows) != len(direct_rows):
            raise RedditThreadQualificationFailure(
                "selection_rows_invalid",
                "selection rows must all be objects",
            )
        return [_validated_selection_row(row) for row in rows]

    candidates = selection.get("candidates")
    capture_slots = selection.get("capture_slots")
    if not isinstance(candidates, list) or not isinstance(capture_slots, list):
        raise RedditThreadQualificationFailure(
            "selection_shape_unsupported",
            "selection must contain rows or candidates plus capture_slots",
        )
    candidate_by_url = {
        row.get("thread_url"): row
        for row in candidates
        if isinstance(row, dict) and isinstance(row.get("thread_url"), str)
    }
    rows = []
    for slot in capture_slots:
        if not isinstance(slot, dict):
            raise RedditThreadQualificationFailure(
                "capture_slot_invalid",
                "capture slots must all be objects",
            )
        candidate = candidate_by_url.get(slot.get("url"))
        if candidate is None:
            raise RedditThreadQualificationFailure(
                "capture_slot_candidate_missing",
                f"capture slot URL has no candidate: {slot.get('url')}",
            )
        rows.append(
            _validated_selection_row(
                {
                    **candidate,
                    "slot_id": slot.get("slot_id"),
                }
            )
        )
    return rows


def _validated_selection_row(row: dict[str, Any]) -> dict[str, Any]:
    required = {
        "slot_id": str,
        "thread_url": str,
        "subreddit": str,
        "comments": int,
        "score": int,
        "subreddit_rank_by_comments": int,
        "subreddit_eligible_threads": int,
    }
    for key, expected_type in required.items():
        value = row.get(key)
        if not isinstance(value, expected_type) or isinstance(value, bool):
            raise RedditThreadQualificationFailure(
                "selection_row_field_invalid",
                f"selection row {row.get('slot_id')} has invalid {key}",
            )
    if row["subreddit_eligible_threads"] < 1:
        raise RedditThreadQualificationFailure(
            "selection_row_field_invalid",
            f"selection row {row['slot_id']} has invalid subreddit_eligible_threads",
        )
    return dict(row)


def _content_record(result: dict[str, Any]) -> dict[str, Any] | None:
    if result.get("capture_exit") != 0:
        return None
    packet_dir_value = result.get("packet_dir")
    if not isinstance(packet_dir_value, str) or not packet_dir_value:
        return None
    path = Path(packet_dir_value) / "raw" / "01_content_record.json"
    if not path.is_file():
        return None
    content = _read_object(path, code="content_record_invalid")
    if content.get("record_kind") != "reddit_thread_content_v0":
        raise RedditThreadQualificationFailure(
            "content_record_kind_invalid",
            f"unsupported content record kind for {result.get('slot_id')}",
        )
    return content


def _prepare_row(
    *,
    selection_row: dict[str, Any],
    result: dict[str, Any],
    content: dict[str, Any] | None,
    label: object,
) -> dict[str, Any]:
    slot_id = selection_row["slot_id"]
    if content is None:
        return {
            **selection_row,
            "capture_status": "gap",
            "qualification_tier": "access_or_processing_gap",
            "qualification_reasons": ["content_record_unavailable"],
            "decision_relevant": None,
            "signal_kinds": None,
            "context_kinds": None,
            "exclusion_reason": None,
            "post_evidence": None,
            "wedge_key": None,
            "post_author_key": None,
            "content_fingerprint": None,
            "resonance": None,
            "evidence_comments": None,
        }

    parsed_label = _validated_label(slot_id=slot_id, label=label, content=content)
    post = content.get("post") if isinstance(content.get("post"), dict) else {}
    post_author = _normalized_author(post.get("author_state"))
    comments = [
        comment
        for comment in content.get("comments", [])
        if isinstance(comment, dict)
    ]
    evidence_ids = set(parsed_label.get("evidence_comment_ids", []))
    evidence_comments = [
        comment
        for comment in comments
        if comment.get("comment_id") in evidence_ids
        and _is_evidence_comment(comment)
    ]
    max_evidence_comment_points = max(
        (
            parsed
            for comment in evidence_comments
            if (parsed := _points(comment.get("score_state"))) is not None
        ),
        default=None,
    )
    relative_head_size = math.ceil(
        selection_row["subreddit_eligible_threads"] * RELATIVE_ENGAGEMENT_HEAD_FRACTION
    )
    resonance_reasons: list[str] = []
    if parsed_label.get("post_evidence") is True:
        if selection_row["subreddit_rank_by_comments"] <= relative_head_size:
            resonance_reasons.append("post_relative_engagement_head")
        if selection_row["comments"] >= ABSOLUTE_COMMENT_RESONANCE_FLOOR:
            resonance_reasons.append("post_absolute_comment_floor")
        if selection_row["score"] >= ABSOLUTE_POST_SCORE_RESONANCE_FLOOR:
            resonance_reasons.append("post_absolute_score_floor")
    if (
        max_evidence_comment_points is not None
        and max_evidence_comment_points >= EVIDENCE_COMMENT_POINT_FLOOR
    ):
        resonance_reasons.append("evidence_comment_point_floor")

    title = selection_row.get("title_or_none")
    post_body = post.get("body_text")
    return {
        **selection_row,
        "capture_status": "content",
        "decision_relevant": parsed_label.get("decision_relevant"),
        "signal_kinds": parsed_label.get("signal_kinds"),
        "context_kinds": parsed_label.get("context_kinds"),
        "exclusion_reason": parsed_label.get("exclusion_reason"),
        "post_evidence": parsed_label.get("post_evidence"),
        "wedge_key": parsed_label.get("wedge_key"),
        "post_author_key": _author_key(post_author),
        "content_fingerprint": _content_fingerprint(title=title, post_body=post_body),
        "resonance": {
            "is_resonant": bool(resonance_reasons),
            "reasons": resonance_reasons,
            "listing_comments": selection_row["comments"],
            "listing_score": selection_row["score"],
            "max_evidence_comment_points": max_evidence_comment_points,
        },
        "evidence_comments": {
            "declared_comment_ids": sorted(evidence_ids),
            "ids_by_points": [
                str(comment["comment_id"])
                for comment in sorted(
                    evidence_comments,
                    key=lambda item: (
                        -(
                            _points(item.get("score_state"))
                            if _points(item.get("score_state")) is not None
                            else -1_000_000
                        ),
                        str(item.get("comment_id")),
                    ),
                )
            ],
            "declared_comment_author_keys": sorted(
                {
                    key
                    for comment in evidence_comments
                    if (key := _author_key(_normalized_author(comment.get("author_state"))))
                    is not None
                }
            ),
        },
        "qualification_tier": None,
        "qualification_reasons": [],
    }


def _validated_label(
    *,
    slot_id: str,
    label: object,
    content: dict[str, Any],
) -> dict[str, Any]:
    if label is None:
        return {}
    if not isinstance(label, dict):
        raise RedditThreadQualificationFailure(
            "thread_label_invalid",
            f"label for {slot_id} must be an object",
        )
    decision_relevant = label.get("decision_relevant")
    if not isinstance(decision_relevant, bool):
        raise RedditThreadQualificationFailure(
            "decision_relevance_invalid",
            f"label for {slot_id} must set decision_relevant true or false",
        )
    if decision_relevant:
        wedge_key = label.get("wedge_key")
        if not isinstance(wedge_key, str) or not wedge_key.strip():
            raise RedditThreadQualificationFailure(
                "wedge_key_missing",
                f"decision-relevant label for {slot_id} must set wedge_key",
            )
        if not isinstance(label.get("post_evidence"), bool):
            raise RedditThreadQualificationFailure(
                "post_evidence_invalid",
                f"decision-relevant label for {slot_id} must set post_evidence true or false",
            )
        signal_kinds = _validated_enum_list(
            slot_id=slot_id,
            field="signal_kinds",
            value=label.get("signal_kinds"),
            allowed=SIGNAL_KINDS,
            allow_empty=False,
        )
        context_kinds = _validated_enum_list(
            slot_id=slot_id,
            field="context_kinds",
            value=label.get("context_kinds"),
            allowed=CONTEXT_KINDS,
            allow_empty=True,
        )
        exclusion_reason = label.get("exclusion_reason")
        if exclusion_reason is not None:
            raise RedditThreadQualificationFailure(
                "exclusion_reason_conflict",
                f"decision-relevant label for {slot_id} cannot set exclusion_reason",
            )
    else:
        signal_kinds = []
        context_kinds = []
        exclusion_reason = label.get("exclusion_reason")
        if exclusion_reason not in EXCLUSION_REASONS:
            raise RedditThreadQualificationFailure(
                "exclusion_reason_invalid",
                f"excluded label for {slot_id} must set one accepted exclusion_reason",
            )
        if label.get("post_evidence") is not None or label.get("wedge_key") is not None:
            raise RedditThreadQualificationFailure(
                "excluded_evidence_conflict",
                f"excluded label for {slot_id} cannot declare post evidence or a wedge",
            )
    ids = label.get("evidence_comment_ids", [])
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        raise RedditThreadQualificationFailure(
            "evidence_comment_ids_invalid",
            f"evidence_comment_ids for {slot_id} must be a string array",
        )
    if not decision_relevant and ids:
        raise RedditThreadQualificationFailure(
            "excluded_evidence_conflict",
            f"excluded label for {slot_id} cannot declare evidence comments",
        )
    if decision_relevant and label.get("post_evidence") is False and not ids:
        raise RedditThreadQualificationFailure(
            "evidence_source_missing",
            f"decision-relevant label for {slot_id} must identify post or comment evidence",
        )
    comments = {
        comment.get("comment_id"): comment
        for comment in content.get("comments", [])
        if isinstance(comment, dict) and isinstance(comment.get("comment_id"), str)
    }
    for comment_id in ids:
        comment = comments.get(comment_id)
        if comment is None or not _is_evidence_comment(comment):
            raise RedditThreadQualificationFailure(
                "evidence_comment_invalid",
                f"{slot_id} declares missing or ineligible evidence comment {comment_id}",
            )
    return {
        "decision_relevant": decision_relevant,
        "signal_kinds": signal_kinds,
        "context_kinds": context_kinds,
        "exclusion_reason": exclusion_reason,
        "post_evidence": label.get("post_evidence") if decision_relevant else None,
        "wedge_key": label.get("wedge_key").strip() if decision_relevant else None,
        "evidence_comment_ids": ids,
    }


def _validated_enum_list(
    *,
    slot_id: str,
    field: str,
    value: object,
    allowed: set[str],
    allow_empty: bool,
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RedditThreadQualificationFailure(
            f"{field}_invalid",
            f"{field} for {slot_id} must be a string array",
        )
    normalized = list(dict.fromkeys(value))
    if not allow_empty and not normalized:
        raise RedditThreadQualificationFailure(
            f"{field}_invalid",
            f"{field} for {slot_id} must not be empty",
        )
    unknown = sorted(set(normalized) - allowed)
    if unknown:
        raise RedditThreadQualificationFailure(
            f"{field}_invalid",
            f"{field} for {slot_id} contains unsupported values: {unknown}",
        )
    return normalized


def _apply_wedge_qualification(rows: list[dict[str, Any]]) -> None:
    relevant_by_wedge: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["capture_status"] != "content":
            continue
        if row["decision_relevant"] is True:
            relevant_by_wedge[row["wedge_key"]].append(row)

    wedge_facts: dict[str, dict[str, Any]] = {}
    for wedge_key, wedge_rows in relevant_by_wedge.items():
        evidence_rows = [row for row in wedge_rows if row["post_evidence"] is True]
        clusters = _content_clusters(evidence_rows)
        known_post_authors = {
            row["post_author_key"]
            for row in evidence_rows
            if row["post_author_key"] is not None
        }
        independent_thread_sources = min(len(clusters), len(known_post_authors))
        comment_authors = {
            author_key
            for row in wedge_rows
            for author_key in row["evidence_comments"]["declared_comment_author_keys"]
            if author_key not in known_post_authors
        }
        independent_sources = independent_thread_sources + len(comment_authors)
        wedge_facts[wedge_key] = {
            "thread_count": len(wedge_rows),
            "evidence_bearing_thread_count": len(evidence_rows),
            "unique_post_author_count": len(known_post_authors),
            "near_duplicate_content_cluster_count": len(clusters),
            "independent_thread_source_count": independent_thread_sources,
            "independent_evidence_commenter_count": len(comment_authors),
            "independent_evidence_source_count": independent_sources,
            "is_resonant": any(row["resonance"]["is_resonant"] for row in wedge_rows),
        }

    for row in rows:
        if row["capture_status"] != "content":
            continue
        if row["decision_relevant"] is False:
            row["qualification_tier"] = "excluded_not_decision_relevant"
            row["qualification_reasons"] = ["explicitly_not_decision_relevant"]
            continue
        if row["decision_relevant"] is not True:
            row["qualification_tier"] = "needs_judgment"
            row["qualification_reasons"] = ["decision_relevance_not_supplied"]
            continue

        facts = wedge_facts[row["wedge_key"]]
        row["wedge_evidence"] = facts
        corroborated = facts["independent_evidence_source_count"] >= 2
        resonant = facts["is_resonant"]
        if resonant and corroborated:
            tier = "critical_signal"
            reasons = ["decision_relevant", "resonant", "independently_corroborated"]
        elif resonant:
            tier = "priority_signal"
            reasons = ["decision_relevant", "resonant", "not_independently_corroborated"]
        elif corroborated:
            tier = "stacked_emerging_signal"
            reasons = ["decision_relevant", "independently_corroborated", "low_engagement"]
        else:
            tier = "low_lead"
            reasons = ["decision_relevant", "low_engagement", "not_independently_corroborated"]
        row["qualification_tier"] = tier
        row["qualification_reasons"] = reasons


def _content_clusters(rows: list[dict[str, Any]]) -> list[list[str]]:
    clusters: list[list[dict[str, Any]]] = []
    for row in sorted(rows, key=lambda item: item["slot_id"]):
        tokens = set(row["content_fingerprint"]["tokens"])
        matched: list[dict[str, Any]] | None = None
        for cluster in clusters:
            if any(
                _jaccard(tokens, set(existing["content_fingerprint"]["tokens"]))
                >= NEAR_DUPLICATE_JACCARD_FLOOR
                for existing in cluster
            ):
                matched = cluster
                break
        if matched is None:
            clusters.append([row])
        else:
            matched.append(row)
    return [[row["slot_id"] for row in cluster] for cluster in clusters]


def _content_fingerprint(*, title: object, post_body: object) -> dict[str, Any]:
    text = f"{title or ''} {post_body or ''}".lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    normalized = " ".join(tokens)
    return {
        "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "tokens": sorted(set(tokens)),
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _is_evidence_comment(comment: dict[str, Any]) -> bool:
    body = comment.get("body_text")
    if not isinstance(body, str):
        return False
    normalized = " ".join(body.split())
    if not normalized or normalized in {"[removed]", "[deleted]"}:
        return False
    return "I am a bot" not in normalized


def _points(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"-?\d[\d,]*", value)
    return int(match.group(0).replace(",", "")) if match else None


def _normalized_author(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized or normalized in {"[deleted]", "[removed]"}:
        return None
    return normalized


def _author_key(author: str | None) -> str | None:
    if author is None:
        return None
    return f"author_{hashlib.sha256(author.encode('utf-8')).hexdigest()[:16]}"


def _counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tiers = Counter(row["qualification_tier"] for row in rows)
    return {
        "thread_count": len(rows),
        "capture_gap_count": tiers.get("access_or_processing_gap", 0),
        "qualification_tier_counts": dict(sorted(tiers.items())),
        "decision_relevant_count": sum(row["decision_relevant"] is True for row in rows),
        "explicitly_not_decision_relevant_count": sum(
            row["decision_relevant"] is False for row in rows
        ),
        "needs_judgment_count": tiers.get("needs_judgment", 0),
    }


def _read_object(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RedditThreadQualificationFailure(code, f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RedditThreadQualificationFailure(code, f"{path}: expected JSON object")
    return value
