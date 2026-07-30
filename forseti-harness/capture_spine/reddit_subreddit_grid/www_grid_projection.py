"""Mechanical projection of one new-Reddit (www) subreddit listing page.

Sibling of ``grid_projection`` for the ``www.reddit.com`` surface, written
because ``old.reddit.com`` stopped serving this client on 2026-07-30 (every
transport -- direct HTTP, CloakBrowser, and operator real Chrome -- received a
byte-identical network-security block, while www rendered normally).

It deliberately emits the SAME ``GridView``/``GridThreadRow`` shape and the
same ``record_kind`` as the old-Reddit projection, distinguished only by
``parser_version`` and by the packet's ``source_surface``.  The materializer,
the weekly reader, and the listing-efficiency selection policy all consume
``grid_view_from_record``; a second record kind would force changes through
that whole chain for a set of identical fields.

Two source artifacts are required, unlike the old surface:

- the rendered DOM carries the thread rows as ``<shreddit-post>`` custom
  elements whose attributes are already typed (score, comment-count,
  created-timestamp, permalink), which is strictly more machine-readable than
  the old-Reddit markup this replaces; and
- the venue envelope (creation date, member and online counts) is NOT in the
  serialized DOM -- it renders through shadow DOM -- so it is read from the
  captured visible text.

Measured constraint (2026-07-31): the www feed is VIRTUALIZED.  Scrolling
unloads the head rather than accumulating it; six scroll passes on r/fragrance
left only ``feedindex`` 170-183 with unhydrated scores.  The no-scroll viewport
carries ``feedindex`` 0..~31, which is the head the weekly method reads, so
this projection is designed against a single no-scroll capture and callers must
not scroll to seek depth.

The projection is read-only and mechanical: source-visible values are carried
as strings, absence is carried as ``None`` plus an absent reason, and nothing
here ranks, scores quality, or claims demand.
"""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import unquote

from capture_spine.reddit_subreddit_grid.grid_projection import (
    GRID_CONTENT_RECORD_KIND,
    GridThreadRow,
    GridView,
    RedditGridProjectionError,
    grid_view_to_dict,
)
from source_capture.projection_shared import canonical_www_reddit_thread_url

# Namespaced so a content record written by this parser can never be mistaken
# for one written by the old-Reddit parser at the same record kind.  Bump on
# ANY behavior change here, for the same reason the old parser bumps.
WWW_GRID_PROJECTION_PARSER_VERSION = "www-2"

# The old-Reddit projection caps at 100 because its URL asked for limit=100, so
# the cap and the page agreed.  On www the rendered VIEWPORT is the bound (a
# 1280x20000 window renders ~102 rows), and a second, tighter cap would make
# listing_thing_count exceed the row count on an ordinary capture -- which the
# caller's anomaly guard reads as a broken parser.  This is a runaway ceiling
# well above the observed window, not a depth policy; if it ever binds, the
# resulting mismatch deliberately routes the packet to raw for inspection.
WWW_MAX_THREAD_ROWS = 250

_POST_TAG = "shreddit-post"
_AD_TAG = "shreddit-ad-post"
_FLAIR_TAG = "shreddit-post-flair"

# The venue envelope flattens to e.g. "Created Mar 3, 2015 Public 701K7.4K":
# members and online counts abut with no separator, so each is matched as one
# number-plus-magnitude token rather than split on whitespace.
_VENUE_RE = re.compile(
    r"Created\s+(?P<created>[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+"
    r"(?:Public|Private|Restricted)\s*"
    r"(?P<members>\d[\d.,]*[KMB]?)?(?P<online>\d[\d.,]*[KMB]?)?"
)

# Flair name is URL-encoded inside the flair link's href
# (?f=flair_name%3A%22Layering%22).  Reading it there avoids depending on the
# nested span markup that carries the same text with styling wrappers.
_FLAIR_HREF_RE = re.compile(
    r"flair_name%3A%22(?P<flair>.*?)%22",
    flags=re.IGNORECASE,
)

