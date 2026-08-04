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
                "executed_at": "2026-08-02T00:04:00+00:00",
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
    family = next(
        row
        for row in ledger["reddit_candidate_frontier"]["query_families"]
        if row["family_id"] == "family-balanced"
    )
    family["family_role"] = "phase2"
    _rewrite_depth_reference(seal, ledger_path, ledger)

    findings = _validate(tmp_path, _make_passing(seal))

    assert "mandatory_high_yield_query_family_not_pre_phase2" in findings


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
    _rewrite_depth_reference(seal, ledger_path, ledger)

    assert "source_limited_axis_overclaims:packaging_reliability" in _validate(
        tmp_path, _make_passing(seal)
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
