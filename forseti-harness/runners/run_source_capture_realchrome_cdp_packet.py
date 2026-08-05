"""Rung-5 capture runner: attach to an operator-provided REAL Chrome over the
Chrome DevTools Protocol and preserve one URL as a Source Capture Packet.

Why this rung exists: Akamai (and similar bot walls) fingerprint the stealth /
headless automation browsers used by the lower rungs (Direct HTTP, anti-block
HTTP, CloakBrowser) and deny them cold on any egress. A genuine Chrome executes
the wall's sensor JS legitimately and earns a valid session on first contact, so
it reaches content the automation rungs cannot. This runner does NOT launch a
browser: it attaches to a real Chrome the operator is already running with
`--remote-debugging-port` (its own dedicated profile), opens a new tab by
default, does an optional same-site warm hop (which seeds the wall's session
cookies even when the hop itself is blocked), navigates the target, and writes
the packet through the existing `write_local_source_capture_packet` seam.
Google queue runners may instead name one persistent tab: the runner reuses
that tab across jobs and leaves it visible for operator clearance if Google
renders a challenge.

Honesty boundary: this is not stealth, not proxy, not login/credential capture.
Only public page content is preserved (rendered DOM, visible text, page-only
viewport screenshot, method metadata) — no cookies, storage state, or account
data. It requires an externally-running real Chrome, so it is operator-gated, not
fully unattended.
"""
from __future__ import annotations

import argparse
import base64
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Protocol, Sequence
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from harness_utils import generate_ulid, utc_now_z
from source_capture import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
    unknown_with_reason,
    write_local_source_capture_packet,
)
from source_capture.content_extraction import (
    CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    CONTENT_RECORD_FILENAME,
    RenderedContentExtractionSpec,
)
from source_capture.rendered_access import RenderedAccessClass, classify_rendered_access
from source_capture.rendered_retention import resolve_rendered_retention
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
    SourceDetailSufficiencyRequirements,
    add_source_detail_sufficiency_arguments,
    build_source_detail_sufficiency_requirements,
    evaluate_source_detail_sufficiency,
    source_detail_sufficiency_failure_message,
    source_detail_sufficiency_limitation,
    source_detail_sufficiency_mode_change,
)

DEFAULT_CDP_ENDPOINT = "http://localhost:9222"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 800
NAVIGATION_HTTP_ERROR_EXIT_CODE = 3
DEFAULT_WINDOW_CHROME_HEIGHT_PX = 150
_PROGRESSIVE_SCROLL_PAUSE_MS = 900
_MAX_PROGRESSIVE_SCROLL_STEPS = 40
BrowserProvisioning = Literal["operator_provided", "unattended_xvfb"]

REALCHROME_CDP_NON_CLAIMS = [
    "not source-content sufficiency proof",
    "not stealth or anti-detect automation",
    "not login, session, credential, or cookie capture",
    "not stored profile, storage-state, or cookie disclosure",
    "not proxy or VPN use",
    "not armory-headless-runner reproducible",
    "not a delivery-location or shopper-origin pin",
    "not ECR design",
    "not Cleaning implementation",
    "not Judgment scoring",
    "not buyer proof",
    "not commercial-readiness logic",
]

# helper-delta: local cookie/secret guard mirrors cloakbrowser_snapshot's intent but is
# scoped to this runner's plain-text metadata/DOM; not a shared helper in harness_utils.
_SECRET_LIKE = re.compile(r"\b(Set-Cookie|cf_clearance|storage_state|user_data_dir)\b", re.IGNORECASE)

# Click every eligible in-place expansion control inside the caller's selector
# whose visible text matches the caller's pattern, and report how many were
# clicked. Anchors carrying an href are deliberately excluded: those navigate
# to another page, and following them would turn one bounded capture into a
# crawl.
_EXPAND_CONTROLS_JS = """
(payload) => {
  const re = new RegExp(payload.pattern, 'i');
  const controls = Array.from(document.querySelectorAll(payload.selector))
    .filter(el => !(el.tagName === 'A' && el.getAttribute('href')))
    .filter(el => el.isConnected && el.getClientRects().length > 0)
    .filter(el => !el.disabled && el.getAttribute('aria-disabled') !== 'true')
    .filter(el => re.test(el.textContent || ''));
  if (!payload.click) return {eligible: controls.length, clicked: 0};
  let clicked = 0;
  for (const control of controls) {
    try { control.click(); clicked += 1; } catch (err) { /* one dead control must not stop the round */ }
  }
  return {eligible: controls.length, clicked};
}
"""


@dataclass(frozen=True)
class RealChromeCDPCaptureResult:
    requested_url: str
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    # ``None`` when the caller suppressed the screenshot.  Suppression is not
    # capture-then-discard: on a tall viewport the raster is the single largest
    # artifact (9.40 MB of 12.0 MB on a measured Reddit listing) and nothing
    # reads it -- the projection reads DOM and visible text, and the access
    # classifier reads the response.
    screenshot_png: bytes | None
    http_status: int | None
    warm_hop_url: str | None
    warm_hop_blocked: bool | None
    viewport_width: int | None = None
    viewport_height: int | None = None
    warning_notes: list[str] = field(default_factory=list)
    # In-place expansion accounting. ``expansion_exhausted`` is the honest
    # distinction a later reader needs: False means the round bound stopped the
    # loop while controls remained, so the DOM is short by an unknown amount.
    expansion_rounds: int = 0
    expansion_clicks: int = 0
    expansion_exhausted: bool | None = None


