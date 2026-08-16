from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from judgment.phase_a_evidence_consumer import (
    EvidenceConsumerError,
    finalize_decision_batch,
    load_prepared_cases,
    prepare_decision_batch,
)
from runners.run_semantic_evidence_integration import (
    finalize_evidence_consumer_batch_run,
    prepare_evidence_consumer_batch_run,
)


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _packet(case_id: str, proposition_id: str, unique_suffix: str) -> dict:
    shared_semantic_ref = "evidence:shared::reaction"
    unique_evidence_id = f"evidence:{unique_suffix}"
    unique_semantic_ref = f"{unique_evidence_id}::tolerance"
    semantic_columns = [
        "semantic_unit_ref",
        "statement",
        "evidence_posture",
        "uncertainty_posture",
        "polarity",
        "subject_product_ids",
        "comparator_product_ids",
        "product_version_ids",
        "axis_ids",
        "conditions",
        "emerging_axis_labels",
    ]
    evidence_columns = [
        "evidence_id",
        "source_artifact_id",
        "source_ref",
        "container_id",
        "publication_time",
        "actor_identity",
        "independence_key",
        "public_identity_key",
        "engagement",
        "semantic_units",
    ]
    packet = {
        "schema_version": "phase_a_evidence_packet_v3",
        "cycle_id": "cycle",
        "question_id": "question",
        "selection": {"mode": "proposition", "proposition_ids": [proposition_id], "axis_ids": []},
        "source_bindings": {"bundle_sha256": "b" * 64, "corpus_sha256": "c" * 64},
        "catalogue_schema": {
            "format": "named_defaults_and_columns_with_positional_rows",
            "missing_value": None,
            "row_semantics": "named defaults and positional columns",
            "source_group_layout": "source grouped",
            "semantic_unit_defaults": {},
            "semantic_unit_columns": semantic_columns,
            "relation_link_columns": ["evidence_id", "semantic_unit_refs"],
        },
        "propositions": [
            {
                "proposition_id": proposition_id,
                "bounded_proposition": f"Bounded proposition for {case_id}.",
                "evidence_relations": {
                    "support": [["evidence:shared", [shared_semantic_ref]]],
                    "counter": [[unique_evidence_id, [unique_semantic_ref]]],
                    "adjacent": [],
                },
            }
        ],
        "source_groups": [
            {
                "source_family": "community",
                "source_role": "community_post",
                "engagement_kind": "points",
                "engagement_context": "native points at observation time",
                "evidence_defaults": {"independence_posture": "credited"},
                "evidence_columns": evidence_columns,
                "engagement_defaults": {"status": "engagement_available", "material_positive": False},
                "engagement_columns": ["raw_value", "observed_at"],
                "evidence_rows": [
                    [
                        "evidence:shared",
                        "source:shared",
                        "https://example.test/shared",
                        "container:shared",
                        "2026-08-01T00:00:00Z",
                        "actor-shared",
                        "independence:shared",
                        "public:shared",
                        [7, "2026-08-02T00:00:00Z"],
                        [[shared_semantic_ref, "Reported reaction.", "first_hand", "asserted", "affirmed", ["product"], [], [], ["reaction"], ["after use"], []]],
                    ],
                    [
                        unique_evidence_id,
                        f"source:{unique_suffix}",
                        f"https://example.test/{unique_suffix}",
                        f"container:{unique_suffix}",
                        "2026-08-03T00:00:00Z",
                        f"actor-{unique_suffix}",
                        f"independence:{unique_suffix}",
                        None,
                        [3, "2026-08-04T00:00:00Z"],
                        [[unique_semantic_ref, "Reported tolerance.", "first_hand", "asserted", "affirmed", ["product"], [], [], ["reaction"], ["individual"], []]],
                    ],
                ],
            }
        ],
        "containers": [
            {"container_id": "container:shared", "container_type": "conversation", "captured_at": "2026-08-05T00:00:00Z", "captured_leaf_count": 1, "completeness": "complete", "capture_boundary": "one leaf", "source_visible_total": 9},
            {"container_id": f"container:{unique_suffix}", "container_type": "conversation", "captured_at": "2026-08-05T00:00:00Z", "captured_leaf_count": 1, "completeness": "complete", "capture_boundary": "one leaf", "source_visible_total": 4},
        ],
        "selection_coverage": {"selected_proposition_count": 1, "truncated": False},
        "unmerged_axis_candidates": [],
        "unscoped_unmerged_candidates": [],
        "unresolved_axis_candidates": [],
        "full_evidence_resolution": {"source": "bound_semantic_evidence_bundle", "lookup_key": "evidence_id", "bundle_sha256": "b" * 64, "body_field": "text", "context_fields": ["product_context", "parent_context"]},
        "output_boundary": ["not a prevalence estimate", "not a causal judgment"],
        "model_api_calls": 0,
    }
    packet["packet_sha256"] = _canonical_hash(packet)
    return packet


