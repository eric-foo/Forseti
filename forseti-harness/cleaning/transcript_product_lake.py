"""Driver: run Pass 1 over a transcript and persist the mentions into the Data Lake.

Mirrors `ecr/lake.py` (read/derive/append), adapted for the LLM extractor: take a
TranscriptInput, run `extract_transcript_products`, and append the validated mentions as a
Silver Vault ``TextObservationSet`` at
``derived/<transcript_anchor>/transcript_product_mentions_silver/<record_id>`` with an
all-or-nothing completion marker (so the runner can skip already-extracted transcripts).

Lives in `cleaning/` because it invokes the LLM extractor. Also owns the source->cues
normalizers (ASR derived record / caption json3), so the runner stays a thin orchestrator.

Spec: youtube_transcript_product_extraction_spec_v0.md (medallion silver lane; daemon-ready).
"""

from __future__ import annotations

import hashlib
import json
import math
import re

from cleaning.transcript_product_extractor import (
    EXTRACTOR_RUBRIC_VERSION,
    TranscriptExtractionResult,
    TranscriptInput,
    extract_transcript_products,
    transcript_measurement,
)
from data_lake.silver_lineage import (
    SilverDerivedRef,
    SilverLineage,
    SilverLineageLimitation,
    SilverRawRef,
    SilverSourceObject,
    validate_silver_lineage,
)
from data_lake.silver_record import (
    CONTENT_HASH_BASIS,
    SILVER_VAULT_RECORD_SCHEMA_VERSION,
    TEXT_OBSERVATION_SET_PAYLOAD_KIND,
    append_silver_record_set,
    silver_content_hash,
)

# Current Silver-envelope lane + its non-authoritative completion-marker lane.
PRODUCT_MENTIONS_LANE = "transcript_product_mentions_silver"
PRODUCT_MENTIONS_SET_LANE = "transcript_product_mentions_completion"
LEGACY_PRODUCT_MENTIONS_LANE = "silver__cleaning__product_mentions"
LEGACY_PRODUCT_MENTIONS_SET_LANE = "silver__cleaning__product_mentions__set"

# Producer identity stamped into the Silver lineage block of every product-mention
# record (the producer is this Pass-1 extractor; its schema version is the rubric).
PRODUCT_MENTIONS_PRODUCER_ID = "cleaning.transcript_product_extractor"

# Record-SHAPE and durable-identity schema token. V3 binds explicit unknown-time grammar; V2 bound identity
# to the exact product-mention policy fingerprint. Prior records re-surface so the
# current-policy record can be written under its distinct identity.
PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION = "transcript_product_mentions_record_v3"

def product_mentions_policy_fingerprint(
    policy_version: str,
    record_schema_version: str = PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
) -> str:
    """Stable identity shared by record ids, payloads, and pickup obligations."""
    return hashlib.sha256(
        f"{PRODUCT_MENTIONS_PRODUCER_ID}\0{policy_version}\0{record_schema_version}".encode(
            "utf-8"
        )
    ).hexdigest()


PRODUCT_MENTIONS_POLICY_FINGERPRINT = product_mentions_policy_fingerprint(
    EXTRACTOR_RUBRIC_VERSION
)


def build_transcript_source_lineage(
    *,
    namespace: str,
    source_surface: str,
    video_id: str,
    derived_ref: SilverDerivedRef | None = None,
    raw_ref: SilverRawRef | None = None,
    limitations: list[SilverLineageLimitation] | None = None,
    captured_at: str | None = None,
) -> SilverLineage:
    """Assemble the Silver lineage block for a product-mention record from the exact
    transcript source the runner discovered. Stamps this producer's identity and the
    transcript's source-local identity (``namespace + kind=transcript + native_id``);
    the caller supplies exactly one of a ``derived_ref`` (ASR -> the consumed
    ``transcript_asr`` derived record) or a ``raw_ref`` (caption -> the json3
    preserved file). Validated on construction (fail-closed)."""
    return SilverLineage(
        producer_id=PRODUCT_MENTIONS_PRODUCER_ID,
        producer_schema_version=EXTRACTOR_RUBRIC_VERSION,
        source_surface=source_surface,
        source_object=SilverSourceObject(namespace=namespace, kind="transcript", native_id=video_id),
        captured_at=captured_at,
        raw_refs=[raw_ref] if raw_ref is not None else [],
        derived_refs=[derived_ref] if derived_ref is not None else [],
        lineage_limitations=list(limitations or []),
    )


def cues_from_asr_record(record: dict) -> list[dict]:
    """Cues from a transcript_asr derived record (already {start_ms,end_ms,text})."""
    cues = record.get("cues")
    return cues if isinstance(cues, list) else []


