"""Offline tests for the IG creator reels-grid deep-capture orchestration.

No network/browser. The grid scan, per-reel deep-capture, and persistence are all
injected as fakes, exactly as ``run_reel_deep_capture`` injects render/download/
transcribe. Covers: engagement ranking + top-N selection, per-reel call order, a
per-reel failure being recorded without aborting the batch, tie / None engagement
handling, and top_n larger than the available reel count.
"""
from __future__ import annotations

import json

import pytest

from data_lake.root import DataLakeRoot
from runners import run_source_capture_ig_reels_creator_deep_capture as creator_runner
from runners import run_source_capture_ig_reels_deep_capture as deep_capture_runner
from runners.run_source_capture_ig_reels_creator_deep_capture import (
    CapturedReel,
    IgReelsGridCaptureError,
    RankedReel,
    rank_reels_by_engagement,
    scan_creator_reels_ranked,
    select_and_capture_top_reels,
)
from source_capture.ig_reels_deep_capture import ReelDeepCaptureResult
from source_capture.ig_reels_deep_capture_lake import DEEP_CAPTURE_SET_LANE, deep_capture_record_id
from source_capture.ig_reels_grid import (
    CLIPS_USER_JSON_METADATA,
    iter_json_media_candidates,
    join_dom_rows_with_json_candidates,
    normalize_dom_grid_rows,
)
from source_capture.ig_reels_grid_capture import (
    IgReelsGridCaptureFailure,
    IgReelsGridCaptureSuccess,
    IgReelsGridPassiveResponse,
)


def _ranked(shortcode: str, engagement: int, *, rank: int = 0) -> RankedReel:
    """A directly-built ranked reel for pure select/loop tests (rank is unused by the loop)."""
    return RankedReel(rank=rank, shortcode=shortcode, engagement=engagement, like_count=None, comment_count=None)


def _fake_result(shortcode: str, *, comments: int = 0, posture: str = "ok") -> ReelDeepCaptureResult:
    return ReelDeepCaptureResult(
        reel_shortcode=shortcode,
        comments=(),
        transcript_posture=posture,
        transcript_cues=(),
        media_url_used=None,
        notes=(f"comments={comments}",),
    )


# --- ranking: engagement = (likes + comments), descending --------------------------


def test_rank_falls_back_to_views_when_likes_are_hidden() -> None:
    # IG serves the public grid anonymously WITHOUT like counts; ranking must fall back to views
    # (which IG still exposes) + flag likes_hidden, NOT rank on near-zero comment counts.
    dom_rows = normalize_dom_grid_rows(
        [
            {"path": "/creator/reel/FEW/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/MANY/", "visibleNumericTexts": ["1"]},
        ],
        final_url="https://www.instagram.com/creator/reels/",
        profile_handle="creator",
    )
    candidates = (
        list(iter_json_media_candidates({"code": "FEW", "comment_count": 9, "play_count": 100}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "MANY", "comment_count": 1, "play_count": 50000}, source_surface=CLIPS_USER_JSON_METADATA))
    )
    ranked = rank_reels_by_engagement(join_dom_rows_with_json_candidates(dom_rows, candidates))
    # Views win despite FEW having more comments -- the old likes+comments rule would invert this.
    assert [r.shortcode for r in ranked] == ["MANY", "FEW"]
    assert all(r.likes_hidden for r in ranked)
    assert ranked[0].view_count == 50000 and ranked[0].like_count is None


