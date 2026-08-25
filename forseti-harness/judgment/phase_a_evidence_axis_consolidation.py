"""Origin-normalized presentation over completed Phase A point artifacts.

The view produced here is a derived consumer projection.  It does not relabel,
reselect, or copy the complete candidate inventories owned by the completed
point artifacts.  Instead it verifies those artifacts and their cold source
bindings, stores each selected origin/evidence item once, and preserves the
claim-relative placement needed to reconstruct every displayed point.
"""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from harness_utils import hash_file
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
    _verify_packet,
)
from judgment.phase_a_evidence_selection import (
    PARENT_CONTEXT_POLICY,
    _verify_bundle,
    load_selection_sources,
)


AXIS_PACK_MANIFEST_VERSION = "phase_a_evidence_axis_pack_manifest_v1"
AXIS_PACK_VERSION = "phase_a_evidence_axis_pack_v1"
LEGACY_CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v1"
CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v2"
LEGACY_CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v1"
CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v2"
DOGFOOD_TRUTH_INDEX_VERSION = "phase_a_evidence_axis_dogfood_truth_index_v1"
SOURCE_AXIS_PACK_VERSION = AXIS_PACK_VERSION
LEGACY_HYDRATION_AXIS_PACK_VERSION = "phase_a_hydration_axis_pack_v2"
LEGACY_CONSOLIDATION_POLICY = "origin_normalized_surface_separated_v1"
CONSOLIDATION_POLICY = "point_routed_origin_normalized_surface_separated_v2"
POINT_TRUTH_ORIGIN_CAP = 13
SUPPORTED_QUOTE_MANIFEST_VERSIONS = {
    "phase_a_evidence_quote_manifest_v6",
    "phase_a_evidence_quote_manifest_v7",
    "phase_a_evidence_quote_manifest_v8",
}
INDEPENDENCE_POSTURES = {
    "credited",
    "possible_same_actor",
    "confirmed_same_actor",
    "unavailable",
}
PROJECTION_MODES = {"direct_outcome", "decision_state"}
IMPLEMENTED_PROJECTION_MODES = PROJECTION_MODES
DECISION_STATE_SPEC_FIELDS = {
    "decision_state_bindings",
    "decision_state_bindings_sha256",
    "decision_state_rejected_point_navigation",
}
DIRECT_OUTCOME_RELATION_SPEC_FIELDS = {"direct_outcome_relation_bindings"}
DIRECT_OUTCOME_BOUNDARIES = (
    "not a causal judgment",
    "not a commercial-pull score",
    "creator influence is not customer corroboration",
)
EVIDENCE_ACCOUNTING_CONTRACT = {
    "point_meaning_rule": (
        "bounded_point on each point row is the authoritative admitted meaning, including "
        "literal comparator, time, and personal-fit terms; placement normalized meanings "
        "are point-relative evidence and may support, counter, qualify, or sit adjacent, "
        "but never broaden, merge, or rewrite the point"
    ),
    "displayed_relation_count_rule": (
        "point relation totals count displayed rows, not origins, people, prevalence, or "
        "same-origin observations; they may exceed distinct-origin counts"
    ),
    "independent_origin_rule": (
        "point relation origin-id arrays count distinct evidence origins; multiple source "
        "observations inside one same-origin group never add independent-origin credit"
    ),
    "source_observation_rule": (
        "same_origin_observation_groups preserve every distinct admitted evidence and semantic "
        "unit that matches a displayed point-relative meaning, relation, and origin"
    ),
    "display_scope_rule": (
        "a same-origin observation group explains a displayed fact only; it does not promote "
        "a non-displayed origin or change selection, relation, or evidential authority"
    ),
    "underlying_event_rule": (
        "repeated source observations may be updates or repeated reporting and do not by "
        "themselves establish multiple underlying purchases, uses, completions, or other events"
    ),
}
DECISION_STATE_BOUNDARIES = (
    "decision states are actor-, object-, and stage-specific, not prevalence or market estimates",
    "intent is not observed behavior",
    "multi-unit purchase or ownership is not observed repurchase",
    (
        "keep the source's price comparison visible: 'expensive for a lip balm' is a "
        "category-relative price concern, while 'overpriced' or 'not worth it' requires "
        "an explicit value rejection"
    ),
    (
        "premium describes source-supported quality or positioning, not price alone; "
        "price, value, intent, and behavior do not by themselves prove pricing power or "
        "support for a higher tier"
    ),
    "companion decision states coexist and are not averaged into sentiment",
)
DECISION_STATE_CONSUMER_CONTRACT = {
    "state_tuple_authority": (
        "explicit spec-authored state kind, direction, object, semantic refs, and qualifiers "
        "for a completed point semantic unit"
    ),
    "unasserted_state_rule": (
        "indexed state assertions are exhaustive for delivered decision states; literal quotes and "
        "qualifications may explain asserted states but may not create an additional "
        "purchase, ownership, intent, recurrence, or other decision state"
    ),
    "point_relation_state_rule": (
        "inside each reader point, relation_facts relation_state_row_ids are the exhaustive "
        "zero-based rows in that point's state_table that explain the point-relative relation; "
        "source_context_state_row_ids preserve other co-occurring states from the same literal "
        "source but may not be attached to the relation; relation_semantic_unit_row_ids are "
        "zero-based rows in the reader semantic_unit_table and do not repeat its statements"
    ),
    "placement_processing_rule": (
        "process every placement exactly once through the same consumer join order; "
        "display order is navigation, not importance or evidential rank"
    ),
    "engagement_rule": (
        "retain source-native engagement as descriptive context only; it may not promote "
        "truth, prevalence, recurrence, cross-platform rank, or commercial pull"
    ),
    "coexistence_rule": (
        "report co-occurring states as coexistence only; do not claim that one state "
        "causes, sustains, cancels, or explains another without separate causal authority"
    ),
    "quote_role": (
        "child quotes stay literal; any needed parent comes only from the matching hash-pinned "
        "candidate inventory, never the spec, and is context rather than evidence; source role "
        "and date are unavailable, while venue and surface remain recoverable from source_ref"
    ),
    "companion_rule": (
        "state assertions may overlap semantic-unit refs when one literal source carries "
        "several non-equivalent states"
    ),
    "context_only_row_rule": (
        "a decision-state point may retain a result or other non-state evidence row as "
        "context only; empty state_ids means no judgment, intent, or behavior was "
        "asserted for that placement"
    ),
    "qualification_rule": (
        "resolve every qualification_ref through point_placements semantic_unit_ref into "
        "semantic_unit_table, or through companion_meaning_index -- a context-only row "
        "routinely qualifies its own primary meaning -- and preserve it when material; "
        "it remains context rather than an additional decision state"
    ),
    "consumer_join_order": [
        "decision_state_group placement_id to point_placements",
        "decision_state_group state_ids to decision_state_index",
        "state semantic refs and qualification_refs to primary or companion semantic units",
        "placement evidence_id and quote_span_id to literal source, date, engagement, and quote",
    ],
    "state_row_columns": [
        "state_kind",
        "commercial_direction",
        "decision_object",
        "semantic_unit_refs",
        "quantity",
        "conditions",
    ],
}
DECISION_STATE_READER_CONTRACT_OVERRIDES = {
    "placement_processing_rule": (
        "process every relation_facts selected_id exactly once through the same consumer join "
        "order; display order is navigation, not importance or evidential rank"
    ),
    "context_only_row_rule": (
        "a decision-state point may retain a result or other non-state evidence fact as "
        "context only; empty state row ids mean no judgment, intent, or behavior was asserted"
    ),
    "qualification_rule": (
        "resolve every state_table semantic_unit_row_ids value through the reader "
        "semantic_unit_table; relation_facts context_only_semantic_unit_row_ids directly "
        "bind material qualification preserved as context rather than another decision state"
    ),
    "consumer_join_order": [
        "point_table relation_facts process each selected_id exactly once and evidence_row_id directly selects its zero-based evidence_table row whose evidence_id rechecks identity",
        "relation_facts relation_state_row_ids and source_context_state_row_ids to the enclosing point row state_table, then verify state_binding_sha256",
        "relation_facts primary, companion, relation, context-only, and state semantic-unit row ids to semantic_unit_table; relation and context-only meanings must belong to the primary-plus-companion ownership set",
        "relation_facts quote_row_id directly selects its zero-based quote_table row and quote_span_id rechecks identity; evidence_table carries literal source, date, engagement, and origin_group_id",
        "relation_facts parent_context_row_ids select zero-based parent_context_table rows and parent_context_ids recheck identity; empty arrays mean no parent context is supplied and do not prove self-containment",
    ],
    "state_row_columns": [
        "state_kind",
        "commercial_direction",
        "decision_object",
        "semantic_unit_row_ids",
        "quantity",
        "conditions",
    ],
}
DECISION_STATE_CONTRACT = {
    "value_judgment": {"stages": {"judgment"}, "directions": {"favorable", "unfavorable", "mixed"}},
    "price_concern": {"stages": {"judgment"}, "directions": {"friction"}},
    "buyers_remorse": {"stages": {"judgment"}, "directions": {"unfavorable"}},
    "preference_judgment": {
        "stages": {"judgment"},
        "directions": {"favorable", "unfavorable", "mixed"},
    },
    "expectation_judgment": {
        "stages": {"judgment"},
        "directions": {"favorable", "unfavorable", "mixed"},
    },
    "purchase_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "trial_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "assortment_request": {"stages": {"intent"}, "directions": {"toward_action"}},
    "use_completion_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "repurchase_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "return_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "switching_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "abandonment_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "purchase": {"stages": {"observed"}, "directions": {"neutral"}},
    "observed_repurchase": {"stages": {"observed"}, "directions": {"toward_action"}},
    "multi_unit_purchase": {"stages": {"observed"}, "directions": {"toward_action"}},
    "acquisition": {"stages": {"observed"}, "directions": {"neutral"}},
    "ownership": {"stages": {"observed"}, "directions": {"neutral"}},
    "wear_event": {"stages": {"event"}, "directions": {"neutral"}},
    "ongoing_use": {"stages": {"observed"}, "directions": {"neutral"}},
    "completed_use": {"stages": {"observed"}, "directions": {"neutral"}},
    "observed_return": {"stages": {"observed"}, "directions": {"away_from_action"}},
    "observed_switch": {"stages": {"observed"}, "directions": {"away_from_action"}},
    "observed_abandonment": {"stages": {"observed"}, "directions": {"away_from_action"}},
    "recommendation": {"stages": {"observed"}, "directions": {"favorable", "unfavorable"}},
}
DECISION_STATE_CONSUMER_CONTRACT["state_kind_stages"] = {
    state_kind: next(iter(contract["stages"]))
    for state_kind, contract in DECISION_STATE_CONTRACT.items()
}
DECISION_STATE_ROW_COLUMNS = tuple(DECISION_STATE_CONSUMER_CONTRACT["state_row_columns"])


