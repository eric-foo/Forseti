from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

import pytest

from data_lake.root import DataLakeRoot, raw_shard
from runners import run_source_capture_tiktok_live_batch_probe as runner
from source_capture.adapters.browser_snapshot import (
    BrowserPageObservationSuccess,
    PAGE_LOAD_BEFORE_POINTER_ACTIONS_HANDOFF_NAME,
    BrowserPagePointerAction,
    BrowserPageResponse,
    BrowserPageWheelAction,
)
from source_capture.auth_state import (
    AuthenticatedSessionMode,
    auth_state_path_for_label,
    write_auth_state_metadata,
)
from source_capture.session_profiles import SourceCaptureSessionProfile
from source_capture.source_access_provenance import HarnessProxyProfilePosture
from source_capture.tiktok.admission import COMPLETE_LANE_NOTE
from source_capture.tiktok.batch_packet import write_tiktok_batch_packet
import source_capture.tiktok.live_batch_probe as live_batch_probe
from source_capture.tiktok.blocker_triage import (
    TIKTOK_BLOCKER_ACTION_CONTINUE,
    TIKTOK_BLOCKER_ACTION_RELOAD_ONCE_CANDIDATE,
    TIKTOK_BLOCKER_ACTION_STOP,
    TIKTOK_BLOCKER_CLASS_CHALLENGE_OR_SECURITY,
    TIKTOK_BLOCKER_CLASS_INFRASTRUCTURE_RELOAD,
    TIKTOK_BLOCKER_CLASS_NO_BLOCKER,
)
from source_capture.tiktok.live_batch_probe import (
    TIKTOK_CHALLENGE_AFTER_CLOSE_DIAGNOSTIC_REASON,
    TIKTOK_CHALLENGE_AFTER_CLOSE_FOLLOWTHROUGH_REASON,
    TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
    TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_REASON,
    TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
    TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON,
    TIKTOK_CHALLENGE_VISUAL_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
    TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
    TIKTOK_COMMENT_ROUTE_NO_RESPONSE_REASON,
    TIKTOK_COMMENT_SURFACE_TOGGLE_POINTER_SEQUENCE_NAME,
    TIKTOK_LOGGED_OUT_SESSION_MODE,
    TIKTOK_MANUAL_CHALLENGE_ATTENTION_REQUIRED_REASON,
    TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
    TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
    TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
    TIKTOK_OPEN_MORE_LIKE_THIS_POINTER_ACTION_NAME,
    TIKTOK_REOPEN_COMMENTS_POINTER_ACTION_NAME,
    is_tiktok_comment_list_url,
    write_tiktok_live_batch_probe_outputs,
)


@dataclass
class _FakeObservationEngine:
    outcomes: list[BrowserPageObservationSuccess]

    def __post_init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def capture_page_observation(
        self,
        *,
        url: str,
        timeout_seconds: float,
        wait_until: str,
        viewport_width: int,
        viewport_height: int,
        dom_extract_script: str,
        dom_extract_arg: object,
        response_url_predicate: Callable[[str], bool],
        pointer_action_response_url_predicate: Callable[[str], bool] | None = None,
        post_load_action_script: str | None = None,
        post_load_action_arg: object = None,
        post_load_wheel_action: BrowserPageWheelAction | None = None,
        post_load_pointer_action: BrowserPagePointerAction | None = None,
        post_load_pointer_actions: tuple[BrowserPagePointerAction, ...] = (),
        selector: str | None = None,
        selector_timeout_seconds: float = 5.0,
        max_response_bytes: int = 5_000_000,
        settle_seconds: float = 0.0,
        lazy_load_scroll_passes: int = 0,
        lazy_load_scroll_step_px: int = 0,
        lazy_load_response_stop_condition: object = None,
        dom_extract_after_lazy_load: bool = False,
        block_resource_types: tuple[str, ...] = (),
        proxy_profile: object = None,
        storage_state_path: Path | None = None,
        headless: bool = True,
        browser_channel: str | None = None,
    ) -> BrowserPageObservationSuccess:
        self.calls.append(
            {
                "url": url,
                "headless": headless,
                "storage_state_path": storage_state_path,
                "post_load_action_script": post_load_action_script,
                "post_load_wheel_action": post_load_wheel_action,
                "post_load_pointer_action": post_load_pointer_action,
                "post_load_pointer_actions": post_load_pointer_actions,
                "response_predicate_matches_comment_list": response_url_predicate(
                    "https://www.tiktok.com/api/comment/list/?aweme_id=7390000000000000001&cursor=0"
                ),
                "response_predicate_matches_subtitle": response_url_predicate(
                    "https://v16-webapp.tiktok.com/subtitle.webvtt"
                ),
                "pointer_stop_predicate_matches_comment_list": (
                    pointer_action_response_url_predicate(
                        "https://www.tiktok.com/api/comment/list/?aweme_id=7390000000000000001&cursor=0"
                    )
                    if pointer_action_response_url_predicate is not None
                    else None
                ),
                "pointer_stop_predicate_matches_subtitle": (
                    pointer_action_response_url_predicate(
                        "https://v16-webapp.tiktok.com/subtitle.webvtt"
                    )
                    if pointer_action_response_url_predicate is not None
                    else None
                ),
            }
        )
        outcome = self.outcomes.pop(0)
        return replace(
            outcome,
            responses=tuple(
                response
                for response in outcome.responses
                if response_url_predicate(response.final_url)
            ),
        )


def _summary_payloads(output: str) -> list[dict[str, object]]:
    return [
        json.loads(line.split("=", 1)[1])
        for line in output.splitlines()
        if line.startswith(runner.SUMMARY_LINE_PREFIX)
    ]


def _write_sessioned_probe(
    tmp_path: Path,
    *,
    video_urls: list[str],
    auth_state_root: Path | None = None,
    **overrides: object,
):
    """Call the SUT with the standard sessioned-probe kwargs of this file."""
    if auth_state_root is None:
        auth_state_root = _auth_state(tmp_path)
    kwargs: dict[str, object] = dict(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=video_urls,
        state_label="test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        auth_state_root=auth_state_root,
        output_dir=tmp_path / "out",
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        random_seed=1,
        sleep_fn=lambda _seconds: None,
    )
    kwargs.update(overrides)
    return write_tiktok_live_batch_probe_outputs(**kwargs)


def _write_logged_out_probe(
    tmp_path: Path,
    *,
    video_urls: list[str],
    **overrides: object,
):
    """Call the SUT with the standard logged-out-probe kwargs of this file."""
    kwargs: dict[str, object] = dict(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=video_urls,
        logged_out=True,
        output_dir=tmp_path / "out",
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        random_seed=1,
        sleep_fn=lambda _seconds: None,
    )
    kwargs.update(overrides)
    return write_tiktok_live_batch_probe_outputs(**kwargs)


def test_live_probe_runner_help_surfaces_sessioned_cold_agent_command(capsys) -> None:
    try:
        runner.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("help did not exit through argparse")

    captured = capsys.readouterr()
    assert "Recommended sessioned cold-agent command" in captured.out
    assert "--session-profile \"chowdakr_sg_tiktok\"" in captured.out
    assert "--admit-output" in captured.out


def _chrome_session_profile() -> SourceCaptureSessionProfile:
    return SourceCaptureSessionProfile(
        alias="chowdakr_sg_tiktok",
        platform="tiktok",
        state_label="test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        required_harness_proxy_profile_posture=(
            HarnessProxyProfilePosture.NO_PROXY_PROFILE_LOADED
        ),
        browser_backend="chrome_cdp",
        challenge_policy="owner_handoff_before_action",
        browser_user_data_label="test-tiktok-browser",
    )


def test_live_probe_runner_uses_profile_chrome_cdp_without_diagnostic_downgrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile_dir = tmp_path / "browser-profile"
    profile_dir.mkdir()
    (profile_dir / "marker").write_text("retained", encoding="utf-8")
    captured: dict[str, object] = {}

    class FakeChromeEngine:
        def __init__(self, **kwargs: object) -> None:
            captured["engine_kwargs"] = kwargs
            captured["engine"] = self
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class Paths:
        grid_result_json_path = tmp_path / "grid.json"
        cadence_result_json_path = tmp_path / "cadence.json"

    Paths.grid_result_json_path.write_text("{}", encoding="utf-8")
    Paths.cadence_result_json_path.write_text(
        json.dumps(
            {
                "requested_video_count": 1,
                "attempted_count": 1,
                "completed_count": 1,
                "challenge_count": 0,
                "results": [],
                "failures": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(runner, "resolve_session_profile", lambda *_a, **_k: _chrome_session_profile())
    monkeypatch.setattr(runner, "validate_session_profile_auth_state", lambda *_a, **_k: None)
    monkeypatch.setattr(runner, "browser_user_data_path_for_label", lambda *_a, **_k: profile_dir)
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda: {"live_endpoints": ["http://127.0.0.1:9223"]},
    )
    monkeypatch.setattr(
        runner,
        "select_profile_bound_local_cdp_endpoint",
        lambda report, *, user_data_dir: "http://127.0.0.1:9223",
    )
    monkeypatch.setattr(runner, "ChromeCdpPageObservationSessionEngine", FakeChromeEngine)

    def fake_write(**kwargs: object):
        captured["write_kwargs"] = kwargs
        return Paths()

    monkeypatch.setattr(runner, "write_tiktok_live_batch_probe_outputs", fake_write)

    assert runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "--session-profile",
            "chowdakr_sg_tiktok",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    ) == 0

    write_kwargs = captured["write_kwargs"]
    assert isinstance(write_kwargs, dict)
    assert write_kwargs["browser_backend"] == "chrome_cdp"
    assert write_kwargs["engine"] is captured["engine"]
    assert captured["engine_kwargs"]["cdp_endpoint"] == "http://127.0.0.1:9223"
    assert captured["engine"].closed is True


def test_live_probe_runner_stops_before_capture_without_one_profile_cdp_endpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile_dir = tmp_path / "browser-profile"
    profile_dir.mkdir()
    (profile_dir / "marker").write_text("retained", encoding="utf-8")
    capture_called = False

    monkeypatch.setattr(runner, "resolve_session_profile", lambda *_a, **_k: _chrome_session_profile())
    monkeypatch.setattr(runner, "validate_session_profile_auth_state", lambda *_a, **_k: None)
    monkeypatch.setattr(runner, "browser_user_data_path_for_label", lambda *_a, **_k: profile_dir)
    monkeypatch.setattr(runner, "probe_local_cdp_endpoints", lambda: {"live_endpoints": []})
    monkeypatch.setattr(
        runner,
        "select_profile_bound_local_cdp_endpoint",
        lambda report, *, user_data_dir: (_ for _ in ()).throw(
            ValueError(
                "Chrome CDP requires exactly one live endpoint bound to the retained "
                "browser profile; observed 0"
            )
        ),
    )

    def unexpected_write(**_kwargs: object):
        nonlocal capture_called
        capture_called = True

    monkeypatch.setattr(runner, "write_tiktok_live_batch_probe_outputs", unexpected_write)

    with pytest.raises(SystemExit) as exc:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--session-profile",
                "chowdakr_sg_tiktok",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )

    assert exc.value.code == 2
    assert capture_called is False


def test_profile_chrome_cdp_engine_rejects_live_wrong_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile_dir = tmp_path / "browser-profile"
    profile_dir.mkdir()
    (profile_dir / "marker").write_text("retained", encoding="utf-8")
    monkeypatch.setattr(runner, "browser_user_data_path_for_label", lambda *_a, **_k: profile_dir)
    monkeypatch.setattr(
        runner,
        "probe_local_cdp_endpoints",
        lambda: {"live_endpoints": ["http://127.0.0.1:9223"]},
    )
    monkeypatch.setattr(
        runner,
        "select_profile_bound_local_cdp_endpoint",
        lambda report, *, user_data_dir: (_ for _ in ()).throw(
            ValueError(
                "Chrome CDP requires exactly one live endpoint bound to the retained "
                "browser profile; observed 0"
            )
        ),
    )

    with pytest.raises(ValueError, match="bound to the retained browser profile"):
        runner._profile_chrome_cdp_engine(_chrome_session_profile())



