"""Origin-normalized presentation over completed Phase A point artifacts.

The view produced here is a derived consumer projection.  It does not relabel,
reselect, or copy the complete candidate inventories owned by the completed
point artifacts.  Instead it verifies those artifacts and their cold source
bindings, stores each selected origin/evidence item once, and preserves the
claim-relative placement needed to reconstruct every displayed point.
"""
from __future__ import annotations

import copy
import hashlib
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
    _expand_packet,
    _verify_packet,
)
from judgment.phase_a_evidence_selection import (
    PARENT_CONTEXT_POLICY,
    SELECTION_BATCH_MANIFEST_VERSION,
    _candidate_rows,
    _verify_bundle,
    load_selection_sources,
    verify_customer_pull_point_frontier,
)


AXIS_PACK_MANIFEST_VERSION = "phase_a_evidence_axis_pack_manifest_v1"
AXIS_PACK_VERSION = "phase_a_evidence_axis_pack_v1"
NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION = "phase_a_evidence_axis_pack_manifest_v2"
NO_FRONTIER_AXIS_PACK_VERSION = "phase_a_evidence_axis_pack_v2"
LEGACY_CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v1"
CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v2"
LEGACY_CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v1"
CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v2"
DOGFOOD_TRUTH_INDEX_VERSION = "phase_a_evidence_axis_dogfood_truth_index_v1"
AXIS_READER_MANIFEST_VERSION = "phase_a_evidence_axis_reader_manifest_v1"
POINT_READER_RUN_MANIFEST_VERSION = "phase_a_evidence_point_reader_run_manifest_v1"
POINT_READER_BRIEF_VERSION = "phase_a_evidence_point_brief_v2"
POINT_READER_REQUEST_VERSION = "phase_a_evidence_point_reader_request_v2"
POINT_READER_AXIS_OUTPUT_VERSION = "phase_a_evidence_point_reader_axis_output_v1"
POINT_READER_SUBJECT_IDENTITY_VERSION = "phase_a_point_reader_subject_identity_v1"
POINT_READER_METHOD_TEXT = (
    "Read exactly one complete Phase A evidence point. Explain only its bounded point. "
    "Use the supplied relation and literal evidence without relabelling either. Preserve "
    "counterevidence and awkward coexistence. For Decision State, distinguish judgment, "
    "intent, observed action, quantity, object, and conditions; never turn intent into "
    "observed behavior or several purchased units into several repurchases. Do not infer "
    "prevalence, causation, market representativeness, pricing power, or a Deliver "
    "recommendation. Cite only supplied point-local placement handles."
)
POINT_READER_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "point_input_sha256",
        "point_id",
        "interpretation",
        "representative_handles",
    ],
    "properties": {
        "point_input_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "point_id": {"type": "string"},
        "interpretation": {"type": "string", "minLength": 1},
        "representative_handles": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["placement_id"],
                "properties": {
                    "placement_id": {"type": "string"},
                },
            },
        },
    },
}
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
    selection_container = _load_object(selection_path, boundary="candidate_access")
    if selection_container.get("schema_version") == SELECTION_BATCH_MANIFEST_VERSION:
        _verify_manifest_hash(
            selection_container,
            expected=selection_container.get("manifest_sha256"),
            boundary="candidate_access",
        )
        selection_manifest = selection_container.get("selection_manifest")
        if not isinstance(selection_manifest, Mapping):
            raise EvidenceConsumerError(
                "candidate_access",
                f"selection batch manifest is missing its embedded manifest: {point_id}",
            )
    else:
        selection_manifest = selection_container
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


def _no_frontier_axis_candidates(
    *,
    axis_id: str,
    subject_product_ids: Sequence[str],
    source_id: str,
    packet: Mapping[str, Any],
    bundle: Mapping[str, Any],
    packet_path: Path,
    bundle_path: Path,
) -> list[dict[str, Any]]:
    sources = [
        {
            "source_id": source_id,
            "packet": packet,
            "bundle": bundle,
            "packet_path": packet_path,
            "bundle_path": bundle_path,
        }
    ]
    candidates = _candidate_rows(
        sources,
        {
            "axis_ids": [axis_id],
            "subject_product_ids": list(subject_product_ids),
            "admit_semantic_refs": [],
            "protected_evidence_ids": {},
        },
    )
    if not candidates:
        raise EvidenceConsumerError(
            "no_frontier_axis_candidates",
            "a no-frontier pack requires axis-tagged evidence candidates",
        )
    refs = [row.get("semantic_unit_ref") for row in candidates]
    if (
        not all(isinstance(value, str) and value for value in refs)
        or len(refs) != len(set(refs))
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_candidates",
            "axis candidate semantic identities are invalid",
        )
    return candidates


def _no_frontier_axis_disposition(
    frontier: Mapping[str, Any], packet: Mapping[str, Any], axis_id: str
) -> dict[str, Any]:
    proposition_axes = {
        row.get("proposition_id"): set(row.get("axis_ids") or [])
        for row in packet.get("propositions", [])
        if isinstance(row, Mapping) and isinstance(row.get("proposition_id"), str)
    }
    admitted_ids = sorted(
        {
            row["proposition_id"]
            for queue in ("retailer_first_queue", "community_discovery_queue")
            for row in frontier.get(queue, [])
            if isinstance(row, Mapping)
            and isinstance(row.get("proposition_id"), str)
            and axis_id in set(row.get("axis_ids") or [])
        }
    )
    if admitted_ids:
        raise EvidenceConsumerError(
            "no_frontier_axis_status",
            f"axis already has admitted frontier points: {admitted_ids}",
        )
    nonpromoted_ids = sorted(
        {
            row["proposition_id"]
            for row in frontier.get("nonpromoted_points", [])
            if isinstance(row, Mapping)
            and isinstance(row.get("proposition_id"), str)
            and axis_id in proposition_axes.get(row["proposition_id"], set())
        }
    )
    return {
        "disposition": "no_admitted_frontier_point",
        "admitted_point_ids": admitted_ids,
        "nonpromoted_point_ids": nonpromoted_ids,
    }


def materialize_phase_a_evidence_no_frontier_axis_manifest(
    *,
    axis_id: str,
    subject_product_ids: Sequence[str],
    source_id: str,
    packet_path: Path,
    bundle_path: Path,
    frontier_path: Path,
) -> dict[str, Any]:
    """Bind an evidence-rich axis that has no admitted frontier point.

    This is not a fallback point generator. It preserves the exact axis-tagged
    candidate inventory and the verified frontier absence without assigning
    support/counter relations that require a bounded point.
    """

    if not isinstance(axis_id, str) or not axis_id.strip():
        raise EvidenceConsumerError("no_frontier_axis_manifest", "axis_id missing")
    if (
        not isinstance(source_id, str)
        or not source_id
        or not subject_product_ids
        or not all(isinstance(value, str) and value for value in subject_product_ids)
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "source and subject identities are invalid"
        )
    packet = _load_object(packet_path, boundary="no_frontier_axis_manifest")
    bundle = _load_object(bundle_path, boundary="no_frontier_axis_manifest")
    frontier = _load_object(frontier_path, boundary="no_frontier_axis_manifest")
    _verify_packet(packet)
    _verify_bundle(bundle)
    if packet.get("source_bindings", {}).get("bundle_sha256") != bundle.get(
        "bundle_sha256"
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "packet and bundle identities differ"
        )
    verify_customer_pull_point_frontier(frontier, packet)
    subjects = sorted(set(subject_product_ids))
    if subjects != sorted(frontier.get("subject_product_ids") or []):
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "frontier subject identity differs"
        )
    _no_frontier_axis_disposition(frontier, packet, axis_id)
    candidates = _no_frontier_axis_candidates(
        axis_id=axis_id,
        subject_product_ids=subjects,
        source_id=source_id,
        packet=packet,
        bundle=bundle,
        packet_path=packet_path,
        bundle_path=bundle_path,
    )
    manifest: dict[str, Any] = {
        "schema_version": NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION,
        "axis_id": axis_id,
        "subject_product_ids": subjects,
        "source_id": source_id,
        "packet_path": str(packet_path),
        "packet_file_sha256": hash_file(packet_path),
        "packet_sha256": packet["packet_sha256"],
        "bundle_path": str(bundle_path),
        "bundle_file_sha256": hash_file(bundle_path),
        "bundle_sha256": bundle["bundle_sha256"],
        "frontier_path": str(frontier_path),
        "frontier_file_sha256": hash_file(frontier_path),
        "frontier_sha256": frontier["frontier_sha256"],
        "expected_semantic_unit_refs": sorted(
            row["semantic_unit_ref"] for row in candidates
        ),
        "candidate_inventory_sha256": _canonical_json_sha256(candidates),
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest, "manifest_sha256")
    return manifest


