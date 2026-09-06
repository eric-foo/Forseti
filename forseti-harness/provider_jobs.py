"""Bounded recovery of immutable provider attempts; never semantic acceptance."""
from __future__ import annotations

import contextlib
import json
import os
import re
import time
from pathlib import Path

from harness_utils import hash_file


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")


@contextlib.contextmanager
def _lock(path, *, wait_seconds=0):
    """OS-owned lock; briefly serialize budget claims, reject duplicate jobs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if not handle.tell():
            handle.write(b"0"); handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            acquire = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            release = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            acquire = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            release = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        deadline = time.monotonic() + wait_seconds
        while True:
            try:
                acquire()
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ValueError("provider job or retry budget is already in use") from None
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        try:
            yield
        finally:
            release()


def transient_failure(receipt, events, stderr):
    """Recognize provider diagnostics only, never answer text or generic timeouts."""
    if receipt.get("outcome") not in {"PROCESS_FAILED", "TIMED_OUT"}:
        return None
    messages = []
    for line in events.splitlines():
        try:
            row = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(row, dict):
            continue
        # A timeout can coexist with completed answers. Preserve those for the
        # existing validator-owned recovery path instead of paying for another
        # generation because an earlier reconnect warning happened to exist.
        if row.get("type") == "turn.completed" or (
            row.get("type") == "item.completed"
            and isinstance(row.get("item"), dict)
            and row["item"].get("type") == "agent_message"
        ):
            return None
        if row.get("type") == "error":
            messages.append(row.get("message"))
        elif row.get("type") == "turn.failed" and isinstance(row.get("error"), dict):
            messages.append(row["error"].get("message"))
    if messages and all(message in {
        "Selected model is at capacity. Please try a different model.",
        "Selected model is at capacity.",
    } for message in messages):
        return "capacity"
    if not messages and re.search(
        r"(?m)^\d{4}-\d\d-\d\dT\S+\s+WARN\s+codex_core::responses_retry: "
        r"stream disconnected - retrying sampling request[^\n]*"
        r"sampling_error=stream disconnected before completion: WebSocket protocol error: "
        r"Connection reset without closing handshake\s*$", stderr,
    ):
        return "connection_reset"
    return None


def _check_attempt(path, binding):
    receipt = _read(path / "execution_receipt.json")
    command = receipt.get("command", [])
    if not command or command[0] != binding["codex_executable"]:
        raise ValueError("provider attempt executable changed")
    for option, key in (("--model", "model"), ("-C", "worktree")):
        if command.count(option) != 1 or command[command.index(option)+1] != binding[key]:
            raise ValueError("provider attempt launch binding changed")
    for name, key in (("prompt", "prompt_sha256"), ("schema", "response_schema_sha256")):
        if receipt.get(key) != binding[name + "_sha256"]:
            raise ValueError("provider attempt input binding changed")
    if receipt.get("launch_metadata", {}).get("authentication_observed") != "chatgpt":
        raise ValueError("provider attempt lacks subscription authentication evidence")
    for name, key in (("events.jsonl", "events_sha256"), ("stderr.log", "stderr_sha256")):
        if hash_file(path / name) != receipt.get(key):
            raise ValueError("provider attempt diagnostic bytes changed")
    if receipt.get("outcome") == "PROCESS_COMPLETED" and hash_file(path / "response.json") != receipt.get("response_sha256"):
        raise ValueError("provider response bytes changed")
    return receipt


def _claim_retry(root, limit, job, attempt_id):
    with _lock(root / "budget.lock", wait_seconds=5):
        policy = root / "policy.json"
        expected = {"retry_limit": limit}
        if policy.exists():
            if _read(policy) != expected:
                raise ValueError("run retry budget changed")
        else:
            _new(policy, expected)
        claims = list(root.glob("claim-*.json"))
        claim = {"job": str(job.resolve()), "attempt_id": attempt_id}
        if any(_read(path) == claim for path in claims):
            return
        if len(claims) >= limit:
            raise ValueError("run retry budget exhausted")
        _new(root / f"claim-{len(claims)+1:06d}.json", claim)


def run_provider_job(*, job_dir: Path, attempt_root: Path, binding: dict,
                     launch, retry_budget_dir: Path, run_retry_limit: int,
                     max_retries: int = 1, retry_delay_seconds: float = 10,
                     sleep=time.sleep):
    """Return process completion or a failed job; callers still validate meaning.

    `launch(attempt_id)` runs the existing subscription-only runner. A crash
    after launch intent with no completion receipt is unknown and never retried.
    Retry claims count even when usage is missing or a later launch is refused.
    """
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in (max_retries, run_retry_limit)):
        raise ValueError("retry limits must be nonnegative integers")
    if not isinstance(retry_delay_seconds, (int, float)) or not 0 <= retry_delay_seconds <= 60:
        raise ValueError("retry delay must be finite and between zero and 60 seconds")
    policy = dict(binding=binding, max_retries=max_retries, run_retry_limit=run_retry_limit,
        retry_budget_dir=str(retry_budget_dir.resolve()), retry_delay_seconds=retry_delay_seconds,
        attempt_root=str(attempt_root.resolve()))
    with _lock(job_dir / "job.lock"):
        contract = job_dir / "binding.json"
        if contract.exists():
            if _read(contract) != policy:
                raise ValueError("provider job binding changed")
        else:
            _new(contract, policy)
        for index in range(max_retries + 1):
            for kind in ("codex", "runner"):
                path = binding["codex_executable"] if kind == "codex" else binding["runner_path"]
                if hash_file(Path(path)) != binding[kind + "_sha256"]:
                    raise ValueError("provider execution source changed")
            for kind in ("prompt", "schema"):
                if hash_file(Path(binding[kind + "_path"])) != binding[kind + "_sha256"]:
                    raise ValueError("provider job input changed")
            aid = job_dir.name + f"-attempt-{index+1:03d}"
            attempt = attempt_root / aid
            intent = job_dir / f"launch-{index+1:03d}.json"
            if (attempt / "execution_receipt.json").exists() and (
                not intent.exists() or _read(intent) != {"attempt_id": aid}
            ):
                raise ValueError("existing provider attempt does not belong to this job")
            if not (attempt / "execution_receipt.json").exists():
                if attempt.exists():
                    raise ValueError("provider launch outcome unknown; inspect preserved attempt before recovery")
                if intent.exists():
                    # Report absence, not a proven pre-launch refusal: the callable
                    # or missing artifacts cannot establish that nothing generated.
                    # Keep the intent and budget claim; never infer safe relaunch.
                    raise ValueError("provider launch intent exists but its attempt directory is missing; execution is unconfirmed; preserve the launch record and inspect launch diagnostics before recovery")
                if index:
                    _claim_retry(retry_budget_dir, run_retry_limit, job_dir, aid)
                    sleep(retry_delay_seconds)
                    for kind in ("codex", "runner"):
                        source_path = binding["codex_executable"] if kind == "codex" else binding["runner_path"]
                        if hash_file(Path(source_path)) != binding[kind + "_sha256"]:
                            raise ValueError("provider execution source changed during retry delay")
                    for kind in ("prompt", "schema"):
                        if hash_file(Path(binding[kind + "_path"])) != binding[kind + "_sha256"]:
                            raise ValueError("provider job input changed during retry delay")
                _new(intent, {"attempt_id": aid})
                launch(aid)
                if not (attempt / "execution_receipt.json").exists():
                    raise ValueError("provider launch returned no execution receipt; authentication or launch failure is not retryable")
            receipt = _check_attempt(attempt, binding)
            if receipt["outcome"] == "PROCESS_COMPLETED":
                return {"status": "PROCESS_COMPLETED_NOT_VALIDATED", "attempt_dir": str(attempt),
                    "execution_receipt": receipt, "attempt_count": index+1}
            cause = transient_failure(receipt, (attempt / "events.jsonl").read_text(encoding="utf-8"),
                (attempt / "stderr.log").read_text(encoding="utf-8"))
            if cause is None or index == max_retries:
                return {"status": "JOB_FAILED", "attempt_dir": str(attempt), "cause": cause or "unclassified",
                    "attempt_count": index+1, "execution_receipt": receipt}
        raise AssertionError("unreachable provider job state")