def test_live_probe_writes_sanitized_staging_compatible_with_batch_admission(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    response_url = (
        "https://www.tiktok.com/api/comment/list/"
        "?aweme_id=7390000000000000001&cursor=0&count=20"
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                page_context_observations=[
                    {
                        "schema_version": "passive_page_interaction_context_v0",
                        "sequence_index": 0,
                        "action_kind": "navigation",
                        "before_action_name": "page_navigation",
                        "observed_at_utc": "2026-07-24T10:00:00Z",
                        "observation_status": "observed",
                        "visibility_state_or_none": "hidden",
                        "document_has_focus_or_none": False,
                    }
                ],
                response=BrowserPageResponse(
                    requested_url=response_url,
                    final_url=response_url,
                    status=200,
                    ok=True,
                    body_text=json.dumps(
                        {
                            "cursor": 20,
                            "has_more": 1,
                            "total": 42,
                            "comments": [
                                {
                                    "cid": "7291",
                                    "text": "Love the breakdown",
                                    "create_time": 1710000000,
                                    "digg_count": 7,
                                    "reply_comment_total": 1,
                                    "user": {
                                        "uid": "u1",
                                        "unique_id": "viewer_one",
                                        "nickname": "Viewer One",
                                    },
                                }
                            ],
                        }
                    ),
                    response_headers={"content-type": "application/json"},
                    request_method="GET",
                    resource_type="fetch",
                ),
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    grid = json.loads(paths.grid_result_json_path.read_text(encoding="utf-8"))
    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    serialized = json.dumps({"grid": grid, "cadence": cadence}, sort_keys=True)

    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 1
    assert cadence["results"][0]["comment_responses"][0]["url_summary"]["query_key_count"] == 3
    assert cadence["results"][0]["comment_responses"][0]["request_method"] == "GET"
    assert cadence["results"][0]["comment_responses"][0]["resource_type"] == "fetch"
    assert "https://www.tiktok.com/api/comment/list/" not in serialized
    assert '"body_text"' not in serialized
    assert str(auth_root) not in serialized
    assert str(engine.calls[0]["storage_state_path"]) not in serialized
    assert cadence["results"][0]["capture_receipt"]["blocker_triage"] == {
        "blocker_class": TIKTOK_BLOCKER_CLASS_NO_BLOCKER,
        "action": TIKTOK_BLOCKER_ACTION_CONTINUE,
        "reason": "no_blocker_markers_observed",
        "challenge_marker_seen": False,
        "dismiss_candidate_count": 0,
        "reload_candidate_count": 0,
        "hydration_present": True,
        "item_struct_present": True,
        "action_mode": "classification_only",
        "action_taken": False,
    }
    receipt = cadence["results"][0]["capture_receipt"]
    assert receipt["page_interaction_context_observations"] == [
        {
            "schema_version": "passive_page_interaction_context_v0",
            "sequence_index": 0,
            "action_kind": "navigation",
            "before_action_name": "page_navigation",
            "observed_at_utc": "2026-07-24T10:00:00Z",
            "observation_status": "observed",
            "visibility_state_or_none": "hidden",
            "document_has_focus_or_none": False,
        }
    ]
    assert receipt["benign_overlay_action"] == _benign_overlay_action_receipt()
    assert receipt["comment_action"] == {
        "sequence_name": TIKTOK_COMMENT_SURFACE_TOGGLE_POINTER_SEQUENCE_NAME,
        "action_count": len(_pointer_action_sequence_receipt()),
        "action_sequence": _pointer_action_sequence_receipt(),
        "clicked_all_targets": True,
    }
    assert engine.calls[0]["headless"] is False
    assert engine.calls[0]["post_load_action_script"] is None
    assert engine.calls[0]["post_load_pointer_action"] is None
    pointer_actions = engine.calls[0]["post_load_pointer_actions"]
    assert isinstance(pointer_actions, tuple)
    assert [action.action_name for action in pointer_actions] == [
        TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
        TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
        *_comment_route_action_names(),
    ]
    assert pointer_actions[0].text_markers == ("retry", "retry again", "try again", "reload")
    assert pointer_actions[1].text_markers == (
        "got it",
        "not now",
        "continue in browser",
        "maybe later",
    )
    assert "browse your feed" in pointer_actions[1].page_text_markers
    assert pointer_actions[1].exact_text_markers == ("ok", "okay")
    assert pointer_actions[2].candidate_selector == (
        '[data-e2e="comment-icon"],[data-e2e*="comment"],button,[role="button"],a'
    )
    assert pointer_actions[2].text_markers == ("comment", "comments")
    assert pointer_actions[2].move_steps_min == 6
    assert pointer_actions[2].move_steps_max == 12
    assert pointer_actions[3].text_markers == (
        "more like this",
        "more-like-this",
        "more_like_this",
        "you may like",
        "you-may-like",
        "you_may_like",
    )
    assert "div,span,p" in pointer_actions[3].candidate_selector
    assert pointer_actions[3].exact_text_markers == ("more like this", "you may like")
    assert pointer_actions[3].prefer_smallest_match is True
    assert (
        pointer_actions[2].wait_after_range
        == live_batch_probe.TIKTOK_STATE_WAIT_5000_DELAY_RANGE
    )
    assert (
        pointer_actions[4].wait_after_range
        == live_batch_probe.TIKTOK_STATE_WAIT_5000_DELAY_RANGE
    )
    for action in pointer_actions:
        if action.action_name in {
            TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
            TIKTOK_REOPEN_COMMENTS_POINTER_ACTION_NAME,
        }:
            assert action.stop_wait_on_observed_response is True
            assert action.stop_sequence_on_observed_response is True
    assert engine.calls[0]["response_predicate_matches_comment_list"] is True

    code, message = write_tiktok_batch_packet(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        batch_label="fake-live-probe",
        decision_question="offline fake-engine admission compatibility",
        grid_result_json=paths.grid_result_json_path.read_bytes(),
        cadence_result_jsons=[paths.cadence_result_json_path.read_bytes()],
        output_directory=tmp_path / "packet",
        source_file_receipts=[],
    )
    assert code == 0
    packet_payload = json.loads(
        (Path(message) / "raw" / "01_tiktok_batch_capture.json").read_text(encoding="utf-8")
    )
    assert packet_payload["batch_summary"]["video_count"] == 1
    assert packet_payload["batch_summary"]["captured_comment_count"] == 1
    assert packet_payload["batch_summary"]["subtitle_info_video_count"] == 1
    assert packet_payload["videos"][0]["subtitles"]["posture"] == "source_native_subtitle_not_captured"
    assert packet_payload["videos"][0]["subtitles"]["subtitle_infos"][0]["url_redacted"] is True


def test_live_probe_captures_source_native_subtitle_transcript(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    video_id = "7390000000000000001"
    subtitle_url = "https://v16-webapp.tiktok.com/subtitle.webvtt"
    subtitle_body = (
        b"WEBVTT\n\n"
        b"00:00:00.000 --> 00:00:01.000\n"
        b"This fragrance is everywhere\n\n"
        b"00:00:01.000 --> 00:00:02.000\n"
        b"Bronze shimmer test\n"
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id=video_id,
                responses=[
                    _comment_response(video_id=video_id),
                    _subtitle_response(url=subtitle_url, body=subtitle_body),
                ],
                subtitle_url=subtitle_url,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        auth_state_root=auth_root,
        engine=engine,
    )

    assert engine.calls[0]["response_predicate_matches_comment_list"] is True
    assert engine.calls[0]["response_predicate_matches_subtitle"] is True
    assert engine.calls[0]["pointer_stop_predicate_matches_comment_list"] is True
    assert engine.calls[0]["pointer_stop_predicate_matches_subtitle"] is False
    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    row = cadence["results"][0]
    subtitle = row["subtitle"]
    assert subtitle["attempted"] is True
    assert subtitle["success"] is True
    assert subtitle["acquisition_mode"] == "browser_observed_only"
    assert subtitle["subtitle_url_sha256"]
    assert subtitle["subtitle_url_length"] == len(subtitle_url)
    assert subtitle["parsed_webvtt"]["cue_count"] == 2
    assert subtitle["parsed_webvtt"]["transcript_text"] == (
        "This fragrance is everywhere\nBronze shimmer test"
    )
    assert cadence["capture_contract"]["raw_subtitle_urls_persisted"] is False
    assert (
        cadence["capture_contract"]["video_navigation_mode"]
        == "direct_selected_url_sequence"
    )
    assert cadence["capture_contract"]["video_page_reuse_policy"] == (
        "capture_engine_defined"
    )
    assert cadence["capture_contract"]["terminal_page_policy"] == (
        "capture_engine_defined"
    )
    assert cadence["capture_contract"]["pointer_movement_policy"] == (
        "meaningful_page_actions_only"
    )
    assert cadence["capture_contract"]["address_bar_simulation"] is False
    assert cadence["capture_contract"]["referrer_spoofing"] is False
    assert cadence["capture_contract"]["return_to_grid_between_videos"] is False
    assert cadence["capture_contract"]["account_safety_pre_action_circuit_breaker"] is False
    assert cadence["capture_contract"]["account_safety_automatic_retry"] is False
    assert cadence["capture_contract"]["cleared_human_captcha_continues_batch"] is True
    assert cadence["capture_contract"]["raw_subtitle_bodies_persisted"] is False
    assert cadence["capture_contract"]["subtitle_tier"] == (
        "source_native_webvtt_transcript_browser_observed_v1"
    )

    code, message = write_tiktok_batch_packet(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        batch_label="fake-live-probe",
        decision_question="offline fake-engine subtitle transcript compatibility",
        grid_result_json=paths.grid_result_json_path.read_bytes(),
        cadence_result_jsons=[paths.cadence_result_json_path.read_bytes()],
        output_directory=tmp_path / "packet",
        source_file_receipts=[],
    )
    assert code == 0
    packet_payload = json.loads(
        (Path(message) / "raw" / "01_tiktok_batch_capture.json").read_text(encoding="utf-8")
    )
    subtitles = packet_payload["videos"][0]["subtitles"]
    assert subtitles["posture"] == "source_native_webvtt_captured"
    assert subtitles["cue_count"] == 2
    assert subtitles["transcript_text"] == "This fragrance is everywhere\nBronze shimmer test"
    assert subtitle_url not in json.dumps(packet_payload)


@pytest.mark.parametrize(
    ("mode", "expected_reason"),
    [
        ("missing", "subtitle_body_not_observed_in_browser_v1"),
        ("mismatched", "subtitle_body_not_observed_in_browser_v1"),
        ("failed", "subtitle_browser_response_not_successful_v1"),
        ("empty", "subtitle_body_not_available_from_browser_response_v1"),
        ("oversized", "subtitle_body_size_cap_exceeded_live_probe_v0"),
    ],
)
def test_live_probe_fails_visibly_without_an_exact_usable_browser_subtitle_response(
    tmp_path: Path,
    mode: str,
    expected_reason: str,
) -> None:
    auth_root = _auth_state(tmp_path)
    video_id = "7390000000000000001"
    subtitle_url = "https://v16-webapp.tiktok.com/subtitle.webvtt"
    responses = [_comment_response(video_id=video_id)]
    if mode == "mismatched":
        responses.append(
            _subtitle_response(
                url="https://v16-webapp.tiktok.com/other-subtitle.webvtt",
                body=b"WEBVTT\n",
            )
        )
    elif mode == "failed":
        responses.append(
            _subtitle_response(url=subtitle_url, body=b"", status=503)
        )
    elif mode == "empty":
        responses.append(_subtitle_response(url=subtitle_url, body=b""))
    elif mode == "oversized":
        responses.append(
            _subtitle_response(
                url=subtitle_url,
                body=b"x" * (live_batch_probe.TIKTOK_SUBTITLE_WEBVTT_MAX_BYTES + 1),
            )
        )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        auth_state_root=auth_root,
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id=video_id,
                    responses=responses,
                    subtitle_url=subtitle_url,
                )
            ]
        ),
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    subtitle = cadence["results"][0]["subtitle"]
    assert subtitle["attempted"] is True
    assert subtitle["success"] is False
    assert subtitle["acquisition_mode"] == "browser_observed_only"
    assert subtitle["reason"] == expected_reason
    assert subtitle_url not in json.dumps(cadence)


def test_capture_contract_reports_verified_session_engine_guarantees() -> None:
    contract = live_batch_probe._capture_contract(
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        session_engine_reused=True,
        account_safety_pre_action_circuit_breaker=True,
    )

    assert contract["video_page_reuse_policy"] == (
        "one_page_sequential_navigation"
    )
    assert contract["terminal_page_policy"] == "leave_last_selected_video_open"
    assert contract["account_safety_pre_action_circuit_breaker"] is True

    fallback = live_batch_probe._capture_contract(
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
    )
    assert fallback["video_page_reuse_policy"] == "capture_engine_defined"
    assert fallback["terminal_page_policy"] == "capture_engine_defined"
    assert fallback["account_safety_pre_action_circuit_breaker"] is False


