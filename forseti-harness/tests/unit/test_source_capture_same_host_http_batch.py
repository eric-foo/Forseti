from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners import run_source_capture_same_host_http_batch as batch_module
from runners.run_source_capture_same_host_http_batch import (
    SameHostHttpJob,
    run_same_host_http_batch,
)


def _write_packet(
    packet_directory: Path,
    *,
    status: int,
    retry_after: str | None = None,
    body_classification: str = "content_unverified",
) -> None:
    raw = packet_directory / "raw"
    raw.mkdir(parents=True)
    (raw / "02_http_response_metadata.json").write_text(
        json.dumps(
            {
                "status": status,
                "retry_after": retry_after,
                "body_classification": body_classification,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _jobs() -> list[SameHostHttpJob]:
    return [
        SameHostHttpJob("one", "https://example.test/one", "Capture one?"),
        SameHostHttpJob("two", "https://example.test/two", "Capture two?"),
    ]


def test_batch_enforces_gap_between_successful_same_host_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(str(kwargs["url"]))
        _write_packet(Path(str(kwargs["output_directory"])), status=200)
        return 0, "captured"

    monkeypatch.setattr(batch_module, "run_source_capture_http_packet", fake_capture)
    exit_code, summary = run_same_host_http_batch(
        jobs=_jobs(),
        output_root=tmp_path / "batch",
        source_family="web_page",
        source_surface="direct_http",
        capture_context="test",
        sleep=sleeps.append,
    )

    assert exit_code == 0
    assert calls == ["https://example.test/one", "https://example.test/two"]
    assert sleeps == [90.0]
    assert summary["completed"] is True
    assert summary["unrun_jobs"] == []


def test_batch_stops_remaining_jobs_when_first_response_is_rate_limited(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(str(kwargs["url"]))
        _write_packet(Path(str(kwargs["output_directory"])), status=429, retry_after="60")
        return 4, "source access failed"

    monkeypatch.setattr(batch_module, "run_source_capture_http_packet", fake_capture)
    exit_code, summary = run_same_host_http_batch(
        jobs=_jobs(),
        output_root=tmp_path / "batch",
        source_family="web_page",
        source_surface="direct_http",
        capture_context="test",
        sleep=sleeps.append,
    )

    assert exit_code == 3
    assert calls == ["https://example.test/one"]
    assert sleeps == []
    assert summary["unrun_jobs"] == ["two"]
    assert summary["attempts"][0]["http_status"] == 429
    assert summary["attempts"][0]["retry_after"] == "60"


def test_batch_stops_on_block_shell_even_if_inner_runner_returns_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(str(kwargs["url"]))
        _write_packet(
            Path(str(kwargs["output_directory"])),
            status=200,
            body_classification="block_shell",
        )
        return 0, "packet preserved with limitation"

    monkeypatch.setattr(batch_module, "run_source_capture_http_packet", fake_capture)
    exit_code, summary = run_same_host_http_batch(
        jobs=_jobs(),
        output_root=tmp_path / "batch",
        source_family="web_page",
        source_surface="direct_http",
        capture_context="test",
        sleep=lambda _seconds: None,
    )

    assert exit_code == 3
    assert calls == ["https://example.test/one"]
    assert summary["unrun_jobs"] == ["two"]
    assert summary["attempts"][0]["body_classification"] == "block_shell"


def test_batch_rejects_mixed_hosts_before_creating_output(tmp_path: Path) -> None:
    jobs = [
        SameHostHttpJob("one", "https://example.test/one", "Capture one?"),
        SameHostHttpJob("two", "https://other.test/two", "Capture two?"),
    ]
    output = tmp_path / "batch"

    with pytest.raises(ValueError, match="same exact hostname"):
        run_same_host_http_batch(
            jobs=jobs,
            output_root=output,
            source_family="web_page",
            source_surface="direct_http",
            capture_context="test",
        )

    assert not output.exists()


def test_batch_refuses_gap_below_polite_floor(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 60"):
        run_same_host_http_batch(
            jobs=_jobs(),
            output_root=tmp_path / "batch",
            source_family="web_page",
            source_surface="direct_http",
            capture_context="test",
            minimum_gap_seconds=59,
        )
