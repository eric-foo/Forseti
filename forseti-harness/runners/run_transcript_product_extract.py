"""Daemon-ready runner: extract product mentions from every committed YouTube transcript.

Decoupled / choreography (not a call-chain): this independently scans the lake for committed
transcripts and extracts any that lack a completed mentions record-set. Daemon-ready by the
spec contract — idempotent (skip-if-done via the completion marker), stateless/resumable
(work is re-derived from the lake each run; a record-set left half-written by a process crash
before its completion marker surfaces as `partial_needs_cleanup` for operator remediation, not
silent auto-resume), per-item failure isolated at BOTH grains (a corrupt packet -> a
`discovery_failed` status; a transcript whose extraction raises -> a `failed` status; the batch
never aborts), single entrypoint (`run_extraction`). A cron/daemon just calls `run_extraction`
on a timer (zero rework).

Pickup is the consumption seam (``data_lake.consumption``): a packet whose completed run was
acknowledged is skipped WITHOUT loading or re-hashing its raw bodies — the obligation
fingerprint (the packet's ``transcript_asr`` record set + model + rubric version) is compared
instead, so a late-arriving ASR record or extraction-policy change re-surfaces the packet
automatically. A packet with any failed or
partial transcript is never acknowledged and re-surfaces every run. Acked-and-unchanged
packets emit NO per-run status entries; the durable ack records under ``acknowledgements/``
are the completion facts. Contract:
``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

No-LLM zone (`runners/`): this file imports the cleaning driver but no LLM SDK
(`tests/contract/test_no_llm_imports.py`). The Transport is INJECTED, so the live caller
(subscription- or API-routed) is wired separately and this stays offline-testable.

Spec: youtube_transcript_product_extraction_spec_v0.md (daemon-readiness contract).
"""

from __future__ import annotations

import hashlib
import json

from cleaning.transcript_product_extractor import EXTRACTOR_RUBRIC_VERSION, TranscriptInput
from cleaning.transcript_product_lake import (
    PRODUCT_MENTIONS_LANE,
    PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
    PRODUCT_MENTIONS_SET_LANE,
    build_transcript_source_lineage,
    cues_from_asr_record,
    cues_from_json3,
    extract_products_into_lake,
    mentions_record_id,
    product_mentions_policy_fingerprint,
)
from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.silver_lineage import SilverAnchor, SilverDerivedRef, SilverRawRef

_ASR_LANE = "transcript_asr"
# Seam ack namespace = this consumer's primary registered output lane (contract rule:
# an ack namespace must be a lane declared in lane_registry.LANE_ROLES).
_ACK_NAMESPACE = PRODUCT_MENTIONS_LANE


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


def _file_id_ending_with(files: dict[str, str], suffix: str) -> str | None:
    """The preserved file_id whose packet-relative path ends with ``suffix`` (for a raw_ref)."""
    for file_id, path in files.items():
        if path.endswith(suffix):
            return file_id
    return None


def _preserved_by_id(manifest: dict) -> dict[str, dict]:
    """Map preserved file_id -> its manifest entry (carries relative_packet_path + sha256)."""
    return {
        pf["file_id"]: pf
        for pf in manifest.get("preserved_files", [])
        if isinstance(pf, dict) and pf.get("file_id")
    }


def _capture_metadata(loaded, files: dict[str, str]) -> dict:
    body = _body_ending_with(loaded, files, "capture_metadata.json")
    if body is None:
        return {}
    try:
        meta = json.loads(body.decode("utf-8"))
        return meta if isinstance(meta, dict) else {}
    except ValueError:
        return {}


def _asr_record_obligation_entries(data_root, audio_packet_id: str) -> list[list[str]]:
    """Cheap input snapshot entries for every present transcript_asr record file.

    NON-RAISING by contract: this feeds ``pickup``'s ``obligation_fn``, and an
    exception there would abort the entire pickup loop. An unreadable record
    becomes an ``unreadable:<type>`` marker entry, so the damage still changes
    the fingerprint and a repair re-surfaces the packet.
    """
    lane_dir = data_root.lane_dir(subtree="derived", raw_anchor=audio_packet_id, lane=_ASR_LANE)
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


