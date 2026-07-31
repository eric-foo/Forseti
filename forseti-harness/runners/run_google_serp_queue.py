"""CLI for the durable Google SERP queue safety controller."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.google_serp_queue_runtime import (  # noqa: E402
    GoogleSerpQueueError,
    initialize_queue,
    inspect_queue,
    next_action,
    report_outcome,
)


EXIT_BY_STATUS = {
    "cooldown": 3,
    "waiting_for_report": 4,
    "owner_ping": 5,
    "failed": 6,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Claim and settle exact Google SERP queue jobs through a durable "
            "block/cooldown/recovery state machine."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--jobs", required=True, type=Path)
    init.add_argument("--state", required=True, type=Path)
    init.add_argument("--owner-ping", required=True, type=Path)
    init.add_argument("--persistent-fallback-enabled", action="store_true")
    init.add_argument("--dedicated-logged-out-cdp-ready", action="store_true")
    init.add_argument("--operator-visible", action="store_true")
    init.add_argument("--rung", type=int, default=0)
    init.add_argument("--jobs-since-rungup", type=int)

    next_parser = sub.add_parser("next")
    next_parser.add_argument("--state", required=True, type=Path)
    next_parser.add_argument("--now")

    report = sub.add_parser("report")
    report.add_argument("--state", required=True, type=Path)
    report.add_argument("--job-id", required=True)
    report.add_argument(
        "--route", required=True, choices=("primary_route", "persistent_realchrome")
    )
    report.add_argument(
        "--outcome", required=True, choices=("success", "blocked", "failed")
    )
    report.add_argument("--packet-locator")
    report.add_argument("--now")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--state", required=True, type=Path)
    return parser


def _now(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            payload = initialize_queue(
                jobs_path=args.jobs,
                state_path=args.state,
                owner_ping_path=args.owner_ping,
                persistent_fallback_enabled=args.persistent_fallback_enabled,
                dedicated_logged_out_cdp_ready=args.dedicated_logged_out_cdp_ready,
                operator_visible=args.operator_visible,
                rung=args.rung,
                jobs_since_rungup=args.jobs_since_rungup,
            )
        elif args.command == "next":
            payload = next_action(state_path=args.state, now=_now(args.now))
        elif args.command == "report":
            payload = report_outcome(
                state_path=args.state,
                job_id=args.job_id,
                route=args.route,
                outcome=args.outcome,
                packet_locator=args.packet_locator,
                now=_now(args.now),
            )
        else:
            payload = inspect_queue(state_path=args.state)
    except (GoogleSerpQueueError, OSError, ValueError) as exc:
        parser.exit(
            status=2,
            message=f"google SERP queue failed: {type(exc).__name__}: {exc}\n",
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    status = payload.get("status")
    return EXIT_BY_STATUS.get(status, 0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