def _build_no_frontier_axis_pack(manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "axis_id",
        "subject_product_ids",
        "source_id",
        "packet_path",
        "packet_file_sha256",
        "packet_sha256",
        "bundle_path",
        "bundle_file_sha256",
        "bundle_sha256",
        "frontier_path",
        "frontier_file_sha256",
        "frontier_sha256",
        "expected_semantic_unit_refs",
        "candidate_inventory_sha256",
        "manifest_sha256",
    }
    if set(manifest) != expected_fields:
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "manifest fields are invalid"
        )
    stored_manifest_hash = manifest.get("manifest_sha256")
    if not isinstance(stored_manifest_hash, str) or stored_manifest_hash != _canonical_hash(
        manifest, "manifest_sha256"
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "stored manifest hash is invalid"
        )
    axis_id = _required_string(
        manifest, "axis_id", boundary="no_frontier_axis_manifest"
    )
    source_id = _required_string(
        manifest, "source_id", boundary="no_frontier_axis_manifest"
    )
    subjects = manifest.get("subject_product_ids")
    expected_refs = manifest.get("expected_semantic_unit_refs")
    if (
        not isinstance(subjects, list)
        or subjects != sorted(set(subjects))
        or not subjects
        or not all(isinstance(value, str) and value for value in subjects)
        or not isinstance(expected_refs, list)
        or expected_refs != sorted(set(expected_refs))
        or not expected_refs
        or not all(isinstance(value, str) and value for value in expected_refs)
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_manifest", "candidate scope is invalid"
        )
    paths = {
        key: Path(_required_string(manifest, key, boundary="no_frontier_axis_manifest"))
        for key in ("packet_path", "bundle_path", "frontier_path")
    }
    for stem in ("packet", "bundle", "frontier"):
        if not paths[f"{stem}_path"].is_file() or hash_file(
            paths[f"{stem}_path"]
        ) != _required_string(
            manifest, f"{stem}_file_sha256", boundary="no_frontier_axis_manifest"
        ):
            raise EvidenceConsumerError(
                "no_frontier_axis_source", f"bound {stem} file changed"
            )
    packet = _load_object(paths["packet_path"], boundary="no_frontier_axis_source")
    bundle = _load_object(paths["bundle_path"], boundary="no_frontier_axis_source")
    frontier = _load_object(
        paths["frontier_path"], boundary="no_frontier_axis_source"
    )
    _verify_packet(packet)
    _verify_bundle(bundle)
    if (
        packet.get("packet_sha256") != manifest.get("packet_sha256")
        or bundle.get("bundle_sha256") != manifest.get("bundle_sha256")
        or frontier.get("frontier_sha256") != manifest.get("frontier_sha256")
        or packet.get("source_bindings", {}).get("bundle_sha256")
        != bundle.get("bundle_sha256")
    ):
        raise EvidenceConsumerError(
            "no_frontier_axis_source", "bound source identity changed"
        )
    verify_customer_pull_point_frontier(frontier, packet)
    if subjects != sorted(frontier.get("subject_product_ids") or []):
        raise EvidenceConsumerError(
            "no_frontier_axis_source", "frontier subject identity differs"
        )
    disposition = _no_frontier_axis_disposition(frontier, packet, axis_id)
    candidates = _no_frontier_axis_candidates(
        axis_id=axis_id,
        subject_product_ids=subjects,
        source_id=source_id,
        packet=packet,
        bundle=bundle,
        packet_path=paths["packet_path"],
        bundle_path=paths["bundle_path"],
    )
    observed_refs = sorted(row["semantic_unit_ref"] for row in candidates)
    if observed_refs != expected_refs:
        raise EvidenceConsumerError(
            "no_frontier_axis_candidate_accounting",
            "axis candidate semantic coverage changed",
        )
    candidate_inventory_sha256 = _canonical_json_sha256(candidates)
    if candidate_inventory_sha256 != manifest.get("candidate_inventory_sha256"):
        raise EvidenceConsumerError(
            "no_frontier_axis_candidate_inventory",
            "axis candidate facts or source attachment changed",
        )
    unique_evidence = {row["evidence_id"] for row in candidates}
    unique_origins = {row["scoped_independence_key"] for row in candidates}
    bindings = {
        key: manifest[key]
        for key in (
            "packet_path",
            "packet_file_sha256",
            "packet_sha256",
            "bundle_path",
            "bundle_file_sha256",
            "bundle_sha256",
            "frontier_path",
            "frontier_file_sha256",
            "frontier_sha256",
        )
    }
    pack: dict[str, Any] = {
        "schema_version": NO_FRONTIER_AXIS_PACK_VERSION,
        "status": "complete_no_admitted_frontier_point_axis_pack",
        "axis_id": axis_id,
        "subject_product_ids": copy.deepcopy(subjects),
        "source_id": source_id,
        "source_manifest": {
            "schema_version": NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION,
            "manifest_sha256": stored_manifest_hash,
        },
        "source_bindings": bindings,
        "valid_point_count": 0,
        "rejected_point_count": 0,
        "frontier_point_count": 0,
        "candidate_semantic_unit_count": len(candidates),
        "unique_evidence_items_across_axis": len(unique_evidence),
        "unique_origins_across_axis": len(unique_origins),
        "candidate_inventory_sha256": candidate_inventory_sha256,
        "frontier_resolution": disposition,
        "candidate_inventory": copy.deepcopy(candidates),
        "reading_contract": {
            "axis_assignment": (
                "axis_ids preserve routing relevance only; without a bounded point they do not "
                "make a row support, counter, or direct product-performance evidence"
            ),
            "engagement": (
                "engagement_context describes the source metric and its positive threshold; "
                "engagement_material_positive is the row-level threshold result, raw_value is "
                "descriptive resonance only, and neither changes evidence truth"
            ),
            "polarity": (
                "polarity describes how the normalized statement is expressed relative to its "
                "own predicate; it is not overall sentiment, product value, or an axis verdict "
                "and must not be aggregated across rows"
            ),
            "evidence_posture": (
                "questions, expectations, intentions, attributed reports, and first-hand "
                "experiences remain distinct through evidence and uncertainty posture"
            ),
            "conflict": (
                "conflicting source-native details stay unresolved unless separate authority "
                "adjudicates them; coexistence is not a defect or an invitation to average"
            ),
            "counting": (
                "candidate rows are semantic statements, unique evidence items are source "
                "observations, and unique origins are origin groups; none is a people or "
                "prevalence count"
            ),
        },
        "cold_reader_resolution": {
            "resolved_candidate_disposition_count": len(candidates),
            "path_resolution": "explicit_manifest_paths_only",
            "literal_source_text": "recover_from_hash_pinned_bundle",
        },
        "non_claims": [
            "no admitted frontier point does not mean no evidence or no meaningful pattern",
            "candidate rows have no support/counter relation until a bounded point is admitted",
            "the inventory does not estimate prevalence, causation, market representativeness, or commercial pull",
            "the inventory is Phase A evidence packaging and makes no Deliver recommendation",
        ],
    }
    pack["axis_pack_sha256"] = _canonical_hash(pack, "axis_pack_sha256")
    return pack


