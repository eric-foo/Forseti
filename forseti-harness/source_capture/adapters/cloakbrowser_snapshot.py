from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from time import monotonic_ns
from typing import Callable, Protocol, TypeAlias
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from harness_utils import utc_now_z
from source_capture.proxy_profiles import ProxyProfile
from source_capture.rendered_access import RenderedAccessClass, classify_rendered_access


DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 720
DEFAULT_MAX_ARTIFACT_BYTES = 5_000_000
ALLOWED_WAIT_UNTIL = {"commit", "domcontentloaded", "load", "networkidle"}
# Pause after each scroll-to-bottom pass so lazy-loaded ("load more" / infinite
# scroll) content has time to fetch and render before the next pass or capture.
_SCROLL_PASS_SETTLE_MS = 2000
# Max time to wait for an operator-supplied "load more" control to become
# clickable before giving up that pass (treated as end-of-list, not an error).
_LOAD_MORE_CLICK_TIMEOUT_MS = 5000
# Pause after each progressive scroll step so an IntersectionObserver-gated
# section (e.g. a lazy-rendered reviews widget) can enter the viewport, fetch,
# and render before the next step or the capture.
_PROGRESSIVE_SCROLL_PAUSE_MS = 1500
# Safety cap on progressive scroll steps so an infinite-scroll page (whose
# scrollHeight keeps growing) cannot loop unbounded.
_MAX_PROGRESSIVE_SCROLL_STEPS = 40
_SCROLL_TARGET_CONDITION_TIMEOUT_MS = 5000
_SCROLL_TARGET_POLL_MS = 100
CLOAKBROWSER_METHOD_CATEGORY = "anti_blocking_browser"
CLOAKBROWSER_BACKEND = "playwright"
CAPTURE_PHASE_TIMING_SCHEMA_VERSION = 3
HEAVY_RESOURCE_TYPES = frozenset({"font", "image", "media"})
SECRET_LIKE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "auth",
    "authorization",
    "bearer",
    "client_secret",
    "code",
    "cookie",
    "key",
    "password",
    "refresh_token",
    "session",
    "sid",
    "token",
}
SECRET_LIKE_WARNING_TERMS = SECRET_LIKE_QUERY_KEYS | {
    "set-cookie",
    "storage_state",
    "user_data_dir",
}


class CloakBrowserSnapshotFailureKind(StrEnum):
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TIMEOUT = "timeout"
    CAPTURE_FAILED = "capture_failed"
    ACCESS_BLOCKED = "access_blocked"
    EMPTY_RENDERED_DOM = "empty_rendered_dom"
    EMPTY_SCREENSHOT = "empty_screenshot"
    SIZE_CAP_EXCEEDED = "size_cap_exceeded"


@dataclass(frozen=True)
class CloakBrowserSnapshotSuccess:
    requested_url: str
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    screenshot_png: bytes
    metadata: dict[str, object]
    warning_notes: list[str]
    limitation_notes: list[str]
    access_block_reason: str | None = None


@dataclass(frozen=True)
class CloakBrowserSnapshotFailure:
    requested_url: str
    failure_kind: CloakBrowserSnapshotFailureKind
    message: str
    final_url: str | None = None


CloakBrowserSnapshotResult: TypeAlias = CloakBrowserSnapshotSuccess | CloakBrowserSnapshotFailure


@dataclass(frozen=True)
class PreCaptureOutcome:
    """What a pre-capture plugin's ``before`` step did, recorded verbatim.

    ``attempted`` is whether the plugin ran at all; ``steps_completed`` is whether
    EVERY step the plugin attempted succeeded (False if any failed); ``reason`` names
    the first failed step (None when nothing failed). ``warning_notes`` are the per-step
    warnings the plugin emitted (e.g. a fallback was used). This is an observed record of
    the pre-capture attempt, never a claim that the storefront flipped -- confirmation is
    the post-capture ``confirm`` step's job (INV-1: facts only).
    """

    attempted: bool
    steps_completed: bool
    reason: str | None = None
    warning_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PinConfirmation:
    """Whether the post-capture rendered DOM CONFIRMS the plugin's intended pin took effect.

    ``confirmed`` is True only when a positive signal is observed in the rendered DOM;
    ``detail`` is the human-readable reason (the signal observed, or why it was absent).
    The adapter never asserts a pin from clicks alone -- this is the source of truth for
    the packet's ``pin_confirmed`` field and the honesty of the limitation note.
    """

    confirmed: bool
    detail: str


@dataclass(frozen=True)
class ScrollStopCondition:
    """Generic visible-text condition that may stop further lazy-load actions.

    Reaching this condition is only an interaction hint. Post-capture source-detail
    sufficiency still decides whether the preserved artifacts satisfy the goal.
    """

    visible_text_contains: tuple[str, ...] = ()
    visible_text_regexes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.visible_text_contains and not self.visible_text_regexes:
            raise ValueError("scroll stop condition requires at least one visible-text marker")
        for value in self.visible_text_contains:
            if not value.strip():
                raise ValueError("scroll stop condition literals must not be blank")
        for pattern in self.visible_text_regexes:
            if not pattern.strip():
                raise ValueError("scroll stop condition regexes must not be blank")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"scroll stop condition regex is not valid: {pattern!r}") from exc

    def reached(self, visible_text: str) -> bool:
        return all(value in visible_text for value in self.visible_text_contains) and all(
            re.search(pattern, visible_text) is not None for pattern in self.visible_text_regexes
        )


