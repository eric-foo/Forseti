"""Behaviour bound: a snapshot of the wrong page never commits as success.

The www batch reuses a persistent tab in the operator's real Chrome. On
2026-08-03 a human navigated that tab while a wave ran, and 21 slots committed
packets whose manifests honestly named a different (years-old) thread while
the journal rows read success. The final url is now checked against a
caller-supplied target identity pattern before any packet is written; a
mismatch is a typed RealChromeWrongPageError that carries both urls and no
http_status (so refusal circuit breakers ignore it).
"""
from __future__ import annotations

import json

import pytest

from runners import run_reddit_old_http_batch as batch
from runners import run_source_capture_realchrome_cdp_packet as cdp

WWW_URL = "https://www.reddit.com/r/Indiemakeupandmore/comments/1v8wez7/whatcha_haulin/"
WRONG_URL = "https://www.reddit.com/r/boxycharm/comments/lcw4s4/how_do_you_guys_use_the_jet_lag_mask/"


class _FixedPageEngine:
    """Engine stub whose snapshot always lands on ``final_url``."""

    def __init__(self, final_url: str):
        self.final_url = final_url

    def capture(self, **kwargs) -> cdp.RealChromeCDPCaptureResult:
        return cdp.RealChromeCDPCaptureResult(
            requested_url=kwargs["url"],
            final_url=self.final_url,
            title="t",
            rendered_dom="<html><body>x</body></html>",
            visible_text="x",
            screenshot_png=None,
            http_status=200,
            warm_hop_url=None,
            warm_hop_blocked=None,
        )


def test_wrong_page_error_is_typed_and_breaker_invisible():
    exc = cdp.RealChromeWrongPageError(
        "wrong page", requested_url=WWW_URL, final_url=WRONG_URL
    )
    assert isinstance(exc, cdp.RealChromeCDPUnavailable)
    assert exc.requested_url == WWW_URL
    assert exc.final_url == WRONG_URL
    # No http_status attribute contract: the batch refusal counter keys on
    # hasattr(exc, "http_status"), and a local tab race must not trip it.
    assert not hasattr(exc, "http_status")


def test_thread_identity_rejects_a_matching_path_on_another_host():
    lookalike = f"https://example.com/?next={WWW_URL}"
    assert not batch._same_www_thread_identity(lookalike, WWW_URL)
    assert batch._same_www_thread_identity(
        "https://www.reddit.com/r/elsewhere/comments/1v8wez7/renamed/?share=1",
        WWW_URL,
    )


def test_mismatched_final_url_raises_before_any_packet_is_written(tmp_path):
    out = tmp_path / "packets"
    with pytest.raises(cdp.RealChromeWrongPageError) as excinfo:
        cdp.run_source_capture_realchrome_cdp_packet(
            url=WWW_URL,
            source_family="reddit_thread",
            source_surface="www_reddit_realchrome_cdp",
            decision_question="q",
            output_directory=out,
            target_identity_pattern=r"/comments/1v8wez7(?:[/?#]|$)",
            engine=_FixedPageEngine(WRONG_URL),
        )
    assert excinfo.value.final_url == WRONG_URL
    # Nothing durable exists for the wrong page.
    assert not out.exists() or not any(out.iterdir())


def test_matching_final_url_passes_the_guard(tmp_path):
    # A slug/query variant of the SAME thread id is a legitimate redirect and
    # must pass; only the thread identity is bound.
    exit_code, message = cdp.run_source_capture_realchrome_cdp_packet(
        url=WWW_URL,
        source_family="reddit_thread",
        source_surface="www_reddit_realchrome_cdp",
        decision_question="q",
        output_directory=tmp_path / "packets",
        target_identity_pattern=r"/comments/1v8wez7(?:[/?#]|$)",
        engine=_FixedPageEngine(
            "https://www.reddit.com/r/Indiemakeupandmore/comments/1v8wez7/renamed_slug/?share=1"
        ),
    )
    assert exit_code == 0, message


def test_no_pattern_keeps_todays_unchecked_behavior(tmp_path):
    exit_code, message = cdp.run_source_capture_realchrome_cdp_packet(
        url=WWW_URL,
        source_family="reddit_thread",
        source_surface="www_reddit_realchrome_cdp",
        decision_question="q",
        output_directory=tmp_path / "packets",
        engine=_FixedPageEngine(WRONG_URL),
    )
    assert exit_code == 0, message


def test_www_batch_binds_the_thread_identity(tmp_path, monkeypatch):
    seen: dict[str, object] = {}

    def spy(**kwargs):
        seen["target_identity_check"] = kwargs.get("target_identity_check")
        raise cdp.RealChromeCDPUnavailable("stop here; only the binding is under test")

    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", spy)
    batch.run_reddit_old_http_batch(
        slots=[batch.BatchSlot(slot_id="s1", url=WWW_URL)],
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        cadence_mode="fixed",
        delay_seconds=0.0,
    )
    check = seen["target_identity_check"]
    assert callable(check)
    assert check(WWW_URL)
    assert not check(WRONG_URL)
    assert not check(f"https://example.com/?next={WWW_URL}")


def test_batch_row_records_wrong_page_without_breaker_pressure(tmp_path, monkeypatch):
    def wrong_page(**kwargs):
        raise cdp.RealChromeWrongPageError(
            f"snapshot landed on {WRONG_URL!r}, which does not match the target "
            f"identity pattern for requested {kwargs['url']!r}",
            requested_url=kwargs["url"],
            final_url=WRONG_URL,
        )

    monkeypatch.setattr(cdp, "run_source_capture_realchrome_cdp_packet", wrong_page)
    exit_code, message = batch.run_reddit_old_http_batch(
        slots=[
            batch.BatchSlot(slot_id=f"s{i}", url=WWW_URL) for i in range(1, 5)
        ],
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        cadence_mode="fixed",
        delay_seconds=0.0,
    )
    assert exit_code == 0
    summary = json.loads(
        (tmp_path / "out" / "batch_summary.json").read_text(encoding="utf-8")
    )
    rows = summary["results"]
    # Four consecutive wrong-page failures exceed the refusal threshold (3)
    # yet must not trip the breaker: they are local races, not server refusals.
    assert len(rows) == 4
    assert all(row["capture_exit"] == 2 for row in rows)
    assert all(row["navigation_http_status"] is None for row in rows)
    assert all(
        row["capture_message"].startswith("RealChromeWrongPageError:") for row in rows
    )
    assert summary["circuit_breaker"]["tripped"] is False