def build_phase_a_evidence_axis_pack(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build a generic, cold-resolvable Phase A axis pack from explicit pins."""

    if manifest.get("schema_version") == NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION:
        return _build_no_frontier_axis_pack(manifest)
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

    if pack.get("schema_version") == NO_FRONTIER_AXIS_PACK_VERSION:
        stored = pack.get("axis_pack_sha256")
        if stored != expected_axis_pack_sha256:
            raise EvidenceConsumerError(
                "axis_pack_verification",
                "trusted axis pack identity differs from saved pack",
            )
        if not isinstance(stored, str) or stored != _canonical_hash(
            pack, "axis_pack_sha256"
        ):
            raise EvidenceConsumerError(
                "axis_pack_verification", "stored axis pack hash is invalid"
            )
        source_manifest = pack.get("source_manifest")
        bindings = pack.get("source_bindings")
        candidates = pack.get("candidate_inventory")
        if (
            not isinstance(source_manifest, Mapping)
            or source_manifest.get("schema_version")
            != NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION
            or not isinstance(source_manifest.get("manifest_sha256"), str)
            or not isinstance(bindings, Mapping)
            or not isinstance(candidates, list)
            or not candidates
            or not all(isinstance(row, Mapping) for row in candidates)
        ):
            raise EvidenceConsumerError(
                "axis_pack_verification", "no-frontier axis pack closure is invalid"
            )
        refs = sorted(
            row.get("semantic_unit_ref")
            for row in candidates
            if isinstance(row.get("semantic_unit_ref"), str)
        )
        if len(refs) != len(candidates) or len(refs) != len(set(refs)):
            raise EvidenceConsumerError(
                "axis_pack_verification", "candidate semantic identities are invalid"
            )
        manifest: dict[str, Any] = {
            "schema_version": NO_FRONTIER_AXIS_PACK_MANIFEST_VERSION,
            "axis_id": pack.get("axis_id"),
            "subject_product_ids": copy.deepcopy(pack.get("subject_product_ids")),
            "source_id": pack.get("source_id"),
            **copy.deepcopy(dict(bindings)),
            "expected_semantic_unit_refs": refs,
            "candidate_inventory_sha256": pack.get("candidate_inventory_sha256"),
            "manifest_sha256": source_manifest["manifest_sha256"],
        }
        if _canonical_hash(manifest, "manifest_sha256") != source_manifest[
            "manifest_sha256"
        ]:
            raise EvidenceConsumerError(
                "axis_pack_verification", "source manifest identity changed"
            )
        rebuilt = build_phase_a_evidence_axis_pack(manifest)
        if rebuilt != dict(pack):
            raise EvidenceConsumerError(
                "axis_pack_reprojection",
                "saved axis pack differs from deterministic source projection",
            )
        return rebuilt
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


def _axis_reader_fact_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    """Serialize complete reader facts deterministically as one JSON object per line."""

    return b"".join(
        json.dumps(
            dict(row),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
        for row in rows
    )


def _axis_reader_point_filename(point_id: str) -> str:
    """Keep ordinary point ids readable without restricting valid identities."""

    if (
        point_id not in {".", ".."}
        and all(character.isalnum() or character in "._-" for character in point_id)
    ):
        return f"{point_id}.jsonl"
    digest = hashlib.sha256(point_id.encode("utf-8")).hexdigest()
    return f"point_{digest}.jsonl"


def build_axis_reader_bundle(
    view: Mapping[str, Any], *, source_view_path: Path, facts_dir: Path
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Build a route-aware manifest plus self-contained fact stream for cold readers.

    The validated consolidated view remains authoritative.  This bundle changes only
    physical reading locality: every displayed placement carries its literal meaning,
    provenance, quote, companions, and any authored decision states in one fact.
    """

    source_view_path = source_view_path.resolve()
    facts_dir = facts_dir.resolve()
    source_bytes = source_view_path.read_bytes()
    source_file_value = json.loads(source_bytes.decode("utf-8-sig"))
    if not isinstance(source_file_value, dict) or source_file_value != dict(view):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification",
            "source view path does not contain the supplied view",
        )
    validated = validate_axis_consolidated_view(
        view,
        expected_view_sha256=_required_string(
            view, "view_sha256", boundary="axis_reader_bundle_verification"
        ),
    )
    if validated.get("schema_version") != CONSOLIDATED_VIEW_VERSION:
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification",
            "reader bundles require a point-routed v2 consolidated view",
        )

    point_rows = validated.get("point_index")
    placement_rows = validated.get("point_placements")
    if not isinstance(point_rows, list) or not isinstance(placement_rows, list):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "validated view lacks point placements"
        )
    point_by_id = {
        _required_string(row, "point_id", boundary="axis_reader_bundle_verification"): row
        for row in point_rows
        if isinstance(row, Mapping)
    }
    if len(point_by_id) != len(point_rows):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "point identity is duplicated"
        )
    evidence_by_id = {
        row["evidence_id"]: row for row in validated.get("evidence_index", [])
    }
    origin_by_id = {
        row["origin_group_id"]: row for row in validated.get("origin_index", [])
    }
    quote_by_id = {
        row["quote_span_id"]: row for row in validated.get("quote_spans", [])
    }
    companion_by_ref = {
        row["semantic_unit_ref"]: row
        for row in validated.get("companion_meaning_index", [])
    }

    state_binding_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(validated.get("decision_state_groups"), list):
        placements_by_id = {
            row["placement_id"]: row for row in placement_rows
        }
        bindings = _bindings_from_decision_state_groups(
            _expand_compact_decision_state_groups(validated),
            placements=placements_by_id,
        )
        for point_binding in bindings:
            for row in point_binding["rows"]:
                state_binding_by_key[(point_binding["point_id"], row["selected_id"])] = row

    facts: list[dict[str, Any]] = []
    observed_placements: set[str] = set()
    for placement in sorted(
        placement_rows, key=lambda row: (row["point_id"], row["placement_id"])
    ):
        if not isinstance(placement, Mapping):
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "point placement is invalid"
            )
        point_id = _required_string(
            placement, "point_id", boundary="axis_reader_bundle_verification"
        )
        point = point_by_id.get(point_id)
        if point is None:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "placement point is unresolved"
            )
        placement_id = _required_string(
            placement, "placement_id", boundary="axis_reader_bundle_verification"
        )
        if placement_id in observed_placements:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "placement identity is duplicated"
            )
        observed_placements.add(placement_id)
        evidence_id = _required_string(
            placement, "evidence_id", boundary="axis_reader_bundle_verification"
        )
        origin_group_id = _required_string(
            placement, "origin_group_id", boundary="axis_reader_bundle_verification"
        )
        quote_span_id = _required_string(
            placement, "quote_span_id", boundary="axis_reader_bundle_verification"
        )
        try:
            evidence = evidence_by_id[evidence_id]
            origin = origin_by_id[origin_group_id]
            quote = quote_by_id[quote_span_id]
        except KeyError as exc:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification",
                f"placement literal binding is unresolved: {placement_id}",
            ) from exc
        companion_refs = list(placement["same_evidence_companion_meaning_refs"])
        try:
            companion_meanings = [
                copy.deepcopy(companion_by_ref[ref]) for ref in companion_refs
            ]
        except KeyError as exc:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification",
                f"placement companion meaning is unresolved: {placement_id}",
            ) from exc
        state_binding = state_binding_by_key.get(
            (point_id, _required_string(
                placement, "selected_id", boundary="axis_reader_bundle_verification"
            ))
        )
        relation_refs = (
            state_binding["relation_semantic_unit_refs"]
            if state_binding is not None
            else placement.get(
                "relation_semantic_unit_refs", [placement["semantic_unit_ref"]]
            )
        )
        context = placement["candidate_context"]
        fact: dict[str, Any] = {
            "point_id": point_id,
            "bounded_point": point["bounded_point"],
            "projection_mode": point["projection_mode"],
            "placement_id": placement_id,
            "selected_id": placement["selected_id"],
            "relation": placement["relation"],
            "layer": placement["layer"],
            "reason_code": placement["reason_code"],
            "display_label": placement["display_label"],
            "point_relative_meaning": {
                "semantic_unit_ref": placement["semantic_unit_ref"],
                "statement": placement["normalized_meaning"],
                "relation_semantic_unit_refs": copy.deepcopy(relation_refs),
                "conditions": copy.deepcopy(context["conditions"]),
                "polarity": context["polarity"],
                "axis_ids": copy.deepcopy(context["axis_ids"]),
                "independence_posture": context["independence_posture"],
                "product_version_ids": copy.deepcopy(context["product_version_ids"]),
                "retained_unmerged": context["retained_unmerged"],
                "uncertainty_posture": context["uncertainty_posture"],
            },
            "evidence": {
                "evidence_id": evidence["evidence_id"],
                "origin_group_id": evidence["origin_group_id"],
                "source_venue": evidence["source_venue"],
                "source_role": evidence["source_role"],
                "content_surface": evidence["content_surface"],
                "source_ref": evidence["source_ref"],
                "publication_time": evidence["publication_time"],
                "engagement": copy.deepcopy(evidence["engagement"]),
                "container_ids": copy.deepcopy(evidence["container_ids"]),
            },
            "origin": {
                "origin_group_id": origin["origin_group_id"],
                "independence_key": origin["independence_key"],
                "independence_posture": origin["independence_posture"],
            },
            "quote": {
                "quote_span_id": quote["quote_span_id"],
                "evidence_id": quote["evidence_id"],
                "quote_status": quote["quote_status"],
                "exact_quote": quote["exact_quote"],
                "quote_unavailable_cause": quote["quote_unavailable_cause"],
            },
            "companion_meanings": companion_meanings,
            "parent_contexts": copy.deepcopy(placement.get("parent_contexts", [])),
            "origin_candidate_ids": copy.deepcopy(placement["origin_candidate_ids"]),
        }
        if state_binding is not None:
            fact["decision_state"] = copy.deepcopy(state_binding)
        facts.append(fact)

    if len(facts) != validated["counts"]["placement_count"]:
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "reader fact coverage is incomplete"
        )
    unbound_state_rows = sorted(set(state_binding_by_key) - {
        (fact["point_id"], fact["selected_id"]) for fact in facts
    })
    if unbound_state_rows:
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "decision-state fact is unresolved"
        )

    source_axis_pack = validated.get("source_axis_pack")
    if not isinstance(source_axis_pack, Mapping):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "source axis pack binding is missing"
        )
    axis_pack_path = Path(_required_string(
        source_axis_pack, "path", boundary="axis_reader_bundle_verification"
    ))
    axis_pack = _load_object(axis_pack_path, boundary="axis_reader_bundle_verification")
    rejected_points = validated.get("rejected_point_index")
    if rejected_points is None:
        rejected_points = axis_pack.get("rejected_points")
    if not isinstance(rejected_points, list):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "rejected frontier is unresolved"
        )

    fact_rows_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        fact_rows_by_point[fact["point_id"]].append(fact)
    facts_by_point = {
        point_id: _axis_reader_fact_bytes(fact_rows_by_point[point_id])
        for point_id in sorted(point_by_id)
    }
    manifest_points: list[dict[str, Any]] = []
    for point in point_rows:
        point_id = _required_string(
            point, "point_id", boundary="axis_reader_bundle_verification"
        )
        point_facts = facts_by_point[point_id]
        point_row = copy.deepcopy(point)
        point_row["facts_file"] = {
            "path": str(facts_dir / _axis_reader_point_filename(point_id)),
            "fact_count": len(fact_rows_by_point[point_id]),
            "raw_sha256": hashlib.sha256(point_facts).hexdigest(),
        }
        manifest_points.append(point_row)
    manifest: dict[str, Any] = {
        "schema_version": AXIS_READER_MANIFEST_VERSION,
        "axis_id": validated["axis_id"],
        "source_view": {
            "path": str(source_view_path),
            "raw_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "view_sha256": validated["view_sha256"],
        },
        "source_axis_pack": copy.deepcopy(dict(source_axis_pack)),
        "counts": copy.deepcopy(validated["counts"]),
        "navigation_groups": copy.deepcopy(validated["navigation_groups"]),
        "projection_routes": copy.deepcopy(validated["projection_routes"]),
        "points": manifest_points,
        "rejected_points": sorted(
            copy.deepcopy(rejected_points), key=lambda row: row["point_id"]
        ),
        "facts_directory": {
            "path": str(facts_dir),
            "format": "one complete displayed fact per JSON line",
            "lookup_rule": "read each point facts_file exactly once",
            "fact_count": len(facts),
            "point_file_count": len(facts_by_point),
        },
        "evidence_accounting_contract": copy.deepcopy(
            validated["evidence_accounting_contract"]
        ),
        "non_claims": copy.deepcopy(validated["non_claims"]),
        "reader_rule": (
            "Read each point facts_file exactly once and process every displayed fact. "
            "Display order is navigation, "
            "not importance. bounded_point is the exact point meaning; a fact's statement "
            "explains its relation but never redefines or broadens that point. Each fact "
            "keeps its point-relative meaning, literal evidence, "
            "origin, quote, companion meanings, and any authored decision states together; "
            "do not transfer meaning or metadata across facts. The fact's relation is "
            "authoritative for exactly the semantic refs listed in "
            "point_relative_meaning.relation_semantic_unit_refs; never relabel it from "
            "the quote or give it to any other companion meaning. Never describe a whole "
            "relation bucket from representative examples: either verify every fact in the "
            "bucket or use explicitly non-exhaustive wording such as 'includes'. Keep publication times literal; "
            "do not calculate an elapsed interval unless the source states it. Any exact "
            "relation counts or all-evidence source-surface summary must come from every fact "
            "in that point file. A summary labelled representative may name only the facts "
            "actually displayed as representatives. If a displayed representative has "
            "quote_status quote_available, either reproduce its exact quote or retain "
            "quote_span_id with the point, evidence, and relation so the bound quote stays directly recoverable; "
            "never substitute an unbound excerpt. When a neighboring meaning is authored as "
            "support, describe it as evidence for the exact bounded_point; never rewrite "
            "the admitted point as an OR-list of neighboring meanings. Any output field "
            "for the exact or admitted meaning must copy bounded_point verbatim and contain "
            "nothing else; put evidence explanations and qualifiers in separate fields. "
            "A structured point brief must copy displayed_relation_row_counts and "
            "truth_origin_count into reader_accounting; these are rows and origin groups, "
            "never people, votes, or prevalence."
        ),
    }
    if "decision_state_contract" in validated:
        manifest["decision_state_contract"] = copy.deepcopy(
            validated["decision_state_contract"]
        )
    manifest["reader_manifest_sha256"] = _canonical_json_sha256(manifest)
    return manifest, facts_by_point


