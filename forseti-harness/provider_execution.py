"""Run one external model attempt; stage validators still own acceptance."""
from __future__ import annotations

import json
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, BinaryIO, Sequence

from harness_utils import hash_file, utc_now_z_microseconds
from provider_attempts import codex_usage_from_events


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _stop_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        # Target only the process this invocation launched, including its children.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False, timeout=5,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def execute_provider_attempt(
    *, command: Sequence[str], prompt_path: Path, attempt_dir: Path,
    timeout_seconds: float, stderr_echo: BinaryIO | None = None,
    response_schema_path: Path | None = None,
) -> dict[str, Any]:
    """Preserve live streams, bound the whole process attempt, and never publish.

    The child writes directly to files: no pipe buffer can hide a reconnect or
    deadlock while the parent waits. The deadline includes launch and input read,
    and neither client retries nor emitted events reset it.
    """
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must contain nonempty string arguments")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    if not attempt_dir.is_dir():
        raise ValueError("attempt_dir must be reserved before execution")
    for source in (prompt_path, response_schema_path):
        if source is not None and not source.is_file():
            raise ValueError(f"input file does not exist: {source}")
    paths = {name: attempt_dir / name for name in (
        "execution_started.json", "execution_receipt.json", "events.jsonl",
        "stderr.log", "response.json",
    )}
    for target in paths.values():
        if target.exists():
            raise ValueError(f"refusing to overwrite existing output: {target}")
    start = {
        "schema_version": "forseti_provider_execution_started_v1",
        "command": list(command), "started_at": utc_now_z_microseconds(),
        "timeout_seconds": timeout_seconds,
        "prompt_path": str(prompt_path), "prompt_sha256": hash_file(prompt_path),
        "prompt_bytes": prompt_path.stat().st_size,
        "response_schema_path": str(response_schema_path) if response_schema_path else None,
        "response_schema_sha256": hash_file(response_schema_path) if response_schema_path else None,
    }
    # Exclusive creation is the launch lock when two callers share a reservation.
    _write_new_json(paths["execution_started.json"], start)
    started = time.monotonic()
    deadline = started + timeout_seconds
    echo = stderr_echo if stderr_echo is not None else sys.stderr.buffer
    creation = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    outcome, exit_code, error = "LAUNCH_FAILED", None, None
    process: subprocess.Popen[bytes] | None = None
    interrupted: BaseException | None = None
    with (prompt_path.open("rb") as prompt,
          paths["events.jsonl"].open("xb") as stdout,
          paths["stderr.log"].open("xb") as stderr,
          paths["stderr.log"].open("rb") as live_stderr):
        def mirror() -> None:
            chunk = live_stderr.read()
            if chunk:
                echo.write(chunk)
                echo.flush()

        try:
            process = subprocess.Popen(list(command), stdin=prompt, stdout=stdout, stderr=stderr, **creation)
            while process.poll() is None:
                mirror()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    outcome = "TIMED_OUT"
                    _stop_process_tree(process)
                    break
                try:
                    process.wait(timeout=min(0.1, remaining))
                except subprocess.TimeoutExpired:
                    pass
            exit_code = process.returncode
            if outcome != "TIMED_OUT":
                outcome = "PROCESS_COMPLETED" if exit_code == 0 else "PROCESS_FAILED"
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
            outcome = "EXECUTION_ERROR" if process is not None else "LAUNCH_FAILED"
            if process is not None:
                try:
                    _stop_process_tree(process)
                    exit_code = process.returncode
                except Exception as cleanup_error:
                    error += f"; cleanup failed: {cleanup_error}"
            if not isinstance(exc, Exception):
                interrupted = exc
        finally:
            mirror()
    wall_seconds = time.monotonic() - started
    stderr_text = paths["stderr.log"].read_text(encoding="utf-8", errors="replace")
    try:
        usage = codex_usage_from_events(paths["events.jsonl"])
        usage_status, usage_error = "COMPLETED_TURN_REPORTED", None
    except ValueError as exc:
        usage, usage_status, usage_error = None, "UNOBSERVED_OR_INCOMPLETE", str(exc)
    inputs_unchanged = hash_file(prompt_path) == start["prompt_sha256"] and (
        response_schema_path is None or hash_file(response_schema_path) == start["response_schema_sha256"]
    )
    if not inputs_unchanged:
        outcome = "INPUT_CHANGED"
    receipt = {
        **start, "schema_version": "forseti_provider_execution_receipt_v1",
        "outcome": outcome, "completed_at": utc_now_z_microseconds(), "exit_code": exit_code,
        "error": error, "wall_seconds": wall_seconds,
        "useful_compute_seconds": None, "useful_compute_seconds_status": "UNOBSERVED",
        "observed_retry_events": stderr_text.count("retrying sampling request"),
        "observed_transport_fallback_events": stderr_text.count("falling back to HTTP"),
        "retry_observation_scope": "recognized Codex stderr messages; not provider request accounting",
        "usage": usage, "usage_status": usage_status, "usage_error": usage_error,
        "usage_scope": "reported completed-turn fields; hidden retry usage is not independently observed",
        "events_sha256": hash_file(paths["events.jsonl"]),
        "stderr_sha256": hash_file(paths["stderr.log"]),
        "response_sha256": hash_file(paths["response.json"]) if paths["response.json"].is_file() else None,
        "response_bytes": paths["response.json"].stat().st_size if paths["response.json"].is_file() else 0,
        "acceptance_status": "NOT_VALIDATED",
    }
    _write_new_json(paths["execution_receipt.json"], receipt)
    if interrupted is not None:
        raise interrupted
    return {**receipt, "execution_receipt_path": str(paths["execution_receipt.json"])}