def _decision_state_reader_contract(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Translate only view-specific join vocabulary into reader-table vocabulary."""

    reader_contract = copy.deepcopy(dict(contract))
    reader_contract.update(copy.deepcopy(DECISION_STATE_READER_CONTRACT_OVERRIDES))
    return reader_contract


def _reader_evidence_accounting_contract() -> dict[str, str]:
    """Preserve the full accounting rules in compact reader wording."""

    reader_contract = {
        "point_meaning_rule": (
            "bounded_point is the sole admitted point meaning; placements may support, "
            "counter, qualify, or sit adjacent but never widen, merge, or rewrite it"
        ),
        "displayed_relation_count_rule": (
            "relation_counts are displayed rows, not origins, people, prevalence, or "
            "same-origin observations; they may exceed origin counts"
        ),
        "independent_origin_rule": (
            "relation origin ids count distinct evidence origins; repeated same-origin "
            "observations add no independent credit"
        ),
        "source_observation_rule": (
            "same_origin_observation_groups retain each distinct admitted evidence and "
            "semantic observation matching the displayed point relation and origin"
        ),
        "display_scope_rule": (
            "same-origin groups explain displayed facts only; they do not promote origins "
            "or alter selection, relation, or authority"
        ),
        "underlying_event_rule": (
            "repeated source observations do not establish multiple underlying events"
        ),
    }
    if set(reader_contract) != set(EVIDENCE_ACCOUNTING_CONTRACT):
        raise EvidenceConsumerError(
            "decision_state_reader_accounting_contract",
            "compact accounting rules do not match authoritative rule identities",
        )
    return reader_contract


def _load_object(path: Path, *, boundary: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceConsumerError(boundary, f"cannot load JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceConsumerError(boundary, f"expected JSON object: {path}")
    return value


def _verify_manifest_hash(
    value: Mapping[str, Any], *, expected: Any, boundary: str
) -> None:
    stored = value.get("manifest_sha256")
    payload = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if not isinstance(stored, str) or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError(boundary, "stored manifest hash is invalid")
    if stored != expected:
        raise EvidenceConsumerError(boundary, "manifest identity differs from point binding")


def _canonical_hash(value: Mapping[str, Any], field: str) -> str:
    return _canonical_json_sha256({key: item for key, item in value.items() if key != field})


def _required_string(value: Mapping[str, Any], key: str, *, boundary: str) -> str:
    observed = value.get(key)
    if not isinstance(observed, str) or not observed:
        raise EvidenceConsumerError(boundary, f"{key} must be a nonempty string")
    return observed


def _string_list(value: Any, *, boundary: str, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise EvidenceConsumerError(boundary, f"{field} must be a string list")
    return list(value)


def _is_truth_support_origin(row: Mapping[str, Any]) -> bool:
    """Only a truth-support row contributes to a truth-origin count.

    Displayed rows carry other layers (creator influence, for example).  Those
    origins remain displayed and counted as origins, but they are not customer
    truth and must never enter a count named for truth support.
    """
    return row.get("layer") == "truth_support" and isinstance(
        row.get("origin_group_id"), str
    )


def _point_rows(artifact: Mapping[str, Any], *, point_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_groups = artifact.get("source_groups")
    if not isinstance(source_groups, list):
        raise EvidenceConsumerError("point_binding", f"source groups invalid: {point_id}")
    for source_group in source_groups:
        if not isinstance(source_group, Mapping) or not isinstance(
            source_group.get("rows"), list
        ):
            raise EvidenceConsumerError("point_binding", f"source group rows invalid: {point_id}")
        for row in source_group["rows"]:
            if not isinstance(row, Mapping):
                raise EvidenceConsumerError("point_binding", f"display row invalid: {point_id}")
            rows.append(dict(row))
    return rows


def _validated_candidate_parent_contexts(
    candidate: Mapping[str, Any], *, point_id: str, selected_id: str
) -> list[dict[str, str]]:
    """Read linked parent context only from the hash-pinned candidate row."""

    raw_contexts = candidate.get("parent_context", [])
    if not isinstance(raw_contexts, list):
        raise EvidenceConsumerError(
            "decision_state_parent_context_binding",
            f"candidate parent contexts are invalid: {point_id}::{selected_id}",
        )
    contexts: list[dict[str, str]] = []
    seen_context_ids: set[str] = set()
    for raw_context in raw_contexts:
        if not isinstance(raw_context, Mapping) or set(raw_context) != {
            "context_id",
            "source_ref",
            "text",
        }:
            raise EvidenceConsumerError(
                "decision_state_parent_context_binding",
                f"candidate parent context fields are invalid: {point_id}::{selected_id}",
            )
        context = {
            field: _required_string(
                raw_context,
                field,
                boundary="decision_state_parent_context_binding",
            )
            for field in ("context_id", "source_ref", "text")
        }
        if context["context_id"] in seen_context_ids:
            raise EvidenceConsumerError(
                "decision_state_parent_context_binding",
                f"candidate parent context is duplicated: {point_id}::{selected_id}",
            )
        seen_context_ids.add(context["context_id"])
        contexts.append(context)
    return contexts


def _validate_point_binding(
    descriptor: Mapping[str, Any], *, expected_axis: str, require_complete_pins: bool
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    point_id = _required_string(descriptor, "point_id", boundary="point_binding")
    bounded_point = _required_string(descriptor, "bounded_point", boundary="point_binding")
    artifact_path = Path(_required_string(descriptor, "artifact_path", boundary="point_binding"))
    expected_artifact_hash = _required_string(
        descriptor, "artifact_sha256", boundary="point_binding"
    )
    if not artifact_path.is_file() or hash_file(artifact_path) != expected_artifact_hash:
        raise EvidenceConsumerError("point_binding", f"point artifact changed: {point_id}")
    artifact = _load_object(artifact_path, boundary="point_binding")
    if artifact.get("point_id") != point_id:
        raise EvidenceConsumerError("point_binding", f"point identity changed: {point_id}")
    if artifact.get("bounded_point") != bounded_point:
        raise EvidenceConsumerError("point_binding", f"bounded point changed: {point_id}")
    if require_complete_pins and artifact.get("schema_version") != (
        "phase_a_evidence_selection_artifact_v2"
    ):
        raise EvidenceConsumerError("point_policy", f"unsupported point artifact: {point_id}")

    candidates = artifact.get("candidate_dispositions")
    if not isinstance(candidates, list) or not candidates:
        raise EvidenceConsumerError("candidate_access", f"candidate inventory missing: {point_id}")
    candidate_ids = [row.get("candidate_id") for row in candidates if isinstance(row, Mapping)]
    if (
        len(candidate_ids) != len(candidates)
        or not all(isinstance(value, str) and value for value in candidate_ids)
        or len(set(candidate_ids)) != len(candidate_ids)
    ):
        raise EvidenceConsumerError("candidate_access", f"candidate identities invalid: {point_id}")
    candidate_by_id = {
        row["candidate_id"]: dict(row) for row in candidates if isinstance(row, Mapping)
    }

    selection_path = Path(
        _required_string(descriptor, "selection_manifest_path", boundary="candidate_access")
    )
    expected_selection_file_hash = _required_string(
        descriptor, "selection_manifest_file_sha256", boundary="candidate_access"
    )
    if (
        not selection_path.is_file()
        or hash_file(selection_path) != expected_selection_file_hash
    ):
        raise EvidenceConsumerError("candidate_access", f"selection manifest changed: {point_id}")
    selection_manifest = _load_object(selection_path, boundary="candidate_access")
    _verify_manifest_hash(
        selection_manifest,
        expected=descriptor.get("selection_manifest_sha256"),
        boundary="candidate_access",
    )
    if selection_manifest.get("candidate_inventory_sha256") != artifact.get(
        "candidate_inventory_sha256"
    ):
        raise EvidenceConsumerError(
            "candidate_access", f"candidate inventory binding changed: {point_id}"
        )
    parent_context_policy = selection_manifest.get("parent_context_policy")
    if parent_context_policy == PARENT_CONTEXT_POLICY:
        source_shaped_candidates = [
            {
                key: copy.deepcopy(value)
                for key, value in candidate.items()
                if key not in {"relation", "reason_code"}
            }
            for candidate in candidates
        ]
        if _canonical_json_sha256(source_shaped_candidates) != selection_manifest.get(
            "candidate_inventory_sha256"
        ):
            raise EvidenceConsumerError(
                "candidate_access",
                f"candidate disposition inventory changed: {point_id}",
            )
    elif any("parent_context" in candidate for candidate in candidates):
        raise EvidenceConsumerError(
            "candidate_access",
            f"candidate parent context lacks a linked source policy: {point_id}",
        )
    selection_spec = selection_manifest.get("spec")
    frontier_binding = (
        selection_spec.get("customer_pull_frontier_binding")
        if isinstance(selection_spec, Mapping)
        else None
    )
    literal_frontier_axis_binding = (
        isinstance(selection_spec, Mapping)
        and selection_spec.get("axis_ids") == []
        and selection_spec.get("relation_response_mode") == "literal_ids"
        and selection_spec.get("relation_policy") == "bounded_point"
        and isinstance(frontier_binding, Mapping)
        and frontier_binding.get("proposition_id") == point_id
        and frontier_binding.get("candidate_admission") == "literal_point_relations"
        and all(
            isinstance(candidate.get("axis_ids"), list)
            and expected_axis in candidate["axis_ids"]
            for candidate in candidate_by_id.values()
        )
    )
    if (
        not isinstance(selection_spec, Mapping)
        or (
            selection_spec.get("axis_ids") != [expected_axis]
            and not literal_frontier_axis_binding
        )
    ):
        raise EvidenceConsumerError("candidate_access", f"axis binding changed: {point_id}")
    sources = load_selection_sources(selection_manifest)
    for source in sources:
        packet = source.get("packet")
        bundle = source.get("bundle")
        if not isinstance(packet, Mapping) or not isinstance(bundle, Mapping):
            raise EvidenceConsumerError("source_binding", f"source binding invalid: {point_id}")
        _verify_packet(packet)
        _verify_bundle(bundle)
        if packet.get("source_bindings", {}).get("bundle_sha256") != bundle.get(
            "bundle_sha256"
        ):
            raise EvidenceConsumerError(
                "source_binding", f"packet/bundle binding changed: {point_id}"
            )

    quote_path = Path(
        _required_string(descriptor, "quote_manifest_path", boundary="quote_binding")
    )
    if require_complete_pins:
        expected_quote_file_hash = _required_string(
            descriptor, "quote_manifest_file_sha256", boundary="quote_binding"
        )
        if not quote_path.is_file() or hash_file(quote_path) != expected_quote_file_hash:
            raise EvidenceConsumerError("quote_binding", f"quote manifest changed: {point_id}")
    elif not quote_path.is_file():
        raise EvidenceConsumerError("quote_binding", f"quote manifest missing: {point_id}")
    else:
        expected_quote_file_hash = hash_file(quote_path)
    quote_manifest = _load_object(quote_path, boundary="quote_binding")
    _verify_manifest_hash(
        quote_manifest,
        expected=descriptor.get("quote_manifest_sha256"),
        boundary="quote_binding",
    )
    if quote_manifest.get("schema_version") not in SUPPORTED_QUOTE_MANIFEST_VERSIONS:
        raise EvidenceConsumerError("quote_binding", f"unsupported quote policy: {point_id}")
    if quote_manifest.get("selection_manifest_sha256") != artifact.get(
        "selection_manifest_sha256"
    ):
        raise EvidenceConsumerError("quote_binding", f"quote lineage changed: {point_id}")
    if quote_manifest.get("candidate_inventory_sha256") not in {
        None,
        artifact.get("candidate_inventory_sha256"),
    }:
        raise EvidenceConsumerError(
            "quote_binding", f"quote candidate binding changed: {point_id}"
        )
    if artifact.get("quote_manifest_sha256") not in {
        None,
        quote_manifest.get("manifest_sha256"),
    }:
        raise EvidenceConsumerError("quote_binding", f"artifact quote binding changed: {point_id}")

    if require_complete_pins:
        if artifact.get("truth_group_cap") != POINT_TRUTH_ORIGIN_CAP:
            raise EvidenceConsumerError(
                "point_policy", f"truth origin cap must be {POINT_TRUTH_ORIGIN_CAP}: {point_id}"
            )
        if artifact.get("selection_manifest_sha256") != selection_manifest.get(
            "manifest_sha256"
        ):
            raise EvidenceConsumerError(
                "point_policy", f"artifact selection binding changed: {point_id}"
            )
        artifact_policy = artifact.get("policy_revision")
        if artifact_policy is not None and artifact_policy != descriptor.get("policy_revision"):
            raise EvidenceConsumerError("point_policy", f"policy lineage changed: {point_id}")

    rows = _point_rows(artifact, point_id=point_id)
    for row in rows:
        origin_candidate_ids = row.get("origin_candidate_ids")
        if (
            not isinstance(origin_candidate_ids, list)
            or not origin_candidate_ids
            or not all(candidate_id in candidate_by_id for candidate_id in origin_candidate_ids)
        ):
            raise EvidenceConsumerError(
                "point_binding", f"display candidate missing: {point_id}"
            )
        matching = [
            candidate_by_id[candidate_id]
            for candidate_id in origin_candidate_ids
            if candidate_by_id[candidate_id].get("evidence_id") == row.get("evidence_id")
            and candidate_by_id[candidate_id].get("semantic_unit_ref")
            == row.get("semantic_unit_ref")
        ]
        if len(matching) != 1 or matching[0].get("relation") != row.get("relation"):
            raise EvidenceConsumerError(
                "point_binding", f"display relation binding changed: {point_id}"
            )
        _validated_candidate_parent_contexts(
            matching[0],
            point_id=point_id,
            selected_id=_required_string(
                row, "selected_id", boundary="decision_state_parent_context_binding"
            ),
        )
    truth_origins = {
        row["origin_group_id"] for row in rows if _is_truth_support_origin(row)
    }
    if artifact.get("truth_group_count") != len(truth_origins):
        raise EvidenceConsumerError("point_policy", f"truth origin count changed: {point_id}")
    if len(truth_origins) > POINT_TRUTH_ORIGIN_CAP:
        raise EvidenceConsumerError("point_policy", f"truth origin cap exceeded: {point_id}")
    if require_complete_pins:
        disclosure = artifact.get("selection_disclosure")
        if (
            artifact.get("relation_confirmation_status") != "passed"
            or artifact.get("point_scope_confirmation_status") != "passed"
            or not isinstance(artifact.get("point_scope_confirmation_reason"), str)
            or not artifact["point_scope_confirmation_reason"].strip()
            or not isinstance(disclosure, Mapping)
            or disclosure.get("candidate_semantic_row_count") != len(candidates)
            or disclosure.get("displayed_row_count") != len(rows)
            or disclosure.get("displayed_truth_origin_count") != len(truth_origins)
        ):
            raise EvidenceConsumerError(
                "point_policy", f"point completion policy changed: {point_id}"
            )

    relation_counts = {"support": 0, "counter": 0, "adjacent": 0}
    for row in rows:
        relation = row.get("relation")
        if relation not in relation_counts:
            raise EvidenceConsumerError("point_binding", f"displayed relation invalid: {point_id}")
        relation_counts[relation] += 1
    descriptor_out = {
        "point_id": point_id,
        "bounded_point": bounded_point,
        "artifact_path": str(artifact_path),
        "artifact_sha256": expected_artifact_hash,
        "candidate_count": len(candidates),
        "display_row_count": len(rows),
        "truth_origin_count": len(truth_origins),
        "relation_counts": relation_counts,
        "policy_revision": _required_string(
            descriptor, "policy_revision", boundary="point_policy"
        ),
        "policy_lineage": {
            "artifact_schema_version": artifact.get("schema_version"),
            "selection_manifest_schema_version": selection_manifest.get("schema_version"),
            "quote_manifest_schema_version": quote_manifest.get("schema_version"),
        },
        "selection_manifest_path": str(selection_path),
        "selection_manifest_file_sha256": expected_selection_file_hash,
        "selection_manifest_sha256": selection_manifest["manifest_sha256"],
        "quote_manifest_path": str(quote_path),
        "quote_manifest_file_sha256": expected_quote_file_hash,
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
    }
    bindings = {
        key: descriptor_out[key]
        for key in (
            "artifact_path",
            "artifact_sha256",
            "selection_manifest_path",
            "selection_manifest_file_sha256",
            "selection_manifest_sha256",
            "quote_manifest_path",
            "quote_manifest_file_sha256",
            "quote_manifest_sha256",
        )
    }
    return artifact, candidate_by_id, {"descriptor": descriptor_out, "bindings": bindings}


def build_phase_a_evidence_axis_pack(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build a generic, cold-resolvable Phase A axis pack from explicit pins."""

    if manifest.get("schema_version") != AXIS_PACK_MANIFEST_VERSION:
        raise EvidenceConsumerError("axis_manifest", "unsupported axis manifest version")
    if set(manifest) != {
        "schema_version",
        "axis_id",
        "accepted_points",
        "rejected_points",
        "manifest_sha256",
    }:
        raise EvidenceConsumerError("axis_manifest", "axis manifest fields are invalid")
    stored_manifest_hash = manifest.get("manifest_sha256")
    if not isinstance(stored_manifest_hash, str) or stored_manifest_hash != _canonical_hash(
        manifest, "manifest_sha256"
    ):
        raise EvidenceConsumerError("axis_manifest", "stored manifest hash is invalid")
    axis_id = _required_string(manifest, "axis_id", boundary="axis_manifest")
    accepted = manifest.get("accepted_points")
    rejected = manifest.get("rejected_points")
    if not isinstance(accepted, list):
        raise EvidenceConsumerError("axis_manifest", "accepted_points must be explicit")
    if not isinstance(rejected, list):
        raise EvidenceConsumerError("axis_manifest", "rejected_points must be explicit")
    if not accepted and not rejected:
        raise EvidenceConsumerError(
            "axis_manifest", "the accepted/rejected frontier must be nonempty"
        )

    accepted_ids = [row.get("point_id") for row in accepted if isinstance(row, Mapping)]
    if (
        len(accepted_ids) != len(accepted)
        or not all(isinstance(value, str) and value for value in accepted_ids)
        or len(set(accepted_ids)) != len(accepted_ids)
    ):
        raise EvidenceConsumerError("axis_manifest", "accepted point identities are invalid")
    accepted_fields = {
        "point_id",
        "bounded_point",
        "artifact_path",
        "artifact_sha256",
        "policy_revision",
        "selection_manifest_path",
        "selection_manifest_file_sha256",
        "selection_manifest_sha256",
        "quote_manifest_path",
        "quote_manifest_file_sha256",
        "quote_manifest_sha256",
    }
    if any(set(row) != accepted_fields for row in accepted):
        raise EvidenceConsumerError("axis_manifest", "accepted point pins are incomplete")
    rejected_rows: list[dict[str, str]] = []
    rejected_ids: list[str] = []
    rejected_receipt_count = 0
    rejected_base_fields = {"point_id", "bounded_point", "disposition", "reason"}
    rejected_receipt_fields = {
        "resolution_receipt_path",
        "resolution_receipt_sha256",
    }
    for row in rejected:
        if not isinstance(row, Mapping):
            raise EvidenceConsumerError("axis_manifest", "rejected point must be an object")
        row_fields = frozenset(row)
        if row_fields not in {
            frozenset(rejected_base_fields),
            frozenset(rejected_base_fields | rejected_receipt_fields),
        }:
            raise EvidenceConsumerError("axis_manifest", "rejected point fields are invalid")
        point_id = _required_string(row, "point_id", boundary="axis_manifest")
        rejected_ids.append(point_id)
        normalized_rejected = {
            "point_id": point_id,
            "bounded_point": _required_string(row, "bounded_point", boundary="axis_manifest"),
            "disposition": _required_string(row, "disposition", boundary="axis_manifest"),
            "reason": _required_string(row, "reason", boundary="axis_manifest"),
        }
        if row_fields == frozenset(rejected_base_fields | rejected_receipt_fields):
            receipt_path = Path(
                _required_string(
                    row, "resolution_receipt_path", boundary="axis_manifest"
                )
            )
            receipt_sha256 = _required_string(
                row, "resolution_receipt_sha256", boundary="axis_manifest"
            )
            if not receipt_path.is_file() or hash_file(receipt_path) != receipt_sha256:
                raise EvidenceConsumerError(
                    "rejected_point_resolution",
                    f"rejected-point receipt changed: {point_id}",
                )
            receipt = _load_object(
                receipt_path, boundary="rejected_point_resolution"
            )
            if (
                receipt.get("schema_version")
                != "phase_a_rejected_point_resolution_receipt_v1"
                or receipt.get("point_id") != point_id
                or not isinstance(receipt.get("failure_boundary"), str)
                or not receipt["failure_boundary"]
            ):
                raise EvidenceConsumerError(
                    "rejected_point_resolution",
                    f"rejected-point receipt does not resolve this point: {point_id}",
                )
            normalized_rejected.update(
                {
                    "resolution_receipt_path": str(receipt_path),
                    "resolution_receipt_sha256": receipt_sha256,
                }
            )
            rejected_receipt_count += 1
        rejected_rows.append(normalized_rejected)
    if len(set(rejected_ids)) != len(rejected_ids):
        raise EvidenceConsumerError("axis_manifest", "rejected point identities are invalid")
    overlap = set(accepted_ids) & set(rejected_ids)
    if overlap:
        raise EvidenceConsumerError(
            "axis_manifest", f"accepted/rejected point overlap: {sorted(overlap)}"
        )
    if not accepted and rejected_receipt_count != len(rejected_rows):
        raise EvidenceConsumerError(
            "rejected_point_resolution",
            "a rejected-only axis requires one literal resolution receipt per point",
        )

    point_descriptors: list[dict[str, Any]] = []
    unique_truth_origins: set[str] = set()
    unique_evidence: set[str] = set()
    candidate_total = 0
    display_total = 0
    for descriptor in accepted:
        artifact, _, checked = _validate_point_binding(
            descriptor, expected_axis=axis_id, require_complete_pins=True
        )
        normalized = checked["descriptor"]
        point_descriptors.append(normalized)
        candidate_total += normalized["candidate_count"]
        display_total += normalized["display_row_count"]
        for row in _point_rows(artifact, point_id=normalized["point_id"]):
            unique_evidence.add(row["evidence_id"])
            if _is_truth_support_origin(row):
                unique_truth_origins.add(row["origin_group_id"])

    pack: dict[str, Any] = {
        "schema_version": AXIS_PACK_VERSION,
        "status": (
            "complete_valid_axis_pack"
            if point_descriptors
            else "complete_rejected_axis_pack"
        ),
        "axis_id": axis_id,
        "source_manifest": {
            "schema_version": AXIS_PACK_MANIFEST_VERSION,
            "manifest_sha256": stored_manifest_hash,
        },
        "valid_point_count": len(point_descriptors),
        "rejected_point_count": len(rejected_rows),
        "frontier_point_count": len(point_descriptors) + len(rejected_rows),
        "display_row_slots": display_total,
        "unique_truth_origins_across_axis": len(unique_truth_origins),
        "unique_evidence_items_across_axis": len(unique_evidence),
        "cold_reader_resolution": {
            "resolved_candidate_disposition_count": candidate_total,
            "path_resolution": "explicit_manifest_paths_only",
        },
        "points": point_descriptors,
        "rejected_points": rejected_rows,
        "non_claims": [
            "the axis pack does not change point selection, relation, quote, packet, or bundle authority",
            "rejected points are frontier closure dispositions, not evidence exclusions",
            "origin counts are evidence-origin groups, not people or prevalence",
        ],
    }
    if rejected_receipt_count:
        pack["cold_reader_resolution"]["rejected_resolution_receipt_count"] = (
            rejected_receipt_count
        )
    pack["axis_pack_sha256"] = _canonical_hash(pack, "axis_pack_sha256")
    return pack


def validate_phase_a_evidence_axis_pack(
    pack: Mapping[str, Any], *, expected_axis_pack_sha256: str
) -> dict[str, Any]:
    """Validate a saved generic axis pack against an externally pinned identity."""

    if pack.get("schema_version") != AXIS_PACK_VERSION:
        raise EvidenceConsumerError("axis_pack_verification", "unsupported axis pack version")
    stored = pack.get("axis_pack_sha256")
    if stored != expected_axis_pack_sha256:
        raise EvidenceConsumerError(
            "axis_pack_verification", "trusted axis pack identity differs from saved pack"
        )
    if not isinstance(stored, str) or stored != _canonical_hash(pack, "axis_pack_sha256"):
        raise EvidenceConsumerError("axis_pack_verification", "stored axis pack hash is invalid")
    source_manifest = pack.get("source_manifest")
    points = pack.get("points")
    rejected = pack.get("rejected_points")
    if (
        not isinstance(source_manifest, Mapping)
        or source_manifest.get("schema_version") != AXIS_PACK_MANIFEST_VERSION
        or not isinstance(source_manifest.get("manifest_sha256"), str)
        or not isinstance(points, list)
        or not isinstance(rejected, list)
        or (not points and not rejected)
        or not all(isinstance(row, Mapping) for row in points)
        or not all(isinstance(row, Mapping) for row in rejected)
    ):
        raise EvidenceConsumerError("axis_pack_verification", "axis pack closure is invalid")
    manifest: dict[str, Any] = {
        "schema_version": AXIS_PACK_MANIFEST_VERSION,
        "axis_id": pack.get("axis_id"),
        "accepted_points": [
            {
                key: row[key]
                for key in (
                    "point_id",
                    "bounded_point",
                    "artifact_path",
                    "artifact_sha256",
                    "policy_revision",
                    "selection_manifest_path",
                    "selection_manifest_file_sha256",
                    "selection_manifest_sha256",
                    "quote_manifest_path",
                    "quote_manifest_file_sha256",
                    "quote_manifest_sha256",
                )
            }
            for row in points
            if isinstance(row, Mapping)
        ],
        "rejected_points": copy.deepcopy(rejected),
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest, "manifest_sha256")
    if manifest["manifest_sha256"] != source_manifest["manifest_sha256"]:
        raise EvidenceConsumerError("axis_pack_verification", "source manifest identity changed")
    rebuilt = build_phase_a_evidence_axis_pack(manifest)
    if rebuilt != dict(pack):
        raise EvidenceConsumerError(
            "axis_pack_reprojection", "saved axis pack differs from deterministic source projection"
        )
    return rebuilt


def _publication_year(value: Any) -> int | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).year
    except ValueError:
        return None


