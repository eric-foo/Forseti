"""Rolling raw sample store for content-only capture surfaces.

Content-only retention discards the rendered bytes that make an extractor defect
repairable after the fact.  The rolling sample buys back a *recent* ground truth
at bounded disk cost: the FIRST capture of a surface on a given day -- or the
first of a batch campaign, keyed by an operator-supplied run key -- keeps its
rendered DOM and visible text in an operator-drive sample store alongside the
content record the runner banked in flight.  Everything older than
``ROLLING_RAW_SAMPLE_WINDOW_DAYS`` is pruned on the next claim.

This is deliberately NOT a permanent pinned corpus (owner decision 2026-07-28).
Nothing here is durable evidence, and nothing is retained forever; the store is
a regression-check input whose whole value is being recent.

The sample lives beside the packet rather than inside it, so a content-only
packet keeps one uniform shape and pruning never mutates an already-written
capture artifact.  Pruning deletes only directories this store created under
its own root.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROLLING_RAW_SAMPLE_WINDOW_DAYS = 30
ROLLING_RAW_SAMPLE_STATE_FILENAME = "rolling_raw_sample_state.json"
ROLLING_RAW_SAMPLE_STATE_VERSION = "rolling_raw_sample_state_v0"
RENDERED_DOM_SAMPLE_FILENAME = "rendered_dom.html"
VISIBLE_TEXT_SAMPLE_FILENAME = "visible_text.txt"
CONTENT_RECORD_SAMPLE_FILENAME = "content_record.json"
SAMPLE_METADATA_FILENAME = "sample_metadata.json"


@dataclass(frozen=True)
class RollingRawSampleClaim:
    """The outcome of asking whether this capture owes the store a sample."""

    granted: bool
    surface: str
    sample_key: str
    reason: str
    directory: Path | None = None
    sampled_on: date | None = None
    pruned_keys: tuple[str, ...] = ()


class RollingRawSampleStore:
    """Claim-and-write access to one operator-drive rolling sample root."""

    def __init__(self, root: Path, *, window_days: int = ROLLING_RAW_SAMPLE_WINDOW_DAYS):
        if window_days < 1:
            raise ValueError(f"window_days must be >= 1; got {window_days}")
        self.root = Path(root)
        self.window_days = window_days

    # -- state -----------------------------------------------------------

    @property
    def state_path(self) -> Path:
        return self.root / ROLLING_RAW_SAMPLE_STATE_FILENAME

    def _read_state(self) -> dict:
        if not self.state_path.exists():
            return {"state_version": ROLLING_RAW_SAMPLE_STATE_VERSION, "samples": {}}
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"rolling raw sample state at {self.state_path} is not readable JSON; "
                "refusing to guess which samples exist"
            ) from exc
        if not isinstance(state, dict) or not isinstance(state.get("samples"), dict):
            raise ValueError(
                f"rolling raw sample state at {self.state_path} is not a "
                f"{ROLLING_RAW_SAMPLE_STATE_VERSION} document"
            )
        return state

    def _write_state(self, state: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # -- claim / write ---------------------------------------------------

    @staticmethod
    def _entry_key(surface: str, sample_key: str) -> str:
        return f"{surface}|{sample_key}"

    def claim(
        self,
        *,
        surface: str,
        capture_date: date,
        run_key: str | None = None,
    ) -> RollingRawSampleClaim:
        """Decide whether this capture is the window's sample for its surface.

        The sample key is the operator-supplied ``run_key`` for a batch campaign
        (first capture of the run) and otherwise the capture's ISO date (first
        capture of the day).  Pruning runs on every claim so a lane that keeps
        capturing keeps the window bounded without a separate sweep job.
        """
        if not surface.strip():
            raise ValueError("surface must be a non-empty string")
        sample_key = (run_key or capture_date.isoformat()).strip()
        if not sample_key:
            raise ValueError("run_key must be non-empty when supplied")

        state = self._read_state()
        pruned = self._prune(state, today=capture_date)
        entry_key = self._entry_key(surface, sample_key)

        if entry_key in state["samples"]:
            if pruned:
                self._write_state(state)
            return RollingRawSampleClaim(
                granted=False,
                surface=surface,
                sample_key=sample_key,
                reason=(
                    f"surface {surface!r} already has a rolling raw sample for "
                    f"{sample_key!r}"
                ),
                pruned_keys=pruned,
            )

        directory = self.root / _safe_component(surface) / _safe_component(sample_key)
        if pruned:
            self._write_state(state)
        return RollingRawSampleClaim(
            granted=True,
            surface=surface,
            sample_key=sample_key,
            reason=(
                f"first capture of surface {surface!r} for {sample_key!r}; keeping "
                f"rendered bytes for the {self.window_days}-day regression window"
            ),
            directory=directory,
            sampled_on=capture_date,
            pruned_keys=pruned,
        )

    def write_sample(
        self,
        claim: RollingRawSampleClaim,
        *,
        rendered_dom: bytes,
        visible_text: bytes,
        content_record: bytes,
        metadata: dict,
    ) -> Path:
        """Write and then commit a claimed sample.

        State is recorded only after every required byte is present. If a write
        raises or the process stops early, the next capture can claim the key
        again instead of treating a nonexistent sample as already banked.
        """
        if not claim.granted or claim.directory is None or claim.sampled_on is None:
            raise ValueError("write_sample requires a granted claim")
        state = self._read_state()
        entry_key = self._entry_key(claim.surface, claim.sample_key)
        if entry_key in state["samples"]:
            raise ValueError(
                f"rolling raw sample {claim.surface!r}/{claim.sample_key!r} "
                "was already committed"
            )
        claim.directory.mkdir(parents=True, exist_ok=True)
        (claim.directory / RENDERED_DOM_SAMPLE_FILENAME).write_bytes(rendered_dom)
        (claim.directory / VISIBLE_TEXT_SAMPLE_FILENAME).write_bytes(visible_text)
        (claim.directory / CONTENT_RECORD_SAMPLE_FILENAME).write_bytes(content_record)
        (claim.directory / SAMPLE_METADATA_FILENAME).write_text(
            json.dumps(
                {
                    "surface": claim.surface,
                    "sample_key": claim.sample_key,
                    "window_days": self.window_days,
                    "non_claims": [
                        "rolling regression sample; not durable evidence",
                        "auto-pruned outside the window; never a permanent corpus",
                    ],
                    **metadata,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        state["samples"][entry_key] = {
            "surface": claim.surface,
            "sample_key": claim.sample_key,
            "sampled_on": claim.sampled_on.isoformat(),
            "relative_path": str(claim.directory.relative_to(self.root)).replace(
                "\\", "/"
            ),
        }
        self._write_state(state)
        return claim.directory

    # -- prune -----------------------------------------------------------

    def _prune(self, state: dict, *, today: date) -> tuple[str, ...]:
        cutoff = today - timedelta(days=self.window_days)
        pruned: list[str] = []
        for entry_key, entry in list(state["samples"].items()):
            try:
                sampled_on = date.fromisoformat(str(entry.get("sampled_on", "")))
            except ValueError:
                # An unparseable date cannot be aged out safely; leave it and let
                # the operator see it rather than deleting on a guess.
                continue
            if sampled_on >= cutoff:
                continue
            relative = str(entry.get("relative_path", "")).strip()
            if relative:
                directory = self.root / relative
                if _is_inside(directory, self.root) and directory.is_dir():
                    shutil.rmtree(directory)
            del state["samples"][entry_key]
            pruned.append(entry_key)
        return tuple(pruned)

    def prune(self, *, today: date) -> tuple[str, ...]:
        """Prune aged-out samples without claiming a new one."""
        state = self._read_state()
        pruned = self._prune(state, today=today)
        if pruned:
            self._write_state(state)
        return pruned

    # -- read ------------------------------------------------------------

    def current_samples(self) -> list[dict]:
        """Every sample currently inside the window, oldest first."""
        state = self._read_state()
        entries = [dict(entry) for entry in state["samples"].values()]
        entries.sort(key=lambda entry: (entry.get("sampled_on", ""), entry.get("surface", "")))
        for entry in entries:
            entry["directory"] = str(self.root / str(entry.get("relative_path", "")))
        return entries


def _safe_component(value: str) -> str:
    """Filesystem-safe, collision-resistant component; never empty/traversing."""
    cleaned = "".join(
        char if (char.isalnum() or char in {"-", "_", "."}) else "_" for char in value
    ).strip("._") or "unnamed"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{cleaned[:100]}-{digest}"


def _is_inside(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


__all__ = [
    "CONTENT_RECORD_SAMPLE_FILENAME",
    "RENDERED_DOM_SAMPLE_FILENAME",
    "ROLLING_RAW_SAMPLE_STATE_FILENAME",
    "ROLLING_RAW_SAMPLE_WINDOW_DAYS",
    "SAMPLE_METADATA_FILENAME",
    "VISIBLE_TEXT_SAMPLE_FILENAME",
    "RollingRawSampleClaim",
    "RollingRawSampleStore",
]