class RealChromeCDPEngine(Protocol):
    def capture(
        self,
        *,
        url: str,
        cdp_endpoint: str,
        warm_hop_url: str | None,
        settle_seconds: float,
        scroll_step_px: int,
        scroll_passes: int,
        timeout_seconds: float,
        viewport_width: int,
        viewport_height: int,
        persistent_tab_marker: str | None,
        fit_viewport_to_window: bool,
        capture_screenshot: bool = True,
        ready_selector: str | None = None,
        expand_control_pattern: str | None = None,
        expand_control_selector: str = "button, a",
        expand_max_rounds: int = 0,
        expand_settle_ms: int = 6000,
    ) -> RealChromeCDPCaptureResult: ...


class RealChromeCDPUnavailable(RuntimeError):
    pass


class RealChromeNavigationHTTPError(RealChromeCDPUnavailable):
    """The target navigation reached the server and was refused with an HTTP
    error response. Subclasses RealChromeCDPUnavailable so every existing
    handler keeps its exit behavior; the distinct type exists because a
    server-side refusal (throttling burst, 5xx) must never read as local
    Chrome/CDP unavailability -- that misread hid an 11-slot refusal burst in
    the 2026-08-01 batch. ``http_status`` is the refused status when the
    response listener observed it, else None.
    """

    def __init__(self, message: str, *, http_status: int | None):
        super().__init__(message)
        self.http_status = http_status


class RealChromeWrongPageError(RealChromeCDPUnavailable):
    """The snapshot was taken on a page other than the requested target.

    A persistent tab lives in the operator's real Chrome, so a human can
    navigate it while a capture is settling or expanding; the snapshot then
    honestly preserves the wrong page while the batch row reads success. The
    2026-08-03 wave committed 21 such packets (old unrelated threads) before
    this guard existed. Subclasses RealChromeCDPUnavailable so existing
    handlers keep their exit behavior; carries no ``http_status`` so refusal
    circuit breakers ignore it (a local race, not a server refusal).
    """

    def __init__(self, message: str, *, requested_url: str, final_url: str):
        super().__init__(message)
        self.requested_url = requested_url
        self.final_url = final_url


def _is_navigation_http_error(exc: BaseException, observed_status: int | None) -> bool:
    """A navigation failure is an HTTP refusal when Chromium says so or when
    the main-frame navigation response itself carried an error status."""
    if "ERR_HTTP_RESPONSE_CODE_FAILURE" in str(exc):
        return True
    return observed_status is not None and observed_status >= 400


def _capture_viewport_screenshot(*, page, context, timeout_ms: float, warnings: list[str]) -> bytes:
    """Capture a real viewport PNG, bypassing Playwright's font wait if needed."""

    try:
        screenshot = page.screenshot(type="png", full_page=False, timeout=timeout_ms)
    except Exception as playwright_error:
        session = None
        try:
            session = context.new_cdp_session(page)
            response = session.send(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "fromSurface": True,
                    "captureBeyondViewport": False,
                },
            )
            encoded = response.get("data") if isinstance(response, dict) else None
            if not isinstance(encoded, str) or not encoded:
                raise RuntimeError("raw CDP screenshot returned no data")
            screenshot = base64.b64decode(encoded, validate=True)
            if not screenshot.startswith(b"\x89PNG\r\n\x1a\n"):
                raise RuntimeError("raw CDP screenshot was not a PNG")
        except Exception as cdp_error:
            raise RealChromeCDPUnavailable(
                "Playwright viewport screenshot failed and the raw CDP fallback "
                f"also failed: {type(playwright_error).__name__}: {playwright_error}; "
                f"{type(cdp_error).__name__}: {cdp_error}"
            ) from cdp_error
        finally:
            if session is not None:
                try:
                    session.detach()
                except Exception:
                    pass
        warnings.append(
            "playwright_viewport_screenshot_failed_raw_cdp_fallback_used: "
            f"{type(playwright_error).__name__}"
        )
    if not isinstance(screenshot, bytes) or not screenshot:
        raise RealChromeCDPUnavailable("viewport screenshot returned no bytes")
    return screenshot


def _navigate_target(
    *,
    page,
    url: str,
    timeout_ms: float,
    persistent_tab_marker: str | None,
):
    """Navigate if needed and restore the marker after a document swap."""
    if persistent_tab_marker is not None and getattr(page, "url", None) == url:
        # A matching URL can come from an earlier attempt whose navigation
        # committed but never finished loading; capture must not silently read
        # that partial document. Waiting is a no-op on an already-loaded page,
        # and a load that cannot finish surfaces as the caller's typed failure.
        page.wait_for_load_state("load", timeout=timeout_ms)
        page.evaluate(
            "(marker) => { window.name = marker; }", persistent_tab_marker
        )
        return None
    response = page.goto(url, wait_until="load", timeout=timeout_ms)
    if persistent_tab_marker is not None:
        page.evaluate(
            "(marker) => { window.name = marker; }", persistent_tab_marker
        )
    return response


