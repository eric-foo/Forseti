from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Sequence
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import generate_ulid
from source_capture import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
    publish_completed_source_capture_packet,
    unknown_with_reason,
    write_local_source_capture_packet,
)

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot

from source_capture.adapters import CloakBrowserSnapshotFailure, fetch_cloakbrowser_snapshot_capture
from source_capture.adapters.amazon_delivery_location import (
    AmazonDeliveryLocationPlugin,
    AmazonSearchGridPlugin,
)
from source_capture.adapters.cloakbrowser_snapshot import (
    ALLOWED_WAIT_UNTIL,
    DEFAULT_MAX_ARTIFACT_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    CloakBrowserSnapshotEngine,
    CloakBrowserSnapshotFailureKind,
)
from source_capture.adapters.luckyscent_us_market import LuckyscentUSMarketPlugin
from source_capture.adapters.revolve_us_market import RevolveUSMarketPlugin
from source_capture.adapters.nordstrom_country_preference import (
    NORDSTROM_REVIEW_POSTURES,
    NordstromCountryPreferencePlugin,
    observe_nordstrom_deep_review_window,
    observe_nordstrom_review_window,
)
from source_capture.adapters.sephora_us_market import SephoraUSMarketPlugin
from source_capture.adapters.sephora_catalog_traversal import (
    SephoraCatalogTraversalPlugin,
)
from source_capture.adapters.target_delivery_location import (
    TargetDeliveryLocationPlugin,
    TargetGridPlugin,
)
from source_capture.adapters.ulta_us_market import UltaUSMarketPlugin
from source_capture.auth_state import AuthenticatedSessionMode
from source_capture.browser_user_data import browser_user_data_path_for_label
from source_capture.cli_support import (
    add_durability_arguments,
    build_intended_cadence,
    build_optional_fact,
    require_series_identity,
)
from source_capture.content_extraction import (
    CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    CONTENT_RECORD_FILENAME,
    RenderedContentExtractionSpec,
)
from source_capture.proxy_profiles import ProxyCategory, ProxyProfile, load_proxy_profile
from source_capture.retail_capture_profiles import (
    RetailCaptureProfile,
    get_retail_capture_profile,
    merge_source_detail_sufficiency_requirements,
    retail_capture_profile_names,
    target_bestseller_grid_url,
    validate_retail_capture_profile_route,
)
from source_capture.retail_grid_projection import (
    AMAZON_GRID_CONTENT_RECORD_VERSION,
    TARGET_GRID_CONTENT_RECORD_VERSION,
    append_retail_grid_observation_into_lake,
    build_amazon_grid_aggregate_content_record,
    build_retail_grid_observation,
    build_target_grid_aggregate_content_record,
    write_retail_grid_projection,
)
from source_capture.sephora_brand_grid import (
    SEPHORA_GRID_CONTENT_RECORD_VERSION,
    build_sephora_brand_grid_content_record,
)
from source_capture.sephora_catalog_grid import (
    SEPHORA_CATALOG_GRID_CONTENT_RECORD_VERSION,
    build_sephora_catalog_grid_aggregate_content_record,
    build_sephora_catalog_grid_content_record,
)
from source_capture.ulta_brand_grid import (
    ULTA_GRID_CONTENT_RECORD_VERSION,
    build_ulta_brand_grid_content_record,
)
from source_capture.revolve_brand_grid import (
    REVOLVE_GRID_PARSER_VERSION,
    build_revolve_brand_grid_content_record,
)
from source_capture.retail_pdp_content import (
    AMAZON_PDP_CONTENT_PROFILE,
    AMAZON_PDP_PARSER_VERSION,
    LUCKYSCENT_PDP_CONTENT_PROFILE,
    LUCKYSCENT_PDP_PARSER_VERSION,
    NORDSTROM_PDP_CONTENT_PROFILE,
    NORDSTROM_PDP_PARSER_VERSION,
    REVOLVE_PDP_CONTENT_PROFILE,
    REVOLVE_PDP_PARSER_VERSION,
    SEPHORA_PDP_CONTENT_PROFILE,
    SEPHORA_PDP_PARSER_VERSION,
    TARGET_PDP_CONTENT_PROFILE,
    TARGET_PDP_PARSER_VERSION,
    ULTA_PDP_CONTENT_PROFILE,
    ULTA_PDP_PARSER_VERSION,
    build_amazon_pdp_aggregate_content_record,
    build_luckyscent_pdp_aggregate_content_record,
    build_nordstrom_pdp_aggregate_content_record,
    build_revolve_pdp_aggregate_content_record,
    build_sephora_pdp_aggregate_content_record,
    build_target_pdp_aggregate_content_record,
    build_ulta_pdp_aggregate_content_record,
)
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


CLOAKBROWSER_SNAPSHOT_NON_CLAIMS = [
    "not content sufficiency proof",
    "not login or session capture",
    "not stored profile or cookie use",
    "not proxy use",
    "not credential injection",
    "not CAPTCHA solving",
    "not crawler or source discovery",
    "not Reddit-specific capture logic",
    "not API SDK use",
    "not OCR or image analysis",
    "not ECR design",
    "not Cleaning implementation",
    "not Judgment scoring",
    "not buyer proof",
    "not commercial-readiness logic",
]
_BROWSER_SECRET_PATTERNS = (
    re.compile(r"cf_clearance\s*=", re.IGNORECASE),
    re.compile(r'"name"\s*:\s*"cf_clearance"', re.IGNORECASE),
)
_BROWSER_SECRET_HEADER_PATTERN = re.compile(
    r"\b(?:Cookie|Set-Cookie)\s*:\s*[A-Za-z0-9_.-]+\s*=",
    re.IGNORECASE,
)
_BROWSER_SECRET_METADATA_PATTERNS = (
    re.compile(r"\b(?:Cookie|Set-Cookie)\s*:", re.IGNORECASE),
    re.compile(r'"(?:cookies|origins)"\s*:\s*\[', re.IGNORECASE),
)

SEPHORA_MARKET_PIN_FAILURE_MODE_CHANGE = "sephora_market_pin_failed"
_SEPHORA_HOSTS = frozenset({"sephora.com", "www.sephora.com"})
LUCKYSCENT_MARKET_PIN_FAILURE_MODE_CHANGE = "luckyscent_market_pin_failed"
LUCKYSCENT_OVERLAY_DISMISSAL_FAILURE_MODE_CHANGE = (
    "luckyscent_overlay_dismissal_failed"
)
_LUCKYSCENT_HOSTS = frozenset({"luckyscent.com", "www.luckyscent.com"})
NORDSTROM_COUNTRY_PIN_FAILURE_MODE_CHANGE = "nordstrom_country_pin_failed"
NORDSTROM_REVIEW_POSTURE_FAILURE_MODE_CHANGE = "nordstrom_review_posture_failed"
_NORDSTROM_HOSTS = frozenset({"nordstrom.com", "www.nordstrom.com"})
AMAZON_DELIVERY_PIN_FAILURE_MODE_CHANGE = "amazon_delivery_zip_pin_failed"
AMAZON_US_VPN_FALLBACK_REQUIRED_MODE_CHANGE = "amazon_us_vpn_fallback_required"
_AMAZON_US_HOSTS = frozenset({"amazon.com", "www.amazon.com"})
# Amazon and Target ZIP requests are optional local fulfillment context.
# US-facing catalog/PDP admission remains bound to the retailer profile's
# hostname, currency, identity, and content-sufficiency checks.
_AMAZON_SG_HOSTS = frozenset({"amazon.sg", "www.amazon.sg"})
TARGET_DELIVERY_PIN_FAILURE_MODE_CHANGE = "target_delivery_zip_pin_failed"
TARGET_GRID_CONTENT_PROFILE = "target_grid_aggregate"
AMAZON_GRID_CONTENT_PROFILE = "amazon_grid_aggregate"
SEPHORA_CATALOG_GRID_CONTENT_PROFILE = "sephora_catalog_grid_aggregate"
_SEPHORA_GRID_CONTENT_PROFILES = frozenset(
    {"sephora_grid_aggregate", SEPHORA_CATALOG_GRID_CONTENT_PROFILE}
)
_TARGET_HOSTS = frozenset({"target.com", "www.target.com"})
ULTA_MARKET_PIN_FAILURE_MODE_CHANGE = "ulta_market_pin_failed"
_ULTA_HOSTS = frozenset({"ulta.com", "www.ulta.com"})
REVOLVE_MARKET_PIN_FAILURE_MODE_CHANGE = "revolve_market_pin_failed"
_REVOLVE_HOSTS = frozenset({"revolve.com", "www.revolve.com"})
RETAIL_TARGET_IDENTITY_FAILURE_MODE_CHANGE = "retail_target_identity_failed"
_RETAIL_GRID_PROJECTION_PROFILES = frozenset(
    {
        "sephora_grid_aggregate",
        SEPHORA_CATALOG_GRID_CONTENT_PROFILE,
        "amazon_grid_aggregate",
        "target_grid_aggregate",
        "ulta_grid_aggregate",
        "ulta_category_grid_aggregate",
        "revolve_grid_aggregate",
    }
)
_ULTA_GRID_PROFILES = frozenset({"ulta_grid_aggregate", "ulta_category_grid_aggregate"})