class PreCapturePlugin(Protocol):
    """Site-specific capture lifecycle steps the generic adapter runs without site knowledge.

    The generic adapter knows nothing about any storefront, widget, or signal: it calls
    ``before`` after page creation (before the main goto), ``confirm`` on the rendered DOM
    after capture, ``describe`` for non-secret metadata, and ``note`` for the operator-facing
    limitation note. A plugin may also expose ``before_scroll`` for a bounded site-owned
    interaction after navigation and settling but before any configured scrolling, and/or
    ``before_snapshot`` for a bounded interaction after scrolling but before serialization.
    All site-specific wording (storefront name, currency signals, widget steps) lives in the
    plugin, never here. ``humanize`` selects the humanized browser launch profile.
    """

    @property
    def humanize(self) -> bool:
        ...

    def before(self, page: object, *, setup_timeout_ms: float) -> PreCaptureOutcome:
        ...

    def confirm(self, rendered_dom: str) -> PinConfirmation:
        ...

    def describe(self) -> dict[str, object]:
        ...

    def note(self, outcome: PreCaptureOutcome, confirmation: PinConfirmation) -> str:
        ...


class CloakBrowserSnapshotEngineResult(Protocol):
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    screenshot_png: bytes
    warning_notes: list[str]
    capture_phase_timing: dict[str, object]
    # Recorded by the engine when a pre-capture plugin ran ``before`` the main goto; None
    # when no plugin was supplied. ``fetch_...`` reads it via getattr so engines that predate
    # the seam (or fakes) without the attribute degrade to "no plugin ran".
    pre_capture_outcome: PreCaptureOutcome | None
    # Optional bounded site-owned action after navigation/settling and before scrolling.
    before_scroll_outcome: PreCaptureOutcome | None
    # Optional bounded site-owned action after navigation/scrolling and before snapshot.
    before_snapshot_outcome: PreCaptureOutcome | None


class CloakBrowserSnapshotEngine(Protocol):
    def capture(
        self,
        *,
        url: str,
        timeout_seconds: float,
        wait_until: str,
        viewport_width: int,
        viewport_height: int,
        proxy_profile: ProxyProfile | None,
        block_heavy_assets: bool,
        settle_seconds: float,
        scroll_passes: int,
        load_more_selector: str | None,
        load_more_clicks: int,
        scroll_step_px: int,
        scroll_stop_condition: ScrollStopCondition | None,
        scroll_target_selector: str | None,
        pre_capture: PreCapturePlugin | None,
        user_data_dir: Path | None = None,
    ) -> CloakBrowserSnapshotEngineResult:
        ...


