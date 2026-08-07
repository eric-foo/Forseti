from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from judgment.phase_a_semantic_run import (
    RUN_SPEC_VERSION,
    audit_phase_a_source,
    build_retailer_source_manifest,
    census_phase_a_customer_corpus,
    materialize_phase_a_v3,
    materialize_serp_source_frontier_review,
    prepare_serp_source_frontier_inventory,
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
    assert invalid["invalid_responses"][0]["error"] == (
        "batch response has stale bundle hash"
    )
    assert recovered["batch_stage_complete"] is True


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
    spec_path = tmp_path / "surface-spec.json"
    _write_json(
        spec_path,
        {
            "schema_version": "phase_a_serp_source_surface_spec_v1",
            "search_surfaces": [
                {
                    "phase": "serp_phase1",
                    "job_id": "p1",
                    "artifact_ids": ["serp-1"],
                }
            ],
            "source_artifacts": [
                {
                    "artifact_id": "serp-1",
                    "locator": str(record_path),
                    "raw_sha256": _raw_sha(record_path),
                }
            ],
        },
    )

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
