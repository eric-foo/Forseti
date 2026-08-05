"""Ensure one visible retained-profile Chrome CDP session is ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.browser_user_data import browser_user_data_path_for_label
from source_capture.retained_chrome_session import (
    DEFAULT_RETAINED_CHROME_CDP_PORT,
    DEFAULT_RETAINED_CHROME_STARTUP_TIMEOUT_SECONDS,
    ensure_retained_chrome_session,
)
from source_capture.session_profiles import (
    default_session_profile_auth_state_root,
    resolve_session_profile,
    validate_session_profile_auth_state,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Launch or reuse one visible Chrome endpoint bound to a configured "
            "retained session profile. The command never navigates an existing "
            "tab, closes Chrome, inspects profile contents, or solves a challenge."
        )
    )
    parser.add_argument("--session-profile", required=True)
    parser.add_argument("--session-profile-config", type=Path)
    parser.add_argument("--auth-state-root", type=Path)
    parser.add_argument("--cdp-port", type=int, default=DEFAULT_RETAINED_CHROME_CDP_PORT)
    parser.add_argument(
        "--startup-timeout-seconds",
        type=float,
        default=DEFAULT_RETAINED_CHROME_STARTUP_TIMEOUT_SECONDS,
    )
    parser.add_argument("--launch-url", default="about:blank")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.cdp_port <= 65535:
        parser.error("--cdp-port must be in 1..65535")
    try:
        profile = resolve_session_profile(
            args.session_profile,
            config_path=args.session_profile_config,
        )
        validate_session_profile_auth_state(
            profile,
            auth_state_root=(
                args.auth_state_root or default_session_profile_auth_state_root()
            ),
        )
        if profile.browser_backend != "chrome_cdp":
            raise ValueError("session profile does not select the Chrome CDP backend")
        if profile.browser_user_data_label is None:
            raise ValueError("Chrome CDP session profile requires retained browser data")
        session = ensure_retained_chrome_session(
            user_data_dir=browser_user_data_path_for_label(
                profile.browser_user_data_label
            ),
            cdp_endpoint=f"http://127.0.0.1:{args.cdp_port}",
            launch_url=args.launch_url,
            startup_timeout_seconds=args.startup_timeout_seconds,
        )
    except ValueError as exc:
        parser.exit(status=3, message=f"retained Chrome unavailable: {exc}\n")
    receipt = session.sanitized_receipt()
    receipt.update(
        {
            "session_profile": profile.alias,
            "browser_backend": profile.browser_backend,
            "challenge_policy": profile.challenge_policy,
            "secret_values_exposed": False,
        }
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
