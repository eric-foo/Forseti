"""YouTube audio download + VAD-gated ASR for the transcript spine (ASR fallback).

The ASR-fallback path for no-caption videos: download bestaudio (yt-dlp android_vr,
token-free) and transcribe it with faster-whisper. The speech-gate is faster-whisper's
BUILT-IN Silero VAD (`vad_filter=True`) — it removes non-speech before the decoder, so a
music/no-speech clip yields zero segments (posture `no_speech`) instead of a hallucinated
transcript. No separate VAD dependency. Public data only, anonymous.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import tempfile

# faster-whisper is imported lazily inside transcribe_audio (optional `transcribe` extra); yt-dlp
# is invoked as a subprocess (`python -m yt_dlp`), so neither is a module-import dependency here.

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")

# Liveness backstop: bound a hung `yt-dlp` bestaudio download (subprocess.run kills the child on
# timeout) so a stuck child cannot block the ASR fallback path forever.
_YTDLP_AUDIO_TIMEOUT_SECONDS = 300


def download_audio(video_id: str) -> tuple[bytes, str] | None:
    """Download bestaudio via yt-dlp android_vr (token-free). Returns (bytes, ext) or None.

    Validates the id BEFORE building any URL / touching the network (review: pre-network guard,
    matching the caption path).
    """
    if not _VIDEO_ID.fullmatch(video_id or ""):
        return None
    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory(prefix="orca_audio_") as tmp:
        out_tmpl = os.path.join(tmp, "%(id)s.%(ext)s")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "-f", "ba/b",
                 "--extractor-args", "youtube:player-client=android_vr", "-o", out_tmpl, url],
                capture_output=True, text=True, timeout=_YTDLP_AUDIO_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return None
        hits = glob.glob(os.path.join(tmp, f"{video_id}.*"))
        if proc.returncode != 0 or not hits:
            return None
        path = hits[0]
        ext = os.path.splitext(path)[1].lstrip(".") or "bin"
        with open(path, "rb") as fh:
            return fh.read(), ext


def transcribe_audio(audio_path: str, *, model_name: str = "small", compute_type: str = "int8"):
    """One-shot compatibility entrypoint; batches use an AudioTranscriber session."""
    with AudioTranscriber(model_name=model_name, compute_type=compute_type) as transcribe:
        return transcribe(audio_path)


class AudioTranscriber:
    """Lazy model reuse within one serial batch; no process-global model cache.

    Entering the session does not import faster-whisper or load a model. Exiting
    drops the retained model reference; native memory reclamation is backend-owned.
    Failed initialization or decoding never leaves a model for the next attempt.
    """

    def __init__(self, *, model_name: str = "small", compute_type: str = "int8"):
        self._model_name = model_name
        self._compute_type = compute_type
        self._model = None

    def __enter__(self) -> AudioTranscriber:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._model = None

    def __call__(self, audio_path: str):
        """VAD-gated faster-whisper. Returns (posture, cues, model_info).

        `vad_filter=True` is the built-in Silero-VAD speech-gate; zero speech segments ->
        posture 'no_speech' (never a fabricated/hallucinated transcript). A model-load/decode
        failure returns posture 'failed' with a bounded failure_message (never raises out of here,
        so the caller can always record a posture). Cues carry ms timing.

        Provenance honesty (review): `model_repo_id` is the HF repo id; `model_digest` is None with
        a stated basis because faster-whisper exposes no weights hash at runtime (the field is not a
        repo id wearing a digest's name).
        """
        model_name = self._model_name
        compute_type = self._compute_type
        import faster_whisper  # lazy: ASR is an optional runtime path (the `transcribe` extra)

        base_info = {
            "tool": "faster-whisper",
            "tool_version": faster_whisper.__version__,
            "model": model_name,
            "model_repo_id": f"Systran/faster-whisper-{model_name}",
            "model_digest": None,
            "model_digest_basis": "not available from the faster-whisper runtime (no weights hash exposed)",
            "compute_type": compute_type,
            "decode_params": {"beam_size": 1, "vad_filter": True, "condition_on_previous_text": False},
            "speech_gate": "faster-whisper builtin Silero VAD (onnx)",
        }
        try:
            if self._model is None:
                self._model = faster_whisper.WhisperModel(model_name, device="cpu", compute_type=compute_type)
            segments, info = self._model.transcribe(
                audio_path, beam_size=1, vad_filter=True, condition_on_previous_text=False
            )
            cues = [
                {"start_ms": int(s.start * 1000), "end_ms": int(s.end * 1000), "text": s.text.strip()}
                for s in segments
                if s.text and s.text.strip()
            ]
        except Exception as exc:  # noqa: BLE001 - any model/decode failure -> a `failed` posture, never a raise
            self._model = None
            return "failed", [], {**base_info, "detected_language": None,
                                  "failure_type": type(exc).__name__, "failure_message": str(exc)[:200]}

        posture = "transcribed" if cues else "no_speech"
        return posture, cues, {**base_info, "detected_language": getattr(info, "language", None)}
