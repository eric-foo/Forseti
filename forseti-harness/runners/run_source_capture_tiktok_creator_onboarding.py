"""CLI: supervised one-creator TikTok onboarding in one browser context."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture_spine.creator_profile_current.registry_match_preflight import (
    RECEIPT_WRAPPER_KEY,
    build_creator_registry_match_preflight_receipt,
    dump_creator_registry_match_preflight_receipt,
)
from capture_spine.creator_profile_current.creator_onboarding_selection import (
    eligible_creator_onboarding_candidates,
)
from capture_spine.creator_profile_current.validation import (
    load_creator_profile_current_view,
)
from data_lake.canonical_json import canonical_record_bytes
from data_lake.creator_audience_queue import (
    CreatorAudienceQueueError,
    assert_creator_audience_capacity,
    enqueue_creator_audience_job,
    unfinished_profile_subject_ids,
)
from data_lake.creator_registry import load_current_registry_preflight_view
from data_lake.root import DataLakeRoot
from capture_spine.tiktok_creator_discovery_frontier.frontier_selector import (
    apply_tiktok_creator_onboarding_dedupe,
    build_tiktok_creator_promotion_decisions,
    promotion_decision_for_handle,
    rank_tiktok_creator_discovery_targets,
)
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    load_creator_frontier_dispositions,
    load_tiktok_creator_discovery_frontier_registers,
    write_creator_frontier_dispositions,
)
from capture_spine.tiktok_creator_discovery_frontier import (
    LinkHubOutcome,
    RefreshOutcome,
    ScanReceipt,
    SuggestedAccountObservation,
    build_tiktok_creator_discovery_frontier_register,
    write_tiktok_creator_discovery_frontier_register,
)
from source_capture.session_profiles import (
    default_session_profile_auth_state_root,
    resolve_session_profile,
)
from source_capture.adapters.browser_session_probe import probe_local_cdp_endpoints
from source_capture.tiktok.batch_coverage import (
    build_tiktok_batch_coverage_from_lake,
    build_tiktok_batch_coverage_from_packet_directory,
)
from source_capture.tiktok.batch_packet import TIKTOK_BATCH_CAPTURE_SURFACE
from source_capture.tiktok.batch_packet import write_tiktok_batch_packet
from source_capture.tiktok.creator_onboarding import (
    DEFAULT_MAX_GRID_SCROLL_PASSES,
    DEFAULT_SELECTION_COUNT,
    DEFAULT_WINDOW_SIZE,
    GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT,
    TikTokCreatorMarketDeferred,
    TikTokCreatorOnboardingError,
    assess_tiktok_creator_market,
    run_tiktok_creator_onboarding,
    run_tiktok_creator_profile_refresh,
)
from source_capture.tiktok.grid_packet import write_tiktok_grid_packet
from runners.run_tiktok_creator_onboarding_coordinator import prepare_onboarding
from tiktok_creator_metronome import (
    activate_metronome,
    active_metronome,
    deactivate_metronome,
    open_direct_run_metronome,
)
SUMMARY_PREFIX = "tiktok_creator_onboarding_summary_json="
PROGRESS_PREFIX = "tiktok_creator_onboarding_progress_json="
BLOCKER_PREFIX = "tiktok_creator_onboarding_blocker_json="
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREATOR_REGISTRY = (
    ROOT
    / "forseti/product/spines/capture/core/source_families/social_media"
    / "creator_registry/creator_profile_current_view_v0.json"
)
REGISTRY_PREFLIGHT_JSON_NAME = "creator_registry_match_preflight.json"
PROMOTION_DECISIONS_JSON_NAME = "tiktok_creator_promotion_decisions.json"
DEFAULT_DECISION_QUESTION = (
    "Admit the selected TikTok onboarding videos' public comments, "
    "subtitles, source text, and typed extraction seeds."
)
PROFILE_REFRESH_DECISION_QUESTION = (
    "Admit the current TikTok profile bio, exact profile metrics, and grid identifiers."
)
CDP_RECOVERY = "launch Desktop shortcut Forseti TikTok Capture and retry"
DEFAULT_AUDIENCE_QUESTION = (
    "What is this creator's ideal audience and commercial fit based only on "
    "the admitted evidence?"
)


class CdpSessionUnavailable(TikTokCreatorOnboardingError):
    """Raised when the dedicated local TikTok CDP endpoint is not reachable."""


class AudienceQueueCapacityReached(TikTokCreatorOnboardingError):
    """Raised before browser work when creator-audience WIP is at its cap."""


def _onboarding_window_size(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("window size must be an integer") from exc
    if parsed < GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT:
        raise argparse.ArgumentTypeError(
            "window size must be at least "
            f"{GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT}"
        )
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Assess a new TikTok creator from current profile/grid evidence, or fully "
            "capture a Registry-admitted creator through the retained Chrome CDP session."
        ),
        epilog=(
            "Cold-agent default session alias: chowdakr_sg_tiktok. "
            "A missing or invalid alias blocks; this runner never downgrades to logged-out mode."
        ),
    )
    parser.add_argument(
        "--creator-handle",
        help=(
            "TikTok handle. When omitted for new_onboarding, auto-select the sole "
            "actionable not_onboarded TikTok platform account in the Creator "
            "Registry. An explicit new_onboarding handle must already be a Registry "
            "not_onboarded account; new_capture instead requires an absent account "
            "and performs assessment only."
        ),
    )
    parser.add_argument(
        "--creator-intent",
        choices=("new_onboarding", "new_capture", "update_existing"),
        default="new_onboarding",
        help=(
            "New onboarding requires an exact Creator Registry match with "
            "onboarding_state=not_onboarded and no current deferred/rejected "
            "Frontier disposition; new capture blocks exact matches and captures only "
            "current profile/grid assessment evidence; update existing requires an "
            "exact match."
        ),
    )
    parser.add_argument(
        "--creator-registry", type=Path, default=DEFAULT_CREATOR_REGISTRY
    )
    parser.add_argument(
        "--promotion-grid-dir",
        type=Path,
        help=(
            "Discovery Frontier *.grid.json directory; writes promotion decisions. "
            "With an explicit --creator-handle and --data-root, also records that "
            "creator's eligible/deferred Frontier disposition."
        ),
    )
    parser.add_argument(
        "--promotion-only",
        action="store_true",
        help="write promotion decisions and exit before Registry/browser work",
    )
    parser.add_argument(
        "--session-profile",
        default="chowdakr_sg_tiktok",
        help="Machine-local retained Chrome CDP TikTok session alias.",
    )
    parser.add_argument("--session-profile-config", type=Path)
    parser.add_argument("--auth-state-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--window-size",
        type=_onboarding_window_size,
        default=DEFAULT_WINDOW_SIZE,
        help=(
            "Maximum frozen grid rows; must be at least the 27-video acquisition "
            "minimum."
        ),
    )
    parser.add_argument(
        "--max-grid-scroll-passes",
        type=int,
        default=DEFAULT_MAX_GRID_SCROLL_PASSES,
        help=(
            "Safety cap per selected-tile lookup during deep-capture grid pagination; "
            "initial acquisition uses zero wheels for an already-loaded 27-video "
            "window, otherwise stops after its first sufficient new DOM batch."
        ),
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument(
        "--cadence-min-gap-seconds",
        type=float,
        default=None,
        help=(
            "Optional legacy uniform-cadence minimum; requires "
            "--cadence-max-gap-seconds. Omit both for the onboarding long-tail profile."
        ),
    )
    parser.add_argument(
        "--cadence-max-gap-seconds",
        type=float,
        default=None,
        help=(
            "Optional legacy uniform-cadence maximum; requires "
            "--cadence-min-gap-seconds. Omit both for the onboarding long-tail profile."
        ),
    )
    parser.add_argument("--cadence-window-seconds", type=float)
    parser.add_argument("--random-seed", type=int)
    admission = parser.add_mutually_exclusive_group()
    admission.add_argument("--admit-output", type=Path)
    admission.add_argument("--data-root")
    parser.add_argument("--batch-label", default="tiktok_creator_onboarding")
    parser.add_argument(
        "--prior-capture-pointer",
        help=(
            "Prior TikTok batch packet to reuse. By default this validates its "
            "transcript/comment coverage and captures only current profile evidence."
        ),
    )
    parser.add_argument(
        "--force-deep-recapture",
        action="store_true",
        help=(
            "With --prior-capture-pointer, deliberately repeat the full eight-video "
            "deep capture instead of the reuse-first profile refresh."
        ),
    )
    parser.add_argument(
        "--decision-question",
        default=DEFAULT_DECISION_QUESTION,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    journal = open_direct_run_metronome(
        args.output_dir,
        creator_handle=args.creator_handle,
    )
    if journal is None:
        return _run_main(parser, args)

    token = activate_metronome(journal)
    journal.record(
        "run_started",
        details={
            "run_kind": "direct_creator_runner",
            "creator_intent": args.creator_intent,
            "creator_handles": (
                [args.creator_handle.strip().lstrip("@").lower()]
                if args.creator_handle
                else []
            ),
        },
    )
    try:
        exit_code = _run_main(parser, args)
    except SystemExit as exc:
        raw_code = exc.code
        exit_code = raw_code if isinstance(raw_code, int) else 1
        journal.close_for_exit_code(exit_code)
        raise
    except BaseException:
        journal.close(
            status="failed",
            terminal_reason="unhandled_exception",
            counters={"exit_code": 3},
        )
        raise
    else:
        journal.close_for_exit_code(exit_code)
        return exit_code
    finally:
        deactivate_metronome(token)


def _run_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if (args.cadence_min_gap_seconds is None) != (
        args.cadence_max_gap_seconds is None
    ):
        parser.error(
            "--cadence-min-gap-seconds and --cadence-max-gap-seconds "
            "must be supplied together"
        )
    if (
        args.cadence_window_seconds is not None
        and args.cadence_min_gap_seconds is None
    ):
        parser.error(
            "--cadence-window-seconds requires explicit cadence min and max gaps"
        )
    data_root = None
    capture_scope = (
        "candidate_assessment"
        if args.creator_intent == "new_capture"
        else "full_deep_capture"
    )
    prior_coverage: dict[str, object] | None = None
    promotion_decisions = None
    frontier_registers: list[dict[str, object]] = []
    frontier_dispositions: dict[str, object] | None = None
    frontier_queue: dict[str, object] | None = None
    pending_audience_subject_ids: set[str] = set()
    audience_queue_result: dict[str, object] | None = None
    try:
        if args.promotion_only and args.promotion_grid_dir is None:
            raise ValueError("--promotion-only requires --promotion-grid-dir")
        if args.data_root is not None:
            data_root = DataLakeRoot.resolve(explicit=args.data_root)
            registry_document = load_current_registry_preflight_view(data_root)
            frontier_registers = load_tiktok_creator_discovery_frontier_registers(data_root)
            frontier_dispositions = load_creator_frontier_dispositions(data_root)
            pending_audience_subject_ids = unfinished_profile_subject_ids(data_root)
            registry_source_pointer = (
                "indexes/derived_retrieval/creator_registry/CURRENT"
            )
            registry_sha256 = hashlib.sha256(
                canonical_record_bytes(registry_document)
            ).hexdigest()
        else:
            registry_document = load_creator_profile_current_view(args.creator_registry)
            registry_source_pointer = str(args.creator_registry)
            registry_sha256 = hashlib.sha256(args.creator_registry.read_bytes()).hexdigest()
        if args.promotion_grid_dir is not None:
            promotion_path, promotion_decisions = _write_promotion_decisions(
                args.promotion_grid_dir,
                args.output_dir,
                registry_document=registry_document,
                frontier_registers=frontier_registers,
                frontier_dispositions=frontier_dispositions,
                data_root=data_root,
                explicit_creator_handle=args.creator_handle,
            )
            _emit_progress("promotion_decisions_complete", {"path": str(promotion_path), "counts": promotion_decisions["tiktok_creator_promotion_decisions"]["counts"]})
        if args.promotion_only:
            return 0
        args.creator_handle, selected_candidate = _resolve_creator_handle(
            creator_handle=args.creator_handle,
            creator_intent=args.creator_intent,
            registry_document=registry_document,
            frontier_dispositions=frontier_dispositions,
            pending_profile_subject_ids=pending_audience_subject_ids,
        )
        if selected_candidate is not None:
            _emit_progress("creator_selected_from_registry", selected_candidate)
        _emit_progress(
            "preflight_started",
            {
                "creator_handle": args.creator_handle.strip().lstrip("@").lower(),
                "session_profile": args.session_profile,
            },
        )
        preflight_path, preflight_result = _write_creator_registry_preflight(
            creator_handle=args.creator_handle,
            creator_intent=args.creator_intent,
            registry_document=registry_document,
            registry_source_pointer=registry_source_pointer,
            registry_sha256=registry_sha256,
            output_dir=args.output_dir,
        )
        if args.creator_intent == "new_onboarding":
            decision = preflight_result.get("decision")
            if decision != "existing_match":
                raise TikTokCreatorOnboardingError(
                    "new_onboarding requires one exact Registry not_onboarded account; "
                    f"genuinely absent accounts must be candidate-admitted first; found decision={decision!r}"
                )
            onboarding_state = preflight_result.get("registry_onboarding_state")
            if onboarding_state != "not_onboarded":
                raise TikTokCreatorOnboardingError(
                    "new_onboarding requires onboarding_state=not_onboarded; "
                    f"found onboarding_state={onboarding_state!r}"
                )
            if pending_audience_subject_ids:
                matched = preflight_result.get("matched_registry_profiles")
                if not isinstance(matched, list) or len(matched) != 1:
                    raise TikTokCreatorOnboardingError(
                        "new_onboarding requires one exact Registry profile match"
                    )
                matched_subject = (
                    matched[0].get("profile_subject_id")
                    if isinstance(matched[0], dict)
                    else None
                )
                if matched_subject in pending_audience_subject_ids:
                    raise TikTokCreatorOnboardingError(
                        "creator already has a queued or running audience onboarding job"
                    )
            disposition = _frontier_disposition_for_handle(
                frontier_dispositions, args.creator_handle
            )
            if disposition is not None and disposition.get("status") in {"deferred", "rejected"}:
                raise TikTokCreatorOnboardingError(
                    "current Frontier disposition blocks onboarding: "
                    f"status={disposition.get('status')!r}"
                )
        if preflight_result["action_status"] != "allowed":
            raise TikTokCreatorOnboardingError(
                f"Creator Registry preflight blocked: {preflight_result['action_blockers']}"
            )
        if args.force_deep_recapture and not args.prior_capture_pointer:
            raise ValueError(
                "--force-deep-recapture requires --prior-capture-pointer"
            )
        if args.creator_intent == "new_capture" and args.force_deep_recapture:
            raise ValueError(
                "new_capture is assessment-only and does not permit deep recapture"
            )
        if args.prior_capture_pointer and not args.force_deep_recapture:
            prior_coverage = _validate_reusable_prior_capture(
                prior_capture_pointer=args.prior_capture_pointer,
                creator_handle=args.creator_handle,
                data_root=data_root,
            )
            capture_scope = "profile_refresh"
            _emit_progress(
                "prior_capture_reuse_validated",
                {
                    "prior_capture_pointer": args.prior_capture_pointer,
                    "captured_comment_count": prior_coverage[
                        "nonblank_top_level_comment_count"
                    ],
                    "subtitle_cue_count": prior_coverage[
                        "nonblank_transcript_cue_count"
                    ],
                },
            )
        if data_root is not None and args.creator_intent == "new_onboarding":
            try:
                queue_counts = assert_creator_audience_capacity(data_root)
            except CreatorAudienceQueueError as exc:
                if str(exc).startswith("AUDIENCE_QUEUE_CAPACITY_REACHED:"):
                    raise AudienceQueueCapacityReached(str(exc)) from exc
                raise
            _emit_progress("audience_queue_capacity_available", queue_counts)
        auth_state_root = args.auth_state_root or default_session_profile_auth_state_root()
        _emit_progress("registry_preflight_complete", {"status": "allowed"})
        session_profile = resolve_session_profile(
            args.session_profile,
            config_path=args.session_profile_config,
        )
        _emit_progress(
            "session_profile_resolved",
            {"session_profile": args.session_profile},
        )
        cdp_report = probe_local_cdp_endpoints(
            (9222,),
            timeout_seconds=min(args.timeout_seconds, 2.0),
        )
        if cdp_report["browser_available"] is not True:
            raise CdpSessionUnavailable(CDP_RECOVERY)
        _emit_progress(
            "cdp_session_available",
            {"endpoint": "http://127.0.0.1:9222"},
        )
        if capture_scope in {"candidate_assessment", "profile_refresh"}:
            paths = run_tiktok_creator_profile_refresh(
                creator_handle=args.creator_handle,
                session_profile=session_profile,
                output_dir=args.output_dir,
                auth_state_root=auth_state_root,
                window_size=args.window_size,
                timeout_seconds=args.timeout_seconds,
                settle_seconds=args.settle_seconds,
                max_grid_scroll_passes=args.max_grid_scroll_passes,
                progress_fn=_emit_progress,
            )
        else:
            paths = run_tiktok_creator_onboarding(
                creator_handle=args.creator_handle,
                session_profile=session_profile,
                output_dir=args.output_dir,
                auth_state_root=auth_state_root,
                window_size=args.window_size,
                selection_count=DEFAULT_SELECTION_COUNT,
                timeout_seconds=args.timeout_seconds,
                settle_seconds=args.settle_seconds,
                max_grid_scroll_passes=args.max_grid_scroll_passes,
                cadence_min_gap_seconds=args.cadence_min_gap_seconds,
                cadence_max_gap_seconds=args.cadence_max_gap_seconds,
                cadence_window_seconds=args.cadence_window_seconds,
                random_seed=args.random_seed,
                progress_fn=_emit_progress,
                enforce_us_market_gate=(
                    args.creator_intent in {"new_capture", "new_onboarding"}
                ),
            )
        if capture_scope == "candidate_assessment":
            grid = json.loads(paths.grid_window_json_path.read_text(encoding="utf-8"))
            assessment = assess_tiktok_creator_market(
                creator_handle=args.creator_handle,
                profile_bio_text_or_none=grid.get("profile_bio_text_or_none"),
                profile_bio_status=str(grid.get("profile_bio_status") or ""),
                source_artifact=paths.grid_window_json_path.name,
            )
            _emit_progress(
                "market_gate",
                {
                    "decision": assessment["decision"],
                    "reason_code_or_none": assessment["reason_code_or_none"],
                },
            )
            if assessment["decision"] != "passed_no_non_us_evidence":
                raise TikTokCreatorMarketDeferred(assessment)
    except TikTokCreatorMarketDeferred as exc:
        assessment = exc.assessment
        if data_root is not None:
            try:
                result = write_creator_frontier_dispositions(
                    data_root=data_root,
                    actions=[
                        _market_defer_action(
                            creator_handle=args.creator_handle,
                            assessment=assessment,
                        )
                    ],
                )
            except Exception as write_exc:
                _emit_blocker("MARKET_DEFER_WRITE_FAILED", "market_gate")
                parser.exit(
                    status=3,
                    message=(
                        "source capture tiktok market defer write failed: "
                        f"{type(write_exc).__name__}: {write_exc}\n"
                    ),
                )
                return 3
            _emit_progress(
                "market_defer_recorded",
                {
                    "creator_handle": args.creator_handle.strip().lstrip("@").lower(),
                    "reason_code": assessment["reason_code_or_none"],
                    "write_status": result["status"],
                    "raw_anchor_or_none": result.get("raw_anchor"),
                    "record_id_or_none": result.get("record_id"),
                },
            )
        _emit_blocker(
            "CANDIDATE_MARKET_DEFERRED",
            "market_gate",
            recovery="reconsider after the explicit non-US profile signal changes",
        )
        parser.exit(status=2, message=f"{exc}\n")
        return 2
    except (OSError, ValueError, TikTokCreatorOnboardingError) as exc:
        if isinstance(exc, CdpSessionUnavailable):
            _emit_blocker(
                "CDP_SESSION_UNAVAILABLE",
                "browser_preflight",
                recovery=CDP_RECOVERY,
            )
        elif isinstance(exc, AudienceQueueCapacityReached):
            _emit_blocker(
                "AUDIENCE_QUEUE_CAPACITY_REACHED",
                "browser_preflight",
                recovery="finish or explicitly block an audience queue job, then retry",
            )
        elif str(exc) == "logged_out_session":
            _emit_blocker("LOGGED_OUT_SESSION", "authenticated_browser_session")
        elif str(exc) == "account_safety_stop":
            _emit_blocker("ACCOUNT_SAFETY_STOP", "deep_capture")
        else:
            _emit_blocker(
                "ONBOARDING_PRECHECK_OR_CAPTURE_FAILED", "onboarding"
            )
        parser.exit(
            status=2,
            message=f"source capture tiktok creator onboarding failed: {exc}\n",
        )
        return 2
    except Exception as exc:
        _emit_blocker("ONBOARDING_UNEXPECTED_FAILURE", "onboarding")
        parser.exit(
            status=3,
            message=f"source capture tiktok creator onboarding failed: {type(exc).__name__}: {exc}\n",
        )
        return 3

    admitted_path: str | None = None
    frontier_path: str | None = None
    registry_projection_refresh: dict[str, object] | None = None
    if args.admit_output is not None or args.data_root is not None:
        _emit_progress("admission_started", {})
        try:
            if capture_scope in {"candidate_assessment", "profile_refresh"}:
                exit_code, output = write_tiktok_grid_packet(
                    grid_window_json=paths.grid_window_json_path.read_bytes(),
                    output_directory=args.admit_output if data_root is None else None,
                    data_root=data_root,
                    session_identity=args.session_profile,
                    prior_capture_pointer=args.prior_capture_pointer,
                    decision_question=(
                        PROFILE_REFRESH_DECISION_QUESTION
                        if args.decision_question == DEFAULT_DECISION_QUESTION
                        else args.decision_question
                    ),
                )
            else:
                exit_code, output = write_tiktok_batch_packet(
                    creator_handle=args.creator_handle,
                    creator_profile_url=(
                        f"https://www.tiktok.com/@{args.creator_handle.strip().lstrip('@')}"
                    ),
                    grid_result_json=paths.live_grid_json_path.read_bytes(),
                    cadence_result_jsons=[paths.live_cadence_json_path.read_bytes()],
                    grid_window_json=paths.grid_window_json_path.read_bytes(),
                    selection_result_json=paths.selection_json_path.read_bytes(),
                    suggested_accounts_json=paths.suggested_accounts_json_path.read_bytes(),
                    activity_journal_jsonl=paths.activity_journal_jsonl_path.read_bytes(),
                    output_directory=args.admit_output if data_root is None else None,
                    data_root=data_root,
                    decision_question=args.decision_question,
                    batch_label=args.batch_label,
                    source_file_receipts=[
                        _source_receipt(paths.live_grid_json_path, "grid_result_json"),
                        _source_receipt(
                            paths.live_cadence_json_path, "cadence_result_json_1"
                        ),
                        _source_receipt(
                            paths.grid_window_json_path, "grid_window_json"
                        ),
                        _source_receipt(
                            paths.selection_json_path, "selection_result_json"
                        ),
                        _source_receipt(
                            paths.suggested_accounts_json_path,
                            "suggested_accounts_json",
                        ),
                        _source_receipt(
                            paths.activity_journal_jsonl_path,
                            "source_capture_activity_jsonl",
                        ),
                    ],
                    prior_capture_pointer=args.prior_capture_pointer,
                )
        except Exception as exc:
            _emit_blocker("ADMISSION_FAILED", "admission")
            parser.exit(
                status=3,
                message=(
                    "source capture tiktok creator onboarding admission failed: "
                    f"{type(exc).__name__}: {exc}\n"
                ),
            )
            return 3
        if exit_code != 0:
            _emit_blocker("ADMISSION_FAILED", "admission")
            parser.exit(
                status=exit_code,
                message=f"source capture tiktok creator onboarding admission failed: {output}\n",
            )
        admitted_path = str(output)
        if data_root is not None:
            _emit_progress(
                "registry_admission_deferred_until_validated_judgment",
                {"admitted_path": admitted_path},
            )
        if data_root is not None and capture_scope == "full_deep_capture":
            try:
                frontier_path = _write_suggested_frontier(
                    creator_handle=args.creator_handle,
                    session_profile=args.session_profile,
                    suggested_receipt_path=paths.suggested_accounts_json_path,
                    admitted_path=Path(admitted_path),
                    data_root=data_root,
                )
                frontier_queue = _build_frontier_queue(
                    data_root=data_root,
                    registry_document=registry_document,
                    frontier_dispositions=frontier_dispositions,
                )
            except Exception as exc:
                _emit_blocker("SUGGESTED_FRONTIER_WRITE_FAILED", "admission")
                parser.exit(
                    status=3,
                    message=(
                        "source capture tiktok suggested frontier write failed: "
                        f"{type(exc).__name__}: {exc}\n"
                    ),
                )
                return 3

        if data_root is not None and args.creator_intent == "new_onboarding":
            try:
                grid_packet_id = Path(str(admitted_path)).name
                content_packet_id = (
                    str(prior_coverage["packet_id"])
                    if capture_scope == "profile_refresh" and prior_coverage is not None
                    else grid_packet_id
                )
                prepared = prepare_onboarding(
                    data_root=data_root,
                    packet_id=content_packet_id,
                    grid_packet_id=(
                        grid_packet_id if grid_packet_id != content_packet_id else None
                    ),
                    creator_id=None,
                    profile_subject_id=None,
                    question=DEFAULT_AUDIENCE_QUESTION,
                    evidence_cutoff=_packet_capture_time(data_root, grid_packet_id),
                    work_dir=(
                        args.output_dir
                        / "creator_audience_queue"
                        / content_packet_id
                    ),
                )
                audience_queue_result = enqueue_creator_audience_job(
                    data_root=data_root,
                    bundle_path=Path(str(prepared["bundle_out"])),
                    prompt_path=Path(str(prepared["prompt_out"])),
                )
                _emit_progress("audience_job_enqueued", audience_queue_result)
            except Exception as exc:
                _emit_blocker(
                    "AUDIENCE_QUEUE_ENQUEUE_FAILED",
                    "post_capture_audience_handoff",
                    recovery=(
                        "reuse the admitted packet with the TikTok onboarding "
                        "coordinator prepare --enqueue command; do not recapture"
                    ),
                )
                parser.exit(
                    status=3,
                    message=(
                        "source capture tiktok audience queue enqueue failed; "
                        "capture remains reusable: "
                        f"{type(exc).__name__}: {exc}\n"
                    ),
                )
                return 3

    receipt = json.loads(paths.onboarding_receipt_json_path.read_text(encoding="utf-8"))
    browser_lifecycle = receipt.get("browser_lifecycle")
    if not isinstance(browser_lifecycle, dict):
        browser_lifecycle = {}
    _emit_summary(
        {
            "status": receipt["status"],
            "capture_scope": capture_scope,
            "creator_handle": receipt["creator_handle"],
            "session_profile": receipt["session_profile"],
            "window_size": receipt["window_size"],
            "selection_count": receipt["selection_count"],
            "window_cap": receipt["window_cap"],
            "creator_intent": args.creator_intent,
            "registry_preflight_path": str(preflight_path),
            "selected_count": receipt["selected_count"],
            "completed_deep_capture_count": receipt[
                "completed_deep_capture_count"
            ],
            "suggested_accounts_status": receipt.get(
                "suggested_accounts_status_or_none"
            ),
            "suggested_outer_ui_route": receipt.get(
                "suggested_outer_ui_route_or_none"
            ),
            "page_acquisition_policy": browser_lifecycle.get(
                "page_acquisition_policy"
            ),
            "initial_platform_match_count": browser_lifecycle.get(
                "initial_platform_match_count"
            ),
            "initial_exact_match_count": browser_lifecycle.get(
                "initial_exact_match_count"
            ),
            "page_adoption_count": browser_lifecycle.get(
                "page_adoption_count"
            ),
            "page_creation_count": browser_lifecycle.get(
                "page_creation_count"
            ),
            "page_navigation_count": browser_lifecycle.get(
                "page_navigation_count"
            ),
            "same_url_navigation_suppression_count": browser_lifecycle.get(
                "same_url_navigation_suppression_count"
            ),
            "humanized_input_preset": browser_lifecycle.get(
                "humanized_input_preset"
            ),
            "initial_deep_capture_wait": receipt.get(
                "initial_deep_capture_wait_or_none"
            ),
            "grid_deep_entry": receipt.get("grid_deep_entry_or_none"),
            "output_dir": str(args.output_dir),
            "admitted_path_or_none": admitted_path,
            "prior_capture_pointer_or_none": args.prior_capture_pointer,
            "profile_refresh_packet_or_none": (
                admitted_path if capture_scope == "profile_refresh" else None
            ),
            "suggested_frontier_path_or_none": frontier_path,
            "suggested_frontier_queue_or_none": frontier_queue,
            "audience_queue_job_or_none": audience_queue_result,
            "registry_projection_refresh_or_none": registry_projection_refresh,
        }
    )
    return 0


def _resolve_creator_handle(
    *,
    creator_handle: str | None,
    creator_intent: str,
    registry_document: dict[str, object] | None = None,
    registry_path: Path | None = None,
    frontier_dispositions: dict[str, object] | None = None,
    pending_profile_subject_ids: set[str] | None = None,
) -> tuple[str, dict[str, str] | None]:
    if creator_handle is not None and creator_handle.strip():
        return creator_handle, None
    if creator_intent != "new_onboarding":
        raise ValueError(
            "--creator-handle is required unless --creator-intent=new_onboarding"
        )
    if registry_document is None:
        if registry_path is None:
            raise ValueError("registry_document or registry_path is required")
        registry_document = load_creator_profile_current_view(registry_path)
    candidates = eligible_creator_onboarding_candidates(registry_document, platform="tiktok")
    pending = pending_profile_subject_ids or set()
    candidates = [
        candidate
        for candidate in candidates
        if (
            (_frontier_disposition_for_handle(frontier_dispositions, candidate["public_handle"]) or {}).get("status")
            not in {"deferred", "rejected"}
        )
        and candidate["platform_account_id"] not in pending
    ]
    if not candidates:
        raise ValueError("Creator Registry has no actionable not_onboarded tiktok account")
    if len(candidates) != 1:
        raise ValueError(
            "Creator Registry has multiple actionable not_onboarded tiktok accounts; "
            f"provide --creator-handle from {[row['platform_account_id'] for row in candidates]}"
        )
    candidate = {**candidates[0], "selection_policy": "sole_actionable_registry_not_onboarded_account"}
    return candidate["public_handle"], candidate



def _write_promotion_decisions(
    grid_dir: Path,
    output_dir: Path,
    *,
    registry_document: dict[str, object],
    frontier_registers: Sequence[dict[str, object]] = (),
    frontier_dispositions: dict[str, object] | None = None,
    data_root: DataLakeRoot | None = None,
    explicit_creator_handle: str | None = None,
) -> tuple[Path, dict[str, object]]:
    paths = sorted(grid_dir.glob("*.grid.json"), key=lambda path: path.name.lower())
    if not paths:
        raise ValueError(f"no *.grid.json files in {grid_dir}")
    grids, sources = [], []
    for path in paths:
        raw = path.read_bytes()
        grid = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(grid, dict):
            raise ValueError(f"grid must be an object: {path}")
        grids.append(grid)
        sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
    document = apply_tiktok_creator_onboarding_dedupe(
        build_tiktok_creator_promotion_decisions(grids, sources=sources),
        registry_states=_registry_tiktok_states(registry_document),
        frontier_registers=frontier_registers,
        frontier_dispositions=frontier_dispositions,
    )
    if data_root is not None and explicit_creator_handle is not None:
        _write_promotion_frontier_disposition(
            data_root=data_root,
            document=document,
            creator_handle=explicit_creator_handle,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / PROMOTION_DECISIONS_JSON_NAME
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return output, document


def _write_promotion_frontier_disposition(
    *,
    data_root: DataLakeRoot,
    document: dict[str, object],
    creator_handle: str,
) -> dict[str, object]:
    decision = promotion_decision_for_handle(document, creator_handle)
    if decision is None:
        raise ValueError(
            f"promotion grids do not contain explicit creator handle: {creator_handle}"
        )
    frontier_dispositions = load_creator_frontier_dispositions(data_root)
    current = _frontier_disposition_for_handle(frontier_dispositions, creator_handle)
    compatibility_disposition = decision.get("owner_onboarding_disposition_or_none")
    if current is None and compatibility_disposition is not None:
        raise ValueError(
            "refusing to record a promotion disposition over the non-performance "
            f"compatibility owner disposition for {creator_handle}: "
            f"{compatibility_disposition}"
        )
    action = _promotion_frontier_action(decision)
    if current is not None and not _promotion_action_matches_current(
        action=action, current=current
    ):
        current_note = str(current.get("note_or_none") or "")
        performance_owned = (
            current.get("status") in {"eligible", "deferred"}
            and (
                current.get("reason_code") in {"low_potential", "low_reach"}
                or current_note.startswith("policy=tiktok_fragrance_creator_promotion_policy_")
            )
        )
        if not performance_owned:
            raise ValueError(
                "refusing to supersede non-performance Creator Frontier disposition "
                f"for {creator_handle}: status={current.get('status')}, "
                f"reason_code={current.get('reason_code')}"
            )
    return write_creator_frontier_dispositions(data_root=data_root, actions=[action])


def _promotion_frontier_action(
    decision: Mapping[str, object],
) -> dict[str, object]:
    handle = str(decision.get("handle") or "").strip().lstrip("@")
    note = str(decision.get("decision_note") or "").strip()
    reason = decision.get("decision_reason_code")
    if not handle or not note or not isinstance(reason, str):
        raise ValueError("promotion decision lacks handle, reason, or note")
    if decision.get("registry_action") == "promote_now":
        return {
            "platform": "tiktok",
            "handle": handle,
            "status": "eligible",
            "priority": "normal",
            "reason_code": "other",
            "note": note,
        }
    if decision.get("registry_action") != "do_not_promote":
        raise ValueError("promotion decision has invalid registry_action")
    return {
        "platform": "tiktok",
        "handle": handle,
        "status": "deferred",
        "reason_code": (
            "other"
            if reason == "quality_unavailable_weekly_below_p25"
            else "low_potential"
        ),
        "note": note,
        "reconsideration": "new_signal",
    }


def _promotion_action_matches_current(
    *, action: dict[str, object], current: dict[str, object]
) -> bool:
    return (
        current.get("status") == action.get("status")
        and current.get("priority_or_none") == action.get("priority")
        and current.get("reason_code") == action.get("reason_code")
        and current.get("note_or_none") == action.get("note")
        and current.get("reconsideration_or_none") == action.get("reconsideration")
    )


def _registry_tiktok_states(registry: dict[str, object]) -> dict[str, str]:
    wrapper = registry.get("creator_profile_current_view")
    if not isinstance(wrapper, dict) or not isinstance(wrapper.get("profiles"), list):
        raise ValueError("Creator Registry current view requires profiles")
    states = {}
    for profile in wrapper["profiles"]:
        if not isinstance(profile, dict):
            continue
        onboarding = profile.get("onboarding")
        state = onboarding.get("onboarding_state") if isinstance(onboarding, dict) else None
        if state not in {"onboarded", "not_onboarded"}:
            raise ValueError("Creator Registry profile has invalid onboarding state")
        for account in profile.get("platform_accounts", []):
            if isinstance(account, dict) and str(account.get("platform", "")).lower() == "tiktok":
                handle = str(account.get("normalized_public_handle") or account.get("public_handle") or "").strip().lstrip("@").lower()
                if handle in states:
                    raise ValueError(f"duplicate TikTok registry handle: {handle}")
                states[handle] = state
    return states


def _emit_progress(event: str, fields: dict[str, object]) -> None:
    journal = active_metronome()
    if journal is not None:
        journal.record_progress(event, fields)
    print(
        PROGRESS_PREFIX
        + json.dumps({"event": event, **fields}, sort_keys=True),
        flush=True,
    )


def _emit_blocker(code: str, phase: str, *, recovery: str | None = None) -> None:
    journal = active_metronome()
    if journal is not None:
        journal.record_blocker(code, phase)
    payload = {"code": code, "phase": phase}
    if recovery is not None:
        payload["recovery"] = recovery
    print(
        BLOCKER_PREFIX
        + json.dumps(payload, sort_keys=True),
        flush=True,
    )


def _emit_summary(payload: dict[str, object]) -> None:
    journal = active_metronome()
    if journal is not None:
        journal.record(
            "runner_summary",
            details={
                "status": str(payload.get("status") or ""),
                "capture_scope": str(payload.get("capture_scope") or ""),
                "creator_intent": str(payload.get("creator_intent") or ""),
                "completed_deep_capture_count": int(
                    payload.get("completed_deep_capture_count") or 0
                ),
            },
        )
    print(
        SUMMARY_PREFIX + json.dumps(payload, sort_keys=True),
        flush=True,
    )


def _market_defer_action(
    *, creator_handle: str, assessment: dict[str, object]
) -> dict[str, object]:
    reason_code = assessment.get("reason_code_or_none")
    reconsideration = assessment.get("reconsideration_or_none")
    evidence = assessment.get("evidence")
    country_flag_codes = (
        evidence.get("country_flag_codes") if isinstance(evidence, dict) else None
    )
    if (
        reason_code != "non_us_market"
        or reconsideration != "new_signal"
        or not isinstance(evidence, dict)
        or not isinstance(country_flag_codes, list)
        or any(not isinstance(value, str) for value in country_flag_codes)
    ):
        raise ValueError("market defer assessment is not a canonical deferred decision")
    note = (
        "standing owner US-market gate applied to same-read TikTok profile bio; "
        f"bio_status={evidence.get('profile_bio_status')}; "
        f"non_us_country_flags={','.join(code for code in country_flag_codes if code != 'US') or 'none'}"
    )
    return {
        "platform": "tiktok",
        "handle": creator_handle,
        "status": "deferred",
        "reason_code": reason_code,
        "note": note,
        "reconsideration": reconsideration,
    }


def _validate_reusable_prior_capture(
    *,
    prior_capture_pointer: str,
    creator_handle: str,
    data_root: object | None,
) -> dict[str, object]:
    normalized_handle = creator_handle.strip().lstrip("@").lower()
    if data_root is not None:
        if prior_capture_pointer in data_root.tombstoned_packet_ids():
            raise ValueError(
                f"prior capture packet is tombstoned: {prior_capture_pointer}"
            )
        coverage = build_tiktok_batch_coverage_from_lake(
            data_root, prior_capture_pointer
        )
    else:
        coverage = build_tiktok_batch_coverage_from_packet_directory(
            Path(prior_capture_pointer)
        )
    if coverage.get("source_surface") != TIKTOK_BATCH_CAPTURE_SURFACE:
        raise ValueError("prior capture is not a TikTok creator batch packet")
    if str(coverage.get("creator_handle") or "").strip().lstrip("@").lower() != normalized_handle:
        raise ValueError("prior capture creator_handle does not match requested creator")
    rollup = coverage.get("coverage_rollup")
    if not isinstance(rollup, dict):
        raise ValueError("prior capture has no audience evidence coverage rollup")
    captured_comment_count = rollup.get("nonblank_top_level_comment_count")
    subtitle_cue_count = rollup.get("nonblank_transcript_cue_count")
    if (
        not isinstance(captured_comment_count, int)
        or captured_comment_count <= 0
        or not isinstance(subtitle_cue_count, int)
        or subtitle_cue_count <= 0
    ):
        raise ValueError(
            "prior capture is not reusable: at least one captured comment and "
            "one transcript/subtitle cue are required"
        )
    return {
        "packet_id": coverage.get("packet_id"),
        "nonblank_top_level_comment_count": captured_comment_count,
        "nonblank_transcript_cue_count": subtitle_cue_count,
    }


def _packet_capture_time(data_root: DataLakeRoot, packet_id: str) -> str:
    manifest = data_root.load_raw_packet(packet_id).manifest
    timing = manifest.get("timing")
    capture_time = timing.get("capture_time") if isinstance(timing, dict) else None
    value = capture_time.get("value") if isinstance(capture_time, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"packet has no exact capture timestamp: {packet_id}")
    return value.strip()


def _write_creator_registry_preflight(
    *,
    creator_handle: str,
    creator_intent: str,
    registry_document: dict[str, object] | None = None,
    registry_source_pointer: str | None = None,
    registry_sha256: str | None = None,
    registry_path: Path | None = None,
    output_dir: Path,
) -> tuple[Path, dict[str, object]]:
    normalized_handle = creator_handle.strip().lstrip("@").lower()
    if registry_document is None:
        if registry_path is None:
            raise ValueError("registry_document or registry_path is required")
        registry_document = load_creator_profile_current_view(registry_path)
        registry_source_pointer = str(registry_path)
        registry_sha256 = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    if registry_source_pointer is None or registry_sha256 is None:
        raise ValueError("registry source pointer and sha256 are required")
    registry_intent = (
        "classify" if creator_intent == "new_onboarding" else creator_intent
    )
    receipt = build_creator_registry_match_preflight_receipt(
        candidates=[
            {
                "candidate_id": f"tiktok-{normalized_handle}",
                "platform": "tiktok",
                "public_handle_or_none": normalized_handle,
                "public_profile_url_or_none": (
                    f"https://www.tiktok.com/@{normalized_handle}"
                ),
                "intended_action": registry_intent,
            }
        ],
        registry_document=registry_document,
        registry_source_pointer=registry_source_pointer,
        registry_sha256=registry_sha256,
        generated_at_utc=(
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / REGISTRY_PREFLIGHT_JSON_NAME
    receipt_path.write_text(
        dump_creator_registry_match_preflight_receipt(receipt),
        encoding="utf-8",
        newline="\n",
    )
    result = receipt[RECEIPT_WRAPPER_KEY]["results"][0]
    if not isinstance(result, dict):
        raise ValueError("Creator Registry preflight result must be an object")
    result["registry_onboarding_state"] = _matched_registry_onboarding_state(
        registry_document=registry_document,
        preflight_result=result,
    )
    return receipt_path, result


def _matched_registry_onboarding_state(
    *,
    registry_document: dict[str, object],
    preflight_result: dict[str, object],
) -> str | None:
    if preflight_result.get("decision") != "existing_match":
        return None
    matches = preflight_result.get("matched_registry_profiles")
    if not isinstance(matches, list) or len(matches) != 1:
        raise ValueError(
            "exact Creator Registry match must identify exactly one registry profile"
        )
    match = matches[0]
    if not isinstance(match, dict):
        raise ValueError("matched Creator Registry profile must be an object")
    profile_subject_id = match.get("profile_subject_id")
    wrapper = registry_document.get("creator_profile_current_view")
    if not isinstance(wrapper, dict):
        raise ValueError("Creator Registry current-view wrapper must be an object")
    profiles = wrapper.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Creator Registry profiles must be a list")
    matched_profiles = [
        profile
        for profile in profiles
        if isinstance(profile, dict)
        and profile.get("profile_subject_id") == profile_subject_id
    ]
    if len(matched_profiles) != 1:
        raise ValueError(
            "exact Creator Registry match must resolve to exactly one current profile"
        )
    onboarding = matched_profiles[0].get("onboarding")
    if not isinstance(onboarding, dict):
        raise ValueError("matched Creator Registry profile has no onboarding object")
    onboarding_state = onboarding.get("onboarding_state")
    if onboarding_state not in {"not_onboarded", "onboarded"}:
        raise ValueError(
            "matched Creator Registry profile has invalid onboarding_state"
        )
    return onboarding_state


def _source_receipt(path: Path, role: str) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "role": role,
        "file_name": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def _write_suggested_frontier(
    *,
    creator_handle: str,
    session_profile: str,
    suggested_receipt_path: Path,
    admitted_path: Path,
    data_root: object,
) -> str | None:
    suggested_receipt = json.loads(
        suggested_receipt_path.read_text(encoding="utf-8")
    )
    rows = suggested_receipt.get("suggested_accounts")
    if suggested_receipt.get("status") != "captured" or not isinstance(rows, list) or not rows:
        return None

    handle = creator_handle.strip().lstrip("@").lower()
    packet_id = admitted_path.name
    capture_timestamp = (
        suggested_receipt.get("attempt_receipt", {}).get("capture_timestamp")
    )
    if not isinstance(capture_timestamp, str) or not capture_timestamp:
        raise ValueError("captured suggested accounts require capture_timestamp")
    external_links = suggested_receipt.get("profile_external_links")
    link_hub_url = None
    if isinstance(external_links, list):
        for row in external_links:
            if isinstance(row, dict) and isinstance(row.get("url"), str):
                link_hub_url = row["url"]
                break

    run_id = f"tiktok_creator_onboarding_{packet_id.lower()}"
    register_id = f"tiktok_creator_discovery_frontier_{handle}_{packet_id.lower()}"
    scan_receipt = ScanReceipt(
        receipt_id=f"receipt_{run_id}",
        run_id=run_id,
        register_id=register_id,
        root_seed={
            "platform": "tiktok",
            "handle": handle,
            "url": f"https://www.tiktok.com/@{handle}",
        },
        source_surface="tiktok_followers_dialog_suggested_existing_chrome_cdp",
        captured_at_utc=capture_timestamp,
        method_mode="existing_chrome_cdp_dom_extraction",
        access_mode="owner_authorized_retained_session_screen_light_dom_read",
        extraction_method="visible_dialog_suggested_profile_rows_or_profile_fallback",
        browser_session_label_or_none=session_profile,
        parent_grid_packet_id_or_none=packet_id,
        parent_grid_packet_path_or_none=str(admitted_path),
        source_packet_id_or_none=packet_id,
        source_packet_path_or_none=str(admitted_path),
        parent_profile_capture_status="tiktok_parent_profile_grid_packet_available",
        suggested_accounts_capture_status="tiktok_suggested_accounts_packet_available",
        link_hub_capture_status=(
            LinkHubOutcome.CAPTURED if link_hub_url else LinkHubOutcome.NONE_VISIBLE
        ),
        link_hub_url_or_none=link_hub_url,
        browser_closed_by_runner=False,
        refresh_attempt_count=0,
        refresh_outcome=RefreshOutcome.NOT_NEEDED,
        pagination_bound=len(rows),
        suggested_accounts_observed=len(rows),
        candidate_profiles_opened=0,
        follow_unfollow_actions_taken=0,
        screenshots_emitted_to_chat=0,
        caps_applied={
            "root_profiles": 1,
            "suggested_accounts_observed": len(rows),
            "candidate_profiles_opened": 0,
            "screenshots_emitted_to_chat": 0,
        },
        stop_reason="bounded_suggested_accounts_observation_complete",
        exclusions=(
            "no_candidate_profile_open",
            "no_follow_unfollow_action",
            "no_metric_rollup",
            "no_registry_mutation",
            "no_screenshot_chat_output",
        ),
    ).to_dict()
    outer_ui_route = suggested_receipt.get("outer_ui_route")
    observed_sections = (
        ("followers_dialog_suggested_tab",)
        if outer_ui_route == "followers_dialog_suggested_tab_primary"
        else ("profile_suggested_accounts_view_all_fallback",)
    )
    observations = [
        SuggestedAccountObservation(
            handle=str(row["handle"]),
            display_name_or_none=(
                str(row["display_text_or_none"])
                if row.get("display_text_or_none")
                else None
            ),
            source_url_or_locator=(
                str(row["profile_url"]) if row.get("profile_url") else None
            ),
            observed_sections=observed_sections,
        )
        for row in rows
        if isinstance(row, dict) and row.get("handle")
    ]
    register = build_tiktok_creator_discovery_frontier_register(
        scan_receipt=scan_receipt,
        suggested_accounts=observations,
        prior_register_pointer=(
            f"{admitted_path}/raw/04_tiktok_suggested_accounts_attempt.json"
        ),
    )
    written = write_tiktok_creator_discovery_frontier_register(
        register,
        data_root,
        record_id=f"{register_id}.json",
    )
    if written is None:
        raise RuntimeError(
            "captured suggested accounts did not produce a frontier artifact"
        )
    written_path = Path(written)
    if not written_path.is_file():
        raise RuntimeError(
            f"suggested frontier writer returned a missing artifact: {written_path}"
        )
    return str(written_path)


def _build_frontier_queue(
    *,
    data_root: object,
    registry_document: dict[str, object],
    frontier_dispositions: dict[str, object] | None = None,
) -> dict[str, object]:
    registers = load_tiktok_creator_discovery_frontier_registers(data_root)
    ranked = rank_tiktok_creator_discovery_targets(
        registers,
        already_scanned_handles=(
            *tuple(_registry_tiktok_states(registry_document)),
            *tuple(_frontier_disposition_handles(frontier_dispositions)),
        ),
    )
    return {
        "register_count": len(registers),
        "actionable_candidate_count": len(ranked),
        "actionable_handles": [str(row["handle"]) for row in ranked],
    }


def _frontier_disposition_handles(document: dict[str, object] | None) -> list[str]:
    if document is None:
        return []
    wrapper = document.get("creator_frontier_disposition_current")
    if not isinstance(wrapper, dict) or wrapper.get("schema_version") != "creator_frontier_disposition_current_v1":
        raise ValueError("unsupported Creator Frontier disposition current view")
    rows = wrapper.get("dispositions")
    if not isinstance(rows, list):
        raise ValueError("Creator Frontier disposition current view requires dispositions")
    handles: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Creator Frontier disposition rows must be objects")
        handle = str(row.get("public_handle") or "").strip().lstrip("@").lower()
        if (
            not handle
            or handle in handles
            or row.get("status") not in {"eligible", "deferred", "rejected"}
        ):
            raise ValueError("Creator Frontier disposition handles must be unique normalized text")
        handles.append(handle)
    return handles


def _frontier_disposition_for_handle(
    document: dict[str, object] | None, handle: str
) -> dict[str, object] | None:
    normalized = handle.strip().lstrip("@").lower()
    _frontier_disposition_handles(document)
    wrapper = None if document is None else document.get("creator_frontier_disposition_current")
    if document is not None and (
        not isinstance(wrapper, dict)
        or wrapper.get("schema_version") != "creator_frontier_disposition_current_v1"
        or not isinstance(wrapper.get("dispositions"), list)
    ):
        raise ValueError("unsupported Creator Frontier disposition current view")
    matches = [
        row
        for row in ([] if wrapper is None else wrapper["dispositions"])
        if isinstance(row, dict)
        and str(row.get("public_handle") or "").strip().lstrip("@").lower() == normalized
    ]
    if len(matches) > 1:
        raise ValueError("multiple current Frontier dispositions match one TikTok handle")
    return matches[0] if matches else None


if __name__ == "__main__":
    raise SystemExit(main())
