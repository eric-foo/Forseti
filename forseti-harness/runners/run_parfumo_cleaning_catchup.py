"""Daemon-ready runner: derive Parfumo Cleaning output for every committed packet.

The seam-shaped CATCH-UP entrypoint for the Parfumo Cleaning lane, mirroring the
adjudicated Fragrantica catch-up (`run_fragrantica_cleaning_catchup`, findings
F-FRAG-001/002 closed) with Parfumo constants. Until now the audit pack +
post-cleaned Silver records were written only when an operator pointed
``cleaning.parfumo_lake.derive_parfumo_cleaning_into_lake`` at one packet: the lane
had NO discovery. This runner independently scans committed availability and derives
for every packet whose current obligation is not yet acknowledged.

Pickup is the consumption seam (``data_lake.consumption``). The obligation snapshot
is policy-only: the raw packet is immutable (write-once), the Parfumo projection is
rebuilt in memory from raw bodies (committed ``projection_parfumo`` records are NOT
consumed), and the cleaning packet's ECR ref is symbolic-by-convention — so the
derivation has no growable derived-record inputs, and the envelope enumerates EVERY
output-shaping pre-existing constant (the F-FRAG-001 adjudicated convention).
Skip-if-done keys on the ACK: this lane writes no record-set completion marker
(audit + Silver are independent appends with fresh ULIDs), so an unacknowledged
fingerprint always derives a FRESH audit sibling + Silver records and the ack cites
them; a crash mid-derivation leaves unreferenced siblings and NO ack, so the packet
re-surfaces and re-derives cleanly.
Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

SURFACE GATE (the F-FRAG-002 adjudicated allowlist convention): the
``fragrance_native_database`` family is shared with the fragrantica and basenotes
cleaning lanes, split by ``source_surface``. Parfumo owns TWO in-scope surfaces
(direct HTTP + chrome-extension targeted rendered; the lake adapter passes the
packet's surface through to the cleaning builder). KNOWN other-lane surfaces are
acknowledged with explicit out-of-scope evidence; UNKNOWN surfaces surface as a
visible ``unsupported_surface`` status, are never acknowledged, and re-surface every
run until deliberately classified — never an open-world ack that could pre-close a
future surface.

Failure stays loud and isolated per packet: a missing availability entry is a
``discovery_failed`` status; a verified-read/validation/derivation raise is a
``derive_failed`` status; both leave the packet unacknowledged and re-surfacing every
run. The one narrow exception: a zero-``handles`` ``CleaningPacket`` validation
failure whose direct-HTTP packet manifest records a source-side access failure
(e.g. a Cloudflare/anti-bot HTTP block) is an honest non-cleanable outcome, not a
parser bug, and is acknowledged with explicit
``no_cleanable_content_for_blocked_capture`` evidence naming the recorded access
posture; any other zero-``handles`` shape still raises ``derive_failed`` unchanged.
An ack write failure surfaces as ``ack_failed``.
Acked-and-unchanged packets emit NO per-run status entries. Per-packet availability
reconcile failures surface as ``availability_reconcile_failed`` (the F-ECR-001
adjudicated shape) while healthy packets still index and process.

No-LLM zone (`runners/`): the Cleaning derivation is mechanical — this runner needs
no transport, so ``--run`` IS the cadence entrypoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError

from cleaning.models import CLEANING_CORE_VERSION
from cleaning.parfumo import PARFUMO_RATING_CARRY_RULE
from cleaning.parfumo_lake import (
    CLEANING_AUDIT_PACK_SCHEMA_VERSION,
    PARFUMO_AUDIT_PACK_PRODUCER_SCHEMA_VERSION,
    PARFUMO_CLEANING_AUDIT_LANE,
    PARFUMO_CLEANING_METHOD_ID,
    PARFUMO_CLEANING_SILVER_LANE,
    PARFUMO_RATING_METRIC_ABSENT_RESIDUAL,
    PARFUMO_SILVER_METRIC_PRODUCER_SCHEMA_VERSION,
    PARFUMO_SILVER_PRODUCER_SCHEMA_VERSION,
    SILVER_VAULT_RECORD_SCHEMA_VERSION,
    TEXT_NORMALIZATION_RULE,
    _REVIEW_RATING_METRIC_SPECS,
    derive_parfumo_cleaning_into_lake,
)
from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.root import DataLakeRootError
from source_capture.fragrantica_projection import FRAGRANTICA_SOURCE_SURFACES
from source_capture.models import SourceCapturePacket, VisibleFactStatus
from source_capture.parfumo_projection import (
    PARFUMO_DIRECT_HTTP_SOURCE_SURFACE,
    PARFUMO_PROJECTION_CERTIFICATION,
    PARFUMO_PROJECTION_METHOD,
    PARFUMO_PROJECTION_VERSION,
    PARFUMO_TARGETED_RENDERED_SOURCE_SURFACE,
)

# Seam ack namespace = the audit-pack lane (contract rule: an ack namespace must be
# a lane declared in lane_registry.LANE_ROLES; exactly one audit pack exists per
# derivation, and the ack's evidence cites it).
_ACK_NAMESPACE = PARFUMO_CLEANING_AUDIT_LANE
_SEAM_CONSUMER = "parfumo_cleaning_catchup"
_SOURCE_FAMILY = "fragrance_native_database"
_PARFUMO_SURFACES = frozenset(
    {
        PARFUMO_DIRECT_HTTP_SOURCE_SURFACE,
        PARFUMO_TARGETED_RENDERED_SOURCE_SURFACE,
    }
)
_KNOWN_OUT_OF_SCOPE_SURFACES = FRAGRANTICA_SOURCE_SURFACES | frozenset(
    {"basenotes_product_page_user_cleared_persistent_chrome_current_window"}
)
# Producer convention written by runners/run_source_capture_http_packet.py onto
# access_posture for any non-2xx direct-HTTP response (e.g. a Cloudflare/anti-bot
# 403 block): "direct_http access_failed with HTTP {status} {reason}; response
# body preserved". Distinguishes an honest source-side block (this packet class
# genuinely has nothing to clean) from a real extraction bug on a real page.
_BLOCKED_CAPTURE_ACCESS_POSTURE_PREFIX = "direct_http access_failed with HTTP "


def _is_zero_handles_validation_error(exc: ValidationError) -> bool:
    """True only for the exact CleaningPacket.handles too_short shape -- never a
    broader match that could absorb an unrelated validation failure."""
    errors = exc.errors()
    if len(errors) != 1:
        return False
    error = errors[0]
    return error.get("type") == "too_short" and error.get("loc") == ("handles",)


def _blocked_capture_evidence_or_none(
    *, data_root, packet_id: str, surface: str
) -> dict | None:
    """Re-read the committed packet manifest and return blocked-capture ack
    evidence when a direct-HTTP packet's access_posture confirms a recorded
    source-side access failure, else None. Any re-read failure returns None
    (never acks on an uncertain classification)."""
    if surface != PARFUMO_DIRECT_HTTP_SOURCE_SURFACE:
        return None
    try:
        loaded = data_root.load_raw_packet(packet_id)
        packet = SourceCapturePacket.model_validate(loaded.manifest)
    except Exception:  # noqa: BLE001 - classification-only re-read; never surfaced as the cause
        return None
    if packet.source_surface != PARFUMO_DIRECT_HTTP_SOURCE_SURFACE:
        return None
    access_posture = packet.access_posture
    if access_posture.status != VisibleFactStatus.KNOWN:
        return None
    if access_posture.value is None or not access_posture.value.startswith(
        _BLOCKED_CAPTURE_ACCESS_POSTURE_PREFIX
    ):
        return None
    return {
        "kind": "no_cleanable_content_for_blocked_capture",
        "raw_anchor": packet_id,
        "source_surface": surface,
        "basis": access_posture.value,
    }


def _packet_obligation() -> dict:
    """The cheap obligation snapshot: constant per policy version, enumerating every
    output-shaping pre-existing constant (F-FRAG-001 convention). NON-RAISING by
    construction (pickup's obligation_fn aborts the whole loop on a raise)."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        # Surface-gate policy (F-IGRC-002 convention): the gate decides derive vs
        # out-of-scope ack vs visible-unsupported, so reclassifying a surface must
        # re-fingerprint and re-surface previously acked packets.
        "source_family": _SOURCE_FAMILY,
        "in_scope_surfaces": sorted(_PARFUMO_SURFACES),
        "known_out_of_scope_surfaces": sorted(_KNOWN_OUT_OF_SCOPE_SURFACES),
        "cleaning_core_version": CLEANING_CORE_VERSION,
        "projection_method": PARFUMO_PROJECTION_METHOD,
        "projection_version": PARFUMO_PROJECTION_VERSION,
        "projection_certification": PARFUMO_PROJECTION_CERTIFICATION,
        "cleaning_audit_pack_schema_version": CLEANING_AUDIT_PACK_SCHEMA_VERSION,
        "audit_pack_schema_version": PARFUMO_AUDIT_PACK_PRODUCER_SCHEMA_VERSION,
        "silver_vault_record_schema_version": SILVER_VAULT_RECORD_SCHEMA_VERSION,
        "silver_schema_version": PARFUMO_SILVER_PRODUCER_SCHEMA_VERSION,
        "silver_metric_schema_version": PARFUMO_SILVER_METRIC_PRODUCER_SCHEMA_VERSION,
        "cleaning_method_id": PARFUMO_CLEANING_METHOD_ID,
        "text_normalization_rule": TEXT_NORMALIZATION_RULE,
        "rating_carry_rule": PARFUMO_RATING_CARRY_RULE,
        "rating_metric_absent_residual": PARFUMO_RATING_METRIC_ABSENT_RESIDUAL,
        "review_rating_metric_specs": [list(spec) for spec in _REVIEW_RATING_METRIC_SPECS],
    }


