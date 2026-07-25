"""Deterministic aggregate record for paginated Ulta category bestseller grids."""

from __future__ import annotations

from dataclasses import replace
from math import ceil
from typing import Mapping, Sequence

from source_capture.ulta_brand_grid import (
    ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION,
    UltaBrandGridCard,
    UltaBrandGridStateError,
    load_ulta_brand_grid_state,
)


ULTA_CATEGORY_PAGE_SIZE = 64
ULTA_CATEGORY_MAX_WINDOW = 720


def requested_ulta_category_window(declared_count: int) -> int:
    """Return the top-quartile target, capped by the commissioned 720 placements."""

    if declared_count < 1:
        raise ValueError("Ulta category declared count must be positive")
    return min(ceil(declared_count / 4), ULTA_CATEGORY_MAX_WINDOW)


def build_ulta_category_grid_aggregate_content_record(
    *,
    rendered_pages: Sequence[str],
    requested_url: str,
    page_urls: Sequence[str],
    traversal_observation: Mapping[str, object],
) -> dict[str, object]:
    """Merge deterministic ``?page=N`` pages into one bounded category record."""

    if not rendered_pages or len(rendered_pages) != len(page_urls):
        raise UltaBrandGridStateError(
            "Ulta category traversal requires equally sized non-empty page DOMs and URLs"
        )
    states = [load_ulta_brand_grid_state(dom) for dom in rendered_pages]
    if any(state is None for state in states):
        raise UltaBrandGridStateError(
            "Ulta category traversal page omitted rendered grid state"
        )
    concrete_states = [state for state in states if state is not None]
    first = concrete_states[0]
    if first.declared_count is None:
        raise UltaBrandGridStateError(
            "Ulta category traversal requires a declared result count"
        )
    requested_window_count = requested_ulta_category_window(first.declared_count)
    requested_page_count = ceil(requested_window_count / ULTA_CATEGORY_PAGE_SIZE)

    cards: list[UltaBrandGridCard] = []
    for page_index, state in enumerate(concrete_states, start=1):
        if state.declared_count != first.declared_count:
            raise UltaBrandGridStateError(
                f"Ulta category declared count changed on page {page_index}"
            )
        if state.brand_name != first.brand_name:
            raise UltaBrandGridStateError(
                f"Ulta category heading changed on page {page_index}"
            )
        if state.selected_sort_id != "best_sellers":
            raise UltaBrandGridStateError(
                f"Ulta category page {page_index} did not retain best_sellers sort"
            )
        for card in state.cards:
            if len(cards) >= requested_window_count:
                break
            cards.append(
                replace(
                    card,
                    grid_position=(
                        (page_index - 1) * ULTA_CATEGORY_PAGE_SIZE
                        + card.grid_position
                    ),
                )
            )

    if len(cards) != requested_window_count:
        raise UltaBrandGridStateError(
            "Ulta category traversal did not fill its requested bounded window: "
            f"requested={requested_window_count}:captured={len(cards)}"
        )
    termination = traversal_observation.get("termination")
    if termination not in {
        "requested_page_window_reconciled",
        "retailer_terminal_reconciled",
    }:
        raise UltaBrandGridStateError(
            "Ulta category traversal termination was not reconciled"
        )

    return {
        "content_record_version": ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION,
        "retailer": "ulta",
        "final_url": page_urls[-1],
        "requested_url": requested_url,
        "category_name": first.brand_name,
        "viewed_count": len(cards),
        "declared_count": first.declared_count,
        "load_more_control_present": len(cards) < first.declared_count,
        "explicit_currency_codes": list(
            dict.fromkeys(
                code
                for state in concrete_states
                for code in state.explicit_currency_codes
            )
        ),
        "selected_sort_id": "best_sellers",
        "requested_window_count": requested_window_count,
        "requested_page_count": requested_page_count,
        "captured_page_count": len(concrete_states),
        "traversal_termination": termination,
        "page_urls": list(page_urls),
        "page_observations": list(
            traversal_observation.get("pageObservations", [])
            if isinstance(traversal_observation.get("pageObservations"), list)
            else []
        ),
        "cards": [
            {
                "grid_position": card.grid_position,
                "source_product_id": card.source_product_id,
                "selected_sku_id": card.selected_sku_id,
                "product_url": card.product_url,
                "brand_name": card.brand_name,
                "name": card.name,
                "price_display": card.price_display,
                "average_rating": card.average_rating,
                "review_count": card.review_count,
                "visible_variant_count": card.visible_variant_count,
                "visible_variant_label": card.visible_variant_label,
                "badges": list(card.badges),
            }
            for card in cards
        ],
    }


__all__ = [
    "ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION",
    "ULTA_CATEGORY_MAX_WINDOW",
    "ULTA_CATEGORY_PAGE_SIZE",
    "build_ulta_category_grid_aggregate_content_record",
    "requested_ulta_category_window",
]
