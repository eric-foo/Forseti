"""Fail-closed semantic calibration over bounded Evidence Consolidation slices.

Deterministic code owns source projection, route identity, response structure,
gold completeness, field obligations, and stop aggregation.  A cold human or
agent adjudicator still owns meaning equivalence and atom matching; missing
adjudication is therefore a blocker, never an implicit pass.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Mapping, Sequence

from harness_utils import sha256_bytes
from judgment.semantic_evidence_integration import (
    BATCH_RESPONSE_VERSION_V3,
    BUNDLE_VERSION_V5,
    METHOD_VERSION_V5,
    SemanticIntegrationError,
    build_batch_prompts,
    build_bundle,
    finalize_v3_view,
    materialize_source_v3,
    validate_batch_responses,
    verify_bundle_context,
)


CALIBRATION_SPEC_VERSION_V1 = "semantic_calibration_spec_v1"
CALIBRATION_SPEC_VERSION_V2 = "semantic_calibration_spec_v2"
CALIBRATION_SPEC_VERSION = "semantic_calibration_spec_v3"
CALIBRATION_ADJUDICATION_VERSION_V1 = "semantic_calibration_adjudication_v1"
CALIBRATION_ADJUDICATION_VERSION_V2 = "semantic_calibration_adjudication_v2"
CALIBRATION_ADJUDICATION_VERSION = "semantic_calibration_adjudication_v3"
CALIBRATION_PREPARATION_VERSION = "semantic_calibration_preparation_v1"
CALIBRATION_REPORT_VERSION = "semantic_calibration_report_v1"

SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT = """# Semantic Calibration Adjudication Contract

Contract version: `semantic_calibration_adjudication_contract_v1`

`statement_direction_supported` asks whether the source supports the semantic
unit's complete truth-conditional direction and whether `polarity` matches the
logical form written in `statement`. It is not a sentiment or lower-is-negative
judgment.

- An affirmative comparison remains `polarity: affirmed` even when it uses
  `less`, `lower`, or another downward comparison. For example,
  `A is less moisturising than B` is an affirmed ordering claim.
- A statement with logical negation such as “A is not as moisturising as B”,
  “never repurchases”, or “does not dry the lips” is `polarity: negated`.
- Comparative direction is carried by the complete statement plus its subject
  and comparator roles. Mark the judgment false when the unit reverses that
  ordering, swaps the products, drops a comparison or negation, or assigns a
  polarity that conflicts with the written statement.
- Do not mark an otherwise supported unit false merely because its asserted
  comparison is unfavorable, lower, or contains the word `less`.

