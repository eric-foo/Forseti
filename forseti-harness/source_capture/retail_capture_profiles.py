from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse

from source_capture.adapters.cloakbrowser_snapshot import ScrollStopCondition
from source_capture.sephora_catalog_grid import (
    SEPHORA_CATALOG_MAX_PAGE,
    extract_sephora_catalog_request,
)
from source_capture.source_detail_sufficiency import (
    SourceDetailSufficiencyRequirements,
    validate_source_detail_sufficiency_requirements,
)


RETAIL_CAPTURE_PROFILE_SCHEMA_VERSION = 4


_AMAZON_ASIN_IN_PATH = re.compile(r"/(?:dp|gp/product|gp/aw/d)/([A-Za-z0-9]{10})(?:[/?]|$)")
_NORDSTROM_PRODUCT_ID_IN_PATH = re.compile(r"/s/[^/?]+/(\d+)(?:[/?]|$)")
_SEPHORA_PRODUCT_ID_IN_PATH = re.compile(r"-(P\d+)(?:[/?]|$)", flags=re.IGNORECASE)
_ULTA_PRODUCT_ID_IN_PATH = re.compile(
    r"/p/[A-Za-z0-9%.~-]*?-((?:(?:xlsImpprod|pimprod|prod)[A-Za-z0-9]+|VP\d+))(?:[/?]|$)",
    flags=re.IGNORECASE,
)
_TARGET_PRODUCT_ID_IN_PATH = re.compile(r"/-/A-(\d+)(?:[/?]|$)", flags=re.IGNORECASE)
_TARGET_BRAND_GRID_PATH = re.compile(
    r"^/b/(?P<slug>[^/]+)/-/N-[^/]+/?$", flags=re.IGNORECASE
)
_REVOLVE_STYLE_ID_IN_PATH = re.compile(
    r"/dp/(?P<style_id>[A-Z0-9]{2,12}-[A-Z]{1,4}\d+)(?:[/?]|$)",
    flags=re.IGNORECASE,
)
_REVOLVE_BRAND_GRID_PATH = re.compile(
    r"^/(?P<slug>[a-z0-9][a-z0-9-]*)/br/(?P<brand_id>[a-f0-9]{6})/?$",
    flags=re.IGNORECASE,
)


def extract_amazon_asin_from_url(url: str) -> str | None:
    match = _AMAZON_ASIN_IN_PATH.search(urlparse(url).path)
    return match.group(1) if match else None


def extract_amazon_search_query_from_url(url: str) -> str | None:
    values = parse_qs(urlparse(url).query).get("k")
    if not values or not values[0].strip():
        return None
    return values[0].strip()


def extract_nordstrom_product_id_from_url(url: str) -> str | None:
    match = _NORDSTROM_PRODUCT_ID_IN_PATH.search(urlparse(url).path)
    return match.group(1) if match else None


def extract_sephora_product_id_from_url(url: str) -> str | None:
    match = _SEPHORA_PRODUCT_ID_IN_PATH.search(urlparse(url).path)
    return match.group(1).upper() if match else None


def extract_ulta_product_id_from_url(url: str) -> str | None:
    match = _ULTA_PRODUCT_ID_IN_PATH.search(urlparse(url).path)
    return match.group(1) if match else None


def extract_target_product_id_from_url(url: str) -> str | None:
    match = _TARGET_PRODUCT_ID_IN_PATH.search(urlparse(url).path)
    return match.group(1) if match else None


def extract_revolve_style_id_from_url(url: str) -> str | None:
    match = _REVOLVE_STYLE_ID_IN_PATH.search(urlparse(url).path)
    return match.group("style_id").upper() if match else None


def extract_retailer_product_identity_from_url(
    retailer: str, url: str
) -> str | None:
    """Return the stable retailer-native PDP identity encoded by ``url``."""
    extractors = {
        "amazon": extract_amazon_asin_from_url,
        "revolve": extract_revolve_style_id_from_url,
        "sephora": extract_sephora_product_id_from_url,
        "target": extract_target_product_id_from_url,
        "ulta": extract_ulta_product_id_from_url,
    }
    extractor = extractors.get(retailer)
    return None if extractor is None else extractor(url)


