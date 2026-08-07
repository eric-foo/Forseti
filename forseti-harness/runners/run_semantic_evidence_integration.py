"""Prepare and compile one agent-run semantic evidence integration job."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judgment.semantic_evidence_integration import (  # noqa: E402
    SemanticIntegrationError,
    build_batch_prompts,
    build_bundle,
    build_reconciliation_prompt,
    finalize_view,
    validate_batch_responses,
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
    max_batch_chars: int,
) -> dict[str, Any]:
    source = _load_object(source_path)
    _verify_sources(source, repo_root=repo_root)
    bundle = build_bundle(source, max_batch_chars=max_batch_chars)
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
    return {
        "status": "SEMANTIC_BATCH_JUDGMENT_REQUIRED",
        "bundle_sha256": bundle["bundle_sha256"],
        "corpus_sha256": bundle["corpus_sha256"],
        "batch_count": len(prompts),
        "admitted_evidence_unit_count": bundle["coverage_denominator"]["admitted_evidence_unit_count"],
        "bundle_out": str(bundle_out),
        "prompt_dir": str(prompt_dir),
        "model_api_calls": 0,
    }


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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare-batches")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--repo-root", type=Path, required=True)
    prepare.add_argument("--bundle-out", type=Path, required=True)
    prepare.add_argument("--prompt-dir", type=Path, required=True)
    prepare.add_argument("--max-batch-chars", type=int, default=80_000)

    submit = sub.add_parser("submit-batches")
    submit.add_argument("--bundle", type=Path, required=True)
    submit.add_argument("--response", type=Path, action="append", required=True)
    submit.add_argument("--compiled-out", type=Path, required=True)

    reconcile = sub.add_parser("prepare-reconciliation")
    reconcile.add_argument("--bundle", type=Path, required=True)
    reconcile.add_argument("--compiled", type=Path, required=True)
    reconcile.add_argument("--prompt-out", type=Path, required=True)

    finish = sub.add_parser("finalize")
    finish.add_argument("--bundle", type=Path, required=True)
    finish.add_argument("--compiled", type=Path, required=True)
    finish.add_argument("--response", type=Path, required=True)
    finish.add_argument("--view-out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare-batches":
            result = prepare_batches(
                source_path=args.source,
                repo_root=args.repo_root,
                bundle_out=args.bundle_out,
                prompt_dir=args.prompt_dir,
                max_batch_chars=args.max_batch_chars,
            )
        elif args.command == "submit-batches":
            result = submit_batches(
                bundle_path=args.bundle,
                response_paths=args.response,
                compiled_out=args.compiled_out,
            )
        elif args.command == "prepare-reconciliation":
            result = prepare_reconciliation(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                prompt_out=args.prompt_out,
            )
        else:
            result = finalize(
                bundle_path=args.bundle,
                compiled_path=args.compiled,
                response_path=args.response,
                view_out=args.view_out,
            )
    except (OSError, ValueError, json.JSONDecodeError, SemanticIntegrationError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
