from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from runners import run_source_capture_same_host_http_batch as batch_module
from runners.run_source_capture_same_host_http_batch import (
    SameHostHttpJob,
    run_same_host_http_batch,
)
from runners.run_source_capture_http_packet import DirectHttpPacketOutcome


def _outcome(
    *,
    status: int = 200,
    exit_code: int = 0,
    retry_after: str | None = None,
    body_classification: str = "content_unverified",
    body_classification_signal: str | None = None,
    login_gate_signal: str | None = None,
    content_capture_allowed: bool = True,
) -> DirectHttpPacketOutcome:
    return DirectHttpPacketOutcome(
        exit_code=exit_code,
        message="captured",
        http_status=status,
        retry_after=retry_after,
        retry_after_disposition="captured" if retry_after is not None else "absent",
        content_capture_allowed=content_capture_allowed,
        body_classification=body_classification,
        body_classification_signal=body_classification_signal,
        login_gate_signal=login_gate_signal,
        access_block_reason=None if content_capture_allowed else "test_refusal",
    )


def _publish_outcome(kwargs: dict[str, object], outcome: DirectHttpPacketOutcome) -> None:
    observer = kwargs["outcome_observer"]
    assert callable(observer)
    observer(outcome)


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
        outcome = _outcome()
        _publish_outcome(kwargs, outcome)
        return outcome.exit_code, outcome.message

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
        outcome = _outcome(
            status=429,
            retry_after="60",
            content_capture_allowed=False,
        )
        _publish_outcome(kwargs, outcome)
        return outcome.exit_code, outcome.message

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
        outcome = _outcome(
            status=200,
            body_classification="block_shell",
            body_classification_signal="test_block",
            content_capture_allowed=False,
        )
        _publish_outcome(kwargs, outcome)
        return outcome.exit_code, outcome.message

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


@pytest.mark.parametrize("bad_gap", [float("nan"), float("inf"), float("-inf")])
def test_batch_rejects_non_finite_gap_before_output_or_capture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bad_gap: float
) -> None:
    output = tmp_path / "batch"

    def unexpected_capture(**_kwargs: object) -> tuple[int, str]:
        raise AssertionError("capture must not run")

    monkeypatch.setattr(batch_module, "run_source_capture_http_packet", unexpected_capture)
    with pytest.raises(ValueError, match="must be finite"):
        run_same_host_http_batch(
            jobs=_jobs(),
            output_root=output,
            source_family="web_page",
            source_surface="direct_http",
            capture_context="test",
            minimum_gap_seconds=bad_gap,
        )

    assert not output.exists()


def test_batch_writes_attempted_and_unrun_accounting_before_reraising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    jobs = _jobs() + [
        SameHostHttpJob("three", "https://example.test/three", "Capture three?")
    ]
    calls: list[str] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(str(kwargs["url"]))
        if len(calls) == 2:
            raise RuntimeError("inner runner exploded")
        outcome = _outcome()
        _publish_outcome(kwargs, outcome)
        return outcome.exit_code, outcome.message

    monkeypatch.setattr(batch_module, "run_source_capture_http_packet", fake_capture)
    output = tmp_path / "batch"

    with pytest.raises(RuntimeError, match="inner runner exploded"):
        run_same_host_http_batch(
            jobs=jobs,
            output_root=output,
            source_family="web_page",
            source_surface="direct_http",
            capture_context="test",
            sleep=lambda _seconds: None,
        )

    summary = json.loads(
        (output / "same_host_http_batch_summary.json").read_text(encoding="utf-8")
    )
    assert [item["result"] for item in summary["attempts"]] == [
        "captured",
        "runner_exception",
    ]
    assert summary["unrun_jobs"] == ["three"]
    assert summary["completed"] is False


@dataclass(frozen=True)
class _RouteResponse:
    status: int
    body: bytes
    headers: dict[str, str]


