"""Daemon-ready TikTok transcript product-extraction runner.

Discovers committed TikTok creator-batch admission packets, converts each
source-native WebVTT transcript into the shared ``TranscriptInput`` shape, and
persists product mentions through ``cleaning.transcript_product_lake``.  TikTok
owns only packet discovery and cue normalization; extraction policy and the
Silver product-mention record shape stay source-family agnostic.

The runner is idempotent and failure-isolated.  Completed transcript record
sets are skipped, crash-partial sets surface as ``partial_needs_cleanup``, and
a packet is acknowledged only when every extractable transcript is complete.
The injected transport keeps the runner offline-testable and does not grant a
live provider call.
"""

from __future__ import annotations

import hashlib
import json
import re

from cleaning.transcript_product_extractor import EXTRACTOR_RUBRIC_VERSION, TranscriptInput
from cleaning.transcript_product_lake import (
    PRODUCT_MENTIONS_LANE,
    PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
    PRODUCT_MENTIONS_SET_LANE,
    build_transcript_source_lineage,
    extract_products_into_lake,
    mentions_record_id,
)
from data_lake.consumption import (
    ack_packet,
    pickup,
    reconcile_availability_per_packet,
)
from data_lake.silver_lineage import SilverAnchor, SilverRawRef
from source_capture.tiktok.batch_packet import (
    TIKTOK_BATCH_CAPTURE_JSON_NAME,
    TIKTOK_BATCH_CAPTURE_SURFACE,
)

_ACK_NAMESPACE = PRODUCT_MENTIONS_LANE
_SEAM_CONSUMER = "tiktok_product_extract"
_SOURCE_FAMILY = "tiktok"
_SOURCE_ROUTE = "tiktok_batch_source_native_webvtt"
_WEBVTT_TIMESTAMP = re.compile(
    r"^(?P<hours>\d{2,}):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)\.(?P<millis>\d{3})$"
)


def _file_paths(manifest: dict) -> dict[str, str]:
    return {
        str(preserved.get("file_id") or ""): str(preserved.get("relative_packet_path") or "")
        for preserved in manifest.get("preserved_files", [])
        if isinstance(preserved, dict) and preserved.get("file_id")
    }


def _preserved_by_id(manifest: dict) -> dict[str, dict]:
    return {
        str(preserved["file_id"]): preserved
        for preserved in manifest.get("preserved_files", [])
        if isinstance(preserved, dict) and preserved.get("file_id")
    }


def _batch_file_id(files: dict[str, str]) -> str | None:
    for file_id, path in files.items():
        if path.endswith(TIKTOK_BATCH_CAPTURE_JSON_NAME):
            return file_id
    return None


def _timestamp_to_ms(value: object) -> int:
    if not isinstance(value, str):
        raise ValueError("TikTok subtitle cue timestamp must be a string")
    match = _WEBVTT_TIMESTAMP.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"invalid TikTok WebVTT timestamp: {value!r}")
    return (
        int(match.group("hours")) * 3_600_000
        + int(match.group("minutes")) * 60_000
        + int(match.group("seconds")) * 1_000
        + int(match.group("millis"))
    )


def _normalized_cues(raw_cues: object) -> list[dict]:
    if not isinstance(raw_cues, list):
        raise ValueError("TikTok subtitle cues must be a list")
    cues: list[dict] = []
    for index, raw_cue in enumerate(raw_cues):
        if not isinstance(raw_cue, dict):
            raise ValueError(f"TikTok subtitle cue {index} is not an object")
        text = str(raw_cue.get("text") or "").strip()
        if not text:
            raise ValueError(f"TikTok subtitle cue {index} has blank text")
        start_ms = _timestamp_to_ms(raw_cue.get("start"))
        end_ms = _timestamp_to_ms(raw_cue.get("end"))
        if end_ms < start_ms:
            raise ValueError(f"TikTok subtitle cue {index} ends before it starts")
        cues.append({"start_ms": start_ms, "end_ms": end_ms, "text": text})
    return cues


def _packet_obligation(data_root, packet_id: str, model: str) -> dict:
    """Cheap immutable-input fingerprint; no raw body load on acknowledged skips."""
    availability = data_root.read_availability(packet_id) or {}
    return {
        "obligation_schema": 1,
        "consumer": _SEAM_CONSUMER,
        "model": model,
        "rubric_version": EXTRACTOR_RUBRIC_VERSION,
        "record_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
        "manifest_sha256": str(availability.get("manifest_sha256") or "missing"),
    }


