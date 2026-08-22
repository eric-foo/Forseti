"""New-Reddit (www) listing projection.

The inline fixture reproduces the shapes measured on real captures 2026-07-31,
each of which broke a naive parser:

- an image post whose ``content-href`` is the MEDIA url while ``permalink``
  holds the thread (preferring content-href dropped 64 of 102 real rows);
- an ad element, which carries no thread permalink and must stay out of both
  the row set and the thing count;
- the "Stickied post" icon, which new Reddit renders inside EVERY post and
  hides with a ``hidden`` class, so presence of the token is not the signal;
- the venue envelope, which is absent from the serialized DOM and read from
  visible text where the member and online counts abut with no separator.
"""

from __future__ import annotations

import pytest

from capture_spine.reddit_subreddit_grid.grid_projection import (
    grid_view_from_record,
    grid_view_projection_anomaly,
)
from capture_spine.reddit_subreddit_grid.www_grid_projection import (
    WWW_GRID_PROJECTION_PARSER_VERSION,
    build_www_grid_content_record,
    project_www_reddit_grid,
)

LISTING_URL = "https://www.reddit.com/r/testsub/top/?t=week"

# Every post carries the hidden stickied icon, exactly as the real surface does.
_HIDDEN_STICKY = (
    '<rpl-tooltip content="Stickied post">'
    '<svg aria-label="Stickied post" class="hidden stickied-status shrink-0"></svg>'
    "</rpl-tooltip>"
)
_SHOWN_STICKY = (
    '<rpl-tooltip content="Stickied post">'
    '<svg aria-label="Stickied post" class="stickied-status shrink-0"></svg>'
    "</rpl-tooltip>"
)


def _post(
    *,
    slug: str,
    title: str,
    score: str,
    comments: str,
    content_href: str | None = None,
    post_type: str = "self",
    domain: str = "self.testsub",
    preview_image_url: str | None = None,
    preview_alt_text: str = "",
    flair: str | None = None,
    sticky: bool = False,
) -> str:
    permalink = f"/r/testsub/comments/{slug}/{slug}_title/"
    href = content_href or f"https://www.reddit.com{permalink}"
    flair_markup = (
        f'<shreddit-post-flair><a href="/r/testsub/?f=flair_name%3A%22{flair}%22">'
        f"<span>{flair}</span></a></shreddit-post-flair>"
        if flair
        else ""
    )
    preview_markup = (
        f'<img src="{preview_image_url}" alt="{preview_alt_text}">'
        if preview_image_url
        else ""
    )
    return (
        f'<shreddit-post permalink="{permalink}" content-href="{href}"'
        f' post-type="{post_type}" domain="{domain}"'
        f' post-title="{title}" score="{score}" comment-count="{comments}"'
        f' created-timestamp="2026-07-24T01:11:13.173000+0000"'
        f' subreddit-prefixed-name="r/testsub" id="t3_{slug}">'
        f"{_SHOWN_STICKY if sticky else _HIDDEN_STICKY}"
        '<img src="https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png"'
        ' alt="u/example avatar">'
        f"{preview_markup}"
        f"{flair_markup}"
        f"<shreddit-post-overflow-menu></shreddit-post-overflow-menu>"
        f"</shreddit-post>"
    )


DOM = (
    "<html><body>"
    + _post(slug="aaa", title="Text post", score="893", comments="285", flair="Layering")
    + _post(
        slug="bbb",
        title="Image post",
        score="258",
        comments="173",
        content_href="https://i.redd.it/m57ff44vggfh1.jpeg",
        post_type="image",
        domain="i.redd.it",
        preview_image_url="https://preview.redd.it/m57ff44vggfh1.jpeg?width=640",
        preview_alt_text="r/testsub - Image post",
    )
    + _post(
        slug="ccc",
        title="Gallery post",
        score="14",
        comments="2",
        content_href="https://www.reddit.com/gallery/1v5nfk2",
        post_type="gallery",
        domain="reddit.com",
    )
    + '<shreddit-ad-post content-href="https://samsung.com" post-title="Ad"></shreddit-ad-post>'
    + "</body></html>"
)

VISIBLE_TEXT = "Created Mar 3, 2015 Public 701K7.4K R/TESTSUB RULES"


def _record():
    return build_www_grid_content_record(
        rendered_dom=DOM, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )


def test_permalink_wins_over_media_content_href() -> None:
    rows = _record()["grid_view"]["thread_rows"]
    urls = [row["thread_url"] for row in rows]
    assert urls == [
        "https://www.reddit.com/r/testsub/comments/aaa/aaa_title/",
        "https://www.reddit.com/r/testsub/comments/bbb/bbb_title/",
        "https://www.reddit.com/r/testsub/comments/ccc/ccc_title/",
    ]


