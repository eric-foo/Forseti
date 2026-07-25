"""Run one bounded logged-in TikTok promotion/activity probe."""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture_spine.tiktok_creator_discovery_frontier.frontier_selector import (
    promotion_decision_for_handle,
)
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    load_creator_frontier_dispositions,
)
from data_lake.canonical_json import canonical_record_bytes
from data_lake.creator_audience_queue import assert_creator_audience_capacity
from data_lake.creator_registry import load_current_registry_preflight_view
from data_lake.creator_registry import load_current_creator_registry
from data_lake.root import DataLakeRoot
from harness_utils import sha256_bytes
from source_capture.adapters.browser_session_probe import probe_local_cdp_endpoints
from source_capture.session_profiles import (
    default_session_profile_auth_state_root,
    resolve_session_profile,
)
from source_capture.tiktok.creator_onboarding import (
    TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
    TikTokLoggedOutSessionError,
    run_tiktok_creator_observation_activity,
)
from tiktok_creator_metronome import (
    JOURNAL_SCHEMA_VERSION,
    METRONOME_PROJECTION_KEY,
    METRONOME_PROJECTION_SCHEMA_VERSION,
    METRONOME_UMBRELLA_NAME,
    PROBE_JOURNAL_NAME,
    SUPERVISED_ENV_NAME,
    TikTokMetronomeJournal,
    refresh_metronome_umbrella,
    summarize_metronome_journal,
    validate_metronome_row,
)


ROOT = Path(__file__).resolve().parents[2]
ONBOARDING_RUNNER = (
    ROOT / "forseti-harness/runners/run_source_capture_tiktok_creator_onboarding.py"
)
REGISTRY_RUNNER = ROOT / "forseti-harness/runners/run_creator_registry_lake.py"
SUMMARY_PREFIX = "tiktok_creator_onboarding_summary_json="
PROGRESS_PREFIX = "tiktok_creator_onboarding_progress_json="
BLOCKER_PREFIX = "tiktok_creator_onboarding_blocker_json="
PROBE_SCHEMA_VERSION = JOURNAL_SCHEMA_VERSION
PROFILE_DELAY_MIN_SECONDS = 41
PROFILE_DELAY_MAX_SECONDS = 93
REJECTION_STREAK_TRIGGER = 1
OBSERVATION_COUNT = 1
_ProbeJournal = TikTokMetronomeJournal
_refresh_metronome_umbrella = refresh_metronome_umbrella
_summarize_probe_journal = summarize_metronome_journal
_validate_probe_journal_row = validate_metronome_row


class TikTokCreatorActivityProbeError(RuntimeError):
    """Fail-closed probe error."""


@dataclass(frozen=True)
class _ChildResult:
    exit_code: int
    summary: dict[str, object] | None
    progress: tuple[dict[str, object], ...]
    blockers: tuple[dict[str, object], ...]


