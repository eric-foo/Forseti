"""Exercise a real killable metadata child without yt-dlp or network access."""
from __future__ import annotations

import json
import subprocess
import time

import pytest

from runners import run_source_capture_youtube_caption_packet as runner
from source_capture.transcript import youtube_captions as captions


def _fake_ytdlp(tmp_path, monkeypatch, body):
    package = tmp_path / "yt_dlp"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__main__.py").write_text(body, encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    monkeypatch.setattr(captions, "_ytdlp_version", lambda: "fixture")


def test_metadata_child_preserves_unicode_and_track_metadata(tmp_path, monkeypatch):
    info = {"id": "abcdefghijk", "title": "Crème 日本", "language": "fr",
            "subtitles": {"fr": [{"ext": "json3"}]}, "automatic_captions": {}}
    _fake_ytdlp(tmp_path, monkeypatch,
                "import sys\n"
                "assert '--ignore-config' in sys.argv and '--skip-download' in sys.argv\n"
                "assert '--dump-single-json' in sys.argv and '--no-playlist' in sys.argv\n"
                "assert sys.argv[-2:] == ['--', 'https://www.youtube.com/watch?v=abcdefghijk']\n"
                # Write through the child's text layer, as yt-dlp does. Writing
                # pre-encoded bytes to stdout.buffer would bypass the encoding
                # boundary this test exists to cover.
                f"print({json.dumps(info, ensure_ascii=False)!r})\n")
    assert captions._extract_info("https://www.youtube.com/watch?v=abcdefghijk") == info


def test_metadata_child_stdout_is_utf8_despite_ambient_encoding(tmp_path, monkeypatch):
    """A non-UTF-8 ambient text layer must not silently truncate metadata.

    yt-dlp encodes its JSON with the stream's own encoding and ``errors='ignore'``
    (``yt_dlp.utils.write_string``), so characters unsupported by an ambient cp1252 encoding
    would be dropped before the parent's UTF-8 decode ever runs.
    """
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    _fake_ytdlp(tmp_path, monkeypatch,
                "import sys, json\n"
                "enc = sys.stdout.encoding\n"
                "info = {'id': 'abcdefghijk', 'title': 'Crème 日本', 'child_stdout_encoding': enc}\n"
                "s = json.dumps(info, ensure_ascii=False)\n"
                # yt_dlp.utils.write_string: encode with the stream encoding, ignoring losses.
                "sys.stdout.buffer.write(s.encode(enc, 'ignore'))\n")
    info = captions._extract_info("https://www.youtube.com/watch?v=abcdefghijk")
    assert info["child_stdout_encoding"].lower().replace("_", "-") == "utf-8"
    assert info["title"] == "Crème 日本"


def test_hung_metadata_child_is_reaped_and_runner_reports_error_not_asr(tmp_path, monkeypatch, capsys):
    marker = tmp_path / "child-survived"
    _fake_ytdlp(tmp_path, monkeypatch,
                "import time\nfrom pathlib import Path\ntime.sleep(2)\n"
                f"Path({str(marker)!r}).write_text('survived')\n")
    monkeypatch.setattr(captions, "_YTDLP_METADATA_TIMEOUT_SECONDS", 0.25)
    children = []
    original_popen = subprocess.Popen

    def track_child(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(subprocess, "Popen", track_child)
    monkeypatch.setattr(runner, "write_caption_packet",
                        lambda *a, **kw: pytest.fail("metadata failure reached packet/ASR writer"))
    started = time.monotonic()
    with pytest.raises(SystemExit) as exc:
        runner.main(["--video-id", "abcdefghijk", "--output", str(tmp_path / "out")])
    assert exc.value.code == 3
    assert "metadata_timeout" in capsys.readouterr().err
    assert time.monotonic() - started < 5
    assert len(children) == 1 and children[0].poll() is not None
    assert not marker.exists()
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("body, error", [
    ("import sys; sys.stderr.write('provider unavailable'); sys.exit(7)", RuntimeError),
    ("print('not json')", ValueError),
    ("print('null')", ValueError),
    ("print('{}')", ValueError),
])
def test_failed_or_invalid_metadata_never_means_no_captions(tmp_path, monkeypatch, body, error):
    _fake_ytdlp(tmp_path, monkeypatch, body)
    with pytest.raises(error):
        captions.fetch_youtube_caption_artifacts("abcdefghijk")
