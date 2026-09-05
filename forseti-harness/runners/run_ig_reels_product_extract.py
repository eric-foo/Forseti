"""Daemon-ready runner: extract product mentions from every committed Instagram Reel transcript.

The IG analogue of `run_transcript_product_extract` (YouTube). Decoupled / choreography (not a
call-chain): independently scans the lake for committed IG-Reel audio packets and deep-capture
transcript records, then extracts any transcript lacking a completed mentions record-set.
Daemon-ready by the same contract — idempotent (skip-if-done), stateless/resumable, and per-item
failure isolated after candidate enumeration at BOTH grains (a corrupt packet ->
`discovery_failed`; a transcript whose extraction raises -> `failed`). Enumeration-time
filesystem failures still surface instead of being laundered into fake success.

Pickup for the PACKET-BACKED route is the consumption seam (``data_lake.consumption``): a
committed ``instagram_creator`` packet whose completed run was acknowledged is skipped WITHOUT
loading or re-hashing its raw bodies — the obligation fingerprint (the packet's
``transcript_asr`` records + model + rubric version) is compared instead, so a late-arriving
ASR record or extraction-policy change re-surfaces the packet automatically.
Acked-and-unchanged packets emit NO per-run status entries; the durable ack records under
``acknowledgements/`` are the completion facts.
Contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

Current deep-capture transcripts are packet-backed and therefore use the same consumption seam.
Historical shortcode-anchored record sets remain visible only through marker discovery so their
unsupported lineage can be reported as audit-only; no ack is written under those non-packet
anchors.

IG is its OWN runner (not an edit to the YouTube runner, which hardcodes
`list_available(source_family="youtube")`): packet discovery keys on source_family=instagram_creator
and the ig_reels_audio surface; per-reel deep capture is discovered from its completed derived
record sets. IG Reels have no caption track, so ASR is the transcript kind for both routes. The
extract+persist seam (`cleaning.transcript_product_lake`) and the schema are source-family-agnostic
and reused verbatim.

No-LLM zone (`runners/`): imports the cleaning driver but no LLM SDK
(`tests/contract/test_no_llm_imports.py`). The Transport is INJECTED, so the live caller
(subscription- or API-routed) is wired separately and this stays offline-testable.

Spec: forseti/product/spines/capture/core/source_families/social_media/instagram/
ig_reels_transcript_product_extraction_spec_v0.md (IG delta; daemon-readiness inherited).
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

from cleaning.transcript_product_extractor import EXTRACTOR_RUBRIC_VERSION, TranscriptInput
from cleaning.transcript_product_lake import (
    PRODUCT_MENTIONS_LANE,
    PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
    PRODUCT_MENTIONS_SET_LANE,
    build_transcript_source_lineage,
    cues_from_asr_record,
    extract_products_into_lake,
    mentions_record_id,
)
from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.root import DataLakeRootError
from data_lake.silver_record import SILVER_VAULT_RECORD_SCHEMA_VERSION
from data_lake.silver_lineage import SilverDerivedRef
from source_capture.ig_reels_deep_capture_lake import (
    DEEP_CAPTURE_PACKET_SURFACE,
    DEEP_CAPTURE_SET_LANE,
    REEL_TRANSCRIPT_LANE,
    current_deep_capture_record,
    deep_capture_shortcode,
    transcript_compatibility_view,
)

_ASR_LANE = "transcript_asr"
_IG_SOURCE_FAMILY = "instagram_creator"
_IG_AUDIO_SURFACE = "ig_reels_audio"
# Seam ack namespace = this consumer's primary registered output lane (contract rule:
# an ack namespace must be a lane declared in lane_registry.LANE_ROLES).
_ACK_NAMESPACE = PRODUCT_MENTIONS_LANE
# Distinct consumer identity in the obligation envelope: IG and YouTube share the ack
# namespace but must never cross-satisfy each other's fingerprints.
_SEAM_CONSUMER = "ig_reels_product_extract"
DEFAULT_EXTRACTION_MODEL = "codex-extraction-v0"
_DEEP_CAPTURE_ROUTE = "deep_capture_render_audio"
_DEEP_CAPTURE_SURFACE = "ig_reels_deep_capture_render_audio"


def _file_paths(manifest: dict) -> dict[str, str]:
    return {
        pf.get("file_id", ""): pf.get("relative_packet_path", "")
        for pf in manifest.get("preserved_files", [])
        if isinstance(pf, dict)
    }


def _body_ending_with(loaded, files: dict[str, str], suffix: str) -> bytes | None:
    for file_id, path in files.items():
        if path.endswith(suffix):
            return loaded.bodies.get(file_id)
    return None


def _capture_metadata(loaded, files: dict[str, str]) -> dict:
    body = _body_ending_with(loaded, files, "capture_metadata.json")
    if body is None:
        return {}
    try:
        meta = json.loads(body.decode("utf-8"))
        return meta if isinstance(meta, dict) else {}
    except ValueError:
        return {}


def _lane_dir(data_root, *, raw_anchor: str, lane: str):
    resolver = getattr(data_root, "lane_dir", None)
    if resolver is not None:
        return resolver(subtree="derived", raw_anchor=raw_anchor, lane=lane)
    return data_root.path / "derived" / raw_anchor / lane


def _record_path(data_root, *, raw_anchor: str, lane: str, record_id: str):
    resolver = getattr(data_root, "record_path", None)
    if resolver is not None:
        return resolver(
            subtree="derived", raw_anchor=raw_anchor, lane=lane, record_id=record_id
        )
    return data_root.path / "derived" / raw_anchor / lane / record_id


def _derived_record_obligation_entries(data_root, raw_anchor: str, lane: str) -> list[list[str]]:
    """Cheap input snapshot entries for every present record in one derived lane."""
    lane_dir = _lane_dir(data_root, raw_anchor=raw_anchor, lane=lane)
    if not lane_dir.is_dir():
        return []
    entries: list[list[str]] = []
    for record_file in sorted(lane_dir.iterdir()):
        if not record_file.is_file():
            continue
        try:
            body = record_file.read_bytes()
            record_sha = hashlib.sha256(body).hexdigest()
        except OSError as exc:
            record_sha = f"unreadable:{type(exc).__name__}"
        entries.append([record_file.name, record_sha])
    return entries


def _asr_record_obligation_entries(data_root, audio_packet_id: str) -> list[list[str]]:
    return _derived_record_obligation_entries(data_root, audio_packet_id, _ASR_LANE)


def _asr_records(data_root, audio_packet_id: str) -> list[tuple[dict, str, str]]:
    """Read transcript_asr derived records by path, returning (record, record_id, sha256).

    The record_id and sha256 let product-mention Silver lineage reference the exact
    transcript record consumed, rather than only the packet/shortcode anchor. A damaged
    record is a packet discovery failure, not a missing transcript.
    """
    lane_dir = _lane_dir(data_root, raw_anchor=audio_packet_id, lane=_ASR_LANE)
    if not lane_dir.is_dir():
        return []
    records: list[tuple[dict, str, str]] = []
    for record_file in sorted(lane_dir.iterdir()):
        if not record_file.is_file():
            continue
        try:
            body = record_file.read_bytes()
        except OSError as exc:
            raise ValueError(f"transcript_asr record {record_file.name!r} unreadable") from exc
        record_sha = hashlib.sha256(body).hexdigest()
        try:
            data = json.loads(body.decode("utf-8"))
        except ValueError as exc:
            raise ValueError(f"transcript_asr record {record_file.name!r} invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError(f"transcript_asr record {record_file.name!r} is not a JSON object")
        records.append((data, record_file.name, record_sha))
    return records


def _read_derived_json_record(data_root, *, raw_anchor: str, lane: str, record_id: str) -> tuple[dict, str] | None:
    path = _record_path(data_root, raw_anchor=raw_anchor, lane=lane, record_id=record_id)
    try:
        body = path.read_bytes()
        data = json.loads(body.decode("utf-8"))
    except (OSError, ValueError):
        return None
    return (data, hashlib.sha256(body).hexdigest()) if isinstance(data, dict) else None


def _iter_derived_lane_records(data_root, lane: str):
    derived = data_root.path / "derived"
    if not derived.is_dir():
        return
    for shard_dir in sorted(derived.iterdir()):
        if not shard_dir.is_dir():
            continue
        for anchor_dir in sorted(shard_dir.iterdir()):
            if not anchor_dir.is_dir():
                continue
            lane_dir = anchor_dir / lane
            if not lane_dir.is_dir():
                continue
            for record_file in sorted(lane_dir.iterdir()):
                if record_file.is_file():
                    yield anchor_dir.name, record_file.name


def _transcript_source_key(*, transcript_anchor: str, source_kind: str, asr_record_id: str | None = None) -> str:
    if source_kind == "asr":
        return f"{transcript_anchor}:asr:{asr_record_id or 'unknown_record'}"
    return f"{transcript_anchor}:{source_kind}"


def _candidate_packet_ids(data_root) -> tuple[list[str], list[dict]]:
    """Committed instagram_creator packet ids over a freshly reconciled availability
    surface, plus per-packet reconcile failures. The rebuild deletes index entries
    first, so a swallowed reconcile failure would silently hide healthy packets —
    failures must reach the caller's visibility channel (F-ECR-001 adjudicated
    shape, shared helper in data_lake.consumption)."""
    failures = reconcile_availability_per_packet(data_root)
    return list(data_root.list_available(source_family=_IG_SOURCE_FAMILY)), failures


def _packet_obligation(data_root, packet_id: str, model: str) -> dict:
    """The cheap obligation snapshot for one committed packet: raw is immutable
    (write-once), so the only growable inputs are the packet's ``transcript_asr``
    derived records; the extraction model and rubric version are policy inputs too.
    No raw bodies are loaded or re-hashed here."""
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        "model": model,
        "rubric_version": EXTRACTOR_RUBRIC_VERSION,
        "record_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
        "asr_records": sorted(_asr_record_obligation_entries(data_root, packet_id)),
        "deep_capture_transcripts": sorted(
            _derived_record_obligation_entries(data_root, packet_id, REEL_TRANSCRIPT_LANE)
        ),
        "deep_capture_markers": sorted(
            _derived_record_obligation_entries(data_root, packet_id, DEEP_CAPTURE_SET_LANE)
        ),
    }


def _transcripts_for_packet(data_root, packet_id: str) -> list[TranscriptInput]:
    """Normalize one committed IG packet into TranscriptInput(s). MAY RAISE on a corrupt packet
    (fail-closed `load_raw_packet` sha mismatch) — the caller isolates per packet.

    Both standalone audio and current deep-capture packets can carry packet-backed transcripts.
    The instagram_creator family also holds grid-metadata packets with NO audio, which are
    skipped here. Only `transcribed` records with cues are used.
    """
    loaded = data_root.load_raw_packet(packet_id)
    manifest = loaded.manifest
    if manifest.get("source_surface") == DEEP_CAPTURE_PACKET_SURFACE:
        candidates = _deep_capture_transcript_candidates(data_root, packet_anchor=packet_id)
        failures = [failure for _transcript, failure in candidates if failure is not None]
        if failures:
            raise ValueError(str(failures[0].get("error") or "deep-capture discovery failed"))
        return [transcript for transcript, _failure in candidates if transcript is not None]
    if manifest.get("source_surface") != _IG_AUDIO_SURFACE:
        return []  # e.g. ig_reels_grid_dom_passive_json: no audio/transcript -> not a transcript source
    files = _file_paths(manifest)
    meta = _capture_metadata(loaded, files)
    meta_shortcode = str(meta.get("platform_shortcode") or "")

    transcripts: list[TranscriptInput] = []
    for record, record_id, record_sha in _asr_records(data_root, packet_id):
        if record.get("posture") != "transcribed":
            continue
        cues = cues_from_asr_record(record)
        shortcode = str(record.get("video_id") or meta_shortcode)
        if cues and shortcode:
            source_key = _transcript_source_key(
                transcript_anchor=packet_id,
                source_kind="asr",
                asr_record_id=record_id,
            )
            lineage = build_transcript_source_lineage(
                namespace="instagram",
                source_surface=_IG_AUDIO_SURFACE,
                video_id=shortcode,
                derived_ref=SilverDerivedRef(
                    raw_anchor=packet_id,
                    lane=_ASR_LANE,
                    record_id=record_id,
                    sha256=record_sha,
                    hash_basis="derived_record_bytes",
                    relation="consumed",
                ),
                captured_at=str(record.get("retrieval_time_utc") or "") or None,
            )
            transcripts.append(
                TranscriptInput(
                    shortcode,
                    packet_id,
                    "asr",
                    cues,
                    source_lineage=lineage,
                    transcript_source_key=source_key,
                    source_route="standalone_audio_packet",
                    asr_record_id=record_id,
                )
            )
    return transcripts


def _deep_capture_transcript_candidates(
    data_root, *, packet_anchor: str | None = None
) -> list[tuple[TranscriptInput | None, dict | None]]:
    candidates: list[tuple[TranscriptInput | None, dict | None]] = []
    for raw_anchor, record_id in _iter_derived_lane_records(data_root, DEEP_CAPTURE_SET_LANE) or ():
        if packet_anchor is not None and raw_anchor != packet_anchor:
            continue
        if packet_anchor is None:
            try:
                if data_root.find_packet(raw_anchor) is not None:
                    continue
            except DataLakeRootError:
                # Historical anchors are shortcodes, not packet ids.
                pass
        source_key = _transcript_source_key(
            transcript_anchor=raw_anchor,
            source_kind="asr",
            asr_record_id=record_id,
        )
        failure_identity = {
            "anchor": raw_anchor,
            "video_id": raw_anchor,
            "transcript_source_key": source_key,
            "source_route": _DEEP_CAPTURE_ROUTE,
            "asr_record_id": record_id,
        }
        try:
            complete = data_root.is_record_set_complete(
                subtree="derived",
                raw_anchor=raw_anchor,
                record_id=record_id,
                completion_lane=DEEP_CAPTURE_SET_LANE,
            )
        except Exception as exc:  # noqa: BLE001 - one damaged marker must not abort the batch
            candidates.append(
                (
                    None,
                    {
                        **failure_identity,
                        "status": "discovery_failed",
                        "error": f"{type(exc).__name__}: {exc}"[:200],
                    },
                )
            )
            continue
        if not complete:
            candidates.append(
                (
                    None,
                    {
                        **failure_identity,
                        "status": "discovery_failed",
                        "error": "ValueError: incomplete deep-capture record set",
                    },
                )
            )
            continue
        marker_path = data_root.record_path(
            subtree="derived",
            raw_anchor=raw_anchor,
            lane=DEEP_CAPTURE_SET_LANE,
            record_id=record_id,
        )
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            marker = {}
        if REEL_TRANSCRIPT_LANE not in marker.get("member_lanes", []):
            continue
        loaded = _read_derived_json_record(
            data_root,
            raw_anchor=raw_anchor,
            lane=REEL_TRANSCRIPT_LANE,
            record_id=record_id,
        )
        if loaded is None:
            candidates.append(
                (
                    None,
                    {
                        **failure_identity,
                        "status": "discovery_failed",
                        "error": "ValueError: deep-capture transcript record unreadable",
                    },
                )
            )
            continue
        record, record_sha = loaded
        if not current_deep_capture_record(
            data_root,
            record=record,
            raw_anchor=raw_anchor,
            lane=REEL_TRANSCRIPT_LANE,
            record_id=record_id,
        ):
            is_envelope = record.get("schema_version") == SILVER_VAULT_RECORD_SCHEMA_VERSION
            candidates.append(
                (
                    None,
                    {
                        **failure_identity,
                        "status": "discovery_failed" if is_envelope else "historical_audit_only",
                        "error": (
                            "current deep-capture envelope or exact source refs invalid"
                            if is_envelope
                            else "legacy deep-capture transcript lacks resolvable source-backed Silver envelope"
                        ),
                    },
                )
            )
            continue
        record_shortcode = deep_capture_shortcode(record) or ""
        if not record_shortcode:
            candidates.append(
                (
                    None,
                    {
                        **failure_identity,
                        "status": "discovery_failed",
                        "error": "ValueError: deep-capture transcript shortcode absent",
                    },
                )
            )
            continue
        compatibility = transcript_compatibility_view(record)
        cues = cues_from_asr_record(compatibility)
        if not cues:
            continue
        lineage = build_transcript_source_lineage(
            namespace="instagram",
            source_surface=_DEEP_CAPTURE_SURFACE,
            video_id=record_shortcode,
            derived_ref=SilverDerivedRef(
                raw_anchor=raw_anchor,
                lane=REEL_TRANSCRIPT_LANE,
                record_id=record_id,
                sha256=record_sha,
                hash_basis="derived_record_bytes",
                relation="consumed",
                record_set_completion_lane=DEEP_CAPTURE_SET_LANE,
            ),
            captured_at=str(record.get("captured_at") or "") or None,
        )
        candidates.append(
            (
                TranscriptInput(
                    record_shortcode,
                    raw_anchor,
                    "asr",
                    cues,
                    source_lineage=lineage,
                    transcript_source_key=source_key,
                    source_route=_DEEP_CAPTURE_ROUTE,
                    asr_record_id=record_id,
                ),
                None,
            )
        )
    return candidates


def discover_transcript_candidates(data_root) -> list[tuple[TranscriptInput | None, dict | None]]:
    """Return all IG transcript candidates with discovery failures isolated per source.

    The order matches ``run_extraction``: committed packet-backed transcripts first, then
    completed deep-capture transcripts. A candidate is ``(transcript, None)``; a damaged
    source is ``(None, failure_dict)`` so callers can surface the failure without aborting.
    """
    candidates: list[tuple[TranscriptInput | None, dict | None]] = []
    packet_ids, reconcile_failures = _candidate_packet_ids(data_root)
    candidates.extend((None, failure) for failure in reconcile_failures)
    for packet_id in packet_ids:
        try:
            transcripts = _transcripts_for_packet(data_root, packet_id)
        except Exception as exc:  # noqa: BLE001 - corrupt packet discovery must not abort the poll
            candidates.append(
                (
                    None,
                    {
                        "packet_id": packet_id,
                        "status": "discovery_failed",
                        "error": f"{type(exc).__name__}: {exc}"[:200],
                    },
                )
            )
            continue
        candidates.extend((transcript, None) for transcript in transcripts)
    candidates.extend(_deep_capture_transcript_candidates(data_root))
    return candidates


def iter_transcripts(data_root) -> list[TranscriptInput]:
    """Return transcript candidates only, dropping isolated discovery failures."""
    return [
        transcript
        for transcript, failure in discover_transcript_candidates(data_root)
        if transcript is not None and failure is None
    ]


def _mentions_set_state(data_root, transcript: TranscriptInput, model: str) -> str:
    rid = mentions_record_id(transcript, model)
    if data_root.is_record_set_complete(
        subtree="derived",
        raw_anchor=transcript.transcript_anchor,
        record_id=rid,
        completion_lane=PRODUCT_MENTIONS_SET_LANE,
    ):
        return "complete"
    member_path = _record_path(
        data_root,
        raw_anchor=transcript.transcript_anchor,
        lane=PRODUCT_MENTIONS_LANE,
        record_id=rid,
    )
    if member_path.exists():
        return "partial_needs_cleanup"
    return "extractable"


def pending_extraction_counts(*, data_root, model: str = DEFAULT_EXTRACTION_MODEL) -> dict[str, int]:
    """Count extractable and crash-partial IG Reel transcript mention sets.

    Scheduler gate helper: no LLM and no network. A no-work count is a valid
    claim only over a fully reconciled availability surface (seam contract), so
    a per-packet reconcile failure raises loud here instead of silently
    under-counting. Corrupt packets past reconcile are isolated the same way
    discovery isolates them in ``run_extraction``.
    """
    counts = {"extractable": 0, "partial_needs_cleanup": 0}
    packet_ids, reconcile_failures = _candidate_packet_ids(data_root)
    if reconcile_failures:
        first = reconcile_failures[0]
        raise DataLakeRootError(
            "availability reconcile failed before pending count: "
            f"{first['packet_id']}: {first['error']}"
        )
    for packet_id in packet_ids:
        try:
            transcripts = _transcripts_for_packet(data_root, packet_id)
        except Exception:  # noqa: BLE001 - corrupt packet discovery must not abort the poll
            continue
        for transcript in transcripts:
            state = _mentions_set_state(data_root, transcript, model)
            if state in counts:
                counts[state] += 1
    for transcript, _failure in _deep_capture_transcript_candidates(data_root):
        if transcript is None:
            continue
        state = _mentions_set_state(data_root, transcript, model)
        if state in counts:
            counts[state] += 1
    return counts


def count_pending_extractions(*, data_root, model: str = DEFAULT_EXTRACTION_MODEL) -> int:
    """Count transcripts that can be extracted now without manual cleanup."""
    return pending_extraction_counts(data_root=data_root, model=model)["extractable"]


def count_partial_extractions(*, data_root, model: str = DEFAULT_EXTRACTION_MODEL) -> int:
    """Count incomplete mention sets that need operator cleanup before retry."""
    return pending_extraction_counts(data_root=data_root, model=model)["partial_needs_cleanup"]


def run_extraction(
    *,
    data_root,
    transport,
    provider,
    model: str,
    api_key: str,
    max_tokens: int = 2048,
) -> list[dict]:
    """The single daemon entrypoint: extract mentions for every not-yet-done IG-Reel transcript.

    Failure-isolated at both grains (corrupt packet -> `discovery_failed`; per-transcript raise ->
    `failed`; the batch always continues). Idempotent (skip-if-done). A record-set half-written
    before its completion marker (process crash) yields `partial_needs_cleanup`. Returns one status
    dict per processed packet/transcript.

    Packet-backed route (including current deep capture): seam pickup — an acked-and-unchanged packet is skipped without loading
    raw bodies and emits NO status entry (the durable ack record is the completion fact); a packet
    whose transcripts all complete is acknowledged with completion evidence, and an ack write
    failure surfaces as an `ack_failed` status. A packet with any failed or partial transcript is
    never acknowledged and re-surfaces every run. Historical deep-capture records are re-walked
    only to report their audit-only posture and are never acknowledged.
    """
    results: list[dict] = []
    # Visible reconcile opt-out per the seam contract: this runner reconciles
    # ITSELF first, per packet, so one corrupt manifest becomes a visible
    # availability_reconcile_failed status while healthy packets still index
    # and process — instead of pickup's whole-batch fail-loud default reconcile.
    results.extend(reconcile_availability_per_packet(data_root))
    for item in pickup(
        data_root,
        ack_namespace=_ACK_NAMESPACE,
        obligation_fn=lambda packet_id: _packet_obligation(data_root, packet_id, model),
        source_family=_IG_SOURCE_FAMILY,
        reconcile=False,
    ):
        packet_id = item.raw_anchor
        try:
            transcripts = _transcripts_for_packet(data_root, packet_id)
        except Exception as exc:  # noqa: BLE001 - a corrupt packet -> discovery_failed, batch continues
            results.append(
                {
                    "packet_id": packet_id,
                    "status": "discovery_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
            continue
        packet_complete = True
        evidence: list[dict] = []
        for transcript in transcripts:
            entry = _extract_one_transcript(
                data_root=data_root,
                transcript=transcript,
                transport=transport,
                provider=provider,
                model=model,
                api_key=api_key,
                max_tokens=max_tokens,
                results=results,
            )
            if entry is None:
                packet_complete = False
            else:
                evidence.append(entry)
        if packet_complete:
            if not evidence:
                # No extractable transcript in this packet under the current inputs
                # (e.g. a grid-metadata surface, or only non-transcribed ASR records);
                # the discovery outcome IS the completion evidence. A later ASR record
                # changes the obligation fingerprint and re-surfaces the packet.
                evidence = [{"kind": "no_extractable_transcripts", "raw_anchor": packet_id}]
            outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
    # Historical deep-capture route: shortcode anchors are not committed
    # availability, so retain marker-based discovery solely for visible audit-only status.
    for transcript, failure in _deep_capture_transcript_candidates(data_root):
        if failure is not None:
            results.append(failure)
            continue
        if transcript is None:
            continue
        _extract_one_transcript(
            data_root=data_root,
            transcript=transcript,
            transport=transport,
            provider=provider,
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            results=results,
        )
    return results


def _result_identity(transcript: TranscriptInput) -> dict:
    return {
        key: value
        for key, value in {
            "anchor": transcript.transcript_anchor,
            "video_id": transcript.video_id,
            "transcript_source_key": transcript.transcript_source_key,
            "source_route": transcript.source_route,
            "asr_record_id": transcript.asr_record_id,
        }.items()
        if value is not None
    }


def _extract_one_transcript(
    *,
    data_root,
    transcript: TranscriptInput,
    transport,
    provider,
    model: str,
    api_key: str,
    max_tokens: int,
    results: list[dict],
) -> dict | None:
    """Process one transcript, appending its status entry to ``results``.

    Returns the completion-evidence entry (for the packet route's ack) when the
    transcript's mentions record-set is complete after this call — done before or
    extracted now — and ``None`` on failure or partial (the packet must then stay
    unacknowledged and re-surface). The deep-capture route ignores the return.
    """
    anchor = transcript.transcript_anchor
    try:
        rid = mentions_record_id(transcript, model)
        completion_evidence = {
            "kind": "record_set_complete",
            "raw_anchor": anchor,
            "completion_lane": PRODUCT_MENTIONS_SET_LANE,
            "record_id": rid,
        }
        if data_root.is_record_set_complete(
            subtree="derived",
            raw_anchor=anchor,
            record_id=rid,
            completion_lane=PRODUCT_MENTIONS_SET_LANE,
        ):
            results.append({**_result_identity(transcript), "status": "skipped_done"})
            return completion_evidence
        member_path = _record_path(
            data_root, raw_anchor=anchor, lane=PRODUCT_MENTIONS_LANE, record_id=rid
        )
        if member_path.exists():
            results.append({**_result_identity(transcript), "status": "partial_needs_cleanup"})
            return None
        paths = extract_products_into_lake(
            data_root=data_root,
            transcript=transcript,
            transport=transport,
            provider=provider,
            model=model,
            api_key=api_key,
            record_id=rid,
            max_tokens=max_tokens,
        )
        written = next(iter(paths.values()), None)
        results.append(
            {
                **_result_identity(transcript),
                "status": "extracted",
                "path": str(written) if written is not None else None,
            }
        )
        return completion_evidence
    except Exception as exc:  # noqa: BLE001 - per-item failure isolation (daemon-ready)
        results.append(
            {
                **_result_identity(transcript),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}"[:200],
            }
        )
        return None

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IG Reels product extraction runner utilities."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the LLM-free count of extractable IG Reel transcripts.",
    )
    parser.add_argument(
        "--check-partials",
        action="store_true",
        help="Print the LLM-free count of partial mentions sets needing cleanup.",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Forseti data lake root. Defaults to FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_EXTRACTION_MODEL,
        help="Model token used in the deterministic mentions record_id.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.check and args.check_partials:
        parser.exit(status=2, message="choose exactly one of --check or --check-partials\n")
    if not args.check and not args.check_partials:
        parser.exit(status=2, message="no action requested; use --check or --check-partials\n")

    from data_lake.root import DataLakeRoot

    try:
        data_root = DataLakeRoot.resolve(explicit=args.data_root)
    except Exception as exc:  # noqa: BLE001 - CLI must surface root resolution failures
        parser.exit(status=2, message=f"data root required: {type(exc).__name__}: {exc}\n")
    counts = pending_extraction_counts(data_root=data_root, model=args.model)
    key = "extractable" if args.check else "partial_needs_cleanup"
    print(counts[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
