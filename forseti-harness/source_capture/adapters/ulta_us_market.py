"""Ulta US/USD storefront assertion for anonymous CloakBrowser capture.

Ulta exposes no public country selector on the commissioned PDP. Its rendered
document does, however, bind the served site through first-party locale/site
configuration and binds offer currency independently in both a product price
node and Product JSON-LD. This plugin performs no preference mutation and
confirms that conjunction only after the main page renders.

Delivery location is deliberately outside this assertion.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Iterator, Literal
from urllib.parse import parse_qs, urlparse

from source_capture.adapters.cloakbrowser_snapshot import (
    PinConfirmation,
    PreCaptureOutcome,
)


_ULTA_HOSTS = frozenset({"ulta.com", "www.ulta.com"})
_APP_LOCALE_RE = re.compile(
    r"""window\.__APP_LOCALE__\s*=\s*["'](?P<value>[^"']+)["']""",
    flags=re.IGNORECASE,
)
_ULTASITE_RE = re.compile(r"ultasite=(?P<value>[A-Za-z_-]+)", flags=re.IGNORECASE)


@dataclass(frozen=True)
class UltaUSMarketPlugin:
    """Confirm an Ulta PDP or brand grid is serving its US storefront."""

    target_url: str
    sku: str | None = None
    country_code: str = "US"
    currency_code: str = "USD"
    page_kind: Literal["pdp", "grid"] = "pdp"

    def __post_init__(self) -> None:
        parsed = urlparse(self.target_url)
        if self.country_code != "US" or self.currency_code != "USD":
            raise ValueError("Ulta market assertion currently supports only US/USD")
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in _ULTA_HOSTS:
            raise ValueError("Ulta market assertion requires an HTTPS ulta.com URL")
        if self.page_kind == "grid":
            path = parsed.path.rstrip("/")
            if not (
                re.fullmatch(r"/brand/[a-z0-9][a-z0-9-]*", path)
                or re.fullmatch(r"/shop/[a-z0-9][a-z0-9-]*/all", path)
            ):
                raise ValueError(
                    "Ulta grid market assertion requires an exact /brand/<slug> "
                    "or /shop/<category>/all URL"
                )
            return
        requested_skus = parse_qs(parsed.query).get("sku", [])
        if self.sku is None or requested_skus != [self.sku] or not self.sku.isdigit():
            raise ValueError(
                "Ulta market assertion requires an HTTPS ulta.com PDP with one "
                "numeric sku query value matching the commissioned SKU"
            )

    @property
    def humanize(self) -> bool:
        return False

    def before(self, page: object, *, setup_timeout_ms: float) -> PreCaptureOutcome:
        del page, setup_timeout_ms
        return PreCaptureOutcome(
            attempted=True,
            steps_completed=True,
            reason=None,
            warning_notes=[],
        )

    def confirm(self, rendered_dom: str) -> PinConfirmation:
        return confirm_ulta_us_market(
            rendered_dom, expected_sku=self.sku, page_kind=self.page_kind
        )

    def describe(self) -> dict[str, object]:
        return {
            "pre_capture": "ulta_us_market_assertion",
            "country_code_requested": self.country_code,
            "currency_code_requested": self.currency_code,
            "product_sku_requested": self.sku,
            "page_kind": self.page_kind,
            "market_preference_action": "none_rendered_market_assertion",
        }

    def note(self, outcome: PreCaptureOutcome, confirmation: PinConfirmation) -> str:
        if confirmation.confirmed:
            if self.page_kind == "grid":
                return (
                    "declared_storefront_market: Ulta rendered brand grid CONFIRMED as "
                    f"US country route ({confirmation.detail}); currency and delivery "
                    "location remain un-pinned"
                )
            return (
                "declared_storefront_market: Ulta rendered PDP CONFIRMED as "
                f"US/USD ({confirmation.detail}); delivery location remains un-pinned"
            )
        reason = confirmation.detail
        if not outcome.steps_completed and outcome.reason is not None:
            reason = f"pre-capture assertion setup failed: {outcome.reason}; {reason}"
        return (
            "declared_storefront_market: Ulta rendered-market assertion NOT confirmed "
            f"({reason}); treat storefront country and currency as un-pinned "
            "(honest gap)"
        )


def confirm_ulta_us_market(
    rendered_dom: str,
    *,
    expected_sku: str | None,
    page_kind: Literal["pdp", "grid"] = "pdp",
) -> PinConfirmation:
    """Require Ulta-owned US site state plus two independent bound USD offers."""
    dom = rendered_dom or ""
    parser = _UltaMarkupParser()
    try:
        parser.feed(dom)
        parser.close()
    except Exception:
        return PinConfirmation(
            confirmed=False,
            detail="required Ulta US/USD rendered conjunction absent: malformed HTML",
        )

    html_langs = set(parser.html_langs)
    app_locales = {match.group("value") for match in _APP_LOCALE_RE.finditer(dom)}
    ulta_sites = {
        match.group("value").lower() for match in _ULTASITE_RE.finditer(dom)
    }
    us_site_state = (
        html_langs == {"en-US"}
        and app_locales == {"en-US"}
        and ulta_sites == {"en-us"}
    )

    if page_kind == "grid":
        if us_site_state:
            return PinConfirmation(
                confirmed=True,
                detail=(
                    "root/app/site state consistently bound en-US; the brand grid "
                    "does not expose an independent currency binding"
                ),
            )
        return PinConfirmation(
            confirmed=False,
            detail=(
                "required Ulta US rendered conjunction absent: consistent html "
                "lang=en-US, window.__APP_LOCALE__=en-US, and Ulta GraphQL "
                "ultasite=en-us"
            ),
        )

    if expected_sku is None:
        return PinConfirmation(
            confirmed=False,
            detail="required Ulta US/USD rendered conjunction absent: expected PDP SKU",
        )

    product_placements = [
        attributes
        for attributes in parser.square_placements
        if attributes.get("data-page-type") == "product"
    ]
    matching_placements = [
        attributes
        for attributes in product_placements
        if attributes.get("data-consumer-locale") == "en_US"
        and attributes.get("data-currency") == "USD"
        and _nonempty_number(attributes.get("data-amount"))
    ]
    placement_has_conflict = any(
        (
            attributes.get("data-consumer-locale") not in {None, "en_US"}
            or attributes.get("data-currency") not in {None, "USD"}
        )
        for attributes in product_placements
    )
    usd_price_node = bool(matching_placements) and not placement_has_conflict

    product_offer = any(
        _is_bound_ulta_usd_product(candidate, expected_sku=expected_sku)
        for candidate in _iter_json_ld_objects(parser.json_ld_documents)
    )

    if us_site_state and usd_price_node and product_offer:
        return PinConfirmation(
            confirmed=True,
            detail=(
                "root/app/site state consistently bound en-US, one Ulta product "
                "price node bound consumer locale en_US and currency USD, and Product "
                f"JSON-LD bound SKU {expected_sku} to a nonempty USD offer"
            ),
        )

    missing: list[str] = []
    if not us_site_state:
        missing.append(
            "consistent html lang=en-US, window.__APP_LOCALE__=en-US, and "
            "Ulta GraphQL ultasite=en-us"
        )
    if not usd_price_node:
        missing.append(
            "non-conflicting Ulta product price node with "
            "data-consumer-locale=en_US, data-currency=USD, and nonempty amount"
        )
    if not product_offer:
        missing.append(
            f"Product JSON-LD SKU {expected_sku} with a nonempty USD offer"
        )
    return PinConfirmation(
        confirmed=False,
        detail="required Ulta US/USD rendered conjunction absent: " + "; ".join(missing),
    )


class _UltaMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.html_langs: list[str] = []
        self.square_placements: list[dict[str, str]] = []
        self.json_ld_documents: list[str] = []
        self._in_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        lowered_tag = tag.lower()
        if lowered_tag == "html":
            self.html_langs.append(attributes.get("lang", ""))
        elif lowered_tag == "square-placement":
            self.square_placements.append(attributes)
        elif (
            lowered_tag == "script"
            and attributes.get("type", "").lower() == "application/ld+json"
        ):
            self._in_json_ld = True
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_json_ld:
            self.json_ld_documents.append("".join(self._json_ld_parts))
            self._json_ld_parts = []
            self._in_json_ld = False


def _iter_json_ld_objects(documents: list[str]) -> Iterator[dict[str, Any]]:
    for document in documents:
        try:
            value = json.loads(document)
        except (json.JSONDecodeError, TypeError):
            continue
        yield from _walk_json_objects(value)


def _walk_json_objects(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json_objects(child)


def _is_bound_ulta_usd_product(
    candidate: dict[str, Any],
    *,
    expected_sku: str,
) -> bool:
    if candidate.get("@type") != "Product" or str(candidate.get("sku")) != expected_sku:
        return False
    offers = candidate.get("offers")
    offer_values = offers if isinstance(offers, list) else [offers]
    return any(
        isinstance(offer, dict)
        and offer.get("@type") == "Offer"
        and offer.get("priceCurrency") == "USD"
        and _nonempty_number(offer.get("price"))
        for offer in offer_values
    )


def _nonempty_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value >= 0
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        return float(value) >= 0
    except ValueError:
        return False
