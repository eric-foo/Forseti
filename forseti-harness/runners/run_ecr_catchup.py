"""Daemon-ready runner: derive source-side ECR postures for every committed packet.

The seam-shaped CATCH-UP entrypoint for the ECR lane. Until now ECR record sets were
written only when an operator pointed ``ecr.lake.derive_ecr_into_lake`` at one packet
(smoke runner / pilot flows): the lane had NO discovery, so a packet nobody pointed at
never got its ECR records. This runner independently scans committed availability and
derives the four-posture sibling set for every packet whose current obligation is not
yet acknowledged.

Pickup is the consumption seam (``data_lake.consumption``): the obligation snapshot is
{schema, consumer, deriver_version} ONLY — the raw packet is immutable (write-once), the
derivers are pure over its manifest, and ECR consumes no growable derived records, so
the deriver policy token is the lane's only re-trigger input. A committed packet is
therefore picked up exactly once per policy version. Skip-if-done keys on the ACK, not
on existing ``ecr_set`` markers: a pre-seam sibling set carries no deriver-version
attribution, so an unacknowledged fingerprint always derives a FRESH sibling set
(append-only re-derive is the lane's documented semantic) and the ack cites that set.
Consequence, stated: the first catch-up run over a lake holding pre-seam ECR sets
re-derives those packets once — benign sibling duplication, never an overwrite.
Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

Failure stays loud and isolated per packet: a packet whose verified read, manifest
validation, or derivation raises yields a ``derive_failed`` status, is never
acknowledged, and re-surfaces every run. An ack write failure surfaces as
``ack_failed``. Acked-and-unchanged packets emit NO per-run status entries; the
durable ack records under ``acknowledgements/`` are the completion facts.

No-LLM zone (`runners/`): the ECR derivers are pure functions over the packet
manifest — this runner needs no transport, so ``--run`` IS the cadence entrypoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.root import DataLakeRootError
from ecr.deriver import ECR_DERIVER_VERSION
from ecr.lake import ECR_COMPLETION_LANE, derive_ecr_into_lake

# Seam ack namespace = the ECR derivation-completion lane (contract rule: an ack
# namespace must be a lane declared in lane_registry.LANE_ROLES; ecr_set is the
# lane whose completion marker the ack's evidence cites).
_ACK_NAMESPACE = ECR_COMPLETION_LANE
_SEAM_CONSUMER = "ecr_catchup"


def _packet_obligation() -> dict:
    """The cheap obligation snapshot: constant per policy version. Raw is immutable
    and ECR reads no derived records, so no per-packet input enumeration exists —
    a new committed packet surfaces as a new unacknowledged anchor, and a deriver
    policy change re-fingerprints (and so re-surfaces) every anchor. NON-RAISING
    by construction (pickup's obligation_fn aborts the whole loop on a raise)."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        "deriver_version": ECR_DERIVER_VERSION,
    }


def pending_packets(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed packet ids whose current ECR obligation is not acknowledged.
    Scheduler gate helper: no derivation and no writes beyond the availability
    reconcile."""
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
    """The single daemon entrypoint: derive the ECR sibling set for every committed
    packet whose current obligation is unacknowledged, then acknowledge with the
    completed set as evidence.

    Per-packet failure isolation: a verified-read/validation/derivation raise yields
    a ``derive_failed`` status and the batch continues; the packet stays
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
        reconcile=False,
        scope_packet_ids=scope_packet_ids,
    ):
        packet_id = item.raw_anchor
        try:
            paths = derive_ecr_into_lake(data_root=data_root, packet_id=packet_id)
        except Exception as exc:  # noqa: BLE001 - per-packet failure isolation (daemon-ready)
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "derive_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
            continue
        record_id = next(iter(paths.values())).name
        evidence = [
            {
                "kind": "record_set_complete",
                "raw_anchor": packet_id,
                "completion_lane": ECR_COMPLETION_LANE,
                "record_id": record_id,
            }
        ]
        outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
        if outcome != "acked":
            results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
        else:
            results.append({"packet_id": packet_id, "status": "derived", "record_id": record_id})
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ECR catch-up runner utilities.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the count of committed packets whose ECR obligation is unacknowledged.",
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
        if entry["status"] != "derived":
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
