from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from runners import run_tiktok_creator_activity_probe as probe


def test_rejection_streak_triggers_exactly_on_second_and_resets() -> None:
    state = probe._ProbeState()

    assert state.record_performance_rejection() is False
    assert state.rejection_streak == 1
    assert state.record_performance_rejection() is True
    assert state.rejection_streak == 2

    state.observation_intervention_count += 1
    state.reset_rejection_streak()
    assert state.rejection_streak == 0
    assert state.record_performance_rejection() is False


def test_probe_journal_records_contiguous_millisecond_events(tmp_path) -> None:
    monotonic_values = iter((100.0, 100.0, 100.1234, 100.5001))
    utc_values = iter(
        (
            datetime(2026, 7, 25, 1, 0, tzinfo=UTC),
            datetime(2026, 7, 25, 1, 0, 0, 123000, tzinfo=UTC),
            datetime(2026, 7, 25, 1, 0, 0, 500000, tzinfo=UTC),
        )
    )
    path = tmp_path / probe.PROBE_JOURNAL_NAME
    journal = probe._ProbeJournal(
        path,
        monotonic_fn=lambda: next(monotonic_values),
        utc_now_fn=lambda: next(utc_values),
    )
    journal.record("run_started", details={"creator_handles": ["one"]})
    journal.record(
        "promotion_decision",
        handle="one",
        details={"registry_action": "do_not_promote"},
    )
    journal.close(
        status="complete",
        terminal_reason="test_complete",
        counters=probe._ProbeState().counters(),
    )

    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["sequence"] for row in rows] == [0, 1, 2]
    assert [row["elapsed_ms"] for row in rows] == [0, 123, 500]
    assert rows[-1]["event_type"] == "terminal"


def test_probe_journal_rejects_secret_or_url_material(tmp_path) -> None:
    journal = probe._ProbeJournal(tmp_path / probe.PROBE_JOURNAL_NAME)

    with pytest.raises(ValueError, match="forbidden field"):
        journal.record("unsafe", details={"profile_url": "redacted"})

    journal.close(
        status="failed",
        terminal_reason="test_complete",
        counters=probe._ProbeState().counters(),
    )


def test_authority_helpers_resolve_current_shapes() -> None:
    registry = {
        "creator_registry_index": {
            "platform_accounts": [
                {
                    "platform": "tiktok",
                    "platform_account_id": "acct_1",
                    "platform_public_account_id_or_none": "native_1",
                    "normalized_public_handle": "creator",
                    "onboarding": {"onboarding_state": "not_onboarded"},
                    "monitoring_eligibility": {"eligible": False},
                }
            ]
        }
    }
    frontier = {
        "creator_frontier_disposition_current": {
            "dispositions": [
                {
                    "platform": "tiktok",
                    "public_handle": "creator",
                    "disposition_id": "cfd_1",
                    "status": "eligible",
                }
            ]
        }
    }

    assert probe._registry_account_for_handle(registry, "creator") == {
        "registry_account_id": "acct_1",
        "stable_native_id": "native_1",
        "monitoring_eligible": False,
        "onboarding_state": "not_onboarded",
    }
    assert probe._current_disposition_for_handle(
        frontier, "creator"
    )["record_id"] == "cfd_1"
