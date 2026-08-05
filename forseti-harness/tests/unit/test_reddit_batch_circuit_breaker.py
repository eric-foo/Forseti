"""Behaviour bound for the batch runner's consecutive-refusal circuit breaker.

The 2026-08-01 leaderboard run spent 8 consecutive server-refused requests
(HTTP 429) learning what the first 2 already said. The breaker stops the
batch on N consecutive typed refusals; unattempted slots get no journal row,
so --resume picks up exactly there. It is a stop, never a retry.
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
    """script maps url -> 'ok' | 'refuse' | 'die'."""

    def fake(**kwargs):
        url = kwargs["url"]
        calls.append(url)
        action = script[url]
        if action == "refuse":
            raise RealChromeNavigationHTTPError(
                f"target navigation for {url} was refused (status=429)", http_status=429
            )
        if action == "die":
            raise RuntimeError("TimeoutError: Page.goto")
        return 0, "ok"

    return fake


def test_breaker_stops_after_consecutive_refusals_and_resume_continues(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {URLS[0]: "ok", URLS[1]: "refuse", URLS[2]: "refuse",
              URLS[3]: "refuse", URLS[4]: "ok", URLS[5]: "ok"}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    exit_code, message = _run(tmp_path)
    assert exit_code == 0
    # Three consecutive refusals trip the breaker; slots 5 and 6 were never
    # asked for.
    assert calls == URLS[:4]
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is True
    assert summary["circuit_breaker"]["tripped_after_slot"] == "slot_004"
    assert summary["circuit_breaker"]["slots_not_attempted"] == ["slot_005", "slot_006"]
    assert [r["slot_id"] for r in summary["results"]] == [
        "slot_001", "slot_002", "slot_003", "slot_004",
    ]
    assert summary["results"][1]["navigation_http_status"] == 429

    # A later resume attempts exactly the never-attempted slots -- the
    # refused ones are journaled as attempted and are not re-requested. The
    # tripped run's summary is set aside as evidence, not erased and not a
    # blocker.
    calls.clear()
    exit_code, message = _run(tmp_path, resume=True)
    assert exit_code == 0
    assert (tmp_path / "out" / "batch_summary.superseded_01.json").exists()
    assert calls == [URLS[4], URLS[5]]
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert summary["carried_slot_count"] == 4
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
    script = {URLS[0]: "refuse", URLS[1]: "refuse", URLS[2]: "ok",
              URLS[3]: "refuse", URLS[4]: "refuse", URLS[5]: "ok"}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    _, message = _run(tmp_path)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert len(summary["results"]) == 6


def test_zero_disables_the_breaker(tmp_path, monkeypatch):
    calls: list[str] = []
    script = {url: "refuse" for url in URLS}
    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", _capture(script, calls))
    _, message = _run(tmp_path, breaker=0)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["circuit_breaker"]["tripped"] is False
    assert len(summary["results"]) == 6


def test_normal_non_success_response_also_trips_the_breaker(tmp_path, monkeypatch):
    """Playwright may return a 429 Response instead of raising from goto."""
    calls: list[str] = []

    def refused_packet(**kwargs):
        calls.append(kwargs["slot"].url)
        packet = kwargs["output_directory"]
        raw = packet / "raw"
        raw.mkdir(parents=True)
        # Real raw-failure packets carry a double numeric prefix from
        # retention renumbering; the guard must match this production shape.
        (raw / "03_04_realchrome_snapshot_metadata.json").write_text(
            json.dumps({"http_response_status": 429}), encoding="utf-8"
        )
        return batch.CONTENT_EXTRACTION_FAILED_EXIT_CODE, str(packet)

    monkeypatch.setattr(batch, "_capture_www_thread", refused_packet)
    _, message = _run(tmp_path)
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert calls == URLS[:3]
    assert summary["circuit_breaker"]["tripped"] is True
    assert [row["navigation_http_status"] for row in summary["results"]] == [429, 429, 429]


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
