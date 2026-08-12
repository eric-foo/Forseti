"""Prepare and compile one agent-run semantic evidence integration job."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judgment.semantic_evidence_integration import (  # noqa: E402
    BUNDLE_VERSION_V4,
    SemanticIntegrationError,
    apply_row_verification,
    build_batch_prompts,
    build_bundle,
    build_prompt_execution_pack,
    build_reconciliation_prompt,
    finalize_v3_view,
    finalize_view,
    materialize_source_v3,
    project_evidence_packet,
    prepare_reconciliation_stage,
    prepare_row_verification,
    reconstruct_prompt_execution_payload,
    validate_batch_responses,
    validate_reconciliation_stage,
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
from harness_utils import hash_file  # noqa: E402


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
    expected_ids = [row["batch_id"] for row in bundle.get("batches", [])]
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
                "batch_id": batch_id,
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
    revolve_completion_receipt_path: Path,
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
    *, bundle_path: Path, compilation_path: Path, stage_out: Path, prompt_dir: Path
) -> dict[str, Any]:
    bundle = _load_object(bundle_path)
    compilation = _load_object(compilation_path)
    stage, prompts = prepare_reconciliation_stage(bundle, compilation)
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
    terminal = (
        compilation["input_batch_count"] == 1
        and bool(compilation["semantic_nodes"])
        and all(
            row["terminal_proposition"] is True
            for row in compilation["semantic_nodes"]
        )
    )
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


def project_evidence_packet_run(
    *,
    view_path: Path,
    bundle_path: Path,
    batch_compilation_path: Path,
    node_compilation_path: Path,
    axis_ids: list[str],
    proposition_ids: list[str],
    packet_out: Path,
) -> dict[str, Any]:
    view = _load_object(view_path)
    bundle = _load_object(bundle_path)
    batch_compilation = _load_object(batch_compilation_path)
    node_compilation = _load_object(node_compilation_path)
    packet = project_evidence_packet(
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
        "--revolve-completion-receipt", type=Path, required=True
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

    status = sub.add_parser("status")
    status.add_argument("--bundle", type=Path, required=True)
    status.add_argument("--response-dir", type=Path, required=True)

    finish_v3 = sub.add_parser("finalize-v3")
    finish_v3.add_argument("--bundle", type=Path, required=True)
    finish_v3.add_argument("--batch-compilation", type=Path, required=True)
    finish_v3.add_argument("--node-compilation", type=Path, required=True)
    finish_v3.add_argument("--view-out", type=Path, required=True)

    evidence_packet = sub.add_parser("project-evidence-packet")
    evidence_packet.add_argument("--view", type=Path, required=True)
    evidence_packet.add_argument("--bundle", type=Path, required=True)
    evidence_packet.add_argument("--batch-compilation", type=Path, required=True)
    evidence_packet.add_argument("--node-compilation", type=Path, required=True)
    selection = evidence_packet.add_mutually_exclusive_group(required=True)
    selection.add_argument("--axis-id", action="append", default=[])
    selection.add_argument("--proposition-id", action="append", default=[])
    evidence_packet.add_argument("--packet-out", type=Path, required=True)

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
        elif args.command == "project-evidence-packet":
            result = project_evidence_packet_run(
                view_path=args.view,
                bundle_path=args.bundle,
                batch_compilation_path=args.batch_compilation,
                node_compilation_path=args.node_compilation,
                axis_ids=args.axis_id,
                proposition_ids=args.proposition_id,
                packet_out=args.packet_out,
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
    ) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.command == "evaluate-calibration" and result.get("status") != "SEMANTIC_CALIBRATION_PASS":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
