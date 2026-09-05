#!/usr/bin/env python3
"""Run one immutable, progress-visible Codex provider attempt; never publish it."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from provider_attempts import reserve_provider_attempt  # noqa: E402
from provider_execution import execute_provider_attempt  # noqa: E402


# These override the sign-in or provider route independently of user config.
# Never log their values or silently remove them and change the caller's intent.
AUTH_ROUTE_OVERRIDES = (
    "OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_BASE_URL",
)
CHATGPT_CONFIG = ("cli_auth_credentials_store=\"file\"", "model_provider=\"openai\"")


def _local_codex_check(executable: str, arguments: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    # No prompt or model call. Bound diagnostics independently of generation.
    try:
        return subprocess.run(
            [executable, *arguments], env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        # Native diagnostic output can contain credential fragments.
        raise ValueError(f"Codex local check failed ({type(exc).__name__}); check the selected installation and execution permissions") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-schema", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex-executable", type=Path, required=True,
                        help="Absolute path to the selected Codex executable; never search PATH")
    parser.add_argument("--require-chatgpt", action="store_true",
                        help="Require file-backed ChatGPT sign-in; reject API or unknown authentication before generation")
    # Owner's standing launch rule; reject before reservation or provider access.
    parser.add_argument("--reasoning-effort", choices=("high",), default="high")
    parser.add_argument("--timeout-seconds", type=float, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be finite and positive")
    if not args.prompt_file.is_file() or not args.output_schema.is_file() or not args.worktree.is_dir():
        parser.error("prompt/schema must be accessible files and worktree an accessible directory")
    if not args.codex_executable.is_absolute() or not args.codex_executable.is_file():
        parser.error("--codex-executable must name an existing absolute executable path; no PATH fallback")
    executable = str(args.codex_executable.resolve())
    # Windows batch shims introduce an extra shell and installation selection.
    if args.codex_executable.suffix.lower() in (".cmd", ".bat"):
        parser.error("--codex-executable must select the native executable, not a .cmd/.bat shim")
    for label, source in (("prompt", args.prompt_file), ("schema", args.output_schema)):
        try:
            with source.open("rb") as handle:
                handle.read(1)
        except OSError:
            parser.error(f"{label} is unreadable in this execution context; use accessible run files")
    env = dict(os.environ)
    config: list[str] = []
    metadata = {"authentication_policy": "chatgpt_only" if args.require_chatgpt else "caller_managed"}
    if args.require_chatgpt:
        conflicts = [name for name in AUTH_ROUTE_OVERRIDES if env.get(name)]
        if conflicts:
            parser.error("subscription-only launch rejects credential/endpoint overrides: " + ", ".join(conflicts))
        # Pin the same store and home for the read-only check and execution.
        env["CODEX_HOME"] = str(Path(env.get("CODEX_HOME") or Path.home() / ".codex").resolve())
        config = [part for value in CHATGPT_CONFIG for part in ("--config", value)]
    try:
        version = _local_codex_check(executable, ["--version"], env)
        if version.returncode or not re.fullmatch(r"codex-cli \d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version.stdout.strip()):
            raise ValueError("selected executable did not report a Codex CLI version")
        metadata["codex_version"] = version.stdout.strip()
        if args.require_chatgpt:
            status = _local_codex_check(executable, [*config, "login", "status"], env)
            if status.returncode or (status.stdout + status.stderr).strip() != "Logged in using ChatGPT":
                raise ValueError("ChatGPT authentication was not verified; check file-backed sign-in in this execution context (no generation launched)")
            metadata["authentication_observed"] = "chatgpt"
            # Enforce again inside Codex to close credential changes after status.
            config += ["--config", 'forced_login_method="chatgpt"']
        reserved = reserve_provider_attempt(attempt_root=args.attempt_root, attempt_id=args.attempt_id)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    attempt_dir = Path(reserved["attempt_dir"])
    command = [
        executable, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--json", "--sandbox", "read-only", "-C", str(args.worktree),
        "--model", args.model, "--config", f'model_reasoning_effort="{args.reasoning_effort}"',
        *config,
        "--output-schema", str(args.output_schema),
        "--output-last-message", str(attempt_dir / "response.json"), "-",
    ]
    print(f"FORSETI_PROVIDER_ATTEMPT_STARTED {args.attempt_id}; limit={args.timeout_seconds}s", file=sys.stderr, flush=True)
    try:
        receipt = execute_provider_attempt(
            command=command, prompt_path=args.prompt_file, attempt_dir=attempt_dir,
            timeout_seconds=args.timeout_seconds, response_schema_path=args.output_schema,
            env=env, launch_metadata=metadata,
        )
    except OSError:
        parser.error(f"execution file access failed; inspect preserved attempt {attempt_dir}; do not retry its ID")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["outcome"] == "PROCESS_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
