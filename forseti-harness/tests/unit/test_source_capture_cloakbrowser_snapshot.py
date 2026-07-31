from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import source_capture.adapters.cloakbrowser_snapshot as cloakbrowser_snapshot_module
from runners import run_source_capture_cloakbrowser_packet as cloakbrowser_runner
from runners.run_source_capture_cloakbrowser_packet import CLOAKBROWSER_SNAPSHOT_NON_CLAIMS
from source_capture import CaptureModeCategory
from source_capture.adapters.cloakbrowser_snapshot import (
    CloakBrowserSnapshotFailure,
    CloakBrowserSnapshotFailureKind,
    CloakBrowserSnapshotSuccess,
    PinConfirmation,
    PreCaptureOutcome,
    _CloakBrowserSnapshotEngine,
    _looks_like_cloakbrowser_dependency_failure,
    fetch_cloakbrowser_snapshot_capture,
)
from source_capture.proxy_profiles import ProxyCategory, ProxyProfile
from source_capture.retail_capture_profiles import get_retail_capture_profile
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
    SourceDetailSufficiencyRequirements,
)


@pytest.fixture
def scratch_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "_test_runs"
    path = root / f"source_capture_cloakbrowser_snapshot_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@dataclass(frozen=True)
class _FakeEngineResult:
    final_url: str
    title: str | None
    rendered_dom: str
    visible_text: str
    screenshot_png: bytes
    warning_notes: list[str] = field(default_factory=list)
    navigation_response_status: int | None = None
    navigation_retry_after: str | None = None


class _FakeCloakBrowserEngine:
    def __init__(self, result: _FakeEngineResult | Exception) -> None:
        self.result = result
        self.capture_kwargs: dict[str, object] | None = None

    def capture(self, **kwargs: object) -> _FakeEngineResult:
        self.capture_kwargs = dict(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_fetch_cloakbrowser_snapshot_capture_with_fake_engine_records_method_provenance() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/rendered",
            title="Rendered Source",
            rendered_dom="<html><body><h1>Rendered source</h1></body></html>",
            visible_text="Rendered source",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        timeout_seconds=5,
        wait_until="domcontentloaded",
        viewport_width=1024,
        viewport_height=768,
        max_artifact_bytes=10_000,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.requested_url == "https://example.com/source"
    assert result.final_url == "https://example.com/rendered"
    assert result.warning_notes == [
        "cloakbrowser_snapshot landed at https://example.com/rendered from requested URL https://example.com/source"
    ]
    assert result.metadata["method_category"] == "anti_blocking_browser"
    assert result.metadata["browser_engine"] == "cloakbrowser"
    assert result.metadata["cloakbrowser_backend"] == "playwright"
    assert result.metadata["profile_persistence"] == "none"
    assert result.metadata["persistent_profile_loaded"] is False
    assert result.metadata["storage_state_loaded"] is False
    assert result.metadata["proxy_used"] is False
    assert result.metadata["proxy_category"] is None
    assert result.metadata["proxy_disclosure"] == "none"
    assert result.metadata["proxy_endpoint_recorded"] is False
    assert result.metadata["proxy_exit_ip_recorded"] is False
    assert result.metadata["geoip_used"] is False
    assert result.metadata["extension_paths_loaded"] is False
    assert result.metadata["wait_until"] == "domcontentloaded"
    assert result.metadata["viewport_width"] == 1024
    assert result.metadata["viewport_height"] == 768
    assert result.metadata["screenshot_mode"] == "viewport"
    assert result.metadata["capture_phase_timing"] == {
        "schema_version": 3,
        "measurement_status": "unavailable",
        "clock": "monotonic",
        "unit": "milliseconds",
        "phases_ms": {},
        "progressive_scroll_steps": [],
        "scroll_passes": [],
        "load_more_actions": [],
        "scroll_target": {
            "configured": False,
            "action_ms": None,
            "condition_wait_ms": None,
            "reached": None,
        },
        "scroll_stop_condition": {
            "configured": False,
            "reached": None,
            "reached_stage": None,
            "checks": [],
        },
        "total_capture_wall_ms": None,
        "reason": "capture engine did not report phase timings",
    }
    assert result.metadata["rendered_dom_byte_count"] == len(result.rendered_dom.encode("utf-8"))
    assert result.metadata["visible_text_byte_count"] == len(result.visible_text.encode("utf-8"))
    assert result.metadata["screenshot_byte_count"] == len(result.screenshot_png)
    assert result.metadata["access_blocked"] is False
    assert result.metadata["access_block_reason"] is None
    assert result.metadata["navigation_response_status"] is None
    assert result.metadata["navigation_retry_after"] is None
    assert result.access_block_reason is None
    assert result.limitation_notes == []
    assert engine.capture_kwargs == {
        "url": "https://example.com/source",
        "timeout_seconds": 5,
        "wait_until": "domcontentloaded",
        "viewport_width": 1024,
        "viewport_height": 768,
        "proxy_profile": None,
        "block_heavy_assets": False,
        "settle_seconds": 0.0,
        "scroll_passes": 0,
        "load_more_selector": None,
        "load_more_clicks": 0,
        "scroll_step_px": 0,
        "scroll_stop_condition": None,
        "scroll_target_selector": None,
        "pre_capture": None,
        "user_data_dir": None,
        "full_page_screenshot": False,
    }


def test_fetch_cloakbrowser_snapshot_records_rate_limit_status_and_retry_after() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/source",
            title=None,
            rendered_dom="<html><body>local_rate_limited</body></html>",
            visible_text="local_rate_limited",
            screenshot_png=b"\x89PNG\r\n\x1a\nrate-limit",
            navigation_response_status=429,
            navigation_retry_after="120",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        max_artifact_bytes=10_000,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.access_block_reason == "local_rate_limited"
    assert result.metadata["access_blocked"] is True
    assert result.metadata["navigation_response_status"] == 429
    assert result.metadata["navigation_retry_after"] == "120"
    assert any(note.startswith("access_failed:") for note in result.limitation_notes)


def test_fetch_cloakbrowser_snapshot_treats_http_429_as_rate_limited() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/source",
            title="Temporary response",
            rendered_dom="<html><body>Please retry later</body></html>",
            visible_text="Please retry later",
            screenshot_png=b"\x89PNG\r\n\x1a\nrate-limit",
            navigation_response_status=429,
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        max_artifact_bytes=10_000,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.access_block_reason == "http_429_rate_limited"


def _fake_engine() -> _FakeCloakBrowserEngine:
    return _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/rendered",
            title="Rendered Source",
            rendered_dom="<html><body><h1>Rendered source</h1></body></html>",
            visible_text="Rendered source",
            screenshot_png=b"cloakbrowser-png-bytes",
        )
    )


def test_full_page_screenshot_forwards_and_is_stated_in_provenance() -> None:
    """The flag must reach the engine AND be reported in the metadata.

    screenshot_mode used to be the literal "viewport", which would have kept
    reporting viewport while capturing full pages. Provenance that silently
    lies is worse than provenance that is missing: a reader cannot tell it
    is wrong.
    """
    engine = _fake_engine()
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=engine,
        full_page_screenshot=True,
    )
    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["full_page_screenshot"] is True
    assert result.metadata["screenshot_mode"] == "full_page"


def test_viewport_stays_the_default_for_existing_callers() -> None:
    engine = _fake_engine()
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=engine,
    )
    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["full_page_screenshot"] is False
    assert result.metadata["screenshot_mode"] == "viewport"


def test_fetch_cloakbrowser_snapshot_capture_default_engine_is_visible_dependency_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import_module(name: str) -> object:
        assert name == "cloakbrowser"
        raise ModuleNotFoundError("No module named 'cloakbrowser'")

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    result = fetch_cloakbrowser_snapshot_capture(url="https://example.com/source")

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.DEPENDENCY_UNAVAILABLE
    assert "CloakBrowser is not installed" in result.message


