from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from judgment.phase_a_evidence_consumer import EvidenceConsumerError
from judgment.phase_a_evidence_selection import (
    BATCHED_QUOTE_MANIFEST_VERSION,
    DISPLAY_LABEL_BY_REASON_CODE,
    PARENT_CONTEXT_POLICY,
    SELECTION_SPEC_VERSION,
    VALUE_REASON_RELATIONS,
    _candidate_rows,
    _bucket_priority,
    _display_label,
    _numeric_engagement,
    _policy_guidance,
    _publication_time_value,
    _publication_year,
    _relation_prompt_envelope,
    _relation_schema,
    _select_groups,
    _source_venue,
    _temporal_display_priority,
    _truth_row_display_eligible,
    _validate_relation_response,
    build_customer_pull_point_frontier,
    finalize_batched_preselection_relation_confirmations_prepare_quotes,
    finalize_preselection_relation_confirmation_prepare_quotes,
    finalize_batched_relations_prepare_quotes,
    finalize_quotes as _finalize_quotes_runtime,
    finalize_relations_prepare_quotes,
    prepare_evidence_selection,
    prepare_evidence_selection_batches,
    prepare_batched_preselection_relation_confirmations,
    prepare_preselection_relation_confirmation,
    prepare_selected_relation_confirmation,
    selection_spec_from_customer_pull_frontier,
    verify_customer_pull_point_frontier,
)
from runners.run_semantic_evidence_integration import (
    _parser,
    build_customer_pull_point_frontier_run,
    finalize_batched_preselection_relation_confirmation_run,
    finalize_evidence_selection_batches_run,
    finalize_evidence_selection_quotes_run,
    finalize_evidence_selection_relations_run,
    materialize_customer_pull_point_selection_spec_run,
    prepare_evidence_selection_batches_run,
    prepare_evidence_selection_run,
    prepare_batched_preselection_relation_confirmation_run,
)


def _canonical_hash(value: object) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _packet_and_bundle(count: int = 14) -> tuple[dict, dict]:
    semantic_columns = [
        "semantic_unit_ref",
        "statement",
        "evidence_posture",
        "uncertainty_posture",
        "polarity",
        "subject_product_ids",
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
        "independence_posture",
        "independence_key",
        "public_identity_key",
        "engagement",
        "semantic_units",
    ]
    groups = []
    bundle_units = []
    roles = [
        ("reddit_community", "community_post", "score_state", "reddit.com"),
        ("retailer_review", "retailer_review", "positive_helpful_count", "sephora.com"),
        ("retailer_review", "retailer_review", "positive_helpful_count", "amazon.com"),
        ("creator_social", "audience_comment", "comment_diggs", "tiktok.com"),
        ("creator_social", "creator_authored", "video_diggs", "tiktok.com"),
    ]
    rows_by_role: dict[tuple[str, str, str, str], list[list]] = {role: [] for role in roles}
    unmerged = []
    for index in range(count):
        role = roles[index % len(roles)]
        family, source_role, _, domain = role
        evidence_id = f"{source_role}:{index}"
        semantic_ref = f"{evidence_id}::hydration"
        condition = ["after use"] if index % 4 else ["overnight"]
        statement = (
            f"Customer report {index} says the balm feels moisturizing."
            if source_role != "creator_authored"
            else f"Creator post {index} presents the balm as moisturizing."
        )
        engagement = [
            "engagement_available",
            f"{100-index} points" if source_role == "community_post" else 100 - index,
            "2026-08-18T00:00:00Z",
            index % 3 != 0,
        ]
        semantic = [
            semantic_ref,
            statement,
            "first_hand" if source_role != "creator_authored" else "creator_claim",
            "asserted",
            "affirmed",
            ["summer-fridays-lip-butter-balm"],
            [],
            "hydration_and_moisture texture_and_skin_finish" if index == 0 else ["hydration_and_moisture"],
            condition,
            [],
        ]
        row = [
            evidence_id,
            f"artifact:{index}",
            f"https://{domain}/evidence/{index}",
            f"container:{index}",
            "2026-08-17T00:00:00Z",
            f"actor:{index}",
            "credited",
            f"origin:{index}",
            f"public:{index}",
            engagement,
            [semantic],
        ]
        rows_by_role[role].append(row)
        unmerged.append({"evidence_id": evidence_id, "semantic_unit_ref": semantic_ref, "reason": "retained"})
        bundle_units.append(
            {
                "evidence_id": evidence_id,
                "source_artifact_id": f"artifact:{index}",
                "source_ref": f"https://{domain}/evidence/{index}",
                "text": f"Opening context. This balm feels moisturizing after use number {index}. Closing context.",
            }
        )
    for (family, source_role, engagement_kind, _), rows in rows_by_role.items():
        if not rows:
            continue
        groups.append(
            {
                "source_family": family,
                "source_role": source_role,
                "engagement_kind": engagement_kind,
                "engagement_context": "source-native metric",
                "evidence_defaults": {},
                "evidence_columns": evidence_columns,
                "engagement_defaults": {},
                "engagement_columns": ["status", "raw_value", "observed_at", "material_positive"],
                "evidence_rows": rows,
            }
        )
    bundle = {
        "schema_version": "semantic_evidence_bundle_v5",
        "evidence_units": bundle_units,
    }
    bundle["bundle_sha256"] = _canonical_hash(bundle)
    packet = {
        "schema_version": "phase_a_evidence_packet_v3",
        "selection": {"mode": "axis", "axis_ids": ["hydration_and_moisture"], "proposition_ids": []},
        "source_bindings": {"bundle_sha256": bundle["bundle_sha256"], "corpus_sha256": "c" * 64},
        "catalogue_schema": {
            "semantic_unit_defaults": {},
            "semantic_unit_columns": semantic_columns,
            "relation_link_columns": ["evidence_id", "semantic_unit_refs"],
        },
        "propositions": [],
        "source_groups": groups,
        "containers": [],
        "unmerged_axis_candidates": unmerged,
        "unscoped_unmerged_candidates": [],
        "unresolved_axis_candidates": [],
        "full_evidence_resolution": {"bundle_sha256": bundle["bundle_sha256"], "body_field": "text"},
        "model_api_calls": 0,
    }
    packet["packet_sha256"] = _canonical_hash(packet)
    return packet, bundle


def _spec(count: int = 14) -> dict:
    # Nominate only evidence the fixture actually emits: an unresolvable
    # nomination is now a closed boundary, not a silently ignored line.
    protected: dict[str, list[str]] = {"safety": ["community_post:0"]}
    if count > 6:
        protected["costly_behavior"] = ["retailer_review:6"]
    return {
        "schema_version": SELECTION_SPEC_VERSION,
        "selection_id": "hydration-pilot",
        "bounded_claim": "The balm provides immediate hydration after use.",
        "axis_ids": ["hydration_and_moisture"],
        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
        "sources": [],
        "protected_evidence_ids": protected,
    }


def _write_source(tmp_path: Path, count: int = 14) -> tuple[dict, list[dict]]:
    packet, bundle = _packet_and_bundle(count)
    packet_path = tmp_path / "packet.json"
    bundle_path = tmp_path / "bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    source = {
        "source_id": "full-corpus",
        "packet_path": packet_path,
        "bundle_path": bundle_path,
        "packet": packet,
        "bundle": bundle,
    }
    return _spec(count), [source]


def _reseal(source: dict) -> None:
    """Re-hash a source after an intentional body edit, then rewrite both files."""
    bundle = source["bundle"]
    bundle.pop("bundle_sha256", None)
    bundle["bundle_sha256"] = _canonical_hash(bundle)
    packet = source["packet"]
    packet["source_bindings"]["bundle_sha256"] = bundle["bundle_sha256"]
    packet["full_evidence_resolution"]["bundle_sha256"] = bundle["bundle_sha256"]
    packet.pop("packet_sha256", None)
    packet["packet_sha256"] = _canonical_hash(packet)
    source["packet_path"].write_text(json.dumps(packet), encoding="utf-8")
    source["bundle_path"].write_text(json.dumps(bundle), encoding="utf-8")


def _attach_parent_context(source: dict, evidence_id: str, text: str) -> str:
    unit = next(
        row for row in source["bundle"]["evidence_units"] if row["evidence_id"] == evidence_id
    )
    context_id = "context:shared-parent"
    unit["parent_context_refs"] = [context_id]
    source["bundle"]["semantic_work_unit_projection"] = {
        "context_registry": [
            {
                "context_id": context_id,
                "context_type": "parent_text",
                "source_artifact_id": unit["source_artifact_id"],
                "source_ref": "https://reddit.com/thread/parent",
                "text": text,
            }
        ]
    }
    _reseal(source)
    return context_id


def _relation_response(candidates: list[dict]) -> dict:
    rows = []
    for index, candidate in enumerate(candidates):
        if candidate["layer"] == "influence_context":
            relation = "adjacent"
        elif index % 4 == 0:
            relation = "counter"
        else:
            relation = "support"
        rows.append({"candidate_id": candidate["candidate_id"], "relation": relation, "reason_code": "bounded_meaning"})
    return {"results": rows}


def _positional_relation_response(candidates: list[dict]) -> dict:
    literal = _relation_response(candidates)["results"]
    return {
        "results_by_candidate_row": {
            f"row_{index:04d}": row["relation"]
            for index, row in enumerate(literal)
        }
    }


def _batched_positional_relation_response(candidates: list[dict], batch_id: str) -> dict:
    return {**_positional_relation_response(candidates), "batch_id": batch_id}


def _proposition_packet_for_frontier() -> dict:
    packet, _ = _packet_and_bundle(10)
    propositions = [
        {
            "proposition_id": "point-retailer",
            "bounded_proposition": "Customers say the balm is worth buying again.",
            "claim_kind": "customer_experience",
            "axis_ids": ["value_and_quantity"],
            "subject_product_ids": ["summer-fridays-lip-butter-balm"],
            "product_version_ids": [],
            "conditions": [],
            "evidence_item_counts": {"support": 1, "counter": 1, "adjacent": 0},
            "evidence_relations": {
                "support": [["retailer_review:1", ["retailer_review:1::hydration"]]],
                "counter": [["community_post:0", ["community_post:0::hydration"]]],
                "adjacent": [],
            },
        },
        {
            "proposition_id": "point-community-behavior",
            "bounded_proposition": "Customers report buying the balm repeatedly.",
            "claim_kind": "reported_behavior",
            "axis_ids": ["value_and_quantity"],
            "subject_product_ids": ["summer-fridays-lip-butter-balm"],
            "product_version_ids": [],
            "conditions": [],
            "evidence_item_counts": {"support": 1, "counter": 0, "adjacent": 0},
            "evidence_relations": {
                "support": [["community_post:5", ["community_post:5::hydration"]]],
                "counter": [],
                "adjacent": [],
            },
        },
        {
            "proposition_id": "point-creator-only",
            "bounded_proposition": "A creator presents the balm as desirable.",
            "claim_kind": "customer_experience",
            "axis_ids": ["hype_originality_and_trust"],
            "subject_product_ids": ["summer-fridays-lip-butter-balm"],
            "product_version_ids": [],
            "conditions": [],
            "evidence_item_counts": {"support": 1, "counter": 0, "adjacent": 0},
            "evidence_relations": {
                "support": [["creator_authored:4", ["creator_authored:4::hydration"]]],
                "counter": [],
                "adjacent": [],
            },
        },
    ]
    packet["selection"] = {
        "mode": "proposition",
        "axis_ids": ["value_and_quantity", "hype_originality_and_trust"],
        "proposition_ids": [row["proposition_id"] for row in propositions],
    }
    packet["selection_coverage"] = {
        "truncated": False,
        "selected_proposition_count": len(propositions),
    }
    packet["propositions"] = propositions
    packet.pop("packet_sha256")
    packet["packet_sha256"] = _canonical_hash(packet)
    return packet


def test_customer_pull_frontier_is_retailer_first_not_retailer_only_and_accounts_all_points() -> None:
    packet = _proposition_packet_for_frontier()

    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="summer-fridays-commercial-points",
        business_question="Which customer-valued strengths and objections deserve commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )

    verify_customer_pull_point_frontier(frontier, packet)
    assert [row["proposition_id"] for row in frontier["retailer_first_queue"]] == [
        "point-retailer"
    ]
    assert [row["proposition_id"] for row in frontier["community_discovery_queue"]] == [
        "point-community-behavior"
    ]
    assert "reported_behavior" in frontier["community_discovery_queue"][0][
        "earning_reasons"
    ]
    assert frontier["nonpromoted_points"] == [
        {
            "proposition_id": "point-creator-only",
            "disposition": "no_customer_truth_support_in_bound_packet",
        }
    ]
    accounted = {
        row["proposition_id"]
        for key in (
            "retailer_first_queue",
            "community_discovery_queue",
            "nonpromoted_points",
        )
        for row in frontier[key]
    }
    assert accounted == set(packet["selection"]["proposition_ids"])
    assert frontier["subject_filtered_proposition_ids"] == []
    assert frontier["accounting"]["input_proposition_count"] == 3
    assert frontier["accounting"]["subject_filtered_count"] == 0
    assert frontier["customer_pull_policy"]["retailer_is_admission_gate"] is False
    assert frontier["customer_pull_policy"]["cross_platform_score"] is None
    assert build_customer_pull_point_frontier(
        packet,
        frontier_id="summer-fridays-commercial-points",
        business_question=frontier["business_question"],
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    ) == frontier


def _frontier_point(proposition_id: str, claim_kind: str, support: list[str]) -> dict:
    return {
        "proposition_id": proposition_id,
        "bounded_proposition": f"Customers report the balm behaves as {proposition_id}.",
        "claim_kind": claim_kind,
        "axis_ids": ["value_and_quantity"],
        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
        "product_version_ids": [],
        "conditions": [],
        "evidence_item_counts": {"support": len(support), "counter": 0, "adjacent": 0},
        "evidence_relations": {
            "support": [
                [evidence_id, [f"{evidence_id}::hydration"]]
                for evidence_id in support
            ],
            "counter": [],
            "adjacent": [],
        },
    }


def _frontier_packet_for(propositions: list[dict], count: int = 25) -> dict:
    packet, _ = _packet_and_bundle(count)
    packet["selection"] = {
        "mode": "proposition",
        "axis_ids": ["value_and_quantity"],
        "proposition_ids": [row["proposition_id"] for row in propositions],
    }
    packet["selection_coverage"] = {
        "truncated": False,
        "selected_proposition_count": len(propositions),
    }
    packet["propositions"] = propositions
    packet.pop("packet_sha256")
    packet["packet_sha256"] = _canonical_hash(packet)
    return packet


