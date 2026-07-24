from __future__ import annotations

import hashlib
import html as html_module
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Mapping
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

from pydantic import Field, field_validator, model_validator

from harness_utils import generate_ulid
from schemas.case_models import StrictModel
from source_capture.models import PreservedFile, SourceCapturePacket, SourceCaptureSlice, VisibleFactStatus
from source_capture.projection_shared import is_forbidden_field_token_match
from source_capture.retail_capture_profiles import (
    extract_amazon_search_query_from_url,
    extract_target_grid_subject_from_url,
)
from source_capture.retail_pdp_projection import RetailProjectionRawAnchor, RetailProjectionRawRef
from source_capture.sephora_brand_grid import (
    SephoraBrandGridState,
    SephoraBrandGridStateError,
    load_sephora_brand_grid_state,
)
from source_capture.sephora_catalog_grid import (
    SEPHORA_CATALOG_MAX_PAGE,
    SEPHORA_CATALOG_PAGE_SIZE,
    SephoraCatalogAggregateState,
    SephoraCatalogGridStateError,
    extract_sephora_catalog_request,
    load_sephora_catalog_aggregate_state,
)

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot


RETAIL_GRID_PROJECTION_METHOD = "retail_grid_mechanical_projection"
RETAIL_GRID_PROJECTION_VERSION = "v0"
RETAIL_GRID_OBSERVATION_VERSION = "v1"
RETAIL_GRID_PROJECTION_CERTIFICATION = "view_only; not_cleaned; not_normalized; not_judgment_ready"
PROJECTION_RETAIL_GRID_LANE = "projection_retail_grid"
TARGET_GRID_CONTENT_RECORD_VERSION = "target_grid_content_v2"
_SUPPORTED_TARGET_GRID_CONTENT_RECORD_VERSIONS = frozenset(
    {"target_grid_content_v1", TARGET_GRID_CONTENT_RECORD_VERSION}
)
AMAZON_GRID_CONTENT_RECORD_VERSION = "amazon_grid_content_v1"

RetailGridRetailer = Literal[
    "walmart", "target", "sephora", "ulta", "amazon", "revolve"
]

_FORBIDDEN_FIELD_TOKENS = frozenset(
    {
        "action_ceiling",
        "credibility",
        "decision_strength",
        "demand",
        "discount",
        "exclude",
        "excluded",
        "inclusion",
        "integrity",
        "judgment",
        "signal_use",
        "strength",
        "strong",
        "weak",
    }
)
_NEXT_DATA_RE = re.compile(
    r"<script[^>]+id=[\"']__NEXT_DATA__[\"'][^>]*>(?P<json>.*?)</script>",
    flags=re.IGNORECASE | re.DOTALL,
)
_TARGET_CARD_RE = re.compile(
    r"<div[^>]*\bdata-focusid=[\"'](?P<product_id>\d+)_product_card[\"'][^>]*>",
    flags=re.IGNORECASE,
)
_AMAZON_CARD_RE = re.compile(
    r"<div\b(?=[^>]*\bdata-component-type=[\"']s-search-result[\"'])"
    r"(?=[^>]*\bdata-asin=[\"'](?P<asin>[A-Z0-9]{10})[\"'])[^>]*>",
    flags=re.IGNORECASE,
)
_AMAZON_US_MARKETPLACE_MARKERS = (
    "ue_sn = 'www.amazon.com'",
    "retail:prod:www.amazon.com",
    "assoc_handle=usflex",
)
_SCRIPT_OR_STYLE_RE = re.compile(
    r"<(?P<tag>script|style)\b[^>]*>.*?</(?P=tag)\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
_DIV_BOUNDARY_RE = re.compile(r"<(?P<closing>/?)div\b[^>]*>", re.IGNORECASE)
_PRICE_RANGE_RE = re.compile(
    r"^\s*\$?(?P<minimum>\d+(?:\.\d+)?)\s*[-\u2013]\s*\$?(?P<maximum>\d+(?:\.\d+)?)\s*$"
)


class RetailGridProjectionInputError(ValueError):
    """A packet cannot be projected without verified raw files and grid identity."""


class RetailGridProjectionRow(StrictModel):
    row_id: str
    row_kind: Literal["retail_grid_product"] = "retail_grid_product"
    retailer: RetailGridRetailer
    raw_ref: RetailProjectionRawRef | None = None
    raw_anchor: RetailProjectionRawAnchor | None = None
    placements: list["RetailGridProjectionPlacement"] = Field(default_factory=list)
    source_visible_fields: dict[str, Any | None]
    residuals: list[str] = Field(default_factory=list)

    @field_validator("source_visible_fields")
    @classmethod
    def require_identity_and_reject_judgment(
        cls, value: dict[str, Any | None]
    ) -> dict[str, Any | None]:
        missing = [
            field
            for field in ("source_product_id", "product_url", "name")
            if not isinstance(value.get(field), str) or not str(value[field]).strip()
        ]
        if missing:
            raise ValueError(
                "retail grid product rows require non-empty source identity fields: "
                + ", ".join(missing)
            )
        forbidden = sorted(key for key in value if _is_forbidden_field_name(key))
        if forbidden:
            raise ValueError(
                "retail grid projection may carry source-visible facts only; "
                f"forbidden Judgment field(s): {', '.join(forbidden)}"
            )
        return value


class RetailGridProjectionPlacement(StrictModel):
    grid_position: int = Field(ge=1)
    page: int | None = Field(default=None, ge=1)
    page_position: int | None = Field(default=None, ge=1)
    raw_anchor: RetailProjectionRawAnchor | None = None


class RetailGridCaptureEvent(StrictModel):
    capture_event_id: str
    anchor_kind: Literal["capture_event"] = "capture_event"
    captured_at: str
    requested_url: str
    final_url: str
    capture_profile: str
    parser_version: str
    series_id: str | None = None
    raw_sample_packet_id: str | None = None


class RetailGridCompletenessReconciliation(StrictModel):
    status: Literal["complete", "incomplete", "not_evaluated"]
    page_declared_result_count: int | None = Field(default=None, ge=0)
    extracted_unique_parent_count: int = Field(ge=0)
    extracted_placement_count: int = Field(ge=0)
    duplicate_placement_count: int = Field(ge=0)
    subject_binding_confirmed: bool | None = None
    termination: Literal[
        "retailer_serialized_count_reconciled",
        "retailer_visible_count_reconciled",
        "requested_page_window_reconciled",
        "retailer_terminal_reconciled",
        "unproven",
        "not_evaluated",
    ]
    residuals: list[str] = Field(default_factory=list)


class RetailGridProjectionLossLedger(StrictModel):
    preserved_evidence_rows: int = Field(ge=0)
    timing: Literal["separate_not_collapsed"] = "separate_not_collapsed"
    hierarchy_preserved: bool = True
    structure_preserved: bool
    certification: Literal[
        "source_visible_product_tiles_preserved; does_not_certify_cleaning"
    ] = "source_visible_product_tiles_preserved; does_not_certify_cleaning"


class RetailGridProjectionPacket(StrictModel):
    projection_method: Literal["retail_grid_mechanical_projection"] = RETAIL_GRID_PROJECTION_METHOD
    projection_version: Literal["v0", "v1"] = RETAIL_GRID_PROJECTION_VERSION
    certification: Literal[
        "view_only; not_cleaned; not_normalized; not_judgment_ready"
    ] = RETAIL_GRID_PROJECTION_CERTIFICATION
    packet_id: str | None = None
    capture_event: RetailGridCaptureEvent | None = None
    rows: list[RetailGridProjectionRow] = Field(default_factory=list)
    source_visible_grid_facts: dict[str, Any | None] = Field(default_factory=dict)
    completeness: RetailGridCompletenessReconciliation
    loss_ledger: RetailGridProjectionLossLedger
    residuals: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "RetailGridProjectionPacket":
        if self.projection_version == "v0":
            if not self.packet_id or self.capture_event is not None:
                raise ValueError("retail grid projection v0 requires packet_id only")
            if any(row.raw_ref is None or row.raw_anchor is None for row in self.rows):
                raise ValueError("retail grid projection v0 rows require raw references")
            if any(
                placement.raw_anchor is None
                for row in self.rows
                for placement in row.placements
            ):
                raise ValueError("retail grid projection v0 placements require raw anchors")
        else:
            if self.packet_id is not None or self.capture_event is None:
                raise ValueError("retail grid observation v1 requires capture_event only")
            sample_packet_id = self.capture_event.raw_sample_packet_id
            for row in self.rows:
                if sample_packet_id is None:
                    if row.raw_ref is not None or row.raw_anchor is not None:
                        raise ValueError(
                            "derived-only retail grid observation rows must not claim raw evidence"
                        )
                    if any(item.raw_anchor is not None for item in row.placements):
                        raise ValueError(
                            "derived-only retail grid observation placements must not claim raw evidence"
                        )
                elif row.raw_ref is None or row.raw_ref.packet_id != sample_packet_id:
                    raise ValueError(
                        "sample-backed retail grid rows must reference raw_sample_packet_id"
                    )
                elif row.raw_anchor is None or any(
                    item.raw_anchor is None for item in row.placements
                ):
                    raise ValueError(
                        "sample-backed retail grid rows and placements require raw anchors"
                    )
        if self.loss_ledger.preserved_evidence_rows != len(self.rows):
            raise ValueError("loss_ledger.preserved_evidence_rows must match rows length")
        if self.loss_ledger.structure_preserved != bool(self.rows):
            raise ValueError("grid structure_preserved must be true exactly when product rows exist")
        if self.completeness.extracted_unique_parent_count != len(self.rows):
            raise ValueError(
                "completeness.extracted_unique_parent_count must match rows length"
            )
        expected_placements = sum(max(1, len(row.placements)) for row in self.rows)
        if self.completeness.extracted_placement_count != expected_placements:
            raise ValueError(
                "completeness.extracted_placement_count must match anchored placements"
            )
        if (
            self.completeness.duplicate_placement_count
            != expected_placements - len(self.rows)
        ):
            raise ValueError(
                "completeness.duplicate_placement_count must match placement surplus"
            )
        return self


def build_retail_grid_projection_from_packet_directory(
    *, packet_directory: Path
) -> RetailGridProjectionPacket:
    packet, raw_file_bytes_by_file_id = load_verified_source_capture_packet_directory(packet_directory)
    return build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id=raw_file_bytes_by_file_id
    )


