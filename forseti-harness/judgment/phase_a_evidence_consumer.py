"""Decision-only Phase A evidence consumption with deterministic rehydration."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness_utils import sha256_text


DECISION_BATCH_MANIFEST_VERSION = "phase_a_evidence_decision_batch_manifest_v1"
EVIDENCE_PACKET_VERSION = "phase_a_evidence_packet_v3"
SYNTHESIS_FIELDS = (
    "summary",
    "supporting_refs",
    "counter_refs",
    "conditions_and_qualifiers",
    "behavior_signals",
    "engagement_observations",
    "uncertainties",
)
NONEMPTY_SYNTHESIS_ARRAYS = (
    "conditions_and_qualifiers",
    "behavior_signals",
    "engagement_observations",
    "uncertainties",
)

DECISION_BATCH_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the ordered case envelopes and frozen Phase A evidence-packet v3 JSON supplied through stdin. Return only the required JSON schema.

Return one result per case in the supplied case order and exactly one decision per selected proposition in selector order. Never move a judgment or ref between cases. The model creates only the synthesis judgment and literal evidence/semantic refs; deterministic code reattaches all source facts, inventories, and resolution metadata. Named defaults apply to every row in their scope, and positional values map to same-position named columns.

For each case, synthesize its complete evidence set without dropping support, counter, adjacent, unresolved, or unmerged material. supporting_refs may contain only literal evidence IDs or semantic-unit refs linked as support in that case; counter_refs may contain only refs linked as counter in that case. Include at least one when that relation exists, otherwise an empty array. Preserve conflict, conditions, behavior, engagement meaning, uncertainty, and causal limits. The four narrative arrays must each be nonempty; state absence instead of inventing it. Do not estimate prevalence, claim causation, create a commercial-pull score, or estimate people with similar experiences.

ORDERED_CASE_ENVELOPES_JSON:
{envelopes}
"""

DECISION_SINGLE_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the case selectors and frozen Phase A evidence-packet v3 JSON supplied through stdin. Return only the required JSON schema.

Return exactly one decision for each selected proposition, in selector order. The model creates only the synthesis judgment and literal evidence/semantic refs; deterministic code reattaches all source facts, inventories, and resolution metadata. Named defaults apply to every row in their scope, and positional values map to the same-position named columns.

Synthesize the complete evidence set without dropping support, counter, adjacent, unresolved, or unmerged material. supporting_refs may contain only literal evidence IDs or semantic-unit refs linked as support; counter_refs may contain only refs linked as counter. Include at least one when that relation exists, otherwise an empty array. Preserve conflict, conditions, behavior, engagement meaning, uncertainty, and causal limits. The four narrative arrays must each be nonempty; state absence instead of inventing it. Do not estimate prevalence, claim causation, create a commercial-pull score, or estimate people with similar experiences.

CASE_SELECTORS_JSON:
{selectors}

