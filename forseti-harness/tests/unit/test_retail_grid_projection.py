from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from data_lake.root import DataLakeRoot
from runners import run_retail_grid_projection as grid_projection_runner
from runners.run_capture_ecr_cleaning_smoke import run_capture_ecr_cleaning_smoke
from source_capture.models import (
    CaptureModeCategory,
    PacketTiming,
    PreservedFile,
    ReceiptMetadata,
    SourceCapturePacket,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
    unknown_with_reason,
)
from source_capture.retail_grid_projection import (
    RetailGridProjectionInputError,
    append_retail_grid_observation_into_lake,
    build_amazon_grid_aggregate_content_record,
    build_retail_grid_projection,
    build_retail_grid_observation,
    build_retail_grid_projection_from_packet_directory,
    build_target_grid_aggregate_content_record,
    project_retail_grid_into_lake,
    write_retail_grid_projection,
)
from source_capture.sephora_brand_grid import (
    SEPHORA_GRID_CONTENT_RECORD_VERSION,
    build_sephora_brand_grid_content_record,
)
from source_capture.sephora_catalog_grid import (
    SEPHORA_CATALOG_GRID_CONTENT_RECORD_VERSION,
    SephoraCatalogGridStateError,
    build_sephora_catalog_grid_aggregate_content_record,
)
from source_capture.ulta_brand_grid import (
    ULTA_GRID_CONTENT_RECORD_VERSION,
    build_ulta_brand_grid_content_record,
)
from source_capture.writer import write_local_source_capture_packet


_TARGET_SEARCH_GRID_URL = (
    "https://www.target.com/s?searchTerm=lip%20mask&sortBy=bestselling"
    "&moveTo=product-list-grid"
)
_TARGET_BRAND_GRID_URL = (
    "https://www.target.com/b/e-l-f/-/N-5oajg?sortBy=bestselling"
    "&moveTo=product-list-grid"
)
_AMAZON_GRID_URL = "https://www.amazon.com/s?k=Tower+28+Beauty"


