"""www transport selection on the Reddit grid runner.

The roster, cadence, batch summary, and duplicate checks are transport-agnostic
and stay single-homed; only URL shape, extraction spec, and capture call differ.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from capture_spine.reddit_subreddit_grid.materializer import (
    RegistryRefreshError,
    _resolve_grid_metadata_file,
    _verify_successful_grid_response,
)
from runners.run_reddit_grid_capture import (
    GridProjectionAnomalyError,
    GRID_TRANSPORTS,
    build_grid_listing_url,
    build_validated_www_grid_content_record,
    build_www_grid_listing_url,
    run_reddit_grid_capture,
)
from source_capture import known_fact
from source_capture.content_extraction import CONTENT_EXTRACTION_FAILED_EXIT_CODE


def test_www_url_carries_no_limit_parameter() -> None:
    assert (
        build_www_grid_listing_url(subreddit="testsub", listing="top", time_window="week")
        == "https://www.reddit.com/r/testsub/top/?t=week"
    )


def test_old_url_is_unchanged_by_the_www_addition() -> None:
    assert build_grid_listing_url(
        subreddit="testsub", listing="top", time_window="week", limit=100
    ) == "https://old.reddit.com/r/testsub/top/?t=week&limit=100"


def test_www_hot_listing_takes_no_time_window() -> None:
    assert (
        build_www_grid_listing_url(subreddit="testsub", listing="hot", time_window=None)
        == "https://www.reddit.com/r/testsub/hot/"
    )
    with pytest.raises(ValueError):
        build_www_grid_listing_url(subreddit="testsub", listing="hot", time_window="week")


def test_www_transport_refuses_a_raw_retention_request(tmp_path) -> None:
    """Never raw-only is enforced at the boundary, not left to the caller."""
    with pytest.raises(ValueError) as excinfo:
        run_reddit_grid_capture(
            subreddits=["testsub"],
            listing="top",
            time_window="week",
            output_root=tmp_path / "out",
            decision_question="q",
            transport="www_realchrome",
            requested_retention_mode="raw",
        )
    assert "never-raw-only" in str(excinfo.value)


def test_www_transport_refuses_a_listing_limit(tmp_path) -> None:
    """A limit www ignores would be a cap the operator believes is enforced."""
    with pytest.raises(ValueError) as excinfo:
        run_reddit_grid_capture(
            subreddits=["testsub"],
            listing="top",
            time_window="week",
            output_root=tmp_path / "out",
            decision_question="q",
            transport="www_realchrome",
            limit=100,
        )
    assert "limit" in str(excinfo.value)


def test_unknown_transport_fails_closed(tmp_path) -> None:
    with pytest.raises(ValueError) as excinfo:
        run_reddit_grid_capture(
            subreddits=["testsub"],
            listing="top",
            time_window="week",
            output_root=tmp_path / "out",
            decision_question="q",
            transport="carrier_pigeon",
        )
    assert "transport must be one of" in str(excinfo.value)


def test_default_transport_is_the_existing_one() -> None:
    assert GRID_TRANSPORTS[0] == "old_http"


def test_www_capture_waits_for_a_row_that_carries_a_permalink(monkeypatch, tmp_path) -> None:
    """Readiness is a populated row, not merely a post element existing.

    On 2026-07-31, 8 of 91 captures snapshotted before the feed was usable: 4
    with no posts at all and 4 with post elements whose permalink attribute had
    not populated. `shreddit-post[permalink]` is the one selector that covers
    both, because a row without a permalink yields no thread URL and so never
    becomes a projected row.
    """
    import runners.run_reddit_grid_capture as module

    seen: list[dict] = []
    monkeypatch.setattr(
        "runners.run_source_capture_realchrome_cdp_packet."
        "run_source_capture_realchrome_cdp_packet",
        lambda **kwargs: (seen.append(kwargs), (0, str(tmp_path / "packet")))[1],
    )
    run_reddit_grid_capture(
        subreddits=["alpha"],
        listing="top",
        time_window="week",
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        delay_seconds=0,
    )
    assert seen[0]["ready_selector"] == module.WWW_READY_SELECTOR
    assert seen[0]["ready_selector"] == "shreddit-post[permalink]"


def test_cycle_basis_subtracts_the_capture_duration() -> None:
    """A target start-to-start interval, not a wait bolted onto the capture."""
    from runners.run_reddit_grid_capture import _paced_wait

    row: dict = {}
    assert _paced_wait(planned=40.0, elapsed=25.0, basis="cycle", row=row) == 15.0
    assert "cadence_overrun_seconds" not in row


def test_gap_basis_is_unchanged_by_capture_duration() -> None:
    """The existing meaning must not move for callers that never asked."""
    from runners.run_reddit_grid_capture import _paced_wait

    assert _paced_wait(planned=40.0, elapsed=25.0, basis="gap", row={}) == 40.0


def test_a_capture_slower_than_its_target_is_reported_not_hidden() -> None:
    """Otherwise a pass whose captures overrun paces itself by accident."""
    from runners.run_reddit_grid_capture import _paced_wait

    row: dict = {}
    assert _paced_wait(planned=31.0, elapsed=42.0, basis="cycle", row=row) == 0.0
    assert row["cadence_overrun_seconds"] == 11.0


def test_unknown_cadence_basis_fails_closed(tmp_path) -> None:
    with pytest.raises(ValueError) as excinfo:
        run_reddit_grid_capture(
            subreddits=["testsub"],
            listing="top",
            time_window="week",
            output_root=tmp_path / "out",
            decision_question="q",
            cadence_basis="vibes",
        )
    assert "cadence_basis must be one of" in str(excinfo.value)


def test_www_capture_reuses_one_persistent_tab(monkeypatch, tmp_path) -> None:
    """One marked tab for the whole pass, not 91 open/close cycles."""
    import runners.run_reddit_grid_capture as module

    seen: list[dict] = []

    def _fake(**kwargs):
        seen.append(kwargs)
        return 0, str(tmp_path / "packet")

    monkeypatch.setattr(module, "run_source_capture_realchrome_cdp_packet", _fake, raising=False)
    monkeypatch.setattr(
        "runners.run_source_capture_realchrome_cdp_packet."
        "run_source_capture_realchrome_cdp_packet",
        _fake,
    )
    run_reddit_grid_capture(
        subreddits=["alpha", "beta"],
        listing="top",
        time_window="week",
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        delay_seconds=0,
    )
    assert len(seen) == 2
    markers = {call["persistent_tab_marker"] for call in seen}
    assert markers == {module.WWW_PERSISTENT_TAB_MARKER}
    # Same marker for every subreddit is what makes the tab persist; a distinct
    # marker per capture would silently reintroduce one tab per request.
    assert len(markers) == 1


def test_www_capture_binds_the_declared_listing_identity(monkeypatch, tmp_path) -> None:
    import runners.run_reddit_grid_capture as module

    seen: dict[str, object] = {}

    def _fake(**kwargs):
        seen.update(kwargs)
        return 0, str(tmp_path / "packet")

    monkeypatch.setattr(
        "runners.run_source_capture_realchrome_cdp_packet."
        "run_source_capture_realchrome_cdp_packet",
        _fake,
    )
    run_reddit_grid_capture(
        subreddits=["alpha"],
        listing="top",
        time_window="week",
        output_root=tmp_path / "out",
        decision_question="q",
        transport="www_realchrome",
        delay_seconds=0,
    )
    check = seen["target_identity_check"]
    assert callable(check)
    assert check("https://www.reddit.com/r/alpha/top/?t=week")
    assert not check("https://www.reddit.com/r/beta/top/?t=week")
    assert not check("https://www.reddit.com/r/alpha/hot/")


def test_old_http_cycle_basis_subtracts_capture_duration(monkeypatch, tmp_path) -> None:
    import runners.run_reddit_grid_capture as module

    now = [0.0]
    sleeps: list[float] = []

    def _capture(**_kwargs):
        now[0] += 25.0
        return 0, "packet"

    monkeypatch.setattr(module, "run_source_capture_http_packet", _capture)
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(module.time, "sleep", sleeps.append)
    run_reddit_grid_capture(
        subreddits=["alpha", "beta"],
        listing="top",
        time_window="week",
        output_root=tmp_path / "out",
        decision_question="q",
        transport="old_http",
        cadence_mode="fixed",
        cadence_basis="cycle",
        delay_seconds=40.0,
    )
    assert sleeps == [15.0]


def test_www_unrecognized_zero_row_shell_fails_projection_validation() -> None:
    with pytest.raises(GridProjectionAnomalyError, match="no_thread_rows"):
        build_validated_www_grid_content_record(
            rendered_dom="<html><body>Log in to continue</body></html>",
            visible_text="Log in to continue",
            final_url="https://www.reddit.com/r/testsub/top/?t=week",
            subreddit="testsub",
            listing_url="https://www.reddit.com/r/testsub/top/?t=week",
        )


def test_www_verified_empty_requires_the_declared_final_url() -> None:
    with pytest.raises(
        GridProjectionAnomalyError, match="empty_listing_final_url_mismatch"
    ):
        build_validated_www_grid_content_record(
            rendered_dom="<html><body></body></html>",
            visible_text="There are no posts in this community",
            final_url="https://www.reddit.com/r/other/top/?t=week",
            subreddit="testsub",
            listing_url="https://www.reddit.com/r/testsub/top/?t=week",
        )


def test_www_batch_exposes_content_extraction_failure(monkeypatch, tmp_path) -> None:
    import runners.run_reddit_grid_capture as module

    packet_path = tmp_path / "failure_packet"
    monkeypatch.setattr(
        module,
        "_capture_www_grid",
        lambda **_kwargs: (CONTENT_EXTRACTION_FAILED_EXIT_CODE, str(packet_path)),
    )
    output_root = tmp_path / "out"
    exit_code, summary_path = run_reddit_grid_capture(
        subreddits=["testsub"],
        listing="top",
        time_window="week",
        output_root=output_root,
        decision_question="q",
        transport="www_realchrome",
        delay_seconds=0,
    )
    assert exit_code == 0
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    assert summary["capture_success_count"] == 0
    assert summary["content_extraction_failure_count"] == 1
    assert summary["results"][0]["capture_exit"] == CONTENT_EXTRACTION_FAILED_EXIT_CODE
    assert summary["results"][0]["packet_path"] == str(packet_path)


def _packet_with_posture(posture: str, *file_names: str):
    return SimpleNamespace(
        preserved_files=[
            SimpleNamespace(
                relative_packet_path=f"raw/{index:02d}_{name}", sha256="unused"
            )
            for index, name in enumerate(file_names, start=1)
        ],
        source_slices=[
            SimpleNamespace(
                locator=known_fact("https://www.reddit.com/r/testsub/top/?t=week"),
                access_posture=known_fact(posture),
            )
        ],
    )


def test_www_metadata_filename_must_match_the_transport() -> None:
    packet = _packet_with_posture(
        "real_browser_cdp preserved rendered public page artifacts",
        "http_response_metadata.json",
    )
    with pytest.raises(RegistryRefreshError, match="realchrome_snapshot_metadata"):
        _resolve_grid_metadata_file(
            packet,
            expected_locator="https://www.reddit.com/r/testsub/top/?t=week",
        )


def test_www_metadata_rejects_conflicting_status_keys(tmp_path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "status": 200,
                "http_response_status": 403,
                "access_blocked": False,
                "rendered_access_classification": "no_block_marker",
                "final_url": "https://www.reddit.com/r/testsub/top/?t=week",
            }
        ),
        encoding="utf-8",
    )
    packet = _packet_with_posture(
        "real_browser_cdp preserved rendered public page artifacts"
    )
    with pytest.raises(RegistryRefreshError, match="unexpected status key"):
        _verify_successful_grid_response(
            packet=packet,
            metadata_path=metadata_path,
            expected_locator="https://www.reddit.com/r/testsub/top/?t=week",
            expected_subreddit="testsub",
        )


def test_www_access_failed_posture_cannot_match_success(tmp_path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "http_response_status": 200,
                "access_blocked": False,
                "rendered_access_classification": "no_block_marker",
                "method_category": "real_browser_cdp",
                "requested_url": "https://www.reddit.com/r/testsub/top/?t=week",
                "final_url": "https://www.reddit.com/r/testsub/top/?t=week",
            }
        ),
        encoding="utf-8",
    )
    packet = _packet_with_posture(
        "real_browser_cdp access_failed with access block reddit_network_security_block"
    )
    with pytest.raises(RegistryRefreshError, match="no successful source slice"):
        _verify_successful_grid_response(
            packet=packet,
            metadata_path=metadata_path,
            expected_locator="https://www.reddit.com/r/testsub/top/?t=week",
            expected_subreddit="testsub",
        )


def test_cli_passes_transport_and_endpoint_through(monkeypatch, tmp_path) -> None:
    """argparse accepting a flag proves nothing about it reaching the function.

    A live pass on 2026-07-31 was invoked with --transport www_realchrome and
    silently ran the old transport, because the flag was registered but never
    forwarded. Every function-level test still passed.
    """
    import runners.run_reddit_grid_capture as module

    seen: dict[str, object] = {}

    def _fake(**kwargs):
        seen.update(kwargs)
        return 0, "ok"

    monkeypatch.setattr(module, "run_reddit_grid_capture", _fake)
    module.main(
        [
            "--subreddit", "testsub",
            "--listing", "top",
            "--time-window", "week",
            "--transport", "www_realchrome",
            "--cdp-endpoint", "http://127.0.0.1:9223",
            "--output-root", str(tmp_path / "out"),
            "--decision-question", "q",
        ]
    )
    assert seen["transport"] == "www_realchrome"
    assert seen["cdp_endpoint"] == "http://127.0.0.1:9223"
