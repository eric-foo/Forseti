"""Daemon-ready runner: derive Fragrantica Cleaning output for every committed packet.

The seam-shaped CATCH-UP entrypoint for the Fragrantica Cleaning lane. Until now the
audit pack + post-cleaned Silver records were written only when an operator pointed
``cleaning.fragrantica_lake.derive_fragrantica_cleaning_into_lake`` at one packet: the
lane had NO discovery, so a packet nobody pointed at never got its Cleaning records.
This runner independently scans committed availability and derives for every packet
whose current obligation is not yet acknowledged.

Pickup is the consumption seam (``data_lake.consumption``). The obligation snapshot is
policy-only: the raw packet is immutable (write-once), the Fragrantica projection is
rebuilt in memory from raw bodies (the committed ``projection_fragrantica`` records are
NOT consumed), and the cleaning packet's ECR ref is symbolic-by-convention (no committed
ECR content is read) — so the derivation has no growable derived-record inputs, and the
pre-existing policy constants (cleaning core, projection version, producer schema
versions) are the lane's only re-trigger inputs. Skip-if-done keys on the ACK: this
lane writes no record-set completion marker (audit + Silver are independent appends
with fresh ULIDs), so an unacknowledged fingerprint always derives a FRESH audit
sibling + fresh Silver records and the ack cites them; a crash mid-derivation leaves
unreferenced siblings and NO ack, so the packet re-surfaces and re-derives cleanly.
Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

SURFACE GATE: the ``fragrance_native_database`` family is shared with the basenotes and
parfumo cleaning lanes, split by ``source_surface``. A picked-up packet whose committed
availability entry carries a non-Fragrantica surface has no Fragrantica-cleanable
content — the discovery outcome IS the completion evidence (the IG runner's
grid-packet precedent), and a surface is immutable, so the packet is acknowledged with
explicit out-of-scope evidence rather than re-surfacing forever or being handed to the
wrong deriver. Those packets remain fully available to their own lanes' namespaces.

Failure stays loud and isolated per packet: a missing availability entry is a
``discovery_failed`` status; a verified-read/validation/derivation raise is a
``derive_failed`` status; both leave the packet unacknowledged and re-surfacing every
run. An ack write failure surfaces as ``ack_failed``. Acked-and-unchanged packets emit
NO per-run status entries. Per-packet availability reconcile failures surface as
``availability_reconcile_failed`` (the F-ECR-001 adjudicated shape) while healthy
packets still index and process.

No-LLM zone (`runners/`): the Cleaning derivation is mechanical (projection rebuild +
transform ledger) — this runner needs no transport, so ``--run`` IS the cadence
entrypoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cleaning.fragrantica_lake import (
    CLEANING_AUDIT_PACK_SCHEMA_VERSION,
    FRAGRANTICA_AUDIT_PACK_PRODUCER_SCHEMA_VERSION,
    FRAGRANTICA_CLEANING_AUDIT_LANE,
    FRAGRANTICA_CLEANING_METHOD_ID,
    FRAGRANTICA_REVIEW_VOTE_POLICY_VERSION,
    FRAGRANTICA_CLEANING_SILVER_LANE,
    FRAGRANTICA_SILVER_METRIC_PRODUCER_SCHEMA_VERSION,
    FRAGRANTICA_SILVER_PRODUCER_SCHEMA_VERSION,
    REVIEW_TEXT_NORMALIZATION_RULE,
    REVIEW_VOTE_CARRY_RULE,
    SILVER_VAULT_RECORD_SCHEMA_VERSION,
    _REVIEW_VOTE_METRIC_SPECS,
    derive_fragrantica_cleaning_into_lake,
)
from cleaning.models import CLEANING_CORE_VERSION
from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.root import DataLakeRootError
from source_capture.fragrantica_projection import (
    FRAGRANTICA_PROJECTION_CERTIFICATION,
    FRAGRANTICA_PROJECTION_METHOD,
    FRAGRANTICA_PROJECTION_VERSION,
    FRAGRANTICA_SOURCE_SURFACES,
)

# Seam ack namespace = the audit-pack lane (contract rule: an ack namespace must be
# a lane declared in lane_registry.LANE_ROLES; exactly one audit pack exists per
# derivation, and the ack's evidence cites it).
_ACK_NAMESPACE = FRAGRANTICA_CLEANING_AUDIT_LANE
_SEAM_CONSUMER = "fragrantica_cleaning_catchup"
_SOURCE_FAMILY = "fragrance_native_database"
_FRAGRANTICA_SURFACES = FRAGRANTICA_SOURCE_SURFACES
_KNOWN_OUT_OF_SCOPE_SURFACES = frozenset(
    {
        "basenotes_product_page_user_cleared_persistent_chrome_current_window",
        "parfumo_product_page_direct_http",
        "parfumo_product_page_chrome_extension_targeted_rendered_session",
    }
)


def _packet_obligation() -> dict:
    """The cheap obligation snapshot: constant per policy version. Raw is immutable,
    the projection is rebuilt from raw in memory, and no committed derived record is
    consumed — so no per-packet input enumeration exists, and the pre-existing policy
    constants are the only re-trigger inputs. NON-RAISING by construction (pickup's
    obligation_fn aborts the whole loop on a raise)."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        # Surface-gate policy (F-IGRC-002 convention): the gate decides derive vs
        # out-of-scope ack vs visible-unsupported, so reclassifying a surface must
        # re-fingerprint and re-surface previously acked packets.
        "source_family": _SOURCE_FAMILY,
        "in_scope_surfaces": sorted(_FRAGRANTICA_SURFACES),
        "known_out_of_scope_surfaces": sorted(_KNOWN_OUT_OF_SCOPE_SURFACES),
        "cleaning_core_version": CLEANING_CORE_VERSION,
        "projection_method": FRAGRANTICA_PROJECTION_METHOD,
        "projection_version": FRAGRANTICA_PROJECTION_VERSION,
        "projection_certification": FRAGRANTICA_PROJECTION_CERTIFICATION,
        "cleaning_audit_pack_schema_version": CLEANING_AUDIT_PACK_SCHEMA_VERSION,
        "audit_pack_schema_version": FRAGRANTICA_AUDIT_PACK_PRODUCER_SCHEMA_VERSION,
        "silver_vault_record_schema_version": SILVER_VAULT_RECORD_SCHEMA_VERSION,
        "silver_schema_version": FRAGRANTICA_SILVER_PRODUCER_SCHEMA_VERSION,
        "silver_metric_schema_version": FRAGRANTICA_SILVER_METRIC_PRODUCER_SCHEMA_VERSION,
        "cleaning_method_id": FRAGRANTICA_CLEANING_METHOD_ID,
        "review_text_normalization_rule": REVIEW_TEXT_NORMALIZATION_RULE,
        "review_vote_carry_rule": REVIEW_VOTE_CARRY_RULE,
        "review_vote_policy_version": FRAGRANTICA_REVIEW_VOTE_POLICY_VERSION,
        "review_vote_metric_specs": [list(spec) for spec in _REVIEW_VOTE_METRIC_SPECS],
    }


