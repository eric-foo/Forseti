from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from judgment.semantic_evidence_integration import (
    BATCH_RESPONSE_VERSION,
    BATCH_RESPONSE_VERSION_V2,
    BUNDLE_VERSION,
    BUNDLE_VERSION_V2,
    BUNDLE_VERSION_V3,
    BUNDLE_VERSION_V4,
    EVIDENCE_PACKET_VERSION,
    METHOD_VERSION,
    METHOD_VERSION_V2,
    METHOD_VERSION_V3,
    RECONCILIATION_RESPONSE_VERSION,
    RECONCILIATION_RESPONSE_VERSION_V2,
    SOURCE_VERSION_V2,
    SOURCE_VERSION_V3,
    SemanticIntegrationError,
    build_batch_prompts,
    build_bundle,
    build_reconciliation_prompt,
    finalize_view,
    finalize_v3_view,
    materialize_source_v3,
    project_evidence_packet,
    prepare_reconciliation_stage,
    validate_batch_responses,
    validate_reconciliation_stage,
)
from runners.run_semantic_evidence_integration import (
    prepare_batches,
    publish_batch_response_file,
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
    assert len({row["evidence_id"] for row in packet["evidence"]}) == 7
    assert len(packet["containers"]) == 7
    linked_unit = packet["evidence"][0]["proposition_relations"][0][
        "semantic_units"
    ][0]
    assert {
        "evidence_posture",
        "uncertainty_posture",
        "polarity",
    } <= set(linked_unit)
    assert all("conclusion" not in row for row in packet["propositions"])
    assert all("recommendation" not in row for row in packet["propositions"])
    assert packet["model_api_calls"] == 0


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
    view = load("view.json")

    packet = project_evidence_packet(
        view, bundle, compiled, terminal, axis_ids=["reaction_and_breakout"]
    )

    assert packet["selection_coverage"]["selected_proposition_count"] == 17
    assert packet["selection_coverage"]["returned_evidence_item_count"] == 44
    assert len({row["evidence_id"] for row in packet["evidence"]}) == 44
    assert len(packet["containers"]) == 30
    per_proposition_links = sum(
        sum(row["evidence_item_counts"].values())
        for row in packet["propositions"]
    )
    assert per_proposition_links > 44


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
    assert packet["unresolved_axis_candidates"][0]["evidence"][
        "evidence_id"
    ] == unresolved_evidence_id


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

    assert result["batch_count"] == 4
    assert assignment["worker_count"] == 3
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
    assert finalize_v3_view(bundle, compiled, nodes_two) == load("view.json")

    sensitivity = load("partition_sensitivity.json")
    assert isinstance(sensitivity, dict)
    assert sensitivity["partitions_differ"] is True
    assert sensitivity["flattened_membership_and_counts_equal"] is True
