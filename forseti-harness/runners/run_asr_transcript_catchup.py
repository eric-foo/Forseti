"""Daemon-ready runner: transcribe every committed, untranscribed audio packet.

The seam-shaped CATCH-UP entrypoint for the transcript_asr lane. The ASR writers
(``source_capture/transcript/{asr_packet,ig_reels_audio_packet}.py``) fuse capture
and transcription — an audio packet whose transcription crashed mid-write, or that
was committed by any path without its transcript, never gets one: the lane had no
discovery. This runner independently scans committed availability across BOTH audio
families (YouTube ``youtube_audio`` and IG ``ig_reels_audio``) and derives the
transcript_asr record for every packet whose current obligation is not acknowledged,
using the injected NON-API local transcriber (faster-whisper via
``source_capture.transcript.audio_asr``; the runner itself imports no ASR library).

Pickup is the consumption seam (``data_lake.consumption``). The obligation snapshot
is policy-only: the raw audio is immutable, no committed derived record is consumed,
and the transcriber policy (tool/model/compute/decode params) is CLI-injected and
enumerated in the envelope — a model change re-fingerprints and re-surfaces every
packet (the record id embeds the model, so re-derivation lands a NEW record, never
an append-only collision). Skip-if-done keys on the ACK; a pre-existing
CURRENT-policy transcript (capture-time fusion or a crash between record and ack)
is acknowledged by citation (``acked_existing_transcript``) — that is same-policy
crash recovery, not an old-policy record satisfying a new-policy fingerprint.

BLOCK-DON'T-BURN: a failed transcription writes NO record and NO ack — the
deterministic model+audio record id is append-only, and committing an environment
failure (model missing, decode error) would permanently block retry under the same
policy. The packet surfaces as a loud ``derive_failed`` and re-surfaces every run.
``no_speech`` (the VAD gate found no speech) is an honest completion and is acked.

SURFACE GATES (F-FRAG-002 shape, F-IGRC-002 fingerprinting): per family, the known
non-audio surfaces are acked out-of-scope with explicit evidence; unknown surfaces
stay visible and UNACKED as ``unsupported_surface``. Deep-capture audio stays out
of the seam by frozen decision (its transcripts are deep-capture record sets).

Failure stays loud and isolated per packet; availability reconcile is the shared
per-packet fail-visible helper. Acked-and-unchanged packets emit NO status entries.

ASR COST GATE: ``--run`` executes local ASR compute (owner-operated cadence); no
network and no API spend. ``--check`` counts pending work without loading audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.consumption import (
    PickupItem,
    append_ack,
    is_acknowledged,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.root import DataLakeRootError
from source_capture.transcript.asr_packet import (
    asr_record_id,
    transcribe_committed_audio_packet,
)
from source_capture.transcript.ig_reels_audio_packet import (
    ig_asr_record_id,
    transcribe_committed_ig_audio_packet,
)

# Seam ack namespace = the transcript lane (contract rule: an ack namespace must be
# a lane declared in lane_registry.LANE_ROLES; the ack's evidence cites the
# transcript record it committed or found).
_ACK_NAMESPACE = "transcript_asr"
_SEAM_CONSUMER = "asr_transcript_catchup"
_TRANSCRIPT_LANE = "transcript_asr"
_TRANSCRIPT_SET_LANE = "transcript_asr__set"

# Per-family seam configuration. Both audio families share the consumer, the
# transcriber policy, and the ack namespace; they differ in surface gates, the
# committed-packet transcription path, and the record-id rule (IG bounds the
# model token). Known out-of-scope surfaces are owned by other lanes and are
# acked with explicit evidence; unknown surfaces stay visible and unacked.
_FAMILY_CONFIGS = (
    {
        "source_family": "youtube",
        "in_scope_surface": "youtube_audio",
        "known_out_of_scope_surfaces": frozenset(
            {
                "youtube_captions",
                "youtube_watch_metadata_comments",
                "youtube_channel_rss_feed",
                # Probe surfaces verified non-audio from their live manifests
                # (media_modality_posture: "media bytes out of scope"; grid
                # HTML/JSON and feed XML respectively) — 2026-07-04 census.
                "yt_shorts_channel_grid_probe_v0",
                "yt_channel_rss_feed_probe_v0",
            }
        ),
        "record_id_fn": asr_record_id,
        "transcribe_fn_name": "transcribe_committed_audio_packet",
        "uses_record_set": True,
    },
    {
        "source_family": "instagram_creator",
        "in_scope_surface": "ig_reels_audio",
        "known_out_of_scope_surfaces": frozenset(
            {
                "ig_reels_grid_dom_passive_json",
                "ig_reels_deep_capture_render_audio",
                "ig_calls_browser_snapshot",
            }
        ),
        "record_id_fn": ig_asr_record_id,
        "transcribe_fn_name": "transcribe_committed_ig_audio_packet",
        "uses_record_set": False,
    },
)

_COMMITTED_TRANSCRIBERS = {
    "transcribe_committed_audio_packet": transcribe_committed_audio_packet,
    "transcribe_committed_ig_audio_packet": transcribe_committed_ig_audio_packet,
}


def default_transcriber_policy(*, model_name: str, compute_type: str) -> dict:
    """The enveloped ASR policy for the local faster-whisper path — mirrors
    ``audio_asr.transcribe_audio``'s provenance so the obligation names exactly
    the policy the injected transcriber runs."""
    return {
        "tool": "faster-whisper",
        "model": model_name,
        "compute_type": compute_type,
        "decode_params": {"beam_size": 1, "vad_filter": True, "condition_on_previous_text": False},
        "speech_gate": "faster-whisper builtin Silero VAD (onnx)",
    }


def _packet_obligation(family_config: dict, transcriber_policy: dict) -> dict:
    """The cheap obligation snapshot: constant per (family gate, transcriber
    policy). Raw audio is immutable and no committed derived record is consumed —
    the gate and the transcriber policy are the lane's only re-trigger inputs
    (F-FRAG-001 + F-IGRC-002 conventions). NON-RAISING by construction."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        "source_family": family_config["source_family"],
        "in_scope_surface": family_config["in_scope_surface"],
        "known_out_of_scope_surfaces": sorted(family_config["known_out_of_scope_surfaces"]),
        "record_id_policy": "asr_<model_token>__<audio_sha16>",
        "failed_posture_policy": "no_record_no_ack_resurface",
        "transcriber_policy": transcriber_policy,
    }