def _case(case_id: str, proposition_id: str, suffix: str) -> dict:
    packet = _packet(case_id, proposition_id, suffix)
    return {
        "case_id": case_id,
        "packet_path": Path(f"{case_id}-packet.json"),
        "selectors_path": Path(f"{case_id}-selectors.json"),
        "packet": packet,
        "selectors": {
            "case_id": case_id,
            "proposition_id": proposition_id,
            "targets": [
                {"target_id": "T01", "evidence_id": "evidence:shared", "semantic_unit_ref": "evidence:shared::reaction"},
                {"target_id": "T02", "evidence_id": f"evidence:{suffix}", "semantic_unit_ref": f"evidence:{suffix}::tolerance"},
            ],
        },
    }


def _synthesis(support_ref: str, counter_ref: str) -> dict:
    return {
        "summary": "Bounded conflicting accounts remain individual reports.",
        "supporting_refs": [support_ref],
        "counter_refs": [counter_ref],
        "conditions_and_qualifiers": ["Individual conditions remain material."],
        "behavior_signals": ["No purchase behavior was captured."],
        "engagement_observations": ["Native points are preserved without cross-source comparison."],
        "uncertainties": ["No prevalence or causal inference is available."],
    }


def _response(cases: list[dict]) -> dict:
    return {
        "cases": [
            {
                "case_id": case["case_id"],
                "decisions": [
                    {
                        "proposition_id": case["selectors"]["proposition_id"],
                        "synthesis": _synthesis("evidence:shared", f"evidence:{case['case_id'][-1]}::tolerance"),
                    }
                ],
            }
            for case in cases
        ]
    }


def _cases() -> list[dict]:
    return [_case("case-1", "prop-1", "1"), _case("case-2", "prop-2", "2")]


def test_decision_batch_round_trip_is_exact_deterministic_and_source_owned() -> None:
    cases = _cases()
    prompt, schema, manifest = prepare_decision_batch(cases)
    response = _response(cases)

    first = finalize_decision_batch(cases, response)
    second = finalize_decision_batch(cases, response)

    assert first == second
    assert manifest["case_order"] == ["case-1", "case-2"]
    assert schema["required"] == ["cases"]
    assert "ORDERED_CASE_ENVELOPES_JSON" in prompt
    assert first[0]["reconstructed_rows"][0]["public_identity_key"] == "public:shared"
    assert first[0]["reconstructed_rows"][0]["engagement_raw_value"] == 7
    assert first[0]["relation_inventory"] == [
        {"evidence_id": "evidence:1", "semantic_unit_ref": "evidence:1::tolerance", "relation": "counter"},
        {"evidence_id": "evidence:shared", "semantic_unit_ref": "evidence:shared::reaction", "relation": "support"},
    ]
    assert first[0]["evidence_id_inventory"] == ["evidence:1", "evidence:shared"]
    assert first[0]["full_evidence_resolution"] == cases[0]["packet"]["full_evidence_resolution"]
    assert first[0]["bounded_proposition"] == "Bounded proposition for case-1."
    assert first[0]["evidence_packet"] == cases[0]["packet"]