@dataclass
class _ProbeState:
    rejection_streak: int = 0
    assessed_count: int = 0
    promoted_count: int = 0
    rejected_count: int = 0
    deferred_count: int = 0
    onboarded_count: int = 0
    observation_intervention_count: int = 0

    def record_performance_rejection(self) -> bool:
        self.rejected_count += 1
        self.rejection_streak += 1
        return self.rejection_streak == REJECTION_STREAK_TRIGGER

    def reset_rejection_streak(self) -> None:
        self.rejection_streak = 0

    def counters(self) -> dict[str, int]:
        return {
            "assessed_count": self.assessed_count,
            "promoted_count": self.promoted_count,
            "rejected_count": self.rejected_count,
            "deferred_count": self.deferred_count,
            "onboarded_count": self.onboarded_count,
            "observation_intervention_count": (
                self.observation_intervention_count
            ),
            "rejection_streak": self.rejection_streak,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--creator-handle",
        action="append",
        required=True,
        help="Repeat exactly five times in frozen probe order.",
    )
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--session-profile",
        default="chowdakr_sg_tiktok",
    )
    parser.add_argument("--session-profile-config", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--settle-seconds", type=float, default=5.0)
    return parser


def _run_required_skip_observation(
    *,
    handle: str,
    reason: str,
    grid_path: Path,
    session_profile: Any,
    auth_state_root: Path,
    timeout_seconds: float,
    settle_seconds: float,
    rng: Any,
    journal: _ProbeJournal,
    state: _ProbeState,
) -> None:
    journal.record(
        "observation_intervention_started",
        handle=handle,
        details={
            "observation_count": OBSERVATION_COUNT,
            "reason": reason,
        },
    )
    grid_window = json.loads(grid_path.read_text(encoding="utf-8"))
    receipt = run_tiktok_creator_observation_activity(
        creator_handle=handle,
        session_profile=session_profile,
        grid_window=grid_window,
        auth_state_root=auth_state_root,
        observation_count=OBSERVATION_COUNT,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        max_grid_scroll_passes=1,
        rng=rng,
        event_fn=lambda event, fields: journal.record(
            event, handle=handle, details=fields
        ),
    )
    if receipt.get("status") != "complete":
        raise TikTokCreatorActivityProbeError(
            f"required observation intervention failed for {handle}"
        )
    state.observation_intervention_count += 1
    state.reset_rejection_streak()
    journal.record(
        "observation_intervention_finished",
        handle=handle,
        details={
            "observation_count": OBSERVATION_COUNT,
            "reason": reason,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handles = tuple(_normalize_handle(handle) for handle in args.creator_handle)
    if len(handles) != 5:
        raise SystemExit("--creator-handle must be supplied exactly five times")
    if len(set(handles)) != len(handles):
        raise SystemExit("probe creator handles must be unique")

    rng = random.SystemRandom()
    state = _ProbeState()
    journal = _ProbeJournal(args.output_dir / PROBE_JOURNAL_NAME)
    status = "failed"
    terminal_reason = "unexpected_failure"
    try:
        journal.record(
            "run_started",
            details={
                "run_kind": "creator_activity_probe",
                "creator_handles": list(handles),
                "profile_delay_min_seconds": PROFILE_DELAY_MIN_SECONDS,
                "profile_delay_max_seconds": PROFILE_DELAY_MAX_SECONDS,
                "rejection_streak_trigger": REJECTION_STREAK_TRIGGER,
                "observation_count": OBSERVATION_COUNT,
                "observation_dwell_policy": "onboarding_weighted_long_tail",
                "observation_dwell_median_seconds": 12.894737,
                "observation_dwell_tail_probability": 0.05,
                "observation_trigger_policy": (
                    "after_every_rejected_or_deferred_creator"
                ),
            },
        )
        data_root = DataLakeRoot.resolve(explicit=args.data_root)
        session_profile = resolve_session_profile(
            args.session_profile,
            config_path=args.session_profile_config,
        )
        auth_state_root = default_session_profile_auth_state_root()
        _record_authority_snapshot(
            journal=journal,
            data_root=data_root,
            handle=None,
        )
        for handle in handles:
            delay_seconds = rng.randint(
                PROFILE_DELAY_MIN_SECONDS,
                PROFILE_DELAY_MAX_SECONDS,
            )
            journal.record(
                "profile_timer_drawn",
                handle=handle,
                details={"planned_seconds": delay_seconds},
            )
            _record_authority_snapshot(
                journal=journal,
                data_root=data_root,
                handle=handle,
            )
            timer_started: float | None = None

            def on_progress(payload: dict[str, object]) -> None:
                nonlocal timer_started
                phase = str(payload.get("event") or "")
                if phase == "collect_profile_grid" and timer_started is None:
                    timer_started = time.monotonic()
                    journal.record(
                        "profile_navigation_started",
                        handle=handle,
                        details={
                            "planned_delay_seconds": delay_seconds,
                        },
                    )

            capture_dir = args.output_dir / "promotion" / handle / "capture"
            assessment = _run_onboarding_child(
                [
                    "--creator-handle",
                    handle,
                    "--creator-intent",
                    "new_capture",
                    "--data-root",
                    args.data_root,
                    "--output-dir",
                    str(capture_dir),
                    "--session-profile",
                    args.session_profile,
                    "--timeout-seconds",
                    str(args.timeout_seconds),
                    "--settle-seconds",
                    str(args.settle_seconds),
                ],
                journal=journal,
                handle=handle,
                on_progress=on_progress,
            )
            if _has_blocker(assessment, "LOGGED_OUT_SESSION"):
                status = "logged_out"
                terminal_reason = "forced_logout_detected"
                journal.record(
                    "first_logout_detected",
                    handle=handle,
                    details={"phase": "candidate_assessment"},
                )
                break
            if _has_blocker(assessment, "CANDIDATE_MARKET_DEFERRED"):
                state.deferred_count += 1
                journal.record(
                    "nonperformance_defer",
                    handle=handle,
                    details={
                        "rejection_streak": state.rejection_streak,
                        "reason": "market_gate",
                    },
                )
                _run_required_skip_observation(
                    handle=handle,
                    reason="market_defer",
                    grid_path=(
                        capture_dir
                        / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME
                    ),
                    session_profile=session_profile,
                    auth_state_root=auth_state_root,
                    timeout_seconds=args.timeout_seconds,
                    settle_seconds=args.settle_seconds,
                    rng=rng,
                    journal=journal,
                    state=state,
                )
                _release_after_timer(
                    journal=journal,
                    handle=handle,
                    timer_started=timer_started,
                    planned_seconds=delay_seconds,
                )
                continue
            if assessment.exit_code != 0 or assessment.summary is None:
                raise TikTokCreatorActivityProbeError(
                    f"candidate assessment failed for {handle}"
                )
            state.assessed_count += 1
            grid_path = capture_dir / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME
            decision_input = (
                args.output_dir / "promotion" / handle / "decision-input"
            )
            decision_input.mkdir(parents=True, exist_ok=False)
            decision_grid_path = decision_input / f"{handle}.grid.json"
            shutil.copyfile(grid_path, decision_grid_path)
            decision_dir = args.output_dir / "promotion" / handle / "decision"
            promotion = _run_onboarding_child(
                [
                    "--creator-handle",
                    handle,
                    "--promotion-grid-dir",
                    str(decision_input),
                    "--promotion-only",
                    "--data-root",
                    args.data_root,
                    "--output-dir",
                    str(decision_dir),
                ],
                journal=journal,
                handle=handle,
            )
            if promotion.exit_code != 0:
                raise TikTokCreatorActivityProbeError(
                    f"promotion decision failed for {handle}"
                )
            decision_document = json.loads(
                (
                    decision_dir / "tiktok_creator_promotion_decisions.json"
                ).read_text(encoding="utf-8")
            )
            decision = promotion_decision_for_handle(
                decision_document, handle
            )
            if decision is None:
                raise TikTokCreatorActivityProbeError(
                    f"promotion decision is missing for {handle}"
                )
            registry_action = str(decision.get("registry_action") or "")
            journal.record(
                "promotion_decision",
                handle=handle,
                details={
                    "registry_action": registry_action,
                    "decision_reason_code": str(
                        decision.get("decision_reason_code") or ""
                    ),
                    "age_normalized_quality_index_or_none": decision.get(
                        "age_normalized_quality_index_or_none"
                    ),
                    "reliable_weekly_reach": decision.get(
                        "reliable_weekly_reach"
                    ),
                },
            )
            if registry_action == "do_not_promote":
                trigger_observation = state.record_performance_rejection()
                journal.record(
                    "rejection_streak_changed",
                    handle=handle,
                    details={
                        "rejection_streak": state.rejection_streak,
                        "observation_triggered": trigger_observation,
                    },
                )
                if trigger_observation:
                    _run_required_skip_observation(
                        handle=handle,
                        reason="performance_rejection",
                        grid_path=grid_path,
                        session_profile=session_profile,
                        auth_state_root=auth_state_root,
                        timeout_seconds=args.timeout_seconds,
                        settle_seconds=args.settle_seconds,
                        rng=rng,
                        journal=journal,
                        state=state,
                    )
            elif registry_action == "promote_now":
                state.promoted_count += 1
                disposition = _current_disposition_for_handle(
                    load_creator_frontier_dispositions(data_root),
                    handle,
                )
                if (
                    disposition is None
                    or disposition.get("status") != "eligible"
                    or not disposition.get("record_id")
                ):
                    raise TikTokCreatorActivityProbeError(
                        f"current eligible Frontier disposition is missing for {handle}"
                    )
                admitted_path = assessment.summary.get(
                    "admitted_path_or_none"
                )
                if not isinstance(admitted_path, str) or not admitted_path:
                    raise TikTokCreatorActivityProbeError(
                        f"assessment packet is missing for {handle}"
                    )
                packet_path = Path(admitted_path)
                if not packet_path.is_dir():
                    raise TikTokCreatorActivityProbeError(
                        f"assessment packet path is unavailable for {handle}"
                    )
                journal.record(
                    "candidate_admission_started",
                    handle=handle,
                    details={
                        "packet_id": packet_path.name,
                        "frontier_disposition_id": disposition["record_id"],
                    },
                )
                admission = _run_json_child(
                    [
                        sys.executable,
                        str(REGISTRY_RUNNER),
                        "admit-tiktok-candidate",
                        "--data-root",
                        args.data_root,
                        "--packet-id",
                        packet_path.name,
                        "--frontier-disposition-id",
                        str(disposition["record_id"]),
                    ]
                )
                if admission.get("status") == "error":
                    raise TikTokCreatorActivityProbeError(
                        f"candidate admission failed for {handle}: "
                        f"{admission.get('error')}"
                    )
                account = _registry_account_for_handle(
                    load_current_creator_registry(data_root),
                    handle,
                )
                if (
                    account is None
                    or account["onboarding_state"] != "not_onboarded"
                    or account["monitoring_eligible"] is not False
                ):
                    raise TikTokCreatorActivityProbeError(
                        f"candidate admission verification failed for {handle}"
                    )
                journal.record(
                    "candidate_admission_finished",
                    handle=handle,
                    details={
                        "packet_id": packet_path.name,
                        "registry_account_id": account["registry_account_id"],
                        "stable_native_id": account["stable_native_id"],
                    },
                )
                onboarding_dir = (
                    args.output_dir / "onboarding" / handle
                )
                onboarding = _run_onboarding_child(
                    [
                        "--creator-handle",
                        handle,
                        "--creator-intent",
                        "new_onboarding",
                        "--data-root",
                        args.data_root,
                        "--output-dir",
                        str(onboarding_dir),
                        "--session-profile",
                        args.session_profile,
                        "--timeout-seconds",
                        str(args.timeout_seconds),
                        "--settle-seconds",
                        str(args.settle_seconds),
                    ],
                    journal=journal,
                    handle=handle,
                )
                if _has_blocker(onboarding, "LOGGED_OUT_SESSION"):
                    status = "logged_out"
                    terminal_reason = "forced_logout_detected"
                    journal.record(
                        "first_logout_detected",
                        handle=handle,
                        details={"phase": "immediate_onboarding"},
                    )
                    break
                if onboarding.exit_code != 0 or onboarding.summary is None:
                    raise TikTokCreatorActivityProbeError(
                        f"immediate onboarding failed for {handle}"
                    )
                state.onboarded_count += 1
                state.reset_rejection_streak()
                journal.record(
                    "rejection_streak_reset",
                    handle=handle,
                    details={"reason": "onboarding_complete"},
                )
            else:
                raise TikTokCreatorActivityProbeError(
                    f"unsupported promotion action for {handle}: {registry_action}"
                )
            _release_after_timer(
                journal=journal,
                handle=handle,
                timer_started=timer_started,
                planned_seconds=delay_seconds,
            )
        else:
            status = "complete"
            terminal_reason = "five_handle_probe_complete"
        return 0 if status == "complete" else 2
    except TikTokLoggedOutSessionError:
        status = "logged_out"
        terminal_reason = "forced_logout_detected"
        journal.record(
            "first_logout_detected",
            handle=handle,
            details={"phase": "observation_activity"},
        )
        return 2
    except Exception as exc:
        journal.record(
            "probe_failure",
            details={"error_type": type(exc).__name__},
        )
        terminal_reason = (
            terminal_reason
            if terminal_reason != "unexpected_failure"
            else type(exc).__name__
        )
        print(
            f"tiktok creator activity probe failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 3
    finally:
        journal.close(
            status=status,
            terminal_reason=terminal_reason,
            counters=state.counters(),
        )


def _run_onboarding_child(
    args: Sequence[str],
    *,
    journal: _ProbeJournal,
    handle: str,
    on_progress: Callable[[dict[str, object]], None] | None = None,
) -> _ChildResult:
    command = [sys.executable, str(ONBOARDING_RUNNER), *args]
    child_environment = os.environ.copy()
    child_environment[SUPERVISED_ENV_NAME] = "1"
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=child_environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    summary: dict[str, object] | None = None
    progress: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.rstrip("\r\n")
        print(line, flush=True)
        if line.startswith(PROGRESS_PREFIX):
            payload = _parse_prefixed_json(line, PROGRESS_PREFIX)
            progress.append(payload)
            journal.record(
                "runner_progress",
                handle=handle,
                details=_sanitized_progress_details(payload),
            )
            if on_progress is not None:
                on_progress(payload)
        elif line.startswith(BLOCKER_PREFIX):
            payload = _parse_prefixed_json(line, BLOCKER_PREFIX)
            blockers.append(payload)
            journal.record(
                "runner_blocker",
                handle=handle,
                details={
                    "code": str(payload.get("code") or ""),
                    "phase": str(payload.get("phase") or ""),
                },
            )
        elif line.startswith(SUMMARY_PREFIX):
            summary = _parse_prefixed_json(line, SUMMARY_PREFIX)
            journal.record(
                "runner_summary",
                handle=handle,
                details={
                    "status": str(summary.get("status") or ""),
                    "capture_scope": str(
                        summary.get("capture_scope") or ""
                    ),
                    "completed_deep_capture_count": int(
                        summary.get("completed_deep_capture_count") or 0
                    ),
                },
            )
    exit_code = process.wait()
    return _ChildResult(
        exit_code=exit_code,
        summary=summary,
        progress=tuple(progress),
        blockers=tuple(blockers),
    )


def _run_json_child(command: Sequence[str]) -> dict[str, object]:
    result = subprocess.run(
        list(command),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr, flush=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise TikTokCreatorActivityProbeError(
            "child command did not emit one JSON result"
        ) from exc
    if not isinstance(payload, dict) or result.returncode not in {0, 2}:
        raise TikTokCreatorActivityProbeError(
            f"child command failed with exit code {result.returncode}"
        )
    return payload


def _record_authority_snapshot(
    *,
    journal: _ProbeJournal,
    data_root: DataLakeRoot,
    handle: str | None,
) -> None:
    registry = load_current_registry_preflight_view(data_root)
    frontier = load_creator_frontier_dispositions(data_root)
    queue_counts = assert_creator_audience_capacity(data_root)
    cdp = probe_local_cdp_endpoints((9222,), timeout_seconds=2.0)
    if cdp.get("browser_available") is not True:
        raise TikTokCreatorActivityProbeError("CDP session is unavailable")
    journal.record(
        "authority_snapshot",
        handle=handle,
        details={
            "registry_sha256": sha256_bytes(canonical_record_bytes(registry)),
            "frontier_sha256": sha256_bytes(canonical_record_bytes(frontier)),
            "queue_queued": int(queue_counts.get("queued") or 0),
            "queue_running": int(queue_counts.get("running") or 0),
            "cdp_available": True,
        },
    )


def _release_after_timer(
    *,
    journal: _ProbeJournal,
    handle: str,
    timer_started: float | None,
    planned_seconds: int,
) -> None:
    if timer_started is None:
        raise TikTokCreatorActivityProbeError(
            f"profile timer never started for {handle}"
        )
    elapsed = max(0.0, time.monotonic() - timer_started)
    remaining = max(0.0, planned_seconds - elapsed)
    journal.record(
        "next_profile_release_wait_started",
        handle=handle,
        details={
            "planned_seconds": planned_seconds,
            "elapsed_seconds": round(elapsed, 6),
            "remaining_seconds": round(remaining, 6),
        },
    )
    if remaining:
        time.sleep(remaining)
    journal.record(
        "profile_timer_expired",
        handle=handle,
        details={
            "planned_seconds": planned_seconds,
            "detected_late_by_seconds": round(
                max(
                    0.0,
                    time.monotonic() - timer_started - planned_seconds,
                ),
                6,
            ),
        },
    )
    journal.record(
        "next_profile_released",
        handle=handle,
        details={
            "planned_seconds": planned_seconds,
            "actual_seconds": round(
                max(0.0, time.monotonic() - timer_started), 6
            ),
        },
    )


def _registry_account_for_handle(
    document: Mapping[str, object],
    handle: str,
) -> dict[str, object] | None:
    wrapper = document.get("creator_registry_index")
    accounts = (
        wrapper.get("platform_accounts")
        if isinstance(wrapper, dict)
        else None
    )
    if not isinstance(accounts, list):
        raise TikTokCreatorActivityProbeError(
            "Registry current authority has no platform accounts"
        )
    matches: list[dict[str, object]] = []
    for account in accounts:
        if not isinstance(account, dict):
            continue
        raw_handle = str(
            account.get("normalized_public_handle")
            or account.get("public_handle")
            or ""
        ).strip()
        if not raw_handle:
            continue
        account_handle = _normalize_handle(raw_handle)
        if (
            str(account.get("platform") or "").lower() == "tiktok"
            and account_handle == handle
        ):
            onboarding = account.get("onboarding")
            monitoring = account.get("monitoring_eligibility")
            matches.append(
                {
                    "registry_account_id": str(
                        account.get("platform_account_id") or ""
                    ),
                    "stable_native_id": str(
                        account.get(
                            "platform_public_account_id_or_none"
                        )
                        or ""
                    ),
                    "monitoring_eligible": (
                        monitoring.get("eligible")
                        if isinstance(monitoring, dict)
                        else None
                    ),
                    "onboarding_state": (
                        onboarding.get("onboarding_state")
                        if isinstance(onboarding, dict)
                        else None
                    ),
                }
            )
    if len(matches) > 1:
        raise TikTokCreatorActivityProbeError(
            f"duplicate Registry TikTok identity for {handle}"
        )
    return matches[0] if matches else None


def _current_disposition_for_handle(
    document: Mapping[str, object],
    handle: str,
) -> dict[str, object] | None:
    wrapper = document.get("creator_frontier_disposition_current")
    current = (
        wrapper.get("dispositions")
        if isinstance(wrapper, dict)
        else None
    )
    if not isinstance(current, list):
        raise TikTokCreatorActivityProbeError(
            "Frontier disposition view has no current rows"
        )
    matches = [
        row
        for row in current
        if isinstance(row, dict)
        and str(row.get("platform") or "").lower() == "tiktok"
        and str(row.get("public_handle") or "").strip()
        and _normalize_handle(str(row.get("public_handle") or "")) == handle
    ]
    if len(matches) > 1:
        raise TikTokCreatorActivityProbeError(
            f"duplicate current Frontier disposition for {handle}"
        )
    if not matches:
        return None
    result = dict(matches[0])
    result["record_id"] = result.get("disposition_id")
    return result


def _sanitized_progress_details(
    payload: Mapping[str, object],
) -> dict[str, object]:
    result: dict[str, object] = {
        "phase": str(payload.get("event") or "")
    }
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
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
    return result


def _parse_prefixed_json(line: str, prefix: str) -> dict[str, object]:
    payload = json.loads(line[len(prefix) :])
    if not isinstance(payload, dict):
        raise TikTokCreatorActivityProbeError(
            f"{prefix} payload must be an object"
        )
    return payload


def _has_blocker(result: _ChildResult, code: str) -> bool:
    return any(blocker.get("code") == code for blocker in result.blockers)


def _normalize_handle(value: str) -> str:
    normalized = value.strip().lstrip("@").lower()
    if not normalized:
        raise ValueError("TikTok handle is required")
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
