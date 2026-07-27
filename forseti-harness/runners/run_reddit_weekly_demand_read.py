"""Weekly demand read over committed reddit_subreddit_grid top/week packets.

Evidence-layer reader (weekly demand radar spec, section E): discovers this
week's ``top/?t=week`` grid packets for the lake-registry roster, ranks
problem candidates by discussion density and evidence volume, and emits one
JSON document. Pure read -- no lake writes, no network, no analysis persisted.

Owner contract:
- forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
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
DEFAULT_ENGAGEMENT_HEAD_FRACTION = 0.5
DEFAULT_OPAQUE_TAIL_AUDIT_FRACTION = 0.1
DEFAULT_TAIL_RESCUE_MIN_COMMENTS = 1
DEFAULT_TAIL_RESCUE_SCORE = 2
DEFAULT_ZERO_COMMENT_TAIL_RESCUE_SCORE = 3
DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_COMMENTS = 5
DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_SCORE = 25
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

_STRONG_TAIL_TITLE_REASONS = frozenset(
    {
        "pain_or_failure",
        "praise_or_success",
        "comparison_or_choice",
        "concrete_outcome_or_experience",
        "review_or_update",
    }
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


def _tail_title_rescue_score(
    *,
    title_reasons: list[str],
    context_reasons: list[str],
) -> int:
    # One direct pain/praise/outcome/review family is sufficient evidence to
    # inspect a thread with observed discussion. Generic questions, routines, hauls, and
    # discussion flairs carry only one point and need concrete product,
    # ingredient, technique, price, or variant context to qualify.
    score = (
        2
        if any(reason in _STRONG_TAIL_TITLE_REASONS for reason in title_reasons)
        else 0
    )
    if score == 0 and title_reasons:
        score = 1
    if context_reasons:
        score += 1
    return score


def _tail_title_rescue_eligible(*, comments: int, rescue_score: int) -> bool:
    threshold = (
        DEFAULT_TAIL_RESCUE_SCORE
        if comments >= DEFAULT_TAIL_RESCUE_MIN_COMMENTS
        else DEFAULT_ZERO_COMMENT_TAIL_RESCUE_SCORE
    )
    return rescue_score >= threshold


def _audit_order_key(*, as_of: _dt.date, subreddit: str, thread_url: str) -> str:
    return hashlib.sha256(
        f"{as_of.isoformat()}\0{subreddit}\0{thread_url}".encode("utf-8")
    ).hexdigest()


def _absolute_engagement_rescue_eligible(*, comments: int, score: int) -> bool:
    return (
        comments >= DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_COMMENTS
        or score >= DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_SCORE
    )


def _select_deep_dive_rows(
    *,
    subreddit: str,
    rows: list[dict[str, Any]],
    as_of: _dt.date,
    opaque_tail_audit_fraction: float,
) -> list[dict[str, Any]]:
    if not 0 < opaque_tail_audit_fraction <= 1:
        raise ValueError("opaque_tail_audit_fraction must be greater than zero and at most one")

    ranked = sorted(
        rows,
        key=lambda item: (-item["comments"], -item["score"], item["thread_url"]),
    )
    head_size = math.ceil(len(ranked) * DEFAULT_ENGAGEMENT_HEAD_FRACTION)
    selected: list[dict[str, Any]] = []
    audit_tail: list[dict[str, Any]] = []
    for position, item in enumerate(ranked, start=1):
        title_class, title_reasons = _classify_title_signal(
            item["title_or_none"],
            item["flair_or_none"],
        )
        title_context_reasons = _title_context_reasons(
            item["title_or_none"],
            item["flair_or_none"],
        )
        title_rescue_score = _tail_title_rescue_score(
            title_reasons=title_reasons,
            context_reasons=title_context_reasons,
        )
        title_rescue_eligible = _tail_title_rescue_eligible(
            comments=item["comments"],
            rescue_score=title_rescue_score,
        )
        enriched = {
            **item,
            "subreddit_rank_by_comments": position,
            "subreddit_eligible_threads": len(ranked),
            "title_signal_class": title_class,
            "title_signal_reasons": title_reasons,
            "title_context_reasons": title_context_reasons,
            "title_rescue_score": title_rescue_score,
            "title_rescue_eligible": title_rescue_eligible,
        }
        if position <= head_size:
            selected.append({**enriched, "selection_reason": "engagement_head"})
        elif title_class in {"explicit", "suggestive"} and title_rescue_eligible:
            selected.append({**enriched, "selection_reason": f"title_{title_class}"})
        else:
            audit_tail.append(enriched)
            if _absolute_engagement_rescue_eligible(
                comments=item["comments"],
                score=item["score"],
            ):
                selected.append(
                    {**enriched, "selection_reason": "absolute_engagement_rescue"}
                )

    if audit_tail:
        audit_size = max(1, math.ceil(len(audit_tail) * opaque_tail_audit_fraction))
        audited = sorted(
            audit_tail,
            key=lambda item: _audit_order_key(
                as_of=as_of,
                subreddit=subreddit,
                thread_url=item["thread_url"],
            ),
        )[:audit_size]
        selected_urls = {str(item["thread_url"]) for item in selected}
        for item in audited:
            if str(item["thread_url"]) in selected_urls:
                continue
            selection_reason = (
                "opaque_tail_audit"
                if item["title_signal_class"] == "opaque"
                else "weak_signal_tail_audit"
            )
            selected.append({**item, "selection_reason": selection_reason})
    return selected


def run_weekly_demand_read(
    *,
    data_root: DataLakeRoot,
    as_of: _dt.date,
    opaque_tail_audit_fraction: float = DEFAULT_OPAQUE_TAIL_AUDIT_FRACTION,
) -> dict[str, Any]:
    if not 0 < opaque_tail_audit_fraction <= 1:
        raise ValueError("opaque_tail_audit_fraction must be greater than zero and at most one")
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
        usable = [(row, score, comments) for row, score, comments in scored
                  if score is not None and comments is not None]
        total_score = sum(score for _, score, _ in usable)
        total_comments = sum(comments for _, _, comments in usable)
        score_floor = min((score for _, score, _ in usable), default=None)
        if score_floor is not None and score_floor > PAGE_OVERFLOW_SCORE_FLOOR:
            floor_tripwire.append(name)
        sub_health.append(
            {
                "subreddit": name,
                "packet_id": packet_id,
                "observed_at": read.observed_at,
                "created_utc_or_none": read.grid_view.created_utc_or_none,
                "posts": len(usable),
                "rows_dropped_unparsed": len(scored) - len(usable),
                "weekly_score": total_score,
                "weekly_comments": total_comments,
                "page1_score_floor": score_floor,
                "deep_dive_head_size": math.ceil(
                    len(usable) * DEFAULT_ENGAGEMENT_HEAD_FRACTION
                ),
            }
        )
        eligible = [
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
        ]
        eligible_threads_found += len(eligible)
        for item in eligible:
            title_class, _reasons = _classify_title_signal(
                item["title_or_none"],
                item["flair_or_none"],
            )
            title_signal_counts[title_class] += 1
        candidates.extend(
            _select_deep_dive_rows(
                subreddit=name,
                rows=eligible,
                as_of=as_of,
                opaque_tail_audit_fraction=opaque_tail_audit_fraction,
            )
        )

    candidates.sort(key=lambda item: (-item["comments"], item["thread_url"]))
    selection_reason_counts = Counter(
        item["selection_reason"] for item in candidates
    )
    capture_slots = [
        {"slot_id": f"weekly_{index:04d}", "url": item["thread_url"]}
        for index, item in enumerate(candidates, start=1)
    ]
    return {
        "reader": "reddit_weekly_demand_read",
        "as_of": as_of.isoformat(),
        "window_start": window_start.isoformat(),
        "selection_policy": {
            "engagement_head_fraction": DEFAULT_ENGAGEMENT_HEAD_FRACTION,
            "engagement_rank_primary": "comments",
            "engagement_rank_tiebreakers": ["score", "thread_url"],
            "tail_title_rescue_classes": ["explicit", "suggestive"],
            "tail_title_rescue_min_comments": DEFAULT_TAIL_RESCUE_MIN_COMMENTS,
            "tail_title_rescue_score": DEFAULT_TAIL_RESCUE_SCORE,
            "zero_comment_tail_rescue_score": DEFAULT_ZERO_COMMENT_TAIL_RESCUE_SCORE,
            "absolute_engagement_rescue_min_comments": (
                DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_COMMENTS
            ),
            "absolute_engagement_rescue_min_score": (
                DEFAULT_ABSOLUTE_ENGAGEMENT_MIN_SCORE
            ),
            "tail_title_rescue_scoring": {
                "strong_pain_praise_outcome_comparison_or_review": 2,
                "generic_question_routine_haul_or_discussion": 1,
                "concrete_entity_ingredient_technique_price_or_variant_context": 1,
            },
            "opaque_tail_audit_fraction": opaque_tail_audit_fraction,
            "opaque_tail_audit_minimum_per_subreddit": 1,
            "opaque_tail_audit_rotation": "sha256(as_of, subreddit, thread_url)",
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
        "candidates_found": len(candidates),
        "selection_reason_counts": dict(sorted(selection_reason_counts.items())),
        "title_signal_counts": dict(sorted(title_signal_counts.items())),
        "candidates": candidates,
        "capture_slots": capture_slots,
        "page_overflow_tripwire": floor_tripwire,
        "non_claims": [
            "not metric authority",
            "not demand proof or venue scoring",
            "title signals route capture; they do not establish pain, praise, causation, or prevalence",
            "not a lake write (recompute from packets at will)",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read this week's top/?t=week reddit_subreddit_grid packets for the "
            "registry roster and emit ranked problem candidates as JSON."
        )
    )
    parser.add_argument("--data-root", default=None, help="Lake root (defaults to resolution).")
    parser.add_argument("--as-of", default=None, help="ISO date closing the 7-day window; defaults to today (UTC).")
    parser.add_argument(
        "--opaque-tail-audit-fraction",
        type=float,
        default=DEFAULT_OPAQUE_TAIL_AUDIT_FRACTION,
    )
    parser.add_argument("--output", type=Path, default=None, help="Also write the JSON document here.")
    parser.add_argument(
        "--capture-list-output",
        type=Path,
        default=None,
        help="Also write a run_reddit_old_http_batch.py-compatible selected URL list.",
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
        payload = run_weekly_demand_read(
            data_root=data_root,
            as_of=as_of,
            opaque_tail_audit_fraction=args.opaque_tail_audit_fraction,
        )
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        if args.capture_list_output is not None:
            args.capture_list_output.parent.mkdir(parents=True, exist_ok=True)
            args.capture_list_output.write_text(
                json.dumps(
                    payload["capture_slots"],
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
