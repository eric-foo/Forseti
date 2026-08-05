"""CLI for the resumable Phase A Google-to-Reddit CO3 controller."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.phase_a_customer_evidence_pipeline import (  # noqa: E402
    PipelineBlocked,
    PipelineError,
    append_family,
    import_decisions,
    initialize_pipeline,
    inspect_pipeline,
    run_pipeline,
)


EXIT_BY_STATUS = {
    "waiting_for_decisions": 3,
    "resumable": 4,
    "interrupted_resumable": 4,
    "owner_ping": 5,
    "blocked": 6,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline qualified Google SERP discoveries into one paced, "
            "source-native Reddit capture worker for Phase A CO3."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--config", required=True, type=Path)
    init.add_argument("--run-root", required=True, type=Path)

    run = commands.add_parser("run")
    run.add_argument("--run-root", required=True, type=Path)

    status = commands.add_parser("status")
    status.add_argument("--run-root", required=True, type=Path)

    decisions = commands.add_parser("import-decisions")
    decisions.add_argument("--run-root", required=True, type=Path)
    decisions.add_argument("--decisions", required=True, type=Path)

    family = commands.add_parser("append-family")
    family.add_argument("--run-root", required=True, type=Path)
    family.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            payload = initialize_pipeline(config_path=args.config, run_root=args.run_root)
        elif args.command == "run":
            payload = run_pipeline(run_root=args.run_root)
        elif args.command == "status":
            payload = inspect_pipeline(run_root=args.run_root)
        elif args.command == "import-decisions":
            payload = import_decisions(run_root=args.run_root, decisions_path=args.decisions)
        else:
            payload = append_family(run_root=args.run_root, manifest_path=args.manifest)
    except PipelineBlocked as exc:
        parser.exit(status=6, message=f"phase A customer evidence pipeline blocked: {exc}\n")
    except (PipelineError, OSError, ValueError) as exc:
        parser.exit(
            status=2,
            message=(
                "phase A customer evidence pipeline failed: "
                f"{type(exc).__name__}: {exc}\n"
            ),
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return EXIT_BY_STATUS.get(payload.get("status"), 0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
