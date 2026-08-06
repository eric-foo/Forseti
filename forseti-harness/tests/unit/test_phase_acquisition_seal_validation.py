from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from runners.run_phase_acquisition_seal_validation import (
    BROAD_UNDERSTANDING_PROFILE,
    CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    CONSUMER_DEPTH_LEDGER_VERSION,
    DEPTH_LEDGER_VERSION,
    LEGACY_SEAL_VERSION,
    PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION,
    SEAL_VERSION,
    _artifact_hash,
    _validate_reddit_candidate_frontier,
    main,
    validate_phase_acquisition_seal,
)


def _artifact(tmp_path: Path, name: str, text: str | None = None) -> dict[str, str]:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or f"artifact:{name}\n", encoding="utf-8")
    # Repository-internal evidence locators must stay checkout-portable, so
    # fixtures pin repo-root-relative locators exactly as real seals must.
    return {"locator": name, "sha256": _artifact_hash(path)}


def _depth_ledger(tmp_path: Path) -> dict[str, str]:
    source = _artifact(tmp_path, "depth_source.md")
    artifact_id = "depth-source"
    ledger = {
        "schema_version": DEPTH_LEDGER_VERSION,
        "profile_id": BROAD_UNDERSTANDING_PROFILE,
        "subject": "Summer Fridays",
        "cycle_id": "summer_fridays_confirmation",
        "artifacts": [{"artifact_id": artifact_id, **source}],
        "families": {
            "outside_in": {
                "units": [
                    {
                        "unit_id": f"outside-{index}",
                        "origin_id": f"publisher-{index}.example",
                        "artifact_id": artifact_id,
                        "independence": "independent_origin",
                        "echo_group_id": f"story-{index // 2}",
                    }
                    for index in range(12)
                ]
            },
            "retailer_reviews": {
                "corpora": [
                    {
                        "corpus_id": "retailer-a:provider-a",
                        "artifact_id": artifact_id,
                        "unique_review_count": 400,
                        "cross_corpus_duplicate_count": 0,
                        "product_context_ids": ["p1", "p2", "p3"],
                        "category_ids": ["lip", "skincare"],
                        "rating_bands": ["low", "mid", "high"],
                    },
                    {
                        "corpus_id": "retailer-b:provider-b",
                        "artifact_id": artifact_id,
                        "unique_review_count": 400,
                        "cross_corpus_duplicate_count": 20,
                        "product_context_ids": ["p4", "p5", "p6"],
                        "category_ids": ["makeup", "skincare"],
                        "rating_bands": ["low", "mid", "high"],
                    },
                ]
            },
            "reddit_forum": {
                "threads": [
                    {
                        "thread_id": f"thread-{index}",
                        "community_id": f"community-{index % 4}",
                        "topic_category": f"topic-{index % 3}",
                        "artifact_id": artifact_id,
                        "independence": "independent_thread",
                    }
                    for index in range(40)
                ]
            },
            "native_social": {
                "posts": [
                    {
                        "unit_id": f"native-{index}",
                        "platform": "youtube" if index % 2 else "instagram",
                        "post_id": f"post-{index}",
                        "creator_id": f"creator-{index}",
                        "perspective": "positive" if index % 2 else "critical",
                        "artifact_id": artifact_id,
                        "independence": "independent_post",
                    }
                    for index in range(30)
                ]
            },
        },
        "closure": {
            "echo_groups_adjudicated": True,
            "material_seams": [
                {"seam_id": "value", "disposition": "bounded"}
            ],
            "batches": [
                {
                    "batch_id": "batch-1",
                    "candidate_moves_checked": 3,
                    "material_incremental_value": False,
                    "new_material_seams": 0,
                    "changed_material_dispositions": 0,
                },
                {
                    "batch_id": "batch-2",
                    "candidate_moves_checked": 2,
                    "material_incremental_value": False,
                    "new_material_seams": 0,
                    "changed_material_dispositions": 0,
                },
            ],
            "remaining_moves": [
                {
                    "move_id": "another-same-story",
                    "disposition": "dominated",
                    "material": False,
                }
            ],
            "conclusion": "complete",
        },
    }
    path = tmp_path / "evidence_depth_ledger.json"
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return {"locator": "evidence_depth_ledger.json", "sha256": _artifact_hash(path)}