def run_source_capture_cloakbrowser_packet(
    *,
    url: str,
    source_family: str,
    source_surface: str,
    decision_question: str,
    output_directory: Path | None = None,
    data_root: "DataLakeRoot | None" = None,
    capture_context: str,
    operator_category: str,
    capture_mode: CaptureModeCategory,
    session_id: str | None,
    proxy_profile: ProxyProfile | None,
    browser_user_data_label: str | None = None,
    browser_user_data_session_mode: AuthenticatedSessionMode | None = None,
    browser_user_data_dir: Path | None = None,
    actor_audience_context,
    visible_mode_changes: Sequence[str],
    source_publication_or_event,
    source_edit_or_version,
    cutoff_posture,
    recapture_time,
    re_capture_relationship,
    warnings: Sequence[str],
    limitations: Sequence[str],
    source_detail_sufficiency_requirements: SourceDetailSufficiencyRequirements | None = None,
    retail_capture_profile: RetailCaptureProfile | None = None,
    timeout_seconds: float,
    wait_until: str,
    viewport_width: int,
    viewport_height: int,
    max_artifact_bytes: int,
    block_heavy_assets: bool,
    settle_seconds: float = 0.0,
    scroll_passes: int = 0,
    load_more_selector: str | None = None,
    load_more_clicks: int | None = None,
    scroll_step_px: int = 0,
    scroll_target_selector: str | None = None,
    delivery_zip: str | None = None,
    delivery_zip_setup_timeout_seconds: float = 30.0,
    amazon_grid_page_count: int = 2,
    sephora_catalog_page_count: int = 2,
    nordstrom_country: str | None = None,
    nordstrom_country_setup_timeout_seconds: float = 45.0,
    nordstrom_review_posture: str | None = None,
    luckyscent_market: str | None = None,
    sephora_market: str | None = None,
    ulta_market: str | None = None,
    revolve_market: str | None = None,
    target_zip: str | None = None,
    target_zip_setup_timeout_seconds: float = 30.0,
    session_visibility_pin=None,
    locale_pin=None,
    currency_pin=None,
    variant_pin=None,
    series_id: str | None = None,
    cold_start_at=None,
    pre_coverage_history_posture=None,
    intended_cadence: dict[str, object] | None = None,
    content_extraction: RenderedContentExtractionSpec | None = None,
    retail_grid_projection_output: Path | None = None,
    retain_retail_grid_raw_sample: bool = False,
    capture_engine: CloakBrowserSnapshotEngine | None = None,
) -> tuple[int, str]:
    if (output_directory is None) == (data_root is None):
        raise ValueError("exactly one of output_directory or data_root is required")
    if browser_user_data_dir is not None and (
        browser_user_data_label is None or browser_user_data_session_mode is None
    ):
        raise ValueError(
            "browser_user_data_dir requires browser_user_data_label and browser_user_data_session_mode "
            "so the packet's visible-mode-change and non-claims provenance reflects the persistent "
            "profile load; a caller must not load a stored profile without disclosing it in the packet"
        )
    if retain_retail_grid_raw_sample and (
        data_root is None
        or retail_capture_profile is None
        or retail_capture_profile.name not in _RETAIL_GRID_PROJECTION_PROFILES
    ):
        raise ValueError(
            "retain_retail_grid_raw_sample requires --data-root and a retail grid profile"
        )

    if retail_capture_profile is not None:
        if retail_capture_profile.name == TARGET_GRID_CONTENT_PROFILE:
            url = target_bestseller_grid_url(url)
        if retail_capture_profile.name == SEPHORA_CATALOG_GRID_CONTENT_PROFILE:
            # Complete category pages come from retailer-owned PageJSON; keep
            # scrolling and Show More disabled for CLI and direct callers.
            settle_seconds = retail_capture_profile.settle_seconds
            scroll_passes = retail_capture_profile.scroll_passes
            scroll_step_px = retail_capture_profile.scroll_step_px
            load_more_selector = retail_capture_profile.load_more_selector
            load_more_clicks = retail_capture_profile.load_more_clicks
        if retail_capture_profile.source_surface != "cloakbrowser_snapshot":
            raise ValueError(
                f"retail capture profile {retail_capture_profile.name} belongs to "
                f"{retail_capture_profile.source_surface}; use the matching capture runner"
            )
        validate_retail_capture_profile_route(
            retail_capture_profile,
            url=url,
            source_family=source_family,
            source_surface=source_surface,
        )
        _validate_retail_baseline_profile_request(
            retail_capture_profile=retail_capture_profile,
            delivery_zip=delivery_zip,
            sephora_market=sephora_market,
            ulta_market=ulta_market,
            revolve_market=revolve_market,
            target_zip=target_zip,
        )
        source_detail_sufficiency_requirements = (
            merge_source_detail_sufficiency_requirements(
                source_detail_sufficiency_requirements,
                retail_capture_profile.requirements_for_capture(url=url),
            )
        )
        _validate_retail_grid_projection_request(
            retail_capture_profile=retail_capture_profile,
            retail_grid_projection_output=retail_grid_projection_output,
            data_root_mode=data_root is not None,
            sephora_market=sephora_market,
            ulta_market=ulta_market,
            revolve_market=revolve_market,
        )
        if retail_capture_profile.name == SEPHORA_PDP_CONTENT_PROFILE:
            if sephora_market != "US":
                raise ValueError(
                    "sephora_pdp_aggregate content capture requires --sephora-market US"
                )
            if content_extraction is None:
                content_extraction = _sephora_content_extraction_spec("content")
        if retail_capture_profile.name in _SEPHORA_GRID_CONTENT_PROFILES:
            if content_extraction is None:
                content_extraction = (
                    _sephora_catalog_grid_content_extraction_spec()
                    if retail_capture_profile.name
                    == SEPHORA_CATALOG_GRID_CONTENT_PROFILE
                    else _sephora_grid_content_extraction_spec()
                )
        if retail_capture_profile.name == LUCKYSCENT_PDP_CONTENT_PROFILE:
            if luckyscent_market != "US":
                raise ValueError(
                    "luckyscent_pdp_aggregate content capture requires --luckyscent-market US"
                )
            if content_extraction is None:
                content_extraction = _luckyscent_content_extraction_spec("content")
        if retail_capture_profile.name == NORDSTROM_PDP_CONTENT_PROFILE:
            if nordstrom_country != "US":
                raise ValueError(
                    "nordstrom_pdp_aggregate content capture requires "
                    "--nordstrom-country US"
                )
            if content_extraction is None:
                content_extraction = _nordstrom_content_extraction_spec("content")
        if retail_capture_profile.name == ULTA_PDP_CONTENT_PROFILE:
            if ulta_market != "US":
                raise ValueError(
                    "ulta_pdp_aggregate content capture requires --ulta-market US"
                )
            if content_extraction is None:
                content_extraction = _ulta_content_extraction_spec("content")
        if retail_capture_profile.name in _ULTA_GRID_PROFILES:
            if content_extraction is None:
                content_extraction = _ulta_grid_content_extraction_spec()
        if retail_capture_profile.name == REVOLVE_PDP_CONTENT_PROFILE:
            if revolve_market != "US":
                raise ValueError(
                    "revolve_pdp_aggregate content capture requires "
                    "--revolve-market US"
                )
            if content_extraction is None:
                content_extraction = _revolve_content_extraction_spec("content")
        if retail_capture_profile.name == "revolve_grid_aggregate":
            if content_extraction is None:
                content_extraction = _revolve_grid_content_extraction_spec()
        if retail_capture_profile.name == TARGET_PDP_CONTENT_PROFILE:
            if content_extraction is None:
                content_extraction = _target_content_extraction_spec("content")
        if retail_capture_profile.name == AMAZON_PDP_CONTENT_PROFILE:
            if content_extraction is None:
                content_extraction = _amazon_content_extraction_spec("content")
    if (
        retail_capture_profile is not None
        and load_more_selector is None
        and load_more_clicks is None
    ):
        load_more_selector = retail_capture_profile.load_more_selector
        load_more_clicks = retail_capture_profile.load_more_clicks
    elif load_more_clicks is None:
        load_more_clicks = 0
    if (
        retail_capture_profile is not None
        and retail_capture_profile.name == AMAZON_PDP_CONTENT_PROFILE
        and content_extraction is not None
    ):
        _validate_amazon_content_capture_envelope(
            requested_retention_mode=content_extraction.requested_retention_mode,
            scroll_passes=scroll_passes,
            scroll_step_px=scroll_step_px,
            scroll_target_selector=scroll_target_selector,
            load_more_clicks=load_more_clicks,
        )
    if nordstrom_review_posture is not None:
        if (
            retail_capture_profile is None
            or retail_capture_profile.name != NORDSTROM_PDP_CONTENT_PROFILE
        ):
            raise ValueError(
                "Nordstrom review posture requires nordstrom_pdp_aggregate"
            )
        if nordstrom_country != "US":
            raise ValueError(
                "Nordstrom review posture requires --nordstrom-country US"
            )
        if nordstrom_review_posture not in NORDSTROM_REVIEW_POSTURES:
            raise ValueError(
                "unsupported Nordstrom review posture "
                f"{nordstrom_review_posture!r}"
            )
        if load_more_clicks != 0:
            raise ValueError(
                "Nordstrom review postures own and record their adaptive six-row "
                "continuation actions; generic load-more clicks are forbidden"
            )

    site_specific_preferences = [
        delivery_zip is not None,
        nordstrom_country is not None,
        luckyscent_market is not None,
        sephora_market is not None,
        ulta_market is not None,
        revolve_market is not None,
        target_zip is not None,
    ]
    if sum(site_specific_preferences) > 1:
        raise ValueError(
            "only one site-specific pre-capture preference may be supplied: "
            "--delivery-zip, --nordstrom-country, --luckyscent-market, or "
            "--sephora-market, --ulta-market, --revolve-market, or --target-zip"
        )
    if (
        retail_capture_profile is not None
        and retail_capture_profile.name == AMAZON_GRID_CONTENT_PROFILE
    ):
        _validate_amazon_delivery_zip_url(url)
        pre_capture = AmazonSearchGridPlugin(
            target_url=url,
            page_count=amazon_grid_page_count,
            delivery_zip=delivery_zip,
            setup_timeout_seconds=delivery_zip_setup_timeout_seconds,
            traversal_timeout_seconds=timeout_seconds,
        )
        content_extraction = RenderedContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version=AMAZON_GRID_CONTENT_RECORD_VERSION,
            extractor=lambda _rendered_dom, _visible_text, _final_url: (
                build_amazon_grid_aggregate_content_record(
                    rendered_pages=pre_capture.grid_page_doms,
                    requested_url=url,
                    page_urls=pre_capture.grid_page_urls,
                    traversal_observation=pre_capture.grid_observation,
                )
            ),
        )
    elif (
        retail_capture_profile is not None
        and retail_capture_profile.name == SEPHORA_CATALOG_GRID_CONTENT_PROFILE
    ):
        if sephora_market != "US":
            raise ValueError(
                "sephora_catalog_grid_aggregate requires --sephora-market US"
            )
        pre_capture = SephoraCatalogTraversalPlugin(
            target_url=url,
            page_count=sephora_catalog_page_count,
            traversal_timeout_seconds=timeout_seconds,
        )
        content_extraction = RenderedContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version=SEPHORA_CATALOG_GRID_CONTENT_RECORD_VERSION,
            extractor=lambda _rendered_dom, _visible_text, _final_url: (
                build_sephora_catalog_grid_aggregate_content_record(
                    rendered_pages=pre_capture.grid_page_doms,
                    requested_url=url,
                    page_urls=pre_capture.grid_page_urls,
                    traversal_observation=pre_capture.grid_observation,
                )
            ),
        )
    elif delivery_zip is not None:
        _validate_amazon_delivery_zip_url(url)
        pre_capture = AmazonDeliveryLocationPlugin(
            delivery_zip=delivery_zip,
            setup_timeout_seconds=delivery_zip_setup_timeout_seconds,
        )
    elif nordstrom_country is not None:
        pre_capture = NordstromCountryPreferencePlugin(
            country_code=nordstrom_country,
            setup_timeout_seconds=nordstrom_country_setup_timeout_seconds,
            target_url=url,
            review_posture=nordstrom_review_posture,
        )
    elif luckyscent_market is not None:
        pre_capture = LuckyscentUSMarketPlugin(country_code=luckyscent_market)
    elif sephora_market is not None:
        _validate_sephora_us_market_url(url)
        pre_capture = SephoraUSMarketPlugin(
            target_url=url,
            country_code=sephora_market,
            page_kind=(
                "grid"
                if retail_capture_profile is not None
                and retail_capture_profile.name in _SEPHORA_GRID_CONTENT_PROFILES
                else "pdp"
            ),
        )
        if (
            retail_capture_profile is not None
            and retail_capture_profile.name in _SEPHORA_GRID_CONTENT_PROFILES
        ):
            content_extraction = (
                _sephora_catalog_grid_content_extraction_spec()
                if retail_capture_profile.name
                == SEPHORA_CATALOG_GRID_CONTENT_PROFILE
                else _sephora_grid_content_extraction_spec()
            )
    elif ulta_market is not None:
        ulta_page_kind = (
            "grid"
            if retail_capture_profile is not None
            and retail_capture_profile.name in _ULTA_GRID_PROFILES
            else "pdp"
        )
        ulta_sku = _validate_ulta_us_market_url(url, page_kind=ulta_page_kind)
        pre_capture = UltaUSMarketPlugin(
            target_url=url,
            sku=ulta_sku,
            country_code=ulta_market,
            page_kind=ulta_page_kind,
        )
        if ulta_page_kind == "grid":
            content_extraction = _ulta_grid_content_extraction_spec()
    elif revolve_market is not None:
        revolve_page_kind = (
            "grid"
            if retail_capture_profile is not None
            and retail_capture_profile.name == "revolve_grid_aggregate"
            else "pdp"
        )
        revolve_style_id = _validate_revolve_us_market_url(
            url, page_kind=revolve_page_kind
        )
        pre_capture = RevolveUSMarketPlugin(
            target_url=url,
            style_id=revolve_style_id,
            country_code=revolve_market,
            page_kind=revolve_page_kind,
        )
        if revolve_page_kind == "grid":
            content_extraction = _revolve_grid_content_extraction_spec()
    elif (
        retail_capture_profile is not None
        and retail_capture_profile.name == TARGET_GRID_CONTENT_PROFILE
    ):
        _validate_target_delivery_zip_url(url)
        pre_capture = TargetGridPlugin(
            target_url=url,
            delivery_zip=target_zip,
            setup_timeout_seconds=target_zip_setup_timeout_seconds,
            traversal_timeout_seconds=timeout_seconds,
            require_delivery_pin=target_zip is not None,
        )
        content_extraction = RenderedContentExtractionSpec(
            requested_retention_mode="content",
            extractor_version=TARGET_GRID_CONTENT_RECORD_VERSION,
            extractor=lambda _rendered_dom, _visible_text, _final_url: (
                build_target_grid_aggregate_content_record(
                    rendered_pages=pre_capture.grid_page_doms,
                    requested_url=url,
                    page_urls=pre_capture.grid_page_urls,
                    traversal_observation=pre_capture.grid_observation,
                )
            ),
        )
    elif target_zip is not None:
        _validate_target_delivery_zip_url(url)
        pre_capture = TargetDeliveryLocationPlugin(
            target_url=url,
            delivery_zip=target_zip,
            setup_timeout_seconds=target_zip_setup_timeout_seconds,
        )
    else:
        pre_capture = None
    capture_result = fetch_cloakbrowser_snapshot_capture(
        url=url,
        timeout_seconds=timeout_seconds,
        wait_until=wait_until,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        max_artifact_bytes=max_artifact_bytes,
        proxy_profile=proxy_profile,
        block_heavy_assets=block_heavy_assets,
        settle_seconds=settle_seconds,
        scroll_passes=scroll_passes,
        load_more_selector=load_more_selector,
        load_more_clicks=load_more_clicks,
        scroll_step_px=scroll_step_px,
        scroll_stop_condition=(
            retail_capture_profile.scroll_stop_condition()
            if retail_capture_profile is not None
            else None
        ),
        scroll_target_selector=(
            scroll_target_selector
            if scroll_target_selector is not None
            else retail_capture_profile.scroll_target_selector
            if retail_capture_profile is not None
            else None
        ),
        pre_capture=pre_capture,
        user_data_dir=browser_user_data_dir,
        engine=capture_engine,
    )
    if isinstance(capture_result, CloakBrowserSnapshotFailure):
        return 3, f"{_failure_report_token(capture_result.failure_kind)}: {capture_result.message}"

    if retail_capture_profile is not None:
        capture_result.metadata["retail_capture_profile"] = retail_capture_profile.metadata()

    packet_warnings = list(warnings) + capture_result.warning_notes
    packet_limitations = list(limitations) + capture_result.limitation_notes
    retail_target_identity_failure = _retail_target_identity_failure(
        retail_capture_profile=retail_capture_profile,
        requested_url=url,
        final_url=capture_result.final_url,
    )
    if retail_target_identity_failure is not None:
        packet_limitations.append(
            f"{RETAIL_TARGET_IDENTITY_FAILURE_MODE_CHANGE}: "
            f"{retail_target_identity_failure}; packet preserved but MUST NOT be "
            "admitted as evidence for the commissioned product"
        )
    sephora_pin_failure = _sephora_market_pin_failure(
        sephora_market=sephora_market,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if sephora_pin_failure is not None:
        packet_limitations.append(
            f"{SEPHORA_MARKET_PIN_FAILURE_MODE_CHANGE}: {sephora_pin_failure}; packet "
            "preserved but MUST NOT be admitted as the asserted Sephora storefront evidence"
        )
    nordstrom_pin_failure = _nordstrom_country_pin_failure(
        nordstrom_country=nordstrom_country,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if nordstrom_pin_failure is not None:
        packet_limitations.append(
            f"{NORDSTROM_COUNTRY_PIN_FAILURE_MODE_CHANGE}: "
            f"{nordstrom_pin_failure}; packet preserved but MUST NOT be admitted "
            "as Nordstrom US/USD storefront evidence"
        )
    nordstrom_review_observation = _nordstrom_review_posture_observation(
        requested_posture=nordstrom_review_posture,
        rendered_dom=capture_result.rendered_dom,
        capture_timestamp=capture_result.metadata.get("capture_timestamp"),
    )
    nordstrom_review_posture_failure = _nordstrom_review_posture_failure(
        observation=nordstrom_review_observation,
        before_snapshot_steps_completed=capture_result.metadata.get(
            "before_snapshot_steps_completed"
        ),
    )
    capture_result.metadata["nordstrom_review_window"] = (
        nordstrom_review_observation
    )
    capture_result.metadata["nordstrom_review_posture_confirmed"] = (
        nordstrom_review_posture is not None
        and nordstrom_review_posture_failure is None
    )
    if nordstrom_review_posture_failure is not None:
        packet_limitations.append(
            f"{NORDSTROM_REVIEW_POSTURE_FAILURE_MODE_CHANGE}: "
            f"{nordstrom_review_posture_failure}; packet preserved but MUST NOT be "
            "admitted as the Nordstrom onboarding review posture"
        )
    ulta_pin_failure = _ulta_market_pin_failure(
        ulta_market=ulta_market,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if ulta_pin_failure is not None:
        packet_limitations.append(
            f"{ULTA_MARKET_PIN_FAILURE_MODE_CHANGE}: {ulta_pin_failure}; packet "
            "preserved but MUST NOT be admitted as Ulta US/USD storefront evidence"
        )
    revolve_pin_failure = _revolve_market_pin_failure(
        revolve_market=revolve_market,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if revolve_pin_failure is not None:
        packet_limitations.append(
            f"{REVOLVE_MARKET_PIN_FAILURE_MODE_CHANGE}: {revolve_pin_failure}; "
            "packet preserved but MUST NOT be admitted as REVOLVE US/USD "
            "storefront evidence"
        )
    luckyscent_pin_failure = _luckyscent_market_pin_failure(
        luckyscent_market=luckyscent_market,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if luckyscent_pin_failure is not None:
        packet_limitations.append(
            f"{LUCKYSCENT_MARKET_PIN_FAILURE_MODE_CHANGE}: "
            f"{luckyscent_pin_failure}; packet preserved but MUST NOT be admitted "
            "as Luckyscent US/USD storefront evidence"
        )
    luckyscent_overlay_failure = _luckyscent_overlay_dismissal_failure(
        luckyscent_market=luckyscent_market,
        before_scroll_steps_completed=capture_result.metadata.get(
            "before_scroll_steps_completed"
        ),
        before_scroll_reason=capture_result.metadata.get(
            "before_scroll_reason"
        ),
    )
    if luckyscent_overlay_failure is not None:
        packet_limitations.append(
            f"{LUCKYSCENT_OVERLAY_DISMISSAL_FAILURE_MODE_CHANGE}: "
            f"{luckyscent_overlay_failure}; packet preserved but MUST NOT be "
            "admitted as unobstructed Luckyscent content evidence"
        )
    amazon_pin_failure = _amazon_delivery_pin_failure(
        delivery_zip=delivery_zip,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    amazon_vpn_fallback_reason = _amazon_us_vpn_fallback_reason(
        delivery_zip=delivery_zip,
        final_url=capture_result.final_url,
    )
    target_pin_failure = _target_delivery_pin_failure(
        target_zip=target_zip,
        final_url=capture_result.final_url,
        pin_confirmed=capture_result.metadata.get("pin_confirmed"),
    )
    if delivery_zip is not None:
        capture_result.metadata["amazon_us_vpn_fallback_required"] = (
            amazon_vpn_fallback_reason is not None
        )
        capture_result.metadata["amazon_us_vpn_fallback_trigger"] = (
            "final_marketplace_host_amazon_sg"
            if amazon_vpn_fallback_reason is not None
            else None
        )
    if amazon_pin_failure is not None:
        packet_limitations.append(
            f"{AMAZON_DELIVERY_PIN_FAILURE_MODE_CHANGE}: {amazon_pin_failure}; packet "
            "preserved but MUST NOT be admitted as Amazon US delivery-pinned evidence"
        )
    if amazon_vpn_fallback_reason is not None:
        packet_limitations.append(
            f"{AMAZON_US_VPN_FALLBACK_REQUIRED_MODE_CHANGE}: "
            f"{amazon_vpn_fallback_reason}; preserve this failed packet, then an "
            "operator or cold agent may activate the pre-existing Surfshark "
            "United States / New York route and repeat the exact capture once. "
            "The capture runner did not activate or verify the VPN; Amazon-owned "
            "US marketplace, exact USD, and delivery ZIP signals still decide admission"
        )
    if target_pin_failure is not None:
        packet_limitations.append(
            f"{TARGET_DELIVERY_PIN_FAILURE_MODE_CHANGE}: {target_pin_failure}; packet "
            "preserved but MUST NOT be admitted as Target US delivery-pinned evidence"
        )
    if block_heavy_assets:
        packet_limitations.append(
            "CloakBrowser snapshot blocked image, media, and font network resources to bound "
            "proxy bandwidth; rendered content sufficiency is not asserted"
        )
    sufficiency_result = evaluate_source_detail_sufficiency(
        requirements=source_detail_sufficiency_requirements,
        access_block_reason=capture_result.access_block_reason,
        visible_text=capture_result.visible_text,
        rendered_dom=capture_result.rendered_dom,
    )
    sufficiency_limitation = source_detail_sufficiency_limitation(sufficiency_result)
    if sufficiency_limitation is not None:
        packet_limitations.append(sufficiency_limitation)
    packet_visible_mode_changes = list(visible_mode_changes)
    if retail_target_identity_failure is not None:
        packet_visible_mode_changes.append(
            RETAIL_TARGET_IDENTITY_FAILURE_MODE_CHANGE
        )
    if sephora_pin_failure is not None:
        packet_visible_mode_changes.append(SEPHORA_MARKET_PIN_FAILURE_MODE_CHANGE)
    if nordstrom_pin_failure is not None:
        packet_visible_mode_changes.append(
            NORDSTROM_COUNTRY_PIN_FAILURE_MODE_CHANGE
        )
    if nordstrom_review_posture_failure is not None:
        packet_visible_mode_changes.append(
            NORDSTROM_REVIEW_POSTURE_FAILURE_MODE_CHANGE
        )
    elif nordstrom_review_posture is not None:
        assert nordstrom_review_observation is not None
        packet_visible_mode_changes.append(
            "Nordstrom review sort selected: Most Recent; "
            f"{nordstrom_review_observation['captured_review_count']} main-list "
            "rows retained across "
            f"{nordstrom_review_observation['continuation_activations']} "
            "Load 6 more reviews activations; 30-day status "
            f"{nordstrom_review_observation['status']}"
        )
    if ulta_pin_failure is not None:
        packet_visible_mode_changes.append(ULTA_MARKET_PIN_FAILURE_MODE_CHANGE)
    if revolve_pin_failure is not None:
        packet_visible_mode_changes.append(REVOLVE_MARKET_PIN_FAILURE_MODE_CHANGE)
    if luckyscent_pin_failure is not None:
        packet_visible_mode_changes.append(
            LUCKYSCENT_MARKET_PIN_FAILURE_MODE_CHANGE
        )
    if luckyscent_overlay_failure is not None:
        packet_visible_mode_changes.append(
            LUCKYSCENT_OVERLAY_DISMISSAL_FAILURE_MODE_CHANGE
        )
    if amazon_pin_failure is not None:
        packet_visible_mode_changes.append(AMAZON_DELIVERY_PIN_FAILURE_MODE_CHANGE)
    if amazon_vpn_fallback_reason is not None:
        packet_visible_mode_changes.append(AMAZON_US_VPN_FALLBACK_REQUIRED_MODE_CHANGE)
    if target_pin_failure is not None:
        packet_visible_mode_changes.append(TARGET_DELIVERY_PIN_FAILURE_MODE_CHANGE)
    sufficiency_mode_change = source_detail_sufficiency_mode_change(sufficiency_result)
    if sufficiency_mode_change is not None:
        packet_visible_mode_changes.append(sufficiency_mode_change)

    rendered_dom_for_packet = capture_result.rendered_dom
    if (
        retail_capture_profile is not None
        and retail_capture_profile.name == TARGET_GRID_CONTENT_PROFILE
    ):
        rendered_dom_for_packet = _strip_script_elements(rendered_dom_for_packet)
        packet_limitations.append(
            "Target grid security redaction removed script elements before packet "
            "staging because the retailer embeds ephemeral guest-session material; the "
            "sanitized multi-page content record remains the source-visible grid evidence"
        )
        packet_visible_mode_changes.append(
            "Target grid script elements removed before packet staging"
        )
    rendered_dom_bytes = rendered_dom_for_packet.encode("utf-8")
    visible_text_bytes = capture_result.visible_text.encode("utf-8")
    snapshot_metadata_bytes = (
        json.dumps(capture_result.metadata, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    input_artifacts = [
        ("rendered_dom", "cloakbrowser_rendered_dom.html", rendered_dom_bytes),
        ("visible_text", "cloakbrowser_visible_text.txt", visible_text_bytes),
        ("screenshot", "cloakbrowser_viewport_screenshot.png", capture_result.screenshot_png),
        (
            "browser_metadata",
            "cloakbrowser_snapshot_metadata.json",
            snapshot_metadata_bytes,
        ),
    ]
    if content_extraction is not None:
        _assert_no_browser_secret_bytes(
            (role, body)
            for role, _filename, body in input_artifacts
            if role != "screenshot"
        )
    extraction_failure: str | None = None
    content_record_bytes: bytes | None = None
    if (
        content_extraction is not None
        and content_extraction.requested_retention_mode == "content"
    ):
        try:
            record = content_extraction.extractor(
                rendered_dom_bytes,
                visible_text_bytes,
                capture_result.final_url,
            )
            if not isinstance(record, dict):
                raise TypeError(
                    "rendered content extractor must return a JSON object, "
                    f"got {type(record).__name__}"
                )
            serialization_options: dict[str, object] = {
                "sort_keys": True,
                "ensure_ascii": False,
            }
            if content_extraction.json_indent is None:
                serialization_options["separators"] = (",", ":")
            else:
                serialization_options["indent"] = content_extraction.json_indent
            content_record_bytes = (
                json.dumps(record, **serialization_options) + "\n"
            ).encode("utf-8")
            extraction_status = "succeeded"
        except Exception as exc:
            extraction_failure = f"{type(exc).__name__}: {exc}"
            extraction_status = f"failed: {extraction_failure}"
    elif content_extraction is not None:
        extraction_status = "not_attempted: raw retention requested"
    else:
        extraction_status = "not_configured"

    # A failed Target grid traversal still leaves whatever pages it reached in
    # hand, so content extraction can succeed over a partial corpus. That is an
    # admission failure like any other: preserve the raw inputs for diagnosis
    # instead of shipping a canonical-content-shaped record inside a packet that
    # MUST NOT be admitted. Amazon/Target fulfillment-pin failures are excluded:
    # they invalidate only local fulfillment claims, not otherwise sufficient
    # US-facing catalog or PDP content. Their raw inputs still survive alongside
    # the content record so the unresolved location is diagnosable.
    grid_traversal_failed = (
        retail_capture_profile is not None
        and retail_capture_profile.name
        in {TARGET_GRID_CONTENT_PROFILE, AMAZON_GRID_CONTENT_PROFILE}
        and capture_result.metadata.get("before_snapshot_steps_completed") is not True
    )
    retention_admission_failed = (
        capture_result.access_block_reason is not None
        or grid_traversal_failed
        or sephora_pin_failure is not None
        or nordstrom_pin_failure is not None
        or nordstrom_review_posture_failure is not None
        or ulta_pin_failure is not None
        or revolve_pin_failure is not None
        or luckyscent_pin_failure is not None
        or luckyscent_overlay_failure is not None
        or (sufficiency_result.enabled and not sufficiency_result.passed)
    )
    retail_grid_raw_sample = (
        retain_retail_grid_raw_sample
        and content_record_bytes is not None
        and not retention_admission_failed
        and extraction_failure is None
    )
    fulfillment_pin_failure_with_content = (
        (amazon_pin_failure is not None or target_pin_failure is not None)
        and content_record_bytes is not None
        and extraction_failure is None
        and not retention_admission_failed
    )
    raw_extraction_inputs_preserved = (
        content_extraction is None
        or content_extraction.requested_retention_mode == "raw"
        or extraction_failure is not None
        or retention_admission_failed
        or retail_grid_raw_sample
        or fulfillment_pin_failure_with_content
    )
    retention_outcome = (
        "raw_sample"
        if retail_grid_raw_sample
        else "content"
        if content_record_bytes is not None
        and (
            not raw_extraction_inputs_preserved
            or fulfillment_pin_failure_with_content
        )
        else "raw_failure"
        if extraction_failure is not None or retention_admission_failed
        else "raw"
    )
    preserved_by_role = {
        "rendered_dom": raw_extraction_inputs_preserved,
        "visible_text": raw_extraction_inputs_preserved,
        "screenshot": True,
        "browser_metadata": True,
    }
    artifacts = [
        (filename, body)
        for role, filename, body in input_artifacts
        if preserved_by_role[role]
    ]
    # The canonical content record ships only when the packet actually retained
    # canonical content. Extraction runs before admission is decided, so a pin,
    # sufficiency, or access failure can leave a successfully parsed record in
    # hand; retaining it would put a canonical-content-shaped artifact inside a
    # packet that MUST NOT be admitted. Discard it the way an extraction failure
    # never produces one -- the preserved rendered DOM and visible text re-derive
    # it at this extractor_version whenever a diagnosis needs it.
    content_record_retained = retention_outcome in {"content", "raw_sample"}
    if content_record_retained:
        assert content_record_bytes is not None
        artifacts.append((CONTENT_RECORD_FILENAME, content_record_bytes))
    if retail_grid_raw_sample:
        grid_pages = tuple(getattr(pre_capture, "grid_page_doms", ()) or ())
        if not grid_pages:
            grid_pages = (capture_result.rendered_dom,)
        sample_record = {
            "sample_version": "retail_grid_raw_sample_v1",
            "requested_url": capture_result.requested_url,
            "final_url": capture_result.final_url,
            "pages": [
                {
                    "page": index,
                    "rendered_dom_without_scripts": _strip_script_elements(page),
                }
                for index, page in enumerate(grid_pages, start=1)
            ],
        }
        sample_json_bytes = (
            json.dumps(sample_record, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        _assert_no_browser_secret_bytes(
            [("retail_grid_raw_sample", sample_json_bytes)]
        )
        sample_bytes = gzip.compress(sample_json_bytes, mtime=0)
        artifacts.append(("retail_grid_raw_sample_pages.json.gz", sample_bytes))
    if content_extraction is not None:
        content_extraction_metadata = {
            "requested_retention_mode": content_extraction.requested_retention_mode,
            "retention_outcome": retention_outcome,
            "extractor_version": content_extraction.extractor_version,
            "extraction_status": extraction_status,
            "inputs": [
                {
                    "role": role,
                    "filename": filename,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "byte_count": len(body),
                    "preserved": preserved_by_role[role],
                }
                for role, filename, body in input_artifacts
            ],
        }
        artifacts.append(
            (
                "content_extraction_metadata.json",
                (
                    json.dumps(content_extraction_metadata, indent=2, sort_keys=True)
                    + "\n"
                ).encode("utf-8"),
            )
        )
        if extraction_failure is not None:
            packet_limitations.append(
                "content extraction failed in flight; rendered DOM, visible text, "
                f"browser metadata, and screenshot preserved as fallback: {extraction_failure}"
            )
        elif retail_grid_raw_sample:
            packet_limitations.append(
                "explicit retail-grid QA sample: source bodies and the capture-time "
                "content record preserved; this does not make raw retention routine"
            )
        elif fulfillment_pin_failure_with_content:
            packet_limitations.append(
                "requested local fulfillment pin was not confirmed; canonical PDP "
                "content and raw inputs were both preserved for diagnosis, the run "
                "exited nonzero, and Cleaning must not admit the packet as pinned "
                "fulfillment evidence"
            )
        elif (
            content_extraction.requested_retention_mode == "content"
            and not raw_extraction_inputs_preserved
        ):
            packet_limitations.append(
                "derived-only retail-grid capture: transient source bodies discarded after "
                "successful projection filing"
                if retail_capture_profile is not None
                and retail_capture_profile.name in _RETAIL_GRID_PROJECTION_PROFILES
                else "content-retention packet: rendered DOM and visible text discarded after "
                "hashing; content record, browser metadata, and screenshot preserved"
            )
        elif content_extraction.requested_retention_mode == "content":
            packet_limitations.append(
                "content-retention admission failed; the extracted content record was "
                "discarded and rendered DOM and visible text preserved for diagnosis"
            )
        packet_visible_mode_changes.append(
            f"requested retention mode: {content_extraction.requested_retention_mode}"
        )
        if not raw_extraction_inputs_preserved:
            packet_visible_mode_changes.append(
                "rendered DOM and visible text hashed then discarded after successful "
                "capture-time extraction"
            )
        if content_record_retained:
            packet_visible_mode_changes.append(
                "capture-time rendered content record preserved"
            )
        if retail_grid_raw_sample:
            packet_visible_mode_changes.append(
                "explicit retail-grid raw sample retained with script-stripped traversed pages"
            )

    is_retail_grid = (
        retail_capture_profile is not None
        and retail_capture_profile.name in _RETAIL_GRID_PROJECTION_PROFILES
    )
    derived_only_grid_run = (
        data_root is not None and is_retail_grid and not raw_extraction_inputs_preserved
    )
    persist_raw_packet = not derived_only_grid_run
    grid_projection_path: Path | None = None
    grid_projection_failure: str | None = None
    raw_packet_path: Path | None = None
    staging_root: Path | None = None
    if data_root is not None:
        staging_parent = data_root.stage_raw_packet(generate_ulid())
        staging_root = staging_parent
    else:
        assert output_directory is not None
        staging_parent = output_directory.parent
        staging_parent.mkdir(parents=True, exist_ok=True)
    staged_paths = [staging_parent / filename for filename, _body in artifacts]
    if any(path.exists() for path in staged_paths):
        raise ValueError(
            "CloakBrowser snapshot staging files already exist in the output parent; clear them before rerunning"
        )

    written_paths: list[Path] = []
    try:
        for staged_path, (_filename, body) in zip(staged_paths, artifacts, strict=True):
            staged_path.write_bytes(body)
            written_paths.append(staged_path)

        timing = PacketTiming(
            source_publication_or_event=source_publication_or_event
            or unknown_with_reason("CloakBrowser snapshot adapter did not infer source publication or event timing"),
            source_edit_or_version=source_edit_or_version
            or unknown_with_reason("CloakBrowser snapshot adapter did not infer source edit or version timing"),
            capture_time=known_fact(str(capture_result.metadata["capture_timestamp"])),
            recapture_time=recapture_time
            or not_applicable("CloakBrowser snapshot packet did not model an earlier capture by default"),
            cutoff_posture=cutoff_posture
            or unknown_with_reason("CloakBrowser snapshot runner did not receive cutoff posture metadata"),
        )
        archive_posture = not_attempted("CloakBrowser snapshot adapter does not query archive or history services")
        media_posture = known_fact(
            "cloakbrowser_snapshot preserved a viewport screenshot; linked media files were not independently preserved"
        )
        access_posture = known_fact(
            _access_posture_value(
                proxy_profile=proxy_profile,
                access_block_reason=capture_result.access_block_reason,
                browser_user_data_session_mode=browser_user_data_session_mode,
            )
        )
        recapture_posture = re_capture_relationship or not_applicable(
            "no prior source capture packet was supplied for this CloakBrowser snapshot capture"
        )

        ephemeral_packet_directory = (
            staging_parent / "ephemeral_retail_grid_packet"
            if derived_only_grid_run
            else None
        )
        result = write_local_source_capture_packet(
            output_directory=(
                ephemeral_packet_directory
                if derived_only_grid_run
                else output_directory
            ),
            data_root=(data_root if persist_raw_packet else None),
            input_files=written_paths,
            source_family=source_family,
            source_surface=source_surface,
            source_locator=known_fact(capture_result.requested_url),
            decision_question=decision_question,
            capture_context=capture_context,
            actor_audience_context=actor_audience_context
            or unknown_with_reason("actor or audience context was not supplied to the CloakBrowser snapshot runner"),
            capture_mode=capture_mode,
            operator_category=operator_category,
            session_identity=session_id,
            visible_mode_changes=_visible_mode_changes(
                visible_mode_changes=packet_visible_mode_changes,
                browser_user_data_label=browser_user_data_label,
                browser_user_data_session_mode=browser_user_data_session_mode,
            ),
            source_publication_or_event=timing.source_publication_or_event,
            source_edit_or_version=timing.source_edit_or_version,
            cutoff_posture=timing.cutoff_posture,
            recapture_time=timing.recapture_time,
            access_posture=access_posture,
            archive_history_posture=archive_posture,
            media_modality_posture=media_posture,
            re_capture_relationship=recapture_posture,
            # Demand-durability series facts (Ob.17). Element 2 (series origin) + Element 4
            # (declared cadence) ride on the packet; Element 1 pins ride on the slice below.
            # All optional + forwarded verbatim, so a non-durability capture leaves them None
            # (back-compat; no manifest bump). Observed facts only, never weights (INV-1).
            series_id=series_id,
            cold_start_at=cold_start_at,
            pre_coverage_history_posture=pre_coverage_history_posture,
            intended_cadence=intended_cadence,
            source_slices=[
                SourceCaptureSlice(
                    slice_id="cloakbrowser_snapshot_01",
                    locator=known_fact(capture_result.final_url),
                    timing=timing,
                    access_posture=access_posture,
                    archive_history_posture=archive_posture,
                    media_modality_posture=media_posture,
                    re_capture_relationship=recapture_posture,
                    session_visibility_pin=session_visibility_pin,
                    locale_pin=locale_pin,
                    currency_pin=currency_pin,
                    variant_pin=variant_pin,
                    limitations=packet_limitations,
                    warning_notes=packet_warnings,
                    preserved_file_ids=[
                        f"file_{index:02d}" for index in range(1, len(artifacts) + 1)
                    ],
                )
            ],
            warnings=packet_warnings,
            limitations=packet_limitations,
            receipt_summary=_receipt_summary(
                source_family=source_family,
                access_block_reason=capture_result.access_block_reason,
                requested_retention_mode=(
                    content_extraction.requested_retention_mode
                    if content_extraction is not None
                    else None
                ),
                raw_extraction_inputs_preserved=raw_extraction_inputs_preserved,
                nordstrom_review_posture=nordstrom_review_posture,
            ),
            receipt_non_claims=_cloakbrowser_snapshot_non_claims(
                proxy_profile=proxy_profile,
                access_block_reason=capture_result.access_block_reason,
                browser_user_data_session_mode=browser_user_data_session_mode,
            ),
        )
        if persist_raw_packet:
            raw_packet_path = Path(result.output_directory)

        if (
            is_retail_grid
            and data_root is not None
            and not retention_admission_failed
            and extraction_failure is None
        ):
            try:
                body_by_file_id = {
                    preserved.file_id: body
                    for preserved, (_filename, body) in zip(
                        result.packet.preserved_files, artifacts, strict=True
                    )
                }
                assert content_extraction is not None
                observation = build_retail_grid_observation(
                    packet=result.packet,
                    raw_file_bytes_by_file_id=body_by_file_id,
                    captured_at=str(capture_result.metadata["capture_timestamp"]),
                    requested_url=capture_result.requested_url,
                    final_url=capture_result.final_url,
                    capture_profile=retail_capture_profile.name,
                    parser_version=content_extraction.extractor_version,
                    series_id=series_id,
                    retain_raw_sample=retail_grid_raw_sample,
                )
                if observation.completeness.status != "complete":
                    grid_projection_failure = (
                        "retail_grid_completeness_failed: "
                        f"status={observation.completeness.status}; "
                        + "; ".join(observation.completeness.residuals)
                    )
                    if derived_only_grid_run:
                        raw_packet_path = publish_completed_source_capture_packet(
                            data_root=data_root,
                            packet_directory=Path(result.output_directory),
                            packet_id=result.packet.packet_id,
                        )
                else:
                    grid_projection_path = append_retail_grid_observation_into_lake(
                        data_root=data_root,
                        observation=observation,
                    )
            except Exception as exc:
                grid_projection_failure = (
                    "retail_grid_projection_failed: "
                    f"{type(exc).__name__}: {exc}"
                )
                if derived_only_grid_run:
                    raw_packet_path = publish_completed_source_capture_packet(
                        data_root=data_root,
                        packet_directory=Path(result.output_directory),
                        packet_id=result.packet.packet_id,
                    )
    finally:
        for staging_path in written_paths:
            try:
                staging_path.unlink()
            except FileNotFoundError:
                pass
        if staging_root is not None:
            shutil.rmtree(staging_root, ignore_errors=True)
    if is_retail_grid and data_root is None:
        try:
            assert retail_grid_projection_output is not None
            projection = write_retail_grid_projection(
                packet_directory=Path(result.output_directory),
                output_path=retail_grid_projection_output,
            )
            grid_projection_path = retail_grid_projection_output
            if projection.completeness.status == "incomplete":
                grid_projection_failure = (
                    "retail_grid_completeness_failed: "
                    + "; ".join(projection.completeness.residuals)
                )
        except Exception as exc:
            grid_projection_failure = (
                "retail_grid_projection_failed: "
                f"{type(exc).__name__}: {exc}"
            )
    diagnostic_packet_path = raw_packet_path or Path(result.output_directory)
    if retail_target_identity_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{RETAIL_TARGET_IDENTITY_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {retail_target_identity_failure}",
        )
    if sephora_pin_failure is not None:
        projection_detail = (
            f"; projection preserved at {grid_projection_path}"
            if grid_projection_path is not None
            else f"; {grid_projection_failure}"
            if grid_projection_failure is not None
            else ""
        )
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{SEPHORA_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {sephora_pin_failure}{projection_detail}",
        )
    if grid_projection_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{grid_projection_failure}: packet preserved at {diagnostic_packet_path}; "
            f"projection={grid_projection_path or 'not_written'}",
        )
    if nordstrom_pin_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{NORDSTROM_COUNTRY_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {nordstrom_pin_failure}",
        )
    if nordstrom_review_posture_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{NORDSTROM_REVIEW_POSTURE_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {nordstrom_review_posture_failure}",
        )
    if ulta_pin_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{ULTA_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {ulta_pin_failure}",
        )
    if revolve_pin_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{REVOLVE_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {revolve_pin_failure}",
        )
    if luckyscent_pin_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{LUCKYSCENT_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {luckyscent_pin_failure}",
        )
    if luckyscent_overlay_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{LUCKYSCENT_OVERLAY_DISMISSAL_FAILURE_MODE_CHANGE}: packet "
            f"preserved at {diagnostic_packet_path}; "
            f"{luckyscent_overlay_failure}",
        )
    if amazon_pin_failure is not None:
        failure_tokens = [AMAZON_DELIVERY_PIN_FAILURE_MODE_CHANGE]
        if amazon_vpn_fallback_reason is not None:
            failure_tokens.append(AMAZON_US_VPN_FALLBACK_REQUIRED_MODE_CHANGE)
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{'+'.join(failure_tokens)}: packet preserved at "
            f"{diagnostic_packet_path}; {amazon_pin_failure}",
        )
    if target_pin_failure is not None:
        return (
            SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
            f"{TARGET_DELIVERY_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
            f"{diagnostic_packet_path}; {target_pin_failure}",
        )
    if sufficiency_result.enabled and not sufficiency_result.passed:
        return SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, source_detail_sufficiency_failure_message(
            output_directory=str(diagnostic_packet_path),
            result=sufficiency_result,
        )
    if extraction_failure is not None:
        return CONTENT_EXTRACTION_FAILED_EXIT_CODE, str(diagnostic_packet_path)
    if grid_projection_path is not None:
        if data_root is not None:
            sample_detail = (
                f"raw sample preserved at {raw_packet_path}; "
                if retail_grid_raw_sample
                else "raw sample not retained; "
            )
            return (
                0,
                f"{sample_detail}derived observation preserved at {grid_projection_path}",
            )
        return (
            0,
            f"raw packet preserved at {result.output_directory}; "
            f"projection preserved at {grid_projection_path}",
        )
    return 0, result.output_directory


def _write_text(path: Path, text: str) -> None:
    path.write_text(f"{text}\n", encoding="utf-8", newline="\n")


def _validate_sephora_us_market_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    country_switch = parse_qs(parsed.query).get("country_switch", [])
    if hostname not in _SEPHORA_HOSTS or not any(
        value.lower() == "us" for value in country_switch
    ):
        raise ValueError(
            "--sephora-market US requires a sephora.com URL with country_switch=us"
        )


def _retail_target_identity_failure(
    *,
    retail_capture_profile: RetailCaptureProfile | None,
    requested_url: str,
    final_url: str,
) -> str | None:
    if retail_capture_profile is None:
        return None
    expected = retail_capture_profile.target_product_identity_from_url(
        url=requested_url
    )
    if expected is None:
        return None
    observed = retail_capture_profile.target_product_identity_from_url(url=final_url)
    if observed is not None and observed.casefold() == expected.casefold():
        return None
    return (
        f"{retail_capture_profile.name} requested product {expected!r}, but the "
        f"final browser route encoded {observed!r}"
    )


def _validate_retail_baseline_profile_request(
    *,
    retail_capture_profile: RetailCaptureProfile,
    delivery_zip: str | None,
    sephora_market: str | None,
    ulta_market: str | None,
    target_zip: str | None,
    revolve_market: str | None = None,
) -> None:
    if retail_capture_profile.page_kind not in {"grid_aggregate", "pdp_aggregate"}:
        return
    if not retail_capture_profile.ordinary_operation:
        raise ValueError(
            f"retail capture profile {retail_capture_profile.name} is not admitted "
            "for ordinary operation; preserve the capability gap instead"
        )
    if retail_capture_profile.retailer in {"amazon", "target"}:
        # A ZIP is optional local fulfillment context. It is neither a US-surface
        # admission requirement nor restricted to a single commissioned value.
        return
    required_pin = {
        "sephora": (sephora_market, "US", "--sephora-market US"),
        "ulta": (ulta_market, "US", "--ulta-market US"),
        "revolve": (revolve_market, "US", "--revolve-market US"),
    }.get(retail_capture_profile.retailer)
    if required_pin is None:
        return
    actual, expected, flag = required_pin
    if actual != expected:
        raise ValueError(
            f"{retail_capture_profile.name} shallow baseline requires {flag}"
        )


def _validate_retail_grid_projection_request(
    *,
    retail_capture_profile: RetailCaptureProfile,
    retail_grid_projection_output: Path | None,
    data_root_mode: bool = False,
    sephora_market: str | None = None,
    ulta_market: str | None = None,
    revolve_market: str | None = None,
) -> None:
    if retail_capture_profile.name in _SEPHORA_GRID_CONTENT_PROFILES:
        if sephora_market != "US":
            raise ValueError(
                f"{retail_capture_profile.name} requires --sephora-market US"
            )
    elif retail_capture_profile.name in _ULTA_GRID_PROFILES:
        if ulta_market != "US":
            raise ValueError(
                f"{retail_capture_profile.name} requires --ulta-market US"
            )
    elif retail_capture_profile.name == "revolve_grid_aggregate":
        if revolve_market != "US":
            raise ValueError("revolve_grid_aggregate requires --revolve-market US")

    if retail_capture_profile.name in _RETAIL_GRID_PROJECTION_PROFILES:
        if data_root_mode and retail_grid_projection_output is not None:
            raise ValueError(
                "--retail-grid-projection-output is forbidden in --data-root mode; "
                "retail-grid projection filing is automatic"
            )
        if not data_root_mode and retail_grid_projection_output is None:
            raise ValueError(
                f"{retail_capture_profile.name} requires "
                "--retail-grid-projection-output"
            )
    elif retail_grid_projection_output is not None:
        raise ValueError(
            "--retail-grid-projection-output currently requires an admitted "
            "Amazon, Sephora, Target, Ulta, or REVOLVE grid profile"
        )


def _sephora_market_pin_failure(
    *,
    sephora_market: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if sephora_market is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _SEPHORA_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, not sephora.com"
        )
    if pin_confirmed is not True:
        reasons.append("required rendered-market assertion was not confirmed")
    return "; ".join(reasons) if reasons else None


def _sephora_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=SEPHORA_PDP_PARSER_VERSION,
        json_indent=None,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_sephora_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _sephora_grid_content_extraction_spec() -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode="content",
        extractor_version=SEPHORA_GRID_CONTENT_RECORD_VERSION,
        json_indent=None,
        extractor=lambda rendered_dom, _visible_text, final_url: (
            build_sephora_brand_grid_content_record(
                rendered_dom=rendered_dom.decode("utf-8", errors="replace"),
                final_url=final_url,
            )
        ),
    )


def _sephora_catalog_grid_content_extraction_spec() -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode="content",
        extractor_version=SEPHORA_CATALOG_GRID_CONTENT_RECORD_VERSION,
        json_indent=None,
        extractor=lambda rendered_dom, _visible_text, final_url: (
            build_sephora_catalog_grid_content_record(
                rendered_dom=rendered_dom.decode("utf-8", errors="replace"),
                final_url=final_url,
            )
        ),
    )


def _nordstrom_country_pin_failure(
    *,
    nordstrom_country: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if nordstrom_country is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _NORDSTROM_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, "
            "not nordstrom.com"
        )
    if pin_confirmed is not True:
        reasons.append("US/USD rendered-storefront conjunction was not confirmed")
    return "; ".join(reasons) if reasons else None


def _nordstrom_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=NORDSTROM_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_nordstrom_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _nordstrom_review_posture_observation(
    *,
    requested_posture: str | None,
    rendered_dom: str,
    capture_timestamp: object,
) -> dict[str, object] | None:
    if requested_posture is None:
        return None
    if requested_posture in {"most_helpful_100", "most_recent_100"}:
        return observe_nordstrom_deep_review_window(
            rendered_dom,
            requested_sort=(
                "Most Helpful"
                if requested_posture == "most_helpful_100"
                else "Most Recent"
            ),
            limit=100,
        )
    if not isinstance(capture_timestamp, str):
        return {
            "admitted": False,
            "status": "invalid",
            "reason": "capture timestamp unavailable",
        }
    try:
        reference_date = date.fromisoformat(capture_timestamp[:10])
    except ValueError:
        return {
            "admitted": False,
            "status": "invalid",
            "reason": "capture timestamp malformed",
        }
    return observe_nordstrom_review_window(
        rendered_dom,
        reference_date=reference_date,
    )


def _nordstrom_review_posture_failure(
    *,
    observation: dict[str, object] | None,
    before_snapshot_steps_completed: object,
) -> str | None:
    if observation is None:
        return None
    reasons: list[str] = []
    if before_snapshot_steps_completed is not True:
        reasons.append("site-owned review-order selection did not complete")
    if observation.get("admitted") is not True:
        reasons.append(
            "bounded requested review coverage was not admitted "
            f"(status={observation.get('status')}, "
            f"review_ids={observation.get('review_ids')})"
        )
    return "; ".join(reasons) if reasons else None


def _validate_ulta_us_market_url(
    url: str, *, page_kind: Literal["pdp", "grid"] = "pdp"
) -> str | None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if page_kind == "grid":
        path = parsed.path.rstrip("/")
        if hostname not in _ULTA_HOSTS or not (
            re.fullmatch(r"/brand/[a-z0-9][a-z0-9-]*", path)
            or re.fullmatch(r"/shop/[a-z0-9][a-z0-9-]*/all", path)
        ):
            raise ValueError(
                "--ulta-market US grid capture requires an exact "
                "ulta.com/brand/<slug> or ulta.com/shop/<category>/all URL"
            )
        return None
    sku_values = parse_qs(parsed.query).get("sku", [])
    if (
        hostname not in _ULTA_HOSTS
        or len(sku_values) != 1
        or not sku_values[0].isdigit()
    ):
        raise ValueError(
            "--ulta-market US requires an ulta.com PDP URL with exactly one numeric sku"
        )
    return sku_values[0]


def _ulta_market_pin_failure(
    *,
    ulta_market: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if ulta_market is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _ULTA_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, not ulta.com"
        )
    if pin_confirmed is not True:
        reasons.append("US/USD rendered-market conjunction was not confirmed")
    return "; ".join(reasons) if reasons else None


def _validate_revolve_us_market_url(
    url: str, *, page_kind: Literal["pdp", "grid"] = "pdp"
) -> str | None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in _REVOLVE_HOSTS or parsed.scheme != "https":
        raise ValueError("--revolve-market US requires an HTTPS revolve.com URL")
    if page_kind == "grid":
        if not re.fullmatch(
            r"/[a-z0-9][a-z0-9-]*/br/[a-f0-9]{6}",
            parsed.path.rstrip("/"),
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "--revolve-market US grid capture requires "
                "/<brand>/br/<brand-id>"
            )
        return None
    match = re.search(
        r"/dp/(?P<style_id>[A-Z0-9]{2,12}-[A-Z]{1,4}\d+)/?$",
        parsed.path,
        flags=re.IGNORECASE,
    )
    if match is None:
        raise ValueError(
            "--revolve-market US PDP capture requires /dp/<REVOLVE-style-id>"
        )
    return match.group("style_id").upper()


def _revolve_market_pin_failure(
    *,
    revolve_market: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if revolve_market is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _REVOLVE_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, "
            "not revolve.com"
        )
    if pin_confirmed is not True:
        reasons.append("US/USD rendered-market conjunction was not confirmed")
    return "; ".join(reasons) if reasons else None


def _luckyscent_market_pin_failure(
    *,
    luckyscent_market: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if luckyscent_market is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _LUCKYSCENT_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, "
            "not luckyscent.com"
        )
    if pin_confirmed is not True:
        reasons.append("US/USD rendered-market conjunction was not confirmed")
    return "; ".join(reasons) if reasons else None


def _luckyscent_overlay_dismissal_failure(
    *,
    luckyscent_market: str | None,
    before_scroll_steps_completed: object,
    before_scroll_reason: object,
) -> str | None:
    # Only an affirmative completed receipt admits content: ``True`` covers both
    # an absent modal and a successful dismissal, ``False`` is a failed
    # dismissal, and ``None``/missing means the receipt never arrived.
    if luckyscent_market is None or before_scroll_steps_completed is True:
        return None
    if isinstance(before_scroll_reason, str) and before_scroll_reason.strip():
        return before_scroll_reason.strip()
    if before_scroll_steps_completed is False:
        return "route-owned pre-scroll overlay action did not complete"
    return "route-owned pre-scroll overlay outcome was not recorded"


def _luckyscent_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=LUCKYSCENT_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_luckyscent_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _ulta_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=ULTA_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_ulta_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _ulta_grid_content_extraction_spec() -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode="content",
        extractor_version=ULTA_GRID_CONTENT_RECORD_VERSION,
        json_indent=None,
        extractor=lambda rendered_dom, _visible_text, final_url: (
            build_ulta_brand_grid_content_record(
                rendered_dom=rendered_dom.decode("utf-8", errors="replace"),
                final_url=final_url,
            )
        ),
    )


def _revolve_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=REVOLVE_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_revolve_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            ).model_dump(mode="json")
        ),
    )


def _revolve_grid_content_extraction_spec() -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode="content",
        extractor_version=REVOLVE_GRID_PARSER_VERSION,
        json_indent=None,
        extractor=lambda rendered_dom, _visible_text, final_url: (
            build_revolve_brand_grid_content_record(
                rendered_dom=rendered_dom.decode("utf-8", errors="replace"),
                final_url=final_url,
            )
        ),
    )


