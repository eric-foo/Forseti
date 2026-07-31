from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runners.run_google_ads_transparency_projection import main
from source_capture.google_ads_transparency_projection import (
    build_google_ads_transparency_projection_from_packet_directory,
    google_ads_transparency_projection_json_text,
)
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


ADVERTISER_NAME = "Example Beauty, LLC"
ADVERTISER_ID = "AR12345678901234567890"
LOCATOR = (
    "https://adstransparency.google.com/advertiser/"
    f"{ADVERTISER_ID}?region=US"
)
CREATIVE_A = "CR11111111111111111111"
CREATIVE_B = "CR22222222222222222222"


def _dom(*, advertiser_name: str = ADVERTISER_NAME) -> bytes:
    return (
        "<html><body>"
        f'<div class="advertiser-name x">{advertiser_name}</div>'
        f'<div class="legal-name x"><strong>Legal name:</strong> {advertiser_name}</div>'
        '<div class="location x"><strong>Based in:</strong> the United States</div>'
        '<verification-popup><span>View advertiser identity verification process</span>'
        "</verification-popup>"
        "<span>Any time</span><span>All platforms</span><span>All formats</span>"
        "<span>~3 ads</span>"
        f'<a href="/advertiser/{ADVERTISER_ID}/creative/{CREATIVE_A}?region=US" '
        'aria-label="Advertisement (1 of 3)"></a>'
        f'<a href="/advertiser/{ADVERTISER_ID}/creative/{CREATIVE_A}?region=US" '
        'aria-label="Advertisement (2 of 3)"></a>'
        f'<a href="/advertiser/{ADVERTISER_ID}/creative/{CREATIVE_B}?region=US" '
        'aria-label="Advertisement (3 of 3)"></a>'
        "</body></html>"
    ).encode("utf-8")


def _metadata(*, final_url: str = LOCATOR) -> bytes:
    return json.dumps(
        {
            "access_blocked": False,
            "capture_timestamp": "2026-07-31T01:02:03Z",
            "final_url": final_url,
            "requested_url": final_url,
            "scroll_passes": 10,
        },
        sort_keys=True,
    ).encode("utf-8")


def _timing() -> PacketTiming:
    return PacketTiming(
        source_publication_or_event=unknown_with_reason(
            "test fixture has no source event time"
        ),
        source_edit_or_version=unknown_with_reason(
            "test fixture has no source edit time"
        ),
        capture_time=known_fact("2026-07-31T01:02:03Z"),
        recapture_time=not_applicable("first capture"),
        cutoff_posture=unknown_with_reason("test fixture has no cutoff"),
    )


def _write_packet(
    packet_dir: Path,
    *,
    dom: bytes | None = None,
    metadata: bytes | None = None,
    source_family: str = "google_ads_transparency_center",
    locator: str = LOCATOR,
) -> Path:
    dom = _dom() if dom is None else dom
    metadata = _metadata(final_url=locator) if metadata is None else metadata
    raw_dir = packet_dir / "raw"
    raw_dir.mkdir(parents=True)
    dom_path = raw_dir / "01_cloakbrowser_rendered_dom.html"
    metadata_path = raw_dir / "04_cloakbrowser_snapshot_metadata.json"
    dom_path.write_bytes(dom)
    metadata_path.write_bytes(metadata)
    timing = _timing()
    packet = SourceCapturePacket(
        packet_id="01TESTGOOGLEADSPROJECTION",
        manifest_version="source_capture_packet_manifest_v1",
        obligation_contract_version=(
            "core_spine_v0_data_capture_spine_obligation_contract_v0"
        ),
        source_family=source_family,
        source_surface="Google Ads Transparency Center advertiser inventory",
        source_locator=known_fact(locator),
        requested_decision_context=known_fact("test advertiser inventory"),
        capture_context=known_fact("unit test packet"),
        actor_audience_context=unknown_with_reason("not supplied by fixture"),
        capture_mode=CaptureModeCategory.AUTOMATED_EXTRACTION,
        operator_category="unit_test",
        session_identity="01TESTSESSION",
        timing=timing,
        access_posture=known_fact("public rendered packet fixture"),
        archive_history_posture=not_attempted("archive not queried"),
        media_modality_posture=not_attempted("linked media not fetched"),
        re_capture_relationship=not_applicable("first capture"),
        source_slices=[
            SourceCaptureSlice(
                slice_id="cloakbrowser_snapshot_01",
                locator=known_fact(locator),
                timing=timing,
                access_posture=known_fact("public rendered packet fixture"),
                archive_history_posture=not_attempted("archive not queried"),
                media_modality_posture=not_attempted("linked media not fetched"),
                re_capture_relationship=not_applicable("first capture"),
                preserved_file_ids=["file_01", "file_02"],
            )
        ],
        preserved_files=[
            PreservedFile(
                file_id="file_01",
                original_path="cloakbrowser_rendered_dom.html",
                relative_packet_path="raw/01_cloakbrowser_rendered_dom.html",
                sha256=hashlib.sha256(dom).hexdigest(),
                hash_basis="raw_stored_bytes",
                size_bytes=len(dom),
            ),
            PreservedFile(
                file_id="file_02",
                original_path="cloakbrowser_snapshot_metadata.json",
                relative_packet_path="raw/04_cloakbrowser_snapshot_metadata.json",
                sha256=hashlib.sha256(metadata).hexdigest(),
                hash_basis="raw_stored_bytes",
                size_bytes=len(metadata),
            ),
        ],
        receipt_metadata=ReceiptMetadata(
            title="Google Ads Transparency fixture",
            generated_at="2026-07-31T01:02:03Z",
            summary="unit test packet",
            non_claims=["not source exhaustion"],
        ),
    )
    manifest_path = packet_dir / "manifest.json"
    manifest_path.write_text(
        packet.model_dump_json(indent=2), encoding="utf-8"
    )
    return packet_dir


