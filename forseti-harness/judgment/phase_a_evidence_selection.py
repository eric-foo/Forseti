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
from datetime import datetime
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
CUSTOMER_PULL_FRONTIER_VERSION = "phase_a_customer_pull_point_frontier_v1"
SELECTION_MANIFEST_VERSION = "phase_a_evidence_selection_manifest_v1"
PARENT_CONTEXT_POLICY = "linked_parent_context_v1"
SELECTION_BATCH_MANIFEST_VERSION = "phase_a_evidence_selection_batch_manifest_v1"
LEGACY_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v1"
PREVIOUS_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v3"
PRECONFIRMATION_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v4"
PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v5"
QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v6"
PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v7"
BATCHED_QUOTE_MANIFEST_VERSION = QUOTE_MANIFEST_VERSION
RELATION_CONFIRMATION_MANIFEST_VERSION = (
    "phase_a_evidence_relation_confirmation_manifest_v2"
)
PRESELECTION_RELATION_CONFIRMATION_MANIFEST_VERSION = (
    "phase_a_evidence_preselection_relation_confirmation_manifest_v1"
)
PRESELECTION_CONFIRMATION_BATCH_MANIFEST_VERSION = (
    "phase_a_evidence_preselection_confirmation_batch_manifest_v1"
)
RELATIONS = ("support", "counter", "adjacent", "exclude")
POINT_SCOPE_STATUSES = ("single_point", "broad_axis_or_bundle")
RELATION_RESPONSE_MODES = ("literal_ids", "positional")
RELATION_POLICIES = ("auto", "bounded_point")
TEMPORAL_PRESENTATION_POLICIES = ("recent_year_coverage_v1",)
FRONTIER_RELATION_DISPLAY_POLICY = "literal_point_relations_display_eligible_v1"
FRONTIER_RELATION_REJECTION_CAUSES = (
    "literal_source_does_not_state_bounded_relation",
    "no_context_complete_quote_within_display_limit",
)
RECENT_YEAR_COUNT = 2
POSITIONAL_REASON_CODE_BY_RELATION = {
    "support": "matching_customer_experience",
    "counter": "differing_customer_experience",
    "adjacent": "related_customer_context",
    "exclude": "wrong_scope_or_non_evidence",
}
TRUTH_ROLES = {"community_post", "retailer_review", "audience_comment"}
INFLUENCE_ROLES = {"creator_authored"}
MAX_TRUTH_GROUPS = 13
MAX_CONFIGURABLE_TRUTH_GROUPS = 20
MAX_RELATION_BATCH_SIZE = 300
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
    "high_spend_followed_by_buyer_remorse": "High spend, followed by buyer’s remorse",
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
    "high_spend_followed_by_buyer_remorse": "counter",
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
    "high_spend_followed_by_buyer_remorse": 0,
    "purchase_regret_due_cost": 0,
    "explicit_poor_value": 0,
    "performance_not_worth_price": 1,
    "price_increase_quality_decline": 1,
    "too_little_product_for_price": 2,
    "packaging_waste_undermines_value": 2,
    "cheaper_equivalent_available": 3,
    "comparator_better_value": 3,
}

LITERAL_RELATION_RESPONSE_INSTRUCTION = "Return every candidate_id exactly once and in the supplied order."
POSITIONAL_RELATION_RESPONSE_INSTRUCTION = "Return one relation for every required row_NNNN property under results_by_candidate_row. Each row_NNNN property corresponds to zero-based supplied candidate position NNNN. Do not return candidate IDs, row numbers, or reason codes."
BATCHED_RELATION_RESPONSE_INSTRUCTION = "Return the batch_id shown in the envelope exactly as supplied, and one relation for every required row_NNNN property under results_by_candidate_row. Each row_NNNN property corresponds to zero-based supplied candidate position NNNN within this batch only. Do not return candidate IDs, row numbers, or reason codes."

BOUNDED_POINT_RELATION_DEFINITIONS = " Support directly supports the bounded claim. Counter directly opposes or materially qualifies it. Adjacent is relevant context that directly establishes neither direction. Exclude is wrong-scope or non-evidence."


RELATION_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded claim and ordered, source-owned candidate rows below. Return only the required JSON.

{response_instruction} Label each row's relation to the bounded claim as support, counter, adjacent, or exclude.{reason_instruction}{relation_definitions} Relation is about meaning, never engagement size. Read same_evidence_companion_meanings as context that can qualify or reverse the candidate's implication, not as separately admitted candidates. Linked parent context may resolve an omitted referent or terse agreement only when the parent clearly supplies the same subject, attribute or outcome, direction, and material condition; otherwise do not inherit the missing meaning. A reply may adopt the parent's experience when it unambiguously says that the same thing happened to its own speaker, but the parent's experience never becomes the reply speaker's merely because both appear in one thread. Do not isolate price discomfort from same-source purchase or repurchase behavior: for a value claim, willingness to buy despite the price is countervailing behavior rather than evidence of poor value. Preserve product, variant, timing, comparison, uncertainty, and source-role boundaries. Keep a source's report of another person's experience adjacent unless the directly quoted speaker's own account is the evidence unit. A creator-authored item is influence context and cannot corroborate customer experience. Do not estimate prevalence, causation, commercial pull, or a number of similar customers.

{policy_guidance}

SELECTION_ENVELOPE_JSON:
{envelope}
"""

VALUE_RELATION_GUIDANCE = """VALUE-BOX POLICY: Use a support or counter label only when the candidate's normalized meaning directly concerns price, value, quantity-for-price, purchase commitment, repurchase, or whether benefits justify cost, either alone or together with its same-evidence companion meanings. Same-evidence meanings may jointly support one code when one supplies an explicit price/value premise and another supplies purchase, repurchase, repeated ownership, or stated benefits; the code must describe that combined visible meaning, never a conclusion absent from the whole same-evidence set. When an explicit price or cost premise is paired with purchase, repurchase, or repeated ownership, use the corresponding `*_despite_price` code rather than a plain behavior or generic good-value code. An explicit same-evidence statement of regret, waste, or poor value makes every candidate from that evidence origin counter or adjacent unless the same source explicitly says it will buy or repurchase again despite the cost, or explicitly concludes that the product is worth the price. Trying to make a regretted purchase feel more worthwhile by displaying empties, using it up, or otherwise rationalizing sunk cost does not countervail the regret or waste. Those two exceptions decide the lane before either regret code is considered: neither regret code may be used on an origin the same source keeps positive by explicitly buying or repurchasing again despite the cost, or by concluding the product is worth the price. Once the regret does keep the candidate counter, use `high_spend_followed_by_buyer_remorse` only when the same evidence explicitly states a substantial completed spend amount, or explicitly characterizes the completed spend as substantial, and also states cost-linked regret. Multiple units alone do not establish high spend. The code does not imply repurchase, a transaction count, or future intent. Use `purchase_regret_due_cost` when regret exists without explicit substantial completed spending. Companion meanings must not turn a formula, hydration, scent, trial-only, gift-card, or generic purchase statement into value evidence; those are adjacent unless the same-evidence set states the cost/value tradeoff. Use `repurchase_intent`, `multiple_purchases`, or `purchase_commitment` when the behavior is visible but price resistance is not; the corresponding `*_despite_price` code requires explicit source meaning about price or cost. Time to finish, pan, or empty a product is completed-use evidence, not quantity efficiency, repurchase, or good value by itself. If the same evidence explicitly says it will buy or repurchase again, use the matching purchase or repurchase code; otherwise keep completed use adjacent. Use `product_goes_a_long_way` only when the source explicitly says a small amount suffices or otherwise states quantity efficiency. `benefits_justify_price` requires an explicit worth/price tradeoff. `better_value_than_comparator` means the subject product is better value; `comparator_better_value` means the other product is better value. Use exactly one relation-aligned code from this list: {reason_codes}."""

QUOTE_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the ordered selected rows and source bodies below. Return only the required JSON.

Return every selected_id exactly once and in order. Choose one context-complete contiguous exact substring of at most 220 characters that directly substantiates every material component of the supplied normalized meaning, including its outcome, direction, comparator, product or formula distinction, and usage or timing condition when present. When the supplied body is 220 characters or shorter and is relevant, return the entire body; do not clip it. Include any nearby same-evidence companion meaning that materially qualifies or reverses it. Do not optimize for brevity: when the necessary source wording fits, retain it instead of clipping to a merely related phrase, and do not end mid-phrase or before a word that completes a material condition. Before returning each row, silently locate the source wording for every material component, expand the span for its antecedent and nearby qualification, then verify the final boundaries and length. Return quote_status=quote_unavailable and exact_quote=null only after verifying that no one contiguous span within 220 characters supports the full normalized meaning; inability to include optional non-reversing context is not enough. Do not start the quote with an unresolved pronoun such as she, he, they, it, this, that, these, or those when nearby preceding text names the antecedent and the combined span fits within 220 characters. Product identity may rely on the evidence row; this pronoun rule does not require the quote to repeat the product name or reject an otherwise exact, relevant span. The display_label is presentation metadata, not source meaning, and can never make an otherwise irrelevant substring acceptable. Use same_evidence_companion_meanings to detect context that cannot be clipped away. Preserve spelling and punctuation. Do not rewrite, repair, add ellipses, or combine non-contiguous spans.

SELECTED_EVIDENCE_ENVELOPE_JSON:
{envelope}
"""

RELATION_CONFIRMATION_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded point and ordered selected rows below. Return only the required JSON.

Independently classify every selected row as support, counter, adjacent, or exclude. Support directly supports the bounded point. Counter directly opposes or materially qualifies it. Adjacent is relevant context that does not directly establish either direction. Exclude is wrong-scope or non-evidence. Linked parent context may resolve an omitted referent or terse agreement only when the parent clearly supplies the same subject, attribute or outcome, direction, and material condition; otherwise do not inherit the missing meaning. point_parent_context_ids may clarify bounded_point for this scope decision, but they do not attach their meaning to every candidate. A candidate may use parent content for its own relation only when its parent_context_ids names that exact context. A reply may adopt the parent's experience when it unambiguously says that the same thing happened to its own speaker, but the parent's experience never becomes the reply speaker's merely because both appear in one thread. Preserve product, variant, timing, comparison, condition, uncertainty, and source-role boundaries. A source reporting another person's experience remains adjacent unless the directly quoted speaker's own account is the evidence unit. Creator-authored material remains adjacent influence context and cannot become customer corroboration. Judge meaning, not engagement or popularity.

Also decide whether bounded_point is one specific, direction-bearing proposition about one material product attribute or outcome under one compatible condition set. Two tightly joined effects remain one point when the source itself presents them as one experience under the same subject, direction, and conditions; do not split a source-native progression such as becoming dry and cracked merely because it names both effects. Return point_scope=single_point only for that shape. Return point_scope=broad_axis_or_bundle when it merely names an area of experience (for example "hydration experiences" or "value experiences"), combines materially different attributes/outcomes/directions/conditions, or otherwise could make unrelated mentions look corroborative. Give one short point_scope_reason based only on the supplied point and rows.

The first-pass relation, reason code, display label, engagement, and selection priority are intentionally absent. The rows carry opaque confirmation_row_id handles and are ordered by a content-derived key that encodes no first-pass signal, so neither the handle nor the row order tells you anything about the first pass. Return every confirmation_row_id exactly once and in order.

SELECTED_RELATION_CONFIRMATION_ENVELOPE_JSON:
{envelope}
"""

PRESELECTION_RELATION_CONFIRMATION_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded point and ordered candidate rows below. Return only the required JSON.

Independently classify every row as support, counter, adjacent, or exclude before any display cap is applied. Support directly supports the bounded point. Counter directly opposes or materially qualifies it. Adjacent is relevant context that does not directly establish either direction. Exclude is wrong-scope or non-evidence. Linked parent context may resolve an omitted referent or terse agreement only when the parent clearly supplies the same subject, attribute or outcome, direction, and material condition; otherwise do not inherit the missing meaning. point_parent_context_ids may clarify bounded_point for this scope decision, but they do not attach their meaning to every candidate. A candidate may use parent content for its own relation only when its parent_context_ids names that exact context. A reply may adopt the parent's experience when it unambiguously says that the same thing happened to its own speaker, but the parent's experience never becomes the reply speaker's merely because both appear in one thread. Preserve product, variant, timing, comparison, condition, uncertainty, and source-role boundaries. A source reporting another person's experience remains adjacent unless the directly quoted speaker's own account is the evidence unit. Creator-authored material remains adjacent influence context and cannot become customer corroboration. Judge meaning, not engagement or popularity. Return a short lowercase snake_case reason_code naming the visible evidence meaning without using those internal relation words.

{policy_guidance}

Also decide whether bounded_point is one specific, direction-bearing proposition about one material product attribute or outcome under one compatible condition set. Two tightly joined effects remain one point when the source itself presents them as one experience under the same subject, direction, and conditions; do not split a source-native progression such as becoming dry and cracked merely because it names both effects. Return point_scope=single_point only for that shape. Return point_scope=broad_axis_or_bundle when it merely names an area, combines materially different attributes, outcomes, directions, or conditions, or could make unrelated mentions look corroborative.

The first-pass relation, reason code, engagement, and selection priority are intentionally absent. Opaque row handles and content-derived order reveal no first-pass signal. Return every confirmation_row_id exactly once and in order.

PRESELECTION_RELATION_CONFIRMATION_ENVELOPE_JSON:
{envelope}
"""

PRESELECTION_CONFIRMATION_BATCH_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded point and ordered candidate rows below. Return only the required JSON.

Independently classify every row as support, counter, adjacent, or exclude before any display cap is applied. Support directly supports the bounded point. Counter directly opposes or materially qualifies it. Adjacent is relevant context that does not directly establish either direction. Exclude is wrong-scope or non-evidence. Linked parent context may resolve an omitted referent or terse agreement only when the parent clearly supplies the same subject, attribute or outcome, direction, and material condition; otherwise do not inherit the missing meaning. point_parent_context_ids may clarify bounded_point for this scope decision, but they do not attach their meaning to every candidate. A candidate may use parent content for its own relation only when its parent_context_ids names that exact context. A reply may adopt the parent's experience when it unambiguously says that the same thing happened to its own speaker, but the parent's experience never becomes the reply speaker's merely because both appear in one thread. Preserve product, variant, timing, comparison, condition, uncertainty, and source-role boundaries. A source reporting another person's experience remains adjacent unless the directly quoted speaker's own account is the evidence unit. Creator-authored material remains adjacent influence context and cannot become customer corroboration. Judge meaning, not engagement or popularity. Return a short lowercase snake_case reason_code naming the visible evidence meaning without using those internal relation words.

{policy_guidance}

Also decide whether bounded_point is one specific, direction-bearing proposition about one material product attribute or outcome under one compatible condition set. Two tightly joined effects remain one point when the source itself presents them as one experience under the same subject, direction, and conditions; do not split a source-native progression such as becoming dry and cracked merely because it names both effects. Return point_scope=single_point only for that shape. Return point_scope=broad_axis_or_bundle when it merely names an area, combines materially different attributes, outcomes, directions, or conditions, or could make unrelated mentions look corroborative.

The first-pass relation, reason code, engagement, and selection priority are intentionally absent. Opaque row handles and content-derived order reveal no first-pass signal. Return batch_id unchanged and every confirmation_row_id exactly once and in order.

PRESELECTION_RELATION_CONFIRMATION_BATCH_ENVELOPE_JSON:
{envelope}
"""


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _frontier_point_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    reasons = set(row.get("earning_reasons", []))
    origin_count = int(row.get("independent_support_origin_count", 0))
    material_count = len(row.get("material_support_evidence_ids", []))
    role_count = len(set(row.get("customer_support_roles", [])))
    cross_role_recurrence = origin_count >= 2 and role_count >= 2
    return (
        -origin_count,
        0 if cross_role_recurrence else 1,
        -material_count,
        0 if "reported_behavior" in reasons else 1,
        str(row.get("proposition_id")),
    )