def test_rank_keeps_a_visible_like_when_a_tied_candidate_only_has_views() -> None:
    # A reel can join multiple surfaces with TIED engagement: one carrying a visible like, another
    # only views. The like-bearing candidate must not be discarded for the higher-view one, and the
    # grid must NOT be treated as likes-hidden just because the tie-break selected a no-likes surface.
    dom_rows = normalize_dom_grid_rows(
        [
            {"path": "/creator/reel/HASLIKES/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/VIEWSONLY/", "visibleNumericTexts": ["1"]},
        ],
        final_url="https://www.instagram.com/creator/reels/",
        profile_handle="creator",
    )
    candidates = (
        list(iter_json_media_candidates({"code": "HASLIKES", "like_count": 10, "comment_count": 0}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "HASLIKES", "comment_count": 10, "play_count": 100}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "VIEWSONLY", "comment_count": 1, "play_count": 99999}, source_surface=CLIPS_USER_JSON_METADATA))
    )
    ranked = rank_reels_by_engagement(join_dom_rows_with_json_candidates(dom_rows, candidates))
    by_code = {r.shortcode: r for r in ranked}
    assert not any(r.likes_hidden for r in ranked)        # a visible like exists in the grid
    assert by_code["HASLIKES"].like_count == 10           # the visible like was not discarded
    assert ranked[0].shortcode == "HASLIKES"              # likes regime: engagement(10) beats views


def test_rank_reels_orders_by_likes_plus_comments_descending() -> None:
    # Build joined rows through the real grid pipeline so ranking is exercised end-to-end.
    dom_rows = normalize_dom_grid_rows(
        [
            {"path": "/creator/reel/LOW/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/HIGH/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/MID/", "visibleNumericTexts": ["1"]},
        ],
        final_url="https://www.instagram.com/creator/reels/",
        profile_handle="creator",
    )
    candidates = (
        list(iter_json_media_candidates({"code": "LOW", "like_count": 1, "comment_count": 1}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "HIGH", "like_count": 500, "comment_count": 40}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "MID", "like_count": 100, "comment_count": 5}, source_surface=CLIPS_USER_JSON_METADATA))
    )
    joined = join_dom_rows_with_json_candidates(dom_rows, candidates)

    ranked = rank_reels_by_engagement(joined)

    assert [(r.rank, r.shortcode, r.engagement) for r in ranked] == [
        (1, "HIGH", 540),
        (2, "MID", 105),
        (3, "LOW", 2),
    ]


def test_rank_reels_treats_none_engagement_as_zero_and_keeps_grid_order_on_ties() -> None:
    # A reel with NO joined candidate (None likes/comments) and two true ties.
    dom_rows = normalize_dom_grid_rows(
        [
            {"path": "/creator/reel/NOCAND/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/TIE_A/", "visibleNumericTexts": ["1"]},
            {"path": "/creator/reel/TIE_B/", "visibleNumericTexts": ["1"]},
        ],
        final_url="https://www.instagram.com/creator/reels/",
        profile_handle="creator",
    )
    candidates = (
        # NOCAND deliberately has no JSON candidate -> None likes/comments -> engagement 0.
        list(iter_json_media_candidates({"code": "TIE_A", "like_count": 10, "comment_count": 0}, source_surface=CLIPS_USER_JSON_METADATA))
        + list(iter_json_media_candidates({"code": "TIE_B", "like_count": 10, "comment_count": 0}, source_surface=CLIPS_USER_JSON_METADATA))
    )
    joined = join_dom_rows_with_json_candidates(dom_rows, candidates)

    ranked = rank_reels_by_engagement(joined)

    # Ties (TIE_A, TIE_B both 10) keep grid order via the stable sort; NOCAND sinks to 0.
    assert [(r.shortcode, r.engagement) for r in ranked] == [
        ("TIE_A", 10),
        ("TIE_B", 10),
        ("NOCAND", 0),
    ]
    assert ranked[2].like_count is None and ranked[2].comment_count is None


def test_rank_reels_picks_the_candidate_with_most_engagement_signal() -> None:
    # One shortcode joins two surfaces; the surface that omitted counts must not mask
    # the one that has them. Rank on the richer candidate.
    dom_rows = normalize_dom_grid_rows(
        [{"path": "/creator/reel/MULTI/", "visibleNumericTexts": ["1"]}],
        final_url="https://www.instagram.com/creator/reels/",
        profile_handle="creator",
    )
    empty = iter_json_media_candidates({"code": "MULTI"}, source_surface=CLIPS_USER_JSON_METADATA)
    rich = iter_json_media_candidates(
        {"code": "MULTI", "like_count": 33, "comment_count": 7}, source_surface=CLIPS_USER_JSON_METADATA
    )
    joined = join_dom_rows_with_json_candidates(dom_rows, [*empty, *rich])

    ranked = rank_reels_by_engagement(joined)

    assert len(ranked) == 1
    assert (ranked[0].shortcode, ranked[0].engagement, ranked[0].like_count, ranked[0].comment_count) == (
        "MULTI",
        40,
        33,
        7,
    )