def test_listing_visible_content_context_is_retained() -> None:
    rows = _record()["grid_view"]["thread_rows"]

    assert rows[0]["listing_post_type_or_none"] == "self"
    assert rows[0]["listing_content_url_or_none"].endswith("/comments/aaa/aaa_title/")
    assert rows[0]["listing_content_domain_or_none"] == "self.testsub"
    assert rows[1]["listing_post_type_or_none"] == "image"
    assert rows[1]["listing_content_url_or_none"] == "https://i.redd.it/m57ff44vggfh1.jpeg"
    assert rows[1]["listing_content_domain_or_none"] == "i.redd.it"
    assert rows[1]["listing_preview_image_url_or_none"] == (
        "https://preview.redd.it/m57ff44vggfh1.jpeg?width=640"
    )
    assert rows[1]["listing_preview_alt_text_or_none"] == "r/testsub - Image post"


def test_ads_are_excluded_from_rows_and_thing_count() -> None:
    """An ad in either count would trip the caller's row-count anomaly guard."""
    view = _record()["grid_view"]
    assert view["listing_thing_count_or_none"] == 3
    assert view["listing_permalink_count_or_none"] == 3
    assert len(view["thread_rows"]) == 3
    assert not any(row["promoted"] for row in view["thread_rows"])


def test_ad_with_reddit_permalink_is_still_excluded() -> None:
    """Observed 2026-08-22: promoted rows can now look like Reddit threads."""
    ad = (
        '<shreddit-ad-post permalink="/r/u_brand/comments/ad123/campaign/"'
        ' content-href="https://www.reddit.com/r/u_brand/comments/ad123/campaign/"'
        ' created-timestamp="2026-08-22T01:02:03.000000+0000"'
        ' post-title="Campaign"></shreddit-ad-post>'
    )
    view = build_www_grid_content_record(
        rendered_dom=DOM + ad,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )["grid_view"]
    assert view["listing_thing_count_or_none"] == 3
    assert view["listing_permalink_count_or_none"] == 3
    assert len(view["thread_rows"]) == 3
    # Counting alone would still pass if the ad displaced an organic row, so
    # name the ad's own canonical URL and require it to be absent.
    assert "https://www.reddit.com/r/u_brand/comments/ad123/campaign/" not in [
        row["thread_url"] for row in view["thread_rows"]
    ]
    assert not any(row["promoted"] for row in view["thread_rows"])


def test_duplicate_permalink_is_one_semantic_row() -> None:
    duplicate = _post(
        slug="aaa", title="Duplicate shell", score="1", comments="0"
    )
    view = build_www_grid_content_record(
        rendered_dom=DOM + f"<section>{duplicate}</section>",
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )["grid_view"]
    assert view["listing_thing_count_or_none"] == 3
    assert view["listing_permalink_count_or_none"] == 3
    assert len(view["thread_rows"]) == 3
    # First element wins: the later shell carries thinner values, and letting
    # it overwrite the row would silently downgrade score and comment count.
    assert view["thread_rows"][0]["visible_title_or_none"] == "Text post"
    assert view["thread_rows"][0]["visible_score_or_none"] == "893"