def _asr_records(data_root, audio_packet_id: str) -> list[tuple[dict, str, str]]:
    """Read transcript_asr derived records by path, returning ``(record, record_id, sha256)``.

    The record_id (file name) and content sha256 let a consumer reference the EXACT
    consumed transcript record (closing same-shortcode ambiguity). Derived records carry
    no by-key hash, so sha256 is computed from the record file bytes -- equal to the
    derivation-time member_sha256 the lake committed in the transcript_asr set marker.
    A damaged record is a packet discovery failure, not a missing transcript.
    """
    lane_dir = data_root.lane_dir(subtree="derived", raw_anchor=audio_packet_id, lane=_ASR_LANE)
    if not lane_dir.is_dir():
        return []
    records: list[tuple[dict, str, str]] = []
    # transcript_asr record ids carry no extension (asr_packet.py), so read every file, not *.json.
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


def _packet_obligation(data_root, packet_id: str, model: str) -> dict:
    """The cheap obligation snapshot for one packet: raw is immutable (write-once),
    so the only growable inputs are the packet's ``transcript_asr`` derived records;
    the extraction model and rubric version are policy inputs too (their change must
    re-trigger a re-check). No raw bodies are loaded or re-hashed here."""
    return {
        "obligation_schema": 2,
        "consumer": "transcript_product_extract",
        "model": model,
        "rubric_version": EXTRACTOR_RUBRIC_VERSION,
        "policy_fingerprint_sha256": product_mentions_policy_fingerprint(
            EXTRACTOR_RUBRIC_VERSION
        ),
        "record_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
        "asr_records": sorted(_asr_record_obligation_entries(data_root, packet_id)),
    }


def _transcripts_for_packet(data_root, packet_id: str) -> list[TranscriptInput]:
    """Normalize one committed packet into TranscriptInput(s). MAY RAISE on a corrupt packet
    (e.g. a fail-closed `load_raw_packet` sha mismatch) — the caller isolates per packet.

    Caption packets carry the transcript json3 directly (bronze); audio packets carry it as a
    derived `transcript_asr` record (only `transcribed` records with cues are used).
    """
    loaded = data_root.load_raw_packet(packet_id)
    manifest = loaded.manifest
    surface = manifest.get("source_surface")
    files = _file_paths(manifest)
    meta = _capture_metadata(loaded, files)
    meta_video_id = str(meta.get("platform_video_id") or "")

    transcripts: list[TranscriptInput] = []
    if surface == "youtube_captions":
        json3 = _body_ending_with(loaded, files, ".json3")
        json3_file_id = _file_id_ending_with(files, ".json3")
        if json3 is not None and json3_file_id and meta_video_id:
            cues = cues_from_json3(json3)
            if cues:
                # Caption transcript is read from a raw json3 preserved file -> raw_ref to it.
                preserved = _preserved_by_id(manifest).get(json3_file_id, {})
                raw_ref = SilverRawRef(
                    packet_id=packet_id,
                    file_id=json3_file_id,
                    relative_packet_path=str(preserved.get("relative_packet_path") or "") or None,
                    sha256=str(preserved.get("sha256") or "") or None,
                    hash_basis="raw_stored_bytes",
                    anchor=SilverAnchor(kind="file"),
                    relation="consumed",
                )
                lineage = build_transcript_source_lineage(
                    namespace="youtube",
                    source_surface=surface,
                    video_id=meta_video_id,
                    raw_ref=raw_ref,
                    captured_at=str(meta.get("capture_timestamp") or "") or None,
                )
                transcripts.append(
                    TranscriptInput(meta_video_id, packet_id, "caption", cues, source_lineage=lineage)
                )
    elif surface == "youtube_audio":
        for record, record_id, record_sha in _asr_records(data_root, packet_id):
            if record.get("posture") != "transcribed":
                continue
            cues = cues_from_asr_record(record)
            video_id = str(record.get("video_id") or meta_video_id)
            if cues and video_id:
                # The ASR transcript IS a derived record -> derived_ref to the EXACT record consumed.
                derived_ref = SilverDerivedRef(
                    raw_anchor=packet_id,
                    lane=_ASR_LANE,
                    record_id=record_id,
                    sha256=record_sha,
                    hash_basis="derived_record_bytes",
                    relation="consumed",
                )
                lineage = build_transcript_source_lineage(
                    namespace="youtube",
                    source_surface=surface,
                    video_id=video_id,
                    derived_ref=derived_ref,
                    captured_at=str(record.get("retrieval_time_utc") or "") or None,
                )
                transcripts.append(
                    TranscriptInput(video_id, packet_id, "asr", cues, source_lineage=lineage)
                )
    return transcripts