def test_amazon_ranked_window_projects_fields_duplicates_and_count_drift() -> None:
    pages = (
        _amazon_grid_page_html(
            products=[
                ("B000000001", "SOS Daily Rescue Facial Spray", "$16.00", True),
                ("B000000002", "ShineOn Lip Jelly", "$16.00", False),
            ],
            start=1,
            end=2,
            total=214,
        ),
        _amazon_grid_page_html(
            products=[
                ("B000000002", "ShineOn Lip Jelly", "$16.00", True),
            ],
            start=3,
            end=3,
            total=219,
        ),
    )
    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=pages,
        requested_url=_AMAZON_GRID_URL,
        page_urls=(_AMAZON_GRID_URL, f"{_AMAZON_GRID_URL}&page=2"),
        traversal_observation={
            "amazon_grid_requested_page_count": 2,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "requested_page_window_reconciled"
    assert projection.completeness.page_declared_result_count == 219
    assert projection.completeness.extracted_unique_parent_count == 2
    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.duplicate_placement_count == 1
    assert projection.source_visible_grid_facts["requested_page_count"] == 2
    assert projection.source_visible_grid_facts["captured_page_count"] == 2
    assert projection.source_visible_grid_facts[
        "displayed_result_total_observations"
    ] == [214, 219]
    duplicate = next(
        row for row in projection.rows if row.source_visible_fields["source_product_id"] == "B000000002"
    )
    assert [(item.page, item.page_position) for item in duplicate.placements] == [
        (1, 2),
        (2, 1),
    ]
    assert duplicate.source_visible_fields["price_display"] == "$16.00"
    assert duplicate.source_visible_fields["average_rating"] == "4.6"
    assert duplicate.source_visible_fields["rating_count"] == "1234"
    assert duplicate.source_visible_fields["bought_recently_text"] == "1K+ bought in past month"
    assert duplicate.source_visible_fields["location_binding"] == "us_marketplace_only"
    # No single posture describes both placements. Preserve each observed value
    # in placement order and clear the parent-level scalar rather than letting the
    # first placement silently stand in for the second.
    assert duplicate.source_visible_fields["sponsored_posture"] is None
    assert [
        item["sponsored_posture"]
        for item in duplicate.source_visible_fields["placement_source_visible_fields"]
    ] == ["organic", "sponsored"]
    assert (
        "amazon_grid_duplicate_parent_placement_field_differs:B000000002:sponsored_posture"
        in duplicate.residuals
    )
    assert (
        "amazon_grid_duplicate_parent_placement_field_differs:B000000002:sponsored_posture"
        in projection.residuals
    )


def test_amazon_ranked_window_fails_closed_when_displayed_ranges_are_not_consecutive() -> None:
    pages = (
        _amazon_grid_page_html(
            products=[
                ("B000000001", "SOS Daily Rescue Facial Spray", "$16.00", False),
                ("B000000002", "ShineOn Lip Jelly", "$16.00", False),
            ],
            start=1,
            end=2,
            total=214,
        ),
        _amazon_grid_page_html(
            products=[
                ("B000000003", "LipSoftie Lip Treatment", "$18.00", False),
                ("B000000004", "SunnyDays Sunscreen Foundation", "$26.00", False),
            ],
            start=5,
            end=6,
            total=214,
        ),
    )
    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=pages,
        requested_url=_AMAZON_GRID_URL,
        page_urls=(_AMAZON_GRID_URL, f"{_AMAZON_GRID_URL}&page=2"),
        traversal_observation={
            "amazon_grid_requested_page_count": 2,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "incomplete"
    assert projection.completeness.termination == "unproven"
    assert (
        "amazon_grid_result_range_not_consecutive:2:2:5"
        in projection.completeness.residuals
    )


def test_amazon_ranked_window_fails_closed_when_requested_pages_do_not_reconcile() -> None:
    page = _amazon_grid_page_html(
        products=[("B000000001", "SOS Daily Rescue Facial Spray", "$16.00", False)],
        start=1,
        end=1,
        total=214,
    )
    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=(page,),
        requested_url=_AMAZON_GRID_URL,
        page_urls=(_AMAZON_GRID_URL,),
        traversal_observation={
            "amazon_grid_requested_page_count": 3,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "incomplete"
    assert projection.completeness.termination == "unproven"
    assert any(
        value.startswith("amazon_grid_requested_window_page_count_mismatch:")
        for value in projection.completeness.residuals
    )


def test_amazon_ranked_window_preserves_sponsored_redirect_url() -> None:
    page = _amazon_grid_page_html(
        products=[("B000000001", "Sponsored Serum", "$24.00", True)],
        start=1,
        end=1,
        total=1,
    ).replace(
        "/Sponsored-Serum/dp/B000000001/ref=sr_1_1",
        "/sspa/click?spc=abc&amp;url=%2FSponsored-Serum%2Fdp%2FB000000001",
    )

    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=(page,),
        requested_url=_AMAZON_GRID_URL,
        page_urls=(_AMAZON_GRID_URL,),
        traversal_observation={
            "amazon_grid_requested_page_count": 1,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )

    product = record["pages"][0]["products"][0]
    assert product["product_url"] == (
        "https://www.amazon.com/sspa/click?spc=abc&"
        "url=%2FSponsored-Serum%2Fdp%2FB000000001"
    )
    assert record["residuals"] == []
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )
    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )
    assert projection.rows[0].source_visible_fields["product_url"] == product["product_url"]
    assert projection.rows[0].source_visible_fields["canonical_product_url"] is None


def test_amazon_ranked_window_names_placements_beyond_displayed_range_span() -> None:
    page = _amazon_grid_page_html(
        products=[
            ("B000000001", "First Ranked Product", "$16.00", False),
            ("B000000002", "Second Ranked Product", "$18.00", False),
            ("B000000003", "Additional Sponsored Product", "$20.00", True),
        ],
        start=1,
        end=2,
        total=115,
    )
    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=(page,),
        requested_url=_AMAZON_GRID_URL,
        page_urls=(_AMAZON_GRID_URL,),
        traversal_observation={
            "amazon_grid_requested_page_count": 1,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert projection.source_visible_grid_facts["displayed_result_range_slot_count"] == 2
    assert (
        projection.source_visible_grid_facts[
            "source_visible_placements_beyond_displayed_range_span"
        ]
        == 1
    )


def test_amazon_ranked_window_preserves_displayed_range_card_count_difference() -> None:
    page = _amazon_grid_page_html(
        products=[("B000000001", "Only Loaded Product", "$16.00", False)],
        start=49,
        end=96,
        total=115,
    )
    record = build_amazon_grid_aggregate_content_record(
        rendered_pages=(page,),
        requested_url=_AMAZON_GRID_URL,
        page_urls=(f"{_AMAZON_GRID_URL}&page=2",),
        traversal_observation={
            "amazon_grid_requested_page_count": 1,
            "amazon_grid_termination": "requested_page_window_reconciled",
        },
    )

    assert record["residuals"] == []
    assert len(record["pages"][0]["products"]) == 1
    assert record["result_range_observations"] == [
        {"start": 49, "end": 96, "total": 115}
    ]
    body = (json.dumps(record) + "\n").encode("utf-8")
    packet = _packet(
        retailer="amazon",
        locator=_AMAZON_GRID_URL,
        relative_path="raw/01_rendered_content.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert (
        projection.source_visible_grid_facts[
            "displayed_range_slots_without_source_visible_product_card"
        ]
        == 47
    )


def test_walmart_next_data_projection_preserves_one_row_per_product_tile() -> None:
    next_data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "searchResult": {
                        "itemStacks": [
                            {
                                "items": [
                                    _walmart_item(item_type="REGULAR", selected_variant=None),
                                    {"__typename": "SearchPlaceholder"},
                                    _walmart_item(item_type="VARIANT", selected_variant="Single"),
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
    body = _walmart_html(next_data)
    packet = _packet(
        retailer="walmart",
        locator="https://www.walmart.com/search?q=lip%20mask",
        relative_path="raw/01_http_response_body.bin",
        body=body,
        surface="direct_http",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert len(projection.rows) == 2
    assert projection.loss_ledger.structure_preserved is True
    assert [row.raw_anchor.anchor_value for row in projection.rows] == [
        "/props/pageProps/initialData/searchResult/itemStacks/0/items/0",
        "/props/pageProps/initialData/searchResult/itemStacks/0/items/2",
    ]
    first, second = projection.rows
    assert first.source_visible_fields["source_product_id"] == "2150828728"
    assert first.source_visible_fields["product_url"].startswith("https://www.walmart.com/ip/")
    assert first.source_visible_fields["price"] == "2.97"
    assert first.source_visible_fields["average_rating"] == 4.4
    assert first.source_visible_fields["rating_count"] == 180
    assert first.source_visible_fields["written_review_count"] is None
    assert first.source_visible_fields["availability_summary"] == "In stock"
    assert first.source_visible_fields["pickup_availability"] == "Pickup as soon as 12pm"
    assert first.source_visible_fields["delivery_availability"] == "Delivery as soon as 13 mins"
    assert first.source_visible_fields["location_ids"] == ["3081"]
    assert first.source_visible_fields["seller"] == "Walmart.com"
    assert first.source_visible_fields["exact_inventory_quantity_posture"] == "not_observed"
    assert first.source_visible_fields["sold_units_posture"] == "not_observed"
    assert second.source_visible_fields["selected_variant"] == "Single"
    assert "walmart_grid_exact_inventory_quantity_not_observed" in first.residuals
    assert "walmart_grid_sold_units_not_observed" in first.residuals


def test_walmart_grid_skips_incomplete_tile_and_preserves_valid_rows() -> None:
    valid = _walmart_item(item_type="REGULAR", selected_variant=None)
    incomplete = {
        "__typename": "Product",
        "usItemId": "9999999999",
        "name": "Incomplete product tile",
        "canonicalUrl": None,
    }
    next_data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "searchResult": {
                        "itemStacks": [{"items": [valid, incomplete]}]
                    }
                }
            }
        }
    }
    body = _walmart_html(next_data)
    packet = _packet(
        retailer="walmart",
        locator="https://www.walmart.com/search?q=lip%20mask",
        relative_path="raw/01_http_response_body.bin",
        body=body,
        surface="direct_http",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert [
        row.source_visible_fields["source_product_id"] for row in projection.rows
    ] == ["2150828728"]
    assert (
        "walmart_grid_01:walmart:grid_tile_identity_incomplete:0:1"
        in projection.residuals
    )
    assert projection.loss_ledger.structure_preserved is True


def test_target_rendered_projection_preserves_product_cards_and_channel_availability() -> None:
    body = _target_html().encode("utf-8")
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert len(projection.rows) == 2
    row = projection.rows[0]
    assert row.source_visible_fields["source_product_id"] == "94631382"
    assert row.source_visible_fields["product_url"] == (
        "https://www.target.com/p/byoma-liptide-lip-mask-0-2-fl-oz/-/A-94631382#lnk=sametab"
    )
    assert row.source_visible_fields["name"].startswith("BYOMA Liptide Lip Mask")
    assert row.source_visible_fields["price"] == "10.99"
    assert row.source_visible_fields["average_rating"] == "3.8"
    assert row.source_visible_fields["rating_count"] == "145"
    assert row.source_visible_fields["written_review_count"] is None
    assert row.source_visible_fields["availability_summary"] == "In stock"
    assert row.source_visible_fields["pickup_availability"] == "ready by July 10"
    assert row.source_visible_fields["delivery_availability"] == "as soon as 2am"
    assert row.source_visible_fields["shipping_availability"] == "arrives Tue, Jul 14"
    assert row.raw_anchor.anchor_kind == "html_selector"
    assert row.raw_anchor.anchor_value == (
        ':nth-match([data-focusid="94631382_product_card"], 1)'
    )
    assert row.source_visible_fields["exact_inventory_quantity_posture"] == "not_observed"
    assert row.source_visible_fields["sold_units_posture"] == "not_observed"
    assert "target_grid_location_pin_not_observed" in row.residuals


def test_target_duplicate_product_placements_receive_ordinal_anchors() -> None:
    rendered_html = _target_html().replace(
        'data-focusid="91234567_product_card"',
        'data-focusid="94631382_product_card"',
    ).replace("preselect=91234567", "preselect=94631382")
    body = rendered_html.encode("utf-8")
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )
    duplicate = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "94631382"
    )

    assert [placement.raw_anchor.anchor_value for placement in duplicate.placements] == [
        ':nth-match([data-focusid="94631382_product_card"], 1)',
        ':nth-match([data-focusid="94631382_product_card"], 2)',
    ]
    assert any("duplicate_parent_placement" in value for value in duplicate.residuals)


def test_target_content_record_reconciles_pages_duplicates_query_and_fields() -> None:
    rendered_pages = (
        _target_grid_page_html(
            products=[
                ("10000001", "First Target Product", "$10.99"),
                ("10000002", "Second Target Product", "$8.00"),
            ],
            declared=4,
        ),
        _target_grid_page_html(
            products=[
                ("10000002", "Second Target Product", "$8.00"),
                ("10000003", "Third Target Product", "$6.50"),
            ],
            declared=4,
        ).replace(": Target</title>", ": Page 2 : Target</title>"),
    )
    record = build_target_grid_aggregate_content_record(
        rendered_pages=rendered_pages,
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(
            _TARGET_SEARCH_GRID_URL,
            _TARGET_SEARCH_GRID_URL + "&Nao=24",
        ),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )
    body = (json.dumps(record, sort_keys=True) + "\n").encode()
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_rendered_content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert projection.completeness.extracted_unique_parent_count == 3
    assert projection.completeness.extracted_placement_count == 4
    assert projection.completeness.duplicate_placement_count == 1
    assert projection.completeness.subject_binding_confirmed is True
    assert projection.completeness.termination == "retailer_visible_count_reconciled"
    assert projection.source_visible_grid_facts["page_load_count"] == 2
    assert projection.source_visible_grid_facts[
        "declared_result_count_observations"
    ] == [4, 4]
    duplicate = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "10000002"
    )
    assert [(item.page, item.page_position) for item in duplicate.placements] == [
        (1, 2),
        (2, 1),
    ]
    first = projection.rows[0]
    assert first.source_visible_fields["price_display"] == "$10.99"
    assert first.source_visible_fields["price"] == "10.99"
    assert first.source_visible_fields["average_rating"] == "4.6"
    assert first.source_visible_fields["rating_count"] == "145"
    assert first.source_visible_fields["location_pin"] == "10001"
    assert first.source_visible_fields["visible_fulfilment_text"] == [
        "Shipping dates may vary"
    ]


def test_target_brand_grid_binds_subject_bestseller_order_and_merchandising() -> None:
    rendered_pages = (
        _target_grid_page_html(
            products=[
                ("10000001", "First e.l.f. Product", "$10.99"),
                ("10000002", "Second e.l.f. Product", "$8.00"),
            ],
            declared=3,
            title="e.l.f. : Target",
            heading="e.l.f.",
        ).replace(
            "<span>$10.99</span>",
            "<span>Bestseller</span><span>34k+ bought in last month</span>"
            "<span>$10.99</span>",
            1,
        ),
        _target_grid_page_html(
            products=[("10000003", "Third e.l.f. Product", "$6.50")],
            declared=3,
            title="e.l.f. : Page 2 : Target",
            heading="e.l.f.",
        ),
    )
    record = build_target_grid_aggregate_content_record(
        rendered_pages=rendered_pages,
        requested_url=_TARGET_BRAND_GRID_URL,
        page_urls=(_TARGET_BRAND_GRID_URL, _TARGET_BRAND_GRID_URL + "&Nao=24"),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )
    body = (json.dumps(record, sort_keys=True) + "\n").encode()
    packet = _packet(
        retailer="target",
        locator=_TARGET_BRAND_GRID_URL,
        relative_path="raw/01_rendered_content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert projection.source_visible_grid_facts["page_kind"] == "brand_grid"
    assert projection.source_visible_grid_facts["requested_subject"] == "e-l-f"
    assert projection.source_visible_grid_facts["observed_subjects"] == ["e.l.f."]
    assert projection.source_visible_grid_facts["sort_order"] == "bestselling"
    first = projection.rows[0].source_visible_fields
    assert first["retailer_merchandising_labels"] == ["Bestseller"]
    assert first["bought_recently_text"] == "34k+ bought in last month"


def test_target_brand_grid_does_not_admit_missing_bestseller_order() -> None:
    rendered = _target_grid_page_html(
        products=[("10000001", "First e.l.f. Product", "$10.99")],
        declared=1,
        title="e.l.f. : Target",
        heading="e.l.f.",
    )
    unsorted_url = "https://www.target.com/b/e-l-f/-/N-5oajg"
    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=unsorted_url,
        page_urls=(unsorted_url,),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )

    assert "target_grid_bestseller_sort_unconfirmed" in record["residuals"]


def test_target_content_record_fails_closed_on_count_or_identity_gap() -> None:
    rendered = _target_grid_page_html(
        products=[("10000001", "", "$10.99")],
        declared=2,
    )
    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(_TARGET_SEARCH_GRID_URL,),
        traversal_observation={"target_grid_termination": "unproven"},
    )
    body = (json.dumps(record, sort_keys=True) + "\n").encode()
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_rendered_content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "incomplete"
    assert projection.completeness.termination == "unproven"
    assert "target_grid_incomplete_product_identity_present" in (
        projection.completeness.residuals
    )
    assert any(
        "declared_placement_count_mismatch" in value
        for value in projection.completeness.residuals
    )