def _amazon_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=AMAZON_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_amazon_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _validate_amazon_content_capture_envelope(
    *,
    requested_retention_mode: str,
    scroll_passes: int,
    scroll_step_px: int,
    scroll_target_selector: str | None,
    load_more_clicks: int,
) -> None:
    """Fail before navigation when generic actions exceed Amazon's bound envelope."""
    if requested_retention_mode != "content":
        return
    if scroll_passes != 0 or scroll_step_px != 0:
        raise ValueError(
            "amazon_pdp_aggregate content capture permits only the optional "
            "bounded --scroll-target-selector #customerReviews action; generic "
            "scroll passes and progressive scrolling are forbidden"
        )
    if scroll_target_selector not in {None, "#customerReviews"}:
        raise ValueError(
            "amazon_pdp_aggregate content capture may scroll only to #customerReviews"
        )
    if load_more_clicks != 0:
        raise ValueError(
            "amazon_pdp_aggregate content capture forbids generic load-more, "
            "pagination, and review-portal actions"
        )


def _target_content_extraction_spec(mode: str) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version=TARGET_PDP_PARSER_VERSION,
        extractor=lambda rendered_dom, visible_text, final_url: (
            build_target_pdp_aggregate_content_record(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                source_url=final_url,
            )
        ),
    )