def fetch_cloakbrowser_snapshot_capture(
    *,
    url: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    wait_until: str = "load",
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
    viewport_height: int = DEFAULT_VIEWPORT_HEIGHT,
    max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    proxy_profile: ProxyProfile | None = None,
    block_heavy_assets: bool = False,
    settle_seconds: float = 0.0,
    scroll_passes: int = 0,
    load_more_selector: str | None = None,
    load_more_clicks: int = 0,
    scroll_step_px: int = 0,
    scroll_stop_condition: ScrollStopCondition | None = None,
    scroll_target_selector: str | None = None,
    pre_capture: PreCapturePlugin | None = None,
    user_data_dir: Path | None = None,
    engine: CloakBrowserSnapshotEngine | None = None,
) -> CloakBrowserSnapshotResult:
    normalized_url = _validate_http_url(url)
    _validate_positive_number("timeout_seconds", timeout_seconds)
    _validate_positive_int("viewport_width", viewport_width)
    _validate_positive_int("viewport_height", viewport_height)
    _validate_positive_int("max_artifact_bytes", max_artifact_bytes)
    if settle_seconds < 0:
        raise ValueError("settle_seconds must be zero or greater")
    if scroll_passes < 0:
        raise ValueError("scroll_passes must be zero or greater")
    if scroll_step_px < 0:
        raise ValueError("scroll_step_px must be zero or greater")
    if load_more_clicks < 0:
        raise ValueError("load_more_clicks must be zero or greater")
    if load_more_clicks > 0 and not load_more_selector:
        raise ValueError("load_more_selector is required when load_more_clicks is greater than zero")
    if scroll_target_selector is not None and scroll_stop_condition is None:
        raise ValueError("scroll_target_selector requires scroll_stop_condition")
    if user_data_dir is not None and proxy_profile is not None:
        raise ValueError(
            "CloakBrowser persistent-context capture (user_data_dir) does not apply proxy_profile; "
            "the persistent-context launch path never receives the proxy, so combining them would "
            "record proxy_used/proxy_category in packet metadata while no proxy was actually used. "
            "Supply only one of user_data_dir or proxy_profile."
        )
    if wait_until not in ALLOWED_WAIT_UNTIL:
        allowed = ", ".join(sorted(ALLOWED_WAIT_UNTIL))
        raise ValueError(f"wait_until must be one of: {allowed}")

    capture_engine = engine or _CloakBrowserSnapshotEngine()
    try:
        engine_result = capture_engine.capture(
            url=normalized_url,
            timeout_seconds=timeout_seconds,
            wait_until=wait_until,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            proxy_profile=proxy_profile,
            block_heavy_assets=block_heavy_assets,
            settle_seconds=settle_seconds,
            scroll_passes=scroll_passes,
            load_more_selector=load_more_selector,
            load_more_clicks=load_more_clicks,
            scroll_step_px=scroll_step_px,
            scroll_stop_condition=scroll_stop_condition,
            scroll_target_selector=scroll_target_selector,
            pre_capture=pre_capture,
            user_data_dir=user_data_dir,
        )
    except _CloakBrowserSnapshotDependencyUnavailable as exc:
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            failure_kind=CloakBrowserSnapshotFailureKind.DEPENDENCY_UNAVAILABLE,
            message=_redact_proxy_secret(str(exc), proxy_profile=proxy_profile),
        )
    except Exception as exc:
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            failure_kind=_failure_kind_from_exception(exc),
            message=_redact_proxy_secret(
                f"CloakBrowser snapshot capture failed: {exc}", proxy_profile=proxy_profile
            ),
        )

    final_url = _sanitize_engine_final_url(engine_result.final_url)
    if final_url is None:
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="CloakBrowser snapshot returned a final URL with embedded credentials",
        )

    if not engine_result.rendered_dom:
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            final_url=final_url,
            failure_kind=CloakBrowserSnapshotFailureKind.EMPTY_RENDERED_DOM,
            message="CloakBrowser snapshot returned an empty rendered DOM",
        )
    if not engine_result.screenshot_png:
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            final_url=final_url,
            failure_kind=CloakBrowserSnapshotFailureKind.EMPTY_SCREENSHOT,
            message="CloakBrowser snapshot returned an empty screenshot",
        )

    artifact_sizes = {
        "rendered_dom": len(engine_result.rendered_dom.encode("utf-8")),
        "visible_text": len(engine_result.visible_text.encode("utf-8")),
        "screenshot_png": len(engine_result.screenshot_png),
    }
    oversized = {
        name: size
        for name, size in artifact_sizes.items()
        if size > max_artifact_bytes
    }
    if oversized:
        details = ", ".join(f"{name}={size}" for name, size in sorted(oversized.items()))
        return CloakBrowserSnapshotFailure(
            requested_url=normalized_url,
            final_url=final_url,
            failure_kind=CloakBrowserSnapshotFailureKind.SIZE_CAP_EXCEEDED,
            message=(
                f"CloakBrowser snapshot artifact exceeded max-artifact-bytes cap "
                f"({max_artifact_bytes}): {details}"
            ),
        )

    warning_notes: list[str] = []
    if final_url != normalized_url:
        warning_notes.append(
            f"cloakbrowser_snapshot landed at {final_url} from requested URL {normalized_url}"
        )
    warning_notes.extend(
        _sanitize_engine_warning_notes(engine_result.warning_notes, proxy_profile=proxy_profile)
    )
    rendered_access = classify_rendered_access(
        title=engine_result.title,
        rendered_dom=engine_result.rendered_dom,
        visible_text=engine_result.visible_text,
    )
    access_block_reason = (
        rendered_access.signal
        if rendered_access.classification == RenderedAccessClass.ACCESS_BLOCKED
        else None
    )
    limitation_notes: list[str] = []
    if access_block_reason is not None:
        limitation_notes.append(
            "access_failed: CloakBrowser rendered an access-block/interstitial page "
            f"instead of source content: {access_block_reason}; block artifacts preserved"
        )
    elif rendered_access.classification == RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER:
        limitation_notes.append(
            "rendered_access_warning: CloakBrowser rendered DOM still contains "
            f"{rendered_access.signal}; visible text may be source content, but content "
            "sufficiency is not asserted"
        )

    # Pre-capture plugin seam: the generic adapter knows nothing about any storefront or
    # signal. It records the plugin's pre-capture OUTCOME (an attempt, never a claim) and,
    # crucially, confirms the intended effect against the RENDERED DOM here -- so the
    # limitation note and pin_confirmed flag reflect what was observed, never clicks alone.
    pre_capture_outcome: PreCaptureOutcome | None = getattr(
        engine_result, "pre_capture_outcome", None
    )
    before_scroll_outcome: PreCaptureOutcome | None = getattr(
        engine_result, "before_scroll_outcome", None
    )
    before_snapshot_outcome: PreCaptureOutcome | None = getattr(
        engine_result, "before_snapshot_outcome", None
    )
    pin_confirmed: bool | None = None
    pre_capture_metadata: dict[str, object] = {}
    if pre_capture is not None:
        if pre_capture_outcome is None:
            pre_capture_outcome = PreCaptureOutcome(
                attempted=False,
                steps_completed=False,
                reason="engine did not report a pre-capture outcome",
            )
        confirmation = pre_capture.confirm(rendered_dom=engine_result.rendered_dom)
        pin_confirmed = confirmation.confirmed
        limitation_notes.append(pre_capture.note(pre_capture_outcome, confirmation))
        pre_capture_metadata = dict(pre_capture.describe())

    capture_phase_timing = getattr(engine_result, "capture_phase_timing", None)
    if not isinstance(capture_phase_timing, dict):
        capture_phase_timing = {
            "schema_version": CAPTURE_PHASE_TIMING_SCHEMA_VERSION,
            "measurement_status": "unavailable",
            "clock": "monotonic",
            "unit": "milliseconds",
            "phases_ms": {},
            "progressive_scroll_steps": [],
            "scroll_passes": [],
            "load_more_actions": [],
            "scroll_target": {
                "configured": scroll_target_selector is not None,
                "action_ms": None,
                "condition_wait_ms": None,
                "reached": None,
            },
            "scroll_stop_condition": {
                "configured": scroll_stop_condition is not None,
                "reached": None,
                "reached_stage": None,
                "checks": [],
            },
            "total_capture_wall_ms": None,
            "reason": "capture engine did not report phase timings",
        }

    metadata = {
        "requested_url": normalized_url,
        "final_url": final_url,
        "title": engine_result.title,
        "capture_timestamp": utc_now_z(),
        "timeout_seconds": timeout_seconds,
        "wait_until": wait_until,
        "settle_seconds": settle_seconds,
        "scroll_passes": scroll_passes,
        "scroll_step_px": scroll_step_px,
        "load_more_selector": load_more_selector,
        "load_more_clicks": load_more_clicks,
        "scroll_stop_condition_configured": scroll_stop_condition is not None,
        "scroll_target_selector": scroll_target_selector,
        "viewport_width": viewport_width,
        "viewport_height": viewport_height,
        "screenshot_mode": "viewport",
        "method_category": CLOAKBROWSER_METHOD_CATEGORY,
        "browser_engine": "cloakbrowser",
        "cloakbrowser_backend": CLOAKBROWSER_BACKEND,
        "profile_persistence": "local_ignored_profile" if user_data_dir is not None else "none",
        "persistent_profile_loaded": user_data_dir is not None,
        "storage_state_loaded": False,
        "browser_context_scope": getattr(
            engine_result, "browser_context_scope", "single_capture"
        ),
        "browser_context_reused": bool(
            getattr(engine_result, "browser_context_reused", False)
        ),
        "proxy_used": proxy_profile is not None,
        "proxy_category": proxy_profile.proxy_category.value if proxy_profile is not None else None,
        "proxy_disclosure": "category_only" if proxy_profile is not None else "none",
        "proxy_endpoint_recorded": False,
        "proxy_exit_ip_recorded": False,
        "geoip_used": proxy_profile.geoip_enabled if proxy_profile is not None else False,
        "proxy_timezone": proxy_profile.timezone if proxy_profile is not None else None,
        "proxy_locale": proxy_profile.locale if proxy_profile is not None else None,
        "extension_paths_loaded": False,
        "heavy_assets_blocked": block_heavy_assets,
        "blocked_resource_types": sorted(HEAVY_RESOURCE_TYPES) if block_heavy_assets else [],
        "capture_phase_timing": capture_phase_timing,
        "access_blocked": access_block_reason is not None,
        "access_block_reason": access_block_reason,
        "rendered_access_classification": rendered_access.classification.value,
        "rendered_access_signal": rendered_access.signal,
        "rendered_access_detail": rendered_access.detail,
        # Pre-capture plugin provenance (generic; site-specific fields ride in describe()).
        # humanize_mode_active records whether the humanized launch profile was used;
        # pin_confirmed is the post-capture confirmation (None when no plugin ran), NEVER
        # inferred from clicks. attempted/steps_completed/reason mirror the before() outcome.
        "humanize_mode_active": pre_capture.humanize if pre_capture is not None else False,
        "pin_confirmed": pin_confirmed,
        "pre_capture_attempted": (
            pre_capture_outcome.attempted if pre_capture_outcome is not None else False
        ),
        "pre_capture_steps_completed": (
            pre_capture_outcome.steps_completed if pre_capture_outcome is not None else False
        ),
        "pre_capture_reason": (
            pre_capture_outcome.reason if pre_capture_outcome is not None else None
        ),
        "before_scroll_attempted": (
            before_scroll_outcome.attempted
            if before_scroll_outcome is not None
            else False
        ),
        "before_scroll_steps_completed": (
            before_scroll_outcome.steps_completed
            if before_scroll_outcome is not None
            else False
        ),
        "before_scroll_reason": (
            before_scroll_outcome.reason
            if before_scroll_outcome is not None
            else None
        ),
        "before_snapshot_attempted": (
            before_snapshot_outcome.attempted
            if before_snapshot_outcome is not None
            else False
        ),
        "before_snapshot_steps_completed": (
            before_snapshot_outcome.steps_completed
            if before_snapshot_outcome is not None
            else False
        ),
        "before_snapshot_reason": (
            before_snapshot_outcome.reason
            if before_snapshot_outcome is not None
            else None
        ),
        "rendered_dom_byte_count": artifact_sizes["rendered_dom"],
        "visible_text_byte_count": artifact_sizes["visible_text"],
        "screenshot_byte_count": artifact_sizes["screenshot_png"],
        **pre_capture_metadata,
    }

    return CloakBrowserSnapshotSuccess(
        requested_url=normalized_url,
        final_url=final_url,
        title=engine_result.title,
        rendered_dom=engine_result.rendered_dom,
        visible_text=engine_result.visible_text,
        screenshot_png=engine_result.screenshot_png,
        metadata=metadata,
        warning_notes=warning_notes,
        limitation_notes=limitation_notes,
        access_block_reason=access_block_reason,
    )


