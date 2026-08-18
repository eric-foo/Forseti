"""Hash-bound Phase A evidence selection and exact-quote finalization.

This is a consumer of ``phase_a_evidence_packet_v3``.  It does not create a
new evidence authority: packet facts remain source-owned, external models only
label admitted candidates and extract quotes, and deterministic code owns
identity, selection, lineage, and exactness checks.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from harness_utils import hash_file, sha256_text
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
    _expand_packet,
    _relation_rows,
    _verify_packet,
)


SELECTION_SPEC_VERSION = "phase_a_evidence_selection_spec_v1"
SELECTION_MANIFEST_VERSION = "phase_a_evidence_selection_manifest_v1"
LEGACY_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v1"
QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v3"
RELATIONS = ("support", "counter", "adjacent", "exclude")
TRUTH_ROLES = {"community_post", "retailer_review", "audience_comment"}
INFLUENCE_ROLES = {"creator_authored"}
MAX_TRUTH_GROUPS = 10
MAX_INFLUENCE_GROUPS = 3
MAX_QUOTE_CHARACTERS = 220
PROTECTED_LANES = ("safety", "costly_behavior")
# One venue per publisher, matched on the registered domain and any subdomain of
# it, so host variants (old./np./new./sh.reddit.com, vm./vt./m.tiktok.com,
# community.sephora.com, smile.amazon.com) cannot split one venue into several
# display sections and several engagement-ordering buckets.
VENUE_HOST_SUFFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("reddit", ("reddit.com", "redd.it")),
    ("tiktok", ("tiktok.com",)),
    ("sephora", ("sephora.com",)),
    ("amazon", ("amazon.com", "amazon.co.uk")),
    ("revolve", ("revolve.com",)),
)
# A whole numeric token only: a partial parse of "1.2k" or "1,234" would order
# rows by a value the source never stated.
ENGAGEMENT_NUMBER_RE = re.compile(r"^\s*(-?[0-9]+(?:\.[0-9]+)?)(?![0-9A-Za-z.,])")
INTERNAL_RELATION_LABEL_RE = re.compile(r"\b(?:support|counter|adjacent|exclude)\b", re.IGNORECASE)
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
DISPLAY_LABEL_BY_REASON_CODE = {
    "repurchase_despite_price": "Repurchase intent despite price",
    "explicitly_worth_price": "Explicitly worth the price",
    "pricey_but_worth_it": "Explicitly worth the price",
    "favorable_price_content_ratio": "Strong price-to-quantity value",
    "reasonably_priced_two_pack": "Reasonably priced two-pack",
    "too_expensive_for_amount": "Too little product for the price",
    "explicitly_not_worth_price": "Not worth the price",
    "disappointing_fill_amount": "Too little product for the tube size",
    "container_barely_filled": "Too little product for the tube size",
    "performance_not_worth_price": "Performance does not justify the price",
    "longevity_justifies_price": "Longevity justifies the price",
    "purchase_despite_price": "Purchase commitment despite price",
    "multiple_purchases_despite_price": "Repeated purchasing despite price",
    "repurchase_intent": "Repurchase intent",
    "multiple_purchases": "Repeated purchasing",
    "purchase_commitment": "Purchase commitment",
    "explicit_good_value": "Explicitly good value",
    "benefits_justify_price": "Benefits justify the price",
    "favorable_price_quantity_comparison": "Favorable price-to-quantity value",
    "better_value_than_comparator": "Better value than the comparison",
    "reasonable_bundle_price": "Reasonably priced bundle",
    "product_goes_a_long_way": "A little product goes a long way",
    "purchase_regret_due_cost": "Purchase regret due to cost",
    "explicit_poor_value": "Explicitly poor value",
    "too_little_product_for_price": "Too little product for the price",
    "packaging_waste_undermines_value": "Packaging waste undermines value",
    "price_increase_quality_decline": "Higher price with lower quality",
    "cheaper_equivalent_available": "Cheaper equivalent available",
    "comparator_better_value": "Comparison offers better value",
    # Adjacent value meanings are not value evidence, but they may still be
    # displayed as influence context or operator-protected rows.
    "price_or_quantity_fact_only": "Price or quantity detail only",
    "purchase_without_value_judgment": "Purchase without a value judgment",
    "non_value_product_experience": "Product experience outside value",
    "unclear_value_implication": "Unclear value implication",
}

VALUE_AXIS_ID = "value_and_quantity"
VALUE_REASON_RELATIONS = {
    "repurchase_despite_price": "support",
    "multiple_purchases_despite_price": "support",
    "purchase_despite_price": "support",
    "repurchase_intent": "support",
    "multiple_purchases": "support",
    "purchase_commitment": "support",
    "explicit_good_value": "support",
    "benefits_justify_price": "support",
    "favorable_price_quantity_comparison": "support",
    "better_value_than_comparator": "support",
    "reasonable_bundle_price": "support",
    "product_goes_a_long_way": "support",
    "purchase_regret_due_cost": "counter",
    "explicit_poor_value": "counter",
    "too_little_product_for_price": "counter",
    "performance_not_worth_price": "counter",
    "packaging_waste_undermines_value": "counter",
    "price_increase_quality_decline": "counter",
    "cheaper_equivalent_available": "counter",
    "comparator_better_value": "counter",
    "price_or_quantity_fact_only": "adjacent",
    "purchase_without_value_judgment": "adjacent",
    "non_value_product_experience": "adjacent",
    "unclear_value_implication": "adjacent",
    "wrong_product_or_scope": "exclude",
    "duplicate_or_non_evidence": "exclude",
}
VALUE_SUPPORT_PRIORITY = {
    "repurchase_despite_price": 0,
    "multiple_purchases_despite_price": 0,
    "purchase_despite_price": 0,
    "repurchase_intent": 0,
    "multiple_purchases": 0,
    "purchase_commitment": 0,
    "explicit_good_value": 3,
    "benefits_justify_price": 3,
    "favorable_price_quantity_comparison": 4,
    "better_value_than_comparator": 4,
    "reasonable_bundle_price": 4,
    "product_goes_a_long_way": 4,
}
VALUE_COUNTER_PRIORITY = {
    "purchase_regret_due_cost": 0,
    "explicit_poor_value": 0,
    "performance_not_worth_price": 1,
    "price_increase_quality_decline": 1,
    "too_little_product_for_price": 2,
    "packaging_waste_undermines_value": 2,
    "cheaper_equivalent_available": 3,
    "comparator_better_value": 3,
}

RELATION_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded claim and ordered, source-owned candidate rows below. Return only the required JSON.

Return every candidate_id exactly once and in the supplied order. Label its relation to the bounded claim as support, counter, adjacent, or exclude and supply one short lowercase snake_case reason_code that names the evidence meaning without repeating those internal relation words. Relation is about meaning, never engagement size. Read same_evidence_companion_meanings as context that can qualify or reverse the candidate's implication, not as separately admitted candidates. Do not isolate price discomfort from same-source purchase or repurchase behavior: for a value claim, willingness to buy despite the price is countervailing behavior rather than evidence of poor value. Preserve product, variant, timing, comparison, uncertainty, and source-role boundaries. A creator-authored item is influence context and cannot corroborate customer experience. Do not estimate prevalence, causation, commercial pull, or a number of similar customers.

{policy_guidance}

SELECTION_ENVELOPE_JSON:
{envelope}
"""