def extract_retailer_variant_identity_from_url(
    retailer: str, url: str
) -> str | None:
    """Return an explicitly selected retailer SKU/variant when the route exposes one."""
    query_keys = {
        "sephora": "skuId",
        "target": "preselect",
        "ulta": "sku",
    }
    key = query_keys.get(retailer)
    if key is None:
        return None
    values = parse_qs(urlparse(url).query).get(key)
    if not values or not values[0].strip():
        return None
    return values[0].strip()


def extract_revolve_grid_subject_from_url(
    url: str,
) -> tuple[str, str] | None:
    match = _REVOLVE_BRAND_GRID_PATH.fullmatch(urlparse(url).path)
    if match is None:
        return None
    return match.group("slug").lower(), match.group("brand_id").lower()


def extract_target_search_query_from_url(url: str) -> str | None:
    values = parse_qs(urlparse(url).query).get("searchTerm")
    if not values or not values[0].strip():
        return None
    return values[0].strip()


def extract_target_grid_subject_from_url(url: str) -> tuple[str, str] | None:
    """Return the retailer-owned Target grid subject encoded by ``url``."""
    parsed = urlparse(url)
    if parsed.path.rstrip("/") == "/s":
        query = extract_target_search_query_from_url(url)
        return ("search_query", query) if query is not None else None
    match = _TARGET_BRAND_GRID_PATH.fullmatch(parsed.path)
    if match is None:
        return None
    return "brand", match.group("slug")