def write_retail_grid_projection(
    *, packet_directory: Path, output_path: Path
) -> RetailGridProjectionPacket:
    projection = build_retail_grid_projection_from_packet_directory(
        packet_directory=packet_directory
    )
    if output_path.exists():
        raise RetailGridProjectionInputError(
            f"projection output already exists; refusing overwrite: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"{json.dumps(projection.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return projection


def project_retail_grid_into_lake(
    *,
    data_root: "DataLakeRoot",
    packet_id: str,
    record_id: str | None = None,
) -> tuple[RetailGridProjectionPacket, Path]:
    """Project one hash-verified raw packet into an append-only derived record."""
    loaded = data_root.load_raw_packet(packet_id)
    packet = SourceCapturePacket.model_validate(loaded.manifest)
    projection = build_retail_grid_projection(
        packet=packet,
        raw_file_bytes_by_file_id=loaded.bodies,
    )
    record = record_id if record_id is not None else generate_ulid()
    derived_path = _append_projection_record(
        data_root=data_root,
        source_anchor=packet_id,
        record_id=record,
        projection=projection,
    )
    return projection, derived_path


def build_retail_grid_observation(
    *,
    packet: SourceCapturePacket,
    raw_file_bytes_by_file_id: Mapping[str, bytes],
    captured_at: str,
    requested_url: str,
    final_url: str,
    capture_profile: str,
    parser_version: str,
    series_id: str | None,
    retain_raw_sample: bool,
) -> RetailGridProjectionPacket:
    """Build a v1 derived observation from transient capture material.

    The packet-shaped input is an in-flight parsing envelope. It becomes durable
    raw evidence only when ``retain_raw_sample`` is true.
    """

    projected = build_retail_grid_projection(
        packet=packet,
        raw_file_bytes_by_file_id=raw_file_bytes_by_file_id,
    )
    sample_packet_id = packet.packet_id if retain_raw_sample else None
    rows: list[dict[str, Any]] = []
    for row in projected.rows:
        value = row.model_dump(mode="json")
        if sample_packet_id is None:
            value["raw_ref"] = None
            value["raw_anchor"] = None
            for placement in value["placements"]:
                placement["raw_anchor"] = None
        rows.append(value)
    return RetailGridProjectionPacket.model_validate(
        {
            **projected.model_dump(mode="json"),
            "projection_version": RETAIL_GRID_OBSERVATION_VERSION,
            "packet_id": None,
            "capture_event": {
                "capture_event_id": packet.packet_id,
                "captured_at": captured_at,
                "requested_url": requested_url,
                "final_url": final_url,
                "capture_profile": capture_profile,
                "parser_version": parser_version,
                "series_id": series_id,
                "raw_sample_packet_id": sample_packet_id,
            },
            "rows": rows,
        }
    )


def append_retail_grid_observation_into_lake(
    *,
    data_root: "DataLakeRoot",
    observation: RetailGridProjectionPacket,
    record_id: str | None = None,
) -> Path:
    """Append one v1 observation under its capture-event source anchor."""

    if observation.projection_version != RETAIL_GRID_OBSERVATION_VERSION:
        raise RetailGridProjectionInputError("only v1 observations use capture-event filing")
    assert observation.capture_event is not None
    record = record_id if record_id is not None else generate_ulid()
    return _append_projection_record(
        data_root=data_root,
        source_anchor=observation.capture_event.capture_event_id,
        record_id=record,
        projection=observation,
    )


def _append_projection_record(
    *,
    data_root: "DataLakeRoot",
    source_anchor: str,
    record_id: str,
    projection: RetailGridProjectionPacket,
) -> Path:
    return data_root.append_record(
        subtree="derived",
        # ``raw_anchor`` is the v4.1 API's compatibility name; the forward
        # contract now permits a capture-event source anchor for this lane.
        raw_anchor=source_anchor,
        lane=PROJECTION_RETAIL_GRID_LANE,
        record_id=f"{record_id}.json",
        data=_projection_json_text(projection).encode("utf-8"),
    )


def build_target_grid_aggregate_content_record(
    *,
    rendered_pages: tuple[str, ...],
    requested_url: str,
    page_urls: tuple[str, ...],
    traversal_observation: Mapping[str, object],
) -> dict[str, object]:
    """Extract a token-free Target multi-page search or brand-grid evidence record."""
    if not rendered_pages:
        raise RetailGridProjectionInputError(
            "Target grid content extraction requires at least one rendered page"
        )
    if len(rendered_pages) != len(page_urls):
        raise RetailGridProjectionInputError(
            "Target grid rendered page and URL counts must match"
        )

    requested_subject = extract_target_grid_subject_from_url(requested_url)
    requested_subject_kind = requested_subject[0] if requested_subject else None
    requested_subject_value = requested_subject[1] if requested_subject else None
    pages: list[dict[str, object]] = []
    record_residuals: list[str] = []
    declared_counts: list[int] = []
    observed_queries: list[str] = []
    observed_subjects: list[str] = []
    observed_delivery_zips: list[str] = []
    for page_index, (rendered_dom, page_url) in enumerate(
        zip(rendered_pages, page_urls, strict=True), start=1
    ):
        page = _parse_target_grid_page(
            rendered_dom,
            page_number=page_index,
            subject_kind=requested_subject_kind,
        )
        page["url"] = page_url
        pages.append(page)
        record_residuals.extend(str(value) for value in page["residuals"])
        declared = page.get("declared_result_count")
        if isinstance(declared, int):
            declared_counts.append(declared)
        observed_query = page.get("observed_query")
        if isinstance(observed_query, str):
            observed_queries.append(observed_query)
        observed_subject = page.get("observed_subject")
        if isinstance(observed_subject, str):
            observed_subjects.append(observed_subject)
        delivery_zip = page.get("delivery_zip")
        if isinstance(delivery_zip, str):
            observed_delivery_zips.append(delivery_zip)

    requested_query = (
        requested_subject_value
        if requested_subject_kind == "search_query"
        else None
    )
    placement_count = sum(len(page["products"]) for page in pages)
    product_ids = [
        str(product["product_id"])
        for page in pages
        for product in page["products"]
        if isinstance(product, dict) and isinstance(product.get("product_id"), str)
    ]
    unique_parent_count = len(set(product_ids))
    duplicate_count = placement_count - unique_parent_count
    declared_count = declared_counts[-1] if declared_counts else None
    if not declared_counts:
        record_residuals.append("target_grid_page_declared_count_absent")
    if requested_subject is None:
        record_residuals.append("target_grid_requested_subject_absent")
    if not observed_subjects or any(
        _normalize_target_subject(value, kind=requested_subject_kind)
        != _normalize_target_subject(
            requested_subject_value, kind=requested_subject_kind
        )
        for value in observed_subjects
        if requested_subject_value is not None
    ):
        record_residuals.append("target_grid_subject_binding_unconfirmed")
    observed_sort_orders = [
        value
        for page_url in page_urls
        if (value := _target_grid_sort_order(page_url)) is not None
    ]
    if len(observed_sort_orders) != len(page_urls) or any(
        value != "bestselling" for value in observed_sort_orders
    ):
        record_residuals.append("target_grid_bestseller_sort_unconfirmed")
    if not observed_delivery_zips or len(set(observed_delivery_zips)) != 1:
        record_residuals.append("target_grid_delivery_zip_unconfirmed_in_page_states")

    return {
        "content_record_version": TARGET_GRID_CONTENT_RECORD_VERSION,
        "retailer": "target",
        "page_kind": (
            "brand_grid" if requested_subject_kind == "brand" else "search_grid"
        ),
        "requested_url": requested_url,
        "requested_subject_kind": requested_subject_kind,
        "requested_subject": requested_subject_value,
        "observed_subjects": _dedupe(observed_subjects),
        "requested_query": requested_query,
        "observed_queries": _dedupe(observed_queries),
        "sort_order": (
            "bestselling"
            if observed_sort_orders
            and len(observed_sort_orders) == len(page_urls)
            and all(value == "bestselling" for value in observed_sort_orders)
            else None
        ),
        "delivery_zip": (
            observed_delivery_zips[0]
            if observed_delivery_zips and len(set(observed_delivery_zips)) == 1
            else None
        ),
        "declared_result_count": declared_count,
        "declared_result_count_observations": declared_counts,
        "page_load_count": len(pages),
        "extracted_placement_count": placement_count,
        "extracted_unique_parent_count": unique_parent_count,
        "duplicate_placement_count": duplicate_count,
        "traversal_termination": traversal_observation.get(
            "target_grid_termination", "unproven"
        ),
        "pages": pages,
        "residuals": _dedupe(record_residuals),
    }


def build_amazon_grid_aggregate_content_record(
    *,
    rendered_pages: tuple[str, ...],
    requested_url: str,
    page_urls: tuple[str, ...],
    traversal_observation: Mapping[str, object],
) -> dict[str, object]:
    """Extract a token-free Amazon ranked-search window content record."""
    if not rendered_pages:
        raise RetailGridProjectionInputError(
            "Amazon grid content extraction requires at least one rendered page"
        )
    if len(rendered_pages) != len(page_urls):
        raise RetailGridProjectionInputError(
            "Amazon grid rendered page and URL counts must match"
        )
    requested_query = extract_amazon_search_query_from_url(requested_url)
    pages: list[dict[str, object]] = []
    residuals: list[str] = []
    observed_queries: list[str] = []
    range_observations: list[dict[str, int]] = []
    observed_delivery_zips: list[str] = []
    for page_number, (rendered_dom, page_url) in enumerate(
        zip(rendered_pages, page_urls, strict=True), start=1
    ):
        page = _parse_amazon_grid_page(
            rendered_dom,
            page_number=page_number,
            page_url=page_url,
        )
        pages.append(page)
        residuals.extend(str(value) for value in page["residuals"])
        observed_query = page.get("observed_query")
        if isinstance(observed_query, str):
            observed_queries.append(observed_query)
        result_range = page.get("result_range")
        if isinstance(result_range, dict):
            range_observations.append(result_range)
        delivery_zip = page.get("delivery_zip")
        if isinstance(delivery_zip, str):
            observed_delivery_zips.append(delivery_zip)

    placement_count = sum(len(page["products"]) for page in pages)
    product_ids = [
        str(product["product_id"])
        for page in pages
        for product in page["products"]
        if isinstance(product, dict) and isinstance(product.get("product_id"), str)
    ]
    if requested_query is None:
        residuals.append("amazon_grid_requested_query_absent")
    if len(observed_queries) != len(pages) or any(
        _normalize_query(query) != _normalize_query(requested_query or "")
        for query in observed_queries
    ):
        residuals.append("amazon_grid_query_binding_unconfirmed")
    if len(range_observations) != len(pages):
        residuals.append("amazon_grid_result_range_absent")
    if any(page.get("us_marketplace_confirmed") is not True for page in pages):
        residuals.append("amazon_grid_us_marketplace_unconfirmed")

    requested_page_count = traversal_observation.get(
        "amazon_grid_requested_page_count", len(pages)
    )
    return {
        "content_record_version": AMAZON_GRID_CONTENT_RECORD_VERSION,
        "retailer": "amazon",
        "page_kind": "ranked_search_window",
        "requested_url": requested_url,
        "requested_query": requested_query,
        "observed_queries": _dedupe(observed_queries),
        "delivery_zip": (
            observed_delivery_zips[0]
            if observed_delivery_zips and len(set(observed_delivery_zips)) == 1
            else None
        ),
        "location_binding": (
            "delivery_zip"
            if observed_delivery_zips
            else "us_marketplace_only"
        ),
        "requested_page_count": requested_page_count,
        "captured_page_count": len(pages),
        "result_range_observations": range_observations,
        "population_observations": traversal_observation.get(
            "amazon_grid_population_observations", []
        ),
        "displayed_result_total_observations": [
            value["total"] for value in range_observations if "total" in value
        ],
        "extracted_placement_count": placement_count,
        "extracted_unique_parent_count": len(set(product_ids)),
        "duplicate_placement_count": placement_count - len(set(product_ids)),
        "traversal_termination": traversal_observation.get(
            "amazon_grid_termination", "unproven"
        ),
        "pages": pages,
        "residuals": _dedupe(residuals),
    }


def _is_grid_content_record(text: str, *, retailer: RetailGridRetailer) -> bool:
    """Return whether text is this retailer's compact grid content record."""
    if retailer == "target":
        return _load_target_grid_content_record(text) is not None
    if retailer == "amazon":
        return _load_amazon_grid_content_record(text) is not None
    if retailer not in {"sephora", "ulta", "revolve"}:
        return False
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        return False
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return False
    return (
        isinstance(payload, dict)
        and "content_record_version" in payload
        and payload.get("retailer") == retailer
    )


def build_retail_grid_projection(
    *, packet: SourceCapturePacket, raw_file_bytes_by_file_id: Mapping[str, bytes]
) -> RetailGridProjectionPacket:
    retailer = detect_retail_grid_retailer(packet)
    content_record_file_ids = {
        file_id
        for source_slice in packet.source_slices
        for file_id in source_slice.preserved_file_ids
        if (body := raw_file_bytes_by_file_id.get(file_id)) is not None
        and _is_grid_content_record(
            body.decode("utf-8", errors="replace"), retailer=retailer
        )
    }
    if retailer == "revolve":
        from source_capture.revolve_grid_projection import (
            build_revolve_grid_projection,
        )

        if content_record_file_ids:
            packet = packet.model_copy(
                update={
                    "source_slices": [
                        source_slice.model_copy(
                            update={
                                "preserved_file_ids": [
                                    file_id
                                    for file_id in source_slice.preserved_file_ids
                                    if file_id in content_record_file_ids
                                ]
                            }
                        )
                        for source_slice in packet.source_slices
                        if any(
                            file_id in content_record_file_ids
                            for file_id in source_slice.preserved_file_ids
                        )
                    ]
                }
            )
        return build_revolve_grid_projection(
            packet=packet, raw_file_bytes_by_file_id=raw_file_bytes_by_file_id
        )
    if retailer == "ulta":
        from source_capture.ulta_grid_projection import build_ulta_grid_projection

        if content_record_file_ids:
            packet = packet.model_copy(
                update={
                    "source_slices": [
                        source_slice.model_copy(
                            update={
                                "preserved_file_ids": [
                                    file_id
                                    for file_id in source_slice.preserved_file_ids
                                    if file_id in content_record_file_ids
                                ]
                            }
                        )
                        for source_slice in packet.source_slices
                        if any(
                            file_id in content_record_file_ids
                            for file_id in source_slice.preserved_file_ids
                        )
                    ]
                }
            )
        return build_ulta_grid_projection(
            packet=packet, raw_file_bytes_by_file_id=raw_file_bytes_by_file_id
        )
    preserved_files = {item.file_id: item for item in packet.preserved_files}
    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    sephora_states: list[SephoraBrandGridState] = []
    sephora_catalog_states: list[SephoraCatalogAggregateState] = []
    target_states: list[dict[str, Any]] = []
    amazon_states: list[dict[str, Any]] = []
    for source_slice in packet.source_slices:
        raw_ref = RetailProjectionRawRef(
            packet_id=packet.packet_id, slice_id=source_slice.slice_id
        )
        slice_row_count = 0
        for file_id in source_slice.preserved_file_ids:
            if content_record_file_ids and file_id not in content_record_file_ids:
                continue
            preserved_file = preserved_files[file_id]
            body = raw_file_bytes_by_file_id.get(file_id)
            if body is None:
                raise ValueError(f"raw bytes are required for preserved file id: {file_id}")
            raw_anchor = _raw_anchor(preserved_file)
            text = body.decode("utf-8", errors="replace")
            if retailer == "walmart":
                projected, file_residuals = _project_walmart_next_data(
                    text,
                    packet=packet,
                    source_slice=source_slice,
                    raw_ref=raw_ref,
                    raw_anchor=raw_anchor,
                )
            elif retailer == "target":
                projected, file_residuals, target_state = _project_target_cards(
                    text,
                    packet=packet,
                    source_slice=source_slice,
                    raw_ref=raw_ref,
                    raw_anchor=raw_anchor,
                )
                if target_state is not None:
                    target_states.append(target_state)
            elif retailer == "amazon":
                projected, file_residuals, amazon_state = _project_amazon_cards(
                    text,
                    packet=packet,
                    source_slice=source_slice,
                    raw_ref=raw_ref,
                    raw_anchor=raw_anchor,
                )
                if amazon_state is not None:
                    amazon_states.append(amazon_state)
            else:
                (
                    projected,
                    file_residuals,
                    sephora_state,
                    sephora_catalog_state,
                ) = _project_sephora_linkstore(
                    text,
                    packet=packet,
                    source_slice=source_slice,
                    raw_ref=raw_ref,
                    raw_anchor=raw_anchor,
                )
                if sephora_state is not None:
                    sephora_states.append(sephora_state)
                if sephora_catalog_state is not None:
                    sephora_catalog_states.append(sephora_catalog_state)
            rows.extend(projected)
            residuals.extend(file_residuals)
            slice_row_count += len(projected)
        if slice_row_count == 0:
            residuals.append(f"{source_slice.slice_id}:{retailer}:grid_product_tiles_absent")

    if retailer == "sephora":
        rows, merge_residuals = _merge_sephora_parent_rows(rows)
        residuals.extend(merge_residuals)
        if sephora_catalog_states:
            grid_facts, completeness = _sephora_catalog_grid_reconciliation(
                packet=packet,
                rows=rows,
                states=sephora_catalog_states,
                brand_states=sephora_states,
                residuals=residuals,
            )
        else:
            grid_facts, completeness = _sephora_grid_reconciliation(
                packet=packet,
                rows=rows,
                states=sephora_states,
                residuals=residuals,
            )
    elif retailer == "target":
        rows, merge_residuals = _merge_target_parent_rows(rows)
        residuals.extend(merge_residuals)
        grid_facts, completeness = _target_grid_reconciliation(
            packet=packet,
            rows=rows,
            states=target_states,
            residuals=residuals,
        )
    elif retailer == "amazon":
        rows, merge_residuals = _merge_amazon_parent_rows(rows)
        residuals.extend(merge_residuals)
        grid_facts, completeness = _amazon_grid_reconciliation(
            packet=packet,
            rows=rows,
            states=amazon_states,
            residuals=residuals,
        )
    else:
        grid_facts = {}
        completeness = RetailGridCompletenessReconciliation(
            status="not_evaluated",
            extracted_unique_parent_count=len(rows),
            extracted_placement_count=len(rows),
            duplicate_placement_count=0,
            subject_binding_confirmed=None,
            termination="not_evaluated",
            residuals=[],
        )

    return RetailGridProjectionPacket(
        packet_id=packet.packet_id,
        rows=rows,
        source_visible_grid_facts=grid_facts,
        completeness=completeness,
        loss_ledger=RetailGridProjectionLossLedger(
            preserved_evidence_rows=len(rows), structure_preserved=bool(rows)
        ),
        residuals=_dedupe(residuals),
    )


def _project_sephora_linkstore(
    text: str,
    *,
    packet: SourceCapturePacket,
    source_slice: SourceCaptureSlice,
    raw_ref: RetailProjectionRawRef,
    raw_anchor: RetailProjectionRawAnchor,
) -> tuple[
    list[RetailGridProjectionRow],
    list[str],
    SephoraBrandGridState | None,
    SephoraCatalogAggregateState | None,
]:
    try:
        catalog_state = load_sephora_catalog_aggregate_state(text)
    except SephoraCatalogGridStateError as exc:
        raise RetailGridProjectionInputError(str(exc)) from exc
    if catalog_state is not None:
        rows, residuals = _project_sephora_catalog_state(
            catalog_state,
            packet=packet,
            source_slice=source_slice,
            raw_ref=raw_ref,
            raw_anchor=raw_anchor,
        )
        return rows, residuals, None, catalog_state
    try:
        state = load_sephora_brand_grid_state(text)
    except SephoraBrandGridStateError as exc:
        raise RetailGridProjectionInputError(str(exc)) from exc
    if state is None:
        return [], [], None, None
    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    currency_code = (
        state.explicit_currency_codes[0]
        if len(state.explicit_currency_codes) == 1
        else None
    )
    for index, product in enumerate(state.products):
        product_id = _text(product.get("productId"))
        product_url = _absolute_url(
            "https://www.sephora.com", _text(product.get("targetUrl"))
        )
        name = _text(product.get("displayName"))
        if product_id is None or product_url is None or name is None:
            residuals.append(
                f"{source_slice.slice_id}:sephora:grid_tile_identity_incomplete:{index}"
            )
            continue
        current_sku = product.get("currentSku")
        current_sku = current_sku if isinstance(current_sku, dict) else {}
        pointer = f"/page/nthBrand/products/{index}"
        placement_anchor = _with_anchor(raw_anchor, "json_pointer", pointer)
        price_display = _text(current_sku.get("listPrice"))
        price, price_range = _price_fields(price_display)
        fields = _base_fields(
            packet=packet, source_slice=source_slice, retailer="sephora"
        )
        fields.update(
            {
                "source_product_id": product_id,
                "product_url": product_url,
                "canonical_product_url": _canonical_url(product_url),
                "name": name,
                "brand": _text(product.get("brandName")),
                "grid_position": index + 1,
                "category": None,
                "breadcrumb": None,
                "selected_sku_id": _text(current_sku.get("skuId")),
                "selected_variant": None,
                "price": price,
                "price_display": price_display,
                "price_range": price_range,
                "price_currency": currency_code,
                "currency_symbol": (
                    "$"
                    if price_display is not None and price_display.startswith("$")
                    else None
                ),
                "average_rating": _first_present(product.get("rating")),
                "rating_count": _first_present(product.get("reviews")),
                "review_count": _first_present(product.get("reviews")),
                "badges": _sephora_badges(current_sku),
                "availability_summary": None,
                "pickup_eligible": _strict_bool(product.get("pickupEligible")),
                "same_day_eligible": _strict_bool(product.get("sameDayEligible")),
                "visible_variant_count": _integer(product.get("moreColors")),
                "location_ids": [],
                "seller": "Sephora",
            }
        )
        row_residuals = _row_residuals(
            retailer="sephora",
            selected_variant=None,
            location_observed=False,
        )
        row_residuals.extend(
            [
                "sephora_grid_product_category_not_observed",
                "sephora_grid_availability_summary_not_observed",
            ]
        )
        if currency_code is None:
            row_residuals.append("sephora_grid_explicit_currency_code_not_observed")
        rows.append(
            RetailGridProjectionRow(
                row_id=f"{source_slice.slice_id}:grid:sephora:{product_id}",
                retailer="sephora",
                raw_ref=raw_ref,
                raw_anchor=placement_anchor,
                placements=[
                    RetailGridProjectionPlacement(
                        grid_position=index + 1, raw_anchor=placement_anchor
                    )
                ],
                source_visible_fields=fields,
                residuals=_dedupe(row_residuals),
            )
        )
    return rows, residuals, state, None


def _project_sephora_catalog_state(
    state: SephoraCatalogAggregateState,
    *,
    packet: SourceCapturePacket,
    source_slice: SourceCaptureSlice,
    raw_ref: RetailProjectionRawRef,
    raw_anchor: RetailProjectionRawAnchor,
) -> tuple[list[RetailGridProjectionRow], list[str]]:
    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    for index, product in enumerate(state.products):
        product_id = _text(product.get("productId"))
        product_url = _absolute_url(
            "https://www.sephora.com", _text(product.get("targetUrl"))
        )
        name = _text(product.get("displayName"))
        position = _integer(product.get("gridPosition")) or index + 1
        if product_id is None or product_url is None or name is None:
            residuals.append(
                f"{source_slice.slice_id}:sephora:catalog_grid_tile_identity_incomplete:"
                f"{index}"
            )
            continue
        current_sku = product.get("currentSku")
        current_sku = current_sku if isinstance(current_sku, dict) else {}
        page_index = (position - 1) // SEPHORA_CATALOG_PAGE_SIZE
        product_index = (position - 1) % SEPHORA_CATALOG_PAGE_SIZE
        pointer = (
            f"/page/catalogAggregate/pages/{page_index}/products/{product_index}"
        )
        placement_anchor = _with_anchor(raw_anchor, "json_pointer", pointer)
        price_display = _text(current_sku.get("listPrice"))
        price, price_range = _price_fields(price_display)
        fields = _base_fields(
            packet=packet, source_slice=source_slice, retailer="sephora"
        )
        fields.update(
            {
                "source_product_id": product_id,
                "product_url": product_url,
                "canonical_product_url": _canonical_url(product_url),
                "name": name,
                "brand": _text(product.get("brandName")),
                "grid_position": position,
                "category": state.category_name or state.category_slug,
                "breadcrumb": None,
                "selected_sku_id": _text(current_sku.get("skuId")),
                "selected_variant": None,
                "price": price,
                "price_display": price_display,
                "price_range": price_range,
                "price_currency": None,
                "currency_symbol": (
                    "$"
                    if price_display is not None and price_display.startswith("$")
                    else None
                ),
                "average_rating": _first_present(product.get("rating")),
                "rating_count": _first_present(product.get("reviews")),
                "review_count": _first_present(product.get("reviews")),
                "badges": [],
                "availability_summary": None,
                "pickup_eligible": None,
                "same_day_eligible": None,
                "visible_variant_count": None,
                "location_ids": [],
                "seller": "Sephora",
            }
        )
        row_residuals = _row_residuals(
            retailer="sephora",
            selected_variant=None,
            location_observed=False,
        )
        row_residuals.extend(
            [
                "sephora_catalog_grid_availability_summary_not_observed",
                "sephora_catalog_grid_explicit_currency_code_not_observed",
            ]
        )
        page = ((position - 1) // SEPHORA_CATALOG_PAGE_SIZE) + 1
        page_position = ((position - 1) % SEPHORA_CATALOG_PAGE_SIZE) + 1
        rows.append(
            RetailGridProjectionRow(
                row_id=f"{source_slice.slice_id}:grid:sephora:{product_id}",
                retailer="sephora",
                raw_ref=raw_ref,
                raw_anchor=placement_anchor,
                placements=[
                    RetailGridProjectionPlacement(
                        grid_position=position,
                        page=page,
                        page_position=page_position,
                        raw_anchor=placement_anchor,
                    )
                ],
                source_visible_fields=fields,
                residuals=_dedupe(row_residuals),
            )
        )
    return rows, residuals


def _merge_sephora_parent_rows(
    rows: list[RetailGridProjectionRow],
) -> tuple[list[RetailGridProjectionRow], list[str]]:
    by_product_id: dict[str, RetailGridProjectionRow] = {}
    residuals: list[str] = []
    for row in rows:
        product_id = str(row.source_visible_fields["source_product_id"])
        existing = by_product_id.get(product_id)
        if existing is None:
            by_product_id[product_id] = row
            continue
        placements = [*existing.placements, *row.placements]
        row_residuals = [
            *existing.residuals,
            f"sephora_grid_duplicate_parent_placement:{product_id}:{len(placements)}",
        ]
        if existing.source_visible_fields != row.source_visible_fields:
            row_residuals.append(
                f"sephora_grid_duplicate_parent_fields_differ:{product_id}"
            )
        by_product_id[product_id] = existing.model_copy(
            update={
                "placements": placements,
                "residuals": _dedupe(row_residuals),
            }
        )
        residuals.append(
            f"sephora_grid_duplicate_parent_placement:{product_id}:{len(placements)}"
        )
    return list(by_product_id.values()), residuals


def _sephora_grid_reconciliation(
    *,
    packet: SourceCapturePacket,
    rows: list[RetailGridProjectionRow],
    states: list[SephoraBrandGridState],
    residuals: list[str],
) -> tuple[dict[str, Any | None], RetailGridCompletenessReconciliation]:
    reconciliation_residuals: list[str] = []
    state = states[0] if len(states) == 1 else None
    if not states:
        reconciliation_residuals.append("sephora_grid_linkstore_state_absent")
    elif len(states) != 1:
        reconciliation_residuals.append(
            f"sephora_grid_linkstore_state_count:{len(states)}"
        )
    declared_count = state.total_products if state is not None else None
    placement_count = sum(max(1, len(row.placements)) for row in rows)
    duplicate_count = placement_count - len(rows)
    requested_slug = _requested_brand_slug(packet)
    observed_brand = state.brand_name if state is not None else None
    observed_target = state.target_url if state is not None else None
    subject_confirmed = (
        requested_slug is not None
        and observed_brand is not None
        and _slugify(observed_brand) == requested_slug
        and observed_target is not None
        and urlparse(observed_target).path.rstrip("/")
        == f"/brand/{requested_slug}"
    )
    if not subject_confirmed:
        reconciliation_residuals.append("sephora_grid_subject_binding_unconfirmed")
    if declared_count is None:
        reconciliation_residuals.append("sephora_grid_page_declared_count_absent")
    elif declared_count != len(rows):
        reconciliation_residuals.append(
            "sephora_grid_declared_unique_parent_count_mismatch:"
            f"declared={declared_count}:extracted={len(rows)}"
        )
    if state is not None and len(state.products) != placement_count:
        reconciliation_residuals.append(
            "sephora_grid_serialized_placement_count_mismatch:"
            f"serialized={len(state.products)}:anchored={placement_count}"
        )
    if any("identity_incomplete" in item for item in residuals):
        reconciliation_residuals.append(
            "sephora_grid_incomplete_product_identity_present"
        )
    complete = not reconciliation_residuals
    grid_facts: dict[str, Any | None] = {
        "retailer": "sephora",
        "page_kind": "brand_grid",
        "brand_id": state.brand_id if state is not None else None,
        "brand_name": observed_brand,
        "short_name": state.short_name if state is not None else None,
        "result_id": state.result_id if state is not None else None,
        "target_url": observed_target,
        "canonical_url": state.canonical_url if state is not None else None,
        "page_size": state.page_size if state is not None else None,
        "page_declared_result_count": declared_count,
        "serialized_product_placement_count": (
            len(state.products) if state is not None else None
        ),
        "requested_brand_slug": requested_slug,
        "subject_binding_confirmed": subject_confirmed,
        "explicit_currency_codes": (
            list(state.explicit_currency_codes) if state is not None else []
        ),
        "currency_evidence_paths": (
            list(state.currency_evidence_paths) if state is not None else []
        ),
        "delivery_location_pin": None,
    }
    return grid_facts, RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_count,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination=(
            "retailer_serialized_count_reconciled" if complete else "unproven"
        ),
        residuals=_dedupe(reconciliation_residuals),
    )


def _sephora_catalog_grid_reconciliation(
    *,
    packet: SourceCapturePacket,
    rows: list[RetailGridProjectionRow],
    states: list[SephoraCatalogAggregateState],
    brand_states: list[SephoraBrandGridState],
    residuals: list[str],
) -> tuple[dict[str, Any | None], RetailGridCompletenessReconciliation]:
    reconciliation_residuals: list[str] = []
    state = states[0] if len(states) == 1 else None
    if len(states) != 1:
        reconciliation_residuals.append(
            f"sephora_catalog_grid_state_count:{len(states)}"
        )
    if brand_states:
        reconciliation_residuals.append(
            f"sephora_catalog_grid_brand_state_collision:{len(brand_states)}"
        )

    requested = _requested_sephora_catalog(packet)
    requested_slug = requested[0] if requested is not None else None
    requested_start_page = requested[1] if requested is not None else None
    requested_sort = requested[2] if requested is not None else None
    subject_confirmed = (
        state is not None
        and requested_slug is not None
        and requested_slug == state.category_slug
        and urlparse(state.target_url).path.rstrip("/")
        == f"/shop/{requested_slug}"
    )
    if not subject_confirmed:
        reconciliation_residuals.append(
            "sephora_catalog_grid_subject_binding_unconfirmed"
        )
    if (
        state is None
        or requested_start_page != 1
        or state.requested_page_count < 1
        or state.requested_page_count > SEPHORA_CATALOG_MAX_PAGE
    ):
        reconciliation_residuals.append(
            "sephora_catalog_grid_requested_window_unconfirmed"
        )
    if (
        state is None
        or requested_sort != "BEST_SELLING"
        or state.sort_by != requested_sort
    ):
        reconciliation_residuals.append(
            "sephora_catalog_grid_bestseller_sort_unconfirmed"
        )
    countries = (
        [page.serialized_country for page in state.pages]
        if state is not None
        else []
    )
    if state is None or not countries or any(country != "US" for country in countries):
        reconciliation_residuals.append(
            "sephora_catalog_grid_serialized_us_country_unconfirmed"
        )

    placement_count = sum(max(1, len(row.placements)) for row in rows)
    duplicate_count = placement_count - len(rows)
    declared_count = state.total_products if state is not None else None
    requested_window_end = (
        min(
            state.requested_page_count * state.page_size,
            state.total_products,
        )
        if state is not None
        else None
    )
    page_numbers = (
        [page.requested_page for page in state.pages]
        if state is not None
        else []
    )
    if (
        state is None
        or page_numbers != list(range(1, state.requested_page_count + 1))
    ):
        reconciliation_residuals.append(
            f"sephora_catalog_grid_page_sequence_mismatch:{page_numbers}"
        )
    if requested_window_end is None or placement_count != requested_window_end:
        reconciliation_residuals.append(
            "sephora_catalog_grid_placement_window_mismatch:"
            f"placements={placement_count}:window={requested_window_end}"
        )
    serialized_count = len(state.products) if state is not None else None
    if serialized_count != placement_count:
        reconciliation_residuals.append(
            "sephora_catalog_grid_serialized_placement_count_mismatch:"
            f"serialized={serialized_count}:anchored={placement_count}"
        )
    if duplicate_count:
        reconciliation_residuals.append(
            f"sephora_catalog_grid_duplicate_parent_count:{duplicate_count}"
        )
    positions = sorted(
        placement.grid_position for row in rows for placement in row.placements
    )
    if (
        requested_window_end is None
        or positions != list(range(1, requested_window_end + 1))
    ):
        reconciliation_residuals.append(
            "sephora_catalog_grid_rank_sequence_non_contiguous"
        )
    if state is not None and state.has_more != (
        requested_window_end < state.total_products
    ):
        reconciliation_residuals.append(
            "sephora_catalog_grid_continuation_state_inconsistent"
        )
    traversal = state.traversal_observation if state is not None else {}
    if (
        state is None
        or traversal.get("capturedPageCount") != state.requested_page_count
        or traversal.get("extractedUniqueParentCount") != serialized_count
        or traversal.get("duplicatePlacementCount") != 0
        or traversal.get("termination")
        not in {"requested_page_window_reconciled", "retailer_terminal_reconciled"}
    ):
        reconciliation_residuals.append(
            "sephora_catalog_grid_traversal_receipt_unreconciled"
        )
    if any("identity_incomplete" in item for item in residuals):
        reconciliation_residuals.append(
            "sephora_catalog_grid_incomplete_product_identity_present"
        )

    complete = not reconciliation_residuals
    grid_facts: dict[str, Any | None] = {
        "retailer": "sephora",
        "page_kind": "catalog_grid",
        "category_slug": state.category_slug if state is not None else None,
        "category_name": state.category_name if state is not None else None,
        "category_id": state.category_id if state is not None else None,
        "result_ids": (
            [page.result_id for page in state.pages] if state is not None else []
        ),
        "target_url": state.target_url if state is not None else None,
        "requested_category_slug": requested_slug,
        "requested_start_page": requested_start_page,
        "requested_page_count": (
            state.requested_page_count if state is not None else None
        ),
        "requested_sort": requested_sort,
        "sort_label": "Bestselling" if state is not None else None,
        "window_start": 1 if state is not None else None,
        "window_end": requested_window_end,
        "page_declared_result_count": declared_count,
        "serialized_product_placement_count": serialized_count,
        "has_more": state.has_more if state is not None else None,
        "subject_binding_confirmed": subject_confirmed,
        "serialized_countries": countries,
        "delivery_location_pin": None,
    }
    return grid_facts, RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_count,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination=(
            str(traversal.get("termination"))
            if complete
            else "unproven"
        ),
        residuals=_dedupe(reconciliation_residuals),
    )


def _project_walmart_next_data(
    text: str,
    *,
    packet: SourceCapturePacket,
    source_slice: SourceCaptureSlice,
    raw_ref: RetailProjectionRawRef,
    raw_anchor: RetailProjectionRawAnchor,
) -> tuple[list[RetailGridProjectionRow], list[str]]:
    match = _NEXT_DATA_RE.search(text)
    if match is None:
        return [], []
    try:
        payload = json.loads(match.group("json"))
    except json.JSONDecodeError as exc:
        raise RetailGridProjectionInputError("Walmart __NEXT_DATA__ is malformed") from exc

    stacks = _nested_value(
        payload, "props", "pageProps", "initialData", "searchResult", "itemStacks"
    )
    if not isinstance(stacks, list):
        return [], []

    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    for stack_index, stack in enumerate(stacks):
        items = stack.get("items") if isinstance(stack, dict) else None
        if not isinstance(items, list):
            continue
        for item_index, item in enumerate(items):
            if not isinstance(item, dict) or item.get("__typename") != "Product":
                continue
            product_id = _text(item.get("usItemId"))
            product_url = _absolute_url("https://www.walmart.com", _text(item.get("canonicalUrl")))
            name = _text(item.get("name"))
            if product_id is None or product_url is None or name is None:
                residuals.append(
                    f"{source_slice.slice_id}:walmart:grid_tile_identity_incomplete:"
                    f"{stack_index}:{item_index}"
                )
                continue
            pointer = (
                f"/props/pageProps/initialData/searchResult/itemStacks/{stack_index}"
                f"/items/{item_index}"
            )
            fields = _base_fields(packet=packet, source_slice=source_slice, retailer="walmart")
            fields.update(
                {
                    "source_product_id": product_id,
                    "product_url": product_url,
                    "name": name,
                    "selected_variant": _walmart_selected_variant(item, product_id),
                    "price": _walmart_price(item),
                    "price_currency": _fact_value(source_slice.currency_pin),
                    "currency_symbol": "$" if _walmart_price_text(item).startswith("$") else None,
                    "average_rating": _first_present(item.get("averageRating"), _nested_value(item, "rating", "averageRating")),
                    "rating_count": _first_present(item.get("numberOfReviews"), _nested_value(item, "rating", "numberOfReviews")),
                    "written_review_count": None,
                    "availability_summary": _first_present(
                        _nested_value(item, "availabilityStatusV2", "display"),
                        item.get("availabilityStatusDisplayValue"),
                    ),
                    "shipping_availability": _walmart_fulfilment_badge(item, "FF_SHIPPING"),
                    "pickup_availability": _walmart_fulfilment_badge(item, "FF_PICKUP"),
                    "delivery_availability": _walmart_fulfilment_badge(item, "FF_DELIVERY"),
                    "location_ids": _walmart_location_ids(item),
                    "seller": _text(item.get("sellerName")),
                }
            )
            row_residuals = _row_residuals(
                retailer="walmart",
                selected_variant=fields["selected_variant"],
                location_observed=bool(fields["location_ids"]),
            )
            rows.append(
                RetailGridProjectionRow(
                    row_id=(
                        f"{source_slice.slice_id}:grid:walmart:{stack_index}:{item_index}:"
                        f"{product_id or 'missing'}"
                    ),
                    retailer="walmart",
                    raw_ref=raw_ref,
                    raw_anchor=_with_anchor(raw_anchor, "json_pointer", pointer),
                    source_visible_fields=fields,
                    residuals=row_residuals,
                )
            )
    return rows, residuals


def _load_target_grid_content_record(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(value, dict)
        or value.get("content_record_version")
        not in _SUPPORTED_TARGET_GRID_CONTENT_RECORD_VERSIONS
    ):
        return None
    if not isinstance(value.get("pages"), list):
        raise RetailGridProjectionInputError("Target grid content record pages are absent")
    return value


def _load_amazon_grid_content_record(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(value, dict)
        or value.get("content_record_version") != AMAZON_GRID_CONTENT_RECORD_VERSION
    ):
        return None
    if not isinstance(value.get("pages"), list):
        raise RetailGridProjectionInputError("Amazon grid content record pages are absent")
    return value


def _parse_amazon_grid_page(
    rendered_dom: str,
    *,
    page_number: int,
    page_url: str,
) -> dict[str, object]:
    matches = list(_AMAZON_CARD_RE.finditer(rendered_dom))
    boundary_source = _SCRIPT_OR_STYLE_RE.sub(
        lambda match: " " * (match.end() - match.start()), rendered_dom
    )
    products: list[dict[str, object | None]] = []
    residuals: list[str] = []
    occurrences_by_asin: dict[str, int] = {}
    for position, match in enumerate(matches, start=1):
        asin = match.group("asin").upper()
        end = _target_card_end(boundary_source, match.start())
        if end is None:
            residuals.append(
                f"amazon_grid_card_boundary_unproven:{page_number}:{position}:{asin}"
            )
            end = (
                matches[position].start()
                if position < len(matches)
                else match.end()
            )
        card = rendered_dom[match.start() : end]
        occurrence = occurrences_by_asin.get(asin, 0) + 1
        occurrences_by_asin[asin] = occurrence
        href = _first_regex(
            card,
            (
                rf"\bhref=[\"']([^\"']*/dp/{re.escape(asin)}(?:[/?][^\"']*)?)[\"']",
                rf"\bhref=[\"']([^\"']*/gp/product/{re.escape(asin)}(?:[/?][^\"']*)?)[\"']",
                r"<a\b(?=[^>]*\bhref=[\"']([^\"']+)[\"'])[^>]*>"
                r"(?:(?!</a>).)*?<h2\b",
                r"<h2\b[^>]*>(?:(?!</h2>).)*?<a\b"
                r"(?=[^>]*\bhref=[\"']([^\"']+)[\"'])",
            ),
        )
        product_url = _absolute_url(
            "https://www.amazon.com",
            html_module.unescape(href) if href is not None else None,
        )
        heading_candidates: list[tuple[str | None, str | None]] = []
        for heading in re.finditer(
            r"<h2\b(?P<attrs>[^>]*)>(?P<body>.*?)</h2>",
            card,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            aria_label = _first_regex(
                heading.group("attrs"), (r"\baria-label=[\"']([^\"']+)[\"']",)
            )
            heading_candidates.append((aria_label, _html_text(heading.group("body"))))
        name = next(
            (html_module.unescape(label) for label, _ in heading_candidates if label),
            None,
        )
        if name is None:
            texts = [text for _, text in heading_candidates if text]
            name = max(texts, key=len) if texts else None
        if product_url is None or name is None:
            residuals.append(
                f"amazon_grid_card_identity_incomplete:{page_number}:{position}:{asin}"
            )

        price_display = _first_regex(
            card,
            (
                r"<span\b[^>]*class=[\"'][^\"']*a-offscreen[^\"']*[\"'][^>]*>\s*(\$\d[\d,]*(?:\.\d{2})?)",
            ),
        )
        rating_match = re.search(
            r"aria-label=[\"'](?P<rating>[0-9.]+)\s+out of 5 stars(?:, rating details)?[\"']",
            card,
            flags=re.IGNORECASE,
        )
        rating_count = _first_regex(
            card,
            (
                r"aria-label=[\"']([0-9][0-9,]*)\s+ratings?[\"']",
                r">\s*\(([0-9][0-9,]*)\)\s*<",
            ),
        )
        plain_text = _html_text(card) or ""
        bought_recently = _first_regex(
            plain_text,
            (r"([0-9][0-9,.]*[KMB]?\+?\s+bought in past month)",),
        )
        delivery_text = _amazon_delivery_block_text(card)
        source_index = _first_regex(match.group(0), (r"\bdata-index=[\"'](\d+)[\"']",))
        products.append(
            {
                "product_id": asin,
                "product_url": product_url,
                "name": name,
                "page": page_number,
                "page_position": position,
                "page_occurrence": occurrence,
                "source_index": int(source_index) if source_index is not None else None,
                "price_display": price_display,
                "price": (
                    price_display.lstrip("$").replace(",", "")
                    if price_display is not None
                    else None
                ),
                "currency_symbol": "$" if price_display is not None else None,
                "average_rating": rating_match.group("rating") if rating_match else None,
                "rating_count": (
                    rating_count.replace(",", "") if rating_count is not None else None
                ),
                "availability_summary": delivery_text,
                "shipping_availability": None,
                "pickup_availability": None,
                "delivery_availability": delivery_text,
                "visible_fulfilment_text": [delivery_text] if delivery_text else [],
                "sponsored_posture": (
                    "sponsored"
                    if re.search(r"\bSponsored\b", plain_text, re.IGNORECASE)
                    else "organic"
                ),
                "retailer_merchandising_labels": [],
                "bought_recently_text": bought_recently,
            }
        )

    page_text = _html_text(rendered_dom) or ""
    range_match = re.search(
        r"(?<!\d)(?P<start>\d[\d,]*)\s*[-\u2013]\s*(?P<end>\d[\d,]*)"
        r"\s+of\s+(?:over\s+)?(?P<total>\d[\d,]*)\s+results?\s+for\b",
        page_text,
        flags=re.IGNORECASE,
    )
    result_range = (
        {
            key: int(range_match.group(key).replace(",", ""))
            for key in ("start", "end", "total")
        }
        if range_match is not None
        else None
    )
    if not products:
        residuals.append(f"amazon_grid_product_cards_absent:{page_number}")
    if result_range is None:
        residuals.append(f"amazon_grid_result_range_absent:{page_number}")
    requested_query = extract_amazon_search_query_from_url(page_url)
    zip_match = re.search(
        r"(?:Deliver to|delivery location)[^<\d]{0,80}(?P<zip>\d{5})(?!\d)",
        rendered_dom,
        flags=re.IGNORECASE,
    )
    return {
        "page": page_number,
        "url": page_url,
        "observed_query": requested_query,
        "result_range": result_range,
        "delivery_zip": zip_match.group("zip") if zip_match else None,
        "us_marketplace_confirmed": any(
            marker in rendered_dom for marker in _AMAZON_US_MARKETPLACE_MARKERS
        ),
        "products": products,
        "residuals": _dedupe(residuals),
    }


def _amazon_delivery_block_text(card: str) -> str | None:
    match = re.search(
        r"<div\b(?=[^>]*\bdata-cy=[\"']delivery-block[\"'])[^>]*>",
        card,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    end = _target_card_end(card, match.start())
    return _html_text(card[match.start() : end]) if end is not None else None


def _parse_target_grid_page(
    rendered_dom: str,
    *,
    page_number: int,
    subject_kind: str | None = None,
) -> dict[str, object]:
    matches = list(_TARGET_CARD_RE.finditer(rendered_dom))
    boundary_source = _SCRIPT_OR_STYLE_RE.sub(
        lambda match: " " * (match.end() - match.start()), rendered_dom
    )
    products: list[dict[str, object | None]] = []
    residuals: list[str] = []
    occurrences_by_product_id: dict[str, int] = {}
    for index, match in enumerate(matches):
        end = _target_card_end(boundary_source, match.start())
        if end is None:
            residuals.append(
                f"target_grid_card_boundary_unproven:{page_number}:{index + 1}:"
                f"{match.group('product_id')}"
            )
            end = matches[index + 1].start() if index + 1 < len(matches) else match.end()
        card = rendered_dom[match.start() : end]
        product_id = match.group("product_id")
        occurrence = occurrences_by_product_id.get(product_id, 0) + 1
        occurrences_by_product_id[product_id] = occurrence
        content_anchor = next(
            (
                anchor
                for anchor in re.finditer(
                    r"<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a>",
                    card,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if re.search(
                    r"\bdata-test=[\"']content[\"']",
                    anchor.group("attrs"),
                    flags=re.IGNORECASE,
                )
            ),
            None,
        )
        content_href = (
            _first_regex(
                content_anchor.group("attrs"),
                (r"\bhref=[\"']([^\"']*/p/[^\"']+)[\"']",),
            )
            if content_anchor is not None
            else None
        )
        product_url = _absolute_url(
            "https://www.target.com",
            content_href
            or _first_regex(card, (r"href=[\"']([^\"']*/p/[^\"']+)[\"']",)),
        )
        legacy_name = _first_regex(
            card,
            (
                r"<a[^>]+aria-label=[\"']([^\"']+)[\"'][^>]+data-test=[\"']@web/ProductCard/title[\"']",
                r"data-test=[\"']@web/ProductCard/title[\"'][^>]+aria-label=[\"']([^\"']+)[\"']",
            ),
        )
        heading_match = re.search(
            r"<h3\b[^>]*>(?P<body>.*?)</h3>",
            content_anchor.group("body") if content_anchor is not None else card,
            re.I | re.S,
        )
        name = (
            html_module.unescape(legacy_name)
            if legacy_name is not None
            else _html_text(heading_match.group("body"))
            if heading_match is not None
            else None
        )
        identity_residual = product_url is None or name is None
        if identity_residual:
            residuals.append(
                f"target_grid_card_identity_incomplete:{page_number}:{index + 1}:{product_id}"
            )

        price_display = _first_regex(
            card,
            (r"data-test=[\"']current-price[\"'][^>]*>\s*<span>\s*([^<]+)",),
        )
        if price_display is None:
            heading_region = (
                content_anchor.group("body") if content_anchor is not None else card
            )
            price_region = (
                heading_region[: heading_match.start()]
                if heading_match is not None
                else heading_region
            )
            price_display = _first_regex(price_region, (r"(\$\d+(?:\.\d{2})?)",))
        price_display = html_module.unescape(price_display) if price_display else None

        rating_match = re.search(
            r"aria-label=[\"'](?:Average customer rating is\s+)?([0-9.]+)"
            r"(?:\s+out of 5)?\s+stars?\s+with\s+([0-9,]+)\s+"
            r"(?:ratings?|reviews?)\.??[\"']",
            card,
            flags=re.IGNORECASE,
        )
        pickup = _target_channel_text(card, "Pickup")
        delivery = _target_channel_text(card, "Delivery")
        shipping = _target_channel_text(card, "Shipping")
        overall_availability = _first_regex(
            card,
            (
                r"data-test=[\"']lowStockMessaging[\"'][^>]*>.*?"
                r"<span[^>]*>([^<]+)</span>",
            ),
        )
        plain_text = _html_text(card) or ""
        merchandising_labels = _dedupe(
            label
            for label in (
                "Bestseller",
                "Highly rated",
                "Rarely returned",
                "New at Target",
            )
            if label.casefold() in plain_text.casefold()
        )
        bought_recently_text = _first_regex(
            plain_text,
            (r"(\d+(?:\.\d+)?[kKmM]?\+\s+bought in last month)",),
        )
        visible_fulfilment = _dedupe(
            value
            for value in (
                pickup,
                delivery,
                shipping,
                "Shipping dates may vary" if "Shipping dates may vary" in plain_text else None,
                "Free 2-Day Shipping" if "Free 2-Day Shipping" in plain_text else None,
            )
            if value
        )
        products.append(
            {
                "product_id": product_id,
                "product_url": product_url,
                "name": name,
                "page": page_number,
                "page_position": index + 1,
                "page_occurrence": occurrence,
                "price_display": price_display,
                "price": price_display.lstrip("$").strip() if price_display else None,
                "currency_symbol": (
                    "$" if price_display is not None and price_display.startswith("$") else None
                ),
                "average_rating": rating_match.group(1) if rating_match else None,
                "rating_count": (
                    rating_match.group(2).replace(",", "")
                    if rating_match
                    else None
                ),
                "availability_summary": (
                    html_module.unescape(overall_availability)
                    if overall_availability
                    else None
                ),
                "shipping_availability": shipping,
                "pickup_availability": pickup,
                "delivery_availability": delivery,
                "visible_fulfilment_text": visible_fulfilment,
                "sponsored_posture": "sponsored" if "Sponsored" in plain_text else None,
                "retailer_merchandising_labels": merchandising_labels,
                "bought_recently_text": bought_recently_text,
            }
        )

    page_text = _html_text(rendered_dom) or ""
    declared_match = re.search(
        r"(?<!\d)(?P<count>\d[\d,]*)\s+results\b", page_text, re.IGNORECASE
    )
    title_match = re.search(r"<title\b[^>]*>(?P<title>.*?)</title>", rendered_dom, re.I | re.S)
    title_text = _html_text(title_match.group("title")) if title_match is not None else None
    observed_query: str | None = None
    if title_text is not None:
        query_match = re.fullmatch(
            r'\s*"?(?P<query>.+?)"?\s*(?:\:\s*Page\s+\d+)?\s*:\s*Target\s*',
            title_text,
            flags=re.IGNORECASE,
        )
        if query_match is not None:
            observed_query = query_match.group("query").strip().strip('"')
    page_heading_match = re.search(
        r"<h1\b[^>]*>(?P<heading>.*?)</h1>",
        rendered_dom,
        flags=re.IGNORECASE | re.DOTALL,
    )
    observed_brand = (
        _html_text(page_heading_match.group("heading"))
        if page_heading_match is not None
        else None
    )
    observed_subject = observed_brand if subject_kind == "brand" else observed_query
    zip_match = re.search(
        r"aria-label=[\"']Ship to location:\s*(?P<zip>\d{5})[\"']",
        rendered_dom,
        re.IGNORECASE,
    )
    return {
        "page": page_number,
        "declared_result_count": (
            int(declared_match.group("count").replace(",", ""))
            if declared_match is not None
            else None
        ),
        "observed_query": observed_query,
        "observed_brand": observed_brand,
        "observed_subject": observed_subject,
        "delivery_zip": zip_match.group("zip") if zip_match is not None else None,
        "products": products,
        "residuals": _dedupe(residuals),
    }


def _target_card_end(rendered_dom: str, start: int) -> int | None:
    depth = 0
    for boundary in _DIV_BOUNDARY_RE.finditer(rendered_dom, start):
        if boundary.group("closing"):
            depth -= 1
            if depth == 0:
                return boundary.end()
            if depth < 0:
                return None
        else:
            depth += 1
    return None


def _html_text(value: str) -> str | None:
    # Script and style bodies survive tag stripping as ordinary text, so
    # serialized page state would otherwise be read as retailer-rendered text.
    text = re.sub(r"<[^>]+>", " ", _SCRIPT_OR_STYLE_RE.sub(" ", value))
    normalized = " ".join(html_module.unescape(text).split())
    return normalized or None


def _observation_list(state: dict[str, Any] | None, key: str) -> list[Any]:
    value = state.get(key) if state is not None else None
    return list(value) if isinstance(value, list) else []


def _target_requested_query(url: str) -> str | None:
    values = parse_qs(urlparse(url).query).get("searchTerm")
    if not values or not values[0].strip():
        return None
    return values[0].strip()


def _target_requested_query_from_packet(packet: SourceCapturePacket) -> str | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        query = _target_requested_query(locator)
        if query is not None:
            return query
    return None


def _target_requested_subject_from_packet(
    packet: SourceCapturePacket,
) -> tuple[str, str] | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        subject = extract_target_grid_subject_from_url(locator)
        if subject is not None:
            return subject
    return None


def _normalize_query(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalize_target_subject(value: str | None, *, kind: str | None) -> str:
    if value is None:
        return ""
    if kind == "brand":
        return re.sub(r"[^a-z0-9]+", "", value.casefold())
    return _normalize_query(value)


def _target_grid_sort_order(url: str) -> str | None:
    for key, values in parse_qs(urlparse(url).query).items():
        if key.casefold() == "sortby" and values:
            return values[0].casefold()
    return None


def _project_target_cards(
    text: str,
    *,
    packet: SourceCapturePacket,
    source_slice: SourceCaptureSlice,
    raw_ref: RetailProjectionRawRef,
    raw_anchor: RetailProjectionRawAnchor,
) -> tuple[list[RetailGridProjectionRow], list[str], dict[str, Any] | None]:
    content_record = _load_target_grid_content_record(text)
    if content_record is not None:
        placements = [
            (page_index, product_index, product)
            for page_index, page in enumerate(content_record["pages"])
            if isinstance(page, dict) and isinstance(page.get("products"), list)
            for product_index, product in enumerate(page["products"])
            if isinstance(product, dict)
        ]
    else:
        page = _parse_target_grid_page(text, page_number=1)
        placements = [
            (0, product_index, product)
            for product_index, product in enumerate(page["products"])
            if isinstance(product, dict)
        ]

    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    for global_index, (page_index, product_index, product) in enumerate(placements):
        product_id = _text(product.get("product_id"))
        product_url = _text(product.get("product_url"))
        name = _text(product.get("name"))
        if product_id is None or product_url is None or name is None:
            residuals.append(
                f"{source_slice.slice_id}:target:grid_card_identity_incomplete:"
                f"{page_index + 1}:{product_index + 1}"
            )
            continue
        if content_record is not None:
            anchor = _with_anchor(
                raw_anchor,
                "json_pointer",
                f"/pages/{page_index}/products/{product_index}",
            )
        else:
            anchor = _with_anchor(
                raw_anchor,
                "html_selector",
                f':nth-match([data-focusid="{product_id}_product_card"], '
                f'{product.get("page_occurrence", 1)})',
            )
        page_number = _integer(product.get("page")) or page_index + 1
        page_position = _integer(product.get("page_position")) or product_index + 1
        fields = _base_fields(packet=packet, source_slice=source_slice, retailer="target")
        fields.update(
            {
                "source_product_id": product_id,
                "product_url": product_url,
                "canonical_product_url": _canonical_url(product_url),
                "name": name,
                "selected_variant": None,
                "price": _text(product.get("price")),
                "price_display": _text(product.get("price_display")),
                "price_currency": None,
                "currency_symbol": product.get("currency_symbol"),
                "average_rating": _text(product.get("average_rating")),
                "rating_count": _text(product.get("rating_count")),
                "written_review_count": None,
                "availability_summary": _text(product.get("availability_summary")),
                "shipping_availability": _text(product.get("shipping_availability")),
                "pickup_availability": _text(product.get("pickup_availability")),
                "delivery_availability": _text(product.get("delivery_availability")),
                "visible_fulfilment_text": product.get("visible_fulfilment_text", []),
                "sponsored_posture": _text(product.get("sponsored_posture")),
                "retailer_merchandising_labels": product.get(
                    "retailer_merchandising_labels", []
                ),
                "bought_recently_text": _text(product.get("bought_recently_text")),
                "location_pin": (
                    content_record.get("delivery_zip")
                    if content_record is not None
                    else None
                ),
                "location_ids": [],
                "seller": None,
            }
        )
        placement = RetailGridProjectionPlacement(
            grid_position=global_index + 1,
            page=page_number,
            page_position=page_position,
            raw_anchor=anchor,
        )
        rows.append(
            RetailGridProjectionRow(
                row_id=(
                    f"{source_slice.slice_id}:grid:target:{global_index}:{product_id}"
                ),
                retailer="target",
                raw_ref=raw_ref,
                raw_anchor=anchor,
                placements=[placement],
                source_visible_fields=fields,
                residuals=_row_residuals(
                    retailer="target",
                    selected_variant=None,
                    location_observed=fields["location_pin"] is not None,
                ),
            )
        )
    state = content_record
    if state is None and rows:
        state = {
            "content_record_version": "target_grid_rendered_dom_v0",
            "requested_subject_kind": None,
            "requested_subject": None,
            "observed_subjects": [],
            "requested_query": None,
            "observed_queries": [],
            "sort_order": None,
            "delivery_zip": None,
            "declared_result_count": None,
            "page_load_count": 1,
            "traversal_termination": "unproven",
            "residuals": list(page["residuals"]),
        }
    return rows, residuals, state


def _merge_target_parent_rows(
    rows: list[RetailGridProjectionRow],
) -> tuple[list[RetailGridProjectionRow], list[str]]:
    by_product_id: dict[str, RetailGridProjectionRow] = {}
    residuals: list[str] = []
    placement_fields = {"location_pin"}
    for row in rows:
        product_id = str(row.source_visible_fields["source_product_id"])
        existing = by_product_id.get(product_id)
        if existing is None:
            by_product_id[product_id] = row
            continue
        placements = [*existing.placements, *row.placements]
        row_residuals = [
            *existing.residuals,
            f"target_grid_duplicate_parent_placement:{product_id}:{len(placements)}",
        ]
        comparable_existing = {
            key: value
            for key, value in existing.source_visible_fields.items()
            if key not in placement_fields
        }
        comparable_row = {
            key: value
            for key, value in row.source_visible_fields.items()
            if key not in placement_fields
        }
        if comparable_existing != comparable_row:
            row_residuals.append(
                f"target_grid_duplicate_parent_fields_differ:{product_id}"
            )
        by_product_id[product_id] = existing.model_copy(
            update={"placements": placements, "residuals": _dedupe(row_residuals)}
        )
        residuals.append(
            f"target_grid_duplicate_parent_placement:{product_id}:{len(placements)}"
        )
    return list(by_product_id.values()), residuals


def _target_grid_reconciliation(
    *,
    packet: SourceCapturePacket,
    rows: list[RetailGridProjectionRow],
    states: list[dict[str, Any]],
    residuals: list[str],
) -> tuple[dict[str, Any | None], RetailGridCompletenessReconciliation]:
    reconciliation_residuals: list[str] = []
    state = states[0] if len(states) == 1 else None
    if not states:
        reconciliation_residuals.append("target_grid_content_record_absent")
    elif len(states) != 1:
        reconciliation_residuals.append(
            f"target_grid_content_record_count:{len(states)}"
        )
    requested_subject = _target_requested_subject_from_packet(packet)
    requested_subject_kind = requested_subject[0] if requested_subject else None
    requested_subject_value = requested_subject[1] if requested_subject else None
    requested_query = (
        requested_subject_value
        if requested_subject_kind == "search_query"
        else None
    )
    observed_subjects = (
        state.get("observed_subjects", []) if state is not None else []
    )
    if (
        not observed_subjects
        and requested_subject_kind == "search_query"
        and state is not None
    ):
        observed_subjects = state.get("observed_queries", [])
    subject_confirmed = bool(
        requested_subject_value
        and isinstance(observed_subjects, list)
        and observed_subjects
        and all(
            isinstance(value, str)
            and _normalize_target_subject(value, kind=requested_subject_kind)
            == _normalize_target_subject(
                requested_subject_value, kind=requested_subject_kind
            )
            for value in observed_subjects
        )
    )
    if not subject_confirmed:
        reconciliation_residuals.append("target_grid_subject_binding_unconfirmed")
    placement_count = sum(max(1, len(row.placements)) for row in rows)
    duplicate_count = placement_count - len(rows)
    declared_count = (
        state.get("declared_result_count") if state is not None else None
    )
    if not isinstance(declared_count, int):
        declared_count = None
        reconciliation_residuals.append("target_grid_page_declared_count_absent")
    elif declared_count != placement_count:
        reconciliation_residuals.append(
            "target_grid_declared_placement_count_mismatch:"
            f"declared={declared_count}:placements={placement_count}"
        )
    # Traversal terminates against the count visible on the current page. A live
    # assortment change during the multi-page walk is retained as an advisory
    # residual when the final visible count, placements, identities, subject,
    # sort, and termination otherwise reconcile. This truthfully describes a
    # mostly complete longitudinal observation without pretending that every
    # page came from a frozen retailer snapshot.
    declared_observations = [
        value
        for value in _observation_list(state, "declared_result_count_observations")
        if isinstance(value, int) and not isinstance(value, bool)
    ]
    advisory_residuals: list[str] = []
    if len(set(declared_observations)) > 1:
        advisory_residuals.append(
            "target_grid_declared_count_changed_during_traversal:"
            f"minimum={min(declared_observations)}:"
            f"maximum={max(declared_observations)}"
        )
    termination = state.get("traversal_termination") if state is not None else None
    if termination != "retailer_declared_count_reconciled":
        reconciliation_residuals.append("target_grid_termination_unproven")
    if any("identity_incomplete" in item for item in residuals):
        reconciliation_residuals.append("target_grid_incomplete_product_identity_present")
    if state is not None:
        reconciliation_residuals.extend(
            str(value) for value in state.get("residuals", []) if isinstance(value, str)
        )
    sort_order = state.get("sort_order") if state is not None else None
    if sort_order != "bestselling":
        reconciliation_residuals.append("target_grid_bestseller_sort_unconfirmed")
    complete = not reconciliation_residuals
    grid_facts: dict[str, Any | None] = {
        "retailer": "target",
        "page_kind": (
            "brand_grid" if requested_subject_kind == "brand" else "search_grid"
        ),
        "requested_subject_kind": requested_subject_kind,
        "requested_subject": requested_subject_value,
        "observed_subjects": observed_subjects,
        "requested_query": requested_query,
        "observed_queries": (
            state.get("observed_queries", []) if state is not None else []
        ),
        "sort_order": sort_order,
        "delivery_zip": state.get("delivery_zip") if state is not None else None,
        "page_load_count": state.get("page_load_count") if state is not None else None,
        "page_declared_result_count": declared_count,
        "declared_result_count_observations": _observation_list(
            state, "declared_result_count_observations"
        ),
        "extracted_placement_count": placement_count,
        "duplicate_placement_count": duplicate_count,
        "subject_binding_confirmed": subject_confirmed,
    }
    return grid_facts, RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_count,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination="retailer_visible_count_reconciled" if complete else "unproven",
        residuals=_dedupe([*reconciliation_residuals, *advisory_residuals]),
    )


def _project_amazon_cards(
    text: str,
    *,
    packet: SourceCapturePacket,
    source_slice: SourceCaptureSlice,
    raw_ref: RetailProjectionRawRef,
    raw_anchor: RetailProjectionRawAnchor,
) -> tuple[list[RetailGridProjectionRow], list[str], dict[str, Any] | None]:
    content_record = _load_amazon_grid_content_record(text)
    if content_record is None:
        return [], [], None
    placements = [
        (page_index, product_index, product)
        for page_index, page in enumerate(content_record["pages"])
        if isinstance(page, dict) and isinstance(page.get("products"), list)
        for product_index, product in enumerate(page["products"])
        if isinstance(product, dict)
    ]
    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    for global_index, (page_index, product_index, product) in enumerate(placements):
        asin = _text(product.get("product_id"))
        product_url = _text(product.get("product_url"))
        name = _text(product.get("name"))
        if asin is None or product_url is None or name is None:
            residuals.append(
                f"{source_slice.slice_id}:amazon:grid_card_identity_incomplete:"
                f"{page_index + 1}:{product_index + 1}"
            )
            continue
        anchor = _with_anchor(
            raw_anchor,
            "json_pointer",
            f"/pages/{page_index}/products/{product_index}",
        )
        page_number = _integer(product.get("page")) or page_index + 1
        page_position = _integer(product.get("page_position")) or product_index + 1
        placement_source_visible_fields = {
            "page": page_number,
            "page_position": page_position,
            "source_result_index": product.get("source_index"),
            "product_url": product_url,
            "availability_summary": _text(product.get("availability_summary")),
            "delivery_availability": _text(product.get("delivery_availability")),
            "visible_fulfilment_text": product.get("visible_fulfilment_text", []),
            "sponsored_posture": _text(product.get("sponsored_posture")),
        }
        fields = _base_fields(packet=packet, source_slice=source_slice, retailer="amazon")
        fields.update(
            {
                "source_product_id": asin,
                "product_url": product_url,
                "canonical_product_url": _amazon_canonical_product_url(product_url),
                "name": name,
                "selected_variant": None,
                "price": _text(product.get("price")),
                "price_display": _text(product.get("price_display")),
                "price_currency": None,
                "currency_symbol": product.get("currency_symbol"),
                "average_rating": _text(product.get("average_rating")),
                "rating_count": _text(product.get("rating_count")),
                "written_review_count": None,
                "availability_summary": _text(product.get("availability_summary")),
                "shipping_availability": _text(product.get("shipping_availability")),
                "pickup_availability": _text(product.get("pickup_availability")),
                "delivery_availability": _text(product.get("delivery_availability")),
                "visible_fulfilment_text": product.get("visible_fulfilment_text", []),
                "sponsored_posture": _text(product.get("sponsored_posture")),
                "retailer_merchandising_labels": product.get(
                    "retailer_merchandising_labels", []
                ),
                "bought_recently_text": _text(product.get("bought_recently_text")),
                "location_pin": content_record.get("delivery_zip"),
                "location_binding": content_record.get("location_binding"),
                "source_result_index": product.get("source_index"),
                "placement_source_visible_fields": [placement_source_visible_fields],
                "location_ids": [],
                "seller": None,
            }
        )
        placement = RetailGridProjectionPlacement(
            grid_position=global_index + 1,
            page=page_number,
            page_position=page_position,
            raw_anchor=anchor,
        )
        rows.append(
            RetailGridProjectionRow(
                row_id=f"{source_slice.slice_id}:grid:amazon:{global_index}:{asin}",
                retailer="amazon",
                raw_ref=raw_ref,
                raw_anchor=anchor,
                placements=[placement],
                source_visible_fields=fields,
                residuals=_row_residuals(
                    retailer="amazon",
                    selected_variant=None,
                    location_observed=content_record.get("location_binding") is not None,
                ),
            )
        )
    return rows, residuals, content_record


def _merge_amazon_parent_rows(
    rows: list[RetailGridProjectionRow],
) -> tuple[list[RetailGridProjectionRow], list[str]]:
    by_asin: dict[str, RetailGridProjectionRow] = {}
    residuals: list[str] = []
    placement_fields = {
        "availability_summary",
        "delivery_availability",
        "visible_fulfilment_text",
        "sponsored_posture",
        "source_result_index",
        "placement_source_visible_fields",
    }
    for row in rows:
        asin = str(row.source_visible_fields["source_product_id"])
        existing = by_asin.get(asin)
        if existing is None:
            by_asin[asin] = row
            continue
        placements = [*existing.placements, *row.placements]
        row_residuals = [
            *existing.residuals,
            f"amazon_grid_duplicate_parent_placement:{asin}:{len(placements)}",
        ]
        comparable_existing = {
            key: value
            for key, value in existing.source_visible_fields.items()
            if key not in placement_fields
        }
        comparable_row = {
            key: value
            for key, value in row.source_visible_fields.items()
            if key not in placement_fields
        }
        if comparable_existing != comparable_row:
            row_residuals.append(f"amazon_grid_duplicate_parent_fields_differ:{asin}")
        # The merged parent keeps the first placement's per-placement fields, so a
        # value that genuinely varies between placements (Amazon routinely repeats an
        # organic ASIN as a later sponsored card) would otherwise be silently dropped
        # and the surviving value would misdescribe the discarded placement. Name the
        # divergence per field so the record states what varied instead of asserting
        # one placement's fact for every placement.
        merged_fields = dict(existing.source_visible_fields)
        existing_placement_facts = existing.source_visible_fields.get(
            "placement_source_visible_fields", []
        )
        row_placement_facts = row.source_visible_fields.get(
            "placement_source_visible_fields", []
        )
        merged_fields["placement_source_visible_fields"] = [
            *(existing_placement_facts if isinstance(existing_placement_facts, list) else []),
            *(row_placement_facts if isinstance(row_placement_facts, list) else []),
        ]
        for key in sorted(placement_fields - {"placement_source_visible_fields"}):
            if existing.source_visible_fields.get(key) != row.source_visible_fields.get(key):
                divergence = f"amazon_grid_duplicate_parent_placement_field_differs:{asin}:{key}"
                row_residuals.append(divergence)
                residuals.append(divergence)
                merged_fields[key] = None
        by_asin[asin] = existing.model_copy(
            update={
                "placements": placements,
                "source_visible_fields": merged_fields,
                "residuals": _dedupe(row_residuals),
            }
        )
        residuals.append(
            f"amazon_grid_duplicate_parent_placement:{asin}:{len(placements)}"
        )
    return list(by_asin.values()), residuals


def _amazon_requested_query_from_packet(packet: SourceCapturePacket) -> str | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        query = extract_amazon_search_query_from_url(locator)
        if query is not None:
            return query
    return None


def _amazon_grid_reconciliation(
    *,
    packet: SourceCapturePacket,
    rows: list[RetailGridProjectionRow],
    states: list[dict[str, Any]],
    residuals: list[str],
) -> tuple[dict[str, Any | None], RetailGridCompletenessReconciliation]:
    reconciliation_residuals: list[str] = []
    state = states[0] if len(states) == 1 else None
    if not states:
        reconciliation_residuals.append("amazon_grid_content_record_absent")
    elif len(states) != 1:
        reconciliation_residuals.append(f"amazon_grid_content_record_count:{len(states)}")
    requested_query = _amazon_requested_query_from_packet(packet)
    observed_queries = state.get("observed_queries", []) if state is not None else []
    subject_confirmed = bool(
        requested_query
        and isinstance(observed_queries, list)
        and observed_queries
        and all(
            isinstance(value, str)
            and _normalize_query(value) == _normalize_query(requested_query)
            for value in observed_queries
        )
    )
    if not subject_confirmed:
        reconciliation_residuals.append("amazon_grid_query_binding_unconfirmed")
    placement_count = sum(max(1, len(row.placements)) for row in rows)
    duplicate_count = placement_count - len(rows)
    requested_page_count = state.get("requested_page_count") if state is not None else None
    captured_page_count = state.get("captured_page_count") if state is not None else None
    termination = state.get("traversal_termination") if state is not None else None
    if not isinstance(requested_page_count, int) or requested_page_count <= 0:
        reconciliation_residuals.append("amazon_grid_requested_page_count_invalid")
    if not isinstance(captured_page_count, int) or captured_page_count <= 0:
        reconciliation_residuals.append("amazon_grid_captured_page_count_invalid")
    if termination == "requested_page_window_reconciled":
        if captured_page_count != requested_page_count:
            reconciliation_residuals.append(
                "amazon_grid_requested_window_page_count_mismatch:"
                f"requested={requested_page_count}:captured={captured_page_count}"
            )
    elif termination == "retailer_terminal_reconciled":
        if (
            isinstance(requested_page_count, int)
            and isinstance(captured_page_count, int)
            and captured_page_count > requested_page_count
        ):
            reconciliation_residuals.append("amazon_grid_terminal_exceeded_requested_window")
    else:
        reconciliation_residuals.append("amazon_grid_termination_unproven")
    ranges = state.get("result_range_observations", []) if state is not None else []
    population_observations = (
        state.get("population_observations", []) if state is not None else []
    )
    if not isinstance(ranges, list) or len(ranges) != captured_page_count:
        reconciliation_residuals.append("amazon_grid_result_range_count_mismatch")
    # A "requested_page_window_reconciled" termination claims a CONSECUTIVE ranked
    # window. Page-number continuity is checked during traversal against the URL, but
    # nothing here checked the retailer-displayed ranges themselves, so a gapped,
    # repeated, or reversed displayed window would still be reported complete.
    if isinstance(ranges, list):
        previous_end: int | None = None
        for index, observation in enumerate(ranges, start=1):
            start = observation.get("start") if isinstance(observation, dict) else None
            end = observation.get("end") if isinstance(observation, dict) else None
            if not isinstance(start, int) or not isinstance(end, int) or start > end:
                reconciliation_residuals.append(
                    f"amazon_grid_result_range_invalid:{index}"
                )
                previous_end = None
                continue
            if previous_end is not None and start != previous_end + 1:
                reconciliation_residuals.append(
                    "amazon_grid_result_range_not_consecutive:"
                    f"{index}:{previous_end}:{start}"
                )
            previous_end = end
    if any("identity_incomplete" in item for item in residuals):
        reconciliation_residuals.append("amazon_grid_incomplete_product_identity_present")
    if state is not None:
        reconciliation_residuals.extend(
            str(value) for value in state.get("residuals", []) if isinstance(value, str)
        )
    complete = not reconciliation_residuals
    displayed_totals = (
        state.get("displayed_result_total_observations", []) if state is not None else []
    )
    declared_total = (
        displayed_totals[-1]
        if isinstance(displayed_totals, list)
        and displayed_totals
        and isinstance(displayed_totals[-1], int)
        else None
    )
    valid_range_spans = (
        [
            observation["end"] - observation["start"] + 1
            for observation in ranges
            if isinstance(observation, dict)
            and isinstance(observation.get("start"), int)
            and isinstance(observation.get("end"), int)
            and observation["start"] <= observation["end"]
        ]
        if isinstance(ranges, list)
        else []
    )
    displayed_range_slot_count = (
        sum(valid_range_spans)
        if isinstance(ranges, list) and len(valid_range_spans) == len(ranges)
        else None
    )
    grid_facts: dict[str, Any | None] = {
        "retailer": "amazon",
        "page_kind": "ranked_search_window",
        "requested_query": requested_query,
        "observed_queries": observed_queries,
        "requested_page_count": requested_page_count,
        "captured_page_count": captured_page_count,
        "result_range_observations": ranges,
        "displayed_result_total_observations": displayed_totals,
        "population_observations": population_observations,
        "delivery_zip": state.get("delivery_zip") if state is not None else None,
        "location_binding": state.get("location_binding") if state is not None else None,
        "extracted_placement_count": placement_count,
        "displayed_result_range_slot_count": displayed_range_slot_count,
        "source_visible_placements_beyond_displayed_range_span": (
            max(0, placement_count - displayed_range_slot_count)
            if displayed_range_slot_count is not None
            else None
        ),
        "displayed_range_slots_without_source_visible_product_card": (
            max(0, displayed_range_slot_count - placement_count)
            if displayed_range_slot_count is not None
            else None
        ),
        "duplicate_placement_count": duplicate_count,
        "subject_binding_confirmed": subject_confirmed,
    }
    completeness_termination = (
        termination
        if complete
        and termination
        in {"requested_page_window_reconciled", "retailer_terminal_reconciled"}
        else "unproven"
    )
    return grid_facts, RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_total,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination=completeness_termination,
        residuals=_dedupe(reconciliation_residuals),
    )


def _base_fields(
    *, packet: SourceCapturePacket, source_slice: SourceCaptureSlice, retailer: RetailGridRetailer
) -> dict[str, Any | None]:
    return {
        "retailer": retailer,
        "page_kind": "grid",
        "capture_time": _fact_value(source_slice.timing.capture_time),
        "locale_pin": _fact_value(source_slice.locale_pin),
        "location_pin": None,
        "series_id": packet.series_id,
        "exact_inventory_quantity": None,
        "exact_inventory_quantity_posture": "not_observed",
        "sold_units": None,
        "sold_units_posture": "not_observed",
    }


def _row_residuals(
    *, retailer: RetailGridRetailer, selected_variant: object, location_observed: bool
) -> list[str]:
    residuals = [
        f"{retailer}_grid_written_review_count_not_observed",
        f"{retailer}_grid_exact_inventory_quantity_not_observed",
        f"{retailer}_grid_sold_units_not_observed",
    ]
    if selected_variant is None:
        residuals.append(f"{retailer}_grid_selected_variant_not_observed")
    if not location_observed:
        residuals.append(f"{retailer}_grid_location_pin_not_observed")
    return residuals


def _walmart_selected_variant(item: dict[str, Any], product_id: str | None) -> str | None:
    variants = item.get("variantList")
    if not isinstance(variants, list) or product_id is None:
        return None
    for variant in variants:
        if isinstance(variant, dict) and _text(variant.get("usItemId")) == product_id:
            return _first_text(variant.get("displayName"), variant.get("name"))
    return None


def _walmart_price(item: dict[str, Any]) -> str | None:
    value = item.get("price")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = _walmart_price_text(item)
    return text.lstrip("$").strip() or None


def _walmart_price_text(item: dict[str, Any]) -> str:
    return _first_text(
        _nested_value(item, "priceInfo", "linePriceDisplay"),
        _nested_value(item, "priceInfo", "linePrice"),
    ) or ""


def _walmart_fulfilment_badge(item: dict[str, Any], key: str) -> str | None:
    badges = item.get("fulfillmentBadgeGroups")
    if not isinstance(badges, list):
        return None
    for badge in badges:
        if isinstance(badge, dict) and badge.get("key") == key:
            parts = [_text(badge.get("text")), _text(badge.get("slaText"))]
            return " ".join(part for part in parts if part).strip() or None
    return None


def _walmart_location_ids(item: dict[str, Any]) -> list[str]:
    summaries = item.get("fulfillmentSummary")
    if not isinstance(summaries, list):
        return []
    return _dedupe(
        _text(summary.get("storeId"))
        for summary in summaries
        if isinstance(summary, dict) and _text(summary.get("storeId"))
    )


def _target_channel_text(card: str, label: str) -> str | None:
    value = _first_regex(
        card,
        (
            rf"<span[^>]*>\s*{re.escape(label)}\s*</span>\s*<span[^>]*>([^<]+)</span>",
        ),
    )
    return html_module.unescape(value) if value else None


def detect_retail_grid_retailer(packet: SourceCapturePacket) -> RetailGridRetailer:
    """Return the retailer named by an admitted source-visible grid locator."""
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        parsed = urlparse(locator)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/").lower()
        if _hostname_matches(hostname, "walmart.com") and path == "/search":
            return "walmart"
        if (
            _hostname_matches(hostname, "target.com")
            and extract_target_grid_subject_from_url(locator) is not None
        ):
            return "target"
        if _hostname_matches(hostname, "sephora.com") and (
            path.startswith("/brand/")
            or extract_sephora_catalog_request(locator) is not None
        ):
            return "sephora"
        if _hostname_matches(hostname, "ulta.com") and (
            path.startswith("/brand/")
            or re.fullmatch(r"/shop/[a-z0-9][a-z0-9-]*/all", path)
        ):
            return "ulta"
        if (
            _hostname_matches(hostname, "amazon.com")
            and path == "/s"
            and extract_amazon_search_query_from_url(locator) is not None
        ):
            return "amazon"
        if (
            _hostname_matches(hostname, "revolve.com")
            and re.fullmatch(
                r"/[a-z0-9][a-z0-9-]*/br/[a-f0-9]{6}",
                path,
                flags=re.IGNORECASE,
            )
        ):
            return "revolve"
    raise RetailGridProjectionInputError(
        "retail grid projection requires an admitted source-visible Walmart search, "
        "Target search/brand, Sephora brand/catalog, Ulta brand/category, Amazon search, "
        "or REVOLVE brand locator"
    )


def _hostname_matches(hostname: str, retailer_domain: str) -> bool:
    return hostname == retailer_domain or hostname.endswith(f".{retailer_domain}")


def load_verified_source_capture_packet_directory(
    packet_directory: Path,
) -> tuple[SourceCapturePacket, dict[str, bytes]]:
    """Load a packet directory and re-hash every manifest-declared raw file."""
    manifest_path = packet_directory / "manifest.json"
    if not manifest_path.is_file():
        raise RetailGridProjectionInputError(f"packet manifest not found: {manifest_path}")
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise RetailGridProjectionInputError(f"manifest is not a JSON object: {manifest_path}")
    packet = SourceCapturePacket.model_validate(raw_manifest)
    bodies: dict[str, bytes] = {}
    packet_root = packet_directory.resolve()
    for preserved_file in packet.preserved_files:
        relative = Path(preserved_file.relative_packet_path)
        if relative.is_absolute():
            raise RetailGridProjectionInputError(
                f"preserved path for {preserved_file.file_id!r} is absolute; block-don't-repair"
            )
        resolved = (packet_root / relative).resolve()
        try:
            resolved.relative_to(packet_root)
        except ValueError as exc:
            raise RetailGridProjectionInputError(
                f"preserved path for {preserved_file.file_id!r} resolves outside the packet dir; block-don't-repair"
            ) from exc
        if not resolved.is_file():
            raise RetailGridProjectionInputError(
                f"preserved file for {preserved_file.file_id!r} not found; block-don't-repair"
            )
        body = resolved.read_bytes()
        if len(body) != preserved_file.size_bytes:
            raise RetailGridProjectionInputError(
                f"preserved file size mismatch for {preserved_file.file_id!r}; block-don't-repair"
            )
        if hashlib.sha256(body).hexdigest() != preserved_file.sha256:
            raise RetailGridProjectionInputError(
                f"preserved file sha256 mismatch for {preserved_file.file_id!r}; block-don't-repair"
            )
        bodies[preserved_file.file_id] = body
    return packet, bodies


def _raw_anchor(preserved_file: PreservedFile) -> RetailProjectionRawAnchor:
    return RetailProjectionRawAnchor(
        file_id=preserved_file.file_id,
        relative_packet_path=preserved_file.relative_packet_path,
        sha256=preserved_file.sha256,
        hash_basis=preserved_file.hash_basis,
        anchor_kind="file",
    )


def _with_anchor(
    raw_anchor: RetailProjectionRawAnchor,
    anchor_kind: Literal["html_selector", "json_pointer", "text_pattern"],
    anchor_value: str,
) -> RetailProjectionRawAnchor:
    return raw_anchor.model_copy(
        update={"anchor_kind": anchor_kind, "anchor_value": anchor_value}
    )


def _nested_value(value: object, *keys: str) -> object | None:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _fact_value(fact: object | None) -> str | None:
    if fact is not None and getattr(fact, "status", None) == VisibleFactStatus.KNOWN:
        return getattr(fact, "value", None)
    return None


def _absolute_url(base: str, value: str | None) -> str | None:
    return urljoin(base, html_module.unescape(value)) if value else None


def _requested_brand_slug(packet: SourceCapturePacket) -> str | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        parts = [part for part in urlparse(locator).path.split("/") if part]
        if len(parts) >= 2 and parts[0].lower() == "brand":
            return parts[1].lower()
    return None


def _requested_sephora_catalog(
    packet: SourceCapturePacket,
) -> tuple[str, int, str] | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator is None:
            continue
        request = extract_sephora_catalog_request(locator)
        if request is not None:
            return request
    return None


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _canonical_url(value: str) -> str:
    parsed = urlparse(value)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _amazon_canonical_product_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.path.rstrip("/").casefold() == "/sspa/click":
        return None
    return _canonical_url(value)


def _price_fields(
    value: str | None,
) -> tuple[str | None, dict[str, str] | None]:
    if value is None:
        return None, None
    range_match = _PRICE_RANGE_RE.fullmatch(value)
    if range_match is not None:
        return None, {
            "minimum": range_match.group("minimum"),
            "maximum": range_match.group("maximum"),
        }
    return value.lstrip("$").strip() or None, None


def _sephora_badges(current_sku: dict[str, Any]) -> list[str]:
    badges = []
    badge = _text(current_sku.get("badge"))
    if badge is not None:
        badges.append(badge)
    for key in (
        "isAppExclusive",
        "isBI",
        "isBest",
        "isBestseller",
        "isFirstAccess",
        "isLimitedEdition",
        "isLimitedTimeOffer",
        "isNatural",
        "isNew",
        "isOnlineOnly",
        "isOrganic",
        "isSephoraExclusive",
    ):
        if current_sku.get(key) is True:
            badges.append(key)
    return badges


def _integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _strict_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _first_regex(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return " ".join(match.group(1).split())
    return None


def _first_present(*values: object) -> object | None:
    return next((value for value in values if value is not None and value != ""), None)


def _first_text(*values: object) -> str | None:
    return next((text for value in values if (text := _text(value))), None)


def _text(value: object) -> str | None:
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        text = str(value).strip()
        return text or None
    return None


def _dedupe(values: Any) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _is_forbidden_field_name(key: str) -> bool:
    return is_forbidden_field_token_match(key, _FORBIDDEN_FIELD_TOKENS)


def _projection_json_text(projection: RetailGridProjectionPacket) -> str:
    return f"{json.dumps(projection.model_dump(mode='json'), indent=2, sort_keys=True)}\n"


__all__ = [
    "RETAIL_GRID_PROJECTION_CERTIFICATION",
    "RETAIL_GRID_PROJECTION_METHOD",
    "RETAIL_GRID_PROJECTION_VERSION",
    "PROJECTION_RETAIL_GRID_LANE",
    "RetailGridCompletenessReconciliation",
    "RetailGridProjectionInputError",
    "RetailGridProjectionLossLedger",
    "RetailGridProjectionPacket",
    "RetailGridProjectionPlacement",
    "RetailGridProjectionRow",
    "build_amazon_grid_aggregate_content_record",
    "build_retail_grid_projection",
    "build_retail_grid_projection_from_packet_directory",
    "detect_retail_grid_retailer",
    "load_verified_source_capture_packet_directory",
    "project_retail_grid_into_lake",
    "write_retail_grid_projection",
]
