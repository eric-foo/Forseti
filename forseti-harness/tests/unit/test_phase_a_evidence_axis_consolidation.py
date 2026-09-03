from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import pytest

from harness_utils import hash_file
from judgment.phase_a_evidence_axis_consolidation import (
    AXIS_PACK_MANIFEST_VERSION,
    AXIS_PACK_VERSION,
    AXIS_READER_MANIFEST_VERSION,
    AXIS_READER_ACCOUNTING_VERSION,
    POINT_READER_AXIS_OUTPUT_VERSION,
    POINT_READER_BRIEF_VERSION,
    POINT_READER_METHOD_TEXT,
    POINT_READER_RESPONSE_SCHEMA,
    POINT_READER_RUN_MANIFEST_VERSION,
    CONSOLIDATED_VIEW_VERSION,
    CONSOLIDATION_SPEC_VERSION,
    CURRENT_CONSOLIDATION_SPEC_VERSION,
    DECISION_STATE_BOUNDARIES,
    DECISION_STATE_CONSUMER_CONTRACT,
    DIRECT_OUTCOME_BOUNDARIES,
    RELATION_SEMANTIC_WARRANT_BOUNDARY,
    DOGFOOD_TRUTH_INDEX_VERSION,
    EVIDENCE_ACCOUNTING_CONTRACT,
    LEGACY_CONSOLIDATED_VIEW_VERSION,
    LEGACY_CONSOLIDATION_SPEC_VERSION,
    _axis_reader_point_filename,
    _point_reader_state_ledger,
    _reader_evidence_accounting_contract,
    _validate_decision_state_reader_evidence_rows,
    bind_axis_reader_output_schema,
    bind_point_reader_response_schema,
    assemble_axis_point_reader_output,
    build_axis_point_reader_snapshot,
    build_axis_reader_bundle,
    build_axis_reader_accounting,
    build_axis_dogfood_truth_index,
    build_axis_consolidated_view,
    build_phase_a_evidence_axis_pack,
    compile_point_reader_brief,
    point_placement_keys,
    point_reader_input_sha256,
    validate_axis_point_reader_output,
    validate_axis_point_reader_snapshot,
    validate_axis_reader_bundle,
    validate_axis_reader_accounting,
    validate_axis_reader_structured_output,
    validate_axis_dogfood_truth_index,
    validate_axis_consolidated_view,
    validate_phase_a_evidence_axis_pack,
    validate_point_reader_brief,
    validate_point_reader_completion_membership,
)
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
)
from judgment.phase_a_decision_state_reconciliation import (
    DECISION_STATE_ADJUDICATION_VERSION,
    DECISION_STATE_RECONCILIATION_PLAN_VERSION,
    finalize_phase_a_decision_state_reconciliation,
    prepare_phase_a_decision_state_reconciliation,
)
from judgment.phase_a_evidence_selection import PARENT_CONTEXT_POLICY
from runners.run_phase_a_evidence_axis_consolidation import (
    build_axis_pack_run,
    build_dogfood_truth_run,
    build_reader_run,
    build_reader_accounting_run,
    build_point_reader_run,
    bind_reader_output_schema_run,
    build_run,
    validate_axis_pack_run,
    validate_dogfood_truth_run,
    validate_reader_run,
    validate_reader_accounting_run,
    validate_reader_output_run,
    validate_run,
    finalize_point_reader_run,
    prepare_point_reader_request_run,
    prepare_point_reader_requests_run,
    validate_point_reader_output_run,
    validate_point_reader_run,
)
import runners.run_phase_a_evidence_axis_consolidation as consolidation_runner
import judgment.phase_a_evidence_axis_consolidation as consolidation_judgment


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _manifest(**values: Any) -> dict[str, Any]:
    values["manifest_sha256"] = _canonical_json_sha256(values)
    return values


def _rehash_manifest(value: dict[str, Any]) -> None:
    value.pop("manifest_sha256", None)
    value["manifest_sha256"] = _canonical_json_sha256(value)


def _rehash_reader_manifest(value: dict[str, Any]) -> None:
    value.pop("reader_manifest_sha256", None)
    value["reader_manifest_sha256"] = _canonical_json_sha256(value)


def _write_reader_facts(facts_dir: Path, streams: Mapping[str, bytes]) -> None:
    facts_dir.mkdir()
    for point_id, fact_bytes in streams.items():
        (facts_dir / _axis_reader_point_filename(point_id)).write_bytes(fact_bytes)


def _reader_facts(streams: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for point_id in sorted(streams)
        for line in streams[point_id].decode("utf-8").splitlines()
    ]


def _structured_reader_output(
    manifest: Mapping[str, Any], streams: Mapping[str, bytes]
) -> dict[str, Any]:
    facts_by_point = {
        point_id: [json.loads(line) for line in value.decode("utf-8").splitlines()]
        for point_id, value in streams.items()
    }
    return {
        "point_accounting": [
            {
                "point_id": point["point_id"],
                "bounded_point": point["bounded_point"],
                "route": point["projection_mode"],
            }
            for point in manifest["points"]
        ],
        "accepted_points": [
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
                    "candidate_pool_accounting": point[
                        "candidate_pool_accounting"
                    ],
                },
                "representative_evidence": [
                    {
                        "evidence_id": fact["evidence"]["evidence_id"],
                        "relation": fact["relation"],
                        "quote_span_id": fact["quote"]["quote_span_id"],
                        "quote_status": fact["quote"]["quote_status"],
                        "exact_quote": fact["quote"]["exact_quote"],
                    }
                ],
            }
            for point in manifest["points"]
            for fact in facts_by_point[point["point_id"]][:1]
        ],
    }


def _reader_output_base_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "point_accounting": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "point_id": {"type": "string"},
                        "bounded_point": {"type": "string"},
                        "route": {"type": "string"},
                    },
                },
            },
            "accepted_points": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "point_id": {"type": "string"},
                        "bounded_point": {"type": "string"},
                        "projection_route": {"type": "string"},
                        "exact_phase_a_meaning": {"type": "string"},
                        "reader_accounting": {
                            "type": "object",
                            "properties": {
                                "displayed_relation_row_counts": {
                                    "type": "object",
                                    "properties": {
                                        "support": {"type": "integer"},
                                        "counter": {"type": "integer"},
                                        "adjacent": {"type": "integer"},
                                    },
                                },
                                "truth_origin_count": {"type": "integer"},
                                "candidate_pool_accounting": {
                                    "type": "object",
                                    "additionalProperties": True,
                                },
                            },
                        },
                    },
                },
            },
        },
    }


def test_axis_reader_point_filename_preserves_identity_without_path_restriction() -> None:
    assert _axis_reader_point_filename("prop_safe-1.2") == "prop_safe-1.2.jsonl"
    unsafe = _axis_reader_point_filename("point:valid/but-not-a-filename")
    assert unsafe.startswith("point_") and unsafe.endswith(".jsonl")
    assert ":" not in unsafe and "/" not in unsafe


def _candidate(
    candidate_id: str,
    *,
    evidence_id: str,
    semantic_ref: str,
    relation: str,
    origin: str,
    container: str,
    conditions: list[str] | None = None,
    independence_posture: str = "credited",
    normalized_meaning: str | None = None,
    source_ref: str | None = None,
    publication_time: str = "2025-06-01T00:00:00+00:00",
    engagement_value: Any = None,
) -> dict[str, Any]:
    if evidence_id.startswith("reddit:"):
        _, thread_id, item_id = evidence_id.split(":")
        source_ref = source_ref or (
            f"https://www.reddit.com/r/test/comments/{thread_id}/title/"
            if item_id == "post"
            else f"https://www.reddit.com/comments/{thread_id}/_/{item_id}"
        )
        source_venue = "reddit"
        source_role = "community_post"
        engagement_kind = "score_state"
    else:
        source_ref = source_ref or f"https://www.sephora.com/product/test#{evidence_id}"
        source_venue = "sephora"
        source_role = "retailer_review"
        engagement_kind = "positive_helpful_count"
    return {
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "semantic_unit_ref": semantic_ref,
        "normalized_meaning": normalized_meaning or f"Meaning for {semantic_ref}",
        "relation": relation,
        "scoped_independence_key": origin,
        "independence_posture": independence_posture,
        "container_id": container,
        "source_ref": source_ref,
        "publication_time": publication_time,
        "source_venue": source_venue,
        "source_role": source_role,
        "engagement_kind": engagement_kind,
        "engagement_status": "engagement_available",
        "engagement_raw_value": engagement_value,
        "engagement_observed_at": None,
        "engagement_material_positive": False,
        "source_id": "fixture",
        "packet_sha256": "fixture_packet_sha256",
        "conditions": conditions or [],
        "product_version_ids": [],
        "uncertainty_posture": "asserted",
    }


def _row(
    selected_id: str,
    *,
    evidence_id: str,
    semantic_ref: str,
    relation: str,
    origin: str,
    independence_key: str,
    source_ref: str,
    source_venue: str,
    source_role: str,
    engagement_kind: str,
    engagement_value: Any,
    quote: str,
    candidate_id: str,
    companion_meanings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "selected_id": selected_id,
        "evidence_id": evidence_id,
        "semantic_unit_ref": semantic_ref,
        "relation": relation,
        "origin_group_id": origin,
        "independence_key": independence_key,
        "origin_candidate_ids": [candidate_id],
        "layer": "truth_support",
        "reason_code": "matching_experience",
        "display_label": "Matching experience",
        "normalized_meaning": f"Meaning for {semantic_ref}",
        "source_family": "retailer_review" if source_role == "retailer_review" else "reddit_community",
        "source_role": source_role,
        "source_venue": source_venue,
        "source_venue_basis": "fixture",
        "source_ref": source_ref,
        "publication_time": "2025-06-01T00:00:00+00:00",
        "engagement_kind": engagement_kind,
        "engagement_raw_value": engagement_value,
        "engagement_observed_at": None,
        "quote_status": "quote_available",
        "exact_quote": quote,
        "quote_unavailable_cause": None,
        "same_evidence_companion_meanings": companion_meanings or [],
    }


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    selection_source_calls: list[Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Path]]:
    recorded = [] if selection_source_calls is None else selection_source_calls

    def _record_selection_sources(manifest: Mapping[str, Any]) -> list[Any]:
        recorded.append(manifest)
        return []

    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation.load_selection_sources",
        _record_selection_sources,
    )
    point_data = {
        "point_a": {
            "bounded_point": "The balm is hydrating.",
            "rows": [
                _row(
                    "selected_01",
                    evidence_id="reddit:thread1:post",
                    semantic_ref="reddit:thread1:post::hydrating",
                    relation="support",
                    origin="scope::reddit:alice",
                    independence_key="reddit:alice",
                    source_ref="https://www.reddit.com/r/test/comments/thread1/title/",
                    source_venue="reddit",
                    source_role="community_post",
                    engagement_kind="score_state",
                    engagement_value="200 points",
                    quote="It is hydrating.",
                    candidate_id="candidate_a",
                    companion_meanings=[
                        {
                            "semantic_unit_ref": "reddit:thread1:post::texture",
                            "normalized_meaning": "It also feels smooth.",
                            "polarity": "affirmed",
                        }
                    ],
                ),
                _row(
                    "selected_02",
                    evidence_id="reddit:thread1:comment1",
                    semantic_ref="reddit:thread1:comment1::dry",
                    relation="counter",
                    origin="scope::reddit:bob",
                    independence_key="reddit:bob",
                    source_ref="https://www.reddit.com/comments/thread1/_/comment1",
                    source_venue="reddit",
                    source_role="community_post",
                    engagement_kind="score_state",
                    engagement_value="200 points",
                    quote="It dried my lips.",
                    candidate_id="candidate_b",
                ),
            ],
            "candidates": [
                _candidate(
                    "candidate_a",
                    evidence_id="reddit:thread1:post",
                    semantic_ref="reddit:thread1:post::hydrating",
                    relation="support",
                    origin="scope::reddit:alice",
                    container="reddit_thread_thread1",
                ),
                _candidate(
                    "candidate_b",
                    evidence_id="reddit:thread1:comment1",
                    semantic_ref="reddit:thread1:comment1::dry",
                    relation="counter",
                    origin="scope::reddit:bob",
                    container="reddit_thread_thread1",
                    conditions=["after repeated use"],
                ),
                _candidate(
                    "candidate_unseen_a",
                    evidence_id="reddit:thread2:post",
                    semantic_ref="reddit:thread2:post::other",
                    relation="adjacent",
                    origin="scope::reddit:other",
                    container="reddit_thread_thread2",
                ),
            ],
        },
        "point_b": {
            "bounded_point": "The balm does not moisturize.",
            "rows": [
                _row(
                    "selected_01",
                    evidence_id="reddit:thread1:post",
                    semantic_ref="reddit:thread1:post::hydrating",
                    relation="counter",
                    origin="scope::reddit:alice",
                    independence_key="reddit:alice",
                    source_ref="https://www.reddit.com/r/test/comments/thread1/title/",
                    source_venue="reddit",
                    source_role="community_post",
                    engagement_kind="score_state",
                    engagement_value="200 points",
                    quote="It is hydrating.",
                    candidate_id="candidate_a",
                    companion_meanings=[
                        {
                            "semantic_unit_ref": "reddit:thread1:post::texture",
                            "normalized_meaning": "It also feels smooth.",
                            "polarity": "affirmed",
                        }
                    ],
                ),
                _row(
                    "selected_02",
                    evidence_id="retailer:sephora:review1",
                    semantic_ref="retailer:sephora:review1::dry",
                    relation="support",
                    origin="scope::sephora:carol",
                    independence_key="sephora:carol",
                    source_ref="https://www.sephora.com/product/test#review1",
                    source_venue="sephora",
                    source_role="retailer_review",
                    engagement_kind="positive_helpful_count",
                    engagement_value=12,
                    quote="It did not moisturize.",
                    candidate_id="candidate_c",
                ),
            ],
            "candidates": [
                _candidate(
                    "candidate_a",
                    evidence_id="reddit:thread1:post",
                    semantic_ref="reddit:thread1:post::hydrating",
                    relation="counter",
                    origin="scope::reddit:alice",
                    container="reddit_thread_thread1",
                ),
                _candidate(
                    "candidate_c",
                    evidence_id="retailer:sephora:review1",
                    semantic_ref="retailer:sephora:review1::dry",
                    relation="support",
                    origin="scope::sephora:carol",
                    container="sephora_product_test",
                ),
                _candidate(
                    "candidate_unseen_b",
                    evidence_id="reddit:thread3:post",
                    semantic_ref="reddit:thread3:post::other",
                    relation="adjacent",
                    origin="scope::reddit:other2",
                    container="reddit_thread_thread3",
                ),
            ],
        },
    }
    descriptors = []
    paths: dict[str, Path] = {}
    for point_id, data in point_data.items():
        inventory_hash = _canonical_json_sha256(
            [
                {
                    key: value
                    for key, value in candidate.items()
                    if key not in {"relation", "reason_code"}
                }
                for candidate in data["candidates"]
            ]
        )
        selection = _manifest(
            schema_version="phase_a_evidence_selection_manifest_v1",
            candidate_inventory_sha256=inventory_hash,
            spec={"schema_version": "phase_a_evidence_selection_spec_v1", "axis_ids": ["hydration_and_moisture"]},
            sources=[],
        )
        selection_path = tmp_path / point_id / "selection.json"
        _write(selection_path, selection)
        quote = _manifest(
            schema_version="phase_a_evidence_quote_manifest_v6",
            selection_manifest_sha256=selection["manifest_sha256"],
            candidate_inventory_sha256=inventory_hash,
        )
        quote_path = tmp_path / point_id / "quote.json"
        _write(quote_path, quote)
        relation_counts: dict[str, int] = {}
        for row in data["rows"]:
            relation_counts[row["relation"]] = relation_counts.get(row["relation"], 0) + 1
        artifact = {
            "schema_version": "phase_a_evidence_selection_artifact_v2",
            "point_id": point_id,
            "bounded_point": data["bounded_point"],
            "candidate_dispositions": data["candidates"],
            "candidate_inventory_sha256": inventory_hash,
            "selection_manifest_sha256": selection["manifest_sha256"],
            "quote_manifest_sha256": quote["manifest_sha256"],
            "truth_group_cap": 13,
            "truth_group_count": 2,
            "relation_confirmation_status": "passed",
            "point_scope_confirmation_status": "passed",
            "point_scope_confirmation_reason": "one bounded fixture point",
            "selection_disclosure": {
                "candidate_semantic_row_count": 3,
                "displayed_row_count": 2,
                "displayed_truth_origin_count": 2,
            },
            "source_groups": [{"rows": data["rows"]}],
            "output_boundary": [
                "not a prevalence estimate",
                *DIRECT_OUTCOME_BOUNDARIES,
            ],
        }
        artifact_path = tmp_path / point_id / "artifact.json"
        _write(artifact_path, artifact)
        paths[f"artifact_{point_id}"] = artifact_path
        paths[f"selection_{point_id}"] = selection_path
        descriptors.append(
            {
                "point_id": point_id,
                "bounded_point": data["bounded_point"],
                "artifact_path": str(artifact_path),
                "artifact_sha256": hash_file(artifact_path),
                "candidate_count": 3,
                "display_row_count": 2,
                "truth_origin_count": 2,
                "relation_counts": relation_counts,
                "policy_revision": "fixture",
                "selection_manifest_path": str(selection_path),
                "selection_manifest_file_sha256": hash_file(selection_path),
                "selection_manifest_sha256": selection["manifest_sha256"],
                "quote_manifest_path": str(quote_path),
                "quote_manifest_sha256": quote["manifest_sha256"],
            }
        )
    axis = {
        "schema_version": "phase_a_hydration_axis_pack_v2",
        "status": "complete_valid_axis_pack",
        "axis_id": "hydration_and_moisture",
        "valid_point_count": 2,
        "display_row_slots": 4,
        "unique_truth_origins_across_axis": 3,
        "unique_evidence_items_across_axis": 3,
        "cold_reader_resolution": {"resolved_candidate_disposition_count": 6},
        "points": descriptors,
    }
    axis_path = tmp_path / "axis.json"
    _write(axis_path, axis)
    paths["axis"] = axis_path
    spec = {
        "schema_version": CONSOLIDATION_SPEC_VERSION,
        "axis_id": "hydration_and_moisture",
        "source_axis_pack_path": str(axis_path),
        "source_axis_pack_sha256": hash_file(axis_path),
        "navigation_groups": [
            {
                "group_id": "hydration_efficacy",
                "label": "Hydration efficacy",
                "families": [
                    {
                        "family_id": "hydration_direction",
                        "label": "Hydration direction",
                        "point_ids": ["point_a", "point_b"],
                    }
                ],
            }
        ],
        "projection_routes": [
            {
                "projection_mode": "direct_outcome",
                "point_ids": ["point_a", "point_b"],
            }
        ],
    }
    return spec, paths


def _generic_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    legacy_spec, paths = _fixture(tmp_path, monkeypatch)
    legacy_axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    accepted = []
    for descriptor in legacy_axis["points"]:
        accepted.append(
            {
                "point_id": descriptor["point_id"],
                "bounded_point": descriptor["bounded_point"],
                "artifact_path": descriptor["artifact_path"],
                "artifact_sha256": descriptor["artifact_sha256"],
                "policy_revision": descriptor["policy_revision"],
                "selection_manifest_path": descriptor["selection_manifest_path"],
                "selection_manifest_file_sha256": descriptor[
                    "selection_manifest_file_sha256"
                ],
                "selection_manifest_sha256": descriptor["selection_manifest_sha256"],
                "quote_manifest_path": descriptor["quote_manifest_path"],
                "quote_manifest_file_sha256": hash_file(
                    Path(descriptor["quote_manifest_path"])
                ),
                "quote_manifest_sha256": descriptor["quote_manifest_sha256"],
            }
        )
    manifest = _manifest(
        schema_version=AXIS_PACK_MANIFEST_VERSION,
        axis_id="hydration_and_moisture",
        accepted_points=accepted,
        rejected_points=[
            {
                "point_id": "point_rejected",
                "bounded_point": "The balm fixes every lip outcome.",
                "disposition": "point_scope_failed",
                "reason": "broad_axis_or_bundle",
            }
        ],
    )
    pack = build_phase_a_evidence_axis_pack(manifest)
    axis_path = tmp_path / "generic_axis.json"
    _write(axis_path, pack)
    paths["generic_axis"] = axis_path
    spec = copy.deepcopy(legacy_spec)
    spec["source_axis_pack_path"] = str(axis_path)
    spec["source_axis_pack_sha256"] = hash_file(axis_path)
    return manifest, spec, paths


def _actor_scope_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, current_count: int | None = None):
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    scope = {"mode": "source_local_reports"}
    for descriptor in manifest["accepted_points"][:current_count]:
        selection_path = Path(descriptor["selection_manifest_path"])
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection["spec"].update(schema_version="phase_a_evidence_selection_spec_v2", point_actor_scope=scope)
        _rehash_manifest(selection)
        _write(selection_path, selection)
        quote_path = Path(descriptor["quote_manifest_path"])
        quote = json.loads(quote_path.read_text(encoding="utf-8"))
        quote.update(point_actor_scope=scope, selection_manifest_sha256=selection["manifest_sha256"])
        _rehash_manifest(quote)
        _write(quote_path, quote)
        artifact_path = Path(descriptor["artifact_path"])
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact.update(point_actor_scope=scope, selection_manifest_sha256=selection["manifest_sha256"], quote_manifest_sha256=quote["manifest_sha256"])
        _write(artifact_path, artifact)
        descriptor.update(artifact_sha256=hash_file(artifact_path), selection_manifest_file_sha256=hash_file(selection_path), selection_manifest_sha256=selection["manifest_sha256"], quote_manifest_file_sha256=hash_file(quote_path), quote_manifest_sha256=quote["manifest_sha256"])
    _rehash_manifest(manifest)
    _write(paths["generic_axis"], build_phase_a_evidence_axis_pack(manifest))
    spec["source_axis_pack_sha256"] = hash_file(paths["generic_axis"])
    return manifest, spec, paths


@pytest.mark.parametrize("mutation", ["omit", "change"])
def test_actor_scope_wrong_cause_reaches_public_pack_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    manifest, _, _ = _actor_scope_fixture(tmp_path, monkeypatch)
    descriptor = manifest["accepted_points"][0]
    path = Path(descriptor["artifact_path"])
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "omit":
        del artifact["point_actor_scope"]
    else:
        artifact["point_actor_scope"] = {"mode": "identified_actor", "source_id": "other", "independence_key": "foreign"}
    _write(path, artifact)
    descriptor["artifact_sha256"] = hash_file(path)
    _rehash_manifest(manifest)
    with pytest.raises(EvidenceConsumerError) as caught:
        build_phase_a_evidence_axis_pack(manifest)
    assert caught.value.boundary == "point_actor_scope"
    assert "between selection and reader" in str(caught.value)


@pytest.mark.parametrize("current_count", [1, 2])
def test_actor_scope_survives_both_public_readers_and_rejects_omission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, current_count: int) -> None:
    _, spec, _ = _actor_scope_fixture(tmp_path, monkeypatch, current_count=current_count)
    _route_fixture_as_current_mixed(spec)
    view = build_axis_consolidated_view(spec)
    assert "point_actor_scope" in view["decision_state_reader_surface"]["point_table"]["columns"]
    path = tmp_path / "view.json"
    _write(path, view)
    facts_dir = tmp_path / "facts"
    manifest, streams = build_axis_reader_bundle(view, source_view_path=path, facts_dir=facts_dir)
    _write_reader_facts(facts_dir, streams)
    output = _structured_reader_output(manifest, streams)
    scope = {"mode": "source_local_reports"}
    scoped_ids = {row["point_id"] for row in view["point_index"] if "point_actor_scope" in row}
    assert len(scoped_ids) == current_count
    for row in output["accepted_points"]:
        if row["point_id"] in scoped_ids:
            row["point_actor_scope"] = scope
    assert validate_axis_reader_structured_output(manifest, facts_dir=facts_dir, expected_reader_manifest_sha256=manifest["reader_manifest_sha256"], output=output)
    bound = bind_axis_reader_output_schema(manifest, _reader_output_base_schema())
    assert sum("point_actor_scope" in row.get("required", []) for row in bound["properties"]["accepted_points"]["items"]["anyOf"]) == current_count
    del next(row for row in output["accepted_points"] if row["point_id"] in scoped_ids)["point_actor_scope"]
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_reader_structured_output(manifest, facts_dir=facts_dir, expected_reader_manifest_sha256=manifest["reader_manifest_sha256"], output=output)
    assert caught.value.boundary == "point_actor_scope"
    snapshot, payloads = build_axis_point_reader_snapshot(view, source_view_path=path, subject_identity=_point_reader_subject_identity())
    store = tmp_path / "point_store"
    _write_point_reader_store(store, snapshot, payloads)
    point = next(row for row in snapshot["points"] if row["point_id"] in scoped_ids)
    request = consolidation_runner._point_reader_request(snapshot, point, payloads[point["point_id"]])
    assert request["point_actor_scope"] == scope
    brief = compile_point_reader_brief(snapshot, point_store_dir=store, point_id=point["point_id"], response=_point_reader_response(point, payloads[point["point_id"]]))
    assert brief["point_actor_scope"] == scope
    validate_point_reader_brief(snapshot, point_store_dir=store, brief=brief)
    del brief["point_actor_scope"]
    brief.pop("brief_sha256")
    brief["brief_sha256"] = _canonical_json_sha256(brief)
    # A valid outer hash cannot conceal omission of compiler-owned scope.
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(snapshot, point_store_dir=store, brief=brief)
    assert caught.value.boundary == "point_reader_brief"
    assert "compiled point binding changed" in str(caught.value)