def test_singleton_uses_measured_unbatched_response_envelope() -> None:
    case = _cases()[0]
    prompt, schema, manifest = prepare_decision_batch([case])
    response = _response([case])["cases"][0]

    artifacts = finalize_decision_batch([case], response)

    assert manifest["response_envelope"] == "single_case"
    assert schema["required"] == ["case_id", "decisions"]
    assert "CASE_SELECTORS_JSON" in prompt
    assert artifacts[0]["case_id"] == "case-1"


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("shuffled", "shuffled_proposition_order"),
        ("duplicate_proposition", "duplicate_proposition_id"),
        ("missing_result", "missing_proposition_result"),
        ("foreign_ref", "foreign_evidence_ref"),
        ("cross_batch_ref", "mutated_literal_ref"),
        ("foreign_judgment", "judgment_identity_mismatch"),
    ],
)
def test_decision_batch_wrong_cause_mutations_fail_at_first_boundary(
    mutation: str, boundary: str
) -> None:
    cases = _cases()
    response = _response(cases)
    if mutation == "shuffled":
        response["cases"].reverse()
    elif mutation == "duplicate_proposition":
        response["cases"][1]["decisions"][0]["proposition_id"] = "prop-1"
    elif mutation == "missing_result":
        response["cases"][0]["decisions"] = []
    elif mutation == "foreign_ref":
        response["cases"][1]["decisions"][0]["synthesis"]["counter_refs"] = ["evidence:1"]
    elif mutation == "cross_batch_ref":
        response["cases"][0]["decisions"][0]["synthesis"]["counter_refs"] = ["evidence:outside"]
    else:
        response["cases"][0]["decisions"], response["cases"][1]["decisions"] = response["cases"][1]["decisions"], response["cases"][0]["decisions"]

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_decision_batch(cases, response)
    assert caught.value.boundary == boundary


def test_prepare_rejects_unrelated_batch() -> None:
    cases = _cases()
    cases[1]["packet"]["source_bindings"]["bundle_sha256"] = "d" * 64
    cases[1]["packet"]["packet_sha256"] = _canonical_hash(
        {key: value for key, value in cases[1]["packet"].items() if key != "packet_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_decision_batch(cases)
    assert caught.value.boundary == "unrelated_batch"


def test_runner_prepares_and_finalizes_hash_bound_batch(tmp_path: Path) -> None:
    cases = _cases()
    spec_cases = []
    for case in cases:
        packet_path = tmp_path / f"{case['case_id']}-packet.json"
        selectors_path = tmp_path / f"{case['case_id']}-selectors.json"
        packet_path.write_text(json.dumps(case["packet"]), encoding="utf-8")
        selectors_path.write_text(json.dumps(case["selectors"]), encoding="utf-8")
        spec_cases.append({"case_id": case["case_id"], "packet_path": packet_path.name, "selectors_path": selectors_path.name})
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({"schema_version": "phase_a_evidence_consumer_batch_spec_v1", "cases": spec_cases}), encoding="utf-8")
    prompt_path = tmp_path / "prompt.txt"
    schema_path = tmp_path / "schema.json"
    manifest_path = tmp_path / "manifest.json"

    prepared = prepare_evidence_consumer_batch_run(
        spec_path=spec_path,
        prompt_out=prompt_path,
        response_schema_out=schema_path,
        manifest_out=manifest_path,
    )
    loaded = load_prepared_cases(json.loads(manifest_path.read_text(encoding="utf-8")))
    response_path = tmp_path / "response.json"
    response_path.write_text(json.dumps(_response(loaded)), encoding="utf-8")
    completed = finalize_evidence_consumer_batch_run(
        manifest_path=manifest_path,
        response_path=response_path,
        artifact_dir=tmp_path / "artifacts",
    )

    assert prepared["status"] == "PHASE_A_EVIDENCE_CONSUMER_BATCH_READY"
    assert prepared["model_api_calls"] == 0
    assert completed["status"] == "PHASE_A_EVIDENCE_CONSUMER_BATCH_COMPLETE"
    assert completed["case_order"] == ["case-1", "case-2"]
    assert len(completed["artifact_sha256"]) == 2