class _LiveRealChromeCDPEngine:
    def capture(
        self,
        *,
        url: str,
        cdp_endpoint: str,
        warm_hop_url: str | None,
        settle_seconds: float,
        scroll_step_px: int,
        scroll_passes: int,
        timeout_seconds: float,
        viewport_width: int,
        viewport_height: int,
        persistent_tab_marker: str | None,
        fit_viewport_to_window: bool,
        capture_screenshot: bool = True,
        ready_selector: str | None = None,
        expand_control_pattern: str | None = None,
        expand_control_selector: str = "button, a",
        expand_max_rounds: int = 0,
        expand_settle_ms: int = 6000,
    ) -> RealChromeCDPCaptureResult:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:  # pragma: no cover - env dependency
            raise RealChromeCDPUnavailable(
                "playwright is required for the real-Chrome CDP runner; install it before use"
            ) from exc

        timeout_ms = timeout_seconds * 1000
        warnings: list[str] = []
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(cdp_endpoint)
            except Exception as exc:
                raise RealChromeCDPUnavailable(
                    f"could not attach to a real Chrome over CDP at {cdp_endpoint}; start Chrome with "
                    f"--remote-debugging-port and confirm the endpoint. Underlying error: {exc}"
                ) from exc
            if not browser.contexts:
                raise RealChromeCDPUnavailable(
                    "attached Chrome exposes no browser context; open a normal (non-incognito) window"
                )
            context = browser.contexts[0]
            page, close_page = _select_or_create_page(
                context=context,
                target_url=url,
                persistent_tab_marker=persistent_tab_marker,
            )
            warm_hop_blocked: bool | None = None
            try:
                actual_viewport_width = viewport_width
                actual_viewport_height = viewport_height
                if fit_viewport_to_window:
                    dimensions = page.evaluate(
                        "() => ({width: window.outerWidth, height: window.outerHeight})"
                    )
                    actual_viewport_width = max(320, int(dimensions["width"]))
                    actual_viewport_height = max(
                        600,
                        int(dimensions["height"]) - DEFAULT_WINDOW_CHROME_HEIGHT_PX,
                    )
                page.set_viewport_size(
                    {
                        "width": actual_viewport_width,
                        "height": actual_viewport_height,
                    }
                )
                if warm_hop_url:
                    try:
                        page.goto(warm_hop_url, wait_until="load", timeout=timeout_ms)
                        page.wait_for_timeout(3000)
                        hop_dom = page.content()
                        hop_txt = page.locator("body").inner_text(timeout=timeout_ms)
                        hop_access = classify_rendered_access(
                            title=page.title(), rendered_dom=hop_dom, visible_text=hop_txt
                        )
                        warm_hop_blocked = (
                            hop_access.classification == RenderedAccessClass.ACCESS_BLOCKED
                        )
                    except Exception as exc:
                        warnings.append(f"warm hop to {warm_hop_url} failed (continuing): {exc}")
                # The target capture is guarded and mapped to a typed failure: this rung
                # exists to hit bot walls, which routinely hang or reset the target
                # navigation. A raw Playwright error here must become a clean exit-3, not an
                # uncaught traceback. page.close() in the finally still runs either way.
                try:
                    navigation_statuses: list[int] = []

                    def _record_navigation_status(resp, _page=page):
                        # Failure-path listener: when goto raises (e.g.
                        # net::ERR_HTTP_RESPONSE_CODE_FAILURE) it returns no
                        # Response object, and this is the only place the
                        # refused status can still be read.
                        try:
                            if (
                                resp.request.is_navigation_request()
                                and resp.frame == _page.main_frame
                            ):
                                navigation_statuses.append(resp.status)
                        except Exception:
                            pass

                    page.on("response", _record_navigation_status)
                    try:
                        response = _navigate_target(
                            page=page,
                            url=url,
                            timeout_ms=timeout_ms,
                            persistent_tab_marker=persistent_tab_marker,
                        )
                    except Exception as exc:
                        observed = (
                            navigation_statuses[-1] if navigation_statuses else None
                        )
                        if _is_navigation_http_error(exc, observed):
                            raise RealChromeNavigationHTTPError(
                                f"target navigation for {url} was refused with an "
                                "HTTP error response "
                                f"(status={'unknown' if observed is None else observed}); "
                                "server-side refusal, not CDP unavailability. "
                                f"Underlying error: {type(exc).__name__}: {exc}",
                                http_status=observed,
                            ) from exc
                        raise
                    finally:
                        page.remove_listener("response", _record_navigation_status)
                    http_status = response.status if response is not None else None
                    settle_block_signal = None
                    remaining_settle_ms = int(settle_seconds * 1000)
                    while remaining_settle_ms > 0:
                        try:
                            settle_access = classify_rendered_access(
                                title=page.title(),
                                rendered_dom=page.content(),
                                visible_text=page.locator("body").inner_text(
                                    timeout=min(timeout_ms, 3000)
                                ),
                            )
                            if (
                                settle_access.classification
                                == RenderedAccessClass.ACCESS_BLOCKED
                            ):
                                settle_block_signal = settle_access.signal
                        except Exception as exc:
                            warnings.append(f"settle access inspection failed: {exc}")
                        pause_ms = min(1000, remaining_settle_ms)
                        page.wait_for_timeout(pause_ms)
                        remaining_settle_ms -= pause_ms
                    if settle_block_signal:
                        warnings.append(
                            "transient_access_block_observed_during_settle: "
                            f"{settle_block_signal}"
                        )
                    if ready_selector:
                        # A fixed settle is a guess about render time, and a
                        # wrong guess is indistinguishable from an empty page:
                        # 8 of 91 captures on 2026-07-31 snapshotted a rendered
                        # shell whose feed had not arrived, or rows whose
                        # attributes had not populated. Waiting on a caller-named
                        # readiness condition replaces the guess. A timeout is
                        # recorded and capture continues, so the packet still
                        # exists as evidence and the projection guard is what
                        # decides whether it may be admitted.
                        try:
                            page.wait_for_selector(
                                ready_selector, timeout=min(timeout_ms, 60000)
                            )
                        except Exception as exc:
                            warnings.append(
                                f"ready_selector {ready_selector!r} did not appear "
                                f"before snapshot: {type(exc).__name__}"
                            )
                    expansion_rounds = 0
                    expansion_clicks = 0
                    expansion_exhausted: bool | None = None
                    if expand_control_pattern and expand_max_rounds > 0:
                        # Some surfaces paint only a fraction of their content
                        # and hide the rest behind in-place expansion controls
                        # (a measured Reddit thread served 35 of 198 comments on
                        # first paint). Click every matching control, settle, and
                        # repeat until none remain. Only IN-PLACE controls are
                        # clicked: this never follows a link to another page, so
                        # it stays one bounded capture rather than a crawl.
                        expansion_exhausted = False
                        for _ in range(expand_max_rounds):
                            try:
                                outcome = page.evaluate(
                                    _EXPAND_CONTROLS_JS,
                                    {
                                        "pattern": expand_control_pattern,
                                        "selector": expand_control_selector,
                                        "click": True,
                                    },
                                )
                            except Exception as exc:
                                warnings.append(
                                    f"expansion round failed (continuing): {type(exc).__name__}: {exc}"
                                )
                                expansion_exhausted = None
                                break
                            eligible = int(outcome.get("eligible", 0))
                            clicked = int(outcome.get("clicked", 0))
                            if not eligible:
                                expansion_exhausted = True
                                break
                            if not clicked:
                                warnings.append(
                                    f"expansion round found {eligible} eligible control(s) "
                                    "but clicked none; exhaustion is unknown"
                                )
                                expansion_exhausted = None
                                break
                            expansion_rounds += 1
                            expansion_clicks += clicked
                            if clicked < eligible:
                                warnings.append(
                                    f"expansion round clicked {clicked} of {eligible} eligible control(s)"
                                )
                            page.wait_for_timeout(expand_settle_ms)
                        else:
                            # Probe after the final settle without another click.
                            # The old loop always reported False when the final
                            # allowed click actually removed the last control.
                            try:
                                remaining = page.evaluate(
                                    _EXPAND_CONTROLS_JS,
                                    {
                                        "pattern": expand_control_pattern,
                                        "selector": expand_control_selector,
                                        "click": False,
                                    },
                                )
                                remaining_count = int(remaining.get("eligible", 0))
                                expansion_exhausted = remaining_count == 0
                                if remaining_count:
                                    warnings.append(
                                        f"expansion stopped at the {expand_max_rounds}-round bound "
                                        f"with {remaining_count} eligible control(s) still present; "
                                        "captured DOM is short by an unknown amount"
                                    )
                            except Exception as exc:
                                expansion_exhausted = None
                                warnings.append(
                                    "expansion exhaustion probe failed: "
                                    f"{type(exc).__name__}: {exc}"
                                )
                    if scroll_step_px > 0:
                        position = 0
                        for _ in range(_MAX_PROGRESSIVE_SCROLL_STEPS):
                            height = page.evaluate("() => document.body.scrollHeight")
                            if position >= height:
                                break
                            position += scroll_step_px
                            page.evaluate("(y) => window.scrollTo(0, y)", position)
                            page.wait_for_timeout(_PROGRESSIVE_SCROLL_PAUSE_MS)
                    for _ in range(scroll_passes):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(_PROGRESSIVE_SCROLL_PAUSE_MS)
                        page.evaluate("window.scrollTo(0, 0)")
                    rendered_dom = page.content()
                    try:
                        visible_text = page.locator("body").inner_text(timeout=timeout_ms)
                    except Exception as exc:
                        visible_text = ""
                        warnings.append(f"visible_text extraction failed: {exc}")
                    screenshot_png = (
                        _capture_viewport_screenshot(
                            page=page,
                            context=context,
                            timeout_ms=(
                                min(timeout_ms, 5_000)
                                if persistent_tab_marker is not None
                                else timeout_ms
                            ),
                            warnings=warnings,
                        )
                        if capture_screenshot
                        else None
                    )
                    final_url = page.url
                    title = page.title()
                except RealChromeCDPUnavailable:
                    # Already typed (e.g. RealChromeNavigationHTTPError); the
                    # blanket wrap below must not relabel it as generic
                    # CDP failure.
                    raise
                except Exception as exc:
                    raise RealChromeCDPUnavailable(
                        f"real Chrome target capture failed for {url}: {type(exc).__name__}: {exc}"
                    ) from exc
            finally:
                if close_page:
                    page.close()  # close only the tab created for this one-shot capture
        return RealChromeCDPCaptureResult(
            requested_url=url,
            final_url=final_url,
            title=title,
            rendered_dom=rendered_dom,
            visible_text=visible_text,
            screenshot_png=screenshot_png,
            http_status=http_status,
            warm_hop_url=warm_hop_url,
            warm_hop_blocked=warm_hop_blocked,
            viewport_width=actual_viewport_width,
            viewport_height=actual_viewport_height,
            warning_notes=warnings,
            expansion_rounds=expansion_rounds,
            expansion_clicks=expansion_clicks,
            expansion_exhausted=expansion_exhausted,
        )


