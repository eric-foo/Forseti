"""Text fidelity at both public Reddit content-record consumers."""
from __future__ import annotations

import pytest

from source_capture.reddit_consolidation import (
    build_thread_content_record,
    build_www_thread_content_record,
)


def _record(surface: str, body: str) -> dict:
    if surface == "old":
        html = f'''<div class="thing link" data-fullname="t3_thread">
          <div class="usertext-body"><div class="md">{body}</div></div>
        </div><div class="thing comment" data-fullname="t1_comment"
          data-parent="t3_thread" data-author="customer">
          <div class="usertext-body"><div class="md">{body}</div></div>
        </div>'''
        builder = build_thread_content_record
    else:
        html = f'''<shreddit-post id="t3_thread" post-title="Thread">
          <shreddit-post-text-body>{body}</shreddit-post-text-body>
        </shreddit-post><shreddit-comment-tree totalcomments="1">
          <shreddit-comment thingid="t1_comment" parentid="t3_thread"
            author="customer" depth="0"><div slot="comment">{body}</div>
          </shreddit-comment></shreddit-comment-tree>'''
        builder = build_www_thread_content_record
    return builder(html_text=html, source_url="https://www.reddit.com/comments/thread/")


@pytest.mark.parametrize("surface", ["old", "www"])
@pytest.mark.parametrize(("body", "expected"), [
    ('<p>Third tube of <search-telemetry-tracker>Instant Angel</search-telemetry-tracker>'
     ' and I love it. I use <em>tret</em> too.</p>',
     'Third tube of Instant Angel and I love it. I use tret too.'),
    ('<p>I <strong>do <em>not</em></strong> recommend it.</p>',
     'I do not recommend it.'),
    ('<p>A <a href="/x">moist</a>urizer &amp; balm.</p><p>Next<br>line.</p>',
     'A moisturizer & balm. Next line.'),
    ('<blockquote><p>It <em>burned</em> my skin.</p></blockquote>'
     '<p>That did not happen to me.</p>',
     '<blockquote> It burned my skin. </blockquote> That did not happen to me.'),
    ('<p>Before.</p><blockquote>Outer<blockquote>Inner</blockquote>Tail</blockquote>'
     '<p>After.</p>',
     'Before. <blockquote> Outer <blockquote> Inner </blockquote> Tail </blockquote> After.'),
    ('<blockquote><p> </p></blockquote><p>Own words.</p>', 'Own words.'),
])
def test_public_records_preserve_text_order_and_quote_boundaries(surface, body, expected):
    first = _record(surface, body)
    assert first == _record(surface, body)
    assert first["post"]["body_text"] == expected
    assert first["comments"][0]["body_text"] == expected
    assert first["comments"][0]["comment_id"] == "comment"
    assert first["comments"][0]["author_state"] == "customer"
    assert first["counts"]["comments_parsed"] == 1


@pytest.mark.parametrize("surface", ["old", "www"])
def test_empty_blockquote_does_not_invent_a_readable_comment(surface):
    record = _record(surface, '<blockquote><p> </p></blockquote>')
    assert record["comments"][0]["body_text"] == ""
    assert record["comments"][0]["comment_posture"] == "media_only"


@pytest.mark.parametrize(("surface", "expected_version"), [("old", "2"), ("www", "www-3")])
def test_corrected_projection_has_a_distinct_parser_identity(surface, expected_version):
    assert _record(surface, "Unformatted text.")["parser_version"] == expected_version


def test_old_title_uses_the_title_link_not_adjacent_flair_or_domain():
    record = build_thread_content_record(
        html_text='<div class="thing link" data-fullname="t3_thread">'
        '<p class="title"><a class="title">Sensitive <em>skin</em>?</a>'
        '<span>Product Request</span><span>(self.SkincareAddiction)</span></p></div>',
        source_url="https://old.reddit.com/comments/thread/",
    )
    assert record["thread"]["title"] == "Sensitive skin?"