def pending_packets(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed family packet ids whose current Cleaning obligation is not
    acknowledged. Scheduler gate helper: no derivation and no writes beyond the
    availability reconcile."""
    if reconcile_availability:
        failures = reconcile_availability_per_packet(
            data_root, scope_packet_ids=scope_packet_ids
        )
        if failures:
            first = failures[0]
            raise DataLakeRootError(
                "availability reconcile failed before pending check: "
                f"{first['packet_id']}: {first['error']}"
            )
    return [
        item.raw_anchor
        for item in pickup(
            data_root,
            ack_namespace=_ACK_NAMESPACE,
            obligation_fn=lambda _pid: _packet_obligation(),
            source_family=_SOURCE_FAMILY,
            reconcile=False,
            scope_packet_ids=scope_packet_ids,
        )
    ]


def run_catchup(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[dict]:
    """The single daemon entrypoint: derive the Parfumo Cleaning audit pack +
    post-cleaned Silver for every committed family packet (both Parfumo surfaces)
    whose current obligation is unacknowledged, then acknowledge with the
    derivation as evidence.

    Known other-lane surfaces are acknowledged with explicit out-of-scope evidence;
    unknown surfaces stay visible and unacknowledged (module doc). Per-packet
    failure isolation: a raise yields ``derive_failed`` and the batch continues.
    Acked-and-unchanged packets emit no status entries. Returns one status dict per
    processed packet.
    """
    results: list[dict] = []
    # Visible reconcile opt-out per the seam contract: this runner reconciles
    # ITSELF first, per packet, so one corrupt manifest becomes a visible
    # availability_reconcile_failed status while healthy packets still index
    # and process — instead of pickup's whole-batch fail-loud default reconcile.
    if reconcile_availability:
        results.extend(
            reconcile_availability_per_packet(
                data_root, scope_packet_ids=scope_packet_ids
            )
        )
    for item in pickup(
        data_root,
        ack_namespace=_ACK_NAMESPACE,
        obligation_fn=lambda _pid: _packet_obligation(),
        source_family=_SOURCE_FAMILY,
        reconcile=False,
        scope_packet_ids=scope_packet_ids,
    ):
        packet_id = item.raw_anchor
        entry = data_root.read_availability(packet_id)
        if entry is None:
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "discovery_failed",
                    "error": "availability entry missing after reconcile",
                }
            )
            continue
        surface = entry.get("source_surface")
        if surface not in _PARFUMO_SURFACES:
            if surface not in _KNOWN_OUT_OF_SCOPE_SURFACES:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "unsupported_surface",
                        "source_surface": surface,
                        "error": "unrecognized fragrance_native_database surface for Parfumo Cleaning",
                    }
                )
                continue
            # Shared-family packet owned by another cleaning lane: no
            # Parfumo-cleanable content, and a surface is immutable — the
            # discovery outcome IS the completion evidence (IG grid precedent).
            evidence = [
                {
                    "kind": "no_cleanable_content_for_surface",
                    "raw_anchor": packet_id,
                    "source_surface": surface,
                    "basis": "known_non_parfumo_source_surface",
                }
            ]
            outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
            else:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "acked_no_cleanable_content",
                        "source_surface": surface,
                    }
                )
            continue
        try:
            derived = derive_parfumo_cleaning_into_lake(data_root=data_root, packet_id=packet_id)
        except ValidationError as exc:
            blocked_evidence = None
            if _is_zero_handles_validation_error(exc):
                blocked_evidence = _blocked_capture_evidence_or_none(
                    data_root=data_root, packet_id=packet_id, surface=surface
                )
            if blocked_evidence is None:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "derive_failed",
                        "error": f"{type(exc).__name__}: {exc}"[:200],
                    }
                )
                continue
            # Honest zero-handle outcome: the capture is a recorded source-side
            # access failure (e.g. a Cloudflare/anti-bot block), not a parser bug --
            # a surface is immutable, so the discovery + access-posture evidence IS
            # the completion evidence (mirrors the known-out-of-scope-surface ack
            # above).
            outcome = ack_packet(data_root, item, [blocked_evidence], ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
            else:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "acked_no_cleanable_content",
                        "source_surface": surface,
                    }
                )
            continue
        except Exception as exc:  # noqa: BLE001 - per-packet failure isolation (daemon-ready)
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "derive_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
            continue
        audit_record_id = derived.audit_record["record_id"]
        evidence = [
            {
                "kind": "derived_record",
                "raw_anchor": packet_id,
                "lane": PARFUMO_CLEANING_AUDIT_LANE,
                "record_id": audit_record_id,
                "content_hash": derived.audit_record["content_hash"],
            },
            {
                "kind": "silver_records",
                "raw_anchor": packet_id,
                "lane": PARFUMO_CLEANING_SILVER_LANE,
                "record_ids": [record["record_id"] for record in derived.silver_records],
                "count": len(derived.silver_records),
            },
        ]
        outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
        if outcome != "acked":
            results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
        else:
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "derived",
                    "audit_record_id": audit_record_id,
                    "silver_count": len(derived.silver_records),
                }
            )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parfumo Cleaning catch-up runner utilities.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the count of committed family packets whose Cleaning obligation is unacknowledged.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the catch-up: derive + acknowledge every unacknowledged packet.",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Forseti data lake root. Defaults to FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.check == args.run:
        parser.exit(status=2, message="choose exactly one of --check or --run\n")

    from data_lake.root import DataLakeRoot

    try:
        data_root = DataLakeRoot.resolve(explicit=args.data_root)
    except Exception as exc:  # noqa: BLE001 - CLI must surface root resolution failures
        parser.exit(status=2, message=f"data root required: {type(exc).__name__}: {exc}\n")
    if args.check:
        print(len(pending_packets(data_root=data_root)))
        return 0
    failures = 0
    for entry in run_catchup(data_root=data_root):
        print(json.dumps(entry, ensure_ascii=False, sort_keys=True))
        if entry["status"] not in {"derived", "acked_no_cleanable_content"}:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
