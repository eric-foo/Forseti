"""Build or validate a derived Phase A axis consolidation view."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judgment.phase_a_evidence_axis_consolidation import (  # noqa: E402
    _axis_reader_point_filename,
    bind_axis_reader_output_schema,
    build_axis_reader_bundle,
    build_axis_dogfood_truth_index,
    build_axis_consolidated_view,
    build_phase_a_evidence_axis_pack,
    validate_axis_reader_bundle,
    validate_axis_reader_structured_output,
    validate_axis_dogfood_truth_index,
    validate_axis_consolidated_view,
    validate_phase_a_evidence_axis_pack,
)


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
    validate_axis_reader_bundle(
        manifest,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--spec", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    build_pack_parser = subparsers.add_parser("build-axis-pack")
    build_pack_parser.add_argument("--manifest", type=Path, required=True)
    build_pack_parser.add_argument("--output", type=Path, required=True)
    validate_pack_parser = subparsers.add_parser("validate-axis-pack")
    validate_pack_parser.add_argument("--pack", type=Path, required=True)
    validate_pack_parser.add_argument("--expected-axis-pack-sha256", required=True)
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
    args = parser.parse_args()
    if args.command == "build-axis-pack":
        result = build_axis_pack_run(
            manifest_path=args.manifest, output_path=args.output
        )
    elif args.command == "validate-axis-pack":
        result = validate_axis_pack_run(
            pack_path=args.pack,
            expected_axis_pack_sha256=args.expected_axis_pack_sha256,
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
    else:
        result = validate_run(
            view_path=args.view,
            expected_view_sha256=args.expected_view_sha256,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
