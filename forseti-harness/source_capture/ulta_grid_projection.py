from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping
from urllib.parse import urlparse, urlunparse

from source_capture.models import SourceCapturePacket, VisibleFactStatus
from source_capture.ulta_brand_grid import (
    ULTA_GRID_CONTENT_RECORD_VERSION,
    UltaBrandGridState,
    UltaBrandGridStateError,
    load_ulta_brand_grid_state,
)


_PRICE_RANGE_RE = re.compile(
    r"^\s*\$?(?P<minimum>\d+(?:\.\d+)?)\s*[-\u2013]\s*\$?(?P<maximum>\d+(?:\.\d+)?)\s*$"
)
_PRIMARY_PRICE_RE = re.compile(
    r"^\s*\$(?P<price>\d+(?:\.\d+)?)(?:\s*\([^)]*value\))?\s*$",
    re.IGNORECASE,
)
_PLACEMENT_SCOPED_FIELDS = frozenset({"grid_position"})


def build_ulta_grid_projection(
    *, packet: SourceCapturePacket, raw_file_bytes_by_file_id: Mapping[str, bytes]
):
    from source_capture.retail_grid_projection import (
        RetailGridCompletenessReconciliation,
        RetailGridProjectionLossLedger,
        RetailGridProjectionPacket,
        RetailGridProjectionPlacement,
        RetailGridProjectionRow,
        RetailGridProjectionInputError,
    )
    from source_capture.retail_pdp_projection import RetailProjectionRawAnchor, RetailProjectionRawRef

    preserved_files = {item.file_id: item for item in packet.preserved_files}
    rows: list[RetailGridProjectionRow] = []
    residuals: list[str] = []
    states: list[UltaBrandGridState] = []
    for source_slice in packet.source_slices:
        raw_ref = RetailProjectionRawRef(packet_id=packet.packet_id, slice_id=source_slice.slice_id)
        slice_row_count = 0
        for file_id in source_slice.preserved_file_ids:
            preserved_file = preserved_files[file_id]
            body = raw_file_bytes_by_file_id.get(file_id)
            if body is None:
                raise ValueError(f"raw bytes are required for preserved file id: {file_id}")
            try:
                state = load_ulta_brand_grid_state(body.decode("utf-8", errors="replace"))
            except UltaBrandGridStateError as exc:
                raise RetailGridProjectionInputError(str(exc)) from exc
            if state is None:
                continue
            states.append(state)
            raw_anchor = RetailProjectionRawAnchor(
                file_id=preserved_file.file_id,
                relative_packet_path=preserved_file.relative_packet_path,
                sha256=preserved_file.sha256,
                hash_basis=preserved_file.hash_basis,
                anchor_kind="file",
            )
            currency_code = (
                state.explicit_currency_codes[0]
                if len(state.explicit_currency_codes) == 1
                else None
            )
            for card in state.cards:
                if card.source_product_id is None or card.product_url is None or card.name is None:
                    residuals.append(
                        f"{source_slice.slice_id}:ulta:grid_tile_identity_incomplete:{card.grid_position}"
                    )
                    continue
                if state.content_record_version == ULTA_GRID_CONTENT_RECORD_VERSION:
                    placement_anchor = raw_anchor.model_copy(
                        update={
                            "anchor_kind": "json_pointer",
                            "anchor_value": f"/cards/{card.grid_position - 1}",
                        }
                    )
                else:
                    selector = (
                        f':nth-match([data-test="products-list-item"], '
                        f"{card.grid_position})"
                    )
                    placement_anchor = raw_anchor.model_copy(
                        update={"anchor_kind": "html_selector", "anchor_value": selector}
                    )
                price, price_range = _price_fields(card.price_display)
                fields: dict[str, Any | None] = {
                    "retailer": "ulta",
                    "page_kind": "grid",
                    "capture_time": _fact_value(source_slice.timing.capture_time),
                    "locale_pin": _fact_value(source_slice.locale_pin),
                    "location_pin": None,
                    "series_id": packet.series_id,
                    "exact_inventory_quantity": None,
                    "exact_inventory_quantity_posture": "not_observed",
                    "sold_units": None,
                    "sold_units_posture": "not_observed",
                    "source_product_id": card.source_product_id,
                    "product_url": card.product_url,
                    "canonical_product_url": _canonical_url(card.product_url),
                    "name": card.name,
                    "brand": card.brand_name,
                    "grid_position": card.grid_position,
                    "category": None,
                    "breadcrumb": None,
                    "selected_sku_id": card.selected_sku_id,
                    "selected_variant": None,
                    "price": price,
                    "price_display": card.price_display,
                    "price_range": price_range,
                    "price_currency": currency_code,
                    "currency_symbol": (
                        "$" if card.price_display and card.price_display.startswith("$") else None
                    ),
                    "average_rating": card.average_rating,
                    "rating_count": card.review_count,
                    "review_count": card.review_count,
                    "badges": list(card.badges),
                    "availability_summary": None,
                    "pickup_eligible": None,
                    "same_day_eligible": None,
                    "visible_variant_count": card.visible_variant_count,
                    "visible_variant_label": card.visible_variant_label,
                    "location_ids": [],
                    "seller": "Ulta Beauty",
                }
                row_residuals = [
                    "ulta_grid_written_review_count_not_observed",
                    "ulta_grid_exact_inventory_quantity_not_observed",
                    "ulta_grid_sold_units_not_observed",
                    "ulta_grid_selected_variant_not_observed",
                    "ulta_grid_location_pin_not_observed",
                    "ulta_grid_product_category_not_observed",
                    "ulta_grid_availability_summary_not_observed",
                ]
                if currency_code is None:
                    row_residuals.append("ulta_grid_explicit_currency_code_not_observed")
                if card.price_display is None:
                    row_residuals.append("ulta_grid_price_display_not_observed")
                elif price is None and price_range is None:
                    row_residuals.append("ulta_grid_price_display_not_mechanically_parsed")
                if card.average_rating is None or card.review_count is None:
                    row_residuals.append("ulta_grid_average_rating_not_observed")
                if not card.badges:
                    row_residuals.append("ulta_grid_badge_tags_not_observed")
                rows.append(
                    RetailGridProjectionRow(
                        row_id=f"{source_slice.slice_id}:grid:ulta:{card.source_product_id}",
                        retailer="ulta",
                        raw_ref=raw_ref,
                        raw_anchor=placement_anchor,
                        placements=[
                            RetailGridProjectionPlacement(
                                grid_position=card.grid_position, raw_anchor=placement_anchor
                            )
                        ],
                        source_visible_fields=fields,
                        residuals=row_residuals,
                    )
                )
                slice_row_count += 1
        if slice_row_count == 0:
            residuals.append(f"{source_slice.slice_id}:ulta:grid_product_tiles_absent")

    rows, merge_residuals = _merge_parent_rows(rows)
    residuals.extend(merge_residuals)
    placement_count = sum(max(1, len(row.placements)) for row in rows)
    duplicate_count = placement_count - len(rows)
    state = states[0] if len(states) == 1 else None

    requested_category_slug = _requested_category_slug(packet)
    if requested_category_slug is not None:
        return _build_ulta_category_grid_result(
            packet=packet,
            rows=rows,
            residuals=residuals,
            states=states,
            state=state,
            placement_count=placement_count,
            duplicate_count=duplicate_count,
            requested_category_slug=requested_category_slug,
            RetailGridCompletenessReconciliation=RetailGridCompletenessReconciliation,
            RetailGridProjectionLossLedger=RetailGridProjectionLossLedger,
            RetailGridProjectionPacket=RetailGridProjectionPacket,
        )

    reconciliation_residuals: list[str] = []
    if not states:
        reconciliation_residuals.append("ulta_grid_state_absent")
    elif len(states) != 1:
        reconciliation_residuals.append(f"ulta_grid_state_count:{len(states)}")
    declared_count = state.declared_count if state else None
    viewed_count = state.viewed_count if state else None
    requested_slug = _requested_brand_slug(packet)
    observed_brand = state.brand_name if state else None
    subject_confirmed = bool(
        requested_slug and observed_brand and _slugify(observed_brand) == requested_slug
    )
    if not subject_confirmed:
        reconciliation_residuals.append("ulta_grid_subject_binding_unconfirmed")
    if declared_count is None:
        reconciliation_residuals.append("ulta_grid_declared_count_absent")
    elif declared_count != placement_count:
        reconciliation_residuals.append(
            f"ulta_grid_declared_placement_count_mismatch:declared={declared_count}:anchored={placement_count}"
        )
    if viewed_count is None:
        residuals.append("ulta_grid_viewed_count_absent")
    elif viewed_count != placement_count:
        residuals.append(
            f"ulta_grid_viewed_count_stale:viewed={viewed_count}:anchored={placement_count}"
        )
    if state and len(state.cards) != placement_count:
        reconciliation_residuals.append(
            f"ulta_grid_serialized_placement_count_mismatch:serialized={len(state.cards)}:anchored={placement_count}"
        )
    if state and state.load_more_control_present:
        reconciliation_residuals.append("ulta_grid_load_more_control_still_present")
    if any("identity_incomplete" in item for item in residuals):
        reconciliation_residuals.append("ulta_grid_incomplete_product_identity_present")
    complete = not reconciliation_residuals
    completeness = RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_count,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination="retailer_visible_count_reconciled" if complete else "unproven",
        residuals=reconciliation_residuals,
    )
    return RetailGridProjectionPacket(
        packet_id=packet.packet_id,
        rows=rows,
        source_visible_grid_facts={
            "retailer": "ulta",
            "page_kind": "brand_grid",
            "brand_name": observed_brand,
            "requested_brand_slug": requested_slug,
            "subject_binding_confirmed": subject_confirmed,
            "page_declared_result_count": declared_count,
            "viewed_product_placement_count": viewed_count,
            "serialized_product_placement_count": len(state.cards) if state else None,
            "explicit_currency_codes": list(state.explicit_currency_codes) if state else [],
            "delivery_location_pin": None,
        },
        completeness=completeness,
        loss_ledger=RetailGridProjectionLossLedger(
            preserved_evidence_rows=len(rows), structure_preserved=bool(rows)
        ),
        residuals=list(dict.fromkeys(residuals)),
    )


