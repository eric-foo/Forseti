#!/usr/bin/env python3
"""Run one immutable, progress-visible Codex provider attempt; never publish it."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from provider_attempts import reserve_provider_attempt  # noqa: E402
from provider_execution import execute_provider_attempt  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-schema", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", choices=("none", "minimal", "low", "medium", "high", "xhigh"), required=True)
    parser.add_argument("--timeout-seconds", type=float, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be finite and positive")
    if not args.prompt_file.is_file() or not args.output_schema.is_file() or not args.worktree.is_dir():
        parser.error("prompt, schema, and worktree must exist")
    executable = shutil.which("codex")
    if executable is None:
        parser.error("codex executable not found")
    reserved = reserve_provider_attempt(attempt_root=args.attempt_root, attempt_id=args.attempt_id)
    attempt_dir = Path(reserved["attempt_dir"])
    command = [
        executable, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--json", "--sandbox", "read-only", "-C", str(args.worktree),
        "--model", args.model, "--config", f'model_reasoning_effort="{args.reasoning_effort}"',
        "--output-schema", str(args.output_schema),
        "--output-last-message", str(attempt_dir / "response.json"), "-",
    ]
    print(f"FORSETI_PROVIDER_ATTEMPT_STARTED {args.attempt_id}; limit={args.timeout_seconds}s", file=sys.stderr, flush=True)
    receipt = execute_provider_attempt(
        command=command, prompt_path=args.prompt_file, attempt_dir=attempt_dir,
        timeout_seconds=args.timeout_seconds, response_schema_path=args.output_schema,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["outcome"] == "PROCESS_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