def test_actor_scope_rule_is_frozen_and_only_invalidates_scoped_point_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, spec, _ = _actor_scope_fixture(tmp_path, monkeypatch, current_count=1)
    view = build_axis_consolidated_view(spec)
    path = tmp_path / "view.json"
    _write(path, view)
    snapshot, payloads = build_axis_point_reader_snapshot(view, source_view_path=path, subject_identity=_point_reader_subject_identity())
    original_rule = snapshot["method_binding"]["actor_scope_rule"]
    monkeypatch.setattr(consolidation_judgment, "POINT_ACTOR_SCOPE_GUIDANCE", original_rule + " Changed reading rule.")
    updated, _ = build_axis_point_reader_snapshot(view, source_view_path=path, subject_identity=_point_reader_subject_identity())
    for before, after in zip(snapshot["points"], updated["points"], strict=True):
        assert (before["point_input_sha256"] != after["point_input_sha256"]) == ("point_actor_scope" in before)
    scoped = next(row for row in snapshot["points"] if "point_actor_scope" in row)
    request = consolidation_runner._point_reader_request(snapshot, scoped, payloads[scoped["point_id"]])
    assert request["actor_scope_rule"] == original_rule
    snapshot["method_binding"]["actor_scope_rule"] += " Tampered rule."
    snapshot.pop("snapshot_sha256")
    snapshot["snapshot_sha256"] = _canonical_json_sha256(snapshot)
    with pytest.raises(EvidenceConsumerError) as caught:
        consolidation_judgment._validate_point_reader_manifest_shape(snapshot, expected_snapshot_sha256=snapshot["snapshot_sha256"])
    assert caught.value.boundary == "point_actor_scope"
    assert "reading rule binding changed" in str(caught.value)


def test_axis_pack_resolves_selection_manifest_embedded_in_relation_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    descriptor = manifest["accepted_points"][0]
    selection_path = Path(descriptor["selection_manifest_path"])
    embedded = json.loads(selection_path.read_text(encoding="utf-8"))
    batch = _manifest(
        schema_version="phase_a_evidence_selection_batch_manifest_v1",
        selection_manifest=embedded,
        batches=[],
    )
    batch_path = tmp_path / "selection_batch_manifest.json"
    _write(batch_path, batch)
    descriptor["selection_manifest_path"] = str(batch_path)
    descriptor["selection_manifest_file_sha256"] = hash_file(batch_path)
    _rehash_manifest(manifest)

    pack = build_phase_a_evidence_axis_pack(manifest)

    assert pack["points"][0]["selection_manifest_path"] == str(batch_path)
    assert (
        pack["points"][0]["selection_manifest_sha256"]
        == embedded["manifest_sha256"]
    )


def _repin_parent_context_candidate_inventory(
    manifest: dict[str, Any], descriptor: dict[str, Any], artifact: dict[str, Any]
) -> None:
    source_inventory = [
        {
            key: value
            for key, value in candidate.items()
            if key not in {"relation", "reason_code", "relation_semantic_unit_refs"}
        }
        for candidate in artifact["candidate_dispositions"]
    ]
    inventory_hash = _canonical_json_sha256(source_inventory)
    selection_path = Path(descriptor["selection_manifest_path"])
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection["parent_context_policy"] = PARENT_CONTEXT_POLICY
    selection["candidate_inventory_sha256"] = inventory_hash
    _rehash_manifest(selection)
    _write(selection_path, selection)
    quote_path = Path(descriptor["quote_manifest_path"])
    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    quote["selection_manifest_sha256"] = selection["manifest_sha256"]
    quote["candidate_inventory_sha256"] = inventory_hash
    _rehash_manifest(quote)
    _write(quote_path, quote)
    artifact["candidate_inventory_sha256"] = inventory_hash
    artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
    artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
    artifact_path = Path(descriptor["artifact_path"])
    _write(artifact_path, artifact)
    descriptor["artifact_sha256"] = hash_file(artifact_path)
    descriptor["selection_manifest_file_sha256"] = hash_file(selection_path)
    descriptor["selection_manifest_sha256"] = selection["manifest_sha256"]
    descriptor["quote_manifest_file_sha256"] = hash_file(quote_path)
    descriptor["quote_manifest_sha256"] = quote["manifest_sha256"]
    _rehash_manifest(manifest)


def test_axis_pack_accepts_current_candidate_relation_bindings_as_derived_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    descriptor = manifest["accepted_points"][0]
    artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
    artifact["schema_version"] = "phase_a_evidence_selection_artifact_v3"
    for candidate in artifact["candidate_dispositions"]:
        candidate["relation_semantic_unit_refs"] = [candidate["semantic_unit_ref"]]
    _repin_parent_context_candidate_inventory(manifest, descriptor, artifact)

    pack = build_phase_a_evidence_axis_pack(manifest)

    assert pack["valid_point_count"] == 2


def test_axis_pack_does_not_reinterpret_candidate_relation_bindings_as_historical_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    descriptor = manifest["accepted_points"][0]
    artifact_path = Path(descriptor["artifact_path"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["candidate_dispositions"][0]["relation_semantic_unit_refs"] = [
        artifact["candidate_dispositions"][0]["semantic_unit_ref"]
    ]
    _repin_parent_context_candidate_inventory(manifest, descriptor, artifact)

    with pytest.raises(
        EvidenceConsumerError, match="candidate disposition inventory changed"
    ) as caught:
        build_phase_a_evidence_axis_pack(manifest)

    assert caught.value.boundary == "candidate_access"


def _route_every_point_as_decision_state(spec: dict[str, Any]) -> None:
    axis_pack = json.loads(Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8"))
    point_ids: list[str] = []
    bindings: list[dict[str, Any]] = []
    for descriptor in axis_pack["points"]:
        point_id = descriptor["point_id"]
        point_ids.append(point_id)
        artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
        row_bindings = []
        for source_group in artifact["source_groups"]:
            for row in source_group["rows"]:
                assertions = [
                    {
                        "state_kind": "value_judgment",
                        "commercial_direction": "favorable",
                        "decision_object": "fixture balm",
                        "semantic_unit_refs": [row["semantic_unit_ref"]],
                        "quantity": None,
                        "conditions": [],
                    }
                ]
                for companion in row["same_evidence_companion_meanings"]:
                    assertions.append(
                        {
                            "state_kind": "preference_judgment",
                            "commercial_direction": "favorable",
                            "decision_object": "fixture balm texture",
                            "semantic_unit_refs": [companion["semantic_unit_ref"]],
                            "quantity": None,
                            "conditions": [],
                        }
                    )
                row_bindings.append(
                    {
                        "selected_id": row["selected_id"],
                        "state_assertions": assertions,
                        "context_only_semantic_unit_refs": [],
                        "relation_semantic_unit_refs": [row["semantic_unit_ref"]],
                    }
                )
        bindings.append({"point_id": point_id, "rows": row_bindings})
    spec["projection_routes"] = [
        {"projection_mode": "decision_state", "point_ids": point_ids}
    ]
    spec["decision_state_bindings"] = bindings


def _bind_current_direct_outcome_relations(
    spec: dict[str, Any],
    *,
    point_ids: set[str] | None = None,
    companion_for: tuple[str, str] | None = None,
) -> None:
    """Author explicit fixture bindings; production code never chooses these refs."""

    axis_pack = json.loads(Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8"))
    bindings: list[dict[str, Any]] = []
    decision_rows = {
        (binding["point_id"], row["selected_id"]): row[
            "relation_semantic_unit_refs"
        ]
        for binding in spec.get("decision_state_bindings", [])
        for row in binding["rows"]
    }
    for descriptor in axis_pack["points"]:
        point_id = descriptor["point_id"]
        artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
        artifact["schema_version"] = "phase_a_evidence_selection_artifact_v3"
        if RELATION_SEMANTIC_WARRANT_BOUNDARY not in artifact["output_boundary"]:
            artifact["output_boundary"].append(RELATION_SEMANTIC_WARRANT_BOUNDARY)
        rows = []
        for source_group in artifact["source_groups"]:
            for row in source_group["rows"]:
                relation_refs = decision_rows.get(
                    (point_id, row["selected_id"]), [row["semantic_unit_ref"]]
                )
                if companion_for == (point_id, row["selected_id"]):
                    relation_refs = [
                        row["same_evidence_companion_meanings"][0]["semantic_unit_ref"]
                    ]
                row["relation_semantic_unit_refs"] = sorted(relation_refs)
                if point_ids is None or point_id in point_ids:
                    rows.append(
                        {
                            "selected_id": row["selected_id"],
                            "relation_semantic_unit_refs": sorted(relation_refs),
                        }
                    )
        artifact_path = Path(descriptor["artifact_path"])
        _write(artifact_path, artifact)
        descriptor["artifact_sha256"] = hash_file(artifact_path)
        if point_ids is None or point_id in point_ids:
            bindings.append({"point_id": point_id, "rows": rows})
    if axis_pack.get("schema_version") == AXIS_PACK_VERSION:
        refreshed_manifest = _manifest(
            schema_version=AXIS_PACK_MANIFEST_VERSION,
            axis_id=axis_pack["axis_id"],
            accepted_points=[
                {
                    key: descriptor[key]
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
                for descriptor in axis_pack["points"]
            ],
            rejected_points=copy.deepcopy(axis_pack["rejected_points"]),
        )
        axis_pack = build_phase_a_evidence_axis_pack(refreshed_manifest)
    axis_path = Path(spec["source_axis_pack_path"])
    _write(axis_path, axis_pack)
    spec["source_axis_pack_sha256"] = hash_file(axis_path)
    spec["schema_version"] = CURRENT_CONSOLIDATION_SPEC_VERSION
    spec["direct_outcome_relation_bindings"] = bindings


def _route_fixture_as_current_mixed(spec: dict[str, Any]) -> tuple[str, str]:
    _route_every_point_as_decision_state(spec)
    direct_point_id = "point_a"
    decision_point_id = "point_b"
    spec["projection_routes"] = [
        {"projection_mode": "direct_outcome", "point_ids": [direct_point_id]},
        {"projection_mode": "decision_state", "point_ids": [decision_point_id]},
    ]
    spec["decision_state_bindings"] = [
        binding
        for binding in spec["decision_state_bindings"]
        if binding["point_id"] == decision_point_id
    ]
    _bind_current_direct_outcome_relations(spec, point_ids={direct_point_id})
    return direct_point_id, decision_point_id


def _synchronize_semantic_binding_row(
    spec: dict[str, Any], authoritative_row: Mapping[str, Any]
) -> None:
    refs = {
        ref
        for assertion in authoritative_row["state_assertions"]
        for ref in assertion["semantic_unit_refs"]
    } | set(authoritative_row["context_only_semantic_unit_refs"])
    for point_binding in spec["decision_state_bindings"]:
        for row in point_binding["rows"]:
            row_refs = {
                ref
                for assertion in row["state_assertions"]
                for ref in assertion["semantic_unit_refs"]
            } | set(row["context_only_semantic_unit_refs"])
            if row is not authoritative_row and row_refs == refs:
                row["state_assertions"] = copy.deepcopy(
                    authoritative_row["state_assertions"]
                )
                row["context_only_semantic_unit_refs"] = copy.deepcopy(
                    authoritative_row["context_only_semantic_unit_refs"]
                )


def _projected_state_assertions(
    view: Mapping[str, Any], group: Mapping[str, Any]
) -> list[dict[str, Any]]:
    columns = view["decision_state_index"]["columns"]
    rows = {row[0]: row for row in view["decision_state_index"]["rows"]}
    return [
        dict(zip(columns[1:], rows[state_id][1:])) for state_id in group["state_ids"]
    ]


def _refresh_axis_binding(spec: dict[str, Any], paths: dict[str, Path]) -> None:
    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    for descriptor in axis["points"]:
        artifact_path = Path(descriptor["artifact_path"])
        descriptor["artifact_sha256"] = hash_file(artifact_path)
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])


def test_build_normalizes_origins_and_separates_post_comment_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)

    assert view["counts"] == {
        "point_count": 2,
        "candidate_disposition_count": 6,
        "placement_count": 4,
        "unique_origin_count": 3,
        "credited_origin_count": 3,
        "uncredited_origin_count": 0,
        "unique_evidence_count": 3,
        "unique_quote_span_count": 3,
        "unique_companion_meaning_count": 1,
        "available_quote_span_count": 3,
        "unavailable_quote_span_count": 0,
    }
    alice = next(row for row in view["origin_index"] if row["independence_key"] == "reddit:alice")
    assert len(alice["placement_ids"]) == 2
    assert alice["independence_posture"] == "credited"
    point_a = next(row for row in view["point_index"] if row["point_id"] == "point_a")
    assert point_a["support_origin_ids"] == ["scope::reddit:alice"]
    assert point_a["counter_origin_ids"] == ["scope::reddit:bob"]
    assert point_a["adjacent_origin_ids"] == []
    assert {row["content_surface"] for row in view["engagement_buckets"]} == {
        "reddit_post",
        "reddit_comment",
        "sephora_review",
    }
    assert view["container_concentrations"] == [
        {
            "container_id": "reddit_thread_thread1",
            "distinct_origin_count": 2,
            "origin_group_ids": ["scope::reddit:alice", "scope::reddit:bob"],
            "evidence_ids": ["reddit:thread1:comment1", "reddit:thread1:post"],
        }
    ]
    assert "candidate_dispositions" not in json.dumps(view)
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view
    assert build_axis_consolidated_view(spec) == view


def test_evidence_identity_ignores_other_evidence_in_same_origin_candidate_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_b"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    post_row = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["evidence_id"] == "reddit:thread1:post"
    )
    other_candidate = next(
        row
        for row in artifact["candidate_dispositions"]
        if row["evidence_id"] != post_row["evidence_id"]
        and isinstance(row.get("container_id"), str)
    )
    post_row["origin_candidate_ids"].append(other_candidate["candidate_id"])
    _write(artifact_path, artifact)
    descriptor = next(
        row for row in manifest["accepted_points"] if row["point_id"] == "point_b"
    )
    descriptor["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(manifest)
    axis_path = paths["generic_axis"]
    _write(axis_path, build_phase_a_evidence_axis_pack(manifest))
    spec["source_axis_pack_sha256"] = hash_file(axis_path)

    view = build_axis_consolidated_view(spec)
    evidence = next(
        row for row in view["evidence_index"] if row["evidence_id"] == "reddit:thread1:post"
    )

    assert other_candidate["container_id"] not in evidence["container_ids"]
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def _bind_shared_foreign_container_candidate(paths: dict[str, Path]) -> None:
    """Give both fixture points one identical extra candidate under a displayed origin.

    `reddit:thread1:post` is displayed by both fixture points, so the extra
    candidate has to be identical in both or the cross-point evidence identity
    guard fails first and the container boundary under test is never reached.
    """
    for point_id in ("point_a", "point_b"):
        artifact_path = paths[f"artifact_{point_id}"]
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact["candidate_dispositions"].append(
            _candidate(
                "candidate_shared_other",
                evidence_id="reddit:thread7:post",
                semantic_ref="reddit:thread7:post::other",
                relation="adjacent",
                origin="scope::reddit:alice",
                container="reddit_thread_thread7",
            )
        )
        post_row = next(
            row
            for group in artifact["source_groups"]
            for row in group["rows"]
            if row["evidence_id"] == "reddit:thread1:post"
        )
        post_row["origin_candidate_ids"].append("candidate_shared_other")
        _write(artifact_path, artifact)


def test_legacy_v1_container_ids_keep_their_frozen_origin_bundle_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A published v1 view must keep the container_ids bytes it was published with.

    The routed v2 projection narrows an evidence row's containers to that
    evidence's own candidates. Applying the same narrowing to v1 silently
    rewrites already published v1 views, so the frozen route keeps the original
    origin-bundle union and only v2 narrows.
    """
    spec, paths = _fixture(tmp_path, monkeypatch)
    _bind_shared_foreign_container_candidate(paths)
    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    for descriptor in axis["points"]:
        descriptor["candidate_count"] = 4
        descriptor["artifact_sha256"] = hash_file(Path(descriptor["artifact_path"]))
    axis["cold_reader_resolution"]["resolved_candidate_disposition_count"] = 8
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])

    routed_view = build_axis_consolidated_view(spec)
    legacy_spec = copy.deepcopy(spec)
    legacy_spec["schema_version"] = LEGACY_CONSOLIDATION_SPEC_VERSION
    legacy_spec.pop("projection_routes")
    legacy_view = build_axis_consolidated_view(legacy_spec)

    def containers(view: Mapping[str, Any]) -> list[str]:
        return next(
            row
            for row in view["evidence_index"]
            if row["evidence_id"] == "reddit:thread1:post"
        )["container_ids"]

    assert containers(routed_view) == ["reddit_thread_thread1"]
    assert containers(legacy_view) == [
        "reddit_thread_thread1",
        "reddit_thread_thread7",
    ]
    assert validate_axis_consolidated_view(
        legacy_view, expected_view_sha256=legacy_view["view_sha256"]
    ) == legacy_view


def test_same_origin_repeated_observation_survives_without_adding_origin_credit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    selected = artifact["source_groups"][0]["rows"][0]
    artifact["candidate_dispositions"].extend(
        [
            _candidate(
                "candidate_a_repeat",
                evidence_id="reddit:thread2:comment2",
                semantic_ref="reddit:thread2:comment2::hydrating",
                relation="support",
                origin="scope::reddit:alice",
                container="reddit_thread_thread2",
                normalized_meaning=selected["normalized_meaning"],
                publication_time="2025-07-02T03:04:05+00:00",
                engagement_value="999 points",
            ),
            # A second candidate id for the same evidence/semantic unit is not a
            # second source observation.
            _candidate(
                "candidate_a_repeat_duplicate",
                evidence_id="reddit:thread2:comment2",
                semantic_ref="reddit:thread2:comment2::hydrating",
                relation="support",
                origin="scope::reddit:alice",
                container="reddit_thread_thread2",
                normalized_meaning=selected["normalized_meaning"],
                publication_time="2025-07-02T03:04:05+00:00",
                engagement_value="999 points",
            ),
            _candidate(
                "candidate_a_other_meaning",
                evidence_id="reddit:thread3:comment3",
                semantic_ref="reddit:thread3:comment3::smooth",
                relation="support",
                origin="scope::reddit:alice",
                container="reddit_thread_thread3",
                normalized_meaning="The balm feels smooth.",
            ),
            _candidate(
                "candidate_other_origin",
                evidence_id="reddit:thread4:comment4",
                semantic_ref="reddit:thread4:comment4::hydrating",
                relation="support",
                origin="scope::reddit:dana",
                container="reddit_thread_thread4",
                normalized_meaning=selected["normalized_meaning"],
            ),
            _candidate(
                "candidate_a_other_relation",
                evidence_id="reddit:thread5:comment5",
                semantic_ref="reddit:thread5:comment5::hydrating",
                relation="counter",
                origin="scope::reddit:alice",
                container="reddit_thread_thread5",
                normalized_meaning=selected["normalized_meaning"],
            ),
        ]
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = 8
    _write(artifact_path, artifact)
    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    point_a = next(row for row in axis["points"] if row["point_id"] == "point_a")
    point_a["candidate_count"] = 8
    point_a["artifact_sha256"] = hash_file(artifact_path)
    axis["cold_reader_resolution"]["resolved_candidate_disposition_count"] = 11
    axis["rejected_points"] = []
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])

    direct_view = build_axis_consolidated_view(spec)
    point = next(row for row in direct_view["point_index"] if row["point_id"] == "point_a")
    assert point["support_origin_ids"] == ["scope::reddit:alice"]
    assert point["displayed_relation_row_counts"]["support"] == 1
    assert len(point["same_origin_observation_groups"]) == 1
    group = point["same_origin_observation_groups"][0]
    assert group["source_observation_count"] == 2
    assert group["layer"] == "truth_support"
    assert group["origin_group_id"] == "scope::reddit:alice"
    assert group["normalized_meaning"] == selected["normalized_meaning"]
    assert [row["evidence_id"] for row in group["observations"]] == [
        "reddit:thread1:post",
        "reddit:thread2:comment2",
    ]
    assert [row["content_surface"] for row in group["observations"]] == [
        "reddit_post",
        "reddit_comment",
    ]
    assert [row["publication_time"] for row in group["observations"]] == [
        "2025-06-01T00:00:00+00:00",
        "2025-07-02T03:04:05+00:00",
    ]
    assert group["observations"][1]["candidate_ids"] == [
        "candidate_a_repeat",
        "candidate_a_repeat_duplicate",
    ]
    assert direct_view["evidence_accounting_contract"] == EVIDENCE_ACCOUNTING_CONTRACT

    _route_every_point_as_decision_state(spec)
    decision_view = build_axis_consolidated_view(spec)
    reader = decision_view["decision_state_reader_surface"]
    assert (
        reader["evidence_accounting_contract"]
        == _reader_evidence_accounting_contract()
    )
    columns = reader["point_table"]["columns"]
    point_row = next(
        row
        for row in reader["point_table"]["rows"]
        if row[columns.index("point_id")] == "point_a"
    )
    assert point_row[columns.index("same_origin_observation_groups")] == [group]
    assert point_row[columns.index("relation_counts")]["support"] == 1
    assert build_axis_consolidated_view(spec) == decision_view


def test_routed_views_keep_bounded_point_authoritative_over_placement_meanings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    expected = (
        "bounded_point on each point row is the authoritative admitted meaning, including "
        "literal comparator, time, and personal-fit terms; placement normalized meanings "
        "are point-relative evidence and may support, counter, qualify, or sit adjacent, "
        "but never broaden, merge, or rewrite the point"
    )
    count_rule = (
        "point relation totals count displayed rows, not origins, people, prevalence, or "
        "same-origin observations; they may exceed distinct-origin counts"
    )

    direct_view = build_axis_consolidated_view(spec)
    assert direct_view["evidence_accounting_contract"]["point_meaning_rule"] == expected
    assert (
        direct_view["evidence_accounting_contract"]["displayed_relation_count_rule"]
        == count_rule
    )
    for point in direct_view["point_index"]:
        assert "authoritative_point_meaning" not in point
        assert point["displayed_relation_row_counts"] == {
            relation: sum(
                placement["point_id"] == point["point_id"]
                and placement["relation"] == relation
                for placement in direct_view["point_placements"]
            )
            for relation in ("support", "counter", "adjacent")
        }

    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    axis["rejected_points"] = []
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])
    _route_every_point_as_decision_state(spec)
    decision_view = build_axis_consolidated_view(spec)
    reader = decision_view["decision_state_reader_surface"]
    compact_accounting = _reader_evidence_accounting_contract()
    assert reader["evidence_accounting_contract"] == compact_accounting
    assert (
        reader["evidence_accounting_contract"]["displayed_relation_count_rule"]
        == compact_accounting["displayed_relation_count_rule"]
    )
    point_columns = reader["point_table"]["columns"]
    assert "bounded_point" in point_columns
    assert "relation_counts" in point_columns
    assert "point_index" not in reader
    assert all(
        "point_index" not in rule and "authoritative_point_meaning" not in rule
        for rule in reader["evidence_accounting_contract"].values()
    )


def test_reader_accounting_contract_rejects_an_authority_key_fork(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        EVIDENCE_ACCOUNTING_CONTRACT,
        "future_accounting_rule",
        "A future authoritative rule must not disappear from the compact reader.",
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        _reader_evidence_accounting_contract()

    assert caught.value.boundary == "decision_state_reader_accounting_contract"


def test_dogfood_truth_index_preserves_observations_states_and_literal_rejections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    selected = artifact["source_groups"][0]["rows"][0]
    artifact["candidate_dispositions"].append(
        _candidate(
            "candidate_a_truth_repeat",
            evidence_id="reddit:thread2:comment2",
            semantic_ref="reddit:thread2:comment2::hydrating",
            relation="support",
            origin="scope::reddit:alice",
            container="reddit_thread_thread2",
            normalized_meaning=selected["normalized_meaning"],
            publication_time="2025-07-02T03:04:05+00:00",
        )
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = 4
    _write(artifact_path, artifact)
    accepted = next(
        row for row in manifest["accepted_points"] if row["point_id"] == "point_a"
    )
    accepted["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(manifest)
    pack = build_phase_a_evidence_axis_pack(manifest)
    _write(paths["generic_axis"], pack)
    spec["source_axis_pack_sha256"] = hash_file(paths["generic_axis"])
    _route_every_point_as_decision_state(spec)
    first_binding = spec["decision_state_bindings"][0]["rows"][0]
    first_binding["state_assertions"][0]["decision_object"] = (
        "Cherry and Brown Sugar scents"
    )
    _synchronize_semantic_binding_row(spec, first_binding)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    _write(view_path, view)

    truth = build_axis_dogfood_truth_index(view, source_view_path=view_path)

    assert truth["schema_version"] == DOGFOOD_TRUTH_INDEX_VERSION
    assert truth["counts"] == {
        "accepted_point_count": 2,
        "rejected_point_count": 1,
        "frontier_point_count": 3,
    }
    assert truth["rejected_points"] == [
        {
            "point_id": "point_rejected",
            "bounded_point": "The balm fixes every lip outcome.",
            "disposition": "point_scope_failed",
            "reason": "broad_axis_or_bundle",
        }
    ]
    point_a = next(row for row in truth["accepted_points"] if row["point_id"] == "point_a")
    assert point_a["same_origin_observation_groups"][0][
        "source_observation_count"
    ] == 2
    assert [
        row["content_surface"]
        for row in point_a["same_origin_observation_groups"][0]["observations"]
    ] == ["reddit_post", "reddit_comment"]
    assert any(
        row[2] == "Cherry and Brown Sugar scents"
        for row in point_a["state_table"]["rows"]
    )
    routed_ids = sorted(
        point_id
        for route in truth["projection_routes"]
        for point_id in route["point_ids"]
    )
    assert routed_ids == ["point_a", "point_b"]
    assert "point_rejected" not in routed_ids
    assert validate_axis_dogfood_truth_index(
        truth, expected_truth_index_sha256=truth["truth_index_sha256"]
    ) == truth


@pytest.mark.parametrize(
    "mutation",
    [
        "derived_disposition",
        "invent_rejected_route",
        "drop_same_origin_observation",
        "drop_decision_state",
    ],
)
def test_dogfood_truth_wrong_cause_reaches_reprojection_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    selected = artifact["source_groups"][0]["rows"][0]
    artifact["candidate_dispositions"].append(
        _candidate(
            "candidate_a_wrong_cause_repeat",
            evidence_id="reddit:thread2:comment2",
            semantic_ref="reddit:thread2:comment2::hydrating",
            relation="support",
            origin="scope::reddit:alice",
            container="reddit_thread_thread2",
            normalized_meaning=selected["normalized_meaning"],
        )
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = 4
    _write(artifact_path, artifact)
    accepted = next(
        row for row in manifest["accepted_points"] if row["point_id"] == "point_a"
    )
    accepted["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(manifest)
    _write(paths["generic_axis"], build_phase_a_evidence_axis_pack(manifest))
    spec["source_axis_pack_sha256"] = hash_file(paths["generic_axis"])
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    _write(view_path, view)
    changed = build_axis_dogfood_truth_index(view, source_view_path=view_path)
    if mutation == "derived_disposition":
        changed["rejected_points"][0]["disposition"] = (
            "nonpromoted_no_investigation_earning_signal"
        )
    elif mutation == "invent_rejected_route":
        changed["projection_routes"][0]["point_ids"].append("point_rejected")
    elif mutation == "drop_same_origin_observation":
        point_a = next(
            row for row in changed["accepted_points"] if row["point_id"] == "point_a"
        )
        point_a["same_origin_observation_groups"][0]["observations"].pop()
        point_a["same_origin_observation_groups"][0]["source_observation_count"] = 1
    else:
        point_a = next(
            row for row in changed["accepted_points"] if row["point_id"] == "point_a"
        )
        point_a["state_table"]["rows"].pop()
    changed.pop("truth_index_sha256")
    changed["truth_index_sha256"] = _canonical_json_sha256(changed)

    with pytest.raises(
        EvidenceConsumerError, match="saved truth index differs"
    ) as caught:
        validate_axis_dogfood_truth_index(
            changed,
            expected_truth_index_sha256=changed["truth_index_sha256"],
        )
    assert caught.value.boundary == "dogfood_truth_index_reprojection"


def test_dogfood_truth_index_refuses_an_absent_rejected_point_frontier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    assert "rejected_point_index" not in view
    view_path = tmp_path / "view.json"
    _write(view_path, view)

    with pytest.raises(
        EvidenceConsumerError, match="no rejected-point frontier"
    ) as caught:
        build_axis_dogfood_truth_index(view, source_view_path=view_path)
    assert caught.value.boundary == "dogfood_truth_index_verification"


def test_axis_reader_bundle_keeps_complete_direct_outcome_facts_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    facts_dir = tmp_path / "reader_facts"
    _write(view_path, view)

    manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, fact_streams)
    facts = _reader_facts(fact_streams)

    assert manifest["schema_version"] == AXIS_READER_MANIFEST_VERSION
    assert manifest["facts_directory"]["fact_count"] == view["counts"]["placement_count"]
    assert all(point["facts_file"]["fact_count"] for point in manifest["points"])
    assert "never redefines or broadens that point" in manifest["reader_rule"]
    assert "never relabel it from the quote" in manifest["reader_rule"]
    assert "give it to any other companion meaning" in manifest["reader_rule"]
    assert "Never describe a whole relation bucket" in manifest["reader_rule"]
    assert "source-surface summary must come from every fact" in manifest["reader_rule"]
    assert "summary labelled representative may name only" in manifest["reader_rule"]
    assert "retain quote_span_id with the point" in manifest["reader_rule"]
    assert "never rewrite the admitted point as an OR-list" in manifest["reader_rule"]
    assert "must copy bounded_point verbatim" in manifest["reader_rule"]
    assert "copy displayed_relation_row_counts" in manifest["reader_rule"]
    assert manifest["rejected_points"] == [
        {
            "point_id": "point_rejected",
            "bounded_point": "The balm fixes every lip outcome.",
            "disposition": "point_scope_failed",
            "reason": "broad_axis_or_bundle",
        }
    ]
    assert len({fact["placement_id"] for fact in facts}) == len(facts)
    assert all(fact["projection_mode"] == "direct_outcome" for fact in facts)
    assert all("decision_state" not in fact for fact in facts)
    assert all(
        {
            "bounded_point",
            "point_relative_meaning",
            "evidence",
            "origin",
            "quote",
            "companion_meanings",
            "parent_contexts",
        }
        <= set(fact)
        for fact in facts
    )
    assert build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    ) == (manifest, fact_streams)
    assert validate_axis_reader_bundle(
        manifest,
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
    ) == (manifest, fact_streams)


def test_axis_reader_accounting_keeps_full_candidate_pool_distinct_from_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    pack_path = paths["generic_axis"]
    pack = json.loads(pack_path.read_text(encoding="utf-8"))

    accounting = build_axis_reader_accounting(
        pack, source_axis_pack_path=pack_path
    )

    assert accounting["schema_version"] == AXIS_READER_ACCOUNTING_VERSION
    assert accounting["status"] == "point_bearing_candidate_accounting"
    point_a = next(
        row for row in accounting["points"] if row["point_id"] == "point_a"
    )
    assert point_a["full_candidate_pool"]["semantic_row_count"] == 3
    assert point_a["full_candidate_pool"]["evidence_item_count"] == 3
    assert point_a["full_candidate_pool"]["origin_count"] == 3
    assert set(point_a["full_candidate_pool"]) == {
        "semantic_row_count",
        "evidence_item_count",
        "origin_count",
        "material_engagement_origin_count",
        "independence_posture_origin_counts",
        "relation_counts",
        "direct_relation_origin_overlap",
        "direct_relation_by_source_role",
    }
    assert point_a["full_candidate_pool"]["relation_counts"] == {
        "adjacent": {
            "semantic_row_count": 1,
            "evidence_item_count": 1,
            "origin_count": 1,
            "material_engagement_origin_count": 0,
        },
        "counter": {
            "semantic_row_count": 1,
            "evidence_item_count": 1,
            "origin_count": 1,
            "material_engagement_origin_count": 0,
        },
        "exclude": {
            "semantic_row_count": 0,
            "evidence_item_count": 0,
            "origin_count": 0,
            "material_engagement_origin_count": 0,
        },
        "support": {
            "semantic_row_count": 1,
            "evidence_item_count": 1,
            "origin_count": 1,
            "material_engagement_origin_count": 0,
        },
    }
    assert point_a["display_panel"]["semantic_row_count"] == 2
    assert point_a["display_panel"]["relation_row_counts"] == {
        "adjacent": 0,
        "counter": 1,
        "support": 1,
    }
    assert set(point_a["display_panel"]) == {
        "semantic_row_count",
        "relation_row_counts",
        "scope",
    }
    assert point_a["full_candidate_pool"]["direct_relation_origin_overlap"] == {
        "support_only": 1,
        "counter_only": 1,
        "both": 0,
    }
    point_b = next(
        row for row in accounting["points"] if row["point_id"] == "point_b"
    )
    assert {
        (row["source_role"], row["relation"])
        for row in point_b["full_candidate_pool"][
            "direct_relation_by_source_role"
        ]
    } == {
        ("community_post", "counter"),
        ("retailer_review", "support"),
    }
    assert "not prevalence" in " ".join(accounting["non_claims"])
    assert build_axis_reader_accounting(
        pack, source_axis_pack_path=pack_path
    ) == accounting
    assert validate_axis_reader_accounting(
        accounting,
        expected_accounting_sha256=accounting["accounting_sha256"],
    ) == accounting

    accounting_path = tmp_path / "reader_accounting.json"
    built = build_reader_accounting_run(
        pack_path=pack_path, output_path=accounting_path
    )
    assert built["model_api_calls"] == 0
    assert validate_reader_accounting_run(
        accounting_path=accounting_path,
        expected_accounting_sha256=built["accounting_sha256"],
    )["status"] == "valid"

    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view_with_accounting.json"
    _write(view_path, view)
    reader, _ = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "reader_facts"
    )
    embedded = next(
        row for row in reader["points"] if row["point_id"] == "point_a"
    )["candidate_pool_accounting"]
    assert embedded == point_a


def test_current_reader_rejects_legacy_hydration_pack_but_replay_still_builds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    pack_path = paths["axis"]
    pack = json.loads(pack_path.read_text(encoding="utf-8"))

    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "legacy_replay_view.json"
    _write(view_path, view)

    with pytest.raises(EvidenceConsumerError) as error:
        build_axis_reader_accounting(pack, source_axis_pack_path=pack_path)

    assert error.value.boundary == "axis_reader_accounting"
    assert "historical replay inputs" in str(error.value)

    with pytest.raises(EvidenceConsumerError) as bundle_error:
        build_axis_reader_bundle(
            view,
            source_view_path=view_path,
            facts_dir=tmp_path / "legacy_reader_facts",
        )
    assert bundle_error.value.boundary == "axis_reader_accounting"
    assert "unsupported source axis pack" in str(bundle_error.value)


def test_axis_reader_accounting_rejects_a_coherently_rehashed_false_full_pool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, paths = _generic_fixture(tmp_path, monkeypatch)
    pack_path = paths["generic_axis"]
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    accounting = build_axis_reader_accounting(
        pack, source_axis_pack_path=pack_path
    )
    accounting["points"][0]["full_candidate_pool"]["relation_counts"][
        "support"
    ]["origin_count"] += 1
    accounting.pop("accounting_sha256")
    accounting["accounting_sha256"] = _canonical_json_sha256(accounting)

    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_reader_accounting(
            accounting,
            expected_accounting_sha256=accounting["accounting_sha256"],
        )
    assert caught.value.boundary == "axis_reader_accounting_reprojection"


def test_reader_instructions_oblige_pool_counts_before_display_balance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The consumer surface, not only the workflow doc, must carry the duty.

    Deterministic validators can prove the accounting arrives; they cannot read
    prose.  The reachable boundary is the instruction the cold reader actually
    receives, so assert the affirmative duty survives into the rendered
    point-reader request and the axis reader contract beside a pool the display
    panel does not cover.
    """

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view_path = tmp_path / "view.json"
    identity_path = tmp_path / "subject.json"
    manifest_path = tmp_path / "run.json"
    store = tmp_path / "point_store"
    view = build_axis_consolidated_view(spec)
    _write(view_path, view)
    _write(identity_path, _point_reader_subject_identity())

    run = build_point_reader_run(
        view_path=view_path,
        subject_identity_path=identity_path,
        manifest_output_path=manifest_path,
        point_store_dir=store,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    point = next(
        row for row in manifest["points"] if row["point_id"] == "point_a"
    )
    request_path = tmp_path / "request.json"
    prepare_point_reader_request_run(
        manifest_path=manifest_path,
        point_store_dir=store,
        point_id=point["point_id"],
        output_path=request_path,
        expected_snapshot_sha256=run["snapshot_sha256"],
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))

    # The request carries strictly more pool than the display panel shows.
    carried = request["candidate_pool_accounting"]
    assert (
        carried["full_candidate_pool"]["semantic_row_count"]
        > carried["display_panel"]["semantic_row_count"]
    )

    # The duty to disclose that gap is affirmative, not merely a prohibition.
    method_text = request["method_text"]
    assert method_text == POINT_READER_METHOD_TEXT
    assert "before characterizing direction or balance" in method_text
    assert "never let the displayed examples stand in for the full pool" in method_text

    reader, _ = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "contract_facts"
    )
    reader_rule = reader["reader_rule"]
    assert "before characterizing direction or balance" in reader_rule
    assert "when useful" not in reader_rule


def test_axis_reader_bundle_keeps_decision_state_and_mixed_routes_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["projection_routes"] = [
        {"projection_mode": "direct_outcome", "point_ids": ["point_a"]},
        {"projection_mode": "decision_state", "point_ids": ["point_b"]},
    ]
    spec["decision_state_bindings"] = [
        binding
        for binding in spec["decision_state_bindings"]
        if binding["point_id"] == "point_b"
    ]
    spec["decision_state_rejected_point_navigation"] = [
        {
            "point_id": "point_rejected",
            "navigation_group_id": "hydration_efficacy",
        }
    ]
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "mixed_view.json"
    facts_dir = tmp_path / "mixed_reader"
    _write(view_path, view)

    manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    facts = _reader_facts(fact_streams)
    direct = [fact for fact in facts if fact["point_id"] == "point_a"]
    decision = [fact for fact in facts if fact["point_id"] == "point_b"]

    assert direct and decision
    assert all("decision_state" not in fact for fact in direct)
    assert all(fact["decision_state"]["state_assertions"] for fact in decision)
    assert all(
        fact["decision_state"]["relation_semantic_unit_refs"]
        == fact["point_relative_meaning"]["relation_semantic_unit_refs"]
        for fact in decision
    )
    assert manifest["rejected_points"][0]["navigation_group_id"] == "hydration_efficacy"


def test_axis_reader_structured_output_fails_loud_on_model_bookkeeping_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    facts_dir = tmp_path / "reader_facts"
    _write(view_path, view)
    manifest, streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, streams)
    output = _structured_reader_output(manifest, streams)

    assert validate_axis_reader_structured_output(
        manifest,
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
        output=output,
    )["status"] == "valid"

    mutations = []
    wrong_pair = copy.deepcopy(output)
    wrong_pair["accepted_points"][0]["bounded_point"] = "A different point."
    mutations.append(wrong_pair)
    broadened = copy.deepcopy(output)
    broadened["accepted_points"][0]["exact_phase_a_meaning"] += " Also glossy."
    mutations.append(broadened)
    wrong_accounting = copy.deepcopy(output)
    wrong_accounting["accepted_points"][0]["reader_accounting"][
        "truth_origin_count"
    ] += 1
    mutations.append(wrong_accounting)
    missing_quote = copy.deepcopy(output)
    missing_quote["accepted_points"][0]["representative_evidence"][0][
        "exact_quote"
    ] = None
    missing_quote["accepted_points"][0]["representative_evidence"][0].pop(
        "quote_span_id"
    )
    mutations.append(missing_quote)
    wrong_handle = copy.deepcopy(output)
    wrong_handle["accepted_points"][0]["representative_evidence"][0][
        "quote_span_id"
    ] = "quote_invented"
    mutations.append(wrong_handle)
    wrong_relation = copy.deepcopy(output)
    wrong_relation["accepted_points"][0]["representative_evidence"][0][
        "relation"
    ] = "invented_relation"
    mutations.append(wrong_relation)

    for candidate in mutations:
        with pytest.raises(
            EvidenceConsumerError, match="axis_reader_output_verification"
        ):
            validate_axis_reader_structured_output(
                manifest,
                facts_dir=facts_dir,
                expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
                output=candidate,
            )


