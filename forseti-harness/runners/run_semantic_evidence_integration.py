"""Prepare and compile one agent-run semantic evidence integration job."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judgment.semantic_evidence_integration import (  # noqa: E402
    BUNDLE_VERSION_V4,
    RECONCILIATION_POLICY_VERSION_V2,
    SemanticIntegrationError,
    apply_row_verification,
    apply_row_repair,
    build_batch_prompts,
    build_batch_response_schema,
    build_bundle,
    build_prompt_execution_pack,
    build_reconciliation_prompt,
    finalize_v3_view,
    finalize_relation_closed_view,
    finalize_view,
    is_terminal_reconciliation_compilation,
    materialize_source_v3,
    migrate_repaired_terminal_compilation,
    project_evidence_packet,
    project_evidence_packet_v1,
    project_evidence_packet_v2,
    prepare_targeted_benchmark_audit,
    prepare_reconciliation_stage,
    prepare_relation_closure_stage,
    prepare_row_repair,
    prepare_row_verification,
    reconstruct_prompt_execution_payload,
    validate_batch_responses,
    validate_reconciliation_stage,
    validate_relation_closure_stage,
    validate_targeted_benchmark_audit,
)
from judgment.semantic_calibration import (  # noqa: E402
    CALIBRATION_PREPARATION_VERSION,
    SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT,
    SemanticCalibrationError,
    adjudication_contract_identity,
    evaluate_semantic_calibration,
    prepare_semantic_calibration,
    validate_calibration_spec,
)
from judgment.phase_a_semantic_run import (  # noqa: E402
    audit_phase_a_source,
    build_phase_a_reddit_source_v3,
    build_phase_a_retailer_source_v3,
    build_phase_a_product_axis_proof_source,
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
from judgment.phase_a_evidence_consumer import (  # noqa: E402
    EvidenceConsumerError,
    finalize_decision_batch,
    load_prepared_cases,
    prepare_decision_batch,
)
from judgment.phase_a_evidence_selection import (  # noqa: E402
    SELECTION_SPEC_VERSION,
    SELECTION_BATCH_MANIFEST_VERSION,
    build_customer_pull_point_frontier,
    finalize_batched_preselection_relation_confirmations_prepare_quotes,
    finalize_batched_relations_prepare_quotes,
    finalize_preselection_relation_confirmation_prepare_quotes,
    finalize_quotes,
    finalize_relations_prepare_quotes,
    load_selection_sources,
    prepare_evidence_selection,
    prepare_evidence_selection_batches,
    prepare_batched_preselection_relation_confirmations,
    prepare_preselection_relation_confirmation,
    prepare_selected_relation_confirmation,
    selection_spec_from_customer_pull_frontier,
    validate_evidence_selection_batch_response,
    verify_customer_pull_point_frontier,
)
from harness_utils import hash_file  # noqa: E402
from provider_attempts import (  # noqa: E402
    publish_provider_attempt,
    reserve_provider_attempt,
)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _write_json(path: Path, value: Any) -> None:
    _write_new(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )


def _load_prepared_prompts(
    slice_dir: Path, bundle: dict[str, Any]
) -> list[dict[str, Any]]:
    prompt_dir = slice_dir / "prompts"
    expected_prompts = {
        row["batch_id"]: row for row in build_batch_prompts(bundle)
    }
    expected_ids = list(expected_prompts)
    observed_paths = {
        path.stem: path for path in prompt_dir.glob("*.md") if path.is_file()
    }
    if set(observed_paths) != set(expected_ids):
        raise ValueError(f"prepared prompt set does not match bundle: {slice_dir}")
    prompts: list[dict[str, Any]] = []
    for batch_id in expected_ids:
        prompt_text = observed_paths[batch_id].read_bytes().decode("utf-8")
        prompts.append(
            {
                # Metadata comes from the bound producer; prompt text must still
                # come from disk so substitution remains observable to evaluation.
                **expected_prompts[batch_id],
                "prompt": prompt_text,
                "prompt_utf8_bytes": len(prompt_text.encode("utf-8")),
            }
        )
    return prompts


def _resolve_artifact(repo_root: Path, locator: str) -> Path:
    raw = Path(locator)
    if raw.is_absolute():
        resolved = raw.resolve(strict=True)
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError:
            return resolved
        raise ValueError(f"repository-internal artifact must use a relative locator: {locator}")
    resolved = (repo_root / raw).resolve(strict=True)
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"artifact locator escapes repo root: {locator}") from exc
    return resolved


def _verify_sources(source: dict[str, Any], *, repo_root: Path) -> None:
    artifacts = source.get("source_artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("source_artifacts must be a list")
    for row in artifacts:
        if not isinstance(row, dict):
            raise ValueError("source artifact must be an object")
        locator = row.get("locator")
        expected = row.get("sha256")
        if not isinstance(locator, str) or not isinstance(expected, str):
            raise ValueError("source artifact lacks locator or sha256")
        observed = hash_file(_resolve_artifact(repo_root, locator))
        if observed != expected:
            raise ValueError(
                f"source artifact hash mismatch for {row.get('artifact_id')}: "
                f"expected {expected}, observed {observed}"
            )


def prepare_semantic_calibration_run(
    *, source_path: Path, spec_path: Path, output_dir: Path
) -> dict[str, Any]:
    """Prepare exact spec-selected calibration slices and their prompts."""
    source = _load_object(source_path)
    spec = _load_object(spec_path)
    prepared = prepare_semantic_calibration(source, spec)
    _write_json(output_dir / "preparation_receipt.json", prepared["receipt"])
    adjudication_contract_path = output_dir / "adjudication_contract.md"
    _write_new(
        adjudication_contract_path,
        SEMANTIC_CALIBRATION_ADJUDICATION_CONTRACT.encode("utf-8"),
    )
    for slice_row in prepared["slices"]:
        slice_dir = output_dir / slice_row["slice_id"]
        _write_json(slice_dir / "source.json", slice_row["source"])
        _write_json(slice_dir / "bundle.json", slice_row["bundle"])
        _write_json(slice_dir / "route_fingerprint.json", slice_row["route_fingerprint"])
        for prompt in slice_row["prompts"]:
            _write_new(
                slice_dir / "prompts" / f"{prompt['batch_id']}.md",
                prompt["prompt"].encode("utf-8"),
            )
    cold_repeat = prepared.get("cold_repeat")
    if isinstance(cold_repeat, dict):
        cold_dir = output_dir / "cold-repeat"
        _write_json(cold_dir / "source.json", cold_repeat["source"])
        _write_json(cold_dir / "bundle.json", cold_repeat["bundle"])
        _write_json(
            cold_dir / "route_fingerprint.json",
            cold_repeat["route_fingerprint"],
        )
        for prompt in cold_repeat["prompts"]:
            _write_new(
                cold_dir / "prompts" / f"{prompt['batch_id']}.md",
                prompt["prompt"].encode("utf-8"),
            )
    return {
        "status": "SEMANTIC_CALIBRATION_PREPARED",
        "preparation_sha256": prepared["receipt"]["preparation_sha256"],
        "adjudication_contract_id": prepared["receipt"][
            "adjudication_contract_id"
        ],
        "adjudication_contract_sha256": hash_file(adjudication_contract_path),
        "spec_sha256": prepared["receipt"]["spec_sha256"],
        "slice_count": len(prepared["slices"]),
        "work_unit_count": sum(
            len(row["bundle"]["batches"]) for row in prepared["slices"]
        )
        + (
            0
            if not isinstance(cold_repeat, dict)
            else len(cold_repeat["bundle"]["batches"])
        ),
        "model_api_calls": 0,
    }


def evaluate_semantic_calibration_run(
    *,
    source_path: Path,
    prepared_dir: Path,
    spec_path: Path,
    response_root: Path,
    cold_response_root: Path | None,
    reconciliation_root: Path | None,
    adjudication_path: Path | None,
    report_out: Path,
    verified_compilation_root: Path | None = None,
) -> dict[str, Any]:
    """Evaluate returned calibration slices; a non-pass remains visible."""
    # The sidecar is the adjudicator-facing ruler. New preparations bind its
    # stable id and full hash in the receipt; legacy preparations may carry one
    # of the two exact preserved v1 rulers or no sidecar at all.
    adjudication_contract_path = prepared_dir / "adjudication_contract.md"
    contract_identity = (
        adjudication_contract_identity(adjudication_contract_path.read_bytes())
        if adjudication_contract_path.is_file()
        else None
    )
    receipt = _load_object(prepared_dir / "preparation_receipt.json")
    if receipt.get("schema_version") == CALIBRATION_PREPARATION_VERSION:
        if contract_identity is None:
            raise ValueError("bound calibration preparation lacks its ruler sidecar")
        for field, observed in contract_identity.items():
            if receipt.get(field) != observed:
                raise ValueError(
                    f"prepared adjudication contract does not match receipt: {field}"
                )
    source = _load_object(source_path)
    spec = _load_object(spec_path)
    normalized = validate_calibration_spec(spec)
    prepared: dict[str, Any] = {
        "receipt": receipt,
        "slices": [],
        "cold_repeat": None,
    }
    responses_by_slice: dict[str, list[dict[str, Any]]] = {}
    cold_responses_by_slice: dict[str, list[dict[str, Any]]] = {}
    for slice_spec in normalized["slices"]:
        slice_id = slice_spec["slice_id"]
        slice_dir = prepared_dir / slice_id
        bundle = _load_object(slice_dir / "bundle.json")
        prepared["slices"].append(
            {
                "slice_id": slice_id,
                "source": _load_object(slice_dir / "source.json"),
                "bundle": bundle,
                "prompts": _load_prepared_prompts(slice_dir, bundle),
                "route_fingerprint": _load_object(
                    slice_dir / "route_fingerprint.json"
                ),
            }
        )
        response_dir = response_root / slice_id
        responses_by_slice[slice_id] = [
            _load_object(path)
            for path in sorted(response_dir.glob("batch-*.json"))
            if path.is_file()
        ]
    if normalized["cold_repeat"] is not None:
        cold_dir = prepared_dir / "cold-repeat"
        cold_bundle = _load_object(cold_dir / "bundle.json")
        prepared["cold_repeat"] = {
            "slice_id": "cold-repeat",
            "source": _load_object(cold_dir / "source.json"),
            "bundle": cold_bundle,
            "prompts": _load_prepared_prompts(cold_dir, cold_bundle),
            "route_fingerprint": _load_object(
                cold_dir / "route_fingerprint.json"
            ),
        }
        if cold_response_root is not None:
            cold_response_dir = cold_response_root / "cold-repeat"
            cold_responses_by_slice["cold-repeat"] = [
                _load_object(path)
                for path in sorted(cold_response_dir.glob("batch-*.json"))
                if path.is_file()
            ]
    adjudication = (
        None if adjudication_path is None else _load_object(adjudication_path)
    )
    reconciliation_by_slice = (
        {}
        if reconciliation_root is None
        else {
            slice_spec["slice_id"]: {
                "node_compilation": _load_object(
                    reconciliation_root
                    / slice_spec["slice_id"]
                    / "node_compilation.json"
                ),
                "view": _load_object(
                    reconciliation_root / slice_spec["slice_id"] / "view.json"
                ),
            }
            for slice_spec in normalized["slices"]
            if (reconciliation_root / slice_spec["slice_id"] / "view.json").is_file()
        }
    )
    verified_slice_ids = [row["slice_id"] for row in normalized["slices"]]
    if normalized["cold_repeat"] is not None:
        verified_slice_ids.append("cold-repeat")
    verified_compilations_by_slice = (
        {}
        if verified_compilation_root is None
        else {
            slice_id: _load_object(
                verified_compilation_root / slice_id / "batch_compilation.json"
            )
            for slice_id in verified_slice_ids
            if (
                verified_compilation_root / slice_id / "batch_compilation.json"
            ).is_file()
        }
    )
    report = evaluate_semantic_calibration(
        prepared,
        spec,
        responses_by_slice,
        adjudication,
        cold_responses_by_slice,
        reconciliation_by_slice,
        verified_compilations_by_slice,
        full_source=source,
    )
    _write_json(report_out, report)
    return report


def prepare_batches(
    *, source_path: Path, repo_root: Path, bundle_out: Path, prompt_dir: Path,
    max_batch_chars: int, max_prompt_bytes: int | None = None,
    max_evidence_per_work_unit: int = 120,
) -> dict[str, Any]:
    source = _load_object(source_path)
    _verify_sources(source, repo_root=repo_root)
    bundle = build_bundle(
        source,
        max_batch_chars=max_batch_chars,
        max_prompt_bytes=max_prompt_bytes,
        max_evidence_per_work_unit=max_evidence_per_work_unit,
    )
    if prompt_dir.exists():
        raise ValueError(f"refusing to write into existing prompt directory: {prompt_dir}")
    _write_json(bundle_out, bundle)
    prompt_dir.mkdir(parents=True)
    prompts = build_batch_prompts(bundle)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
        if "response_schema" in row:
            _write_json(
                prompt_dir / "response-schemas" / f"{row['batch_id']}.json",
                row["response_schema"],
            )
    # Only the legacy v4 projection carries a static partition. The new
    # generation selects work globally at run time, so writing an assignment
    # manifest here would reintroduce the topology it removed.
    if bundle.get("schema_version") == BUNDLE_VERSION_V4:
        _write_json(
            prompt_dir / "worker_assignments.json",
            {
                "schema_version": "semantic_worker_assignment_v1",
                "bundle_sha256": bundle["bundle_sha256"],
                # Report the partitioning the bundle actually carries rather
                # than a constant the manifest cannot fall out of sync with.
                "worker_count": bundle["semantic_work_unit_projection"]["worker_count"],
                "assignments": [
                    {
                        "batch_id": row["batch_id"],
                        "worker_partition": row["worker_partition"],
                        "prompt_file": f"{row['batch_id']}.md",
                    }
                    for row in prompts
                ],
            },
        )
    return {
        "status": "SEMANTIC_BATCH_JUDGMENT_REQUIRED",
        "bundle_sha256": bundle["bundle_sha256"],
        "corpus_sha256": bundle["corpus_sha256"],
        "batch_count": len(prompts),
        "response_schema_count": sum(
            1 for row in prompts if "response_schema" in row
        ),
        "admitted_evidence_unit_count": bundle["coverage_denominator"]["admitted_evidence_unit_count"],
        "bundle_out": str(bundle_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
        **(
            {
                "max_prompt_bytes": bundle["max_prompt_bytes"],
                "largest_rendered_prompt_bytes": max(
                    row["prompt_utf8_bytes"] for row in prompts
                ),
                "captured_item_count": bundle["coverage_denominator"][
                    "captured_item_count"
                ],
            }
            if bundle.get("schema_version") in {
                "semantic_evidence_bundle_v3",
                BUNDLE_VERSION_V4,
            }
            else {}
        ),
    }


def prepare_prompt_execution_pack(
    *, bundle_path: Path, pack_dir: Path
) -> dict[str, Any]:
    """Write a load-once frame plus exact per-batch semantic payloads."""
    if pack_dir.exists():
        raise ValueError(f"refusing to write into existing execution pack: {pack_dir}")
    bundle = _load_object(bundle_path)
    frame, manifest, payloads = build_prompt_execution_pack(bundle)
    pack_dir.mkdir(parents=True)
    _write_new(pack_dir / manifest["frame_file"], frame.encode("utf-8"))
    for payload in payloads:
        # Field order is part of the historical pretty-JSON prompt bytes.
        # The generic writer sorts nested keys, so payloads use their bound
        # insertion order and are reconstructed again after the fresh read.
        _write_new(
            pack_dir / "payloads" / f"{payload['batch_id']}.json",
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            + b"\n",
        )
    for batch in manifest["batches"]:
        schema_file = batch.get("response_schema_file")
        if schema_file is not None:
            schema = build_batch_response_schema(bundle, batch["batch_id"])
            if schema is None:
                raise ValueError(
                    f"execution manifest unexpectedly names a response schema for {batch['batch_id']}"
                )
            _write_json(pack_dir / schema_file, schema)
    _write_json(pack_dir / "manifest.json", manifest)
    verified = verify_prompt_execution_pack(
        bundle_path=bundle_path,
        pack_dir=pack_dir,
    )
    return {
        "status": "SEMANTIC_PROMPT_EXECUTION_PACK_PREPARED",
        **verified,
    }


def verify_prompt_execution_pack(
    *, bundle_path: Path, pack_dir: Path
) -> dict[str, Any]:
    """Fresh-read one stored pack and compare it to its immutable bundle."""
    bundle = _load_object(bundle_path)
    expected_frame, expected_manifest, expected_payloads = (
        build_prompt_execution_pack(bundle)
    )
    # Text-mode reads translate CRLF, so a frame whose stored bytes are no
    # longer the hash-bound frame could still compare equal. The frame is
    # spliced into prompts as raw text, so decode its bytes directly.
    observed_frame = (
        (pack_dir / expected_manifest["frame_file"]).read_bytes().decode("utf-8")
    )
    if observed_frame != expected_frame:
        raise ValueError("stored execution frame does not match bundle")
    observed_manifest = _load_object(pack_dir / "manifest.json")
    if observed_manifest != expected_manifest:
        raise ValueError("stored execution manifest does not match bundle")
    # The pack is exclusive: a verified pack may hold no file the bundle does
    # not name, so a stale, renamed, or leftover payload cannot ride along
    # unverified and cannot inflate the stored-byte total reported below.
    expected_files = {
        Path(expected_manifest["frame_file"]),
        Path("manifest.json"),
        *(Path(row["payload_file"]) for row in expected_manifest["batches"]),
        *(
            Path(row["response_schema_file"])
            for row in expected_manifest["batches"]
            if "response_schema_file" in row
        ),
    }
    observed_files = {
        path.relative_to(pack_dir) for path in pack_dir.rglob("*") if path.is_file()
    }
    if observed_files != expected_files:
        raise ValueError("stored execution pack file set does not match bundle")
    payload_path_by_batch = {
        row["batch_id"]: pack_dir / row["payload_file"]
        for row in expected_manifest["batches"]
    }
    for expected in expected_payloads:
        observed = _load_object(payload_path_by_batch[expected["batch_id"]])
        if observed != expected:
            raise ValueError(
                f"stored execution payload {expected['batch_id']} does not match bundle"
            )
        # Dict equality does not consider key order, but prompt bytes do.
        # Reconstructing the freshly read object closes that serialization gap.
        try:
            reconstruct_prompt_execution_payload(observed_frame, observed)
        except SemanticIntegrationError as exc:
            raise ValueError(
                f"stored execution payload {expected['batch_id']} cannot reconstruct"
            ) from exc
    for batch in expected_manifest["batches"]:
        schema_file = batch.get("response_schema_file")
        if schema_file is None:
            continue
        expected_schema = build_batch_response_schema(bundle, batch["batch_id"])
        observed_schema = _load_object(pack_dir / schema_file)
        if observed_schema != expected_schema:
            raise ValueError(
                f"stored response schema {batch['batch_id']} does not match bundle"
            )
    stored_bytes = sum(
        path.stat().st_size for path in pack_dir.rglob("*") if path.is_file()
    )
    original_bytes = expected_manifest["original_total_prompt_bytes"]
    return {
        "verification_status": "SEMANTIC_PROMPT_EXECUTION_PACK_VERIFIED",
        "bundle_sha256": bundle["bundle_sha256"],
        "batch_count": expected_manifest["batch_count"],
        "pack_dir": str(pack_dir),
        "manifest_sha256": expected_manifest["manifest_sha256"],
        "original_total_prompt_bytes": original_bytes,
        "execution_pack_stored_bytes": stored_bytes,
        "stored_byte_reduction": original_bytes - stored_bytes,
        "stored_byte_reduction_pct": round(
            100 * (original_bytes - stored_bytes) / original_bytes, 2
        ),
        "model_api_calls": 0,
    }


def materialize_v3(
    *, source_path: Path, repo_root: Path, source_out: Path
) -> dict[str, Any]:
    source = _load_object(source_path)
    _verify_sources(source, repo_root=repo_root)
    materialized = materialize_source_v3(source)
    _write_json(source_out, materialized)
    counts: dict[str, int] = {}
    for row in materialized["captured_items"]:
        disposition = row["accounting_disposition"]
        counts[disposition] = counts.get(disposition, 0) + 1
    return {
        "status": "SEMANTIC_EVIDENCE_SOURCE_V3_MATERIALIZED",
        "source_sha256": materialized["source_sha256"],
        "captured_item_count": len(materialized["captured_items"]),
        "captured_container_count": len(materialized["containers"]),
        "accounting_disposition_counts": dict(sorted(counts.items())),
        "source_out": str(source_out),
        "model_api_calls": 0,
    }


def build_product_axis_proof_run(
    *,
    full_source_path: Path,
    run_spec_path: Path,
    stable_product_id: str,
    axis_ids: list[str],
    repo_root: Path,
    source_out: Path,
) -> dict[str, Any]:
    source = build_phase_a_product_axis_proof_source(
        full_source_path=full_source_path,
        run_spec_path=run_spec_path,
        stable_product_id=stable_product_id,
        axis_ids=axis_ids,
        repo_root=repo_root,
    )
    _write_json(source_out, source)
    family_counts: dict[str, int] = {}
    for row in source["captured_items"]:
        family = row["source_family"]
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "status": "PHASE_A_PRODUCT_AXIS_PROOF_SOURCE_READY",
        "source_sha256": source["source_sha256"],
        "stable_product_id": stable_product_id,
        "axis_ids": sorted(axis_ids),
        "assessable_evidence_count": len(source["captured_items"]),
        "source_family_counts": dict(sorted(family_counts.items())),
        "source_out": str(source_out),
        "model_api_calls": 0,
    }


def audit_phase_a_source_run(
    *, spec_path: Path, repo_root: Path, audit_out: Path
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    audit = audit_phase_a_source(spec, repo_root=repo_root)
    _write_json(audit_out, audit)
    return {
        "status": (
            "PHASE_A_SOURCE_AUDIT_COMPLETE"
            if audit["complete"]
            else "PHASE_A_SOURCE_AUDIT_BLOCKED"
        ),
        "audit_sha256": audit["audit_sha256"],
        "sealed_route_count": audit["sealed_route_count"],
        "verified_source_binding_count": len(audit["verified_source_bindings"]),
        "blocked_routes": audit["blocked_routes"],
        "audit_out": str(audit_out),
        "model_api_calls": 0,
    }


def census_phase_a_corpus_run(
    *,
    evidence_ledger_path: Path,
    retailer_coding_path: Path,
    retailer_source_manifest_path: Path,
    census_out: Path,
) -> dict[str, Any]:
    census = census_phase_a_customer_corpus(
        evidence_ledger_path=evidence_ledger_path,
        retailer_coding_path=retailer_coding_path,
        retailer_source_manifest_path=retailer_source_manifest_path,
    )
    _write_json(census_out, census)
    return {
        "status": "PHASE_A_CUSTOMER_CORPUS_CENSUS_COMPLETE",
        "census_sha256": census["census_sha256"],
        "reddit": census["reddit"],
        "retailer_reviews": census["retailer_reviews"],
        "census_out": str(census_out),
        "model_api_calls": 0,
    }


def build_retailer_source_manifest_run(
    *, retailer_coding_path: Path, manifest_out: Path
) -> dict[str, Any]:
    manifest = build_retailer_source_manifest(retailer_coding_path=retailer_coding_path)
    _write_json(manifest_out, manifest)
    return {
        "status": "RETAILER_REVIEW_SOURCE_MANIFEST_COMPLETE",
        "manifest_sha256": manifest["manifest_sha256"],
        "source_set_sha256": manifest["source_set_sha256"],
        "source_file_count": len(manifest["sources"]),
        "manifest_out": str(manifest_out),
        "model_api_calls": 0,
    }


def build_phase_a_reddit_source_v3_run(
    *,
    run_spec_path: Path,
    evidence_ledger_path: Path,
    repo_root: Path,
    source_out: Path,
) -> dict[str, Any]:
    source = build_phase_a_reddit_source_v3(
        run_spec_path=run_spec_path,
        evidence_ledger_path=evidence_ledger_path,
        repo_root=repo_root,
    )
    _write_json(source_out, source)
    dispositions = {
        disposition: sum(
            row["accounting_disposition"] == disposition
            for row in source["captured_items"]
        )
        for disposition in ("assess", "mechanically_excluded", "blocked")
    }
    return {
        "status": "PHASE_A_REDDIT_SOURCE_V3_COMPLETE",
        "source_sha256": source["source_sha256"],
        "source_artifact_count": len(source["source_artifacts"]),
        "container_count": len(source["containers"]),
        "captured_item_count": len(source["captured_items"]),
        "accounting_disposition_counts": dispositions,
        "source_out": str(source_out),
        "model_api_calls": 0,
    }


def build_phase_a_retailer_source_v3_run(
    *,
    run_spec_path: Path,
    retailer_coding_path: Path,
    retailer_source_manifest_path: Path,
    revolve_completion_receipt_path: Path | None,
    repo_root: Path,
    source_out: Path,
) -> dict[str, Any]:
    source = build_phase_a_retailer_source_v3(
        run_spec_path=run_spec_path,
        retailer_coding_path=retailer_coding_path,
        retailer_source_manifest_path=retailer_source_manifest_path,
        revolve_completion_receipt_path=revolve_completion_receipt_path,
        repo_root=repo_root,
    )
    _write_json(source_out, source)
    dispositions = {
        disposition: sum(
            row["accounting_disposition"] == disposition
            for row in source["captured_items"]
        )
        for disposition in ("assess", "mechanically_excluded", "blocked")
    }
    return {
        "status": "PHASE_A_RETAILER_SOURCE_V3_COMPLETE",
        "source_sha256": source["source_sha256"],
        "source_artifact_count": len(source["source_artifacts"]),
        "container_count": len(source["containers"]),
        "captured_item_count": len(source["captured_items"]),
        "accounting_disposition_counts": dispositions,
        "source_out": str(source_out),
        "model_api_calls": 0,
    }


def prepare_serp_source_frontier_run(
    *, surface_spec_path: Path, inventory_out: Path
) -> dict[str, Any]:
    inventory = prepare_serp_source_frontier_inventory(
        surface_spec_path=surface_spec_path
    )
    _write_json(inventory_out, inventory)
    return {
        "status": "SERP_SOURCE_FRONTIER_SEMANTIC_REVIEW_REQUIRED",
        "inventory_sha256": inventory["inventory_sha256"],
        "source_artifact_count": inventory["source_artifact_count"],
        "eligible_row_count": inventory["eligible_row_count"],
        "inventory_out": str(inventory_out),
        "model_api_calls": 0,
    }


def build_serp_source_surface_spec_run(
    *, surface_map_path: Path, surface_spec_out: Path
) -> dict[str, Any]:
    spec = build_serp_source_surface_spec(surface_map_path=surface_map_path)
    _write_json(surface_spec_out, spec)
    return {
        "status": "SERP_SOURCE_SURFACE_SPEC_COMPLETE",
        "surface_spec_sha256": spec["surface_spec_sha256"],
        "search_surface_count": len(spec["search_surfaces"]),
        "source_artifact_count": len(spec["source_artifacts"]),
        "surface_spec_out": str(surface_spec_out),
        "model_api_calls": 0,
    }


def materialize_serp_source_frontier_review_run(
    *, inventory_path: Path, review_path: Path, result_out: Path
) -> dict[str, Any]:
    result = materialize_serp_source_frontier_review(
        inventory_path=inventory_path, review_path=review_path
    )
    _write_json(result_out, result)
    return {
        "status": "SERP_SOURCE_FRONTIER_REVIEW_MATERIALIZED",
        "result_sha256": result["result_sha256"],
        "classification_counts": result["classification_counts"],
        "locator_recovery_target_count": len(result["locator_recovery_targets"]),
        "result_out": str(result_out),
        "model_api_calls": 0,
    }


def reconcile_serp_frontier_targets_run(
    *, frontier_result_path: Path, evidence_ledger_path: Path, result_out: Path
) -> dict[str, Any]:
    result = reconcile_serp_frontier_targets(
        frontier_result_path=frontier_result_path,
        evidence_ledger_path=evidence_ledger_path,
    )
    _write_json(result_out, result)
    return {
        "status": "SERP_FRONTIER_TARGETS_RECONCILED",
        "reconciliation_sha256": result["reconciliation_sha256"],
        "target_count": len(result["targets"]),
        "terminal_state_counts": result["terminal_state_counts"],
        "result_out": str(result_out),
        "model_api_calls": 0,
    }


def materialize_phase_a_source(
    *,
    spec_path: Path,
    repo_root: Path,
    source_out: Path,
    receipt_out: Path,
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    source, receipt = materialize_phase_a_v3(spec, repo_root=repo_root)
    _write_json(source_out, source)
    _write_json(receipt_out, receipt)
    return {
        "status": "PHASE_A_SEMANTIC_SOURCE_MATERIALIZED",
        "source_sha256": source["source_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "captured_item_count": receipt["captured_item_count"],
        "captured_container_count": receipt["captured_container_count"],
        "source_out": str(source_out),
        "receipt_out": str(receipt_out),
        "model_api_calls": 0,
    }


def validate_batch_response_file(
    *, bundle_path: Path, response_path: Path, receipt_out: Path | None
) -> dict[str, Any]:
    receipt = validate_one_batch_response(
        _load_object(bundle_path), _load_object(response_path)
    )
    if receipt_out is not None:
        _write_json(receipt_out, receipt)
    return {
        "status": "SEMANTIC_BATCH_RESPONSE_VALID",
        **receipt,
        "receipt_out": str(receipt_out) if receipt_out is not None else None,
        "model_api_calls": 0,
    }


def publish_batch_response_file(
    *,
    bundle_path: Path,
    staged_response_path: Path,
    response_dir: Path,
) -> dict[str, Any]:
    """Validate one sibling temp response and atomically publish it once."""
    response_dir.mkdir(parents=True, exist_ok=True)
    if staged_response_path.parent.resolve() != response_dir.resolve():
        raise ValueError("staged response must be a sibling of its final response")
    if not staged_response_path.name.endswith(".json.tmp"):
        raise ValueError("staged response must use the .json.tmp suffix")
    response = _load_object(staged_response_path)
    receipt = validate_one_batch_response(_load_object(bundle_path), response)
    batch_ids = receipt["validated_batch_ids"]
    if len(batch_ids) != 1:
        raise ValueError("staged response must validate exactly one batch")
    target = response_dir / f"{batch_ids[0]}.json"
    try:
        # Same-directory hard-link creation is atomic and no-replace on both
        # Windows and POSIX. `os.rename` silently replaces on POSIX.
        os.link(staged_response_path, target)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing response: {target}") from exc
    except OSError as exc:
        raise ValueError(
            f"atomic no-replace response publication failed: {target}"
        ) from exc
    try:
        staged_response_path.unlink()
    except OSError as exc:
        raise ValueError(
            "response final was published but staged-response cleanup failed: "
            f"{staged_response_path}"
        ) from exc
    return {
        "status": "SEMANTIC_BATCH_RESPONSE_PUBLISHED",
        **receipt,
        "response_path": str(target),
        "model_api_calls": 0,
    }


def reserve_evidence_selection_provider_attempt(
    *, attempt_root: Path, attempt_id: str
) -> dict[str, Any]:
    """Atomically reserve one immutable external-model attempt directory."""
    reserved = reserve_provider_attempt(attempt_root=attempt_root, attempt_id=attempt_id)
    return {
        "status": "PHASE_A_EVIDENCE_PROVIDER_ATTEMPT_RESERVED",
        **reserved,
    }


def publish_evidence_selection_provider_attempt(
    *,
    attempt_dir: Path,
    response_dir: Path,
    canonical_response_name: str,
    batch_manifest_path: Path | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Preserve attempt usage and atomically publish one response without replace."""
    if (batch_manifest_path is None) != (batch_id is None):
        raise ValueError("batch manifest and batch_id must be supplied together")

    def _validate(response: dict[str, Any]) -> Mapping[str, Any]:
        if batch_manifest_path is None or batch_id is None:
            return {}
        batch_manifest = _load_object(batch_manifest_path)
        selection_manifest = batch_manifest.get("selection_manifest")
        if not isinstance(selection_manifest, dict):
            raise ValueError("selection batch manifest is missing its selection manifest")
        return validate_evidence_selection_batch_response(
            batch_manifest,
            load_selection_sources(selection_manifest),
            batch_id=batch_id,
            response=response,
        )

    published = publish_provider_attempt(
        attempt_dir=attempt_dir,
        response_dir=response_dir,
        canonical_response_name=canonical_response_name,
        usage_schema_version="phase_a_evidence_provider_attempt_usage_v1",
        validate_response=_validate,
    )
    return {
        "status": "PHASE_A_EVIDENCE_PROVIDER_ATTEMPT_PUBLISHED",
        **published,
    }