def _ack_packet(data_root, item: PickupItem, evidence: list[dict]) -> str:
    """Record the lane-owned completion fact. A create collision (another completer
    won the race) is fine when the obligation is now acknowledged; anything else is
    a real ack failure surfaced as a status."""
    try:
        append_ack(
            data_root,
            raw_anchor=item.raw_anchor,
            ack_namespace=_ACK_NAMESPACE,
            obligation=item.obligation,
            evidence=evidence,
        )
    except DataLakeRootError as exc:
        if is_acknowledged(
            data_root,
            raw_anchor=item.raw_anchor,
            ack_namespace=_ACK_NAMESPACE,
            obligation=item.obligation,
        ):
            return "acked"
        return f"ack_failed: {type(exc).__name__}: {exc}"[:200]
    return "acked"


def _verified_manifest(data_root, entry: dict) -> dict:
    """Read the committed manifest named by the availability entry, verified
    against the entry's recorded sha256 — the cheap read half for the record-id
    pre-check (the heavy body-verifying read stays inside the transcription)."""
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


def _audio_sha_from_manifest(manifest: dict) -> str:
    preserved = manifest.get("preserved_files") or []
    audio_entry = next(
        (pf for pf in preserved if ".audio." in str(pf.get("relative_packet_path", ""))), None
    )
    if audio_entry is None or not isinstance(audio_entry.get("sha256"), str):
        raise DataLakeRootError("committed packet has no preserved .audio. file with a sha256")
    return audio_entry["sha256"]