# --- select top-N + per-reel capture loop ------------------------------------------


def test_selects_exactly_top_n_in_rank_order_calling_capture_once_each() -> None:
    ranked = [_ranked("A", 100), _ranked("B", 50), _ranked("C", 10), _ranked("D", 1)]
    calls: list[str] = []

    def capture(shortcode: str) -> ReelDeepCaptureResult:
        calls.append(shortcode)
        return _fake_result(shortcode)

    captured = select_and_capture_top_reels(ranked, top_n=2, capture_fn=capture)

    # Exactly the top 2, in rank order, captured once each.
    assert calls == ["A", "B"]
    assert [c.ranked.shortcode for c in captured] == ["A", "B"]
    assert all(c.ok for c in captured)


def test_per_reel_failure_is_recorded_and_does_not_stop_the_batch() -> None:
    ranked = [_ranked("A", 100), _ranked("BOOM", 50), _ranked("C", 10)]
    calls: list[str] = []

    def capture(shortcode: str) -> ReelDeepCaptureResult:
        calls.append(shortcode)
        if shortcode == "BOOM":
            raise RuntimeError("render exploded")
        return _fake_result(shortcode)

    captured = select_and_capture_top_reels(ranked, top_n=3, capture_fn=capture)

    # Every selected reel was attempted, including the one AFTER the failure.
    assert calls == ["A", "BOOM", "C"]
    assert [c.ranked.shortcode for c in captured] == ["A", "BOOM", "C"]
    boom = captured[1]
    assert not boom.ok and boom.result is None
    assert boom.error is not None and "render exploded" in boom.error
    # The reels on either side still produced results.
    assert captured[0].ok and captured[2].ok


def test_top_n_larger_than_available_captures_all_without_error() -> None:
    ranked = [_ranked("A", 9), _ranked("B", 8)]
    calls: list[str] = []

    captured = select_and_capture_top_reels(
        ranked, top_n=10, capture_fn=lambda code: (calls.append(code), _fake_result(code))[1]
    )

    assert calls == ["A", "B"]
    assert [c.ranked.shortcode for c in captured] == ["A", "B"]


def test_top_n_zero_captures_nothing() -> None:
    captured = select_and_capture_top_reels(
        [_ranked("A", 9)], top_n=0, capture_fn=lambda code: pytest.fail("must not capture when top_n=0")
    )
    assert captured == []


def test_negative_top_n_rejected() -> None:
    with pytest.raises(ValueError):
        select_and_capture_top_reels([_ranked("A", 1)], top_n=-1, capture_fn=lambda code: _fake_result(code))


def test_persist_fn_runs_only_for_captured_reels_and_records_its_failure() -> None:
    ranked = [_ranked("OK", 100), _ranked("BOOM", 50)]
    persisted_codes: list[str] = []

    def capture(shortcode: str) -> ReelDeepCaptureResult:
        if shortcode == "BOOM":
            raise RuntimeError("no render")
        return _fake_result(shortcode)

    def persist(result: ReelDeepCaptureResult, ranked_reel: RankedReel) -> str:
        persisted_codes.append(result.reel_shortcode)
        return f"persisted: {result.reel_shortcode}"

    captured = select_and_capture_top_reels(ranked, top_n=2, capture_fn=capture, persist_fn=persist)

    # Persistence ran only for the reel that captured successfully, never the failed one.
    assert persisted_codes == ["OK"]
    assert captured[0].persisted == "persisted: OK"
    assert captured[1].persisted is None  # failed capture is never persisted