def _consumer_depth_ledger(tmp_path: Path) -> dict[str, str]:
    reference = _depth_ledger(tmp_path)
    path = tmp_path / reference["locator"]
    ledger = json.loads(path.read_text(encoding="utf-8"))
    ledger["schema_version"] = CONSUMER_DEPTH_LEDGER_VERSION
    ledger["profile_id"] = CONSUMER_BRAND_UNDERSTANDING_PROFILE
    external = ledger["families"].pop("outside_in")
    for row in external["units"]:
        row["source_type"] = "consumer_editorial"
        row["relationship"] = "apparently_independent"
    ledger["families"]["external_context"] = external
    for row in ledger["families"]["native_social"]["posts"]:
        row["relationship"] = "apparently_independent"
    # Each usable independent thread pins its own source-native packet.
    for index, row in enumerate(ledger["families"]["reddit_forum"]["threads"]):
        thread_artifact = _artifact(tmp_path, f"thread_native_{index}.md")
        ledger["artifacts"].append(
            {"artifact_id": f"thread-native-{index}", **thread_artifact}
        )
        row["artifact_id"] = f"thread-native-{index}"

    coding = {
        "schema_version": "retailer_product_axis_coding_v1",
        "subject": ledger["subject"],
        "cycle_id": ledger["cycle_id"],
        "corpora": [],
        "rows": [],
    }
    incidence = []
    for corpus in ledger["families"]["retailer_reviews"]["corpora"]:
        corpus_id = corpus["corpus_id"]
        eligible = (
            corpus["unique_review_count"]
            - corpus["cross_corpus_duplicate_count"]
        )
        coding["corpora"].append(
            {
                "corpus_id": corpus_id,
                "eligible_text_review_count": eligible,
                "excluded_no_usable_text_count": 0,
            }
        )
        for index in range(eligible):
            has_axis = index < 2
            coding["rows"].append(
                {
                    "corpus_id": corpus_id,
                    "review_id": f"{corpus_id}-review-{index}",
                    "product_context_id": corpus["product_context_ids"][0],
                    "incentive_state": "not_marked_incentivized",
                    "axis_codes": (
                        [
                            {
                                "axis_id": "packaging_reliability",
                                "choice_outcomes": (
                                    ["returned_or_refunded"]
                                    if index == 0
                                    else ["none_explicit"]
                                ),
                            }
                        ]
                        if has_axis
                        else []
                    ),
                    "overall_choice_outcomes": (
                        ["returned_or_refunded"]
                        if index == 0
                        else ["none_explicit"]
                    ),
                    "source_row_ref": f"depth-source#{corpus_id}-{index}",
                }
            )
        incidence.append(
            {
                "corpus_id": corpus_id,
                "eligible_text_review_count": eligible,
                "axis_mention_count": 2,
                "negative_choice_review_count": 1,
                "positive_choice_review_count": 0,
                "disclosed_incentivized_axis_mention_count": 0,
            }
        )
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    ledger["artifacts"].append(
        {
            "artifact_id": "retailer-axis-coding",
            "locator": "retailer_product_axis_coding.json",
            "sha256": _artifact_hash(coding_path),
        }
    )
    ledger["retailer_axis_coding"] = {"artifact_id": "retailer-axis-coding"}
    ledger["product_axes"] = [
        {
            "axis_id": "packaging_reliability",
            "label": "Packaging reliability",
            "scope": "brand and product",
            "polarity": "pain",
            "strength": "strong",
            "disposition": "material",
            "decision_maturity": "decision_mature",
            "closure_basis": "evidence_supported",
            "claim_ceiling": "strong_qualitative",
            "decision_frontier_family_ids": [
                "family-final-a",
                "family-final-b",
            ],
            "decision_usefulness": {
                "status": "strategically_material",
                "customer_tension": (
                    "Customers value portable packaging, but failures in dispensing "
                    "can erase that convenience."
                ),
                "decision_effects": {
                    "segment_or_condition": "Frequent on-the-go use.",
                    "behavior_or_purchase_consequence": "Returns after packaging failure.",
                    "competitor_destination": "A more reliable alternative package.",
                },
                "strongest_counterevidence": (
                    "Some customers retain the product because the package is convenient."
                ),
                "competitive_decision": (
                    "Compete on verified dispensing reliability without conceding portability."
                ),
                "decision_bearing_support_refs": [
                    {
                        "family": "reddit_forum",
                        "unit_id": "thread-0",
                        "role": "behavior_or_purchase_consequence",
                    },
                    {
                        "family": "reddit_forum",
                        "unit_id": "thread-1",
                        "role": "counterevidence",
                    },
                    {
                        "family": "native_social",
                        "unit_id": "native-0",
                        "role": "customer_tension",
                    },
                ],
                "limitations": [
                    "Qualitative captured-sample evidence; not population prevalence."
                ],
            },
            "support_refs": [
                {
                    "family": "reddit_forum",
                    "unit_id": f"thread-{index}",
                    "contribution": "corroborates",
                    "choice": "subject",
                }
                for index in range(3)
            ]
            + [
                {
                    "family": "native_social",
                    "unit_id": f"native-{index}",
                    "contribution": "sharpens",
                    "choice": "conditional",
                }
                for index in range(3)
            ],
            "retailer_incidence": incidence,
            "focused_search_jobs": [
                {
                    "job_id": "P2-001",
                    "goal": "corroborate_or_segment",
                    "disposition": "captured",
                    "workstream": "product_axis",
                    "planned_at": "2026-08-02T00:01:00+00:00",
                    "search_artifact_id": "phase2-search",
                    "target_ids": ["target-1"],
                },
                {
                    "job_id": "P2-002",
                    "goal": "compare_switch_or_value",
                    "disposition": "no_material_yield",
                    "workstream": "product_axis",
                    "planned_at": "2026-08-02T00:02:00+00:00",
                    "search_artifact_id": "phase2-search",
                    "target_ids": ["target-2"],
                },
                {
                    "job_id": "P2-003",
                    "goal": "disconfirm_or_strongest_delight",
                    "disposition": "no_material_yield",
                    "workstream": "product_axis",
                    "planned_at": "2026-08-02T00:03:00+00:00",
                    "search_artifact_id": "phase2-search",
                    "target_ids": ["target-3"],
                },
            ],
        }
    ]
    axis_inventory = {
        "schema_version": "consumer_brand_axis_inventory_v1",
        "subject": ledger["subject"],
        "cycle_id": ledger["cycle_id"],
        "created_at": "2026-08-02T00:00:00+00:00",
        "axes": [
            {
                key: ledger["product_axes"][0][key]
                for key in ("axis_id", "label", "polarity", "disposition")
            }
        ],
    }
    inventory_path = tmp_path / "consumer_axis_inventory.json"
    inventory_path.write_text(
        json.dumps(axis_inventory, indent=2) + "\n", encoding="utf-8"
    )
    inventory_digest = _artifact_hash(inventory_path)
    ledger["artifacts"].append(
        {
            "artifact_id": "axis-inventory",
            "locator": "consumer_axis_inventory.json",
            "sha256": inventory_digest,
        }
    )
    ledger["axis_inventory"] = {"artifact_id": "axis-inventory"}
    for job in ledger["product_axes"][0]["focused_search_jobs"]:
        job["axis_inventory_sha256"] = inventory_digest
    community_coding = {
        "schema_version": "community_axis_coding_v1",
        "subject": ledger["subject"],
        "cycle_id": ledger["cycle_id"],
        "rows": [
            {
                "thread_id": f"thread-{index}",
                "comment_id": f"comment-{index}",
                "product_context": "Lip Butter Balm",
                "axis_ids": ["packaging_reliability"],
                "contribution": "corroborates",
                "choice": "subject",
                "alternative_brand": None,
                "explicit_outcome": "none_explicit",
                "source_ref": f"depth-source#thread-{index}",
                "parser_limitation": None,
            }
            for index in range(40)
        ],
    }
    community_path = tmp_path / "community_axis_coding.json"
    community_path.write_text(
        json.dumps(community_coding, indent=2) + "\n", encoding="utf-8"
    )
    ledger["artifacts"].append(
        {
            "artifact_id": "community-axis-coding",
            "locator": "community_axis_coding.json",
            "sha256": _artifact_hash(community_path),
        }
    )
    ledger["community_axis_coding"] = {
        "artifact_id": "community-axis-coding"
    }
    ledger["target_reconciliation"] = [
        {
            "target_id": "target-1",
            "discovered_by_job_id": "P2-001",
            "axis_ids": ["packaging_reliability"],
            "locator": "https://example.test/thread-0",
            "source_family": "reddit_forum",
            "terminal_state": "used",
            "native_artifact_id": "thread-native-0",
            "evidence_refs": [
                {"family": "reddit_forum", "unit_id": "thread-0"}
            ],
        },
        {
            "target_id": "target-2",
            "discovered_by_job_id": "P2-002",
            "axis_ids": ["packaging_reliability"],
            "locator": "https://example.test/search-2",
            "source_family": "reddit_forum",
            "terminal_state": "no_material_yield",
            "evidence_refs": [],
        },
        {
            "target_id": "target-3",
            "discovered_by_job_id": "P2-003",
            "axis_ids": ["packaging_reliability"],
            "locator": "https://example.test/search-3",
            "source_family": "reddit_forum",
            "terminal_state": "no_material_yield",
            "evidence_refs": [],
        },
    ]
    serp_packet = _artifact(tmp_path, "serp_packet.json", '{"results": []}\n')
    ledger["artifacts"].append({"artifact_id": "serp-packet", **serp_packet})
    search_payload = {
        "schema_version": "consumer_brand_phase2_search_v1",
        "subject": ledger["subject"],
        "cycle_id": ledger["cycle_id"],
        "jobs": [
            {
                "job_id": job["job_id"],
                "axis_id": "packaging_reliability",
                "goal": job["goal"],
                "query": f"Summer Fridays {job['goal']}",
                "executed_at": "2026-08-02T00:09:00+00:00",
                "serp_packet_artifact_ids": ["serp-packet"],
                "selected_target_ids": job["target_ids"],
            }
            for job in ledger["product_axes"][0]["focused_search_jobs"]
        ],
    }
    search_path = tmp_path / "consumer_phase2_search.json"
    search_path.write_text(
        json.dumps(search_payload, indent=2) + "\n", encoding="utf-8"
    )
    ledger["artifacts"].append(
        {
            "artifact_id": "phase2-search",
            "locator": "consumer_phase2_search.json",
            "sha256": _artifact_hash(search_path),
        }
    )
    frontier_initial = _artifact(
        tmp_path, "reddit_frontier_initial.json", '{"results": ["initial"]}\n'
    )
    frontier_final_a = _artifact(
        tmp_path, "reddit_frontier_final_a.json", '{"results": []}\n'
    )
    frontier_final_b = _artifact(
        tmp_path, "reddit_frontier_final_b.json", '{"results": []}\n'
    )
    frontier_mandatory_2 = _artifact(
        tmp_path, "reddit_frontier_behavior.json", '{"results": []}\n'
    )
    frontier_mandatory_3 = _artifact(
        tmp_path, "reddit_frontier_brandless.json", '{"results": []}\n'
    )
    frontier_mandatory_4 = _artifact(
        tmp_path, "reddit_frontier_condition.json", '{"results": []}\n'
    )
    ledger["artifacts"].extend(
        [
            {"artifact_id": "reddit-frontier-initial", **frontier_initial},
            {"artifact_id": "reddit-frontier-final-a", **frontier_final_a},
            {"artifact_id": "reddit-frontier-final-b", **frontier_final_b},
            {"artifact_id": "reddit-frontier-behavior", **frontier_mandatory_2},
            {"artifact_id": "reddit-frontier-brandless", **frontier_mandatory_3},
            {"artifact_id": "reddit-frontier-condition", **frontier_mandatory_4},
        ]
    )
    initial_candidate_ids = [f"thread-{index}" for index in range(40)] + [
        "thread-duplicate-candidate"
    ]
    ledger["reddit_candidate_frontier"] = {
        "status": "source_exhausted",
        "reason": (
            "Every eligible candidate surfaced by the bounded discovery "
            "routes is terminally accounted below."
        ),
        "discovery_jobs": [
            {
                "job_id": "RWL-001",
                "axis_id": "packaging_reliability",
                "query": "Summer Fridays packaging Reddit",
                "executed_at": "2026-08-02T00:05:00+00:00",
                "artifact_ids": ["reddit-frontier-initial"],
                "candidate_thread_ids": initial_candidate_ids,
            },
            {
                "job_id": "RFD-M2-001",
                "axis_id": "packaging_reliability",
                "query": "Summer Fridays returned switched packaging Reddit",
                "executed_at": "2026-08-02T00:06:00+00:00",
                "artifact_ids": ["reddit-frontier-behavior"],
                "candidate_thread_ids": [],
            },
            {
                "job_id": "RFD-M3-001",
                "axis_id": "packaging_reliability",
                "query": "Lip Butter Balm applicator Reddit",
                "executed_at": "2026-08-02T00:07:00+00:00",
                "artifact_ids": ["reddit-frontier-brandless"],
                "candidate_thread_ids": [],
            },
            {
                "job_id": "RFD-M4-001",
                "axis_id": "packaging_reliability",
                "query": "Summer Fridays after use packaging condition Reddit",
                "executed_at": "2026-08-02T00:08:00+00:00",
                "artifact_ids": ["reddit-frontier-condition"],
                "candidate_thread_ids": [],
            },
            {
                "job_id": "RFD-A-001",
                "axis_id": "packaging_reliability",
                "query": "Summer Fridays packaging problems Reddit",
                "executed_at": "2026-08-02T00:10:00+00:00",
                "artifact_ids": ["reddit-frontier-final-a"],
                "candidate_thread_ids": [],
            },
            {
                "job_id": "RFD-B-001",
                "axis_id": "packaging_reliability",
                "query": "Summer Fridays applicator complaints Reddit",
                "executed_at": "2026-08-02T00:11:00+00:00",
                "artifact_ids": ["reddit-frontier-final-b"],
                "candidate_thread_ids": [],
            },
        ],
        "query_families": [
            {
                "family_id": "family-balanced",
                "family_kind": "balanced_axis_baseline",
                "family_role": "mandatory_high_yield",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RWL-001"],
                "planned_at": "2026-08-02T00:04:00+00:00",
                "status": "completed",
            },
            {
                "family_id": "family-behavior",
                "family_kind": "behavior_consequence_displacement",
                "family_role": "mandatory_high_yield",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RFD-M2-001"],
                "planned_at": "2026-08-02T00:05:00+00:00",
                "status": "completed",
            },
            {
                "family_id": "family-brandless",
                "family_kind": "brandless_exact_product",
                "family_role": "mandatory_high_yield",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RFD-M3-001"],
                "planned_at": "2026-08-02T00:06:00+00:00",
                "status": "completed",
            },
            {
                "family_id": "family-condition",
                "family_kind": "condition_post_use",
                "family_role": "mandatory_high_yield",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RFD-M4-001"],
                "planned_at": "2026-08-02T00:07:00+00:00",
                "status": "completed",
            },
            {
                "family_id": "family-final-a",
                "family_kind": "late_pain_stress_test",
                "family_role": "continuation",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RFD-A-001"],
                "planned_at": "2026-08-02T00:09:00+00:00",
                "status": "completed",
            },
            {
                "family_id": "family-final-b",
                "family_kind": "late_counterevidence_test",
                "family_role": "continuation",
                "scope_axis_ids": ["packaging_reliability"],
                "job_ids": ["RFD-B-001"],
                "planned_at": "2026-08-02T00:10:00+00:00",
                "status": "completed",
            },
        ],
        "candidates": [
            {
                "thread_id": f"thread-{index}",
                "discovered_by_job_id": "RWL-001",
                "terminal_state": "captured_used",
            }
            for index in range(40)
        ]
        + [
            {
                "thread_id": "thread-duplicate-candidate",
                "discovered_by_job_id": "RWL-001",
                "terminal_state": "duplicate_thread",
                "reason": "Exact crosspost of thread-3.",
            }
        ],
    }
    family_jobs = [
        ("family-balanced", "RWL-001", 40, True),
        ("family-behavior", "RFD-M2-001", 0, False),
        ("family-brandless", "RFD-M3-001", 0, False),
        ("family-condition", "RFD-M4-001", 0, False),
        ("family-final-a", "RFD-A-001", 0, False),
        ("family-final-b", "RFD-B-001", 0, False),
    ]
    ledger["closure"]["batches"] = [
        {
            "batch_id": f"batch-{index}",
            "query_family_id": family_id,
            "job_ids": [job_id],
            "batch_kind": "live_acquisition",
            "candidate_moves_checked": 1,
            "material_incremental_value": material,
            "material_additions": (
                [
                    {
                        "addition_id": "addition-packaging-axis",
                        "kind": "new_axis",
                        "axis_ids": ["packaging_reliability"],
                        "evidence_refs": ["reddit_forum:thread-0"],
                        "decision_effect": "Established the packaging pain axis.",
                    }
                ]
                if material
                else []
            ),
            "new_material_seams": 1 if material else 0,
            "changed_material_dispositions": 0,
            "new_product_axes": 1 if material else 0,
            "changed_axis_strengths": 0,
            "changed_axis_incidence": 0,
            "new_customer_segments": 0,
            "new_product_conditions": 0,
            "new_comparison_choices": 0,
            "new_competitor_alternatives": 0,
            "new_usable_reddit_threads": usable,
        }
        for index, (family_id, job_id, usable, material) in enumerate(
            family_jobs, start=1
        )
    ]
    ledger["closure"]["decision_frontier"] = {
        "status": "decision_mature",
        "decision_mature_axis_ids": ["packaging_reliability"],
        "open_axis_ids": [],
    }
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return {"locator": "evidence_depth_ledger.json", "sha256": _artifact_hash(path)}


def _campaign_view(tmp_path: Path) -> dict[str, str]:
    view = {
        "schema_version": "campaign_evidence_view_v1",
        "subject": "Summer Fridays",
        "cycle_id": "summer_fridays_confirmation",
        "units": [
            {
                "unit_id": "cv-owned-1",
                "source_role": "owned_post",
                "publisher_identity": "summerfridays",
                "brand_binding": "Summer Fridays",
                "product_bindings": ["Lip Butter Balm"],
                "claim_bindings": ["hydration"],
                "source_surface": "instagram",
                "source_refs": ["packet:owned-1"],
                "published_at": "2026-07-25",
                "observed_at": "2026-08-01",
                "captured_at": "2026-08-01T00:00:00+00:00",
                "relationship_posture": "owned",
                "linkage_posture": "direct",
                "independent_origin_key": "creator:summerfridays",
                "independent_origin_credit": False,
                "claim_ceiling": "owned direction evidence only",
            },
            {
                # Direct partnership byline: observed relationship, direct
                # ad-to-creator linkage.
                "unit_id": "cv-partner-ad-1",
                "source_role": "paid_ad",
                "publisher_identity": "JADE LILY with Summer Fridays",
                "brand_binding": "Summer Fridays",
                "product_bindings": ["Lip Butter Balm"],
                "claim_bindings": [],
                "source_surface": "meta_ad_library",
                "source_refs": ["packet:meta-ad-1"],
                "published_at": "2026-07-15",
                "observed_at": None,
                "captured_at": "2026-08-01T00:00:00+00:00",
                "relationship_posture": "partnership_byline_observed",
                "linkage_posture": "direct",
                "independent_origin_key": "advertiser:summerfridays",
                "independent_origin_credit": False,
                "claim_ceiling": "advertiser strategy evidence, not customer proof",
            },
            {
                "unit_id": "cv-creator-1",
                "source_role": "creator_authored",
                "publisher_identity": "creator-a",
                "brand_binding": "Summer Fridays",
                "product_bindings": [],
                "claim_bindings": [],
                "source_surface": "youtube",
                "source_refs": ["packet:creator-a-1"],
                "published_at": None,
                "observed_at": "2026-08-01",
                "captured_at": "2026-08-01T00:00:00+00:00",
                "relationship_posture": "apparently_independent",
                "linkage_posture": "unknown",
                "independent_origin_key": "creator:creator-a",
                "independent_origin_credit": True,
                "claim_ceiling": "single creator perspective",
            },
            {
                # Unknown creator relationship stays relationship_unknown and
                # earns no independence credit.
                "unit_id": "cv-creator-2",
                "source_role": "creator_authored",
                "publisher_identity": "creator-b",
                "brand_binding": "Summer Fridays",
                "product_bindings": [],
                "claim_bindings": [],
                "source_surface": "tiktok",
                "source_refs": ["packet:creator-b-1"],
                "published_at": None,
                "observed_at": None,
                "captured_at": "2026-08-01T00:00:00+00:00",
                "relationship_posture": "relationship_unknown",
                "linkage_posture": "unknown",
                "independent_origin_key": "creator:creator-b",
                "independent_origin_credit": False,
                "claim_ceiling": "relationship unknown; not organic",
            },
        ],
        "clusters": [
            {
                "cluster_id": "cl-direct-1",
                "basis": "direct",
                "member_unit_ids": ["cv-owned-1", "cv-partner-ad-1"],
            },
            {
                # Inferred message cluster with an honest ceiling.
                "cluster_id": "cl-inferred-1",
                "basis": "inferred",
                "member_unit_ids": ["cv-creator-1", "cv-creator-2"],
                "provenance": "shared creative fingerprint across both units",
                "reversal_condition": (
                    "distinct creative origins observed for either unit"
                ),
            },
        ],
    }
    path = tmp_path / "campaign_evidence_view.json"
    path.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
    return {"locator": "campaign_evidence_view.json", "sha256": _artifact_hash(path)}