@pytest.fixture
def batch_http_server():
    routes = {
        "/ok": _RouteResponse(200, b"ordinary source content", {"Content-Type": "text/html"}),
        "/login": _RouteResponse(
            200,
            b'<html><form action="/login">Sign in to continue</form></html>',
            {"Content-Type": "text/html"},
        ),
        "/second": _RouteResponse(200, b"must stay unrun", {"Content-Type": "text/html"}),
        "/rate-empty": _RouteResponse(429, b"", {"Retry-After": "600"}),
        "/rate-large-length": _RouteResponse(
            429,
            b"abcdef",
            {"Retry-After": "601", "Content-Length": "6"},
        ),
        "/rate-large-stream": _RouteResponse(429, b"abcdef", {"Retry-After": "602"}),
        "/rate-unsafe": _RouteResponse(429, b"", {"Retry-After": "x" * 257}),
        "/cf-mitigated": _RouteResponse(
            200,
            b"benign-looking shell",
            {"Content-Type": "text/html", "CF-Mitigated": "challenge"},
        ),
        "/encoded": _RouteResponse(
            200,
            b"encoded-looking bytes",
            {"Content-Type": "text/html", "Content-Encoding": "gzip"},
        ),
    }
    requested_paths: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            requested_paths.append(self.path)
            route = routes[self.path]
            self.send_response(route.status)
            for key, value in route.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if route.body:
                self.wfile.write(route.body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", requested_paths
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _server_jobs(base_url: str, first_path: str) -> list[SameHostHttpJob]:
    return [
        SameHostHttpJob("one", f"{base_url}{first_path}", "Capture one?"),
        SameHostHttpJob("two", f"{base_url}/second", "Capture two?"),
    ]


def test_integration_login_shell_stops_queue_from_authoritative_admission(
    batch_http_server, tmp_path: Path
) -> None:
    base_url, requested_paths = batch_http_server
    exit_code, summary = run_same_host_http_batch(
        jobs=_server_jobs(base_url, "/login"),
        output_root=tmp_path / "batch",
        source_family="web_page",
        source_surface="direct_http",
        capture_context="integration test",
        sleep=lambda _seconds: None,
    )

    assert exit_code == 3
    assert requested_paths == ["/login"]
    assert summary["unrun_jobs"] == ["two"]
    assert summary["attempts"][0]["result"] == "stopped_on_failure"
    assert summary["attempts"][0]["login_gate_signal"] == "login_redirect"
    assert summary["attempts"][0]["content_capture_allowed"] is False


@pytest.mark.parametrize(
    ("path", "max_bytes", "expected_retry_after", "expected_disposition"),
    [
        ("/rate-empty", 5, "600", "captured"),
        ("/rate-large-length", 5, "601", "captured"),
        ("/rate-large-stream", 5, "602", "captured"),
        ("/rate-unsafe", 5, None, "rejected_unsafe"),
    ],
)
def test_integration_rejected_response_retains_status_and_retry_after(
    batch_http_server,
    tmp_path: Path,
    path: str,
    max_bytes: int,
    expected_retry_after: str | None,
    expected_disposition: str,
) -> None:
    base_url, requested_paths = batch_http_server
    exit_code, summary = run_same_host_http_batch(
        jobs=_server_jobs(base_url, path),
        output_root=tmp_path / path.removeprefix("/"),
        source_family="web_page",
        source_surface="direct_http",
        capture_context="integration test",
        max_bytes=max_bytes,
        sleep=lambda _seconds: None,
    )

    assert exit_code == 3
    assert requested_paths == [path]
    assert summary["unrun_jobs"] == ["two"]
    attempt = summary["attempts"][0]
    assert attempt["http_status"] == 429
    assert attempt["retry_after"] == expected_retry_after
    assert attempt["retry_after_disposition"] == expected_disposition


@pytest.mark.parametrize(
    ("path", "expected_classification", "expected_signal"),
    [
        ("/cf-mitigated", "block_shell", "cloudflare_mitigated"),
        ("/encoded", "content_unverified", "encoded_body_uninspectable"),
    ],
)
def test_integration_response_headers_stop_uninspectable_capture(
    batch_http_server,
    tmp_path: Path,
    path: str,
    expected_classification: str,
    expected_signal: str,
) -> None:
    base_url, requested_paths = batch_http_server
    exit_code, summary = run_same_host_http_batch(
        jobs=_server_jobs(base_url, path),
        output_root=tmp_path / path.removeprefix("/"),
        source_family="web_page",
        source_surface="direct_http",
        capture_context="integration test",
        sleep=lambda _seconds: None,
    )

    assert exit_code == 3
    assert requested_paths == [path]
    attempt = summary["attempts"][0]
    assert attempt["body_classification"] == expected_classification
    assert attempt["body_classification_signal"] == expected_signal
    assert attempt["content_capture_allowed"] is False