def _content_surface(row: Mapping[str, Any]) -> tuple[str, str]:
    venue = _required_string(row, "source_venue", boundary="content_surface")
    role = _required_string(row, "source_role", boundary="content_surface")
    evidence_id = _required_string(row, "evidence_id", boundary="content_surface")
    source_ref = _required_string(row, "source_ref", boundary="content_surface")
    if venue == "reddit":
        parts = evidence_id.split(":")
        if len(parts) != 3 or parts[0] != "reddit" or not parts[1] or not parts[2]:
            raise EvidenceConsumerError(
                "content_surface", "Reddit evidence identity cannot distinguish post/comment"
            )
        path_parts = [part for part in urlparse(source_ref).path.split("/") if part]
        try:
            comments_index = path_parts.index("comments")
        except ValueError as exc:
            raise EvidenceConsumerError(
                "content_surface", "Reddit source reference has no comments path"
            ) from exc
        if (
            comments_index + 1 >= len(path_parts)
            or path_parts[comments_index + 1] != parts[1]
        ):
            raise EvidenceConsumerError(
                "content_surface", "Reddit thread identity is absent from its source reference"
            )
        if parts[2] == "post":
            # A thread permalink carries at most the slug after the thread id;
            # any further segment is a comment id, whatever the marker claims.
            if len(path_parts[comments_index + 2 :]) > 1:
                raise EvidenceConsumerError(
                    "content_surface", "Reddit post identity conflicts with comment URL"
                )
            return "reddit_post", "reddit_evidence_id_post_marker"
        if parts[2] not in path_parts[comments_index + 2 :]:
            raise EvidenceConsumerError(
                "content_surface", "Reddit comment identity is absent from its source reference"
            )
        return "reddit_comment", "reddit_evidence_id_comment_marker"
    if role == "retailer_review":
        return f"{venue}_review", "source_role_and_venue"
    if role == "audience_comment":
        return f"{venue}_audience_comment", "source_role_and_venue"
    if role == "creator_authored":
        return f"{venue}_creator_post", "source_role_and_venue"
    if role == "community_post":
        return f"{venue}_community_post", "source_role_and_venue"
    raise EvidenceConsumerError(
        "content_surface", f"unsupported source role for presentation: {role}"
    )


def _navigation_groups(
    spec: Mapping[str, Any], point_ids: set[str]
) -> tuple[list[dict[str, Any]], dict[str, tuple[str, str]]]:
    groups = spec.get("navigation_groups")
    if not isinstance(groups, list) or not groups:
        raise EvidenceConsumerError("navigation_spec", "navigation_groups must be nonempty")
    normalized: list[dict[str, Any]] = []
    placement: dict[str, tuple[str, str]] = {}
    seen_groups: set[str] = set()
    seen_families: set[str] = set()
    for group in groups:
        if not isinstance(group, Mapping):
            raise EvidenceConsumerError("navigation_spec", "group must be an object")
        group_id = _required_string(group, "group_id", boundary="navigation_spec")
        label = _required_string(group, "label", boundary="navigation_spec")
        if group_id in seen_groups:
            raise EvidenceConsumerError("navigation_spec", "duplicate group_id")
        seen_groups.add(group_id)
        families = group.get("families")
        if not isinstance(families, list) or not families:
            raise EvidenceConsumerError("navigation_spec", f"{group_id} has no families")
        normalized_families = []
        for family in families:
            if not isinstance(family, Mapping):
                raise EvidenceConsumerError("navigation_spec", "family must be an object")
            family_id = _required_string(family, "family_id", boundary="navigation_spec")
            family_label = _required_string(family, "label", boundary="navigation_spec")
            family_points = _string_list(
                family.get("point_ids"), boundary="navigation_spec", field="point_ids"
            )
            if not family_points:
                raise EvidenceConsumerError("navigation_spec", f"{family_id} has no points")
            if family_id in seen_families:
                raise EvidenceConsumerError("navigation_spec", "duplicate family_id")
            seen_families.add(family_id)
            for point_id in family_points:
                if point_id not in point_ids:
                    raise EvidenceConsumerError(
                        "navigation_spec", f"unknown point_id in navigation: {point_id}"
                    )
                if point_id in placement:
                    raise EvidenceConsumerError(
                        "navigation_spec", f"point_id appears more than once: {point_id}"
                    )
                placement[point_id] = (group_id, family_id)
            normalized_families.append(
                {
                    "family_id": family_id,
                    "label": family_label,
                    "point_ids": family_points,
                }
            )
        normalized.append(
            {"group_id": group_id, "label": label, "families": normalized_families}
        )
    if set(placement) != point_ids:
        missing = sorted(point_ids - set(placement))
        raise EvidenceConsumerError(
            "navigation_spec", f"navigation does not cover every point: {missing}"
        )
    return normalized, placement


