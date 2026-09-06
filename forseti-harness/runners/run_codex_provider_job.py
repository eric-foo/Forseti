#!/usr/bin/env python3
"""Resume one subscription-only provider job with a finite shared retry budget."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))
from harness_utils import hash_file
from provider_jobs import run_provider_job
from runners.run_codex_provider_attempt import preloaded_context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("job-dir", "attempt-root", "retry-budget-dir", "prompt-file", "output-schema", "worktree", "codex-executable"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", choices=["high"], default="high")
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--run-retry-limit", type=int, required=True)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--retry-delay-seconds", type=float, default=10)
    parser.add_argument("--preload-context", type=Path, action="append", default=[],
                        help="Required context supplied verbatim to a job without shell tools; repeat per file")
    args = parser.parse_args()
    native = HARNESS_ROOT / "runners/run_codex_provider_attempt.py"
    try:
        binding = dict(prompt_path=str(args.prompt_file.resolve(strict=True)), prompt_sha256=hash_file(args.prompt_file),
            schema_path=str(args.output_schema.resolve(strict=True)), schema_sha256=hash_file(args.output_schema),
            model=args.model, reasoning_effort=args.reasoning_effort, timeout_seconds=args.timeout_seconds,
            worktree=str(args.worktree.resolve(strict=True)), codex_executable=str(args.codex_executable.resolve(strict=True)),
            codex_sha256=hash_file(args.codex_executable), runner_path=str(native),runner_sha256=hash_file(native))
        context, context_files = preloaded_context(args.preload_context)
        if context:
            binding["preloaded_context_sha256"] = hashlib.sha256(context.encode("utf-8")).hexdigest()
            binding["preloaded_context_files"] = context_files
        def launch(aid):
            command = [sys.executable, str(native), "--attempt-root", str(args.attempt_root), "--attempt-id", aid,
                "--prompt-file", binding["prompt_path"], "--output-schema", binding["schema_path"],
                "--worktree", binding["worktree"], "--codex-executable", binding["codex_executable"],
                "--model", args.model, "--reasoning-effort", "high", "--require-chatgpt",
                "--timeout-seconds", str(args.timeout_seconds)]
            if context:
                command += ["--expected-context-sha256", binding["preloaded_context_sha256"]]
                for record in context_files:
                    command += ["--preload-context", record["path"]]
            subprocess.run(command, check=False)
        result = run_provider_job(job_dir=args.job_dir, attempt_root=args.attempt_root, binding=binding,
            launch=launch, retry_budget_dir=args.retry_budget_dir, run_retry_limit=args.run_retry_limit,
            max_retries=args.max_retries, retry_delay_seconds=args.retry_delay_seconds)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PROCESS_COMPLETED_NOT_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