def test_persist_fn_failure_is_recorded_not_fatal() -> None:
    def persist(_result: ReelDeepCaptureResult, _ranked: RankedReel) -> str:
        raise OSError("disk full")

    captured = select_and_capture_top_reels(
        [_ranked("A", 1)], top_n=1, capture_fn=lambda code: _fake_result(code), persist_fn=persist
    )

    assert captured[0].ok  # capture itself still succeeded
    assert captured[0].persisted is not None and "persist-failed" in captured[0].persisted


# --- grid scan wiring: rank from a faked grid capture, fail closed on capture failure --


def _passive(source_surface: str, body: dict) -> IgReelsGridPassiveResponse:
    return IgReelsGridPassiveResponse(
        source_surface=source_surface,
        requested_url="https://www.instagram.com/api/v1/clips/user/?target_user_id=1",
        final_url="https://www.instagram.com/api/v1/clips/user/?target_user_id=1",
        status=200,
        ok=True,
        body_text=json.dumps(body),
        response_headers={"content-type": "application/json"},
    )


def _fake_grid_capture(**_kwargs) -> IgReelsGridCaptureSuccess:
    clips = {
        "items": [
            {"media": {"code": "TOP", "like_count": 900, "comment_count": 80, "ig_play_count": 5000}},
            {"media": {"code": "MIDDLE", "like_count": 100, "comment_count": 9, "ig_play_count": 2000}},
            {"media": {"code": "BOTTOM", "like_count": 3, "comment_count": 1, "ig_play_count": 50}},
        ]
    }
    return IgReelsGridCaptureSuccess(
        requested_url="https://www.instagram.com/creator/reels/",
        final_url="https://www.instagram.com/creator/reels/",
        title="creator reels",
        visible_text="creator",
        dom_rows=[
            {"path": f"/creator/reel/{code}/", "visibleNumericTexts": ["1"], "rect": {"x": 0, "y": 0, "width": 200, "height": 300}}
            for code in ("TOP", "MIDDLE", "BOTTOM")
        ],
        passive_json_responses=[_passive(CLIPS_USER_JSON_METADATA, clips)],
        metadata={"capture_timestamp": "2026-06-22T10:00:00Z"},
    )


def test_scan_creator_reels_ranked_ranks_from_a_faked_grid_capture() -> None:
    ranked, capture = scan_creator_reels_ranked(handle="@creator", capture_fetcher=_fake_grid_capture)

    assert isinstance(capture, IgReelsGridCaptureSuccess)
    assert [(r.shortcode, r.engagement) for r in ranked] == [
        ("TOP", 980),
        ("MIDDLE", 109),
        ("BOTTOM", 4),
    ]


def test_scan_creator_reels_ranked_uses_grid_packet_capture_defaults() -> None:
    seen: dict[str, object] = {}

    def _recording(**kwargs) -> IgReelsGridCaptureSuccess:
        seen.update(kwargs)
        return _fake_grid_capture()

    scan_creator_reels_ranked(handle="creator", capture_fetcher=_recording)

    assert seen["viewport_width"] == 1080
    assert seen["viewport_height"] == 1920
    assert seen["max_response_bytes"] == 5_000_000
    assert seen["block_heavy_assets"] is True
    assert seen["storage_state_path"] is None
    assert seen["headless"] is True
    assert seen["browser_channel"] is None


def test_scan_creator_reels_ranked_raises_typed_error_on_grid_capture_failure() -> None:
    def _failing(**_kwargs) -> IgReelsGridCaptureFailure:
        return IgReelsGridCaptureFailure(
            requested_url="https://www.instagram.com/creator/reels/",
            failure_kind="capture_failed",
            message="browser page observation capture failed",
            final_url="https://www.instagram.com/creator/reels/",
        )

    with pytest.raises(IgReelsGridCaptureError) as excinfo:
        scan_creator_reels_ranked(handle="creator", capture_fetcher=_failing)
    assert "capture failed" in str(excinfo.value).lower()