def validate_axis_reader_bundle(
    manifest: Mapping[str, Any],
    *,
    facts_dir: Path,
    expected_reader_manifest_sha256: str,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Rebuild a saved reader bundle from its independently hash-pinned source view."""

    if manifest.get("schema_version") != AXIS_READER_MANIFEST_VERSION:
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "unsupported reader manifest version"
        )
    stored = manifest.get("reader_manifest_sha256")
    if stored != expected_reader_manifest_sha256:
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification",
            "trusted reader manifest identity differs from saved manifest",
        )
    payload = {
        key: value for key, value in manifest.items()
        if key != "reader_manifest_sha256"
    }
    if not isinstance(stored, str) or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "stored reader manifest hash is invalid"
        )
    facts_dir = facts_dir.resolve()
    directory_binding = manifest.get("facts_directory")
    point_rows = manifest.get("points")
    if (
        not isinstance(directory_binding, Mapping)
        or directory_binding.get("path") != str(facts_dir)
        or not isinstance(point_rows, list)
    ):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "reader facts directory changed"
        )
    fact_streams: dict[str, bytes] = {}
    total_fact_count = 0
    expected_paths: set[Path] = set()
    for point in point_rows:
        if not isinstance(point, Mapping):
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader point is invalid"
            )
        point_id = _required_string(
            point, "point_id", boundary="axis_reader_bundle_verification"
        )
        facts_binding = point.get("facts_file")
        if not isinstance(facts_binding, Mapping):
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader point facts are missing"
            )
        facts_path = Path(_required_string(
            facts_binding, "path", boundary="axis_reader_bundle_verification"
        )).resolve()
        expected_path = (facts_dir / _axis_reader_point_filename(point_id)).resolve()
        if facts_path != expected_path:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader point facts path changed"
            )
        facts_bytes = facts_path.read_bytes()
        expected_paths.add(facts_path)
        if facts_binding.get("raw_sha256") != hashlib.sha256(facts_bytes).hexdigest():
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader fact bytes changed"
            )
        try:
            parsed_facts = [
                json.loads(line) for line in facts_bytes.decode("utf-8").splitlines()
            ]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader fact stream is invalid"
            ) from exc
        if (
            any(not isinstance(row, dict) for row in parsed_facts)
            or len(parsed_facts) != facts_binding.get("fact_count")
        ):
            raise EvidenceConsumerError(
                "axis_reader_bundle_verification", "reader fact count changed"
            )
        fact_streams[point_id] = facts_bytes
        total_fact_count += len(parsed_facts)
    if (
        total_fact_count != directory_binding.get("fact_count")
        or len(fact_streams) != directory_binding.get("point_file_count")
        or set(facts_dir.glob("*.jsonl")) != expected_paths
    ):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "reader facts directory is incomplete"
        )
    source_view = manifest.get("source_view")
    if not isinstance(source_view, Mapping):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "source view binding is missing"
        )
    source_path = Path(_required_string(
        source_view, "path", boundary="axis_reader_bundle_verification"
    ))
    if hash_file(source_path) != source_view.get("raw_sha256"):
        raise EvidenceConsumerError(
            "axis_reader_bundle_verification", "source view raw bytes changed"
        )
    source = _load_object(source_path, boundary="axis_reader_bundle_verification")
    rebuilt_manifest, rebuilt_fact_streams = build_axis_reader_bundle(
        source, source_view_path=source_path, facts_dir=facts_dir
    )
    if rebuilt_manifest != dict(manifest) or rebuilt_fact_streams != fact_streams:
        raise EvidenceConsumerError(
            "axis_reader_bundle_reprojection",
            "saved reader bundle differs from the validated source view",
        )
    return rebuilt_manifest, rebuilt_fact_streams


def validate_axis_reader_structured_output(
    manifest: Mapping[str, Any],
    *,
    facts_dir: Path,
    expected_reader_manifest_sha256: str,
    output: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail loud when a structured cold-reader brief misbinds reader facts."""

    validated, fact_streams = validate_axis_reader_bundle(
        manifest,
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=expected_reader_manifest_sha256,
    )
    point_contract = {
        point["point_id"]: (point["bounded_point"], point["projection_mode"])
        for point in validated["points"]
    }
    accounting_contract = {
        point["point_id"]: {
            "displayed_relation_row_counts": point["displayed_relation_row_counts"],
            "truth_origin_count": point["truth_origin_count"],
        }
        for point in validated["points"]
    }
    facts_by_point = {
        point_id: [
            json.loads(line)
            for line in fact_bytes.decode("utf-8").splitlines()
        ]
        for point_id, fact_bytes in fact_streams.items()
    }

    def validated_point_rows(field: str, route_field: str) -> list[Mapping[str, Any]]:
        rows = output.get(field)
        if not isinstance(rows, list) or any(
            not isinstance(row, Mapping) for row in rows
        ):
            raise EvidenceConsumerError(
                "axis_reader_output_verification",
                f"structured output {field} is missing or invalid",
            )
        observed_ids = [row.get("point_id") for row in rows]
        if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != set(
            point_contract
        ):
            raise EvidenceConsumerError(
                "axis_reader_output_verification",
                f"structured output {field} does not account every accepted point once",
            )
        for row in rows:
            point_id = row["point_id"]
            bounded_point, projection_mode = point_contract[point_id]
            if (
                row.get("bounded_point") != bounded_point
                or row.get(route_field) != projection_mode
            ):
                raise EvidenceConsumerError(
                    "axis_reader_output_verification",
                    "structured output changed a point identity, meaning, or route",
                )
        return rows

    validated_point_rows("point_accounting", "route")
    accepted_rows = validated_point_rows("accepted_points", "projection_route")
    representative_count = 0
    for point_row in accepted_rows:
        point_id = point_row["point_id"]
        bounded_point = point_contract[point_id][0]
        if point_row.get("exact_phase_a_meaning") != bounded_point:
            raise EvidenceConsumerError(
                "axis_reader_output_verification",
                "structured output changed the exact admitted meaning",
            )
        if point_row.get("reader_accounting") != accounting_contract[point_id]:
            raise EvidenceConsumerError(
                "axis_reader_output_verification",
                "structured output changed or omitted exact reader accounting",
            )
        representatives = point_row.get("representative_evidence")
        if not isinstance(representatives, list) or any(
            not isinstance(row, Mapping) for row in representatives
        ):
            raise EvidenceConsumerError(
                "axis_reader_output_verification",
                "structured output representatives are missing or invalid",
            )
        for representative in representatives:
            representative_count += 1
            evidence_id = representative.get("evidence_id")
            relation = representative.get("relation")
            quote_status = representative.get("quote_status")
            exact_quote = representative.get("exact_quote")
            if exact_quote is not None and not isinstance(exact_quote, str):
                raise EvidenceConsumerError(
                    "axis_reader_output_verification",
                    "structured output representative quote is not literal text",
                )
            quote_span_id = representative.get("quote_span_id")
            has_bound_handle = isinstance(quote_span_id, str)
            matching_facts = [
                fact
                for fact in facts_by_point[point_id]
                if fact["evidence"]["evidence_id"] == evidence_id
                and fact["relation"] == relation
                and fact["quote"]["quote_status"] == quote_status
                and (
                    (
                        has_bound_handle
                        and fact["quote"]["quote_span_id"] == quote_span_id
                        and exact_quote in {None, fact["quote"]["exact_quote"]}
                    )
                    or (
                        not has_bound_handle
                        and fact["quote"]["exact_quote"] == exact_quote
                    )
                )
            ]
            if not matching_facts or (
                quote_status == "quote_available"
                and not has_bound_handle
                and (not isinstance(exact_quote, str) or not exact_quote)
            ):
                raise EvidenceConsumerError(
                    "axis_reader_output_verification",
                    "structured output cited a cross-point, wrong-relation, or missing quote",
                )
    return {
        "status": "valid",
        "point_count": len(point_contract),
        "representative_count": representative_count,
        "reader_manifest_sha256": validated["reader_manifest_sha256"],
    }


def _json_schema_type_admits(declared: Any, value: Any) -> bool:
    """Report whether a declared JSON Schema type can carry this bound constant.

    A constant pinned onto an incompatible declared type produces a schema no
    output can satisfy, so the mismatch must fail here rather than surface as an
    unexplained decoding failure.
    """

    for name in declared if isinstance(declared, list) else [declared]:
        if name == "boolean":
            if isinstance(value, bool):
                return True
        elif name in {"integer", "number"}:
            if isinstance(value, bool):
                continue
            if isinstance(value, int) or (name == "number" and isinstance(value, float)):
                return True
        elif name == "string":
            if isinstance(value, str):
                return True
        elif name == "null":
            if value is None:
                return True
        elif name == "array":
            if isinstance(value, list):
                return True
        elif name == "object":
            if isinstance(value, Mapping):
                return True
    return False


def bind_axis_reader_output_schema(
    manifest: Mapping[str, Any], base_schema: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind structured brief point identities and counts for constrained decoding."""

    if manifest.get("schema_version") != AXIS_READER_MANIFEST_VERSION:
        raise EvidenceConsumerError(
            "axis_reader_output_schema_binding", "unsupported reader manifest version"
        )
    properties = base_schema.get("properties")
    if not isinstance(properties, Mapping):
        raise EvidenceConsumerError(
            "axis_reader_output_schema_binding", "base schema properties are missing"
        )
    schema = copy.deepcopy(dict(base_schema))
    bound_properties = schema["properties"]
    point_rows = manifest.get("points")
    if not isinstance(point_rows, list) or not point_rows:
        raise EvidenceConsumerError(
            "axis_reader_output_schema_binding", "reader points are missing"
        )

    def bind_items(field: str, constants: Sequence[Mapping[str, Any]]) -> None:
        def bind_value(property_schema: dict[str, Any], value: Any) -> dict[str, Any]:
            bound = copy.deepcopy(property_schema)
            if "type" in bound and not _json_schema_type_admits(bound["type"], value):
                raise EvidenceConsumerError(
                    "axis_reader_output_schema_binding",
                    f"base schema {field} type cannot carry its bound value",
                )
            if isinstance(value, Mapping):
                child_properties = bound.get("properties")
                if not isinstance(child_properties, dict):
                    raise EvidenceConsumerError(
                        "axis_reader_output_schema_binding",
                        f"base schema {field} object properties are missing",
                    )
                for child_key, child_value in value.items():
                    child_schema = child_properties.get(child_key)
                    if not isinstance(child_schema, dict):
                        raise EvidenceConsumerError(
                            "axis_reader_output_schema_binding",
                            f"base schema {field} lacks {child_key}",
                        )
                    child_properties[child_key] = bind_value(child_schema, child_value)
                return bound
            if "type" not in bound:
                raise EvidenceConsumerError(
                    "axis_reader_output_schema_binding",
                    f"base schema {field} scalar lacks a type",
                )
            bound["const"] = copy.deepcopy(value)
            return bound

        array_schema = bound_properties.get(field)
        if not isinstance(array_schema, dict) or not isinstance(
            array_schema.get("items"), Mapping
        ):
            raise EvidenceConsumerError(
                "axis_reader_output_schema_binding",
                f"base schema {field} item contract is missing",
            )
        template = array_schema["items"]
        variants = []
        for row_constants in constants:
            variant = copy.deepcopy(dict(template))
            item_properties = variant.get("properties")
            if not isinstance(item_properties, dict):
                raise EvidenceConsumerError(
                    "axis_reader_output_schema_binding",
                    f"base schema {field} properties are missing",
                )
            for key, value in row_constants.items():
                if key not in item_properties:
                    raise EvidenceConsumerError(
                        "axis_reader_output_schema_binding",
                        f"base schema {field} lacks {key}",
                    )
                property_schema = item_properties[key]
                if not isinstance(property_schema, dict) or "type" not in property_schema:
                    raise EvidenceConsumerError(
                        "axis_reader_output_schema_binding",
                        f"base schema {field}.{key} lacks a type",
                    )
                item_properties[key] = bind_value(property_schema, value)
            variants.append(variant)
        array_schema["minItems"] = len(constants)
        array_schema["maxItems"] = len(constants)
        array_schema["items"] = {"anyOf": variants}

    bind_items(
        "point_accounting",
        [
            {
                "point_id": point["point_id"],
                "bounded_point": point["bounded_point"],
                "route": point["projection_mode"],
            }
            for point in point_rows
        ],
    )
    bind_items(
        "accepted_points",
        [
            {
                "point_id": point["point_id"],
                "bounded_point": point["bounded_point"],
                "projection_route": point["projection_mode"],
                "exact_phase_a_meaning": point["bounded_point"],
                "reader_accounting": {
                    "displayed_relation_row_counts": point[
                        "displayed_relation_row_counts"
                    ],
                    "truth_origin_count": point["truth_origin_count"],
                },
            }
            for point in point_rows
        ],
    )
    return schema


POINT_READER_POLICY = {
    "semantic_unit": "one complete accepted Phase A point",
    "model_scope": "interpretation plus point-local evidence handles only",
    "deterministic_fields": (
        "subject, point, route, accounting, literal representatives, and the complete "
        "Decision State ledger are compiler-owned"
    ),
    "coverage": "every accepted point exactly once; no duplicate or foreign point",
    "rejected_frontier": (
        "each rejected point receives a deterministic receipt bound to the validated "
        "axis pack; no model call is spent on rejection bookkeeping"
    ),
    "non_claims": [
        "no Deliver recommendation",
        "no prevalence or causal claim",
        "no Data Lake persistence or global index",
        "no axis-level semantic condensation",
    ],
}


def _point_reader_subject_identity(value: Mapping[str, Any]) -> dict[str, str]:
    expected = {
        "schema_version",
        "company_id",
        "product_id",
        "cutoff",
    }
    if set(value) != expected or value.get("schema_version") != (
        POINT_READER_SUBJECT_IDENTITY_VERSION
    ):
        raise EvidenceConsumerError(
            "point_reader_subject_identity", "subject identity fields are invalid"
        )
    return {
        key: _required_string(value, key, boundary="point_reader_subject_identity")
        for key in ("schema_version", "company_id", "product_id", "cutoff")
    }


def _point_reader_state_ledger(facts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    for fact in facts:
        raw_state = fact.get("decision_state")
        if raw_state is None:
            continue
        if not isinstance(raw_state, Mapping):
            raise EvidenceConsumerError(
                "point_reader_decision_state", "decision-state fact is invalid"
            )
        state = copy.deepcopy(dict(raw_state))
        assertions = state.get("state_assertions")
        if not isinstance(assertions, list):
            raise EvidenceConsumerError(
                "point_reader_decision_state", "decision-state assertions are invalid"
            )
        normalized_assertions: list[dict[str, Any]] = []
        for assertion in assertions:
            if not isinstance(assertion, Mapping):
                raise EvidenceConsumerError(
                    "point_reader_decision_state", "decision-state assertion is invalid"
                )
            normalized = copy.deepcopy(dict(assertion))
            state_kind = _required_string(
                normalized, "state_kind", boundary="point_reader_decision_state"
            )
            stage = DECISION_STATE_CONSUMER_CONTRACT["state_kind_stages"].get(
                state_kind
            )
            if stage is None:
                raise EvidenceConsumerError(
                    "point_reader_decision_state", "decision-state kind is unsupported"
                )
            if normalized.get("stage") not in (None, stage):
                raise EvidenceConsumerError(
                    "point_reader_decision_state", "decision-state stage changed"
                )
            normalized["stage"] = stage
            normalized_assertions.append(normalized)
        state["state_assertions"] = normalized_assertions
        row_payload = {
            "point_id": fact["point_id"],
            "placement_id": fact["placement_id"],
            "selected_id": fact["selected_id"],
            "evidence_id": fact["evidence"]["evidence_id"],
            "relation": fact["relation"],
            "decision_state": state,
        }
        state_selected_id = state.pop("selected_id", fact["selected_id"])
        if state_selected_id != fact["selected_id"]:
            raise EvidenceConsumerError(
                "point_reader_decision_state",
                "decision-state selected identity changed",
            )
        ledger.append(
            {
                **state,
                "state_row_id": "state_row_"
                + _canonical_json_sha256(row_payload),
                "placement_id": fact["placement_id"],
                "selected_id": fact["selected_id"],
                "evidence_id": fact["evidence"]["evidence_id"],
                "relation": fact["relation"],
            }
        )
    return ledger


def point_reader_input_sha256(input_contract: Mapping[str, Any]) -> str:
    """Hash every semantic dependency that must invalidate reusable point work."""

    forbidden = {"path", "absolute_path", "mtime", "point_input_sha256"}
    if forbidden & set(input_contract):
        raise EvidenceConsumerError(
            "point_reader_identity", "point identity contains a storage-local field"
        )
    return _canonical_json_sha256(dict(input_contract))


def _point_reader_rejected_receipts(
    rejected: Sequence[Mapping[str, Any]], *, axis_pack_sha256: str
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for row in sorted(rejected, key=lambda value: value["point_id"]):
        receipt = {
            "schema_version": "phase_a_point_reader_rejected_receipt_v1",
            "point_id": _required_string(
                row, "point_id", boundary="point_reader_rejected_frontier"
            ),
            "bounded_point": _required_string(
                row, "bounded_point", boundary="point_reader_rejected_frontier"
            ),
            "disposition": _required_string(
                row, "disposition", boundary="point_reader_rejected_frontier"
            ),
            "reason": _required_string(
                row, "reason", boundary="point_reader_rejected_frontier"
            ),
            "source_axis_pack_sha256": axis_pack_sha256,
            "resolution_kind": "validated_axis_frontier_disposition",
        }
        if "resolution_receipt_sha256" in row:
            receipt["source_resolution_receipt_sha256"] = _required_string(
                row,
                "resolution_receipt_sha256",
                boundary="point_reader_rejected_frontier",
            )
        receipt["receipt_sha256"] = _canonical_json_sha256(receipt)
        receipts.append(receipt)
    return receipts


def build_axis_point_reader_snapshot(
    view: Mapping[str, Any],
    *,
    source_view_path: Path,
    subject_identity: Mapping[str, Any],
    method_text: str = POINT_READER_METHOD_TEXT,
    response_schema: Mapping[str, Any] = POINT_READER_RESPONSE_SCHEMA,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Create a path-independent point work snapshot over one validated axis."""

    subject = _point_reader_subject_identity(subject_identity)
    if not isinstance(method_text, str) or not method_text.strip():
        raise EvidenceConsumerError(
            "point_reader_method", "point-reader method text is empty"
        )
    if not isinstance(response_schema, Mapping):
        raise EvidenceConsumerError(
            "point_reader_method", "point-reader response schema is invalid"
        )
    source_view_path = source_view_path.resolve()
    legacy_manifest, point_payloads = build_axis_reader_bundle(
        view,
        source_view_path=source_view_path,
        facts_dir=source_view_path.parent / ".point-reader-runtime",
    )
    source_axis_pack = legacy_manifest["source_axis_pack"]
    axis_pack = _load_object(
        Path(source_axis_pack["path"]), boundary="point_reader_snapshot"
    )
    axis_pack_sha256 = _required_string(
        axis_pack, "axis_pack_sha256", boundary="point_reader_snapshot"
    )
    validate_phase_a_evidence_axis_pack(
        axis_pack, expected_axis_pack_sha256=axis_pack_sha256
    )
    lineage_by_point = {row["point_id"]: row for row in axis_pack["points"]}
    subject_sha256 = _canonical_json_sha256(subject)
    method_sha256 = hashlib.sha256(method_text.encode("utf-8")).hexdigest()
    response_schema_value = copy.deepcopy(dict(response_schema))
    response_schema_sha256 = _canonical_json_sha256(response_schema_value)
    policy_sha256 = _canonical_json_sha256(POINT_READER_POLICY)

    point_records: list[dict[str, Any]] = []
    for legacy_point in sorted(legacy_manifest["points"], key=lambda row: row["point_id"]):
        point_id = legacy_point["point_id"]
        payload = point_payloads[point_id]
        facts = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
        ledger = _point_reader_state_ledger(facts)
        lineage = lineage_by_point.get(point_id)
        if not isinstance(lineage, Mapping):
            raise EvidenceConsumerError(
                "point_reader_identity", "point lineage is unresolved"
            )
        input_contract = {
            "subject_identity_sha256": subject_sha256,
            "axis_id": legacy_manifest["axis_id"],
            "point_id": point_id,
            "bounded_point": legacy_point["bounded_point"],
            "projection_mode": legacy_point["projection_mode"],
            "point_payload_raw_sha256": hashlib.sha256(payload).hexdigest(),
            "decision_state_ledger_sha256": _canonical_json_sha256(ledger),
            "source_lineage": {
                key: copy.deepcopy(lineage[key])
                for key in (
                    "artifact_sha256",
                    "selection_manifest_file_sha256",
                    "selection_manifest_sha256",
                    "quote_manifest_file_sha256",
                    "quote_manifest_sha256",
                    "policy_revision",
                    "policy_lineage",
                )
            },
            "method_text_sha256": method_sha256,
            "response_schema_sha256": response_schema_sha256,
            "point_reader_policy_sha256": policy_sha256,
            "point_brief_schema_version": POINT_READER_BRIEF_VERSION,
        }
        point_input = point_reader_input_sha256(input_contract)
        point_records.append(
            {
                "point_id": point_id,
                "bounded_point": legacy_point["bounded_point"],
                "projection_mode": legacy_point["projection_mode"],
                "displayed_relation_row_counts": copy.deepcopy(
                    legacy_point["displayed_relation_row_counts"]
                ),
                "truth_origin_count": legacy_point["truth_origin_count"],
                "fact_count": len(facts),
                "point_payload_file": f"point_{point_input}.jsonl",
                "response_file": f"response_{point_input}.json",
                "brief_file": f"brief_{point_input}.json",
                "input_contract": input_contract,
                "point_input_sha256": point_input,
            }
        )

    rejected_receipts = _point_reader_rejected_receipts(
        legacy_manifest["rejected_points"], axis_pack_sha256=axis_pack_sha256
    )
    source_bytes = source_view_path.read_bytes()
    manifest: dict[str, Any] = {
        "schema_version": POINT_READER_RUN_MANIFEST_VERSION,
        "subject_identity": subject,
        "subject_identity_sha256": subject_sha256,
        "axis_id": legacy_manifest["axis_id"],
        "source_binding": {
            "source_view_raw_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "source_view_sha256": view["view_sha256"],
            "source_axis_pack_sha256": axis_pack_sha256,
        },
        "method_binding": {
            "method_text": method_text,
            "method_text_sha256": method_sha256,
            "response_schema": response_schema_value,
            "response_schema_sha256": response_schema_sha256,
            "point_reader_policy": copy.deepcopy(POINT_READER_POLICY),
            "point_reader_policy_sha256": policy_sha256,
        },
        "points": point_records,
        "rejected_point_receipts": rejected_receipts,
        "counts": {
            "accepted_point_count": len(point_records),
            "rejected_point_count": len(rejected_receipts),
            "frontier_point_count": len(point_records) + len(rejected_receipts),
        },
        "storage_contract": {
            "point_store_root": "runtime_supplied",
            "lookup_rule": "join point_payload_file inside the supplied point store",
            "portable_identity_excludes": ["absolute paths", "mtimes", "labels alone"],
        },
    }
    manifest["snapshot_sha256"] = _canonical_json_sha256(manifest)
    return manifest, point_payloads


def _validate_point_reader_manifest_shape(
    manifest: Mapping[str, Any], *, expected_snapshot_sha256: str
) -> dict[str, Any]:
    if manifest.get("schema_version") != POINT_READER_RUN_MANIFEST_VERSION:
        raise EvidenceConsumerError(
            "point_reader_snapshot", "unsupported point-reader snapshot"
        )
    stored = manifest.get("snapshot_sha256")
    if stored != expected_snapshot_sha256:
        raise EvidenceConsumerError(
            "point_reader_snapshot", "trusted snapshot identity changed"
        )
    if not isinstance(stored, str) or stored != _canonical_json_sha256(
        {key: value for key, value in manifest.items() if key != "snapshot_sha256"}
    ):
        raise EvidenceConsumerError(
            "point_reader_snapshot", "stored snapshot identity is invalid"
        )
    subject = _point_reader_subject_identity(manifest.get("subject_identity", {}))
    if manifest.get("subject_identity_sha256") != _canonical_json_sha256(subject):
        raise EvidenceConsumerError(
            "point_reader_subject_identity", "subject identity binding changed"
        )
    method = manifest.get("method_binding")
    if not isinstance(method, Mapping):
        raise EvidenceConsumerError("point_reader_method", "method binding is missing")
    method_text = method.get("method_text")
    response_schema = method.get("response_schema")
    policy = method.get("point_reader_policy")
    if (
        not isinstance(method_text, str)
        or method.get("method_text_sha256")
        != hashlib.sha256(method_text.encode("utf-8")).hexdigest()
        or not isinstance(response_schema, Mapping)
        or method.get("response_schema_sha256")
        != _canonical_json_sha256(dict(response_schema))
        or not isinstance(policy, Mapping)
        or method.get("point_reader_policy_sha256")
        != _canonical_json_sha256(dict(policy))
    ):
        raise EvidenceConsumerError(
            "point_reader_method", "method content binding changed"
        )
    points = manifest.get("points")
    if not isinstance(points, list) or not points:
        raise EvidenceConsumerError("point_reader_snapshot", "snapshot points are missing")
    point_ids = [row.get("point_id") for row in points if isinstance(row, Mapping)]
    if (
        len(point_ids) != len(points)
        or any(not isinstance(point_id, str) for point_id in point_ids)
        or len(set(point_ids)) != len(point_ids)
    ):
        raise EvidenceConsumerError(
            "point_reader_snapshot", "snapshot point identities are invalid"
        )
    for point in points:
        contract = point.get("input_contract")
        if not isinstance(contract, Mapping) or point.get(
            "point_input_sha256"
        ) != point_reader_input_sha256(contract):
            raise EvidenceConsumerError(
                "point_reader_identity", "point input identity changed"
            )
        expected_file = f"point_{point['point_input_sha256']}.jsonl"
        expected_response = f"response_{point['point_input_sha256']}.json"
        expected_brief = f"brief_{point['point_input_sha256']}.json"
        if (
            point.get("point_payload_file") != expected_file
            or point.get("response_file") != expected_response
            or point.get("brief_file") != expected_brief
        ):
            raise EvidenceConsumerError(
                "point_reader_identity", "point payload lookup changed"
            )
    counts = manifest.get("counts")
    receipts = manifest.get("rejected_point_receipts")
    if not isinstance(counts, Mapping) or not isinstance(receipts, list):
        raise EvidenceConsumerError(
            "point_reader_snapshot", "snapshot frontier accounting is invalid"
        )
    if (
        counts.get("accepted_point_count") != len(points)
        or counts.get("rejected_point_count") != len(receipts)
        or counts.get("frontier_point_count") != len(points) + len(receipts)
    ):
        raise EvidenceConsumerError(
            "point_reader_snapshot", "snapshot frontier accounting changed"
        )
    for receipt in receipts:
        if not isinstance(receipt, Mapping) or receipt.get(
            "receipt_sha256"
        ) != _canonical_json_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        ):
            raise EvidenceConsumerError(
                "point_reader_rejected_frontier", "rejected receipt changed"
            )
    rejected_ids = [receipt.get("point_id") for receipt in receipts]
    source_binding = manifest.get("source_binding")
    if (
        any(not isinstance(point_id, str) for point_id in rejected_ids)
        or len(rejected_ids) != len(set(rejected_ids))
        or set(point_ids) & set(rejected_ids)
        or not isinstance(source_binding, Mapping)
        or any(
            receipt.get("source_axis_pack_sha256")
            != source_binding.get("source_axis_pack_sha256")
            for receipt in receipts
        )
    ):
        raise EvidenceConsumerError(
            "point_reader_rejected_frontier",
            "accepted and rejected frontier membership changed",
        )
    return copy.deepcopy(dict(manifest))


def validate_axis_point_reader_snapshot(
    manifest: Mapping[str, Any],
    *,
    point_store_dir: Path,
    expected_snapshot_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    validated = _validate_point_reader_manifest_shape(
        manifest,
        expected_snapshot_sha256=(
            expected_snapshot_sha256
            if expected_snapshot_sha256 is not None
            else str(manifest.get("snapshot_sha256"))
        ),
    )
    payloads: dict[str, bytes] = {}
    for point in validated["points"]:
        path = point_store_dir / point["point_payload_file"]
        if not path.is_file():
            raise EvidenceConsumerError(
                "point_reader_store", f"point payload is missing: {point['point_id']}"
            )
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != point["input_contract"][
            "point_payload_raw_sha256"
        ]:
            raise EvidenceConsumerError(
                "point_reader_store", f"point payload changed: {point['point_id']}"
            )
        facts = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
        if len(facts) != point["fact_count"] or any(
            fact.get("point_id") != point["point_id"] for fact in facts
        ):
            raise EvidenceConsumerError(
                "point_reader_store", f"point payload coverage changed: {point['point_id']}"
            )
        if _canonical_json_sha256(_point_reader_state_ledger(facts)) != point[
            "input_contract"
        ]["decision_state_ledger_sha256"]:
            raise EvidenceConsumerError(
                "point_reader_decision_state",
                f"point state ledger changed: {point['point_id']}",
            )
        payloads[point["point_id"]] = payload
    return validated, payloads


def bind_point_reader_response_schema(
    manifest: Mapping[str, Any], point_id: str
) -> dict[str, Any]:
    validated = _validate_point_reader_manifest_shape(
        manifest, expected_snapshot_sha256=str(manifest.get("snapshot_sha256"))
    )
    point = next(
        (row for row in validated["points"] if row["point_id"] == point_id), None
    )
    if point is None:
        raise EvidenceConsumerError(
            "point_reader_response_schema", "response point is not in the snapshot"
        )
    schema = copy.deepcopy(validated["method_binding"]["response_schema"])
    properties = schema.get("properties")
    if (
        not isinstance(properties, dict)
        or not isinstance(properties.get("point_id"), dict)
        or not isinstance(properties.get("point_input_sha256"), dict)
    ):
        raise EvidenceConsumerError(
            "point_reader_response_schema", "response schema identity fields are missing"
        )
    properties["point_id"]["const"] = point_id
    properties["point_input_sha256"]["const"] = point["point_input_sha256"]
    return schema


def _point_reader_facts(
    manifest: Mapping[str, Any], point_store_dir: Path, point_id: str
) -> tuple[Mapping[str, Any], list[dict[str, Any]]]:
    validated, payloads = validate_axis_point_reader_snapshot(
        manifest, point_store_dir=point_store_dir
    )
    point = next(
        (row for row in validated["points"] if row["point_id"] == point_id), None
    )
    if point is None:
        raise EvidenceConsumerError(
            "point_reader_response", "response point is not in the snapshot"
        )
    return point, [
        json.loads(line) for line in payloads[point_id].decode("utf-8").splitlines()
    ]


def _compile_point_reader_brief_from_validated_facts(
    manifest: Mapping[str, Any],
    *,
    point: Mapping[str, Any],
    facts: Sequence[Mapping[str, Any]],
    response: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile after the caller has validated the snapshot and this point payload."""

    point_id = point["point_id"]
    if set(response) != {
        "point_input_sha256",
        "point_id",
        "interpretation",
        "representative_handles",
    }:
        raise EvidenceConsumerError(
            "point_reader_response", "point response fields are invalid"
        )
    if (
        response.get("point_id") != point_id
        or response.get("point_input_sha256") != point["point_input_sha256"]
    ):
        raise EvidenceConsumerError(
            "point_reader_response", "point response identity changed"
        )
    interpretation = response.get("interpretation")
    handles = response.get("representative_handles")
    if not isinstance(interpretation, str) or not interpretation.strip():
        raise EvidenceConsumerError(
            "point_reader_response", "point interpretation is missing"
        )
    if not isinstance(handles, list) or not handles or any(
        not isinstance(handle, Mapping) for handle in handles
    ):
        raise EvidenceConsumerError(
            "point_reader_response", "representative handles are invalid"
        )
    representatives: list[dict[str, Any]] = []
    observed_handles: set[str] = set()
    for handle in handles:
        if set(handle) != {"placement_id"}:
            raise EvidenceConsumerError(
                "point_reader_response", "representative handle fields are invalid"
            )
        handle_key = handle["placement_id"]
        if not isinstance(handle_key, str):
            raise EvidenceConsumerError(
                "point_reader_response", "representative handle is invalid"
            )
        if handle_key in observed_handles:
            raise EvidenceConsumerError(
                "point_reader_response", "representative handle is duplicated"
            )
        observed_handles.add(handle_key)
        matches = [
            fact
            for fact in facts
            if fact["placement_id"] == handle_key
        ]
        if len(matches) != 1:
            raise EvidenceConsumerError(
                "point_reader_response",
                "representative handle is foreign, ambiguous, or cross-point",
            )
        fact = matches[0]
        representatives.append(
            {
                "placement_id": fact["placement_id"],
                "evidence_id": fact["evidence"]["evidence_id"],
                "relation": fact["relation"],
                "quote_span_id": fact["quote"]["quote_span_id"],
                "quote_status": fact["quote"]["quote_status"],
                "exact_quote": fact["quote"]["exact_quote"],
                "source_ref": fact["evidence"]["source_ref"],
                "source_venue": fact["evidence"]["source_venue"],
                "source_role": fact["evidence"]["source_role"],
                "content_surface": fact["evidence"]["content_surface"],
                "publication_time": fact["evidence"]["publication_time"],
                "engagement": copy.deepcopy(fact["evidence"]["engagement"]),
                "origin_group_id": fact["origin"]["origin_group_id"],
            }
        )
    required_relations = {
        relation
        for relation in ("support", "counter")
        if point["displayed_relation_row_counts"].get(relation, 0) > 0
    }
    represented_relations = {row["relation"] for row in representatives}
    if required_relations - represented_relations:
        raise EvidenceConsumerError(
            "point_reader_response",
            "representative handles omit displayed support or counterevidence",
        )
    ledger = _point_reader_state_ledger(facts)
    brief: dict[str, Any] = {
        "schema_version": POINT_READER_BRIEF_VERSION,
        "point_input_sha256": point["point_input_sha256"],
        "subject_identity": copy.deepcopy(manifest["subject_identity"]),
        "axis_id": manifest["axis_id"],
        "point_id": point_id,
        "bounded_point": point["bounded_point"],
        "projection_mode": point["projection_mode"],
        "reader_accounting": {
            "displayed_relation_row_counts": copy.deepcopy(
                point["displayed_relation_row_counts"]
            ),
            "truth_origin_count": point["truth_origin_count"],
        },
        "model_interpretation": interpretation,
        "representative_evidence": representatives,
        "decision_state_ledger": ledger,
        "decision_state_ledger_sha256": _canonical_json_sha256(ledger),
        "source_point_payload": {
            "file_name": point["point_payload_file"],
            "raw_sha256": point["input_contract"]["point_payload_raw_sha256"],
        },
        "non_claims": copy.deepcopy(POINT_READER_POLICY["non_claims"]),
    }
    brief["brief_sha256"] = _canonical_json_sha256(brief)
    return brief


def compile_point_reader_brief(
    manifest: Mapping[str, Any],
    *,
    point_store_dir: Path,
    point_id: str,
    response: Mapping[str, Any],
) -> dict[str, Any]:
    point, facts = _point_reader_facts(manifest, point_store_dir, point_id)
    return _compile_point_reader_brief_from_validated_facts(
        manifest, point=point, facts=facts, response=response
    )


def _validate_point_reader_brief_from_validated_facts(
    manifest: Mapping[str, Any],
    *,
    point: Mapping[str, Any],
    facts: Sequence[Mapping[str, Any]],
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate after the caller has validated the snapshot and this point payload."""

    if brief.get("schema_version") != POINT_READER_BRIEF_VERSION:
        raise EvidenceConsumerError(
            "point_reader_brief", "unsupported point brief"
        )
    if "snapshot_sha256" in brief:
        raise EvidenceConsumerError(
            "point_reader_brief", "point brief contains an axis-scoped binding"
        )
    point_id = brief.get("point_id")
    if not isinstance(point_id, str):
        raise EvidenceConsumerError("point_reader_brief", "point brief identity is missing")
    if point_id != point.get("point_id"):
        raise EvidenceConsumerError(
            "point_reader_brief", "point brief identity changed"
        )
    expected_ledger = _point_reader_state_ledger(facts)
    observed_ledger = brief.get("decision_state_ledger")
    if (
        not isinstance(observed_ledger, list)
        or brief.get("decision_state_ledger_sha256")
        != _canonical_json_sha256(observed_ledger)
        or observed_ledger != expected_ledger
    ):
        raise EvidenceConsumerError(
            "point_reader_decision_state",
            "compiled brief omitted, altered, or transferred a decision state",
        )
    expected_bindings = {
        "point_input_sha256": point["point_input_sha256"],
        "subject_identity": manifest["subject_identity"],
        "axis_id": manifest["axis_id"],
        "bounded_point": point["bounded_point"],
        "projection_mode": point["projection_mode"],
        "reader_accounting": {
            "displayed_relation_row_counts": point["displayed_relation_row_counts"],
            "truth_origin_count": point["truth_origin_count"],
        },
        "source_point_payload": {
            "file_name": point["point_payload_file"],
            "raw_sha256": point["input_contract"]["point_payload_raw_sha256"],
        },
    }
    if any(brief.get(key) != value for key, value in expected_bindings.items()):
        raise EvidenceConsumerError(
            "point_reader_brief", "compiled point binding changed"
        )
    interpretation = brief.get("model_interpretation")
    representatives = brief.get("representative_evidence")
    if not isinstance(interpretation, str) or not interpretation.strip():
        raise EvidenceConsumerError(
            "point_reader_brief", "compiled interpretation is missing"
        )
    if not isinstance(representatives, list):
        raise EvidenceConsumerError(
            "point_reader_brief", "compiled representatives are invalid"
        )
    fact_keys = {
        fact["placement_id"]: fact
        for fact in facts
    }
    for row in representatives:
        if not isinstance(row, Mapping):
            raise EvidenceConsumerError(
                "point_reader_brief", "compiled representative is invalid"
            )
        fact = fact_keys.get(row.get("placement_id"))
        if fact is None:
            raise EvidenceConsumerError(
                "point_reader_brief", "compiled representative is foreign"
            )
        expected = {
            "placement_id": fact["placement_id"],
            "evidence_id": fact["evidence"]["evidence_id"],
            "relation": fact["relation"],
            "quote_span_id": fact["quote"]["quote_span_id"],
            "quote_status": fact["quote"]["quote_status"],
            "exact_quote": fact["quote"]["exact_quote"],
            "source_ref": fact["evidence"]["source_ref"],
            "source_venue": fact["evidence"]["source_venue"],
            "source_role": fact["evidence"]["source_role"],
            "content_surface": fact["evidence"]["content_surface"],
            "publication_time": fact["evidence"]["publication_time"],
            "engagement": fact["evidence"]["engagement"],
            "origin_group_id": fact["origin"]["origin_group_id"],
        }
        if dict(row) != expected:
            raise EvidenceConsumerError(
                "point_reader_brief", "compiled representative metadata changed"
            )
    if brief.get("brief_sha256") != _canonical_json_sha256(
        {key: value for key, value in brief.items() if key != "brief_sha256"}
    ):
        raise EvidenceConsumerError(
            "point_reader_brief", "compiled brief identity changed"
        )
    return copy.deepcopy(dict(brief))


def validate_point_reader_brief(
    manifest: Mapping[str, Any],
    *,
    point_store_dir: Path,
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    point_id = brief.get("point_id")
    if not isinstance(point_id, str):
        raise EvidenceConsumerError("point_reader_brief", "point brief identity is missing")
    point, facts = _point_reader_facts(manifest, point_store_dir, point_id)
    return _validate_point_reader_brief_from_validated_facts(
        manifest, point=point, facts=facts, brief=brief
    )


def validate_point_reader_completion_membership(
    expected_point_ids: Sequence[str], observed: Sequence[Mapping[str, Any]]
) -> list[str]:
    expected = list(expected_point_ids)
    if len(expected) != len(set(expected)):
        raise EvidenceConsumerError(
            "point_reader_completion", "expected point membership is duplicated"
        )
    observed_ids = [row.get("point_id") for row in observed]
    if (
        len(observed_ids) != len(set(observed_ids))
        or set(observed_ids) != set(expected)
    ):
        raise EvidenceConsumerError(
            "point_reader_completion",
            "completed points are missing, duplicated, or foreign",
        )
    return expected


def assemble_axis_point_reader_output(
    manifest: Mapping[str, Any], *, briefs: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    validated = _validate_point_reader_manifest_shape(
        manifest, expected_snapshot_sha256=str(manifest.get("snapshot_sha256"))
    )
    expected_ids = [row["point_id"] for row in validated["points"]]
    validate_point_reader_completion_membership(expected_ids, briefs)
    by_id = {brief["point_id"]: copy.deepcopy(dict(brief)) for brief in briefs}
    ordered = [by_id[point_id] for point_id in expected_ids]
    for point, brief in zip(validated["points"], ordered, strict=True):
        if (
            brief.get("schema_version") != POINT_READER_BRIEF_VERSION
            or brief.get("point_input_sha256") != point["point_input_sha256"]
            or brief.get("brief_sha256")
            != _canonical_json_sha256(
                {key: value for key, value in brief.items() if key != "brief_sha256"}
            )
            or brief.get("decision_state_ledger_sha256")
            != _canonical_json_sha256(brief.get("decision_state_ledger"))
        ):
            raise EvidenceConsumerError(
                "point_reader_completion", "completed point binding changed"
            )
        if brief.get("decision_state_ledger_sha256") != point["input_contract"][
            "decision_state_ledger_sha256"
        ]:
            raise EvidenceConsumerError(
                "point_reader_decision_state",
                "completed point omitted, altered, or transferred a decision state",
            )
    output: dict[str, Any] = {
        "schema_version": POINT_READER_AXIS_OUTPUT_VERSION,
        "snapshot_sha256": validated["snapshot_sha256"],
        "subject_identity": copy.deepcopy(validated["subject_identity"]),
        "axis_id": validated["axis_id"],
        "accepted_points": ordered,
        "rejected_point_receipts": copy.deepcopy(
            validated["rejected_point_receipts"]
        ),
        "counts": copy.deepcopy(validated["counts"]),
        "non_claims": copy.deepcopy(POINT_READER_POLICY["non_claims"]),
    }
    output["axis_output_sha256"] = _canonical_json_sha256(output)
    return output


def validate_axis_point_reader_output(
    manifest: Mapping[str, Any],
    *,
    output: Mapping[str, Any],
    point_store_dir: Path,
) -> dict[str, Any]:
    validated, payloads = validate_axis_point_reader_snapshot(
        manifest, point_store_dir=point_store_dir
    )
    return _validate_axis_point_reader_output_from_validated_snapshot(
        validated, payloads=payloads, output=output
    )


def _validate_axis_point_reader_output_from_validated_snapshot(
    manifest: Mapping[str, Any],
    *,
    payloads: Mapping[str, bytes],
    output: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an axis output without re-reading an already validated point store."""

    if output.get("schema_version") != POINT_READER_AXIS_OUTPUT_VERSION:
        raise EvidenceConsumerError(
            "point_reader_completion", "unsupported point-reader axis output"
        )
    if output.get("axis_output_sha256") != _canonical_json_sha256(
        {key: value for key, value in output.items() if key != "axis_output_sha256"}
    ):
        raise EvidenceConsumerError(
            "point_reader_completion", "axis output identity changed"
        )
    rebuilt = assemble_axis_point_reader_output(
        manifest, briefs=output.get("accepted_points", [])
    )
    points_by_id = {point["point_id"]: point for point in manifest["points"]}
    for brief in rebuilt["accepted_points"]:
        point = points_by_id[brief["point_id"]]
        facts = [
            json.loads(line)
            for line in payloads[point["point_id"]].decode("utf-8").splitlines()
        ]
        _validate_point_reader_brief_from_validated_facts(
            manifest, point=point, facts=facts, brief=brief
        )
    if rebuilt != dict(output):
        raise EvidenceConsumerError(
            "point_reader_completion", "axis output differs from its snapshot"
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