def run_extraction(
    *,
    data_root,
    transport,
    provider,
    model: str,
    api_key: str,
    max_tokens: int = 2048,
) -> list[dict]:
    """The single daemon entrypoint: extract mentions for every not-yet-done transcript.

    Failure-isolated at both grains: a corrupt packet yields a `discovery_failed` status; a
    transcript whose check/extraction raises yields a `failed` status — the batch always
    continues. Idempotent (skip-if-done). A record-set half-written before its completion marker
    (process crash) yields `partial_needs_cleanup` rather than a re-colliding `failed` forever.
    Acked-and-unchanged packets are skipped by the seam without loading raw bodies and emit no
    status entry (the ack record is the durable completion fact); a packet whose transcripts all
    complete is acknowledged, and an ack write failure surfaces as an `ack_failed` status.
    Returns one status dict per processed packet/transcript.
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
        source_family="youtube",
        reconcile=False,
    ):
        packet_id = item.raw_anchor
        try:
            transcripts = _transcripts_for_packet(data_root, packet_id)
        except Exception as exc:  # noqa: BLE001 - a corrupt packet -> discovery_failed, batch continues
            results.append(
                {"packet_id": packet_id, "status": "discovery_failed", "error": f"{type(exc).__name__}: {exc}"[:200]}
            )
            continue
        packet_complete = True
        evidence: list[dict] = []
        for transcript in transcripts:
            anchor = transcript.transcript_anchor
            try:
                policy_fingerprint = product_mentions_policy_fingerprint(
                    EXTRACTOR_RUBRIC_VERSION
                )
                rid = mentions_record_id(
                    transcript,
                    model,
                    policy_fingerprint_sha256=policy_fingerprint,
                )
                if data_root.is_record_set_complete(
                    subtree="derived",
                    raw_anchor=anchor,
                    record_id=rid,
                    completion_lane=PRODUCT_MENTIONS_SET_LANE,
                ):
                    results.append(
                        {"anchor": anchor, "video_id": transcript.video_id, "status": "skipped_done"}
                    )
                    evidence.append(
                        {"kind": "record_set_complete", "raw_anchor": anchor,
                         "completion_lane": PRODUCT_MENTIONS_SET_LANE, "record_id": rid}
                    )
                    continue
                member_path = data_root.record_path(
                    subtree="derived", raw_anchor=anchor, lane=PRODUCT_MENTIONS_LANE, record_id=rid
                )
                if member_path.exists():
                    # Member record written but the completion marker is absent: a crash between the
                    # two writes. The deterministic record_id would re-collide on every rerun, so
                    # surface it for operator cleanup rather than looping forever on `failed`.
                    results.append(
                        {"anchor": anchor, "video_id": transcript.video_id, "status": "partial_needs_cleanup"}
                    )
                    packet_complete = False
                    continue
                paths = extract_products_into_lake(
                    data_root=data_root,
                    transcript=transcript,
                    transport=transport,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    record_id=rid,
                    policy_version=EXTRACTOR_RUBRIC_VERSION,
                    policy_fingerprint_sha256=policy_fingerprint,
                    max_tokens=max_tokens,
                )
                written = next(iter(paths.values()), None)
                results.append(
                    {
                        "anchor": anchor,
                        "video_id": transcript.video_id,
                        "status": "extracted",
                        "path": str(written) if written is not None else None,
                    }
                )
                evidence.append(
                    {"kind": "record_set_complete", "raw_anchor": anchor,
                     "completion_lane": PRODUCT_MENTIONS_SET_LANE, "record_id": rid}
                )
            except Exception as exc:  # noqa: BLE001 - per-item failure isolation (daemon-ready)
                results.append(
                    {"anchor": anchor, "video_id": transcript.video_id, "status": "failed", "error": f"{type(exc).__name__}: {exc}"[:200]}
                )
                packet_complete = False
        if packet_complete:
            if not evidence:
                # No extractable transcript in this packet under the current inputs; the
                # discovery outcome IS the completion evidence. A later ASR record changes
                # the obligation fingerprint and re-surfaces the packet.
                evidence = [{"kind": "no_extractable_transcripts", "raw_anchor": packet_id}]
            outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
    return results