@pytest.mark.parametrize("current_authoring", [False, True])
@pytest.mark.parametrize("quote_mode", ["honest_unavailable", "neighboring_quote"])
def test_structured_reader_checks_companion_quote_ownership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current_authoring: bool,
    quote_mode: str,
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    axis_pack = json.loads(Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8"))
    descriptor = axis_pack["points"][0]
    point_id = descriptor["point_id"]
    artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
    row = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["same_evidence_companion_meanings"]
    )
    companion_ref = row["same_evidence_companion_meanings"][0]["semantic_unit_ref"]
    if current_authoring:
        _bind_current_direct_outcome_relations(
            spec, companion_for=(point_id, row["selected_id"])
        )
    else:
        spec["direct_outcome_relation_bindings"] = [{
            "point_id": point_id,
            "rows": [{
                "selected_id": row["selected_id"],
                "relation_semantic_unit_refs": [companion_ref],
            }],
        }]
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    _write(view_path, view)
    facts_dir = tmp_path / "facts"
    manifest, streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, streams)
    fact = next(
        fact for fact in _reader_facts(streams)
        if fact["point_id"] == point_id and fact["selected_id"] == row["selected_id"]
    )
    assert fact["point_relative_meaning"]["relation_semantic_unit_refs"] == [companion_ref]
    assert fact["quote"]["quote_status"] == "quote_available"
    output = _structured_reader_output(manifest, streams)
    point = next(row for row in output["accepted_points"] if row["point_id"] == point_id)
    point["representative_evidence"] = [{
        "evidence_id": fact["evidence"]["evidence_id"],
        "relation": fact["relation"],
        "quote_span_id": None if quote_mode == "honest_unavailable" else fact["quote"]["quote_span_id"],
        "quote_status": "quote_unavailable" if quote_mode == "honest_unavailable" else "quote_available",
        "exact_quote": None if quote_mode == "honest_unavailable" else fact["quote"]["exact_quote"],
    }]
    # The view, bundle and all source hashes are freshly built and valid. Only
    # relation ownership of the presented quote differs; a stale hash cannot pass.
    if quote_mode == "neighboring_quote":
        with pytest.raises(EvidenceConsumerError, match="relation-owned quote") as caught:
            validate_axis_reader_structured_output(
                manifest, facts_dir=facts_dir,
                expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
                output=output,
            )
        assert caught.value.boundary == "axis_reader_output_verification"
    else:
        assert validate_axis_reader_structured_output(
            manifest, facts_dir=facts_dir,
            expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
            output=output,
        )["status"] == "valid"


def test_axis_reader_output_schema_binds_exact_point_pairs_and_accounting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    _write(view_path, view)
    manifest, _ = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "facts"
    )

    bound = bind_axis_reader_output_schema(manifest, _reader_output_base_schema())
    accounting_variants = bound["properties"]["point_accounting"]["items"][
        "anyOf"
    ]
    accepted_variants = bound["properties"]["accepted_points"]["items"]["anyOf"]

    assert len(accounting_variants) == len(manifest["points"])
    assert len(accepted_variants) == len(manifest["points"])
    assert {
        variant["properties"]["point_id"]["const"]
        for variant in accepted_variants
    } == {point["point_id"] for point in manifest["points"]}
    for variant, point in zip(accepted_variants, manifest["points"], strict=True):
        properties = variant["properties"]
        assert properties["bounded_point"]["const"] == point["bounded_point"]
        assert properties["exact_phase_a_meaning"]["const"] == point["bounded_point"]
        accounting_properties = properties["reader_accounting"]["properties"]
        assert accounting_properties["truth_origin_count"]["const"] == point[
            "truth_origin_count"
        ]
        relation_properties = accounting_properties["displayed_relation_row_counts"][
            "properties"
        ]
        assert {
            relation: relation_properties[relation]["const"]
            for relation in ("support", "counter", "adjacent")
        } == point["displayed_relation_row_counts"]


@pytest.mark.parametrize(
    "mutation",
    (
        "cross_point",
        "wrong_relation",
        "wrong_date",
        "wrong_engagement",
        "wrong_surface",
        "wrong_quote",
        "missing_fact",
    ),
)
def test_axis_reader_bundle_wrong_cause_reaches_reprojection_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / f"view_{mutation}.json"
    facts_dir = tmp_path / f"reader_{mutation}"
    _write(view_path, view)
    manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, fact_streams)
    point_id = sorted(fact_streams)[0]
    facts_path = facts_dir / f"{point_id}.jsonl"
    facts = [
        json.loads(line)
        for line in fact_streams[point_id].decode("utf-8").splitlines()
    ]
    if mutation == "cross_point":
        facts[0]["point_id"] = "point_b"
    elif mutation == "wrong_relation":
        facts[0]["relation"] = "adjacent"
    elif mutation == "wrong_date":
        facts[0]["evidence"]["publication_time"] = "2099-01-01"
    elif mutation == "wrong_engagement":
        facts[0]["evidence"]["engagement"]["raw_value"] = "invented"
    elif mutation == "wrong_surface":
        facts[0]["evidence"]["content_surface"] = "reddit_post"
    elif mutation == "wrong_quote":
        facts[0]["quote"]["exact_quote"] = "invented quote"
    else:
        facts.pop()
    changed_bytes = b"".join(
        json.dumps(
            fact, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        + b"\n"
        for fact in facts
    )
    facts_path.write_bytes(changed_bytes)
    point_manifest = next(
        point for point in manifest["points"] if point["point_id"] == point_id
    )
    point_manifest["facts_file"]["raw_sha256"] = hash_file(facts_path)
    point_manifest["facts_file"]["fact_count"] = len(facts)
    manifest["facts_directory"]["fact_count"] = sum(
        point["facts_file"]["fact_count"] for point in manifest["points"]
    )
    _rehash_reader_manifest(manifest)

    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_reader_bundle(
            manifest,
            facts_dir=facts_dir,
            expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
        )
    assert caught.value.boundary == "axis_reader_bundle_reprojection"


def test_axis_reader_bundle_rejects_state_transition_tamper_at_reprojection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "state_view.json"
    facts_dir = tmp_path / "state_reader"
    _write(view_path, view)
    manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, fact_streams)
    point_id = sorted(fact_streams)[0]
    facts_path = facts_dir / f"{point_id}.jsonl"
    facts = [
        json.loads(line)
        for line in fact_streams[point_id].decode("utf-8").splitlines()
    ]
    facts[0]["decision_state"]["state_assertions"][0]["state_kind"] = (
        "observed_repurchase"
    )
    changed_bytes = b"".join(
        json.dumps(
            fact, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        + b"\n"
        for fact in facts
    )
    facts_path.write_bytes(changed_bytes)
    point_manifest = next(
        point for point in manifest["points"] if point["point_id"] == point_id
    )
    point_manifest["facts_file"]["raw_sha256"] = hash_file(facts_path)
    _rehash_reader_manifest(manifest)

    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_reader_bundle(
            manifest,
            facts_dir=facts_dir,
            expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
        )
    assert caught.value.boundary == "axis_reader_bundle_reprojection"


def test_axis_reader_structured_output_rejects_a_non_literal_representative_quote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-string quote must fail loud here, not crash the evidence check."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    facts_dir = tmp_path / "reader_facts"
    _write(view_path, view)
    manifest, streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_dir
    )
    _write_reader_facts(facts_dir, streams)

    for wrong_quote in ([], {}, 12, True):
        output = _structured_reader_output(manifest, streams)
        output["accepted_points"][0]["representative_evidence"][0][
            "exact_quote"
        ] = wrong_quote
        with pytest.raises(EvidenceConsumerError) as caught:
            validate_axis_reader_structured_output(
                manifest,
                facts_dir=facts_dir,
                expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
                output=output,
            )
        assert caught.value.boundary == "axis_reader_output_verification"


def test_axis_reader_output_schema_binding_rejects_an_incompatible_base_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A constant pinned onto an incompatible declared type is unsatisfiable."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    _write(view_path, view)
    manifest, _ = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "facts"
    )

    integer_count_as_string = _reader_output_base_schema()
    integer_count_as_string["properties"]["accepted_points"]["items"]["properties"][
        "reader_accounting"
    ]["properties"]["truth_origin_count"]["type"] = "string"
    string_point_id_as_integer = _reader_output_base_schema()
    string_point_id_as_integer["properties"]["point_accounting"]["items"][
        "properties"
    ]["point_id"]["type"] = "integer"
    object_accounting_as_array = _reader_output_base_schema()
    object_accounting_as_array["properties"]["accepted_points"]["items"][
        "properties"
    ]["reader_accounting"]["type"] = "array"

    for base_schema in (
        integer_count_as_string,
        string_point_id_as_integer,
        object_accounting_as_array,
    ):
        with pytest.raises(EvidenceConsumerError) as caught:
            bind_axis_reader_output_schema(manifest, base_schema)
        assert caught.value.boundary == "axis_reader_output_schema_binding"

    unchanged = bind_axis_reader_output_schema(manifest, _reader_output_base_schema())
    assert unchanged["properties"]["accepted_points"]["items"]["anyOf"]