def _existing_transcript_path(
    data_root, *, packet_id: str, record_id: str, uses_record_set: bool
) -> Path | None:
    """The CURRENT-policy transcript record's path when it already exists and is
    complete (capture-time fusion, or a crash between record and ack). For the
    record-set flavor, a member without its completion marker is NOT done — the
    derivation attempt will collide loudly (derive_failed) instead of acking a
    half-written set."""
    record_path = data_root.record_path(
        subtree="derived", raw_anchor=packet_id, lane=_TRANSCRIPT_LANE, record_id=record_id
    )
    if not record_path.is_file():
        return None
    if uses_record_set and not data_root.is_record_set_complete(
        subtree="derived",
        raw_anchor=packet_id,
        record_id=record_id,
        completion_lane=_TRANSCRIPT_SET_LANE,
    ):
        return None
    return record_path


def _transcript_evidence(record_path: Path, *, packet_id: str, record_id: str) -> list[dict]:
    body = record_path.read_bytes()
    record = json.loads(body.decode("utf-8"))
    return [
        {
            "kind": "transcript_record",
            "raw_anchor": packet_id,
            "lane": _TRANSCRIPT_LANE,
            "record_id": record_id,
            "posture": record.get("posture"),
            "cue_count": record.get("cue_count"),
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "byte_count": len(body),
        }
    ]


