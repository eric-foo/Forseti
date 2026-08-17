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
QUOTE_MANIFEST_VERSION = "phase_a_evidence_quote_manifest_v1"
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

RELATION_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the bounded claim and ordered, source-owned candidate rows below. Return only the required JSON.

Return every candidate_id exactly once and in the supplied order. Label its relation to the bounded claim as support, counter, adjacent, or exclude and supply one short reason_code. Relation is about meaning, never engagement size. Preserve product, variant, timing, comparison, uncertainty, and source-role boundaries. A creator-authored item is influence context and cannot corroborate customer experience. Do not estimate prevalence, causation, commercial pull, or a number of similar customers.

SELECTION_ENVELOPE_JSON:
{envelope}
"""

QUOTE_PROMPT = """Do not call tools or inspect the filesystem. Analyze only the ordered selected rows and source bodies below. Return only the required JSON.

Return every selected_id exactly once and in order. If the body is available, choose one contiguous exact substring of at most 220 characters that directly expresses the supplied normalized meaning. Preserve spelling and punctuation. Do not rewrite, repair, add ellipses, or combine non-contiguous spans. If no relevant exact substring exists, return quote_status=quote_unavailable and exact_quote=null. Exact text that does not express the normalized meaning is not an acceptable quote.

SELECTED_SOURCE_BODIES_JSON:
{rows}
"""


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


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
            return None
        if set(value) != {"negative", "positive", "total"} or not all(
            isinstance(value[key], (int, float)) and not isinstance(value[key], bool)
            for key in value
        ):
            raise EvidenceConsumerError(
                "missing_engagement", "Sephora helpful-vote shape is invalid"
            )
        if value["negative"] < 0 or value["positive"] < 0 or value["total"] != value["negative"] + value["positive"]:
            raise EvidenceConsumerError(
                "missing_engagement", "Sephora helpful-vote totals are inconsistent"
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


def _relation_schema() -> dict[str, Any]:
    row = {
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string"},
            "relation": {"type": "string", "enum": list(RELATIONS)},
            "reason_code": {"type": "string"},
        },
        "required": ["candidate_id", "relation", "reason_code"],
        "additionalProperties": False,
    }
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
        "required": ["selected_id", "quote_status", "exact_quote"],
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
    prompt = RELATION_PROMPT.format(envelope=_compact(envelope))
    schema = _relation_schema()
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
    quiet = [
        row
        for row in ordered[1:]
        if row.get("engagement_material_positive") is False
        and first.get("engagement_material_positive") is not False
    ]
    distinct = [
        row
        for row in ordered[1:]
        if row["relation"] != first["relation"] or row.get("conditions") != first.get("conditions")
    ]
    if quiet:
        displays.append(quiet[0])
    elif distinct:
        displays.append(distinct[0])
    return displays


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
                }
            )
    return rows


def _select_groups(rows: Sequence[Mapping[str, Any]], layer: str, cap: int) -> list[dict[str, Any]]:
    eligible = [dict(row) for row in rows if row["layer"] == layer and row["relation"] != "exclude"]
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
                "origin_has_quiet": any(
                    row.get("engagement_material_positive") is False for row in members
                ),
                "origin_has_unknown_engagement": any(
                    row.get("engagement_status") == "engagement_unavailable" for row in members
                ),
                "origin_protected_lanes": sorted(
                    {
                        lane
                        for row in members
                        for lane in row.get("protected_lanes", [])
                    }
                ),
                "display_members": _display_members(members),
            }
        )
    if len(groups) <= cap:
        selected_groups = sorted(
            groups, key=lambda row: (row["source_role"], row["source_venue"], _global_priority(row))
        )
        return _flatten_display_groups(selected_groups)

    selected: list[dict[str, Any]] = []
    selected_origins: set[str] = set()

    def reserve(predicate: Any) -> None:
        choices = [row for row in groups if row["origin_group_id"] not in selected_origins and predicate(row)]
        if choices:
            choice = sorted(choices, key=_global_priority)[0]
            selected.append(choice)
            selected_origins.add(choice["origin_group_id"])

    if layer == "truth_support":
        reserve(lambda row: "support" in row["origin_relations"])
        reserve(lambda row: "counter" in row["origin_relations"])
        reserve(lambda row: row["origin_has_quiet"])
        reserve(lambda row: row["origin_has_unknown_engagement"])
        reserve(lambda row: "safety" in row["origin_protected_lanes"])
        reserve(lambda row: "costly_behavior" in row["origin_protected_lanes"])
    if len(selected) > cap:
        raise EvidenceConsumerError("presentation_cap_insufficient", "protected lanes exceed cap")

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
    return _flatten_display_groups(selected)


def _validate_relation_response(
    candidates: Sequence[Mapping[str, Any]], response: Mapping[str, Any]
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
        if result["relation"] not in RELATIONS or not isinstance(result["reason_code"], str) or not result["reason_code"].strip():
            raise EvidenceConsumerError("relation_response_shape", "invalid relation result")
        if candidate["layer"] == "influence_context" and result["relation"] in {"support", "counter"}:
            raise EvidenceConsumerError(
                "creator_customer_laundering", "creator-authored evidence cannot corroborate customer truth"
            )
        merged.append({**candidate, "relation": result["relation"], "reason_code": result["reason_code"]})
    return merged


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
    labeled = _validate_relation_response(candidates, response)
    truth = _select_groups(labeled, "truth_support", MAX_TRUTH_GROUPS)
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
                "source_body": bodies.get((row["source_id"], row["evidence_id"])),
            }
        )
    prompt = QUOTE_PROMPT.format(rows=_compact(quote_rows))
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
    if quote_manifest.get("schema_version") != QUOTE_MANIFEST_VERSION or stored != _canonical_json_sha256(payload):
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
        if set(quote_row) != {"selected_id", "quote_status", "exact_quote"}:
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
            if quote not in body:
                raise EvidenceConsumerError("quote_exactness", "quote is not a contiguous exact substring")
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
                "exact_quote": quote,
                "normalized_meaning": selected_row["normalized_meaning"],
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
            "an exact quote is verified for exactness only, not for semantic relevance",
            "quote_unavailable with source_body_present true means no quote was produced from an available body",
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
