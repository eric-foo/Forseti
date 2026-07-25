from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlparse


_VIEWED_COUNT_RE = re.compile(r"You have viewed\s+(?P<viewed>\d+)\s+of\s+(?P<total>\d+)", re.IGNORECASE)
# Ulta category grids carry the declared cohort size in the document <title>
# (e.g. "Shop All Makeup - 7092 Products | Ulta Beauty"). This is a robust
# fallback for the declared count when the view-triggered "You have viewed N of M"
# footer has not rendered. Brand-grid titles carry no "N Products" phrase.
_PRODUCTS_TITLE_COUNT_RE = re.compile(r"(?P<total>\d[\d,]*)\s+Products\b", re.IGNORECASE)
_RATING_RE = re.compile(
    r"(?P<rating>\d+(?:\.\d+)?)\s+out of 5 stars\s*;\s*"
    r"(?P<reviews>\d[\d,]*)\s+reviews?",
    re.IGNORECASE,
)
_VARIANT_RE = re.compile(r"(?P<count>\d+)\s+(?:colou?rs?|sizes?)", re.IGNORECASE)
# Ulta product URLs end in ``-<productId>`` where the id ends in a digit. The id
# is usually letter-prefixed (``pimprod2059833``, ``xlsImpprod14251035``) but
# legacy drugstore products carry a purely-numeric id (e.g. ``-2641``), so the
# leading letter must be optional or those real products lose their identity.
_PRODUCT_ID_RE = re.compile(r"-([A-Za-z0-9]*\d)$")
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)
# Ulta serializes stale continuation state (for example an earlier
# `productsViewedLabel`) inside `<script id="apollo_state">`. That CDATA is not
# rendered text, so it must never reach the visible-text or card captures.
_NON_RENDERED_TEXT_TAGS = frozenset({"script", "style"})
ULTA_GRID_CONTENT_RECORD_VERSION = "ulta_grid_content_v1"
ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION = "ulta_category_grid_content_v1"


class UltaBrandGridStateError(ValueError):
    """The rendered Ulta brand grid could not be parsed deterministically."""


@dataclass(frozen=True)
class UltaBrandGridCard:
    grid_position: int
    source_product_id: str | None
    selected_sku_id: str | None
    product_url: str | None
    brand_name: str | None
    name: str | None
    price_display: str | None
    average_rating: str | None
    review_count: int | None
    visible_variant_count: int | None
    visible_variant_label: str | None
    badges: tuple[str, ...]


@dataclass(frozen=True)
class UltaBrandGridState:
    brand_name: str | None
    viewed_count: int | None
    declared_count: int | None
    cards: tuple[UltaBrandGridCard, ...]
    load_more_control_present: bool
    explicit_currency_codes: tuple[str, ...]
    content_record_version: str | None = None
    # The retailer-owned selected sort id (e.g. ``best_sellers``) rendered in the
    # grid's Sort By control. ``None`` on brand grids, which expose no sort control.
    selected_sort_id: str | None = None
    category_name: str | None = None
    requested_window_count: int | None = None
    requested_page_count: int | None = None
    captured_page_count: int | None = None
    traversal_termination: str | None = None


@dataclass
class _CardBuilder:
    grid_position: int
    selected_sku_id: str | None
    product_url: str | None = None
    brand_name: str | None = None
    name: str | None = None
    price_display: str | None = None
    rating_text: str | None = None
    variant_text: str | None = None
    badges: list[str] = field(default_factory=list)


@dataclass
class _Capture:
    field_name: str
    tag: str
    depth: int
    parts: list[str] = field(default_factory=list)