VALUE_RELATION_GUIDANCE = """VALUE-BOX POLICY: Use a support or counter label only when the candidate's normalized meaning directly concerns price, value, quantity-for-price, purchase commitment, repurchase, or whether benefits justify cost, either alone or together with its same-evidence companion meanings. Same-evidence meanings may jointly support one code when one supplies an explicit price/value premise and another supplies purchase, repurchase, repeated ownership, or stated benefits; the code must describe that combined visible meaning, never a conclusion absent from the whole same-evidence set. An explicit same-evidence statement of regret, waste, or poor value reverses a positive purchase inference unless an explicit later repurchase, purchase commitment, or worth statement countervails it. Companion meanings must not turn a formula, hydration, scent, trial-only, gift-card, or generic purchase statement into value evidence; those are adjacent unless the same-evidence set states the cost/value tradeoff. Use `repurchase_intent`, `multiple_purchases`, or `purchase_commitment` when the behavior is visible but price resistance is not; the corresponding `*_despite_price` code requires explicit source meaning about price or cost. Use `product_goes_a_long_way` for quantity efficiency without an explicit price judgment; `benefits_justify_price` requires an explicit worth/price tradeoff. `better_value_than_comparator` means the subject product is better value; `comparator_better_value` means the other product is better value. Use exactly one relation-aligned code from this list: {reason_codes}."""

QUOTE_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the ordered selected rows and source bodies below. Return only the required JSON.

Return every selected_id exactly once and in order. If an available source body is 220 characters or fewer, return the entire body as the exact quote; never clip a short comment before a material qualification or countervailing behavior. For a longer body, choose one contiguous exact substring of at most 220 characters that directly expresses both the supplied normalized meaning and display_label, and includes any nearby clause that materially qualifies or reverses it; if that cannot fit, return quote_status=quote_unavailable and exact_quote=null. Use same_evidence_companion_meanings to detect context that cannot be clipped away. Preserve spelling and punctuation. Do not rewrite, repair, add ellipses, or combine non-contiguous spans. Exact text that does not express the normalized meaning and display label is not an acceptable quote.