def _understanding_route(tmp_path: Path) -> dict:
    frame = _artifact(tmp_path, "serp_phase1_comparator_frame.md")
    adjudicated = _artifact(tmp_path, "serp_phase2_adjudicated_set.md")
    verification_return = _artifact(tmp_path, "verification_return.md")
    return {
        "route_version": "1.1.0",
        "comparator_closure": {
            "state": "phase_a_competitor_context_closed",
            "candidate_frame": frame,
            "adjudicated_set": adjudicated,
            "frame_candidate_ids": ["cand-elf", "cand-rhode", "cand-generic"],
            "candidates": [
                {
                    "candidate_id": "cand-elf",
                    "name": "e.l.f. Glow Reviver",
                    "material": True,
                    "disposition": "promoted",
                    "decision_ready": True,
                    "subject_product_identity": (
                        "Summer Fridays Lip Butter Balm 15 g"
                    ),
                    "competitor_product_identity": (
                        "e.l.f. Glow Reviver Lip Oil 0.52 oz"
                    ),
                    "claim_ceiling": (
                        "observed comparison context; not market share"
                    ),
                    "portfolio_role": {
                        "scope": "product",
                        "assessed_identity": (
                            "e.l.f. Glow Reviver Lip Oil 0.52 oz"
                        ),
                        "status": "likely_major",
                        "basis": "multi_source_inference",
                        "evidence_refs": ["elf-owned-range", "elf-ulta-list"],
                    },
                    "observed_positions": [
                        {
                            "position_id": "elf-ulta-lip-oil-2026-08-06",
                            "scope_kind": "retailer_category",
                            "source_or_retailer": "Ulta",
                            "market_scope": "US / lip oil category page",
                            "observed_at": "2026-08-06T12:00:00Z",
                            "rank": 2,
                            "list_size": 24,
                            "label": "second item in the observed list",
                            "evidence_refs": ["elf-ulta-list"],
                        }
                    ],
                    "shared_axis_ids": ["format", "price", "claim_language"],
                    "lane_evidence": {
                        "co1_owned_ad_positioning": {
                            "status": "observed",
                            "evidence_refs": ["elf-owned-range"],
                        },
                        "co2_retailer_product": {
                            "status": "observed",
                            "evidence_refs": ["elf-ulta-list"],
                        },
                        "co3_retailer_review": {
                            "status": "observed",
                            "evidence_refs": ["elf-ulta-reviews"],
                        },
                        "co3_reddit_community": {
                            "status": "observed",
                            "evidence_refs": ["elf-reddit-thread-1"],
                        },
                        "campaign_creator_comparison": {
                            "status": "observed",
                            "evidence_refs": ["elf-creator-post-1"],
                        },
                    },
                },
                {
                    # Terminal watch-only competitor.
                    "candidate_id": "cand-rhode",
                    "name": "Rhode Peptide Lip Treatment",
                    "material": True,
                    "disposition": "watch_listed",
                    "decision_ready": False,
                    "subject_product_identity": (
                        "Summer Fridays Lip Butter Balm 15 g"
                    ),
                    "competitor_product_identity": (
                        "Rhode Peptide Lip Treatment 10 ml"
                    ),
                    "claim_ceiling": "watch-only; no decision licence",
                    "portfolio_role": {
                        "scope": "product",
                        "assessed_identity": (
                            "Rhode Peptide Lip Treatment 10 ml"
                        ),
                        "status": "unclear",
                        "basis": "unresolved",
                        "evidence_refs": [],
                        "gap_reason": (
                            "sampled public sources did not establish portfolio role"
                        ),
                    },
                    "observed_positions": [],
                    "position_gap_reason": (
                        "sampled sources exposed no stable ordered list"
                    ),
                    "lane_evidence": {
                        "co1_owned_ad_positioning": {
                            "status": "none_found",
                            "gap_reason": "no material owned/ad comparison found",
                        },
                        "co2_retailer_product": {
                            "status": "observed",
                            "evidence_refs": ["rhode-pdp"],
                        },
                        "co3_retailer_review": {
                            "status": "none_found",
                            "gap_reason": "no retailer review corpus was exposed",
                        },
                        "co3_reddit_community": {
                            "status": "none_found",
                            "gap_reason": "no material sampled comparison found",
                        },
                        "campaign_creator_comparison": {
                            "status": "blocked",
                            "gap_reason": "creator post was not retrievable",
                        },
                    },
                },
                {
                    # Rejected non-competitor.
                    "candidate_id": "cand-generic",
                    "name": "generic commodity name",
                    "material": False,
                    "disposition": "rejected",
                    "decision_ready": False,
                    "claim_ceiling": "harvest-quality rejection",
                },
            ],
        },
        "campaign_evidence_integration": {
            "status": "completed",
            "view": _campaign_view(tmp_path),
            "targeted_capture_requests": [
                {
                    "request_id": "CEI-REQ-001",
                    "target": "exact creator post resolving ad linkage",
                    "disposition": "captured",
                }
            ],
        },
        "verification_requests": [
            {
                "request_id": "VER-001",
                "product_identity": "Summer Fridays Sheer Skin Tint",
                "trigger_kind": "contradiction",
                "trigger_evidence_refs": ["thread-0", "native-0"],
                "claim": "SPF claim drift across sampled PDP history",
                "status": "completed",
                "return": verification_return,
            }
        ],
        "retailer_state_accounting": {
            "claims": [
                {
                    "claim_id": "RSA-001",
                    "kind": "retailer_state_snapshot",
                    "retailer": "sephora",
                    "product_identity": "Lip Butter Balm 15 g",
                    "market_scope": "US",
                    "current_observation_ref": "pdp-obs-2",
                },
                {
                    # Comparable two-snapshot retailer change.
                    "claim_id": "RSA-002",
                    "kind": "retailer_state_change",
                    "retailer": "sephora",
                    "product_identity": "Lip Butter Balm 15 g",
                    "market_scope": "US",
                    "prior_observation_ref": "pdp-obs-1",
                    "current_observation_ref": "pdp-obs-2",
                    "change_summary": "in_stock -> out_of_stock",
                },
                {
                    "claim_id": "RSA-003",
                    "kind": "movement_unresolved_baseline_only",
                    "retailer": "ulta",
                    "product_identity": "Jet Lag Mask 64 g",
                    "market_scope": "US",
                    "current_observation_ref": "pdp-obs-3",
                },
            ]
        },
    }


def _blocked_seal(tmp_path: Path) -> dict:
    specialist_returns = []
    for actor in ("CO1", "CO2", "CO3"):
        artifact = _artifact(tmp_path, f"{actor.lower()}_terminal.md")
        specialist_returns.append(
            {
                "actor": actor,
                "terminal_locator": artifact["locator"],
                "sha256": artifact["sha256"],
                "status": "BLOCKED_TERMINAL",
            }
        )
    phase1 = _artifact(tmp_path, "serp_phase1.md")
    phase2 = _artifact(tmp_path, "serp_phase2.md")
    receipt = _artifact(
        tmp_path,
        "decision_receipt.json",
        json.dumps({"entries": []}, indent=2) + "\n",
    )
    phase2_jobs = [f"P2-{index:03d}" for index in range(1, 6)]
    terminals = {row["actor"]: row for row in specialist_returns}

    def completed_route(
        route_id: str, phase: str, job_id: str, actor: str
    ) -> dict:
        terminal = terminals[actor]
        return {
            "route_id": route_id,
            "phase": phase,
            "required": True,
            "material": True,
            "planned_job_ids": [job_id],
            "planned_count": 1,
            "completed_job_ids": [job_id],
            "completed_count": 1,
            "blocked_job_ids": [],
            "blocked_count": 0,
            "unrun_job_ids": [],
            "unrun_count": 0,
            "terminal_artifact_locator": terminal["terminal_locator"],
            "terminal_artifact_sha256": terminal["sha256"],
        }

    specialist_routes = [
        completed_route(
            "official_retailer_authorization", "co1", "AUTH-001", "CO1"
        ),
        completed_route(
            "google_ads_transparency", "co1", "GADS-001", "CO1"
        ),
        completed_route("meta_ads_library", "co1", "MADS-001", "CO1"),
        completed_route("retailer_full_pdp", "co2", "PDP-001", "CO2"),
        completed_route("reddit_weekly_lake", "co3", "RWL-001", "CO3"),
        completed_route("reddit_community_scout", "co3", "RCS-001", "CO3"),
    ]
    reddit_route = next(
        row
        for row in specialist_routes
        if row["route_id"] == "reddit_community_scout"
    )
    frontier_job_ids = [
        "RFD-M2-001",
        "RFD-M3-001",
        "RFD-M4-001",
        "RFD-A-001",
        "RFD-B-001",
    ]
    reddit_route["planned_job_ids"].extend(frontier_job_ids)
    reddit_route["planned_count"] = 1 + len(frontier_job_ids)
    reddit_route["completed_job_ids"].extend(frontier_job_ids)
    reddit_route["completed_count"] = 1 + len(frontier_job_ids)
    understanding_route = _understanding_route(tmp_path)
    campaign_view = understanding_route["campaign_evidence_integration"]["view"]
    campaign_route = {
        "route_id": "campaign_evidence_integration",
        "phase": "campaign_integration",
        "required": True,
        "material": True,
        "planned_job_ids": ["CEI-001"],
        "planned_count": 1,
        "completed_job_ids": ["CEI-001"],
        "completed_count": 1,
        "blocked_job_ids": [],
        "blocked_count": 0,
        "unrun_job_ids": [],
        "unrun_count": 0,
        "terminal_artifact_locator": campaign_view["locator"],
        "terminal_artifact_sha256": campaign_view["sha256"],
    }
    return {
        "schema_version": SEAL_VERSION,
        "cycle_id": "summer_fridays_confirmation",
        "subject": "Summer Fridays",
        "acquisition_gate": "blocked",
        "seal_state": "BLOCKED_ACQUISITION_INCOMPLETE",
        "deliver_allowed": False,
        "controller_placement": {
            "controller_actor": "CO0",
            "placement": "top_level",
            "worker_slots_required": 3,
            "worker_slots_available": 3,
        },
        "route_capability_preflight": {
            "checked_before_network_capture": True,
            "google_serp": {
                "mode": "cooldown_only",
                "primary_route_ready": True,
                "queue_state_writable": True,
                "persistent_fallback_ready": False,
            },
            "reddit_weekly_lake": {"reader_status": "ready"},
            "paid_ad_transparency": {
                "google_ads_transparency": "ready",
                "meta_ads_library": "ready",
            },
            "tiktok_shop": {
                "trigger": "not_required",
                "route_status": "not_checked_until_trigger",
            },
            "native_social": {
                platform: {
                    "trigger": "not_required",
                    "route_status": "not_checked_until_trigger",
                }
                for platform in ("tiktok", "instagram", "youtube")
            },
        },
        "specialist_returns": specialist_returns,
        "post_phase1_continuation_mode": "bounded_salvage",
        "route_job_accounting": [
            {
                "route_id": "serp_phase1",
                "phase": "serp_phase1",
                "required": True,
                "material": True,
                "planned_job_ids": ["P1-001"],
                "planned_count": 1,
                "completed_job_ids": ["P1-001"],
                "completed_count": 1,
                "blocked_job_ids": [],
                "blocked_count": 0,
                "unrun_job_ids": [],
                "unrun_count": 0,
                "terminal_artifact_locator": phase1["locator"],
                "terminal_artifact_sha256": phase1["sha256"],
            },
            *specialist_routes,
            campaign_route,
            {
                "route_id": "serp_phase2",
                "phase": "serp_phase2",
                "required": True,
                "material": True,
                "planned_job_ids": list(phase2_jobs),
                "planned_count": 5,
                "completed_job_ids": [],
                "completed_count": 0,
                "blocked_job_ids": [],
                "blocked_count": 0,
                "unrun_job_ids": list(phase2_jobs),
                "unrun_count": 5,
                "terminal_artifact_locator": phase2["locator"],
                "terminal_artifact_sha256": phase2["sha256"],
            },
        ],
        "serp_phase2_decision_receipt": {
            **receipt,
            "entries": 0,
        },
        "evidence_depth_ledger": _depth_ledger(tmp_path),
        "understanding_route": understanding_route,
        "resume_contract": {
            "pending_job_ids": list(phase2_jobs),
            "reusable_artifacts": [
                {
                    "locator": specialist_returns[0]["terminal_locator"],
                    "sha256": specialist_returns[0]["sha256"],
                    "invalid_if": [
                        "bound question changes",
                        "artifact hash changes",
                    ],
                }
            ],
        },
    }