def test_customer_pull_frontier_orders_real_queues_by_evidence_then_behavior() -> None:
    packet = _frontier_packet_for(
        [
            _frontier_point(
                "retailer-deeper",
                "customer_experience",
                [
                    "retailer_review:1",
                    "retailer_review:2",
                    "retailer_review:6",
                    "retailer_review:7",
                ],
            ),
            _frontier_point(
                "retailer-cross-role",
                "customer_experience",
                ["community_post:5", "retailer_review:1"],
            ),
            _frontier_point(
                "stronger",
                "customer_experience",
                [
                    "community_post:0",
                    "community_post:5",
                    "community_post:10",
                    "community_post:15",
                ],
            ),
            _frontier_point(
                "weaker-behavior",
                "reported_behavior",
                ["community_post:5", "community_post:10"],
            ),
            _frontier_point(
                "equal", "customer_experience", ["community_post:5", "community_post:15"]
            ),
            _frontier_point(
                "equal-behavior",
                "reported_behavior",
                ["community_post:5", "community_post:15"],
            ),
        ]
    )

    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="strength-before-behavior",
        business_question="Which customer points deserve commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )

    verify_customer_pull_point_frontier(frontier, packet)
    assert [row["proposition_id"] for row in frontier["retailer_first_queue"]] == [
        "retailer-deeper",
        "retailer-cross-role",
    ]
    assert [
        row["proposition_id"] for row in frontier["community_discovery_queue"]
    ] == [
        "stronger",
        "weaker-behavior",
        "equal-behavior",
        "equal",
    ]


def test_customer_pull_frontier_denies_material_credit_to_unavailable_engagement() -> None:
    packet = _frontier_packet_for(
        [_frontier_point("quiet-point", "customer_experience", ["community_post:quiet"])]
    )
    packet["source_groups"].append(
        {
            "source_family": "reddit_community",
            "source_role": "community_post",
            "engagement_kind": "engagement_unavailable",
            "engagement_context": "unavailable",
            "evidence_defaults": {},
            "evidence_columns": packet["source_groups"][0]["evidence_columns"],
            "engagement_defaults": {"material_positive": True},
            "engagement_columns": ["status"],
            "evidence_rows": [
                [
                    "community_post:quiet",
                    "artifact:quiet",
                    "https://reddit.com/evidence/quiet",
                    "container:quiet",
                    "2026-08-17T00:00:00Z",
                    "actor:quiet",
                    "credited",
                    "origin:quiet",
                    "public:quiet",
                    ["engagement_unavailable"],
                    [
                        [
                            "community_post:quiet::hydration",
                            "Customer report quiet says the balm feels moisturizing.",
                            "first_hand",
                            "asserted",
                            "affirmed",
                            ["summer-fridays-lip-butter-balm"],
                            [],
                            ["hydration_and_moisture"],
                            ["after use"],
                            [],
                        ]
                    ],
                ]
            ],
        }
    )
    packet.pop("packet_sha256")
    packet["packet_sha256"] = _canonical_hash(packet)

    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="unavailable-engagement",
        business_question="Which customer points deserve commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )

    verify_customer_pull_point_frontier(frontier, packet)
    assert frontier["community_discovery_queue"] == []
    assert frontier["nonpromoted_points"] == [
        {
            "proposition_id": "quiet-point",
            "disposition": "no_investigation_earning_signal",
        }
    ]


def test_customer_pull_frontier_exposes_subject_filtered_propositions() -> None:
    packet = _proposition_packet_for_frontier()
    other = copy.deepcopy(packet["propositions"][0])
    other["proposition_id"] = "point-other-product"
    other["subject_product_ids"] = ["another-product"]
    packet["propositions"].append(other)
    packet["selection"]["proposition_ids"].append(other["proposition_id"])
    packet["selection_coverage"]["selected_proposition_count"] += 1
    packet.pop("packet_sha256")
    packet["packet_sha256"] = _canonical_hash(packet)

    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="subject-scoped-frontier",
        business_question="Which points merit commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )

    verify_customer_pull_point_frontier(frontier, packet)
    assert frontier["subject_filtered_proposition_ids"] == ["point-other-product"]
    assert frontier["accounting"] == {
        "input_proposition_count": 4,
        "considered_proposition_count": 3,
        "subject_filtered_count": 1,
        "retailer_first_count": 1,
        "community_discovery_count": 1,
        "nonpromoted_count": 1,
    }

    hidden = copy.deepcopy(frontier)
    hidden["subject_filtered_proposition_ids"] = []
    hidden["accounting"]["subject_filtered_count"] = 0
    hidden["frontier_sha256"] = _canonical_hash(
        {key: value for key, value in hidden.items() if key != "frontier_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        verify_customer_pull_point_frontier(hidden, packet)
    assert caught.value.boundary == "customer_pull_frontier_accounting"


def test_customer_pull_frontier_binding_and_materialized_point_spec_fail_closed() -> None:
    packet = _proposition_packet_for_frontier()
    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="frontier",
        business_question="Which points merit commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )
    spec = selection_spec_from_customer_pull_frontier(
        frontier, packet, "point-community-behavior"
    )
    assert spec["truth_group_cap"] == 13
    assert spec["bounded_claim"] == "Customers report buying the balm repeatedly."
    assert spec["customer_pull_frontier_binding"]["queue"] == "community_discovery_queue"

    tampered = copy.deepcopy(frontier)
    tampered["retailer_first_queue"][0]["bounded_point"] = "Edited point"
    with pytest.raises(EvidenceConsumerError) as caught:
        verify_customer_pull_point_frontier(tampered, packet)
    assert caught.value.boundary == "customer_pull_frontier_verification"

    retailer_only = copy.deepcopy(frontier)
    retailer_only["community_discovery_queue"] = []
    retailer_only["frontier_sha256"] = _canonical_hash(
        {key: value for key, value in retailer_only.items() if key != "frontier_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        verify_customer_pull_point_frontier(retailer_only, packet)
    assert caught.value.boundary == "customer_pull_frontier_accounting"


def test_non_value_frontier_point_admits_its_complete_axis_with_bound_recency_policy() -> None:
    packet = _proposition_packet_for_frontier()
    hydration = {
        "proposition_id": "point-hydration",
        "bounded_proposition": "Customers report that the balm hydrates their lips.",
        "claim_kind": "customer_experience",
        "axis_ids": ["hydration_and_moisture"],
        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
        "product_version_ids": [],
        "conditions": [],
        "evidence_item_counts": {"support": 1, "counter": 0, "adjacent": 0},
        "evidence_relations": {
            "support": [["community_post:5", ["community_post:5::hydration"]]],
            "counter": [],
            "adjacent": [],
        },
    }
    packet["propositions"].append(hydration)
    packet["selection"]["axis_ids"].append("hydration_and_moisture")
    packet["selection"]["proposition_ids"].append("point-hydration")
    packet["selection_coverage"]["selected_proposition_count"] += 1
    packet.pop("packet_sha256")
    packet["packet_sha256"] = _canonical_hash(packet)
    frontier = build_customer_pull_point_frontier(
        packet,
        frontier_id="frontier",
        business_question="Which points merit commercial investigation?",
        subject_product_ids=["summer-fridays-lip-butter-balm"],
    )
    spec = selection_spec_from_customer_pull_frontier(
        frontier, packet, "point-hydration"
    )
    _, bundle = _packet_and_bundle(10)
    sources = [
        {
            "source_id": "full-corpus",
            "packet_path": Path("packet.json"),
            "bundle_path": Path("bundle.json"),
            "packet": packet,
            "bundle": bundle,
        }
    ]

    assert spec["axis_ids"] == ["hydration_and_moisture"]
    assert spec["relation_response_mode"] == "positional"
    assert spec["temporal_presentation_policy"] == "recent_year_coverage_v1"
    assert len(_candidate_rows(sources, spec)) == 10

    tampered = copy.deepcopy(spec)
    tampered["axis_ids"] = ["texture_and_skin_finish"]
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(tampered, sources)
    assert caught.value.boundary == "customer_pull_frontier_binding"

    tampered = copy.deepcopy(spec)
    tampered.pop("temporal_presentation_policy")
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(tampered, sources)
    assert caught.value.boundary == "customer_pull_frontier_binding"


def test_recent_year_policy_changes_display_only_and_keeps_an_older_anchor(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 40)
    candidates = _candidate_rows(sources, spec)
    labeled = []
    years = (2023, 2024, 2025, 2026)
    for index, candidate in enumerate(candidates):
        row = dict(candidate)
        row["publication_time"] = f"{years[index % 4]}-06-01T00:00:00Z"
        row["engagement_material_positive"] = True
        row["relation"] = "counter" if index % 5 == 0 else "support"
        row["reason_code"] = "bounded_meaning"
        labeled.append(row)

    selected = _select_groups(
        labeled,
        "truth_support",
        13,
        temporal_policy="recent_year_coverage_v1",
    )
    displayed_years = {
        int(row["publication_time"][:4])
        for row in selected
        if row["publication_time"] is not None
    }

    assert {2025, 2026} <= displayed_years
    assert displayed_years & {2023, 2024}
    assert len({row["origin_group_id"] for row in selected}) == 13



def test_relation_prompt_and_corroboration_ignore_date_and_engagement(
    tmp_path: Path,
) -> None:
    """Presentation metadata cannot enter relation or origin corroboration."""
    spec, sources = _write_source(tmp_path, 10)
    original = []
    for index, candidate in enumerate(_candidate_rows(sources, spec)):
        original.append(
            dict(
                candidate,
                publication_time=f"202{3 + index % 4}-06-01T00:00:00Z",
                engagement_raw_value=index,
                engagement_material_positive=True,
                relation="counter" if index % 4 == 0 else "support",
                reason_code="bounded_meaning",
            )
        )
    mutated = [
        dict(
            row,
            publication_time=f"202{6 - index % 4}-07-02T00:00:00Z",
            engagement_raw_value=1000 - index,
            engagement_observed_at="2030-01-01T00:00:00Z",
        )
        for index, row in enumerate(original)
    ]

    # These fields are absent from the provider-visible relation envelope, so
    # the model cannot award truth or direction from age or engagement.
    assert _relation_prompt_envelope(spec, original) == _relation_prompt_envelope(
        spec, mutated
    )

    original_selected = _select_groups(
        original,
        "truth_support",
        13,
        temporal_policy="recent_year_coverage_v1",
    )
    mutated_selected = _select_groups(
        mutated,
        "truth_support",
        13,
        temporal_policy="recent_year_coverage_v1",
    )

    def _corroboration(rows: list[dict]) -> dict[str, tuple]:
        return {
            row["origin_group_id"]: (
                row["origin_candidate_count"],
                tuple(row["origin_relations"]),
                tuple(row["origin_candidate_ids"]),
            )
            for row in rows
        }

    assert _corroboration(original_selected) == _corroboration(mutated_selected)


def test_linked_parent_context_is_exact_compact_and_hash_bound(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 5)
    spec["admit_semantic_refs"] = [
        {
            "source_id": "full-corpus",
            "semantic_unit_ref": "community_post:0::hydration",
        }
    ]
    parent_text = (
        "Summer Fridays left my lips unbearably dry and cracked after two days."
    )
    context_id = _attach_parent_context(
        sources[0], "community_post:0", parent_text
    )

    prompt, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    row = next(
        candidate
        for candidate in candidates
        if candidate["evidence_id"] == "community_post:0"
    )

    assert manifest["parent_context_policy"] == PARENT_CONTEXT_POLICY
    assert row["parent_context"] == [
        {
            "context_id": f"full-corpus::{context_id}",
            "source_ref": "https://reddit.com/thread/parent",
            "text": parent_text,
        }
    ]
    assert all(
        not candidate["parent_context"]
        for candidate in candidates
        if candidate["semantic_unit_ref"]
        != "community_post:0::hydration"
    )
    envelope = json.loads(prompt.split("SELECTION_ENVELOPE_JSON:\n", 1)[1])
    assert envelope["parent_context_columns"] == [
        "parent_context_id",
        "source_ref",
        "parent_text",
    ]
    assert envelope["parent_context_rows"] == [
        [
            f"full-corpus::{context_id}",
            "https://reddit.com/thread/parent",
            parent_text,
        ]
    ]
    candidate_index = envelope["candidate_columns"].index("parent_context_ids")
    assert any(
        candidate_row[candidate_index] == [f"full-corpus::{context_id}"]
        for candidate_row in envelope["candidate_rows"]
    )
    assert prompt.count(parent_text) == 1
    assert "otherwise do not inherit the missing meaning" in prompt

    first_pass = _relation_response(candidates)
    preselection_prompt, _, _ = prepare_preselection_relation_confirmation(
        manifest, sources, first_pass
    )
    assert preselection_prompt.count(parent_text) == 1
    assert '"point_parent_context_ids"' in preselection_prompt
    assert '"parent_context_ids"' in preselection_prompt
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, first_pass
    )
    selected_prompt, _, _ = prepare_selected_relation_confirmation(quote_manifest)
    assert selected_prompt.count(parent_text) == 1
    assert '"point_parent_context_ids"' in selected_prompt
    assert '"parent_context_ids"' in selected_prompt

    legacy_candidates = _candidate_rows(
        sources, spec, include_parent_context=False
    )
    legacy_manifest = copy.deepcopy(manifest)
    legacy_manifest.pop("parent_context_policy")
    legacy_manifest["candidate_inventory_sha256"] = _canonical_hash(
        legacy_candidates
    )
    legacy_manifest["manifest_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in legacy_manifest.items()
            if key != "manifest_sha256"
        }
    )
    _, _, legacy_quote_manifest = finalize_relations_prepare_quotes(
        legacy_manifest, sources, _relation_response(legacy_candidates)
    )
    assert all(
        "parent_context" not in row
        for row in legacy_quote_manifest["selected_rows"]
    )


def test_linked_parent_context_reaches_every_scope_batch_without_row_laundering(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["admit_semantic_refs"] = [
        {
            "source_id": "full-corpus",
            "semantic_unit_ref": "audience_comment:3::hydration",
        }
    ]
    spec["relation_response_mode"] = "positional"
    spec["relation_policy"] = "bounded_point"
    parent_text = "The balm did nothing to hydrate my lips overnight."
    context_id = _attach_parent_context(
        sources[0], "audience_comment:3", parent_text
    )
    full_context_id = f"full-corpus::{context_id}"

    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=3
    )
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _batched_positional_relation_response(
            subset, batch["batch_id"]
        )

    _, prompts = prepare_batched_preselection_relation_confirmations(
        batch_manifest, sources, responses, batch_size=1
    )
    row_context_links = 0
    for prompt, _ in prompts:
        envelope = json.loads(
            prompt.split(
                "PRESELECTION_RELATION_CONFIRMATION_BATCH_ENVELOPE_JSON:\n", 1
            )[1]
        )
        assert envelope["point_parent_context_ids"] == [full_context_id]
        assert envelope["parent_context_rows"] == [
            [
                full_context_id,
                "https://reddit.com/thread/parent",
                parent_text,
            ]
        ]
        assert prompt.count(parent_text) == 1
        if "parent_context_ids" in envelope["candidate_columns"]:
            context_index = envelope["candidate_columns"].index(
                "parent_context_ids"
            )
            row_context_links += sum(
                row[context_index] == [full_context_id]
                for row in envelope["candidate_rows"]
            )
    # This exact child is outside the material/protected confirmation frontier.
    # Its parent may still clarify the bounded point, but cannot be attached to
    # any different candidate row in these batches.
    assert row_context_links == 0

    _, _, selection_manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        selection_manifest, sources, _positional_relation_response(candidates)
    )
    assert all(
        row["semantic_unit_ref"] != "audience_comment:3::hydration"
        for row in quote_manifest["selected_rows"]
    )
    selected_prompt, _, _ = prepare_selected_relation_confirmation(quote_manifest)
    assert selected_prompt.count(parent_text) == 1
    selected_envelope = json.loads(
        selected_prompt.split(
            "SELECTED_RELATION_CONFIRMATION_ENVELOPE_JSON:\n", 1
        )[1]
    )
    assert selected_envelope["point_parent_context_ids"] == [full_context_id]
    assert "parent_context_ids" not in selected_envelope["selected_columns"]


def test_linked_parent_context_fails_closed_on_unknown_or_wrong_artifact(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 5)
    spec["admit_semantic_refs"] = [
        {
            "source_id": "full-corpus",
            "semantic_unit_ref": "community_post:0::hydration",
        }
    ]
    context_id = _attach_parent_context(
        sources[0], "community_post:0", "The parent names one exact outcome."
    )
    registry = sources[0]["bundle"]["semantic_work_unit_projection"][
        "context_registry"
    ]
    registry[0]["source_artifact_id"] = "another-artifact"
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "parent_context_resolution"

    registry[0]["source_artifact_id"] = "artifact:0"
    unit = next(
        row
        for row in sources[0]["bundle"]["evidence_units"]
        if row["evidence_id"] == "community_post:0"
    )
    unit["parent_context_refs"] = [f"{context_id}:missing"]
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "parent_context_resolution"

def test_year_derivation_matches_admitted_publication_time_shapes() -> None:
    """A publication time the consumer admits must not read back as undated."""
    basic_format = "20260601T000000+00:00"
    assert _publication_time_value(basic_format) == basic_format
    assert _publication_year({"publication_time": basic_format}) == 2026
    assert _publication_year({"publication_time": "2026-06-01T00:00:00Z"}) == 2026
    assert _publication_year({"publication_time": "2026-05-13"}) == 2026
    assert _publication_year({"publication_time": None}) is None
    assert _publication_year({"publication_time": "not-a-date"}) is None


def test_temporal_display_order_never_reads_unavailable_engagement_as_zero() -> None:
    """Missing engagement is not zero engagement, even for display order."""

    def _row(selected_id: str, raw_value: object, kind: str = "score_state") -> dict:
        return {
            "selected_id": selected_id,
            "publication_time": "2026-06-01T00:00:00Z",
            "engagement_kind": kind,
            "engagement_raw_value": raw_value,
        }

    downvoted = _row("row-negative", -5)
    unavailable = _row("row-unavailable", None, "engagement_unavailable")
    zero = _row("row-zero", 0)
    ordered = sorted(
        [unavailable, downvoted, zero], key=_temporal_display_priority
    )

    assert [row["selected_id"] for row in ordered] == [
        "row-zero",
        "row-negative",
        "row-unavailable",
    ]


def test_basic_format_dated_rows_reach_recent_year_coverage(tmp_path: Path) -> None:
    """Recency must see every admitted date shape, not one text spelling."""
    spec, sources = _write_source(tmp_path, 40)
    candidates = _candidate_rows(sources, spec)
    years = (2023, 2024, 2025, 2026)
    labeled = []
    for index, candidate in enumerate(candidates):
        row = dict(candidate)
        row["publication_time"] = f"{years[index % 4]}0601T000000+00:00"
        row["engagement_material_positive"] = True
        row["relation"] = "counter" if index % 5 == 0 else "support"
        row["reason_code"] = "bounded_meaning"
        labeled.append(row)

    selected = _select_groups(
        labeled,
        "truth_support",
        13,
        temporal_policy="recent_year_coverage_v1",
    )

    assert {2025, 2026} <= {_publication_year(row) for row in selected}


def test_temporal_policy_rejects_value_first_selection(tmp_path: Path) -> None:
    spec, sources = _value_axis_source(tmp_path)
    spec["temporal_presentation_policy"] = "recent_year_coverage_v1"

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)

    assert caught.value.boundary == "selection_spec"
    assert "only for non-value" in str(caught.value)