SELECTED_EVIDENCE_ENVELOPE_JSON:
{envelope}
"""


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _uses_value_policy(spec: Mapping[str, Any]) -> bool:
    axis_ids = spec.get("axis_ids")
    return isinstance(axis_ids, list) and set(axis_ids) == {VALUE_AXIS_ID}


def _policy_guidance(spec: Mapping[str, Any]) -> str:
    if not _uses_value_policy(spec):
        return ""
    grouped = "; ".join(
        f"{relation}=[{', '.join(sorted(code for code, lane in VALUE_REASON_RELATIONS.items() if lane == relation))}]"
        for relation in RELATIONS
    )
    return VALUE_RELATION_GUIDANCE.format(reason_codes=grouped)


def _candidate_id(packet_sha256: str, evidence_id: str, semantic_ref: str) -> str:
    return "candidate_" + sha256_text(
        f"{packet_sha256}\n{evidence_id}\n{semantic_ref}"
    )[:24]


def _layer_for_role(source_role: str) -> str:
    if source_role in TRUTH_ROLES:
        return "truth_support"
    if source_role in INFLUENCE_ROLES:
        return "influence_context"
    raise EvidenceConsumerError(
        "unsupported_source_role", f"source role has no evidence layer: {source_role}"
    )


def _numeric_engagement(value: Any, engagement_kind: str | None = None) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = ENGAGEMENT_NUMBER_RE.match(value)
        return float(match.group(1)) if match else None
    if isinstance(value, Mapping):
        if engagement_kind != "sephora_helpful_votes":
            raise EvidenceConsumerError(
                "unsupported_engagement_shape",
                f"mapping engagement is not defined for {engagement_kind}",
            )
        if set(value) != {"negative", "positive", "total"} or not all(
            isinstance(value[key], (int, float)) and not isinstance(value[key], bool)
            for key in value
        ):
            raise EvidenceConsumerError(
                "unsupported_engagement_shape", "Sephora helpful-vote shape is invalid"
            )
        if value["negative"] < 0 or value["positive"] < 0 or value["total"] != value["negative"] + value["positive"]:
            raise EvidenceConsumerError(
                "unsupported_engagement_shape", "Sephora helpful-vote totals are inconsistent"
            )
        return float(value["positive"])
    return None


def _verify_bundle(bundle: Mapping[str, Any]) -> None:
    """Reject a bundle whose body content no longer matches its stored hash.

    The packet/bundle field comparison only proves the two artifacts agree on a
    declared string; it cannot see an edited evidence body.  Quotes are read
    from these bodies, so the bundle is content-verified where it first enters
    the trust boundary.  Later stages inherit that proof through the selection
    manifest's ``bundle_file_sha256`` pin.
    """
    core = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if bundle.get("bundle_sha256") != _canonical_json_sha256(core):
        raise EvidenceConsumerError(
            "bundle_verification", "bundle content does not match its stored bundle_sha256"
        )


def _string_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {part for part in value.split() if part}
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        return set(value)
    if value is None:
        return set()
    raise EvidenceConsumerError("rehydration_source_validation", "expected string or string list")


def _normalized_venue(host: str) -> str | None:
    for venue, suffixes in VENUE_HOST_SUFFIXES:
        if any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes):
            return venue
    return None


def _source_venue(source_role: str, source_ref: Any, evidence_id: str) -> tuple[str, str]:
    if isinstance(source_ref, str):
        host = (urlparse(source_ref).hostname or "").lower().removeprefix("www.")
        if host:
            venue = _normalized_venue(host)
            if venue is not None:
                return venue, "normalized_source_ref_hostname"
            return host, "source_ref_hostname"
    lowered_id = evidence_id.lower()
    if "tiktok" in lowered_id:
        return "tiktok", "evidence_id_source_token"
    if source_role == "retailer_review":
        for venue in ("sephora", "amazon", "revolve"):
            if venue in lowered_id:
                return venue, "evidence_id_source_token"
    prefix = evidence_id.split(":", 1)[0]
    if source_role == "retailer_review" and prefix:
        return prefix.removesuffix("-review"), "evidence_id_prefix"
    return source_role, "source_role"


def _candidate_rows(
    sources: Sequence[Mapping[str, Any]], spec: Mapping[str, Any]
) -> list[dict[str, Any]]:
    axis_ids = spec.get("axis_ids")
    subject_ids = spec.get("subject_product_ids")
    if not isinstance(axis_ids, list) or not all(isinstance(v, str) for v in axis_ids):
        raise EvidenceConsumerError("selection_spec", "axis_ids must be a string list")
    if not isinstance(subject_ids, list) or not subject_ids or not all(isinstance(v, str) for v in subject_ids):
        raise EvidenceConsumerError(
            "selection_spec", "subject_product_ids must be a nonempty string list"
        )
    wanted_axes = set(axis_ids)
    wanted_subjects = set(subject_ids)

    def _nominated_pairs(key: str, field: str) -> set[tuple[str, str]]:
        pairs: set[tuple[str, str]] = set()
        for row in spec.get(key) or []:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("source_id"), str)
                or not isinstance(row.get(field), str)
            ):
                raise EvidenceConsumerError(
                    "selection_spec", f"{key} rows need a string source_id and {field}"
                )
            pairs.add((row["source_id"], row[field]))
        return pairs

    explicit_semantic_refs = _nominated_pairs("admit_semantic_refs", "semantic_unit_ref")
    if not wanted_axes and not explicit_semantic_refs:
        raise EvidenceConsumerError(
            "selection_spec", "axis_ids or admit_semantic_refs must admit candidates"
        )
    explicit_unresolved = _nominated_pairs("admit_unresolved", "evidence_id")
    protected_spec = spec.get("protected_evidence_ids") or {}
    unsupported_lanes = sorted(set(protected_spec) - set(PROTECTED_LANES))
    if unsupported_lanes:
        raise EvidenceConsumerError(
            "selection_spec", f"unsupported protected lane keys: {unsupported_lanes}"
        )
    protected: dict[str, set[str]] = {}
    for key, values in protected_spec.items():
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise EvidenceConsumerError(
                "selection_spec", f"protected lane {key} must be a string list"
            )
        protected[key] = set(values)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    admitted_unresolved: set[tuple[str, str]] = set()
    for source in sources:
        source_id = source["source_id"]
        packet = source["packet"]
        evidence_index, _ = _expand_packet(packet)
        linked_relations: dict[tuple[str, str], set[str]] = defaultdict(set)
        for proposition in packet.get("propositions", []):
            proposition_id = proposition.get("proposition_id")
            for row in _relation_rows(packet, proposition_id):
                linked_relations[(row["evidence_id"], row["semantic_unit_ref"])].add(
                    row["relation"]
                )
        unmerged_refs = {
            row.get("semantic_unit_ref")
            for key in ("unmerged_axis_candidates", "unscoped_unmerged_candidates")
            for row in packet.get(key, [])
            if isinstance(row, dict)
        }
        for evidence_id, (group, evidence) in evidence_index.items():
            layer = _layer_for_role(group["source_role"])
            for semantic in evidence["semantic_units"]:
                axes = _string_values(semantic.get("axis_ids"))
                subjects = _string_values(semantic.get("subject_product_ids"))
                semantic_ref = semantic["semantic_unit_ref"]
                axis_admitted = bool(axes & wanted_axes and subjects & wanted_subjects)
                explicitly_admitted = (source_id, semantic_ref) in explicit_semantic_refs
                if not (axis_admitted or explicitly_admitted):
                    continue
                if explicitly_admitted and subjects and not (subjects & wanted_subjects):
                    raise EvidenceConsumerError(
                        "wrong_product_candidate", f"explicit semantic ref has another subject: {semantic_ref}"
                    )
                cid = _candidate_id(packet["packet_sha256"], evidence_id, semantic_ref)
                if cid in seen:
                    raise EvidenceConsumerError("duplicate_candidate_id", cid)
                seen.add(cid)
                engagement = evidence["engagement"]
                status = engagement.get("status") or "engagement_available"
                # Mapping-valued engagement has source-specific meaning.  Validate
                # every admitted row before selection so an unselected or reserved
                # row cannot silently bypass the source-native shape boundary.
                if isinstance(engagement.get("raw_value"), Mapping):
                    _numeric_engagement(engagement["raw_value"], group["engagement_kind"])
                source_venue, source_venue_basis = _source_venue(
                    group["source_role"], evidence.get("source_ref"), evidence_id
                )
                candidate = {
                    "candidate_id": cid,
                    "source_id": source_id,
                    "packet_sha256": packet["packet_sha256"],
                    "evidence_id": evidence_id,
                    "semantic_unit_ref": semantic_ref,
                    "normalized_meaning": semantic.get("statement"),
                    "subject_product_ids": sorted(subjects),
                    "product_version_ids": semantic.get("product_version_ids", []),
                    "axis_ids": sorted(axes),
                    "conditions": semantic.get("conditions", []),
                    "uncertainty_posture": semantic.get("uncertainty_posture"),
                    "polarity": semantic.get("polarity"),
                    "same_evidence_companion_meanings": [
                        {
                            "semantic_unit_ref": companion.get("semantic_unit_ref"),
                            "statement": companion.get("statement"),
                            "polarity": companion.get("polarity"),
                            "axis_ids": sorted(_string_values(companion.get("axis_ids"))),
                            "conditions": companion.get("conditions", []),
                        }
                        for companion in evidence["semantic_units"]
                        if companion.get("semantic_unit_ref") != semantic_ref
                    ],
                    "source_family": group["source_family"],
                    "source_role": group["source_role"],
                    "layer": layer,
                    "source_artifact_id": evidence.get("source_artifact_id"),
                    "source_ref": evidence.get("source_ref"),
                    "publication_time": evidence.get("publication_time"),
                    "independence_key": evidence.get("independence_key") or evidence_id,
                    "scoped_independence_key": "::".join(
                        (
                            source_id,
                            str(packet.get("source_bindings", {}).get("corpus_sha256")),
                            str(evidence.get("independence_key") or evidence_id),
                        )
                    ),
                    "independence_posture": evidence.get("independence_posture"),
                    "container_id": evidence.get("container_id"),
                    "source_venue": source_venue,
                    "source_venue_basis": source_venue_basis,
                    "engagement_kind": group["engagement_kind"],
                    "engagement_context": group["engagement_context"],
                    "engagement_status": status,
                    "engagement_raw_value": engagement.get("raw_value") if status != "engagement_unavailable" else None,
                    "engagement_observed_at": engagement.get("observed_at") if status != "engagement_unavailable" else None,
                    "engagement_material_positive": engagement.get("material_positive") if status != "engagement_unavailable" else None,
                    "existing_relations": sorted(linked_relations[(evidence_id, semantic_ref)]),
                    "retained_unmerged": semantic_ref in unmerged_refs,
                    "protected_lanes": sorted(
                        lane for lane, ids in protected.items() if evidence_id in ids
                    ),
                }
                candidates.append(candidate)
        unresolved_by_id = {
            row.get("evidence_id"): row.get("disposition")
            for row in packet.get("unresolved_axis_candidates", [])
            if isinstance(row, dict)
        }
        for unresolved_source_id, evidence_id in sorted(explicit_unresolved):
            if unresolved_source_id != source_id:
                continue
            if evidence_id not in unresolved_by_id or evidence_id not in evidence_index:
                raise EvidenceConsumerError(
                    "failed_rehydration_lookup", f"unresolved evidence not found: {evidence_id}"
                )
            group, evidence = evidence_index[evidence_id]
            layer = _layer_for_role(group["source_role"])
            disposition = unresolved_by_id[evidence_id]
            semantic_ref = f"unresolved::{evidence_id}"
            cid = _candidate_id(packet["packet_sha256"], evidence_id, semantic_ref)
            admitted_unresolved.add((source_id, evidence_id))
            if cid in seen:
                continue
            seen.add(cid)
            engagement = evidence["engagement"]
            status = engagement.get("status") or "engagement_available"
            if isinstance(engagement.get("raw_value"), Mapping):
                _numeric_engagement(engagement["raw_value"], group["engagement_kind"])
            meaning = disposition.get("disposition_reason") if isinstance(disposition, dict) else str(disposition)
            source_venue, source_venue_basis = _source_venue(
                group["source_role"], evidence.get("source_ref"), evidence_id
            )
            candidates.append(
                {
                    "candidate_id": cid,
                    "source_id": source_id,
                    "packet_sha256": packet["packet_sha256"],
                    "evidence_id": evidence_id,
                    "semantic_unit_ref": semantic_ref,
                    "normalized_meaning": meaning,
                    "subject_product_ids": [],
                    "product_version_ids": [],
                    "axis_ids": [],
                    "conditions": [],
                    "uncertainty_posture": "unresolved",
                    "polarity": "unresolved",
                    "same_evidence_companion_meanings": [],
                    "source_family": group["source_family"],
                    "source_role": group["source_role"],
                    "layer": layer,
                    "source_artifact_id": evidence.get("source_artifact_id"),
                    "source_ref": evidence.get("source_ref"),
                    "publication_time": evidence.get("publication_time"),
                    "independence_key": evidence.get("independence_key") or evidence_id,
                    "scoped_independence_key": "::".join(
                        (
                            source_id,
                            str(packet.get("source_bindings", {}).get("corpus_sha256")),
                            str(evidence.get("independence_key") or evidence_id),
                        )
                    ),
                    "independence_posture": evidence.get("independence_posture"),
                    "container_id": evidence.get("container_id"),
                    "source_venue": source_venue,
                    "source_venue_basis": source_venue_basis,
                    "engagement_kind": group["engagement_kind"],
                    "engagement_context": group["engagement_context"],
                    "engagement_status": status,
                    "engagement_raw_value": engagement.get("raw_value") if status != "engagement_unavailable" else None,
                    "engagement_observed_at": engagement.get("observed_at") if status != "engagement_unavailable" else None,
                    "engagement_material_positive": engagement.get("material_positive") if status != "engagement_unavailable" else None,
                    "existing_relations": [],
                    "retained_unmerged": False,
                    "protected_lanes": sorted(
                        lane for lane, ids in protected.items() if evidence_id in ids
                    ),
                }
            )
    candidates.sort(key=lambda row: row["candidate_id"])
    admitted_refs = {(row["source_id"], row["semantic_unit_ref"]) for row in candidates}
    missing_explicit = explicit_semantic_refs - admitted_refs
    if missing_explicit:
        raise EvidenceConsumerError(
            "failed_rehydration_lookup", f"explicit semantic refs not found: {sorted(missing_explicit)}"
        )
    missing_unresolved = explicit_unresolved - admitted_unresolved
    if missing_unresolved:
        raise EvidenceConsumerError(
            "failed_rehydration_lookup",
            f"nominated unresolved refs not found: {sorted(missing_unresolved)}",
        )
    admitted_evidence_ids = {row["evidence_id"] for row in candidates}
    missing_protected = sorted(
        evidence_id
        for ids in protected.values()
        for evidence_id in ids
        if evidence_id not in admitted_evidence_ids
    )
    if missing_protected:
        raise EvidenceConsumerError(
            "failed_rehydration_lookup",
            f"protected evidence ids were not admitted: {missing_protected}",
        )
    if not candidates:
        raise EvidenceConsumerError("selection_spec", "no axis-bound candidates admitted")
    return candidates


def _relation_schema(*, value_policy: bool = False) -> dict[str, Any]:
    def result_row(relation: str | None = None) -> dict[str, Any]:
        relation_schema: dict[str, Any] = {"type": "string"}
        reason_schema: dict[str, Any] = {"type": "string"}
        if relation is None:
            relation_schema["enum"] = list(RELATIONS)
        else:
            relation_schema["const"] = relation
            reason_schema["enum"] = sorted(
                code
                for code, expected_relation in VALUE_REASON_RELATIONS.items()
                if expected_relation == relation
            )
        return {
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string"},
                "relation": relation_schema,
                "reason_code": reason_schema,
            },
            "required": ["candidate_id", "relation", "reason_code"],
            "additionalProperties": False,
        }

    row = (
        {"anyOf": [result_row(relation) for relation in RELATIONS]}
        if value_policy
        else result_row()
    )
    return {
        "type": "object",
        "properties": {"results": {"type": "array", "items": row}},
        "required": ["results"],
        "additionalProperties": False,
    }


def _quote_schema() -> dict[str, Any]:
    row = {
        "type": "object",
        "properties": {
            "selected_id": {"type": "string"},
            "quote_status": {
                "type": "string",
                "enum": ["quote_available", "quote_unavailable"],
            },
            "exact_quote": {"type": ["string", "null"]},
        },
        "required": [
            "selected_id",
            "quote_status",
            "exact_quote",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"quotes": {"type": "array", "items": row}},
        "required": ["quotes"],
        "additionalProperties": False,
    }


def prepare_evidence_selection(
    spec: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if spec.get("schema_version") != SELECTION_SPEC_VERSION:
        raise EvidenceConsumerError("selection_spec", "unsupported selection spec")
    if not isinstance(spec.get("selection_id"), str) or not spec["selection_id"]:
        raise EvidenceConsumerError("selection_spec", "selection_id missing")
    if not isinstance(spec.get("bounded_claim"), str) or not spec["bounded_claim"].strip():
        raise EvidenceConsumerError("selection_spec", "bounded_claim missing")
    for source in sources:
        _verify_packet(source["packet"])
        bundle = source["bundle"]
        packet_bundle = source["packet"].get("source_bindings", {}).get("bundle_sha256")
        if bundle.get("bundle_sha256") != packet_bundle:
            raise EvidenceConsumerError("bundle_verification", "packet/bundle hash mismatch")
        _verify_bundle(bundle)
    candidates = _candidate_rows(sources, spec)
    envelope = {
        "selection_id": spec["selection_id"],
        "bounded_claim": spec["bounded_claim"],
        "candidates": candidates,
    }
    value_policy = _uses_value_policy(spec)
    prompt = RELATION_PROMPT.format(
        policy_guidance=_policy_guidance(spec), envelope=_compact(envelope)
    )
    schema = _relation_schema(value_policy=value_policy)
    inventory_sha = _canonical_json_sha256(candidates)
    manifest = {
        "schema_version": SELECTION_MANIFEST_VERSION,
        "selection_id": spec["selection_id"],
        "spec": dict(spec),
        "candidate_count": len(candidates),
        "candidate_inventory_sha256": inventory_sha,
        "sources": [
            {
                "source_id": source["source_id"],
                "packet_path": str(source["packet_path"]),
                "packet_sha256": source["packet"]["packet_sha256"],
                "packet_file_sha256": hash_file(source["packet_path"]),
                "bundle_path": str(source["bundle_path"]),
                "bundle_sha256": source["bundle"]["bundle_sha256"],
                "bundle_file_sha256": hash_file(source["bundle_path"]),
            }
            for source in sources
        ],
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "model_api_calls": 0,
    }
    manifest["manifest_sha256"] = _canonical_json_sha256(manifest)
    return prompt, schema, manifest


def load_selection_sources(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    stored = manifest.get("manifest_sha256")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("schema_version") != SELECTION_MANIFEST_VERSION or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError("manifest_verification", "selection manifest changed")
    sources = []
    for row in manifest.get("sources", []):
        packet_path = Path(row["packet_path"])
        bundle_path = Path(row["bundle_path"])
        if hash_file(packet_path) != row["packet_file_sha256"] or hash_file(bundle_path) != row["bundle_file_sha256"]:
            raise EvidenceConsumerError("manifest_verification", "bound source file changed")
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        if packet.get("packet_sha256") != row["packet_sha256"] or bundle.get("bundle_sha256") != row["bundle_sha256"]:
            raise EvidenceConsumerError("manifest_verification", "bound source identity changed")
        sources.append({**row, "packet": packet, "bundle": bundle, "packet_path": packet_path, "bundle_path": bundle_path})
    candidates = _candidate_rows(sources, manifest["spec"])
    if _canonical_json_sha256(candidates) != manifest.get("candidate_inventory_sha256"):
        raise EvidenceConsumerError("manifest_verification", "candidate inventory changed")
    return sources


def _global_priority(row: Mapping[str, Any]) -> tuple[Any, ...]:
    material = row.get("engagement_material_positive") is True
    return (
        0 if row.get("protected_lanes") else 1,
        0 if row.get("relation") in {"support", "counter"} else 1,
        0 if material else 1,
        row["candidate_id"],
    )


def _bucket_priority(row: Mapping[str, Any]) -> tuple[Any, ...]:
    numeric = _numeric_engagement(
        row.get("engagement_raw_value"), row.get("engagement_kind")
    )
    return (
        0 if row.get("protected_lanes") else 1,
        0 if row.get("relation") in {"support", "counter"} else 1,
        0 if row.get("engagement_material_positive") is True else 1,
        # An uncomparable value orders last on its own rank, so a negative
        # source-native score cannot sort below an unavailable one.
        0 if numeric is not None else 1,
        -numeric if numeric is not None else 0.0,
        row["candidate_id"],
    )


def _display_members(members: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted((dict(row) for row in members), key=_global_priority)
    displays = [ordered[0]]
    first = ordered[0]
    distinct = [
        row
        for row in ordered[1:]
        if row.get("engagement_material_positive") is True
        and (row["relation"] != first["relation"] or row.get("conditions") != first.get("conditions"))
    ]
    if distinct:
        displays.append(distinct[0])
    return displays


def _member_display_lanes(row: Mapping[str, Any]) -> set[str]:
    lanes = {f"relation:{row['relation']}"}
    lanes.update(f"protected:{lane}" for lane in row.get("protected_lanes", []))
    return lanes


def _required_display_members(
    members: Sequence[Mapping[str, Any]],
    required_lanes: Sequence[str],
    required_candidate_ids: Sequence[str],
    *,
    priority: Any = _global_priority,
) -> list[dict[str, Any]]:
    """Return the deterministic minimum rows that make reserved lanes visible.

    Operator-protected candidates are mandatory rows.  At most four ordinary
    lane requirements remain, so exhaustive combinations over one representative
    per distinct coverage signature are bounded and prove minimal cardinality.
    """
    ordered = sorted((dict(row) for row in members), key=priority)
    by_id = {row["candidate_id"]: row for row in ordered}
    try:
        forced = [by_id[candidate_id] for candidate_id in required_candidate_ids]
    except KeyError as exc:
        raise EvidenceConsumerError(
            "required_display_lane_unavailable",
            f"protected candidate is absent from its origin: {exc.args[0]}",
        ) from exc
    required = set(required_lanes)
    covered = set().union(*(_member_display_lanes(row) for row in forced)) if forced else set()
    remaining_lanes = required - covered
    if not remaining_lanes:
        return forced

    forced_ids = set(required_candidate_ids)
    representatives: dict[frozenset[str], dict[str, Any]] = {}
    for row in ordered:
        if row["candidate_id"] in forced_ids:
            continue
        coverage = frozenset(_member_display_lanes(row) & remaining_lanes)
        if coverage and coverage not in representatives:
            representatives[coverage] = row
    choices = list(representatives.values())
    for size in range(1, min(len(remaining_lanes), len(choices)) + 1):
        for chosen in combinations(choices, size):
            chosen_coverage = set().union(*(_member_display_lanes(row) for row in chosen))
            if remaining_lanes <= chosen_coverage:
                return forced + list(chosen)
    raise EvidenceConsumerError(
        "required_display_lane_unavailable",
        f"origin cannot display required lanes: {sorted(remaining_lanes)}",
    )


def _flatten_display_groups(groups: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in groups:
        for display in group["display_members"]:
            rows.append(
                {
                    **display,
                    "origin_group_id": group["origin_group_id"],
                    "origin_candidate_count": group["origin_candidate_count"],
                    "origin_relations": group["origin_relations"],
                    "origin_candidate_ids": group["origin_candidate_ids"],
                    "origin_required_display_lanes": group["required_display_lanes"],
                    "origin_required_display_candidate_ids": group["required_display_candidate_ids"],
                }
            )
    return rows


def _validate_protected_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    protected_wrong_layer = [
        row["candidate_id"]
        for row in rows
        if row.get("protected_lanes") and row.get("layer") != "truth_support"
    ]
    if protected_wrong_layer:
        raise EvidenceConsumerError(
            "protected_lane_wrong_layer",
            f"protected evidence is not customer truth evidence: {protected_wrong_layer}",
        )
    protected_excluded = [
        row["candidate_id"]
        for row in rows
        if row.get("protected_lanes") and row.get("relation") == "exclude"
    ]
    if protected_excluded:
        raise EvidenceConsumerError(
            "protected_candidate_excluded",
            f"protected evidence cannot be excluded from presentation: {protected_excluded}",
        )


def _value_member_priority(row: Mapping[str, Any]) -> tuple[Any, ...]:
    if row.get("relation") == "support":
        return (0, VALUE_SUPPORT_PRIORITY.get(row.get("reason_code"), 99)) + _bucket_priority(row)
    if row.get("relation") == "counter":
        return (1, 0) + _bucket_priority(row)
    return (2, 0) + _bucket_priority(row)


def _value_anchor_priority(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Choose a semantic signal before a source bucket, then rank natively.

    Source role, venue, and metric precede the native engagement value, so a
    Reddit score is never numerically compared with retailer helpful votes.
    Within one bucket, the existing source-native engagement order still
    applies.
    """
    relation = row.get("relation")
    if relation == "support":
        signal_priority = VALUE_SUPPORT_PRIORITY.get(row.get("reason_code"), 99)
    elif relation == "counter":
        signal_priority = VALUE_COUNTER_PRIORITY.get(row.get("reason_code"), 99)
    else:
        signal_priority = 99
    return (
        signal_priority,
        row["source_role"],
        row["source_venue"],
        row["engagement_kind"],
    ) + _bucket_priority(row)