def test_target_grid_declared_count_drift_is_complete_with_advisory_residual() -> None:
    rendered_pages = (
        _target_grid_page_html(
            products=[
                ("10000001", "First Target Product", "$10.99"),
                ("10000002", "Second Target Product", "$8.00"),
            ],
            declared=4,
        ),
        _target_grid_page_html(
            products=[("10000003", "Third Target Product", "$6.50")],
            declared=3,
        ),
    )
    record = build_target_grid_aggregate_content_record(
        rendered_pages=rendered_pages,
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(
            _TARGET_SEARCH_GRID_URL,
            _TARGET_SEARCH_GRID_URL + "&Nao=24",
        ),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )
    body = (json.dumps(record, sort_keys=True) + "\n").encode()
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_rendered_content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.page_declared_result_count == 3
    assert projection.source_visible_grid_facts[
        "declared_result_count_observations"
    ] == [4, 3]
    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "retailer_visible_count_reconciled"
    assert (
        "target_grid_declared_count_changed_during_traversal:minimum=3:maximum=4"
        in projection.completeness.residuals
    )


def test_target_grid_reads_rendered_text_not_serialized_page_state() -> None:
    rendered = (
        _target_grid_page_html(
            products=[("10000001", "Only Target Product", "$10.99")],
            declared=1,
        )
        .replace(
            "<body>",
            '<body><script>window.__TGT__={"copy":"99 results"};</script>',
            1,
        )
        .replace(
            "</body>",
            '<script>window.__RAIL__={"label":"Bestseller","tag":"Sponsored"};'
            "</script></body>",
            1,
        )
    )

    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(_TARGET_SEARCH_GRID_URL,),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )

    page = record["pages"][0]
    assert page["declared_result_count"] == 1
    assert page["products"][0]["retailer_merchandising_labels"] == []
    assert page["products"][0]["sponsored_posture"] is None


def test_target_grid_final_card_excludes_trailing_page_content() -> None:
    rendered = _target_grid_page_html(
        products=[("10000001", "Only Target Product", "$10.99")],
        declared=1,
    ).replace(
        "</body>",
        "<footer>Bestseller Highly rated Sponsored Free 2-Day Shipping</footer>"
        "</body>",
        1,
    )

    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(_TARGET_SEARCH_GRID_URL,),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )

    product = record["pages"][0]["products"][0]
    assert product["retailer_merchandising_labels"] == []
    assert product["sponsored_posture"] is None
    assert product["visible_fulfilment_text"] == ["Shipping dates may vary"]


def test_target_content_record_binds_name_to_current_content_anchor() -> None:
    rendered = _target_grid_page_html(
        products=[("10000001", "Actual Product Name", "$10.99")],
        declared=1,
    ).replace(
        '<div data-focusid="10000001_product_card">',
        '<div data-focusid="10000001_product_card"><h3>Related to your search</h3>',
    )

    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(_TARGET_SEARCH_GRID_URL,),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )

    assert record["pages"][0]["products"][0]["name"] == "Actual Product Name"


def test_target_content_record_takes_precedence_over_fallback_rendered_dom() -> None:
    rendered = _target_grid_page_html(
        products=[("10000001", "Actual Product Name", "$10.99")],
        declared=1,
    )
    record = build_target_grid_aggregate_content_record(
        rendered_pages=(rendered,),
        requested_url=_TARGET_SEARCH_GRID_URL,
        page_urls=(_TARGET_SEARCH_GRID_URL,),
        traversal_observation={
            "target_grid_termination": "retailer_declared_count_reconciled"
        },
    )
    content_body = (json.dumps(record, sort_keys=True) + "\n").encode()
    rendered_body = rendered.encode()
    packet = _packet(
        retailer="target",
        locator=_TARGET_SEARCH_GRID_URL,
        relative_path="raw/01_content_record.json",
        body=content_body,
        surface="cloakbrowser_snapshot",
    )
    fallback_file = PreservedFile(
        file_id="file_02",
        original_path="rendered_dom.html",
        relative_packet_path="raw/02_rendered_dom.html",
        sha256=hashlib.sha256(rendered_body).hexdigest(),
        hash_basis="raw_stored_bytes",
        size_bytes=len(rendered_body),
    )
    packet = packet.model_copy(
        update={
            "preserved_files": [*packet.preserved_files, fallback_file],
            "source_slices": [
                packet.source_slices[0].model_copy(
                    update={"preserved_file_ids": ["file_01", "file_02"]}
                )
            ],
        }
    )

    projection = build_retail_grid_projection(
        packet=packet,
        raw_file_bytes_by_file_id={
            "file_01": content_body,
            "file_02": rendered_body,
        },
    )

    assert projection.completeness.status == "complete"
    assert len(projection.rows) == 1
    assert not any(
        value.startswith("target_grid_content_record_count:")
        for value in projection.completeness.residuals
    )


