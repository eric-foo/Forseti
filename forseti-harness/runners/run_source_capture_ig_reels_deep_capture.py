"""CLI: ONE-render IG reel deep-capture -- audience comments + creator transcript.

Renders a public reel ONCE via the browser-snapshot adapter, then derives BOTH
the audience comments (from the rendered DOM) AND the creator transcript (by
downloading the SAME render's audio handle and transcribing it) -- avoiding the
second yt-dlp page-resolve+fetch the standalone audio path costs.

No-LLM zone (``runners/``): imports the browser adapter, the deterministic
deep-capture parser, and the agnostic transcriber -- no LLM SDK. Public data only,
anonymous. The media handle is TRANSIENT (signed/expiring): it is downloaded into
a TemporaryDirectory for immediate transcription and is never persisted.
"""
from __future__ import annotations

import argparse
import http.client
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urljoin, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.root import DataLakeRoot, DataLakeRootError
from harness_utils import utc_now_z
from source_capture.adapters.browser_snapshot import (
    BrowserSnapshotFailure,
    BrowserSnapshotFailureKind,
    BrowserSnapshotResult,
    fetch_browser_snapshot_capture,
)
from source_capture.ig_reels_deep_capture import _is_ig_media_url, run_reel_deep_capture
from source_capture.ig_reels_deep_capture_lake import (
    deep_capture_record_id,
    write_reel_deep_capture_into_lake,
)
from source_capture.transcript.audio_asr import transcribe_audio

# A realistic desktop UA: the signed fbcdn handle is served to the same anonymous
# context the render used; a bare urllib UA is more likely to be refused.
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_DOWNLOAD_TIMEOUT_SECONDS = 60
_MAX_MEDIA_BYTES = 100_000_000
_MAX_MEDIA_REDIRECTS = 3
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class _MediaRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    http_error_302 = http_error_303 = http_error_307 = http_error_308 = http_error_301


_MEDIA_OPENER = urllib.request.build_opener(_MediaRedirectHandler())


class _MediaDownloadRejectedError(ValueError):
    pass


class _MediaDownloadTooLargeError(ValueError):
    pass


# A single reel-page render fails transiently more often than IG hard-gates the reel: a
# nav timeout, a momentary empty DOM, or a soft logged-out interstitial -- and the SAME reel
# renders fine on a later attempt (observed live: a reel that came back `render_unavailable`
# on one pass `transcribed` on the next). So render with a bounded retry + linear backoff, and
# wait on `load` -- NOT `networkidle`, which almost never settles on Instagram's chatty SPA and
# just times out (every other browser caller already uses `load`). Permanent failures (missing
# browser binary, denied subprocess, deterministic size cap) are not retried.
_RENDER_ATTEMPTS = 3
_RENDER_BACKOFF_SECONDS = 2.0
_RETRYABLE_RENDER_FAILURES = frozenset(
    {
        BrowserSnapshotFailureKind.TIMEOUT,
        BrowserSnapshotFailureKind.CAPTURE_FAILED,
        BrowserSnapshotFailureKind.EMPTY_RENDERED_DOM,
        BrowserSnapshotFailureKind.EMPTY_SCREENSHOT,
    }
)


def _render(
    shortcode: str,
    *,
    attempts: int = _RENDER_ATTEMPTS,
    capture_fn: Callable[..., BrowserSnapshotResult] = fetch_browser_snapshot_capture,
    sleep_fn: Callable[[float], None] = time.sleep,
    backoff_seconds: float = _RENDER_BACKOFF_SECONDS,
) -> str | None:
    """Render a public reel page to DOM, retrying transient browser-snapshot failures.

    Returns the rendered DOM, or None once retries are exhausted (the caller collapses
    that to a `render_unavailable` posture). Only transient failures are retried; a
    permanent failure stops immediately. The last failure reason is emitted to stderr,
    since the caller would otherwise record a bare `render_unavailable` with no cause.
    """
    url = f"https://www.instagram.com/reel/{shortcode}/"
    total = max(1, attempts)
    last_failure: BrowserSnapshotFailure | None = None
    attempt = 0
    for attempt in range(1, total + 1):
        res = capture_fn(
            url=url,
            wait_until="load",
            timeout_seconds=60.0,
            viewport_width=1280,
            viewport_height=2200,
            settle_seconds=6.0,
            headless=True,
        )
        if not isinstance(res, BrowserSnapshotFailure):
            return res.rendered_dom or None
        last_failure = res
        if res.failure_kind not in _RETRYABLE_RENDER_FAILURES:
            break
        if attempt < total:
            sleep_fn(backoff_seconds * attempt)
    if last_failure is not None:
        print(
            f"  render failed for {shortcode} after {attempt} attempt(s): "
            f"{last_failure.failure_kind.value}: {last_failure.message}",
            file=sys.stderr,
        )
    return None


def _is_downloadable_ig_media_url(url: str) -> bool:
    if not _is_ig_media_url(url):
        return False
    return urlparse(url).scheme.lower() == "https"