def _protected_value_group_priority(group: Mapping[str, Any]) -> tuple[Any, ...]:
    """Order mandatory groups without comparing engagement across venues."""
    member_keys = []
    for member in group["origin_members"]:
        relation = member.get("relation")
        relation_priority = 0 if relation == "support" else 1 if relation == "counter" else 2
        member_keys.append(
            (
                relation_priority,
                (
                    VALUE_SUPPORT_PRIORITY.get(member.get("reason_code"), 99)
                    if relation == "support"
                    else VALUE_COUNTER_PRIORITY.get(member.get("reason_code"), 99)
                    if relation == "counter"
                    else 99
                ),
                member["source_role"],
                member["source_venue"],
                member["engagement_kind"],
                member["candidate_id"],
            )
        )
    return min(member_keys)


def _select_value_groups(rows: Sequence[Mapping[str, Any]], cap: int) -> list[dict[str, Any]]:
    _validate_protected_rows(rows)
    eligible = [
        dict(row)
        for row in rows
        if row["layer"] == "truth_support"
        and row["relation"] != "exclude"
        and (
            bool(row.get("protected_lanes"))
            or (
                row.get("engagement_material_positive") is True
                and row["relation"] in {"support", "counter"}
            )
        )
    ]
    origins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        origins[row["scoped_independence_key"]].append(row)

    groups = []
    for origin, members in origins.items():
        members.sort(key=_value_member_priority)
        representative = dict(members[0])
        groups.append(
            {
                **representative,
                "origin_group_id": origin,
                "origin_candidate_count": len(members),
                "origin_relations": sorted({row["relation"] for row in members}),
                "origin_candidate_ids": sorted(row["candidate_id"] for row in members),
                "origin_protected_lanes": sorted(
                    {
                        lane
                        for row in members
                        for lane in row.get("protected_lanes", [])
                    }
                ),
                "origin_members": members,
                "required_display_lanes": [],
                "required_display_candidate_ids": sorted(
                    row["candidate_id"] for row in members if row.get("protected_lanes")
                ),
            }
        )

    selected: list[dict[str, Any]] = []
    selected_origins: set[str] = set()

    def add_group(group: dict[str, Any]) -> bool:
        if group["origin_group_id"] in selected_origins:
            return False
        selected.append(group)
        selected_origins.add(group["origin_group_id"])
        if len(selected_origins) > cap:
            raise EvidenceConsumerError(
                "presentation_cap_insufficient", "required origin groups exceed cap"
            )
        return True

    for group in sorted(
        (row for row in groups if row["origin_protected_lanes"]),
        key=_protected_value_group_priority,
    ):
        add_group(group)
        group["required_display_lanes"].extend(
            f"protected:{lane}" for lane in group["origin_protected_lanes"]
        )

    support_buckets: dict[
        tuple[str, str, str], list[tuple[dict[str, Any], dict[str, Any]]]
    ] = defaultdict(list)
    for group in groups:
        support_members = [
            row for row in group["origin_members"] if row["relation"] == "support"
        ]
        if not support_members:
            continue
        best = min(support_members, key=_value_member_priority)
        support_buckets[
            (best["source_role"], best["source_venue"], best["engagement_kind"])
        ].append((group, best))
    for bucket in support_buckets.values():
        bucket.sort(key=lambda pair: _value_member_priority(pair[1]))

    support_keys = sorted(support_buckets)
    first_support: tuple[dict[str, Any], dict[str, Any]] | None = None
    ordinary_support_order: list[dict[str, Any]] = []

    # Bind the complaint bucket to the best kind of positive value signal, not
    # to whichever source bucket happens to sort first.  Engagement is used only
    # after the source-native bucket is fixed.
    anchor_choices = [pair for bucket in support_buckets.values() for pair in bucket]
    if anchor_choices:
        anchor_group, anchor_member = min(
            anchor_choices, key=lambda pair: _value_anchor_priority(pair[1])
        )
        if anchor_group["origin_group_id"] in selected_origins or len(selected) < cap:
            if "relation:support" not in anchor_group["required_display_lanes"]:
                anchor_group["required_display_lanes"].append("relation:support")
            was_added = add_group(anchor_group)
            if was_added and not anchor_group["origin_protected_lanes"]:
                ordinary_support_order.append(anchor_group)
            first_support = (anchor_group, anchor_member)

    while len(selected) < cap and any(support_buckets[key] for key in support_keys):
        for key in support_keys:
            if len(selected) >= cap:
                break
            if not support_buckets[key]:
                continue
            group, member = support_buckets[key].pop(0)
            if "relation:support" not in group["required_display_lanes"]:
                group["required_display_lanes"].append("relation:support")
            was_added = add_group(group)
            if was_added and first_support is None:
                first_support = (group, member)
            if was_added and not group["origin_protected_lanes"]:
                ordinary_support_order.append(group)

    protected_counter_visible = any(
        member.get("protected_lanes") and member["relation"] == "counter"
        for group in selected
        for member in group["origin_members"]
    )
    if not protected_counter_visible:
        primary_member = first_support[1] if first_support is not None else None
        if primary_member is None:
            counter_anchor_choices = []
            for group in groups:
                counter_anchor_choices.extend(
                    (group, member)
                    for member in group["origin_members"]
                    if member["relation"] == "counter"
                )
            if counter_anchor_choices:
                _, primary_member = min(
                    counter_anchor_choices,
                    key=lambda pair: _value_anchor_priority(pair[1]),
                )
        primary_bucket = (
            (
                primary_member["source_role"],
                primary_member["source_venue"],
                primary_member["engagement_kind"],
            )
            if primary_member is not None
            else None
        )
        counter_choices: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for group in groups:
            matching = [
                row
                for row in group["origin_members"]
                if row["relation"] == "counter"
                and primary_bucket is not None
                and (
                    row["source_role"],
                    row["source_venue"],
                    row["engagement_kind"],
                )
                == primary_bucket
            ]
            if matching:
                counter_choices.append((group, min(matching, key=_bucket_priority)))
        counter_choices.sort(key=lambda pair: _bucket_priority(pair[1]))
        if counter_choices:
            counter_group, _ = counter_choices[0]
            if counter_group["origin_group_id"] not in selected_origins and len(selected) >= cap:
                removable = next(
                    (
                        group
                        for group in reversed(ordinary_support_order)
                        if group is not first_support[0]
                    ),
                    None,
                )
                if removable is not None:
                    selected.remove(removable)
                    selected_origins.remove(removable["origin_group_id"])
                    ordinary_support_order.remove(removable)
            if counter_group["origin_group_id"] in selected_origins or len(selected) < cap:
                add_group(counter_group)
                if "relation:counter" not in counter_group["required_display_lanes"]:
                    counter_group["required_display_lanes"].append("relation:counter")

    for group in selected:
        group["display_members"] = _required_display_members(
            group["origin_members"],
            group["required_display_lanes"],
            group["required_display_candidate_ids"],
            priority=_value_member_priority,
        )
        group.pop("origin_members")
    displayed = _flatten_display_groups(selected)
    protected_candidate_ids = {
        row["candidate_id"] for row in eligible if row.get("protected_lanes")
    }
    displayed_candidate_ids = {row["candidate_id"] for row in displayed}
    if not protected_candidate_ids <= displayed_candidate_ids:
        raise EvidenceConsumerError(
            "protected_candidate_not_visible",
            "one or more protected candidates are absent from the display",
        )
    ordinary_counter_origins = {
        row["origin_group_id"]
        for row in displayed
        if row["relation"] == "counter" and not row.get("protected_lanes")
    }
    if len(ordinary_counter_origins) > 1:
        raise EvidenceConsumerError(
            "value_counter_cap", "value presentation contains more than one ordinary complaint"
        )
    return displayed