class _UltaBrandGridParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.current_card: _CardBuilder | None = None
        self.card_start_depth: int | None = None
        self.captures: list[_Capture] = []
        self.cards: list[UltaBrandGridCard] = []
        self.visible_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.h1_depth: int | None = None
        self.title_parts: list[str] = []
        self.in_title = False
        self.load_more_control_present = False
        self.explicit_currency_codes: list[str] = []
        self.selected_sort_ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered_tag = tag.lower()
        attributes = {key.lower(): value or "" for key, value in attrs}
        if lowered_tag not in _VOID_TAGS:
            self.stack.append(lowered_tag)
        depth = len(self.stack)
        currency = attributes.get("data-currency", "").strip()
        if currency:
            self.explicit_currency_codes.append(currency)
        if attributes.get("data-testid") == "dropdown__header__value":
            sort_id = (attributes.get("id") or "").strip()
            if sort_id and sort_id not in self.selected_sort_ids:
                self.selected_sort_ids.append(sort_id)
        if lowered_tag == "title":
            self.in_title = True

        if (
            self.current_card is None
            and lowered_tag == "li"
            and attributes.get("data-test") == "products-list-item"
        ):
            self.current_card = _CardBuilder(
                grid_position=len(self.cards) + 1,
                selected_sku_id=attributes.get("data-sku-id") or None,
            )
            self.card_start_depth = depth
            return

        if self.current_card is not None:
            href = attributes.get("href")
            if lowered_tag == "a" and href and "/p/" in href and self.current_card.product_url is None:
                self.current_card.product_url = (
                    f"https://www.ulta.com{href}" if href.startswith("/") else href
                )
            field_name = _capture_field(attributes.get("class", ""))
            if field_name is not None:
                self.captures.append(_Capture(field_name=field_name, tag=lowered_tag, depth=depth))
            return

        if lowered_tag == "h1" and self.h1_depth is None:
            self.h1_depth = depth
        if lowered_tag == "button" and "LoadContent__button" in _class_tokens(attributes.get("class", "")):
            self.load_more_control_present = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1] in _NON_RENDERED_TEXT_TAGS:
            return
        text = " ".join(data.split())
        if not text:
            return
        self.visible_parts.append(text)
        if self.in_title:
            self.title_parts.append(text)
        if self.h1_depth is not None:
            self.h1_parts.append(text)
        for capture in self.captures:
            capture.parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        lowered_tag = tag.lower()
        depth = len(self.stack)
        for capture in list(self.captures):
            if capture.tag == lowered_tag and capture.depth == depth:
                self._finish_capture(capture)
                self.captures.remove(capture)
        if self.h1_depth == depth and lowered_tag == "h1":
            self.h1_depth = None
        if lowered_tag == "title":
            self.in_title = False
        if self.current_card is not None and lowered_tag == "li" and self.card_start_depth == depth:
            self.cards.append(_finish_card(self.current_card))
            self.current_card = None
            self.card_start_depth = None
            self.captures.clear()
        if self.stack:
            if self.stack[-1] == lowered_tag:
                self.stack.pop()
            elif lowered_tag in self.stack:
                match_index = len(self.stack) - 1 - self.stack[::-1].index(lowered_tag)
                del self.stack[match_index:]

    def _finish_capture(self, capture: _Capture) -> None:
        if self.current_card is None:
            return
        value = " ".join(capture.parts).strip() or None
        if value is None:
            return
        if capture.field_name == "badge":
            self.current_card.badges.append(value)
        elif getattr(self.current_card, capture.field_name) is None:
            setattr(self.current_card, capture.field_name, value)


def load_ulta_brand_grid_state(rendered_dom: str) -> UltaBrandGridState | None:
    compact_state = _load_compact_state(rendered_dom)
    if compact_state is not None:
        return compact_state

    parser = _UltaBrandGridParser()
    try:
        parser.feed(rendered_dom or "")
        parser.close()
    except Exception as exc:
        raise UltaBrandGridStateError(
            f"Ulta brand-grid rendered DOM is malformed: {type(exc).__name__}"
        ) from exc
    if not parser.cards:
        return None
    count_matches = list(_VIEWED_COUNT_RE.finditer(" ".join(parser.visible_parts)))
    viewed_count: int | None = None
    declared_count: int | None = None
    if count_matches:
        viewed_count = int(count_matches[-1].group("viewed"))
        declared_count = int(count_matches[-1].group("total"))
    if declared_count is None:
        title_match = _PRODUCTS_TITLE_COUNT_RE.search(" ".join(parser.title_parts))
        if title_match:
            declared_count = int(title_match.group("total").replace(",", ""))
    return UltaBrandGridState(
        brand_name=" ".join(parser.h1_parts).strip() or None,
        viewed_count=viewed_count,
        declared_count=declared_count,
        cards=tuple(parser.cards),
        load_more_control_present=parser.load_more_control_present,
        explicit_currency_codes=tuple(dict.fromkeys(parser.explicit_currency_codes)),
        selected_sort_id=(
            parser.selected_sort_ids[0]
            if len(parser.selected_sort_ids) == 1
            else None
        ),
    )