def test_nested_duplicate_post_element_is_one_semantic_row() -> None:
    """The Goal's nested case: the inner element repeats the outer's permalink."""
    outer = _post(slug="aaa", title="Outer", score="10", comments="5")
    inner = _post(slug="aaa", title="Nested duplicate", score="1", comments="0")
    nested_dom = outer.replace("</shreddit-post>", inner + "</shreddit-post>", 1)
    record = build_www_grid_content_record(
        rendered_dom=nested_dom,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    view = record["grid_view"]
    assert view["listing_thing_count_or_none"] == 1
    assert view["listing_permalink_count_or_none"] == 1
    assert [row["visible_title_or_none"] for row in view["thread_rows"]] == ["Outer"]
    assert grid_view_projection_anomaly(grid_view_from_record(record)) is None


def _unclosed(slug: str, title: str) -> str:
    """One organic post element whose end tag never arrives."""
    return _post(slug=slug, title=title, score="10", comments="5").replace(
        "</shreddit-post>", "", 1
    )


@pytest.mark.parametrize(
    "dom, titles",
    [
        (
            _unclosed("aaa", "A")
            + _post(slug="bbb", title="B", score="10", comments="5")
            + _post(slug="ccc", title="C", score="10", comments="5"),
            ["A", "B", "C"],
        ),
        (
            _post(slug="aaa", title="A", score="10", comments="5")
            + _unclosed("bbb", "B")
            + _post(slug="ccc", title="C", score="10", comments="5"),
            ["A", "B", "C"],
        ),
        (
            '<shreddit-ad-post content-href="https://ad.example/">'
            + _post(slug="aaa", title="A", score="10", comments="5")
            + _post(slug="bbb", title="B", score="10", comments="5"),
            ["A", "B"],
        ),
    ],
    ids=["first-post-unclosed", "middle-post-unclosed", "unclosed-ad-wrapper"],
)
def test_a_missing_end_tag_does_not_silently_swallow_later_posts(
    dom: str, titles: list[str]
) -> None:
    """Regression: absorbing siblings as "nested" loses rows the guard cannot see.

    A post element that never closes must not turn every following sibling into
    nested content.  That failure is invisible to the caller's guard, because a
    swallowed element leaves neither a row nor a thing count -- the two numbers
    the guard compares -- so the capture would be retained as complete while
    silently missing most of the listing.
    """
    record = build_www_grid_content_record(
        rendered_dom=dom,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    view = record["grid_view"]
    assert [row["visible_title_or_none"] for row in view["thread_rows"]] == titles
    assert view["listing_thing_count_or_none"] == len(titles)
    assert grid_view_projection_anomaly(grid_view_from_record(record)) is None


def test_malformed_organic_post_still_trips_the_row_count_guard() -> None:
    """Ad exclusion must not make the organic-row guard self-satisfying."""
    malformed = (
        '<shreddit-post permalink="/r/testsub/not-a-comments-thread/"'
        ' created-timestamp="2026-07-24T01:11:13.173000+0000">'
        "</shreddit-post>"
    )
    view = project_www_reddit_grid(
        rendered_dom=DOM + malformed,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    assert view.listing_thing_count_or_none == 4
    assert len(view.thread_rows) == 3
    assert grid_view_projection_anomaly(view) == "thread_row_count_mismatch"


def test_hidden_sticky_icon_does_not_mark_rows_stickied() -> None:
    assert not any(row["stickied"] for row in _record()["grid_view"]["thread_rows"])


def test_shown_sticky_icon_marks_only_that_row() -> None:
    dom = (
        "<html><body>"
        + _post(slug="aaa", title="Normal", score="10", comments="5")
        + _post(slug="bbb", title="Pinned", score="1", comments="0", sticky=True)
        + "</body></html>"
    )
    rows = build_www_grid_content_record(
        rendered_dom=dom, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]["thread_rows"]
    assert [row["stickied"] for row in rows] == [False, True]


def test_all_rows_stickied_remain_source_truth() -> None:
    """A small listing can genuinely consist only of pinned rows."""
    dom = (
        "<html><body>"
        + _post(slug="aaa", title="One", score="10", comments="5", sticky=True)
        + _post(slug="bbb", title="Two", score="9", comments="4", sticky=True)
        + "</body></html>"
    )
    rows = build_www_grid_content_record(
        rendered_dom=dom, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]["thread_rows"]
    assert [row["stickied"] for row in rows] == [True, True]


def test_weekly_reach_is_read_from_the_header_attributes_not_the_text() -> None:
    """Exact integers under Reddit's own names, not positional text guessing.

    Verified against the real preserved capture of r/newinbeauty (2026-07-31):
    weekly-active-users=34364, weekly-contributions=616, which the sidebar
    renders as "34K" and "616" under labels that live in shadow DOM and never
    reach the visible text.
    """
    dom = (
        '<shreddit-subreddit-header name="testsub" weekly-active-users="34364"'
        ' weekly-contributions="616"></shreddit-subreddit-header>' + DOM
    )
    view = build_www_grid_content_record(
        rendered_dom=dom, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]
    assert view["weekly_visitor_count_or_none"] == "34364"
    assert view["weekly_contribution_count_or_none"] == "616"


def test_header_buttons_element_does_not_satisfy_the_header_read() -> None:
    """shreddit-subreddit-header-buttons carries neither count."""
    dom = '<shreddit-subreddit-header-buttons name="testsub"></shreddit-subreddit-header-buttons>' + DOM
    view = build_www_grid_content_record(
        rendered_dom=dom, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]
    assert view["weekly_visitor_count_or_none"] is None


def test_venue_envelope_does_not_claim_a_subscriber_count() -> None:
    """The abutting numbers are WEEKLY VISITORS/CONTRIBUTIONS, not subscribers.

    Measured 2026-07-31: www renders 701K/7.4K for r/30PlusSkinCare, matching the
    operator community-panel reading of 702K weekly visitors and 7.6K weekly
    contributions, while about.json put subscribers at 2,420,271. Reading them as
    subscribers wrote a 3.5x-wrong value into the series the deferred breakout
    rule uses as its normalizer.
    """
    dom = (
        '<shreddit-subreddit-header name="testsub" weekly-active-users="34364"'
        ' weekly-contributions="616"></shreddit-subreddit-header>' + DOM
    )
    view = build_www_grid_content_record(
        rendered_dom=dom, visible_text=VISIBLE_TEXT, subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]
    assert view["visible_subscriber_count_or_none"] is None
    assert view["visible_active_user_count_or_none"] is None
    assert (
        view["visible_volume_signal_absent_reason_or_none"]
        == "www_venue_envelope_exposes_weekly_reach_not_subscriber_counts"
    )
    # The creation date IS a subscriber-independent fact and still projects.
    assert view["created_utc_or_none"] == "2015-03-03"


def test_absent_venue_envelope_carries_an_absent_reason() -> None:
    view = build_www_grid_content_record(
        rendered_dom=DOM, visible_text="no envelope here", subreddit="testsub", listing_url=LISTING_URL
    )["grid_view"]
    assert view["visible_subscriber_count_or_none"] is None
    assert (
        view["visible_volume_signal_absent_reason_or_none"]
        == "visible_volume_not_present_on_declared_surface"
    )


def test_creation_date_without_weekly_metrics_does_not_claim_the_metrics() -> None:
    view = build_www_grid_content_record(
        rendered_dom=DOM,
        visible_text="Created Mar 3, 2015 Public",
        subreddit="testsub",
        listing_url=LISTING_URL,
    )["grid_view"]
    assert view["created_utc_or_none"] == "2015-03-03"
    assert (
        view["visible_volume_signal_absent_reason_or_none"]
        == "visible_volume_not_present_on_declared_surface"
    )


def test_flair_and_timestamp_are_projected() -> None:
    rows = _record()["grid_view"]["thread_rows"]
    assert rows[0]["flair_or_none"] == "Layering"
    assert rows[1]["flair_or_none"] is None
    # 2026-07-24T01:11:13.173Z, cross-checked against calendar.timegm rather
    # than against the parser's own output.
    assert rows[0]["timestamp_utc_ms_or_none"] == "1784855473173"


def test_percent_encoded_flair_is_decoded_in_full() -> None:
    dom = _post(
        slug="aaa",
        title="Encoded flair",
        score="10",
        comments="5",
        flair="Ask%20Me",
    )
    row = build_www_grid_content_record(
        rendered_dom=dom,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )["grid_view"]["thread_rows"][0]
    assert row["flair_or_none"] == "Ask Me"


def test_timezone_naive_timestamp_stays_absent() -> None:
    """Naive datetime.timestamp() would vary with the projection host timezone."""
    dom = _post(slug="aaa", title="Naive time", score="10", comments="5").replace(
        "+0000", ""
    )
    record = build_www_grid_content_record(
        rendered_dom=dom,
        visible_text=VISIBLE_TEXT,
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    row = record["grid_view"]["thread_rows"][0]
    assert row["timestamp_utc_ms_or_none"] is None
    assert grid_view_projection_anomaly(grid_view_from_record(record)) == "no_timestamps"


def test_record_reuses_the_shared_kind_and_folds_through_the_materializer_path() -> None:
    """A second record kind would force changes down the whole consumer chain."""
    record = _record()
    assert record["parser_version"] == WWW_GRID_PROJECTION_PARSER_VERSION
    view = grid_view_from_record(record)
    assert view.subreddit == "testsub"
    assert len(view.thread_rows) == 3


def test_a_quiet_week_projects_as_an_honest_zero_not_an_anomaly() -> None:
    """Reddit's real empty-feed wording, observed 2026-07-31.

    The marker list was previously three GUESSED phrasings, none of which
    matched, so four genuinely quiet subreddits were classified as a parser
    anomaly and refused at the fold. For a weekly demand radar a quiet week is
    signal, not failure.
    """
    view = project_www_reddit_grid(
        rendered_dom=(
            '<shreddit-subreddit-header name="testsub" weekly-active-users="12751"'
            ' weekly-contributions="19"></shreddit-subreddit-header>'
        ),
        visible_text=(
            "r/testsub Create Post This community doesn't have any posts yet "
            "Make one and get this feed started. Created Mar 17, 2013 Restricted"
        ),
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    assert view.thread_rows == ()
    assert view.verified_empty_listing is True
    assert grid_view_projection_anomaly(view) is None
    # A quiet week still reports the venue's reach.
    assert view.weekly_visitor_count_or_none == "12751"


def test_zero_rows_without_an_empty_marker_is_not_a_verified_empty_listing() -> None:
    """A block or unhydrated shell must not read as an authentic empty listing."""
    view = project_www_reddit_grid(
        rendered_dom="<html><body>blocked</body></html>",
        visible_text="You've been blocked by network security.",
        subreddit="testsub",
        listing_url=LISTING_URL,
    )
    assert view.thread_rows == ()
    assert view.verified_empty_listing is False


@pytest.mark.parametrize("name", ["", "has space", "../escape"])
def test_invalid_subreddit_fails_closed(name: str) -> None:
    with pytest.raises(Exception):
        project_www_reddit_grid(
            rendered_dom=DOM, visible_text=VISIBLE_TEXT, subreddit=name, listing_url=LISTING_URL
        )