def _select_groups(
    rows: Sequence[Mapping[str, Any]],
    layer: str,
    cap: int,
    *,
    truth_policy: str = "balanced",
) -> list[dict[str, Any]]:
    if truth_policy not in {"balanced", "value_first"}:
        raise EvidenceConsumerError("selection_policy", f"unsupported policy: {truth_policy}")
    if truth_policy == "value_first" and layer == "truth_support":
        return _select_value_groups(rows, cap)
    _validate_protected_rows(rows)
    eligible = [
        dict(row)
        for row in rows
        if row["layer"] == layer
        and row["relation"] != "exclude"
        and (
            layer != "truth_support"
            or bool(row.get("protected_lanes"))
            or row.get("engagement_material_positive") is True
        )
    ]
    origins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        origins[row["scoped_independence_key"]].append(row)
    groups = []
    for origin, members in origins.items():
        members.sort(key=_global_priority)
        representative = dict(members[0])
        groups.append(
            {
                **representative,
                "origin_group_id": origin,
                "origin_candidate_count": len(members),
                "origin_relations": sorted({row["relation"] for row in members}),
                "origin_candidate_ids": sorted(row["candidate_id"] for row in members),
                "origin_protected_lanes": sorted(
                    {
                        lane
                        for row in members
                        for lane in row.get("protected_lanes", [])
                    }
                ),
                "origin_members": members,
                "required_display_lanes": [],
                "required_display_candidate_ids": sorted(
                    row["candidate_id"] for row in members if row.get("protected_lanes")
                ),
            }
        )

    selected: list[dict[str, Any]] = []
    selected_origins: set[str] = set()

    def add_group(group: dict[str, Any]) -> None:
        if group["origin_group_id"] not in selected_origins:
            selected.append(group)
            selected_origins.add(group["origin_group_id"])
        if len(selected_origins) > cap:
            raise EvidenceConsumerError(
                "presentation_cap_insufficient", "required origin groups exceed cap"
            )

    def reserve_lane(lane: str, predicate: Any) -> None:
        eligible_groups = [row for row in groups if predicate(row)]
        if not eligible_groups:
            return
        already_selected = [
            row for row in eligible_groups if row["origin_group_id"] in selected_origins
        ]
        choice = sorted(already_selected or eligible_groups, key=_global_priority)[0]
        add_group(choice)
        choice["required_display_lanes"].append(lane)

    if layer == "truth_support":
        for group in sorted(
            (row for row in groups if row["origin_protected_lanes"]),
            key=_global_priority,
        ):
            add_group(group)
            group["required_display_lanes"].extend(
                f"protected:{lane}" for lane in group["origin_protected_lanes"]
            )
        reserve_lane("relation:support", lambda row: "support" in row["origin_relations"])
        reserve_lane("relation:counter", lambda row: "counter" in row["origin_relations"])

    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in groups:
        if row["origin_group_id"] not in selected_origins:
            buckets[(row["source_role"], row["source_venue"], row["engagement_kind"])].append(row)
    for bucket in buckets.values():
        bucket.sort(key=_bucket_priority)
    keys = sorted(buckets)
    while len(selected) < cap and any(buckets[key] for key in keys):
        for key in keys:
            if len(selected) >= cap:
                break
            if buckets[key]:
                row = buckets[key].pop(0)
                selected.append(row)
                selected_origins.add(row["origin_group_id"])
    if len(groups) <= cap:
        for row in sorted(
            groups,
            key=lambda group: (
                group["source_role"],
                group["source_venue"],
                _global_priority(group),
            ),
        ):
            add_group(row)
    for group in selected:
        if group["required_display_lanes"] or group["required_display_candidate_ids"]:
            group["display_members"] = _required_display_members(
                group["origin_members"],
                group["required_display_lanes"],
                group["required_display_candidate_ids"],
            )
        else:
            group["display_members"] = _display_members(group["origin_members"])
        group.pop("origin_members")
    displayed = _flatten_display_groups(selected)
    protected_candidate_ids = {
        row["candidate_id"] for row in eligible if row.get("protected_lanes")
    }
    displayed_candidate_ids = {row["candidate_id"] for row in displayed}
    if not protected_candidate_ids <= displayed_candidate_ids:
        raise EvidenceConsumerError(
            "protected_candidate_not_visible",
            "one or more protected candidates are absent from the display",
        )
    return displayed


