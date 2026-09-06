"""Bound Python capture runners while retained browsers outlive the attempt."""
from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile
import time
from threading import Event
from typing import Sequence

RETAINED_BROWSER_BREAKAWAY_ENV = "FORSETI_CAPTURE_JOB_ISOLATED"


class CaptureProcessStopped(RuntimeError):
    def __init__(self, reason: str, cleanup_error: str | None = None):
        self.reason, self.cleanup_error = reason, cleanup_error
        super().__init__(f"capture_{reason}" + (f"; cleanup failed: {cleanup_error}" if cleanup_error else ""))


class _WindowsJob:
    """Own all capture descendants except explicit retained-browser breakaways."""
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c = c
        self.api = c.WinDLL("kernel32", use_last_error=True)
        class Basic(c.Structure):
            _fields_ = [("user_time", c.c_int64), ("job_time", c.c_int64), ("flags", w.DWORD),
                        ("min_working", c.c_size_t), ("max_working", c.c_size_t),
                        ("active_limit", w.DWORD), ("affinity", c.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class Extended(c.Structure):
            _fields_ = [("basic", Basic), ("io_counters", c.c_uint64 * 6),
                        ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                        ("peak_process_memory", c.c_size_t), ("peak_job_memory", c.c_size_t)]
        for name, args, result in (
            ("CreateJobObjectW", [c.c_void_p, w.LPCWSTR], w.HANDLE),
            ("SetInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
            ("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL),
            ("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL),
            ("QueryInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL),
            ("CloseHandle", [w.HANDLE], w.BOOL),
        ):
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000 | 0x0800  # KILL_ON_JOB_CLOSE | BREAKAWAY_OK
        if not self.api.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits)):
            error = c.WinError(c.get_last_error())
            self.close()
            raise error

    def assign(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise self.c.WinError(self.c.get_last_error())

    def stop(self):
        if not self.api.TerminateJobObject(self.handle, 1):
            raise self.c.WinError(self.c.get_last_error())
        # BASIC_ACCOUNTING_INFORMATION: four 64-bit times followed by four DWORDs.
        accounting = self.c.create_string_buffer(48)
        deadline = time.monotonic() + 5
        while True:
            if not self.api.QueryInformationJobObject(self.handle, 1, accounting, 48, None):
                raise self.c.WinError(self.c.get_last_error())
            if int.from_bytes(accounting.raw[40:44], "little") == 0:
                return
            if time.monotonic() >= deadline:
                raise RuntimeError("owned capture descendants may still be running")
            time.sleep(0.01)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def run_capture_process(command: Sequence[str], *, timeout_seconds: float,
                        stop: Event | None = None) -> subprocess.CompletedProcess[str]:
    """Run a Python script with bounded output memory and an owned process group.

    The stdin handshake prevents a Windows child from spawning before job assignment.
    Retained Chrome explicitly escapes this job (or uses its own POSIX session).
    """
    if isinstance(timeout_seconds, bool) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("capture timeout_seconds must be finite and positive")
    if stop is not None and stop.is_set():
        raise CaptureProcessStopped("cancelled")
    deadline = time.monotonic() + timeout_seconds
    job = _WindowsJob() if os.name == "nt" else None
    creation = ({"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
                if os.name == "nt" else {"start_new_session": True})
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    if job is not None:
        env[RETAINED_BROWSER_BREAKAWAY_ENV] = "1"
    else:
        env.pop(RETAINED_BROWSER_BREAKAWAY_ENV, None)
    bootstrap = ("import sys, runpy; "
                 "assert sys.stdin.buffer.read(1) == b'x', 'capture launch handshake failed'; "
                 "sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')")
    process, failure, reason, cleanup = None, None, None, None
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen([command[0], "-c", bootstrap, *command[1:]],
                                       stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                       env=env, **creation)
            if job is not None:
                job.assign(process)
            process.stdin.write(b"x")
            process.stdin.close()
            while True:
                if stop is not None and stop.is_set():
                    reason = "cancelled"
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    reason = "deadline_exceeded"
                    break
                if process.poll() is not None:
                    break
                try:
                    process.wait(timeout=min(0.1, remaining))
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as exc:
            failure = exc
        finally:
            try:
                if process is not None:
                    if job is not None:
                        job.stop()
                    else:
                        from provider_execution import _stop_process_tree
                        cleanup = _stop_process_tree(process)
                    if process.poll() is None:  # also covers failed Windows job assignment
                        process.kill()
                    process.wait(timeout=5)
            except Exception as exc:
                cleanup = f"{type(exc).__name__}: {exc}"
            finally:
                if process is not None and process.stdin is not None:
                    process.stdin.close()
                if job is not None:
                    job.close()
        if reason or cleanup:
            raise CaptureProcessStopped(reason or "cleanup_failed", cleanup) from failure
        if failure is not None:
            raise failure
        def tail(stream):
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 2000))
            return stream.read().decode("utf-8", "replace")
        return subprocess.CompletedProcess(list(command), process.returncode, tail(stdout), tail(stderr))
