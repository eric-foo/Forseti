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
    build_axis_consolidated_view,
    validate_axis_consolidated_view,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--spec", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--view", type=Path, required=True)
    validate_parser.add_argument("--expected-view-sha256", required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build_run(spec_path=args.spec, output_path=args.output)
    else:
        result = validate_run(
            view_path=args.view,
            expected_view_sha256=args.expected_view_sha256,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