def _validate_amazon_delivery_zip_url(url: str) -> None:
    hostname = (urlparse(url).hostname or "").lower()
    if hostname not in _AMAZON_US_HOSTS:
        raise ValueError(
            "--delivery-zip is Amazon-specific and requires an amazon.com capture URL"
        )


def _amazon_delivery_pin_failure(
    *,
    delivery_zip: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if delivery_zip is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _AMAZON_US_HOSTS:
        reasons.append(
            f"final marketplace host was {final_hostname or 'unknown'!r}, not amazon.com"
        )
    if pin_confirmed is not True:
        reasons.append(
            f"requested ZIP {delivery_zip!r} was not confirmed on the captured page"
        )
    return "; ".join(reasons) if reasons else None


def _amazon_us_vpn_fallback_reason(
    *,
    delivery_zip: str | None,
    final_url: str,
) -> str | None:
    """Return a typed recovery reason only for an Amazon-US attempt that lands in SG.

    The runner does not activate or verify a VPN. This narrow classifier lets a cold
    operator distinguish the owner-authorized Surfshark recovery case from selector
    drift, a missing ZIP anchor, or an unrelated marketplace redirect.
    """

    if delivery_zip is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    if final_hostname not in _AMAZON_SG_HOSTS:
        return None
    return (
        f"requested Amazon US delivery ZIP {delivery_zip!r} landed on "
        f"Amazon Singapore host {final_hostname!r}"
    )


def _validate_target_delivery_zip_url(url: str) -> None:
    hostname = (urlparse(url).hostname or "").lower()
    if hostname not in _TARGET_HOSTS:
        raise ValueError(
            "--target-zip is Target-specific and requires a target.com capture URL"
        )


def _target_delivery_pin_failure(
    *,
    target_zip: str | None,
    final_url: str,
    pin_confirmed: object,
) -> str | None:
    if target_zip is None:
        return None
    final_hostname = (urlparse(final_url).hostname or "").lower()
    reasons: list[str] = []
    if final_hostname not in _TARGET_HOSTS:
        reasons.append(
            f"final storefront host was {final_hostname or 'unknown'!r}, not target.com"
        )
    if pin_confirmed is not True:
        reasons.append(
            f"requested Target shipping ZIP {target_zip!r} was not confirmed"
        )
    return "; ".join(reasons) if reasons else None


def _assert_no_browser_secret_bytes(inputs) -> None:
    for role, body in inputs:
        sample = body.decode("utf-8", errors="ignore")
        for pattern in _BROWSER_SECRET_PATTERNS:
            if pattern.search(sample):
                raise ValueError(
                    "browser-secret material is forbidden in rendered content input "
                    f"{role}: {pattern.pattern}"
                )
        role_patterns = (
            _BROWSER_SECRET_METADATA_PATTERNS
            if role == "browser_metadata"
            else (_BROWSER_SECRET_HEADER_PATTERN,)
        )
        for pattern in role_patterns:
            if pattern.search(sample):
                raise ValueError(
                    "browser-secret material is forbidden in rendered content input "
                    f"{role}: {pattern.pattern}"
                )


def _strip_script_elements(rendered_dom: str) -> str:
    return re.sub(
        r"<script\b[^>]*>.*?</script\s*>",
        "",
        rendered_dom,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _failure_report_token(failure_kind: CloakBrowserSnapshotFailureKind) -> str:
    if failure_kind == CloakBrowserSnapshotFailureKind.DEPENDENCY_UNAVAILABLE:
        return "cloakbrowser_dependency_unavailable"
    if failure_kind == CloakBrowserSnapshotFailureKind.ACCESS_BLOCKED:
        return "cloakbrowser_access_blocked"
    return f"cloakbrowser_{failure_kind.value}"


def _access_posture_value(
    *,
    proxy_profile: ProxyProfile | None,
    access_block_reason: str | None,
    browser_user_data_session_mode: AuthenticatedSessionMode | None = None,
) -> str:
    profile_clause = (
        f" using label-indirected local browser profile with {browser_user_data_session_mode.value}"
        if browser_user_data_session_mode is not None
        else ""
    )
    anonymous_clause = "" if browser_user_data_session_mode is not None else " anonymous"
    if access_block_reason is not None:
        base = (
            "cloakbrowser_snapshot access_failed with access block "
            f"{access_block_reason}; rendered block artifacts preserved through{anonymous_clause} "
            f"anti-blocking browser capture{profile_clause}"
        )
        if proxy_profile is None:
            return f"{base}; content sufficiency is not asserted"
        return (
            f"{base} with label-indirected proxy category {proxy_profile.proxy_category.value}; "
            "endpoint, credentials, and exit IP were not recorded; content sufficiency is not asserted"
        )
    if proxy_profile is None:
        return (
            "cloakbrowser_snapshot preserved rendered browser artifacts through"
            f"{anonymous_clause} anti-blocking browser capture{profile_clause}; "
            "content sufficiency is not asserted"
        )
    return (
        "cloakbrowser_snapshot preserved rendered browser artifacts through"
        f"{anonymous_clause} anti-blocking browser capture{profile_clause} with label-indirected proxy category {proxy_profile.proxy_category.value}; endpoint, credentials, "
        "and exit IP were not recorded; content sufficiency is not asserted"
    )


def _receipt_summary(
    *,
    source_family: str,
    access_block_reason: str | None,
    requested_retention_mode: str | None = None,
    raw_extraction_inputs_preserved: bool = True,
    nordstrom_review_posture: str | None = None,
) -> str:
    if access_block_reason is not None:
        summary = (
            f"CloakBrowser snapshot packet for {source_family} with rendered access-block artifacts "
            f"preserved for one supplied URL; source content was not captured: {access_block_reason}."
        )
    elif raw_extraction_inputs_preserved:
        summary = (
            f"CloakBrowser snapshot packet for {source_family} with rendered DOM, visible text, "
            f"viewport screenshot, and method-provenance metadata preserved for one supplied URL."
        )
    else:
        summary = (
            f"CloakBrowser snapshot packet for {source_family} with a capture-time content record, "
            "viewport screenshot, and method-provenance metadata preserved; rendered DOM and "
            "visible text were hashed then discarded after successful extraction."
        )
    if requested_retention_mode is not None:
        summary += f" Requested retention mode: {requested_retention_mode}."
    if nordstrom_review_posture == "recent_window_30d":
        summary += (
            " Nordstrom onboarding review posture: most-helpful positive/critical "
            "pair plus all last-30-day reviews, then up to 30 Most Recent rows when "
            "that cohort has fewer than 12; each continuation activation adds six "
            "rows and is recorded."
        )
    elif nordstrom_review_posture in {"most_helpful_100", "most_recent_100"}:
        label = (
            "Most Helpful"
            if nordstrom_review_posture == "most_helpful_100"
            else "Most Recent"
        )
        summary += (
            f" Nordstrom deep review posture: first up to 100 rows in native {label} "
            "order; six-row continuation activations and provider batch overrun "
            "are recorded."
        )
    return summary


def _cloakbrowser_snapshot_non_claims(
    *,
    proxy_profile: ProxyProfile | None,
    access_block_reason: str | None,
    browser_user_data_session_mode: AuthenticatedSessionMode | None = None,
) -> list[str]:
    if proxy_profile is None:
        base: list[str] = list(CLOAKBROWSER_SNAPSHOT_NON_CLAIMS)
    else:
        base = [
            item
            for item in CLOAKBROWSER_SNAPSHOT_NON_CLAIMS
            if item != "not proxy use"
        ] + [
            "not proxy endpoint or credential disclosure",
            "not proxy success or block-evasion proof",
        ]
    if browser_user_data_session_mode is not None:
        base = [
            item
            for item in base
            if item not in {"not login or session capture", "not stored profile or cookie use"}
        ] + [
            "not password-driven login automation",
            "not raw cookie, storage-state, or profile path disclosure",
            "not session effectiveness proof",
        ]
    if access_block_reason is not None:
        return ["not source-content capture; access-block page artifacts only"] + base
    return base


def _visible_mode_changes(
    *,
    visible_mode_changes: Sequence[str],
    browser_user_data_label: str | None = None,
    browser_user_data_session_mode: AuthenticatedSessionMode | None = None,
) -> list[str]:
    values = list(visible_mode_changes)
    if browser_user_data_label is not None and browser_user_data_session_mode is not None:
        values.append(
            "cloakbrowser_persistent_profile_loaded:"
            f"{browser_user_data_session_mode.value}:{browser_user_data_label}"
        )
    return values


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture one URL through anonymous CloakBrowser and write a Source Capture Packet."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-family", default="web_page")
    parser.add_argument("--source-surface", default="cloakbrowser_snapshot")
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        default=None,
        help="Commit into the Forseti data lake at this root; explicit --data-root is mutually exclusive with --output. FORSETI_DATA_ROOT is used only when --output is omitted; legacy ORCA_DATA_ROOT is also accepted.",
    )
    parser.add_argument(
        "--capture-context",
        default=None,
    )
    parser.add_argument("--operator-category", default="cloakbrowser_snapshot_cli_operator")
    parser.add_argument(
        "--capture-mode",
        choices=[item.value for item in CaptureModeCategory],
        default=CaptureModeCategory.MULTIMODAL.value,
    )
    parser.add_argument(
        "--retention-mode",
        choices=["content", "raw"],
        default=None,
        help=(
            "Retention mode for the enabled Sephora, Luckyscent, Nordstrom, "
            "Ulta, Target, Amazon, and REVOLVE aggregate routes. Omitted defaults those "
            "routes to content; other profiles remain raw."
        ),
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--wait-until",
        choices=sorted(ALLOWED_WAIT_UNTIL),
        default=None,
        help=(
            "Navigation completion event. Default 'load' without a retail profile; "
            "otherwise the profile's measured posture."
        ),
    )
    parser.add_argument("--viewport-width", type=int, default=DEFAULT_VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=DEFAULT_VIEWPORT_HEIGHT)
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument(
        "--retail-capture-profile",
        choices=retail_capture_profile_names(),
        default=None,
        help=(
            "Compile a named retailer/page-kind success profile into the existing post-capture "
            "source-detail sufficiency gate and record its expected route flags."
        ),
    )
    parser.add_argument(
        "--retail-grid-projection-output",
        type=Path,
        default=None,
        help=(
            "Required in local --output mode for admitted Amazon, Sephora, Target, Ulta, and REVOLVE "
            "aggregate grids. Forbidden in --data-root mode, where the hash-verified, "
            "view-only projection is filed automatically."
        ),
    )
    parser.add_argument(
        "--retain-retail-grid-raw-sample",
        action="store_true",
        help=(
            "With --data-root and a retail grid profile, retain this successful capture "
            "as an explicit raw QA sample. Routine successful grid captures keep only "
            "their derived observation; failures retain diagnostic raw evidence."
        ),
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=None,
        help=(
            "Seconds to wait after the load event before capturing, so client-rendered (SPA) "
            "content (e.g. a search/listing grid) can populate. Default 0 without a retail "
            "profile; otherwise the profile's measured posture."
        ),
    )
    parser.add_argument(
        "--scroll-passes",
        type=int,
        default=None,
        help=(
            "After the settle, scroll to the bottom this many times (pausing between) so "
            "lazy-loaded / 'load more' / infinite-scroll content (e.g. product reviews) "
            "populates. Default 0 without a retail profile; otherwise the profile posture."
        ),
    )
    parser.add_argument(
        "--load-more-selector",
        default=None,
        help=(
            "Selector (CSS or 'text=...') for a click-to-load-more control, e.g. "
            "'text=Show more'. Without an explicit value, a retail profile may own the selector."
        ),
    )
    parser.add_argument(
        "--load-more-clicks",
        type=int,
        default=None,
        help=(
            "After scrolling, click --load-more-selector up to this many times (pausing between), "
            "stopping early when it disappears. Default 0 without a retail profile; otherwise "
            "the profile's bounded continuation posture."
        ),
    )
    parser.add_argument(
        "--scroll-step-px",
        type=int,
        default=None,
        help=(
            "Before any scroll-to-bottom passes, scroll down incrementally by this many pixels "
            "(pausing between steps), so content that lazy-loads when its section enters the "
            "viewport (e.g. a reviews widget) is triggered. Default 0 without a retail "
            "profile; otherwise the profile posture."
        ),
    )
    parser.add_argument(
        "--scroll-target-selector",
        default=None,
        help=(
            "Before progressive scrolling, scroll one matching element into view and wait up to "
            "five seconds for the profile's content condition. Falls back to progressive scrolling "
            "when the selector is absent, activation fails, or the condition is not reached. "
            "Requires a retail capture profile."
        ),
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate CLI inputs and optional proxy profile locally, then exit without network capture.",
    )
    parser.add_argument(
        "--old-reddit-only",
        action="store_true",
        help="Fail before network capture unless --url is on old.reddit.com.",
    )
    parser.add_argument(
        "--block-heavy-assets",
        action="store_true",
        help="Block image, media, and font resources during browser capture to reduce bandwidth.",
    )
    parser.add_argument(
        "--guarded-reddit-launch",
        action="store_true",
        help=(
            "Cheap single-URL Reddit launch profile: requires old.reddit.com and blocks heavy "
            "assets. The runner still performs one capture attempt only."
        ),
    )
    parser.add_argument(
        "--delivery-zip",
        default=None,
        help=(
            "US ZIP code to set as delivery location on amazon.com before capture "
            "(e.g. '10001'). Runs a stateful homepage delivery-location widget flow to "
            "ATTEMPT pinning the US storefront, then requires the requested ZIP in Amazon's "
            "rendered location anchor plus an amazon.com US-marketplace marker. humanize=True "
            "is used automatically. If setup redirects or the captured page loses the pin, "
            "the packet is preserved with a typed failure and the runner exits nonzero. "
            "Probed 2026-06-16 and hardened 2026-07-18; subject to Amazon DOM changes."
        ),
    )
    parser.add_argument(
        "--delivery-zip-setup-timeout-seconds",
        type=float,
        default=30.0,
        help=(
            "Bounds the pre-capture delivery-location widget flow (homepage navigation + "
            "widget steps) SEPARATELY from the main capture --timeout-seconds. Default 30.0. "
            "Only used when --delivery-zip is set."
        ),
    )
    parser.add_argument(
        "--amazon-grid-page-count",
        type=int,
        default=2,
        help=(
            "Consecutive ranked Amazon search-result pages to capture with "
            "amazon_grid_aggregate. Default 2. The projection certifies this requested "
            "window, or an earlier retailer-visible terminal page, never the marketplace corpus."
        ),
    )
    parser.add_argument(
        "--sephora-catalog-page-count",
        type=int,
        default=2,
        help=(
            "Consecutive 60-product Sephora BEST_SELLING PageJSON pages to capture "
            "with sephora_catalog_grid_aggregate. Bounded to 1-12; default 2."
        ),
    )
    parser.add_argument(
        "--nordstrom-country",
        choices=["US"],
        default=None,
        help=(
            "Use Nordstrom's own country-preference UI before capture to ATTEMPT a no-proxy "
            "US/USD storefront pin. The packet confirms the pin only when the rendered main "
            "page contains mutually reinforcing Nordstrom US/USD state; dollar-looking prices "
            "and nordcountrycode alone never count."
        ),
    )
    parser.add_argument(
        "--nordstrom-country-setup-timeout-seconds",
        type=float,
        default=45.0,
        help=(
            "Bounds the Nordstrom homepage/target country-preference interaction separately "
            "from --timeout-seconds. Default 45.0; only used with --nordstrom-country."
        ),
    )
    parser.add_argument(
        "--nordstrom-review-posture",
        choices=list(NORDSTROM_REVIEW_POSTURES),
        default=None,
        help=(
            "Nordstrom onboarding-only posture: preserve the most-helpful "
            "positive/critical pair, select Most Recent, retain every review in the "
            "last 30 days, and when that cohort has fewer than 12 continue to 30 "
            "Most Recent rows or proven source exhaustion; record each Load 6 more "
            "reviews activation."
        ),
    )
    parser.add_argument(
        "--luckyscent-market",
        choices=["US"],
        default=None,
        help=(
            "Fail-closed assertion that Luckyscent's canonical route rendered one "
            "storefront i18n context binding country=US, market=market-us, and "
            "currency=USD. Luckyscent exposes no country selector, so this performs no "
            "preference mutation and does not claim a US shopper origin or delivery "
            "location."
        ),
    )
    parser.add_argument(
        "--sephora-market",
        choices=["US"],
        default=None,
        help=(
            "Fail-closed assertion for a Sephora rendered storefront. PDP capture "
            "requires country_switch=us, Sephora.renderQueryParams country=US, and a "
            "Sephora-sold JSON-LD Offer with priceCurrency=USD. Brand-grid capture "
            "admits the US country route only when the country-routing dialog is "
            "absent and every serialized country binds US, while retaining currency "
            "separately and never inferring USD from a dollar glyph. The "
            "country-dialog continuation performs no login and does not claim a "
            "delivery location."
        ),
    )
    parser.add_argument(
        "--ulta-market",
        choices=["US"],
        default=None,
        help=(
            "Fail-closed assertion for an Ulta rendered storefront. PDP capture "
            "requires consistent html/app/GraphQL en-US site state, a USD product "
            "price node, and a SKU-bound Product JSON-LD USD offer. Brand-grid "
            "capture admits only the consistent US country route; grid currency "
            "and delivery location remain explicitly un-pinned. Performs no "
            "preference mutation."
        ),
    )
    parser.add_argument(
        "--revolve-market",
        choices=["US"],
        default=None,
        help=(
            "Use REVOLVE's public country-preference controls to select US and "
            "USD, then fail closed unless the rendered route independently binds "
            "US shipping, the US storefront, and exact USD product state."
        ),
    )
    parser.add_argument(
        "--target-zip",
        default=None,
        help=(
            "Use Target's public shipping-ZIP UI on the exact commissioned target.com "
            "surface, then fail closed unless the final page binds the requested ZIP in "
            "both Target header signals plus serverLocationVariables.location.country=US. "
            "Store/pickup ZIP remains independent and humanize=True is automatic."
        ),
    )
    parser.add_argument(
        "--target-zip-setup-timeout-seconds",
        type=float,
        default=30.0,
        help=(
            "Bounds Target's public ZIP-control readiness and interaction separately "
            "from --timeout-seconds. Default 30.0; only used with --target-zip."
        ),
    )
    parser.add_argument("--proxy-profile-label", default=None)
    parser.add_argument(
        "--proxy-profile-category",
        choices=[item.value for item in ProxyCategory],
        default=None,
    )
    parser.add_argument("--proxy-profile-root", type=Path, default=None)
    parser.add_argument(
        "--browser-user-data-label",
        default=None,
        help=(
            "Optional ignored local CloakBrowser user-data label to reuse for this capture; "
            "never pass raw profile paths, cookies, or credentials. Requires --browser-user-data-session-mode."
        ),
    )
    parser.add_argument(
        "--browser-user-data-session-mode",
        choices=[item.value for item in AuthenticatedSessionMode],
        default=None,
        help="Declared session mode for --browser-user-data-label.",
    )
    parser.add_argument("--actor-audience-context", default=None)
    parser.add_argument("--actor-audience-context-unknown-reason", default=None)
    parser.add_argument("--visible-mode-change", action="append", default=[])
    parser.add_argument("--source-publication-or-event", default=None)
    parser.add_argument("--source-publication-or-event-unknown-reason", default=None)
    parser.add_argument("--source-edit-or-version", default=None)
    parser.add_argument("--source-edit-or-version-unknown-reason", default=None)
    parser.add_argument("--cutoff-posture", default=None)
    parser.add_argument("--cutoff-posture-unknown-reason", default=None)
    parser.add_argument("--recapture-time", default=None)
    parser.add_argument("--recapture-time-not-applicable-reason", default=None)
    parser.add_argument("--recapture-relationship", default=None)
    parser.add_argument("--recapture-relationship-not-applicable-reason", default=None)
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--limitation", action="append", default=[])
    # The SAME demand-durability flag surface the direct_http writer exposes, so the cadence
    # runner's injectable writer_main seam can invoke either writer per slot interchangeably.
    add_durability_arguments(parser)
    add_source_detail_sufficiency_arguments(parser)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    capture_engine: CloakBrowserSnapshotEngine | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        require_series_identity(args)
        retail_capture_profile = (
            get_retail_capture_profile(args.retail_capture_profile)
            if args.retail_capture_profile is not None
            else None
        )
        if retail_capture_profile is not None:
            if retail_capture_profile.source_surface != "cloakbrowser_snapshot":
                raise ValueError(
                    f"retail capture profile {retail_capture_profile.name} belongs to "
                    f"{retail_capture_profile.source_surface}; use the matching capture runner"
                )
            validate_retail_capture_profile_route(
                retail_capture_profile,
                url=args.url,
                source_family=args.source_family,
                source_surface=args.source_surface,
            )
            _validate_retail_baseline_profile_request(
                retail_capture_profile=retail_capture_profile,
                delivery_zip=args.delivery_zip,
                sephora_market=args.sephora_market,
                ulta_market=args.ulta_market,
                revolve_market=args.revolve_market,
                target_zip=args.target_zip,
            )
        elif args.retail_grid_projection_output is not None:
            raise ValueError(
                "--retail-grid-projection-output requires a retail capture profile"
            )
        content_profiles = {
            SEPHORA_PDP_CONTENT_PROFILE,
            LUCKYSCENT_PDP_CONTENT_PROFILE,
            NORDSTROM_PDP_CONTENT_PROFILE,
            ULTA_PDP_CONTENT_PROFILE,
            REVOLVE_PDP_CONTENT_PROFILE,
            TARGET_PDP_CONTENT_PROFILE,
            AMAZON_PDP_CONTENT_PROFILE,
            TARGET_GRID_CONTENT_PROFILE,
            "sephora_grid_aggregate",
            SEPHORA_CATALOG_GRID_CONTENT_PROFILE,
            "ulta_grid_aggregate",
            "revolve_grid_aggregate",
        }
        if args.retention_mode is not None and (
            retail_capture_profile is None
            or retail_capture_profile.name not in content_profiles
        ):
            raise ValueError(
                "--retention-mode currently requires an enabled aggregate "
                "content profile"
            )
        if args.nordstrom_review_posture is not None and (
            retail_capture_profile is None
            or retail_capture_profile.name != NORDSTROM_PDP_CONTENT_PROFILE
        ):
            raise ValueError(
                "--nordstrom-review-posture requires nordstrom_pdp_aggregate"
            )
        content_extraction = None
        if (
            retail_capture_profile is not None
            and retail_capture_profile.name == SEPHORA_PDP_CONTENT_PROFILE
        ):
            if args.sephora_market != "US":
                raise ValueError(
                    "sephora_pdp_aggregate content capture requires --sephora-market US"
                )
            content_extraction = _sephora_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == LUCKYSCENT_PDP_CONTENT_PROFILE
        ):
            if args.luckyscent_market != "US":
                raise ValueError(
                    "luckyscent_pdp_aggregate content capture requires "
                    "--luckyscent-market US"
                )
            content_extraction = _luckyscent_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == NORDSTROM_PDP_CONTENT_PROFILE
        ):
            if args.nordstrom_country != "US":
                raise ValueError(
                    "nordstrom_pdp_aggregate content capture requires "
                    "--nordstrom-country US"
                )
            content_extraction = _nordstrom_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == ULTA_PDP_CONTENT_PROFILE
        ):
            if args.ulta_market != "US":
                raise ValueError(
                    "ulta_pdp_aggregate content capture requires --ulta-market US"
                )
            content_extraction = _ulta_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == REVOLVE_PDP_CONTENT_PROFILE
        ):
            if args.revolve_market != "US":
                raise ValueError(
                    "revolve_pdp_aggregate content capture requires "
                    "--revolve-market US"
                )
            content_extraction = _revolve_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name in _SEPHORA_GRID_CONTENT_PROFILES
        ):
            if args.retention_mode not in {None, "content"}:
                raise ValueError(
                    f"{retail_capture_profile.name} requires compact content retention"
                )
            content_extraction = (
                _sephora_catalog_grid_content_extraction_spec()
                if retail_capture_profile.name
                == SEPHORA_CATALOG_GRID_CONTENT_PROFILE
                else _sephora_grid_content_extraction_spec()
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == "ulta_grid_aggregate"
        ):
            if args.retention_mode not in {None, "content"}:
                raise ValueError(
                    "ulta_grid_aggregate requires compact content retention"
                )
            content_extraction = _ulta_grid_content_extraction_spec()
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == "revolve_grid_aggregate"
        ):
            if args.retention_mode not in {None, "content"}:
                raise ValueError(
                    "revolve_grid_aggregate requires compact content retention"
                )
            content_extraction = _revolve_grid_content_extraction_spec()
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == TARGET_GRID_CONTENT_PROFILE
        ):
            if args.retention_mode not in {None, "content"}:
                raise ValueError(
                    "target_grid_aggregate requires content retention because Target "
                    "embeds ephemeral guest-session material in rendered scripts"
                )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == AMAZON_GRID_CONTENT_PROFILE
        ):
            if args.retention_mode not in {None, "content"}:
                raise ValueError(
                    "amazon_grid_aggregate requires content retention for its "
                    "multi-page ranked-window record"
                )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == TARGET_PDP_CONTENT_PROFILE
        ):
            content_extraction = _target_content_extraction_spec(
                args.retention_mode or "content"
            )
        elif (
            retail_capture_profile is not None
            and retail_capture_profile.name == AMAZON_PDP_CONTENT_PROFILE
        ):
            content_extraction = _amazon_content_extraction_spec(
                args.retention_mode or "content"
            )
        settle_seconds = (
            args.settle_seconds
            if args.settle_seconds is not None
            else retail_capture_profile.settle_seconds
            if retail_capture_profile is not None
            else 0.0
        )
        wait_until = (
            args.wait_until
            if args.wait_until is not None
            else retail_capture_profile.wait_until
            if retail_capture_profile is not None
            else "load"
        )
        scroll_passes = (
            args.scroll_passes
            if args.scroll_passes is not None
            else retail_capture_profile.scroll_passes
            if retail_capture_profile is not None
            else 0
        )
        scroll_step_px = (
            args.scroll_step_px
            if args.scroll_step_px is not None
            else retail_capture_profile.scroll_step_px
            if retail_capture_profile is not None
            else 0
        )
        scroll_target_selector = (
            args.scroll_target_selector
            if args.scroll_target_selector is not None
            else retail_capture_profile.scroll_target_selector
            if retail_capture_profile is not None
            else None
        )
        proxy_profile = _load_optional_proxy_profile(
            label=args.proxy_profile_label,
            category=args.proxy_profile_category,
            profile_root=args.proxy_profile_root,
        )
        browser_user_data_session_mode = (
            AuthenticatedSessionMode(args.browser_user_data_session_mode)
            if args.browser_user_data_session_mode is not None
            else None
        )
        if args.delivery_zip is not None:
            _validate_amazon_delivery_zip_url(args.url)
        if (args.browser_user_data_label is None) != (browser_user_data_session_mode is None):
            raise ValueError(
                "--browser-user-data-label and --browser-user-data-session-mode must be supplied together"
            )
        browser_user_data_dir = None
        if args.browser_user_data_label is not None:
            browser_user_data_dir = browser_user_data_path_for_label(args.browser_user_data_label)
            if not browser_user_data_dir.is_dir():
                raise ValueError(
                    "browser user-data directory does not exist for label: "
                    f"{args.browser_user_data_label}"
                )
        if browser_user_data_dir is not None and proxy_profile is not None:
            raise ValueError(
                "--browser-user-data-label cannot be combined with --proxy-profile-label/"
                "--proxy-profile-category because CloakBrowser persistent-context capture "
                "does not apply proxy profiles"
            )
        old_reddit_only = args.old_reddit_only or args.guarded_reddit_launch
        block_heavy_assets = args.block_heavy_assets or args.guarded_reddit_launch
        if old_reddit_only:
            _validate_old_reddit_url(args.url)
        if args.sephora_market is not None:
            _validate_sephora_us_market_url(args.url)
        if args.ulta_market is not None:
            _validate_ulta_us_market_url(
                args.url,
                page_kind=(
                    "grid"
                    if retail_capture_profile is not None
                    and retail_capture_profile.name in _ULTA_GRID_PROFILES
                    else "pdp"
                ),
            )
        if args.revolve_market is not None:
            _validate_revolve_us_market_url(
                args.url,
                page_kind=(
                    "grid"
                    if retail_capture_profile is not None
                    and retail_capture_profile.name == "revolve_grid_aggregate"
                    else "pdp"
                ),
            )
        if args.target_zip is not None:
            _validate_target_delivery_zip_url(args.url)
        # helper-delta: vs runners/_scaffold.resolve_output_root -- the --preflight-only
        # early return sits between the target checks and DataLakeRoot.resolve, so a
        # preflight run must not attempt (or fail on) lake resolution.
        data_root = None
        data_root_requested = args.data_root is not None or (
            args.output is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))
        )
        if args.output is not None and args.data_root is not None:
            parser.exit(
                status=2,
                message="source capture CloakBrowser snapshot failed: exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
            )
        if args.output is None and not data_root_requested:
            parser.exit(
                status=2,
                message="source capture CloakBrowser snapshot failed: exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
            )
        if retail_capture_profile is not None:
            _validate_retail_grid_projection_request(
                retail_capture_profile=retail_capture_profile,
                retail_grid_projection_output=args.retail_grid_projection_output,
                data_root_mode=bool(data_root_requested),
                sephora_market=args.sephora_market,
                ulta_market=args.ulta_market,
                revolve_market=args.revolve_market,
            )
        if args.preflight_only:
            print(
                "source capture CloakBrowser preflight passed; no network capture attempted; "
                f"proxy_profile={'present' if proxy_profile is not None else 'absent'}; "
                f"browser_user_data_profile={'present' if browser_user_data_dir is not None else 'absent'}; "
                f"old_reddit_only={old_reddit_only}; block_heavy_assets={block_heavy_assets}"
            )
            return 0
        if data_root_requested:
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=args.data_root)
        capture_context = args.capture_context or _default_capture_context(
            proxy_profile=proxy_profile,
            browser_user_data_session_mode=browser_user_data_session_mode,
        )
        exit_code, message = run_source_capture_cloakbrowser_packet(
            url=args.url,
            source_family=args.source_family,
            source_surface=args.source_surface,
            decision_question=args.decision_question,
            output_directory=args.output if data_root is None else None,
            data_root=data_root,
            capture_context=capture_context,
            operator_category=args.operator_category,
            capture_mode=CaptureModeCategory(args.capture_mode),
            session_id=args.session_id,
            proxy_profile=proxy_profile,
            browser_user_data_label=args.browser_user_data_label,
            browser_user_data_session_mode=browser_user_data_session_mode,
            browser_user_data_dir=browser_user_data_dir,
            actor_audience_context=build_optional_fact(
                label="actor/audience context",
                value=args.actor_audience_context,
                unknown_reason=args.actor_audience_context_unknown_reason,
            ),
            visible_mode_changes=args.visible_mode_change,
            source_publication_or_event=build_optional_fact(
                label="source publication or event timing",
                value=args.source_publication_or_event,
                unknown_reason=args.source_publication_or_event_unknown_reason,
            ),
            source_edit_or_version=build_optional_fact(
                label="source edit or version timing",
                value=args.source_edit_or_version,
                unknown_reason=args.source_edit_or_version_unknown_reason,
            ),
            cutoff_posture=build_optional_fact(
                label="cutoff posture",
                value=args.cutoff_posture,
                unknown_reason=args.cutoff_posture_unknown_reason,
            ),
            recapture_time=build_optional_fact(
                label="re-capture timing",
                value=args.recapture_time,
                not_applicable_reason=args.recapture_time_not_applicable_reason,
            ),
            re_capture_relationship=build_optional_fact(
                label="re-capture relationship",
                value=args.recapture_relationship,
                not_applicable_reason=args.recapture_relationship_not_applicable_reason,
            ),
            warnings=args.warning,
            limitations=args.limitation,
            source_detail_sufficiency_requirements=build_source_detail_sufficiency_requirements(args),
            retail_capture_profile=retail_capture_profile,
            timeout_seconds=args.timeout_seconds,
            wait_until=wait_until,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            max_artifact_bytes=args.max_artifact_bytes,
            block_heavy_assets=block_heavy_assets,
            settle_seconds=settle_seconds,
            scroll_passes=scroll_passes,
            load_more_selector=args.load_more_selector,
            load_more_clicks=args.load_more_clicks,
            scroll_step_px=scroll_step_px,
            scroll_target_selector=scroll_target_selector,
            delivery_zip=args.delivery_zip,
            delivery_zip_setup_timeout_seconds=args.delivery_zip_setup_timeout_seconds,
            amazon_grid_page_count=args.amazon_grid_page_count,
            sephora_catalog_page_count=args.sephora_catalog_page_count,
            nordstrom_country=args.nordstrom_country,
            nordstrom_country_setup_timeout_seconds=(
                args.nordstrom_country_setup_timeout_seconds
            ),
            nordstrom_review_posture=args.nordstrom_review_posture,
            luckyscent_market=args.luckyscent_market,
            sephora_market=args.sephora_market,
            ulta_market=args.ulta_market,
            revolve_market=args.revolve_market,
            target_zip=args.target_zip,
            target_zip_setup_timeout_seconds=args.target_zip_setup_timeout_seconds,
            # Demand-durability series facts (Ob.17). Element 1 pins (each an honest
            # value/unknown/not-applicable VisibleFact) ride on the slice; Element 2 origin
            # postures + Element 4 declared cadence ride on the packet. Observed facts only,
            # forwarded verbatim, never weights or a durable-vs-hollow verdict (INV-1).
            session_visibility_pin=build_optional_fact(
                label="session visibility pin",
                value=args.session_visibility_pin,
                unknown_reason=args.session_visibility_pin_unknown_reason,
                not_applicable_reason=args.session_visibility_pin_not_applicable_reason,
            ),
            locale_pin=build_optional_fact(
                label="locale pin",
                value=args.locale_pin,
                unknown_reason=args.locale_pin_unknown_reason,
                not_applicable_reason=args.locale_pin_not_applicable_reason,
            ),
            currency_pin=build_optional_fact(
                label="currency pin",
                value=args.currency_pin,
                unknown_reason=args.currency_pin_unknown_reason,
                not_applicable_reason=args.currency_pin_not_applicable_reason,
            ),
            variant_pin=build_optional_fact(
                label="variant pin",
                value=args.variant_pin,
                unknown_reason=args.variant_pin_unknown_reason,
                not_applicable_reason=args.variant_pin_not_applicable_reason,
            ),
            series_id=args.series_id,
            cold_start_at=build_optional_fact(
                label="cold-start timing",
                value=args.cold_start_at,
                unknown_reason=args.cold_start_at_unknown_reason,
                not_applicable_reason=args.cold_start_at_not_applicable_reason,
            ),
            pre_coverage_history_posture=build_optional_fact(
                label="pre-coverage history posture",
                value=args.pre_coverage_history_posture,
                unknown_reason=args.pre_coverage_history_posture_unknown_reason,
                not_applicable_reason=args.pre_coverage_history_posture_not_applicable_reason,
            ),
            intended_cadence=build_intended_cadence(args),
            content_extraction=content_extraction,
            retail_grid_projection_output=args.retail_grid_projection_output,
            retain_retail_grid_raw_sample=args.retain_retail_grid_raw_sample,
            capture_engine=capture_engine,
        )
    except ValueError as exc:
        parser.exit(status=2, message=f"source capture CloakBrowser snapshot failed: {exc}\n")
    except Exception as exc:
        parser.exit(status=3, message=f"source capture CloakBrowser snapshot failed: {exc}\n")

    if exit_code == 0:
        print(message)
        return 0

    parser.exit(status=exit_code, message=f"source capture CloakBrowser snapshot failed: {message}\n")
    return exit_code


