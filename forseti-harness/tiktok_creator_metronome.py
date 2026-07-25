"""Durable millisecond logging shared by TikTok creator run entrypoints."""
from __future__ import annotations

import json
import os
import time
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Mapping
from uuid import uuid4

from harness_utils import sha256_bytes


PROBE_JOURNAL_NAME = "tiktok_creator_activity_probe.jsonl"
DIRECT_RUN_JOURNAL_NAME = "tiktok_creator_run_metronome.jsonl"
JOURNAL_NAMES = (PROBE_JOURNAL_NAME, DIRECT_RUN_JOURNAL_NAME)
JOURNAL_SCHEMA_VERSION = "tiktok_creator_activity_probe_v0"
METRONOME_UMBRELLA_NAME = "metronome_activity_log.json"
METRONOME_PROJECTION_KEY = "tiktok_run_journal_projection"
METRONOME_PROJECTION_SCHEMA_VERSION = "tiktok_creator_run_projection_v1"
SUPERVISED_ENV_NAME = "FORSETI_TIKTOK_METRONOME_SUPERVISED"
_FORBIDDEN_KEY_PARTS = (
    "url",
    "body",
    "cookie",
    "token",
    "storage",
    "text",
    "html",
    "dom",
)


class TikTokMetronomeError(RuntimeError):
    """Fail-closed metronome error."""