def build_ulta_brand_grid_content_record(
    *, rendered_dom: str, final_url: str
) -> dict[str, object]:
    """Retain parsed grid facts while discarding the rendered browser envelope."""

    state = load_ulta_brand_grid_state(rendered_dom)
    if state is None:
        raise UltaBrandGridStateError(
            "Ulta brand-grid state is absent from the rendered DOM"
        )
    return {
        "content_record_version": ULTA_GRID_CONTENT_RECORD_VERSION,
        "retailer": "ulta",
        "final_url": final_url,
        "brand_name": state.brand_name,
        "viewed_count": state.viewed_count,
        "declared_count": state.declared_count,
        "load_more_control_present": state.load_more_control_present,
        "explicit_currency_codes": list(state.explicit_currency_codes),
        "selected_sort_id": state.selected_sort_id,
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
            for card in state.cards
        ],
    }


def _load_compact_state(value: str) -> UltaBrandGridState | None:
    stripped = (value or "").lstrip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "content_record_version" not in payload:
        return None
    content_record_version = payload.get("content_record_version")
    if content_record_version not in {
        ULTA_GRID_CONTENT_RECORD_VERSION,
        ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION,
    }:
        raise UltaBrandGridStateError("Ulta grid content record version is unsupported")
    if payload.get("retailer") != "ulta":
        raise UltaBrandGridStateError(
            "Ulta grid content record retailer binding is invalid"
        )
    cards_value = payload.get("cards")
    if not isinstance(cards_value, list) or not cards_value:
        raise UltaBrandGridStateError(
            "Ulta grid content record cards must be a non-empty array"
        )
    cards: list[UltaBrandGridCard] = []
    for index, value in enumerate(cards_value):
        if not isinstance(value, dict):
            raise UltaBrandGridStateError(
                "Ulta grid content record cards contains a non-object row"
            )
        grid_position = value.get("grid_position")
        if (
            not isinstance(grid_position, int)
            or isinstance(grid_position, bool)
            or grid_position < 1
        ):
            raise UltaBrandGridStateError(
                f"Ulta grid content record card {index} has an invalid grid position"
            )
        badges = value.get("badges")
        if not isinstance(badges, list) or not all(
            isinstance(badge, str) for badge in badges
        ):
            raise UltaBrandGridStateError(
                f"Ulta grid content record card {index} has invalid badges"
            )
        cards.append(
            UltaBrandGridCard(
                grid_position=grid_position,
                source_product_id=_optional_text_field(value, "source_product_id", index),
                selected_sku_id=_optional_text_field(value, "selected_sku_id", index),
                product_url=_optional_text_field(value, "product_url", index),
                brand_name=_optional_text_field(value, "brand_name", index),
                name=_optional_text_field(value, "name", index),
                price_display=_optional_text_field(value, "price_display", index),
                average_rating=_optional_text_field(value, "average_rating", index),
                review_count=_optional_integer_field(value, "review_count", index),
                visible_variant_count=_optional_integer_field(
                    value, "visible_variant_count", index
                ),
                visible_variant_label=_optional_text_field(
                    value, "visible_variant_label", index
                ),
                badges=tuple(badges),
            )
        )
    currency_codes = payload.get("explicit_currency_codes")
    if not isinstance(currency_codes, list) or not all(
        isinstance(code, str) for code in currency_codes
    ):
        raise UltaBrandGridStateError(
            "Ulta grid content record explicit currency codes are invalid"
        )
    load_more = payload.get("load_more_control_present")
    if not isinstance(load_more, bool):
        raise UltaBrandGridStateError(
            "Ulta grid content record load-more posture is invalid"
        )
    return UltaBrandGridState(
        brand_name=_optional_text_field(payload, "brand_name", -1),
        viewed_count=_optional_integer_field(payload, "viewed_count", -1),
        declared_count=_optional_integer_field(payload, "declared_count", -1),
        cards=tuple(cards),
        load_more_control_present=load_more,
        explicit_currency_codes=tuple(currency_codes),
        content_record_version=str(content_record_version),
        selected_sort_id=_optional_text_field(payload, "selected_sort_id", -1),
        category_name=_optional_text_field(payload, "category_name", -1),
        requested_window_count=_optional_integer_field(
            payload, "requested_window_count", -1
        ),
        requested_page_count=_optional_integer_field(
            payload, "requested_page_count", -1
        ),
        captured_page_count=_optional_integer_field(
            payload, "captured_page_count", -1
        ),
        traversal_termination=_optional_text_field(
            payload, "traversal_termination", -1
        ),
    )


