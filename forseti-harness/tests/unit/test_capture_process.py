"""Real-process ownership, deadline, and cancellation dogfood (no browser/network)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from threading import Event, Thread

import pytest

from source_capture import _capture_process as process_runner


def _alive(pid):
    if os.name == "nt":
        import ctypes as c
        api = c.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.argtypes, api.OpenProcess.restype = [c.c_uint32, c.c_int, c.c_uint32], c.c_void_p
        api.WaitForSingleObject.argtypes = [c.c_void_p, c.c_uint32]
        api.CloseHandle.argtypes = [c.c_void_p]
        handle = api.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return api.WaitForSingleObject(handle, 0) == 258
        finally:
            api.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return not (stat.exists() and stat.read_text().split()[2] == "Z")


@pytest.mark.parametrize("cancel", [False, True])
def test_owned_descendant_stops_but_retained_browser_survives(tmp_path, cancel):
    harness = Path(process_runner.__file__).resolve().parents[1]
    ready = tmp_path / "ready.json"
    sleeper = tmp_path / "sleeper.py"
    sleeper.write_text("import time; time.sleep(15)", encoding="utf-8")
    script = tmp_path / "capture.py"
    script.write_text(
        "import json, subprocess, sys, time\nfrom pathlib import Path\n"
        f"sys.path.insert(0, {str(harness)!r})\n"
        "from source_capture import retained_chrome_session as chrome\n"
        "launch = subprocess.Popen\n"
        f"def fake_browser(command, **kwargs): return launch([sys.executable, {str(sleeper)!r}], **kwargs)\n"
        "subprocess.Popen = fake_browser\n"
        "shared = chrome._launch_visible_chrome(chrome_executable=Path('fixture'), user_data_dir=Path('fixture'), port=1, launch_url='about:blank')\n"
        "subprocess.Popen = launch\n"
        f"owned = launch([sys.executable, {str(sleeper)!r}])\n"
        f"Path({str(ready)!r}).write_text(json.dumps({{'owned':owned.pid,'shared':shared.pid}}))\n"
        "time.sleep(15)\n", encoding="utf-8")
    stop = Event()
    def cancel_when_ready():
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        stop.set()
    watcher = Thread(target=cancel_when_ready) if cancel else None
    if watcher:
        watcher.start()
    started = time.monotonic()
    pids = {}
    try:
        with pytest.raises(process_runner.CaptureProcessStopped) as error:
            process_runner.run_capture_process([sys.executable, str(script)],
                                                timeout_seconds=10 if cancel else 1.5, stop=stop)
        elapsed = time.monotonic() - started
        assert error.value.reason == ("cancelled" if cancel else "deadline_exceeded")
        assert error.value.cleanup_error is None
        assert elapsed < 6
        assert ready.exists(), "runner must actually launch both process classes before stop"
        import json
        pids = json.loads(ready.read_text())
        assert not _alive(pids["owned"]), "owned descendant survived"
        assert _alive(pids["shared"]), "retained browser was killed with capture"
        print(f"process dogfood: cause={error.value.reason}, elapsed={elapsed:.3f}s, owned_alive=False, retained_alive=True")
    finally:
        if watcher:
            watcher.join(timeout=6)
        if ready.exists() and not pids:
            import json
            pids = json.loads(ready.read_text())
        for pid in pids.values():
            if _alive(pid):
                os.kill(pid, signal.SIGTERM)


def test_verbose_runner_output_does_not_deadlock_and_keeps_tail(tmp_path):
    script = tmp_path / "chatty.py"
    script.write_text("import sys\nsys.stdout.write('x' * 1000000 + 'done')\nsys.stderr.write('y' * 1000000 + 'diagnostic')\n")
    result = process_runner.run_capture_process([sys.executable, str(script)], timeout_seconds=5)
    assert result.returncode == 0
    assert result.stdout.endswith("done") and result.stderr.endswith("diagnostic")
    assert len(result.stdout) <= 2000 and len(result.stderr) <= 2000


def test_precancelled_attempt_never_launches(tmp_path):
    stop = Event()
    stop.set()
    with pytest.raises(process_runner.CaptureProcessStopped, match="capture_cancelled"):
        process_runner.run_capture_process([sys.executable, str(tmp_path / "missing.py")], timeout_seconds=1, stop=stop)


@pytest.mark.skipif(os.name != "nt", reason="Windows job assignment boundary")
def test_job_assignment_failure_never_runs_capture(tmp_path, monkeypatch):
    marker = tmp_path / "executed"
    script = tmp_path / "capture.py"
    script.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
    def deny(*args):
        raise PermissionError("injected job assignment denial")
    monkeypatch.setattr(process_runner._WindowsJob, "assign", deny)
    with pytest.raises(PermissionError, match="job assignment"):
        process_runner.run_capture_process([sys.executable, str(script)], timeout_seconds=1)
    assert not marker.exists()
