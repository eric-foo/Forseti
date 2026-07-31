"""Deterministic Google Ads Transparency Center inventory projection.

The generic CloakBrowser packet remains the acquisition authority. This module
only verifies an exact advertiser packet and projects the source-native creative
identifiers already present in its retained DOM. It does not infer creative
copy, destination, placement, spend, targeting, performance, or source
exhaustion.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field

from schemas.case_models import StrictModel
from source_capture.models import PreservedFile, SourceCapturePacket
from source_capture.projection_shared import (
    normalized_html_text,
    read_packet_directory as _read_packet_directory,
)


GOOGLE_ADS_TRANSPARENCY_SOURCE_FAMILY = "google_ads_transparency_center"
GOOGLE_ADS_TRANSPARENCY_SOURCE_SURFACE = (
    "Google Ads Transparency Center advertiser inventory"
)
GOOGLE_ADS_TRANSPARENCY_PROJECTION_VERSION = (
    "google_ads_transparency_observed_creative_inventory_v1"
)
_DOM_BASENAME = "cloakbrowser_rendered_dom.html"
_METADATA_BASENAME = "cloakbrowser_snapshot_metadata.json"
_ADVERTISER_ID_RE = re.compile(r"AR[0-9]+")
_REGION_RE = re.compile(r"[A-Z]{2}")


class GoogleAdsAdvertiser(StrictModel):
    name: str
    advertiser_id: str
    based_in: str | None = None
    verification_ui_observed: bool


class GoogleAdsCapturedFilterState(StrictModel):
    region: str
    date_range: Literal["Any time"] = "Any time"
    platforms: Literal["All platforms"] = "All platforms"
    formats: Literal["All formats"] = "All formats"
    source_order: Literal["source default"] = "source default"


class GoogleAdsSourceEvidence(StrictModel):
    capture_packet_id: str
    capture_time_utc: str
    manifest_sha256: str
    raw_dom_relative_packet_path: str
    raw_dom_sha256: str
    snapshot_metadata_relative_packet_path: str
    snapshot_metadata_sha256: str
    source_header_display: str | None = None
    rendered_card_position_denominator: int = Field(ge=1)
    observed_rendered_card_position_count: int = Field(ge=1)
    continuation_actions: int = Field(ge=0)


class GoogleAdsProjectionSummary(StrictModel):
    extraction_pattern: Literal[
        "advertiser/{advertiser_id}/creative/{creative_id}?region={region}"
    ] = "advertiser/{advertiser_id}/creative/{creative_id}?region={region}"
    duplicate_policy: Literal[
        "retain first DOM occurrence; retain every observed source card position"
    ] = "retain first DOM occurrence; retain every observed source card position"
    observed_distinct_creative_id_count: int = Field(ge=1)
    observed_rendered_card_position_count: int = Field(ge=1)
    repeated_creative_card_position_count: int = Field(ge=0)
    status: Literal["PARTIAL"] = "PARTIAL"
    source_inventory_exhaustion_status: Literal["NOT_PROVEN"] = "NOT_PROVEN"
    currentness: str
    residuals: list[str] = Field(default_factory=list)
    next_source_fact: Literal[
        "A source-visible terminal state or further continuation is required before claiming source exhaustion."
    ] = "A source-visible terminal state or further continuation is required before claiming source exhaustion."


class GoogleAdsCreativeInventoryRow(StrictModel):
    source_dom_order: int = Field(ge=1)
    creative_id: str
    first_source_card_position: int = Field(ge=1)
    source_card_positions: list[int] = Field(min_length=1)
    detail_url: str


class GoogleAdsTransparencyProjection(StrictModel):
    schema_version: Literal[
        "google_ads_transparency_observed_creative_inventory_v1"
    ] = GOOGLE_ADS_TRANSPARENCY_PROJECTION_VERSION
    artifact_role: Literal[
        "Deterministic projection of observed source creative identifiers"
    ] = "Deterministic projection of observed source creative identifiers"
    authority_boundary: Literal["retrieval_only"] = "retrieval_only"
    advertiser: GoogleAdsAdvertiser
    captured_filter_state: GoogleAdsCapturedFilterState
    source_evidence: GoogleAdsSourceEvidence
    projection: GoogleAdsProjectionSummary
    non_claims: list[str]
    creative_inventory: list[GoogleAdsCreativeInventoryRow] = Field(min_length=1)


def build_google_ads_transparency_projection_from_packet_directory(
    packet_or_manifest_path: Path,
    *,
    expected_advertiser_name: str,
    expected_advertiser_id: str,
    expected_region: str,
) -> GoogleAdsTransparencyProjection:
    """Read, verify, and project one exact-advertiser inventory packet."""

    manifest_path = (
        packet_or_manifest_path / "manifest.json"
        if packet_or_manifest_path.is_dir()
        else packet_or_manifest_path
    )
    manifest_bytes_before_read = manifest_path.read_bytes()
    packet, raw_file_bytes_by_file_id = _read_packet_directory(
        packet_or_manifest_path
    )
    manifest_bytes_after_read = manifest_path.read_bytes()
    if manifest_bytes_after_read != manifest_bytes_before_read:
        raise ValueError("google_ads_manifest_changed_during_projection")
    return build_google_ads_transparency_projection(
        packet=packet,
        raw_file_bytes_by_file_id=raw_file_bytes_by_file_id,
        manifest_sha256=hashlib.sha256(manifest_bytes_before_read).hexdigest(),
        expected_advertiser_name=expected_advertiser_name,
        expected_advertiser_id=expected_advertiser_id,
        expected_region=expected_region,
    )


def build_google_ads_transparency_projection(
    *,
    packet: SourceCapturePacket,
    raw_file_bytes_by_file_id: dict[str, bytes],
    manifest_sha256: str,
    expected_advertiser_name: str,
    expected_advertiser_id: str,
    expected_region: str,
) -> GoogleAdsTransparencyProjection:
    """Project source-native IDs after packet, identity, filter, and hash gates."""

    advertiser_name = expected_advertiser_name.strip()
    advertiser_id = expected_advertiser_id.strip()
    region = expected_region.strip().upper()
    if not advertiser_name:
        raise ValueError("expected advertiser name must be non-empty")
    if _ADVERTISER_ID_RE.fullmatch(advertiser_id) is None:
        raise ValueError(
            "expected advertiser id must match the source-native AR<digits> shape"
        )
    if _REGION_RE.fullmatch(region) is None:
        raise ValueError("expected region must be a two-letter uppercase code")

    if packet.source_family != GOOGLE_ADS_TRANSPARENCY_SOURCE_FAMILY:
        raise ValueError(
            "google_ads_source_family_mismatch:"
            f"expected={GOOGLE_ADS_TRANSPARENCY_SOURCE_FAMILY}:"
            f"observed={packet.source_family}"
        )
    if packet.source_surface != GOOGLE_ADS_TRANSPARENCY_SOURCE_SURFACE:
        raise ValueError(
            "google_ads_source_surface_mismatch:"
            f"expected={GOOGLE_ADS_TRANSPARENCY_SOURCE_SURFACE}:"
            f"observed={packet.source_surface}"
        )
    if packet.source_locator.value is None:
        raise ValueError("google_ads_source_locator_unknown")
    locator = packet.source_locator.value
    _validate_exact_advertiser_locator(
        locator, advertiser_id=advertiser_id, region=region
    )

    raw_dom_file = _one_preserved_file(packet, _DOM_BASENAME)
    metadata_file = _one_preserved_file(packet, _METADATA_BASENAME)
    raw_dom_bytes = _verified_preserved_bytes(
        raw_dom_file, raw_file_bytes_by_file_id
    )
    metadata_bytes = _verified_preserved_bytes(
        metadata_file, raw_file_bytes_by_file_id
    )
    raw_dom = raw_dom_bytes.decode("utf-8")
    metadata = json.loads(metadata_bytes.decode("utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("google_ads_snapshot_metadata_must_be_object")
    if metadata.get("access_blocked") is not False:
        raise ValueError("google_ads_snapshot_access_blocked_or_unknown")
    final_url = metadata.get("final_url")
    if not isinstance(final_url, str):
        raise ValueError("google_ads_snapshot_final_url_missing")
    _validate_exact_advertiser_locator(
        final_url, advertiser_id=advertiser_id, region=region
    )
    if final_url != locator:
        raise ValueError("google_ads_manifest_and_snapshot_locator_mismatch")

    capture_time = metadata.get("capture_timestamp")
    continuation_actions = metadata.get("scroll_passes")
    if not isinstance(capture_time, str) or not capture_time:
        raise ValueError("google_ads_snapshot_capture_timestamp_missing")
    if (
        isinstance(continuation_actions, bool)
        or not isinstance(continuation_actions, int)
        or continuation_actions < 0
    ):
        raise ValueError("google_ads_snapshot_scroll_passes_invalid")

    observed_names = _observed_advertiser_names(raw_dom)
    if advertiser_name not in observed_names:
        raise ValueError(
            "google_ads_advertiser_name_not_observed:"
            f"expected={advertiser_name}:observed={sorted(observed_names)}"
        )
    if advertiser_id not in raw_dom:
        raise ValueError(
            f"google_ads_advertiser_id_not_observed:{advertiser_id}"
        )
    for required_filter in ("Any time", "All platforms", "All formats"):
        if required_filter not in raw_dom:
            raise ValueError(
                "google_ads_filter_state_not_observed:"
                f"{required_filter.replace(' ', '_').lower()}"
            )

    card_matches = _card_matches(
        raw_dom, advertiser_id=advertiser_id, region=region
    )
    if not card_matches:
        raise ValueError("google_ads_no_exact_advertiser_creative_cards")

    denominators = {denominator for _, _, denominator in card_matches}
    if len(denominators) != 1:
        raise ValueError(
            "google_ads_source_card_denominator_conflict:"
            + ",".join(str(value) for value in sorted(denominators))
        )
    rendered_position_denominator = next(iter(denominators))
    position_to_creative: dict[int, str] = {}
    creative_positions: dict[str, list[int]] = {}
    ordered_creative_ids: list[str] = []
    for creative_id, position, observed_denominator in card_matches:
        if position < 1 or position > observed_denominator:
            raise ValueError(
                f"google_ads_source_card_position_out_of_range:{position}"
            )
        prior_creative = position_to_creative.setdefault(position, creative_id)
        if prior_creative != creative_id:
            raise ValueError(
                "google_ads_source_card_position_identity_conflict:"
                f"{position}:{prior_creative}:{creative_id}"
            )
        if creative_id not in creative_positions:
            creative_positions[creative_id] = []
            ordered_creative_ids.append(creative_id)
        if position not in creative_positions[creative_id]:
            creative_positions[creative_id].append(position)

    inventory = [
        GoogleAdsCreativeInventoryRow(
            source_dom_order=index,
            creative_id=creative_id,
            first_source_card_position=creative_positions[creative_id][0],
            source_card_positions=creative_positions[creative_id],
            detail_url=(
                "https://adstransparency.google.com/advertiser/"
                f"{advertiser_id}/creative/{creative_id}?region={region}"
            ),
        )
        for index, creative_id in enumerate(ordered_creative_ids, start=1)
    ]
    observed_position_count = len(position_to_creative)
    residuals = ["google_ads_source_exhaustion_signal_not_observed"]
    if observed_position_count < rendered_position_denominator:
        residuals.append(
            "google_ads_rendered_card_positions_not_fully_materialized:"
            f"observed={observed_position_count}:"
            f"denominator={rendered_position_denominator}"
        )
    repeated_position_count = observed_position_count - len(inventory)
    if repeated_position_count:
        residuals.append(
            "google_ads_rendered_card_positions_reuse_creative_ids:"
            f"positions={observed_position_count}:distinct_creatives={len(inventory)}"
        )

    header_match = re.search(r"~[0-9,]+\s+ads", raw_dom, re.IGNORECASE)
    based_in_match = re.search(
        r"Based in:</strong>\s*(?:the\s+)?([^<]+)</div>",
        raw_dom,
        re.IGNORECASE,
    )
    based_in = (
        normalized_html_text(based_in_match.group(1))
        if based_in_match
        else None
    )

    return GoogleAdsTransparencyProjection(
        advertiser=GoogleAdsAdvertiser(
            name=advertiser_name,
            advertiser_id=advertiser_id,
            based_in=based_in,
            verification_ui_observed=(
                "<verification-popup" in raw_dom
                and "identity verification process" in raw_dom
            ),
        ),
        captured_filter_state=GoogleAdsCapturedFilterState(region=region),
        source_evidence=GoogleAdsSourceEvidence(
            capture_packet_id=packet.packet_id,
            capture_time_utc=capture_time,
            manifest_sha256=manifest_sha256,
            raw_dom_relative_packet_path=raw_dom_file.relative_packet_path,
            raw_dom_sha256=raw_dom_file.sha256,
            snapshot_metadata_relative_packet_path=metadata_file.relative_packet_path,
            snapshot_metadata_sha256=metadata_file.sha256,
            source_header_display=header_match.group(0) if header_match else None,
            rendered_card_position_denominator=rendered_position_denominator,
            observed_rendered_card_position_count=observed_position_count,
            continuation_actions=continuation_actions,
        ),
        projection=GoogleAdsProjectionSummary(
            observed_distinct_creative_id_count=len(inventory),
            observed_rendered_card_position_count=observed_position_count,
            repeated_creative_card_position_count=repeated_position_count,
            currentness=f"{capture_time} capture state",
            residuals=residuals,
        ),
        non_claims=[
            "not source exhaustion or all advertiser Google ads",
            "not per-ad placement evidence",
            "not spend, delivery, targeting, impression, reach, performance, or strategy evidence",
            "not complete creative copy, media, destination, product-family, or offer extraction",
            "not proof that each creative ID is visually or byte-distinct",
        ],
        creative_inventory=inventory,
    )


def google_ads_transparency_projection_json_text(
    projection: GoogleAdsTransparencyProjection,
) -> str:
    """Render stable UTF-8 JSON content."""

    return (
        json.dumps(
            projection.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def write_google_ads_transparency_projection(
    *,
    projection: GoogleAdsTransparencyProjection,
    output_path: Path,
    overwrite: bool = False,
) -> Path:
    """Write byte-stable UTF-8 JSON without mutating the source packet."""

    if output_path.exists() and output_path.is_dir():
        raise IsADirectoryError(
            f"projection output is a directory: {output_path}"
        )
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"projection output already exists: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = google_ads_transparency_projection_json_text(projection).encode(
        "utf-8"
    )
    if overwrite:
        output_path.write_bytes(payload)
    else:
        with output_path.open("xb") as handle:
            handle.write(payload)
    return output_path


def _validate_exact_advertiser_locator(
    locator: str, *, advertiser_id: str, region: str
) -> None:
    parsed = urlsplit(locator)
    expected_path = f"/advertiser/{advertiser_id}"
    if (
        parsed.scheme != "https"
        or parsed.hostname != "adstransparency.google.com"
        or parsed.path.rstrip("/") != expected_path
        or parsed.query != f"region={region}"
        or parsed.fragment
    ):
        raise ValueError(
            "google_ads_exact_advertiser_locator_mismatch:"
            f"expected=https://adstransparency.google.com{expected_path}?region={region}:"
            f"observed={locator}"
        )


def _one_preserved_file(
    packet: SourceCapturePacket, basename: str
) -> PreservedFile:
    matches = [
        preserved
        for preserved in packet.preserved_files
        if Path(preserved.relative_packet_path).name.endswith(basename)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"google_ads_preserved_file_count_invalid:{basename}:{len(matches)}"
        )
    return matches[0]


def _verified_preserved_bytes(
    preserved: PreservedFile, raw_file_bytes_by_file_id: dict[str, bytes]
) -> bytes:
    body = raw_file_bytes_by_file_id.get(preserved.file_id)
    if body is None:
        raise ValueError(
            f"google_ads_preserved_bytes_missing:{preserved.file_id}"
        )
    if len(body) != preserved.size_bytes:
        raise ValueError(
            "google_ads_preserved_size_mismatch:"
            f"{preserved.file_id}:expected={preserved.size_bytes}:observed={len(body)}"
        )
    observed_sha256 = hashlib.sha256(body).hexdigest()
    if observed_sha256 != preserved.sha256:
        raise ValueError(
            "google_ads_preserved_sha256_mismatch:"
            f"{preserved.file_id}:expected={preserved.sha256}:observed={observed_sha256}"
        )
    return body


def _observed_advertiser_names(raw_dom: str) -> set[str]:
    patterns = (
        r'<div class="advertiser-name[^"]*">(.*?)</div>',
        r'<div class="legal-name[^"]*"><strong>Legal name:</strong>\s*(.*?)</div>',
    )
    names: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, raw_dom, re.IGNORECASE | re.DOTALL):
            normalized = normalized_html_text(html.unescape(match.group(1)))
            if normalized:
                names.add(normalized)
    return names


def _card_matches(
    raw_dom: str, *, advertiser_id: str, region: str
) -> list[tuple[str, int, int]]:
    pattern = re.compile(
        r'href=["\'](?:https://adstransparency\.google\.com)?'
        rf"/advertiser/{re.escape(advertiser_id)}/creative/(CR[0-9]+)"
        rf"\?region={re.escape(region)}[\"'][^>]*"
        r'aria-label=["\']Advertisement \(([0-9,]+) of ([0-9,]+)\)["\']',
        re.IGNORECASE | re.DOTALL,
    )
    return [
        (
            match.group(1),
            int(match.group(2).replace(",", "")),
            int(match.group(3).replace(",", "")),
        )
        for match in pattern.finditer(raw_dom)
    ]
