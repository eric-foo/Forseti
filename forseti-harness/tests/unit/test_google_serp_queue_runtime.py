from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import pytest

import source_capture.google_serp_queue_runtime as runtime


NOW = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def _initialize(
    tmp_path: Path,
    *,
    queries: tuple[str, ...] = ("Summer Fridays review",),
    fallback_ready: bool = False,
    rung: int = 4,
    jobs_since_rungup: int | None = None,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        json.dumps(
            {
                "schema_version": runtime.JOBS_VERSION,
                "run_id": "summer_fridays_understanding_confirmation",
                "jobs": [
                    {
                        "job_id": f"J{index:03d}",
                        "query": query,
                        "url": (
                            "https://www.google.com/search?q=" + quote_plus(query)
                        ),
                        "selected_type": "subject",
                        "selected_name": "Summer Fridays",
                        "shape": "subject_seed",
                    }
                    for index, query in enumerate(queries, start=1)
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "queue_state.json"
    runtime.initialize_queue(
        jobs_path=jobs_path,
        state_path=state_path,
        owner_ping_path=tmp_path / "OWNER_PING.json",
        persistent_fallback_enabled=fallback_ready,
        dedicated_logged_out_cdp_ready=fallback_ready,
        operator_visible=fallback_ready,
        rung=rung,
        jobs_since_rungup=jobs_since_rungup,
    )
    return state_path


def _claim(state_path: Path, *, now: datetime = NOW) -> dict:
    action = runtime.next_action(state_path=state_path, now=now)
    assert action["status"] == "capture_ready"
    return action


def _report(
    state_path: Path,
    action: dict,
    outcome: str,
    *,
    now: datetime = NOW,
) -> dict:
    return runtime.report_outcome(
        state_path=state_path,
        job_id=action["job"]["job_id"],
        route=action["route"],
        outcome=outcome,
        packet_locator=f"packet:{action['job']['job_id']}:{outcome}",
        now=now,
    )


def test_first_block_cools_down_and_retries_the_exact_held_job_once(
    tmp_path: Path,
) -> None:
    state_path = _initialize(tmp_path)
    first = _claim(state_path)
    blocked = _report(state_path, first, "blocked")

    assert blocked["status"] == "cooldown"
    assert blocked["rung"] == 4
    assert blocked["attempt_history"][0]["packet_locator"] == (
        "packet:J001:blocked"
    )
    assert runtime.next_action(
        state_path=state_path, now=NOW + timedelta(minutes=59)
    )["status"] == "cooldown"

    recovery = _claim(state_path, now=NOW + timedelta(hours=1))
    assert recovery["job"]["job_id"] == first["job"]["job_id"]
    assert recovery["attempt_kind"] == "cooldown_recovery"
    terminal = _report(
        state_path,
        recovery,
        "blocked",
        now=NOW + timedelta(hours=1, seconds=1),
    )

    assert terminal["status"] == "owner_ping"
    assert (tmp_path / "OWNER_PING.json").is_file()
    assert runtime.next_action(
        state_path=state_path, now=NOW + timedelta(hours=2)
    )["status"] == "owner_ping"


def test_block_steps_down_only_inside_five_job_rungup_probation(
    tmp_path: Path,
) -> None:
    state_path = _initialize(tmp_path, rung=4, jobs_since_rungup=5)
    action = _claim(state_path)
    state = _report(state_path, action, "blocked")
    assert state["rung"] == 3

    outside = _initialize(
        tmp_path / "outside", rung=4, jobs_since_rungup=6
    )
    action = _claim(outside)
    state = _report(outside, action, "blocked")
    assert state["rung"] == 4


def test_ready_persistent_fallback_gets_exact_held_job_without_hot_primary_retry(
    tmp_path: Path,
) -> None:
    state_path = _initialize(tmp_path, fallback_ready=True)
    primary = _claim(state_path)
    state = _report(state_path, primary, "blocked")
    assert state["cooldown_until"] is None
    assert state["pending_route"] == runtime.PERSISTENT_ROUTE

    fallback = _claim(state_path, now=NOW + timedelta(seconds=1))
    assert fallback["route"] == runtime.PERSISTENT_ROUTE
    assert fallback["attempt_kind"] == "persistent_fallback"
    assert fallback["job"] == primary["job"]


def test_claim_is_durable_and_prevents_duplicate_navigation(tmp_path: Path) -> None:
    state_path = _initialize(tmp_path)
    first = _claim(state_path)

    second = runtime.next_action(state_path=state_path, now=NOW)

    assert second["status"] == "waiting_for_report"
    assert second["in_flight"]["job_id"] == first["job"]["job_id"]


def test_owner_ping_exists_even_if_terminal_state_write_is_interrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = _initialize(tmp_path)
    first = _claim(state_path)
    _report(state_path, first, "blocked")
    recovery = _claim(state_path, now=NOW + timedelta(hours=1))
    real_write = runtime._atomic_write_json

    def interrupt_terminal(path: Path, value: dict) -> None:
        if value.get("status") == "owner_ping":
            raise OSError("simulated terminal-state write interruption")
        real_write(path, value)

    monkeypatch.setattr(runtime, "_atomic_write_json", interrupt_terminal)
    with pytest.raises(OSError, match="simulated"):
        _report(
            state_path,
            recovery,
            "blocked",
            now=NOW + timedelta(hours=1, seconds=1),
        )

    assert (tmp_path / "OWNER_PING.json").is_file()
    monkeypatch.setattr(runtime, "_atomic_write_json", real_write)
    assert runtime.next_action(state_path=state_path, now=NOW)["status"] == (
        "owner_ping"
    )


def test_third_nonconsecutive_block_stops_before_another_recovery(
    tmp_path: Path,
) -> None:
    state_path = _initialize(
        tmp_path,
        queries=("Summer Fridays review", "Summer Fridays price", "Summer Fridays Reddit"),
    )
    for index in range(2):
        first = _claim(state_path, now=NOW + timedelta(hours=index * 2))
        _report(
            state_path,
            first,
            "blocked",
            now=NOW + timedelta(hours=index * 2),
        )
        recovery = _claim(
            state_path, now=NOW + timedelta(hours=index * 2 + 1)
        )
        _report(
            state_path,
            recovery,
            "success",
            now=NOW + timedelta(hours=index * 2 + 1, seconds=1),
        )

    third = _claim(state_path, now=NOW + timedelta(hours=4))
    state = _report(
        state_path,
        third,
        "blocked",
        now=NOW + timedelta(hours=4),
    )

    assert state["blocks_this_run"] == 3
    assert state["status"] == "owner_ping"
    assert state["cooldown_until"] is None


def test_job_url_must_bind_the_declared_query(tmp_path: Path) -> None:
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        json.dumps(
            {
                "schema_version": runtime.JOBS_VERSION,
                "run_id": "bad",
                "jobs": [
                    {
                        "job_id": "J001",
                        "query": "Summer Fridays review",
                        "url": "https://www.google.com/search?q=different",
                        "selected_type": "subject",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(runtime.GoogleSerpQueueError, match="held query"):
        runtime.initialize_queue(
            jobs_path=jobs_path,
            state_path=tmp_path / "state.json",
            owner_ping_path=tmp_path / "OWNER_PING.json",
            persistent_fallback_enabled=False,
            dedicated_logged_out_cdp_ready=False,
            operator_visible=False,
        )
