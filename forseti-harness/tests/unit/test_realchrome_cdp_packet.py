from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners.run_source_capture_realchrome_cdp_packet import (
    RealChromeCDPCaptureResult,
    _navigate_target,
    _select_or_create_page,
    run_source_capture_realchrome_cdp_packet,
)
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
    SourceDetailSufficiencyRequirements,
)

PDP_URL = "https://www.kohls.com/product/prd-6715879/tower-28-beauty-lipsoftie.jsp"

_CONTENT_DOM = (
    '<html><head><title>Tower 28 LipSoftie</title></head><body>'
    'Tower 28 Beauty LipSoftie $16.00 '
    '<div itemscope itemtype="http://schema.org/Offer">'
    '<meta itemprop="price" content="16"><meta itemprop="priceCurrency" content="USD"></div>'
    '</body></html>'
)
_CONTENT_TEXT = "Tower 28 Beauty LipSoftie Hydrating Tinted Lip Treatment Balm $16.00 " + ("x" * 1200)
_BLOCK_DOM = "<html><head><title>Access Denied</title></head><body>Access Denied Reference #1 errors.edgesuite.net</body></html>"
_BLOCK_TEXT = "Access Denied\nYou don't have permission to access this server.\nerrors.edgesuite.net"


class _FakeEngine:
    def __init__(self, *, dom: str, text: str, status: int, title: str) -> None:
        self._dom, self._text, self._status, self._title = dom, text, status, title
        self.calls: list[dict] = []

    def capture(self, **kwargs) -> RealChromeCDPCaptureResult:
        self.calls.append(kwargs)
        return RealChromeCDPCaptureResult(
            requested_url=kwargs["url"],
            final_url=kwargs["url"],
            title=self._title,
            rendered_dom=self._dom,
            visible_text=self._text,
            screenshot_png=b"\x89PNG\r\n\x1a\n_fake_png_bytes",
            http_status=self._status,
            warm_hop_url=kwargs.get("warm_hop_url"),
            warm_hop_blocked=True if kwargs.get("warm_hop_url") else None,
            warning_notes=[],
        )


def _read_manifest(out: Path) -> dict:
    return json.loads((out / "manifest.json").read_text(encoding="utf-8"))


def test_content_capture_writes_packet_and_passes(tmp_path: Path) -> None:
    engine = _FakeEngine(dom=_CONTENT_DOM, text=_CONTENT_TEXT, status=200, title="Tower 28 LipSoftie")
    out = tmp_path / "pkt"
    code, path = run_source_capture_realchrome_cdp_packet(
        url=PDP_URL,
        source_family="retail_pdp",
        source_surface="realchrome_cdp_snapshot",
        decision_question="q",
        output_directory=out,
        warm_hop_url="https://www.kohls.com/",
        source_detail_sufficiency_requirements=SourceDetailSufficiencyRequirements(
            require_not_access_blocked=True,
            visible_text_contains=("LipSoftie",),
            rendered_dom_regexes=(r'priceCurrency"\s+content="USD"',),
        ),
        engine=engine,
    )
    assert code == 0
    assert Path(path).resolve() == out.resolve()
    m = _read_manifest(out)
    assert m["source_surface"] == "realchrome_cdp_snapshot"
    assert m["source_family"] == "retail_pdp"
    # honest method provenance + no proxy/secret leakage
    meta_file = next(out.glob("raw/*metadata.json"))
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["browser_engine"] == "chrome_real_via_cdp"
    assert meta["proxy_used"] is False
    assert meta["access_blocked"] is False
    assert meta["http_response_status"] == 200
    assert meta["warm_hop_url"] == "https://www.kohls.com/"
    # engine received the warm hop
    assert engine.calls[0]["warm_hop_url"] == "https://www.kohls.com/"


def test_unattended_provisioning_is_preserved_truthfully(tmp_path: Path) -> None:
    engine = _FakeEngine(dom=_CONTENT_DOM, text=_CONTENT_TEXT, status=200, title="Tower 28 LipSoftie")
    out = tmp_path / "pkt"
    code, _ = run_source_capture_realchrome_cdp_packet(
        url=PDP_URL,
        source_family="retail_pdp",
        source_surface="realchrome_cdp_snapshot",
        decision_question="q",
        output_directory=out,
        browser_provisioning="unattended_xvfb",
        persistent_profile_loaded=True,
        engine=engine,
    )

    assert code == 0
    manifest = _read_manifest(out)
    metadata_file = next(out.glob("raw/*metadata.json"))
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert metadata["browser_provisioning"] == "unattended_xvfb"
    assert metadata["persistent_profile_loaded"] is True
    assert "unattended_real_browser_cdp" == manifest["operator_category"]
    assert "unattended_xvfb_realchrome_cdp" in manifest["visible_mode_changes"]


def test_block_is_preserved_and_fails_closed(tmp_path: Path) -> None:
    engine = _FakeEngine(dom=_BLOCK_DOM, text=_BLOCK_TEXT, status=403, title="Access Denied")
    out = tmp_path / "pkt"
    code, path = run_source_capture_realchrome_cdp_packet(
        url=PDP_URL,
        source_family="retail_pdp",
        source_surface="realchrome_cdp_snapshot",
        decision_question="q",
        output_directory=out,
        source_detail_sufficiency_requirements=SourceDetailSufficiencyRequirements(
            require_not_access_blocked=True
        ),
        engine=engine,
    )
    # packet still written to the output dir, but command fails closed on the access block
    assert code == SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE
    assert "source_detail_sufficiency_failed" in path
    m = _read_manifest(out)
    assert m["source_surface"] == "realchrome_cdp_snapshot"
    meta_file = next(out.glob("raw/*metadata.json"))
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["access_blocked"] is True
    assert meta["access_block_reason"]