def _validate_relation_response(
    candidates: Sequence[Mapping[str, Any]],
    response: Mapping[str, Any],
    *,
    value_policy: bool = False,
) -> list[dict[str, Any]]:
    if set(response) != {"results"} or not isinstance(response.get("results"), list):
        raise EvidenceConsumerError("relation_response_shape", "results missing")
    results = response["results"]
    expected = [row["candidate_id"] for row in candidates]
    observed = [row.get("candidate_id") for row in results if isinstance(row, dict)]
    if len(observed) != len(results):
        raise EvidenceConsumerError("relation_response_shape", "invalid result row")
    if len(observed) != len(set(observed)):
        raise EvidenceConsumerError("duplicate_candidate_result", "candidate repeated")
    if set(observed) - set(expected):
        raise EvidenceConsumerError("foreign_candidate_result", "foreign candidate returned")
    if len(observed) != len(expected) or set(observed) != set(expected):
        raise EvidenceConsumerError("missing_candidate_result", "candidate set incomplete")
    if observed != expected:
        raise EvidenceConsumerError("candidate_order_mismatch", "candidate order changed")
    merged = []
    for candidate, result in zip(candidates, results, strict=True):
        if set(result) != {"candidate_id", "relation", "reason_code"}:
            raise EvidenceConsumerError("relation_response_shape", "result shape mismatch")
        if (
            result["relation"] not in RELATIONS
            or not isinstance(result["reason_code"], str)
            or len(result["reason_code"]) > 80
            or not REASON_CODE_RE.fullmatch(result["reason_code"])
        ):
            raise EvidenceConsumerError("relation_response_shape", "invalid relation result")
        if INTERNAL_RELATION_LABEL_RE.search(result["reason_code"].replace("_", " ")):
            raise EvidenceConsumerError(
                "reason_code_relation_leak",
                "reason code must name the evidence meaning, not its internal relation",
            )
        if value_policy:
            expected_relation = VALUE_REASON_RELATIONS.get(result["reason_code"])
            if expected_relation is None:
                raise EvidenceConsumerError(
                    "value_reason_code",
                    "value selection used an unsupported meaning code",
                )
            if result["relation"] != expected_relation:
                raise EvidenceConsumerError(
                    "value_reason_relation_mismatch",
                    "value meaning code does not match its relation lane",
                )
        if candidate["layer"] == "influence_context" and result["relation"] in {"support", "counter"}:
            raise EvidenceConsumerError(
                "creator_customer_laundering", "creator-authored evidence cannot corroborate customer truth"
            )
        merged.append({**candidate, "relation": result["relation"], "reason_code": result["reason_code"]})
    return merged


