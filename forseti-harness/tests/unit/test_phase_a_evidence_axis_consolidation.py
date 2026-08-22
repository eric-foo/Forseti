from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from harness_utils import hash_file
from judgment.phase_a_evidence_axis_consolidation import (
    AXIS_PACK_MANIFEST_VERSION,
    AXIS_PACK_VERSION,
    CONSOLIDATION_SPEC_VERSION,
    build_axis_consolidated_view,
    build_phase_a_evidence_axis_pack,
    point_placement_keys,
    validate_axis_consolidated_view,
    validate_phase_a_evidence_axis_pack,
)
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
)
from runners.run_phase_a_evidence_axis_consolidation import (
    build_axis_pack_run,
    build_run,
    validate_axis_pack_run,
    validate_run,
)


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
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "semantic_unit_ref": semantic_ref,
        "relation": relation,
        "scoped_independence_key": origin,
        "independence_posture": independence_posture,
        "container_id": container,
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
        inventory_hash = f"inventory_{point_id}"
        selection = _manifest(
            schema_version="phase_a_evidence_selection_manifest_v1",
            candidate_inventory_sha256=inventory_hash,
            spec={"axis_ids": ["hydration_and_moisture"]},
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


def test_cold_route_names_generic_commands_and_forbids_sibling_inference() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / "docs/workflows/phase_a_customer_evidence_completion_path_v0.md"
    ).read_text(encoding="utf-8")
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
        "Do not infer any sibling file",
        "phase_a_hydration_axis_pack_v2",
    ):
        assert required in workflow
    assert "Phase A customer-evidence point pack, generic axis pack" in repo_map
    assert "docs/workflows/phase_a_customer_evidence_completion_path_v0.md" in repo_map
    assert 'subparsers.add_parser("build-axis-pack")' in runner
    assert 'subparsers.add_parser("validate-axis-pack")' in runner