def test_sephora_linkstore_projection_deduplicates_parent_products_and_reconciles_count() -> None:
    products = [
        _sephora_product(product_id="P455936", name="Lip Butter Balm"),
        _sephora_product(product_id="P455936", name="Lip Butter Balm"),
        _sephora_product(
            product_id="P429952",
            name="Jet Lag Mask",
            list_price="$26.00 - $49.00",
        ),
    ]
    body = _sephora_grid_html(
        products=products,
        total_products=2,
        currency_code="USD",
    )
    packet = _packet(
        retailer="sephora",
        locator="https://www.sephora.com/brand/summer-fridays?country_switch=us",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert [row.source_visible_fields["source_product_id"] for row in projection.rows] == [
        "P455936",
        "P429952",
    ]
    first = projection.rows[0]
    assert first.source_visible_fields["canonical_product_url"] == (
        "https://www.sephora.com/product/lip-butter-balm-P455936"
    )
    assert first.source_visible_fields["price"] == "24.00"
    assert first.source_visible_fields["price_currency"] == "USD"
    assert first.source_visible_fields["average_rating"] == 4.29
    assert first.source_visible_fields["review_count"] == 17635
    assert first.source_visible_fields["visible_variant_count"] == 11
    assert first.source_visible_fields["badges"] == ["isBestseller", "isNew"]
    assert [placement.grid_position for placement in first.placements] == [1, 2]
    assert [placement.raw_anchor.anchor_value for placement in first.placements] == [
        "/page/nthBrand/products/0",
        "/page/nthBrand/products/1",
    ]
    assert projection.completeness.status == "complete"
    assert projection.completeness.page_declared_result_count == 2
    assert projection.completeness.extracted_unique_parent_count == 2
    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.duplicate_placement_count == 1
    assert projection.completeness.termination == (
        "retailer_serialized_count_reconciled"
    )
    assert projection.source_visible_grid_facts["subject_binding_confirmed"] is True
    ranged = projection.rows[1]
    assert ranged.source_visible_fields["price"] is None
    assert ranged.source_visible_fields["price_display"] == "$26.00 - $49.00"
    assert ranged.source_visible_fields["price_range"] == {
        "minimum": "26.00",
        "maximum": "49.00",
    }


def test_sephora_grid_compact_content_record_preserves_projection_and_anchor() -> None:
    rendered = _sephora_grid_html(
        products=[_sephora_product(product_id="P455936", name="Lip Butter Balm")],
        total_products=1,
        currency_code="USD",
    )
    record = build_sephora_brand_grid_content_record(
        rendered_dom=rendered.decode(),
        final_url="https://www.sephora.com/brand/summer-fridays?country_switch=us",
    )
    body = json.dumps(record, separators=(",", ":")).encode()
    packet = _packet(
        retailer="sephora",
        locator="https://www.sephora.com/brand/summer-fridays?country_switch=us",
        relative_path="raw/content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert record["content_record_version"] == SEPHORA_GRID_CONTENT_RECORD_VERSION
    assert projection.completeness.status == "complete"
    assert projection.rows[0].raw_anchor.anchor_kind == "json_pointer"
    assert projection.rows[0].raw_anchor.anchor_value == "/page/nthBrand/products/0"
    assert b"<html" not in body


def test_sephora_projection_preserves_partial_tile_and_fails_count_reconciliation() -> None:
    incomplete = _sephora_product(product_id="P000002", name="Missing URL")
    incomplete["targetUrl"] = None
    body = _sephora_grid_html(
        products=[
            _sephora_product(product_id="P000001", name="Complete Product"),
            incomplete,
        ],
        total_products=2,
        currency_code="USD",
    )
    packet = _packet(
        retailer="sephora",
        locator="https://www.sephora.com/brand/summer-fridays?country_switch=us",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert len(projection.rows) == 1
    assert projection.completeness.status == "incomplete"
    assert projection.completeness.termination == "unproven"
    assert any(
        "declared_unique_parent_count_mismatch" in residual
        for residual in projection.completeness.residuals
    )
    assert "sephora_grid_incomplete_product_identity_present" in (
        projection.completeness.residuals
    )
    assert any("grid_tile_identity_incomplete:1" in item for item in projection.residuals)


@pytest.mark.parametrize(
    ("requested_page", "window_size"),
    [(2, 120), (5, 300), (12, 720)],
)
def test_sephora_catalog_projection_reconciles_bounded_bestseller_window(
    requested_page: int, window_size: int
) -> None:
    locator = (
        "https://www.sephora.com/shop/makeup-cosmetics?country_switch=us"
        "&lang=en&currentPage=1&sortBy=BEST_SELLING"
    )
    page_urls = [
        (
            "https://www.sephora.com/shop/makeup-cosmetics?country_switch=us"
            f"&lang=en&currentPage={page}&sortBy=BEST_SELLING"
        )
        for page in range(1, requested_page + 1)
    ]
    rendered_pages = [
        _sephora_catalog_grid_html(
            requested_page=page,
            total_products=2391,
        ).decode()
        for page in range(1, requested_page + 1)
    ]
    traversal = {
        "requestedPageCount": requested_page,
        "capturedPageCount": requested_page,
        "extractedUniqueParentCount": window_size,
        "duplicatePlacementCount": 0,
        "termination": "requested_page_window_reconciled",
    }
    record = build_sephora_catalog_grid_aggregate_content_record(
        rendered_pages=rendered_pages,
        requested_url=locator,
        page_urls=page_urls,
        traversal_observation=traversal,
    )
    body = json.dumps(record, separators=(",", ":")).encode()
    packet = _packet(
        retailer="sephora",
        locator=locator,
        relative_path="raw/content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert (
        record["content_record_version"]
        == SEPHORA_CATALOG_GRID_CONTENT_RECORD_VERSION
    )
    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "requested_page_window_reconciled"
    assert projection.completeness.page_declared_result_count == 2391
    assert projection.completeness.extracted_unique_parent_count == window_size
    assert projection.completeness.extracted_placement_count == window_size
    assert projection.completeness.duplicate_placement_count == 0
    assert projection.source_visible_grid_facts["page_kind"] == "catalog_grid"
    assert (
        projection.source_visible_grid_facts["requested_page_count"]
        == requested_page
    )
    assert projection.source_visible_grid_facts["window_end"] == window_size
    assert projection.source_visible_grid_facts["has_more"] is True
    assert projection.source_visible_grid_facts["subject_binding_confirmed"] is True
    assert projection.rows[0].source_visible_fields["source_product_id"] == "P000001"
    assert projection.rows[-1].source_visible_fields["source_product_id"] == (
        f"P{window_size:06d}"
    )
    assert projection.rows[-1].placements[0].grid_position == window_size
    assert projection.rows[-1].placements[0].page == requested_page
    assert projection.rows[-1].placements[0].page_position == 60
    assert projection.rows[0].raw_anchor.anchor_value == (
        "/page/catalogAggregate/pages/0/products/0"
    )
    assert b"<html" not in body


def test_sephora_catalog_projection_fails_closed_on_short_or_duplicate_window() -> None:
    locator = (
        "https://www.sephora.com/shop/makeup-cosmetics?country_switch=us"
        "&lang=en&currentPage=1&sortBy=BEST_SELLING"
    )
    page_urls = [
        locator,
        locator.replace("currentPage=1", "currentPage=2"),
    ]
    rendered_pages = [
        _sephora_catalog_grid_html(
            requested_page=1, total_products=2391
        ).decode(),
        _sephora_catalog_grid_html(
            requested_page=2,
            total_products=2391,
            duplicate_first_product=60,
        ).decode(),
    ]

    with pytest.raises(
        SephoraCatalogGridStateError, match="duplicate product identities"
    ):
        build_sephora_catalog_grid_aggregate_content_record(
            rendered_pages=rendered_pages,
            requested_url=locator,
            page_urls=page_urls,
            traversal_observation={},
        )


def test_grid_projection_runner_writes_hash_verified_sidecar(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    output = tmp_path / "projection" / "retail_grid_projection.json"

    assert grid_projection_runner.main(
        ["--packet-dir", str(packet_dir), "--output", str(output)]
    ) == 0

    assert capsys.readouterr().out.strip() == str(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["projection_method"] == "retail_grid_mechanical_projection"
    assert payload["loss_ledger"]["structure_preserved"] is True
    assert payload["rows"][0]["raw_anchor"]["sha256"] == hashlib.sha256(
        (packet_dir / "raw/01_http_response_body.bin").read_bytes()
    ).hexdigest()


def test_retail_grid_lake_projection_loads_verified_raw_and_appends_derived(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    capture_path = tmp_path / "target_grid.html"
    capture_path.write_text(_target_html(), encoding="utf-8")
    written = write_local_source_capture_packet(
        data_root=root,
        input_files=[capture_path],
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        source_locator=known_fact(
            _TARGET_SEARCH_GRID_URL
        ),
        decision_question="What products are visible in the Target grid?",
        capture_context="offline unit fixture",
    )

    projection, derived_path = project_retail_grid_into_lake(
        data_root=root,
        packet_id=written.packet.packet_id,
        record_id="retail_grid_fixture",
    )

    loaded = root.load_raw_packet(written.packet.packet_id)
    assert loaded.manifest["packet_id"] == written.packet.packet_id
    assert projection.packet_id == written.packet.packet_id
    assert projection.rows
    assert derived_path.relative_to(root.path).parts == (
        "derived",
        hashlib.sha256(written.packet.packet_id.encode("utf-8")).hexdigest()[:3],
        written.packet.packet_id,
        "projection_retail_grid",
        "retail_grid_fixture.json",
    )
    assert json.loads(derived_path.read_text(encoding="utf-8"))["packet_id"] == (
        written.packet.packet_id
    )


def test_v1_retail_grid_observation_uses_capture_event_without_claiming_raw(
    tmp_path: Path,
) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    packet = SourceCapturePacket.model_validate(
        json.loads((packet_dir / "manifest.json").read_text(encoding="utf-8"))
    )
    bodies = {
        item.file_id: (packet_dir / item.relative_packet_path).read_bytes()
        for item in packet.preserved_files
    }

    observation = build_retail_grid_observation(
        packet=packet,
        raw_file_bytes_by_file_id=bodies,
        captured_at="2026-07-22T00:00:00Z",
        requested_url="https://www.walmart.com/search?q=clinique",
        final_url="https://www.walmart.com/search?q=clinique",
        capture_profile="walmart_grid_fixture",
        parser_version="fixture_v1",
        series_id="walmart-clinique-us",
        retain_raw_sample=False,
    )

    assert observation.projection_version == "v1"
    assert observation.packet_id is None
    assert observation.capture_event is not None
    assert observation.capture_event.capture_event_id == packet.packet_id
    assert observation.capture_event.raw_sample_packet_id is None
    assert all(row.raw_ref is None and row.raw_anchor is None for row in observation.rows)
    assert all(
        placement.raw_anchor is None
        for row in observation.rows
        for placement in row.placements
    )

    root = DataLakeRoot.for_test(tmp_path / "derived_only_lake")
    path = append_retail_grid_observation_into_lake(
        data_root=root, observation=observation, record_id="observation_fixture"
    )
    assert path.is_file()
    assert root.list_committed_packet_ids() == []
    assert packet.packet_id in path.parts


def test_v1_sample_backed_observation_keeps_exact_raw_references(tmp_path: Path) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    packet = SourceCapturePacket.model_validate(
        json.loads((packet_dir / "manifest.json").read_text(encoding="utf-8"))
    )
    bodies = {
        item.file_id: (packet_dir / item.relative_packet_path).read_bytes()
        for item in packet.preserved_files
    }

    observation = build_retail_grid_observation(
        packet=packet,
        raw_file_bytes_by_file_id=bodies,
        captured_at="2026-07-22T00:00:00Z",
        requested_url="https://www.walmart.com/search?q=clinique",
        final_url="https://www.walmart.com/search?q=clinique",
        capture_profile="walmart_grid_fixture",
        parser_version="fixture_v1",
        series_id=None,
        retain_raw_sample=True,
    )

    assert observation.capture_event is not None
    assert observation.capture_event.raw_sample_packet_id == packet.packet_id
    assert all(row.raw_ref is not None for row in observation.rows)
    assert all(row.raw_ref.packet_id == packet.packet_id for row in observation.rows if row.raw_ref)


def test_grid_projection_packet_directory_blocks_hash_mismatch(tmp_path: Path) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    raw_path = packet_dir / "raw/01_http_response_body.bin"
    raw_path.write_bytes(raw_path.read_bytes() + b"tampered")

    with pytest.raises(RetailGridProjectionInputError, match="size mismatch"):
        build_retail_grid_projection_from_packet_directory(packet_directory=packet_dir)


def test_grid_projection_packet_directory_blocks_missing_raw_file(tmp_path: Path) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    (packet_dir / "raw/01_http_response_body.bin").unlink()

    with pytest.raises(RetailGridProjectionInputError, match="not found"):
        build_retail_grid_projection_from_packet_directory(packet_directory=packet_dir)


def test_smoke_accepts_grid_projection_and_preserves_anchors_residuals_and_lineage(
    tmp_path: Path,
) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    projection_path = tmp_path / "projection" / "retail_grid_projection.json"
    projection = write_retail_grid_projection(
        packet_directory=packet_dir, output_path=projection_path
    )
    manifest_path = _write_smoke_manifest(
        tmp_path, packet_dir=packet_dir, projection_path=projection_path
    )

    outputs = run_capture_ecr_cleaning_smoke(
        smoke_manifest_path=manifest_path,
        output_dir=tmp_path / "smoke_outputs",
        include_cleaning_transform_smoke=True,
    )

    receipts = _load_json(Path(outputs["ecr_source_side_receipts"]))
    cleaning = _load_json(Path(outputs["cleaning_packet"]))
    summary = _load_json(Path(outputs["smoke_summary"]))
    assert len(receipts["receipts"]) == 1
    assert len(cleaning["handles"]) == len(projection.rows) == 1
    assert len(cleaning["transform_ledger"]) == 1
    handle = cleaning["handles"][0]
    assert handle["source_row_kind"] == "retail_grid_product"
    assert handle["source_anchor"]["anchor_kind"] == "json_pointer"
    assert handle["source_anchor"]["json_pointer"].endswith("/itemStacks/0/items/0")
    assert "walmart_grid_written_review_count_not_observed" in handle["residuals"]
    assert "walmart_grid_exact_inventory_quantity_not_observed" in handle["residuals"]
    assert summary["sources"][0]["page_kind"] == "grid"
    assert summary["sources"][0]["capture_validity_supported"] is True
    assert not any(
        finding["code"] == "retail_row_anchor_unverified"
        for finding in summary["findings"]
    )


def test_smoke_fails_visibly_when_required_grid_identity_is_missing(tmp_path: Path) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    projection_path = tmp_path / "projection" / "retail_grid_projection.json"
    write_retail_grid_projection(packet_directory=packet_dir, output_path=projection_path)
    payload = _load_json(projection_path)
    payload["rows"][0]["source_visible_fields"]["name"] = None
    projection_path.write_text(json.dumps(payload), encoding="utf-8")
    manifest_path = _write_smoke_manifest(
        tmp_path, packet_dir=packet_dir, projection_path=projection_path
    )

    with pytest.raises(ValidationError, match="source identity fields: name"):
        run_capture_ecr_cleaning_smoke(
            smoke_manifest_path=manifest_path, output_dir=tmp_path / "smoke_outputs"
        )


def test_smoke_reports_unverified_grid_json_pointer(tmp_path: Path) -> None:
    packet_dir = _write_walmart_packet(tmp_path)
    projection_path = tmp_path / "projection" / "retail_grid_projection.json"
    write_retail_grid_projection(packet_directory=packet_dir, output_path=projection_path)
    payload = _load_json(projection_path)
    payload["rows"][0]["raw_anchor"]["anchor_value"] = (
        "/props/pageProps/initialData/searchResult/itemStacks/0/items/99"
    )
    projection_path.write_text(json.dumps(payload), encoding="utf-8")
    manifest_path = _write_smoke_manifest(
        tmp_path, packet_dir=packet_dir, projection_path=projection_path
    )

    outputs = run_capture_ecr_cleaning_smoke(
        smoke_manifest_path=manifest_path, output_dir=tmp_path / "smoke_outputs"
    )
    summary = _load_json(Path(outputs["smoke_summary"]))
    assert any(
        finding["code"] == "retail_row_anchor_unverified"
        and finding["reason"] == "json_pointer_absent_from_raw"
        for finding in summary["findings"]
    )


def _walmart_item(*, item_type: str, selected_variant: str | None) -> dict[str, object]:
    item: dict[str, object] = {
        "__typename": "Product",
        "usItemId": "2150828728",
        "name": "Vitamasques Cherry Vegan Collagen Lip Mask, Moisturize & Plump, One Patch",
        "type": item_type,
        "canonicalUrl": "/ip/Vitamasques-Lip-Mask/2150828728?classType=REGULAR",
        "price": 2.97,
        "priceInfo": {"linePriceDisplay": "$2.97"},
        "averageRating": 4.4,
        "numberOfReviews": 180,
        "availabilityStatusV2": {"display": "In stock", "value": "IN_STOCK"},
        "sellerName": "Walmart.com",
        "fulfillmentBadgeGroups": [
            {"key": "FF_DELIVERY", "text": "Delivery as soon as ", "slaText": "13 mins"},
            {"key": "FF_PICKUP", "text": "Pickup as soon as ", "slaText": "12pm"},
        ],
        "fulfillmentSummary": [{"fulfillment": "PICKUP", "storeId": "3081"}],
        "variantList": [],
    }
    if selected_variant:
        item["variantList"] = [
            {"usItemId": "2150828728", "displayName": selected_variant, "name": "1"}
        ]
    return item


def _walmart_html(next_data: dict[str, object]) -> bytes:
    return (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(next_data, separators=(",", ":"))
        + "</script></body></html>"
    ).encode("utf-8")


def _target_html() -> str:
    return """
    <html><body><div data-test="product-grid">
      <div data-focusid="94631382_product_card" data-test="@web/site-top-of-funnel/ProductCardWrapper">
        <a href="/p/byoma-liptide-lip-mask-0-2-fl-oz/-/A-94631382#lnk=sametab">image</a>
        <span data-test="current-price"><span>$10.99</span></span>
        <a aria-label="BYOMA Liptide Lip Mask - 0.2 fl oz: Moisturizing &amp; Vegan"
           data-test="@web/ProductCard/title">BYOMA Liptide Lip Mask</a>
        <div aria-label="3.8 stars with 145 ratings"></div>
        <div data-test="lowStockMessaging"><span>In stock</span></div>
        <span>Pickup </span><span>ready by July 10</span>
        <span>Delivery </span><span>as soon as 2am</span>
        <span>Shipping </span><span>arrives Tue, Jul 14</span>
      </div>
      <div data-focusid="91234567_product_card" data-test="@web/site-top-of-funnel/ProductCardWrapper">
        <a href="/p/second-mask/-/A-90000000?preselect=91234567#lnk=sametab">image</a>
        <span data-test="current-price"><span>$8.00</span></span>
        <a aria-label="Second Lip Mask" data-test="@web/ProductCard/title">Second Lip Mask</a>
        <div aria-label="4.2 stars with 12 ratings"></div>
      </div>
    </div></body></html>
    """


def _amazon_grid_page_html(
    *,
    products: list[tuple[str, str, str, bool]],
    start: int,
    end: int,
    total: int,
) -> str:
    cards = []
    for position, (asin, name, price, sponsored) in enumerate(products, start=1):
        cards.append(
            f"""
            <div data-index="{position}" data-asin="{asin}"
                 data-component-type="s-search-result">
              {'<span>Sponsored</span>' if sponsored else ''}
              <a href="/{name.replace(' ', '-')}/dp/{asin}/ref=sr_1_{position}">
                <h2 aria-label="{name}"><span>{name}</span></h2>
              </a>
              <span aria-label="4.6 out of 5 stars, rating details"></span>
              <a aria-label="1,234 ratings"><span>(1,234)</span></a>
              <span class="a-price"><span class="a-offscreen">{price}</span></span>
              <span>1K+ bought in past month</span>
              <div data-cy="delivery-block">FREE delivery Tomorrow</div>
            </div>
            """
        )
    return f"""
    <html><script>ue_sn = 'www.amazon.com'</script><body>
      <span>{start}-{end} of {total} results for</span>
      <span class="a-color-state">"Tower 28 Beauty"</span>
      {''.join(cards)}
    </body></html>
    """


def _target_grid_page_html(
    *,
    products: list[tuple[str, str, str]],
    declared: int,
    title: str = '"lip mask" : Target',
    heading: str | None = None,
) -> str:
    cards = []
    for product_id, name, price in products:
        product_heading = f"<h3><span>{name}</span></h3>" if name else ""
        cards.append(
            f"""
            <div data-focusid="{product_id}_product_card">
              <a data-test="content" href="/p/product-{product_id}/-/A-{product_id}">
                <span>{price}</span>
                {product_heading}
                <div data-test="rating-stars"
                     aria-label="Average customer rating is 4.6 out of 5 stars with 145 reviews.">
                </div>
                <span>Shipping dates may vary</span>
              </a>
            </div>
            """
        )
    return f"""
    <html><head><title>{title}</title></head><body>
      {f'<h1>{heading}</h1>' if heading is not None else ''}
      <button id="zip-code-id-btn" aria-label="Ship to location: 10001">
        <span data-test="@web/ZipCodeButton/ZipCodeNumber">Ship to 10001</span>
      </button>
      <div>{declared} results</div>
      {''.join(cards)}
    </body></html>
    """


def _sephora_product(
    *, product_id: str, name: str, list_price: str = "$24.00"
) -> dict[str, object]:
    return {
        "brandName": "Summer Fridays",
        "currentSku": {
            "isBestseller": True,
            "isNew": True,
            "listPrice": list_price,
            "skuId": f"SKU-{product_id}",
        },
        "displayName": name,
        "moreColors": 11,
        "pickupEligible": False,
        "productId": product_id,
        "rating": 4.29,
        "reviews": 17635,
        "sameDayEligible": False,
        "targetUrl": f"/product/{name.lower().replace(' ', '-')}-{product_id}?skuId=1",
    }


def _sephora_grid_html(
    *,
    products: list[dict[str, object]],
    total_products: int,
    currency_code: str | None,
) -> bytes:
    nth_brand: dict[str, object] = {
        "brandId": "6247",
        "displayName": "Summer Fridays",
        "shortName": "Summer Fridays",
        "resultId": "test-result",
        "targetUrl": "/brand/summer-fridays",
        "seoCanonicalUrl": "/brand/summer-fridays",
        "pageSize": 60,
        "totalProducts": total_products,
        "products": products,
    }
    if currency_code is not None:
        nth_brand["currencyCode"] = currency_code
    payload = {"page": {"nthBrand": nth_brand}}
    return (
        '<html><body><script id="linkStore" type="text/json">'
        + json.dumps(payload, separators=(",", ":"))
        + "</script></body></html>"
    ).encode("utf-8")


def _sephora_catalog_grid_html(
    *,
    requested_page: int,
    total_products: int,
    duplicate_first_product: int | None = None,
) -> bytes:
    products: list[dict[str, object]] = []
    page_start = ((requested_page - 1) * 60) + 1
    for page_position in range(1, 61):
        product_number = page_start + page_position - 1
        if page_position == 1 and duplicate_first_product is not None:
            product_number = duplicate_first_product
        product_id = f"P{product_number:06d}"
        products.append(
            {
                "productId": product_id,
                "displayName": f"Product {product_number}",
                "targetUrl": (
                    f"/product/product-{product_number}-{product_id}"
                    f"?skuId={product_number}"
                ),
                "brandName": f"Brand {product_number}",
                "currentSku": {
                    "skuId": str(product_number),
                    "listPrice": f"${20 + product_number}.00",
                },
                "rating": "4.5",
                "reviews": str(product_number),
            }
        )
    render_query = json.dumps(
        {
            "country": "US",
            "urlPath": "/shop/makeup-cosmetics",
            "cachedQueryParams": (
                f"currentPage={requested_page}&sortBy=BEST_SELLING"
            ),
        },
        separators=(",", ":"),
    )
    link_store = json.dumps(
        {
            "page": {
                "nthCategory": {
                    "categoryId": "cat140006",
                    "displayName": "Makeup",
                    "currentPage": requested_page,
                    "pageSize": 60,
                    "totalProducts": total_products,
                    "resultId": f"result-{requested_page}",
                    "targetUrl": "/shop/makeup-cosmetics",
                    "sortOptionCode": "BEST_SELLING",
                    "products": products,
                }
            }
        },
        separators=(",", ":"),
    )
    return f"""
    <html><body>
      <script>Sephora.renderQueryParams = {render_query};</script>
      <script id="linkStore" type="text/json">{link_store}</script>
      <h1>Makeup</h1>
      <span>Sort by: <strong>Bestselling</strong></span>
      <div data-cnstrc-browse="true"
           data-cnstrc-num-results="{total_products}"
           data-cnstrc-result-id="result-1"
           data-cnstrc-filter-name="group_id"
           data-cnstrc-filter-value="cat140006">
        <a data-cnstrc-item-id="{products[0]['productId']}">Quicklook $25.00</a>
        <p>1-60 of {total_products} Results</p>
        <button>Show More Products</button>
      </div>
    </body></html>
    """.encode()


def _packet(
    *, retailer: str, locator: str, relative_path: str, body: bytes, surface: str
) -> SourceCapturePacket:
    timing = PacketTiming(
        source_publication_or_event=unknown_with_reason("grid has no source event time"),
        source_edit_or_version=unknown_with_reason("grid has no source edit time"),
        capture_time=known_fact("2026-07-11T00:00:00Z"),
        recapture_time=not_applicable("first capture"),
        cutoff_posture=unknown_with_reason("test fixture has no cutoff"),
    )
    preserved_file = PreservedFile(
        file_id="file_01",
        original_path=Path(relative_path).name,
        relative_packet_path=relative_path,
        sha256=hashlib.sha256(body).hexdigest(),
        hash_basis="raw_stored_bytes",
        size_bytes=len(body),
    )
    return SourceCapturePacket(
        packet_id=f"01TESTGRID{retailer.upper()}",
        manifest_version="source_capture_packet_manifest_v1",
        obligation_contract_version="core_spine_v0_data_capture_spine_obligation_contract_v0",
        source_family="retail_grid",
        source_surface=surface,
        source_locator=known_fact(locator),
        requested_decision_context=known_fact(f"{retailer} grid projection fixture"),
        capture_context=known_fact("unit test packet"),
        actor_audience_context=unknown_with_reason("not supplied"),
        capture_mode=(
            CaptureModeCategory.STRUCTURED_ACCESS
            if retailer == "walmart"
            else CaptureModeCategory.MULTIMODAL
        ),
        operator_category="unit_test",
        session_identity="01TESTGRIDSESSION",
        timing=timing,
        access_posture=known_fact("fixture supplied"),
        archive_history_posture=not_attempted("archive not queried"),
        media_modality_posture=not_attempted("screenshot not supplied"),
        re_capture_relationship=not_applicable("first capture"),
        series_id=f"{retailer}_lip_mask_grid_us_v0",
        source_slices=[
            SourceCaptureSlice(
                slice_id=f"{retailer}_grid_01",
                locator=known_fact(locator),
                timing=timing,
                access_posture=known_fact("fixture supplied"),
                archive_history_posture=not_attempted("archive not queried"),
                media_modality_posture=not_attempted("screenshot not supplied"),
                re_capture_relationship=not_applicable("first capture"),
                locale_pin=known_fact("en-US"),
                currency_pin=known_fact("USD"),
                preserved_file_ids=["file_01"],
            )
        ],
        preserved_files=[preserved_file],
        receipt_metadata=ReceiptMetadata(
            title="Retail grid fixture",
            generated_at="2026-07-11T00:00:00Z",
            summary="unit test packet",
            non_claims=["not Cleaning", "not Judgment"],
        ),
    )


def _write_walmart_packet(tmp_path: Path) -> Path:
    next_data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "searchResult": {
                        "itemStacks": [{"items": [_walmart_item(item_type="REGULAR", selected_variant=None)]}]
                    }
                }
            }
        }
    }
    body = _walmart_html(next_data)
    packet = _packet(
        retailer="walmart",
        locator="https://www.walmart.com/search?q=lip%20mask",
        relative_path="raw/01_http_response_body.bin",
        body=body,
        surface="direct_http",
    )
    packet_dir = tmp_path / "walmart_packet"
    raw_path = packet_dir / packet.preserved_files[0].relative_packet_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(body)
    (packet_dir / "manifest.json").write_text(
        f"{json.dumps(packet.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return packet_dir


def _write_smoke_manifest(
    tmp_path: Path, *, packet_dir: Path, projection_path: Path
) -> Path:
    path = tmp_path / "smoke_manifest.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "retail_grid_fixture_smoke",
                "retail": [
                    {
                        "retailer": "walmart",
                        "packet_dir": str(packet_dir),
                        "projection_json": str(projection_path),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _with_second_preserved_file(
    packet: SourceCapturePacket, *, relative_path: str, body: bytes
) -> SourceCapturePacket:
    manifest = packet.model_dump(mode="json")
    manifest["preserved_files"].append(
        PreservedFile(
            file_id="file_02",
            original_path=Path(relative_path).name,
            relative_packet_path=relative_path,
            sha256=hashlib.sha256(body).hexdigest(),
            hash_basis="raw_stored_bytes",
            size_bytes=len(body),
        ).model_dump(mode="json")
    )
    manifest["source_slices"][0]["preserved_file_ids"] = ["file_01", "file_02"]
    return SourceCapturePacket.model_validate(manifest)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_ulta_grid_projection_reconciles_visible_placements_and_duplicates() -> None:
    body = _ulta_grid_html().encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "retailer_visible_count_reconciled"
    assert projection.completeness.extracted_unique_parent_count == 2
    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.duplicate_placement_count == 1
    first = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "pimprod2056072"
    )
    assert len(first.placements) == 2
    assert first.source_visible_fields["selected_sku_id"] == "2639131"
    assert first.source_visible_fields["price_range"] == {
        "minimum": "18.00",
        "maximum": "89.00",
    }
    assert first.source_visible_fields["average_rating"] == "4.6"
    assert first.source_visible_fields["review_count"] == 4253
    assert first.source_visible_fields["price_currency"] is None


def test_ulta_grid_compact_content_record_preserves_projection_and_anchor() -> None:
    record = build_ulta_brand_grid_content_record(
        rendered_dom=_ulta_grid_html(),
        final_url="https://www.ulta.com/brand/clinique",
    )
    body = json.dumps(record, separators=(",", ":")).encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert record["content_record_version"] == ULTA_GRID_CONTENT_RECORD_VERSION
    assert projection.completeness.status == "complete"
    first = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "pimprod2056072"
    )
    assert [placement.raw_anchor.anchor_kind for placement in first.placements] == [
        "json_pointer",
        "json_pointer",
    ]
    assert [placement.raw_anchor.anchor_value for placement in first.placements] == [
        "/cards/0",
        "/cards/2",
    ]
    assert b"apollo_state" not in body


def test_ulta_grid_sample_packet_projects_content_record_not_both_copies() -> None:
    dom_body = _ulta_grid_html().encode()
    record_body = json.dumps(
        build_ulta_brand_grid_content_record(
            rendered_dom=_ulta_grid_html(),
            final_url="https://www.ulta.com/brand/clinique",
        ),
        separators=(",", ":"),
    ).encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=dom_body,
        surface="cloakbrowser_snapshot",
    )
    packet = _with_second_preserved_file(
        packet, relative_path="raw/02_content_record.json", body=record_body
    )

    projection = build_retail_grid_projection(
        packet=packet,
        raw_file_bytes_by_file_id={"file_01": dom_body, "file_02": record_body},
    )

    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "retailer_visible_count_reconciled"
    assert projection.completeness.extracted_unique_parent_count == 2
    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.duplicate_placement_count == 1
    assert all(
        placement.raw_anchor is not None
        and placement.raw_anchor.file_id == "file_02"
        for row in projection.rows
        for placement in row.placements
    )


def test_ulta_grid_projection_fails_closed_while_load_more_remains() -> None:
    body = _ulta_grid_html(viewed=2, load_more=True).encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.status == "incomplete"
    assert projection.completeness.termination == "unproven"
    assert "ulta_grid_load_more_control_still_present" in projection.completeness.residuals
    assert any("viewed_count_stale" in value for value in projection.residuals)


def test_ulta_grid_projection_reads_the_rendered_viewed_label_not_serialized_state() -> None:
    body = _ulta_grid_html(stale_serialized_viewed=1).encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.source_visible_grid_facts["viewed_product_placement_count"] == 3
    assert not any("viewed_count_stale" in value for value in projection.residuals)
    assert projection.completeness.status == "complete"


def test_ulta_grid_projection_marks_duplicate_slots_without_claiming_field_drift() -> None:
    body = _ulta_grid_html().encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    duplicate = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "pimprod2056072"
    )
    assert any("duplicate_parent_placement" in value for value in duplicate.residuals)
    assert not any("duplicate_parent_fields_differ" in value for value in duplicate.residuals)


def test_ulta_grid_projection_marks_absent_tile_fields_instead_of_asserting_them() -> None:
    body = _ulta_grid_html(bare_tile=True).encode()
    packet = _packet(
        retailer="ulta",
        locator="https://www.ulta.com/brand/clinique",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    bare = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "gwp8589071995"
    )
    assert "ulta_grid_price_display_not_observed" in bare.residuals
    assert "ulta_grid_average_rating_not_observed" in bare.residuals
    assert "ulta_grid_badge_tags_not_observed" in bare.residuals


@pytest.mark.parametrize(
    ("brand_heading", "brand_slug"),
    [("Lancôme", "lancome"), ("Kiehl's", "kiehls"), ("L’Oréal", "loreal")],
)
def test_ulta_grid_subject_binding_folds_accents_and_apostrophes(
    brand_heading: str, brand_slug: str
) -> None:
    body = _ulta_grid_html(brand_heading=brand_heading).encode()
    packet = _packet(
        retailer="ulta",
        locator=f"https://www.ulta.com/brand/{brand_slug}",
        relative_path="raw/01_cloakbrowser_rendered_dom.html",
        body=body,
        surface="cloakbrowser_snapshot",
    )

    projection = build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )

    assert projection.completeness.subject_binding_confirmed is True
    assert "ulta_grid_subject_binding_unconfirmed" not in projection.completeness.residuals