Apply this contract to every semantic unit in each gold case, including units
left explicitly unmerged.
"""

_LIST_UNIT_FIELDS = {
    "subject_product_ids",
    "comparator_product_ids",
    "axis_ids",
    "product_version_ids",
    "conditions",
}
_SCALAR_UNIT_FIELDS = {
    "evidence_posture",
    "uncertainty_posture",
    "polarity",
}
_UNIT_FIELDS = _LIST_UNIT_FIELDS | _SCALAR_UNIT_FIELDS
_FORBIDDEN_GOLD_KEY_PREFIXES = (
    "actual_",
    "machine_",
    "observed_",
    "predicted_",
    "response_",
)
# Every gold container is a closed key set.  A misspelled obligation key would
# otherwise fall through `.get(..., default)` and silently delete that
# obligation from the gate while the report still reads as a pass.
_SPEC_FIELDS = {
    "schema_version",
    "full_source_sha256",
    "method_version",
    "route_contract",
    "slices",
    "relation_obligations",
    "cold_repeat_case_ids",
    "cold_repeat",
    "required_adjudication_version",
    "spec_sha256",
}
_SLICE_FIELDS = {
    "slice_id",
    "purpose",
    "evidence_ids",
    "max_prompt_bytes",
    "max_evidence_per_work_unit",
    "minimum_largest_prompt_bytes",
    "axis_repetition_warning",
    "semantic_unit_density_audit",
    "cases",
}
_CASE_FIELDS = {
    "case_id",
    "evidence_id",
    "archetype",
    "critical",
    "expected_disposition",
    "min_semantic_units",
    "max_semantic_units",
    "required_atoms",
    "forbidden_values",
    "allow_unmatched_units",
}
_ATOM_FIELDS = {"atom_id", "meaning", "expected_fields"}
_RELATION_FIELDS = {"relation_id", "relation_type", "case_ids", "critical", "meaning"}
_COLD_REPEAT_FIELDS = {
    "max_prompt_bytes",
    "max_evidence_per_work_unit",
    "minimum_largest_prompt_bytes",
}
_AXIS_REPETITION_FIELDS = {"minimum_axis_count", "minimum_repeated_units"}
_SEMANTIC_UNIT_DENSITY_AUDIT_FIELDS = {"top_non_gold_rows"}
_SEMANTIC_UNIT_DENSITY_CHECK_FIELDS = {
    "all_units_source_supported",
    "all_units_independently_meaningful",
    "no_duplicate_or_redundant_units",
    "split_granularity_supported",
}
_AXIS_SUPPORT_FIELDS_V2 = {"supported_axis_ids", "unsupported_axis_ids"}
_AXIS_SUPPORT_FIELDS = _AXIS_SUPPORT_FIELDS_V2 | {"statement_direction_supported"}
# The route fields that have an observable in-process counterpart.  Runner
# revision and contract version are operator-declared provenance with nothing
# to check them against, so they are deliberately absent here.
_ROUTE_CONTRACT_VERIFIED_FIELDS = (
    "method_sha256",
    "bundle_schema_version",
    "response_schema_version",
    "prompt_encoding_version",
    "axes_sha256",
    "product_identity_catalog_sha256",
)


class SemanticCalibrationError(ValueError):
    """Raised when calibration inputs cannot support an honest result."""


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    # helper-delta: canonical JSON encoding before shared byte hashing.
    return sha256_bytes(_json_bytes(value))


def _without_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _verify_hash(value: Mapping[str, Any], *, field: str, label: str) -> None:
    observed = value.get(field)
    if not isinstance(observed, str) or observed != _sha256(_without_hash(value, field)):
        raise SemanticCalibrationError(f"{label} has stale or missing {field}")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unique_strings(value: Any, *, label: str, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not _nonempty(item) for item in value)
        or len(value) != len(set(value))
    ):
        raise SemanticCalibrationError(f"{label} must be a unique string list")
    return list(value)


def _reject_unknown_fields(
    value: Mapping[str, Any], allowed: set[str], *, label: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise SemanticCalibrationError(f"{label} has unknown gold fields: {unknown}")


def _reject_machine_output_fields(value: Any, *, path: str = "spec") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str) and key.startswith(_FORBIDDEN_GOLD_KEY_PREFIXES):
                raise SemanticCalibrationError(
                    f"blind calibration spec contains machine-output field: {path}.{key}"
                )
            _reject_machine_output_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_machine_output_fields(item, path=f"{path}[{index}]")


def _validate_expected_fields(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SemanticCalibrationError(f"{label} expected_fields must be an object")
    unknown = set(value) - _UNIT_FIELDS
    if unknown:
        raise SemanticCalibrationError(f"{label} has unknown expected fields: {sorted(unknown)}")
    normalized: dict[str, Any] = {}
    for field, expected in value.items():
        if field in _LIST_UNIT_FIELDS:
            normalized[field] = _unique_strings(
                expected, label=f"{label}.{field}", allow_empty=True
            )
        elif isinstance(expected, str):
            if not _nonempty(expected):
                raise SemanticCalibrationError(f"{label}.{field} cannot be blank")
            normalized[field] = expected
        elif isinstance(expected, list):
            normalized[field] = _unique_strings(
                expected, label=f"{label}.{field}", allow_empty=False
            )
        else:
            raise SemanticCalibrationError(
                f"{label}.{field} must be a string or allowed-value list"
            )
    return normalized


def validate_calibration_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate blind owner gold without reading any response artifact."""
    if (
        not isinstance(spec, Mapping)
        or spec.get("schema_version")
        not in {
            CALIBRATION_SPEC_VERSION_V1,
            CALIBRATION_SPEC_VERSION_V2,
            CALIBRATION_SPEC_VERSION,
        }
    ):
        raise SemanticCalibrationError("invalid semantic calibration spec version")
    _verify_hash(spec, field="spec_sha256", label="semantic calibration spec")
    blind_content = _without_hash(spec, "spec_sha256")
    blind_content.pop("route_contract", None)
    _reject_machine_output_fields(blind_content)
    spec_fields = (
        _SPEC_FIELDS - {"required_adjudication_version"}
        if spec.get("schema_version") == CALIBRATION_SPEC_VERSION_V1
        else _SPEC_FIELDS
    )
    _reject_unknown_fields(spec, spec_fields, label="calibration spec")
    if (
        spec.get("schema_version") != CALIBRATION_SPEC_VERSION_V1
        and spec.get("required_adjudication_version")
        != CALIBRATION_ADJUDICATION_VERSION
    ):
        raise SemanticCalibrationError(
            "current calibration specs must require the current adjudication version"
        )
    if not _nonempty(spec.get("full_source_sha256")):
        raise SemanticCalibrationError("calibration spec lacks full_source_sha256")
    if spec.get("method_version") != METHOD_VERSION_V5:
        raise SemanticCalibrationError("calibration spec must target semantic method v5")
    route_contract = spec.get("route_contract")
    required_route_fields = {
        "runner_revision",
        "contract_version",
        "method_sha256",
        "bundle_schema_version",
        "response_schema_version",
        "prompt_encoding_version",
        "axes_sha256",
        "product_identity_catalog_sha256",
    }
    if not isinstance(route_contract, Mapping) or set(route_contract) != required_route_fields:
        raise SemanticCalibrationError("calibration spec has invalid route_contract")
    for field in required_route_fields - {"product_identity_catalog_sha256"}:
        if not _nonempty(route_contract.get(field)):
            raise SemanticCalibrationError(f"route_contract lacks {field}")
    catalog_sha = route_contract.get("product_identity_catalog_sha256")
    if catalog_sha is not None and not _nonempty(catalog_sha):
        raise SemanticCalibrationError("route_contract has invalid catalog hash")

    slices = spec.get("slices")
    if not isinstance(slices, list) or not slices:
        raise SemanticCalibrationError("calibration spec requires slices")
    seen_slices: set[str] = set()
    seen_cases: set[str] = set()
    evidence_to_slice: dict[str, str] = {}
    normalized_slices: list[dict[str, Any]] = []
    for raw_slice in slices:
        if not isinstance(raw_slice, Mapping) or not _nonempty(raw_slice.get("slice_id")):
            raise SemanticCalibrationError("calibration slice lacks slice_id")
        slice_id = raw_slice["slice_id"]
        if slice_id in seen_slices:
            raise SemanticCalibrationError(f"duplicate calibration slice: {slice_id}")
        seen_slices.add(slice_id)
        _reject_unknown_fields(raw_slice, _SLICE_FIELDS, label=f"slice {slice_id}")
        evidence_ids = _unique_strings(
            raw_slice.get("evidence_ids"), label=f"slice {slice_id} evidence_ids"
        )
        overlap = set(evidence_ids) & set(evidence_to_slice)
        if overlap:
            raise SemanticCalibrationError(
                f"calibration evidence appears in multiple slices: {sorted(overlap)}"
            )
        evidence_to_slice.update({evidence_id: slice_id for evidence_id in evidence_ids})
        max_prompt_bytes = raw_slice.get("max_prompt_bytes")
        max_evidence = raw_slice.get("max_evidence_per_work_unit")
        if not isinstance(max_prompt_bytes, int) or max_prompt_bytes < 1_000:
            raise SemanticCalibrationError(f"slice {slice_id} has invalid max_prompt_bytes")
        if not isinstance(max_evidence, int) or max_evidence < 1:
            raise SemanticCalibrationError(
                f"slice {slice_id} has invalid max_evidence_per_work_unit"
            )
        min_prompt_bytes = raw_slice.get("minimum_largest_prompt_bytes", 0)
        if not isinstance(min_prompt_bytes, int) or min_prompt_bytes < 0:
            raise SemanticCalibrationError(
                f"slice {slice_id} has invalid minimum_largest_prompt_bytes"
            )
        cases = raw_slice.get("cases", [])
        if not isinstance(cases, list):
            raise SemanticCalibrationError(f"slice {slice_id} cases must be a list")
        normalized_cases: list[dict[str, Any]] = []
        case_evidence: set[str] = set()
        for raw_case in cases:
            if not isinstance(raw_case, Mapping):
                raise SemanticCalibrationError(f"slice {slice_id} has invalid case")
            case_id = raw_case.get("case_id")
            evidence_id = raw_case.get("evidence_id")
            disposition = raw_case.get("expected_disposition")
            if not _nonempty(case_id) or case_id in seen_cases:
                raise SemanticCalibrationError(f"duplicate or missing case_id: {case_id}")
            _reject_unknown_fields(raw_case, _CASE_FIELDS, label=f"case {case_id}")
            if evidence_id not in evidence_ids or evidence_id in case_evidence:
                raise SemanticCalibrationError(
                    f"case {case_id} has missing, duplicate, or off-slice evidence_id"
                )
            if disposition not in {
                "claim_bearing",
                "context_only",
                "out_of_scope",
                "unresolved",
            }:
                raise SemanticCalibrationError(f"case {case_id} has invalid disposition")
            min_units = raw_case.get("min_semantic_units")
            max_units = raw_case.get("max_semantic_units")
            if (
                not isinstance(min_units, int)
                or not isinstance(max_units, int)
                or min_units < 0
                or max_units < min_units
            ):
                raise SemanticCalibrationError(f"case {case_id} has invalid unit bounds")
            atoms = raw_case.get("required_atoms", [])
            if not isinstance(atoms, list):
                raise SemanticCalibrationError(f"case {case_id} required_atoms must be a list")
            atom_ids: set[str] = set()
            normalized_atoms: list[dict[str, Any]] = []
            for atom in atoms:
                if not isinstance(atom, Mapping) or not _nonempty(atom.get("atom_id")):
                    raise SemanticCalibrationError(f"case {case_id} has invalid atom")
                atom_id = atom["atom_id"]
                if atom_id in atom_ids or not _nonempty(atom.get("meaning")):
                    raise SemanticCalibrationError(f"case {case_id} has duplicate or empty atom")
                atom_ids.add(atom_id)
                _reject_unknown_fields(
                    atom, _ATOM_FIELDS, label=f"case {case_id} atom {atom_id}"
                )
                normalized_atoms.append(
                    {
                        "atom_id": atom_id,
                        "meaning": atom["meaning"].strip(),
                        "expected_fields": _validate_expected_fields(
                            atom.get("expected_fields", {}),
                            label=f"case {case_id} atom {atom_id}",
                        ),
                    }
                )
            if disposition == "claim_bearing" and not normalized_atoms:
                raise SemanticCalibrationError(
                    f"claim-bearing case {case_id} requires at least one atomic meaning"
                )
            if disposition != "claim_bearing" and (min_units or max_units or atoms):
                raise SemanticCalibrationError(
                    f"non-claim case {case_id} cannot require semantic units"
                )
            forbidden = raw_case.get("forbidden_values", {})
            normalized_forbidden = _validate_expected_fields(
                forbidden, label=f"case {case_id} forbidden_values"
            )
            normalized_cases.append(
                {
                    "case_id": case_id,
                    "evidence_id": evidence_id,
                    "archetype": str(raw_case.get("archetype", "")).strip(),
                    "critical": raw_case.get("critical", True) is not False,
                    "expected_disposition": disposition,
                    "min_semantic_units": min_units,
                    "max_semantic_units": max_units,
                    "required_atoms": normalized_atoms,
                    "forbidden_values": normalized_forbidden,
                    "allow_unmatched_units": raw_case.get("allow_unmatched_units", False)
                    is True,
                }
            )
            case_evidence.add(evidence_id)
            seen_cases.add(case_id)
        anomaly = raw_slice.get("axis_repetition_warning")
        if anomaly is not None:
            if (
                not isinstance(anomaly, Mapping)
                or not isinstance(anomaly.get("minimum_axis_count"), int)
                or anomaly["minimum_axis_count"] < 1
                or not isinstance(anomaly.get("minimum_repeated_units"), int)
                or anomaly["minimum_repeated_units"] < 2
            ):
                raise SemanticCalibrationError(
                    f"slice {slice_id} has invalid axis_repetition_warning"
                )
            _reject_unknown_fields(
                anomaly,
                _AXIS_REPETITION_FIELDS,
                label=f"slice {slice_id} axis_repetition_warning",
            )
            anomaly = dict(anomaly)
        density_audit = raw_slice.get("semantic_unit_density_audit")
        if density_audit is not None:
            if spec.get("schema_version") != CALIBRATION_SPEC_VERSION:
                raise SemanticCalibrationError(
                    "semantic_unit_density_audit requires calibration spec v3"
                )
            if (
                not isinstance(density_audit, Mapping)
                or not isinstance(density_audit.get("top_non_gold_rows"), int)
                or density_audit["top_non_gold_rows"] < 1
            ):
                raise SemanticCalibrationError(
                    f"slice {slice_id} has invalid semantic_unit_density_audit"
                )
            _reject_unknown_fields(
                density_audit,
                _SEMANTIC_UNIT_DENSITY_AUDIT_FIELDS,
                label=f"slice {slice_id} semantic_unit_density_audit",
            )
            density_audit = dict(density_audit)
        normalized_slices.append(
            {
                "slice_id": slice_id,
                "purpose": str(raw_slice.get("purpose", "")).strip(),
                "evidence_ids": evidence_ids,
                "max_prompt_bytes": max_prompt_bytes,
                "max_evidence_per_work_unit": max_evidence,
                "minimum_largest_prompt_bytes": min_prompt_bytes,
                "cases": normalized_cases,
                "axis_repetition_warning": anomaly,
                "semantic_unit_density_audit": density_audit,
            }
        )

    if not seen_cases:
        raise SemanticCalibrationError("calibration spec requires at least one case")

    relations = spec.get("relation_obligations", [])
    if not isinstance(relations, list):
        raise SemanticCalibrationError("relation_obligations must be a list")
    seen_relations: set[str] = set()
    normalized_relations: list[dict[str, Any]] = []
    allowed_relations = {
        "must_co_retrieve",
        "must_merge",
        "must_not_merge",
        "counterevidence_retained",
        "independent_origin_preserved",
        "engagement_not_promoted",
        "meaning_direction_preserved",
    }
    for relation in relations:
        if not isinstance(relation, Mapping) or not _nonempty(relation.get("relation_id")):
            raise SemanticCalibrationError("invalid relation obligation")
        relation_id = relation["relation_id"]
        if relation_id in seen_relations or relation.get("relation_type") not in allowed_relations:
            raise SemanticCalibrationError(f"invalid or duplicate relation: {relation_id}")
        _reject_unknown_fields(
            relation, _RELATION_FIELDS, label=f"relation {relation_id}"
        )
        case_ids = _unique_strings(
            relation.get("case_ids"), label=f"relation {relation_id} case_ids"
        )
        if not set(case_ids) <= seen_cases:
            raise SemanticCalibrationError(f"relation {relation_id} cites unknown cases")
        normalized_relations.append(
            {
                "relation_id": relation_id,
                "relation_type": relation["relation_type"],
                "case_ids": case_ids,
                "critical": relation.get("critical", True) is not False,
                "meaning": str(relation.get("meaning", "")).strip(),
            }
        )
        seen_relations.add(relation_id)

    repeat_cases = _unique_strings(
        spec.get("cold_repeat_case_ids", []),
        label="cold_repeat_case_ids",
        allow_empty=True,
    )
    if not set(repeat_cases) <= seen_cases:
        raise SemanticCalibrationError("cold_repeat_case_ids cites unknown cases")
    cold_repeat = spec.get("cold_repeat")
    if repeat_cases:
        if not isinstance(cold_repeat, Mapping):
            raise SemanticCalibrationError("cold repeats require cold_repeat route bounds")
        _reject_unknown_fields(cold_repeat, _COLD_REPEAT_FIELDS, label="cold_repeat")
        cold_max_prompt = cold_repeat.get("max_prompt_bytes")
        cold_max_evidence = cold_repeat.get("max_evidence_per_work_unit")
        cold_min_prompt = cold_repeat.get("minimum_largest_prompt_bytes", 0)
        if not isinstance(cold_max_prompt, int) or cold_max_prompt < 1_000:
            raise SemanticCalibrationError("cold_repeat has invalid max_prompt_bytes")
        if not isinstance(cold_max_evidence, int) or cold_max_evidence < 1:
            raise SemanticCalibrationError(
                "cold_repeat has invalid max_evidence_per_work_unit"
            )
        if not isinstance(cold_min_prompt, int) or cold_min_prompt < 0:
            raise SemanticCalibrationError(
                "cold_repeat has invalid minimum_largest_prompt_bytes"
            )
        normalized_cold_repeat: dict[str, Any] | None = {
            "max_prompt_bytes": cold_max_prompt,
            "max_evidence_per_work_unit": cold_max_evidence,
            "minimum_largest_prompt_bytes": cold_min_prompt,
        }
    else:
        if cold_repeat is not None:
            raise SemanticCalibrationError(
                "cold_repeat route bounds require cold_repeat_case_ids"
            )
        normalized_cold_repeat = None
    return {
        **_without_hash(spec, "spec_sha256"),
        "slices": normalized_slices,
        "relation_obligations": normalized_relations,
        "cold_repeat_case_ids": repeat_cases,
        "cold_repeat": normalized_cold_repeat,
        "spec_sha256": spec["spec_sha256"],
    }