def test_live_engine_returns_dependency_stop_when_launch_api_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCloakBrowserModule:
        pass

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    result = fetch_cloakbrowser_snapshot_capture(url="https://example.com/source")

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.DEPENDENCY_UNAVAILABLE
    assert "does not expose cloakbrowser.launch" in result.message


def test_geoip_missing_extra_is_classified_as_dependency_failure() -> None:
    error = ModuleNotFoundError("No module named 'geoip2'")

    assert _looks_like_cloakbrowser_dependency_failure(error) is True


def test_live_engine_uses_anonymous_non_persistent_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    launch_kwargs: dict[str, object] = {}
    context_kwargs: dict[str, object] = {}
    goto_kwargs: dict[str, object] = {}

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "Visible source text"

    class FakeNavigationResponse:
        status = 429
        headers = {"retry-after": "120", "set-cookie": "must-not-be-copied"}

    class FakePage:
        url = "https://example.com/rendered"

        def goto(self, url: str, **kwargs: object) -> FakeNavigationResponse:
            goto_kwargs["url"] = url
            goto_kwargs.update(kwargs)
            return FakeNavigationResponse()

        def content(self) -> str:
            return "<html><body>Visible source text</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            assert selector == "body"
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            assert kwargs == {"type": "png", "full_page": False, "timeout": 5000}
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Rendered Source"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            context_kwargs["closed"] = True

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            context_kwargs.update(kwargs)
            return FakeContext()

        def close(self) -> None:
            launch_kwargs["closed"] = True

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            launch_kwargs.update(kwargs)
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    result = _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/source",
        timeout_seconds=5,
        wait_until="domcontentloaded",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
    )

    assert result.final_url == "https://example.com/rendered"
    assert result.title == "Rendered Source"
    assert result.rendered_dom == "<html><body>Visible source text</body></html>"
    assert result.visible_text == "Visible source text"
    assert result.screenshot_png == b"\x89PNG\r\n\x1a\ncloakbrowser"
    assert result.navigation_response_status == 429
    assert result.navigation_retry_after == "120"
    assert launch_kwargs == {
        "headless": True,
        "proxy": None,
        "args": None,
        "stealth_args": True,
        "timezone": None,
        "locale": None,
        "geoip": False,
        "humanize": False,
        "extension_paths": None,
        "closed": True,
    }
    assert context_kwargs == {
        "viewport": {
            "width": 1024,
            "height": 768,
        },
        "closed": True,
    }
    assert goto_kwargs == {
        "url": "https://example.com/source",
        "wait_until": "domcontentloaded",
        "timeout": 5000,
    }


def test_live_engine_uses_persistent_profile_context_when_user_data_dir_is_supplied(
    monkeypatch: pytest.MonkeyPatch, scratch_dir: Path
) -> None:
    launch_called = False
    persistent_context_kwargs: dict[str, object] = {}
    viewport_size: dict[str, int] = {}

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "Visible profile-backed source text"

    class FakePage:
        url = "https://example.com/profile-rendered"

        def set_viewport_size(self, viewport: dict[str, int]) -> None:
            viewport_size.update(viewport)

        def goto(self, url: str, **kwargs: object) -> None:
            return None

        def content(self) -> str:
            return "<html><body>Visible profile-backed source text</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Profile Rendered Source"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            persistent_context_kwargs["closed"] = True

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> object:
            nonlocal launch_called
            launch_called = True
            raise AssertionError("anonymous launch should not be used")

        def launch_persistent_context(self, user_data_dir: Path, **kwargs: object) -> FakeContext:
            persistent_context_kwargs["user_data_dir"] = user_data_dir
            persistent_context_kwargs.update(kwargs)
            return FakeContext()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    result = _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/source",
        timeout_seconds=5,
        wait_until="domcontentloaded",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        user_data_dir=scratch_dir,
    )

    assert result.final_url == "https://example.com/profile-rendered"
    assert result.title == "Profile Rendered Source"
    assert result.visible_text == "Visible profile-backed source text"
    assert launch_called is False
    assert persistent_context_kwargs == {
        "user_data_dir": scratch_dir,
        "headless": True,
        "stealth_args": True,
        "humanize": False,
        "closed": True,
    }
    assert viewport_size == {"width": 1024, "height": 768}

def test_live_engine_passes_proxy_profile_only_to_cloakbrowser_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launch_kwargs: dict[str, object] = {}

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "Visible source text"

    class FakePage:
        url = "https://example.com/rendered"

        def goto(self, url: str, **kwargs: object) -> None:
            return None

        def content(self) -> str:
            return "<html><body>Visible source text</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Rendered Source"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            launch_kwargs.update(kwargs)
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/source",
        timeout_seconds=5,
        wait_until="domcontentloaded",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=profile,
        block_heavy_assets=False,
    )

    assert launch_kwargs["proxy"] == "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"
    assert launch_kwargs["geoip"] is True
    # A profile that declared no geo must still launch with timezone/locale None.
    assert launch_kwargs["timezone"] is None
    assert launch_kwargs["locale"] is None


def test_live_engine_passes_declared_proxy_geo_to_cloakbrowser_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launch_kwargs: dict[str, object] = {}

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "Visible source text"

    class FakePage:
        url = "https://example.com/rendered"

        def goto(self, url: str, **kwargs: object) -> None:
            return None

        def content(self) -> str:
            return "<html><body>Visible source text</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Rendered Source"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            launch_kwargs.update(kwargs)
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
        timezone="America/New_York",
        locale="en-US",
    )

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/source",
        timeout_seconds=5,
        wait_until="domcontentloaded",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=profile,
        block_heavy_assets=False,
    )

    # The declared target geo must reach the cloaked-browser launch so the rendered
    # session's timezone/locale match the proxy exit country, not the capture host.
    assert launch_kwargs["timezone"] == "America/New_York"
    assert launch_kwargs["locale"] == "en-US"
    assert launch_kwargs["proxy"] == "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"
    assert launch_kwargs["geoip"] is True


def test_fetch_cloakbrowser_snapshot_capture_records_declared_proxy_geo() -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
        timezone="America/New_York",
        locale="en-US",
    )
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        proxy_profile=profile,
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.metadata["proxy_timezone"] == "America/New_York"
    assert result.metadata["proxy_locale"] == "en-US"
    # Declared geo is non-secret, but the endpoint/credentials still must not leak.
    serialized = json.dumps(result.metadata, sort_keys=True)
    assert "SUPER_SECRET_PROXY_VALUE" not in serialized
    assert "proxy.example" not in serialized


def test_fetch_cloakbrowser_snapshot_capture_records_proxy_category_without_endpoint() -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        proxy_profile=profile,
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.metadata["proxy_used"] is True
    assert result.metadata["proxy_category"] == "residential_static"
    assert result.metadata["proxy_disclosure"] == "category_only"
    assert result.metadata["proxy_endpoint_recorded"] is False
    assert result.metadata["proxy_exit_ip_recorded"] is False
    assert result.metadata["geoip_used"] is True
    serialized = json.dumps(result.metadata, sort_keys=True)
    assert "SUPER_SECRET_PROXY_VALUE" not in serialized
    assert "proxy.example" not in serialized


def test_fetch_cloakbrowser_snapshot_capture_passes_settle_seconds_to_engine_and_metadata() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/listing",
            title="Listing",
            rendered_dom="<html><body>grid</body></html>",
            visible_text="grid",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/listing",
        settle_seconds=8,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["settle_seconds"] == 8
    assert result.metadata["settle_seconds"] == 8


def test_fetch_cloakbrowser_snapshot_capture_rejects_negative_settle_seconds() -> None:
    with pytest.raises(ValueError, match="settle_seconds"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/listing",
            settle_seconds=-1,
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/listing",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_live_engine_waits_after_load_when_settle_seconds_set(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    waited: list[float] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "grid"

    class FakePage:
        url = "https://example.com/listing"

        def goto(self, url: str, **kwargs: object) -> None:
            calls.append("goto")

        def wait_for_timeout(self, ms: float) -> None:
            waited.append(ms)
            calls.append("wait")

        def content(self) -> str:
            calls.append("content")
            return "<html><body>grid</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Listing"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/listing",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=8,
    )

    # The settle wait fires AFTER goto and BEFORE content extraction.
    assert waited == [8000]
    assert calls.index("goto") < calls.index("wait") < calls.index("content")