def target_bestseller_grid_url(url: str) -> str:
    """Start an admitted Target grid at page one in retailer bestseller order."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
        "target.com",
        "www.target.com",
    }:
        raise ValueError("Target grid capture requires an HTTPS target.com URL")
    if extract_target_grid_subject_from_url(url) is None:
        raise ValueError(
            "Target grid capture requires /s?searchTerm=<query> or "
            "/b/<brand>/-/N-<category>"
        )
    replaced = {"sortby", "moveto", "count", "nao"}
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.casefold() not in replaced
    ]
    query.extend(
        (("sortBy", "bestselling"), ("moveTo", "product-list-grid"))
    )
    return urlunparse(parsed._replace(query=urlencode(query), fragment=""))


def _target_brand_visible_text_regex(slug: str) -> str:
    # Separator-tolerant so ``e-l-f`` matches the rendered ``e.l.f.``, but token
    # bounded for the reason ``_exact_identity_regex`` documents below: an
    # unbounded short brand pattern is also satisfied by an unrelated word that
    # merely contains it (``e-l-f`` inside ``bookshelf``).
    parts = [part for part in re.split(r"[-_]+", slug) if part]
    joined = r"[\s.\-_]*".join(re.escape(part) for part in parts)
    return rf"(?i)(?<![A-Za-z0-9]){joined}(?![A-Za-z0-9])"


def _exact_identity_regex(product_id: str) -> str:
    """Bind ``product_id`` as a whole token in the rendered DOM.

    A bare ``re.escape(product_id)`` also matches inside any longer alphanumeric
    run, so a shorter requested id, or an unrelated numeric blob such as an epoch
    timestamp, satisfies the gate on a page for a different product. The Nordstrom
    derivation avoids this by anchoring its id inside a URL shape; retailer ids
    captured without such a shape use token boundaries instead.
    """
    return rf"(?<![A-Za-z0-9]){re.escape(product_id)}(?![A-Za-z0-9])"


@dataclass(frozen=True)
class RetailCaptureProfile:
    name: str
    retailer: str
    page_kind: str
    hostname: str
    source_surface: str
    ordinary_operation: bool
    requirements: SourceDetailSufficiencyRequirements
    wait_until: str = "load"
    settle_seconds: float = 0.0
    scroll_passes: int = 0
    scroll_step_px: int = 0
    scroll_target_selector: str | None = None
    load_more_selector: str | None = None
    load_more_clicks: int = 0
    requirements_define_scroll_stop: bool = True
    block_heavy_assets: bool = False
    derive_target_asin_from_url: bool = False
    derive_target_query_from_url: bool = False
    derive_target_nordstrom_product_id_from_url: bool = False
    derive_target_sephora_catalog_from_url: bool = False
    derive_target_sephora_product_id_from_url: bool = False
    derive_target_ulta_product_id_from_url: bool = False
    derive_target_target_product_id_from_url: bool = False
    derive_target_target_search_query_from_url: bool = False
    derive_target_target_grid_subject_from_url: bool = False
    derive_target_revolve_style_id_from_url: bool = False
    derive_target_revolve_grid_subject_from_url: bool = False

    def requirements_for_capture(self, *, url: str) -> SourceDetailSufficiencyRequirements:
        """Sufficiency requirements for one capture, with any per-target identity resolved.

        Structural/block-detection literals stay fixed on the profile. A per-target
        identity check is layered on top from ``url`` (rather than a hardcoded canary
        product) so the gate validates the SKU/query actually being captured:

        - ``derive_target_asin_from_url``: single-SKU PDP pages. The ASIN in ``url``
          (``.../dp/<ASIN>`` or ``.../gp/product/<ASIN>``) must appear in the rendered DOM.
        - ``derive_target_query_from_url``: search-results grid pages. The ``k`` query
          parameter in ``url`` must appear in the rendered visible text (Amazon's own
          "1-N of M results for '<query>'" banner echoes it back), proving the grid
          rendered real results for the query actually searched rather than a block page
          or unrelated content.
        - the Nordstrom, Sephora, Ulta, and Target product-id flags: the retailer id in
          ``url`` must appear in the rendered DOM, anchored (URL shape for Nordstrom,
          token boundaries elsewhere) so a longer id or an unrelated numeric run that
          merely contains it cannot satisfy the gate.
        - ``derive_target_sephora_catalog_from_url``: a bounded ``/shop/<category>``
          request whose exact cumulative page and BEST_SELLING sort are echoed by
          Sephora's retailer-owned render-query state.
        - ``derive_target_target_search_query_from_url``: the Target search-grid analogue
          of the Amazon ``k`` check, reading the ``searchTerm`` query parameter.
        - ``derive_target_target_grid_subject_from_url``: a Target search query or
          ``/b/<brand>/-/N-...`` brand slug echoed in retailer-visible page text.
        """
        if self.derive_target_asin_from_url:
            asin = extract_amazon_asin_from_url(url)
            if asin is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires an Amazon ASIN in --url "
                    f"(expected .../dp/<ASIN> or .../gp/product/<ASIN>); got {url!r}"
                )
            target_identity = SourceDetailSufficiencyRequirements(
                rendered_dom_regexes=(re.escape(asin),),
            )
            return merge_source_detail_sufficiency_requirements(self.requirements, target_identity)
        if self.derive_target_query_from_url:
            query = extract_amazon_search_query_from_url(url)
            if query is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a non-empty Amazon search "
                    f"query in --url (expected .../s?k=<query>); got {url!r}"
                )
            target_identity = SourceDetailSufficiencyRequirements(
                visible_text_regexes=(f"(?i){re.escape(query)}",),
            )
            return merge_source_detail_sufficiency_requirements(self.requirements, target_identity)
        if self.derive_target_nordstrom_product_id_from_url:
            product_id = extract_nordstrom_product_id_from_url(url)
            if product_id is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a Nordstrom product id in "
                    f"--url (expected .../s/<slug>/<numeric-id>); got {url!r}"
                )
            target_identity = SourceDetailSufficiencyRequirements(
                rendered_dom_regexes=(rf"/s/[^\"']+/{re.escape(product_id)}(?:[?\"'/]|$)",),
            )
            return merge_source_detail_sufficiency_requirements(
                self.requirements, target_identity
            )
        if self.derive_target_sephora_catalog_from_url:
            request = extract_sephora_catalog_request(url)
            if request is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires an HTTPS Sephora "
                    f"/shop/<category> URL with one currentPage in "
                    f"[1,{SEPHORA_CATALOG_MAX_PAGE}] and "
                    f"sortBy=BEST_SELLING; got {url!r}"
                )
            slug, page, _sort = request
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(
                        rf'"urlPath"\s*:\s*"/shop/{re.escape(slug)}"',
                        r'"cachedQueryParams"\s*:\s*"[^"]*currentPage=[1-5]',
                        r'"cachedQueryParams"\s*:\s*"[^"]*sortBy=BEST_SELLING',
                    )
                ),
            )
        if self.derive_target_sephora_product_id_from_url:
            product_id = extract_sephora_product_id_from_url(url)
            if product_id is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a Sephora product id in "
                    f"--url (expected ...-P<digits>); got {url!r}"
                )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(_exact_identity_regex(product_id),)
                ),
            )
        if self.derive_target_ulta_product_id_from_url:
            product_id = extract_ulta_product_id_from_url(url)
            if product_id is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires an Ulta product id in "
                    f"--url (expected ...-pimprod<digits> or another admitted Ulta id); got {url!r}"
                )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(_exact_identity_regex(product_id),)
                ),
            )
        if self.derive_target_target_product_id_from_url:
            product_id = extract_target_product_id_from_url(url)
            if product_id is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a Target TCIN in "
                    f"--url (expected .../-/A-<digits>); got {url!r}"
                )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(_exact_identity_regex(product_id),)
                ),
            )
        if self.derive_target_target_search_query_from_url:
            query = extract_target_search_query_from_url(url)
            if query is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a non-empty Target search "
                    f"query in --url (expected .../s?searchTerm=<query>); got {url!r}"
                )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    visible_text_regexes=(f"(?i){re.escape(query)}",),
                ),
            )
        if self.derive_target_target_grid_subject_from_url:
            subject = extract_target_grid_subject_from_url(url)
            if subject is None:
                if urlparse(url).path.rstrip("/") == "/s":
                    raise ValueError(
                        f"retail capture profile {self.name} requires a non-empty "
                        f"Target search query in --url; got {url!r}"
                    )
                raise ValueError(
                    f"retail capture profile {self.name} requires a Target search or "
                    f"brand-grid URL; got {url!r}"
                )
            kind, value = subject
            visible_pattern = (
                f"(?i){re.escape(value)}"
                if kind == "search_query"
                else _target_brand_visible_text_regex(value)
            )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    visible_text_regexes=(visible_pattern,),
                ),
            )
        if self.derive_target_revolve_style_id_from_url:
            style_id = extract_revolve_style_id_from_url(url)
            if style_id is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a REVOLVE style "
                    f"id in --url (expected .../dp/<style-id>); got {url!r}"
                )
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(_exact_identity_regex(style_id),)
                ),
            )
        if self.derive_target_revolve_grid_subject_from_url:
            subject = extract_revolve_grid_subject_from_url(url)
            if subject is None:
                raise ValueError(
                    f"retail capture profile {self.name} requires a REVOLVE "
                    f"/<brand>/br/<brand-id> URL; got {url!r}"
                )
            slug, brand_id = subject
            return merge_source_detail_sufficiency_requirements(
                self.requirements,
                SourceDetailSufficiencyRequirements(
                    rendered_dom_regexes=(
                        _exact_identity_regex(brand_id),
                        _target_brand_visible_text_regex(slug),
                    )
                ),
            )
        return self.requirements

    def target_product_identity_from_url(self, *, url: str) -> str | None:
        """Return the profile-bound PDP identity encoded by the URL, if any."""
        if self.derive_target_asin_from_url:
            return extract_amazon_asin_from_url(url)
        if self.derive_target_nordstrom_product_id_from_url:
            return extract_nordstrom_product_id_from_url(url)
        if self.derive_target_sephora_product_id_from_url:
            return extract_sephora_product_id_from_url(url)
        if self.derive_target_ulta_product_id_from_url:
            return extract_ulta_product_id_from_url(url)
        if self.derive_target_target_product_id_from_url:
            return extract_target_product_id_from_url(url)
        if self.derive_target_revolve_style_id_from_url:
            return extract_revolve_style_id_from_url(url)
        return None

    def scroll_stop_condition(self) -> ScrollStopCondition | None:
        if (
            self.source_surface != "cloakbrowser_snapshot"
            or not self.requirements_define_scroll_stop
        ):
            return None
        if (
            not self.requirements.visible_text_contains
            and not self.requirements.visible_text_regexes
        ):
            return None
        return ScrollStopCondition(
            visible_text_contains=self.requirements.visible_text_contains,
            visible_text_regexes=self.requirements.visible_text_regexes,
        )

    def metadata(self) -> dict[str, object]:
        return {
            "schema_version": RETAIL_CAPTURE_PROFILE_SCHEMA_VERSION,
            "name": self.name,
            "retailer": self.retailer,
            "page_kind": self.page_kind,
            "expected_route_flags": {
                "hostname": self.hostname,
                "source_family": "retail_pdp",
                "source_surface": self.source_surface,
                "ordinary_operation": self.ordinary_operation,
                "wait_until": self.wait_until,
                "settle_seconds": self.settle_seconds,
                "scroll_passes": self.scroll_passes,
                "scroll_step_px": self.scroll_step_px,
                "scroll_target_selector": self.scroll_target_selector,
                "load_more_selector": self.load_more_selector,
                "load_more_clicks": self.load_more_clicks,
                "requirements_define_scroll_stop": self.requirements_define_scroll_stop,
                "block_heavy_assets": self.block_heavy_assets,
            },
        }


def _requirements(
    *,
    visible_text_contains: tuple[str, ...] = (),
    visible_text_regexes: tuple[str, ...] = (),
    rendered_dom_contains: tuple[str, ...] = (),
    rendered_dom_regexes: tuple[str, ...] = (),
) -> SourceDetailSufficiencyRequirements:
    requirements = SourceDetailSufficiencyRequirements(
        require_not_access_blocked=True,
        min_visible_text_bytes=20,
        visible_text_contains=visible_text_contains,
        visible_text_regexes=visible_text_regexes,
        rendered_dom_contains=rendered_dom_contains,
        rendered_dom_regexes=rendered_dom_regexes,
    )
    validate_source_detail_sufficiency_requirements(requirements)
    return requirements


_PROFILES = {
    profile.name: profile
    for profile in (
        RetailCaptureProfile(
            name="amazon_grid_aggregate",
            retailer="amazon",
            page_kind="grid_aggregate",
            hostname="www.amazon.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=0.0,
            derive_target_query_from_url=True,
            requirements=_requirements(
                visible_text_regexes=(
                    r"\d[\d,]*-\d[\d,]* of (?:over )?\d[\d,]* results",
                    r"\d(?:\.\d)? out of 5 stars\s+\([\d.]+[KM]?\)",
                    r"\$\d+(?:\.\d{2})?",
                    r"\d+(?:\.\d+)?[KM]?\+ bought in past month",
                ),
                rendered_dom_regexes=(
                    r"(?:ue_sn\s*=\s*'www\.amazon\.com'|retail:prod:www\.amazon\.com|assoc_handle=usflex)",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="amazon_pdp_aggregate",
            retailer="amazon",
            page_kind="pdp_aggregate",
            hostname="www.amazon.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=0.0,
            derive_target_asin_from_url=True,
            requirements=_requirements(
                visible_text_contains=("New York 10001",),
                visible_text_regexes=(
                    r"\d(?:\.\d)? out of 5 stars",
                    r"\$\d+(?:\.\d{2})?",
                    r"\d+(?:\.\d+)?[KM]?\+ bought in past month",
                    r"[\d,]+ global ratings",
                    r"(?:In Stock|Currently unavailable|Temporarily out of stock"
                    r"|Only \d+ left in stock)",
                ),
                rendered_dom_contains=(
                    'name="currencyOfPreference" value="USD"',
                    "/gp/customer-reviews/",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="amazon_pdp_distribution",
            retailer="amazon",
            page_kind="pdp_distribution",
            hostname="www.amazon.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=0.0,
            derive_target_asin_from_url=True,
            requirements=_requirements(
                visible_text_contains=("New York 10001",),
                visible_text_regexes=(
                    r"\d(?:\.\d)? out of 5 stars",
                    r"\$\d+(?:\.\d{2})?",
                    r"\d+(?:\.\d+)?[KM]?\+ bought in past month",
                    r"[\d,]+ global ratings",
                    r"(?:In Stock|Currently unavailable|Temporarily out of stock"
                    r"|Only \d+ left in stock)",
                    r"(?s)5 star\s+\d+%\s+4 star\s+\d+%\s+3 star\s+\d+%"
                    r"\s+2 star\s+\d+%\s+1 star\s+\d+%",
                ),
                rendered_dom_contains=(
                    'name="currencyOfPreference" value="USD"',
                    "/gp/customer-reviews/",
                ),
                rendered_dom_regexes=(r"[\d,]+ customers mention",),
            ),
        ),
        RetailCaptureProfile(
            name="sephora_grid_aggregate",
            retailer="sephora",
            page_kind="grid_aggregate",
            hostname="www.sephora.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=0,
            load_more_selector="text=Show More Products",
            load_more_clicks=10,
            requirements_define_scroll_stop=False,
            requirements=_requirements(
                visible_text_contains=("Quicklook",),
                visible_text_regexes=(
                    r"\d+\s+Results",
                    r"\d+-\d+\s+of\s+\d+\s+Results",
                    r"\$\d+\.\d{2}",
                ),
                rendered_dom_contains=('id="linkStore"', '"nthBrand"'),
                rendered_dom_regexes=(
                    r'"products"\s*:\s*\[',
                    r'"totalProducts"\s*:\s*\d+',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="sephora_catalog_grid_aggregate",
            retailer="sephora",
            page_kind="grid_aggregate",
            hostname="www.sephora.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=0.0,
            scroll_passes=0,
            scroll_step_px=0,
            load_more_selector=None,
            load_more_clicks=0,
            requirements_define_scroll_stop=False,
            derive_target_sephora_catalog_from_url=True,
            requirements=_requirements(
                visible_text_contains=("Quicklook",),
                visible_text_regexes=(
                    r"\d+\s+Results",
                    r"1-\d+\s+of\s+\d+\s+Results",
                    r"Sort\s+by:\s*Bestselling",
                    r"\$\d+\.\d{2}",
                ),
                rendered_dom_contains=(
                    'data-cnstrc-browse="true"',
                    "Sephora.renderQueryParams",
                ),
                rendered_dom_regexes=(
                    r'data-cnstrc-num-results=["\']\d+["\']',
                    r'data-cnstrc-item-id=["\']P\d+["\']',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="sephora_pdp_aggregate",
            retailer="sephora",
            page_kind="pdp_aggregate",
            hostname="www.sephora.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=350,
            derive_target_sephora_product_id_from_url=True,
            requirements=_requirements(
                visible_text_contains=("Ratings & Reviews",),
                visible_text_regexes=(r"Ratings & Reviews \([^)]+\)", r"\$\d+\.\d{2}"),
                rendered_dom_contains=('id="linkStore"', '"product"'),
            ),
        ),
        RetailCaptureProfile(
            name="sephora_pdp_distribution",
            retailer="sephora",
            page_kind="pdp_distribution",
            hostname="www.sephora.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=350,
            scroll_target_selector="#ratings-reviews-container",
            requirements=_requirements(
                visible_text_contains=(
                    "Lip Sleeping Mask",
                    "Ratings & Reviews",
                    "Color",
                    "Summary",
                    "Verified Purchase",
                ),
                visible_text_regexes=(
                    r"Ratings & Reviews \([^)]+\)",
                    r"(?s)Summary\s+5\s+4\s+3\s+2\s+1\s+\d",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="luckyscent_pdp_aggregate",
            retailer="luckyscent",
            page_kind="pdp_aggregate",
            hostname="www.luckyscent.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=5.0,
            scroll_passes=4,
            scroll_step_px=500,
            requirements=_requirements(
                visible_text_contains=(
                    "Bread and Roses",
                    "Fragrance Notes",
                    "Customer Reviews",
                ),
                visible_text_regexes=(
                    r"(?s)Bread and Roses\s+Pearfat Parfum\s+\d(?:\.\d+)?\s+\(\d+\)\s+\$\d+",
                    r"(?s)Customer Reviews\s+\d(?:\.\d+)? out of 5",
                ),
                rendered_dom_contains=(
                    '"@type":"ProductGroup"',
                    'data-product-title="Bread and Roses"',
                ),
                rendered_dom_regexes=(
                    r'"hasVariant"\s*:\s*\[',
                    r'data-review-id="[^"]+"',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="nordstrom_pdp_aggregate",
            retailer="nordstrom",
            page_kind="pdp_aggregate",
            hostname="www.nordstrom.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=500,
            derive_target_nordstrom_product_id_from_url=True,
            requirements=_requirements(
                visible_text_contains=(
                    "Sold by Nordstrom",
                    "Reviews",
                ),
                visible_text_regexes=(
                    r"\$\d+(?:\.\d{2})?",
                    r"\d(?:\.\d+)? out of 5",
                ),
                rendered_dom_regexes=(
                    r'"@type"\s*:\s*"Product"',
                    r'"reviewCount"\s*:\s*(?:\"?\d+\"?)',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="ulta_grid_aggregate",
            retailer="ulta",
            page_kind="grid_aggregate",
            hostname="www.ulta.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            scroll_passes=1,
            load_more_selector="button.LoadContent__button",
            load_more_clicks=10,
            requirements_define_scroll_stop=False,
            requirements=_requirements(
                visible_text_contains=("Add to bag",),
                visible_text_regexes=(
                    r"You have viewed\s+\d+\s+of\s+\d+",
                    r"\$\d+\.\d{2}",
                ),
                rendered_dom_contains=(
                    'data-test="products-list"',
                    'data-test="products-list-item"',
                    "window.__APP_LOCALE__",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="ulta_category_grid_aggregate",
            retailer="ulta",
            page_kind="grid_aggregate",
            hostname="www.ulta.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=0.0,
            scroll_passes=0,
            load_more_selector=None,
            load_more_clicks=0,
            requirements_define_scroll_stop=False,
            requirements=_requirements(
                visible_text_contains=("Add to bag",),
                visible_text_regexes=(
                    r"\$\d+\.\d{2}",
                ),
                rendered_dom_contains=(
                    'data-test="products-list"',
                    'data-test="products-list-item"',
                    "window.__APP_LOCALE__",
                ),
                # The declared cohort count lives in the <title> ("N Products") on
                # every ?page=N page; unlike the view-triggered "You have viewed N of
                # M" footer it renders deterministically, so it is the admission
                # marker for the deterministic page traversal.
                rendered_dom_regexes=(
                    r"\d[\d,]*\s+Products",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="ulta_pdp_aggregate",
            retailer="ulta",
            page_kind="pdp_aggregate",
            hostname="www.ulta.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            derive_target_ulta_product_id_from_url=True,
            requirements=_requirements(
                visible_text_contains=("Reviews",),
                visible_text_regexes=(r"\d+(?:,\d+)* Reviews", r"\$\d+\.\d{2}"),
                rendered_dom_contains=("__APOLLO_STATE__",),
                rendered_dom_regexes=(r'"aggregateRating"', r'"availability"'),
            ),
        ),
        RetailCaptureProfile(
            name="ulta_pdp_distribution",
            retailer="ulta",
            page_kind="pdp_distribution",
            hostname="www.ulta.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            scroll_step_px=350,
            requirements=_requirements(
                visible_text_contains=(
                    "Night Shift Overnight Lip Mask",
                    "Reviews",
                    "RATINGS DISTRIBUTION",
                ),
                visible_text_regexes=(r"(?is)5 stars.*4 stars.*3 stars.*2 stars.*1 star",),
                rendered_dom_contains=("__APOLLO_STATE__",),
            ),
        ),
        RetailCaptureProfile(
            name="walmart_grid_aggregate",
            retailer="walmart",
            page_kind="grid_aggregate",
            hostname="www.walmart.com",
            source_surface="direct_http",
            ordinary_operation=True,
            requirements=_requirements(
                rendered_dom_contains=("__NEXT_DATA__",),
                rendered_dom_regexes=(r'"items"\s*:\s*\[\s*\{', r'"productId"'),
            ),
        ),
        RetailCaptureProfile(
            name="walmart_pdp_aggregate",
            retailer="walmart",
            page_kind="pdp_aggregate",
            hostname="www.walmart.com",
            source_surface="direct_http",
            ordinary_operation=True,
            requirements=_requirements(
                rendered_dom_contains=(
                    "__NEXT_DATA__",
                    "Vitamasques Cherry Vegan Collagen Lip Mask",
                ),
                rendered_dom_regexes=(r'"averageRating"\s*:', r'"numberOfReviews"\s*:'),
            ),
        ),
        RetailCaptureProfile(
            name="walmart_pdp_distribution",
            retailer="walmart",
            page_kind="pdp_distribution",
            hostname="www.walmart.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=5.0,
            scroll_step_px=400,
            requirements=_requirements(
                visible_text_contains=(
                    "Vitamasques Cherry Vegan Collagen Lip Mask",
                    "Customer ratings & reviews",
                    "Pickup",
                    "Shipping",
                ),
                visible_text_regexes=(r"(?s)5 stars.*4 stars.*3 stars.*2 stars.*1 star",),
            ),
        ),
        RetailCaptureProfile(
            name="revolve_grid_aggregate",
            retailer="revolve",
            page_kind="grid_aggregate",
            hostname="www.revolve.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=900,
            requirements_define_scroll_stop=False,
            derive_target_revolve_grid_subject_from_url=True,
            requirements=_requirements(
                visible_text_regexes=(
                    r"\$\d+(?:\.\d{2})?",
                ),
                rendered_dom_contains=(
                    "plp__product",
                    "Country Preference: US",
                    "$USD",
                ),
                rendered_dom_regexes=(
                    r"\d[\d,]*\s+Items?",
                    r'data-yotpo-product-id=["\'][A-Za-z0-9_-]+["\']',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="revolve_pdp_aggregate",
            retailer="revolve",
            page_kind="pdp_aggregate",
            hostname="www.revolve.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            wait_until="domcontentloaded",
            settle_seconds=5.0,
            scroll_passes=1,
            scroll_step_px=900,
            derive_target_revolve_style_id_from_url=True,
            requirements=_requirements(
                visible_text_contains=("Revolve Style No.",),
                visible_text_regexes=(
                    r"\$\d+(?:\.\d{2})?",
                ),
                rendered_dom_contains=(
                    "Country Preference: US",
                    "$USD",
                    "cdn-widgetsrepository.yotpo.com/v1/loader/",
                ),
                rendered_dom_regexes=(
                    r'data-yotpo-currency=["\']USD["\']',
                    r'"priceCurrency"\s*:\s*"USD"',
                ),
            ),
        ),
        RetailCaptureProfile(
            name="target_grid_aggregate",
            retailer="target",
            page_kind="grid_aggregate",
            hostname="www.target.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=6.0,
            scroll_passes=0,
            requirements_define_scroll_stop=False,
            derive_target_target_grid_subject_from_url=True,
            requirements=_requirements(
                visible_text_contains=("results",),
                visible_text_regexes=(r"\d+\s+results", r"\$\d+\.\d{2}"),
            ),
        ),
        RetailCaptureProfile(
            name="target_pdp_aggregate",
            retailer="target",
            page_kind="pdp_aggregate",
            hostname="www.target.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=6.0,
            derive_target_target_product_id_from_url=True,
            requirements=_requirements(
                visible_text_contains=(
                    "reviews",
                    "Pickup",
                    "Shipping",
                ),
                visible_text_regexes=(
                    r"\d(?:\.\d+)? out of 5 stars with \d+ reviews",
                    r"\$\d+\.\d{2}",
                ),
            ),
        ),
        RetailCaptureProfile(
            name="target_pdp_distribution",
            retailer="target",
            page_kind="pdp_distribution",
            hostname="www.target.com",
            source_surface="cloakbrowser_snapshot",
            ordinary_operation=True,
            settle_seconds=6.0,
            scroll_passes=1,
            requirements=_requirements(
                visible_text_contains=("BYOMA Liptide Lip Mask", "Guest ratings & reviews"),
                visible_text_regexes=(
                    r"(?s)5 stars\s+\d+%.*4 stars\s+\d+%.*3 stars\s+\d+%"
                    r".*2 stars\s+\d+%.*1 star\s+\d+%",
                ),
            ),
        ),
    )
}


def retail_capture_profile_names() -> tuple[str, ...]:
    return tuple(sorted(_PROFILES))


def get_retail_capture_profile(name: str) -> RetailCaptureProfile:
    try:
        return _PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"unknown retail capture profile: {name}") from exc


def validate_retail_capture_profile_route(
    profile: RetailCaptureProfile,
    *,
    url: str,
    source_family: str,
    source_surface: str,
) -> None:
    hostname = (urlparse(url).hostname or "").lower()
    if hostname != profile.hostname:
        raise ValueError(
            f"retail capture profile {profile.name} requires hostname {profile.hostname}; "
            f"got {hostname or 'none'}"
        )
    if source_family != "retail_pdp":
        raise ValueError(
            f"retail capture profile {profile.name} requires source_family retail_pdp"
        )
    if source_surface != profile.source_surface:
        raise ValueError(
            f"retail capture profile {profile.name} requires source_surface "
            f"{profile.source_surface}; "
            f"got {source_surface}"
        )


def merge_source_detail_sufficiency_requirements(
    first: SourceDetailSufficiencyRequirements | None,
    second: SourceDetailSufficiencyRequirements | None,
) -> SourceDetailSufficiencyRequirements | None:
    if first is None:
        return second
    if second is None:
        return first

    def unique(values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))

    minimums = [
        value
        for value in (first.min_visible_text_bytes, second.min_visible_text_bytes)
        if value is not None
    ]
    merged = SourceDetailSufficiencyRequirements(
        require_not_access_blocked=(
            first.require_not_access_blocked or second.require_not_access_blocked
        ),
        min_visible_text_bytes=max(minimums) if minimums else None,
        visible_text_contains=unique(first.visible_text_contains + second.visible_text_contains),
        visible_text_regexes=unique(first.visible_text_regexes + second.visible_text_regexes),
        rendered_dom_contains=unique(first.rendered_dom_contains + second.rendered_dom_contains),
        rendered_dom_regexes=unique(first.rendered_dom_regexes + second.rendered_dom_regexes),
    )
    validate_source_detail_sufficiency_requirements(merged)
    return merged