def _project(packet_dir: Path):
    return build_google_ads_transparency_projection_from_packet_directory(
        packet_dir,
        expected_advertiser_name=ADVERTISER_NAME,
        expected_advertiser_id=ADVERTISER_ID,
        expected_region="US",
    )


def test_projection_is_advertiser_bound_partial_and_byte_deterministic(
    tmp_path: Path,
) -> None:
    packet_dir = _write_packet(tmp_path / "packet")

    first = _project(packet_dir)
    second = _project(packet_dir)

    assert google_ads_transparency_projection_json_text(
        first
    ) == google_ads_transparency_projection_json_text(second)
    assert first.advertiser.name == ADVERTISER_NAME
    assert first.advertiser.advertiser_id == ADVERTISER_ID
    assert first.advertiser.based_in == "United States"
    assert first.advertiser.verification_ui_observed is True
    assert first.source_evidence.rendered_card_position_denominator == 3
    assert first.source_evidence.observed_rendered_card_position_count == 3
    assert first.projection.status == "PARTIAL"
    assert first.projection.source_inventory_exhaustion_status == "NOT_PROVEN"
    assert first.projection.observed_distinct_creative_id_count == 2
    assert first.projection.repeated_creative_card_position_count == 1
    assert [row.creative_id for row in first.creative_inventory] == [
        CREATIVE_A,
        CREATIVE_B,
    ]
    assert first.creative_inventory[0].source_card_positions == [1, 2]
    assert first.creative_inventory[1].source_dom_order == 2


def test_wrong_source_family_fails_before_projection(tmp_path: Path) -> None:
    packet_dir = _write_packet(
        tmp_path / "packet", source_family="web_page"
    )

    with pytest.raises(ValueError, match="google_ads_source_family_mismatch"):
        _project(packet_dir)


def test_wrong_expected_advertiser_fails_at_identity_gate(
    tmp_path: Path,
) -> None:
    packet_dir = _write_packet(tmp_path / "packet")

    with pytest.raises(
        ValueError, match="google_ads_advertiser_name_not_observed"
    ):
        build_google_ads_transparency_projection_from_packet_directory(
            packet_dir,
            expected_advertiser_name="Different Company, LLC",
            expected_advertiser_id=ADVERTISER_ID,
            expected_region="US",
        )


def test_wrong_exact_advertiser_locator_fails_closed(tmp_path: Path) -> None:
    wrong_locator = (
        "https://adstransparency.google.com/advertiser/"
        f"{ADVERTISER_ID}?region=CA"
    )
    packet_dir = _write_packet(tmp_path / "packet", locator=wrong_locator)

    with pytest.raises(
        ValueError, match="google_ads_exact_advertiser_locator_mismatch"
    ):
        _project(packet_dir)


def test_dom_tamper_after_manifest_fails_hash_gate(tmp_path: Path) -> None:
    packet_dir = _write_packet(tmp_path / "packet")
    dom_path = packet_dir / "raw" / "01_cloakbrowser_rendered_dom.html"
    tampered = dom_path.read_bytes().replace(b"~3 ads", b"~4 ads")
    dom_path.write_bytes(tampered)

    with pytest.raises(
        ValueError, match="google_ads_preserved_sha256_mismatch"
    ):
        _project(packet_dir)


def test_cli_failure_does_not_write_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packet_dir = _write_packet(tmp_path / "packet")
    output = tmp_path / "projection.json"

    with pytest.raises(SystemExit) as exit_info:
        main(
            [
                "--packet",
                str(packet_dir),
                "--advertiser-name",
                "Different Company, LLC",
                "--advertiser-id",
                ADVERTISER_ID,
                "--region",
                "US",
                "--output",
                str(output),
            ]
        )

    assert exit_info.value.code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "google_ads_advertiser_name_not_observed" in captured.err
    assert "Traceback" not in captured.err