def _display_label(reason_code: str) -> str:
    label = DISPLAY_LABEL_BY_REASON_CODE.get(
        reason_code,
        reason_code.replace("_", " ").capitalize(),
    )
    if len(label) > 80 or INTERNAL_RELATION_LABEL_RE.search(label):
        raise EvidenceConsumerError(
            "display_label",
            "reason code cannot produce a safe customer-facing display label",
        )
    return label


def _bundle_bodies(sources: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], str | None]:
    bodies: dict[tuple[str, str], str | None] = {}
    for source in sources:
        packet_index, _ = _expand_packet(source["packet"])
        units = source["bundle"].get("evidence_units")
        if not isinstance(units, list):
            raise EvidenceConsumerError("bundle_verification", "bundle evidence_units missing")
        bundle_index = {row.get("evidence_id"): row for row in units if isinstance(row, dict)}
        for evidence_id, (_, evidence) in packet_index.items():
            unit = bundle_index.get(evidence_id)
            if unit is None:
                bodies[(source["source_id"], evidence_id)] = None
                continue
            if unit.get("source_artifact_id") != evidence.get("source_artifact_id") or unit.get("source_ref") != evidence.get("source_ref"):
                raise EvidenceConsumerError("body_identity_mismatch", evidence_id)
            text = unit.get("text")
            bodies[(source["source_id"], evidence_id)] = text if isinstance(text, str) and text else None
    return bodies


