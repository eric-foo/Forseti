"""Daemon-ready runner: project every committed IG reels-grid packet into its Silver record.

The seam-shaped CATCH-UP entrypoint for the IG reels-grid projection lane. The lane's
committed records have a REAL downstream consumer — the creator-profile spine's
``instagram_metric_seed`` walks ``derived/<pkt>/projection_ig_reels_grid/`` to build
creator metric seeds — so a committed grid packet without its projection record is
invisible to creator metrics. Until now the lane had two entrypoints, neither on the
seam: the operator-pointed ``project_ig_reels_grid_into_lake`` (no discovery) and the
Bronze-catalog proof path ``project_ig_reels_grid_from_bronze_catalog`` (discovers via
the generated catalog, skip-if-done keyed on RECORD EXISTENCE — so a projection policy
bump would never re-derive; that path remains the catalog plumbing proof, not the
cadence entrypoint). This runner independently scans committed availability and
derives for every packet whose current obligation is not yet acknowledged.

Pickup is the consumption seam (``data_lake.consumption``). The obligation snapshot is
policy-only: the raw packet is immutable (write-once), the projection is a pure
function of raw bytes + policy (no date-relative selection — the capture file's
``selection_policy_version`` is per-packet raw data carried in the output, not a
policy input), and no committed derived record is consumed. Skip-if-done keys on the
ACK: each derivation appends a fresh ULID sibling and the ack cites it; a crash
mid-derivation leaves an unreferenced sibling and NO ack, so the packet re-surfaces
and re-derives cleanly. Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

SURFACE GATE: the ``instagram_creator`` family is shared with the transcript/ASR,
deep-capture, and calls lanes, split by ``source_surface``. A picked-up packet whose
committed availability entry carries a known non-grid surface has no grid-projectable
content — the discovery outcome IS the completion evidence (cleaning-family
precedent), and a surface is immutable, so the packet is acknowledged with explicit
out-of-scope evidence rather than re-surfacing forever. Those packets remain fully
available to their own lanes' namespaces. Unknown family surfaces stay visible and
UNACKED as ``unsupported_surface`` (no open-world acks).

Failure stays loud and isolated per packet: a missing availability entry is a
``discovery_failed`` status; a verified-read/validation/projection raise is a
``derive_failed`` status; both leave the packet unacknowledged and re-surfacing every
run. An ack write failure surfaces as ``ack_failed``. Acked-and-unchanged packets emit
NO per-run status entries. Availability reconcile is the shared per-packet
fail-visible helper (``data_lake.consumption.reconcile_availability_per_packet``).

No-LLM zone (`runners/`): the projection is mechanical (JSON decode + row carry) —
this runner needs no transport, so ``--run`` IS the cadence entrypoint.
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
from harness_utils import generate_ulid
from source_capture.ig_reels_grid_projection import (
    CATCHUP_IG_REELS_GRID_RECORD_ID_PREFIX,
    IG_REELS_PROJECTION_CERTIFICATION,
    IG_REELS_PROJECTION_METHOD,
    IG_REELS_PROJECTION_VERSION,
    PROJECTION_IG_REELS_GRID_LANE,
    _CAPTURE_FILE_BASENAME,
    _DOM_TEXT_KEY_BY_METRIC,
    _JSON_KEY_BY_METRIC,
    _STATIC_VIEW_COUNT_NOT_APPLICABLE_REASON,
    _SURFACE_PREFERENCE,
    project_ig_reels_grid_into_lake,
)

# Seam ack namespace = the projection lane (contract rule: an ack namespace must be
# a lane declared in lane_registry.LANE_ROLES; exactly one derived projection record
# exists per derivation, and the ack's evidence cites it).
_ACK_NAMESPACE = PROJECTION_IG_REELS_GRID_LANE
_SEAM_CONSUMER = "ig_reels_grid_projection_catchup"
_SOURCE_FAMILY = "instagram_creator"
_IN_SCOPE_SURFACE = "ig_reels_grid_dom_passive_json"
# Catch-up records supersede earlier siblings of the same anchor via the projection
# lane's DECLARED derivation rank (projection_record_id_derivation_rank), consumed by
# the creator-metric seed's fail-closed sibling selection -- no longer via this
# prefix's lexical position (F-IGRC-001). The prefix value is single-sourced from the
# lane module and stays frozen: it is fingerprinted into obligation envelopes below.
_CATCHUP_RECORD_ID_PREFIX = CATCHUP_IG_REELS_GRID_RECORD_ID_PREFIX
# Shared-family surfaces owned by OTHER lanes (transcript/ASR audio, deep-capture
# audio, calls/momentum). Their packets carry no grid-projectable content; they are
# acknowledged out-of-scope (module doc) and stay available to their own lanes.
_KNOWN_OUT_OF_SCOPE_SURFACES = frozenset(
    {
        "ig_reels_audio",
        "ig_reels_deep_capture_render_audio",
        "ig_calls_browser_snapshot",
    }
)


def _packet_obligation() -> dict:
    """The cheap obligation snapshot: constant per policy version, enumerating every
    output-shaping pre-existing constant (F-FRAG-001 convention). Raw is immutable,
    the projection consumes no committed derived record, and nothing date-relative
    exists — so the policy constants are the lane's only re-trigger inputs.
    NON-RAISING by construction (pickup's obligation_fn aborts the whole loop on a
    raise)."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        "source_family": _SOURCE_FAMILY,
        "in_scope_surface": _IN_SCOPE_SURFACE,
        "known_out_of_scope_surfaces": sorted(_KNOWN_OUT_OF_SCOPE_SURFACES),
        "catchup_record_id_prefix": _CATCHUP_RECORD_ID_PREFIX,
        "projection_method": IG_REELS_PROJECTION_METHOD,
        "projection_version": IG_REELS_PROJECTION_VERSION,
        "projection_certification": IG_REELS_PROJECTION_CERTIFICATION,
        "capture_file_basename": _CAPTURE_FILE_BASENAME,
        "surface_preference": [
            [surface, rank] for surface, rank in sorted(_SURFACE_PREFERENCE.items())
        ],
        "dom_text_key_by_metric": [
            [metric, key] for metric, key in sorted(_DOM_TEXT_KEY_BY_METRIC.items())
        ],
        "json_key_by_metric": [
            [metric, key] for metric, key in sorted(_JSON_KEY_BY_METRIC.items())
        ],
        "static_view_count_rule": _STATIC_VIEW_COUNT_NOT_APPLICABLE_REASON,
    }


