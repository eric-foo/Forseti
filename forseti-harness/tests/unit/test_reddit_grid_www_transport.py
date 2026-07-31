"""www transport selection on the Reddit grid runner.

The roster, cadence, batch summary, and duplicate checks are transport-agnostic
and stay single-homed; only URL shape, extraction spec, and capture call differ.
"""

from __future__ import annotations

import pytest

from runners.run_reddit_grid_capture import (
    GRID_TRANSPORTS,
    build_grid_listing_url,
    build_www_grid_listing_url,
    run_reddit_grid_capture,
)


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
