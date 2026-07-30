"""Migrate, rebuild, query, and admit the lake-native Creator Registry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.creator_registry import (
    CreatorRegistryLakeError,
    admit_tiktok_creator_account,
    admit_tiktok_creator_candidate,
    admit_youtube_creator_account,
    admit_youtube_creator_candidate,
    cutover_creator_registry_sqlite,
    load_current_creator_profiles,
    load_current_creator_registry,
    migrate_legacy_registry,
    monitoring_eligible_accounts,
    publish_creator_registry_generation,
    retract_tiktok_creator_candidate,
)
from data_lake.root import DataLakeRoot, DataLakeRootError
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    load_creator_frontier_dispositions,
    write_creator_frontier_dispositions,
)


ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOT = (
    ROOT
    / "forseti"
    / "product"
    / "spines"
    / "capture"
    / "core"
    / "source_families"
    / "social_media"
    / "creator_registry"
)
DEFAULT_LEDGER = LEGACY_ROOT / "creator_public_handle_linkage_ledger_v0.json"
DEFAULT_INDEX = LEGACY_ROOT / "creator_registry_index_v0.json"
DEFAULT_PROFILE = LEGACY_ROOT / "creator_profile_current_view_v0.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    migrate = commands.add_parser("migrate")
    migrate.add_argument("--data-root", required=True)
    migrate.add_argument("--account-ledger", type=Path, default=DEFAULT_LEDGER)
    migrate.add_argument("--registry-index", type=Path, default=DEFAULT_INDEX)
    migrate.add_argument("--profile-current", type=Path, default=DEFAULT_PROFILE)
    mode = migrate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")

    rebuild = commands.add_parser("rebuild")
    rebuild.add_argument("--data-root", required=True)
    rebuild_mode = rebuild.add_mutually_exclusive_group(required=True)
    rebuild_mode.add_argument("--dry-run", action="store_true")
    rebuild_mode.add_argument("--write", action="store_true")

    cutover = commands.add_parser("cutover-sqlite")
    cutover.add_argument("--data-root", required=True)
    cutover_mode = cutover.add_mutually_exclusive_group(required=True)
    cutover_mode.add_argument("--dry-run", action="store_true")
    cutover_mode.add_argument("--write", action="store_true")

    show = commands.add_parser("show")
    show.add_argument("--data-root", required=True)
    show.add_argument("--view", choices=("internal", "public"), required=True)

    eligible = commands.add_parser("eligible")
    eligible.add_argument("--data-root", required=True)
    eligible.add_argument("--platform", choices=("instagram", "tiktok", "youtube"))

    admit = commands.add_parser("admit-tiktok")
    admit.add_argument("--data-root", required=True)
    admit.add_argument("--packet-id", required=True)
    admit.add_argument("--judgment-outcome", type=Path, required=True)

    admit_youtube = commands.add_parser("admit-youtube")
    admit_youtube.add_argument("--data-root", required=True)
    admit_youtube.add_argument("--packet-id", required=True)
    admit_youtube.add_argument("--judgment-outcome", type=Path, required=True)

    disposition = commands.add_parser("frontier-disposition")
    disposition.add_argument("--data-root", required=True)
    disposition.add_argument("--platform", choices=("tiktok", "youtube"), default="tiktok")
    disposition.add_argument("--handle", required=True)
    disposition.add_argument("--status", choices=("eligible", "deferred", "rejected"), required=True)
    disposition.add_argument("--priority", choices=("super", "high", "normal", "low"))
    disposition.add_argument(
        "--reason-code",
        choices=(
            "non_us_market", "us_market_unverified", "low_reach", "low_potential", "duplicate_or_backup",
            "profile_unavailable", "self_brand_only", "owner_choice", "other",
        ),
        required=True,
    )
    disposition.add_argument("--note")
    disposition.add_argument("--reconsideration", choices=("owner_reopen", "new_signal"))
    disposition.add_argument("--recorded-at")

    frontier_import = commands.add_parser("frontier-import")
    frontier_import.add_argument("--data-root", required=True)
    frontier_import.add_argument("--input", type=Path, required=True)
    frontier_import.add_argument("--recorded-at")

    frontier_show = commands.add_parser("frontier-show")
    frontier_show.add_argument("--data-root", required=True)

    candidate = commands.add_parser("admit-tiktok-candidate")
    candidate.add_argument("--data-root", required=True)
    candidate.add_argument("--packet-id", required=True)
    candidate.add_argument("--frontier-disposition-id", required=True)

    candidate_youtube = commands.add_parser("admit-youtube-candidate")
    candidate_youtube.add_argument("--data-root", required=True)
    candidate_youtube.add_argument("--packet-id", required=True)
    candidate_youtube.add_argument("--frontier-disposition-id", required=True)

    retract_candidate = commands.add_parser("retract-tiktok-candidate")
    retract_candidate.add_argument("--data-root", required=True)
    retract_candidate.add_argument("--handle", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        dry_run = args.command in {"migrate", "rebuild", "cutover-sqlite"} and args.dry_run
        root = (
            DataLakeRoot.resolve_readonly(explicit=args.data_root)
            if dry_run
            else DataLakeRoot.resolve(explicit=args.data_root)
        )
        if args.command == "migrate":
            result = migrate_legacy_registry(
                data_root=root,
                account_ledger_path=args.account_ledger,
                registry_index_path=args.registry_index,
                profile_current_path=args.profile_current,
                dry_run=args.dry_run,
            )
        elif args.command == "rebuild":
            result = publish_creator_registry_generation(root, dry_run=args.dry_run)
            result = {
                "status": "dry_run_passed" if args.dry_run else "rebuilt",
                **result,
            }
        elif args.command == "cutover-sqlite":
            result = cutover_creator_registry_sqlite(root, dry_run=args.dry_run)
        elif args.command == "show":
            result = (
                load_current_creator_registry(root)
                if args.view == "internal"
                else load_current_creator_profiles(root)
            )
        elif args.command == "eligible":
            rows = monitoring_eligible_accounts(root, platform=args.platform)
            result = {"platform": args.platform, "count": len(rows), "accounts": rows}
        elif args.command == "admit-tiktok":
            result = admit_tiktok_creator_account(
                data_root=root,
                packet_id=args.packet_id,
                judgment_outcome_path=args.judgment_outcome,
            )
        elif args.command == "admit-youtube":
            result = admit_youtube_creator_account(
                data_root=root,
                packet_id=args.packet_id,
                judgment_outcome_path=args.judgment_outcome,
            )
        elif args.command == "frontier-disposition":
            result = write_creator_frontier_dispositions(
                data_root=root,
                actions=[
                    {
                        "platform": args.platform,
                        "handle": args.handle,
                        "status": args.status,
                        "priority": args.priority,
                        "reason_code": args.reason_code,
                        "note": args.note,
                        "reconsideration": args.reconsideration,
                    }
                ],
                recorded_at=args.recorded_at,
            )
        elif args.command == "frontier-import":
            actions = json.loads(args.input.read_text(encoding="utf-8-sig"))
            if not isinstance(actions, list):
                raise ValueError("Frontier import input must be one JSON list of action objects")
            result = write_creator_frontier_dispositions(
                data_root=root,
                actions=actions,
                recorded_at=args.recorded_at,
            )
        elif args.command == "frontier-show":
            result = load_creator_frontier_dispositions(root)
        elif args.command == "admit-tiktok-candidate":
            result = admit_tiktok_creator_candidate(
                data_root=root,
                packet_id=args.packet_id,
                frontier_disposition_id=args.frontier_disposition_id,
            )
        elif args.command == "admit-youtube-candidate":
            result = admit_youtube_creator_candidate(
                data_root=root,
                packet_id=args.packet_id,
                frontier_disposition_id=args.frontier_disposition_id,
            )
        else:
            result = retract_tiktok_creator_candidate(
                data_root=root,
                public_handle=args.handle,
            )
    except (CreatorRegistryLakeError, DataLakeRootError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
