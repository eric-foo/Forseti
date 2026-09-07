"""Operational measurements, separate from Forseti product records.

Tokens are provider observations, never estimates from text length. Cache and
reasoning counters are breakdowns, not extra tokens to add to inclusive totals.
Only metadata and numeric usage are retained; never requests, credentials or
model response text. A broken measurement must not change product behavior.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from uuid import uuid4

TOKEN_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens", "total_tokens",
)
_ACTIVE: ContextVar[RunMeasurement | None] = ContextVar("efficiency_run", default=None)


def _count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _numeric_usage(value: Any) -> dict:
    """Allowlist provider counters; do not copy arbitrary envelope contents."""
    if not isinstance(value, dict):
        return {}
    allowed = set(TOKEN_FIELDS) | {
        "cache_read_input_tokens", "cache_creation_input_tokens",
        "input_tokens_details", "output_tokens_details", "cached_tokens",
        "reasoning_tokens", "cache_creation", "ephemeral_5m_input_tokens",
        "ephemeral_1h_input_tokens",
    }
    return {
        key: _numeric_usage(item) if isinstance(item, dict) else item
        for key, item in value.items()
        if key in allowed and (isinstance(item, dict) or _count(item) is not None)
    }


def unknown_usage(reason: str) -> dict:
    return {"coverage": "unknown", **dict.fromkeys(TOKEN_FIELDS),
            "issues": [reason], "raw_usage": {}}


def normalize_usage(provider: str, usage: Any) -> dict:
    """Normalize observed counters without fabricating absent breakdowns.

    OpenAI/Codex input includes cached input; output includes reasoning. Anthropic
    input excludes cache reads and writes, which must be observed to form a total.
    Missing optional breakdowns do not invalidate an otherwise observed total.
    """
    result = unknown_usage("missing_or_invalid_usage")
    result["raw_usage"] = _numeric_usage(usage)
    if not isinstance(usage, dict):
        return result
    inp, out = _count(usage.get("input_tokens")), _count(usage.get("output_tokens"))
    cached = written = reasoning = None
    if provider in {"openai_responses", "codex_exec", "codex_rollout"}:
        if provider == "openai_responses":
            details = usage.get("input_tokens_details")
            cached = _count(details.get("cached_tokens")) if isinstance(details, dict) else None
            details = usage.get("output_tokens_details")
            reasoning = _count(details.get("reasoning_tokens")) if isinstance(details, dict) else None
        else:
            cached = _count(usage.get("cached_input_tokens"))
            written = _count(usage.get("cache_write_input_tokens"))
            reasoning = _count(usage.get("reasoning_output_tokens"))
    elif provider == "anthropic_messages":
        cached = _count(usage.get("cache_read_input_tokens"))
        written = _count(usage.get("cache_creation_input_tokens"))
        inp = inp + cached + written if None not in (inp, cached, written) else None
    else:
        result["issues"] = ["unsupported_usage_provider"]
        return result
    result.update(input_tokens=inp, output_tokens=out, cached_input_tokens=cached,
                  cache_write_input_tokens=written, reasoning_output_tokens=reasoning)
    problems = []
    if inp is None or out is None:
        problems.append("missing_or_invalid_total_components")
    if inp is not None and cached is not None and cached > inp:
        problems.append("cached_input_exceeds_input")
    if inp is not None and written is not None and written > inp:
        problems.append("cache_write_exceeds_input")
    if out is not None and reasoning is not None and reasoning > out:
        problems.append("reasoning_exceeds_output")
    total = inp + out if inp is not None and out is not None else None
    if "total_tokens" in usage and _count(usage["total_tokens"]) != total:
        problems.append("provider_total_mismatch")
    # A present malformed counter is unknown, not an absent optional breakdown.
    def invalid_numbers(value: dict) -> bool:
        for key, item in value.items():
            if key.endswith("tokens") and key not in {"input_tokens_details", "output_tokens_details"}:
                if _count(item) is None:
                    return True
            if isinstance(item, dict) and invalid_numbers(item):
                return True
        return False
    if invalid_numbers(usage):
        problems.append("invalid_usage_counter")
    result.update(coverage="unknown" if problems else "complete",
                  total_tokens=None if problems else total, issues=problems)
    return result


def aggregate_usage(attempts: list[dict]) -> dict:
    observed = {key: sum(a.get("usage", {}).get(key) or 0 for a in attempts) for key in TOKEN_FIELDS}
    issues = [f"attempt_{index}:{issue}" for index, attempt in enumerate(attempts)
              for issue in attempt.get("usage", {}).get("issues", [])]
    complete = bool(attempts) and all(a.get("usage", {}).get("coverage") == "complete" for a in attempts)
    if not attempts:
        issues.append("no_observed_model_usage")
    totals = {key: observed[key] if complete and all(a["usage"].get(key) is not None for a in attempts) else None
              for key in TOKEN_FIELDS}
    return {"coverage": "complete" if complete else "unknown", **totals,
            "observed_totals": observed, "issues": issues}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def current_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent,
            text=True, stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def make_record(*, workflow: str, workload_id: str, configuration: dict,
                revision: str | None, elapsed_seconds: float, outcome: str,
                quality: dict, attempts: list[dict], **metadata: Any) -> dict:
    if isinstance(elapsed_seconds, bool) or not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must be finite and nonnegative")
    if outcome not in {"success", "failed"}:
        raise ValueError("invalid outcome")
    result = {"schema_version": 1, "run_id": str(uuid4()), "workflow": workflow,
              "workload_id": workload_id, "configuration": configuration,
              "revision": revision, "elapsed_seconds": elapsed_seconds,
              "outcome": outcome, "quality": quality, "attempts": attempts,
              "usage": aggregate_usage(attempts)}
    if set(metadata) & set(result) - {"run_id"}:
        raise ValueError("metadata cannot overwrite measured fields")
    result.update(metadata)
    return result


def write_record(record: dict, output_dir: Path) -> Path:
    """Exclusive single-run file; interrupted/invalid JSON is rejected by readers."""
    body = json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{record['run_id']}.json"
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def current_measurement() -> RunMeasurement | None:
    return _ACTIVE.get()


class RunMeasurement:
    """One outer operation; inner request/parser stages reuse its active context."""
    def __init__(self, workflow: str, workload_id: str, configuration: dict, *,
                 output_dir: Path | None = None, revision: str | None = None):
        self.workflow, self.workload_id, self.configuration = workflow, workload_id, configuration
        default = Path(__file__).resolve().parent / "memory" / "logs" / "efficiency"
        self.output_dir = Path(output_dir or os.environ.get("FORSETI_EFFICIENCY_DIR", default))
        self.revision = revision or os.environ.get("FORSETI_EFFICIENCY_REVISION") or current_revision()
        self.attempts: list[dict] = []
        self.stages: dict[str, float] = {}
        self.quality = {"status": "unmeasured", "oracle": None, "output_fingerprint": None}
        self.metadata: dict = {}
        self.errors: list[str] = []
        self.record: dict | None = None
        self.path: Path | None = None

    def __enter__(self):
        self.started_at = utc_now()
        self.started = time.perf_counter()
        self._token = _ACTIVE.set(self)
        return self

    def add_attempt(self, provider: str, model: str, elapsed_seconds: float,
                    usage: dict, outcome: str = "success") -> None:
        self.attempts.append({"attempt_id": str(uuid4()), "provider": provider, "model": model,
                              "elapsed_seconds": elapsed_seconds, "usage": usage, "outcome": outcome})

    def add_stage(self, name: str, seconds: float) -> None:
        self.stages[name] = self.stages.get(name, 0.0) + seconds

    @contextmanager
    def stage(self, name: str):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.add_stage(name, time.perf_counter() - started)

    def set_quality(self, status: str, oracle: str, output_fingerprint: str | None = None) -> None:
        if status not in {"passed", "failed", "unmeasured"}:
            raise ValueError("invalid quality status")
        self.quality = {"status": status, "oracle": oracle, "output_fingerprint": output_fingerprint}

    def annotate(self, **metadata: Any) -> None:
        self.metadata.update(metadata)

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"efficiency measurement unavailable: {message}", file=sys.stderr)

    def __exit__(self, exc_type, exc, tb):
        elapsed = time.perf_counter() - self.started
        _ACTIVE.reset(self._token)
        try:
            self.record = make_record(
                workflow=self.workflow, workload_id=self.workload_id, configuration=self.configuration,
                revision=self.revision, elapsed_seconds=elapsed,
                outcome="failed" if exc_type else "success", quality=self.quality, attempts=self.attempts,
                started_at=self.started_at, ended_at=utc_now(), stages=self.stages,
                measurement_errors=list(self.errors),
                error_type=exc_type.__name__ if exc_type else None, **self.metadata,
            )
            if self.errors:
                self.record["usage"]["coverage"] = "unknown"
                self.record["usage"]["issues"].extend(self.errors)
            self.path = write_record(self.record, self.output_dir)
        except Exception as failure:  # operational logging never masks product failure/success
            self.error(f"record_write:{type(failure).__name__}")
        return False