class _CloakBrowserSnapshotEngine:
    def __init__(
        self,
        *,
        clock_ns: Callable[[], int] = monotonic_ns,
        reuse_context: bool = False,
    ) -> None:
        self._clock_ns = clock_ns
        self._reuse_context = reuse_context
        self._shared_browser: object | None = None
        self._shared_context: object | None = None
        self._shared_viewport: tuple[int, int] | None = None
        self._shared_humanize: bool | None = None

    def close(self) -> None:
        context, browser = self._shared_context, self._shared_browser
        self._shared_context = None
        self._shared_browser = None
        self._shared_viewport = None
        self._shared_humanize = None
        try:
            if context is not None:
                context.close()  # type: ignore[union-attr]
        finally:
            if browser is not None:
                browser.close()  # type: ignore[union-attr]

    def capture(
        self,
        *,
        url: str,
        timeout_seconds: float,
        wait_until: str,
        viewport_width: int,
        viewport_height: int,
        proxy_profile: ProxyProfile | None,
        block_heavy_assets: bool,
        settle_seconds: float = 0.0,
        scroll_passes: int = 0,
        load_more_selector: str | None = None,
        load_more_clicks: int = 0,
        scroll_step_px: int = 0,
        scroll_stop_condition: ScrollStopCondition | None = None,
        scroll_target_selector: str | None = None,
        pre_capture: PreCapturePlugin | None = None,
        user_data_dir: Path | None = None,
    ) -> CloakBrowserSnapshotEngineResult:
        clock_ns = self._clock_ns
        capture_started_ns = clock_ns()
        phase_ms: dict[str, float] = {}
        progressive_scroll_steps: list[dict[str, float | int]] = []
        scroll_pass_timings: list[dict[str, float | int]] = []
        load_more_timings: list[dict[str, float | int]] = []

        def elapsed_ms(started_ns: int) -> float:
            return round((clock_ns() - started_ns) / 1_000_000, 3)

        humanize = pre_capture.humanize if pre_capture is not None else False
        if self._reuse_context and (proxy_profile is not None or user_data_dir is not None):
            raise ValueError(
                "run-scoped in-memory context reuse cannot load a proxy or stored profile"
            )
        # The pre-capture flow is bounded by its OWN timeout (the plugin carries it, set from
        # the writer's --delivery-zip-setup-timeout-seconds), separate from the main capture
        # timeout below. Default to the main timeout when a plugin exposes no setup bound.
        setup_timeout_ms = float(
            getattr(pre_capture, "setup_timeout_ms", None) or (timeout_seconds * 1000)
        )
        launch_started_ns = clock_ns()
        try:
            cloakbrowser = import_module("cloakbrowser")
        except ModuleNotFoundError as exc:
            raise _CloakBrowserSnapshotDependencyUnavailable(
                "CloakBrowser is not installed. Install the cloakbrowser optional dependency before "
                "running CloakBrowser snapshots."
            ) from exc

        timeout_ms = timeout_seconds * 1000
        browser = None
        context_reused = False
        try:
            if self._reuse_context and self._shared_context is not None:
                if (
                    self._shared_viewport != (viewport_width, viewport_height)
                    or self._shared_humanize != humanize
                ):
                    raise ValueError(
                        "run-scoped CloakBrowser context parameters changed mid-session"
                    )
                context = self._shared_context
                context_reused = True
                phase_ms["dependency_import_browser_launch"] = 0.0
                phase_ms["context_creation"] = 0.0
            elif user_data_dir is not None:
                profile_launcher = getattr(cloakbrowser, "launch_" + "persistent_context", None)
                if not callable(profile_launcher):
                    raise _CloakBrowserSnapshotDependencyUnavailable(
                        "CloakBrowser is installed but does not expose the required "
                        "persistent profile launch API. Install a compatible cloakbrowser "
                        "package before running profile-backed snapshots."
                    )
                context = profile_launcher(
                    user_data_dir,
                    headless=True,
                    stealth_args=True,
                    humanize=humanize,
                )
            else:
                launch = getattr(cloakbrowser, "launch", None)
                if not callable(launch):
                    raise _CloakBrowserSnapshotDependencyUnavailable(
                        "CloakBrowser is installed but does not expose cloakbrowser.launch. "
                        "Install a compatible cloakbrowser package before running CloakBrowser snapshots."
                    )
                browser = launch(
                    headless=True,
                    proxy=proxy_profile.proxy_endpoint if proxy_profile is not None else None,
                    args=None,
                    stealth_args=True,
                    timezone=proxy_profile.timezone if proxy_profile is not None else None,
                    locale=proxy_profile.locale if proxy_profile is not None else None,
                    geoip=proxy_profile.geoip_enabled if proxy_profile is not None else False,
                    humanize=humanize,
                    extension_paths=None,
                )
                phase_ms["dependency_import_browser_launch"] = elapsed_ms(launch_started_ns)
                context_started_ns = clock_ns()
                context = browser.new_context(
                    viewport={
                        "width": viewport_width,
                        "height": viewport_height,
                    }
                )
                phase_ms["context_creation"] = elapsed_ms(context_started_ns)
            if self._reuse_context and not context_reused:
                self._shared_browser = browser
                self._shared_context = context
                self._shared_viewport = (viewport_width, viewport_height)
                self._shared_humanize = humanize
                browser = None
            if user_data_dir is not None:
                phase_ms["dependency_import_browser_launch"] = elapsed_ms(launch_started_ns)
                # A persistent-context launch creates the browser context atomically.
                phase_ms["context_creation"] = 0.0
        except Exception as exc:
            if _looks_like_cloakbrowser_dependency_failure(exc):
                raise _CloakBrowserSnapshotDependencyUnavailable(
                    f"CloakBrowser dependency unavailable: {exc}"
                ) from exc
            raise

        try:
            try:
                page_started_ns = clock_ns()
                page = context.new_page()
                set_viewport_size = getattr(page, "set_viewport_size", None)
                if callable(set_viewport_size):
                    set_viewport_size({"width": viewport_width, "height": viewport_height})
                phase_ms["page_creation"] = elapsed_ms(page_started_ns)
                asset_route_started_ns = clock_ns()
                if block_heavy_assets:
                    page.route(
                        "**/*",
                        lambda route: (
                            route.abort()
                            if route.request.resource_type in HEAVY_RESOURCE_TYPES
                            else route.continue_()
                        ),
                    )
                phase_ms["asset_route_setup"] = elapsed_ms(asset_route_started_ns)
                warning_notes: list[str] = []
                scroll_stop_reached = False
                scroll_stop_reached_stage: str | None = None
                scroll_stop_checks: list[dict[str, object]] = []

                def check_scroll_stop(*, stage: str, index: int | None = None) -> bool:
                    nonlocal scroll_stop_reached, scroll_stop_reached_stage
                    if scroll_stop_condition is None:
                        return False
                    check_started_ns = clock_ns()
                    try:
                        condition_text = page.locator("body").inner_text(timeout=timeout_ms)
                        reached = scroll_stop_condition.reached(condition_text)
                    except Exception as exc:
                        reached = False
                        warning_notes.append(
                            f"cloakbrowser_snapshot scroll stop condition check failed: {exc}"
                        )
                    check: dict[str, object] = {
                        "stage": stage,
                        "check_ms": elapsed_ms(check_started_ns),
                        "reached": reached,
                    }
                    if index is not None:
                        check["index"] = index
                    scroll_stop_checks.append(check)
                    if reached:
                        scroll_stop_reached = True
                        scroll_stop_reached_stage = stage
                    return reached
                # A pre-capture plugin (e.g. a storefront delivery-location pin) runs AFTER page
                # creation but BEFORE the main goto. ``setup_timeout_ms`` bounds the plugin's own
                # navigation/widget steps separately from the main capture ``timeout_ms`` (which is
                # unchanged below). The plugin records an attempt outcome; it never claims success.
                pre_capture_outcome: PreCaptureOutcome | None = None
                pre_capture_started_ns = clock_ns()
                if pre_capture is not None:
                    pre_capture_outcome = pre_capture.before(
                        page, setup_timeout_ms=setup_timeout_ms
                    )
                    warning_notes.extend(pre_capture_outcome.warning_notes)
                phase_ms["pre_capture_plugin"] = elapsed_ms(pre_capture_started_ns)
                navigation_started_ns = clock_ns()
                page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                phase_ms["navigation_wait_until"] = elapsed_ms(navigation_started_ns)
                settle_started_ns = clock_ns()
                if settle_seconds > 0:
                    page.wait_for_timeout(settle_seconds * 1000)
                phase_ms["configured_settle"] = elapsed_ms(settle_started_ns)
                before_scroll_outcome: PreCaptureOutcome | None = None
                before_scroll_started_ns = clock_ns()
                before_scroll = getattr(pre_capture, "before_scroll", None)
                if callable(before_scroll):
                    before_scroll_outcome = before_scroll(
                        page, setup_timeout_ms=setup_timeout_ms
                    )
                    warning_notes.extend(before_scroll_outcome.warning_notes)
                phase_ms["before_scroll_plugin"] = elapsed_ms(
                    before_scroll_started_ns
                )
                check_scroll_stop(stage="after_configured_settle")
                scroll_target_timing: dict[str, object] = {
                    "configured": scroll_target_selector is not None,
                    "action_ms": None,
                    "condition_wait_ms": None,
                    "reached": scroll_stop_reached,
                }
                if scroll_target_selector is not None and not scroll_stop_reached:
                    target_action_started_ns = clock_ns()
                    target_activated = False
                    try:
                        target = page.locator(scroll_target_selector)
                        if target.count() == 0:
                            warning_notes.append(
                                "cloakbrowser_snapshot scroll target selector matched no elements"
                            )
                        else:
                            target.scroll_into_view_if_needed(
                                timeout=min(timeout_ms, _SCROLL_TARGET_CONDITION_TIMEOUT_MS)
                            )
                            target_activated = True
                    except Exception as exc:
                        warning_notes.append(
                            f"cloakbrowser_snapshot scroll target activation failed: {exc}"
                        )
                    scroll_target_timing["action_ms"] = elapsed_ms(target_action_started_ns)
                    if target_activated and scroll_stop_condition is not None:
                        target_wait_started_ns = clock_ns()
                        for _ in range(
                            _SCROLL_TARGET_CONDITION_TIMEOUT_MS // _SCROLL_TARGET_POLL_MS
                        ):
                            if check_scroll_stop(stage="scroll_target"):
                                break
                            page.wait_for_timeout(_SCROLL_TARGET_POLL_MS)
                        scroll_target_timing["condition_wait_ms"] = elapsed_ms(
                            target_wait_started_ns
                        )
                    scroll_target_timing["reached"] = scroll_stop_reached
                if scroll_step_px > 0 and not scroll_stop_reached:
                    position = 0
                    for index in range(_MAX_PROGRESSIVE_SCROLL_STEPS):
                        action_started_ns = clock_ns()
                        height = page.evaluate("() => document.body.scrollHeight")
                        if position >= height:
                            break
                        position += scroll_step_px
                        page.evaluate("(y) => window.scrollTo(0, y)", position)
                        action_ms = elapsed_ms(action_started_ns)
                        action_settle_started_ns = clock_ns()
                        page.wait_for_timeout(_PROGRESSIVE_SCROLL_PAUSE_MS)
                        progressive_scroll_steps.append(
                            {
                                "index": index + 1,
                                "action_ms": action_ms,
                                "post_action_settle_ms": elapsed_ms(action_settle_started_ns),
                            }
                        )
                        if check_scroll_stop(stage="progressive_scroll", index=index + 1):
                            break
                if not scroll_stop_reached:
                    for index in range(scroll_passes):
                        action_started_ns = clock_ns()
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        action_ms = elapsed_ms(action_started_ns)
                        action_settle_started_ns = clock_ns()
                        page.wait_for_timeout(_SCROLL_PASS_SETTLE_MS)
                        scroll_pass_timings.append(
                            {
                                "index": index + 1,
                                "action_ms": action_ms,
                                "post_action_settle_ms": elapsed_ms(action_settle_started_ns),
                            }
                        )
                        if check_scroll_stop(stage="scroll_pass", index=index + 1):
                            break
                if load_more_selector and load_more_clicks > 0 and not scroll_stop_reached:
                    for index in range(load_more_clicks):
                        if page.locator(load_more_selector).count() == 0:
                            break
                        action_started_ns = clock_ns()
                        try:
                            page.locator(load_more_selector).first.click(timeout=_LOAD_MORE_CLICK_TIMEOUT_MS)
                        except Exception as exc:
                            if index == 0:
                                warning_notes.append(
                                    "cloakbrowser_snapshot first configured load-more action failed: "
                                    f"{type(exc).__name__}: {exc}"
                                )
                            break
                        action_ms = elapsed_ms(action_started_ns)
                        action_settle_started_ns = clock_ns()
                        page.wait_for_timeout(_SCROLL_PASS_SETTLE_MS)
                        load_more_timings.append(
                            {
                                "index": index + 1,
                                "action_ms": action_ms,
                                "post_action_settle_ms": elapsed_ms(action_settle_started_ns),
                            }
                        )
                        if check_scroll_stop(stage="load_more", index=index + 1):
                            break
                before_snapshot_outcome: PreCaptureOutcome | None = None
                before_snapshot_started_ns = clock_ns()
                before_snapshot = getattr(pre_capture, "before_snapshot", None)
                if callable(before_snapshot):
                    before_snapshot_outcome = before_snapshot(
                        page, setup_timeout_ms=setup_timeout_ms
                    )
                    warning_notes.extend(before_snapshot_outcome.warning_notes)
                phase_ms["before_snapshot_plugin"] = elapsed_ms(
                    before_snapshot_started_ns
                )
                dom_started_ns = clock_ns()
                rendered_dom = page.content()
                phase_ms["dom_serialization"] = elapsed_ms(dom_started_ns)
                visible_text_started_ns = clock_ns()
                try:
                    visible_text = page.locator("body").inner_text(timeout=timeout_ms)
                except Exception as exc:
                    visible_text = ""
                    warning_notes.append(f"cloakbrowser_snapshot visible_text extraction failed: {exc}")
                phase_ms["visible_text_extraction"] = elapsed_ms(visible_text_started_ns)
                screenshot_started_ns = clock_ns()
                screenshot_png = page.screenshot(
                    type="png",
                    full_page=False,
                    timeout=timeout_ms,
                )
                phase_ms["screenshot"] = elapsed_ms(screenshot_started_ns)
                capture_phase_timing: dict[str, object] = {
                    "schema_version": CAPTURE_PHASE_TIMING_SCHEMA_VERSION,
                    "measurement_status": "measured",
                    "clock": "monotonic",
                    "unit": "milliseconds",
                    "phases_ms": phase_ms,
                    "progressive_scroll_steps": progressive_scroll_steps,
                    "scroll_passes": scroll_pass_timings,
                    "load_more_actions": load_more_timings,
                    "scroll_target": scroll_target_timing,
                    "scroll_stop_condition": {
                        "configured": scroll_stop_condition is not None,
                        "reached": scroll_stop_reached,
                        "reached_stage": scroll_stop_reached_stage,
                        "checks": scroll_stop_checks,
                    },
                }
                return _LiveEngineResult(
                    final_url=page.url,
                    title=page.title(),
                    rendered_dom=rendered_dom,
                    visible_text=visible_text,
                    screenshot_png=screenshot_png,
                    warning_notes=warning_notes,
                    pre_capture_outcome=pre_capture_outcome,
                    before_scroll_outcome=before_scroll_outcome,
                    before_snapshot_outcome=before_snapshot_outcome,
                    capture_phase_timing=capture_phase_timing,
                    browser_context_scope=(
                        "run_scoped_in_memory"
                        if self._reuse_context
                        else "single_capture"
                    ),
                    browser_context_reused=context_reused,
                )
            finally:
                close_started_ns = clock_ns()
                if self._reuse_context:
                    if "page" in locals():
                        page.close()
                else:
                    context.close()
                phase_ms["context_browser_close"] = elapsed_ms(close_started_ns)
        finally:
            if browser is not None:
                browser_close_started_ns = clock_ns()
                browser.close()
                phase_ms["context_browser_close"] = round(
                    phase_ms.get("context_browser_close", 0.0)
                    + elapsed_ms(browser_close_started_ns),
                    3,
                )
            if "capture_phase_timing" in locals():
                capture_phase_timing["total_capture_wall_ms"] = elapsed_ms(capture_started_ns)


