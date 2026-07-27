"""Weekly demand read over committed reddit_subreddit_grid top/week packets.

Evidence-layer reader (weekly demand radar spec, section E): discovers this
week's ``top/?t=week`` grid packets for the lake-registry roster, applies the
stable listing floor, and emits a ranked model-review queue. Pure read -- no
lake writes, no network, no analysis persisted, and no capture authorization.

Owner contract:
- forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md
- forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture_spine.reddit_subreddit_grid.materializer import (
    RegistryRefreshError,
    read_grid_packet,
)
from capture_spine.reddit_subreddit_grid.grid_projection import grid_view_projection_anomaly
from data_lake.reddit_subreddit_registry import capture_roster
from data_lake.root import DataLakeRoot
from runners._scaffold import exit_on_failure

GRID_SOURCE_FAMILY = "reddit_subreddit_grid"
LISTING_EFFICIENCY_POLICY_VERSION = "reddit_listing_efficiency_v0"
GENERAL_DISCUSSION_FLOOR_MAX_COMMENTS = 3
# Page-1 score floor above which a subreddit genuinely overflows one page
# (top-10 carries 65% of weekly score on the measured distribution; a floor
# past 50 means real traction ran off the page and the next pass should
# capture page 2 for that subreddit).
PAGE_OVERFLOW_SCORE_FLOOR = 50

_EXPLICIT_TITLE_SIGNALS = (
    (
        "pain_or_failure",
        re.compile(
            r"\b(?:allerg|bad|broke me out|breakouts?|burn(?:ed|ing)?|"
            r"can(?:no|'t|’t)|damag|disappoint|does(?:n|'t|’t)|dry(?:ing|ness)?|"
            r"fail(?:ed|ing|s)?|hair ?fall|hair loss|hate|hated|hurt|irritat|"
            r"itch|issue|problem|"
            r"reaction|ruined|sensitive|sore|struggl|texture|worse|worst)\w*\b"
        ),
    ),
    (
        "praise_or_success",
        re.compile(
            r"\b(?:amazing|best|favorite|favourite|finally|holy grail|impress|"
            r"love|loved|perfect|recommend|saved|shout[- ]?out|success|worked|"
            r"works|worth)\w*\b"
        ),
    ),
    (
        "comparison_or_choice",
        re.compile(
            r"(?:\b(?:alternative|better|compare|comparison|dupe|overhyped|"
            r"underrated|versus|vs)\b|\bwhich\b)"
        ),
    ),
    (
        "concrete_outcome_or_experience",
        re.compile(
            r"(?:\bbefore\s*(?:/|&|and|-)?\s*after\b|"
            r"\b(?:experience|full pan|lasted|result|started|tried|trying|"
            r"using|used)\w*\b|\b20\d{2}\s*[-–]\s*20\d{2}\b)"
        ),
    ),
    (
        "concrete_question_or_request",
        re.compile(
            r"(?:\?|\b(?:looking for|need|protective styles? for (?:over|under) \d+)\b|"
            r"\b(?:id my|please help)\b|"
            r"^(?:anyone|are|asking|can|could|do|does|has|have|help|how|is|"
            r"should|what|when|where|why|would)\b)"
        ),
    ),
)

_SUGGESTIVE_TITLE_SIGNALS = (
    (
        "review_or_update",
        re.compile(r"\b(?:check[- ]?in|progress|review|update)\w*\b"),
    ),
    (
        "routine_or_collection",
        re.compile(
            r"\b(?:collection|empties|faves?|favorites?|favourites?|haul|"
            r"routine|shelfie|showoff)\w*\b"
        ),
    ),
    (
        "recommendation_or_discussion",
        re.compile(r"\b(?:advice|discussion|recommendation|suggestion|thoughts)\w*\b"),
    ),
)

_CONCRETE_TITLE_CONTEXT_SIGNALS = (
    (
        "named_product_or_ingredient_context",
        re.compile(
            r"\b(?:acid|blush|cleanser|cologne|conditioner|cream|finasteride|"
            r"foundation|fragrance|gel|glue|ingredient|lipstick|mascara|"
            r"minoxidil|moisturi[sz]er|niacinamide|perfume|polish|product|"
            r"retinol|serum|shampoo|sunscreen|tretinoin|vitamin c)\w*\b"
        ),
    ),
    (
        "technique_or_repair_context",
        re.compile(
            r"\b(?:adhesion|application|cure|curing|foil|lamp|layer|patch|"
            r"protective style|repair|swatch|technique)\w*\b"
        ),
    ),
    (
        "price_or_value_context",
        re.compile(
            r"(?:[$€£]\s*\d|\b\d+(?:\.\d+)?\s*(?:dollars?|usd|eur|gbp)\b|"
            r"\b(?:afford|budget|cheap|cost|expensive|price|value)\w*\b)"
        ),
    ),
    (
        "specific_variant_or_constraint",
        re.compile(
            r"(?:\b(?:berry|blonde|cool[- ]?tone|dry skin|oily skin|shade|"
            r"facial hair|hair type|sensitive skin|undertone)\w*\b|"
            r"\b\d+(?:\.\d+)?%\b)"
        ),
    ),
)

def _int_or_none(value: str | None) -> int | None:
    # helper-delta: unlike harness_utils.int_or_none, this accepts signed
    # strings -- a downvoted thread's data-score is legitimately negative and
    # must count, not vanish as unparsed.
    if value is None:
        return None
    digits = value.replace(",", "").strip()
    if digits.lstrip("-").isdigit():
        # str.isdigit() is broader than int() accepts (multiple leading
        # minuses, superscripts, and other Unicode digit forms pass isdigit
        # yet raise in int()), so guard the conversion: a malformed cell must
        # drop to None and be counted as unparsed, never abort the whole read.
        try:
            return int(digits)
        except ValueError:
            return None
    return None


def _is_top_week(listing_url: str) -> bool:
    parsed = urlparse(listing_url)
    parts = [part for part in parsed.path.split("/") if part]
    return bool(parts) and parts[-1] == "top" and "t=week" in (parsed.query or "").split("&")


_BOUNDED_ID_SAMPLE = 20


def _bounded_ids(ids: list[str]) -> dict[str, Any]:
    ordered = sorted(ids)
    return {"count": len(ordered), "sample": ordered[:_BOUNDED_ID_SAMPLE]}


def _packet_capture_time(manifest_path: str) -> _dt.datetime:
    """Read the exact validated source-slice time; packet IDs are opaque."""
    document = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    values = [
        source_slice.get("timing", {}).get("capture_time", {}).get("value")
        for source_slice in document.get("source_slices", [])
        if isinstance(source_slice, dict)
    ]
    timestamps: list[_dt.datetime] = []
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        parsed = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError(f"capture_time is timezone-naive: {value!r}")
        timestamps.append(parsed.astimezone(_dt.timezone.utc))
    if not timestamps:
        raise ValueError("manifest carries no known source-slice capture_time")
    return max(timestamps)


def _classify_title_signal(
    title_or_none: str | None,
    flair_or_none: str | None = None,
) -> tuple[str, list[str]]:
    visible_parts = [
        value.strip()
        for value in (title_or_none, flair_or_none)
        if isinstance(value, str) and value.strip()
    ]
    if not visible_parts:
        return "opaque", []
    normalized = " ".join(" ".join(visible_parts).casefold().split())
    explicit = [
        reason
        for reason, pattern in _EXPLICIT_TITLE_SIGNALS
        if pattern.search(normalized)
    ]
    if explicit:
        return "explicit", explicit
    suggestive = [
        reason
        for reason, pattern in _SUGGESTIVE_TITLE_SIGNALS
        if pattern.search(normalized)
    ]
    if suggestive:
        return "suggestive", suggestive
    return "opaque", []


def _title_context_reasons(
    title_or_none: str | None,
    flair_or_none: str | None = None,
) -> list[str]:
    visible_parts = [
        value.strip()
        for value in (title_or_none, flair_or_none)
        if isinstance(value, str) and value.strip()
    ]
    if not visible_parts:
        return []
    normalized = " ".join(" ".join(visible_parts).casefold().split())
    return [
        reason
        for reason, pattern in _CONCRETE_TITLE_CONTEXT_SIGNALS
        if pattern.search(normalized)
    ]


def _listing_review_sort_key(item: dict[str, Any]) -> tuple[int, bool, int, str]:
    score = item["score"]
    return (
        -item["comments"],
        score is None,
        -(score if score is not None else 0),
        item["thread_url"],
    )


def _build_listing_review_rows(*, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        (
            item
            for item in rows
            if item["comments"] > GENERAL_DISCUSSION_FLOOR_MAX_COMMENTS
        ),
        key=_listing_review_sort_key,
    )
    review_rows: list[dict[str, Any]] = []
    for position, item in enumerate(ranked, start=1):
        title_class, title_reasons = _classify_title_signal(
            item["title_or_none"],
            item["flair_or_none"],
        )
        title_context_reasons = _title_context_reasons(
            item["title_or_none"],
            item["flair_or_none"],
        )
        context_state = (
            "listing_context_insufficient"
            if title_class == "opaque" and not title_context_reasons
            else "listing_context_present"
        )
        review_rows.append(
            {
                **item,
                "subreddit_rank_by_comments": position,
                "subreddit_review_threads": len(ranked),
                "title_signal_class": title_class,
                "title_signal_reasons": title_reasons,
                "title_context_reasons": title_context_reasons,
                "listing_context_state": context_state,
                "selection_reason": "comment_floor_cleared",
                "policy_stage": "requires_commission_model_adjudication",
            }
        )
    return review_rows


def run_weekly_demand_read(
    *,
    data_root: DataLakeRoot,
    as_of: _dt.date,
) -> dict[str, Any]:
    window_start = as_of - _dt.timedelta(days=6)
    # capture_roster: a retired subreddit is not "missing a weekly packet", it
    # is deliberately not captured, and must not inflate the coverage gap.
    roster = capture_roster(data_root)

    # Newest qualifying packet per subreddit; a re-run within the week
    # supersedes rather than double-counts.
    per_sub: dict[str, Any] = {}
    unreadable: list[dict[str, str]] = []
    skipped_non_top_week: list[str] = []
    skipped_outside_window: list[str] = []
    skipped_non_roster: list[dict[str, str]] = []
    projection_anomalies: list[dict[str, str]] = []
    superseded_packets: list[str] = []
    for packet_id in data_root.list_available(source_family=GRID_SOURCE_FAMILY):
        container = data_root.find_packet(packet_id)
        if container is None:
            continue
        try:
            read = read_grid_packet(packet_or_manifest_path=container)
        except RegistryRefreshError as exc:
            unreadable.append({"packet_id": packet_id, "error": f"[{exc.code}] {exc.message}"})
            continue
        if not _is_top_week(read.grid_view.listing_url):
            skipped_non_top_week.append(packet_id)
            continue
        observed = _dt.date.fromisoformat(read.observed_at)
        if not window_start <= observed <= as_of:
            skipped_outside_window.append(packet_id)
            continue
        key = read.subreddit
        if key not in roster:
            skipped_non_roster.append({"packet_id": packet_id, "subreddit": key})
            continue
        anomaly = grid_view_projection_anomaly(read.grid_view)
        if anomaly is not None:
            projection_anomalies.append({"packet_id": packet_id, "anomaly": anomaly})
            continue
        try:
            capture_time = _packet_capture_time(read.manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            unreadable.append({"packet_id": packet_id, "error": f"capture_time: {exc}"})
            continue
        current = per_sub.get(key)
        if current is None or (capture_time, packet_id) > (current[2], current[1]):
            if current is not None:
                superseded_packets.append(current[1])
            per_sub[key] = (read, packet_id, capture_time)
        else:
            superseded_packets.append(packet_id)

    sub_health: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    eligible_threads_found = 0
    listing_review_threads_found = 0
    general_floor_suppressed_threads = 0
    missing_engagement_rows: list[dict[str, Any]] = []
    title_signal_counts: Counter[str] = Counter()
    floor_tripwire: list[str] = []
    for name in sorted(per_sub):
        read, packet_id, _capture_time = per_sub[name]
        rows = [
            row
            for row in read.grid_view.thread_rows
            if not row.stickied and not row.promoted
        ]
        scored = [
            (row, _int_or_none(row.visible_score_or_none), _int_or_none(row.visible_comment_count_or_none))
            for row in rows
        ]
        usable = [
            (row, score, comments)
            for row, score, comments in scored
            if comments is not None
        ]
        missing_comment_rows = [
            {
                "subreddit": name,
                "thread_url": row.thread_url,
                "title_or_none": row.visible_title_or_none,
                "flair_or_none": row.flair_or_none,
                "missing_fields": ["comments"]
                + (["score"] if score is None else []),
            }
            for row, score, comments in scored
            if comments is None
        ]
        missing_engagement_rows.extend(missing_comment_rows)
        total_score = sum(
            score for _, score, _ in usable if score is not None
        )
        total_comments = sum(comments for _, _, comments in usable)
        score_floor = min(
            (score for _, score, _ in usable if score is not None),
            default=None,
        )
        if score_floor is not None and score_floor > PAGE_OVERFLOW_SCORE_FLOOR:
            floor_tripwire.append(name)
        review_rows = _build_listing_review_rows(
            rows=[
                {
                    "subreddit": name,
                    "thread_url": row.thread_url,
                    "title_or_none": row.visible_title_or_none,
                    "flair_or_none": row.flair_or_none,
                    "timestamp_utc_ms_or_none": row.timestamp_utc_ms_or_none,
                    "score": score,
                    "comments": comments,
                }
                for row, score, comments in usable
            ],
        )
        floor_suppressed = len(usable) - len(review_rows)
        sub_health.append(
            {
                "subreddit": name,
                "packet_id": packet_id,
                "observed_at": read.observed_at,
                "created_utc_or_none": read.grid_view.created_utc_or_none,
                "posts": len(usable),
                "rows_dropped_unparsed": len(missing_comment_rows),
                "rows_with_unparsed_score": sum(
                    1 for _, score, _ in usable if score is None
                ),
                "weekly_score": total_score,
                "weekly_comments": total_comments,
                "page1_score_floor": score_floor,
                "listing_policy_review_threads": len(review_rows),
                "general_floor_suppressed_threads": floor_suppressed,
            }
        )
        eligible_threads_found += len(usable)
        listing_review_threads_found += len(review_rows)
        general_floor_suppressed_threads += floor_suppressed
        for item in review_rows:
            title_signal_counts[item["title_signal_class"]] += 1
        candidates.extend(review_rows)

    candidates.sort(key=_listing_review_sort_key)
    selection_reason_counts = Counter(
        item["selection_reason"] for item in candidates
    )
    return {
        "reader": "reddit_weekly_demand_read",
        "as_of": as_of.isoformat(),
        "window_start": window_start.isoformat(),
        "selection_policy": {
            "policy_version": LISTING_EFFICIENCY_POLICY_VERSION,
            "general_discussion_floor_max_comments": GENERAL_DISCUSSION_FLOOR_MAX_COMMENTS,
            "review_min_comments": GENERAL_DISCUSSION_FLOOR_MAX_COMMENTS + 1,
            "zero_or_negative_score_is_veto": False,
            "missing_counts_are_unparsed": True,
            "engagement_rank_primary": "comments",
            "engagement_rank_tiebreakers": ["score", "thread_url"],
            "title_signals_are_binding": False,
            "admission_decision": "commission_conditioned_model_yes_borderline_no",
            "page_overflow_score_floor": PAGE_OVERFLOW_SCORE_FLOOR,
        },
        "roster_count": len(roster),
        "subs_read": len(per_sub),
        "subs_missing_weekly_packet": sorted(set(roster) - set(per_sub)),
        "unreadable_packets": unreadable,
        # These three classes grow with the whole packet corpus (every past
        # week lands outside the window forever), so they report count+sample
        # rather than exhaustive IDs. Non-roster and anomaly dispositions stay
        # exhaustive: they are small and each one is an operator signal.
        "packets_skipped_non_top_week": _bounded_ids(skipped_non_top_week),
        "packets_skipped_outside_window": _bounded_ids(skipped_outside_window),
        "packets_skipped_non_roster": sorted(
            skipped_non_roster, key=lambda item: (item["subreddit"], item["packet_id"])
        ),
        "projection_anomaly_packets": sorted(
            projection_anomalies, key=lambda item: item["packet_id"]
        ),
        "superseded_weekly_packets": _bounded_ids(superseded_packets),
        "sub_health": sub_health,
        "eligible_threads_found": eligible_threads_found,
        "listing_review_threads_found": listing_review_threads_found,
        "general_floor_suppressed_threads": general_floor_suppressed_threads,
        "candidates_found": len(candidates),
        "selection_reason_counts": dict(sorted(selection_reason_counts.items())),
        "title_signal_counts": dict(sorted(title_signal_counts.items())),
        "candidates": candidates,
        "missing_engagement_rows": sorted(
            missing_engagement_rows,
            key=lambda item: (item["subreddit"], item["thread_url"]),
        ),
        "capture_list_status": "blocked_pending_commission_model_adjudication",
        "capture_slots": [],
        "page_overflow_tripwire": floor_tripwire,
        "non_claims": [
            "not metric authority",
            "not demand proof or venue scoring",
            "review-queue membership is not exact-thread capture authorization",
            "title signals are non-binding cues; they do not establish pain, praise, causation, or prevalence",
            "not a lake write (recompute from packets at will)",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read this week's top/?t=week reddit_subreddit_grid packets for the "
            "registry roster and emit a ranked model-review queue as JSON."
        )
    )
    parser.add_argument("--data-root", default=None, help="Lake root (defaults to resolution).")
    parser.add_argument("--as-of", default=None, help="ISO date closing the 7-day window; defaults to today (UTC).")
    parser.add_argument("--output", type=Path, default=None, help="Also write the JSON document here.")
    parser.add_argument(
        "--capture-list-output",
        type=Path,
        default=None,
        help=(
            "Reserved for an adjudicated run_reddit_old_http_batch.py URL list; "
            "fails closed while the reader output is unadjudicated."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    with exit_on_failure(parser, runner_name="reddit weekly demand read"):
        if args.data_root is not None:
            data_root = DataLakeRoot.resolve_readonly(explicit=args.data_root)
        else:
            data_root = DataLakeRoot.resolve_readonly()
        as_of = (
            _dt.date.fromisoformat(args.as_of)
            if args.as_of
            else _dt.datetime.now(_dt.timezone.utc).date()
        )
        payload = run_weekly_demand_read(data_root=data_root, as_of=as_of)
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        if args.capture_list_output is not None:
            raise ValueError(
                "--capture-list-output is blocked pending commission-conditioned "
                "model adjudication; the weekly reader does not authorize capture"
            )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