def _write_seal(tmp_path: Path, seal: dict) -> Path:
    path = tmp_path / "acquisition_seal.md"
    path.write_text(
        "# Acquisition Seal\n\n```yaml\n"
        + yaml.safe_dump(
            {"phase_acquisition_seal": seal},
            sort_keys=False,
            allow_unicode=True,
        )
        + "```\n",
        encoding="utf-8",
    )
    return path


def _validate(tmp_path: Path, seal: dict) -> list[str]:
    return validate_phase_acquisition_seal(
        seal_path=_write_seal(tmp_path, seal), repo_root=tmp_path
    )


def _rewrite_depth_reference(
    seal: dict, ledger_path: Path, ledger: dict
) -> None:
    ledger_path.write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }


def _make_passing(seal: dict) -> dict:
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )
    return seal


def test_blocked_seal_accounts_for_five_unrun_phase2_jobs(
    tmp_path: Path,
) -> None:
    assert _validate(tmp_path, _blocked_seal(tmp_path)) == []


def test_empty_decision_receipt_cannot_hide_unrun_phase2_jobs_in_passing_seal(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "passing_seal_has_material_pending_jobs" in findings
    assert "passing_seal_has_resume_work" in findings


def test_passing_seal_accepts_supported_non_material_blocked_route(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    weekly = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "reddit_weekly_lake"
    )
    weekly["material"] = False
    weekly["blocked_job_ids"] = list(weekly["completed_job_ids"])
    weekly["blocked_count"] = weekly["completed_count"]
    weekly["completed_job_ids"] = []
    weekly["completed_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert _validate(tmp_path, seal) == []


def test_missing_phase2_query_id_breaks_exact_accounting(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["planned_job_ids"].pop()
    phase2["planned_count"] = 4

    assert "planned_jobs_not_fully_accounted" in _validate(tmp_path, seal)


def test_specialist_terminal_hash_drift_is_visible(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    terminal = tmp_path / seal["specialist_returns"][0]["terminal_locator"]
    terminal.write_text("controller-edited bytes\n", encoding="utf-8")

    assert "specialist_terminal_hash_mismatch" in _validate(tmp_path, seal)


def test_text_artifact_line_endings_do_not_forge_hash_drift(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    terminal = tmp_path / seal["specialist_returns"][0]["terminal_locator"]
    lf_content = terminal.read_bytes().replace(b"\r\n", b"\n")
    terminal.write_bytes(lf_content.replace(b"\n", b"\r\n"))

    assert _validate(tmp_path, seal) == []


def test_specialist_actor_set_cannot_be_relabelled_by_controller(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["specialist_returns"][1]["actor"] = "CO0"

    assert "specialist_returns_must_be_co1_co2_co3" in _validate(tmp_path, seal)


def test_fully_completed_seal_passes_with_no_resume_work(tmp_path: Path) -> None:
    seal = deepcopy(_blocked_seal(tmp_path))
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert _validate(tmp_path, seal) == []


def test_consumer_brand_v2_passes_with_axis_evidence_and_coding(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["evidence_depth_ledger"] = _consumer_depth_ledger(tmp_path)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_verified_absent_counterevidence_marker_waives_counterevidence_ref(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    usefulness = ledger["product_axes"][0]["decision_usefulness"]
    usefulness["counterevidence_absent_verified"] = True
    for ref in usefulness["decision_bearing_support_refs"]:
        if ref["role"] == "counterevidence":
            ref["role"] = "segment_or_condition"
    usefulness["strongest_counterevidence"] = (
        "No subject-owned positive event survives re-derivation; recorded as "
        "verified absent, not restated."
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_contradictory_counterevidence_absence_marker_is_visible(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    usefulness = ledger["product_axes"][0]["decision_usefulness"]
    usefulness["counterevidence_absent_verified"] = True
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert (
        "contradictory_counterevidence_absence_marker:packaging_reliability"
        in findings
    )


def test_consumer_brand_v3_requires_three_phase2_goals(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["focused_search_jobs"].pop()
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "incomplete_product_axis_search_goals:packaging_reliability" in findings


def test_consumer_brand_v3_rejects_serp_pointer_as_native_capture(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["target_reconciliation"][0].pop("native_artifact_id")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "missing_consumer_target_native_body:target-1" in findings


def test_consumer_brand_v3_rejects_omitted_captured_evidence_unit(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["target_reconciliation"][0]["evidence_refs"][0][
        "unit_id"
    ] = "captured-but-omitted"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "unresolved_consumer_target_evidence_ref:target-1" in findings


def test_consumer_brand_v3_requires_comment_coding_for_each_reddit_thread(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "community_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["rows"].pop()
    coding_path.write_text(
        json.dumps(coding, indent=2) + "\n", encoding="utf-8"
    )
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "community-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "independent_reddit_threads_without_comment_coding" in findings


def test_consumer_brand_v3_reddit_floor_needs_explicit_exhaustion(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["families"]["reddit_forum"]["threads"] = ledger["families"][
        "reddit_forum"
    ]["threads"][:20]
    coding_path = tmp_path / "community_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["rows"] = coding["rows"][:20]
    coding_path.write_text(
        json.dumps(coding, indent=2) + "\n", encoding="utf-8"
    )
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "community-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "passing_seal_below_depth_floor:reddit_forum_threads" in findings


def test_consumer_brand_v3_accepts_proven_reddit_source_exhaustion(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["families"]["reddit_forum"]["threads"] = ledger["families"][
        "reddit_forum"
    ]["threads"][:20]
    coding_path = tmp_path / "community_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["rows"] = coding["rows"][:20]
    coding_path.write_text(
        json.dumps(coding, indent=2) + "\n", encoding="utf-8"
    )
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "community-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    ledger["reddit_forum_floor_exception"] = {
        "status": "source_exhausted",
        "expected_minimum": 40,
        "observed_usable_threads": 20,
        "reason": "All selected axis queries and targets were exhausted.",
    }
    kept_threads = {
        row["thread_id"] for row in ledger["families"]["reddit_forum"]["threads"]
    }
    ledger["reddit_candidate_frontier"]["candidates"] = [
        row
        for row in ledger["reddit_candidate_frontier"]["candidates"]
        if row["terminal_state"] != "captured_used"
        or row["thread_id"] in kept_threads
    ]
    initial_discovery = next(
        row
        for row in ledger["reddit_candidate_frontier"]["discovery_jobs"]
        if row["job_id"] == "RWL-001"
    )
    initial_discovery["candidate_thread_ids"] = [
        row["thread_id"]
        for row in ledger["reddit_candidate_frontier"]["candidates"]
        if row["discovered_by_job_id"] == "RWL-001"
    ]
    next(
        row
        for row in ledger["closure"]["batches"]
        if row["query_family_id"] == "family-balanced"
    )["new_usable_reddit_threads"] = 20
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v3_final_batches_must_be_live_acquisition(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1]["batch_kind"] = "desk_audit"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "saturation_batch_not_live_acquisition" in findings


def test_consumer_brand_v3_phase2_must_follow_axis_inventory(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["focused_search_jobs"][0][
        "planned_at"
    ] = "2026-08-01T23:59:00+00:00"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "product_axis_search_not_planned_after_inventory:packaging_reliability" in findings


def test_consumer_brand_v2_rejects_family_counts_without_axes(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger.pop("product_axes")
    ledger.pop("retailer_axis_coding")
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "missing_consumer_brand_product_axes" in findings
    assert "passing_consumer_brand_seal_without_axis_closure" in findings


def test_consumer_brand_v2_recomputes_retailer_axis_incidence(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["retailer_incidence"][0][
        "axis_mention_count"
    ] = 200
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert any(
        finding.startswith(
            "retailer_axis_incidence_mismatch:packaging_reliability:"
        )
        and finding.endswith(":axis_mention_count")
        for finding in findings
    )


def test_consumer_brand_v2_malformed_axis_codes_break_axis_closure(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["rows"][0]["axis_codes"] = {"packaging_reliability": True}
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    for row in ledger["artifacts"]:
        if row["artifact_id"] == "retailer-axis-coding":
            row["sha256"] = _artifact_hash(coding_path)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "invalid_coded_review_axis_codes" in findings
    assert "passing_consumer_brand_seal_without_axis_closure" in findings


def test_consumer_brand_v2_keeps_choice_outcomes_on_the_causal_axis(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    for corpus in coding["corpora"]:
        first = next(
            row
            for row in coding["rows"]
            if row["corpus_id"] == corpus["corpus_id"]
        )
        first["axis_codes"].append(
            {
                "axis_id": "hydration_performance",
                "choice_outcomes": ["none_explicit"],
            }
        )
    hydration = deepcopy(ledger["product_axes"][0])
    hydration.update(
        {
            "axis_id": "hydration_performance",
            "label": "Hydration performance",
            "strength": "recurring",
            "disposition": "bounded_nonmaterial",
            "retailer_incidence": [
                {
                    "corpus_id": corpus["corpus_id"],
                    "eligible_text_review_count": (
                        corpus["unique_review_count"]
                        - corpus["cross_corpus_duplicate_count"]
                    ),
                    "axis_mention_count": 1,
                    "negative_choice_review_count": 0,
                    "positive_choice_review_count": 0,
                    "disclosed_incentivized_axis_mention_count": 0,
                }
                for corpus in ledger["families"]["retailer_reviews"]["corpora"]
            ],
            "focused_search_jobs": [],
        }
    )
    ledger["product_axes"].append(hydration)
    inventory_path = tmp_path / "consumer_axis_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["axes"].append(
        {
            key: hydration[key]
            for key in ("axis_id", "label", "polarity", "disposition")
        }
    )
    inventory_path.write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    inventory_digest = _artifact_hash(inventory_path)
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "axis-inventory"
    )["sha256"] = inventory_digest
    for job in ledger["product_axes"][0]["focused_search_jobs"]:
        job["axis_inventory_sha256"] = inventory_digest
    community_path = tmp_path / "community_axis_coding.json"
    community = json.loads(community_path.read_text(encoding="utf-8"))
    for row in community["rows"][:3]:
        row["axis_ids"].append("hydration_performance")
    community_path.write_text(
        json.dumps(community, indent=2) + "\n", encoding="utf-8"
    )
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "community-axis-coding"
    )["sha256"] = _artifact_hash(community_path)
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "retailer-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v2_reuses_pinned_unchanged_retailer_coding(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["cycle_id"] = "prior-consumer-cycle"
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "retailer-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    ledger["retailer_axis_coding"]["reuse"] = {
        "mode": "pinned_unchanged_reuse",
        "source_cycle_id": coding["cycle_id"],
        "current_cycle_id": ledger["cycle_id"],
        "reason": "No retailer corpus or coding rule changed in this continuation.",
    }
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v2_rejects_unreceipted_retailer_coding_reuse(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["cycle_id"] = "prior-consumer-cycle"
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "retailer-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "retailer_axis_coding_cycle_id_mismatch" in findings
    assert "passing_consumer_brand_seal_without_axis_closure" in findings


def test_consumer_brand_v2_rejects_product_context_outside_corpus(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    coding_path = tmp_path / "retailer_product_axis_coding.json"
    coding = json.loads(coding_path.read_text(encoding="utf-8"))
    coding["rows"][0]["product_context_id"] = "not-in-this-corpus"
    coding_path.write_text(json.dumps(coding, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "retailer-axis-coding"
    )["sha256"] = _artifact_hash(coding_path)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "coded_review_product_context_outside_corpus" in findings
    assert "passing_consumer_brand_seal_without_axis_closure" in findings


def test_consumer_brand_v2_counts_distinct_social_creators_for_strength(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["native_social"]["posts"][:3]:
        row["creator_id"] = "one-creator"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "product_axis_strength_mismatch:packaging_reliability:recurring" in findings


@pytest.mark.parametrize(
    ("source_type", "relationship"),
    [
        ("company_profile", "apparently_independent"),
        ("consumer_editorial", "relationship_unknown"),
    ],
)
def test_consumer_brand_v2_nonconsumer_external_units_do_not_supply_support(
    tmp_path: Path,
    source_type: str,
    relationship: str,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["support_refs"] = [
        {
            "family": "reddit_forum",
            "unit_id": f"thread-{index}",
            "contribution": "corroborates",
            "choice": "subject",
        }
        for index in range(3)
    ] + [
        {
            "family": "external_context",
            "unit_id": f"outside-{index}",
            "contribution": "sharpens",
            "choice": "conditional",
        }
            for index in range(3)
        ]
    ledger["product_axes"][0]["decision_usefulness"][
        "decision_bearing_support_refs"
    ] = [
        {
            "family": "reddit_forum",
            "unit_id": "thread-0",
            "role": "behavior_or_purchase_consequence",
        },
        {
            "family": "reddit_forum",
            "unit_id": "thread-1",
            "role": "counterevidence",
        },
        {
            "family": "external_context",
            "unit_id": "outside-0",
            "role": "customer_tension",
        },
    ]
    for row in ledger["families"]["external_context"]["units"][:3]:
        row["source_type"] = source_type
        row["relationship"] = relationship
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "product_axis_strength_mismatch:packaging_reliability:signal" in findings


def test_consumer_brand_v2_independent_editorial_origins_supply_support(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["support_refs"] = [
        {
            "family": "reddit_forum",
            "unit_id": f"thread-{index}",
            "contribution": "corroborates",
            "choice": "subject",
        }
        for index in range(3)
    ] + [
        {
            "family": "external_context",
            "unit_id": f"outside-{index}",
            "contribution": "sharpens",
            "choice": "conditional",
        }
        for index in range(3)
    ]
    ledger["product_axes"][0]["decision_usefulness"][
        "decision_bearing_support_refs"
    ] = [
        {
            "family": "reddit_forum",
            "unit_id": "thread-0",
            "role": "behavior_or_purchase_consequence",
        },
        {
            "family": "reddit_forum",
            "unit_id": "thread-1",
            "role": "counterevidence",
        },
        {
            "family": "external_context",
            "unit_id": "outside-0",
            "role": "customer_tension",
        },
    ]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v2_owned_post_date_must_be_iso_calendar_date(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["families"]["native_social"]["posts"][10].update(
        {
            "relationship": "owned",
            "published_at": "July 41, 2026",
            "direction_event_tags": ["campaign"],
        }
    )
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    assert "missing_owned_social_published_at" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_v2_owned_posts_do_not_supply_independent_support(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["native_social"]["posts"][:3]:
        row.update(
            {
                "relationship": "owned",
                "published_at": "2026-07-01",
                "direction_event_tags": ["campaign"],
            }
        )
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert (
        "product_axis_strength_mismatch:packaging_reliability:signal"
        in findings
    )


def test_consumer_brand_v2_requires_terminal_focused_search(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["focused_search_jobs"][0][
        "disposition"
    ] = "pending"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert (
        "invalid_product_axis_search_disposition:packaging_reliability"
        in findings
    )


def test_consumer_brand_v2_focused_search_disposition_matches_route_state(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["focused_search_jobs"][0][
        "disposition"
    ] = "blocked_no_route"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "product_axis_search_state_mismatch:packaging_reliability" in findings


def test_consumer_brand_v4_material_counters_require_structured_additions(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1]["changed_axis_strengths"] = 1
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"] = {
        "locator": ledger_path.name,
        "sha256": _artifact_hash(ledger_path),
    }

    findings = _validate(tmp_path, _make_passing(seal))

    assert "material_addition_counter_mismatch" in findings
    assert "passing_seal_without_saturation_closure" in findings


def test_completed_jobs_cannot_replace_depth_ledger(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.pop("evidence_depth_ledger")
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert "missing_evidence_depth_ledger" in _validate(tmp_path, seal)


def test_passing_seal_rejects_floor_count_without_independent_units(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    ledger_path = tmp_path / seal["evidence_depth_ledger"]["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["outside_in"]["units"][1:]:
        row["independence"] = "syndicated_copy"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert (
        "passing_seal_below_depth_floor:outside_in_independent_units"
        in findings
    )


def test_passing_seal_requires_two_dry_saturation_batches(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    ledger_path = tmp_path / seal["evidence_depth_ledger"]["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1]["material_incremental_value"] = True
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "saturation_batch_still_material" in findings
    assert "passing_seal_without_saturation_closure" in findings


def test_blocked_seal_allows_partial_rating_bands(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    ledger_path = tmp_path / seal["evidence_depth_ledger"]["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["retailer_reviews"]["corpora"]:
        row["rating_bands"] = ["high"]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)

    assert _validate(tmp_path, seal) == []


def test_passing_seal_requires_complete_rating_bands(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    ledger_path = tmp_path / seal["evidence_depth_ledger"]["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["retailer_reviews"]["corpora"]:
        row["rating_bands"] = ["mid", "high"]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert "retailer_review_rating_bands_incomplete" in _validate(tmp_path, seal)


def test_cli_payload_records_audited_seal_schema_version(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["schema_version"] = LEGACY_SEAL_VERSION
    seal.pop("evidence_depth_ledger")
    path = _write_seal(tmp_path, seal)

    exit_code = main(
        [
            "--seal",
            str(path),
            "--repo-root",
            str(tmp_path),
            "--allow-legacy-v2",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["seal_schema_version"] == LEGACY_SEAL_VERSION


@pytest.mark.parametrize(
    ("field", "replacement", "expected_finding"),
    [
        (
            "subject",
            "Another Company",
            "evidence_depth_ledger_subject_mismatch",
        ),
        (
            "cycle_id",
            "another_cycle",
            "evidence_depth_ledger_cycle_id_mismatch",
        ),
    ],
)
def test_depth_ledger_identity_must_match_seal(
    tmp_path: Path,
    field: str,
    replacement: str,
    expected_finding: str,
) -> None:
    seal = _blocked_seal(tmp_path)
    ledger_path = tmp_path / seal["evidence_depth_ledger"]["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger[field] = replacement
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)

    assert expected_finding in _validate(tmp_path, seal)


@pytest.mark.parametrize(
    ("field", "expected_finding"),
    [
        ("subject", "missing_seal_subject"),
        ("cycle_id", "missing_seal_cycle_id"),
    ],
)
def test_v3_seal_requires_identity_for_depth_binding(
    tmp_path: Path, field: str, expected_finding: str
) -> None:
    seal = _blocked_seal(tmp_path)
    seal.pop(field)

    assert expected_finding in _validate(tmp_path, seal)


def test_legacy_v2_requires_explicit_historical_audit(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["schema_version"] = LEGACY_SEAL_VERSION
    seal.pop("evidence_depth_ledger")
    path = _write_seal(tmp_path, seal)

    assert "legacy_v2_requires_explicit_historical_audit" in (
        validate_phase_acquisition_seal(seal_path=path, repo_root=tmp_path)
    )
    assert validate_phase_acquisition_seal(
        seal_path=path,
        repo_root=tmp_path,
        allow_legacy_v2=True,
    ) == []


def test_passing_seal_cannot_omit_mandatory_specialist_route(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_job_accounting"] = [
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] != "google_ads_transparency"
    ]

    findings = _validate(tmp_path, seal)

    assert any(
        finding.startswith("missing_required_route_accounting:")
        and "google_ads_transparency" in finding
        for finding in findings
    )


def test_triggered_native_route_requires_accounting(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_capability_preflight"]["native_social"]["youtube"] = {
        "trigger": "required",
        "route_status": "ready",
    }

    findings = _validate(tmp_path, seal)

    assert any(
        finding.startswith("missing_required_route_accounting:")
        and "native_youtube" in finding
        for finding in findings
    )


@pytest.mark.parametrize(
    "route_id",
    ["google_ads_transparency", "reddit_weekly_lake"],
)
def test_passing_mandatory_route_cannot_self_label_optional_and_unrun(
    tmp_path: Path, route_id: str
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row for row in seal["route_job_accounting"] if row["route_id"] == route_id
    )
    route["required"] = False
    route["material"] = False
    route["unrun_job_ids"] = list(route["planned_job_ids"])
    route["unrun_count"] = route["planned_count"]
    route["completed_job_ids"] = []
    route["completed_count"] = 0
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert f"mandatory_route_not_required:{route_id}" in findings
    assert f"passing_mandatory_route_has_unrun_jobs:{route_id}" in findings


def test_triggered_native_route_cannot_be_optional_and_unrun(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_capability_preflight"]["native_social"]["youtube"] = {
        "trigger": "required",
        "route_status": "ready",
    }
    artifact = _artifact(tmp_path, "native_youtube.md")
    seal["route_job_accounting"].append(
        {
            "route_id": "native_youtube",
            "phase": "co3",
            "required": False,
            "material": False,
            "planned_job_ids": ["YT-001"],
            "planned_count": 1,
            "completed_job_ids": [],
            "completed_count": 0,
            "blocked_job_ids": [],
            "blocked_count": 0,
            "unrun_job_ids": ["YT-001"],
            "unrun_count": 1,
            "terminal_artifact_locator": artifact["locator"],
            "terminal_artifact_sha256": artifact["sha256"],
        }
    )
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "mandatory_route_not_required:native_youtube" in findings
    assert "passing_mandatory_route_has_unrun_jobs:native_youtube" in findings


def test_mandatory_route_actor_ownership_cannot_be_swapped(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    authorization = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "official_retailer_authorization"
    )
    retailer_pdp = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "retailer_full_pdp"
    )
    authorization["phase"] = "co2"
    retailer_pdp["phase"] = "co1"

    findings = _validate(tmp_path, seal)

    assert "route_phase_mismatch:official_retailer_authorization:co1" in findings
    assert "route_phase_mismatch:retailer_full_pdp:co2" in findings


@pytest.mark.parametrize("material", [None, "false"])
def test_non_boolean_material_cannot_forge_non_material_block(
    tmp_path: Path, material: object
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "google_ads_transparency"
    )
    if material is None:
        route.pop("material")
    else:
        route["material"] = material
    route["completed_job_ids"] = []
    route["completed_count"] = 0
    route["blocked_job_ids"] = list(route["planned_job_ids"])
    route["blocked_count"] = route["planned_count"]
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert "invalid_route_material_flag:google_ads_transparency" in _validate(
        tmp_path, seal
    )


def test_consumer_brand_forty_threads_are_a_floor_not_completion(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(ledger["families"]["reddit_forum"]["threads"]) == 40
    ledger.pop("reddit_candidate_frontier")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "passing_seal_without_reddit_frontier_exhaustion" in findings
    assert (
        "passing_seal_below_depth_floor:reddit_forum_threads" not in findings
    )


def test_consumer_brand_frontier_must_account_for_every_ledger_thread(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["reddit_candidate_frontier"]["candidates"] = [
        row
        for row in ledger["reddit_candidate_frontier"]["candidates"]
        if row["thread_id"] != "thread-39"
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "frontier_missing_ledger_thread" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_frontier_cannot_capture_ghost_threads(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["reddit_candidate_frontier"]["candidates"].append(
        {
            "thread_id": "thread-ghost",
            "discovered_by_job_id": "RWL-001",
            "terminal_state": "captured_used",
        }
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "frontier_captured_thread_not_in_ledger" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_frontier_candidates_need_terminal_reasons_and_jobs(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    candidates = ledger["reddit_candidate_frontier"]["candidates"]
    candidates[-1]["reason"] = ""
    candidates[0]["discovered_by_job_id"] = "never-ran"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "missing_frontier_candidate_reason" in findings
    assert "unaccounted_frontier_candidate_job" in findings


def test_consumer_brand_final_batches_cannot_hide_new_usable_threads(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    candidates = ledger["reddit_candidate_frontier"]["candidates"]
    next(
        row for row in candidates if row["thread_id"] == "thread-39"
    )["discovered_by_job_id"] = "RFD-B-001"
    discovery = ledger["reddit_candidate_frontier"]["discovery_jobs"]
    next(row for row in discovery if row["job_id"] == "RWL-001")[
        "candidate_thread_ids"
    ].remove("thread-39")
    next(row for row in discovery if row["job_id"] == "RFD-B-001")[
        "candidate_thread_ids"
    ].append("thread-39")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "saturation_batch_usable_thread_count_mismatch" in findings


def test_consumer_brand_decision_frontier_can_add_usable_nonmaterial_thread(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    candidates = ledger["reddit_candidate_frontier"]["candidates"]
    next(row for row in candidates if row["thread_id"] == "thread-39")[
        "discovered_by_job_id"
    ] = "RFD-B-001"
    discovery = ledger["reddit_candidate_frontier"]["discovery_jobs"]
    next(row for row in discovery if row["job_id"] == "RWL-001")[
        "candidate_thread_ids"
    ].remove("thread-39")
    next(row for row in discovery if row["job_id"] == "RFD-B-001")[
        "candidate_thread_ids"
    ].append("thread-39")
    next(
        row
        for row in ledger["closure"]["batches"]
        if row["query_family_id"] == "family-balanced"
    )["new_usable_reddit_threads"] = 39
    ledger["closure"]["batches"][-1]["new_usable_reddit_threads"] = 1
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_decision_frontier_requires_two_dry_families(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["decision_frontier_family_ids"] = [
        "family-final-b"
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "invalid_product_axis_decision_frontier:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_decision_frontier_requires_different_family_kinds(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    families = ledger["reddit_candidate_frontier"]["query_families"]
    next(row for row in families if row["family_id"] == "family-final-b")[
        "family_kind"
    ] = "late_pain_stress_test"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "repeated_decision_frontier_family_kind:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_v4_requires_proven_high_yield_family_set(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    family = next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "family-brandless"
    )
    family["family_kind"] = "generic_product_search"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "missing_mandatory_high_yield_query_family" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_requires_high_yield_families_before_phase2(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    search_path = tmp_path / "consumer_phase2_search.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    for job in search["jobs"]:
        job["executed_at"] = "2026-08-02T00:04:00+00:00"
    search_path.write_text(json.dumps(search, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "phase2-search"
    )["sha256"] = _artifact_hash(search_path)
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "mandatory_high_yield_query_family_not_pre_phase2" in findings


def test_consumer_brand_accepts_exact_historical_order_migration_exception(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    search_path = tmp_path / "consumer_phase2_search.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    for job in search["jobs"]:
        job["executed_at"] = "2026-08-02T00:04:00+00:00"
    search_path.write_text(json.dumps(search, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "phase2-search"
    )["sha256"] = _artifact_hash(search_path)
    ledger["reddit_candidate_frontier"]["execution_order_exception"] = {
        "exception_type": "pre_contract_historical_run",
        "cycle_id": ledger["cycle_id"],
        "phase2_started_at": "2026-08-02T00:04:00+00:00",
        "mandatory_families_completed_at": "2026-08-02T00:08:00+00:00",
        "future_runs_covered": False,
        "reason": (
            "This dogfood run began before the mandatory-family ordering "
            "contract was adopted; the observed order remains explicit."
        ),
    }
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_rejects_inexact_order_migration_exception(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    search_path = tmp_path / "consumer_phase2_search.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    for job in search["jobs"]:
        job["executed_at"] = "2026-08-02T00:04:00+00:00"
    search_path.write_text(json.dumps(search, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "phase2-search"
    )["sha256"] = _artifact_hash(search_path)
    ledger["reddit_candidate_frontier"]["execution_order_exception"] = {
        "exception_type": "pre_contract_historical_run",
        "cycle_id": "another-cycle",
        "phase2_started_at": "2026-08-02T00:04:00+00:00",
        "mandatory_families_completed_at": "2026-08-02T00:08:00+00:00",
        "future_runs_covered": False,
        "reason": "Wrong cycle must not waive actual ordering.",
    }
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "invalid_reddit_execution_order_exception" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_rejects_order_exception_after_contract_adoption(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    search_path = tmp_path / "consumer_phase2_search.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    for job in search["jobs"]:
        job["executed_at"] = "2026-08-05T00:04:00+00:00"
    search_path.write_text(json.dumps(search, indent=2) + "\n", encoding="utf-8")
    next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "phase2-search"
    )["sha256"] = _artifact_hash(search_path)
    for row in ledger["reddit_candidate_frontier"]["discovery_jobs"]:
        row["executed_at"] = row["executed_at"].replace(
            "2026-08-02T", "2026-08-05T"
        )
    ledger["reddit_candidate_frontier"]["execution_order_exception"] = {
        "exception_type": "pre_contract_historical_run",
        "cycle_id": ledger["cycle_id"],
        "phase2_started_at": "2026-08-05T00:04:00+00:00",
        "mandatory_families_completed_at": "2026-08-05T00:08:00+00:00",
        "future_runs_covered": False,
        "reason": "A run executed after adoption must not reuse the waiver.",
    }
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "invalid_reddit_execution_order_exception" in findings
    assert "mandatory_high_yield_query_family_not_pre_phase2" in findings


def test_consumer_brand_requires_high_yield_family_execution_order(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    job = next(
        row
        for row in ledger["reddit_candidate_frontier"]["discovery_jobs"]
        if row["job_id"] == "RFD-M2-001"
    )
    job["executed_at"] = "2026-08-02T00:04:00+00:00"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "mandatory_high_yield_query_family_out_of_order" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_decision_frontier_is_chronological(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["decision_frontier_family_ids"] = [
        "family-final-b",
        "family-final-a",
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert (
        "out_of_order_product_axis_decision_frontier:packaging_reliability"
        in _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_material_addition_reopens_affected_axis(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    batch = next(
        row
        for row in ledger["closure"]["batches"]
        if row["query_family_id"] == "family-final-b"
    )
    batch["material_incremental_value"] = True
    batch["material_additions"] = [
        {
            "addition_id": "late-packaging-mechanism",
            "kind": "mechanism",
            "axis_ids": ["packaging_reliability"],
            "evidence_refs": ["reddit_forum:thread-0"],
            "decision_effect": "Introduced a new failure mechanism.",
        }
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "decision_frontier_family_not_materially_dry:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_axis_can_close_after_earlier_material_addition(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    batch = next(
        row
        for row in ledger["closure"]["batches"]
        if row["query_family_id"] == "family-condition"
    )
    batch["material_incremental_value"] = True
    batch["material_additions"] = [
        {
            "addition_id": "condition-segment",
            "kind": "segment_or_condition",
            "axis_ids": ["packaging_reliability"],
            "evidence_refs": ["reddit_forum:thread-0"],
            "decision_effect": "Sharpened the failure to a named use condition.",
        }
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v4_accepts_source_limited_decision_mature_axis(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    axis = ledger["product_axes"][0]
    axis["support_refs"] = axis["support_refs"][:1]
    axis["strength"] = "signal"
    axis["closure_basis"] = "route_bounded_source_exhaustion"
    axis["claim_ceiling"] = "bounded_observation_only"
    axis["source_exhaustion"] = {
        "status": "source_exhausted",
        "expected_minimum": 3,
        "observed_usable_units": 1,
        "reason": "All planned high-yield and frontier families were terminal.",
    }
    axis["decision_usefulness"]["status"] = "source_exhausted_but_weak"
    axis["decision_usefulness"]["decision_bearing_support_refs"] = [
        {
            "family": "reddit_forum",
            "unit_id": "thread-0",
            "role": "customer_tension",
        }
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, _make_passing(seal)) == []


def test_consumer_brand_v4_rejects_source_limited_strong_claim_ceiling(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    axis = ledger["product_axes"][0]
    axis["support_refs"] = axis["support_refs"][:1]
    axis["strength"] = "signal"
    axis["closure_basis"] = "route_bounded_source_exhaustion"
    axis["claim_ceiling"] = "strong_qualitative"
    axis["source_exhaustion"] = {
        "status": "source_exhausted",
        "expected_minimum": 3,
        "observed_usable_units": 1,
        "reason": "All planned high-yield and frontier families were terminal.",
    }
    axis["decision_usefulness"]["status"] = "source_exhausted_but_weak"
    axis["decision_usefulness"]["decision_bearing_support_refs"] = [
        {
            "family": "reddit_forum",
            "unit_id": "thread-0",
            "role": "customer_tension",
        }
    ]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "source_limited_axis_overclaims:packaging_reliability" in _validate(
        tmp_path, _make_passing(seal)
    )


def test_consumer_brand_decision_mature_axis_requires_decision_usefulness(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0].pop("decision_usefulness")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "missing_product_axis_decision_usefulness:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_decision_usefulness_requires_competitive_decision(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["decision_usefulness"]["competitive_decision"] = ""
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "missing_product_axis_competitive_decision:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_decision_usefulness_refs_must_resolve_to_axis_support(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    refs = ledger["product_axes"][0]["decision_usefulness"][
        "decision_bearing_support_refs"
    ]
    refs[0]["unit_id"] = "not-axis-support"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "unresolved_product_axis_decision_support_ref:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_evidence_supported_axis_must_be_decision_useful(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["decision_usefulness"]["status"] = (
        "evidence_covered_but_not_decision_useful"
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "evidence_supported_axis_not_decision_useful:packaging_reliability" in (
        _validate(tmp_path, _make_passing(seal))
    )


def test_consumer_brand_v4_previous_contract_requires_explicit_audit_flag(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["schema_version"] = PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION
    ledger["profile_id"] = PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    _rewrite_depth_reference(seal, ledger_path, ledger)
    seal = _make_passing(seal)
    seal_path = _write_seal(tmp_path, seal)

    assert "legacy_consumer_v2_requires_explicit_historical_audit" in (
        validate_phase_acquisition_seal(seal_path=seal_path, repo_root=tmp_path)
    )
    assert validate_phase_acquisition_seal(
        seal_path=seal_path,
        repo_root=tmp_path,
        allow_legacy_consumer_v2=True,
    ) == []


def test_consumer_brand_v2_audit_still_enforces_final_sweep_batch_contract(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["schema_version"] = PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION
    ledger["profile_id"] = PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    final_batch = ledger["closure"]["batches"][-1]
    final_batch["new_customer_segments"] = 2
    final_batch["batch_kind"] = "lake_reuse"
    _rewrite_depth_reference(seal, ledger_path, ledger)
    seal_path = _write_seal(tmp_path, _make_passing(seal))

    findings = validate_phase_acquisition_seal(
        seal_path=seal_path,
        repo_root=tmp_path,
        allow_legacy_consumer_v2=True,
    )

    assert "saturation_batch_nonzero_new_customer_segments" in findings
    assert "saturation_batch_not_live_acquisition" in findings


def test_consumer_brand_frontier_family_unknown_job_reports_finding(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    family = next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "family-final-b"
    )
    family["job_ids"] = ["RFD-B-001", "RFD-GHOST"]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "invalid_reddit_query_family_jobs" in findings


def test_consumer_brand_blocked_seal_reports_open_axis_without_findings(
    tmp_path: Path,
) -> None:
    seal = _make_passing(_blocked_seal(tmp_path))
    seal.update(
        {
            "acquisition_gate": "blocked",
            "seal_state": "BLOCKED_ACQUISITION_INCOMPLETE",
            "deliver_allowed": False,
        }
    )
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    axis = ledger["product_axes"][0]
    axis["decision_maturity"] = "open"
    for field in (
        "closure_basis",
        "claim_ceiling",
        "decision_frontier_family_ids",
        "decision_usefulness",
    ):
        axis.pop(field, None)
    ledger["closure"]["decision_frontier"] = {
        "status": "open",
        "decision_mature_axis_ids": [],
        "open_axis_ids": ["packaging_reliability"],
    }
    ledger["closure"]["conclusion"] = "incomplete"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert _validate(tmp_path, seal) == []


def test_consumer_brand_open_axis_rejects_stale_closure_fields(
    tmp_path: Path,
) -> None:
    seal = _make_passing(_blocked_seal(tmp_path))
    seal.update(
        {
            "acquisition_gate": "blocked",
            "seal_state": "BLOCKED_ACQUISITION_INCOMPLETE",
            "deliver_allowed": False,
        }
    )
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    axis = ledger["product_axes"][0]
    axis["decision_maturity"] = "open"
    ledger["closure"]["decision_frontier"] = {
        "status": "open",
        "decision_mature_axis_ids": [],
        "open_axis_ids": ["packaging_reliability"],
    }
    ledger["closure"]["conclusion"] = "incomplete"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, seal)

    assert "open_product_axis_has_closure_claim:packaging_reliability" in findings
    assert (
        "open_product_axis_has_decision_frontier:packaging_reliability" in findings
    )


def test_consumer_brand_passing_seal_still_rejects_open_axis(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    axis = ledger["product_axes"][0]
    axis["decision_maturity"] = "open"
    for field in (
        "closure_basis",
        "claim_ceiling",
        "decision_frontier_family_ids",
    ):
        axis.pop(field, None)
    ledger["closure"]["decision_frontier"] = {
        "status": "open",
        "decision_mature_axis_ids": [],
        "open_axis_ids": ["packaging_reliability"],
    }
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "open_product_axis_decision_frontier:packaging_reliability" in findings
    assert "phase_a_decision_frontier_not_mature" in findings
    assert "phase_a_decision_frontier_has_open_axes" in findings


def _multi_axis_frontier_fixture(
    tmp_path: Path,
) -> tuple[dict, dict[str, Path], dict[str, str]]:
    plan = [
        ("m1", "balanced_axis_baseline", "mandatory_high_yield", "01"),
        ("m2", "behavior_consequence_displacement", "mandatory_high_yield", "02"),
        ("m3", "brandless_exact_product", "mandatory_high_yield", "03"),
        ("m4", "condition_post_use", "mandatory_high_yield", "04"),
        ("c1", "late_pain_stress_test", "continuation", "05"),
        ("c2", "late_counterevidence_test", "continuation", "06"),
        ("c3", "late_segment_probe", "continuation", "07"),
        ("c4", "late_alternative_probe", "continuation", "08"),
    ]
    discovery_jobs: list[dict] = []
    query_families: list[dict] = []
    batches: list[dict] = []
    artifacts: dict[str, Path] = {}
    route_jobs: dict[str, str] = {}
    for index, (family_id, kind, role, minute) in enumerate(plan):
        job_id = f"job-{family_id}"
        artifact_id = f"packet-{family_id}"
        artifact_path = tmp_path / f"{artifact_id}.json"
        artifact_path.write_text('{"results": []}\n', encoding="utf-8")
        artifacts[artifact_id] = artifact_path
        route_jobs[job_id] = "completed"
        discovery_jobs.append(
            {
                "job_id": job_id,
                "axis_id": "axis_a" if index % 2 == 0 else "axis_b",
                "query": f"summer fridays {family_id} query",
                "executed_at": f"2026-08-02T00:{minute}:00+00:00",
                "artifact_ids": [artifact_id],
                "candidate_thread_ids": (
                    ["thread-seed"] if family_id == "m1" else []
                ),
            }
        )
        query_families.append(
            {
                "family_id": family_id,
                "family_kind": kind,
                "family_role": role,
                "scope_axis_ids": ["axis_a", "axis_b"],
                "job_ids": [job_id],
                "planned_at": f"2026-08-02T00:{minute}:00+00:00",
                "status": "completed",
            }
        )
        batches.append(
            {
                "batch_id": f"batch-{family_id}",
                "query_family_id": family_id,
                "job_ids": [job_id],
                "batch_kind": "live_acquisition",
                "new_usable_reddit_threads": 0,
                "material_additions": [],
            }
        )
    ledger = {
        "product_axes": [
            {
                "axis_id": "axis_a",
                "disposition": "material",
                "decision_frontier_family_ids": ["c1", "c2"],
            },
            {
                "axis_id": "axis_b",
                "disposition": "material",
                "decision_frontier_family_ids": ["c3", "c4"],
            },
        ],
        "families": {"reddit_forum": {"threads": []}},
        "reddit_candidate_frontier": {
            "status": "source_exhausted",
            "reason": "all planned families terminal",
            "discovery_jobs": discovery_jobs,
            "query_families": query_families,
            "candidates": [
                {
                    "thread_id": "thread-seed",
                    "discovered_by_job_id": "job-m1",
                    "terminal_state": "dominated",
                    "reason": "title-only noise",
                }
            ],
        },
        "closure": {"batches": batches},
    }
    return ledger, artifacts, route_jobs


def _frontier_findings(
    ledger: dict, artifacts: dict[str, Path], route_jobs: dict[str, str]
) -> list[str]:
    findings: list[str] = []
    _validate_reddit_candidate_frontier(
        ledger,
        artifacts=artifacts,
        route_jobs=route_jobs,
        require_complete=True,
        decision_contract=True,
        findings=findings,
    )
    return findings


def _multi_axis_batch(ledger: dict, family_id: str) -> dict:
    return next(
        row
        for row in ledger["closure"]["batches"]
        if row["query_family_id"] == family_id
    )


def test_multi_axis_two_axis_frontier_closes_cleanly(tmp_path: Path) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)

    assert _frontier_findings(ledger, artifacts, route_jobs) == []


def test_multi_axis_early_addition_on_other_axis_does_not_dirty_frontier(
    tmp_path: Path,
) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)
    _multi_axis_batch(ledger, "c1")["material_additions"] = [
        {"addition_id": "b-early", "axis_ids": ["axis_b"]}
    ]

    assert _frontier_findings(ledger, artifacts, route_jobs) == []


def test_multi_axis_late_addition_reopens_only_affected_axis(
    tmp_path: Path,
) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)
    _multi_axis_batch(ledger, "c3")["material_additions"] = [
        {"addition_id": "a-late", "axis_ids": ["axis_a"]}
    ]

    findings = _frontier_findings(ledger, artifacts, route_jobs)

    assert "decision_frontier_precedes_material_addition:axis_a" in findings
    assert not [finding for finding in findings if finding.endswith(":axis_b")]


def test_multi_axis_reset_uses_execution_time_not_planned_time(
    tmp_path: Path,
) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)
    family = next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "c3"
    )
    family["planned_at"] = "2026-08-02T00:04:30+00:00"
    _multi_axis_batch(ledger, "c3")["material_additions"] = [
        {"addition_id": "a-executed-late", "axis_ids": ["axis_a"]}
    ]

    findings = _frontier_findings(ledger, artifacts, route_jobs)

    assert "decision_frontier_precedes_material_addition:axis_a" in findings
    assert not [finding for finding in findings if finding.endswith(":axis_b")]


def test_multi_axis_addition_inside_own_frontier_family_is_not_dry(
    tmp_path: Path,
) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)
    _multi_axis_batch(ledger, "c2")["material_additions"] = [
        {"addition_id": "a-inside", "axis_ids": ["axis_a"]}
    ]

    findings = _frontier_findings(ledger, artifacts, route_jobs)

    assert "decision_frontier_family_not_materially_dry:axis_a" in findings
    assert not [finding for finding in findings if finding.endswith(":axis_b")]


def test_multi_axis_frontier_family_must_scope_the_closing_axis(
    tmp_path: Path,
) -> None:
    ledger, artifacts, route_jobs = _multi_axis_frontier_fixture(tmp_path)
    family = next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "c3"
    )
    family["scope_axis_ids"] = ["axis_a"]

    findings = _frontier_findings(ledger, artifacts, route_jobs)

    assert "decision_frontier_family_missing_axis_scope:axis_b" in findings
    assert not [finding for finding in findings if finding.endswith(":axis_a")]


def test_consumer_brand_final_batches_require_usable_thread_accounting(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1].pop("new_usable_reddit_threads")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "invalid_saturation_batch_new_usable_reddit_threads" in findings


def test_consumer_brand_batch_jobs_cannot_repeat_across_batches(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1]["job_ids"] = ["RFD-A-001"]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "duplicate_saturation_batch_job" in findings


def test_consumer_brand_serp_packet_cannot_be_credited_as_native_body(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["target_reconciliation"][0]["native_artifact_id"] = "serp-packet"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "serp_artifact_credited_as_native_body:target-1" in findings


def test_consumer_brand_threads_cannot_share_one_native_artifact(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["families"]["reddit_forum"]["threads"][1]["artifact_id"] = (
        "thread-native-0"
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "shared_reddit_thread_native_artifact" in findings


def test_consumer_brand_threads_cannot_alias_one_native_artifact_path(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    original = next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "thread-native-0"
    )
    ledger["artifacts"].append(
        {
            "artifact_id": "thread-native-alias",
            **{key: original[key] for key in ("locator", "sha256")},
        }
    )
    ledger["families"]["reddit_forum"]["threads"][1]["artifact_id"] = (
        "thread-native-alias"
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "shared_reddit_thread_native_artifact" in findings


def test_consumer_brand_final_batches_must_be_frontier_discovery(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][0]["job_ids"] = ["P2-004"]
    ledger["closure"]["batches"][1]["job_ids"] = ["P2-005"]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "saturation_batch_query_family_job_mismatch" in findings


def test_consumer_brand_each_decision_frontier_family_scopes_its_axis(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "family-final-a"
    )["scope_axis_ids"] = []
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "invalid_reddit_query_family_axis_scope" in findings
    assert (
        "decision_frontier_family_missing_axis_scope:packaging_reliability"
        in findings
    )


def test_consumer_brand_final_sweeps_require_varied_queries(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    discovery = ledger["reddit_candidate_frontier"]["discovery_jobs"]
    query = next(row for row in discovery if row["job_id"] == "RFD-A-001")[
        "query"
    ]
    next(row for row in discovery if row["job_id"] == "RFD-B-001")[
        "query"
    ] = query.upper()
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "repeated_decision_frontier_query:packaging_reliability" in findings


def test_consumer_brand_final_sweeps_require_distinct_capture_paths(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    original = next(
        row
        for row in ledger["artifacts"]
        if row["artifact_id"] == "reddit-frontier-final-a"
    )
    ledger["artifacts"].append(
        {
            "artifact_id": "reddit-frontier-final-alias",
            **{key: original[key] for key in ("locator", "sha256")},
        }
    )
    discovery = ledger["reddit_candidate_frontier"]["discovery_jobs"]
    next(row for row in discovery if row["job_id"] == "RFD-B-001")[
        "artifact_ids"
    ] = ["reddit-frontier-final-alias"]
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert (
        "shared_decision_frontier_discovery_artifact:packaging_reliability"
        in findings
    )


def test_consumer_brand_discovery_candidate_list_reconciles_to_frontier(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    discovery = ledger["reddit_candidate_frontier"]["discovery_jobs"]
    next(row for row in discovery if row["job_id"] == "RWL-001")[
        "candidate_thread_ids"
    ].remove("thread-39")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "frontier_discovery_candidate_mismatch" in findings


def test_consumer_brand_support_ref_fields_must_match_comment_coding(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["product_axes"][0]["support_refs"][0].update(
        {
            "contribution": "compares",
            "choice": "alternative",
            "alternative_brand": "Laneige",
        }
    )
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert (
        "product_axis_support_not_backed_by_comment_coding:packaging_reliability"
        in findings
    )


def test_consumer_brand_used_target_requires_completed_discovery_job(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["evidence_depth_ledger"] = _consumer_depth_ledger(tmp_path)
    seal = _make_passing(seal)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"].remove("P2-001")
    phase2["completed_count"] -= 1
    phase2["blocked_job_ids"].append("P2-001")
    phase2["blocked_count"] += 1

    findings = _validate(tmp_path, seal)

    assert "nonterminal_consumer_target_job:target-1" in findings


def test_repo_internal_absolute_locators_are_nonportable(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    reference = _consumer_depth_ledger(tmp_path)
    ledger_path = tmp_path / reference["locator"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["artifacts"][0]["locator"] = str(tmp_path / "depth_source.md")
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "nonportable_evidence_depth_source_locator" in findings


@pytest.mark.parametrize("count", [True, 1.0])
def test_route_job_counts_require_exact_integers(
    tmp_path: Path, count: object
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "google_ads_transparency"
    )
    route["planned_count"] = count
    route["completed_count"] = count

    findings = _validate(tmp_path, seal)

    assert findings.count("invalid_planned_count_type") == 1
    assert findings.count("invalid_completed_count_type") == 1


# ---------------------------------------------------------------------------
# Understanding route version, campaign integration, comparator closure,
# conditional verification, and retailer state accounting (route 1.1.0).
# ---------------------------------------------------------------------------


def _rewrite_campaign_view(tmp_path: Path, seal: dict, mutate) -> None:
    view_ref = seal["understanding_route"]["campaign_evidence_integration"][
        "view"
    ]
    path = tmp_path / view_ref["locator"]
    view = json.loads(path.read_text(encoding="utf-8"))
    mutate(view)
    path.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
    view_ref["sha256"] = _artifact_hash(path)
    for row in seal["route_job_accounting"]:
        if row.get("route_id") == "campaign_evidence_integration":
            row["terminal_artifact_sha256"] = view_ref["sha256"]


def test_seal_without_route_version_blocks_by_default(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    del seal["understanding_route"]

    assert "missing_understanding_route_version" in _validate(tmp_path, seal)


def test_preversion_route_audit_switch_permits_historical_seals(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    del seal["understanding_route"]

    findings = validate_phase_acquisition_seal(
        seal_path=_write_seal(tmp_path, seal),
        repo_root=tmp_path,
        allow_preversion_route=True,
    )

    assert "missing_understanding_route_version" not in findings


def test_unknown_route_version_is_invalid(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["understanding_route"]["route_version"] = "9.9.9"

    assert "invalid_understanding_route_version" in _validate(tmp_path, seal)


def test_older_recorded_route_carries_no_current_obligations(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["understanding_route"] = {"route_version": "1.0.0"}

    assert _validate(tmp_path, seal) == []


def test_current_route_requires_campaign_integration_accounting(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_job_accounting"] = [
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] != "campaign_evidence_integration"
    ]

    assert "missing_campaign_integration_route_accounting" in _validate(
        tmp_path, seal
    )


def test_campaign_integration_route_phase_is_bound(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    row = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "campaign_evidence_integration"
    )
    row["phase"] = "co1"

    assert "campaign_integration_phase_mismatch" in _validate(tmp_path, seal)


def test_comparator_candidate_cannot_silently_disappear(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    closure = seal["understanding_route"]["comparator_closure"]
    closure["candidates"] = [
        row
        for row in closure["candidates"]
        if row["candidate_id"] != "cand-rhode"
    ]

    assert "comparator_candidate_silently_dropped:cand-rhode" in _validate(
        tmp_path, seal
    )


def test_promoted_candidate_requires_exact_product_identities(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    closure = seal["understanding_route"]["comparator_closure"]
    promoted = next(
        row
        for row in closure["candidates"]
        if row["candidate_id"] == "cand-elf"
    )
    del promoted["competitor_product_identity"]

    assert "comparator_promoted_without_exact_identity:cand-elf" in _validate(
        tmp_path, seal
    )


def test_material_candidate_requires_every_lane_evidence_state(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    closure = seal["understanding_route"]["comparator_closure"]
    watch = next(
        row
        for row in closure["candidates"]
        if row["candidate_id"] == "cand-rhode"
    )
    del watch["lane_evidence"]["co2_retailer_product"]

    assert (
        "invalid_comparator_lane_evidence:cand-rhode:co2_retailer_product"
        in _validate(tmp_path, seal)
    )


def test_material_candidate_requires_portfolio_role(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    del promoted["portfolio_role"]

    assert "missing_comparator_portfolio_role:cand-elf" in _validate(tmp_path, seal)


def test_explicit_hero_requires_explicit_source_evidence(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    promoted["portfolio_role"].update(
        {"status": "explicit_hero", "basis": "observed_position", "evidence_refs": []}
    )

    assert (
        "comparator_explicit_hero_without_explicit_evidence:cand-elf"
        in _validate(tmp_path, seal)
    )


def test_likely_major_requires_multiple_evidence_refs(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    promoted["portfolio_role"]["evidence_refs"] = ["one-source"]

    assert (
        "comparator_likely_major_without_multisource_evidence:cand-elf"
        in _validate(tmp_path, seal)
    )


def test_unclear_portfolio_role_requires_gap_reason(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    watch = seal["understanding_route"]["comparator_closure"]["candidates"][1]
    del watch["portfolio_role"]["gap_reason"]

    assert "comparator_unclear_role_without_gap_reason:cand-rhode" in _validate(
        tmp_path, seal
    )


def test_source_local_rank_requires_complete_context(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    del promoted["observed_positions"][0]["market_scope"]

    assert "missing_comparator_position_context:cand-elf:market_scope" in _validate(
        tmp_path, seal
    )


def test_source_local_rank_cannot_exceed_list_size(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    promoted["observed_positions"][0]["rank"] = 25

    assert "invalid_comparator_source_local_rank:cand-elf" in _validate(
        tmp_path, seal
    )


def test_universal_comparator_rank_is_forbidden(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    promoted["sales_rank"] = 1

    assert "forbidden_synthetic_comparator_field:cand-elf:sales_rank" in _validate(
        tmp_path, seal
    )


def test_observed_lane_requires_evidence_refs(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    del promoted["lane_evidence"]["co3_reddit_community"]["evidence_refs"]

    assert (
        "observed_comparator_lane_without_evidence:cand-elf:co3_reddit_community"
        in _validate(tmp_path, seal)
    )


def test_empty_lane_requires_gap_reason(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    watch = seal["understanding_route"]["comparator_closure"]["candidates"][1]
    del watch["lane_evidence"]["co3_retailer_review"]["gap_reason"]

    assert (
        "comparator_lane_gap_without_reason:cand-rhode:co3_retailer_review"
        in _validate(tmp_path, seal)
    )


def test_promoted_comparator_requires_shared_axes(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    promoted = seal["understanding_route"]["comparator_closure"]["candidates"][0]
    promoted["shared_axis_ids"] = []

    assert "promoted_comparator_without_shared_axes:cand-elf" in _validate(
        tmp_path, seal
    )


def test_passing_seal_requires_closed_comparator_context(
    tmp_path: Path,
) -> None:
    seal = _make_passing(_blocked_seal(tmp_path))
    seal["understanding_route"]["comparator_closure"]["state"] = (
        "blocked_open_comparator_candidates"
    )

    assert "passing_seal_without_comparator_context_closure" in _validate(
        tmp_path, seal
    )


def test_nonindependent_unit_cannot_earn_origin_credit(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        unit = next(
            row
            for row in view["units"]
            if row["unit_id"] == "cv-partner-ad-1"
        )
        unit["independent_origin_credit"] = True

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert (
        "campaign_credit_without_independent_relationship:cv-partner-ad-1"
        in _validate(tmp_path, seal)
    )


def test_one_origin_key_receives_one_independence_credit(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        base = next(
            row
            for row in view["units"]
            if row["unit_id"] == "cv-creator-1"
        )
        echo = dict(base)
        echo["unit_id"] = "cv-creator-1-echo"
        view["units"].append(echo)

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert (
        "duplicate_independent_origin_credit:creator:creator-a"
        in _validate(tmp_path, seal)
    )


def test_merged_creator_and_audience_role_is_invalid(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        unit = next(
            row
            for row in view["units"]
            if row["unit_id"] == "cv-creator-1"
        )
        unit["source_role"] = "creator_and_audience"

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert "invalid_campaign_unit_source_role:cv-creator-1" in _validate(
        tmp_path, seal
    )


def test_relationship_unknown_cannot_be_relabelled_organic(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        unit = next(
            row
            for row in view["units"]
            if row["unit_id"] == "cv-creator-2"
        )
        unit["relationship_posture"] = "organic"

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert (
        "invalid_campaign_unit_relationship_posture:cv-creator-2"
        in _validate(tmp_path, seal)
    )


def test_direct_cluster_cannot_carry_nondirect_members(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        cluster = next(
            row
            for row in view["clusters"]
            if row["cluster_id"] == "cl-direct-1"
        )
        cluster["member_unit_ids"].append("cv-creator-1")

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert "campaign_cluster_overstated_linkage:cl-direct-1" in _validate(
        tmp_path, seal
    )


def test_inferred_cluster_requires_provenance_and_reversal(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)

    def mutate(view: dict) -> None:
        cluster = next(
            row
            for row in view["clusters"]
            if row["cluster_id"] == "cl-inferred-1"
        )
        del cluster["provenance"]

    _rewrite_campaign_view(tmp_path, seal, mutate)

    assert (
        "campaign_cluster_inference_without_provenance:cl-inferred-1"
        in _validate(tmp_path, seal)
    )


def test_verification_request_requires_material_trigger(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    request = seal["understanding_route"]["verification_requests"][0]
    request["trigger_evidence_refs"] = []

    assert (
        "verification_request_without_material_trigger:VER-001"
        in _validate(tmp_path, seal)
    )


def test_passing_seal_cannot_carry_unrun_verification_request(
    tmp_path: Path,
) -> None:
    seal = _make_passing(_blocked_seal(tmp_path))
    request = seal["understanding_route"]["verification_requests"][0]
    request["status"] = "not_run"

    assert (
        "passing_seal_with_unrun_verification_request:VER-001"
        in _validate(tmp_path, seal)
    )


def test_retailer_state_change_requires_two_observations(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    claims = seal["understanding_route"]["retailer_state_accounting"]["claims"]
    change = next(row for row in claims if row["claim_id"] == "RSA-002")
    del change["prior_observation_ref"]

    assert (
        "retailer_state_change_without_two_observations:RSA-002"
        in _validate(tmp_path, seal)
    )


def test_single_snapshot_cannot_emit_movement(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    claims = seal["understanding_route"]["retailer_state_accounting"]["claims"]
    snapshot = next(row for row in claims if row["claim_id"] == "RSA-001")
    snapshot["change_summary"] = "stock trend inferred from one observation"

    assert "movement_claim_from_single_snapshot:RSA-001" in _validate(
        tmp_path, seal
    )
