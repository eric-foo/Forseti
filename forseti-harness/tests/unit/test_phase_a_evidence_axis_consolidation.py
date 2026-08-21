from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from harness_utils import hash_file
from judgment.phase_a_evidence_axis_consolidation import (
    CONSOLIDATION_SPEC_VERSION,
    build_axis_consolidated_view,
    validate_axis_consolidated_view,
)
from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    _canonical_json_sha256,
)
from runners.run_phase_a_evidence_axis_consolidation import build_run, validate_run


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _manifest(**values: Any) -> dict[str, Any]:
    values["manifest_sha256"] = _canonical_json_sha256(values)
    return values


def _candidate(
    candidate_id: str,
    *,
    evidence_id: str,
    semantic_ref: str,
    relation: str,
    origin: str,
    container: str,
    conditions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "semantic_unit_ref": semantic_ref,
        "relation": relation,
        "scoped_independence_key": origin,
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


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Path]]:
    monkeypatch.setattr(
        "judgment.phase_a_evidence_axis_consolidation.load_selection_sources",
        lambda _manifest: [],
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
        )
        quote_path = tmp_path / point_id / "quote.json"
        _write(quote_path, quote)
        relation_counts: dict[str, int] = {}
        for row in data["rows"]:
            relation_counts[row["relation"]] = relation_counts.get(row["relation"], 0) + 1
        artifact = {
            "point_id": point_id,
            "bounded_point": data["bounded_point"],
            "candidate_dispositions": data["candidates"],
            "candidate_inventory_sha256": inventory_hash,
            "selection_manifest_sha256": selection["manifest_sha256"],
            "truth_group_count": 2,
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
        "unique_evidence_count": 3,
        "unique_quote_span_count": 3,
        "unique_companion_meaning_count": 1,
        "available_quote_span_count": 3,
        "unavailable_quote_span_count": 0,
    }
    alice = next(row for row in view["origin_index"] if row["independence_key"] == "reddit:alice")
    assert len(alice["placement_ids"]) == 2
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
    assert validate_axis_consolidated_view(view) == view
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
    mutated = copy.deepcopy(view)
    mutated["point_placements"][0][field] = value
    mutated["view_sha256"] = _canonical_json_sha256(
        {key: item for key, item in mutated.items() if key != "view_sha256"}
    )
    with pytest.raises(EvidenceConsumerError, match="view_reprojection"):
        validate_axis_consolidated_view(mutated)


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
    assert validate_run(view_path=output_path)["view_sha256"] == result["view_sha256"]
    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_run(spec_path=spec_path, output_path=output_path)