def _ulta_grid_html(
    *,
    viewed: int | None = None,
    load_more: bool = False,
    stale_serialized_viewed: int | None = None,
    bare_tile: bool = False,
    brand_heading: str = "Clinique",
) -> str:
    def card(
        *, sku: str, href: str, name: str, price: str, rating: str, variant: str
    ) -> str:
        return (
            f'<li data-test="products-list-item" data-sku-id="{sku}">'
            f'<a href="{href}">'
            '<span class="pal-c-ProductCardBody--brandName">Clinique</span>'
            f'<span class="pal-c-ProductCardBody--title">{name}</span></a>'
            f'<span class="pal-c-ProductCardBody--price">{price}</span>'
            f'<span class="pal-c-Ratings"><span class="sr-only">{rating}</span></span>'
            f'<span class="pal-c-ProductCardHeader__variant">{variant}</span>'
            "<button>Add to bag</button></li>"
        )

    cards = [
        card(
            sku="2639131",
            href="/p/moisture-surge-100h-auto-replenishing-hydrator-pimprod2056072?sku=2639131",
            name="Moisture Surge 100H Auto-Replenishing Hydrator",
            price="$18.00 - $89.00",
            rating="4.6 out of 5 stars ; 4,253 reviews",
            variant="5 sizes",
        ),
        card(
            sku="2253011",
            href="https://www.ulta.com/p/almost-lipstick-VP11111?sku=2253011",
            name="Almost Lipstick",
            price="$25.00",
            rating="4.5 out of 5 stars ; 2,100 reviews",
            variant="2 colors",
        ),
        card(
            sku="2639131",
            href="/p/moisture-surge-100h-auto-replenishing-hydrator-pimprod2056072?sku=2639131",
            name="Moisture Surge 100H Auto-Replenishing Hydrator",
            price="$18.00 - $89.00",
            rating="4.6 out of 5 stars ; 4,253 reviews",
            variant="5 sizes",
        ),
    ]
    if bare_tile:
        cards.append(
            '<li data-test="products-list-item" data-sku-id="2645498">'
            '<a href="/p/free-gift-with-purchase-gwp8589071995?sku=2645498">'
            '<span class="pal-c-ProductCardBody--brandName">Clinique</span>'
            '<span class="pal-c-ProductCardBody--title">Free gift with purchase</span>'
            "</a></li>"
        )
    declared = len(cards)
    button = '<button class="LoadContent__button">Load More</button>' if load_more else ""
    # Ulta's Apollo cache keeps the pre-continuation label; it is script CDATA, not
    # rendered text, and it is serialized after the rendered label.
    stale_state = (
        '<script id="apollo_state">'
        f'{{"productsViewedLabel":"You have viewed {stale_serialized_viewed} of {declared}"}}'
        "</script>"
        if stale_serialized_viewed is not None
        else ""
    )
    return (
        '<html lang="en-US"><head><script>window.__APP_LOCALE__="en-US";'
        'fetch("/graphql?ultasite=en-us")</script></head><body>'
        f"<h1>{brand_heading}</h1><ul data-test=\"products-list\">"
        + "".join(cards)
        + "</ul>"
        + f"<p>You have viewed {declared if viewed is None else viewed} of {declared}</p>"
        + f"{button}{stale_state}</body></html>"
    )