def test_requires_exactly_one_output_target(tmp_path: Path) -> None:
    engine = _FakeEngine(dom=_CONTENT_DOM, text=_CONTENT_TEXT, status=200, title="t")
    with pytest.raises(ValueError):
        run_source_capture_realchrome_cdp_packet(
            url=PDP_URL,
            source_family="retail_pdp",
            source_surface="realchrome_cdp_snapshot",
            decision_question="q",
            output_directory=None,
            data_root=None,
            engine=engine,
        )


def test_persistent_tab_options_are_preserved_and_forwarded(tmp_path: Path) -> None:
    engine = _FakeEngine(dom=_CONTENT_DOM, text=_CONTENT_TEXT, status=200, title="t")
    out = tmp_path / "pkt"
    code, _ = run_source_capture_realchrome_cdp_packet(
        url="https://www.google.com/search?q=tower+28",
        source_family="search_discovery",
        source_surface="google_serp_us_parameterized_realchrome_cdp",
        decision_question="q",
        output_directory=out,
        persistent_tab_marker="forseti.queue.test",
        fit_viewport_to_window=True,
        visible_mode_changes=("block_route:persistent_realchrome",),
        engine=engine,
    )

    assert code == 0
    assert engine.calls[0]["persistent_tab_marker"] == "forseti.queue.test"
    assert engine.calls[0]["fit_viewport_to_window"] is True
    metadata_file = next(out.glob("raw/*metadata.json"))
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert metadata["persistent_tab"] is True
    assert metadata["persistent_tab_marker"] == "forseti.queue.test"
    manifest = _read_manifest(out)
    assert "persistent_operator_visible_tab" in manifest["visible_mode_changes"]
    assert "window_fitted_viewport" in manifest["visible_mode_changes"]
    assert "block_route:persistent_realchrome" in manifest["visible_mode_changes"]


def test_target_navigation_restores_marker_after_document_swap() -> None:
    class _NavigationPage:
        def __init__(self) -> None:
            self.marker = "forseti.queue"

        def goto(self, url, *, wait_until, timeout):
            assert url == "https://www.google.com/search?q=new"
            assert wait_until == "load"
            assert timeout == 10_000
            self.marker = ""
            return "response"

        def evaluate(self, script, argument=None):
            assert script == "(marker) => { window.name = marker; }"
            self.marker = argument

    page = _NavigationPage()
    response = _navigate_target(
        page=page,
        url="https://www.google.com/search?q=new",
        timeout_ms=10_000,
        persistent_tab_marker="forseti.queue",
    )

    assert response == "response"
    assert page.marker == "forseti.queue"


class _FakePage:
    def __init__(self, *, url: str, marker: str = "") -> None:
        self.url = url
        self.marker = marker

    def is_closed(self) -> bool:
        return False

    def evaluate(self, script: str, argument=None):
        if script == "() => window.name":
            return self.marker
        if "window.name = marker" in script:
            self.marker = argument
            return None
        raise AssertionError(script)


class _FakeContext:
    def __init__(self, pages: list[_FakePage]) -> None:
        self.pages = pages
        self.created = 0

    def new_page(self) -> _FakePage:
        self.created += 1
        page = _FakePage(url="about:blank")
        self.pages.append(page)
        return page


def test_persistent_google_route_reuses_marked_tab() -> None:
    marked = _FakePage(
        url="https://www.google.com/search?q=old", marker="forseti.queue"
    )
    unrelated = _FakePage(url="https://example.com/")
    context = _FakeContext([unrelated, marked])

    page, close_after = _select_or_create_page(
        context=context,
        target_url="https://www.google.com/search?q=new",
        persistent_tab_marker="forseti.queue",
    )

    assert page is marked
    assert close_after is False
    assert context.created == 0


def test_persistent_google_route_adopts_only_unique_search_tab() -> None:
    search = _FakePage(url="https://www.google.com/search?q=old")
    context = _FakeContext([_FakePage(url="https://example.com/"), search])

    page, close_after = _select_or_create_page(
        context=context,
        target_url="https://www.google.com/search?q=new",
        persistent_tab_marker="forseti.queue",
    )

    assert page is search
    assert page.marker == "forseti.queue"
    assert close_after is False
    assert context.created == 0


def test_persistent_google_route_never_hijacks_an_ambiguous_search_tab() -> None:
    """Two unmarked Google tabs are ambiguous: open our own, adopt neither.

    This is the half of "adopts ONLY a unique search tab" that the uniqueness
    guard exists for. Without it the runner seizes whichever operator tab
    happens to sort first and navigates it away mid-session.
    """
    first = _FakePage(url="https://www.google.com/search?q=operator")
    second = _FakePage(url="https://www.google.com/search?q=other")
    context = _FakeContext([first, second])

    page, close_after = _select_or_create_page(
        context=context,
        target_url="https://www.google.com/search?q=new",
        persistent_tab_marker="forseti.queue",
    )

    assert context.created == 1
    assert page is not first and page is not second
    assert page.marker == "forseti.queue"
    assert close_after is False
    # Neither operator tab was claimed or renamed.
    assert first.marker == ""
    assert second.marker == ""