def _projection_routes(
    spec: Mapping[str, Any], point_ids: set[str]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Require one explicit projection route for every v2 point."""

    routes = spec.get("projection_routes")
    if not isinstance(routes, list) or not routes:
        raise EvidenceConsumerError(
            "projection_routing", "projection_routes must be nonempty"
        )
    normalized: list[dict[str, Any]] = []
    placement: dict[str, str] = {}
    seen_modes: set[str] = set()
    for route in routes:
        if not isinstance(route, Mapping):
            raise EvidenceConsumerError("projection_routing", "route must be an object")
        mode = _required_string(route, "projection_mode", boundary="projection_routing")
        route_points = _string_list(
            route.get("point_ids"), boundary="projection_routing", field="point_ids"
        )
        if mode not in PROJECTION_MODES:
            raise EvidenceConsumerError(
                "projection_routing", f"unsupported projection mode: {mode}"
            )
        if mode in seen_modes:
            raise EvidenceConsumerError(
                "projection_routing", f"duplicate projection mode: {mode}"
            )
        if not route_points:
            raise EvidenceConsumerError(
                "projection_routing", f"projection route has no points: {mode}"
            )
        seen_modes.add(mode)
        for point_id in route_points:
            if point_id not in point_ids:
                raise EvidenceConsumerError(
                    "projection_routing", f"unknown point_id in projection route: {point_id}"
                )
            if point_id in placement:
                raise EvidenceConsumerError(
                    "projection_routing", f"point_id appears more than once: {point_id}"
                )
            placement[point_id] = mode
        normalized.append({"projection_mode": mode, "point_ids": route_points})
    if set(placement) != point_ids:
        missing = sorted(point_ids - set(placement))
        raise EvidenceConsumerError(
            "projection_routing", f"projection routes do not cover every point: {missing}"
        )
    unimplemented = sorted(set(placement.values()) - IMPLEMENTED_PROJECTION_MODES)
    if unimplemented:
        raise EvidenceConsumerError(
            "projection_routing",
            f"projection mode is routed but not implemented: {unimplemented[0]}",
        )
    return normalized, placement


def _decision_state_bindings(
    spec: Mapping[str, Any], point_projections: Mapping[str, str]
) -> dict[str, dict[str, Mapping[str, Any]]]:
    """Bind every displayed Decision State row without inferring from point text."""

    decision_point_ids = {
        point_id
        for point_id, projection_mode in point_projections.items()
        if projection_mode == "decision_state"
    }
    raw_bindings = spec.get("decision_state_bindings")
    if not decision_point_ids:
        if raw_bindings not in (None, []):
            raise EvidenceConsumerError(
                "decision_state_binding",
                "decision_state_bindings supplied without a decision_state route",
            )
        return {}
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise EvidenceConsumerError(
            "decision_state_binding",
            "decision_state_bindings must cover every decision_state point",
        )

    normalized: dict[str, dict[str, Mapping[str, Any]]] = {}
    for raw_point in raw_bindings:
        if not isinstance(raw_point, Mapping) or set(raw_point) != {"point_id", "rows"}:
            raise EvidenceConsumerError(
                "decision_state_binding", "point binding fields are invalid"
            )
        point_id = _required_string(
            raw_point, "point_id", boundary="decision_state_binding"
        )
        if point_id not in decision_point_ids:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"binding targets a non-decision-state point: {point_id}",
            )
        if point_id in normalized:
            raise EvidenceConsumerError(
                "decision_state_binding", f"duplicate point binding: {point_id}"
            )
        raw_rows = raw_point.get("rows")
        if not isinstance(raw_rows, list) or not raw_rows:
            raise EvidenceConsumerError(
                "decision_state_binding", f"point binding has no rows: {point_id}"
            )
        rows: dict[str, Mapping[str, Any]] = {}
        for raw_row in raw_rows:
            required_row_fields = {
                "selected_id",
                "state_assertions",
                "context_only_semantic_unit_refs",
                "relation_semantic_unit_refs",
            }
            if not isinstance(raw_row, Mapping) or set(raw_row) != required_row_fields:
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    f"row binding fields are invalid: {point_id}",
                )
            selected_id = _required_string(
                raw_row, "selected_id", boundary="decision_state_binding"
            )
            if selected_id in rows:
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    f"duplicate row binding: {point_id}::{selected_id}",
                )
            rows[selected_id] = dict(raw_row)
        normalized[point_id] = rows

    if set(normalized) != decision_point_ids:
        missing = sorted(decision_point_ids - set(normalized))
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"decision-state bindings do not cover every routed point: {missing}",
        )
    return normalized


def _direct_outcome_relation_bindings(
    spec: Mapping[str, Any], point_projections: Mapping[str, str]
) -> dict[str, dict[str, list[str]]]:
    """Optionally bind the point-relative meaning when a Direct Outcome row's primary is context."""

    raw_bindings = spec.get("direct_outcome_relation_bindings")
    if raw_bindings is None:
        return {}
    direct_point_ids = {
        point_id
        for point_id, projection_mode in point_projections.items()
        if projection_mode == "direct_outcome"
    }
    if not direct_point_ids:
        raise EvidenceConsumerError(
            "direct_outcome_relation_binding",
            "direct-outcome relation bindings supplied without a direct_outcome route",
        )
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise EvidenceConsumerError(
            "direct_outcome_relation_binding", "direct-outcome relation bindings are invalid"
        )
    normalized: dict[str, dict[str, list[str]]] = {}
    for raw_point in raw_bindings:
        if not isinstance(raw_point, Mapping) or set(raw_point) != {"point_id", "rows"}:
            raise EvidenceConsumerError(
                "direct_outcome_relation_binding", "point binding fields are invalid"
            )
        point_id = _required_string(
            raw_point, "point_id", boundary="direct_outcome_relation_binding"
        )
        if point_id not in direct_point_ids or point_id in normalized:
            raise EvidenceConsumerError(
                "direct_outcome_relation_binding", f"invalid bound point: {point_id}"
            )
        rows: dict[str, list[str]] = {}
        raw_rows = raw_point.get("rows")
        if not isinstance(raw_rows, list) or not raw_rows:
            raise EvidenceConsumerError(
                "direct_outcome_relation_binding", f"point binding has no rows: {point_id}"
            )
        for raw_row in raw_rows:
            if not isinstance(raw_row, Mapping) or set(raw_row) != {
                "selected_id",
                "relation_semantic_unit_refs",
            }:
                raise EvidenceConsumerError(
                    "direct_outcome_relation_binding", f"row binding fields are invalid: {point_id}"
                )
            selected_id = _required_string(
                raw_row, "selected_id", boundary="direct_outcome_relation_binding"
            )
            refs = _string_list(
                raw_row.get("relation_semantic_unit_refs"),
                boundary="direct_outcome_relation_binding",
                field="relation_semantic_unit_refs",
            )
            if selected_id in rows or not refs or len(refs) != len(set(refs)):
                raise EvidenceConsumerError(
                    "direct_outcome_relation_binding", f"invalid row binding: {point_id}::{selected_id}"
                )
            rows[selected_id] = sorted(refs)
        normalized[point_id] = rows
    return normalized


def _decision_state_group(
    *,
    point_id: str,
    row: Mapping[str, Any],
    placement: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one spec-authored row state and emit a canonical state group."""

    selected_id = placement["selected_id"]
    primary_ref = _required_string(row, "semantic_unit_ref", boundary="decision_state_binding")
    companion_refs = set(placement["same_evidence_companion_meaning_refs"])
    available_refs = companion_refs | {primary_ref}
    context_refs = _string_list(
        binding.get("context_only_semantic_unit_refs"),
        boundary="decision_state_binding",
        field="context_only_semantic_unit_refs",
    )
    if len(context_refs) != len(set(context_refs)):
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"duplicate context semantic ref: {point_id}::{selected_id}",
        )
    relation_refs = _string_list(
        binding.get("relation_semantic_unit_refs"),
        boundary="decision_state_binding",
        field="relation_semantic_unit_refs",
    )
    if not relation_refs or len(relation_refs) != len(set(relation_refs)):
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"relation semantic refs are empty or duplicated: {point_id}::{selected_id}",
        )

    raw_assertions = binding.get("state_assertions")
    if not isinstance(raw_assertions, list):
        raise EvidenceConsumerError(
            "decision_state_binding", f"row state assertions are invalid: {point_id}::{selected_id}"
        )
    assertions: list[dict[str, Any]] = []
    asserted_refs: set[str] = set()
    assertion_ids: set[str] = set()
    required_fields = {
        "state_kind",
        "commercial_direction",
        "decision_object",
        "semantic_unit_refs",
        "quantity",
        "conditions",
    }
    for raw_assertion in raw_assertions:
        if not isinstance(raw_assertion, Mapping) or set(raw_assertion) != required_fields:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"state assertion fields are invalid: {point_id}::{selected_id}",
            )
        state_kind = _required_string(
            raw_assertion, "state_kind", boundary="decision_state_binding"
        )
        direction = _required_string(
            raw_assertion, "commercial_direction", boundary="decision_state_binding"
        )
        decision_object = _required_string(
            raw_assertion, "decision_object", boundary="decision_state_binding"
        )
        contract = DECISION_STATE_CONTRACT.get(state_kind)
        if contract is None:
            raise EvidenceConsumerError(
                "decision_state_binding", f"unsupported decision state: {state_kind}"
            )
        if direction not in contract["directions"]:
            raise EvidenceConsumerError(
                "decision_state_transition",
                f"invalid state/direction: {point_id}::{selected_id}::{state_kind}",
            )
        stage = next(iter(contract["stages"]))
        semantic_refs = _string_list(
            raw_assertion.get("semantic_unit_refs"),
            boundary="decision_state_binding",
            field="semantic_unit_refs",
        )
        if not semantic_refs or len(semantic_refs) != len(set(semantic_refs)):
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"state semantic refs are empty or duplicated: {point_id}::{selected_id}",
            )
        conditions = _string_list(
            raw_assertion.get("conditions"),
            boundary="decision_state_binding",
            field="conditions",
        )
        if len(conditions) != len(set(conditions)):
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"state conditions are duplicated: {point_id}::{selected_id}",
            )
        quantity = raw_assertion.get("quantity")
        if state_kind == "multi_unit_purchase":
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 2:
                raise EvidenceConsumerError(
                    "decision_state_transition",
                    f"multi-unit purchase requires quantity >= 2: {point_id}::{selected_id}",
                )
        elif quantity is not None:
            raise EvidenceConsumerError(
                "decision_state_transition",
                f"quantity is valid only for multi-unit purchase: {point_id}::{selected_id}",
            )
        normalized = {
            "state_kind": state_kind,
            "stage": stage,
            "commercial_direction": direction,
            "decision_object": decision_object,
            "semantic_unit_refs": sorted(semantic_refs),
            "quantity": quantity,
            "conditions": sorted(conditions),
        }
        assertion_id = "decision_state_" + _canonical_json_sha256(normalized)[:24]
        if assertion_id in assertion_ids:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"duplicate state assertion: {point_id}::{selected_id}",
            )
        assertion_ids.add(assertion_id)
        asserted_refs.update(semantic_refs)
        assertions.append({"decision_state_id": assertion_id, **normalized})

    context_ref_set = set(context_refs)
    if asserted_refs - available_refs or context_ref_set - available_refs:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"state binding references foreign semantic unit: {point_id}::{selected_id}",
        )
    if set(relation_refs) - available_refs:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"relation binding references foreign semantic unit: {point_id}::{selected_id}",
        )
    if asserted_refs & context_ref_set:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"state and context semantic refs overlap: {point_id}::{selected_id}",
        )
    if asserted_refs | context_ref_set != available_refs:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"state binding does not cover every semantic unit: {point_id}::{selected_id}",
        )
    if not assertions and context_ref_set != available_refs:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"context-only row does not cover every semantic unit: {point_id}::{selected_id}",
        )

    group_id = f"decision_state_group_{_canonical_json_sha256([point_id, selected_id])[:24]}"
    return {
        "decision_state_group_id": group_id,
        "point_id": point_id,
        "selected_id": selected_id,
        "placement_id": placement["placement_id"],
        "origin_group_id": placement["origin_group_id"],
        "evidence_id": placement["evidence_id"],
        "relation": placement["relation"],
        "layer": placement["layer"],
        "state_assertions": sorted(assertions, key=lambda item: item["decision_state_id"]),
        "context_only_semantic_unit_refs": sorted(context_refs),
        "relation_semantic_unit_refs": sorted(relation_refs),
    }


def _bindings_from_decision_state_groups(
    groups: Sequence[Mapping[str, Any]],
    *,
    placements: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Recover the authoritative binding payload from canonical projected groups."""

    rows_by_point: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for group in groups:
        point_id = group.get("point_id")
        selected_id = group.get("selected_id")
        placement = None
        placement_id = group.get("placement_id")
        if placements is not None and isinstance(placement_id, str):
            placement = placements.get(placement_id)
        if not isinstance(point_id, str) or not isinstance(selected_id, str):
            placement_id = _required_string(
                group, "placement_id", boundary="decision_state_binding"
            )
            if not isinstance(placement, Mapping):
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    f"projected state group placement is unresolved: {placement_id}",
                )
            point_id = _required_string(
                placement, "point_id", boundary="decision_state_binding"
            )
            selected_id = _required_string(
                placement, "selected_id", boundary="decision_state_binding"
            )
        if selected_id in rows_by_point[point_id]:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"duplicate projected state group: {point_id}::{selected_id}",
            )
        raw_assertions = group.get("state_assertions")
        if raw_assertions is None:
            raw_rows = group.get("state_rows")
            if not isinstance(raw_rows, list):
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    f"projected state rows are invalid: {point_id}::{selected_id}",
                )
            raw_assertions = []
            for raw_row in raw_rows:
                if not isinstance(raw_row, list) or len(raw_row) != len(
                    DECISION_STATE_ROW_COLUMNS
                ):
                    raise EvidenceConsumerError(
                        "decision_state_binding",
                        f"projected state row width is invalid: {point_id}::{selected_id}",
                    )
                raw_assertions.append(dict(zip(DECISION_STATE_ROW_COLUMNS, raw_row)))
        if not isinstance(raw_assertions, list):
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"projected state assertions are invalid: {point_id}::{selected_id}",
            )
        assertions = []
        for raw_assertion in raw_assertions:
            if not isinstance(raw_assertion, Mapping):
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    f"projected state assertion is invalid: {point_id}::{selected_id}",
                )
            assertions.append(
                {
                    key: copy.deepcopy(value)
                    for key, value in raw_assertion.items()
                    if key not in {"decision_state_id", "stage"}
                }
            )
        context_refs = _string_list(
            group.get("context_only_semantic_unit_refs", group.get("qualification_refs")),
            boundary="decision_state_binding",
            field="context_only_semantic_unit_refs",
        )
        rows_by_point[point_id][selected_id] = {
            "selected_id": selected_id,
            "state_assertions": sorted(
                assertions, key=lambda item: _canonical_json_sha256(item)
            ),
            "context_only_semantic_unit_refs": sorted(context_refs),
            "relation_semantic_unit_refs": sorted(
                _string_list(
                    group.get("relation_semantic_unit_refs"),
                    boundary="decision_state_binding",
                    field="relation_semantic_unit_refs",
                )
            ),
        }
    return [
        {
            "point_id": point_id,
            "rows": [rows[selected_id] for selected_id in sorted(rows)],
        }
        for point_id, rows in sorted(rows_by_point.items())
    ]


def _compact_decision_state_group(group: Mapping[str, Any]) -> dict[str, Any]:
    """Reference globally indexed states while retaining a point/row join key."""

    return {
        "placement_id": group["placement_id"],
        "state_ids": [
            assertion["decision_state_id"] for assertion in group["state_assertions"]
        ],
        "qualification_refs": group[
            "context_only_semantic_unit_refs"
        ],
        "relation_semantic_unit_refs": group["relation_semantic_unit_refs"],
    }