def _ulta_category_card(position: int, product_id: str) -> dict:
    return {
        "grid_position": position,
        "source_product_id": product_id,
        "selected_sku_id": f"sku{position}",
        "product_url": f"https://www.ulta.com/p/item-{product_id}?sku=sku{position}",
        "brand_name": "Rare Beauty",
        "name": f"Product {position}",
        "price_display": "$25.00",
        "average_rating": "4.7",
        "review_count": 100 + position,
        "visible_variant_count": None,
        "visible_variant_label": None,
        "badges": [],
    }


def _ulta_category_record(
    *,
    cards: list[dict],
    viewed_count: int | None,
    declared_count: int | None,
    load_more_control_present: bool,
    selected_sort_id: str | None,
    category_heading: str = "Makeup",
) -> bytes:
    record = {
        "content_record_version": ULTA_GRID_CONTENT_RECORD_VERSION,
        "retailer": "ulta",
        "final_url": "https://www.ulta.com/shop/makeup/all?sort=best_sellers",
        "brand_name": category_heading,
        "viewed_count": viewed_count,
        "declared_count": declared_count,
        "load_more_control_present": load_more_control_present,
        "explicit_currency_codes": [],
        "selected_sort_id": selected_sort_id,
        "cards": cards,
    }
    return json.dumps(record, separators=(",", ":")).encode()


