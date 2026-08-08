from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from judgment.phase_a_semantic_run import (
    RUN_SPEC_VERSION,
    audit_phase_a_source,
    build_phase_a_reddit_source_v3,
    build_phase_a_retailer_source_v3,
    build_serp_source_surface_spec,
    build_retailer_source_manifest,
    census_phase_a_customer_corpus,
    materialize_phase_a_v3,
    materialize_serp_source_frontier_review,
    prepare_serp_source_frontier_inventory,
    reconcile_serp_frontier_targets,
    run_status,
    validate_one_batch_response,
    validate_one_reconciliation_response,
)
from judgment.semantic_evidence_integration import (
    SemanticIntegrationError,
    build_bundle,
    prepare_reconciliation_stage,
    validate_batch_responses,
)


def _sha(path: Path) -> str:
    body = path.read_bytes()
    if path.suffix.lower() in {".json", ".md", ".yaml", ".yml"}:
        body = body.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(body).hexdigest()


def _raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> str:
    body = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _source_fragment(tmp_path: Path) -> tuple[Path, dict]:
    raw = tmp_path / "raw-thread.json"
    raw.write_text("source body\n", encoding="utf-8")
    source = {
        "schema_version": "semantic_evidence_source_v3",
        "cycle_id": "cycle-1",
        "question_id": "question-1",
        "question": "What do captured customers report?",
        "corpus_profile": "phase_a_final_acquisition",
        "corpus_scope": "complete controlled fixture",
        "corpus_cutoff": "2026-08-08T00:00:00Z",
        "axes": [{"axis_id": "wear", "label": "Wear"}],
        "source_artifacts": [
            {
                "artifact_id": "raw-thread",
                "locator": "raw-thread.json",
                "sha256": _raw_sha(raw),
            }
        ],
        "containers": [
            {
                "container_id": "thread-1",
                "container_type": "conversation",
                "source_artifact_id": "raw-thread",
                "captured_leaf_count": 1,
                "source_visible_total": 1,
                "completeness": "complete",
                "captured_at": "2026-08-08T00:00:00Z",
                "capture_boundary": "controlled fixture",
            }
        ],
        "captured_items": [
            {
                "evidence_id": "reddit:t1:c1",
                "container_id": "thread-1",
                "source_family": "reddit_community",
                "source_role": "community_post",
                "source_artifact_id": "raw-thread",
                "source_ref": "https://reddit.test/t1/c1",
                "text": "The balm became drying after a week.",
                "accounting_disposition": "assess",
                "accounting_reason": "readable source-native text",
                "product_candidates": ["sf-lbb"],
                "axis_candidates": ["wear"],
                "product_context": [
                    {
                        "context_type": "thread_title",
                        "source_artifact_id": "raw-thread",
                        "text": "Summer Fridays balm wear",
                        "source_ref": "https://reddit.test/t1",
                    }
                ],
                "independence_posture": "credited",
                "independence_key": "reddit:user-1",
                "engagement": {
                    "raw_score": 7,
                    "material_positive": True,
                    "materiality_basis": "fixture cohort policy",
                },
                "conversation_depth": 0,
                "parent_context": [],
            }
        ],
    }
    path = tmp_path / "fragment.json"
    _write_json(path, source)
    return path, source


def _seal(tmp_path: Path) -> Path:
    terminal_a = tmp_path / "terminal-a.md"
    terminal_b = tmp_path / "terminal-b.md"
    terminal_a.write_text("a\n", encoding="utf-8")
    terminal_b.write_text("b\n", encoding="utf-8")
    seal = tmp_path / "seal.md"
    seal.write_text(
        """# Seal

```yaml
phase_acquisition_seal:
  schema_version: phase_acquisition_seal_v3
  cycle_id: cycle-1
  route_job_accounting:
    - route_id: serp
      planned_job_ids: [s1]
      completed_job_ids: [s1]
      blocked_job_ids: []
      unrun_job_ids: []
      terminal_artifact_locator: terminal-a.md
      terminal_artifact_sha256: TERMINAL_A
    - route_id: community
      planned_job_ids: [c1]
      completed_job_ids: [c1]
      blocked_job_ids: []
      unrun_job_ids: []
      terminal_artifact_locator: terminal-b.md
      terminal_artifact_sha256: TERMINAL_B
```
""".replace("TERMINAL_A", _sha(terminal_a)).replace("TERMINAL_B", _sha(terminal_b)),
        encoding="utf-8",
    )
    return seal


def _spec(tmp_path: Path) -> tuple[dict, dict]:
    fragment_path, source = _source_fragment(tmp_path)
    seal_path = _seal(tmp_path)
    spec = {
        "schema_version": RUN_SPEC_VERSION,
        "run_id": "run-1",
        "cycle_id": "cycle-1",
        "question_id": "question-1",
        "question": "What do captured customers report?",
        "corpus_profile": "phase_a_final_acquisition",
        "corpus_scope": "complete controlled fixture",
        "corpus_cutoff": "2026-08-08T00:00:00Z",
        "external_run_root": str(tmp_path / "run"),
        "max_prompt_bytes": 8_000,
        "axes": [{"axis_id": "wear", "label": "Wear"}],
        "acquisition_seal": {"locator": "seal.md", "sha256": _sha(seal_path)},
        "source_bindings": [
            {
                "binding_id": "community-source",
                "adapter": "semantic_evidence_source_v3",
                "locator": "fragment.json",
                "sha256": _sha(fragment_path),
            }
        ],
        "route_classifications": [
            {
                "route_id": "serp",
                "disposition": "discovery_only",
                "reason": "maps sources but is not claim evidence",
            },
            {
                "route_id": "community",
                "disposition": "semantic_source",
                "reason": "source-native customer language",
                "binding_ids": ["community-source"],
            },
        ],
    }
    return spec, source