def test_live_probe_rejects_unanchored_subtitle_host_without_fetch(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    video_id = "7390000000000000001"
    subtitle_url = "https://v16.attacker.example/subtitle.webvtt"
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id=video_id,
                response=_comment_response(video_id=video_id),
                subtitle_url=subtitle_url,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    subtitle = cadence["results"][0]["subtitle"]
    assert subtitle["attempted"] is False
    assert subtitle["success"] is False
    assert subtitle["reason"] == "unsupported_subtitle_url_host_live_probe_v0"
    assert subtitle["subtitle_url_host"] == "v16.attacker.example"
    assert subtitle["subtitle_url_host_supported"] is False
    assert subtitle["subtitle_url_sha256"]
    assert subtitle["subtitle_url_length"] == len(subtitle_url)
    assert subtitle_url not in json.dumps(cadence)

def test_live_probe_logged_out_mode_uses_no_storage_state_and_admits(
    tmp_path: Path,
) -> None:
    video_id = "7390000000000000001"
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id=video_id,
                responses=[
                    _comment_response(video_id=video_id, cid="7291"),
                    _comment_response(video_id=video_id, cid="7292"),
                ],
            )
        ]
    )

    paths = _write_logged_out_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        engine=engine,
    )

    assert engine.calls[0]["storage_state_path"] is None
    grid = json.loads(paths.grid_result_json_path.read_text(encoding="utf-8"))
    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["completed_count"] == 1
    assert cadence["capture_contract"]["session_mode"] == TIKTOK_LOGGED_OUT_SESSION_MODE
    assert cadence["capture_contract"]["logged_out_public"] is True
    row = cadence["results"][0]
    assert row["capture_receipt"]["matched_comment_response_count"] == 2
    assert row["capture_receipt"]["admitted_comment_response_count"] == 1
    assert row["capture_receipt"]["comment_response_cap"] == 1
    assert len(row["comment_responses"]) == 1
    assert grid["capture_contract"]["logged_out_public"] is True

    code, message = write_tiktok_batch_packet(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        batch_label="fake-logged-out-probe",
        decision_question="offline fake-engine logged-out admission compatibility",
        grid_result_json=paths.grid_result_json_path.read_bytes(),
        cadence_result_jsons=[paths.cadence_result_json_path.read_bytes()],
        output_directory=tmp_path / "packet",
        source_file_receipts=[],
    )
    assert code == 0
    packet_payload = json.loads(
        (Path(message) / "raw" / "01_tiktok_batch_capture.json").read_text(encoding="utf-8")
    )
    assert packet_payload["batch_summary"]["captured_comment_count"] == 1


def test_live_probe_runner_rejects_logged_out_with_session_args(tmp_path: Path) -> None:
    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--logged-out",
                "--state-label",
                "test-session",
                "--session-mode",
                AuthenticatedSessionMode.FREE_ACCOUNT_CREATED.value,
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("logged-out mode accepted sessioned auth arguments")


def test_live_probe_runner_can_chain_batch_admission_to_data_root(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    video_id = "7390000000000000001"
    pre_paths = _write_logged_out_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        output_dir=tmp_path / "pre_staging",
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id=video_id,
                    response=_comment_response(video_id=video_id),
                )
            ]
        ),
    )
    captured_kwargs: dict[str, object] = {}

    def fake_write_tiktok_live_batch_probe_outputs(**kwargs: object):
        captured_kwargs.update(kwargs)
        return pre_paths

    monkeypatch.setattr(
        runner,
        "write_tiktok_live_batch_probe_outputs",
        fake_write_tiktok_live_batch_probe_outputs,
    )
    root = DataLakeRoot.for_test(tmp_path / "lake")

    def fake_resolve(
        cls,
        *,
        explicit=None,
        env=None,
        config_path=None,
        expected_uuid=None,
        repo_root=None,
    ):
        assert explicit == str(root.path)
        return root

    monkeypatch.setattr(DataLakeRoot, "resolve", classmethod(fake_resolve))

    code = runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            f"https://www.tiktok.com/@funmi/video/{video_id}",
            "--logged-out",
            "--output-dir",
            str(tmp_path / "unused_staging"),
            "--data-root",
            str(root.path),
            "--batch-label",
            "live-chain-test",
            "--decision-question",
            "live runner admission chain",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    summaries = _summary_payloads(captured.out)
    assert [summary["stage"] for summary in summaries] == ["staging", "admission"]
    assert summaries[0]["admission_target"] == "bronze_data_root"
    assert summaries[0]["outcome"] == "staging_complete"
    assert summaries[0]["admitted_comment_response_count"] == 1
    assert summaries[1]["admission_target"] == "bronze_data_root"
    assert summaries[1]["outcome"] == "bronze_packet_admitted"
    assert summaries[1]["packet_path_printed"] is True
    assert COMPLETE_LANE_NOTE in captured.out
    packet_line = next(
        line for line in captured.out.splitlines() if line.startswith("admitted_packet=")
    )
    packet_dir = Path(packet_line.split("=", 1)[1])
    assert packet_dir.parent == root.path / "raw" / raw_shard(packet_dir.name)
    assert root.find_packet(packet_dir.name) is not None
    packet_payload = json.loads(
        (packet_dir / "raw" / "01_tiktok_batch_capture.json").read_text(
            encoding="utf-8"
        )
    )
    assert packet_payload["batch_summary"]["captured_comment_count"] == 1
    assert packet_payload["source_file_receipts"][0]["file_name"] == (
        "tiktok_live_grid_result.json"
    )
    assert packet_payload["source_file_receipts"][1]["file_name"] == (
        "tiktok_live_cadence_result.json"
    )
    assert captured_kwargs["logged_out"] is True


def test_live_probe_runner_can_chain_batch_admission_to_admit_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    video_id = "7390000000000000001"
    pre_paths = _write_logged_out_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        output_dir=tmp_path / "pre_staging_admit",
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id=video_id,
                    response=_comment_response(video_id=video_id),
                )
            ]
        ),
    )

    def fake_write_tiktok_live_batch_probe_outputs(**_kwargs: object):
        return pre_paths

    monkeypatch.setattr(
        runner,
        "write_tiktok_live_batch_probe_outputs",
        fake_write_tiktok_live_batch_probe_outputs,
    )
    admit_output = tmp_path / "packet"

    code = runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            f"https://www.tiktok.com/@funmi/video/{video_id}",
            "--logged-out",
            "--output-dir",
            str(tmp_path / "unused_staging_admit"),
            "--admit-output",
            str(admit_output),
            "--batch-label",
            "live-chain-admit-output-test",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    summaries = _summary_payloads(captured.out)
    assert [summary["stage"] for summary in summaries] == ["staging", "admission"]
    assert summaries[0]["admission_target"] == "local_admit_output"
    assert summaries[0]["outcome"] == "staging_complete"
    assert summaries[0]["browser_backend"] == "cloakbrowser"
    assert summaries[1]["admission_target"] == "local_admit_output"
    assert summaries[1]["outcome"] == "local_packet_admitted"
    assert summaries[1]["packet_path_printed"] is True
    assert COMPLETE_LANE_NOTE in captured.out
    packet_line = next(
        line for line in captured.out.splitlines() if line.startswith("admitted_packet=")
    )
    assert Path(packet_line.split("=", 1)[1]) == admit_output.resolve()
    packet_payload = json.loads(
        (admit_output / "raw" / "01_tiktok_batch_capture.json").read_text(
            encoding="utf-8"
        )
    )
    assert packet_payload["batch_summary"]["captured_comment_count"] == 1
    assert packet_payload["source_file_receipts"][0]["file_name"] == (
        "tiktok_live_grid_result.json"
    )
    assert packet_payload["source_file_receipts"][1]["file_name"] == (
        "tiktok_live_cadence_result.json"
    )


def test_live_probe_runner_chain_rejects_failed_cadence_before_packet(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    video_id = "7390000000000000001"
    pre_paths = _write_logged_out_probe(
        tmp_path,
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        output_dir=tmp_path / "pre_staging_failed",
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id=video_id,
                    response=_comment_response(video_id=video_id),
                )
            ]
        ),
    )
    cadence = json.loads(pre_paths.cadence_result_json_path.read_text(encoding="utf-8"))
    cadence["challenge_count"] = 1
    pre_paths.cadence_result_json_path.write_text(
        json.dumps(cadence),
        encoding="utf-8",
    )

    def fake_write_tiktok_live_batch_probe_outputs(**_kwargs: object):
        return pre_paths

    monkeypatch.setattr(
        runner,
        "write_tiktok_live_batch_probe_outputs",
        fake_write_tiktok_live_batch_probe_outputs,
    )
    admit_output = tmp_path / "packet"

    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                f"https://www.tiktok.com/@funmi/video/{video_id}",
                "--logged-out",
                "--output-dir",
                str(tmp_path / "unused_staging"),
                "--admit-output",
                str(admit_output),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("failed cadence was admitted by the live runner chain")
    assert not admit_output.exists()
    captured = capsys.readouterr()
    summaries = _summary_payloads(captured.out)
    assert [summary["stage"] for summary in summaries] == ["staging", "admission"]
    assert summaries[0]["outcome"] == "fail_closed_staging_has_failures"
    assert summaries[0]["challenge_count"] == 1
    assert summaries[1]["outcome"] == "fail_closed_admission_rejected"
    assert summaries[1]["fail_closed"] is True


def test_live_probe_runner_rejects_diagnostic_and_followthrough_together(tmp_path: Path) -> None:
    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--logged-out",
                "--allow-challenge-close-diagnostic",
                "--allow-challenge-close-followthrough",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("diagnostic and followthrough modes were accepted together")


def test_live_probe_threads_cloakbrowser_and_human_handoff_options(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_fetch_browser_page_observation_capture(**kwargs: object) -> BrowserPageObservationSuccess:
        captured_kwargs.update(kwargs)
        return _success_observation(
            video_id="7390000000000000001",
            response=_comment_response(video_id="7390000000000000001"),
            subtitle_url="https://v16.tiktokcdn.com/subtitle.webvtt",
        )

    monkeypatch.setattr(
        live_batch_probe,
        "fetch_browser_page_observation_capture",
        fake_fetch_browser_page_observation_capture,
    )

    # Not converted to _write_logged_out_probe: this success path omits the
    # cadence/random_seed kwargs the wrapper binds, and those defaults are
    # recorded in the written cadence result.
    paths = write_tiktok_live_batch_probe_outputs(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        logged_out=True,
        output_dir=tmp_path / "out",
        browser_backend="cloakbrowser",
        cloakbrowser_humanize=True,
        human_challenge_handoff=True,
        human_challenge_handoff_timeout_seconds=7.0,
        allow_challenge_close_followthrough=True,
        sleep_fn=lambda _seconds: None,
    )

    assert captured_kwargs["browser_backend"] == "cloakbrowser"
    assert captured_kwargs["cloakbrowser_humanize"] is True
    assert captured_kwargs["human_challenge_handoff_markers"] == (
        "drag the slider",
        "verify to continue",
        "captcha",
        "security check",
    )
    assert captured_kwargs["human_challenge_handoff_after_action_names"] == (
        PAGE_LOAD_BEFORE_POINTER_ACTIONS_HANDOFF_NAME,
        TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
        TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
        TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
        TIKTOK_OPEN_MORE_LIKE_THIS_POINTER_ACTION_NAME,
        TIKTOK_REOPEN_COMMENTS_POINTER_ACTION_NAME,
    )
    assert captured_kwargs["human_challenge_handoff_timeout_seconds"] == 7.0

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    contract = cadence["capture_contract"]
    assert contract["browser_backend"] == "cloakbrowser"
    assert contract["cloakbrowser_humanize"] is True
    assert contract["human_challenge_handoff_allowed"] is True
    assert contract["human_challenge_handoff_counts_as_clean_capture"] is False
    assert contract["challenge_close_followthrough_allowed"] is True



def test_live_probe_runner_required_proxy_posture_choices_exclude_unknown() -> None:
    parser = runner.build_parser()
    action = next(
        item for item in parser._actions if item.dest == "require_harness_proxy_posture"
    )
    assert action.choices == ["no_proxy_profile_loaded", "proxy_profile_loaded"]


def test_live_probe_runner_admission_targets_stay_mutually_exclusive() -> None:
    parser = runner.build_parser()
    mutually_exclusive_option_sets = [
        {
            option
            for action in group._group_actions
            for option in action.option_strings
        }
        for group in parser._mutually_exclusive_groups
    ]

    assert any(
        {"--admit-output", "--data-root"} <= options
        for options in mutually_exclusive_option_sets
    ), (
        "--admit-output and --data-root must remain in one argparse "
        "mutually-exclusive group"
    )


def test_live_probe_runner_defaults_to_cloakbrowser_packet_grade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Not converted to _write_logged_out_probe: this success path omits the
    # cadence/random_seed kwargs the wrapper binds, and those defaults are
    # recorded in the written cadence result.
    pre_paths = write_tiktok_live_batch_probe_outputs(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        logged_out=True,
        output_dir=tmp_path / "pre",
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id="7390000000000000001",
                    response=_comment_response(video_id="7390000000000000001"),
                    subtitle_url="https://v16.tiktokcdn.com/subtitle.webvtt",
                )
            ]
        ),
        sleep_fn=lambda _seconds: None,
    )
    captured_kwargs: dict[str, object] = {}

    def fake_write_tiktok_live_batch_probe_outputs(**kwargs: object):
        captured_kwargs.update(kwargs)
        return pre_paths

    monkeypatch.setattr(
        runner,
        "write_tiktok_live_batch_probe_outputs",
        fake_write_tiktok_live_batch_probe_outputs,
    )

    code = runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "--logged-out",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    assert captured_kwargs["browser_backend"] == "cloakbrowser"
    assert captured_kwargs["cloakbrowser_humanize"] is True