def _ulta_category_projection(
    body: bytes, *, locator: str = "https://www.ulta.com/shop/makeup/all"
):
    packet = _packet(
        retailer="ulta",
        locator=locator,
        relative_path="raw/content_record.json",
        body=body,
        surface="cloakbrowser_snapshot",
    )
    return build_retail_grid_projection(
        packet=packet, raw_file_bytes_by_file_id={"file_01": body}
    )


def test_ulta_category_grid_confirms_native_bestseller_bounded_top_window() -> None:
    cards = [_ulta_category_card(i, f"pimprod{i:04d}") for i in range(1, 5)]
    body = _ulta_category_record(
        cards=cards,
        viewed_count=4,
        declared_count=7000,
        load_more_control_present=True,
        selected_sort_id="best_sellers",
    )
    projection = _ulta_category_projection(body)
    gf = projection.source_visible_grid_facts
    assert gf["page_kind"] == "category_grid"
    assert gf["requested_category_slug"] == "makeup"
    assert gf["subject_binding_confirmed"] is True
    assert gf["native_bestseller_order_confirmed"] is True
    assert gf["selected_sort_id"] == "best_sellers"
    assert gf["page_declared_result_count"] == 7000
    assert gf["captured_window_placement_count"] == 4
    # A bounded top window: more remain, and that is NOT an incompleteness.
    assert gf["more_available_beyond_window"] is True
    assert projection.completeness.status == "complete"
    assert projection.completeness.termination == "requested_page_window_reconciled"
    assert projection.completeness.residuals == []