def test_cloakbrowser_runner_threads_settle_seconds_to_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://example.com/listing",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/listing",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="does settle thread through?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test settle threading",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        settle_seconds=8,
    )

    assert exit_code == 3
    assert seen["settle_seconds"] == 8


def test_fetch_cloakbrowser_snapshot_capture_passes_scroll_passes_to_engine_and_metadata() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/reviews",
            title="Reviews",
            rendered_dom="<html><body>reviews</body></html>",
            visible_text="reviews",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/reviews",
        scroll_passes=3,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["scroll_passes"] == 3
    assert result.metadata["scroll_passes"] == 3


def test_fetch_cloakbrowser_snapshot_capture_rejects_negative_scroll_passes() -> None:
    with pytest.raises(ValueError, match="scroll_passes"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/reviews",
            scroll_passes=-1,
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/reviews",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_live_engine_scrolls_after_settle_when_scroll_passes_set(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    scrolls: list[str] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "reviews"

    class FakePage:
        url = "https://example.com/reviews"

        def goto(self, url: str, **kwargs: object) -> None:
            calls.append("goto")

        def wait_for_timeout(self, ms: float) -> None:
            calls.append("wait")

        def evaluate(self, script: str) -> None:
            scrolls.append(script)
            calls.append("scroll")

        def content(self) -> str:
            calls.append("content")
            return "<html><body>reviews</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Reviews"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/reviews",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=0.0,
        scroll_passes=3,
    )

    # Three scroll-to-bottom passes, all between goto and the content capture.
    assert len(scrolls) == 3
    assert all("scrollto" in s.lower() for s in scrolls)
    assert calls.count("scroll") == 3
    assert calls.index("goto") < calls.index("scroll") < calls.index("content")


def test_cloakbrowser_runner_threads_scroll_passes_to_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://example.com/reviews",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/reviews",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="does scroll thread through?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test scroll threading",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        scroll_passes=4,
    )

    assert exit_code == 3
    assert seen["scroll_passes"] == 4


def test_fetch_cloakbrowser_snapshot_capture_passes_load_more_to_engine_and_metadata() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/reviews",
            title="Reviews",
            rendered_dom="<html><body>reviews</body></html>",
            visible_text="reviews",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/reviews",
        load_more_selector="text=Show more",
        load_more_clicks=4,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["load_more_selector"] == "text=Show more"
    assert engine.capture_kwargs["load_more_clicks"] == 4
    assert result.metadata["load_more_selector"] == "text=Show more"
    assert result.metadata["load_more_clicks"] == 4


def test_fetch_cloakbrowser_snapshot_capture_requires_selector_for_load_more_clicks() -> None:
    with pytest.raises(ValueError, match="load_more_selector is required"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/reviews",
            load_more_clicks=3,
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/reviews",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_fetch_cloakbrowser_snapshot_capture_rejects_negative_load_more_clicks() -> None:
    with pytest.raises(ValueError, match="load_more_clicks must be zero or greater"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/reviews",
            load_more_selector="text=Show more",
            load_more_clicks=-1,
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/reviews",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_live_engine_clicks_load_more_until_selector_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeBodyLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "reviews"

    class FakeLoadMoreLocator:
        # Present for two clicks; the count gate then reports normal control exhaustion.
        def __init__(self, state: dict) -> None:
            self._state = state

        def count(self) -> int:
            return 1 if self._state["clicks"] < 2 else 0

        @property
        def first(self) -> "FakeLoadMoreLocator":
            return self

        def click(self, *, timeout: float) -> None:
            if self._state["clicks"] >= 2:
                raise TimeoutError("load-more control is gone")
            self._state["clicks"] += 1
            calls.append("click")

    class FakePage:
        url = "https://example.com/reviews"

        def __init__(self) -> None:
            self._state = {"clicks": 0}

        def goto(self, url: str, **kwargs: object) -> None:
            calls.append("goto")

        def wait_for_timeout(self, ms: float) -> None:
            calls.append("wait")

        def content(self) -> str:
            calls.append("content")
            return "<html><body>reviews</body></html>"

        def locator(self, selector: str):
            if selector == "body":
                return FakeBodyLocator()
            return FakeLoadMoreLocator(self._state)

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Reviews"

    page = FakePage()

    class FakeContext:
        def new_page(self) -> FakePage:
            return page

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/reviews",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=0.0,
        scroll_passes=0,
        load_more_selector="text=Show more",
        load_more_clicks=5,
    )

    # 5 requested, but the control vanishes after 2 -> stops at 2, all before content.
    assert calls.count("click") == 2
    assert calls.index("goto") < calls.index("click") < calls.index("content")


def test_cloakbrowser_runner_threads_load_more_to_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://example.com/reviews",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/reviews",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="does load-more thread through?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test load-more threading",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        load_more_selector="text=Show more",
        load_more_clicks=3,
    )

    assert exit_code == 3
    assert seen["load_more_selector"] == "text=Show more"
    assert seen["load_more_clicks"] == 3


def test_cloakbrowser_runner_uses_sephora_grid_profile_load_more_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://www.sephora.com/brand/clinique?country_switch=us",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://www.sephora.com/brand/clinique?country_switch=us",
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        decision_question="does the profile own bounded grid continuation?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test Sephora grid continuation profile",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        retail_capture_profile=get_retail_capture_profile("sephora_grid_aggregate"),
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        sephora_market="US",
        retail_grid_projection_output=Path("unused_projection_on_failure.json"),
    )

    assert exit_code == 3
    assert seen["load_more_selector"] == "text=Show More Products"
    assert seen["load_more_clicks"] == 10
    assert seen["scroll_stop_condition"] is None
    assert seen["pre_capture"].humanize is True
    content_extraction = cloakbrowser_runner._sephora_grid_content_extraction_spec()
    assert content_extraction.requested_retention_mode == "content"
    assert content_extraction.extractor_version == "sephora_grid_content_v1"


def test_cloakbrowser_runner_uses_sephora_catalog_profile_without_load_more(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}
    url = (
        "https://www.sephora.com/shop/makeup-cosmetics?country_switch=us"
        "&lang=en&currentPage=1&sortBy=BEST_SELLING"
    )

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url=url,
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(
        cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture
    )

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url=url,
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        decision_question="does the catalog profile own bounded PageJSON traversal?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test Sephora catalog grid profile",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        retail_capture_profile=get_retail_capture_profile(
            "sephora_catalog_grid_aggregate"
        ),
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        sephora_market="US",
        retail_grid_projection_output=Path("unused_projection_on_failure.json"),
        sephora_catalog_page_count=5,
    )

    assert exit_code == 3
    assert seen["load_more_selector"] is None
    assert seen["load_more_clicks"] == 0
    assert seen["scroll_step_px"] == 0
    assert seen["scroll_stop_condition"] is None
    assert seen["pre_capture"].page_count == 5
    content_extraction = (
        cloakbrowser_runner._sephora_catalog_grid_content_extraction_spec()
    )
    assert content_extraction.requested_retention_mode == "content"
    assert content_extraction.extractor_version == (
        "sephora_catalog_grid_content_v1"
    )


def test_cloakbrowser_runner_uses_ulta_grid_profile_load_more_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://www.ulta.com/brand/clinique",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://www.ulta.com/brand/clinique",
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        decision_question="does the profile own bounded grid continuation?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test Ulta grid continuation profile",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        retail_capture_profile=get_retail_capture_profile("ulta_grid_aggregate"),
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        ulta_market="US",
        retail_grid_projection_output=Path("unused_projection_on_failure.json"),
    )

    assert exit_code == 3
    assert seen["load_more_selector"] == "button.LoadContent__button"
    assert seen["load_more_clicks"] == 10
    assert seen["scroll_stop_condition"] is None
    assert seen["pre_capture"].page_kind == "grid"
    assert seen["pre_capture"].humanize is False
    content_extraction = cloakbrowser_runner._ulta_grid_content_extraction_spec()
    assert content_extraction.requested_retention_mode == "content"
    assert content_extraction.extractor_version == "ulta_grid_content_v1"