def _verify_full_source(source: Mapping[str, Any], expected_sha256: str) -> None:
    if source.get("source_sha256") != expected_sha256:
        raise SemanticCalibrationError("calibration source hash does not match spec")
    if _sha256(_without_hash(source, "source_sha256")) != expected_sha256:
        raise SemanticCalibrationError("calibration source carries a stale source_sha256")


def build_calibration_source(
    full_source: Mapping[str, Any], *, slice_id: str, evidence_ids: Sequence[str]
) -> dict[str, Any]:
    """Project one exact bounded slice without mutating the full source."""
    selected_ids = list(evidence_ids)
    if len(selected_ids) != len(set(selected_ids)):
        raise SemanticCalibrationError("calibration source selection duplicates evidence ids")
    captured = full_source.get("captured_items")
    containers = full_source.get("containers")
    if not isinstance(captured, list) or not isinstance(containers, list):
        raise SemanticCalibrationError("calibration requires semantic source v3")
    by_id = {
        row.get("evidence_id"): row
        for row in captured
        if isinstance(row, Mapping) and _nonempty(row.get("evidence_id"))
    }
    missing = set(selected_ids) - set(by_id)
    if missing:
        raise SemanticCalibrationError(f"calibration selection is missing: {sorted(missing)}")
    selected = [deepcopy(by_id[evidence_id]) for evidence_id in selected_ids]
    not_assessable = [
        row["evidence_id"]
        for row in selected
        if row.get("accounting_disposition") != "assess"
    ]
    if not_assessable:
        raise SemanticCalibrationError(
            f"calibration selection contains non-assessable evidence: {not_assessable}"
        )
    container_counts = Counter(row.get("container_id") for row in selected)
    container_by_id = {
        row.get("container_id"): row
        for row in containers
        if isinstance(row, Mapping) and _nonempty(row.get("container_id"))
    }
    if not set(container_counts) <= set(container_by_id):
        raise SemanticCalibrationError("calibration selection cites missing container")
    selected_containers: list[dict[str, Any]] = []
    for container_id in sorted(container_counts):
        row = deepcopy(container_by_id[container_id])
        row["captured_leaf_count"] = container_counts[container_id]
        selected_containers.append(row)
    projected = deepcopy(dict(full_source))
    projected.pop("source_sha256", None)
    projected["semantic_method_version"] = METHOD_VERSION_V5
    projected["corpus_profile"] = "bounded_regression_slice"
    projected["corpus_scope"] = (
        f"{full_source.get('corpus_scope', 'customer evidence')} | "
        f"semantic calibration slice {slice_id}"
    )
    projected["containers"] = selected_containers
    projected["captured_items"] = selected
    return materialize_source_v3(projected)


