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
from judgment.phase_a_evidence_selection import _verify_bundle, load_selection_sources


AXIS_PACK_MANIFEST_VERSION = "phase_a_evidence_axis_pack_manifest_v1"
AXIS_PACK_VERSION = "phase_a_evidence_axis_pack_v1"
LEGACY_CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v1"
CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v2"
LEGACY_CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v1"
CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v2"
SOURCE_AXIS_PACK_VERSION = AXIS_PACK_VERSION
LEGACY_HYDRATION_AXIS_PACK_VERSION = "phase_a_hydration_axis_pack_v2"
LEGACY_CONSOLIDATION_POLICY = "origin_normalized_surface_separated_v1"
CONSOLIDATION_POLICY = "point_routed_origin_normalized_surface_separated_v2"
POINT_TRUTH_ORIGIN_CAP = 13
SUPPORTED_QUOTE_MANIFEST_VERSIONS = {
    "phase_a_evidence_quote_manifest_v6",
    "phase_a_evidence_quote_manifest_v7",
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
DIRECT_OUTCOME_BOUNDARIES = (
    "not a causal judgment",
    "not a commercial-pull score",
    "creator influence is not customer corroboration",
)
DECISION_STATE_BOUNDARIES = (
    "decision states are actor-, object-, and stage-specific, not prevalence or market estimates",
    "intent is not observed behavior",
    "multi-unit purchase or ownership is not observed repurchase",
    "price concern is not automatically an unfavorable value judgment",
    "companion decision states coexist and are not averaged into sentiment",
)
DECISION_STATE_CONSUMER_CONTRACT = {
    "state_tuple_authority": (
        "explicit spec-authored state kind, direction, object, semantic refs, and qualifiers "
        "for a completed point semantic unit"
    ),
    "unasserted_state_rule": (
        "state_rows are exhaustive for delivered decision states; literal quotes and "
        "qualifications may explain asserted states but may not create an additional "
        "purchase, ownership, intent, recurrence, or other decision state"
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
        "literal source span; it need not restate parent prompt or source context already "
        "bound by the completed semantic unit"
    ),
    "companion_rule": (
        "state assertions may overlap semantic-unit refs when one literal source carries "
        "several non-equivalent states"
    ),
    "qualification_rule": (
        "resolve every qualification_ref through companion_meaning_index and preserve it "
        "when material; it remains context rather than an additional decision state"
    ),
    "consumer_join_order": [
        "decision_state_group placement_id to point_placements",
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
DECISION_STATE_CONTRACT = {
    "value_judgment": {"stages": {"judgment"}, "directions": {"favorable", "unfavorable", "mixed"}},
    "price_concern": {"stages": {"judgment"}, "directions": {"friction"}},
    "buyers_remorse": {"stages": {"judgment"}, "directions": {"unfavorable"}},
    "preference_judgment": {
        "stages": {"judgment"},
        "directions": {"favorable", "unfavorable", "mixed"},
    },
    "purchase_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "repurchase_intent": {"stages": {"intent"}, "directions": {"toward_action"}},
    "return_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "switching_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "abandonment_intent": {"stages": {"intent"}, "directions": {"away_from_action"}},
    "purchase": {"stages": {"observed"}, "directions": {"neutral"}},
    "observed_repurchase": {"stages": {"observed"}, "directions": {"toward_action"}},
    "multi_unit_purchase": {"stages": {"observed"}, "directions": {"toward_action"}},
    "ownership": {"stages": {"observed"}, "directions": {"neutral"}},
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
    if not isinstance(accepted, list) or not accepted:
        raise EvidenceConsumerError("axis_manifest", "accepted_points must be nonempty")
    if not isinstance(rejected, list):
        raise EvidenceConsumerError("axis_manifest", "rejected_points must be explicit")

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
    for row in rejected:
        if not isinstance(row, Mapping):
            raise EvidenceConsumerError("axis_manifest", "rejected point must be an object")
        if set(row) != {"point_id", "bounded_point", "disposition", "reason"}:
            raise EvidenceConsumerError("axis_manifest", "rejected point fields are invalid")
        point_id = _required_string(row, "point_id", boundary="axis_manifest")
        rejected_ids.append(point_id)
        rejected_rows.append(
            {
                "point_id": point_id,
                "bounded_point": _required_string(row, "bounded_point", boundary="axis_manifest"),
                "disposition": _required_string(row, "disposition", boundary="axis_manifest"),
                "reason": _required_string(row, "reason", boundary="axis_manifest"),
            }
        )
    if len(set(rejected_ids)) != len(rejected_ids):
        raise EvidenceConsumerError("axis_manifest", "rejected point identities are invalid")
    overlap = set(accepted_ids) & set(rejected_ids)
    if overlap:
        raise EvidenceConsumerError(
            "axis_manifest", f"accepted/rejected point overlap: {sorted(overlap)}"
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
        "status": "complete_valid_axis_pack",
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
        or not points
        or not isinstance(rejected, list)
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
            if not isinstance(raw_row, Mapping) or set(raw_row) != {
                "selected_id",
                "state_assertions",
                "context_only_semantic_unit_refs",
            }:
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
            rows[selected_id] = raw_row
        normalized[point_id] = rows

    if set(normalized) != decision_point_ids:
        missing = sorted(decision_point_ids - set(normalized))
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"decision-state bindings do not cover every routed point: {missing}",
        )
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

    raw_assertions = binding.get("state_assertions")
    if not isinstance(raw_assertions, list) or not raw_assertions:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"row binding has no state assertions: {point_id}::{selected_id}",
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
        assertion_id = (
            "decision_state_"
            + _canonical_json_sha256([point_id, selected_id, normalized])[:24]
        )
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
    if primary_ref not in asserted_refs:
        raise EvidenceConsumerError(
            "decision_state_binding",
            f"primary semantic unit is not a decision state: {point_id}::{selected_id}",
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
        if not isinstance(point_id, str) or not isinstance(selected_id, str):
            placement_id = _required_string(
                group, "placement_id", boundary="decision_state_binding"
            )
            placement = placements.get(placement_id) if placements is not None else None
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
        if not isinstance(raw_assertions, list) or not raw_assertions:
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
        }
    return [
        {
            "point_id": point_id,
            "rows": [rows[selected_id] for selected_id in sorted(rows)],
        }
        for point_id, rows in sorted(rows_by_point.items())
    ]


def _compact_decision_state_group(group: Mapping[str, Any]) -> dict[str, Any]:
    """Encode repeated state fields once while retaining a point/row join key."""

    assertions = group["state_assertions"]
    return {
        "placement_id": group["placement_id"],
        "state_rows": [
            [assertion[column] for column in DECISION_STATE_ROW_COLUMNS]
            for assertion in assertions
        ],
        "qualification_refs": group[
            "context_only_semantic_unit_refs"
        ],
    }


def _decision_state_rejected_index(
    spec: Mapping[str, Any],
    rejected_points: Sequence[Mapping[str, Any]],
    navigation: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Optionally bind rejected points to an explicit existing navigation group."""

    required_fields = {"point_id", "bounded_point", "disposition", "reason"}
    result: list[dict[str, Any]] = []
    for row in rejected_points:
        if not isinstance(row, Mapping) or set(row) != required_fields:
            raise EvidenceConsumerError(
                "decision_state_binding", "rejected-point fields are invalid"
            )
        result.append(
            {
                field: _required_string(
                    row, field, boundary="decision_state_binding"
                )
                for field in ("point_id", "bounded_point", "disposition", "reason")
            }
        )
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
        legacy_residue = sorted(DECISION_STATE_SPEC_FIELDS & set(spec))
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
    else:
        projection_routes = []
        point_projections = {}
        decision_state_bindings = {}

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
                placements.append(placement)
                point_placement_ids.append(placement_id)
                if is_routed_v2 and point_projections[point_id] == "decision_state":
                    state_binding = point_decision_state_bindings.pop(selected_id, None)
                    if state_binding is None:
                        raise EvidenceConsumerError(
                            "decision_state_binding",
                            f"display row lacks a state binding: {point_id}::{selected_id}",
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
            normalized_decision_state_groups
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
        view["non_claims"].extend(DIRECT_OUTCOME_BOUNDARIES)
        if decision_state_bindings:
            rejected_points = axis_pack.get("rejected_points")
            if not isinstance(rejected_points, list):
                raise EvidenceConsumerError(
                    "decision_state_binding", "source axis rejected-point index is invalid"
                )
            view["decision_state_contract"] = copy.deepcopy(
                DECISION_STATE_CONSUMER_CONTRACT
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
            view["decision_state_groups"], placements=placements
        )
    rebuilt = build_axis_consolidated_view(rebuild_spec)
    if rebuilt != dict(view):
        raise EvidenceConsumerError(
            "view_reprojection", "saved view differs from deterministic source projection"
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
