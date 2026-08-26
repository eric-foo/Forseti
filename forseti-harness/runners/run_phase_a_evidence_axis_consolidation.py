"""Build or validate a derived Phase A axis consolidation view."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judgment.phase_a_evidence_axis_consolidation import (  # noqa: E402
    _axis_reader_point_filename,
    _compile_point_reader_brief_from_validated_facts,
    _validate_axis_point_reader_output_from_validated_snapshot,
    _validate_point_reader_brief_from_validated_facts,
    assemble_axis_point_reader_output,
    bind_axis_reader_output_schema,
    build_axis_point_reader_snapshot,
    build_axis_reader_bundle,
    build_axis_reader_accounting,
    build_no_frontier_reader_request,
    build_axis_dogfood_truth_index,
    build_axis_consolidated_view,
    build_phase_a_evidence_axis_pack,
    compile_point_reader_brief,
    compile_no_frontier_reader_output,
    materialize_phase_a_evidence_no_frontier_axis_manifest,
    POINT_READER_REQUEST_VERSION,
    validate_axis_point_reader_output,
    validate_axis_point_reader_snapshot,
    validate_axis_reader_bundle,
    validate_axis_reader_accounting,
    validate_axis_reader_structured_output,
    validate_axis_dogfood_truth_index,
    validate_axis_consolidated_view,
    validate_phase_a_evidence_axis_pack,
    validate_point_reader_brief,
    validate_no_frontier_reader_output,
    validate_no_frontier_reader_request,
)
from judgment.phase_a_evidence_consumer import EvidenceConsumerError  # noqa: E402


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _write_new_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(value)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def build_run(*, spec_path: Path, output_path: Path) -> dict[str, Any]:
    view = build_axis_consolidated_view(_load_object(spec_path))
    validate_axis_consolidated_view(
        view, expected_view_sha256=view["view_sha256"]
    )
    _write_new(output_path, view)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "view_sha256": view["view_sha256"],
        "counts": view["counts"],
        "model_api_calls": 0,
    }


def build_axis_pack_run(*, manifest_path: Path, output_path: Path) -> dict[str, Any]:
    pack = build_phase_a_evidence_axis_pack(_load_object(manifest_path))
    validate_phase_a_evidence_axis_pack(
        pack, expected_axis_pack_sha256=pack["axis_pack_sha256"]
    )
    _write_new(output_path, pack)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "axis_pack_sha256": pack["axis_pack_sha256"],
        "valid_point_count": pack["valid_point_count"],
        "rejected_point_count": pack["rejected_point_count"],
        "model_api_calls": 0,
    }


def materialize_no_frontier_axis_manifest_run(
    *,
    axis_id: str,
    subject_product_ids: list[str],
    source_id: str,
    packet_path: Path,
    bundle_path: Path,
    frontier_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    manifest = materialize_phase_a_evidence_no_frontier_axis_manifest(
        axis_id=axis_id,
        subject_product_ids=subject_product_ids,
        source_id=source_id,
        packet_path=packet_path,
        bundle_path=bundle_path,
        frontier_path=frontier_path,
    )
    _write_new(output_path, manifest)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "manifest_sha256": manifest["manifest_sha256"],
        "candidate_semantic_unit_count": len(
            manifest["expected_semantic_unit_refs"]
        ),
        "model_api_calls": 0,
    }


def validate_axis_pack_run(
    *, pack_path: Path, expected_axis_pack_sha256: str
) -> dict[str, Any]:
    pack = validate_phase_a_evidence_axis_pack(
        _load_object(pack_path), expected_axis_pack_sha256=expected_axis_pack_sha256
    )
    return {
        "status": "valid",
        "pack_path": str(pack_path),
        "axis_pack_sha256": pack["axis_pack_sha256"],
        "valid_point_count": pack["valid_point_count"],
        "rejected_point_count": pack["rejected_point_count"],
        "model_api_calls": 0,
    }


def build_reader_accounting_run(
    *, pack_path: Path, output_path: Path
) -> dict[str, Any]:
    accounting = build_axis_reader_accounting(
        _load_object(pack_path), source_axis_pack_path=pack_path
    )
    validate_axis_reader_accounting(
        accounting,
        expected_accounting_sha256=accounting["accounting_sha256"],
    )
    _write_new(output_path, accounting)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "accounting_sha256": accounting["accounting_sha256"],
        "point_count": len(accounting["points"]),
        "model_api_calls": 0,
    }


def validate_reader_accounting_run(
    *, accounting_path: Path, expected_accounting_sha256: str
) -> dict[str, Any]:
    accounting = validate_axis_reader_accounting(
        _load_object(accounting_path),
        expected_accounting_sha256=expected_accounting_sha256,
    )
    return {
        "status": "valid",
        "accounting_path": str(accounting_path),
        "accounting_sha256": accounting["accounting_sha256"],
        "point_count": len(accounting["points"]),
        "model_api_calls": 0,
    }


def prepare_no_frontier_reader_request_run(
    *, pack_path: Path, output_path: Path
) -> dict[str, Any]:
    request = build_no_frontier_reader_request(
        _load_object(pack_path), source_axis_pack_path=pack_path
    )
    validate_no_frontier_reader_request(
        request, expected_request_sha256=request["request_sha256"]
    )
    _write_new(output_path, request)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "request_sha256": request["request_sha256"],
        "candidate_row_count": len(request["candidate_rows"]),
        "request_bytes": output_path.stat().st_size,
        "model_api_calls": 0,
    }


def finalize_no_frontier_reader_run(
    *, request_path: Path, response_path: Path, output_path: Path
) -> dict[str, Any]:
    request = _load_object(request_path)
    output = compile_no_frontier_reader_output(
        request, response=_load_object(response_path)
    )
    validate_no_frontier_reader_output(
        request,
        output=output,
        expected_output_sha256=output["output_sha256"],
    )
    _write_new(output_path, output)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "output_sha256": output["output_sha256"],
        "displayed_example_count": output["display_scope"][
            "displayed_example_count"
        ],
        "complete_candidate_row_count": output["display_scope"][
            "complete_candidate_row_count"
        ],
        "model_api_calls": 0,
    }


def validate_no_frontier_reader_output_run(
    *, request_path: Path, output_path: Path, expected_output_sha256: str
) -> dict[str, Any]:
    output = validate_no_frontier_reader_output(
        _load_object(request_path),
        output=_load_object(output_path),
        expected_output_sha256=expected_output_sha256,
    )
    return {
        "status": "valid",
        "output_path": str(output_path),
        "output_sha256": output["output_sha256"],
        "complete_candidate_row_count": output["display_scope"][
            "complete_candidate_row_count"
        ],
        "model_api_calls": 0,
    }


def validate_run(*, view_path: Path, expected_view_sha256: str) -> dict[str, Any]:
    view = validate_axis_consolidated_view(
        _load_object(view_path), expected_view_sha256=expected_view_sha256
    )
    return {
        "status": "valid",
        "view_path": str(view_path),
        "view_sha256": view["view_sha256"],
        "counts": view["counts"],
        "model_api_calls": 0,
    }


def build_dogfood_truth_run(*, view_path: Path, output_path: Path) -> dict[str, Any]:
    view = _load_object(view_path)
    truth_index = build_axis_dogfood_truth_index(
        view, source_view_path=view_path
    )
    validate_axis_dogfood_truth_index(
        truth_index,
        expected_truth_index_sha256=truth_index["truth_index_sha256"],
    )
    _write_new(output_path, truth_index)
    return {
        "status": "complete",
        "output_path": str(output_path),
        "truth_index_sha256": truth_index["truth_index_sha256"],
        "counts": truth_index["counts"],
        "model_api_calls": 0,
    }


def validate_dogfood_truth_run(
    *, truth_path: Path, expected_truth_index_sha256: str
) -> dict[str, Any]:
    truth_index = validate_axis_dogfood_truth_index(
        _load_object(truth_path),
        expected_truth_index_sha256=expected_truth_index_sha256,
    )
    return {
        "status": "valid",
        "truth_path": str(truth_path),
        "truth_index_sha256": truth_index["truth_index_sha256"],
        "counts": truth_index["counts"],
        "model_api_calls": 0,
    }


def build_reader_run(
    *, view_path: Path, manifest_output_path: Path, facts_output_dir: Path
) -> dict[str, Any]:
    occupied = [
        path for path in (manifest_output_path, facts_output_dir) if path.exists()
    ]
    if occupied:
        raise ValueError(f"refusing to overwrite existing output: {occupied[0]}")
    view = _load_object(view_path)
    manifest, fact_streams = build_axis_reader_bundle(
        view, source_view_path=view_path, facts_dir=facts_output_dir
    )
    facts_output_dir.mkdir(parents=True)
    for point_id, fact_bytes in fact_streams.items():
        _write_new_bytes(
            facts_output_dir / _axis_reader_point_filename(point_id), fact_bytes
        )
    _write_new(manifest_output_path, manifest)
    saved_manifest = _load_object(manifest_output_path)
    validate_axis_reader_bundle(
        saved_manifest,
        facts_dir=facts_output_dir,
        expected_reader_manifest_sha256=manifest["reader_manifest_sha256"],
    )
    return {
        "status": "complete",
        "manifest_output_path": str(manifest_output_path),
        "facts_output_dir": str(facts_output_dir),
        "reader_manifest_sha256": manifest["reader_manifest_sha256"],
        "fact_count": manifest["facts_directory"]["fact_count"],
        "model_api_calls": 0,
    }


def validate_reader_run(
    *,
    manifest_path: Path,
    facts_dir: Path,
    expected_reader_manifest_sha256: str,
) -> dict[str, Any]:
    manifest, _ = validate_axis_reader_bundle(
        _load_object(manifest_path),
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=expected_reader_manifest_sha256,
    )
    return {
        "status": "valid",
        "manifest_path": str(manifest_path),
        "facts_dir": str(facts_dir),
        "reader_manifest_sha256": manifest["reader_manifest_sha256"],
        "fact_count": manifest["facts_directory"]["fact_count"],
        "model_api_calls": 0,
    }


def validate_reader_output_run(
    *,
    manifest_path: Path,
    facts_dir: Path,
    output_path: Path,
    expected_reader_manifest_sha256: str,
) -> dict[str, Any]:
    result = validate_axis_reader_structured_output(
        _load_object(manifest_path),
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=expected_reader_manifest_sha256,
        output=_load_object(output_path),
    )
    return {**result, "output_path": str(output_path), "model_api_calls": 0}


def bind_reader_output_schema_run(
    *,
    manifest_path: Path,
    facts_dir: Path,
    base_schema_path: Path,
    output_schema_path: Path,
    expected_reader_manifest_sha256: str,
) -> dict[str, Any]:
    manifest, _ = validate_axis_reader_bundle(
        _load_object(manifest_path),
        facts_dir=facts_dir,
        expected_reader_manifest_sha256=expected_reader_manifest_sha256,
    )
    schema = bind_axis_reader_output_schema(
        manifest, _load_object(base_schema_path)
    )
    _write_new(output_schema_path, schema)
    return {
        "status": "complete",
        "output_schema_path": str(output_schema_path),
        "point_count": len(manifest["points"]),
        "reader_manifest_sha256": manifest["reader_manifest_sha256"],
        "model_api_calls": 0,
    }


def build_point_reader_run(
    *,
    view_path: Path,
    subject_identity_path: Path,
    manifest_output_path: Path,
    point_store_dir: Path,
) -> dict[str, Any]:
    """Freeze one portable point-work snapshot and reuse exact stored inputs."""

    if manifest_output_path.exists():
        raise ValueError(f"refusing to overwrite existing output: {manifest_output_path}")
    manifest, payloads = build_axis_point_reader_snapshot(
        _load_object(view_path),
        source_view_path=view_path,
        subject_identity=_load_object(subject_identity_path),
    )
    point_store_dir.mkdir(parents=True, exist_ok=True)
    materialized = 0
    reused = 0
    for point in manifest["points"]:
        payload = payloads[point["point_id"]]
        point_path = point_store_dir / point["point_payload_file"]
        if point_path.exists():
            if not point_path.is_file() or point_path.read_bytes() != payload:
                raise ValueError(
                    f"stored point payload conflicts with its identity: {point_path}"
                )
            reused += 1
        else:
            _write_new_bytes(point_path, payload)
            materialized += 1
    _write_new(manifest_output_path, manifest)
    saved_manifest = _load_object(manifest_output_path)
    validate_axis_point_reader_snapshot(
        saved_manifest,
        point_store_dir=point_store_dir,
        expected_snapshot_sha256=manifest["snapshot_sha256"],
    )
    return {
        "status": "complete",
        "manifest_output_path": str(manifest_output_path),
        "point_store_dir": str(point_store_dir),
        "snapshot_sha256": manifest["snapshot_sha256"],
        "counts": manifest["counts"],
        "materialized_point_count": materialized,
        "reused_point_count": reused,
        "model_api_calls": 0,
    }


def validate_point_reader_run(
    *,
    manifest_path: Path,
    point_store_dir: Path,
    expected_snapshot_sha256: str,
) -> dict[str, Any]:
    manifest, payloads = validate_axis_point_reader_snapshot(
        _load_object(manifest_path),
        point_store_dir=point_store_dir,
        expected_snapshot_sha256=expected_snapshot_sha256,
    )
    return {
        "status": "valid",
        "manifest_path": str(manifest_path),
        "point_store_dir": str(point_store_dir),
        "snapshot_sha256": manifest["snapshot_sha256"],
        "point_count": len(payloads),
        "counts": manifest["counts"],
        "model_api_calls": 0,
    }


def _point_reader_request(
    manifest: dict[str, Any], point: dict[str, Any], payload: bytes
) -> dict[str, Any]:
    facts = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    response_schema = copy.deepcopy(manifest["method_binding"]["response_schema"])
    properties = response_schema.get("properties")
    if (
        not isinstance(properties, dict)
        or not isinstance(properties.get("point_id"), dict)
        or not isinstance(properties.get("point_input_sha256"), dict)
    ):
        raise EvidenceConsumerError(
            "point_reader_response_schema", "response schema identity fields are missing"
        )
    properties["point_id"]["const"] = point["point_id"]
    properties["point_input_sha256"]["const"] = point["point_input_sha256"]
    request: dict[str, Any] = {
        "schema_version": POINT_READER_REQUEST_VERSION,
        "point_input_sha256": point["point_input_sha256"],
        "point_id": point["point_id"],
        "bounded_point": point["bounded_point"],
        "projection_mode": point["projection_mode"],
        "candidate_pool_accounting": copy.deepcopy(
            point["candidate_pool_accounting"]
        ),
        "method_text": manifest["method_binding"]["method_text"],
        "response_schema": response_schema,
        "facts": facts,
        "response_file": point["response_file"],
    }
    request["request_sha256"] = _canonical_sha256(request)
    return request


def prepare_point_reader_request_run(
    *,
    manifest_path: Path,
    point_store_dir: Path,
    point_id: str,
    output_path: Path,
    expected_snapshot_sha256: str,
) -> dict[str, Any]:
    if output_path.exists():
        raise ValueError(f"refusing to overwrite existing output: {output_path}")
    manifest, payloads = validate_axis_point_reader_snapshot(
        _load_object(manifest_path),
        point_store_dir=point_store_dir,
        expected_snapshot_sha256=expected_snapshot_sha256,
    )
    point = next(
        (row for row in manifest["points"] if row["point_id"] == point_id), None
    )
    if point is None:
        raise ValueError(f"point is not in the snapshot: {point_id}")
    request = _point_reader_request(manifest, point, payloads[point_id])
    _write_new(output_path, request)
    saved = _load_object(output_path)
    if saved != request or saved["request_sha256"] != _canonical_sha256(
        {key: value for key, value in saved.items() if key != "request_sha256"}
    ):
        raise ValueError("saved point-reader request changed after write")
    return {
        "status": "complete",
        "output_path": str(output_path),
        "point_id": point_id,
        "response_file": point["response_file"],
        "request_sha256": request["request_sha256"],
        "model_api_calls": 0,
    }


def prepare_point_reader_requests_run(
    *,
    manifest_path: Path,
    point_store_dir: Path,
    output_dir: Path,
    expected_snapshot_sha256: str,
) -> dict[str, Any]:
    """Materialize all point requests after one complete snapshot validation."""

    manifest, payloads = validate_axis_point_reader_snapshot(
        _load_object(manifest_path),
        point_store_dir=point_store_dir,
        expected_snapshot_sha256=expected_snapshot_sha256,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    materialized = 0
    reused = 0
    for point in manifest["points"]:
        request = _point_reader_request(
            manifest, point, payloads[point["point_id"]]
        )
        request_path = output_dir / f"request_{request['request_sha256']}.json"
        if request_path.exists():
            if not request_path.is_file() or _load_object(request_path) != request:
                raise ValueError(
                    f"stored point request conflicts with its identity: {request_path}"
                )
            reused += 1
        else:
            _write_new(request_path, request)
            materialized += 1
    return {
        "status": "complete",
        "output_dir": str(output_dir),
        "snapshot_sha256": manifest["snapshot_sha256"],
        "materialized_request_count": materialized,
        "reused_request_count": reused,
        "model_api_calls": 0,
    }


def finalize_point_reader_run(
    *,
    manifest_path: Path,
    point_store_dir: Path,
    responses_dir: Path,
    brief_store_dir: Path,
    output_path: Path,
    expected_snapshot_sha256: str,
) -> dict[str, Any]:
    """Compile or reuse points in order; valid earlier work survives interruption."""

    if output_path.exists():
        raise ValueError(f"refusing to overwrite existing output: {output_path}")
    manifest, payloads = validate_axis_point_reader_snapshot(
        _load_object(manifest_path),
        point_store_dir=point_store_dir,
        expected_snapshot_sha256=expected_snapshot_sha256,
    )
    brief_store_dir.mkdir(parents=True, exist_ok=True)
    briefs: list[dict[str, Any]] = []
    missing_point_ids: list[str] = []
    compiled = 0
    reused = 0
    for point in manifest["points"]:
        facts = [
            json.loads(line)
            for line in payloads[point["point_id"]].decode("utf-8").splitlines()
        ]
        brief_path = brief_store_dir / point["brief_file"]
        if brief_path.exists():
            brief = _validate_point_reader_brief_from_validated_facts(
                manifest,
                point=point,
                facts=facts,
                brief=_load_object(brief_path),
            )
            reused += 1
        else:
            response_path = responses_dir / point["response_file"]
            if not response_path.is_file():
                missing_point_ids.append(point["point_id"])
                continue
            brief = _compile_point_reader_brief_from_validated_facts(
                manifest,
                point=point,
                facts=facts,
                response=_load_object(response_path),
            )
            _write_new(brief_path, brief)
            brief = _validate_point_reader_brief_from_validated_facts(
                manifest,
                point=point,
                facts=facts,
                brief=_load_object(brief_path),
            )
            compiled += 1
        briefs.append(brief)
    if missing_point_ids:
        raise EvidenceConsumerError(
            "point_reader_response",
            "point-reader response is missing: " + ", ".join(missing_point_ids),
        )
    output = assemble_axis_point_reader_output(manifest, briefs=briefs)
    _write_new(output_path, output)
    saved = _validate_axis_point_reader_output_from_validated_snapshot(
        manifest,
        output=_load_object(output_path),
        payloads=payloads,
    )
    return {
        "status": "complete",
        "output_path": str(output_path),
        "axis_output_sha256": saved["axis_output_sha256"],
        "compiled_point_count": compiled,
        "reused_brief_count": reused,
        "counts": saved["counts"],
        "model_api_calls": 0,
    }


def validate_point_reader_output_run(
    *,
    manifest_path: Path,
    point_store_dir: Path,
    output_path: Path,
    expected_snapshot_sha256: str,
) -> dict[str, Any]:
    manifest = _load_object(manifest_path)
    if manifest.get("snapshot_sha256") != expected_snapshot_sha256:
        raise ValueError("trusted point-reader snapshot identity changed")
    output = validate_axis_point_reader_output(
        manifest,
        output=_load_object(output_path),
        point_store_dir=point_store_dir,
    )
    return {
        "status": "valid",
        "output_path": str(output_path),
        "snapshot_sha256": manifest["snapshot_sha256"],
        "axis_output_sha256": output["axis_output_sha256"],
        "counts": output["counts"],
        "model_api_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--spec", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    build_pack_parser = subparsers.add_parser("build-axis-pack")
    build_pack_parser.add_argument("--manifest", type=Path, required=True)
    build_pack_parser.add_argument("--output", type=Path, required=True)
    materialize_no_frontier_parser = subparsers.add_parser(
        "materialize-no-frontier-axis-manifest"
    )
    materialize_no_frontier_parser.add_argument("--axis-id", required=True)
    materialize_no_frontier_parser.add_argument(
        "--subject-product-id", action="append", required=True
    )
    materialize_no_frontier_parser.add_argument(
        "--source-id", default="full-corpus"
    )
    materialize_no_frontier_parser.add_argument("--packet", type=Path, required=True)
    materialize_no_frontier_parser.add_argument("--bundle", type=Path, required=True)
    materialize_no_frontier_parser.add_argument(
        "--frontier", type=Path, required=True
    )
    materialize_no_frontier_parser.add_argument("--output", type=Path, required=True)
    validate_pack_parser = subparsers.add_parser("validate-axis-pack")
    validate_pack_parser.add_argument("--pack", type=Path, required=True)
    validate_pack_parser.add_argument("--expected-axis-pack-sha256", required=True)
    build_accounting_parser = subparsers.add_parser("build-reader-accounting")
    build_accounting_parser.add_argument("--axis-pack", type=Path, required=True)
    build_accounting_parser.add_argument("--output", type=Path, required=True)
    validate_accounting_parser = subparsers.add_parser(
        "validate-reader-accounting"
    )
    validate_accounting_parser.add_argument(
        "--accounting", type=Path, required=True
    )
    validate_accounting_parser.add_argument(
        "--expected-accounting-sha256", required=True
    )
    prepare_no_frontier_reader_parser = subparsers.add_parser(
        "prepare-no-frontier-reader-request"
    )
    prepare_no_frontier_reader_parser.add_argument(
        "--axis-pack", type=Path, required=True
    )
    prepare_no_frontier_reader_parser.add_argument(
        "--output", type=Path, required=True
    )
    finalize_no_frontier_reader_parser = subparsers.add_parser(
        "finalize-no-frontier-reader"
    )
    finalize_no_frontier_reader_parser.add_argument(
        "--request", type=Path, required=True
    )
    finalize_no_frontier_reader_parser.add_argument(
        "--response", type=Path, required=True
    )
    finalize_no_frontier_reader_parser.add_argument(
        "--output", type=Path, required=True
    )
    validate_no_frontier_reader_parser = subparsers.add_parser(
        "validate-no-frontier-reader-output"
    )
    validate_no_frontier_reader_parser.add_argument(
        "--request", type=Path, required=True
    )
    validate_no_frontier_reader_parser.add_argument(
        "--output", type=Path, required=True
    )
    validate_no_frontier_reader_parser.add_argument(
        "--expected-output-sha256", required=True
    )
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--view", type=Path, required=True)
    validate_parser.add_argument("--expected-view-sha256", required=True)
    build_truth_parser = subparsers.add_parser("build-dogfood-truth")
    build_truth_parser.add_argument("--view", type=Path, required=True)
    build_truth_parser.add_argument("--output", type=Path, required=True)
    validate_truth_parser = subparsers.add_parser("validate-dogfood-truth")
    validate_truth_parser.add_argument("--truth", type=Path, required=True)
    validate_truth_parser.add_argument("--expected-truth-index-sha256", required=True)
    build_reader_parser = subparsers.add_parser("build-reader")
    build_reader_parser.add_argument("--view", type=Path, required=True)
    build_reader_parser.add_argument("--manifest-output", type=Path, required=True)
    build_reader_parser.add_argument("--facts-output-dir", type=Path, required=True)
    validate_reader_parser = subparsers.add_parser("validate-reader")
    validate_reader_parser.add_argument("--manifest", type=Path, required=True)
    validate_reader_parser.add_argument("--facts-dir", type=Path, required=True)
    validate_reader_parser.add_argument(
        "--expected-reader-manifest-sha256", required=True
    )
    validate_reader_output_parser = subparsers.add_parser("validate-reader-output")
    validate_reader_output_parser.add_argument("--manifest", type=Path, required=True)
    validate_reader_output_parser.add_argument("--facts-dir", type=Path, required=True)
    validate_reader_output_parser.add_argument("--output", type=Path, required=True)
    validate_reader_output_parser.add_argument(
        "--expected-reader-manifest-sha256", required=True
    )
    bind_reader_output_schema_parser = subparsers.add_parser(
        "bind-reader-output-schema"
    )
    bind_reader_output_schema_parser.add_argument("--manifest", type=Path, required=True)
    bind_reader_output_schema_parser.add_argument("--facts-dir", type=Path, required=True)
    bind_reader_output_schema_parser.add_argument(
        "--base-schema", type=Path, required=True
    )
    bind_reader_output_schema_parser.add_argument(
        "--output-schema", type=Path, required=True
    )
    bind_reader_output_schema_parser.add_argument(
        "--expected-reader-manifest-sha256", required=True
    )
    build_point_reader_parser = subparsers.add_parser("build-point-reader-run")
    build_point_reader_parser.add_argument("--view", type=Path, required=True)
    build_point_reader_parser.add_argument(
        "--subject-identity", type=Path, required=True
    )
    build_point_reader_parser.add_argument(
        "--manifest-output", type=Path, required=True
    )
    build_point_reader_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    validate_point_reader_parser = subparsers.add_parser(
        "validate-point-reader-run"
    )
    validate_point_reader_parser.add_argument("--manifest", type=Path, required=True)
    validate_point_reader_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    validate_point_reader_parser.add_argument(
        "--expected-snapshot-sha256", required=True
    )
    prepare_point_reader_parser = subparsers.add_parser(
        "prepare-point-reader-request"
    )
    prepare_point_reader_parser.add_argument("--manifest", type=Path, required=True)
    prepare_point_reader_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    prepare_point_reader_parser.add_argument("--point-id", required=True)
    prepare_point_reader_parser.add_argument("--output", type=Path, required=True)
    prepare_point_reader_parser.add_argument(
        "--expected-snapshot-sha256", required=True
    )
    prepare_point_readers_parser = subparsers.add_parser(
        "prepare-point-reader-requests"
    )
    prepare_point_readers_parser.add_argument("--manifest", type=Path, required=True)
    prepare_point_readers_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    prepare_point_readers_parser.add_argument(
        "--output-dir", type=Path, required=True
    )
    prepare_point_readers_parser.add_argument(
        "--expected-snapshot-sha256", required=True
    )
    finalize_point_reader_parser = subparsers.add_parser(
        "finalize-point-reader-run"
    )
    finalize_point_reader_parser.add_argument("--manifest", type=Path, required=True)
    finalize_point_reader_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    finalize_point_reader_parser.add_argument(
        "--responses-dir", type=Path, required=True
    )
    finalize_point_reader_parser.add_argument(
        "--brief-store-dir", type=Path, required=True
    )
    finalize_point_reader_parser.add_argument("--output", type=Path, required=True)
    finalize_point_reader_parser.add_argument(
        "--expected-snapshot-sha256", required=True
    )
    validate_point_reader_output_parser = subparsers.add_parser(
        "validate-point-reader-output"
    )
    validate_point_reader_output_parser.add_argument(
        "--manifest", type=Path, required=True
    )
    validate_point_reader_output_parser.add_argument(
        "--point-store-dir", type=Path, required=True
    )
    validate_point_reader_output_parser.add_argument(
        "--output", type=Path, required=True
    )
    validate_point_reader_output_parser.add_argument(
        "--expected-snapshot-sha256", required=True
    )
    args = parser.parse_args()
    if args.command == "build-axis-pack":
        result = build_axis_pack_run(
            manifest_path=args.manifest, output_path=args.output
        )
    elif args.command == "materialize-no-frontier-axis-manifest":
        result = materialize_no_frontier_axis_manifest_run(
            axis_id=args.axis_id,
            subject_product_ids=args.subject_product_id,
            source_id=args.source_id,
            packet_path=args.packet,
            bundle_path=args.bundle,
            frontier_path=args.frontier,
            output_path=args.output,
        )
    elif args.command == "validate-axis-pack":
        result = validate_axis_pack_run(
            pack_path=args.pack,
            expected_axis_pack_sha256=args.expected_axis_pack_sha256,
        )
    elif args.command == "build-reader-accounting":
        result = build_reader_accounting_run(
            pack_path=args.axis_pack, output_path=args.output
        )
    elif args.command == "validate-reader-accounting":
        result = validate_reader_accounting_run(
            accounting_path=args.accounting,
            expected_accounting_sha256=args.expected_accounting_sha256,
        )
    elif args.command == "prepare-no-frontier-reader-request":
        result = prepare_no_frontier_reader_request_run(
            pack_path=args.axis_pack, output_path=args.output
        )
    elif args.command == "finalize-no-frontier-reader":
        result = finalize_no_frontier_reader_run(
            request_path=args.request,
            response_path=args.response,
            output_path=args.output,
        )
    elif args.command == "validate-no-frontier-reader-output":
        result = validate_no_frontier_reader_output_run(
            request_path=args.request,
            output_path=args.output,
            expected_output_sha256=args.expected_output_sha256,
        )
    elif args.command == "build":
        result = build_run(spec_path=args.spec, output_path=args.output)
    elif args.command == "build-dogfood-truth":
        result = build_dogfood_truth_run(
            view_path=args.view, output_path=args.output
        )
    elif args.command == "validate-dogfood-truth":
        result = validate_dogfood_truth_run(
            truth_path=args.truth,
            expected_truth_index_sha256=args.expected_truth_index_sha256,
        )
    elif args.command == "build-reader":
        result = build_reader_run(
            view_path=args.view,
            manifest_output_path=args.manifest_output,
            facts_output_dir=args.facts_output_dir,
        )
    elif args.command == "validate-reader":
        result = validate_reader_run(
            manifest_path=args.manifest,
            facts_dir=args.facts_dir,
            expected_reader_manifest_sha256=args.expected_reader_manifest_sha256,
        )
    elif args.command == "validate-reader-output":
        result = validate_reader_output_run(
            manifest_path=args.manifest,
            facts_dir=args.facts_dir,
            output_path=args.output,
            expected_reader_manifest_sha256=args.expected_reader_manifest_sha256,
        )
    elif args.command == "bind-reader-output-schema":
        result = bind_reader_output_schema_run(
            manifest_path=args.manifest,
            facts_dir=args.facts_dir,
            base_schema_path=args.base_schema,
            output_schema_path=args.output_schema,
            expected_reader_manifest_sha256=args.expected_reader_manifest_sha256,
        )
    elif args.command == "build-point-reader-run":
        result = build_point_reader_run(
            view_path=args.view,
            subject_identity_path=args.subject_identity,
            manifest_output_path=args.manifest_output,
            point_store_dir=args.point_store_dir,
        )
    elif args.command == "validate-point-reader-run":
        result = validate_point_reader_run(
            manifest_path=args.manifest,
            point_store_dir=args.point_store_dir,
            expected_snapshot_sha256=args.expected_snapshot_sha256,
        )
    elif args.command == "prepare-point-reader-request":
        result = prepare_point_reader_request_run(
            manifest_path=args.manifest,
            point_store_dir=args.point_store_dir,
            point_id=args.point_id,
            output_path=args.output,
            expected_snapshot_sha256=args.expected_snapshot_sha256,
        )
    elif args.command == "prepare-point-reader-requests":
        result = prepare_point_reader_requests_run(
            manifest_path=args.manifest,
            point_store_dir=args.point_store_dir,
            output_dir=args.output_dir,
            expected_snapshot_sha256=args.expected_snapshot_sha256,
        )
    elif args.command == "finalize-point-reader-run":
        result = finalize_point_reader_run(
            manifest_path=args.manifest,
            point_store_dir=args.point_store_dir,
            responses_dir=args.responses_dir,
            brief_store_dir=args.brief_store_dir,
            output_path=args.output,
            expected_snapshot_sha256=args.expected_snapshot_sha256,
        )
    elif args.command == "validate-point-reader-output":
        result = validate_point_reader_output_run(
            manifest_path=args.manifest,
            point_store_dir=args.point_store_dir,
            output_path=args.output,
            expected_snapshot_sha256=args.expected_snapshot_sha256,
        )
    else:
        result = validate_run(
            view_path=args.view,
            expected_view_sha256=args.expected_view_sha256,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
