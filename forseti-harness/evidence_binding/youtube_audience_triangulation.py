"""Build one YouTube platform-account audience bundle from admitted capture evidence."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


EVIDENCE_BUNDLE_SCHEMA_VERSION = "creator_audience_evidence_bundle_v1"
_WS = re.compile(r"\s+")


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _stable_id(prefix: str, *parts: object, size: int = 20) -> str:
    payload = "\0".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:size]}"


def _index(
    rows: Sequence[Mapping[str, Any]], *, kind: str
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        video_id = str(row.get("video_id") or "").strip()
        if not video_id:
            raise ValueError(f"YouTube {kind} evidence lacks video_id")
        if video_id in indexed:
            raise ValueError(f"duplicate YouTube {kind} evidence for {video_id}")
        indexed[video_id] = row
    return indexed


def build_youtube_creator_audience_evidence_bundle(
    *,
    creator_id: str,
    profile_subject_id: str,
    primary_raw_anchor: str,
    channel_id: str,
    selected_video_ids: Sequence[str],
    watch_records: Sequence[Mapping[str, Any]],
    transcript_records: Sequence[Mapping[str, Any]],
    question: str,
    evidence_cutoff: str,
    method_deck_path: str,
    method_deck_sha256: str,
) -> dict[str, Any]:
    """Assemble one deterministic bundle from 1-8 assessment-selected YouTube videos."""

    required = (
        creator_id,
        profile_subject_id,
        primary_raw_anchor,
        channel_id,
        question,
        evidence_cutoff,
        method_deck_path,
        method_deck_sha256,
    )
    if any(not value.strip() for value in required):
        raise ValueError(
            "creator, subject, anchor, channel, question, cutoff, and method binding are required"
        )
    normalized_creator = creator_id.strip().casefold()
    if not normalized_creator.startswith("youtube:@"):
        normalized_creator = f"youtube:@{normalized_creator.lstrip('@')}"

    requested_ids = [str(video_id).strip() for video_id in selected_video_ids]
    if not requested_ids or any(not video_id for video_id in requested_ids):
        raise ValueError("INCOMPLETE_AUDIENCE_EVIDENCE: selected YouTube videos are required")
    if len(requested_ids) != len(set(requested_ids)):
        raise ValueError("selected YouTube video ids must be unique")
    if len(requested_ids) > 8:
        raise ValueError("YouTube audience adapter accepts at most 8 selected videos")

    watches = _index(watch_records, kind="watch")
    transcripts = _index(transcript_records, kind="transcript")
    expected = set(requested_ids)
    if set(watches) != expected or set(transcripts) != expected:
        raise ValueError(
            "INCOMPLETE_AUDIENCE_EVIDENCE: YouTube selected/watch/transcript video sets differ"
        )

    transcript_evidence: list[dict[str, Any]] = []
    comment_evidence: list[dict[str, Any]] = []
    cluster_members: dict[str, list[str]] = {}
    cluster_text: dict[str, str] = {}
    for video_id in requested_ids:
        watch = watches[video_id]
        if str(watch.get("channel_id") or "") != channel_id:
            raise ValueError(
                f"YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH: video {video_id} watch channel differs"
            )
        transcript = transcripts[video_id]
        cues = transcript.get("cues")
        if not isinstance(cues, list) or not cues:
            raise ValueError(
                f"INCOMPLETE_AUDIENCE_EVIDENCE: video {video_id} has no transcript cues"
            )
        item_transcript_count = 0
        for cue_index, cue in enumerate(cues):
            if not isinstance(cue, Mapping):
                continue
            text = str(cue.get("text") or "").strip()
            if not text:
                continue
            item_transcript_count += 1
            transcript_evidence.append(
                {
                    "evidence_id": _stable_id(
                        "ytte", normalized_creator, video_id, cue_index, text
                    ),
                    "creator_id": normalized_creator,
                    "source_item_id": video_id,
                    "video_id": video_id,
                    "text": text,
                    "start_ms": cue.get("start_ms"),
                    "end_ms": cue.get("end_ms"),
                    "source_pointer": (
                        f"{transcript.get('source_pointer')}#/cues/{cue_index}"
                    ),
                    "transcript_source_kind": transcript.get("source_kind"),
                    "transcript_source_anchor": transcript.get("source_anchor"),
                    "transcript_source_sha256": transcript.get("source_sha256"),
                }
            )
        if item_transcript_count == 0:
            raise ValueError(
                f"INCOMPLETE_AUDIENCE_EVIDENCE: video {video_id} has no usable transcript cues"
            )

        comments = watch.get("comments")
        if not isinstance(comments, list) or not comments:
            raise ValueError(
                f"INCOMPLETE_AUDIENCE_EVIDENCE: video {video_id} has no captured comments"
            )
        item_comment_count = 0
        for source_index, raw in enumerate(comments):
            if not isinstance(raw, Mapping):
                continue
            text = str(raw.get("text") or "").strip()
            if not text:
                continue
            item_comment_count += 1
            comment_id = str(
                raw.get("comment_id") or f"source_order:{source_index + 1}"
            )
            evidence_id = _stable_id(
                "ytce", normalized_creator, video_id, comment_id, text
            )
            cluster_id = _stable_id(
                "ytcc", _WS.sub(" ", text.casefold()).strip(), size=16
            )
            cluster_members.setdefault(cluster_id, []).append(evidence_id)
            cluster_text[cluster_id] = text
            comment_evidence.append(
                {
                    "evidence_id": evidence_id,
                    "creator_id": normalized_creator,
                    "source_item_id": video_id,
                    "video_id": video_id,
                    "comment_id": comment_id,
                    "text": text,
                    "source_order": source_index,
                    "source_pointer": (
                        f"{watch.get('source_pointer')}#/packet/comments/{source_index}"
                    ),
                    "duplicate_cluster_id": cluster_id,
                    "comment_likes": raw.get("like_count"),
                    "comment_like_rank_within_captured": None,
                    "temporal_alignment": "unproven",
                    "comment_attention_record_id": None,
                    "watch_packet_id": watch.get("capture_packet_id"),
                    "watch_packet_sha256": watch.get("source_sha256"),
                }
            )
        if item_comment_count == 0:
            raise ValueError(
                f"INCOMPLETE_AUDIENCE_EVIDENCE: video {video_id} has no usable comments"
            )

    core: dict[str, Any] = {
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "creator_id": normalized_creator,
        "profile_subject_kind": "platform_account",
        "profile_subject_id": profile_subject_id.strip(),
        "platform_scope": "youtube",
        "raw_anchor": primary_raw_anchor.strip(),
        "question": question.strip(),
        "evidence_cutoff": evidence_cutoff.strip(),
        "method_deck_path": method_deck_path.strip(),
        "method_deck_sha256": method_deck_sha256.strip(),
        "capture_scope": {
            "selected_source_item_ids": requested_ids,
            "selected_video_ids": requested_ids,
            "selected_item_count": len(requested_ids),
            "item_selection_policy": "assessment_selected_explicit_complete_videos_v1",
            "comment_selection_posture": (
                "all_captured_top_level_comments_from_selected_watch_packets"
            ),
            "limitations": [
                "not_platform_wide_comment_census",
                "selected_comments_follow_source_default_order_and_may_be_truncated",
                "youtube_comment_engagement_temporal_alignment_unproven",
                "caption_or_asr_transcripts_are_source-specific_not_channel-wide",
            ],
        },
        "transcript_evidence": sorted(
            transcript_evidence, key=lambda row: row["evidence_id"]
        ),
        "comment_evidence": sorted(comment_evidence, key=lambda row: row["evidence_id"]),
        "exact_duplicate_clusters": [
            {
                "cluster_id": cluster_id,
                "representative_text": cluster_text[cluster_id],
                "evidence_ids": sorted(evidence_ids),
                "multiplicity": len(evidence_ids),
            }
            for cluster_id, evidence_ids in sorted(cluster_members.items())
        ],
        "source_refs": {
            "primary_assessment_packet_id": primary_raw_anchor.strip(),
            "youtube_channel_id": channel_id.strip(),
            "watch_packets": [
                {
                    "video_id": video_id,
                    "packet_id": watches[video_id].get("capture_packet_id"),
                    "source_sha256": watches[video_id].get("source_sha256"),
                }
                for video_id in requested_ids
            ],
            "transcripts": [
                {
                    "video_id": video_id,
                    "source_kind": transcripts[video_id].get("source_kind"),
                    "source_anchor": transcripts[video_id].get("source_anchor"),
                    "source_record_id_or_none": transcripts[video_id].get(
                        "source_record_id"
                    ),
                    "source_sha256": transcripts[video_id].get("source_sha256"),
                }
                for video_id in requested_ids
            ],
        },
        "judgment_status": "not_evaluated",
    }
    bundle_hash = f"sha256:{hashlib.sha256(_canonical_bytes(core)).hexdigest()}"
    core["bundle_hash"] = bundle_hash
    core["bundle_id"] = _stable_id("caeb", primary_raw_anchor, bundle_hash)
    core["serialized_utf8_bytes"] = len(_canonical_bytes(core))
    return core


__all__ = [
    "EVIDENCE_BUNDLE_SCHEMA_VERSION",
    "build_youtube_creator_audience_evidence_bundle",
]