def _merge_parent_rows(rows):
    by_product_id = {}
    residuals: list[str] = []
    for row in rows:
        product_id = str(row.source_visible_fields["source_product_id"])
        existing = by_product_id.get(product_id)
        if existing is None:
            by_product_id[product_id] = row
            continue
        placements = [*existing.placements, *row.placements]
        marker = f"ulta_grid_duplicate_parent_placement:{product_id}:{len(placements)}"
        row_residuals = [*existing.residuals, marker]
        if _parent_scoped_fields(existing.source_visible_fields) != _parent_scoped_fields(
            row.source_visible_fields
        ):
            row_residuals.append(f"ulta_grid_duplicate_parent_fields_differ:{product_id}")
        by_product_id[product_id] = existing.model_copy(
            update={"placements": placements, "residuals": list(dict.fromkeys(row_residuals))}
        )
        residuals.append(marker)
    return list(by_product_id.values()), residuals


def _parent_scoped_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Parent-product facts only; a duplicate tile legitimately occupies another slot."""
    return {key: value for key, value in fields.items() if key not in _PLACEMENT_SCOPED_FIELDS}


def _price_fields(value: str | None):
    if value is None:
        return None, None
    range_match = _PRICE_RANGE_RE.fullmatch(value)
    if range_match:
        return None, {"minimum": range_match.group("minimum"), "maximum": range_match.group("maximum")}
    price_match = _PRIMARY_PRICE_RE.fullmatch(value)
    return (price_match.group("price"), None) if price_match else (None, None)


def _requested_brand_slug(packet: SourceCapturePacket) -> str | None:
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator:
            parts = [part for part in urlparse(locator).path.split("/") if part]
            if len(parts) >= 2 and parts[0].lower() == "brand":
                return parts[1].lower()
    return None


def _requested_category_slug(packet: SourceCapturePacket) -> str | None:
    """Return the Ulta category slug for a ``/shop/<category>/all`` grid request."""
    locators = [_fact_value(packet.source_locator)] + [
        _fact_value(source_slice.locator) for source_slice in packet.source_slices
    ]
    for locator in locators:
        if locator:
            parts = [part for part in urlparse(locator).path.split("/") if part]
            if (
                len(parts) == 3
                and parts[0].lower() == "shop"
                and parts[2].lower() == "all"
            ):
                return parts[1].lower()
    return None


def _build_ulta_category_grid_result(
    *,
    packet,
    rows,
    residuals,
    states,
    state,
    placement_count,
    duplicate_count,
    requested_category_slug,
    RetailGridCompletenessReconciliation,
    RetailGridProjectionLossLedger,
    RetailGridProjectionPacket,
):
    """Reconcile a bounded top-window Ulta category bestseller grid.

    Unlike the brand grid (where captured count must equal the declared count), a
    category grid captures a bounded top window of a much larger cohort, so
    ``declared != captured`` is expected and a still-present load-more control is
    not an error. Native bestseller order and category subject must be
    source-confirmed, and the captured window must be a contiguous rank-ordered slice.
    """
    cat_residuals: list[str] = []
    if not states:
        cat_residuals.append("ulta_category_grid_state_absent")
    elif len(states) != 1:
        cat_residuals.append(f"ulta_category_grid_state_count:{len(states)}")

    # The category grid renders its category name in the same <h1> the brand grid
    # uses for the brand name.
    observed_category = state.brand_name if state else None
    selected_sort = state.selected_sort_id if state else None
    subject_confirmed = bool(
        observed_category and _slugify(observed_category) == requested_category_slug
    )
    if not subject_confirmed:
        cat_residuals.append("ulta_category_grid_subject_binding_unconfirmed")
    native_order_confirmed = selected_sort == "best_sellers"
    if not native_order_confirmed:
        cat_residuals.append(
            f"ulta_category_grid_bestseller_sort_unconfirmed:{selected_sort}"
        )

    declared_count = state.declared_count if state else None
    viewed_count = state.viewed_count if state else None
    if declared_count is None:
        cat_residuals.append("ulta_category_grid_declared_count_absent")
    if viewed_count is None:
        cat_residuals.append("ulta_category_grid_viewed_count_absent")
    elif viewed_count != placement_count:
        cat_residuals.append(
            "ulta_category_grid_viewed_count_mismatch:"
            f"viewed={viewed_count}:anchored={placement_count}"
        )
    if state and len(state.cards) != placement_count:
        cat_residuals.append(
            "ulta_category_grid_serialized_placement_count_mismatch:"
            f"serialized={len(state.cards)}:anchored={placement_count}"
        )
    positions = sorted(
        placement.grid_position for row in rows for placement in row.placements
    )
    if positions != list(range(1, placement_count + 1)):
        cat_residuals.append("ulta_category_grid_rank_sequence_non_contiguous")
    if declared_count is not None and placement_count > declared_count:
        cat_residuals.append("ulta_category_grid_window_exceeds_declared_cohort")
    if any("identity_incomplete" in item for item in residuals):
        cat_residuals.append("ulta_category_grid_incomplete_product_identity_present")

    window_exhausts_cohort = (
        declared_count is not None and placement_count >= declared_count
    )
    more_available = bool(state.load_more_control_present) if state else None
    complete = not cat_residuals
    completeness = RetailGridCompletenessReconciliation(
        status="complete" if complete else "incomplete",
        page_declared_result_count=declared_count,
        extracted_unique_parent_count=len(rows),
        extracted_placement_count=placement_count,
        duplicate_placement_count=duplicate_count,
        subject_binding_confirmed=subject_confirmed,
        termination=(
            (
                "retailer_terminal_reconciled"
                if window_exhausts_cohort
                else "requested_page_window_reconciled"
            )
            if complete
            else "unproven"
        ),
        residuals=cat_residuals,
    )
    grid_facts = {
        "retailer": "ulta",
        "page_kind": "category_grid",
        "category_name": observed_category,
        "requested_category_slug": requested_category_slug,
        "subject_binding_confirmed": subject_confirmed,
        "selected_sort_id": selected_sort,
        "native_bestseller_order_confirmed": native_order_confirmed,
        "page_declared_result_count": declared_count,
        "captured_window_placement_count": placement_count,
        "viewed_product_placement_count": viewed_count,
        "serialized_product_placement_count": len(state.cards) if state else None,
        "more_available_beyond_window": more_available,
        "explicit_currency_codes": list(state.explicit_currency_codes) if state else [],
        "delivery_location_pin": None,
    }
    return RetailGridProjectionPacket(
        packet_id=packet.packet_id,
        rows=rows,
        source_visible_grid_facts=grid_facts,
        completeness=completeness,
        loss_ledger=RetailGridProjectionLossLedger(
            preserved_evidence_rows=len(rows), structure_preserved=bool(rows)
        ),
        residuals=list(dict.fromkeys(residuals)),
    )


def _fact_value(fact: object | None) -> str | None:
    if fact is not None and getattr(fact, "status", None) == VisibleFactStatus.KNOWN:
        return getattr(fact, "value", None)
    return None


def _slugify(value: str) -> str:
    """Fold the rendered brand heading the way Ulta folds it into a `/brand/<slug>` path.

    Ulta brand slugs are ASCII and drop diacritics and apostrophes rather than
    replacing them with a separator, so a raw ASCII-only substitution would make
    every accented or possessive brand heading fail subject binding.
    """
    decomposed = unicodedata.normalize("NFKD", value.lower())
    folded = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character) and character not in "'’"
    )
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def _canonical_url(value: str) -> str:
    parsed = urlparse(value)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


__all__ = ["build_ulta_grid_projection"]