def test_live_probe_runner_rejects_playwright_without_diagnostic_opt_in(
    tmp_path: Path,
) -> None:
    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--logged-out",
                "--browser-backend",
                "playwright",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("playwright backend was accepted without diagnostic opt-in")


def test_live_probe_runner_allows_playwright_with_diagnostic_opt_in(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Not converted to _write_logged_out_probe: this success path omits the
    # cadence/random_seed kwargs the wrapper binds, and those defaults are
    # recorded in the written cadence result.
    pre_paths = write_tiktok_live_batch_probe_outputs(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        logged_out=True,
        output_dir=tmp_path / "pre",
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id="7390000000000000001",
                    response=_comment_response(video_id="7390000000000000001"),
                    subtitle_url="https://v16.tiktokcdn.com/subtitle.webvtt",
                )
            ]
        ),
        sleep_fn=lambda _seconds: None,
    )
    captured_kwargs: dict[str, object] = {}

    def fake_write_tiktok_live_batch_probe_outputs(**kwargs: object):
        captured_kwargs.update(kwargs)
        return pre_paths

    monkeypatch.setattr(
        runner,
        "write_tiktok_live_batch_probe_outputs",
        fake_write_tiktok_live_batch_probe_outputs,
    )

    code = runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "--logged-out",
            "--browser-backend",
            "playwright",
            "--allow-diagnostic-browser-backend",
            "--browser-channel",
            "chrome",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    assert captured_kwargs["browser_backend"] == "playwright"
    assert captured_kwargs["browser_channel"] == "chrome"
    assert captured_kwargs["cloakbrowser_humanize"] is False