def test_generic_axis_pack_preserves_same_origin_repeated_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    selected = artifact["source_groups"][0]["rows"][0]
    artifact["candidate_dispositions"].append(
        _candidate(
            "candidate_a_generic_repeat",
            evidence_id="reddit:thread2:comment2",
            semantic_ref="reddit:thread2:comment2::hydrating",
            relation="support",
            origin="scope::reddit:alice",
            container="reddit_thread_thread2",
            normalized_meaning=selected["normalized_meaning"],
            publication_time="2025-07-02T03:04:05+00:00",
        )
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = 4
    _write(artifact_path, artifact)
    accepted = next(
        row for row in manifest["accepted_points"] if row["point_id"] == "point_a"
    )
    accepted["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(manifest)
    pack = build_phase_a_evidence_axis_pack(manifest)
    _write(paths["generic_axis"], pack)
    spec["source_axis_pack_sha256"] = hash_file(paths["generic_axis"])

    view = build_axis_consolidated_view(spec)

    point = next(row for row in view["point_index"] if row["point_id"] == "point_a")
    assert point["same_origin_observation_groups"][0]["source_observation_count"] == 2


def test_same_origin_posture_conflict_fails_before_single_observation_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    selected = artifact["source_groups"][0]["rows"][0]
    artifact["candidate_dispositions"].append(
        _candidate(
            "candidate_a_conflicting_posture",
            evidence_id=selected["evidence_id"],
            semantic_ref=selected["semantic_unit_ref"],
            relation=selected["relation"],
            origin=selected["origin_group_id"],
            container="reddit_thread_thread1",
            independence_posture="unavailable",
            normalized_meaning=selected["normalized_meaning"],
        )
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = 4
    _write(artifact_path, artifact)
    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    point_a = next(row for row in axis["points"] if row["point_id"] == "point_a")
    point_a["candidate_count"] = 4
    point_a["artifact_sha256"] = hash_file(artifact_path)
    axis["cold_reader_resolution"]["resolved_candidate_disposition_count"] = 7
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])

    with pytest.raises(
        EvidenceConsumerError,
        match="same-origin observation posture changed",
    ):
        build_axis_consolidated_view(spec)


def test_legacy_v1_does_not_gain_evidence_accounting_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec["schema_version"] = LEGACY_CONSOLIDATION_SPEC_VERSION
    spec.pop("projection_routes")

    view = build_axis_consolidated_view(spec)

    assert "evidence_accounting_contract" not in view
    assert all(
        "same_origin_observation_groups" not in point
        for point in view["point_index"]
    )


def test_v2_direct_outcome_routes_every_point_and_carries_existing_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)

    assert view["schema_version"] == CONSOLIDATED_VIEW_VERSION
    assert view["projection_routes"] == spec["projection_routes"]
    assert {row["projection_mode"] for row in view["point_index"]} == {
        "direct_outcome"
    }
    assert all(boundary in view["non_claims"] for boundary in DIRECT_OUTCOME_BOUNDARIES)


def test_decision_state_projects_typed_companion_states_and_rejected_frontier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["decision_state_rejected_point_navigation"] = [
        {
            "point_id": "point_rejected",
            "navigation_group_id": "hydration_efficacy",
        }
    ]

    view = build_axis_consolidated_view(spec)

    assert view["counts"]["decision_state_group_count"] == 4
    assert view["counts"]["decision_state_assertion_count"] == 6
    assert view["counts"]["rejected_point_count"] == 1
    assert view["rejected_point_index"] == [
        {
            "point_id": "point_rejected",
            "bounded_point": "The balm fixes every lip outcome.",
            "disposition": "point_scope_failed",
            "reason": "broad_axis_or_bundle",
            "navigation_group_id": "hydration_efficacy",
        }
    ]
    placements = {row["placement_id"]: row for row in view["point_placements"]}
    post_groups = [
        group
        for group in view["decision_state_groups"]
        if placements[group["placement_id"]]["evidence_id"] == "reddit:thread1:post"
    ]
    assert all(
        {state["state_kind"] for state in _projected_state_assertions(view, group)}
        == {"value_judgment", "preference_judgment"}
        for group in post_groups
    )
    assert {placements[group["placement_id"]]["relation"] for group in post_groups} == {
        "support",
        "counter",
    }
    assert all(boundary in view["non_claims"] for boundary in DECISION_STATE_BOUNDARIES)
    assert view["decision_state_contract"] == DECISION_STATE_CONSUMER_CONTRACT
    reader = view["decision_state_reader_surface"]
    assert reader["schema_version"] == "phase_a_evidence_decision_state_reader_surface_v3"
    assert reader["decision_state_contract"]["state_row_columns"] == [
        "state_kind",
        "commercial_direction",
        "decision_object",
        "semantic_unit_row_ids",
        "quantity",
        "conditions",
    ]
    reader_join_order = " ".join(
        reader["decision_state_contract"]["consumer_join_order"]
    )
    for absent_table in (
        "decision_state_groups",
        "point_placements",
        "decision_state_index",
        "companion_meaning_index",
        "qualification_refs",
        "placement_table",
    ):
        assert absent_table not in reader_join_order
    for present_table in (
        "point_table",
        "evidence_table",
        "semantic_unit_table",
        "quote_table",
    ):
        assert present_table in reader_join_order
    assert "placement_table" not in reader
    assert len(reader["point_table"]["rows"]) == view["counts"]["point_count"]
    assert len(reader["evidence_table"]["rows"]) == view["counts"]["unique_evidence_count"]
    point_columns = reader["point_table"]["columns"]
    relation_index = point_columns.index("relation_counts")
    assert sum(
        sum(row[relation_index].values()) for row in reader["point_table"]["rows"]
    ) == view["counts"]["placement_count"]
    relation_facts_index = point_columns.index("relation_facts")
    assert sum(
        len(row[relation_facts_index]["rows"])
        for row in reader["point_table"]["rows"]
    ) == view["counts"]["placement_count"]
    evidence_id_index = reader["evidence_table"]["columns"].index("evidence_id")
    quote_span_id_index = reader["quote_table"]["columns"].index("quote_span_id")
    for point_row in reader["point_table"]["rows"]:
        facts = point_row[relation_facts_index]
        evidence_fact_index = facts["columns"].index("evidence_id")
        evidence_row_index = facts["columns"].index("evidence_row_id")
        quote_span_fact_index = facts["columns"].index("quote_span_id")
        quote_row_index = facts["columns"].index("quote_row_id")
        relation_semantic_rows_index = facts["columns"].index(
            "relation_semantic_unit_row_ids"
        )
        for fact in facts["rows"]:
            assert fact[relation_semantic_rows_index]
            assert all(
                0 <= row_id < len(reader["semantic_unit_table"]["rows"])
                for row_id in fact[relation_semantic_rows_index]
            )
            assert (
                reader["evidence_table"]["rows"][fact[evidence_row_index]][
                    evidence_id_index
                ]
                == fact[evidence_fact_index]
            )
            assert (
                reader["quote_table"]["rows"][fact[quote_row_index]][
                    quote_span_id_index
                ]
                == fact[quote_span_fact_index]
            )
    assert "state assertions are exhaustive" in view["decision_state_contract"]["unasserted_state_rule"]
    assert "every placement exactly once" in view["decision_state_contract"]["placement_processing_rule"]
    assert "descriptive context only" in view["decision_state_contract"]["engagement_rule"]
    assert "coexistence only" in view["decision_state_contract"]["coexistence_rule"]
    assert build_axis_consolidated_view(spec) == view
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def test_decision_state_keeps_price_value_and_premium_meanings_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    row = spec["decision_state_bindings"][0]["rows"][0]
    primary_ref = row["state_assertions"][0]["semantic_unit_refs"][0]
    companion_ref = row["state_assertions"][1]["semantic_unit_refs"][0]
    row["state_assertions"] = [
        {
            "state_kind": "price_concern",
            "commercial_direction": "friction",
            "decision_object": "fixture balm relative to cheaper substitutes",
            "semantic_unit_refs": [primary_ref],
            "quantity": None,
            "conditions": ["at $24"],
        },
        {
            "state_kind": "value_judgment",
            "commercial_direction": "favorable",
            "decision_object": "fixture balm at $24",
            "semantic_unit_refs": [primary_ref],
            "quantity": None,
            "conditions": [],
        },
        {
            "state_kind": "repurchase_intent",
            "commercial_direction": "toward_action",
            "decision_object": "fixture balm",
            "semantic_unit_refs": [primary_ref],
            "quantity": None,
            "conditions": ["at $24"],
        },
        {
            "state_kind": "observed_repurchase",
            "commercial_direction": "toward_action",
            "decision_object": "fixture balm",
            "semantic_unit_refs": [companion_ref],
            "quantity": None,
            "conditions": [],
        },
        {
            "state_kind": "multi_unit_purchase",
            "commercial_direction": "toward_action",
            "decision_object": "fixture balm",
            "semantic_unit_refs": [companion_ref],
            "quantity": 4,
            "conditions": [],
        },
    ]
    _synchronize_semantic_binding_row(spec, row)

    view = build_axis_consolidated_view(spec)
    placement = next(
        item
        for item in view["point_placements"]
        if item["point_id"] == "point_a" and item["selected_id"] == "selected_01"
    )
    group = next(
        item
        for item in view["decision_state_groups"]
        if item["placement_id"] == placement["placement_id"]
    )
    states = {
        item["state_kind"]: item for item in _projected_state_assertions(view, group)
    }

    assert states["price_concern"]["commercial_direction"] == "friction"
    assert states["price_concern"]["conditions"] == ["at $24"]
    assert (
        states["price_concern"]["decision_object"]
        == "fixture balm relative to cheaper substitutes"
    )
    assert states["value_judgment"]["commercial_direction"] == "favorable"
    assert states["value_judgment"]["decision_object"] == "fixture balm at $24"
    assert states["repurchase_intent"]["conditions"] == ["at $24"]
    assert view["decision_state_contract"]["state_kind_stages"][
        "repurchase_intent"
    ] == "intent"
    assert view["decision_state_contract"]["state_kind_stages"][
        "observed_repurchase"
    ] == "observed"
    assert states["observed_repurchase"]["quantity"] is None
    assert states["multi_unit_purchase"]["quantity"] == 4
    assert not {
        "premium",
        "premium_acceptance",
        "pricing_power",
        "tier_potential",
    } & set(view["decision_state_contract"]["state_kind_stages"])
    assert any(
        "expensive for a lip balm" in boundary
        and "overpriced" in boundary
        and "explicit value rejection" in boundary
        for boundary in view["non_claims"]
    )
    assert any(
        "premium describes source-supported quality or positioning" in boundary
        and "not price alone" in boundary
        and "pricing power" in boundary
        and "higher tier" in boundary
        for boundary in view["non_claims"]
    )


def test_mixed_projection_routes_keep_direct_and_decision_points_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["projection_routes"] = [
        {"projection_mode": "direct_outcome", "point_ids": ["point_a"]},
        {"projection_mode": "decision_state", "point_ids": ["point_b"]},
    ]
    spec["decision_state_bindings"] = [
        binding
        for binding in spec["decision_state_bindings"]
        if binding["point_id"] == "point_b"
    ]

    view = build_axis_consolidated_view(spec)

    point_modes = {row["point_id"]: row["projection_mode"] for row in view["point_index"]}
    assert point_modes == {"point_a": "direct_outcome", "point_b": "decision_state"}
    placements = {row["placement_id"]: row for row in view["point_placements"]}
    assert {
        placements[row["placement_id"]]["point_id"]
        for row in view["decision_state_groups"]
    } == {"point_b"}


def test_decision_state_retains_direct_result_row_as_explicit_context_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    row = spec["decision_state_bindings"][0]["rows"][0]
    all_refs = [
        assertion_ref
        for assertion in row["state_assertions"]
        for assertion_ref in assertion["semantic_unit_refs"]
    ]
    row["state_assertions"] = []
    row["context_only_semantic_unit_refs"] = all_refs
    _synchronize_semantic_binding_row(spec, row)

    view = build_axis_consolidated_view(spec)
    placement = next(
        item
        for item in view["point_placements"]
        if item["point_id"] == "point_a" and item["selected_id"] == "selected_01"
    )
    group = next(
        item
        for item in view["decision_state_groups"]
        if item["placement_id"] == placement["placement_id"]
    )

    assert group["state_ids"] == []
    assert group["qualification_refs"] == sorted(all_refs)
    assert view["counts"]["decision_state_group_count"] == 4
    assert view["counts"]["decision_state_assertion_count"] == 2
    assert "empty state_ids means no judgment" in view["decision_state_contract"][
        "context_only_row_rule"
    ]
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def test_decision_state_allows_primary_result_context_with_companion_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    row = spec["decision_state_bindings"][0]["rows"][0]
    primary_ref = row["state_assertions"][0]["semantic_unit_refs"][0]
    row["state_assertions"].pop(0)
    row["context_only_semantic_unit_refs"].append(primary_ref)
    _synchronize_semantic_binding_row(spec, row)

    view = build_axis_consolidated_view(spec)
    placement = next(
        item
        for item in view["point_placements"]
        if item["point_id"] == "point_a" and item["selected_id"] == "selected_01"
    )
    group = next(
        item
        for item in view["decision_state_groups"]
        if item["placement_id"] == placement["placement_id"]
    )

    assert len(group["state_ids"]) == 1
    assert primary_ref in group["qualification_refs"]
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def test_decision_state_rejects_point_context_changing_one_semantic_unit_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    point_a = next(
        row for row in spec["decision_state_bindings"] if row["point_id"] == "point_a"
    )
    point_b = next(
        row for row in spec["decision_state_bindings"] if row["point_id"] == "point_b"
    )
    shared_ref = point_a["rows"][0]["state_assertions"][0]["semantic_unit_refs"][0]
    assertion = next(
        assertion
        for row in point_b["rows"]
        for assertion in row["state_assertions"]
        if shared_ref in assertion["semantic_unit_refs"]
    )
    assertion["decision_object"] = "point-context-biased reinterpretation"

    with pytest.raises(
        EvidenceConsumerError,
        match="semantic unit changes state meaning across points",
    ):
        build_axis_consolidated_view(spec)


def test_decision_state_distinguishes_release_and_finish_intent_from_other_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    first = spec["decision_state_bindings"][0]["rows"][0]["state_assertions"][0]
    second = spec["decision_state_bindings"][0]["rows"][1]["state_assertions"][0]
    first.update(
        {
            "state_kind": "assortment_request",
            "commercial_direction": "toward_action",
            "decision_object": "a mauve Lip Butter Balm release",
        }
    )
    second.update(
        {
            "state_kind": "use_completion_intent",
            "commercial_direction": "toward_action",
            "decision_object": "finishing the owned balm",
        }
    )
    _synchronize_semantic_binding_row(spec, spec["decision_state_bindings"][0]["rows"][0])
    _synchronize_semantic_binding_row(spec, spec["decision_state_bindings"][0]["rows"][1])

    view = build_axis_consolidated_view(spec)
    assert view["decision_state_contract"]["state_kind_stages"][
        "assortment_request"
    ] == "intent"
    assert view["decision_state_contract"]["state_kind_stages"][
        "use_completion_intent"
    ] == "intent"
    assert view["decision_state_contract"]["state_kind_stages"]["trial_intent"] == "intent"
    assert view["decision_state_contract"]["state_kind_stages"]["acquisition"] == "observed"
    kinds = {
        assertion["state_kind"]
        for group in view["decision_state_groups"]
        for assertion in _projected_state_assertions(view, group)
    }
    assert {"assortment_request", "use_completion_intent"} <= kinds
    assert "purchase_intent" not in {
        assertion["state_kind"]
        for assertion in _projected_state_assertions(
            view,
            next(
                group
                for group in view["decision_state_groups"]
                if group["placement_id"]
                == next(
                    item["placement_id"]
                    for item in view["point_placements"]
                    if item["point_id"] == "point_a"
                    and item["selected_id"] == "selected_01"
                )
            ),
        )
    }


def test_decision_state_preserves_expectation_judgment_as_its_own_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    row = spec["decision_state_bindings"][0]["rows"][0]
    row["state_assertions"][0].update(
        {
            "state_kind": "expectation_judgment",
            "commercial_direction": "unfavorable",
            "decision_object": "fixture balm relative to its hype",
        }
    )
    _synchronize_semantic_binding_row(spec, row)

    view = build_axis_consolidated_view(spec)

    assert view["decision_state_contract"]["state_kind_stages"][
        "expectation_judgment"
    ] == "judgment"
    assert any(
        assertion["state_kind"] == "expectation_judgment"
        and assertion["commercial_direction"] == "unfavorable"
        and assertion["decision_object"] == "fixture balm relative to its hype"
        for group in view["decision_state_groups"]
        for assertion in _projected_state_assertions(view, group)
    )


def test_decision_state_keeps_selected_zero_engagement_without_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    for point_id in ("point_a", "point_b"):
        artifact_path = paths[f"artifact_{point_id}"]
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        row = next(
            row
            for group in artifact["source_groups"]
            for row in group["rows"]
            if row["evidence_id"] == "reddit:thread1:post"
        )
        row["engagement_raw_value"] = "0 points"
        candidate = next(
            row
            for row in artifact["candidate_dispositions"]
            if row["evidence_id"] == "reddit:thread1:post"
        )
        candidate.update(
            {
                "engagement_status": "engagement_available",
                "engagement_context": "reddit_post",
                "engagement_material_positive": False,
            }
        )
        _write(artifact_path, artifact)
        point = next(
            row for row in manifest["accepted_points"] if row["point_id"] == point_id
        )
        point["artifact_sha256"] = hash_file(artifact_path)
    axis_path = paths["generic_axis"]
    _rehash_manifest(manifest)
    _write(axis_path, build_phase_a_evidence_axis_pack(manifest))
    spec["source_axis_pack_sha256"] = hash_file(axis_path)
    _route_every_point_as_decision_state(spec)

    view = build_axis_consolidated_view(spec)
    evidence = next(
        row for row in view["evidence_index"] if row["evidence_id"] == "reddit:thread1:post"
    )

    assert evidence["engagement"] == {
        "kind": "score_state",
        "status": "engagement_available",
        "raw_value": "0 points",
        "observed_at": None,
        "context": "reddit_post",
        "material_positive": False,
    }
    assert "promoted" not in evidence["engagement"]
    placements = {row["placement_id"]: row for row in view["point_placements"]}
    assert any(
        placements[row["placement_id"]]["evidence_id"] == evidence["evidence_id"]
        for row in view["decision_state_groups"]
    )
    reader_evidence = _reader_row(
        view["decision_state_reader_surface"]["evidence_table"],
        "evidence_id",
        evidence["evidence_id"],
    )
    assert reader_evidence["engagement_status"] == "engagement_available"
    assert reader_evidence["engagement_raw_value"] == "0 points"
    assert reader_evidence["engagement_context"] == "reddit_post"


def _reader_rows(table: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(table["columns"], row)) for row in table["rows"]]


def _reader_row(table: Mapping[str, Any], key: str, value: Any) -> dict[str, Any]:
    return next(row for row in _reader_rows(table) if row[key] == value)


def test_decision_state_rejects_spec_authored_parent_context_before_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["decision_state_bindings"][0]["rows"][0]["parent_contexts"] = [
        {
            "context_id": "totally-made-up",
            "source_ref": "https://example.invalid/parent",
            "text": "A parent prompt that never existed in the captured corpus.",
        }
    ]

    with pytest.raises(EvidenceConsumerError) as caught:
        build_axis_consolidated_view(spec)

    assert caught.value.boundary == "decision_state_binding"
    assert "row binding fields are invalid" in str(caught.value)


def test_reader_surface_derivations_recover_point_relation_origins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)

    view = build_axis_consolidated_view(spec)
    reader = view["decision_state_reader_surface"]
    origin_by_evidence = {
        row["evidence_id"]: row["origin_group_id"]
        for row in _reader_rows(reader["evidence_table"])
    }

    # Point relation facts now carry the complete compact join; no duplicate
    # placement table is needed.
    assert "placement_table" not in reader
    assert "relation_facts" in reader["derivation_rules"][
        "point_placement_and_relation_origins"
    ]

    for point_row in _reader_rows(reader["point_table"]):
        derived: dict[str, set[str]] = {"support": set(), "counter": set(), "adjacent": set()}
        for fact in _reader_rows(point_row["relation_facts"]):
            derived[fact["relation"]].add(origin_by_evidence[fact["evidence_id"]])
        point = next(
            row for row in view["point_index"] if row["point_id"] == point_row["point_id"]
        )
        assert sorted(derived["support"]) == point["support_origin_ids"]
        assert sorted(derived["counter"]) == point["counter_origin_ids"]
        assert sorted(derived["adjacent"]) == point["adjacent_origin_ids"]


def test_candidate_inventory_rejects_rewritten_parent_context_before_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    for candidate in artifact["candidate_dispositions"]:
        candidate["parent_context"] = []
    source_shaped_candidates = [
        {
            key: value
            for key, value in candidate.items()
            if key not in {"relation", "reason_code"}
        }
        for candidate in artifact["candidate_dispositions"]
    ]
    inventory_hash = _canonical_json_sha256(source_shaped_candidates)
    point = next(
        row for row in manifest["accepted_points"] if row["point_id"] == "point_a"
    )
    selection_path = Path(point["selection_manifest_path"])
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection["parent_context_policy"] = PARENT_CONTEXT_POLICY
    selection["candidate_inventory_sha256"] = inventory_hash
    _rehash_manifest(selection)
    _write(selection_path, selection)
    quote_path = Path(point["quote_manifest_path"])
    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    quote["selection_manifest_sha256"] = selection["manifest_sha256"]
    quote["candidate_inventory_sha256"] = inventory_hash
    _rehash_manifest(quote)
    _write(quote_path, quote)
    artifact["candidate_inventory_sha256"] = inventory_hash
    artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
    artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
    artifact["candidate_dispositions"][0]["parent_context"] = [
        {
            "context_id": "totally-made-up",
            "source_ref": "https://example.invalid/parent",
            "text": "A parent prompt that never existed in the captured corpus.",
        }
    ]
    _write(artifact_path, artifact)
    point["artifact_sha256"] = hash_file(artifact_path)
    point["selection_manifest_file_sha256"] = hash_file(selection_path)
    point["selection_manifest_sha256"] = selection["manifest_sha256"]
    point["quote_manifest_file_sha256"] = hash_file(quote_path)
    point["quote_manifest_sha256"] = quote["manifest_sha256"]
    _rehash_manifest(manifest)

    with pytest.raises(EvidenceConsumerError) as caught:
        build_phase_a_evidence_axis_pack(manifest)

    assert caught.value.boundary == "candidate_access"
    assert "candidate disposition inventory changed" in str(caught.value)