def _select_or_create_page(*, context, target_url: str, persistent_tab_marker: str | None):
    """Return (page, close_after_capture) without touching unrelated tabs."""
    if persistent_tab_marker is None:
        return context.new_page(), True

    for page in context.pages:
        if page.is_closed():
            continue
        try:
            if page.evaluate("() => window.name") == persistent_tab_marker:
                return page, False
        except Exception:
            continue

    target_host = (urlparse(target_url).hostname or "").casefold()
    if target_host in {"google.com", "www.google.com"}:
        google_pages = [
            page
            for page in context.pages
            if not page.is_closed()
            and page.url.startswith(
                ("https://www.google.com/search", "https://google.com/search")
            )
        ]
        if len(google_pages) == 1:
            page = google_pages[0]
            page.evaluate(
                "(marker) => { window.name = marker; }", persistent_tab_marker
            )
            return page, False

    page = context.new_page()
    page.evaluate("(marker) => { window.name = marker; }", persistent_tab_marker)
    return page, False


def run_source_capture_realchrome_cdp_packet(
    *,
    url: str,
    source_family: str,
    source_surface: str,
    decision_question: str,
    output_directory: Path | None = None,
    data_root: object | None = None,
    capture_context: str | None = None,
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
    warm_hop_url: str | None = None,
    settle_seconds: float = 8.0,
    scroll_step_px: int = 0,
    scroll_passes: int = 0,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
    viewport_height: int = DEFAULT_VIEWPORT_HEIGHT,
    warnings: Sequence[str] = (),
    limitations: Sequence[str] = (),
    visible_mode_changes: Sequence[str] = (),
    source_detail_sufficiency_requirements: SourceDetailSufficiencyRequirements | None = None,
    session_id: str | None = None,
    browser_provisioning: BrowserProvisioning = "operator_provided",
    persistent_profile_loaded: bool = False,
    persistent_tab_marker: str | None = None,
    fit_viewport_to_window: bool = False,
    # Both default to today's behavior, so no existing caller changes shape.
    # Content mode is deliberately reachable only programmatically -- the
    # extractor is a Python callable, so there is no CLI flag for it and the
    # command surface other lanes use is untouched.
    content_extraction: RenderedContentExtractionSpec | None = None,
    capture_screenshot: bool = True,
    keep_raw_audit_sample: bool = False,
    # A CSS selector the page must satisfy before the snapshot is taken, so a
    # caller can name what "rendered" means for its own surface instead of
    # trusting a fixed settle to have been long enough.
    ready_selector: str | None = None,
    # A JS-regex source matched against the visible text of in-place expansion
    # controls (buttons and href-less anchors). Left None, nothing is clicked.
    expand_control_pattern: str | None = None,
    expand_control_selector: str = "button, a",
    expand_max_rounds: int = 0,
    expand_settle_ms: int = 6000,
    # A Python regex the FINAL url must match for the snapshot to count as the
    # requested target. Left None, nothing is checked (some lanes legitimately
    # follow redirects whose shape the caller cannot predict). A mismatch is a
    # typed RealChromeWrongPageError raised before any packet is written --
    # never a committed packet whose manifest quietly names a different page.
    target_identity_pattern: str | None = None,
    # Predicate form for callers whose identity rule is structural rather than
    # regex-shaped (for example exact host/path/query equality for a listing).
    # It composes with target_identity_pattern when both are supplied.
    target_identity_check: Callable[[str], bool] | None = None,
    target_identity_description: str | None = None,
    engine: RealChromeCDPEngine | None = None,
) -> tuple[int, str]:
    if (output_directory is None) == (data_root is None):
        raise ValueError("exactly one of output_directory or data_root is required")
    compiled_target_identity = (
        re.compile(target_identity_pattern) if target_identity_pattern is not None else None
    )
    if browser_provisioning not in {"operator_provided", "unattended_xvfb"}:
        raise ValueError("browser_provisioning must be operator_provided or unattended_xvfb")
    if persistent_tab_marker is not None:
        if browser_provisioning != "operator_provided":
            raise ValueError("persistent tabs require operator_provided browser provisioning")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", persistent_tab_marker):
            raise ValueError(
                "persistent_tab_marker must be 1-120 safe identifier characters"
            )

    unattended = browser_provisioning == "unattended_xvfb"
    browser_description = (
        "an unattended headful Google Chrome running under Xvfb"
        if unattended
        else "an operator-provided real Chrome"
    )

    capture_engine = engine or _LiveRealChromeCDPEngine()
    result = capture_engine.capture(
        url=url,
        cdp_endpoint=cdp_endpoint,
        warm_hop_url=warm_hop_url,
        settle_seconds=settle_seconds,
        scroll_step_px=scroll_step_px,
        scroll_passes=scroll_passes,
        timeout_seconds=timeout_seconds,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        persistent_tab_marker=persistent_tab_marker,
        fit_viewport_to_window=fit_viewport_to_window,
        capture_screenshot=capture_screenshot,
        ready_selector=ready_selector,
        expand_control_pattern=expand_control_pattern,
        expand_control_selector=expand_control_selector,
        expand_max_rounds=expand_max_rounds,
        expand_settle_ms=expand_settle_ms,
    )

    final_url = result.final_url or ""
    pattern_matches = (
        compiled_target_identity is None
        or compiled_target_identity.search(final_url) is not None
    )
    predicate_matches = target_identity_check is None or bool(
        target_identity_check(final_url)
    )
    if not pattern_matches or not predicate_matches:
        identity_description = (
            target_identity_description
            or (
                f"target identity pattern {target_identity_pattern!r}"
                if target_identity_pattern is not None
                else "caller-supplied target identity check"
            )
        )
        raise RealChromeWrongPageError(
            f"snapshot landed on {result.final_url!r}, which does not satisfy the "
            f"{identity_description} for requested "
            f"{url!r}; the persistent capture tab was likely navigated away "
            "mid-capture. No packet was written; recapture in a fresh bounded "
            "batch.",
            requested_url=url,
            final_url=result.final_url or "",
        )

    access = classify_rendered_access(
        title=result.title, rendered_dom=result.rendered_dom, visible_text=result.visible_text
    )
    blocked = access.classification == RenderedAccessClass.ACCESS_BLOCKED
    access_block_reason = access.signal if blocked else None

    metadata = {
        "requested_url": result.requested_url,
        "final_url": result.final_url,
        "title": result.title,
        "capture_timestamp": utc_now_z(),
        "method_category": "real_browser_cdp",
        "browser_engine": "chrome_real_via_cdp",
        "browser_provisioning": browser_provisioning,
        "cdp_endpoint": cdp_endpoint,
        "http_response_status": result.http_status,
        "warm_hop_url": result.warm_hop_url,
        "warm_hop_blocked": result.warm_hop_blocked,
        "proxy_used": False,
        "persistent_profile_loaded": persistent_profile_loaded,
        "storage_state_loaded": False,
        "credential_injected": False,
        "logged_in": False,
        "access_blocked": blocked,
        "access_block_reason": access_block_reason,
        "rendered_access_classification": access.classification.value,
        "rendered_access_signal": access.signal,
        "viewport_width": result.viewport_width or viewport_width,
        "viewport_height": result.viewport_height or viewport_height,
        "persistent_tab": persistent_tab_marker is not None,
        "persistent_tab_marker": persistent_tab_marker,
        "fit_viewport_to_window": fit_viewport_to_window,
        "ready_selector": ready_selector,
        "expand_control_pattern": expand_control_pattern,
        "expand_control_selector": expand_control_selector,
        "expand_max_rounds": expand_max_rounds,
        "expansion_rounds": result.expansion_rounds,
        "expansion_clicks": result.expansion_clicks,
        # None when no expansion was requested; False is the load-bearing value
        # -- it means the round bound stopped the loop with controls remaining.
        "expansion_controls_exhausted": result.expansion_exhausted,
        # "not_captured" rather than "viewport"/0: a packet that reports a
        # viewport screenshot of zero bytes claims a capture posture it does not
        # have, and a later reader cannot tell suppression from a failed raster.
        "screenshot_mode": "viewport" if result.screenshot_png is not None else "not_captured",
        "rendered_dom_byte_count": len(result.rendered_dom.encode("utf-8")),
        "visible_text_byte_count": len(result.visible_text.encode("utf-8")),
        "screenshot_byte_count": (
            len(result.screenshot_png) if result.screenshot_png is not None else None
        ),
    }

    dom_bytes = result.rendered_dom.encode("utf-8")
    text_bytes = result.visible_text.encode("utf-8")
    meta_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _assert_no_secret_bytes(
        [("rendered_dom", dom_bytes), ("visible_text", text_bytes), ("browser_metadata", meta_bytes)]
    )

    packet_limitations = list(limitations) + list(result.warning_notes)
    packet_limitations.append(
        f"real_browser_cdp: captured by attaching to {browser_description} over CDP "
        f"({cdp_endpoint}); genuine-browser fingerprint, not a stealth/headless automation browser. "
        "The browser lifecycle is external to this packet writer and the route is NOT reproducible "
        "by the headless armory runners. Only public page content was preserved (no cookies, storage "
        "state, or account data)."
    )
    if blocked:
        packet_limitations.append(
            "access_failed: the real Chrome rendered an access-block/interstitial page instead of "
            f"source content: {access_block_reason}; block artifacts preserved"
        )
    http_admission_failed = result.http_status is not None and (
        type(result.http_status) is not int or not 200 <= result.http_status < 300
    )
    if http_admission_failed:
        packet_limitations.append(
            "access_failed: the real Chrome navigation did not return a successful "
            f"HTTP status ({result.http_status!r}); raw artifacts preserved"
        )

    sufficiency = evaluate_source_detail_sufficiency(
        requirements=source_detail_sufficiency_requirements,
        access_block_reason=access_block_reason,
        visible_text=result.visible_text,
        rendered_dom=result.rendered_dom,
    )
    sufficiency_lim = source_detail_sufficiency_limitation(sufficiency)
    if sufficiency_lim is not None:
        packet_limitations.append(sufficiency_lim)

    packet_mode_changes = list(visible_mode_changes)
    packet_mode_changes.append("real_browser_cdp_snapshot")
    if persistent_tab_marker is not None:
        packet_mode_changes.append("persistent_operator_visible_tab")
    if fit_viewport_to_window:
        packet_mode_changes.append("window_fitted_viewport")
    if unattended:
        packet_mode_changes.append("unattended_xvfb_realchrome_cdp")
    sufficiency_mode = source_detail_sufficiency_mode_change(sufficiency)
    if sufficiency_mode is not None:
        packet_mode_changes.append(sufficiency_mode)

    # Retention is decided BEFORE staging, because the decision determines which
    # artifacts exist in the packet at all.  ``admission_failed`` folds every
    # reason this capture must not be admitted as clean source content, so a
    # clean projection of a block shell is withheld rather than published.
    retention = resolve_rendered_retention(
        spec=content_extraction,
        rendered_dom=dom_bytes,
        visible_text=text_bytes,
        final_url=result.final_url,
        admission_failed=(
            blocked
            or http_admission_failed
            or (sufficiency.enabled and not sufficiency.passed)
        ),
        keep_raw_audit_sample=keep_raw_audit_sample,
    )
    if retention.extraction_failure_or_none is not None:
        packet_limitations.append(
            f"content extraction failed in flight; raw response preserved as fallback: "
            f"{retention.extraction_failure_or_none}"
        )
    if content_extraction is not None:
        packet_limitations.append(
            "retention_outcome="
            f"{retention.retention_outcome}; provenance={json.dumps(retention.provenance, sort_keys=True)}"
        )
        packet_mode_changes.append(f"rendered_retention_{retention.retention_outcome}")

    staged_root = Path(_stage_dir())
    staged_root.mkdir(parents=True, exist_ok=True)
    f_meta = staged_root / "04_realchrome_snapshot_metadata.json"
    f_meta.write_bytes(meta_bytes)
    staged_files = []
    f_dom = f_txt = f_png = None
    if retention.raw_inputs_preserved:
        f_dom = staged_root / "01_realchrome_rendered_dom.html"
        f_txt = staged_root / "02_realchrome_visible_text.txt"
        f_dom.write_bytes(dom_bytes)
        f_txt.write_bytes(text_bytes)
        staged_files += [f_dom, f_txt]
        if result.screenshot_png is not None:
            f_png = staged_root / "03_realchrome_viewport_screenshot.png"
            f_png.write_bytes(result.screenshot_png)
            staged_files.append(f_png)
    if retention.content_record_bytes is not None:
        f_content = staged_root / CONTENT_RECORD_FILENAME
        f_content.write_bytes(retention.content_record_bytes)
        staged_files.append(f_content)
    staged_files.append(f_meta)

    access_posture_value = (
        f"real_browser_cdp access_failed with access block {access_block_reason}; block artifacts "
        f"preserved via {browser_description} over CDP; content sufficiency is not asserted"
        if blocked
        else (
            f"real_browser_cdp access_failed with HTTP {result.http_status!r}; raw artifacts "
            f"preserved via {browser_description} over CDP; content sufficiency is not asserted"
            if http_admission_failed
            else f"real_browser_cdp preserved rendered public page artifacts via {browser_description} "
            "over CDP; genuine-browser fingerprint; content is retailer/source-owned public page state"
        )
    )

    timing = PacketTiming(
        source_publication_or_event=unknown_with_reason("real_browser_cdp did not infer source publication timing"),
        source_edit_or_version=unknown_with_reason("real_browser_cdp did not infer source edit/version timing"),
        capture_time=known_fact(metadata["capture_timestamp"]),
        recapture_time=not_applicable("no prior packet modeled"),
        cutoff_posture=unknown_with_reason("no cutoff posture metadata"),
    )
    slice_ = SourceCaptureSlice(
        slice_id="real_browser_cdp_01",
        locator=known_fact(result.final_url),
        timing=timing,
        access_posture=known_fact(access_posture_value),
        archive_history_posture=not_attempted("real_browser_cdp does not query archive or history services"),
        media_modality_posture=known_fact(
            "preserved a viewport screenshot; linked media files were not independently preserved"
            if result.screenshot_png is not None
            else "no screenshot captured; linked media files were not independently preserved"
        ),
        re_capture_relationship=not_applicable("no prior source capture packet supplied"),
        limitations=packet_limitations,
        warning_notes=list(result.warning_notes),
        # Derived from what was actually staged: the retention decision changes
        # how many artifacts exist, and a fixed four-id list would reference
        # files the packet no longer carries.
        preserved_file_ids=[f"file_{index:02d}" for index in range(1, len(staged_files) + 1)],
    )

    try:
        write_result = write_local_source_capture_packet(
            output_directory=output_directory,
            data_root=data_root,
            input_files=staged_files,
            source_family=source_family,
            source_surface=source_surface,
            source_locator=known_fact(url),
            decision_question=decision_question,
            capture_context=capture_context
            or (
                f"Attached to {browser_description} over CDP "
                f"({cdp_endpoint}); logged out; no proxy, cookie injection, credential, or login. "
                "The packet writer did not launch the browser; not headless-armory-reproducible."
            ),
            actor_audience_context=unknown_with_reason("actor/audience context not supplied"),
            capture_mode=CaptureModeCategory.MULTIMODAL,
            operator_category=(
                "unattended_real_browser_cdp"
                if unattended
                else "real_browser_cdp_operator"
            ),
            session_identity=session_id,
            visible_mode_changes=packet_mode_changes,
            access_posture=known_fact(access_posture_value),
            archive_history_posture=not_attempted("real_browser_cdp does not query archive or history services"),
            media_modality_posture=known_fact(
                "preserved a viewport screenshot; linked media files were not independently preserved"
                if result.screenshot_png is not None
                else "no screenshot captured; linked media files were not independently preserved"
            ),
            re_capture_relationship=not_applicable("no prior source capture packet supplied"),
            source_slices=[slice_],
            warnings=list(warnings) + list(result.warning_notes),
            limitations=packet_limitations,
            receipt_summary=(
                f"Real-Chrome CDP packet for {source_family}: "
                f"{'ACCESS BLOCKED' if blocked else 'HTTP RESPONSE NOT SUCCESSFUL' if http_admission_failed else 'rendered public page content'} for one URL "
                f"(HTTP {result.http_status})."
            ),
            receipt_non_claims=(
                ["not admitted source-content capture; access-failure artifacts only"]
                + REALCHROME_CDP_NON_CLAIMS
                if blocked or http_admission_failed
                else list(REALCHROME_CDP_NON_CLAIMS)
            ),
        )
    finally:
        for f in staged_files:
            try:
                f.unlink()
            except FileNotFoundError:
                pass
        shutil.rmtree(staged_root, ignore_errors=True)

    if sufficiency.enabled and not sufficiency.passed:
        return SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, source_detail_sufficiency_failure_message(
            output_directory=write_result.output_directory, result=sufficiency
        )
    # With no extractor configured, retention_outcome is raw rather than
    # raw_failure.  The HTTP admission result must still drive the exit status:
    # preserving a 4xx/5xx packet as evidence is not a successful capture.
    if content_extraction is None and http_admission_failed:
        return NAVIGATION_HTTP_ERROR_EXIT_CODE, write_result.output_directory
    if content_extraction is not None and retention.retention_outcome == "raw_failure":
        return CONTENT_EXTRACTION_FAILED_EXIT_CODE, write_result.output_directory
    return 0, write_result.output_directory


