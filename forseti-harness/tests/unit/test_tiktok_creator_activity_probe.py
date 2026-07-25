from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from runners import run_tiktok_creator_activity_probe as probe
from runners import run_source_capture_tiktok_creator_onboarding as direct_runner
from tiktok_creator_metronome import (
    DIRECT_RUN_JOURNAL_NAME,
    SUPERVISED_ENV_NAME,
)


def test_first_rejection_requires_observation_and_resets() -> None:
    assert probe.PROFILE_DELAY_MIN_SECONDS == 41
    assert probe.PROFILE_DELAY_MAX_SECONDS == 93
    assert probe.OBSERVATION_COUNT == 1
    args = probe.build_parser().parse_args(
        [
            "--creator-handle",
            "one",
            "--data-root",
            "lake",
            "--output-dir",
            "output",
        ]
    )
    assert args.settle_seconds == 5.0

    state = probe._ProbeState()

    assert state.record_performance_rejection() is True
    assert state.rejection_streak == 1

    state.observation_intervention_count += 1
    state.reset_rejection_streak()
    assert state.rejection_streak == 0
    assert state.record_performance_rejection() is True


def test_required_skip_observation_views_exactly_one_video(
    tmp_path, monkeypatch
) -> None:
    grid_path = tmp_path / "grid.json"
    grid_path.write_text(
        json.dumps({"creator_handle": "creator", "items": []}),
        encoding="utf-8",
    )
    calls = []
    events = []

    class Journal:
        def record(self, event, *, handle=None, details=None):
            events.append((event, handle, details))

    def observe(**kwargs):
        calls.append(kwargs)
        return {"status": "complete"}

    monkeypatch.setattr(
        probe, "run_tiktok_creator_observation_activity", observe
    )
    state = probe._ProbeState(rejection_streak=1)

    probe._run_required_skip_observation(
        handle="creator",
        reason="market_defer",
        grid_path=grid_path,
        session_profile=object(),
        auth_state_root=tmp_path,
        timeout_seconds=30.0,
        settle_seconds=2.0,
        rng=object(),
        journal=Journal(),
        state=state,
    )

    assert len(calls) == 1
    assert calls[0]["observation_count"] == 1
    assert calls[0]["grid_window"]["creator_handle"] == "creator"
    assert state.observation_intervention_count == 1
    assert state.rejection_streak == 0
    assert [event[0] for event in events] == [
        "observation_intervention_started",
        "observation_intervention_finished",
    ]


