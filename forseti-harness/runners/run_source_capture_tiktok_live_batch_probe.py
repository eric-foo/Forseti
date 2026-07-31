from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import as_dict
from source_capture.adapters.browser_session_probe import (
    probe_local_cdp_endpoints,
    select_profile_bound_local_cdp_endpoint,
)
from source_capture.adapters.browser_snapshot import (
    ChromeCdpPageObservationSessionEngine,
)
from source_capture.auth_state import AuthenticatedSessionMode
from source_capture.browser_user_data import browser_user_data_path_for_label
from source_capture.session_profiles import (
    OWNER_HANDOFF_BEFORE_ACTION,
    default_session_profile_auth_state_root,
    resolve_session_profile,
    validate_session_profile_auth_state,
)
from source_capture.source_access_provenance import HarnessProxyProfilePosture
from source_capture.tiktok.admission import COMPLETE_LANE_NOTE
from source_capture.tiktok.batch_packet import write_tiktok_batch_packet
from source_capture.tiktok.live_batch_probe import (
    TIKTOK_BROWSER_BACKEND_CLOAKBROWSER,
    TIKTOK_BROWSER_BACKEND_CHROME_CDP,
    TIKTOK_ACCOUNT_SAFETY_STOP_MARKERS,
    TIKTOK_CHALLENGE_TEXT_MARKERS,
    TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
    TIKTOK_SUPERVISED_DEFAULT_CADENCE_MAX_GAP_SECONDS,
    TIKTOK_SUPERVISED_DEFAULT_CADENCE_MIN_GAP_SECONDS,
    write_tiktok_live_batch_probe_outputs,
)


