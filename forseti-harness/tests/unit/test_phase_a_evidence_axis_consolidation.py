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
    CONSOLIDATED_VIEW_VERSION,
    CONSOLIDATION_SPEC_VERSION,
    DECISION_STATE_BOUNDARIES,
    DECISION_STATE_CONSUMER_CONTRACT,
    DIRECT_OUTCOME_BOUNDARIES,
    LEGACY_CONSOLIDATED_VIEW_VERSION,
    LEGACY_CONSOLIDATION_SPEC_VERSION,
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
                direction = "favorable" if row["relation"] == "support" else "unfavorable"
                assertions = [
                    {
                        "state_kind": "value_judgment",
                        "commercial_direction": direction,
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
                    }
                )
        bindings.append({"point_id": point_id, "rows": row_bindings})
    spec["projection_routes"] = [
        {"projection_mode": "decision_state", "point_ids": point_ids}
    ]
    spec["decision_state_bindings"] = bindings


def _projected_state_assertions(
    view: Mapping[str, Any], group: Mapping[str, Any]
) -> list[dict[str, Any]]:
    columns = view["decision_state_contract"]["state_row_columns"]
    return [dict(zip(columns, row)) for row in group["state_rows"]]


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
    assert "state_rows are exhaustive" in view["decision_state_contract"]["unasserted_state_rule"]
    assert "every placement exactly once" in view["decision_state_contract"]["placement_processing_rule"]
    assert "descriptive context only" in view["decision_state_contract"]["engagement_rule"]
    assert "coexistence only" in view["decision_state_contract"]["coexistence_rule"]
    assert build_axis_consolidated_view(spec) == view
    assert validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    ) == view


def test_decision_state_preserves_premium_potential_inputs_without_inference(
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
            "conditions": [],
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
    assert states["value_judgment"]["commercial_direction"] == "favorable"
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
        ("primary_as_context", "primary semantic unit is not a decision state"),
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
    else:
        primary_ref = first_row["state_assertions"][0]["semantic_unit_refs"][0]
        first_row["state_assertions"].pop(0)
        first_row["context_only_semantic_unit_refs"].append(primary_ref)

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


def test_v2_direct_outcome_requires_the_boundaries_owned_by_each_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, paths = _fixture(tmp_path, monkeypatch)
    artifact_path = paths["artifact_point_a"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["output_boundary"].remove("creator influence is not customer corroboration")
    _write(artifact_path, artifact)
    _refresh_axis_binding(spec, paths)

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
    state_row = mutated["decision_state_groups"][0]["state_rows"][0]
    state_row[0] = "purchase"
    state_row[1] = "neutral"
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
