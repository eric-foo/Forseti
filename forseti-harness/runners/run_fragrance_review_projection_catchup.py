"""Daemon-ready runner: project every committed fragrance-review packet into coverage.

The seam-shaped CATCH-UP entrypoint for the fragrance-review projection lane — the
first projection-family lane on the consumption seam. Until now the coverage
projection was written only when an operator pointed
``source_capture.fragrance_review_lake.project_fragrance_review_into_lake`` at one
packet: the lane had NO discovery, so a teed packet nobody pointed at never got its
derived coverage record. This runner independently scans committed availability and
derives for every packet whose current obligation is not yet acknowledged.

Pickup is the consumption seam (``data_lake.consumption``). The obligation snapshot is
policy-only: the raw packet is immutable (write-once), the coverage projection is
rebuilt in memory from the preserved widget bodies, and no committed derived record is
consumed — so the derivation has no growable derived-record inputs, and the coverage
method/version/certification plus the named selection-policy constants are the lane's
only re-trigger inputs. Skip-if-done keys on the ACK: each derivation appends a fresh
ULID sibling and the ack cites it; a crash mid-derivation leaves an unreferenced
sibling and NO ack, so the packet re-surfaces and re-derives cleanly.
Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

DETERMINISM (the lane's one date-relative input): the coverage selection policy is
recency-windowed and ``build_fragrance_review_coverage`` defaults its ``as_of_date``
to ``date.today()`` — acceptable for an operator run, wrong for a catch-up whose
derived bytes must be a pure function of (immutable raw, policy). This runner pins
``as_of_date`` to the packet's own capture date via
``fragrance_review_lake.capture_as_of_date`` (manifest slice ``timing.capture_time``,
hash-verified against the availability entry), records the resolved date in the ack
evidence (the coverage receipt does not carry it), and declares the rule as the
``as_of_policy`` envelope token. A packet whose capture time cannot be resolved is a
loud per-packet ``derive_failed`` — never a silent ``today()`` fallback.

SURFACE GATE: the ``fragrance_review`` family has exactly one known surface (the
rendered-widget review tee). There is no sibling lane owning other surfaces, so there
is no known-out-of-scope ack path: any other surface is an unrecognized family member
and surfaces as a visible ``unsupported_surface`` status, never an ack (no open-world
acking). Classifying a future second surface is a deliberate policy change here.

Failure stays loud and isolated per packet: a missing availability entry is a
``discovery_failed`` status; a verified-read/resolution/derivation raise is a
``derive_failed`` status; both leave the packet unacknowledged and re-surfacing every
run. An ack write failure surfaces as ``ack_failed``. Acked-and-unchanged packets emit
NO per-run status entries. Per-packet availability reconcile failures surface as
``availability_reconcile_failed`` (the F-ECR-001 adjudicated shape) while healthy
packets still index and process.

No-LLM zone (`runners/`): the projection is mechanical (JSON decode + coverage build)
— this runner needs no transport, so ``--run`` IS the cadence entrypoint.
"""

from __future__ import annotations

import argparse
import hashlib
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
from source_capture.fragrance_review_coverage import (
    FRAGRANCE_REVIEW_COVERAGE_CERTIFICATION,
    FRAGRANCE_REVIEW_COVERAGE_METHOD,
    FRAGRANCE_REVIEW_COVERAGE_VERSION,
    FRAGRANCE_REVIEW_SELECTION_LENGTH_MIN_WORDS,
    FRAGRANCE_REVIEW_SELECTION_REASON_PRIORITY,
    FRAGRANCE_REVIEW_SELECTION_RECENT_MONTHS,
)
from source_capture.fragrance_review_lake import (
    FRAGRANCE_REVIEW_SOURCE_FAMILY,
    FRAGRANCE_REVIEW_SOURCE_SURFACE,
    PROJECTION_FRAGRANCE_REVIEW_LANE,
    capture_as_of_date,
    project_fragrance_review_into_lake,
)

# Seam ack namespace = the projection lane (contract rule: an ack namespace must be
# a lane declared in lane_registry.LANE_ROLES; exactly one derived coverage record
# exists per derivation, and the ack's evidence cites it).
_ACK_NAMESPACE = PROJECTION_FRAGRANCE_REVIEW_LANE
_SEAM_CONSUMER = "fragrance_review_projection_catchup"
_SOURCE_FAMILY = FRAGRANCE_REVIEW_SOURCE_FAMILY
_IN_SCOPE_SURFACE = FRAGRANCE_REVIEW_SOURCE_SURFACE
# The deterministic as-of rule declared to the seam (module doc): the projection is
# re-derived as of the packet's own capture date, resolved via capture_as_of_date.
_AS_OF_POLICY = "packet_capture_date"


