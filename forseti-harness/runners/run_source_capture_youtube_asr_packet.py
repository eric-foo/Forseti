"""CLI: capture YouTube audio + write an ASR transcript derived record (transcript spine v0).

ASR fallback for no-caption videos. Data-lake-mode only (the transcript is a derived record via
DataLakeRoot.append_record). Downloads bestaudio (yt-dlp android_vr, token-free), captures it as a
SourceCapturePacket, then writes derived/<audio-packet_id>/transcript_asr/<id> with VAD-gated
faster-whisper output + provenance. Public data only; captured/derived data lives in the lake.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.transcript import write_asr_transcript
from source_capture.transcript.audio_asr import download_audio, transcribe_audio
from runners._youtube_cli import normalize_video_id_argv

_CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture YouTube audio + write an ASR transcript derived record.")
    parser.add_argument("--video-id", required=True)
    parser.add_argument(
        "--channel-id",
        help=(
            "Expected canonical YouTube channel id. Supply this for creator-audience "
            "evidence so the audio packet remains bound to the assessed account."
        ),
    )
    parser.add_argument("--data-root", default=None, help="Forseti data lake root (or FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT)). ASR is data-lake-mode.")
    parser.add_argument("--model", default="small")
    raw_argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(
        normalize_video_id_argv(raw_argv, option_strings=parser._option_string_actions)
    )
    if args.channel_id is not None and not _CHANNEL_ID.fullmatch(args.channel_id):
        parser.exit(
            status=2,
            message="--channel-id must be a canonical UC-prefixed YouTube channel id\n",
        )

    from data_lake.root import DataLakeRoot

    try:
        root = DataLakeRoot.resolve(explicit=args.data_root)
    except Exception as exc:  # noqa: BLE001
        parser.exit(status=2, message=f"data root required (ASR writes a derived record): {exc}\n")

    res = download_audio(args.video_id)
    if res is None:
        parser.exit(status=4, message=f"audio download failed for {args.video_id}\n")
    audio_bytes, ext = res

    try:
        code, msg = write_asr_transcript(
            video_id=args.video_id,
            audio_bytes=audio_bytes,
            audio_ext=ext,
            transcribe_fn=lambda path: transcribe_audio(path, model_name=args.model),
            data_root=root,
            identity_extra=(
                {"channel_id": args.channel_id}
                if args.channel_id is not None
                else None
            ),
        )
    except Exception as exc:  # noqa: BLE001 - capture/lake errors surface here (incl. re-derive of the SAME audio packet)
        parser.exit(status=3, message=f"asr transcript failed: {type(exc).__name__}: {exc}\n")

    if code == 0:
        print(msg)
        return 0
    parser.exit(status=code, message=f"asr: {msg}\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