def _load_optional_proxy_profile(
    *,
    label: str | None,
    category: str | None,
    profile_root: Path | None,
) -> ProxyProfile | None:
    if label is None and category is None:
        return None
    if not label or not category:
        raise ValueError(
            "proxy profile capture requires both --proxy-profile-label and --proxy-profile-category"
        )
    return load_proxy_profile(
        label,
        proxy_category=ProxyCategory(category),
        profile_root=profile_root,
    )


def _validate_old_reddit_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "old.reddit.com":
        raise ValueError(
            "--old-reddit-only/--guarded-reddit-launch requires an absolute old.reddit.com URL"
        )


def _default_capture_context(
    *,
    proxy_profile: ProxyProfile | None,
    browser_user_data_session_mode: AuthenticatedSessionMode | None = None,
) -> str:
    profile_clause = (
        f" using label-indirected local browser profile with {browser_user_data_session_mode.value}"
        if browser_user_data_session_mode is not None
        else " without stored session or browser profile"
    )
    if proxy_profile is None:
        return (
            "CloakBrowser anti-blocking browser source capture"
            f"{profile_clause}; no proxy, raw cookie export, or credential injection"
        )
    return (
        "CloakBrowser anti-blocking browser source capture"
        f"{profile_clause} and label-indirected {proxy_profile.proxy_category.value} proxy profile; "
        "endpoint, credentials, raw cookies, and profile path are not recorded"
    )


if __name__ == "__main__":
    raise SystemExit(main())