def test_reader_evidence_row_handle_rejects_a_wrong_exact_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    reader = copy.deepcopy(
        build_axis_consolidated_view(spec)["decision_state_reader_surface"]
    )
    reader["parent_context_table"]["rows"] = [
        [
            "context_1",
            "https://www.reddit.com/r/test/comments/parent1/prompt/",
            "Exact parent question 1?",
        ],
        [
            "context_2",
            "https://www.reddit.com/r/test/comments/parent2/prompt/",
            "Exact parent question 2?",
        ],
    ]
    assert reader["parent_context_table"]["columns"] == [
        "context_id",
        "source_ref",
        "text",
    ]
    quote_role = reader["decision_state_contract"]["quote_role"]
    assert "context rather than evidence" in quote_role
    assert "source role and date are unavailable" in quote_role
    assert "venue and surface remain recoverable from source_ref" in quote_role
    point_columns = reader["point_table"]["columns"]
    facts = reader["point_table"]["rows"][0][
        point_columns.index("relation_facts")
    ]
    context_ids_index = facts["columns"].index("parent_context_ids")
    context_rows_index = facts["columns"].index("parent_context_row_ids")
    facts["rows"][0][context_ids_index] = ["context_1"]
    facts["rows"][0][context_rows_index] = [0]
    facts["rows"][1][context_ids_index] = ["context_2"]
    facts["rows"][1][context_rows_index] = [1]
    fact = facts["rows"][0]
    evidence_row_id_index = facts["columns"].index("evidence_row_id")
    evidence_id_index = facts["columns"].index("evidence_id")
    evidence_table_id_index = reader["evidence_table"]["columns"].index(
        "evidence_id"
    )
    original_row_id = fact[evidence_row_id_index]
    wrong_row_id = next(
        row_id
        for row_id, row in enumerate(reader["evidence_table"]["rows"])
        if row_id != original_row_id
        and row[evidence_table_id_index] != fact[evidence_id_index]
    )
    fact[evidence_row_id_index] = wrong_row_id

    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_decision_state_reader_evidence_rows(reader)

    assert caught.value.boundary == "decision_state_reader_evidence_binding"

    reader = copy.deepcopy(
        build_axis_consolidated_view(spec)["decision_state_reader_surface"]
    )
    reader["parent_context_table"]["rows"] = [
        [
            "context_1",
            "https://www.reddit.com/r/test/comments/parent1/prompt/",
            "Exact parent question 1?",
        ],
        [
            "context_2",
            "https://www.reddit.com/r/test/comments/parent2/prompt/",
            "Exact parent question 2?",
        ],
    ]
    point_columns = reader["point_table"]["columns"]
    facts = reader["point_table"]["rows"][0][
        point_columns.index("relation_facts")
    ]
    context_ids_index = facts["columns"].index("parent_context_ids")
    context_rows_index = facts["columns"].index("parent_context_row_ids")
    context_fact = facts["rows"][0]
    context_fact[context_ids_index] = ["context_1"]
    context_fact[context_rows_index] = [1]

    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_decision_state_reader_evidence_rows(reader)

    assert caught.value.boundary == "decision_state_reader_evidence_binding"

    reader = copy.deepcopy(
        build_axis_consolidated_view(spec)["decision_state_reader_surface"]
    )
    point_columns = reader["point_table"]["columns"]
    facts = reader["point_table"]["rows"][0][
        point_columns.index("relation_facts")
    ]
    relation_semantic_rows_index = facts["columns"].index(
        "relation_semantic_unit_row_ids"
    )
    fact = facts["rows"][0]
    context_only_index = facts["columns"].index(
        "context_only_semantic_unit_row_ids"
    )
    foreign_semantic_row_id = facts["rows"][1][relation_semantic_rows_index][0]
    facts["rows"][0][relation_semantic_rows_index] = [foreign_semantic_row_id]
    facts["rows"][0][context_only_index] = [foreign_semantic_row_id]

    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_decision_state_reader_evidence_rows(reader)

    assert caught.value.boundary == "decision_state_reader_evidence_binding"
    assert "semantic rows do not belong" in str(caught.value)

    reader = copy.deepcopy(
        build_axis_consolidated_view(spec)["decision_state_reader_surface"]
    )
    point_columns = reader["point_table"]["columns"]
    facts = reader["point_table"]["rows"][0][
        point_columns.index("relation_facts")
    ]
    fact = facts["rows"][0]
    relation_semantic_rows_index = facts["columns"].index(
        "relation_semantic_unit_row_ids"
    )
    context_only_index = facts["columns"].index(
        "context_only_semantic_unit_row_ids"
    )
    relation_state_index = facts["columns"].index("relation_state_row_ids")
    state_table = reader["point_table"]["rows"][0][
        point_columns.index("state_table")
    ]
    foreign_state_row = copy.deepcopy(
        state_table["rows"][fact[relation_state_index][0]]
    )
    foreign_state_row[state_table["columns"].index("state_kind")] = (
        "preference_judgment"
    )
    state_table["rows"].append(foreign_state_row)
    fact[context_only_index] = list(fact[relation_semantic_rows_index])
    fact[relation_state_index] = [len(state_table["rows"]) - 1]

    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_decision_state_reader_evidence_rows(reader)

    assert caught.value.boundary == "decision_state_reader_evidence_binding"
    assert "state row identity does not match" in str(caught.value)

    reader = copy.deepcopy(
        build_axis_consolidated_view(spec)["decision_state_reader_surface"]
    )
    point_columns = reader["point_table"]["columns"]
    facts = reader["point_table"]["rows"][0][
        point_columns.index("relation_facts")
    ]
    fact = facts["rows"][0]
    quote_row_id_index = facts["columns"].index("quote_row_id")
    quote_span_id_index = facts["columns"].index("quote_span_id")
    quote_table_span_index = reader["quote_table"]["columns"].index(
        "quote_span_id"
    )
    original_quote_row_id = fact[quote_row_id_index]
    fact[quote_row_id_index] = next(
        row_id
        for row_id, row in enumerate(reader["quote_table"]["rows"])
        if row_id != original_quote_row_id
        and row[quote_table_span_index] != fact[quote_span_id_index]
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_decision_state_reader_evidence_rows(reader)

    assert caught.value.boundary == "decision_state_reader_evidence_binding"


def test_reader_relation_facts_bind_only_point_relative_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)

    view = build_axis_consolidated_view(spec)
    reader = view["decision_state_reader_surface"]
    full_state_rows = {
        row["decision_state_id"]: row
        for row in _reader_rows(view["decision_state_index"])
    }
    point_by_placement = {
        row["placement_id"]: row["point_id"] for row in view["point_placements"]
    }
    expected_point_state_ids: dict[str, set[str]] = defaultdict(set)
    for group in view["decision_state_groups"]:
        expected_point_state_ids[point_by_placement[group["placement_id"]]].update(
            group["state_ids"]
        )
    assert "decision_state_index" not in reader
    assert "state_dictionary" not in reader
    semantic_rows = _reader_rows(reader["semantic_unit_table"])

    def expand_reader_state(state: Mapping[str, Any]) -> dict[str, Any]:
        return {
            **{
                key: value
                for key, value in state.items()
                if key != "semantic_unit_row_ids"
            },
            "semantic_unit_refs": [
                semantic_rows[row_id]["semantic_unit_ref"]
                for row_id in state["semantic_unit_row_ids"]
            ],
        }

    def state_refs(state: Mapping[str, Any]) -> set[str]:
        return {
            semantic_rows[row_id]["semantic_unit_ref"]
            for row_id in state["semantic_unit_row_ids"]
        }

    for point in _reader_rows(reader["point_table"]):
        point_states = _reader_rows(point["state_table"])
        expected_states = [
            {
                key: value
                for key, value in full_state_rows[state_id].items()
                if key != "decision_state_id"
            }
            for state_id in sorted(expected_point_state_ids[point["point_id"]])
        ]
        assert [expand_reader_state(state) for state in point_states] == expected_states
        for fact in _reader_rows(point["relation_facts"]):
            relation_refs = {
                semantic_rows[row_id]["semantic_unit_ref"]
                for row_id in fact["relation_semantic_unit_row_ids"]
            }
            relation_states = [
                point_states[row_id] for row_id in fact["relation_state_row_ids"]
            ]
            context_states = [
                point_states[row_id] for row_id in fact["source_context_state_row_ids"]
            ]
            assert all(state_refs(row) & relation_refs for row in relation_states)
            assert all(
                not state_refs(row) & relation_refs for row in context_states
            )

    rule = view["decision_state_contract"]["point_relation_state_rule"]
    assert "relation_state_row_ids" in rule
    assert "source_context_state_row_ids" in rule
    assert "state_table" in rule


def test_context_only_qualification_refs_resolve_through_primary_or_companion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    row = spec["decision_state_bindings"][0]["rows"][0]
    all_refs = [
        assertion_ref
        for assertion in row["state_assertions"]
        for assertion_ref in assertion["semantic_unit_refs"]
    ]
    row["state_assertions"] = []
    row["context_only_semantic_unit_refs"] = all_refs
    _synchronize_semantic_binding_row(spec, row)

    view = build_axis_consolidated_view(spec)
    companion_refs = {row["semantic_unit_ref"] for row in view["companion_meaning_index"]}
    placements = {row["placement_id"]: row for row in view["point_placements"]}
    primary_context_refs = {
        ref
        for group in view["decision_state_groups"]
        for ref in group["qualification_refs"]
        if ref == placements[group["placement_id"]]["semantic_unit_ref"]
    }

    # The context-only form this route allows puts the placement's own primary
    # meaning in qualification_refs, where companion_meaning_index cannot resolve it.
    assert primary_context_refs
    assert not primary_context_refs & companion_refs
    rule = view["decision_state_contract"]["qualification_rule"]
    assert "primary" in rule and "companion" in rule
    semantic_units = {
        row["semantic_unit_ref"]: row
        for row in _reader_rows(
            view["decision_state_reader_surface"]["semantic_unit_table"]
        )
    }
    for ref in primary_context_refs:
        assert semantic_units[ref]["statement"]
    assert "point_placements" in rule and "semantic_unit_table" in rule


@pytest.mark.parametrize(
    "mutation,match",
    [
        (
            {"state_kind": "repurchase_intent", "commercial_direction": "away_from_action"},
            "invalid state/direction",
        ),
        (
            {"state_kind": "buyers_remorse", "commercial_direction": "favorable"},
            "invalid state/direction",
        ),
        (
            {
                "state_kind": "expectation_judgment",
                "commercial_direction": "toward_action",
            },
            "invalid state/direction",
        ),
        (
            {"state_kind": "premium", "commercial_direction": "favorable"},
            "unsupported decision state: premium",
        ),
        (
            {
                "state_kind": "observed_repurchase",
                "commercial_direction": "toward_action",
                "quantity": 4,
            },
            "quantity is valid only for multi-unit purchase",
        ),
        (
            {
                "state_kind": "multi_unit_purchase",
                "commercial_direction": "toward_action",
                "quantity": None,
            },
            "multi-unit purchase requires quantity >= 2",
        ),
        (
            {
                "state_kind": "multi_unit_purchase",
                "commercial_direction": "toward_action",
                "quantity": 1,
            },
            "multi-unit purchase requires quantity >= 2",
        ),
    ],
)
def test_decision_state_wrong_cause_transitions_fail_at_semantic_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict[str, Any],
    match: str,
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    assertion = spec["decision_state_bindings"][0]["rows"][1]["state_assertions"][0]
    assertion.update(mutation)

    with pytest.raises(EvidenceConsumerError, match=match):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing_point", "do not cover every routed point"),
        ("missing_row", "display row lacks a state binding"),
        ("foreign_ref", "references foreign semantic unit"),
        ("missing_companion", "does not cover every semantic unit"),
    ],
)
def test_decision_state_bindings_require_exact_row_and_semantic_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    match: str,
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    first_point = spec["decision_state_bindings"][0]
    first_row = first_point["rows"][0]
    if mutation == "missing_point":
        spec["decision_state_bindings"].pop()
    elif mutation == "missing_row":
        first_point["rows"].pop()
    elif mutation == "foreign_ref":
        first_row["state_assertions"][0]["semantic_unit_refs"] = ["foreign::semantic"]
    elif mutation == "missing_companion":
        first_row["state_assertions"].pop()
    with pytest.raises(EvidenceConsumerError, match=match):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize(
    "routes,error",
    [
        (
            [{"projection_mode": "direct_outcome", "point_ids": ["point_a"]}],
            "projection routes do not cover every point",
        ),
        (
            [
                {
                    "projection_mode": "direct_outcome",
                    "point_ids": ["point_a", "point_a", "point_b"],
                }
            ],
            "point_id appears more than once",
        ),
        (
            [
                {
                    "projection_mode": "direct_outcome",
                    "point_ids": ["point_a", "point_b", "point_foreign"],
                }
            ],
            "unknown point_id in projection route",
        ),
        (
            [
                {
                    "projection_mode": "generic_compact",
                    "point_ids": ["point_a", "point_b"],
                }
            ],
            "unsupported projection mode",
        ),
    ],
)
def test_v2_projection_routes_require_exactly_one_known_route_per_point(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    routes: list[dict[str, Any]],
    error: str,
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec["projection_routes"] = routes
    with pytest.raises(EvidenceConsumerError, match=error):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_state_bindings", []),
        ("decision_state_bindings_sha256", "unused-binding-identity"),
        (
            "decision_state_rejected_point_navigation",
            [
                {
                    "point_id": "point_rejected",
                    "navigation_group_id": "hydration_efficacy",
                }
            ],
        ),
    ],
)
def test_v2_direct_outcome_rejects_decision_state_spec_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec[field] = value

    with pytest.raises(
        EvidenceConsumerError,
        match="decision-state fields supplied without a decision_state route",
    ):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_state_bindings", []),
        ("decision_state_bindings_sha256", "unused-binding-identity"),
        ("decision_state_rejected_point_navigation", []),
    ],
)
def test_v1_rejects_decision_state_spec_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec["schema_version"] = LEGACY_CONSOLIDATION_SPEC_VERSION
    spec.pop("projection_routes")
    spec[field] = value

    with pytest.raises(EvidenceConsumerError, match="invalid in a v1 spec"):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize(
    "rejected_points",
    [
        [{"point_id": "point_rejected"}],
        ["point_rejected"],
    ],
)
def test_decision_state_rejects_incomplete_legacy_rejected_point_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rejected_points: list[Any],
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    axis = json.loads(paths["axis"].read_text(encoding="utf-8"))
    axis["rejected_points"] = rejected_points
    _write(paths["axis"], axis)
    spec["source_axis_pack_sha256"] = hash_file(paths["axis"])
    _route_every_point_as_decision_state(spec)

    with pytest.raises(EvidenceConsumerError, match="rejected-point fields are invalid"):
        build_axis_consolidated_view(spec)


def test_decision_state_preserves_mixed_axis_rejected_point_resolution_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    receipt_path = tmp_path / "rejected-point-receipt.json"
    _write(
        receipt_path,
        {
            "schema_version": "phase_a_rejected_point_resolution_receipt_v1",
            "point_id": "point_rejected",
            "failure_boundary": "frontier_relation_quote_relevance",
        },
    )
    manifest["rejected_points"][0].update(
        {
            "resolution_receipt_path": str(receipt_path),
            "resolution_receipt_sha256": hash_file(receipt_path),
        }
    )
    _rehash_manifest(manifest)
    axis_pack = build_phase_a_evidence_axis_pack(manifest)
    _write(paths["generic_axis"], axis_pack)
    spec["source_axis_pack_sha256"] = hash_file(paths["generic_axis"])
    _route_every_point_as_decision_state(spec)

    view = build_axis_consolidated_view(spec)

    assert view["rejected_point_index"] == [
        {
            "point_id": "point_rejected",
            "bounded_point": "The balm fixes every lip outcome.",
            "disposition": "point_scope_failed",
            "reason": "broad_axis_or_bundle",
            "resolution_receipt_path": str(receipt_path),
            "resolution_receipt_sha256": hash_file(receipt_path),
        }
    ]


@pytest.mark.parametrize("projection_mode", ["direct_outcome", "decision_state"])
def test_v2_routed_points_require_the_boundaries_owned_by_each_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, projection_mode: str
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["output_boundary"].remove("creator influence is not customer corroboration")
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    if projection_mode == "decision_state":
        _route_every_point_as_decision_state(spec)

    with pytest.raises(
        EvidenceConsumerError,
        match="routed point lacks required output boundary: point_a::creator influence",
    ):
        build_axis_consolidated_view(spec)


def test_v1_spec_remains_deterministic_and_reprojects_without_v2_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec["schema_version"] = LEGACY_CONSOLIDATION_SPEC_VERSION
    spec.pop("projection_routes")

    view = build_axis_consolidated_view(spec)

    assert view["schema_version"] == LEGACY_CONSOLIDATED_VIEW_VERSION
    assert "projection_routes" not in view
    assert all("projection_mode" not in row for row in view["point_index"])
    assert all(boundary not in view["non_claims"] for boundary in DIRECT_OUTCOME_BOUNDARIES)
    assert build_axis_consolidated_view(spec) == view
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def test_decision_state_reader_binds_claim_relation_to_companion_meaning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    binding = spec["decision_state_bindings"][0]["rows"][0]
    companion_ref = binding["state_assertions"][1]["semantic_unit_refs"][0]
    binding["relation_semantic_unit_refs"] = [companion_ref]

    view = build_axis_consolidated_view(spec)
    reader = view["decision_state_reader_surface"]
    point_columns = reader["point_table"]["columns"]
    semantic_rows = _reader_rows(reader["semantic_unit_table"])
    assert any(
        any(
            semantic_rows[row_id]["semantic_unit_ref"] == companion_ref
            for row_id in fact[
                fact_columns.index("relation_semantic_unit_row_ids")
            ]
        )
        for row in reader["point_table"]["rows"]
        for fact_table in [row[point_columns.index("relation_facts")]]
        for fact_columns in [fact_table["columns"]]
        for fact in fact_table["rows"]
    )


def test_v2_direct_outcome_can_bind_point_relation_to_companion_meaning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact = json.loads(paths["artifact_point_a"].read_text(encoding="utf-8"))
    row = artifact["source_groups"][0]["rows"][0]
    companion_ref = row["same_evidence_companion_meanings"][0]["semantic_unit_ref"]
    spec["direct_outcome_relation_bindings"] = [
        {
            "point_id": "point_a",
            "rows": [
                {
                    "selected_id": row["selected_id"],
                    "relation_semantic_unit_refs": [companion_ref],
                }
            ],
        }
    ]

    view = build_axis_consolidated_view(spec)
    placement = next(
        item
        for item in view["point_placements"]
        if item["point_id"] == "point_a" and item["selected_id"] == row["selected_id"]
    )
    assert placement["relation_semantic_unit_refs"] == [companion_ref]


def test_v2_direct_outcome_rejects_foreign_relation_semantic_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact = json.loads(paths["artifact_point_a"].read_text(encoding="utf-8"))
    selected_id = artifact["source_groups"][0]["rows"][0]["selected_id"]
    spec["direct_outcome_relation_bindings"] = [
        {
            "point_id": "point_a",
            "rows": [
                {
                    "selected_id": selected_id,
                    "relation_semantic_unit_refs": ["foreign::semantic-unit"],
                }
            ],
        }
    ]

    with pytest.raises(EvidenceConsumerError, match="foreign semantic unit"):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize("relation_refs", [[], ["foreign::semantic-unit"]])
def test_decision_state_rejects_invalid_relation_semantic_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relation_refs: list[str],
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["decision_state_bindings"][0]["rows"][0][
        "relation_semantic_unit_refs"
    ] = relation_refs

    with pytest.raises(EvidenceConsumerError, match="relation semantic|foreign semantic"):
        build_axis_consolidated_view(spec)


@pytest.mark.parametrize("field,value", [("relation", "support"), ("quote_span_id", "quote_fake")])
def test_reprojection_rejects_rehashed_direction_or_quote_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    trusted_view_sha256 = view["view_sha256"]
    mutated = copy.deepcopy(view)
    mutated["point_placements"][0][field] = value
    mutated["view_sha256"] = _canonical_json_sha256(
        {key: item for key, item in mutated.items() if key != "view_sha256"}
    )
    with pytest.raises(EvidenceConsumerError, match="trusted view identity differs"):
        validate_axis_consolidated_view(
            mutated, expected_view_sha256=trusted_view_sha256
        )


def test_external_view_hash_rejects_rehashed_decision_state_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    trusted_view_sha256 = view["view_sha256"]
    mutated = copy.deepcopy(view)
    state_row = mutated["decision_state_index"]["rows"][0]
    state_row[1] = "purchase"
    state_row[2] = "neutral"
    mutated["view_sha256"] = _canonical_json_sha256(
        {key: item for key, item in mutated.items() if key != "view_sha256"}
    )

    with pytest.raises(EvidenceConsumerError, match="trusted view identity differs"):
        validate_axis_consolidated_view(
            mutated, expected_view_sha256=trusted_view_sha256
        )


def test_external_view_hash_rejects_coherent_navigation_regrouping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    view = build_axis_consolidated_view(spec)
    trusted_view_sha256 = view["view_sha256"]
    mutated = copy.deepcopy(view)
    family = mutated["spec"]["navigation_groups"][0]["families"][0]
    family["family_id"] = "misleading_direction"
    family["label"] = "Misleading direction"
    mutated["navigation_groups"][0]["families"][0]["family_id"] = (
        "misleading_direction"
    )
    mutated["navigation_groups"][0]["families"][0]["label"] = (
        "Misleading direction"
    )
    for point in mutated["point_index"]:
        point["family_id"] = "misleading_direction"
    mutated["view_sha256"] = _canonical_json_sha256(
        {key: item for key, item in mutated.items() if key != "view_sha256"}
    )
    with pytest.raises(EvidenceConsumerError, match="trusted view identity differs"):
        validate_axis_consolidated_view(
            mutated, expected_view_sha256=trusted_view_sha256
        )


def test_navigation_must_cover_every_point_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec["navigation_groups"][0]["families"][0]["point_ids"] = ["point_a"]
    with pytest.raises(EvidenceConsumerError, match="navigation does not cover"):
        build_axis_consolidated_view(spec)


def test_same_origin_cannot_change_identity_across_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_b"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["source_groups"][0]["rows"][0]["independence_key"] = "reddit:not-alice"
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    with pytest.raises(EvidenceConsumerError, match="origin independence changed"):
        build_axis_consolidated_view(spec)


def test_origin_index_preserves_unavailable_independence_posture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["candidate_dispositions"][1]["independence_posture"] = "unavailable"
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    view = build_axis_consolidated_view(spec)
    bob = next(row for row in view["origin_index"] if row["independence_key"] == "reddit:bob")
    assert bob["independence_posture"] == "unavailable"
    assert view["counts"]["credited_origin_count"] == 2
    assert view["counts"]["uncredited_origin_count"] == 1


def test_one_origin_cannot_change_independence_posture_across_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_b"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["candidate_dispositions"][0]["independence_posture"] = "unavailable"
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    with pytest.raises(EvidenceConsumerError, match="origin independence posture changed"):
        build_axis_consolidated_view(spec)


def test_undated_engagement_bucket_denies_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    for point_id in ("point_a", "point_b"):
        artifact_path = paths[f"artifact_{point_id}"]
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        for row in artifact["source_groups"][0]["rows"]:
            row["publication_time"] = None
        _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    view = build_axis_consolidated_view(spec)
    assert {row["comparison_boundary"] for row in view["engagement_buckets"]} == {
        "not_comparable_without_observation_year"
    }


def test_companion_meaning_cannot_change_across_placements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_b"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["source_groups"][0]["rows"][0]["same_evidence_companion_meanings"][0][
        "normalized_meaning"
    ] = "Changed meaning."
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    with pytest.raises(EvidenceConsumerError, match="companion meaning changed"):
        build_axis_consolidated_view(spec)


def test_reddit_comment_surface_requires_a_matching_comment_source_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    comment_row = artifact["source_groups"][0]["rows"][1]
    assert comment_row["evidence_id"] == "reddit:thread1:comment1"
    comment_row["source_ref"] = (
        "https://www.reddit.com/r/test/comments/thread1/title/?ref=comment1"
    )
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    with pytest.raises(EvidenceConsumerError, match="Reddit comment identity is absent"):
        build_axis_consolidated_view(spec)


def test_build_verifies_the_cold_selection_sources_of_every_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Mapping[str, Any]] = []
    spec, _ = _fixture(tmp_path, monkeypatch, selection_source_calls=calls)
    build_axis_consolidated_view(spec)
    assert [call["schema_version"] for call in calls] == [
        "phase_a_evidence_selection_manifest_v1"
    ] * 2
    assert len({call["manifest_sha256"] for call in calls}) == 2


def test_candidate_manifest_tampering_fails_before_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    paths["selection_point_a"].write_text("{}\n", encoding="utf-8")
    with pytest.raises(EvidenceConsumerError, match="selection manifest changed"):
        build_axis_consolidated_view(spec)


def test_runner_writes_once_and_validates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    spec_path = tmp_path / "spec.json"
    output_path = tmp_path / "view.json"
    _write(spec_path, spec)
    result = build_run(spec_path=spec_path, output_path=output_path)
    assert result["status"] == "complete"
    assert validate_run(
        view_path=output_path,
        expected_view_sha256=result["view_sha256"],
    )["view_sha256"] == result["view_sha256"]
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_run(spec_path=spec_path, output_path=output_path)


def test_generic_axis_pack_and_view_preserve_point_relation_origin_and_source_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, generic_spec, paths = _generic_fixture(tmp_path, monkeypatch)
    pack = build_phase_a_evidence_axis_pack(manifest)
    legacy_spec = copy.deepcopy(generic_spec)
    legacy_spec["source_axis_pack_path"] = str(paths["axis"])
    legacy_spec["source_axis_pack_sha256"] = hash_file(paths["axis"])

    assert pack["schema_version"] == AXIS_PACK_VERSION
    assert pack["valid_point_count"] == 2
    assert pack["rejected_point_count"] == 1
    assert pack["cold_reader_resolution"] == {
        "resolved_candidate_disposition_count": 6,
        "path_resolution": "explicit_manifest_paths_only",
    }
    assert all(point["quote_manifest_file_sha256"] for point in pack["points"])
    assert validate_phase_a_evidence_axis_pack(
        pack, expected_axis_pack_sha256=pack["axis_pack_sha256"]
    ) == pack

    generic_view = build_axis_consolidated_view(generic_spec)
    legacy_view = build_axis_consolidated_view(legacy_spec)
    assert generic_view["counts"] == legacy_view["counts"]
    assert point_placement_keys(generic_view) == point_placement_keys(legacy_view)
    assert build_axis_consolidated_view(generic_spec) == generic_view
    assert build_phase_a_evidence_axis_pack(manifest) == pack


def test_legacy_hydration_v2_shape_remains_byte_deterministic_and_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, _ = _fixture(tmp_path, monkeypatch)
    first = build_axis_consolidated_view(spec)
    second = build_axis_consolidated_view(spec)
    assert first == second
    assert validate_axis_consolidated_view(
        first, expected_view_sha256=first["view_sha256"]
    ) == first


def _bind_generic_fixture_to_literal_frontier(
    manifest: dict[str, Any], *, expected_axis: str
) -> None:
    for descriptor in manifest["accepted_points"]:
        selection_path = Path(descriptor["selection_manifest_path"])
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection["spec"]["axis_ids"] = []
        selection["spec"]["relation_response_mode"] = "literal_ids"
        selection["spec"]["relation_policy"] = "bounded_point"
        selection["spec"]["customer_pull_frontier_binding"] = {
            "proposition_id": descriptor["point_id"],
            "candidate_admission": "literal_point_relations",
        }
        _rehash_manifest(selection)
        _write(selection_path, selection)

        quote_path = Path(descriptor["quote_manifest_path"])
        quote = json.loads(quote_path.read_text(encoding="utf-8"))
        quote["selection_manifest_sha256"] = selection["manifest_sha256"]
        _rehash_manifest(quote)
        _write(quote_path, quote)

        artifact_path = Path(descriptor["artifact_path"])
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        for candidate in artifact["candidate_dispositions"]:
            candidate["axis_ids"] = [expected_axis]
        artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
        artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
        _write(artifact_path, artifact)

        descriptor["artifact_sha256"] = hash_file(artifact_path)
        descriptor["selection_manifest_file_sha256"] = hash_file(selection_path)
        descriptor["selection_manifest_sha256"] = selection["manifest_sha256"]
        descriptor["quote_manifest_file_sha256"] = hash_file(quote_path)
        descriptor["quote_manifest_sha256"] = quote["manifest_sha256"]
    _rehash_manifest(manifest)