def pending_packets(
    *,
    data_root,
    transcriber_policy: dict,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[str]:
    """Committed audio-family packet ids (both families) whose current transcript
    obligation is not acknowledged. Scheduler gate helper: no audio loading, no
    ASR, and no writes beyond the availability reconcile."""
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
    pending: list[str] = []
    for family_config in _FAMILY_CONFIGS:
        pending.extend(
            item.raw_anchor
            for item in pickup(
                data_root,
                ack_namespace=_ACK_NAMESPACE,
                obligation_fn=lambda _pid, cfg=family_config: _packet_obligation(
                    cfg, transcriber_policy
                ),
                source_family=family_config["source_family"],
                reconcile=False,
                scope_packet_ids=scope_packet_ids,
            )
        )
    return pending


def run_catchup(
    *,
    data_root,
    transcribe_fn: Callable[[str], tuple],
    transcriber_policy: dict,
    scope_packet_ids: Sequence[str] | None = None,
    reconcile_availability: bool = True,
) -> list[dict]:
    """The single cadence entrypoint: for every committed audio-family packet whose
    current obligation is unacknowledged, transcribe (or cite the existing
    current-policy transcript) and acknowledge with the record as evidence.

    Per-packet failure isolation; failed transcriptions write NO record and NO ack
    (module doc). Known non-audio surfaces are acked out-of-scope; unknown surfaces
    are visible ``unsupported_surface`` statuses. Returns one status dict per
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
    for family_config in _FAMILY_CONFIGS:
        transcribe_committed = _COMMITTED_TRANSCRIBERS[family_config["transcribe_fn_name"]]
        for item in pickup(
            data_root,
            ack_namespace=_ACK_NAMESPACE,
            obligation_fn=lambda _pid, cfg=family_config: _packet_obligation(
                cfg, transcriber_policy
            ),
            source_family=family_config["source_family"],
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
            if surface != family_config["in_scope_surface"]:
                if surface not in family_config["known_out_of_scope_surfaces"]:
                    results.append(
                        {
                            "packet_id": packet_id,
                            "status": "unsupported_surface",
                            "source_surface": surface,
                            "error": (
                                "unrecognized "
                                f"{family_config['source_family']} surface for the ASR transcript lane"
                            ),
                        }
                    )
                    continue
                evidence = [
                    {
                        "kind": "no_transcribable_audio_for_surface",
                        "raw_anchor": packet_id,
                        "source_surface": surface,
                        "basis": "known_non_audio_source_surface",
                    }
                ]
                outcome = _ack_packet(data_root, item, evidence)
                if outcome != "acked":
                    results.append(
                        {"packet_id": packet_id, "status": "ack_failed", "error": outcome}
                    )
                else:
                    results.append(
                        {
                            "packet_id": packet_id,
                            "status": "acked_no_transcribable_audio",
                            "source_surface": surface,
                        }
                    )
                continue
            try:
                manifest = _verified_manifest(data_root, entry)
                audio_sha = _audio_sha_from_manifest(manifest)
                record_id = family_config["record_id_fn"](
                    transcriber_policy.get("model"), audio_sha
                )
                existing = _existing_transcript_path(
                    data_root,
                    packet_id=packet_id,
                    record_id=record_id,
                    uses_record_set=family_config["uses_record_set"],
                )
                if existing is not None:
                    evidence = _transcript_evidence(
                        existing, packet_id=packet_id, record_id=record_id
                    )
                    outcome = _ack_packet(data_root, item, evidence)
                    if outcome != "acked":
                        results.append(
                            {"packet_id": packet_id, "status": "ack_failed", "error": outcome}
                        )
                    else:
                        results.append(
                            {
                                "packet_id": packet_id,
                                "status": "acked_existing_transcript",
                                "record_id": record_id,
                                "posture": evidence[0]["posture"],
                            }
                        )
                    continue
                derived = transcribe_committed(
                    data_root,
                    packet_id=packet_id,
                    transcribe_fn=transcribe_fn,
                    expected_model=transcriber_policy.get("model"),
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
            if derived["posture"] == "failed":
                # Block-don't-burn: no record was written; the packet stays
                # unacknowledged and re-surfaces every run (module doc).
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "derive_failed",
                        "error": f"transcriber failed: {derived.get('failure')}",
                    }
                )
                continue
            if derived["record_id"] != record_id:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "derive_failed",
                        "error": (
                            "transcriber model mismatch: "
                            f"expected {record_id}, got {derived['record_id']}"
                        )[:200],
                    }
                )
                continue
            record_path = data_root.record_path(
                subtree="derived",
                raw_anchor=packet_id,
                lane=_TRANSCRIPT_LANE,
                record_id=derived["record_id"],
            )
            evidence = _transcript_evidence(
                record_path, packet_id=packet_id, record_id=derived["record_id"]
            )
            outcome = _ack_packet(data_root, item, evidence)
            if outcome != "acked":
                results.append(
                    {"packet_id": packet_id, "status": "ack_failed", "error": outcome}
                )
            else:
                results.append(
                    {
                        "packet_id": packet_id,
                        "status": "derived",
                        "record_id": derived["record_id"],
                        "posture": derived["posture"],
                        "cue_count": derived["cue_count"],
                    }
                )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASR transcript catch-up runner utilities.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the count of committed audio-family packets whose transcript obligation is unacknowledged.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the catch-up: transcribe + acknowledge every unacknowledged packet (local ASR compute).",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model name (part of the obligation fingerprint).",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="faster-whisper compute type (part of the obligation fingerprint).",
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
    policy = default_transcriber_policy(model_name=args.model, compute_type=args.compute_type)
    if args.check:
        print(len(pending_packets(data_root=data_root, transcriber_policy=policy)))
        return 0

    from source_capture.transcript.audio_asr import AudioTranscriber

    failures = 0
    with AudioTranscriber(model_name=args.model, compute_type=args.compute_type) as transcribe_fn:
        for entry in run_catchup(
            data_root=data_root, transcribe_fn=transcribe_fn, transcriber_policy=policy
        ):
            print(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            if entry["status"] not in {
                "derived",
                "acked_existing_transcript",
                "acked_no_transcribable_audio",
            }:
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
