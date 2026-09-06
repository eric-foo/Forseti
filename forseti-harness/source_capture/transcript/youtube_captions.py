"""YouTube caption acquisition for the transcript spine (Capture layer).

Fetches the ORIGINAL-language caption track via yt-dlp (default token-free client)
and returns the RAW json3 bytes (the authoritative artifact; cue/span ids are the
evidence anchor) plus capture metadata and a NON-AUTHORITATIVE flat-text view.

Public data only, anonymous. Stores nothing; a runner stages the raw json3 +
metadata into a SourceCapturePacket. The flat-text view is a dedup of the json3
(a Cleaning-style NORMALIZATION) and is therefore NEVER a packet PreservedFile.
ASR-derived text is out of scope here (gated on the FileDerivation manifest extension).

Original-language discipline (review AR-04): only a track matching the video's
detected language is treated as original. A translated track is never silently
accepted as original; when the language is undetected we fall back to English but
flag it (`original_language_assumed`). Download results are validated before
`found=True`, distinguishing download_failed / no_caption_track / invalid_caption.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")

# Liveness backstop: a hung `yt-dlp` subprocess would otherwise block the caption capture
# forever. Generous bound (json3 caption files are tiny); subprocess.run kills the child on timeout.
_YTDLP_CAPTION_TIMEOUT_SECONDS = 120
# Bound metadata separately: retries and multiple socket operations must not
# extend this stage indefinitely before the already-bounded caption download.
_YTDLP_METADATA_TIMEOUT_SECONDS = 120
_YTDLP_METADATA_SOCKET_TIMEOUT_SECONDS = 30


def _ytdlp_version() -> str:
    import yt_dlp  # lazy: only needed at real runtime, not at import/test-collection time

    return yt_dlp.version.__version__


def _extract_info(url: str) -> dict:
    """Extract metadata in a killable child; failures are not missing captions.

    yt-dlp remains optional at import time. Ignore ambient CLI configuration so
    user download/postprocessor settings cannot affect this metadata-only call.
    Pin the child's text output to UTF-8 to match the decode below. An ambient
    encoding such as cp1252 can lose characters before the parent receives them
    or make the child fail while writing metadata.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--ignore-config", "--skip-download",
             "--no-playlist", "--dump-single-json", "--quiet", "--no-warnings",
             "--socket-timeout", str(_YTDLP_METADATA_SOCKET_TIMEOUT_SECONDS), "--", url],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=_YTDLP_METADATA_TIMEOUT_SECONDS,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"metadata_timeout: yt-dlp exceeded {_YTDLP_METADATA_TIMEOUT_SECONDS}s"
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"metadata_failed (rc={proc.returncode}): {(proc.stderr or '')[:160]}"
        )
    info = json.loads(proc.stdout)
    if not isinstance(info, dict) or not info.get("id"):
        raise ValueError("metadata_invalid: expected a video metadata object with an id")
    return info


@dataclass
class CaptionFetch:
    video_id: str
    found: bool
    note: str
    lang: str | None = None
    caption_kind: str | None = None          # manual | auto | None
    original_language_assumed: bool = False   # True when language undetected and we assumed en
    json3_bytes: bytes | None = None          # RAW authoritative artifact
    flat_text: str | None = None              # NON-AUTHORITATIVE convenience view
    cue_count: int = 0
    title: str | None = None
    channel_id: str | None = None
    publish_date_iso: str | None = None       # absolute, from yt-dlp upload_date
    duration_s: int | None = None
    tooling: dict = field(default_factory=dict)


def flatten_json3(raw: bytes) -> tuple[str, int]:
    """Dedup rolling json3 cues into readable text. NON-AUTHORITATIVE view."""
    data = json.loads(raw.decode("utf-8", "replace"))
    lines: list[str] = []
    prev = None
    cue_events = 0
    for ev in data.get("events", []):
        segs = ev.get("segs") or []
        if not segs:
            continue
        cue_events += 1
        line = "".join(s.get("utf8", "") for s in segs if isinstance(s, dict)).strip()
        if line and line != prev:
            lines.append(line)
            prev = line
    return "\n".join(lines), cue_events


def _upload_date_iso(info: dict) -> str | None:
    ud = info.get("upload_date")  # YYYYMMDD
    if ud and len(ud) == 8 and ud.isdigit():
        return f"{ud[0:4]}-{ud[4:6]}-{ud[6:8]}"
    return None


