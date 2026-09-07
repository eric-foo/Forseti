"""Offline ASR lifetime, output compatibility, and real batch-wiring tests."""
from __future__ import annotations

import json
import sys
import weakref
from types import SimpleNamespace

import pytest

from data_lake.root import DataLakeRoot
from runners import run_asr_transcript_catchup as catchup
from runners import run_seam_cadence as cadence
from runners import run_source_capture_ig_reels_creator_deep_capture as creator
from source_capture.ig_reels_deep_capture import ReelDeepCaptureResult
from source_capture.transcript.audio_asr import AudioTranscriber, transcribe_audio


@pytest.fixture
def whisper(monkeypatch):
    state = SimpleNamespace(configurations=[], references=[], calls=[], fail_init=0)

    class Model:
        def __init__(self, name, **kwargs):
            state.configurations.append((name, kwargs))
            if state.fail_init:
                state.fail_init -= 1
                raise RuntimeError("model load failed")
            state.references.append(weakref.ref(self))

        def transcribe(self, path, **kwargs):
            state.calls.append((path, kwargs))

            def segments():
                if path == "decode-failure":
                    raise ValueError("decode failed")
                if path != "silence":
                    yield SimpleNamespace(start=0.125, end=1.875, text="  synthetic cue  ")
                    yield SimpleNamespace(start=2, end=3, text="  ")

            return segments(), SimpleNamespace(language="en")

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(__version__="fixture", WhisperModel=Model))
    return state


def test_session_is_lazy_and_preserves_missing_dependency_exception(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with AudioTranscriber() as session:
        with pytest.raises(ModuleNotFoundError):
            session("audio")
    with pytest.raises(ModuleNotFoundError):
        transcribe_audio("audio")


def test_session_reuses_model_and_preserves_serialized_one_shot_output(whisper):
    expected = json.dumps([
        "transcribed", [{"start_ms": 125, "end_ms": 1875, "text": "synthetic cue"}],
        {
            "tool": "faster-whisper", "tool_version": "fixture", "model": "small",
            "model_repo_id": "Systran/faster-whisper-small", "model_digest": None,
            "model_digest_basis": "not available from the faster-whisper runtime (no weights hash exposed)",
            "compute_type": "int8",
            "decode_params": {"beam_size": 1, "vad_filter": True, "condition_on_previous_text": False},
            "speech_gate": "faster-whisper builtin Silero VAD (onnx)", "detected_language": "en",
        },
    ])
    with AudioTranscriber() as session:
        assert whisper.configurations == []
        assert json.dumps(session("first")) == expected
        assert json.dumps(session("second")) == expected
        assert session("silence")[:2] == ("no_speech", [])
        assert len(whisper.configurations) == 1
        assert whisper.references[0]() is not None
    assert whisper.references[0]() is None
    assert json.dumps(transcribe_audio("single")) == expected
    assert len(whisper.configurations) == 2
    assert whisper.references[-1]() is None
    assert all(params == {"beam_size": 1, "vad_filter": True, "condition_on_previous_text": False}
               for _, params in whisper.calls)


def test_sessions_do_not_share_configuration_or_models(whisper):
    for model, compute in [("small", "int8"), ("large", "float32"), ("small", "int8")]:
        with AudioTranscriber(model_name=model, compute_type=compute) as session:
            result = session("audio")
            assert result[2]["model"] == model
            assert result[2]["compute_type"] == compute
    assert whisper.configurations == [
        ("small", {"device": "cpu", "compute_type": "int8"}),
        ("large", {"device": "cpu", "compute_type": "float32"}),
        ("small", {"device": "cpu", "compute_type": "int8"}),
    ]
    assert all(ref() is None for ref in whisper.references)


def test_failed_initialization_and_lazy_decode_are_retried(whisper):
    whisper.fail_init = 1
    with AudioTranscriber() as session:
        failed = session("audio")
        assert failed[:2] == ("failed", [])
        assert failed[2]["failure_type"] == "RuntimeError"
        assert failed[2]["failure_message"] == "model load failed"
        assert session("audio")[0] == "transcribed"
        failed = session("decode-failure")
        assert failed[:2] == ("failed", [])
        assert failed[2]["failure_type"] == "ValueError"
        assert whisper.references[0]() is None
        assert session("audio")[0] == "transcribed"
    assert len(whisper.configurations) == 3
    assert all(ref() is None for ref in whisper.references)


def test_session_releases_model_when_batch_raises(whisper):
    with pytest.raises(RuntimeError, match="batch failed"):
        with AudioTranscriber() as session:
            session("audio")
            raise RuntimeError("batch failed")
    assert whisper.references[0]() is None


@pytest.mark.parametrize("route", ["catchup", "cadence"])
@pytest.mark.parametrize("count", [0, 3])
def test_catchup_entrypoints_inject_one_lazy_batch_session(whisper, monkeypatch, route, count):
    sessions = []

    def run(**kwargs):
        sessions.append(kwargs["transcribe_fn"])
        for index in range(count):
            assert kwargs["transcribe_fn"](f"audio-{index}")[0] == "transcribed"
        return []

    monkeypatch.setattr(catchup, "run_catchup", run)
    monkeypatch.setattr(DataLakeRoot, "resolve", lambda **kwargs: object())
    if route == "catchup":
        assert catchup.main(["--run"]) == 0
    else:
        ctx = cadence.CadenceContext(object(), {}, "small", "int8")
        assert cadence._asr_run(ctx, ()) == []
    assert len(sessions) == 1
    assert len(whisper.configurations) == min(count, 1)
    # Keep the session alive: the context exit itself must release the model.
    assert all(ref() is None for ref in whisper.references)


def test_pending_and_skipped_cadence_do_not_load_optional_asr(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    root = DataLakeRoot.for_test(tmp_path / "lake")
    monkeypatch.setattr(DataLakeRoot, "resolve", lambda **kwargs: root)
    assert catchup.main(["--check"]) == 0
    ctx = cadence.CadenceContext(root, catchup.default_transcriber_policy(model_name="small", compute_type="int8"), "small", "int8")
    assert cadence.run_cadence(ctx, skip_asr=True) == 0


@pytest.mark.parametrize("route", ["callable", "cli"])
@pytest.mark.parametrize("count", [0, 3])
def test_creator_entrypoints_reuse_session_through_real_capture_factory(whisper, monkeypatch, route, count):
    ranked = [creator.RankedReel(rank=i, shortcode=f"reel-{i}", engagement=i, like_count=None, comment_count=None)
              for i in range(count)]
    monkeypatch.setattr(creator, "scan_creator_reels_ranked", lambda **kwargs: (ranked, None))
    sessions = []

    def capture(shortcode, *, transcribe_fn, **kwargs):
        sessions.append(transcribe_fn)
        posture, cues, _info = transcribe_fn(shortcode)
        return ReelDeepCaptureResult(shortcode, (), posture, tuple(cues), None)

    # Leave _make_capture_fn and selection orchestration real; stub only capture I/O.
    monkeypatch.setattr(creator, "run_reel_deep_capture", capture)
    if route == "callable":
        _ranked, captured = creator.run_creator_deep_capture(handle="creator", top_n=3)
        assert len(captured) == count
        assert all(item.ok for item in captured)
    else:
        assert creator.main(["--handle", "creator", "--top-n", "3"]) == 0
    assert len(whisper.configurations) == min(count, 1)
    assert len({id(session) for session in sessions}) == min(count, 1)
    assert all(ref() is None for ref in whisper.references)
