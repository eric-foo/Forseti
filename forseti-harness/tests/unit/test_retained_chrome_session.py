from pathlib import Path

import pytest

from source_capture.retained_chrome_session import ensure_retained_chrome_session


ENDPOINT = "http://127.0.0.1:9223"


def _profile(tmp_path: Path) -> Path:
    profile = tmp_path / "retained-profile"
    profile.mkdir()
    (profile / "marker").write_text("retained", encoding="utf-8")
    return profile


def test_reuses_exact_profile_bound_endpoint_without_launch(tmp_path: Path) -> None:
    profile = _profile(tmp_path)

    session = ensure_retained_chrome_session(
        user_data_dir=profile,
        probe_func=lambda ports: {"live_endpoints": [ENDPOINT]},
        select_func=lambda report, *, user_data_dir: ENDPOINT,
        profile_running_func=lambda _path: (_ for _ in ()).throw(
            AssertionError("running-process fallback should not be read")
        ),
        launch_func=lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("existing exact endpoint must be reused")
        ),
    )

    assert session.disposition == "reused"
    assert session.cdp_endpoint == ENDPOINT


def test_launches_visible_profile_and_proves_exact_binding(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    chrome = tmp_path / "chrome.exe"
    chrome.write_bytes(b"chrome")
    live = False
    launches: list[dict[str, object]] = []

    def probe(ports):
        assert tuple(ports) == (9223,)
        return {"live_endpoints": [ENDPOINT] if live else []}

    def select(report, *, user_data_dir):
        assert user_data_dir == profile.resolve()
        if ENDPOINT not in report["live_endpoints"]:
            raise ValueError("observed 0")
        return ENDPOINT

    def launch(**kwargs):
        nonlocal live
        launches.append(kwargs)
        live = True

    session = ensure_retained_chrome_session(
        user_data_dir=profile,
        probe_func=probe,
        select_func=select,
        profile_running_func=lambda _path: False,
        chrome_executable_func=lambda: chrome,
        launch_func=launch,
        sleep_func=lambda _seconds: None,
    )

    assert session.disposition == "launched"
    assert session.cdp_endpoint == ENDPOINT
    assert len(launches) == 1
    assert launches[0]["user_data_dir"] == profile.resolve()
    assert launches[0]["port"] == 9223
    receipt = session.sanitized_receipt()
    assert "user_data" not in receipt
    assert str(profile) not in str(receipt)


def test_open_profile_without_cdp_fails_without_closing_or_launching(
    tmp_path: Path,
) -> None:
    profile = _profile(tmp_path)

    with pytest.raises(ValueError, match="BLOCKED_RETAINED_PROFILE_OPEN_WITHOUT_CDP"):
        ensure_retained_chrome_session(
            user_data_dir=profile,
            probe_func=lambda ports: {"live_endpoints": []},
            select_func=lambda report, *, user_data_dir: (_ for _ in ()).throw(
                ValueError("observed 0")
            ),
            profile_running_func=lambda _path: True,
            launch_func=lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("harness must not relaunch or close an open profile")
            ),
        )


def test_requested_port_owned_by_wrong_profile_fails_before_launch(
    tmp_path: Path,
) -> None:
    profile = _profile(tmp_path)

    with pytest.raises(
        ValueError, match="BLOCKED_CDP_ENDPOINT_OWNED_BY_DIFFERENT_PROFILE"
    ):
        ensure_retained_chrome_session(
            user_data_dir=profile,
            probe_func=lambda ports: {"live_endpoints": [ENDPOINT]},
            select_func=lambda report, *, user_data_dir: (_ for _ in ()).throw(
                ValueError("wrong profile")
            ),
            profile_running_func=lambda _path: False,
            launch_func=lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("wrong-profile port must never be reused")
            ),
        )


def test_rejects_remote_or_credentialed_cdp_endpoint(tmp_path: Path) -> None:
    profile = _profile(tmp_path)

    for endpoint in (
        "http://example.com:9223",
        "http://user:secret@127.0.0.1:9223",
        "https://127.0.0.1:9223",
    ):
        with pytest.raises(ValueError, match="credential-free loopback"):
            ensure_retained_chrome_session(
                user_data_dir=profile,
                cdp_endpoint=endpoint,
            )
