from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from http.client import HTTPResponse
from typing import TypeAlias
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from harness_utils import utc_now_z


DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_BYTES = 5_000_000
DEFAULT_USER_AGENT = "ForsetiSourceCaptureDirectHTTP/0.1 (stdlib honest fetch; no browser/api/archive)"
_NO_PROXY_OPENER = build_opener(ProxyHandler({}))


class DirectHttpCaptureFailureKind(StrEnum):
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    NO_BODY = "no_body"
    SIZE_CAP_EXCEEDED = "size_cap_exceeded"


@dataclass(frozen=True)
class DirectHttpCaptureSuccess:
    requested_url: str
    final_url: str
    status: int
    reason: str
    metadata: dict[str, object]
    body: bytes
    warning_notes: list[str]
    limitation_notes: list[str]


@dataclass(frozen=True)
class DirectHttpCaptureFailure:
    requested_url: str
    failure_kind: DirectHttpCaptureFailureKind
    message: str
    final_url: str | None = None
    status: int | None = None
    reason: str | None = None


DirectHttpCaptureResult: TypeAlias = DirectHttpCaptureSuccess | DirectHttpCaptureFailure


def fetch_direct_http_capture(
    *,
    url: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> DirectHttpCaptureResult:
    normalized_url = _validate_http_url(url)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")

    request = Request(
        normalized_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "*/*",
        },
        method="GET",
    )

    try:
        with _open_direct_http(request, timeout_seconds=timeout_seconds) as response:
            return _capture_response(
                requested_url=normalized_url,
                response=response,
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
            )
    except HTTPError as exc:
        return _capture_response(
            requested_url=normalized_url,
            response=exc,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
        )
    except URLError as exc:
        return DirectHttpCaptureFailure(
            requested_url=normalized_url,
            failure_kind=_failure_kind_from_url_error(exc),
            message=f"Direct HTTP request failed: {exc.reason}",
        )
    except TimeoutError as exc:
        # A read-phase timeout (socket.timeout, aliased to TimeoutError on 3.10+) fires during
        # response.read() AFTER urlopen returned, so it is NOT a URLError and was previously
        # uncaught -- it propagated and crashed the caller (observed live: a slow archive aborting
        # a whole capture) instead of surfacing as an honest timeout the caller can record, retry,
        # or escalate past.
        return DirectHttpCaptureFailure(
            requested_url=normalized_url,
            failure_kind=DirectHttpCaptureFailureKind.TIMEOUT,
            message=f"Direct HTTP request timed out during response read: {exc}",
        )
    except OSError as exc:
        # Other read-phase socket errors (connection reset, etc.) likewise fire after urlopen and
        # are not URLError (which is handled above and is itself an OSError subclass); record an
        # honest network failure rather than crashing the caller.
        return DirectHttpCaptureFailure(
            requested_url=normalized_url,
            failure_kind=DirectHttpCaptureFailureKind.NETWORK_ERROR,
            message=f"Direct HTTP response read failed: {exc}",
        )


def _capture_response(
    *,
    requested_url: str,
    response: HTTPResponse | HTTPError,
    timeout_seconds: float,
    max_bytes: int,
) -> DirectHttpCaptureResult:
    status = int(response.getcode())
    reason = str(getattr(response, "reason", "") or "")
    final_url = response.geturl()
    headers = response.headers

    content_length = _parse_optional_int(headers.get("Content-Length"))
    if content_length is not None and content_length > max_bytes:
        return DirectHttpCaptureFailure(
            requested_url=requested_url,
            final_url=final_url,
            status=status,
            reason=reason,
            failure_kind=DirectHttpCaptureFailureKind.SIZE_CAP_EXCEEDED,
            message=(
                f"Direct HTTP response exceeded max-bytes cap before body read: "
                f"{content_length} bytes > {max_bytes} bytes"
            ),
        )

    try:
        body = _read_with_cap(response, max_bytes=max_bytes)
    except _BodyTooLargeError as exc:
        return DirectHttpCaptureFailure(
            requested_url=requested_url,
            final_url=final_url,
            status=status,
            reason=reason,
            failure_kind=DirectHttpCaptureFailureKind.SIZE_CAP_EXCEEDED,
            message=str(exc),
        )

    if not body:
        return DirectHttpCaptureFailure(
            requested_url=requested_url,
            final_url=final_url,
            status=status,
            reason=reason,
            failure_kind=DirectHttpCaptureFailureKind.NO_BODY,
            message=f"Direct HTTP response returned HTTP {status} {reason or 'without reason'} with an empty body",
        )

    warning_notes: list[str] = []
    if final_url != requested_url:
        warning_notes.append(f"direct_http followed redirect from {requested_url} to {final_url}")

    limitation_notes: list[str] = []
    if status < 200 or status >= 300:
        limitation_notes.append(
            f"access_failed: direct HTTP returned HTTP {status} {reason or 'without reason'}; response body preserved"
        )

    metadata = {
        "requested_url": requested_url,
        "final_url": final_url,
        "status": status,
        "reason": reason or None,
        "content_type": headers.get("Content-Type"),
        "content_length": content_length,
        "date": headers.get("Date"),
        "last_modified": headers.get("Last-Modified"),
        "etag": headers.get("ETag"),
        "retry_after": _safe_response_header(headers.get("Retry-After")),
        "capture_timestamp": utc_now_z(),
        "timeout_seconds": timeout_seconds,
        "byte_count": len(body),
    }

    return DirectHttpCaptureSuccess(
        requested_url=requested_url,
        final_url=final_url,
        status=status,
        reason=reason,
        metadata=metadata,
        body=body,
        warning_notes=warning_notes,
        limitation_notes=limitation_notes,
    )


def _open_direct_http(request: Request, *, timeout_seconds: float):
    """Open without ambient proxy env so direct_http provenance stays true."""
    return _NO_PROXY_OPENER.open(request, timeout=timeout_seconds)


def _validate_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Direct HTTP capture requires an absolute http:// or https:// URL")
    return parsed.geturl()


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _safe_response_header(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > 256 or any(character in normalized for character in "\r\n"):
        return None
    return normalized


def _read_with_cap(response: HTTPResponse | HTTPError, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(65536, max_bytes - total + 1))
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > max_bytes:
            raise _BodyTooLargeError(
                f"Direct HTTP response exceeded max-bytes cap during body read: {total} bytes > {max_bytes} bytes"
            )
        chunks.append(chunk)


def _failure_kind_from_url_error(error: URLError) -> DirectHttpCaptureFailureKind:
    reason_text = str(error.reason).lower()
    if "timed out" in reason_text or "timeout" in reason_text:
        return DirectHttpCaptureFailureKind.TIMEOUT
    return DirectHttpCaptureFailureKind.NETWORK_ERROR


class _BodyTooLargeError(ValueError):
    pass