class ReusableCloakBrowserSnapshotEngine(_CloakBrowserSnapshotEngine):
    """Reuse one anonymous in-memory context; never load or export stored state."""

    def __init__(self, *, clock_ns: Callable[[], int] = monotonic_ns) -> None:
        super().__init__(clock_ns=clock_ns, reuse_context=True)

    def __enter__(self) -> ReusableCloakBrowserSnapshotEngine:
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()


@dataclass(frozen=True)
class _LiveEngineResult:
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    screenshot_png: bytes
    warning_notes: list[str] = field(default_factory=list)
    pre_capture_outcome: PreCaptureOutcome | None = None
    before_scroll_outcome: PreCaptureOutcome | None = None
    before_snapshot_outcome: PreCaptureOutcome | None = None
    capture_phase_timing: dict[str, object] = field(default_factory=dict)
    browser_context_scope: str = "single_capture"
    browser_context_reused: bool = False


class _CloakBrowserSnapshotDependencyUnavailable(RuntimeError):
    pass


def _validate_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("CloakBrowser snapshot capture requires an absolute http:// or https:// URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("CloakBrowser snapshot capture does not accept URLs with embedded credentials")
    return parsed.geturl()


def _sanitize_engine_final_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return url
    if parsed.username is not None or parsed.password is not None:
        return None

    redacted_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if _is_secret_like_key(key):
            redacted_query.append((key, "[redacted]"))
        else:
            redacted_query.append((key, value))
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(redacted_query, doseq=True),
            parsed.fragment,
        )
    )