def _catchup_record_id() -> str:
    return f"{_CATCHUP_RECORD_ID_PREFIX}_{generate_ulid()}"


def pending_packets(
    *,
    data_root,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed family packet ids whose current projection obligation is not
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
    """The single daemon entrypoint: derive the grid projection for every committed
    family packet whose current obligation is unacknowledged, then acknowledge with
    the derivation as evidence.

    Known non-grid surfaces in the shared family are acknowledged with explicit
    out-of-scope evidence (module doc); unknown surfaces are visible
    ``unsupported_surface`` statuses, never acked. Per-packet failure isolation: a
    raise yields ``derive_failed`` and the batch continues. Acked-and-unchanged
    packets emit no status entries. Returns one status dict per processed packet.
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
            if surface not in _KNOWN_OUT_OF_SCOPE_SURFACES:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "unsupported_surface",
                        "source_surface": surface,
                        "error": "unrecognized instagram_creator surface for the grid projection",
                    }
                )
                continue
            # Shared-family packet owned by another lane: no grid-projectable
            # content, and a surface is immutable — the discovery outcome IS the
            # completion evidence (cleaning-family precedent).
            evidence = [
                {
                    "kind": "no_grid_projectable_content_for_surface",
                    "raw_anchor": packet_id,
                    "source_surface": surface,
                    "basis": "known_non_grid_instagram_creator_surface",
                }
            ]
            outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
            else:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "acked_no_projectable_content",
                        "source_surface": surface,
                    }
                )
            continue
        try:
            projection, derived_path = project_ig_reels_grid_into_lake(
                data_root=data_root, packet_id=packet_id, record_id=_catchup_record_id()
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
                "lane": PROJECTION_IG_REELS_GRID_LANE,
                "record_id": derived_path.name,
                "content_sha256": hashlib.sha256(derived_bytes).hexdigest(),
                "byte_count": len(derived_bytes),
            },
            {
                "kind": "projection_counts",
                "raw_anchor": packet_id,
                "row_count": len(projection.rows),
                "residual_count": len(projection.residuals),
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
                    "row_count": len(projection.rows),
                    "residual_count": len(projection.residuals),
                }
            )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IG reels-grid projection catch-up runner utilities."
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
        if entry["status"] not in {"derived", "acked_no_projectable_content"}:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
