"""Behaviour bound for the new-Reddit (www) thread projection.

The fixture is a real capture (r/Sephora ``1v87d9j``, 2026-08-01) trimmed to a
handful of comment subtrees; attributes and nesting are verbatim.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from source_capture.reddit_consolidation import (
    THREAD_CONTENT_RECORD_KIND,
    WWW_REDDIT_THREAD_PARSER_VERSION,
    build_www_thread_content_record,
    parse_www_reddit_html,
)
from source_capture.reddit_consolidation.parser import RedditParseFailure

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "reddit_thread"
    / "www_sephora_talc_thread.html"
)


@pytest.fixture(scope="module")
def record() -> dict:
    return build_www_thread_content_record(
        html_text=FIXTURE.read_text(encoding="utf-8"),
        source_url="https://www.reddit.com/r/Sephora/comments/1v87d9j/x/",
    )


def test_record_kind_matches_the_old_surface_and_only_the_parser_differs(record):
    # The whole point of the port: every downstream consumer of a thread
    # content record keeps working, and the surface is told apart by version.
    assert record["record_kind"] == THREAD_CONTENT_RECORD_KIND
    assert record["parser_version"] == WWW_REDDIT_THREAD_PARSER_VERSION
    assert WWW_REDDIT_THREAD_PARSER_VERSION != "1"


def test_thread_identity_reads_named_attributes(record):
    assert record["thread"] == {
        "thread_id": "1v87d9j",
        "subreddit": "Sephora",
        "title": "This talc-free trend is terrible for me.",
        "permalink": "/r/Sephora/comments/1v87d9j/this_talcfree_trend_is_terrible_for_me/",
    }
    assert record["post"]["score_state"] == "366"
    assert record["post"]["author_state"] == "Weird_Spend_8097"
    assert record["post"]["timestamp_state"].startswith("2026-07-27T")
    assert "talc" in record["post"]["body_text"]


def test_comment_threading_carries_parent_and_depth(record):
    by_id = {c["comment_id"]: c for c in record["comments"]}
    child = by_id["p08z7g3"]
    assert child["parent_id"] == "p08z2os"
    assert child["depth"] == 1
    assert by_id["p08z2os"]["parent_id"] is None
    assert by_id["p08z2os"]["depth"] == 0


def test_a_reply_body_is_not_folded_into_its_parent(record):
    # www nests replies as real child elements, so an unguarded DOM walk would
    # concatenate the whole subtree into the top-level comment's body.
    by_id = {c["comment_id"]: c for c in record["comments"]}
    for comment in record["comments"]:
        parent = by_id.get(comment["parent_id"] or "")
        if parent is None or len(comment["body_text"]) <= 25:
            continue
        assert comment["body_text"] not in parent["body_text"], (
            f"{comment['comment_id']} body leaked into parent {parent['comment_id']}"
        )


def test_postures_come_from_the_sources_own_markers(record):
    by_id = {c["comment_id"]: c for c in record["comments"]}
    assert by_id["p05nen2"]["comment_posture"] == "deleted"  # is-author-deleted
    assert by_id["p07srd9"]["comment_posture"] == "collapsed"  # collapsed
    assert by_id["p08z2os"]["comment_posture"] == "present"


def test_deleted_author_marker_does_not_erase_a_present_comment_body():
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p">
    </shreddit-post>
    <shreddit-comment-tree totalcomments="2">
      <shreddit-comment thingid="t1_present" author="[deleted]" is-author-deleted>
        <div id="t1_present-comment-rtjson-content" slot="comment">still visible</div>
      </shreddit-comment>
      <shreddit-comment thingid="t1_deleted" author="[deleted]" is-comment-deleted>
      </shreddit-comment>
    </shreddit-comment-tree>
    """
    comments = build_www_thread_content_record(html_text=html, source_url="u")[
        "comments"
    ]
    assert comments[0]["comment_posture"] == "present"
    assert comments[0]["body_text"] == "still visible"
    assert comments[1]["comment_posture"] == "deleted"