def test_customer_pull_frontier_runner_materializes_a_cold_point_spec(
    tmp_path: Path,
) -> None:
    packet = _proposition_packet_for_frontier()
    _, bundle = _packet_and_bundle(10)
    packet_path = tmp_path / "packet.json"
    bundle_path = tmp_path / "bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    frontier_spec_path = tmp_path / "frontier-spec.json"
    frontier_spec_path.write_text(
        json.dumps(
            {
                "packet_path": str(packet_path),
                "frontier_id": "frontier",
                "business_question": "Which points merit commercial investigation?",
                "subject_product_ids": ["summer-fridays-lip-butter-balm"],
                "source_id": "full-corpus",
            }
        ),
        encoding="utf-8",
    )
    frontier_path = tmp_path / "frontier.json"
    result = build_customer_pull_point_frontier_run(
        spec_path=frontier_spec_path, frontier_out=frontier_path
    )
    point_spec_path = tmp_path / "point-spec.json"
    materialized = materialize_customer_pull_point_selection_spec_run(
        frontier_path=frontier_path,
        packet_path=packet_path,
        bundle_path=bundle_path,
        proposition_id="point-community-behavior",
        spec_out=point_spec_path,
    )
    point_spec = json.loads(point_spec_path.read_text(encoding="utf-8"))
    assert result["status"] == "PHASE_A_CUSTOMER_PULL_POINT_FRONTIER_READY"
    assert materialized["truth_group_cap"] == 13
    assert point_spec["sources"][0]["source_id"] == "full-corpus"
    assert point_spec["relation_policy"] == "bounded_point"
    prepared = prepare_evidence_selection_run(
        spec_path=point_spec_path,
        prompt_out=tmp_path / "point-prompt.txt",
        response_schema_out=tmp_path / "point-schema.json",
        manifest_out=tmp_path / "point-manifest.json",
    )
    assert prepared["candidate_count"] == 1
    assert "VALUE-BOX POLICY" not in (tmp_path / "point-prompt.txt").read_text(
        encoding="utf-8"
    )
    point_prompt = (tmp_path / "point-prompt.txt").read_text(encoding="utf-8")
    assert "Support directly supports the bounded claim." in point_prompt
    assert _parser().parse_args(
        [
            "prepare-preselection-relation-confirmation",
            "--selection-manifest",
            "selection.json",
            "--first-response",
            "response.json",
            "--prompt-out",
            "prompt.txt",
            "--response-schema-out",
            "schema.json",
            "--confirmation-manifest-out",
            "confirmation.json",
        ]
    ).command == "prepare-preselection-relation-confirmation"


