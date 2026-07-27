from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.reddit_thread_qualification import (
    RedditThreadQualificationFailure,
    build_reddit_thread_qualification,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Qualify already-captured weekly Reddit threads as low leads, stacked "
            "emerging signals, priority signals, or critical signals without "
            "fetching Reddit again."
        )
    )
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--batch-summary", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        artifact = build_reddit_thread_qualification(
            selection_path=args.selection,
            batch_summary_path=args.batch_summary,
            labels_path=args.labels,
        )
        if args.output.exists():
            raise RedditThreadQualificationFailure(
                "output_exists",
                f"output already exists: {args.output}",
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except RedditThreadQualificationFailure as exc:
        parser.exit(
            status=3,
            message=f"reddit thread qualification refused [{exc.code}]: {exc.message}\n",
        )
    except Exception as exc:
        parser.exit(status=2, message=f"reddit thread qualification failed: {exc}\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