def _sanitize_engine_warning_notes(
    notes: list[str], *, proxy_profile: ProxyProfile | None = None
) -> list[str]:
    sanitized: list[str] = []
    for note in notes:
        lowered = note.lower()
        if any(term in lowered for term in SECRET_LIKE_WARNING_TERMS):
            sanitized.append("cloakbrowser_snapshot engine warning redacted because it contained secret-like text")
        else:
            sanitized.append(_redact_proxy_secret(note, proxy_profile=proxy_profile))
    return sanitized


def _redact_proxy_secret(text: str, *, proxy_profile: ProxyProfile | None) -> str:
    """Strip the in-memory proxy endpoint and its credentials out of operator-
    facing text before it can reach a failure message, CLI output, log, warning
    note, or packet artifact.

    The proxy endpoint string is handed straight to the CloakBrowser launch
    call, so a launch, connection, or dependency exception can echo it (and the
    embedded credentials) verbatim. This is the single point where engine and
    dependency strings are turned into surfaced text, so any endpoint substring
    is masked here. Full endpoint, password, and host[:port] are all redacted so
    a reformatted echo (host-only, credential-only) is also covered; over-
    redaction of a failure string is acceptable, leaking the endpoint is not.
    """
    if proxy_profile is None:
        return text
    endpoint = proxy_profile.proxy_endpoint
    if not endpoint:
        return text
    redacted = text.replace(endpoint, "[redacted-proxy-endpoint]")
    parsed = urlparse(endpoint)
    if parsed.password:
        redacted = redacted.replace(parsed.password, "[redacted-proxy-credential]")
    host = parsed.hostname
    if host:
        if parsed.port is not None:
            redacted = redacted.replace(f"{host}:{parsed.port}", "[redacted-proxy-endpoint]")
        redacted = redacted.replace(host, "[redacted-proxy-endpoint]")
    return redacted


