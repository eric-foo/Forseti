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
)
from judgment.phase_a_evidence_selection import load_selection_sources


CONSOLIDATION_SPEC_VERSION = "phase_a_evidence_axis_consolidation_spec_v1"
CONSOLIDATED_VIEW_VERSION = "phase_a_evidence_axis_consolidated_view_v1"
SOURCE_AXIS_PACK_VERSION = "phase_a_hydration_axis_pack_v2"
CONSOLIDATION_POLICY = "origin_normalized_surface_separated_v1"
INDEPENDENCE_POSTURES = {
    "credited",
    "possible_same_actor",
    "confirmed_same_actor",
    "unavailable",
}


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


def _required_string(value: Mapping[str, Any], key: str, *, boundary: str) -> str:
    observed = value.get(key)
    if not isinstance(observed, str) or not observed:
        raise EvidenceConsumerError(boundary, f"{key} must be a nonempty string")
    return observed


def _string_list(value: Any, *, boundary: str, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise EvidenceConsumerError(boundary, f"{field} must be a string list")
    return list(value)


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
            if "/_/" in source_ref:
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
    descriptor: Mapping[str, Any], *, expected_axis: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    point_id = _required_string(descriptor, "point_id", boundary="point_binding")
    artifact_path = Path(_required_string(descriptor, "artifact_path", boundary="point_binding"))
    expected_artifact_hash = _required_string(
        descriptor, "artifact_sha256", boundary="point_binding"
    )
    if not artifact_path.is_file() or hash_file(artifact_path) != expected_artifact_hash:
        raise EvidenceConsumerError("point_binding", f"point artifact changed: {point_id}")
    artifact = _load_object(artifact_path, boundary="point_binding")
    if artifact.get("point_id") != point_id:
        raise EvidenceConsumerError("point_binding", f"point identity changed: {point_id}")
    if artifact.get("bounded_point") != descriptor.get("bounded_point"):
        raise EvidenceConsumerError("point_binding", f"bounded point changed: {point_id}")
    candidates = artifact.get("candidate_dispositions")
    if not isinstance(candidates, list) or len(candidates) != descriptor.get("candidate_count"):
        raise EvidenceConsumerError("candidate_access", f"candidate count changed: {point_id}")
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
    expected_raw = _required_string(
        descriptor, "selection_manifest_file_sha256", boundary="candidate_access"
    )
    if not selection_path.is_file() or hash_file(selection_path) != expected_raw:
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
    if selection_manifest.get("spec", {}).get("axis_ids") != [expected_axis]:
        raise EvidenceConsumerError("candidate_access", f"axis binding changed: {point_id}")
    load_selection_sources(selection_manifest)

    quote_path = Path(
        _required_string(descriptor, "quote_manifest_path", boundary="quote_binding")
    )
    if not quote_path.is_file():
        raise EvidenceConsumerError("quote_binding", f"quote manifest missing: {point_id}")
    quote_manifest = _load_object(quote_path, boundary="quote_binding")
    _verify_manifest_hash(
        quote_manifest,
        expected=descriptor.get("quote_manifest_sha256"),
        boundary="quote_binding",
    )
    if quote_manifest.get("selection_manifest_sha256") != artifact.get(
        "selection_manifest_sha256"
    ):
        raise EvidenceConsumerError("quote_binding", f"quote lineage changed: {point_id}")
    return artifact, candidate_by_id, {
        "artifact_path": str(artifact_path),
        "artifact_sha256": expected_artifact_hash,
        "selection_manifest_path": str(selection_path),
        "selection_manifest_file_sha256": expected_raw,
        "selection_manifest_sha256": selection_manifest["manifest_sha256"],
        "quote_manifest_path": str(quote_path),
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
    }


def build_axis_consolidated_view(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Build and fully verify one derived, origin-normalized axis view."""

    if spec.get("schema_version") != CONSOLIDATION_SPEC_VERSION:
        raise EvidenceConsumerError("consolidation_spec", "unsupported spec version")
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
    if (
        axis_pack.get("schema_version") != SOURCE_AXIS_PACK_VERSION
        or axis_pack.get("axis_id") != axis_id
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

    origins: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    quote_spans: dict[str, dict[str, Any]] = {}
    companion_meanings: dict[str, dict[str, Any]] = {}
    placements: list[dict[str, Any]] = []
    point_index: list[dict[str, Any]] = []
    candidate_total = 0

    for descriptor in point_descriptors:
        point_id = descriptor["point_id"]
        artifact, candidate_by_id, bindings = _load_point(
            descriptor, expected_axis=axis_id
        )
        candidate_total += len(candidate_by_id)
        point_placement_ids: list[str] = []
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
                observed_relations[relation] += 1
                relation_origin_ids[relation].add(origin_id)
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
        distinct_point_origins = set().union(*relation_origin_ids.values())
        if (
            artifact.get("truth_group_count") != descriptor.get("truth_origin_count")
            or len(distinct_point_origins) != descriptor.get("truth_origin_count")
        ):
            raise EvidenceConsumerError(
                "point_projection", f"truth origin count changed: {point_id}"
            )
        group_id, family_id = point_navigation[point_id]
        point_index.append(
            {
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
        )

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

    view: dict[str, Any] = {
        "schema_version": CONSOLIDATED_VIEW_VERSION,
        "policy": CONSOLIDATION_POLICY,
        "axis_id": axis_id,
        "spec": copy.deepcopy(dict(spec)),
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
    if view["counts"]["point_count"] != axis_pack.get("valid_point_count"):
        raise EvidenceConsumerError("axis_parity", "point count differs from source axis pack")
    if view["counts"]["candidate_disposition_count"] != axis_pack.get(
        "cold_reader_resolution", {}
    ).get("resolved_candidate_disposition_count"):
        raise EvidenceConsumerError("axis_parity", "candidate disposition count changed")
    if view["counts"]["placement_count"] != axis_pack.get("display_row_slots"):
        raise EvidenceConsumerError("axis_parity", "display placement count changed")
    if view["counts"]["unique_origin_count"] != axis_pack.get(
        "unique_truth_origins_across_axis"
    ):
        raise EvidenceConsumerError("axis_parity", "unique origin count changed")
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

    if view.get("schema_version") != CONSOLIDATED_VIEW_VERSION:
        raise EvidenceConsumerError("view_verification", "unsupported view version")
    stored = view.get("view_sha256")
    payload = {key: value for key, value in view.items() if key != "view_sha256"}
    if not isinstance(stored, str) or stored != _canonical_json_sha256(payload):
        raise EvidenceConsumerError("view_verification", "stored view hash is invalid")
    if stored != expected_view_sha256:
        raise EvidenceConsumerError(
            "view_verification", "trusted view identity differs from saved view"
        )
    spec = view.get("spec")
    if not isinstance(spec, Mapping):
        raise EvidenceConsumerError("view_verification", "embedded spec missing")
    rebuilt = build_axis_consolidated_view(spec)
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