def build_customer_pull_point_frontier(
    packet: Mapping[str, Any],
    *,
    frontier_id: str,
    business_question: str,
    subject_product_ids: Sequence[str],
    source_id: str = "full-corpus",
    protected_point_ids: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic retailer-first commercial investigation frontier.

    Retailer evidence earns the first-look queue because it is closest to a
    completed purchase, but it is deliberately not an admission gate.  A
    customer point found only in community evidence remains visible in the
    discovery queue and records that retailer check-back is still outstanding.
    """

    _verify_packet(packet)
    selection = packet.get("selection")
    coverage = packet.get("selection_coverage")
    if (
        not isinstance(selection, Mapping)
        or selection.get("mode") != "proposition"
        or not isinstance(coverage, Mapping)
        or coverage.get("truncated") is not False
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_input",
            "frontier requires a complete, non-truncated proposition packet",
        )
    if not isinstance(frontier_id, str) or not frontier_id.strip():
        raise EvidenceConsumerError("customer_pull_frontier_input", "frontier_id missing")
    if not isinstance(business_question, str) or not business_question.strip():
        raise EvidenceConsumerError(
            "customer_pull_frontier_input", "business_question missing"
        )
    if (
        not isinstance(source_id, str)
        or not source_id
        or not subject_product_ids
        or not all(isinstance(value, str) and value for value in subject_product_ids)
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_input", "source and subject product identities missing"
        )
    protected_input = protected_point_ids or {}
    if set(protected_input) - set(PROTECTED_LANES) or not all(
        isinstance(values, Sequence)
        and not isinstance(values, (str, bytes))
        and all(isinstance(value, str) for value in values)
        for values in protected_input.values()
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_input", "protected point lanes are invalid"
        )
    protected = {
        lane: sorted(set(values)) for lane, values in protected_input.items()
    }
    propositions = packet.get("propositions")
    selected_ids = selection.get("proposition_ids")
    if (
        not isinstance(propositions, list)
        or not isinstance(selected_ids, list)
        or not all(isinstance(value, str) for value in selected_ids)
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_input", "proposition inventory is invalid"
        )
    by_id = {
        row.get("proposition_id"): row
        for row in propositions
        if isinstance(row, Mapping) and isinstance(row.get("proposition_id"), str)
    }
    if len(by_id) != len(propositions) or set(by_id) != set(selected_ids):
        raise EvidenceConsumerError(
            "customer_pull_frontier_input", "selected proposition inventory is not exact"
        )
    wanted_subjects = set(subject_product_ids)
    evidence_index, _ = _expand_packet(packet)
    available_truth_roles = {
        group.get("source_role")
        for group in packet.get("source_groups", [])
        if isinstance(group, Mapping) and group.get("source_role") in TRUTH_ROLES
    }
    retailer_queue: list[dict[str, Any]] = []
    community_queue: list[dict[str, Any]] = []
    nonpromoted: list[dict[str, str]] = []
    considered_ids: list[str] = []
    subject_filtered_ids: list[str] = []

    protected_lookup = {
        proposition_id: lane
        for lane, proposition_ids in protected.items()
        for proposition_id in proposition_ids
    }
    unknown_protected = sorted(set(protected_lookup) - set(by_id))
    if unknown_protected:
        raise EvidenceConsumerError(
            "customer_pull_frontier_input",
            f"protected points are absent: {unknown_protected}",
        )

    for proposition_id in selected_ids:
        proposition = by_id[proposition_id]
        subjects = set(proposition.get("subject_product_ids") or [])
        if not (subjects & wanted_subjects):
            subject_filtered_ids.append(proposition_id)
            continue
        considered_ids.append(proposition_id)
        relations = _relation_rows(packet, proposition_id)
        relation_rows: dict[str, list[dict[str, Any]]] = {
            relation: [] for relation in ("support", "counter", "adjacent")
        }
        for relation_row in relations:
            evidence_id = relation_row["evidence_id"]
            if evidence_id not in evidence_index:
                raise EvidenceConsumerError(
                    "customer_pull_frontier_input",
                    f"linked evidence is unresolved: {evidence_id}",
                )
            group, evidence = evidence_index[evidence_id]
            engagement = evidence.get("engagement") or {}
            engagement_status = engagement.get("status") or "engagement_available"
            venue, venue_basis = _source_venue(
                str(group["source_role"]), evidence.get("source_ref"), evidence_id
            )
            relation_rows[relation_row["relation"]].append(
                {
                    "evidence_id": evidence_id,
                    "semantic_unit_refs": [relation_row["semantic_unit_ref"]],
                    "source_role": group["source_role"],
                    "source_venue": venue,
                    "source_venue_basis": venue_basis,
                    "engagement_kind": group["engagement_kind"],
                    "engagement_status": engagement_status,
                    "engagement_material_positive": (
                        engagement.get("material_positive")
                        if engagement_status != "engagement_unavailable"
                        else None
                    ),
                    "independence_key": evidence.get("independence_key") or evidence_id,
                }
            )
        support = relation_rows["support"]
        customer_support = [row for row in support if row["source_role"] in TRUTH_ROLES]
        support_roles = sorted({row["source_role"] for row in customer_support})
        origins = {
            (packet.get("source_bindings", {}).get("corpus_sha256"), row["independence_key"])
            for row in customer_support
        }
        material_support_ids = sorted(
            {
                row["evidence_id"]
                for row in customer_support
                if row["engagement_material_positive"] is True
            }
        )
        earning_reasons = []
        if proposition.get("claim_kind") == "reported_behavior":
            earning_reasons.append("reported_behavior")
        if len(origins) >= 2:
            earning_reasons.append("independent_customer_recurrence")
        if material_support_ids:
            earning_reasons.append("material_source_native_engagement")
        if proposition_id in protected_lookup:
            earning_reasons.append(f"protected:{protected_lookup[proposition_id]}")
        if not customer_support:
            nonpromoted.append(
                {
                    "proposition_id": proposition_id,
                    "disposition": "no_customer_truth_support_in_bound_packet",
                }
            )
            continue
        if not earning_reasons:
            nonpromoted.append(
                {
                    "proposition_id": proposition_id,
                    "disposition": "no_investigation_earning_signal",
                }
            )
            continue
        retailer_support = "retailer_review" in support_roles
        community_support = any(
            role in {"community_post", "audience_comment"} for role in support_roles
        )
        customer_counter_roles = sorted(
            {
                row["source_role"]
                for row in relation_rows["counter"]
                if row["source_role"] in TRUTH_ROLES
            }
        )
        row = {
            "proposition_id": proposition_id,
            "bounded_point": proposition.get("bounded_proposition"),
            "claim_kind": proposition.get("claim_kind"),
            "axis_ids": sorted(proposition.get("axis_ids") or []),
            "conditions": proposition.get("conditions") or [],
            "customer_support_roles": support_roles,
            "customer_counter_roles": customer_counter_roles,
            "independent_support_origin_count": len(origins),
            "material_support_evidence_ids": material_support_ids,
            "earning_reasons": earning_reasons,
            "relation_rows": relation_rows,
            "checkback": {
                "community": (
                    "support_observed"
                    if community_support
                    else "none_observed_in_bound_packet"
                    if available_truth_roles & {"community_post", "audience_comment"}
                    else "not_checkable_in_bound_packet"
                ),
                "retailer": (
                    "support_observed"
                    if retailer_support
                    else "none_observed_in_bound_packet"
                    if "retailer_review" in available_truth_roles
                    else "not_checkable_in_bound_packet"
                ),
            },
        }
        (retailer_queue if retailer_support else community_queue).append(row)

    retailer_queue.sort(key=_frontier_point_sort_key)
    community_queue.sort(key=_frontier_point_sort_key)
    nonpromoted.sort(key=lambda row: row["proposition_id"])
    frontier = {
        "schema_version": CUSTOMER_PULL_FRONTIER_VERSION,
        "frontier_id": frontier_id.strip(),
        "business_question": business_question.strip(),
        "source_id": source_id,
        "packet_sha256": packet["packet_sha256"],
        "subject_product_ids": sorted(set(subject_product_ids)),
        "protected_point_ids": protected,
        "customer_pull_policy": {
            "retailer_is_first_look_venue": True,
            "retailer_is_admission_gate": False,
            "engagement_is_compared_only_within_source_role_venue_and_metric": True,
            "creator_authored_is_customer_truth": False,
            "cross_platform_score": None,
        },
        "considered_proposition_ids": considered_ids,
        "subject_filtered_proposition_ids": subject_filtered_ids,
        "retailer_first_queue": retailer_queue,
        "community_discovery_queue": community_queue,
        "nonpromoted_points": nonpromoted,
        "accounting": {
            "input_proposition_count": len(selected_ids),
            "considered_proposition_count": len(considered_ids),
            "subject_filtered_count": len(subject_filtered_ids),
            "retailer_first_count": len(retailer_queue),
            "community_discovery_count": len(community_queue),
            "nonpromoted_count": len(nonpromoted),
        },
        "model_api_calls": 0,
    }
    frontier["frontier_sha256"] = _canonical_json_sha256(frontier)
    return frontier


def verify_customer_pull_point_frontier(
    frontier: Mapping[str, Any], packet: Mapping[str, Any]
) -> None:
    stored = frontier.get("frontier_sha256")
    payload = {key: value for key, value in frontier.items() if key != "frontier_sha256"}
    if (
        frontier.get("schema_version") != CUSTOMER_PULL_FRONTIER_VERSION
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_verification", "frontier content changed"
        )
    accounted = [
        row.get("proposition_id")
        for key in (
            "retailer_first_queue",
            "community_discovery_queue",
            "nonpromoted_points",
        )
        for row in frontier.get(key, [])
        if isinstance(row, Mapping)
    ]
    filtered = frontier.get("subject_filtered_proposition_ids") or []
    selected = packet.get("selection", {}).get("proposition_ids") or []
    accounting = frontier.get("accounting") or {}
    if (
        len(accounted) != len(set(accounted))
        or set(accounted) != set(frontier.get("considered_proposition_ids") or [])
        or not isinstance(filtered, list)
        or not all(isinstance(value, str) for value in filtered)
        or len(filtered) != len(set(filtered))
        or set(accounted) & set(filtered)
        or set(accounted) | set(filtered) != set(selected)
        or accounting.get("input_proposition_count") != len(selected)
        or accounting.get("considered_proposition_count") != len(accounted)
        or accounting.get("subject_filtered_count") != len(filtered)
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_accounting", "frontier point accounting is incomplete"
        )
    expected = build_customer_pull_point_frontier(
        packet,
        frontier_id=str(frontier.get("frontier_id", "")),
        business_question=str(frontier.get("business_question", "")),
        subject_product_ids=frontier.get("subject_product_ids") or [],
        source_id=str(frontier.get("source_id", "")),
        protected_point_ids=frontier.get("protected_point_ids") or {},
    )
    if dict(frontier) != expected:
        raise EvidenceConsumerError(
            "customer_pull_frontier_verification", "frontier does not rebuild"
        )


def selection_spec_from_customer_pull_frontier(
    frontier: Mapping[str, Any],
    packet: Mapping[str, Any],
    proposition_id: str,
    *,
    frontier_relation_rejections: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    verify_customer_pull_point_frontier(frontier, packet)
    matches = [
        (queue, row)
        for queue in ("retailer_first_queue", "community_discovery_queue")
        for row in frontier[queue]
        if row.get("proposition_id") == proposition_id
    ]
    if len(matches) != 1:
        raise EvidenceConsumerError(
            "customer_pull_frontier_point", "point is not an admitted frontier candidate"
        )
    queue, point = matches[0]
    admitted = [
        {"source_id": source_id, "semantic_unit_ref": semantic_ref}
        for source_id, semantic_ref in sorted(
            {
                (frontier["source_id"], semantic_ref)
            for relation in ("support", "counter", "adjacent")
            for relation_row in point["relation_rows"][relation]
            for semantic_ref in relation_row["semantic_unit_refs"]
            }
        )
    ]
    point_axis_ids = sorted(
        value for value in point.get("axis_ids", []) if isinstance(value, str)
    )
    expand_axis = bool(point_axis_ids) and VALUE_AXIS_ID not in point_axis_ids
    axis_ids = point_axis_ids if expand_axis else []
    candidate_admission = (
        "subject_axis_union_with_literal_refs"
        if expand_axis
        else "literal_point_relations"
    )
    normalized_rejections = _normalize_frontier_relation_rejections(
        frontier_relation_rejections,
        admitted_refs={(row["source_id"], row["semantic_unit_ref"]) for row in admitted},
    )
    if normalized_rejections:
        _validate_resolved_frontier_earning(
            packet,
            proposition_id,
            rejected_pairs={
                (row["source_id"], row["semantic_unit_ref"])
                for row in normalized_rejections
            },
            source_id=frontier["source_id"],
        )
    binding = {
        "frontier_sha256": frontier["frontier_sha256"],
        "packet_sha256": packet["packet_sha256"],
        "proposition_id": proposition_id,
        "queue": queue,
        "bounded_point_sha256": sha256_text(str(point["bounded_point"])),
        "admit_semantic_refs_sha256": _canonical_json_sha256(admitted),
        "axis_ids_sha256": _canonical_json_sha256(axis_ids),
        "candidate_admission": candidate_admission,
        "relation_response_mode": "positional" if expand_axis else "literal_ids",
        "temporal_presentation_policy": (
            "recent_year_coverage_v1" if expand_axis else None
        ),
        "frontier_relation_display_policy": FRONTIER_RELATION_DISPLAY_POLICY,
        "relation_policy": "bounded_point",
    }
    if normalized_rejections:
        binding["frontier_relation_rejections_sha256"] = _canonical_json_sha256(
            normalized_rejections
        )
    spec = {
        "schema_version": SELECTION_SPEC_VERSION,
        "selection_id": proposition_id,
        "bounded_claim": point["bounded_point"],
        "axis_ids": axis_ids,
        "subject_product_ids": frontier["subject_product_ids"],
        "admit_semantic_refs": admitted,
        "protected_evidence_ids": {},
        "truth_group_cap": MAX_TRUTH_GROUPS,
        "relation_response_mode": "positional" if expand_axis else "literal_ids",
        "relation_policy": "bounded_point",
        "frontier_relation_display_policy": FRONTIER_RELATION_DISPLAY_POLICY,
        "customer_pull_frontier_binding": binding,
    }
    if normalized_rejections:
        spec["frontier_relation_rejections"] = normalized_rejections
    if expand_axis:
        spec["temporal_presentation_policy"] = "recent_year_coverage_v1"
    return spec


def _normalize_frontier_relation_rejections(
    rows: Sequence[Mapping[str, Any]],
    *,
    admitted_refs: set[tuple[str, str]],
) -> list[dict[str, str]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise EvidenceConsumerError(
            "frontier_relation_resolution", "frontier relation rejections must be rows"
        )
    normalized: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "source_id",
            "semantic_unit_ref",
            "cause",
        }:
            raise EvidenceConsumerError(
                "frontier_relation_resolution", "frontier relation rejection shape changed"
            )
        source_id = row.get("source_id")
        semantic_ref = row.get("semantic_unit_ref")
        cause = row.get("cause")
        if (
            not isinstance(source_id, str)
            or not isinstance(semantic_ref, str)
            or cause not in FRONTIER_RELATION_REJECTION_CAUSES
            or (source_id, semantic_ref) not in admitted_refs
        ):
            raise EvidenceConsumerError(
                "frontier_relation_resolution",
                "frontier relation rejection is not an admitted literal relation",
            )
        normalized.append(
            {
                "source_id": source_id,
                "semantic_unit_ref": semantic_ref,
                "cause": cause,
            }
        )
    normalized.sort(key=lambda row: (row["source_id"], row["semantic_unit_ref"]))
    pairs = [(row["source_id"], row["semantic_unit_ref"]) for row in normalized]
    if len(pairs) != len(set(pairs)):
        raise EvidenceConsumerError(
            "frontier_relation_resolution", "frontier relation rejection is duplicated"
        )
    return normalized


def _validate_resolved_frontier_earning(
    packet: Mapping[str, Any],
    proposition_id: str,
    *,
    rejected_pairs: set[tuple[str, str]],
    source_id: str,
) -> None:
    propositions = {
        row.get("proposition_id"): row
        for row in packet.get("propositions", [])
        if isinstance(row, Mapping)
    }
    proposition = propositions.get(proposition_id)
    if not isinstance(proposition, Mapping):
        raise EvidenceConsumerError(
            "frontier_relation_resolution", "frontier proposition is absent"
        )
    evidence_index, _ = _expand_packet(packet)
    relation_rows = _relation_rows(packet, proposition_id)
    support_pairs = {
        (source_id, row["semantic_unit_ref"])
        for row in relation_rows
        if row["relation"] == "support"
    }
    if not rejected_pairs <= support_pairs:
        raise EvidenceConsumerError(
            "frontier_relation_resolution",
            "only a literal support relation can be rejected",
        )
    support_rows: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for relation_row in relation_rows:
        pair = (source_id, relation_row["semantic_unit_ref"])
        if relation_row["relation"] != "support" or pair in rejected_pairs:
            continue
        group, evidence = evidence_index[relation_row["evidence_id"]]
        if group.get("source_role") in TRUTH_ROLES:
            support_rows.append((group, evidence))
    origins = {
        (
            packet.get("source_bindings", {}).get("corpus_sha256"),
            evidence.get("independence_key") or evidence.get("evidence_id"),
        )
        for _, evidence in support_rows
    }
    materially_engaged = any(
        (evidence.get("engagement") or {}).get("status", "engagement_available")
        != "engagement_unavailable"
        and (evidence.get("engagement") or {}).get("material_positive") is True
        for _, evidence in support_rows
    )
    earned = (
        proposition.get("claim_kind") == "reported_behavior"
        or len(origins) >= 2
        or materially_engaged
    )
    if not support_rows or not earned:
        raise EvidenceConsumerError(
            "frontier_relation_resolution",
            "surviving literal relations no longer earn frontier admission",
        )


LEGACY_RELATION_PROMPT_COLUMNS = (
    "candidate_id",
    "normalized_meaning",
    "conditions",
    "polarity",
    "product_version_ids",
    "subject_product_ids",
    "source_role",
    "layer",
    "uncertainty_posture",
    "existing_relations",
    "same_evidence_companion_meanings",
)
RELATION_PROMPT_COLUMNS = LEGACY_RELATION_PROMPT_COLUMNS + ("parent_context_ids",)


def _project_parent_context(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[bool, list[dict[str, Any]], list[list[str]]]:
    context_aware = any(row.get("parent_context") for row in rows)
    if context_aware and not all("parent_context" in row for row in rows):
        raise EvidenceConsumerError(
            "parent_context_resolution", "candidate context projection is mixed-version"
        )
    contexts: dict[str, tuple[str, str]] = {}
    projected_rows: list[dict[str, Any]] = []
    for row in rows:
        projected = dict(row)
        parent_rows = projected.pop("parent_context", [])
        if context_aware:
            if not isinstance(parent_rows, list):
                raise EvidenceConsumerError(
                    "parent_context_resolution", "candidate parent context is malformed"
                )
            parent_ids = []
            for context in parent_rows:
                if (
                    not isinstance(context, Mapping)
                    or not isinstance(context.get("context_id"), str)
                    or not isinstance(context.get("source_ref"), str)
                    or not isinstance(context.get("text"), str)
                    or not context["text"]
                ):
                    raise EvidenceConsumerError(
                        "parent_context_resolution", "candidate parent context is malformed"
                    )
                context_id = context["context_id"]
                value = (context["source_ref"], context["text"])
                if context_id in contexts and contexts[context_id] != value:
                    raise EvidenceConsumerError(
                        "parent_context_resolution",
                        f"parent context identity carries divergent content: {context_id}",
                    )
                contexts[context_id] = value
                parent_ids.append(context_id)
            projected["parent_context_ids"] = parent_ids
        projected_rows.append(projected)
    context_rows = [
        [context_id, source_ref, text]
        for context_id, (source_ref, text) in sorted(contexts.items())
    ]
    return context_aware, projected_rows, context_rows


def _attach_parent_context_envelope(
    envelope: dict[str, Any], context_aware: bool, context_rows: list[list[str]]
) -> None:
    if context_aware:
        envelope["parent_context_columns"] = [
            "parent_context_id",
            "source_ref",
            "parent_text",
        ]
        envelope["parent_context_rows"] = context_rows


def _attach_point_parent_context_envelope(
    envelope: dict[str, Any], point_context_rows: Sequence[Sequence[str]]
) -> None:
    """Expose linked context for point scope without attaching it to every row."""

    if not point_context_rows:
        return
    normalized = [list(row) for row in point_context_rows]
    existing = envelope.get("parent_context_rows", [])
    by_id: dict[str, list[str]] = {}
    for row in [*existing, *normalized]:
        if (
            not isinstance(row, list)
            or len(row) != 3
            or not all(isinstance(value, str) for value in row)
        ):
            raise EvidenceConsumerError(
                "parent_context_resolution", "point parent context is malformed"
            )
        if row[0] in by_id and by_id[row[0]] != row:
            raise EvidenceConsumerError(
                "parent_context_resolution",
                f"parent context identity carries divergent content: {row[0]}",
            )
        by_id[row[0]] = row
    envelope["parent_context_columns"] = [
        "parent_context_id",
        "source_ref",
        "parent_text",
    ]
    envelope["parent_context_rows"] = [by_id[key] for key in sorted(by_id)]
    envelope["point_parent_context_ids"] = [row[0] for row in normalized]


def _compact_companion_meanings(row: Mapping[str, Any]) -> list[list[Any]]:
    return [
        [
            companion.get("statement"),
            companion.get("conditions", []),
            companion.get("polarity"),
            companion.get("axis_ids", []),
        ]
        for companion in row.get("same_evidence_companion_meanings", [])
    ]


def _relation_prompt_envelope(
    spec: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    *,
    batch_id: str | None = None,
) -> dict[str, Any]:
    context_aware, projected_candidates, context_rows = _project_parent_context(
        candidates
    )
    columns = (
        RELATION_PROMPT_COLUMNS if context_aware else LEGACY_RELATION_PROMPT_COLUMNS
    )
    rows = []
    for candidate in projected_candidates:
        projected = dict(candidate)
        projected["same_evidence_companion_meanings"] = _compact_companion_meanings(
            candidate
        )
        rows.append([projected.get(column) for column in columns])
    envelope = {
        "selection_id": spec["selection_id"],
        "bounded_claim": spec["bounded_claim"],
        "candidate_columns": list(columns),
        "candidate_rows": rows,
    }
    _attach_parent_context_envelope(envelope, context_aware, context_rows)
    if batch_id is not None:
        envelope["batch_id"] = batch_id
    return envelope


def _uses_value_policy(
    spec: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]] | None = None
) -> bool:
    relation_policy = spec.get("relation_policy", "auto")
    if relation_policy not in RELATION_POLICIES:
        raise EvidenceConsumerError(
            "selection_spec", f"unsupported relation_policy: {relation_policy}"
        )
    if relation_policy == "bounded_point":
        return False
    axis_ids = spec.get("axis_ids")
    if not isinstance(axis_ids, list):
        return False
    if set(axis_ids) == {VALUE_AXIS_ID}:
        return True
    if axis_ids or not candidates:
        return False
    return all(VALUE_AXIS_ID in set(row.get("axis_ids") or []) for row in candidates)


def _policy_guidance(
    spec: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]] | None = None
) -> str:
    if not _uses_value_policy(spec, candidates):
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


def _publication_time_value(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EvidenceConsumerError(
            "publication_time", "source publication time must be a non-empty ISO date/time"
        )
    normalized = value.strip()
    if normalized.casefold() in {"unknown", "unavailable", "not available"}:
        return None
    try:
        datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceConsumerError(
            "publication_time", f"source publication time is not ISO-shaped: {normalized}"
        ) from exc
    return normalized


def _publication_time_from_artifact(
    source: Mapping[str, Any],
    evidence_id: str,
    source_family: str,
    source_artifact_id: str | None,
    artifact_cache: dict[tuple[str, str], Mapping[str, Any] | None],
) -> str | None:
    if not source_artifact_id:
        return None
    cache_key = (str(source["source_id"]), source_artifact_id)
    if cache_key in artifact_cache:
        record = artifact_cache[cache_key]
        if record is None:
            return None
    else:
        record = None
        artifacts = source["bundle"].get("source_artifacts")
        if not isinstance(artifacts, list):
            artifact_cache[cache_key] = None
            return None
        binding = next(
            (
                row
                for row in artifacts
                if isinstance(row, Mapping) and row.get("artifact_id") == source_artifact_id
            ),
            None,
        )
        if binding is None or not isinstance(binding.get("locator"), str):
            artifact_cache[cache_key] = None
            return None
        path = Path(binding["locator"])
        if not path.is_absolute():
            bundle_path = source.get("bundle_path")
            if not isinstance(bundle_path, (str, Path)):
                artifact_cache[cache_key] = None
                return None
            path = Path(bundle_path).parent / path
        if not path.is_file():
            artifact_cache[cache_key] = None
            return None
        expected_hash = binding.get("sha256")
        if not isinstance(expected_hash, str) or hash_file(path) != expected_hash:
            raise EvidenceConsumerError(
                "publication_time_source_hash", f"source artifact changed: {source_artifact_id}"
            )
        try:
            loaded = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            artifact_cache[cache_key] = None
            return None
        if not isinstance(loaded, Mapping):
            artifact_cache[cache_key] = None
            return None
        record = loaded
        artifact_cache[cache_key] = record
    if source_family == "reddit_community":
        leaf_id = evidence_id.rsplit(":", 1)[-1]
        if leaf_id == "post":
            post = record.get("post")
            return _publication_time_value(
                post.get("timestamp_state") if isinstance(post, Mapping) else None
            )
        comments = record.get("comments")
        if isinstance(comments, list):
            for row in comments:
                if isinstance(row, Mapping) and str(row.get("comment_id")) == leaf_id:
                    return _publication_time_value(row.get("timestamp_state"))
        return None
    if source_family != "retailer_review":
        return None
    review_id = evidence_id.rsplit(":", 1)[-1]
    results = record.get("Results")
    if isinstance(results, list):
        for row in results:
            if isinstance(row, Mapping) and str(row.get("Id")) == review_id:
                return _publication_time_value(row.get("SubmissionTime"))
    rows = record.get("rows")
    if isinstance(rows, list):
        for row in rows:
            fields = row.get("source_visible_fields") if isinstance(row, Mapping) else None
            if isinstance(fields, Mapping) and str(fields.get("review_id")) == review_id:
                return _publication_time_value(fields.get("source_date"))
    responses = record.get("responses")
    if isinstance(responses, list):
        for response in responses:
            if not isinstance(response, Mapping) or not isinstance(response.get("body_text"), str):
                continue
            try:
                body = json.loads(response["body_text"])
            except json.JSONDecodeError as exc:
                raise EvidenceConsumerError(
                    "publication_time_source", "retailer response body is invalid JSON"
                ) from exc
            for row in body.get("reviews", []) if isinstance(body, Mapping) else []:
                if isinstance(row, Mapping) and str(row.get("id")) == review_id:
                    return _publication_time_value(row.get("createdAt"))
    return None


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


def _parent_context_indexes(
    bundle: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    units = bundle.get("evidence_units")
    if not isinstance(units, list):
        raise EvidenceConsumerError("bundle_verification", "bundle evidence_units missing")
    unit_index = {
        row["evidence_id"]: row
        for row in units
        if isinstance(row, Mapping) and isinstance(row.get("evidence_id"), str)
    }
    projection = bundle.get("semantic_work_unit_projection")
    registry_rows = (
        projection.get("context_registry", [])
        if isinstance(projection, Mapping)
        else []
    )
    if not isinstance(registry_rows, list):
        raise EvidenceConsumerError(
            "parent_context_resolution", "bundle context registry is malformed"
        )
    registry: dict[str, Mapping[str, Any]] = {}
    for row in registry_rows:
        context_id = row.get("context_id") if isinstance(row, Mapping) else None
        if not isinstance(context_id, str) or context_id in registry:
            raise EvidenceConsumerError(
                "parent_context_resolution", "bundle context identity is malformed"
            )
        registry[context_id] = row
    return unit_index, registry


def _resolved_parent_context(
    *,
    source_id: str,
    evidence: Mapping[str, Any],
    bundle_unit: Mapping[str, Any] | None,
    context_registry: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    if bundle_unit is None:
        return []
    references = bundle_unit.get("parent_context_refs")
    inline_rows = bundle_unit.get("parent_context")
    if references is not None and inline_rows is not None:
        raise EvidenceConsumerError(
            "parent_context_resolution",
            f"evidence {evidence.get('evidence_id')} carries two parent-context shapes",
        )
    resolved: list[dict[str, str]] = []
    if references is not None:
        if (
            not isinstance(references, list)
            or not all(isinstance(ref, str) and ref for ref in references)
            or len(references) != len(set(references))
        ):
            raise EvidenceConsumerError(
                "parent_context_resolution", "parent context references are malformed"
            )
        for ref in references:
            context = context_registry.get(ref)
            if context is None:
                raise EvidenceConsumerError(
                    "parent_context_resolution", f"unknown parent context: {ref}"
                )
            if (
                context.get("context_type") != "parent_text"
                or context.get("source_artifact_id")
                != evidence.get("source_artifact_id")
                or not isinstance(context.get("source_ref"), str)
                or not isinstance(context.get("text"), str)
                or not context["text"]
            ):
                raise EvidenceConsumerError(
                    "parent_context_resolution", f"invalid parent context: {ref}"
                )
            resolved.append(
                {
                    "context_id": f"{source_id}::{ref}",
                    "source_ref": context["source_ref"],
                    "text": context["text"],
                }
            )
        return resolved
    if inline_rows is None:
        return []
    if not isinstance(inline_rows, list):
        raise EvidenceConsumerError(
            "parent_context_resolution", "inline parent context is malformed"
        )
    for row in inline_rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("source_ref"), str)
            or not isinstance(row.get("text"), str)
            or not row["text"]
        ):
            raise EvidenceConsumerError(
                "parent_context_resolution", "inline parent context is malformed"
            )
        identity = _canonical_json_sha256(
            {"source_ref": row["source_ref"], "text": row["text"]}
        )
        resolved.append(
            {
                "context_id": f"{source_id}::inline::{identity}",
                "source_ref": row["source_ref"],
                "text": row["text"],
            }
        )
    if len({row["context_id"] for row in resolved}) != len(resolved):
        raise EvidenceConsumerError(
            "parent_context_resolution", "inline parent context is duplicated"
        )
    return resolved


def _candidate_rows(
    sources: Sequence[Mapping[str, Any]],
    spec: Mapping[str, Any],
    *,
    include_parent_context: bool = True,
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
    publication_time_cache: dict[tuple[str, str], str | None] = {}
    publication_artifact_cache: dict[
        tuple[str, str], Mapping[str, Any] | None
    ] = {}

    def resolved_publication_time(
        source: Mapping[str, Any],
        evidence_id: str,
        group: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> str | None:
        stored = _publication_time_value(evidence.get("publication_time"))
        if stored is not None:
            return stored
        key = (str(source["source_id"]), evidence_id)
        if key not in publication_time_cache:
            publication_time_cache[key] = _publication_time_from_artifact(
                source,
                evidence_id,
                str(group["source_family"]),
                evidence.get("source_artifact_id"),
                publication_artifact_cache,
            )
        return publication_time_cache[key]

    for source in sources:
        source_id = source["source_id"]
        packet = source["packet"]
        bundle_unit_index, context_registry = _parent_context_indexes(source["bundle"])
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
                    "publication_time": resolved_publication_time(
                        source, evidence_id, group, evidence
                    ),
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
                if include_parent_context:
                    candidate["parent_context"] = (
                        _resolved_parent_context(
                            source_id=source_id,
                            evidence={**evidence, "evidence_id": evidence_id},
                            bundle_unit=bundle_unit_index.get(evidence_id),
                            context_registry=context_registry,
                        )
                        if explicitly_admitted
                        else []
                    )
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
                    "publication_time": resolved_publication_time(
                        source, evidence_id, group, evidence
                    ),
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
                    **(
                        {
                            "parent_context": _resolved_parent_context(
                                source_id=source_id,
                                evidence={**evidence, "evidence_id": evidence_id},
                                bundle_unit=bundle_unit_index.get(evidence_id),
                                context_registry=context_registry,
                            )
                        }
                        if include_parent_context
                        else {}
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


def _relation_schema(
    *,
    value_policy: bool = False,
    response_mode: str = "literal_ids",
    candidate_count: int | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    positional = response_mode == "positional"
    if batch_id is not None and not positional:
        raise ValueError("only a positional relation schema can bind a batch id")
    if positional:
        if candidate_count is None or candidate_count < 1:
            raise ValueError("positional relation schema needs a candidate count")
        row_keys = [f"row_{index:04d}" for index in range(candidate_count)]
        positional_relations = {
            "type": "object",
            "properties": {
                key: {"type": "string", "enum": list(RELATIONS)} for key in row_keys
            },
            "required": row_keys,
            "additionalProperties": False,
        }
        properties: dict[str, Any] = {"results_by_candidate_row": positional_relations}
        required = ["results_by_candidate_row"]
        if batch_id is not None:
            # Row keys restart at row_0000 in every batch, so two same-size
            # batches would otherwise share one byte-identical schema and one
            # interchangeable response.  A single-value batch_id makes each
            # response answerable by exactly one batch.
            properties["batch_id"] = {"type": "string", "enum": [batch_id]}
            required.append("batch_id")
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def result_row(relation: str | None = None) -> dict[str, Any]:
        relation_schema: dict[str, Any] = {"type": "string"}
        reason_schema: dict[str, Any] = {
            "type": "string",
            "pattern": REASON_CODE_RE.pattern,
        }
        if relation is None:
            relation_schema["enum"] = list(RELATIONS)
        else:
            relation_schema["const"] = relation
            reason_schema.pop("pattern")
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


def _quote_has_complete_end(body: str, quote: str) -> bool:
    """Return whether at least one exact occurrence avoids a mid-phrase stop."""

    effective_quote = quote.rstrip()
    if not effective_quote or not effective_quote[-1].isalnum():
        return True

    search_from = 0
    while True:
        occurrence = body.find(quote, search_from)
        if occurrence < 0:
            return False
        suffix_index = occurrence + len(quote)
        while suffix_index < len(body) and body[suffix_index].isspace():
            suffix_index += 1
        if suffix_index >= len(body) or not body[suffix_index].isalnum():
            return True
        search_from = occurrence + 1


def _quote_schema() -> dict[str, Any]:
    row = {
        "type": "object",
        "properties": {
            "selected_id": {"type": "string"},
            "quote_status": {
                "type": "string",
                "enum": ["quote_available", "quote_unavailable"],
            },
            "exact_quote": {
                "type": ["string", "null"],
                "maxLength": MAX_QUOTE_CHARACTERS,
            },
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


def _relation_confirmation_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "point_scope": {
                "type": "string",
                "enum": list(POINT_SCOPE_STATUSES),
            },
            "point_scope_reason": {"type": "string", "minLength": 1},
            "relation_checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "confirmation_row_id": {"type": "string"},
                        "relation": {"type": "string", "enum": list(RELATIONS)},
                    },
                    "required": ["confirmation_row_id", "relation"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["point_scope", "point_scope_reason", "relation_checks"],
        "additionalProperties": False,
    }


def _validate_customer_pull_frontier_spec_binding(
    spec: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]
) -> None:
    binding = spec.get("customer_pull_frontier_binding")
    if binding is None:
        return
    legacy_keys = {
        "frontier_sha256",
        "packet_sha256",
        "proposition_id",
        "queue",
        "bounded_point_sha256",
        "admit_semantic_refs_sha256",
        "relation_policy",
    }
    expanded_keys = legacy_keys | {
        "axis_ids_sha256",
        "candidate_admission",
        "relation_response_mode",
        "temporal_presentation_policy",
    }
    current_keys = expanded_keys | {"frontier_relation_display_policy"}
    resolved_keys = current_keys | {"frontier_relation_rejections_sha256"}
    binding_keys = frozenset(binding) if isinstance(binding, Mapping) else frozenset()
    if not isinstance(binding, Mapping) or binding_keys not in {
        frozenset(legacy_keys),
        frozenset(expanded_keys),
        frozenset(current_keys),
        frozenset(resolved_keys),
    }:
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier binding shape changed"
        )
    if binding_keys == frozenset(legacy_keys) and spec.get("axis_ids"):
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding",
            "legacy frontier binding cannot authorize axis-wide admission",
        )
    if binding_keys in {
        frozenset(expanded_keys),
        frozenset(current_keys),
        frozenset(resolved_keys),
    } and (
        binding.get("axis_ids_sha256")
        != _canonical_json_sha256(spec.get("axis_ids") or [])
        or binding.get("candidate_admission")
        not in {"literal_point_relations", "subject_axis_union_with_literal_refs"}
        or binding.get("relation_response_mode")
        != spec.get("relation_response_mode", "literal_ids")
        or binding.get("temporal_presentation_policy")
        != spec.get("temporal_presentation_policy")
        or (
            binding.get("candidate_admission") == "literal_point_relations"
            and spec.get("axis_ids")
        )
        or (
            binding.get("candidate_admission")
            == "subject_axis_union_with_literal_refs"
            and not spec.get("axis_ids")
        )
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier candidate admission changed"
        )
    if binding_keys in {frozenset(current_keys), frozenset(resolved_keys)}:
        if (
            binding.get("frontier_relation_display_policy")
            != spec.get("frontier_relation_display_policy")
            or spec.get("frontier_relation_display_policy")
            != FRONTIER_RELATION_DISPLAY_POLICY
        ):
            raise EvidenceConsumerError(
                "customer_pull_frontier_binding", "frontier candidate admission changed"
            )
    elif spec.get("frontier_relation_display_policy") is not None:
        # A pre-policy binding pins every other display-affecting spec field.
        # Leaving this one unpinned would let a frozen frontier-bound spec turn
        # quiet-row display on without its binding authorizing the change.
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier candidate admission changed"
        )
    if binding_keys == frozenset(resolved_keys):
        rejections = _normalize_frontier_relation_rejections(
            spec.get("frontier_relation_rejections"),
            admitted_refs={
                (row["source_id"], row["semantic_unit_ref"])
                for row in spec.get("admit_semantic_refs") or []
                if isinstance(row, Mapping)
                and isinstance(row.get("source_id"), str)
                and isinstance(row.get("semantic_unit_ref"), str)
            },
        )
        if (
            not rejections
            or binding.get("frontier_relation_rejections_sha256")
            != _canonical_json_sha256(rejections)
        ):
            raise EvidenceConsumerError(
                "customer_pull_frontier_binding",
                "frontier relation resolution changed",
            )
        packet = next(
            (
                source["packet"]
                for source in sources
                if source["packet"].get("packet_sha256") == binding.get("packet_sha256")
            ),
            None,
        )
        if packet is None:
            raise EvidenceConsumerError(
                "customer_pull_frontier_binding",
                "frontier packet is not among the sources",
            )
        _validate_resolved_frontier_earning(
            packet,
            str(binding.get("proposition_id")),
            rejected_pairs={
                (row["source_id"], row["semantic_unit_ref"])
                for row in rejections
            },
            source_id=rejections[0]["source_id"],
        )
    elif spec.get("frontier_relation_rejections") is not None:
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier relation resolution is unbound"
        )
    if (
        binding.get("queue")
        not in {"retailer_first_queue", "community_discovery_queue"}
        or binding.get("proposition_id") != spec.get("selection_id")
        or binding.get("relation_policy") != spec.get("relation_policy")
        or binding.get("bounded_point_sha256")
        != sha256_text(str(spec.get("bounded_claim", "")))
        or binding.get("admit_semantic_refs_sha256")
        != _canonical_json_sha256(spec.get("admit_semantic_refs") or [])
        or not isinstance(binding.get("frontier_sha256"), str)
    ):
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier-bound point spec changed"
        )
    packet_hashes = {source["packet"].get("packet_sha256") for source in sources}
    if binding.get("packet_sha256") not in packet_hashes:
        raise EvidenceConsumerError(
            "customer_pull_frontier_binding", "frontier packet is not among the sources"
        )


def _temporal_presentation_policy(spec: Mapping[str, Any]) -> str | None:
    policy = spec.get("temporal_presentation_policy")
    if policy is None:
        return None
    if not isinstance(policy, str) or policy not in TEMPORAL_PRESENTATION_POLICIES:
        raise EvidenceConsumerError(
            "selection_spec",
            f"temporal_presentation_policy must be one of {TEMPORAL_PRESENTATION_POLICIES}",
        )
    return policy


def prepare_evidence_selection(
    spec: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if spec.get("schema_version") != SELECTION_SPEC_VERSION:
        raise EvidenceConsumerError("selection_spec", "unsupported selection spec")
    if not isinstance(spec.get("selection_id"), str) or not spec["selection_id"]:
        raise EvidenceConsumerError("selection_spec", "selection_id missing")
    if not isinstance(spec.get("bounded_claim"), str) or not spec["bounded_claim"].strip():
        raise EvidenceConsumerError("selection_spec", "bounded_claim missing")
    _truth_group_cap(spec)
    temporal_policy = _temporal_presentation_policy(spec)
    response_mode = _relation_response_mode(spec)
    for source in sources:
        _verify_packet(source["packet"])
        bundle = source["bundle"]
        packet_bundle = source["packet"].get("source_bindings", {}).get("bundle_sha256")
        if bundle.get("bundle_sha256") != packet_bundle:
            raise EvidenceConsumerError("bundle_verification", "packet/bundle hash mismatch")
        _verify_bundle(bundle)
    _validate_customer_pull_frontier_spec_binding(spec, sources)
    candidates = _candidate_rows(sources, spec)
    value_policy = _uses_value_policy(spec, candidates)
    if value_policy and temporal_policy is not None:
        raise EvidenceConsumerError(
            "selection_spec",
            "temporal presentation is supported only for non-value selections",
        )
    if value_policy and response_mode == "positional":
        raise EvidenceConsumerError(
            "selection_spec",
            "positional relation responses are supported only for non-value selections",
        )
    if value_policy:
        context_aware, projected_candidates, context_rows = _project_parent_context(
            candidates
        )
        envelope = {
            "selection_id": spec["selection_id"],
            "bounded_claim": spec["bounded_claim"],
            "candidates": projected_candidates,
        }
        _attach_parent_context_envelope(envelope, context_aware, context_rows)
    else:
        envelope = _relation_prompt_envelope(spec, candidates)
    prompt = RELATION_PROMPT.format(
        response_instruction=(
            POSITIONAL_RELATION_RESPONSE_INSTRUCTION
            if response_mode == "positional"
            else LITERAL_RELATION_RESPONSE_INSTRUCTION
        ),
        reason_instruction=(
            ""
            if response_mode == "positional"
            else " Supply one short lowercase snake_case reason_code that names the evidence meaning without repeating those internal relation words."
        ),
        relation_definitions=(
            BOUNDED_POINT_RELATION_DEFINITIONS
            if spec.get("relation_policy") == "bounded_point"
            else ""
        ),
        policy_guidance=_policy_guidance(spec, candidates),
        envelope=_compact(envelope),
    )
    schema = _relation_schema(
        value_policy=value_policy,
        response_mode=response_mode,
        candidate_count=len(candidates),
    )
    inventory_sha = _canonical_json_sha256(candidates)
    manifest = {
        "schema_version": SELECTION_MANIFEST_VERSION,
        "selection_id": spec["selection_id"],
        "spec": dict(spec),
        "candidate_count": len(candidates),
        "candidate_inventory_sha256": inventory_sha,
        "parent_context_policy": PARENT_CONTEXT_POLICY,
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


def prepare_evidence_selection_batches(
    spec: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    *,
    batch_size: int,
) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    if (
        isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or batch_size < 1
        or batch_size > MAX_RELATION_BATCH_SIZE
    ):
        raise EvidenceConsumerError(
            "selection_spec",
            f"relation batch size must be an integer from 1 to {MAX_RELATION_BATCH_SIZE}",
        )
    if _relation_response_mode(spec) != "positional":
        raise EvidenceConsumerError(
            "selection_spec", "relation batching requires positional response mode"
        )
    _, _, selection_manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    value_policy = _uses_value_policy(spec, candidates)
    if value_policy:
        raise EvidenceConsumerError(
            "selection_spec", "relation batching is supported only for non-value selections"
        )
    prompts_and_schemas: list[tuple[str, dict[str, Any]]] = []
    batches = []
    # Policy guidance is a property of the whole selection, not of whichever
    # rows land in one batch: deriving it per subset would let a batch that
    # happens to hold only value-axis rows carry value-box guidance the run as
    # a whole rejected.
    policy_guidance = _policy_guidance(spec, candidates)
    for batch_index, start in enumerate(range(0, len(candidates), batch_size), start=1):
        subset = candidates[start : start + batch_size]
        batch_id = f"batch_{batch_index:04d}"
        envelope = _relation_prompt_envelope(spec, subset, batch_id=batch_id)
        prompt = RELATION_PROMPT.format(
            response_instruction=BATCHED_RELATION_RESPONSE_INSTRUCTION,
            reason_instruction="",
            relation_definitions=(
                BOUNDED_POINT_RELATION_DEFINITIONS
                if spec.get("relation_policy") == "bounded_point"
                else ""
            ),
            policy_guidance=policy_guidance,
            envelope=_compact(envelope),
        )
        schema = _relation_schema(
            value_policy=False,
            response_mode="positional",
            candidate_count=len(subset),
            batch_id=batch_id,
        )
        batches.append(
            {
                "batch_id": batch_id,
                "start_index": start,
                "candidate_count": len(subset),
                "candidate_ids_sha256": _canonical_json_sha256(
                    [row["candidate_id"] for row in subset]
                ),
                "prompt_sha256": sha256_text(prompt),
                "response_schema_sha256": _canonical_json_sha256(schema),
            }
        )
        prompts_and_schemas.append((prompt, schema))
    batch_manifest = {
        "schema_version": SELECTION_BATCH_MANIFEST_VERSION,
        "selection_manifest": selection_manifest,
        "selection_manifest_sha256": selection_manifest["manifest_sha256"],
        "candidate_inventory_sha256": selection_manifest[
            "candidate_inventory_sha256"
        ],
        "candidate_count": len(candidates),
        "batch_size": batch_size,
        "batches": batches,
        "model_api_calls": 0,
    }
    batch_manifest["manifest_sha256"] = _canonical_json_sha256(batch_manifest)
    return batch_manifest, prompts_and_schemas


def validate_evidence_selection_batch_response(
    batch_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    *,
    batch_id: str,
    response: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one immutable provider attempt before canonical publication."""

    stored = batch_manifest.get("manifest_sha256")
    payload = {
        key: value for key, value in batch_manifest.items() if key != "manifest_sha256"
    }
    if (
        batch_manifest.get("schema_version") != SELECTION_BATCH_MANIFEST_VERSION
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection batch manifest changed"
        )
    selection_manifest = batch_manifest.get("selection_manifest")
    if (
        not isinstance(selection_manifest, Mapping)
        or selection_manifest.get("manifest_sha256")
        != batch_manifest.get("selection_manifest_sha256")
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection manifest binding changed"
        )
    candidates = _candidate_rows_for_manifest(sources, selection_manifest)
    if (
        len(candidates) != batch_manifest.get("candidate_count")
        or _canonical_json_sha256(candidates)
        != batch_manifest.get("candidate_inventory_sha256")
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "batched candidate inventory changed"
        )
    batches = batch_manifest.get("batches")
    if not isinstance(batches, list):
        raise EvidenceConsumerError(
            "manifest_verification", "selection batches missing"
        )
    matches = [
        batch
        for batch in batches
        if isinstance(batch, Mapping) and batch.get("batch_id") == batch_id
    ]
    if len(matches) != 1:
        raise EvidenceConsumerError(
            "relation_batch_identity", "requested relation batch is not unique"
        )
    batch = matches[0]
    start = batch.get("start_index")
    count = batch.get("candidate_count")
    if (
        not isinstance(start, int)
        or start < 0
        or not isinstance(count, int)
        or count < 1
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "relation batch coverage changed"
        )
    subset = candidates[start : start + count]
    if (
        len(subset) != count
        or _canonical_json_sha256([row["candidate_id"] for row in subset])
        != batch.get("candidate_ids_sha256")
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "relation batch membership changed"
        )
    validated = _validate_relation_response(
        subset,
        response,
        value_policy=False,
        response_mode="positional",
        batch_id=batch_id,
    )
    return {
        "batch_id": batch_id,
        "candidate_count": len(validated),
        "batch_manifest_sha256": stored,
        "response_sha256": _canonical_json_sha256(response),
    }


def _truth_group_cap(spec: Mapping[str, Any]) -> int:
    cap = spec.get("truth_group_cap", MAX_TRUTH_GROUPS)
    if (
        isinstance(cap, bool)
        or not isinstance(cap, int)
        or cap < 1
        or cap > MAX_CONFIGURABLE_TRUTH_GROUPS
    ):
        raise EvidenceConsumerError(
            "selection_spec",
            f"truth_group_cap must be an integer from 1 to {MAX_CONFIGURABLE_TRUTH_GROUPS}",
        )
    return cap


def _relation_response_mode(spec: Mapping[str, Any]) -> str:
    mode = spec.get("relation_response_mode", "literal_ids")
    if not isinstance(mode, str) or mode not in RELATION_RESPONSE_MODES:
        raise EvidenceConsumerError(
            "selection_spec",
            f"relation_response_mode must be one of {RELATION_RESPONSE_MODES}",
        )
    return mode


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
    candidates = _candidate_rows_for_manifest(sources, manifest)
    if _canonical_json_sha256(candidates) != manifest.get("candidate_inventory_sha256"):
        raise EvidenceConsumerError("manifest_verification", "candidate inventory changed")
    return sources


def _candidate_rows_for_manifest(
    sources: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any]
) -> list[dict[str, Any]]:
    policy = manifest.get("parent_context_policy")
    if policy not in {None, PARENT_CONTEXT_POLICY}:
        raise EvidenceConsumerError(
            "manifest_verification", "unsupported parent-context policy"
        )
    return _candidate_rows(
        sources,
        manifest["spec"],
        include_parent_context=policy == PARENT_CONTEXT_POLICY,
    )


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