def test_live_engine_runs_early_and_late_site_actions_at_their_owned_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "rendered source"

    class FakePage:
        url = "https://example.com/rendered"

        def goto(self, url: str, **kwargs: object) -> None:
            calls.append("goto")

        def wait_for_timeout(self, ms: float) -> None:
            calls.append("wait")

        def evaluate(self, script: str, arg: object = None) -> object:
            if "scrollHeight" in script:
                return 700
            if "scrollTo" in script:
                calls.append("scroll")
            return None

        def content(self) -> str:
            calls.append("content")
            return "<html><body>rendered source</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Rendered source"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    class FakePlugin:
        humanize = False

        def before(
            self, page: object, *, setup_timeout_ms: float
        ) -> PreCaptureOutcome:
            calls.append("before")
            return PreCaptureOutcome(attempted=True, steps_completed=True)

        def before_snapshot(
            self, page: object, *, setup_timeout_ms: float
        ) -> PreCaptureOutcome:
            calls.append("before_snapshot")
            return PreCaptureOutcome(attempted=True, steps_completed=True)

        def before_scroll(
            self, page: object, *, setup_timeout_ms: float
        ) -> PreCaptureOutcome:
            calls.append("before_scroll")
            return PreCaptureOutcome(attempted=True, steps_completed=True)

        def confirm(self, rendered_dom: str) -> PinConfirmation:
            return PinConfirmation(confirmed=True, detail="fixture")

        def describe(self) -> dict[str, object]:
            return {}

        def note(
            self,
            outcome: PreCaptureOutcome,
            confirmation: PinConfirmation,
        ) -> str:
            return "fixture"

    monkeypatch.setattr(
        cloakbrowser_snapshot_module,
        "import_module",
        lambda name: FakeCloakBrowserModule(),
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/rendered",
        timeout_seconds=5,
        pre_capture=FakePlugin(),
        scroll_step_px=700,
        engine=_CloakBrowserSnapshotEngine(),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert (
        calls.index("goto")
        < calls.index("before_scroll")
        < calls.index("scroll")
        < calls.index("before_snapshot")
        < calls.index("content")
    )
    assert result.metadata["before_scroll_attempted"] is True
    assert result.metadata["before_scroll_steps_completed"] is True
    assert result.metadata["before_snapshot_attempted"] is True
    assert result.metadata["before_snapshot_steps_completed"] is True


def test_fetch_cloakbrowser_snapshot_capture_passes_scroll_step_px_to_engine_and_metadata() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/reviews",
            title="Reviews",
            rendered_dom="<html><body>reviews</body></html>",
            visible_text="reviews",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/reviews",
        scroll_step_px=700,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["scroll_step_px"] == 700
    assert result.metadata["scroll_step_px"] == 700


def test_fetch_cloakbrowser_snapshot_capture_passes_scroll_target_to_engine_and_metadata() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/reviews",
            title="Reviews",
            rendered_dom="<html><body>reviews</body></html>",
            visible_text="reviews",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/reviews",
        scroll_target_selector="#reviews",
        scroll_stop_condition=cloakbrowser_snapshot_module.ScrollStopCondition(
            visible_text_contains=("reviews",)
        ),
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["scroll_target_selector"] == "#reviews"
    assert result.metadata["scroll_target_selector"] == "#reviews"


def test_fetch_cloakbrowser_snapshot_capture_requires_condition_for_scroll_target() -> None:
    with pytest.raises(ValueError, match="scroll_target_selector requires scroll_stop_condition"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/reviews",
            scroll_target_selector="#reviews",
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/reviews",
                    title="Reviews",
                    rendered_dom="<html><body>reviews</body></html>",
                    visible_text="reviews",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_fetch_cloakbrowser_snapshot_capture_rejects_negative_scroll_step_px() -> None:
    with pytest.raises(ValueError, match="scroll_step_px"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/reviews",
            scroll_step_px=-1,
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/reviews",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_live_engine_progressive_scrolls_before_scroll_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    scrolled_y: list[int] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "reviews"

    class FakePage:
        url = "https://example.com/reviews"

        def goto(self, url: str, **kwargs: object) -> None:
            calls.append("goto")

        def wait_for_timeout(self, ms: float) -> None:
            calls.append("wait")

        def evaluate(self, script: str, arg: object = None) -> object:
            if "scrollHeight" in script:
                return 3000
            if "scrollTo" in script:
                scrolled_y.append(arg)
                calls.append("scroll")
            return None

        def content(self) -> str:
            calls.append("content")
            return "<html><body>reviews</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Reviews"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/reviews",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=0.0,
        scroll_passes=0,
        load_more_selector=None,
        load_more_clicks=0,
        scroll_step_px=700,
    )

    # Steps of 700px until position reaches the 3000px page height: strictly
    # increasing, bounded, and all before the content capture.
    assert scrolled_y == [700, 1400, 2100, 2800, 3500]
    assert scrolled_y == sorted(scrolled_y)
    assert len(scrolled_y) <= cloakbrowser_snapshot_module._MAX_PROGRESSIVE_SCROLL_STEPS
    assert calls.index("goto") < calls.index("scroll") < calls.index("content")


def test_live_engine_progressive_scroll_is_bounded_by_step_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    scrolled_y: list[int] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "reviews"

    class FakePage:
        url = "https://example.com/reviews"

        def goto(self, url: str, **kwargs: object) -> None:
            return None

        def wait_for_timeout(self, ms: float) -> None:
            return None

        def evaluate(self, script: str, arg: object = None) -> object:
            if "scrollHeight" in script:
                return 10_000_000  # an effectively endless (infinite-scroll) page
            if "scrollTo" in script:
                scrolled_y.append(arg)
            return None

        def content(self) -> str:
            return "<html><body>reviews</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Reviews"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/reviews",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=0.0,
        scroll_passes=0,
        load_more_selector=None,
        load_more_clicks=0,
        scroll_step_px=700,
    )

    # An endless page must still stop at the module step cap (never unbounded).
    assert len(scrolled_y) == cloakbrowser_snapshot_module._MAX_PROGRESSIVE_SCROLL_STEPS


def test_live_engine_progressive_scroll_no_op_on_zero_height(monkeypatch: pytest.MonkeyPatch) -> None:
    scrolled_y: list[int] = []

    class FakeLocator:
        def inner_text(self, *, timeout: float) -> str:
            return "reviews"

    class FakePage:
        url = "https://example.com/reviews"

        def goto(self, url: str, **kwargs: object) -> None:
            return None

        def wait_for_timeout(self, ms: float) -> None:
            return None

        def evaluate(self, script: str, arg: object = None) -> object:
            if "scrollHeight" in script:
                return 0  # nothing scrollable (empty/zero-height body)
            if "scrollTo" in script:
                scrolled_y.append(arg)
            return None

        def content(self) -> str:
            return "<html><body>reviews</body></html>"

        def locator(self, selector: str) -> FakeLocator:
            return FakeLocator()

        def screenshot(self, **kwargs: object) -> bytes:
            return b"\x89PNG\r\n\x1a\ncloakbrowser"

        def title(self) -> str:
            return "Reviews"

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self, **kwargs: object) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeCloakBrowserModule:
        def launch(self, **kwargs: object) -> FakeBrowser:
            return FakeBrowser()

    def fake_import_module(name: str) -> FakeCloakBrowserModule:
        assert name == "cloakbrowser"
        return FakeCloakBrowserModule()

    monkeypatch.setattr(cloakbrowser_snapshot_module, "import_module", fake_import_module)

    _CloakBrowserSnapshotEngine().capture(
        url="https://example.com/reviews",
        timeout_seconds=5,
        wait_until="load",
        viewport_width=1024,
        viewport_height=768,
        proxy_profile=None,
        block_heavy_assets=False,
        settle_seconds=0.0,
        scroll_passes=0,
        load_more_selector=None,
        load_more_clicks=0,
        scroll_step_px=700,
    )

    # A zero-height page makes the progressive phase a clean no-op (0 >= 0 breaks first).
    assert scrolled_y == []