def _batch_response(bundle: dict) -> dict:
    batch = bundle["batches"][0]
    return {
        "schema_version": "semantic_evidence_batch_response_v2",
        "bundle_sha256": bundle["bundle_sha256"],
        "batch_id": batch["batch_id"],
        "evidence": [
            {
                "evidence_id": evidence_id,
                "disposition": "claim_bearing",
                "disposition_reason": "direct first-hand experience",
                "semantic_units": [
                    {
                        "semantic_unit_key": "drying-after-week",
                        "statement": "The balm became drying after one week.",
                        "subject_product_ids": ["sf-lbb"],
                        "comparator_product_ids": [],
                        "product_version_ids": [],
                        "axis_ids": ["wear"],
                        "emerging_axis_labels": [],
                        "conditions": ["after one week"],
                        "polarity": "affirmed",
                        "evidence_posture": "first_hand",
                        "uncertainty_posture": "asserted",
                    }
                ],
            }
            for evidence_id in batch["evidence_ids"]
        ],
    }


def _reconciliation_response(stage: dict) -> dict:
    batch = stage["batches"][0]
    return {
        "schema_version": "semantic_evidence_reconciliation_response_v2",
        "stage_sha256": stage["stage_sha256"],
        "batch_id": batch["batch_id"],
        "semantic_nodes": [
            {
                "semantic_node_key": "drying",
                "bounded_meaning": "One captured customer reported drying after one week.",
                "terminal_proposition": True,
                "claim_kind": "customer_experience",
                "subject_product_ids": ["sf-lbb"],
                "comparator_product_ids": [],
                "product_version_ids": [],
                "axis_ids": ["wear"],
                "emerging_axis_labels": [],
                "conditions": ["after one week"],
                "polarity": "affirmed",
                "uncertainty_posture": "asserted",
                "child_relations": [
                    {"child_ref": ref, "relation": "support"}
                    for ref in batch["candidate_refs"]
                ],
                "opposition_checked": True,
                "causal_ceiling": "descriptive_only",
            }
        ],
        "unmerged_children": [],
        "emerging_axis_consolidations": [],
    }


def test_full_corpus_run_audits_every_route_and_materializes_deterministically(
    tmp_path: Path,
) -> None:
    spec, _ = _spec(tmp_path)
    audit = audit_phase_a_source(spec, repo_root=tmp_path)
    first, first_receipt = materialize_phase_a_v3(spec, repo_root=tmp_path)
    second, second_receipt = materialize_phase_a_v3(deepcopy(spec), repo_root=tmp_path)

    assert audit["complete"] is True
    assert audit["sealed_route_count"] == 2
    assert audit["route_disposition_counts"]["semantic_source"] == 1
    assert first == second
    assert first_receipt == second_receipt
    assert first_receipt["captured_item_count"] == 1
    assert first_receipt["historical_seal_restamped"] is False