def route_fingerprint(
    bundle: Mapping[str, Any], *, route_contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    context = verify_bundle_context(bundle)
    projection = bundle.get("semantic_work_unit_projection")
    identity = projection.get("semantic_execution_identity") if isinstance(projection, Mapping) else None
    if not isinstance(identity, Mapping):
        raise SemanticCalibrationError("calibration bundle lacks semantic execution identity")
    axes = bundle.get("axes")
    fingerprint = {
        "bundle_schema_version": bundle.get("schema_version"),
        "method_version": bundle.get("method_version"),
        "method_sha256": bundle.get("method_sha256"),
        "response_schema_version": identity.get("response_schema_version"),
        "compilation_schema_version": identity.get("compilation_schema_version"),
        "prompt_encoding_version": identity.get("prompt_encoding_version"),
        "product_identity_catalog_sha256": identity.get(
            "product_identity_catalog_sha256"
        ),
        "axes_sha256": _sha256(axes),
        "max_prompt_bytes": projection.get("max_prompt_bytes"),
        "max_evidence_per_work_unit": projection.get(
            "max_evidence_per_work_unit"
        ),
        "bundle_sha256": context["bundle_sha256"],
    }
    if route_contract is not None:
        fingerprint["runner_revision"] = route_contract.get("runner_revision")
        fingerprint["contract_version"] = route_contract.get("contract_version")
    return fingerprint


def _projected_evidence_ids(bundle: Mapping[str, Any]) -> list[str]:
    return [
        evidence_id
        for work_unit in bundle["semantic_work_unit_projection"]["work_units"]
        for evidence_id in work_unit["evidence_ids"]
    ]


def prepare_semantic_calibration(
    full_source: Mapping[str, Any], spec: Mapping[str, Any]
) -> dict[str, Any]:
    normalized = validate_calibration_spec(spec)
    _verify_full_source(full_source, normalized["full_source_sha256"])
    prepared_slices: list[dict[str, Any]] = []
    for slice_spec in normalized["slices"]:
        source = build_calibration_source(
            full_source,
            slice_id=slice_spec["slice_id"],
            evidence_ids=slice_spec["evidence_ids"],
        )
        bundle = build_bundle(
            source,
            max_prompt_bytes=slice_spec["max_prompt_bytes"],
            max_evidence_per_work_unit=slice_spec["max_evidence_per_work_unit"],
        )
        if bundle.get("schema_version") != BUNDLE_VERSION_V5:
            raise SemanticCalibrationError("calibration did not produce bundle v5")
        prompts = build_batch_prompts(bundle)
        largest_prompt = max((row["prompt_utf8_bytes"] for row in prompts), default=0)
        if largest_prompt < slice_spec["minimum_largest_prompt_bytes"]:
            raise SemanticCalibrationError(
                f"slice {slice_spec['slice_id']} did not reach its production-shape floor"
            )
        projected_ids = _projected_evidence_ids(bundle)
        if sorted(projected_ids) != sorted(slice_spec["evidence_ids"]):
            raise SemanticCalibrationError(
                f"slice {slice_spec['slice_id']} projection changed selected evidence"
            )
        fingerprint = route_fingerprint(bundle, route_contract=normalized["route_contract"])
        expected_route = normalized["route_contract"]
        for field in _ROUTE_CONTRACT_VERIFIED_FIELDS:
            if fingerprint.get(field) != expected_route.get(field):
                raise SemanticCalibrationError(
                    f"slice {slice_spec['slice_id']} route contract mismatch: {field}"
                )
        prepared_slices.append(
            {
                "slice_id": slice_spec["slice_id"],
                "source": source,
                "bundle": bundle,
                "prompts": prompts,
                "route_fingerprint": fingerprint,
                "largest_prompt_bytes": largest_prompt,
            }
        )
    prepared_cold_repeat: dict[str, Any] | None = None
    if normalized["cold_repeat_case_ids"]:
        case_to_evidence = {
            case["case_id"]: case["evidence_id"]
            for slice_spec in normalized["slices"]
            for case in slice_spec["cases"]
        }
        cold_evidence_ids = list(
            dict.fromkeys(
                case_to_evidence[case_id]
                for case_id in normalized["cold_repeat_case_ids"]
            )
        )
        cold_bounds = normalized["cold_repeat"]
        cold_source = build_calibration_source(
            full_source, slice_id="cold-repeat", evidence_ids=cold_evidence_ids
        )
        cold_bundle = build_bundle(
            cold_source,
            max_prompt_bytes=cold_bounds["max_prompt_bytes"],
            max_evidence_per_work_unit=cold_bounds[
                "max_evidence_per_work_unit"
            ],
        )
        cold_prompts = build_batch_prompts(cold_bundle)
        cold_largest_prompt = max(
            (row["prompt_utf8_bytes"] for row in cold_prompts), default=0
        )
        if cold_largest_prompt < cold_bounds["minimum_largest_prompt_bytes"]:
            raise SemanticCalibrationError(
                "cold-repeat slice did not reach its declared prompt floor"
            )
        cold_fingerprint = route_fingerprint(
            cold_bundle, route_contract=normalized["route_contract"]
        )
        for field in _ROUTE_CONTRACT_VERIFIED_FIELDS:
            if cold_fingerprint.get(field) != normalized["route_contract"].get(field):
                raise SemanticCalibrationError(
                    f"cold-repeat route contract mismatch: {field}"
                )
        prepared_cold_repeat = {
            "slice_id": "cold-repeat",
            "source": cold_source,
            "bundle": cold_bundle,
            "prompts": cold_prompts,
            "route_fingerprint": cold_fingerprint,
            "largest_prompt_bytes": cold_largest_prompt,
        }
    receipt = {
        "schema_version": CALIBRATION_PREPARATION_VERSION,
        "spec_sha256": normalized["spec_sha256"],
        "full_source_sha256": normalized["full_source_sha256"],
        "slices": [
            {
                "slice_id": row["slice_id"],
                "source_sha256": row["source"]["source_sha256"],
                "bundle_sha256": row["bundle"]["bundle_sha256"],
                "work_unit_count": len(row["bundle"]["batches"]),
                "evidence_count": len(row["bundle"]["evidence_units"]),
                "largest_prompt_bytes": row["largest_prompt_bytes"],
                "route_fingerprint": row["route_fingerprint"],
            }
            for row in prepared_slices
        ],
        "cold_repeat": (
            None
            if prepared_cold_repeat is None
            else {
                "source_sha256": prepared_cold_repeat["source"]["source_sha256"],
                "bundle_sha256": prepared_cold_repeat["bundle"]["bundle_sha256"],
                "work_unit_count": len(prepared_cold_repeat["bundle"]["batches"]),
                "evidence_count": len(
                    prepared_cold_repeat["bundle"]["evidence_units"]
                ),
                "largest_prompt_bytes": prepared_cold_repeat[
                    "largest_prompt_bytes"
                ],
                "route_fingerprint": prepared_cold_repeat["route_fingerprint"],
            }
        ),
        "non_claims": [
            "bounded calibration only",
            "not corpus prevalence",
            "not full-corpus execution",
            "not readiness",
        ],
    }
    receipt["preparation_sha256"] = _sha256(receipt)
    return {
        "receipt": receipt,
        "slices": prepared_slices,
        "cold_repeat": prepared_cold_repeat,
    }


def validate_calibration_adjudication(
    adjudication: Mapping[str, Any], *, spec_sha256: str
) -> dict[str, Any]:
    if (
        not isinstance(adjudication, Mapping)
        or adjudication.get("schema_version")
        not in {
            CALIBRATION_ADJUDICATION_VERSION_V1,
            CALIBRATION_ADJUDICATION_VERSION_V2,
            CALIBRATION_ADJUDICATION_VERSION,
        }
    ):
        raise SemanticCalibrationError("invalid calibration adjudication version")
    _verify_hash(
        adjudication,
        field="adjudication_sha256",
        label="semantic calibration adjudication",
    )
    if adjudication.get("spec_sha256") != spec_sha256:
        raise SemanticCalibrationError("adjudication targets another calibration spec")
    if not _nonempty(adjudication.get("adjudicator")):
        raise SemanticCalibrationError("adjudication lacks adjudicator provenance")
    for field, id_field in (
        ("case_adjudications", "case_id"),
        ("relation_adjudications", "relation_id"),
        ("cold_repeat_adjudications", "case_id"),
        ("warning_adjudications", "warning_id"),
    ):
        rows = adjudication.get(field, [])
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
            raise SemanticCalibrationError(f"adjudication {field} must be an object list")
        ids = [row.get(id_field) for row in rows]
        if any(not _nonempty(value) for value in ids) or len(ids) != len(set(ids)):
            raise SemanticCalibrationError(
                f"adjudication {field} has missing or duplicate {id_field}"
            )
    return dict(adjudication)


def _unit_matches_fields(unit: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    for field, wanted in expected.items():
        actual = unit.get(field)
        if field in _LIST_UNIT_FIELDS:
            if not isinstance(actual, list) or not set(wanted) <= set(actual):
                return False
        elif isinstance(wanted, list):
            if actual not in wanted:
                return False
        elif actual != wanted:
            return False
    return True


def _forbidden_values(unit: Mapping[str, Any], forbidden: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    for field, values in forbidden.items():
        actual = unit.get(field)
        if field in _LIST_UNIT_FIELDS:
            overlap = set(actual or []) & set(values)
            if overlap:
                violations.append(f"{field}={sorted(overlap)}")
        elif isinstance(values, list) and actual in values:
            violations.append(f"{field}={actual}")
        elif actual == values:
            violations.append(f"{field}={actual}")
    return violations


def _response_rows(
    bundle: Mapping[str, Any], responses: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Any]]:
    compiled = validate_batch_responses(bundle, responses)
    disposition_by_id = {
        row["evidence_id"]: row for row in compiled["evidence_dispositions"]
    }
    units_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in compiled["semantic_units"]:
        units_by_id[unit["evidence_id"]].append(unit)
    rows = {
        evidence_id: {
            **disposition,
            "semantic_units": units_by_id.get(evidence_id, []),
        }
        for evidence_id, disposition in disposition_by_id.items()
    }
    return rows, compiled


def evaluate_semantic_calibration(
    prepared: Mapping[str, Any],
    spec: Mapping[str, Any],
    responses_by_slice: Mapping[str, Sequence[Mapping[str, Any]]],
    adjudication: Mapping[str, Any] | None,
    cold_responses_by_slice: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    reconciliation_by_slice: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    full_source: Mapping[str, Any],
) -> dict[str, Any]:
    """Combine deterministic gates with explicit semantic adjudication."""
    normalized = validate_calibration_spec(spec)
    _verify_full_source(full_source, normalized["full_source_sha256"])
    expected_prepared = prepare_semantic_calibration(full_source, spec)
    expected_prepared_slices = {
        row["slice_id"]: row for row in expected_prepared["slices"]
    }
    receipt = prepared.get("receipt") if isinstance(prepared, Mapping) else None
    if not isinstance(receipt, Mapping) or receipt.get("spec_sha256") != normalized["spec_sha256"]:
        raise SemanticCalibrationError("prepared calibration does not match spec")
    _verify_hash(
        receipt,
        field="preparation_sha256",
        label="semantic calibration preparation",
    )
    if receipt.get("full_source_sha256") != normalized["full_source_sha256"]:
        raise SemanticCalibrationError("prepared calibration cites another full source")
    prepared_slices = {
        row["slice_id"]: row
        for row in prepared.get("slices", [])
        if isinstance(row, Mapping) and _nonempty(row.get("slice_id"))
    }
    expected_slice_ids = {row["slice_id"] for row in normalized["slices"]}
    if set(prepared_slices) != expected_slice_ids:
        raise SemanticCalibrationError("prepared calibration slice set does not match spec")
    if set(responses_by_slice) - expected_slice_ids:
        raise SemanticCalibrationError("responses contain an unknown calibration slice")
    receipt_slices = {
        row.get("slice_id"): row
        for row in receipt.get("slices", [])
        if isinstance(row, Mapping) and _nonempty(row.get("slice_id"))
    }
    if set(receipt_slices) != expected_slice_ids:
        raise SemanticCalibrationError("preparation receipt slice set does not match spec")
    adjudicated = (
        None
        if adjudication is None
        else validate_calibration_adjudication(
            adjudication, spec_sha256=normalized["spec_sha256"]
        )
    )
    case_adjudications = {
        row.get("case_id"): row
        for row in (adjudicated or {}).get("case_adjudications", [])
        if isinstance(row, Mapping) and _nonempty(row.get("case_id"))
    }
    relation_adjudications = {
        row.get("relation_id"): row
        for row in (adjudicated or {}).get("relation_adjudications", [])
        if isinstance(row, Mapping) and _nonempty(row.get("relation_id"))
    }
    cold_adjudications = {
        row.get("case_id"): row
        for row in (adjudicated or {}).get("cold_repeat_adjudications", [])
        if isinstance(row, Mapping) and _nonempty(row.get("case_id"))
    }
    warning_adjudications = {
        row.get("warning_id"): row
        for row in (adjudicated or {}).get("warning_adjudications", [])
        if isinstance(row, Mapping) and _nonempty(row.get("warning_id"))
    }
    if adjudicated is not None:
        expected_case_ids = {
            case["case_id"]
            for slice_spec in normalized["slices"]
            for case in slice_spec["cases"]
        }
        if set(case_adjudications) - expected_case_ids:
            raise SemanticCalibrationError("adjudication cites an unknown calibration case")
        expected_relation_ids = {
            row["relation_id"] for row in normalized["relation_obligations"]
        }
        if set(relation_adjudications) - expected_relation_ids:
            raise SemanticCalibrationError("adjudication cites an unknown relation")
        if set(cold_adjudications) - set(normalized["cold_repeat_case_ids"]):
            raise SemanticCalibrationError("adjudication cites an unknown cold repeat")
        expected_warning_ids = {
            f"repeated-large-axis-signature:{row['slice_id']}"
            for row in normalized["slices"]
            if row.get("axis_repetition_warning") is not None
        }
        for row in normalized["slices"]:
            if row.get("semantic_unit_density_audit") is None:
                continue
            gold_evidence_ids = {case["evidence_id"] for case in row["cases"]}
            expected_warning_ids.update(
                f"semantic-unit-density-audit:{row['slice_id']}:{evidence_id}"
                for evidence_id in row["evidence_ids"]
                if evidence_id not in gold_evidence_ids
            )
        if set(warning_adjudications) - expected_warning_ids:
            raise SemanticCalibrationError("adjudication cites an unknown warning")
    failures: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    required_adjudication_version = normalized.get(
        "required_adjudication_version"
    )
    if required_adjudication_version is not None and (
        adjudicated is None
        or adjudicated.get("schema_version") != required_adjudication_version
    ):
        blockers.append(
            {
                "code": "ADJUDICATION_VERSION_REQUIRED",
                "required_version": required_adjudication_version,
                "observed_version": (
                    None if adjudicated is None else adjudicated.get("schema_version")
                ),
            }
        )
    if receipt != expected_prepared["receipt"]:
        failures.append({"code": "PREPARATION_RECEIPT_MISMATCH"})
    case_results: list[dict[str, Any]] = []
    compiled_by_slice: dict[str, Any] = {}
    cold_compilation: dict[str, Any] | None = None
    case_to_slice = {
        case["case_id"]: slice_spec["slice_id"]
        for slice_spec in normalized["slices"]
        for case in slice_spec["cases"]
    }
    cold_responses = cold_responses_by_slice or {}
    reconciliations = reconciliation_by_slice or {}
    allowed_cold_keys = {"cold-repeat"} if normalized["cold_repeat"] is not None else set()
    if set(cold_responses) - allowed_cold_keys:
        raise SemanticCalibrationError("cold responses contain an unknown calibration slice")
    if set(reconciliations) - expected_slice_ids:
        raise SemanticCalibrationError(
            "reconciliation outputs contain an unknown calibration slice"
        )
    for slice_spec in normalized["slices"]:
        slice_id = slice_spec["slice_id"]
        prepared_slice = prepared_slices.get(slice_id)
        responses = responses_by_slice.get(slice_id)
        if not isinstance(prepared_slice, Mapping) or responses is None:
            blockers.append(
                {"code": "CALIBRATION_SLICE_MISSING", "slice_id": slice_id}
            )
            continue
        bundle = prepared_slice["bundle"]
        receipt_slice = receipt_slices[slice_id]
        source = prepared_slice.get("source")
        expected_slice = expected_prepared_slices[slice_id]
        exact_mismatches = [
            field
            for field in ("source", "bundle", "prompts", "route_fingerprint")
            if prepared_slice.get(field) != expected_slice.get(field)
        ]
        if exact_mismatches:
            failures.append(
                {
                    "code": "PREPARED_SLICE_SPEC_MISMATCH",
                    "slice_id": slice_id,
                    "detail": ", ".join(exact_mismatches),
                }
            )
            continue
        if (
            not isinstance(source, Mapping)
            or source.get("source_sha256") != receipt_slice.get("source_sha256")
            or bundle.get("bundle_sha256") != receipt_slice.get("bundle_sha256")
            or prepared_slice.get("route_fingerprint")
            != receipt_slice.get("route_fingerprint")
        ):
            failures.append(
                {"code": "PREPARED_SLICE_LINEAGE_MISMATCH", "slice_id": slice_id}
            )
            continue
        if route_fingerprint(
            bundle, route_contract=normalized["route_contract"]
        ) != prepared_slice.get("route_fingerprint"):
            failures.append(
                {"code": "ROUTE_FINGERPRINT_MISMATCH", "slice_id": slice_id}
            )
            continue
        try:
            rows, compiled = _response_rows(bundle, responses)
        except SemanticIntegrationError as exc:
            failures.append(
                {
                    "code": "STRUCTURAL_VALIDATION_FAILED",
                    "slice_id": slice_id,
                    "detail": str(exc),
                }
            )
            continue
        compiled_by_slice[slice_id] = compiled
        anomaly = slice_spec.get("axis_repetition_warning")
        if anomaly:
            signatures: Counter[tuple[str, ...]] = Counter(
                tuple(sorted(unit["axis_ids"]))
                for unit in compiled["semantic_units"]
                if len(unit["axis_ids"]) >= anomaly["minimum_axis_count"]
            )
            repeated = [
                {"axis_ids": list(signature), "unit_count": count}
                for signature, count in signatures.items()
                if count >= anomaly["minimum_repeated_units"]
            ]
            if repeated:
                warning_id = f"repeated-large-axis-signature:{slice_id}"
                warning_adjudication = warning_adjudications.get(warning_id)
                warning_outcome = (
                    warning_adjudication.get("outcome")
                    if isinstance(warning_adjudication, Mapping)
                    else None
                )
                warning = {
                    "warning_id": warning_id,
                    "code": "REPEATED_LARGE_AXIS_SIGNATURE",
                    "slice_id": slice_id,
                    "signatures": repeated,
                    "adjudication_outcome": warning_outcome or "missing",
                }
                warnings.append(warning)
                if (
                    not isinstance(warning_adjudication, Mapping)
                    or warning_adjudication.get("compilation_sha256")
                    != compiled["compilation_sha256"]
                    or warning_outcome
                    not in {"reviewed_benign", "reviewed_defect", "unresolved"}
                ):
                    blockers.append(
                        {
                            "code": "WARNING_ADJUDICATION_MISSING_OR_STALE",
                            "warning_id": warning_id,
                        }
                    )
                elif warning_outcome == "reviewed_defect":
                    failures.append(
                        {
                            "code": "SEMANTIC_ANOMALY_CONFIRMED",
                            "warning_id": warning_id,
                            "critical": True,
                        }
                    )
                elif warning_outcome == "unresolved":
                    blockers.append(
                        {
                            "code": "SEMANTIC_ANOMALY_UNRESOLVED",
                            "warning_id": warning_id,
                        }
                    )
        density_audit = slice_spec.get("semantic_unit_density_audit")
        if density_audit:
            gold_evidence_ids = {
                case["evidence_id"] for case in slice_spec["cases"]
            }
            ranked_rows = sorted(
                (
                    (evidence_id, len(row["semantic_units"]))
                    for evidence_id, row in rows.items()
                    if evidence_id not in gold_evidence_ids
                    and row["semantic_units"]
                ),
                key=lambda item: (-item[1], item[0]),
            )[: density_audit["top_non_gold_rows"]]
            for evidence_id, unit_count in ranked_rows:
                warning_id = (
                    f"semantic-unit-density-audit:{slice_id}:{evidence_id}"
                )
                warning_adjudication = warning_adjudications.get(warning_id)
                warning_outcome = (
                    warning_adjudication.get("outcome")
                    if isinstance(warning_adjudication, Mapping)
                    else None
                )
                density_checks = (
                    warning_adjudication.get("checks")
                    if isinstance(warning_adjudication, Mapping)
                    else None
                )
                valid_density_checks = (
                    isinstance(warning_adjudication, Mapping)
                    and set(warning_adjudication)
                    == {
                        "warning_id",
                        "compilation_sha256",
                        "outcome",
                        "checks",
                    }
                    and isinstance(density_checks, Mapping)
                    and set(density_checks)
                    == _SEMANTIC_UNIT_DENSITY_CHECK_FIELDS
                    and all(
                        value is None or isinstance(value, bool)
                        for value in density_checks.values()
                    )
                )
                derived_outcome = None
                if valid_density_checks:
                    if any(value is None for value in density_checks.values()):
                        derived_outcome = "unresolved"
                    elif all(density_checks.values()):
                        derived_outcome = "reviewed_benign"
                    else:
                        derived_outcome = "reviewed_defect"
                warnings.append(
                    {
                        "warning_id": warning_id,
                        "code": "SEMANTIC_UNIT_DENSITY_AUDIT",
                        "slice_id": slice_id,
                        "evidence_id": evidence_id,
                        "semantic_unit_count": unit_count,
                        "adjudication_outcome": warning_outcome or "missing",
                    }
                )
                if (
                    not isinstance(warning_adjudication, Mapping)
                    or warning_adjudication.get("compilation_sha256")
                    != compiled["compilation_sha256"]
                    or not valid_density_checks
                    or warning_outcome != derived_outcome
                ):
                    blockers.append(
                        {
                            "code": "WARNING_ADJUDICATION_MISSING_OR_STALE",
                            "warning_id": warning_id,
                        }
                    )
                elif warning_outcome == "reviewed_defect":
                    failures.append(
                        {
                            "code": "SEMANTIC_ANOMALY_CONFIRMED",
                            "warning_id": warning_id,
                            "critical": True,
                        }
                    )
                elif warning_outcome == "unresolved":
                    blockers.append(
                        {
                            "code": "SEMANTIC_ANOMALY_UNRESOLVED",
                            "warning_id": warning_id,
                        }
                    )
        for case in slice_spec["cases"]:
            row = rows.get(case["evidence_id"])
            case_failures: list[str] = []
            case_blockers: list[str] = []
            if row is None:
                case_failures.append("evidence row missing after structural validation")
                units: list[Mapping[str, Any]] = []
            else:
                units = row["semantic_units"]
                if row["disposition"] != case["expected_disposition"]:
                    case_failures.append(
                        f"expected disposition {case['expected_disposition']}, got {row['disposition']}"
                    )
                if not case["min_semantic_units"] <= len(units) <= case["max_semantic_units"]:
                    case_failures.append(
                        f"semantic unit count {len(units)} outside "
                        f"{case['min_semantic_units']}..{case['max_semantic_units']}"
                    )
                for unit in units:
                    for violation in _forbidden_values(unit, case["forbidden_values"]):
                        case_failures.append(
                            f"unit {unit['semantic_unit_ref']} carries forbidden {violation}"
                        )
            adjudicated_case = case_adjudications.get(case["case_id"])
            if isinstance(adjudicated_case, Mapping) and adjudicated_case.get(
                "compilation_sha256"
            ) != compiled["compilation_sha256"]:
                case_blockers.append("semantic adjudication targets another compilation")
            required_atoms = {atom["atom_id"]: atom for atom in case["required_atoms"]}
            atom_matches = (
                adjudicated_case.get("atom_matches", {})
                if isinstance(adjudicated_case, Mapping)
                else {}
            )
            if required_atoms and not isinstance(atom_matches, Mapping):
                atom_matches = {}
            # Strip the exact evidence prefix rather than splitting on the first
            # `::`, so an evidence id that itself contains `::` cannot rename
            # the key the adjudicator has to cite.
            units_by_key = {
                unit["semantic_unit_ref"].removeprefix(
                    f"{unit['evidence_id']}::"
                ): unit
                for unit in units
            }
            adjudication_version = (
                adjudication.get("schema_version")
                if adjudication is not None
                else None
            )
            if adjudication_version in {
                CALIBRATION_ADJUDICATION_VERSION_V2,
                CALIBRATION_ADJUDICATION_VERSION,
            } and units_by_key:
                axis_support = (
                    adjudicated_case.get("axis_support_by_unit")
                    if isinstance(adjudicated_case, Mapping)
                    else None
                )
                if not isinstance(axis_support, Mapping):
                    case_blockers.append("units lack per-axis semantic adjudication")
                else:
                    judged_keys = set(axis_support)
                    actual_keys = set(units_by_key)
                    if judged_keys != actual_keys:
                        case_blockers.append(
                            "per-axis semantic adjudication keys do not match units: "
                            f"missing={sorted(actual_keys - judged_keys)}, "
                            f"unexpected={sorted(judged_keys - actual_keys)}"
                        )
                    for unit_key in sorted(actual_keys & judged_keys):
                        axis_judgment = axis_support[unit_key]
                        required_fields = (
                            _AXIS_SUPPORT_FIELDS
                            if adjudication_version == CALIBRATION_ADJUDICATION_VERSION
                            else _AXIS_SUPPORT_FIELDS_V2
                        )
                        if (
                            not isinstance(axis_judgment, Mapping)
                            or set(axis_judgment) != required_fields
                        ):
                            case_blockers.append(
                                f"unit {unit_key} has invalid per-axis semantic adjudication"
                            )
                            continue
                        supported = axis_judgment.get("supported_axis_ids")
                        unsupported = axis_judgment.get("unsupported_axis_ids")
                        if (
                            not isinstance(supported, list)
                            or not isinstance(unsupported, list)
                            or any(not _nonempty(axis_id) for axis_id in supported + unsupported)
                            or len(supported) != len(set(supported))
                            or len(unsupported) != len(set(unsupported))
                            or set(supported) & set(unsupported)
                            or set(supported) | set(unsupported)
                            != set(units_by_key[unit_key]["axis_ids"])
                        ):
                            case_blockers.append(
                                f"unit {unit_key} has incomplete per-axis semantic adjudication"
                            )
                            continue
                        if unsupported:
                            case_failures.append(
                                f"unit {unit_key} carries semantically unsupported axes "
                                f"{sorted(unsupported)}"
                            )
                        if adjudication_version == CALIBRATION_ADJUDICATION_VERSION:
                            direction_supported = axis_judgment.get(
                                "statement_direction_supported"
                            )
                            if not isinstance(direction_supported, bool):
                                case_blockers.append(
                                    f"unit {unit_key} lacks a valid semantic direction judgment"
                                )
                            elif not direction_supported:
                                case_failures.append(
                                    f"unit {unit_key} does not preserve its asserted meaning direction"
                                )
            matched_keys: set[str] = set()
            for atom_id, atom in required_atoms.items():
                if not isinstance(atom_matches, Mapping) or atom_id not in atom_matches:
                    case_blockers.append(f"atom {atom_id} lacks semantic adjudication")
                    continue
                unit_key = atom_matches[atom_id]
                if unit_key is None:
                    case_failures.append(
                        f"atom {atom_id} has no equivalent semantic unit"
                    )
                    continue
                if not _nonempty(unit_key):
                    case_blockers.append(
                        f"atom {atom_id} has invalid semantic adjudication"
                    )
                    continue
                unit = units_by_key.get(unit_key)
                if unit is None:
                    case_failures.append(f"atom {atom_id} cites unknown unit key {unit_key}")
                    continue
                if unit_key in matched_keys:
                    case_failures.append(
                        f"atom {atom_id} reuses unit key {unit_key} already matched to another atom"
                    )
                    continue
                matched_keys.add(unit_key)
                if not _unit_matches_fields(unit, atom["expected_fields"]):
                    case_failures.append(
                        f"atom {atom_id} matched a unit with incompatible structured fields"
                    )
            if required_atoms and not case["allow_unmatched_units"]:
                unmatched = set(units_by_key) - matched_keys
                if unmatched:
                    case_blockers.append(
                        f"semantic units lack atom adjudication: {sorted(unmatched)}"
                    )
            result = {
                "case_id": case["case_id"],
                "slice_id": slice_id,
                "evidence_id": case["evidence_id"],
                "status": "fail" if case_failures else "blocked" if case_blockers else "pass",
                "failures": case_failures,
                "blockers": case_blockers,
            }
            case_results.append(result)
            for detail in case_failures:
                failures.append(
                    {
                        "code": "CALIBRATION_CASE_FAILED",
                        "case_id": case["case_id"],
                        "slice_id": slice_id,
                        "critical": case["critical"],
                        "detail": detail,
                    }
                )
            for detail in case_blockers:
                blockers.append(
                    {
                        "code": "SEMANTIC_ADJUDICATION_MISSING",
                        "case_id": case["case_id"],
                        "slice_id": slice_id,
                        "critical": case["critical"],
                        "detail": detail,
                    }
                )

    if normalized["cold_repeat"] is not None:
        prepared_cold = prepared.get("cold_repeat")
        receipt_cold = receipt.get("cold_repeat")
        if not isinstance(prepared_cold, Mapping) or not isinstance(
            receipt_cold, Mapping
        ):
            blockers.append({"code": "COLD_REPEAT_PREPARATION_MISSING"})
        else:
            cold_bundle = prepared_cold.get("bundle")
            cold_source = prepared_cold.get("source")
            expected_cold = expected_prepared["cold_repeat"]
            cold_exact_mismatches = [
                field
                for field in ("source", "bundle", "prompts", "route_fingerprint")
                if not isinstance(expected_cold, Mapping)
                or prepared_cold.get(field) != expected_cold.get(field)
            ]
            if cold_exact_mismatches:
                failures.append(
                    {
                        "code": "COLD_REPEAT_SPEC_MISMATCH",
                        "detail": ", ".join(cold_exact_mismatches),
                    }
                )
            elif (
                not isinstance(cold_bundle, Mapping)
                or not isinstance(cold_source, Mapping)
                or cold_source.get("source_sha256")
                != receipt_cold.get("source_sha256")
                or cold_bundle.get("bundle_sha256")
                != receipt_cold.get("bundle_sha256")
                or prepared_cold.get("route_fingerprint")
                != receipt_cold.get("route_fingerprint")
                or route_fingerprint(
                    cold_bundle, route_contract=normalized["route_contract"]
                )
                != prepared_cold.get("route_fingerprint")
            ):
                failures.append({"code": "COLD_REPEAT_LINEAGE_MISMATCH"})
            else:
                if "cold-repeat" not in cold_responses:
                    blockers.append({"code": "COLD_REPEAT_RESPONSE_MISSING"})
                else:
                    try:
                        _, cold_compilation = _response_rows(
                            cold_bundle, cold_responses["cold-repeat"]
                        )
                    except SemanticIntegrationError as exc:
                        failures.append(
                            {
                                "code": "COLD_STRUCTURAL_VALIDATION_FAILED",
                                "slice_id": "cold-repeat",
                                "detail": str(exc),
                            }
                        )

    reconciled_views: dict[str, Mapping[str, Any]] = {}
    for slice_id, packet in reconciliations.items():
        if not isinstance(packet, Mapping):
            raise SemanticCalibrationError("reconciliation output must be an object")
        prepared_slice = prepared_slices[slice_id]
        compilation = compiled_by_slice.get(slice_id)
        node_compilation = packet.get("node_compilation")
        supplied_view = packet.get("view")
        if compilation is None:
            continue
        if not isinstance(node_compilation, Mapping) or not isinstance(
            supplied_view, Mapping
        ):
            failures.append(
                {"code": "RECONCILIATION_OUTPUT_INVALID", "slice_id": slice_id}
            )
            continue
        try:
            rebuilt_view = finalize_v3_view(
                prepared_slice["bundle"], compilation, node_compilation
            )
        except SemanticIntegrationError as exc:
            failures.append(
                {
                    "code": "RECONCILIATION_VALIDATION_FAILED",
                    "slice_id": slice_id,
                    "detail": str(exc),
                }
            )
            continue
        if rebuilt_view != supplied_view:
            failures.append(
                {"code": "RECONCILIATION_VIEW_MISMATCH", "slice_id": slice_id}
            )
            continue
        reconciled_views[slice_id] = supplied_view

    relation_results: list[dict[str, Any]] = []
    for relation in normalized["relation_obligations"]:
        result = relation_adjudications.get(relation["relation_id"])
        outcome = result.get("outcome") if isinstance(result, Mapping) else None
        relation_slice_ids = {case_to_slice[case_id] for case_id in relation["case_ids"]}
        expected_hashes = {
            slice_id: compiled_by_slice[slice_id]["compilation_sha256"]
            for slice_id in relation_slice_ids
            if slice_id in compiled_by_slice
        }
        expected_view_hashes = {
            slice_id: reconciled_views[slice_id]["view_sha256"]
            for slice_id in relation_slice_ids
            if slice_id in reconciled_views
        }
        if set(expected_view_hashes) != relation_slice_ids:
            blockers.append(
                {
                    "code": "RECONCILIATION_OUTPUT_MISSING",
                    "relation_id": relation["relation_id"],
                    "critical": relation["critical"],
                }
            )
            outcome = "missing"
        if isinstance(result, Mapping) and result.get(
            "compilation_sha256_by_slice"
        ) != expected_hashes:
            blockers.append(
                {
                    "code": "RELATION_ADJUDICATION_STALE",
                    "relation_id": relation["relation_id"],
                    "critical": relation["critical"],
                }
            )
            outcome = "missing"
        if isinstance(result, Mapping) and result.get(
            "view_sha256_by_slice"
        ) != expected_view_hashes:
            blockers.append(
                {
                    "code": "RELATION_VIEW_ADJUDICATION_STALE",
                    "relation_id": relation["relation_id"],
                    "critical": relation["critical"],
                }
            )
            outcome = "missing"
        if outcome not in {"satisfied", "violated", "unresolved"}:
            blockers.append(
                {
                    "code": "RELATION_ADJUDICATION_MISSING",
                    "relation_id": relation["relation_id"],
                    "critical": relation["critical"],
                }
            )
            outcome = "missing"
        elif outcome != "satisfied" and relation["critical"]:
            failures.append(
                {
                    "code": "RELATION_OBLIGATION_FAILED",
                    "relation_id": relation["relation_id"],
                    "outcome": outcome,
                    "critical": True,
                }
            )
        relation_results.append(
            {"relation_id": relation["relation_id"], "outcome": outcome}
        )
    cold_results: list[dict[str, Any]] = []
    for case_id in normalized["cold_repeat_case_ids"]:
        result = cold_adjudications.get(case_id)
        outcome = result.get("outcome") if isinstance(result, Mapping) else None
        slice_id = case_to_slice[case_id]
        primary_compiled = compiled_by_slice.get(slice_id)
        repeat_compiled = cold_compilation
        primary_hash = (
            None if primary_compiled is None else primary_compiled["compilation_sha256"]
        )
        repeat_hash = (
            None if repeat_compiled is None else repeat_compiled["compilation_sha256"]
        )
        if repeat_compiled is None:
            blockers.append(
                {"code": "COLD_REPEAT_RESPONSE_MISSING", "case_id": case_id}
            )
            outcome = "missing"
        elif primary_hash is None:
            # Without a primary compilation there is nothing for the repeat to
            # be consistent with; an omitted primary hash must not read as a
            # matched one.
            blockers.append(
                {
                    "code": "COLD_REPEAT_PRIMARY_COMPILATION_MISSING",
                    "case_id": case_id,
                }
            )
            outcome = "missing"
        elif isinstance(result, Mapping) and (
            result.get("primary_compilation_sha256") != primary_hash
            or result.get("repeat_compilation_sha256") != repeat_hash
        ):
            blockers.append(
                {"code": "COLD_REPEAT_ADJUDICATION_STALE", "case_id": case_id}
            )
            outcome = "missing"
        if outcome not in {"consistent", "inconsistent", "unresolved"}:
            blockers.append(
                {"code": "COLD_REPEAT_ADJUDICATION_MISSING", "case_id": case_id}
            )
            outcome = "missing"
        elif outcome != "consistent":
            failures.append(
                {
                    "code": "COLD_REPEAT_INCONSISTENT",
                    "case_id": case_id,
                    "outcome": outcome,
                }
            )
        cold_results.append({"case_id": case_id, "outcome": outcome})

    hard_failures = [row for row in failures if row.get("critical", True)]
    if hard_failures:
        status = "SEMANTIC_CALIBRATION_FAIL"
    elif blockers:
        status = "SEMANTIC_CALIBRATION_BLOCKED"
    else:
        status = "SEMANTIC_CALIBRATION_PASS"
    report = {
        "schema_version": CALIBRATION_REPORT_VERSION,
        "status": status,
        "spec_sha256": normalized["spec_sha256"],
        "preparation_sha256": receipt.get("preparation_sha256"),
        "adjudication_sha256": (
            None if adjudicated is None else adjudicated["adjudication_sha256"]
        ),
        "slice_compilation_sha256": {
            slice_id: compilation["compilation_sha256"]
            for slice_id, compilation in sorted(compiled_by_slice.items())
        },
        "cold_slice_compilation_sha256": (
            None
            if cold_compilation is None
            else cold_compilation["compilation_sha256"]
        ),
        "reconciliation_view_sha256": {
            slice_id: view["view_sha256"]
            for slice_id, view in sorted(reconciled_views.items())
        },
        "case_results": case_results,
        "relation_results": relation_results,
        "cold_repeat_results": cold_results,
        "hard_failures": hard_failures,
        "measured_failures": failures,
        "blockers": blockers,
        "warnings": warnings,
        "scope_boundary": (
            "bounded calibration result only; not a prevalence estimate, "
            "full-corpus result, readiness claim, or corpus-resume authority"
        ),
    }
    report["report_sha256"] = _sha256(report)
    return report


__all__ = [
    "CALIBRATION_ADJUDICATION_VERSION",
    "CALIBRATION_ADJUDICATION_VERSION_V1",
    "CALIBRATION_ADJUDICATION_VERSION_V2",
    "CALIBRATION_PREPARATION_VERSION",
    "CALIBRATION_REPORT_VERSION",
    "CALIBRATION_SPEC_VERSION",
    "CALIBRATION_SPEC_VERSION_V1",
    "CALIBRATION_SPEC_VERSION_V2",
    "SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT",
    "SemanticCalibrationError",
    "build_calibration_source",
    "evaluate_semantic_calibration",
    "prepare_semantic_calibration",
    "route_fingerprint",
    "validate_calibration_adjudication",
    "validate_calibration_spec",
]
