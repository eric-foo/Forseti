from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.cli_support import build_optional_fact
from source_capture.models import (
    CUTOFF_POSTURE_VALUES,
    CaptureModeCategory,
    VisibleFact,
    known_fact,
    unknown_with_reason,
)
from source_capture.writer import write_local_source_capture_packet

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot


def build_source_locator(*, source_locator: str | None, unknown_reason: str | None) -> VisibleFact:
    if source_locator:
        return known_fact(source_locator)
    if unknown_reason:
        return unknown_with_reason(unknown_reason)
    raise ValueError("either --source-locator or --source-locator-unknown-reason is required")


def build_cutoff_posture(
    *, value: str | None, unknown_reason: str | None
) -> VisibleFact | None:
    fact = build_optional_fact(
        label="cutoff posture",
        value=value,
        unknown_reason=unknown_reason,
    )
    if value is not None and value not in CUTOFF_POSTURE_VALUES:
        allowed = ", ".join(sorted(CUTOFF_POSTURE_VALUES))
        raise ValueError(f"cutoff posture must be one of: {allowed}")
    return fact


def run_source_capture_packet(
    *,
    source_family: str,
    source_surface: str,
    source_locator: VisibleFact,
    decision_question: str,
    input_files: Sequence[Path],
    output_directory: Path | None = None,
    data_root: "DataLakeRoot | None" = None,
    capture_context: str,
    operator_category: str,
    capture_mode: CaptureModeCategory,
    session_id: str | None,
    actor_audience_context: VisibleFact | None,
    visible_mode_changes: Sequence[str],
    source_publication_or_event: VisibleFact | None,
    source_edit_or_version: VisibleFact | None,
    cutoff_posture: VisibleFact | None,
    capture_time: VisibleFact | None = None,
    recapture_time: VisibleFact | None,
    access_posture: VisibleFact | None,
    archive_history_posture: VisibleFact | None,
    media_modality_posture: VisibleFact | None,
    re_capture_relationship: VisibleFact | None,
    warnings: Sequence[str],
    limitations: Sequence[str],
) -> str:
    result = write_local_source_capture_packet(
        output_directory=output_directory,
        data_root=data_root,
        input_files=input_files,
        source_family=source_family,
        source_surface=source_surface,
        source_locator=source_locator,
        decision_question=decision_question,
        capture_context=capture_context,
        actor_audience_context=actor_audience_context,
        capture_mode=capture_mode,
        operator_category=operator_category,
        session_identity=session_id,
        visible_mode_changes=visible_mode_changes,
        source_publication_or_event=source_publication_or_event,
        source_edit_or_version=source_edit_or_version,
        cutoff_posture=cutoff_posture,
        capture_time=capture_time,
        recapture_time=recapture_time,
        access_posture=access_posture,
        archive_history_posture=archive_history_posture,
        media_modality_posture=media_modality_posture,
        re_capture_relationship=re_capture_relationship,
        warnings=warnings,
        limitations=limitations,
    )
    return result.output_directory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Package already-local source artifacts into a no-network Source Capture Packet directory."
    )
    parser.add_argument("--source-family", required=True)
    parser.add_argument("--source-surface", default="local_file_artifact")
    locator_group = parser.add_mutually_exclusive_group(required=True)
    locator_group.add_argument("--source-locator")
    locator_group.add_argument("--source-locator-unknown-reason")
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--input-file", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        default=None,
        help="Commit into the Forseti data lake at this root; explicit --data-root is mutually exclusive with --output. FORSETI_DATA_ROOT is used only when --output is omitted; legacy ORCA_DATA_ROOT is also accepted.",
    )
    parser.add_argument(
        "--capture-context",
        default="local file packaging of already-local source artifacts",
    )
    parser.add_argument("--operator-category", default="local_cli_operator")
    parser.add_argument(
        "--capture-mode",
        choices=[item.value for item in CaptureModeCategory],
        default=CaptureModeCategory.AGENT_ASSISTED.value,
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--actor-audience-context", default=None)
    parser.add_argument("--actor-audience-context-unknown-reason", default=None)
    parser.add_argument("--visible-mode-change", action="append", default=[])
    parser.add_argument("--source-publication-or-event", default=None)
    parser.add_argument("--source-publication-or-event-unknown-reason", default=None)
    parser.add_argument("--source-edit-or-version", default=None)
    parser.add_argument("--source-edit-or-version-unknown-reason", default=None)
    parser.add_argument(
        "--cutoff-posture",
        default=None,
        help=f"Known cutoff posture; one of: {', '.join(sorted(CUTOFF_POSTURE_VALUES))}",
    )
    parser.add_argument("--cutoff-posture-unknown-reason", default=None)
    parser.add_argument(
        "--capture-time",
        default=None,
        help=(
            "Original capture/access time for packaging an earlier already-local "
            "artifact set. Omit to use packet-generation time."
        ),
    )
    parser.add_argument("--recapture-time", default=None)
    parser.add_argument("--recapture-time-not-applicable-reason", default=None)
    parser.add_argument("--access-posture", default=None)
    parser.add_argument("--access-posture-unknown-reason", default=None)
    parser.add_argument("--access-posture-not-attempted-reason", default=None)
    parser.add_argument("--archive-history-posture", default=None)
    parser.add_argument("--archive-history-not-attempted-reason", default=None)
    parser.add_argument("--media-modality-posture", default=None)
    parser.add_argument("--media-modality-not-attempted-reason", default=None)
    parser.add_argument("--recapture-relationship", default=None)
    parser.add_argument("--recapture-relationship-not-applicable-reason", default=None)
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--limitation", action="append", default=[])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        cutoff_posture = build_cutoff_posture(
            value=args.cutoff_posture,
            unknown_reason=args.cutoff_posture_unknown_reason,
        )
    except Exception as exc:
        parser.exit(status=2, message=f"source capture packet failed: {exc}\n")

    # helper-delta: vs runners/_scaffold.resolve_output_root -- unprefixed messages,
    # resolution outside any try, and the exactly-one xor check re-runs after resolution.
    data_root = None
    if args.output is not None and args.data_root is not None:
        parser.exit(
            status=2,
            message="exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
        )
    data_root_requested = args.data_root is not None or (
        args.output is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))
    )
    if data_root_requested:
        from data_lake.root import DataLakeRoot

        data_root = DataLakeRoot.resolve(explicit=args.data_root)
    if (args.output is None) == (data_root is None):
        parser.exit(
            status=2,
            message="exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
        )
    try:
        output_directory = run_source_capture_packet(
            source_family=args.source_family,
            source_surface=args.source_surface,
            source_locator=build_source_locator(
                source_locator=args.source_locator,
                unknown_reason=args.source_locator_unknown_reason,
            ),
            decision_question=args.decision_question,
            input_files=args.input_file,
            output_directory=args.output,
            data_root=data_root,
            capture_context=args.capture_context,
            operator_category=args.operator_category,
            capture_mode=CaptureModeCategory(args.capture_mode),
            session_id=args.session_id,
            actor_audience_context=build_optional_fact(
                label="actor/audience context",
                value=args.actor_audience_context,
                unknown_reason=args.actor_audience_context_unknown_reason,
            ),
            visible_mode_changes=args.visible_mode_change,
            source_publication_or_event=build_optional_fact(
                label="source publication or event timing",
                value=args.source_publication_or_event,
                unknown_reason=args.source_publication_or_event_unknown_reason,
            ),
            source_edit_or_version=build_optional_fact(
                label="source edit or version timing",
                value=args.source_edit_or_version,
                unknown_reason=args.source_edit_or_version_unknown_reason,
            ),
            cutoff_posture=cutoff_posture,
            capture_time=build_optional_fact(
                label="capture timing",
                value=args.capture_time,
            ),
            recapture_time=build_optional_fact(
                label="re-capture timing",
                value=args.recapture_time,
                not_applicable_reason=args.recapture_time_not_applicable_reason,
            ),
            access_posture=build_optional_fact(
                label="access posture",
                value=args.access_posture,
                unknown_reason=args.access_posture_unknown_reason,
                not_attempted_reason=args.access_posture_not_attempted_reason,
            ),
            archive_history_posture=build_optional_fact(
                label="archive/history posture",
                value=args.archive_history_posture,
                not_attempted_reason=args.archive_history_not_attempted_reason,
            ),
            media_modality_posture=build_optional_fact(
                label="media/modality posture",
                value=args.media_modality_posture,
                not_attempted_reason=args.media_modality_not_attempted_reason,
            ),
            re_capture_relationship=build_optional_fact(
                label="re-capture relationship",
                value=args.recapture_relationship,
                not_applicable_reason=args.recapture_relationship_not_applicable_reason,
            ),
            warnings=args.warning,
            limitations=args.limitation,
        )
    except Exception as exc:
        parser.exit(status=2, message=f"source capture packet failed: {exc}\n")

    print(output_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