def cues_from_json3(raw: bytes) -> list[dict]:
    """Parse caption json3 into ms-timed cues, PRESERVING timing.

    Unlike `flatten_json3` (which drops timing for a readable view), this keeps each event's
    start/end so caption-sourced mentions still get a timestamp anchor (CE5). Rolling
    duplicate lines are collapsed (consecutive identical text), matching the flattener.
    """
    # Fail-closed: an untrusted/corrupt json3 body yields [] (the runner then skips it),
    # never an exception that could abort the batch.
    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        return []
    events = data.get("events", []) if isinstance(data, dict) else []
    cues: list[dict] = []
    prev: str | None = None
    for event in events:
        if not isinstance(event, dict):
            continue
        segs = event.get("segs") or []
        if not isinstance(segs, list) or not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs if isinstance(s, dict)).strip()
        if not text or text == prev:
            continue
        # finite-guard, not just type-guard: json.loads accepts bare NaN/Infinity, which ARE
        # floats (so isinstance passes) but raise on int() — guard them or the documented
        # fail-closed contract breaks. Negative duration is clamped so end_ms >= start_ms.
        raw_start = event.get("tStartMs", 0)
        start = int(raw_start) if isinstance(raw_start, (int, float)) and math.isfinite(raw_start) else 0
        duration = event.get("dDurationMs")
        end = (
            start + max(0, int(duration))
            if isinstance(duration, (int, float)) and math.isfinite(duration)
            else start
        )
        cues.append({"start_ms": start, "end_ms": end, "text": text})
        prev = text
    return cues


def mentions_record_id(
    transcript: TranscriptInput,
    model: str,
    *,
    policy_fingerprint_sha256: str = PRODUCT_MENTIONS_POLICY_FINGERPRINT,
) -> str:
    """Deterministic per transcript source/content/model/policy.

    The model token is bounded so the id stays within the lake's 128-char _SAFE_SEGMENT limit
    for any model string; the full model is still recorded in the record payload + provenance.
    """
    token = re.sub(r"[^A-Za-z0-9_-]", "-", str(model))[:48]
    if re.fullmatch(r"[0-9a-f]{64}", policy_fingerprint_sha256) is None:
        raise ValueError("policy_fingerprint_sha256 must be lowercase 64-hex")
    digest_input = (
        f"{policy_fingerprint_sha256}\x00{transcript.joined_text}"
    )
    if transcript.transcript_source_key:
        digest_input = f"{transcript.transcript_source_key}\x00{digest_input}"
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
    return f"mentions_{token}__{digest[:16]}__p{policy_fingerprint_sha256[:12]}.json"


def _product_mentions_payload(
    *,
    transcript: TranscriptInput,
    result: TranscriptExtractionResult,
    model: str,
    extraction_backend: str,
    policy_version: str,
    policy_fingerprint_sha256: str,
    extraction_provenance: dict | None = None,
) -> dict:
    if transcript.source_lineage is None:
        raise ValueError("Product-mention Silver output requires exact transcript lineage")
    lineage = validate_silver_lineage(transcript.source_lineage)
    lineage_fields = lineage.to_record_fields()
    recorded_at = lineage_fields.get("captured_at")
    if not isinstance(recorded_at, str) or not recorded_at.strip():
        raise ValueError(
            "Product-mention Silver output requires the transcript packet capture time "
            "as recorded_at; it must not be substituted for observed_at."
        )
    evidence_refs = [*lineage_fields["raw_refs"], *lineage_fields["derived_refs"]]
    if not evidence_refs:
        raise ValueError("Product-mention Silver output requires source-backed evidence_refs")
    rows = []
    for mention in result.mentions:
        body = mention.model_dump(mode="json")
        quote = body["source_pointer"]
        rows.append(
            {
                "row_id": body["mention_id"],
                "text_artifact_type": "transcript_quote",
                "text_value": quote,
                "text_ref": None,
                "text_hash": f"sha256:{hashlib.sha256(quote.encode('utf-8')).hexdigest()}",
                "text_posture": {"kind": "observed", "reason_code": None, "reason_detail": None},
                "coverage_window": {"start": None, "end": None},
                "source_span": {"start_ms": body["start_ms"], "end_ms": body["end_ms"]},
                "mention": body,
            }
        )
    subject_namespace = (
        lineage.source_object.namespace if lineage.source_object is not None else "unknown"
    )
    record = {
        "record_id": "",
        "raw_anchor": transcript.transcript_anchor,
        "lane_namespace": PRODUCT_MENTIONS_LANE,
        "producer_id": PRODUCT_MENTIONS_PRODUCER_ID,
        "schema_version": SILVER_VAULT_RECORD_SCHEMA_VERSION,
        "producer_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
        "content_hash": "",
        "content_hash_basis": CONTENT_HASH_BASIS,
        "record_kind": "observation",
        "payload_kind": TEXT_OBSERVATION_SET_PAYLOAD_KIND,
        "producer_row_kind": "transcript_product_mentions",
        "record_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION,
        "source_family": "social_media",
        **lineage_fields,
        "payload": {
            "observation": {
                "subject": {
                    "ref_type": "entity_key",
                    "ref": {
                        "namespace": subject_namespace,
                        "kind": "public_content_object",
                        "native_id": transcript.video_id,
                    },
                },
                "effective_interval": {
                    "start": None,
                    "start_precision": "unknown",
                    "unknown_reason": (
                        "The transcript source does not carry a source-effective "
                        "observation time."
                    ),
                },
                "recorded_at": recorded_at,
                "evidence_refs": evidence_refs,
                "limitations": [
                    "Source-effective time is unknown; recorded_at is the transcript "
                    "packet capture time and is not observed_at."
                ],
                "observation_set_kind": "transcript_product_mentions",
                "policy_version": policy_version,
                "policy_fingerprint_sha256": policy_fingerprint_sha256,
                "row_count": len(rows),
                "rows": rows,
            }
        },
        "provenance": {
            "transcript_source_key": transcript.transcript_source_key,
            "source_route": transcript.source_route,
            "asr_record_id": transcript.asr_record_id,
            "transcript_source": transcript.transcript_source,
            "model": model,
            "rubric_version": policy_version,
            "extraction_backend": extraction_backend,
            "rejected_count": len(result.rejected),
            **({"extraction_provenance": dict(extraction_provenance)} if extraction_provenance else {}),
        },
        "non_claims": [
            "not product identity resolution",
            "not a creator or product verdict",
            "not proof of transcript completeness",
        ],
    }
    return record


