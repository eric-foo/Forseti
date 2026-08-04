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
from typing import Literal, Protocol, Sequence
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
from source_capture.rendered_access import RenderedAccessClass, classify_rendered_access
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


@dataclass(frozen=True)
class RealChromeCDPCaptureResult:
    requested_url: str
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    screenshot_png: bytes
    http_status: int | None
    warm_hop_url: str | None
    warm_hop_blocked: bool | None
    viewport_width: int | None = None
    viewport_height: int | None = None
    warning_notes: list[str] = field(default_factory=list)


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
    ) -> RealChromeCDPCaptureResult: ...


class RealChromeCDPUnavailable(RuntimeError):
    pass


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
                    response = _navigate_target(
                        page=page,
                        url=url,
                        timeout_ms=timeout_ms,
                        persistent_tab_marker=persistent_tab_marker,
                    )
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
                    screenshot_png = _capture_viewport_screenshot(
                        page=page,
                        context=context,
                        timeout_ms=(
                            min(timeout_ms, 5_000)
                            if persistent_tab_marker is not None
                            else timeout_ms
                        ),
                        warnings=warnings,
                    )
                    final_url = page.url
                    title = page.title()
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
    engine: RealChromeCDPEngine | None = None,
) -> tuple[int, str]:
    if (output_directory is None) == (data_root is None):
        raise ValueError("exactly one of output_directory or data_root is required")
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
        "screenshot_mode": "viewport",
        "rendered_dom_byte_count": len(result.rendered_dom.encode("utf-8")),
        "visible_text_byte_count": len(result.visible_text.encode("utf-8")),
        "screenshot_byte_count": len(result.screenshot_png),
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

    staged_root = Path(_stage_dir())
    staged_root.mkdir(parents=True, exist_ok=True)
    f_dom = staged_root / "01_realchrome_rendered_dom.html"
    f_txt = staged_root / "02_realchrome_visible_text.txt"
    f_png = staged_root / "03_realchrome_viewport_screenshot.png"
    f_meta = staged_root / "04_realchrome_snapshot_metadata.json"
    f_dom.write_bytes(dom_bytes)
    f_txt.write_bytes(text_bytes)
    f_png.write_bytes(result.screenshot_png)
    f_meta.write_bytes(meta_bytes)

    access_posture_value = (
        f"real_browser_cdp access_failed with access block {access_block_reason}; block artifacts "
        f"preserved via {browser_description} over CDP; content sufficiency is not asserted"
        if blocked
        else f"real_browser_cdp preserved rendered public page artifacts via {browser_description} "
        "over CDP; genuine-browser fingerprint; content is retailer/source-owned public page state"
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
        ),
        re_capture_relationship=not_applicable("no prior source capture packet supplied"),
        limitations=packet_limitations,
        warning_notes=list(result.warning_notes),
        preserved_file_ids=["file_01", "file_02", "file_03", "file_04"],
    )

    try:
        write_result = write_local_source_capture_packet(
            output_directory=output_directory,
            data_root=data_root,
            input_files=[f_dom, f_txt, f_png, f_meta],
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
            ),
            re_capture_relationship=not_applicable("no prior source capture packet supplied"),
            source_slices=[slice_],
            warnings=list(warnings) + list(result.warning_notes),
            limitations=packet_limitations,
            receipt_summary=(
                f"Real-Chrome CDP packet for {source_family}: "
                f"{'ACCESS BLOCKED' if blocked else 'rendered public page content'} for one URL "
                f"(HTTP {result.http_status})."
            ),
            receipt_non_claims=(
                ["not source-content capture; access-block page artifacts only"] + REALCHROME_CDP_NON_CLAIMS
                if blocked
                else list(REALCHROME_CDP_NON_CLAIMS)
            ),
        )
    finally:
        for f in (f_dom, f_txt, f_png, f_meta):
            try:
                f.unlink()
            except FileNotFoundError:
                pass
        shutil.rmtree(staged_root, ignore_errors=True)

    if sufficiency.enabled and not sufficiency.passed:
        return SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, source_detail_sufficiency_failure_message(
            output_directory=write_result.output_directory, result=sufficiency
        )
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