SUMMARY_LINE_PREFIX = "tiktok_live_probe_summary_json="
SUMMARY_SCHEMA_VERSION = "tiktok_live_probe_summary_v0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture sanitized local TikTok staging JSON for one creator. "
            "Sessioned mode requires a pre-bootstrapped auth-state label; "
            "--logged-out uses no storage state. By default this runner writes "
            "staging JSON only; --admit-output or --data-root chains the "
            "existing TikTok batch admission gate after staging."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Recommended sessioned cold-agent command:\n"
            "  python runners/run_source_capture_tiktok_live_batch_probe.py `\n"
            "    --creator-handle \"<handle>\" `\n"
            "    --creator-profile-url \"https://www.tiktok.com/@<handle>\" `\n"
            "    --video-url \"https://www.tiktok.com/@<handle>/video/<video-id>\" `\n"
            "    --session-profile \"chowdakr_sg_tiktok\" `\n"
            "    --output-dir \".\\_test_runs\\tiktok_live_<handle>\" `\n"
            "    --admit-output \".\\_test_runs\\tiktok_live_<handle>_packet\"\n"
            "\n"
            "Use --data-root only when the owner explicitly wants immediate bronze/lake admission."
        ),
    )
    parser.add_argument("--creator-handle", required=True)
    parser.add_argument("--creator-profile-url", required=True)
    parser.add_argument("--video-url", action="append", required=True, dest="video_urls")
    parser.add_argument("--state-label")
    parser.add_argument(
        "--session-profile",
        help=(
            "Resolve a machine-local cookie-backed session profile before browser "
            "launch. Profile failure blocks; it never downgrades to logged-out mode."
        ),
    )
    parser.add_argument(
        "--session-profile-config",
        type=Path,
        help="Explicit machine-local session-profile config path.",
    )
    parser.add_argument("--auth-state-root", type=Path, help=argparse.SUPPRESS)

    parser.add_argument(
        "--session-mode",
        choices=[mode.value for mode in AuthenticatedSessionMode],
    )
    parser.add_argument(
        "--logged-out",
        action="store_true",
        help="Use no auth storage state; measure public logged-out TikTok access only.",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    admission_target = parser.add_mutually_exclusive_group(required=False)
    admission_target.add_argument(
        "--admit-output",
        type=Path,
        default=None,
        help=(
            "After live staging, admit through the network-free TikTok batch gate "
            "into this local SourceCapturePacket directory."
        ),
    )
    admission_target.add_argument(
        "--data-root",
        default=None,
        help=(
            "After live staging, admit through the network-free TikTok batch gate "
            "into this explicit Forseti data lake root. FORSETI_DATA_ROOT and "
            "legacy ORCA_DATA_ROOT are not read by this live runner."
        ),
    )
    parser.add_argument("--batch-label", default="tiktok_creator_batch")
    parser.add_argument(
        "--decision-question",
        default="Admit TikTok creator-batch comment, subtitle, source-text, and typed extraction seed signals.",
        help="Decision question for the optional batch-admission packet.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument(
        "--wait-until",
        choices=("commit", "domcontentloaded", "load", "networkidle"),
        default="domcontentloaded",
    )
    parser.add_argument("--viewport-width", type=int, default=1280)
    parser.add_argument("--viewport-height", type=int, default=720)
    parser.add_argument("--max-response-bytes", type=int, default=5_000_000)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument("--selector-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--browser-channel")
    parser.add_argument(
        "--browser-backend",
        choices=("playwright", "cloakbrowser"),
        default=None,
        help=(
            "Browser backend for rendered page observation. TikTok packet-grade "
            "capture defaults to cloakbrowser; playwright is diagnostic-only."
        ),
    )
    parser.add_argument(
        "--allow-diagnostic-browser-backend",
        action="store_true",
        help=(
            "Allow non-CloakBrowser backend use for explicit diagnostics. "
            "Diagnostic backend runs are not the TikTok packet-grade route."
        ),
    )
    parser.add_argument(
        "--require-harness-proxy-posture",
        choices=[
            HarnessProxyProfilePosture.NO_PROXY_PROFILE_LOADED.value,
            HarnessProxyProfilePosture.PROXY_PROFILE_LOADED.value,
        ],
        default=None,
        help=(
            "Require the auth-state provenance sidecar to attest the Source Capture "
            "harness proxy-profile posture before opening TikTok. This is not a "
            "full-network no-proxy egress proof."
        ),
    )
    parser.add_argument(
        "--cloakbrowser-humanize",
        action="store_true",
        help="Enable CloakBrowser humanized pointer/keyboard timing when using the cloakbrowser backend.",
    )
    parser.add_argument(
        "--human-challenge-handoff",
        action="store_true",
        help=(
            "Before scripted pointer actions, prompt the operator to solve a visible "
            "slider/captcha in the open browser. Scripted actions remain suppressed "
            "until the marker clears; the receipt records source-access intervention."
        ),
    )
    parser.add_argument(
        "--human-challenge-handoff-timeout-seconds",
        type=float,
        default=180.0,
    )
    parser.add_argument(
        "--cadence-min-gap-seconds",
        type=float,
        default=TIKTOK_SUPERVISED_DEFAULT_CADENCE_MIN_GAP_SECONDS,
    )
    parser.add_argument(
        "--cadence-max-gap-seconds",
        type=float,
        default=TIKTOK_SUPERVISED_DEFAULT_CADENCE_MAX_GAP_SECONDS,
    )
    parser.add_argument("--cadence-window-seconds", type=float)
    parser.add_argument("--random-seed", type=int)
    parser.add_argument(
        "--allow-challenge-close-diagnostic",
        action="store_true",
        help=(
            "Diagnostic only: use a bounded pointer click on a TikTok challenge "
            "modal X/Close control before the comment route. Any resulting "
            "capture is not clean admission proof."
        ),
    )
    parser.add_argument(
        "--allow-challenge-close-followthrough",
        action="store_true",
        help=(
            "Owner-authorized public challenge X/Close follow-through: click a "
            "dismiss control, then attempt the page-owned comment route. This "
            "does not solve a puzzle and receipts preserve the intervention."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    session_profile = None
    if args.session_profile is not None:
        manual_profile_fields = (
            args.state_label,
            args.session_mode,
            args.require_harness_proxy_posture,
            args.browser_backend,
            args.browser_channel,
        )
        if (
            args.logged_out
            or any(value is not None for value in manual_profile_fields)
            or args.allow_diagnostic_browser_backend
            or args.cloakbrowser_humanize
            or args.human_challenge_handoff
            or args.allow_challenge_close_diagnostic
            or args.allow_challenge_close_followthrough
        ):
            parser.error(
                "--session-profile cannot be combined with manual session, browser, "
                "or challenge-policy flags"
            )
        try:
            auth_state_root = (
                args.auth_state_root or default_session_profile_auth_state_root()
            )
            session_profile = resolve_session_profile(
                args.session_profile,
                config_path=args.session_profile_config,
            )
            validate_session_profile_auth_state(
                session_profile,
                auth_state_root=auth_state_root,
            )
        except ValueError as exc:
            parser.error(f"BLOCKED_SESSION_PROFILE_UNAVAILABLE: {exc}")
        state_label = session_profile.state_label
        session_mode = session_profile.session_mode
        required_harness_proxy_profile_posture = (
            session_profile.required_harness_proxy_profile_posture
        )
        browser_backend = session_profile.browser_backend
        human_challenge_handoff = (
            session_profile.challenge_policy == OWNER_HANDOFF_BEFORE_ACTION
        )
        allow_challenge_close_diagnostic = False
        allow_challenge_close_followthrough = False
        logged_out = False
    else:
        if args.session_profile_config is not None:
            parser.error("--session-profile-config requires --session-profile")
        state_label = args.state_label
        logged_out = args.logged_out
        browser_backend = args.browser_backend or TIKTOK_BROWSER_BACKEND_CLOAKBROWSER
        human_challenge_handoff = args.human_challenge_handoff
        auth_state_root = args.auth_state_root
        allow_challenge_close_diagnostic = args.allow_challenge_close_diagnostic
        allow_challenge_close_followthrough = args.allow_challenge_close_followthrough
        if logged_out:
            if state_label is not None or args.session_mode is not None:
                parser.error(
                    "--logged-out cannot be combined with --state-label or --session-mode"
                )
            if args.require_harness_proxy_posture is not None:
                parser.error(
                    "--require-harness-proxy-posture requires sessioned mode with --state-label"
                )
            session_mode = None
        else:
            if state_label is None or args.session_mode is None:
                parser.error(
                    "sessioned mode requires --state-label and --session-mode; "
                    "use --logged-out for public logged-out capture"
                )
            session_mode = AuthenticatedSessionMode(args.session_mode)
        required_harness_proxy_profile_posture = (
            HarnessProxyProfilePosture(args.require_harness_proxy_posture)
            if args.require_harness_proxy_posture is not None
            else None
        )

    if allow_challenge_close_diagnostic and allow_challenge_close_followthrough:
        parser.error(
            "--allow-challenge-close-diagnostic and "
            "--allow-challenge-close-followthrough are mutually exclusive"
        )
    if (
        browser_backend != TIKTOK_BROWSER_BACKEND_CLOAKBROWSER
        and not (
            session_profile is not None
            and browser_backend == TIKTOK_BROWSER_BACKEND_CHROME_CDP
        )
        and not args.allow_diagnostic_browser_backend
    ):
        parser.error(
            "manual non-CloakBrowser backends are diagnostic-only for TikTok; pass "
            "--allow-diagnostic-browser-backend to opt in"
        )
    if (
        browser_backend == TIKTOK_BROWSER_BACKEND_CLOAKBROWSER
        and args.browser_channel is not None
    ):
        parser.error(
            "--browser-channel cannot be combined with --browser-backend cloakbrowser"
        )
    if args.cloakbrowser_humanize and browser_backend != TIKTOK_BROWSER_BACKEND_CLOAKBROWSER:
        parser.error("--cloakbrowser-humanize requires --browser-backend cloakbrowser")
    cloakbrowser_humanize = (
        args.cloakbrowser_humanize
        or browser_backend == TIKTOK_BROWSER_BACKEND_CLOAKBROWSER
    )
    owned_engine = None
    if (
        session_profile is not None
        and browser_backend == TIKTOK_BROWSER_BACKEND_CHROME_CDP
    ):
        try:
            owned_engine = _profile_chrome_cdp_engine(session_profile)
        except ValueError as exc:
            parser.error(f"BLOCKED_SESSION_PROFILE_UNAVAILABLE: {exc}")
    try:
        paths = write_tiktok_live_batch_probe_outputs(
            creator_handle=args.creator_handle,
            creator_profile_url=args.creator_profile_url,
            video_urls=args.video_urls,
            state_label=state_label,
            session_mode=session_mode,
            logged_out=logged_out,
            auth_state_root=auth_state_root,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout_seconds,
            wait_until=args.wait_until,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            max_response_bytes=args.max_response_bytes,
            settle_seconds=args.settle_seconds,
            selector_timeout_seconds=args.selector_timeout_seconds,
            browser_channel=args.browser_channel,
            browser_backend=browser_backend,
            required_harness_proxy_profile_posture=required_harness_proxy_profile_posture,
            cloakbrowser_humanize=cloakbrowser_humanize,
            human_challenge_handoff=human_challenge_handoff,
            human_challenge_handoff_timeout_seconds=args.human_challenge_handoff_timeout_seconds,
            cadence_min_gap_seconds=args.cadence_min_gap_seconds,
            cadence_max_gap_seconds=args.cadence_max_gap_seconds,
            cadence_window_seconds=args.cadence_window_seconds,
            random_seed=args.random_seed,
            allow_challenge_close_diagnostic=allow_challenge_close_diagnostic,
            allow_challenge_close_followthrough=allow_challenge_close_followthrough,
            engine=owned_engine,
        )
    finally:
        if owned_engine is not None:
            owned_engine.close()
    print(f"grid_result_json={paths.grid_result_json_path}")
    print(f"cadence_result_json={paths.cadence_result_json_path}")
    admission_target = _admission_target_kind(
        admit_output=args.admit_output,
        data_root=args.data_root,
    )
    print(
        _summary_line(
            _staging_summary(
                paths=paths,
                admission_target=admission_target,
                browser_backend=browser_backend,
                session_mode=(
                    "public_logged_out"
                    if logged_out
                    else session_mode.value
                ),
                provenance_requirement_status=(
                    "validated"
                    if required_harness_proxy_profile_posture is not None
                    else "not_requested"
                ),
            )
        )
    )
    if args.admit_output is not None or args.data_root is not None:
        try:
            data_root = None
            if args.data_root is not None:
                from data_lake.root import DataLakeRoot

                data_root = DataLakeRoot.resolve(explicit=args.data_root)
            exit_code, admitted_path = write_tiktok_batch_packet(
                creator_handle=args.creator_handle,
                creator_profile_url=args.creator_profile_url,
                grid_result_json=paths.grid_result_json_path.read_bytes(),
                cadence_result_jsons=[paths.cadence_result_json_path.read_bytes()],
                output_directory=args.admit_output if data_root is None else None,
                data_root=data_root,
                decision_question=args.decision_question,
                batch_label=args.batch_label,
                source_file_receipts=[
                    _source_receipt(paths.grid_result_json_path, "grid_result_json"),
                    _source_receipt(paths.cadence_result_json_path, "cadence_result_json_1"),
                ],
            )
        except ValueError as exc:
            print(
                _summary_line(
                    _admission_summary(
                        admission_target=admission_target,
                        outcome="fail_closed_admission_rejected",
                        error_type=type(exc).__name__,
                    )
                )
            )
            parser.exit(status=2, message=f"source capture tiktok live batch admission failed: {exc}\n")
        except Exception as exc:  # noqa: BLE001 - keep admission/lake failures visible
            print(
                _summary_line(
                    _admission_summary(
                        admission_target=admission_target,
                        outcome="fail_closed_admission_infra_error",
                        error_type=type(exc).__name__,
                    )
                )
            )
            parser.exit(
                status=3,
                message=(
                    "source capture tiktok live batch admission failed: "
                    f"{type(exc).__name__}: {exc}\n"
                ),
            )
        if exit_code != 0:
            print(
                _summary_line(
                    _admission_summary(
                        admission_target=admission_target,
                        outcome="fail_closed_admission_nonzero_exit",
                        error_type="nonzero_exit",
                    )
                )
            )
            parser.exit(
                status=exit_code,
                message=f"source capture tiktok live batch admission failed: {admitted_path}\n",
            )
        print(COMPLETE_LANE_NOTE)
        print(
            _summary_line(
                _admission_summary(
                    admission_target=admission_target,
                    outcome=(
                        "bronze_packet_admitted"
                        if admission_target == "bronze_data_root"
                        else "local_packet_admitted"
                    ),
                )
            )
        )
        print(f"admitted_packet={admitted_path}")
    return 0


def _profile_chrome_cdp_engine(session_profile):  # noqa: ANN001
    user_data_label = session_profile.browser_user_data_label
    if user_data_label is None:
        raise ValueError("Chrome CDP session profile requires a retained browser profile")
    user_data_dir = browser_user_data_path_for_label(user_data_label)
    if not user_data_dir.is_dir() or not any(user_data_dir.iterdir()):
        raise ValueError("retained browser profile is missing or empty")
    probe = probe_local_cdp_endpoints()
    endpoint = select_profile_bound_local_cdp_endpoint(
        probe,
        user_data_dir=user_data_dir,
    )
    return ChromeCdpPageObservationSessionEngine(
        cdp_endpoint=endpoint,
        pre_action_stop_markers=TIKTOK_ACCOUNT_SAFETY_STOP_MARKERS,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
    )


def _summary_line(payload: dict[str, object]) -> str:
    return (
        SUMMARY_LINE_PREFIX
        + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    )


def _admission_target_kind(*, admit_output: Path | None, data_root: str | None) -> str:
    if admit_output is not None:
        return "local_admit_output"
    if data_root is not None:
        return "bronze_data_root"
    return "staging_only"


def _staging_summary(
    *,
    paths,
    admission_target: str,
    browser_backend: str,
    session_mode: str | None,
    provenance_requirement_status: str,
) -> dict[str, object]:
    cadence = _read_json_object(paths.cadence_result_json_path)
    results = _as_list(cadence.get("results"))
    failures = _as_list(cadence.get("failures"))
    owner_attention_required = _owner_attention_required(results=results, failures=failures)
    challenge_count = _first_int(cadence.get("challenge_count"), 0)
    failure_count = len(failures)
    subtitle_reason_counts: dict[str, int] = {}
    subtitle_success_count = 0
    admitted_comment_response_count = 0
    dom_visible_comment_candidate_count = 0
    for row in results:
        row_dict = as_dict(row)
        receipt = as_dict(row_dict.get("capture_receipt"))
        admitted_comment_response_count += _first_int(
            receipt.get("admitted_comment_response_count"), 0
        )
        dom_visible_comment_candidate_count += _first_int(
            receipt.get("dom_visible_comment_candidate_count"), 0
        )
        subtitle = as_dict(row_dict.get("subtitle"))
        reason = _first_str(subtitle.get("reason"))
        if _as_bool(subtitle.get("success")) is True:
            subtitle_success_count += 1
        elif reason:
            subtitle_reason_counts[reason] = subtitle_reason_counts.get(reason, 0) + 1
    first_failure_reason = None
    if failures:
        first_failure_reason = _first_str(as_dict(failures[0]).get("reason"))
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": "staging",
        "outcome": _staging_outcome(
            completed_count=_first_int(cadence.get("completed_count"), 0),
            challenge_count=challenge_count,
            failure_count=failure_count,
            owner_attention_required=owner_attention_required,
        ),
        "admission_target": admission_target,
        "browser_backend": browser_backend,
        "session_mode": session_mode,
        "provenance_requirement_status": provenance_requirement_status,
        "requested_video_count": _first_int(cadence.get("requested_video_count"), 0),
        "attempted_count": _first_int(cadence.get("attempted_count"), 0),
        "completed_count": _first_int(cadence.get("completed_count"), 0),
        "challenge_count": challenge_count,
        "failure_count": failure_count,
        "first_failure_reason": first_failure_reason,
        "owner_attention_required": owner_attention_required,
        "admitted_comment_response_count": admitted_comment_response_count,
        "dom_visible_comment_candidate_count": dom_visible_comment_candidate_count,
        "subtitle_success_count": subtitle_success_count,
        "subtitle_non_capture_reason_counts": subtitle_reason_counts,
    }


def _admission_summary(
    *,
    admission_target: str,
    outcome: str,
    error_type: str | None = None,
) -> dict[str, object]:
    summary: dict[str, object] = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": "admission",
        "admission_target": admission_target,
        "outcome": outcome,
    }
    if error_type is not None:
        summary["error_type"] = error_type
        summary["fail_closed"] = True
    else:
        summary["packet_path_printed"] = True
    return summary


def _staging_outcome(
    *,
    completed_count: int,
    challenge_count: int,
    failure_count: int,
    owner_attention_required: bool,
) -> str:
    if owner_attention_required:
        return "owner_attention_required"
    if challenge_count > 0 or failure_count > 0:
        return "fail_closed_staging_has_failures"
    if completed_count > 0:
        return "staging_complete"
    return "fail_closed_no_completed_videos"


def _owner_attention_required(*, results: list[object], failures: list[object]) -> bool:
    for row in results:
        receipt = as_dict(as_dict(row).get("capture_receipt"))
        if _as_bool(receipt.get("owner_attention_required")) is True:
            return True
        if _as_bool(receipt.get("manual_challenge_attention_required")) is True:
            return True
    for failure in failures:
        triage = as_dict(as_dict(failure).get("blocker_triage"))
        if _as_bool(triage.get("owner_attention_required")) is True:
            return True
        if _as_bool(triage.get("manual_challenge_attention_required")) is True:
            return True
    return False


def _read_json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _first_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _first_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _as_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _source_receipt(path: Path, role: str) -> dict[str, object]:
    raw = path.read_bytes()
    resolved = str(path.resolve())
    return {
        "role": role,
        "file_name": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "source_path_sha256": hashlib.sha256(resolved.encode("utf-8")).hexdigest(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
