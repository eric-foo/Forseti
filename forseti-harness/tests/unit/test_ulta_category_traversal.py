from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from runners import run_source_capture_cloakbrowser_packet as cloak_writer
from source_capture.adapters.cloakbrowser_snapshot import (
    CloakBrowserSnapshotFailure,
    CloakBrowserSnapshotFailureKind,
)
from source_capture.adapters.ulta_category_traversal import (
    UltaCategoryTraversalPlugin,
)
from source_capture.retail_capture_profiles import get_retail_capture_profile
from source_capture.ulta_category_grid import (
    ULTA_CATEGORY_MAX_WINDOW,
    build_ulta_category_grid_aggregate_content_record,
)


_URL = "https://www.ulta.com/shop/makeup/all?sort=best_sellers"


def _card(local_position: int, page: int) -> str:
    product_number = (page - 1) * 64 + local_position
    return (
        f'<li data-test="products-list-item" data-sku-id="{product_number}">'
        f'<a href="/p/product-{product_number}-pimprod{product_number:06d}">'
        '<span class="pal-c-ProductCardBody--brandName">Rare Beauty</span>'
        f'<span class="pal-c-ProductCardBody--title">Product {product_number}</span>'
        '<span class="pal-c-ProductCardBody--price">$25.00</span>'
        "</a></li>"
    )


def _page_dom(
    page: int,
    *,
    declared_count: int,
    card_count: int = 64,
    selected_sort_id: str = "best_sellers",
    conflicting_sort_id: str | None = None,
) -> str:
    conflicting_sort = (
        f'<span data-testid="dropdown__header__value" id="{conflicting_sort_id}">'
        "Other Sort</span>"
        if conflicting_sort_id is not None
        else ""
    )
    return (
        '<html lang="en-US"><head><script>window.__APP_LOCALE__="en-US";'
        + 'fetch("/graphql?ultasite=en-us")</script></head><body>'
        + "<h1>Makeup</h1>"
        + f'<span data-testid="dropdown__header__value" id="{selected_sort_id}">'
        + "Best Sellers</span>"
        + conflicting_sort
        + '<ul data-test="products-list">'
        + "".join(_card(index, page) for index in range(1, card_count + 1))
        + "</ul>"
        + f"<p>You have viewed {card_count} of {declared_count}</p>"
        + "</body></html>"
    )


class _FakePage:
    def __init__(self, pages: dict[int, str]) -> None:
        self._pages = pages
        self._page = 1
        self.url = _URL
        self.visited: list[str] = []

    def goto(self, url: str, **_kwargs: object) -> None:
        self.url = url
        self.visited.append(url)
        self._page = int(parse_qs(urlparse(url).query)["page"][0])

    def wait_for_timeout(self, _milliseconds: float) -> None:
        return None

    def evaluate(self, _script: str) -> None:
        return None

    def content(self) -> str:
        return self._pages[self._page]


def test_traversal_captures_deterministic_top_quartile_capped_at_720() -> None:
    page = _FakePage(
        {index: _page_dom(index, declared_count=3_000) for index in range(1, 13)}
    )
    plugin = UltaCategoryTraversalPlugin(
        target_url=_URL,
        traversal_timeout_seconds=30,
    )

    outcome = plugin.before_snapshot(page, setup_timeout_ms=30_000)

    assert outcome.steps_completed is True
    assert len(page.visited) == 12
    assert all(
        parse_qs(urlparse(url).query)["sort"] == ["best_sellers"]
        for url in page.visited
    )
    record = build_ulta_category_grid_aggregate_content_record(
        rendered_pages=plugin.grid_page_doms,
        requested_url=_URL,
        page_urls=plugin.grid_page_urls,
        traversal_observation=plugin.grid_observation,
    )
    assert record["requested_window_count"] == ULTA_CATEGORY_MAX_WINDOW
    assert record["requested_page_count"] == 12
    assert record["captured_page_count"] == 12
    assert len(record["cards"]) == 720
    assert record["cards"][0]["grid_position"] == 1
    assert record["cards"][-1]["grid_position"] == 720
    assert record["traversal_termination"] == "requested_page_window_reconciled"
    assert plugin.confirm("").confirmed is True


