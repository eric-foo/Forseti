import sys
import types
from pathlib import Path

from runners import run_google_serp_persistent_fallback_packet as fallback_runner
from runners.run_google_serp_persistent_fallback_packet import (
    PERSISTENT_BLOCK_ROUTE_MODE,
    notify_operator_once,
    run_google_serp_persistent_fallback,
)
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
)


def test_block_is_preserved_notified_once_and_exact_job_resumes(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter((SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, 0))
    inspections = iter(
        (
            {"access_blocked": True, "query": "held query"},
            {"access_blocked": False, "query": "held query"},
        )
    )
    notifications: list[dict] = []
    sleeps: list[float] = []

    def capture(**_kwargs):
        output.mkdir()
        (output / "manifest.json").write_text("{}\n", encoding="utf-8")
        code = next(capture_codes)
        return code, str(output)

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-1",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0.25,
        capture_func=capture,
        inspect_func=lambda **_kwargs: next(inspections),
        notify_func=lambda **kwargs: notifications.append(kwargs),
        sleep_func=lambda seconds: sleeps.append(seconds),
    )

    assert code == 0
    assert len(notifications) == 1
    assert len(list(archive.glob("job-1_*"))) == 1
    assert not (archive / "block_alert.json").exists()
    assert sleeps == [0.25, 0.25]
    assert output.is_dir()


def test_clear_wrong_query_does_not_resume_navigation(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter((SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, 0))
    inspections = iter(
        (
            {"access_blocked": False, "query": "another query"},
            {"access_blocked": False, "query": "held query"},
        )
    )
    inspected: list[dict] = []
    captures: list[dict] = []

    def capture(**kwargs):
        captures.append(kwargs)
        output.mkdir()
        return next(capture_codes), str(output)

    def inspect(**_kwargs):
        state = next(inspections)
        inspected.append(state)
        return state

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-2",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0,
        capture_func=capture,
        inspect_func=inspect,
        notify_func=lambda **_kwargs: None,
        sleep_func=lambda _seconds: None,
    )

    assert code == 0
    # Load-bearing: an unblocked tab showing a DIFFERENT query must not end the
    # wait. Without the query-identity guard the loop breaks on the first
    # inspection and the second one is never consumed, so this count -- not the
    # exit code -- is what fails if the guard is dropped.
    assert len(inspected) == 2
    assert [state["query"] for state in inspected] == ["another query", "held query"]
    # The exact held job is what resumes, both before and after the block.
    assert len(captures) == 2
    assert {call["url"] for call in captures} == {
        "https://www.google.com/search?q=held+query"
    }
    assert {
        call["visible_mode_changes"] for call in captures
    } == {(PERSISTENT_BLOCK_ROUTE_MODE,)}


def test_each_distinct_block_pings_the_operator(tmp_path: Path) -> None:
    """A job blocked again after a clearance must ping again, not wait silently."""
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter(
        (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            0,
        )
    )
    inspections = iter(
        (
            {"access_blocked": False, "query": "held query"},
            {"access_blocked": False, "query": "held query"},
        )
    )
    notifications: list[dict] = []

    def capture(**_kwargs):
        output.mkdir()
        (output / "manifest.json").write_text("{}\n", encoding="utf-8")
        return next(capture_codes), str(output)

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-3",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0,
        capture_func=capture,
        inspect_func=lambda **_kwargs: next(inspections),
        notify_func=lambda **kwargs: notifications.append(kwargs),
        sleep_func=lambda _seconds: None,
    )

    assert code == 0
    assert len(notifications) == 2
    # Both block packets are preserved, not overwritten by the second block.
    assert len(list(archive.glob("job-3_*"))) == 2
    assert not (archive / "block_alert.json").exists()


def test_terminal_failure_clears_stale_operator_alert(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter((SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, 7))

    def capture(**_kwargs):
        output.mkdir()
        (output / "manifest.json").write_text("{}\n", encoding="utf-8")
        return next(capture_codes), str(output)

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-terminal-failure",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0,
        capture_func=capture,
        inspect_func=lambda **_kwargs: {
            "access_blocked": False,
            "query": "held query",
        },
        notify_func=lambda **_kwargs: None,
        sleep_func=lambda _seconds: None,
    )

    assert code == 7
    assert not (archive / "block_alert.json").exists()


def test_operator_alert_reaches_stderr_when_desktop_channels_fail(
    monkeypatch, capsys
) -> None:
    """The alert must survive a host with no `msg.exe` and no audio device.

    Both desktop channels are best-effort, so stderr is the fail-visible
    process channel. `subprocess.run` is stubbed because the real call raises
    a visible desktop dialog.
    """

    def _explode(*_args, **_kwargs):
        raise FileNotFoundError("msg.exe is not installed on this host")

    monkeypatch.setattr(fallback_runner.subprocess, "run", _explode)
    silent_winsound = types.ModuleType("winsound")
    silent_winsound.MB_ICONEXCLAMATION = 0
    silent_winsound.MessageBeep = lambda _flag: None
    monkeypatch.setitem(sys.modules, "winsound", silent_winsound)

    notify_operator_once(job_id="job-4", query="held query")

    captured = capsys.readouterr()
    assert "Forseti Google block alert" in captured.err
    assert "job-4: held query" in captured.err
