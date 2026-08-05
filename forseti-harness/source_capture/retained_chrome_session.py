"""Launch or reuse one visible Chrome CDP session bound to retained user data.

The public result is deliberately sanitized: callers receive the loopback CDP
endpoint and launch disposition, never the browser profile path or process
command line.  This module does not navigate, inspect profile contents, close
Chrome, or interact with challenges.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urlparse

from source_capture.adapters.browser_session_probe import (
    probe_local_cdp_endpoints,
    select_profile_bound_local_cdp_endpoint,
)


DEFAULT_RETAINED_CHROME_CDP_PORT = 9223
DEFAULT_RETAINED_CHROME_STARTUP_TIMEOUT_SECONDS = 15.0
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True)
class RetainedChromeSession:
    cdp_endpoint: str
    disposition: str

    def sanitized_receipt(self) -> dict[str, object]:
        return {
            "status": "ready",
            "cdp_endpoint": self.cdp_endpoint,
            "disposition": self.disposition,
            "profile_bound": True,
            "browser_visible": True,
            "profile_path_exposed": False,
        }


def ensure_retained_chrome_session(
    *,
    user_data_dir: Path,
    cdp_endpoint: str = f"http://127.0.0.1:{DEFAULT_RETAINED_CHROME_CDP_PORT}",
    launch_url: str = "about:blank",
    startup_timeout_seconds: float = DEFAULT_RETAINED_CHROME_STARTUP_TIMEOUT_SECONDS,
    probe_func: Callable[..., dict[str, object]] = probe_local_cdp_endpoints,
    select_func: Callable[..., str] = select_profile_bound_local_cdp_endpoint,
    profile_running_func: Callable[[Path], bool] | None = None,
    chrome_executable_func: Callable[[], Path] | None = None,
    launch_func: Callable[..., object] | None = None,
    sleep_func: Callable[[float], None] = time.sleep,
    monotonic_func: Callable[[], float] = time.monotonic,
) -> RetainedChromeSession:
    """Return the exact retained-profile endpoint, launching visible Chrome if absent."""
    resolved_user_data_dir = user_data_dir.resolve()
    if not resolved_user_data_dir.is_dir() or not any(resolved_user_data_dir.iterdir()):
        raise ValueError("retained browser profile is missing or empty")
    endpoint, port = _validated_loopback_endpoint(cdp_endpoint)
    if not isinstance(startup_timeout_seconds, (int, float)) or isinstance(
        startup_timeout_seconds, bool
    ) or startup_timeout_seconds <= 0:
        raise ValueError("startup_timeout_seconds must be positive")

    def probe() -> dict[str, object]:
        return probe_func((port,))

    report = probe()
    try:
        selected = select_func(report, user_data_dir=resolved_user_data_dir)
    except ValueError:
        selected = None
    if selected is not None:
        if _normalized_endpoint(selected) != endpoint:
            raise ValueError("retained Chrome is bound to an unexpected CDP endpoint")
        return RetainedChromeSession(cdp_endpoint=endpoint, disposition="reused")

    is_profile_running = profile_running_func or _windows_profile_root_process_running
    if is_profile_running(resolved_user_data_dir):
        raise ValueError(
            "BLOCKED_RETAINED_PROFILE_OPEN_WITHOUT_CDP: close that retained Chrome "
            "window and rerun; the harness never closes operator Chrome"
        )
    if endpoint in report.get("live_endpoints", []):
        raise ValueError(
            "BLOCKED_CDP_ENDPOINT_OWNED_BY_DIFFERENT_PROFILE: requested loopback "
            "endpoint is already in use"
        )

    find_chrome = chrome_executable_func or _find_chrome_executable
    launch = launch_func or _launch_visible_chrome
    launch(
        chrome_executable=find_chrome(),
        user_data_dir=resolved_user_data_dir,
        port=port,
        launch_url=launch_url,
    )

    deadline = monotonic_func() + float(startup_timeout_seconds)
    last_error: ValueError | None = None
    while monotonic_func() < deadline:
        sleep_func(0.25)
        report = probe()
        try:
            selected = select_func(report, user_data_dir=resolved_user_data_dir)
        except ValueError as exc:
            last_error = exc
            continue
        if _normalized_endpoint(selected) != endpoint:
            raise ValueError("retained Chrome launched on an unexpected CDP endpoint")
        return RetainedChromeSession(cdp_endpoint=endpoint, disposition="launched")
    raise ValueError(
        "BLOCKED_RETAINED_CHROME_CDP_STARTUP: launched Chrome did not prove the "
        "exact retained-profile endpoint before timeout"
    ) from last_error


def _validated_loopback_endpoint(value: str) -> tuple[str, int]:
    parsed = urlparse(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOCAL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("cdp_endpoint must be a credential-free loopback HTTP origin")
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is None:
        raise ValueError("cdp_endpoint must include an explicit port")
    return f"http://127.0.0.1:{port}", port


def _normalized_endpoint(value: str) -> str:
    return _validated_loopback_endpoint(value)[0]


def _find_chrome_executable() -> Path:
    configured = os.environ.get("FORSETI_CHROME_EXECUTABLE")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    discovered = shutil.which("chrome") or shutil.which("chrome.exe")
    if discovered:
        candidates.append(Path(discovered))
    for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        root = os.environ.get(env_name)
        if root:
            candidates.append(Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError("BLOCKED_CHROME_EXECUTABLE_UNAVAILABLE")


def _launch_visible_chrome(
    *, chrome_executable: Path, user_data_dir: Path, port: int, launch_url: str
) -> subprocess.Popen[bytes]:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    return subprocess.Popen(
        [
            str(chrome_executable),
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            launch_url,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        close_fds=True,
    )


def _windows_profile_root_process_running(user_data_dir: Path) -> bool:
    if os.name != "nt":
        raise ValueError(
            "retained Chrome profile process binding is currently supported on Windows only"
        )
    env = os.environ.copy()
    env["FORSETI_EXPECTED_CHROME_USER_DATA_DIR"] = str(user_data_dir)
    script = r"""
$ErrorActionPreference = 'Stop'
$expected = [System.IO.Path]::GetFullPath(
  $env:FORSETI_EXPECTED_CHROME_USER_DATA_DIR
).TrimEnd([char[]]@(
  [System.IO.Path]::DirectorySeparatorChar,
  [System.IO.Path]::AltDirectorySeparatorChar
))
$found = $false
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -and $_.CommandLine -notmatch '(?i)(?:^|\s)--type=' } |
  ForEach-Object {
    if ($_.CommandLine -notmatch '(?i)(?:^|\s)--user-data-dir=(?:"([^"]+)"|(\S+))') { return }
    $candidate = if ($Matches[1]) { $Matches[1] } else { $Matches[2] }
    try {
      $candidate = [System.IO.Path]::GetFullPath($candidate).TrimEnd([char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
      ))
    } catch { return }
    if ($candidate.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
      $found = $true
    }
  }
@{ running = $found } | ConvertTo-Json -Compress
"""
    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            check=False,
            env=env,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("unable to verify retained Chrome profile process state") from None
    if completed.returncode != 0:
        raise ValueError("unable to verify retained Chrome profile process state")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise ValueError("retained Chrome profile process state returned invalid data") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("running"), bool):
        raise ValueError("retained Chrome profile process state returned invalid data")
    return payload["running"]


__all__ = [
    "DEFAULT_RETAINED_CHROME_CDP_PORT",
    "DEFAULT_RETAINED_CHROME_STARTUP_TIMEOUT_SECONDS",
    "RetainedChromeSession",
    "ensure_retained_chrome_session",
]