def finalize_relations_prepare_quotes(
    manifest: Mapping[str, Any], sources: Sequence[Mapping[str, Any]], response: Mapping[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    candidates = _candidate_rows(sources, manifest["spec"])
    value_policy = _uses_value_policy(manifest["spec"])
    labeled = _validate_relation_response(
        candidates, response, value_policy=value_policy
    )
    truth = _select_groups(
        labeled,
        "truth_support",
        MAX_TRUTH_GROUPS,
        truth_policy="value_first" if value_policy else "balanced",
    )
    influence = _select_groups(labeled, "influence_context", MAX_INFLUENCE_GROUPS)
    selected = truth + influence
    bodies = _bundle_bodies(sources)
    quote_rows = []
    for index, row in enumerate(selected, start=1):
        selected_id = f"selected_{index:02d}"
        row["selected_id"] = selected_id
        quote_rows.append(
            {
                "selected_id": selected_id,
                "candidate_id": row["candidate_id"],
                "normalized_meaning": row["normalized_meaning"],
                "same_evidence_companion_meanings": row[
                    "same_evidence_companion_meanings"
                ],
                "relation": row["relation"],
                "reason_code": row["reason_code"],
                "display_label": _display_label(row["reason_code"]),
                "source_body": bodies.get((row["source_id"], row["evidence_id"])),
            }
        )
    prompt = QUOTE_PROMPT.format(
        envelope=_compact(
            {
                "bounded_claim": manifest["spec"]["bounded_claim"],
                "selected_rows": quote_rows,
            }
        )
    )
    schema = _quote_schema()
    quote_manifest = {
        "schema_version": QUOTE_MANIFEST_VERSION,
        "selection_manifest_sha256": manifest["manifest_sha256"],
        "candidate_inventory_sha256": manifest["candidate_inventory_sha256"],
        "labeled_inventory": labeled,
        "labeled_inventory_sha256": _canonical_json_sha256(labeled),
        "selected_rows": selected,
        "selected_rows_sha256": _canonical_json_sha256(selected),
        "quote_body_sha256": {
            row["selected_id"]: sha256_text(row["source_body"]) if row["source_body"] is not None else None
            for row in quote_rows
        },
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "model_api_calls": 0,
    }
    quote_manifest["manifest_sha256"] = _canonical_json_sha256(quote_manifest)
    return prompt, schema, quote_manifest


def finalize_quotes(
    quote_manifest: Mapping[str, Any], sources: Sequence[Mapping[str, Any]], response: Mapping[str, Any]
) -> dict[str, Any]:
    stored = quote_manifest.get("manifest_sha256")
    payload = {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    manifest_version = quote_manifest.get("schema_version")
    if (
        manifest_version not in {LEGACY_QUOTE_MANIFEST_VERSION, QUOTE_MANIFEST_VERSION}
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError("manifest_verification", "quote manifest changed")
    if set(response) != {"quotes"} or not isinstance(response.get("quotes"), list):
        raise EvidenceConsumerError("quote_response_shape", "quotes missing")
    selected = quote_manifest["selected_rows"]
    expected = [row["selected_id"] for row in selected]
    quotes = response["quotes"]
    observed = [row.get("selected_id") for row in quotes if isinstance(row, dict)]
    if len(observed) != len(quotes):
        raise EvidenceConsumerError("quote_response_shape", "invalid quote row")
    if len(observed) != len(set(observed)):
        raise EvidenceConsumerError("duplicate_quote_result", "selected row repeated")
    if set(observed) - set(expected):
        raise EvidenceConsumerError("foreign_quote_result", "foreign selected row")
    if observed != expected:
        boundary = "missing_quote_result" if set(observed) != set(expected) else "quote_order_mismatch"
        raise EvidenceConsumerError(boundary, "quote result set/order mismatch")
    bodies = _bundle_bodies(sources)
    recorded_body_hashes = quote_manifest["quote_body_sha256"]
    output_rows = []
    for selected_row, quote_row in zip(selected, quotes, strict=True):
        expected_quote_fields = {"selected_id", "quote_status", "exact_quote"}
        if set(quote_row) != expected_quote_fields:
            raise EvidenceConsumerError("quote_response_shape", "quote row shape mismatch")
        body = bodies.get((selected_row["source_id"], selected_row["evidence_id"]))
        selected_id = selected_row["selected_id"]
        if selected_id not in recorded_body_hashes:
            raise EvidenceConsumerError(
                "manifest_verification", f"quote manifest recorded no body hash for {selected_id}"
            )
        if (sha256_text(body) if body is not None else None) != recorded_body_hashes[selected_id]:
            raise EvidenceConsumerError(
                "body_identity_mismatch",
                f"source body changed after the quote manifest was written: {selected_id}",
            )
        status = quote_row["quote_status"]
        quote = quote_row["exact_quote"]
        if body is None:
            if status != "quote_unavailable" or quote is not None:
                raise EvidenceConsumerError("quote_unavailable", "missing body cannot produce a quote")
        elif status == "quote_available":
            if not isinstance(quote, str) or not quote:
                raise EvidenceConsumerError("quote_exactness", "available quote missing")
            if len(quote) > MAX_QUOTE_CHARACTERS:
                raise EvidenceConsumerError("quote_overlength", "quote exceeds 220 characters")
            if sum(character.isalnum() for character in quote) < 2:
                raise EvidenceConsumerError(
                    "quote_substance", "available quote has fewer than two alphanumeric characters"
                )
            if quote not in body:
                raise EvidenceConsumerError("quote_exactness", "quote is not a contiguous exact substring")
            if len(body) <= MAX_QUOTE_CHARACTERS and quote != body:
                raise EvidenceConsumerError(
                    "quote_context_incomplete",
                    "a short source body must be quoted in full",
                )
        elif status == "quote_unavailable":
            if quote is not None:
                raise EvidenceConsumerError("quote_response_shape", "unavailable quote must be null")
        else:
            raise EvidenceConsumerError("quote_response_shape", "invalid quote status")
        output_rows.append(
            {
                "selected_id": selected_row["selected_id"],
                "layer": selected_row["layer"],
                "source_family": selected_row["source_family"],
                "source_role": selected_row["source_role"],
                "source_venue": selected_row["source_venue"],
                "source_venue_basis": selected_row["source_venue_basis"],
                "quote_status": status,
                # A reader cannot otherwise tell an absent source body from a
                # body that was present and yielded no quote.
                "source_body_present": body is not None,
                "quote_unavailable_cause": (
                    None
                    if status == "quote_available"
                    else (
                        "source_body_unavailable"
                        if body is None
                        else "no_relevant_exact_quote_returned"
                    )
                ),
                "exact_quote": quote,
                **(
                    {"display_label": _display_label(selected_row["reason_code"])}
                    if manifest_version == QUOTE_MANIFEST_VERSION
                    else {}
                ),
                "normalized_meaning": selected_row["normalized_meaning"],
                "same_evidence_companion_meanings": selected_row[
                    "same_evidence_companion_meanings"
                ],
                "relation": selected_row["relation"],
                "reason_code": selected_row["reason_code"],
                "engagement_kind": selected_row["engagement_kind"],
                "engagement_raw_value": selected_row["engagement_raw_value"],
                "engagement_observed_at": selected_row["engagement_observed_at"],
                "publication_time": selected_row["publication_time"],
                "source_ref": selected_row["source_ref"],
                "evidence_id": selected_row["evidence_id"],
                "semantic_unit_ref": selected_row["semantic_unit_ref"],
                "independence_key": selected_row["independence_key"],
                "origin_group_id": selected_row["origin_group_id"],
                "origin_candidate_count": selected_row["origin_candidate_count"],
                "origin_candidate_ids": selected_row["origin_candidate_ids"],
            }
        )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in output_rows:
        grouped[
            f"{row['layer']}::{row['source_family']}::{row['source_role']}::{row['source_venue']}"
        ].append(row)
    return {
        "schema_version": "phase_a_evidence_selection_artifact_v1",
        "selection_manifest_sha256": quote_manifest["selection_manifest_sha256"],
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
        "candidate_inventory_sha256": quote_manifest["candidate_inventory_sha256"],
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "candidate_dispositions": quote_manifest["labeled_inventory"],
        "truth_group_count": len(
            {row["origin_group_id"] for row in output_rows if row["layer"] == "truth_support"}
        ),
        "influence_group_count": len(
            {row["origin_group_id"] for row in output_rows if row["layer"] == "influence_context"}
        ),
        "source_groups": [
            {"group_key": key, "rows": grouped[key]} for key in sorted(grouped)
        ],
        "output_boundary": [
            "not a prevalence estimate",
            "not a causal judgment",
            "not a commercial-pull score",
            "creator influence is not customer corroboration",
            "a source body of 220 characters or fewer is quoted in full to prevent context clipping",
            "longer exact quotes remain quality-adjudicated for semantic relevance and context completeness",
            "quote_unavailable with source_body_present true means no quote was produced from an available body",
            "quote_unavailable_cause names whether the source body was unavailable or returned no relevant exact quote",
        ],
        "model_api_calls": 0,
    }


__all__ = [
    "QUOTE_MANIFEST_VERSION",
    "SELECTION_MANIFEST_VERSION",
    "SELECTION_SPEC_VERSION",
    "finalize_quotes",
    "finalize_relations_prepare_quotes",
    "load_selection_sources",
    "prepare_evidence_selection",
]
