"""Seam catch-up tests for the ASR transcript lane (YouTube + IG audio families).

Mirrors the adjudicated catch-up suite shape plus this lane's specifics: the
injected non-API transcriber, model-scoped record ids (a policy bump re-derives
under a NEW id — never an append-only collision), same-policy crash recovery by
citation (``acked_existing_transcript``), and the block-don't-burn rule (a
failed transcription writes NO record and NO ack, so the deterministic record
id is never burned and the packet re-surfaces).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import runners.run_asr_transcript_catchup as catchup
from data_lake.consumption import find_acks
from data_lake.root import DataLakeRoot, raw_shard
from harness_utils import generate_ulid
from source_capture.models import known_fact
from source_capture.transcript.asr_packet import asr_record_id
from source_capture.transcript.audio_asr import AudioTranscriber
from source_capture.transcript.ig_reels_audio_packet import (
    transcribe_committed_ig_audio_packet,
)
from source_capture.writer import write_local_source_capture_packet

_YT_VIDEO_ID = "vid00000001"  # exactly 11 chars, YouTube id shaped
_IG_SHORTCODE = "DZsynthreel"
_POLICY = catchup.default_transcriber_policy(model_name="small", compute_type="int8")


def _fake_ok(_audio_path: str):
    return (
        "transcribed",
        [{"start_ms": 0, "end_ms": 900, "text": "synthetic cue"}],
        {"tool": "faster-whisper", "model": "small", "compute_type": "int8"},
    )


def _fake_silent(_audio_path: str):
    return ("no_speech", [], {"tool": "faster-whisper", "model": "small"})


def _fake_fail(_audio_path: str):
    return ("failed", [], {"tool": "faster-whisper", "model": "small", "failure_message": "model missing"})


def _fake_mismatched_model(_audio_path: str):
    return (
        "transcribed",
        [{"start_ms": 0, "end_ms": 900, "text": "synthetic cue"}],
        {"tool": "faster-whisper", "model": "large", "compute_type": "int8"},
    )


def _commit_audio_packet(
    root: DataLakeRoot,
    tmp_path: Path,
    *,
    family: str = "youtube",
    surface: str = "youtube_audio",
    ident_key: str = "platform_video_id",
    ident: str = _YT_VIDEO_ID,
) -> str:
    stage = tmp_path / f"stage_{generate_ulid()}"
    stage.mkdir(parents=True)
    audio = stage / f"{ident}.audio.m4a"
    audio.write_bytes(b"fake-audio-bytes:" + ident.encode("utf-8"))
    meta = stage / "capture_metadata.json"
    meta.write_text(
        json.dumps({ident_key: ident, "platform": family}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return write_local_source_capture_packet(
        data_root=root,
        input_files=[audio, meta],
        source_family=family,
        source_surface=surface,
        source_locator=known_fact(f"https://example.test/{ident}"),
        decision_question="q",
        capture_context="asr transcript catchup test",
    ).packet.packet_id


def _transcript_dir(root: DataLakeRoot, packet_id: str) -> Path:
    return root.lane_dir(subtree="derived", raw_anchor=packet_id, lane="transcript_asr")


def _acks(root: DataLakeRoot, packet_id: str) -> list[dict]:
    return find_acks(root, raw_anchor=packet_id, ack_namespace="transcript_asr")


def _run(root: DataLakeRoot, fn=_fake_ok, policy: dict | None = None) -> list[dict]:
    return catchup.run_catchup(
        data_root=root, transcribe_fn=fn, transcriber_policy=policy or _POLICY
    )


def test_reused_session_failure_does_not_burn_record_or_ack(tmp_path, monkeypatch) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    packet_id = _commit_audio_packet(root, tmp_path)
    constructions = []

    class Model:
        def __init__(self, *args, **kwargs):
            constructions.append(self)

        def transcribe(self, *args, **kwargs):
            if len(constructions) == 1:
                raise RuntimeError("temporary decoder failure")
            return iter([SimpleNamespace(start=0, end=1, text="synthetic cue")]), SimpleNamespace(language="en")

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(__version__="fixture", WhisperModel=Model))
    with AudioTranscriber() as session:
        failed = _run(root, fn=session)
        assert [entry["status"] for entry in failed] == ["derive_failed"]
        assert _acks(root, packet_id) == []
        assert not _transcript_dir(root, packet_id).exists()
        recovered = _run(root, fn=session)
        assert [entry["status"] for entry in recovered] == ["derived"]
        assert len(_acks(root, packet_id)) == 1
    assert len(constructions) == 2


def test_catchup_discovers_transcribes_and_acks(tmp_path: Path) -> None:
    # S1: a committed, untranscribed audio packet gets its transcript record
    # (record-set complete) plus a lane-owned ack citing it.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)

    results = _run(root)

    assert [entry["status"] for entry in results] == ["derived"]
    assert results[0]["posture"] == "transcribed"
    assert results[0]["cue_count"] == 1
    record_id = results[0]["record_id"]
    assert record_id.startswith("asr_small__")
    assert (_transcript_dir(root, pid) / record_id).is_file()
    assert root.is_record_set_complete(
        subtree="derived", raw_anchor=pid, record_id=record_id, completion_lane="transcript_asr__set"
    )
    (ack,) = _acks(root, pid)
    assert ack["obligation"]["consumer"] == "asr_transcript_catchup"
    assert ack["obligation"]["transcriber_policy"]["model"] == "small"


def test_second_run_is_a_no_op(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)
    _run(root)

    second = _run(root)

    assert second == []
    assert len(list(_transcript_dir(root, pid).iterdir())) == 1
    assert len(_acks(root, pid)) == 1


def test_model_policy_bump_re_surfaces_and_re_derives_under_new_id(tmp_path: Path) -> None:
    # S3 + no-collision: a model change re-fingerprints the obligation AND lands
    # a NEW record id (the id embeds the model), never an append-only refusal.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)
    _run(root)

    def fake_large(_audio_path: str):
        return (
            "transcribed",
            [{"start_ms": 0, "end_ms": 500, "text": "large cue"}],
            {"tool": "faster-whisper", "model": "large"},
        )

    large_policy = catchup.default_transcriber_policy(model_name="large", compute_type="int8")
    results = _run(root, fn=fake_large, policy=large_policy)

    assert [entry["status"] for entry in results] == ["derived"]
    assert results[0]["record_id"].startswith("asr_large__")
    assert len(_acks(root, pid)) == 2
    assert len(list(_transcript_dir(root, pid).iterdir())) == 2


def test_failed_transcription_writes_no_record_and_re_surfaces(tmp_path: Path) -> None:
    # Block-don't-burn: a failed transcription is a loud derive_failed with NO
    # record (the model+audio record id stays unburned) and NO ack; the packet
    # re-surfaces and succeeds once the transcriber recovers.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)

    first = _run(root, fn=_fake_fail)

    assert [entry["status"] for entry in first] == ["derive_failed"]
    assert "transcriber failed" in first[0]["error"]
    assert not _transcript_dir(root, pid).is_dir()
    assert _acks(root, pid) == []

    recovered = _run(root, fn=_fake_ok)
    assert [entry["status"] for entry in recovered] == ["derived"]
    assert len(_acks(root, pid)) == 1


@pytest.mark.parametrize(
    ("family", "surface", "ident_key", "ident"),
    (
        ("youtube", "youtube_audio", "platform_video_id", _YT_VIDEO_ID),
        ("instagram_creator", "ig_reels_audio", "platform_shortcode", _IG_SHORTCODE),
    ),
)
def test_transcriber_policy_model_mismatch_writes_no_record_and_re_surfaces(
    tmp_path: Path, family: str, surface: str, ident_key: str, ident: str
) -> None:
    # The obligation is fingerprinted with the CLI policy model. If the injected
    # transcriber reports a different model, the runner must not write a record
    # or ack the packet under the wrong policy.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(
        root, tmp_path, family=family, surface=surface, ident_key=ident_key, ident=ident
    )

    first = _run(root, fn=_fake_mismatched_model)

    assert [entry["status"] for entry in first] == ["derive_failed"]
    assert "transcriber model mismatch" in first[0]["error"]
    assert not _transcript_dir(root, pid).is_dir()
    assert _acks(root, pid) == []

    recovered = _run(root, fn=_fake_ok)
    assert [entry["status"] for entry in recovered] == ["derived"]
    assert recovered[0]["record_id"].startswith("asr_small__")
    assert len(_acks(root, pid)) == 1


def test_no_speech_is_an_honest_ack(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)

    results = _run(root, fn=_fake_silent)

    assert [entry["status"] for entry in results] == ["derived"]
    assert results[0]["posture"] == "no_speech"
    assert results[0]["cue_count"] == 0
    assert len(_acks(root, pid)) == 1


def test_existing_current_policy_transcript_is_acked_by_citation(tmp_path: Path) -> None:
    # Same-policy crash recovery: a transcript written without its ack (here via
    # the IG committed-packet module path) is cited, not re-derived — and this is
    # NOT an old-policy record satisfying a new fingerprint (the id embeds the
    # policy).
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(
        root,
        tmp_path,
        family="instagram_creator",
        surface="ig_reels_audio",
        ident_key="platform_shortcode",
        ident=_IG_SHORTCODE,
    )
    derived = transcribe_committed_ig_audio_packet(
        root, packet_id=pid, transcribe_fn=_fake_ok
    )
    assert derived["posture"] == "transcribed"

    results = _run(root)

    assert [entry["status"] for entry in results] == ["acked_existing_transcript"]
    assert results[0]["record_id"] == derived["record_id"]
    assert len(list(_transcript_dir(root, pid).iterdir())) == 1
    assert len(_acks(root, pid)) == 1


def test_ig_audio_packet_derives_and_acks(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(
        root,
        tmp_path,
        family="instagram_creator",
        surface="ig_reels_audio",
        ident_key="platform_shortcode",
        ident=_IG_SHORTCODE,
    )

    results = _run(root)

    assert [entry["status"] for entry in results] == ["derived"]
    assert results[0]["packet_id"] == pid
    record = json.loads(
        (_transcript_dir(root, pid) / results[0]["record_id"]).read_text(encoding="utf-8")
    )
    assert record["platform"] == "instagram"
    assert record["shortcode"] == _IG_SHORTCODE


def test_known_other_lane_surface_is_acked_out_of_scope(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path, surface="youtube_captions")

    results = _run(root)

    assert [entry["status"] for entry in results] == ["acked_no_transcribable_audio"]
    assert results[0]["source_surface"] == "youtube_captions"
    assert not _transcript_dir(root, pid).is_dir()
    (ack,) = _acks(root, pid)
    assert ack["evidence"][0]["kind"] == "no_transcribable_audio_for_surface"
    assert _run(root) == []


def test_yt_probe_surfaces_are_acked_out_of_scope(tmp_path: Path) -> None:
    # The 2026-07-04 live census found these two probe surfaces pending as
    # unsupported_surface; their manifests declare "media bytes out of scope",
    # so they are gated out like the other known non-audio YT surfaces.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    # Distinct ident per surface: it feeds both the preserved bytes and the
    # source_locator, so two otherwise-identical fixture packets for the same
    # default ident would collide with the Bronze write-gate's duplicate check.
    pids = [
        _commit_audio_packet(root, tmp_path, surface=surface, ident=surface)
        for surface in ("yt_shorts_channel_grid_probe_v0", "yt_channel_rss_feed_probe_v0")
    ]

    results = _run(root)

    assert [entry["status"] for entry in results] == ["acked_no_transcribable_audio"] * 2
    for pid in pids:
        (ack,) = _acks(root, pid)
        assert ack["evidence"][0]["kind"] == "no_transcribable_audio_for_surface"
    assert _run(root) == []


def test_out_of_scope_policy_change_re_surfaces_previous_ack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # F-IGRC-002 convention: the surface gate is fingerprinted policy.
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path, surface="youtube_captions")
    assert [r["status"] for r in _run(root)] == ["acked_no_transcribable_audio"]

    trimmed = []
    for config in catchup._FAMILY_CONFIGS:
        updated = dict(config)
        if config["source_family"] == "youtube":
            updated["known_out_of_scope_surfaces"] = frozenset()
        trimmed.append(updated)
    monkeypatch.setattr(catchup, "_FAMILY_CONFIGS", tuple(trimmed))

    second = _run(root)
    assert [r["status"] for r in second] == ["unsupported_surface"]
    assert len(_acks(root, pid)) == 1


def test_unsupported_surface_is_visible_and_never_acked(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path, surface="youtube_mystery_surface")

    for results in (_run(root), _run(root)):
        assert [entry["status"] for entry in results] == ["unsupported_surface"]
    assert _acks(root, pid) == []


def test_reconcile_failure_is_per_packet_and_healthy_packets_proceed(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    good_pid = _commit_audio_packet(root, tmp_path)
    corrupt_pid = generate_ulid()
    corrupt_dir = root.path / "raw" / raw_shard(corrupt_pid) / corrupt_pid
    corrupt_dir.mkdir(parents=True)
    (corrupt_dir / "manifest.json").write_text("{not json", encoding="utf-8")

    results = _run(root)

    by_pid = {entry["packet_id"]: entry for entry in results}
    assert by_pid[corrupt_pid]["status"] == "availability_reconcile_failed"
    assert by_pid[good_pid]["status"] == "derived"


def test_pending_check_fails_loud_on_reconcile_failure(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    corrupt_pid = generate_ulid()
    corrupt_dir = root.path / "raw" / raw_shard(corrupt_pid) / corrupt_pid
    corrupt_dir.mkdir(parents=True)
    (corrupt_dir / "manifest.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(Exception, match="availability reconcile failed"):
        catchup.pending_packets(data_root=root, transcriber_policy=_POLICY)


def test_check_mode_counts_pending_across_both_families(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    yt_pid = _commit_audio_packet(root, tmp_path)
    ig_pid = _commit_audio_packet(
        root,
        tmp_path,
        family="instagram_creator",
        surface="ig_reels_audio",
        ident_key="platform_shortcode",
        ident=_IG_SHORTCODE,
    )

    pending = catchup.pending_packets(data_root=root, transcriber_policy=_POLICY)
    assert set(pending) == {yt_pid, ig_pid}

    _run(root)
    assert catchup.pending_packets(data_root=root, transcriber_policy=_POLICY) == []


def test_ack_evidence_is_dereferenceable(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    pid = _commit_audio_packet(root, tmp_path)
    _run(root)

    (ack,) = _acks(root, pid)
    (evidence,) = ack["evidence"]
    record_path = _transcript_dir(root, pid) / evidence["record_id"]
    body = record_path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == evidence["content_sha256"]
    assert evidence["byte_count"] == len(body)
    record = json.loads(body.decode("utf-8"))
    assert evidence["posture"] == record["posture"]
    # the record cites the packet's own preserved audio sha (verified read basis)
    manifest = json.loads(
        (root.path / "raw" / raw_shard(pid) / pid / "manifest.json").read_text(encoding="utf-8")
    )
    audio_sha = next(
        pf["sha256"]
        for pf in manifest["preserved_files"]
        if ".audio." in pf["relative_packet_path"]
    )
    assert record["provenance"]["source_sha256"] == audio_sha
    assert evidence["record_id"] == asr_record_id("small", audio_sha)


def test_cli_requires_exactly_one_mode() -> None:
    with pytest.raises(SystemExit) as excinfo:
        catchup.main([])
    assert excinfo.value.code == 2