def test_scan_creator_reels_ranked_raises_typed_error_on_access_block() -> None:
    def _blocked(**_kwargs) -> IgReelsGridCaptureSuccess:
        return IgReelsGridCaptureSuccess(
            requested_url="https://www.instagram.com/creator/reels/",
            final_url="https://www.instagram.com/accounts/login/?next=%2Fcreator%2Freels%2F",
            title="Login - Instagram",
            visible_text="Log in to continue",
            dom_rows=[],
            passive_json_responses=[],
            metadata={"capture_timestamp": "2026-06-22T10:00:00Z"},
        )

    with pytest.raises(IgReelsGridCaptureError) as excinfo:
        scan_creator_reels_ranked(handle="creator", capture_fetcher=_blocked)

    assert "access-blocked" in str(excinfo.value)
    assert "redirected_to_login" in str(excinfo.value)


def test_scan_then_select_end_to_end_offline() -> None:
    # Full offline path: scan a faked grid -> rank -> capture top-N with a fake capture_fn.
    ranked, _capture = scan_creator_reels_ranked(handle="creator", capture_fetcher=_fake_grid_capture)
    calls: list[str] = []
    captured = select_and_capture_top_reels(
        ranked, top_n=2, capture_fn=lambda code: (calls.append(code), _fake_result(code))[1]
    )
    assert calls == ["TOP", "MIDDLE"]
    assert [c.ranked.shortcode for c in captured] == ["TOP", "MIDDLE"]
    assert all(isinstance(c, CapturedReel) and c.ok for c in captured)


def test_creator_main_persists_when_forseti_data_root_env_set(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "forseti-data")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    seen: dict[str, object] = {}

    class _TempDir:
        def __init__(self, *_, **__) -> None:  # noqa: ANN002, ANN003
            pass

        def __enter__(self) -> str:
            return str(scratch)

        def __exit__(self, *_exc: object) -> bool:
            return False

    def resolve(*, explicit=None):  # noqa: ANN001
        seen["explicit"] = explicit
        return root

    monkeypatch.setenv("FORSETI_DATA_ROOT", str(root.path))
    monkeypatch.setattr(deep_capture_runner.DataLakeRoot, "resolve", staticmethod(resolve))
    monkeypatch.setattr(creator_runner.tempfile, "TemporaryDirectory", _TempDir)
    monkeypatch.setattr(
        creator_runner,
        "scan_creator_reels_ranked",
        lambda **_kwargs: ([_ranked("A", 1, rank=1)], _fake_grid_capture()),
    )
    monkeypatch.setattr(
        creator_runner,
        "_make_capture_fn",
        lambda _scratch, *, transcribe_fn: (
            lambda shortcode: ReelDeepCaptureResult(
                reel_shortcode=shortcode,
                comments=(),
                transcript_posture="transcribed",
                transcript_cues=({"start_ms": 0, "end_ms": 10, "text": "hi"},),
                media_url_used="https://x.fbcdn.net/clip.mp4",
                audio_bytes=b"audio",
                audio_ext="mp4",
            )
        ),
    )

    assert creator_runner.main(["--handle", "creator", "--top-n", "1"]) == 0

    result = ReelDeepCaptureResult(
        "A", (), "transcribed", ({"start_ms": 0, "end_ms": 10, "text": "hi"},),
        "https://x.fbcdn.net/clip.mp4", audio_bytes=b"audio", audio_ext="mp4"
    )
    rid = deep_capture_record_id(result)
    assert seen == {"explicit": None}
    assert "persisted:" in capsys.readouterr().out
    packet_ids = [
        packet_id
        for packet_id in root.list_available(source_family="instagram_creator")
        if root.load_raw_packet(packet_id).manifest.get("source_surface") == "ig_reels_deep_capture"
    ]
    [packet_id] = packet_ids
    assert root.is_record_set_complete(
        subtree="derived", raw_anchor=packet_id, record_id=rid, completion_lane=DEEP_CAPTURE_SET_LANE
    )
