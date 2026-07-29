"""Capture one held Google job through the persistent operator-visible route.

This wrapper is the queue-runner seam used after a lower-route block. It keeps
one marked tab, preserves every block packet, notifies once per distinct block,
waits without navigation while the operator clears the visible challenge, then
recaptures the exact URL. It never clicks or solves the challenge.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners.run_source_capture_realchrome_cdp_packet import (
    DEFAULT_CDP_ENDPOINT,
    RealChromeCDPUnavailable,
    run_source_capture_realchrome_cdp_packet,
)
from source_capture.rendered_access import (
    RenderedAccessClass,
    classify_rendered_access,
)
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
    SourceDetailSufficiencyRequirements,
)


DEFAULT_POLL_SECONDS = 5.0
PERSISTENT_BLOCK_ROUTE_MODE = "block_route:persistent_realchrome"


def _normalize_query(value: str) -> str:
    return " ".join(value.split()).casefold()


def inspect_persistent_google_tab(*, cdp_endpoint: str, marker: str) -> dict:
    """Read the marker-owned tab without navigation or interaction."""
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependency
        raise RealChromeCDPUnavailable(
            "playwright is required for persistent-tab inspection"
        ) from exc

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(cdp_endpoint)
        except Exception as exc:
            raise RealChromeCDPUnavailable(
                f"could not inspect real Chrome at {cdp_endpoint}: {exc}"
            ) from exc
        if not browser.contexts:
            raise RealChromeCDPUnavailable(
                "attached Chrome exposes no normal browser context"
            )
        page = None
        for candidate in browser.contexts[0].pages:
            if candidate.is_closed():
                continue
            try:
                if candidate.evaluate("() => window.name") == marker:
                    page = candidate
                    break
            except Exception:
                continue
        if page is None:
            raise RealChromeCDPUnavailable(
                f"persistent capture tab {marker!r} is not open"
            )
        rendered_dom = page.content()
        visible_text = page.locator("body").inner_text(timeout=10_000)
        title = page.title()
        access = classify_rendered_access(
            title=title,
            rendered_dom=rendered_dom,
            visible_text=visible_text,
        )
        rendered_query = parse_qs(urlparse(page.url).query).get("q", [""])[0]
        return {
            "url": page.url,
            "query": rendered_query,
            "access_blocked": (
                access.classification == RenderedAccessClass.ACCESS_BLOCKED
            ),
            "access_signal": access.signal,
        }


def notify_operator_once(*, job_id: str, query: str) -> None:
    message = (
        f"Forseti Google block alert\n{job_id}: {query}\n"
        "Navigation is paused. Manually clear the visible challenge in the "
        "persistent capture tab; the held query will then resume."
    )
    # stderr keeps the alert fail-visible to the supervising process even when
    # the best-effort desktop toast or beep is unavailable.
    print(message, file=sys.stderr, flush=True)
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass
    if os.name == "nt":
        try:
            subprocess.run(
                ["msg.exe", "*", message],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
        except Exception:
            pass


def _archive_block_packet(*, output: Path, archive_root: Path, job_id: str) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = archive_root / f"{job_id}_{stamp}"
    shutil.move(str(output), str(target))
    return target


def run_google_serp_persistent_fallback(
    *,
    url: str,
    query: str,
    job_id: str,
    output: Path,
    block_archive: Path,
    cdp_endpoint: str,
    marker: str,
    decision_question: str,
    source_family: str = "search_discovery",
    source_surface: str = "google_serp_us_parameterized_realchrome_cdp",
    capture_context: str | None = None,
    settle_seconds: float = 8.0,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    capture_func: Callable[..., tuple[int, str]] = run_source_capture_realchrome_cdp_packet,
    inspect_func: Callable[..., dict] = inspect_persistent_google_tab,
    notify_func: Callable[..., None] = notify_operator_once,
    sleep_func: Callable[[float], None] = time.sleep,
) -> tuple[int, str]:
    """Capture, waiting through operator-cleared blocks without hot navigation."""
    parsed_url = urlparse(url)
    if (parsed_url.hostname or "").casefold() not in {"google.com", "www.google.com"}:
        raise ValueError("persistent Google fallback requires a google.com search URL")
    url_query = parse_qs(parsed_url.query).get("q", [""])[0]
    if _normalize_query(url_query) != _normalize_query(query):
        raise ValueError("URL query must match the held query exactly")

    alert_path = block_archive / "block_alert.json"
    while True:
        code, message = capture_func(
            url=url,
            source_family=source_family,
            source_surface=source_surface,
            decision_question=decision_question,
            output_directory=output,
            capture_context=capture_context,
            cdp_endpoint=cdp_endpoint,
            settle_seconds=settle_seconds,
            persistent_tab_marker=marker,
            fit_viewport_to_window=True,
            visible_mode_changes=(PERSISTENT_BLOCK_ROUTE_MODE,),
            source_detail_sufficiency_requirements=SourceDetailSufficiencyRequirements(
                require_not_access_blocked=True
            ),
        )
        if code != SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE:
            # The process is no longer waiting for an operator, whether the
            # terminal result is success or a different visible failure.
            alert_path.unlink(missing_ok=True)
            return code, message

        archived = _archive_block_packet(
            output=output, archive_root=block_archive, job_id=job_id
        )
        alert = {
            "status": "blocked_waiting_operator",
            "job_id": job_id,
            "query": query,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "preserved_block_packet": str(archived),
        }
        alert_path.write_text(
            json.dumps(alert, indent=2) + "\n", encoding="utf-8"
        )
        # Once per DISTINCT block, not once per job: the inner loop below only
        # exits after the operator has cleared the challenge and the tab has
        # rendered the held query unblocked, so reaching this line again is a
        # genuinely new block. Latching on the first one leaves every later
        # block in the same job waiting silently and forever.
        notify_func(job_id=job_id, query=query)

        while True:
            sleep_func(poll_seconds)
            try:
                state = inspect_func(cdp_endpoint=cdp_endpoint, marker=marker)
            except RealChromeCDPUnavailable:
                continue
            if (
                not state["access_blocked"]
                and _normalize_query(state["query"]) == _normalize_query(query)
            ):
                break


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture a held Google job through one persistent real-Chrome tab."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--block-archive", required=True, type=Path)
    parser.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    parser.add_argument("--persistent-tab-marker", required=True)
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--capture-context")
    parser.add_argument("--settle-seconds", type=float, default=8.0)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        code, message = run_google_serp_persistent_fallback(
            url=args.url,
            query=args.query,
            job_id=args.job_id,
            output=args.output,
            block_archive=args.block_archive,
            cdp_endpoint=args.cdp_endpoint,
            marker=args.persistent_tab_marker,
            decision_question=args.decision_question,
            capture_context=args.capture_context,
            settle_seconds=args.settle_seconds,
            poll_seconds=args.poll_seconds,
        )
    except (RealChromeCDPUnavailable, ValueError) as exc:
        parser.exit(status=3, message=f"persistent Google fallback unavailable: {exc}\n")
    if code == 0:
        print(message)
        return 0
    parser.exit(status=code, message=f"persistent Google fallback failed: {message}\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
