"""Delta-only Decision State reconciliation for current Phase A authoring.

This module does not infer a decision state.  It verifies current axis packs,
compares their stable semantic-unit identities with explicitly pinned prior
consolidation specs, reuses only one unambiguous exact historical judgment, and
prepares the remaining new or conflicting units for bounded adjudication.
Finalization compiles the resulting judgments into current v4 consolidation
specs and proves them at the existing consolidation consumer boundary.
"""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness_utils import hash_file
from judgment.phase_a_evidence_axis_consolidation import (
    AXIS_PACK_VERSION,
    CURRENT_CONSOLIDATION_SPEC_VERSION,
    DECISION_STATE_CONTRACT,
    PROJECTION_MODES,
    build_axis_consolidated_view,
    validate_axis_consolidated_view,
)
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
)


DECISION_STATE_RECONCILIATION_PLAN_VERSION = (
    "phase_a_decision_state_reconciliation_plan_v1"
)
DECISION_STATE_RECONCILIATION_MANIFEST_VERSION = (
    "phase_a_decision_state_reconciliation_manifest_v1"
)
DECISION_STATE_ADJUDICATION_VERSION = "phase_a_decision_state_adjudication_v1"


def _load_object(path: Path, *, boundary: str) -> dict[str, Any]:
    if not path.is_file():
        raise EvidenceConsumerError(boundary, f"required file is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceConsumerError(boundary, f"invalid JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceConsumerError(boundary, f"expected JSON object: {path}")
    return value


def _required_string(value: Mapping[str, Any], field: str, *, boundary: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise EvidenceConsumerError(boundary, f"{field} must be a nonempty string")
    return result


def _string_list(value: Any, *, field: str, boundary: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise EvidenceConsumerError(boundary, f"{field} must be a string list")
    return list(value)


def _load_pinned_object(binding: Mapping[str, Any], *, boundary: str) -> tuple[Path, dict[str, Any]]:
    if set(binding) != {"path", "sha256"}:
        raise EvidenceConsumerError(boundary, "pinned file binding fields are invalid")
    path = Path(_required_string(binding, "path", boundary=boundary))
    expected = _required_string(binding, "sha256", boundary=boundary)
    if not path.is_file() or hash_file(path) != expected:
        raise EvidenceConsumerError(boundary, f"pinned file changed: {path}")
    return path, _load_object(path, boundary=boundary)


def _semantic_unit(
    *,
    evidence_id: str,
    semantic_unit_ref: str,
    statement: str,
    axis_ids: Any,
    conditions: Any,
    polarity: Any,
) -> dict[str, Any]:
    boundary = "decision_state_reconciliation_identity"
    if not statement:
        raise EvidenceConsumerError(boundary, f"semantic statement is missing: {semantic_unit_ref}")
    payload = {
        "evidence_id": evidence_id,
        "semantic_unit_ref": semantic_unit_ref,
        "statement": statement,
        "axis_ids": sorted(
            _string_list(
                [] if axis_ids is None else axis_ids,
                field="axis_ids",
                boundary=boundary,
            )
        ),
        "conditions": sorted(
            _string_list(
                [] if conditions is None else conditions,
                field="conditions",
                boundary=boundary,
            )
        ),
        "polarity": "not_recorded" if polarity is None else polarity,
    }
    if not isinstance(payload["polarity"], str) or not payload["polarity"]:
        raise EvidenceConsumerError(boundary, f"semantic polarity is missing: {semantic_unit_ref}")
    content_sha256 = _canonical_json_sha256(payload)
    return {
        **payload,
        "content_sha256": content_sha256,
        "identity_id": "decision_state_unit_" + content_sha256[:24],
    }


def _candidate_semantic_units(artifact: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    boundary = "decision_state_reconciliation_identity"
    candidates = artifact.get("candidate_dispositions")
    if not isinstance(candidates, list) or not candidates:
        raise EvidenceConsumerError(boundary, "candidate disposition inventory is missing")
    units: dict[str, dict[str, Any]] = {}

    def add(unit: dict[str, Any]) -> None:
        semantic_ref = unit["semantic_unit_ref"]
        existing = units.get(semantic_ref)
        if existing is not None and existing != unit:
            raise EvidenceConsumerError(
                boundary, f"semantic unit has conflicting content: {semantic_ref}"
            )
        units[semantic_ref] = unit

    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise EvidenceConsumerError(boundary, "candidate disposition row is invalid")
        evidence_id = _required_string(candidate, "evidence_id", boundary=boundary)
        semantic_ref = _required_string(candidate, "semantic_unit_ref", boundary=boundary)
        statement = _required_string(candidate, "normalized_meaning", boundary=boundary)
        add(
            _semantic_unit(
                evidence_id=evidence_id,
                semantic_unit_ref=semantic_ref,
                statement=statement,
                axis_ids=candidate.get("axis_ids"),
                conditions=candidate.get("conditions"),
                polarity=candidate.get("polarity"),
            )
        )
        companions = candidate.get("same_evidence_companion_meanings", [])
        if not isinstance(companions, list):
            raise EvidenceConsumerError(boundary, "companion meaning inventory is invalid")
        for companion in companions:
            if not isinstance(companion, Mapping):
                raise EvidenceConsumerError(boundary, "companion meaning row is invalid")
            add(
                _semantic_unit(
                    evidence_id=evidence_id,
                    semantic_unit_ref=_required_string(
                        companion, "semantic_unit_ref", boundary=boundary
                    ),
                    statement=_required_string(companion, "statement", boundary=boundary),
                    axis_ids=companion.get("axis_ids"),
                    conditions=companion.get("conditions"),
                    polarity=companion.get("polarity"),
                )
            )
    return units


def _axis_selected_rows(
    pack: Mapping[str, Any], *, pack_path: Path, require_relation_refs: bool = True
) -> dict[str, list[dict[str, Any]]]:
    boundary = "decision_state_reconciliation_current_axis"
    if pack.get("schema_version") != AXIS_PACK_VERSION:
        raise EvidenceConsumerError(boundary, "current reconciliation requires a current axis pack")
    stored_pack_hash = pack.get("axis_pack_sha256")
    unhashed_pack = dict(pack)
    unhashed_pack.pop("axis_pack_sha256", None)
    if (
        not isinstance(stored_pack_hash, str)
        or _canonical_json_sha256(unhashed_pack) != stored_pack_hash
    ):
        raise EvidenceConsumerError(boundary, "axis pack identity is invalid")
    points = pack.get("points")
    if not isinstance(points, list) or not points:
        raise EvidenceConsumerError(boundary, "current axis pack has no accepted points")
    rows_by_point: dict[str, list[dict[str, Any]]] = {}
    global_slots: dict[tuple[str, str], str] = {}
    for descriptor in points:
        if not isinstance(descriptor, Mapping):
            raise EvidenceConsumerError(boundary, "axis point descriptor is invalid")
        point_id = _required_string(descriptor, "point_id", boundary=boundary)
        artifact_path = Path(
            _required_string(descriptor, "artifact_path", boundary=boundary)
        )
        expected_hash = _required_string(descriptor, "artifact_sha256", boundary=boundary)
        if not artifact_path.is_file() or hash_file(artifact_path) != expected_hash:
            raise EvidenceConsumerError(boundary, f"point artifact changed: {point_id}")
        artifact = _load_object(artifact_path, boundary=boundary)
        units = _candidate_semantic_units(artifact)
        source_groups = artifact.get("source_groups")
        if not isinstance(source_groups, list) or not source_groups:
            raise EvidenceConsumerError(boundary, f"point source groups are missing: {point_id}")
        point_rows: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        for group in source_groups:
            group_rows = group.get("rows") if isinstance(group, Mapping) else None
            if not isinstance(group_rows, list):
                raise EvidenceConsumerError(boundary, f"point source rows are invalid: {point_id}")
            for raw_row in group_rows:
                if not isinstance(raw_row, Mapping):
                    raise EvidenceConsumerError(boundary, f"point source row is invalid: {point_id}")
                selected_id = _required_string(raw_row, "selected_id", boundary=boundary)
                if selected_id in selected_ids:
                    raise EvidenceConsumerError(
                        boundary, f"duplicate selected row: {point_id}::{selected_id}"
                    )
                selected_ids.add(selected_id)
                evidence_id = _required_string(raw_row, "evidence_id", boundary=boundary)
                primary_ref = _required_string(
                    raw_row, "semantic_unit_ref", boundary=boundary
                )
                companions = raw_row.get("same_evidence_companion_meanings")
                if not isinstance(companions, list):
                    raise EvidenceConsumerError(
                        boundary, f"companion meanings are invalid: {point_id}::{selected_id}"
                    )
                available_refs = [primary_ref]
                row_companions: dict[str, Mapping[str, Any]] = {}
                for item in companions:
                    if not isinstance(item, Mapping):
                        raise EvidenceConsumerError(
                            boundary,
                            f"companion meaning is invalid: {point_id}::{selected_id}",
                        )
                    semantic_ref = _required_string(
                        item, "semantic_unit_ref", boundary=boundary
                    )
                    row_companions[semantic_ref] = item
                    available_refs.append(semantic_ref)
                if len(available_refs) != len(set(available_refs)):
                    raise EvidenceConsumerError(
                        boundary, f"duplicate semantic ref: {point_id}::{selected_id}"
                    )
                row_units = []
                for semantic_ref in available_refs:
                    unit = units.get(semantic_ref)
                    if unit is None and semantic_ref in row_companions:
                        companion = row_companions[semantic_ref]
                        statement = companion.get("statement")
                        if not isinstance(statement, str) or not statement:
                            statement = _required_string(
                                companion, "normalized_meaning", boundary=boundary
                            )
                        unit = _semantic_unit(
                            evidence_id=evidence_id,
                            semantic_unit_ref=semantic_ref,
                            statement=statement,
                            axis_ids=companion.get("axis_ids"),
                            conditions=companion.get("conditions"),
                            polarity=companion.get("polarity"),
                        )
                        units[semantic_ref] = unit
                    if unit is None or unit["evidence_id"] != evidence_id:
                        raise EvidenceConsumerError(
                            boundary,
                            f"selected row references foreign semantic content: "
                            f"{point_id}::{selected_id}::{semantic_ref}",
                        )
                    slot = (evidence_id, semantic_ref)
                    previous_content = global_slots.get(slot)
                    if previous_content is not None and previous_content != unit["content_sha256"]:
                        raise EvidenceConsumerError(
                            "decision_state_reconciliation_current_identity",
                            f"current semantic identity has conflicting content: {semantic_ref}",
                        )
                    global_slots[slot] = unit["content_sha256"]
                    row_units.append(copy.deepcopy(unit))
                if require_relation_refs:
                    relation_refs = _string_list(
                        raw_row.get("relation_semantic_unit_refs"),
                        field="relation_semantic_unit_refs",
                        boundary=boundary,
                    )
                    if not relation_refs or len(relation_refs) != len(set(relation_refs)):
                        raise EvidenceConsumerError(
                            boundary,
                            f"current relation binding is missing or duplicated: "
                            f"{point_id}::{selected_id}",
                        )
                    if set(relation_refs) - set(available_refs):
                        raise EvidenceConsumerError(
                            boundary,
                            f"current relation binding is foreign: {point_id}::{selected_id}",
                        )
                else:
                    relation_refs = []
                point_rows.append(
                    {
                        "point_id": point_id,
                        "selected_id": selected_id,
                        "evidence_id": evidence_id,
                        "semantic_units": row_units,
                        "relation_semantic_unit_refs": sorted(relation_refs),
                    }
                )
        rows_by_point[point_id] = point_rows
    return rows_by_point


def _projection_by_point(spec: Mapping[str, Any], point_ids: set[str]) -> dict[str, str]:
    boundary = "decision_state_reconciliation_projection"
    routes = spec.get("projection_routes")
    if isinstance(routes, Mapping):
        routes = [routes]
    if not isinstance(routes, list) or not routes:
        raise EvidenceConsumerError(boundary, "projection routes are missing")
    result: dict[str, str] = {}
    for route in routes:
        if not isinstance(route, Mapping):
            raise EvidenceConsumerError(boundary, "projection route is invalid")
        mode = _required_string(route, "projection_mode", boundary=boundary)
        if mode not in PROJECTION_MODES:
            raise EvidenceConsumerError(boundary, f"projection mode is invalid: {mode}")
        route_points = _string_list(
            route.get("point_ids"), field="point_ids", boundary=boundary
        )
        for point_id in route_points:
            if point_id not in point_ids or point_id in result:
                raise EvidenceConsumerError(
                    boundary, f"projection membership is invalid: {point_id}"
                )
            result[point_id] = mode
    if set(result) != point_ids:
        raise EvidenceConsumerError(boundary, "projection routes do not cover current points")
    return result


def _state_cell(assertion: Mapping[str, Any]) -> dict[str, Any]:
    boundary = "decision_state_reconciliation_history"
    required = {
        "state_kind",
        "commercial_direction",
        "decision_object",
        "semantic_unit_refs",
        "quantity",
        "conditions",
    }
    if set(assertion) != required:
        raise EvidenceConsumerError(boundary, "historical state assertion fields are invalid")
    refs = sorted(
        _string_list(
            assertion.get("semantic_unit_refs"),
            field="semantic_unit_refs",
            boundary=boundary,
        )
    )
    if not refs or len(refs) != len(set(refs)):
        raise EvidenceConsumerError(boundary, "historical state assertion refs are invalid")
    state_kind = _required_string(assertion, "state_kind", boundary=boundary)
    direction = _required_string(assertion, "commercial_direction", boundary=boundary)
    decision_object = _required_string(assertion, "decision_object", boundary=boundary)
    contract = DECISION_STATE_CONTRACT.get(state_kind)
    if contract is None or direction not in contract["directions"]:
        raise EvidenceConsumerError(boundary, "historical state is outside contract")
    quantity = assertion.get("quantity")
    if state_kind == "multi_unit_purchase":
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 2:
            raise EvidenceConsumerError(boundary, "historical multi-unit state lacks quantity")
    elif quantity is not None:
        raise EvidenceConsumerError(boundary, "historical state quantity is invalid")
    return {
        "classification": "state",
        "semantic_unit_refs": refs,
        "state_kind": state_kind,
        "commercial_direction": direction,
        "decision_object": decision_object,
        "quantity": quantity,
        "conditions": sorted(
            _string_list(
                assertion.get("conditions"), field="conditions", boundary=boundary
            )
        ),
    }


def _context_cell(semantic_ref: str) -> dict[str, Any]:
    return {
        "classification": "context_only",
        "semantic_unit_refs": [semantic_ref],
        "state_kind": None,
        "commercial_direction": None,
        "decision_object": None,
        "quantity": None,
        "conditions": [],
    }


def _historical_observations(
    spec_binding: Mapping[str, Any]
) -> list[dict[str, Any]]:
    boundary = "decision_state_reconciliation_history"
    spec_path, spec = _load_pinned_object(spec_binding, boundary=boundary)
    pack_path = Path(_required_string(spec, "source_axis_pack_path", boundary=boundary))
    expected_pack_hash = _required_string(
        spec, "source_axis_pack_sha256", boundary=boundary
    )
    if not pack_path.is_file() or hash_file(pack_path) != expected_pack_hash:
        raise EvidenceConsumerError(boundary, f"historical axis pack changed: {pack_path}")
    pack = _load_object(pack_path, boundary=boundary)
    rows_by_point = _axis_selected_rows(
        pack, pack_path=pack_path, require_relation_refs=False
    )
    row_index = {
        (point_id, row["selected_id"]): row
        for point_id, rows in rows_by_point.items()
        for row in rows
    }
    observations: list[dict[str, Any]] = []
    bindings = spec.get("decision_state_bindings")
    if bindings in (None, []):
        return observations
    if not isinstance(bindings, list):
        raise EvidenceConsumerError(boundary, "historical Decision State bindings are invalid")
    for point_binding in bindings:
        if not isinstance(point_binding, Mapping):
            raise EvidenceConsumerError(boundary, "historical point binding is invalid")
        point_id = _required_string(point_binding, "point_id", boundary=boundary)
        rows = point_binding.get("rows")
        if not isinstance(rows, list):
            raise EvidenceConsumerError(boundary, "historical row bindings are invalid")
        for binding_row in rows:
            if not isinstance(binding_row, Mapping):
                raise EvidenceConsumerError(boundary, "historical row binding is invalid")
            selected_id = _required_string(
                binding_row, "selected_id", boundary=boundary
            )
            source_row = row_index.get((point_id, selected_id))
            if source_row is None:
                raise EvidenceConsumerError(
                    boundary, f"historical selected row is missing: {point_id}::{selected_id}"
                )
            units = {
                unit["semantic_unit_ref"]: unit for unit in source_row["semantic_units"]
            }
            assertions = binding_row.get("state_assertions")
            if not isinstance(assertions, list):
                raise EvidenceConsumerError(boundary, "historical state assertions are invalid")
            cells = [_state_cell(assertion) for assertion in assertions]
            context_refs = _string_list(
                binding_row.get("context_only_semantic_unit_refs"),
                field="context_only_semantic_unit_refs",
                boundary=boundary,
            )
            cells.extend(_context_cell(ref) for ref in context_refs)
            cells_by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for cell in cells:
                cell_refs = cell["semantic_unit_refs"]
                for semantic_ref in cell_refs:
                    unit = units.get(semantic_ref)
                    if unit is None:
                        raise EvidenceConsumerError(
                            boundary, f"historical judgment references foreign meaning: {semantic_ref}"
                        )
                    cells_by_ref[semantic_ref].append(copy.deepcopy(cell))
            if set(cells_by_ref) != set(units):
                raise EvidenceConsumerError(
                    boundary,
                    f"historical judgment does not cover row meanings: {point_id}::{selected_id}",
                )
            context_ref_set = set(context_refs)
            asserted_ref_set = {
                semantic_ref
                for cell in cells
                if cell["classification"] == "state"
                for semantic_ref in cell["semantic_unit_refs"]
            }
            if context_ref_set & asserted_ref_set:
                raise EvidenceConsumerError(
                    boundary,
                    f"historical state and context overlap: {point_id}::{selected_id}",
                )
            for semantic_ref, ref_cells in cells_by_ref.items():
                if semantic_ref in context_ref_set and len(ref_cells) != 1:
                    raise EvidenceConsumerError(
                        boundary,
                        f"historical context ref also carries state: {semantic_ref}",
                    )
                unit = units[semantic_ref]
                observations.append(
                    {
                        "identity_id": unit["identity_id"],
                        "evidence_id": unit["evidence_id"],
                        "semantic_unit_ref": semantic_ref,
                        "content_sha256": unit["content_sha256"],
                        "bundle": sorted(
                            ref_cells, key=lambda item: _canonical_json_sha256(item)
                        ),
                        "source_spec_path": str(spec_path),
                        "source_spec_sha256": spec_binding["sha256"],
                    }
                )
    return observations


def _response_schema(*, reconciliation_scope_sha256: str) -> dict[str, Any]:
    required = [
        "item_ids",
        "classification",
        "state_kind",
        "commercial_direction",
        "decision_object",
        "quantity",
        "conditions",
    ]
    item_ids_schema = {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "string",
            "pattern": "^decision_state_unit_[0-9a-f]{24}$",
        },
    }

    def judgment_variant(state_kind: str | None) -> dict[str, Any]:
        if state_kind is None:
            properties: dict[str, Any] = {
                "item_ids": {**item_ids_schema, "maxItems": 1},
                "classification": {"type": "string", "const": "context_only"},
                "state_kind": {"type": "null"},
                "commercial_direction": {"type": "null"},
                "decision_object": {"type": "null"},
                "quantity": {"type": "null"},
                "conditions": {
                    "type": "array",
                    "maxItems": 0,
                    "items": {"type": "string"},
                },
            }
        else:
            properties = {
                "item_ids": item_ids_schema,
                "classification": {"type": "string", "const": "state"},
                "state_kind": {"type": "string", "const": state_kind},
                "commercial_direction": {
                    "type": "string",
                    "enum": sorted(DECISION_STATE_CONTRACT[state_kind]["directions"]),
                },
                "decision_object": {"type": "string", "minLength": 1},
                "quantity": (
                    {"type": "integer", "minimum": 2}
                    if state_kind == "multi_unit_purchase"
                    else {"type": "null"}
                ),
                "conditions": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                },
            }
        return {
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": properties,
        }

    variants = [judgment_variant(None)]
    variants.extend(
        judgment_variant(state_kind) for state_kind in sorted(DECISION_STATE_CONTRACT)
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "reconciliation_scope_sha256",
            "judgments",
        ],
        "properties": {
            "schema_version": {
                "type": "string",
                "const": DECISION_STATE_ADJUDICATION_VERSION,
            },
            "reconciliation_scope_sha256": {
                "type": "string",
                "const": reconciliation_scope_sha256,
            },
            "judgments": {
                "type": "array",
                "minItems": 1,
                "items": {"anyOf": variants},
            },
        },
    }


def _prompt(
    groups: Sequence[Mapping[str, Any]], *, reconciliation_scope_sha256: str
) -> str:
    payload = json.dumps(groups, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "Classify only the unresolved atomic semantic units below for Phase A Decision "
        "State projection. This is bounded evidence packing, not Deliver. For each item, "
        "either mark it context_only or bind the explicit actor judgment/action state. "
        "Keep intent separate from observed behavior; multiple units are not multiple "
        "repurchases; price concern is not automatically poor value; remorse is not erased "
        "by future intent. Group item_ids only when the statements from the same evidence "
        "jointly express one indivisible state. Account for every item_id at least once; "
        "repeat an item_id only when one atomic statement genuinely carries multiple distinct "
        "states. For context_only return exactly one singleton judgment with null state_kind, "
        "commercial_direction, decision_object, "
        "and quantity with empty conditions. Return reconciliation_scope_sha256 exactly as "
        f"{reconciliation_scope_sha256}. For state, use the supplied schema vocabulary "
        "and preserve explicit object, quantity, and conditions. Historical alternatives "
        "are allegations to adjudicate, not votes.\n\nUNRESOLVED_EVIDENCE_GROUPS:\n"
        + payload
    )


def prepare_phase_a_decision_state_reconciliation(
    plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Prepare one run-scoped, cross-axis delta reconciliation manifest."""

    boundary = "decision_state_reconciliation_plan"
    if plan.get("schema_version") != DECISION_STATE_RECONCILIATION_PLAN_VERSION:
        raise EvidenceConsumerError(boundary, "unsupported reconciliation plan version")
    if set(plan) != {"schema_version", "current_axes", "prior_specs"}:
        raise EvidenceConsumerError(boundary, "reconciliation plan fields are invalid")
    raw_axes = plan.get("current_axes")
    raw_prior = plan.get("prior_specs")
    if not isinstance(raw_axes, list) or not raw_axes:
        raise EvidenceConsumerError(boundary, "reconciliation plan has no current axes")
    if not isinstance(raw_prior, list):
        raise EvidenceConsumerError(boundary, "reconciliation prior specs are invalid")

    history_by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    history_by_slot: dict[tuple[str, str], set[str]] = defaultdict(set)
    for spec_binding in raw_prior:
        if not isinstance(spec_binding, Mapping):
            raise EvidenceConsumerError(boundary, "prior spec binding is invalid")
        for observation in _historical_observations(spec_binding):
            history_by_identity[observation["identity_id"]].append(observation)
            history_by_slot[
                (observation["evidence_id"], observation["semantic_unit_ref"])
            ].add(observation["content_sha256"])

    axes: list[dict[str, Any]] = []
    current_units: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    axis_ids: set[str] = set()
    for raw_axis in raw_axes:
        if not isinstance(raw_axis, Mapping) or set(raw_axis) != {
            "axis_pack",
            "spec_template",
        }:
            raise EvidenceConsumerError(boundary, "current axis binding fields are invalid")
        pack_path, pack = _load_pinned_object(
            raw_axis["axis_pack"], boundary="decision_state_reconciliation_current_axis"
        )
        spec_path, template = _load_pinned_object(
            raw_axis["spec_template"], boundary="decision_state_reconciliation_current_axis"
        )
        axis_id = _required_string(pack, "axis_id", boundary=boundary)
        if axis_id != template.get("axis_id") or axis_id in axis_ids:
            raise EvidenceConsumerError(boundary, f"current axis identity is invalid: {axis_id}")
        axis_ids.add(axis_id)
        rows_by_point = _axis_selected_rows(pack, pack_path=pack_path)
        routes = _projection_by_point(template, set(rows_by_point))
        shell = copy.deepcopy(template)
        shell["schema_version"] = CURRENT_CONSOLIDATION_SPEC_VERSION
        shell["source_axis_pack_path"] = str(pack_path)
        shell["source_axis_pack_sha256"] = raw_axis["axis_pack"]["sha256"]
        for field in (
            "decision_state_bindings",
            "decision_state_bindings_sha256",
            "direct_outcome_relation_bindings",
        ):
            shell.pop(field, None)
        direct_bindings: list[dict[str, Any]] = []
        decision_point_ids: list[str] = []
        for point_id, point_rows in rows_by_point.items():
            mode = routes[point_id]
            if mode == "direct_outcome":
                direct_bindings.append(
                    {
                        "point_id": point_id,
                        "rows": [
                            {
                                "selected_id": row["selected_id"],
                                "relation_semantic_unit_refs": copy.deepcopy(
                                    row["relation_semantic_unit_refs"]
                                ),
                            }
                            for row in point_rows
                        ],
                    }
                )
                continue
            decision_point_ids.append(point_id)
            for row in point_rows:
                row_copy = {
                    "axis_id": axis_id,
                    "point_id": point_id,
                    "selected_id": row["selected_id"],
                    "evidence_id": row["evidence_id"],
                    "identity_ids": [
                        unit["identity_id"] for unit in row["semantic_units"]
                    ],
                    "relation_semantic_unit_refs": copy.deepcopy(
                        row["relation_semantic_unit_refs"]
                    ),
                }
                rows.append(row_copy)
                for unit in row["semantic_units"]:
                    existing = current_units.get(unit["identity_id"])
                    if existing is not None and existing != unit:
                        raise EvidenceConsumerError(
                            "decision_state_reconciliation_current_identity",
                            f"current semantic identity collision: {unit['semantic_unit_ref']}",
                        )
                    current_units[unit["identity_id"]] = copy.deepcopy(unit)
        if direct_bindings:
            shell["direct_outcome_relation_bindings"] = direct_bindings
        axes.append(
            {
                "axis_id": axis_id,
                "axis_pack_path": str(pack_path),
                "axis_pack_file_sha256": raw_axis["axis_pack"]["sha256"],
                "spec_template_path": str(spec_path),
                "spec_template_file_sha256": raw_axis["spec_template"]["sha256"],
                "decision_state_point_ids": sorted(decision_point_ids),
                "spec_shell": shell,
            }
        )

    reusable_bundle_by_identity: dict[str, list[dict[str, Any]]] = {}
    unresolved_causes: dict[str, set[str]] = defaultdict(set)
    prior_alternatives: dict[str, list[dict[str, Any]]] = {}
    for identity_id, unit in current_units.items():
        observations = history_by_identity.get(identity_id, [])
        bundles_by_sha: dict[str, list[dict[str, Any]]] = {}
        for observation in observations:
            bundle = observation["bundle"]
            bundles_by_sha[_canonical_json_sha256(bundle)] = bundle
        prior_alternatives[identity_id] = [
            copy.deepcopy(bundles_by_sha[key]) for key in sorted(bundles_by_sha)
        ]
        if len(bundles_by_sha) == 1:
            reusable_bundle_by_identity[identity_id] = copy.deepcopy(
                next(iter(bundles_by_sha.values()))
            )
        elif len(bundles_by_sha) > 1:
            unresolved_causes[identity_id].add("conflicting_history")
        else:
            slot = (unit["evidence_id"], unit["semantic_unit_ref"])
            cause = "changed_content" if history_by_slot.get(slot) else "new_semantic_unit"
            unresolved_causes[identity_id].add(cause)

    # A historical multi-ref assertion is reusable only as one complete cell.
    # Current v4 rows address meanings by semantic ref, so one evidence/ref slot
    # must resolve to one current identity across every axis in this run; the
    # per-pack identity check cannot see a conflict raised by a second pack.
    current_by_slot: dict[tuple[str, str], str] = {}
    for identity_id, unit in current_units.items():
        slot = (unit["evidence_id"], unit["semantic_unit_ref"])
        if current_by_slot.setdefault(slot, identity_id) != identity_id:
            raise EvidenceConsumerError(
                "decision_state_reconciliation_current_identity",
                f"current semantic identity has conflicting content across axes: "
                f"{unit['semantic_unit_ref']}",
            )
    changed = True
    while changed:
        changed = False
        for identity_id, bundle in list(reusable_bundle_by_identity.items()):
            unit = current_units[identity_id]
            for cell in bundle:
                member_ids = [
                    current_by_slot.get((unit["evidence_id"], semantic_ref))
                    for semantic_ref in cell["semantic_unit_refs"]
                ]
                complete = all(member_ids)
                expected_sha = _canonical_json_sha256(cell)
                if complete:
                    complete = all(
                        member_id in reusable_bundle_by_identity
                        and any(
                            _canonical_json_sha256(member_cell) == expected_sha
                            for member_cell in reusable_bundle_by_identity[member_id]
                        )
                        and not unresolved_causes.get(member_id)
                        for member_id in member_ids
                    )
                if complete:
                    continue
                affected = {
                    identity_id,
                    *(member_id for member_id in member_ids if member_id),
                }
                for member_id in affected:
                    if member_id in reusable_bundle_by_identity:
                        reusable_bundle_by_identity.pop(member_id, None)
                        unresolved_causes[member_id].add(
                            "partial_or_conflicting_state_group"
                        )
                        changed = True
                break

    reused_cells: dict[str, dict[str, Any]] = {}
    reuse_cell_ids_by_identity: dict[str, list[str]] = {}
    for identity_id, bundle in reusable_bundle_by_identity.items():
        unit = current_units[identity_id]
        cell_ids: list[str] = []
        for cell in bundle:
            cell_payload = {"evidence_id": unit["evidence_id"], **cell}
            cell_id = "decision_state_cell_" + _canonical_json_sha256(cell_payload)[:24]
            reused_cells[cell_id] = cell_payload
            cell_ids.append(cell_id)
        reuse_cell_ids_by_identity[identity_id] = sorted(cell_ids)

    unresolved_units: list[dict[str, Any]] = []
    for identity_id in sorted(unresolved_causes):
        unit = current_units[identity_id]
        unresolved_units.append(
            {
                **copy.deepcopy(unit),
                "causes": sorted(unresolved_causes[identity_id]),
                "prior_judgment_alternatives": prior_alternatives.get(identity_id, []),
            }
        )
    unresolved_ids = {unit["identity_id"] for unit in unresolved_units}
    affected_rows = sum(
        1 for row in rows if unresolved_ids & set(row["identity_ids"])
    )
    groups: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in unresolved_units:
        grouped[unit["evidence_id"]].append(unit)
    for evidence_id in sorted(grouped):
        groups.append(
            {
                "evidence_id": evidence_id,
                "items": sorted(grouped[evidence_id], key=lambda item: item["identity_id"]),
            }
        )

    reconciliation_scope_sha256 = _canonical_json_sha256(
        {
            "plan": plan,
            "unresolved_evidence_groups": groups,
        }
    )

    manifest: dict[str, Any] = {
        "schema_version": DECISION_STATE_RECONCILIATION_MANIFEST_VERSION,
        "plan": copy.deepcopy(plan),
        "axes": sorted(axes, key=lambda item: item["axis_id"]),
        "rows": sorted(
            rows, key=lambda item: (item["axis_id"], item["point_id"], item["selected_id"])
        ),
        "current_semantic_units": [
            current_units[key] for key in sorted(current_units)
        ],
        "reused_cells": [reused_cells[key] | {"cell_id": key} for key in sorted(reused_cells)],
        "reuse_cell_ids_by_identity": {
            key: reuse_cell_ids_by_identity[key]
            for key in sorted(reuse_cell_ids_by_identity)
        },
        "unresolved_evidence_groups": groups,
        "reconciliation_scope_sha256": reconciliation_scope_sha256,
        "counts": {
            "axis_count": len(axes),
            "decision_state_point_count": sum(
                len(axis["decision_state_point_ids"]) for axis in axes
            ),
            "decision_state_row_count": len(rows),
            "semantic_unit_count": len(current_units),
            "reused_semantic_unit_count": len(reuse_cell_ids_by_identity),
            "unresolved_semantic_unit_count": len(unresolved_units),
            "affected_row_count": affected_rows,
        },
        "prompt": (
            _prompt(
                groups,
                reconciliation_scope_sha256=reconciliation_scope_sha256,
            )
            if unresolved_units
            else None
        ),
        "response_schema": (
            _response_schema(
                reconciliation_scope_sha256=reconciliation_scope_sha256
            )
            if unresolved_units
            else None
        ),
        "model_api_calls": 0,
        "non_claims": [
            "historical agreement supports mechanical reuse, not semantic truth",
            "conflicts and new meanings require bounded judgment",
            "relation remains point-relative and is copied only from the current v3 selection artifact",
            "this run-scoped manifest is not a global semantic registry or Deliver output",
        ],
    }
    manifest["manifest_sha256"] = _canonical_json_sha256(manifest)
    return manifest


def _adjudicated_cells(
    manifest: Mapping[str, Any], adjudication: Mapping[str, Any] | None
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    boundary = "decision_state_reconciliation_adjudication"
    unresolved = {
        item["identity_id"]: item
        for group in manifest["unresolved_evidence_groups"]
        for item in group["items"]
    }
    if not unresolved:
        if adjudication not in (None, {}):
            raise EvidenceConsumerError(boundary, "adjudication supplied with no unresolved units")
        return {}, {}
    if not isinstance(adjudication, Mapping):
        raise EvidenceConsumerError(boundary, "unresolved units require adjudication")
    if adjudication.get("schema_version") != DECISION_STATE_ADJUDICATION_VERSION:
        raise EvidenceConsumerError(boundary, "unsupported adjudication version")
    if adjudication.get("reconciliation_scope_sha256") != manifest.get(
        "reconciliation_scope_sha256"
    ):
        raise EvidenceConsumerError(boundary, "adjudication scope identity changed")
    if set(adjudication) != {
        "schema_version",
        "reconciliation_scope_sha256",
        "judgments",
    }:
        raise EvidenceConsumerError(boundary, "adjudication fields are invalid")
    judgments = adjudication.get("judgments")
    if not isinstance(judgments, list):
        raise EvidenceConsumerError(boundary, "adjudication judgments are missing")
    seen: set[str] = set()
    classifications_by_identity: dict[str, set[str]] = defaultdict(set)
    cells: dict[str, dict[str, Any]] = {}
    cell_ids_by_identity: dict[str, list[str]] = defaultdict(list)
    for judgment in judgments:
        if not isinstance(judgment, Mapping) or set(judgment) != {
            "item_ids",
            "classification",
            "state_kind",
            "commercial_direction",
            "decision_object",
            "quantity",
            "conditions",
        }:
            raise EvidenceConsumerError(boundary, "adjudication judgment fields are invalid")
        item_ids = _string_list(
            judgment.get("item_ids"), field="item_ids", boundary=boundary
        )
        if not item_ids or len(item_ids) != len(set(item_ids)):
            raise EvidenceConsumerError(boundary, "adjudication item coverage is duplicated")
        if set(item_ids) - set(unresolved):
            raise EvidenceConsumerError(boundary, "adjudication item coverage is invalid")
        evidence_ids = {unresolved[item_id]["evidence_id"] for item_id in item_ids}
        if len(evidence_ids) != 1:
            raise EvidenceConsumerError(boundary, "adjudication groups cross evidence")
        classification = judgment.get("classification")
        refs = sorted(unresolved[item_id]["semantic_unit_ref"] for item_id in item_ids)
        if classification == "context_only":
            if len(item_ids) != 1 or item_ids[0] in seen:
                raise EvidenceConsumerError(
                    boundary, "context-only adjudication must be one unrepeated item"
                )
            if any(
                judgment.get(field) is not None
                for field in (
                    "state_kind",
                    "commercial_direction",
                    "decision_object",
                    "quantity",
                )
            ) or judgment.get("conditions") != []:
                raise EvidenceConsumerError(boundary, "context-only adjudication invents state")
            cell = _context_cell(refs[0])
        elif classification == "state":
            state_kind = judgment.get("state_kind")
            direction = judgment.get("commercial_direction")
            decision_object = judgment.get("decision_object")
            conditions = judgment.get("conditions")
            if (
                not isinstance(state_kind, str)
                or state_kind not in DECISION_STATE_CONTRACT
                or direction not in DECISION_STATE_CONTRACT[state_kind]["directions"]
                or not isinstance(decision_object, str)
                or not decision_object
                or not isinstance(conditions, list)
                or any(not isinstance(item, str) or not item for item in conditions)
                or len(conditions) != len(set(conditions))
            ):
                raise EvidenceConsumerError(boundary, "adjudicated state is outside contract")
            quantity = judgment.get("quantity")
            if state_kind == "multi_unit_purchase":
                if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 2:
                    raise EvidenceConsumerError(boundary, "multi-unit adjudication lacks quantity")
            elif quantity is not None:
                raise EvidenceConsumerError(boundary, "adjudication quantity is invalid")
            cell = {
                "classification": "state",
                "semantic_unit_refs": refs,
                "state_kind": state_kind,
                "commercial_direction": direction,
                "decision_object": decision_object,
                "quantity": quantity,
                "conditions": sorted(conditions),
            }
        else:
            raise EvidenceConsumerError(boundary, "adjudication classification is invalid")
        for item_id in item_ids:
            classifications_by_identity[item_id].add(classification)
            if len(classifications_by_identity[item_id]) != 1:
                raise EvidenceConsumerError(
                    boundary, "adjudication mixes state and context for one item"
                )
        seen.update(item_ids)
        cell_payload = {"evidence_id": next(iter(evidence_ids)), **cell}
        cell_id = "decision_state_cell_" + _canonical_json_sha256(cell_payload)[:24]
        if cell_id in cells:
            raise EvidenceConsumerError(boundary, "adjudication repeats an identical state cell")
        cells[cell_id] = cell_payload
        for item_id in item_ids:
            cell_ids_by_identity[item_id].append(cell_id)
    if seen != set(unresolved):
        missing = sorted(set(unresolved) - seen)
        raise EvidenceConsumerError(
            boundary, f"adjudication does not cover every unresolved unit: {missing[0]}"
        )
    return cells, {
        identity_id: sorted(cell_ids)
        for identity_id, cell_ids in cell_ids_by_identity.items()
    }


def finalize_phase_a_decision_state_reconciliation(
    manifest: Mapping[str, Any], *, adjudication: Mapping[str, Any] | None
) -> dict[str, dict[str, Any]]:
    """Compile complete current v4 specs and validate the real consumer boundary."""

    boundary = "decision_state_reconciliation_manifest"
    if manifest.get("schema_version") != DECISION_STATE_RECONCILIATION_MANIFEST_VERSION:
        raise EvidenceConsumerError(boundary, "unsupported reconciliation manifest version")
    expected_hash = manifest.get("manifest_sha256")
    unhashed = dict(manifest)
    unhashed.pop("manifest_sha256", None)
    if not isinstance(expected_hash, str) or _canonical_json_sha256(unhashed) != expected_hash:
        raise EvidenceConsumerError(boundary, "reconciliation manifest identity changed")
    regenerated = prepare_phase_a_decision_state_reconciliation(manifest["plan"])
    if regenerated != manifest:
        raise EvidenceConsumerError(boundary, "reconciliation inputs changed after preparation")

    cells = {
        cell["cell_id"]: {key: copy.deepcopy(value) for key, value in cell.items() if key != "cell_id"}
        for cell in manifest["reused_cells"]
    }
    cell_ids_by_identity = {
        identity_id: list(cell_ids)
        for identity_id, cell_ids in manifest["reuse_cell_ids_by_identity"].items()
    }
    adjudicated, adjudicated_ids = _adjudicated_cells(manifest, adjudication)
    cells.update(adjudicated)
    cell_ids_by_identity.update(adjudicated_ids)
    current_units = {
        unit["identity_id"]: unit for unit in manifest["current_semantic_units"]
    }

    rows_by_axis_point: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in manifest["rows"]:
        row_cell_ids: list[str] = []
        seen_cell_ids: set[str] = set()
        for identity_id in row["identity_ids"]:
            identity_cell_ids = cell_ids_by_identity.get(identity_id)
            if not identity_cell_ids:
                raise EvidenceConsumerError(
                    "decision_state_reconciliation_coverage",
                    f"semantic unit has no final judgment: {identity_id}",
                )
            for cell_id in identity_cell_ids:
                if cell_id not in seen_cell_ids:
                    seen_cell_ids.add(cell_id)
                    row_cell_ids.append(cell_id)
        available_refs = {
            current_units[identity_id]["semantic_unit_ref"]
            for identity_id in row["identity_ids"]
        }
        asserted_refs: set[str] = set()
        context_refs: set[str] = set()
        assertions: list[dict[str, Any]] = []
        for cell_id in row_cell_ids:
            cell = cells[cell_id]
            if cell["evidence_id"] != row["evidence_id"]:
                raise EvidenceConsumerError(
                    "decision_state_reconciliation_coverage",
                    f"judgment crosses evidence: {row['point_id']}::{row['selected_id']}",
                )
            refs = set(cell["semantic_unit_refs"])
            if not refs <= available_refs:
                raise EvidenceConsumerError(
                    "decision_state_reconciliation_coverage",
                    f"judgment cell is incomplete in current row: "
                    f"{row['point_id']}::{row['selected_id']}",
                )
            if cell["classification"] == "context_only":
                context_refs.update(refs)
            else:
                asserted_refs.update(refs)
                assertions.append(
                    {
                        "state_kind": cell["state_kind"],
                        "commercial_direction": cell["commercial_direction"],
                        "decision_object": cell["decision_object"],
                        "semantic_unit_refs": sorted(refs),
                        "quantity": cell["quantity"],
                        "conditions": copy.deepcopy(cell["conditions"]),
                    }
                )
        if asserted_refs & context_refs or asserted_refs | context_refs != available_refs:
            raise EvidenceConsumerError(
                "decision_state_reconciliation_coverage",
                f"final judgment does not cover row exactly: "
                f"{row['point_id']}::{row['selected_id']}",
            )
        rows_by_axis_point[(row["axis_id"], row["point_id"])].append(
            {
                "selected_id": row["selected_id"],
                "state_assertions": sorted(
                    assertions, key=lambda item: _canonical_json_sha256(item)
                ),
                "context_only_semantic_unit_refs": sorted(context_refs),
                "relation_semantic_unit_refs": copy.deepcopy(
                    row["relation_semantic_unit_refs"]
                ),
            }
        )

    outputs: dict[str, dict[str, Any]] = {}
    for axis in manifest["axes"]:
        axis_id = axis["axis_id"]
        spec = copy.deepcopy(axis["spec_shell"])
        bindings = [
            {
                "point_id": point_id,
                "rows": sorted(
                    rows_by_axis_point[(axis_id, point_id)],
                    key=lambda item: item["selected_id"],
                ),
            }
            for point_id in axis["decision_state_point_ids"]
        ]
        if bindings:
            spec["decision_state_bindings"] = bindings
        else:
            spec.pop("decision_state_bindings", None)
            spec.pop("decision_state_rejected_point_navigation", None)
        view = build_axis_consolidated_view(copy.deepcopy(spec))
        validate_axis_consolidated_view(view, expected_view_sha256=view["view_sha256"])
        outputs[axis_id] = spec
    return outputs
