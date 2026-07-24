"""Bounded, fail-closed traversal of Ulta category bestseller pages."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from math import ceil
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from source_capture.adapters.cloakbrowser_snapshot import (
    PinConfirmation,
    PreCaptureOutcome,
)
from source_capture.adapters.ulta_us_market import (
    UltaUSMarketPlugin,
    confirm_ulta_us_market,
)
from source_capture.ulta_brand_grid import load_ulta_brand_grid_state
from source_capture.ulta_category_grid import (
    ULTA_CATEGORY_PAGE_SIZE,
    requested_ulta_category_window,
)


@dataclass
class UltaCategoryTraversalPlugin:
    """Capture the commissioned top-quartile window through ``?page=N`` URLs."""

    target_url: str
    traversal_timeout_seconds: float = 90.0
    _grid_page_doms: list[str] = field(default_factory=list, init=False, repr=False)
    _grid_page_urls: list[str] = field(default_factory=list, init=False, repr=False)
    _grid_observation: dict[str, object] = field(
        default_factory=dict, init=False, repr=False
    )
    _traversal_completed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        parsed = urlparse(self.target_url)
        parts = [part for part in parsed.path.split("/") if part]
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if (
            parsed.scheme != "https"
            or (parsed.hostname or "").lower() not in {"ulta.com", "www.ulta.com"}
            or len(parts) != 3
            or parts[0].lower() != "shop"
            or parts[2].lower() != "all"
        ):
            raise ValueError(
                "Ulta category traversal requires an HTTPS /shop/<category>/all URL"
            )
        if query.get("sort") != "best_sellers":
            raise ValueError(
                "Ulta category traversal requires source-native sort=best_sellers"
            )
        if self.traversal_timeout_seconds <= 0:
            raise ValueError("Ulta category traversal timeout must be positive")

    @property
    def humanize(self) -> bool:
        return False

    @property
    def grid_page_doms(self) -> tuple[str, ...]:
        return tuple(self._grid_page_doms)

    @property
    def grid_page_urls(self) -> tuple[str, ...]:
        return tuple(self._grid_page_urls)

    @property
    def grid_observation(self) -> dict[str, object]:
        return dict(self._grid_observation)

    def before(self, page: object, *, setup_timeout_ms: float) -> PreCaptureOutcome:
        return UltaUSMarketPlugin(
            target_url=self.target_url,
            country_code="US",
            page_kind="grid",
        ).before(page, setup_timeout_ms=setup_timeout_ms)

    def before_snapshot(
        self, page: object, *, setup_timeout_ms: float
    ) -> PreCaptureOutcome:
        deadline = time.monotonic() + self.traversal_timeout_seconds
        page_observations: list[dict[str, object]] = []
        declared_count: int | None = None
        requested_window_count: int | None = None
        requested_page_count: int | None = None
        category_name: str | None = None
        try:
            expected_page = 1
            while requested_page_count is None or expected_page <= requested_page_count:
                requested_page_url = _category_page_url(
                    self.target_url, page=expected_page
                )
                page.goto(  # type: ignore[union-attr]
                    requested_page_url,
                    wait_until="domcontentloaded",
                    timeout=_remaining_ms(deadline),
                )
                page.wait_for_timeout(  # type: ignore[union-attr]
                    min(1_000, int(setup_timeout_ms), _remaining_ms(deadline))
                )
                if not _matches_requested_page(
                    str(page.url), requested_page_url, expected_page  # type: ignore[union-attr]
                ):
                    return self._failed(
                        f"page {expected_page} navigation did not retain its "
                        "category path, page number, and bestseller sort",
                        page_observations,
                    )
                page.evaluate(  # type: ignore[union-attr]
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
                page.wait_for_timeout(  # type: ignore[union-attr]
                    min(1_000, int(setup_timeout_ms), _remaining_ms(deadline))
                )
                rendered_dom = page.content()  # type: ignore[union-attr]
                state = load_ulta_brand_grid_state(rendered_dom)
                if state is None:
                    return self._failed(
                        f"page {expected_page} omitted rendered grid state",
                        page_observations,
                    )
                if state.selected_sort_id != "best_sellers":
                    return self._failed(
                        f"page {expected_page} did not retain best_sellers sort",
                        page_observations,
                    )
                if declared_count is None:
                    if state.declared_count is None or state.declared_count < 1:
                        return self._failed(
                            "page 1 omitted a positive declared result count",
                            page_observations,
                        )
                    declared_count = state.declared_count
                    requested_window_count = requested_ulta_category_window(
                        declared_count
                    )
                    requested_page_count = ceil(
                        requested_window_count / ULTA_CATEGORY_PAGE_SIZE
                    )
                    category_name = state.brand_name
                elif state.declared_count != declared_count:
                    return self._failed(
                        f"declared result count changed on page {expected_page}",
                        page_observations,
                    )
                if state.brand_name != category_name:
                    return self._failed(
                        f"category heading changed on page {expected_page}",
                        page_observations,
                    )
                local_positions = [card.grid_position for card in state.cards]
                if local_positions != list(range(1, len(state.cards) + 1)):
                    return self._failed(
                        f"page {expected_page} local ranks were not contiguous",
                        page_observations,
                    )
                assert requested_window_count is not None
                remaining = requested_window_count - (
                    (expected_page - 1) * ULTA_CATEGORY_PAGE_SIZE
                )
                required_on_page = min(ULTA_CATEGORY_PAGE_SIZE, remaining)
                if len(state.cards) < required_on_page:
                    return self._failed(
                        f"page {expected_page} returned {len(state.cards)} cards "
                        f"before the requested window required {required_on_page}",
                        page_observations,
                    )
                self._grid_page_doms.append(rendered_dom)
                self._grid_page_urls.append(requested_page_url)
                page_observations.append(
                    {
                        "page": expected_page,
                        "productCount": len(state.cards),
                        "retainedCount": required_on_page,
                        "selectedSortId": state.selected_sort_id,
                        "finalUrl": str(page.url),  # type: ignore[union-attr]
                    }
                )
                expected_page += 1
        except Exception as exc:
            return self._failed(
                f"traversal failed ({type(exc).__name__}: {exc})",
                page_observations,
            )

        assert declared_count is not None
        assert requested_window_count is not None
        assert requested_page_count is not None
        termination = (
            "retailer_terminal_reconciled"
            if requested_window_count >= declared_count
            else "requested_page_window_reconciled"
        )
        self._traversal_completed = True
        self._grid_observation = {
            "pageSize": ULTA_CATEGORY_PAGE_SIZE,
            "declaredResultCount": declared_count,
            "requestedWindowCount": requested_window_count,
            "requestedPageCount": requested_page_count,
            "capturedPageCount": len(self._grid_page_doms),
            "pageObservations": page_observations,
            "termination": termination,
        }
        return _outcome()

    def confirm(self, rendered_dom: str) -> PinConfirmation:
        del rendered_dom
        confirmed = self._traversal_completed and bool(self._grid_page_doms) and all(
            confirm_ulta_us_market(
                dom,
                expected_sku=None,
                page_kind="grid",
            ).confirmed
            for dom in self._grid_page_doms
        )
        return PinConfirmation(
            confirmed=confirmed,
            detail=(
                "every retained Ulta category page bound the en-US site conjunction "
                "and the deterministic page window completed"
                if confirmed
                else "Ulta category pages did not unanimously bind en-US or traversal failed"
            ),
        )

    def note(self, outcome: PreCaptureOutcome, confirmation: PinConfirmation) -> str:
        reason = confirmation.detail
        if not outcome.steps_completed and outcome.reason:
            reason = f"{outcome.reason}; {reason}"
        return (
            "declared_storefront_market: Ulta category route CONFIRMED as US "
            f"({reason}); currency and delivery location remain un-pinned"
            if confirmation.confirmed
            else f"declared_storefront_market: Ulta category route NOT confirmed ({reason})"
        )

    def describe(self) -> dict[str, object]:
        return {
            "pre_capture": "ulta_category_deterministic_page_traversal",
            "market_page_kind": "grid",
            "country_code_requested": "US",
            "currency_code_requested": None,
            "market_confirmation_scope": "retailer_rendered_country_route_only",
            **self._grid_observation,
        }

    def _failed(
        self, reason: str, observations: list[dict[str, object]]
    ) -> PreCaptureOutcome:
        self._grid_observation = {
            "pageSize": ULTA_CATEGORY_PAGE_SIZE,
            "capturedPageCount": len(self._grid_page_doms),
            "pageObservations": list(observations),
            "termination": "unproven",
            "failure": reason,
        }
        return _outcome(reason=reason)


def _category_page_url(url: str, *, page: int) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["page"] = str(page)
    query["sort"] = "best_sellers"
    return urlunparse(parsed._replace(query=urlencode(query)))


def _matches_requested_page(
    final_url: str, requested_url: str, expected_page: int
) -> bool:
    final = urlparse(final_url)
    requested = urlparse(requested_url)
    query = dict(parse_qsl(final.query, keep_blank_values=True))
    return (
        final.scheme == "https"
        and (final.hostname or "").lower() in {"ulta.com", "www.ulta.com"}
        and final.path.rstrip("/") == requested.path.rstrip("/")
        and query.get("page") == str(expected_page)
        and query.get("sort") == "best_sellers"
    )


def _remaining_ms(deadline: float) -> int:
    remaining = int((deadline - time.monotonic()) * 1000)
    if remaining <= 0:
        raise TimeoutError("Ulta category traversal timeout exhausted")
    return remaining


def _outcome(*, reason: str | None = None) -> PreCaptureOutcome:
    return PreCaptureOutcome(
        attempted=True,
        steps_completed=reason is None,
        reason=reason,
        warning_notes=[],
    )


__all__ = ["UltaCategoryTraversalPlugin"]
