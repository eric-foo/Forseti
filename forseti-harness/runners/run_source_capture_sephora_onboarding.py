"""Capture Sephora onboarding Q&A, review windows, and age counts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.root import DataLakeRoot
from source_capture.sephora_onboarding_capture import (
    DEFAULT_QUESTION_LIMIT,
    DEFAULT_RECENT_WINDOW_DAYS,
    DEFAULT_REVIEW_PAGE_LIMIT,
    capture_sephora_onboarding_packet,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Use a hash-verified rendered Sephora PDP or canonical aggregate-content "
            "parent packet to capture a raw-preserved Bazaarvoice onboarding companion. "
            "Aggregate-content parents trigger a target-bound live configuration refresh. "
            "The data root is explicit because this command performs live structured "
            "acquisition and commits append-only raw evidence."
        )
    )
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--parent-packet-id", required=True)
    parser.add_argument(
        "--configuration-source-packet-id",
        help=(
            "Optional hash-verified Sephora US packet whose preserved rendered DOM "
            "supplies tenant-level read configuration when the canonical content "
            "parent has none."
        ),
    )
    parser.add_argument(
        "--question-limit",
        type=int,
        default=DEFAULT_QUESTION_LIMIT,
        help="Bounded Most Answers question window (1-100; default 100).",
    )
    parser.add_argument(
        "--review-page-limit",
        type=int,
        default=DEFAULT_REVIEW_PAGE_LIMIT,
        help="Bazaarvoice page size for review snapshots (1-100; default 100).",
    )
    parser.add_argument(
        "--recent-window-days",
        type=int,
        default=DEFAULT_RECENT_WINDOW_DAYS,
        help="Most Recent source-date window in days (minimum/default 30).",
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=8_000_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = DataLakeRoot.resolve(explicit=args.data_root)
    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=args.parent_packet_id,
        question_limit=args.question_limit,
        review_page_limit=args.review_page_limit,
        recent_window_days=args.recent_window_days,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
        configuration_source_packet_id=args.configuration_source_packet_id,
    )
    summary = result["summary"]
    compact = {
        "packet_id": result["packet_id"],
        "output_directory": result["output_directory"],
        "record_kind": summary.get("record_kind"),
        "questions": summary.get("questions", {}),
        "reviews": summary.get("reviews", {}),
        "content_qualification": summary.get("content_qualification"),
        "row_accounting": summary.get("row_accounting"),
        "loss_ledger": summary.get("loss_ledger"),
        "raw_failure_fallback": summary.get("raw_failure_fallback"),
    }
    if isinstance(compact["questions"], dict):
        compact["questions"] = {
            key: value
            for key, value in compact["questions"].items()
            if key != "question_inventory"
        }
    if isinstance(compact["reviews"], dict):
        compact["reviews"] = dict(compact["reviews"])
        for view_name in ("most_helpful", "most_recent_30d"):
            view = compact["reviews"].get(view_name)
            if isinstance(view, dict):
                compact["reviews"][view_name] = {
                    key: value
                    for key, value in view.items()
                    if key
                    not in {
                        "review_inventory",
                        "captured_page_review_inventory",
                        "within_window_review_inventory",
                    }
                }
    print(json.dumps(compact, indent=2, sort_keys=True, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