def test_failed_skip_observation_stops_before_state_reset(
    tmp_path, monkeypatch
) -> None:
    grid_path = tmp_path / "grid.json"
    grid_path.write_text(
        json.dumps({"creator_handle": "creator", "items": []}),
        encoding="utf-8",
    )

    class Journal:
        def record(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr(
        probe,
        "run_tiktok_creator_observation_activity",
        lambda **_kwargs: {"status": "failed"},
    )
    state = probe._ProbeState(rejection_streak=1)

    with pytest.raises(
        probe.TikTokCreatorActivityProbeError,
        match="required observation intervention failed",
    ):
        probe._run_required_skip_observation(
            handle="creator",
            reason="performance_rejection",
            grid_path=grid_path,
            session_profile=object(),
            auth_state_root=tmp_path,
            timeout_seconds=30.0,
            settle_seconds=2.0,
            rng=object(),
            journal=Journal(),
            state=state,
        )

    assert state.observation_intervention_count == 0
    assert state.rejection_streak == 1


@pytest.mark.parametrize("first_outcome", ("market_defer", "performance_reject"))
def test_first_noninteractive_outcome_observes_before_next_profile(
    tmp_path, monkeypatch, first_outcome
) -> None:
    actions = []
    first_handle = (
        "deferred" if first_outcome == "market_defer" else "rejected"
    )

    class Rng:
        def randint(self, _minimum, _maximum):
            return 54

    def run_child(args, *, journal, handle, on_progress=None):
        del journal
        if handle == "loggedout":
            actions.append("capture:loggedout")
            return probe._ChildResult(
                exit_code=2,
                summary=None,
                progress=(),
                blockers=({"code": "LOGGED_OUT_SESSION"},),
            )
        if "--promotion-only" in args:
            actions.append(f"promotion:{handle}")
            output_dir = args[args.index("--output-dir") + 1]
            decision_dir = tmp_path / "run" / "promotion" / handle / "decision"
            assert str(decision_dir) == output_dir
            decision_dir.mkdir(parents=True)
            (decision_dir / "tiktok_creator_promotion_decisions.json").write_text(
                "{}",
                encoding="utf-8",
            )
            return probe._ChildResult(
                exit_code=0,
                summary={},
                progress=(),
                blockers=(),
            )
        actions.append(f"capture:{handle}")
        if on_progress is not None:
            on_progress({"event": "collect_profile_grid"})
        capture_dir = tmp_path / "run" / "promotion" / handle / "capture"
        capture_dir.mkdir(parents=True)
        (capture_dir / probe.TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME).write_text(
            json.dumps({"creator_handle": handle, "items": []}),
            encoding="utf-8",
        )
        if first_outcome == "market_defer":
            return probe._ChildResult(
                exit_code=2,
                summary=None,
                progress=(),
                blockers=({"code": "CANDIDATE_MARKET_DEFERRED"},),
            )
        return probe._ChildResult(
            exit_code=0,
            summary={"admitted_path_or_none": str(tmp_path / "packet")},
            progress=(),
            blockers=(),
        )

    def observe(**kwargs):
        actions.append(f"observe:{kwargs['creator_handle']}")
        assert kwargs["observation_count"] == 1
        return {"status": "complete"}

    monkeypatch.setattr(probe.random, "SystemRandom", lambda: Rng())
    monkeypatch.setattr(
        probe.DataLakeRoot, "resolve", lambda **_kwargs: object()
    )
    monkeypatch.setattr(
        probe, "resolve_session_profile", lambda *_args, **_kwargs: object()
    )
    monkeypatch.setattr(
        probe, "default_session_profile_auth_state_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        probe, "_record_authority_snapshot", lambda **_kwargs: None
    )
    monkeypatch.setattr(probe, "_run_onboarding_child", run_child)
    monkeypatch.setattr(
        probe,
        "promotion_decision_for_handle",
        lambda _document, _handle: {
            "registry_action": "do_not_promote",
            "decision_reason_code": "below_both_p25",
            "age_normalized_quality_index_or_none": 1.0,
            "reliable_weekly_reach": 1.0,
        },
    )
    monkeypatch.setattr(
        probe, "run_tiktok_creator_observation_activity", observe
    )
    monkeypatch.setattr(
        probe,
        "_release_after_timer",
        lambda **kwargs: actions.append(f"release:{kwargs['handle']}"),
    )

    exit_code = probe.main(
        [
            "--creator-handle",
            first_handle,
            "--creator-handle",
            "loggedout",
            "--creator-handle",
            "three",
            "--creator-handle",
            "four",
            "--creator-handle",
            "five",
            "--data-root",
            str(tmp_path / "lake"),
            "--output-dir",
            str(tmp_path / "run"),
        ]
    )

    assert exit_code == 2
    expected = [f"capture:{first_handle}"]
    if first_outcome == "performance_reject":
        expected.append(f"promotion:{first_handle}")
    expected.extend(
        [
            f"observe:{first_handle}",
            f"release:{first_handle}",
            "capture:loggedout",
        ]
    )
    assert actions == expected


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


def test_probe_journal_keeps_existing_metronome_umbrella_current(
    tmp_path,
) -> None:
    umbrella_path = tmp_path / probe.METRONOME_UMBRELLA_NAME
    umbrella_path.write_text(
        json.dumps({"schema_version": "legacy", "runs": [{"handle": "one"}]}),
        encoding="utf-8",
    )
    journal_path = (
        tmp_path / "activity-probe-test" / probe.PROBE_JOURNAL_NAME
    )
    journal = probe._ProbeJournal(journal_path)

    journal.record(
        "run_started",
        details={"creator_handles": ["one", "two"]},
    )
    journal.record("profile_timer_started", handle="one")

    running_document = json.loads(umbrella_path.read_text(encoding="utf-8"))
    running_projection = running_document[probe.METRONOME_PROJECTION_KEY]
    assert running_document["runs"] == [{"handle": "one"}]
    assert running_projection["aggregate"] == {
        "run_count": 1,
        "event_count": 2,
        "logout_detection_count": 0,
        "journal_kind_counts": {"activity_probe": 1},
        "status_counts": {"running": 1},
    }
    assert running_projection["runs"][0]["last_sequence"] == 1
    assert running_projection["runs"][0]["current_handle_or_none"] == "one"

    journal.close(
        status="complete",
        terminal_reason="test_complete",
        counters=probe._ProbeState(assessed_count=1).counters(),
    )

    complete_document = json.loads(umbrella_path.read_text(encoding="utf-8"))
    run = complete_document[probe.METRONOME_PROJECTION_KEY]["runs"][0]
    assert run["status"] == "complete"
    assert run["terminal_reason_or_none"] == "test_complete"
    assert run["terminal_counters"]["assessed_count"] == 1
    assert run["journal_sha256"] == sha256(journal_path.read_bytes()).hexdigest()


def test_refresh_metronome_umbrella_backfills_all_probe_journals(
    tmp_path,
) -> None:
    umbrella_path = tmp_path / probe.METRONOME_UMBRELLA_NAME
    umbrella_path.write_text('{"schema_version":"legacy"}', encoding="utf-8")
    first_path = tmp_path / "activity-probe-a" / probe.PROBE_JOURNAL_NAME
    first = probe._ProbeJournal(first_path)
    first.record("run_started", details={"creator_handles": ["one"]})
    first.record("first_logout_detected", handle="one")
    first.close(
        status="logged_out",
        terminal_reason="forced_logout_detected",
        counters=probe._ProbeState(assessed_count=1).counters(),
    )

    second_path = tmp_path / "activity-probe-b" / probe.PROBE_JOURNAL_NAME
    second = probe._ProbeJournal(second_path)
    second.record("run_started", details={"creator_handles": ["two"]})

    document = probe._refresh_metronome_umbrella(
        umbrella_path,
        refreshed_at_utc="2026-07-25T01:02:03.004Z",
    )
    projection = document[probe.METRONOME_PROJECTION_KEY]
    assert projection["refreshed_at_utc"] == "2026-07-25T01:02:03.004Z"
    assert projection["aggregate"] == {
        "run_count": 2,
        "event_count": 4,
        "logout_detection_count": 1,
        "journal_kind_counts": {"activity_probe": 2},
        "status_counts": {
            "interrupted_without_terminal": 1,
            "logged_out": 1,
        },
    }
    assert [run["journal_path"] for run in projection["runs"]] == [
        "activity-probe-a/tiktok_creator_activity_probe.jsonl",
        "activity-probe-b/tiktok_creator_activity_probe.jsonl",
    ]

    second.close(
        status="failed",
        terminal_reason="owner_interrupted",
        counters=probe._ProbeState().counters(),
    )


def test_direct_runner_automatically_logs_under_metronome_root(
    tmp_path, monkeypatch
) -> None:
    umbrella_path = tmp_path / probe.METRONOME_UMBRELLA_NAME
    umbrella_path.write_text('{"schema_version":"legacy"}', encoding="utf-8")
    output_dir = tmp_path / "promotion" / "creator" / "capture"

    def fake_run(_parser, _args):
        direct_runner._emit_progress(
            "collect_profile_grid",
            {"creator_handle": "creator"},
        )
        direct_runner._emit_summary(
            {
                "status": "complete",
                "capture_scope": "candidate_assessment",
                "creator_intent": "new_capture",
                "completed_deep_capture_count": 0,
            }
        )
        return 0

    monkeypatch.setattr(direct_runner, "_run_main", fake_run)
    assert direct_runner.main(
        [
            "--creator-handle",
            "creator",
            "--creator-intent",
            "new_capture",
            "--output-dir",
            str(output_dir),
        ]
    ) == 0

    journal_path = output_dir / DIRECT_RUN_JOURNAL_NAME
    rows = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["event_type"] for row in rows] == [
        "run_started",
        "runner_progress",
        "runner_summary",
        "terminal",
    ]
    assert [row["sequence"] for row in rows] == [0, 1, 2, 3]
    projection = json.loads(umbrella_path.read_text(encoding="utf-8"))[
        probe.METRONOME_PROJECTION_KEY
    ]
    assert projection["aggregate"]["journal_kind_counts"] == {
        "direct_runner": 1
    }
    assert projection["runs"][0]["status"] == "complete"
    assert projection["runs"][0]["journal_sha256"] == sha256(
        journal_path.read_bytes()
    ).hexdigest()