def _open_media_url(request: urllib.request.Request, *, timeout_seconds: float):
    return _MEDIA_OPENER.open(request, timeout=timeout_seconds)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _stream_response_to_file(response, path: str, *, max_bytes: int) -> int:  # noqa: ANN001
    content_length = _parse_optional_int(response.headers.get("Content-Length"))
    if content_length is not None and content_length > max_bytes:
        raise _MediaDownloadTooLargeError(
            f"media response exceeded max-bytes cap before body read: {content_length} > {max_bytes}"
        )

    total = 0
    with open(path, "wb") as handle:
        while True:
            chunk = response.read(min(65536, max_bytes - total + 1))
            if not chunk:
                return total
            total += len(chunk)
            if total > max_bytes:
                raise _MediaDownloadTooLargeError(
                    f"media response exceeded max-bytes cap during body read: {total} > {max_bytes}"
                )
            handle.write(chunk)


def _redirect_target(current_url: str, error: urllib.error.HTTPError) -> str | None:
    location = error.headers.get("Location")
    if not location:
        return None
    return urljoin(current_url, location)


def _download_media_to_path(
    url: str,
    path: str,
    *,
    max_bytes: int = _MAX_MEDIA_BYTES,
    timeout_seconds: float = _DOWNLOAD_TIMEOUT_SECONDS,
    max_redirects: int = _MAX_MEDIA_REDIRECTS,
) -> int:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_redirects < 0:
        raise ValueError("max_redirects must be non-negative")

    current_url = url
    for _redirect_count in range(max_redirects + 1):
        if not _is_downloadable_ig_media_url(current_url):
            raise _MediaDownloadRejectedError("media URL host or scheme is not allowed")

        request = urllib.request.Request(current_url, headers={"User-Agent": _UA})
        try:
            with _open_media_url(request, timeout_seconds=timeout_seconds) as response:
                final_url = response.geturl()
                if not _is_downloadable_ig_media_url(final_url):
                    raise _MediaDownloadRejectedError("media response final URL host or scheme is not allowed")
                return _stream_response_to_file(response, path, max_bytes=max_bytes)
        except urllib.error.HTTPError as error:
            if error.code not in _REDIRECT_STATUSES:
                raise
            redirect_url = _redirect_target(current_url, error)
            if redirect_url is None or not _is_downloadable_ig_media_url(redirect_url):
                raise _MediaDownloadRejectedError("media redirect target host or scheme is not allowed") from error
            current_url = redirect_url

    raise _MediaDownloadRejectedError("media redirect limit exceeded")


def _make_downloader(scratch_dir: str, *, max_bytes: int = _MAX_MEDIA_BYTES):
    def _download(url: str) -> str | None:
        path = os.path.join(scratch_dir, "reel_audio.mp4")
        try:
            bytes_written = _download_media_to_path(url, path, max_bytes=max_bytes)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, http.client.HTTPException):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            return None
        if bytes_written <= 0:
            if os.path.exists(path):
                os.remove(path)
            return None
        return path

    return _download


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One-render IG reel deep-capture (audience comments + creator transcript)."
    )
    parser.add_argument("--shortcode", required=True, help="IG Reel shortcode (e.g. DaA8n7EhqTR).")
    parser.add_argument("--model", default="small", help="faster-whisper model size.")
    parser.add_argument(
        "--data-root",
        default=None,
        help="Forseti data lake root (or FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT)). When set, persists the silver "
        "deep-capture record-set (comments + transcript); omit for stdout-only.",
    )
    args = parser.parse_args(argv)

    try:
        data_root = _resolve_optional_data_root(args.data_root)
    except DataLakeRootError as exc:
        parser.error(f"invalid Forseti data lake root: {exc}")

    with tempfile.TemporaryDirectory(prefix="forseti_deepcap_") as scratch:
        result = run_reel_deep_capture(
            args.shortcode,
            render_fn=_render,
            download_fn=_make_downloader(scratch),
            transcribe_fn=lambda path: transcribe_audio(path, model_name=args.model),
        )
        # transcription happens inside this block, while the temp audio file still exists.

        persisted = None
        if data_root is not None:
            persisted = _persist_deep_capture(result, data_root=data_root)

    print(
        f"reel={result.reel_shortcode} "
        f"comments={len(result.comments)} "
        f"transcript_posture={result.transcript_posture} "
        f"transcript_cues={len(result.transcript_cues)} "
        f"audio_handle={'used' if result.media_url_used else 'none'}"
    )
    for note in result.notes:
        print(f"  note: {note}")

    if persisted is not None:
        print(f"  {persisted}")
    return 0


def _persist_deep_capture(result, *, data_root: DataLakeRoot) -> str:
    """Persist a new packet-backed deep-capture observation."""
    written = write_reel_deep_capture_into_lake(
        data_root=data_root,
        result=result,
        generated_at=utc_now_z(),
        record_id=deep_capture_record_id(result),
    )
    exclusions = f" excluded={','.join(written.excluded_legs)}" if written.excluded_legs else ""
    return (
        f"persisted: packet={written.packet_id} record={written.record_id} "
        f"silver_lanes={','.join(sorted(written))}{exclusions}"
    )


def _resolve_optional_data_root(data_root_arg: str | None) -> DataLakeRoot | None:
    if data_root_arg is None and not (
        os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT")
    ):
        return None
    return DataLakeRoot.resolve(explicit=data_root_arg)


if __name__ == "__main__":
    raise SystemExit(main())