def _publication_year(row: Mapping[str, Any]) -> int | None:
    """Derive the calendar year from an already-admitted publication time.

    ``_publication_time_value`` admits every ISO-8601 shape ``fromisoformat``
    parses, including basic format such as ``20260601T000000+00:00``.  Reading
    the year back through a narrower text pattern would silently reclassify a
    dated row as undated, so reuse the parse that admitted the value.
    """
    value = row.get("publication_time")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).year
    except ValueError:
        return None


def _temporal_display_priority(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Order one already-comparable source group under the recency preference.

    Engagement is compared only inside one calendar year and one native metric
    kind, never across platforms.  An unavailable value orders last on its own
    rank because missing engagement is not zero engagement: a reported negative
    source-native score must not sort below a row that reported none.
    """
    numeric = _numeric_engagement(
        row["engagement_raw_value"], row["engagement_kind"]
    )
    return (
        -(_publication_year(row) or 0),
        0 if numeric is not None else 1,
        row["engagement_kind"],
        -numeric if numeric is not None else 0.0,
        row["selected_id"],
    )


def _display_members(
    members: Sequence[Mapping[str, Any]], *, priority: Any = _global_priority
) -> list[dict[str, Any]]:
    ordered = sorted((dict(row) for row in members), key=priority)
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

    Operator-protected and frontier-defining candidates are mandatory rows.
    At most four ordinary lane requirements remain, so exhaustive combinations
    over one representative per distinct coverage signature are bounded and
    prove minimal cardinality.
    """
    ordered = sorted((dict(row) for row in members), key=priority)
    by_id = {row["candidate_id"]: row for row in ordered}
    try:
        forced = [by_id[candidate_id] for candidate_id in required_candidate_ids]
    except KeyError as exc:
        raise EvidenceConsumerError(
            "required_display_lane_unavailable",
            f"required candidate is absent from its origin: {exc.args[0]}",
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


def _truth_row_display_eligible(
    row: Mapping[str, Any],
    truth_policy: str,
    *,
    frontier_relation_bound: bool = False,
) -> bool:
    """Apply the exact pre-cap admission rule for one truth-support row."""
    if truth_policy not in {"balanced", "value_first"}:
        raise EvidenceConsumerError(
            "selection_policy", f"unsupported policy: {truth_policy}"
        )
    if row.get("layer") != "truth_support" or row.get("relation") == "exclude":
        return False
    if row.get("protected_lanes"):
        return True
    if frontier_relation_bound:
        return True
    if row.get("engagement_material_positive") is not True:
        return False
    return truth_policy == "balanced" or row.get("relation") in {
        "support",
        "counter",
    }


def _frontier_relation_candidate_ids(
    spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> frozenset[str]:
    policy = spec.get("frontier_relation_display_policy")
    if policy is None:
        return frozenset()
    if policy != FRONTIER_RELATION_DISPLAY_POLICY:
        raise EvidenceConsumerError(
            "selection_spec", "unsupported frontier relation display policy"
        )
    admitted_refs = {
        (row["source_id"], row["semantic_unit_ref"])
        for row in spec.get("admit_semantic_refs") or []
    }
    rejected_refs = {
        (row["source_id"], row["semantic_unit_ref"])
        for row in _normalize_frontier_relation_rejections(
            spec.get("frontier_relation_rejections") or [],
            admitted_refs=admitted_refs,
        )
    }
    return frozenset(
        row["candidate_id"]
        for row in rows
        if (row["source_id"], row["semantic_unit_ref"]) in admitted_refs
        and (row["source_id"], row["semantic_unit_ref"]) not in rejected_refs
    )


def _apply_frontier_relation_rejections(
    spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    admitted_refs = {
        (row["source_id"], row["semantic_unit_ref"])
        for row in spec.get("admit_semantic_refs") or []
    }
    rejected_refs = {
        (row["source_id"], row["semantic_unit_ref"])
        for row in _normalize_frontier_relation_rejections(
            spec.get("frontier_relation_rejections") or [],
            admitted_refs=admitted_refs,
        )
    }
    resolved = []
    for source_row in rows:
        row = dict(source_row)
        if (row["source_id"], row["semantic_unit_ref"]) in rejected_refs:
            row["relation"] = "exclude"
            row["reason_code"] = "literal_source_does_not_state_bounded_relation"
        resolved.append(row)
    return resolved


def _preselection_relation_confirmation_schema(
    *, value_policy: bool, batch_id: str | None = None
) -> dict[str, Any]:
    def check_row(relation: str | None = None) -> dict[str, Any]:
        relation_schema: dict[str, Any] = {"type": "string"}
        reason_schema: dict[str, Any] = {
            "type": "string",
            "pattern": REASON_CODE_RE.pattern,
        }
        if relation is None:
            relation_schema["enum"] = list(RELATIONS)
        else:
            relation_schema["const"] = relation
            reason_schema = {
                "type": "string",
                "enum": sorted(
                    code
                    for code, expected_relation in VALUE_REASON_RELATIONS.items()
                    if expected_relation == relation
                ),
            }
        return {
            "type": "object",
            "properties": {
                "confirmation_row_id": {"type": "string"},
                "relation": relation_schema,
                "reason_code": reason_schema,
            },
            "required": ["confirmation_row_id", "relation", "reason_code"],
            "additionalProperties": False,
        }

    row = (
        {"anyOf": [check_row(relation) for relation in RELATIONS]}
        if value_policy
        else check_row()
    )
    properties = {
        "point_scope": {"type": "string", "enum": list(POINT_SCOPE_STATUSES)},
        "point_scope_reason": {"type": "string", "minLength": 1},
        "relation_checks": {"type": "array", "items": row},
    }
    required = ["point_scope", "point_scope_reason", "relation_checks"]
    if batch_id is not None:
        properties["batch_id"] = {"type": "string", "const": batch_id}
        required.append("batch_id")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _select_value_groups(
    rows: Sequence[Mapping[str, Any]],
    cap: int,
    *,
    frontier_relation_candidate_ids: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    _validate_protected_rows(rows)
    eligible = [
        dict(row)
        for row in rows
        if _truth_row_display_eligible(
            row,
            "value_first",
            frontier_relation_bound=row["candidate_id"]
            in frontier_relation_candidate_ids,
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
                    row["candidate_id"]
                    for row in members
                    if row.get("protected_lanes")
                    or row["candidate_id"] in frontier_relation_candidate_ids
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

    # These rows supplied the literal relations that admitted the point. They
    # must survive the origin cap so their wording is displayed and enters the
    # exact-quote relevance check. If the complete frontier itself exceeds the
    # cap, fail visibly instead of completing from an unchecked subset.
    for group in sorted(
        (
            row
            for row in groups
            if frontier_relation_candidate_ids
            & set(row["origin_candidate_ids"])
        ),
        key=_value_member_priority,
    ):
        add_group(group)

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
    frontier_candidate_ids = {
        row["candidate_id"]
        for row in eligible
        if row["candidate_id"] in frontier_relation_candidate_ids
    }
    if not frontier_candidate_ids <= displayed_candidate_ids:
        raise EvidenceConsumerError(
            "frontier_candidate_not_visible",
            "one or more frontier-defining candidates are absent from the display",
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
    temporal_policy: str | None = None,
    frontier_relation_candidate_ids: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    if truth_policy not in {"balanced", "value_first"}:
        raise EvidenceConsumerError("selection_policy", f"unsupported policy: {truth_policy}")
    if truth_policy == "value_first" and layer == "truth_support":
        return _select_value_groups(
            rows,
            cap,
            frontier_relation_candidate_ids=frontier_relation_candidate_ids,
        )
    if temporal_policy is not None and temporal_policy not in TEMPORAL_PRESENTATION_POLICIES:
        raise EvidenceConsumerError(
            "selection_policy", f"unsupported temporal policy: {temporal_policy}"
        )
    _validate_protected_rows(rows)
    eligible = [
        dict(row)
        for row in rows
        if row["layer"] == layer
        and row["relation"] != "exclude"
        and (
            layer != "truth_support"
            or _truth_row_display_eligible(
                row,
                truth_policy,
                frontier_relation_bound=row["candidate_id"]
                in frontier_relation_candidate_ids,
            )
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
                "origin_publication_years": sorted(
                    {
                        year
                        for row in members
                        if (year := _publication_year(row)) is not None
                    }
                ),
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
                    row["candidate_id"]
                    for row in members
                    if row.get("protected_lanes")
                    or row["candidate_id"] in frontier_relation_candidate_ids
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
        if temporal_policy is not None:
            priority = lambda row: (
                row["source_role"],
                row["source_venue"],
                row["engagement_kind"],
                _bucket_priority(row),
            )
        else:
            priority = _global_priority
        choice = sorted(already_selected or eligible_groups, key=priority)[0]
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
        for group in sorted(
            (
                row
                for row in groups
                if frontier_relation_candidate_ids
                & set(row["origin_candidate_ids"])
            ),
            key=_global_priority,
        ):
            add_group(group)
        reserve_lane("relation:support", lambda row: "support" in row["origin_relations"])
        reserve_lane("relation:counter", lambda row: "counter" in row["origin_relations"])

        if temporal_policy == "recent_year_coverage_v1" and len(selected) < cap:
            observed_years = sorted(
                {
                    year
                    for group in groups
                    for year in group["origin_publication_years"]
                },
                reverse=True,
            )
            recent_years = observed_years[:RECENT_YEAR_COUNT]
            temporal_buckets: dict[
                tuple[int, str, str, str], list[dict[str, Any]]
            ] = defaultdict(list)
            for group in groups:
                years = group["origin_publication_years"]
                latest_year = max(years) if years else None
                if latest_year in recent_years:
                    temporal_buckets[
                        (
                            latest_year,
                            group["source_role"],
                            group["source_venue"],
                            group["engagement_kind"],
                        )
                    ].append(group)
            for bucket in temporal_buckets.values():
                bucket.sort(key=_bucket_priority)
            covered_recent_keys = {
                (
                    max(group["origin_publication_years"]),
                    group["source_role"],
                    group["source_venue"],
                    group["engagement_kind"],
                )
                for group in selected
                if group["origin_publication_years"]
                and max(group["origin_publication_years"]) in recent_years
            }
            recent_target = min((cap + 1) // 2, len(temporal_buckets))
            year_queues = {
                year: sorted(key for key in temporal_buckets if key[0] == year)
                for year in recent_years
            }
            while (
                len(covered_recent_keys) < recent_target
                and len(selected) < cap
                and any(year_queues.values())
            ):
                progressed = False
                for year in recent_years:
                    while year_queues[year]:
                        key = year_queues[year].pop(0)
                        if key in covered_recent_keys:
                            continue
                        candidates_in_bucket = [
                            group
                            for group in temporal_buckets[key]
                            if group["origin_group_id"] not in selected_origins
                        ]
                        if candidates_in_bucket:
                            add_group(candidates_in_bucket[0])
                            covered_recent_keys.add(key)
                            progressed = True
                        break
                    if len(covered_recent_keys) >= recent_target or len(selected) >= cap:
                        break
                if not progressed:
                    break

            # Recency is a display preference, not permission to erase the
            # earlier history of the point. Keep one dated pre-window origin
            # when one exists and the cap still has room.
            if len(selected) < cap and recent_years:
                older_groups = [
                    group
                    for group in groups
                    if group["origin_group_id"] not in selected_origins
                    and group["origin_publication_years"]
                    and max(group["origin_publication_years"]) < min(recent_years)
                ]
                if older_groups:
                    older_bucket_keys = sorted(
                        {
                            (
                                group["source_role"],
                                group["source_venue"],
                                group["engagement_kind"],
                            )
                            for group in older_groups
                        }
                    )
                    anchor_key = older_bucket_keys[0]
                    anchor_bucket = sorted(
                        (
                            group
                            for group in older_groups
                            if (
                                group["source_role"],
                                group["source_venue"],
                                group["engagement_kind"],
                            )
                            == anchor_key
                        ),
                        key=lambda group: (
                            -max(group["origin_publication_years"]),
                            _bucket_priority(group),
                        ),
                    )
                    add_group(anchor_bucket[0])

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
                priority=(
                    _bucket_priority
                    if temporal_policy is not None
                    else _global_priority
                ),
            )
        else:
            group["display_members"] = _display_members(
                group["origin_members"],
                priority=(
                    _bucket_priority
                    if temporal_policy is not None
                    else _global_priority
                ),
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
    frontier_candidate_ids = {
        row["candidate_id"]
        for row in eligible
        if row["candidate_id"] in frontier_relation_candidate_ids
    }
    if not frontier_candidate_ids <= displayed_candidate_ids:
        raise EvidenceConsumerError(
            "frontier_candidate_not_visible",
            "one or more frontier-defining candidates are absent from the display",
        )
    return displayed


def _validate_relation_response(
    candidates: Sequence[Mapping[str, Any]],
    response: Mapping[str, Any],
    *,
    value_policy: bool = False,
    response_mode: str = "literal_ids",
    batch_id: str | None = None,
) -> list[dict[str, Any]]:
    expected = [row["candidate_id"] for row in candidates]
    if response_mode == "positional":
        response_key = "results_by_candidate_row"
        expected_keys = {response_key} if batch_id is None else {response_key, "batch_id"}
        if set(response) != expected_keys or not isinstance(
            response.get(response_key), dict
        ):
            raise EvidenceConsumerError(
                "relation_response_shape", "positional results missing"
            )
        if batch_id is not None and response.get("batch_id") != batch_id:
            raise EvidenceConsumerError(
                "relation_batch_identity",
                "relation response does not carry the batch identity it answers",
            )
        positional_results = response[response_key]
        expected_row_keys = [f"row_{index:04d}" for index in range(len(expected))]
        if set(positional_results) != set(expected_row_keys):
            raise EvidenceConsumerError(
                "missing_candidate_result", "positional candidate count changed"
            )
        results = []
        for candidate_id, row_key in zip(expected, expected_row_keys, strict=True):
            relation = positional_results[row_key]
            if not isinstance(relation, str):
                raise EvidenceConsumerError(
                    "relation_response_shape", "invalid relation result"
                )
            results.append(
                {
                    "candidate_id": candidate_id,
                    "relation": relation,
                    "reason_code": POSITIONAL_REASON_CODE_BY_RELATION.get(
                        relation, ""
                    ),
                }
            )
    else:
        if set(response) != {"results"} or not isinstance(response.get("results"), list):
            raise EvidenceConsumerError("relation_response_shape", "results missing")
        results = response["results"]
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
        reason_code = result["reason_code"]
        if not value_policy:
            reason_code = _normalize_reason_code(reason_code)
        if INTERNAL_RELATION_LABEL_RE.search(reason_code.replace("_", " ")):
            raise EvidenceConsumerError(
                "reason_code_relation_leak",
                "reason code must name the evidence meaning, not its internal relation",
            )
        if value_policy:
            expected_relation = VALUE_REASON_RELATIONS.get(reason_code)
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
        merged.append({**candidate, "relation": result["relation"], "reason_code": reason_code})
    return merged


def _normalize_reason_code(reason_code: str) -> str:
    """Keep ordinary ``exclude`` verbs from masquerading as lane labels."""

    tokens = reason_code.split("_")
    return "_".join(
        "omits" if token == "exclude" and 0 < index < len(tokens) - 1 else token
        for index, token in enumerate(tokens)
    )


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


QUOTE_PROMPT_COLUMNS = (
    "selected_id",
    "display_label",
    "normalized_meaning",
    "relation",
    "same_evidence_companion_meanings",
    "body_id",
)

LEGACY_RELATION_CONFIRMATION_COLUMNS = (
    "confirmation_row_id",
    "normalized_meaning",
    "conditions",
    "subject_product_ids",
    "product_version_ids",
    "source_role",
    "same_evidence_companion_meanings",
)
RELATION_CONFIRMATION_COLUMNS = LEGACY_RELATION_CONFIRMATION_COLUMNS + (
    "parent_context_ids",
)


def _quote_prompt_envelope(
    bounded_claim: str,
    selected: Sequence[Mapping[str, Any]],
    bodies: Mapping[tuple[str, str], str | None],
    *,
    required_quote_candidate_ids: frozenset[str] = frozenset(),
) -> tuple[dict[str, Any], list[str]]:
    """Project long bodies and frontier-defining rows into quote review.

    Ordinary short bodies are already exact quotes under the owning contract.
    A frontier-defining row is different: its meaning helped admit the point,
    so the provider must verify that even a short literal body substantiates it.
    Missing bodies remain deterministically unavailable.
    """

    body_ids: dict[str, str] = {}
    body_rows: list[list[str]] = []
    selected_rows: list[list[Any]] = []
    provider_selected_ids: list[str] = []
    for row in selected:
        body = bodies.get((row["source_id"], row["evidence_id"]))
        if body is None or (
            len(body) <= MAX_QUOTE_CHARACTERS
            and row["candidate_id"] not in required_quote_candidate_ids
        ):
            continue
        if body not in body_ids:
            body_id = f"body_{len(body_ids) + 1:02d}"
            body_ids[body] = body_id
            body_rows.append([body_id, body])
        provider_selected_ids.append(row["selected_id"])
        selected_rows.append(
            [
                row["selected_id"],
                _display_label(row["reason_code"]),
                row["normalized_meaning"],
                row["relation"],
                _compact_companion_meanings(row),
                body_ids[body],
            ]
        )
    return (
        {
            "bounded_claim": bounded_claim,
            "body_columns": ["body_id", "source_body"],
            "body_rows": body_rows,
            "selected_columns": list(QUOTE_PROMPT_COLUMNS),
            "selected_rows": selected_rows,
        },
        provider_selected_ids,
    )


def _confirmation_row_presentation(
    selected: Sequence[Mapping[str, Any]], selected_rows_sha256: str
) -> list[tuple[str, Mapping[str, Any]]]:
    """Order the confirmation rows by a content-derived key.

    Selection order encodes the first pass: protected and reserved
    support/counter origins lead, and the creator-influence block always
    trails.  Presenting the rows in selection order would hand the confirming
    workload the selection priority the manifest claims is hidden, so the
    presented order and the row handles are derived from the bound row
    identities instead.
    """
    ordered = sorted(
        selected,
        key=lambda row: (
            sha256_text(f"{selected_rows_sha256}::{row['candidate_id']}"),
            row["candidate_id"],
        ),
    )
    return [
        (f"row_{index:02d}", row) for index, row in enumerate(ordered, start=1)
    ]


def _confirmation_prompt_projection(
    presentation: Sequence[tuple[str, Mapping[str, Any]]],
) -> tuple[bool, tuple[str, ...], list[list[Any]], list[list[str]]]:
    context_aware, projected, context_rows = _project_parent_context(
        [row for _, row in presentation]
    )
    columns = (
        RELATION_CONFIRMATION_COLUMNS
        if context_aware
        else LEGACY_RELATION_CONFIRMATION_COLUMNS
    )
    rows = [
        [
            row_id,
            row["normalized_meaning"],
            row.get("conditions", []),
            row.get("subject_product_ids", []),
            row.get("product_version_ids", []),
            row["source_role"],
            _compact_companion_meanings(row),
            *([row.get("parent_context_ids", [])] if context_aware else []),
        ]
        for (row_id, _), row in zip(presentation, projected, strict=True)
    ]
    return context_aware, columns, rows, context_rows


def _relation_confirmation_prompt_envelope(
    bounded_claim: str,
    presentation: Sequence[tuple[str, Mapping[str, Any]]],
    *,
    point_context_rows: Sequence[Sequence[str]] = (),
) -> dict[str, Any]:
    context_aware, columns, rows, context_rows = _confirmation_prompt_projection(
        presentation
    )
    envelope = {
        "bounded_point": bounded_claim,
        "selected_columns": list(columns),
        "selected_rows": rows,
    }
    _attach_parent_context_envelope(envelope, context_aware, context_rows)
    _attach_point_parent_context_envelope(envelope, point_context_rows)
    return envelope


def _prepare_quotes_from_labeled(
    manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    labeled: Sequence[Mapping[str, Any]],
    *,
    schema_version: str,
    preselection_confirmation: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    truth_group_cap = _truth_group_cap(manifest["spec"])
    value_policy = _uses_value_policy(manifest["spec"], labeled)
    truth_selection_policy = "value_first" if value_policy else "balanced"
    temporal_policy = _temporal_presentation_policy(manifest["spec"])
    labeled = _apply_frontier_relation_rejections(manifest["spec"], labeled)
    frontier_relation_candidate_ids = _frontier_relation_candidate_ids(
        manifest["spec"], labeled
    )
    truth = _select_groups(
        labeled,
        "truth_support",
        truth_group_cap,
        truth_policy=truth_selection_policy,
        temporal_policy=temporal_policy,
        frontier_relation_candidate_ids=frontier_relation_candidate_ids,
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
    quote_envelope, provider_selected_ids = _quote_prompt_envelope(
        manifest["spec"]["bounded_claim"],
        selected,
        bodies,
        required_quote_candidate_ids=frontier_relation_candidate_ids,
    )
    prompt = QUOTE_PROMPT.format(envelope=_compact(quote_envelope))
    schema = _quote_schema()
    quote_manifest = {
        "schema_version": schema_version,
        "selection_id": manifest["selection_id"],
        "bounded_claim": manifest["spec"]["bounded_claim"],
        "selection_manifest_sha256": manifest["manifest_sha256"],
        "candidate_inventory_sha256": manifest["candidate_inventory_sha256"],
        "labeled_inventory": labeled,
        "labeled_inventory_sha256": _canonical_json_sha256(labeled),
        "selected_rows": selected,
        "selected_rows_sha256": _canonical_json_sha256(selected),
        "truth_group_cap": truth_group_cap,
        "truth_selection_policy": truth_selection_policy,
        "selected_relation_confirmation_required": schema_version == QUOTE_MANIFEST_VERSION,
        "provider_selected_ids": provider_selected_ids,
        "quote_body_sha256": {
            row["selected_id"]: sha256_text(row["source_body"]) if row["source_body"] is not None else None
            for row in quote_rows
        },
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "model_api_calls": 0,
    }
    if frontier_relation_candidate_ids:
        quote_manifest["frontier_relation_display_policy"] = (
            FRONTIER_RELATION_DISPLAY_POLICY
        )
        quote_manifest["frontier_relation_candidate_ids"] = sorted(
            frontier_relation_candidate_ids
        )
    _, _, point_context_rows = _project_parent_context(labeled)
    if point_context_rows:
        quote_manifest["point_parent_context_rows"] = point_context_rows
    if preselection_confirmation is not None:
        quote_manifest["preselection_relation_confirmation"] = dict(
            preselection_confirmation
        )
    if temporal_policy is not None:
        recent_years = sorted(
            {
                year
                for row in labeled
                if row["layer"] == "truth_support"
                and _truth_row_display_eligible(
                    row,
                    truth_selection_policy,
                    frontier_relation_bound=row["candidate_id"]
                    in frontier_relation_candidate_ids,
                )
                and (year := _publication_year(row)) is not None
            },
            reverse=True,
        )[:RECENT_YEAR_COUNT]
        quote_manifest["temporal_presentation_policy"] = temporal_policy
        quote_manifest["recent_calendar_years"] = recent_years
    quote_manifest["manifest_sha256"] = _canonical_json_sha256(quote_manifest)
    return prompt, schema, quote_manifest


def finalize_relations_prepare_quotes(
    manifest: Mapping[str, Any], sources: Sequence[Mapping[str, Any]], response: Mapping[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    candidates = _candidate_rows_for_manifest(sources, manifest)
    response_mode = _relation_response_mode(manifest["spec"])
    value_policy = _uses_value_policy(manifest["spec"], candidates)
    labeled = _validate_relation_response(
        candidates,
        response,
        value_policy=value_policy,
        response_mode=response_mode,
    )
    return _prepare_quotes_from_labeled(
        manifest,
        sources,
        labeled,
        schema_version=QUOTE_MANIFEST_VERSION,
    )


def _preselection_confirmation_candidates(
    labeled: Sequence[Mapping[str, Any]],
    *,
    frontier_relation_candidate_ids: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Return every row that could reach a displayed evidence pack.

    Truth rows can reach display only when material-positive, explicitly
    protected, or literally bound to the frontier point.  Influence rows use a
    separate cap and therefore all require confirmation.  The frontier is
    independent of the first-pass relation, so a mistaken ``exclude`` cannot
    hide a high-signal, protected, or frontier-defining row.
    """

    return [
        dict(row)
        for row in labeled
        if row.get("layer") == "influence_context"
        or row.get("protected_lanes")
        or row.get("engagement_material_positive") is True
        or row["candidate_id"] in frontier_relation_candidate_ids
    ]


def _preselection_confirmation_state(
    manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    first_pass_response: Mapping[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
    list[tuple[str, Mapping[str, Any]]],
    bool,
]:
    stored = manifest.get("manifest_sha256")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        manifest.get("schema_version") != SELECTION_MANIFEST_VERSION
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection manifest changed"
        )
    candidates = _candidate_rows_for_manifest(sources, manifest)
    if _canonical_json_sha256(candidates) != manifest.get("candidate_inventory_sha256"):
        raise EvidenceConsumerError(
            "manifest_verification", "candidate inventory changed"
        )
    value_policy = _uses_value_policy(manifest["spec"], candidates)
    labeled = _validate_relation_response(
        candidates,
        first_pass_response,
        value_policy=value_policy,
        response_mode=_relation_response_mode(manifest["spec"]),
    )
    labeled = _apply_frontier_relation_rejections(manifest["spec"], labeled)
    frontier_relation_candidate_ids = _frontier_relation_candidate_ids(
        manifest["spec"], labeled
    )
    frontier = _preselection_confirmation_candidates(
        labeled,
        frontier_relation_candidate_ids=frontier_relation_candidate_ids,
    )
    if not frontier:
        raise EvidenceConsumerError(
            "preselection_confirmation_empty",
            "no frontier-bound, material, protected, or influence candidates can reach display",
        )
    frontier_sha256 = _canonical_json_sha256(frontier)
    presentation = _confirmation_row_presentation(frontier, frontier_sha256)
    return (
        candidates,
        labeled,
        frontier,
        frontier_sha256,
        presentation,
        value_policy,
    )


def prepare_preselection_relation_confirmation(
    manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    first_pass_response: Mapping[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    (
        candidates,
        labeled,
        _,
        frontier_sha256,
        presentation,
        value_policy,
    ) = _preselection_confirmation_state(manifest, sources, first_pass_response)
    context_aware, columns, rows, context_rows = _confirmation_prompt_projection(
        presentation
    )
    envelope = {
        "bounded_point": manifest["spec"]["bounded_claim"],
        "candidate_columns": list(columns),
        "candidate_rows": rows,
    }
    _attach_parent_context_envelope(envelope, context_aware, context_rows)
    _, _, point_context_rows = _project_parent_context(candidates)
    _attach_point_parent_context_envelope(envelope, point_context_rows)
    prompt = PRESELECTION_RELATION_CONFIRMATION_PROMPT.format(
        policy_guidance=_policy_guidance(manifest["spec"], candidates),
        envelope=_compact(envelope),
    )
    schema = _preselection_relation_confirmation_schema(value_policy=value_policy)
    confirmation_manifest = {
        "schema_version": PRESELECTION_RELATION_CONFIRMATION_MANIFEST_VERSION,
        "selection_manifest_sha256": manifest["manifest_sha256"],
        "candidate_inventory_sha256": manifest["candidate_inventory_sha256"],
        "first_pass_response_sha256": _canonical_json_sha256(first_pass_response),
        "labeled_inventory_sha256": _canonical_json_sha256(labeled),
        "confirmation_frontier_sha256": frontier_sha256,
        "confirmation_row_ids": [row_id for row_id, _ in presentation],
        "confirmation_candidate_ids": [
            row["candidate_id"] for _, row in presentation
        ],
        "value_policy": value_policy,
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "hidden_first_pass_fields": [
            "candidate_id",
            "relation",
            "reason_code",
            "engagement",
            "selection_priority",
        ],
        "model_api_calls": 0,
    }
    confirmation_manifest["manifest_sha256"] = _canonical_json_sha256(
        confirmation_manifest
    )
    return prompt, schema, confirmation_manifest


def finalize_preselection_relation_confirmation_prepare_quotes(
    manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    first_pass_response: Mapping[str, Any],
    confirmation_manifest: Mapping[str, Any],
    confirmation_response: Mapping[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    _, _, expected_manifest = prepare_preselection_relation_confirmation(
        manifest, sources, first_pass_response
    )
    if dict(confirmation_manifest) != expected_manifest:
        raise EvidenceConsumerError(
            "manifest_verification", "preselection confirmation binding changed"
        )
    if set(confirmation_response) != {
        "point_scope",
        "point_scope_reason",
        "relation_checks",
    } or not isinstance(confirmation_response.get("relation_checks"), list):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "relation_checks missing"
        )
    if (
        confirmation_response.get("point_scope") not in POINT_SCOPE_STATUSES
        or not isinstance(confirmation_response.get("point_scope_reason"), str)
        or not confirmation_response["point_scope_reason"].strip()
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "point scope result missing or invalid"
        )
    if confirmation_response["point_scope"] != "single_point":
        raise EvidenceConsumerError(
            "bounded_point_not_confirmed",
            confirmation_response["point_scope_reason"].strip(),
        )
    checks = confirmation_response["relation_checks"]
    if not all(
        isinstance(row, Mapping)
        and set(row) == {"confirmation_row_id", "relation", "reason_code"}
        for row in checks
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "relation check row shape mismatch"
        )
    expected_row_ids = expected_manifest["confirmation_row_ids"]
    observed = [row["confirmation_row_id"] for row in checks]
    if len(observed) != len(set(observed)):
        raise EvidenceConsumerError(
            "duplicate_relation_confirmation", "candidate row repeated"
        )
    if set(observed) - set(expected_row_ids):
        raise EvidenceConsumerError(
            "foreign_relation_confirmation", "foreign candidate row"
        )
    if observed != expected_row_ids:
        boundary = (
            "missing_relation_confirmation"
            if set(observed) != set(expected_row_ids)
            else "relation_confirmation_order_mismatch"
        )
        raise EvidenceConsumerError(boundary, "relation check set/order mismatch")

    candidates = _candidate_rows_for_manifest(sources, manifest)
    labeled = _validate_relation_response(
        candidates,
        first_pass_response,
        value_policy=expected_manifest["value_policy"],
        response_mode=_relation_response_mode(manifest["spec"]),
    )
    by_id = {row["candidate_id"]: dict(row) for row in labeled}
    changed = 0
    for candidate_id, check in zip(
        expected_manifest["confirmation_candidate_ids"], checks, strict=True
    ):
        relation = check["relation"]
        reason_code = check["reason_code"]
        if (
            relation not in RELATIONS
            or not isinstance(reason_code, str)
            or len(reason_code) > 80
            or not REASON_CODE_RE.fullmatch(reason_code)
        ):
            raise EvidenceConsumerError(
                "relation_confirmation_shape", "invalid relation confirmation"
            )
        if not expected_manifest["value_policy"]:
            reason_code = _normalize_reason_code(reason_code)
        if INTERNAL_RELATION_LABEL_RE.search(reason_code.replace("_", " ")):
            raise EvidenceConsumerError(
                "reason_code_relation_leak",
                "reason code must name the evidence meaning, not its internal relation",
            )
        if expected_manifest["value_policy"] and VALUE_REASON_RELATIONS.get(reason_code) != relation:
            raise EvidenceConsumerError(
                "relation_reason_mismatch", "confirmed value reason does not match relation"
            )
        row = by_id[candidate_id]
        if row["layer"] == "influence_context" and relation in {"support", "counter"}:
            raise EvidenceConsumerError(
                "creator_customer_laundering",
                "creator-authored evidence cannot corroborate customer truth",
            )
        changed += int(
            row["relation"] != relation or row["reason_code"] != reason_code
        )
        row["relation"] = relation
        row["reason_code"] = reason_code
    final_labeled = [by_id[row["candidate_id"]] for row in labeled]
    confirmation_binding = {
        "status": "passed",
        "confirmation_manifest_sha256": expected_manifest["manifest_sha256"],
        "confirmation_response_sha256": _canonical_json_sha256(confirmation_response),
        "confirmed_candidate_count": len(checks),
        "changed_first_pass_count": changed,
        "point_scope_reason": confirmation_response["point_scope_reason"].strip(),
    }
    prompt, schema, quote_manifest = _prepare_quotes_from_labeled(
        manifest,
        sources,
        final_labeled,
        schema_version=PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
        preselection_confirmation=confirmation_binding,
    )
    confirmed_ids = set(expected_manifest["confirmation_candidate_ids"])
    unconfirmed_selected = sorted(
        row["candidate_id"]
        for row in quote_manifest["selected_rows"]
        if row["candidate_id"] not in confirmed_ids
    )
    if unconfirmed_selected:
        raise EvidenceConsumerError(
            "selected_relation_unconfirmed",
            f"selected rows escaped confirmation: {unconfirmed_selected}",
        )
    quote_manifest.pop("manifest_sha256")
    quote_manifest["preselection_replay"] = {
        "selection_manifest": dict(manifest),
        "first_pass_response": dict(first_pass_response),
        "confirmation_manifest": dict(confirmation_manifest),
        "confirmation_response": dict(confirmation_response),
    }
    quote_manifest["manifest_sha256"] = _canonical_json_sha256(quote_manifest)
    return prompt, schema, quote_manifest


def _assemble_batched_relation_response(
    batch_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    responses: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    stored = batch_manifest.get("manifest_sha256")
    payload = {
        key: value for key, value in batch_manifest.items() if key != "manifest_sha256"
    }
    if (
        batch_manifest.get("schema_version") != SELECTION_BATCH_MANIFEST_VERSION
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection batch manifest changed"
        )
    selection_manifest = batch_manifest.get("selection_manifest")
    if (
        not isinstance(selection_manifest, Mapping)
        or selection_manifest.get("manifest_sha256")
        != batch_manifest.get("selection_manifest_sha256")
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection manifest binding changed"
        )
    candidates = _candidate_rows_for_manifest(sources, selection_manifest)
    if (
        len(candidates) != batch_manifest.get("candidate_count")
        or _canonical_json_sha256(candidates)
        != batch_manifest.get("candidate_inventory_sha256")
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "batched candidate inventory changed"
        )
    batches = batch_manifest.get("batches")
    if not isinstance(batches, list):
        raise EvidenceConsumerError(
            "manifest_verification", "selection batches missing"
        )
    expected_batch_ids = [row.get("batch_id") for row in batches]
    if (
        not all(isinstance(batch_id, str) for batch_id in expected_batch_ids)
        or len(expected_batch_ids) != len(set(expected_batch_ids))
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selection batch identities changed"
        )
    if set(responses) != set(expected_batch_ids):
        raise EvidenceConsumerError(
            "missing_relation_batch", "relation batch response set changed"
        )
    full_results = {}
    expected_start = 0
    for batch in batches:
        batch_id = batch["batch_id"]
        start = batch.get("start_index")
        count = batch.get("candidate_count")
        if start != expected_start or not isinstance(count, int) or count < 1:
            raise EvidenceConsumerError(
                "manifest_verification", "relation batch coverage changed"
            )
        subset = candidates[start : start + count]
        if (
            len(subset) != count
            or _canonical_json_sha256([row["candidate_id"] for row in subset])
            != batch.get("candidate_ids_sha256")
        ):
            raise EvidenceConsumerError(
                "manifest_verification", "relation batch membership changed"
            )
        validated = _validate_relation_response(
            subset,
            responses[batch_id],
            value_policy=False,
            response_mode="positional",
            batch_id=batch_id,
        )
        full_results.update(
            {
                f"row_{start + local_index:04d}": row["relation"]
                for local_index, row in enumerate(validated)
            }
        )
        expected_start += count
    if expected_start != len(candidates):
        raise EvidenceConsumerError(
            "manifest_verification", "relation batch coverage is incomplete"
        )
    transport = {
        "mode": "named_positional_batches",
        "batch_manifest_sha256": batch_manifest["manifest_sha256"],
        "batch_count": len(batches),
        "batch_response_sha256": {
            batch_id: _canonical_json_sha256(responses[batch_id])
            for batch_id in expected_batch_ids
        },
    }
    return (
        dict(selection_manifest),
        {"results_by_candidate_row": full_results},
        transport,
    )


def finalize_batched_relations_prepare_quotes(
    batch_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    responses: Mapping[str, Mapping[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    selection_manifest, first_response, transport = (
        _assemble_batched_relation_response(batch_manifest, sources, responses)
    )
    prompt, schema, quote_manifest = finalize_relations_prepare_quotes(
        selection_manifest, sources, first_response
    )
    quote_manifest.pop("manifest_sha256")
    quote_manifest["schema_version"] = BATCHED_QUOTE_MANIFEST_VERSION
    quote_manifest["relation_transport"] = transport
    quote_manifest["manifest_sha256"] = _canonical_json_sha256(quote_manifest)
    return prompt, schema, quote_manifest


def prepare_batched_preselection_relation_confirmations(
    batch_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    responses: Mapping[str, Mapping[str, Any]],
    *,
    batch_size: int,
) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    if (
        isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or batch_size < 1
        or batch_size > MAX_RELATION_BATCH_SIZE
    ):
        raise EvidenceConsumerError(
            "selection_spec",
            f"confirmation batch size must be an integer from 1 to {MAX_RELATION_BATCH_SIZE}",
        )
    selection_manifest, first_response, relation_transport = (
        _assemble_batched_relation_response(batch_manifest, sources, responses)
    )
    (
        candidates,
        labeled,
        _,
        frontier_sha256,
        presentation,
        value_policy,
    ) = _preselection_confirmation_state(
        selection_manifest, sources, first_response
    )
    prompts_and_schemas: list[tuple[str, dict[str, Any]]] = []
    batches = []
    _, _, point_context_rows = _project_parent_context(candidates)
    for batch_index, start in enumerate(
        range(0, len(presentation), batch_size), start=1
    ):
        subset = presentation[start : start + batch_size]
        confirmation_batch_id = f"confirmation_batch_{batch_index:04d}"
        context_aware, columns, rows, context_rows = _confirmation_prompt_projection(
            subset
        )
        envelope = {
            "batch_id": confirmation_batch_id,
            "bounded_point": selection_manifest["spec"]["bounded_claim"],
            "candidate_columns": list(columns),
            "candidate_rows": rows,
        }
        _attach_parent_context_envelope(envelope, context_aware, context_rows)
        _attach_point_parent_context_envelope(envelope, point_context_rows)
        prompt = PRESELECTION_CONFIRMATION_BATCH_PROMPT.format(
            policy_guidance=_policy_guidance(
                selection_manifest["spec"], candidates
            ),
            envelope=_compact(envelope),
        )
        schema = _preselection_relation_confirmation_schema(
            value_policy=value_policy, batch_id=confirmation_batch_id
        )
        batches.append(
            {
                "batch_id": confirmation_batch_id,
                "start_index": start,
                "candidate_count": len(subset),
                "confirmation_row_ids": [row_id for row_id, _ in subset],
                "confirmation_candidate_ids_sha256": _canonical_json_sha256(
                    [row["candidate_id"] for _, row in subset]
                ),
                "prompt_sha256": sha256_text(prompt),
                "response_schema_sha256": _canonical_json_sha256(schema),
            }
        )
        prompts_and_schemas.append((prompt, schema))
    confirmation_batch_manifest = {
        "schema_version": PRESELECTION_CONFIRMATION_BATCH_MANIFEST_VERSION,
        "selection_manifest_sha256": selection_manifest["manifest_sha256"],
        "relation_transport": relation_transport,
        "first_pass_response_sha256": _canonical_json_sha256(first_response),
        "labeled_inventory_sha256": _canonical_json_sha256(labeled),
        "confirmation_frontier_sha256": frontier_sha256,
        "confirmation_candidate_count": len(presentation),
        "batch_size": batch_size,
        "batches": batches,
        "value_policy": value_policy,
        "model_api_calls": 0,
    }
    confirmation_batch_manifest["manifest_sha256"] = _canonical_json_sha256(
        confirmation_batch_manifest
    )
    return confirmation_batch_manifest, prompts_and_schemas


def finalize_batched_preselection_relation_confirmations_prepare_quotes(
    batch_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    responses: Mapping[str, Mapping[str, Any]],
    confirmation_batch_manifest: Mapping[str, Any],
    confirmation_batch_responses: Mapping[str, Mapping[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    expected_manifest, _ = prepare_batched_preselection_relation_confirmations(
        batch_manifest,
        sources,
        responses,
        batch_size=confirmation_batch_manifest.get("batch_size"),
    )
    if dict(confirmation_batch_manifest) != expected_manifest:
        raise EvidenceConsumerError(
            "manifest_verification", "preselection confirmation batches changed"
        )
    expected_ids = [row["batch_id"] for row in expected_manifest["batches"]]
    if set(confirmation_batch_responses) != set(expected_ids):
        raise EvidenceConsumerError(
            "missing_relation_confirmation_batch",
            "preselection confirmation response set changed",
        )
    merged_checks = []
    point_scope_reasons = []
    for batch in expected_manifest["batches"]:
        batch_id = batch["batch_id"]
        response = confirmation_batch_responses[batch_id]
        if set(response) != {
            "batch_id",
            "point_scope",
            "point_scope_reason",
            "relation_checks",
        } or not isinstance(response.get("relation_checks"), list):
            raise EvidenceConsumerError(
                "relation_confirmation_shape", "batched relation checks missing"
            )
        if response.get("batch_id") != batch_id:
            raise EvidenceConsumerError(
                "relation_confirmation_batch_identity",
                "preselection confirmation answered another batch",
            )
        if (
            response.get("point_scope") not in POINT_SCOPE_STATUSES
            or not isinstance(response.get("point_scope_reason"), str)
            or not response["point_scope_reason"].strip()
        ):
            raise EvidenceConsumerError(
                "relation_confirmation_shape", "point scope result missing or invalid"
            )
        if response["point_scope"] != "single_point":
            raise EvidenceConsumerError(
                "bounded_point_not_confirmed",
                response["point_scope_reason"].strip(),
            )
        checks = response["relation_checks"]
        observed = [
            row.get("confirmation_row_id") for row in checks if isinstance(row, dict)
        ]
        if observed != batch["confirmation_row_ids"]:
            boundary = (
                "missing_relation_confirmation"
                if set(observed) != set(batch["confirmation_row_ids"])
                else "relation_confirmation_order_mismatch"
            )
            raise EvidenceConsumerError(boundary, "relation check set/order mismatch")
        merged_checks.extend(checks)
        point_scope_reasons.append(response["point_scope_reason"].strip())

    selection_manifest, first_response, relation_transport = (
        _assemble_batched_relation_response(batch_manifest, sources, responses)
    )
    _, _, canonical_confirmation_manifest = prepare_preselection_relation_confirmation(
        selection_manifest, sources, first_response
    )
    canonical_confirmation_response = {
        "point_scope": "single_point",
        "point_scope_reason": point_scope_reasons[0],
        "relation_checks": merged_checks,
    }
    prompt, schema, quote_manifest = (
        finalize_preselection_relation_confirmation_prepare_quotes(
            selection_manifest,
            sources,
            first_response,
            canonical_confirmation_manifest,
            canonical_confirmation_response,
        )
    )
    quote_manifest.pop("manifest_sha256")
    quote_manifest["relation_transport"] = relation_transport
    quote_manifest["preselection_relation_confirmation"][
        "canonical_single_prompt_executed"
    ] = False
    quote_manifest["preselection_confirmation_transport"] = {
        "mode": "named_preselection_confirmation_batches",
        "batch_manifest_sha256": confirmation_batch_manifest["manifest_sha256"],
        "batch_count": len(expected_ids),
        "batch_response_sha256": {
            batch_id: _canonical_json_sha256(
                confirmation_batch_responses[batch_id]
            )
            for batch_id in expected_ids
        },
        "point_scope_reasons": point_scope_reasons,
    }
    quote_manifest["preselection_replay"] = {
        "batch_manifest": dict(batch_manifest),
        "batch_responses": {
            batch_id: dict(response) for batch_id, response in responses.items()
        },
        "confirmation_batch_manifest": dict(confirmation_batch_manifest),
        "confirmation_batch_responses": {
            batch_id: dict(response)
            for batch_id, response in confirmation_batch_responses.items()
        },
    }
    quote_manifest["manifest_sha256"] = _canonical_json_sha256(quote_manifest)
    return prompt, schema, quote_manifest


def _verified_quote_manifest_version(quote_manifest: Mapping[str, Any]) -> str:
    stored = quote_manifest.get("manifest_sha256")
    payload = {
        key: value for key, value in quote_manifest.items() if key != "manifest_sha256"
    }
    manifest_version = quote_manifest.get("schema_version")
    if (
        manifest_version
        not in {
            LEGACY_QUOTE_MANIFEST_VERSION,
            PREVIOUS_QUOTE_MANIFEST_VERSION,
            PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
            PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
            QUOTE_MANIFEST_VERSION,
            PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
        }
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "quote manifest changed"
        )
    return manifest_version


def prepare_selected_relation_confirmation(
    quote_manifest: Mapping[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    manifest_version = _verified_quote_manifest_version(quote_manifest)
    if (
        manifest_version != QUOTE_MANIFEST_VERSION
        or quote_manifest.get("selected_relation_confirmation_required") is not True
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_not_required",
            "only current quote manifests require selected-row confirmation",
        )
    selected = quote_manifest.get("selected_rows")
    if (
        not isinstance(selected, list)
        or quote_manifest.get("selected_rows_sha256")
        != _canonical_json_sha256(selected)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "selected rows changed"
        )
    presentation = _confirmation_row_presentation(
        selected, quote_manifest["selected_rows_sha256"]
    )
    envelope = _relation_confirmation_prompt_envelope(
        quote_manifest["bounded_claim"],
        presentation,
        point_context_rows=quote_manifest.get("point_parent_context_rows", []),
    )
    prompt = RELATION_CONFIRMATION_PROMPT.format(envelope=_compact(envelope))
    schema = _relation_confirmation_schema()
    confirmation_manifest = {
        "schema_version": RELATION_CONFIRMATION_MANIFEST_VERSION,
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
        "selection_manifest_sha256": quote_manifest["selection_manifest_sha256"],
        "selected_rows_sha256": quote_manifest["selected_rows_sha256"],
        "confirmation_row_ids": [
            confirmation_row_id for confirmation_row_id, _ in presentation
        ],
        "confirmation_row_selected_ids": [
            row["selected_id"] for _, row in presentation
        ],
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "hidden_first_pass_fields": [
            "relation",
            "reason_code",
            "display_label",
            "engagement",
            "selection_priority",
        ],
        "model_api_calls": 0,
    }
    confirmation_manifest["manifest_sha256"] = _canonical_json_sha256(
        confirmation_manifest
    )
    return prompt, schema, confirmation_manifest


def _validate_selected_relation_confirmation(
    quote_manifest: Mapping[str, Any],
    confirmation_manifest: Mapping[str, Any],
    response: Mapping[str, Any],
) -> tuple[str, str]:
    stored = confirmation_manifest.get("manifest_sha256")
    payload = {
        key: value
        for key, value in confirmation_manifest.items()
        if key != "manifest_sha256"
    }
    if (
        confirmation_manifest.get("schema_version")
        != RELATION_CONFIRMATION_MANIFEST_VERSION
        or stored != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "relation confirmation manifest changed"
        )
    # The confirmation manifest is a pure function of the bound quote manifest,
    # so re-deriving it is the only available proof that the workload actually
    # sent was the hidden-label prompt this manifest names.  Comparing only the
    # binding hashes would accept a hand-written manifest whose recorded
    # prompt_sha256 belongs to a prompt that leaked the first-pass labels.
    _, _, expected_manifest = prepare_selected_relation_confirmation(quote_manifest)
    if dict(confirmation_manifest) != expected_manifest:
        raise EvidenceConsumerError(
            "manifest_verification", "relation confirmation binding changed"
        )
    selected_by_id = {row["selected_id"]: row for row in quote_manifest["selected_rows"]}
    expected = expected_manifest["confirmation_row_ids"]
    selected_ids = expected_manifest["confirmation_row_selected_ids"]
    if set(response) != {
        "point_scope",
        "point_scope_reason",
        "relation_checks",
    } or not isinstance(
        response.get("relation_checks"), list
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "relation_checks missing"
        )
    if (
        response.get("point_scope") not in POINT_SCOPE_STATUSES
        or not isinstance(response.get("point_scope_reason"), str)
        or not response["point_scope_reason"].strip()
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "point scope result missing or invalid"
        )
    if response["point_scope"] != "single_point":
        raise EvidenceConsumerError(
            "bounded_point_not_confirmed", response["point_scope_reason"].strip()
        )
    checks = response["relation_checks"]
    if not all(
        isinstance(row, dict) and set(row) == {"confirmation_row_id", "relation"}
        for row in checks
    ):
        raise EvidenceConsumerError(
            "relation_confirmation_shape", "relation check row shape mismatch"
        )
    observed = [row["confirmation_row_id"] for row in checks]
    if len(observed) != len(set(observed)):
        raise EvidenceConsumerError(
            "duplicate_relation_confirmation", "selected row repeated"
        )
    if set(observed) - set(expected):
        raise EvidenceConsumerError(
            "foreign_relation_confirmation", "foreign selected row"
        )
    if observed != expected:
        boundary = (
            "missing_relation_confirmation"
            if set(observed) != set(expected)
            else "relation_confirmation_order_mismatch"
        )
        raise EvidenceConsumerError(boundary, "relation check set/order mismatch")
    for selected_id, check in zip(selected_ids, checks, strict=True):
        selected_row = selected_by_id[selected_id]
        if check["relation"] not in RELATIONS:
            raise EvidenceConsumerError(
                "relation_confirmation_shape", "invalid confirmed relation"
            )
        if check["relation"] != selected_row["relation"]:
            raise EvidenceConsumerError(
                "selected_relation_disagreement",
                f"independent relation check disagrees for {selected_row['selected_id']}",
            )
    return stored, response["point_scope_reason"].strip()


def finalize_quotes(
    quote_manifest: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    response: Mapping[str, Any],
    confirmation_manifest: Mapping[str, Any] | None = None,
    confirmation_response: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    manifest_version = _verified_quote_manifest_version(quote_manifest)
    if manifest_version == PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION:
        replay = quote_manifest.get("preselection_replay")
        legacy_replay_keys = {
            "selection_manifest",
            "first_pass_response",
            "confirmation_manifest",
            "confirmation_response",
        }
        batched_replay_keys = {
            "batch_manifest",
            "batch_responses",
            "confirmation_batch_manifest",
            "confirmation_batch_responses",
        }
        replay_keys = frozenset(replay) if isinstance(replay, Mapping) else frozenset()
        if not isinstance(replay, Mapping) or replay_keys not in {
            frozenset(legacy_replay_keys),
            frozenset(batched_replay_keys),
        }:
            raise EvidenceConsumerError(
                "manifest_verification", "preselection replay binding missing"
            )
        if replay_keys == frozenset(legacy_replay_keys):
            _, _, expected_quote_manifest = (
                finalize_preselection_relation_confirmation_prepare_quotes(
                    replay["selection_manifest"],
                    sources,
                    replay["first_pass_response"],
                    replay["confirmation_manifest"],
                    replay["confirmation_response"],
                )
            )
        else:
            _, _, expected_quote_manifest = (
                finalize_batched_preselection_relation_confirmations_prepare_quotes(
                    replay["batch_manifest"],
                    sources,
                    replay["batch_responses"],
                    replay["confirmation_batch_manifest"],
                    replay["confirmation_batch_responses"],
                )
            )
        if dict(quote_manifest) != expected_quote_manifest:
            raise EvidenceConsumerError(
                "manifest_verification", "preselection quote lineage changed"
            )
    confirmation_manifest_sha256 = None
    point_scope_confirmation_reason = None
    if manifest_version == QUOTE_MANIFEST_VERSION:
        if confirmation_manifest is None or confirmation_response is None:
            raise EvidenceConsumerError(
                "selected_relation_confirmation_required",
                "current evidence packs require independent selected-row confirmation",
            )
        (
            confirmation_manifest_sha256,
            point_scope_confirmation_reason,
        ) = _validate_selected_relation_confirmation(
            quote_manifest, confirmation_manifest, confirmation_response
        )
    elif confirmation_manifest is not None or confirmation_response is not None:
        raise EvidenceConsumerError(
            "unexpected_relation_confirmation",
            "historical quote manifests do not accept a confirmation attachment",
        )
    if set(response) != {"quotes"} or not isinstance(response.get("quotes"), list):
        raise EvidenceConsumerError("quote_response_shape", "quotes missing")
    selected = quote_manifest["selected_rows"]
    frontier_relation_ids = quote_manifest.get(
        "frontier_relation_candidate_ids", []
    )
    if not isinstance(frontier_relation_ids, list) or not all(
        isinstance(value, str) for value in frontier_relation_ids
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "frontier relation quote ids are invalid"
        )
    frontier_relation_candidate_ids = frozenset(frontier_relation_ids)
    expected = (
        quote_manifest.get("provider_selected_ids")
        if manifest_version
        in {
            PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
            PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
            QUOTE_MANIFEST_VERSION,
            PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
        }
        else [row["selected_id"] for row in selected]
    )
    if not isinstance(expected, list) or not all(
        isinstance(selected_id, str) for selected_id in expected
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "provider quote ids are invalid"
        )
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
    if manifest_version in {
        PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
        PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
        QUOTE_MANIFEST_VERSION,
        PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
    }:
        derived_provider_ids = [
            row["selected_id"]
            for row in selected
            if (
                (body := bodies.get((row["source_id"], row["evidence_id"])))
                is not None
                and (
                    len(body) > MAX_QUOTE_CHARACTERS
                    or row["candidate_id"] in frontier_relation_candidate_ids
                )
            )
        ]
        if expected != derived_provider_ids:
            raise EvidenceConsumerError(
                "manifest_verification", "provider quote workload changed"
            )
    quote_results = {row["selected_id"]: row for row in quotes}
    output_rows = []
    for selected_row in selected:
        selected_id = selected_row["selected_id"]
        quote_row = quote_results.get(selected_id)
        expected_quote_fields = {"selected_id", "quote_status", "exact_quote"}
        if quote_row is not None and set(quote_row) != expected_quote_fields:
            raise EvidenceConsumerError("quote_response_shape", "quote row shape mismatch")
        body = bodies.get((selected_row["source_id"], selected_row["evidence_id"]))
        if selected_id not in recorded_body_hashes:
            raise EvidenceConsumerError(
                "manifest_verification", f"quote manifest recorded no body hash for {selected_id}"
            )
        if (sha256_text(body) if body is not None else None) != recorded_body_hashes[selected_id]:
            raise EvidenceConsumerError(
                "body_identity_mismatch",
                f"source body changed after the quote manifest was written: {selected_id}",
            )
        if quote_row is None:
            if manifest_version not in {
                PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
                PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
                QUOTE_MANIFEST_VERSION,
                PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
            }:
                raise EvidenceConsumerError(
                    "missing_quote_result", "selected row has no quote result"
                )
            if body is None:
                status = "quote_unavailable"
                quote = None
            elif len(body) <= MAX_QUOTE_CHARACTERS:
                status = "quote_available"
                quote = body
            else:
                raise EvidenceConsumerError(
                    "missing_quote_result", "long source body has no quote result"
                )
        else:
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
            if (
                manifest_version
                in {
                    PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
                    PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
                    QUOTE_MANIFEST_VERSION,
                    PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
                }
                and not _quote_has_complete_end(body, quote)
            ):
                raise EvidenceConsumerError(
                    "quote_boundary_incomplete",
                    "available quote stops before the next source word",
                )
            if len(body) <= MAX_QUOTE_CHARACTERS and quote != body:
                raise EvidenceConsumerError(
                    "quote_context_incomplete",
                    "a short source body must be quoted in full",
                )
        elif status == "quote_unavailable":
            if quote is not None:
                raise EvidenceConsumerError("quote_response_shape", "unavailable quote must be null")
            if (
                body is not None
                and selected_row["candidate_id"]
                in frontier_relation_candidate_ids
            ):
                raise EvidenceConsumerError(
                    "frontier_relation_quote_relevance",
                    "a frontier-defining relation has no relevant exact quote",
                )
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
                    if manifest_version
                    in {
                        PREVIOUS_QUOTE_MANIFEST_VERSION,
                        PRECONFIRMATION_QUOTE_MANIFEST_VERSION,
                        PRECONFIRMATION_BATCHED_QUOTE_MANIFEST_VERSION,
                        QUOTE_MANIFEST_VERSION,
                        PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
                    }
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
    temporal_policy = quote_manifest.get("temporal_presentation_policy")
    if temporal_policy is not None:
        if temporal_policy not in TEMPORAL_PRESENTATION_POLICIES:
            raise EvidenceConsumerError(
                "manifest_verification", "temporal presentation policy changed"
            )
        for rows in grouped.values():
            rows.sort(key=_temporal_display_priority)
    artifact = {
        "schema_version": (
            "phase_a_evidence_selection_artifact_v2"
            if manifest_version
            in {QUOTE_MANIFEST_VERSION, PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION}
            else "phase_a_evidence_selection_artifact_v1"
        ),
        "selection_manifest_sha256": quote_manifest["selection_manifest_sha256"],
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
        "candidate_inventory_sha256": quote_manifest["candidate_inventory_sha256"],
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "candidate_dispositions": quote_manifest["labeled_inventory"],
        "truth_group_cap": quote_manifest.get("truth_group_cap", MAX_TRUTH_GROUPS),
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
    if temporal_policy is not None:
        timeline: dict[int | None, list[str]] = defaultdict(list)
        for row in output_rows:
            timeline[_publication_year(row)].append(row["selected_id"])
        ordered_years = sorted(
            (year for year in timeline if year is not None), reverse=True
        )
        if None in timeline:
            ordered_years.append(None)
        artifact["timeline"] = [
            {
                "calendar_year": year,
                "selected_ids": timeline[year],
            }
            for year in ordered_years
        ]
    if manifest_version in {
        QUOTE_MANIFEST_VERSION,
        PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION,
    }:
        if manifest_version == PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION:
            preselection = quote_manifest.get("preselection_relation_confirmation")
            if (
                not isinstance(preselection, Mapping)
                or preselection.get("status") != "passed"
                or not isinstance(preselection.get("confirmation_manifest_sha256"), str)
                or not isinstance(preselection.get("point_scope_reason"), str)
                or not preselection["point_scope_reason"].strip()
            ):
                raise EvidenceConsumerError(
                    "manifest_verification",
                    "preselection relation confirmation is missing or changed",
                )
            confirmation_manifest_sha256 = preselection[
                "confirmation_manifest_sha256"
            ]
            point_scope_confirmation_reason = preselection[
                "point_scope_reason"
            ].strip()
        labeled_inventory = quote_manifest["labeled_inventory"]
        truth_selection_policy = quote_manifest.get("truth_selection_policy")
        if truth_selection_policy not in {"balanced", "value_first"}:
            raise EvidenceConsumerError(
                "manifest_verification", "truth selection policy missing or changed"
            )
        frontier_relation_policy = quote_manifest.get(
            "frontier_relation_display_policy"
        )
        frontier_relation_ids = quote_manifest.get(
            "frontier_relation_candidate_ids", []
        )
        if (
            frontier_relation_policy not in {None, FRONTIER_RELATION_DISPLAY_POLICY}
            or not isinstance(frontier_relation_ids, list)
            or not all(isinstance(value, str) for value in frontier_relation_ids)
            or (
                frontier_relation_policy is None
                and frontier_relation_ids
            )
        ):
            raise EvidenceConsumerError(
                "manifest_verification",
                "frontier relation display binding changed",
            )
        truth_rows = [
            row
            for row in output_rows
            if row["layer"] == "truth_support"
        ]
        artifact.update(
            {
                "point_id": quote_manifest["selection_id"],
                "bounded_point": quote_manifest["bounded_claim"],
                "relation_confirmation_status": "passed",
                "relation_confirmation_manifest_sha256": confirmation_manifest_sha256,
                "point_scope_confirmation_status": "passed",
                "point_scope_confirmation_reason": point_scope_confirmation_reason,
                "selection_disclosure": {
                    "candidate_semantic_row_count": len(labeled_inventory),
                    "candidate_evidence_item_count": len(
                        {
                            (row["source_id"], row["evidence_id"])
                            for row in labeled_inventory
                        }
                    ),
                    "candidate_truth_origin_count": len(
                        {
                            row["scoped_independence_key"]
                            for row in labeled_inventory
                            if row["layer"] == "truth_support"
                            and row["relation"] != "exclude"
                        }
                    ),
                    "display_eligible_truth_origin_count": len(
                        {
                            row["scoped_independence_key"]
                            for row in labeled_inventory
                            if _truth_row_display_eligible(
                                row,
                                truth_selection_policy,
                                frontier_relation_bound=row["candidate_id"]
                                in frontier_relation_candidate_ids,
                            )
                        }
                    ),
                    "displayed_row_count": len(output_rows),
                    "displayed_truth_origin_count": len(
                        {row["origin_group_id"] for row in truth_rows}
                    ),
                    "displayed_support_origin_count": len(
                        {
                            row["origin_group_id"]
                            for row in truth_rows
                            if row["relation"] == "support"
                        }
                    ),
                    "displayed_counter_origin_count": len(
                        {
                            row["origin_group_id"]
                            for row in truth_rows
                            if row["relation"] == "counter"
                        }
                    ),
                    "displayed_adjacent_origin_count": len(
                        {
                            row["origin_group_id"]
                            for row in truth_rows
                            if row["relation"] == "adjacent"
                        }
                    ),
                    "displayed_influence_origin_count": artifact[
                        "influence_group_count"
                    ],
                    "presentation_basis": [
                        "one externally scope-confirmed evidence point; a broad axis or bundled claim fails before artifact completion",
                        "distinct truth origins capped separately from creator influence",
                        "display_eligible_truth_origin_count is the exact pre-cap origin pool under the recorded truth selection policy; origins outside that pool are not cap omissions",
                        (
                            "a quiet truth origin is display-eligible only when it is operator-protected or literally bound to the accepted frontier point; that visibility grants no resonance credit, and value-first still excludes unbound material adjacent origins"
                            if frontier_relation_candidate_ids
                            else "a truth origin with no operator-protected lane and no material positive source-native engagement is never displayed; value-first also excludes material adjacent origins"
                        ),
                        "support, counterevidence, protected evidence, source diversity, and source-native engagement within comparable buckets",
                        "all admitted candidate dispositions remain available",
                    ],
                },
            }
        )
        if temporal_policy is not None:
            recent_years = quote_manifest.get("recent_calendar_years")
            if (
                not isinstance(recent_years, list)
                or len(recent_years) > RECENT_YEAR_COUNT
                or not all(isinstance(year, int) for year in recent_years)
            ):
                raise EvidenceConsumerError(
                    "manifest_verification", "recent calendar-year binding changed"
                )
            recent_set = set(recent_years)
            artifact["selection_disclosure"].update(
                {
                    "temporal_presentation_policy": temporal_policy,
                    "recent_calendar_years": recent_years,
                    "displayed_recent_truth_origin_count": len(
                        {
                            row["origin_group_id"]
                            for row in truth_rows
                            if _publication_year(row) in recent_set
                        }
                    ),
                    "displayed_dated_pre_window_truth_origin_count": len(
                        {
                            row["origin_group_id"]
                            for row in truth_rows
                            if (year := _publication_year(row)) is not None
                            and recent_years
                            and year < min(recent_years)
                        }
                    ),
                }
            )
            artifact["selection_disclosure"]["presentation_basis"].extend(
                [
                    "recent calendar years receive display representation across available source-native buckets; age never changes a relation or evidentiary weight",
                    "one dated pre-window origin is retained when eligible and cap space permits; undated evidence remains in complete accounting",
                    "timeline groups exact selected rows by calendar year without strong, weak, fresh, or stale judgments",
                ]
            )
        artifact["output_boundary"].append(
            "candidate and displayed counts describe evidence accounting, not customer prevalence"
        )
    return artifact


__all__ = [
    "CUSTOMER_PULL_FRONTIER_VERSION",
    "PRESELECTION_CONFIRMED_QUOTE_MANIFEST_VERSION",
    "QUOTE_MANIFEST_VERSION",
    "SELECTION_MANIFEST_VERSION",
    "SELECTION_SPEC_VERSION",
    "build_customer_pull_point_frontier",
    "finalize_batched_preselection_relation_confirmations_prepare_quotes",
    "finalize_preselection_relation_confirmation_prepare_quotes",
    "finalize_quotes",
    "finalize_relations_prepare_quotes",
    "load_selection_sources",
    "prepare_evidence_selection",
    "prepare_batched_preselection_relation_confirmations",
    "prepare_preselection_relation_confirmation",
    "prepare_selected_relation_confirmation",
    "selection_spec_from_customer_pull_frontier",
    "verify_customer_pull_point_frontier",
]
