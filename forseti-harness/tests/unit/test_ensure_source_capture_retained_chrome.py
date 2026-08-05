import json
from pathlib import Path

from runners import ensure_source_capture_retained_chrome as runner
from source_capture.auth_state import AuthenticatedSessionMode
from source_capture.retained_chrome_session import RetainedChromeSession
from source_capture.session_profiles import SourceCaptureSessionProfile
from source_capture.source_access_provenance import HarnessProxyProfilePosture


def _profile() -> SourceCaptureSessionProfile:
    return SourceCaptureSessionProfile(
        alias="chowdakr_sg_tiktok",
        platform="tiktok",
        state_label="state",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        required_harness_proxy_profile_posture=(
            HarnessProxyProfilePosture.NO_PROXY_PROFILE_LOADED
        ),
        browser_backend="chrome_cdp",
        challenge_policy="owner_handoff_before_action",
        browser_user_data_label="retained",
    )


def test_cli_emits_only_sanitized_ready_receipt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    profile_dir = tmp_path / "secret-profile-path"
    profile_dir.mkdir()
    (profile_dir / "marker").write_text("retained", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(runner, "resolve_session_profile", lambda *_a, **_k: _profile())
    monkeypatch.setattr(
        runner, "validate_session_profile_auth_state", lambda *_a, **_k: None
    )
    monkeypatch.setattr(
        runner, "browser_user_data_path_for_label", lambda *_a, **_k: profile_dir
    )

    def ensure(**kwargs):
        captured.update(kwargs)
        return RetainedChromeSession(
            cdp_endpoint="http://127.0.0.1:9223",
            disposition="launched",
        )

    monkeypatch.setattr(runner, "ensure_retained_chrome_session", ensure)

    assert runner.main(["--session-profile", "chowdakr_sg_tiktok"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["disposition"] == "launched"
    assert payload["profile_bound"] is True
    assert payload["secret_values_exposed"] is False
    assert str(profile_dir) not in str(payload)
    assert captured["user_data_dir"] == profile_dir
