from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError

import pytest

import source_capture.adapters.direct_http as direct_http_module
from runners import run_source_capture_http_packet as http_runner
from runners.run_source_capture_http_packet import DIRECT_HTTP_NON_CLAIMS
from source_capture import CaptureModeCategory
from source_capture.adapters.direct_http import (
    DirectHttpCaptureFailure,
    DirectHttpCaptureFailureKind,
    DirectHttpCaptureSuccess,
    fetch_direct_http_capture,
)
from source_capture.content_extraction import ContentExtractionSpec
from source_capture.reddit_consolidation import build_thread_content_record
from source_capture.retail_capture_profiles import get_retail_capture_profile


@pytest.fixture
def scratch_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "_test_runs"
    path = root / f"source_capture_direct_http_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@dataclass(frozen=True)
class _RouteResponse:
    status: int
    body: bytes
    headers: dict[str, str]


@pytest.fixture
def http_server():
    routes = {
        "/ok": _RouteResponse(
            status=200,
            body=b"hello direct http\n",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "ETag": '"etag-123"',
                "Last-Modified": "Tue, 02 Jun 2026 00:00:00 GMT",
                "Set-Cookie": "session=should_not_be_preserved",
            },
        ),
        "/missing-with-body": _RouteResponse(
            status=404,
            body=b"not found but body present\n",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
            },
        ),
        "/rate-limited": _RouteResponse(
            status=429,
            body=b"local_rate_limited\n",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Retry-After": "60",
            },
        ),
        "/empty": _RouteResponse(
            status=204,
            body=b"",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
            },
        ),
        "/too-large": _RouteResponse(
            status=200,
            body=b"abcdef",
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": "6",
            },
        ),
        "/redirect": _RouteResponse(
            status=302,
            body=b"",
            headers={
                "Location": "/ok",
            },
        ),
        "/redirect-login": _RouteResponse(
            status=302,
            body=b"",
            headers={
                "Location": "/login",
            },
        ),
        "/login": _RouteResponse(
            status=200,
            body=b'<html><form action="/login">Sign in to continue</form></html>',
            headers={
                "Content-Type": "text/html; charset=utf-8",
            },
        ),
        "/block-shell": _RouteResponse(
            status=200,
            body=b"<html><body>You have been blocked by network security.</body></html>",
            headers={
                "Content-Type": "text/html; charset=utf-8",
            },
        ),
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            route = routes.get(self.path)
            if route is None:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"unexpected path")
                return

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
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_fetch_direct_http_capture_read_timeout_is_honest_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # A read-phase socket timeout fires during response.read(), AFTER urlopen returned, so it is
    # not a URLError. It must surface as an honest DirectHttpCaptureFailure(TIMEOUT), never an
    # uncaught crash (observed live: a slow archive aborting a whole capture).
    class _ReadTimesOut:
        reason = "OK"
        headers: dict[str, str] = {}

        def getcode(self) -> int:
            return 200

        def geturl(self) -> str:
            return "https://example.com/slow"

        def read(self, *_args: object, **_kwargs: object) -> bytes:
            raise TimeoutError("The read operation timed out")

        def __enter__(self) -> "_ReadTimesOut":
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

    monkeypatch.setattr(
        direct_http_module, "_open_direct_http", lambda request, *, timeout_seconds: _ReadTimesOut()
    )
    result = fetch_direct_http_capture(url="https://example.com/slow", timeout_seconds=5, max_bytes=1024)
    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind is DirectHttpCaptureFailureKind.TIMEOUT
    assert "timed out" in result.message.lower()