def _compact_decision_state_index(
    groups: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    assertions: dict[str, list[Any]] = {}
    for group in groups:
        for assertion in group["state_assertions"]:
            decision_state_id = assertion["decision_state_id"]
            row = [
                decision_state_id,
                *[assertion[column] for column in DECISION_STATE_ROW_COLUMNS],
            ]
            previous = assertions.setdefault(decision_state_id, row)
            if previous != row:
                raise EvidenceConsumerError(
                    "decision_state_semantic_consistency",
                    f"decision-state identity changed: {decision_state_id}",
                )
    return {
        "columns": ["decision_state_id", *DECISION_STATE_ROW_COLUMNS],
        "rows": [assertions[key] for key in sorted(assertions)],
    }


def _expand_compact_decision_state_groups(
    view: Mapping[str, Any],
) -> list[dict[str, Any]]:
    raw_index = view.get("decision_state_index")
    raw_groups = view.get("decision_state_groups")
    expected_columns = ["decision_state_id", *DECISION_STATE_ROW_COLUMNS]
    if (
        not isinstance(raw_index, Mapping)
        or raw_index.get("columns") != expected_columns
        or not isinstance(raw_index.get("rows"), list)
        or not isinstance(raw_groups, list)
    ):
        raise EvidenceConsumerError(
            "decision_state_binding", "compact decision-state index is invalid"
        )
    state_rows: dict[str, list[Any]] = {}
    for row in raw_index["rows"]:
        if not isinstance(row, list) or len(row) != len(expected_columns):
            raise EvidenceConsumerError(
                "decision_state_binding", "compact decision-state row width is invalid"
            )
        decision_state_id = row[0]
        if not isinstance(decision_state_id, str) or decision_state_id in state_rows:
            raise EvidenceConsumerError(
                "decision_state_binding", "compact decision-state identity is invalid"
            )
        state_rows[decision_state_id] = row[1:]
    expanded = []
    for group in raw_groups:
        if not isinstance(group, Mapping) or set(group) != {
            "placement_id",
            "state_ids",
            "qualification_refs",
            "relation_semantic_unit_refs",
        }:
            raise EvidenceConsumerError(
                "decision_state_binding", "compact decision-state group is invalid"
            )
        state_ids = _string_list(
            group.get("state_ids"),
            boundary="decision_state_binding",
            field="state_ids",
        )
        if len(state_ids) != len(set(state_ids)) or any(
            state_id not in state_rows for state_id in state_ids
        ):
            raise EvidenceConsumerError(
                "decision_state_binding", "compact decision-state references are invalid"
            )
        expanded.append(
            {
                "placement_id": group["placement_id"],
                "state_rows": [state_rows[state_id] for state_id in state_ids],
                "qualification_refs": group["qualification_refs"],
                "relation_semantic_unit_refs": group["relation_semantic_unit_refs"],
            }
        )
    return expanded


def _row_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> dict[str, Any]:
    return {
        "columns": list(columns),
        "rows": [[copy.deepcopy(row[column]) for column in columns] for row in rows],
    }


def _reader_state_binding_sha256(
    *,
    relation_state_rows: Sequence[Sequence[Any]],
    source_context_state_rows: Sequence[Sequence[Any]],
) -> str:
    return _canonical_json_sha256(
        {
            "relation_state_rows": [list(row) for row in relation_state_rows],
            "source_context_state_rows": [
                list(row) for row in source_context_state_rows
            ],
        }
    )


def _validate_decision_state_reader_evidence_rows(
    reader: Mapping[str, Any],
) -> None:
    boundary = "decision_state_reader_evidence_binding"

    def valid_row_ids(value: Any, row_count: int) -> bool:
        return (
            isinstance(value, list)
            and all(
                not isinstance(row_id, bool)
                and isinstance(row_id, int)
                and 0 <= row_id < row_count
                for row_id in value
            )
            and len(value) == len(set(value))
        )

    evidence_table = reader.get("evidence_table")
    quote_table = reader.get("quote_table")
    semantic_table = reader.get("semantic_unit_table")
    parent_context_table = reader.get("parent_context_table")
    point_table = reader.get("point_table")
    if not all(
        isinstance(value, Mapping)
        for value in (
            evidence_table,
            quote_table,
            semantic_table,
            parent_context_table,
            point_table,
        )
    ):
        raise EvidenceConsumerError(
            boundary, "reader evidence, quote, semantic, or point table is missing"
        )
    evidence_columns = evidence_table.get("columns")
    evidence_rows = evidence_table.get("rows")
    quote_columns = quote_table.get("columns")
    quote_rows = quote_table.get("rows")
    semantic_columns = semantic_table.get("columns")
    semantic_rows = semantic_table.get("rows")
    parent_context_columns = parent_context_table.get("columns")
    parent_context_rows = parent_context_table.get("rows")
    point_columns = point_table.get("columns")
    point_rows = point_table.get("rows")
    if not all(
        isinstance(value, list)
        for value in (
            evidence_columns,
            evidence_rows,
            quote_columns,
            quote_rows,
            semantic_columns,
            semantic_rows,
            parent_context_columns,
            parent_context_rows,
            point_columns,
            point_rows,
        )
    ):
        raise EvidenceConsumerError(boundary, "reader table shape is invalid")
    try:
        evidence_id_index = evidence_columns.index("evidence_id")
        quote_span_id_index = quote_columns.index("quote_span_id")
        semantic_ref_index = semantic_columns.index("semantic_unit_ref")
        parent_context_id_index = parent_context_columns.index("context_id")
        state_table_index = point_columns.index("state_table")
        relation_facts_index = point_columns.index("relation_facts")
    except ValueError as exc:
        raise EvidenceConsumerError(boundary, "reader join column is missing") from exc
    for point_row in point_rows:
        if not isinstance(point_row, list) or len(point_row) != len(point_columns):
            raise EvidenceConsumerError(boundary, "reader point row is invalid")
        facts = point_row[relation_facts_index]
        state_table = point_row[state_table_index]
        if not isinstance(facts, Mapping):
            raise EvidenceConsumerError(boundary, "reader relation facts are invalid")
        if not isinstance(state_table, Mapping):
            raise EvidenceConsumerError(boundary, "reader state table is invalid")
        state_columns = state_table.get("columns")
        state_rows = state_table.get("rows")
        if not isinstance(state_columns, list) or not isinstance(state_rows, list):
            raise EvidenceConsumerError(boundary, "reader state table is invalid")
        try:
            state_semantic_rows_index = state_columns.index("semantic_unit_row_ids")
        except ValueError as exc:
            raise EvidenceConsumerError(
                boundary, "reader state semantic binding is missing"
            ) from exc
        fact_columns = facts.get("columns")
        fact_rows = facts.get("rows")
        if not isinstance(fact_columns, list) or not isinstance(fact_rows, list):
            raise EvidenceConsumerError(boundary, "reader relation facts are invalid")
        try:
            fact_evidence_id_index = fact_columns.index("evidence_id")
            fact_selected_id_index = fact_columns.index("selected_id")
            fact_evidence_row_index = fact_columns.index("evidence_row_id")
            fact_quote_span_id_index = fact_columns.index("quote_span_id")
            fact_quote_row_index = fact_columns.index("quote_row_id")
            fact_primary_semantic_row_index = fact_columns.index(
                "primary_semantic_unit_row_id"
            )
            fact_companion_semantic_rows_index = fact_columns.index(
                "companion_semantic_unit_row_ids"
            )
            fact_relation_semantic_rows_index = fact_columns.index(
                "relation_semantic_unit_row_ids"
            )
            fact_context_only_semantic_rows_index = fact_columns.index(
                "context_only_semantic_unit_row_ids"
            )
            fact_relation_state_rows_index = fact_columns.index(
                "relation_state_row_ids"
            )
            fact_source_context_state_rows_index = fact_columns.index(
                "source_context_state_row_ids"
            )
            fact_state_binding_sha256_index = fact_columns.index(
                "state_binding_sha256"
            )
            fact_parent_context_ids_index = fact_columns.index(
                "parent_context_ids"
            )
            fact_parent_context_rows_index = fact_columns.index(
                "parent_context_row_ids"
            )
        except ValueError as exc:
            raise EvidenceConsumerError(
                boundary, "reader relation evidence row binding is missing"
            ) from exc
        seen_selected_ids: set[str] = set()
        for fact in fact_rows:
            if not isinstance(fact, list) or len(fact) != len(fact_columns):
                raise EvidenceConsumerError(boundary, "reader relation fact is invalid")
            row_id = fact[fact_evidence_row_index]
            if (
                isinstance(row_id, bool)
                or not isinstance(row_id, int)
                or row_id < 0
                or row_id >= len(evidence_rows)
            ):
                raise EvidenceConsumerError(
                    boundary, "reader evidence row id is out of range"
                )
            evidence_row = evidence_rows[row_id]
            if (
                not isinstance(evidence_row, list)
                or len(evidence_row) != len(evidence_columns)
                or evidence_row[evidence_id_index] != fact[fact_evidence_id_index]
            ):
                raise EvidenceConsumerError(
                    boundary, "reader evidence row identity does not match relation fact"
                )
            quote_row_id = fact[fact_quote_row_index]
            if (
                isinstance(quote_row_id, bool)
                or not isinstance(quote_row_id, int)
                or quote_row_id < 0
                or quote_row_id >= len(quote_rows)
            ):
                raise EvidenceConsumerError(
                    boundary, "reader quote row id is out of range"
                )
            quote_row = quote_rows[quote_row_id]
            if (
                not isinstance(quote_row, list)
                or len(quote_row) != len(quote_columns)
                or quote_row[quote_span_id_index]
                != fact[fact_quote_span_id_index]
            ):
                raise EvidenceConsumerError(
                    boundary, "reader quote row identity does not match relation fact"
                )
            relation_semantic_row_ids = fact[fact_relation_semantic_rows_index]
            if (
                not isinstance(relation_semantic_row_ids, list)
                or not relation_semantic_row_ids
                or any(
                    isinstance(row_id, bool)
                    or not isinstance(row_id, int)
                    or row_id < 0
                    or row_id >= len(semantic_rows)
                    for row_id in relation_semantic_row_ids
                )
            ):
                raise EvidenceConsumerError(
                    boundary, "reader relation semantic row binding is invalid"
                )
            primary_semantic_row_id = fact[fact_primary_semantic_row_index]
            companion_semantic_row_ids = fact[fact_companion_semantic_rows_index]
            if (
                isinstance(primary_semantic_row_id, bool)
                or not isinstance(primary_semantic_row_id, int)
                or primary_semantic_row_id < 0
                or primary_semantic_row_id >= len(semantic_rows)
                or not valid_row_ids(companion_semantic_row_ids, len(semantic_rows))
                or primary_semantic_row_id in companion_semantic_row_ids
            ):
                raise EvidenceConsumerError(
                    boundary, "reader semantic ownership binding is invalid"
                )
            owned_semantic_row_ids = {
                primary_semantic_row_id,
                *companion_semantic_row_ids,
            }
            selected_id = fact[fact_selected_id_index]
            if (
                not isinstance(selected_id, str)
                or not selected_id
                or selected_id in seen_selected_ids
            ):
                raise EvidenceConsumerError(
                    boundary, "reader selected identity is invalid or duplicated"
                )
            seen_selected_ids.add(selected_id)
            context_only_semantic_row_ids = fact[
                fact_context_only_semantic_rows_index
            ]
            relation_state_row_ids = fact[fact_relation_state_rows_index]
            source_context_state_row_ids = fact[
                fact_source_context_state_rows_index
            ]
            if any(
                not valid_row_ids(row_ids, row_count)
                for row_ids, row_count in (
                    (context_only_semantic_row_ids, len(semantic_rows)),
                    (relation_state_row_ids, len(state_rows)),
                    (source_context_state_row_ids, len(state_rows)),
                )
            ):
                raise EvidenceConsumerError(
                    boundary, "reader state or context-only row binding is invalid"
                )
            if set(relation_state_row_ids) & set(source_context_state_row_ids):
                raise EvidenceConsumerError(
                    boundary, "reader relation and source-context states overlap"
                )
            resolved_state_rows: list[list[list[Any]]] = [[], []]
            for partition_index, state_row_ids in enumerate(
                (relation_state_row_ids, source_context_state_row_ids)
            ):
                for state_row_id in state_row_ids:
                    state_row = state_rows[state_row_id]
                    if not isinstance(state_row, list) or len(state_row) != len(
                        state_columns
                    ):
                        raise EvidenceConsumerError(boundary, "reader state row is invalid")
                    state_semantic_row_ids = state_row[state_semantic_rows_index]
                    if (
                        not isinstance(state_semantic_row_ids, list)
                        or any(
                            isinstance(row_id, bool)
                            or not isinstance(row_id, int)
                            or row_id < 0
                            or row_id >= len(semantic_rows)
                            for row_id in state_semantic_row_ids
                        )
                    ):
                        raise EvidenceConsumerError(
                            boundary, "reader state semantic row binding is invalid"
                        )
                    if not set(state_semantic_row_ids) <= owned_semantic_row_ids:
                        raise EvidenceConsumerError(
                            boundary,
                            "reader state semantics do not belong to the selected placement",
                        )
                    resolved_state_rows[partition_index].append(state_row)
            state_binding_sha256 = fact[fact_state_binding_sha256_index]
            if (
                not isinstance(state_binding_sha256, str)
                or state_binding_sha256
                != _reader_state_binding_sha256(
                    relation_state_rows=resolved_state_rows[0],
                    source_context_state_rows=resolved_state_rows[1],
                )
            ):
                raise EvidenceConsumerError(
                    boundary, "reader state row identity does not match relation fact"
                )
            resolved_relation_refs: set[str] = set()
            for semantic_row_id in relation_semantic_row_ids:
                semantic_row = semantic_rows[semantic_row_id]
                if not isinstance(semantic_row, list) or len(semantic_row) != len(
                    semantic_columns
                ):
                    raise EvidenceConsumerError(
                        boundary, "reader semantic unit row is invalid"
                    )
                semantic_ref = semantic_row[semantic_ref_index]
                if not isinstance(semantic_ref, str) or not semantic_ref:
                    raise EvidenceConsumerError(
                        boundary, "reader semantic unit identity is invalid"
                    )
                resolved_relation_refs.add(semantic_ref)
            if (
                len(resolved_relation_refs) != len(relation_semantic_row_ids)
                or not set(relation_semantic_row_ids) <= owned_semantic_row_ids
                or not set(context_only_semantic_row_ids) <= owned_semantic_row_ids
            ):
                raise EvidenceConsumerError(
                    boundary,
                    "reader relation semantic rows do not belong to the selected placement",
                )
            context_ids = fact[fact_parent_context_ids_index]
            context_row_ids = fact[fact_parent_context_rows_index]
            if (
                not isinstance(context_ids, list)
                or not isinstance(context_row_ids, list)
                or len(context_ids) != len(context_row_ids)
                or len(context_ids) != len(set(context_ids))
            ):
                raise EvidenceConsumerError(
                    boundary, "reader parent context row binding is invalid"
                )
            for context_id, context_row_id in zip(
                context_ids, context_row_ids, strict=True
            ):
                if (
                    not isinstance(context_id, str)
                    or not context_id
                    or isinstance(context_row_id, bool)
                    or not isinstance(context_row_id, int)
                    or context_row_id < 0
                    or context_row_id >= len(parent_context_rows)
                ):
                    raise EvidenceConsumerError(
                        boundary, "reader parent context row id is out of range"
                    )
                context_row = parent_context_rows[context_row_id]
                if (
                    not isinstance(context_row, list)
                    or len(context_row) != len(parent_context_columns)
                    or context_row[parent_context_id_index] != context_id
                ):
                    raise EvidenceConsumerError(
                        boundary,
                        "reader parent context row identity does not match relation fact",
                    )


def _decision_state_reader_surface(view: Mapping[str, Any]) -> dict[str, Any]:
    """Project the verified view into a compact, complete cold-reader join surface."""

    groups = {
        row["placement_id"]: row for row in view["decision_state_groups"]
    }
    state_columns = view["decision_state_index"]["columns"]
    state_ref_index = state_columns.index("semantic_unit_refs")
    state_rows = {
        row[0]: row for row in view["decision_state_index"]["rows"]
    }
    semantic_units: dict[str, dict[str, Any]] = {
        row["semantic_unit_ref"]: {
            "semantic_unit_ref": row["semantic_unit_ref"],
            "statement": row.get("statement", row.get("normalized_meaning")),
            "conditions": row.get("conditions", []),
            "polarity": row.get("polarity"),
            "axis_ids": row.get("axis_ids", []),
        }
        for row in view["companion_meaning_index"]
    }
    placement_rows = []
    point_relation_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"support": 0, "counter": 0, "adjacent": 0}
    )
    for placement in view["point_placements"]:
        semantic_ref = placement["semantic_unit_ref"]
        primary = {
            "semantic_unit_ref": semantic_ref,
            "statement": placement["normalized_meaning"],
            "conditions": placement["candidate_context"]["conditions"],
            "polarity": placement["candidate_context"]["polarity"],
            "axis_ids": placement["candidate_context"]["axis_ids"],
        }
        previous = semantic_units.setdefault(semantic_ref, primary)
        if previous["statement"] != primary["statement"]:
            raise EvidenceConsumerError(
                "decision_state_semantic_consistency",
                f"semantic unit reader meaning changed: {semantic_ref}",
            )
        previous["conditions"] = sorted(
            set(previous["conditions"]) | set(primary["conditions"])
        )
        previous["axis_ids"] = sorted(
            set(previous["axis_ids"]) | set(primary["axis_ids"])
        )
        polarities = {
            value for value in (previous["polarity"], primary["polarity"]) if value is not None
        }
        if len(polarities) > 1:
            raise EvidenceConsumerError(
                "decision_state_semantic_consistency",
                f"semantic unit reader polarity changed: {semantic_ref}",
            )
        previous["polarity"] = next(iter(polarities), None)
        group = groups.get(placement["placement_id"])
        point_relation_counts[placement["point_id"]][placement["relation"]] += 1
        placement_rows.append(
            {
                key: value
                for key, value in (
                    ("point_id", placement["point_id"]),
                    ("selected_id", placement["selected_id"]),
                    ("relation", placement["relation"]),
                    ("layer", placement["layer"]),
                    ("evidence_id", placement["evidence_id"]),
                    ("semantic_unit_ref", semantic_ref),
                    ("quote_span_id", placement["quote_span_id"]),
                    (
                        "companion_semantic_unit_refs",
                        placement["same_evidence_companion_meaning_refs"],
                    ),
                    (
                        "relation_semantic_unit_refs",
                        group["relation_semantic_unit_refs"]
                        if group is not None
                        else placement.get("relation_semantic_unit_refs", [semantic_ref]),
                    ),
                    (
                        "context_only_semantic_unit_refs",
                        (
                            group["qualification_refs"]
                            if group is not None
                            else [
                                semantic_ref,
                                *placement["same_evidence_companion_meaning_refs"],
                            ]
                        ),
                    ),
                    ("parent_contexts", placement.get("parent_contexts", [])),
                    ("state_ids", group["state_ids"] if group is not None else []),
                )
            }
        )
    evidence_rows = [
        {
            "evidence_id": row["evidence_id"],
            "origin_group_id": row["origin_group_id"],
            "source_venue": row["source_venue"],
            "source_role": row["source_role"],
            "content_surface": row["content_surface"],
            "source_ref": row["source_ref"],
            "publication_time": row["publication_time"],
            "engagement_kind": row["engagement"]["kind"],
            "engagement_status": row["engagement"]["status"],
            "engagement_raw_value": row["engagement"]["raw_value"],
            "engagement_observed_at": row["engagement"]["observed_at"],
            "engagement_context": row["engagement"]["context"],
            "engagement_material_positive": row["engagement"]["material_positive"],
            "container_ids": row["container_ids"],
        }
        for row in view["evidence_index"]
    ]
    evidence_row_ids = {
        row["evidence_id"]: row_id for row_id, row in enumerate(evidence_rows)
    }
    if len(evidence_row_ids) != len(evidence_rows):
        raise EvidenceConsumerError(
            "decision_state_reader_evidence_binding",
            "reader evidence identity is duplicated",
        )
    quote_rows = list(view["quote_spans"])
    quote_row_ids = {
        row["quote_span_id"]: row_id for row_id, row in enumerate(quote_rows)
    }
    if len(quote_row_ids) != len(quote_rows):
        raise EvidenceConsumerError(
            "decision_state_reader_evidence_binding",
            "reader quote identity is duplicated",
        )
    quote_statuses = {
        row["quote_span_id"]: row["quote_status"] for row in quote_rows
    }
    parent_contexts: dict[str, dict[str, str]] = {}
    for row in placement_rows:
        for context in row["parent_contexts"]:
            context_id = context["context_id"]
            previous = parent_contexts.setdefault(context_id, context)
            if previous != context:
                raise EvidenceConsumerError(
                    "decision_state_parent_context_binding",
                    f"parent context identity changed: {context_id}",
                )
    parent_context_rows = [parent_contexts[key] for key in sorted(parent_contexts)]
    parent_context_row_ids = {
        row["context_id"]: row_id
        for row_id, row in enumerate(parent_context_rows)
    }
    relation_fact_columns = [
        "selected_id",
        "layer",
        "relation",
        "evidence_id",
        "evidence_row_id",
        "quote_span_id",
        "quote_row_id",
        "primary_semantic_unit_row_id",
        "companion_semantic_unit_row_ids",
        "relation_semantic_unit_row_ids",
        "context_only_semantic_unit_row_ids",
        "quote_status",
        "parent_context_ids",
        "parent_context_row_ids",
        "relation_state_row_ids",
        "source_context_state_row_ids",
        "state_binding_sha256",
    ]
    point_state_ids: dict[str, set[str]] = defaultdict(set)
    for row in placement_rows:
        point_state_ids[row["point_id"]].update(row["state_ids"])
    point_state_row_ids = {
        point_id: {
            state_id: row_id for row_id, state_id in enumerate(sorted(state_ids))
        }
        for point_id, state_ids in point_state_ids.items()
    }
    semantic_ref_row_ids = {
        semantic_ref: row_id
        for row_id, semantic_ref in enumerate(sorted(semantic_units))
    }
    compact_state_rows = {
        state_id: [
            *row[1:4],
            [semantic_ref_row_ids[semantic_ref] for semantic_ref in row[state_ref_index]],
            *row[5:],
        ]
        for state_id, row in state_rows.items()
    }
    point_relation_facts: dict[str, list[list[Any]]] = defaultdict(list)
    for row in placement_rows:
        relation_state_ids = [
            state_id
            for state_id in row["state_ids"]
            if set(state_rows[state_id][state_ref_index])
            & set(row["relation_semantic_unit_refs"])
        ]
        source_context_state_ids = [
            state_id
            for state_id in row["state_ids"]
            if not set(state_rows[state_id][state_ref_index])
            & set(row["relation_semantic_unit_refs"])
        ]
        point_relation_facts[row["point_id"]].append(
            [
                row["selected_id"],
                row["layer"],
                row["relation"],
                row["evidence_id"],
                evidence_row_ids[row["evidence_id"]],
                row["quote_span_id"],
                quote_row_ids[row["quote_span_id"]],
                semantic_ref_row_ids[row["semantic_unit_ref"]],
                [
                    semantic_ref_row_ids[semantic_ref]
                    for semantic_ref in row["companion_semantic_unit_refs"]
                ],
                [
                    semantic_ref_row_ids[semantic_ref]
                    for semantic_ref in row["relation_semantic_unit_refs"]
                ],
                [
                    semantic_ref_row_ids[semantic_ref]
                    for semantic_ref in row["context_only_semantic_unit_refs"]
                ],
                quote_statuses[row["quote_span_id"]],
                [context["context_id"] for context in row["parent_contexts"]],
                [
                    parent_context_row_ids[context["context_id"]]
                    for context in row["parent_contexts"]
                ],
                [
                    point_state_row_ids[row["point_id"]][state_id]
                    for state_id in relation_state_ids
                ],
                [
                    point_state_row_ids[row["point_id"]][state_id]
                    for state_id in source_context_state_ids
                ],
                _reader_state_binding_sha256(
                    relation_state_rows=[
                        compact_state_rows[state_id] for state_id in relation_state_ids
                    ],
                    source_context_state_rows=[
                        compact_state_rows[state_id]
                        for state_id in source_context_state_ids
                    ],
                ),
            ]
        )
    point_rows = [
        {
            **row,
            "relation_counts": point_relation_counts[row["point_id"]],
            "state_table": {
                "columns": [
                    "state_kind",
                    "commercial_direction",
                    "decision_object",
                    "semantic_unit_row_ids",
                    "quantity",
                    "conditions",
                ],
                "rows": [
                    compact_state_rows[state_id]
                    for state_id in sorted(point_state_ids[row["point_id"]])
                ],
            },
            "relation_facts": {
                "columns": relation_fact_columns,
                "rows": point_relation_facts[row["point_id"]],
            },
        }
        for row in view["point_index"]
    ]
    point_columns = (
        "point_id",
        "bounded_point",
        "projection_mode",
        "navigation_group_id",
        "family_id",
        "truth_origin_count",
        "candidate_count",
        "candidate_inventory_sha256",
        "bindings",
        "relation_counts",
        "same_origin_observation_groups",
        "state_table",
        "relation_facts",
    )
    evidence_columns = tuple(evidence_rows[0])
    semantic_columns = (
        "semantic_unit_ref",
        "statement",
        "conditions",
        "polarity",
        "axis_ids",
    )
    origin_columns = (
        "origin_group_id",
        "independence_key",
        "independence_posture",
    )
    quote_columns = (
        "quote_span_id",
        "evidence_id",
        "quote_status",
        "exact_quote",
        "quote_unavailable_cause",
    )
    parent_context_columns = ("context_id", "source_ref", "text")
    reader = {
        "schema_version": "phase_a_evidence_decision_state_reader_surface_v3",
        "axis_id": view["axis_id"],
        "source_axis_pack": copy.deepcopy(view["source_axis_pack"]),
        "counts": copy.deepcopy(view["counts"]),
        "navigation_groups": copy.deepcopy(view["navigation_groups"]),
        "projection_routes": copy.deepcopy(view["projection_routes"]),
        "point_table": _row_table(point_rows, point_columns),
        "evidence_table": _row_table(evidence_rows, evidence_columns),
        "origin_table": _row_table(view["origin_index"], origin_columns),
        "quote_table": _row_table(quote_rows, quote_columns),
        "parent_context_table": _row_table(
            parent_context_rows, parent_context_columns
        ),
        "semantic_unit_table": _row_table(
            [semantic_units[key] for key in sorted(semantic_units)], semantic_columns
        ),
        "evidence_accounting_contract": _reader_evidence_accounting_contract(),
        "decision_state_contract": _decision_state_reader_contract(
            view["decision_state_contract"]
        ),
        "rejected_point_index": copy.deepcopy(view["rejected_point_index"]),
        "non_claims": copy.deepcopy(view["non_claims"]),
        "derivation_rules": {
            "placement_origin": (
                "each point relation_facts row directly binds selected_id to evidence_row_id; "
                "the selected evidence_table row's evidence_id must match before origin_group_id is used"
            ),
            "point_relation_facts": (
                "relation_facts exhaustively bind every displayed placement to the literal "
                "semantic_unit_table rows and relation_state_row_ids that explain its "
                "point-relative relation; source_context_state_row_ids coexist but may not be "
                "attached to the relation; state_binding_sha256 rechecks both state partitions; "
                "primary_semantic_unit_row_id and companion_semantic_unit_row_ids own the exact "
                "semantic rows available to that selected evidence; state row ids are zero-based "
                "rows in the same point row's state_table and semantic row ids are zero-based rows "
                "in the global semantic_unit_table; "
                "evidence_row_id and quote_row_id directly bind the literal provenance and quote; "
                "parent_context_row_ids bind any exact parent prompt required to interpret a terse reply"
            ),
            "state_semantic_unit_rows": (
                "each point state_table semantic_unit_row_ids value is a zero-based row in the "
                "reader semantic_unit_table, preserving exact semantic refs without repeating them"
            ),
            "context_only_semantic_unit_refs": (
                "relation_facts context_only_semantic_unit_row_ids directly select zero-based "
                "reader semantic_unit_table rows owned by the same primary-plus-companion evidence"
            ),
            "point_placement_and_relation_origins": (
                "group each point's relation_facts rows by relation, then select evidence_table "
                "origin_group_id by evidence_row_id after matching evidence_id"
            ),
            "origin_evidence_and_containers": (
                "group evidence_table evidence_id and container_ids by origin_group_id"
            ),
            "container_concentrations": (
                "group evidence_table origin_group_id and evidence_id by container_id"
            ),
        },
    }
    _validate_decision_state_reader_evidence_rows(reader)
    return reader