def _optional_text_field(
    value: dict[str, object], field_name: str, card_index: int
) -> str | None:
    field_value = value.get(field_name)
    if field_value is None or isinstance(field_value, str):
        return field_value
    context = "record" if card_index < 0 else f"card {card_index}"
    raise UltaBrandGridStateError(
        f"Ulta grid content record {context} has invalid {field_name}"
    )


def _optional_integer_field(
    value: dict[str, object], field_name: str, card_index: int
) -> int | None:
    field_value = value.get(field_name)
    if field_value is None or (
        isinstance(field_value, int)
        and not isinstance(field_value, bool)
        and field_value >= 0
    ):
        return field_value
    context = "record" if card_index < 0 else f"card {card_index}"
    raise UltaBrandGridStateError(
        f"Ulta grid content record {context} has invalid {field_name}"
    )


def _finish_card(card: _CardBuilder) -> UltaBrandGridCard:
    rating_match = _RATING_RE.search(card.rating_text or "")
    variant_match = _VARIANT_RE.search(card.variant_text or "")
    return UltaBrandGridCard(
        grid_position=card.grid_position,
        source_product_id=_product_id_from_url(card.product_url),
        selected_sku_id=card.selected_sku_id,
        product_url=card.product_url,
        brand_name=card.brand_name,
        name=card.name,
        price_display=card.price_display,
        average_rating=rating_match.group("rating") if rating_match else None,
        review_count=int(rating_match.group("reviews").replace(",", "")) if rating_match else None,
        visible_variant_count=int(variant_match.group("count")) if variant_match else None,
        visible_variant_label=card.variant_text,
        badges=tuple(dict.fromkeys(card.badges)),
    )


def _product_id_from_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    if (parsed.hostname or "").lower() not in {"ulta.com", "www.ulta.com"}:
        return None
    match = _PRODUCT_ID_RE.search(parsed.path.rstrip("/"))
    return match.group(1) if match else None


def _capture_field(class_value: str) -> str | None:
    tokens = _class_tokens(class_value)
    if "pal-c-ProductCardBody--brandName" in tokens:
        return "brand_name"
    if "pal-c-ProductCardBody--title" in tokens:
        return "name"
    if "pal-c-ProductCardBody--price" in tokens:
        return "price_display"
    if "pal-c-ProductCardHeader__variant" in tokens:
        return "variant_text"
    if "sr-only" in tokens:
        return "rating_text"
    if any("badge" in token.lower() for token in tokens):
        return "badge"
    return None


def _class_tokens(value: str) -> frozenset[str]:
    return frozenset(value.split())


__all__ = [
    "ULTA_CATEGORY_GRID_CONTENT_RECORD_VERSION",
    "ULTA_GRID_CONTENT_RECORD_VERSION",
    "UltaBrandGridCard",
    "UltaBrandGridState",
    "UltaBrandGridStateError",
    "build_ulta_brand_grid_content_record",
    "load_ulta_brand_grid_state",
]
