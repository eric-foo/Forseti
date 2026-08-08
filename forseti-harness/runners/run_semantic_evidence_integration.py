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
    build_batch_prompts,
    build_bundle,
    build_reconciliation_prompt,
    finalize_v3_view,
    finalize_view,
    materialize_source_v3,
    project_evidence_packet,
    prepare_reconciliation_stage,
    validate_batch_responses,
    validate_reconciliation_stage,
)
from judgment.phase_a_semantic_run import (  # noqa: E402
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
    if bundle.get("schema_version") == BUNDLE_VERSION_V4:
        _write_json(
            prompt_dir / "worker_assignments.json",
            {
                "schema_version": "semantic_worker_assignment_v1",
                "bundle_sha256": bundle["bundle_sha256"],
                "worker_count": 3,
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
    if target.exists():
        raise ValueError(f"refusing to overwrite existing response: {target}")
    try:
        os.rename(staged_response_path, target)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing response: {target}") from exc
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

    submit = sub.add_parser("submit-batches")
    submit.add_argument("--bundle", type=Path, required=True)
    submit.add_argument("--response", type=Path, action="append", required=True)
    submit.add_argument("--compiled-out", type=Path, required=True)

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
        elif args.command == "submit-batches":
            result = submit_batches(
                bundle_path=args.bundle,
                response_paths=args.response,
                compiled_out=args.compiled_out,
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
        else:
            result = project_evidence_packet_run(
                view_path=args.view,
                bundle_path=args.bundle,
                batch_compilation_path=args.batch_compilation,
                node_compilation_path=args.node_compilation,
                axis_ids=args.axis_id,
                proposition_ids=args.proposition_id,
                packet_out=args.packet_out,
            )
    except (OSError, ValueError, json.JSONDecodeError, SemanticIntegrationError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