def test_direct_runner_logs_logout_and_repeat_without_overwriting(
    tmp_path, monkeypatch
) -> None:
    umbrella_path = tmp_path / probe.METRONOME_UMBRELLA_NAME
    umbrella_path.write_text("{}", encoding="utf-8")

    def fake_logout(parser, _args):
        direct_runner._emit_blocker(
            "LOGGED_OUT_SESSION",
            "authenticated_browser_session",
        )
        parser.exit(2, "logged out\n")

    monkeypatch.setattr(direct_runner, "_run_main", fake_logout)
    for handle in ("one", "two"):
        with pytest.raises(SystemExit) as exc:
            direct_runner.main(
                [
                    "--creator-handle",
                    handle,
                    "--creator-intent",
                    "new_capture",
                    "--output-dir",
                    str(tmp_path / handle / "capture"),
                ]
            )
        assert exc.value.code == 2

    projection = json.loads(umbrella_path.read_text(encoding="utf-8"))[
        probe.METRONOME_PROJECTION_KEY
    ]
    assert projection["aggregate"]["run_count"] == 2
    assert projection["aggregate"]["logout_detection_count"] == 2
    assert projection["aggregate"]["status_counts"] == {"logged_out": 2}
    assert {run["current_handle_or_none"] for run in projection["runs"]} == {
        "one",
        "two",
    }


def test_probe_supervision_avoids_duplicate_direct_journal(
    tmp_path, monkeypatch
) -> None:
    umbrella_path = tmp_path / probe.METRONOME_UMBRELLA_NAME
    umbrella_path.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "supervised" / "capture"
    monkeypatch.setenv(SUPERVISED_ENV_NAME, "1")
    monkeypatch.setattr(direct_runner, "_run_main", lambda *_args: 0)

    assert direct_runner.main(
        [
            "--creator-handle",
            "creator",
            "--creator-intent",
            "new_capture",
            "--output-dir",
            str(output_dir),
        ]
    ) == 0
    assert not (output_dir / DIRECT_RUN_JOURNAL_NAME).exists()
    assert probe.METRONOME_PROJECTION_KEY not in json.loads(
        umbrella_path.read_text(encoding="utf-8")
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
