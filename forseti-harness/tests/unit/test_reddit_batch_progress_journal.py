"""Behaviour bound for the batch runner's durable progress journal and resume.

The 2026-08-01 www batch was killed externally between slots 75 and 76 of 127
(session teardown, not a runner defect). Because the summary was written only
after the final slot, the run's entire record vanished even though every
captured packet was already safely in the lake. The journal makes each slot's
outcome durable the moment it finishes; --resume makes recovery cost zero
additional Reddit requests for slots already attempted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners import run_reddit_old_http_batch as batch

URLS = [
    f"https://old.reddit.com/r/Sephora/comments/1v87d9{n}/talc/" for n in ("a", "b", "c")
]
SLOTS = [
    batch.BatchSlot(slot_id=f"slot_{i:03d}", url=url) for i, url in enumerate(URLS, start=1)
]


def _fake_capture_factory(calls: list[str], *, die_on: str | None = None):
    def fake_capture(**kwargs):
        url = kwargs["url"]
        if die_on is not None and url == die_on:
            # BaseException, like the real external kill: the per-slot
            # Exception handler must not swallow it into a fake failure row.
            raise KeyboardInterrupt(f"killed at {url}")
        calls.append(url)
        return 0, "ok"

    return fake_capture


def _run(tmp_path: Path, *, resume: bool = False):
    return batch.run_reddit_old_http_batch(
        slots=SLOTS,
        output_root=tmp_path / "out",
        decision_question="q",
        cadence_mode="fixed",
        delay_seconds=0.0,
        resume=resume,
    )


def test_each_slot_is_journaled_before_the_run_can_die(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls, die_on=URLS[2])
    )
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path)

    out = tmp_path / "out"
    assert not (out / "batch_summary.json").exists()
    lines = (out / "batch_progress.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines]
    # The two slots that finished before the kill are durably recorded; the
    # killed slot has no row and is therefore the resume point.
    assert [row["slot_id"] for row in rows] == ["slot_001", "slot_002"]
    assert all(row["capture_exit"] == 0 for row in rows)


def test_an_interrupted_output_root_refuses_a_fresh_run_without_resume(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls, die_on=URLS[2])
    )
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path)
    with pytest.raises(ValueError, match="--resume"):
        _run(tmp_path)
    # The refusal must fire before any new Reddit request.
    assert calls == URLS[:2]


def test_resume_carries_journaled_slots_and_requests_only_the_rest(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls, die_on=URLS[2])
    )
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path)

    calls.clear()
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls)
    )
    exit_code, message = _run(tmp_path, resume=True)
    assert exit_code == 0
    # Exactly one request: the slot with no journal row. Journaled slots are
    # never re-requested regardless of their exit code (no retry escalation).
    assert calls == [URLS[2]]

    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["resumed"] is True
    assert summary["carried_slot_count"] == 2
    assert summary["url_count"] == 3
    assert [row["slot_id"] for row in summary["results"]] == [
        "slot_001", "slot_002", "slot_003",
    ]
    assert summary["capture_success_count"] == 3


def test_resume_refuses_a_journal_from_a_different_batch(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls, die_on=URLS[2])
    )
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path)

    foreign_slots = [
        batch.BatchSlot(
            slot_id="slot_001",
            url="https://old.reddit.com/r/Sephora/comments/zzzzzz/other/",
        )
    ]
    with pytest.raises(ValueError, match="different batch"):
        batch.run_reddit_old_http_batch(
            slots=foreign_slots,
            output_root=tmp_path / "out",
            decision_question="q",
            cadence_mode="fixed",
            delay_seconds=0.0,
            resume=True,
        )


def test_resume_with_nothing_journaled_is_refused(tmp_path):
    with pytest.raises(ValueError, match="no progress journal"):
        batch.run_reddit_old_http_batch(
            slots=SLOTS,
            output_root=tmp_path / "out",
            decision_question="q",
            cadence_mode="fixed",
            delay_seconds=0.0,
            resume=True,
        )


def test_completed_summary_is_not_moved_when_nothing_remains_to_resume(
    tmp_path, monkeypatch
):
    calls: list[str] = []
    monkeypatch.setattr(
        batch, "run_source_capture_http_packet", _fake_capture_factory(calls)
    )
    _, message = _run(tmp_path)
    summary_path = Path(message)
    original_summary = summary_path.read_bytes()

    with pytest.raises(ValueError, match="nothing to resume"):
        _run(tmp_path, resume=True)

    assert summary_path.read_bytes() == original_summary
    assert not list(summary_path.parent.glob("batch_summary.superseded_*.json"))
    assert calls == URLS


def test_main_forwards_resume(tmp_path, monkeypatch):
    url_list = tmp_path / "urls.json"
    url_list.write_text(json.dumps(URLS), encoding="utf-8")
    seen: dict = {}
    monkeypatch.setattr(
        batch, "run_reddit_old_http_batch", lambda **kw: (seen.update(kw), (0, "ok"))[1]
    )
    batch.main(
        [
            "--url-list", str(url_list),
            "--output-root", str(tmp_path / "out"),
            "--decision-question", "q",
            "--resume",
        ]
    )
    assert seen["resume"] is True