def _transcript_for_video(
    *,
    packet_id: str,
    index: int,
    raw_video: object,
    file_id: str,
    preserved: dict,
    captured_at: str | None,
) -> TranscriptInput | None:
    """Normalize one video row into a ``TranscriptInput``, or ``None`` when it has no
    captured subtitles to extract. MAY RAISE ``ValueError`` for a malformed claim
    (blank cues, a bad timestamp, a transcript/hash mismatch) -- isolated to THIS
    video by the caller so one corrupt sibling never drops the rest of the batch."""
    if not isinstance(raw_video, dict):
        raise ValueError(f"TikTok batch packet {packet_id} video {index} is not an object")
    video_id = str(raw_video.get("video_id") or "").strip()
    if not video_id:
        raise ValueError(f"TikTok batch packet {packet_id} video {index} lacks video_id")
    subtitles = raw_video.get("subtitles")
    if not isinstance(subtitles, dict):
        return None
    if subtitles.get("posture") != "source_native_webvtt_captured":
        return None
    cues = _normalized_cues(subtitles.get("cues"))
    if not cues:
        raise ValueError(f"TikTok video {video_id} claims captured subtitles without cues")
    transcript_text = subtitles.get("transcript_text")
    if not isinstance(transcript_text, str) or not transcript_text.strip():
        raise ValueError(f"TikTok video {video_id} captured transcript lacks text")
    transcript_sha = str(subtitles.get("transcript_text_sha256") or "").strip()
    if not transcript_sha:
        raise ValueError(f"TikTok video {video_id} captured transcript lacks text sha256")
    actual_transcript_sha = hashlib.sha256(transcript_text.encode("utf-8")).hexdigest()
    if actual_transcript_sha != transcript_sha:
        raise ValueError(f"TikTok video {video_id} transcript text sha256 mismatch")
    if "\n".join(cue["text"] for cue in cues) != transcript_text:
        raise ValueError(f"TikTok video {video_id} transcript text does not match its cues")
    source_key = f"{packet_id}:tiktok:{video_id}:{transcript_sha}"
    raw_ref = SilverRawRef(
        packet_id=packet_id,
        slice_id="tiktok_batch_admission_01",
        file_id=file_id,
        relative_packet_path=str(preserved.get("relative_packet_path") or "") or None,
        sha256=str(preserved.get("sha256") or "") or None,
        hash_basis="raw_stored_bytes",
        anchor=SilverAnchor(kind="json_pointer", value=f"/videos/{index}/subtitles"),
        relation="consumed",
    )
    lineage = build_transcript_source_lineage(
        namespace="tiktok",
        source_surface=TIKTOK_BATCH_CAPTURE_SURFACE,
        video_id=video_id,
        raw_ref=raw_ref,
        captured_at=captured_at,
    )
    return TranscriptInput(
        video_id=video_id,
        transcript_anchor=packet_id,
        transcript_source="asr",
        cues=cues,
        source_lineage=lineage,
        transcript_source_key=source_key,
        source_route=_SOURCE_ROUTE,
    )