def test_ulta_category_grid_wrong_category_subject_fails() -> None:
    cards = [_ulta_category_card(i, f"pimprod{i:04d}") for i in range(1, 4)]
    body = _ulta_category_record(
        cards=cards,
        viewed_count=3,
        declared_count=7000,
        load_more_control_present=True,
        selected_sort_id="best_sellers",
        category_heading="Fragrance",
    )
    projection = _ulta_category_projection(
        body, locator="https://www.ulta.com/shop/makeup/all"
    )
    assert projection.source_visible_grid_facts["subject_binding_confirmed"] is False
    assert projection.completeness.status == "incomplete"
    assert (
        "ulta_category_grid_subject_binding_unconfirmed"
        in projection.completeness.residuals
    )


def test_ulta_category_grid_non_bestseller_sort_fails_for_sort_not_cards() -> None:
    cards = [_ulta_category_card(i, f"pimprod{i:04d}") for i in range(1, 4)]
    body = _ulta_category_record(
        cards=cards,
        viewed_count=3,
        declared_count=7000,
        load_more_control_present=True,
        selected_sort_id="top_rated",
    )
    projection = _ulta_category_projection(body)
    # Cards are intact and ordered; admission fails for the sort, not missing cards.
    assert len(projection.rows) == 3
    assert (
        projection.source_visible_grid_facts["native_bestseller_order_confirmed"]
        is False
    )
    assert projection.completeness.status == "incomplete"
    assert any(
        residual.startswith("ulta_category_grid_bestseller_sort_unconfirmed")
        for residual in projection.completeness.residuals
    )


def test_ulta_category_grid_premature_stop_breaks_rank_contiguity() -> None:
    # Positions 1,2,4 (missing 3) simulate a dropped placement / premature stop.
    cards = [_ulta_category_card(p, f"pimprod{p:04d}") for p in (1, 2, 4)]
    body = _ulta_category_record(
        cards=cards,
        viewed_count=3,
        declared_count=7000,
        load_more_control_present=True,
        selected_sort_id="best_sellers",
    )
    projection = _ulta_category_projection(body)
    assert projection.completeness.status == "incomplete"
    assert (
        "ulta_category_grid_rank_sequence_non_contiguous"
        in projection.completeness.residuals
    )


def test_ulta_category_grid_duplicate_parent_stays_visible() -> None:
    # Same product at positions 1 and 3; a distinct product at 2.
    base = _ulta_category_card(1, "pimprod0001")
    duplicate = dict(base)
    duplicate["grid_position"] = 3
    cards = [base, _ulta_category_card(2, "pimprod0002"), duplicate]
    body = _ulta_category_record(
        cards=cards,
        viewed_count=3,
        declared_count=7000,
        load_more_control_present=True,
        selected_sort_id="best_sellers",
    )
    projection = _ulta_category_projection(body)
    assert projection.completeness.extracted_unique_parent_count == 2
    assert projection.completeness.extracted_placement_count == 3
    assert projection.completeness.duplicate_placement_count == 1
    dup = next(
        row
        for row in projection.rows
        if row.source_visible_fields["source_product_id"] == "pimprod0001"
    )
    assert len(dup.placements) == 2
    # Duplicate visibility is not itself an incompleteness for a category grid.
    assert projection.completeness.status == "complete"