def _detect_access_blocked_page(
    *,
    title: str | None,
    rendered_dom: str,
    visible_text: str,
) -> str | None:
    rendered_access = classify_rendered_access(
        title=title,
        rendered_dom=rendered_dom,
        visible_text=visible_text,
    )
    if rendered_access.classification == RenderedAccessClass.ACCESS_BLOCKED:
        return rendered_access.signal
    return None


def _is_secret_like_key(key: str) -> bool:
    lowered = key.lower()
    return any(term in lowered for term in SECRET_LIKE_QUERY_KEYS)


def _validate_positive_number(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def _validate_positive_int(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def _failure_kind_from_exception(error: Exception) -> CloakBrowserSnapshotFailureKind:
    text = f"{type(error).__name__}: {error}".lower()
    if "timeout" in text or "timed out" in text:
        return CloakBrowserSnapshotFailureKind.TIMEOUT
    return CloakBrowserSnapshotFailureKind.CAPTURE_FAILED


def _looks_like_cloakbrowser_dependency_failure(error: Exception) -> bool:
    text = f"{type(error).__name__}: {error}".lower()
    if "geoip2" in text or "socksio" in text:
        return True
    return "cloakbrowser" in text and (
        "binary" in text
        or "chromium" in text
        or "download" in text
        or "executable" in text
        or "not found" in text
    )
