"""CLI for deterministic Google Ads Transparency Center packet projection."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.google_ads_transparency_projection import (  # noqa: E402
    build_google_ads_transparency_projection_from_packet_directory,
    google_ads_transparency_projection_json_text,
    write_google_ads_transparency_projection,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic, advertiser-bound creative-ID projection from "
            "an existing Google Ads Transparency Center Source Capture Packet."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--packet", type=Path, help="Packet directory or manifest.json path."
    )
    source.add_argument(
        "--packet-id", help="Committed raw packet id in the Forseti data lake."
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help=(
            "Forseti data-lake root for --packet-id. FORSETI_DATA_ROOT is used "
            "when omitted; legacy ORCA_DATA_ROOT is also accepted."
        ),
    )
    parser.add_argument("--advertiser-name", required=True)
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path; stdout when omitted.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing --output path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.packet is not None:
            if args.data_root is not None:
                raise ValueError("--data-root is only valid with --packet-id")
            packet_path = args.packet
        else:
            data_root_value = (
                args.data_root
                or os.environ.get("FORSETI_DATA_ROOT")
                or os.environ.get("ORCA_DATA_ROOT")
            )
            if not data_root_value:
                raise ValueError(
                    "--data-root or FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT) "
                    "is required with --packet-id"
                )
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=data_root_value)
            packet_path = data_root.find_packet(args.packet_id)
            if packet_path is None:
                raise FileNotFoundError(
                    f"raw packet not found: {args.packet_id}"
                )

        projection = (
            build_google_ads_transparency_projection_from_packet_directory(
                packet_path,
                expected_advertiser_name=args.advertiser_name,
                expected_advertiser_id=args.advertiser_id,
                expected_region=args.region,
            )
        )
        if args.output is not None:
            written = write_google_ads_transparency_projection(
                projection=projection,
                output_path=args.output,
                overwrite=args.overwrite,
            )
            print(written)
            return 0
        print(google_ads_transparency_projection_json_text(projection), end="")
        return 0
    except Exception as exc:  # noqa: BLE001 - packet failures stay controlled
        parser.exit(
            status=2,
            message=(
                "google ads transparency projection failed: "
                f"{type(exc).__name__}: {exc}\n"
            ),
        )


if __name__ == "__main__":
    raise SystemExit(main())