def test_axis_pack_accepts_frontier_literal_ref_points_bound_by_candidate_axes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    _bind_generic_fixture_to_literal_frontier(
        manifest, expected_axis="hydration_and_moisture"
    )

    pack = build_phase_a_evidence_axis_pack(manifest)

    assert pack["valid_point_count"] == 2


def test_axis_pack_rejects_frontier_literal_ref_point_with_foreign_candidate_axis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    _bind_generic_fixture_to_literal_frontier(
        manifest, expected_axis="hydration_and_moisture"
    )
    descriptor = manifest["accepted_points"][0]
    artifact_path = Path(descriptor["artifact_path"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["candidate_dispositions"][0]["axis_ids"] = ["value_and_quantity"]
    _write(artifact_path, artifact)
    descriptor["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(manifest)

    with pytest.raises(EvidenceConsumerError, match="axis binding changed"):
        build_phase_a_evidence_axis_pack(manifest)


def _repin_literal_frontier_point(
    manifest: dict[str, Any], descriptor: dict[str, Any], selection: dict[str, Any]
) -> None:
    """Re-pin every hash downstream of a mutated selection manifest.

    Without this the artifact/selection/quote pins fail first and the axis
    binding boundary under test is never reached.
    """
    selection_path = Path(descriptor["selection_manifest_path"])
    _rehash_manifest(selection)
    _write(selection_path, selection)

    quote_path = Path(descriptor["quote_manifest_path"])
    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    quote["selection_manifest_sha256"] = selection["manifest_sha256"]
    _rehash_manifest(quote)
    _write(quote_path, quote)

    artifact_path = Path(descriptor["artifact_path"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
    artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
    _write(artifact_path, artifact)

    descriptor["artifact_sha256"] = hash_file(artifact_path)
    descriptor["selection_manifest_file_sha256"] = hash_file(selection_path)
    descriptor["selection_manifest_sha256"] = selection["manifest_sha256"]
    descriptor["quote_manifest_file_sha256"] = hash_file(quote_path)
    descriptor["quote_manifest_sha256"] = quote["manifest_sha256"]
    _rehash_manifest(manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        "relation_response_mode",
        "relation_policy",
        "frontier_proposition_id",
        "frontier_candidate_admission",
        "frontier_binding_absent",
    ],
)
def test_literal_frontier_exception_requires_every_declared_condition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """An empty `axis_ids` is admitted only by the whole frontier binding.

    Each condition is dropped in isolation from an otherwise admitted point,
    with every downstream pin refreshed, so the axis binding boundary is the
    one that fails rather than an earlier hash guard.
    """
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    _bind_generic_fixture_to_literal_frontier(
        manifest, expected_axis="hydration_and_moisture"
    )
    descriptor = manifest["accepted_points"][0]
    selection_path = Path(descriptor["selection_manifest_path"])
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    spec = selection["spec"]
    if mutation == "relation_response_mode":
        spec["relation_response_mode"] = "named_axis_ids"
    elif mutation == "relation_policy":
        spec["relation_policy"] = "broad_axis"
    elif mutation == "frontier_proposition_id":
        spec["customer_pull_frontier_binding"]["proposition_id"] = "point_elsewhere"
    elif mutation == "frontier_candidate_admission":
        spec["customer_pull_frontier_binding"]["candidate_admission"] = (
            "named_axis_relations"
        )
    else:
        spec.pop("customer_pull_frontier_binding")
    _repin_literal_frontier_point(manifest, descriptor, selection)

    with pytest.raises(EvidenceConsumerError, match="axis binding changed"):
        build_phase_a_evidence_axis_pack(manifest)


def test_axis_builder_rejects_schema_rename_with_hidden_sibling_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    near_miss = copy.deepcopy(manifest)
    point = near_miss["accepted_points"][0]
    for field in (
        "selection_manifest_path",
        "selection_manifest_file_sha256",
        "selection_manifest_sha256",
        "quote_manifest_path",
        "quote_manifest_file_sha256",
        "quote_manifest_sha256",
    ):
        point.pop(field)
    _rehash_manifest(near_miss)
    with pytest.raises(EvidenceConsumerError, match="accepted point pins are incomplete"):
        build_phase_a_evidence_axis_pack(near_miss)


def test_rejected_only_axis_requires_and_preserves_cold_resolution_receipt(
    tmp_path: Path,
) -> None:
    receipt_path = tmp_path / "rejected-point-receipt.json"
    _write(
        receipt_path,
        {
            "schema_version": "phase_a_rejected_point_resolution_receipt_v1",
            "point_id": "point_rejected",
            "failure_boundary": "frontier_relation_quote_relevance",
        },
    )
    manifest = {
        "schema_version": AXIS_PACK_MANIFEST_VERSION,
        "axis_id": "application_and_tool_performance",
        "accepted_points": [],
        "rejected_points": [
            {
                "point_id": "point_rejected",
                "bounded_point": "A rejected application point.",
                "disposition": "frontier_relation_quote_relevance_failed",
                "reason": "The relation-bearing source body does not support the point.",
                "resolution_receipt_path": str(receipt_path),
                "resolution_receipt_sha256": hash_file(receipt_path),
            }
        ],
    }
    _rehash_manifest(manifest)

    pack = build_phase_a_evidence_axis_pack(manifest)
    assert pack["status"] == "complete_rejected_axis_pack"
    assert pack["valid_point_count"] == 0
    assert pack["rejected_point_count"] == 1
    assert pack["cold_reader_resolution"][
        "rejected_resolution_receipt_count"
    ] == 1
    assert validate_phase_a_evidence_axis_pack(
        pack, expected_axis_pack_sha256=pack["axis_pack_sha256"]
    ) == pack

    pack_path = tmp_path / "rejected-only-axis-pack.json"
    _write(pack_path, pack)
    rejected_route_spec = {
        "schema_version": CONSOLIDATION_SPEC_VERSION,
        "axis_id": "application_and_tool_performance",
        "source_axis_pack_path": str(pack_path),
        "source_axis_pack_sha256": hash_file(pack_path),
        "navigation_groups": [],
        "projection_routes": [
            {
                "projection_mode": "decision_state",
                "point_ids": ["point_rejected"],
            }
        ],
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        build_axis_consolidated_view(rejected_route_spec)
    assert caught.value.boundary == "axis_binding"

    receiptless = copy.deepcopy(manifest)
    for row in receiptless["rejected_points"]:
        row.pop("resolution_receipt_path")
        row.pop("resolution_receipt_sha256")
    _rehash_manifest(receiptless)
    with pytest.raises(EvidenceConsumerError) as caught:
        build_phase_a_evidence_axis_pack(receiptless)
    assert caught.value.boundary == "rejected_point_resolution"

    wrong_point_receipt = {
        "schema_version": "phase_a_rejected_point_resolution_receipt_v1",
        "point_id": "some_other_point",
        "failure_boundary": "frontier_relation_quote_relevance",
    }
    _write(receipt_path, wrong_point_receipt)
    wrong_point_manifest = copy.deepcopy(manifest)
    wrong_point_manifest["rejected_points"][0][
        "resolution_receipt_sha256"
    ] = hash_file(receipt_path)
    _rehash_manifest(wrong_point_manifest)
    with pytest.raises(EvidenceConsumerError) as caught:
        build_phase_a_evidence_axis_pack(wrong_point_manifest)
    assert caught.value.boundary == "rejected_point_resolution"

    receipt_path.write_text("changed\n", encoding="utf-8")
    with pytest.raises(EvidenceConsumerError) as caught:
        build_phase_a_evidence_axis_pack(manifest)
    assert caught.value.boundary == "rejected_point_resolution"


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("duplicate_point", "accepted point identities are invalid"),
        ("accepted_rejected_overlap", "accepted/rejected point overlap"),
        ("missing_point_pin", "accepted point pins are incomplete"),
        ("wrong_axis", "axis binding changed"),
        ("stale_selection_binding", "manifest identity differs"),
        ("stale_quote_binding", "manifest identity differs"),
    ],
)
def test_axis_manifest_wrong_cause_guards_fail_at_their_named_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    match: str,
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    changed = copy.deepcopy(manifest)
    if mutation == "duplicate_point":
        changed["accepted_points"].append(copy.deepcopy(changed["accepted_points"][0]))
    elif mutation == "accepted_rejected_overlap":
        changed["rejected_points"][0]["point_id"] = changed["accepted_points"][0][
            "point_id"
        ]
    elif mutation == "missing_point_pin":
        changed["accepted_points"][0].pop("artifact_sha256")
    elif mutation == "wrong_axis":
        changed["axis_id"] = "value_and_quantity"
    elif mutation == "stale_selection_binding":
        changed["accepted_points"][0]["selection_manifest_sha256"] = "0" * 64
    else:
        changed["accepted_points"][0]["quote_manifest_sha256"] = "0" * 64
    _rehash_manifest(changed)
    with pytest.raises(EvidenceConsumerError, match=match):
        build_phase_a_evidence_axis_pack(changed)


def test_altered_point_file_fails_at_the_point_file_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, paths = _generic_fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["bounded_point"] = "Altered after pinning."
    _write(artifact_path, artifact)
    with pytest.raises(EvidenceConsumerError, match="point artifact changed"):
        build_phase_a_evidence_axis_pack(manifest)


def test_packet_bundle_mismatch_fails_at_source_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation.load_selection_sources",
        lambda _: [
            {
                "packet": {"source_bindings": {"bundle_sha256": "packet_bundle"}},
                "bundle": {"bundle_sha256": "different_bundle"},
            }
        ],
    )
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation._verify_packet", lambda _: None
    )
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation._verify_bundle", lambda _: None
    )
    with pytest.raises(EvidenceConsumerError, match="packet/bundle binding changed"):
        build_phase_a_evidence_axis_pack(manifest)


@pytest.mark.parametrize("stale_source", ["packet", "bundle"])
def test_stale_packet_or_bundle_self_binding_is_reverified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stale_source: str,
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation.load_selection_sources",
        lambda _: [
            {
                "packet": {"source_bindings": {"bundle_sha256": "bundle"}},
                "bundle": {"bundle_sha256": "bundle"},
            }
        ],
    )

    def _packet_check(_: Mapping[str, Any]) -> None:
        if stale_source == "packet":
            raise EvidenceConsumerError("packet_verification", "packet hash mismatch")

    def _bundle_check(_: Mapping[str, Any]) -> None:
        if stale_source == "bundle":
            raise EvidenceConsumerError("bundle_verification", "bundle hash mismatch")

    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation._verify_packet", _packet_check
    )
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation._verify_bundle", _bundle_check
    )
    with pytest.raises(EvidenceConsumerError, match=f"{stale_source} hash mismatch"):
        build_phase_a_evidence_axis_pack(manifest)