# A new-Reddit listing renders the "Stickied post" icon inside EVERY post and
# hides it with a `hidden` class.  Presence of the markup is therefore not the
# signal -- absence of `hidden` on the stickied-status element is.  Matching the
# token alone would mark every row stickied and silently empty the deep-dive
# queue, since the selection policy drops stickied rows.
_STICKIED_CLASS_RE = re.compile(r'class="([^"]*\bstickied-status\b[^"]*)"')

_EMPTY_LISTING_MARKERS = (
    "there are no posts in this community",
    "nothing here",
    "no posts in r/",
)


def _decode_created_date(raw: str) -> str | None:
    """'Mar 3, 2015' -> '2015-03-03'; unparseable input stays absent."""
    try:
        return datetime.strptime(raw.strip(), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def _timestamp_utc_ms(raw: str | None) -> str | None:
    """ISO created-timestamp -> epoch-millisecond string, matching the old row shape."""
    if not raw:
        return None
    text = raw.strip().replace("+0000", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        # ``datetime.timestamp`` interprets a naive value in the host timezone,
        # which would make this otherwise-pure projection environment-dependent.
        return None
    return str(int(moment.timestamp() * 1000))


class _WwwRedditGridParser(HTMLParser):
    """Collect one row per ``shreddit-post``/``shreddit-ad-post`` element.

    ``HTMLParser`` reports exact tag names, so ``shreddit-post`` never matches
    the ``shreddit-post-overflow-menu``/``shreddit-post-flair`` siblings that a
    substring or regex scan would sweep up.
    """

    def __init__(self, *, declared_subreddit: str) -> None:
        super().__init__(convert_charrefs=True)
        self.declared_subreddit = declared_subreddit
        self.thread_rows: list[GridThreadRow] = []
        self.listing_thing_count = 0
        self.listing_permalink_count = 0
        self._open: dict[str, str] | None = None
        self._open_promoted = False
        self._open_flair: str | None = None
        self._open_stickied = False
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: (value or "") for key, value in attrs}
        if tag in (_POST_TAG, _AD_TAG):
            self._finish()
            self._open = attributes
            self._open_promoted = tag == _AD_TAG
            self._open_flair = None
            self._open_stickied = False
            self._depth = 1
            # Ads are deliberately outside the thing count.  New-Reddit ad
            # elements carry no thread permalink, so they can never become
            # rows, and counting them would make thing_count exceed the row
            # count on every capture -- which the caller's projection-anomaly
            # guard reads as a broken parser and falls back to raw for.  The
            # selection policy already excludes promoted rows, so nothing
            # decision-relevant is lost by leaving them out of both.
            if tag == _POST_TAG:
                self.listing_thing_count += 1
            return
        if self._open is None:
            return
        self._depth += 1
        if tag == _FLAIR_TAG and self._open_flair is None:
            # The flair element's own attributes do not carry the name; it is
            # read from the child link in handle_startendtag/starttag below.
            return
        href = attributes.get("href", "")
        if self._open_flair is None and "flair_name%3A%22" in href:
            match = _FLAIR_HREF_RE.search(href)
            if match:
                self._open_flair = unquote(match.group("flair")).strip() or None
        css = attributes.get("class", "")
        if "stickied-status" in css and "hidden" not in css.split():
            self._open_stickied = True

    def handle_endtag(self, tag: str) -> None:
        if self._open is None:
            return
        if tag in (_POST_TAG, _AD_TAG):
            self._finish()
            return
        self._depth -= 1

    def close(self) -> None:  # pragma: no cover - exercised via feed/close
        super().close()
        self._finish()

    def _finish(self) -> None:
        attributes, self._open = self._open, None
        if attributes is None:
            return
        # ``permalink`` first, and it is the only reliable source: on image and
        # gallery posts ``content-href`` is the MEDIA url (i.redd.it/... ,
        # /gallery/...), not the thread.  Preferring content-href silently
        # dropped 64 of 102 rows on an image-heavy subreddit because those
        # media urls fail the /comments/ canonicalization.
        thread_url = canonical_www_reddit_thread_url(
            attributes.get("permalink") or attributes.get("content-href") or ""
        )
        if thread_url is None:
            return
        self.listing_permalink_count += 1
        prefixed = attributes.get("subreddit-prefixed-name") or ""
        subreddit = prefixed.removeprefix("r/").strip().lower() or self.declared_subreddit
        self.thread_rows.append(
            GridThreadRow(
                thread_url=thread_url,
                subreddit=subreddit,
                visible_title_or_none=(attributes.get("post-title") or "").strip() or None,
                visible_score_or_none=(attributes.get("score") or "").strip() or None,
                visible_comment_count_or_none=(attributes.get("comment-count") or "").strip() or None,
                promoted=self._open_promoted,
                timestamp_utc_ms_or_none=_timestamp_utc_ms(attributes.get("created-timestamp")),
                stickied=self._open_stickied,
                flair_or_none=self._open_flair,
            )
        )


def project_www_reddit_grid(
    *,
    rendered_dom: str,
    visible_text: str,
    subreddit: str,
    listing_url: str,
    max_thread_rows: int = WWW_MAX_THREAD_ROWS,
) -> GridView:
    """Project one www listing capture into the shared grid view."""
    if not subreddit.isascii() or not subreddit.replace("_", "").isalnum():
        raise RedditGridProjectionError(
            "invalid_subreddit", f"invalid subreddit name: {subreddit!r}"
        )
    if max_thread_rows <= 0:
        raise RedditGridProjectionError("invalid_cap", "max_thread_rows must be greater than zero")

    parser = _WwwRedditGridParser(declared_subreddit=subreddit.lower())
    parser.feed(rendered_dom)
    parser.close()

    rows: list[GridThreadRow] = []
    seen: set[str] = set()
    for row in parser.thread_rows:
        if row.thread_url in seen:
            continue
        rows.append(row)
        seen.add(row.thread_url)
        if len(rows) >= max_thread_rows:
            break

    venue = _VENUE_RE.search(visible_text or "")
    members = venue.group("members") if venue else None
    online = venue.group("online") if venue else None
    created = _decode_created_date(venue.group("created")) if venue else None

    absent_reason = None
    if members is None and online is None:
        absent_reason = "visible_volume_not_present_on_declared_surface"

    lowered = (visible_text or "").lower()
    return GridView(
        subreddit=subreddit.lower(),
        listing_url=listing_url,
        visible_subscriber_count_or_none=members,
        visible_active_user_count_or_none=online,
        visible_volume_signal_absent_reason_or_none=absent_reason,
        thread_rows=tuple(rows),
        created_utc_or_none=created,
        listing_thing_count_or_none=parser.listing_thing_count,
        listing_permalink_count_or_none=parser.listing_permalink_count,
        verified_empty_listing=(
            parser.listing_thing_count == 0
            and any(marker in lowered for marker in _EMPTY_LISTING_MARKERS)
        ),
    )


def build_www_grid_content_record(
    *,
    rendered_dom: str,
    visible_text: str,
    subreddit: str,
    listing_url: str,
) -> dict:
    """Project one www listing capture into the deterministic packet record.

    Pure function of its inputs (no timestamps, no environment reads) so a
    qualification run can re-extract scratch raw bytes and compare the result
    byte-for-byte against the stored record.
    """
    view = project_www_reddit_grid(
        rendered_dom=rendered_dom,
        visible_text=visible_text,
        subreddit=subreddit,
        listing_url=listing_url,
    )
    return {
        "record_kind": GRID_CONTENT_RECORD_KIND,
        "parser_version": WWW_GRID_PROJECTION_PARSER_VERSION,
        "grid_view": grid_view_to_dict(view),
    }


__all__ = [
    "WWW_GRID_PROJECTION_PARSER_VERSION",
    "build_www_grid_content_record",
    "project_www_reddit_grid",
]