def validate_reconciliation_response_file(
    *,
    bundle_path: Path,
    stage_path: Path,
    response_path: Path,
    receipt_out: Path | None,
) -> dict[str, Any]:
    receipt = validate_one_reconciliation_response(
        _load_object(bundle_path),
        _load_object(stage_path),
        _load_object(response_path),
    )
    if receipt_out is not None:
        _write_json(receipt_out, receipt)
    return {
        "status": "SEMANTIC_RECONCILIATION_RESPONSE_VALID",
        **receipt,
        "receipt_out": str(receipt_out) if receipt_out is not None else None,
        "model_api_calls": 0,
    }


def semantic_run_status(
    *, bundle_path: Path, response_dir: Path
) -> dict[str, Any]:
    responses = []
    if response_dir.exists():
        for path in sorted(response_dir.glob("*.json")):
            try:
                responses.append(_load_object(path))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                responses.append({"batch_id": path.stem, "invalid_file_error": str(exc)})
        # A staged artifact is work in flight, not accepted output. Report it
        # rather than letting an interrupted publish look like missing work.
        for path in sorted(response_dir.glob("*.json.tmp")):
            responses.append(
                {"batch_id": path.name[: -len(".json.tmp")], "staged_artifact": True}
            )
    return run_status(bundle=_load_object(bundle_path), batch_responses=responses)