def _stage_dir() -> str:
    import tempfile

    return str(Path(tempfile.gettempdir()) / f"realchrome_cdp_stage_{generate_ulid()}")


def _assert_no_secret_bytes(inputs) -> None:
    for role, body in inputs:
        if _SECRET_LIKE.search(body.decode("utf-8", errors="ignore")):
            raise ValueError(f"secret-like material is forbidden in preserved input {role}")


def _validate_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("real-Chrome CDP capture requires an absolute http:// or https:// URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("real-Chrome CDP capture does not accept URLs with embedded credentials")
    return url


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Attach to an operator-provided real Chrome over CDP and write a Source Capture Packet."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-family", default="web_page")
    parser.add_argument("--source-surface", default="realchrome_cdp_snapshot")
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        default=None,
        help="Commit into the Forseti data lake at this root; mutually exclusive with --output. "
        "FORSETI_DATA_ROOT is used only when --output is omitted.",
    )
    parser.add_argument("--capture-context", default=None)
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument(
        "--warm-hop-url",
        default=None,
        help="Optional same-site URL to navigate first (seeds the wall's session cookies even if the "
        "hop itself is blocked), e.g. the retailer homepage before a deep-linked PDP.",
    )
    parser.add_argument("--settle-seconds", type=float, default=8.0)
    parser.add_argument("--scroll-step-px", type=int, default=0)
    parser.add_argument("--scroll-passes", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--viewport-width", type=int, default=DEFAULT_VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=DEFAULT_VIEWPORT_HEIGHT)
    parser.add_argument(
        "--persistent-tab-marker",
        default=None,
        help=(
            "Reuse one marker-owned tab across captures and leave it open. "
            "Intended for an operator-visible Google queue fallback."
        ),
    )
    parser.add_argument(
        "--fit-viewport-to-window",
        action="store_true",
        help="Fit the emulated page viewport to the visible Chrome window.",
    )
    parser.add_argument(
        "--no-screenshot",
        action="store_true",
        help=(
            "Skip the viewport screenshot entirely -- not captured rather than "
            "captured and discarded, so the raster cost is not paid at all."
        ),
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--visible-mode-change", action="append", default=[])
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate CLI inputs locally, then exit without attaching or capturing.",
    )
    add_source_detail_sufficiency_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        _validate_http_url(args.url)
        if args.warm_hop_url is not None:
            _validate_http_url(args.warm_hop_url)
        requirements = build_source_detail_sufficiency_requirements(args)
        import os

        data_root_requested = args.data_root is not None or (
            args.output is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))
        )
        if args.output is not None and args.data_root is not None:
            parser.exit(status=2, message="exactly one of --output or --data-root is required\n")
        if args.output is None and not data_root_requested:
            parser.exit(status=2, message="exactly one of --output or --data-root/FORSETI_DATA_ROOT is required\n")
        if args.preflight_only:
            print("real-Chrome CDP preflight passed; no attach or capture attempted")
            return 0
        data_root = None
        if data_root_requested:
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=args.data_root)
        exit_code, message = run_source_capture_realchrome_cdp_packet(
            url=args.url,
            source_family=args.source_family,
            source_surface=args.source_surface,
            decision_question=args.decision_question,
            output_directory=args.output if data_root is None else None,
            data_root=data_root,
            capture_context=args.capture_context,
            cdp_endpoint=args.cdp_endpoint,
            warm_hop_url=args.warm_hop_url,
            settle_seconds=args.settle_seconds,
            scroll_step_px=args.scroll_step_px,
            scroll_passes=args.scroll_passes,
            timeout_seconds=args.timeout_seconds,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            persistent_tab_marker=args.persistent_tab_marker,
            fit_viewport_to_window=args.fit_viewport_to_window,
            capture_screenshot=not args.no_screenshot,
            warnings=args.warning,
            limitations=args.limitation,
            visible_mode_changes=args.visible_mode_change,
            source_detail_sufficiency_requirements=requirements,
            session_id=args.session_id,
        )
    except RealChromeCDPUnavailable as exc:
        parser.exit(status=3, message=f"real-Chrome CDP capture unavailable: {exc}\n")
    except ValueError as exc:
        parser.exit(status=2, message=f"real-Chrome CDP capture failed: {exc}\n")
    if exit_code == 0:
        print(message)
        return 0
    parser.exit(status=exit_code, message=f"real-Chrome CDP capture failed: {message}\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