def test_generic_pack_rejects_a_nonstandard_truth_origin_cap_after_repinning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, paths = _generic_fixture(tmp_path, monkeypatch)
    changed = copy.deepcopy(manifest)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["truth_group_cap"] = 20
    _write(artifact_path, artifact)
    changed["accepted_points"][0]["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(changed)
    with pytest.raises(EvidenceConsumerError, match="truth origin cap must be 13"):
        build_phase_a_evidence_axis_pack(changed)


def test_generic_pack_accepts_truth_origin_cap_bound_by_selection_spec(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, paths = _generic_fixture(tmp_path, monkeypatch)
    descriptor = manifest["accepted_points"][0]
    selection_path = Path(descriptor["selection_manifest_path"])
    quote_path = Path(descriptor["quote_manifest_path"])
    artifact_path = Path(descriptor["artifact_path"])

    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection["spec"]["truth_group_cap"] = 20
    _rehash_manifest(selection)
    _write(selection_path, selection)

    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    quote["selection_manifest_sha256"] = selection["manifest_sha256"]
    quote["truth_group_cap"] = 20
    _rehash_manifest(quote)
    _write(quote_path, quote)

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
    artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
    artifact["truth_group_cap"] = 20
    _write(artifact_path, artifact)

    descriptor.update(
        artifact_sha256=hash_file(artifact_path),
        selection_manifest_file_sha256=hash_file(selection_path),
        selection_manifest_sha256=selection["manifest_sha256"],
        quote_manifest_file_sha256=hash_file(quote_path),
        quote_manifest_sha256=quote["manifest_sha256"],
    )
    _rehash_manifest(manifest)

    pack = build_phase_a_evidence_axis_pack(manifest)
    assert pack["points"][0]["point_id"] == "point_a"
    assert paths["artifact_point_a"].is_file()


def test_non_truth_support_origin_is_displayed_but_never_counted_as_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A creator-influence origin must not enter any truth-origin count.

    Every fixture and pilot row so far carries `layer: truth_support`, so the
    layer discriminator is otherwise unexercised: an all-layer origin union and
    a truth-only union coincide and a relabel cannot be observed.
    """
    manifest, spec, paths = _generic_fixture(tmp_path, monkeypatch)
    baseline = build_phase_a_evidence_axis_pack(manifest)
    assert baseline["unique_truth_origins_across_axis"] == 3

    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    rows = artifact["source_groups"][0]["rows"]
    influence = copy.deepcopy(rows[0])
    influence.update(
        {
            "selected_id": "selected_influence",
            "evidence_id": "reddit:thread9:post",
            "semantic_unit_ref": "reddit:thread9:post::creator",
            "relation": "adjacent",
            "origin_group_id": "scope::reddit:creator",
            "independence_key": "reddit:creator",
            "origin_candidate_ids": ["candidate_influence"],
            "layer": "creator_influence",
            "source_ref": "https://www.reddit.com/r/test/comments/thread9/title/",
            "same_evidence_companion_meanings": [],
        }
    )
    rows.append(influence)
    artifact["candidate_dispositions"].append(
        _candidate(
            "candidate_influence",
            evidence_id="reddit:thread9:post",
            semantic_ref="reddit:thread9:post::creator",
            relation="adjacent",
            origin="scope::reddit:creator",
            container="reddit_thread_thread9",
        )
    )
    artifact["selection_disclosure"]["candidate_semantic_row_count"] = len(
        artifact["candidate_dispositions"]
    )
    artifact["selection_disclosure"]["displayed_row_count"] = len(rows)
    _write(artifact_path, artifact)
    changed = copy.deepcopy(manifest)
    changed["accepted_points"][0]["artifact_sha256"] = hash_file(artifact_path)
    _rehash_manifest(changed)

    pack = build_phase_a_evidence_axis_pack(changed)
    assert pack["unique_truth_origins_across_axis"] == 3
    assert pack["display_row_slots"] == baseline["display_row_slots"] + 1
    assert [point["truth_origin_count"] for point in pack["points"]] == [2, 2]

    pack_path = tmp_path / "layered_axis.json"
    _write(pack_path, pack)
    layered_spec = copy.deepcopy(spec)
    layered_spec["source_axis_pack_path"] = str(pack_path)
    layered_spec["source_axis_pack_sha256"] = hash_file(pack_path)
    view = build_axis_consolidated_view(layered_spec)
    assert view["counts"]["unique_origin_count"] == 4
    assert view["counts"]["placement_count"] == 5
    influence_placement = next(
        row for row in view["point_placements"] if row["layer"] == "creator_influence"
    )
    assert influence_placement["origin_group_id"] == "scope::reddit:creator"


def test_reddit_post_surface_rejects_a_comment_permalink_with_a_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The `:post` marker must lose to a URL that names a comment.

    `reddit:thread1:post` is displayed by both fixture points, so the rewrite
    is applied to both. Rewriting one would trip the cross-point evidence
    identity guard first and prove the wrong boundary.
    """
    spec, paths = _fixture(tmp_path, monkeypatch)
    for point_id in ("point_a", "point_b"):
        artifact_path = paths[f"artifact_{point_id}"]
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        post_row = artifact["source_groups"][0]["rows"][0]
        assert post_row["evidence_id"] == "reddit:thread1:post"
        post_row["source_ref"] = (
            "https://www.reddit.com/r/test/comments/thread1/title/comment1/"
        )
        _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)
    with pytest.raises(
        EvidenceConsumerError, match="Reddit post identity conflicts with comment URL"
    ):
        build_axis_consolidated_view(spec)


def test_navigation_rejects_duplicate_membership_and_foreign_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    duplicate = copy.deepcopy(spec)
    duplicate["navigation_groups"][0]["families"].append(
        {
            "family_id": "duplicate_family",
            "label": "Duplicate",
            "point_ids": ["point_a"],
        }
    )
    with pytest.raises(EvidenceConsumerError, match="appears more than once"):
        build_axis_consolidated_view(duplicate)

    foreign = copy.deepcopy(spec)
    foreign["navigation_groups"][0]["families"][0]["point_ids"].append(
        "foreign_point"
    )
    with pytest.raises(EvidenceConsumerError, match="unknown point_id"):
        build_axis_consolidated_view(foreign)


def test_stored_and_external_axis_and_view_hashes_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    bad_manifest = copy.deepcopy(manifest)
    bad_manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(EvidenceConsumerError, match="stored manifest hash is invalid"):
        build_phase_a_evidence_axis_pack(bad_manifest)

    pack = build_phase_a_evidence_axis_pack(manifest)
    bad_pack = copy.deepcopy(pack)
    bad_pack["axis_pack_sha256"] = "0" * 64
    with pytest.raises(EvidenceConsumerError, match="stored axis pack hash is invalid"):
        validate_phase_a_evidence_axis_pack(
            bad_pack, expected_axis_pack_sha256=bad_pack["axis_pack_sha256"]
        )
    with pytest.raises(EvidenceConsumerError, match="trusted axis pack identity differs"):
        validate_phase_a_evidence_axis_pack(
            pack, expected_axis_pack_sha256="f" * 64
        )

    view = build_axis_consolidated_view(spec)
    mutated = copy.deepcopy(view)
    mutated["view_sha256"] = "0" * 64
    with pytest.raises(EvidenceConsumerError, match="stored view hash is invalid"):
        validate_axis_consolidated_view(
            mutated, expected_view_sha256=mutated["view_sha256"]
        )
    with pytest.raises(EvidenceConsumerError, match="trusted view identity differs"):
        validate_axis_consolidated_view(view, expected_view_sha256="f" * 64)


def test_axis_pack_runner_writes_once_and_validates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _, _ = _generic_fixture(tmp_path, monkeypatch)
    manifest_path = tmp_path / "axis_manifest.json"
    output_path = tmp_path / "axis_pack.json"
    _write(manifest_path, manifest)
    result = build_axis_pack_run(manifest_path=manifest_path, output_path=output_path)
    assert result["status"] == "complete"
    assert validate_axis_pack_run(
        pack_path=output_path,
        expected_axis_pack_sha256=result["axis_pack_sha256"],
    )["axis_pack_sha256"] == result["axis_pack_sha256"]
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_axis_pack_run(manifest_path=manifest_path, output_path=output_path)


def test_dogfood_truth_runner_writes_once_and_rebuilds_from_source_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view_path = tmp_path / "view.json"
    truth_path = tmp_path / "truth.json"
    _write(view_path, build_axis_consolidated_view(spec))

    built = build_dogfood_truth_run(
        view_path=view_path, output_path=truth_path
    )

    assert built["model_api_calls"] == 0
    assert validate_dogfood_truth_run(
        truth_path=truth_path,
        expected_truth_index_sha256=built["truth_index_sha256"],
    )["status"] == "valid"
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_dogfood_truth_run(view_path=view_path, output_path=truth_path)


def test_axis_reader_runner_writes_once_and_rebuilds_from_source_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view_path = tmp_path / "reader_view.json"
    manifest_path = tmp_path / "reader_manifest.json"
    facts_dir = tmp_path / "reader_facts"
    _write(view_path, build_axis_consolidated_view(spec))

    built = build_reader_run(
        view_path=view_path,
        manifest_output_path=manifest_path,
        facts_output_dir=facts_dir,
    )

    assert built["model_api_calls"] == 0
    assert validate_reader_run(
        manifest_path=manifest_path,
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=built["reader_manifest_sha256"],
    )["status"] == "valid"
    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    saved_streams = {
        point["point_id"]: Path(point["facts_file"]["path"]).read_bytes()
        for point in saved_manifest["points"]
    }
    output_path = tmp_path / "reader_output.json"
    _write(output_path, _structured_reader_output(saved_manifest, saved_streams))
    assert validate_reader_output_run(
        manifest_path=manifest_path,
        facts_dir=facts_dir,
        output_path=output_path,
        expected_reader_manifest_sha256=built["reader_manifest_sha256"],
    )["status"] == "valid"
    base_schema_path = tmp_path / "base_schema.json"
    bound_schema_path = tmp_path / "bound_schema.json"
    _write(base_schema_path, _reader_output_base_schema())
    assert bind_reader_output_schema_run(
        manifest_path=manifest_path,
        facts_dir=facts_dir,
        base_schema_path=base_schema_path,
        output_schema_path=bound_schema_path,
        expected_reader_manifest_sha256=built["reader_manifest_sha256"],
    )["status"] == "complete"
    assert json.loads(bound_schema_path.read_text(encoding="utf-8"))["properties"][
        "accepted_points"
    ]["items"]["anyOf"]
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_reader_run(
            view_path=view_path,
            manifest_output_path=manifest_path,
            facts_output_dir=facts_dir,
        )
    reserved_manifest = tmp_path / "reserved_manifest.json"
    untouched_facts = tmp_path / "untouched_facts"
    _write(reserved_manifest, {})
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_reader_run(
            view_path=view_path,
            manifest_output_path=reserved_manifest,
            facts_output_dir=untouched_facts,
        )
    assert not untouched_facts.exists()


def test_axis_reader_runner_validates_the_manifest_bytes_it_wrote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A corrupted durable manifest cannot inherit an in-memory success result."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    view_path = tmp_path / "reader_view.json"
    manifest_path = tmp_path / "reader_manifest.json"
    facts_dir = tmp_path / "reader_facts"
    _write(view_path, build_axis_consolidated_view(spec))
    original_write_new = consolidation_runner._write_new

    def write_then_corrupt(path: Path, value: Any) -> None:
        original_write_new(path, value)
        if path == manifest_path:
            saved = json.loads(path.read_text(encoding="utf-8"))
            saved["axis_id"] = "corrupted_after_write"
            _write(path, saved)

    monkeypatch.setattr(consolidation_runner, "_write_new", write_then_corrupt)

    with pytest.raises(EvidenceConsumerError) as caught:
        consolidation_runner.build_reader_run(
            view_path=view_path,
            manifest_output_path=manifest_path,
            facts_output_dir=facts_dir,
        )
    assert caught.value.boundary == "axis_reader_bundle_verification"


def _point_reader_subject_identity() -> dict[str, str]:
    return {
        "schema_version": "phase_a_point_reader_subject_identity_v1",
        "company_id": "summer-fridays",
        "product_id": "lip-butter-balm",
        "cutoff": "2026-08-25",
    }


def _write_point_reader_store(
    store: Path,
    manifest: Mapping[str, Any],
    payloads: Mapping[str, bytes],
) -> None:
    store.mkdir()
    for point in manifest["points"]:
        (store / point["point_payload_file"]).write_bytes(
            payloads[point["point_id"]]
        )


def _point_reader_response(
    point: Mapping[str, Any], payload: bytes
) -> dict[str, Any]:
    facts = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    required_relations = {
        relation
        for relation in ("support", "counter")
        if point["displayed_relation_row_counts"].get(relation, 0) > 0
    }
    representatives = []
    represented_relations = set()
    for fact in facts:
        if fact["relation"] in required_relations - represented_relations:
            representatives.append({"placement_id": fact["placement_id"]})
            represented_relations.add(fact["relation"])
    if not representatives:
        representatives.append({"placement_id": facts[0]["placement_id"]})
    return {
        "point_input_sha256": point["point_input_sha256"],
        "point_id": point["point_id"],
        "interpretation": (
            f"Evidence for {point['bounded_point']} remains mixed where the "
            "literal point facts disagree."
        ),
        "representative_handles": representatives,
    }


def test_point_reader_compiler_closes_decision_state_at_consumer_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A coherently rehashed compact brief cannot omit or transfer state."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "decision_view.json"
    store = tmp_path / "point_store"
    _write(view_path, view)
    manifest, payloads = build_axis_point_reader_snapshot(
        view,
        source_view_path=view_path,
        subject_identity=_point_reader_subject_identity(),
    )
    _write_point_reader_store(store, manifest, payloads)

    briefs = []
    for point in manifest["points"]:
        response = _point_reader_response(point, payloads[point["point_id"]])
        brief = compile_point_reader_brief(
            manifest,
            point_store_dir=store,
            point_id=point["point_id"],
            response=response,
        )
        assert brief["schema_version"] == POINT_READER_BRIEF_VERSION
        assert brief["decision_state_ledger"]
        fact_by_placement = {
            fact["placement_id"]: fact
            for fact in (
                json.loads(line)
                for line in payloads[point["point_id"]]
                .decode("utf-8")
                .splitlines()
            )
        }
        assert all(
            representative["selected_row_meaning"]
            == fact_by_placement[representative["placement_id"]][
                "point_relative_meaning"
            ]
            for representative in brief["representative_evidence"]
        )
        assert validate_point_reader_brief(
            manifest, point_store_dir=store, brief=brief
        ) == brief
        briefs.append(brief)

    output = assemble_axis_point_reader_output(manifest, briefs=briefs)
    assert output["schema_version"] == POINT_READER_AXIS_OUTPUT_VERSION
    assert validate_axis_point_reader_output(
        manifest, output=output, point_store_dir=store
    ) == output

    first_facts = [
        json.loads(line)
        for line in payloads[manifest["points"][0]["point_id"]]
        .decode("utf-8")
        .splitlines()
    ]
    support_source = next(
        fact for fact in first_facts if fact["relation"] == "support"
    )
    same_quote_facts = [copy.deepcopy(support_source), copy.deepcopy(support_source)]
    same_quote_facts[1]["placement_id"] += "::second-meaning"
    same_quote_facts[1]["relation"] = "counter"
    same_quote_facts[1]["point_relative_meaning"]["semantic_unit_ref"] += (
        "::second-meaning"
    )
    same_quote_facts[1]["point_relative_meaning"][
        "relation_semantic_unit_refs"
    ] = [same_quote_facts[1]["point_relative_meaning"]["semantic_unit_ref"]]
    same_quote_facts[1]["point_relative_meaning"]["statement"] = (
        "A different exact meaning retained from the same literal quote."
    )
    same_quote_brief = consolidation_judgment._compile_point_reader_brief_from_validated_facts(
        manifest,
        point=manifest["points"][0],
        facts=same_quote_facts,
        response={
            "point_input_sha256": manifest["points"][0]["point_input_sha256"],
            "point_id": manifest["points"][0]["point_id"],
            "interpretation": "One quote retains two distinct bounded meanings.",
            "representative_handles": [
                {"placement_id": fact["placement_id"]}
                for fact in same_quote_facts
            ],
        },
    )
    same_quote_representatives = same_quote_brief["representative_evidence"]
    assert same_quote_representatives[0]["exact_quote"] == same_quote_representatives[1][
        "exact_quote"
    ]
    assert (
        same_quote_representatives[0]["point_relative_meaning"]
        != same_quote_representatives[1]["point_relative_meaning"]
    )
    companion_only_fact = copy.deepcopy(support_source)
    companion = companion_only_fact["companion_meanings"][0]
    companion_only_fact["point_relative_meaning"][
        "relation_semantic_unit_refs"
    ] = [companion["semantic_unit_ref"]]
    companion_facts = [
        companion_only_fact,
        next(fact for fact in first_facts if fact["relation"] == "counter"),
    ]
    companion_brief = consolidation_judgment._compile_point_reader_brief_from_validated_facts(
        manifest,
        point=manifest["points"][0],
        facts=companion_facts,
        response={
            "point_input_sha256": manifest["points"][0]["point_input_sha256"],
            "point_id": manifest["points"][0]["point_id"],
            "interpretation": "The relation uses an exact same-evidence companion.",
            "representative_handles": [
                {"placement_id": fact["placement_id"]} for fact in companion_facts
            ],
        },
    )
    companion_representative = companion_brief["representative_evidence"][0]
    assert companion_representative["point_relative_meaning"][
        "semantic_unit_ref"
    ] == companion["semantic_unit_ref"]
    assert companion_representative["selected_row_meaning"][
        "semantic_unit_ref"
    ] == support_source["point_relative_meaning"]["semantic_unit_ref"]
    assert companion_representative["quote_status"] == "quote_unavailable"
    assert companion_representative["quote_span_id"] is None
    assert companion_representative["exact_quote"] is None
    assert companion_representative["selected_row_quote"] == support_source["quote"]
    companion_meaning = companion_representative["point_relative_meaning"]
    selected_row_meaning = companion_representative["selected_row_meaning"]
    # A companion binding carries only its own semantic fields; the ones it does
    # not carry must read as unbound rather than as the selected row's values.
    assert companion_meaning["axis_ids"] is None
    assert companion_meaning["conditions"] is None
    assert companion_meaning["product_version_ids"] is None
    assert companion_meaning["uncertainty_posture"] is None
    assert companion_meaning["unbound_meaning_fields"] == [
        "axis_ids",
        "conditions",
        "product_version_ids",
        "uncertainty_posture",
    ]
    # Lineage stays the verbatim selected row, without relation-facing markers.
    assert "unbound_meaning_fields" not in selected_row_meaning
    assert selected_row_meaning == companion_only_fact["point_relative_meaning"]
    assert isinstance(selected_row_meaning["axis_ids"], list)
    assert isinstance(selected_row_meaning["conditions"], list)
    assert companion_meaning["statement"] == companion["normalized_meaning"]
    assert companion_meaning["polarity"] == companion["polarity"]
    assert "normalized_meaning" not in companion_meaning

    # A relation co-bound to the selected row keeps the headline meaning owned by
    # the same semantic unit as the headline quote, whatever order the refs list.
    co_bound_fact = copy.deepcopy(support_source)
    co_bound_fact["point_relative_meaning"]["relation_semantic_unit_refs"] = [
        companion["semantic_unit_ref"],
        support_source["point_relative_meaning"]["semantic_unit_ref"],
    ]
    co_bound_representative = consolidation_judgment._point_reader_representative(
        co_bound_fact
    )
    assert co_bound_representative["point_relative_meaning"]["semantic_unit_ref"] == (
        support_source["point_relative_meaning"]["semantic_unit_ref"]
    )
    assert co_bound_representative["quote_span_id"] == support_source["quote"][
        "quote_span_id"
    ]
    assert [
        meaning["semantic_unit_ref"]
        for meaning in co_bound_representative["relation_bound_meanings"]
    ] == co_bound_fact["point_relative_meaning"]["relation_semantic_unit_refs"]
    co_bound_by_ref = {
        meaning["semantic_unit_ref"]: meaning
        for meaning in co_bound_representative["relation_bound_meanings"]
    }
    assert co_bound_by_ref[
        support_source["point_relative_meaning"]["semantic_unit_ref"]
    ]["unbound_meaning_fields"] == []
    assert co_bound_by_ref[companion["semantic_unit_ref"]][
        "unbound_meaning_fields"
    ] == ["axis_ids", "conditions", "product_version_ids", "uncertainty_posture"]
    support = support_source
    assert any(fact["relation"] == "counter" for fact in first_facts)
    with pytest.raises(EvidenceConsumerError) as caught:
        compile_point_reader_brief(
            manifest,
            point_store_dir=store,
            point_id=manifest["points"][0]["point_id"],
            response={
                "point_input_sha256": manifest["points"][0]["point_input_sha256"],
                "point_id": manifest["points"][0]["point_id"],
                "interpretation": "counterevidence deliberately omitted",
                "representative_handles": [
                    {"placement_id": support["placement_id"]}
                ],
            },
        )
    assert caught.value.boundary == "point_reader_response"

    wrong_state = copy.deepcopy(briefs[0])
    wrong_state["decision_state_ledger"][0]["state_assertions"][0][
        "state_kind"
    ] = "observed_repurchase"
    wrong_state["decision_state_ledger_sha256"] = _canonical_json_sha256(
        wrong_state["decision_state_ledger"]
    )
    wrong_state["brief_sha256"] = _canonical_json_sha256(
        {key: value for key, value in wrong_state.items() if key != "brief_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(
            manifest, point_store_dir=store, brief=wrong_state
        )
    assert caught.value.boundary == "point_reader_decision_state"
    wrong_state_output = copy.deepcopy(output)
    wrong_state_output["accepted_points"][0] = wrong_state
    wrong_state_output["axis_output_sha256"] = _canonical_json_sha256(
        {
            key: value
            for key, value in wrong_state_output.items()
            if key != "axis_output_sha256"
        }
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_point_reader_output(
            manifest, output=wrong_state_output, point_store_dir=store
        )
    assert caught.value.boundary == "point_reader_decision_state"

    wrong_quote_output = copy.deepcopy(output)
    wrong_quote = wrong_quote_output["accepted_points"][0]
    wrong_quote["representative_evidence"][0]["exact_quote"] = "borrowed quote"
    wrong_quote["brief_sha256"] = _canonical_json_sha256(
        {key: value for key, value in wrong_quote.items() if key != "brief_sha256"}
    )
    wrong_quote_output["axis_output_sha256"] = _canonical_json_sha256(
        {
            key: value
            for key, value in wrong_quote_output.items()
            if key != "axis_output_sha256"
        }
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_axis_point_reader_output(
            manifest, output=wrong_quote_output, point_store_dir=store
        )
    assert caught.value.boundary == "point_reader_brief"

    wrong_meaning = copy.deepcopy(briefs[0])
    wrong_meaning["representative_evidence"][0]["point_relative_meaning"][
        "statement"
    ] = "meaning moved from another evidence placement"
    wrong_meaning["brief_sha256"] = _canonical_json_sha256(
        {key: value for key, value in wrong_meaning.items() if key != "brief_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(
            manifest, point_store_dir=store, brief=wrong_meaning
        )
    assert caught.value.boundary == "point_reader_brief"

    wrong_accounting_brief = copy.deepcopy(briefs[0])
    wrong_accounting_brief["reader_accounting"]["candidate_pool_accounting"][
        "full_candidate_pool"
    ]["relation_counts"]["support"]["origin_count"] += 1
    wrong_accounting_brief["brief_sha256"] = _canonical_json_sha256(
        {
            key: value
            for key, value in wrong_accounting_brief.items()
            if key != "brief_sha256"
        }
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(
            manifest, point_store_dir=store, brief=wrong_accounting_brief
        )
    assert caught.value.boundary == "point_reader_brief"

    transferred = copy.deepcopy(briefs[0])
    transferred["decision_state_ledger"] = copy.deepcopy(
        briefs[1]["decision_state_ledger"]
    )
    transferred["decision_state_ledger_sha256"] = _canonical_json_sha256(
        transferred["decision_state_ledger"]
    )
    transferred["brief_sha256"] = _canonical_json_sha256(
        {key: value for key, value in transferred.items() if key != "brief_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(
            manifest, point_store_dir=store, brief=transferred
        )
    assert caught.value.boundary == "point_reader_decision_state"

    axis_bound = copy.deepcopy(briefs[0])
    axis_bound["snapshot_sha256"] = manifest["snapshot_sha256"]
    axis_bound["brief_sha256"] = _canonical_json_sha256(
        {key: value for key, value in axis_bound.items() if key != "brief_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        validate_point_reader_brief(
            manifest, point_store_dir=store, brief=axis_bound
        )
    assert caught.value.boundary == "point_reader_brief"

    mismatched_selected_identity = copy.deepcopy(first_facts[0])
    mismatched_selected_identity["decision_state"]["selected_id"] = (
        "selected_elsewhere"
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _point_reader_state_ledger([mismatched_selected_identity])
    assert caught.value.boundary == "point_reader_decision_state"


def test_point_reader_identity_binds_meaning_but_not_storage_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    first_path = tmp_path / "root_a" / "view.json"
    second_path = tmp_path / "root_b" / "view.json"
    _write(first_path, view)
    _write(second_path, view)
    subject = _point_reader_subject_identity()

    first, first_payloads = build_axis_point_reader_snapshot(
        view, source_view_path=first_path, subject_identity=subject
    )
    relocated, _ = build_axis_point_reader_snapshot(
        view, source_view_path=second_path, subject_identity=subject
    )
    assert [row["point_input_sha256"] for row in first["points"]] == [
        row["point_input_sha256"] for row in relocated["points"]
    ]

    changed_method, _ = build_axis_point_reader_snapshot(
        view,
        source_view_path=first_path,
        subject_identity=subject,
        method_text=POINT_READER_METHOD_TEXT + "\nMaterial method change.",
    )
    assert all(
        before["point_input_sha256"] != after["point_input_sha256"]
        for before, after in zip(first["points"], changed_method["points"], strict=True)
    )
    assert all(
        before["response_file"] != after["response_file"]
        for before, after in zip(first["points"], changed_method["points"], strict=True)
    )
    stale_response = _point_reader_response(
        first["points"][0],
        first_payloads[first["points"][0]["point_id"]],
    )
    _, changed_payloads = build_axis_point_reader_snapshot(
        view,
        source_view_path=first_path,
        subject_identity=subject,
        method_text=POINT_READER_METHOD_TEXT + "\nMaterial method change.",
    )
    changed_store = tmp_path / "changed_store"
    _write_point_reader_store(changed_store, changed_method, changed_payloads)
    with pytest.raises(EvidenceConsumerError) as caught:
        compile_point_reader_brief(
            changed_method,
            point_store_dir=changed_store,
            point_id=changed_method["points"][0]["point_id"],
            response=stale_response,
        )
    assert caught.value.boundary == "point_reader_response"
    changed_schema = copy.deepcopy(POINT_READER_RESPONSE_SCHEMA)
    changed_schema["description"] = "Material schema change"
    rebound_schema, _ = build_axis_point_reader_snapshot(
        view,
        source_view_path=first_path,
        subject_identity=subject,
        response_schema=changed_schema,
    )
    assert all(
        before["point_input_sha256"] != after["point_input_sha256"]
        for before, after in zip(first["points"], rebound_schema["points"], strict=True)
    )
    changed_subject = copy.deepcopy(subject)
    changed_subject["company_id"] = "another-company"
    rebound_subject, _ = build_axis_point_reader_snapshot(
        view, source_view_path=first_path, subject_identity=changed_subject
    )
    assert all(
        before["point_input_sha256"] != after["point_input_sha256"]
        for before, after in zip(first["points"], rebound_subject["points"], strict=True)
    )

    changed_one = copy.deepcopy(first["points"][0]["input_contract"])
    changed_one["decision_state_ledger_sha256"] = "f" * 64
    assert point_reader_input_sha256(changed_one) != first["points"][0][
        "point_input_sha256"
    ]
    assert first["points"][1]["point_input_sha256"] == relocated["points"][1][
        "point_input_sha256"
    ]


def test_point_reader_runner_reuses_valid_points_and_recovers_partial_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view_path = tmp_path / "view.json"
    identity_path = tmp_path / "subject.json"
    first_manifest_path = tmp_path / "run_1.json"
    second_manifest_path = tmp_path / "run_2.json"
    store = tmp_path / "point_store"
    _write(view_path, build_axis_consolidated_view(spec))
    _write(identity_path, _point_reader_subject_identity())

    first = build_point_reader_run(
        view_path=view_path,
        subject_identity_path=identity_path,
        manifest_output_path=first_manifest_path,
        point_store_dir=store,
    )
    assert first["materialized_point_count"] == 2
    assert first["reused_point_count"] == 0
    second = build_point_reader_run(
        view_path=view_path,
        subject_identity_path=identity_path,
        manifest_output_path=second_manifest_path,
        point_store_dir=store,
    )
    assert second["materialized_point_count"] == 0
    assert second["reused_point_count"] == 2
    assert second["snapshot_sha256"] == first["snapshot_sha256"]
    assert validate_point_reader_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        expected_snapshot_sha256=second["snapshot_sha256"],
    )["status"] == "valid"

    manifest = json.loads(second_manifest_path.read_text(encoding="utf-8"))
    responses = tmp_path / "responses"
    responses.mkdir()
    first_point = manifest["points"][0]
    first_payload = (store / first_point["point_payload_file"]).read_bytes()
    second_point = manifest["points"][1]
    second_payload = (store / second_point["point_payload_file"]).read_bytes()
    _write(
        responses / second_point["response_file"],
        _point_reader_response(second_point, second_payload),
    )
    request_path = tmp_path / "request.json"
    prepared = prepare_point_reader_request_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        point_id=first_point["point_id"],
        output_path=request_path,
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert prepared["response_file"] == first_point["response_file"]
    assert request["method_text"] == POINT_READER_METHOD_TEXT
    assert request["candidate_pool_accounting"] == first_point[
        "candidate_pool_accounting"
    ]
    assert request["response_schema"] == bind_point_reader_response_schema(
        manifest, first_point["point_id"]
    )
    request_batch = tmp_path / "requests"
    batch = prepare_point_reader_requests_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        output_dir=request_batch,
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert batch["materialized_request_count"] == 2
    assert batch["reused_request_count"] == 0
    replayed_batch = prepare_point_reader_requests_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        output_dir=request_batch,
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert replayed_batch["materialized_request_count"] == 0
    assert replayed_batch["reused_request_count"] == 2

    briefs = tmp_path / "brief_store"
    with pytest.raises(EvidenceConsumerError, match="response is missing"):
        finalize_point_reader_run(
            manifest_path=second_manifest_path,
            point_store_dir=store,
            responses_dir=responses,
            brief_store_dir=briefs,
            output_path=tmp_path / "partial_output.json",
            expected_snapshot_sha256=second["snapshot_sha256"],
        )
    assert len(list(briefs.glob("brief_*.json"))) == 1

    for point in manifest["points"][:1]:
        payload = (store / point["point_payload_file"]).read_bytes()
        _write(
            responses / point["response_file"],
            _point_reader_response(point, payload),
        )
    snapshot_validation_calls = 0
    original_snapshot_validation = (
        consolidation_runner.validate_axis_point_reader_snapshot
    )

    def count_snapshot_validation(*args: Any, **kwargs: Any) -> Any:
        nonlocal snapshot_validation_calls
        snapshot_validation_calls += 1
        return original_snapshot_validation(*args, **kwargs)

    monkeypatch.setattr(
        consolidation_runner,
        "validate_axis_point_reader_snapshot",
        count_snapshot_validation,
    )
    judgment_snapshot_validation_calls = 0
    original_judgment_snapshot_validation = (
        consolidation_judgment.validate_axis_point_reader_snapshot
    )

    def count_judgment_snapshot_validation(*args: Any, **kwargs: Any) -> Any:
        nonlocal judgment_snapshot_validation_calls
        judgment_snapshot_validation_calls += 1
        return original_judgment_snapshot_validation(*args, **kwargs)

    monkeypatch.setattr(
        consolidation_judgment,
        "validate_axis_point_reader_snapshot",
        count_judgment_snapshot_validation,
    )
    completed = finalize_point_reader_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        responses_dir=responses,
        brief_store_dir=briefs,
        output_path=tmp_path / "complete_output.json",
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert completed["compiled_point_count"] == 1
    assert completed["reused_brief_count"] == 1
    assert snapshot_validation_calls == 1
    assert judgment_snapshot_validation_calls == 0
    assert validate_point_reader_output_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        output_path=tmp_path / "complete_output.json",
        expected_snapshot_sha256=second["snapshot_sha256"],
    )["status"] == "valid"
    assert judgment_snapshot_validation_calls == 1

    empty_responses = tmp_path / "empty_responses"
    empty_responses.mkdir()
    replayed = finalize_point_reader_run(
        manifest_path=second_manifest_path,
        point_store_dir=store,
        responses_dir=empty_responses,
        brief_store_dir=briefs,
        output_path=tmp_path / "replayed_output.json",
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert replayed["compiled_point_count"] == 0
    assert replayed["reused_brief_count"] == 2
    assert snapshot_validation_calls == 2
    assert judgment_snapshot_validation_calls == 1


def test_point_reader_reuses_point_work_across_axis_snapshot_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Axis provenance may change without invalidating identical point work."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    view = build_axis_consolidated_view(spec)
    view_path = tmp_path / "view.json"
    identity_path = tmp_path / "subject.json"
    store = tmp_path / "point_store"
    responses = tmp_path / "responses"
    briefs = tmp_path / "briefs"
    requests = tmp_path / "requests"
    _write(view_path, view)
    _write(identity_path, _point_reader_subject_identity())

    first = build_point_reader_run(
        view_path=view_path,
        subject_identity_path=identity_path,
        manifest_output_path=tmp_path / "run_1.json",
        point_store_dir=store,
    )
    first_manifest = json.loads((tmp_path / "run_1.json").read_text(encoding="utf-8"))
    responses.mkdir()
    for point in first_manifest["points"]:
        payload = (store / point["point_payload_file"]).read_bytes()
        _write(responses / point["response_file"], _point_reader_response(point, payload))
    prepare_point_reader_requests_run(
        manifest_path=tmp_path / "run_1.json",
        point_store_dir=store,
        output_dir=requests,
        expected_snapshot_sha256=first["snapshot_sha256"],
    )
    finalize_point_reader_run(
        manifest_path=tmp_path / "run_1.json",
        point_store_dir=store,
        responses_dir=responses,
        brief_store_dir=briefs,
        output_path=tmp_path / "output_1.json",
        expected_snapshot_sha256=first["snapshot_sha256"],
    )

    view_path.write_text(
        json.dumps(view, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    second = build_point_reader_run(
        view_path=view_path,
        subject_identity_path=identity_path,
        manifest_output_path=tmp_path / "run_2.json",
        point_store_dir=store,
    )
    second_manifest = json.loads((tmp_path / "run_2.json").read_text(encoding="utf-8"))
    assert second["snapshot_sha256"] != first["snapshot_sha256"]
    assert [point["point_input_sha256"] for point in second_manifest["points"]] == [
        point["point_input_sha256"] for point in first_manifest["points"]
    ]
    replayed_requests = prepare_point_reader_requests_run(
        manifest_path=tmp_path / "run_2.json",
        point_store_dir=store,
        output_dir=requests,
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert replayed_requests["materialized_request_count"] == 0
    assert replayed_requests["reused_request_count"] == len(second_manifest["points"])

    empty_responses = tmp_path / "empty_responses"
    empty_responses.mkdir()
    replayed = finalize_point_reader_run(
        manifest_path=tmp_path / "run_2.json",
        point_store_dir=store,
        responses_dir=empty_responses,
        brief_store_dir=briefs,
        output_path=tmp_path / "output_2.json",
        expected_snapshot_sha256=second["snapshot_sha256"],
    )
    assert replayed["compiled_point_count"] == 0
    assert replayed["reused_brief_count"] == len(second_manifest["points"])


def test_point_reader_membership_scales_without_a_whole_axis_schema() -> None:
    for count in (1, 100, 1000):
        expected = [f"point_{index:04d}" for index in range(count)]
        assert validate_point_reader_completion_membership(
            expected, [{"point_id": point_id} for point_id in expected]
        ) == expected
        with pytest.raises(EvidenceConsumerError):
            validate_point_reader_completion_membership(
                expected, [{"point_id": point_id} for point_id in expected[:-1]]
            )
        if count > 1:
            duplicated = [{"point_id": point_id} for point_id in expected]
            duplicated[-1] = {"point_id": expected[0]}
            with pytest.raises(EvidenceConsumerError):
                validate_point_reader_completion_membership(expected, duplicated)


def test_cold_route_names_generic_commands_and_forbids_sibling_inference() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / "docs/workflows/phase_a_customer_evidence_completion_path_v0.md"
    ).read_text(encoding="utf-8")
    normalized_workflow = " ".join(workflow.split())
    repo_map = (repository_root / "docs/workflows/forseti_repo_map_v0.md").read_text(
        encoding="utf-8"
    )
    runner = (
        repository_root
        / "forseti-harness/runners/run_phase_a_evidence_axis_consolidation.py"
    ).read_text(encoding="utf-8")
    for required in (
        "phase_a_evidence_axis_pack_manifest_v1",
        "phase_a_evidence_axis_pack_v1",
        "build-axis-pack --manifest",
        "validate-axis-pack --pack",
        "build-dogfood-truth",
        "validate-dogfood-truth",
        "build-reader",
        "build-reader-accounting",
        "validate-reader-accounting",
        "validate-reader",
        "validate-reader-output",
        "bind-reader-output-schema",
        "build-point-reader-run",
        "validate-point-reader-run",
        "prepare-point-reader-requests",
        "finalize-point-reader-run",
        "validate-point-reader-output",
        "--facts-output-dir",
        "--facts-dir",
        "one complete displayed fact per line",
        "Direct Outcome, Decision State, and mixed axes",
        "position_unstable",
        "routed v2 consolidated view",
        "Absence from the small index is therefore not evidence",
        "Do not infer any sibling file",
        "phase_a_hydration_axis_pack_v2",
        "reconstructed hash-bound bytes",
        "independently produced historical artifact",
        "old consumer path remains replayable",
        "Use cold model dogfood only",
        "test_rejected_literal_frontier_relation_stays_accounted_without_forcing_display",
    ):
        assert required in normalized_workflow
    # Co-presence anywhere in the map is not a route.  The module names and the
    # owning workflow have to sit in one quick-index row, or a cold agent who
    # greps the map for the file it is about to change lands somewhere else.
    machinery_rows = [
        line
        for line in repo_map.splitlines()
        if line.lstrip().startswith("|")
        and "docs/workflows/phase_a_customer_evidence_completion_path_v0.md" in line
    ]
    assert len(machinery_rows) == 1
    for required in (
        "Phase A evidence machinery",
        "phase_a_evidence_selection.py",
        "phase_a_evidence_axis_consolidation.py",
    ):
        assert required in machinery_rows[0]
    assert 'subparsers.add_parser("build-axis-pack")' in runner
    assert '"prepare-relation-review"' not in runner
    assert '"finalize-relation-review"' not in runner
    assert 'subparsers.add_parser("build-point-reader-run")' in runner
    assert '"prepare-point-reader-requests"' in runner
    assert '"finalize-point-reader-run"' in runner
    assert 'subparsers.add_parser("validate-axis-pack")' in runner
    assert 'subparsers.add_parser("build-dogfood-truth")' in runner
    assert 'subparsers.add_parser("validate-dogfood-truth")' in runner


def test_current_direct_outcome_binding_reaches_both_reader_surfaces_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    direct_point_id, _ = _route_fixture_as_current_mixed(spec)
    axis_pack = json.loads(Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8"))
    descriptor = next(
        row for row in axis_pack["points"] if row["point_id"] == direct_point_id
    )
    artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
    authored_row = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["same_evidence_companion_meanings"]
    )
    companion_ref = authored_row["same_evidence_companion_meanings"][0][
        "semantic_unit_ref"
    ]
    _bind_current_direct_outcome_relations(
        spec,
        point_ids={direct_point_id},
        companion_for=(direct_point_id, authored_row["selected_id"]),
    )

    view = build_axis_consolidated_view(spec)
    assert RELATION_SEMANTIC_WARRANT_BOUNDARY in view["non_claims"]
    placement = next(
        row
        for row in view["point_placements"]
        if row["point_id"] == direct_point_id
        and row["selected_id"] == authored_row["selected_id"]
    )
    assert placement["relation_semantic_unit_refs"] == [companion_ref]

    decision_reader = view["decision_state_reader_surface"]
    assert RELATION_SEMANTIC_WARRANT_BOUNDARY in decision_reader["non_claims"]
    point_columns = decision_reader["point_table"]["columns"]
    semantic_rows = _reader_rows(decision_reader["semantic_unit_table"])
    direct_point = next(
        row
        for row in decision_reader["point_table"]["rows"]
        if row[point_columns.index("point_id")] == direct_point_id
    )
    relation_facts = direct_point[point_columns.index("relation_facts")]
    fact_columns = relation_facts["columns"]
    compact_fact = next(
        row
        for row in relation_facts["rows"]
        if row[fact_columns.index("selected_id")] == authored_row["selected_id"]
    )
    assert [
        semantic_rows[row_id]["semantic_unit_ref"]
        for row_id in compact_fact[
            fact_columns.index("relation_semantic_unit_row_ids")
        ]
    ] == [companion_ref]

    view_path = tmp_path / "current_mixed_view.json"
    _write(view_path, view)
    reader_manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "current_mixed_facts"
    )
    assert RELATION_SEMANTIC_WARRANT_BOUNDARY in reader_manifest["non_claims"]
    full_fact = next(
        json.loads(line)
        for line in fact_streams[direct_point_id].decode("utf-8").splitlines()
        if json.loads(line)["selected_id"] == authored_row["selected_id"]
    )
    assert full_fact["point_id"] == direct_point_id
    assert full_fact["selected_id"] == authored_row["selected_id"]
    assert full_fact["relation"] == authored_row["relation"]
    assert full_fact["evidence"]["evidence_id"] == authored_row["evidence_id"]
    assert full_fact["point_relative_meaning"][
        "relation_semantic_unit_refs"
    ] == [companion_ref]


def test_current_owned_relation_ref_substitution_fails_at_lineage_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    direct_point_id, _ = _route_fixture_as_current_mixed(spec)
    axis_pack = json.loads(Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8"))
    descriptor = next(
        row for row in axis_pack["points"] if row["point_id"] == direct_point_id
    )
    artifact = json.loads(Path(descriptor["artifact_path"]).read_text(encoding="utf-8"))
    authored_row = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["same_evidence_companion_meanings"]
    )
    companion_ref = authored_row["same_evidence_companion_meanings"][0][
        "semantic_unit_ref"
    ]
    spec_row = next(
        row
        for binding in spec["direct_outcome_relation_bindings"]
        if binding["point_id"] == direct_point_id
        for row in binding["rows"]
        if row["selected_id"] == authored_row["selected_id"]
    )
    assert spec_row["relation_semantic_unit_refs"] == [
        authored_row["semantic_unit_ref"]
    ]
    spec_row["relation_semantic_unit_refs"] = [companion_ref]

    with pytest.raises(
        EvidenceConsumerError, match="relation binding changed after selection"
    ) as caught:
        build_axis_consolidated_view(spec)
    assert caught.value.boundary == "relation_binding_lineage"


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing_all", "must cover every direct_outcome point"),
        ("missing_point", "do not cover every routed point"),
        ("missing_row", "lacks an explicit relation binding"),
        ("duplicate_ref", "invalid row binding"),
        ("foreign_ref", "foreign semantic unit"),
    ],
)
def test_current_direct_outcome_bindings_fail_at_the_explicit_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    match: str,
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    spec["schema_version"] = CURRENT_CONSOLIDATION_SPEC_VERSION
    if mutation != "missing_all":
        _bind_current_direct_outcome_relations(spec)
        if mutation == "missing_point":
            spec["direct_outcome_relation_bindings"].pop()
        elif mutation == "missing_row":
            spec["direct_outcome_relation_bindings"][0]["rows"].pop()
        elif mutation == "duplicate_ref":
            row = spec["direct_outcome_relation_bindings"][0]["rows"][0]
            row["relation_semantic_unit_refs"] *= 2
        else:
            spec["direct_outcome_relation_bindings"][0]["rows"][0][
                "relation_semantic_unit_refs"
            ] = ["foreign::semantic-unit"]

    with pytest.raises(EvidenceConsumerError, match=match) as caught:
        build_axis_consolidated_view(spec)
    assert caught.value.boundary == "direct_outcome_relation_binding"


def test_current_reader_refuses_missing_direct_binding_without_primary_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    direct_point_id, _ = _route_fixture_as_current_mixed(spec)
    view = build_axis_consolidated_view(spec)
    direct_placement = next(
        row
        for row in view["point_placements"]
        if row["point_id"] == direct_point_id
    )
    direct_placement.pop("relation_semantic_unit_refs")

    with pytest.raises(
        EvidenceConsumerError,
        match="relation_semantic_unit_refs must be a string list",
    ) as caught:
        consolidation_judgment._decision_state_reader_surface(view)
    assert caught.value.boundary == "direct_outcome_relation_binding"


def test_historical_v2_direct_outcome_keeps_its_stamped_primary_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    _route_every_point_as_decision_state(spec)
    spec["projection_routes"] = [
        {"projection_mode": "direct_outcome", "point_ids": ["point_a"]},
        {"projection_mode": "decision_state", "point_ids": ["point_b"]},
    ]
    spec["decision_state_bindings"] = [
        binding
        for binding in spec["decision_state_bindings"]
        if binding["point_id"] == "point_b"
    ]
    view = build_axis_consolidated_view(spec)
    placement = next(
        row for row in view["point_placements"] if row["point_id"] == "point_a"
    )
    assert "relation_semantic_unit_refs" not in placement
    primary_ref = placement["semantic_unit_ref"]

    reader = view["decision_state_reader_surface"]
    semantic_rows = _reader_rows(reader["semantic_unit_table"])
    point_columns = reader["point_table"]["columns"]
    point_row = next(
        row
        for row in reader["point_table"]["rows"]
        if row[point_columns.index("point_id")] == placement["point_id"]
    )
    relation_facts = point_row[point_columns.index("relation_facts")]
    fact_columns = relation_facts["columns"]
    fact_row = next(
        row
        for row in relation_facts["rows"]
        if row[fact_columns.index("selected_id")] == placement["selected_id"]
    )
    assert [
        semantic_rows[row_id]["semantic_unit_ref"]
        for row_id in fact_row[
            fact_columns.index("relation_semantic_unit_row_ids")
        ]
    ] == [primary_ref]

    view_path = tmp_path / "historical_v2_view.json"
    _write(view_path, view)
    _, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=tmp_path / "historical_v2_facts"
    )
    full_fact = next(
        json.loads(line)
        for line in fact_streams[placement["point_id"]].decode("utf-8").splitlines()
        if json.loads(line)["selected_id"] == placement["selected_id"]
    )
    assert full_fact["point_relative_meaning"][
        "relation_semantic_unit_refs"
    ] == [primary_ref]


def test_historical_spec_cannot_consume_current_row_owned_relation_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A v2 spec must not strip a v3 artifact's owned refs back to the primary."""

    _, spec, _ = _generic_fixture(tmp_path, monkeypatch)
    direct_point_id, _ = _route_fixture_as_current_mixed(spec)
    axis_pack = json.loads(
        Path(spec["source_axis_pack_path"]).read_text(encoding="utf-8")
    )
    descriptor = next(
        row for row in axis_pack["points"] if row["point_id"] == direct_point_id
    )
    artifact = json.loads(
        Path(descriptor["artifact_path"]).read_text(encoding="utf-8")
    )
    authored_row = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["same_evidence_companion_meanings"]
    )
    companion_ref = authored_row["same_evidence_companion_meanings"][0][
        "semantic_unit_ref"
    ]
    _bind_current_direct_outcome_relations(
        spec,
        point_ids={direct_point_id},
        companion_for=(direct_point_id, authored_row["selected_id"]),
    )
    current_view = build_axis_consolidated_view(copy.deepcopy(spec))
    current_placement = next(
        row
        for row in current_view["point_placements"]
        if row["point_id"] == direct_point_id
        and row["selected_id"] == authored_row["selected_id"]
    )
    assert current_placement["relation_semantic_unit_refs"] == [companion_ref]
    assert companion_ref != authored_row["semantic_unit_ref"]

    downgraded = copy.deepcopy(spec)
    downgraded["schema_version"] = CONSOLIDATION_SPEC_VERSION
    downgraded.pop("direct_outcome_relation_bindings", None)

    with pytest.raises(
        EvidenceConsumerError,
        match="historical consolidation spec cannot consume row-owned relation",
    ) as caught:
        build_axis_consolidated_view(downgraded)
    assert caught.value.boundary == "relation_binding_lineage"


def _decision_state_reconciliation_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    _, prior_spec, _ = _generic_fixture(tmp_path / "prior", monkeypatch)
    _route_every_point_as_decision_state(prior_spec)
    prior_spec_path = tmp_path / "prior_spec.json"
    _write(prior_spec_path, prior_spec)

    _, current_template, _ = _generic_fixture(tmp_path / "current", monkeypatch)
    _route_every_point_as_decision_state(current_template)
    _bind_current_direct_outcome_relations(current_template)
    current_template.pop("direct_outcome_relation_bindings", None)
    current_template_path = tmp_path / "current_template.json"
    _write(current_template_path, current_template)
    current_pack_path = Path(current_template["source_axis_pack_path"])
    plan = {
        "schema_version": DECISION_STATE_RECONCILIATION_PLAN_VERSION,
        "current_axes": [
            {
                "axis_pack": {
                    "path": str(current_pack_path),
                    "sha256": hash_file(current_pack_path),
                },
                "spec_template": {
                    "path": str(current_template_path),
                    "sha256": hash_file(current_template_path),
                },
            }
        ],
        "prior_specs": [
            {"path": str(prior_spec_path), "sha256": hash_file(prior_spec_path)}
        ],
    }
    return plan, prior_spec, prior_spec_path, current_template_path


def test_decision_state_reconciliation_reuses_stable_meaning_not_positional_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, prior_spec, _, template_path = _decision_state_reconciliation_fixture(
        tmp_path, monkeypatch
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template["decision_state_bindings"][0]["rows"][0]["state_assertions"][0][
        "state_kind"
    ] = "purchase_intent"
    _write(template_path, template)
    plan["current_axes"][0]["spec_template"]["sha256"] = hash_file(template_path)

    manifest = prepare_phase_a_decision_state_reconciliation(plan)
    assert manifest["counts"]["unresolved_semantic_unit_count"] == 0
    assert manifest["counts"]["reused_semantic_unit_count"] > 0
    assert manifest["response_schema"] is None

    output = finalize_phase_a_decision_state_reconciliation(
        manifest, adjudication=None
    )["hydration_and_moisture"]
    output_rows = {
        (binding["point_id"], row["selected_id"]): row
        for binding in output["decision_state_bindings"]
        for row in binding["rows"]
    }
    prior_rows = {
        (binding["point_id"], row["selected_id"]): row
        for binding in prior_spec["decision_state_bindings"]
        for row in binding["rows"]
    }
    assert {
        _canonical_json_sha256(assertion)
        for assertion in output_rows[("point_a", "selected_01")]["state_assertions"]
    } == {
        _canonical_json_sha256(assertion)
        for assertion in prior_rows[("point_a", "selected_01")]["state_assertions"]
    }
    assert all(
        assertion["state_kind"] != "purchase_intent"
        for binding in output["decision_state_bindings"]
        for row in binding["rows"]
        for assertion in row["state_assertions"]
    )
    build_axis_consolidated_view(output)


def test_decision_state_reconciliation_surfaces_conflicting_history_before_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, prior_spec, _, _ = _decision_state_reconciliation_fixture(
        tmp_path, monkeypatch
    )
    conflicting = copy.deepcopy(prior_spec)
    assertion = conflicting["decision_state_bindings"][0]["rows"][0][
        "state_assertions"
    ][0]
    assertion.update(
        {
            "state_kind": "preference_judgment",
            "commercial_direction": "favorable",
            "decision_object": "different fixture interpretation",
        }
    )
    conflicting_path = tmp_path / "conflicting_prior_spec.json"
    _write(conflicting_path, conflicting)
    plan["prior_specs"].append(
        {"path": str(conflicting_path), "sha256": hash_file(conflicting_path)}
    )

    manifest = prepare_phase_a_decision_state_reconciliation(plan)
    unresolved = [
        item
        for group in manifest["unresolved_evidence_groups"]
        for item in group["items"]
    ]
    assert unresolved
    assert any("conflicting_history" in item["causes"] for item in unresolved)
    assert manifest["response_schema"]["properties"]["schema_version"] == {
        "type": "string",
        "const": DECISION_STATE_ADJUDICATION_VERSION,
    }
    assert manifest["response_schema"]["properties"][
        "reconciliation_scope_sha256"
    ] == {
        "type": "string",
        "const": manifest["reconciliation_scope_sha256"],
    }
    assert manifest["reconciliation_scope_sha256"] in manifest["prompt"]
    assert "Decision State describes the actor, not the product outcome" in manifest[
        "prompt"
    ]
    assert "Use expectation_judgment only when" in manifest["prompt"]
    assert "a plain product attribute or observed outcome is context_only" in manifest[
        "prompt"
    ]
    assert "price and quantity alone do not prove it" in manifest["prompt"]
    assert "Ownership or carrying does not prove use" in manifest["prompt"]
    assert "without explicit ownership or use, is context_only" in manifest["prompt"]
    assert "prefers A over B" in manifest["prompt"]
    assert "exact midpoint numeric rating as mixed" in manifest["prompt"]
    assert "return every state separately" in manifest["prompt"]
    state_variants = {
        variant["properties"]["state_kind"].get("const"): variant
        for variant in manifest["response_schema"]["properties"]["judgments"][
            "items"
        ]["anyOf"]
    }
    assert state_variants[None]["properties"]["item_ids"]["maxItems"] == 1
    assert all(
        "uniqueItems" not in variant["properties"]["conditions"]
        for state_kind, variant in state_variants.items()
        if state_kind is not None
    )
    assert "List each condition once" in manifest["prompt"]
    assert state_variants["purchase"]["properties"]["commercial_direction"][
        "enum"
    ] == ["neutral"]
    assert state_variants["wear_event"]["properties"]["commercial_direction"][
        "enum"
    ] == ["neutral"]
    assert state_variants["repurchase_intent"]["properties"][
        "commercial_direction"
    ]["enum"] == ["toward_action"]
    with pytest.raises(
        EvidenceConsumerError, match="unresolved units require adjudication"
    ) as caught:
        finalize_phase_a_decision_state_reconciliation(manifest, adjudication=None)
    assert caught.value.boundary == "decision_state_reconciliation_adjudication"


def test_decision_state_reconciliation_adjudication_closes_exact_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, prior_spec, _, _ = _decision_state_reconciliation_fixture(
        tmp_path, monkeypatch
    )
    conflicting = copy.deepcopy(prior_spec)
    conflicting["decision_state_bindings"][0]["rows"][0]["state_assertions"][0].update(
        {
            "state_kind": "preference_judgment",
            "commercial_direction": "favorable",
            "decision_object": "different fixture interpretation",
        }
    )
    conflicting_path = tmp_path / "conflicting_prior_spec.json"
    _write(conflicting_path, conflicting)
    plan["prior_specs"].append(
        {"path": str(conflicting_path), "sha256": hash_file(conflicting_path)}
    )
    manifest = prepare_phase_a_decision_state_reconciliation(plan)
    item_ids = [
        item["identity_id"]
        for group in manifest["unresolved_evidence_groups"]
        for item in group["items"]
    ]
    adjudication = {
        "schema_version": DECISION_STATE_ADJUDICATION_VERSION,
        "reconciliation_scope_sha256": manifest["reconciliation_scope_sha256"],
        "judgments": [
            {
                "item_ids": [item_id],
                "classification": "context_only",
                "state_kind": None,
                "commercial_direction": None,
                "decision_object": None,
                "quantity": None,
                "conditions": [],
            }
            for item_id in item_ids
        ],
    }
    output = finalize_phase_a_decision_state_reconciliation(
        manifest, adjudication=adjudication
    )["hydration_and_moisture"]
    build_axis_consolidated_view(output)

    omitted = copy.deepcopy(adjudication)
    omitted["judgments"].pop()
    with pytest.raises(
        EvidenceConsumerError, match="does not cover every unresolved unit"
    ) as caught:
        finalize_phase_a_decision_state_reconciliation(
            manifest, adjudication=omitted
        )
    assert caught.value.boundary == "decision_state_reconciliation_adjudication"


def test_decision_state_reconciliation_runner_materializes_bound_provider_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, prior_spec, _, _ = _decision_state_reconciliation_fixture(
        tmp_path, monkeypatch
    )
    conflicting = copy.deepcopy(prior_spec)
    conflicting["decision_state_bindings"][0]["rows"][0]["state_assertions"][0][
        "decision_object"
    ] = "conflicting fixture object"
    conflicting_path = tmp_path / "runner_conflicting_spec.json"
    _write(conflicting_path, conflicting)
    plan["prior_specs"].append(
        {"path": str(conflicting_path), "sha256": hash_file(conflicting_path)}
    )
    plan_path = tmp_path / "reconciliation_plan.json"
    _write(plan_path, plan)
    manifest_path = tmp_path / "reconciliation_manifest.json"
    prompt_path = tmp_path / "reconciliation_prompt.txt"
    schema_path = tmp_path / "reconciliation_schema.json"

    result = consolidation_runner.prepare_decision_state_reconciliation_run(
        plan_path=plan_path,
        output_path=manifest_path,
        prompt_output=prompt_path,
        response_schema_output=schema_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert prompt_path.read_text(encoding="utf-8").rstrip("\n") == manifest["prompt"]
    assert json.loads(schema_path.read_text(encoding="utf-8")) == manifest[
        "response_schema"
    ]
    assert result["manifest_sha256"] == manifest["manifest_sha256"]
    assert result["prompt_file_sha256"] == hash_file(prompt_path)
    assert result["response_schema_file_sha256"] == hash_file(schema_path)

    with pytest.raises(ValueError, match="must be supplied together"):
        consolidation_runner.prepare_decision_state_reconciliation_run(
            plan_path=plan_path,
            output_path=tmp_path / "unused_manifest.json",
            prompt_output=tmp_path / "unused_prompt.txt",
            response_schema_output=None,
        )


def _repin_point_chain(
    descriptor: dict[str, Any],
    artifact: dict[str, Any],
    *,
    selection_axis_ids: list[str] | None = None,
) -> None:
    """Rehash one point's artifact, selection, and quote chain after an edit."""

    artifact_path = Path(descriptor["artifact_path"])
    inventory_hash = _canonical_json_sha256(
        [
            {
                key: value
                for key, value in row.items()
                if key not in {"relation", "reason_code", "relation_semantic_unit_refs"}
            }
            for row in artifact["candidate_dispositions"]
        ]
    )
    artifact["candidate_inventory_sha256"] = inventory_hash
    selection_path = Path(descriptor["selection_manifest_path"])
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selection["candidate_inventory_sha256"] = inventory_hash
    if selection_axis_ids is not None:
        selection["spec"] = {**selection["spec"], "axis_ids": list(selection_axis_ids)}
    _rehash_manifest(selection)
    _write(selection_path, selection)
    quote_path = Path(descriptor["quote_manifest_path"])
    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    quote["candidate_inventory_sha256"] = inventory_hash
    quote["selection_manifest_sha256"] = selection["manifest_sha256"]
    _rehash_manifest(quote)
    _write(quote_path, quote)
    artifact["selection_manifest_sha256"] = selection["manifest_sha256"]
    artifact["quote_manifest_sha256"] = quote["manifest_sha256"]
    _write(artifact_path, artifact)
    descriptor["artifact_sha256"] = hash_file(artifact_path)
    descriptor["selection_manifest_file_sha256"] = hash_file(selection_path)
    descriptor["selection_manifest_sha256"] = selection["manifest_sha256"]
    descriptor["quote_manifest_file_sha256"] = hash_file(quote_path)
    descriptor["quote_manifest_sha256"] = quote["manifest_sha256"]


def _rebuild_axis_pack(
    pack_path: Path, pack: dict[str, Any], *, axis_id: str
) -> None:
    rebuilt_manifest = _manifest(
        schema_version=AXIS_PACK_MANIFEST_VERSION,
        axis_id=axis_id,
        accepted_points=[
            {
                key: point[key]
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
            for point in pack["points"]
        ],
        rejected_points=copy.deepcopy(pack["rejected_points"]),
    )
    _write(pack_path, build_phase_a_evidence_axis_pack(rebuilt_manifest))


def _rebind_axis_pack(pack_path: Path, *, axis_id: str) -> None:
    """Move a fixture axis pack to another axis without changing any meaning."""

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    for descriptor in pack["points"]:
        artifact = json.loads(
            Path(descriptor["artifact_path"]).read_text(encoding="utf-8")
        )
        _repin_point_chain(descriptor, artifact, selection_axis_ids=[axis_id])
    _rebuild_axis_pack(pack_path, pack, axis_id=axis_id)


def _rewrite_point_meaning(
    pack_path: Path, *, point_id: str, semantic_unit_ref: str, suffix: str
) -> None:
    """Change one point meaning in place and rebuild the owning axis pack."""

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    descriptor = next(
        point for point in pack["points"] if point["point_id"] == point_id
    )
    artifact = json.loads(
        Path(descriptor["artifact_path"]).read_text(encoding="utf-8")
    )
    selected = next(
        row
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["semantic_unit_ref"] == semantic_unit_ref
    )
    selected["normalized_meaning"] += suffix
    candidate = next(
        row
        for row in artifact["candidate_dispositions"]
        if row["semantic_unit_ref"] == semantic_unit_ref
    )
    candidate["normalized_meaning"] = selected["normalized_meaning"]
    _repin_point_chain(descriptor, artifact)
    _rebuild_axis_pack(pack_path, pack, axis_id=pack["axis_id"])


def test_decision_state_reconciliation_treats_changed_content_as_new_judgment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, _, _, template_path = _decision_state_reconciliation_fixture(
        tmp_path, monkeypatch
    )
    current_pack_path = Path(plan["current_axes"][0]["axis_pack"]["path"])
    semantic_ref = "retailer:sephora:review1::dry"
    _rewrite_point_meaning(
        current_pack_path,
        point_id="point_b",
        semantic_unit_ref=semantic_ref,
        suffix=" Changed current wording.",
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template["source_axis_pack_sha256"] = hash_file(current_pack_path)
    _write(template_path, template)
    plan["current_axes"][0]["axis_pack"]["sha256"] = hash_file(current_pack_path)
    plan["current_axes"][0]["spec_template"]["sha256"] = hash_file(template_path)

    reconciliation = prepare_phase_a_decision_state_reconciliation(plan)
    changed = [
        item
        for group in reconciliation["unresolved_evidence_groups"]
        for item in group["items"]
        if item["semantic_unit_ref"] == semantic_ref
    ]
    assert len(changed) == 1
    assert changed[0]["causes"] == ["changed_content"]


def test_decision_state_reconciliation_rejects_cross_axis_meaning_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, _, _, _ = _decision_state_reconciliation_fixture(
        tmp_path / "first", monkeypatch
    )
    second_plan, _, _, second_template_path = _decision_state_reconciliation_fixture(
        tmp_path / "second", monkeypatch
    )
    second_pack_path = Path(second_plan["current_axes"][0]["axis_pack"]["path"])
    _rebind_axis_pack(second_pack_path, axis_id="value_and_quantity")

    def _rebind_plan() -> None:
        second_template = json.loads(
            second_template_path.read_text(encoding="utf-8")
        )
        second_template["axis_id"] = "value_and_quantity"
        second_template["source_axis_pack_sha256"] = hash_file(second_pack_path)
        _write(second_template_path, second_template)
        binding = {
            "axis_pack": {
                "path": str(second_pack_path),
                "sha256": hash_file(second_pack_path),
            },
            "spec_template": {
                "path": str(second_template_path),
                "sha256": hash_file(second_template_path),
            },
        }
        plan["current_axes"] = [plan["current_axes"][0], binding]

    _rebind_plan()
    shared = prepare_phase_a_decision_state_reconciliation(plan)
    assert [axis["axis_id"] for axis in shared["axes"]] == [
        "hydration_and_moisture",
        "value_and_quantity",
    ]
    axes_by_identity: dict[str, set[str]] = {}
    for row in shared["rows"]:
        for identity_id in row["identity_ids"]:
            axes_by_identity.setdefault(identity_id, set()).add(row["axis_id"])
    assert any(len(axes) > 1 for axes in axes_by_identity.values())

    _rewrite_point_meaning(
        second_pack_path,
        point_id="point_b",
        semantic_unit_ref="retailer:sephora:review1::dry",
        suffix=" Second axis wording.",
    )
    _rebind_plan()

    with pytest.raises(
        EvidenceConsumerError, match="conflicting content across axes"
    ) as caught:
        prepare_phase_a_decision_state_reconciliation(plan)
    assert caught.value.boundary == "decision_state_reconciliation_current_identity"