def test_fetch_direct_http_capture_read_oserror_is_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # A non-timeout read-phase socket error (e.g. connection reset) likewise fires after urlopen and
    # is not a URLError; record an honest NETWORK_ERROR failure rather than crashing the caller.
    class _ReadResets:
        reason = "OK"
        headers: dict[str, str] = {}

        def getcode(self) -> int:
            return 200

        def geturl(self) -> str:
            return "https://example.com/reset"

        def read(self, *_args: object, **_kwargs: object) -> bytes:
            raise ConnectionResetError("connection reset by peer")

        def __enter__(self) -> "_ReadResets":
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

    monkeypatch.setattr(
        direct_http_module, "_open_direct_http", lambda request, *, timeout_seconds: _ReadResets()
    )
    result = fetch_direct_http_capture(url="https://example.com/reset", timeout_seconds=5, max_bytes=1024)
    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind is DirectHttpCaptureFailureKind.NETWORK_ERROR


def test_fetch_direct_http_capture_returns_selected_metadata_for_success(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/ok", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureSuccess)
    assert result.status == 200
    assert result.body == b"hello direct http\n"
    assert result.metadata["requested_url"] == f"{http_server}/ok"
    assert result.metadata["final_url"] == f"{http_server}/ok"
    assert result.metadata["content_type"] == "text/plain; charset=utf-8"
    assert result.metadata["etag"] == '"etag-123"'
    assert result.metadata["last_modified"] == "Tue, 02 Jun 2026 00:00:00 GMT"
    assert result.metadata["byte_count"] == len(result.body)
    assert "set_cookie" not in result.metadata


@pytest.mark.parametrize(
    ("body", "expected_exit"),
    [
        (
            b'<script id="__NEXT_DATA__">{"averageRating":4.4,"numberOfReviews":41}</script>'
            b"Vitamasques Cherry Vegan Collagen Lip Mask",
            0,
        ),
        (b"<html><body>navigation shell</body></html>", 4),
    ],
)
def test_direct_http_runner_enforces_walmart_profile_after_packet_write(
    monkeypatch: pytest.MonkeyPatch,
    scratch_dir: Path,
    body: bytes,
    expected_exit: int,
) -> None:
    url = (
        "https://www.walmart.com/ip/Vitamasques-Cherry-Vegan-Collagen-Lip-Mask-"
        "Moisturise-Plump-One-Patch/2150828728"
    )

    def fake_capture(**kwargs: object) -> DirectHttpCaptureSuccess:
        return DirectHttpCaptureSuccess(
            requested_url=url,
            final_url=url,
            status=200,
            reason="OK",
            metadata={
                "requested_url": url,
                "final_url": url,
                "capture_timestamp": "2026-07-11T00:00:00Z",
            },
            body=body,
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(http_runner, "fetch_direct_http_capture", fake_capture)
    output = scratch_dir / f"walmart_profile_{expected_exit}"

    exit_code, _ = http_runner.run_source_capture_http_packet(
        url=url,
        source_family="retail_pdp",
        source_surface="direct_http",
        decision_question="Does direct state satisfy the Walmart aggregate profile?",
        output_directory=output,
        capture_context="unit test",
        operator_category="direct_http_cli_operator",
        capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
        session_id=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        retail_capture_profile=get_retail_capture_profile("walmart_pdp_aggregate"),
        timeout_seconds=20,
        max_bytes=1024,
    )

    assert exit_code == expected_exit
    metadata = json.loads(
        (output / "raw/02_http_response_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["retail_capture_profile"]["name"] == "walmart_pdp_aggregate"
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    expected_mode = (
        "source_detail_sufficiency_passed"
        if expected_exit == 0
        else "source_detail_sufficiency_failed"
    )
    assert expected_mode in manifest["visible_mode_changes"]


def test_fetch_direct_http_capture_allows_non_2xx_body(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/missing-with-body", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureSuccess)
    assert result.status == 404
    assert result.body == b"not found but body present\n"
    assert any("access_failed" in item for item in result.limitation_notes)


def test_fetch_direct_http_capture_preserves_safe_retry_after(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/rate-limited", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureSuccess)
    assert result.status == 429
    assert result.metadata["retry_after"] == "60"
    assert result.metadata["retry_after_disposition"] == "captured"


@pytest.mark.parametrize(
    ("value", "expected_value", "expected_disposition"),
    [
        (None, None, "absent"),
        ("60", "60", "captured"),
        (" ", None, "rejected_unsafe"),
        ("x" * 257, None, "rejected_unsafe"),
    ],
)
def test_retry_after_observation_distinguishes_absent_from_rejected(
    value: str | None,
    expected_value: str | None,
    expected_disposition: str,
) -> None:
    assert direct_http_module._response_header_observation(value) == (
        expected_value,
        expected_disposition,
    )


def test_fetch_direct_http_capture_fails_for_empty_body(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/empty", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind == DirectHttpCaptureFailureKind.NO_BODY
    assert result.status == 204


def test_fetch_direct_http_capture_fails_for_size_cap(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/too-large", timeout_seconds=5, max_bytes=5)

    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind == DirectHttpCaptureFailureKind.SIZE_CAP_EXCEEDED
    assert result.status == 200


def test_fetch_direct_http_capture_classifies_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> object:
        raise URLError("timed out")

    monkeypatch.setattr(direct_http_module, "_open_direct_http", raise_timeout)

    result = fetch_direct_http_capture(url="https://example.test/source", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind == DirectHttpCaptureFailureKind.TIMEOUT
    assert "timed out" in result.message


def test_fetch_direct_http_capture_classifies_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_network_error(*args: object, **kwargs: object) -> object:
        raise URLError("name resolution failed")

    monkeypatch.setattr(direct_http_module, "_open_direct_http", raise_network_error)

    result = fetch_direct_http_capture(url="https://example.test/source", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureFailure)
    assert result.failure_kind == DirectHttpCaptureFailureKind.NETWORK_ERROR
    assert "name resolution failed" in result.message


def test_fetch_direct_http_capture_follows_redirects(http_server: str) -> None:
    result = fetch_direct_http_capture(url=f"{http_server}/redirect", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureSuccess)
    assert result.final_url == f"{http_server}/ok"
    assert result.warning_notes == [f"direct_http followed redirect from {http_server}/redirect to {http_server}/ok"]


def test_fetch_direct_http_capture_ignores_ambient_proxy_env(
    http_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "")

    result = fetch_direct_http_capture(url=f"{http_server}/ok", timeout_seconds=5, max_bytes=1024)

    assert isinstance(result, DirectHttpCaptureSuccess)
    assert result.status == 200
    assert result.body == b"hello direct http\n"


def test_http_runner_writes_packet_with_metadata_and_body_files(http_server: str, scratch_dir: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/ok",
            "--decision-question",
            "What did the HTTP source return before cutoff?",
            "--output",
            str(output_dir),
            "--cutoff-posture",
            "pre_cutoff",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_locator"]["value"] == f"{http_server}/ok"
    assert manifest["source_slices"][0]["locator"]["value"] == f"{http_server}/ok"
    assert manifest["preserved_files"][0]["relative_packet_path"] == "raw/01_http_response_body.bin"
    assert manifest["preserved_files"][1]["relative_packet_path"] == "raw/02_http_response_metadata.json"
    assert manifest["receipt_metadata"]["summary"] == "Direct HTTP packet for web_page with HTTP 200 and 18 preserved body bytes."
    assert "not direct HTTP fetch" not in manifest["receipt_metadata"]["non_claims"]
    assert manifest["receipt_metadata"]["non_claims"] == DIRECT_HTTP_NON_CLAIMS
    for non_claim in DIRECT_HTTP_NON_CLAIMS:
        assert non_claim in (output_dir / "receipt.md").read_text(encoding="utf-8")
    assert (
        manifest["actor_audience_context"]["reason"]
        == "actor or audience context was not supplied to the direct HTTP runner"
    )
    metadata = json.loads((output_dir / "raw" / "02_http_response_metadata.json").read_text(encoding="utf-8"))
    assert metadata["requested_url"] == f"{http_server}/ok"
    assert metadata["final_url"] == f"{http_server}/ok"
    assert metadata["status"] == 200
    assert "Set-Cookie" not in metadata


def test_http_runner_returns_3_and_writes_no_packet_for_empty_body(http_server: str, scratch_dir: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/empty",
            "--decision-question",
            "What did the empty response return?",
            "--output",
            str(output_dir),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 3
    assert "empty body" in result.stderr
    assert not output_dir.exists()


def test_http_runner_returns_0_and_marks_non_2xx_limitation(http_server: str, scratch_dir: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/missing-with-body",
            "--decision-question",
            "What did the missing page return?",
            "--output",
            str(output_dir),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["access_posture"]["value"].startswith("direct_http access_failed with HTTP 404")
    assert any("access_failed" in item for item in manifest["limitations"])


def test_http_runner_preserves_login_redirect_but_marks_access_failed(
    http_server: str, scratch_dir: Path
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "login_redirect_packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/redirect-login",
            "--decision-question",
            "Did Direct HTTP preserve source content rather than an access shell?",
            "--output",
            str(output_dir),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads(
        (output_dir / "raw/02_http_response_metadata.json").read_text(encoding="utf-8")
    )
    preserved_body = (output_dir / "raw/01_http_response_body.bin").read_bytes()

    assert "access_failed" in manifest["access_posture"]["value"]
    assert "login_redirect" in manifest["access_posture"]["value"]
    assert any(
        "visible_capture_limitation" in item and "login" in item
        for item in manifest["limitations"]
    )
    assert metadata["final_url"] == f"{http_server}/login"
    assert b'Sign in to continue' in preserved_body


def test_http_runner_marks_2xx_block_shell_as_access_failed(
    http_server: str, scratch_dir: Path
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "block_shell_packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/block-shell",
            "--decision-question",
            "Did Direct HTTP preserve source content rather than a block shell?",
            "--output",
            str(output_dir),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads(
        (output_dir / "raw/02_http_response_metadata.json").read_text(encoding="utf-8")
    )

    assert "access_failed" in manifest["access_posture"]["value"]
    assert "block_shell" in manifest["access_posture"]["value"]
    assert any(
        "visible_capture_limitation" in item and "block/challenge shell" in item
        for item in manifest["limitations"]
    )
    assert metadata["body_classification"] == "block_shell"
    assert metadata["body_classification_signal"] == "generic_block"


def test_content_mode_does_not_extract_or_discard_login_shell(
    http_server: str, scratch_dir: Path
) -> None:
    output_dir = scratch_dir / "login_content_mode_packet"
    extractor_called = False

    def extractor(_body_text: str, _final_url: str) -> dict:
        nonlocal extractor_called
        extractor_called = True
        return {"incorrectly_promoted": True}

    exit_code, _ = http_runner.run_source_capture_http_packet(
        url=f"{http_server}/redirect-login",
        source_family="web_page",
        source_surface="direct_http",
        decision_question="Can a login shell enter content retention?",
        output_directory=output_dir,
        capture_context="unit test",
        operator_category="direct_http_cli_operator",
        capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
        session_id=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=5,
        max_bytes=1024,
        content_extraction=ContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version="test_v1",
            extractor=extractor,
        ),
    )

    metadata = json.loads(
        (output_dir / "raw/02_http_response_metadata.json").read_text(encoding="utf-8")
    )
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 4
    assert extractor_called is False
    assert metadata["content_extraction"]["retention_outcome"] == "raw_failure"
    assert metadata["content_extraction"]["raw_preserved"] is True
    assert (output_dir / "raw/01_http_response_body.bin").exists()
    assert not (output_dir / "raw/content_record.json").exists()
    assert "access_failed" in manifest["access_posture"]["value"]


def test_content_mode_extracts_visible_old_reddit_thread_with_onboarding_login_form(
    monkeypatch: pytest.MonkeyPatch, scratch_dir: Path
) -> None:
    url = "https://old.reddit.com/r/orca_test/comments/abc/visible_thread/"
    body = b"""\
<html><body>
  <form action="https://www.reddit.com/r/orca_test/post/login">
    Log in
    <div class="g-recaptcha" data-sitekey="public-widget-key"></div>
    <span class="error bad_captcha" style="display:none"></span>
  </form>
  <div class="thing link" id="thing_t3_abc" data-fullname="t3_abc"
       data-subreddit="orca_test" data-author="poster">
    <a class="title">Visible thread</a>
    <div class="usertext-body"><p>Visible post body</p></div>
  </div>
  <div class="thing comment" data-fullname="t1_comment" data-parent="t3_abc"
       data-author="commenter">
    <div class="usertext-body"><p>Visible comment body</p></div>
  </div>
</body></html>
"""

    def fake_capture(**_kwargs: object) -> DirectHttpCaptureSuccess:
        return DirectHttpCaptureSuccess(
            requested_url=url,
            final_url=url,
            status=200,
            reason="OK",
            metadata={
                "requested_url": url,
                "final_url": url,
                "capture_timestamp": "2026-07-23T00:00:00Z",
            },
            body=body,
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(http_runner, "fetch_direct_http_capture", fake_capture)
    output_dir = scratch_dir / "reddit_onboarding_form"

    exit_code, _ = http_runner.run_source_capture_http_packet(
        url=url,
        source_family="reddit_thread",
        source_surface="old_reddit_direct_http",
        decision_question="What source-visible Reddit content is present?",
        output_directory=output_dir,
        capture_context="unit test",
        operator_category="reddit_old_http_batch_operator",
        capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
        session_id=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=5,
        max_bytes=4096,
        content_extraction=ContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version="test_v1",
            extractor=lambda html_text, final_url: build_thread_content_record(
                html_text=html_text,
                source_url=final_url,
            ),
        ),
    )

    metadata = json.loads(
        (output_dir / "raw/02_http_response_metadata.json").read_text(encoding="utf-8")
    )
    content = json.loads(
        (output_dir / "raw/01_content_record.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert metadata["login_gate_signal"] is None
    assert metadata["body_classification"] == "content_unverified"
    assert metadata["body_classification_signal"] is None
    assert metadata["content_extraction"]["retention_outcome"] == "content"
    assert content["thread"]["thread_id"] == "abc"
    assert content["counts"]["comments_parsed"] == 1


def test_http_runner_sets_demand_durability_series_fields(http_server: str, scratch_dir: Path) -> None:
    # Step 2 (durability-series writer): a demand-durability capture POPULATES the hardened
    # additive-optional schema fields as first-class fields -- the Element 1 pins on the slice
    # and the Element 2/4 series facts on the packet -- NOT in capture_context (the pilot
    # stopgap). intended_cadence is the declared CadencePlan.to_dict() shape. INV-1: these are
    # observed facts, never weights or a durable-vs-hollow verdict.
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/ok",
            "--decision-question",
            "Is demand for this SKU durable across the series window?",
            "--output",
            str(output_dir),
            "--series-id",
            "pilot_sdj_bumbum_001",
            "--session-visibility-pin",
            "logged_out_public",
            "--locale-pin",
            "en-US",
            "--currency-pin",
            "USD",
            "--variant-pin-unknown-reason",
            "default on-page variant; not pinned to a specific SKU id",
            "--cold-start-at",
            "2026-06-15T00:00:00Z",
            "--pre-coverage-history-posture",
            "uncovered by construction; series began at first commissioned capture",
            "--intended-cadence-mode",
            "fixed",
            "--intended-cadence-slot-count",
            "14",
            "--intended-cadence-delay-seconds",
            "86400",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    # Element 2 / 4 series facts ride on the packet as first-class schema fields.
    assert manifest["series_id"] == "pilot_sdj_bumbum_001"
    assert manifest["cold_start_at"] == {"status": "known", "value": "2026-06-15T00:00:00Z", "reason": None}
    assert manifest["pre_coverage_history_posture"]["status"] == "known"
    assert manifest["pre_coverage_history_posture"]["value"].startswith("uncovered by construction")
    # intended_cadence is the canonical CadencePlan.to_dict() shape (no invented shape).
    cadence = manifest["intended_cadence"]
    assert cadence["mode"] == "fixed"
    assert cadence["slot_count"] == 14
    assert cadence["delay_seconds"] == 86400.0
    assert cadence["planned_offsets_seconds"][0] == 0.0
    assert cadence["planned_offsets_seconds"][-1] == 1123200.0

    # Element 1 pins ride on the slice (not capture_context).
    observed_slice = manifest["source_slices"][0]
    assert observed_slice["session_visibility_pin"] == {"status": "known", "value": "logged_out_public", "reason": None}
    assert observed_slice["locale_pin"]["value"] == "en-US"
    assert observed_slice["currency_pin"]["value"] == "USD"
    assert observed_slice["variant_pin"]["status"] == "unknown_with_reason"

    # The pins did NOT leak into capture_context -- the whole point of step 2.
    assert manifest["capture_context"]["value"] == "direct HTTP source capture with stdlib urllib"


def test_http_runner_rejects_cadence_subflag_without_mode(http_server: str, scratch_dir: Path) -> None:
    # Major 1: a cadence subflag supplied without --intended-cadence-mode is an incoherent partial
    # plan. It must fail VISIBLY (non-zero exit, error names the mode requirement) rather than being
    # silently dropped. --series-id is supplied so the series-identity gate passes and the cadence
    # gate is what fires.
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/ok",
            "--decision-question",
            "Does a cadence subflag without a mode fail visibly?",
            "--output",
            str(output_dir),
            "--series-id",
            "pilot_partial_cadence_001",
            "--intended-cadence-slot-count",
            "14",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--intended-cadence-mode" in result.stderr
    assert not output_dir.exists()


def test_http_runner_rejects_durability_field_without_series_id(http_server: str, scratch_dir: Path) -> None:
    # Major 2: a demand-durability fact supplied without --series-id has no series identity to ride
    # on. It must fail VISIBLY (non-zero exit, error names the series-id requirement) before the
    # capture runs, rather than writing facts with no identity.
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/ok",
            "--decision-question",
            "Does a durability field without a series id fail visibly?",
            "--output",
            str(output_dir),
            "--locale-pin",
            "en-GB",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--series-id" in result.stderr
    assert not output_dir.exists()


def test_http_runner_leaves_durability_fields_none_for_non_durability_capture(
    http_server: str, scratch_dir: Path
) -> None:
    # Back-compat: a capture that supplies no durability flags leaves every durability field
    # unset (None) on both the packet and the slice. No manifest_version bump -- the fields are
    # additive-optional, mirroring the archive_snapshot_time precedent.
    project_root = Path(__file__).resolve().parents[2]
    output_dir = scratch_dir / "packet"

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_source_capture_http_packet.py",
            "--url",
            f"{http_server}/ok",
            "--decision-question",
            "What did the HTTP source return before cutoff?",
            "--output",
            str(output_dir),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == "source_capture_packet_manifest_v1"
    assert manifest["series_id"] is None
    assert manifest["cold_start_at"] is None
    assert manifest["pre_coverage_history_posture"] is None
    assert manifest["intended_cadence"] is None
    observed_slice = manifest["source_slices"][0]
    assert observed_slice["session_visibility_pin"] is None
    assert observed_slice["locale_pin"] is None
    assert observed_slice["currency_pin"] is None
    assert observed_slice["variant_pin"] is None