def test_run_audit_rejects_old_subset_style_missing_route_and_stale_source(
    tmp_path: Path,
) -> None:
    spec, _ = _spec(tmp_path)
    spec["route_classifications"].pop()
    with pytest.raises(SemanticIntegrationError, match="do not match sealed routes"):
        audit_phase_a_source(spec, repo_root=tmp_path)

    spec, _ = _spec(tmp_path)
    (tmp_path / "fragment.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(SemanticIntegrationError, match="hash mismatch"):
        audit_phase_a_source(spec, repo_root=tmp_path)

    spec, _ = _spec(tmp_path)
    (tmp_path / "raw-thread.json").write_text("changed body\n", encoding="utf-8")
    with pytest.raises(SemanticIntegrationError, match="source artifact.*hash mismatch"):
        audit_phase_a_source(spec, repo_root=tmp_path)


def test_blocked_route_cannot_materialize_a_complete_view(tmp_path: Path) -> None:
    spec, _ = _spec(tmp_path)
    spec["route_classifications"][1] = {
        "route_id": "community",
        "disposition": "blocked",
        "reason": "raw body unavailable",
    }
    spec["source_bindings"] = []
    audit = audit_phase_a_source(spec, repo_root=tmp_path)
    assert audit["complete"] is False
    assert audit["blocked_routes"] == ["community"]
    with pytest.raises(SemanticIntegrationError, match="blocked source route"):
        materialize_phase_a_v3(spec, repo_root=tmp_path)


def test_individual_batch_and_reconciliation_responses_validate_before_compile(
    tmp_path: Path,
) -> None:
    spec, _ = _spec(tmp_path)
    source, _ = materialize_phase_a_v3(spec, repo_root=tmp_path)
    bundle = build_bundle(source, max_prompt_bytes=8_000)
    response = _batch_response(bundle)

    receipt = validate_one_batch_response(bundle, response)
    status = run_status(bundle=bundle, batch_responses=[response])
    assert receipt["validated_batch_ids"] == ["batch-0001"]
    assert status["batch_stage_complete"] is True
    assert status["next_status"] == "SEMANTIC_BATCH_COMPILATION_READY"

    compiled = validate_batch_responses(bundle, [response])
    stage, _ = prepare_reconciliation_stage(bundle, compiled)
    reconciliation = _reconciliation_response(stage)
    reconciliation_receipt = validate_one_reconciliation_response(
        bundle, stage, reconciliation
    )
    assert reconciliation_receipt["validated_batch_ids"] == [
        stage["batches"][0]["batch_id"]
    ]


def test_status_reports_interrupted_and_bad_work_without_fake_completion(
    tmp_path: Path,
) -> None:
    spec, _ = _spec(tmp_path)
    source, _ = materialize_phase_a_v3(spec, repo_root=tmp_path)
    bundle = build_bundle(source, max_prompt_bytes=8_000)
    response = _batch_response(bundle)
    bad = deepcopy(response)
    bad["bundle_sha256"] = "0" * 64

    interrupted = run_status(bundle=bundle, batch_responses=[])
    invalid = run_status(bundle=bundle, batch_responses=[bad])
    recovered = run_status(bundle=bundle, batch_responses=[response])

    assert interrupted["missing_batch_ids"] == ["batch-0001"]
    assert interrupted["batch_stage_complete"] is False
    assert interrupted["worker_partitions"] == [
        {
            "worker_partition": 1,
            "expected_batch_count": 1,
            "valid_batch_count": 0,
            "missing_batch_ids": ["batch-0001"],
        }
    ]
    assert invalid["invalid_responses"][0]["error"] == (
        "batch response has stale bundle hash"
    )
    assert recovered["batch_stage_complete"] is True

    stale_bundle = deepcopy(bundle)
    stale_bundle["question"] = "tampered after bundle hashing"
    with pytest.raises(SemanticIntegrationError, match="stored bundle_sha256"):
        run_status(bundle=stale_bundle, batch_responses=[])


def test_duplicate_route_must_name_a_route_that_owns_evidence(tmp_path: Path) -> None:
    spec, _ = _spec(tmp_path)
    spec["source_bindings"] = []
    spec["route_classifications"][1] = {
        "route_id": "community",
        "disposition": "duplicate_of",
        "duplicate_of": "serp",
        "reason": "reuses the discovery route",
    }
    with pytest.raises(SemanticIntegrationError, match="owns no evidence"):
        audit_phase_a_source(spec, repo_root=tmp_path)

    spec, _ = _spec(tmp_path)
    spec["source_bindings"] = []
    spec["route_classifications"][0] = {
        "route_id": "serp",
        "disposition": "blocked",
        "reason": "final fragment not produced",
    }
    spec["route_classifications"][1] = {
        "route_id": "community",
        "disposition": "duplicate_of",
        "duplicate_of": "serp",
        "reason": "reuses evidence the blocked route still owes",
    }
    audit = audit_phase_a_source(spec, repo_root=tmp_path)
    assert audit["complete"] is False
    assert audit["blocked_routes"] == ["serp"]


def _census_inputs(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    packet = tmp_path / "packet"
    raw = packet / "raw"
    raw.mkdir(parents=True)
    content = {
        "thread": {"thread_id": "1gti140", "title": "A Summer Fridays thread"},
        "post": {"body_text": "The root body is evidence too."},
        "comments": [
            {"comment_id": "c1", "body_text": "Summer Fridays changed for me."},
            {"comment_id": "c2", "body_text": ""},
        ],
    }
    content_path = raw / "01_content_record.json"
    _write_json(content_path, content)
    manifest = {
        "preserved_files": [
                {
                    "relative_packet_path": "raw/01_content_record.json",
                    "sha256": _raw_sha(content_path),
            }
        ]
    }
    manifest_path = packet / "manifest.json"
    _write_json(manifest_path, manifest)
    canonical_manifest_sha = hashlib.sha256(
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    retailer_source = tmp_path / "review.json"
    retailer_source.write_text(
        '{"Results":[{"Id":"r1","ReviewText":"Readable"}]}\n',
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.json"
    community_coding = tmp_path / "community.json"
    _write_json(community_coding, {"legacy_parent_threads_not_requalified": []})
    ledger = {
            "cycle_id": "cycle-1",
            "artifacts": [
                {
                    "artifact_id": "reddit-manifest-1gti140",
                    "locator": str(manifest_path),
                    "sha256": canonical_manifest_sha,
                },
                {
                    "artifact_id": "community-coding",
                    "locator": str(community_coding),
                    "sha256": _sha(community_coding),
                },
            ],
            "families": {
                "reddit_forum": {
                    "threads": [
                        {
                            "thread_id": "1gti140",
                            "artifact_id": "reddit-manifest-1gti140",
                        }
                    ]
                }
            },
            "target_reconciliation": [
                    {
                        "target_id": "reddit_1gti140",
                        "source_family": "reddit_forum",
                        "terminal_state": "captured_excluded",
                        "native_artifact_id": "reddit-manifest-1gti140",
                    }
            ],
            "community_axis_coding": {"artifact_id": "community-coding"},
    }
    _write_json(ledger_path, ledger)
    retailer_path = tmp_path / "retailer.json"
    _write_json(
        retailer_path,
        {
            "corpora": [
                {
                    "corpus_id": "retailer",
                    "eligible_text_review_count": 1,
                    "excluded_no_usable_text_count": 2,
                }
            ],
            "rows": [
                {
                    "corpus_id": "retailer",
                    "review_id": "r1",
                    "source_row_ref": f"{retailer_source}#review:r1",
                }
            ],
        },
    )
    manifest_path = tmp_path / "retailer-source-manifest.json"
    _write_json(
        manifest_path,
        build_retailer_source_manifest(retailer_coding_path=retailer_path),
    )
    return ledger_path, retailer_path, manifest_path, ledger


def test_customer_corpus_census_counts_excluded_thread_bodies_and_rating_only_rows(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, _ = _census_inputs(tmp_path)

    census = census_phase_a_customer_corpus(
        evidence_ledger_path=ledger_path,
        retailer_coding_path=retailer_path,
        retailer_source_manifest_path=manifest_path,
    )

    assert census["reddit"]["captured_leaf_count"] == 3
    assert census["reddit"]["readable_leaf_count"] == 2
    assert census["reddit"]["captured_excluded_readable_leaf_count"] == 2
    assert census["retailer_reviews"]["captured_review_count"] == 3
    assert census["selected_subset_used_as_denominator"] is False


def test_retailer_census_rejects_source_bytes_changed_after_manifest(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, _ = _census_inputs(tmp_path)
    retailer = json.loads(retailer_path.read_text(encoding="utf-8"))
    locator = retailer["rows"][0]["source_row_ref"].partition("#review:")[0]
    Path(locator).write_text(
        '{"Results":[{"Id":"different","ReviewText":"Changed"}]}\n',
        encoding="utf-8",
    )

    with pytest.raises(SemanticIntegrationError, match="source hash mismatch"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )


def test_serp_frontier_inventory_enumerates_sources_without_google_prompts(
    tmp_path: Path,
) -> None:
    record_path = tmp_path / "serp.json"
    _write_json(
        record_path,
        {
            "content_record_version": "google_serp_content_v3",
            "rows": [
                {
                    "module_type": "organic",
                    "order_in_module": 1,
                    "title": "Relevant review",
                    "displayed_source": "Example",
                    "canonical_url": "https://example.test/review",
                },
                {
                    "module_type": "people_also_ask",
                    "order_in_module": 1,
                    "title": "A question",
                    "displayed_source": "Google",
                    "canonical_url": None,
                },
                {
                    "module_type": "related_search",
                    "order_in_module": 1,
                    "title": "A suggestion",
                    "displayed_source": "Google",
                    "canonical_url": None,
                },
            ],
        },
    )
    queue_path = tmp_path / "queue-state.json"
    _write_json(
        queue_path,
        {
            "schema_version": "google_serp_queue_state_v1",
            "status": "complete",
            "jobs": [{"job_id": "p1"}],
            "completed_job_ids": ["p1"],
            "failed_job_ids": [],
            "attempt_history": [
                {
                    "job_id": "p1",
                    "outcome": "success",
                    "packet_locator": str(record_path),
                }
            ],
        },
    )
    map_path = tmp_path / "surface-map.json"
    _write_json(
        map_path,
        {
            "schema_version": "phase_a_serp_source_surface_map_v1",
            "search_surfaces": [
                {
                    "phase": "serp_phase1",
                    "job_id": "p1",
                    "artifacts": [
                        {"artifact_id": "serp-1", "locator": str(record_path)}
                    ],
                }
            ],
            "producer_queue_states": [
                {
                    "phase": "serp_phase1",
                    "artifact_id": "queue-1",
                    "locator": str(queue_path),
                }
            ],
        },
    )
    spec = build_serp_source_surface_spec(surface_map_path=map_path)
    spec_path = tmp_path / "surface-spec.json"
    _write_json(spec_path, spec)

    inventory = prepare_serp_source_frontier_inventory(surface_spec_path=spec_path)

    assert inventory["eligible_row_count"] == 1
    assert inventory["row_inventory"][0]["title"] == "Relevant review"
    inventory_path = tmp_path / "inventory.json"
    _write_json(inventory_path, inventory)
    review_path = tmp_path / "review.json"
    _write_json(
        review_path,
        {
            "schema_version": "phase_a_serp_source_review_v1",
            "inventory_sha256": inventory["inventory_sha256"],
            "review_method": "agent_semantic_judgment",
            "model_api_calls": 0,
            "row_decisions": [
                {
                    "artifact_id": "serp-1",
                    "module_type": "organic",
                    "order_in_module": 1,
                    "disposition": "routed",
                    "reason": "The row is a plausible native evidence door.",
                }
            ],
        },
    )
    result = materialize_serp_source_frontier_review(
        inventory_path=inventory_path, review_path=review_path
    )
    assert result["classification_counts"] == {
        "routed": 1,
        "duplicate": 0,
        "excluded": 0,
    }
    assert len(result["locator_recovery_targets"]) == 1
    assert result["frontier"]["producer_job_packet_inventory"] == [
        {
            "phase": "serp_phase1",
            "job_id": "p1",
            "producer_job_id": "p1",
            "producer_queue_state_artifact_id": "queue-1",
            "artifact_ids": ["serp-1"],
            "successful_packet_count": 1,
        }
    ]


def test_serp_surface_spec_rejects_a_successful_packet_omitted_from_the_map(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    for path, title in ((first, "First"), (second, "Second")):
        _write_json(
            path,
            {
                "content_record_version": "google_serp_content_v3",
                "rows": [
                    {
                        "module_type": "organic",
                        "order_in_module": 1,
                        "title": title,
                        "displayed_source": "Example",
                    }
                ],
            },
        )
    queue_path = tmp_path / "queue-state.json"
    _write_json(
        queue_path,
        {
            "schema_version": "google_serp_queue_state_v1",
            "status": "complete",
            "jobs": [{"job_id": "p1"}],
            "completed_job_ids": ["p1"],
            "failed_job_ids": [],
            "attempt_history": [
                {"job_id": "p1", "outcome": "success", "packet_locator": str(first)},
                {"job_id": "p1", "outcome": "success", "packet_locator": str(second)},
            ],
        },
    )
    map_path = tmp_path / "surface-map.json"
    _write_json(
        map_path,
        {
            "schema_version": "phase_a_serp_source_surface_map_v1",
            "search_surfaces": [
                {
                    "phase": "serp_phase1",
                    "job_id": "p1",
                    "artifacts": [{"artifact_id": "serp-1", "locator": str(first)}],
                }
            ],
            "producer_queue_states": [
                {
                    "phase": "serp_phase1",
                    "artifact_id": "queue-1",
                    "locator": str(queue_path),
                }
            ],
        },
    )

    with pytest.raises(SemanticIntegrationError, match="does not exactly match"):
        build_serp_source_surface_spec(surface_map_path=map_path)


def test_serp_surface_spec_rejects_one_packet_under_two_artifact_ids(
    tmp_path: Path,
) -> None:
    """The identity invariant also covers focused-search packet surfaces."""
    packet = tmp_path / "packet.json"
    _write_json(
        packet,
        {
            "content_record_version": "google_serp_content_v3",
            "rows": [
                {
                    "module_type": "organic",
                    "order_in_module": 1,
                    "title": "Shared",
                    "displayed_source": "Example",
                }
            ],
        },
    )
    queue_path = tmp_path / "queue-state.json"
    _write_json(
        queue_path,
        {
            "schema_version": "google_serp_queue_state_v1",
            "status": "complete",
            "jobs": [{"job_id": "p1"}],
            "completed_job_ids": ["p1"],
            "failed_job_ids": [],
            "attempt_history": [
                {"job_id": "p1", "outcome": "success", "packet_locator": str(packet)},
            ],
        },
    )
    map_path = tmp_path / "surface-map.json"
    _write_json(
        map_path,
        {
            "schema_version": "phase_a_serp_source_surface_map_v1",
            "search_surfaces": [
                {
                    "phase": "serp_phase1",
                    "job_id": "p1",
                    "artifacts": [{"artifact_id": "serp-1", "locator": str(packet)}],
                },
                {
                    "phase": "phase_a_adjustment",
                    "job_id": "adjust-1",
                    "artifacts": [{"artifact_id": "serp-2", "locator": str(packet)}],
                },
            ],
            "producer_queue_states": [
                {
                    "phase": "serp_phase1",
                    "artifact_id": "queue-1",
                    "locator": str(queue_path),
                }
            ],
        },
    )

    with pytest.raises(SemanticIntegrationError, match="under two artifact ids"):
        build_serp_source_surface_spec(surface_map_path=map_path)

    producer_inventory = [
        {
            "phase": "serp_phase1",
            "job_id": "p1",
            "producer_job_id": "p1",
            "producer_queue_state_artifact_id": "queue-1",
            "artifact_ids": ["serp-1"],
            "successful_packet_count": 1,
        }
    ]
    forged_spec_path = tmp_path / "forged-spec.json"
    _write_json(
        forged_spec_path,
        {
            "schema_version": "phase_a_serp_source_surface_spec_v1",
            "search_surfaces": [
                {
                    "phase": "serp_phase1",
                    "job_id": "p1",
                    "artifact_ids": ["serp-1"],
                },
                {
                    "phase": "phase_a_adjustment",
                    "job_id": "adjust-1",
                    "artifact_ids": ["serp-2"],
                },
            ],
            "source_artifacts": [
                {
                    "artifact_id": artifact_id,
                    "locator": str(packet),
                    "raw_sha256": _raw_sha(packet),
                }
                for artifact_id in ("serp-1", "serp-2")
            ],
            "producer_queue_states": [
                {
                    "phase": "serp_phase1",
                    "artifact_id": "queue-1",
                    "locator": str(queue_path),
                    "raw_sha256": _raw_sha(queue_path),
                }
            ],
            "producer_job_packet_inventory": producer_inventory,
            "producer_job_packet_inventory_sha256": _canonical(
                producer_inventory
            ),
        },
    )

    with pytest.raises(SemanticIntegrationError, match="under two artifact ids"):
        prepare_serp_source_frontier_inventory(
            surface_spec_path=forged_spec_path
        )


def test_serp_frontier_review_rejects_bulk_default_or_missing_row_decision(
    tmp_path: Path,
) -> None:
    inventory = {
        "schema_version": "phase_a_serp_source_inventory_v1",
        "inventory_sha256": "inventory-hash",
        "row_inventory": [
            {"artifact_id": "serp-1", "module_type": "organic", "order_in_module": 1}
        ],
        "search_surfaces": [],
    }
    inventory_path = tmp_path / "inventory.json"
    _write_json(inventory_path, inventory)
    review_path = tmp_path / "review.json"
    _write_json(
        review_path,
        {
            "schema_version": "phase_a_serp_source_review_v1",
            "inventory_sha256": "inventory-hash",
            "review_method": "agent_semantic_judgment",
            "model_api_calls": 0,
            "default_semantic_decision": {"disposition": "routed", "reason": "bulk"},
            "row_decisions": [],
        },
    )
    with pytest.raises(SemanticIntegrationError, match="cannot use a default"):
        materialize_serp_source_frontier_review(
            inventory_path=inventory_path, review_path=review_path
        )

    _write_json(
        review_path.with_name("missing.json"),
        {
            "schema_version": "phase_a_serp_source_review_v1",
            "inventory_sha256": "inventory-hash",
            "review_method": "agent_semantic_judgment",
            "model_api_calls": 0,
            "row_decisions": [],
        },
    )
    with pytest.raises(SemanticIntegrationError, match="exactly cover"):
        materialize_serp_source_frontier_review(
            inventory_path=inventory_path, review_path=review_path.with_name("missing.json")
        )


def test_retailer_census_rejects_a_manifest_declared_review_absent_from_the_source(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, _ = _census_inputs(tmp_path)
    retailer = json.loads(retailer_path.read_text(encoding="utf-8"))
    retailer["rows"][0]["review_id"] = "ghost"
    retailer["rows"][0]["source_row_ref"] = (
        retailer["rows"][0]["source_row_ref"].partition("#review:")[0] + "#review:ghost"
    )
    _write_json(retailer_path, retailer)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # A hand-authored manifest can name a review the source file never had.
    manifest["retailer_coding_raw_sha256"] = _raw_sha(retailer_path)
    manifest["sources"][0]["referenced_review_ids"] = ["ghost"]
    manifest["source_set_sha256"] = _canonical(manifest["sources"])
    manifest.pop("manifest_sha256")
    manifest["manifest_sha256"] = _canonical(manifest)
    _write_json(manifest_path, manifest)

    with pytest.raises(
        SemanticIntegrationError, match="absent from its source-native review rows"
    ):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )


def test_retailer_census_rejects_collapsed_or_undeclared_corpus_denominators(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, _ = _census_inputs(tmp_path)
    retailer = json.loads(retailer_path.read_text(encoding="utf-8"))
    # The surviving duplicate keeps the eligible-count reconciliation honest
    # while 40 excluded reviews vanish from the captured denominator.
    retailer["corpora"].insert(
        0,
        {
            "corpus_id": "retailer",
            "eligible_text_review_count": 0,
            "excluded_no_usable_text_count": 40,
        },
    )
    _write_json(retailer_path, retailer)
    _write_json(
        manifest_path, build_retailer_source_manifest(retailer_coding_path=retailer_path)
    )
    with pytest.raises(SemanticIntegrationError, match="duplicate corpus id"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )

    ledger_path, retailer_path, manifest_path, _ = _census_inputs(tmp_path / "second")
    retailer = json.loads(retailer_path.read_text(encoding="utf-8"))
    retailer["corpora"][0]["corpus_id"] = "a_different_corpus"
    _write_json(retailer_path, retailer)
    _write_json(
        manifest_path, build_retailer_source_manifest(retailer_coding_path=retailer_path)
    )
    with pytest.raises(SemanticIntegrationError, match="no declared denominator"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )


def test_census_rejects_a_reddit_packet_source_file_without_a_pinned_hash(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, ledger = _census_inputs(tmp_path)
    packet_manifest_path = Path(ledger["artifacts"][0]["locator"])
    packet_manifest = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
    packet_manifest["preserved_files"][0].pop("sha256")
    _write_json(packet_manifest_path, packet_manifest)
    ledger["artifacts"][0]["sha256"] = hashlib.sha256(
        (
            json.dumps(packet_manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode()
    ).hexdigest()
    _write_json(ledger_path, ledger)

    with pytest.raises(SemanticIntegrationError, match="lacks a pinned hash"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )


def test_census_rejects_a_union_that_silently_drops_captured_threads(
    tmp_path: Path,
) -> None:
    ledger_path, retailer_path, manifest_path, ledger = _census_inputs(tmp_path)
    ledger["families"]["reddit_forum"]["threads"].append(
        {"thread_id": "1abcxyz", "artifact_id": "reddit-manifest-1abcxyz"}
    )
    _write_json(ledger_path, ledger)
    with pytest.raises(SemanticIntegrationError, match="missing from the captured-corpus union"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )

    ledger_path, retailer_path, manifest_path, ledger = _census_inputs(tmp_path / "second")
    ledger["target_reconciliation"].append(
        {
            "target_id": "reddit_1abcxyz",
            "source_family": "reddit_forum",
            "terminal_state": "used",
        }
    )
    _write_json(ledger_path, ledger)
    with pytest.raises(SemanticIntegrationError, match="lacks a native packet binding"):
        census_phase_a_customer_corpus(
            evidence_ledger_path=ledger_path,
            retailer_coding_path=retailer_path,
            retailer_source_manifest_path=manifest_path,
        )


def _source_run_spec(tmp_path: Path) -> Path:
    path = tmp_path / "run-spec.json"
    _write_json(
        path,
        {
            "schema_version": RUN_SPEC_VERSION,
            "run_id": "source-builder-fixture",
            "cycle_id": "cycle-1",
            "question_id": "question-1",
            "question": "What do captured customers report?",
            "corpus_profile": "phase_a_final_acquisition",
            "corpus_scope": "complete controlled source-builder fixture",
            "corpus_cutoff": "2026-08-08T00:00:00Z",
            "external_run_root": str(tmp_path / "run"),
            "max_prompt_bytes": 8_000,
            "axes": [{"axis_id": "wear", "label": "Wear"}],
        },
    )
    return path


def test_reddit_source_builder_keeps_titles_as_context_and_excludes_placeholders(
    tmp_path: Path,
) -> None:
    spec_path = _source_run_spec(tmp_path)
    packet = tmp_path / "packet"
    raw = packet / "raw"
    raw.mkdir(parents=True)
    content_path = raw / "content_record.json"
    _write_json(
        content_path,
        {
            "thread": {"thread_id": "abc", "title": "Summer Fridays wear"},
            "post": {
                "body_text": "[deleted]",
                "author_state": "[deleted]",
                "score_state": "5 points",
            },
            "comments": [
                {
                    "row_id": "comment_1",
                    "comment_id": "deleted",
                    "body_text": "[removed]",
                    "depth": 0,
                },
                {
                    "row_id": "comment_2",
                    "comment_id": "c2",
                    "body_text": "It lasts through lunch.",
                    "author_state": "customer",
                    "score_state": "2 points",
                    "depth": 2,
                },
            ],
        },
    )
    manifest_path = packet / "manifest.json"
    _write_json(
        manifest_path,
        {
            "source_locator": {
                "status": "known",
                "value": "https://old.reddit.com/r/test/comments/abc/example/",
            },
            "timing": {
                "capture_time": {
                    "status": "known",
                    "value": "2026-08-01T00:00:00Z",
                }
            },
            "preserved_files": [
                {
                    "relative_packet_path": "raw/content_record.json",
                    "sha256": _raw_sha(content_path),
                }
            ],
        },
    )
    community_path = tmp_path / "community.json"
    _write_json(
        community_path,
        {
            "legacy_parent_threads_not_requalified": [],
            "rows": [
                {
                    "thread_id": "abc",
                    "comment_id": "c2",
                    "product_context": "Lip Butter Balm",
                    "axis_ids": ["wear"],
                }
            ],
        },
    )
    ledger_path = tmp_path / "ledger.json"
    _write_json(
        ledger_path,
        {
            "cycle_id": "cycle-1",
            "artifacts": [
                {
                    "artifact_id": "reddit_manifest_abc",
                    "locator": str(manifest_path),
                    "sha256": _sha(manifest_path),
                },
                {
                    "artifact_id": "community",
                    "locator": str(community_path),
                    "sha256": _sha(community_path),
                },
            ],
            "families": {
                "reddit_forum": {
                    "threads": [
                        {"thread_id": "abc", "artifact_id": "reddit_manifest_abc"}
                    ]
                }
            },
            "target_reconciliation": [
                {
                    "target_id": "reddit_abc",
                    "source_family": "reddit_forum",
                    "terminal_state": "used",
                    "native_artifact_id": "reddit_manifest_abc",
                    "axis_ids": ["wear"],
                }
            ],
            "community_axis_coding": {"artifact_id": "community"},
        },
    )

    source = build_phase_a_reddit_source_v3(
        run_spec_path=spec_path,
        evidence_ledger_path=ledger_path,
        repo_root=tmp_path,
    )

    assert len(source["captured_items"]) == 3
    assert [row["accounting_disposition"] for row in source["captured_items"]].count(
        "mechanically_excluded"
    ) == 2
    assessed = next(
        row for row in source["captured_items"] if row["accounting_disposition"] == "assess"
    )
    assert assessed["text"] == "It lasts through lunch."
    assert assessed["product_context"][0]["text"] == "Summer Fridays wear"
    assert assessed["product_candidates"] == ["Lip Butter Balm"]
    assert assessed["engagement"]["material_positive"] is True
    assert assessed["conversation_depth"] == 0
    assert assessed["source_reported_depth"] == 2
    assert next(
        row["locator"]
        for row in source["source_artifacts"]
        if row["artifact_id"] == "reddit_evidence_ledger"
    ) == "ledger.json"

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["families"]["reddit_forum"]["threads"].append(
        {"thread_id": "missing", "artifact_id": "reddit_manifest_missing"}
    )
    _write_json(ledger_path, ledger)
    with pytest.raises(SemanticIntegrationError, match="outside captured union"):
        build_phase_a_reddit_source_v3(
            run_spec_path=spec_path,
            evidence_ledger_path=ledger_path,
            repo_root=tmp_path,
        )


def _revolve_corpus(
    path: Path, reviews: list[dict], *, product_id: str | None = None
) -> None:
    _write_json(
        path,
        {
            "schema_version": "revolve_review_corpus_recent_v1",
            "source_product_ids": [product_id or path.stem],
            "captured_review_ids": [str(row["id"]) for row in reviews],
            "responses": [
                {
                    "body_text": json.dumps(
                        {"reviews": reviews}, ensure_ascii=False, sort_keys=True
                    )
                }
            ],
        },
    )


def test_retailer_source_builder_enumerates_deduplicates_and_fails_on_uncoded_text(
    tmp_path: Path,
) -> None:
    spec_path = _source_run_spec(tmp_path)
    source_a = tmp_path / "revolve-a.json"
    source_b = tmp_path / "revolve-b.json"
    placeholder = "This REVOLVE shopper left a rating without a review."
    _revolve_corpus(
        source_a,
        [
            {
                "id": "r1",
                "content": "Comfortable for hours.",
                "votesUp": 1,
                "user": {"userId": "user-1"},
            },
            {"id": "p1", "content": placeholder, "votesUp": 0, "user": {}},
        ],
        product_id="SUMR-WU1",
    )
    _revolve_corpus(
        source_b,
        [
            {
                "id": "r1",
                "content": "Comfortable for hours.",
                "votesUp": 1,
                "user": {"userId": "user-1"},
            },
            {"id": "p1", "content": placeholder, "votesUp": 0, "user": {}},
            {"id": "p2", "content": placeholder, "votesUp": 0, "user": {}},
        ],
        product_id="SUMR-WU14",
    )
    coding_path = tmp_path / "retailer-coding.json"
    _write_json(
        coding_path,
        {
            "rows": [
                {
                    "corpus_id": "revolve_native_reviews",
                    "review_id": "r1",
                    "product_context_id": "SUMR-WU1",
                    "axis_codes": [{"axis_id": "wear"}],
                    "source_row_ref": f"{source_a}#review:r1",
                }
            ]
        },
    )
    manifest_path = tmp_path / "retailer-manifest.json"
    _write_json(
        manifest_path,
        build_retailer_source_manifest(retailer_coding_path=coding_path),
    )
    completion_path = tmp_path / "completion.json"

    def write_completion() -> None:
        _write_json(
            completion_path,
            {
                "schema_version": "revolve_review_corpus_completion_run_v1",
                "completed_corpus_count": 2,
                "captured_review_occurrence_count": 5,
                "unique_review_id_count": 3,
                "cross_corpus_duplicate_review_ids": ["p1", "r1"],
                "outcomes": [
                    {
                        "status": "complete",
                        "failure": None,
                        "receipt_path": str(path),
                        "receipt_sha256": _raw_sha(path),
                        "captured_review_count": 2 if path == source_a else 3,
                    }
                    for path in (source_a, source_b)
                ],
            },
        )

    write_completion()
    source = build_phase_a_retailer_source_v3(
        run_spec_path=spec_path,
        retailer_coding_path=coding_path,
        retailer_source_manifest_path=manifest_path,
        revolve_completion_receipt_path=completion_path,
        repo_root=tmp_path,
    )
    assert len(source["containers"]) == 3
    assert len(source["source_artifacts"]) == 5
    assert sum(
        row["accounting_disposition"] == "assess" for row in source["captured_items"]
    ) == 1
    assert sum(
        row["accounting_disposition"] == "mechanically_excluded"
        for row in source["captured_items"]
    ) == 2
    readable = next(
        row for row in source["captured_items"] if row["accounting_disposition"] == "assess"
    )
    assert readable["engagement"]["material_positive"] is True
    assert readable["product_candidates"] == ["SUMR-WU1", "SUMR-WU14"]
    assert {
        (row["text"], row["source_artifact_id"], row["source_ref"])
        for row in readable["product_context"]
    } == {
        (
            "SUMR-WU1",
            next(
                row["artifact_id"]
                for row in source["source_artifacts"]
                if Path(row["locator"]).name == source_a.name
            ),
            f"{source_a}#review:r1",
        ),
        (
            "SUMR-WU14",
            next(
                row["artifact_id"]
                for row in source["source_artifacts"]
                if Path(row["locator"]).name == source_b.name
            ),
            f"{source_b}#review:r1",
        ),
    }
    assert {row["captured_at"] for row in source["containers"]} == {
        "capture_time_unavailable_in_preserved_source"
    }
    assert next(
        row["locator"]
        for row in source["source_artifacts"]
        if row["artifact_id"] == "retailer_axis_coding"
    ) == "retailer-coding.json"

    _revolve_corpus(
        source_b,
        [
            {
                "id": "r1",
                "content": "Comfortable for hours.",
                "votesUp": 1,
                "user": {"userId": "user-1"},
            },
            {"id": "p1", "content": placeholder, "votesUp": 0, "user": {}},
            {"id": "p2", "content": "This uncoded review must not vanish.", "votesUp": 0, "user": {}},
        ],
        product_id="SUMR-WU14",
    )
    write_completion()
    with pytest.raises(SemanticIntegrationError, match="uncoded"):
        build_phase_a_retailer_source_v3(
            run_spec_path=spec_path,
            retailer_coding_path=coding_path,
            retailer_source_manifest_path=manifest_path,
            revolve_completion_receipt_path=completion_path,
            repo_root=tmp_path,
        )


def test_reddit_source_builder_keeps_the_root_post_in_every_reply_ancestry(
    tmp_path: Path,
) -> None:
    spec_path = _source_run_spec(tmp_path)
    packet = tmp_path / "packet"
    raw = packet / "raw"
    raw.mkdir(parents=True)
    content_path = raw / "content_record.json"
    _write_json(
        content_path,
        {
            "thread": {"thread_id": "abc", "title": "Summer Fridays wear"},
            "post": {
                "body_text": "Does the balm survive a workday?",
                "author_state": "asker",
                "score_state": "9 points",
            },
            "comments": [
                {
                    "row_id": "comment_1",
                    "comment_id": "c1",
                    "body_text": "It lasts through lunch.",
                    "author_state": "customer",
                    "score_state": "2 points",
                    "depth": 0,
                },
                {
                    "row_id": "comment_2",
                    "comment_id": "c2",
                    "body_text": "Same for me.",
                    "author_state": "other",
                    "score_state": "2 points",
                    "depth": 1,
                },
            ],
        },
    )
    manifest_path = packet / "manifest.json"
    _write_json(
        manifest_path,
        {
            "source_locator": {
                "status": "known",
                "value": "https://old.reddit.com/r/test/comments/abc/example/",
            },
            "timing": {
                "capture_time": {"status": "known", "value": "2026-08-01T00:00:00Z"}
            },
            "preserved_files": [
                {
                    "relative_packet_path": "raw/content_record.json",
                    "sha256": _raw_sha(content_path),
                }
            ],
        },
    )
    community_path = tmp_path / "community.json"
    _write_json(
        community_path,
        {"legacy_parent_threads_not_requalified": [], "rows": []},
    )
    ledger_path = tmp_path / "ledger.json"
    _write_json(
        ledger_path,
        {
            "cycle_id": "cycle-1",
            "artifacts": [
                {
                    "artifact_id": "reddit_manifest_abc",
                    "locator": str(manifest_path),
                    "sha256": _sha(manifest_path),
                },
                {
                    "artifact_id": "community",
                    "locator": str(community_path),
                    "sha256": _sha(community_path),
                },
            ],
            "families": {
                "reddit_forum": {
                    "threads": [
                        {"thread_id": "abc", "artifact_id": "reddit_manifest_abc"}
                    ]
                }
            },
            "target_reconciliation": [
                {
                    "target_id": "reddit_abc",
                    "source_family": "reddit_forum",
                    "terminal_state": "used",
                    "native_artifact_id": "reddit_manifest_abc",
                    "axis_ids": ["wear"],
                }
            ],
            "community_axis_coding": {"artifact_id": "community"},
        },
    )

    source = build_phase_a_reddit_source_v3(
        run_spec_path=spec_path,
        evidence_ledger_path=ledger_path,
        repo_root=tmp_path,
    )
    items = {row["evidence_id"]: row for row in source["captured_items"]}
    post = items["reddit:abc:post"]
    top_level = items["reddit:abc:c1"]
    reply = items["reddit:abc:c2"]

    # A depth-0 reply answers the root post, so the post body must travel with
    # it; dropping the root also makes a personal-agreement unit unvalidatable.
    assert [row["source_ref"] for row in top_level["parent_context"]] == [
        post["source_ref"]
    ]
    assert top_level["parent_context"][0]["text"] == post["text"]
    assert top_level["conversation_depth"] == 1
    assert top_level["source_reported_depth"] == 0
    assert [row["source_ref"] for row in reply["parent_context"]] == [
        post["source_ref"],
        top_level["source_ref"],
    ]
    assert reply["conversation_depth"] == 2


def test_serp_target_reconciliation_links_only_exact_native_object_ids(
    tmp_path: Path,
) -> None:
    frontier_path = tmp_path / "frontier.json"
    frontier = {
        "schema_version": "phase_a_serp_source_frontier_review_result_v1",
        "locator_recovery_targets": [
            {
                "target_id": "reddit-hit",
                "locator": "https://www.reddit.com/r/x/comments/abc/title/",
            },
            {
                "target_id": "video-hit",
                "locator": "https://www.youtube.com/watch?v=video123",
            },
            {"target_id": "miss", "locator": "https://example.test/editorial"},
        ],
    }
    frontier["result_sha256"] = _canonical(frontier)
    _write_json(frontier_path, frontier)
    ledger_path = tmp_path / "ledger.json"
    _write_json(
        ledger_path,
        {
            "target_reconciliation": [
                {
                    "target_id": "reddit_abc",
                    "source_family": "reddit_forum",
                    "locator": "https://old.reddit.com/r/x/comments/abc/title/",
                    "native_artifact_id": "reddit_manifest_abc",
                }
            ],
            "families": {
                "native_social": {
                    "posts": [
                        {
                            "unit_id": "yt_video123",
                            "platform": "youtube",
                            "post_id": "video123",
                            "artifact_id": "social-composition",
                        }
                    ]
                }
            },
        },
    )

    result = reconcile_serp_frontier_targets(
        frontier_result_path=frontier_path, evidence_ledger_path=ledger_path
    )

    assert result["terminal_state_counts"] == {
        "already_captured": 2,
        "historical_capture_unavailable": 1,
    }
    assert result["new_source_acquisition_performed"] is False