def pending_packets(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed family packet ids whose current Cleaning obligation is not
    acknowledged (all surfaces; out-of-scope surfaces leave the backlog after
    their first-run out-of-scope ack). Scheduler gate helper: no derivation and
    no writes beyond the availability reconcile."""
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
    """The single daemon entrypoint: derive the Fragrantica Cleaning audit pack +
    post-cleaned Silver for every committed family packet whose current obligation
    is unacknowledged, then acknowledge with the derivation as evidence.

    Non-Fragrantica surfaces in the shared family are acknowledged with explicit
    out-of-scope evidence (module doc). Per-packet failure isolation: a raise
    yields ``derive_failed`` and the batch continues; the packet stays
    unacknowledged and re-surfaces every run. Acked-and-unchanged packets emit no
    status entries. Returns one status dict per processed packet.
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
        if surface not in _FRAGRANTICA_SURFACES:
            if surface not in _KNOWN_OUT_OF_SCOPE_SURFACES:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "unsupported_surface",
                        "source_surface": surface,
                        "error": "unrecognized fragrance_native_database surface for Fragrantica Cleaning",
                    }
                )
                continue
            # Shared-family packet owned by another cleaning lane: no
            # Fragrantica-cleanable content, and a surface is immutable — the
            # discovery outcome IS the completion evidence (IG grid precedent).
            evidence = [
                {
                    "kind": "no_cleanable_content_for_surface",
                    "raw_anchor": packet_id,
                    "source_surface": surface,
                    "basis": "known_non_fragrantica_source_surface",
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
            derived = derive_fragrantica_cleaning_into_lake(data_root=data_root, packet_id=packet_id)
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
                "lane": FRAGRANTICA_CLEANING_AUDIT_LANE,
                "record_id": audit_record_id,
                "content_hash": derived.audit_record["content_hash"],
            },
            {
                "kind": "silver_records",
                "raw_anchor": packet_id,
                "lane": FRAGRANTICA_CLEANING_SILVER_LANE,
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
    parser = argparse.ArgumentParser(description="Fragrantica Cleaning catch-up runner utilities.")
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