def test_preselection_confirmation_recovers_material_candidate_before_cap_selection(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    _, _, selection_manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    first_pass = _relation_response(candidates)
    recovered = next(
        row
        for row in candidates
        if row["layer"] == "truth_support"
        and row["engagement_material_positive"] is True
        and not row["protected_lanes"]
    )
    first_row = next(
        row for row in first_pass["results"] if row["candidate_id"] == recovered["candidate_id"]
    )
    first_row["relation"] = "exclude"
    first_row["reason_code"] = "wrong_scope"

    prompt, schema, confirmation_manifest = prepare_preselection_relation_confirmation(
        selection_manifest, sources, first_pass
    )
    assert recovered["candidate_id"] in confirmation_manifest["confirmation_candidate_ids"]
    assert recovered["candidate_id"] not in prompt
    assert schema["required"] == [
        "point_scope",
        "point_scope_reason",
        "relation_checks",
    ]
    original_by_id = {
        row["candidate_id"]: row for row in _validate_relation_response(candidates, first_pass)
    }
    response = {
        "point_scope": "single_point",
        "point_scope_reason": "One direction-bearing hydration point.",
        "relation_checks": [],
    }
    for row_id, candidate_id in zip(
        confirmation_manifest["confirmation_row_ids"],
        confirmation_manifest["confirmation_candidate_ids"],
        strict=True,
    ):
        relation = "support" if candidate_id == recovered["candidate_id"] else original_by_id[candidate_id]["relation"]
        response["relation_checks"].append(
            {
                "confirmation_row_id": row_id,
                "relation": relation,
                "reason_code": "matching_customer_experience" if relation == "support" else (
                    "differing_customer_experience" if relation == "counter" else (
                        "related_customer_context" if relation == "adjacent" else "wrong_scope_or_non_evidence"
                    )
                ),
            }
        )

    _, _, quote_manifest = finalize_preselection_relation_confirmation_prepare_quotes(
        selection_manifest,
        sources,
        first_pass,
        confirmation_manifest,
        response,
    )
    assert recovered["candidate_id"] in {
        row["candidate_id"] for row in quote_manifest["selected_rows"]
    }
    assert quote_manifest["preselection_relation_confirmation"]["status"] == "passed"
    assert quote_manifest["selected_relation_confirmation_required"] is False
    artifact = _finalize_quotes_runtime(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )
    assert artifact["relation_confirmation_status"] == "passed"
    assert artifact["point_scope_confirmation_reason"] == response[
        "point_scope_reason"
    ]
    assert recovered["candidate_id"] in {
        row["candidate_id"] for row in artifact["candidate_dispositions"]
        if row["relation"] == "support"
    }
    forged = copy.deepcopy(quote_manifest)
    forged_confirmation_manifest = forged["preselection_replay"][
        "confirmation_manifest"
    ]
    forged_index = next(
        index
        for index, candidate_id in enumerate(
            forged_confirmation_manifest["confirmation_candidate_ids"]
        )
        if not original_by_id[candidate_id]["protected_lanes"]
    )
    forged["preselection_replay"]["confirmation_response"]["relation_checks"][forged_index][
        "relation"
    ] = "exclude"
    forged["preselection_replay"]["confirmation_response"]["relation_checks"][forged_index][
        "reason_code"
    ] = "wrong_scope_or_non_evidence"
    forged["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "manifest_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(forged, sources, _quote_response(forged, sources))
    assert caught.value.boundary == "manifest_verification"

    missing = copy.deepcopy(response)
    missing["relation_checks"].pop()
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_preselection_relation_confirmation_prepare_quotes(
            selection_manifest,
            sources,
            first_pass,
            confirmation_manifest,
            missing,
        )
    assert caught.value.boundary == "missing_relation_confirmation"


def test_preselection_confirmation_reapplies_first_pass_row_guards(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    _, _, selection_manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    first_pass = _relation_response(candidates)
    _, _, confirmation_manifest = prepare_preselection_relation_confirmation(
        selection_manifest, sources, first_pass
    )
    original_by_id = {
        row["candidate_id"]: row
        for row in _validate_relation_response(candidates, first_pass)
    }
    reason_by_relation = {
        "support": "matching_customer_experience",
        "counter": "differing_customer_experience",
        "adjacent": "related_customer_context",
        "exclude": "wrong_scope_or_non_evidence",
    }

    def _confirmation(overrides: dict[str, tuple[str, str]]) -> dict:
        checks = []
        for row_id, candidate_id in zip(
            confirmation_manifest["confirmation_row_ids"],
            confirmation_manifest["confirmation_candidate_ids"],
            strict=True,
        ):
            relation = original_by_id[candidate_id]["relation"]
            relation, reason_code = overrides.get(
                candidate_id, (relation, reason_by_relation[relation])
            )
            checks.append(
                {
                    "confirmation_row_id": row_id,
                    "relation": relation,
                    "reason_code": reason_code,
                }
            )
        return {
            "point_scope": "single_point",
            "point_scope_reason": "One direction-bearing hydration point.",
            "relation_checks": checks,
        }

    creator_id = next(
        row["candidate_id"]
        for row in candidates
        if row["layer"] == "influence_context"
        and row["candidate_id"] in confirmation_manifest["confirmation_candidate_ids"]
    )
    truth_id = next(
        row["candidate_id"]
        for row in candidates
        if row["layer"] == "truth_support"
        and row["candidate_id"] in confirmation_manifest["confirmation_candidate_ids"]
    )

    for overrides, boundary in (
        (
            {creator_id: ("support", "matching_customer_experience")},
            "creator_customer_laundering",
        ),
        ({truth_id: ("adjacent", "adjacent_to_the_claim")}, "reason_code_relation_leak"),
        (
            {truth_id: ("adjacent", "a" + "_bcde" * 30)},
            "relation_confirmation_shape",
        ),
    ):
        with pytest.raises(EvidenceConsumerError) as caught:
            finalize_preselection_relation_confirmation_prepare_quotes(
                selection_manifest,
                sources,
                first_pass,
                confirmation_manifest,
                _confirmation(overrides),
            )
        assert caught.value.boundary == boundary

    laundered_first_pass = copy.deepcopy(first_pass)
    for row in laundered_first_pass["results"]:
        if row["candidate_id"] == creator_id:
            row["relation"] = "support"
    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_relation_response(candidates, laundered_first_pass)
    assert caught.value.boundary == "creator_customer_laundering"


def test_missing_packet_publication_time_is_rehydrated_from_hash_bound_reddit_source(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, count=1)
    source = sources[0]
    packet = source["packet"]
    bundle = source["bundle"]
    evidence_columns = packet["source_groups"][0]["evidence_columns"]
    evidence_row = packet["source_groups"][0]["evidence_rows"][0]
    semantic_columns = packet["catalogue_schema"]["semantic_unit_columns"]
    semantic_row = evidence_row[evidence_columns.index("semantic_units")][0]
    old_ref = semantic_row[semantic_columns.index("semantic_unit_ref")]
    new_evidence_id = "reddit:abc:post"
    new_semantic_ref = "reddit:abc:post::hydration"
    evidence_row[evidence_columns.index("evidence_id")] = new_evidence_id
    evidence_row[evidence_columns.index("source_artifact_id")] = "reddit_source_abc"
    evidence_row[evidence_columns.index("source_ref")] = (
        "https://www.reddit.com/r/test/comments/abc/example/"
    )
    evidence_row[evidence_columns.index("publication_time")] = None
    semantic_row[semantic_columns.index("semantic_unit_ref")] = new_semantic_ref
    packet["unmerged_axis_candidates"][0]["evidence_id"] = new_evidence_id
    packet["unmerged_axis_candidates"][0]["semantic_unit_ref"] = new_semantic_ref
    raw_path = tmp_path / "reddit_content_record.json"
    raw_path.write_text(
        json.dumps(
            {
                "post": {
                    "body_text": "This balm feels moisturizing after use number 0.",
                    "timestamp_state": "2026-07-29T08:17:00+0000",
                },
                "comments": [],
            }
        ),
        encoding="utf-8",
    )
    bundle["evidence_units"][0].update(
        {
            "evidence_id": new_evidence_id,
            "source_artifact_id": "reddit_source_abc",
            "source_ref": "https://www.reddit.com/r/test/comments/abc/example/",
        }
    )
    bundle["source_artifacts"] = [
        {
            "artifact_id": "reddit_source_abc",
            "locator": str(raw_path),
            "sha256": __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest(),
        }
    ]
    spec["protected_evidence_ids"] = {"safety": [new_evidence_id]}
    assert old_ref != new_semantic_ref
    _reseal(source)

    candidates = _candidate_rows(sources, spec)

    assert candidates[0]["publication_time"] == "2026-07-29T08:17:00+0000"
    raw_path.write_text("{}", encoding="utf-8")
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "publication_time_source_hash"


def test_hash_bound_unsupported_source_format_leaves_publication_time_unavailable(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, count=1)
    source = sources[0]
    packet = source["packet"]
    bundle = source["bundle"]
    evidence_columns = packet["source_groups"][0]["evidence_columns"]
    evidence_row = packet["source_groups"][0]["evidence_rows"][0]
    evidence_id = evidence_row[evidence_columns.index("evidence_id")]
    evidence_row[evidence_columns.index("publication_time")] = None
    evidence_row[evidence_columns.index("source_artifact_id")] = "legacy_binary_source"
    raw_path = tmp_path / "legacy_response.bin"
    raw_path.write_bytes(b"not a supported JSON source artifact")
    bundle["evidence_units"][0]["source_artifact_id"] = "legacy_binary_source"
    bundle["source_artifacts"] = [
        {
            "artifact_id": "legacy_binary_source",
            "locator": str(raw_path),
            "sha256": __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest(),
        }
    ]
    _reseal(source)

    candidates = _candidate_rows(sources, spec)

    assert next(row for row in candidates if row["evidence_id"] == evidence_id)[
        "publication_time"
    ] is None


def _quote_response(quote_manifest: dict, sources: list[dict]) -> dict:
    bodies = {
        row["evidence_id"]: row["text"]
        for row in sources[0]["bundle"]["evidence_units"]
    }
    provider_ids = set(
        quote_manifest.get(
            "provider_selected_ids",
            [row["selected_id"] for row in quote_manifest["selected_rows"]],
        )
    )
    return {
        "quotes": [
            {
                "selected_id": row["selected_id"],
                "quote_status": "quote_available",
                "exact_quote": (
                    bodies[row["evidence_id"]][:220]
                    if len(bodies[row["evidence_id"]]) <= 220
                    else bodies[row["evidence_id"]][:220].rsplit(".", 1)[0] + "."
                ),
            }
            for row in quote_manifest["selected_rows"]
            if row["selected_id"] in provider_ids
        ]
    }


def _confirmation_response(
    quote_manifest: dict,
    *,
    point_scope: str = "single_point",
    point_scope_reason: str = "One product attribute and direction under one compatible condition set.",
) -> dict:
    """Build a confirmation response that agrees with every first-pass label.

    This is a transport fixture, not evidence of an independent second pass:
    it copies the first-pass relation by construction.  Independence is a
    property of the emitted prompt, which
    `test_selected_relation_confirmation_hides_first_pass_labels_and_rejects_flip`
    checks directly.
    """
    _, _, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )
    relation_by_selected_id = {
        row["selected_id"]: row["relation"]
        for row in quote_manifest["selected_rows"]
    }
    return {
        "point_scope": point_scope,
        "point_scope_reason": point_scope_reason,
        "relation_checks": [
            {
                "confirmation_row_id": confirmation_row_id,
                "relation": relation_by_selected_id[selected_id],
            }
            for confirmation_row_id, selected_id in zip(
                confirmation_manifest["confirmation_row_ids"],
                confirmation_manifest["confirmation_row_selected_ids"],
                strict=True,
            )
        ]
    }


# This shadows the imported module function on purpose so the tests that
# predate the confirmation gate keep exercising the full v6 path.  A test that
# needs the real signature calls `_finalize_quotes_runtime` instead.
def finalize_quotes(quote_manifest: dict, sources: list[dict], response: dict) -> dict:
    _, _, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )
    return _finalize_quotes_runtime(
        quote_manifest,
        sources,
        response,
        confirmation_manifest,
        _confirmation_response(quote_manifest),
    )


def test_selection_round_trip_accounts_every_candidate_separates_creator_and_caps_origins(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path)
    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    relation_response = _relation_response(candidates)

    quote_prompt, quote_schema, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, relation_response
    )
    artifact = finalize_quotes(quote_manifest, sources, _quote_response(quote_manifest, sources))

    assert len(candidates) == 14
    assert artifact["candidate_count"] == 14
    assert len(artifact["candidate_dispositions"]) == 14
    assert artifact["truth_group_count"] <= 13
    assert artifact["influence_group_count"] <= 3
    assert all(
        row["relation"] == "adjacent"
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["layer"] == "influence_context"
    )
    assert any(group["group_key"].endswith("::amazon") for group in artifact["source_groups"])
    assert "every candidate_id exactly once" in prompt
    assert "Support directly supports the bounded claim." not in prompt
    assert "contiguous exact substring" in quote_prompt
    assert "Do not start the quote with an unresolved pronoun" in quote_prompt
    assert "Product identity may rely on the evidence row" in quote_prompt
    assert "every material component" in quote_prompt
    assert "Do not optimize for brevity" in quote_prompt
    assert "silently locate the source wording" in quote_prompt
    assert "optional non-reversing context is not enough" in quote_prompt
    assert schema["required"] == ["results"]
    assert quote_schema["required"] == ["quotes"]


def test_default_point_pack_caps_at_thirteen_and_discloses_pool(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 40)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(candidates)
    )

    artifact = finalize_quotes(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )

    assert artifact["schema_version"] == "phase_a_evidence_selection_artifact_v2"
    assert artifact["point_id"] == spec["selection_id"]
    assert artifact["bounded_point"] == spec["bounded_claim"]
    assert artifact["truth_group_cap"] == 13
    assert artifact["truth_group_count"] == 13
    assert artifact["relation_confirmation_status"] == "passed"
    disclosure = artifact["selection_disclosure"]
    assert disclosure["candidate_semantic_row_count"] == 40
    assert disclosure["candidate_evidence_item_count"] == 40
    assert disclosure["candidate_truth_origin_count"] == 32
    assert disclosure["display_eligible_truth_origin_count"] == 23
    assert disclosure["displayed_truth_origin_count"] == 13
    assert disclosure["displayed_row_count"] == sum(
        len(group["rows"]) for group in artifact["source_groups"]
    )
    assert artifact["point_scope_confirmation_status"] == "passed"
    assert artifact["point_scope_confirmation_reason"]
    assert any(
        basis.startswith("one externally scope-confirmed evidence point")
        and "broad axis or bundled claim fails" in basis
        for basis in disclosure["presentation_basis"]
    )
    # The disclosed candidate pool is larger than the pool the cap chose from,
    # so the basis has to name the display-eligibility gate that drops the rest.
    assert any(
        "material positive source-native engagement is never displayed" in basis
        for basis in disclosure["presentation_basis"]
    )


def test_selected_relation_confirmation_hides_first_pass_labels_and_rejects_flip(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 14)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )

    prompt, schema, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )
    envelope = json.loads(
        prompt.split("SELECTED_RELATION_CONFIRMATION_ENVELOPE_JSON:\n", 1)[1]
    )
    assert envelope["selected_columns"] == [
        "confirmation_row_id",
        "normalized_meaning",
        "conditions",
        "subject_product_ids",
        "product_version_ids",
        "source_role",
        "same_evidence_companion_meanings",
    ]
    assert schema["required"] == [
        "point_scope",
        "point_scope_reason",
        "relation_checks",
    ]
    assert confirmation_manifest["hidden_first_pass_fields"] == [
        "relation",
        "reason_code",
        "display_label",
        "engagement",
        "selection_priority",
    ]
    # `selection_priority` is only genuinely hidden if the presented order is
    # not the selection order.  Selection order leads with the protected and
    # reserved support/counter origins and always trails with the adjacent
    # creator-influence block, so presenting rows in that order would hand the
    # confirming workload the priority the manifest claims to withhold.
    selection_order = [row["selected_id"] for row in quote_manifest["selected_rows"]]
    assert len(selection_order) > 3
    assert confirmation_manifest["confirmation_row_selected_ids"] != selection_order
    assert sorted(confirmation_manifest["confirmation_row_selected_ids"]) == sorted(
        selection_order
    )
    assert confirmation_manifest["confirmation_row_ids"] == [
        f"row_{index:02d}" for index in range(1, len(selection_order) + 1)
    ]
    assert not any(
        selected_id in prompt for selected_id in selection_order
    ), "the confirmation prompt must not carry first-pass selected_id handles"
    # A second preparation of the same bound manifest reproduces the presented
    # order exactly, so the de-correlated order stays replayable.
    assert (
        prepare_selected_relation_confirmation(quote_manifest)[2]
        == confirmation_manifest
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            _quote_response(quote_manifest, sources),
        )
    assert caught.value.boundary == "selected_relation_confirmation_required"

    flipped = _confirmation_response(quote_manifest)
    flipped["relation_checks"][0]["relation"] = (
        "counter"
        if flipped["relation_checks"][0]["relation"] == "support"
        else "support"
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            _quote_response(quote_manifest, sources),
            confirmation_manifest,
            flipped,
        )
    assert caught.value.boundary == "selected_relation_disagreement"

    missing = _confirmation_response(quote_manifest)
    missing["relation_checks"].pop()
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            _quote_response(quote_manifest, sources),
            confirmation_manifest,
            missing,
        )
    assert caught.value.boundary == "missing_relation_confirmation"

    rebound = copy.deepcopy(confirmation_manifest)
    rebound["quote_manifest_sha256"] = "0" * 64
    rebound["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in rebound.items() if key != "manifest_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            _quote_response(quote_manifest, sources),
            rebound,
            _confirmation_response(quote_manifest),
        )
    assert caught.value.boundary == "manifest_verification"


def test_selected_relation_confirmation_rejects_a_broad_axis_as_a_point(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 14)
    spec["bounded_claim"] = "Customers report hydration experiences with the balm."
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    _, _, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            _quote_response(quote_manifest, sources),
            confirmation_manifest,
            _confirmation_response(
                quote_manifest,
                point_scope="broad_axis_or_bundle",
                point_scope_reason="The claim names an experience area without one direction-bearing outcome.",
            ),
        )
    assert caught.value.boundary == "bounded_point_not_confirmed"