def test_completeness_states_the_shortfall_rather_than_implying_none(record):
    completeness = record["comment_completeness"]
    assert completeness["basis"] == "shreddit-comment-tree[totalcomments]"
    assert completeness["declared_total_comments"] == 198
    captured = completeness["comments_captured"]
    # Literal fixture facts, rather than values re-derived from this parser:
    # the trimmed DOM carries 26 comment elements and 19 unique nofollow
    # continuation targets (four targets are rendered twice).
    assert captured == 26
    assert captured == record["counts"]["comments_parsed"]
    assert completeness["comments_not_captured"] == 172
    assert completeness["captured_matches_declared_total"] is False
    assert completeness["capture_is_complete"] is False
    assert completeness["continuation_links_not_followed"] == 19
    assert completeness["continuation_reason"]
    # The shortfall must also be visible to a reader who only skims warnings.
    assert any("198" in warning for warning in record["warnings"])


def test_absent_comment_tree_reports_unknown_completeness_not_zero():
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p"
      author="a" created-timestamp="2026-01-01T00:00:00+0000" score="5">
    </shreddit-post>
    """
    record = build_www_thread_content_record(html_text=html, source_url="u")
    completeness = record["comment_completeness"]
    # No declared total means completeness is UNKNOWN. Reporting 0 missing here
    # would assert a completeness the page never stated.
    assert completeness["declared_total_comments"] is None
    assert completeness["comments_not_captured"] is None
    assert completeness["captured_matches_declared_total"] is None
    assert completeness["capture_is_complete"] is None
    assert completeness["basis"] is None
    assert any("no_comment_tree_total" in item for item in record["limitations"])


def test_declared_count_match_is_not_promoted_to_completeness_proof():
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p">
    </shreddit-post>
    <shreddit-comment-tree totalcomments="1">
      <shreddit-comment thingid="t1_one" author="a">
        <div id="t1_one-comment-rtjson-content" slot="comment">one</div>
      </shreddit-comment>
    </shreddit-comment-tree>
    """
    record = build_www_thread_content_record(html_text=html, source_url="u")
    completeness = record["comment_completeness"]
    assert completeness["comments_not_captured"] == 0
    assert completeness["captured_matches_declared_total"] is True
    assert completeness["capture_is_complete"] is None
    assert any("not_independent_completeness_oracle" in item for item in record["limitations"])


def test_captured_count_above_declared_total_is_an_unknown_mismatch_not_zero_gap():
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p">
    </shreddit-post>
    <shreddit-comment-tree totalcomments="1">
      <shreddit-comment thingid="t1_one" author="a"></shreddit-comment>
      <shreddit-comment thingid="t1_two" author="b"></shreddit-comment>
    </shreddit-comment-tree>
    """
    record = build_www_thread_content_record(html_text=html, source_url="u")
    completeness = record["comment_completeness"]
    assert completeness["comments_not_captured"] is None
    assert completeness["captured_matches_declared_total"] is False
    assert completeness["capture_is_complete"] is None
    assert any("exceed" in warning for warning in record["warnings"])


def test_comment_count_is_scoped_to_the_declared_comment_tree():
    html = """
    <shreddit-post id="t3_abc" subreddit-name="X" post-title="T" permalink="/p">
    </shreddit-post>
    <shreddit-comment thingid="t1_unrelated" author="sidebar"></shreddit-comment>
    <shreddit-comment-tree totalcomments="1">
      <shreddit-comment thingid="t1_in_tree" author="a"></shreddit-comment>
    </shreddit-comment-tree>
    """
    record = build_www_thread_content_record(html_text=html, source_url="u")
    assert [comment["comment_id"] for comment in record["comments"]] == ["in_tree"]


def test_a_page_without_a_post_envelope_fails_closed():
    with pytest.raises(RedditParseFailure) as excinfo:
        parse_www_reddit_html("<html><body>Log in to continue</body></html>")
    assert excinfo.value.code == "required_thread_envelope_missing"


def test_projection_is_a_pure_function_of_its_inputs(record):
    again = build_www_thread_content_record(
        html_text=FIXTURE.read_text(encoding="utf-8"),
        source_url="https://www.reddit.com/r/Sephora/comments/1v87d9j/x/",
    )
    # Ephemeral qualification re-projects sampled bytes and compares them to the
    # stored record, so any clock or environment read here would break it.
    assert again == record