def _packet_obligation() -> dict:
    """The cheap obligation snapshot: constant per policy version. Raw is immutable,
    the projection is rebuilt from raw in memory, and no committed derived record is
    consumed — so no per-packet input enumeration exists, and the coverage policy
    constants are the only re-trigger inputs. The per-packet as-of DATE is derived
    data (immutable raw → date), not policy, so only the resolution RULE is
    enumerated. NON-RAISING by construction (pickup's obligation_fn aborts the whole
    loop on a raise)."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        # Surface-gate policy (F-IGRC-002 convention): the gate decides derive vs
        # visible-unsupported, so reclassifying the surface must re-fingerprint
        # and re-surface previously acked packets.
        "source_family": _SOURCE_FAMILY,
        "in_scope_surface": _IN_SCOPE_SURFACE,
        "coverage_method": FRAGRANCE_REVIEW_COVERAGE_METHOD,
        "coverage_version": FRAGRANCE_REVIEW_COVERAGE_VERSION,
        "coverage_certification": FRAGRANCE_REVIEW_COVERAGE_CERTIFICATION,
        "selection_recent_months": FRAGRANCE_REVIEW_SELECTION_RECENT_MONTHS,
        "selection_length_min_words": FRAGRANCE_REVIEW_SELECTION_LENGTH_MIN_WORDS,
        "selection_reason_priority": [
            [reason, rank]
            for reason, rank in sorted(FRAGRANCE_REVIEW_SELECTION_REASON_PRIORITY.items())
        ],
        "max_selected_rows": None,
        "as_of_policy": _AS_OF_POLICY,
    }


def _verified_manifest(data_root, entry: dict) -> dict:
    """Read the committed manifest named by the availability entry, verified against
    the entry's recorded sha256 — the cheap read half for as-of resolution (the heavy
    body-verifying read stays inside the projection's ``load_raw_packet``)."""
    relpath = entry.get("manifest_relpath")
    expected = entry.get("manifest_sha256")
    if not isinstance(relpath, str) or not isinstance(expected, str):
        raise DataLakeRootError("availability entry is missing manifest_relpath/manifest_sha256")
    manifest_path = data_root.path / relpath
    manifest_bytes = manifest_path.read_bytes()
    actual = hashlib.sha256(manifest_bytes).hexdigest()
    if actual != expected:
        raise DataLakeRootError(
            f"manifest bytes do not match the availability entry sha256 for {relpath} "
            f"(expected {expected}, got {actual})"
        )
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise DataLakeRootError(f"raw manifest is not a JSON object: {relpath}")
    return manifest


def pending_packets(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed family packet ids whose current projection obligation is not
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
    """The single daemon entrypoint: derive the coverage projection for every
    committed family packet whose current obligation is unacknowledged, then
    acknowledge with the derivation as evidence.

    Per-packet failure isolation: a raise yields ``derive_failed`` and the batch
    continues; the packet stays unacknowledged and re-surfaces every run. An
    unrecognized family surface is a visible ``unsupported_surface`` status, never
    an ack (module doc). Acked-and-unchanged packets emit no status entries.
    Returns one status dict per processed packet.
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
        if surface != _IN_SCOPE_SURFACE:
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "unsupported_surface",
                    "source_surface": surface,
                    "error": "unrecognized fragrance_review surface for the coverage projection",
                }
            )
            continue
        try:
            manifest = _verified_manifest(data_root, entry)
            as_of = capture_as_of_date(manifest)
            receipt, derived_path = project_fragrance_review_into_lake(
                data_root=data_root, packet_id=packet_id, as_of_date=as_of
            )
        except Exception as exc:  # noqa: BLE001 - per-packet failure isolation (daemon-ready)
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "derive_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
            continue
        derived_bytes = derived_path.read_bytes()
        evidence = [
            {
                "kind": "derived_record",
                "raw_anchor": packet_id,
                "lane": PROJECTION_FRAGRANCE_REVIEW_LANE,
                "record_id": derived_path.name,
                "content_sha256": hashlib.sha256(derived_bytes).hexdigest(),
                "byte_count": len(derived_bytes),
            },
            {
                # The coverage receipt does not record the as-of it used; the ack
                # is the audit trail for the deterministic resolution (module doc).
                "kind": "as_of_resolution",
                "raw_anchor": packet_id,
                "as_of_policy": _AS_OF_POLICY,
                "as_of_date": as_of.isoformat(),
            },
            {
                "kind": "coverage_counts",
                "raw_anchor": packet_id,
                "row_count": len(receipt.rows),
                "selected_row_count": len(receipt.selected_row_ids),
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
                    "derived_record_id": derived_path.name,
                    "as_of_date": as_of.isoformat(),
                    "row_count": len(receipt.rows),
                    "selected_row_count": len(receipt.selected_row_ids),
                }
            )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fragrance-review projection catch-up runner utilities."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the count of committed family packets whose projection obligation is unacknowledged.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the catch-up: project + acknowledge every unacknowledged packet.",
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
