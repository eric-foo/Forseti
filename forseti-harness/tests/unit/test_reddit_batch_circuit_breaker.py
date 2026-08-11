"""Behaviour bound for the batch runner's HTTP-refusal circuit breakers.

The 2026-08-01 leaderboard run spent 8 consecutive server-refused requests
(HTTP 429) learning what the first 2 already said. The first 429 now stops
immediately; other typed refusals retain an N-consecutive threshold. An
explicit cooldown resume retries the failed slot and untouched tail while
carrying completed packets.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners import run_reddit_old_http_batch as batch
from runners.run_source_capture_realchrome_cdp_packet import (
    RealChromeNavigationHTTPError,
)
from runners import run_source_capture_realchrome_cdp_packet as cdp

URLS = [
    f"https://www.reddit.com/r/Sephora/comments/1v87d9{n}/talc/"
    for n in ("a", "b", "c", "d", "e", "f")
]
SLOTS = [
    batch.BatchSlot(slot_id=f"slot_{i:03d}", url=url) for i, url in enumerate(URLS, start=1)
]


def _run(tmp_path: Path, *, resume: bool = False, breaker: int = 3):
    return batch.run_reddit_old_http_batch(
        slots=SLOTS,
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        cadence_mode="fixed",
        delay_seconds=0.0,
        resume=resume,
        refusal_circuit_breaker=breaker,
    )


def _capture(script: dict[str, str], calls: list[str]):
    """script maps url -> 'ok' | 'refuse' | 'refuse500' | 'die'."""

    def fake(**kwargs):
        url = kwargs["url"]
        calls.append(url)
        action = script[url]
        if action == "refuse":
            raise RealChromeNavigationHTTPError(
                f"target navigation for {url} was refused (status=429)", http_status=429
            )
        if action == "refuse500":
            raise RealChromeNavigationHTTPError(
                f"target navigation for {url} was refused (status=500)", http_status=500
            )
        if action == "die":
            raise RuntimeError("TimeoutError: Page.goto")
        return 0, "ok"

    return fake


def test_first_429_stops_and_resume_retries_only_failed_and_unattempted_slots(
    tmp_path, monkeypatch
):
    calls: list[str] = []
    script = {URLS[0]: "ok", URLS[1]: "refuse", URLS[2]: "refuse",
              URLS[3]: "refuse", URLS[4]: "ok", URLS[5]: "ok"}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    exit_code, message = _run(tmp_path)
    assert exit_code == batch.REDDIT_CIRCUIT_BREAK_EXIT_CODE
    assert calls == URLS[:2]
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is True
    assert summary["circuit_breaker"]["tripped_after_slot"] == "slot_002"
    assert summary["circuit_breaker"]["reason"] == "http_429"
    assert summary["circuit_breaker"]["slots_not_attempted"] == [
        "slot_003", "slot_004", "slot_005", "slot_006"
    ]
    assert [r["slot_id"] for r in summary["results"]] == [
        "slot_001", "slot_002",
    ]
    assert summary["results"][1]["navigation_http_status"] == 429

    # A later explicit resume after cooldown carries the success, retries the
    # refused slot, and then continues the untouched tail.
    calls.clear()
    script.update({url: "ok" for url in URLS})
    exit_code, message = _run(tmp_path, resume=True)
    assert exit_code == 0
    assert (tmp_path / "out" / "batch_summary.superseded_01.json").exists()
    assert calls == URLS[1:]
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert summary["carried_slot_count"] == 1
    assert len(summary["results"]) == 6


def test_non_refusal_failures_never_trip_the_breaker(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {url: "die" for url in URLS}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    _, message = _run(tmp_path)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert len(summary["results"]) == 6


def test_a_success_resets_the_refusal_streak(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {URLS[0]: "refuse500", URLS[1]: "refuse500", URLS[2]: "ok",
              URLS[3]: "refuse500", URLS[4]: "refuse500", URLS[5]: "ok"}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    _, message = _run(tmp_path)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert len(summary["results"]) == 6


def test_zero_disables_the_breaker(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {url: "refuse500" for url in URLS}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    _, message = _run(tmp_path, breaker=0)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert len(summary["results"]) == 6


def test_first_429_is_not_disabled_by_the_generic_refusal_threshold(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {url: "refuse" for url in URLS}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    exit_code, message = _run(tmp_path, breaker=0)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert exit_code == batch.REDDIT_CIRCUIT_BREAK_EXIT_CODE
    assert calls == [URLS[0]]
    assert summary["circuit_breaker"]["reason"] == "http_429"


def test_main_forwards_the_breaker_threshold(tmp_path, monkeypatch):
    url_list = tmp_path / "urls.json"
    url_list.write_text(json.dumps(["https://old.reddit.com/r/x/comments/aa/p/"]), encoding="utf-8")
    seen: dict = {}
    monkeypatch.setattr(
        batch, "run_reddit_old_http_batch", lambda **kw: (seen.update(kw), (0, "ok"))[1]
    )
    batch.main(
        [
            "--url-list", str(url_list),
            "--output-root", str(tmp_path / "out"),
            "--decision-question", "q",
            "--refusal-circuit-breaker", "5",
        ]
    )
    assert seen["refusal_circuit_breaker"] == 5