def fetch_youtube_caption_artifacts(video_id: str) -> CaptionFetch:
    if not _VIDEO_ID.fullmatch(video_id or ""):
        return CaptionFetch(video_id=video_id, found=False,
                            note="invalid YouTube video id (expected 11 chars [A-Za-z0-9_-])")

    url = f"https://www.youtube.com/watch?v={video_id}"
    tooling = {
        "tool": "yt-dlp",
        "tool_version": _ytdlp_version(),
        # yt-dlp default selects a token-free client (android_vr) for subs+info; validated this
        # session. NOTE: android_vr excludes made-for-kids content (v0 residual for non-kids creators).
        "client": "yt-dlp-default",
        "sub_format": "json3",
    }

    # 1) extract_info (no download): original language + identity + available tracks (yt-dlp, lazy).
    info = _extract_info(url)

    base = dict(
        video_id=video_id,
        title=info.get("title"),
        channel_id=info.get("channel_id"),
        publish_date_iso=_upload_date_iso(info),
        duration_s=info.get("duration"),
        tooling=tooling,
    )

    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    orig = info.get("language")  # may carry a region, e.g. "en-US"; None when undetected
    orig_base = orig.split("-")[0] if orig else None

    def _match(tracks: dict) -> str | None:
        # The original-language track: exact code, then primary subtag (en-US -> en).
        # Never a translation (translations are keyed by target lang, not the source base).
        if orig and orig in tracks:
            return orig
        if orig_base:
            if orig_base in tracks:
                return orig_base
            for key in tracks:
                if key.split("-")[0] == orig_base:
                    return key
        return None

    assumed = False
    m_key, a_key = _match(manual), _match(auto)
    if m_key:
        lang, kind = m_key, "manual"
    elif a_key:
        lang, kind = a_key, "auto"
    elif orig:
        # Original language known but no matching track -> do NOT accept a translated track.
        return CaptionFetch(found=False, lang=orig,
                            note=f"no original-language ({orig}) caption track; only translations/other langs present",
                            **base)
    elif "en" in manual:
        lang, kind, assumed = "en", "manual", True
    elif "en" in auto:
        lang, kind, assumed = "en", "auto", True
    else:
        return CaptionFetch(found=False, note="no_caption_track: original language undetected and no en track", **base)

    # 2) download that lang's json3 via yt-dlp CLI (default token-free client), then VALIDATE.
    write_flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
    with tempfile.TemporaryDirectory(prefix="orca_cap_") as tmp:
        out_tmpl = os.path.join(tmp, "%(id)s.%(ext)s")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--skip-download", write_flag,
                 "--sub-langs", lang, "--sub-format", "json3", "-o", out_tmpl, url],
                capture_output=True, text=True, timeout=_YTDLP_CAPTION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return CaptionFetch(found=False, lang=lang, caption_kind=kind,
                                note=f"download_timeout: yt-dlp exceeded {_YTDLP_CAPTION_TIMEOUT_SECONDS}s", **base)
        if proc.returncode != 0:
            return CaptionFetch(found=False, lang=lang, caption_kind=kind,
                                note=f"download_failed (rc={proc.returncode}): {(proc.stderr or '')[:160]}", **base)
        hits = sorted(glob.glob(os.path.join(tmp, f"{video_id}*.json3")))
        if not hits:
            return CaptionFetch(found=False, lang=lang, caption_kind=kind,
                                note="no_caption_track: download produced no json3", **base)
        with open(hits[0], "rb") as fh:
            raw = fh.read()

    if not raw.strip():
        return CaptionFetch(found=False, lang=lang, caption_kind=kind, note="invalid_caption: empty json3", **base)
    try:
        flat, cues = flatten_json3(raw)
    except Exception as exc:  # noqa: BLE001 - any parse failure is an invalid caption, not success
        return CaptionFetch(found=False, lang=lang, caption_kind=kind,
                            note=f"invalid_caption: json3 parse failed ({type(exc).__name__})", **base)
    if cues == 0:
        return CaptionFetch(found=False, lang=lang, caption_kind=kind, note="invalid_caption: no cues in json3", **base)

    return CaptionFetch(found=True, note="ok", lang=lang, caption_kind=kind,
                        original_language_assumed=assumed, json3_bytes=raw,
                        flat_text=flat, cue_count=cues, **base)