def test_selected_relation_confirmation_rejects_duplicate_foreign_and_reordered_rows(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 14)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    _, _, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )
    quote_response = _quote_response(quote_manifest, sources)

    def _finalize(confirmation_response: dict) -> None:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            quote_response,
            confirmation_manifest,
            confirmation_response,
        )

    duplicated = _confirmation_response(quote_manifest)
    duplicated["relation_checks"][1] = copy.deepcopy(
        duplicated["relation_checks"][0]
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize(duplicated)
    assert caught.value.boundary == "duplicate_relation_confirmation"

    foreign = _confirmation_response(quote_manifest)
    foreign["relation_checks"][0]["confirmation_row_id"] = "row_99"
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize(foreign)
    assert caught.value.boundary == "foreign_relation_confirmation"

    reordered = _confirmation_response(quote_manifest)
    reordered["relation_checks"].reverse()
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize(reordered)
    assert caught.value.boundary == "relation_confirmation_order_mismatch"

    # A confirmation manifest whose recorded prompt hash does not belong to the
    # prompt this quote manifest actually produces is rejected, so a
    # hand-written manifest cannot vouch for a workload that saw the labels.
    forged = copy.deepcopy(confirmation_manifest)
    forged["prompt_sha256"] = "0" * 64
    forged["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in forged.items() if key != "manifest_sha256"}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            quote_manifest,
            sources,
            quote_response,
            forged,
            _confirmation_response(quote_manifest),
        )
    assert caught.value.boundary == "manifest_verification"


def test_historical_quote_manifests_reject_and_never_require_confirmation(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 14)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    _, _, confirmation_manifest = prepare_selected_relation_confirmation(
        quote_manifest
    )
    confirmation_response = _confirmation_response(quote_manifest)

    historical = copy.deepcopy(quote_manifest)
    for key in (
        "selection_id",
        "bounded_claim",
        "selected_relation_confirmation_required",
        "manifest_sha256",
    ):
        historical.pop(key)
    historical["schema_version"] = "phase_a_evidence_quote_manifest_v4"
    historical["manifest_sha256"] = _canonical_hash(historical)

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_selected_relation_confirmation(historical)
    assert caught.value.boundary == "relation_confirmation_not_required"

    with pytest.raises(EvidenceConsumerError) as caught:
        _finalize_quotes_runtime(
            historical,
            sources,
            _quote_response(historical, sources),
            confirmation_manifest,
            confirmation_response,
        )
    assert caught.value.boundary == "unexpected_relation_confirmation"

    artifact = _finalize_quotes_runtime(
        historical, sources, _quote_response(historical, sources)
    )
    assert artifact["schema_version"] == "phase_a_evidence_selection_artifact_v1"
    assert "selection_disclosure" not in artifact


def test_quotes_runner_replays_a_historical_manifest_without_confirmation(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 14)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    for key in (
        "selection_id",
        "bounded_claim",
        "selected_relation_confirmation_required",
        "manifest_sha256",
    ):
        quote_manifest.pop(key)
    quote_manifest["schema_version"] = "phase_a_evidence_quote_manifest_v4"
    quote_manifest["manifest_sha256"] = _canonical_hash(quote_manifest)

    manifest_path = tmp_path / "selection-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    quote_manifest_path = tmp_path / "historical-quote-manifest.json"
    quote_manifest_path.write_text(json.dumps(quote_manifest), encoding="utf-8")
    response_path = tmp_path / "historical-quote-response.json"
    response_path.write_text(
        json.dumps(_quote_response(quote_manifest, sources)), encoding="utf-8"
    )
    artifact_path = tmp_path / "historical-artifact.json"

    completed = finalize_evidence_selection_quotes_run(
        selection_manifest_path=manifest_path,
        quote_manifest_path=quote_manifest_path,
        response_path=response_path,
        confirmation_manifest_path=None,
        confirmation_response_path=None,
        artifact_out=artifact_path,
    )

    assert completed["status"] == "PHASE_A_EVIDENCE_SELECTION_COMPLETE"
    assert (
        json.loads(artifact_path.read_text())["schema_version"]
        == "phase_a_evidence_selection_artifact_v1"
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_evidence_selection_quotes_run(
            selection_manifest_path=manifest_path,
            quote_manifest_path=quote_manifest_path,
            response_path=response_path,
            confirmation_manifest_path=tmp_path / "confirmation-manifest.json",
            confirmation_response_path=None,
            artifact_out=tmp_path / "unused-artifact.json",
        )
    assert caught.value.boundary == "relation_confirmation_shape"

    parsed = _parser().parse_args(
        [
            "finalize-evidence-selection-quotes",
            "--selection-manifest",
            str(manifest_path),
            "--quote-manifest",
            str(quote_manifest_path),
            "--response",
            str(response_path),
            "--artifact-out",
            str(tmp_path / "parser-artifact.json"),
        ]
    )
    assert parsed.confirmation_manifest is None
    assert parsed.confirmation_response is None


def test_selection_spec_can_raise_truth_origin_cap_to_twenty_without_changing_influence_cap(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 40)
    spec["truth_group_cap"] = 20
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)

    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(candidates)
    )
    artifact = finalize_quotes(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )

    assert artifact["truth_group_cap"] == 20
    assert artifact["truth_group_count"] == 20
    assert artifact["influence_group_count"] <= 3


def test_positional_relation_mode_rehydrates_candidate_identity_without_returning_ids(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)

    assert "Do not return candidate IDs" in prompt
    assert schema["required"] == ["results_by_candidate_row"]
    row_schema = schema["properties"]["results_by_candidate_row"]
    assert row_schema["required"] == [
        f"row_{index:04d}" for index in range(len(candidates))
    ]
    assert row_schema["properties"]["row_0000"]["enum"] == [
        "support",
        "counter",
        "adjacent",
        "exclude",
    ]

    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _positional_relation_response(candidates)
    )

    assert [row["candidate_id"] for row in quote_manifest["labeled_inventory"]] == [
        row["candidate_id"] for row in candidates
    ]
    assert {
        row["reason_code"] for row in quote_manifest["labeled_inventory"]
    } <= {
        "matching_customer_experience",
        "differing_customer_experience",
        "related_customer_context",
        "wrong_scope_or_non_evidence",
    }