class TikTokMetronomeJournal:
    def __init__(
        self,
        path: Path,
        *,
        umbrella_path: Path | None = None,
        default_handle: str | None = None,
        monotonic_fn: Callable[[], float] = time.monotonic,
        utc_now_fn: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._stream = path.open("xb")
        self._monotonic_fn = monotonic_fn
        self._utc_now_fn = utc_now_fn
        self._started_monotonic = monotonic_fn()
        self._run_id = uuid4().hex
        self._sequence = 0
        self._closed = False
        self._default_handle = (
            _normalize_handle(default_handle) if default_handle else None
        )
        self._last_blocker_code: str | None = None
        self._umbrella_path = umbrella_path or find_metronome_umbrella(
            path.parent
        )

    @property
    def run_id(self) -> str:
        return self._run_id

    def set_default_handle(self, handle: str) -> None:
        self._default_handle = _normalize_handle(handle)

    def record(
        self,
        event_type: str,
        *,
        handle: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        if self._closed:
            raise TikTokMetronomeError("metronome journal is already closed")
        normalized_handle = (
            _normalize_handle(handle)
            if handle
            else self._default_handle
        )
        row = {
            "schema_version": JOURNAL_SCHEMA_VERSION,
            "run_id": self._run_id,
            "sequence": self._sequence,
            "observed_at_utc": _utc_iso(self._utc_now_fn()),
            "elapsed_ms": int(
                round(
                    max(
                        0.0,
                        self._monotonic_fn() - self._started_monotonic,
                    )
                    * 1000
                )
            ),
            "event_type": event_type,
            "handle_or_none": normalized_handle,
            "details": dict(details or {}),
        }
        validate_metronome_row(row)
        self._stream.write(
            json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._sequence += 1
        if self._umbrella_path is not None:
            refresh_metronome_umbrella(
                self._umbrella_path,
                active_journal_path=self.path,
                refreshed_at_utc=str(row["observed_at_utc"]),
            )

    def record_progress(
        self,
        event: str,
        fields: Mapping[str, object],
    ) -> None:
        raw_handle = fields.get("creator_handle")
        if isinstance(raw_handle, str) and raw_handle.strip():
            self.set_default_handle(raw_handle)
        details: dict[str, object] = {"phase": event}
        for key in (
            "status",
            "decision",
            "reason_code_or_none",
            "completed_count",
            "selected_count",
            "packet_id",
            "record_id_or_none",
            "write_status",
        ):
            value = fields.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                details[key] = value
        self.record("runner_progress", details=details)

    def record_blocker(self, code: str, phase: str) -> None:
        self._last_blocker_code = code
        self.record(
            "runner_blocker",
            details={"code": code, "phase": phase},
        )

    def close_for_exit_code(self, exit_code: int) -> None:
        if self._last_blocker_code == "LOGGED_OUT_SESSION":
            status = "logged_out"
            terminal_reason = "forced_logout_detected"
        elif exit_code == 0:
            status = "complete"
            terminal_reason = "direct_runner_complete"
        else:
            status = "failed"
            terminal_reason = (
                self._last_blocker_code or f"exit_code_{exit_code}"
            )
        self.close(
            status=status,
            terminal_reason=terminal_reason,
            counters={"exit_code": exit_code},
        )

    def close(
        self,
        *,
        status: str,
        terminal_reason: str,
        counters: Mapping[str, int],
    ) -> None:
        if self._closed:
            return
        try:
            self.record(
                "terminal",
                details={
                    "status": status,
                    "terminal_reason": terminal_reason,
                    **dict(counters),
                },
            )
        finally:
            self._stream.close()
            self._closed = True


_ACTIVE_JOURNAL: ContextVar[TikTokMetronomeJournal | None] = ContextVar(
    "tiktok_creator_metronome_active_journal",
    default=None,
)


def activate_metronome(
    journal: TikTokMetronomeJournal,
) -> Token[TikTokMetronomeJournal | None]:
    return _ACTIVE_JOURNAL.set(journal)


def deactivate_metronome(
    token: Token[TikTokMetronomeJournal | None],
) -> None:
    _ACTIVE_JOURNAL.reset(token)


def active_metronome() -> TikTokMetronomeJournal | None:
    return _ACTIVE_JOURNAL.get()


def open_direct_run_metronome(
    output_dir: Path,
    *,
    creator_handle: str | None,
) -> TikTokMetronomeJournal | None:
    if os.environ.get(SUPERVISED_ENV_NAME) == "1":
        return None
    umbrella_path = find_metronome_umbrella(output_dir)
    if umbrella_path is None:
        return None
    return TikTokMetronomeJournal(
        output_dir / DIRECT_RUN_JOURNAL_NAME,
        umbrella_path=umbrella_path,
        default_handle=creator_handle,
    )


def find_metronome_umbrella(start: Path) -> Path | None:
    current = start.resolve()
    for directory in (current, *current.parents):
        candidate = directory / METRONOME_UMBRELLA_NAME
        if candidate.is_file():
            return candidate
    return None


def refresh_metronome_umbrella(
    umbrella_path: Path,
    *,
    active_journal_path: Path | None = None,
    refreshed_at_utc: str | None = None,
) -> dict[str, object]:
    document = json.loads(umbrella_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TikTokMetronomeError(
            "metronome umbrella must contain one JSON object"
        )

    run_root = umbrella_path.parent
    journal_paths = sorted(
        path
        for journal_name in JOURNAL_NAMES
        for path in run_root.rglob(journal_name)
    )
    runs = [
        summarize_metronome_journal(
            path,
            run_root=run_root,
            is_active=(
                active_journal_path is not None
                and path.resolve() == active_journal_path.resolve()
            ),
        )
        for path in journal_paths
    ]
    status_counts: dict[str, int] = {}
    journal_kind_counts: dict[str, int] = {}
    event_count = 0
    logout_detection_count = 0
    for run in runs:
        status = str(run["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
        journal_kind = str(run["journal_kind"])
        journal_kind_counts[journal_kind] = (
            journal_kind_counts.get(journal_kind, 0) + 1
        )
        event_count += int(run["event_count"])
        event_type_counts = run["event_type_counts"]
        assert isinstance(event_type_counts, dict)
        logout_detection_count += int(
            event_type_counts.get("first_logout_detected", 0)
        )
        if (
            run["status"] == "logged_out"
            and event_type_counts.get("first_logout_detected", 0) == 0
        ):
            logout_detection_count += 1

    document.pop("activity_probe_journal_projection", None)
    document[METRONOME_PROJECTION_KEY] = {
        "schema_version": METRONOME_PROJECTION_SCHEMA_VERSION,
        "refreshed_at_utc": (
            refreshed_at_utc or _utc_iso(datetime.now(UTC))
        ),
        "authority": (
            "Per-run TikTok metronome JSONL files are the authoritative "
            "millisecond event logs; this field is an atomically refreshed "
            "projection."
        ),
        "run_root": str(run_root.resolve()),
        "aggregate": {
            "run_count": len(runs),
            "event_count": event_count,
            "logout_detection_count": logout_detection_count,
            "journal_kind_counts": dict(sorted(journal_kind_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "runs": runs,
    }
    _atomic_write_json(umbrella_path, document)
    return document


def summarize_metronome_journal(
    path: Path,
    *,
    run_root: Path,
    is_active: bool = False,
) -> dict[str, object]:
    raw_bytes = path.read_bytes()
    rows: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(raw_bytes.splitlines(), start=1):
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise TikTokMetronomeError(
                f"invalid metronome journal JSON at {path}:{line_number}"
            ) from exc
        if not isinstance(row, dict):
            raise TikTokMetronomeError(
                f"metronome journal row is not an object at {path}:{line_number}"
            )
        validate_metronome_row(row)
        rows.append(row)
    if not rows:
        raise TikTokMetronomeError(f"metronome journal is empty: {path}")

    run_ids = {str(row["run_id"]) for row in rows}
    if len(run_ids) != 1:
        raise TikTokMetronomeError(
            f"metronome journal contains multiple run ids: {path}"
        )
    sequences = [int(row["sequence"]) for row in rows]
    if sequences != list(range(len(rows))):
        raise TikTokMetronomeError(
            f"metronome journal sequence is not contiguous: {path}"
        )

    event_type_counts: dict[str, int] = {}
    creator_handles: list[str] = []
    terminal_details: dict[str, object] | None = None
    current_handle: str | None = None
    run_kind: str | None = None
    creator_intent: str | None = None
    for row in rows:
        event_type = str(row["event_type"])
        event_type_counts[event_type] = (
            event_type_counts.get(event_type, 0) + 1
        )
        handle = row.get("handle_or_none")
        if isinstance(handle, str):
            current_handle = handle
        details = row["details"]
        assert isinstance(details, dict)
        if event_type == "run_started":
            raw_handles = details.get("creator_handles")
            if isinstance(raw_handles, list):
                creator_handles = [
                    str(value) for value in raw_handles if isinstance(value, str)
                ]
            raw_kind = details.get("run_kind")
            if isinstance(raw_kind, str):
                run_kind = raw_kind
            raw_intent = details.get("creator_intent")
            if isinstance(raw_intent, str):
                creator_intent = raw_intent
        elif event_type == "terminal":
            terminal_details = details

    if terminal_details is None:
        status = "running" if is_active else "interrupted_without_terminal"
        terminal_reason: object = None
        counters: dict[str, int] = {}
    else:
        status = str(terminal_details.get("status") or "unknown")
        terminal_reason = terminal_details.get("terminal_reason")
        counters = {
            key: int(value)
            for key, value in terminal_details.items()
            if key not in {"status", "terminal_reason"}
            and isinstance(value, int)
        }

    journal_kind = (
        "activity_probe"
        if path.name == PROBE_JOURNAL_NAME
        else "direct_runner"
    )
    return {
        "journal_path": path.relative_to(run_root).as_posix(),
        "journal_kind": journal_kind,
        "journal_sha256": sha256_bytes(raw_bytes),
        "journal_byte_length": len(raw_bytes),
        "run_id": next(iter(run_ids)),
        "run_kind_or_none": run_kind,
        "creator_intent_or_none": creator_intent,
        "creator_handles": creator_handles,
        "first_observed_at_utc": str(rows[0]["observed_at_utc"]),
        "last_observed_at_utc": str(rows[-1]["observed_at_utc"]),
        "last_sequence": sequences[-1],
        "event_count": len(rows),
        "event_type_counts": dict(sorted(event_type_counts.items())),
        "current_handle_or_none": current_handle,
        "status": status,
        "terminal_reason_or_none": terminal_reason,
        "terminal_counters": counters,
    }


def validate_metronome_row(row: Mapping[str, object]) -> None:
    if row.get("schema_version") != JOURNAL_SCHEMA_VERSION:
        raise ValueError("metronome journal schema version is invalid")
    if not isinstance(row.get("run_id"), str) or not row["run_id"]:
        raise ValueError("metronome journal run id is required")
    if not isinstance(row.get("sequence"), int):
        raise ValueError("metronome journal sequence is invalid")
    if not isinstance(row.get("elapsed_ms"), int) or row["elapsed_ms"] < 0:
        raise ValueError("metronome journal elapsed_ms is invalid")
    if not isinstance(row.get("event_type"), str) or not row["event_type"]:
        raise ValueError("metronome journal event type is required")
    handle = row.get("handle_or_none")
    if handle is not None and (
        not isinstance(handle, str) or _normalize_handle(handle) != handle
    ):
        raise ValueError("metronome journal handle is invalid")
    details = row.get("details")
    if not isinstance(details, Mapping):
        raise ValueError("metronome journal details must be an object")
    _reject_forbidden_material(details)
    json.dumps(row, ensure_ascii=False, allow_nan=False)


def _reject_forbidden_material(value: object, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError(
                    f"metronome journal contains forbidden field at {path}.{key}"
                )
            _reject_forbidden_material(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_material(child, path=f"{path}[{index}]")
    elif isinstance(value, str) and (
        "://" in value
        or value.lower().startswith(("bearer ", "sessionid="))
    ):
        raise ValueError(
            f"metronome journal contains forbidden string material at {path}"
        )


def _normalize_handle(value: str) -> str:
    normalized = value.strip().lstrip("@").lower()
    if not normalized:
        raise ValueError("TikTok handle is required")
    return normalized


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("UTC time must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, document: Mapping[str, object]) -> None:
    temporary_path = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp"
    )
    payload = (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        ).encode("utf-8")
        + b"\n"
    )
    try:
        with temporary_path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
