"""Behaviour bound: a server-side HTTP refusal is never misread as CDP loss.

In the 2026-08-01 www batch, 11 of 54 slots failed with
net::ERR_HTTP_RESPONSE_CODE_FAILURE at Page.goto and were reported as
RealChromeCDPUnavailable with no status code -- a Reddit throttling burst
misfiled as local Chrome failure. The refusal now has its own type carrying
the observed status, and the batch row records that status as a field.
"""
from __future__ import annotations

import json

import pytest

from runners import run_reddit_old_http_batch as batch
from runners import run_source_capture_realchrome_cdp_packet as cdp

WWW_URL = "https://www.reddit.com/r/Sephora/comments/1v87d9j/talc/"


def test_navigation_http_error_is_a_typed_cdp_unavailable_subclass():
    # Subclassing keeps every existing `except RealChromeCDPUnavailable`
    # handler working (exit 3, batch row capture); the distinct type and
    # status make the refusal diagnosable after the fact.
    exc = cdp.RealChromeNavigationHTTPError("refused", http_status=429)
    assert isinstance(exc, cdp.RealChromeCDPUnavailable)
    assert exc.http_status == 429
    assert cdp.RealChromeNavigationHTTPError("refused", http_status=None).http_status is None


def test_navigation_failure_classification():
    chromium_refusal = RuntimeError(
        "Page.goto: net::ERR_HTTP_RESPONSE_CODE_FAILURE at https://www.reddit.com/..."
    )
    timeout = RuntimeError("Page.goto: Timeout 20000ms exceeded.")
    assert cdp._is_navigation_http_error(chromium_refusal, None)
    assert cdp._is_navigation_http_error(timeout, 429)
    assert cdp._is_navigation_http_error(timeout, 503)
    assert not cdp._is_navigation_http_error(timeout, None)
    # A 2xx main-frame response observed alongside an unrelated error is not
    # an HTTP refusal.
    assert not cdp._is_navigation_http_error(timeout, 200)


def test_batch_row_records_the_refused_status(tmp_path, monkeypatch):
    def refuse(**kwargs):
        raise cdp.RealChromeNavigationHTTPError(
            f"target navigation for {kwargs['url']} was refused with an HTTP error "
            "response (status=429); server-side refusal, not CDP unavailability.",
            http_status=429,
        )

    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", refuse)
    exit_code, message = batch.run_reddit_old_http_batch(
        slots=[batch.BatchSlot(slot_id="s1", url=WWW_URL)],
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        cadence_mode="fixed",
        delay_seconds=0.0,
    )
    assert exit_code == 0
    summary = json.loads((tmp_path / "out" / "batch_summary.json").read_text(encoding="utf-8"))
    (row,) = summary["results"]
    assert row["capture_exit"] == 2
    assert row["navigation_http_status"] == 429
    assert row["capture_message"].startswith("RealChromeNavigationHTTPError:")
    # The journal row carries the same field, so a killed run keeps it too.
    (journal_row,) = [
        json.loads(line)
        for line in (tmp_path / "out" / "batch_progress.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert journal_row["navigation_http_status"] == 429


def test_batch_row_status_stays_none_for_non_http_failures(tmp_path, monkeypatch):
    def die(**kwargs):
        raise cdp.RealChromeCDPUnavailable("could not attach to a real Chrome over CDP")

    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", die)
    batch.run_reddit_old_http_batch(
        slots=[batch.BatchSlot(slot_id="s1", url=WWW_URL)],
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        cadence_mode="fixed",
        delay_seconds=0.0,
    )
    summary = json.loads((tmp_path / "out" / "batch_summary.json").read_text(encoding="utf-8"))
    (row,) = summary["results"]
    assert row["capture_exit"] == 2
    assert row["navigation_http_status"] is None
