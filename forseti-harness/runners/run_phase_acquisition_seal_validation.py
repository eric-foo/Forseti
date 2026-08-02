"""Validate acquisition accounting and evidence depth in an Understanding seal."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import hash_file, sha256_bytes  # noqa: E402


SEAL_VERSION = "phase_acquisition_seal_v3"
LEGACY_SEAL_VERSION = "phase_acquisition_seal_v2"
DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v1"
BROAD_UNDERSTANDING_PROFILE = "broad_company_understanding_v1"
CONSUMER_DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v2"
CONSUMER_BRAND_UNDERSTANDING_PROFILE = (
    "broad_consumer_brand_understanding_v1"
)
BROAD_UNDERSTANDING_FLOORS = {
    "outside_in_independent_units": 12,
    "outside_in_independent_origins": 12,
    "retailer_review_unique_rows": 750,
    "retailer_review_corpora": 2,
    "retailer_review_product_contexts": 5,
    "retailer_review_categories": 3,
    "reddit_forum_threads": 20,
    "reddit_forum_communities": 4,
    "reddit_forum_topic_categories": 3,
    "native_social_posts": 30,
    "native_social_creators": 20,
    "native_social_platforms": 2,
    "native_social_perspectives": 2,
}
CONSUMER_BRAND_UNDERSTANDING_FLOORS = {
    **{
        key: value
        for key, value in BROAD_UNDERSTANDING_FLOORS.items()
        if not key.startswith("outside_in_")
    },
    "external_context_independent_units": 12,
    "external_context_independent_origins": 12,
}

_EXTERNAL_CONTEXT_SOURCE_TYPES = {
    "corporate_or_transaction",
    "trade_press",
    "consumer_editorial",
    "company_profile",
    "other_external",
}
_SOCIAL_RELATIONSHIPS = {
    "owned",
    "retailer_operated",
    "disclosed_paid_or_affiliate",
    "apparently_independent",
    "relationship_unknown",
}
_QUALIFYING_SOCIAL_RELATIONSHIPS = {"apparently_independent"}
_AXIS_POLARITIES = {"pain", "delight", "mixed"}
_AXIS_STRENGTHS = {"signal", "recurring", "strong"}
_AXIS_DISPOSITIONS = {
    "material",
    "bounded_nonmaterial",
    "merged",
    "blocked_material",
}
_FOCUSED_SEARCH_GOALS = {
    "corroborate_or_segment",
    "disconfirm_or_compare",
}
_FOCUSED_SEARCH_TERMINALS = {
    "captured",
    "no_material_yield",
    "dominated",
    "blocked_no_route",
}
_INCENTIVE_STATES = {
    "disclosed_incentivized",
    "not_marked_incentivized",
    "unknown",
}
_CHOICE_OUTCOMES = {
    "returned_or_refunded",
    "return_intended",
    "stopped_or_discarded",
    "switched_or_replaced",
    "reduced_use",
    "no_future_purchase",
    "retained_or_repurchased",
    "none_explicit",
}
_NEGATIVE_CHOICE_OUTCOMES = _CHOICE_OUTCOMES - {
    "retained_or_repurchased",
    "none_explicit",
}
_POSITIVE_CHOICE_OUTCOMES = {"retained_or_repurchased"}
MANDATORY_ROUTE_IDS = {
    "serp_phase1",
    "official_retailer_authorization",
    "google_ads_transparency",
    "meta_ads_library",
    "retailer_full_pdp",
    "reddit_weekly_lake",
    "reddit_community_scout",
    "serp_phase2",
}
MANDATORY_ROUTE_PHASES = {
    "serp_phase1": "serp_phase1",
    "official_retailer_authorization": "co1",
    "google_ads_transparency": "co1",
    "meta_ads_library": "co1",
    "retailer_full_pdp": "co2",
    "reddit_weekly_lake": "co3",
    "reddit_community_scout": "co3",
    "serp_phase2": "serp_phase2",
}
_YAML_FENCE = re.compile(r"```yaml\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_TEXT_ARTIFACT_SUFFIXES = {".json", ".md", ".yaml", ".yml"}


def validate_phase_acquisition_seal(
    *,
    seal_path: Path,
    repo_root: Path,
    allow_legacy_v2: bool = False,
) -> list[str]:
    seal = _load_seal(seal_path)
    findings: list[str] = []
    schema_version = seal.get("schema_version")
    if schema_version == LEGACY_SEAL_VERSION and not allow_legacy_v2:
        findings.append("legacy_v2_requires_explicit_historical_audit")
    elif schema_version not in {SEAL_VERSION, LEGACY_SEAL_VERSION}:
        findings.append("invalid_schema_version")

    gate = seal.get("acquisition_gate")
    seal_state = seal.get("seal_state")
    deliver_allowed = seal.get("deliver_allowed")
    valid_pass = (
        gate == "pass"
        and seal_state == "SEALED_READY_FOR_DELIVER"
        and deliver_allowed is True
    )
    valid_block = (
        gate == "blocked"
        and seal_state == "BLOCKED_ACQUISITION_INCOMPLETE"
        and deliver_allowed is False
    )
    if not (valid_pass or valid_block):
        findings.append("inconsistent_gate_state")

    _validate_controller_placement(seal, findings)
    conditional_routes = _validate_capability_preflight(
        seal, valid_pass=valid_pass, findings=findings
    )
    _validate_specialist_returns(
        seal, repo_root=repo_root, findings=findings
    )
    material_pending = _validate_route_accounting(
        seal,
        repo_root=repo_root,
        valid_pass=valid_pass,
        conditional_routes=conditional_routes,
        findings=findings,
    )
    _validate_decision_receipt(seal, repo_root=repo_root, findings=findings)
    _validate_resume_contract(
        seal,
        repo_root=repo_root,
        expected_pending=material_pending,
        valid_pass=valid_pass,
        findings=findings,
    )
    if schema_version == SEAL_VERSION:
        _validate_understanding_evidence_depth(
            seal,
            repo_root=repo_root,
            valid_pass=valid_pass,
            findings=findings,
        )
    continuation = seal.get("post_phase1_continuation_mode")
    if continuation not in {"full", "bounded_salvage", "stop"}:
        findings.append("invalid_post_phase1_continuation_mode")
    elif valid_pass and continuation != "full":
        findings.append("passing_seal_requires_full_continuation")
    return sorted(set(findings))


def _validate_understanding_evidence_depth(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    valid_pass: bool,
    findings: list[str],
) -> None:
    reference = seal.get("evidence_depth_ledger")
    if not isinstance(reference, dict):
        findings.append("missing_evidence_depth_ledger")
        return
    locator = reference.get("locator")
    digest = reference.get("sha256")
    before = len(findings)
    _verify_artifact(
        locator,
        digest,
        repo_root=repo_root,
        code="evidence_depth_ledger",
        findings=findings,
    )
    if len(findings) != before:
        return
    ledger_path = Path(str(locator))
    if not ledger_path.is_absolute():
        ledger_path = repo_root / ledger_path
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(
            f"invalid_evidence_depth_ledger:{type(exc).__name__}"
        )
        return
    if not isinstance(ledger, dict):
        findings.append("invalid_evidence_depth_ledger_shape")
        return
    ledger_version = ledger.get("schema_version")
    profile_id = ledger.get("profile_id")
    if ledger_version not in {
        DEPTH_LEDGER_VERSION,
        CONSUMER_DEPTH_LEDGER_VERSION,
    }:
        findings.append("invalid_evidence_depth_ledger_version")
    if profile_id not in {
        BROAD_UNDERSTANDING_PROFILE,
        CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    }:
        findings.append("invalid_understanding_completion_profile")
    valid_profile_pair = (
        ledger_version == DEPTH_LEDGER_VERSION
        and profile_id == BROAD_UNDERSTANDING_PROFILE
    ) or (
        ledger_version == CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    if not valid_profile_pair:
        findings.append("understanding_profile_schema_mismatch")
    consumer_brand = ledger_version == CONSUMER_DEPTH_LEDGER_VERSION
    seal_subject = seal.get("subject")
    if not isinstance(seal_subject, str) or not seal_subject:
        findings.append("missing_seal_subject")
    elif ledger.get("subject") != seal_subject:
        findings.append("evidence_depth_ledger_subject_mismatch")
    seal_cycle_id = seal.get("cycle_id")
    if not isinstance(seal_cycle_id, str) or not seal_cycle_id:
        findings.append("missing_seal_cycle_id")
    elif ledger.get("cycle_id") != seal_cycle_id:
        findings.append("evidence_depth_ledger_cycle_id_mismatch")

    artifacts = _validate_depth_artifacts(
        ledger.get("artifacts"), repo_root=repo_root, findings=findings
    )
    families = ledger.get("families")
    if not isinstance(families, dict):
        findings.append("missing_evidence_depth_families")
        families = {}
    metrics: dict[str, int] = {}
    if consumer_brand:
        metrics.update(
            _validate_external_context_depth(
                families.get("external_context"),
                artifacts=artifacts,
                findings=findings,
            )
        )
    else:
        metrics.update(
            _validate_outside_in_depth(
                families.get("outside_in"),
                artifacts=artifacts,
                findings=findings,
            )
        )
    metrics.update(
        _validate_retailer_review_depth(
            families.get("retailer_reviews"),
            artifacts=artifacts,
            require_complete=valid_pass,
            findings=findings,
        )
    )
    metrics.update(
        _validate_reddit_depth(
            families.get("reddit_forum"), artifacts=artifacts, findings=findings
        )
    )
    metrics.update(
        _validate_native_social_depth(
            families.get("native_social"),
            artifacts=artifacts,
            consumer_brand=consumer_brand,
            findings=findings,
        )
    )
    product_axis_complete = True
    if consumer_brand:
        product_axis_complete = _validate_consumer_brand_product_axes(
            ledger,
            artifacts=artifacts,
            families=families,
            route_jobs=_route_job_states(seal),
            require_complete=valid_pass,
            findings=findings,
        )
    closure_complete = _validate_depth_closure(
        ledger.get("closure"),
        require_complete=valid_pass,
        consumer_brand=consumer_brand,
        findings=findings,
    )
    if valid_pass:
        floors = (
            CONSUMER_BRAND_UNDERSTANDING_FLOORS
            if consumer_brand
            else BROAD_UNDERSTANDING_FLOORS
        )
        for metric, minimum in floors.items():
            if metrics.get(metric, 0) < minimum:
                findings.append(f"passing_seal_below_depth_floor:{metric}")
        if not closure_complete:
            findings.append("passing_seal_without_saturation_closure")
        if consumer_brand and not product_axis_complete:
            findings.append("passing_consumer_brand_seal_without_axis_closure")


def _validate_depth_artifacts(
    value: Any,
    *,
    repo_root: Path,
    findings: list[str],
) -> dict[str, Path]:
    if not isinstance(value, list) or not value:
        findings.append("missing_evidence_depth_artifacts")
        return {}
    artifacts: dict[str, Path] = {}
    for row in value:
        if not isinstance(row, dict):
            findings.append("invalid_evidence_depth_artifact")
            continue
        artifact_id = row.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            findings.append("missing_evidence_depth_artifact_id")
            continue
        if artifact_id in artifacts:
            findings.append("duplicate_evidence_depth_artifact_id")
            continue
        locator = row.get("locator")
        path = Path(str(locator))
        if not path.is_absolute():
            path = repo_root / path
        artifacts[artifact_id] = path
        _verify_artifact(
            locator,
            row.get("sha256"),
            repo_root=repo_root,
            code="evidence_depth_source",
            findings=findings,
        )
    return artifacts


def _valid_depth_rows(
    value: Any,
    *,
    row_name: str,
    id_field: str,
    artifacts: Mapping[str, Path],
    findings: list[str],
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        findings.append(f"missing_{row_name}_rows")
        return []
    rows: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, dict):
            findings.append(f"invalid_{row_name}_row")
            continue
        row_id = row.get(id_field)
        if not isinstance(row_id, str) or not row_id:
            findings.append(f"missing_{row_name}_{id_field}")
            continue
        if row_id in seen:
            findings.append(f"duplicate_{row_name}_{id_field}")
            continue
        seen.add(row_id)
        artifact_id = row.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id not in artifacts:
            findings.append(f"unresolved_{row_name}_artifact")
        rows.append(row)
    return rows


def _string_set(value: Any, *, code: str, findings: list[str]) -> set[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        findings.append(code)
        return set()
    return set(value)


def _validate_outside_in_depth(
    value: Any, *, artifacts: Mapping[str, Path], findings: list[str]
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_outside_in_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("units"),
        row_name="outside_in",
        id_field="unit_id",
        artifacts=artifacts,
        findings=findings,
    )
    origins: set[str] = set()
    independent_units = 0
    for row in rows:
        origin = row.get("origin_id")
        if not isinstance(origin, str) or not origin:
            findings.append("missing_outside_in_origin_id")
            continue
        if row.get("independence") not in {
            "independent_origin",
            "same_origin",
            "syndicated_copy",
        }:
            findings.append("invalid_outside_in_independence")
            continue
        echo_group = row.get("echo_group_id")
        if not isinstance(echo_group, str) or not echo_group:
            findings.append("missing_outside_in_echo_group")
        if row.get("independence") == "independent_origin":
            independent_units += 1
            origins.add(origin)
    return {
        "outside_in_independent_units": independent_units,
        "outside_in_independent_origins": len(origins),
    }


def _validate_external_context_depth(
    value: Any,
    *,
    artifacts: Mapping[str, Path],
    findings: list[str],
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_external_context_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("units"),
        row_name="external_context",
        id_field="unit_id",
        artifacts=artifacts,
        findings=findings,
    )
    origins: set[str] = set()
    independent_units = 0
    for row in rows:
        origin = row.get("origin_id")
        if not isinstance(origin, str) or not origin:
            findings.append("missing_external_context_origin_id")
            continue
        independence = row.get("independence")
        if independence not in {
            "independent_origin",
            "same_origin",
            "syndicated_copy",
        }:
            findings.append("invalid_external_context_independence")
            continue
        echo_group = row.get("echo_group_id")
        if not isinstance(echo_group, str) or not echo_group:
            findings.append("missing_external_context_echo_group")
        if row.get("source_type") not in _EXTERNAL_CONTEXT_SOURCE_TYPES:
            findings.append("invalid_external_context_source_type")
        if independence == "independent_origin":
            independent_units += 1
            origins.add(origin)
    return {
        "external_context_independent_units": independent_units,
        "external_context_independent_origins": len(origins),
    }


def _validate_retailer_review_depth(
    value: Any,
    *,
    artifacts: Mapping[str, Path],
    require_complete: bool,
    findings: list[str],
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_retailer_review_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("corpora"),
        row_name="retailer_review",
        id_field="corpus_id",
        artifacts=artifacts,
        findings=findings,
    )
    total = 0
    product_contexts: set[str] = set()
    categories: set[str] = set()
    rating_bands: set[str] = set()
    for row in rows:
        unique_count = row.get("unique_review_count")
        duplicate_count = row.get("cross_corpus_duplicate_count")
        if (
            not isinstance(unique_count, int)
            or isinstance(unique_count, bool)
            or unique_count < 0
        ):
            findings.append("invalid_unique_review_count")
            unique_count = 0
        if (
            not isinstance(duplicate_count, int)
            or isinstance(duplicate_count, bool)
            or duplicate_count < 0
            or duplicate_count > unique_count
        ):
            findings.append("invalid_cross_corpus_duplicate_count")
            duplicate_count = 0
        total += unique_count - duplicate_count
        product_contexts.update(
            _string_set(
                row.get("product_context_ids"),
                code="invalid_retailer_review_product_contexts",
                findings=findings,
            )
        )
        categories.update(
            _string_set(
                row.get("category_ids"),
                code="invalid_retailer_review_categories",
                findings=findings,
            )
        )
        rating_bands.update(
            _string_set(
                row.get("rating_bands"),
                code="invalid_retailer_review_rating_bands",
                findings=findings,
            )
        )
    # Band completeness is part of the passing-seal entry floor, not a shape
    # requirement on an honestly partial blocked seal.
    if (
        require_complete
        and rows
        and not {"low", "mid", "high"}.issubset(rating_bands)
    ):
        findings.append("retailer_review_rating_bands_incomplete")
    return {
        "retailer_review_unique_rows": total,
        "retailer_review_corpora": len(rows),
        "retailer_review_product_contexts": len(product_contexts),
        "retailer_review_categories": len(categories),
    }


def _validate_reddit_depth(
    value: Any, *, artifacts: Mapping[str, Path], findings: list[str]
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_reddit_forum_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("threads"),
        row_name="reddit_forum",
        id_field="thread_id",
        artifacts=artifacts,
        findings=findings,
    )
    communities: set[str] = set()
    topics: set[str] = set()
    independent_threads = 0
    for row in rows:
        community = row.get("community_id")
        topic = row.get("topic_category")
        if not isinstance(community, str) or not community:
            findings.append("missing_reddit_forum_community")
        if not isinstance(topic, str) or not topic:
            findings.append("missing_reddit_forum_topic_category")
        if row.get("independence") not in {
            "independent_thread",
            "duplicate_thread",
        }:
            findings.append("invalid_reddit_forum_independence")
        elif row.get("independence") == "independent_thread":
            independent_threads += 1
            if isinstance(community, str) and community:
                communities.add(community)
            if isinstance(topic, str) and topic:
                topics.add(topic)
    return {
        "reddit_forum_threads": independent_threads,
        "reddit_forum_communities": len(communities),
        "reddit_forum_topic_categories": len(topics),
    }


def _validate_native_social_depth(
    value: Any,
    *,
    artifacts: Mapping[str, Path],
    consumer_brand: bool = False,
    findings: list[str],
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_native_social_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("posts"),
        row_name="native_social",
        id_field="unit_id",
        artifacts=artifacts,
        findings=findings,
    )
    creators: set[str] = set()
    platforms: set[str] = set()
    perspectives: set[str] = set()
    independent_posts = 0
    post_ids: set[tuple[str, str]] = set()
    for row in rows:
        platform = row.get("platform")
        post_id = row.get("post_id")
        creator_id = row.get("creator_id")
        perspective = row.get("perspective")
        if not isinstance(platform, str) or not platform:
            findings.append("missing_native_social_platform")
            platform = ""
        if not isinstance(post_id, str) or not post_id:
            findings.append("missing_native_social_post_id")
        elif (platform, post_id) in post_ids:
            findings.append("duplicate_native_social_post_id")
        else:
            post_ids.add((platform, post_id))
        if not isinstance(creator_id, str) or not creator_id:
            findings.append("missing_native_social_creator_id")
        if perspective not in {"positive", "neutral", "critical", "mixed"}:
            findings.append("invalid_native_social_perspective")
        if row.get("independence") not in {
            "independent_post",
            "same_creator_followup",
            "syndicated_copy",
        }:
            findings.append("invalid_native_social_independence")
        elif row.get("independence") == "independent_post":
            independent_posts += 1
            if platform:
                platforms.add(platform)
            if isinstance(creator_id, str) and creator_id:
                creators.add(creator_id)
            if perspective in {"positive", "neutral", "critical", "mixed"}:
                perspectives.add(str(perspective))
        if consumer_brand:
            relationship = row.get("relationship")
            if relationship not in _SOCIAL_RELATIONSHIPS:
                findings.append("invalid_native_social_relationship")
            if relationship == "owned":
                published_at = row.get("published_at")
                if not isinstance(published_at, str) or not published_at:
                    findings.append("missing_owned_social_published_at")
                direction_tags = row.get("direction_event_tags")
                if not isinstance(direction_tags, list) or not direction_tags or any(
                    not isinstance(item, str) or not item
                    for item in direction_tags
                ):
                    findings.append("invalid_owned_social_direction_event_tags")
    return {
        "native_social_posts": independent_posts,
        "native_social_creators": len(creators),
        "native_social_platforms": len(platforms),
        "native_social_perspectives": len(perspectives),
    }


def _route_job_states(seal: Mapping[str, Any]) -> dict[str, str]:
    states: dict[str, str] = {}
    rows = seal.get("route_job_accounting")
    if not isinstance(rows, list):
        return states
    for row in rows:
        if not isinstance(row, dict):
            continue
        for state in ("completed", "blocked", "unrun"):
            values = row.get(f"{state}_job_ids")
            if not isinstance(values, list):
                continue
            for job_id in values:
                if isinstance(job_id, str) and job_id:
                    states[job_id] = state
    return states


def _consumer_support_registry(
    families: Mapping[str, Any],
) -> dict[tuple[str, str], bool]:
    registry: dict[tuple[str, str], bool] = {}
    external = families.get("external_context")
    if isinstance(external, dict) and isinstance(external.get("units"), list):
        for row in external["units"]:
            if not isinstance(row, dict):
                continue
            unit_id = row.get("unit_id")
            if isinstance(unit_id, str) and unit_id:
                registry[("external_context", unit_id)] = (
                    row.get("independence") == "independent_origin"
                )
    reddit = families.get("reddit_forum")
    if isinstance(reddit, dict) and isinstance(reddit.get("threads"), list):
        for row in reddit["threads"]:
            if not isinstance(row, dict):
                continue
            thread_id = row.get("thread_id")
            if isinstance(thread_id, str) and thread_id:
                registry[("reddit_forum", thread_id)] = (
                    row.get("independence") == "independent_thread"
                )
    social = families.get("native_social")
    if isinstance(social, dict) and isinstance(social.get("posts"), list):
        for row in social["posts"]:
            if not isinstance(row, dict):
                continue
            unit_id = row.get("unit_id")
            if isinstance(unit_id, str) and unit_id:
                registry[("native_social", unit_id)] = (
                    row.get("independence") == "independent_post"
                    and row.get("relationship")
                    in _QUALIFYING_SOCIAL_RELATIONSHIPS
                )
    return registry


def _load_retailer_axis_coding(
    value: Any,
    *,
    ledger: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    retailer_corpora: Mapping[str, int],
    axis_ids: set[str],
    findings: list[str],
) -> tuple[dict[tuple[str, str], dict[str, int]], bool]:
    if not isinstance(value, dict):
        findings.append("missing_retailer_axis_coding")
        return {}, False
    artifact_id = value.get("artifact_id")
    if not isinstance(artifact_id, str) or artifact_id not in artifacts:
        findings.append("unresolved_retailer_axis_coding_artifact")
        return {}, False
    try:
        coding = json.loads(artifacts[artifact_id].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"invalid_retailer_axis_coding:{type(exc).__name__}")
        return {}, False
    if not isinstance(coding, dict):
        findings.append("invalid_retailer_axis_coding_shape")
        return {}, False
    complete = True
    if coding.get("schema_version") != "retailer_product_axis_coding_v1":
        findings.append("invalid_retailer_axis_coding_version")
        complete = False
    if coding.get("subject") != ledger.get("subject"):
        findings.append("retailer_axis_coding_subject_mismatch")
        complete = False
    if coding.get("cycle_id") != ledger.get("cycle_id"):
        findings.append("retailer_axis_coding_cycle_id_mismatch")
        complete = False

    boundaries = coding.get("corpora")
    boundary_map: dict[str, int] = {}
    if not isinstance(boundaries, list):
        findings.append("missing_retailer_axis_coding_boundaries")
        complete = False
    else:
        for row in boundaries:
            if not isinstance(row, dict):
                findings.append("invalid_retailer_axis_coding_boundary")
                complete = False
                continue
            corpus_id = row.get("corpus_id")
            if (
                not isinstance(corpus_id, str)
                or not corpus_id
                or corpus_id in boundary_map
            ):
                findings.append("invalid_retailer_axis_coding_corpus_id")
                complete = False
                continue
            eligible = row.get("eligible_text_review_count")
            excluded = row.get("excluded_no_usable_text_count")
            if (
                not isinstance(eligible, int)
                or isinstance(eligible, bool)
                or eligible < 0
                or not isinstance(excluded, int)
                or isinstance(excluded, bool)
                or excluded < 0
            ):
                findings.append("invalid_retailer_axis_coding_boundary_counts")
                complete = False
                continue
            boundary_map[corpus_id] = eligible
            expected = retailer_corpora.get(corpus_id)
            if expected is None:
                findings.append("unknown_retailer_axis_coding_corpus")
                complete = False
            elif eligible + excluded != expected:
                findings.append(
                    f"retailer_axis_coding_boundary_mismatch:{corpus_id}"
                )
                complete = False
    if set(boundary_map) != set(retailer_corpora):
        findings.append("retailer_axis_coding_corpora_incomplete")
        complete = False

    rows = coding.get("rows")
    counts: dict[tuple[str, str], dict[str, int]] = {}
    row_counts: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    if not isinstance(rows, list):
        findings.append("missing_retailer_axis_coding_rows")
        return counts, False
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_retailer_axis_coding_row")
            complete = False
            continue
        corpus_id = row.get("corpus_id")
        review_id = row.get("review_id")
        if not isinstance(corpus_id, str) or corpus_id not in boundary_map:
            findings.append("invalid_coded_review_corpus")
            complete = False
            continue
        if (
            not isinstance(review_id, str)
            or not review_id
            or (corpus_id, review_id) in seen
        ):
            findings.append("invalid_or_duplicate_coded_review_id")
            complete = False
            continue
        seen.add((corpus_id, review_id))
        row_counts[corpus_id] = row_counts.get(corpus_id, 0) + 1
        if not isinstance(row.get("product_context_id"), str) or not row.get(
            "product_context_id"
        ):
            findings.append("missing_coded_review_product_context")
            complete = False
        if row.get("incentive_state") not in _INCENTIVE_STATES:
            findings.append("invalid_coded_review_incentive_state")
            complete = False
        source_row_ref = row.get("source_row_ref")
        if not isinstance(source_row_ref, str) or not source_row_ref:
            findings.append("missing_coded_review_source_row_ref")
            complete = False
        row_axis_ids = _string_set(
            row.get("axis_ids"),
            code="invalid_coded_review_axis_ids",
            findings=findings,
        )
        unknown_axes = row_axis_ids - axis_ids
        if unknown_axes:
            findings.append("coded_review_references_unknown_axis")
            complete = False
        outcomes = _string_set(
            row.get("choice_outcomes"),
            code="invalid_coded_review_choice_outcomes",
            findings=findings,
        )
        if not outcomes or not outcomes.issubset(_CHOICE_OUTCOMES):
            findings.append("invalid_coded_review_choice_outcome")
            complete = False
        if "none_explicit" in outcomes and len(outcomes) > 1:
            findings.append("coded_review_none_outcome_conflict")
            complete = False
        for axis_id in row_axis_ids & axis_ids:
            key = (axis_id, corpus_id)
            aggregate = counts.setdefault(
                key,
                {
                    "axis_mention_count": 0,
                    "negative_choice_review_count": 0,
                    "positive_choice_review_count": 0,
                    "disclosed_incentivized_axis_mention_count": 0,
                },
            )
            aggregate["axis_mention_count"] += 1
            if outcomes & _NEGATIVE_CHOICE_OUTCOMES:
                aggregate["negative_choice_review_count"] += 1
            if outcomes & _POSITIVE_CHOICE_OUTCOMES:
                aggregate["positive_choice_review_count"] += 1
            if row.get("incentive_state") == "disclosed_incentivized":
                aggregate["disclosed_incentivized_axis_mention_count"] += 1
    for corpus_id, eligible in boundary_map.items():
        if row_counts.get(corpus_id, 0) != eligible:
            findings.append(f"retailer_axis_coding_row_count_mismatch:{corpus_id}")
            complete = False
        for axis_id in axis_ids:
            counts.setdefault(
                (axis_id, corpus_id),
                {
                    "axis_mention_count": 0,
                    "negative_choice_review_count": 0,
                    "positive_choice_review_count": 0,
                    "disclosed_incentivized_axis_mention_count": 0,
                },
            )["eligible_text_review_count"] = eligible
    return counts, complete


def _retailer_corpus_effective_counts(
    families: Mapping[str, Any],
) -> dict[str, int]:
    result: dict[str, int] = {}
    family = families.get("retailer_reviews")
    if not isinstance(family, dict) or not isinstance(family.get("corpora"), list):
        return result
    for row in family["corpora"]:
        if not isinstance(row, dict):
            continue
        corpus_id = row.get("corpus_id")
        unique = row.get("unique_review_count")
        duplicate = row.get("cross_corpus_duplicate_count")
        if (
            isinstance(corpus_id, str)
            and corpus_id
            and isinstance(unique, int)
            and not isinstance(unique, bool)
            and isinstance(duplicate, int)
            and not isinstance(duplicate, bool)
            and 0 <= duplicate <= unique
        ):
            result[corpus_id] = unique - duplicate
    return result


def _validate_axis_incidence(
    axis: Mapping[str, Any],
    *,
    axis_id: str,
    coding_counts: Mapping[tuple[str, str], Mapping[str, int]],
    corpora: set[str],
    findings: list[str],
) -> tuple[int, int, int]:
    value = axis.get("retailer_incidence")
    if not isinstance(value, list):
        findings.append(f"missing_product_axis_incidence:{axis_id}")
        return 0, 0, 0
    seen: set[str] = set()
    corpora_with_mentions = 0
    negative_choices = 0
    positive_choices = 0
    fields = (
        "eligible_text_review_count",
        "axis_mention_count",
        "negative_choice_review_count",
        "positive_choice_review_count",
        "disclosed_incentivized_axis_mention_count",
    )
    for row in value:
        if not isinstance(row, dict):
            findings.append(f"invalid_product_axis_incidence:{axis_id}")
            continue
        corpus_id = row.get("corpus_id")
        if (
            not isinstance(corpus_id, str)
            or corpus_id not in corpora
            or corpus_id in seen
        ):
            findings.append(f"invalid_product_axis_incidence_corpus:{axis_id}")
            continue
        seen.add(corpus_id)
        expected = coding_counts.get((axis_id, corpus_id), {})
        for field in fields:
            observed = row.get(field)
            if observed != expected.get(field, 0):
                findings.append(
                    f"retailer_axis_incidence_mismatch:{axis_id}:{corpus_id}:{field}"
                )
        mentions = expected.get("axis_mention_count", 0)
        if mentions > 0:
            corpora_with_mentions += 1
        negative_choices += expected.get("negative_choice_review_count", 0)
        positive_choices += expected.get("positive_choice_review_count", 0)
    if seen != corpora:
        findings.append(f"product_axis_incidence_corpora_incomplete:{axis_id}")
    return corpora_with_mentions, negative_choices, positive_choices


def _validate_focused_search_jobs(
    axis: Mapping[str, Any],
    *,
    axis_id: str,
    route_jobs: Mapping[str, str],
    required: bool,
    findings: list[str],
) -> bool:
    value = axis.get("focused_search_jobs")
    if not isinstance(value, list):
        if required:
            findings.append(f"missing_product_axis_focused_search:{axis_id}")
        return not required
    goals: set[str] = set()
    job_ids: set[str] = set()
    complete = True
    for row in value:
        if not isinstance(row, dict):
            findings.append(f"invalid_product_axis_focused_search:{axis_id}")
            complete = False
            continue
        goal = row.get("goal")
        job_id = row.get("job_id")
        disposition = row.get("disposition")
        if goal not in _FOCUSED_SEARCH_GOALS or goal in goals:
            findings.append(f"invalid_product_axis_search_goal:{axis_id}")
            complete = False
        else:
            goals.add(str(goal))
        if not isinstance(job_id, str) or not job_id or job_id in job_ids:
            findings.append(f"invalid_product_axis_search_job_id:{axis_id}")
            complete = False
        else:
            job_ids.add(job_id)
            state = route_jobs.get(job_id)
            if state is None:
                findings.append(f"unaccounted_product_axis_search_job:{axis_id}")
                complete = False
            elif state == "unrun":
                findings.append(f"unrun_product_axis_search_job:{axis_id}")
                complete = False
            elif disposition == "blocked_no_route" and state != "blocked":
                findings.append(f"product_axis_search_state_mismatch:{axis_id}")
                complete = False
            elif disposition != "blocked_no_route" and state != "completed":
                findings.append(f"product_axis_search_state_mismatch:{axis_id}")
                complete = False
        if disposition not in _FOCUSED_SEARCH_TERMINALS:
            findings.append(f"invalid_product_axis_search_disposition:{axis_id}")
            complete = False
    if required and goals != _FOCUSED_SEARCH_GOALS:
        findings.append(f"incomplete_product_axis_search_goals:{axis_id}")
        complete = False
    return complete


def _validate_consumer_brand_product_axes(
    ledger: Mapping[str, Any],
    *,
    artifacts: Mapping[str, Path],
    families: Mapping[str, Any],
    route_jobs: Mapping[str, str],
    require_complete: bool,
    findings: list[str],
) -> bool:
    axes = ledger.get("product_axes")
    if not isinstance(axes, list) or not axes:
        findings.append("missing_consumer_brand_product_axes")
        axes = []
        complete = False
    else:
        complete = True
    axis_rows: dict[str, Mapping[str, Any]] = {}
    for row in axes:
        if not isinstance(row, dict):
            findings.append("invalid_consumer_brand_product_axis")
            complete = False
            continue
        axis_id = row.get("axis_id")
        if (
            not isinstance(axis_id, str)
            or not axis_id
            or axis_id in axis_rows
        ):
            findings.append("invalid_or_duplicate_product_axis_id")
            complete = False
            continue
        axis_rows[axis_id] = row
        if not isinstance(row.get("label"), str) or not row.get("label"):
            findings.append(f"missing_product_axis_label:{axis_id}")
            complete = False
        if not isinstance(row.get("scope"), str) or not row.get("scope"):
            findings.append(f"missing_product_axis_scope:{axis_id}")
            complete = False
        if row.get("polarity") not in _AXIS_POLARITIES:
            findings.append(f"invalid_product_axis_polarity:{axis_id}")
            complete = False
        if row.get("strength") not in _AXIS_STRENGTHS:
            findings.append(f"invalid_product_axis_strength:{axis_id}")
            complete = False
        if row.get("disposition") not in _AXIS_DISPOSITIONS:
            findings.append(f"invalid_product_axis_disposition:{axis_id}")
            complete = False
        if require_complete and row.get("disposition") == "blocked_material":
            findings.append(f"blocked_material_product_axis:{axis_id}")
            complete = False

    retailer_corpora = _retailer_corpus_effective_counts(families)
    coding_counts, coding_complete = _load_retailer_axis_coding(
        ledger.get("retailer_axis_coding"),
        ledger=ledger,
        artifacts=artifacts,
        retailer_corpora=retailer_corpora,
        axis_ids=set(axis_rows),
        findings=findings,
    )
    complete = complete and coding_complete
    registry = _consumer_support_registry(families)
    for axis_id, axis in axis_rows.items():
        refs = axis.get("support_refs")
        family_counts: dict[str, int] = {}
        seen_refs: set[tuple[str, str]] = set()
        if not isinstance(refs, list):
            findings.append(f"missing_product_axis_support_refs:{axis_id}")
            refs = []
            complete = False
        for ref in refs:
            if not isinstance(ref, dict):
                findings.append(f"invalid_product_axis_support_ref:{axis_id}")
                complete = False
                continue
            family = ref.get("family")
            unit_id = ref.get("unit_id")
            key = (str(family), str(unit_id))
            if (
                family not in {"external_context", "reddit_forum", "native_social"}
                or not isinstance(unit_id, str)
                or not unit_id
                or key in seen_refs
            ):
                findings.append(f"invalid_or_duplicate_product_axis_support_ref:{axis_id}")
                complete = False
                continue
            seen_refs.add(key)
            qualifies = registry.get(key)
            if qualifies is None:
                findings.append(f"unresolved_product_axis_support_ref:{axis_id}")
                complete = False
            elif qualifies:
                family_counts[str(family)] = family_counts.get(str(family), 0) + 1

        corpora_with_mentions, negative_choices, positive_choices = (
            _validate_axis_incidence(
                axis,
                axis_id=axis_id,
                coding_counts=coding_counts,
                corpora=set(retailer_corpora),
                findings=findings,
            )
        )
        independent_support = sum(family_counts.values())
        recurring = independent_support >= 3 and len(family_counts) >= 2
        strong_distribution = (
            independent_support >= 6
            and len(family_counts) >= 2
            and sum(value >= 2 for value in family_counts.values()) >= 2
        )
        polarity = axis.get("polarity")
        choice_supported = (
            negative_choices > 0
            if polarity == "pain"
            else positive_choices > 0
            if polarity == "delight"
            else negative_choices + positive_choices > 0
        )
        strong = (
            strong_distribution
            and corpora_with_mentions >= 2
            and choice_supported
        )
        expected_strength = "strong" if strong else "recurring" if recurring else "signal"
        if axis.get("strength") != expected_strength:
            findings.append(
                f"product_axis_strength_mismatch:{axis_id}:{expected_strength}"
            )
            complete = False
        search_required = axis.get("disposition") in {
            "material",
            "blocked_material",
        }
        if not _validate_focused_search_jobs(
            axis,
            axis_id=axis_id,
            route_jobs=route_jobs,
            required=search_required,
            findings=findings,
        ):
            complete = False
    return complete


def _validate_depth_closure(
    value: Any,
    *,
    require_complete: bool,
    consumer_brand: bool = False,
    findings: list[str],
) -> bool:
    if not isinstance(value, dict):
        findings.append("missing_evidence_depth_closure")
        return False
    complete = True
    echo_state = value.get("echo_groups_adjudicated")
    if not isinstance(echo_state, bool):
        findings.append("invalid_echo_group_adjudication_state")
        complete = False
    elif echo_state is not True:
        if require_complete:
            findings.append("echo_groups_not_adjudicated")
        complete = False
    seams = value.get("material_seams")
    if not isinstance(seams, list) or not seams:
        findings.append("missing_material_seam_accounting")
        complete = False
    else:
        seam_ids: set[str] = set()
        for row in seams:
            if not isinstance(row, dict):
                findings.append("invalid_material_seam")
                complete = False
                continue
            seam_id = row.get("seam_id")
            if not isinstance(seam_id, str) or not seam_id or seam_id in seam_ids:
                findings.append("invalid_material_seam_id")
                complete = False
            else:
                seam_ids.add(seam_id)
            disposition = row.get("disposition")
            if disposition not in {
                "supported",
                "contradicted",
                "bounded",
                "blocked_no_remaining_path",
                "open",
                "blocked_route_available",
            }:
                findings.append("invalid_material_seam_disposition")
                complete = False
            elif disposition in {"open", "blocked_route_available"}:
                if require_complete:
                    findings.append("open_material_seam")
                complete = False
    batches = value.get("batches")
    if not isinstance(batches, list):
        findings.append("invalid_saturation_batches")
        complete = False
    elif len(batches) < 2:
        if require_complete:
            findings.append("insufficient_saturation_batches")
        complete = False
    else:
        for row in batches[-2:]:
            if not isinstance(row, dict):
                findings.append("invalid_saturation_batch")
                complete = False
                continue
            checked = row.get("candidate_moves_checked")
            if (
                not isinstance(checked, int)
                or isinstance(checked, bool)
                or checked < 1
            ):
                findings.append("saturation_batch_checked_no_moves")
                complete = False
            material_value = row.get("material_incremental_value")
            if not isinstance(material_value, bool):
                findings.append("invalid_saturation_batch_material_value")
                complete = False
            elif material_value is not False:
                if require_complete:
                    findings.append("saturation_batch_still_material")
                complete = False
            batch_fields = [
                "new_material_seams",
                "changed_material_dispositions",
            ]
            if consumer_brand:
                batch_fields.extend(
                    [
                        "new_product_axes",
                        "changed_axis_strengths",
                        "changed_axis_incidence",
                    ]
                )
            for field in batch_fields:
                metric = row.get(field)
                if (
                    not isinstance(metric, int)
                    or isinstance(metric, bool)
                    or metric < 0
                ):
                    findings.append(f"invalid_saturation_batch_{field}")
                    complete = False
                elif metric != 0:
                    if require_complete:
                        findings.append(f"saturation_batch_nonzero_{field}")
                    complete = False
    remaining = value.get("remaining_moves")
    if not isinstance(remaining, list):
        findings.append("missing_remaining_move_accounting")
        complete = False
    else:
        for row in remaining:
            if not isinstance(row, dict):
                findings.append("invalid_remaining_move")
                complete = False
                continue
            disposition = row.get("disposition")
            if disposition not in {
                "dominated",
                "source_exhausted",
                "unsafe_or_prohibited",
                "blocked_no_route",
                "deferred_nonmaterial",
                "material_open",
                "blocked_route_available",
            }:
                findings.append("invalid_remaining_move_disposition")
                complete = False
            material = row.get("material")
            if not isinstance(material, bool):
                findings.append("invalid_remaining_move_material_flag")
                complete = False
            elif material is not False:
                if require_complete:
                    findings.append("material_remaining_move")
                complete = False
    conclusion = value.get("conclusion")
    if conclusion not in {"complete", "incomplete"}:
        findings.append("invalid_evidence_depth_conclusion")
        complete = False
    elif conclusion != "complete":
        complete = False
    return complete


def _load_seal(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"seal could not be read: {exc}") from exc
    for block in _YAML_FENCE.findall(text):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict) and isinstance(
            parsed.get("phase_acquisition_seal"), dict
        ):
            return parsed["phase_acquisition_seal"]
    raise ValueError("no phase_acquisition_seal YAML block found")


def _validate_controller_placement(
    seal: Mapping[str, Any], findings: list[str]
) -> None:
    value = seal.get("controller_placement")
    if not isinstance(value, dict):
        findings.append("missing_controller_placement")
        return
    if value.get("controller_actor") != "CO0" or value.get("placement") != (
        "top_level"
    ):
        findings.append("invalid_controller_placement")
    if value.get("worker_slots_required") != 3:
        findings.append("invalid_worker_slot_requirement")
    available = value.get("worker_slots_available")
    if not isinstance(available, int) or isinstance(available, bool) or available < 3:
        findings.append("blocked_controller_capacity")


def _validate_capability_preflight(
    seal: Mapping[str, Any], *, valid_pass: bool, findings: list[str]
) -> set[str]:
    conditional_routes: set[str] = set()
    value = seal.get("route_capability_preflight")
    if not isinstance(value, dict):
        findings.append("missing_route_capability_preflight")
        return conditional_routes
    if value.get("checked_before_network_capture") is not True:
        findings.append("capability_preflight_not_forefront")
    google = value.get("google_serp")
    if not isinstance(google, dict):
        findings.append("missing_google_serp_capability")
    else:
        mode = google.get("mode")
        if mode not in {"persistent_fallback", "cooldown_only"}:
            findings.append("invalid_google_recovery_mode")
        if google.get("primary_route_ready") is not True:
            findings.append("google_primary_route_not_ready")
        if google.get("queue_state_writable") is not True:
            findings.append("google_queue_state_not_writable")
        if mode == "persistent_fallback" and google.get(
            "persistent_fallback_ready"
        ) is not True:
            findings.append("google_persistent_fallback_not_ready")
    reddit = value.get("reddit_weekly_lake")
    if not isinstance(reddit, dict) or reddit.get("reader_status") not in {
        "ready",
        "blocked",
    }:
        findings.append("invalid_reddit_weekly_capability")
    elif valid_pass and reddit.get("reader_status") != "ready":
        findings.append("passing_seal_with_blocked_reddit_weekly_reader")
    paid = value.get("paid_ad_transparency")
    if not isinstance(paid, dict):
        findings.append("missing_paid_ad_capability")
    else:
        for key in ("google_ads_transparency", "meta_ads_library"):
            if paid.get(key) not in {"ready", "identity_pending", "blocked"}:
                findings.append(f"invalid_{key}_capability")
            elif valid_pass and paid.get(key) != "ready":
                findings.append(f"passing_seal_without_{key}_capability")
    shop = value.get("tiktok_shop")
    if not isinstance(shop, dict):
        findings.append("missing_tiktok_shop_capability")
    else:
        trigger = shop.get("trigger")
        route_status = shop.get("route_status")
        if trigger not in {"required", "not_required", "unknown"}:
            findings.append("invalid_tiktok_shop_trigger")
        if route_status not in {
            "ready",
            "not_checked_until_trigger",
            "EGRESS_SESSION_UNHEALTHY",
            "TTSHOP_ROUTE_BLOCKED",
            "EGRESS_COUNTRY_WRONG",
        }:
            findings.append("invalid_tiktok_shop_route_status")
        if valid_pass and trigger == "unknown":
            findings.append("passing_seal_with_unknown_tiktok_shop_trigger")
        if valid_pass and trigger == "required" and route_status != "ready":
            findings.append("passing_seal_with_blocked_required_tiktok_shop")
        if trigger == "required":
            conditional_routes.add("tiktok_shop")
    native = value.get("native_social")
    if not isinstance(native, dict):
        findings.append("missing_native_social_capability")
    else:
        for platform in ("tiktok", "instagram", "youtube"):
            row = native.get(platform)
            if not isinstance(row, dict):
                findings.append(f"missing_native_{platform}_capability")
                continue
            trigger = row.get("trigger")
            route_status = row.get("route_status")
            if trigger not in {"required", "not_required", "unknown"}:
                findings.append(f"invalid_native_{platform}_trigger")
            if route_status not in {
                "ready",
                "not_checked_until_trigger",
                "blocked",
            }:
                findings.append(f"invalid_native_{platform}_route_status")
            if valid_pass and trigger == "unknown":
                findings.append(f"passing_seal_with_unknown_native_{platform}_trigger")
            if valid_pass and trigger == "required" and route_status != "ready":
                findings.append(f"passing_seal_with_blocked_native_{platform}")
            if trigger == "required":
                conditional_routes.add(f"native_{platform}")
    return conditional_routes


def _validate_specialist_returns(
    seal: Mapping[str, Any], *, repo_root: Path, findings: list[str]
) -> None:
    rows = seal.get("specialist_returns")
    if not isinstance(rows, list):
        findings.append("missing_specialist_returns")
        return
    actors: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_specialist_return")
            continue
        actor = row.get("actor")
        actors.append(str(actor))
        _verify_artifact(
            row.get("terminal_locator"),
            row.get("sha256"),
            repo_root=repo_root,
            code="specialist_terminal",
            findings=findings,
        )
    if sorted(actors) != ["CO1", "CO2", "CO3"]:
        findings.append("specialist_returns_must_be_co1_co2_co3")


def _validate_route_accounting(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    valid_pass: bool,
    conditional_routes: set[str],
    findings: list[str],
) -> set[str]:
    rows = seal.get("route_job_accounting")
    if not isinstance(rows, list) or not rows:
        findings.append("missing_route_job_accounting")
        return set()
    route_ids: set[str] = set()
    global_jobs: set[str] = set()
    phases: set[str] = set()
    material_pending: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_route_job_accounting_row")
            continue
        route_id = row.get("route_id")
        if not isinstance(route_id, str) or not route_id:
            findings.append("missing_route_id")
            continue
        if route_id in route_ids:
            findings.append("duplicate_route_id")
        route_ids.add(route_id)
        phase = row.get("phase")
        if isinstance(phase, str):
            phases.add(phase)
        if not isinstance(row.get("required"), bool):
            findings.append(f"invalid_route_required_flag:{route_id}")
        if not isinstance(row.get("material"), bool):
            findings.append(f"invalid_route_material_flag:{route_id}")
        lists: dict[str, list[str]] = {}
        for name in ("planned", "completed", "blocked", "unrun"):
            raw = row.get(f"{name}_job_ids")
            if not isinstance(raw, list) or any(
                not isinstance(item, str) or not item for item in raw
            ):
                findings.append(f"invalid_{name}_job_ids")
                raw = []
            if len(raw) != len(set(raw)):
                findings.append(f"duplicate_{name}_job_ids")
            lists[name] = raw
            count = row.get(f"{name}_count")
            if not isinstance(count, int) or isinstance(count, bool):
                findings.append(f"invalid_{name}_count_type")
            if count != len(raw):
                findings.append(f"{name}_count_mismatch")
        planned = set(lists["planned"])
        required_routes = MANDATORY_ROUTE_IDS | conditional_routes
        if route_id in required_routes:
            if not planned:
                findings.append(f"mandatory_route_has_no_accounting_job:{route_id}")
            if row.get("required") is not True:
                findings.append(f"mandatory_route_not_required:{route_id}")
            expected_phase = MANDATORY_ROUTE_PHASES.get(route_id, "co3")
            if phase != expected_phase:
                findings.append(
                    f"route_phase_mismatch:{route_id}:{expected_phase}"
                )
            if valid_pass and lists["unrun"]:
                findings.append(
                    f"passing_mandatory_route_has_unrun_jobs:{route_id}"
                )
        disposition_sets = [
            set(lists["completed"]),
            set(lists["blocked"]),
            set(lists["unrun"]),
        ]
        if any(
            disposition_sets[left] & disposition_sets[right]
            for left in range(3)
            for right in range(left + 1, 3)
        ):
            findings.append("job_dispositions_overlap")
        if planned != set().union(*disposition_sets):
            findings.append("planned_jobs_not_fully_accounted")
        if global_jobs & planned:
            findings.append("job_id_reused_across_routes")
        global_jobs.update(planned)
        pending = set(lists["blocked"]) | set(lists["unrun"])
        if row.get("required") is True and row.get("material") is True:
            material_pending.update(pending)
            if valid_pass and pending:
                findings.append("passing_seal_has_material_pending_jobs")
        _verify_artifact(
            row.get("terminal_artifact_locator"),
            row.get("terminal_artifact_sha256"),
            repo_root=repo_root,
            code="route_terminal_artifact",
            findings=findings,
        )
    missing_routes = sorted((MANDATORY_ROUTE_IDS | conditional_routes) - route_ids)
    if missing_routes:
        findings.append("missing_required_route_accounting:" + ",".join(missing_routes))
    for phase in ("serp_phase1", "co1", "co2", "co3", "serp_phase2"):
        if phase not in phases:
            findings.append(f"missing_{phase}_accounting")
    return material_pending


def _validate_decision_receipt(
    seal: Mapping[str, Any], *, repo_root: Path, findings: list[str]
) -> None:
    receipt = seal.get("serp_phase2_decision_receipt")
    if not isinstance(receipt, dict):
        findings.append("missing_serp_phase2_decision_receipt")
        return
    _verify_artifact(
        receipt.get("locator"),
        receipt.get("sha256"),
        repo_root=repo_root,
        code="serp_phase2_decision_receipt",
        findings=findings,
    )
    entries = receipt.get("entries")
    if not isinstance(entries, int) or isinstance(entries, bool) or entries < 0:
        findings.append("invalid_serp_phase2_decision_entry_count")


def _validate_resume_contract(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    expected_pending: set[str],
    valid_pass: bool,
    findings: list[str],
) -> None:
    resume = seal.get("resume_contract")
    if not isinstance(resume, dict):
        findings.append("missing_resume_contract")
        return
    pending = resume.get("pending_job_ids")
    if not isinstance(pending, list) or any(
        not isinstance(item, str) or not item for item in pending
    ):
        findings.append("invalid_resume_pending_jobs")
        pending = []
    if set(pending) != expected_pending:
        findings.append("resume_pending_jobs_mismatch")
    if valid_pass and pending:
        findings.append("passing_seal_has_resume_work")
    reusable = resume.get("reusable_artifacts")
    if not isinstance(reusable, list):
        findings.append("invalid_reusable_artifacts")
        return
    for row in reusable:
        if not isinstance(row, dict):
            findings.append("invalid_reusable_artifact")
            continue
        invalid_if = row.get("invalid_if")
        if not isinstance(invalid_if, list) or not invalid_if or any(
            not isinstance(item, str) or not item for item in invalid_if
        ):
            findings.append("missing_reusable_artifact_invalidation")
        _verify_artifact(
            row.get("locator"),
            row.get("sha256"),
            repo_root=repo_root,
            code="reusable_artifact",
            findings=findings,
        )


def _verify_artifact(
    locator: Any,
    digest: Any,
    *,
    repo_root: Path,
    code: str,
    findings: list[str],
) -> None:
    if not isinstance(locator, str) or not locator:
        findings.append(f"missing_{code}_locator")
        return
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest.casefold()):
        findings.append(f"invalid_{code}_sha256")
        return
    path = Path(locator)
    if not path.is_absolute():
        path = repo_root / path
    if not path.is_file():
        findings.append(f"missing_{code}_file")
        return
    if _artifact_hash(path).casefold() != digest.casefold():
        findings.append(f"{code}_hash_mismatch")


def _artifact_hash(path: Path) -> str:
    """Hash seal text canonically while retaining exact-byte binary checks."""
    if path.suffix.lower() not in _TEXT_ARTIFACT_SUFFIXES:
        return hash_file(path)
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_bytes(content)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a phase_acquisition_seal_v3 YAML block and its hashes."
    )
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--allow-legacy-v2",
        action="store_true",
        help=(
            "Audit a historical phase_acquisition_seal_v2. Legacy v2 seals "
            "do not satisfy the current broad-Understanding completion contract."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        seal_schema_version = _load_seal(args.seal.resolve()).get("schema_version")
        findings = validate_phase_acquisition_seal(
            seal_path=args.seal.resolve(),
            repo_root=args.repo_root.resolve(),
            allow_legacy_v2=args.allow_legacy_v2,
        )
    except Exception as exc:  # noqa: BLE001 - controlled validator diagnostic
        parser.exit(
            status=2,
            message=f"phase acquisition seal validation failed: {type(exc).__name__}: {exc}\n",
        )
    payload = {
        "validator": SEAL_VERSION,
        "seal_schema_version": seal_schema_version,
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
