"""Probe local CDP endpoints before declaring a controllable browser unavailable.

Probe-and-report only: this module never attaches, navigates, captures, or
mutates browser state. It exists because a prior TikTok scan lane declared
"no controllable browser session" while a CloakBrowser CDP endpoint was
listening on 127.0.0.1:9223 -- an unavailability claim must now be backed by
a probe report naming the endpoints actually checked.

Local-only posture mirrors the LinkedIn lane's CDP attach rules: loopback
hosts only, no embedded credentials, no remote relays.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import urlparse

DEFAULT_CDP_PROBE_PORTS: tuple[int, ...] = (9222, 9223)
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_DEFAULT_TIMEOUT_SECONDS = 2.0


def probe_local_cdp_endpoints(
    ports: Sequence[int] = DEFAULT_CDP_PROBE_PORTS,
    *,
    host: str = "127.0.0.1",
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    opener: Callable[[str, float], str] | None = None,
) -> dict[str, Any]:
    """Return a probe report over ``http://<host>:<port>/json/version`` checks.

    ``opener`` is injectable for tests: it receives (url, timeout_seconds) and
    returns the response body text, raising on failure. The report is data,
    not authorization: a live endpoint proves reachability only.
    """
    if host not in _LOCAL_HOSTS:
        raise ValueError(
            f"probe host must be local ({sorted(_LOCAL_HOSTS)}); refusing {host!r}"
        )
    if not ports:
        raise ValueError("probe requires at least one port")
    for port in ports:
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            raise ValueError(f"probe port must be an integer in 1..65535; got {port!r}")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ValueError(f"probe timeout_seconds must be positive; got {timeout_seconds!r}")
    # IPv6 literals need brackets in URLs (http://[::1]:9223).
    host_for_url = f"[{host}]" if ":" in host else host
    read = opener or _http_get
    probed: list[dict[str, Any]] = []
    live_endpoints: list[str] = []
    for port in ports:
        endpoint = f"http://{host_for_url}:{int(port)}"
        url = f"{endpoint}/json/version"
        entry: dict[str, Any] = {
            "endpoint": endpoint,
            "live": False,
            "browser_or_none": None,
            "error_or_none": None,
        }
        try:
            body = read(url, timeout_seconds)
            entry["live"] = True
            try:
                version = json.loads(body)
                if isinstance(version, dict):
                    browser = version.get("Browser")
                    if isinstance(browser, str) and browser.strip():
                        entry["browser_or_none"] = browser
            except ValueError:
                pass  # live but non-JSON body: reachability stands, identity unknown
            live_endpoints.append(endpoint)
        except Exception as exc:  # noqa: BLE001 - each endpoint reports its own failure
            entry["error_or_none"] = f"{type(exc).__name__}: {exc}"
        probed.append(entry)
    return {
        "probe_kind": "local_cdp_endpoint_probe",
        "host": host,
        "ports_checked": [int(port) for port in ports],
        "probed": probed,
        "live_endpoints": live_endpoints,
        "browser_available": bool(live_endpoints),
    }


def select_profile_bound_local_cdp_endpoint(
    report: dict[str, Any],
    *,
    user_data_dir: Path,
    bound_port_reader: Callable[[Path], Sequence[int]] | None = None,
) -> str:
    """Select the one live endpoint owned by the retained Chrome profile.

    Endpoint reachability alone is not identity. On Windows the default reader
    checks the browser process command line and returns only the CDP ports whose
    root Chrome process was launched with the exact retained user-data path.
    Raw process command lines and profile paths never enter the returned report.
    """
    live_endpoints = report.get("live_endpoints")
    if not isinstance(live_endpoints, list):
        raise ValueError("Chrome CDP probe returned invalid live endpoint data")
    read_bound_ports = bound_port_reader or _windows_profile_bound_cdp_ports
    bound_ports = set(read_bound_ports(user_data_dir.resolve()))
    matching: list[str] = []
    for endpoint in live_endpoints:
        if not isinstance(endpoint, str):
            raise ValueError("Chrome CDP probe returned an invalid loopback endpoint")
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in _LOCAL_HOSTS:
            raise ValueError("Chrome CDP probe returned a non-loopback endpoint")
        try:
            port = parsed.port
        except ValueError:
            raise ValueError("Chrome CDP probe returned an invalid loopback port") from None
        if port in bound_ports:
            matching.append(endpoint)
    if len(matching) != 1:
        raise ValueError(
            "Chrome CDP requires exactly one live endpoint bound to the retained "
            f"browser profile; observed {len(matching)}"
        )
    return matching[0]


def _windows_profile_bound_cdp_ports(user_data_dir: Path) -> tuple[int, ...]:
    """Return sanitized CDP ports for root Chrome processes using ``user_data_dir``."""
    if os.name != "nt":
        raise ValueError(
            "retained Chrome profile process binding is currently supported on Windows only"
        )
    env = os.environ.copy()
    env["FORSETI_EXPECTED_CDP_USER_DATA_DIR"] = str(user_data_dir)
    script = r"""
$ErrorActionPreference = 'Stop'
$expected = [System.IO.Path]::GetFullPath(
  $env:FORSETI_EXPECTED_CDP_USER_DATA_DIR
).TrimEnd([char[]]@(
  [System.IO.Path]::DirectorySeparatorChar,
  [System.IO.Path]::AltDirectorySeparatorChar
))
$ports = @(
  Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
    Where-Object {
      $_.CommandLine -and $_.CommandLine -notmatch '(?i)(?:^|\s)--type='
    } |
    ForEach-Object {
      $commandLine = $_.CommandLine
      if ($commandLine -notmatch '(?i)(?:^|\s)--user-data-dir=(?:"([^"]+)"|(\S+))') {
        return
      }
      $profileArgument = if ($Matches[1]) { $Matches[1] } else { $Matches[2] }
      try {
        $profilePath = [System.IO.Path]::GetFullPath($profileArgument).TrimEnd(
          [char[]]@(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
          )
        )
      } catch {
        return
      }
      if (-not $profilePath.Equals(
        $expected,
        [System.StringComparison]::OrdinalIgnoreCase
      )) {
        return
      }
      if ($commandLine -match '(?i)(?:^|\s)--remote-debugging-port=(\d{1,5})(?:\s|$)') {
        [int]$Matches[1]
      }
    } |
    Sort-Object -Unique
)
@($ports) | ConvertTo-Json -Compress
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
        raise ValueError("unable to verify retained Chrome profile process binding") from None
    if completed.returncode != 0:
        raise ValueError("unable to verify retained Chrome profile process binding")
    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        raise ValueError("retained Chrome profile process binding returned invalid data") from None
    if isinstance(payload, int):
        payload = [payload]
    if not isinstance(payload, list) or any(
        not isinstance(port, int)
        or isinstance(port, bool)
        or not 1 <= port <= 65535
        for port in payload
    ):
        raise ValueError("retained Chrome profile process binding returned invalid ports")
    return tuple(payload)


def _http_get(url: str, timeout_seconds: float) -> str:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - loopback-only by construction
        return response.read().decode("utf-8", errors="replace")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe local CDP endpoints and print a JSON probe report. Report-only: "
            "never attaches to or mutates a browser."
        )
    )
    parser.add_argument(
        "--port",
        action="append",
        type=int,
        dest="ports",
        help=f"Port to probe on 127.0.0.1. Repeatable. Defaults to {DEFAULT_CDP_PROBE_PORTS}.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=_DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = probe_local_cdp_endpoints(
        tuple(args.ports) if args.ports else DEFAULT_CDP_PROBE_PORTS,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