def _transcripts_for_packet(data_root, packet_id: str) -> tuple[list[TranscriptInput], list[dict]]:
    """Normalize one committed TikTok batch packet into its transcripts.

    MAY RAISE on a packet-structural corruption (missing/unreadable/invalid batch
    capture JSON, no videos list) -- the caller isolates per packet, matching the
    YouTube/IG runners. A malformed SINGLE video (bad cue timestamp, blank text, a
    transcript/hash mismatch) is isolated to that video only: it comes back as a
    discovery-failure entry alongside its siblings' valid transcripts, so one
    corrupt video in a multi-video batch never drops or blocks the rest.
    """
    loaded = data_root.load_raw_packet(packet_id)
    manifest = loaded.manifest
    if manifest.get("source_surface") != TIKTOK_BATCH_CAPTURE_SURFACE:
        return [], []

    files = _file_paths(manifest)
    file_id = _batch_file_id(files)
    if file_id is None:
        raise ValueError(f"TikTok batch packet {packet_id} has no preserved batch capture JSON")
    body = loaded.bodies.get(file_id)
    if body is None:
        raise ValueError(f"TikTok batch packet {packet_id} batch capture body is absent")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"TikTok batch packet {packet_id} batch capture JSON is invalid") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("videos"), list):
        raise ValueError(f"TikTok batch packet {packet_id} has no videos list")

    preserved = _preserved_by_id(manifest)[file_id]
    captured_at = str(payload.get("capture_timestamp") or "") or None
    transcripts: list[TranscriptInput] = []
    discovery_failures: list[dict] = []
    for index, raw_video in enumerate(payload["videos"]):
        try:
            transcript = _transcript_for_video(
                packet_id=packet_id,
                index=index,
                raw_video=raw_video,
                file_id=file_id,
                preserved=preserved,
                captured_at=captured_at,
            )
        except Exception as exc:  # noqa: BLE001 - isolate one malformed sibling video
            video_id = (
                str(raw_video.get("video_id") or "").strip() if isinstance(raw_video, dict) else ""
            )
            discovery_failures.append(
                {
                    "packet_id": packet_id,
                    "video_id": video_id or f"video_index_{index}",
                    "status": "discovery_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
            continue
        if transcript is not None:
            transcripts.append(transcript)
    return transcripts, discovery_failures


def _result_identity(transcript: TranscriptInput) -> dict:
    return {
        "anchor": transcript.transcript_anchor,
        "video_id": transcript.video_id,
        "transcript_source_key": transcript.transcript_source_key,
        "source_route": transcript.source_route,
    }


def run_extraction(
    *,
    data_root,
    transport,
    provider,
    model: str,
    api_key: str,
    max_tokens: int = 2048,
) -> list[dict]:
    """Extract all pending TikTok transcript mentions with per-item isolation."""
    results: list[dict] = []
    results.extend(reconcile_availability_per_packet(data_root))
    for item in pickup(
        data_root,
        ack_namespace=_ACK_NAMESPACE,
        obligation_fn=lambda packet_id: _packet_obligation(data_root, packet_id, model),
        source_family=_SOURCE_FAMILY,
        reconcile=False,
    ):
        packet_id = item.raw_anchor
        try:
            transcripts, discovery_failures = _transcripts_for_packet(data_root, packet_id)
        except Exception as exc:  # noqa: BLE001 - isolate one corrupt packet
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
        if discovery_failures:
            # A malformed sibling never blocks or drops the rest of the batch (it is
            # isolated to its own status entry above), but the packet as a whole must
            # stay unacknowledged so the damaged video keeps re-surfacing for repair.
            results.extend(discovery_failures)
            packet_complete = False
        for transcript in transcripts:
            identity = _result_identity(transcript)
            try:
                record_id = mentions_record_id(transcript, model)
                completion_evidence = {
                    "kind": "record_set_complete",
                    "raw_anchor": packet_id,
                    "completion_lane": PRODUCT_MENTIONS_SET_LANE,
                    "record_id": record_id,
                    "video_id": transcript.video_id,
                }
                if data_root.is_record_set_complete(
                    subtree="derived",
                    raw_anchor=packet_id,
                    record_id=record_id,
                    completion_lane=PRODUCT_MENTIONS_SET_LANE,
                ):
                    results.append({**identity, "status": "skipped_done"})
                    evidence.append(completion_evidence)
                    continue
                member_path = data_root.record_path(
                    subtree="derived",
                    raw_anchor=packet_id,
                    lane=PRODUCT_MENTIONS_LANE,
                    record_id=record_id,
                )
                if member_path.exists():
                    results.append({**identity, "status": "partial_needs_cleanup"})
                    packet_complete = False
                    continue
                paths = extract_products_into_lake(
                    data_root=data_root,
                    transcript=transcript,
                    transport=transport,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    record_id=record_id,
                    max_tokens=max_tokens,
                )
                written = next(iter(paths.values()), None)
                results.append(
                    {
                        **identity,
                        "status": "extracted",
                        "path": str(written) if written is not None else None,
                    }
                )
                evidence.append(completion_evidence)
            except Exception as exc:  # noqa: BLE001 - isolate one transcript
                results.append(
                    {**identity, "status": "failed", "error": f"{type(exc).__name__}: {exc}"[:200]}
                )
                packet_complete = False

        if packet_complete:
            if not evidence:
                evidence = [{"kind": "no_extractable_transcripts", "raw_anchor": packet_id}]
            outcome = ack_packet(data_root, item, evidence, ack_namespace=_ACK_NAMESPACE)
            if outcome != "acked":
                results.append({"packet_id": packet_id, "status": "ack_failed", "error": outcome})
    return results