def submit_batches(
    *, bundle_path: Path, response_paths: list[Path], compiled_out: Path
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    responses = [_load_object(path) for path in response_paths]
    compiled = validate_batch_responses(bundle, responses)
    _write_json(compiled_out, compiled)
    return {
        "status": "SEMANTIC_RECONCILIATION_REQUIRED",
        "compilation_sha256": compiled["compilation_sha256"],
        "semantic_unit_count": len(compiled["semantic_units"]),
        "compiled_out": str(compiled_out),
        "model_api_calls": 0,
    }


def prepare_row_verification_run(
    *,
    bundle_path: Path,
    compiled_path: Path,
    stage_out: Path,
    prompt_dir: Path,
    max_prompt_bytes: int | None = None,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compiled = _load_object(compiled_path)
    stage, prompts = prepare_row_verification(
        bundle, compiled, max_prompt_bytes=max_prompt_bytes
    )
    if prompt_dir.exists():
        raise ValueError(
            f"refusing to write into existing verification prompt directory: {prompt_dir}"
        )
    _write_json(stage_out, stage)
    prompt_dir.mkdir(parents=True)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
    return {
        "status": "SEMANTIC_ROW_VERIFICATION_REQUIRED",
        "stage_sha256": stage["stage_sha256"],
        "input_compilation_sha256": stage["input_compilation_sha256"],
        "claim_bearing_count": stage["coverage_proof"]["claim_bearing_count"],
        "verification_batch_count": len(prompts),
        "largest_rendered_prompt_bytes": max(
            (row["prompt_utf8_bytes"] for row in prompts), default=0
        ),
        "stage_out": str(stage_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
    }


def submit_row_verification_run(
    *,
    bundle_path: Path,
    compiled_path: Path,
    stage_path: Path,
    response_paths: list[Path],
    verified_out: Path,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compiled = _load_object(compiled_path)
    stage = _load_object(stage_path)
    responses = [_load_object(path) for path in response_paths]
    verified = apply_row_verification(bundle, compiled, stage, responses)
    _write_json(verified_out, verified)
    manifest = verified["row_verification_manifest"]
    return {
        "status": "SEMANTIC_ROW_VERIFICATION_APPLIED",
        "compilation_sha256": verified["compilation_sha256"],
        "input_compilation_sha256": manifest["input_compilation_sha256"],
        "decision_counts": manifest["decision_counts"],
        "semantic_unit_count": len(verified["semantic_units"]),
        "verified_out": str(verified_out),
        "model_api_calls": 0,
    }


def prepare_targeted_benchmark_audit_run(
    *,
    bundle_path: Path,
    verified_path: Path,
    selection_path: Path,
    benchmark_path: Path,
    row_verification_stage_path: Path,
    stage_out: Path,
    shared_frame_out: Path,
    prompt_manifest_out: Path,
    assignment_manifest_out: Path,
    prompt_dir: Path,
    max_prompt_bytes: int | None = None,
    worker_count: int = 6,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    verified = _load_object(verified_path)
    selection = _load_object(selection_path)
    benchmark = _load_object(benchmark_path)
    row_stage = _load_object(row_verification_stage_path)
    stage, shared_frame, prompts, prompt_manifest, assignments = (
        prepare_targeted_benchmark_audit(
            bundle,
            verified,
            selection,
            benchmark,
            row_stage,
            input_raw_sha256={
                "selection": hash_file(selection_path),
                "benchmark": hash_file(benchmark_path),
                "bundle": hash_file(bundle_path),
                "row_verification_stage": hash_file(row_verification_stage_path),
                "verified_compilation": hash_file(verified_path),
            },
            max_prompt_bytes=max_prompt_bytes,
            worker_count=worker_count,
        )
    )
    output_files = [
        stage_out,
        shared_frame_out,
        prompt_manifest_out,
        assignment_manifest_out,
    ]
    existing = [str(path) for path in output_files if path.exists()]
    if prompt_dir.exists():
        existing.append(str(prompt_dir))
    if existing:
        raise ValueError(
            "refusing to overwrite targeted audit outputs: " + ", ".join(existing)
        )
    _write_json(stage_out, stage)
    _write_new(shared_frame_out, shared_frame.encode("utf-8") + b"\n")
    _write_json(prompt_manifest_out, prompt_manifest)
    _write_json(assignment_manifest_out, assignments)
    prompt_dir.mkdir(parents=True)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
    return {
        "status": "TARGETED_BENCHMARK_AUDIT_REQUIRED",
        "stage_sha256": stage["stage_sha256"],
        "prompt_manifest_sha256": prompt_manifest["manifest_sha256"],
        "assignment_manifest_sha256": assignments["manifest_sha256"],
        "selected_batch_count": stage["coverage_proof"]["selected_batch_count"],
        "selected_evidence_count": stage["coverage_proof"]["selected_evidence_count"],
        "worker_count": worker_count,
        "largest_payload_bytes": max(
            (row["prompt_utf8_bytes"] for row in prompts), default=0
        ),
        "model_api_calls": 0,
    }


def submit_targeted_benchmark_audit_run(
    *,
    stage_path: Path,
    prompt_manifest_path: Path,
    response_paths: list[Path],
    audit_out: Path,
) -> dict[str, Any]:
    result = validate_targeted_benchmark_audit(
        _load_object(stage_path),
        _load_object(prompt_manifest_path),
        [_load_object(path) for path in response_paths],
    )
    _write_json(audit_out, result)
    return {
        "status": "TARGETED_BENCHMARK_AUDIT_APPLIED",
        "result_sha256": result["result_sha256"],
        "decision_counts": result["decision_counts"],
        "repair_evidence_count": len(result["repair_evidence_ids"]),
        "audit_out": str(audit_out),
        "model_api_calls": 0,
    }


def validate_relation_closure_response_file(
    *,
    bundle_path: Path,
    stage_path: Path,
    response_path: Path,
    receipt_out: Path | None,
) -> dict[str, Any]:
    receipt = validate_relation_closure_stage(
        _load_object(bundle_path),
        _load_object(stage_path),
        [_load_object(response_path)],
        require_all=False,
    )
    if receipt_out is not None:
        _write_json(receipt_out, receipt)
    return {
        "status": "SEMANTIC_RELATION_CLOSURE_RESPONSE_VALID",
        **receipt,
        "receipt_out": str(receipt_out) if receipt_out is not None else None,
        "model_api_calls": 0,
    }


def prepare_row_repair_run(
    *,
    bundle_path: Path,
    verified_path: Path,
    evidence_ids: list[str],
    stage_out: Path,
    prompt_dir: Path,
    max_prompt_bytes: int | None = None,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    verified = _load_object(verified_path)
    stage, prompts = prepare_row_repair(
        bundle,
        verified,
        evidence_ids=evidence_ids,
        max_prompt_bytes=max_prompt_bytes,
    )
    if prompt_dir.exists():
        raise ValueError(f"refusing to write into existing repair prompt directory: {prompt_dir}")
    _write_json(stage_out, stage)
    prompt_dir.mkdir(parents=True)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
    return {
        "status": "SEMANTIC_ROW_REPAIR_REQUIRED",
        "stage_sha256": stage["stage_sha256"],
        "input_verified_compilation_sha256": stage[
            "input_verified_compilation_sha256"
        ],
        "selected_evidence_count": len(stage["selected_evidence_ids"]),
        "repair_batch_count": len(prompts),
        "stage_out": str(stage_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
    }


def submit_row_repair_run(
    *,
    bundle_path: Path,
    verified_path: Path,
    stage_path: Path,
    response_paths: list[Path],
    repaired_out: Path,
) -> dict[str, Any]:
    repaired = apply_row_repair(
        _load_object(bundle_path),
        _load_object(verified_path),
        _load_object(stage_path),
        [_load_object(path) for path in response_paths],
    )
    _write_json(repaired_out, repaired)
    manifest = repaired["row_repair_manifest"]
    return {
        "status": "SEMANTIC_ROW_REPAIR_APPLIED",
        "compilation_sha256": repaired["compilation_sha256"],
        "input_verified_compilation_sha256": manifest[
            "input_verified_compilation_sha256"
        ],
        "selected_evidence_count": len(manifest["selected_evidence_ids"]),
        "decision_counts": manifest["decision_counts"],
        "repaired_out": str(repaired_out),
        "model_api_calls": 0,
    }


def prepare_reconciliation(
    *, bundle_path: Path, compiled_path: Path, prompt_out: Path
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compiled = _load_object(compiled_path)
    prompt = build_reconciliation_prompt(bundle, compiled)
    _write_new(prompt_out, prompt.encode("utf-8") + b"\n")
    return {
        "status": "SEMANTIC_RECONCILIATION_JUDGMENT_REQUIRED",
        "bundle_sha256": bundle["bundle_sha256"],
        "compilation_sha256": compiled["compilation_sha256"],
        "prompt_out": str(prompt_out),
        "model_api_calls": 0,
    }


def finalize(
    *, bundle_path: Path, compiled_path: Path, response_path: Path, view_out: Path
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compiled = _load_object(compiled_path)
    response = _load_object(response_path)
    view = finalize_view(bundle, compiled, response)
    _write_json(view_out, view)
    return {
        "status": "SEMANTIC_EVIDENCE_INTEGRATION_COMPLETE",
        "view_sha256": view["view_sha256"],
        "proposition_count": len(view["propositions"]),
        "accounted_evidence_unit_count": view["coverage"]["accounted_evidence_unit_count"],
        "view_out": str(view_out),
        "model_api_calls": 0,
    }


def prepare_reconciliation_level(
    *,
    bundle_path: Path,
    compilation_path: Path,
    stage_out: Path,
    prompt_dir: Path,
    reconciliation_policy_version: str | None = None,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compilation = _load_object(compilation_path)
    stage, prompts = prepare_reconciliation_stage(
        bundle,
        compilation,
        reconciliation_policy_version=reconciliation_policy_version,
    )
    if prompt_dir.exists():
        raise ValueError(f"refusing to write into existing prompt directory: {prompt_dir}")
    _write_json(stage_out, stage)
    prompt_dir.mkdir(parents=True)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
    return {
        "status": "SEMANTIC_RECONCILIATION_LEVEL_JUDGMENT_REQUIRED",
        "stage_sha256": stage["stage_sha256"],
        "level": stage["level"],
        "batch_count": len(prompts),
        "candidate_count": len(stage["candidates"]),
        "reconciliation_policy_version": stage.get("reconciliation_policy_version"),
        "reconciliation_mode": stage.get("reconciliation_mode"),
        "largest_rendered_prompt_bytes": max(
            row["prompt_utf8_bytes"] for row in prompts
        ),
        "stage_out": str(stage_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
    }


def submit_reconciliation_level(
    *,
    bundle_path: Path,
    stage_path: Path,
    response_paths: list[Path],
    compilation_out: Path,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    stage = _load_object(stage_path)
    responses = [_load_object(path) for path in response_paths]
    compilation = validate_reconciliation_stage(bundle, stage, responses)
    _write_json(compilation_out, compilation)
    terminal = is_terminal_reconciliation_compilation(compilation)
    return {
        "status": (
            "SEMANTIC_FINALIZATION_READY"
            if terminal
            else "SEMANTIC_RECONCILIATION_LEVEL_REQUIRED"
        ),
        "node_compilation_sha256": compilation["node_compilation_sha256"],
        "level": compilation["level"],
        "node_count": len(compilation["semantic_nodes"]),
        "terminal": terminal,
        "compilation_out": str(compilation_out),
        "model_api_calls": 0,
    }


def prepare_relation_closure_run(
    *,
    bundle_path: Path,
    node_compilation_path: Path,
    stage_out: Path,
    prompt_dir: Path,
    max_prompt_bytes: int | None = None,
) -> dict[str, Any]:
    stage, prompts = prepare_relation_closure_stage(
        _load_object(bundle_path),
        _load_object(node_compilation_path),
        max_prompt_bytes=max_prompt_bytes,
    )
    if prompt_dir.exists():
        raise ValueError(f"refusing to write into existing closure prompt directory: {prompt_dir}")
    _write_json(stage_out, stage)
    prompt_dir.mkdir(parents=True)
    for row in prompts:
        _write_new(
            prompt_dir / f"{row['batch_id']}.md",
            row["prompt"].encode("utf-8") + b"\n",
        )
    return {
        "status": "SEMANTIC_RELATION_CLOSURE_REQUIRED",
        "stage_sha256": stage["stage_sha256"],
        "candidate_count": len(stage["candidates"]),
        "batch_count": len(prompts),
        "largest_rendered_prompt_bytes": max(
            (row["prompt_utf8_bytes"] for row in prompts), default=0
        ),
        "stage_out": str(stage_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
    }


def submit_relation_closure_run(
    *,
    bundle_path: Path,
    stage_path: Path,
    response_paths: list[Path],
    compilation_out: Path,
) -> dict[str, Any]:
    compilation = validate_relation_closure_stage(
        _load_object(bundle_path),
        _load_object(stage_path),
        [_load_object(path) for path in response_paths],
    )
    _write_json(compilation_out, compilation)
    terminal = is_terminal_reconciliation_compilation(compilation)
    return {
        "status": (
            "SEMANTIC_FINALIZATION_READY"
            if terminal
            else "SEMANTIC_RELATION_CLOSURE_REQUIRED"
        ),
        "node_compilation_sha256": compilation["node_compilation_sha256"],
        "node_count": len(compilation["semantic_nodes"]),
        "terminal": terminal,
        "coverage": compilation["relation_coverage"],
        "compilation_out": str(compilation_out),
        "model_api_calls": 0,
    }


def finalize_v3(
    *,
    bundle_path: Path,
    batch_compilation_path: Path,
    node_compilation_path: Path,
    view_out: Path,
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    batch_compilation = _load_object(batch_compilation_path)
    node_compilation = _load_object(node_compilation_path)
    view = finalize_v3_view(bundle, batch_compilation, node_compilation)
    _write_json(view_out, view)
    return {
        "status": "SEMANTIC_EVIDENCE_INTEGRATION_COMPLETE",
        "view_sha256": view["view_sha256"],
        "proposition_count": len(view["propositions"]),
        "captured_item_count": view["coverage"]["captured_item_count"],
        "accounted_item_count": view["coverage"]["accounted_item_count"],
        "view_out": str(view_out),
        "model_api_calls": 0,
    }


def migrate_repaired_terminal_run(
    *,
    bundle_path: Path,
    source_batch_compilation_path: Path,
    repaired_batch_compilation_path: Path,
    source_node_compilation_path: Path,
    compilation_out: Path,
    manifest_out: Path,
) -> dict[str, Any]:
    paths = {
        "bundle": bundle_path,
        "source_batch_compilation": source_batch_compilation_path,
        "repaired_batch_compilation": repaired_batch_compilation_path,
        "source_node_compilation": source_node_compilation_path,
    }
    compilation = migrate_repaired_terminal_compilation(
        _load_object(bundle_path),
        _load_object(source_batch_compilation_path),
        _load_object(repaired_batch_compilation_path),
        _load_object(source_node_compilation_path),
        raw_file_sha256s={name: hash_file(path) for name, path in paths.items()},
    )
    _write_json(compilation_out, compilation)
    _write_json(manifest_out, compilation["terminal_repair_migration_manifest"])
    manifest = compilation["terminal_repair_migration_manifest"]
    return {
        "status": "SEMANTIC_TERMINAL_REPAIR_MIGRATION_COMPLETE",
        "node_compilation_sha256": compilation["node_compilation_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "source_node_count": manifest["source_node_count"],
        "output_node_count": manifest["output_node_count"],
        "reused_node_count": len(manifest["reused_source_semantic_node_refs"]),
        "invalidated_node_count": len(
            manifest["invalidated_source_semantic_node_refs"]
        ),
        "coalesced_group_count": len(manifest["coalesced_node_groups"]),
        "compilation_out": str(compilation_out),
        "manifest_out": str(manifest_out),
        "model_api_calls": 0,
    }


def finalize_relation_closed(
    *,
    bundle_path: Path,
    batch_compilation_path: Path,
    relation_compilation_path: Path,
    view_out: Path,
) -> dict[str, Any]:
    view = finalize_relation_closed_view(
        _load_object(bundle_path),
        _load_object(batch_compilation_path),
        _load_object(relation_compilation_path),
    )
    _write_json(view_out, view)
    return {
        "status": "SEMANTIC_EVIDENCE_INTEGRATION_COMPLETE",
        "view_sha256": view["view_sha256"],
        "proposition_count": len(view["propositions"]),
        "captured_item_count": view["coverage"]["captured_item_count"],
        "accounted_item_count": view["coverage"]["accounted_item_count"],
        "view_out": str(view_out),
        "model_api_calls": 0,
    }


def project_evidence_packet_run(
    *,
    view_path: Path,
    bundle_path: Path,
    batch_compilation_path: Path,
    node_compilation_path: Path,
    axis_ids: list[str],
    proposition_ids: list[str],
    packet_out: Path,
    packet_version: str = "v3",
) -> dict[str, Any]:
    view = _load_object(view_path)
    bundle = _load_object(bundle_path)
    batch_compilation = _load_object(batch_compilation_path)
    node_compilation = _load_object(node_compilation_path)
    if packet_version not in {"v1", "v2", "v3"}:
        raise ValueError("packet_version must be v1, v2, or v3")
    projector = {
        "v1": project_evidence_packet_v1,
        "v2": project_evidence_packet_v2,
        "v3": project_evidence_packet,
    }[packet_version]
    packet = projector(
        view,
        bundle,
        batch_compilation,
        node_compilation,
        axis_ids=axis_ids,
        proposition_ids=proposition_ids,
    )
    _write_json(packet_out, packet)
    return {
        "status": "PHASE_A_EVIDENCE_PACKET_READY",
        "packet_schema_version": packet["schema_version"],
        "packet_sha256": packet["packet_sha256"],
        "selected_proposition_count": packet["selection_coverage"][
            "selected_proposition_count"
        ],
        "returned_evidence_item_count": packet["selection_coverage"][
            "returned_evidence_item_count"
        ],
        "packet_out": str(packet_out),
        "model_api_calls": 0,
    }


def prepare_evidence_consumer_batch_run(
    *,
    spec_path: Path,
    prompt_out: Path,
    response_schema_out: Path,
    manifest_out: Path,
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    if spec.get("schema_version") != "phase_a_evidence_consumer_batch_spec_v1":
        raise ValueError("unsupported evidence consumer batch spec")
    rows = spec.get("cases")
    if not isinstance(rows, list):
        raise ValueError("evidence consumer batch cases must be a list")
    cases = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("evidence consumer batch case must be an object")
        packet_path = (spec_path.parent / Path(row["packet_path"])).resolve(strict=True)
        selectors_path = (spec_path.parent / Path(row["selectors_path"])).resolve(strict=True)
        cases.append(
            {
                "case_id": row.get("case_id"),
                "packet_path": packet_path,
                "selectors_path": selectors_path,
                "packet": _load_object(packet_path),
                "selectors": _load_object(selectors_path),
            }
        )
    prompt, response_schema, manifest = prepare_decision_batch(cases)
    for output in (prompt_out, response_schema_out, manifest_out):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(prompt_out, prompt.encode("utf-8"))
    _write_json(response_schema_out, response_schema)
    _write_json(manifest_out, manifest)
    return {
        "status": "PHASE_A_EVIDENCE_CONSUMER_BATCH_READY",
        "case_count": len(cases),
        "case_order": manifest["case_order"],
        "manifest_sha256": manifest["manifest_sha256"],
        "prompt_out": str(prompt_out),
        "response_schema_out": str(response_schema_out),
        "manifest_out": str(manifest_out),
        "model_api_calls": 0,
    }


def finalize_evidence_consumer_batch_run(
    *,
    manifest_path: Path,
    response_path: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    manifest = _load_object(manifest_path)
    cases = load_prepared_cases(manifest)
    response = _load_object(response_path)
    artifacts = finalize_decision_batch(cases, response)
    output_paths = [artifact_dir / f"{artifact['case_id']}.json" for artifact in artifacts]
    existing = [str(path) for path in output_paths if path.exists()]
    if existing:
        raise ValueError(f"refusing to overwrite existing output: {existing}")
    for path, artifact in zip(output_paths, artifacts, strict=True):
        _write_json(path, artifact)
    return {
        "status": "PHASE_A_EVIDENCE_CONSUMER_BATCH_COMPLETE",
        "case_count": len(artifacts),
        "case_order": [artifact["case_id"] for artifact in artifacts],
        "artifact_paths": [str(path) for path in output_paths],
        "artifact_sha256": [hash_file(path) for path in output_paths],
        "model_api_calls": 0,
    }


def build_customer_pull_point_frontier_run(
    *, spec_path: Path, frontier_out: Path
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    packet_path = (spec_path.parent / Path(spec["packet_path"])).resolve(strict=True)
    protected = spec.get("protected_point_ids") or {}
    frontier = build_customer_pull_point_frontier(
        _load_object(packet_path),
        frontier_id=spec["frontier_id"],
        business_question=spec["business_question"],
        subject_product_ids=spec["subject_product_ids"],
        source_id=spec.get("source_id", "full-corpus"),
        protected_point_ids=protected,
    )
    if frontier_out.exists():
        raise ValueError(f"refusing to overwrite existing output: {frontier_out}")
    _write_json(frontier_out, frontier)
    return {
        "status": "PHASE_A_CUSTOMER_PULL_POINT_FRONTIER_READY",
        "retailer_first_count": frontier["accounting"]["retailer_first_count"],
        "community_discovery_count": frontier["accounting"][
            "community_discovery_count"
        ],
        "nonpromoted_count": frontier["accounting"]["nonpromoted_count"],
        "frontier_sha256": frontier["frontier_sha256"],
        "model_api_calls": 0,
    }


def materialize_customer_pull_point_selection_spec_run(
    *,
    frontier_path: Path,
    packet_path: Path,
    bundle_path: Path,
    proposition_id: str,
    spec_out: Path,
    point_actor_scope: Mapping[str, Any],
    rejected_frontier_semantic_refs: Sequence[str] = (),
) -> dict[str, Any]:
    frontier = _load_object(frontier_path)
    packet = _load_object(packet_path)
    verify_customer_pull_point_frontier(frontier, packet)
    spec = selection_spec_from_customer_pull_frontier(
        frontier,
        packet,
        proposition_id,
        point_actor_scope=point_actor_scope,
        frontier_relation_rejections=[
            {
                "source_id": frontier["source_id"],
                "semantic_unit_ref": semantic_ref,
                "cause": "literal_source_does_not_state_bounded_relation",
            }
            for semantic_ref in rejected_frontier_semantic_refs
        ],
    )
    spec["sources"] = [
        {
            "source_id": frontier["source_id"],
            "packet_path": str(packet_path.resolve(strict=True)),
            "bundle_path": str(bundle_path.resolve(strict=True)),
        }
    ]
    if spec_out.exists():
        raise ValueError(f"refusing to overwrite existing output: {spec_out}")
    _write_json(spec_out, spec)
    return {
        "status": "PHASE_A_CUSTOMER_PULL_POINT_SELECTION_SPEC_READY",
        "selection_id": spec["selection_id"],
        "frontier_sha256": frontier["frontier_sha256"],
        "truth_group_cap": spec["truth_group_cap"],
        "rejected_frontier_relation_count": len(rejected_frontier_semantic_refs),
        "model_api_calls": 0,
    }


def _selection_sources_from_spec(
    spec_path: Path, spec: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = spec.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("evidence selection sources must be a nonempty list")
    sources = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("evidence selection source must be an object")
        packet_path = (spec_path.parent / Path(row["packet_path"])).resolve(strict=True)
        bundle_path = (spec_path.parent / Path(row["bundle_path"])).resolve(strict=True)
        sources.append(
            {
                "source_id": row["source_id"],
                "packet_path": packet_path,
                "bundle_path": bundle_path,
                "packet": _load_object(packet_path),
                "bundle": _load_object(bundle_path),
            }
        )
    return sources


def prepare_evidence_selection_run(
    *,
    spec_path: Path,
    prompt_out: Path,
    response_schema_out: Path,
    manifest_out: Path,
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    if spec.get("schema_version") != SELECTION_SPEC_VERSION:
        raise EvidenceConsumerError("point_actor_scope", "fresh authoring requires selection spec v2; frozen v1 replay uses finalization")
    sources = _selection_sources_from_spec(spec_path, spec)
    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    for output in (prompt_out, response_schema_out, manifest_out):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(prompt_out, prompt.encode("utf-8"))
    _write_json(response_schema_out, schema)
    _write_json(manifest_out, manifest)
    return {
        "status": "PHASE_A_EVIDENCE_SELECTION_RELATIONS_READY",
        "candidate_count": manifest["candidate_count"],
        "candidate_inventory_sha256": manifest["candidate_inventory_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def prepare_evidence_selection_batches_run(
    *,
    spec_path: Path,
    batch_size: int,
    batch_dir: Path,
    batch_manifest_out: Path,
) -> dict[str, Any]:
    spec = _load_object(spec_path)
    if spec.get("schema_version") != SELECTION_SPEC_VERSION:
        raise EvidenceConsumerError("point_actor_scope", "fresh authoring requires selection spec v2; frozen v1 replay uses finalization")
    sources = _selection_sources_from_spec(spec_path, spec)
    batch_manifest, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=batch_size
    )
    output_paths = [batch_manifest_out]
    for batch in batch_manifest["batches"]:
        output_paths.extend(
            [
                batch_dir / f"{batch['batch_id']}_prompt.txt",
                batch_dir / f"{batch['batch_id']}_schema.json",
            ]
        )
    existing = [str(path) for path in output_paths if path.exists()]
    if existing:
        raise ValueError(f"refusing to overwrite existing output: {existing}")
    for batch, (prompt, schema) in zip(
        batch_manifest["batches"], prompts_and_schemas, strict=True
    ):
        _write_new(
            batch_dir / f"{batch['batch_id']}_prompt.txt", prompt.encode("utf-8")
        )
        _write_json(batch_dir / f"{batch['batch_id']}_schema.json", schema)
    _write_json(batch_manifest_out, batch_manifest)
    return {
        "status": "PHASE_A_EVIDENCE_SELECTION_RELATION_BATCHES_READY",
        "candidate_count": batch_manifest["candidate_count"],
        "batch_count": len(batch_manifest["batches"]),
        "batch_manifest_sha256": batch_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def finalize_evidence_selection_relations_run(
    *,
    manifest_path: Path,
    response_path: Path,
    quote_prompt_out: Path,
    quote_schema_out: Path,
    quote_manifest_out: Path,
    confirmation_prompt_out: Path,
    confirmation_schema_out: Path,
    confirmation_manifest_out: Path,
) -> dict[str, Any]:
    manifest = _load_object(manifest_path)
    sources = load_selection_sources(manifest)
    response = _load_object(response_path)
    prompt, schema, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, response
    )
    confirmation_prompt, confirmation_schema, confirmation_manifest = (
        prepare_selected_relation_confirmation(quote_manifest)
    )
    for output in (
        quote_prompt_out,
        quote_schema_out,
        quote_manifest_out,
        confirmation_prompt_out,
        confirmation_schema_out,
        confirmation_manifest_out,
    ):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(quote_prompt_out, prompt.encode("utf-8"))
    _write_json(quote_schema_out, schema)
    _write_json(quote_manifest_out, quote_manifest)
    _write_new(confirmation_prompt_out, confirmation_prompt.encode("utf-8"))
    _write_json(confirmation_schema_out, confirmation_schema)
    _write_json(confirmation_manifest_out, confirmation_manifest)
    return {
        "status": "PHASE_A_EVIDENCE_SELECTION_QUOTES_AND_CONFIRMATION_READY",
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "truth_group_count": len(
            {
                row["origin_group_id"]
                for row in quote_manifest["selected_rows"]
                if row["layer"] == "truth_support"
            }
        ),
        "influence_group_count": len(
            {
                row["origin_group_id"]
                for row in quote_manifest["selected_rows"]
                if row["layer"] == "influence_context"
            }
        ),
        "manifest_sha256": quote_manifest["manifest_sha256"],
        "confirmation_manifest_sha256": confirmation_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def prepare_preselection_relation_confirmation_run(
    *,
    selection_manifest_path: Path,
    first_response_path: Path,
    prompt_out: Path,
    response_schema_out: Path,
    confirmation_manifest_out: Path,
) -> dict[str, Any]:
    selection_manifest = _load_object(selection_manifest_path)
    sources = load_selection_sources(selection_manifest)
    prompt, schema, confirmation_manifest = prepare_preselection_relation_confirmation(
        selection_manifest, sources, _load_object(first_response_path)
    )
    for output in (prompt_out, response_schema_out, confirmation_manifest_out):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(prompt_out, prompt.encode("utf-8"))
    _write_json(response_schema_out, schema)
    _write_json(confirmation_manifest_out, confirmation_manifest)
    return {
        "status": "PHASE_A_PRESELECTION_RELATION_CONFIRMATION_READY",
        "confirmation_candidate_count": len(
            confirmation_manifest["confirmation_candidate_ids"]
        ),
        "confirmation_manifest_sha256": confirmation_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def finalize_preselection_relation_confirmation_run(
    *,
    selection_manifest_path: Path,
    first_response_path: Path,
    confirmation_manifest_path: Path,
    confirmation_response_path: Path,
    quote_prompt_out: Path,
    quote_schema_out: Path,
    quote_manifest_out: Path,
) -> dict[str, Any]:
    selection_manifest = _load_object(selection_manifest_path)
    sources = load_selection_sources(selection_manifest)
    prompt, schema, quote_manifest = (
        finalize_preselection_relation_confirmation_prepare_quotes(
            selection_manifest,
            sources,
            _load_object(first_response_path),
            _load_object(confirmation_manifest_path),
            _load_object(confirmation_response_path),
        )
    )
    for output in (quote_prompt_out, quote_schema_out, quote_manifest_out):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(quote_prompt_out, prompt.encode("utf-8"))
    _write_json(quote_schema_out, schema)
    _write_json(quote_manifest_out, quote_manifest)
    return {
        "status": "PHASE_A_CONFIRMED_EVIDENCE_SELECTION_QUOTES_READY",
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "selected_row_count": len(quote_manifest["selected_rows"]),
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def finalize_evidence_selection_batches_run(
    *,
    batch_manifest_path: Path,
    response_dir: Path,
    quote_prompt_out: Path,
    quote_schema_out: Path,
    quote_manifest_out: Path,
    confirmation_prompt_out: Path,
    confirmation_schema_out: Path,
    confirmation_manifest_out: Path,
) -> dict[str, Any]:
    batch_manifest = _load_object(batch_manifest_path)
    selection_manifest = batch_manifest.get("selection_manifest")
    if not isinstance(selection_manifest, dict):
        raise ValueError("selection batch manifest is missing its selection manifest")
    sources = load_selection_sources(selection_manifest)
    responses = {
        batch["batch_id"]: _load_object(
            response_dir / f"{batch['batch_id']}_response.json"
        )
        for batch in batch_manifest.get("batches", [])
    }
    prompt, schema, quote_manifest = finalize_batched_relations_prepare_quotes(
        batch_manifest, sources, responses
    )
    confirmation_prompt, confirmation_schema, confirmation_manifest = (
        prepare_selected_relation_confirmation(quote_manifest)
    )
    for output in (
        quote_prompt_out,
        quote_schema_out,
        quote_manifest_out,
        confirmation_prompt_out,
        confirmation_schema_out,
        confirmation_manifest_out,
    ):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(quote_prompt_out, prompt.encode("utf-8"))
    _write_json(quote_schema_out, schema)
    _write_json(quote_manifest_out, quote_manifest)
    _write_new(confirmation_prompt_out, confirmation_prompt.encode("utf-8"))
    _write_json(confirmation_schema_out, confirmation_schema)
    _write_json(confirmation_manifest_out, confirmation_manifest)
    return {
        "status": "PHASE_A_EVIDENCE_SELECTION_QUOTES_AND_CONFIRMATION_READY",
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "batch_count": len(batch_manifest["batches"]),
        "truth_group_count": len(
            {
                row["origin_group_id"]
                for row in quote_manifest["selected_rows"]
                if row["layer"] == "truth_support"
            }
        ),
        "influence_group_count": len(
            {
                row["origin_group_id"]
                for row in quote_manifest["selected_rows"]
                if row["layer"] == "influence_context"
            }
        ),
        "manifest_sha256": quote_manifest["manifest_sha256"],
        "confirmation_manifest_sha256": confirmation_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def _load_relation_batch_responses(
    batch_manifest: Mapping[str, Any], response_dir: Path
) -> dict[str, dict[str, Any]]:
    return {
        batch["batch_id"]: _load_object(
            response_dir / f"{batch['batch_id']}_response.json"
        )
        for batch in batch_manifest.get("batches", [])
    }


def prepare_batched_preselection_relation_confirmation_run(
    *,
    batch_manifest_path: Path,
    response_dir: Path,
    batch_size: int,
    confirmation_batch_dir: Path,
    confirmation_batch_manifest_out: Path,
) -> dict[str, Any]:
    batch_manifest = _load_object(batch_manifest_path)
    selection_manifest = batch_manifest.get("selection_manifest")
    if not isinstance(selection_manifest, dict):
        raise ValueError("selection batch manifest is missing its selection manifest")
    sources = load_selection_sources(selection_manifest)
    responses = _load_relation_batch_responses(batch_manifest, response_dir)
    confirmation_batch_manifest, prompts_and_schemas = (
        prepare_batched_preselection_relation_confirmations(
            batch_manifest, sources, responses, batch_size=batch_size
        )
    )
    output_paths = [confirmation_batch_manifest_out]
    for batch in confirmation_batch_manifest["batches"]:
        output_paths.extend(
            [
                confirmation_batch_dir / f"{batch['batch_id']}_prompt.txt",
                confirmation_batch_dir / f"{batch['batch_id']}_schema.json",
            ]
        )
    existing = [str(path) for path in output_paths if path.exists()]
    if existing:
        raise ValueError(f"refusing to overwrite existing output: {existing}")
    for batch, (prompt, schema) in zip(
        confirmation_batch_manifest["batches"], prompts_and_schemas, strict=True
    ):
        _write_new(
            confirmation_batch_dir / f"{batch['batch_id']}_prompt.txt",
            prompt.encode("utf-8"),
        )
        _write_json(
            confirmation_batch_dir / f"{batch['batch_id']}_schema.json", schema
        )
    _write_json(confirmation_batch_manifest_out, confirmation_batch_manifest)
    return {
        "status": "PHASE_A_PRESELECTION_RELATION_CONFIRMATION_BATCHES_READY",
        "candidate_count": batch_manifest["candidate_count"],
        "relation_batch_count": len(batch_manifest["batches"]),
        "confirmation_candidate_count": confirmation_batch_manifest[
            "confirmation_candidate_count"
        ],
        "confirmation_batch_count": len(confirmation_batch_manifest["batches"]),
        "confirmation_batch_manifest_sha256": confirmation_batch_manifest[
            "manifest_sha256"
        ],
        "model_api_calls": 0,
    }


def finalize_batched_preselection_relation_confirmation_run(
    *,
    batch_manifest_path: Path,
    response_dir: Path,
    confirmation_batch_manifest_path: Path,
    confirmation_response_dir: Path,
    quote_prompt_out: Path,
    quote_schema_out: Path,
    quote_manifest_out: Path,
) -> dict[str, Any]:
    batch_manifest = _load_object(batch_manifest_path)
    selection_manifest = batch_manifest.get("selection_manifest")
    if not isinstance(selection_manifest, dict):
        raise ValueError("selection batch manifest is missing its selection manifest")
    sources = load_selection_sources(selection_manifest)
    responses = _load_relation_batch_responses(batch_manifest, response_dir)
    confirmation_batch_manifest = _load_object(confirmation_batch_manifest_path)
    confirmation_batch_responses = {
        batch["batch_id"]: _load_object(
            confirmation_response_dir / f"{batch['batch_id']}_response.json"
        )
        for batch in confirmation_batch_manifest.get("batches", [])
    }
    prompt, schema, quote_manifest = (
        finalize_batched_preselection_relation_confirmations_prepare_quotes(
            batch_manifest,
            sources,
            responses,
            confirmation_batch_manifest,
            confirmation_batch_responses,
        )
    )
    for output in (quote_prompt_out, quote_schema_out, quote_manifest_out):
        if output.exists():
            raise ValueError(f"refusing to overwrite existing output: {output}")
    _write_new(quote_prompt_out, prompt.encode("utf-8"))
    _write_json(quote_schema_out, schema)
    _write_json(quote_manifest_out, quote_manifest)
    return {
        "status": "PHASE_A_BATCHED_CONFIRMED_EVIDENCE_SELECTION_QUOTES_READY",
        "candidate_count": len(quote_manifest["labeled_inventory"]),
        "relation_batch_count": len(batch_manifest["batches"]),
        "confirmation_batch_count": len(confirmation_batch_manifest["batches"]),
        "selected_row_count": len(quote_manifest["selected_rows"]),
        "quote_manifest_sha256": quote_manifest["manifest_sha256"],
        "model_api_calls": 0,
    }


def _selection_manifest_for_finalization(path: Path) -> dict[str, Any]:
    selection_manifest = _load_object(path)
    if selection_manifest.get("schema_version") != SELECTION_BATCH_MANIFEST_VERSION:
        return selection_manifest
    embedded = selection_manifest.get("selection_manifest")
    if not isinstance(embedded, dict):
        raise EvidenceConsumerError(
            "manifest_verification",
            "selection batch manifest is missing its embedded selection manifest",
        )
    return embedded


def finalize_evidence_selection_quotes_run(
    *,
    selection_manifest_path: Path,
    quote_manifest_path: Path,
    response_path: Path,
    confirmation_manifest_path: Path | None,
    confirmation_response_path: Path | None,
    artifact_out: Path,
) -> dict[str, Any]:
    selection_manifest = _selection_manifest_for_finalization(selection_manifest_path)
    sources = load_selection_sources(selection_manifest)
    quote_manifest = _load_object(quote_manifest_path)
    if quote_manifest.get("selection_manifest_sha256") != selection_manifest.get(
        "manifest_sha256"
    ):
        raise EvidenceConsumerError(
            "manifest_verification", "quote manifest belongs to another selection"
        )
    # A historical v1/v3/v4/v5 quote manifest carries no confirmation
    # obligation and rejects a confirmation attachment, so replaying one has to
    # be able to reach finalize_quotes with no confirmation supplied.
    if (confirmation_manifest_path is None) != (confirmation_response_path is None):
        raise EvidenceConsumerError(
            "relation_confirmation_shape",
            "supply both the confirmation manifest and its response, or neither",
        )
    artifact = finalize_quotes(
        quote_manifest,
        sources,
        _load_object(response_path),
        (
            _load_object(confirmation_manifest_path)
            if confirmation_manifest_path is not None
            else None
        ),
        (
            _load_object(confirmation_response_path)
            if confirmation_response_path is not None
            else None
        ),
    )
    if artifact_out.exists():
        raise ValueError(f"refusing to overwrite existing output: {artifact_out}")
    _write_json(artifact_out, artifact)
    return {
        "status": "PHASE_A_EVIDENCE_SELECTION_COMPLETE",
        "candidate_count": artifact["candidate_count"],
        "truth_group_count": artifact["truth_group_count"],
        "influence_group_count": artifact["influence_group_count"],
        "artifact_out": str(artifact_out),
        "artifact_sha256": hash_file(artifact_out),
        "model_api_calls": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materialize = sub.add_parser("materialize-v3")
    materialize.add_argument("--source", type=Path, required=True)
    materialize.add_argument("--repo-root", type=Path, required=True)
    materialize.add_argument("--source-out", type=Path, required=True)

    audit_phase_a = sub.add_parser("audit-phase-a-source")
    audit_phase_a.add_argument("--spec", type=Path, required=True)
    audit_phase_a.add_argument("--repo-root", type=Path, required=True)
    audit_phase_a.add_argument("--audit-out", type=Path, required=True)

    census_phase_a = sub.add_parser("census-phase-a-corpus")
    census_phase_a.add_argument("--evidence-ledger", type=Path, required=True)
    census_phase_a.add_argument("--retailer-coding", type=Path, required=True)
    census_phase_a.add_argument("--retailer-source-manifest", type=Path, required=True)
    census_phase_a.add_argument("--census-out", type=Path, required=True)

    retailer_manifest = sub.add_parser("build-retailer-source-manifest")
    retailer_manifest.add_argument("--retailer-coding", type=Path, required=True)
    retailer_manifest.add_argument("--manifest-out", type=Path, required=True)

    reddit_source = sub.add_parser("build-phase-a-reddit-source-v3")
    reddit_source.add_argument("--run-spec", type=Path, required=True)
    reddit_source.add_argument("--evidence-ledger", type=Path, required=True)
    reddit_source.add_argument("--repo-root", type=Path, required=True)
    reddit_source.add_argument("--source-out", type=Path, required=True)

    retailer_source = sub.add_parser("build-phase-a-retailer-source-v3")
    retailer_source.add_argument("--run-spec", type=Path, required=True)
    retailer_source.add_argument("--retailer-coding", type=Path, required=True)
    retailer_source.add_argument(
        "--retailer-source-manifest", type=Path, required=True
    )
    retailer_source.add_argument(
        "--revolve-completion-receipt", type=Path
    )
    retailer_source.add_argument("--repo-root", type=Path, required=True)
    retailer_source.add_argument("--source-out", type=Path, required=True)

    product_axis_proof = sub.add_parser("build-product-axis-proof-source")
    product_axis_proof.add_argument("--full-source", type=Path, required=True)
    product_axis_proof.add_argument("--run-spec", type=Path, required=True)
    product_axis_proof.add_argument("--stable-product-id", required=True)
    product_axis_proof.add_argument("--axis-id", action="append", required=True)
    product_axis_proof.add_argument("--repo-root", type=Path, required=True)
    product_axis_proof.add_argument("--source-out", type=Path, required=True)

    serp_frontier = sub.add_parser("prepare-serp-source-frontier")
    serp_frontier.add_argument("--surface-spec", type=Path, required=True)
    serp_frontier.add_argument("--inventory-out", type=Path, required=True)

    serp_surface_spec = sub.add_parser("build-serp-source-surface-spec")
    serp_surface_spec.add_argument("--surface-map", type=Path, required=True)
    serp_surface_spec.add_argument("--surface-spec-out", type=Path, required=True)

    serp_review = sub.add_parser("materialize-serp-source-frontier-review")
    serp_review.add_argument("--inventory", type=Path, required=True)
    serp_review.add_argument("--review", type=Path, required=True)
    serp_review.add_argument("--result-out", type=Path, required=True)

    serp_reconciliation = sub.add_parser("reconcile-serp-frontier-targets")
    serp_reconciliation.add_argument("--frontier-result", type=Path, required=True)
    serp_reconciliation.add_argument("--evidence-ledger", type=Path, required=True)
    serp_reconciliation.add_argument("--result-out", type=Path, required=True)

    materialize_phase_a = sub.add_parser("materialize-phase-a-v3")
    materialize_phase_a.add_argument("--spec", type=Path, required=True)
    materialize_phase_a.add_argument("--repo-root", type=Path, required=True)
    materialize_phase_a.add_argument("--source-out", type=Path, required=True)
    materialize_phase_a.add_argument("--receipt-out", type=Path, required=True)

    prepare = sub.add_parser("prepare-batches")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--repo-root", type=Path, required=True)
    prepare.add_argument("--bundle-out", type=Path, required=True)
    prepare.add_argument("--prompt-dir", type=Path, required=True)
    prepare.add_argument("--max-batch-chars", type=int, default=80_000)
    prepare.add_argument("--max-prompt-bytes", type=int)
    prepare.add_argument("--max-evidence-per-work-unit", type=int, default=120)

    execution_pack = sub.add_parser("prepare-prompt-execution-pack")
    execution_pack.add_argument("--bundle", type=Path, required=True)
    execution_pack.add_argument("--pack-dir", type=Path, required=True)

    verify_execution_pack = sub.add_parser("verify-prompt-execution-pack")
    verify_execution_pack.add_argument("--bundle", type=Path, required=True)
    verify_execution_pack.add_argument("--pack-dir", type=Path, required=True)

    submit = sub.add_parser("submit-batches")
    submit.add_argument("--bundle", type=Path, required=True)
    submit.add_argument("--response", type=Path, action="append", required=True)
    submit.add_argument("--compiled-out", type=Path, required=True)

    prepare_verification = sub.add_parser("prepare-row-verification")
    prepare_verification.add_argument("--bundle", type=Path, required=True)
    prepare_verification.add_argument("--compiled", type=Path, required=True)
    prepare_verification.add_argument("--stage-out", type=Path, required=True)
    prepare_verification.add_argument("--prompt-dir", type=Path, required=True)
    prepare_verification.add_argument("--max-prompt-bytes", type=int)

    submit_verification = sub.add_parser("submit-row-verification")
    submit_verification.add_argument("--bundle", type=Path, required=True)
    submit_verification.add_argument("--compiled", type=Path, required=True)
    submit_verification.add_argument("--stage", type=Path, required=True)
    submit_verification.add_argument(
        "--response", type=Path, action="append", default=[]
    )
    submit_verification.add_argument("--verified-out", type=Path, required=True)

    prepare_repair = sub.add_parser("prepare-row-repair")
    prepare_repair.add_argument("--bundle", type=Path, required=True)
    prepare_repair.add_argument("--verified", type=Path, required=True)
    prepare_repair.add_argument("--evidence-id", action="append", required=True)
    prepare_repair.add_argument("--stage-out", type=Path, required=True)
    prepare_repair.add_argument("--prompt-dir", type=Path, required=True)
    prepare_repair.add_argument("--max-prompt-bytes", type=int)

    submit_repair = sub.add_parser("submit-row-repair")
    submit_repair.add_argument("--bundle", type=Path, required=True)
    submit_repair.add_argument("--verified", type=Path, required=True)
    submit_repair.add_argument("--stage", type=Path, required=True)
    submit_repair.add_argument("--response", type=Path, action="append", required=True)
    submit_repair.add_argument("--repaired-out", type=Path, required=True)

    prepare_audit = sub.add_parser("prepare-targeted-benchmark-audit")
    prepare_audit.add_argument("--bundle", type=Path, required=True)
    prepare_audit.add_argument("--verified", type=Path, required=True)
    prepare_audit.add_argument("--selection", type=Path, required=True)
    prepare_audit.add_argument("--benchmark", type=Path, required=True)
    prepare_audit.add_argument("--row-verification-stage", type=Path, required=True)
    prepare_audit.add_argument("--stage-out", type=Path, required=True)
    prepare_audit.add_argument("--shared-frame-out", type=Path, required=True)
    prepare_audit.add_argument("--prompt-manifest-out", type=Path, required=True)
    prepare_audit.add_argument("--assignment-manifest-out", type=Path, required=True)
    prepare_audit.add_argument("--prompt-dir", type=Path, required=True)
    prepare_audit.add_argument("--max-prompt-bytes", type=int)
    prepare_audit.add_argument("--worker-count", type=int, default=6)

    submit_audit = sub.add_parser("submit-targeted-benchmark-audit")
    submit_audit.add_argument("--stage", type=Path, required=True)
    submit_audit.add_argument("--prompt-manifest", type=Path, required=True)
    submit_audit.add_argument("--response", type=Path, action="append", required=True)
    submit_audit.add_argument("--audit-out", type=Path, required=True)

    validate_batch = sub.add_parser("validate-batch-response")
    validate_batch.add_argument("--bundle", type=Path, required=True)
    validate_batch.add_argument("--response", type=Path, required=True)
    validate_batch.add_argument("--receipt-out", type=Path)

    publish_batch = sub.add_parser("publish-batch-response")
    publish_batch.add_argument("--bundle", type=Path, required=True)
    publish_batch.add_argument("--staged-response", type=Path, required=True)
    publish_batch.add_argument("--response-dir", type=Path, required=True)

    reconcile = sub.add_parser("prepare-reconciliation")
    reconcile.add_argument("--bundle", type=Path, required=True)
    reconcile.add_argument("--compiled", type=Path, required=True)
    reconcile.add_argument("--prompt-out", type=Path, required=True)

    finish = sub.add_parser("finalize")
    finish.add_argument("--bundle", type=Path, required=True)
    finish.add_argument("--compiled", type=Path, required=True)
    finish.add_argument("--response", type=Path, required=True)
    finish.add_argument("--view-out", type=Path, required=True)

    reconcile_level = sub.add_parser("prepare-reconciliation-level")
    reconcile_level.add_argument("--bundle", type=Path, required=True)
    reconcile_level.add_argument("--compilation", type=Path, required=True)
    reconcile_level.add_argument("--stage-out", type=Path, required=True)
    reconcile_level.add_argument("--prompt-dir", type=Path, required=True)
    reconcile_level.add_argument(
        "--reconciliation-policy",
        choices=[RECONCILIATION_POLICY_VERSION_V2],
    )

    submit_level = sub.add_parser("submit-reconciliation-level")
    submit_level.add_argument("--bundle", type=Path, required=True)
    submit_level.add_argument("--stage", type=Path, required=True)
    submit_level.add_argument("--response", type=Path, action="append", required=True)
    submit_level.add_argument("--compilation-out", type=Path, required=True)

    validate_reconciliation = sub.add_parser("validate-reconciliation-response")
    validate_reconciliation.add_argument("--bundle", type=Path, required=True)
    validate_reconciliation.add_argument("--stage", type=Path, required=True)
    validate_reconciliation.add_argument("--response", type=Path, required=True)
    validate_reconciliation.add_argument("--receipt-out", type=Path)

    prepare_closure = sub.add_parser("prepare-relation-closure")
    prepare_closure.add_argument("--bundle", type=Path, required=True)
    prepare_closure.add_argument("--node-compilation", type=Path, required=True)
    prepare_closure.add_argument("--stage-out", type=Path, required=True)
    prepare_closure.add_argument("--prompt-dir", type=Path, required=True)
    prepare_closure.add_argument("--max-prompt-bytes", type=int)

    submit_closure = sub.add_parser("submit-relation-closure")
    submit_closure.add_argument("--bundle", type=Path, required=True)
    submit_closure.add_argument("--stage", type=Path, required=True)
    submit_closure.add_argument("--response", type=Path, action="append", default=[])
    submit_closure.add_argument("--compilation-out", type=Path, required=True)

    validate_closure = sub.add_parser("validate-relation-closure-response")
    validate_closure.add_argument("--bundle", type=Path, required=True)
    validate_closure.add_argument("--stage", type=Path, required=True)
    validate_closure.add_argument("--response", type=Path, required=True)
    validate_closure.add_argument("--receipt-out", type=Path)

    status = sub.add_parser("status")
    status.add_argument("--bundle", type=Path, required=True)
    status.add_argument("--response-dir", type=Path, required=True)

    finish_v3 = sub.add_parser("finalize-v3")
    finish_v3.add_argument("--bundle", type=Path, required=True)
    finish_v3.add_argument("--batch-compilation", type=Path, required=True)
    finish_v3.add_argument("--node-compilation", type=Path, required=True)
    finish_v3.add_argument("--view-out", type=Path, required=True)

    migrate_terminal = sub.add_parser("migrate-repaired-terminal")
    migrate_terminal.add_argument("--bundle", type=Path, required=True)
    migrate_terminal.add_argument(
        "--source-batch-compilation", type=Path, required=True
    )
    migrate_terminal.add_argument(
        "--repaired-batch-compilation", type=Path, required=True
    )
    migrate_terminal.add_argument(
        "--source-node-compilation", type=Path, required=True
    )
    migrate_terminal.add_argument("--compilation-out", type=Path, required=True)
    migrate_terminal.add_argument("--manifest-out", type=Path, required=True)

    finish_closed = sub.add_parser("finalize-relation-closed")
    finish_closed.add_argument("--bundle", type=Path, required=True)
    finish_closed.add_argument("--batch-compilation", type=Path, required=True)
    finish_closed.add_argument("--relation-compilation", type=Path, required=True)
    finish_closed.add_argument("--view-out", type=Path, required=True)

    evidence_packet = sub.add_parser("project-evidence-packet")
    evidence_packet.add_argument("--view", type=Path, required=True)
    evidence_packet.add_argument("--bundle", type=Path, required=True)
    evidence_packet.add_argument("--batch-compilation", type=Path, required=True)
    evidence_packet.add_argument("--node-compilation", type=Path, required=True)
    selection = evidence_packet.add_mutually_exclusive_group(required=True)
    selection.add_argument("--axis-id", action="append", default=[])
    selection.add_argument("--proposition-id", action="append", default=[])
    evidence_packet.add_argument("--packet-out", type=Path, required=True)
    evidence_packet.add_argument(
        "--packet-version", choices=("v1", "v2", "v3"), default="v3"
    )

    consumer_prepare = sub.add_parser("prepare-evidence-consumer-batch")
    consumer_prepare.add_argument("--spec", type=Path, required=True)
    consumer_prepare.add_argument("--prompt-out", type=Path, required=True)
    consumer_prepare.add_argument("--response-schema-out", type=Path, required=True)
    consumer_prepare.add_argument("--manifest-out", type=Path, required=True)

    consumer_finalize = sub.add_parser("finalize-evidence-consumer-batch")
    consumer_finalize.add_argument("--manifest", type=Path, required=True)
    consumer_finalize.add_argument("--response", type=Path, required=True)
    consumer_finalize.add_argument("--artifact-dir", type=Path, required=True)

    frontier_build = sub.add_parser("build-customer-pull-point-frontier")
    frontier_build.add_argument("--spec", type=Path, required=True)
    frontier_build.add_argument("--frontier-out", type=Path, required=True)

    frontier_point = sub.add_parser(
        "materialize-customer-pull-point-selection-spec"
    )
    frontier_point.add_argument("--frontier", type=Path, required=True)
    frontier_point.add_argument("--packet", type=Path, required=True)
    frontier_point.add_argument("--bundle", type=Path, required=True)
    frontier_point.add_argument("--proposition-id", required=True)
    frontier_point.add_argument("--point-actor-scope", type=json.loads, required=True,
                                help="Authored JSON: source_local_reports mode, or identified_actor mode with source_id and independence_key")
    frontier_point.add_argument(
        "--reject-frontier-relation",
        action="append",
        default=[],
        dest="rejected_frontier_semantic_refs",
        help=(
            "literal semantic ref whose bound source does not state the point; "
            "repeat for multiple rejected relations"
        ),
    )
    frontier_point.add_argument("--spec-out", type=Path, required=True)

    selection_prepare = sub.add_parser("prepare-evidence-selection")
    selection_prepare.add_argument("--spec", type=Path, required=True)
    selection_prepare.add_argument("--prompt-out", type=Path, required=True)
    selection_prepare.add_argument("--response-schema-out", type=Path, required=True)
    selection_prepare.add_argument("--manifest-out", type=Path, required=True)

    selection_batch_prepare = sub.add_parser("prepare-evidence-selection-batches")
    selection_batch_prepare.add_argument("--spec", type=Path, required=True)
    selection_batch_prepare.add_argument("--batch-size", type=int, required=True)
    selection_batch_prepare.add_argument("--batch-dir", type=Path, required=True)
    selection_batch_prepare.add_argument(
        "--batch-manifest-out", type=Path, required=True
    )

    attempt_reserve = sub.add_parser("reserve-evidence-selection-provider-attempt")
    attempt_reserve.add_argument("--attempt-root", type=Path, required=True)
    attempt_reserve.add_argument("--attempt-id", required=True)

    attempt_publish = sub.add_parser("publish-evidence-selection-provider-attempt")
    attempt_publish.add_argument("--attempt-dir", type=Path, required=True)
    attempt_publish.add_argument("--response-dir", type=Path, required=True)
    attempt_publish.add_argument("--canonical-response-name", required=True)
    attempt_publish.add_argument("--batch-manifest", type=Path)
    attempt_publish.add_argument("--batch-id")

    selection_relations = sub.add_parser("finalize-evidence-selection-relations")
    selection_relations.add_argument("--manifest", type=Path, required=True)
    selection_relations.add_argument("--response", type=Path, required=True)
    selection_relations.add_argument("--quote-prompt-out", type=Path, required=True)
    selection_relations.add_argument("--quote-schema-out", type=Path, required=True)
    selection_relations.add_argument("--quote-manifest-out", type=Path, required=True)
    selection_relations.add_argument(
        "--confirmation-prompt-out", type=Path, required=True
    )
    selection_relations.add_argument(
        "--confirmation-schema-out", type=Path, required=True
    )
    selection_relations.add_argument(
        "--confirmation-manifest-out", type=Path, required=True
    )

    preselection_confirmation = sub.add_parser(
        "prepare-preselection-relation-confirmation"
    )
    preselection_confirmation.add_argument(
        "--selection-manifest", type=Path, required=True
    )
    preselection_confirmation.add_argument(
        "--first-response", type=Path, required=True
    )
    preselection_confirmation.add_argument("--prompt-out", type=Path, required=True)
    preselection_confirmation.add_argument(
        "--response-schema-out", type=Path, required=True
    )
    preselection_confirmation.add_argument(
        "--confirmation-manifest-out", type=Path, required=True
    )

    preselection_finalize = sub.add_parser(
        "finalize-preselection-relation-confirmation"
    )
    preselection_finalize.add_argument(
        "--selection-manifest", type=Path, required=True
    )
    preselection_finalize.add_argument("--first-response", type=Path, required=True)
    preselection_finalize.add_argument(
        "--confirmation-manifest", type=Path, required=True
    )
    preselection_finalize.add_argument(
        "--confirmation-response", type=Path, required=True
    )
    preselection_finalize.add_argument(
        "--quote-prompt-out", type=Path, required=True
    )
    preselection_finalize.add_argument(
        "--quote-schema-out", type=Path, required=True
    )
    preselection_finalize.add_argument(
        "--quote-manifest-out", type=Path, required=True
    )

    batched_preselection_confirmation = sub.add_parser(
        "prepare-batched-preselection-relation-confirmation"
    )
    batched_preselection_confirmation.add_argument(
        "--batch-manifest", type=Path, required=True
    )
    batched_preselection_confirmation.add_argument(
        "--response-dir", type=Path, required=True
    )
    batched_preselection_confirmation.add_argument(
        "--batch-size", type=int, required=True
    )
    batched_preselection_confirmation.add_argument(
        "--confirmation-batch-dir", type=Path, required=True
    )
    batched_preselection_confirmation.add_argument(
        "--confirmation-batch-manifest-out", type=Path, required=True
    )

    batched_preselection_finalize = sub.add_parser(
        "finalize-batched-preselection-relation-confirmation"
    )
    batched_preselection_finalize.add_argument(
        "--batch-manifest", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--response-dir", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--confirmation-batch-manifest", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--confirmation-response-dir", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--quote-prompt-out", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--quote-schema-out", type=Path, required=True
    )
    batched_preselection_finalize.add_argument(
        "--quote-manifest-out", type=Path, required=True
    )

    selection_batch_relations = sub.add_parser(
        "finalize-evidence-selection-batches"
    )
    selection_batch_relations.add_argument(
        "--batch-manifest", type=Path, required=True
    )
    selection_batch_relations.add_argument("--response-dir", type=Path, required=True)
    selection_batch_relations.add_argument(
        "--quote-prompt-out", type=Path, required=True
    )
    selection_batch_relations.add_argument(
        "--quote-schema-out", type=Path, required=True
    )
    selection_batch_relations.add_argument(
        "--quote-manifest-out", type=Path, required=True
    )
    selection_batch_relations.add_argument(
        "--confirmation-prompt-out", type=Path, required=True
    )
    selection_batch_relations.add_argument(
        "--confirmation-schema-out", type=Path, required=True
    )
    selection_batch_relations.add_argument(
        "--confirmation-manifest-out", type=Path, required=True
    )

    selection_quotes = sub.add_parser("finalize-evidence-selection-quotes")
    selection_quotes.add_argument("--selection-manifest", type=Path, required=True)
    selection_quotes.add_argument("--quote-manifest", type=Path, required=True)
    selection_quotes.add_argument("--response", type=Path, required=True)
    # Required for a v6 pack. Omit both for a frontier-bound v7 pack, whose
    # preselection confirmation is already hash-bound, or for historical
    # v1/v3/v4/v5 replay, which fails closed on any attachment.
    selection_quotes.add_argument(
        "--confirmation-manifest", type=Path, default=None
    )
    selection_quotes.add_argument(
        "--confirmation-response", type=Path, default=None
    )
    selection_quotes.add_argument("--artifact-out", type=Path, required=True)

    calibration_prepare = sub.add_parser("prepare-calibration")
    calibration_prepare.add_argument("--source", type=Path, required=True)
    calibration_prepare.add_argument("--spec", type=Path, required=True)
    calibration_prepare.add_argument("--output-dir", type=Path, required=True)

    calibration_evaluate = sub.add_parser("evaluate-calibration")
    calibration_evaluate.add_argument("--source", type=Path, required=True)
    calibration_evaluate.add_argument("--prepared-dir", type=Path, required=True)
    calibration_evaluate.add_argument("--spec", type=Path, required=True)
    calibration_evaluate.add_argument("--response-root", type=Path, required=True)
    calibration_evaluate.add_argument("--cold-response-root", type=Path)
    calibration_evaluate.add_argument("--reconciliation-root", type=Path)
    calibration_evaluate.add_argument("--verified-compilation-root", type=Path)
    calibration_evaluate.add_argument("--adjudication", type=Path)
    calibration_evaluate.add_argument("--report-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "materialize-v3":
            result = materialize_v3(
                source_path=args.source,
                repo_root=args.repo_root,
                source_out=args.source_out,
            )
        elif args.command == "audit-phase-a-source":
            result = audit_phase_a_source_run(
                spec_path=args.spec,
                repo_root=args.repo_root,
                audit_out=args.audit_out,
            )
        elif args.command == "census-phase-a-corpus":
            result = census_phase_a_corpus_run(
                evidence_ledger_path=args.evidence_ledger,
                retailer_coding_path=args.retailer_coding,
                retailer_source_manifest_path=args.retailer_source_manifest,
                census_out=args.census_out,
            )
        elif args.command == "build-retailer-source-manifest":
            result = build_retailer_source_manifest_run(
                retailer_coding_path=args.retailer_coding,
                manifest_out=args.manifest_out,
            )
        elif args.command == "build-phase-a-reddit-source-v3":
            result = build_phase_a_reddit_source_v3_run(
                run_spec_path=args.run_spec,
                evidence_ledger_path=args.evidence_ledger,
                repo_root=args.repo_root,
                source_out=args.source_out,
            )
        elif args.command == "build-phase-a-retailer-source-v3":
            result = build_phase_a_retailer_source_v3_run(
                run_spec_path=args.run_spec,
                retailer_coding_path=args.retailer_coding,
                retailer_source_manifest_path=args.retailer_source_manifest,
                revolve_completion_receipt_path=args.revolve_completion_receipt,
                repo_root=args.repo_root,
                source_out=args.source_out,
            )
        elif args.command == "build-product-axis-proof-source":
            result = build_product_axis_proof_run(
                full_source_path=args.full_source,
                run_spec_path=args.run_spec,
                stable_product_id=args.stable_product_id,
                axis_ids=args.axis_id,
                repo_root=args.repo_root,
                source_out=args.source_out,
            )
        elif args.command == "prepare-serp-source-frontier":
            result = prepare_serp_source_frontier_run(
                surface_spec_path=args.surface_spec,
                inventory_out=args.inventory_out,
            )
        elif args.command == "build-serp-source-surface-spec":
            result = build_serp_source_surface_spec_run(
                surface_map_path=args.surface_map,
                surface_spec_out=args.surface_spec_out,
            )
        elif args.command == "materialize-serp-source-frontier-review":
            result = materialize_serp_source_frontier_review_run(
                inventory_path=args.inventory,
                review_path=args.review,
                result_out=args.result_out,
            )
        elif args.command == "reconcile-serp-frontier-targets":
            result = reconcile_serp_frontier_targets_run(
                frontier_result_path=args.frontier_result,
                evidence_ledger_path=args.evidence_ledger,
                result_out=args.result_out,
            )
        elif args.command == "materialize-phase-a-v3":
            result = materialize_phase_a_source(
                spec_path=args.spec,
                repo_root=args.repo_root,
                source_out=args.source_out,
                receipt_out=args.receipt_out,
            )
        elif args.command == "prepare-batches":
            result = prepare_batches(
                source_path=args.source,
                repo_root=args.repo_root,
                bundle_out=args.bundle_out,
                prompt_dir=args.prompt_dir,
                max_batch_chars=args.max_batch_chars,
                max_prompt_bytes=args.max_prompt_bytes,
                max_evidence_per_work_unit=args.max_evidence_per_work_unit,
            )
        elif args.command == "prepare-prompt-execution-pack":
            result = prepare_prompt_execution_pack(
                bundle_path=args.bundle,
                pack_dir=args.pack_dir,
            )
        elif args.command == "verify-prompt-execution-pack":
            result = verify_prompt_execution_pack(
                bundle_path=args.bundle,
                pack_dir=args.pack_dir,
            )
        elif args.command == "submit-batches":
            result = submit_batches(
                bundle_path=args.bundle,
                response_paths=args.response,
                compiled_out=args.compiled_out,
            )
        elif args.command == "prepare-row-verification":
            result = prepare_row_verification_run(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                stage_out=args.stage_out,
                prompt_dir=args.prompt_dir,
                max_prompt_bytes=args.max_prompt_bytes,
            )
        elif args.command == "submit-row-verification":
            result = submit_row_verification_run(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                stage_path=args.stage,
                response_paths=args.response,
                verified_out=args.verified_out,
            )
        elif args.command == "prepare-row-repair":
            result = prepare_row_repair_run(
                bundle_path=args.bundle,
                verified_path=args.verified,
                evidence_ids=args.evidence_id,
                stage_out=args.stage_out,
                prompt_dir=args.prompt_dir,
                max_prompt_bytes=args.max_prompt_bytes,
            )
        elif args.command == "submit-row-repair":
            result = submit_row_repair_run(
                bundle_path=args.bundle,
                verified_path=args.verified,
                stage_path=args.stage,
                response_paths=args.response,
                repaired_out=args.repaired_out,
            )
        elif args.command == "prepare-targeted-benchmark-audit":
            result = prepare_targeted_benchmark_audit_run(
                bundle_path=args.bundle,
                verified_path=args.verified,
                selection_path=args.selection,
                benchmark_path=args.benchmark,
                row_verification_stage_path=args.row_verification_stage,
                stage_out=args.stage_out,
                shared_frame_out=args.shared_frame_out,
                prompt_manifest_out=args.prompt_manifest_out,
                assignment_manifest_out=args.assignment_manifest_out,
                prompt_dir=args.prompt_dir,
                max_prompt_bytes=args.max_prompt_bytes,
                worker_count=args.worker_count,
            )
        elif args.command == "submit-targeted-benchmark-audit":
            result = submit_targeted_benchmark_audit_run(
                stage_path=args.stage,
                prompt_manifest_path=args.prompt_manifest,
                response_paths=args.response,
                audit_out=args.audit_out,
            )
        elif args.command == "validate-batch-response":
            result = validate_batch_response_file(
                bundle_path=args.bundle,
                response_path=args.response,
                receipt_out=args.receipt_out,
            )
        elif args.command == "publish-batch-response":
            result = publish_batch_response_file(
                bundle_path=args.bundle,
                staged_response_path=args.staged_response,
                response_dir=args.response_dir,
            )
        elif args.command == "prepare-reconciliation":
            result = prepare_reconciliation(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                prompt_out=args.prompt_out,
            )
        elif args.command == "finalize":
            result = finalize(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                response_path=args.response,
                view_out=args.view_out,
            )
        elif args.command == "prepare-reconciliation-level":
            result = prepare_reconciliation_level(
                bundle_path=args.bundle,
                compilation_path=args.compilation,
                stage_out=args.stage_out,
                prompt_dir=args.prompt_dir,
                reconciliation_policy_version=args.reconciliation_policy,
            )
        elif args.command == "submit-reconciliation-level":
            result = submit_reconciliation_level(
                bundle_path=args.bundle,
                stage_path=args.stage,
                response_paths=args.response,
                compilation_out=args.compilation_out,
            )
        elif args.command == "validate-reconciliation-response":
            result = validate_reconciliation_response_file(
                bundle_path=args.bundle,
                stage_path=args.stage,
                response_path=args.response,
                receipt_out=args.receipt_out,
            )
        elif args.command == "prepare-relation-closure":
            result = prepare_relation_closure_run(
                bundle_path=args.bundle,
                node_compilation_path=args.node_compilation,
                stage_out=args.stage_out,
                prompt_dir=args.prompt_dir,
                max_prompt_bytes=args.max_prompt_bytes,
            )
        elif args.command == "submit-relation-closure":
            result = submit_relation_closure_run(
                bundle_path=args.bundle,
                stage_path=args.stage,
                response_paths=args.response,
                compilation_out=args.compilation_out,
            )
        elif args.command == "validate-relation-closure-response":
            result = validate_relation_closure_response_file(
                bundle_path=args.bundle,
                stage_path=args.stage,
                response_path=args.response,
                receipt_out=args.receipt_out,
            )
        elif args.command == "status":
            result = semantic_run_status(
                bundle_path=args.bundle,
                response_dir=args.response_dir,
            )
        elif args.command == "finalize-v3":
            result = finalize_v3(
                bundle_path=args.bundle,
                batch_compilation_path=args.batch_compilation,
                node_compilation_path=args.node_compilation,
                view_out=args.view_out,
            )
        elif args.command == "migrate-repaired-terminal":
            result = migrate_repaired_terminal_run(
                bundle_path=args.bundle,
                source_batch_compilation_path=args.source_batch_compilation,
                repaired_batch_compilation_path=args.repaired_batch_compilation,
                source_node_compilation_path=args.source_node_compilation,
                compilation_out=args.compilation_out,
                manifest_out=args.manifest_out,
            )
        elif args.command == "finalize-relation-closed":
            result = finalize_relation_closed(
                bundle_path=args.bundle,
                batch_compilation_path=args.batch_compilation,
                relation_compilation_path=args.relation_compilation,
                view_out=args.view_out,
            )
        elif args.command == "project-evidence-packet":
            result = project_evidence_packet_run(
                view_path=args.view,
                bundle_path=args.bundle,
                batch_compilation_path=args.batch_compilation,
                node_compilation_path=args.node_compilation,
                axis_ids=args.axis_id,
                proposition_ids=args.proposition_id,
                packet_out=args.packet_out,
                packet_version=args.packet_version,
            )
        elif args.command == "prepare-evidence-consumer-batch":
            result = prepare_evidence_consumer_batch_run(
                spec_path=args.spec,
                prompt_out=args.prompt_out,
                response_schema_out=args.response_schema_out,
                manifest_out=args.manifest_out,
            )
        elif args.command == "finalize-evidence-consumer-batch":
            result = finalize_evidence_consumer_batch_run(
                manifest_path=args.manifest,
                response_path=args.response,
                artifact_dir=args.artifact_dir,
            )
        elif args.command == "build-customer-pull-point-frontier":
            result = build_customer_pull_point_frontier_run(
                spec_path=args.spec,
                frontier_out=args.frontier_out,
            )
        elif args.command == "materialize-customer-pull-point-selection-spec":
            result = materialize_customer_pull_point_selection_spec_run(
                frontier_path=args.frontier,
                packet_path=args.packet,
                bundle_path=args.bundle,
                proposition_id=args.proposition_id,
                spec_out=args.spec_out,
                point_actor_scope=args.point_actor_scope,
                rejected_frontier_semantic_refs=(
                    args.rejected_frontier_semantic_refs
                ),
            )
        elif args.command == "prepare-evidence-selection":
            result = prepare_evidence_selection_run(
                spec_path=args.spec,
                prompt_out=args.prompt_out,
                response_schema_out=args.response_schema_out,
                manifest_out=args.manifest_out,
            )
        elif args.command == "prepare-evidence-selection-batches":
            result = prepare_evidence_selection_batches_run(
                spec_path=args.spec,
                batch_size=args.batch_size,
                batch_dir=args.batch_dir,
                batch_manifest_out=args.batch_manifest_out,
            )
        elif args.command == "reserve-evidence-selection-provider-attempt":
            result = reserve_evidence_selection_provider_attempt(
                attempt_root=args.attempt_root,
                attempt_id=args.attempt_id,
            )
        elif args.command == "publish-evidence-selection-provider-attempt":
            result = publish_evidence_selection_provider_attempt(
                attempt_dir=args.attempt_dir,
                response_dir=args.response_dir,
                canonical_response_name=args.canonical_response_name,
                batch_manifest_path=args.batch_manifest,
                batch_id=args.batch_id,
            )
        elif args.command == "finalize-evidence-selection-relations":
            result = finalize_evidence_selection_relations_run(
                manifest_path=args.manifest,
                response_path=args.response,
                quote_prompt_out=args.quote_prompt_out,
                quote_schema_out=args.quote_schema_out,
                quote_manifest_out=args.quote_manifest_out,
                confirmation_prompt_out=args.confirmation_prompt_out,
                confirmation_schema_out=args.confirmation_schema_out,
                confirmation_manifest_out=args.confirmation_manifest_out,
            )
        elif args.command == "prepare-preselection-relation-confirmation":
            result = prepare_preselection_relation_confirmation_run(
                selection_manifest_path=args.selection_manifest,
                first_response_path=args.first_response,
                prompt_out=args.prompt_out,
                response_schema_out=args.response_schema_out,
                confirmation_manifest_out=args.confirmation_manifest_out,
            )
        elif args.command == "finalize-preselection-relation-confirmation":
            result = finalize_preselection_relation_confirmation_run(
                selection_manifest_path=args.selection_manifest,
                first_response_path=args.first_response,
                confirmation_manifest_path=args.confirmation_manifest,
                confirmation_response_path=args.confirmation_response,
                quote_prompt_out=args.quote_prompt_out,
                quote_schema_out=args.quote_schema_out,
                quote_manifest_out=args.quote_manifest_out,
            )
        elif args.command == "prepare-batched-preselection-relation-confirmation":
            result = prepare_batched_preselection_relation_confirmation_run(
                batch_manifest_path=args.batch_manifest,
                response_dir=args.response_dir,
                batch_size=args.batch_size,
                confirmation_batch_dir=args.confirmation_batch_dir,
                confirmation_batch_manifest_out=args.confirmation_batch_manifest_out,
            )
        elif args.command == "finalize-batched-preselection-relation-confirmation":
            result = finalize_batched_preselection_relation_confirmation_run(
                batch_manifest_path=args.batch_manifest,
                response_dir=args.response_dir,
                confirmation_batch_manifest_path=args.confirmation_batch_manifest,
                confirmation_response_dir=args.confirmation_response_dir,
                quote_prompt_out=args.quote_prompt_out,
                quote_schema_out=args.quote_schema_out,
                quote_manifest_out=args.quote_manifest_out,
            )
        elif args.command == "finalize-evidence-selection-batches":
            result = finalize_evidence_selection_batches_run(
                batch_manifest_path=args.batch_manifest,
                response_dir=args.response_dir,
                quote_prompt_out=args.quote_prompt_out,
                quote_schema_out=args.quote_schema_out,
                quote_manifest_out=args.quote_manifest_out,
                confirmation_prompt_out=args.confirmation_prompt_out,
                confirmation_schema_out=args.confirmation_schema_out,
                confirmation_manifest_out=args.confirmation_manifest_out,
            )
        elif args.command == "finalize-evidence-selection-quotes":
            result = finalize_evidence_selection_quotes_run(
                selection_manifest_path=args.selection_manifest,
                quote_manifest_path=args.quote_manifest,
                response_path=args.response,
                confirmation_manifest_path=args.confirmation_manifest,
                confirmation_response_path=args.confirmation_response,
                artifact_out=args.artifact_out,
            )
        elif args.command == "prepare-calibration":
            result = prepare_semantic_calibration_run(
                source_path=args.source,
                spec_path=args.spec,
                output_dir=args.output_dir,
            )
        else:
            result = evaluate_semantic_calibration_run(
                source_path=args.source,
                prepared_dir=args.prepared_dir,
                spec_path=args.spec,
                response_root=args.response_root,
                cold_response_root=args.cold_response_root,
                reconciliation_root=args.reconciliation_root,
                verified_compilation_root=args.verified_compilation_root,
                adjudication_path=args.adjudication,
                report_out=args.report_out,
            )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        SemanticIntegrationError,
        SemanticCalibrationError,
        EvidenceConsumerError,
    ) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.command == "evaluate-calibration" and result.get("status") != "SEMANTIC_CALIBRATION_PASS":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