def _validate_decision_state_semantic_consistency(
    groups: Sequence[Mapping[str, Any]],
) -> None:
    """Keep one semantic unit's state meaning stable across every point placement."""

    observed: dict[str, str] = {}
    for group in groups:
        signatures_by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for assertion in group["state_assertions"]:
            signature = {
                key: copy.deepcopy(value)
                for key, value in assertion.items()
                if key not in {"decision_state_id", "semantic_unit_refs"}
            }
            for semantic_ref in assertion["semantic_unit_refs"]:
                signatures_by_ref[semantic_ref].append(signature)
        for semantic_ref in group["context_only_semantic_unit_refs"]:
            signatures_by_ref.setdefault(semantic_ref, [])
        for semantic_ref, signatures in signatures_by_ref.items():
            identity = _canonical_json_sha256(
                sorted(signatures, key=_canonical_json_sha256)
            )
            previous = observed.setdefault(semantic_ref, identity)
            if previous != identity:
                raise EvidenceConsumerError(
                    "decision_state_semantic_consistency",
                    f"semantic unit changes state meaning across points: {semantic_ref}",
                )


def _decision_state_rejected_index(
    spec: Mapping[str, Any],
    rejected_points: Sequence[Mapping[str, Any]],
    navigation: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Optionally bind rejected points to an explicit existing navigation group."""

    required_fields = {"point_id", "bounded_point", "disposition", "reason"}
    receipt_fields = {"resolution_receipt_path", "resolution_receipt_sha256"}
    result: list[dict[str, Any]] = []
    for row in rejected_points:
        if not isinstance(row, Mapping) or set(row) not in {
            frozenset(required_fields),
            frozenset(required_fields | receipt_fields),
        }:
            raise EvidenceConsumerError(
                "decision_state_binding", "rejected-point fields are invalid"
            )
        normalized = {
            field: _required_string(
                row, field, boundary="decision_state_binding"
            )
            for field in ("point_id", "bounded_point", "disposition", "reason")
        }
        if receipt_fields <= set(row):
            normalized.update(
                {
                    field: _required_string(
                        row, field, boundary="decision_state_binding"
                    )
                    for field in sorted(receipt_fields)
                }
            )
        result.append(normalized)
    raw_bindings = spec.get("decision_state_rejected_point_navigation")
    if raw_bindings is None:
        return result
    if not isinstance(raw_bindings, list):
        raise EvidenceConsumerError(
            "decision_state_binding", "rejected-point navigation must be a list"
        )
    rejected_ids = {row["point_id"] for row in result}
    navigation_group_ids = {
        _required_string(row, "group_id", boundary="decision_state_binding")
        for row in navigation
    }
    bindings: dict[str, str] = {}
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, Mapping) or set(raw_binding) != {
            "point_id",
            "navigation_group_id",
        }:
            raise EvidenceConsumerError(
                "decision_state_binding", "rejected-point navigation fields are invalid"
            )
        point_id = _required_string(
            raw_binding, "point_id", boundary="decision_state_binding"
        )
        group_id = _required_string(
            raw_binding, "navigation_group_id", boundary="decision_state_binding"
        )
        if point_id not in rejected_ids or point_id in bindings:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"rejected-point navigation identity is invalid: {point_id}",
            )
        if group_id not in navigation_group_ids:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"rejected point targets an unknown navigation group: {point_id}::{group_id}",
            )
        bindings[point_id] = group_id
    if set(bindings) != rejected_ids:
        raise EvidenceConsumerError(
            "decision_state_binding",
            "rejected-point navigation does not cover every rejected point",
        )
    for row in result:
        row["navigation_group_id"] = bindings[row["point_id"]]
    return result


def _stable_evidence(
    row: Mapping[str, Any], candidate: Mapping[str, Any], surface: str, basis: str
) -> dict[str, Any]:
    return {
        "evidence_id": row["evidence_id"],
        "origin_group_id": row["origin_group_id"],
        "source_family": row["source_family"],
        "source_role": row["source_role"],
        "source_venue": row["source_venue"],
        "source_venue_basis": row["source_venue_basis"],
        "source_ref": row["source_ref"],
        "source_body_present": row.get("source_body_present"),
        "publication_time": row.get("publication_time"),
        "content_surface": surface,
        "content_surface_basis": basis,
        "engagement": {
            "kind": row.get("engagement_kind"),
            "status": candidate.get("engagement_status"),
            "raw_value": row.get("engagement_raw_value"),
            "observed_at": row.get("engagement_observed_at"),
            "context": candidate.get("engagement_context"),
            "material_positive": candidate.get("engagement_material_positive"),
        },
    }


def _same_origin_observation_groups(
    *,
    point_id: str,
    displayed_rows: Sequence[Mapping[str, Any]],
    candidate_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Preserve repeated source observations without manufacturing recurrence credit."""

    displayed_keys: set[tuple[str, str, str, str]] = set()
    for row in displayed_rows:
        relation = _required_string(row, "relation", boundary="evidence_accounting")
        if relation not in {"support", "counter", "adjacent"}:
            raise EvidenceConsumerError(
                "evidence_accounting", f"unsupported displayed relation: {point_id}::{relation}"
            )
        displayed_keys.add(
            (
                _required_string(row, "layer", boundary="evidence_accounting"),
                relation,
                _required_string(
                    row, "normalized_meaning", boundary="evidence_accounting"
                ),
                _required_string(row, "origin_group_id", boundary="evidence_accounting"),
            )
        )

    groups: list[dict[str, Any]] = []
    for layer, relation, normalized_meaning, origin_group_id in sorted(displayed_keys):
        matching = [
            candidate
            for candidate in candidate_by_id.values()
            if candidate.get("relation") == relation
            and candidate.get("normalized_meaning") == normalized_meaning
            and candidate.get("scoped_independence_key") == origin_group_id
        ]
        observations: dict[tuple[str, str], dict[str, Any]] = {}
        candidate_ids: dict[tuple[str, str], set[str]] = defaultdict(set)
        independence_postures: set[str] = set()
        for candidate in matching:
            evidence_id = _required_string(
                candidate, "evidence_id", boundary="evidence_accounting"
            )
            semantic_unit_ref = _required_string(
                candidate, "semantic_unit_ref", boundary="evidence_accounting"
            )
            observation_key = (evidence_id, semantic_unit_ref)
            surface, _ = _content_surface(candidate)
            record = {
                "evidence_id": evidence_id,
                "semantic_unit_ref": semantic_unit_ref,
                "source_ref": _required_string(
                    candidate, "source_ref", boundary="evidence_accounting"
                ),
                "publication_time": candidate.get("publication_time"),
                "source_venue": _required_string(
                    candidate, "source_venue", boundary="evidence_accounting"
                ),
                "source_role": _required_string(
                    candidate, "source_role", boundary="evidence_accounting"
                ),
                "content_surface": surface,
                "engagement": {
                    "kind": candidate.get("engagement_kind"),
                    "status": candidate.get("engagement_status"),
                    "raw_value": candidate.get("engagement_raw_value"),
                    "observed_at": candidate.get("engagement_observed_at"),
                    "material_positive": candidate.get("engagement_material_positive"),
                },
                "lineage": {
                    "source_id": candidate.get("source_id"),
                    "packet_sha256": candidate.get("packet_sha256"),
                },
            }
            previous = observations.setdefault(observation_key, record)
            if previous != record:
                raise EvidenceConsumerError(
                    "evidence_accounting",
                    f"source observation changed inside one point: "
                    f"{point_id}::{evidence_id}::{semantic_unit_ref}",
                )
            candidate_ids[observation_key].add(
                _required_string(candidate, "candidate_id", boundary="evidence_accounting")
            )
            independence_posture = candidate.get("independence_posture")
            if independence_posture not in INDEPENDENCE_POSTURES:
                raise EvidenceConsumerError(
                    "evidence_accounting", "source observation independence posture is invalid"
                )
            independence_postures.add(independence_posture)
        if not observations:
            continue
        if len(independence_postures) != 1:
            raise EvidenceConsumerError(
                "evidence_accounting",
                f"same-origin observation posture changed: {point_id}::{origin_group_id}",
            )
        if len(observations) <= 1:
            continue
        observation_rows = []
        for observation_key, record in observations.items():
            observation_rows.append(
                {
                    **record,
                    "candidate_ids": sorted(candidate_ids[observation_key]),
                }
            )
        observation_rows.sort(
            key=lambda row: (
                row["publication_time"] or "",
                row["evidence_id"],
                row["semantic_unit_ref"],
            )
        )
        groups.append(
            {
                "layer": layer,
                "relation": relation,
                "normalized_meaning": normalized_meaning,
                "origin_group_id": origin_group_id,
                "independence_posture": next(iter(independence_postures)),
                "source_observation_count": len(observation_rows),
                "observations": observation_rows,
            }
        )
    return groups


def _quote_span(row: Mapping[str, Any]) -> dict[str, Any]:
    core = {
        "evidence_id": row["evidence_id"],
        "quote_status": row.get("quote_status"),
        "exact_quote": row.get("exact_quote"),
        "quote_unavailable_cause": row.get("quote_unavailable_cause"),
    }
    return {"quote_span_id": f"quote_{_canonical_json_sha256(core)[:24]}", **core}


def _load_point(
    descriptor: Mapping[str, Any], *, expected_axis: str, require_complete_pins: bool
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    artifact, candidate_by_id, checked = _validate_point_binding(
        descriptor,
        expected_axis=expected_axis,
        require_complete_pins=require_complete_pins,
    )
    normalized = checked["descriptor"]
    for key in ("candidate_count", "display_row_count", "truth_origin_count"):
        if descriptor.get(key) != normalized[key]:
            raise EvidenceConsumerError(
                "point_binding", f"declared point summary changed: {descriptor.get('point_id')}::{key}"
            )
    declared_relations = descriptor.get("relation_counts")
    if not isinstance(declared_relations, Mapping) or {
        relation: declared_relations.get(relation, 0)
        for relation in ("support", "counter", "adjacent")
    } != normalized["relation_counts"]:
        raise EvidenceConsumerError(
            "point_binding",
            f"declared point summary changed: {descriptor.get('point_id')}::relation_counts",
        )
    bindings = checked["bindings"]
    if not require_complete_pins:
        bindings = {
            key: value
            for key, value in bindings.items()
            if key != "quote_manifest_file_sha256"
        }
    return artifact, candidate_by_id, bindings


def build_axis_consolidated_view(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Build and fully verify one derived, origin-normalized axis view."""

    spec_version = spec.get("schema_version")
    if spec_version not in {
        LEGACY_CONSOLIDATION_SPEC_VERSION,
        CONSOLIDATION_SPEC_VERSION,
    }:
        raise EvidenceConsumerError("consolidation_spec", "unsupported spec version")
    is_routed_v2 = spec_version == CONSOLIDATION_SPEC_VERSION
    if not is_routed_v2:
        legacy_residue = sorted(
            (DECISION_STATE_SPEC_FIELDS | DIRECT_OUTCOME_RELATION_SPEC_FIELDS) & set(spec)
        )
        if legacy_residue:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"decision-state fields are invalid in a v1 spec: {legacy_residue}",
            )
    axis_id = _required_string(spec, "axis_id", boundary="consolidation_spec")
    axis_path = Path(
        _required_string(spec, "source_axis_pack_path", boundary="consolidation_spec")
    )
    expected_axis_hash = _required_string(
        spec, "source_axis_pack_sha256", boundary="consolidation_spec"
    )
    if not axis_path.is_file() or hash_file(axis_path) != expected_axis_hash:
        raise EvidenceConsumerError("axis_binding", "source axis pack changed")
    axis_pack = _load_object(axis_path, boundary="axis_binding")
    axis_pack_version = axis_pack.get("schema_version")
    if axis_pack_version == SOURCE_AXIS_PACK_VERSION:
        stored_pack_hash = axis_pack.get("axis_pack_sha256")
        if not isinstance(stored_pack_hash, str):
            raise EvidenceConsumerError("axis_binding", "generic axis pack identity missing")
        validate_phase_a_evidence_axis_pack(
            axis_pack, expected_axis_pack_sha256=stored_pack_hash
        )
        require_complete_pins = True
    elif axis_pack_version == LEGACY_HYDRATION_AXIS_PACK_VERSION:
        require_complete_pins = False
    else:
        raise EvidenceConsumerError("axis_binding", "unsupported source axis pack version")
    if (
        axis_pack.get("axis_id") != axis_id
        or axis_pack.get("status") != "complete_valid_axis_pack"
    ):
        raise EvidenceConsumerError("axis_binding", "unsupported or incomplete source axis pack")
    point_descriptors = axis_pack.get("points")
    if not isinstance(point_descriptors, list) or not point_descriptors:
        raise EvidenceConsumerError("axis_binding", "axis pack has no points")
    point_ids = [row.get("point_id") for row in point_descriptors if isinstance(row, Mapping)]
    if (
        len(point_ids) != len(point_descriptors)
        or not all(isinstance(value, str) and value for value in point_ids)
        or len(set(point_ids)) != len(point_ids)
    ):
        raise EvidenceConsumerError("axis_binding", "axis point identities are invalid")
    navigation, point_navigation = _navigation_groups(spec, set(point_ids))
    if is_routed_v2:
        projection_routes, point_projections = _projection_routes(spec, set(point_ids))
        if "decision_state" not in point_projections.values():
            direct_only_residue = sorted(DECISION_STATE_SPEC_FIELDS & set(spec))
            if direct_only_residue:
                raise EvidenceConsumerError(
                    "decision_state_binding",
                    "decision-state fields supplied without a decision_state route: "
                    f"{direct_only_residue}",
                )
        decision_state_bindings = _decision_state_bindings(spec, point_projections)
        direct_outcome_relation_bindings = _direct_outcome_relation_bindings(
            spec, point_projections
        )
    else:
        projection_routes = []
        point_projections = {}
        decision_state_bindings = {}
        direct_outcome_relation_bindings = {}

    origins: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    quote_spans: dict[str, dict[str, Any]] = {}
    companion_meanings: dict[str, dict[str, Any]] = {}
    placements: list[dict[str, Any]] = []
    decision_state_groups: list[dict[str, Any]] = []
    point_index: list[dict[str, Any]] = []
    axis_truth_origin_ids: set[str] = set()
    candidate_total = 0

    for descriptor in point_descriptors:
        point_id = descriptor["point_id"]
        artifact, candidate_by_id, bindings = _load_point(
            descriptor,
            expected_axis=axis_id,
            require_complete_pins=require_complete_pins,
        )
        if is_routed_v2:
            output_boundary = artifact.get("output_boundary")
            missing_boundaries = [
                boundary
                for boundary in DIRECT_OUTCOME_BOUNDARIES
                if not isinstance(output_boundary, list) or boundary not in output_boundary
            ]
            if missing_boundaries:
                raise EvidenceConsumerError(
                    "projection_boundary",
                    f"routed point lacks required output boundary: "
                    f"{point_id}::{missing_boundaries[0]}",
                )
        candidate_total += len(candidate_by_id)
        point_placement_ids: list[str] = []
        point_decision_state_bindings = dict(decision_state_bindings.get(point_id, {}))
        point_direct_relation_bindings = dict(
            direct_outcome_relation_bindings.get(point_id, {})
        )
        point_truth_origin_ids: set[str] = set()
        seen_selected: set[str] = set()
        observed_relations: dict[str, int] = {
            "support": 0,
            "counter": 0,
            "adjacent": 0,
        }
        relation_origin_ids: dict[str, set[str]] = {
            "support": set(),
            "counter": set(),
            "adjacent": set(),
        }
        source_groups = artifact.get("source_groups")
        if not isinstance(source_groups, list):
            raise EvidenceConsumerError("point_projection", f"source groups invalid: {point_id}")
        same_origin_observation_groups = (
            _same_origin_observation_groups(
                point_id=point_id,
                displayed_rows=_point_rows(artifact, point_id=point_id),
                candidate_by_id=candidate_by_id,
            )
            if is_routed_v2
            else []
        )
        for source_group in source_groups:
            if not isinstance(source_group, Mapping) or not isinstance(
                source_group.get("rows"), list
            ):
                raise EvidenceConsumerError(
                    "point_projection", f"source group rows invalid: {point_id}"
                )
            for raw_row in source_group["rows"]:
                if not isinstance(raw_row, Mapping):
                    raise EvidenceConsumerError(
                        "point_projection", f"display row invalid: {point_id}"
                    )
                row = dict(raw_row)
                selected_id = _required_string(row, "selected_id", boundary="point_projection")
                if selected_id in seen_selected:
                    raise EvidenceConsumerError(
                        "point_projection", f"duplicate selected_id: {point_id}::{selected_id}"
                    )
                seen_selected.add(selected_id)
                relation = _required_string(row, "relation", boundary="point_projection")
                if relation not in {"support", "counter", "adjacent"}:
                    raise EvidenceConsumerError(
                        "point_projection", f"unsupported displayed relation: {relation}"
                    )
                candidate_ids = _string_list(
                    row.get("origin_candidate_ids"),
                    boundary="point_projection",
                    field="origin_candidate_ids",
                )
                if any(candidate_id not in candidate_by_id for candidate_id in candidate_ids):
                    raise EvidenceConsumerError(
                        "point_projection", f"display candidate missing: {point_id}::{selected_id}"
                    )
                matching = [
                    candidate_by_id[candidate_id]
                    for candidate_id in candidate_ids
                    if candidate_by_id[candidate_id].get("evidence_id") == row.get("evidence_id")
                    and candidate_by_id[candidate_id].get("semantic_unit_ref")
                    == row.get("semantic_unit_ref")
                ]
                if len(matching) != 1:
                    raise EvidenceConsumerError(
                        "point_projection",
                        f"display row does not resolve to one candidate: {point_id}::{selected_id}",
                    )
                candidate = matching[0]
                if candidate.get("relation") != relation:
                    raise EvidenceConsumerError(
                        "point_projection", f"candidate relation changed: {point_id}::{selected_id}"
                    )
                origin_id = _required_string(row, "origin_group_id", boundary="origin_identity")
                independence_key = _required_string(
                    row, "independence_key", boundary="origin_identity"
                )
                independence_posture = candidate.get("independence_posture")
                if independence_posture not in INDEPENDENCE_POSTURES:
                    raise EvidenceConsumerError(
                        "origin_identity", "origin independence posture is invalid"
                    )
                evidence_id = _required_string(row, "evidence_id", boundary="point_projection")
                surface, surface_basis = _content_surface(row)
                stable = _stable_evidence(row, candidate, surface, surface_basis)
                stable["container_ids"] = sorted(
                    {
                        item.get("container_id")
                        for item in (candidate_by_id[value] for value in candidate_ids)
                        # Narrowing an evidence row to its own candidates is a
                        # v2 correction; applying it to v1 would rewrite already
                        # published frozen v1 container_ids.
                        if not is_routed_v2 or item.get("evidence_id") == evidence_id
                        if isinstance(item.get("container_id"), str) and item.get("container_id")
                    }
                )
                previous_evidence = evidence.get(evidence_id)
                if previous_evidence is not None and previous_evidence != stable:
                    raise EvidenceConsumerError(
                        "evidence_identity", f"evidence facts changed across points: {evidence_id}"
                    )
                evidence[evidence_id] = stable
                quote = _quote_span(row)
                previous_quote = quote_spans.get(quote["quote_span_id"])
                if previous_quote is not None and previous_quote != quote:
                    raise EvidenceConsumerError("quote_identity", "quote span hash collision")
                quote_spans[quote["quote_span_id"]] = quote
                companion_refs: list[str] = []
                raw_companions = row.get("same_evidence_companion_meanings") or []
                if not isinstance(raw_companions, list):
                    raise EvidenceConsumerError(
                        "companion_identity", "companion meanings must be a list"
                    )
                for raw_companion in raw_companions:
                    if not isinstance(raw_companion, Mapping):
                        raise EvidenceConsumerError(
                            "companion_identity", "companion meaning must be an object"
                        )
                    companion = copy.deepcopy(dict(raw_companion))
                    companion_ref = _required_string(
                        companion, "semantic_unit_ref", boundary="companion_identity"
                    )
                    previous_companion = companion_meanings.get(companion_ref)
                    if previous_companion is not None and previous_companion != companion:
                        raise EvidenceConsumerError(
                            "companion_identity",
                            f"companion meaning changed across placements: {companion_ref}",
                        )
                    companion_meanings[companion_ref] = companion
                    companion_refs.append(companion_ref)
                placement_id = f"placement_{_canonical_json_sha256([point_id, selected_id])[:24]}"
                placement = {
                    "placement_id": placement_id,
                    "point_id": point_id,
                    "selected_id": selected_id,
                    "origin_group_id": origin_id,
                    "evidence_id": evidence_id,
                    "semantic_unit_ref": row["semantic_unit_ref"],
                    "relation": relation,
                    "layer": row["layer"],
                    "reason_code": row["reason_code"],
                    "display_label": row["display_label"],
                    "normalized_meaning": row["normalized_meaning"],
                    "same_evidence_companion_meaning_refs": companion_refs,
                    "candidate_context": {
                        "axis_ids": sorted(
                            value
                            for value in candidate.get("axis_ids", [])
                            if isinstance(value, str)
                        ),
                        "conditions": sorted(
                            value
                            for value in candidate.get("conditions", [])
                            if isinstance(value, str)
                        ),
                        "existing_relations": copy.deepcopy(
                            candidate.get("existing_relations") or []
                        ),
                        "independence_posture": candidate.get("independence_posture"),
                        "polarity": candidate.get("polarity"),
                        "product_version_ids": sorted(
                            value
                            for value in candidate.get("product_version_ids", [])
                            if isinstance(value, str)
                        ),
                        "protected_lanes": sorted(
                            value
                            for value in candidate.get("protected_lanes", [])
                            if isinstance(value, str)
                        ),
                        "retained_unmerged": candidate.get("retained_unmerged"),
                        "subject_product_ids": sorted(
                            value
                            for value in candidate.get("subject_product_ids", [])
                            if isinstance(value, str)
                        ),
                        "uncertainty_posture": candidate.get("uncertainty_posture"),
                    },
                    "quote_span_id": quote["quote_span_id"],
                    "origin_candidate_ids": candidate_ids,
                }
                if is_routed_v2 and point_projections[point_id] == "direct_outcome":
                    relation_refs = point_direct_relation_bindings.pop(selected_id, None)
                    if relation_refs is not None:
                        available_relation_refs = {
                            row["semantic_unit_ref"],
                            *placement["same_evidence_companion_meaning_refs"],
                        }
                        if set(relation_refs) - available_relation_refs:
                            raise EvidenceConsumerError(
                                "direct_outcome_relation_binding",
                                f"relation binding references foreign semantic unit: "
                                f"{point_id}::{selected_id}",
                            )
                        placement["relation_semantic_unit_refs"] = relation_refs
                placements.append(placement)
                point_placement_ids.append(placement_id)
                if is_routed_v2 and point_projections[point_id] == "decision_state":
                    state_binding = point_decision_state_bindings.pop(selected_id, None)
                    if state_binding is None:
                        raise EvidenceConsumerError(
                            "decision_state_binding",
                            f"display row lacks a state binding: {point_id}::{selected_id}",
                        )
                    placement["parent_contexts"] = copy.deepcopy(
                        _validated_candidate_parent_contexts(
                            candidate,
                            point_id=point_id,
                            selected_id=selected_id,
                        )
                    )
                    state_group = _decision_state_group(
                        point_id=point_id,
                        row=row,
                        placement=placement,
                        binding=state_binding,
                    )
                    decision_state_groups.append(state_group)
                observed_relations[relation] += 1
                relation_origin_ids[relation].add(origin_id)
                if _is_truth_support_origin(row):
                    point_truth_origin_ids.add(origin_id)
                origin = origins.setdefault(
                    origin_id,
                    {
                        "origin_group_id": origin_id,
                        "independence_key": independence_key,
                        "independence_posture": independence_posture,
                        "evidence_ids": set(),
                        "placement_ids": set(),
                        "container_ids": set(),
                    },
                )
                if origin["independence_key"] != independence_key:
                    raise EvidenceConsumerError(
                        "origin_identity", f"origin independence changed: {origin_id}"
                    )
                if origin["independence_posture"] != independence_posture:
                    raise EvidenceConsumerError(
                        "origin_identity",
                        f"origin independence posture changed: {origin_id}",
                    )
                origin["evidence_ids"].add(evidence_id)
                origin["placement_ids"].add(placement_id)
                origin["container_ids"].update(stable["container_ids"])
        if point_decision_state_bindings:
            raise EvidenceConsumerError(
                "decision_state_binding",
                f"state binding targets a non-displayed row: "
                f"{point_id}::{sorted(point_decision_state_bindings)[0]}",
            )
        if point_direct_relation_bindings:
            raise EvidenceConsumerError(
                "direct_outcome_relation_binding",
                f"relation binding targets a non-displayed row: "
                f"{point_id}::{sorted(point_direct_relation_bindings)[0]}",
            )
        declared_relations = descriptor.get("relation_counts")
        if not isinstance(declared_relations, Mapping) or set(declared_relations) - {
            "support",
            "counter",
            "adjacent",
        }:
            raise EvidenceConsumerError(
                "point_projection", f"declared relation counts invalid: {point_id}"
            )
        expected_relations = {
            relation_name: declared_relations.get(relation_name, 0)
            for relation_name in ("support", "counter", "adjacent")
        }
        if observed_relations != expected_relations:
            raise EvidenceConsumerError(
                "point_projection", f"display relation counts changed: {point_id}"
            )
        if len(point_placement_ids) != descriptor.get("display_row_count"):
            raise EvidenceConsumerError(
                "point_projection", f"display row count changed: {point_id}"
            )
        if (
            artifact.get("truth_group_count") != descriptor.get("truth_origin_count")
            or len(point_truth_origin_ids) != descriptor.get("truth_origin_count")
        ):
            raise EvidenceConsumerError(
                "point_projection", f"truth origin count changed: {point_id}"
            )
        axis_truth_origin_ids.update(point_truth_origin_ids)
        group_id, family_id = point_navigation[point_id]
        point_entry = {
                "point_id": point_id,
                "bounded_point": artifact["bounded_point"],
                "navigation_group_id": group_id,
                "family_id": family_id,
                "policy_revision": descriptor.get("policy_revision"),
                "candidate_count": len(candidate_by_id),
                "candidate_inventory_sha256": artifact["candidate_inventory_sha256"],
                "truth_origin_count": artifact["truth_group_count"],
                "support_origin_ids": sorted(relation_origin_ids["support"]),
                "counter_origin_ids": sorted(relation_origin_ids["counter"]),
                "adjacent_origin_ids": sorted(relation_origin_ids["adjacent"]),
                "placement_ids": sorted(point_placement_ids),
                "bindings": bindings,
            }
        if is_routed_v2:
            point_entry["projection_mode"] = point_projections[point_id]
            point_entry["displayed_relation_row_counts"] = copy.deepcopy(
                observed_relations
            )
            point_entry["same_origin_observation_groups"] = (
                same_origin_observation_groups
            )
        point_index.append(point_entry)

    normalized_origins = []
    for origin_id in sorted(origins):
        origin = origins[origin_id]
        normalized_origins.append(
            {
                "origin_group_id": origin_id,
                "independence_key": origin["independence_key"],
                "independence_posture": origin["independence_posture"],
                "evidence_ids": sorted(origin["evidence_ids"]),
                "placement_ids": sorted(origin["placement_ids"]),
                "container_ids": sorted(origin["container_ids"]),
            }
        )
    normalized_evidence = [evidence[key] for key in sorted(evidence)]
    normalized_quotes = [quote_spans[key] for key in sorted(quote_spans)]
    normalized_companions = [companion_meanings[key] for key in sorted(companion_meanings)]
    normalized_placements = sorted(placements, key=lambda row: row["placement_id"])
    normalized_decision_state_groups = sorted(
        decision_state_groups, key=lambda row: row["decision_state_group_id"]
    )
    _validate_decision_state_semantic_consistency(normalized_decision_state_groups)
    point_index.sort(key=lambda row: row["point_id"])

    engagement_buckets: dict[tuple[str, str, str, str, str], set[str]] = defaultdict(set)
    for row in normalized_evidence:
        engagement = row["engagement"]
        year = _publication_year(row.get("publication_time"))
        key = (
            row["content_surface"],
            row["source_venue"],
            row["source_role"],
            str(engagement.get("kind") or "engagement_unavailable"),
            str(year) if year is not None else "undated",
        )
        engagement_buckets[key].add(row["evidence_id"])
    normalized_buckets = [
        {
            "content_surface": key[0],
            "source_venue": key[1],
            "source_role": key[2],
            "engagement_kind": key[3],
            "calendar_year": key[4],
            "comparison_boundary": (
                "not_comparable_without_observation_year"
                if key[4] == "undated"
                else "within_bucket_only"
            ),
            "evidence_ids": sorted(values),
        }
        for key, values in sorted(engagement_buckets.items())
    ]

    container_origins: dict[str, set[str]] = defaultdict(set)
    container_evidence: dict[str, set[str]] = defaultdict(set)
    for row in normalized_evidence:
        for container_id in row["container_ids"]:
            container_origins[container_id].add(row["origin_group_id"])
            container_evidence[container_id].add(row["evidence_id"])
    concentrations = [
        {
            "container_id": container_id,
            "distinct_origin_count": len(container_origins[container_id]),
            "origin_group_ids": sorted(container_origins[container_id]),
            "evidence_ids": sorted(container_evidence[container_id]),
        }
        for container_id in sorted(container_origins)
        if len(container_origins[container_id]) > 1
    ]

    embedded_spec = copy.deepcopy(dict(spec))
    decision_state_binding_sha256: str | None = None
    if normalized_decision_state_groups:
        normalized_binding_payload = _bindings_from_decision_state_groups(
            normalized_decision_state_groups,
            placements={
                row["placement_id"]: row for row in normalized_placements
            },
        )
        decision_state_binding_sha256 = _canonical_json_sha256(
            normalized_binding_payload
        )
        declared_binding_sha256 = spec.get("decision_state_bindings_sha256")
        if declared_binding_sha256 not in (None, decision_state_binding_sha256):
            raise EvidenceConsumerError(
                "decision_state_binding", "decision-state binding identity changed"
            )
        embedded_spec.pop("decision_state_bindings", None)
        embedded_spec["decision_state_bindings_sha256"] = decision_state_binding_sha256

    view: dict[str, Any] = {
        "schema_version": (
            CONSOLIDATED_VIEW_VERSION
            if is_routed_v2
            else LEGACY_CONSOLIDATED_VIEW_VERSION
        ),
        "policy": CONSOLIDATION_POLICY if is_routed_v2 else LEGACY_CONSOLIDATION_POLICY,
        "axis_id": axis_id,
        "spec": embedded_spec,
        "source_axis_pack": {
            "path": str(axis_path),
            "raw_sha256": expected_axis_hash,
            "schema_version": axis_pack["schema_version"],
        },
        "navigation_groups": navigation,
        "point_index": point_index,
        "origin_index": normalized_origins,
        "evidence_index": normalized_evidence,
        "quote_spans": normalized_quotes,
        "companion_meaning_index": normalized_companions,
        "point_placements": normalized_placements,
        "engagement_buckets": normalized_buckets,
        "container_concentrations": concentrations,
        "counts": {
            "point_count": len(point_index),
            "candidate_disposition_count": candidate_total,
            "placement_count": len(normalized_placements),
            "unique_origin_count": len(normalized_origins),
            "credited_origin_count": sum(
                row["independence_posture"] == "credited" for row in normalized_origins
            ),
            "uncredited_origin_count": sum(
                row["independence_posture"] != "credited" for row in normalized_origins
            ),
            "unique_evidence_count": len(normalized_evidence),
            "unique_quote_span_count": len(normalized_quotes),
            "unique_companion_meaning_count": len(normalized_companions),
            "available_quote_span_count": sum(
                row["quote_status"] == "quote_available" for row in normalized_quotes
            ),
            "unavailable_quote_span_count": sum(
                row["quote_status"] == "quote_unavailable" for row in normalized_quotes
            ),
        },
        "non_claims": [
            "origin counts are evidence-origin groups, not people or prevalence; "
            "independence posture is explicit per origin",
            "engagement is source-native resonance and is not independent-origin credit",
            "dated engagement values are comparable only inside one declared "
            "content-surface bucket; undated values are not comparable",
            "the view does not change point relations, selection, or evidence authority",
        ],
    }
    if is_routed_v2:
        view["projection_routes"] = projection_routes
        view["evidence_accounting_contract"] = copy.deepcopy(
            EVIDENCE_ACCOUNTING_CONTRACT
        )
        view["non_claims"].extend(DIRECT_OUTCOME_BOUNDARIES)
        view["non_claims"].append(
            "multiple dated observations from one origin remain one origin and do not by "
            "themselves establish multiple underlying events"
        )
        if decision_state_bindings:
            rejected_points = axis_pack.get("rejected_points")
            if not isinstance(rejected_points, list):
                raise EvidenceConsumerError(
                    "decision_state_binding", "source axis rejected-point index is invalid"
                )
            view["decision_state_contract"] = copy.deepcopy(
                DECISION_STATE_CONSUMER_CONTRACT
            )
            view["decision_state_index"] = _compact_decision_state_index(
                normalized_decision_state_groups
            )
            view["decision_state_groups"] = [
                _compact_decision_state_group(group)
                for group in normalized_decision_state_groups
            ]
            view["rejected_point_index"] = _decision_state_rejected_index(
                spec, rejected_points, navigation
            )
            view["counts"]["decision_state_group_count"] = len(
                normalized_decision_state_groups
            )
            view["counts"]["decision_state_assertion_count"] = sum(
                len(row["state_assertions"]) for row in normalized_decision_state_groups
            )
            view["counts"]["rejected_point_count"] = len(rejected_points)
            view["non_claims"].extend(DECISION_STATE_BOUNDARIES)
            view["decision_state_reader_surface"] = _decision_state_reader_surface(view)
    if view["counts"]["point_count"] != axis_pack.get("valid_point_count"):
        raise EvidenceConsumerError("axis_parity", "point count differs from source axis pack")
    if view["counts"]["candidate_disposition_count"] != axis_pack.get(
        "cold_reader_resolution", {}
    ).get("resolved_candidate_disposition_count"):
        raise EvidenceConsumerError("axis_parity", "candidate disposition count changed")
    if view["counts"]["placement_count"] != axis_pack.get("display_row_slots"):
        raise EvidenceConsumerError("axis_parity", "display placement count changed")
    if len(axis_truth_origin_ids) != axis_pack.get("unique_truth_origins_across_axis"):
        raise EvidenceConsumerError("axis_parity", "unique truth origin count changed")
    if view["counts"]["unique_evidence_count"] != axis_pack.get(
        "unique_evidence_items_across_axis"
    ):
        raise EvidenceConsumerError("axis_parity", "unique evidence count changed")
    view["view_sha256"] = _canonical_json_sha256(view)
    return view


def validate_axis_consolidated_view(
    view: Mapping[str, Any], *, expected_view_sha256: str
) -> dict[str, Any]:
    """Reproject a saved view and require one externally trusted view identity."""

    if view.get("schema_version") not in {
        LEGACY_CONSOLIDATED_VIEW_VERSION,
        CONSOLIDATED_VIEW_VERSION,
    }:
        raise EvidenceConsumerError("view_verification", "unsupported view version")
    stored = view.get("view_sha256")
    if stored != expected_view_sha256:
        raise EvidenceConsumerError(
            "view_verification", "trusted view identity differs from saved view"
        )
    payload = {key: value for key, value in view.items() if key != "view_sha256"}
    if not isinstance(stored, str) or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError("view_verification", "stored view hash is invalid")
    spec = view.get("spec")
    if not isinstance(spec, Mapping):
        raise EvidenceConsumerError("view_verification", "embedded spec missing")
    rebuild_spec = copy.deepcopy(dict(spec))
    if view.get("schema_version") == CONSOLIDATED_VIEW_VERSION and isinstance(
        view.get("decision_state_groups"), list
    ):
        placements = {
            row["placement_id"]: row
            for row in view.get("point_placements", [])
            if isinstance(row, Mapping) and isinstance(row.get("placement_id"), str)
        }
        rebuild_spec["decision_state_bindings"] = _bindings_from_decision_state_groups(
            _expand_compact_decision_state_groups(view), placements=placements
        )
    rebuilt = build_axis_consolidated_view(rebuild_spec)
    if rebuilt != dict(view):
        raise EvidenceConsumerError(
            "view_reprojection", "saved view differs from deterministic source projection"
        )
    return rebuilt


def build_axis_dogfood_truth_index(
    view: Mapping[str, Any], *, source_view_path: Path
) -> dict[str, Any]:
    """Build a compact exact-fact index for blind representation comparisons.

    The index owns only facts copied or mechanically derived from the validated
    consolidated view. Absence from this index is never evidence that a detail
    was invented; the source view remains the exact-detail authority.
    """

    source_view_path = source_view_path.resolve()
    source_bytes = source_view_path.read_bytes()
    source_file_value = json.loads(source_bytes.decode("utf-8-sig"))
    if not isinstance(source_file_value, dict) or source_file_value != dict(view):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification",
            "source view path does not contain the supplied view",
        )
    validated = validate_axis_consolidated_view(
        view, expected_view_sha256=_required_string(
            view, "view_sha256", boundary="dogfood_truth_index_verification"
        )
    )
    point_rows = validated.get("point_index")
    placement_rows = validated.get("point_placements")
    routes = validated.get("projection_routes")
    if (
        not isinstance(point_rows, list)
        or not isinstance(placement_rows, list)
        or not isinstance(routes, list)
    ):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification",
            "validated view lacks point, placement, or routing facts",
        )

    reader_point_by_id: dict[str, dict[str, Any]] = {}
    reader = validated.get("decision_state_reader_surface")
    if isinstance(reader, Mapping):
        point_table = reader.get("point_table")
        if not isinstance(point_table, Mapping):
            raise EvidenceConsumerError(
                "dogfood_truth_index_verification",
                "decision-state reader point table is missing",
            )
        columns = point_table.get("columns")
        rows = point_table.get("rows")
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise EvidenceConsumerError(
                "dogfood_truth_index_verification",
                "decision-state reader point table is invalid",
            )
        for row in rows:
            if not isinstance(row, list) or len(row) != len(columns):
                raise EvidenceConsumerError(
                    "dogfood_truth_index_verification",
                    "decision-state reader point row is invalid",
                )
            expanded = dict(zip(columns, row, strict=True))
            point_id = expanded.get("point_id")
            if not isinstance(point_id, str) or point_id in reader_point_by_id:
                raise EvidenceConsumerError(
                    "dogfood_truth_index_verification",
                    "decision-state reader point identity is invalid",
                )
            reader_point_by_id[point_id] = expanded

    placements_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for placement in placement_rows:
        if not isinstance(placement, Mapping):
            raise EvidenceConsumerError(
                "dogfood_truth_index_verification", "point placement is invalid"
            )
        point_id = _required_string(
            placement, "point_id", boundary="dogfood_truth_index_verification"
        )
        placements_by_point[point_id].append(copy.deepcopy(dict(placement)))

    accepted_points: list[dict[str, Any]] = []
    for point in sorted(point_rows, key=lambda row: row["point_id"]):
        if not isinstance(point, Mapping):
            raise EvidenceConsumerError(
                "dogfood_truth_index_verification", "point index row is invalid"
            )
        point_id = _required_string(
            point, "point_id", boundary="dogfood_truth_index_verification"
        )
        accepted = {
            "point_id": point_id,
            "bounded_point": _required_string(
                point, "bounded_point", boundary="dogfood_truth_index_verification"
            ),
            "projection_mode": _required_string(
                point, "projection_mode", boundary="dogfood_truth_index_verification"
            ),
            "relation_origin_ids": {
                relation: copy.deepcopy(point.get(f"{relation}_origin_ids", []))
                for relation in ("support", "counter", "adjacent")
            },
            "same_origin_observation_groups": copy.deepcopy(
                point.get("same_origin_observation_groups", [])
            ),
            "placements": sorted(
                placements_by_point.pop(point_id, []),
                key=lambda row: row["placement_id"],
            ),
        }
        reader_point = reader_point_by_id.get(point_id)
        if reader_point is not None:
            accepted["state_table"] = copy.deepcopy(reader_point["state_table"])
            accepted["relation_facts"] = copy.deepcopy(reader_point["relation_facts"])
        accepted_points.append(accepted)
    if placements_by_point:
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification",
            "placement references a point outside the accepted point index",
        )

    source_axis_pack = validated.get("source_axis_pack")
    if not isinstance(source_axis_pack, Mapping):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "source axis pack binding is missing"
        )
    axis_pack_path = Path(
        _required_string(
            source_axis_pack, "path", boundary="dogfood_truth_index_verification"
        )
    )
    axis_pack = _load_object(axis_pack_path, boundary="dogfood_truth_index_verification")
    rejected_points = validated.get("rejected_point_index")
    if rejected_points is None:
        # An absent rejected frontier is unknown, never an empty one. Defaulting
        # it to [] would let this builder, its rebuild validator, and a dogfood
        # judge all assert that no point was ever rejected.
        rejected_points = axis_pack.get("rejected_points")
        if rejected_points is None:
            raise EvidenceConsumerError(
                "dogfood_truth_index_verification",
                "source axis pack states no rejected-point frontier",
            )
    if not isinstance(rejected_points, list):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "rejected point index is invalid"
        )
    rejected_points = sorted(
        copy.deepcopy(rejected_points), key=lambda row: row["point_id"]
    )
    accepted_ids = [row["point_id"] for row in accepted_points]
    rejected_ids = [row["point_id"] for row in rejected_points]
    routed_ids = sorted(
        point_id for route in routes for point_id in route.get("point_ids", [])
    )
    if routed_ids != sorted(accepted_ids) or set(routed_ids) & set(rejected_ids):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification",
            "projection routes must cover accepted points only",
        )

    truth_index: dict[str, Any] = {
        "schema_version": DOGFOOD_TRUTH_INDEX_VERSION,
        "axis_id": validated["axis_id"],
        "source_view": {
            "path": str(source_view_path),
            "raw_sha256": hash_file(source_view_path),
            "view_sha256": validated["view_sha256"],
        },
        "source_axis_pack": copy.deepcopy(dict(source_axis_pack)),
        "counts": {
            "accepted_point_count": len(accepted_points),
            "rejected_point_count": len(rejected_points),
            "frontier_point_count": len(accepted_points) + len(rejected_points),
        },
        "projection_routes": copy.deepcopy(routes),
        "accepted_points": accepted_points,
        "rejected_points": rejected_points,
        "exact_detail_authority": {
            "rule": (
                "absence from this index is not evidence of invention; resolve disputed "
                "source, date, engagement, origin, relation, quote, or companion details "
                "against the validated source view"
            ),
            "source_view_sections": [
                "origin_index",
                "evidence_index",
                "quote_spans",
                "companion_meaning_index",
                "point_placements",
            ],
        },
        "non_claims": copy.deepcopy(validated.get("non_claims", [])),
    }
    truth_index["truth_index_sha256"] = _canonical_json_sha256(truth_index)
    return truth_index


def validate_axis_dogfood_truth_index(
    truth_index: Mapping[str, Any], *, expected_truth_index_sha256: str
) -> dict[str, Any]:
    """Rebuild a saved dogfood truth index from its validated source view."""

    if truth_index.get("schema_version") != DOGFOOD_TRUTH_INDEX_VERSION:
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "unsupported truth index version"
        )
    stored = truth_index.get("truth_index_sha256")
    if stored != expected_truth_index_sha256:
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification",
            "trusted truth index identity differs from saved index",
        )
    payload = {
        key: value for key, value in truth_index.items() if key != "truth_index_sha256"
    }
    if not isinstance(stored, str) or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "stored truth index hash is invalid"
        )
    source_view = truth_index.get("source_view")
    if not isinstance(source_view, Mapping):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "source view binding is missing"
        )
    source_path = Path(
        _required_string(
            source_view, "path", boundary="dogfood_truth_index_verification"
        )
    )
    if hash_file(source_path) != source_view.get("raw_sha256"):
        raise EvidenceConsumerError(
            "dogfood_truth_index_verification", "source view raw bytes changed"
        )
    view = _load_object(source_path, boundary="dogfood_truth_index_verification")
    rebuilt = build_axis_dogfood_truth_index(view, source_view_path=source_path)
    if rebuilt != dict(truth_index):
        raise EvidenceConsumerError(
            "dogfood_truth_index_reprojection",
            "saved truth index differs from the validated source view",
        )
    return rebuilt


def point_placement_keys(view: Mapping[str, Any]) -> list[tuple[Any, ...]]:
    """Return the exact claim-relative facts used by dogfood parity checks."""

    rows = view.get("point_placements")
    if not isinstance(rows, Sequence):
        raise EvidenceConsumerError("view_verification", "point placements missing")
    return sorted(
        (
            row["point_id"],
            row["selected_id"],
            row["origin_group_id"],
            row["evidence_id"],
            row["semantic_unit_ref"],
            row["relation"],
            tuple(row["candidate_context"]["conditions"]),
            tuple(row["candidate_context"]["product_version_ids"]),
            row["quote_span_id"],
        )
        for row in rows
        if isinstance(row, Mapping)
    )