def test_traversal_uses_one_page_for_small_top_quartile_and_truncates_record() -> None:
    page = _FakePage({1: _page_dom(1, declared_count=100)})
    plugin = UltaCategoryTraversalPlugin(target_url=_URL)

    outcome = plugin.before_snapshot(page, setup_timeout_ms=30_000)
    record = build_ulta_category_grid_aggregate_content_record(
        rendered_pages=plugin.grid_page_doms,
        requested_url=_URL,
        page_urls=plugin.grid_page_urls,
        traversal_observation=plugin.grid_observation,
    )

    assert outcome.steps_completed is True
    assert len(page.visited) == 1
    assert record["requested_window_count"] == 25
    assert len(record["cards"]) == 25
    assert record["cards"][-1]["grid_position"] == 25


def test_traversal_fails_when_a_page_is_short_before_requested_window() -> None:
    pages = {
        1: _page_dom(1, declared_count=3_000),
        2: _page_dom(2, declared_count=3_000, card_count=10),
    }
    page = _FakePage(pages)
    plugin = UltaCategoryTraversalPlugin(target_url=_URL)

    outcome = plugin.before_snapshot(page, setup_timeout_ms=30_000)

    assert outcome.steps_completed is False
    assert "returned 10 cards" in str(outcome.reason)
    assert plugin.grid_observation["termination"] == "unproven"
    assert plugin.confirm("").confirmed is False


def test_traversal_fails_when_bestseller_sort_disappears_on_later_page() -> None:
    pages = {
        1: _page_dom(1, declared_count=600),
        2: _page_dom(2, declared_count=600, selected_sort_id="top_rated"),
    }
    page = _FakePage(pages)
    plugin = UltaCategoryTraversalPlugin(target_url=_URL)

    outcome = plugin.before_snapshot(page, setup_timeout_ms=30_000)

    assert outcome.steps_completed is False
    assert "did not retain best_sellers sort" in str(outcome.reason)


def test_traversal_rejects_conflicting_rendered_sort_ids() -> None:
    page = _FakePage(
        {
            1: _page_dom(
                1,
                declared_count=100,
                conflicting_sort_id="top_rated",
            )
        }
    )
    plugin = UltaCategoryTraversalPlugin(target_url=_URL)

    outcome = plugin.before_snapshot(page, setup_timeout_ms=30_000)

    assert outcome.steps_completed is False
    assert "did not retain best_sellers sort" in str(outcome.reason)


def test_runner_selects_category_traversal_and_disables_generic_load_more(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: dict[str, Any] = {}

    def fake_capture(**kwargs: Any) -> CloakBrowserSnapshotFailure:
        observed.update(kwargs)
        return CloakBrowserSnapshotFailure(
            requested_url=kwargs["url"],
            failure_kind=CloakBrowserSnapshotFailureKind.CAPTURE_FAILED,
            message="expected test stop",
        )

    monkeypatch.setattr(
        cloak_writer,
        "fetch_cloakbrowser_snapshot_capture",
        fake_capture,
    )
    exit_code, _message = cloak_writer.run_source_capture_cloakbrowser_packet(
        url=_URL,
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        decision_question="Can Ulta category pagination remain deterministic?",
        output_directory=tmp_path / "packet",
        capture_context="offline test",
        operator_category="test",
        capture_mode=cloak_writer.CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=cloak_writer.unknown_with_reason("not needed"),
        visible_mode_changes=[],
        source_publication_or_event=cloak_writer.unknown_with_reason("not needed"),
        source_edit_or_version=cloak_writer.unknown_with_reason("not needed"),
        cutoff_posture=cloak_writer.unknown_with_reason("not needed"),
        recapture_time=cloak_writer.not_applicable("not needed"),
        re_capture_relationship=cloak_writer.not_applicable("not needed"),
        warnings=[],
        limitations=[],
        retail_capture_profile=get_retail_capture_profile(
            "ulta_category_grid_aggregate"
        ),
        timeout_seconds=30,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=5_000_000,
        block_heavy_assets=False,
        settle_seconds=5,
        scroll_passes=1,
        load_more_selector="button.LoadContent__button",
        load_more_clicks=11,
        ulta_market="US",
        retail_grid_projection_output=tmp_path / "projection.json",
    )

    assert exit_code != 0
    assert isinstance(observed["pre_capture"], UltaCategoryTraversalPlugin)
    assert observed["wait_until"] == "load"
    assert observed["settle_seconds"] == 0
    assert observed["scroll_passes"] == 0
    assert observed["load_more_selector"] is None
    assert observed["load_more_clicks"] == 0
