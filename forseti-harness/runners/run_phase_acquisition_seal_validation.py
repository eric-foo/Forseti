"""Validate acquisition accounting and evidence depth in an Understanding seal."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
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
LEGACY_CONSUMER_DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v2"
LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE = (
    "broad_consumer_brand_understanding_v1"
)
PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v3"
PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE = (
    "broad_consumer_brand_understanding_v2"
)
CONSUMER_DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v4"
CONSUMER_BRAND_UNDERSTANDING_PROFILE = (
    "broad_consumer_brand_understanding_v3"
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
    "reddit_forum_threads": 40,
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
_AXIS_DECISION_MATURITY = {"open", "decision_mature"}
_AXIS_CLOSURE_BASES = {
    "evidence_supported",
    "route_bounded_source_exhaustion",
}
_AXIS_CLAIM_CEILINGS = {"strong_qualitative", "bounded_observation_only"}
_AXIS_DECISION_USEFULNESS_STATUSES = {
    "strategically_material",
    "decision_useful",
    "source_exhausted_but_weak",
    "evidence_covered_but_not_decision_useful",
}
_AXIS_DECISION_SUPPORT_ROLES = {
    "customer_tension",
    "segment_or_condition",
    "behavior_or_purchase_consequence",
    "competitor_destination",
    "counterevidence",
}
_AXIS_DISPOSITIONS = {
    "material",
    "bounded_nonmaterial",
    "merged",
    "blocked_material",
}
_LEGACY_FOCUSED_SEARCH_GOALS = {
    "corroborate_or_segment",
    "disconfirm_or_compare",
}
_FOCUSED_SEARCH_GOALS = {
    "corroborate_or_segment",
    "compare_switch_or_value",
    "disconfirm_or_strongest_delight",
}
_FOCUSED_SEARCH_TERMINALS = {
    "captured",
    "no_material_yield",
    "dominated",
    "blocked_no_route",
}
_AXIS_SUPPORT_CONTRIBUTIONS = {
    "corroborates",
    "contradicts",
    "compares",
    "sharpens",
}
_AXIS_SUPPORT_CHOICES = {
    "subject",
    "alternative",
    "neither",
    "conditional",
    "unstated",
}
_TARGET_TERMINAL_STATES = {
    "used",
    "captured_excluded",
    "no_material_yield",
    "blocked",
    "unavailable",
}
_FRONTIER_CANDIDATE_STATES = {
    "captured_used",
    "captured_excluded",
    "duplicate_thread",
    "no_usable_content",
    "dominated",
    "blocked",
    "unavailable",
}
_QUERY_FAMILY_ROLES = {"mandatory_high_yield", "phase2", "continuation"}
# The mandatory-family ordering contract was adopted at this instant. A
# pre_contract_historical_run exception can only describe a Phase 2 that
# actually executed before adoption; a later run cannot re-declare it.
_EXECUTION_ORDER_CONTRACT_ADOPTED_AT = datetime.fromisoformat(
    "2026-08-04T00:00:00+00:00"
)
_MANDATORY_HIGH_YIELD_FAMILY_ORDER = (
    "balanced_axis_baseline",
    "behavior_consequence_displacement",
    "brandless_exact_product",
    "condition_post_use",
)
_MANDATORY_HIGH_YIELD_FAMILY_KINDS = set(_MANDATORY_HIGH_YIELD_FAMILY_ORDER)
_MATERIAL_ADDITION_KINDS = {
    "new_axis",
    "tier_change",
    "mechanism",
    "segment_or_condition",
    "behavior_consequence",
    "competitor_destination",
    "contradiction",
    "sampling_risk_change",
    "competitive_action_change",
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
    "rejected_or_not_recommended",
    "retained_or_repurchased",
    "recommended_or_would_purchase",
    "none_explicit",
}
_NEGATIVE_CHOICE_OUTCOMES = _CHOICE_OUTCOMES - {
    "retained_or_repurchased",
    "recommended_or_would_purchase",
    "none_explicit",
}
_POSITIVE_CHOICE_OUTCOMES = {
    "retained_or_repurchased",
    "recommended_or_would_purchase",
}
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
    # Required only when the seal records route version 1.1.0 or later; it
    # joins the required set via the conditional-route mechanism, not
    # MANDATORY_ROUTE_IDS.
    "campaign_evidence_integration": "campaign_integration",
}
# Understanding Acquire & Seal route versioning (owning authority: CSB
# playbook `understanding_acquire_seal_route`). Versioning started
# 2026-08-07; seals sealed before that carry no stamped version and are
# audited with --allow-preversion-route.
UNDERSTANDING_ROUTE_VERSIONS = {"1.0.0", "1.1.0", "1.2.0", "1.3.0"}
CURRENT_UNDERSTANDING_ROUTE_VERSION = "1.3.0"
CAMPAIGN_EVIDENCE_VIEW_VERSION = "campaign_evidence_view_v1"
_CAMPAIGN_INTEGRATION_ROUTE_ID = "campaign_evidence_integration"
_CAMPAIGN_INTEGRATION_ROUTE_VERSIONS = {"1.1.0", "1.2.0", "1.3.0"}
# Route 1.1.0 introduced comparator closure, campaign-evidence integration,
# conditional verification, and retailer-state accounting together, so a
# historical audit of a 1.1.0 seal still owes all of them. Pre-fanout
# qualification and price/size context entered at 1.2.0 and are never
# back-claimed onto an earlier stamped seal. 1.0.0 owes none of them.
_ROUTE_REVISION_1_1_OBLIGATION_VERSIONS = {"1.1.0", "1.2.0", "1.3.0"}
_ROUTE_REVISION_1_2_OBLIGATION_VERSIONS = {"1.2.0", "1.3.0"}
_ROUTE_REVISION_1_3_OBLIGATION_VERSIONS = {"1.3.0"}
_CAMPAIGN_SOURCE_ROLES = {
    "owned_post",
    "paid_ad",
    "creator_authored",
    "audience_comment",
    "retailer_review",
    "retailer_qa",
    "community_post",
}
_CAMPAIGN_RELATIONSHIP_POSTURES = {
    "owned",
    "retailer_operated",
    "disclosed_paid_or_affiliate",
    "partnership_byline_observed",
    "apparently_independent",
    "relationship_unknown",
}
_CAMPAIGN_LINKAGE_POSTURES = {"direct", "inferred", "unknown"}
_CAMPAIGN_CLUSTER_BASES = {"direct", "inferred"}
_CAMPAIGN_CAPTURE_REQUEST_STATES = {
    "captured",
    "blocked",
    "no_longer_material",
}
_COMPARATOR_CLOSURE_STATES = {
    "phase_a_competitor_context_closed",
    "blocked_open_comparator_candidates",
}
_COMPARATOR_DISPOSITIONS = {
    "promoted",
    "rejected",
    "watch_listed",
    "role_bounded",
    "explicit_gap",
}
_COMPARATOR_PREFANOUT_POSTURES = {
    "core_fanout",
    "bounded_watch",
    "rejected_before_fanout",
}
_COMPARATOR_PREFANOUT_ROLES = {
    "direct_peer",
    "value_substitute",
    "adjacent",
    "unresolved",
    "non_competitor",
}
_COMPARATOR_PREFANOUT_SOURCE_ROLES = {
    "reddit_community",
    "retailer_review",
    "creator_authored",
    "independent_editorial",
}
_COMPARATOR_ACTOR_OVERLAP_POSTURES = {
    "no_match_observed",
    "possible_same_actor",
    "confirmed_same_actor",
    "unavailable",
}
_COMPARATOR_CHOICE_STATUSES = {"observed", "partial", "unresolved"}
_COMPARATOR_CHOICE_POSTURES = {
    "subject_advantage",
    "competitor_advantage",
    "split_or_conditional",
    "parity_or_unresolved",
}
_INTELLIGENCE_CLAIM_SUPPORT_POSTURES = {
    "isolated",
    "directly_observed",
    "resonance_supported",
    "independently_repeated",
    "cross_venue_corroborated",
}
_INTELLIGENCE_CLAIM_CONFLICT_POSTURES = {
    "not_checked",
    "none_observed",
    "mixed",
    "contradicted",
}
_INTELLIGENCE_CLAIM_SOURCE_ROLES = {
    "owned_source",
    "paid_ad",
    "retailer_product",
    "retailer_review",
    "reddit_community",
    "creator_authored",
    "independent_editorial",
    "direct_measurement",
    "other_public_source",
}
_COMPARATOR_PRICE_SIZE_STATUSES = {"observed", "partial", "unavailable"}
_COMPARATOR_SIZE_NORMALIZATION_POSTURES = {
    "same_unit",
    "source_normalized",
    "not_directly_normalized",
    "unavailable",
}
_COMPARATOR_LANE_KEYS = (
    "co1_owned_ad_positioning",
    "co2_retailer_product",
    "co3_retailer_review",
    "co3_reddit_community",
    "campaign_creator_comparison",
)
_COMPARATOR_LANE_STATES = {"observed", "none_found", "blocked"}
_COMPARATOR_PORTFOLIO_ROLES = {
    "explicit_hero",
    "likely_major",
    "supporting",
    "unclear",
}
_COMPARATOR_PORTFOLIO_ROLE_SCOPES = {"product", "franchise"}
_COMPARATOR_PORTFOLIO_ROLE_BASES = {
    "explicit_source",
    "multi_source_inference",
    "observed_position",
    "unresolved",
}
_COMPARATOR_POSITION_SCOPES = {
    "brand_portfolio",
    "retailer_category",
    "retailer_collection",
    "market_list",
}
_COMPARATOR_FORBIDDEN_SYNTHETIC_FIELDS = {
    "rank",
    "overall_rank",
    "sales_rank",
    "market_share",
    "sentiment_score",
    "reddit_sentiment",
}
_VERIFICATION_TRIGGER_KINDS = {
    "material_axis",
    "contradiction",
    "condition_or_consequence",
    "competitor_destination",
    "sampling_risk",
}
_VERIFICATION_STATUSES = {"completed", "blocked", "not_run"}
_RETAILER_STATE_KINDS = {
    "retailer_state_snapshot",
    "retailer_state_change",
    "movement_unresolved_baseline_only",
}
_YAML_FENCE = re.compile(r"```yaml\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_TEXT_ARTIFACT_SUFFIXES = {".json", ".md", ".yaml", ".yml"}


def _is_enum_value(value: Any, allowed: set[str]) -> bool:
    """Enum membership that survives unhashable YAML values.

    A seal is operator-authored YAML, so any field can arrive as a list or
    mapping. Bare ``value in allowed`` raises ``TypeError`` on those shapes,
    which would crash the run instead of emitting a finding.
    """
    return isinstance(value, str) and value in allowed


def validate_phase_acquisition_seal(
    *,
    seal_path: Path,
    repo_root: Path,
    allow_legacy_v2: bool = False,
    allow_legacy_consumer_v1: bool = False,
    allow_legacy_consumer_v2: bool = False,
    allow_preversion_route: bool = False,
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
    route_block = seal.get("understanding_route")
    if (
        schema_version == SEAL_VERSION
        and isinstance(route_block, dict)
        and _is_enum_value(
            route_block.get("route_version"),
            _CAMPAIGN_INTEGRATION_ROUTE_VERSIONS,
        )
    ):
        # Campaign integration entered the route at 1.1.0 and remains a
        # mandatory accounted job in later revisions. Historical audits retain
        # the obligations of the version stamped on the seal.
        conditional_routes = conditional_routes | {
            _CAMPAIGN_INTEGRATION_ROUTE_ID
        }
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
            allow_legacy_consumer_v1=allow_legacy_consumer_v1,
            allow_legacy_consumer_v2=allow_legacy_consumer_v2,
            findings=findings,
        )
        _validate_understanding_route(
            seal,
            repo_root=repo_root,
            valid_pass=valid_pass,
            allow_preversion_route=allow_preversion_route,
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
    allow_legacy_consumer_v1: bool,
    allow_legacy_consumer_v2: bool,
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
        LEGACY_CONSUMER_DEPTH_LEDGER_VERSION,
        PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION,
        CONSUMER_DEPTH_LEDGER_VERSION,
    }:
        findings.append("invalid_evidence_depth_ledger_version")
    if profile_id not in {
        BROAD_UNDERSTANDING_PROFILE,
        LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE,
        PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE,
        CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    }:
        findings.append("invalid_understanding_completion_profile")
    valid_profile_pair = (
        ledger_version == DEPTH_LEDGER_VERSION
        and profile_id == BROAD_UNDERSTANDING_PROFILE
    ) or (
        ledger_version == LEGACY_CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    ) or (
        ledger_version == PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    ) or (
        ledger_version == CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    if not valid_profile_pair:
        findings.append("understanding_profile_schema_mismatch")
    legacy_consumer_brand = (
        ledger_version == LEGACY_CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    previous_consumer_brand = (
        ledger_version == PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    current_consumer_brand = (
        ledger_version == CONSUMER_DEPTH_LEDGER_VERSION
        and profile_id == CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    consumer_brand = (
        legacy_consumer_brand or previous_consumer_brand or current_consumer_brand
    )
    if legacy_consumer_brand and not allow_legacy_consumer_v1:
        findings.append("legacy_consumer_v1_requires_explicit_historical_audit")
    if previous_consumer_brand and not allow_legacy_consumer_v2:
        findings.append("legacy_consumer_v2_requires_explicit_historical_audit")
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
            families.get("reddit_forum"),
            artifacts=artifacts,
            require_distinct_artifacts=(previous_consumer_brand or current_consumer_brand),
            findings=findings,
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
            current_contract=(previous_consumer_brand or current_consumer_brand),
            decision_contract=current_consumer_brand,
            findings=findings,
        )
    closure_complete = _validate_depth_closure(
        ledger.get("closure"),
        require_complete=valid_pass,
        consumer_brand=consumer_brand,
        current_consumer_contract=current_consumer_brand,
        previous_consumer_contract=previous_consumer_brand,
        axis_maturity={
            str(row.get("axis_id")): row.get("decision_maturity")
            for row in ledger.get("product_axes", [])
            if isinstance(row, dict)
            and row.get("disposition") in {"material", "blocked_material"}
        },
        route_jobs=_route_job_states(seal),
        findings=findings,
    )
    if previous_consumer_brand or current_consumer_brand:
        _validate_reddit_candidate_frontier(
            ledger,
            artifacts=artifacts,
            route_jobs=_route_job_states(seal),
            require_complete=valid_pass,
            decision_contract=current_consumer_brand,
            findings=findings,
        )
    if valid_pass:
        floors = (
            CONSUMER_BRAND_UNDERSTANDING_FLOORS
            if (previous_consumer_brand or current_consumer_brand)
            else {
                **CONSUMER_BRAND_UNDERSTANDING_FLOORS,
                "reddit_forum_threads": BROAD_UNDERSTANDING_FLOORS[
                    "reddit_forum_threads"
                ],
            }
            if legacy_consumer_brand
            else BROAD_UNDERSTANDING_FLOORS
        )
        for metric, minimum in floors.items():
            below_floor = metrics.get(metric, 0) < minimum
            reddit_exception = (
                (previous_consumer_brand or current_consumer_brand)
                and metric == "reddit_forum_threads"
                and _valid_reddit_floor_exception(
                    ledger,
                    observed=metrics.get(metric, 0),
                    route_jobs=_route_job_states(seal),
                    decision_contract=current_consumer_brand,
                )
            )
            if below_floor and not reddit_exception:
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
        if row.get("relationship") not in _SOCIAL_RELATIONSHIPS:
            findings.append("invalid_external_context_relationship")
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
    value: Any,
    *,
    artifacts: Mapping[str, Path],
    require_distinct_artifacts: bool = False,
    findings: list[str],
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
    independent_artifacts: set[Path] = set()
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
            if require_distinct_artifacts:
                artifact_id = row.get("artifact_id")
                if isinstance(artifact_id, str) and artifact_id in artifacts:
                    artifact_path = artifacts[artifact_id].resolve()
                    if artifact_path in independent_artifacts:
                        findings.append("shared_reddit_thread_native_artifact")
                    independent_artifacts.add(artifact_path)
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
                try:
                    normalized_date = (
                        date.fromisoformat(published_at)
                        if isinstance(published_at, str)
                        and re.fullmatch(r"\d{4}-\d{2}-\d{2}", published_at)
                        else None
                    )
                except ValueError:
                    normalized_date = None
                if normalized_date is None:
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
) -> dict[tuple[str, str], str | None]:
    registry: dict[tuple[str, str], str | None] = {}
    external = families.get("external_context")
    if isinstance(external, dict) and isinstance(external.get("units"), list):
        for row in external["units"]:
            if not isinstance(row, dict):
                continue
            unit_id = row.get("unit_id")
            if isinstance(unit_id, str) and unit_id:
                origin_id = row.get("origin_id")
                registry[("external_context", unit_id)] = (
                    str(origin_id)
                    if row.get("independence") == "independent_origin"
                    and row.get("source_type")
                    in {"consumer_editorial", "trade_press"}
                    and row.get("relationship")
                    in _QUALIFYING_SOCIAL_RELATIONSHIPS
                    and isinstance(origin_id, str)
                    and origin_id
                    else None
                )
    reddit = families.get("reddit_forum")
    if isinstance(reddit, dict) and isinstance(reddit.get("threads"), list):
        for row in reddit["threads"]:
            if not isinstance(row, dict):
                continue
            thread_id = row.get("thread_id")
            if isinstance(thread_id, str) and thread_id:
                registry[("reddit_forum", thread_id)] = (
                    thread_id
                    if row.get("independence") == "independent_thread"
                    else None
                )
    social = families.get("native_social")
    if isinstance(social, dict) and isinstance(social.get("posts"), list):
        for row in social["posts"]:
            if not isinstance(row, dict):
                continue
            unit_id = row.get("unit_id")
            if isinstance(unit_id, str) and unit_id:
                creator_id = row.get("creator_id")
                registry[("native_social", unit_id)] = (
                    str(creator_id)
                    if row.get("independence") == "independent_post"
                    and row.get("relationship")
                    in _QUALIFYING_SOCIAL_RELATIONSHIPS
                    and isinstance(creator_id, str)
                    and creator_id
                    else None
                )
    return registry


def _load_retailer_axis_coding(
    value: Any,
    *,
    ledger: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    retailer_corpora: Mapping[str, int],
    retailer_product_contexts: Mapping[str, set[str]],
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
    coding_cycle_id = coding.get("cycle_id")
    ledger_cycle_id = ledger.get("cycle_id")
    if coding_cycle_id != ledger_cycle_id:
        reuse = value.get("reuse")
        if not (
            isinstance(reuse, dict)
            and reuse.get("mode") == "pinned_unchanged_reuse"
            and reuse.get("source_cycle_id") == coding_cycle_id
            and reuse.get("current_cycle_id") == ledger_cycle_id
            and isinstance(reuse.get("reason"), str)
            and reuse.get("reason")
        ):
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
        product_context_id = row.get("product_context_id")
        if not isinstance(product_context_id, str) or not product_context_id:
            findings.append("missing_coded_review_product_context")
            complete = False
        elif product_context_id not in retailer_product_contexts.get(
            corpus_id, set()
        ):
            findings.append("coded_review_product_context_outside_corpus")
            complete = False
        if row.get("incentive_state") not in _INCENTIVE_STATES:
            findings.append("invalid_coded_review_incentive_state")
            complete = False
        source_row_ref = row.get("source_row_ref")
        if not isinstance(source_row_ref, str) or not source_row_ref:
            findings.append("missing_coded_review_source_row_ref")
            complete = False
        outcomes = _string_set(
            row.get("overall_choice_outcomes"),
            code="invalid_coded_review_overall_choice_outcomes",
            findings=findings,
        )
        if not outcomes or not outcomes.issubset(_CHOICE_OUTCOMES):
            findings.append("invalid_coded_review_overall_choice_outcome")
            complete = False
        if "none_explicit" in outcomes and len(outcomes) > 1:
            findings.append("coded_review_overall_none_outcome_conflict")
            complete = False

        axis_codes = row.get("axis_codes")
        if not isinstance(axis_codes, list):
            findings.append("invalid_coded_review_axis_codes")
            complete = False
            axis_codes = []
        seen_axis_codes: set[str] = set()
        valid_axis_codes: list[tuple[str, set[str]]] = []
        for axis_code in axis_codes:
            if not isinstance(axis_code, dict):
                findings.append("invalid_coded_review_axis_code")
                complete = False
                continue
            axis_id = axis_code.get("axis_id")
            if (
                not isinstance(axis_id, str)
                or not axis_id
                or axis_id in seen_axis_codes
            ):
                findings.append("invalid_or_duplicate_coded_review_axis_id")
                complete = False
                continue
            seen_axis_codes.add(axis_id)
            if axis_id not in axis_ids:
                findings.append("coded_review_references_unknown_axis")
                complete = False
                continue
            axis_outcomes = _string_set(
                axis_code.get("choice_outcomes"),
                code="invalid_coded_review_axis_choice_outcomes",
                findings=findings,
            )
            if not axis_outcomes or not axis_outcomes.issubset(
                _CHOICE_OUTCOMES
            ):
                findings.append("invalid_coded_review_axis_choice_outcome")
                complete = False
                continue
            if "none_explicit" in axis_outcomes and len(axis_outcomes) > 1:
                findings.append("coded_review_axis_none_outcome_conflict")
                complete = False
                continue
            explicit_axis_outcomes = axis_outcomes - {"none_explicit"}
            if explicit_axis_outcomes - outcomes:
                findings.append("coded_review_axis_outcome_not_in_overall")
                complete = False
                continue
            valid_axis_codes.append((axis_id, axis_outcomes))

        for axis_id, axis_outcomes in valid_axis_codes:
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
            if axis_outcomes & _NEGATIVE_CHOICE_OUTCOMES:
                aggregate["negative_choice_review_count"] += 1
            if axis_outcomes & _POSITIVE_CHOICE_OUTCOMES:
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


def _retailer_corpus_product_contexts(
    families: Mapping[str, Any],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    family = families.get("retailer_reviews")
    if not isinstance(family, dict) or not isinstance(family.get("corpora"), list):
        return result
    for row in family["corpora"]:
        if not isinstance(row, dict):
            continue
        corpus_id = row.get("corpus_id")
        values = row.get("product_context_ids")
        if (
            isinstance(corpus_id, str)
            and corpus_id
            and isinstance(values, list)
            and all(isinstance(value, str) and value for value in values)
        ):
            result[corpus_id] = set(values)
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


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_consumer_axis_inventory(
    value: Any,
    *,
    ledger: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    axis_rows: Mapping[str, Mapping[str, Any]],
    findings: list[str],
) -> tuple[str | None, datetime | None, bool]:
    if not isinstance(value, dict):
        findings.append("missing_consumer_axis_inventory")
        return None, None, False
    artifact_id = value.get("artifact_id")
    if not isinstance(artifact_id, str) or artifact_id not in artifacts:
        findings.append("unresolved_consumer_axis_inventory_artifact")
        return None, None, False
    path = artifacts[artifact_id]
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"invalid_consumer_axis_inventory:{type(exc).__name__}")
        return None, None, False
    if not isinstance(inventory, dict):
        findings.append("invalid_consumer_axis_inventory_shape")
        return None, None, False
    complete = True
    if inventory.get("schema_version") != "consumer_brand_axis_inventory_v1":
        findings.append("invalid_consumer_axis_inventory_version")
        complete = False
    if inventory.get("subject") != ledger.get("subject"):
        findings.append("consumer_axis_inventory_subject_mismatch")
        complete = False
    if inventory.get("cycle_id") != ledger.get("cycle_id"):
        findings.append("consumer_axis_inventory_cycle_id_mismatch")
        complete = False
    created_at = _parse_iso_datetime(inventory.get("created_at"))
    if created_at is None:
        findings.append("invalid_consumer_axis_inventory_created_at")
        complete = False
    rows = inventory.get("axes")
    observed: dict[str, tuple[Any, Any, Any]] = {}
    if not isinstance(rows, list):
        findings.append("missing_consumer_axis_inventory_axes")
        complete = False
    else:
        for row in rows:
            if not isinstance(row, dict):
                findings.append("invalid_consumer_axis_inventory_axis")
                complete = False
                continue
            axis_id = row.get("axis_id")
            if (
                not isinstance(axis_id, str)
                or not axis_id
                or axis_id in observed
            ):
                findings.append("invalid_or_duplicate_consumer_axis_inventory_id")
                complete = False
                continue
            observed[axis_id] = (
                row.get("label"),
                row.get("polarity"),
                row.get("disposition"),
            )
    expected = {
        axis_id: (
            row.get("label"),
            row.get("polarity"),
            row.get("disposition"),
        )
        for axis_id, row in axis_rows.items()
    }
    if observed != expected:
        findings.append("consumer_axis_inventory_drift")
        complete = False
    return _artifact_hash(path), created_at, complete


def _load_community_axis_coding(
    value: Any,
    *,
    ledger: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    families: Mapping[str, Any],
    axis_ids: set[str],
    findings: list[str],
) -> tuple[dict[str, set[str]], dict[tuple[str, str], set[tuple[str, str, str]]], bool]:
    if not isinstance(value, dict):
        findings.append("missing_community_axis_coding")
        return {}, {}, False
    artifact_id = value.get("artifact_id")
    if not isinstance(artifact_id, str) or artifact_id not in artifacts:
        findings.append("unresolved_community_axis_coding_artifact")
        return {}, {}, False
    try:
        coding = json.loads(artifacts[artifact_id].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"invalid_community_axis_coding:{type(exc).__name__}")
        return {}, {}, False
    if not isinstance(coding, dict):
        findings.append("invalid_community_axis_coding_shape")
        return {}, {}, False
    complete = True
    if coding.get("schema_version") != "community_axis_coding_v1":
        findings.append("invalid_community_axis_coding_version")
        complete = False
    if coding.get("subject") != ledger.get("subject"):
        findings.append("community_axis_coding_subject_mismatch")
        complete = False
    if coding.get("cycle_id") != ledger.get("cycle_id"):
        findings.append("community_axis_coding_cycle_id_mismatch")
        complete = False
    reddit = families.get("reddit_forum")
    reddit_rows = (
        reddit.get("threads", [])
        if isinstance(reddit, dict)
        and isinstance(reddit.get("threads"), list)
        else []
    )
    thread_ids = {
        row.get("thread_id")
        for row in reddit_rows
        if isinstance(row, dict)
        and row.get("independence") == "independent_thread"
        and isinstance(row.get("thread_id"), str)
    }
    coded_threads: set[str] = set()
    axis_threads: dict[str, set[str]] = {}
    coded_fields: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    seen: set[tuple[str, str]] = set()
    rows = coding.get("rows")
    if not isinstance(rows, list):
        findings.append("missing_community_axis_coding_rows")
        return {}, {}, False
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_community_axis_coding_row")
            complete = False
            continue
        thread_id = row.get("thread_id")
        comment_id = row.get("comment_id")
        if (
            not isinstance(thread_id, str)
            or thread_id not in thread_ids
            or not isinstance(comment_id, str)
            or not comment_id
            or (thread_id, comment_id) in seen
        ):
            findings.append("invalid_or_duplicate_community_comment_id")
            complete = False
            continue
        seen.add((thread_id, comment_id))
        coded_threads.add(thread_id)
        product_context = row.get("product_context")
        if not isinstance(product_context, str) or not product_context:
            findings.append("missing_community_product_context")
            complete = False
        row_axis_ids = _string_set(
            row.get("axis_ids"),
            code="invalid_community_axis_ids",
            findings=findings,
        )
        if not row_axis_ids or not row_axis_ids.issubset(axis_ids):
            findings.append("community_coding_references_unknown_axis")
            complete = False
        for axis_id in row_axis_ids & axis_ids:
            axis_threads.setdefault(axis_id, set()).add(thread_id)
        contribution = row.get("contribution")
        if contribution not in _AXIS_SUPPORT_CONTRIBUTIONS:
            findings.append("invalid_community_contribution")
            complete = False
        choice = row.get("choice")
        if choice not in _AXIS_SUPPORT_CHOICES:
            findings.append("invalid_community_choice")
            complete = False
        if (
            contribution in _AXIS_SUPPORT_CONTRIBUTIONS
            and choice in _AXIS_SUPPORT_CHOICES
        ):
            row_fields = (
                str(contribution),
                str(choice),
                str(row.get("alternative_brand") or "").strip(),
            )
            for axis_id in row_axis_ids & axis_ids:
                coded_fields.setdefault((axis_id, thread_id), set()).add(
                    row_fields
                )
        if choice == "alternative" and not str(row.get("alternative_brand", "")).strip():
            findings.append("missing_community_alternative_brand")
            complete = False
        if row.get("explicit_outcome") not in _CHOICE_OUTCOMES:
            findings.append("invalid_community_explicit_outcome")
            complete = False
        if not isinstance(row.get("source_ref"), str) or not row.get("source_ref"):
            findings.append("missing_community_source_ref")
            complete = False
        if row.get("parser_limitation") is not None and not isinstance(
            row.get("parser_limitation"), str
        ):
            findings.append("invalid_community_parser_limitation")
            complete = False
    missing = thread_ids - coded_threads
    if missing:
        findings.append("independent_reddit_threads_without_comment_coding")
        complete = False
    return axis_threads, coded_fields, complete


def _load_consumer_phase2_searches(
    *,
    ledger: Mapping[str, Any],
    artifacts: Mapping[str, Path],
    axis_rows: Mapping[str, Mapping[str, Any]],
    findings: list[str],
) -> tuple[dict[tuple[str, str], Mapping[str, Any]], bool]:
    artifact_ids = {
        job.get("search_artifact_id")
        for axis in axis_rows.values()
        for job in axis.get("focused_search_jobs", [])
        if isinstance(job, dict)
        and isinstance(job.get("search_artifact_id"), str)
    }
    if not artifact_ids:
        findings.append("missing_consumer_phase2_search_artifacts")
        return {}, False
    registry: dict[tuple[str, str], Mapping[str, Any]] = {}
    complete = True
    for artifact_id in artifact_ids:
        if artifact_id not in artifacts:
            continue
        try:
            payload = json.loads(artifacts[artifact_id].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"invalid_consumer_phase2_search_artifact:{type(exc).__name__}")
            complete = False
            continue
        if not isinstance(payload, dict):
            findings.append("invalid_consumer_phase2_search_artifact_shape")
            complete = False
            continue
        if payload.get("schema_version") != "consumer_brand_phase2_search_v1":
            findings.append("invalid_consumer_phase2_search_artifact_version")
            complete = False
        if payload.get("subject") != ledger.get("subject"):
            findings.append("consumer_phase2_search_subject_mismatch")
            complete = False
        if payload.get("cycle_id") != ledger.get("cycle_id"):
            findings.append("consumer_phase2_search_cycle_id_mismatch")
            complete = False
        jobs = payload.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            findings.append("missing_consumer_phase2_search_jobs")
            complete = False
            continue
        for row in jobs:
            if not isinstance(row, dict):
                findings.append("invalid_consumer_phase2_search_job")
                complete = False
                continue
            job_id = row.get("job_id")
            key = (str(artifact_id), str(job_id))
            if not isinstance(job_id, str) or not job_id or key in registry:
                findings.append("invalid_or_duplicate_consumer_phase2_search_job_id")
                complete = False
                continue
            registry[key] = row
            if not isinstance(row.get("query"), str) or not row.get("query"):
                findings.append(f"missing_consumer_phase2_search_query:{job_id}")
                complete = False
            if _parse_iso_datetime(row.get("executed_at")) is None:
                findings.append(f"invalid_consumer_phase2_search_executed_at:{job_id}")
                complete = False
            packet_ids = row.get("serp_packet_artifact_ids")
            if not isinstance(packet_ids, list) or not packet_ids:
                findings.append(f"missing_consumer_phase2_search_packets:{job_id}")
                complete = False
            elif any(
                not isinstance(packet_id, str) or packet_id not in artifacts
                for packet_id in packet_ids
            ):
                findings.append(f"unresolved_consumer_phase2_search_packet:{job_id}")
                complete = False
    return registry, complete


def _validate_target_reconciliation(
    value: Any,
    *,
    artifacts: Mapping[str, Path],
    registry: Mapping[tuple[str, str], str | None],
    axis_ids: set[str],
    route_jobs: Mapping[str, str],
    search_artifact_ids: set[str],
    findings: list[str],
) -> tuple[dict[str, Mapping[str, Any]], bool]:
    if not isinstance(value, list) or not value:
        findings.append("missing_consumer_target_reconciliation")
        return {}, False
    search_paths = {
        artifacts[artifact_id].resolve()
        for artifact_id in search_artifact_ids
        if artifact_id in artifacts
    }
    targets: dict[str, Mapping[str, Any]] = {}
    complete = True
    for row in value:
        if not isinstance(row, dict):
            findings.append("invalid_consumer_target_reconciliation")
            complete = False
            continue
        target_id = row.get("target_id")
        if (
            not isinstance(target_id, str)
            or not target_id
            or target_id in targets
        ):
            findings.append("invalid_or_duplicate_consumer_target_id")
            complete = False
            continue
        targets[target_id] = row
        job_id = row.get("discovered_by_job_id")
        job_state = (
            route_jobs.get(job_id) if isinstance(job_id, str) else None
        )
        if not isinstance(job_id, str) or job_state is None:
            findings.append(f"unaccounted_consumer_target_job:{target_id}")
            complete = False
        row_axis_ids = _string_set(
            row.get("axis_ids"),
            code="invalid_consumer_target_axis_ids",
            findings=findings,
        )
        if not row_axis_ids or not row_axis_ids.issubset(axis_ids):
            findings.append(f"consumer_target_references_unknown_axis:{target_id}")
            complete = False
        if not isinstance(row.get("locator"), str) or not row.get("locator"):
            findings.append(f"missing_consumer_target_locator:{target_id}")
            complete = False
        state = row.get("terminal_state")
        if state not in _TARGET_TERMINAL_STATES:
            findings.append(f"invalid_consumer_target_state:{target_id}")
            complete = False
            continue
        capture_artifact_id = row.get("native_artifact_id")
        if state in {"used", "captured_excluded"}:
            if job_state is not None and job_state != "completed":
                findings.append(f"nonterminal_consumer_target_job:{target_id}")
                complete = False
            if (
                not isinstance(capture_artifact_id, str)
                or capture_artifact_id not in artifacts
            ):
                findings.append(f"missing_consumer_target_native_body:{target_id}")
                complete = False
            elif (
                capture_artifact_id in search_artifact_ids
                or artifacts[capture_artifact_id].resolve() in search_paths
            ):
                findings.append(
                    f"serp_artifact_credited_as_native_body:{target_id}"
                )
                complete = False
        evidence_refs = row.get("evidence_refs")
        if state == "used":
            if not isinstance(evidence_refs, list) or not evidence_refs:
                findings.append(f"missing_consumer_target_evidence_refs:{target_id}")
                complete = False
            else:
                for ref in evidence_refs:
                    if not isinstance(ref, dict):
                        findings.append(f"invalid_consumer_target_evidence_ref:{target_id}")
                        complete = False
                        continue
                    key = (str(ref.get("family")), str(ref.get("unit_id")))
                    if key not in registry:
                        findings.append(f"unresolved_consumer_target_evidence_ref:{target_id}")
                        complete = False
        elif state != "no_material_yield" and not str(row.get("reason", "")).strip():
            findings.append(f"missing_consumer_target_reason:{target_id}")
            complete = False
    return targets, complete


def _validate_focused_search_jobs(
    axis: Mapping[str, Any],
    *,
    axis_id: str,
    route_jobs: Mapping[str, str],
    required: bool,
    current_contract: bool,
    inventory_digest: str | None,
    inventory_created_at: datetime | None,
    artifacts: Mapping[str, Path],
    search_jobs: Mapping[tuple[str, str], Mapping[str, Any]],
    targets: Mapping[str, Mapping[str, Any]],
    findings: list[str],
) -> bool:
    value = axis.get("focused_search_jobs")
    if not isinstance(value, list):
        if required:
            findings.append(f"missing_product_axis_focused_search:{axis_id}")
        return not required
    expected_goals = (
        _FOCUSED_SEARCH_GOALS
        if current_contract
        else _LEGACY_FOCUSED_SEARCH_GOALS
    )
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
        if goal not in expected_goals or goal in goals:
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
        if current_contract:
            if row.get("workstream") != "product_axis":
                findings.append(f"invalid_product_axis_search_workstream:{axis_id}")
                complete = False
            if row.get("axis_inventory_sha256") != inventory_digest:
                findings.append(f"product_axis_search_inventory_mismatch:{axis_id}")
                complete = False
            planned_at = _parse_iso_datetime(row.get("planned_at"))
            if (
                planned_at is None
                or inventory_created_at is None
                or planned_at <= inventory_created_at
            ):
                findings.append(f"product_axis_search_not_planned_after_inventory:{axis_id}")
                complete = False
            search_artifact_id = row.get("search_artifact_id")
            if (
                not isinstance(search_artifact_id, str)
                or search_artifact_id not in artifacts
            ):
                findings.append(f"missing_product_axis_search_artifact:{axis_id}")
                complete = False
            search_record = search_jobs.get(
                (str(search_artifact_id), str(job_id))
            )
            if search_record is None:
                findings.append(f"unresolved_product_axis_search_record:{axis_id}")
                complete = False
            else:
                if (
                    search_record.get("axis_id") != axis_id
                    or search_record.get("goal") != goal
                ):
                    findings.append(f"product_axis_search_record_mismatch:{axis_id}")
                    complete = False
                executed_at = _parse_iso_datetime(search_record.get("executed_at"))
                if (
                    planned_at is None
                    or executed_at is None
                    or executed_at < planned_at
                ):
                    findings.append(f"product_axis_search_executed_before_plan:{axis_id}")
                    complete = False
            target_ids = row.get("target_ids")
            if not isinstance(target_ids, list):
                findings.append(f"missing_product_axis_search_targets:{axis_id}")
                complete = False
            elif disposition == "captured" and not target_ids:
                findings.append(f"captured_product_axis_search_without_targets:{axis_id}")
                complete = False
            else:
                if search_record is not None and search_record.get(
                    "selected_target_ids"
                ) != target_ids:
                    findings.append(f"product_axis_search_target_inventory_mismatch:{axis_id}")
                    complete = False
                target_states: list[str] = []
                for target_id in target_ids:
                    target = targets.get(str(target_id))
                    if target is None:
                        findings.append(f"unresolved_product_axis_search_target:{axis_id}")
                        complete = False
                        continue
                    if target.get("discovered_by_job_id") != job_id:
                        findings.append(f"product_axis_search_target_job_mismatch:{axis_id}")
                        complete = False
                    if axis_id not in target.get("axis_ids", []):
                        findings.append(f"product_axis_search_target_axis_mismatch:{axis_id}")
                        complete = False
                    target_states.append(str(target.get("terminal_state")))
                if disposition == "captured" and "used" not in target_states:
                    findings.append(f"captured_product_axis_search_without_used_native_body:{axis_id}")
                    complete = False
                if disposition == "blocked_no_route" and any(
                    state not in {"blocked", "unavailable"}
                    for state in target_states
                ):
                    findings.append(f"blocked_product_axis_search_target_mismatch:{axis_id}")
                    complete = False
    if required and goals != expected_goals:
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
    current_contract: bool,
    decision_contract: bool,
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
        if decision_contract and row.get("disposition") in {
            "material",
            "blocked_material",
        }:
            maturity = row.get("decision_maturity")
            closure_basis = row.get("closure_basis")
            claim_ceiling = row.get("claim_ceiling")
            frontier_ids = row.get("decision_frontier_family_ids")
            if maturity not in _AXIS_DECISION_MATURITY:
                findings.append(f"invalid_product_axis_decision_maturity:{axis_id}")
                complete = False
            elif require_complete and maturity != "decision_mature":
                findings.append(f"open_product_axis_decision_frontier:{axis_id}")
                complete = False
            if maturity == "decision_mature":
                if closure_basis not in _AXIS_CLOSURE_BASES:
                    findings.append(f"invalid_product_axis_closure_basis:{axis_id}")
                    complete = False
                if claim_ceiling not in _AXIS_CLAIM_CEILINGS:
                    findings.append(f"invalid_product_axis_claim_ceiling:{axis_id}")
                    complete = False
                if (
                    not isinstance(frontier_ids, list)
                    or len(frontier_ids) != 2
                    or any(
                        not isinstance(item, str) or not item
                        for item in frontier_ids
                    )
                    or len(set(frontier_ids)) != 2
                ):
                    findings.append(
                        f"invalid_product_axis_decision_frontier:{axis_id}"
                    )
                    complete = False
            elif maturity == "open":
                if closure_basis is not None or claim_ceiling is not None:
                    findings.append(f"open_product_axis_has_closure_claim:{axis_id}")
                    complete = False
                if (
                    frontier_ids is not None
                    and frontier_ids != []
                    and frontier_ids != ()
                ):
                    findings.append(f"open_product_axis_has_decision_frontier:{axis_id}")
                    complete = False
                if row.get("decision_usefulness") is not None:
                    findings.append(
                        f"open_product_axis_has_decision_usefulness:{axis_id}"
                    )
                    complete = False
            else:
                complete = False

    retailer_corpora = _retailer_corpus_effective_counts(families)
    retailer_product_contexts = _retailer_corpus_product_contexts(families)
    coding_counts, coding_complete = _load_retailer_axis_coding(
        ledger.get("retailer_axis_coding"),
        ledger=ledger,
        artifacts=artifacts,
        retailer_corpora=retailer_corpora,
        retailer_product_contexts=retailer_product_contexts,
        axis_ids=set(axis_rows),
        findings=findings,
    )
    complete = complete and coding_complete
    registry = _consumer_support_registry(families)
    inventory_digest: str | None = None
    inventory_created_at: datetime | None = None
    community_axis_threads: dict[str, set[str]] = {}
    community_coded_fields: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    search_jobs: dict[tuple[str, str], Mapping[str, Any]] = {}
    targets: dict[str, Mapping[str, Any]] = {}
    if current_contract:
        inventory_digest, inventory_created_at, inventory_complete = (
            _load_consumer_axis_inventory(
                ledger.get("axis_inventory"),
                ledger=ledger,
                artifacts=artifacts,
                axis_rows=axis_rows,
                findings=findings,
            )
        )
        community_axis_threads, community_coded_fields, community_complete = (
            _load_community_axis_coding(
                ledger.get("community_axis_coding"),
                ledger=ledger,
                artifacts=artifacts,
                families=families,
                axis_ids=set(axis_rows),
                findings=findings,
            )
        )
        search_jobs, searches_complete = _load_consumer_phase2_searches(
            ledger=ledger,
            artifacts=artifacts,
            axis_rows=axis_rows,
            findings=findings,
        )
        search_artifact_ids = {
            artifact_id for artifact_id, _job_id in search_jobs
        }
        for record in search_jobs.values():
            packet_ids = record.get("serp_packet_artifact_ids")
            if isinstance(packet_ids, list):
                search_artifact_ids.update(
                    packet_id
                    for packet_id in packet_ids
                    if isinstance(packet_id, str)
                )
        targets, targets_complete = _validate_target_reconciliation(
            ledger.get("target_reconciliation"),
            artifacts=artifacts,
            registry=registry,
            axis_ids=set(axis_rows),
            route_jobs=route_jobs,
            search_artifact_ids=search_artifact_ids,
            findings=findings,
        )
        complete = (
            complete
            and inventory_complete
            and community_complete
            and searches_complete
            and targets_complete
        )
    for axis_id, axis in axis_rows.items():
        refs = axis.get("support_refs")
        family_origins: dict[str, set[str]] = {}
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
            if current_contract:
                if ref.get("contribution") not in _AXIS_SUPPORT_CONTRIBUTIONS:
                    findings.append(f"invalid_product_axis_support_contribution:{axis_id}")
                    complete = False
                choice = ref.get("choice")
                if choice not in _AXIS_SUPPORT_CHOICES:
                    findings.append(f"invalid_product_axis_support_choice:{axis_id}")
                    complete = False
                if choice == "alternative" and not str(
                    ref.get("alternative_brand", "")
                ).strip():
                    findings.append(f"missing_product_axis_support_alternative:{axis_id}")
                    complete = False
            if key not in registry:
                findings.append(f"unresolved_product_axis_support_ref:{axis_id}")
                complete = False
            else:
                origin_key = registry[key]
                if origin_key is not None:
                    family_origins.setdefault(str(family), set()).add(origin_key)
            if current_contract and family == "reddit_forum":
                if unit_id not in community_axis_threads.get(axis_id, set()):
                    findings.append(
                        f"uncoded_reddit_product_axis_support:{axis_id}"
                    )
                    complete = False
                elif (
                    ref.get("contribution") in _AXIS_SUPPORT_CONTRIBUTIONS
                    and ref.get("choice") in _AXIS_SUPPORT_CHOICES
                    and (
                        str(ref.get("contribution")),
                        str(ref.get("choice")),
                        str(ref.get("alternative_brand") or "").strip(),
                    )
                    not in community_coded_fields.get(
                        (axis_id, unit_id), set()
                    )
                ):
                    findings.append(
                        f"product_axis_support_not_backed_by_comment_coding:{axis_id}"
                    )
                    complete = False

        if (
            decision_contract
            and axis.get("disposition") in {"material", "blocked_material"}
            and axis.get("decision_maturity") == "decision_mature"
        ):
            usefulness = axis.get("decision_usefulness")
            if not isinstance(usefulness, dict):
                findings.append(
                    f"missing_product_axis_decision_usefulness:{axis_id}"
                )
                complete = False
            else:
                status = usefulness.get("status")
                if status not in _AXIS_DECISION_USEFULNESS_STATUSES:
                    findings.append(
                        f"invalid_product_axis_decision_usefulness_status:{axis_id}"
                    )
                    complete = False
                closure_basis = axis.get("closure_basis")
                if (
                    closure_basis == "evidence_supported"
                    and status not in {"strategically_material", "decision_useful"}
                ):
                    findings.append(
                        f"evidence_supported_axis_not_decision_useful:{axis_id}"
                    )
                    complete = False
                if (
                    closure_basis == "route_bounded_source_exhaustion"
                    and status != "source_exhausted_but_weak"
                ):
                    findings.append(
                        f"source_limited_axis_wrong_decision_usefulness:{axis_id}"
                    )
                    complete = False
                for field, finding in (
                    ("customer_tension", "missing_product_axis_customer_tension"),
                    (
                        "strongest_counterevidence",
                        "missing_product_axis_strongest_counterevidence",
                    ),
                    (
                        "competitive_decision",
                        "missing_product_axis_competitive_decision",
                    ),
                ):
                    if not isinstance(usefulness.get(field), str) or not str(
                        usefulness.get(field)
                    ).strip():
                        findings.append(f"{finding}:{axis_id}")
                        complete = False
                effects = usefulness.get("decision_effects")
                if not isinstance(effects, dict):
                    findings.append(f"missing_product_axis_decision_effects:{axis_id}")
                    complete = False
                else:
                    for field in (
                        "segment_or_condition",
                        "behavior_or_purchase_consequence",
                        "competitor_destination",
                    ):
                        if not isinstance(effects.get(field), str) or not str(
                            effects.get(field)
                        ).strip():
                            findings.append(
                                f"missing_product_axis_decision_effect:{axis_id}:{field}"
                            )
                            complete = False
                decision_refs = usefulness.get("decision_bearing_support_refs")
                minimum_refs = (
                    3 if closure_basis == "evidence_supported" else 1
                )
                decision_roles: set[str] = set()
                decision_ref_keys: set[tuple[str, str]] = set()
                if (
                    not isinstance(decision_refs, list)
                    or len(decision_refs) < minimum_refs
                ):
                    findings.append(
                        f"insufficient_product_axis_decision_support_refs:{axis_id}"
                    )
                    complete = False
                    decision_refs = []
                for ref in decision_refs:
                    if not isinstance(ref, dict):
                        findings.append(
                            f"invalid_product_axis_decision_support_ref:{axis_id}"
                        )
                        complete = False
                        continue
                    family = ref.get("family")
                    unit_id = ref.get("unit_id")
                    role = ref.get("role")
                    key = (str(family), str(unit_id))
                    if (
                        not isinstance(family, str)
                        or not family
                        or not isinstance(unit_id, str)
                        or not unit_id
                        or role not in _AXIS_DECISION_SUPPORT_ROLES
                        or key in decision_ref_keys
                    ):
                        findings.append(
                            f"invalid_product_axis_decision_support_ref:{axis_id}"
                        )
                        complete = False
                        continue
                    decision_ref_keys.add(key)
                    decision_roles.add(str(role))
                    if key not in seen_refs:
                        findings.append(
                            f"unresolved_product_axis_decision_support_ref:{axis_id}"
                        )
                        complete = False
                if closure_basis == "evidence_supported":
                    absence_marker = usefulness.get(
                        "counterevidence_absent_verified"
                    )
                    if absence_marker not in (None, True):
                        findings.append(
                            "invalid_product_axis_counterevidence_absence_marker"
                            f":{axis_id}"
                        )
                        complete = False
                    if absence_marker is True and "counterevidence" in decision_roles:
                        findings.append(
                            "contradictory_counterevidence_absence_marker"
                            f":{axis_id}"
                        )
                        complete = False
                    if (
                        "counterevidence" not in decision_roles
                        and absence_marker is not True
                    ):
                        findings.append(
                            f"missing_product_axis_counterevidence_ref:{axis_id}"
                        )
                        complete = False
                    if not decision_roles & {
                        "segment_or_condition",
                        "behavior_or_purchase_consequence",
                        "competitor_destination",
                    }:
                        findings.append(
                            f"missing_product_axis_decision_consequence_ref:{axis_id}"
                        )
                        complete = False
                limitations = usefulness.get("limitations")
                if (
                    not isinstance(limitations, list)
                    or not limitations
                    or any(
                        not isinstance(item, str) or not item.strip()
                        for item in limitations
                    )
                ):
                    findings.append(f"missing_product_axis_decision_limits:{axis_id}")
                    complete = False

        corpora_with_mentions, negative_choices, positive_choices = (
            _validate_axis_incidence(
                axis,
                axis_id=axis_id,
                coding_counts=coding_counts,
                corpora=set(retailer_corpora),
                findings=findings,
            )
        )
        family_counts = {
            family: len(origins) for family, origins in family_origins.items()
        }
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
        if decision_contract and axis.get("disposition") in {
            "material",
            "blocked_material",
        }:
            closure_basis = axis.get("closure_basis")
            claim_ceiling = axis.get("claim_ceiling")
            if closure_basis == "evidence_supported":
                if expected_strength != "strong":
                    findings.append(
                        f"evidence_supported_axis_not_strong:{axis_id}"
                    )
                    complete = False
                if claim_ceiling != "strong_qualitative":
                    findings.append(
                        f"evidence_supported_axis_wrong_claim_ceiling:{axis_id}"
                    )
                    complete = False
            elif closure_basis == "route_bounded_source_exhaustion":
                if claim_ceiling != "bounded_observation_only":
                    findings.append(
                        f"source_limited_axis_overclaims:{axis_id}"
                    )
                    complete = False
        search_required = axis.get("disposition") in {
            "material",
            "blocked_material",
        }
        if current_contract and search_required and len(seen_refs) < 3:
            exhaustion = axis.get("source_exhaustion")
            if not (
                isinstance(exhaustion, dict)
                and exhaustion.get("status") == "source_exhausted"
                and exhaustion.get("expected_minimum") == 3
                and exhaustion.get("observed_usable_units") == len(seen_refs)
                and isinstance(exhaustion.get("reason"), str)
                and exhaustion.get("reason")
            ):
                findings.append(f"product_axis_below_nonretailer_support_floor:{axis_id}")
                complete = False
        if not _validate_focused_search_jobs(
            axis,
            axis_id=axis_id,
            route_jobs=route_jobs,
            required=search_required,
            current_contract=current_contract,
            inventory_digest=inventory_digest,
            inventory_created_at=inventory_created_at,
            artifacts=artifacts,
            search_jobs=search_jobs,
            targets=targets,
            findings=findings,
        ):
            complete = False
    return complete


def _valid_reddit_floor_exception(
    ledger: Mapping[str, Any],
    *,
    observed: int,
    route_jobs: Mapping[str, str],
    decision_contract: bool,
) -> bool:
    value = ledger.get("reddit_forum_floor_exception")
    if not (
        isinstance(value, dict)
        and value.get("status") == "source_exhausted"
        and value.get("expected_minimum") == 40
        and value.get("observed_usable_threads") == observed
        and isinstance(value.get("reason"), str)
        and value.get("reason")
    ):
        return False
    targets = ledger.get("target_reconciliation")
    if not isinstance(targets, list) or not targets:
        return False
    if any(
        not isinstance(row, dict)
        or row.get("terminal_state") not in _TARGET_TERMINAL_STATES
        for row in targets
    ):
        return False
    axes = ledger.get("product_axes")
    if not isinstance(axes, list):
        return False
    for axis in axes:
        if not isinstance(axis, dict) or axis.get("disposition") not in {
            "material",
            "blocked_material",
        }:
            continue
        if decision_contract and (
            axis.get("decision_maturity") != "decision_mature"
            or axis.get("claim_ceiling") not in _AXIS_CLAIM_CEILINGS
        ):
            return False
        jobs = axis.get("focused_search_jobs")
        if not isinstance(jobs, list) or len(jobs) < 3:
            return False
        for job in jobs:
            if not isinstance(job, dict):
                return False
            state = route_jobs.get(str(job.get("job_id")))
            if state not in {"completed", "blocked"}:
                return False
    closure = ledger.get("closure")
    batches = closure.get("batches") if isinstance(closure, dict) else None
    if not isinstance(batches, list) or len(batches) < 2:
        return False
    zero_fields = {
        "new_material_seams",
        "changed_material_dispositions",
        "new_product_axes",
        "changed_axis_strengths",
        "changed_axis_incidence",
        "new_customer_segments",
        "new_product_conditions",
        "new_comparison_choices",
        "new_competitor_alternatives",
    }
    if not decision_contract:
        zero_fields.add("new_usable_reddit_threads")
    return all(
        isinstance(row, dict)
        and row.get("batch_kind") == "live_acquisition"
        and row.get("material_incremental_value") is False
        and (
            not decision_contract
            or (
                isinstance(row.get("material_additions"), list)
                and not row.get("material_additions")
            )
        )
        and all(row.get(field) == 0 for field in zero_fields)
        for row in batches[-2:]
    )


def _independent_reddit_thread_ids(ledger: Mapping[str, Any]) -> set[str]:
    families = ledger.get("families")
    reddit = families.get("reddit_forum") if isinstance(families, dict) else None
    rows = (
        reddit.get("threads")
        if isinstance(reddit, dict) and isinstance(reddit.get("threads"), list)
        else []
    )
    return {
        row["thread_id"]
        for row in rows
        if isinstance(row, dict)
        and row.get("independence") == "independent_thread"
        and isinstance(row.get("thread_id"), str)
        and row.get("thread_id")
    }


def _consumer_phase2_execution_times(
    ledger: Mapping[str, Any], artifacts: Mapping[str, Path]
) -> list[datetime]:
    """Return observed Phase 2 execution times from the pinned search artifacts.

    The search artifacts are validated separately. This helper deliberately
    reads their actual job timestamps instead of inferring Phase 2 chronology
    from a Reddit query-family role label.
    """
    job_keys = {
        (str(job.get("search_artifact_id")), str(job.get("job_id")))
        for axis in ledger.get("product_axes", [])
        if isinstance(axis, dict)
        for job in axis.get("focused_search_jobs", [])
        if isinstance(job, dict)
        and isinstance(job.get("search_artifact_id"), str)
        and isinstance(job.get("job_id"), str)
    }
    artifact_ids = {artifact_id for artifact_id, _job_id in job_keys}
    observed: list[datetime] = []
    for artifact_id in artifact_ids:
        path = artifacts.get(artifact_id)
        if path is None:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            continue
        for row in jobs:
            if not isinstance(row, dict):
                continue
            key = (artifact_id, str(row.get("job_id")))
            if key not in job_keys:
                continue
            executed_at = _parse_iso_datetime(row.get("executed_at"))
            if executed_at is not None:
                observed.append(executed_at)
    return observed


def _validate_reddit_candidate_frontier(
    ledger: Mapping[str, Any],
    *,
    artifacts: Mapping[str, Path],
    route_jobs: Mapping[str, str],
    require_complete: bool,
    decision_contract: bool,
    findings: list[str],
) -> bool:
    """The 40-thread floor is a minimum, never a completion target.

    A passing current-profile seal must prove that the bounded eligible
    candidate frontier was exhausted: every discovered candidate thread is
    terminally accounted, every credited ledger thread is a captured frontier
    candidate. The current decision contract separately proves that each axis
    crossed two varied, materially dry query-family frontiers; usable threads
    remain visible acquisition yield and do not themselves reopen an axis.
    """
    value = ledger.get("reddit_candidate_frontier")
    if not isinstance(value, dict):
        if require_complete:
            findings.append("passing_seal_without_reddit_frontier_exhaustion")
            findings.append("missing_reddit_frontier_discovery_jobs")
        return False
    complete = True
    if (
        value.get("status") != "source_exhausted"
        or not isinstance(value.get("reason"), str)
        or not value.get("reason")
    ):
        findings.append("invalid_reddit_frontier_status")
        complete = False
    material_axes = {
        str(row.get("axis_id"))
        for row in ledger.get("product_axes", [])
        if isinstance(row, dict)
        and row.get("disposition") in {"material", "blocked_material"}
        and isinstance(row.get("axis_id"), str)
        and row.get("axis_id")
    }
    discovery_jobs = value.get("discovery_jobs")
    discovery_by_id: dict[str, Mapping[str, Any]] = {}
    discovery_artifacts: dict[str, set[Path]] = {}
    discovery_executed_at: dict[str, datetime] = {}
    if not isinstance(discovery_jobs, list) or not discovery_jobs:
        findings.append("missing_reddit_frontier_discovery_jobs")
        complete = False
    else:
        for row in discovery_jobs:
            if not isinstance(row, dict):
                findings.append("invalid_reddit_frontier_discovery_job")
                complete = False
                continue
            job_id = row.get("job_id")
            if (
                not isinstance(job_id, str)
                or not job_id
                or job_id in discovery_by_id
            ):
                findings.append("invalid_or_duplicate_frontier_discovery_job")
                complete = False
                continue
            discovery_by_id[job_id] = row
            if route_jobs.get(job_id) != "completed":
                findings.append("frontier_discovery_job_not_completed")
                complete = False
            axis_id = row.get("axis_id")
            if not isinstance(axis_id, str) or axis_id not in material_axes:
                findings.append("invalid_frontier_discovery_axis")
                complete = False
            if not isinstance(row.get("query"), str) or not row.get(
                "query", ""
            ).strip():
                findings.append("missing_frontier_discovery_query")
                complete = False
            executed_at = _parse_iso_datetime(row.get("executed_at"))
            if executed_at is None:
                findings.append("invalid_frontier_discovery_executed_at")
                complete = False
            else:
                discovery_executed_at[job_id] = executed_at
            artifact_ids = row.get("artifact_ids")
            paths: set[Path] = set()
            if (
                not isinstance(artifact_ids, list)
                or not artifact_ids
                or any(
                    not isinstance(item, str) or not item
                    for item in artifact_ids
                )
            ):
                findings.append("missing_frontier_discovery_artifacts")
                complete = False
            else:
                for artifact_id in artifact_ids:
                    if artifact_id not in artifacts:
                        findings.append("unresolved_frontier_discovery_artifact")
                        complete = False
                        continue
                    paths.add(artifacts[artifact_id].resolve())
                if len(paths) != len(artifact_ids):
                    findings.append("duplicate_frontier_discovery_artifact_path")
                    complete = False
            discovery_artifacts[job_id] = paths
            candidate_ids = row.get("candidate_thread_ids")
            if (
                not isinstance(candidate_ids, list)
                or any(
                    not isinstance(item, str) or not item
                    for item in candidate_ids
                )
                or len(set(candidate_ids)) != len(candidate_ids)
            ):
                findings.append("invalid_frontier_discovery_candidate_ids")
                complete = False
    query_families: dict[str, Mapping[str, Any]] = {}
    family_jobs: dict[str, set[str]] = {}
    family_artifacts: dict[str, set[Path]] = {}
    family_started_at: dict[str, datetime] = {}
    family_completed_at: dict[str, datetime] = {}
    job_family: dict[str, str] = {}
    mandatory_family_ids_by_kind: dict[str, list[str]] = {}
    if decision_contract:
        family_rows = value.get("query_families")
        if not isinstance(family_rows, list) or not family_rows:
            findings.append("missing_reddit_frontier_query_families")
            complete = False
            family_rows = []
        for family in family_rows:
            if not isinstance(family, dict):
                findings.append("invalid_reddit_frontier_query_family")
                complete = False
                continue
            family_id = family.get("family_id")
            if (
                not isinstance(family_id, str)
                or not family_id
                or family_id in query_families
            ):
                findings.append("invalid_or_duplicate_reddit_query_family")
                complete = False
                continue
            query_families[family_id] = family
            family_kind = family.get("family_kind")
            family_role = family.get("family_role")
            if not isinstance(family_kind, str) or not family_kind:
                findings.append("missing_reddit_query_family_kind")
                complete = False
            if family_role not in _QUERY_FAMILY_ROLES:
                findings.append("invalid_reddit_query_family_role")
                complete = False
            if family.get("status") != "completed":
                findings.append("reddit_query_family_not_completed")
                complete = False
            planned_at = _parse_iso_datetime(family.get("planned_at"))
            if planned_at is None:
                findings.append("invalid_reddit_query_family_planned_at")
                complete = False
            scope_axis_ids = family.get("scope_axis_ids")
            if (
                not isinstance(scope_axis_ids, list)
                or not scope_axis_ids
                or any(
                    not isinstance(axis_id, str) or axis_id not in material_axes
                    for axis_id in scope_axis_ids
                )
            ):
                findings.append("invalid_reddit_query_family_axis_scope")
                complete = False
            job_ids = family.get("job_ids")
            jobs = (
                {str(job_id) for job_id in job_ids}
                if isinstance(job_ids, list)
                else set()
            )
            if (
                not jobs
                or len(jobs) != len(job_ids or [])
                or any(job_id not in discovery_by_id for job_id in jobs)
            ):
                findings.append("invalid_reddit_query_family_jobs")
                complete = False
            for job_id in jobs:
                if job_id in job_family:
                    findings.append("reddit_discovery_job_in_multiple_families")
                    complete = False
                job_family[job_id] = family_id
            family_jobs[family_id] = jobs
            family_artifacts[family_id] = set().union(
                *(discovery_artifacts.get(job_id, set()) for job_id in jobs)
            )
            execution_times = [
                discovery_executed_at[job_id]
                for job_id in jobs
                if job_id in discovery_executed_at
            ]
            if len(execution_times) == len(jobs) and execution_times:
                family_started_at[family_id] = min(execution_times)
                family_completed_at[family_id] = max(execution_times)
            if family_role == "mandatory_high_yield" and isinstance(
                family_kind, str
            ):
                mandatory_family_ids_by_kind.setdefault(family_kind, []).append(
                    family_id
                )
        if set(job_family) != set(discovery_by_id):
            findings.append("unassigned_reddit_discovery_job_family")
            complete = False
        mandatory_kinds = {
            str(family.get("family_kind"))
            for family in query_families.values()
            if family.get("family_role") == "mandatory_high_yield"
        }
        if not _MANDATORY_HIGH_YIELD_FAMILY_KINDS <= mandatory_kinds:
            findings.append("missing_mandatory_high_yield_query_family")
            complete = False
        mandatory_completed_at = [
            family_completed_at[family_id]
            for family_ids in mandatory_family_ids_by_kind.values()
            for family_id in family_ids
            if family_id in family_completed_at
        ]
        phase2_execution_times = _consumer_phase2_execution_times(
            ledger, artifacts
        )
        if mandatory_completed_at and phase2_execution_times:
            mandatory_completed = max(mandatory_completed_at)
            phase2_started = min(phase2_execution_times)
            order_violation = mandatory_completed >= phase2_started
            exception = value.get("execution_order_exception")
            if order_violation:
                valid_exception = (
                    isinstance(exception, dict)
                    and exception.get("exception_type")
                    == "pre_contract_historical_run"
                    and phase2_started < _EXECUTION_ORDER_CONTRACT_ADOPTED_AT
                    and exception.get("cycle_id") == ledger.get("cycle_id")
                    and _parse_iso_datetime(exception.get("phase2_started_at"))
                    == phase2_started
                    and _parse_iso_datetime(
                        exception.get("mandatory_families_completed_at")
                    )
                    == mandatory_completed
                    and exception.get("future_runs_covered") is False
                    and isinstance(exception.get("reason"), str)
                    and bool(exception.get("reason").strip())
                )
                if not valid_exception:
                    if exception is not None:
                        findings.append(
                            "invalid_reddit_execution_order_exception"
                        )
                    findings.append(
                        "mandatory_high_yield_query_family_not_pre_phase2"
                    )
                    complete = False
            elif exception is not None:
                findings.append("unnecessary_reddit_execution_order_exception")
                complete = False
        for earlier_kind, later_kind in zip(
            _MANDATORY_HIGH_YIELD_FAMILY_ORDER[:-1],
            _MANDATORY_HIGH_YIELD_FAMILY_ORDER[1:],
            strict=True,
        ):
            earlier_completed = [
                family_completed_at[family_id]
                for family_id in mandatory_family_ids_by_kind.get(earlier_kind, [])
                if family_id in family_completed_at
            ]
            later_started = [
                family_started_at[family_id]
                for family_id in mandatory_family_ids_by_kind.get(later_kind, [])
                if family_id in family_started_at
            ]
            if (
                earlier_completed
                and later_started
                and max(earlier_completed) >= min(later_started)
            ):
                findings.append("mandatory_high_yield_query_family_out_of_order")
                complete = False

    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        findings.append("missing_reddit_frontier_candidates")
        return False
    seen: set[str] = set()
    captured: set[str] = set()
    candidate_rows: list[Mapping[str, Any]] = []
    for row in candidates:
        if not isinstance(row, dict):
            findings.append("invalid_reddit_frontier_candidate")
            complete = False
            continue
        thread_id = row.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id or thread_id in seen:
            findings.append("invalid_or_duplicate_frontier_candidate")
            complete = False
            continue
        seen.add(thread_id)
        candidate_rows.append(row)
        state = row.get("terminal_state")
        if state not in _FRONTIER_CANDIDATE_STATES:
            findings.append("invalid_frontier_candidate_state")
            complete = False
            continue
        job_id = row.get("discovered_by_job_id")
        if (
            not isinstance(job_id, str)
            or job_id not in discovery_by_id
            or route_jobs.get(job_id) != "completed"
        ):
            findings.append("unaccounted_frontier_candidate_job")
            complete = False
        if state == "captured_used":
            captured.add(thread_id)
        elif not str(row.get("reason", "")).strip():
            findings.append("missing_frontier_candidate_reason")
            complete = False
    candidates_by_job: dict[str, set[str]] = {}
    for row in candidate_rows:
        job_id = row.get("discovered_by_job_id")
        thread_id = row.get("thread_id")
        if isinstance(job_id, str) and isinstance(thread_id, str):
            candidates_by_job.setdefault(job_id, set()).add(thread_id)
    for job_id, row in discovery_by_id.items():
        declared_ids = row.get("candidate_thread_ids")
        if (
            isinstance(declared_ids, list)
            and all(isinstance(item, str) and item for item in declared_ids)
            and set(declared_ids) != candidates_by_job.get(job_id, set())
        ):
            findings.append("frontier_discovery_candidate_mismatch")
            complete = False
    thread_ids = _independent_reddit_thread_ids(ledger)
    if thread_ids - captured:
        findings.append("frontier_missing_ledger_thread")
        complete = False
    if captured - thread_ids:
        findings.append("frontier_captured_thread_not_in_ledger")
        complete = False
    closure = ledger.get("closure")
    batches = closure.get("batches") if isinstance(closure, dict) else None
    if decision_contract and isinstance(batches, list):
        batch_by_family: dict[str, Mapping[str, Any]] = {}
        additions_by_family_axis: dict[tuple[str, str], int] = {}
        for batch in batches:
            if not isinstance(batch, dict):
                continue
            family_id = batch.get("query_family_id")
            if not isinstance(family_id, str) or family_id not in query_families:
                findings.append("saturation_batch_unknown_query_family")
                complete = False
                continue
            if family_id in batch_by_family:
                findings.append("duplicate_saturation_batch_query_family")
                complete = False
            batch_by_family[family_id] = batch
            batch_job_ids = (
                {str(job_id) for job_id in batch.get("job_ids", [])}
                if isinstance(batch.get("job_ids"), list)
                else set()
            )
            if batch_job_ids != family_jobs.get(family_id, set()):
                findings.append("saturation_batch_query_family_job_mismatch")
                complete = False
            observed = sum(
                1
                for row in candidate_rows
                if row.get("terminal_state") == "captured_used"
                and str(row.get("discovered_by_job_id")) in batch_job_ids
            )
            declared = batch.get("new_usable_reddit_threads")
            if (
                isinstance(declared, int)
                and not isinstance(declared, bool)
                and declared != observed
            ):
                findings.append("saturation_batch_usable_thread_count_mismatch")
                complete = False
            additions = batch.get("material_additions")
            if isinstance(additions, list):
                for addition in additions:
                    if not isinstance(addition, dict):
                        continue
                    for axis_id in addition.get("axis_ids", []):
                        if isinstance(axis_id, str):
                            key = (family_id, axis_id)
                            additions_by_family_axis[key] = (
                                additions_by_family_axis.get(key, 0) + 1
                            )
        if set(batch_by_family) != set(query_families):
            findings.append("reddit_query_family_without_saturation_batch")
            complete = False
        mandatory_cutoff = (
            max(mandatory_completed_at) if mandatory_completed_at else None
        )
        for axis in ledger.get("product_axes", []):
            if (
                not isinstance(axis, dict)
                or axis.get("disposition") not in {"material", "blocked_material"}
            ):
                continue
            axis_id = str(axis.get("axis_id"))
            frontier_ids = axis.get("decision_frontier_family_ids")
            if not isinstance(frontier_ids, list) or len(frontier_ids) != 2:
                continue
            selected: list[Mapping[str, Any]] = []
            for family_id in frontier_ids:
                family = query_families.get(str(family_id))
                if family is None:
                    findings.append(
                        f"unresolved_product_axis_decision_frontier:{axis_id}"
                    )
                    complete = False
                    continue
                selected.append(family)
                if axis_id not in family.get("scope_axis_ids", []):
                    findings.append(
                        f"decision_frontier_family_missing_axis_scope:{axis_id}"
                    )
                    complete = False
                if family.get("family_role") != "continuation":
                    findings.append(
                        f"decision_frontier_family_not_continuation:{axis_id}"
                    )
                    complete = False
                started_at = family_started_at.get(str(family_id))
                if (
                    mandatory_cutoff is None
                    or started_at is None
                    or started_at <= mandatory_cutoff
                ):
                    findings.append(
                        f"decision_frontier_precedes_mandatory_families:{axis_id}"
                    )
                    complete = False
                batch = batch_by_family.get(str(family_id))
                if batch is None or batch.get("batch_kind") != "live_acquisition":
                    findings.append(
                        f"decision_frontier_family_not_live_acquisition:{axis_id}"
                    )
                    complete = False
                if additions_by_family_axis.get((str(family_id), axis_id), 0):
                    findings.append(
                        f"decision_frontier_family_not_materially_dry:{axis_id}"
                    )
                    complete = False
            if len(selected) != 2:
                continue
            selected_times = [
                (
                    family_started_at.get(str(family_id)),
                    family_completed_at.get(str(family_id)),
                )
                for family_id in frontier_ids
            ]
            if all(
                started_at is not None and completed_at is not None
                for started_at, completed_at in selected_times
            ):
                first_started, first_completed = selected_times[0]
                second_started, _second_completed = selected_times[1]
                if first_completed >= second_started:
                    findings.append(
                        f"out_of_order_product_axis_decision_frontier:{axis_id}"
                    )
                    complete = False
                frontier_start = min(first_started, second_started)
                later_addition = any(
                    affected_axis == axis_id
                    and family_completed_at.get(family_id) is not None
                    and family_completed_at[family_id] >= frontier_start
                    and family_id not in set(map(str, frontier_ids))
                    for (family_id, affected_axis) in additions_by_family_axis
                )
                if later_addition:
                    findings.append(
                        f"decision_frontier_precedes_material_addition:{axis_id}"
                    )
                    complete = False
            if selected[0].get("family_kind") == selected[1].get("family_kind"):
                findings.append(f"repeated_decision_frontier_family_kind:{axis_id}")
                complete = False
            first_id, second_id = map(str, frontier_ids)
            first_queries = {
                str(discovery_by_id[job_id].get("query", "")).strip().casefold()
                for job_id in family_jobs.get(first_id, set())
                if job_id in discovery_by_id
            }
            second_queries = {
                str(discovery_by_id[job_id].get("query", "")).strip().casefold()
                for job_id in family_jobs.get(second_id, set())
                if job_id in discovery_by_id
            }
            if first_queries & second_queries:
                findings.append(f"repeated_decision_frontier_query:{axis_id}")
                complete = False
            if family_artifacts.get(first_id, set()) & family_artifacts.get(
                second_id, set()
            ):
                findings.append(
                    f"shared_decision_frontier_discovery_artifact:{axis_id}"
                )
                complete = False
    elif isinstance(batches, list) and len(batches) >= 2:
        final_queries: dict[str, set[str]] = {}
        final_artifact_paths: set[Path] = set()
        for batch in batches[-2:]:
            if not isinstance(batch, dict):
                continue
            job_ids = batch.get("job_ids")
            batch_jobs = (
                {str(job_id) for job_id in job_ids}
                if isinstance(job_ids, list)
                else set()
            )
            if not batch_jobs or any(
                job_id not in discovery_by_id for job_id in batch_jobs
            ):
                findings.append("saturation_batch_not_reddit_frontier_discovery")
                complete = False
            batch_axes = {
                str(discovery_by_id[job_id].get("axis_id"))
                for job_id in batch_jobs
                if job_id in discovery_by_id
            }
            if batch_axes != material_axes:
                findings.append("saturation_batch_missing_reddit_axis_coverage")
                complete = False
            for job_id in batch_jobs:
                discovery = discovery_by_id.get(job_id)
                if discovery is None:
                    continue
                axis_id = str(discovery.get("axis_id"))
                query = str(discovery.get("query", "")).strip().casefold()
                if query and query in final_queries.setdefault(axis_id, set()):
                    findings.append("repeated_final_frontier_query")
                    complete = False
                final_queries[axis_id].add(query)
                paths = discovery_artifacts.get(job_id, set())
                if paths & final_artifact_paths:
                    findings.append("shared_final_frontier_discovery_artifact")
                    complete = False
                final_artifact_paths.update(paths)
            observed = sum(
                1
                for row in candidate_rows
                if row.get("terminal_state") == "captured_used"
                and str(row.get("discovered_by_job_id")) in batch_jobs
            )
            declared = batch.get("new_usable_reddit_threads")
            if (
                isinstance(declared, int)
                and not isinstance(declared, bool)
                and declared != observed
            ):
                findings.append("saturation_batch_usable_thread_count_mismatch")
                complete = False
    return complete


def _validate_depth_closure(
    value: Any,
    *,
    require_complete: bool,
    consumer_brand: bool = False,
    current_consumer_contract: bool = False,
    previous_consumer_contract: bool = False,
    axis_maturity: Mapping[str, Any] | None = None,
    route_jobs: Mapping[str, str] | None = None,
    findings: list[str],
) -> bool:
    if not isinstance(value, dict):
        findings.append("missing_evidence_depth_closure")
        return False
    material_axes = set(axis_maturity) if axis_maturity else set()
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
    if current_consumer_contract:
        frontier = value.get("decision_frontier")
        expected_mature = {
            axis_id
            for axis_id, maturity in (axis_maturity or {}).items()
            if maturity == "decision_mature"
        }
        expected_open = material_axes - expected_mature
        if not isinstance(frontier, dict):
            findings.append("missing_phase_a_decision_frontier")
            complete = False
        else:
            mature = frontier.get("decision_mature_axis_ids")
            open_axes = frontier.get("open_axis_ids")
            status = frontier.get("status")
            if status not in {"decision_mature", "open"}:
                findings.append("invalid_phase_a_decision_frontier_status")
                complete = False
            elif status != "decision_mature":
                if require_complete:
                    findings.append("phase_a_decision_frontier_not_mature")
                complete = False
            if (
                not isinstance(mature, list)
                or not isinstance(open_axes, list)
                or set(map(str, mature)) != expected_mature
                or set(map(str, open_axes)) != expected_open
            ):
                findings.append("phase_a_decision_frontier_axis_mismatch")
                complete = False
            if isinstance(open_axes, list) and open_axes:
                if status == "decision_mature":
                    findings.append("phase_a_decision_frontier_has_open_axes")
                elif require_complete:
                    findings.append("phase_a_decision_frontier_has_open_axes")
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
        if current_consumer_contract or previous_consumer_contract:
            batch_job_ids: set[str] = set()
            for row in batches:
                if not isinstance(row, dict):
                    continue
                job_ids = row.get("job_ids")
                if not isinstance(job_ids, list):
                    continue
                for job_id in job_ids:
                    if str(job_id) in batch_job_ids:
                        findings.append("duplicate_saturation_batch_job")
                        complete = False
                    batch_job_ids.add(str(job_id))
        rows_to_check = batches if current_consumer_contract else batches[-2:]
        for row in rows_to_check:
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
            elif not current_consumer_contract and material_value is not False:
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
            if current_consumer_contract or previous_consumer_contract:
                batch_fields.extend(
                    [
                        "new_customer_segments",
                        "new_product_conditions",
                        "new_comparison_choices",
                        "new_competitor_alternatives",
                    ]
                )
                if previous_consumer_contract:
                    batch_fields.append("new_usable_reddit_threads")
                if row.get("batch_kind") != "live_acquisition":
                    findings.append("saturation_batch_not_live_acquisition")
                    complete = False
                job_ids = row.get("job_ids")
                if not isinstance(job_ids, list) or not job_ids:
                    findings.append("saturation_batch_missing_job_ids")
                    complete = False
                else:
                    states = route_jobs or {}
                    for job_id in job_ids:
                        if states.get(str(job_id)) not in {"completed", "blocked"}:
                            findings.append("saturation_batch_job_not_terminal")
                            complete = False
            if current_consumer_contract:
                if not isinstance(row.get("query_family_id"), str) or not row.get(
                    "query_family_id"
                ):
                    findings.append("saturation_batch_missing_query_family_id")
                    complete = False
                new_usable = row.get("new_usable_reddit_threads")
                if (
                    not isinstance(new_usable, int)
                    or isinstance(new_usable, bool)
                    or new_usable < 0
                ):
                    findings.append(
                        "invalid_saturation_batch_new_usable_reddit_threads"
                    )
                    complete = False
                additions = row.get("material_additions")
                if not isinstance(additions, list):
                    findings.append("invalid_saturation_batch_material_additions")
                    complete = False
                else:
                    for addition in additions:
                        if not isinstance(addition, dict):
                            findings.append("invalid_material_addition")
                            complete = False
                            continue
                        if addition.get("kind") not in _MATERIAL_ADDITION_KINDS:
                            findings.append("invalid_material_addition_kind")
                            complete = False
                        addition_axes = addition.get("axis_ids")
                        if (
                            not isinstance(addition_axes, list)
                            or not addition_axes
                            or any(
                                not isinstance(axis_id, str)
                                or axis_id not in (material_axes or set())
                                for axis_id in addition_axes
                            )
                        ):
                            findings.append("invalid_material_addition_axes")
                            complete = False
                        evidence_refs = addition.get("evidence_refs")
                        if (
                            not isinstance(evidence_refs, list)
                            or not evidence_refs
                            or any(not isinstance(ref, str) or not ref for ref in evidence_refs)
                        ):
                            findings.append("invalid_material_addition_evidence")
                            complete = False
                        if not isinstance(addition.get("decision_effect"), str) or not addition.get(
                            "decision_effect"
                        ):
                            findings.append("missing_material_addition_decision_effect")
                            complete = False
                    if isinstance(material_value, bool) and material_value != bool(
                        additions
                    ):
                        findings.append("material_addition_value_mismatch")
                        complete = False
            for field in batch_fields:
                metric = row.get(field)
                if (
                    not isinstance(metric, int)
                    or isinstance(metric, bool)
                    or metric < 0
                ):
                    findings.append(f"invalid_saturation_batch_{field}")
                    complete = False
                elif metric != 0 and not current_consumer_contract:
                    if require_complete:
                        findings.append(f"saturation_batch_nonzero_{field}")
                    complete = False
            if current_consumer_contract and isinstance(
                row.get("material_additions"), list
            ):
                has_legacy_material_counter = any(
                    isinstance(row.get(field), int)
                    and not isinstance(row.get(field), bool)
                    and row.get(field) > 0
                    for field in batch_fields
                )
                if has_legacy_material_counter and not row.get("material_additions"):
                    findings.append("material_addition_counter_mismatch")
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


def _validate_understanding_route(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    valid_pass: bool,
    allow_preversion_route: bool,
    findings: list[str],
) -> None:
    """Enforce the seal-recorded route version and its current obligations.

    Shape checks only: relationship interpretation, campaign clustering, and
    competitor directness remain evidence-backed judgment.
    """
    route = seal.get("understanding_route")
    if not isinstance(route, dict) or not route.get("route_version"):
        if not allow_preversion_route:
            findings.append("missing_understanding_route_version")
        return
    version = route.get("route_version")
    if not _is_enum_value(version, UNDERSTANDING_ROUTE_VERSIONS):
        findings.append("invalid_understanding_route_version")
        return
    if version != CURRENT_UNDERSTANDING_ROUTE_VERSION:
        # Like the legacy seal and ledger switches, reading an older recorded
        # route is an explicit historical audit, never a flag-free
        # current-contract pass.
        if not allow_preversion_route:
            findings.append(
                "noncurrent_route_version_requires_explicit_historical_audit"
            )
            return
    if version not in _ROUTE_REVISION_1_1_OBLIGATION_VERSIONS:
        # Pre-1.1.0 routes carried none of the obligations below.
        return
    # An authorized historical audit still enforces the obligations the
    # stamped version itself carried; later-version obligations are gated
    # per-check below and are never back-claimed onto an older seal.
    rows = seal.get("route_job_accounting")
    if isinstance(rows, list):
        campaign_row = next(
            (
                item
                for item in rows
                if isinstance(item, dict)
                and item.get("route_id") == _CAMPAIGN_INTEGRATION_ROUTE_ID
            ),
            None,
        )
        # Presence, phase, required-flag, and completion accounting flow
        # through the mandatory-route machinery via conditional_routes; the
        # integration row must additionally be material so blocked jobs
        # cannot ride a non-material waiver into a passing seal.
        if campaign_row is not None and campaign_row.get("material") is not True:
            findings.append("campaign_integration_route_not_material")
    _validate_comparator_closure(
        route.get("comparator_closure"),
        repo_root=repo_root,
        valid_pass=valid_pass,
        route_version=version,
        findings=findings,
    )
    _validate_campaign_integration(
        route.get("campaign_evidence_integration"),
        seal=seal,
        repo_root=repo_root,
        valid_pass=valid_pass,
        findings=findings,
    )
    _validate_verification_requests(
        route.get("verification_requests"),
        repo_root=repo_root,
        valid_pass=valid_pass,
        findings=findings,
    )
    _validate_retailer_state_accounting(
        route.get("retailer_state_accounting"), findings=findings
    )


def _forbidden_synthetic_keys(
    value: Any, *, exempt: frozenset[str] = frozenset()
) -> set[str]:
    """Recursively collect forbidden synthetic-conclusion field names.

    ``exempt`` names are permitted at the top level of ``value`` only (the
    source-local ``rank`` inside one observed position); nested shapes never
    inherit the exemption, so a renested rank/share field cannot bypass the
    source-local limitation.
    """
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if (
                key in _COMPARATOR_FORBIDDEN_SYNTHETIC_FIELDS
                and key not in exempt
            ):
                found.add(key)
            found |= _forbidden_synthetic_keys(nested)
    elif isinstance(value, list):
        for item in value:
            found |= _forbidden_synthetic_keys(item)
    return found


def _validate_comparator_prefanout_qualification(
    row: Mapping[str, Any],
    *,
    candidate_id: str,
    route_version: str,
    findings: list[str],
) -> None:
    qualification = row.get("prefanout_qualification")
    if not isinstance(qualification, dict):
        findings.append(
            f"missing_comparator_prefanout_qualification:{candidate_id}"
        )
        return

    posture = qualification.get("posture")
    if not _is_enum_value(posture, _COMPARATOR_PREFANOUT_POSTURES):
        findings.append(f"invalid_comparator_prefanout_posture:{candidate_id}")
    comparator_role = qualification.get("comparator_role")
    if not _is_enum_value(comparator_role, _COMPARATOR_PREFANOUT_ROLES):
        findings.append(f"invalid_comparator_prefanout_role:{candidate_id}")

    # Every frame row points to the open-comparator SERP observation that
    # surfaced it, so discovery provenance survives a weaker posture too.
    search_refs = qualification.get("open_comparator_search_refs")
    if (
        not isinstance(search_refs, list)
        or not search_refs
        or any(not isinstance(ref, str) or not ref for ref in search_refs)
    ):
        findings.append(
            "invalid_comparator_prefanout_open_comparator_search:"
            + candidate_id
        )

    # Identity evidence is typed per product: an untyped list cannot show that
    # both named products were bound, because two refs to the same product
    # would satisfy a bar that names both.
    identity_evidence = qualification.get("identity_evidence_refs")
    identity_sides: dict[str, list[str]] = {}
    if not isinstance(identity_evidence, dict):
        findings.append(
            f"invalid_comparator_prefanout_identity_evidence:{candidate_id}"
        )
    else:
        for side in ("subject", "competitor"):
            refs = identity_evidence.get(side)
            if not isinstance(refs, list) or any(
                not isinstance(ref, str) or not ref for ref in refs
            ):
                findings.append(
                    "invalid_comparator_prefanout_identity_evidence:"
                    + f"{candidate_id}:{side}"
                )
                continue
            identity_sides[side] = list(refs)

    origins = qualification.get("independent_comparison_origins")
    valid_origin_keys: set[str] = set()
    valid_source_roles: set[str] = set()
    credited_origin_evidence: set[str] = set()
    public_actor_keys: set[str] = set()
    identity_check_required = (
        route_version in _ROUTE_REVISION_1_3_OBLIGATION_VERSIONS
    )
    if not isinstance(origins, list):
        findings.append(f"invalid_comparator_prefanout_origins:{candidate_id}")
        origins = []
    for origin in origins:
        if not isinstance(origin, dict):
            findings.append(f"invalid_comparator_prefanout_origin:{candidate_id}")
            continue
        origin_key = origin.get("origin_key")
        valid_origin_key = isinstance(origin_key, str) and bool(origin_key)
        if not valid_origin_key:
            findings.append(
                f"missing_comparator_prefanout_origin_key:{candidate_id}"
            )
        elif origin_key in valid_origin_keys:
            findings.append(
                f"duplicate_comparator_prefanout_origin_key:{candidate_id}"
            )
        else:
            valid_origin_keys.add(origin_key)
        source_role = origin.get("source_role")
        valid_source_role = _is_enum_value(
            source_role, _COMPARATOR_PREFANOUT_SOURCE_ROLES
        )
        if not valid_source_role:
            findings.append(
                f"invalid_comparator_prefanout_source_role:{candidate_id}"
            )
        identity_credited = True
        if identity_check_required:
            public_actor_key = origin.get("public_actor_key")
            overlap_posture = origin.get("identity_overlap_posture")
            normalized_actor_key = (
                public_actor_key.strip().casefold()
                if isinstance(public_actor_key, str)
                else ""
            )
            valid_public_actor_key = (
                bool(normalized_actor_key)
                and normalized_actor_key != "unavailable"
            )
            if not isinstance(public_actor_key, str) or not public_actor_key:
                findings.append(
                    "missing_comparator_prefanout_public_actor_key:"
                    + candidate_id
                )
            if not _is_enum_value(
                overlap_posture, _COMPARATOR_ACTOR_OVERLAP_POSTURES
            ):
                findings.append(
                    "invalid_comparator_prefanout_identity_overlap_posture:"
                    + candidate_id
                )
                identity_credited = False
            elif overlap_posture != "no_match_observed":
                identity_credited = False
            elif not valid_public_actor_key:
                findings.append(
                    "comparator_prefanout_identity_credit_without_actor_key:"
                    + candidate_id
                )
                identity_credited = False
            elif normalized_actor_key in public_actor_keys:
                findings.append(
                    "duplicate_comparator_prefanout_public_actor_key:"
                    + f"{candidate_id}:{normalized_actor_key}"
                )
                identity_credited = False
            else:
                public_actor_keys.add(normalized_actor_key)
        evidence_refs = origin.get("evidence_refs")
        if (
            not isinstance(evidence_refs, list)
            or not evidence_refs
            or any(
                not isinstance(evidence_ref, str) or not evidence_ref
                for evidence_ref in evidence_refs
            )
        ):
            findings.append(
                f"missing_comparator_prefanout_origin_evidence:{candidate_id}"
            )
            continue
        # An origin that re-cites another origin's evidence unit is an alias
        # of one underlying origin, not independent repeated comparison.
        shared = credited_origin_evidence.intersection(evidence_refs)
        if shared:
            findings.append(
                "shared_comparator_prefanout_origin_evidence:"
                + f"{candidate_id}:{','.join(sorted(shared))}"
            )
            identity_credited = False
        credited_origin_evidence.update(evidence_refs)
        if identity_credited and valid_origin_key and valid_source_role:
            valid_source_roles.add(source_role)
        elif identity_check_required and valid_origin_key:
            valid_origin_keys.discard(origin_key)

    if posture == "core_fanout":
        for identity_key in (
            "subject_product_identity",
            "competitor_product_identity",
        ):
            identity = row.get(identity_key)
            if not isinstance(identity, str) or not identity:
                findings.append(
                    "comparator_core_fanout_without_exact_identity:"
                    + candidate_id
                )
                break
        for side in ("subject", "competitor"):
            if side in identity_sides and not identity_sides[side]:
                findings.append(
                    "insufficient_comparator_prefanout_identity_evidence:"
                    + f"{candidate_id}:{side}"
                )
        if _is_enum_value(
            comparator_role, {"adjacent", "unresolved", "non_competitor"}
        ):
            findings.append(
                f"invalid_comparator_core_fanout_role:{candidate_id}"
            )
        shared_job = qualification.get("shared_job")
        if not isinstance(shared_job, str) or not shared_job:
            findings.append(
                f"missing_comparator_prefanout_shared_job:{candidate_id}"
            )
        if len(valid_origin_keys) < 2:
            findings.append(
                f"insufficient_comparator_prefanout_origins:{candidate_id}"
            )
        if len(valid_source_roles) < 2:
            findings.append(
                "insufficient_comparator_prefanout_source_roles:"
                + candidate_id
            )
    elif _is_enum_value(posture, {"bounded_watch", "rejected_before_fanout"}):
        gap_reason = qualification.get("gap_reason")
        if not isinstance(gap_reason, str) or not gap_reason:
            findings.append(
                f"comparator_prefanout_gap_without_reason:{candidate_id}"
            )
        if (
            posture == "rejected_before_fanout"
            and comparator_role != "non_competitor"
        ):
            findings.append(
                f"invalid_comparator_prefanout_rejection_role:{candidate_id}"
            )


def _validate_comparator_choice_explanation(
    explanation: Any,
    *,
    candidate_id: str,
    shared_axis_ids: Any,
    promoted: bool,
    findings: list[str],
) -> None:
    if not isinstance(explanation, dict):
        findings.append(f"missing_comparator_choice_explanation:{candidate_id}")
        return

    status = explanation.get("status")
    if not _is_enum_value(status, _COMPARATOR_CHOICE_STATUSES):
        findings.append(f"invalid_comparator_choice_status:{candidate_id}")
    summary = explanation.get("summary")
    if not isinstance(summary, str) or not summary:
        findings.append(f"missing_comparator_choice_summary:{candidate_id}")

    final_role = explanation.get("final_comparator_role")
    if not _is_enum_value(final_role, _COMPARATOR_PREFANOUT_ROLES):
        findings.append(f"invalid_comparator_final_role:{candidate_id}")
    role_rationale = explanation.get("role_rationale")
    if not isinstance(role_rationale, str) or not role_rationale:
        findings.append(f"missing_comparator_final_role_rationale:{candidate_id}")
    role_refs = explanation.get("role_evidence_refs")
    valid_role_refs = (
        isinstance(role_refs, list)
        and bool(role_refs)
        and all(isinstance(ref, str) and ref for ref in role_refs)
    )
    if final_role != "unresolved" and not valid_role_refs:
        findings.append(f"missing_comparator_final_role_evidence:{candidate_id}")

    axis_findings = explanation.get("axis_findings")
    if not isinstance(axis_findings, list):
        findings.append(f"invalid_comparator_choice_axes:{candidate_id}")
        axis_findings = []
    if status == "observed" and not axis_findings:
        findings.append(f"observed_comparator_choice_without_axes:{candidate_id}")
    seen_axis_ids: set[str] = set()
    shared_axis_set = (
        {axis_id for axis_id in shared_axis_ids if isinstance(axis_id, str)}
        if isinstance(shared_axis_ids, list)
        else set()
    )
    for axis_row in axis_findings:
        if not isinstance(axis_row, dict):
            findings.append(f"invalid_comparator_choice_axis:{candidate_id}")
            continue
        axis_id = axis_row.get("axis_id")
        if (
            not isinstance(axis_id, str)
            or not axis_id
            or axis_id in seen_axis_ids
        ):
            findings.append(f"invalid_comparator_choice_axis_id:{candidate_id}")
        else:
            seen_axis_ids.add(axis_id)
            if shared_axis_set and axis_id not in shared_axis_set:
                findings.append(
                    f"comparator_choice_axis_not_shared:{candidate_id}:{axis_id}"
                )
        if not _is_enum_value(
            axis_row.get("choice_posture"), _COMPARATOR_CHOICE_POSTURES
        ):
            findings.append(
                f"invalid_comparator_choice_axis_posture:{candidate_id}"
            )
        if not isinstance(axis_row.get("why"), str) or not axis_row.get("why"):
            findings.append(f"missing_comparator_choice_axis_why:{candidate_id}")
        conditions = axis_row.get("conditions")
        if not isinstance(conditions, list) or any(
            not isinstance(condition, str) or not condition
            for condition in conditions
        ):
            findings.append(
                f"invalid_comparator_choice_axis_conditions:{candidate_id}"
            )
        evidence_refs = axis_row.get("evidence_refs")
        if (
            not isinstance(evidence_refs, list)
            or not evidence_refs
            or any(not isinstance(ref, str) or not ref for ref in evidence_refs)
        ):
            findings.append(
                f"missing_comparator_choice_axis_evidence:{candidate_id}"
            )

        claim_support = axis_row.get("claim_support")
        if not isinstance(claim_support, dict):
            findings.append(
                f"missing_comparator_choice_axis_claim_support:{candidate_id}"
            )
            continue
        bounded_proposition = claim_support.get("bounded_proposition")
        if not isinstance(bounded_proposition, str) or not bounded_proposition:
            findings.append(
                f"missing_comparator_choice_axis_proposition:{candidate_id}"
            )
        support_posture = claim_support.get("support_posture")
        if not _is_enum_value(
            support_posture, _INTELLIGENCE_CLAIM_SUPPORT_POSTURES
        ):
            findings.append(
                f"invalid_comparator_choice_axis_support_posture:{candidate_id}"
            )
        independent_origin_count = claim_support.get("independent_origin_count")
        if (
            not isinstance(independent_origin_count, int)
            or isinstance(independent_origin_count, bool)
            or independent_origin_count < 1
        ):
            findings.append(
                f"invalid_comparator_choice_axis_origin_count:{candidate_id}"
            )
        source_roles = claim_support.get("source_roles")
        valid_source_roles = (
            isinstance(source_roles, list)
            and bool(source_roles)
            and all(
                _is_enum_value(role, _INTELLIGENCE_CLAIM_SOURCE_ROLES)
                for role in source_roles
            )
        )
        if not valid_source_roles:
            findings.append(
                f"invalid_comparator_choice_axis_source_roles:{candidate_id}"
            )

        ref_fields: dict[str, list[str]] = {}
        for field_name in (
            "engagement_evidence_refs",
            "behavior_evidence_refs",
            "counterevidence_refs",
        ):
            refs = claim_support.get(field_name)
            if not isinstance(refs, list) or any(
                not isinstance(ref, str) or not ref for ref in refs
            ):
                findings.append(
                    f"invalid_comparator_choice_axis_{field_name}:{candidate_id}"
                )
                ref_fields[field_name] = []
            else:
                ref_fields[field_name] = refs

        conflict_posture = claim_support.get("conflict_posture")
        if not _is_enum_value(
            conflict_posture, _INTELLIGENCE_CLAIM_CONFLICT_POSTURES
        ):
            findings.append(
                f"invalid_comparator_choice_axis_conflict_posture:{candidate_id}"
            )
        causal_ceiling = claim_support.get("causal_ceiling")
        if not isinstance(causal_ceiling, str) or not causal_ceiling:
            findings.append(
                f"missing_comparator_choice_axis_causal_ceiling:{candidate_id}"
            )

        choice_posture = axis_row.get("choice_posture")
        directional_choice = choice_posture in {
            "subject_advantage",
            "competitor_advantage",
        }
        if support_posture == "isolated" and directional_choice:
            findings.append(
                f"isolated_comparator_choice_axis_direction:{candidate_id}"
            )
        if (
            support_posture == "resonance_supported"
            and not ref_fields.get("engagement_evidence_refs")
        ):
            findings.append(
                f"resonant_comparator_choice_axis_without_engagement:{candidate_id}"
            )
        if support_posture in {
            "independently_repeated",
            "cross_venue_corroborated",
        } and (
            not isinstance(independent_origin_count, int)
            or isinstance(independent_origin_count, bool)
            or independent_origin_count < 2
        ):
            findings.append(
                f"repeated_comparator_choice_axis_without_two_origins:{candidate_id}"
            )
        if (
            support_posture == "cross_venue_corroborated"
            and (not valid_source_roles or len(set(source_roles)) < 2)
        ):
            findings.append(
                f"cross_venue_comparator_choice_axis_without_two_roles:{candidate_id}"
            )
        if conflict_posture in {"mixed", "contradicted"} and not ref_fields.get(
            "counterevidence_refs"
        ):
            findings.append(
                f"comparator_choice_axis_conflict_without_counterevidence:{candidate_id}"
            )
        if conflict_posture == "mixed" and choice_posture != "split_or_conditional":
            findings.append(
                f"mixed_comparator_choice_axis_not_split:{candidate_id}"
            )
        if (
            conflict_posture == "contradicted"
            and choice_posture != "parity_or_unresolved"
        ):
            findings.append(
                f"contradicted_comparator_choice_axis_still_directional:{candidate_id}"
            )
        if conflict_posture == "not_checked" and status == "observed":
            findings.append(
                f"observed_comparator_choice_axis_without_conflict_check:{candidate_id}"
            )

    if _is_enum_value(status, {"partial", "unresolved"}) and (
        not isinstance(explanation.get("gap_reason"), str)
        or not explanation.get("gap_reason")
    ):
        findings.append(f"comparator_choice_gap_without_reason:{candidate_id}")
    if promoted and status != "observed":
        findings.append(
            f"promoted_comparator_without_observed_choice:{candidate_id}"
        )
    if promoted and _is_enum_value(
        final_role, {"adjacent", "unresolved", "non_competitor"}
    ):
        findings.append(f"invalid_promoted_comparator_final_role:{candidate_id}")


def _validate_comparator_price_size_context(
    context: Any,
    *,
    candidate_id: str,
    findings: list[str],
) -> None:
    if not isinstance(context, dict):
        findings.append(f"missing_comparator_price_size_context:{candidate_id}")
        return
    status = context.get("status")
    if not _is_enum_value(status, _COMPARATOR_PRICE_SIZE_STATUSES):
        findings.append(f"invalid_comparator_price_size_status:{candidate_id}")
        return
    normalization = context.get("normalization_posture")
    if not _is_enum_value(
        normalization, _COMPARATOR_SIZE_NORMALIZATION_POSTURES
    ):
        findings.append(
            f"invalid_comparator_size_normalization_posture:{candidate_id}"
        )
    if status != "observed":
        if (
            not isinstance(context.get("gap_reason"), str)
            or not context.get("gap_reason")
        ):
            findings.append(f"comparator_price_size_gap_without_reason:{candidate_id}")
        return

    observations: dict[str, Mapping[str, Any]] = {}
    for side in ("subject", "competitor"):
        observation = context.get(side)
        if not isinstance(observation, dict):
            findings.append(
                f"missing_comparator_price_size_observation:{candidate_id}:{side}"
            )
            continue
        observations[side] = observation
        for field in (
            "product_identity",
            "currency",
            "size_unit",
            "market_scope",
            "observed_at",
        ):
            if (
                not isinstance(observation.get(field), str)
                or not observation.get(field)
            ):
                findings.append(
                    "missing_comparator_price_size_field:"
                    + f"{candidate_id}:{side}:{field}"
                )
        for field in ("price_amount", "size_value"):
            value = observation.get(field)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value <= 0
            ):
                findings.append(
                    "invalid_comparator_price_size_number:"
                    + f"{candidate_id}:{side}:{field}"
                )
        observed_at = observation.get("observed_at")
        if (
            isinstance(observed_at, str)
            and observed_at
            and _parse_iso_datetime(observed_at) is None
        ):
            findings.append(
                f"invalid_comparator_price_size_observed_at:{candidate_id}:{side}"
            )
        evidence_refs = observation.get("evidence_refs")
        if (
            not isinstance(evidence_refs, list)
            or not evidence_refs
            or any(not isinstance(ref, str) or not ref for ref in evidence_refs)
        ):
            findings.append(
                f"missing_comparator_price_size_evidence:{candidate_id}:{side}"
            )

    if normalization == "same_unit" and len(observations) == 2:
        if (
            observations["subject"].get("size_unit")
            != observations["competitor"].get("size_unit")
        ):
            findings.append(f"comparator_size_unit_mismatch:{candidate_id}")
    if (
        _is_enum_value(normalization, {"same_unit", "source_normalized"})
        and len(observations) == 2
        and observations["subject"].get("currency")
        != observations["competitor"].get("currency")
    ):
        # A posture that licenses direct comparison cannot span two
        # currencies: the sticker numbers would otherwise read as equal price.
        findings.append(f"comparator_price_currency_mismatch:{candidate_id}")
    if normalization == "source_normalized":
        normalization_refs = context.get("normalization_evidence_refs")
        if (
            not isinstance(normalization_refs, list)
            or not normalization_refs
            or any(
                not isinstance(ref, str) or not ref
                for ref in normalization_refs
            )
        ):
            findings.append(
                f"missing_comparator_size_normalization_evidence:{candidate_id}"
            )


def _validate_comparator_closure(
    closure: Any,
    *,
    repo_root: Path,
    valid_pass: bool,
    route_version: str,
    findings: list[str],
) -> None:
    if not isinstance(closure, dict):
        findings.append("missing_comparator_closure")
        return
    state = closure.get("state")
    if state not in _COMPARATOR_CLOSURE_STATES:
        findings.append("invalid_comparator_closure_state")
    elif valid_pass and state != "phase_a_competitor_context_closed":
        findings.append("passing_seal_without_comparator_context_closure")
    for key, code in (
        ("candidate_frame", "comparator_candidate_frame"),
        ("adjudicated_set", "comparator_adjudicated_set"),
    ):
        reference = closure.get(key)
        if not isinstance(reference, dict):
            findings.append(f"missing_{code}")
            continue
        _verify_artifact(
            reference.get("locator"),
            reference.get("sha256"),
            repo_root=repo_root,
            code=code,
            findings=findings,
        )
    raw_frame_ids = closure.get("frame_candidate_ids")
    frame_ids = _string_set(
        raw_frame_ids,
        code="invalid_comparator_frame_candidate_ids",
        findings=findings,
    )
    if (
        isinstance(raw_frame_ids, list)
        and all(isinstance(item, str) for item in raw_frame_ids)
        and len(raw_frame_ids) != len(frame_ids)
    ):
        findings.append("duplicate_comparator_frame_candidate_ids")
    candidates = closure.get("candidates")
    if not isinstance(candidates, list):
        findings.append("invalid_comparator_candidates")
        candidates = []
    seen: set[str] = set()
    for row in candidates:
        if not isinstance(row, dict):
            findings.append("invalid_comparator_candidate")
            continue
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            findings.append("missing_comparator_candidate_id")
            continue
        if candidate_id in seen:
            findings.append("duplicate_comparator_candidate_id")
            continue
        seen.add(candidate_id)
        if (
            candidate_id in frame_ids
            and route_version in _ROUTE_REVISION_1_2_OBLIGATION_VERSIONS
        ):
            _validate_comparator_prefanout_qualification(
                row,
                candidate_id=candidate_id,
                route_version=route_version,
                findings=findings,
            )
        material = row.get("material")
        if not isinstance(material, bool):
            findings.append(
                f"invalid_comparator_candidate_material_flag:{candidate_id}"
            )
            material = False
        disposition = row.get("disposition")
        if disposition not in _COMPARATOR_DISPOSITIONS:
            findings.append(f"invalid_comparator_disposition:{candidate_id}")
        decision_ready = row.get("decision_ready")
        if not isinstance(decision_ready, bool):
            findings.append(
                f"invalid_comparator_decision_ready_flag:{candidate_id}"
            )
            decision_ready = False
        if decision_ready and disposition != "promoted":
            findings.append(
                f"inconsistent_comparator_decision_ready:{candidate_id}"
            )
        if disposition == "promoted" or decision_ready:
            # The Phase 2 decision contract requires both exact product
            # identities before a candidate may be direct/decision-ready.
            for identity_key in (
                "subject_product_identity",
                "competitor_product_identity",
            ):
                value = row.get(identity_key)
                if not isinstance(value, str) or not value:
                    findings.append(
                        "comparator_promoted_without_exact_identity:"
                        + candidate_id
                    )
                    break
        ceiling = row.get("claim_ceiling")
        if not isinstance(ceiling, str) or not ceiling:
            findings.append(f"missing_comparator_claim_ceiling:{candidate_id}")
        if (disposition == "promoted" or decision_ready) and not material:
            # A promoted/decision-ready direct competitor cannot waive the
            # material-candidate evidence obligations by self-declaring
            # non-materiality.
            findings.append(
                f"promoted_comparator_not_material:{candidate_id}"
            )
        # The synthetic-conclusion ban is doctrine-wide: it applies to every
        # candidate row and every nested shape, not only material ones. The
        # observed_positions subtree is scanned separately with its
        # source-local rank exemption.
        forbidden_fields = sorted(
            _forbidden_synthetic_keys(
                {
                    key: nested
                    for key, nested in row.items()
                    if key != "observed_positions"
                }
            )
        )
        if forbidden_fields:
            findings.append(
                "forbidden_synthetic_comparator_field:"
                + f"{candidate_id}:{','.join(forbidden_fields)}"
            )
        if material:
            portfolio_role = row.get("portfolio_role")
            if not isinstance(portfolio_role, dict):
                findings.append(f"missing_comparator_portfolio_role:{candidate_id}")
            else:
                role_scope = portfolio_role.get("scope")
                role_status = portfolio_role.get("status")
                role_basis = portfolio_role.get("basis")
                assessed_identity = portfolio_role.get("assessed_identity")
                role_refs = portfolio_role.get("evidence_refs")
                valid_role_refs = (
                    isinstance(role_refs, list)
                    and bool(role_refs)
                    and all(isinstance(ref, str) and ref for ref in role_refs)
                )
                if role_scope not in _COMPARATOR_PORTFOLIO_ROLE_SCOPES:
                    findings.append(
                        f"invalid_comparator_portfolio_role_scope:{candidate_id}"
                    )
                if role_status not in _COMPARATOR_PORTFOLIO_ROLES:
                    findings.append(
                        f"invalid_comparator_portfolio_role_status:{candidate_id}"
                    )
                if role_basis not in _COMPARATOR_PORTFOLIO_ROLE_BASES:
                    findings.append(
                        f"invalid_comparator_portfolio_role_basis:{candidate_id}"
                    )
                if not isinstance(assessed_identity, str) or not assessed_identity:
                    findings.append(
                        f"missing_comparator_portfolio_role_identity:{candidate_id}"
                    )
                elif (
                    role_scope == "product"
                    and isinstance(row.get("competitor_product_identity"), str)
                    and assessed_identity != row.get("competitor_product_identity")
                ):
                    findings.append(
                        f"comparator_portfolio_product_identity_mismatch:{candidate_id}"
                    )
                if role_status == "explicit_hero" and (
                    role_basis != "explicit_source" or not valid_role_refs
                ):
                    findings.append(
                        f"comparator_explicit_hero_without_explicit_evidence:{candidate_id}"
                    )
                elif role_status == "likely_major" and (
                    role_basis != "multi_source_inference"
                    or not valid_role_refs
                    or len(set(role_refs)) < 2
                ):
                    findings.append(
                        f"comparator_likely_major_without_multisource_evidence:{candidate_id}"
                    )
                elif role_status == "supporting" and (
                    role_basis
                    not in {
                        "explicit_source",
                        "multi_source_inference",
                        "observed_position",
                    }
                    or not valid_role_refs
                ):
                    findings.append(
                        f"comparator_supporting_role_without_positive_evidence:{candidate_id}"
                    )
                elif role_status == "unclear" and (
                    role_basis != "unresolved"
                    or not isinstance(portfolio_role.get("gap_reason"), str)
                    or not portfolio_role.get("gap_reason")
                ):
                    findings.append(
                        f"comparator_unclear_role_without_gap_reason:{candidate_id}"
                    )

            positions = row.get("observed_positions")
            if not isinstance(positions, list):
                findings.append(f"invalid_comparator_observed_positions:{candidate_id}")
            else:
                if not positions and (
                    not isinstance(row.get("position_gap_reason"), str)
                    or not row.get("position_gap_reason")
                ):
                    findings.append(
                        f"comparator_position_gap_without_reason:{candidate_id}"
                    )
                position_ids: set[str] = set()
                for position in positions:
                    if not isinstance(position, dict):
                        findings.append(
                            f"invalid_comparator_observed_position:{candidate_id}"
                        )
                        continue
                    position_id = position.get("position_id")
                    if (
                        not isinstance(position_id, str)
                        or not position_id
                        or position_id in position_ids
                    ):
                        findings.append(
                            f"invalid_comparator_position_id:{candidate_id}"
                        )
                    else:
                        position_ids.add(position_id)
                    if position.get("scope_kind") not in _COMPARATOR_POSITION_SCOPES:
                        findings.append(
                            f"invalid_comparator_position_scope:{candidate_id}"
                        )
                    for field in (
                        "source_or_retailer",
                        "market_scope",
                        "observed_at",
                    ):
                        if (
                            not isinstance(position.get(field), str)
                            or not position.get(field)
                        ):
                            findings.append(
                                "missing_comparator_position_context:"
                                + f"{candidate_id}:{field}"
                            )
                    observed_at = position.get("observed_at")
                    if (
                        isinstance(observed_at, str)
                        and observed_at
                        and _parse_iso_datetime(observed_at) is None
                    ):
                        # A malformed observation time must not earn
                        # source-local position credit.
                        findings.append(
                            "invalid_comparator_position_observed_at:"
                            + candidate_id
                        )
                    position_refs = position.get("evidence_refs")
                    if (
                        not isinstance(position_refs, list)
                        or not position_refs
                        or any(
                            not isinstance(ref, str) or not ref
                            for ref in position_refs
                        )
                    ):
                        findings.append(
                            f"missing_comparator_position_evidence:{candidate_id}"
                        )
                    rank = position.get("rank")
                    list_size = position.get("list_size")
                    label = position.get("label")
                    has_numeric_position = rank is not None or list_size is not None
                    if has_numeric_position and (
                        not isinstance(rank, int)
                        or isinstance(rank, bool)
                        or not isinstance(list_size, int)
                        or isinstance(list_size, bool)
                        or rank < 1
                        or list_size < 1
                        or rank > list_size
                    ):
                        findings.append(
                            f"invalid_comparator_source_local_rank:{candidate_id}"
                        )
                    if not has_numeric_position and (
                        not isinstance(label, str) or not label
                    ):
                        findings.append(
                            f"comparator_position_without_rank_or_label:{candidate_id}"
                        )
                    forbidden_position_fields = sorted(
                        _forbidden_synthetic_keys(
                            position, exempt=frozenset({"rank"})
                        )
                    )
                    if forbidden_position_fields:
                        findings.append(
                            "forbidden_synthetic_comparator_position_field:"
                            + f"{candidate_id}:{','.join(forbidden_position_fields)}"
                        )

            shared_axis_ids = row.get("shared_axis_ids")
            if disposition == "promoted" or decision_ready:
                if (
                    not isinstance(shared_axis_ids, list)
                    or not shared_axis_ids
                    or any(
                        not isinstance(axis_id, str) or not axis_id
                        for axis_id in shared_axis_ids
                    )
                ):
                    findings.append(
                        f"promoted_comparator_without_shared_axes:{candidate_id}"
                    )
            elif shared_axis_ids is not None and (
                not isinstance(shared_axis_ids, list)
                or any(
                    not isinstance(axis_id, str) or not axis_id
                    for axis_id in shared_axis_ids
                )
            ):
                findings.append(f"invalid_comparator_shared_axes:{candidate_id}")
            if route_version in _ROUTE_REVISION_1_3_OBLIGATION_VERSIONS:
                _validate_comparator_choice_explanation(
                    row.get("competitive_choice_explanation"),
                    candidate_id=candidate_id,
                    shared_axis_ids=shared_axis_ids,
                    promoted=disposition == "promoted" or decision_ready,
                    findings=findings,
                )
            if (
                route_version in _ROUTE_REVISION_1_2_OBLIGATION_VERSIONS
                and isinstance(shared_axis_ids, list)
                and any(
                    isinstance(axis_id, str)
                    and any(
                        token in axis_id.lower()
                        for token in ("price", "value", "quantity", "cost")
                    )
                    for axis_id in shared_axis_ids
                )
            ):
                _validate_comparator_price_size_context(
                    row.get("price_size_context"),
                    candidate_id=candidate_id,
                    findings=findings,
                )

            lanes = row.get("lane_evidence")
            if not isinstance(lanes, dict):
                findings.append(
                    f"missing_comparator_lane_evidence:{candidate_id}"
                )
            else:
                if "co3_customer_comparison" in lanes:
                    findings.append(
                        f"combined_comparator_customer_lane_not_allowed:{candidate_id}"
                    )
                for lane in _COMPARATOR_LANE_KEYS:
                    lane_row = lanes.get(lane)
                    if (
                        not isinstance(lane_row, dict)
                        or lane_row.get("status") not in _COMPARATOR_LANE_STATES
                    ):
                        findings.append(
                            "invalid_comparator_lane_evidence:"
                            + f"{candidate_id}:{lane}"
                        )
                        continue
                    lane_status = lane_row.get("status")
                    lane_refs = lane_row.get("evidence_refs")
                    if lane_status == "observed" and (
                        not isinstance(lane_refs, list)
                        or not lane_refs
                        or any(
                            not isinstance(ref, str) or not ref
                            for ref in lane_refs
                        )
                    ):
                        findings.append(
                            "observed_comparator_lane_without_evidence:"
                            + f"{candidate_id}:{lane}"
                        )
                    elif lane_status in {"none_found", "blocked"} and (
                        not isinstance(lane_row.get("gap_reason"), str)
                        or not lane_row.get("gap_reason")
                    ):
                        findings.append(
                            "comparator_lane_gap_without_reason:"
                            + f"{candidate_id}:{lane}"
                        )
    dropped = sorted(frame_ids - seen)
    if dropped:
        findings.append(
            "comparator_candidate_silently_dropped:" + ",".join(dropped)
        )


def _validate_campaign_integration(
    block: Any,
    *,
    seal: Mapping[str, Any],
    repo_root: Path,
    valid_pass: bool,
    findings: list[str],
) -> None:
    if not isinstance(block, dict):
        findings.append("missing_campaign_evidence_integration")
        return
    status = block.get("status")
    if status not in {"completed", "blocked"}:
        findings.append("invalid_campaign_integration_status")
    elif valid_pass and status != "completed":
        findings.append("passing_seal_without_campaign_integration")
    requests = block.get("targeted_capture_requests")
    if not isinstance(requests, list):
        findings.append("invalid_campaign_capture_requests")
        requests = []
    request_ids: set[str] = set()
    for row in requests:
        if not isinstance(row, dict):
            findings.append("invalid_campaign_capture_request")
            continue
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            findings.append("missing_campaign_capture_request_id")
            continue
        if request_id in request_ids:
            findings.append("duplicate_campaign_capture_request_id")
            continue
        request_ids.add(request_id)
        target = row.get("target")
        if not isinstance(target, str) or not target:
            findings.append(f"missing_campaign_capture_request_target:{request_id}")
        if row.get("disposition") not in _CAMPAIGN_CAPTURE_REQUEST_STATES:
            findings.append(
                f"invalid_campaign_capture_request_disposition:{request_id}"
            )
    reference = block.get("view")
    if not isinstance(reference, dict):
        findings.append("missing_campaign_evidence_view")
        return
    locator = reference.get("locator")
    before = len(findings)
    _verify_artifact(
        locator,
        reference.get("sha256"),
        repo_root=repo_root,
        code="campaign_evidence_view",
        findings=findings,
    )
    if len(findings) != before:
        return
    view_path = Path(str(locator))
    if not view_path.is_absolute():
        view_path = repo_root / view_path
    try:
        view = json.loads(view_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"invalid_campaign_evidence_view:{type(exc).__name__}")
        return
    if not isinstance(view, dict):
        findings.append("invalid_campaign_evidence_view_shape")
        return
    _validate_campaign_view(view, seal=seal, findings=findings)


def _validate_campaign_view(
    view: Mapping[str, Any],
    *,
    seal: Mapping[str, Any],
    findings: list[str],
) -> None:
    if view.get("schema_version") != CAMPAIGN_EVIDENCE_VIEW_VERSION:
        findings.append("invalid_campaign_evidence_view_version")
    if view.get("subject") != seal.get("subject"):
        findings.append("campaign_view_subject_mismatch")
    if view.get("cycle_id") != seal.get("cycle_id"):
        findings.append("campaign_view_cycle_id_mismatch")
    units = view.get("units")
    if not isinstance(units, list):
        findings.append("invalid_campaign_view_units")
        units = []
    unit_ids: set[str] = set()
    credited_origins: set[str] = set()
    for row in units:
        if not isinstance(row, dict):
            findings.append("invalid_campaign_view_unit")
            continue
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id:
            findings.append("missing_campaign_unit_id")
            continue
        if unit_id in unit_ids:
            findings.append("duplicate_campaign_unit_id")
            continue
        unit_ids.add(unit_id)
        if row.get("source_role") not in _CAMPAIGN_SOURCE_ROLES:
            # Creator-authored and audience/customer evidence keep distinct
            # roles; a merged or unknown role is a defect, never a default.
            findings.append(f"invalid_campaign_unit_source_role:{unit_id}")
        for key, code in (
            ("publisher_identity", "publisher_identity"),
            ("brand_binding", "brand_binding"),
            ("source_surface", "source_surface"),
            ("captured_at", "captured_at"),
            ("independent_origin_key", "origin_key"),
            ("claim_ceiling", "claim_ceiling"),
        ):
            value = row.get(key)
            if not isinstance(value, str) or not value:
                findings.append(f"missing_campaign_unit_{code}:{unit_id}")
        for key in ("published_at", "observed_at"):
            value = row.get(key)
            if value is None:
                # Unknown source timestamps stay null, never invented.
                continue
            if (
                not isinstance(value, str)
                or not value
                or _parse_iso_datetime(value) is None
            ):
                findings.append(f"invalid_campaign_unit_{key}:{unit_id}")
        captured_at = row.get("captured_at")
        if (
            isinstance(captured_at, str)
            and captured_at
            and _parse_iso_datetime(captured_at) is None
        ):
            findings.append(f"invalid_campaign_unit_captured_at:{unit_id}")
        for key in ("product_bindings", "claim_bindings"):
            bindings = row.get(key)
            if not isinstance(bindings, list) or any(
                not isinstance(item, str) or not item for item in bindings
            ):
                findings.append(f"invalid_campaign_unit_{key}:{unit_id}")
        refs = row.get("source_refs")
        if not isinstance(refs, list) or not refs or any(
            not isinstance(item, str) or not item for item in refs
        ):
            findings.append(f"missing_campaign_unit_source_refs:{unit_id}")
        relationship = row.get("relationship_posture")
        if relationship not in _CAMPAIGN_RELATIONSHIP_POSTURES:
            findings.append(
                f"invalid_campaign_unit_relationship_posture:{unit_id}"
            )
        if row.get("linkage_posture") not in _CAMPAIGN_LINKAGE_POSTURES:
            findings.append(f"invalid_campaign_unit_linkage_posture:{unit_id}")
        credit = row.get("independent_origin_credit")
        if not isinstance(credit, bool):
            findings.append(f"invalid_campaign_unit_origin_credit:{unit_id}")
            continue
        if credit:
            if relationship != "apparently_independent":
                findings.append(
                    f"campaign_credit_without_independent_relationship:{unit_id}"
                )
            origin_key = row.get("independent_origin_key")
            if isinstance(origin_key, str) and origin_key:
                if origin_key in credited_origins:
                    findings.append(
                        f"duplicate_independent_origin_credit:{origin_key}"
                    )
                credited_origins.add(origin_key)
    linkage_by_unit = {
        str(row.get("unit_id")): row.get("linkage_posture")
        for row in units
        if isinstance(row, dict)
    }
    clusters = view.get("clusters", [])
    if not isinstance(clusters, list):
        findings.append("invalid_campaign_clusters")
        clusters = []
    cluster_ids: set[str] = set()
    for cluster in clusters:
        if not isinstance(cluster, dict):
            findings.append("invalid_campaign_cluster")
            continue
        cluster_id = cluster.get("cluster_id")
        if not isinstance(cluster_id, str) or not cluster_id:
            findings.append("missing_campaign_cluster_id")
            continue
        if cluster_id in cluster_ids:
            findings.append("duplicate_campaign_cluster_id")
            continue
        cluster_ids.add(cluster_id)
        members = cluster.get("member_unit_ids")
        if not isinstance(members, list) or not members or any(
            not isinstance(item, str) or not item for item in members
        ):
            findings.append(f"invalid_campaign_cluster_members:{cluster_id}")
            members = []
        elif len(members) != len(set(members)):
            findings.append(f"duplicate_campaign_cluster_member:{cluster_id}")
        unresolved = [item for item in members if item not in unit_ids]
        if unresolved:
            findings.append(f"unresolved_campaign_cluster_member:{cluster_id}")
        basis = cluster.get("basis")
        if basis not in _CAMPAIGN_CLUSTER_BASES:
            findings.append(f"invalid_campaign_cluster_basis:{cluster_id}")
        elif basis == "direct":
            if any(
                linkage_by_unit.get(item) != "direct"
                for item in members
                if item in unit_ids
            ):
                findings.append(
                    f"campaign_cluster_overstated_linkage:{cluster_id}"
                )
        elif basis == "inferred":
            for key in ("provenance", "reversal_condition"):
                value = cluster.get(key)
                if not isinstance(value, str) or not value:
                    findings.append(
                        "campaign_cluster_inference_without_provenance:"
                        + cluster_id
                    )
                    break


def _validate_verification_requests(
    requests: Any,
    *,
    repo_root: Path,
    valid_pass: bool,
    findings: list[str],
) -> None:
    if not isinstance(requests, list):
        findings.append("missing_verification_requests")
        return
    request_ids: set[str] = set()
    for row in requests:
        if not isinstance(row, dict):
            findings.append("invalid_verification_request")
            continue
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            findings.append("missing_verification_request_id")
            continue
        if request_id in request_ids:
            findings.append("duplicate_verification_request_id")
            continue
        request_ids.add(request_id)
        product = row.get("product_identity")
        claim = row.get("claim")
        trigger_kind = row.get("trigger_kind")
        trigger_refs = row.get("trigger_evidence_refs")
        has_trigger = (
            isinstance(product, str)
            and product
            and trigger_kind in _VERIFICATION_TRIGGER_KINDS
            and isinstance(trigger_refs, list)
            and trigger_refs
            and all(
                isinstance(item, str) and item for item in trigger_refs
            )
            and isinstance(claim, str)
            and claim
        )
        if not has_trigger:
            # Verification is conditional: reconciled product identity ×
            # material axis/contradiction × verifiable claim, never
            # catalog-wide.
            findings.append(
                f"verification_request_without_material_trigger:{request_id}"
            )
        status = row.get("status")
        if status not in _VERIFICATION_STATUSES:
            findings.append(f"invalid_verification_status:{request_id}")
            continue
        if valid_pass and status == "not_run":
            findings.append(
                f"passing_seal_with_unrun_verification_request:{request_id}"
            )
        if status == "completed":
            reference = row.get("return")
            if not isinstance(reference, dict):
                findings.append(f"missing_verification_return:{request_id}")
                continue
            _verify_artifact(
                reference.get("locator"),
                reference.get("sha256"),
                repo_root=repo_root,
                code="verification_return",
                findings=findings,
            )


def _validate_retailer_state_accounting(
    block: Any, *, findings: list[str]
) -> None:
    if not isinstance(block, dict):
        findings.append("missing_retailer_state_accounting")
        return
    claims = block.get("claims")
    if not isinstance(claims, list):
        findings.append("invalid_retailer_state_claims")
        return
    claim_ids: set[str] = set()
    for row in claims:
        if not isinstance(row, dict):
            findings.append("invalid_retailer_state_claim")
            continue
        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            findings.append("missing_retailer_state_claim_id")
            continue
        if claim_id in claim_ids:
            findings.append("duplicate_retailer_state_claim_id")
            continue
        claim_ids.add(claim_id)
        kind = row.get("kind")
        if kind not in _RETAILER_STATE_KINDS:
            findings.append(f"invalid_retailer_state_kind:{claim_id}")
            continue
        for key in ("retailer", "product_identity", "market_scope"):
            value = row.get(key)
            if not isinstance(value, str) or not value:
                findings.append(
                    f"missing_retailer_state_identity:{claim_id}:{key}"
                )
        current_ref = row.get("current_observation_ref")
        if not isinstance(current_ref, str) or not current_ref:
            findings.append(
                f"missing_retailer_state_observation_ref:{claim_id}"
            )
            current_ref = ""
        prior_ref = row.get("prior_observation_ref")
        if kind == "retailer_state_change":
            # A movement event requires two comparable observations; one
            # snapshot is a state, never a change.
            if (
                not isinstance(prior_ref, str)
                or not prior_ref
                or prior_ref == current_ref
            ):
                findings.append(
                    f"retailer_state_change_without_two_observations:{claim_id}"
                )
            change_summary = row.get("change_summary")
            if not isinstance(change_summary, str) or not change_summary:
                findings.append(
                    f"retailer_state_change_without_summary:{claim_id}"
                )
        else:
            if prior_ref not in (None, "") or row.get("change_summary") not in (
                None,
                "",
            ):
                findings.append(
                    f"movement_claim_from_single_snapshot:{claim_id}"
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
    if path.is_absolute():
        # Repository-tracked evidence must stay checkout-portable; absolute
        # locators are for machine-local raw-lake roots outside the repo only.
        if path.resolve().is_relative_to(Path(repo_root).resolve()):
            findings.append(f"nonportable_{code}_locator")
    else:
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
    parser.add_argument(
        "--allow-legacy-consumer-v1",
        action="store_true",
        help=(
            "Audit a historical broad_consumer_brand_understanding_v1 ledger. "
            "It does not satisfy the current consumer-brand Phase A contract."
        ),
    )
    parser.add_argument(
        "--allow-legacy-consumer-v2",
        action="store_true",
        help=(
            "Audit a historical broad_consumer_brand_understanding_v2 ledger. "
            "It does not satisfy the current decision-maturity Phase A contract."
        ),
    )
    parser.add_argument(
        "--allow-preversion-route",
        action="store_true",
        help=(
            "Audit a seal sealed before Understanding route versioning began "
            "(2026-08-07) - such seals carry no stamped route version - or a "
            "seal stamped with a known older route version. This switch "
            "never satisfies the current route contract."
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
            allow_legacy_consumer_v1=args.allow_legacy_consumer_v1,
            allow_legacy_consumer_v2=args.allow_legacy_consumer_v2,
            allow_preversion_route=args.allow_preversion_route,
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
