"""Prepare and submit one YouTube creator-audience Judgment from captured evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cleaning.transcript_product_lake import cues_from_asr_record, cues_from_json3
from data_lake.creator_registry import (
    extract_youtube_assessment_packet_identity,
    resolve_youtube_profile_subject_id,
)
from data_lake.root import DataLakeRoot, DataLakeRootError, raw_shard
from evidence_binding.tiktok_audience_triangulation import (
    ASSEMBLY_RECEIPT_LANE,
    build_assembly_receipt,
)
from evidence_binding.youtube_audience_triangulation import (
    build_youtube_creator_audience_evidence_bundle,
)
from judgment.creator_audience import (
    METHOD_DECK_RELATIVE_PATH,
    build_creator_audience_prompt,
    load_method_deck,
)
from runners.run_tiktok_creator_audience_triangulation import (
    _write_new,
    _write_new_json,
    submit_subscription_judgment,
)
from youtube_capture.behavioral_projection import (
    ASR_LANE,
    ASR_SET_LANE,
    WATCH_METADATA_SURFACE,
    metadata_packet_for_video,
    transcript_sources_for_video,
)


_ASSESSMENT_JSON = "youtube_creator_assessment.json"
_WATCH_CAPTURE_JSON = "youtube_watch_capture.json"


def _preserved_body(
    data_root: DataLakeRoot, packet_id: str, *, suffix: str
) -> tuple[bytes, Mapping[str, Any], str]:
    loaded = data_root.load_raw_packet(packet_id)
    matches = [
        row
        for row in loaded.manifest.get("preserved_files", [])
        if isinstance(row, Mapping)
        and str(row.get("relative_packet_path") or "").replace("\\", "/").endswith(suffix)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"packet {packet_id} requires exactly one preserved file ending {suffix!r}"
        )
    row = matches[0]
    file_id = str(row.get("file_id") or "")
    body = loaded.bodies.get(file_id)
    if body is None:
        raise ValueError(f"packet {packet_id} preserved body is absent: {suffix}")
    digest = hashlib.sha256(body).hexdigest()
    if digest != row.get("sha256"):
        raise ValueError(f"packet {packet_id} preserved body hash changed: {suffix}")
    relative = str(row.get("relative_packet_path") or "").replace("\\", "/")
    pointer = f"raw/{raw_shard(packet_id)}/{packet_id}/{relative}"
    return body, row, pointer


def _assessment(
    data_root: DataLakeRoot, packet_id: str
) -> tuple[dict[str, Any], dict[str, str]]:
    identity = extract_youtube_assessment_packet_identity(data_root, packet_id)
    body, _row, _pointer = _preserved_body(
        data_root, packet_id, suffix=_ASSESSMENT_JSON
    )
    value = json.loads(body.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("YouTube assessment body must be an object")
    return value, identity


def _watch_record(
    data_root: DataLakeRoot,
    *,
    video_id: str,
    channel_id: str,
    packet_id: str | None = None,
) -> dict[str, Any]:
    if packet_id is None:
        packet = metadata_packet_for_video(data_root, video_id)
    else:
        loaded = data_root.load_raw_packet(packet_id)
        if (
            loaded.manifest.get("source_family") != "youtube"
            or loaded.manifest.get("source_surface") != WATCH_METADATA_SURFACE
        ):
            raise ValueError(
                f"explicit YouTube watch packet {packet_id} has unsupported source surface"
            )
        body, _row, _pointer = _preserved_body(
            data_root, packet_id, suffix=_WATCH_CAPTURE_JSON
        )
        payload = json.loads(body.decode("utf-8-sig"))
        if (
            not isinstance(payload, Mapping)
            or payload.get("platform_video_id") != video_id
            or not isinstance(payload.get("packet"), Mapping)
        ):
            raise ValueError(
                f"explicit YouTube watch packet {packet_id} does not bind video {video_id}"
            )
        packet = dict(payload["packet"])
        packet["capture_packet_id"] = packet_id
        packet.setdefault("capture_timestamp", payload.get("capture_timestamp"))
    if packet is None:
        raise ValueError(
            f"INCOMPLETE_AUDIENCE_EVIDENCE: no YouTube watch packet for {video_id}"
        )
    packet_id = str(packet.get("capture_packet_id") or "")
    channel = packet.get("channel") if isinstance(packet.get("channel"), Mapping) else {}
    if channel.get("channel_id") != channel_id:
        raise ValueError(
            f"YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH: video {video_id} watch packet "
            f"belongs to {channel.get('channel_id')!r}, not {channel_id!r}"
        )
    comments = packet.get("comments")
    if not isinstance(comments, list) or not comments:
        raise ValueError(
            f"INCOMPLETE_AUDIENCE_EVIDENCE: no captured comments for {video_id}"
        )
    body, row, pointer = _preserved_body(
        data_root, packet_id, suffix=_WATCH_CAPTURE_JSON
    )
    if hashlib.sha256(body).hexdigest() != row.get("sha256"):
        raise ValueError(f"YouTube watch body hash changed for {video_id}")
    return {
        "video_id": video_id,
        "channel_id": channel_id,
        "capture_packet_id": packet_id,
        "capture_timestamp": packet.get("capture_timestamp"),
        "comments": comments,
        "source_pointer": pointer,
        "source_sha256": f"sha256:{row['sha256']}",
    }


def _source_rank(source: Mapping[str, Any]) -> tuple[int, str, str]:
    kind = str(source.get("source_kind") or "")
    caption_kind = str(source.get("caption_kind") or "")
    rank = 0 if kind == "caption" and caption_kind == "manual" else 1 if kind == "caption" else 2
    return (
        rank,
        str(source.get("capture_timestamp") or ""),
        str(source.get("transcript_anchor") or ""),
    )


def _selected_transcript_source(
    data_root: DataLakeRoot, *, video_id: str, packet_id: str | None = None
) -> Mapping[str, Any]:
    if packet_id is not None:
        loaded = data_root.load_raw_packet(packet_id)
        if loaded.manifest.get("source_family") != "youtube":
            raise ValueError(
                f"explicit YouTube transcript packet {packet_id} has unsupported source family"
            )
        surface = loaded.manifest.get("source_surface")
        if surface == "youtube_captions":
            return {
                "platform_video_id": video_id,
                "transcript_anchor": packet_id,
                "source_kind": "caption",
                "capture_timestamp": "",
                "extraction_eligible": True,
            }
        if surface == "youtube_audio":
            lane_dir = data_root.lane_dir(
                subtree="derived", raw_anchor=packet_id, lane=ASR_LANE
            )
            records = [
                path.name
                for path in sorted(lane_dir.iterdir())
                if path.is_file()
                and data_root.is_record_set_complete(
                    subtree="derived",
                    raw_anchor=packet_id,
                    record_id=path.name,
                    completion_lane=ASR_SET_LANE,
                )
            ] if lane_dir.is_dir() else []
            if len(records) != 1:
                raise ValueError(
                    f"explicit YouTube audio packet {packet_id} requires exactly one "
                    f"complete ASR record; found {len(records)}"
                )
            return {
                "platform_video_id": video_id,
                "transcript_anchor": packet_id,
                "source_kind": "asr",
                "asr_record_id": records[0],
                "capture_timestamp": "",
                "extraction_eligible": True,
            }
        raise ValueError(
            f"explicit YouTube transcript packet {packet_id} has unsupported surface {surface!r}"
        )
    eligible = [
        source
        for source in transcript_sources_for_video(data_root, video_id)
        if source.get("extraction_eligible") is True
    ]
    if not eligible:
        raise ValueError(
            f"INCOMPLETE_AUDIENCE_EVIDENCE: no complete transcript for {video_id}"
        )
    best_rank = min(_source_rank(source)[0] for source in eligible)
    return max(
        (source for source in eligible if _source_rank(source)[0] == best_rank),
        key=lambda source: _source_rank(source)[1:],
    )


def _transcript_record(
    data_root: DataLakeRoot,
    *,
    video_id: str,
    channel_id: str,
    packet_id: str | None = None,
) -> dict[str, Any]:
    source = _selected_transcript_source(
        data_root, video_id=video_id, packet_id=packet_id
    )
    anchor = str(source.get("transcript_anchor") or "")
    kind = str(source.get("source_kind") or "")
    if kind == "caption":
        metadata_body, _metadata_row, _metadata_pointer = _preserved_body(
            data_root, anchor, suffix="capture_metadata.json"
        )
        metadata = json.loads(metadata_body.decode("utf-8-sig"))
        if (
            not isinstance(metadata, Mapping)
            or metadata.get("platform_video_id") != video_id
            or metadata.get("channel_id") != channel_id
        ):
            raise ValueError(
                f"YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH: caption identity differs for {video_id}"
            )
        body, row, pointer = _preserved_body(data_root, anchor, suffix=".json3")
        cues = cues_from_json3(body)
        record_id = None
    elif kind == "asr":
        record_id = str(source.get("asr_record_id") or "")
        if not record_id or not data_root.is_record_set_complete(
            subtree="derived",
            raw_anchor=anchor,
            record_id=record_id,
            completion_lane=ASR_SET_LANE,
        ):
            raise ValueError(f"incomplete YouTube ASR record for {video_id}")
        path = data_root.record_path(
            subtree="derived",
            raw_anchor=anchor,
            lane=ASR_LANE,
            record_id=record_id,
        )
        body = path.read_bytes()
        record = json.loads(body.decode("utf-8-sig"))
        if not isinstance(record, dict) or record.get("video_id") != video_id:
            raise ValueError(f"YouTube ASR record identity differs for {video_id}")
        metadata_body, _metadata_row, _metadata_pointer = _preserved_body(
            data_root, anchor, suffix="capture_metadata.json"
        )
        metadata = json.loads(metadata_body.decode("utf-8-sig"))
        if (
            not isinstance(metadata, Mapping)
            or metadata.get("platform_video_id") != video_id
            or metadata.get("channel_id") != channel_id
        ):
            raise ValueError(
                f"YOUTUBE_EVIDENCE_ACCOUNT_MISMATCH: ASR identity differs for {video_id}"
            )
        cues = cues_from_asr_record(record)
        pointer = path.relative_to(data_root.path.resolve()).as_posix()
        row = {"sha256": hashlib.sha256(body).hexdigest()}
    else:
        raise ValueError(f"unsupported YouTube transcript source kind: {kind!r}")
    if not cues:
        raise ValueError(
            f"INCOMPLETE_AUDIENCE_EVIDENCE: selected transcript has no cues for {video_id}"
        )
    return {
        "video_id": video_id,
        "source_kind": kind,
        "source_anchor": anchor,
        "source_record_id": record_id,
        "source_pointer": pointer,
        "source_sha256": f"sha256:{row['sha256']}",
        "cues": cues,
    }


def prepare_youtube_subscription_judgment(
    *,
    data_root: DataLakeRoot,
    assessment_packet_id: str,
    creator_id: str,
    profile_subject_id: str,
    video_ids: Sequence[str],
    watch_packet_ids: Mapping[str, str] | None = None,
    transcript_packet_ids: Mapping[str, str] | None = None,
    question: str,
    evidence_cutoff: str,
    bundle_out: Path,
    prompt_out: Path,
) -> dict[str, Any]:
    if bundle_out.resolve() == prompt_out.resolve():
        raise ValueError("bundle_out and prompt_out must be different files")
    assessment, identity = _assessment(data_root, assessment_packet_id)
    expected_creator = f"youtube:@{identity['public_handle']}"
    if creator_id.strip().casefold() != expected_creator:
        raise ValueError(
            f"requested creator {creator_id!r} does not match assessment {expected_creator!r}"
        )
    resolved_subject = resolve_youtube_profile_subject_id(
        data_root=data_root,
        packet_id=assessment_packet_id,
        requested_id=profile_subject_id,
    )
    if resolved_subject != profile_subject_id:
        raise ValueError("requested profile subject does not match YouTube identity")

    selected_rows = assessment.get("selected_video_pages")
    selected = {
        str(row.get("video_id"))
        for row in selected_rows
        if isinstance(row, Mapping) and row.get("video_id")
    } if isinstance(selected_rows, list) else set()
    requested = [str(video_id).strip() for video_id in video_ids]
    if not requested or any(not video_id for video_id in requested):
        raise ValueError("YouTube Judgment requires one or more selected video ids")
    if len(requested) != len(set(requested)):
        raise ValueError("YouTube Judgment selected video ids must be unique")
    outside = sorted(set(requested) - selected)
    if outside:
        raise ValueError(
            f"YouTube Judgment videos are not assessment-selected: {outside!r}"
        )
    for label, packet_ids in (
        ("watch", watch_packet_ids),
        ("transcript", transcript_packet_ids),
    ):
        if packet_ids is not None and set(packet_ids) != set(requested):
            raise ValueError(
                f"explicit YouTube {label} packet map must match selected video ids exactly"
            )

    channel_id = identity["platform_public_account_id"]
    watch_records = [
        _watch_record(
            data_root,
            video_id=video_id,
            channel_id=channel_id,
            packet_id=(watch_packet_ids or {}).get(video_id),
        )
        for video_id in requested
    ]
    transcript_records = [
        _transcript_record(
            data_root,
            video_id=video_id,
            channel_id=channel_id,
            packet_id=(transcript_packet_ids or {}).get(video_id),
        )
        for video_id in requested
    ]
    method_text, method_hash = load_method_deck()
    bundle = build_youtube_creator_audience_evidence_bundle(
        creator_id=creator_id,
        profile_subject_id=profile_subject_id,
        primary_raw_anchor=assessment_packet_id,
        channel_id=channel_id,
        selected_video_ids=requested,
        watch_records=watch_records,
        transcript_records=transcript_records,
        question=question,
        evidence_cutoff=evidence_cutoff,
        method_deck_path=METHOD_DECK_RELATIVE_PATH,
        method_deck_sha256=method_hash,
    )
    _write_new_json(bundle_out, bundle)
    _write_new(
        prompt_out,
        build_creator_audience_prompt(bundle, method_text=method_text) + "\n",
    )

    receipt = build_assembly_receipt(bundle)
    receipt_bytes = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    receipt_path = data_root.record_path(
        subtree="derived",
        raw_anchor=assessment_packet_id,
        lane=ASSEMBLY_RECEIPT_LANE,
        record_id=str(receipt["record_id"]),
    )
    if receipt_path.exists():
        if receipt_path.read_bytes() != receipt_bytes:
            raise ValueError("existing YouTube audience assembly receipt differs")
    else:
        data_root.append_record(
            subtree="derived",
            raw_anchor=assessment_packet_id,
            lane=ASSEMBLY_RECEIPT_LANE,
            record_id=str(receipt["record_id"]),
            data=receipt_bytes,
        )
    return {
        "status": "SUBSCRIPTION_JUDGMENT_REQUIRED",
        "creator_id": bundle["creator_id"],
        "profile_subject_id": bundle["profile_subject_id"],
        "platform_scope": "youtube",
        "assessment_packet_id": assessment_packet_id,
        "selected_video_ids": requested,
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "method_deck_sha256": method_hash,
        "bundle_out": str(bundle_out),
        "prompt_out": str(prompt_out),
        "assembly_receipt_record_id": receipt["record_id"],
        "transcript_evidence_count": len(bundle["transcript_evidence"]),
        "comment_evidence_count": len(bundle["comment_evidence"]),
        "model_api_calls": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--data-root", required=True)
    prepare.add_argument("--assessment-packet-id", required=True)
    prepare.add_argument("--creator-id", required=True)
    prepare.add_argument("--profile-subject-id", required=True)
    prepare.add_argument("--video-id", action="append", required=True)
    prepare.add_argument(
        "--watch-packet",
        action="append",
        default=[],
        metavar="VIDEO_ID=PACKET_ID",
        help="Bind an exact captured watch packet and bypass lake-wide discovery.",
    )
    prepare.add_argument(
        "--transcript-packet",
        action="append",
        default=[],
        metavar="VIDEO_ID=PACKET_ID",
        help="Bind an exact caption/audio packet and bypass lake-wide discovery.",
    )
    prepare.add_argument("--question", required=True)
    prepare.add_argument("--evidence-cutoff", required=True)
    prepare.add_argument("--bundle-out", type=Path, required=True)
    prepare.add_argument("--prompt-out", type=Path, required=True)

    submit = subparsers.add_parser("submit")
    submit.add_argument("--data-root", required=True)
    submit.add_argument("--bundle", type=Path, required=True)
    response = submit.add_mutually_exclusive_group(required=True)
    response.add_argument("--response", type=Path)
    response.add_argument("--response-stdin", action="store_true")
    submit.add_argument("--snapshot-out", type=Path, required=True)
    return parser


def _packet_map(values: Sequence[str], *, option: str) -> dict[str, str] | None:
    if not values:
        return None
    mapped: dict[str, str] = {}
    for value in values:
        video_id, separator, packet_id = value.partition("=")
        video_id = video_id.strip()
        packet_id = packet_id.strip()
        if not separator or not video_id or not packet_id:
            raise ValueError(f"{option} requires VIDEO_ID=PACKET_ID")
        if video_id in mapped:
            raise ValueError(f"{option} repeats video id {video_id!r}")
        mapped[video_id] = packet_id
    return mapped


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_youtube_subscription_judgment(
                data_root=DataLakeRoot.resolve(explicit=args.data_root),
                assessment_packet_id=args.assessment_packet_id,
                creator_id=args.creator_id,
                profile_subject_id=args.profile_subject_id,
                video_ids=args.video_id,
                watch_packet_ids=_packet_map(
                    args.watch_packet, option="--watch-packet"
                ),
                transcript_packet_ids=_packet_map(
                    args.transcript_packet, option="--transcript-packet"
                ),
                question=args.question,
                evidence_cutoff=args.evidence_cutoff,
                bundle_out=args.bundle_out,
                prompt_out=args.prompt_out,
            )
        else:
            response_bytes = (
                sys.stdin.buffer.read()
                if args.response_stdin
                else args.response.read_bytes()
            )
            result = submit_subscription_judgment(
                data_root=DataLakeRoot.resolve(explicit=args.data_root),
                bundle_path=args.bundle,
                response_bytes=response_bytes,
                snapshot_out=args.snapshot_out,
            )
    except (DataLakeRootError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result.get("status") == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