EVIDENCE_PACKAGE_JSON:
{packet}
"""


class EvidenceConsumerError(ValueError):
    """A deterministic consumer boundary rejected the batch or response."""

    def __init__(self, boundary: str, message: str) -> None:
        super().__init__(f"{boundary}: {message}")
        self.boundary = boundary


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _canonical_json_sha256(value: Any) -> str:
    return sha256_text(_compact(value))


def _canonical_packet_hash(packet: Mapping[str, Any]) -> str:
    return _canonical_json_sha256(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )


def _verify_packet(packet: Mapping[str, Any]) -> None:
    if packet.get("schema_version") != EVIDENCE_PACKET_VERSION:
        raise EvidenceConsumerError("packet_verification", "not a v3 packet")
    if packet.get("packet_sha256") != _canonical_packet_hash(packet):
        raise EvidenceConsumerError("packet_verification", "packet hash mismatch")


def _decision_case_schema() -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}}
    synthesis = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "supporting_refs": string_array,
            "counter_refs": string_array,
            "conditions_and_qualifiers": string_array,
            "behavior_signals": string_array,
            "engagement_observations": string_array,
            "uncertainties": string_array,
        },
        "required": list(SYNTHESIS_FIELDS),
        "additionalProperties": False,
    }
    decision = {
        "type": "object",
        "properties": {
            "proposition_id": {"type": "string"},
            "synthesis": synthesis,
        },
        "required": ["proposition_id", "synthesis"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "case_id": {"type": "string"},
            "decisions": {"type": "array", "items": decision},
        },
        "required": ["case_id", "decisions"],
        "additionalProperties": False,
    }


def decision_response_schema() -> dict[str, Any]:
    case = _decision_case_schema()
    return {
        "type": "object",
        "properties": {"cases": {"type": "array", "items": case}},
        "required": ["cases"],
        "additionalProperties": False,
    }


def decision_single_response_schema() -> dict[str, Any]:
    return _decision_case_schema()


def _expand_packet(
    packet: Mapping[str, Any],
) -> tuple[dict[str, tuple[dict[str, Any], dict[str, Any]]], dict[str, dict[str, Any]]]:
    _verify_packet(packet)
    schema = packet.get("catalogue_schema")
    if not isinstance(schema, dict):
        raise EvidenceConsumerError("rehydration_source_validation", "missing catalogue schema")
    semantic_columns = schema.get("semantic_unit_columns")
    semantic_defaults = schema.get("semantic_unit_defaults")
    if not isinstance(semantic_columns, list) or not isinstance(semantic_defaults, dict):
        raise EvidenceConsumerError("rehydration_source_validation", "invalid semantic layout")
    evidence_index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    semantic_index: dict[str, dict[str, Any]] = {}
    for group in packet.get("source_groups", []):
        if not isinstance(group, dict):
            raise EvidenceConsumerError("rehydration_source_validation", "invalid source group")
        for required in ("source_family", "source_role", "engagement_kind", "engagement_context"):
            if required not in group:
                raise EvidenceConsumerError("rehydration_source_validation", f"missing group field {required}")
        evidence_columns = group.get("evidence_columns")
        evidence_defaults = group.get("evidence_defaults")
        engagement_columns = group.get("engagement_columns")
        engagement_defaults = group.get("engagement_defaults")
        evidence_rows = group.get("evidence_rows")
        if not (
            isinstance(evidence_columns, list)
            and isinstance(evidence_defaults, dict)
            and isinstance(engagement_columns, list)
            and isinstance(engagement_defaults, dict)
            and isinstance(evidence_rows, list)
        ):
            raise EvidenceConsumerError("rehydration_source_validation", "invalid evidence layout")
        if "engagement" not in evidence_columns or "semantic_units" not in evidence_columns:
            raise EvidenceConsumerError("rehydration_source_validation", "missing nested evidence columns")
        for values in evidence_rows:
            if not isinstance(values, list) or len(values) != len(evidence_columns):
                raise EvidenceConsumerError("rehydration_source_validation", "evidence row width mismatch")
            evidence = dict(evidence_defaults)
            evidence.update(dict(zip(evidence_columns, values, strict=True)))
            raw_engagement = evidence.get("engagement")
            if not isinstance(raw_engagement, list) or len(raw_engagement) != len(engagement_columns):
                raise EvidenceConsumerError("missing_engagement", "engagement row missing or malformed")
            engagement = dict(engagement_defaults)
            engagement.update(dict(zip(engagement_columns, raw_engagement, strict=True)))
            status = engagement.get("status")
            unavailable = status == "engagement_unavailable" or group["engagement_kind"] == "engagement_unavailable"
            if unavailable:
                if status != "engagement_unavailable" or group["engagement_kind"] != "engagement_unavailable":
                    raise EvidenceConsumerError("missing_engagement", "unavailable engagement posture is inconsistent")
            elif status not in {None, "engagement_available"}:
                raise EvidenceConsumerError("missing_engagement", "engagement status is invalid")
            elif not {"raw_value", "observed_at", "material_positive"}.issubset(engagement):
                raise EvidenceConsumerError("missing_engagement", "available engagement facts are incomplete")
            evidence["engagement"] = engagement
            raw_semantics = evidence.get("semantic_units")
            if not isinstance(raw_semantics, list):
                raise EvidenceConsumerError("rehydration_source_validation", "semantic units missing")
            expanded_semantics = []
            for row in raw_semantics:
                if not isinstance(row, list) or len(row) != len(semantic_columns):
                    raise EvidenceConsumerError("rehydration_source_validation", "semantic row width mismatch")
                semantic = {**semantic_defaults, **dict(zip(semantic_columns, row, strict=True))}
                semantic_ref = semantic.get("semantic_unit_ref")
                if not isinstance(semantic_ref, str) or not semantic_ref:
                    raise EvidenceConsumerError("rehydration_source_validation", "semantic ref missing")
                if semantic_ref in semantic_index:
                    raise EvidenceConsumerError("rehydration_source_validation", "duplicate semantic ref")
                semantic_index[semantic_ref] = semantic
                expanded_semantics.append(semantic)
            evidence["semantic_units"] = expanded_semantics
            evidence_id = evidence.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                raise EvidenceConsumerError("rehydration_source_validation", "evidence id missing")
            if evidence_id in evidence_index:
                raise EvidenceConsumerError("rehydration_source_validation", "duplicate evidence id")
            evidence_index[evidence_id] = (group, evidence)
    return evidence_index, semantic_index


def _relation_rows(packet: Mapping[str, Any], proposition_id: str) -> list[dict[str, str]]:
    columns = packet["catalogue_schema"].get("relation_link_columns")
    if columns != ["evidence_id", "semantic_unit_refs"]:
        raise EvidenceConsumerError("rehydration_source_validation", "unexpected relation columns")
    proposition = next(
        (row for row in packet.get("propositions", []) if row.get("proposition_id") == proposition_id),
        None,
    )
    if proposition is None:
        raise EvidenceConsumerError("failed_rehydration_lookup", "proposition not found")
    relations = proposition.get("evidence_relations")
    if not isinstance(relations, dict):
        raise EvidenceConsumerError("rehydration_source_validation", "relations missing")
    rows: list[dict[str, str]] = []
    for relation in ("adjacent", "counter", "support"):
        links = relations.get(relation)
        if not isinstance(links, list):
            raise EvidenceConsumerError("rehydration_source_validation", f"{relation} relations missing")
        for link in links:
            if not isinstance(link, list) or len(link) != 2:
                raise EvidenceConsumerError("rehydration_source_validation", "relation row malformed")
            evidence_id, semantic_refs = link
            if not isinstance(evidence_id, str) or not isinstance(semantic_refs, list):
                raise EvidenceConsumerError("rehydration_source_validation", "relation row invalid")
            for semantic_ref in semantic_refs:
                if not isinstance(semantic_ref, str):
                    raise EvidenceConsumerError("rehydration_source_validation", "relation ref invalid")
                rows.append({"evidence_id": evidence_id, "semantic_unit_ref": semantic_ref, "relation": relation})
    return sorted(rows, key=lambda row: (row["evidence_id"], row["semantic_unit_ref"], row["relation"]))


def _target_row(
    packet: Mapping[str, Any],
    evidence_index: Mapping[str, tuple[dict[str, Any], dict[str, Any]]],
    semantic_index: Mapping[str, dict[str, Any]],
    relation_rows: Sequence[Mapping[str, str]],
    target: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_id = target.get("evidence_id")
    semantic_ref = target.get("semantic_unit_ref")
    if evidence_id not in evidence_index or semantic_ref not in semantic_index:
        raise EvidenceConsumerError("failed_rehydration_lookup", "target lookup failed")
    group, evidence = evidence_index[evidence_id]
    semantic = semantic_index[semantic_ref]
    if semantic not in evidence["semantic_units"]:
        raise EvidenceConsumerError("wrong_row_attachment", "semantic ref belongs to another evidence row")
    containers = {row.get("container_id"): row for row in packet.get("containers", [])}
    container = containers.get(evidence.get("container_id"))
    if not isinstance(container, dict):
        raise EvidenceConsumerError("failed_rehydration_lookup", "container lookup failed")
    relation_values = sorted(
        row["relation"]
        for row in relation_rows
        if row["evidence_id"] == evidence_id and row["semantic_unit_ref"] == semantic_ref
    )
    if not relation_values:
        raise EvidenceConsumerError("failed_rehydration_lookup", "target relation lookup failed")
    engagement = evidence["engagement"]
    unavailable = engagement.get("status") == "engagement_unavailable" or group["engagement_kind"] == "engagement_unavailable"
    return {
        "target_id": target.get("target_id"),
        "evidence_id": evidence_id,
        "source_role": group["source_role"],
        "source_family": group["source_family"],
        "publication_time": evidence.get("publication_time"),
        "engagement_kind": group["engagement_kind"],
        "engagement_context": group["engagement_context"],
        "engagement_raw_value": None if unavailable else engagement.get("raw_value"),
        "engagement_observed_at": None if unavailable else engagement.get("observed_at"),
        "engagement_material_positive": None if unavailable else engagement.get("material_positive"),
        "actor_identity": evidence.get("actor_identity"),
        "independence_posture": evidence.get("independence_posture"),
        "independence_key": evidence.get("independence_key"),
        "public_identity_key": evidence.get("public_identity_key"),
        "semantic_unit_ref": semantic_ref,
        "statement": semantic.get("statement"),
        "evidence_posture": semantic.get("evidence_posture"),
        "uncertainty_posture": semantic.get("uncertainty_posture"),
        "polarity": semantic.get("polarity"),
        "conditions": semantic.get("conditions", []),
        "relation": "+".join(relation_values),
        "container_id": container.get("container_id"),
        "container_type": container.get("container_type"),
        "captured_at": container.get("captured_at"),
        "captured_leaf_count": container.get("captured_leaf_count"),
        "completeness": container.get("completeness"),
        "capture_boundary": container.get("capture_boundary"),
        "source_visible_total": container.get("source_visible_total"),
    }


def _validate_synthesis(synthesis: Any, relation_rows: Sequence[Mapping[str, str]]) -> None:
    if not isinstance(synthesis, dict) or set(synthesis) != set(SYNTHESIS_FIELDS):
        raise EvidenceConsumerError("omitted_required_judgment", "synthesis shape mismatch")
    if not isinstance(synthesis.get("summary"), str) or not synthesis["summary"].strip():
        raise EvidenceConsumerError("omitted_required_judgment", "summary missing")
    for field in SYNTHESIS_FIELDS[1:]:
        if not isinstance(synthesis.get(field), list) or not all(isinstance(value, str) for value in synthesis[field]):
            raise EvidenceConsumerError("omitted_required_judgment", f"{field} invalid")
    for field in NONEMPTY_SYNTHESIS_ARRAYS:
        if not synthesis[field]:
            raise EvidenceConsumerError("omitted_required_judgment", f"{field} empty")
    allowed: dict[str, set[str]] = {"support": set(), "counter": set()}
    for row in relation_rows:
        if row["relation"] in allowed:
            allowed[row["relation"]].update((row["evidence_id"], row["semantic_unit_ref"]))
    for field, relation in (("supporting_refs", "support"), ("counter_refs", "counter")):
        refs = synthesis[field]
        invented = sorted(set(refs) - allowed[relation])
        if invented:
            raise EvidenceConsumerError("mutated_literal_ref", f"invalid {field}: {invented}")
        if allowed[relation] and not refs:
            raise EvidenceConsumerError("omitted_required_judgment", f"{field} required")
        if not allowed[relation] and refs:
            raise EvidenceConsumerError("mutated_literal_ref", f"{field} must be empty")


def _validate_case(case: Mapping[str, Any]) -> None:
    case_id = case.get("case_id")
    packet = case.get("packet")
    selectors = case.get("selectors")
    if not isinstance(case_id, str) or not case_id:
        raise EvidenceConsumerError("case_validation", "case id missing")
    if not isinstance(packet, dict) or not isinstance(selectors, dict):
        raise EvidenceConsumerError("case_validation", "packet and selectors are required")
    _verify_packet(packet)
    if selectors.get("case_id") != case_id:
        raise EvidenceConsumerError("case_validation", "selector case id mismatch")
    proposition_id = selectors.get("proposition_id")
    selected_ids = packet.get("selection", {}).get("proposition_ids")
    if selected_ids != [proposition_id]:
        raise EvidenceConsumerError("case_validation", "measured route requires one selected proposition")
    targets = selectors.get("targets")
    if not isinstance(targets, list) or not targets:
        raise EvidenceConsumerError("case_validation", "targets missing")
    target_ids = [target.get("target_id") for target in targets if isinstance(target, dict)]
    if len(target_ids) != len(targets) or len(target_ids) != len(set(target_ids)):
        raise EvidenceConsumerError("wrong_row_attachment", "target identity invalid")
    evidence_index, semantic_index = _expand_packet(packet)
    relation_keys = {
        (row["evidence_id"], row["semantic_unit_ref"])
        for row in _relation_rows(packet, proposition_id)
    }
    for target in targets:
        key = (target.get("evidence_id"), target.get("semantic_unit_ref"))
        if key not in relation_keys:
            raise EvidenceConsumerError("failed_rehydration_lookup", "target is not linked to proposition")
        if key[0] not in evidence_index or key[1] not in semantic_index:
            raise EvidenceConsumerError("failed_rehydration_lookup", "target lookup failed")


def _evidence_ids(case: Mapping[str, Any]) -> set[str]:
    packet = case["packet"]
    proposition_id = case["selectors"]["proposition_id"]
    return {row["evidence_id"] for row in _relation_rows(packet, proposition_id)}


def prepare_decision_batch(cases: Sequence[Mapping[str, Any]]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if not cases:
        raise EvidenceConsumerError("batch_validation", "at least one case is required")
    for case in cases:
        _validate_case(case)
    case_ids = [case.get("case_id") for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise EvidenceConsumerError("duplicate_case_id", "duplicate case id")
    if len(cases) > 1:
        bindings = [case["packet"].get("source_bindings") for case in cases]
        if not all(isinstance(binding, dict) for binding in bindings):
            raise EvidenceConsumerError("unrelated_batch", "source bindings missing")
        bundles = {binding.get("bundle_sha256") for binding in bindings}
        corpora = {binding.get("corpus_sha256") for binding in bindings}
        shared_evidence = set.intersection(*(_evidence_ids(case) for case in cases))
        if len(bundles) != 1 or len(corpora) != 1 or not shared_evidence:
            raise EvidenceConsumerError(
                "unrelated_batch",
                "multi-case batches require one bound corpus, one bundle, and shared evidence",
            )
    if len(cases) == 1:
        prompt = DECISION_SINGLE_PROMPT.format(
            selectors=_compact(cases[0]["selectors"]),
            packet=_compact(cases[0]["packet"]),
        )
        schema = decision_single_response_schema()
        response_envelope = "single_case"
    else:
        envelopes = [
            {
                "case_id": case["case_id"],
                "selectors": case["selectors"],
                "evidence_package": case["packet"],
            }
            for case in cases
        ]
        prompt = DECISION_BATCH_PROMPT.format(envelopes=_compact(envelopes))
        schema = decision_response_schema()
        response_envelope = "ordered_cases"
    manifest = {
        "schema_version": DECISION_BATCH_MANIFEST_VERSION,
        "case_order": case_ids,
        "response_envelope": response_envelope,
        "cases": [
            {
                "case_id": case["case_id"],
                "packet_path": str(case["packet_path"]),
                "packet_sha256": case["packet"]["packet_sha256"],
                "selectors_path": str(case["selectors_path"]),
                "selectors_sha256": _canonical_json_sha256(case["selectors"]),
                "proposition_id": case["selectors"]["proposition_id"],
            }
            for case in cases
        ],
        "prompt_sha256": sha256_text(prompt),
        "response_schema_sha256": _canonical_json_sha256(schema),
        "model_api_calls": 0,
    }
    manifest["manifest_sha256"] = _canonical_json_sha256(manifest)
    return prompt, schema, manifest


def _rehydrate_case(
    packet: Mapping[str, Any], selectors: Mapping[str, Any], decision_response: Mapping[str, Any]
) -> dict[str, Any]:
    if decision_response.get("case_id") != selectors.get("case_id"):
        raise EvidenceConsumerError("cross_proposition_contamination", "case id mismatch")
    expected_ids = [selectors.get("proposition_id")]
    decisions = decision_response.get("decisions")
    if not isinstance(decisions, list):
        raise EvidenceConsumerError("missing_proposition_result", "decisions missing")
    observed_ids = [row.get("proposition_id") for row in decisions if isinstance(row, dict)]
    if len(observed_ids) != len(set(observed_ids)):
        raise EvidenceConsumerError("duplicate_proposition_id", "duplicate proposition id")
    if observed_ids != expected_ids:
        boundary = "shuffled_proposition_order" if sorted(observed_ids) == sorted(expected_ids) else "judgment_identity_mismatch"
        raise EvidenceConsumerError(boundary, "proposition identity/order mismatch")
    evidence_index, semantic_index = _expand_packet(packet)
    relation_rows = _relation_rows(packet, expected_ids[0])
    for row in relation_rows:
        evidence_id = row["evidence_id"]
        semantic_ref = row["semantic_unit_ref"]
        if evidence_id not in evidence_index or semantic_ref not in semantic_index:
            raise EvidenceConsumerError("failed_rehydration_lookup", "relation lookup failed")
        if semantic_index[semantic_ref] not in evidence_index[evidence_id][1]["semantic_units"]:
            raise EvidenceConsumerError("wrong_row_attachment", "relation row attachment failed")
    rows = [
        _target_row(packet, evidence_index, semantic_index, relation_rows, target)
        for target in selectors["targets"]
    ]
    synthesis = decisions[0].get("synthesis")
    _validate_synthesis(synthesis, relation_rows)
    resolution = copy.deepcopy(packet.get("full_evidence_resolution"))
    if not isinstance(resolution, dict):
        raise EvidenceConsumerError("rehydration_source_validation", "resolution metadata missing")
    proposition = next(
        row
        for row in packet["propositions"]
        if row["proposition_id"] == expected_ids[0]
    )
    return {
        "case_id": selectors["case_id"],
        "proposition_id": expected_ids[0],
        "bounded_proposition": copy.deepcopy(proposition["bounded_proposition"]),
        "reconstructed_rows": rows,
        "relation_inventory": relation_rows,
        "evidence_id_inventory": sorted(evidence_index),
        "full_evidence_resolution": resolution,
        "evidence_packet": copy.deepcopy(packet),
        "synthesis": copy.deepcopy(synthesis),
    }


def finalize_decision_batch(
    cases: Sequence[Mapping[str, Any]], response: Mapping[str, Any]
) -> list[dict[str, Any]]:
    for case in cases:
        _validate_case(case)
    if len(cases) == 1:
        response = {"cases": [response]}
    if set(response) != {"cases"}:
        raise EvidenceConsumerError("batch_shape_invalid", "response shape mismatch")
    expected_case_ids = [case["case_id"] for case in cases]
    rows = response.get("cases")
    if not isinstance(rows, list):
        raise EvidenceConsumerError("missing_batch_results", "cases missing")
    observed_case_ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    if len(observed_case_ids) != len(rows):
        raise EvidenceConsumerError("batch_shape_invalid", "case row invalid")
    if len(observed_case_ids) != len(set(observed_case_ids)):
        raise EvidenceConsumerError("duplicate_case_id", "duplicate case id")
    if len(rows) != len(cases) or set(observed_case_ids) != set(expected_case_ids):
        raise EvidenceConsumerError("missing_batch_results", "case result set mismatch")
    if observed_case_ids != expected_case_ids:
        raise EvidenceConsumerError("shuffled_proposition_order", "case/proposition order mismatch")
    for row in rows:
        if set(row) != {"case_id", "decisions"}:
            raise EvidenceConsumerError("batch_shape_invalid", "case result shape mismatch")
        decisions = row.get("decisions")
        if not isinstance(decisions, list):
            raise EvidenceConsumerError("missing_proposition_result", "decisions missing")
        for decision in decisions:
            if not isinstance(decision, dict) or set(decision) != {"proposition_id", "synthesis"}:
                raise EvidenceConsumerError("batch_shape_invalid", "decision shape mismatch")
    observed_prop_ids = [
        decision.get("proposition_id")
        for row in rows
        for decision in row.get("decisions", [])
        if isinstance(decision, dict)
    ]
    expected_prop_ids = [case["selectors"]["proposition_id"] for case in cases]
    if len(observed_prop_ids) != len(set(observed_prop_ids)):
        raise EvidenceConsumerError("duplicate_proposition_id", "duplicate proposition id")
    if len(observed_prop_ids) != len(expected_prop_ids):
        raise EvidenceConsumerError("missing_proposition_result", "proposition result count mismatch")
    if observed_prop_ids != expected_prop_ids:
        raise EvidenceConsumerError("judgment_identity_mismatch", "judgment belongs to another proposition")

    ref_owners: dict[str, set[str]] = {}
    allowed_by_case: dict[str, dict[str, set[str]]] = {}
    for case in cases:
        relation_rows = _relation_rows(case["packet"], case["selectors"]["proposition_id"])
        allowed = {"support": set(), "counter": set()}
        for relation_row in relation_rows:
            relation = relation_row["relation"]
            if relation in allowed:
                for ref in (relation_row["evidence_id"], relation_row["semantic_unit_ref"]):
                    allowed[relation].add(ref)
                    ref_owners.setdefault(ref, set()).add(case["case_id"])
        allowed_by_case[case["case_id"]] = allowed
    batch_case_ids = set(expected_case_ids)
    for case, row in zip(cases, rows, strict=True):
        synthesis = row["decisions"][0].get("synthesis", {})
        for field, relation in (("supporting_refs", "support"), ("counter_refs", "counter")):
            refs = synthesis.get(field, [])
            for ref in refs if isinstance(refs, list) else []:
                if ref in allowed_by_case[case["case_id"]][relation]:
                    continue
                owners = ref_owners.get(ref, set())
                if owners & (batch_case_ids - {case["case_id"]}):
                    raise EvidenceConsumerError("foreign_evidence_ref", "ref belongs to another batched proposition")
                raise EvidenceConsumerError("mutated_literal_ref", "ref is not linked to this proposition")
    return [
        _rehydrate_case(case["packet"], case["selectors"], row)
        for case, row in zip(cases, rows, strict=True)
    ]


def load_prepared_cases(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    stored_hash = manifest.get("manifest_sha256")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        manifest.get("schema_version") != DECISION_BATCH_MANIFEST_VERSION
        or stored_hash != _canonical_json_sha256(payload)
    ):
        raise EvidenceConsumerError("manifest_verification", "manifest hash or version mismatch")
    cases = []
    for row in manifest.get("cases", []):
        packet_path = Path(row["packet_path"])
        selectors_path = Path(row["selectors_path"])
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        selectors = json.loads(selectors_path.read_text(encoding="utf-8-sig"))
        if (
            packet.get("packet_sha256") != row.get("packet_sha256")
            or _canonical_json_sha256(selectors) != row.get("selectors_sha256")
        ):
            raise EvidenceConsumerError("manifest_verification", "prepared input changed")
        cases.append(
            {
                "case_id": row["case_id"],
                "packet_path": packet_path,
                "selectors_path": selectors_path,
                "packet": packet,
                "selectors": selectors,
            }
        )
    if [case["case_id"] for case in cases] != manifest.get("case_order"):
        raise EvidenceConsumerError("manifest_verification", "case order changed")
    return cases


__all__ = [
    "DECISION_BATCH_MANIFEST_VERSION",
    "DECISION_BATCH_PROMPT",
    "DECISION_SINGLE_PROMPT",
    "EvidenceConsumerError",
    "decision_response_schema",
    "decision_single_response_schema",
    "finalize_decision_batch",
    "load_prepared_cases",
    "prepare_decision_batch",
]