def test_positional_relation_mode_rejects_missing_row_at_identity_boundary(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"].pop("row_0007")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "missing_candidate_result"


def test_positional_relation_mode_rejects_substituted_row_key_at_identity_boundary(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"]["row_9999"] = response[
        "results_by_candidate_row"
    ].pop("row_0001")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "missing_candidate_result"


def test_batched_positional_relations_rehydrate_the_same_full_inventory(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    batch_manifest, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=7
    )
    candidates = _candidate_rows(sources, spec)
    full_response = _positional_relation_response(candidates)
    responses = {}
    for batch, (prompt, schema) in zip(
        batch_manifest["batches"], prompts_and_schemas, strict=True
    ):
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = {
            "batch_id": batch["batch_id"],
            "results_by_candidate_row": {
                f"row_{local_index:04d}": full_response[
                    "results_by_candidate_row"
                ][f"row_{start + local_index:04d}"]
                for local_index in range(len(subset))
            },
        }
        assert "Do not return candidate IDs" in prompt
        assert schema["required"] == ["results_by_candidate_row", "batch_id"]
        assert schema["properties"]["batch_id"]["enum"] == [batch["batch_id"]]

    _, _, batched_quote_manifest = finalize_batched_relations_prepare_quotes(
        batch_manifest, sources, responses
    )
    _, _, unbatched_manifest = prepare_evidence_selection(spec, sources)
    _, _, unbatched_quote_manifest = finalize_relations_prepare_quotes(
        unbatched_manifest, sources, full_response
    )

    assert [row["candidate_count"] for row in batch_manifest["batches"]] == [7, 7, 6]
    assert batched_quote_manifest["labeled_inventory"] == unbatched_quote_manifest[
        "labeled_inventory"
    ]
    assert batched_quote_manifest["selected_rows"] == unbatched_quote_manifest[
        "selected_rows"
    ]
    assert batched_quote_manifest["relation_transport"] == {
        "mode": "named_positional_batches",
        "batch_manifest_sha256": batch_manifest["manifest_sha256"],
        "batch_count": 3,
        "batch_response_sha256": {
            batch_id: _canonical_hash(response)
            for batch_id, response in responses.items()
        },
    }
    assert batched_quote_manifest["schema_version"] == BATCHED_QUOTE_MANIFEST_VERSION
    assert "relation_transport" not in unbatched_quote_manifest
    batched_artifact = finalize_quotes(
        batched_quote_manifest,
        sources,
        _quote_response(batched_quote_manifest, sources),
    )
    unbatched_artifact = finalize_quotes(
        unbatched_quote_manifest,
        sources,
        _quote_response(unbatched_quote_manifest, sources),
    )
    assert batched_artifact["source_groups"] == unbatched_artifact["source_groups"]


def test_batched_frontier_route_confirms_before_cap_and_replays_exactly(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    spec["relation_policy"] = "bounded_point"
    spec["temporal_presentation_policy"] = "recent_year_coverage_v1"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=7
    )
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        response = _batched_positional_relation_response(subset, batch["batch_id"])
        responses[batch["batch_id"]] = response

    confirmation_manifest, confirmation_prompts = (
        prepare_batched_preselection_relation_confirmations(
            batch_manifest, sources, responses, batch_size=5
        )
    )
    reason_by_relation = {
        "support": "matching_customer_experience",
        "counter": "differing_customer_experience",
        "adjacent": "related_customer_context",
        "exclude": "wrong_scope_or_non_evidence",
    }
    confirmation_responses = {}
    for batch, (prompt, _) in zip(
        confirmation_manifest["batches"], confirmation_prompts, strict=True
    ):
        envelope = json.loads(
            prompt.split(
                "PRESELECTION_RELATION_CONFIRMATION_BATCH_ENVELOPE_JSON:\n", 1
            )[1]
        )
        checks = []
        for row in envelope["candidate_rows"]:
            relation = "adjacent" if row[5] == "creator_authored" else "support"
            checks.append(
                {
                    "confirmation_row_id": row[0],
                    "relation": relation,
                    "reason_code": reason_by_relation[relation],
                }
            )
        confirmation_responses[batch["batch_id"]] = {
            "batch_id": batch["batch_id"],
            "point_scope": "single_point",
            "point_scope_reason": "One direction-bearing hydration point.",
            "relation_checks": checks,
        }
    _, _, quote_manifest = (
        finalize_batched_preselection_relation_confirmations_prepare_quotes(
            batch_manifest,
            sources,
            responses,
            confirmation_manifest,
            confirmation_responses,
        )
    )
    artifact = _finalize_quotes_runtime(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )

    assert quote_manifest["schema_version"].endswith("_v7")
    assert quote_manifest["relation_transport"]["mode"] == "named_positional_batches"
    assert quote_manifest["preselection_relation_confirmation"]["status"] == "passed"
    assert artifact["candidate_count"] == 20
    assert artifact["timeline"]
    assert artifact["selection_disclosure"]["temporal_presentation_policy"] == (
        "recent_year_coverage_v1"
    )

    tampered = copy.deepcopy(responses)
    tampered["batch_0001"]["batch_id"] = "batch_0002"
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_batched_preselection_relation_confirmations(
            batch_manifest, sources, tampered, batch_size=5
        )
    assert caught.value.boundary == "relation_batch_identity"

    missing_confirmation = copy.deepcopy(confirmation_responses)
    missing_confirmation.pop(next(iter(missing_confirmation)))
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_preselection_relation_confirmations_prepare_quotes(
            batch_manifest,
            sources,
            responses,
            confirmation_manifest,
            missing_confirmation,
        )
    assert caught.value.boundary == "missing_relation_confirmation_batch"

    wrong_identity = copy.deepcopy(confirmation_responses)
    first_confirmation_id = next(iter(wrong_identity))
    wrong_identity[first_confirmation_id]["batch_id"] = "confirmation_batch_9999"
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_preselection_relation_confirmations_prepare_quotes(
            batch_manifest,
            sources,
            responses,
            confirmation_manifest,
            wrong_identity,
        )
    assert caught.value.boundary == "relation_confirmation_batch_identity"

    broad = copy.deepcopy(confirmation_responses)
    broad[first_confirmation_id]["point_scope"] = "broad_axis_or_bundle"
    broad[first_confirmation_id]["point_scope_reason"] = "This is only an area."
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_preselection_relation_confirmations_prepare_quotes(
            batch_manifest,
            sources,
            responses,
            confirmation_manifest,
            broad,
        )
    assert caught.value.boundary == "bounded_point_not_confirmed"


def test_batched_positional_relations_reject_missing_batch(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    candidates = _candidate_rows(sources, spec)
    first = batch_manifest["batches"][0]
    responses = {
        first["batch_id"]: _positional_relation_response(
            candidates[: first["candidate_count"]]
        )
    }

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "missing_relation_batch"


def test_batched_positional_relations_reject_local_row_reordering(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _batched_positional_relation_response(
            subset, batch["batch_id"]
        )
    first_rows = responses["batch_0001"]["results_by_candidate_row"]
    first_rows["row_9999"] = first_rows.pop("row_0001")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "missing_candidate_result"


def test_batched_positional_relations_reject_tampered_manifest(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    batch_manifest["candidate_count"] = 9

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, {})

    assert caught.value.boundary == "manifest_verification"


def test_batched_positional_relations_reject_duplicate_batch_identity(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    batch_manifest["batches"][1]["batch_id"] = "batch_0001"
    batch_manifest.pop("manifest_sha256")
    batch_manifest["manifest_sha256"] = _canonical_hash(batch_manifest)

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, {})

    assert caught.value.boundary == "manifest_verification"


def test_batched_positional_relations_reject_transposed_same_size_batches(
    tmp_path: Path,
) -> None:
    """Two same-size batches must not accept each other's response.

    Row keys restart at row_0000 in every batch, so without a per-batch
    identity a mis-filed response file finalizes cleanly with every candidate
    still accounted exactly once and every relation silently taken from the
    wrong batch.
    """

    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    batch_manifest, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=10
    )
    candidates = _candidate_rows(sources, spec)

    assert [row["candidate_count"] for row in batch_manifest["batches"]] == [10, 10]
    first_schema, second_schema = (schema for _, schema in prompts_and_schemas)
    assert first_schema != second_schema
    assert (
        batch_manifest["batches"][0]["response_schema_sha256"]
        != batch_manifest["batches"][1]["response_schema_sha256"]
    )

    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _batched_positional_relation_response(
            subset, batch["batch_id"]
        )
    responses["batch_0001"], responses["batch_0002"] = (
        responses["batch_0002"],
        responses["batch_0001"],
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "relation_batch_identity"


def test_batched_positional_relations_reject_absent_batch_identity(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(spec, sources, batch_size=6)
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _positional_relation_response(subset)

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "relation_response_shape"


def test_positional_relation_mode_rejects_non_string_relation_value(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"]["row_0000"] = {"relation": "support"}

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "relation_response_shape"


def test_relation_batch_policy_guidance_is_selection_wide_not_per_batch(
    tmp_path: Path,
) -> None:
    """A batch is a transport slice, so it cannot acquire its own policy lane."""

    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    candidates = _candidate_rows(sources, spec)
    selection_guidance = _policy_guidance(spec, candidates)
    _, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )

    for prompt, _ in prompts_and_schemas:
        assert ("VALUE-BOX POLICY" in prompt) == ("VALUE-BOX POLICY" in selection_guidance)


@pytest.mark.parametrize("batch_size", [0, 301, "100", True])
def test_relation_batching_rejects_invalid_batch_size(
    tmp_path: Path, batch_size: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["relation_response_mode"] = "positional"

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection_batches(spec, sources, batch_size=batch_size)

    assert caught.value.boundary == "selection_spec"


def test_relation_batching_rejects_literal_id_mode(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path)

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection_batches(spec, sources, batch_size=5)

    assert caught.value.boundary == "selection_spec"


def test_relation_batch_runner_writes_and_finalizes_exact_batch_set(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    spec["sources"] = [
        {
            "source_id": sources[0]["source_id"],
            "packet_path": str(sources[0]["packet_path"]),
            "bundle_path": str(sources[0]["bundle_path"]),
        }
    ]
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    batch_dir = tmp_path / "prepared"
    batch_manifest_path = tmp_path / "batch_manifest.json"

    prepared = prepare_evidence_selection_batches_run(
        spec_path=spec_path,
        batch_size=6,
        batch_dir=batch_dir,
        batch_manifest_out=batch_manifest_path,
    )
    batch_manifest = json.loads(batch_manifest_path.read_text(encoding="utf-8"))
    candidates = _candidate_rows(sources, spec)
    response_dir = tmp_path / "responses"
    response_dir.mkdir()
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        (response_dir / f"{batch['batch_id']}_response.json").write_text(
            json.dumps(
                _batched_positional_relation_response(subset, batch["batch_id"])
            ),
            encoding="utf-8",
        )

    finalized = finalize_evidence_selection_batches_run(
        batch_manifest_path=batch_manifest_path,
        response_dir=response_dir,
        quote_prompt_out=tmp_path / "quote_prompt.txt",
        quote_schema_out=tmp_path / "quote_schema.json",
        quote_manifest_out=tmp_path / "quote_manifest.json",
        confirmation_prompt_out=tmp_path / "confirmation_prompt.txt",
        confirmation_schema_out=tmp_path / "confirmation_schema.json",
        confirmation_manifest_out=tmp_path / "confirmation_manifest.json",
    )

    assert prepared["candidate_count"] == 10
    assert prepared["batch_count"] == 2
    assert finalized["candidate_count"] == 10
    assert finalized["batch_count"] == 2
    assert (batch_dir / "batch_0001_prompt.txt").is_file()
    assert (batch_dir / "batch_0002_schema.json").is_file()

    preselection_manifest_path = tmp_path / "preselection_batch_manifest.json"
    preselection_batch_dir = tmp_path / "preselection_batches"
    preselection = prepare_batched_preselection_relation_confirmation_run(
        batch_manifest_path=batch_manifest_path,
        response_dir=response_dir,
        batch_size=4,
        confirmation_batch_dir=preselection_batch_dir,
        confirmation_batch_manifest_out=preselection_manifest_path,
    )
    confirmation_manifest = json.loads(
        preselection_manifest_path.read_text(encoding="utf-8")
    )
    reason_by_relation = {
        "support": "matching_customer_experience",
        "counter": "differing_customer_experience",
        "adjacent": "related_customer_context",
        "exclude": "wrong_scope_or_non_evidence",
    }
    confirmation_response_dir = tmp_path / "preselection_responses"
    confirmation_response_dir.mkdir()
    for batch in confirmation_manifest["batches"]:
        prompt = (
            preselection_batch_dir / f"{batch['batch_id']}_prompt.txt"
        ).read_text(encoding="utf-8")
        envelope = json.loads(
            prompt.split(
                "PRESELECTION_RELATION_CONFIRMATION_BATCH_ENVELOPE_JSON:\n", 1
            )[1]
        )
        checks = []
        for row in envelope["candidate_rows"]:
            relation = "adjacent" if row[5] == "creator_authored" else "support"
            checks.append(
                {
                    "confirmation_row_id": row[0],
                    "relation": relation,
                    "reason_code": reason_by_relation[relation],
                }
            )
        (confirmation_response_dir / f"{batch['batch_id']}_response.json").write_text(
            json.dumps(
                {
                    "batch_id": batch["batch_id"],
                "point_scope": "single_point",
                "point_scope_reason": "One direction-bearing hydration point.",
                    "relation_checks": checks,
                }
            ),
            encoding="utf-8",
        )
    confirmed = finalize_batched_preselection_relation_confirmation_run(
        batch_manifest_path=batch_manifest_path,
        response_dir=response_dir,
        confirmation_batch_manifest_path=preselection_manifest_path,
        confirmation_response_dir=confirmation_response_dir,
        quote_prompt_out=tmp_path / "v7_quote_prompt.txt",
        quote_schema_out=tmp_path / "v7_quote_schema.json",
        quote_manifest_out=tmp_path / "v7_quote_manifest.json",
    )
    assert preselection["candidate_count"] == 10
    assert confirmed["candidate_count"] == 10
    assert confirmed["relation_batch_count"] == 2
    assert _parser().parse_args(
        [
            "prepare-batched-preselection-relation-confirmation",
            "--batch-manifest",
            "batches.json",
            "--response-dir",
            "responses",
            "--batch-size",
            "4",
            "--confirmation-batch-dir",
            "confirmation-batches",
            "--confirmation-batch-manifest-out",
            "confirmation.json",
        ]
    ).command == "prepare-batched-preselection-relation-confirmation"


@pytest.mark.parametrize("cap", [0, 21, "15", True])
def test_selection_spec_rejects_invalid_truth_origin_cap(
    tmp_path: Path, cap: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["truth_group_cap"] = cap

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)

    assert caught.value.boundary == "selection_spec"


@pytest.mark.parametrize("mode", ["ids", "ordered", 1, True])
def test_selection_spec_rejects_invalid_relation_response_mode(
    tmp_path: Path, mode: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["relation_response_mode"] = mode

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)

    assert caught.value.boundary == "selection_spec"


def test_provider_prompts_are_compact_views_while_manifests_keep_full_facts(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 5)
    relation_prompt, relation_schema, manifest = prepare_evidence_selection(
        spec, sources
    )
    assert '"candidate_columns"' in relation_prompt
    assert '"independence_posture"' not in relation_prompt
    assert '"source_ref"' not in relation_prompt
    assert '"engagement_raw_value"' not in relation_prompt
    assert manifest["candidate_inventory_sha256"]
    assert relation_schema["properties"]["results"]["items"]["properties"][
        "reason_code"
    ]["pattern"]

    long_body = "One shared body. " + "x" * 300
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = long_body
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    quote_prompt, quote_schema, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    assert quote_prompt.count(long_body) == 1
    assert '"body_columns"' in quote_prompt
    assert len(quote_manifest["provider_selected_ids"]) == len(
        quote_manifest["selected_rows"]
    )
    exact_quote_schema = quote_schema["properties"]["quotes"]["items"][
        "properties"
    ]["exact_quote"]
    assert exact_quote_schema["maxLength"] == 220


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("missing", "missing_candidate_result"),
        ("duplicate", "duplicate_candidate_result"),
        ("foreign", "foreign_candidate_result"),
    ],
)
def test_relation_candidate_accounting_fails_at_intended_boundary(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 4)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    response = _relation_response(_candidate_rows(sources, spec))
    if mutation == "missing":
        response["results"].pop()
    elif mutation == "duplicate":
        response["results"].append(copy.deepcopy(response["results"][0]))
    else:
        response["results"][-1]["candidate_id"] = "candidate_foreign"
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == boundary


def test_creator_cannot_be_laundered_into_customer_support(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 5)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _relation_response(candidates)
    creator = next(index for index, row in enumerate(candidates) if row["layer"] == "influence_context")
    response["results"][creator]["relation"] = "support"
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == "creator_customer_laundering"


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("changed_character", "quote_exactness"),
        ("overlength", "quote_overlength"),
        ("inserted_ellipsis", "quote_exactness"),
    ],
)
def test_quote_mutations_fail_at_exact_boundary(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 2)
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = "Opening context. " + "x" * 400 + " Closing context."
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    row = response["quotes"][0]
    if mutation == "changed_character":
        row["exact_quote"] = row["exact_quote"].replace("Opening", "Changed", 1)
    elif mutation == "overlength":
        row["exact_quote"] = "x" * 221
    else:
        row["exact_quote"] = "Opening ... Closing context."
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == boundary


def test_quote_stopping_before_the_next_source_word_fails_loud(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = (
        "Opening context. The balm feels better in this bitter cold, even overnight. "
        + "x" * 221
    )
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = "The balm feels better in this bitter"

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)

    assert caught.value.boundary == "quote_boundary_incomplete"


def test_quote_ending_at_source_punctuation_passes_clause_boundary_guard(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = (
        "Opening context. The balm feels better in this bitter cold, even overnight. "
        + "x" * 221
    )
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = "The balm feels better in this bitter cold"

    artifact = finalize_quotes(quote_manifest, sources, response)

    assert artifact["source_groups"][0]["rows"][0]["exact_quote"].endswith("bitter cold")


def test_missing_body_is_typed_unavailable_and_exact_but_semantically_different_text_remains_quality_visible(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"] = []
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {"quotes": []}
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["quote_status"] == "quote_unavailable"
    assert row["source_body_present"] is False
    assert row["quote_unavailable_cause"] == "source_body_unavailable"
    assert row["normalized_meaning"]


def test_quote_unavailable_from_an_available_body_is_distinguishable_from_a_missing_body(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "x" * 400
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {
        "quotes": [
            {
                "selected_id": quote_manifest["selected_rows"][0]["selected_id"],
                "quote_status": "quote_unavailable",
                "exact_quote": None,
            }
        ]
    }
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["quote_status"] == "quote_unavailable"
    assert row["source_body_present"] is True
    assert row["quote_unavailable_cause"] == "no_relevant_exact_quote_returned"


def test_source_native_ellipsis_is_preserved_when_the_quote_is_exact(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "My lips burn… only after this shade."
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {"quotes": []}
    artifact = finalize_quotes(quote_manifest, sources, response)
    output_row = artifact["source_groups"][0]["rows"][0]
    assert output_row["exact_quote"] == "My lips burn… only after this shade."
    assert output_row["quote_unavailable_cause"] is None


def test_short_source_body_cannot_be_clipped_before_material_countervailing_behavior(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    body = (
        "Do I cringe a little every time I remember the price tag? Yes. "
        "Will I be repurchasing vanilla AND vanilla beige? Also yes."
    )
    sources[0]["bundle"]["evidence_units"][0]["text"] = body
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    quote_prompt, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    assert spec["bounded_claim"] in quote_prompt
    assert body not in quote_prompt
    assert quote_manifest["provider_selected_ids"] == []
    artifact = finalize_quotes(quote_manifest, sources, {"quotes": []})
    row = artifact["source_groups"][0]["rows"][0]
    assert row["exact_quote"] == body


def test_display_label_uses_customer_facing_signal_and_preserves_source_meanings(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "Opening complete sentence. " + "x" * 400
    _reseal(sources[0])
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    for suffix, statement in (
        ("vanilla", "The author intends to repurchase the Vanilla option."),
        ("vanilla-beige", "The author intends to repurchase the Vanilla Beige shade."),
    ):
        companion = copy.deepcopy(evidence_row[10][0])
        companion[0] = f"community_post:0::{suffix}"
        companion[1] = statement
        companion[7] = ["shade_and_color_fit"]
        companion[8] = []
        evidence_row[10].append(companion)
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")

    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidate = _candidate_rows(sources, spec)[0]
    relation_response = {
        "results": [
            {
                "candidate_id": candidate["candidate_id"],
                "relation": "counter",
                "reason_code": "repurchase_despite_price",
            }
        ]
    }
    quote_prompt, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, relation_response
    )
    assert "Repurchase intent despite price" in quote_prompt
    response = _quote_response(quote_manifest, sources)
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["display_label"] == "Repurchase intent despite price"
    assert "presentation_statement" not in row
    assert [meaning["statement"] for meaning in row["same_evidence_companion_meanings"]] == [
        "The author intends to repurchase the Vanilla option.",
        "The author intends to repurchase the Vanilla Beige shade.",
    ]


@pytest.mark.parametrize(
    ("reason_code", "boundary"),
    [
        ("", "relation_response_shape"),
        ("Not a code", "relation_response_shape"),
        ("x" * 81, "relation_response_shape"),
        ("counter_to_poor_value", "reason_code_relation_leak"),
    ],
)
def test_relation_reason_code_cannot_leak_internal_relation_into_display_label(
    tmp_path: Path,
    reason_code: str,
    boundary: str,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidate = _candidate_rows(sources, spec)[0]
    response = {
        "results": [
            {
                "candidate_id": candidate["candidate_id"],
                "relation": "counter",
                "reason_code": reason_code,
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == boundary


def test_legacy_quote_manifest_retains_its_original_response_shape(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    quote_manifest["schema_version"] = "phase_a_evidence_quote_manifest_v1"
    quote_manifest.pop("provider_selected_ids")
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    response = _quote_response(quote_manifest, sources)
    artifact = _finalize_quotes_runtime(quote_manifest, sources, response)
    assert "display_label" not in artifact["source_groups"][0]["rows"][0]


def test_v3_quote_manifest_remains_finalizable_with_all_selected_responses(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    quote_manifest["schema_version"] = "phase_a_evidence_quote_manifest_v3"
    quote_manifest.pop("provider_selected_ids")
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    response = _quote_response(quote_manifest, sources)
    artifact = _finalize_quotes_runtime(quote_manifest, sources, response)
    assert artifact["source_groups"][0]["rows"][0]["display_label"]


def test_v4_provider_subset_is_recomputed_from_bound_body_lengths(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    selected_id = quote_manifest["selected_rows"][0]["selected_id"]
    quote_manifest["provider_selected_ids"] = [selected_id]
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    body = sources[0]["bundle"]["evidence_units"][0]["text"]
    response = {
        "quotes": [
            {
                "selected_id": selected_id,
                "quote_status": "quote_available",
                "exact_quote": body,
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "manifest_verification"
    assert "provider quote workload changed" in str(caught.value)


def test_candidate_exposes_same_evidence_companion_meanings_without_admitting_them(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    companion = copy.deepcopy(evidence_row[10][0])
    companion[0] = "community_post:0::repurchase"
    companion[1] = "The author intends to repurchase two named shades."
    companion[7] = ["shade_and_color_fit"]
    companion[8] = []
    evidence_row[10].append(companion)
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")

    candidates = _candidate_rows(sources, spec)
    assert len(candidates) == 1
    assert candidates[0]["same_evidence_companion_meanings"] == [
        {
            "semantic_unit_ref": "community_post:0::repurchase",
            "statement": "The author intends to repurchase two named shades.",
            "polarity": "affirmed",
            "axis_ids": ["shade_and_color_fit"],
            "conditions": [],
        }
    ]


def test_sephora_positive_helpful_votes_rank_inside_only_the_sephora_bucket() -> None:
    common = {
        "protected_lanes": [],
        "relation": "support",
        "engagement_material_positive": True,
        "engagement_kind": "sephora_helpful_votes",
    }
    higher = {**common, "candidate_id": "higher", "engagement_raw_value": {"negative": 6, "positive": 30, "total": 36}}
    lower = {**common, "candidate_id": "lower", "engagement_raw_value": {"negative": 2, "positive": 24, "total": 26}}
    assert _bucket_priority(higher) < _bucket_priority(lower)
    with pytest.raises(EvidenceConsumerError) as caught:
        _bucket_priority({**higher, "engagement_raw_value": {"negative": 6, "positive": 30, "total": 35}})
    assert caught.value.boundary == "unsupported_engagement_shape"


def test_unknown_mapping_engagement_fails_during_candidate_admission(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    evidence_row[9][1] = {"likes": 50}
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "unsupported_engagement_shape"


def test_known_host_variants_group_under_one_source_venue() -> None:
    assert _source_venue("community_post", "https://reddit.com/r/x", "reddit:1")[:1] == ("reddit",)
    assert _source_venue("community_post", "https://old.reddit.com/r/x", "reddit:2")[:1] == ("reddit",)
    assert _source_venue("audience_comment", "https://m.tiktok.com/v/1", "tiktok-comment:1")[:1] == ("tiktok",)
    assert _source_venue("retailer_review", "https://www.sephora.com/product/x", "retailer:sephora:1")[:1] == ("sephora",)


@pytest.mark.parametrize(
    ("role", "source_ref", "evidence_id", "venue"),
    [
        ("community_post", "https://np.reddit.com/r/x/comments/1", "reddit:1", "reddit"),
        ("community_post", "https://new.reddit.com/r/x/comments/2", "reddit:2", "reddit"),
        ("community_post", "https://sh.reddit.com/r/x/comments/3", "reddit:3", "reddit"),
        ("community_post", "https://redd.it/abc", "reddit:4", "reddit"),
        ("audience_comment", "https://vm.tiktok.com/ZM123/", "tiktok-comment:1", "tiktok"),
        ("audience_comment", "https://vt.tiktok.com/ZS456/", "tiktok-comment:2", "tiktok"),
        ("retailer_review", "https://smile.amazon.com/dp/B0", "retailer:amazon:1", "amazon"),
        ("retailer_review", "https://community.sephora.com/t/x", "retailer:sephora:1", "sephora"),
    ],
)
def test_host_variants_and_short_links_do_not_split_one_venue(
    role: str, source_ref: str, evidence_id: str, venue: str
) -> None:
    assert _source_venue(role, source_ref, evidence_id) == (venue, "normalized_source_ref_hostname")


def test_a_lookalike_host_is_not_absorbed_into_a_known_venue() -> None:
    assert _source_venue("community_post", "https://notreddit.com/x", "x:1") == (
        "notreddit.com",
        "source_ref_hostname",
    )


def test_partial_numeric_engagement_strings_are_refused_rather_than_misread() -> None:
    common = {"protected_lanes": [], "relation": "support",
              "engagement_material_positive": True, "engagement_kind": "reddit_points"}
    # "1.2k points" must not order as 1.0 behind a genuine "5 points".
    abbreviated = {**common, "candidate_id": "a", "engagement_raw_value": "1.2k points"}
    grouped = {**common, "candidate_id": "b", "engagement_raw_value": "1,234 points"}
    plain = {**common, "candidate_id": "c", "engagement_raw_value": "5 points"}
    assert _numeric_engagement("1.2k points", "reddit_points") is None
    assert _numeric_engagement("1,234 points", "reddit_points") is None
    assert _numeric_engagement("922", "reddit_points") == 922.0
    assert _numeric_engagement("368 points", "reddit_points") == 368.0
    ordered = [row["candidate_id"] for row in sorted([abbreviated, grouped, plain], key=_bucket_priority)]
    assert ordered[0] == "c"


def test_a_negative_native_score_still_orders_above_unavailable_engagement() -> None:
    common = {"protected_lanes": [], "relation": "support",
              "engagement_material_positive": True, "engagement_kind": "reddit_points"}
    downvoted = {**common, "candidate_id": "a_downvoted", "engagement_raw_value": -30}
    unavailable = {**common, "candidate_id": "b_unavailable", "engagement_raw_value": None}
    assert _bucket_priority(downvoted) < _bucket_priority(unavailable)


def test_edited_bundle_body_without_a_resealed_hash_fails_bundle_verification(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "Fabricated body text the bundle hash never covered."
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)
    assert caught.value.boundary == "bundle_verification"


def test_body_swapped_after_the_quote_manifest_cannot_supply_a_quote(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = "Body substituted after the quote manifest was written."
    response = {"quotes": []}
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "body_identity_mismatch"


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("unresolved_wrong_source", "failed_rehydration_lookup"),
        ("protected_absent_evidence", "failed_rehydration_lookup"),
        ("protected_unknown_lane", "selection_spec"),
        ("nomination_row_malformed", "selection_spec"),
    ],
)
def test_operator_nominations_that_cannot_resolve_fail_closed(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 4)
    if mutation == "unresolved_wrong_source":
        spec["admit_unresolved"] = [{"source_id": "not-a-source", "evidence_id": "community_post:0"}]
    elif mutation == "protected_absent_evidence":
        spec["protected_evidence_ids"] = {"safety": ["community_post:404"]}
    elif mutation == "protected_unknown_lane":
        spec["protected_evidence_ids"] = {"safety_critical": ["community_post:0"]}
    else:
        spec["admit_semantic_refs"] = ["community_post:0::hydration"]
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == boundary


def test_same_origin_distinct_relation_is_one_capped_group_with_two_visible_candidates(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    # Force the two semantic rows to share a scoped origin.
    for group in sources[0]["packet"]["source_groups"]:
        for row in group["evidence_rows"]:
            row[7] = "shared-origin"
    sources[0]["packet"]["packet_sha256"] = _canonical_hash(
        {key: value for key, value in sources[0]["packet"].items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(sources[0]["packet"]), encoding="utf-8")
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _relation_response(candidates)
    response["results"][0]["relation"] = "support"
    response["results"][1]["relation"] = "counter"
    _, _, quote_manifest = finalize_relations_prepare_quotes(manifest, sources, response)
    assert len({row["origin_group_id"] for row in quote_manifest["selected_rows"]}) == 1
    assert len(quote_manifest["selected_rows"]) == 2


def _selection_row(
    candidate_id: str,
    *,
    origin: str = "origin:shared",
    relation: str = "support",
    reason_code: str = "explicit_good_value",
    material_positive: bool | None = True,
    protected_lanes: list[str] | None = None,
    engagement_status: str = "engagement_available",
    engagement_raw_value: int | str | None = 10,
    source_role: str = "community_post",
    source_venue: str = "reddit",
    engagement_kind: str = "reddit_points",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "layer": "truth_support",
        "relation": relation,
        "reason_code": reason_code,
        "scoped_independence_key": origin,
        "source_role": source_role,
        "source_venue": source_venue,
        "engagement_kind": engagement_kind,
        "engagement_raw_value": engagement_raw_value,
        "engagement_material_positive": material_positive,
        "engagement_status": engagement_status,
        "conditions": [],
        "protected_lanes": protected_lanes or [],
    }


def _value_axis_source(tmp_path: Path, count: int = 6) -> tuple[dict, list[dict]]:
    """Build a real-entry-point value-axis source and spec."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    packet, bundle = _packet_and_bundle(count)
    for group in packet["source_groups"]:
        for row in group["evidence_rows"]:
            for semantic in row[-1]:
                axes = semantic[7]
                semantic[7] = (
                    axes.replace("hydration_and_moisture", "value_and_quantity")
                    if isinstance(axes, str)
                    else ["value_and_quantity"]
                )
    packet["selection"]["axis_ids"] = ["value_and_quantity"]
    packet.pop("packet_sha256", None)
    packet["packet_sha256"] = _canonical_hash(packet)
    packet_path = tmp_path / "packet.json"
    bundle_path = tmp_path / "bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    spec = dict(_spec(count))
    spec["axis_ids"] = ["value_and_quantity"]
    spec["bounded_claim"] = "Customers repurchase the balm despite its price."
    return spec, [
        {
            "source_id": "full-corpus",
            "packet_path": packet_path,
            "bundle_path": bundle_path,
            "packet": packet,
            "bundle": bundle,
        }
    ]


def _value_relation_response(
    candidates: list[dict], overrides: dict[str, tuple[str, str]] | None = None
) -> dict:
    overrides = overrides or {}
    rows = []
    for candidate in candidates:
        if candidate["evidence_id"] in overrides:
            relation, reason_code = overrides[candidate["evidence_id"]]
        elif candidate["layer"] == "influence_context":
            relation, reason_code = "adjacent", "non_value_product_experience"
        else:
            relation, reason_code = "support", "explicit_good_value"
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "relation": relation,
                "reason_code": reason_code,
            }
        )
    return {"results": rows}


def test_a_value_axis_spec_turns_on_the_value_prompt_and_schema_at_the_real_entry_point(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path)
    prompt, schema, _ = prepare_evidence_selection(spec, sources)
    assert "VALUE-BOX POLICY" in prompt
    variants = schema["properties"]["results"]["items"]["anyOf"]
    by_relation = {
        row["properties"]["relation"]["const"]: set(
            row["properties"]["reason_code"]["enum"]
        )
        for row in variants
    }
    assert "better_value_than_comparator" in by_relation["support"]
    assert "comparator_better_value" in by_relation["counter"]

    balanced_dir = tmp_path / "balanced"
    balanced_dir.mkdir(parents=True, exist_ok=True)
    non_value_prompt, non_value_schema, _ = prepare_evidence_selection(
        *_write_source(balanced_dir)
    )
    assert "VALUE-BOX POLICY" not in non_value_prompt
    assert "anyOf" not in non_value_schema["properties"]["results"]["items"]


def test_value_policy_does_not_turn_time_to_finish_into_quantity_value() -> None:
    guidance = _policy_guidance({"axis_ids": ["value_and_quantity"]})

    assert "Time to finish, pan, or empty a product is completed-use evidence" in guidance
    assert "not quantity efficiency" in guidance
    assert "explicitly says it will buy or repurchase again" in guidance


def test_explicit_only_value_refs_turn_on_value_policy_without_admitting_the_whole_axis(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path, count=3)
    all_candidates = _candidate_rows(sources, spec)
    admitted = all_candidates[:2]
    spec["axis_ids"] = []
    spec["admit_semantic_refs"] = [
        {
            "source_id": candidate["source_id"],
            "semantic_unit_ref": candidate["semantic_unit_ref"],
        }
        for candidate in admitted
    ]

    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    assert manifest["candidate_count"] == 2
    assert "VALUE-BOX POLICY" in prompt
    assert "anyOf" in schema["properties"]["results"]["items"]

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(
            manifest,
            sources,
            _relation_response(_candidate_rows(sources, manifest["spec"])),
        )
    assert caught.value.boundary == "value_reason_code"


def test_mixed_explicit_refs_do_not_inherit_value_only_policy(tmp_path: Path) -> None:
    spec, sources = _value_axis_source(tmp_path, count=2)
    packet = sources[0]["packet"]
    semantic_rows = [
        semantic
        for group in packet["source_groups"]
        for evidence in group["evidence_rows"]
        for semantic in evidence[-1]
    ]
    semantic_rows[1][7] = ["hydration_and_moisture"]
    _reseal(sources[0])
    explicit_candidates = _candidate_rows(sources, spec)
    # The axis spec now admits only the remaining value row; explicitly nominate
    # both rows to form the mixed bounded set.
    hydration_ref = semantic_rows[1][0]
    spec["axis_ids"] = []
    spec["admit_semantic_refs"] = [
        {
            "source_id": "full-corpus",
            "semantic_unit_ref": explicit_candidates[0]["semantic_unit_ref"],
        },
        {"source_id": "full-corpus", "semantic_unit_ref": hydration_ref},
    ]

    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    assert manifest["candidate_count"] == 2
    assert "VALUE-BOX POLICY" not in prompt
    assert "anyOf" not in schema["properties"]["results"]["items"]


def test_a_value_axis_spec_keeps_a_highly_engaged_adjacent_row_out_of_the_displayed_box(
    tmp_path: Path,
) -> None:
    adjacent = {"community_post:5": ("adjacent", "non_value_product_experience")}
    spec, sources = _value_axis_source(tmp_path / "value")
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, manifest["spec"])
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _value_relation_response(candidates, adjacent)
    )
    artifact = finalize_quotes(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )
    assert quote_manifest["truth_selection_policy"] == "value_first"
    expected_eligible_origins = {
        row["scoped_independence_key"]
        for row in quote_manifest["labeled_inventory"]
        if _truth_row_display_eligible(row, "value_first")
    }
    assert artifact["selection_disclosure"][
        "display_eligible_truth_origin_count"
    ] == len(expected_eligible_origins)
    displayed = {row["evidence_id"] for group in artifact["source_groups"] for row in group["rows"]}
    accounted = {row["evidence_id"] for row in artifact["candidate_dispositions"]}
    assert "community_post:5" not in displayed
    assert "community_post:5" in accounted

    balanced_spec, balanced_sources = _value_axis_source(tmp_path / "balanced")
    balanced_spec["axis_ids"] = ["value_and_quantity", "hydration_and_moisture"]
    _, _, balanced_manifest = prepare_evidence_selection(balanced_spec, balanced_sources)
    balanced_candidates = _candidate_rows(balanced_sources, balanced_manifest["spec"])
    _, _, balanced_quotes = finalize_relations_prepare_quotes(
        balanced_manifest,
        balanced_sources,
        _value_relation_response(balanced_candidates, adjacent),
    )
    balanced_artifact = finalize_quotes(
        balanced_quotes,
        balanced_sources,
        _quote_response(balanced_quotes, balanced_sources),
    )
    balanced_displayed = {
        row["evidence_id"]
        for group in balanced_artifact["source_groups"]
        for row in group["rows"]
    }
    assert "community_post:5" in balanced_displayed


def test_a_value_axis_spec_rejects_an_inverted_comparator_through_the_real_finalizer(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, manifest["spec"])
    response = _value_relation_response(
        candidates, {"community_post:5": ("counter", "better_value_than_comparator")}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_every_value_reason_code_that_can_be_displayed_has_a_curated_label() -> None:
    displayable = {
        code
        for code, relation in VALUE_REASON_RELATIONS.items()
        if relation in {"support", "counter", "adjacent"}
    }
    assert displayable <= set(DISPLAY_LABEL_BY_REASON_CODE)


def test_value_policy_keeps_positive_value_first_and_only_one_direct_complaint() -> None:
    rows = [
        _selection_row(
            "repurchase-204",
            origin="origin:repurchase",
            reason_code="repurchase_despite_price",
            engagement_raw_value="204 points",
        ),
        _selection_row(
            "appeal-10",
            origin="origin:appeal",
            reason_code="multiple_purchases_despite_price",
            engagement_raw_value="10 points",
        ),
        _selection_row(
            "value-per-ounce-514",
            origin="origin:value-per-ounce",
            reason_code="favorable_price_quantity_comparison",
            engagement_raw_value="514 points",
        ),
        _selection_row(
            "retailer-value-31",
            origin="origin:retailer-value",
            reason_code="favorable_price_quantity_comparison",
            engagement_raw_value=31,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "regret-1174",
            origin="origin:regret",
            relation="counter",
            reason_code="purchase_regret_due_cost",
            engagement_raw_value="1174 points",
        ),
        _selection_row(
            "retailer-complaint-35",
            origin="origin:retailer-complaint",
            relation="counter",
            reason_code="too_little_product_for_price",
            engagement_raw_value=35,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "formula-599",
            origin="origin:formula",
            relation="adjacent",
            reason_code="non_value_product_experience",
            engagement_raw_value="599 points",
        ),
    ]

    selected = _select_groups(rows, "truth_support", 5, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}

    assert {"repurchase-204", "appeal-10"} <= selected_ids
    assert "formula-599" not in selected_ids
    assert [row["candidate_id"] for row in selected if row["relation"] == "counter"] == [
        "regret-1174"
    ]
    assert len({row["origin_group_id"] for row in selected}) == 5


def test_value_behavior_tier_uses_native_engagement_not_behavior_subtype() -> None:
    rows = [
        _selection_row(
            f"repurchase-{engagement}",
            origin=f"origin:repurchase:{engagement}",
            reason_code="repurchase_despite_price",
            engagement_raw_value=f"{engagement} points",
        )
        for engagement in (204, 44, 11, 3)
    ]
    rows.extend(
        [
            _selection_row(
                "multiple-purchases-10",
                origin="origin:multiple-purchases",
                reason_code="multiple_purchases_despite_price",
                engagement_raw_value="10 points",
            ),
            _selection_row(
                "regret-1174",
                origin="origin:regret",
                relation="counter",
                reason_code="purchase_regret_due_cost",
                engagement_raw_value="1174 points",
            ),
        ]
    )
    selected = _select_groups(rows, "truth_support", 5, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}
    assert "multiple-purchases-10" in selected_ids
    assert "repurchase-3" not in selected_ids


def test_value_reason_codes_must_match_their_relation_lane() -> None:
    candidate = _selection_row("candidate:value")
    response = {
        "results": [
            {
                "candidate_id": "candidate:value",
                "relation": "support",
                "reason_code": "purchase_regret_due_cost",
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_relation_response([candidate], response, value_policy=True)
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_high_spend_buyer_remorse_is_one_counter_meaning_without_journey_fields() -> None:
    code = "high_spend_followed_by_buyer_remorse"
    assert VALUE_REASON_RELATIONS[code] == "counter"
    assert _display_label(code) == "High spend, followed by buyer’s remorse"
    assert _display_label("purchase_regret_due_cost") == "Purchase regret due to cost"

    candidate = _selection_row("candidate:high-spend-remorse", relation="counter")
    accepted = _validate_relation_response(
        [candidate],
        {
            "results": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "relation": "counter",
                    "reason_code": code,
                }
            ]
        },
        value_policy=True,
    )
    assert accepted[0]["reason_code"] == code
    assert not ({"future_intent", "transaction_count", "post_purchase_value"} & accepted[0].keys())


def test_high_spend_buyer_remorse_cannot_be_promoted_to_value_support() -> None:
    candidate = _selection_row("candidate:high-spend-remorse")
    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_relation_response(
            [candidate],
            {
                "results": [
                    {
                        "candidate_id": candidate["candidate_id"],
                        "relation": "support",
                        "reason_code": "high_spend_followed_by_buyer_remorse",
                    }
                ]
            },
            value_policy=True,
        )
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_value_response_schema_makes_comparator_direction_unambiguous() -> None:
    variants = _relation_schema(value_policy=True)["properties"]["results"]["items"][
        "anyOf"
    ]
    by_relation = {
        row["properties"]["relation"]["const"]: set(
            row["properties"]["reason_code"]["enum"]
        )
        for row in variants
    }
    assert "better_value_than_comparator" in by_relation["support"]
    assert "better_value_than_comparator" not in by_relation["counter"]
    assert "comparator_better_value" in by_relation["counter"]
    assert {
        "repurchase_intent",
        "multiple_purchases",
        "purchase_commitment",
        "product_goes_a_long_way",
    } <= by_relation["support"]


def test_value_prompt_forbids_companion_only_formula_complaints_from_value_lanes() -> None:
    guidance = _policy_guidance({"axis_ids": ["value_and_quantity"]})
    assert "formula, hydration, scent, trial-only, gift-card" in guidance
    assert "must not turn" in guidance
    assert "repurchase_despite_price" in guidance
    assert "repurchase_intent" in guidance
    assert "requires explicit source meaning about price or cost" in guidance
    assert "whole same-evidence set" in guidance
    assert "every candidate from that evidence origin counter or adjacent" in guidance
    assert "rationalizing sunk cost does not countervail" in guidance
    assert "use the corresponding `*_despite_price` code" in guidance
    assert "does not imply repurchase, a transaction count, or future intent" in guidance
    assert "Multiple units alone do not establish high spend" in guidance
    assert "regret exists without explicit substantial completed spending" in guidance
    # The buy-again / worth-the-price exceptions must still decide the lane
    # before either regret code is offered, or the regret routing sentences
    # would demote an explicit repurchase-despite-price origin to counter.
    assert "neither regret code may be used on an origin" in guidance
    assert guidance.index("Those two exceptions decide the lane") < guidance.index(
        "Use `purchase_regret_due_cost`"
    )
    assert "product_goes_a_long_way" in guidance
    assert _policy_guidance({"axis_ids": ["hydration_and_moisture"]}) == ""


def test_value_policy_does_not_compare_counter_engagement_across_venues() -> None:
    rows = [
        _selection_row(
            "reddit-value",
            origin="origin:reddit-value",
            reason_code="explicit_good_value",
            engagement_raw_value="20 points",
        ),
        _selection_row(
            "sephora-complaint",
            origin="origin:sephora-complaint",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value=200,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == ["reddit-value"]


def test_value_policy_shows_the_strongest_native_complaint_when_no_support_exists() -> None:
    rows = [
        _selection_row(
            f"regret-{points}",
            origin=f"origin:regret:{points}",
            relation="counter",
            reason_code="purchase_regret_due_cost",
            engagement_raw_value=f"{points} points",
        )
        for points in (4, 1174, 31)
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == ["regret-1174"]


def test_value_policy_anchors_the_complaint_to_the_best_signal_not_first_bucket() -> None:
    rows = [
        _selection_row(
            "reddit-weak-2",
            origin="origin:reddit-weak",
            reason_code="explicit_good_value",
            engagement_raw_value="2 points",
        ),
        _selection_row(
            "reddit-counter-1",
            origin="origin:reddit-counter",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value="1 point",
        ),
        _selection_row(
            "sephora-strong-999",
            origin="origin:sephora-strong",
            reason_code="repurchase_despite_price",
            engagement_raw_value=999,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "sephora-counter-900",
            origin="origin:sephora-counter",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value=900,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 4, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}
    assert "sephora-strong-999" in selected_ids
    assert "sephora-counter-900" in selected_ids
    assert "reddit-counter-1" not in selected_ids


def test_value_policy_orders_protected_origins_without_cross_venue_engagement() -> None:
    rows = [
        _selection_row(
            "reddit-protected-2",
            origin="origin:reddit-protected",
            protected_lanes=["costly_behavior"],
            engagement_raw_value="2 points",
        ),
        _selection_row(
            "sephora-protected-999",
            origin="origin:sephora-protected",
            protected_lanes=["costly_behavior"],
            engagement_raw_value=999,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == [
        "reddit-protected-2",
        "sephora-protected-999",
    ]


def test_value_policy_keeps_operator_protected_counter_even_without_positive_engagement() -> None:
    rows = [
        _selection_row(
            "protected-costly",
            origin="origin:protected",
            relation="counter",
            reason_code="explicit_poor_value",
            material_positive=False,
            protected_lanes=["costly_behavior"],
        ),
        _selection_row(
            "positive",
            origin="origin:positive",
            reason_code="explicit_good_value",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert {row["candidate_id"] for row in selected} == {"protected-costly", "positive"}


def test_same_origin_displays_material_support_and_counter_but_not_unprotected_quiet() -> None:
    rows = [
        _selection_row("support", relation="support"),
        _selection_row("counter", relation="counter"),
        _selection_row("quiet", relation="adjacent", material_positive=False),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"support", "counter"}
    assert {"relation:support", "relation:counter"} <= set(
        selected[0]["origin_required_display_lanes"]
    )


def test_unprotected_quiet_counter_is_retained_but_not_forced_into_presentation() -> None:
    rows = [
        _selection_row("material_support", origin="origin:support", relation="support"),
        _selection_row(
            "quiet_counter",
            origin="origin:counter",
            relation="counter",
            material_positive=False,
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"material_support"}


def test_protected_quiet_behavior_remains_visible() -> None:
    rows = [
        _selection_row(
            "quiet_behavior",
            origin="origin:behavior",
            relation="counter",
            material_positive=False,
            protected_lanes=["costly_behavior"],
        )
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"quiet_behavior"}


def test_under_cap_reservation_does_not_hide_counter_behind_quiet_row() -> None:
    rows = [
        _selection_row("a_support", relation="support"),
        _selection_row("b_quiet", relation="adjacent", material_positive=False),
        _selection_row("z_counter", relation="counter"),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert "z_counter" in {row["candidate_id"] for row in selected}


def test_more_than_ten_protected_origins_fails_the_origin_cap() -> None:
    rows = [
        _selection_row(
            f"protected:{index}",
            origin=f"origin:{index}",
            protected_lanes=["safety"],
        )
        for index in range(11)
    ]
    with pytest.raises(EvidenceConsumerError) as caught:
        _select_groups(rows, "truth_support", 10)
    assert caught.value.boundary == "presentation_cap_insufficient"


def test_every_operator_protected_candidate_and_origin_is_visible() -> None:
    rows = [
        _selection_row("safety:a", origin="origin:a", protected_lanes=["safety"]),
        _selection_row("safety:b", origin="origin:b", protected_lanes=["safety"]),
        _selection_row(
            "costly:b", origin="origin:b", relation="counter", protected_lanes=["costly_behavior"]
        ),
        _selection_row("ordinary", origin="origin:c"),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    protected = {"safety:a", "safety:b", "costly:b"}
    assert protected <= {row["candidate_id"] for row in selected}
    assert {"origin:a", "origin:b"} <= {row["origin_group_id"] for row in selected}


@pytest.mark.parametrize("quote", [" ", "!", "a", "💄"])
def test_available_quote_requires_two_unicode_alphanumeric_characters(
    tmp_path: Path, quote: str
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = (
        "x" * 221 + f" before {quote} after"
    )
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = quote
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "quote_substance"


def test_two_character_exact_quote_is_allowed_without_a_lexical_relevance_gate(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "x" * 221 + " no"
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = "no"
    artifact = finalize_quotes(quote_manifest, sources, response)
    assert artifact["source_groups"][0]["rows"][0]["exact_quote"] == "no"


def test_runner_three_stage_round_trip_is_deterministic_and_no_provider(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 4)
    spec["sources"] = [
        {"source_id": "full-corpus", "packet_path": "packet.json", "bundle_path": "bundle.json"}
    ]
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    prompt = tmp_path / "relation-prompt.txt"
    schema = tmp_path / "relation-schema.json"
    manifest_path = tmp_path / "selection-manifest.json"
    prepared = prepare_evidence_selection_run(
        spec_path=spec_path, prompt_out=prompt, response_schema_out=schema, manifest_out=manifest_path
    )
    manifest = json.loads(manifest_path.read_text())
    candidates = _candidate_rows(sources, spec)
    relation_path = tmp_path / "relation-response.json"
    relation_path.write_text(json.dumps(_relation_response(candidates)), encoding="utf-8")
    quote_prompt = tmp_path / "quote-prompt.txt"
    quote_schema = tmp_path / "quote-schema.json"
    quote_manifest_path = tmp_path / "quote-manifest.json"
    confirmation_prompt = tmp_path / "confirmation-prompt.txt"
    confirmation_schema = tmp_path / "confirmation-schema.json"
    confirmation_manifest_path = tmp_path / "confirmation-manifest.json"
    relation_final = finalize_evidence_selection_relations_run(
        manifest_path=manifest_path,
        response_path=relation_path,
        quote_prompt_out=quote_prompt,
        quote_schema_out=quote_schema,
        quote_manifest_out=quote_manifest_path,
        confirmation_prompt_out=confirmation_prompt,
        confirmation_schema_out=confirmation_schema,
        confirmation_manifest_out=confirmation_manifest_path,
    )
    quote_manifest = json.loads(quote_manifest_path.read_text())
    quote_response_path = tmp_path / "quote-response.json"
    quote_response_path.write_text(json.dumps(_quote_response(quote_manifest, sources)), encoding="utf-8")
    confirmation_response_path = tmp_path / "confirmation-response.json"
    confirmation_response_path.write_text(
        json.dumps(_confirmation_response(quote_manifest)), encoding="utf-8"
    )
    artifact_path = tmp_path / "artifact.json"
    completed = finalize_evidence_selection_quotes_run(
        selection_manifest_path=manifest_path,
        quote_manifest_path=quote_manifest_path,
        response_path=quote_response_path,
        confirmation_manifest_path=confirmation_manifest_path,
        confirmation_response_path=confirmation_response_path,
        artifact_out=artifact_path,
    )
    assert prepared["model_api_calls"] == relation_final["model_api_calls"] == completed["model_api_calls"] == 0
    assert relation_final["status"] == "PHASE_A_EVIDENCE_SELECTION_QUOTES_AND_CONFIRMATION_READY"
    assert confirmation_prompt.is_file()
    assert confirmation_schema.is_file()
    assert confirmation_manifest_path.is_file()
    first = json.loads(artifact_path.read_text())
    second = finalize_quotes(quote_manifest, sources, _quote_response(quote_manifest, sources))
    assert first == second
    assert first["relation_confirmation_status"] == "passed"