def test_cloakbrowser_runner_threads_scroll_step_px_to_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://example.com/reviews",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/reviews",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="does scroll-step thread through?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test scroll-step threading",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
        scroll_step_px=700,
    )

    assert exit_code == 3
    assert seen["scroll_step_px"] == 700


def test_cloakbrowser_runner_uses_retail_profile_scroll_target(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        seen.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url="https://www.sephora.com/product/lip-sleeping-mask-P420652",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="stub failure after recording kwargs",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)
    profile = cloakbrowser_runner.get_retail_capture_profile("sephora_pdp_distribution")

    exit_code, _ = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://www.sephora.com/product/lip-sleeping-mask-P420652",
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        decision_question="does the target selector thread through?",
        output_directory=Path("unused_no_packet_on_failure"),
        capture_context="test target-selector threading",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        retail_capture_profile=profile,
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
    )

    assert exit_code == 3
    assert seen["scroll_target_selector"] == "#ratings-reviews-container"


def test_fetch_cloakbrowser_snapshot_capture_records_heavy_asset_blocking() -> None:
    engine = _FakeCloakBrowserEngine(
        _FakeEngineResult(
            final_url="https://example.com/source",
            title=None,
            rendered_dom="<html><body>ok</body></html>",
            visible_text="ok",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        )
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        block_heavy_assets=True,
        engine=engine,
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.metadata["heavy_assets_blocked"] is True
    assert result.metadata["blocked_resource_types"] == ["font", "image", "media"]
    assert engine.capture_kwargs is not None
    assert engine.capture_kwargs["block_heavy_assets"] is True


def test_fetch_cloakbrowser_snapshot_capture_metadata_has_no_secret_bearing_fields() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    serialized = json.dumps(result.metadata, sort_keys=True).lower()
    forbidden_terms = {
        "authorization",
        "bearer",
        "client_secret",
        "cookie",
        "password",
        "proxy_url",
        "storage_state_path",
        "token",
        "user_data_dir",
    }
    assert not any(term in serialized for term in forbidden_terms)


def test_fetch_cloakbrowser_snapshot_capture_preserves_access_blocked_reddit_security_page() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
                title="",
                rendered_dom=(
                    "<html><body>You've been blocked by network security. "
                    "If you think you've been blocked by mistake, file a ticket below."
                    "</body></html>"
                ),
                visible_text=(
                    "You've been blocked by network security. If you think you've been blocked "
                    "by mistake, file a ticket below and we'll look into it. File a ticket"
                ),
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.final_url == "https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/"
    assert result.access_block_reason == "reddit_network_security_block"
    assert result.metadata["access_blocked"] is True
    assert result.metadata["access_block_reason"] == "reddit_network_security_block"
    assert any("access_failed" in item for item in result.limitation_notes)
    assert "You've been blocked by network security" in result.visible_text


def test_fetch_cloakbrowser_snapshot_capture_marks_residual_cloudflare_challenge_without_access_failed() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://www.basenotes.com/fragrances/mojave-ghost-by-byredo.26143979/",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://www.basenotes.com/fragrances/mojave-ghost-by-byredo.26143979/",
                title="Mojave Ghost by Byredo",
                rendered_dom=(
                    "<html><body>Reviews 1 2 3 Basenotes source content"
                    "<script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script>"
                    "</body></html>"
                ),
                visible_text="Reviews 1 2 3 Basenotes source content",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.access_block_reason is None
    assert result.metadata["access_blocked"] is False
    assert result.metadata["rendered_access_classification"] == "residual_challenge_marker"
    assert result.metadata["rendered_access_signal"] == "residual_cloudflare_challenge_marker"
    assert any("rendered_access_warning" in item for item in result.limitation_notes)
    assert not any("access_failed" in item for item in result.limitation_notes)

def test_fetch_cloakbrowser_snapshot_capture_flags_amazon_continue_shopping_interstitial() -> None:
    # Amazon serves a low-content "Continue shopping" bot interstitial AT the PDP URL
    # (no redirect) with none of the product substrate. It must be classified
    # access_failed so the durability runner records an un-observed gap rather than a
    # fake observation (INV-1 / no-fake-success).
    pdp_url = "https://www.amazon.com/Laneige-Sleeping-Berry/dp/B07XXPHQZK"
    result = fetch_cloakbrowser_snapshot_capture(
        url=pdp_url,
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url=pdp_url,
                title="Amazon.com",
                rendered_dom=(
                    "<html><body><button>Continue shopping</button>"
                    "<p>Click the button below to continue shopping</p>"
                    "</body></html>"
                ),
                visible_text=(
                    "Click the button below to continue shopping\n"
                    "Continue shopping\n"
                    "Conditions of Use Privacy Policy\n"
                    "© 1996-2025, Amazon.com, Inc. or its affiliates"
                ),
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.final_url == pdp_url
    assert result.access_block_reason == "amazon_continue_shopping_interstitial"
    assert result.metadata["access_blocked"] is True
    assert result.metadata["access_block_reason"] == "amazon_continue_shopping_interstitial"
    assert any("access_failed" in item for item in result.limitation_notes)


def test_fetch_cloakbrowser_snapshot_capture_rejects_credential_bearing_final_url() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://user:pass@example.com/rendered",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.CAPTURE_FAILED
    assert "embedded credentials" in result.message
    assert "user:pass" not in result.message


def test_fetch_cloakbrowser_snapshot_capture_redacts_secret_like_final_url_query_values() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/rendered?token=secret-value&ok=1",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.final_url == "https://example.com/rendered?token=%5Bredacted%5D&ok=1"
    assert result.metadata["final_url"] == result.final_url
    assert "secret-value" not in json.dumps(result.metadata)
    assert "secret-value" not in "\n".join(result.warning_notes)


def test_fetch_cloakbrowser_snapshot_capture_redacts_secret_like_engine_warning_notes() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                warning_notes=["debug Authorization: Bearer secret-value", "safe warning"],
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    assert result.warning_notes == [
        "cloakbrowser_snapshot engine warning redacted because it contained secret-like text",
        "safe warning",
    ]
    assert "secret-value" not in "\n".join(result.warning_notes)


def test_fetch_cloakbrowser_snapshot_capture_redacts_proxy_endpoint_from_engine_failure_message() -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        proxy_profile=profile,
        engine=_FakeCloakBrowserEngine(
            RuntimeError(
                "proxy connection failed for "
                "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.CAPTURE_FAILED
    assert "SUPER_SECRET_PROXY_VALUE" not in result.message
    assert "proxy.example" not in result.message
    assert "[redacted-proxy-endpoint]" in result.message


def test_fetch_cloakbrowser_snapshot_capture_redacts_proxy_endpoint_from_dependency_failure_message() -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )
    dependency_error = cloakbrowser_snapshot_module._CloakBrowserSnapshotDependencyUnavailable(
        "CloakBrowser dependency unavailable: socksio missing while dialing "
        "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        proxy_profile=profile,
        engine=_FakeCloakBrowserEngine(dependency_error),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.DEPENDENCY_UNAVAILABLE
    assert "SUPER_SECRET_PROXY_VALUE" not in result.message
    assert "proxy.example" not in result.message


def test_fetch_cloakbrowser_snapshot_capture_redacts_proxy_endpoint_from_engine_warning_notes() -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )

    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        proxy_profile=profile,
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                warning_notes=[
                    "cloakbrowser_snapshot visible_text extraction failed: render context "
                    "bound to http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"
                ],
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotSuccess)
    joined = "\n".join(result.warning_notes)
    assert "SUPER_SECRET_PROXY_VALUE" not in joined
    assert "proxy.example" not in joined


def test_fetch_cloakbrowser_snapshot_capture_rejects_embedded_credentials_url() -> None:
    with pytest.raises(ValueError, match="embedded credentials"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://user:pass@example.com/source",
            engine=_FakeCloakBrowserEngine(
                _FakeEngineResult(
                    final_url="https://example.com/source",
                    title=None,
                    rendered_dom="<html><body>ok</body></html>",
                    visible_text="ok",
                    screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
                )
            ),
        )


def test_fetch_cloakbrowser_snapshot_capture_returns_size_cap_failure() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        max_artifact_bytes=5,
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"x" * 51,
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.SIZE_CAP_EXCEEDED
    assert "screenshot_png=51" in result.message


def test_fetch_cloakbrowser_snapshot_capture_classifies_timeout() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(TimeoutError("navigation timed out")),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.TIMEOUT


def test_fetch_cloakbrowser_snapshot_capture_returns_empty_rendered_dom_failure() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="",
                visible_text="text without dom",
                screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.EMPTY_RENDERED_DOM


def test_fetch_cloakbrowser_snapshot_capture_returns_empty_screenshot_failure() -> None:
    result = fetch_cloakbrowser_snapshot_capture(
        url="https://example.com/source",
        engine=_FakeCloakBrowserEngine(
            _FakeEngineResult(
                final_url="https://example.com/source",
                title=None,
                rendered_dom="<html><body>ok</body></html>",
                visible_text="ok",
                screenshot_png=b"",
            )
        ),
    )

    assert isinstance(result, CloakBrowserSnapshotFailure)
    assert result.failure_kind == CloakBrowserSnapshotFailureKind.EMPTY_SCREENSHOT


def test_cloakbrowser_snapshot_runner_writes_packet_with_four_artifacts(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        return CloakBrowserSnapshotSuccess(
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            title="Rendered Source",
            rendered_dom="<html><body><main>Visible source language</main></body></html>",
            visible_text="Visible source language",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={
                "requested_url": "https://example.com/source",
                "final_url": "https://example.com/source",
                "title": "Rendered Source",
                "capture_timestamp": "2026-06-06T01:02:03Z",
                "timeout_seconds": kwargs["timeout_seconds"],
                "wait_until": kwargs["wait_until"],
                "viewport_width": kwargs["viewport_width"],
                "viewport_height": kwargs["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "none",
                "storage_state_loaded": False,
                "proxy_used": False,
                "geoip_used": False,
                "extension_paths_loaded": False,
                "rendered_dom_byte_count": 64,
                "visible_text_byte_count": 23,
                "screenshot_byte_count": 20,
            },
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/source",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="What rendered source was visible before cutoff?",
        output_directory=output_dir,
        capture_context="test CloakBrowser snapshot",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=["operator-visible limitation travels"],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=5_000,
        block_heavy_assets=False,
    )

    assert exit_code == 0
    assert message == str(output_dir.resolve())
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_surface"] == "cloakbrowser_snapshot"
    assert manifest["capture_mode"] == "multimodal"
    assert manifest["source_slices"][0]["slice_id"] == "cloakbrowser_snapshot_01"
    assert manifest["source_slices"][0]["preserved_file_ids"] == [
        "file_01",
        "file_02",
        "file_03",
        "file_04",
    ]
    assert [item["relative_packet_path"] for item in manifest["preserved_files"]] == [
        "raw/01_cloakbrowser_rendered_dom.html",
        "raw/02_cloakbrowser_visible_text.txt",
        "raw/03_cloakbrowser_viewport_screenshot.png",
        "raw/04_cloakbrowser_snapshot_metadata.json",
    ]
    assert manifest["receipt_metadata"]["non_claims"] == CLOAKBROWSER_SNAPSHOT_NON_CLAIMS
    assert "operator-visible limitation travels" in manifest["limitations"]
    assert "anti-blocking browser capture" in manifest["access_posture"]["value"]
    metadata_text = (output_dir / "raw" / "04_cloakbrowser_snapshot_metadata.json").read_text(encoding="utf-8")
    assert "cloakbrowser" in metadata_text
    assert "Visible source language" in (output_dir / "raw" / "02_cloakbrowser_visible_text.txt").read_text(
        encoding="utf-8"
    )
    assert not (output_dir.parent / "cloakbrowser_rendered_dom.html").exists()
    assert not (output_dir.parent / "cloakbrowser_snapshot_metadata.json").exists()
    receipt_text = (output_dir / "receipt.md").read_text(encoding="utf-8")
    for non_claim in CLOAKBROWSER_SNAPSHOT_NON_CLAIMS:
        assert non_claim in receipt_text


def _fake_cloakbrowser_runner_success(**kwargs: object) -> CloakBrowserSnapshotSuccess:
    return CloakBrowserSnapshotSuccess(
        requested_url="https://example.com/source",
        final_url="https://example.com/source",
        title="Rendered Source",
        rendered_dom="<html><body><main>Visible source language</main></body></html>",
        visible_text="Visible source language",
        screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
        metadata={
            "requested_url": "https://example.com/source",
            "final_url": "https://example.com/source",
            "title": "Rendered Source",
            "capture_timestamp": "2026-06-06T01:02:03Z",
            "timeout_seconds": kwargs["timeout_seconds"],
            "wait_until": kwargs["wait_until"],
            "viewport_width": kwargs["viewport_width"],
            "viewport_height": kwargs["viewport_height"],
            "screenshot_mode": "viewport",
            "method_category": "anti_blocking_browser",
            "browser_engine": "cloakbrowser",
            "cloakbrowser_backend": "playwright",
            "profile_persistence": "none",
            "storage_state_loaded": False,
            "proxy_used": False,
            "geoip_used": False,
            "extension_paths_loaded": False,
            "rendered_dom_byte_count": 64,
            "visible_text_byte_count": 23,
            "screenshot_byte_count": 20,
        },
        warning_notes=[],
        limitation_notes=[],
    )


def test_cloakbrowser_snapshot_runner_writes_proxy_category_without_proxy_secret(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=True,
    )

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        assert kwargs["proxy_profile"] is profile
        return CloakBrowserSnapshotSuccess(
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            title="Rendered Source",
            rendered_dom="<html><body><main>Visible source language</main></body></html>",
            visible_text="Visible source language",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={
                "requested_url": "https://example.com/source",
                "final_url": "https://example.com/source",
                "title": "Rendered Source",
                "capture_timestamp": "2026-06-06T01:02:03Z",
                "timeout_seconds": kwargs["timeout_seconds"],
                "wait_until": kwargs["wait_until"],
                "viewport_width": kwargs["viewport_width"],
                "viewport_height": kwargs["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "none",
                "storage_state_loaded": False,
                "proxy_used": True,
                "proxy_category": "residential_static",
                "proxy_disclosure": "category_only",
                "proxy_endpoint_recorded": False,
                "proxy_exit_ip_recorded": False,
                "geoip_used": True,
                "extension_paths_loaded": False,
                "rendered_dom_byte_count": 64,
                "visible_text_byte_count": 23,
                "screenshot_byte_count": 20,
            },
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/source",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="What rendered source was visible before cutoff?",
        output_directory=output_dir,
        capture_context="test CloakBrowser proxied snapshot",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=profile,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=5_000,
        block_heavy_assets=False,
    )

    assert exit_code == 0
    assert message == str(output_dir.resolve())
    combined_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() not in {".png"}
    )
    assert "residential_static" in combined_text
    assert "not proxy endpoint or credential disclosure" in combined_text
    assert "SUPER_SECRET_PROXY_VALUE" not in combined_text
    assert "proxy.example" not in combined_text


def test_cloakbrowser_snapshot_runner_records_heavy_asset_blocking_limitation(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        assert kwargs["block_heavy_assets"] is True
        return CloakBrowserSnapshotSuccess(
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            title="Rendered Source",
            rendered_dom="<html><body><main>Visible source language</main></body></html>",
            visible_text="Visible source language",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={
                "requested_url": "https://example.com/source",
                "final_url": "https://example.com/source",
                "title": "Rendered Source",
                "capture_timestamp": "2026-06-06T01:02:03Z",
                "timeout_seconds": kwargs["timeout_seconds"],
                "wait_until": kwargs["wait_until"],
                "viewport_width": kwargs["viewport_width"],
                "viewport_height": kwargs["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "none",
                "storage_state_loaded": False,
                "proxy_used": False,
                "geoip_used": False,
                "extension_paths_loaded": False,
                "heavy_assets_blocked": True,
                "blocked_resource_types": ["font", "image", "media"],
                "rendered_dom_byte_count": 64,
                "visible_text_byte_count": 23,
                "screenshot_byte_count": 20,
            },
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/source",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="What rendered source was visible before cutoff?",
        output_directory=output_dir,
        capture_context="test CloakBrowser snapshot",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=5_000,
        block_heavy_assets=True,
    )

    assert exit_code == 0
    assert message == str(output_dir.resolve())
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert any("blocked image, media, and font" in item for item in manifest["limitations"])
    metadata = json.loads(
        (output_dir / "raw" / "04_cloakbrowser_snapshot_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["heavy_assets_blocked"] is True
    assert metadata["blocked_resource_types"] == ["font", "image", "media"]


def test_cloakbrowser_snapshot_runner_returns_3_without_packet_on_capture_failure(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fail_capture(**kwargs: object) -> CloakBrowserSnapshotFailure:
        return CloakBrowserSnapshotFailure(
            requested_url="https://example.com/source",
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="CloakBrowser failed visibly",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fail_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://example.com/source",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="What rendered source was visible before cutoff?",
        output_directory=output_dir,
        capture_context="test CloakBrowser snapshot",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
    )

    assert exit_code == 3
    assert message == "cloakbrowser_capture_failed: CloakBrowser failed visibly"
    assert not output_dir.exists()


def test_cloakbrowser_snapshot_cli_preflight_validates_without_capture(
    scratch_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_root = scratch_dir / "_proxy_profiles"
    profile_root.mkdir(parents=True)
    (profile_root / "reddit-res.json").write_text(
        json.dumps({"server": "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"}),
        encoding="utf-8",
    )
    (profile_root / "reddit-res.meta.json").write_text(
        json.dumps(
            {
                "profile_file": "reddit-res.json",
                "proxy_category": "residential_rotating",
                "geoip_enabled": True,
            }
        ),
        encoding="utf-8",
    )

    exit_code = cloakbrowser_runner.main(
        [
            "--url",
            "https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
            "--decision-question",
            "Can guarded launch preflight validate locally?",
            "--output",
            str(scratch_dir / "packet"),
            "--proxy-profile-label",
            "reddit-res",
            "--proxy-profile-category",
            "residential_rotating",
            "--proxy-profile-root",
            str(profile_root),
            "--guarded-reddit-launch",
            "--preflight-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "preflight passed" in captured.out
    assert "no network capture attempted" in captured.out
    assert "SUPER_SECRET_PROXY_VALUE" not in captured.out
    assert "proxy.example" not in captured.out
    assert not (scratch_dir / "packet").exists()


@pytest.mark.parametrize(
    ("profile", "url", "market_flag"),
    [
        (
            "sephora_grid_aggregate",
            "https://www.sephora.com/brand/summer-fridays?country_switch=us",
            "--sephora-market",
        ),
        (
            "ulta_grid_aggregate",
            "https://www.ulta.com/brand/clinique",
            "--ulta-market",
        ),
        (
            "ulta_category_grid_aggregate",
            "https://www.ulta.com/shop/makeup/all?sort=best_sellers",
            "--ulta-market",
        ),
    ],
)
def test_compact_grid_profiles_accept_explicit_content_retention_preflight(
    scratch_dir: Path,
    capsys: pytest.CaptureFixture[str],
    profile: str,
    url: str,
    market_flag: str,
) -> None:
    assert cloakbrowser_runner.main(
        [
            "--url",
            url,
            "--source-family",
            "retail_pdp",
            "--decision-question",
            "Can compact grid retention preflight validate locally?",
            "--output",
            str(scratch_dir / profile),
            "--retail-grid-projection-output",
            str(scratch_dir / f"{profile}.json"),
            "--retail-capture-profile",
            profile,
            market_flag,
            "US",
            "--retention-mode",
            "content",
            "--preflight-only",
        ]
    ) == 0
    assert "preflight passed" in capsys.readouterr().out


def test_cloakbrowser_snapshot_cli_preflight_rejects_proxy_with_browser_profile(
    scratch_dir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_root = scratch_dir / "_proxy_profiles"
    profile_root.mkdir(parents=True)
    (profile_root / "quora-res.json").write_text(
        json.dumps({"server": "http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080"}),
        encoding="utf-8",
    )
    (profile_root / "quora-res.meta.json").write_text(
        json.dumps(
            {
                "profile_file": "quora-res.json",
                "proxy_category": "residential_rotating",
                "geoip_enabled": True,
            }
        ),
        encoding="utf-8",
    )
    browser_profile = scratch_dir / "browser-profile"
    browser_profile.mkdir()
    monkeypatch.setattr(
        cloakbrowser_runner,
        "browser_user_data_path_for_label",
        lambda label: browser_profile,
    )

    with pytest.raises(SystemExit) as excinfo:
        cloakbrowser_runner.main(
            [
                "--url",
                "https://www.quora.com/search?q=B2B%20questions",
                "--decision-question",
                "Can profile-backed preflight validate locally?",
                "--output",
                str(scratch_dir / "packet"),
                "--proxy-profile-label",
                "quora-res",
                "--proxy-profile-category",
                "residential_rotating",
                "--proxy-profile-root",
                str(profile_root),
                "--browser-user-data-label",
                "quora-client",
                "--browser-user-data-session-mode",
                "client_provided_session",
                "--preflight-only",
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "--browser-user-data-label cannot be combined" in captured.err
    assert "does not apply proxy profiles" in captured.err
    assert "preflight passed" not in captured.out
    assert "SUPER_SECRET_PROXY_VALUE" not in captured.err
    assert "proxy.example" not in captured.err
    assert not (scratch_dir / "packet").exists()


def test_cloakbrowser_snapshot_cli_guarded_reddit_rejects_non_old_reddit_url(
    scratch_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cloakbrowser_runner.main(
            [
                "--url",
                "https://www.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
                "--decision-question",
                "Can guarded launch reject non-old Reddit locally?",
                "--output",
                str(scratch_dir / "packet"),
                "--guarded-reddit-launch",
                "--preflight-only",
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "requires an absolute old.reddit.com URL" in captured.err
    assert not (scratch_dir / "packet").exists()


def test_cloakbrowser_snapshot_runner_writes_access_blocked_packet(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        return CloakBrowserSnapshotSuccess(
            requested_url="https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
            final_url="https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
            title="",
            rendered_dom=(
                "<html><body>You've been blocked by network security. "
                "If you think you've been blocked by mistake, file a ticket below."
                "</body></html>"
            ),
            visible_text=(
                "You've been blocked by network security. If you think you've been blocked "
                "by mistake, file a ticket below and we'll look into it. File a ticket"
            ),
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={
                "requested_url": "https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
                "final_url": "https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
                "title": "",
                "capture_timestamp": "2026-06-06T01:02:03Z",
                "timeout_seconds": kwargs["timeout_seconds"],
                "wait_until": kwargs["wait_until"],
                "viewport_width": kwargs["viewport_width"],
                "viewport_height": kwargs["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "none",
                "storage_state_loaded": False,
                "proxy_used": False,
                "geoip_used": False,
                "extension_paths_loaded": False,
                "access_blocked": True,
                "access_block_reason": "reddit_network_security_block",
                "rendered_dom_byte_count": 146,
                "visible_text_byte_count": 116,
                "screenshot_byte_count": 20,
            },
            warning_notes=[],
            limitation_notes=[
                "access_failed: CloakBrowser rendered an access-block/interstitial page "
                "instead of source content: reddit_network_security_block; block artifacts preserved"
            ],
            access_block_reason="reddit_network_security_block",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://old.reddit.com/r/SaaS/comments/1es61lz/why_is_b2b_so_much_better/",
        source_family="reddit_thread",
        source_surface="old_reddit_cloakbrowser_snapshot",
        decision_question="What rendered Reddit thread was visible?",
        output_directory=output_dir,
        capture_context="test CloakBrowser Reddit snapshot",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
    )

    assert exit_code == 0
    assert message == str(output_dir.resolve())
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["access_posture"]["value"].startswith(
        "cloakbrowser_snapshot access_failed with access block reddit_network_security_block"
    )
    assert any("access_failed" in item for item in manifest["limitations"])
    assert "source content was not captured" in manifest["receipt_metadata"]["summary"]
    metadata = json.loads(
        (output_dir / "raw" / "04_cloakbrowser_snapshot_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["access_blocked"] is True
    assert metadata["access_block_reason"] == "reddit_network_security_block"
    visible_text = (output_dir / "raw" / "02_cloakbrowser_visible_text.txt").read_text(
        encoding="utf-8"
    )
    assert "You've been blocked by network security" in visible_text
    non_claims = manifest["receipt_metadata"]["non_claims"]
    assert any("not source-content capture" in item for item in non_claims)


def test_cloakbrowser_snapshot_runner_cleans_staged_files_when_metadata_write_fails(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        return CloakBrowserSnapshotSuccess(
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            title="Rendered Source",
            rendered_dom="<html><body>ok</body></html>",
            visible_text="ok",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={"bad": object()},
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    with pytest.raises(TypeError):
        cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
            url="https://example.com/source",
            source_family="web_page",
            source_surface="cloakbrowser_snapshot",
            decision_question="What rendered source was visible before cutoff?",
            output_directory=output_dir,
            capture_context="test CloakBrowser snapshot",
            operator_category="cloakbrowser_snapshot_cli_operator",
            capture_mode=CaptureModeCategory.MULTIMODAL,
            session_id=None,
            proxy_profile=None,
            actor_audience_context=None,
            visible_mode_changes=[],
            source_publication_or_event=None,
            source_edit_or_version=None,
            cutoff_posture=None,
            recapture_time=None,
            re_capture_relationship=None,
            warnings=[],
            limitations=[],
            timeout_seconds=30,
            wait_until="load",
            viewport_width=1280,
            viewport_height=720,
            max_artifact_bytes=50_000,
            block_heavy_assets=False,
        )

    assert not output_dir.exists()
    assert not (output_dir.parent / "cloakbrowser_rendered_dom.html").exists()
    assert not (output_dir.parent / "cloakbrowser_visible_text.txt").exists()
    assert not (output_dir.parent / "cloakbrowser_viewport_screenshot.png").exists()
    assert not (output_dir.parent / "cloakbrowser_snapshot_metadata.json").exists()


def test_cloakbrowser_snapshot_runner_fail_closes_source_detail_sufficiency_after_packet_write(
    scratch_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = scratch_dir / "packet"

    def fake_capture(**kwargs: object) -> CloakBrowserSnapshotSuccess:
        return CloakBrowserSnapshotSuccess(
            requested_url="https://www.quora.com/search?q=B2B%20questions",
            final_url="https://www.quora.com/search?q=B2B%20questions",
            title="Just a moment...",
            rendered_dom="<html><script>window.__cf_chl_tk = 'token'</script></html>",
            visible_text="",
            screenshot_png=b"\x89PNG\r\n\x1a\ncloakbrowser",
            metadata={
                "requested_url": "https://www.quora.com/search?q=B2B%20questions",
                "final_url": "https://www.quora.com/search?q=B2B%20questions",
                "title": "Just a moment...",
                "capture_timestamp": "2026-07-09T01:02:03Z",
                "timeout_seconds": kwargs["timeout_seconds"],
                "wait_until": kwargs["wait_until"],
                "viewport_width": kwargs["viewport_width"],
                "viewport_height": kwargs["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "local_ignored_profile",
                "persistent_profile_loaded": True,
                "storage_state_loaded": False,
                "access_blocked": True,
                "access_block_reason": "cloudflare_interstitial",
                "rendered_dom_byte_count": 64,
                "visible_text_byte_count": 0,
                "screenshot_byte_count": 20,
            },
            warning_notes=[],
            limitation_notes=[
                "access_failed: CloakBrowser rendered an access-block/interstitial page instead of source content: cloudflare_interstitial; block artifacts preserved"
            ],
            access_block_reason="cloudflare_interstitial",
        )

    monkeypatch.setattr(cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture)

    exit_code, message = cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
        url="https://www.quora.com/search?q=B2B%20questions",
        source_family="web_page",
        source_surface="cloakbrowser_snapshot",
        decision_question="Can Quora search provide B2B question candidates?",
        output_directory=output_dir,
        capture_context="test CloakBrowser sufficiency gate",
        operator_category="cloakbrowser_snapshot_cli_operator",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        browser_user_data_label="quora-client",
        browser_user_data_session_mode=None,
        browser_user_data_dir=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        source_detail_sufficiency_requirements=SourceDetailSufficiencyRequirements(
            require_not_access_blocked=True,
            min_visible_text_bytes=100,
            visible_text_contains=("Results for B2B questions",),
        ),
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=50_000,
        block_heavy_assets=False,
    )

    assert exit_code == SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE
    assert str(output_dir.resolve()) in message
    assert output_dir.exists()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "source_detail_sufficiency_failed" in manifest["visible_mode_changes"]
    assert any("source_detail_sufficiency_failed" in item for item in manifest["limitations"])
    assert any("not source-content capture" in item for item in manifest["receipt_metadata"]["non_claims"])


def test_fetch_cloakbrowser_snapshot_capture_rejects_combining_user_data_dir_and_proxy_profile(
    scratch_dir: Path,
) -> None:
    profile = ProxyProfile(
        proxy_endpoint="http://user:SUPER_SECRET_PROXY_VALUE@proxy.example:8080",
        proxy_category=ProxyCategory.RESIDENTIAL_STATIC,
        geoip_enabled=False,
    )

    with pytest.raises(ValueError, match="does not apply proxy_profile"):
        fetch_cloakbrowser_snapshot_capture(
            url="https://example.com/source",
            proxy_profile=profile,
            user_data_dir=scratch_dir,
        )


def test_cloakbrowser_runner_rejects_user_data_dir_without_label_and_session_mode(
    scratch_dir: Path,
) -> None:
    output_dir = scratch_dir / "packet"

    with pytest.raises(
        ValueError, match="browser_user_data_dir requires browser_user_data_label"
    ):
        cloakbrowser_runner.run_source_capture_cloakbrowser_packet(
            url="https://www.quora.com/search?q=B2B%20questions",
            source_family="web_page",
            source_surface="cloakbrowser_snapshot",
            decision_question="Can Quora search provide B2B question candidates?",
            output_directory=output_dir,
            capture_context="test provenance guard",
            operator_category="cloakbrowser_snapshot_cli_operator",
            capture_mode=CaptureModeCategory.MULTIMODAL,
            session_id=None,
            proxy_profile=None,
            browser_user_data_label=None,
            browser_user_data_session_mode=None,
            browser_user_data_dir=scratch_dir,
            actor_audience_context=None,
            visible_mode_changes=[],
            source_publication_or_event=None,
            source_edit_or_version=None,
            cutoff_posture=None,
            recapture_time=None,
            re_capture_relationship=None,
            warnings=[],
            limitations=[],
            timeout_seconds=20,
            wait_until="load",
            viewport_width=1280,
            viewport_height=720,
            max_artifact_bytes=50_000,
            block_heavy_assets=False,
        )
