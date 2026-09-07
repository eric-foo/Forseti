"""Transport and persistence falsifiers; semantic behavior is measured by dogfood."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

import judgment.semantic_evidence_integration as semantic
import judgment.phase_a_evidence_selection as selection
from judgment.phase_a_semantic_run import materialize_phase_a_v3
from test_phase_a_semantic_run import _spec_v8
from test_semantic_evidence_integration import (
    _source_v7, _v5_responses, _row_verification_responses, _group_level_responses,
)


def test_new_run_selects_preventive_method_without_restamping_previous_run(tmp_path):
    spec = _spec_v8(tmp_path)
    bindings = []
    for run_version in ("phase_a_semantic_integration_run_v10", "phase_a_semantic_integration_run_v11"):
        spec["schema_version"] = run_version
        source, _ = materialize_phase_a_v3(spec, repo_root=tmp_path)
        bundle = semantic.build_bundle(source, max_prompt_bytes=30_000)
        bindings.append((bundle["method_version"], semantic._verification_method(bundle)[0]))
        prompts = semantic.build_batch_prompts(bundle)
        assert sum(len(batch["evidence_ids"]) for batch in bundle["batches"]) == len(bundle["evidence_units"])
        assert all(semantic.build_batch_response_schema(bundle, row["batch_id"]) for row in prompts)
    assert bindings == [
        (semantic.METHOD_VERSION_V12, semantic.ROW_VERIFICATION_METHOD_VERSION_V11),
        (semantic.METHOD_VERSION_V13, semantic.ROW_VERIFICATION_METHOD_VERSION_V12),
    ]


def _portable_pipeline(tmp_path, dates, *, mutate_materializer=None):
    source = _source_v7(count=len(dates))
    expected = {}
    for row, date in zip(source["captured_items"], dates, strict=True):
        row["publication_time"] = date
        expected[row["evidence_id"]] = date
    materialized = semantic.materialize_source_v3(source)
    # The second materialization models a source migration while Collection
    # locators remain inaccessible; no date may be replaced with capture time.
    if mutate_materializer:
        materialized = mutate_materializer(materialized)
    materialized = semantic.materialize_source_v3(materialized)
    assert {row["evidence_id"]: row.get("publication_time") for row in materialized["captured_items"]} == expected, "publication time changed during materialization"
    bundle = semantic.build_bundle(materialized, max_prompt_bytes=30_000)
    compiled = semantic.validate_batch_responses(bundle, _v5_responses(bundle, detailed_per_batch=len(dates)))
    stage, _ = semantic.prepare_row_verification(bundle, compiled, max_prompt_bytes=30_000)
    verified = semantic.apply_row_verification(bundle, compiled, stage, _row_verification_responses(stage))
    reconciliation, _ = semantic.prepare_reconciliation_stage(bundle, verified)
    terminal = semantic.validate_reconciliation_stage(bundle, reconciliation, _group_level_responses(reconciliation, terminal=True))
    view = semantic.finalize_v3_view(bundle, verified, terminal)
    packet = semantic.project_evidence_packet(view, bundle, verified, terminal, axis_ids=["wear"])
    bundle_path, packet_path = tmp_path/"bundle.json", tmp_path/"packet.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    source_binding = {"source_id": "portable", "bundle": bundle, "packet": packet,
                      "bundle_path": bundle_path, "packet_path": packet_path}
    assert selection._has_portable_materialized_source_identity(source_binding)
    subjects = sorted({product for row in verified["semantic_units"] for product in row["subject_product_ids"]})
    candidates = selection._candidate_rows([source_binding], {"axis_ids": ["wear"], "subject_product_ids": subjects})
    return expected, candidates


def test_verified_dates_reach_portable_selection_without_collection_paths(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("portable selection reopened a legacy Collection artifact")
    monkeypatch.setattr(selection, "_publication_time_from_artifact", forbidden)
    dates = ["2025-03-03T02:19:07.000+00:00", "2026-06-16", None, "2 months ago"]
    expected, candidates = _portable_pipeline(tmp_path, dates)
    observed = {row["evidence_id"]: row["publication_time"] for row in candidates}
    assert len(observed) == len(dates)
    assert observed == {key: selection._publication_time_value(value) for key, value in expected.items()}


def test_date_preservation_signal_rejects_loss_inside_an_admitted_row(tmp_path):
    def lose_known_date(source):
        source = deepcopy(source)
        source["captured_items"][0].pop("publication_time")
        # Deliberately rehash: hash integrity alone cannot detect semantic loss.
        source.pop("source_sha256")
        source["source_sha256"] = semantic._sha256(source)
        return source
    with pytest.raises(AssertionError, match="publication time changed during materialization"):
        _portable_pipeline(tmp_path, ["2026-06-16", None], mutate_materializer=lose_known_date)
