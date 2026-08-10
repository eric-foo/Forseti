"""Behaviour bound for the thread batch runner's www transport.

Includes a test that drives ``main()``. An earlier transport flag on the grid
runner was registered on the parser and never forwarded, so every "www" pass
silently ran the old transport; only a test that goes through argv catches
that class of defect.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners import run_reddit_old_http_batch as batch

WWW_URL = "https://www.reddit.com/r/Sephora/comments/1v87d9j/talc/"
OLD_URL = "https://old.reddit.com/r/Sephora/comments/1v87d9j/talc/"


def test_url_host_bound_follows_the_selected_transport():
    assert batch._validate_thread_url(OLD_URL, transport="old_http") == OLD_URL
    assert batch._validate_thread_url(WWW_URL, transport="www_realchrome") == WWW_URL
    with pytest.raises(ValueError, match="old.reddit.com"):
        batch._validate_thread_url(WWW_URL, transport="old_http")
    with pytest.raises(ValueError, match="www.reddit.com"):
        batch._validate_thread_url(OLD_URL, transport="www_realchrome")


def test_a_non_thread_url_is_refused_on_either_transport():
    for transport, url in (
        ("old_http", "https://old.reddit.com/r/Sephora/"),
        ("www_realchrome", "https://www.reddit.com/r/Sephora/"),
    ):
        with pytest.raises(ValueError, match="/comments/"):
            batch._validate_thread_url(url, transport=transport)


def test_www_transport_refuses_raw_retention(tmp_path):
    # The Reddit lane binds never-raw-only; a raw www capture would retain more
    # than the lane allows and preserve nothing the deep read consumes.
    with pytest.raises(ValueError, match="never-raw-only"):
        batch.run_reddit_old_http_batch(
            slots=[batch.BatchSlot(slot_id="s1", url=WWW_URL)],
            output_root=tmp_path / "out",
            decision_question="q",
            transport="www_realchrome",
            requested_retention_mode="raw",
        )


def test_unknown_transport_is_refused(tmp_path):
    with pytest.raises(ValueError, match="transport must be one of"):
        batch.run_reddit_old_http_batch(
            slots=[batch.BatchSlot(slot_id="s1", url=OLD_URL)],
            output_root=tmp_path / "out",
            decision_question="q",
            transport="carrier_pigeon",
        )


def test_main_forwards_the_transport_to_the_runner(tmp_path, monkeypatch):
    url_list = tmp_path / "urls.json"
    url_list.write_text(json.dumps([WWW_URL]), encoding="utf-8")
    seen: dict = {}

    def fake_run(**kwargs):
        seen.update(kwargs)
        return 0, "ok"

    monkeypatch.setattr(batch, "run_reddit_old_http_batch", fake_run)
    exit_code = batch.main(
        [
            "--url-list", str(url_list),
            "--output-root", str(tmp_path / "out"),
            "--decision-question", "q",
            "--transport", "www_realchrome",
            "--cdp-endpoint", "http://127.0.0.1:9999",
        ]
    )
    assert exit_code == 0
    assert seen["transport"] == "www_realchrome"
    assert seen["cdp_endpoint"] == "http://127.0.0.1:9999"
    # The slot list must be validated against the www host, not old.reddit.
    assert [slot.url for slot in seen["slots"]] == [WWW_URL]


def test_main_defaults_to_the_old_transport(tmp_path, monkeypatch):
    url_list = tmp_path / "urls.json"
    url_list.write_text(json.dumps([OLD_URL]), encoding="utf-8")
    seen: dict = {}
    monkeypatch.setattr(
        batch, "run_reddit_old_http_batch", lambda **kw: (seen.update(kw), (0, "ok"))[1]
    )
    batch.main(
        [
            "--url-list", str(url_list),
            "--output-root", str(tmp_path / "out"),
            "--decision-question", "q",
        ]
    )
    assert seen["transport"] == "old_http"


def test_rendered_but_empty_comment_tree_is_refused_as_an_anomaly():
    # A shell that declares comments and renders none must keep raw for audit
    # rather than ship a zero-comment record for a busy thread.
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p"
      author="a" created-timestamp="2026-01-01T00:00:00+0000" score="5">
    </shreddit-post>
    <shreddit-comment-tree totalcomments="198"></shreddit-comment-tree>
    """
    with pytest.raises(
        batch.ThreadProjectionAnomalyError, match="declared_comments_none_rendered"
    ):
        batch.build_validated_www_thread_content_record(
            html_text=html, source_url="u"
        )


def test_a_genuinely_empty_thread_is_not_treated_as_an_anomaly():
    # Zero declared and zero rendered is an honest zero, not a block shell.
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p"
      author="a" created-timestamp="2026-01-01T00:00:00+0000" score="5">
    </shreddit-post>
    <shreddit-comment-tree totalcomments="0"></shreddit-comment-tree>
    """
    record = batch.build_validated_www_thread_content_record(
        html_text=html, source_url="u"
    )
    assert record["counts"]["comments_parsed"] == 0
    assert record["comment_completeness"]["captured_matches_declared_total"] is True
    assert record["comment_completeness"]["capture_is_complete"] is None


def test_www_summary_does_not_claim_it_avoided_browser_automation():
    # The www transport drives real Chrome and clicks expansion controls.
    from source_capture.reddit_consolidation import WWW_REDDIT_THREAD_PARSER_VERSION

    assert WWW_REDDIT_THREAD_PARSER_VERSION.startswith("www-")
    assert batch.TRANSPORT_SOURCE_SURFACES["www_realchrome"] == "www_reddit_realchrome_cdp"
    assert batch.TRANSPORT_HOSTS["www_realchrome"] == "www.reddit.com"


def test_grid_cli_preserves_the_lane_cadence_defaults():
    from runners import run_reddit_grid_capture as grid

    args = grid._build_parser().parse_args(
        ["--subreddit", "Sephora", "--output-root", "out", "--decision-question", "q"]
    )
    assert args.cadence_mode == grid.DEFAULT_CADENCE_MODE
    assert args.cadence_basis == grid.DEFAULT_CADENCE_BASIS
