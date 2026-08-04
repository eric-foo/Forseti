"""Deterministic human view over a consumer-brand Phase A evidence ledger.

The ledger and community coding remain the evidence-bearing artifacts.  This
module only renders their acquisition yield in a form an operator can audit.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


class AcquisitionYieldReportError(ValueError):
    """Raised when the requested report cannot be derived without guessing."""


def _objects(value: Any, *, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise AcquisitionYieldReportError(f"{label} must be a list of objects")
    return list(value)


def _text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AcquisitionYieldReportError(f"{label} must be non-empty text")
    return value.strip()


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.1f}%)"


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    rendered = ["| " + " | ".join(_cell(value) for value in headers) + " |"]
    rendered.append("| " + " | ".join("---" for _ in headers) + " |")
    rendered.extend(
        "| " + " | ".join(_cell(value) for value in row) + " |" for row in rows
    )
    return "\n".join(rendered)


def _family_scorecard(
    ledger: Mapping[str, Any], coding: Mapping[str, Any]
) -> str:
    families = ledger.get("families")
    if not isinstance(families, Mapping):
        raise AcquisitionYieldReportError("ledger families must be an object")

    external = families.get("external_context", {})
    external_units = _objects(
        external.get("units", []) if isinstance(external, Mapping) else [],
        label="external_context.units",
    )
    qualifying_external_origins = {
        str(row.get("origin_id"))
        for row in external_units
        if row.get("independence") == "independent_origin"
        and row.get("relationship") == "apparently_independent"
        and row.get("source_type") in {"consumer_editorial", "trade_press"}
        and row.get("origin_id")
    }

    retailer = families.get("retailer_reviews", {})
    corpora = _objects(
        retailer.get("corpora", []) if isinstance(retailer, Mapping) else [],
        label="retailer_reviews.corpora",
    )
    denominators: dict[str, int] = {}
    for axis in _objects(ledger.get("product_axes"), label="product_axes"):
        for row in _objects(axis.get("retailer_incidence"), label="retailer_incidence"):
            corpus_id = _text(row.get("corpus_id"), label="corpus_id")
            value = row.get("eligible_text_review_count")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise AcquisitionYieldReportError(
                    f"invalid eligible review denominator for {corpus_id}"
                )
            previous = denominators.setdefault(corpus_id, value)
            if previous != value:
                raise AcquisitionYieldReportError(
                    f"retailer denominator drift for {corpus_id}: {previous} != {value}"
                )

    reddit = families.get("reddit_forum", {})
    threads = _objects(
        reddit.get("threads", []) if isinstance(reddit, Mapping) else [],
        label="reddit_forum.threads",
    )
    communities = {str(row.get("community_id")) for row in threads if row.get("community_id")}
    parsed_comments = coding.get("parsed_comment_count", 0)
    if not isinstance(parsed_comments, int) or isinstance(parsed_comments, bool):
        raise AcquisitionYieldReportError("parsed_comment_count must be an integer")

    social = families.get("native_social", {})
    posts = _objects(
        social.get("posts", []) if isinstance(social, Mapping) else [],
        label="native_social.posts",
    )
    creators = {str(row.get("creator_id")) for row in posts if row.get("creator_id")}
    independent_creators = {
        str(row.get("creator_id"))
        for row in posts
        if row.get("relationship") == "apparently_independent" and row.get("creator_id")
    }
    owned_posts = sum(row.get("relationship") == "owned" for row in posts)

    rows = [
        (
            "External company, editorial and industry context",
            f"{len(external_units)} units",
            f"{len(qualifying_external_origins)} qualifying independent consumer/trade origins",
            "Company context and non-retailer corroboration",
            "Non-qualifying company/profile/relationship rows do not earn independent axis credit",
        ),
        (
            "Retailer reviews",
            f"{sum(denominators.values())} eligible text rows",
            f"{len(corpora)} distinct corpora",
            "Captured-sample axis incidence and explicit choice outcomes",
            "Not a market return, rejection, or population-prevalence rate",
        ),
        (
            "Reddit/forums",
            f"{len(threads)} source-native threads; {parsed_comments} parsed comments",
            f"{len(communities)} communities",
            "Corroboration, comparison, contradiction, and sharpening",
            "Discovery-targeted qualitative evidence, not representative sentiment",
        ),
        (
            "Native social",
            f"{len(posts)} posts; {len(creators)} creators",
            f"{len(independent_creators)} apparently independent creators; {owned_posts} owned posts",
            "Creator narratives and owned-direction evidence",
            "Not a complete creator landscape or prevalence sample",
        ),
    ]
    return _table(
        ("Family", "Usable volume", "Distribution", "Supports", "Ceiling"), rows
    )


def _support_origin_maps(families: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    social = families.get("native_social", {})
    social_rows = _objects(
        social.get("posts", []) if isinstance(social, Mapping) else [],
        label="native_social.posts",
    )
    social_origins = {
        str(row["unit_id"]): str(row["creator_id"])
        for row in social_rows
        if row.get("unit_id")
        and row.get("creator_id")
        and row.get("independence") == "independent_post"
        and row.get("relationship") == "apparently_independent"
    }
    external = families.get("external_context", {})
    external_rows = _objects(
        external.get("units", []) if isinstance(external, Mapping) else [],
        label="external_context.units",
    )
    external_origins = {
        str(row["unit_id"]): str(row["origin_id"])
        for row in external_rows
        if row.get("unit_id")
        and row.get("origin_id")
        and row.get("independence") == "independent_origin"
        and row.get("relationship") == "apparently_independent"
        and row.get("source_type") in {"consumer_editorial", "trade_press"}
    }
    return social_origins, external_origins


def render_phase_a_acquisition_yield(
    *,
    ledger: Mapping[str, Any],
    community_coding: Mapping[str, Any],
    search_rounds: Sequence[Mapping[str, Any]],
) -> str:
    """Render the acquisition-yield section from evidence-bearing inputs.

    ``search_rounds`` supplies the non-derivable intent for each executed round.
    All counts and dispositions are recomputed from the ledger and coding.
    """

    frontier = ledger.get("reddit_candidate_frontier")
    if not isinstance(frontier, Mapping):
        raise AcquisitionYieldReportError("missing reddit_candidate_frontier")
    jobs = _objects(frontier.get("discovery_jobs"), label="discovery_jobs")
    candidates = _objects(frontier.get("candidates"), label="candidates")
    query_families = _objects(
        frontier.get("query_families"), label="query_families"
    )
    closure = ledger.get("closure")
    if not isinstance(closure, Mapping):
        raise AcquisitionYieldReportError("missing closure")
    closure_batches = _objects(closure.get("batches"), label="closure.batches")
    coding_rows = _objects(community_coding.get("rows"), label="community coding rows")
    axes = _objects(ledger.get("product_axes"), label="product_axes")
    families = ledger.get("families")
    if not isinstance(families, Mapping):
        raise AcquisitionYieldReportError("ledger families must be an object")

    jobs_by_id: dict[str, Mapping[str, Any]] = {}
    for row in jobs:
        job_id = _text(row.get("job_id"), label="discovery job_id")
        if job_id in jobs_by_id:
            raise AcquisitionYieldReportError(f"duplicate discovery job: {job_id}")
        jobs_by_id[job_id] = row

    family_by_job: dict[str, str] = {}
    family_by_id: dict[str, Mapping[str, Any]] = {}
    for family in query_families:
        family_id = _text(family.get("family_id"), label="query family_id")
        if family_id in family_by_id:
            raise AcquisitionYieldReportError(f"duplicate query family: {family_id}")
        family_by_id[family_id] = family
        family_job_ids = family.get("job_ids")
        if not isinstance(family_job_ids, list) or not family_job_ids:
            raise AcquisitionYieldReportError(f"query family {family_id} has no jobs")
        for job_id in map(str, family_job_ids):
            if job_id in family_by_job:
                raise AcquisitionYieldReportError(
                    f"search job assigned to multiple query families: {job_id}"
                )
            family_by_job[job_id] = family_id
    if set(family_by_job) != set(jobs_by_id):
        raise AcquisitionYieldReportError("discovery jobs are not fully assigned to query families")

    batch_by_family: dict[str, Mapping[str, Any]] = {}
    for batch in closure_batches:
        family_id = _text(batch.get("query_family_id"), label="batch query_family_id")
        if family_id in batch_by_family:
            raise AcquisitionYieldReportError(
                f"duplicate closure batch for query family: {family_id}"
            )
        batch_by_family[family_id] = batch

    candidate_by_id: dict[str, Mapping[str, Any]] = {}
    for row in candidates:
        thread_id = _text(row.get("thread_id"), label="candidate thread_id")
        if thread_id in candidate_by_id:
            raise AcquisitionYieldReportError(f"duplicate candidate: {thread_id}")
        candidate_by_id[thread_id] = row

    normalized_rounds: list[dict[str, Any]] = []
    seen_rounds: set[str] = set()
    assigned_jobs: set[str] = set()
    for raw in search_rounds:
        if not isinstance(raw, Mapping):
            raise AcquisitionYieldReportError("every search round must be an object")
        round_id = _text(raw.get("round_id"), label="round_id")
        if round_id in seen_rounds:
            raise AcquisitionYieldReportError(f"duplicate round_id: {round_id}")
        seen_rounds.add(round_id)
        job_ids_value = raw.get("job_ids")
        if not isinstance(job_ids_value, list) or not job_ids_value:
            raise AcquisitionYieldReportError(f"round {round_id} has no job_ids")
        job_ids = [_text(value, label=f"round {round_id} job_id") for value in job_ids_value]
        if len(job_ids) != len(set(job_ids)):
            raise AcquisitionYieldReportError(f"round {round_id} repeats a job_id")
        unknown = set(job_ids) - set(jobs_by_id)
        if unknown:
            raise AcquisitionYieldReportError(
                f"round {round_id} references unknown jobs: {sorted(unknown)}"
            )
        overlap = set(job_ids) & assigned_jobs
        if overlap:
            raise AcquisitionYieldReportError(
                f"search jobs assigned to multiple rounds: {sorted(overlap)}"
            )
        assigned_jobs.update(job_ids)
        normalized_rounds.append(
            {
                "round_id": round_id,
                "purpose": _text(raw.get("purpose"), label=f"round {round_id} purpose"),
                "launch_reason": _text(
                    raw.get("launch_reason"), label=f"round {round_id} launch_reason"
                ),
                "distinction": _text(
                    raw.get("distinction"), label=f"round {round_id} distinction"
                ),
                "job_ids": job_ids,
            }
        )

    coding_axes_by_thread: dict[str, set[str]] = defaultdict(set)
    for row in coding_rows:
        thread_id = _text(row.get("thread_id"), label="coding thread_id")
        axis_ids = row.get("axis_ids")
        if not isinstance(axis_ids, list) or not axis_ids:
            raise AcquisitionYieldReportError(f"coding row {thread_id} has no axis_ids")
        coding_axes_by_thread[thread_id].update(str(axis_id) for axis_id in axis_ids)

    reddit = families.get("reddit_forum", {})
    reddit_rows = _objects(
        reddit.get("threads", []) if isinstance(reddit, Mapping) else [],
        label="reddit_forum.threads",
    )
    reddit_thread_ids = {
        _text(row.get("thread_id"), label="reddit thread_id") for row in reddit_rows
    }
    for thread_id, candidate in candidate_by_id.items():
        if candidate.get("terminal_state") != "captured_used":
            continue
        if thread_id not in reddit_thread_ids:
            raise AcquisitionYieldReportError(
                f"captured_used candidate is absent from the Reddit evidence family: {thread_id}"
            )
        if thread_id not in coding_axes_by_thread:
            raise AcquisitionYieldReportError(
                f"captured_used candidate has no community coding row: {thread_id}"
            )

    round_rows: list[tuple[Any, ...]] = []
    query_rows: list[tuple[Any, ...]] = []
    all_round_job_ids: set[str] = set()
    round_yield: list[tuple[str, int, int, set[str], set[str]]] = []
    for round_row in normalized_rounds:
        job_ids = set(round_row["job_ids"])
        all_round_job_ids.update(job_ids)
        axes_covered = {
            str(jobs_by_id[job_id].get("axis_id")) for job_id in round_row["job_ids"]
        }
        surfaced: set[str] = set()
        repeat_sightings = 0
        for job_id in round_row["job_ids"]:
            job = jobs_by_id[job_id]
            surfaced_values = job.get("surfaced_thread_ids", job.get("candidate_thread_ids", []))
            if not isinstance(surfaced_values, list):
                raise AcquisitionYieldReportError(f"job {job_id} has invalid surfaced_thread_ids")
            job_surfaced = {str(value) for value in surfaced_values if str(value)}
            surfaced.update(job_surfaced)
            repeat_sightings += sum(
                candidate_by_id.get(thread_id, {}).get("discovered_by_job_id") != job_id
                for thread_id in job_surfaced
                if thread_id in candidate_by_id
            )

        first_seen_rows = [
            row for row in candidates if row.get("discovered_by_job_id") in job_ids
        ]
        states = Counter(str(row.get("terminal_state")) for row in first_seen_rows)
        usable = states["captured_used"]
        round_family_ids = {family_by_job[job_id] for job_id in job_ids}
        material_additions = [
            addition
            for family_id in round_family_ids
            for addition in batch_by_family.get(family_id, {}).get(
                "material_additions", []
            )
            if isinstance(addition, Mapping)
        ]
        round_yield.append(
            (
                round_row["round_id"],
                usable,
                len(material_additions),
                axes_covered,
                round_family_ids,
            )
        )
        round_rows.append(
            (
                round_row["round_id"],
                round_row["launch_reason"],
                round_row["distinction"],
                ", ".join(sorted(round_family_ids)),
                f"{len(job_ids)} jobs / {len(axes_covered)} axes",
                len(surfaced),
                len(first_seen_rows),
                usable,
                states["dominated"],
                states["captured_excluded"],
                states["blocked"],
                repeat_sightings,
                _percent(usable, len(first_seen_rows)),
                len(material_additions),
            )
        )
        for job_id in round_row["job_ids"]:
            job = jobs_by_id[job_id]
            job_surfaced_values = job.get(
                "surfaced_thread_ids", job.get("candidate_thread_ids", [])
            )
            job_surfaced = {
                str(value) for value in job_surfaced_values if str(value)
            }
            first_seen = [
                row for row in candidates if row.get("discovered_by_job_id") == job_id
            ]
            useful = sum(row.get("terminal_state") == "captured_used" for row in first_seen)
            query_rows.append(
                (
                    job_id,
                    job.get("axis_id", "unknown"),
                    job.get("query", ""),
                    round_row["purpose"],
                    len(job_surfaced),
                    len(first_seen),
                    useful,
                    ", ".join(str(value) for value in job.get("artifact_ids", [])),
                )
            )

    social_origins, external_origins = _support_origin_maps(families)
    axis_rows: list[tuple[Any, ...]] = []
    for axis in axes:
        axis_id = _text(axis.get("axis_id"), label="axis_id")
        relevant_coding = [
            row for row in coding_rows if axis_id in set(map(str, row.get("axis_ids", [])))
        ]
        reddit_threads = {str(row["thread_id"]) for row in relevant_coding}
        round_added = {
            thread_id
            for thread_id in reddit_threads
            if candidate_by_id.get(thread_id, {}).get("discovered_by_job_id")
            in all_round_job_ids
            and candidate_by_id.get(thread_id, {}).get("terminal_state") == "captured_used"
        }
        contribution_counts = Counter(str(row.get("contribution")) for row in relevant_coding)
        contributions = ", ".join(
            f"{key} {value}" for key, value in sorted(contribution_counts.items())
        ) or "none"
        outcomes = Counter(
            str(row.get("explicit_outcome"))
            for row in relevant_coding
            if row.get("explicit_outcome") not in {None, "none_explicit"}
        )
        outcome_text = ", ".join(f"{key} {value}" for key, value in sorted(outcomes.items())) or "none explicit"
        alternatives = sorted(
            {str(row["alternative_brand"]) for row in relevant_coding if row.get("alternative_brand")}
        )

        reddit_origins: set[str] = set()
        social_axis_origins: set[str] = set()
        external_axis_origins: set[str] = set()
        for ref in _objects(axis.get("support_refs"), label=f"support_refs:{axis_id}"):
            family = ref.get("family")
            unit_id = str(ref.get("unit_id") or "")
            if family == "reddit_forum" and unit_id:
                reddit_origins.add(unit_id)
            elif family == "native_social" and unit_id in social_origins:
                social_axis_origins.add(social_origins[unit_id])
            elif family == "external_context" and unit_id in external_origins:
                external_axis_origins.add(external_origins[unit_id])
        spread = (
            f"Reddit {len(reddit_origins)}; creators {len(social_axis_origins)}; "
            f"external {len(external_axis_origins)}"
        )
        incidence_parts = []
        for row in _objects(axis.get("retailer_incidence"), label=f"retailer_incidence:{axis_id}"):
            incidence_parts.append(
                f"{row.get('corpus_id')}: {row.get('axis_mention_count')}/"
                f"{row.get('eligible_text_review_count')} mentions; "
                f"choice -{row.get('negative_choice_review_count')}/+"
                f"{row.get('positive_choice_review_count')}"
            )
        axis_rows.append(
            (
                axis.get("label", axis_id),
                axis.get("polarity", "unknown"),
                axis.get("strength", "unknown"),
                axis.get("decision_maturity", "unknown"),
                axis.get("closure_basis", "unknown"),
                axis.get("claim_ceiling", "unknown"),
                spread,
                f"{len(reddit_threads)} total; {len(round_added)} added by reported rounds",
                contributions,
                outcome_text,
                ", ".join(alternatives) if alternatives else "none named",
                "; ".join(incidence_parts),
            )
        )

    final_lines: list[str] = []
    frontier_rows = []
    for axis in axes:
        if axis.get("disposition") not in {"material", "blocked_material"}:
            continue
        axis_id = _text(axis.get("axis_id"), label="axis_id")
        frontier_ids = axis.get("decision_frontier_family_ids")
        if not isinstance(frontier_ids, list):
            frontier_ids = []
        family_details = []
        for family_id in map(str, frontier_ids):
            batch = batch_by_family.get(family_id, {})
            additions = [
                addition
                for addition in batch.get("material_additions", [])
                if isinstance(addition, Mapping)
                and axis_id in set(map(str, addition.get("axis_ids", [])))
            ]
            family_details.append(
                f"{family_id}: usable {batch.get('new_usable_reddit_threads', 'unknown')}, "
                f"material {len(additions)}"
            )
        frontier_rows.append(
            (
                axis.get("label", axis_id),
                axis.get("decision_maturity", "unknown"),
                axis.get("closure_basis", "unknown"),
                axis.get("claim_ceiling", "unknown"),
                "; ".join(family_details) or "not declared",
            )
        )
    final_lines.append(
        "A useful thread may sharpen the record without changing a decision. "
        "Only structured material additions reopen an affected axis; the "
        "acquisition-seal validator still owns the completion decision."
    )
    final_lines.append(
        _table(
            (
                "Axis",
                "Decision maturity",
                "Closure basis",
                "Claim ceiling",
                "Two-family frontier (usable vs material)",
            ),
            frontier_rows,
        )
    )

    return "\n\n".join(
        [
            "## Evidence at a glance\n\n" + _family_scorecard(ledger, community_coding),
            "## Search design and yield\n\n"
            "A useful thread is a source-native captured Reddit body that clears the "
            "run's admission floor and carries at least one exact community-axis coding "
            "row. Discovery yield is an acquisition-process rate, not customer prevalence.\n\n"
            + _table(
                (
                    "Round",
                    "Why it ran",
                    "How it differed",
                    "Query family",
                    "Coverage",
                    "Unique surfaced",
                    "First-seen",
                    "Useful",
                    "Pre-capture excluded",
                    "Captured excluded",
                    "Blocked",
                    "Repeat sightings",
                    "Discovery yield",
                    "Material additions",
                ),
                round_rows,
            ),
            "## Product-axis decision support\n\n"
            "This is evidence accounting, not Deliver synthesis or a recommendation about how to compete.\n\n"
            + _table(
                (
                    "Axis",
                    "Polarity",
                    "Strength",
                    "Decision maturity",
                    "Closure basis",
                    "Claim ceiling",
                    "Qualifying non-retailer spread",
                    "Reddit threads",
                    "Contribution rows",
                    "Explicit outcomes",
                    "Named alternatives",
                    "Retailer captured-sample incidence",
                ),
                axis_rows,
            ),
            "## Exact search register\n\n"
            + _table(
                (
                    "Job",
                    "Axis",
                    "Exact query",
                    "Purpose",
                    "Surfaced",
                    "First-seen",
                    "Useful",
                    "Pinned result artifacts",
                ),
                query_rows,
            ),
            "## Decision-frontier observation\n\n" + "\n\n".join(final_lines),
        ]
    ) + "\n"
