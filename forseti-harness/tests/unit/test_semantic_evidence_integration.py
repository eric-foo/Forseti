from __future__ import annotations

from judgment import semantic_evidence_integration as semantic_module

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

from judgment.semantic_evidence_integration import (
    _packet_v2_engagement_observation,
    _packet_v3_group_layout,
    _validate_evidence_packet_v3_preserves_v2,
    _terminal_repair_coalesce_group,
    BATCH_COMPILATION_VERSION_V2,
    BATCH_COMPILATION_VERSION_V3,
    BATCH_RESPONSE_VERSION,
    BATCH_RESPONSE_VERSION_V2,
    BATCH_RESPONSE_VERSION_V3,
    BATCH_KEYED_RESPONSE_VERSION,
    BATCH_KEYED_RESPONSE_VERSION_V2,
    BATCH_KEYED_RESPONSE_VERSION_V3,
    BUNDLE_VERSION,
    BUNDLE_VERSION_V2,
    BUNDLE_VERSION_V3,
    BUNDLE_VERSION_V4,
    BUNDLE_VERSION_V5,
    EVIDENCE_PACKET_VERSION,
    EVIDENCE_PACKET_VERSION_V1,
    EVIDENCE_PACKET_VERSION_V2,
    METHOD_TEXT_V5,
    METHOD_TEXT_V6,
    METHOD_TEXT_V7,
    METHOD_TEXT_V8,
    METHOD_TEXT_V9,
    METHOD_TEXT_V10,
    METHOD_VERSION,
    METHOD_VERSION_V2,
    METHOD_VERSION_V3,
    METHOD_VERSION_V4,
    METHOD_VERSION_V5,
    METHOD_VERSION_V6,
    METHOD_VERSION_V7,
    METHOD_VERSION_V8,
    METHOD_VERSION_V9,
    METHOD_VERSION_V10,
    RECONCILIATION_POLICY_VERSION_V2,
    RELATION_CLOSURE_COMPILATION_VERSION,
    RELATION_CLOSURE_RESPONSE_VERSION,
    PROMPT_ENCODING_VERSION,
    ROW_VERIFICATION_METHOD_TEXT,
    ROW_VERIFICATION_METHOD_TEXT_V3,
    ROW_VERIFICATION_METHOD_TEXT_V4,
    ROW_VERIFICATION_METHOD_TEXT_V5,
    ROW_VERIFICATION_METHOD_TEXT_V6,
    ROW_VERIFICATION_METHOD_TEXT_V7,
    ROW_VERIFICATION_METHOD_TEXT_V8,
    ROW_VERIFICATION_METHOD_VERSION,
    ROW_VERIFICATION_METHOD_VERSION_V3,
    ROW_VERIFICATION_METHOD_VERSION_V4,
    ROW_VERIFICATION_METHOD_VERSION_V5,
    ROW_VERIFICATION_METHOD_VERSION_V6,
    ROW_VERIFICATION_METHOD_VERSION_V7,
    ROW_VERIFICATION_METHOD_VERSION_V8,
    ROW_VERIFICATION_RESPONSE_VERSION,
    TARGETED_AUDIT_RESPONSE_VERSION,
    TERMINAL_REPAIR_MIGRATION_COMPILATION_VERSION,
    RECONCILIATION_RESPONSE_VERSION,
    RECONCILIATION_RESPONSE_VERSION_V2,
    SOURCE_VERSION_V2,
    SOURCE_VERSION_V3,
    SemanticIntegrationError,
    VIEW_VERSION,
    WORK_UNIT_PROJECTION_VERSION_V2,
    apply_row_verification,
    apply_row_repair,
    build_batch_prompts,
    build_batch_response_schema,
    build_bundle,
    build_prompt_execution_pack,
    build_reconciliation_prompt,
    finalize_view,
    finalize_v3_view,
    finalize_relation_closed_view,
    is_terminal_reconciliation_compilation,
    materialize_source_v3,
    migrate_repaired_terminal_compilation,
    project_evidence_packet,
    project_evidence_packet_v1,
    project_evidence_packet_v2,
    prepare_reconciliation_stage,
    prepare_relation_closure_stage,
    prepare_row_verification,
    prepare_row_repair,
    prepare_targeted_benchmark_audit,
    reconstruct_prompt_execution_payload,
    validate_batch_responses,
    validate_row_verified_compilation,
    validate_reconciliation_stage,
    validate_relation_closure_stage,
    validate_targeted_benchmark_audit,
    verify_bundle_context,
)
from judgment.semantic_calibration import (
    ADJUDICATION_CONTRACT_ID,
    ADJUDICATION_CONTRACT_SHA256,
    CALIBRATION_ADJUDICATION_VERSION,
    CALIBRATION_ADJUDICATION_VERSION_V1,
    CALIBRATION_ADJUDICATION_VERSION_V2,
    CALIBRATION_PREPARATION_VERSION,
    CALIBRATION_PREPARATION_VERSION_V1,
    CALIBRATION_REPORT_VERSION,
    CALIBRATION_REPORT_VERSION_V1,
    CALIBRATION_SPEC_VERSION,
    CALIBRATION_SPEC_VERSION_V1,
    SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT,
    SemanticCalibrationError,
    adjudication_contract_identity,
    evaluate_semantic_calibration,
    prepare_semantic_calibration,
    validate_calibration_spec,
)
from runners.run_semantic_evidence_integration import (
    _parser as _semantic_integration_parser,
    evaluate_semantic_calibration_run,
    migrate_repaired_terminal_run,
    prepare_batches,
    prepare_relation_closure_run,
    prepare_row_repair_run,
    prepare_prompt_execution_pack,
    project_evidence_packet_run,
    prepare_semantic_calibration_run,
    prepare_row_verification_run,
    prepare_targeted_benchmark_audit_run,
    publish_batch_response_file,
    submit_row_verification_run,
    submit_relation_closure_run,
    submit_row_repair_run,
    validate_relation_closure_response_file,
    verify_prompt_execution_pack,
)


def _digest(data: bytes = b"source\n") -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _source() -> dict:
    return {
        "cycle_id": "summer-fridays-understanding",
        "question_id": "phase-a-evidence-integration",
        "question": "What do customers choose and why?",
        "axes": [
            {"axis_id": "comfort", "label": "Comfort"},
            {"axis_id": "wear_and_longevity", "label": "Wear and longevity"},
        ],
        "source_artifacts": [
            {
                "artifact_id": "community-coding",
                "locator": "community.json",
                "sha256": _digest(),
            },
            {
                "artifact_id": "retailer-coding",
                "locator": "retailer.json",
                "sha256": _digest(),
            },
            {
                "artifact_id": "owned-capture",
                "locator": "owned.json",
                "sha256": _digest(),
            },
        ],
        "evidence_units": [
            {
                "evidence_id": "reddit:1ft1w8d:lppwb5s",
                "source_family": "reddit_community",
                "source_role": "community_post",
                "source_artifact_id": "community-coding",
                "source_ref": "https://reddit.test/1ft1w8d#lppwb5s",
                "text": (
                    "These smell good and more comfortable than ole henriksen "
                    "and lasts longer on lips than laneige glowy but I find it "
                    "to disappear still too quickly."
                ),
                "product_candidates": ["sf-lbb", "ole-pout", "laneige-glowy"],
                "axis_candidates": ["comfort", "wear_and_longevity"],
                "independence_key": "reddit:u/customer-a",
                "engagement": {"material_positive": False, "kind": "points", "value": 1},
            },
            {
                "evidence_id": "retailer:laneige-wear-1",
                "source_family": "retailer_reviews",
                "source_role": "retailer_review",
                "source_artifact_id": "retailer-coding",
                "source_ref": "retailer:review-1",
                "text": "Laneige lasts longer than Summer Fridays for me.",
                "product_candidates": ["sf-lbb", "laneige-glowy"],
                "axis_candidates": ["wear_and_longevity"],
                "independence_key": "retailer:reviewer-b",
                "engagement": {"material_positive": False},
            },
            {
                "evidence_id": "owned:sf-pdp",
                "source_family": "owned_product",
                "source_role": "owned_source",
                "source_artifact_id": "owned-capture",
                "source_ref": "https://summerfridays.test/lbb",
                "text": "A cushiony balm formulated for lasting hydration.",
                "product_candidates": ["sf-lbb"],
                "axis_candidates": ["comfort", "wear_and_longevity"],
                "independence_key": "owned:summer-fridays",
                "engagement": {"material_positive": False},
            },
            {
                "evidence_id": "reddit:echo",
                "source_family": "reddit_community",
                "source_role": "community_post",
                "source_artifact_id": "community-coding",
                "source_ref": "https://reddit.test/echo",
                "text": "Same author's follow-up without a new experience.",
                "product_candidates": ["sf-lbb"],
                "axis_candidates": [],
                "independence_key": "reddit:u/customer-a",
                "engagement": {"material_positive": False},
            },
        ],
    }


def _bundle(*, max_batch_chars: int = 80_000) -> dict:
    return build_bundle(_source(), max_batch_chars=max_batch_chars)


def _source_v2() -> dict:
    source = deepcopy(_source())
    source["schema_version"] = SOURCE_VERSION_V2
    for unit in source["evidence_units"]:
        unit["product_context"] = [
            {
                "context_type": "source_scope",
                "source_artifact_id": unit["source_artifact_id"],
                "text": "Summer Fridays Lip Butter Balm comparison corpus",
                "source_ref": unit["source_ref"],
            }
        ]
    source["evidence_units"][0]["product_context"] = [
        {
            "context_type": "thread_title",
            "source_artifact_id": source["evidence_units"][0]["source_artifact_id"],
            "text": "Summer Fridays Brown Sugar mini doesn't seem full",
            "source_ref": source["evidence_units"][0]["source_ref"],
        }
    ]
    return source


def _batch_responses(bundle: dict) -> list[dict]:
    rows = {
        "reddit:1ft1w8d:lppwb5s": {
            "evidence_id": "reddit:1ft1w8d:lppwb5s",
            "disposition": "claim_bearing",
            "disposition_reason": "contains two product comparisons",
            "semantic_units": [
                {
                    "semantic_unit_key": "comfort-vs-ole",
                    "statement": "Summer Fridays felt more comfortable than Ole Henriksen.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["ole-pout"],
                    "axis_ids": ["comfort"],
                    "emerging_axis_labels": [],
                    "conditions": ["reported lip use"],
                },
                {
                    "semantic_unit_key": "wear-vs-laneige",
                    "statement": "Summer Fridays lasted longer than Laneige Glowy for this customer.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["laneige-glowy"],
                    "axis_ids": ["wear_and_longevity"],
                    "emerging_axis_labels": [],
                    "conditions": ["individual reported experience"],
                },
            ],
        },
        "retailer:laneige-wear-1": {
            "evidence_id": "retailer:laneige-wear-1",
            "disposition": "claim_bearing",
            "disposition_reason": "explicit opposing wear comparison",
            "semantic_units": [
                {
                    "semantic_unit_key": "laneige-wear-counter",
                    "statement": "Laneige lasted longer than Summer Fridays for this reviewer.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["laneige-glowy"],
                    "axis_ids": ["wear_and_longevity"],
                    "emerging_axis_labels": [],
                    "conditions": ["individual reported experience"],
                }
            ],
        },
        "owned:sf-pdp": {
            "evidence_id": "owned:sf-pdp",
            "disposition": "claim_bearing",
            "disposition_reason": "owned product positioning",
            "semantic_units": [
                {
                    "semantic_unit_key": "owned-lasting-hydration",
                    "statement": "Summer Fridays positions the balm as lasting hydration.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": [],
                    "axis_ids": ["wear_and_longevity"],
                    "emerging_axis_labels": [],
                    "conditions": ["owned claim at observed cutoff"],
                }
            ],
        },
        "reddit:echo": {
            "evidence_id": "reddit:echo",
            "disposition": "context_only",
            "disposition_reason": "no separate product experience",
            "semantic_units": [],
        },
    }
    responses = []
    for batch in bundle["batches"]:
        responses.append(
            {
                "schema_version": BATCH_RESPONSE_VERSION,
                "bundle_sha256": bundle["bundle_sha256"],
                "batch_id": batch["batch_id"],
                "evidence": [rows[evidence_id] for evidence_id in batch["evidence_ids"]],
            }
        )
    return responses


def _reconciliation(bundle: dict, compiled: dict) -> dict:
    return {
        "schema_version": RECONCILIATION_RESPONSE_VERSION,
        "bundle_sha256": bundle["bundle_sha256"],
        "compilation_sha256": compiled["compilation_sha256"],
        "propositions": [
            {
                "proposition_key": "sf-comfort-vs-ole",
                "bounded_proposition": (
                    "One captured customer reported Summer Fridays as more comfortable "
                    "than Ole Henriksen."
                ),
                "claim_kind": "customer_experience",
                "subject_product_ids": ["sf-lbb"],
                "comparator_product_ids": ["ole-pout"],
                "axis_ids": ["comfort"],
                "emerging_axis_labels": [],
                "conditions": ["reported lip use"],
                "relations": [
                    {
                        "semantic_unit_ref": "reddit:1ft1w8d:lppwb5s::comfort-vs-ole",
                        "relation": "support",
                    }
                ],
                "opposition_checked": True,
                "causal_ceiling": "descriptive_only",
            },
            {
                "proposition_key": "sf-wear-vs-laneige",
                "bounded_proposition": (
                    "Captured customer reports disagree on whether Summer Fridays or "
                    "Laneige Glowy lasts longer."
                ),
                "claim_kind": "customer_experience",
                "subject_product_ids": ["sf-lbb"],
                "comparator_product_ids": ["laneige-glowy"],
                "axis_ids": ["wear_and_longevity"],
                "emerging_axis_labels": [],
                "conditions": ["individual reported experience"],
                "relations": [
                    {
                        "semantic_unit_ref": "reddit:1ft1w8d:lppwb5s::wear-vs-laneige",
                        "relation": "support",
                    },
                    {
                        "semantic_unit_ref": "retailer:laneige-wear-1::laneige-wear-counter",
                        "relation": "counter",
                    },
                ],
                "opposition_checked": True,
                "causal_ceiling": "descriptive_only",
            },
            {
                "proposition_key": "sf-owned-lasting-hydration",
                "bounded_proposition": "Summer Fridays used lasting-hydration positioning.",
                "claim_kind": "actor_strategy",
                "subject_product_ids": ["sf-lbb"],
                "comparator_product_ids": [],
                "axis_ids": ["wear_and_longevity"],
                "emerging_axis_labels": [],
                "conditions": ["owned claim at observed cutoff"],
                "relations": [
                    {
                        "semantic_unit_ref": "owned:sf-pdp::owned-lasting-hydration",
                        "relation": "support",
                    }
                ],
                "opposition_checked": False,
                "causal_ceiling": "descriptive_only",
            },
        ],
        "unmerged_semantic_units": [],
    }


def _compiled(bundle: dict) -> dict:
    return validate_batch_responses(bundle, _batch_responses(bundle))


def test_prompts_ask_for_meaning_and_account_for_every_alias() -> None:
    bundle = _bundle()
    prompts = build_batch_prompts(bundle)

    assert len(prompts) == 1
    normalized_prompt = " ".join(prompts[0]["prompt"].lower().split())
    assert "read for meaning rather than exact wording" in normalized_prompt
    for unit in bundle["evidence_units"]:
        assert unit["evidence_id"] in prompts[0]["prompt"]


def test_v2_prompts_bind_ambiguous_product_language_through_context() -> None:
    bundle = build_bundle(_source_v2())
    prompt = build_batch_prompts(bundle)[0]["prompt"]

    assert bundle["schema_version"] == BUNDLE_VERSION_V2
    assert bundle["method_version"] == METHOD_VERSION_V2
    assert "Product candidates are hypotheses, never product truth" in prompt
    assert "Summer Fridays Brown Sugar mini doesn't seem full" in prompt
    assert '"context_type": "thread_title"' in prompt


def test_legacy_source_remains_reproducible_as_v1() -> None:
    bundle = build_bundle(_source())

    assert bundle["schema_version"] == BUNDLE_VERSION
    assert bundle["method_version"] == METHOD_VERSION


@pytest.mark.parametrize(
    "product_context",
    [
        None,
        [],
        [
            {
                "context_type": "unknown",
                "source_artifact_id": "community-coding",
                "text": "title",
                "source_ref": "ref",
            }
        ],
        [
            {
                "context_type": "thread_title",
                "source_artifact_id": "community-coding",
                "text": "",
                "source_ref": "ref",
            }
        ],
    ],
)
def test_v2_rejects_missing_or_malformed_product_context(product_context: object) -> None:
    source = _source_v2()
    source["evidence_units"][0]["product_context"] = product_context

    with pytest.raises(SemanticIntegrationError, match="product_context"):
        build_bundle(source)


def test_v2_can_preserve_ambiguous_wrong_product_item_as_out_of_scope() -> None:
    source = _source_v2()
    unit = source["evidence_units"][0]
    unit["text"] = "Does it have a plumping effect or a lip burney feel?"
    unit["product_candidates"] = ["summer-fridays-lip-butter-balm"]
    unit["product_context"] = [
        {
            "context_type": "parent_text",
            "source_artifact_id": unit["source_artifact_id"],
            "text": "Question and replies concern the Summer Fridays Lip Oil.",
            "source_ref": unit["source_ref"],
        }
    ]
    bundle = build_bundle(source)
    responses = _batch_responses(bundle)
    response_unit = next(
        row
        for response in responses
        for row in response["evidence"]
        if row["evidence_id"] == unit["evidence_id"]
    )
    response_unit.update(
        {
            "disposition": "out_of_scope",
            "disposition_reason": "context binds the statement to Lip Oil, not Lip Butter Balm",
            "semantic_units": [],
        }
    )

    compiled = validate_batch_responses(bundle, responses)

    assert next(
        row
        for row in compiled["evidence_dispositions"]
        if row["evidence_id"] == unit["evidence_id"]
    )["disposition"] == "out_of_scope"


def test_v2_product_context_must_cite_a_pinned_source_artifact() -> None:
    source = _source_v2()
    source["evidence_units"][0]["product_context"][0][
        "source_artifact_id"
    ] = "not-pinned"

    with pytest.raises(SemanticIntegrationError, match="unknown source artifact"):
        build_bundle(source)


def test_v1_rejects_unversioned_product_context() -> None:
    source = _source()
    source["evidence_units"][0]["product_context"] = [
        {
            "context_type": "source_scope",
            "source_artifact_id": "community-coding",
            "text": "Lip Butter Balm",
            "source_ref": source["evidence_units"][0]["source_ref"],
        }
    ]

    with pytest.raises(SemanticIntegrationError, match="v1 source"):
        build_bundle(source)


def test_real_sf_sentence_keeps_ole_comfort_separate_from_laneige_wear() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    view = finalize_view(bundle, compiled, _reconciliation(bundle, compiled))

    by_text = {row["bounded_proposition"]: row for row in view["propositions"]}
    comfort = next(row for text, row in by_text.items() if "more comfortable" in text)
    wear = next(row for text, row in by_text.items() if "disagree" in text)

    assert comfort["comparator_product_ids"] == ["ole-pout"]
    assert comfort["axis_ids"] == ["comfort"]
    assert wear["comparator_product_ids"] == ["laneige-glowy"]
    assert wear["axis_ids"] == ["wear_and_longevity"]
    assert not [
        row
        for row in view["propositions"]
        if row["comparator_product_ids"] == ["ole-pout"]
        and "wear_and_longevity" in row["axis_ids"]
    ]


def test_view_preserves_counterevidence_and_complete_coverage() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    view = finalize_view(bundle, compiled, _reconciliation(bundle, compiled))
    wear = next(
        row for row in view["propositions"] if "disagree" in row["bounded_proposition"]
    )

    assert wear["claim_support"]["conflict_posture"] == "mixed"
    assert wear["claim_support"]["counterevidence_refs"] == [
        "retailer:laneige-wear-1"
    ]
    assert view["coverage"] == {
        "admitted_evidence_unit_count": 4,
        "accounted_evidence_unit_count": 4,
        "source_family_counts": {
            "owned_product": 1,
            "reddit_community": 2,
            "retailer_reviews": 1,
        },
        "unresolved_evidence_ids": [],
        "complete": True,
    }


def test_missing_alias_disposition_fails_at_coverage_gate() -> None:
    bundle = _bundle()
    responses = _batch_responses(bundle)
    responses[0]["evidence"].pop()

    with pytest.raises(SemanticIntegrationError, match="account for every alias"):
        validate_batch_responses(bundle, responses)


def test_stale_batch_hash_fails_before_semantic_compilation() -> None:
    bundle = _bundle()
    responses = _batch_responses(bundle)
    responses[0]["bundle_sha256"] = "0" * 64

    with pytest.raises(SemanticIntegrationError, match="stale bundle hash"):
        validate_batch_responses(bundle, responses)


def test_reconciliation_cannot_cross_comparator_bindings() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    response["propositions"][0]["comparator_product_ids"] = ["laneige-glowy"]

    with pytest.raises(SemanticIntegrationError, match="crosses product or comparator"):
        finalize_view(bundle, compiled, response)


def test_owned_claim_cannot_be_customer_experience_support() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    response["propositions"][2]["claim_kind"] = "customer_experience"

    with pytest.raises(SemanticIntegrationError, match="incompetent"):
        finalize_view(bundle, compiled, response)


def test_same_origin_does_not_gain_independence_credit() -> None:
    source = _source()
    source["evidence_units"][3]["text"] = "Summer Fridays was more comfortable than Ole."
    source["evidence_units"][3]["axis_candidates"] = ["comfort"]
    source["evidence_units"][3]["product_candidates"] = ["sf-lbb", "ole-pout"]
    bundle = build_bundle(source)
    responses = _batch_responses(bundle)
    echo = next(row for row in responses[0]["evidence"] if row["evidence_id"] == "reddit:echo")
    echo.update(
        {
            "disposition": "claim_bearing",
            "disposition_reason": "same author repeats the comparison",
            "semantic_units": [
                {
                    "semantic_unit_key": "comfort-repeat",
                    "statement": "Summer Fridays felt more comfortable than Ole.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["ole-pout"],
                    "axis_ids": ["comfort"],
                    "emerging_axis_labels": [],
                    "conditions": ["reported lip use"],
                }
            ],
        }
    )
    compiled = validate_batch_responses(bundle, responses)
    response = _reconciliation(bundle, compiled)
    response["propositions"][0]["relations"].append(
        {"semantic_unit_ref": "reddit:echo::comfort-repeat", "relation": "support"}
    )
    view = finalize_view(bundle, compiled, response)
    comfort = next(row for row in view["propositions"] if "more comfortable" in row["bounded_proposition"])

    assert comfort["claim_support"]["independent_origin_count"] == 1
    assert comfort["claim_support"]["support_posture"] == "isolated"


def test_emerging_axis_is_visible_but_not_added_to_axis_inventory() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    response["propositions"][0]["emerging_axis_labels"] = ["social-aura"]
    view = finalize_view(bundle, compiled, response)

    assert view["emerging_axis_candidates"] == ["social-aura"]
    assert {row["axis_id"] for row in bundle["axes"]} == {
        "comfort",
        "wear_and_longevity",
    }


def test_identical_inputs_produce_identical_bundle_and_view_hashes() -> None:
    first_bundle = _bundle()
    second_bundle = _bundle()
    first_compiled = _compiled(first_bundle)
    second_compiled = _compiled(second_bundle)
    first_view = finalize_view(
        first_bundle, first_compiled, _reconciliation(first_bundle, first_compiled)
    )
    second_view = finalize_view(
        second_bundle, second_compiled, _reconciliation(second_bundle, second_compiled)
    )

    assert first_bundle["bundle_sha256"] == second_bundle["bundle_sha256"]
    assert first_view["view_sha256"] == second_view["view_sha256"]


def test_all_semantic_units_must_be_reconciled_or_dispositioned() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    response["propositions"].pop()

    with pytest.raises(SemanticIntegrationError, match="every semantic unit"):
        finalize_view(bundle, compiled, response)


def test_reconciliation_prompt_contains_every_compiled_meaning() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    prompt = build_reconciliation_prompt(bundle, compiled)

    for unit in compiled["semantic_units"]:
        assert unit["semantic_unit_ref"] in prompt
    assert "V8 KEYED RESPONSE TRANSPORT" not in prompt
    assert "decisions_by_evidence_id" not in prompt


def test_uncredited_role_cannot_manufacture_cross_venue_credit() -> None:
    source = _source()
    source["evidence_units"][3]["independence_key"] = "reddit:u/customer-c"
    source["evidence_units"][3]["axis_candidates"] = ["comfort"]
    source["evidence_units"][3]["product_candidates"] = ["sf-lbb", "ole-pout"]
    source["evidence_units"].append(
        {
            "evidence_id": "retailer:uncredited-comfort",
            "source_family": "retailer_reviews",
            "source_role": "retailer_review",
            "source_artifact_id": "retailer-coding",
            "source_ref": "retailer:review-2",
            "text": "More comfortable than Ole Henriksen for me too.",
            "product_candidates": ["sf-lbb", "ole-pout"],
            "axis_candidates": ["comfort"],
            "engagement": {"material_positive": False},
        }
    )
    bundle = build_bundle(source)
    comfort_unit = {
        "subject_product_ids": ["sf-lbb"],
        "comparator_product_ids": ["ole-pout"],
        "axis_ids": ["comfort"],
        "emerging_axis_labels": [],
        "conditions": ["reported lip use"],
    }
    rows = {
        row["evidence_id"]: row
        for base_response in _batch_responses(_bundle())
        for row in base_response["evidence"]
    }
    rows["reddit:echo"] = {
        "evidence_id": "reddit:echo",
        "disposition": "claim_bearing",
        "disposition_reason": "second credited comfort comparison",
        "semantic_units": [
            {
                "semantic_unit_key": "comfort-second",
                "statement": "Summer Fridays felt more comfortable than Ole.",
                **comfort_unit,
            }
        ],
    }
    rows["retailer:uncredited-comfort"] = {
        "evidence_id": "retailer:uncredited-comfort",
        "disposition": "claim_bearing",
        "disposition_reason": "uncredited comfort comparison",
        "semantic_units": [
            {
                "semantic_unit_key": "comfort-uncredited",
                "statement": "Summer Fridays felt more comfortable than Ole Henriksen.",
                **comfort_unit,
            }
        ],
    }
    responses = [
        {
            "schema_version": BATCH_RESPONSE_VERSION,
            "bundle_sha256": bundle["bundle_sha256"],
            "batch_id": batch["batch_id"],
            "evidence": [rows[evidence_id] for evidence_id in batch["evidence_ids"]],
        }
        for batch in bundle["batches"]
    ]
    compiled = validate_batch_responses(bundle, responses)
    response = _reconciliation(bundle, compiled)
    response["propositions"][0]["relations"].extend(
        [
            {"semantic_unit_ref": "reddit:echo::comfort-second", "relation": "support"},
            {
                "semantic_unit_ref": "retailer:uncredited-comfort::comfort-uncredited",
                "relation": "support",
            },
        ]
    )
    view = finalize_view(bundle, compiled, response)
    comfort = next(
        row for row in view["propositions"] if "more comfortable" in row["bounded_proposition"]
    )

    assert comfort["claim_support"]["independent_origin_count"] == 2
    assert comfort["claim_support"]["support_posture"] == "independently_repeated"


def test_semantic_unit_ref_collision_is_rejected() -> None:
    source = _source()
    source["evidence_units"][0]["evidence_id"] = "amb"
    source["evidence_units"][1]["evidence_id"] = "amb::comfort"
    bundle = build_bundle(source)
    rows = {
        "amb": {
            "evidence_id": "amb",
            "disposition": "claim_bearing",
            "disposition_reason": "comfort comparison",
            "semantic_units": [
                {
                    "semantic_unit_key": "comfort::vs-ole",
                    "statement": "Summer Fridays felt more comfortable than Ole Henriksen.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["ole-pout"],
                    "axis_ids": ["comfort"],
                    "emerging_axis_labels": [],
                    "conditions": [],
                }
            ],
        },
        "amb::comfort": {
            "evidence_id": "amb::comfort",
            "disposition": "claim_bearing",
            "disposition_reason": "wear comparison",
            "semantic_units": [
                {
                    "semantic_unit_key": "vs-ole",
                    "statement": "Laneige lasted longer than Summer Fridays for this reviewer.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": ["laneige-glowy"],
                    "axis_ids": ["wear_and_longevity"],
                    "emerging_axis_labels": [],
                    "conditions": [],
                }
            ],
        },
        "owned:sf-pdp": {
            "evidence_id": "owned:sf-pdp",
            "disposition": "context_only",
            "disposition_reason": "not needed for this fixture",
            "semantic_units": [],
        },
        "reddit:echo": {
            "evidence_id": "reddit:echo",
            "disposition": "context_only",
            "disposition_reason": "no separate product experience",
            "semantic_units": [],
        },
    }
    responses = [
        {
            "schema_version": BATCH_RESPONSE_VERSION,
            "bundle_sha256": bundle["bundle_sha256"],
            "batch_id": batch["batch_id"],
            "evidence": [rows[evidence_id] for evidence_id in batch["evidence_ids"]],
        }
        for batch in bundle["batches"]
    ]

    with pytest.raises(SemanticIntegrationError, match="duplicate semantic unit ref"):
        validate_batch_responses(bundle, responses)


def test_tampered_bundle_with_stale_stored_hash_is_rejected() -> None:
    bundle = _bundle()
    responses = _batch_responses(bundle)
    tampered = next(
        row
        for row in bundle["evidence_units"]
        if row["evidence_id"] == "retailer:laneige-wear-1"
    )
    tampered["independence_key"] = "reddit:u/customer-a"

    with pytest.raises(SemanticIntegrationError, match="stored bundle_sha256"):
        validate_batch_responses(bundle, responses)


def test_tampered_compilation_with_stale_stored_hash_is_rejected() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    compiled["semantic_units"][0]["subject_product_ids"] = ["laneige-glowy"]

    with pytest.raises(SemanticIntegrationError, match="stored compilation_sha256"):
        finalize_view(bundle, compiled, response)


def test_unmerged_unit_emerging_axis_nomination_stays_visible() -> None:
    bundle = _bundle()
    responses = _batch_responses(bundle)
    echo = next(
        row for row in responses[0]["evidence"] if row["evidence_id"] == "reddit:echo"
    )
    echo.update(
        {
            "disposition": "claim_bearing",
            "disposition_reason": "mentions an application ritual",
            "semantic_units": [
                {
                    "semantic_unit_key": "ritual",
                    "statement": "The customer described a nightly application ritual.",
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": [],
                    "axis_ids": [],
                    "emerging_axis_labels": ["application_ritual"],
                    "conditions": [],
                }
            ],
        }
    )
    compiled = validate_batch_responses(bundle, responses)
    response = _reconciliation(bundle, compiled)
    response["unmerged_semantic_units"] = [
        {
            "semantic_unit_ref": "reddit:echo::ritual",
            "reason": "single ambiguous mention without a bounded proposition",
        }
    ]
    view = finalize_view(bundle, compiled, response)

    assert "application_ritual" in view["emerging_axis_candidates"]


def test_duplicate_proposition_identity_is_rejected() -> None:
    bundle = _bundle()
    compiled = _compiled(bundle)
    response = _reconciliation(bundle, compiled)
    clone = deepcopy(response["propositions"][0])
    clone["proposition_key"] = "sf-comfort-vs-ole-as-behavior"
    clone["claim_kind"] = "reported_behavior"
    response["propositions"].append(clone)

    with pytest.raises(SemanticIntegrationError, match="duplicate proposition identity"):
        finalize_view(bundle, compiled, response)


def test_prepare_runner_verifies_sources_and_makes_no_api_call(tmp_path: Path) -> None:
    for name in ("community.json", "retailer.json", "owned.json"):
        (tmp_path / name).write_bytes(b"source\n")
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(_source()), encoding="utf-8")

    result = prepare_batches(
        source_path=source_path,
        repo_root=tmp_path,
        bundle_out=tmp_path / "bundle.json",
        prompt_dir=tmp_path / "prompts",
        max_batch_chars=80_000,
    )

    assert result["status"] == "SEMANTIC_BATCH_JUDGMENT_REQUIRED"
    assert result["model_api_calls"] == 0
    assert (tmp_path / "prompts" / "batch-0001.md").is_file()


def test_prepare_runner_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    for name in ("community.json", "retailer.json", "owned.json"):
        (tmp_path / name).write_bytes(b"wrong\n")
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(_source()), encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        prepare_batches(
            source_path=source_path,
            repo_root=tmp_path,
            bundle_out=tmp_path / "bundle.json",
            prompt_dir=tmp_path / "prompts",
            max_batch_chars=80_000,
        )


def _source_v3(*, actor_mode: str = "distinct", count: int = 7) -> dict:
    artifacts = []
    containers = []
    items = []
    for index in range(count):
        artifact_id = f"thread-{index + 1}"
        container_id = f"reddit-thread-{index + 1}"
        evidence_id = f"reddit:t{index + 1}:comment"
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "locator": f"thread-{index + 1}.json",
                "sha256": _digest(f"thread-{index + 1}\n".encode()),
            }
        )
        containers.append(
            {
                "container_id": container_id,
                "container_type": "conversation",
                "source_artifact_id": artifact_id,
                "captured_leaf_count": 1,
                "source_visible_total": "unavailable",
                "completeness": "unavailable",
                "captured_at": "2026-08-08T00:00:00Z",
                "capture_boundary": "controlled one-leaf fixture",
            }
        )
        actor_key = "reddit:one-actor" if actor_mode == "same" else f"reddit:actor-{index + 1}"
        items.append(
            {
                "evidence_id": evidence_id,
                "container_id": container_id,
                "source_family": "reddit_community",
                "source_role": "community_post",
                "source_artifact_id": artifact_id,
                "source_ref": f"https://reddit.test/t{index + 1}",
                "text": "The balm became drying after a week of use.",
                "accounting_disposition": "assess",
                "accounting_reason": "captured text leaf inside fixture scope",
                "product_candidates": ["sf-lbb"],
                "axis_candidates": ["wear"],
                "product_context": [
                    {
                        "context_type": "thread_title",
                        "source_artifact_id": artifact_id,
                        "text": "Summer Fridays Lip Butter Balm wear",
                        "source_ref": f"https://reddit.test/t{index + 1}",
                    }
                ],
                "independence_posture": "credited",
                "independence_key": actor_key,
                "engagement": {"material_positive": False},
                "conversation_depth": 0,
                "parent_context": [],
            }
        )
    return {
        "schema_version": SOURCE_VERSION_V3,
        "cycle_id": "controlled-seven-thread-proof",
        "question_id": "drying-after-use",
        "question": "What captured customers report about wear",
        "corpus_profile": "bounded_regression_slice",
        "corpus_scope": "controlled seven-thread corpus",
        "corpus_cutoff": "2026-08-08T00:00:00Z",
        "axes": [{"axis_id": "wear", "label": "Wear"}],
        "source_artifacts": artifacts,
        "containers": containers,
        "captured_items": items,
    }


def _product_catalog(*, artifact_id: str = "thread-1") -> dict:
    catalog = {
        "schema_version": "product_identity_catalog_v1",
        "products": [
            {
                "stable_product_id": "summer-fridays-lip-butter-balm",
                "display_name": "Summer Fridays Lip Butter Balm",
                "source_product_ids": ["P455936", "sf-lbb"],
                "aliases": ["Lip Butter Balm"],
                "authority_artifact_ids": [artifact_id],
            }
        ],
    }
    catalog["catalog_sha256"] = _canonical_hash(catalog)
    return catalog


def _v3_batch_responses(bundle: dict) -> list[dict]:
    responses = []
    for batch in bundle["batches"]:
        rows = []
        for evidence_id in batch["evidence_ids"]:
            rows.append(
                {
                    "evidence_id": evidence_id,
                    "disposition": "claim_bearing",
                    "disposition_reason": "direct first-hand experience",
                    "semantic_units": [
                        {
                            "semantic_unit_key": "drying-after-week",
                            "statement": "The balm became drying after one week of use.",
                            "subject_product_ids": ["sf-lbb"],
                            "comparator_product_ids": [],
                            "product_version_ids": [],
                            "axis_ids": ["wear"],
                            "emerging_axis_labels": [],
                            "conditions": ["after one week of use"],
                            "polarity": "affirmed",
                            "evidence_posture": "first_hand",
                            "uncertainty_posture": "asserted",
                        }
                    ],
                }
            )
        responses.append(
            {
                "schema_version": BATCH_RESPONSE_VERSION_V2,
                "bundle_sha256": bundle["bundle_sha256"],
                "batch_id": batch["batch_id"],
                "evidence": rows,
            }
        )
    return responses


def _group_level_responses(stage: dict, *, terminal: bool) -> list[dict]:
    candidate_index = {row["candidate_ref"]: row for row in stage["candidates"]}
    responses = []
    for batch in stage["batches"]:
        selected = [candidate_index[ref] for ref in batch["candidate_refs"]]
        conditions = sorted(
            {
                condition
                for row in selected
                for lineage in row["condition_lineage"]
                for condition in lineage["conditions"]
            }
        )
        polarities = {row["polarity"] for row in selected}
        emerging_labels = sorted(
            {
                label
                for row in selected
                for label in row["emerging_axis_labels"]
            }
        )
        responses.append(
            {
                "schema_version": RECONCILIATION_RESPONSE_VERSION_V2,
                "stage_sha256": stage["stage_sha256"],
                "batch_id": batch["batch_id"],
                "semantic_nodes": [
                    {
                        "semantic_node_key": f"group-{batch['batch_id']}",
                        "bounded_meaning": "Captured customers reported drying after one week of use.",
                        "terminal_proposition": terminal,
                        "claim_kind": "customer_experience" if terminal else None,
                        "subject_product_ids": ["sf-lbb"],
                        "comparator_product_ids": [],
                        "product_version_ids": [],
                        "axis_ids": ["wear"],
                        "emerging_axis_labels": emerging_labels,
                        "conditions": conditions,
                        "polarity": next(iter(polarities)) if len(polarities) == 1 else "mixed",
                        "uncertainty_posture": "asserted",
                        "child_relations": [
                            {"child_ref": ref, "relation": "support"}
                            for ref in batch["candidate_refs"]
                        ],
                        "opposition_checked": True if terminal else None,
                        "causal_ceiling": "descriptive_only" if terminal else None,
                    }
                ],
                "unmerged_children": [],
                "emerging_axis_consolidations": [],
            }
        )
    return responses


def _v3_complete_view(*, actor_mode: str = "distinct") -> tuple[dict, dict, dict, dict]:
    return _v3_complete_view_at_ceiling(actor_mode=actor_mode, max_prompt_bytes=8_000)


def _v3_complete_view_at_ceiling(
    *, actor_mode: str = "distinct", max_prompt_bytes: int
) -> tuple[dict, dict, dict, dict]:
    bundle = build_bundle(
        _source_v3(actor_mode=actor_mode), max_prompt_bytes=max_prompt_bytes
    )
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage_one, _ = prepare_reconciliation_stage(bundle, compiled)
    level_one = validate_reconciliation_stage(
        bundle, stage_one, _group_level_responses(stage_one, terminal=False)
    )
    stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
    assert len(stage_two["batches"]) == 1
    level_two = validate_reconciliation_stage(
        bundle, stage_two, _group_level_responses(stage_two, terminal=True)
    )
    return bundle, compiled, level_two, finalize_v3_view(bundle, compiled, level_two)


def test_v3_seven_threads_stack_without_inventing_seven_people() -> None:
    _, _, _, distinct_view = _v3_complete_view(actor_mode="distinct")
    _, _, _, same_actor_view = _v3_complete_view(actor_mode="same")

    distinct = distinct_view["propositions"][0]
    same_actor = same_actor_view["propositions"][0]
    assert distinct["evidence_stack"]["support_evidence_item_count"] == 7
    assert distinct["evidence_stack"]["support_container_count"] == 7
    assert distinct["claim_support"]["independent_origin_count"] == 7
    assert same_actor["evidence_stack"]["support_container_count"] == 7
    assert same_actor["claim_support"]["independent_origin_count"] == 1


def _rehash_view(view: dict) -> dict:
    core = {key: value for key, value in view.items() if key != "view_sha256"}
    view["view_sha256"] = hashlib.sha256(
        json.dumps(
            core, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return view


def _rehash_batch_compilation(compilation: dict) -> dict:
    core = {
        key: value for key, value in compilation.items() if key != "compilation_sha256"
    }
    compilation["compilation_sha256"] = hashlib.sha256(
        json.dumps(
            core, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return compilation


def _packet_v3_evidence_rows(packet: dict) -> list[dict]:
    schema = packet["catalogue_schema"]
    semantic_columns = schema["semantic_unit_columns"]
    rows: list[dict] = []
    for source_group in packet["source_groups"]:
        evidence_columns = source_group["evidence_columns"]
        engagement_columns = source_group["engagement_columns"]
        for values in source_group["evidence_rows"]:
            evidence = deepcopy(source_group["evidence_defaults"])
            evidence.update(dict(zip(evidence_columns, values, strict=True)))
            engagement = deepcopy(source_group["engagement_defaults"])
            engagement.update(
                dict(zip(engagement_columns, evidence["engagement"], strict=True))
            )
            evidence["engagement"] = engagement
            evidence["semantic_units"] = [
                {
                    **schema["semantic_unit_defaults"],
                    **dict(zip(semantic_columns, semantic, strict=True)),
                }
                for semantic in evidence["semantic_units"]
            ]
            rows.append(evidence)
    return rows


@pytest.mark.parametrize(
    ("engagement", "expected"),
    [
        (
            {
                "material_positive": True,
                "materiality_basis": "Reddit score exceeds the self-vote baseline",
                "raw_score_state": "3 points",
            },
            (
                "score_state",
                "Reddit score exceeds the self-vote baseline",
                {
                    "raw_value": "3 points",
                    "observed_at": None,
                    "material_positive": True,
                },
            ),
        ),
        (
            {
                "material_positive": False,
                "materiality_basis": "positive helpful vote count exceeds zero",
                "raw_positive_helpful_count": None,
            },
            (
                "positive_helpful_count",
                "positive helpful vote count exceeds zero",
                {
                    "raw_value": None,
                    "observed_at": None,
                    "material_positive": False,
                },
            ),
        ),
    ],
)
def test_packet_normalizes_legacy_source_native_engagement_without_loss(
    engagement: dict, expected: tuple[str, str, dict]
) -> None:
    assert _packet_v2_engagement_observation({"engagement": engagement}) == expected


def test_packet_v3_keeps_required_available_engagement_field_when_all_values_are_null() -> None:
    _, _, defaults, columns = _packet_v3_group_layout(
        {
            "engagement_kind": "score_state",
            "evidence": [
                {
                    "evidence_id": "reddit:1:comment",
                    "engagement": {
                        "raw_value": "3 points",
                        "observed_at": None,
                        "material_positive": True,
                    },
                    "semantic_units": [],
                }
            ],
        }
    )

    assert defaults == {"raw_value": "3 points", "material_positive": True}
    assert columns == ["observed_at"]


@pytest.mark.parametrize(
    "engagement",
    [
        {"material_positive": True},
        {
            "material_positive": True,
            "raw_points": 3,
            "raw_likes": 4,
        },
        {
            "kind": "points",
            "raw_value": 3,
            "material_positive": True,
            "unpreserved_native_field": "loss",
        },
    ],
)
def test_packet_rejects_engagement_that_cannot_be_losslessly_normalized(
    engagement: dict,
) -> None:
    with pytest.raises(SemanticIntegrationError, match="engagement"):
        _packet_v2_engagement_observation({"engagement": engagement})


def test_v3_evidence_packet_returns_the_complete_stack_without_a_conclusion() -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]

    packet = project_evidence_packet(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )

    assert packet["schema_version"] == EVIDENCE_PACKET_VERSION
    assert packet["selection_coverage"] == {
        "selected_proposition_count": 1,
        "returned_evidence_item_count": 7,
        "returned_container_count": 7,
        "support_evidence_item_count": 7,
        "counter_evidence_item_count": 0,
        "adjacent_evidence_item_count": 0,
        "mixed_relation_evidence_item_count": 0,
        "independent_support_origin_count": 7,
        "support_source_role_count": 1,
        "support_source_roles": ["community_post"],
        "relation_count_semantics": (
            "distinct evidence union per relation; relation unions can overlap"
        ),
        "corpus_unmerged_semantic_unit_count": 0,
        "unmerged_axis_candidate_count": 0,
        "unscoped_unmerged_candidate_count": 0,
        "unresolved_axis_candidate_count": 0,
        "truncated": False,
    }
    evidence_rows = _packet_v3_evidence_rows(packet)
    assert len({row["evidence_id"] for row in evidence_rows}) == 7
    assert sum(row["evidence_count"] for row in packet["source_groups"]) == 7
    assert all("text" not in row for row in evidence_rows)
    assert all("source_role" not in row for row in evidence_rows)
    assert all("engagement_kind" in row for row in packet["source_groups"])
    assert all(
        {"raw_value", "observed_at", "material_positive"} <= set(row["engagement"])
        or row["engagement"] == {"status": "engagement_unavailable"}
        for row in evidence_rows
    )
    assert len(packet["containers"]) == 7
    linked_unit = next(
        unit for evidence in evidence_rows for unit in evidence["semantic_units"]
    )
    assert {
        "evidence_posture",
        "uncertainty_posture",
        "polarity",
    } <= set(linked_unit)
    assert all("conclusion" not in row for row in packet["propositions"])
    assert all("recommendation" not in row for row in packet["propositions"])
    assert packet["propositions"][0]["evidence_relations"]["support"]
    assert packet["catalogue_coverage"]["inline_full_text_evidence_item_count"] == 0
    assert packet["model_api_calls"] == 0


def test_evidence_packet_v1_remains_explicitly_reproducible() -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]

    packet = project_evidence_packet_v1(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )

    assert packet["schema_version"] == EVIDENCE_PACKET_VERSION_V1
    assert len({row["evidence_id"] for row in packet["evidence"]}) == 7
    assert "source_groups" not in packet


def test_evidence_packet_v2_remains_explicitly_reproducible() -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]

    packet = project_evidence_packet_v2(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )

    assert packet["schema_version"] == EVIDENCE_PACKET_VERSION_V2
    assert all("evidence" in row for row in packet["source_groups"])


def test_evidence_packet_runner_defaults_v3_and_preserves_explicit_v2(
    tmp_path: Path,
) -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]
    inputs = {
        "view_path": (tmp_path / "view.json", view),
        "bundle_path": (tmp_path / "bundle.json", bundle),
        "batch_compilation_path": (tmp_path / "compiled.json", compiled),
        "node_compilation_path": (tmp_path / "terminal.json", terminal),
    }
    for path, value in inputs.values():
        path.write_text(json.dumps(value), encoding="utf-8")
    kwargs = {
        key: path for key, (path, _) in inputs.items()
    }
    kwargs.update(
        {
            "axis_ids": [],
            "proposition_ids": [proposition_id],
        }
    )

    default_result = project_evidence_packet_run(
        **kwargs, packet_out=tmp_path / "default.json"
    )
    v2_result = project_evidence_packet_run(
        **kwargs, packet_out=tmp_path / "v2.json", packet_version="v2"
    )

    assert default_result["packet_schema_version"] == EVIDENCE_PACKET_VERSION
    assert v2_result["packet_schema_version"] == EVIDENCE_PACKET_VERSION_V2


def test_evidence_packet_v3_preservation_signal_rejects_wrong_cause_mutations() -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]
    baseline = project_evidence_packet_v2(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )
    candidate = project_evidence_packet(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )
    candidate.pop("packet_sha256")

    relation_mutation = deepcopy(candidate)
    relation_mutation["propositions"][0]["evidence_relations"]["support"].pop()
    with pytest.raises(SemanticIntegrationError, match="proposition relations"):
        _validate_evidence_packet_v3_preserves_v2(relation_mutation, baseline)

    engagement_mutation = deepcopy(candidate)
    engagement_index = candidate["source_groups"][0]["evidence_columns"].index(
        "engagement"
    )
    engagement_columns = candidate["source_groups"][0]["engagement_columns"]
    if "raw_value" in engagement_columns:
        raw_value_index = engagement_columns.index("raw_value")
        engagement_mutation["source_groups"][0]["evidence_rows"][0][
            engagement_index
        ][raw_value_index] = "removed"
    else:
        engagement_mutation["source_groups"][0]["engagement_defaults"][
            "raw_value"
        ] = "removed"
    with pytest.raises(SemanticIntegrationError, match="evidence rows"):
        _validate_evidence_packet_v3_preserves_v2(engagement_mutation, baseline)


def test_evidence_packet_v3_is_byte_deterministic() -> None:
    bundle, compiled, terminal, view = _v3_complete_view()
    proposition_id = view["propositions"][0]["proposition_id"]

    first = project_evidence_packet(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )
    second = project_evidence_packet(
        view, bundle, compiled, terminal, proposition_ids=[proposition_id]
    )

    assert first["packet_sha256"] == second["packet_sha256"]
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )


def test_v3_evidence_packet_axis_union_deduplicates_shared_evidence() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dogfood = (
        repo_root
        / "docs/research/summer_fridays_understanding_dogfood_20260802_p11r7"
        / "semantic_integration_multisource_route_1_6_regression_20260808_v0"
    )

    def load(name: str) -> dict:
        value = json.loads((dogfood / name).read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value

    bundle = load("bundle.json")
    compiled = load("batch_compilation.json")
    terminal = load("node_compilation_2.json")
    historical_view = load("view.json")
    view = finalize_v3_view(bundle, compiled, terminal)
    expected_view = deepcopy(historical_view)
    for proposition in expected_view["propositions"]:
        if proposition["claim_support"]["conflict_posture"] == "none_observed":
            proposition["claim_support"]["conflict_posture"] = "not_checked"
    _rehash_view(expected_view)
    assert view == expected_view

    packet = project_evidence_packet(
        view, bundle, compiled, terminal, axis_ids=["reaction_and_breakout"]
    )

    assert packet["selection_coverage"]["selected_proposition_count"] == 17
    assert packet["selection_coverage"]["returned_evidence_item_count"] == 44
    evidence_rows = _packet_v3_evidence_rows(packet)
    assert len({row["evidence_id"] for row in evidence_rows}) == 44
    assert len(packet["containers"]) == 30
    linked_evidence_ids = [
        link[
            packet["catalogue_schema"]["relation_link_columns"].index(
                "evidence_id"
            )
        ]
        for proposition in packet["propositions"]
        for relation_links in proposition["evidence_relations"].values()
        for link in relation_links
    ]
    per_proposition_links = len(linked_evidence_ids)
    assert per_proposition_links > 44
    shared_id = next(
        evidence_id
        for evidence_id in set(linked_evidence_ids)
        if linked_evidence_ids.count(evidence_id) > 1
    )
    assert sum(row["evidence_id"] == shared_id for row in evidence_rows) == 1


def test_v3_evidence_packet_preserves_counterevidence_and_unresolved_candidates() -> None:
    bundle = build_bundle(_source_v3(), max_prompt_bytes=8_000)
    responses = _v3_batch_responses(bundle)
    unresolved_evidence_id = responses[-1]["evidence"][-1]["evidence_id"]
    responses[-1]["evidence"][-1]["disposition"] = "unresolved"
    responses[-1]["evidence"][-1]["reason"] = "meaning remains ambiguous"
    responses[-1]["evidence"][-1]["semantic_units"] = []
    compiled = validate_batch_responses(bundle, responses)
    stage_one, _ = prepare_reconciliation_stage(bundle, compiled)
    level_one_responses = _group_level_responses(stage_one, terminal=False)
    level_one_responses[0]["semantic_nodes"][0]["child_relations"][0][
        "relation"
    ] = "counter"
    level_one = validate_reconciliation_stage(
        bundle, stage_one, level_one_responses
    )
    stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
    terminal_responses = _group_level_responses(stage_two, terminal=True)
    terminal = validate_reconciliation_stage(
        bundle, stage_two, terminal_responses
    )
    view = finalize_v3_view(bundle, compiled, terminal)

    packet = project_evidence_packet(
        view, bundle, compiled, terminal, axis_ids=["wear"]
    )

    assert packet["selection_coverage"]["counter_evidence_item_count"] > 0
    assert packet["selection_coverage"]["unresolved_axis_candidate_count"] == 1
    assert (
        packet["unresolved_axis_candidates"][0]["evidence_id"]
        == unresolved_evidence_id
    )


def test_v3_evidence_packet_keeps_no_axis_unmerged_meaning_visible() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dogfood = (
        repo_root
        / "docs/research/summer_fridays_understanding_dogfood_20260802_p11r7"
        / "semantic_integration_multisource_route_1_6_regression_20260808_v0"
    )

    def load(name: str) -> dict:
        value = json.loads((dogfood / name).read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value

    bundle = load("bundle.json")
    compiled = load("batch_compilation.json")
    terminal = load("node_compilation_2.json")
    unscoped_ref = terminal["unmerged_semantic_units"][0]["semantic_unit_ref"]
    semantic = next(
        row
        for row in compiled["semantic_units"]
        if row["semantic_unit_ref"] == unscoped_ref
    )
    semantic["axis_ids"] = []
    _rehash_batch_compilation(compiled)
    terminal["batch_compilation_sha256"] = compiled["compilation_sha256"]
    _rehash_node_compilation(terminal)
    view = finalize_v3_view(bundle, compiled, terminal)

    packet = project_evidence_packet(
        view, bundle, compiled, terminal, axis_ids=["reaction_and_breakout"]
    )

    assert packet["selection_coverage"]["corpus_unmerged_semantic_unit_count"] == 5
    assert packet["selection_coverage"]["unscoped_unmerged_candidate_count"] == 1
    assert packet["unscoped_unmerged_candidates"][0]["semantic_unit_ref"] == unscoped_ref


def test_v3_evidence_packet_fails_closed_on_unknown_or_inconsistent_selection() -> None:
    bundle, compiled, terminal, original = _v3_complete_view()
    proposition_id = original["propositions"][0]["proposition_id"]

    with pytest.raises(SemanticIntegrationError, match="unknown evidence-packet axis"):
        project_evidence_packet(
            original, bundle, compiled, terminal, axis_ids=["unknown"]
        )
    with pytest.raises(SemanticIntegrationError, match="exactly one selection mode"):
        project_evidence_packet(
            original,
            bundle,
            compiled,
            terminal,
            axis_ids=["wear"],
            proposition_ids=[proposition_id],
        )

    inconsistent = deepcopy(original)
    inconsistent["evidence_to_propositions"].pop(
        next(iter(inconsistent["evidence_to_propositions"]))
    )
    _rehash_view(inconsistent)
    with pytest.raises(SemanticIntegrationError, match="do not rebuild"):
        project_evidence_packet(
            inconsistent,
            bundle,
            compiled,
            terminal,
            proposition_ids=[proposition_id],
        )

    stale_compilation = deepcopy(compiled)
    stale_compilation["semantic_units"][0]["statement"] = "altered after finalization"
    _rehash_batch_compilation(stale_compilation)
    with pytest.raises(SemanticIntegrationError, match="root batch compilation"):
        project_evidence_packet(
            original,
            bundle,
            stale_compilation,
            terminal,
            proposition_ids=[proposition_id],
        )


def test_v3_prompts_never_exceed_actual_rendered_utf8_ceiling() -> None:
    bundle = build_bundle(_source_v3(), max_prompt_bytes=8_000)
    prompts = build_batch_prompts(bundle)

    assert bundle["schema_version"] == BUNDLE_VERSION_V4
    assert prompts
    assert all(row["prompt_utf8_bytes"] <= 8_000 for row in prompts)
    assert all("CONTEXT_TABLE" in row["prompt"] for row in prompts)
    proof = bundle["semantic_work_unit_projection"]["coverage_proof"]
    assert proof["bijection_complete"] is True
    assert proof["projected_evidence_count"] == proof["admitted_evidence_count"]
    oversized = _source_v3(count=1)
    oversized["captured_items"][0]["text"] = "é" * 8_000
    with pytest.raises(SemanticIntegrationError, match="rendered prompt byte ceiling"):
        build_bundle(oversized, max_prompt_bytes=8_000)


def test_method_v4_binds_stable_product_identity_and_preserves_v3_history() -> None:
    historical_source = _source_v3(count=2)
    historical = build_bundle(
        historical_source,
        max_prompt_bytes=8_000,
        target_bundle_version=BUNDLE_VERSION_V3,
    )
    assert historical["method_version"] == METHOD_VERSION_V3
    assert "semantic_method_version" not in historical

    source = deepcopy(historical_source)
    source["semantic_method_version"] = METHOD_VERSION_V4
    source["corpus_profile"] = "phase_a_final_acquisition"
    source["product_identity_catalog"] = _product_catalog()
    source["captured_items"][0]["product_candidates"] = []
    source["captured_items"][0]["text"] = (
        "Dream Lip Oil fades quickly, unlike this balm."
    )
    source["captured_items"][0]["product_context"][0]["text"] = (
        "Summer Fridays Lip Butter Balm [summer-fridays-lip-butter-balm]; "
        "source product id P455936"
    )

    bundle = build_bundle(source, max_prompt_bytes=8_000)
    prompt = build_batch_prompts(bundle)[0]["prompt"]

    assert bundle["method_version"] == METHOD_VERSION_V4
    assert bundle["semantic_method_version"] == METHOD_VERSION_V4
    assert "wording inside a review or comment may" in prompt
    assert "mention another product without changing" in prompt
    assert prompt.count("\n\nPRODUCT_IDENTITY_CATALOG\n") == 1
    assert "use it only as the run's verified" in prompt
    assert "summer-fridays-lip-butter-balm" in prompt
    assert materialize_source_v3(source)["semantic_method_version"] == METHOD_VERSION_V4

    with pytest.raises(SemanticIntegrationError, match="requires bundle v4"):
        build_bundle(
            source,
            max_prompt_bytes=8_000,
            target_bundle_version=BUNDLE_VERSION_V3,
        )


def test_method_v4_final_acquisition_catalog_fails_closed() -> None:
    source = _source_v3(count=1)
    source["semantic_method_version"] = METHOD_VERSION_V4
    source["corpus_profile"] = "phase_a_final_acquisition"

    with pytest.raises(SemanticIntegrationError, match="lacks product catalog"):
        build_bundle(source, max_prompt_bytes=12_000)

    source["product_identity_catalog"] = _product_catalog()
    tampered = deepcopy(source)
    tampered["product_identity_catalog"]["products"][0]["display_name"] = (
        "Altered product"
    )
    with pytest.raises(SemanticIntegrationError, match="stored catalog_sha256"):
        build_bundle(tampered, max_prompt_bytes=12_000)

    collision = deepcopy(source)
    collision["product_identity_catalog"]["products"].append(
        {
            "stable_product_id": "summer-fridays-second-balm",
            "display_name": "Summer Fridays Second Balm",
            "source_product_ids": ["second-balm"],
            "aliases": ["Lip Butter Balm"],
            "authority_artifact_ids": ["thread-1"],
        }
    )
    collision["product_identity_catalog"]["products"] = sorted(
        collision["product_identity_catalog"]["products"],
        key=lambda row: row["stable_product_id"],
    )
    collision["product_identity_catalog"]["catalog_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in collision["product_identity_catalog"].items()
            if key != "catalog_sha256"
        }
    )
    with pytest.raises(SemanticIntegrationError, match="multiple stable products"):
        build_bundle(collision, max_prompt_bytes=12_000)


def test_method_v4_mixed_product_thread_keeps_leaf_product_roles() -> None:
    source = _source_v3(count=1)
    source["semantic_method_version"] = METHOD_VERSION_V4
    source["corpus_profile"] = "phase_a_final_acquisition"
    source["containers"][0]["captured_leaf_count"] = 3
    body = source["captured_items"][0]
    body["evidence_id"] = "reddit:t1:body"
    body["text"] = "Which Summer Fridays products are worth buying?"
    body["product_candidates"] = []
    comment = deepcopy(body)
    comment["evidence_id"] = "reddit:t1:comment"
    comment["source_ref"] = "https://reddit.test/t1/comment"
    comment["text"] = "Lip Butter Balm feels better, but Jet Lag Mask broke me out."
    comment["conversation_depth"] = 1
    comment["parent_context"] = [
        {"source_ref": body["source_ref"], "text": body["text"]}
    ]
    reply = deepcopy(comment)
    reply["evidence_id"] = "reddit:t1:reply"
    reply["source_ref"] = "https://reddit.test/t1/reply"
    reply["text"] = "Same, the mask broke me out too."
    reply["conversation_depth"] = 2
    reply["parent_context"] = [
        {"source_ref": body["source_ref"], "text": body["text"]},
        {"source_ref": comment["source_ref"], "text": comment["text"]},
    ]
    source["captured_items"] = [body, comment, reply]
    catalog = _product_catalog()
    catalog["products"].insert(
        0,
        {
            "stable_product_id": "summer-fridays-jet-lag-mask",
            "display_name": "Summer Fridays Jet Lag Mask",
            "source_product_ids": ["jet-lag-mask"],
            "aliases": ["Jet Lag Mask"],
            "authority_artifact_ids": ["thread-1"],
        },
    )
    catalog["catalog_sha256"] = _canonical_hash(
        {key: value for key, value in catalog.items() if key != "catalog_sha256"}
    )
    source["product_identity_catalog"] = catalog

    bundle = build_bundle(source, max_prompt_bytes=20_000)
    prompt = build_batch_prompts(bundle)[0]["prompt"]
    assert prompt.count("\n\nPRODUCT_IDENTITY_CATALOG\n") == 1
    assert all(row["product_candidates"] == [] for row in bundle["evidence_units"])

    response = {
        "schema_version": BATCH_RESPONSE_VERSION_V2,
        "bundle_sha256": bundle["bundle_sha256"],
        "batch_id": bundle["batches"][0]["batch_id"],
        "evidence": [
            {
                "evidence_id": "reddit:t1:body",
                "disposition": "context_only",
                "disposition_reason": "brand-level question without a product experience",
                "semantic_units": [],
            },
            {
                "evidence_id": "reddit:t1:comment",
                "disposition": "claim_bearing",
                "disposition_reason": "two distinct product experiences",
                "semantic_units": [
                    {
                        "semantic_unit_key": "balm-comfort",
                        "statement": "Lip Butter Balm felt comparatively comfortable.",
                        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
                        "comparator_product_ids": [],
                        "product_version_ids": [],
                        "axis_ids": ["wear"],
                        "emerging_axis_labels": [],
                        "conditions": [],
                        "polarity": "affirmed",
                        "evidence_posture": "first_hand",
                        "uncertainty_posture": "asserted",
                    },
                    {
                        "semantic_unit_key": "mask-reaction",
                        "statement": "Jet Lag Mask was associated with a breakout.",
                        "subject_product_ids": ["summer-fridays-jet-lag-mask"],
                        "comparator_product_ids": [],
                        "product_version_ids": [],
                        "axis_ids": [],
                        "emerging_axis_labels": ["skin reaction"],
                        "conditions": [],
                        "polarity": "affirmed",
                        "evidence_posture": "first_hand",
                        "uncertainty_posture": "asserted",
                    },
                ],
            },
            {
                "evidence_id": "reddit:t1:reply",
                "disposition": "claim_bearing",
                "disposition_reason": "personal agreement about the mask",
                "semantic_units": [
                    {
                        "semantic_unit_key": "mask-agreement",
                        "statement": "The reply author also associated the mask with a breakout.",
                        "subject_product_ids": ["summer-fridays-jet-lag-mask"],
                        "comparator_product_ids": [],
                        "product_version_ids": [],
                        "axis_ids": [],
                        "emerging_axis_labels": ["skin reaction"],
                        "conditions": [],
                        "polarity": "affirmed",
                        "evidence_posture": "personal_agreement",
                        "uncertainty_posture": "asserted",
                    }
                ],
            },
        ],
    }
    compiled = validate_batch_responses(bundle, [response])
    assert {
        tuple(row["subject_product_ids"]) for row in compiled["semantic_units"]
    } == {
        ("summer-fridays-lip-butter-balm",),
        ("summer-fridays-jet-lag-mask",),
    }

    forged = deepcopy(response)
    forged["evidence"][1]["semantic_units"][0]["subject_product_ids"] = [
        "summer-fridays-invented-product"
    ]
    with pytest.raises(SemanticIntegrationError, match="unknown catalog product"):
        validate_batch_responses(bundle, [forged])

    invented_variant = deepcopy(response)
    invented_variant["evidence"][1]["semantic_units"][0][
        "product_version_ids"
    ] = ["summer-fridays-lip-butter-balm-brown-sugar"]
    with pytest.raises(
        SemanticIntegrationError, match="unverified catalog product version"
    ):
        validate_batch_responses(bundle, [invented_variant])


def test_v4_prepare_runner_writes_deterministic_three_worker_assignment(
    tmp_path: Path,
) -> None:
    source = _source_v3()
    for index in range(1, 8):
        (tmp_path / f"thread-{index}.json").write_bytes(
            f"thread-{index}\n".encode()
        )
    source_path = tmp_path / "source-v3.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    result = prepare_batches(
        source_path=source_path,
        repo_root=tmp_path,
        bundle_out=tmp_path / "bundle-v4.json",
        prompt_dir=tmp_path / "prompts-v4",
        max_batch_chars=20_000,
        max_prompt_bytes=20_000,
        max_evidence_per_work_unit=2,
    )
    assignment = json.loads(
        (tmp_path / "prompts-v4" / "worker_assignments.json").read_text(
            encoding="utf-8"
        )
    )

    bundle = json.loads(
        (tmp_path / "bundle-v4.json").read_text(encoding="utf-8")
    )

    assert result["batch_count"] == 4
    assert assignment["worker_count"] == 3
    assert (
        assignment["worker_count"]
        == bundle["semantic_work_unit_projection"]["worker_count"]
    )
    assert [row["worker_partition"] for row in assignment["assignments"]] == [
        1,
        2,
        3,
        1,
    ]


def test_v4_publish_validates_sibling_temp_and_refuses_existing_target(
    tmp_path: Path,
) -> None:
    bundle = build_bundle(_source_v3(count=1), max_prompt_bytes=8_000)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    response_dir = tmp_path / "responses"
    response_dir.mkdir()
    staged = response_dir / "batch-0001.json.tmp"
    staged.write_text(
        json.dumps(_v3_batch_responses(bundle)[0]), encoding="utf-8"
    )

    result = publish_batch_response_file(
        bundle_path=bundle_path,
        staged_response_path=staged,
        response_dir=response_dir,
    )

    target = response_dir / "batch-0001.json"
    assert result["status"] == "SEMANTIC_BATCH_RESPONSE_PUBLISHED"
    assert target.is_file()
    assert not staged.exists()

    staged.write_text(
        json.dumps(_v3_batch_responses(bundle)[0]), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="refusing to overwrite"):
        publish_batch_response_file(
            bundle_path=bundle_path,
            staged_response_path=staged,
            response_dir=response_dir,
        )
    assert staged.is_file()


def test_v4_publish_fails_closed_when_no_replace_link_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = build_bundle(_source_v3(count=1), max_prompt_bytes=8_000)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    response_dir = tmp_path / "responses"
    response_dir.mkdir()
    staged = response_dir / "batch-0001.json.tmp"
    staged.write_text(
        json.dumps(_v3_batch_responses(bundle)[0]), encoding="utf-8"
    )

    def unavailable(_source: Path, _target: Path) -> None:
        raise OSError("hard links unavailable")

    monkeypatch.setattr(os, "link", unavailable)

    with pytest.raises(ValueError, match="atomic no-replace"):
        publish_batch_response_file(
            bundle_path=bundle_path,
            staged_response_path=staged,
            response_dir=response_dir,
        )

    assert staged.is_file()
    assert not (response_dir / "batch-0001.json").exists()


def test_v4_stores_accounting_by_reference_and_renders_shared_context_once() -> None:
    source = _source_v3(count=1)
    source["containers"][0]["captured_leaf_count"] = 2
    second = deepcopy(source["captured_items"][0])
    second["evidence_id"] = "reddit:t1:reply"
    second["source_ref"] = "https://reddit.test/t1/reply"
    second["conversation_depth"] = 1
    second["parent_context"] = [
        {
            "source_ref": "https://reddit.test/t1",
            "text": "The balm became drying after a week of use.",
        }
    ]
    source["captured_items"].append(second)

    bundle = build_bundle(source, max_prompt_bytes=20_000)
    prompts = build_batch_prompts(bundle)

    assert bundle["schema_version"] == BUNDLE_VERSION_V4
    assert all("text" not in row for row in bundle["corpus_accounting"])
    assert {
        row["evidence_unit_ref"] for row in bundle["corpus_accounting"]
    } == {"reddit:t1:comment", "reddit:t1:reply"}
    assert len(prompts) == 1
    assert prompts[0]["prompt"].count("Summer Fridays Lip Butter Balm wear") == 1
    assert prompts[0]["prompt"].count("The balm became drying after a week of use.") == 3


def test_v4_reconciliation_prompt_omits_expanded_lineage_but_stage_keeps_it() -> None:
    bundle = build_bundle(_source_v3(), max_prompt_bytes=8_000)
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage_one, _ = prepare_reconciliation_stage(bundle, compiled)
    nodes_one = validate_reconciliation_stage(
        bundle, stage_one, _group_level_responses(stage_one, terminal=False)
    )

    stage_two, prompts = prepare_reconciliation_stage(bundle, nodes_one)

    assert stage_two["candidates"][0]["leaf_relations"]
    assert stage_two["candidates"][0]["condition_lineage"]
    assert all('"leaf_relations"' not in row["prompt"] for row in prompts)
    assert all('"condition_lineage"' not in row["prompt"] for row in prompts)


def test_v4_projection_rejects_rehashed_coverage_and_context_forgery() -> None:
    bundle = build_bundle(_source_v3(count=2), max_prompt_bytes=8_000)
    forged = deepcopy(bundle)
    projection = forged["semantic_work_unit_projection"]
    projection["work_units"][0]["evidence_ids"].pop()
    projection["projection_sha256"] = _canonical_hash(
        {key: value for key, value in projection.items() if key != "projection_sha256"}
    )
    forged["bundle_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="batch register|coverage"):
        validate_batch_responses(forged, [], require_all=False)

    forged = deepcopy(bundle)
    projection = forged["semantic_work_unit_projection"]
    projection["context_registry"][0]["context_type"] = "parent_text"
    projection["projection_sha256"] = _canonical_hash(
        {key: value for key, value in projection.items() if key != "projection_sha256"}
    )
    forged["bundle_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="misbound context refs"):
        validate_batch_responses(forged, [], require_all=False)


def test_v4_projection_rejects_dangling_or_misplaced_accounting_reference() -> None:
    bundle = build_bundle(_source_v3(count=2), max_prompt_bytes=8_000)

    forged = deepcopy(bundle)
    row = next(
        item
        for item in forged["corpus_accounting"]
        if item["accounting_disposition"] == "assess"
    )
    row["evidence_unit_ref"] = "reddit:t9:does-not-exist"
    forged["bundle_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="cites unknown evidence unit"):
        build_batch_prompts(forged)
    with pytest.raises(SemanticIntegrationError, match="cites unknown evidence unit"):
        validate_batch_responses(forged, [], require_all=False)

    duplicated = deepcopy(bundle)
    rows = [
        item
        for item in duplicated["corpus_accounting"]
        if item["accounting_disposition"] == "assess"
    ]
    rows[1]["evidence_unit_ref"] = rows[0]["evidence_unit_ref"]
    duplicated["bundle_sha256"] = _canonical_hash(
        {key: value for key, value in duplicated.items() if key != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="not a bijection over admitted"):
        validate_batch_responses(duplicated, [], require_all=False)


def test_v4_accounting_keeps_nonassessable_text_for_inspection() -> None:
    source = _source_v3(count=1)
    source["containers"][0]["captured_leaf_count"] = 2
    blocked = deepcopy(source["captured_items"][0])
    blocked["evidence_id"] = "reddit:t1:blocked"
    blocked["source_ref"] = "https://reddit.test/t1/blocked"
    blocked["accounting_disposition"] = "blocked"
    blocked["accounting_reason"] = "truncated body cannot be safely assessed"
    blocked["text"] = "partial body kept visible for inspection"
    source["captured_items"].append(blocked)

    bundle = build_bundle(source, max_prompt_bytes=20_000)
    accounted = {row["evidence_id"]: row for row in bundle["corpus_accounting"]}
    rematerialized = {
        row["evidence_id"]: row
        for row in materialize_source_v3(source)["captured_items"]
    }

    assert bundle["schema_version"] == BUNDLE_VERSION_V4
    assert accounted["reddit:t1:blocked"]["text"] == (
        "partial body kept visible for inspection"
    )
    assert "evidence_unit_ref" not in accounted["reddit:t1:blocked"]
    assert "text" not in accounted["reddit:t1:comment"]
    assert rematerialized["reddit:t1:blocked"]["text"] == (
        "partial body kept visible for inspection"
    )


def test_v4_prompts_render_sources_that_omit_optional_v3_fields() -> None:
    for field, rendered in (
        ("product_candidates", '"product_candidates": []'),
        ("axis_candidates", '"axis_candidates": []'),
        ("conversation_depth", '"conversation_depth": 0'),
    ):
        source = _source_v3(count=1)
        source["captured_items"][0].pop(field)

        bundle = build_bundle(source, max_prompt_bytes=20_000)
        prompts = build_batch_prompts(bundle)

        assert bundle["schema_version"] == BUNDLE_VERSION_V4
        assert len(prompts) == 1
        assert rendered in prompts[0]["prompt"]


def test_v4_materialization_shares_one_context_index_across_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from judgment import semantic_evidence_integration as integration

    original = integration._context_index
    calls: list[str] = []

    def counted(bundle: dict) -> dict:
        calls.append(bundle["bundle_sha256"])
        return original(bundle)

    monkeypatch.setattr(integration, "_context_index", counted)
    source = _source_v3(count=6)

    materialize_source_v3(source)

    # One shared index for the whole corpus, never one rebuild per leaf.
    assert len(calls) == 1


def test_v4_exact_public_handle_match_across_scoped_origins_gets_one_credit() -> None:
    source = _source_v3(count=2)
    source["captured_items"][0]["independence_key"] = "reddit:same-handle"
    source["captured_items"][1]["independence_key"] = "retailer:same-handle"
    for row in source["captured_items"]:
        row["public_identity_key"] = "public_handle:same-handle"
    bundle = build_bundle(source, max_prompt_bytes=8_000)
    assert sorted(
        row["independence_posture"] for row in bundle["evidence_units"]
    ) == ["credited", "possible_same_actor"]
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage_one, _ = prepare_reconciliation_stage(bundle, compiled)
    nodes_one = validate_reconciliation_stage(
        bundle, stage_one, _group_level_responses(stage_one, terminal=False)
    )
    stage_two, _ = prepare_reconciliation_stage(bundle, nodes_one)
    terminal = validate_reconciliation_stage(
        bundle, stage_two, _group_level_responses(stage_two, terminal=True)
    )

    view = finalize_v3_view(bundle, compiled, terminal)

    assert view["propositions"][0]["claim_support"]["independent_origin_count"] == 1


def test_personal_agreement_support_never_adds_independent_origin_credit() -> None:
    source = _source_v7(count=2)
    source["captured_items"][1]["conversation_depth"] = 1
    source["captured_items"][1]["parent_context"] = [
        {
            "source_ref": "https://reddit.test/t2",
            "text": "The parent reported the balm becoming drying after one week.",
        }
    ]
    bundle = build_bundle(source, max_prompt_bytes=20_000)
    responses = _v5_responses(bundle, detailed_per_batch=2)
    responses[0]["evidence"][1]["semantic_units"][0]["evidence_posture"] = (
        "personal_agreement"
    )
    compiled = validate_batch_responses(bundle, responses)
    verification_stage, _ = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    verified = apply_row_verification(
        bundle,
        compiled,
        verification_stage,
        _row_verification_responses(verification_stage),
    )
    stage, prompts = prepare_reconciliation_stage(bundle, verified)
    assert all("never describe it as first-hand" in row["prompt"] for row in prompts)
    assert all(
        "posture-neutral bounded wording" in " ".join(row["prompt"].split())
        for row in prompts
    )
    terminal = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=True)
    )

    view = finalize_v3_view(bundle, verified, terminal)

    support = view["propositions"][0]["claim_support"]
    assert len(support["evidence_refs"]) == 2
    assert support["independent_origin_count"] == 1
    assert support["support_posture"] == "isolated"


def _agreement_bundle_and_units() -> tuple[dict, dict]:
    """One method-v7 verified compilation with one first-hand and one agreement unit."""
    source = _source_v7(count=2)
    source["captured_items"][1]["conversation_depth"] = 1
    source["captured_items"][1]["parent_context"] = [
        {
            "source_ref": "https://reddit.test/t2",
            "text": "The parent reported the balm becoming drying after one week.",
        }
    ]
    bundle = build_bundle(source, max_prompt_bytes=20_000)
    responses = _v5_responses(bundle, detailed_per_batch=2)
    responses[0]["evidence"][1]["semantic_units"][0]["evidence_posture"] = (
        "personal_agreement"
    )
    compiled = validate_batch_responses(bundle, responses)
    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, compiled, stage, _row_verification_responses(stage)
    )
    return bundle, verified


def test_personal_agreement_adds_no_origin_through_flat_finalization() -> None:
    # The flat v1 route is a second live terminal finalization consumer for a
    # method-v7 compilation, so agreement must not become a second independent
    # customer there either.
    bundle, verified = _agreement_bundle_and_units()
    units = verified["semantic_units"]
    assert {row["evidence_posture"] for row in units} == {
        "first_hand",
        "personal_agreement",
    }
    merged = _flat_reconciliation(bundle, verified)
    merged["propositions"] = [
        {
            **merged["propositions"][0],
            "relations": [
                {"semantic_unit_ref": row["semantic_unit_ref"], "relation": "support"}
                for row in units
            ],
        }
    ]

    support = finalize_view(bundle, verified, merged)["propositions"][0][
        "claim_support"
    ]

    assert len(support["evidence_refs"]) == 2
    assert support["independent_origin_count"] == 1
    assert support["support_posture"] == "isolated"


def test_method_v7_flat_finalization_uses_credited_public_origins() -> None:
    # The flat finalizer must apply the same conservative actor-credit rule as
    # the hierarchical finalizer: a public identity seen through two scoped
    # origins is one credited origin, not two customers.
    source = _source_v7(count=2)
    source["captured_items"][0]["independence_key"] = "reddit:same-handle"
    source["captured_items"][1]["independence_key"] = "retailer:same-handle"
    for row in source["captured_items"]:
        row["public_identity_key"] = "public_handle:same-handle"
    bundle = build_bundle(source, max_prompt_bytes=20_000)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, compiled, stage, _row_verification_responses(stage)
    )
    units = verified["semantic_units"]
    merged = _flat_reconciliation(bundle, verified)
    merged["propositions"] = [
        {
            **merged["propositions"][0],
            "relations": [
                {"semantic_unit_ref": row["semantic_unit_ref"], "relation": "support"}
                for row in units
            ],
        }
    ]

    support = finalize_view(bundle, verified, merged)["propositions"][0][
        "claim_support"
    ]

    assert support["independent_origin_count"] == 1
    assert support["support_posture"] == "isolated"


@pytest.mark.parametrize("method", [semantic_module.METHOD_VERSION_V11, semantic_module.METHOD_VERSION_V12])
def test_current_reconciliation_preserves_literal_conditions_and_bounded_scope(method) -> None:
    source = _source_v10(count=1)
    source["semantic_method_version"] = method
    bundle = build_bundle(source, max_prompt_bytes=30_000)
    responses = _keyed_responses(bundle)
    evidence_id = bundle["batches"][0]["evidence_ids"][0]
    decision = _claim_row(evidence_id)
    decision.pop("evidence_id")
    decision["semantic_units"][0]["subject_product_ids"] = ["summer-fridays-lip-butter-balm"]
    decision["semantic_units"][0]["conditions"] = ["Winter and overnight use."]
    responses[0]["decisions_by_evidence_id"][evidence_id] = decision
    primary = validate_batch_responses(bundle, responses)
    verification_stage, _ = prepare_row_verification(bundle, primary)
    verified = apply_row_verification(bundle, primary, verification_stage, _row_verification_responses(verification_stage))
    stage, prompts = prepare_reconciliation_stage(bundle, verified, reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2)
    policy = prompts[0]["prompt"].split("\n\nCANDIDATES\n", 1)[0]
    current = method == semantic_module.METHOD_VERSION_V12
    assert ("response_schema" in prompts[0]) is current
    assert "Copy every child condition verbatim" not in policy
    assert ("unnamed item does not establish a range-wide claim" in policy) is current
    assert ("Purchase intent, acquisition, use, and repurchase are different states" in policy) is current
    assert ("generic approval does not establish a particular benefit" in policy) is current
    assert ("use each semantic_node_key at most once" in policy) is current
    assert ("never attach the same key as both support and counter" in policy) is current
    assert ("TERMINAL_SOURCE_ROLE_COMPETENCE" in policy) is current
    assert ("counter leaves under a counter child both count" in policy) is current
    assert ('"source_roles_by_relation"' in prompts[0]["prompt"]) is current
    if current:
        # The prompt states the composition rule instead of asking the model to
        # rederive it, so keep that sentence pinned to _relation_product itself.
        assert all(
            (semantic_module._relation_product(child, leaf) == "support")
            is (child == leaf and "adjacent" not in {child, leaf})
            for child in semantic_module.RELATIONS
            for leaf in semantic_module.RELATIONS
        )
        agent_rows = json.loads(prompts[0]["prompt"].split("\n\nCANDIDATES\n", 1)[1])
        assert agent_rows[0]["source_roles_by_relation"] == {
            "support": ["community_post"], "counter": [], "adjacent": []}
        assert "community_post" not in semantic_module._competent_roles("observable_fact")
        competence = json.loads(policy.split("\nTERMINAL_SOURCE_ROLE_COMPETENCE\n", 1)[1].split("\n", 1)[0])
        assert competence == {kind: sorted(semantic_module._competent_roles(kind)) for kind in semantic_module.CLAIM_KINDS}
    assert prompts[0]["prompt_utf8_bytes"] == len(prompts[0]["prompt"].encode("utf-8"))
    assert prompts[0]["prompt_utf8_bytes"] <= bundle["max_prompt_bytes"]
    assert prepare_reconciliation_stage(bundle, verified, reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2) == (stage, prompts)
    correct = _group_level_responses(stage, terminal=True)
    for field in ("subject_product_ids", "comparator_product_ids", "product_version_ids", "axis_ids", "conditions"):
        correct[0]["semantic_nodes"][0][field] = list(stage["candidates"][0][field])
    nodes = validate_reconciliation_stage(bundle, stage, correct)
    if current:
        schema = prompts[0]["response_schema"]
        assert schema["properties"]["decisions_by_candidate_ref"]["required"] == stage["batches"][0]["candidate_refs"]
        node_items = schema["properties"]["semantic_nodes"]["items"]
        by_terminal = {
            choice["properties"]["terminal_proposition"]["const"]: choice
            for choice in node_items["anyOf"]
        }
        assert by_terminal[False]["properties"]["opposition_checked"] == {
            "type": ["boolean", "null"]
        }
        assert by_terminal[True]["properties"]["opposition_checked"] == {
            "type": "boolean"
        }
        assert all(
            "child_relations" not in choice["properties"]
            for choice in node_items.get("anyOf", [node_items])
        )
        assert schema["properties"]["emerging_axis_consolidations"]["maxItems"] == 0
    _, next_prompts = prepare_reconciliation_stage(bundle, nodes)
    assert all("Copy every child condition verbatim" not in row["prompt"] for row in next_prompts)
    assert all(('"source_roles_by_relation"' in row["prompt"]) is current for row in next_prompts)
    changed = deepcopy(correct)
    changed[0]["semantic_nodes"][0]["conditions"] = ["For one author, winter and overnight use."]
    with pytest.raises(SemanticIntegrationError, match="drops a child condition"):
        validate_reconciliation_stage(bundle, stage, changed)
    wrong_kind = deepcopy(correct)
    wrong_kind[0]["semantic_nodes"][0]["claim_kind"] = "observable_fact"
    with pytest.raises(SemanticIntegrationError, match="source roles incompetent for observable_fact"):
        validate_reconciliation_stage(bundle, stage, wrong_kind)


def test_current_reconciliation_schema_is_persisted_at_public_prepare(tmp_path: Path) -> None:
    from runners.run_semantic_evidence_integration import prepare_reconciliation_level

    source = _source_v10(count=1)
    source["semantic_method_version"] = semantic_module.METHOD_VERSION_V12
    bundle = build_bundle(source, max_prompt_bytes=30_000)
    responses = _keyed_responses(bundle)
    evidence_id = bundle["batches"][0]["evidence_ids"][0]
    row = _claim_row(evidence_id)
    row.pop("evidence_id")
    row["semantic_units"][0]["subject_product_ids"] = ["summer-fridays-lip-butter-balm"]
    row["semantic_units"][0]["emerging_axis_labels"] = ["texture_detail"]
    responses[0]["decisions_by_evidence_id"][evidence_id] = row
    raw = validate_batch_responses(bundle, responses)
    verification, _ = prepare_row_verification(bundle, raw)
    verified = apply_row_verification(bundle, raw, verification, _row_verification_responses(verification))
    stage, prompts = prepare_reconciliation_stage(bundle, verified,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)
    bp, cp = tmp_path / "bundle.json", tmp_path / "compiled.json"
    bp.write_text(json.dumps(bundle), encoding="utf-8")
    cp.write_text(json.dumps(verified), encoding="utf-8")
    prepare_reconciliation_level(bundle_path=bp, compilation_path=cp,
        stage_out=tmp_path / "stage.json", prompt_dir=tmp_path / "prompts")
    assert json.loads((tmp_path / "stage.json").read_text()) == stage
    for prompt in prompts:
        path = tmp_path / "prompts" / prompt["batch_id"]
        assert path.with_suffix(".md").read_bytes() == (prompt["prompt"] + "\n").encode("utf-8")
        assert json.loads(path.with_suffix(".schema.json").read_text()) == prompt["response_schema"]
    labels = prompts[0]["response_schema"]["properties"]["assignments_by_original_label"]
    assert labels["required"] == ["texture_detail"]
    # Correct outer hashes: omissions must reach the existing coverage boundary.
    response = _singleton_reconciliation_responses(stage)
    with pytest.raises(SemanticIntegrationError, match="does not account for every emerging label"):
        validate_reconciliation_stage(bundle, stage, response)
    response[0]["emerging_axis_consolidations"] = [{"candidate_key": "texture", "canonical_label": "texture detail",
        "original_labels": ["texture_detail"], "disposition": "accepted", "reason": "Distinct source detail."}]
    validate_reconciliation_stage(bundle, stage, response)
    response[0]["semantic_nodes"][0]["child_relations"][0]["child_ref"] = "foreign::meaning"
    with pytest.raises(SemanticIntegrationError, match="unknown, duplicate, or invalid child"):
        validate_reconciliation_stage(bundle, stage, response)


def _decision_reconciliation_fixture(count=2):
    source = _source_v10(count=count)
    source["semantic_method_version"] = semantic_module.METHOD_VERSION_V12
    bundle = build_bundle(source, max_prompt_bytes=30_000)
    responses = _keyed_responses(bundle)
    n = 0
    for response in responses:
        for eid in response["decisions_by_evidence_id"]:
            row = _claim_row(eid)
            row.pop("evidence_id")
            unit = row["semantic_units"][0]
            unit["subject_product_ids"] = ["summer-fridays-lip-butter-balm"]
            unit["conditions"] = ["when it warms up"] if n == 0 else []
            unit["polarity"] = "affirmed" if n == 0 else "negated"
            unit["emerging_axis_labels"] = ["price transparency", "formula interest"]
            response["decisions_by_evidence_id"][eid] = row
            n += 1
    compiled = validate_batch_responses(bundle, responses)
    verification, _ = prepare_row_verification(bundle, compiled)
    verified = apply_row_verification(bundle, compiled, verification, _row_verification_responses(verification))
    stage, prompts = prepare_reconciliation_stage(bundle, verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2)
    old = _singleton_reconciliation_responses(stage)[0]
    node = old["semantic_nodes"][0]
    source_fields = {"subject_product_ids", "comparator_product_ids", "product_version_ids",
        "conditions", "polarity", "emerging_axis_labels", "child_relations"}
    response = {
        "schema_version": semantic_module.RECONCILIATION_RESPONSE_VERSION_V3,
        "stage_sha256": stage["stage_sha256"], "batch_id": stage["batches"][0]["batch_id"],
        "semantic_nodes": [{k: v for k, v in node.items() if k not in source_fields}],
        "decisions_by_candidate_ref": {ref: {"attachments": [{
            "semantic_node_key": node["semantic_node_key"], "relation": "adjacent" if i == 0 else "support"}],
            "unmerged_reason": None} for i, ref in enumerate(stage["batches"][0]["candidate_refs"])},
        "emerging_axis_consolidations": [{"candidate_key": "group", "canonical_label": "bounded label group",
            "disposition": "accepted", "reason": "Test grouping; semantic warrant not mechanically proven."}],
        "assignments_by_original_label": {label: "group" for label in ["price transparency", "formula interest"]},
    }
    return bundle, verified, stage, prompts, response


def test_decision_reconciliation_public_consumers_preserve_owned_facts_and_resume(tmp_path):
    from runners.run_semantic_evidence_integration import prepare_reconciliation_level, submit_reconciliation_level
    bundle, verified, stage, prompts, response = _decision_reconciliation_fixture()
    bp, cp, sp, rp = [tmp_path / name for name in ("bundle.json", "compiled.json", "stage.json", "response.json")]
    for path, value in [(bp, bundle), (cp, verified), (sp, stage), (rp, response)]:
        path.write_text(json.dumps(value), encoding="utf-8")
    prepare_reconciliation_level(bundle_path=bp, compilation_path=cp, existing_stage_path=sp,
        stage_out=tmp_path / "resumed.json", prompt_dir=tmp_path / "prompts",
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_LEGACY)
    assert json.loads((tmp_path / "resumed.json").read_text()) == stage
    schema = json.loads((tmp_path / "prompts" / (response["batch_id"] + ".schema.json")).read_text())
    assert schema == prompts[0]["response_schema"]
    assert schema["properties"]["schema_version"]["const"] == semantic_module.RECONCILIATION_RESPONSE_VERSION_V3
    for slot in schema["properties"]["decisions_by_candidate_ref"]["properties"].values():
        slot = schema["$defs"][slot["$ref"].rsplit("/", 1)[1]]
        assert slot["properties"]["attachments"]["minItems"] == 1
        assert slot["properties"]["unmerged_reason"] == {"type": "null"}
    submit_reconciliation_level(bundle_path=bp, stage_path=sp, response_paths=[rp], compilation_out=tmp_path / "nodes.json")
    result = json.loads((tmp_path / "nodes.json").read_text())
    assert result == validate_reconciliation_stage(bundle, stage, [response])
    assert result == validate_reconciliation_stage(bundle, stage, [deepcopy(response)])
    node = result["semantic_nodes"][0]
    assert node["conditions"] == ["when it warms up"]
    assert node["polarity"] == "mixed"
    assert node["emerging_axis_labels"] == ["formula interest", "price transparency"]
    assert node["subject_product_ids"] == ["summer-fridays-lip-butter-balm"]
    assert node["condition_lineage"] == sorted([lineage for child in stage["candidates"]
        for lineage in child["condition_lineage"]], key=lambda row: row["semantic_unit_ref"])
    assert node["child_relations"] == [{"child_ref": ref, "relation": decision["attachments"][0]["relation"]}
        for ref, decision in response["decisions_by_candidate_ref"].items()]
    # A single candidate may support multiple independently worded nodes.
    extra = deepcopy(response["semantic_nodes"][0]); extra["semantic_node_key"] = "another"
    response["semantic_nodes"].append(extra)
    next(iter(response["decisions_by_candidate_ref"].values()))["attachments"].append(
        {"semantic_node_key": "another", "relation": "support"})
    assert len(validate_reconciliation_stage(bundle, stage, [response])["semantic_nodes"]) == 2


@pytest.mark.parametrize("mutation,error", [
    ("missing_candidate", "candidate decisions has missing or foreign fields"),
    ("foreign_candidate", "candidate decisions has missing or foreign fields"),
    ("missing_label", "label assignments has missing or foreign fields"),
    ("foreign_label", "label assignments has missing or foreign fields"),
    ("duplicate_attachment", "foreign, duplicate or invalid attachment"),
    ("foreign_node", "missing semantic node definitions"),
    ("missing_decision", "requires attachments xor unmerged reason"),
    ("prohibited_unmerged", "cannot unmerge required finding"),
    ("both_destinations", "requires attachments xor unmerged reason"),
    ("foreign_group", "foreign label group assignment"),
    ("duplicate_group", "duplicate or empty label group"),
    ("duplicate_node", "duplicate or empty node key"),
    ("orphan_node", "orphan node"),
    ("unused_group", "unused label group"),
    ("model_owned_copy", "node has missing or foreign fields"),
    ("wrong_identity", "crosses product, comparator, or version bindings"),
])
def test_decision_reconciliation_wrong_cause(mutation, error):
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    decisions = response["decisions_by_candidate_ref"]
    first = next(iter(decisions)); decision = decisions[first]
    if mutation == "missing_candidate": del decisions[first]
    elif mutation == "foreign_candidate": decisions["foreign::unit"] = decisions.pop(first)
    elif mutation == "missing_label": del response["assignments_by_original_label"]["price transparency"]
    elif mutation == "foreign_label": response["assignments_by_original_label"]["foreign"] = "group"
    elif mutation == "duplicate_attachment": decision["attachments"] *= 2
    elif mutation == "foreign_node": decision["attachments"][0]["semantic_node_key"] = "foreign"
    elif mutation == "missing_decision": decision["attachments"] = []
    elif mutation == "prohibited_unmerged": decision.update(attachments=[], unmerged_reason="Only formula interest.")
    elif mutation == "both_destinations": decision["unmerged_reason"] = "Also unmerged."
    elif mutation == "foreign_group": response["assignments_by_original_label"]["price transparency"] = "foreign"
    elif mutation == "duplicate_group": response["emerging_axis_consolidations"] *= 2
    elif mutation == "duplicate_node": response["semantic_nodes"] *= 2
    elif mutation == "orphan_node": response["semantic_nodes"].append({**response["semantic_nodes"][0], "semantic_node_key": "orphan"})
    elif mutation == "unused_group": response["emerging_axis_consolidations"].append({**response["emerging_axis_consolidations"][0], "candidate_key": "unused"})
    elif mutation == "model_owned_copy": response["semantic_nodes"][0]["conditions"] = []
    elif mutation == "wrong_identity":
        stage["candidates"][1]["subject_product_ids"] = ["different-product"]
        stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
        response["stage_sha256"] = stage["stage_sha256"]
    with pytest.raises(SemanticIntegrationError, match=error):
        validate_reconciliation_stage(bundle, stage, [response])


def test_reconciliation_diagnostic_lists_independent_existing_defects_without_accepting():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    decisions = response["decisions_by_candidate_ref"]
    refs = list(decisions)
    main = response["semantic_nodes"][0]

    # Four independent faults coexist in one original response.  The ordinary
    # consumer must still stop at its unchanged first error.
    decisions[refs[0]]["attachments"].append(deepcopy(decisions[refs[0]]["attachments"][0]))
    decisions[refs[1]]["attachments"][0]["semantic_node_key"] = "missing"
    orphan = deepcopy(main)
    orphan["semantic_node_key"] = "orphan"
    counter_only = deepcopy(main)
    counter_only["semantic_node_key"] = "counter-only"
    counter_only.update(
        terminal_proposition=True,
        claim_kind="customer_experience",
        causal_ceiling="causal_not_established",
        opposition_checked=True,
    )
    response["semantic_nodes"].extend([orphan, counter_only])
    decisions[refs[0]]["attachments"].append(
        {"semantic_node_key": "counter-only", "relation": "counter"}
    )

    with pytest.raises(
        SemanticIntegrationError,
        match="decision reconciliation foreign, duplicate or invalid attachment",
    ):
        validate_reconciliation_stage(bundle, stage, [response])

    original = deepcopy(response)
    diagnostic = semantic_module.diagnose_reconciliation_response(bundle, stage, response)
    assert response == original
    assert diagnostic == semantic_module.diagnose_reconciliation_response(
        bundle, stage, deepcopy(response)
    )
    assert diagnostic["valid"] is False and diagnostic["accepted"] is False
    assert diagnostic["primary_validation_error"] == (
        "decision reconciliation foreign, duplicate or invalid attachment"
    )
    assert diagnostic["primary_error_covered"] is True
    codes = {row["code"] for row in diagnostic["issues"]}
    assert {
        "duplicate_or_invalid_attachment",
        "missing_node_definition",
        "orphan_node",
        "terminal_lacks_support",
    } <= codes
    assert diagnostic["semantic_warrant_proven"] is False
    assert diagnostic["model_api_calls"] == 0


def test_reconciliation_diagnostic_keeps_valid_response_clean_and_public_output_write_once(tmp_path):
    from runners.run_semantic_evidence_integration import (
        _load_object,
        _write_json,
        diagnose_reconciliation_response_file,
    )

    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    diagnostic = semantic_module.diagnose_reconciliation_response(bundle, stage, response)
    assert diagnostic["valid"] is True and diagnostic["accepted"] is True
    assert diagnostic["issue_count"] == 0 and diagnostic["issues"] == []
    assert diagnostic["primary_validation_error"] is None
    assert diagnostic["primary_error_covered"] is True

    bundle_path, stage_path, response_path = [
        tmp_path / name for name in ("bundle.json", "stage.json", "response.json")
    ]
    for path, value in (
        (bundle_path, bundle),
        (stage_path, stage),
        (response_path, response),
    ):
        _write_json(path, value)
    output = tmp_path / "diagnostic.json"
    result = diagnose_reconciliation_response_file(
        bundle_path=bundle_path,
        stage_path=stage_path,
        response_path=response_path,
        diagnostic_out=output,
    )
    assert result["status"] == "SEMANTIC_RECONCILIATION_RESPONSE_VALID"
    assert _load_object(output) == diagnostic
    with pytest.raises(ValueError, match="refusing to overwrite"):
        diagnose_reconciliation_response_file(
            bundle_path=bundle_path,
            stage_path=stage_path,
            response_path=response_path,
            diagnostic_out=output,
        )


def test_reconciliation_diagnostic_skips_claim_checks_after_identity_crossing():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    stage["candidates"][1]["subject_product_ids"] = ["different-product"]
    stage["stage_sha256"] = semantic_module._sha256(
        {key: value for key, value in stage.items() if key != "stage_sha256"}
    )
    response["stage_sha256"] = stage["stage_sha256"]
    for decision in response["decisions_by_candidate_ref"].values():
        decision["attachments"][0]["relation"] = "counter"

    diagnostic = semantic_module.diagnose_reconciliation_response(bundle, stage, response)
    codes = {row["code"] for row in diagnostic["issues"]}
    assert "identity_crossing" in codes
    assert "terminal_lacks_support" not in codes
    assert any(
        row["scope"] == "node"
        and "crossed identity" in row["reason"]
        for row in diagnostic["skipped_dependent_checks"]
    )


def test_reconciliation_diagnostic_never_guesses_definition_or_orphan_from_malformed_rows():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    refs = list(response["decisions_by_candidate_ref"])
    attached = deepcopy(response["semantic_nodes"][0])
    attached["semantic_node_key"] = "attached-through-malformed-attachment"
    response["semantic_nodes"].append(attached)
    response["decisions_by_candidate_ref"][refs[1]]["attachments"].append(
        {"semantic_node_key": attached["semantic_node_key"], "relation": "bogus"}
    )
    # A defined-but-malformed node is not an undefined node, and a node whose
    # only attachment is malformed is not an unattached node.
    response["semantic_nodes"][0]["foreign_field"] = 1

    diagnostic = semantic_module.diagnose_reconciliation_response(bundle, stage, response)
    codes = {row["code"] for row in diagnostic["issues"]}
    assert "missing_node_definition" not in codes and "orphan_node" not in codes
    reasons = {row["reason"] for row in diagnostic["skipped_dependent_checks"]}
    assert "exact nonempty node definition is required" in reasons
    assert "malformed attachment cannot enter graph checks" in reasons
    assert (
        "malformed decisions or attachments cannot show whether a node is unattached"
        in reasons
    )
    assert diagnostic["valid"] is False and diagnostic["primary_error_covered"] is False


@pytest.mark.parametrize("field", ["subject_product_ids", "comparator_product_ids", "product_version_ids"])
@pytest.mark.parametrize("relation", sorted(semantic_module.RELATIONS))
def test_normal_identity_namespaces_bind_all_roles_and_relations(field, relation):
    import re
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    stage["candidates"][1][field] = ["different-identity"]
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    record = semantic_module.prepare_reconciliation_prompts(bundle, stage,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)[0]
    schema = record["response_schema"]
    decisions = response["decisions_by_candidate_ref"]
    patterns = []
    for ref in decisions:
        slot = schema["properties"]["decisions_by_candidate_ref"]["properties"][ref]
        shape = schema["$defs"][slot["$ref"].rsplit("/", 1)[1]]
        patterns.append(shape["properties"]["attachments"]["items"]["properties"]["semantic_node_key"]["pattern"])
        decisions[ref]["attachments"][0]["relation"] = relation
    assert patterns[0] != patterns[1]
    # A coherent illegal merge passes no stale-hash guard: fail specifically
    # on identity in native compilation and on the other candidate's pattern.
    key = patterns[0][1:] + "arbitrary_" * 200
    response["semantic_nodes"][0]["semantic_node_key"] = key
    for decision in decisions.values():
        decision["attachments"][0]["semantic_node_key"] = key
    assert re.match(patterns[0], key) and not re.match(patterns[1], key)
    with pytest.raises(SemanticIntegrationError, match="crosses product, comparator, or version bindings"):
        validate_reconciliation_stage(bundle, stage, [response])
    second = deepcopy(response["semantic_nodes"][0])
    second["semantic_node_key"] = patterns[1][1:] + "model_authored"
    response["semantic_nodes"].append(second)
    list(decisions.values())[1]["attachments"][0]["semantic_node_key"] = second["semantic_node_key"]
    assert len(validate_reconciliation_stage(bundle, stage, [response])["semantic_nodes"]) == 2


def test_normal_identity_class_sets_preserve_roles_and_unbounded_key_space():
    rows = [dict(candidate_ref=str(n), subject_product_ids=subject,
                 comparator_product_ids=comparator, product_version_ids=version)
            for n, (subject, comparator, version) in enumerate([
                (["a", "b"], ["c"], []), (["b", "a", "a"], ["c"], []),
                (["c"], ["a", "b"], []), (["a", "b"], [], ["c"]),
                ([], [], []), (["a"], ["b", "c"], [])])]
    prefixes = semantic_module._reconciliation_identity_prefixes(rows)
    assert prefixes["0"] == prefixes["1"]
    assert len(set(prefixes.values())) == 5
    assert prefixes == semantic_module._reconciliation_identity_prefixes(list(reversed(rows)))


def test_public_normal_authoring_default_and_legacy_replay_are_separate(tmp_path):
    from runners.run_semantic_evidence_integration import prepare_reconciliation_level
    bundle, compiled, stage, legacy, _ = _decision_reconciliation_fixture(count=40)
    for name, value in [("bundle", bundle), ("compiled", compiled), ("stage", stage)]:
        (tmp_path / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
    for revision in [None, semantic_module.RECONCILIATION_AUTHORING_LEGACY]:
        directory = tmp_path / (revision or "current")
        result = prepare_reconciliation_level(bundle_path=tmp_path/"bundle.json",
            compilation_path=tmp_path/"compiled.json", existing_stage_path=tmp_path/"stage.json",
            stage_out=directory/"stage.json", prompt_dir=directory/"prompts", authoring_revision=revision)
        expected = semantic_module.prepare_reconciliation_prompts(bundle, stage,
            authoring_revision=revision or semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)
        assert json.loads((directory/"stage.json").read_text()) == stage
        for row in expected:
            assert (directory/"prompts"/f"{row['batch_id']}.md").read_bytes() == (row["prompt"] + "\n").encode()
            assert json.loads((directory/"prompts"/f"{row['batch_id']}.schema.json").read_text()) == row["response_schema"]
        assert result["authoring_revision"] == (revision or semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)
    assert semantic_module.prepare_reconciliation_prompts(bundle, stage,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_LEGACY) == legacy
    new_stage, new_prompts = prepare_reconciliation_stage(bundle, compiled,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)
    assert len(new_prompts) > 1
    assert all(row["prompt_utf8_bytes"] <= bundle["max_prompt_bytes"] for row in new_prompts)
    assert sorted(ref for batch in new_stage["batches"] for ref in batch["candidate_refs"]) == sorted(row["candidate_ref"] for row in new_stage["candidates"])


@pytest.mark.parametrize("revision,version", [("unknown", None),
    (semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1, semantic_module.RECONCILIATION_RESPONSE_VERSION_V2)])
def test_normal_authoring_wrong_revision_fails_before_rendering(revision, version):
    bundle, _, stage, _, _ = _decision_reconciliation_fixture()
    with pytest.raises(SemanticIntegrationError, match="unsupported reconciliation normal-authoring revision"):
        semantic_module.prepare_reconciliation_prompts(bundle, stage,
            authoring_revision=revision, response_version=version)


def test_identity_authoring_preserves_shared_multiple_nodes_and_later_levels():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    record = semantic_module.prepare_reconciliation_prompts(bundle, stage,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)[0]
    assert len(record["response_schema"]["$defs"]) == 1  # shared identity, not per-candidate slots
    response["semantic_nodes"][0]["semantic_node_key"] = "k000_shared"
    extra = deepcopy(response["semantic_nodes"][0])
    extra.update(semantic_node_key="k000_another_unbounded_key", bounded_meaning="A semantically dubious assertion, not mechanically adjudicated.")
    response["semantic_nodes"].append(extra)
    for decision in response["decisions_by_candidate_ref"].values():
        decision["attachments"][0]["semantic_node_key"] = "k000_shared"
        decision["attachments"].append({"semantic_node_key": extra["semantic_node_key"], "relation": "support"})
    nodes = validate_reconciliation_stage(bundle, stage, [response])
    assert len(nodes["semantic_nodes"]) == 2
    next_stage, next_prompts = prepare_reconciliation_stage(bundle, nodes,
        authoring_revision=semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1)
    assert next_stage["level"] == 2
    assert next_stage["reconciliation_mode"] == "convergence"
    assert all(row["authoring_revision"] == semantic_module.RECONCILIATION_AUTHORING_IDENTITY_V1 for row in next_prompts)
    assert all("NORMAL_AUTHORING_REVISION" in row["prompt"] for row in next_prompts)
    # A separately selected historical request remains free of normal-only constraints.
    assert all("NORMAL_AUTHORING_REVISION" not in row["prompt"] for row in
        semantic_module.prepare_reconciliation_prompts(bundle, next_stage))


def test_decision_reconciliation_does_not_infer_semantic_truth():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    response["semantic_nodes"][0]["bounded_meaning"] = "A semantically dubious interpretation remains review-owned."
    result = validate_reconciliation_stage(bundle, stage, [response])
    assert result["semantic_nodes"][0]["bounded_meaning"] == response["semantic_nodes"][0]["bounded_meaning"]
    assert not result["semantic_nodes"][0]["terminal_proposition"]


def _missing_definition_fixture():
    bundle, _, stage, _, original = _decision_reconciliation_fixture()
    # Retain one valid definition: minItems alone cannot close this omission.
    extra = deepcopy(original["semantic_nodes"][0])
    extra["semantic_node_key"] = "preserved"
    original["semantic_nodes"].append(extra)
    next(iter(original["decisions_by_candidate_ref"].values()))["attachments"].append(
        {"semantic_node_key": "preserved", "relation": "adjacent"})
    failed = deepcopy(original)
    missing = failed["semantic_nodes"].pop(0)
    request = semantic_module.prepare_reconciliation_definition_recovery(bundle, stage, failed)
    patch = {key: spec["const"] for key, spec in request["response_schema"]["properties"].items()
             if key != "definitions_by_key"}
    patch["definitions_by_key"] = {missing["semantic_node_key"]: {
        "node": missing, "cannot_define_reason": None}}
    return bundle, stage, original, failed, request, patch


def test_definition_recovery_exact_successor_and_durable_public_consumer(tmp_path):
    from runners.run_semantic_evidence_integration import (
        compose_reconciliation_definitions, prepare_reconciliation_definitions,
        submit_reconciliation_definitions, _write_json, _load_object,
    )
    bundle, stage, original, failed, request, patch = _missing_definition_fixture()
    with pytest.raises(semantic_module.MissingReconciliationDefinitions) as caught:
        validate_reconciliation_stage(bundle, stage, [failed])
    assert set(caught.value.bindings) == set(patch["definitions_by_key"])
    assert len(failed["semantic_nodes"]) == 1
    paths = [tmp_path / name for name in ("bundle.json", "stage.json", "failed.json", "patch.json")]
    for path, obj in zip(paths, (bundle, stage, failed, patch)):
        _write_json(path, obj)
    args = dict(bundle_path=paths[0], stage_path=paths[1], failed_response_path=paths[2])
    result = prepare_reconciliation_definitions(**args, output_dir=tmp_path / "request")
    assert result["missing_definition_count"] == 1 and result["model_api_calls"] == 0
    assert _load_object(tmp_path / "request/request.json")["request"] == request
    node_choices = request["response_schema"]["$defs"]["node"]["anyOf"]
    by_terminal = {
        choice["properties"]["terminal_proposition"]["const"]: choice
        for choice in node_choices
    }
    assert by_terminal[False]["properties"]["opposition_checked"] == {
        "type": ["boolean", "null"]
    }
    assert by_terminal[True]["properties"]["opposition_checked"] == {
        "type": "boolean"
    }
    with pytest.raises(ValueError, match="existing definition-recovery directory"):
        prepare_reconciliation_definitions(**args, output_dir=tmp_path / "request")
    composed = compose_reconciliation_definitions(
        **args,
        request_path=tmp_path / "request/request.json",
        patch_path=paths[3],
        output_dir=tmp_path / "composed",
    )
    assert composed["status"] == "DEFINITIONS_COMPOSED_NOT_ACCEPTED"
    assert composed["accepted"] is False
    expected_intermediate = semantic_module.compose_reconciliation_definition_recovery_intermediate(
        bundle, stage, failed, request, patch
    )
    assert _load_object(tmp_path / "composed/intermediate-response.json") == expected_intermediate
    assert _load_object(tmp_path / "composed/receipt.json")[
        "intermediate_response_sha256"
    ] == composed["intermediate_response_sha256"]
    # The documented operator route must exist on the public runner CLI.
    from runners.run_semantic_evidence_integration import main

    assert main(["compose-reconciliation-definitions",
                 "--bundle", str(paths[0]), "--stage", str(paths[1]),
                 "--failed-response", str(paths[2]),
                 "--request", str(tmp_path / "request/request.json"),
                 "--patch", str(paths[3]),
                 "--output-dir", str(tmp_path / "cli-composed")]) == 0
    assert _load_object(tmp_path / "cli-composed/intermediate-response.json") == expected_intermediate
    assert _load_object(tmp_path / "cli-composed/receipt.json") == _load_object(
        tmp_path / "composed/receipt.json")
    submit_args = dict(**args, request_path=tmp_path / "request/request.json",
                       patch_path=paths[3], output_dir=tmp_path / "successor")
    receipt = submit_reconciliation_definitions(**submit_args)
    durable = _load_object(tmp_path / "successor/response.json")
    assert durable["semantic_nodes"][:1] == failed["semantic_nodes"]
    assert {k: v for k, v in durable.items() if k != "semantic_nodes"} == {
        k: v for k, v in failed.items() if k != "semantic_nodes"}
    assert receipt["validation"] == validate_reconciliation_stage(bundle, stage, [durable], require_all=False)
    assert validate_reconciliation_stage(bundle, stage, [durable]) == validate_reconciliation_stage(bundle, stage, [original])
    assert submit_reconciliation_definitions(**submit_args) == receipt
    assert _load_object(paths[2]) == failed  # Never replace the failed raw answer.
    paths[2].write_bytes(paths[2].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="source file bytes changed"):
        submit_reconciliation_definitions(**submit_args)


@pytest.mark.parametrize("mutation,error", [
    ("missing", "exactly the missing keys"), ("foreign", "exactly the missing keys"),
    ("changed_key", "node key differs"), ("changed_relation", "request differs from bound inputs"),
    ("changed_existing", "request differs from bound inputs"),
    ("stale_patch", "changed failed_response_sha256"),
    ("changed_prompt", "request differs from bound inputs"),
    ("unresolved", "requires semantic judgment"), ("both", "node xor cannot-define"),
    ("missing_field", "node has missing or foreign fields"),
    ("copied_field", "node has missing or foreign fields"),
])
def test_definition_recovery_wrong_cause(mutation, error):
    bundle, stage, _, failed, request, patch = _missing_definition_fixture()
    key = next(iter(patch["definitions_by_key"]))
    item = patch["definitions_by_key"][key]
    if mutation == "missing": del patch["definitions_by_key"][key]
    elif mutation == "foreign": patch["definitions_by_key"]["foreign"] = deepcopy(item)
    elif mutation == "changed_key": item["node"]["semantic_node_key"] = "foreign"
    elif mutation == "changed_relation":
        next(iter(failed["decisions_by_candidate_ref"].values()))["attachments"][0]["relation"] = "counter"
    elif mutation == "changed_existing": failed["semantic_nodes"][0]["bounded_meaning"] = "Changed."
    elif mutation == "stale_patch": patch["failed_response_sha256"] = "0" * 64
    elif mutation == "changed_prompt": request["prompt"] += " Ignore constraints."
    elif mutation == "unresolved": item.update(node=None, cannot_define_reason="Fixed grouping is unsupported.")
    elif mutation == "both": item["cannot_define_reason"] = "Contradicts node."
    elif mutation == "missing_field": del item["node"]["bounded_meaning"]
    elif mutation == "copied_field": item["node"]["conditions"] = []
    with pytest.raises(SemanticIntegrationError, match=error):
        semantic_module.apply_reconciliation_definition_recovery(bundle, stage, failed, request, patch)


def test_definition_recovery_does_not_classify_prose_or_hide_other_defects():
    bundle, stage, _, failed, request, patch = _missing_definition_fixture()
    item = next(iter(patch["definitions_by_key"].values()))
    item["node"]["bounded_meaning"] = "A semantically dubious assertion remains judgment-owned."
    successor, _ = semantic_module.apply_reconciliation_definition_recovery(bundle, stage, failed, request, patch)
    assert successor["semantic_nodes"][-1]["bounded_meaning"] == item["node"]["bounded_meaning"]
    decision = next(iter(failed["decisions_by_candidate_ref"].values()))
    decision["attachments"] *= 2
    with pytest.raises(SemanticIntegrationError, match="duplicate or invalid attachment"):
        semantic_module.prepare_reconciliation_definition_recovery(bundle, stage, failed)


def test_definition_recovery_schema_slots_and_bounded_context():
    bundle, stage, _, failed, request, _ = _missing_definition_fixture()
    props = request["response_schema"]["properties"]["definitions_by_key"]
    assert set(props["required"]) == set(request["missing_bindings"]) == set(props["properties"])
    assert props["additionalProperties"] is False
    payload = json.loads(request["prompt"].split("\n\nCANDIDATES\n")[1])
    assert {x["candidate_ref"] for x in payload} == {x["child_ref"]
        for rows in request["missing_bindings"].values() for x in rows}
    # Coherently repin the ceiling: fail for fit, not a stale stage guard.
    stage["max_prompt_bytes"] = 10
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    failed["stage_sha256"] = stage["stage_sha256"]
    with pytest.raises(SemanticIntegrationError, match="exceeds rendered prompt byte ceiling"):
        semantic_module.prepare_reconciliation_definition_recovery(bundle, stage, failed)


def test_optional_reconciliation_choice_schema_rejects_both_destinations():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    for candidate in stage["candidates"]:
        candidate["evidence_postures"] = ["attribution_or_echo"]
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    schema = semantic_module.prepare_reconciliation_prompts(bundle, stage)[0]["response_schema"]
    alternatives = schema["$defs"]["decision"]["anyOf"]
    assert alternatives[0]["properties"]["attachments"]["minItems"] == 1
    assert alternatives[0]["properties"]["unmerged_reason"] == {"type": "null"}
    assert alternatives[1]["properties"]["attachments"]["maxItems"] == 0
    assert alternatives[1]["properties"]["unmerged_reason"] == {"type": "string", "minLength": 1}
    decision = next(iter(response["decisions_by_candidate_ref"].values()))
    decision["unmerged_reason"] = "Retained context, not terminal proof."
    with pytest.raises(SemanticIntegrationError, match="attachments xor unmerged reason"):
        validate_reconciliation_stage(bundle, stage, [response])


def _local_repair_fixture():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    refs = list(response["decisions_by_candidate_ref"])
    node = response["semantic_nodes"][0]
    node["semantic_node_key"] = "affected"
    response["semantic_nodes"].append({**deepcopy(node), "semantic_node_key": "untouched"})
    for ref, key in zip(refs, ("affected", "untouched"), strict=True):
        response["decisions_by_candidate_ref"][ref] = {"attachments": [{"semantic_node_key": key, "relation": "support"}], "unmerged_reason": None}
    request = semantic_module.prepare_reconciliation_repair(bundle, stage, response,
        node_keys=["affected"], reason="Check this bounded wording against its exact source; no automatic verdict.")
    corrected = {**deepcopy(node), "bounded_meaning": "A bounded source report, not a population estimate.", "opposition_checked": False}
    del corrected["opposition_checked"]
    patch = {"request_sha256": request["request_sha256"], "correction": {"replacement": {
        "semantic_nodes": [corrected], "decisions_by_candidate_ref": {refs[0]: deepcopy(response["decisions_by_candidate_ref"][refs[0]])}},
        "cannot_repair_reason": None}}
    return bundle, stage, response, request, patch


def test_local_repair_table_encoding_preserves_typed_values_and_missing_fields():
    rows = [dict(ref=f"row-{i}", same=["a", None], typed=value, text="not safe; 皮肤")
            for i, value in enumerate([True, 1, 1.0, False, 0, None] * 5)]
    context = {"candidates": rows, "evidence": [], "contexts": [{"a": None}, {}],
               "semantic_nodes": [], "decisions_by_candidate_ref": {"columns": "literal"}}
    original = deepcopy(context)
    packed = semantic_module._pack_reconciliation_repair_context(context)
    table = packed["candidates"]
    assert "typed" in table["columns"] and "typed" not in table["shared_fields"]
    restored = [{**table["shared_fields"], **dict(zip(table["columns"], cells, strict=True))}
                for cells in table["rows"]]
    assert json.dumps(restored, sort_keys=True) == json.dumps(rows, sort_keys=True)
    assert packed["contexts"] == context["contexts"]  # Missing is not null.
    assert packed["decisions_by_candidate_ref"] == context["decisions_by_candidate_ref"]
    assert context == original


def _oversize_local_repair_fixture():
    bundle, stage, response, _, _ = _local_repair_fixture()
    response["semantic_nodes"] = response["semantic_nodes"][:1]
    for decision in response["decisions_by_candidate_ref"].values():
        decision["attachments"] = [{"semantic_node_key": "affected", "relation": "support"}]
    nomination = dict(node_keys=["affected"], reason="Preserve every original source and binding.")
    original = semantic_module.prepare_reconciliation_repair(bundle, stage, response, **nomination)
    stage["max_prompt_bytes"] = original["prompt_utf8_bytes"] - 1
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    return bundle, stage, response, nomination, original


def test_local_repair_oversize_tables_reach_public_consumer_without_changing_scope(tmp_path):
    from runners.run_semantic_evidence_integration import (
        prepare_reconciliation_local_repair, submit_reconciliation_local_repair, _write_json, _load_object)
    bundle, stage, response, nomination, original = _oversize_local_repair_fixture()
    paths = [tmp_path / n for n in ("bundle.json", "stage.json", "response.json", "nomination.json")]
    for p, value in zip(paths, (bundle, stage, response, nomination), strict=True):
        _write_json(p, value)
    args = dict(bundle_path=paths[0], stage_path=paths[1], failed_response_path=paths[2])
    prepare_reconciliation_local_repair(**args, nomination_path=paths[3], output_dir=tmp_path / "request")
    request = _load_object(tmp_path / "request/request.json")["request"]
    assert "PACKED_REPAIR_CONTEXT_V1" in request["prompt"]
    assert "use each semantic_node_key at most once" in request["prompt"]
    assert "never attach the same key as both support and counter" in request["prompt"]
    assert request["prompt_utf8_bytes"] <= stage["max_prompt_bytes"] < original["prompt_utf8_bytes"]
    context = json.loads(original["prompt"].split("\n\nLOCAL_REPAIR_CONTEXT\n")[1])
    packed = json.loads(request["prompt"].split("\n\nLOCAL_REPAIR_CONTEXT\n")[1])
    for key in ("candidates", "evidence", "contexts", "semantic_nodes"):
        table = packed[key]
        if isinstance(table, dict):
            packed[key] = [{**table["shared_fields"], **dict(zip(table["columns"], row, strict=True))}
                           for row in table["rows"]]
    assert json.dumps(packed, sort_keys=True) == json.dumps(context, sort_keys=True)
    patch = dict(request_sha256=request["request_sha256"], correction=dict(cannot_repair_reason=None,
        replacement=dict(decisions_by_candidate_ref=deepcopy(response["decisions_by_candidate_ref"]),
            semantic_nodes=[{k: v for k, v in n.items() if k != "opposition_checked"} for n in response["semantic_nodes"]])))
    _write_json(tmp_path / "patch.json", patch)
    submitted = dict(**args, request_path=tmp_path / "request/request.json", patch_path=tmp_path / "patch.json",
                     output_dir=tmp_path / "successor")
    receipt = submit_reconciliation_local_repair(**submitted)
    assert submit_reconciliation_local_repair(**submitted) == receipt
    assert _load_object(tmp_path / "successor/response.json") == response
    for error, changed in (("authorized candidate scope", deepcopy(patch)), ("crosses replacement scope", deepcopy(patch))):
        decisions = changed["correction"]["replacement"]["decisions_by_candidate_ref"]
        ref = next(iter(decisions))
        if error == "authorized candidate scope":
            del decisions[ref]
        else:
            decisions[ref]["attachments"][0]["semantic_node_key"] = "foreign"
        with pytest.raises(SemanticIntegrationError, match=error):
            semantic_module.apply_reconciliation_repair(bundle, stage, response, request, changed)
    tampered = deepcopy(request)
    tampered["prompt"] += "\nChanged source context."
    identity = {k: v for k, v in tampered.items() if k not in {"request_sha256", "response_schema"}}
    tampered["request_sha256"] = semantic_module._sha256(identity)
    with pytest.raises(SemanticIntegrationError, match="request differs from bound inputs"):
        semantic_module.apply_reconciliation_repair(bundle, stage, response, tampered, patch)


def test_local_repair_public_consumer_is_exact_bounded_and_repeatable(tmp_path):
    from runners.run_semantic_evidence_integration import (
        prepare_reconciliation_local_repair, submit_reconciliation_local_repair, _write_json, _load_object)
    bundle, stage, response, request, patch = _local_repair_fixture()
    paths = [tmp_path / name for name in ("bundle.json", "stage.json", "response.json", "nomination.json", "patch.json")]
    for path, value in zip(paths, (bundle, stage, response, request["nomination"], patch), strict=True):
        _write_json(path, value)
    args = dict(bundle_path=paths[0], stage_path=paths[1], failed_response_path=paths[2])
    prepared = prepare_reconciliation_local_repair(**args, nomination_path=paths[3], output_dir=tmp_path / "request")
    assert prepared["candidate_count"] == 1 and prepared["model_api_calls"] == 0
    assert _load_object(tmp_path / "request/request.json")["request"] == request
    schema = request["response_schema"]
    assert schema["type"] == "object" and "anyOf" not in schema
    assert schema["additionalProperties"] is False
    node_choices = schema["properties"]["correction"]["anyOf"][0]["properties"][
        "replacement"
    ]["properties"]["semantic_nodes"]["items"]["anyOf"]
    by_terminal = {
        choice["properties"]["terminal_proposition"]["const"]: choice
        for choice in node_choices
    }
    assert all(choice["additionalProperties"] is False for choice in node_choices)
    assert by_terminal[False]["properties"]["claim_kind"] == {"type": "null"}
    assert by_terminal[False]["properties"]["causal_ceiling"] == {"type": "null"}
    assert None not in by_terminal[True]["properties"]["claim_kind"]["enum"]
    assert None not in by_terminal[True]["properties"]["causal_ceiling"]["enum"]
    assert len(schema["properties"]["correction"]["anyOf"]) == 2
    submitted = dict(**args, request_path=tmp_path / "request/request.json", patch_path=paths[4], output_dir=tmp_path / "successor")
    receipt = submit_reconciliation_local_repair(**submitted)
    successor = _load_object(tmp_path / "successor/response.json")
    assert successor["semantic_nodes"][1] == response["semantic_nodes"][1]
    assert successor["decisions_by_candidate_ref"] == response["decisions_by_candidate_ref"]
    assert successor["assignments_by_original_label"] == response["assignments_by_original_label"]
    assert successor["semantic_nodes"][0]["opposition_checked"] is False
    assert receipt["validation"] == validate_reconciliation_stage(bundle, stage, [successor], require_all=False)
    assert submit_reconciliation_local_repair(**submitted) == receipt
    assert _load_object(paths[2]) == response
    paths[2].write_bytes(paths[2].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="source file bytes changed"):
        submit_reconciliation_local_repair(**submitted)


def test_local_repair_can_prepare_exact_chained_missing_definitions(tmp_path):
    from runners.run_semantic_evidence_integration import (
        _load_object,
        _write_json,
        compose_reconciliation_local_repair,
        prepare_reconciliation_definitions_after_local_repair,
        prepare_reconciliation_local_repair,
    )

    bundle, stage, response, request, patch = _local_repair_fixture()
    refs = list(response["decisions_by_candidate_ref"])
    response["decisions_by_candidate_ref"][refs[1]]["attachments"].append(
        {"semantic_node_key": "missing", "relation": "support"}
    )
    request = semantic_module.prepare_reconciliation_repair(
        bundle,
        stage,
        response,
        node_keys=["affected"],
        reason="Correct only the nominated component.",
    )
    patch["request_sha256"] = request["request_sha256"]
    patch["correction"]["replacement"]["decisions_by_candidate_ref"] = {
        refs[0]: deepcopy(response["decisions_by_candidate_ref"][refs[0]])
    }
    with pytest.raises(semantic_module.MissingReconciliationDefinitions):
        semantic_module.apply_reconciliation_repair(
            bundle, stage, response, request, patch
        )

    intermediate, definition_request = (
        semantic_module.prepare_reconciliation_definition_recovery_after_repair(
            bundle, stage, response, request, patch
        )
    )
    assert set(definition_request["missing_bindings"]) == {"missing"}
    assert intermediate["semantic_nodes"][1] == response["semantic_nodes"][1]
    assert intermediate["decisions_by_candidate_ref"][refs[1]] == response[
        "decisions_by_candidate_ref"
    ][refs[1]]

    paths = {
        name: tmp_path / f"{name}.json"
        for name in ("bundle", "stage", "response", "nomination", "patch")
    }
    for name, value in (
        ("bundle", bundle),
        ("stage", stage),
        ("response", response),
        ("nomination", request["nomination"]),
        ("patch", patch),
    ):
        _write_json(paths[name], value)
    prepare_reconciliation_local_repair(
        bundle_path=paths["bundle"],
        stage_path=paths["stage"],
        failed_response_path=paths["response"],
        nomination_path=paths["nomination"],
        output_dir=tmp_path / "local-request",
    )
    composed = compose_reconciliation_local_repair(
        bundle_path=paths["bundle"],
        stage_path=paths["stage"],
        failed_response_path=paths["response"],
        repair_request_path=tmp_path / "local-request/request.json",
        repair_patch_path=paths["patch"],
        output_dir=tmp_path / "composed",
    )
    assert composed["accepted"] is False
    assert composed["status"] == "LOCAL_REPAIR_COMPOSED_NOT_ACCEPTED"
    assert _load_object(tmp_path / "composed/intermediate-response.json") == intermediate
    assert _load_object(tmp_path / "composed/receipt.json")[
        "intermediate_response_sha256"
    ] == composed["intermediate_response_sha256"]
    result = prepare_reconciliation_definitions_after_local_repair(
        bundle_path=paths["bundle"],
        stage_path=paths["stage"],
        failed_response_path=paths["response"],
        repair_request_path=tmp_path / "local-request/request.json",
        repair_patch_path=paths["patch"],
        output_dir=tmp_path / "definition-request",
    )
    durable = _load_object(tmp_path / "definition-request/intermediate-response.json")
    durable_request = _load_object(tmp_path / "definition-request/request.json")
    chain_receipt = _load_object(tmp_path / "definition-request/chain-receipt.json")
    assert result["intermediate_accepted"] is False
    assert durable == intermediate
    assert durable_request["request"] == definition_request
    assert durable_request["input_sha256"]["failed_response"] == chain_receipt[
        "intermediate_response_sha256"
    ]
    assert result["chain_receipt"] == chain_receipt
    assert chain_receipt["repair_patch_sha256"]

    # The documented operator route must exist on the public runner CLI.
    from runners.run_semantic_evidence_integration import main

    bound = ["--bundle", str(paths["bundle"]), "--stage", str(paths["stage"]),
             "--failed-response", str(paths["response"]),
             "--request", str(tmp_path / "local-request/request.json"),
             "--patch", str(paths["patch"])]
    assert main(["compose-reconciliation-repair", *bound,
                 "--output-dir", str(tmp_path / "cli-composed")]) == 0
    assert _load_object(tmp_path / "cli-composed/intermediate-response.json") == intermediate
    assert _load_object(tmp_path / "cli-composed/receipt.json") == _load_object(
        tmp_path / "composed/receipt.json")
    assert main(["prepare-reconciliation-definitions-after-repair", *bound,
                 "--output-dir", str(tmp_path / "cli-definition-request")]) == 0
    assert _load_object(tmp_path / "cli-definition-request/request.json") == durable_request
    assert _load_object(tmp_path / "cli-definition-request/chain-receipt.json") == chain_receipt
    # Refuse a second write into the same durable directory through the CLI too.
    assert main(["compose-reconciliation-repair", *bound,
                 "--output-dir", str(tmp_path / "cli-composed")]) == 2


@pytest.mark.parametrize("mutation,error", [
    ("foreign_candidate", "authorized candidate scope"), ("missing_candidate", "authorized candidate scope"),
    ("foreign_node", "foreign or duplicate node"), ("duplicate_node", "foreign or duplicate node"),
    ("foreign_link", "crosses replacement scope"), ("retained_clearance", "model-authored opposition clearance"),
    ("changed_request", "request differs from bound inputs"), ("changed_patch_pin", "changed request identity"),
    ("refusal", "requires semantic judgment"), ("both", "replacement xor cannot-repair"),
    ("unsupported_counter", "lacks support"), ("both_destinations", "attachments xor unmerged reason"),
])
def test_local_repair_wrong_cause(mutation, error):
    bundle, stage, response, request, patch = _local_repair_fixture()
    replacement = patch["correction"]["replacement"]
    decisions = replacement["decisions_by_candidate_ref"]
    ref = next(iter(decisions))
    if mutation == "foreign_candidate": decisions["foreign"] = decisions.pop(ref)
    elif mutation == "missing_candidate": decisions.clear()
    elif mutation == "foreign_node": replacement["semantic_nodes"][0]["semantic_node_key"] = "untouched"
    elif mutation == "duplicate_node": replacement["semantic_nodes"] *= 2
    elif mutation == "foreign_link": decisions[ref]["attachments"][0]["semantic_node_key"] = "untouched"
    elif mutation == "retained_clearance": replacement["semantic_nodes"][0]["opposition_checked"] = True
    elif mutation == "changed_request": request["context_sha256"] = "0" * 64
    elif mutation == "changed_patch_pin": patch["request_sha256"] = "0" * 64
    elif mutation == "refusal": patch["correction"].update(replacement=None, cannot_repair_reason="Cannot establish the allegation.")
    elif mutation == "both": patch["correction"]["cannot_repair_reason"] = "Not sure."
    elif mutation == "unsupported_counter":
        decisions[ref]["attachments"][0]["relation"] = "counter"
        replacement["semantic_nodes"][0].update(terminal_proposition=True, claim_kind="customer_experience", causal_ceiling="descriptive_only")
    elif mutation == "both_destinations": decisions[ref]["unmerged_reason"] = "Also retained."
    with pytest.raises(SemanticIntegrationError, match=error):
        semantic_module.apply_reconciliation_repair(bundle, stage, response, request, patch)


def test_local_repair_connected_scope_context_and_semantic_nonclaim():
    bundle, stage, response, request, patch = _local_repair_fixture()
    context = json.loads(request["prompt"].split("\n\nLOCAL_REPAIR_CONTEXT\n")[1])
    assert len(context["candidates"]) == len(context["evidence"]) == 1
    assert context["source_inventory_not_claim_support"]["evidence_row_count"] == 1
    assert context["evidence"][0]["text"]
    assert "untouched" not in {n["semantic_node_key"] for n in context["semantic_nodes"]}
    ref = next(iter(response["decisions_by_candidate_ref"]))
    response["decisions_by_candidate_ref"][ref]["attachments"].append({"semantic_node_key": "untouched", "relation": "adjacent"})
    connected = semantic_module.prepare_reconciliation_repair(bundle, stage, response, **request["nomination"])
    assert connected["node_keys"] == ["affected", "untouched"] and len(connected["candidate_refs"]) == 2
    # No prose classifier: structural success never certifies this assertion.
    bundle, stage, response, request, patch = _local_repair_fixture()
    patch["correction"]["replacement"]["semantic_nodes"][0]["bounded_meaning"] = "Everyone in the market loves it."
    successor, _ = semantic_module.apply_reconciliation_repair(bundle, stage, response, request, patch)
    assert successor["semantic_nodes"][0]["bounded_meaning"] == "Everyone in the market loves it."
    stage["max_prompt_bytes"] = 1
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    with pytest.raises(SemanticIntegrationError, match="exceeds rendered prompt byte ceiling"):
        semantic_module.prepare_reconciliation_repair(bundle, stage, response, **request["nomination"])


def test_local_repair_missing_node_orphan_and_noop():
    bundle, stage, response, request, patch = _local_repair_fixture()
    del response["semantic_nodes"][0]
    request = semantic_module.prepare_reconciliation_repair(bundle, stage, response, node_keys=["affected"], reason="Missing definition.")
    patch["request_sha256"] = request["request_sha256"]
    successor, _ = semantic_module.apply_reconciliation_repair(bundle, stage, response, request, patch)
    orphan = {**deepcopy(successor["semantic_nodes"][0]), "semantic_node_key": "orphan"}
    successor["semantic_nodes"].append(orphan)
    request = semantic_module.prepare_reconciliation_repair(bundle, stage, successor, node_keys=["orphan"], reason="Unattached heading.")
    patch = {"request_sha256": request["request_sha256"], "correction": {"replacement": {"semantic_nodes": [], "decisions_by_candidate_ref": {}}, "cannot_repair_reason": None}}
    repaired, _ = semantic_module.apply_reconciliation_repair(bundle, stage, successor, request, patch)
    assert repaired["semantic_nodes"] == successor["semantic_nodes"][:-1]
    # A truthy prior clearance separates exact-no-op retention from blanket
    # invalidation; an already-false flag cannot tell those two rules apart.
    next(n for n in repaired["semantic_nodes"] if n["semantic_node_key"] == "affected")["opposition_checked"] = True
    request = semantic_module.prepare_reconciliation_repair(bundle, stage, repaired, node_keys=["affected"], reason="An allegation may be wrong.")
    patch["request_sha256"] = request["request_sha256"]
    patch["correction"]["replacement"] = {"semantic_nodes": [{k:v for k,v in n.items() if k!="opposition_checked"} for n in repaired["semantic_nodes"] if n["semantic_node_key"] == "affected"],
        "decisions_by_candidate_ref": {r: repaired["decisions_by_candidate_ref"][r] for r in request["candidate_refs"]}}
    noop, _ = semantic_module.apply_reconciliation_repair(bundle, stage, repaired, request, patch)
    assert noop == repaired
    assert next(n for n in noop["semantic_nodes"] if n["semantic_node_key"] == "affected")["opposition_checked"] is True
    # Either changed meaning OR changed attachments invalidates true clearance.
    # The relation-only case keeps the node body exact, exposing an ignored link.
    for change in ("meaning", "attachment"):
        changed = deepcopy(patch)
        replacement = changed["correction"]["replacement"]
        if change == "meaning":
            replacement["semantic_nodes"][0]["bounded_meaning"] = "A revised bounded assertion."
        else:
            next(iter(replacement["decisions_by_candidate_ref"].values()))["attachments"][0]["relation"] = "adjacent"
        edited, _ = semantic_module.apply_reconciliation_repair(bundle, stage, repaired, request, changed)
        assert next(n for n in edited["semantic_nodes"] if n["semantic_node_key"] == "affected")["opposition_checked"] is False


def test_local_repair_explicit_duplicate_key_replaces_every_duplicate_and_owner():
    bundle, stage, response, _, patch = _local_repair_fixture()
    duplicate = deepcopy(response["semantic_nodes"][0])
    duplicate["bounded_meaning"] = "A second meaning incorrectly reused the same key."
    response["semantic_nodes"].insert(1, duplicate)
    with pytest.raises(SemanticIntegrationError, match="omits duplicate nodes: affected"):
        semantic_module.prepare_reconciliation_repair(
            bundle,
            stage,
            response,
            node_keys=["untouched"],
            reason="An unrelated issue cannot hide a duplicate key.",
        )
    request = semantic_module.prepare_reconciliation_repair(
        bundle,
        stage,
        response,
        node_keys=["affected"],
        reason="Separate or consolidate the duplicate meanings using their exact sources.",
    )
    context = json.loads(request["prompt"].split("\n\nLOCAL_REPAIR_CONTEXT\n")[1])
    assert [node["semantic_node_key"] for node in context["semantic_nodes"]].count(
        "affected"
    ) == 2
    patch["request_sha256"] = request["request_sha256"]
    successor, _ = semantic_module.apply_reconciliation_repair(
        bundle, stage, response, request, patch
    )
    assert [node["semantic_node_key"] for node in successor["semantic_nodes"]].count(
        "affected"
    ) == 1
    repaired = next(
        node for node in successor["semantic_nodes"] if node["semantic_node_key"] == "affected"
    )
    assert repaired["opposition_checked"] is False


@pytest.mark.parametrize("field", ["subject_product_ids", "comparator_product_ids", "product_version_ids"])
def test_local_repair_requires_all_known_identity_conflicts_before_public_preparation(tmp_path, field):
    from runners.run_semantic_evidence_integration import (
        prepare_reconciliation_local_repair, submit_reconciliation_local_repair, _write_json, _load_object)
    bundle, _, stage, _, response = _decision_reconciliation_fixture(count=5)
    refs = stage["batches"][0]["candidate_refs"]
    assert len(refs) == 5
    index = {c["candidate_ref"]: c for c in stage["candidates"]}
    # Two disjoint violations in already-admitted candidates, plus valid work.
    for ref in (refs[1], refs[3]):
        index[ref][field] = ["summer-fridays-second-balm"] if field == "subject_product_ids" else ["summer-fridays-lip-butter-balm"]
    stage["stage_sha256"] = semantic_module._sha256({k:v for k,v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    template = response["semantic_nodes"][0]
    keys = ["first", "second", "untouched"]
    response["semantic_nodes"] = [{**deepcopy(template), "semantic_node_key": key} for key in keys]
    for ref, key in zip(refs, ("first", "first", "second", "second", "untouched"), strict=True):
        response["decisions_by_candidate_ref"][ref] = {
            "attachments": [{"semantic_node_key": key, "relation": "support"}], "unmerged_reason": None}
    # The original consumer reaches the identity guard, not a stale outer hash.
    with pytest.raises(SemanticIntegrationError, match="semantic node first crosses product"):
        validate_reconciliation_stage(bundle, stage, [response], require_all=False)
    paths = [tmp_path / name for name in ("bundle.json", "stage.json", "response.json", "nomination.json")]
    nomination = {"node_keys": ["first"], "reason": "Correct the identified identity grouping."}
    for path, value in zip(paths, (bundle, stage, response, nomination), strict=True):
        _write_json(path, value)
    args = dict(bundle_path=paths[0], stage_path=paths[1], failed_response_path=paths[2], nomination_path=paths[3])
    with pytest.raises(SemanticIntegrationError, match="local repair nomination omits incompatible nodes: second"):
        prepare_reconciliation_local_repair(**args, output_dir=tmp_path / "incomplete")
    assert not (tmp_path / "incomplete").exists()  # No launchable request or output.
    # An unrelated nomination reports BOTH known conflicts in one preparation.
    with pytest.raises(SemanticIntegrationError, match="omits incompatible nodes: first, second"):
        semantic_module.prepare_reconciliation_repair(bundle, stage, response,
            node_keys=["untouched"], reason="Review this separate wording.")
    # Explicit complete scope, not automatic expansion or semantic relabeling.
    nomination["node_keys"].append("second")
    args["nomination_path"] = tmp_path / "complete-nomination.json"
    _write_json(args["nomination_path"], nomination)
    prepared = prepare_reconciliation_local_repair(**args, output_dir=tmp_path / "complete")
    request = _load_object(tmp_path / "complete/request.json")["request"]
    assert prepared["candidate_count"] == 4 and prepared["model_api_calls"] == 0
    assert request["node_keys"] == ["first", "second"]
    assert request["candidate_refs"] == sorted(refs[:4]) and refs[4] not in request["prompt"]
    replacement = {"semantic_nodes": [], "decisions_by_candidate_ref": {}}
    for i, ref in enumerate(refs[:4]):
        key = f"separate_{i}"
        replacement["semantic_nodes"].append({**{k:v for k,v in template.items() if k != "opposition_checked"},
            "semantic_node_key": key})
        replacement["decisions_by_candidate_ref"][ref] = {
            "attachments": [{"semantic_node_key": key, "relation": "support"}], "unmerged_reason": None}
    patch = {"request_sha256": request["request_sha256"],
        "correction": {"replacement": replacement, "cannot_repair_reason": None}}
    patch_path = tmp_path / "patch.json"
    _write_json(patch_path, patch)
    submitted = dict(bundle_path=paths[0], stage_path=paths[1], failed_response_path=paths[2],
        request_path=tmp_path / "complete/request.json", patch_path=patch_path, output_dir=tmp_path / "successor")
    receipt = submit_reconciliation_local_repair(**submitted)
    assert submit_reconciliation_local_repair(**submitted) == receipt
    durable = _load_object(tmp_path / "successor/response.json")
    assert next(n for n in durable["semantic_nodes"] if n["semantic_node_key"] == "untouched") == response["semantic_nodes"][-1]
    assert durable["decisions_by_candidate_ref"][refs[4]] == response["decisions_by_candidate_ref"][refs[4]]
    assert _load_object(paths[2]) == response


def test_current_reconciliation_teaches_claim_relative_abstraction_not_literal_equivalence():
    bundle, _, stage, prompts, _ = _decision_reconciliation_fixture()
    policy = prompts[0]["prompt"].split("\n\nCANDIDATES\n", 1)[0]
    assert "Useful common claims need not repeat every child's wording or detail" in policy
    assert "Critique the unsupported change in meaning, not missing literal words" in policy
    assert "buy or try can support expressed interest" in policy
    assert "reported_behavior would credit behavior_evidence_refs" in policy
    assert "Do not join different benefits or behaviors with 'or'" not in policy
    assert "meaning-equivalent semantic nodes" not in policy
    legacy = semantic_module.prepare_reconciliation_prompts(bundle, stage,
        response_version=semantic_module.RECONCILIATION_RESPONSE_VERSION_V2)[0]["prompt"]
    assert "Useful common claims need not" not in legacy
    assert "Do not join different benefits or behaviors with 'or'" in legacy


def test_current_reconciliation_and_definition_recovery_leave_headcounts_to_compiler():
    bundle, _, stage, prompts, _ = _decision_reconciliation_fixture()
    _, _, _, _, request, _ = _missing_definition_fixture()
    for prompt in (prompts[0]["prompt"], request["prompt"]):
        policy = prompt.split("\n\nCANDIDATES\n", 1)[0]
        assert "Write bounded_meaning without inferring an author headcount" in policy
        assert "several statements or comments may come from one person" in policy
        assert "Code supplies origin and source-observation counts" in policy
        assert "Keep source-attributed statements about other people explicitly attributed" in policy
        assert "Inverse comparisons can express the same fact" in policy
        assert "one exact stored subject/comparator orientation" in policy
        candidates = json.loads(prompt.split("\n\nCANDIDATES\n", 1)[1].split(
            "\n\nEMERGING_AXIS_LABELS_TO_CONSOLIDATE\n", 1)[0])
        assert all("independence_key" not in row for row in candidates)
    legacy = semantic_module.prepare_reconciliation_prompts(bundle, stage,
        response_version=semantic_module.RECONCILIATION_RESPONSE_VERSION_V2)[0]["prompt"]
    assert "Write bounded_meaning without inferring an author headcount" not in legacy


def test_shared_interest_reaches_final_view_without_completed_behavior_credit():
    # Synthetic consumer fixture, not proof that a provider interprets sources.
    source = _source_v10(count=2)
    source["semantic_method_version"] = semantic_module.METHOD_VERSION_V12
    bundle = build_bundle(source, max_prompt_bytes=30_000)
    responses = _keyed_responses(bundle)
    statements = iter(["I want to buy this balm.", "I strongly want to try this balm."])
    for response in responses:
        for eid in response["decisions_by_evidence_id"]:
            row = _claim_row(eid)
            row.pop("evidence_id")
            row["semantic_units"][0].update(statement=next(statements), conditions=[],
                axis_ids=[], subject_product_ids=["summer-fridays-lip-butter-balm"])
            response["decisions_by_evidence_id"][eid] = row
    compiled = validate_batch_responses(bundle, responses)
    verification, _ = prepare_row_verification(bundle, compiled)
    verified = apply_row_verification(bundle, compiled, verification, _row_verification_responses(verification))
    stage, _ = prepare_reconciliation_stage(bundle, verified)
    old = _group_level_responses(stage, terminal=True)[0]
    node = old["semantic_nodes"][0]
    node.update(bounded_meaning="Expressed interest in this balm.", axis_ids=[],
        subject_product_ids=["summer-fridays-lip-butter-balm"])
    carried = {"subject_product_ids", "comparator_product_ids", "product_version_ids",
        "conditions", "polarity", "emerging_axis_labels", "child_relations"}
    response = dict(schema_version=semantic_module.RECONCILIATION_RESPONSE_VERSION_V3,
        stage_sha256=stage["stage_sha256"], batch_id=old["batch_id"],
        semantic_nodes=[{k: v for k, v in node.items() if k not in carried}],
        decisions_by_candidate_ref={ref: {"attachments": [{"semantic_node_key":node["semantic_node_key"],
            "relation":"support"}], "unmerged_reason":None} for ref in stage["batches"][0]["candidate_refs"]},
        assignments_by_original_label={}, emerging_axis_consolidations=[])
    nodes = validate_reconciliation_stage(bundle, stage, [response])
    view = finalize_v3_view(bundle, verified, nodes)
    proposition = view["propositions"][0]
    assert proposition["bounded_proposition"] == "Expressed interest in this balm."
    assert proposition["claim_kind"] == "customer_experience"
    assert len(proposition["claim_support"]["evidence_refs"]) == 2
    assert proposition["claim_support"]["behavior_evidence_refs"] == []
    assert set(proposition["semantic_relations"]["support"]) == set(response["decisions_by_candidate_ref"])
    assert [row["statement"] for row in verified["semantic_units"]] == [
        "I want to buy this balm.", "I strongly want to try this balm."]


def test_decision_reconciliation_resume_compacts_only_whitespace():
    bundle, _, stage, prompts, _ = _decision_reconciliation_fixture()
    stage["max_prompt_bytes"] = prompts[0]["prompt_utf8_bytes"] - 1
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    compact = semantic_module.prepare_reconciliation_prompts(bundle, stage)[0]
    assert compact["prompt_utf8_bytes"] <= stage["max_prompt_bytes"]
    marker = "\n\nCANDIDATES\n"
    labels = "\n\nEMERGING_AXIS_LABELS_TO_CONSOLIDATE\n"
    assert json.loads(compact["prompt"].split(marker)[1].split(labels)[0]) == json.loads(
        prompts[0]["prompt"].split(marker)[1].split(labels)[0])
    assert compact["response_schema"]["properties"]["decisions_by_candidate_ref"] == prompts[0]["response_schema"]["properties"]["decisions_by_candidate_ref"]


def test_decision_reconciliation_carries_historical_node_conditions_to_next_level():
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    index = {row["candidate_ref"]: row for row in stage["candidates"]}
    historical = semantic_module._assemble_decision_reconciliation(response, stage, stage["batches"][0],
        set(response["assignments_by_original_label"]), index, semantic_module._unit_index(bundle))
    # v2 allowed qualified node conditions in addition to literal leaf conditions.
    historical["semantic_nodes"][0]["conditions"].append("A retained prior-node qualification.")
    old_nodes = validate_reconciliation_stage(bundle, stage, [historical])
    next_stage, _ = prepare_reconciliation_stage(bundle, old_nodes)
    response["stage_sha256"] = next_stage["stage_sha256"]
    response["batch_id"] = next_stage["batches"][0]["batch_id"]
    response["decisions_by_candidate_ref"] = {next_stage["candidates"][0]["candidate_ref"]:
        {"attachments": [{"semantic_node_key": response["semantic_nodes"][0]["semantic_node_key"], "relation": "support"}], "unmerged_reason": None}}
    response["emerging_axis_consolidations"] = []
    response["assignments_by_original_label"] = {}
    compiled = validate_reconciliation_stage(bundle, next_stage, [response])
    assert set(compiled["semantic_nodes"][0]["conditions"]) == set(old_nodes["semantic_nodes"][0]["conditions"])
    assert compiled["semantic_nodes"][0]["condition_lineage"] == old_nodes["semantic_nodes"][0]["condition_lineage"]


def test_decision_reconciliation_public_loader_rejects_duplicate_keys(tmp_path):
    from runners.run_semantic_evidence_integration import _load_object
    path = tmp_path / "duplicate.json"
    path.write_text('{"assignments_by_original_label":{"price transparency":"one","price transparency":"two"}}')
    with pytest.raises(ValueError, match="duplicate JSON object key 'price transparency'"):
        _load_object(path)


def test_decision_reconciliation_v2_replay_and_mixed_transport():
    bundle, verified, stage, _, response = _decision_reconciliation_fixture()
    old_stage, old_prompts = prepare_reconciliation_stage(bundle, verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
        response_version=semantic_module.RECONCILIATION_RESPONSE_VERSION_V2)
    assert old_prompts == semantic_module.prepare_reconciliation_prompts(bundle, old_stage,
        response_version=semantic_module.RECONCILIATION_RESPONSE_VERSION_V2)
    assert "Copy every child condition verbatim" in old_prompts[0]["prompt"]
    index = {row["candidate_ref"]: row for row in stage["candidates"]}
    old = semantic_module._assemble_decision_reconciliation(response, stage, stage["batches"][0],
        set(response["assignments_by_original_label"]), index, semantic_module._unit_index(bundle))
    assert validate_reconciliation_stage(bundle, stage, [old]) == validate_reconciliation_stage(bundle, stage, [response])

    # A real split stage consumes one frozen v2 answer and one v3 answer together.
    refs = stage["batches"][0]["candidate_refs"]
    first_id = response["batch_id"]
    second_id = "reconcile-0001-0002"
    stage["batches"] = [{"batch_id": first_id, "candidate_refs": [refs[0]]},
                        {"batch_id": second_id, "candidate_refs": [refs[1]]}]
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    old["stage_sha256"] = response["stage_sha256"] = stage["stage_sha256"]
    old["semantic_nodes"][0]["child_relations"] = [{"child_ref": refs[0], "relation": "adjacent"}]
    old["semantic_nodes"][0]["polarity"] = stage["candidates"][0]["polarity"]
    response["batch_id"] = second_id
    del response["decisions_by_candidate_ref"][refs[0]]
    response["assignments_by_original_label"] = {}
    response["emerging_axis_consolidations"] = []
    mixed = validate_reconciliation_stage(bundle, stage, [old, response])
    assert len(mixed["semantic_nodes"]) == 2
    assert len(mixed["emerging_axis_consolidations"]) == 1
    assert {leaf["semantic_unit_ref"] for node in mixed["semantic_nodes"] for leaf in node["leaf_relations"]} == set(refs)


@pytest.mark.parametrize("mode,postures,allowed", [
    ("normal", ["first_hand"], False),
    ("normal", ["attribution_or_echo"], True),
    ("convergence", ["first_hand"], True),
])
def test_decision_reconciliation_schema_and_consumer_retention_agree(mode, postures, allowed):
    bundle, _, stage, _, response = _decision_reconciliation_fixture()
    stage["reconciliation_mode"] = mode
    for candidate in stage["candidates"]:
        candidate["evidence_postures"] = postures
    stage["stage_sha256"] = semantic_module._sha256({k: v for k, v in stage.items() if k != "stage_sha256"})
    response["stage_sha256"] = stage["stage_sha256"]
    response["semantic_nodes"] = []
    for decision in response["decisions_by_candidate_ref"].values():
        decision.update(attachments=[], unmerged_reason="Retained without terminal promotion.")
    prompt = semantic_module.prepare_reconciliation_prompts(bundle, stage)[0]
    assert prompt["response_schema"]["properties"]["semantic_nodes"].get("minItems", 0) == (0 if allowed else 1)
    slot = next(iter(prompt["response_schema"]["properties"]["decisions_by_candidate_ref"]["properties"].values()))
    slot = prompt["response_schema"]["$defs"][slot["$ref"].rsplit("/", 1)[1]]
    assert ("anyOf" in slot) is allowed
    if allowed:
        assert len(validate_reconciliation_stage(bundle, stage, [response])["unmerged_semantic_units"]) == 2
    else:
        with pytest.raises(SemanticIntegrationError, match="cannot unmerge required finding"):
            validate_reconciliation_stage(bundle, stage, [response])


def test_current_reconciliation_role_projection_preserves_relation_orientation() -> None:
    candidate = {
        "candidate_ref": "node", "statement": "bounded", "subject_product_ids": ["product"],
        "comparator_product_ids": [], "product_version_ids": [], "axis_ids": [],
        "emerging_axis_labels": [], "conditions": [], "polarity": "affirmed",
        "uncertainty_posture": "asserted",
        "leaf_relations": [{"semantic_unit_ref": "one::u", "relation": "support"},
                           {"semantic_unit_ref": "two::u", "relation": "counter"}],
    }
    index = {"one": {"source_role": "community_post"}, "two": {"source_role": "owned_source"}}
    projected = semantic_module._agent_reconciliation_candidate(candidate, evidence_index=index, include_source_roles=True)
    assert projected["source_roles_by_relation"] == {
        "support": ["community_post"], "counter": ["owned_source"], "adjacent": []}
    assert "source_roles_by_relation" not in semantic_module._agent_reconciliation_candidate(candidate)
    with pytest.raises(SemanticIntegrationError, match="prompt lacks source roles"):
        semantic_module._agent_reconciliation_candidate(candidate, include_source_roles=True)


def test_historical_methods_keep_their_frozen_reconciliation_posture_wording() -> None:
    # The agreement/origin sentence states a method-v7 rule. Methods v5 and v6
    # still credit personal_agreement in finalization, so emitting it for them
    # would instruct against their own projection and rewrite a frozen prompt.
    agreement_rule = "never use it to claim an additional independent origin"
    carried = "may use only first_hand or personal_agreement"
    for source in (_source_v5(count=2), _source_v6(count=2)):
        bundle = build_bundle(source, max_prompt_bytes=20_000)
        compiled = validate_batch_responses(
            bundle, _v5_responses(bundle, detailed_per_batch=2)
        )
        _, prompts = prepare_reconciliation_stage(bundle, compiled)
        assert prompts
        assert all(carried in row["prompt"] for row in prompts)
        assert not any(agreement_rule in row["prompt"] for row in prompts)

    bundle, verified = _agreement_bundle_and_units()
    _, v7_prompts = prepare_reconciliation_stage(bundle, verified)
    assert all(agreement_rule in row["prompt"] for row in v7_prompts)


def test_v3_full_corpus_accounting_fails_closed_on_missing_leaf() -> None:
    source = _source_v3()
    source["captured_items"].pop()

    with pytest.raises(SemanticIntegrationError, match="captured_leaf_count"):
        build_bundle(source, max_prompt_bytes=8_000)


def test_v3_materializer_is_deterministic_and_rejects_unsupported_family() -> None:
    source = _source_v3(count=2)
    first = materialize_source_v3(source)
    second = materialize_source_v3(deepcopy(source))
    assert first == second
    assert first["source_sha256"]

    source["captured_items"][0]["source_family"] = "unknown_future_family"
    with pytest.raises(SemanticIntegrationError, match="unsupported source_family"):
        materialize_source_v3(source)


def test_v3_materializer_validates_without_provisional_batch_packing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_packed(*args: object, **kwargs: object) -> list[dict]:
        raise AssertionError("batch packing belongs to prepare-batches")

    monkeypatch.setattr(
        "judgment.semantic_evidence_integration._pack_v4_work_units",
        fail_if_packed,
    )
    source = _source_v3(count=2)

    materialized = materialize_source_v3(source)

    assert len(materialized["captured_items"]) == 2
    with pytest.raises(AssertionError, match="prepare-batches"):
        build_bundle(source, max_prompt_bytes=8_000)


def test_v3_unknown_actor_cannot_receive_independence_credit() -> None:
    source = _source_v3(count=1)
    source["captured_items"][0]["independence_posture"] = "unavailable"
    # The stale-looking key is retained deliberately: compiler posture, not a
    # nonempty operator string, owns whether independence credit is possible.
    bundle = build_bundle(source, max_prompt_bytes=8_000)
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    terminal = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=True)
    )
    view = finalize_v3_view(bundle, compiled, terminal)

    assert view["propositions"][0]["claim_support"]["independent_origin_count"] == 0


def test_v3_reconciliation_rejects_dropped_conditions_and_collapsed_negation() -> None:
    bundle = build_bundle(_source_v3(count=2), max_prompt_bytes=20_000)
    responses = _v3_batch_responses(bundle)
    responses[0]["evidence"][1]["semantic_units"][0]["conditions"] = ["only in winter"]
    responses[0]["evidence"][1]["semantic_units"][0]["polarity"] = "negated"
    compiled = validate_batch_responses(bundle, responses)
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    collapsed = _group_level_responses(stage, terminal=True)
    collapsed[0]["semantic_nodes"][0]["conditions"] = ["after one week of use"]
    collapsed[0]["semantic_nodes"][0]["polarity"] = "affirmed"

    with pytest.raises(
        SemanticIntegrationError, match="drops a child condition|collapses child polarity"
    ):
        validate_reconciliation_stage(bundle, stage, collapsed)


def test_v3_reconciliation_rejects_stale_stage_and_unaccounted_child() -> None:
    bundle = build_bundle(_source_v3(count=2), max_prompt_bytes=20_000)
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    responses = _group_level_responses(stage, terminal=True)
    stale = deepcopy(responses)
    stale[0]["stage_sha256"] = "0" * 64
    with pytest.raises(SemanticIntegrationError, match="stale stage hash"):
        validate_reconciliation_stage(bundle, stage, stale)

    missing = deepcopy(responses)
    missing[0]["semantic_nodes"][0]["child_relations"].pop()
    with pytest.raises(SemanticIntegrationError, match="does not account for every child"):
        validate_reconciliation_stage(bundle, stage, missing)


def test_v3_reconciliation_rejects_same_level_cycle() -> None:
    bundle = build_bundle(_source_v3(count=2), max_prompt_bytes=20_000)
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    node_compilation = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=False)
    )
    node_ref = node_compilation["semantic_nodes"][0]["semantic_node_ref"]
    node_compilation["semantic_nodes"][0]["child_relations"] = [
        {"child_ref": node_ref, "relation": "support"}
    ]
    unhashed = dict(node_compilation)
    unhashed.pop("node_compilation_sha256")
    node_compilation["node_compilation_sha256"] = hashlib.sha256(
        json.dumps(
            unhashed, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()

    with pytest.raises(SemanticIntegrationError, match="same-level link or cycle"):
        prepare_reconciliation_stage(bundle, node_compilation)


def test_v3_emerging_labels_require_explicit_consolidation() -> None:
    bundle = build_bundle(_source_v3(count=1), max_prompt_bytes=20_000)
    responses = _v3_batch_responses(bundle)
    responses[0]["evidence"][0]["semantic_units"][0]["emerging_axis_labels"] = [
        "nightly ritual"
    ]
    compiled = validate_batch_responses(bundle, responses)
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    reconciliation = _group_level_responses(stage, terminal=True)

    with pytest.raises(SemanticIntegrationError, match="every emerging label"):
        validate_reconciliation_stage(bundle, stage, reconciliation)

    reconciliation[0]["emerging_axis_consolidations"] = [
        {
            "candidate_key": "ritual",
            "canonical_label": "use ritual",
            "original_labels": ["nightly ritual"],
            "disposition": "accepted",
            "reason": "meaning-equivalent use ritual label",
        }
    ]
    terminal = validate_reconciliation_stage(bundle, stage, reconciliation)
    view = finalize_v3_view(bundle, compiled, terminal)
    assert view["emerging_axis_candidates"][0]["original_labels"] == [
        "nightly ritual"
    ]


def test_v4_one_batch_owns_level_wide_emerging_axis_consolidation() -> None:
    bundle = build_bundle(_source_v3(), max_prompt_bytes=6_000)
    responses = _v3_batch_responses(bundle)
    for response in responses:
        for evidence in response["evidence"]:
            for unit in evidence["semantic_units"]:
                unit["emerging_axis_labels"] = ["shared label"]
    compiled = validate_batch_responses(bundle, responses)

    stage, prompts = prepare_reconciliation_stage(bundle, compiled)
    assert len(stage["batches"]) > 1
    owner = stage["emerging_axis_owner_batch_id"]
    assert owner == stage["batches"][0]["batch_id"]
    assert "EMERGING_AXIS_LABELS_TO_CONSOLIDATE" in prompts[0]["prompt"]
    assert all(
        "Return an empty emerging_axis_consolidations list" in row["prompt"]
        for row in prompts[1:]
    )

    reconciliation = _group_level_responses(stage, terminal=False)
    for response in reconciliation:
        response["emerging_axis_consolidations"] = (
            [
                {
                    "candidate_key": "shared",
                    "canonical_label": "shared label",
                    "original_labels": ["shared label"],
                    "disposition": "accepted",
                    "reason": "one level-wide semantic decision",
                }
            ]
            if response["batch_id"] == owner
            else []
        )

    level_one = validate_reconciliation_stage(bundle, stage, reconciliation)
    assert level_one["emerging_axis_consolidations"] == [
        {
            "candidate_key": "shared",
            "canonical_label": "shared label",
            "original_labels": ["shared label"],
            "disposition": "accepted",
            "reason": "one level-wide semantic decision",
        }
    ]


def _one_label_level_one(*, disposition: str = "blocker") -> tuple[dict, dict, dict]:
    bundle = build_bundle(_source_v3(count=1), max_prompt_bytes=20_000)
    responses = _v3_batch_responses(bundle)
    responses[0]["evidence"][0]["semantic_units"][0]["emerging_axis_labels"] = [
        "nightly ritual"
    ]
    compiled = validate_batch_responses(bundle, responses)
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    reconciliation = _group_level_responses(stage, terminal=False)
    reconciliation[0]["emerging_axis_consolidations"] = [
        {
            "candidate_key": "ritual",
            "canonical_label": "use ritual",
            "original_labels": ["nightly ritual"],
            "disposition": disposition,
            "reason": "frozen lower-level disposition",
        }
    ]
    return bundle, compiled, validate_reconciliation_stage(
        bundle, stage, reconciliation
    )


def test_v3_lower_level_blocker_survives_to_terminal_view() -> None:
    bundle, compiled, level_one = _one_label_level_one()
    stage_two, prompts = prepare_reconciliation_stage(bundle, level_one)
    assert "every label was already carried from a prior level" in prompts[0]["prompt"]
    assert stage_two["carried_emerging_axis_consolidations"] == [
        {
            "candidate_key": "ritual",
            "canonical_label": "use ritual",
            "original_labels": ["nightly ritual"],
            "disposition": "blocker",
            "reason": "frozen lower-level disposition",
        }
    ]
    terminal = validate_reconciliation_stage(
        bundle, stage_two, _group_level_responses(stage_two, terminal=True)
    )
    view = finalize_v3_view(bundle, compiled, terminal)

    assert view["emerging_axis_candidates"] == stage_two[
        "carried_emerging_axis_consolidations"
    ]


@pytest.mark.parametrize("replacement", [[], ["nightly ritual", "invented label"]])
def test_v3_parent_cannot_drop_or_invent_child_emerging_labels(
    replacement: list[str],
) -> None:
    bundle, _, level_one = _one_label_level_one(disposition="accepted")
    stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
    responses = _group_level_responses(stage_two, terminal=True)
    responses[0]["semantic_nodes"][0]["emerging_axis_labels"] = replacement

    with pytest.raises(SemanticIntegrationError, match="exact union"):
        validate_reconciliation_stage(bundle, stage_two, responses)


@pytest.mark.parametrize(
    "replacement",
    [
        {
            "candidate_key": "ritual-copy",
            "canonical_label": "copied ritual",
            "original_labels": ["nightly ritual"],
            "disposition": "nonmaterial",
            "reason": "attempted overwrite",
        },
        {
            "candidate_key": "ritual",
            "canonical_label": "different label",
            "original_labels": ["new label"],
            "disposition": "accepted",
            "reason": "attempted key overwrite",
        },
    ],
)
def test_v3_carried_consolidation_cannot_be_duplicated_or_overwritten(
    replacement: dict,
) -> None:
    bundle, _, level_one = _one_label_level_one(disposition="accepted")
    stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
    responses = _group_level_responses(stage_two, terminal=True)
    responses[0]["emerging_axis_consolidations"] = [replacement]

    with pytest.raises(SemanticIntegrationError, match="invalid or duplicate"):
        validate_reconciliation_stage(bundle, stage_two, responses)


def _rehash_node_compilation(compilation: dict) -> dict:
    core = {
        key: value
        for key, value in compilation.items()
        if key != "node_compilation_sha256"
    }
    compilation["node_compilation_sha256"] = hashlib.sha256(
        json.dumps(
            core, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return compilation


def test_v3_terminal_hierarchy_cannot_drop_a_semantic_unit() -> None:
    bundle, compiled, terminal, _ = _v3_complete_view()
    forged = deepcopy(terminal)
    node = forged["semantic_nodes"][0]
    dropped = node["leaf_relations"][0]["semantic_unit_ref"]
    node["leaf_relations"] = node["leaf_relations"][1:]
    node["condition_lineage"] = [
        row for row in node["condition_lineage"] if row["semantic_unit_ref"] != dropped
    ]
    _rehash_node_compilation(forged)

    with pytest.raises(SemanticIntegrationError, match="every semantic unit"):
        finalize_v3_view(bundle, compiled, forged)


def test_v3_finalization_rejects_lineage_from_another_batch_compilation() -> None:
    bundle, _, terminal, _ = _v3_complete_view()
    different = _v3_batch_responses(bundle)
    different[0]["evidence"][0]["semantic_units"][0]["statement"] = (
        "A different meaning with the same semantic-unit denominator."
    )
    other_compilation = validate_batch_responses(bundle, different)

    with pytest.raises(SemanticIntegrationError, match="root batch compilation"):
        finalize_v3_view(bundle, other_compilation, terminal)


def test_v3_finalization_rejects_unmerged_unit_outside_the_batch_compilation() -> None:
    bundle, compiled, terminal, _ = _v3_complete_view()
    forged = deepcopy(terminal)
    forged["unmerged_semantic_units"] = [
        {"semantic_unit_ref": "reddit:t1:comment::not-a-real-unit", "reason": "forged"}
    ]
    _rehash_node_compilation(forged)

    with pytest.raises(SemanticIntegrationError, match="not part of this batch compilation"):
        finalize_v3_view(bundle, compiled, forged)


def test_v3_finalization_rejects_a_repeated_unmerged_semantic_unit() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dogfood = (
        repo_root
        / "docs/research/summer_fridays_understanding_dogfood_20260802_p11r7"
        / "semantic_integration_multisource_route_1_6_regression_20260808_v0"
    )
    bundle = json.loads((dogfood / "bundle.json").read_text(encoding="utf-8"))
    compiled = json.loads(
        (dogfood / "batch_compilation.json").read_text(encoding="utf-8")
    )
    terminal = json.loads(
        (dogfood / "node_compilation_2.json").read_text(encoding="utf-8")
    )
    assert terminal["unmerged_semantic_units"]

    repeated = deepcopy(terminal)
    repeated["unmerged_semantic_units"].append(
        deepcopy(repeated["unmerged_semantic_units"][0])
    )
    _rehash_node_compilation(repeated)

    with pytest.raises(
        SemanticIntegrationError, match="duplicate unmerged semantic unit"
    ):
        finalize_v3_view(bundle, compiled, repeated)


def test_v3_controlled_partition_sensitivity_preserves_leaf_membership_and_counts() -> None:
    _, _, _, narrow = _v3_complete_view_at_ceiling(max_prompt_bytes=8_000)
    _, _, _, wide = _v3_complete_view_at_ceiling(max_prompt_bytes=12_000)

    narrow_prop = narrow["propositions"][0]
    wide_prop = wide["propositions"][0]
    assert set(narrow_prop["semantic_relations"]["support"]) == set(
        wide_prop["semantic_relations"]["support"]
    )
    assert narrow_prop["evidence_stack"] == wide_prop["evidence_stack"]
    assert narrow_prop["claim_support"] == wide_prop["claim_support"]


def test_route_1_6_multisource_dogfood_rebuilds_exactly() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dogfood = (
        repo_root
        / "docs/research/summer_fridays_understanding_dogfood_20260802_p11r7"
        / "semantic_integration_multisource_route_1_6_regression_20260808_v0"
    )

    def load(name: str) -> dict | list:
        return json.loads((dogfood / name).read_text(encoding="utf-8"))

    source = load("source.json")
    expected_bundle = load("bundle.json")
    assert isinstance(source, dict) and isinstance(expected_bundle, dict)
    bundle = build_bundle(
        source,
        max_prompt_bytes=150_000,
        target_bundle_version=BUNDLE_VERSION_V3,
    )
    assert bundle == expected_bundle

    responses = load("batch_responses.json")
    assert isinstance(responses, list)
    compiled = validate_batch_responses(bundle, responses)
    assert compiled == load("batch_compilation.json")

    stage_one, prompts_one = prepare_reconciliation_stage(bundle, compiled)
    assert stage_one == load("reconciliation_stage_1.json")
    assert prompts_one == load("reconciliation_prompts_1.json")
    responses_one = load("reconciliation_responses_1.json")
    assert isinstance(responses_one, list)
    nodes_one = validate_reconciliation_stage(
        bundle, stage_one, responses_one
    )
    assert nodes_one == load("node_compilation_1.json")

    stage_two, prompts_two = prepare_reconciliation_stage(bundle, nodes_one)
    assert stage_two == load("reconciliation_stage_2.json")
    assert prompts_two == load("reconciliation_prompts_2.json")
    response_two = load("reconciliation_response_2.json")
    assert isinstance(response_two, dict)
    nodes_two = validate_reconciliation_stage(
        bundle, stage_two, [response_two]
    )
    assert nodes_two == load("node_compilation_2.json")
    historical_view = load("view.json")
    current_view = finalize_v3_view(bundle, compiled, nodes_two)
    expected_view = deepcopy(historical_view)
    for proposition in expected_view["propositions"]:
        if proposition["claim_support"]["conflict_posture"] == "none_observed":
            proposition["claim_support"]["conflict_posture"] = "not_checked"
    _rehash_view(expected_view)
    assert current_view == expected_view

    sensitivity = load("partition_sensitivity.json")
    assert isinstance(sensitivity, dict)
    assert sensitivity["partitions_differ"] is True
    assert sensitivity["flattened_membership_and_counts_equal"] is True


# --- New generation: bundle v5 / projection v2 / method v5 / response v3 ---
#
# Frozen legacy expectations below were observed from the pre-change module at
# revision 27b3c56d. They are byte-level regression anchors for the legacy v4
# path, not semantic ground truth.
_FROZEN_V4_PLAIN = {
    "bundle_sha256": "3478626e9e8296250969ff83f648ae71b09f475eb68eedf9107488539efebf1b",
    "corpus_sha256": "c344feb0b7741fcf76ac83784091a076cfe8a1b591e59575eeecb5c00640971d",
    "projection_sha256": "710685030cdbdd417411d3d75531d9ad96609931d5fbe3eaef17af5afc035887",
    "prompt_utf8_bytes": 7174,
    "prompt_sha256": "1f6e556f3d79933756a32421d21802bb07018e27ca6605e406e513b655028aa2",
    "compilation_sha256": "248c87617f6a2101bb382eb28a61d369d7064ff84930c04fd52aa19cd99e85eb",
}
_FROZEN_V4_CATALOG = {
    "bundle_sha256": "b69d975f4bf2b84696050543e877988f8cd2c7b775e42a44da69d85380464a51",
    "corpus_sha256": "1f407c04a777ff1e00fb8fa27ec1ecfff02a323fba1927b91989a8d307fe43a9",
    "prompt_utf8_bytes": 8333,
    "prompt_sha256": "ae56141d2837b71dedd6ab336d81f1b7bc75844b5f655b11e9b19a2f17f14382",
}


def _joined_prompt_digest(prompts: list[dict]) -> tuple[int, str]:
    joined = "\n".join(row["prompt"] for row in prompts).encode("utf-8")
    return len(joined), hashlib.sha256(joined).hexdigest()


def _source_v5(*, count: int = 7, catalog: bool = False) -> dict:
    source = _source_v3(count=count)
    source["semantic_method_version"] = METHOD_VERSION_V5
    if catalog:
        source["product_identity_catalog"] = _product_catalog()
    return source


def _source_v6(*, count: int = 7, catalog: bool = False) -> dict:
    source = _source_v5(count=count, catalog=catalog)
    source["semantic_method_version"] = METHOD_VERSION_V6
    return source


def _source_v7(*, count: int = 7, catalog: bool = False) -> dict:
    source = _source_v6(count=count, catalog=catalog)
    source["semantic_method_version"] = METHOD_VERSION_V7
    return source


def _source_v8(*, count: int = 7, catalog: bool = True) -> dict:
    source = _source_v7(count=count, catalog=catalog)
    source["semantic_method_version"] = METHOD_VERSION_V8
    return source


def _source_v9(*, count: int = 7, catalog: bool = True) -> dict:
    source = _source_v8(count=count, catalog=catalog)
    source["semantic_method_version"] = METHOD_VERSION_V9
    return source


def _source_v10(*, count: int = 7, catalog: bool = True) -> dict:
    source = _source_v9(count=count, catalog=catalog)
    source["semantic_method_version"] = METHOD_VERSION_V10
    return source


def _bundle_v5(*, count: int = 7, max_prompt_bytes: int = 12_000) -> dict:
    return build_bundle(_source_v5(count=count), max_prompt_bytes=max_prompt_bytes)


def _bundle_v8(*, count: int = 7, max_prompt_bytes: int = 12_000) -> dict:
    return build_bundle(_source_v8(count=count), max_prompt_bytes=max_prompt_bytes)


def _bundle_v9(*, count: int = 7, max_prompt_bytes: int = 12_000) -> dict:
    return build_bundle(_source_v9(count=count), max_prompt_bytes=max_prompt_bytes)


def _bundle_v10(*, count: int = 7, max_prompt_bytes: int = 12_000) -> dict:
    return build_bundle(_source_v10(count=count), max_prompt_bytes=max_prompt_bytes)


def _claim_row(evidence_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "disposition": "claim_bearing",
        "disposition_reason": "direct first-hand experience",
        "semantic_units": [
            {
                "semantic_unit_key": "drying-after-week",
                "statement": "The balm became drying after one week of use.",
                "subject_product_ids": ["sf-lbb"],
                "comparator_product_ids": [],
                "product_version_ids": [],
                "axis_ids": ["wear"],
                "emerging_axis_labels": [],
                "conditions": ["after one week of use"],
                "polarity": "affirmed",
                "evidence_posture": "first_hand",
                "uncertainty_posture": "asserted",
            }
        ],
    }


def _v5_responses(
    bundle: dict, *, detailed_per_batch: int = 1, group_disposition: str = "context_only"
) -> list[dict]:
    """Detailed head plus one explicit-id terminal group per work unit."""
    responses = []
    for batch in bundle["batches"]:
        ids = batch["evidence_ids"]
        detailed, grouped = ids[:detailed_per_batch], ids[detailed_per_batch:]
        responses.append(
            {
                "schema_version": BATCH_RESPONSE_VERSION_V3,
                "bundle_sha256": bundle["bundle_sha256"],
                "batch_id": batch["batch_id"],
                "evidence": [_claim_row(row) for row in detailed],
                "terminal_groups": (
                    [
                        {
                            "disposition": group_disposition,
                            "disposition_reason": (
                                "no bounded proposition remains after reading context"
                            ),
                            "evidence_ids": list(grouped),
                        }
                    ]
                    if grouped
                    else []
                ),
            }
        )
    return responses


def _keyed_responses(bundle: dict) -> list[dict]:
    response_version = bundle["semantic_work_unit_projection"][
        "semantic_execution_identity"
    ]["response_schema_version"]
    return [
        {
            "schema_version": response_version,
            "bundle_sha256": bundle["bundle_sha256"],
            "batch_id": batch["batch_id"],
            "decisions_by_evidence_id": {
                evidence_id: {
                    "disposition": "context_only",
                    "disposition_reason": "no bounded proposition remains after context",
                    "semantic_units": [],
                }
                for evidence_id in batch["evidence_ids"]
            },
        }
        for batch in bundle["batches"]
    ]


def _row_verification_responses(
    stage: dict, decisions: dict[str, dict] | None = None
) -> list[dict]:
    decisions = decisions or {}
    return [
        {
            "schema_version": ROW_VERIFICATION_RESPONSE_VERSION,
            "stage_sha256": stage["stage_sha256"],
            "batch_id": batch["batch_id"],
            "decisions": [
                {
                    "evidence_id": evidence_id,
                    "decision": decisions.get(evidence_id, {}).get(
                        "decision", "accept"
                    ),
                    "reason": decisions.get(evidence_id, {}).get(
                        "reason", "the proposed row is complete and source-supported"
                    ),
                    "replacement": decisions.get(evidence_id, {}).get(
                        "replacement"
                    ),
                }
                for evidence_id in batch["evidence_ids"]
            ],
        }
        for batch in stage["batches"]
    ]


def _targeted_audit_fixture() -> tuple[dict, dict, dict, dict, dict, dict[str, str]]:
    bundle = _bundle_v5(count=36, max_prompt_bytes=12_000)
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    row_stage, _ = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    verified = apply_row_verification(
        bundle, compiled, row_stage, _row_verification_responses(row_stage)
    )
    batch_ids = [row["batch_id"] for row in bundle["batches"]]
    evidence_count = sum(len(row["evidence_ids"]) for row in bundle["batches"])
    raw = {
        "selection": "a" * 64,
        "benchmark": "b" * 64,
        "bundle": "c" * 64,
        "row_verification_stage": "d" * 64,
        "verified_compilation": "e" * 64,
    }
    benchmark = {
        "schema_version": "forseti_extraction_latency_optimization_benchmark_v2",
        "identities": {
            "bundle_stored_canonical_sha256": bundle["bundle_sha256"],
            "bundle_raw_file_sha256": raw["bundle"],
        },
        "benchmark": {
            "prompt_count": len(batch_ids),
            "validated_evidence_count": evidence_count,
        },
    }
    midpoint = len(batch_ids) // 2
    group_ids = [batch_ids[:midpoint], batch_ids[midpoint:]]
    selection = {
        "schema_version": "targeted_benchmark_audit_selection_v1",
        "authority": {
            "benchmark_raw_sha256": raw["benchmark"],
            "bundle_stored_canonical_sha256": bundle["bundle_sha256"],
            "bundle_raw_sha256": raw["bundle"],
            "row_verification_stage_stored_canonical_sha256": row_stage[
                "stage_sha256"
            ],
            "row_verification_stage_raw_sha256": raw["row_verification_stage"],
        },
        "selection_method": {
            "kind": "complete_benchmark_denominator",
            "prompt_count": len(batch_ids),
            "evidence_leaf_count": evidence_count,
        },
        "benchmark_groups": [
            {
                "source_receipt_worker_id": f"source-worker-{index + 1}",
                "batch_ids": ids,
                "evidence_leaf_count": sum(
                    len(bundle["batches"][batch_ids.index(batch_id)]["evidence_ids"])
                    for batch_id in ids
                ),
            }
            for index, ids in enumerate(group_ids)
        ],
        "constraints": {
            "manual_full_payload_read": True,
            "genuine_prompt_local_semantic_judgment": True,
            "semantic_automation": False,
            "regex_or_keyword_semantic_rules": False,
            "templates_or_defaults": False,
            "external_provider_or_model_api_calls": 0,
            "prevalence_or_causal_inference": False,
            "global_absence_identity_or_opposition_claims": False,
            "customer_ready_conclusions": False,
        },
    }
    return bundle, verified, selection, benchmark, row_stage, raw


def test_targeted_benchmark_audit_binds_exact_groups_and_balances_workers() -> None:
    bundle, verified, selection, benchmark, row_stage, raw = (
        _targeted_audit_fixture()
    )
    prepared = prepare_targeted_benchmark_audit(
        bundle,
        verified,
        selection,
        benchmark,
        row_stage,
        input_raw_sha256=raw,
        max_prompt_bytes=100_000,
        worker_count=6,
    )
    stage, frame, prompts, prompt_manifest, assignments = prepared
    assert stage["coverage_proof"]["selected_evidence_count"] == 36
    assert stage["coverage_proof"]["original_batch_groups_preserved"] is True
    assert [row["batch_id"] for row in prompts] == [
        row["batch_id"] for row in bundle["batches"]
    ]
    assert stage["audit_method_version"] == "targeted_benchmark_audit_method_v2"
    assert stage["audit_method_sha256"] == semantic_module._sha256(
        semantic_module.TARGETED_AUDIT_METHOD_TEXT
    )
    assert "TARGETED BENCHMARK AUDIT METHOD V2" in frame
    assert "decision-relevant finding required by this audit" in frame
    assert "vocabulary mismatch itself is not a repair reason" in frame
    assert "existence or completion state of an event or action" in frame
    assert "Descriptive-channel detail is not load-bearing unless" in frame
    assert "looks supple" not in semantic_module.TARGETED_AUDIT_METHOD_TEXT
    assert "feels supple" not in semantic_module.TARGETED_AUDIT_METHOD_TEXT
    assert "decided to try" not in semantic_module.TARGETED_AUDIT_METHOD_TEXT
    assert "bought" not in semantic_module.TARGETED_AUDIT_METHOD_TEXT
    assert prompt_manifest["stage_sha256"] == stage["stage_sha256"]
    assigned = [
        prompt["batch_id"]
        for worker in assignments["workers"]
        for prompt in worker["prompts"]
    ]
    assert sorted(assigned) == sorted(row["batch_id"] for row in prompts)
    assert len(assignments["workers"]) == 6
    assert max(len(row["prompts"]) for row in assignments["workers"]) == 2
    assert prepared == prepare_targeted_benchmark_audit(
        bundle,
        verified,
        selection,
        benchmark,
        row_stage,
        input_raw_sha256=raw,
        max_prompt_bytes=100_000,
        worker_count=6,
    )

    responses = []
    repair_id = stage["batches"][0]["evidence_ids"][0]
    for batch in stage["batches"]:
        responses.append(
            {
                "schema_version": TARGETED_AUDIT_RESPONSE_VERSION,
                "stage_sha256": stage["stage_sha256"],
                "batch_id": batch["batch_id"],
                "decisions": [
                    {
                        "evidence_id": evidence_id,
                        "decision": "repair" if evidence_id == repair_id else "accept",
                        "reason": "manual source comparison found the bounded result",
                    }
                    for evidence_id in batch["evidence_ids"]
                ],
            }
        )
    result = validate_targeted_benchmark_audit(stage, prompt_manifest, responses)
    assert result["repair_evidence_ids"] == [repair_id]
    assert result["coverage_proof"]["complete"] is True


def test_targeted_benchmark_audit_rejects_identity_substitution() -> None:
    bundle, verified, selection, benchmark, row_stage, raw = (
        _targeted_audit_fixture()
    )
    forged = deepcopy(selection)
    forged["authority"]["benchmark_raw_sha256"] = "f" * 64
    with pytest.raises(SemanticIntegrationError, match="identity mismatch"):
        prepare_targeted_benchmark_audit(
            bundle,
            verified,
            forged,
            benchmark,
            row_stage,
            input_raw_sha256=raw,
            max_prompt_bytes=100_000,
            worker_count=6,
        )


def test_targeted_benchmark_audit_runner_refuses_overwrite(tmp_path: Path) -> None:
    bundle, verified, selection, benchmark, row_stage, _ = _targeted_audit_fixture()
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    paths = {
        "bundle": inputs / "bundle.json",
        "verified": inputs / "verified.json",
        "row_stage": inputs / "row_stage.json",
        "benchmark": inputs / "benchmark.json",
        "selection": inputs / "selection.json",
    }
    for key, value in (
        ("bundle", bundle),
        ("verified", verified),
        ("row_stage", row_stage),
    ):
        paths[key].write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    bundle_raw = _digest(paths["bundle"].read_bytes())
    row_stage_raw = _digest(paths["row_stage"].read_bytes())
    benchmark["identities"]["bundle_raw_file_sha256"] = bundle_raw
    paths["benchmark"].write_text(json.dumps(benchmark, sort_keys=True), encoding="utf-8")
    selection["authority"].update(
        {
            "benchmark_raw_sha256": _digest(paths["benchmark"].read_bytes()),
            "bundle_raw_sha256": bundle_raw,
            "row_verification_stage_raw_sha256": row_stage_raw,
        }
    )
    paths["selection"].write_text(json.dumps(selection, sort_keys=True), encoding="utf-8")
    outputs = tmp_path / "outputs"
    kwargs = {
        "bundle_path": paths["bundle"],
        "verified_path": paths["verified"],
        "selection_path": paths["selection"],
        "benchmark_path": paths["benchmark"],
        "row_verification_stage_path": paths["row_stage"],
        "stage_out": outputs / "stage.json",
        "shared_frame_out": outputs / "shared_frame.md",
        "prompt_manifest_out": outputs / "prompt_manifest.json",
        "assignment_manifest_out": outputs / "assignments.json",
        "prompt_dir": outputs / "prompts",
        "max_prompt_bytes": 100_000,
        "worker_count": 6,
    }
    result = prepare_targeted_benchmark_audit_run(**kwargs)
    assert result["status"] == "TARGETED_BENCHMARK_AUDIT_REQUIRED"
    stage_bytes = kwargs["stage_out"].read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        prepare_targeted_benchmark_audit_run(**kwargs)
    assert kwargs["stage_out"].read_bytes() == stage_bytes


def test_row_verification_replaces_the_whole_row_and_keeps_one_active_result() -> None:
    bundle = _bundle_v5(count=4)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=3)
    )
    stage, prompts = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    claim_ids = [row["evidence_id"] for row in stage["verification_rows"]]
    assert len(claim_ids) == 3
    assert stage["coverage_proof"]["bijection_complete"] is True
    assert all(row["prompt_utf8_bytes"] <= stage["max_prompt_bytes"] for row in prompts)
    assert all("ROWS_TO_VERIFY" in row["prompt"] for row in prompts)
    assert all("V8 KEYED RESPONSE TRANSPORT" not in row["prompt"] for row in prompts)
    assert all("decisions_by_evidence_id" not in row["prompt"] for row in prompts)
    assert all('"decisions"' in row["prompt"] for row in prompts)
    assert stage["verification_method_version"] == ROW_VERIFICATION_METHOD_VERSION
    normalized_prompts = [" ".join(row["prompt"].split()) for row in prompts]
    assert all("Before checking fields, privately restate" in row for row in normalized_prompts)
    assert all(
        "does not cancel or replace an earlier judgment" in row
        for row in normalized_prompts
    )
    assert all("Map each meaning to the proposed units" in row for row in normalized_prompts)
    assert all("before field checking" in row for row in normalized_prompts)
    assert all("direct short answer" in row["prompt"] for row in prompts)
    assert all("Resolve a leading yes/no" in row["prompt"] for row in prompts)
    assert all(
        "repurchase of a named shade, or of an all/every-shade collection"
        in row["prompt"]
        for row in prompts
    )
    assert all("Do not carry an axis across a clause boundary" in row["prompt"] for row in prompts)
    assert all(
        "A customer attribute conditions a result only when" in row["prompt"]
        for row in prompts
    )
    assert all("directly relevant baseline" in row for row in normalized_prompts)
    assert all("source explicitly scopes that result" in row for row in normalized_prompts)
    assert all("Conjunction, proximity, or shared body area" in row for row in normalized_prompts)
    assert all("leave the result unconditioned" in row for row in normalized_prompts)
    assert all(
        "not retained as a result's condition" in row for row in normalized_prompts
    )
    assert all("omit it from that result's statement too" in row for row in normalized_prompts)
    assert all("explicitly identifies the bound product" in row for row in normalized_prompts)
    assert all("ambiguous antecedent remains context" in row for row in normalized_prompts)
    assert all("source-to-unit completeness pass" in row for row in normalized_prompts)
    assert all("same dimension and direction" in row for row in normalized_prompts)
    assert all("Unqualified liking, preference" in row["prompt"] for row in prompts)
    assert all("favorite evaluation of a named shade carries" in row["prompt"] for row in prompts)
    assert all("Drying, becoming drier, or losing moisture" in row["prompt"] for row in prompts)
    assert all("adjacent or comparator product is not a target-product" in row["prompt"] for row in prompts)
    assert all("Preserve the proposed row by default" in row["prompt"] for row in prompts)
    assert all("Replacement is correction, not fresh regeneration" in row for row in normalized_prompts)
    assert all("One side's quantity cannot create" in row["prompt"] for row in prompts)
    replacement = _claim_row(claim_ids[1])
    replacement["semantic_units"][0]["semantic_unit_key"] = "corrected-value"
    replacement["semantic_units"][0]["statement"] = (
        "The balm is not worth its advertised price."
    )
    replacement["semantic_units"][0]["axis_ids"] = []
    decisions = {
        claim_ids[1]: {
            "decision": "replace",
            "reason": "the original overstated the source",
            "replacement": replacement,
        },
        claim_ids[2]: {
            "decision": "unresolved",
            "reason": "the source supports multiple plausible meanings",
            "replacement": None,
        },
    }
    responses = _row_verification_responses(stage, decisions)
    verified = apply_row_verification(bundle, compiled, stage, responses)

    refs = {row["semantic_unit_ref"] for row in verified["semantic_units"]}
    assert f"{claim_ids[0]}::drying-after-week" in refs
    assert f"{claim_ids[1]}::corrected-value" in refs
    assert f"{claim_ids[1]}::drying-after-week" not in refs
    assert not any(ref.startswith(f"{claim_ids[2]}::") for ref in refs)
    dispositions = {
        row["evidence_id"]: row["disposition"]
        for row in verified["evidence_dispositions"]
    }
    assert dispositions[claim_ids[2]] == "unresolved"
    assert list(dispositions.values()).count("context_only") == 1
    assert verified["raw_response_manifest"] == compiled["raw_response_manifest"]
    assert verified["row_verification_manifest"]["decision_counts"] == {
        "accept": 1,
        "replace": 1,
        "unresolved": 1,
    }
    assert verified["row_verification_manifest"]["schema_version"] == (
        "semantic_evidence_row_verification_manifest_v2"
    )
    assert verified["row_verification_manifest"]["verification_method_version"] == (
        ROW_VERIFICATION_METHOD_VERSION
    )
    assert verified["row_verification_manifest"]["verification_method_sha256"] == (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT)
    )
    reconciliation, _ = prepare_reconciliation_stage(bundle, verified)
    assert reconciliation["batch_compilation_sha256"] == verified["compilation_sha256"]


def test_selective_row_repair_preserves_untouched_rows_and_invalidates_old_lineage() -> None:
    bundle, verified = _verified_policy_compilation(count=2)
    selected = verified["evidence_dispositions"][0]["evidence_id"]
    untouched = verified["evidence_dispositions"][1]["evidence_id"]
    repair_stage, _ = prepare_row_repair(
        bundle, verified, evidence_ids=[selected], max_prompt_bytes=20_000
    )
    replacement = deepcopy(repair_stage["verification_rows"][0]["proposed_result"])
    replacement["semantic_units"][0]["statement"] = (
        "The balm became noticeably drying after one week of use."
    )
    repaired = apply_row_repair(
        bundle,
        verified,
        repair_stage,
        _row_verification_responses(
            repair_stage,
            {
                selected: {
                    "decision": "replace",
                    "reason": "the qualified intensity was omitted",
                    "replacement": replacement,
                }
            },
        ),
    )

    def active_row(compilation: dict, evidence_id: str) -> tuple[dict, list[dict]]:
        disposition = next(
            row
            for row in compilation["evidence_dispositions"]
            if row["evidence_id"] == evidence_id
        )
        units = [
            row
            for row in compilation["semantic_units"]
            if row["evidence_id"] == evidence_id
        ]
        return disposition, units

    assert repaired["compilation_sha256"] != verified["compilation_sha256"]
    assert active_row(repaired, untouched) == active_row(verified, untouched)
    assert active_row(repaired, selected) != active_row(verified, selected)
    assert repaired["row_repair_manifest"]["selected_evidence_ids"] == [selected]
    prepare_reconciliation_stage(bundle, repaired)

    old_stage, _ = prepare_reconciliation_stage(bundle, verified)
    old_terminal = validate_reconciliation_stage(
        bundle,
        old_stage,
        _terminal_singleton_reconciliation_responses(old_stage),
    )
    with pytest.raises(SemanticIntegrationError, match="stale root batch compilation"):
        finalize_v3_view(bundle, repaired, old_terminal)


def _terminal_repair_migration_fixture(
    *,
    repaired_statement: str | None = None,
    repaired_conditions: list[str] | None = None,
    source_levels: int = 1,
) -> tuple[dict, dict, dict, dict]:
    bundle = build_bundle(_source_v7(count=2), max_prompt_bytes=20_000)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    verification_stage, _ = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    selected = verification_stage["verification_rows"][0]["evidence_id"]
    old_replacement = deepcopy(
        verification_stage["verification_rows"][0]["proposed_result"]
    )
    old_replacement["semantic_units"][0]["polarity"] = "negated"
    source_verified = apply_row_verification(
        bundle,
        compiled,
        verification_stage,
        _row_verification_responses(
            verification_stage,
            {
                selected: {
                    "decision": "replace",
                    "reason": "seed one historical polarity defect",
                    "replacement": old_replacement,
                }
            },
        ),
    )
    source_stage, _ = prepare_reconciliation_stage(
        bundle,
        source_verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
    )
    if source_levels == 1:
        source_terminal = validate_reconciliation_stage(
            bundle,
            source_stage,
            _terminal_singleton_reconciliation_responses(source_stage),
        )
    else:
        # One 1:1 normal level first, so the terminal level's children are
        # prior-level semantic nodes rather than leaves.
        level_one = validate_reconciliation_stage(
            bundle,
            source_stage,
            _singleton_reconciliation_responses(source_stage),
        )
        source_stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
        source_terminal = validate_reconciliation_stage(
            bundle,
            source_stage_two,
            _group_level_responses(source_stage_two, terminal=True),
        )
    repair_stage, _ = prepare_row_repair(
        bundle,
        source_verified,
        evidence_ids=[selected],
        max_prompt_bytes=20_000,
    )
    repaired_replacement = deepcopy(
        repair_stage["verification_rows"][0]["proposed_result"]
    )
    repaired_replacement["semantic_units"][0]["polarity"] = "affirmed"
    if repaired_statement is not None:
        repaired_replacement["semantic_units"][0]["statement"] = repaired_statement
    if repaired_conditions is not None:
        repaired_replacement["semantic_units"][0]["conditions"] = repaired_conditions
    repaired = apply_row_repair(
        bundle,
        source_verified,
        repair_stage,
        _row_verification_responses(
            repair_stage,
            {
                selected: {
                    "decision": "replace",
                    "reason": "repair the historical row",
                    "replacement": repaired_replacement,
                }
            },
        ),
    )
    return bundle, source_verified, repaired, source_terminal


def _migrate_terminal_fixture(
    bundle: dict,
    source_verified: dict,
    repaired: dict,
    source_terminal: dict,
) -> dict:
    return migrate_repaired_terminal_compilation(
        bundle,
        source_verified,
        repaired,
        source_terminal,
        raw_file_sha256s={
            "bundle": "1" * 64,
            "source_batch_compilation": "2" * 64,
            "repaired_batch_compilation": "3" * 64,
            "source_node_compilation": "4" * 64,
        },
    )


def _rehash_node_compilation(compilation: dict) -> None:
    compilation.pop("node_compilation_sha256", None)
    compilation["node_compilation_sha256"] = _canonical_hash(compilation)


def test_terminal_repair_migration_reuses_only_unchanged_leaves_and_coalesces() -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture()
    )
    with pytest.raises(SemanticIntegrationError, match="duplicate proposition identity"):
        finalize_v3_view(bundle, source_verified, source_terminal)
    with pytest.raises(SemanticIntegrationError, match="stale root batch compilation"):
        finalize_v3_view(bundle, repaired, source_terminal)

    migrated = _migrate_terminal_fixture(
        bundle, source_verified, repaired, source_terminal
    )
    repeated = _migrate_terminal_fixture(
        bundle, source_verified, repaired, source_terminal
    )
    assert migrated == repeated
    assert migrated["schema_version"] == TERMINAL_REPAIR_MIGRATION_COMPILATION_VERSION
    assert len(migrated["semantic_nodes"]) == 1
    manifest = migrated["terminal_repair_migration_manifest"]
    assert manifest["source_node_count"] == 2
    assert manifest["output_node_count"] == 1
    assert len(manifest["reused_source_semantic_node_refs"]) == 1
    assert len(manifest["invalidated_source_semantic_node_refs"]) == 1
    assert len(manifest["coalesced_node_groups"]) == 1
    assert manifest["provider_calls"] == 0
    assert manifest["relation_closure_claimed"] is False
    assert "input_node_compilation_sha256" not in migrated
    node = migrated["semantic_nodes"][0]
    assert node["polarity"] == "affirmed"
    assert len(node["leaf_relations"]) == 2
    view = finalize_v3_view(bundle, repaired, migrated)
    assert len(view["propositions"]) == 1
    assert view["propositions"][0]["claim_support"]["conflict_posture"] == (
        "not_checked"
    )
    assert len(view["propositions"][0]["claim_support"]["evidence_refs"]) == 2
    packet = project_evidence_packet(
        view,
        bundle,
        repaired,
        migrated,
        proposition_ids=[view["propositions"][0]["proposition_id"]],
    )
    assert packet["schema_version"] == EVIDENCE_PACKET_VERSION


@pytest.mark.parametrize(
    ("statement", "conditions", "error"),
    [
        (
            "The balm became severely drying after one week of use.",
            None,
            "non-polarity leaf changes",
        ),
        (None, ["after two weeks of use"], "non-polarity leaf changes"),
    ],
)
def test_terminal_repair_migration_rejects_same_id_semantic_changes(
    statement: str | None,
    conditions: list[str] | None,
    error: str,
) -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture(
            repaired_statement=statement,
            repaired_conditions=conditions,
        )
    )
    with pytest.raises(SemanticIntegrationError, match=error):
        _migrate_terminal_fixture(
            bundle, source_verified, repaired, source_terminal
        )


def test_terminal_repair_migration_rederivation_keeps_source_child_node_lineage() -> None:
    """A rederived node must keep its own children, not its flattened leaves."""
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture(source_levels=2)
    )
    assert source_terminal["level"] == 2
    migrated = _migrate_terminal_fixture(
        bundle, source_verified, repaired, source_terminal
    )
    manifest = migrated["terminal_repair_migration_manifest"]
    invalidated = set(manifest["invalidated_source_semantic_node_refs"])
    assert invalidated

    source_by_ref = {
        node["semantic_node_ref"]: node for node in source_terminal["semantic_nodes"]
    }
    expected_children = {
        relation["child_ref"]
        for ref in invalidated
        for relation in source_by_ref[ref]["child_relations"]
    }
    leaf_refs = set(manifest["terminal_leaf_semantic_unit_refs"]) | set(
        manifest["unmerged_semantic_unit_refs"]
    )
    # Above level 0 a child ref names a prior-level node, never a leaf unit.
    assert expected_children
    assert not expected_children & leaf_refs

    migrated_children = {
        relation["child_ref"]
        for node in migrated["semantic_nodes"]
        for relation in node["child_relations"]
    }
    assert expected_children <= migrated_children
    assert not migrated_children & leaf_refs


def test_terminal_repair_migration_rejects_relation_and_condition_conflicts() -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture()
    )
    migrated = _migrate_terminal_fixture(
        bundle, source_verified, repaired, source_terminal
    )
    first = deepcopy(migrated["semantic_nodes"][0])
    second = deepcopy(first)
    first["semantic_node_ref"] = "first"
    second["semantic_node_ref"] = "second"
    second["leaf_relations"][0]["relation"] = "counter"
    with pytest.raises(SemanticIntegrationError, match="leaf relation"):
        _terminal_repair_coalesce_group(
            [first, second],
            repaired_compilation_sha256=repaired["compilation_sha256"],
        )

    second = deepcopy(first)
    second["semantic_node_ref"] = "second"
    second["condition_lineage"][0]["conditions"] = ["different condition"]
    with pytest.raises(SemanticIntegrationError, match="condition-lineage conflict"):
        _terminal_repair_coalesce_group(
            [first, second],
            repaired_compilation_sha256=repaired["compilation_sha256"],
        )


def test_terminal_repair_migration_rejects_tampering_missing_and_stale_lineage() -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture()
    )
    tampered = deepcopy(source_terminal)
    tampered["semantic_nodes"][0]["bounded_meaning"] = "tampered"
    with pytest.raises(SemanticIntegrationError, match="stored node_compilation_sha256"):
        _migrate_terminal_fixture(bundle, source_verified, repaired, tampered)

    missing = deepcopy(source_terminal)
    missing["semantic_nodes"][0]["leaf_relations"] = []
    _rehash_node_compilation(missing)
    with pytest.raises(SemanticIntegrationError, match="lacks leaf lineage"):
        _migrate_terminal_fixture(bundle, source_verified, repaired, missing)

    stale = deepcopy(source_terminal)
    stale["batch_compilation_sha256"] = "0" * 64
    _rehash_node_compilation(stale)
    with pytest.raises(SemanticIntegrationError, match="source node lineage is stale"):
        _migrate_terminal_fixture(bundle, source_verified, repaired, stale)


def test_terminal_repair_migration_finalizer_rejects_seeded_wrong_causes_first() -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture()
    )
    migrated = _migrate_terminal_fixture(
        bundle, source_verified, repaired, source_terminal
    )

    wrong_polarity = deepcopy(migrated)
    wrong_polarity["semantic_nodes"][0]["polarity"] = "negated"
    _rehash_node_compilation(wrong_polarity)
    with pytest.raises(SemanticIntegrationError, match="current leaf polarity"):
        finalize_v3_view(bundle, repaired, wrong_polarity)

    changed_unmerged = deepcopy(migrated)
    changed_unmerged["unmerged_semantic_units"] = [
        {
            "semantic_unit_ref": migrated["semantic_nodes"][0]["leaf_relations"][0][
                "semantic_unit_ref"
            ],
            "reason": "forged membership",
        }
    ]
    _rehash_node_compilation(changed_unmerged)
    with pytest.raises(SemanticIntegrationError, match="both used and unmerged"):
        finalize_v3_view(bundle, repaired, changed_unmerged)

    closure_trapdoor = deepcopy(migrated)
    closure_trapdoor["relation_coverage"] = {"complete": True}
    _rehash_node_compilation(closure_trapdoor)
    with pytest.raises(SemanticIntegrationError, match="cannot carry relation-closure"):
        finalize_v3_view(bundle, repaired, closure_trapdoor)

    uncoalesced = deepcopy(migrated)
    uncoalesced["semantic_nodes"].append(deepcopy(uncoalesced["semantic_nodes"][0]))
    uncoalesced["semantic_nodes"][1]["semantic_node_ref"] = "duplicate-node"
    uncoalesced["output_node_count"] = 2
    uncoalesced["terminal_repair_migration_manifest"]["output_node_count"] = 2
    uncoalesced["terminal_repair_migration_manifest"]["source_node_count"] = 3
    uncoalesced["terminal_repair_migration_manifest"][
        "reused_source_semantic_node_refs"
    ].append("duplicate-source")
    uncoalesced["terminal_repair_migration_manifest"].pop("manifest_sha256")
    uncoalesced["terminal_repair_migration_manifest"]["manifest_sha256"] = (
        _canonical_hash(uncoalesced["terminal_repair_migration_manifest"])
    )
    _rehash_node_compilation(uncoalesced)
    with pytest.raises(SemanticIntegrationError, match="uncoalesced duplicate"):
        finalize_v3_view(bundle, repaired, uncoalesced)


def test_terminal_repair_migration_runner_hash_binds_raw_inputs_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    bundle, source_verified, repaired, source_terminal = (
        _terminal_repair_migration_fixture()
    )
    paths = {
        "bundle": tmp_path / "bundle.json",
        "source": tmp_path / "source-verified.json",
        "repaired": tmp_path / "repaired.json",
        "terminal": tmp_path / "source-terminal.json",
    }
    for name, value in (
        ("bundle", bundle),
        ("source", source_verified),
        ("repaired", repaired),
        ("terminal", source_terminal),
    ):
        paths[name].write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    compilation_out = tmp_path / "successor" / "node-compilation.json"
    manifest_out = tmp_path / "successor" / "manifest.json"
    result = migrate_repaired_terminal_run(
        bundle_path=paths["bundle"],
        source_batch_compilation_path=paths["source"],
        repaired_batch_compilation_path=paths["repaired"],
        source_node_compilation_path=paths["terminal"],
        compilation_out=compilation_out,
        manifest_out=manifest_out,
    )
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    assert result["status"] == "SEMANTIC_TERMINAL_REPAIR_MIGRATION_COMPLETE"
    assert result["model_api_calls"] == 0
    assert manifest["raw_file_sha256s"] == {
        "bundle": _digest(paths["bundle"].read_bytes()),
        "repaired_batch_compilation": _digest(paths["repaired"].read_bytes()),
        "source_batch_compilation": _digest(paths["source"].read_bytes()),
        "source_node_compilation": _digest(paths["terminal"].read_bytes()),
    }
    with pytest.raises(ValueError, match="refusing to overwrite"):
        migrate_repaired_terminal_run(
            bundle_path=paths["bundle"],
            source_batch_compilation_path=paths["source"],
            repaired_batch_compilation_path=paths["repaired"],
            source_node_compilation_path=paths["terminal"],
            compilation_out=compilation_out,
            manifest_out=manifest_out,
        )


def test_row_verification_v9_installs_general_completeness_and_context_boundaries() -> None:
    normalized = " ".join(ROW_VERIFICATION_METHOD_TEXT.split())
    assert ROW_VERIFICATION_METHOD_TEXT.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V9"
    )
    assert "ROW VERIFICATION METHOD V3" not in ROW_VERIFICATION_METHOD_TEXT
    assert "ROW VERIFICATION METHOD V4" not in ROW_VERIFICATION_METHOD_TEXT
    assert "ROW VERIFICATION METHOD V5" not in ROW_VERIFICATION_METHOD_TEXT
    assert "ROW VERIFICATION METHOD V6" not in ROW_VERIFICATION_METHOD_TEXT
    assert "ROW VERIFICATION METHOD V7" not in ROW_VERIFICATION_METHOD_TEXT
    assert "ROW VERIFICATION METHOD V8" not in ROW_VERIFICATION_METHOD_TEXT
    assert ROW_VERIFICATION_METHOD_TEXT_V4.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V4"
    )
    assert ROW_VERIFICATION_METHOD_TEXT_V5.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V5"
    )
    assert ROW_VERIFICATION_METHOD_TEXT_V6.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V6"
    )
    assert ROW_VERIFICATION_METHOD_TEXT_V7.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V7"
    )
    assert ROW_VERIFICATION_METHOD_TEXT_V8.startswith(
        "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V8"
    )
    assert _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V6) == (
        "fdf78f437e99275719bec13c32379ed83717f7551f128975d0017760e0e77f0f"
    )
    assert _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V7) == (
        "a2387611eb8dfd89a0266a1e9b9ab3c4ffe1bf1466fe7e5d2b40c92005bc361c"
    )
    for principle in (
        "smallest complete set of standalone meanings",
        "direct answers, evaluations, results, comparisons, reasons, contrasts",
        "explicitly withdraws or corrects it",
        "Later context may narrow but does not cancel or replace",
        "Shared product, axis, or topic does not make one unit cover another",
        "Map each meaning to the proposed units before field checking",
        "source explicitly scopes that result to the attribute",
        "Conjunction, proximity, or shared body area is not enough",
        "Split a conjoined attribute phrase and keep only the part whose baseline"
        " that result reports",
        "If uncertain, leave the result unconditioned",
        "If a customer attribute is not retained as a result's condition, omit it"
        " from that result's statement too",
        "repurchase of a named shade, or of an all/every-shade collection, carries"
        " shade_and_color_fit",
        "sale timing or price is expressly a condition of an intended or hypothetical"
        " purchase, it also carries value_and_quantity",
        "Drying, becoming drier, or losing moisture supports"
        " hydration_and_moisture",
        "severity of drying alone does not turn moisture loss into a reaction",
        "A unit solely about an adjacent or comparator product is not a"
        " target-product unit",
        "Preserve the proposed row by default",
        "Replacement is correction, not fresh regeneration",
        "restore every supported meaning, axis, product binding, condition,"
        " posture, and direction",
        "every field is supported by the source or supplied context",
        "source-to-unit completeness pass",
        "every clause and every explicit relation between clauses",
        "same dimension and direction for both sides",
        "adjacency alone cannot create the relation",
        "supported adjacent-product meaning under its own subject",
        "Every supported independently usable meaning maps to exactly one unit",
        "directly relevant baseline for that result",
        "explicitly identifies the bound product as causing, worsening, changing,"
        " or eliciting that response",
        "vague product-category wording",
        "ambiguous antecedent remains context",
        "Local ambiguity does not erase unambiguous meanings elsewhere in the row",
        "Use unresolved only when no safe complete row exists",
        "uncertain variant referent only to its verified shared product",
        "ambiguous echo as axis-free, detail-free personal agreement",
        "Preserve an explicit overall evaluation separately from attribute facts",
        "Resolve pronouns, omitted subjects, and evaluation scope from the whole leaf",
        "not from the nearest named option alone",
        "Preserve explicit ownership or experience as its own meaning",
        "Earlier extraction examples identify separate atoms; they do not decide",
        "susceptibility to irritation or reaction does not by itself establish a",
        "hydration or moisture baseline",
        "Explicit loss, absorption, or waste of usable product supports",
        "value_and_quantity even when it occurs through a tool or texture",
    ):
        assert principle in normalized
    normalized_v4 = " ".join(ROW_VERIFICATION_METHOD_TEXT_V4.split())
    normalized_v7 = " ".join(ROW_VERIFICATION_METHOD_TEXT_V7.split())
    assert "Sensitivity alone is not a moisture baseline" in normalized_v4
    assert "product-linked sensitivity is reaction or tolerance context" in normalized_v4
    assert "SEMANTIC EVIDENCE ROW VERIFICATION METHOD V7" in normalized_v7
    assert "susceptibility to irritation or reaction" not in normalized_v7
    assert "waste of usable product supports" not in normalized_v7
    assert "merely buying, owning, or repurchasing that shade may not" not in normalized
    for case_phrase in (
        "Summer Fridays",
        "Vanilla Beige",
        "worth $24",
        "lip balm",
        "lip gloss",
        "Lanolips",
        "sensitive lips",
        "Fenty",
        "YSL",
        "Hourglass",
    ):
        assert case_phrase not in ROW_VERIFICATION_METHOD_TEXT


def test_row_verification_is_deterministic_and_fails_on_missing_decision() -> None:
    bundle = _bundle_v5(count=3)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=3)
    )
    stage_one, prompts_one = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    stage_two, prompts_two = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    assert stage_one == stage_two
    assert prompts_one == prompts_two

    complete = _row_verification_responses(stage_one)
    assert apply_row_verification(bundle, compiled, stage_one, complete) == (
        apply_row_verification(bundle, compiled, stage_two, complete)
    )
    missing = deepcopy(complete)
    missing[0]["decisions"].pop()
    with pytest.raises(
        SemanticIntegrationError,
        match="does not decide every row exactly once",
    ):
        apply_row_verification(bundle, compiled, stage_one, missing)


def _identity_bound_row_stage(phase: str) -> tuple[dict, dict, dict, list[dict]]:
    source = _source_v10(count=4)
    source["semantic_method_version"] = semantic_module.METHOD_VERSION_V12
    bundle = build_bundle(source, max_prompt_bytes=60_000)
    raw = _keyed_responses(bundle)
    for response in raw:
        for evidence_id in response["decisions_by_evidence_id"]:
            row = _claim_row(evidence_id)
            row["semantic_units"][0]["subject_product_ids"] = [
                bundle["product_identity_catalog"]["products"][0]["stable_product_id"]
            ]
            row.pop("evidence_id")
            response["decisions_by_evidence_id"][evidence_id] = row
    compiled = validate_batch_responses(bundle, raw)
    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=60_000)
    if phase == "repair":
        compiled = apply_row_verification(
            bundle, compiled, stage, _row_verification_responses(stage)
        )
        stage, _ = prepare_row_repair(
            bundle, compiled,
            evidence_ids=[row["evidence_id"] for row in compiled["evidence_dispositions"][:3]],
            max_prompt_bytes=60_000,
        )
    assert len(stage["batches"]) == 1
    ids = stage["batches"][0]["evidence_ids"]
    replacement = deepcopy(next(row["proposed_result"] for row in stage["verification_rows"]
                                if row["evidence_id"] == ids[1]))
    replacement["semantic_units"][0]["statement"] = "The balm became noticeably drying after one week of use."
    responses = _row_verification_responses(stage, {
        ids[1]: {"decision": "replace", "reason": "restore the qualified intensity", "replacement": replacement},
        ids[2]: {"decision": "unresolved", "reason": "ambiguous source meaning", "replacement": None},
    })
    return bundle, compiled, stage, responses


@pytest.mark.parametrize("phase", ["verification", "repair"])
def test_row_decisions_bind_identity_not_list_position(phase: str) -> None:
    bundle, compiled, stage, responses = _identity_bound_row_stage(phase)
    apply = apply_row_verification if phase == "verification" else apply_row_repair
    expected = apply(bundle, compiled, stage, responses)
    permuted = deepcopy(responses)
    permuted[0]["decisions"].reverse()
    observed = apply(bundle, compiled, stage, permuted)
    assert observed["semantic_units"] == expected["semantic_units"]
    assert observed["evidence_dispositions"] == expected["evidence_dispositions"]
    assert observed["raw_response_manifest"] == compiled["raw_response_manifest"]
    # Raw answer order remains provenance, not a rewritten answer or row owner.
    assert observed["compilation_sha256"] != expected["compilation_sha256"]
    if phase == "verification":
        validate_row_verified_compilation(bundle, compiled, observed)
    reconciliation, _ = prepare_reconciliation_stage(bundle, observed)
    assert reconciliation["batch_compilation_sha256"] == observed["compilation_sha256"]
    ids = stage["batches"][0]["evidence_ids"]
    assert next(row for row in observed["semantic_units"] if row["evidence_id"] == ids[1])["statement"] == (
        "The balm became noticeably drying after one week of use."
    )
    assert not any(row["evidence_id"] == ids[2] for row in observed["semantic_units"])


@pytest.mark.parametrize("phase", ["verification", "repair"])
@pytest.mark.parametrize("violation", ["missing", "duplicate", "foreign", "replacement_identity"])
def test_unordered_row_decisions_still_reject_wrong_identity(phase: str, violation: str) -> None:
    bundle, compiled, stage, responses = _identity_bound_row_stage(phase)
    apply = apply_row_verification if phase == "verification" else apply_row_repair
    rows = responses[0]["decisions"]
    if violation == "missing":
        rows.pop()
        message = "does not decide every row exactly once"
    elif violation == "duplicate":
        rows[-1] = deepcopy(rows[0])
        message = f"invalid row {phase} decision"
    elif violation == "foreign":
        rows[0]["evidence_id"] = "foreign-evidence-id"
        message = f"invalid row {phase} decision"
    else:
        rows[1]["replacement"]["evidence_id"] = rows[0]["evidence_id"]
        message = "changes (evidence )?identity"
    # Stage and source hashes stay correct: the named identity boundary must fail.
    rows.reverse()
    with pytest.raises(SemanticIntegrationError, match=message):
        apply(bundle, compiled, stage, responses)


def _keyed_row_review_response(response: dict) -> dict:
    return {
        "schema_version": semantic_module.ROW_VERIFICATION_KEYED_RESPONSE_VERSION,
        "stage_sha256": response["stage_sha256"], "batch_id": response["batch_id"],
        "decisions_by_evidence_id": {
            row["evidence_id"]: {key: value for key, value in row.items() if key != "evidence_id"}
            for row in response["decisions"]
        },
    }


@pytest.mark.parametrize("phase", ["verification", "repair"])
def test_keyed_row_review_preserves_stage_replay_and_semantic_consumer(phase: str) -> None:
    bundle, compiled, stage, responses = _identity_bound_row_stage(phase)
    prepare = prepare_row_verification if phase == "verification" else prepare_row_repair
    apply = apply_row_verification if phase == "verification" else apply_row_repair
    kwargs = {"evidence_ids": stage["selected_evidence_ids"]} if phase == "repair" else {}
    current_stage, prompts = prepare(bundle, compiled, max_prompt_bytes=60_000, **kwargs)
    replay_stage, replay = prepare(bundle, compiled, max_prompt_bytes=60_000,
        response_version=semantic_module.ROW_VERIFICATION_RESPONSE_VERSION, **kwargs)
    assert current_stage == replay_stage == stage
    for current, historical in zip(prompts, replay, strict=True):
        assert "response_schema" not in historical
        rows = [row for row in stage["verification_rows"] if row["evidence_id"] in historical["evidence_ids"]]
        assert historical["prompt"] == semantic_module._render_row_verification_prompt(
            bundle, stage_sha256=stage["stage_sha256"], batch_id=historical["batch_id"], rows=rows)
        assert current["prompt_utf8_bytes"] <= historical["prompt_utf8_bytes"]
        schema = current["response_schema"]
        keyed = schema["properties"]["decisions_by_evidence_id"]
        assert keyed["required"] == current["evidence_ids"]
        assert set(keyed["properties"]) == set(current["evidence_ids"])
        assert keyed["additionalProperties"] is False
        for ref, value in keyed["properties"].items():
            replacement = value["properties"]["replacement"]["anyOf"][1]
            assert replacement["properties"]["evidence_id"] == {"type": "string", "const": ref}
            assert "evidence_id" in replacement["required"]
    original = deepcopy(responses)
    keyed_responses = [_keyed_row_review_response(row) for row in responses]
    observed = apply(bundle, compiled, stage, keyed_responses)
    expected = apply(bundle, compiled, stage, responses)
    assert observed["semantic_units"] == expected["semantic_units"]
    assert observed["evidence_dispositions"] == expected["evidence_dispositions"]
    assert observed["compilation_sha256"] != expected["compilation_sha256"]
    assert responses == original
    reconciliation, _ = prepare_reconciliation_stage(bundle, observed)
    assert reconciliation["batch_compilation_sha256"] == observed["compilation_sha256"]


@pytest.mark.parametrize("phase", ["verification", "repair"])
@pytest.mark.parametrize("violation", ["missing", "foreign", "misbound", "body_identity", "extra_envelope"])
def test_keyed_row_review_rejects_wrong_cause_at_identity_boundary(phase: str, violation: str) -> None:
    bundle, compiled, stage, responses = _identity_bound_row_stage(phase)
    keyed = _keyed_row_review_response(responses[0])
    values = keyed["decisions_by_evidence_id"]
    ids = list(values)
    message = "keyed response must decide every assigned row exactly once"
    if violation == "missing":
        values.pop(ids[0])
    elif violation == "foreign":
        values["foreign-id"] = values.pop(ids[0])
    elif violation == "misbound":
        values[ids[1]]["replacement"]["evidence_id"] = ids[0]
        message = "changes (evidence )?identity"
    elif violation == "body_identity":
        values[ids[0]]["evidence_id"] = ids[1]
        message = "keyed decision shape"
    else:
        keyed["decisions"] = responses[0]["decisions"]
        message = "keyed response shape"
    apply = apply_row_verification if phase == "verification" else apply_row_repair
    # Valid stage/hash/batch reach the intended transport/ownership boundary.
    with pytest.raises(SemanticIntegrationError, match=message):
        apply(bundle, compiled, stage, [keyed])


@pytest.mark.parametrize("phase", ["verification", "repair"])
def test_current_row_review_runner_persists_required_answer_schema(tmp_path: Path, phase: str) -> None:
    bundle, compiled, stage, _ = _identity_bound_row_stage(phase)
    bundle_path, compiled_path = tmp_path / "bundle.json", tmp_path / "compiled.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    compiled_path.write_text(json.dumps(compiled), encoding="utf-8")
    kwargs = dict(bundle_path=bundle_path, stage_out=tmp_path / "stage.json",
        prompt_dir=tmp_path / "prompts", max_prompt_bytes=60_000)
    if phase == "verification":
        prepare_row_verification_run(compiled_path=compiled_path, **kwargs)
        _, expected = prepare_row_verification(bundle, compiled, max_prompt_bytes=60_000)
    else:
        prepare_row_repair_run(verified_path=compiled_path, evidence_ids=stage["selected_evidence_ids"], **kwargs)
        _, expected = prepare_row_repair(bundle, compiled, evidence_ids=stage["selected_evidence_ids"], max_prompt_bytes=60_000)
    assert json.loads((tmp_path / "stage.json").read_text()) == stage
    for row in expected:
        assert json.loads((tmp_path / "prompts" / f"{row['batch_id']}.schema.json").read_text()) == row["response_schema"]
        assert (tmp_path / "prompts" / f"{row['batch_id']}.md").read_bytes() == (row["prompt"] + "\n").encode("utf-8")


def test_row_review_mixes_saved_v1_and_current_v2_without_rewriting_answers() -> None:
    source = _source_v10(count=4)
    source["semantic_method_version"] = semantic_module.METHOD_VERSION_V12
    bundle = build_bundle(source, max_prompt_bytes=60_000, max_evidence_per_work_unit=2)
    raw = _keyed_responses(bundle)
    for response in raw:
        for ref in response["decisions_by_evidence_id"]:
            row = _claim_row(ref)
            row["semantic_units"][0]["subject_product_ids"] = [
                bundle["product_identity_catalog"]["products"][0]["stable_product_id"]]
            row.pop("evidence_id")
            response["decisions_by_evidence_id"][ref] = row
    compiled = validate_batch_responses(bundle, raw)
    stage, _ = prepare_row_verification(bundle, compiled)
    assert len(stage["batches"]) == 2
    historical = _row_verification_responses(stage)
    mixed = [deepcopy(historical[0]), _keyed_row_review_response(historical[1])]
    raw_pins = [semantic_module._sha256(row) for row in mixed]
    result = apply_row_verification(bundle, compiled, stage, mixed)
    expected = apply_row_verification(bundle, compiled, stage, historical)
    assert result["semantic_units"] == expected["semantic_units"]
    assert result["evidence_dispositions"] == expected["evidence_dispositions"]
    assert raw_pins == [semantic_module._sha256(row) for row in mixed]
    assert result["compilation_sha256"] != expected["compilation_sha256"]
    validate_row_verified_compilation(bundle, compiled, result)


def test_row_verification_rejects_a_patched_accept_and_invalid_replacement() -> None:
    bundle = _bundle_v5(count=1)
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=20_000)
    evidence_id = stage["verification_rows"][0]["evidence_id"]

    patched_accept = _row_verification_responses(stage)
    patched_accept[0]["decisions"][0]["replacement"] = _claim_row(evidence_id)
    with pytest.raises(
        SemanticIntegrationError, match="accept decision.*must not carry"
    ):
        apply_row_verification(bundle, compiled, stage, patched_accept)

    invalid = _claim_row(evidence_id)
    invalid["semantic_units"][0]["axis_ids"] = ["not-a-real-axis"]
    invalid_response = _row_verification_responses(
        stage,
        {
            evidence_id: {
                "decision": "replace",
                "reason": "replacement exercises the shared validator",
                "replacement": invalid,
            }
        },
    )
    with pytest.raises(SemanticIntegrationError, match="cites unknown axis"):
        apply_row_verification(bundle, compiled, stage, invalid_response)


def test_row_verification_manifest_binds_the_active_compilation_content() -> None:
    bundle = _bundle_v5(count=2)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=20_000)
    rejected_id = stage["verification_rows"][-1]["evidence_id"]
    verified = apply_row_verification(
        bundle,
        compiled,
        stage,
        _row_verification_responses(
            stage,
            {
                rejected_id: {
                    "decision": "unresolved",
                    "reason": "the source cannot support one safe complete result",
                    "replacement": None,
                }
            },
        ),
    )

    # A real verifier rejected one row, but the original compilation still
    # carries it. Stapling the honest manifest onto that original compilation
    # must not turn the rejected row back into active evidence.
    forged = deepcopy(compiled)
    forged["row_verification_manifest"] = deepcopy(
        verified["row_verification_manifest"]
    )
    forged["compilation_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "compilation_sha256"}
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the active row content",
    ):
        prepare_reconciliation_stage(bundle, forged)

    malformed = deepcopy(verified)
    del malformed["raw_response_manifest"]
    malformed["compilation_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in malformed.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="lacks active compilation content",
    ):
        prepare_reconciliation_stage(bundle, malformed)

    for field, value in (
        ("verification_method_version", "semantic_evidence_row_verification_method_v1"),
        ("verification_method_sha256", "0" * 64),
    ):
        wrong_method = deepcopy(verified)
        wrong_method["row_verification_manifest"][field] = value
        wrong_method["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
            {
                key: item
                for key, item in wrong_method["row_verification_manifest"].items()
                if key != "manifest_sha256"
            }
        )
        wrong_method["compilation_sha256"] = _canonical_hash(
            {
                key: item
                for key, item in wrong_method.items()
                if key != "compilation_sha256"
            }
        )
        with pytest.raises(
            SemanticIntegrationError,
            match="does not bind the current verification method",
        ):
            prepare_reconciliation_stage(bundle, wrong_method)

    historical_v3 = deepcopy(verified)
    historical_v3["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V3
    )
    historical_v3["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V3)
    )
    historical_v3["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v3["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v3["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v3.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v3)

    historical_v4 = deepcopy(verified)
    historical_v4["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V4
    )
    historical_v4["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V4)
    )
    historical_v4["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v4["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v4["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v4.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v4)

    historical_v5 = deepcopy(verified)
    historical_v5["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V5
    )
    historical_v5["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V5)
    )
    historical_v5["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v5["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v5["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v5.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v5)

    historical_v6 = deepcopy(verified)
    historical_v6["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V6
    )
    historical_v6["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V6)
    )
    historical_v6["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v6["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v6["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v6.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v6)

    historical_v7 = deepcopy(verified)
    historical_v7["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V7
    )
    historical_v7["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V7)
    )
    historical_v7["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v7["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v7["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v7.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v7)

    historical_v8 = deepcopy(verified)
    historical_v8["row_verification_manifest"]["verification_method_version"] = (
        ROW_VERIFICATION_METHOD_VERSION_V8
    )
    historical_v8["row_verification_manifest"]["verification_method_sha256"] = (
        _canonical_hash(ROW_VERIFICATION_METHOD_TEXT_V8)
    )
    historical_v8["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v8["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    historical_v8["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in historical_v8.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="does not bind the current verification method",
    ):
        prepare_reconciliation_stage(bundle, historical_v8)

    legacy_manifest = deepcopy(verified)
    legacy_manifest["row_verification_manifest"]["schema_version"] = (
        "semantic_evidence_row_verification_manifest_v1"
    )
    del legacy_manifest["row_verification_manifest"]["verification_method_version"]
    del legacy_manifest["row_verification_manifest"]["verification_method_sha256"]
    legacy_manifest["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in legacy_manifest["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    legacy_manifest["compilation_sha256"] = _canonical_hash(
        {
            key: item
            for key, item in legacy_manifest.items()
            if key != "compilation_sha256"
        }
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="invalid row verification manifest shape",
    ):
        prepare_reconciliation_stage(bundle, legacy_manifest)


def test_verified_calibration_compilation_binds_its_exact_primary_input() -> None:
    bundle = build_bundle(_source_v7(count=2), max_prompt_bytes=12_000)
    primary = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    stage, _ = prepare_row_verification(bundle, primary, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, primary, stage, _row_verification_responses(stage)
    )
    validate_row_verified_compilation(bundle, primary, verified)

    forged = deepcopy(verified)
    forged["row_verification_manifest"]["input_compilation_sha256"] = "0" * 64
    forged["row_verification_manifest"]["manifest_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in forged["row_verification_manifest"].items()
            if key != "manifest_sha256"
        }
    )
    forged["compilation_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "compilation_sha256"}
    )
    with pytest.raises(
        SemanticIntegrationError,
        match="cites another input compilation",
    ):
        validate_row_verified_compilation(bundle, primary, forged)


def test_unverified_compilation_supplied_as_verified_stays_a_visible_failure() -> None:
    # A historical-method slice tolerates a compilation with no row
    # verification manifest, so the v7 gate does not fire. Supplying such a
    # compilation as the verified one must still fail as a modeled semantic
    # error the calibration report can carry.
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    assert bundle["method_version"] == "semantic_evidence_integration_method_v5"
    responses = _v5_responses(bundle)
    primary = validate_batch_responses(bundle, responses)
    assert "row_verification_manifest" not in primary

    with pytest.raises(
        SemanticIntegrationError,
        match="lacks a row verification manifest",
    ):
        validate_row_verified_compilation(bundle, primary, deepcopy(primary))

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, primary["compilation_sha256"]),
        None,
        None,
        {"semantic-core": primary},
        full_source=source,
    )
    assert any(
        row["code"] == "STRUCTURAL_VALIDATION_FAILED"
        and "lacks a row verification manifest" in row["detail"]
        for row in report["hard_failures"]
    )


def test_cold_repeat_blocks_a_verified_primary_against_an_unverified_repeat() -> None:
    # A method-v7 repeat without its own verified compilation must not be
    # compared against the verified primary.
    source = materialize_source_v3(_source_v7(count=2))
    spec = _calibration_spec(source)
    spec["cold_repeat_case_ids"] = ["drying-after-week"]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 12_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    cold_bundle = prepared["cold_repeat"]["bundle"]
    primary_responses = _v5_responses(bundle)
    repeat_responses = _v5_responses(cold_bundle)
    primary = validate_batch_responses(bundle, primary_responses)
    repeat = validate_batch_responses(cold_bundle, repeat_responses)
    stage, _ = prepare_row_verification(bundle, primary, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, primary, stage, _row_verification_responses(stage)
    )
    assert "row_verification_manifest" not in repeat

    adjudication = _calibration_adjudication(spec, verified["compilation_sha256"])
    adjudication["cold_repeat_adjudications"] = [
        {
            "case_id": "drying-after-week",
            "primary_compilation_sha256": verified["compilation_sha256"],
            "repeat_compilation_sha256": repeat["compilation_sha256"],
            "outcome": "consistent",
        }
    ]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": primary_responses},
        adjudication,
        {"cold-repeat": repeat_responses},
        None,
        {"semantic-core": verified},
        full_source=source,
    )
    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        row["code"] == "COLD_STRUCTURAL_VALIDATION_FAILED"
        and "requires a row-verified compilation" in row["detail"]
        for row in report["hard_failures"]
    )
    assert any(
        row["code"] == "COLD_REPEAT_VERIFICATION_LINEAGE_MISMATCH"
        and row["case_id"] == "drying-after-week"
        for row in report["blockers"]
    )
    assert report["cold_repeat_results"] == [
        {"case_id": "drying-after-week", "outcome": "missing"}
    ]


def test_cold_repeat_uses_its_own_row_verified_compilation() -> None:
    source = materialize_source_v3(_source_v7(count=2))
    spec = _calibration_spec(source)
    spec["cold_repeat_case_ids"] = ["drying-after-week"]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 12_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    cold_bundle = prepared["cold_repeat"]["bundle"]
    primary_responses = _v5_responses(bundle)
    repeat_responses = _v5_responses(cold_bundle)
    primary = validate_batch_responses(bundle, primary_responses)
    repeat = validate_batch_responses(cold_bundle, repeat_responses)
    primary_stage, _ = prepare_row_verification(
        bundle, primary, max_prompt_bytes=20_000
    )
    repeat_stage, _ = prepare_row_verification(
        cold_bundle, repeat, max_prompt_bytes=20_000
    )
    verified_primary = apply_row_verification(
        bundle,
        primary,
        primary_stage,
        _row_verification_responses(primary_stage),
    )
    verified_repeat = apply_row_verification(
        cold_bundle,
        repeat,
        repeat_stage,
        _row_verification_responses(repeat_stage),
    )

    adjudication = _calibration_adjudication(
        spec, verified_primary["compilation_sha256"]
    )
    adjudication["cold_repeat_adjudications"] = [
        {
            "case_id": "drying-after-week",
            "primary_compilation_sha256": verified_primary["compilation_sha256"],
            "repeat_compilation_sha256": verified_repeat["compilation_sha256"],
            "outcome": "consistent",
        }
    ]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": primary_responses},
        adjudication,
        {"cold-repeat": repeat_responses},
        None,
        {
            "semantic-core": verified_primary,
            "cold-repeat": verified_repeat,
        },
        full_source=source,
    )
    assert not any(
        row["code"] == "COLD_REPEAT_VERIFICATION_LINEAGE_MISMATCH"
        for row in report["blockers"]
    )
    assert report["cold_repeat_results"] == [
        {"case_id": "drying-after-week", "outcome": "consistent"}
    ]


def test_row_verification_runner_writes_stage_prompts_and_verified_compilation(
    tmp_path: Path,
) -> None:
    bundle = _bundle_v5(count=2)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    bundle_path = tmp_path / "bundle.json"
    compiled_path = tmp_path / "compiled.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    compiled_path.write_text(json.dumps(compiled), encoding="utf-8")
    stage_path = tmp_path / "verification-stage.json"
    prompt_dir = tmp_path / "verification-prompts"
    prepared = prepare_row_verification_run(
        bundle_path=bundle_path,
        compiled_path=compiled_path,
        stage_out=stage_path,
        prompt_dir=prompt_dir,
        max_prompt_bytes=20_000,
    )
    assert prepared["status"] == "SEMANTIC_ROW_VERIFICATION_REQUIRED"
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    responses = _row_verification_responses(stage)
    response_paths = []
    for row in responses:
        path = tmp_path / f"{row['batch_id']}.json"
        path.write_text(json.dumps(row), encoding="utf-8")
        response_paths.append(path)
    verified_path = tmp_path / "verified.json"
    submitted = submit_row_verification_run(
        bundle_path=bundle_path,
        compiled_path=compiled_path,
        stage_path=stage_path,
        response_paths=response_paths,
        verified_out=verified_path,
    )
    assert submitted["status"] == "SEMANTIC_ROW_VERIFICATION_APPLIED"
    assert verified_path.exists()


def test_method_v7_requires_verification_without_rewriting_v6_extraction_rules() -> None:
    v6_bundle = build_bundle(_source_v6(count=2), max_prompt_bytes=12_000)
    v7_bundle = build_bundle(_source_v7(count=2), max_prompt_bytes=12_000)
    assert METHOD_TEXT_V7.replace("METHOD V7", "METHOD V6", 1) == METHOD_TEXT_V6
    assert [row["prompt_utf8_bytes"] for row in build_batch_prompts(v7_bundle)] == [
        row["prompt_utf8_bytes"] for row in build_batch_prompts(v6_bundle)
    ]

    v6_compiled = validate_batch_responses(v6_bundle, _v5_responses(v6_bundle))
    prepare_reconciliation_stage(v6_bundle, v6_compiled)

    v7_compiled = validate_batch_responses(v7_bundle, _v5_responses(v7_bundle))
    with pytest.raises(
        SemanticIntegrationError,
        match="method v7 requires row verification",
    ):
        prepare_reconciliation_stage(v7_bundle, v7_compiled)
    stage, _ = prepare_row_verification(
        v7_bundle, v7_compiled, max_prompt_bytes=20_000
    )
    verified = apply_row_verification(
        v7_bundle, v7_compiled, stage, _row_verification_responses(stage)
    )
    reconciliation, _ = prepare_reconciliation_stage(v7_bundle, verified)
    assert reconciliation["batch_compilation_sha256"] == verified["compilation_sha256"]

    level_one = validate_reconciliation_stage(
        v7_bundle,
        reconciliation,
        _group_level_responses(reconciliation, terminal=False),
    )
    level_two, _ = prepare_reconciliation_stage(v7_bundle, level_one)
    assert level_two["level"] == 2
    assert level_two["batch_compilation_sha256"] == verified["compilation_sha256"]


def _verified_policy_compilation(
    *, count: int, max_prompt_bytes: int = 12_000
) -> tuple[dict, dict]:
    bundle = build_bundle(
        _source_v7(count=count), max_prompt_bytes=max_prompt_bytes
    )
    compiled = validate_batch_responses(
        bundle,
        _v5_responses(bundle, detailed_per_batch=count),
    )
    verification_stage, _ = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=20_000
    )
    verified = apply_row_verification(
        bundle,
        compiled,
        verification_stage,
        _row_verification_responses(verification_stage),
    )
    return bundle, verified


def _singleton_reconciliation_responses(stage: dict) -> list[dict]:
    candidate_index = {row["candidate_ref"]: row for row in stage["candidates"]}
    responses = []
    for batch in stage["batches"]:
        nodes = []
        for index, child_ref in enumerate(batch["candidate_refs"], start=1):
            candidate = candidate_index[child_ref]
            nodes.append(
                {
                    # Keys deliberately repeat in other prompt batches. They
                    # are local response handles, not corpus-global identity.
                    "semantic_node_key": f"node-{index}",
                    "bounded_meaning": candidate["statement"],
                    "terminal_proposition": False,
                    "claim_kind": None,
                    "subject_product_ids": candidate["subject_product_ids"],
                    "comparator_product_ids": candidate["comparator_product_ids"],
                    "product_version_ids": candidate["product_version_ids"],
                    "axis_ids": candidate["axis_ids"],
                    "emerging_axis_labels": candidate["emerging_axis_labels"],
                    "conditions": candidate["conditions"],
                    "polarity": candidate["polarity"],
                    "uncertainty_posture": candidate["uncertainty_posture"],
                    "child_relations": [
                        {"child_ref": child_ref, "relation": "support"}
                    ],
                    "opposition_checked": None,
                    "causal_ceiling": None,
                }
            )
        responses.append(
            {
                "schema_version": RECONCILIATION_RESPONSE_VERSION_V2,
                "stage_sha256": stage["stage_sha256"],
                "batch_id": batch["batch_id"],
                "semantic_nodes": nodes,
                "unmerged_children": [],
                "emerging_axis_consolidations": [],
            }
        )
    return responses


def _terminal_singleton_reconciliation_responses(stage: dict) -> list[dict]:
    responses = _singleton_reconciliation_responses(stage)
    for response in responses:
        for node in response["semantic_nodes"]:
            node["terminal_proposition"] = True
            node["claim_kind"] = "customer_experience"
            node["opposition_checked"] = False
            node["causal_ceiling"] = "descriptive_only"
    return responses


def _relation_closure_responses(
    stage: dict,
    *,
    default_relation: str = "equivalent",
    relation_by_pair: dict[tuple[str, str], str] | None = None,
) -> list[dict]:
    relation_by_pair = relation_by_pair or {}
    responses = []
    for batch in stage["batches"]:
        left = batch["left_candidate_refs"]
        right = batch["right_candidate_refs"]
        pairs = (
            [
                tuple(sorted((left[index], left[other])))
                for index in range(len(left))
                for other in range(index + 1, len(left))
            ]
            if batch["same_block"]
            else [tuple(sorted((left_ref, right_ref))) for left_ref in left for right_ref in right]
        )
        responses.append(
            {
                "schema_version": RELATION_CLOSURE_RESPONSE_VERSION,
                "stage_sha256": stage["stage_sha256"],
                "batch_id": batch["batch_id"],
                "relations": [
                    {
                        "left_ref": pair[0],
                        "right_ref": pair[1],
                        "relation": relation_by_pair.get(pair, default_relation),
                        "reason": "the pair has the selected semantic relationship",
                    }
                    for pair in pairs
                ],
            }
        )
    return responses


def test_policy_v2_node_keys_are_local_to_each_prompt_batch() -> None:
    bundle, verified = _verified_policy_compilation(
        count=40, max_prompt_bytes=12_000
    )
    stage, _ = prepare_reconciliation_stage(
        bundle,
        verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
    )
    assert len(stage["batches"]) > 1

    compiled = validate_reconciliation_stage(
        bundle, stage, _singleton_reconciliation_responses(stage)
    )

    assert len(compiled["semantic_nodes"]) == len(stage["candidates"])
    assert len({row["semantic_node_ref"] for row in compiled["semantic_nodes"]}) == len(
        compiled["semantic_nodes"]
    )

    duplicate_within_one_batch = _singleton_reconciliation_responses(stage)
    first_with_two_nodes = next(
        row for row in duplicate_within_one_batch if len(row["semantic_nodes"]) > 1
    )
    first_with_two_nodes["semantic_nodes"][1]["semantic_node_key"] = (
        first_with_two_nodes["semantic_nodes"][0]["semantic_node_key"]
    )
    with pytest.raises(SemanticIntegrationError, match="duplicate or empty semantic node"):
        validate_reconciliation_stage(bundle, stage, duplicate_within_one_batch)


def test_policy_v2_normal_mode_cannot_drop_a_customer_singleton() -> None:
    bundle, verified = _verified_policy_compilation(count=1)
    stage, _ = prepare_reconciliation_stage(
        bundle,
        verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
    )
    assert stage["reconciliation_mode"] == "normal"
    response = _singleton_reconciliation_responses(stage)[0]
    response["semantic_nodes"] = []
    response["unmerged_children"] = [
        {
            "child_ref": stage["candidates"][0]["candidate_ref"],
            "reason": "Only one customer reported it.",
        }
    ]

    with pytest.raises(
        SemanticIntegrationError,
        match="normal reconciliation cannot unmerge customer finding",
    ):
        validate_reconciliation_stage(bundle, stage, [response])


def test_policy_v2_still_requires_the_verified_row_compilation() -> None:
    bundle = build_bundle(_source_v7(count=1), max_prompt_bytes=12_000)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=1)
    )

    with pytest.raises(
        SemanticIntegrationError,
        match="method v7 requires row verification",
    ):
        prepare_reconciliation_stage(
            bundle,
            compiled,
            reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
        )


def test_policy_v2_enters_convergence_and_enforces_source_row_support() -> None:
    bundle, verified = _verified_policy_compilation(count=2)
    stage_one, _ = prepare_reconciliation_stage(
        bundle,
        verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
    )
    level_one = validate_reconciliation_stage(
        bundle, stage_one, _singleton_reconciliation_responses(stage_one)
    )

    stage_two, prompts_two = prepare_reconciliation_stage(bundle, level_one)
    assert stage_two["reconciliation_mode"] == "convergence"
    assert all('"supporting_evidence_row_count": 1' in row["prompt"] for row in prompts_two)

    with pytest.raises(
        SemanticIntegrationError,
        match="lacks repeated source-row support",
    ):
        validate_reconciliation_stage(
            bundle, stage_two, _singleton_reconciliation_responses(stage_two)
        )

    level_two = validate_reconciliation_stage(
        bundle,
        stage_two,
        _group_level_responses(stage_two, terminal=False),
    )
    stage_three, prompts_three = prepare_reconciliation_stage(bundle, level_two)
    assert stage_three["reconciliation_mode"] == "convergence"
    assert '"supporting_evidence_row_count": 2' in prompts_three[0]["prompt"]

    response = _group_level_responses(stage_three, terminal=False)[0]
    response["semantic_nodes"] = []
    response["unmerged_children"] = [
        {
            "child_ref": stage_three["candidates"][0]["candidate_ref"],
            "reason": "Retained only as retrieval evidence.",
        }
    ]
    with pytest.raises(
        SemanticIntegrationError,
        match="convergence cannot unmerge repeated customer finding",
    ):
        validate_reconciliation_stage(bundle, stage_three, [response])


def test_policy_v2_multi_batch_fixed_point_is_terminal() -> None:
    compilation = {
        "input_batch_count": 2,
        "input_candidate_count": 2,
        "reconciliation_policy_version": RECONCILIATION_POLICY_VERSION_V2,
        "reconciliation_mode": "convergence",
        "semantic_nodes": [
            {"terminal_proposition": True},
            {"terminal_proposition": True},
        ],
    }

    assert is_terminal_reconciliation_compilation(compilation)

    changed = deepcopy(compilation)
    changed["input_candidate_count"] = 3
    assert not is_terminal_reconciliation_compilation(changed)

    normal = deepcopy(compilation)
    normal["reconciliation_mode"] = "normal"
    assert not is_terminal_reconciliation_compilation(normal)


def _relation_closure_fixture(
    *, count: int = 3, closure_prompt_bytes: int = 12_000
) -> tuple[dict, dict, dict, dict]:
    bundle, verified = _verified_policy_compilation(
        count=count, max_prompt_bytes=12_000
    )
    stage, _ = prepare_reconciliation_stage(
        bundle,
        verified,
        reconciliation_policy_version=RECONCILIATION_POLICY_VERSION_V2,
    )
    frontier = validate_reconciliation_stage(
        bundle, stage, _terminal_singleton_reconciliation_responses(stage)
    )
    closure_stage, _ = prepare_relation_closure_stage(
        bundle, frontier, max_prompt_bytes=closure_prompt_bytes
    )
    return bundle, verified, frontier, closure_stage


def test_relation_closure_merges_equivalent_nodes_across_prompt_partitions() -> None:
    bundle, verified, frontier, small_stage = _relation_closure_fixture(
        count=8, closure_prompt_bytes=4_500
    )
    frontier = deepcopy(frontier)
    frontier["semantic_nodes"][0]["bounded_meaning"] = (
        "After a week of use, the balm had become drying."
    )
    _rehash_node_compilation(frontier)
    small_stage, _ = prepare_relation_closure_stage(
        bundle, frontier, max_prompt_bytes=4_500
    )
    large_stage, _ = prepare_relation_closure_stage(
        bundle, frontier, max_prompt_bytes=30_000
    )
    assert len(small_stage["batches"]) > len(large_stage["batches"])

    small = validate_relation_closure_stage(
        bundle, small_stage, _relation_closure_responses(small_stage)
    )
    large = validate_relation_closure_stage(
        bundle, large_stage, _relation_closure_responses(large_stage)
    )

    assert small["schema_version"] == RELATION_CLOSURE_COMPILATION_VERSION
    assert len(small["semantic_nodes"]) == 1
    assert len(large["semantic_nodes"]) == 1
    assert small["semantic_nodes"] == large["semantic_nodes"]
    assert small["relation_coverage"]["complete"] is True
    small_view = finalize_relation_closed_view(bundle, verified, small)
    large_view = finalize_relation_closed_view(bundle, verified, large)
    assert small_view["propositions"] == large_view["propositions"]
    assert small_view["view_sha256"] == large_view["view_sha256"]


def test_relation_closure_unresolved_pair_blocks_finalization() -> None:
    bundle, verified, _, stage = _relation_closure_fixture(count=2)
    closed = validate_relation_closure_stage(
        bundle,
        stage,
        _relation_closure_responses(stage, default_relation="unresolved"),
    )

    assert closed["relation_coverage"]["complete"] is False
    assert closed["relation_coverage"]["unresolved_pair_count"] == 1
    assert not is_terminal_reconciliation_compilation(closed)
    with pytest.raises(SemanticIntegrationError, match="complete global relation closure"):
        finalize_relation_closed_view(bundle, verified, closed)


def _rehash_relation_closure_compilation(compilation: dict) -> dict:
    coverage = compilation["relation_coverage"]
    coverage["coverage_sha256"] = _canonical_hash(
        {key: value for key, value in coverage.items() if key != "coverage_sha256"}
    )
    return _rehash_node_compilation(compilation)


def test_relation_closure_cannot_take_generic_single_batch_terminal_shortcut() -> None:
    bundle, verified, _, stage = _relation_closure_fixture(count=2)
    closed = validate_relation_closure_stage(
        bundle, stage, _relation_closure_responses(stage)
    )
    forged = deepcopy(closed)
    forged["input_batch_count"] = 1
    forged["relation_coverage"]["decided_pair_count"] = 0
    forged["relation_coverage"]["complete"] = False
    _rehash_relation_closure_compilation(forged)

    assert not is_terminal_reconciliation_compilation(forged)
    with pytest.raises(SemanticIntegrationError, match="relation closure coverage"):
        finalize_relation_closed_view(bundle, verified, forged)


def test_schema_stripped_relation_closure_cannot_fall_back_to_generic_finalization() -> None:
    bundle, verified, frontier, _ = _relation_closure_fixture(count=3)
    frontier = deepcopy(frontier)
    for index, node in enumerate(frontier["semantic_nodes"], start=1):
        node["bounded_meaning"] = f"Distinct supported assertion {index}."
    _rehash_node_compilation(frontier)
    stage, _ = prepare_relation_closure_stage(bundle, frontier)
    closed = validate_relation_closure_stage(
        bundle,
        stage,
        _relation_closure_responses(stage, default_relation="opposed"),
    )
    assert {
        proposition["claim_support"]["conflict_posture"]
        for proposition in finalize_relation_closed_view(bundle, verified, closed)[
            "propositions"
        ]
    } == {"mixed"}
    forged = deepcopy(closed)
    forged.pop("schema_version")
    forged["input_batch_count"] = 1
    _rehash_node_compilation(forged)

    assert not is_terminal_reconciliation_compilation(forged)
    with pytest.raises(SemanticIntegrationError, match="invalid relation closure"):
        finalize_v3_view(bundle, verified, forged)


@pytest.mark.parametrize("membership_mutation", ["missing", "duplicate"])
def test_relation_closure_rejects_tampered_class_membership(
    membership_mutation: str,
) -> None:
    bundle, verified, _, stage = _relation_closure_fixture(count=3)
    closed = validate_relation_closure_stage(
        bundle, stage, _relation_closure_responses(stage)
    )
    forged = deepcopy(closed)
    child_relations = forged["semantic_nodes"][0]["child_relations"]
    if membership_mutation == "missing":
        child_relations.pop()
    else:
        child_relations.append(deepcopy(child_relations[0]))
    _rehash_relation_closure_compilation(forged)

    assert not is_terminal_reconciliation_compilation(forged)
    with pytest.raises(SemanticIntegrationError, match="candidate membership"):
        finalize_relation_closed_view(bundle, verified, forged)


@pytest.mark.parametrize("membership_mutation", ["substitute", "pad"])
def test_relation_closure_binds_pair_identity_to_exact_candidate_membership(
    membership_mutation: str,
) -> None:
    bundle, verified, _, stage = _relation_closure_fixture(count=3)
    closed = validate_relation_closure_stage(
        bundle, stage, _relation_closure_responses(stage)
    )
    forged = deepcopy(closed)
    child_relations = forged["semantic_nodes"][0]["child_relations"]
    if membership_mutation == "substitute":
        for index, relation in enumerate(child_relations):
            relation["child_ref"] = f"substituted-candidate-{index:04d}"
    else:
        child_relations.append(
            {"child_ref": "padded-candidate-0004", "relation": "support"}
        )
        coverage = forged["relation_coverage"]
        coverage["required_candidate_count"] = 4
        coverage["required_pair_count"] = 6
        coverage["decided_pair_count"] = 6
    _rehash_relation_closure_compilation(forged)

    assert not is_terminal_reconciliation_compilation(forged)
    with pytest.raises(SemanticIntegrationError, match="pair identity"):
        finalize_relation_closed_view(bundle, verified, forged)


def test_relation_closure_structural_cardinality_accepts_valid_happy_path() -> None:
    bundle, verified, _, stage = _relation_closure_fixture(count=3)
    closed = validate_relation_closure_stage(
        bundle, stage, _relation_closure_responses(stage)
    )

    assert is_terminal_reconciliation_compilation(closed)
    assert finalize_relation_closed_view(bundle, verified, closed)[
        "schema_version"
    ] == "semantic_evidence_integration_view_v3"


def test_single_candidate_relation_closure_cli_accepts_zero_pair_responses() -> None:
    args = _semantic_integration_parser().parse_args(
        [
            "submit-relation-closure",
            "--bundle",
            "bundle.json",
            "--stage",
            "stage.json",
            "--compilation-out",
            "closed.json",
        ]
    )

    assert args.response == []


def test_relation_closure_requires_complete_global_classification() -> None:
    bundle, _, _, stage = _relation_closure_fixture(count=2)
    responses = _relation_closure_responses(stage)
    responses[0]["relations"].pop()

    with pytest.raises(
        SemanticIntegrationError, match="does not decide every required pair"
    ):
        validate_relation_closure_stage(bundle, stage, responses)


def test_relation_closure_rejects_mixed_polarity_before_prompting() -> None:
    bundle, _, frontier, _ = _relation_closure_fixture(count=1)
    forged = deepcopy(frontier)
    forged["semantic_nodes"][0]["polarity"] = "mixed"
    _rehash_node_compilation(forged)

    with pytest.raises(SemanticIntegrationError, match="requires row repair"):
        prepare_relation_closure_stage(bundle, forged)


def test_relation_closure_derives_symmetric_opposition() -> None:
    bundle, verified, frontier, _ = _relation_closure_fixture(count=2)
    forged = deepcopy(frontier)
    forged["semantic_nodes"][1]["polarity"] = "negated"
    forged["semantic_nodes"][1]["bounded_meaning"] = (
        "The balm did not become drying after one week of use."
    )
    _rehash_node_compilation(forged)
    stage, _ = prepare_relation_closure_stage(bundle, forged)
    closed = validate_relation_closure_stage(
        bundle,
        stage,
        _relation_closure_responses(stage, default_relation="opposed"),
    )

    assert len(closed["semantic_nodes"]) == 2
    opposition = {
        node["semantic_node_ref"]: node["opposing_semantic_node_refs"]
        for node in closed["semantic_nodes"]
    }
    left, right = opposition
    assert opposition[left] == [right]
    assert opposition[right] == [left]
    view = finalize_relation_closed_view(bundle, verified, closed)
    propositions = {row["proposition_id"]: row for row in view["propositions"]}
    assert len(propositions) == 2
    for proposition_id, proposition in propositions.items():
        assert proposition["claim_support"]["conflict_posture"] == "mixed"
        assert proposition["claim_support"]["counterevidence_refs"]
        assert len(proposition["opposing_proposition_ids"]) == 1
        opposite = proposition["opposing_proposition_ids"][0]
        assert propositions[opposite]["opposing_proposition_ids"] == [proposition_id]


def test_relation_closure_and_selective_repair_runner_surfaces(tmp_path: Path) -> None:
    bundle, verified, frontier, _ = _relation_closure_fixture(count=2)
    bundle_path = tmp_path / "bundle.json"
    verified_path = tmp_path / "verified.json"
    frontier_path = tmp_path / "frontier.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    verified_path.write_text(json.dumps(verified), encoding="utf-8")
    frontier_path.write_text(json.dumps(frontier), encoding="utf-8")

    closure_stage_path = tmp_path / "closure-stage.json"
    closure_prompt_dir = tmp_path / "closure-prompts"
    prepared = prepare_relation_closure_run(
        bundle_path=bundle_path,
        node_compilation_path=frontier_path,
        stage_out=closure_stage_path,
        prompt_dir=closure_prompt_dir,
    )
    assert prepared["status"] == "SEMANTIC_RELATION_CLOSURE_REQUIRED"
    closure_stage = json.loads(closure_stage_path.read_text(encoding="utf-8"))
    closure_response_paths = []
    for response in _relation_closure_responses(closure_stage):
        path = tmp_path / f"{response['batch_id']}.json"
        path.write_text(json.dumps(response), encoding="utf-8")
        closure_response_paths.append(path)
    validation_receipt = tmp_path / "closure-validation.json"
    validated = validate_relation_closure_response_file(
        bundle_path=bundle_path,
        stage_path=closure_stage_path,
        response_path=closure_response_paths[0],
        receipt_out=validation_receipt,
    )
    assert validated["status"] == "SEMANTIC_RELATION_CLOSURE_RESPONSE_VALID"
    assert validation_receipt.exists()
    closure_out = tmp_path / "closure.json"
    submitted = submit_relation_closure_run(
        bundle_path=bundle_path,
        stage_path=closure_stage_path,
        response_paths=closure_response_paths,
        compilation_out=closure_out,
    )
    assert submitted["status"] == "SEMANTIC_FINALIZATION_READY"
    assert submitted["terminal"] is True

    unresolved_response_paths = []
    for response in _relation_closure_responses(
        closure_stage, default_relation="unresolved"
    ):
        path = tmp_path / f"unresolved-{response['batch_id']}.json"
        path.write_text(json.dumps(response), encoding="utf-8")
        unresolved_response_paths.append(path)
    unresolved = submit_relation_closure_run(
        bundle_path=bundle_path,
        stage_path=closure_stage_path,
        response_paths=unresolved_response_paths,
        compilation_out=tmp_path / "unresolved-closure.json",
    )
    assert unresolved["status"] == "SEMANTIC_RELATION_CLOSURE_REQUIRED"
    assert unresolved["terminal"] is False

    selected = verified["evidence_dispositions"][0]["evidence_id"]
    repair_stage_path = tmp_path / "repair-stage.json"
    repair_prompt_dir = tmp_path / "repair-prompts"
    repair_prepared = prepare_row_repair_run(
        bundle_path=bundle_path,
        verified_path=verified_path,
        evidence_ids=[selected],
        stage_out=repair_stage_path,
        prompt_dir=repair_prompt_dir,
        max_prompt_bytes=20_000,
    )
    assert repair_prepared["status"] == "SEMANTIC_ROW_REPAIR_REQUIRED"
    repair_stage = json.loads(repair_stage_path.read_text(encoding="utf-8"))
    repair_response = _row_verification_responses(repair_stage)[0]
    repair_response_path = tmp_path / "repair-response.json"
    repair_response_path.write_text(json.dumps(repair_response), encoding="utf-8")
    repaired_out = tmp_path / "repaired.json"
    repair_submitted = submit_row_repair_run(
        bundle_path=bundle_path,
        verified_path=verified_path,
        stage_path=repair_stage_path,
        response_paths=[repair_response_path],
        repaired_out=repaired_out,
    )
    assert repair_submitted["status"] == "SEMANTIC_ROW_REPAIR_APPLIED"


def _flat_reconciliation(bundle: dict, compiled: dict) -> dict:
    return {
        "schema_version": RECONCILIATION_RESPONSE_VERSION,
        "bundle_sha256": bundle["bundle_sha256"],
        "compilation_sha256": compiled["compilation_sha256"],
        "propositions": [
            {
                "proposition_key": f"prop-{index}",
                "bounded_proposition": unit["statement"],
                "claim_kind": "customer_experience",
                "subject_product_ids": unit["subject_product_ids"],
                "comparator_product_ids": unit["comparator_product_ids"],
                "axis_ids": unit["axis_ids"],
                "emerging_axis_labels": unit["emerging_axis_labels"],
                "conditions": unit["conditions"],
                "causal_ceiling": "descriptive_only",
                "opposition_checked": True,
                "relations": [
                    {
                        "semantic_unit_ref": unit["semantic_unit_ref"],
                        "relation": "support",
                    }
                ],
            }
            for index, unit in enumerate(compiled["semantic_units"])
        ],
        "unmerged_semantic_units": [],
    }


def test_method_v7_flat_finalization_also_refuses_an_unverified_compilation() -> None:
    bundle = build_bundle(_source_v7(count=2), max_prompt_bytes=12_000)
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))

    # The flat v1 reconciliation route is a second terminal finalization path.
    # It must not become the way an unverified v7 compilation reaches a view.
    with pytest.raises(
        SemanticIntegrationError,
        match="method v7 requires row verification",
    ):
        finalize_view(bundle, compiled, _flat_reconciliation(bundle, compiled))

    stage, _ = prepare_row_verification(bundle, compiled, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, compiled, stage, _row_verification_responses(stage)
    )
    view = finalize_view(bundle, verified, _flat_reconciliation(bundle, verified))
    assert view["schema_version"] == VIEW_VERSION
    assert len(view["propositions"]) == len(verified["semantic_units"])


def _calibration_spec(source: dict, *, forbidden_product: str | None = None) -> dict:
    evidence_ids = [row["evidence_id"] for row in source["captured_items"]]
    route_bundle = build_bundle(source, max_prompt_bytes=16_000)
    spec = {
        "schema_version": CALIBRATION_SPEC_VERSION,
        "required_adjudication_version": CALIBRATION_ADJUDICATION_VERSION,
        "full_source_sha256": source["source_sha256"],
        "method_version": source["semantic_method_version"],
        "route_contract": {
            "runner_revision": "test-fixture-revision",
            "contract_version": "v11-test",
            "method_sha256": route_bundle["method_sha256"],
            "bundle_schema_version": BUNDLE_VERSION_V5,
            "response_schema_version": route_bundle["semantic_work_unit_projection"][
                "semantic_execution_identity"
            ]["response_schema_version"],
            "prompt_encoding_version": route_bundle["semantic_work_unit_projection"][
                "semantic_execution_identity"
            ]["prompt_encoding_version"],
            "axes_sha256": _canonical_hash(source["axes"]),
            "product_identity_catalog_sha256": source.get(
                "product_identity_catalog", {}
            ).get("catalog_sha256"),
        },
        "slices": [
            {
                "slice_id": "semantic-core",
                "purpose": "controlled semantic calibration fixture",
                "evidence_ids": evidence_ids,
                "max_prompt_bytes": 16_000,
                "max_evidence_per_work_unit": 120,
                "minimum_largest_prompt_bytes": 1_000,
                "axis_repetition_warning": {
                    "minimum_axis_count": 1,
                    "minimum_repeated_units": 2,
                },
                "semantic_unit_density_audit": {"top_non_gold_rows": 1},
                "cases": [
                    {
                        "case_id": "drying-after-week",
                        "evidence_id": evidence_ids[0],
                        "archetype": "first-hand conditioned claim",
                        "critical": True,
                        "expected_disposition": "claim_bearing",
                        "min_semantic_units": 1,
                        "max_semantic_units": 1,
                        "required_atoms": [
                            {
                                "atom_id": "drying",
                                "meaning": "The balm became drying after a week of use.",
                                "expected_fields": {
                                    "subject_product_ids": ["sf-lbb"],
                                    "axis_ids": ["wear"],
                                    "evidence_posture": "first_hand",
                                },
                            }
                        ],
                        "forbidden_values": (
                            {"subject_product_ids": [forbidden_product]}
                            if forbidden_product
                            else {}
                        ),
                        "allow_unmatched_units": False,
                    }
                ],
            }
        ],
        "relation_obligations": [],
        "cold_repeat_case_ids": [],
    }
    spec["spec_sha256"] = _canonical_hash(spec)
    return spec


def _calibration_adjudication(spec: dict, compilation_sha256: str) -> dict:
    warning_adjudications = [
        {
            "warning_id": "repeated-large-axis-signature:semantic-core",
            "compilation_sha256": compilation_sha256,
            "outcome": "reviewed_benign",
        }
    ]
    gold_evidence_ids = {
        case["evidence_id"] for case in spec["slices"][0]["cases"]
    }
    non_gold_evidence_ids = [
        evidence_id
        for evidence_id in spec["slices"][0]["evidence_ids"]
        if evidence_id not in gold_evidence_ids
    ]
    if (
        spec["slices"][0].get("semantic_unit_density_audit") is not None
        and non_gold_evidence_ids
    ):
        warning_adjudications.append(
            {
                "warning_id": (
                    "semantic-unit-density-audit:semantic-core:"
                    f"{non_gold_evidence_ids[0]}"
                ),
                "compilation_sha256": compilation_sha256,
                "outcome": "reviewed_benign",
                "checks": {
                    "all_units_source_supported": True,
                    "all_units_independently_meaningful": True,
                    "no_duplicate_or_redundant_units": True,
                    "split_granularity_supported": True,
                },
            }
        )
    adjudication = {
        "schema_version": CALIBRATION_ADJUDICATION_VERSION,
        "spec_sha256": spec["spec_sha256"],
        "adjudicator": "cold-test-adjudicator",
        "case_adjudications": [
            {
                "case_id": "drying-after-week",
                "compilation_sha256": compilation_sha256,
                "atom_matches": {"drying": "drying-after-week"},
                "axis_support_by_unit": {
                    "drying-after-week": {
                        "supported_axis_ids": ["wear"],
                        "unsupported_axis_ids": [],
                        "statement_direction_supported": True,
                    }
                },
            }
        ],
        "relation_adjudications": [],
        "cold_repeat_adjudications": [],
        "warning_adjudications": warning_adjudications,
    }
    adjudication["adjudication_sha256"] = _canonical_hash(adjudication)
    return adjudication


@pytest.mark.parametrize("method", sorted(semantic_module.SEMANTIC_METHODS_V7_PLUS))
def test_calibration_current_methods_require_verified_primary_and_repeat(method, tmp_path: Path) -> None:
    source = _source_v7(count=2)
    source["semantic_method_version"] = method
    source = materialize_source_v3(source)
    spec = _calibration_spec(source)
    spec["cold_repeat_case_ids"] = ["drying-after-week"]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 16_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    assert prepared == prepare_semantic_calibration(source, spec)
    responses, verified = {}, {}
    for name, part in (("semantic-core", prepared["slices"][0]),
                       ("cold-repeat", prepared["cold_repeat"])):
        bundle = part["bundle"]
        assert bundle["method_version"] == method
        responses[name] = [
            semantic_module._batch_response_from_rows(
                bundle, batch["batch_id"], [_claim_row(eid) for eid in batch["evidence_ids"]]
            ) for batch in bundle["batches"]
        ]
        raw = validate_batch_responses(bundle, responses[name])
        stage, _ = prepare_row_verification(bundle, raw, max_prompt_bytes=30_000)
        verified[name] = apply_row_verification(
            bundle, raw, stage, _row_verification_responses(stage)
        )
    adjudication = _calibration_adjudication(spec, verified["semantic-core"]["compilation_sha256"])
    adjudication["cold_repeat_adjudications"] = [{
        "case_id": "drying-after-week",
        "primary_compilation_sha256": verified["semantic-core"]["compilation_sha256"],
        "repeat_compilation_sha256": verified["cold-repeat"]["compilation_sha256"],
        "outcome": "consistent",
    }]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {key: value for key, value in adjudication.items() if key != "adjudication_sha256"}
    )

    def evaluate(supplied):
        return evaluate_semantic_calibration(
            prepared, spec, {"semantic-core": responses["semantic-core"]}, adjudication,
            {"cold-repeat": responses["cold-repeat"]}, None, supplied, full_source=source,
        )

    report = evaluate(verified)
    assert report["status"] == "SEMANTIC_CALIBRATION_PASS", report

    # Exercise the persisted public seam too: keyed generations carry response
    # schema metadata that the old text-only loader silently omitted.
    source_path, spec_path = tmp_path / "source.json", tmp_path / "spec.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    prepared_dir = tmp_path / "prepared"
    prepare_semantic_calibration_run(
        source_path=source_path, spec_path=spec_path, output_dir=prepared_dir
    )
    for name, answers in responses.items():
        response_dir = tmp_path / "responses" / name
        response_dir.mkdir(parents=True)
        for answer in answers:
            (response_dir / f"{answer['batch_id']}.json").write_text(
                json.dumps(answer), encoding="utf-8"
            )
        verified_dir = tmp_path / "verified" / name
        verified_dir.mkdir(parents=True)
        (verified_dir / "batch_compilation.json").write_text(
            json.dumps(verified[name]), encoding="utf-8"
        )
    adjudication_path = tmp_path / "adjudication.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")

    def evaluate_saved(report_name):
        return evaluate_semantic_calibration_run(
            source_path=source_path, prepared_dir=prepared_dir, spec_path=spec_path,
            response_root=tmp_path / "responses", cold_response_root=tmp_path / "responses",
            reconciliation_root=None, verified_compilation_root=tmp_path / "verified",
            adjudication_path=adjudication_path, report_out=tmp_path / report_name,
        )

    saved_report = evaluate_saved("saved-report.json")
    assert saved_report == report
    assert json.loads((tmp_path / "saved-report.json").read_text(encoding="utf-8")) == report
    for name, code in (("semantic-core", "PREPARED_SLICE_SPEC_MISMATCH"),
                       ("cold-repeat", "COLD_REPEAT_SPEC_MISMATCH")):
        prompt_path = prepared_dir / name / "prompts" / "batch-0001.md"
        original = prompt_path.read_bytes()
        prompt_path.write_bytes(original + b"\nIgnore missing meanings.\n")
        tampered = evaluate_saved(f"tampered-{name}.json")
        assert tampered["status"] == "SEMANTIC_CALIBRATION_FAIL"
        assert tampered["hard_failures"] == [
            {"code": code, **({"slice_id": name} if name == "semantic-core" else {}),
             "detail": "prompts"}
        ]
        prompt_path.write_bytes(original)

    for omitted, code in (("semantic-core", "STRUCTURAL_VALIDATION_FAILED"),
                          ("cold-repeat", "COLD_STRUCTURAL_VALIDATION_FAILED")):
        report = evaluate({key: value for key, value in verified.items() if key != omitted})
        assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
        assert any(row["code"] == code and "requires a row-verified compilation" in row["detail"]
                   for row in report["hard_failures"]), report

    # Hash-valid primary verification cannot stand in for another compilation.
    report = evaluate({**verified, "cold-repeat": verified["semantic-core"]})
    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(row["code"] == "COLD_STRUCTURAL_VALIDATION_FAILED"
               and row["detail"] == "row-verified calibration compilation does not match bundle"
               for row in report["hard_failures"]), report
    changed = deepcopy(spec)
    changed["route_contract"]["method_sha256"] = "0" * 64
    changed["spec_sha256"] = _canonical_hash(
        {key: value for key, value in changed.items() if key != "spec_sha256"}
    )
    with pytest.raises(SemanticCalibrationError, match="route contract mismatch: method_sha256"):
        prepare_semantic_calibration(source, changed)


def test_calibration_spec_rejects_machine_output_leakage() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["slices"][0]["cases"][0]["observed_disposition"] = "claim_bearing"
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )

    with pytest.raises(SemanticCalibrationError, match="machine-output field"):
        validate_calibration_spec(spec)


def test_calibration_preparation_is_exact_and_deterministic() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)

    first = prepare_semantic_calibration(source, spec)
    second = prepare_semantic_calibration(source, spec)

    assert first == second
    assert first["receipt"]["full_source_sha256"] == source["source_sha256"]
    prepared = first["slices"][0]
    assert prepared["bundle"]["schema_version"] == BUNDLE_VERSION_V5
    assert [
        evidence_id
        for batch in prepared["bundle"]["batches"]
        for evidence_id in batch["evidence_ids"]
    ] == spec["slices"][0]["evidence_ids"]
    assert source == materialize_source_v3(_source_v5(count=2))


def test_calibration_preparation_uses_the_spec_bound_v6_method() -> None:
    source = materialize_source_v3(_source_v6(count=2))
    spec = _calibration_spec(source)

    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]

    assert spec["method_version"] == METHOD_VERSION_V6
    assert bundle["schema_version"] == BUNDLE_VERSION_V5
    assert bundle["method_version"] == METHOD_VERSION_V6
    identity = bundle["semantic_work_unit_projection"]["semantic_execution_identity"]
    assert identity["response_schema_version"] == BATCH_RESPONSE_VERSION_V3
    assert "V6 MEANING-PRESERVATION CLARIFICATIONS" in build_batch_prompts(bundle)[
        0
    ]["prompt"]


def test_calibration_preparation_rejects_a_stale_route_fingerprint() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["route_contract"]["method_sha256"] = "0" * 64
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )

    with pytest.raises(SemanticCalibrationError, match="method_sha256"):
        prepare_semantic_calibration(source, spec)


def test_calibration_blocks_without_semantic_adjudication() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": _v5_responses(bundle)},
        None,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        row["code"] == "SEMANTIC_ADJUDICATION_MISSING"
        for row in report["blockers"]
    )


def test_calibration_treats_explicit_atom_no_match_as_failure() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["case_adjudications"][0]["atom_matches"]["drying"] = None
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        "has no equivalent semantic unit" in row["detail"]
        for row in report["hard_failures"]
    )


def test_calibration_v2_rejects_a_semantically_unsupported_axis() -> None:
    raw_source = _source_v5(count=2)
    raw_source["axes"].append({"axis_id": "hydration", "label": "Hydration"})
    raw_source["captured_items"][0]["axis_candidates"].append("hydration")
    source = materialize_source_v3(raw_source)
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    responses[0]["evidence"][0]["semantic_units"][0]["axis_ids"].append(
        "hydration"
    )
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    axis_judgment = adjudication["case_adjudications"][0][
        "axis_support_by_unit"
    ]["drying-after-week"]
    axis_judgment["unsupported_axis_ids"].append("hydration")
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        "semantically unsupported axes ['hydration']" in row["detail"]
        for row in report["hard_failures"]
    )


def test_calibration_v3_rejects_bad_direction_on_an_unmerged_unit() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["case_adjudications"][0]["axis_support_by_unit"][
        "drying-after-week"
    ]["statement_direction_supported"] = False
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        "does not preserve its asserted meaning direction" in row["detail"]
        for row in report["hard_failures"]
    )


def test_calibration_v2_blocks_when_axis_judgment_is_missing() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    del adjudication["case_adjudications"][0]["axis_support_by_unit"]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        "units lack per-axis semantic adjudication" in row["detail"]
        for row in report["blockers"]
    )


def test_calibration_v1_adjudication_remains_readable_for_historical_reports() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["schema_version"] = CALIBRATION_SPEC_VERSION_V1
    del spec["required_adjudication_version"]
    del spec["slices"][0]["semantic_unit_density_audit"]
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["schema_version"] = CALIBRATION_ADJUDICATION_VERSION_V1
    del adjudication["case_adjudications"][0]["axis_support_by_unit"]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"


def test_calibration_v2_spec_remains_readable_without_density_audit() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["schema_version"] = "semantic_calibration_spec_v2"
    del spec["slices"][0]["semantic_unit_density_audit"]
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )

    assert validate_calibration_spec(spec)["schema_version"] == (
        "semantic_calibration_spec_v2"
    )


def test_calibration_v2_adjudication_remains_readable_for_historical_reports() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["schema_version"] = CALIBRATION_SPEC_VERSION_V1
    del spec["required_adjudication_version"]
    del spec["slices"][0]["semantic_unit_density_audit"]
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["schema_version"] = CALIBRATION_ADJUDICATION_VERSION_V2
    del adjudication["case_adjudications"][0]["axis_support_by_unit"][
        "drying-after-week"
    ]["statement_direction_supported"]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"


def test_calibration_v2_cannot_pass_with_historical_v1_adjudication() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["schema_version"] = CALIBRATION_ADJUDICATION_VERSION_V1
    del adjudication["case_adjudications"][0]["axis_support_by_unit"]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        row["code"] == "ADJUDICATION_VERSION_REQUIRED"
        for row in report["blockers"]
    )


def test_calibration_cannot_satisfy_two_atoms_with_one_broad_unit() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    second_atom = deepcopy(spec["slices"][0]["cases"][0]["required_atoms"][0])
    second_atom["atom_id"] = "week-condition"
    second_atom["meaning"] = "The drying appeared after one week of use."
    spec["slices"][0]["cases"][0]["required_atoms"].append(second_atom)
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["case_adjudications"][0]["atom_matches"][
        "week-condition"
    ] = "drying-after-week"
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any("reuses unit key" in row["detail"] for row in report["hard_failures"])


def test_calibration_passes_matching_semantic_atom_and_warns_on_repetition() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle, detailed_per_batch=2)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"
    assert report["case_results"][0]["status"] == "pass"
    assert report["warnings"][0]["code"] == "REPEATED_LARGE_AXIS_SIGNATURE"


def test_calibration_density_audit_requires_a_bound_semantic_judgment() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle, detailed_per_batch=2)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["warning_adjudications"] = adjudication[
        "warning_adjudications"
    ][:1]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        row["code"] == "WARNING_ADJUDICATION_MISSING_OR_STALE"
        and row["warning_id"].startswith("semantic-unit-density-audit:")
        for row in report["blockers"]
    )


def test_calibration_density_audit_confirmed_defect_is_a_hard_failure() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle, detailed_per_batch=2)
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["warning_adjudications"][1]["outcome"] = "reviewed_defect"
    adjudication["warning_adjudications"][1]["checks"][
        "split_granularity_supported"
    ] = False
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        row["code"] == "SEMANTIC_ANOMALY_CONFIRMED"
        and row["warning_id"].startswith("semantic-unit-density-audit:")
        for row in report["hard_failures"]
    )


def test_calibration_rejects_structurally_valid_wrong_known_product() -> None:
    raw_source = _source_v5(count=2, catalog=True)
    catalog = raw_source["product_identity_catalog"]
    catalog.pop("catalog_sha256")
    catalog["products"].append(
        {
            "stable_product_id": "other-balm",
            "display_name": "Other Balm",
            "source_product_ids": ["other-balm"],
            "aliases": ["Other"],
            "authority_artifact_ids": ["thread-1"],
        }
    )
    catalog["products"].sort(key=lambda row: row["stable_product_id"])
    catalog["catalog_sha256"] = _canonical_hash(catalog)
    source = materialize_source_v3(raw_source)
    spec = _calibration_spec(source, forbidden_product="other-balm")
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    responses[0]["evidence"][0]["semantic_units"][0]["subject_product_ids"] = [
        "other-balm"
    ]

    # The route validator accepts the catalog-valid substitution; calibration
    # must still reject its meaning and binding.
    validate_batch_responses(bundle, responses)
    compilation = validate_batch_responses(bundle, responses)
    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any("forbidden subject_product_ids" in row["detail"] for row in report["hard_failures"])


def test_calibration_runner_writes_once_and_evaluates_bound_outputs(
    tmp_path: Path,
) -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    source_path = tmp_path / "source.json"
    spec_path = tmp_path / "spec.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    prepared_dir = tmp_path / "prepared"

    result = prepare_semantic_calibration_run(
        source_path=source_path,
        spec_path=spec_path,
        output_dir=prepared_dir,
    )
    assert result["status"] == "SEMANTIC_CALIBRATION_PREPARED"
    assert result["adjudication_contract_id"] == ADJUDICATION_CONTRACT_ID
    assert result["adjudication_contract_sha256"] == (
        ADJUDICATION_CONTRACT_SHA256
    )
    receipt = json.loads(
        (prepared_dir / "preparation_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["schema_version"] == CALIBRATION_PREPARATION_VERSION
    assert receipt["adjudication_contract_id"] == ADJUDICATION_CONTRACT_ID
    assert receipt["adjudication_contract_sha256"] == (
        ADJUDICATION_CONTRACT_SHA256
    )
    adjudication_contract = (
        prepared_dir / "adjudication_contract.md"
    ).read_text(encoding="utf-8")
    normalized_contract = " ".join(adjudication_contract.split())
    assert "A is less moisturising than B" in normalized_contract
    assert "`polarity: affirmed`" in normalized_contract
    assert "not a sentiment or lower-is-negative judgment" in normalized_contract
    assert "wanting more pigment is `polarity: affirmed`" in normalized_contract
    assert "different number of supported atomic units is not by itself inconsistent" in normalized_contract
    assert "both attributed parent claims and its own first-hand shopping reaction" in normalized_contract
    assert "`case_adjudications`, `relation_adjudications`," in normalized_contract
    assert "`cold_repeat_adjudications`, and `warning_adjudications` literally" in normalized_contract
    assert "mapping every required atom id to one semantic-unit key or" in normalized_contract
    assert "a disjoint, complete partition of that unit's actual `axis_ids`" in normalized_contract
    assert "`primary_compilation_sha256`, `repeat_compilation_sha256`" in normalized_contract
    assert "`all_units_source_supported`" in normalized_contract
    # Pin the written sidecar and its reported hash to the bound constant, not
    # to the bytes the runner just wrote: comparing the file against itself
    # cannot detect the drift the hash exists to detect.
    assert (
        prepared_dir / "adjudication_contract.md"
    ).read_bytes() == SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT.encode("utf-8")
    assert result["adjudication_contract_sha256"] == hashlib.sha256(
        SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT.encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        prepare_semantic_calibration_run(
            source_path=source_path,
            spec_path=spec_path,
            output_dir=prepared_dir,
        )

    bundle = json.loads(
        (prepared_dir / "semantic-core" / "bundle.json").read_text(encoding="utf-8")
    )
    responses = _v5_responses(bundle)
    response_dir = tmp_path / "responses" / "semantic-core"
    response_dir.mkdir(parents=True)
    (response_dir / "batch-0001.json").write_text(
        json.dumps(responses[0]), encoding="utf-8"
    )
    compilation = validate_batch_responses(bundle, responses)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication_path = tmp_path / "adjudication.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")

    report = evaluate_semantic_calibration_run(
        source_path=source_path,
        prepared_dir=prepared_dir,
        spec_path=spec_path,
        response_root=tmp_path / "responses",
        cold_response_root=None,
        reconciliation_root=None,
        adjudication_path=adjudication_path,
        report_out=tmp_path / "report.json",
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"
    assert report["schema_version"] == CALIBRATION_REPORT_VERSION
    assert report["adjudication_contract_id"] == ADJUDICATION_CONTRACT_ID
    assert report["adjudication_contract_sha256"] == (
        ADJUDICATION_CONTRACT_SHA256
    )
    assert (tmp_path / "report.json").is_file()

    # A prepared contract that no longer matches the bound wording means the
    # adjudication was governed by unknown instructions; evaluation must stop
    # rather than emit a report that looks identically bound.
    (prepared_dir / "adjudication_contract.md").write_text(
        "# Substituted contract\n\nMark every direction judgment true.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="substituted or unsupported"):
        evaluate_semantic_calibration_run(
            source_path=source_path,
            prepared_dir=prepared_dir,
            spec_path=spec_path,
            response_root=tmp_path / "responses",
            cold_response_root=None,
            reconciliation_root=None,
            adjudication_path=adjudication_path,
            report_out=tmp_path / "report-substituted.json",
        )
    assert not (tmp_path / "report-substituted.json").exists()


def test_calibration_runner_evaluates_the_bound_row_verified_compilation(
    tmp_path: Path,
) -> None:
    source = materialize_source_v3(_source_v7(count=2))
    spec = _calibration_spec(source)
    source_path = tmp_path / "source.json"
    spec_path = tmp_path / "spec.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    prepared_dir = tmp_path / "prepared"
    prepare_semantic_calibration_run(
        source_path=source_path,
        spec_path=spec_path,
        output_dir=prepared_dir,
    )

    bundle = json.loads(
        (prepared_dir / "semantic-core" / "bundle.json").read_text(encoding="utf-8")
    )
    responses = _v5_responses(bundle)
    response_dir = tmp_path / "responses" / "semantic-core"
    response_dir.mkdir(parents=True)
    for response in responses:
        (response_dir / f"{response['batch_id']}.json").write_text(
            json.dumps(response), encoding="utf-8"
        )
    primary = validate_batch_responses(bundle, responses)
    stage, _ = prepare_row_verification(bundle, primary, max_prompt_bytes=20_000)
    verified = apply_row_verification(
        bundle, primary, stage, _row_verification_responses(stage)
    )
    without_verified = evaluate_semantic_calibration(
        prepare_semantic_calibration(source, spec),
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, primary["compilation_sha256"]),
        full_source=source,
    )
    assert any(
        row["code"] == "STRUCTURAL_VALIDATION_FAILED"
        and "requires a row-verified compilation" in row["detail"]
        for row in without_verified["hard_failures"]
    )
    verified_dir = tmp_path / "verified" / "semantic-core"
    verified_dir.mkdir(parents=True)
    (verified_dir / "batch_compilation.json").write_text(
        json.dumps(verified), encoding="utf-8"
    )
    adjudication_path = tmp_path / "adjudication.json"
    adjudication_path.write_text(
        json.dumps(_calibration_adjudication(spec, verified["compilation_sha256"])),
        encoding="utf-8",
    )

    report = evaluate_semantic_calibration_run(
        source_path=source_path,
        prepared_dir=prepared_dir,
        spec_path=spec_path,
        response_root=tmp_path / "responses",
        cold_response_root=None,
        reconciliation_root=None,
        verified_compilation_root=tmp_path / "verified",
        adjudication_path=adjudication_path,
        report_out=tmp_path / "report.json",
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"
    assert report["slice_compilation_sha256"] == {
        "semantic-core": verified["compilation_sha256"]
    }


def test_legacy_calibration_receipt_keeps_v1_report_shape() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    legacy_receipt = deepcopy(prepared["receipt"])
    legacy_receipt["schema_version"] = CALIBRATION_PREPARATION_VERSION_V1
    legacy_receipt.pop("adjudication_contract_id")
    legacy_receipt.pop("adjudication_contract_sha256")
    legacy_receipt["preparation_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in legacy_receipt.items()
            if key != "preparation_sha256"
        }
    )
    prepared["receipt"] = legacy_receipt
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["schema_version"] == CALIBRATION_REPORT_VERSION_V1
    assert "adjudication_contract_id" not in report
    assert "adjudication_contract_sha256" not in report


def test_current_adjudication_contract_has_a_pinned_identity() -> None:
    assert ADJUDICATION_CONTRACT_SHA256 == (
        "2ffa9d5fcc0f040406c0ab61dd1d0694f78660daa638d6c0eaac36d7f1d91796"
    )
    identity = adjudication_contract_identity(
        SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT.encode("utf-8")
    )

    assert identity == {
        "adjudication_contract_id": ADJUDICATION_CONTRACT_ID,
        "adjudication_contract_sha256": ADJUDICATION_CONTRACT_SHA256,
    }
    with pytest.raises(
        SemanticCalibrationError, match="substituted or unsupported"
    ):
        adjudication_contract_identity(b"# unknown ruler\n")


def test_cold_repeat_adjudication_is_bound_to_both_compilations() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["cold_repeat_case_ids"] = ["drying-after-week"]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 12_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    cold_bundle = prepared["cold_repeat"]["bundle"]
    assert [row["evidence_id"] for row in cold_bundle["evidence_units"]] == [
        source["captured_items"][0]["evidence_id"]
    ]
    primary = _v5_responses(bundle)
    repeat = _v5_responses(cold_bundle)
    primary_compilation = validate_batch_responses(bundle, primary)
    repeat_compilation = validate_batch_responses(cold_bundle, repeat)
    adjudication = _calibration_adjudication(
        spec, primary_compilation["compilation_sha256"]
    )
    adjudication["cold_repeat_adjudications"] = [
        {
            "case_id": "drying-after-week",
            "primary_compilation_sha256": primary_compilation["compilation_sha256"],
            "repeat_compilation_sha256": repeat_compilation["compilation_sha256"],
            "outcome": "consistent",
        }
    ]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": primary},
        adjudication,
        {"cold-repeat": repeat},
        full_source=source,
    )
    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"

    stale = deepcopy(adjudication)
    stale["cold_repeat_adjudications"][0]["repeat_compilation_sha256"] = "0" * 64
    stale["adjudication_sha256"] = _canonical_hash(
        {key: value for key, value in stale.items() if key != "adjudication_sha256"}
    )
    blocked = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": primary},
        stale,
        {"cold-repeat": repeat},
        full_source=source,
    )
    assert blocked["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        row["code"] == "COLD_REPEAT_ADJUDICATION_STALE"
        for row in blocked["blockers"]
    )


def test_relation_adjudication_requires_a_rebuilt_final_view() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    second_case = deepcopy(spec["slices"][0]["cases"][0])
    second_case["case_id"] = "drying-after-week-second-origin"
    second_case["evidence_id"] = source["captured_items"][1]["evidence_id"]
    spec["slices"][0]["cases"].append(second_case)
    spec["relation_obligations"] = [
        {
            "relation_id": "same-meaning-independent-origins",
            "relation_type": "independent_origin_preserved",
            "case_ids": ["drying-after-week", "drying-after-week-second-origin"],
            "critical": True,
            "meaning": "Both origins remain visible in one reconciled meaning.",
        }
    ]
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle, detailed_per_batch=2)
    compilation = validate_batch_responses(bundle, responses)
    stage, _ = prepare_reconciliation_stage(bundle, compilation)
    terminal = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=True)
    )
    view = finalize_v3_view(bundle, compilation, terminal)
    adjudication = _calibration_adjudication(
        spec, compilation["compilation_sha256"]
    )
    adjudication["case_adjudications"].append(
        {
            "case_id": "drying-after-week-second-origin",
            "compilation_sha256": compilation["compilation_sha256"],
            "atom_matches": {"drying": "drying-after-week"},
            "axis_support_by_unit": {
                "drying-after-week": {
                    "supported_axis_ids": ["wear"],
                    "unsupported_axis_ids": [],
                    "statement_direction_supported": True,
                }
            },
        }
    )
    adjudication["relation_adjudications"] = [
        {
            "relation_id": "same-meaning-independent-origins",
            "compilation_sha256_by_slice": {
                "semantic-core": compilation["compilation_sha256"]
            },
            "view_sha256_by_slice": {"semantic-core": view["view_sha256"]},
            "outcome": "satisfied",
        }
    ]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    without_view = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        full_source=source,
    )
    assert without_view["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert any(
        row["code"] == "RECONCILIATION_OUTPUT_MISSING"
        for row in without_view["blockers"]
    )

    with_view = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        adjudication,
        reconciliation_by_slice={
            "semantic-core": {"node_compilation": terminal, "view": view}
        },
        full_source=source,
    )
    assert with_view["status"] == "SEMANTIC_CALIBRATION_PASS"


def test_calibration_spec_accepts_meaning_direction_relation() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    case_id = spec["slices"][0]["cases"][0]["case_id"]
    spec["relation_obligations"] = [
        {
            "relation_id": "negation-survives-final-view",
            "relation_type": "meaning_direction_preserved",
            "case_ids": [case_id],
            "critical": True,
            "meaning": "The final meaning preserves the child's negation.",
        }
    ]
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )

    normalized = validate_calibration_spec(spec)

    assert normalized["relation_obligations"][0]["relation_type"] == (
        "meaning_direction_preserved"
    )


def _rehash_spec(spec: dict) -> None:
    spec["spec_sha256"] = _canonical_hash(
        {key: value for key, value in spec.items() if key != "spec_sha256"}
    )


def test_calibration_spec_rejects_a_misspelled_obligation_field() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["slices"][0]["casses"] = spec["slices"][0].pop("cases")
    _rehash_spec(spec)

    # A silently ignored obligation key would delete every case from the gate
    # while the report still read as a pass.
    with pytest.raises(SemanticCalibrationError, match="unknown gold fields"):
        validate_calibration_spec(spec)


def test_calibration_spec_requires_at_least_one_case() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["slices"][0]["cases"] = []
    _rehash_spec(spec)

    with pytest.raises(SemanticCalibrationError, match="at least one case"):
        validate_calibration_spec(spec)


def test_claim_bearing_calibration_case_requires_an_atomic_meaning() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["slices"][0]["cases"][0]["required_atoms"] = []
    _rehash_spec(spec)

    with pytest.raises(SemanticCalibrationError, match="atomic meaning"):
        validate_calibration_spec(spec)


def test_calibration_spec_closes_every_gold_container() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    case_id = spec["slices"][0]["cases"][0]["case_id"]
    spec["relation_obligations"] = [
        {
            "relation_id": "self-retrieval",
            "relation_type": "must_co_retrieve",
            "case_ids": [case_id],
            "critical": True,
            "meaning": "fixture relation",
        }
    ]
    spec["cold_repeat_case_ids"] = [case_id]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 12_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    containers = (
        (),
        ("slices", 0),
        ("slices", 0, "cases", 0),
        ("slices", 0, "cases", 0, "required_atoms", 0),
        ("relation_obligations", 0),
        ("cold_repeat",),
        ("slices", 0, "axis_repetition_warning"),
    )

    for path in containers:
        candidate = deepcopy(spec)
        target = candidate
        for key in path:
            target = target[key]
        target["unexpected_gold_field"] = True
        _rehash_spec(candidate)
        with pytest.raises(SemanticCalibrationError, match="unknown gold fields"):
            validate_calibration_spec(candidate)


def test_calibration_evaluation_rejects_a_substituted_prepared_bundle() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)

    narrow_spec = deepcopy(spec)
    narrow_spec["slices"][0]["evidence_ids"] = spec["slices"][0]["evidence_ids"][:1]
    _rehash_spec(narrow_spec)
    narrow = prepare_semantic_calibration(source, narrow_spec)["slices"][0]

    # A substituted prepared directory can always be made self-consistent: the
    # preparation receipt is self-hashed, so on its own it proves nothing about
    # which route and which evidence the gate actually judged.
    forged = deepcopy(prepared)
    forged["slices"][0]["source"] = narrow["source"]
    forged["slices"][0]["bundle"] = narrow["bundle"]
    forged["slices"][0]["route_fingerprint"] = narrow["route_fingerprint"]
    receipt = deepcopy(prepared["receipt"])
    receipt["slices"][0]["source_sha256"] = narrow["source"]["source_sha256"]
    receipt["slices"][0]["bundle_sha256"] = narrow["bundle"]["bundle_sha256"]
    receipt["slices"][0]["route_fingerprint"] = narrow["route_fingerprint"]
    receipt["slices"][0]["evidence_count"] = len(narrow["bundle"]["evidence_units"])
    receipt["slices"][0]["work_unit_count"] = len(narrow["bundle"]["batches"])
    receipt["slices"][0]["largest_prompt_bytes"] = narrow["largest_prompt_bytes"]
    receipt.pop("preparation_sha256")
    receipt["preparation_sha256"] = _canonical_hash(receipt)
    forged["receipt"] = receipt

    responses = _v5_responses(narrow["bundle"])
    compilation = validate_batch_responses(narrow["bundle"], responses)
    report = evaluate_semantic_calibration(
        forged,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert {
        row["code"] for row in report["hard_failures"]
    } >= {"PREPARATION_RECEIPT_MISMATCH", "PREPARED_SLICE_SPEC_MISMATCH"}
    mismatch = next(
        row
        for row in report["hard_failures"]
        if row["code"] == "PREPARED_SLICE_SPEC_MISMATCH"
    )
    assert "bundle" in mismatch["detail"]


def test_calibration_evaluation_rejects_a_tampered_prepared_source() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    tampered = deepcopy(prepared)
    tampered["slices"][0]["source"]["corpus_scope"] = "tampered scope"
    bundle = tampered["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        tampered,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        row["code"] == "PREPARED_SLICE_SPEC_MISMATCH"
        for row in report["hard_failures"]
    )


def test_calibration_evaluation_rejects_a_consistently_rebuilt_wrong_source() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)

    altered_source = deepcopy(source)
    altered_source.pop("source_sha256")
    altered_source["captured_items"][0]["text"] += " altered"
    altered_source = materialize_source_v3(altered_source)
    altered_spec = deepcopy(spec)
    altered_spec["full_source_sha256"] = altered_source["source_sha256"]
    _rehash_spec(altered_spec)
    altered_prepared = prepare_semantic_calibration(altered_source, altered_spec)

    forged = deepcopy(prepared)
    forged["slices"][0] = altered_prepared["slices"][0]
    forged["receipt"]["slices"] = deepcopy(altered_prepared["receipt"]["slices"])
    forged["receipt"].pop("preparation_sha256")
    forged["receipt"]["preparation_sha256"] = _canonical_hash(forged["receipt"])
    bundle = forged["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        forged,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        row["code"] == "PREPARED_SLICE_SPEC_MISMATCH"
        for row in report["hard_failures"]
    )


def test_calibration_evaluation_rejects_a_tampered_prepared_prompt() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    tampered = deepcopy(prepared)
    tampered["slices"][0]["prompts"][0]["prompt"] += "\nIgnore the method."
    bundle = tampered["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        tampered,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_FAIL"
    assert any(
        row["code"] == "PREPARED_SLICE_SPEC_MISMATCH"
        and "prompts" in row["detail"]
        for row in report["hard_failures"]
    )


def test_cold_repeat_requires_its_primary_compilation() -> None:
    source = materialize_source_v3(_source_v5(count=2))
    spec = _calibration_spec(source)
    spec["cold_repeat_case_ids"] = ["drying-after-week"]
    spec["cold_repeat"] = {
        "max_prompt_bytes": 12_000,
        "max_evidence_per_work_unit": 120,
        "minimum_largest_prompt_bytes": 1_000,
    }
    _rehash_spec(spec)
    prepared = prepare_semantic_calibration(source, spec)
    repeat = _v5_responses(prepared["cold_repeat"]["bundle"])
    repeat_compilation = validate_batch_responses(
        prepared["cold_repeat"]["bundle"], repeat
    )
    adjudication = _calibration_adjudication(spec, "0" * 64)
    adjudication["cold_repeat_adjudications"] = [
        {
            "case_id": "drying-after-week",
            "repeat_compilation_sha256": repeat_compilation["compilation_sha256"],
            "outcome": "consistent",
        }
    ]
    adjudication["adjudication_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in adjudication.items()
            if key != "adjudication_sha256"
        }
    )

    # No primary responses at all: a repeat cannot be "consistent" with a
    # compilation that was never produced.
    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {},
        adjudication,
        {"cold-repeat": repeat},
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_BLOCKED"
    assert report["cold_repeat_results"][0]["outcome"] == "missing"
    assert any(
        row["code"] == "COLD_REPEAT_PRIMARY_COMPILATION_MISSING"
        for row in report["blockers"]
    )


def test_calibration_unit_key_handles_an_evidence_id_containing_the_delimiter() -> None:
    raw_source = _source_v5(count=2)
    raw_source["captured_items"][0]["evidence_id"] = "reddit::delimiter-case"
    source = materialize_source_v3(raw_source)
    spec = _calibration_spec(source)
    prepared = prepare_semantic_calibration(source, spec)
    bundle = prepared["slices"][0]["bundle"]
    responses = _v5_responses(bundle)
    compilation = validate_batch_responses(bundle, responses)

    report = evaluate_semantic_calibration(
        prepared,
        spec,
        {"semantic-core": responses},
        _calibration_adjudication(spec, compilation["compilation_sha256"]),
        full_source=source,
    )

    assert report["status"] == "SEMANTIC_CALIBRATION_PASS"


def test_legacy_v4_bundle_prompt_and_compilation_bytes_are_unchanged() -> None:
    bundle = build_bundle(_source_v3(count=7), max_prompt_bytes=8_000)
    assert bundle["schema_version"] == BUNDLE_VERSION_V4
    assert bundle["bundle_sha256"] == _FROZEN_V4_PLAIN["bundle_sha256"]
    assert bundle["corpus_sha256"] == _FROZEN_V4_PLAIN["corpus_sha256"]
    assert (
        bundle["semantic_work_unit_projection"]["projection_sha256"]
        == _FROZEN_V4_PLAIN["projection_sha256"]
    )
    prompt_bytes, prompt_sha = _joined_prompt_digest(build_batch_prompts(bundle))
    assert prompt_bytes == _FROZEN_V4_PLAIN["prompt_utf8_bytes"]
    assert prompt_sha == _FROZEN_V4_PLAIN["prompt_sha256"]
    compiled = validate_batch_responses(bundle, _v3_batch_responses(bundle))
    assert compiled["schema_version"] == BATCH_COMPILATION_VERSION_V2
    assert compiled["compilation_sha256"] == _FROZEN_V4_PLAIN["compilation_sha256"]
    # The legacy compilation gains no new-generation lineage field.
    assert "raw_response_manifest" not in compiled


def test_legacy_v4_catalog_prompt_bytes_are_unchanged() -> None:
    source = _source_v3(count=7)
    source["semantic_method_version"] = METHOD_VERSION_V4
    source["product_identity_catalog"] = _product_catalog()
    bundle = build_bundle(source, max_prompt_bytes=12_000)
    assert bundle["bundle_sha256"] == _FROZEN_V4_CATALOG["bundle_sha256"]
    assert bundle["corpus_sha256"] == _FROZEN_V4_CATALOG["corpus_sha256"]
    prompt_bytes, prompt_sha = _joined_prompt_digest(build_batch_prompts(bundle))
    assert prompt_bytes == _FROZEN_V4_CATALOG["prompt_utf8_bytes"]
    assert prompt_sha == _FROZEN_V4_CATALOG["prompt_sha256"]


def test_v5_projection_binds_execution_identity_without_worker_topology() -> None:
    bundle = _bundle_v5()
    assert bundle["schema_version"] == BUNDLE_VERSION_V5
    projection = bundle["semantic_work_unit_projection"]
    assert projection["schema_version"] == WORK_UNIT_PROJECTION_VERSION_V2
    identity = projection["semantic_execution_identity"]
    assert identity["method_version"] == METHOD_VERSION_V5
    assert identity["method_sha256"] == bundle["method_sha256"]
    assert identity["response_schema_version"] == BATCH_RESPONSE_VERSION_V3
    assert identity["compilation_schema_version"] == BATCH_COMPILATION_VERSION_V3
    assert identity["prompt_encoding_version"] == PROMPT_ENCODING_VERSION
    assert identity["corpus_scope"] == bundle["corpus_scope"]
    assert identity["corpus_cutoff"] == bundle["corpus_cutoff"]
    assert projection["max_prompt_bytes"] == bundle["max_prompt_bytes"]
    # No static worker topology anywhere in the new semantic identity.
    assert "worker_count" not in projection
    assert all("worker_partition" not in row for row in projection["work_units"])
    assert all("worker_partition" not in row for row in bundle["batches"])
    prompts = build_batch_prompts(bundle)
    assert all("worker_partition" not in row for row in prompts)
    # Complete assessable-denominator coverage is still proven exactly.
    assert projection["coverage_proof"]["bijection_complete"] is True
    assert projection["coverage_proof"]["admitted_evidence_count"] == 7


def test_v5_prompt_keeps_pretty_json_encoding_and_asks_for_two_populations() -> None:
    prompt = build_batch_prompts(_bundle_v5())[0]["prompt"]
    assert "SEMANTIC EVIDENCE INTEGRATION METHOD V5" in prompt
    assert '"terminal_groups"' in prompt
    assert '"schema_version": "semantic_evidence_batch_response_v3"' in prompt
    assert '"required stable product id"' in prompt
    # Pretty, indented encoding is retained; no compact separators appear.
    assert '"evidence": [' in prompt
    assert '{"evidence_id"' not in prompt


def test_v6_reuses_v5_transport_without_changing_frozen_v5_text() -> None:
    assert hashlib.sha256(METHOD_TEXT_V5.encode("utf-8")).hexdigest() == (
        "711d36f03998958f35801722fd6ce759d576eede987d2ff47a78ea5df255a111"
    )
    bundle = build_bundle(_source_v6(), max_prompt_bytes=12_000)
    prompt = build_batch_prompts(bundle)[0]["prompt"]

    assert bundle["schema_version"] == BUNDLE_VERSION_V5
    assert bundle["method_version"] == METHOD_VERSION_V6
    # v6 is derived from the v5 constant, so an edit to either text silently
    # moves the bound method hash.  Pin the value the durable calibration
    # route contract binds so drift fails here instead of quietly orphaning
    # the frozen replay evidence from the prompt that produced it.
    assert bundle["method_sha256"] == (
        "9ff5c8a8be460ef2b599d08ec08485ebbd698ef12ad2db9eb9cf8bad38090805"
    )
    identity = bundle["semantic_work_unit_projection"]["semantic_execution_identity"]
    assert identity["response_schema_version"] == BATCH_RESPONSE_VERSION_V3
    assert identity["method_sha256"] == bundle["method_sha256"]
    assert "SEMANTIC EVIDENCE INTEGRATION METHOD V6" in prompt
    assert "V6 MEANING-PRESERVATION CLARIFICATIONS" in prompt


def test_v8_uses_exact_keyed_transport_without_changing_v7_replay() -> None:
    historical = build_bundle(_source_v7(), max_prompt_bytes=12_000)
    current = _bundle_v8()

    assert historical["semantic_work_unit_projection"]["semantic_execution_identity"][
        "response_schema_version"
    ] == BATCH_RESPONSE_VERSION_V3
    assert validate_batch_responses(historical, _v5_responses(historical))[
        "schema_version"
    ] == BATCH_COMPILATION_VERSION_V3

    identity = current["semantic_work_unit_projection"]["semantic_execution_identity"]
    assert identity["method_version"] == METHOD_VERSION_V8
    assert identity["response_schema_version"] == BATCH_KEYED_RESPONSE_VERSION
    prompt_row = build_batch_prompts(current)[0]
    assert "SEMANTIC EVIDENCE INTEGRATION METHOD V8" in prompt_row["prompt"]
    assert '"decisions_by_evidence_id"' in prompt_row["prompt"]
    assert '"terminal_groups"' not in prompt_row["prompt"]
    assert prompt_row["response_schema"] == build_batch_response_schema(
        current, prompt_row["batch_id"]
    )
    assert METHOD_TEXT_V8.startswith(METHOD_TEXT_V7.replace("METHOD V7", "METHOD V8", 1))


def test_v8_keyed_response_schema_pins_every_expected_id() -> None:
    bundle = _bundle_v8()
    batch = bundle["batches"][0]
    schema = build_batch_response_schema(bundle, batch["batch_id"])
    assert schema is not None
    decisions = schema["properties"]["decisions_by_evidence_id"]
    assert list(decisions["properties"]) == batch["evidence_ids"]
    assert decisions["required"] == batch["evidence_ids"]
    assert decisions["additionalProperties"] is False
    assert "evidence_id" not in schema["$defs"]["decision"]["properties"]


def test_v9_schema_forbids_personal_agreement_without_parent_context() -> None:
    historical = _bundle_v8()
    current = _bundle_v9()
    batch = current["batches"][0]
    evidence_id = batch["evidence_ids"][0]
    historical_schema = build_batch_response_schema(historical, batch["batch_id"])
    current_schema = build_batch_response_schema(current, batch["batch_id"])
    assert historical_schema is not None
    assert current_schema is not None
    assert historical_schema["properties"]["schema_version"]["const"] == (
        BATCH_KEYED_RESPONSE_VERSION
    )
    assert current_schema["properties"]["schema_version"]["const"] == (
        BATCH_KEYED_RESPONSE_VERSION_V2
    )
    assert historical_schema["properties"]["decisions_by_evidence_id"][
        "properties"
    ][evidence_id]["$ref"] == "#/$defs/decision"
    assert current_schema["properties"]["decisions_by_evidence_id"][
        "properties"
    ][evidence_id]["$ref"] == "#/$defs/decision_no_parent_agreement"
    postures = current_schema["$defs"]["semantic_unit_no_parent_agreement"][
        "properties"
    ]["evidence_posture"]["enum"]
    assert "personal_agreement" not in postures
    assert "personal_agreement" in historical_schema["$defs"]["semantic_unit"][
        "properties"
    ]["evidence_posture"]["enum"]
    assert METHOD_TEXT_V9.startswith(METHOD_TEXT_V8.replace("METHOD V8", "METHOD V9", 1))


def test_v9_schema_preserves_personal_agreement_when_parent_context_exists() -> None:
    source = _source_v9(count=1)
    source["captured_items"][0]["conversation_depth"] = 1
    source["captured_items"][0]["parent_context"] = [
        {
            "source_ref": "https://reddit.test/t1#parent",
            "text": "Instant Angel is my favorite moisturizer.",
        }
    ]
    bundle = build_bundle(source, max_prompt_bytes=12_000)
    batch = bundle["batches"][0]
    evidence_id = batch["evidence_ids"][0]
    schema = build_batch_response_schema(bundle, batch["batch_id"])
    assert schema is not None
    assert schema["properties"]["decisions_by_evidence_id"]["properties"][
        evidence_id
    ]["$ref"] == "#/$defs/decision"
    assert "personal_agreement" in schema["$defs"]["semantic_unit"]["properties"][
        "evidence_posture"
    ]["enum"]


def test_v10_schema_requires_one_subject_without_changing_v9_replay() -> None:
    historical = _bundle_v9()
    current = _bundle_v10()
    historical_schema = build_batch_response_schema(historical, "batch-0001")
    current_schema = build_batch_response_schema(current, "batch-0001")
    assert historical_schema is not None
    assert current_schema is not None
    assert historical_schema["properties"]["schema_version"]["const"] == (
        BATCH_KEYED_RESPONSE_VERSION_V2
    )
    assert current_schema["properties"]["schema_version"]["const"] == (
        BATCH_KEYED_RESPONSE_VERSION_V3
    )
    assert "minItems" not in historical_schema["$defs"]["semantic_unit"][
        "properties"
    ]["subject_product_ids"]
    assert current_schema["$defs"]["semantic_unit"]["properties"][
        "subject_product_ids"
    ]["minItems"] == 1
    assert current_schema["$defs"]["semantic_unit_no_parent_agreement"][
        "properties"
    ]["subject_product_ids"]["minItems"] == 1
    assert METHOD_TEXT_V10.startswith(
        METHOD_TEXT_V9.replace("METHOD V9", "METHOD V10", 1)
    )


@pytest.mark.parametrize("axis_id,label", [
    ("hydration_and_moisture", "Hydration and moisture"),
    ("hydration_barrier_visible_results", "Hydration, barrier support, and visible results"),
    ("custom-performance", "Performance under extended use"),
])
@pytest.mark.parametrize("method,verifier", [
    (semantic_module.METHOD_VERSION_V11, semantic_module.ROW_VERIFICATION_METHOD_VERSION_V10),
    (semantic_module.METHOD_VERSION_V12, semantic_module.ROW_VERIFICATION_METHOD_VERSION_V11),
])
def test_supplied_axis_vocabulary_reaches_all_current_consumers(axis_id, label, method, verifier) -> None:
    source = _source_v10(count=1)
    source["semantic_method_version"] = method
    source["axes"] = [{"axis_id": axis_id, "label": label}]
    source["captured_items"][0]["axis_candidates"] = [axis_id]
    bundle = build_bundle(source, max_prompt_bytes=30_000)
    initial = build_batch_prompts(bundle)
    schema = build_batch_response_schema(bundle, "batch-0001")
    assert schema["$defs"]["semantic_unit"]["properties"]["axis_ids"]["items"]["enum"] == [axis_id]
    assert schema["$defs"]["semantic_unit"]["properties"]["subject_product_ids"]["minItems"] == 1
    assert "personal_agreement" not in schema["$defs"]["semantic_unit_no_parent_agreement"]["properties"]["evidence_posture"]["enum"]
    responses = _keyed_responses(bundle)
    evidence_id = bundle["batches"][0]["evidence_ids"][0]
    decision = _claim_row(evidence_id)
    decision.pop("evidence_id")
    decision["semantic_units"][0]["axis_ids"] = [axis_id]
    decision["semantic_units"][0]["subject_product_ids"] = ["summer-fridays-lip-butter-balm"]
    responses[0]["decisions_by_evidence_id"][evidence_id] = decision
    primary = validate_batch_responses(bundle, responses)
    stage, verification = prepare_row_verification(bundle, primary)
    assert stage["verification_method_version"] == verifier
    verified = apply_row_verification(bundle, primary, stage, _row_verification_responses(stage))
    _, reconciliation = prepare_reconciliation_stage(bundle, verified)
    _, repairs = prepare_row_repair(bundle, verified, evidence_ids=[evidence_id])
    forbidden = ("shade_and_color_fit", "texture_and_skin_finish", "formula_consistency_and_change",
                 "reaction_and_breakout", "hydration_and_moisture", "value_and_quantity")
    for rendered in [*initial, *verification, *repairs]:
        policy = rendered["prompt"].split("\n\nCURRENT_AXES\n", 1)[0]
        assert "CURRENT_AXES is the sole vocabulary for output axis_ids" in policy
        assert not any(identifier in policy for identifier in forbidden)
        assert axis_id in rendered["prompt"]
        if method == semantic_module.METHOD_VERSION_V12:
            assert "discard generic approval" not in policy
            assert "Delete generic\napproval" not in policy
            assert "explicit overall evaluation as its own axis-free meaning" in policy
            assert "reason attached to the behavior it explains" in policy
            assert "Polarity records logical form, not sentiment" in policy
    # Reconciliation already uses a generic, ID-free policy and supplied candidates;
    # do not replace it with the much larger extraction/verifier instruction stack.
    for rendered in reconciliation:
        policy = rendered["prompt"].split("\n\nCANDIDATES\n", 1)[0]
        assert not any(identifier in policy for identifier in forbidden)
        assert axis_id in rendered["prompt"]
    assert build_batch_prompts(bundle) == initial
    # Corrupt the semantic output, not its outer bundle/stage hashes.
    foreign = deepcopy(responses)
    foreign[0]["decisions_by_evidence_id"][evidence_id]["semantic_units"][0]["axis_ids"] = ["foreign-axis"]
    with pytest.raises(SemanticIntegrationError, match="cites unknown axis"):
        validate_batch_responses(bundle, foreign)
    unassigned = deepcopy(responses)
    unassigned_unit = unassigned[0]["decisions_by_evidence_id"][evidence_id]["semantic_units"][0]
    unassigned_unit["axis_ids"] = []
    unassigned_unit["emerging_axis_labels"] = ["unmapped bounded meaning"]
    retained = validate_batch_responses(bundle, unassigned)
    assert retained["semantic_units"][0]["axis_ids"] == []
    assert retained["semantic_units"][0]["statement"] == decision["semantic_units"][0]["statement"]
    # A coherently rehashed historical-method substitution must fail downstream.
    forged = deepcopy(verified)
    manifest = forged["row_verification_manifest"]
    manifest["verification_method_version"] = ROW_VERIFICATION_METHOD_VERSION
    manifest["verification_method_sha256"] = _canonical_hash(ROW_VERIFICATION_METHOD_TEXT)
    manifest.pop("manifest_sha256")
    manifest["manifest_sha256"] = _canonical_hash(manifest)
    forged.pop("compilation_sha256")
    forged["compilation_sha256"] = _canonical_hash(forged)
    with pytest.raises(SemanticIntegrationError, match="does not bind the current verification method"):
        prepare_reconciliation_stage(bundle, forged)


def test_v11_preserves_historical_method_bytes_and_replay() -> None:
    assert _canonical_hash(METHOD_TEXT_V10) == "59276fffa718e56ed71859f22607cf765cd8ff31dcb797100cda7037e59d1278"
    assert _canonical_hash(ROW_VERIFICATION_METHOD_TEXT) == "309aa130e366a84c2d4b53ba34b117caf77858239db611574c1bb0ec10c5c5c4"
    # Independently captured before the v12 correction, not generated from v12.
    assert hashlib.sha256(semantic_module.METHOD_TEXT_V11.encode()).hexdigest() == (
        "a303d4953f279a739cc4f8c23f43f47ed48d2ec52abfdb868802a83026e44960"
    )
    assert hashlib.sha256(semantic_module.ROW_VERIFICATION_METHOD_TEXT_V10.encode()).hexdigest() == (
        "026a88d4fc15cb2e0863e1d4b5ec3a8e104da387a35ca73009654ee50c2a2093"
    )
    bundle = _bundle_v10(count=1)
    responses = _keyed_responses(bundle)
    evidence_id = bundle["batches"][0]["evidence_ids"][0]
    decision = _claim_row(evidence_id)
    decision.pop("evidence_id")
    decision["semantic_units"][0]["subject_product_ids"] = ["summer-fridays-lip-butter-balm"]
    responses[0]["decisions_by_evidence_id"][evidence_id] = decision
    primary = validate_batch_responses(bundle, responses)
    stage, prompts = prepare_row_verification(bundle, primary, max_prompt_bytes=30_000)
    assert stage["verification_method_version"] == ROW_VERIFICATION_METHOD_VERSION
    assert ROW_VERIFICATION_METHOD_TEXT in prompts[0]["prompt"]
    verified = apply_row_verification(bundle, primary, stage, _row_verification_responses(stage))
    prepare_reconciliation_stage(bundle, verified)


def test_v8_keyed_response_normalizes_to_existing_compilation() -> None:
    bundle = _bundle_v8()
    compiled = validate_batch_responses(bundle, _keyed_responses(bundle))
    assert compiled["schema_version"] == BATCH_COMPILATION_VERSION_V3
    assert [row["evidence_id"] for row in compiled["evidence_dispositions"]] == [
        row["evidence_id"] for row in bundle["evidence_units"]
    ]
    assert all(
        row["disposition"] == "context_only"
        for row in compiled["evidence_dispositions"]
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda response, ids: response["decisions_by_evidence_id"].pop(ids[0]),
            "does not account for every keyed evidence id exactly once",
        ),
        (
            lambda response, ids: response["decisions_by_evidence_id"].__setitem__(
                "foreign-evidence-id",
                response["decisions_by_evidence_id"][ids[0]],
            ),
            "reports unexpected evidence id foreign-evidence-id",
        ),
        (
            lambda response, ids: response["decisions_by_evidence_id"][ids[0]].__setitem__(
                "evidence_id", ids[0]
            ),
            "repeats evidence_id",
        ),
    ],
)
def test_v8_keyed_transport_fails_named_identity_mutations(mutate, message: str) -> None:
    bundle = _bundle_v8()
    responses = _keyed_responses(bundle)
    ids = bundle["batches"][0]["evidence_ids"]
    mutate(responses[0], ids)
    with pytest.raises(SemanticIntegrationError, match=message):
        validate_batch_responses(bundle, responses)


def test_v6_amendment_uses_general_meaning_rules_not_new_product_examples() -> None:
    amendment = METHOD_TEXT_V6.split("V6 MEANING-PRESERVATION CLARIFICATIONS", 1)[1]
    normalized = " ".join(amendment.split())
    for principle in (
        "explicit relationships",
        "Contrast and qualification still follow atomicity",
        "split opposite directions and discard generic approval",
        "stated reason remains attached",
        "never proves a purchase count",
        "retain the relative comparison",
        "outcome and direction",
        "named shade's ownership, selection, or preference",
        "adopting a parent's named-shade choice or preference",
        "Proximity alone is insufficient",
        "Non-drying is bounded hydration",
        "Physical thickness, viscosity, or feel is texture",
        "generic nickname proves no exact product",
        "asserted desire is affirmed",
        "Nearby preference supplies no reason, axis, or comparison",
        "Unmerged means unconsolidated",
    ):
        assert principle in normalized
    for product_specific_example in (
        "Summer Fridays",
        "Vanilla Beige",
        "Poppy",
        "buttercream",
    ):
        assert product_specific_example not in amendment


def test_v5_method_states_the_mandatory_four_way_boundary() -> None:
    normalized = " ".join(METHOD_TEXT_V5.split())
    for disposition in ("claim_bearing", "unresolved", "context_only", "out_of_scope"):
        assert disposition in normalized
    required_semantics = (
        "Judge every leaf exactly once after context",
        "There is no keyword, phrase, or length rule",
        '"same" may adopt one clearly targeted parent meaning',
        "never every clause of a multi-point parent",
        '"Love it" with only a known product remains context_only',
        '"Vanilla Beige!" -> "My fav!"',
        "claim_bearing personal_agreement with no axis",
        '"I always reach for it" is bounded behavior',
        "personal_agreement adopts only the target",
        "low-information same-thread recurrence",
        "never cross-venue credit",
        "attribution_or_echo reports the parent, adds no origin",
        "names attribution in its statement",
        "leading yes/no reply adopts the parent question's exact predicate",
        "Context fills an omitted predicate, not posture",
        "Evidence posture describes support, not the verb",
        "strategy_statement is organizational, never customer behavior",
        "Polarity is logical assertion, not sentiment",
        '"is drying", "worsens peeling", and "reaches for other formulas" are affirmed',
        '"is not drying" and "not the most hydrating" are negated',
        "Every unit carries a verified subject id",
        "catalog is vocabulary, not proof",
        "One unit is one independently testable proposition",
        "split them even when product, axis, or posture matches",
        '"good, but not worth $24" yields only "not worth $24"',
        "never a bundled mixed-direction unit",
        '"I have Poppy" and "would get it only on sale" are separate',
        '"Not the most hydrating" and "does not make lips drier" are separate',
        "target-versus-comparator hydration contrast",
        "Axis candidates are vocabulary, not assignments",
        "Worsening peeling supports reaction_and_breakout",
        "not-drying alone supports hydration only",
        "go-to behavior is axis-free",
        "named shade ownership remains the shade-axis exception",
        "attach the opposite as counter rather than emit two support-only claims",
        "first_hand and personal_agreement preferences may support one proposition",
        "preserve both actors and disclose their shared thread",
    )
    for phrase in required_semantics:
        assert phrase in normalized


def test_v5_method_installs_no_phrase_blacklist_or_keyword_gate() -> None:
    text = METHOD_TEXT_V5
    normalized = " ".join(text.split())
    assert "There is no keyword, phrase, or length rule" in normalized
    # The worked examples describe semantic boundaries, not matchable input
    # filters. Short inputs can still be detailed, terminal, or unresolved.
    for phrase in ('"same"', '"My fav!"', '"I always reach for it"'):
        assert phrase in text
    assert '"Love it" with only a known product remains context_only' in text
    assert "one clearly targeted parent meaning" in text


def test_v5_terminal_grouping_expands_to_one_row_per_evidence_id() -> None:
    bundle = _bundle_v5()
    responses = _v5_responses(bundle)
    compiled = validate_batch_responses(bundle, responses)
    assert compiled["schema_version"] == BATCH_COMPILATION_VERSION_V3
    dispositions = compiled["evidence_dispositions"]
    # Exact one-row-per-evidence-id expansion over the whole denominator.
    assert len(dispositions) == 7
    assert [row["evidence_id"] for row in dispositions] == bundle["batches"][0][
        "evidence_ids"
    ]
    assert sum(row["disposition"] == "claim_bearing" for row in dispositions) == 1
    assert sum(row["disposition"] == "context_only" for row in dispositions) == 6
    # Disposition reason survives expansion unchanged for every grouped id.
    grouped_reasons = {
        row["disposition_reason"]
        for row in dispositions
        if row["disposition"] == "context_only"
    }
    assert grouped_reasons == {
        "no bounded proposition remains after reading context"
    }
    # A terminal leaf emits no semantic unit, so it costs nothing downstream.
    assert len(compiled["semantic_units"]) == 1


def test_v5_grouped_and_detailed_terminal_decisions_agree_exactly() -> None:
    """Grouping is transport only: it must not change the compiled meaning."""
    bundle = _bundle_v5()
    grouped = validate_batch_responses(bundle, _v5_responses(bundle))
    reason = "no bounded proposition remains after reading context"
    detailed_responses = []
    for batch in bundle["batches"]:
        ids = batch["evidence_ids"]
        rows = [_claim_row(ids[0])] + [
            {
                "evidence_id": row,
                "disposition": "context_only",
                "disposition_reason": reason,
                "semantic_units": [],
            }
            for row in ids[1:]
        ]
        detailed_responses.append(
            {
                "schema_version": BATCH_RESPONSE_VERSION_V3,
                "bundle_sha256": bundle["bundle_sha256"],
                "batch_id": batch["batch_id"],
                "evidence": rows,
                "terminal_groups": [],
            }
        )
    detailed = validate_batch_responses(bundle, detailed_responses)
    assert grouped["evidence_dispositions"] == detailed["evidence_dispositions"]
    assert grouped["semantic_units"] == detailed["semantic_units"]
    # Lineage still distinguishes the two durable raw artifacts.
    assert (
        grouped["raw_response_manifest"]["manifest_sha256"]
        != detailed["raw_response_manifest"]["manifest_sha256"]
    )
    assert grouped["compilation_sha256"] != detailed["compilation_sha256"]


def test_v5_compilation_binds_canonical_raw_response_hashes() -> None:
    bundle = _bundle_v5()
    responses = _v5_responses(bundle)
    compiled = validate_batch_responses(bundle, responses)
    manifest = compiled["raw_response_manifest"]
    assert manifest["schema_version"] == "semantic_evidence_raw_response_manifest_v1"
    assert [row["batch_id"] for row in manifest["responses"]] == sorted(
        row["batch_id"] for row in responses
    )
    assert manifest["responses"][0]["raw_response_sha256"] == _canonical_hash(
        responses[0]
    )
    # Re-authoring the same decisions as a different raw artifact changes the
    # proven lineage even though the expansion is identical.
    reworded = deepcopy(responses)
    reworded[0]["terminal_groups"][0]["evidence_ids"] = list(
        reversed(reworded[0]["terminal_groups"][0]["evidence_ids"])
    )
    relineaged = validate_batch_responses(bundle, reworded)
    assert (
        relineaged["evidence_dispositions"] == compiled["evidence_dispositions"]
    )
    assert (
        relineaged["raw_response_manifest"]["manifest_sha256"]
        != manifest["manifest_sha256"]
    )


def test_v5_reconciliation_requires_compilation_v3_lineage() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    assert stage["batch_compilation_sha256"] == compiled["compilation_sha256"]
    stripped = deepcopy(compiled)
    stripped.pop("raw_response_manifest")
    stripped["compilation_sha256"] = _canonical_hash(
        {k: v for k, v in stripped.items() if k != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="raw response lineage"):
        prepare_reconciliation_stage(bundle, stripped)


def test_v5_rejects_legacy_compilation_generation_at_reconciliation() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    downgraded = deepcopy(compiled)
    downgraded["schema_version"] = BATCH_COMPILATION_VERSION_V2
    downgraded["compilation_sha256"] = _canonical_hash(
        {k: v for k, v in downgraded.items() if k != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="compilation generation"):
        prepare_reconciliation_stage(bundle, downgraded)


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        pytest.param(
            lambda r, ids: r["terminal_groups"][0]["evidence_ids"].append(ids[-1]),
            "repeats an evidence id",
            id="duplicate_inside_one_group",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"].append(
                {
                    "disposition": "out_of_scope",
                    "disposition_reason": "second reason",
                    "evidence_ids": [ids[-1]],
                }
            ),
            "across terminal groups",
            id="duplicate_across_groups",
        ),
        pytest.param(
            lambda r, ids: r["evidence"].append(_claim_row(ids[-1])),
            "both detailed and grouped",
            id="detailed_and_grouped_overlap",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0]["evidence_ids"].append(
                "reddit:nonexistent:comment"
            ),
            "unexpected evidence id",
            id="unexpected_evidence_id",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0]["evidence_ids"].pop(),
            "every alias exactly once",
            id="silently_omitted_evidence_id",
        ),
        pytest.param(
            lambda r, ids: r.__setitem__("terminal_groups", []),
            "every alias exactly once",
            id="implicit_remainder",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0].__setitem__(
                "disposition", "claim_bearing"
            ),
            "may only group",
            id="claim_bearing_cannot_be_grouped",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0].__setitem__(
                "disposition", "unresolved"
            ),
            "may only group",
            id="unresolved_cannot_be_grouped",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0].__setitem__(
                "disposition_reason", "  "
            ),
            "lacks an explicit reason",
            id="group_without_reason",
        ),
        pytest.param(
            lambda r, ids: r["terminal_groups"][0].pop("evidence_ids"),
            "list its evidence ids explicitly",
            id="group_without_explicit_ids",
        ),
    ],
)
def test_v5_raw_evidence_id_accounting_fails_closed(mutate, match) -> None:
    bundle = _bundle_v5()
    responses = _v5_responses(bundle)
    ids = bundle["batches"][0]["evidence_ids"]
    mutate(responses[0], ids)
    with pytest.raises(SemanticIntegrationError, match=match):
        validate_batch_responses(bundle, responses)


def test_v5_duplicate_detailed_record_is_not_masked_by_dictionary_collapse() -> None:
    """A repeated detailed id must fail rather than silently collapse to one."""
    bundle = _bundle_v5()
    responses = _v5_responses(bundle, detailed_per_batch=2)
    ids = bundle["batches"][0]["evidence_ids"]
    # Replace a grouped id with a repeat of an already-detailed id so the total
    # occurrence count still equals the expected denominator.
    responses[0]["terminal_groups"][0]["evidence_ids"].pop()
    responses[0]["evidence"].append(_claim_row(ids[0]))
    with pytest.raises(SemanticIntegrationError, match="detailed records"):
        validate_batch_responses(bundle, responses)


def test_v5_rejects_wrong_response_generation_in_both_directions() -> None:
    new_bundle = _bundle_v5()
    legacy_response = deepcopy(_v5_responses(new_bundle)[0])
    legacy_response["schema_version"] = BATCH_RESPONSE_VERSION_V2
    with pytest.raises(SemanticIntegrationError, match="invalid batch response version"):
        validate_batch_responses(new_bundle, [legacy_response], require_all=False)

    legacy_bundle = build_bundle(_source_v3(count=7), max_prompt_bytes=8_000)
    new_response = deepcopy(_v3_batch_responses(legacy_bundle)[0])
    new_response["schema_version"] = BATCH_RESPONSE_VERSION_V3
    with pytest.raises(SemanticIntegrationError, match="invalid batch response version"):
        validate_batch_responses(legacy_bundle, [new_response], require_all=False)


@pytest.mark.parametrize(
    ("method_version", "target_bundle_version", "match"),
    [
        (METHOD_VERSION_V5, BUNDLE_VERSION_V4, "method v5 requires bundle v5"),
        (METHOD_VERSION_V6, BUNDLE_VERSION_V4, "method v6 requires bundle v5"),
        (METHOD_VERSION_V7, BUNDLE_VERSION_V4, "method v7 requires bundle v5"),
        (METHOD_VERSION_V4, BUNDLE_VERSION_V5, "method v4 requires bundle v4"),
        (
            METHOD_VERSION_V3,
            BUNDLE_VERSION_V5,
            "bundle v5 requires a supported semantic method v5 or later",
        ),
        (METHOD_VERSION_V5, BUNDLE_VERSION_V3, "method v5 requires bundle v5"),
    ],
)
def test_incoherent_generation_combinations_fail_closed(
    method_version, target_bundle_version, match
) -> None:
    source = _source_v3(count=3)
    source["semantic_method_version"] = method_version
    with pytest.raises(SemanticIntegrationError, match=match):
        build_bundle(
            source,
            max_prompt_bytes=12_000,
            target_bundle_version=target_bundle_version,
        )


def test_coherent_generations_are_both_accepted() -> None:
    legacy = build_bundle(_source_v3(count=3), max_prompt_bytes=8_000)
    assert legacy["schema_version"] == BUNDLE_VERSION_V4
    assert legacy["method_version"] == METHOD_VERSION_V3
    new = _bundle_v5(count=3)
    assert new["schema_version"] == BUNDLE_VERSION_V5
    assert new["method_version"] == METHOD_VERSION_V5


def test_v5_final_acquisition_still_requires_a_verified_catalog() -> None:
    source = _source_v5(count=3)
    source["corpus_profile"] = "phase_a_final_acquisition"
    with pytest.raises(SemanticIntegrationError, match="lacks product catalog"):
        build_bundle(source, max_prompt_bytes=12_000)
    source["product_identity_catalog"] = _product_catalog()
    bundle = build_bundle(source, max_prompt_bytes=12_000)
    identity = bundle["semantic_work_unit_projection"]["semantic_execution_identity"]
    assert (
        identity["product_identity_catalog_sha256"]
        == bundle["product_identity_catalog"]["catalog_sha256"]
    )


def test_v5_projection_rejects_forged_execution_identity() -> None:
    bundle = _bundle_v5()
    tampered = deepcopy(bundle)
    projection = tampered["semantic_work_unit_projection"]
    projection["semantic_execution_identity"]["prompt_encoding_version"] = (
        "semantic_prompt_encoding_compact_json_v1"
    )
    projection["projection_sha256"] = _canonical_hash(
        {k: v for k, v in projection.items() if k != "projection_sha256"}
    )
    tampered["bundle_sha256"] = _canonical_hash(
        {k: v for k, v in tampered.items() if k != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="prompt_encoding_version"):
        build_batch_prompts(tampered)


def test_v5_projection_rejects_reintroduced_worker_topology() -> None:
    bundle = _bundle_v5()
    tampered = deepcopy(bundle)
    projection = tampered["semantic_work_unit_projection"]
    projection["worker_count"] = 3
    projection["projection_sha256"] = _canonical_hash(
        {k: v for k, v in projection.items() if k != "projection_sha256"}
    )
    tampered["bundle_sha256"] = _canonical_hash(
        {k: v for k, v in tampered.items() if k != "bundle_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="static worker topology"):
        build_batch_prompts(tampered)


def test_reused_bundle_context_cannot_be_applied_to_another_bundle() -> None:
    bundle = _bundle_v5()
    other = _bundle_v5(count=3)
    context = verify_bundle_context(bundle)
    with pytest.raises(SemanticIntegrationError, match="does not match this bundle"):
        validate_batch_responses(
            other, _v5_responses(other), require_all=False, context=context
        )


def test_v5_prepare_runner_writes_no_static_worker_assignment(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = _source_v5(count=7)
    for index in range(7):
        (repo_root / f"thread-{index + 1}.json").write_bytes(
            f"thread-{index + 1}\n".encode("utf-8")
        )
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    result = prepare_batches(
        source_path=source_path,
        repo_root=repo_root,
        bundle_out=tmp_path / "bundle.json",
        prompt_dir=tmp_path / "prompts",
        max_batch_chars=80_000,
        max_prompt_bytes=12_000,
    )
    assert result["model_api_calls"] == 0
    assert not (tmp_path / "prompts" / "worker_assignments.json").exists()
    assert sorted(p.name for p in (tmp_path / "prompts").glob("*")) == ["batch-0001.md"]


def test_v8_prepare_runner_writes_exact_keyed_response_schemas(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = _source_v8(count=7)
    for index in range(7):
        (repo_root / f"thread-{index + 1}.json").write_bytes(
            f"thread-{index + 1}\n".encode("utf-8")
        )
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    bundle_path = tmp_path / "bundle.json"
    result = prepare_batches(
        source_path=source_path,
        repo_root=repo_root,
        bundle_out=bundle_path,
        prompt_dir=tmp_path / "prompts",
        max_batch_chars=80_000,
        max_prompt_bytes=12_000,
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    schema_path = tmp_path / "prompts" / "response-schemas" / "batch-0001.json"
    assert result["response_schema_count"] == len(bundle["batches"])
    assert json.loads(schema_path.read_text(encoding="utf-8")) == (
        build_batch_response_schema(bundle, "batch-0001")
    )


def test_v8_execution_pack_verifies_bound_response_schema(tmp_path: Path) -> None:
    bundle = _bundle_v8(count=40, max_prompt_bytes=12_000)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    pack_dir = tmp_path / "execution-pack"
    result = prepare_prompt_execution_pack(
        bundle_path=bundle_path,
        pack_dir=pack_dir,
    )
    schema_path = pack_dir / "response-schemas" / "batch-0001.json"
    assert result["verification_status"] == "SEMANTIC_PROMPT_EXECUTION_PACK_VERIFIED"
    assert schema_path.is_file()

    tampered = json.loads(schema_path.read_text(encoding="utf-8"))
    tampered["title"] = "wrong schema"
    schema_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="stored response schema batch-0001"):
        verify_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)


def test_v5_execution_pack_reconstructs_every_standalone_prompt_exactly() -> None:
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    prompts = {row["batch_id"]: row["prompt"] for row in build_batch_prompts(bundle)}
    assert len(prompts) > 1

    frame, manifest, payloads = build_prompt_execution_pack(bundle)
    assert manifest["batch_count"] == len(prompts)
    assert frame.count("__FORSETI_BATCH_ID__") == 1
    assert [row["batch_id"] for row in payloads] == [
        row["batch_id"] for row in bundle["batches"]
    ]
    assert {
        evidence_id
        for payload in payloads
        for evidence_id in (
            row["evidence_id"] for row in payload["evidence_batch"]
        )
    } == {row["evidence_id"] for row in bundle["evidence_units"]}
    for payload in payloads:
        assert reconstruct_prompt_execution_payload(frame, payload) == prompts[
            payload["batch_id"]
        ]

    original_bytes = sum(len(prompt.encode("utf-8")) for prompt in prompts.values())
    thin_bytes = len(frame.encode("utf-8")) + sum(
        len(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
        + 1
        for row in payloads
    )
    assert thin_bytes < original_bytes

    tampered = deepcopy(payloads[0])
    tampered["context_table"] = []
    with pytest.raises(SemanticIntegrationError, match="does not match its hash"):
        reconstruct_prompt_execution_payload(frame, tampered)


def test_prepare_prompt_execution_pack_writes_load_once_frame(tmp_path: Path) -> None:
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    pack_dir = tmp_path / "execution-pack"

    result = prepare_prompt_execution_pack(
        bundle_path=bundle_path,
        pack_dir=pack_dir,
    )

    assert result["status"] == "SEMANTIC_PROMPT_EXECUTION_PACK_PREPARED"
    assert result["verification_status"] == "SEMANTIC_PROMPT_EXECUTION_PACK_VERIFIED"
    assert result["batch_count"] == len(bundle["batches"])
    assert result["stored_byte_reduction"] > 0
    assert (pack_dir / "shared-frame.md").is_file()
    assert (pack_dir / "manifest.json").is_file()
    assert len(list((pack_dir / "payloads").glob("batch-*.json"))) == len(
        bundle["batches"]
    )
    with pytest.raises(ValueError, match="existing execution pack"):
        prepare_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)

    first_payload = pack_dir / "payloads" / "batch-0001.json"
    tampered = json.loads(first_payload.read_text(encoding="utf-8"))
    tampered["context_table"] = []
    first_payload.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match bundle"):
        verify_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)


def _prepared_pack(tmp_path: Path) -> tuple[Path, Path]:
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    pack_dir = tmp_path / "execution-pack"
    prepare_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)
    return bundle_path, pack_dir


def test_execution_pack_verification_reads_persisted_frame_bytes(
    tmp_path: Path,
) -> None:
    """A frame whose stored bytes changed must not verify as byte-exact.

    Text-mode reads translate CRLF, so line-ending rewrites in transport would
    otherwise pass while every reconstructed prompt diverged from its hash.
    """
    bundle_path, pack_dir = _prepared_pack(tmp_path)
    frame_path = pack_dir / "shared-frame.md"
    original = frame_path.read_bytes()
    frame_path.write_bytes(original.replace(b"\n", b"\r\n"))
    assert frame_path.read_bytes() != original

    with pytest.raises(ValueError, match="stored execution frame does not match"):
        verify_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)


@pytest.mark.parametrize(
    "relative_path",
    [
        "payloads/stale-batch-0001.json",
        "payloads/superseded/batch-0001.json",
        "leftover-prompt.md",
    ],
)
def test_execution_pack_verification_rejects_unnamed_stored_files(
    tmp_path: Path, relative_path: str
) -> None:
    """A verified pack may hold no file the bundle does not name."""
    bundle_path, pack_dir = _prepared_pack(tmp_path)
    stray = pack_dir / relative_path
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(b'{"stale": true}\n')

    with pytest.raises(ValueError, match="pack file set does not match bundle"):
        verify_prompt_execution_pack(bundle_path=bundle_path, pack_dir=pack_dir)


@pytest.mark.parametrize(
    "escaped",
    ["../escaped-batch", "CON", "batch-0001.", "batch_0001"],
)
def test_execution_pack_refuses_unsafe_batch_id_file_name(
    tmp_path: Path, escaped: str
) -> None:
    """A batch id that is not one safe path component writes nothing."""
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    original_id = bundle["batches"][0]["batch_id"]
    bundle["batches"][0]["batch_id"] = escaped
    for row in bundle["semantic_work_unit_projection"]["work_units"]:
        if row["work_unit_id"] == original_id:
            row["work_unit_id"] = escaped
    for value, field in (
        (bundle["semantic_work_unit_projection"], "projection_sha256"),
        (bundle, "bundle_sha256"),
    ):
        value[field] = _canonical_hash(
            {key: item for key, item in value.items() if key != field}
        )

    with pytest.raises(SemanticIntegrationError, match="not a safe execution pack"):
        build_prompt_execution_pack(bundle)

    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(SemanticIntegrationError, match="not a safe execution pack"):
        prepare_prompt_execution_pack(
            bundle_path=bundle_path, pack_dir=tmp_path / "nested" / "execution-pack"
        )
    assert not (tmp_path / "nested" / "execution-pack").exists()


def test_v5_lineage_must_cover_every_work_unit() -> None:
    """A manifest that names fewer raw artifacts than work units fails closed."""
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    assert len(bundle["batches"]) > 1
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    thinned = deepcopy(compiled)
    manifest = thinned["raw_response_manifest"]
    manifest["responses"] = manifest["responses"][:-1]
    manifest["manifest_sha256"] = _canonical_hash(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    )
    thinned["compilation_sha256"] = _canonical_hash(
        {k: v for k, v in thinned.items() if k != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="does not cover every work unit"):
        prepare_reconciliation_stage(bundle, thinned)


def test_v5_lineage_manifest_hash_is_verified() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    forged = deepcopy(compiled)
    forged["raw_response_manifest"]["responses"][0]["raw_response_sha256"] = "0" * 64
    forged["compilation_sha256"] = _canonical_hash(
        {k: v for k, v in forged.items() if k != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="raw response manifest"):
        prepare_reconciliation_stage(bundle, forged)


def test_v5_lineage_manifest_requires_each_raw_response_hash() -> None:
    """Rehashing a manifest cannot make a missing raw artifact binding valid."""
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    forged = deepcopy(compiled)
    manifest = forged["raw_response_manifest"]
    manifest["responses"][0].pop("raw_response_sha256")
    manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    forged["compilation_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="raw response manifest row"):
        prepare_reconciliation_stage(bundle, forged)


def test_v5_lineage_rejects_duplicate_raw_response_hashes() -> None:
    """Rehashing cannot alias two work units to one raw response artifact."""
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    assert len(bundle["batches"]) > 1
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    forged = deepcopy(compiled)
    manifest = forged["raw_response_manifest"]
    manifest["responses"][1]["raw_response_sha256"] = manifest["responses"][0][
        "raw_response_sha256"
    ]
    manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    forged["compilation_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "compilation_sha256"}
    )
    with pytest.raises(SemanticIntegrationError, match="repeats a digest"):
        prepare_reconciliation_stage(bundle, forged)


def test_v5_reconciliation_carries_posture_and_rejects_customer_proof_early() -> None:
    bundle = _bundle_v5()
    responses = _v5_responses(bundle, detailed_per_batch=7)
    responses[0]["evidence"][0]["semantic_units"][0][
        "evidence_posture"
    ] = "strategy_statement"
    compiled = validate_batch_responses(bundle, responses)
    stage, prompts = prepare_reconciliation_stage(bundle, compiled)

    assert stage["candidates"][0]["evidence_postures"] == ["strategy_statement"]
    assert '"evidence_postures": [' in prompts[0]["prompt"]
    with pytest.raises(
        SemanticIntegrationError,
        match="uses non-experience posture as customer proof",
    ):
        validate_reconciliation_stage(
            bundle,
            stage,
            _group_level_responses(stage, terminal=True),
        )


def test_v5_reconciliation_rejects_incompetent_source_role_before_finalization() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    reconciliation = _group_level_responses(stage, terminal=True)
    reconciliation[0]["semantic_nodes"][0]["claim_kind"] = "observable_fact"

    with pytest.raises(
        SemanticIntegrationError,
        match="uses source roles incompetent for observable_fact",
    ):
        validate_reconciliation_stage(bundle, stage, reconciliation)


def _staged_node_responses(
    stage: dict,
    groups: list[list[tuple[str, str]]],
    *,
    terminal: bool,
    claim_kind: str | None = None,
) -> list[dict]:
    """One node per group with explicit per-child stances, not blanket support."""
    index = {row["candidate_ref"]: row for row in stage["candidates"]}
    responses = []
    for batch in stage["batches"]:
        nodes = []
        for position, group in enumerate(groups):
            selected = [
                (ref, stance) for ref, stance in group if ref in batch["candidate_refs"]
            ]
            if not selected:
                continue
            polarities = {index[ref]["polarity"] for ref, _ in selected}
            nodes.append(
                {
                    "semantic_node_key": f"{batch['batch_id']}-node-{position}",
                    "bounded_meaning": (
                        f"Bounded meaning {position} of {batch['batch_id']}."
                    ),
                    "terminal_proposition": terminal,
                    "claim_kind": claim_kind if terminal else None,
                    "subject_product_ids": ["sf-lbb"],
                    "comparator_product_ids": [],
                    "product_version_ids": [],
                    "axis_ids": ["wear"],
                    "emerging_axis_labels": sorted(
                        {
                            label
                            for ref, _ in selected
                            for label in index[ref]["emerging_axis_labels"]
                        }
                    ),
                    "conditions": sorted(
                        {
                            condition
                            for ref, _ in selected
                            for lineage in index[ref]["condition_lineage"]
                            for condition in lineage["conditions"]
                        }
                    ),
                    "polarity": (
                        next(iter(polarities)) if len(polarities) == 1 else "mixed"
                    ),
                    "uncertainty_posture": "asserted",
                    "child_relations": [
                        {"child_ref": ref, "relation": stance}
                        for ref, stance in selected
                    ],
                    "opposition_checked": True if terminal else None,
                    "causal_ceiling": "descriptive_only" if terminal else None,
                }
            )
        responses.append(
            {
                "schema_version": RECONCILIATION_RESPONSE_VERSION_V2,
                "stage_sha256": stage["stage_sha256"],
                "batch_id": batch["batch_id"],
                "semantic_nodes": nodes,
                "unmerged_children": [],
                "emerging_axis_consolidations": [],
            }
        )
    return responses


def _node_ref_carrying(compilation: dict, unit_ref: str) -> str:
    [node_ref] = [
        row["semantic_node_ref"]
        for row in compilation["semantic_nodes"]
        if any(leaf["semantic_unit_ref"] == unit_ref for leaf in row["leaf_relations"])
    ]
    return node_ref


def _v5_mixed_role_stage() -> tuple[dict, dict, list[str]]:
    """Three claim-bearing units; only the first carries an observable-fact role."""
    source = _source_v5()
    source["captured_items"][0]["source_role"] = "owned_source"
    bundle = build_bundle(source, max_prompt_bytes=12_000)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=3)
    )
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    refs = [row["candidate_ref"] for row in stage["candidates"]]
    assert refs[0].startswith("reddit:t1:comment::")
    assert len(refs) == 3
    return bundle, stage, refs


def test_v5_reconciliation_checks_only_supporting_source_roles_for_competence() -> None:
    bundle, stage, refs = _v5_mixed_role_stage()
    reconciliation = _staged_node_responses(
        stage,
        [[(refs[0], "support"), (refs[1], "counter"), (refs[2], "adjacent")]],
        terminal=True,
        claim_kind="observable_fact",
    )

    terminal = validate_reconciliation_stage(bundle, stage, reconciliation)

    node = terminal["semantic_nodes"][0]
    assert node["claim_kind"] == "observable_fact"
    # The community_post leaves are present and carry the non-support stances,
    # so acceptance is not an artifact of an empty counter/adjacent set.
    assert node["leaf_relations"] == [
        {"semantic_unit_ref": refs[0], "relation": "support"},
        {"semantic_unit_ref": refs[1], "relation": "counter"},
        {"semantic_unit_ref": refs[2], "relation": "adjacent"},
    ]


def test_v5_reconciliation_rejects_incompetent_support_beside_competent_support() -> None:
    bundle, stage, refs = _v5_mixed_role_stage()
    reconciliation = _staged_node_responses(
        stage,
        [[(refs[0], "support"), (refs[1], "support"), (refs[2], "adjacent")]],
        terminal=True,
        claim_kind="observable_fact",
    )

    with pytest.raises(
        SemanticIntegrationError,
        match=r"incompetent for observable_fact: \['community_post'\]",
    ):
        validate_reconciliation_stage(bundle, stage, reconciliation)


def test_v5_reconciliation_composes_relations_before_judging_competence() -> None:
    bundle, stage, refs = _v5_mixed_role_stage()
    level_one = validate_reconciliation_stage(
        bundle,
        stage,
        _staged_node_responses(
            stage,
            [[(refs[0], "support")], [(refs[1], "counter")], [(refs[2], "counter")]],
            terminal=False,
        ),
    )
    stage_two, _ = prepare_reconciliation_stage(bundle, level_one)
    competent = _node_ref_carrying(level_one, refs[0])
    community_one = _node_ref_carrying(level_one, refs[1])
    community_two = _node_ref_carrying(level_one, refs[2])

    # counter x counter composes to support, so the community leaf reaches the
    # terminal claim as support even though level one recorded it as counter.
    with pytest.raises(
        SemanticIntegrationError,
        match=r"incompetent for observable_fact: \['community_post'\]",
    ):
        validate_reconciliation_stage(
            bundle,
            stage_two,
            _staged_node_responses(
                stage_two,
                [
                    [
                        (competent, "support"),
                        (community_one, "counter"),
                        (community_two, "support"),
                    ]
                ],
                terminal=True,
                claim_kind="observable_fact",
            ),
        )

    # support x counter stays counter, so the same community leaves do not
    # contaminate competence when nothing flips them back to support.
    accepted = validate_reconciliation_stage(
        bundle,
        stage_two,
        _staged_node_responses(
            stage_two,
            [
                [
                    (competent, "support"),
                    (community_one, "support"),
                    (community_two, "support"),
                ]
            ],
            terminal=True,
            claim_kind="observable_fact",
        ),
    )

    assert accepted["semantic_nodes"][0]["leaf_relations"] == [
        {"semantic_unit_ref": refs[0], "relation": "support"},
        {"semantic_unit_ref": refs[1], "relation": "counter"},
        {"semantic_unit_ref": refs[2], "relation": "counter"},
    ]


def test_v5_reconciliation_rejects_terminal_node_without_effective_support() -> None:
    bundle, stage, refs = _v5_mixed_role_stage()
    reconciliation = _staged_node_responses(
        stage,
        [[(refs[0], "counter"), (refs[1], "counter"), (refs[2], "adjacent")]],
        terminal=True,
        claim_kind="observable_fact",
    )

    with pytest.raises(SemanticIntegrationError, match="lacks support"):
        validate_reconciliation_stage(bundle, stage, reconciliation)


def test_v5_reconciliation_rejects_ambiguous_leaf_source_lineage() -> None:
    source = _source_v5()
    source["captured_items"][0]["evidence_id"] = "reddit:t1"
    source["captured_items"][1]["evidence_id"] = "reddit:t1::comment"
    bundle = build_bundle(source, max_prompt_bytes=12_000)
    compiled = validate_batch_responses(
        bundle, _v5_responses(bundle, detailed_per_batch=2)
    )
    stage, _ = prepare_reconciliation_stage(bundle, compiled)

    # 'reddit:t1::comment::drying-after-week' decomposes at two '::' boundaries
    # that both name real evidence units, so its owning source is unknowable
    # from the ref alone and must not be resolved by guess.
    with pytest.raises(
        SemanticIntegrationError,
        match=(
            "ambiguous source lineage for "
            "reddit:t1::comment::drying-after-week"
        ),
    ):
        validate_reconciliation_stage(
            bundle, stage, _group_level_responses(stage, terminal=True)
        )


def test_v5_finalization_retains_source_role_competence_backstop() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    terminal = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=True)
    )
    forged = deepcopy(terminal)
    forged["semantic_nodes"][0]["claim_kind"] = "observable_fact"
    _rehash_node_compilation(forged)

    with pytest.raises(
        SemanticIntegrationError,
        match="uses source roles incompetent for observable_fact",
    ):
        finalize_v3_view(bundle, compiled, forged)


def test_policy_v2_finalization_never_promotes_local_opposition_check_to_none_observed() -> None:
    bundle = _bundle_v5()
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    terminal = validate_reconciliation_stage(
        bundle, stage, _group_level_responses(stage, terminal=True)
    )

    assert all(node["opposition_checked"] is True for node in terminal["semantic_nodes"])
    view = finalize_v3_view(bundle, compiled, terminal)

    assert {
        proposition["claim_support"]["conflict_posture"]
        for proposition in view["propositions"]
    } == {"not_checked"}


def test_v5_multi_work_unit_run_accounts_for_every_leaf_once() -> None:
    """Exact denominator coverage across several prompt-bounded work units."""
    bundle = _bundle_v5(count=40, max_prompt_bytes=9_000)
    assert len(bundle["batches"]) > 1
    compiled = validate_batch_responses(bundle, _v5_responses(bundle))
    accounted = [row["evidence_id"] for row in compiled["evidence_dispositions"]]
    assert len(accounted) == 40
    assert sorted(accounted) == sorted(row["evidence_id"] for row in bundle["evidence_units"])
    assert len(compiled["raw_response_manifest"]["responses"]) == len(bundle["batches"])


def test_v5_flows_through_unchanged_v2_downstream_interfaces() -> None:
    """Reconciliation v2, node v2, view v2, and packet v1 consume compilation v3."""
    bundle = _bundle_v5()
    responses = [
        {
            "schema_version": BATCH_RESPONSE_VERSION_V3,
            "bundle_sha256": bundle["bundle_sha256"],
            "batch_id": batch["batch_id"],
            "evidence": [_claim_row(row) for row in batch["evidence_ids"]],
            "terminal_groups": [],
        }
        for batch in bundle["batches"]
    ]
    compiled = validate_batch_responses(bundle, responses)
    assert compiled["schema_version"] == BATCH_COMPILATION_VERSION_V3

    stage_one, prompts_one = prepare_reconciliation_stage(bundle, compiled)
    assert stage_one["emerging_axis_owner_batch_id"] == stage_one["batches"][0][
        "batch_id"
    ]
    assert all('"leaf_relations"' not in row["prompt"] for row in prompts_one)
    assert all('"condition_lineage"' not in row["prompt"] for row in prompts_one)
    level_one = validate_reconciliation_stage(
        bundle, stage_one, _group_level_responses(stage_one, terminal=False)
    )
    stage_two, prompts_two = prepare_reconciliation_stage(bundle, level_one)
    assert stage_two["emerging_axis_owner_batch_id"] == stage_two["batches"][0][
        "batch_id"
    ]
    assert all('"leaf_relations"' not in row["prompt"] for row in prompts_two)
    assert all('"condition_lineage"' not in row["prompt"] for row in prompts_two)
    level_two = validate_reconciliation_stage(
        bundle, stage_two, _group_level_responses(stage_two, terminal=True)
    )
    assert level_one["schema_version"] == "semantic_evidence_node_compilation_v2"

    view = finalize_v3_view(bundle, compiled, level_two)
    assert view["schema_version"] == "semantic_evidence_integration_view_v2"
    packet = project_evidence_packet(
        view, bundle, compiled, level_two, axis_ids=["wear"]
    )
    assert packet["schema_version"] == EVIDENCE_PACKET_VERSION
    # Lineage still resolves to the new compilation generation, unmodified.
    assert packet["source_bindings"]["compilation_sha256"] == (
        compiled["compilation_sha256"]
    )
    assert packet["source_bindings"]["bundle_sha256"] == bundle["bundle_sha256"]
    evidence_rows = _packet_v3_evidence_rows(packet)
    assert evidence_rows
    assert all("product_context" not in row for row in evidence_rows)
    assert all("parent_context" not in row for row in evidence_rows)
    assert all("product_context_refs" not in row for row in evidence_rows)
    assert all("parent_context_refs" not in row for row in evidence_rows)
    assert packet["full_evidence_resolution"] == {
        "source": "bound_semantic_evidence_bundle",
        "lookup_key": "evidence_id",
        "bundle_sha256": bundle["bundle_sha256"],
        "body_field": "text",
        "context_fields": ["product_context", "parent_context"],
    }
    assert packet["model_api_calls"] == 0