def write_product_mentions_result_into_lake(
    *,
    data_root,
    transcript: TranscriptInput,
    result: TranscriptExtractionResult,
    model: str,
    record_id: str | None = None,
    policy_version: str = EXTRACTOR_RUBRIC_VERSION,
    policy_fingerprint_sha256: str | None = None,
    extraction_backend: str,
    extraction_provenance: dict | None = None,
) -> dict[str, "object"]:
    """Append an already-validated product extraction result to the silver lane.

    Provider-backed extraction and operator-assisted extraction share this write boundary so
    downstream projection reads one product-mention record shape. Re-appending the same
    record_id is refused by the lake (write-once); callers check completion before writing.
    """
    policy_fingerprint_sha256 = policy_fingerprint_sha256 or product_mentions_policy_fingerprint(
        policy_version
    )
    rid = record_id or mentions_record_id(
        transcript,
        model,
        policy_fingerprint_sha256=policy_fingerprint_sha256,
    )
    record = _product_mentions_payload(
        transcript=transcript,
        result=result,
        model=model,
        extraction_backend=extraction_backend,
        policy_version=policy_version,
        policy_fingerprint_sha256=policy_fingerprint_sha256,
        extraction_provenance=extraction_provenance,
    )
    record["record_id"] = rid
    record["content_hash"] = f"sha256:{silver_content_hash(record)}"
    return append_silver_record_set(
        data_root,
        raw_anchor=transcript.transcript_anchor,
        record_id=rid,
        records={PRODUCT_MENTIONS_LANE: record},
        completion_lane=PRODUCT_MENTIONS_SET_LANE,
    )


def extract_products_into_lake(
    *,
    data_root,
    transcript: TranscriptInput,
    transport,
    provider,
    model: str,
    api_key: str,
    record_id: str | None = None,
    policy_version: str = EXTRACTOR_RUBRIC_VERSION,
    policy_fingerprint_sha256: str | None = None,
    max_tokens: int = 2048,
) -> dict[str, "object"]:
    """Run Pass 1 for one transcript and append the silver mentions record-set.

    Returns the written member paths. Re-appending the same record_id is refused by the lake
    (write-once); the runner avoids that by checking `is_record_set_complete` first.
    """
    with transcript_measurement(transcript, "transcript_products_into_lake", {
        "provider": str(provider), "model": model, "max_tokens": max_tokens,
        "policy_version": policy_version,
        "policy_fingerprint_sha256": policy_fingerprint_sha256 or product_mentions_policy_fingerprint(policy_version),
    }) as measurement:
        result = extract_transcript_products(
            transcript,
            transport=transport,
            provider=provider,
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
        )
        with measurement.stage("lake_write"):
            written = write_product_mentions_result_into_lake(
                data_root=data_root,
                transcript=transcript,
                result=result,
                model=model,
                record_id=record_id,
                policy_version=policy_version,
                policy_fingerprint_sha256=policy_fingerprint_sha256,
                extraction_backend="provider_api",
            )
        # Measurement reads only: the validated writer and authoritative payload stay unchanged.
        # A readback failure is a failed measurement oracle, not a failed product write.
        with measurement.stage("persisted_verify"):
            try:
                path = written[PRODUCT_MENTIONS_LANE]
                fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
                expected = data_root.read_record_set_member_sha256(
                    subtree="derived", raw_anchor=transcript.transcript_anchor,
                    record_id=path.name, completion_lane=PRODUCT_MENTIONS_SET_LANE,
                    member_lane=PRODUCT_MENTIONS_LANE,
                )
                if fingerprint != expected:
                    raise ValueError("persisted member hash differs from completion marker")
            except Exception as exc:
                measurement.set_quality("failed", "silver_validated_write_and_marker_sha256_v1")
                measurement.error(f"persisted_verify:{type(exc).__name__}")
            else:
                measurement.set_quality("passed", "silver_validated_write_and_marker_sha256_v1",
                                        output_fingerprint=fingerprint)
        return written