def test_live_probe_runner_allows_pre_action_handoff_without_followthrough(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    class _Paths:
        grid_result_json_path = tmp_path / "grid.json"
        cadence_result_json_path = tmp_path / "cadence.json"

    def fake_write(**kwargs: object) -> _Paths:
        captured_kwargs.update(kwargs)
        return _Paths()

    monkeypatch.setattr(runner, "write_tiktok_live_batch_probe_outputs", fake_write)
    monkeypatch.setattr(
        runner,
        "_staging_summary",
        lambda **_kwargs: {"schema_version": "test", "stage": "staging"},
    )

    code = runner.main(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "--logged-out",
            "--human-challenge-handoff",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    assert captured_kwargs["human_challenge_handoff"] is True
    assert captured_kwargs["allow_challenge_close_followthrough"] is False


def test_live_probe_runner_rejects_cloakbrowser_with_browser_channel(tmp_path: Path) -> None:
    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--logged-out",
                "--browser-backend",
                "cloakbrowser",
                "--browser-channel",
                "chrome",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("cloakbrowser backend accepted browser-channel")


def test_live_probe_runner_rejects_cloakbrowser_humanize_with_playwright_backend(
    tmp_path: Path,
) -> None:
    try:
        runner.main(
            [
                "--creator-handle",
                "funmi",
                "--creator-profile-url",
                "https://www.tiktok.com/@funmi",
                "--video-url",
                "https://www.tiktok.com/@funmi/video/7390000000000000001",
                "--logged-out",
                "--browser-backend",
                "playwright",
                "--allow-diagnostic-browser-backend",
                "--cloakbrowser-humanize",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("cloakbrowser humanize was accepted with playwright backend")


def test_live_probe_rejects_cloakbrowser_humanize_without_cloakbrowser_backend(
    tmp_path: Path,
) -> None:
    try:
        # Wrapper-bound cadence gaps and random_seed are inert here: the call
        # rejects the humanize/backend mix before the cadence plan is built.
        _write_logged_out_probe(
            tmp_path,
            video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
            browser_backend="playwright",
            cloakbrowser_humanize=True,
        )
    except ValueError as exc:
        assert "cloakbrowser_humanize requires browser_backend='cloakbrowser'" in str(exc)
    else:
        raise AssertionError("cloakbrowser humanize was accepted without cloakbrowser backend")



def test_live_probe_required_harness_proxy_posture_rejects_legacy_auth_state_before_browser(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(outcomes=[])

    try:
        # Wrapper-bound cadence gaps and random_seed are inert here: the call
        # rejects on auth-state provenance before the cadence plan is built.
        _write_sessioned_probe(
            tmp_path,
            video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
            auth_state_root=auth_root,
            required_harness_proxy_profile_posture="no_proxy_profile_loaded",
            engine=engine,
        )
    except ValueError as exc:
        assert "source-access provenance is missing or legacy-only" in str(exc)
    else:
        raise AssertionError("legacy auth-state satisfied required provenance")

    assert engine.calls == []


def test_live_probe_required_harness_proxy_posture_allows_matching_auth_state_provenance(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state_with_provenance(
        tmp_path,
        harness_proxy_profile_posture="no_proxy_profile_loaded",
        proxy_category="none",
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                subtitle_url="https://v16.tiktokcdn.com/subtitle.webvtt",
            )
        ]
    )

    # Not converted to _write_sessioned_probe: this success path omits the
    # cadence/random_seed kwargs the wrapper binds, and those defaults are
    # recorded in the written cadence result.
    paths = write_tiktok_live_batch_probe_outputs(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        state_label="test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        auth_state_root=auth_root,
        output_dir=tmp_path / "out",
        required_harness_proxy_profile_posture="no_proxy_profile_loaded",
        engine=engine,
        sleep_fn=lambda _seconds: None,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert engine.calls[0]["storage_state_path"] == auth_root / "test-session.json"
    assert (
        cadence["capture_contract"]["required_harness_proxy_profile_posture"]
        == "no_proxy_profile_loaded"
    )


def test_live_probe_required_harness_proxy_posture_rejects_mismatched_posture_before_browser(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state_with_provenance(
        tmp_path,
        harness_proxy_profile_posture="proxy_profile_loaded",
        proxy_category="residential_rotating",
    )
    engine = _FakeObservationEngine(outcomes=[])

    try:
        # Wrapper-bound cadence gaps and random_seed are inert here: the call
        # rejects on proxy-posture mismatch before the cadence plan is built.
        _write_sessioned_probe(
            tmp_path,
            video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
            auth_state_root=auth_root,
            required_harness_proxy_profile_posture="no_proxy_profile_loaded",
            engine=engine,
        )
    except ValueError as exc:
        assert "harness proxy-profile posture mismatch" in str(exc)
    else:
        raise AssertionError("mismatched proxy posture satisfied required provenance")

    assert engine.calls == []


def test_live_probe_filters_non_get_comment_list_responses_when_method_available(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    response_url = (
        "https://www.tiktok.com/api/comment/list/"
        "?aweme_id=7390000000000000001&cursor=0&count=20"
    )
    get_body = json.dumps(
        {
            "cursor": 20,
            "has_more": 0,
            "total": 1,
            "comments": [
                {
                    "cid": "7291",
                    "text": "Real body",
                    "create_time": 1710000000,
                    "user": {"uid": "u1", "unique_id": "viewer_one"},
                }
            ],
        }
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                responses=[
                    BrowserPageResponse(
                        requested_url=response_url,
                        final_url=response_url,
                        status=200,
                        ok=True,
                        body_text="",
                        response_headers={"content-type": "application/json"},
                        request_method="OPTIONS",
                        resource_type="fetch",
                    ),
                    BrowserPageResponse(
                        requested_url=response_url,
                        final_url=response_url,
                        status=200,
                        ok=True,
                        body_text=get_body,
                        response_headers={"content-type": "application/json"},
                        request_method="GET",
                        resource_type="fetch",
                    ),
                ],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    row = cadence["results"][0]
    assert row["capture_receipt"]["response_count"] == 2
    assert row["capture_receipt"]["matched_comment_response_count"] == 1
    assert row["capture_receipt"]["admitted_comment_response_count"] == 1
    assert len(row["comment_responses"]) == 1
    assert row["comment_responses"][0]["request_method"] == "GET"
    assert row["comment_responses"][0]["body_assessment"]["json_parse_ok"] is True
    assert row["comment_responses"][0]["body_assessment"]["comment_count"] == 1

def test_live_probe_keeps_only_platform_default_first_comment_response(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    response_url = (
        "https://www.tiktok.com/api/comment/list/"
        "?aweme_id=7390000000000000001&cursor=0&count=20"
    )
    responses = [
        BrowserPageResponse(
            requested_url=response_url,
            final_url=response_url,
            status=200,
            ok=True,
            body_text=json.dumps(
                {
                    "cursor": index * 20,
                    "has_more": 1,
                    "total": 3,
                    "comments": [
                        {
                            "cid": f"729{index}",
                            "text": f"Body {index}",
                            "create_time": 1710000000 + index,
                            "user": {"uid": f"u{index}", "unique_id": f"viewer_{index}"},
                        }
                    ],
                }
            ),
            response_headers={"content-type": "application/json"},
            request_method="GET",
            resource_type="fetch",
        )
        for index in range(3)
    ]
    engine = _FakeObservationEngine(
        outcomes=[_success_observation(video_id="7390000000000000001", responses=responses)]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    row = cadence["results"][0]
    assert (
        cadence["capture_contract"]["comment_selection_policy"]
        == "platform_default_first_response_only"
    )
    assert cadence["capture_contract"]["comment_pagination"] is False
    assert row["capture_receipt"]["response_count"] == 3
    assert row["capture_receipt"]["matched_comment_response_count"] == 3
    assert row["capture_receipt"]["admitted_comment_response_count"] == 1
    assert row["capture_receipt"]["comment_response_cap"] == 1
    assert (
        row["capture_receipt"]["comment_selection_policy"]
        == "platform_default_first_response_only"
    )
    assert len(row["comment_responses"]) == 1
    assert [
        response["body_assessment"]["comments"][0]["cid"]
        for response in row["comment_responses"]
    ] == ["7290"]



def test_live_probe_challenge_close_diagnostic_flag_prepends_close_action(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_diagnostic=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    pointer_actions = engine.calls[0]["post_load_pointer_actions"]
    assert [action.action_name for action in pointer_actions] == [
        TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
        TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
        TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
        *_comment_route_with_diagnostic_action_names(),
    ]
    close_action = pointer_actions[2]
    assert close_action.page_text_markers == (
        "drag the slider",
        "verify to continue",
        "captcha",
        "security check",
    )
    assert close_action.exact_text_markers == ("x", "×")
    assert close_action.prefer_top_right is True
    assert close_action.visual_top_right_x_fallback is True
    visual_close_action = pointer_actions[-1]
    assert visual_close_action.action_name == (
        TIKTOK_CHALLENGE_VISUAL_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME
    )
    assert visual_close_action.page_text_markers == (
        "drag the slider",
        "verify to continue",
        "captcha",
        "security check",
    )
    assert visual_close_action.visual_top_right_x_fallback is True
    assert cadence["capture_contract"]["challenge_close_diagnostic_allowed"] is True
    assert cadence["capture_contract"]["challenge_close_counts_as_success"] is False
    assert cadence["completed_count"] == 1
    receipt = cadence["results"][0]["capture_receipt"]
    assert receipt["benign_overlay_action"]["action_name"] == (
        TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME
    )
    assert receipt["comment_action"]["action_count"] == len(_pointer_action_sequence_receipt())


def test_live_probe_challenge_close_followthrough_admits_post_close_comments(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right_visual_x",
    )
    followthrough_close_receipt.update(
        {
            "target_kind": "visual_x",
            "visual_fallback_attempted": True,
            "visual_fallback_target_found": True,
            "visual_fallback_candidate_count": 1,
            "visual_fallback_confidence": 0.812,
            "visual_fallback_screenshot_sha256": "b" * 64,
            "visual_fallback_crop_box": {"x": 576, "y": 0, "width": 704, "height": 324},
            "target_box": {"x": 796.0, "y": 190.0, "width": 16.0, "height": 16.0},
            "click_point": {"x": 803.3, "y": 197.4},
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": True,
            "post_click_visual_candidate_count": 0,
            "post_click_visual_screenshot_sha256": "c" * 64,
        }
    )
    visual_followthrough_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right_visual_x",
    )
    visual_followthrough_receipt.update(
        {
            "candidate_count": 0,
            "matched_count": 0,
            "target_found": False,
            "clicked": False,
            "move_steps": None,
            "target_kind": "visual_x",
            "visual_fallback_attempted": True,
            "visual_fallback_target_found": False,
            "visual_fallback_candidate_count": 0,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        followthrough_close_receipt,
        visual_followthrough_receipt,
        *_pointer_action_sequence_receipt(),
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    pointer_actions = engine.calls[0]["post_load_pointer_actions"]
    assert [action.action_name for action in pointer_actions] == [
        TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
        TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
        TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        *_comment_route_with_followthrough_action_names(),
    ]
    assert pointer_actions[2].page_text_markers == (
        "drag the slider",
        "verify to continue",
        "captcha",
        "security check",
    )
    assert pointer_actions[3].page_text_markers == (
        "drag the slider",
        "verify to continue",
        "captcha",
        "security check",
    )
    assert pointer_actions[3].visual_top_right_x_fallback is True
    assert pointer_actions[3].stop_sequence_on_failed_post_click_verification is True
    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 1
    assert cadence["challenge_count"] == 0
    assert cadence["challenge_close_followthrough_count"] == 1
    assert cadence["capture_contract"]["challenge_close_diagnostic_allowed"] is False
    assert cadence["capture_contract"]["challenge_close_followthrough_allowed"] is True
    row = cadence["results"][0]
    receipt = row["capture_receipt"]
    assert receipt["challenge_close_followthrough"] is True
    assert receipt["challenge_close_accepted"] is True
    assert receipt["challenge_close_action"]["action_name"] == (
        TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME
    )
    assert receipt["challenge_close_action"]["target_box"]["x"] == 796.0
    assert receipt["challenge_close_action"]["click_point"] == {"x": 803.3, "y": 197.4}
    assert [
        action["action_name"] for action in receipt["pointer_action_chronology"]
    ] == [action["action_name"] for action in pointer_sequence]
    assert [
        action["action_name"] for action in receipt["challenge_close_attempts"]
    ] == [
        TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
    ]
    assert receipt["admitted_comment_response_count"] == 1
    assert len(row["comment_responses"]) == 1

    code, message = write_tiktok_batch_packet(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        batch_label="fake-followthrough-probe",
        decision_question="offline fake-engine followthrough admission compatibility",
        grid_result_json=paths.grid_result_json_path.read_bytes(),
        cadence_result_jsons=[paths.cadence_result_json_path.read_bytes()],
        output_directory=tmp_path / "packet",
        source_file_receipts=[],
    )
    assert code == 0
    packet_payload = json.loads(
        (Path(message) / "raw" / "01_tiktok_batch_capture.json").read_text(encoding="utf-8")
    )
    assert packet_payload["batch_summary"]["challenge_close_followthrough_video_count"] == 1
    intervention = packet_payload["videos"][0]["source_access_intervention"]
    assert intervention["posture"] == "owner_authorized_challenge_x_close_followthrough"
    assert intervention["followthrough"] is True
    assert intervention["accepted"] is True
    assert intervention["clicked"] is True
    assert intervention["post_click_absence_verified"] is True
    assert intervention["post_click_visual_target_absent"] is True


def test_live_probe_prefers_late_accepted_close_over_earlier_failed_click(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    failed_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right",
    )
    failed_close_receipt.update(
        {
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": False,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": True,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 2,
        }
    )
    late_visual_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
    )
    late_visual_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": True,
            "post_click_visual_candidate_count": 0,
        }
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=[
                    _benign_overlay_action_receipt(),
                    failed_close_receipt,
                    *_pointer_action_sequence_receipt(),
                    late_visual_close_receipt,
                ],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    receipt = cadence["results"][0]["capture_receipt"]
    assert receipt["challenge_close_accepted"] is True
    assert receipt["challenge_close_action"]["action_name"] == (
        TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME
    )
    assert receipt["challenge_close_action"]["selection_strategy"] == "center_modal_visual_x"
    assert receipt["admitted_comment_response_count"] == 1

def test_live_probe_prefers_late_failed_close_over_earlier_failed_click(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    early_failed_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right",
        page_text_gate_matched=True,
        page_text_matched_marker="drag the slider",
    )
    early_failed_close_receipt.update(
        {
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": True,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 3,
        }
    )
    late_failed_visual_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
        page_text_gate_matched=True,
        page_text_matched_marker="drag the slider",
    )
    late_failed_visual_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 22,
            "post_click_visual_zone_candidate_count": 0,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        early_failed_close_receipt,
        *_pointer_action_sequence_receipt(),
        late_failed_visual_close_receipt,
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["completed_count"] == 0
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON
    close_action = failure["blocker_triage"]["challenge_close_action"]
    assert close_action["action_name"] == (
        TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME
    )
    assert close_action["post_click_visual_candidate_count"] == 22
    assert close_action["post_click_visual_zone_candidate_count"] == 0

def test_live_probe_challenge_close_followthrough_stops_if_close_not_accepted(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
        page_text_gate_matched=True,
        page_text_matched_marker="drag the slider",
    )
    followthrough_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 4,
            "post_click_visual_screenshot_sha256": "d" * 64,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        followthrough_close_receipt,
        *_pointer_action_sequence_receipt(),
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    assert cadence["challenge_close_followthrough_count"] == 0
    assert cadence["results"] == []
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON
    triage = failure["blocker_triage"]
    assert triage["challenge_close_action"]["clicked"] is True
    assert triage["challenge_close_action"]["post_click_absence_verified"] is True
    assert triage["challenge_close_action"]["post_click_visual_candidate_count"] == 4
    assert triage["challenge_close_action"]["post_click_visual_target_absent"] is False
    assert triage["challenge_close_accepted"] is False
    assert triage["matched_marker"] == "drag the slider"
    assert triage["challenge_kind"] == "slider"
    assert triage["owner_attention_required"] is True
    assert triage["manual_challenge_attention_required"] is True
    assert (
        triage["owner_attention_reason"]
        == TIKTOK_MANUAL_CHALLENGE_ATTENTION_REQUIRED_REASON
    )
    assert triage["owner_attention_route"] == "fail_closed_no_handoff_prompt"
    assert triage["agent_may_solve_challenge"] is False
    assert triage["owner_attention_counts_as_clean_capture"] is False
    assert triage["matched_comment_response_count"] == 1
    assert triage["admitted_comment_response_count"] == 0
    assert triage["dom_visible_comment_candidate_count"] == 0
    assert [
        action["action_name"] for action in triage["pointer_action_chronology"]
    ] == [action["action_name"] for action in pointer_sequence]
    assert [
        action["action_name"] for action in triage["challenge_close_attempts"]
    ] == [TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME]


def test_live_probe_close_not_accepted_reports_handoff_prompt_route_when_enabled(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
        page_text_gate_matched=True,
        page_text_matched_marker="drag the slider",
    )
    followthrough_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 4,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        followthrough_close_receipt,
        *_pointer_action_sequence_receipt(),
    ]
    handoff_attempt = {
        "action_name": "human_challenge_handoff_v0",
        "action_mode": "source_access_intervention",
        "action_taken": True,
        "captcha_solving_by_agent": False,
        "prompted": True,
        "prompt_surface": "test_prompt",
        "matched_marker": "drag the slider",
        "cleared": False,
    }
    engine = _FakeObservationEngine(
        outcomes=[
            BrowserPageObservationSuccess(
                requested_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                final_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                title="TikTok",
                visible_text="video loaded",
                dom_observation={
                    "hydration_json_text": json.dumps(_hydration("7390000000000000001"))
                },
                responses=[_comment_response(video_id="7390000000000000001")],
                metadata={
                    "post_load_pointer_action": pointer_sequence[-1],
                    "post_load_pointer_actions": pointer_sequence,
                    "human_challenge_handoff_attempts": [handoff_attempt],
                },
                warning_notes=[],
                limitation_notes=[],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        human_challenge_handoff=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["completed_count"] == 0
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON
    triage = failure["blocker_triage"]
    assert triage["challenge_close_accepted"] is False
    assert triage["owner_attention_required"] is True
    assert triage["manual_challenge_attention_required"] is True
    assert (
        triage["owner_attention_reason"]
        == TIKTOK_MANUAL_CHALLENGE_ATTENTION_REQUIRED_REASON
    )
    # Handoff enabled and attempted must route to the prompt path, not the
    # fail-closed-no-handoff path, while still refusing to count as clean capture.
    assert triage["owner_attention_route"] == "harness_human_challenge_handoff_prompt"
    assert triage["human_challenge_handoff_enabled"] is True
    assert triage["human_challenge_handoff_attempted"] is True
    assert triage["agent_may_solve_challenge"] is False
    assert triage["owner_attention_counts_as_clean_capture"] is False



def test_live_probe_counts_cleared_handoff_and_continues_batch(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    first = _success_observation(
        video_id="7390000000000000001",
        response=_comment_response(video_id="7390000000000000001"),
    )
    first.metadata["human_challenge_handoff_attempts"] = [
        {
            "action_name": "human_challenge_handoff_v0",
            "action_mode": "source_access_intervention",
            "action_taken": True,
            "captcha_solving_by_agent": False,
            "prompted": True,
            "prompt_surface": "test_prompt",
            "matched_marker": "drag the slider",
            "cleared": True,
        }
    ]
    second = _success_observation(
        video_id="7390000000000000002",
        response=_comment_response(video_id="7390000000000000002"),
    )
    engine = _FakeObservationEngine(outcomes=[first, second])

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        state_label="test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        auth_state_root=auth_root,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        human_challenge_handoff=True,
        engine=engine,
        sleep_fn=lambda _seconds: None,
    )

    cadence = result["cadence_result"]
    assert cadence["attempted_count"] == 2
    assert cadence["completed_count"] == 2
    assert cadence["challenge_count"] == 0
    assert cadence["human_challenge_handoff_count"] == 1
    assert cadence["cleared_human_challenge_handoff_count"] == 1

def test_live_probe_failed_close_receipt_surfaces_center_modal_zone_candidate_count(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
        page_text_gate_matched=True,
        page_text_matched_marker="drag the slider",
    )
    followthrough_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            # The center modal cleared (zone count 0) but stray top-right glyphs
            # keep the broad candidate count high.
            "post_click_visual_candidate_count": 22,
            "post_click_visual_zone_candidate_count": 0,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        followthrough_close_receipt,
        *_pointer_action_sequence_receipt(),
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON
    triage = failure["blocker_triage"]
    close_action = triage["challenge_close_action"]
    # The receipt now distinguishes stray-glyph residue from a persisting modal.
    assert close_action["post_click_visual_candidate_count"] == 22
    assert close_action["post_click_visual_zone_candidate_count"] == 0
    # Acceptance semantics are unchanged: the broad count still fails the close
    # closed, so the zero admission and stop hold.
    assert triage["challenge_close_accepted"] is False
    assert cadence["results"] == []


def test_live_probe_failed_close_without_comment_actions_has_no_comment_action_label(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="center_modal_visual_x",
    )
    followthrough_close_receipt.update(
        {
            "target_kind": "visual_x",
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 3,
        }
    )
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                pointer_sequence=[_benign_overlay_action_receipt(), followthrough_close_receipt],
                dom_comment_candidates=[],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_X_CLOSE_NOT_ACCEPTED_REASON
    triage = failure["blocker_triage"]
    assert triage["challenge_close_action"]["clicked"] is True
    assert triage["challenge_close_accepted"] is False
    assert triage["owner_attention_required"] is True
    assert triage["manual_challenge_attention_required"] is True
    assert triage["owner_attention_route"] == "fail_closed_no_handoff_prompt"
    assert "challenge_close_followthrough" not in triage
    assert "comment_action" not in triage
    assert triage["matched_comment_response_count"] == 0
    assert triage["admitted_comment_response_count"] == 0
    assert triage["dom_visible_comment_candidate_count"] == 0

def test_live_probe_challenge_close_followthrough_stops_if_challenge_remains(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    followthrough_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right_visual_x",
    )
    followthrough_close_receipt.update(
        {
            "post_click_absence_checked": True,
            "post_click_absence_marker_count": 4,
            "post_click_absence_verified": True,
            "post_click_visual_check_attempted": True,
            "post_click_visual_target_found": False,
            "post_click_visual_target_absent": False,
            "post_click_visual_candidate_count": 4,
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        followthrough_close_receipt,
        *_pointer_action_sequence_receipt(),
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
                visible_text="Drag the slider to fit the puzzle",
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_followthrough=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    assert cadence["results"] == []
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_AFTER_CLOSE_FOLLOWTHROUGH_REASON
    triage = failure["blocker_triage"]
    assert triage["challenge_close_action"]["action_name"] == (
        TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME
    )
    assert "challenge_close_followthrough" not in triage
    assert triage["challenge_close_accepted"] is False
    assert triage["owner_attention_required"] is True
    assert triage["manual_challenge_attention_required"] is True
    assert triage["owner_attention_route"] == "fail_closed_no_handoff_prompt"
    assert triage["comment_action"]["action_count"] == len(_pointer_action_sequence_receipt())
    assert triage["matched_comment_response_count"] == 1
    assert triage["admitted_comment_response_count"] == 0
    assert triage["dom_visible_comment_candidate_count"] == 0
    assert "challenge_close_diagnostic" not in triage


def test_live_probe_challenge_close_diagnostic_is_not_completion(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    dom_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
        wait_ms=0,
        page_text_gate_matched=False,
        selection_strategy="top_right",
    )
    dom_close_receipt.update(
        {
            "candidate_count": 0,
            "matched_count": 0,
            "target_found": False,
            "clicked": False,
            "move_steps": None,
        }
    )
    visual_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right_visual_x",
    )
    visual_close_receipt.update(
        {
            "candidate_count": 0,
            "matched_count": 0,
            "target_kind": "visual_x",
            "visual_fallback_attempted": True,
            "visual_fallback_target_found": True,
            "visual_fallback_candidate_count": 1,
            "visual_fallback_confidence": 0.812,
            "visual_fallback_screenshot_sha256": "a" * 64,
            "visual_fallback_crop_box": {"x": 576, "y": 0, "width": 704, "height": 324},
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        dom_close_receipt,
        *_pointer_action_sequence_receipt(),
        visual_close_receipt,
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_diagnostic=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(cadence, sort_keys=True)
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    assert cadence["results"] == []
    assert "comment_responses" not in serialized
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_REASON
    triage = failure["blocker_triage"]
    assert triage["blocker_class"] == "challenge_close_diagnostic"
    assert triage["action"] == "stop"
    assert triage["action_taken"] is True
    assert triage["challenge_close_diagnostic"] == pointer_sequence[-1]
    assert triage["comment_action"]["action_count"] == len(_pointer_action_sequence_receipt())
    assert triage["matched_comment_response_count"] == 1
    assert triage["admitted_comment_response_count"] == 0
    assert triage["dom_visible_comment_candidate_count"] == 0


def test_live_probe_challenge_after_close_diagnostic_keeps_challenge_stop(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    dom_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
        wait_ms=0,
        page_text_gate_matched=False,
        selection_strategy="top_right",
    )
    dom_close_receipt.update(
        {
            "candidate_count": 0,
            "matched_count": 0,
            "target_found": False,
            "clicked": False,
            "move_steps": None,
        }
    )
    visual_close_receipt = _pointer_action_receipt(
        action_name=TIKTOK_CHALLENGE_VISUAL_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
        wait_ms=2000,
        selection_strategy="top_right_visual_x",
    )
    visual_close_receipt.update(
        {
            "candidate_count": 0,
            "matched_count": 0,
            "target_kind": "visual_x",
            "visual_fallback_attempted": True,
            "visual_fallback_target_found": True,
            "visual_fallback_candidate_count": 1,
            "visual_fallback_confidence": 0.812,
            "visual_fallback_screenshot_sha256": "a" * 64,
            "visual_fallback_crop_box": {"x": 576, "y": 0, "width": 704, "height": 324},
        }
    )
    pointer_sequence = [
        _benign_overlay_action_receipt(),
        dom_close_receipt,
        *_pointer_action_sequence_receipt(),
        visual_close_receipt,
    ]
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                response=_comment_response(video_id="7390000000000000001"),
                pointer_sequence=pointer_sequence,
                visible_text="Drag the slider.",
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        allow_challenge_close_diagnostic=True,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_CHALLENGE_AFTER_CLOSE_DIAGNOSTIC_REASON
    triage = failure["blocker_triage"]
    assert triage["reason"] == "platform_challenge_observed"
    assert triage["matched_marker"] == "drag the slider"
    assert triage["challenge_kind"] == "slider"
    assert triage["challenge_close_diagnostic"] == pointer_sequence[-1]
    assert triage["comment_action"]["action_count"] == len(_pointer_action_sequence_receipt())
    assert triage["matched_comment_response_count"] == 1
    assert triage["admitted_comment_response_count"] == 0
    assert triage["dom_visible_comment_candidate_count"] == 0



def test_live_probe_continues_after_zero_comment_list_response(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(video_id="7390000000000000001", responses=[]),
            _success_observation(
                video_id="7390000000000000002",
                response=_comment_response(video_id="7390000000000000002"),
            ),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 2
    assert cadence["completed_count"] == 1
    assert cadence["partial_count"] == 1
    assert cadence["challenge_count"] == 0
    assert [row["video_id"] for row in cadence["results"]] == [
        "7390000000000000001",
        "7390000000000000002",
    ]
    assert [row["status"] for row in cadence["results"]] == ["partial_failure", "completed"]
    assert cadence["failures"][0]["reason"] == TIKTOK_COMMENT_ROUTE_NO_RESPONSE_REASON
    assert cadence["failures"][0]["blocker_triage"] == {
        "blocker_class": "comment_route_zero_yield",
        "action": "continue",
        "reason": TIKTOK_COMMENT_ROUTE_NO_RESPONSE_REASON,
        "action_mode": "diagnosis_only",
        "action_taken": False,
        "benign_overlay_action": _benign_overlay_action_receipt(),
        "comment_action": {
            "sequence_name": TIKTOK_COMMENT_SURFACE_TOGGLE_POINTER_SEQUENCE_NAME,
            "action_count": len(_pointer_action_sequence_receipt()),
            "action_sequence": _pointer_action_sequence_receipt(),
            "clicked_all_targets": True,
        },
        "response_count": 0,
        "matched_comment_response_count": 0,
        "admitted_comment_response_count": 0,
        "dom_visible_comment_candidate_count": 0,
    }
    assert len(engine.calls) == 2


def test_live_probe_zero_comment_response_reports_missing_comment_route_actions(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                responses=[],
                pointer_sequence=[_retry_action_receipt(), _benign_overlay_action_receipt()],
            ),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    triage = cadence["failures"][0]["blocker_triage"]
    assert triage["comment_action"] == {
        "sequence_name": TIKTOK_COMMENT_SURFACE_TOGGLE_POINTER_SEQUENCE_NAME,
        "action_count": 0,
        "action_sequence": [],
        "clicked_all_targets": False,
    }

def test_live_probe_completes_with_dom_visible_comment_fallback(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                responses=[],
                dom_comment_candidates=[
                    {
                        "text": "What perfume is this?",
                        "selector": '[data-e2e*="comment"]',
                    }
                ],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 1
    assert cadence["challenge_count"] == 0
    assert cadence["failures"] == []
    row = cadence["results"][0]
    assert row["comment_responses"] == []
    assert row["dom_visible_comment_candidates"][0]["text"] == "What perfume is this?"
    receipt = row["capture_receipt"]
    assert receipt["admitted_comment_response_count"] == 0
    assert receipt["dom_visible_comment_candidate_count"] == 1
    assert receipt["comment_capture_fallback"] == "dom_visible_comment_candidates_v0"


def test_live_probe_rejects_dom_visible_count_badge_as_comment_fallback(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            _success_observation(
                video_id="7390000000000000001",
                responses=[],
                dom_comment_candidates=[
                    {
                        "text": "303",
                        "selector": '[data-e2e*="comment"]',
                    },
                    {
                        "text": "1.2K comments",
                        "selector": '[data-e2e*="comment"]',
                    },
                ],
            )
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=["https://www.tiktok.com/@funmi/video/7390000000000000001"],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 0
    assert cadence["partial_count"] == 1
    assert cadence["results"][0]["status"] == "partial_failure"
    assert cadence["results"][0]["dom_visible_comment_candidates"] == []
    failure = cadence["failures"][0]
    assert failure["reason"] == TIKTOK_COMMENT_ROUTE_NO_RESPONSE_REASON
    triage = failure["blocker_triage"]
    assert triage["dom_visible_comment_candidate_count"] == 0
    assert triage["matched_comment_response_count"] == 0

def test_live_probe_stops_on_platform_challenge(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            BrowserPageObservationSuccess(
                requested_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                final_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                title="Verify to continue",
                visible_text="Drag the slider to verify to continue",
                dom_observation={"hydration_json_text": None},
                responses=[],
                metadata={"post_load_pointer_action": _pointer_action_receipt()},
                warning_notes=[],
                limitation_notes=[],
            ),
            _success_observation(video_id="7390000000000000002"),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    assert cadence["failures"][0]["reason"] == "platform_challenge_observed"
    assert cadence["failures"][0]["blocker_triage"]["blocker_class"] == (
        TIKTOK_BLOCKER_CLASS_CHALLENGE_OR_SECURITY
    )
    assert cadence["failures"][0]["blocker_triage"]["action"] == TIKTOK_BLOCKER_ACTION_STOP
    assert cadence["failures"][0]["blocker_triage"]["action_taken"] is False
    assert cadence["failures"][0]["blocker_triage"]["matched_marker"] == "verify to continue"
    assert cadence["failures"][0]["blocker_triage"]["challenge_kind"] == "slider"
    assert len(engine.calls) == 1


def test_live_probe_account_risk_is_non_retriable_batch_stop(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            BrowserPageObservationSuccess(
                requested_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                final_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                title="TikTok",
                visible_text="Your account might be at risk",
                dom_observation={"hydration_json_text": "{}"},
                responses=[],
                metadata={
                    "post_load_pointer_actions": [],
                    "pre_action_stop_attempts": [
                        {
                            "action_name": "pre_action_terminal_stop_v0",
                            "automatic_retry_allowed": False,
                        }
                    ],
                },
                warning_notes=[],
                limitation_notes=[],
            ),
            _success_observation(video_id="7390000000000000002"),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert len(engine.calls) == 1
    triage = cadence["failures"][0]["blocker_triage"]
    assert triage["challenge_kind"] == "account_risk"
    assert triage["account_safety_stop"] is True
    assert triage["automatic_retry_allowed"] is False
    assert triage["operator_next_action"] == "review_security_alerts_before_new_run"


def test_live_probe_stops_on_missing_video_detail_hydration(tmp_path: Path) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            BrowserPageObservationSuccess(
                requested_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                final_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                title="TikTok",
                visible_text="video loaded",
                dom_observation={"hydration_json_text": None},
                responses=[],
                metadata={"post_load_pointer_action": _pointer_action_receipt()},
                warning_notes=[],
                limitation_notes=[],
            ),
            _success_observation(video_id="7390000000000000002"),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 1
    assert cadence["completed_count"] == 0
    assert cadence["challenge_count"] == 1
    assert cadence["failures"][0]["reason"] == "missing_video_detail_hydration"
    assert cadence["failures"][0]["blocker_triage"]["blocker_class"] == (
        TIKTOK_BLOCKER_CLASS_INFRASTRUCTURE_RELOAD
    )
    assert cadence["failures"][0]["blocker_triage"]["action"] == (
        TIKTOK_BLOCKER_ACTION_RELOAD_ONCE_CANDIDATE
    )
    assert cadence["failures"][0]["blocker_triage"]["action_taken"] is False
    assert len(engine.calls) == 1


def test_live_probe_does_not_stop_on_close_text_without_blocker_candidate(
    tmp_path: Path,
) -> None:
    auth_root = _auth_state(tmp_path)
    engine = _FakeObservationEngine(
        outcomes=[
            BrowserPageObservationSuccess(
                requested_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                final_url="https://www.tiktok.com/@funmi/video/7390000000000000001",
                title="TikTok",
                visible_text="Close",
                dom_observation={
                    "hydration_json_text": json.dumps(_hydration("7390000000000000001"))
                },
                responses=[_comment_response()],
                metadata={"post_load_pointer_action": _pointer_action_receipt()},
                warning_notes=[],
                limitation_notes=[],
            ),
            _success_observation(video_id="7390000000000000002", response=_comment_response()),
        ]
    )

    paths = _write_sessioned_probe(
        tmp_path,
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        auth_state_root=auth_root,
        engine=engine,
    )

    cadence = json.loads(paths.cadence_result_json_path.read_text(encoding="utf-8"))
    assert cadence["attempted_count"] == 2
    assert cadence["completed_count"] == 2
    assert cadence["challenge_count"] == 0
    assert cadence["failures"] == []
    first_triage = cadence["results"][0]["capture_receipt"]["blocker_triage"]
    assert first_triage["blocker_class"] == TIKTOK_BLOCKER_CLASS_NO_BLOCKER
    assert first_triage["action"] == TIKTOK_BLOCKER_ACTION_CONTINUE
    assert "Close" not in json.dumps(cadence)
    assert len(engine.calls) == 2

def test_live_probe_runner_exposes_no_secret_or_storage_path_flags() -> None:
    forbidden_destinations = {"password", "username", "token", "cookie", "profile"}
    forbidden_options = {
        "--password",
        "--username",
        "--token",
        "--cookie",
        "--profile",
        "--profile-path",
        "--storage-state-path",
    }
    parser = runner.build_parser()
    destinations = {action.dest for action in parser._actions}
    options = {option for action in parser._actions for option in action.option_strings}
    assert destinations.isdisjoint(forbidden_destinations)
    assert options.isdisjoint(forbidden_options)


def test_comment_list_predicate_is_tiktok_path_only() -> None:
    assert is_tiktok_comment_list_url("https://www.tiktok.com/api/comment/list/?cursor=0")
    assert is_tiktok_comment_list_url("https://www.tiktok.com/api/comment/list/?signed=value")
    assert not is_tiktok_comment_list_url("https://www.tiktok.com/api/user/list/?cursor=0")
    assert not is_tiktok_comment_list_url("https://not-tiktok.example.com/api/comment/list/?cursor=0")
    assert not is_tiktok_comment_list_url("https://example.com/api/comment/list/?cursor=0")


def _comment_route_action_names() -> list[str]:
    return [
        TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
        TIKTOK_OPEN_MORE_LIKE_THIS_POINTER_ACTION_NAME,
        TIKTOK_REOPEN_COMMENTS_POINTER_ACTION_NAME,
    ]


def _comment_route_with_followthrough_action_names() -> list[str]:
    names: list[str] = []
    for action_name in _comment_route_action_names():
        names.extend(
            [
                action_name,
                TIKTOK_CHALLENGE_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
                TIKTOK_CHALLENGE_VISUAL_CLOSE_FOLLOWTHROUGH_POINTER_ACTION_NAME,
            ]
        )
    return names


def _comment_route_with_diagnostic_action_names() -> list[str]:
    names: list[str] = []
    for action_name in _comment_route_action_names():
        names.extend(
            [
                action_name,
                TIKTOK_CHALLENGE_VISUAL_CLOSE_DIAGNOSTIC_POINTER_ACTION_NAME,
            ]
        )
    return names

def _auth_state(tmp_path: Path) -> Path:
    auth_root = tmp_path / "auth"
    path = auth_state_path_for_label("test-session", auth_state_root=auth_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cookies": [], "origins": []}), encoding="utf-8")
    write_auth_state_metadata(
        "test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        auth_state_root=auth_root,
    )
    return auth_root



def _auth_state_with_provenance(
    tmp_path: Path,
    *,
    harness_proxy_profile_posture: str,
    proxy_category: str,
) -> Path:
    auth_root = tmp_path / "auth"
    path = auth_state_path_for_label("test-session", auth_state_root=auth_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cookies": [], "origins": []}), encoding="utf-8")
    write_auth_state_metadata(
        "test-session",
        session_mode=AuthenticatedSessionMode.FREE_ACCOUNT_CREATED,
        auth_state_root=auth_root,
        source_access_provenance={
            "source_access_posture": "free_account_created_session",
            "browser_backend": "cloakbrowser",
            "harness_proxy_profile_posture": harness_proxy_profile_posture,
            "proxy_category": proxy_category,
            "warmup_user_data_label_sha256": "a" * 64,
            "state_content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "no_secret_scan": "passed",
        },
    )
    return auth_root


def _comment_response(
    *,
    video_id: str = "7390000000000000001",
    cid: str = "7291",
) -> BrowserPageResponse:
    response_url = (
        "https://www.tiktok.com/api/comment/list/"
        f"?aweme_id={video_id}&cursor=0&count=20"
    )
    return BrowserPageResponse(
        requested_url=response_url,
        final_url=response_url,
        status=200,
        ok=True,
        body_text=json.dumps(
            {
                "cursor": 20,
                "has_more": 0,
                "total": 1,
                "comments": [
                    {
                        "cid": cid,
                        "text": "Route proof",
                        "create_time": 1710000000,
                        "digg_count": 1,
                        "reply_comment_total": 0,
                        "user": {
                            "uid": "u1",
                            "unique_id": "viewer_one",
                            "nickname": "Viewer One",
                        },
                    }
                ],
            }
        ),
        response_headers={"content-type": "application/json"},
        request_method="GET",
        resource_type="fetch",
    )


def _subtitle_response(
    *,
    url: str,
    body: bytes,
    status: int = 200,
) -> BrowserPageResponse:
    return BrowserPageResponse(
        requested_url=url,
        final_url=url,
        status=status,
        ok=200 <= status < 300,
        body_text=body.decode("utf-8"),
        response_headers={"content-type": "text/vtt"},
        request_method="GET",
        resource_type="fetch",
    )


def _success_observation(
    *,
    video_id: str,
    response: BrowserPageResponse | None = None,
    responses: list[BrowserPageResponse] | None = None,
    pointer_sequence: list[dict[str, object]] | None = None,
    visible_text: str = "video loaded",
    dom_comment_candidates: list[dict[str, object]] | None = None,
    subtitle_url: str = "https://subtitle.example.invalid/subtitle.webvtt",
    page_context_observations: list[dict[str, object]] | None = None,
) -> BrowserPageObservationSuccess:
    pointer_sequence = pointer_sequence or _live_pointer_action_sequence_receipt()
    dom_observation: dict[str, object] = {
        "hydration_json_text": json.dumps(_hydration(video_id, subtitle_url=subtitle_url))
    }
    if dom_comment_candidates is not None:
        dom_observation["visible_comment_candidates"] = dom_comment_candidates
    return BrowserPageObservationSuccess(
        requested_url=f"https://www.tiktok.com/@funmi/video/{video_id}",
        final_url=f"https://www.tiktok.com/@funmi/video/{video_id}",
        title="TikTok",
        visible_text=visible_text,
        dom_observation=dom_observation,
        responses=responses if responses is not None else ([response] if response is not None else []),
        metadata={
            "post_load_pointer_action": pointer_sequence[-1],
            "post_load_pointer_actions": pointer_sequence,
            **(
                {
                    "page_interaction_context_observations": (
                        page_context_observations
                    )
                }
                if page_context_observations is not None
                else {}
            ),
        },
        warning_notes=[],
        limitation_notes=[],
    )


def test_overlay_route_uses_grid_metadata_without_item_struct() -> None:
    video_id = "7390000000000000001"
    capture = _success_observation(
        video_id=video_id,
        response=_comment_response(video_id=video_id),
    )
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": False,
            "visible_comment_candidates": [],
            "subtitle_tracks": [],
        }
    )
    sequence_calls: list[tuple[int, list[str]]] = []

    def capture_from_grid(
        index: int, pending_urls: list[str]
    ) -> tuple[str, BrowserPageObservationSuccess]:
        sequence_calls.append((index, list(pending_urls)))
        return pending_urls[0], capture

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[f"https://www.tiktok.com/@funmi/video/{video_id}"],
        logged_out=True,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=capture_from_grid,
        grid_candidates_by_video_id={
            video_id: {
                "video_id": video_id,
                "video_url": f"https://www.tiktok.com/@funmi/video/{video_id}",
                "desc": "Grid description",
                "createTime": 1710000000,
                "author": {"id": "author-1", "uniqueId": "funmi"},
                "stats": {
                    "playCount": 1000,
                    "diggCount": 50,
                    "commentCount": 42,
                    "shareCount": 3,
                    "collectCount": 2,
                },
                "music": {"id": "music-1", "title": "Original sound"},
            }
        },
        sleep_fn=lambda _seconds: None,
    )

    assert sequence_calls == [
        (0, [f"https://www.tiktok.com/@funmi/video/{video_id}"])
    ]
    assert result["cadence_result"]["completed_count"] == 1
    row = result["cadence_result"]["results"][0]
    assert row["capture_receipt"]["deep_capture_route"] == "grid_tile_overlay"
    assert row["capture_receipt"]["item_struct_present"] is False
    assert row["capture_receipt"]["comment_outcome"] == "captured"
    assert row["capture_receipt"]["overlay_evidence"]["ready"] is True
    assert row["subtitle"] == {
        "attempted": False,
        "success": False,
        "reason": "no_subtitle_url_in_hydration_v0",
    }
    assert result["grid_result"]["response_items"][0]["desc"] == "Grid description"
    contract = result["cadence_result"]["capture_contract"]
    assert contract["video_navigation_mode"] == "grid_tile_overlay_sequence"
    assert contract["direct_video_navigation"] is False
    assert contract["item_struct_required"] is False


def test_overlay_route_uses_exact_profile_grid_subtitle_source() -> None:
    video_id = "7390000000000000001"
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"
    subtitle_url = "https://v16-webapp.tiktok.com/grid-subtitle.webvtt"
    subtitle_body = (
        b"WEBVTT\n\n"
        b"00:00:00.000 --> 00:00:01.000\n"
        b"Grid transcript recovered\n"
    )
    capture = _success_observation(
        video_id=video_id,
        responses=[
            _comment_response(video_id=video_id),
            _subtitle_response(url=subtitle_url, body=subtitle_body),
        ],
    )
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": False,
            "visible_comment_candidates": [],
            "subtitle_tracks": [],
        }
    )

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[video_url],
        logged_out=True,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=lambda _index, _pending: (video_url, capture),
        grid_candidates_by_video_id={
            video_id: {
                "video_id": video_id,
                "video_url": video_url,
                "author": {"uniqueId": "funmi"},
                "stats": {"playCount": 1000},
            }
        },
        profile_grid_subtitle_sources_by_video_id={
            video_id: {
                "id": video_id,
                "video": {
                    "subtitleInfos": [
                        {
                            "Format": "webvtt",
                            "LanguageCodeName": "eng-US",
                            "Url": subtitle_url,
                        }
                    ]
                },
            }
        },
        sleep_fn=lambda _seconds: None,
    )

    row = result["cadence_result"]["results"][0]
    assert row["capture_receipt"]["item_struct_present"] is False
    assert (
        row["capture_receipt"]["field_provenance"]["subtitles"]
        == "profile_grid_item_list_item_struct"
    )
    assert row["hydration"]["subtitle_metadata_source"] == (
        "profile_grid_item_list_item_struct"
    )
    assert row["subtitle"]["success"] is True
    assert row["subtitle"]["parsed_webvtt"]["cue_count"] == 1
    assert (
        row["subtitle"]["parsed_webvtt"]["transcript_text"]
        == "Grid transcript recovered"
    )
    assert subtitle_url not in json.dumps(result)


def test_overlay_route_uses_exact_react_video_subtitle_source() -> None:
    video_id = "7390000000000000001"
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"
    subtitle_url = "https://v16-webapp.tiktok.com/react-subtitle.webvtt"
    subtitle_body = (
        b"WEBVTT\n\n"
        b"00:00:00.000 --> 00:00:01.000\n"
        b"React transcript recovered\n"
    )
    capture = _success_observation(
        video_id=video_id,
        responses=[
            _comment_response(video_id=video_id),
            _subtitle_response(url=subtitle_url, body=subtitle_body),
        ],
    )
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": False,
            "visible_comment_candidates": [],
            "subtitle_tracks": [],
            "react_video_subtitle_source": {
                "id": video_id,
                "video": {
                    "subtitleInfos": [
                        {
                            "Format": "webvtt",
                            "LanguageCodeName": "eng-US",
                            "Url": subtitle_url,
                        }
                    ]
                },
            },
        }
    )

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[video_url],
        logged_out=True,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=lambda _index, _pending: (video_url, capture),
        grid_candidates_by_video_id={
            video_id: {
                "video_id": video_id,
                "video_url": video_url,
                "author": {"uniqueId": "funmi"},
                "stats": {"playCount": 1000},
            }
        },
        sleep_fn=lambda _seconds: None,
    )

    row = result["cadence_result"]["results"][0]
    assert row["capture_receipt"]["item_struct_present"] is False
    assert (
        row["capture_receipt"]["field_provenance"]["subtitles"]
        == "overlay_react_video_info"
    )
    assert row["subtitle"]["success"] is True
    assert row["subtitle"]["parsed_webvtt"]["cue_count"] == 1
    assert (
        row["subtitle"]["parsed_webvtt"]["transcript_text"]
        == "React transcript recovered"
    )
    assert subtitle_url not in json.dumps(result)


def test_overlay_route_rejects_mismatched_react_video_subtitle_source() -> None:
    video_id = "7390000000000000001"
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"
    capture = _success_observation(video_id=video_id)
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": True,
            "visible_comment_candidates": [],
            "subtitle_tracks": [],
            "react_video_subtitle_source": {
                "id": "7390000000000000002",
                "video": {"subtitleInfos": []},
            },
        }
    )

    with pytest.raises(
        ValueError,
        match="overlay React subtitle source id does not match",
    ):
        live_batch_probe.run_tiktok_live_batch_probe(
            creator_handle="funmi",
            creator_profile_url="https://www.tiktok.com/@funmi",
            video_urls=[video_url],
            logged_out=True,
            cadence_min_gap_seconds=0,
            cadence_max_gap_seconds=0,
            capture_route="grid_tile_overlay",
            page_capture_sequence_fn=lambda _index, _pending: (
                video_url,
                capture,
            ),
            grid_candidates_by_video_id={
                video_id: {
                    "video_id": video_id,
                    "video_url": video_url,
                    "stats": {"playCount": 1000},
                }
            },
            sleep_fn=lambda _seconds: None,
        )


def test_overlay_route_rejects_mismatched_profile_grid_subtitle_source() -> None:
    video_id = "7390000000000000001"
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"

    with pytest.raises(
        ValueError,
        match="profile grid subtitle source id does not match",
    ):
        live_batch_probe.run_tiktok_live_batch_probe(
            creator_handle="funmi",
            creator_profile_url="https://www.tiktok.com/@funmi",
            video_urls=[video_url],
            logged_out=True,
            capture_route="grid_tile_overlay",
            page_capture_sequence_fn=lambda _index, _pending: (
                video_url,
                _success_observation(video_id=video_id),
            ),
            grid_candidates_by_video_id={
                video_id: {
                    "video_id": video_id,
                    "video_url": video_url,
                    "stats": {"playCount": 1000},
                }
            },
            profile_grid_subtitle_sources_by_video_id={
                video_id: {
                    "id": "7390000000000000002",
                    "video": {"subtitleInfos": []},
                }
            },
        )


def test_overlay_route_preserves_dom_view_provenance_without_zero_filling_engagement() -> None:
    video_id = "7390000000000000001"
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"
    capture = _success_observation(video_id=video_id, response=_comment_response(video_id=video_id))
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": False,
            "visible_comment_candidates": [],
            "subtitle_tracks": [],
        }
    )

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[video_url],
        logged_out=True,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=lambda _index, _pending: (video_url, capture),
        grid_candidates_by_video_id={
            video_id: {
                "video_id": video_id,
                "video_url": video_url,
                "author": {"uniqueId": "funmi"},
                "stats": {"playCount": 31_800},
                "grid_view_count": {
                    "raw_text_or_none": "31.8K",
                    "parsed_approximate_count_or_none": 31_800,
                    "source": "profile_grid_dom_view_count_footer",
                    "source_display_precision": "rounded_compact",
                    "used_for_play_count": True,
                },
            }
        },
        sleep_fn=lambda _seconds: None,
    )

    grid_candidate = result["grid_result"]["response_items"][0]
    assert grid_candidate["stats"] == {"playCount": 31_800}
    assert grid_candidate["grid_view_count"]["raw_text_or_none"] == "31.8K"
    field_provenance = result["cadence_result"]["results"][0]["capture_receipt"][
        "field_provenance"
    ]
    assert field_provenance["play_count"] == (
        "profile_grid_dom_view_count_footer_rounded_compact"
    )
    assert field_provenance["structured_video_metadata"] == (
        "profile_grid_item_response_with_rounded_dom_view_fallback"
    )


def test_overlay_route_preserves_visible_empty_comment_outcome() -> None:
    video_id = "7390000000000000001"
    capture = _success_observation(video_id=video_id, responses=[])
    capture.dom_observation.update(
        {
            "hydration_json_text": None,
            "video_overlay_detected": True,
            "visible_video_element_count": 1,
            "overlay_video_id_or_none": video_id,
            "overlay_creator_handle_or_none": "funmi",
            "comment_surface_detected": True,
            "comment_surface_visible_empty": True,
            "visible_comment_candidates": [],
        }
    )
    video_url = f"https://www.tiktok.com/@funmi/video/{video_id}"

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[video_url],
        logged_out=True,
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=lambda _index, _pending: (video_url, capture),
        grid_candidates_by_video_id={
            video_id: {
                "video_id": video_id,
                "video_url": video_url,
                "author": {"uniqueId": "funmi"},
                "stats": {"playCount": 1000, "diggCount": 50},
            }
        },
        sleep_fn=lambda _seconds: None,
    )

    assert result["cadence_result"]["completed_count"] == 1
    assert result["cadence_result"]["failures"] == []
    assert (
        result["cadence_result"]["results"][0]["capture_receipt"][
            "comment_outcome"
        ]
        == "visible_empty"
    )


def _live_pointer_action_sequence_receipt() -> list[dict[str, object]]:
    return [_retry_action_receipt(), _benign_overlay_action_receipt(), *_pointer_action_sequence_receipt()]


def _retry_action_receipt() -> dict[str, object]:
    return _pointer_action_receipt(
        action_name=TIKTOK_RETRY_VISIBLE_ERROR_POINTER_ACTION_NAME,
        wait_ms=2500,
        page_text_gate_matched=False,
        selection_strategy="first_match",
    )


def _benign_overlay_action_receipt() -> dict[str, object]:
    return _pointer_action_receipt(
        action_name=TIKTOK_DISMISS_BENIGN_OVERLAY_POINTER_ACTION_NAME,
        wait_ms=1500,
        page_text_gate_matched=True,
        selection_strategy="first_match",
    )


def _pointer_action_sequence_receipt() -> list[dict[str, object]]:
    return [
        _pointer_action_receipt(
            action_name=TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
            wait_ms=5000,
        ),
        _pointer_action_receipt(
            action_name=TIKTOK_OPEN_MORE_LIKE_THIS_POINTER_ACTION_NAME,
            wait_ms=2000,
        ),
        _pointer_action_receipt(
            action_name=TIKTOK_REOPEN_COMMENTS_POINTER_ACTION_NAME,
            wait_ms=5000,
        ),
    ]


def _pointer_action_receipt(
    *,
    action_name: str = TIKTOK_OPEN_COMMENTS_POINTER_ACTION_NAME,
    wait_ms: int = 2500,
    page_text_gate_matched: bool | None = None,
    selection_strategy: str | None = None,
    page_text_matched_marker: str | None = None,
) -> dict[str, object]:
    receipt: dict[str, object | None] = {
        "action_name": action_name,
        "candidate_count": 5,
        "matched_count": 1,
        "target_found": True,
        "clicked": True,
        "move_steps": 7,
        "wait_ms": wait_ms,
        "target_kind": "button",
        "page_text_gate_matched": page_text_gate_matched,
        "page_text_matched_marker": page_text_matched_marker,
        "selection_strategy": selection_strategy,
    }
    return {key: value for key, value in receipt.items() if value is not None}


def _hydration(
    video_id: str,
    *,
    subtitle_url: str = "https://subtitle.example.invalid/subtitle.webvtt",
) -> dict[str, object]:
    return {
        "__DEFAULT_SCOPE__": {
            "webapp.video-detail": {
                "itemInfo": {
                    "itemStruct": {
                        "id": video_id,
                        "desc": "Testing #capture",
                        "createTime": 1710000000,
                        "stats": {
                            "playCount": 1000,
                            "diggCount": 50,
                            "commentCount": 42,
                            "shareCount": 3,
                            "collectCount": 2,
                        },
                        "author": {"uniqueId": "funmi", "nickname": "Funmi"},
                        "music": {"id": "m1", "title": "Original sound", "duration": 12},
                        "video": {
                            "subtitleInfos": [
                                {
                                    "Format": "webvtt",
                                    "LanguageCodeName": "eng-US",
                                    "LanguageID": "2",
                                    "Size": 123,
                                    "Source": "MT",
                                    "Version": "1",
                                    "Url": subtitle_url,
                                }
                            ]
                        },
                    }
                }
            }
        }
    }


def test_cadence_waits_full_dwell_after_completed_browser_work() -> None:
    monotonic_values = iter((3.0, 13.0))
    sleep_calls: list[float] = []

    capture_started_at, actual_dwell = (
        live_batch_probe._wait_for_next_capture_after_completion(
        planned_dwell_seconds=10.0,
        monotonic_fn=lambda: next(monotonic_values),
        sleep_fn=sleep_calls.append,
    )
    )

    assert sleep_calls == [10.0]
    assert capture_started_at == 13.0
    assert actual_dwell == 10.0


def test_completion_relative_cadence_does_not_collapse_after_slow_browser_work() -> None:
    monotonic_values = iter((12.0, 22.0))
    sleep_calls: list[float] = []

    capture_started_at, actual_dwell = (
        live_batch_probe._wait_for_next_capture_after_completion(
        planned_dwell_seconds=10.0,
        monotonic_fn=lambda: next(monotonic_values),
        sleep_fn=sleep_calls.append,
    )
    )

    assert sleep_calls == [10.0]
    assert capture_started_at == 22.0
    assert actual_dwell == 10.0


def test_cadence_receipts_completion_relative_realized_wait() -> None:
    sleep_calls: list[float] = []
    activity_events: list[tuple[str, dict[str, object]]] = []
    monotonic_values = iter((3.0, 13.0))
    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        logged_out=True,
        cadence_min_gap_seconds=10.0,
        cadence_max_gap_seconds=10.0,
        engine=_FakeObservationEngine(
            outcomes=[
                _success_observation(
                    video_id="7390000000000000001",
                    response=_comment_response(video_id="7390000000000000001"),
                ),
                _success_observation(
                    video_id="7390000000000000002",
                    response=_comment_response(video_id="7390000000000000002"),
                ),
            ]
        ),
        sleep_fn=sleep_calls.append,
        monotonic_fn=lambda: next(monotonic_values),
        activity_event_fn=lambda event, fields: activity_events.append(
            (event, fields)
        ),
    )

    assert sleep_calls == [10.0]
    assert result["cadence_result"]["realized_inter_video_waits"] == [
        {
            "transition_index": 0,
            "prior_video_id": "7390000000000000001",
            "configured_range_seconds": {"min": 10.0, "max": 10.0},
            "planned_seconds": 10.0,
            "actual_seconds": 10.0,
            "basis": "prior_capture_complete_to_next_capture_start",
        }
    ]
    assert (
        result["cadence_result"]["capture_contract"]["inter_video_wait_basis"]
        == "prior_capture_complete_to_next_capture_start"
    )
    assert [event for event, _fields in activity_events] == [
        "cadence_wait_started",
        "cadence_wait_finished",
    ]
    assert activity_events[0][1]["policy"] == "completion_relative"
    assert activity_events[1][1]["actual_seconds"] == 10.0


def test_live_probe_cli_defaults_to_twelve_forty_five_second_range() -> None:
    args = runner.build_parser().parse_args(
        [
            "--creator-handle",
            "funmi",
            "--creator-profile-url",
            "https://www.tiktok.com/@funmi",
            "--video-url",
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "--logged-out",
            "--output-dir",
            "out",
        ]
    )

    assert (args.cadence_min_gap_seconds + args.cadence_max_gap_seconds) / 2 == 28.5
    assert args.cadence_min_gap_seconds == 12.0
    assert args.cadence_max_gap_seconds == 45.0


def test_default_cloakbrowser_batch_reuses_one_owned_session(monkeypatch) -> None:
    instances: list[object] = []
    seen_engines: list[object] = []

    class FakeSessionEngine:
        def __init__(self, **_kwargs: object) -> None:
            self.closed = False
            instances.append(self)

        def close(self) -> None:
            self.closed = True

        @property
        def lifecycle_receipt(self) -> dict[str, object]:
            return {
                "engine": "fake_cloakbrowser_page_observation_session",
                "browser_launch_count": 1,
                "context_creation_count": 1,
                "capture_attempt_count": len(seen_engines),
                "capture_success_count": len(seen_engines),
                "closed": self.closed,
            }

    def fake_fetch_browser_page_observation_capture(
        **kwargs: object,
    ) -> BrowserPageObservationSuccess:
        seen_engines.append(kwargs["engine"])
        video_id = str(kwargs["url"]).rsplit("/", 1)[-1]
        return _success_observation(
            video_id=video_id,
            response=_comment_response(video_id=video_id),
            subtitle_url="https://v16.tiktokcdn.com/subtitle.webvtt",
        )

    monkeypatch.setattr(
        live_batch_probe,
        "CloakBrowserPageObservationSessionEngine",
        FakeSessionEngine,
    )
    monkeypatch.setattr(
        live_batch_probe,
        "fetch_browser_page_observation_capture",
        fake_fetch_browser_page_observation_capture,
    )

    result = live_batch_probe.run_tiktok_live_batch_probe(
        creator_handle="funmi",
        creator_profile_url="https://www.tiktok.com/@funmi",
        video_urls=[
            "https://www.tiktok.com/@funmi/video/7390000000000000001",
            "https://www.tiktok.com/@funmi/video/7390000000000000002",
        ],
        logged_out=True,
        browser_backend="cloakbrowser",
        cadence_min_gap_seconds=0,
        cadence_max_gap_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

    assert len(instances) == 1
    assert seen_engines == [instances[0], instances[0]]
    assert instances[0].closed is True
    assert result["cadence_result"]["browser_lifecycle"] == {
        "engine": "fake_cloakbrowser_page_observation_session",
        "browser_launch_count": 1,
        "context_creation_count": 1,
        "capture_attempt_count": 2,
        "capture_success_count": 2,
        "closed": True,
    }
