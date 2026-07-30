from __future__ import annotations

from pathlib import Path

import pytest

from data_lake import root as root_module
from runners import run_source_capture_youtube_asr_packet as runner

_LEADING_DASH_VIDEO_ID = "-V7MN2IWMpA"


def test_youtube_asr_runner_accepts_leading_dash_video_id(monkeypatch, tmp_path: Path) -> None:
    resolved_root = object()

    class FakeDataLakeRoot:
        @staticmethod
        def resolve(*, explicit):
            assert explicit == str(tmp_path / "lake")
            return resolved_root

    def fake_download(video_id: str):
        assert video_id == _LEADING_DASH_VIDEO_ID
        return b"audio", "webm"

    def fake_write_asr_transcript(**kwargs):
        assert kwargs["video_id"] == _LEADING_DASH_VIDEO_ID
        assert kwargs["audio_bytes"] == b"audio"
        assert kwargs["audio_ext"] == "webm"
        assert kwargs["data_root"] is resolved_root
        assert kwargs["identity_extra"] == {
            "channel_id": "UC" + "A" * 22
        }
        return 0, "derived/path"

    monkeypatch.setattr(root_module, "DataLakeRoot", FakeDataLakeRoot)
    monkeypatch.setattr(runner, "download_audio", fake_download)
    monkeypatch.setattr(runner, "write_asr_transcript", fake_write_asr_transcript)

    assert runner.main(
        [
            "--video-id",
            _LEADING_DASH_VIDEO_ID,
            "--channel-id",
            "UC" + "A" * 22,
            "--data-root",
            str(tmp_path / "lake"),
        ]
    ) == 0


def test_youtube_asr_runner_rejects_noncanonical_channel_id() -> None:
    with pytest.raises(SystemExit) as exc:
        runner.main(
            [
                "--video-id",
                _LEADING_DASH_VIDEO_ID,
                "--channel-id",
                "not-a-channel",
                "--data-root",
                "C:\\unused",
            ]
        )

    assert exc.value.code == 2


def test_youtube_asr_runner_rejects_data_root_flag_as_missing_video_id(monkeypatch, tmp_path: Path) -> None:
    resolved_root = object()
    monkeypatch.setenv("FORSETI_DATA_ROOT", str(tmp_path / "lake"))

    class FakeDataLakeRoot:
        @staticmethod
        def resolve(*, explicit):
            assert explicit is None
            return resolved_root

    def fail_download(_video_id: str):  # pragma: no cover - must not be reached
        raise AssertionError("download should not run when video id is missing")

    monkeypatch.setattr(root_module, "DataLakeRoot", FakeDataLakeRoot)
    monkeypatch.setattr(runner, "download_audio", fail_download)

    with pytest.raises(SystemExit) as exc:
        runner.main(["--video-id", "--data-root"])

    assert exc.value.code == 2
