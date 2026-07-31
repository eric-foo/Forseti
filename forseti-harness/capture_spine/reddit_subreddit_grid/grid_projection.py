"""Mechanical projection of one old Reddit subreddit listing (grid) page.

One grid page carries both radar layers at once:

- the venue envelope (titlebox subscriber / active-user counts when the
  subreddit's markup exposes them), and
- the thread grid (one row per listing ``thing`` with visible engagement:
  score and comment count).

The projection is read-only and mechanical: source-visible values are
carried as strings, absence is carried as ``None`` plus an absent reason,
and nothing here ranks, scores quality, or claims demand.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlsplit

from source_capture.projection_shared import canonical_old_reddit_thread_url

# Bump on ANY behavior change to this projection so content packets written
# under the old behavior stay distinguishable from re-projections under the
# new one (qualification compares records only within one version).
# v4: distinguish a verified old-Reddit empty listing from an unparseable
# zero-row response such as a login wall.
GRID_PROJECTION_PARSER_VERSION = "4"

GRID_CONTENT_RECORD_KIND = "reddit_subreddit_grid_view_v0"

# Both Reddit listing hosts are grid capture surfaces.  www joined on 2026-07-30
# when old.reddit stopped serving this client; old.reddit stays because the
# block may be lifted and its transport is otherwise unchanged.
OLD_REDDIT_LISTING_HOST = "old.reddit.com"
WWW_REDDIT_LISTING_HOST = "www.reddit.com"
GRID_LISTING_HOSTS = frozenset({OLD_REDDIT_LISTING_HOST, WWW_REDDIT_LISTING_HOST})


class RedditGridProjectionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class GridThreadRow:
    thread_url: str
    subreddit: str
    visible_title_or_none: str | None
    visible_score_or_none: str | None
    visible_comment_count_or_none: str | None
    promoted: bool
    # v2 fields default so v1 content records still reconstruct via **row.
    timestamp_utc_ms_or_none: str | None = None
    stickied: bool = False
    flair_or_none: str | None = None


@dataclass(frozen=True)
class GridView:
    subreddit: str
    listing_url: str
    visible_subscriber_count_or_none: str | None
    visible_active_user_count_or_none: str | None
    visible_volume_signal_absent_reason_or_none: str | None
    thread_rows: tuple[GridThreadRow, ...] = field(default_factory=tuple)
    # v2: sidebar "a community for ..." age element, ISO datetime string.
    created_utc_or_none: str | None = None
    # v3 diagnostics. None means a v1/v2 content record did not carry them.
    listing_thing_count_or_none: int | None = None
    listing_permalink_count_or_none: int | None = None
    # v4: source-visible proof that zero rows means an authentic empty listing,
    # not a block/login shell or parser failure.
    verified_empty_listing: bool = False
    # v5, www surface only: new Reddit states weekly reach on the subreddit
    # header element, old Reddit has no equivalent.  Kept SEPARATE from
    # visible_active_user_count_or_none, which on old Reddit means "users here
    # now" -- collapsing a weekly total into a concurrent gauge is the same
    # category error that put weekly visitors into a subscriber field.
    weekly_visitor_count_or_none: str | None = None
    weekly_contribution_count_or_none: str | None = None


def project_old_reddit_grid_html(
    *,
    html_text: str,
    subreddit: str,
    listing_url: str,
    max_thread_rows: int = 100,
) -> GridView:
    """Project one old Reddit listing page into a grid view.

    ``subreddit`` is the declared capture target; rows whose ``thing`` markup
    names another subreddit (cross-posted link entries) keep their true home
    subreddit, which is honest provenance, not traversal.
    """
    if not subreddit.isascii() or not subreddit.replace("_", "").isalnum():
        raise RedditGridProjectionError("invalid_subreddit", f"invalid subreddit name: {subreddit!r}")
    if max_thread_rows <= 0:
        raise RedditGridProjectionError("invalid_cap", "max_thread_rows must be greater than zero")

    parser = _OldRedditGridParser(declared_subreddit=subreddit)
    parser.feed(html_text)

    rows: list[GridThreadRow] = []
    seen: set[str] = set()
    for row in parser.thread_rows:
        if row.thread_url in seen:
            continue
        rows.append(row)
        seen.add(row.thread_url)
        if len(rows) >= max_thread_rows:
            break

    absent_reason = None
    if parser.visible_subscriber_count is None and parser.visible_active_user_count is None:
        absent_reason = "visible_volume_not_present_on_declared_surface"

    return GridView(
        subreddit=subreddit,
        listing_url=listing_url,
        visible_subscriber_count_or_none=parser.visible_subscriber_count,
        visible_active_user_count_or_none=parser.visible_active_user_count,
        visible_volume_signal_absent_reason_or_none=absent_reason,
        thread_rows=tuple(rows),
        created_utc_or_none=parser.visible_created_utc,
        listing_thing_count_or_none=parser.listing_thing_count,
        listing_permalink_count_or_none=parser.listing_permalink_count,
        verified_empty_listing=(
            parser.listing_thing_count == 0
            and parser.listing_permalink_count == 0
            and _is_verified_empty_listing_html(html_text)
        ),
    )


def build_grid_content_record(
    *,
    html_text: str,
    subreddit: str,
    listing_url: str,
) -> dict:
    """Project one grid page into the deterministic content-packet record.

    Pure function of its inputs (no timestamps, no environment reads) so a
    qualification can re-extract scratch raw bytes and compare the result
    byte-for-byte against the stored record.
    """
    view = project_old_reddit_grid_html(
        html_text=html_text,
        subreddit=subreddit,
        listing_url=listing_url,
    )
    return {
        "record_kind": GRID_CONTENT_RECORD_KIND,
        "parser_version": GRID_PROJECTION_PARSER_VERSION,
        "grid_view": grid_view_to_dict(view),
    }


def grid_view_to_dict(view: GridView) -> dict:
    payload = asdict(view)
    payload["thread_rows"] = list(payload["thread_rows"])
    return payload


def grid_view_from_record(record: dict) -> GridView:
    """Rebuild a GridView from a content-packet record (materializer read path)."""
    if not isinstance(record, dict) or record.get("record_kind") != GRID_CONTENT_RECORD_KIND:
        raise RedditGridProjectionError(
            "record_kind_mismatch",
            f"expected a {GRID_CONTENT_RECORD_KIND!r} record, got {record.get('record_kind') if isinstance(record, dict) else type(record).__name__!r}",
        )
    payload = record.get("grid_view")
    if not isinstance(payload, dict):
        raise RedditGridProjectionError("record_shape", "content record carries no grid_view object")
    try:
        rows = tuple(GridThreadRow(**row) for row in payload.get("thread_rows", []))
        return GridView(
            subreddit=payload["subreddit"],
            listing_url=payload["listing_url"],
            visible_subscriber_count_or_none=payload["visible_subscriber_count_or_none"],
            visible_active_user_count_or_none=payload["visible_active_user_count_or_none"],
            visible_volume_signal_absent_reason_or_none=payload["visible_volume_signal_absent_reason_or_none"],
            thread_rows=rows,
            # v1 records predate this key; absent means unobserved, not empty.
            created_utc_or_none=payload.get("created_utc_or_none"),
            listing_thing_count_or_none=payload.get("listing_thing_count_or_none"),
            listing_permalink_count_or_none=payload.get("listing_permalink_count_or_none"),
            verified_empty_listing=payload.get("verified_empty_listing", False),
            weekly_visitor_count_or_none=payload.get("weekly_visitor_count_or_none"),
            weekly_contribution_count_or_none=payload.get("weekly_contribution_count_or_none"),
        )
    except (KeyError, TypeError) as exc:
        raise RedditGridProjectionError(
            "record_shape",
            f"content record grid_view does not match the GridView shape: {exc}",
        ) from exc


def grid_view_projection_anomaly(view: GridView) -> str | None:
    """Return the first retention-worthy projection anomaly, if any."""
    rows = view.thread_rows
    if not rows:
        if view.verified_empty_listing:
            return None
        return "no_thread_rows"
    if (
        view.listing_thing_count_or_none is not None
        and view.listing_thing_count_or_none != len(rows)
    ):
        return "thread_row_count_mismatch"
    if view.listing_permalink_count_or_none == 0:
        return "no_permalinks"
    if all(row.timestamp_utc_ms_or_none is None for row in rows):
        return "no_timestamps"
    return None


def same_grid_listing_url(actual_url: str, expected_url: str) -> bool:
    """Compare one final Reddit listing URL to its requested locator.

    Both hosts are grid surfaces since old.reddit stopped serving this client
    (2026-07-30), but they must MATCH EACH OTHER rather than merely both being
    allowed: a www capture that satisfied an old.reddit locator would let one
    surface's evidence ledger as the other's, which is the cross-surface
    confusion the two canonical thread-URL helpers are also kept apart to avoid.
    """
    try:
        actual = urlsplit(actual_url)
        expected = urlsplit(expected_url)
    except (TypeError, ValueError):
        return False
    return (
        actual.scheme.lower() == expected.scheme.lower() == "https"
        and actual.netloc.lower() == expected.netloc.lower()
        and actual.netloc.lower() in GRID_LISTING_HOSTS
        and actual.path.rstrip("/").casefold() == expected.path.rstrip("/").casefold()
        and sorted(parse_qsl(actual.query, keep_blank_values=True))
        == sorted(parse_qsl(expected.query, keep_blank_values=True))
    )


def _is_verified_empty_listing_html(html_text: str) -> bool:
    """Require the old-Reddit listing shell and its explicit no-results row."""
    decoded = unescape(html_text)
    return bool(
        re.search(
            r"""<body\b[^>]*\bclass=["'][^"']*\blisting-page\b[^"']*["']""",
            decoded,
            flags=re.IGNORECASE,
        )
        and re.search(
            r"""<div\b(?=[^>]*\bid=["']siteTable["'])(?=[^>]*\bclass=["'][^"']*\bsitetable\b)[^>]*>""",
            decoded,
            flags=re.IGNORECASE,
        )
        and re.search(
            r"""<p\b(?=[^>]*\bid=["']noresults["'])(?=[^>]*\bclass=["'][^"']*\berror\b)[^>]*>\s*there doesn't seem to be anything here\s*</p>""",
            decoded,
            flags=re.IGNORECASE,
        )
    )


class _OldRedditGridParser(HTMLParser):
    """Single pass over a grid page: titlebox numbers + listing things.

    Thing rows prefer old Reddit's own machine attributes
    (``data-permalink`` / ``data-score`` / ``data-comments-count`` on
    ``div.thing``) and fall back to the title anchor plus visible score /
    comments text when an attribute is absent.
    """

    _VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, *, declared_subreddit: str) -> None:
        super().__init__(convert_charrefs=True)
        self.declared_subreddit = declared_subreddit
        self.thread_rows: list[GridThreadRow] = []
        self.visible_subscriber_count: str | None = None
        self.visible_active_user_count: str | None = None
        self.visible_created_utc: str | None = None
        self.listing_thing_count = 0
        self.listing_permalink_count = 0
        self._open_tags: list[str] = []
        self._titlebox_depth = 0
        self._users_online_depth = 0
        self._age_span_depth = 0
        self._capturing_flair_depth: int | None = None
        self._capturing_number_for: str | None = None
        self._capturing_number_depth: int | None = None
        self._thing_depth = 0
        self._current: dict[str, str | bool | None] | None = None
        self._capturing_title_depth: int | None = None
        self._capturing_score_depth: int | None = None
        self._capturing_comments_depth: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        class_tokens = set(attr_map.get("class", "").split())
        if tag not in self._VOID_TAGS:
            self._open_tags.append(tag)

        self._advance_titlebox(tag, class_tokens)
        if "users-online" in class_tokens:
            self._users_online_depth += 1
        elif self._users_online_depth and tag not in self._VOID_TAGS:
            self._users_online_depth += 1
        if "age" in class_tokens and tag == "span" and self._titlebox_depth:
            self._age_span_depth += 1
        elif self._age_span_depth and tag not in self._VOID_TAGS:
            self._age_span_depth += 1
        if (
            tag == "time"
            and self._age_span_depth
            and self.visible_created_utc is None
            and attr_map.get("datetime")
        ):
            # Sidebar "a community for N years" element; the datetime attribute
            # is the venue's exact creation instant.
            self.visible_created_utc = attr_map["datetime"]
        if tag == "span" and "number" in class_tokens and self._titlebox_depth:
            target = "active_users" if self._users_online_depth else "subscribers"
            already_captured = (
                self.visible_active_user_count if target == "active_users" else self.visible_subscriber_count
            )
            # First complete span wins per field: a later same-class span must
            # not append onto an already-captured value; fragments within one
            # span still accumulate while the capture stays open.
            if already_captured is None:
                self._capturing_number_for = target
                self._capturing_number_depth = self._titlebox_depth

        if "thing" in class_tokens:
            self.listing_thing_count += 1
            if attr_map.get("data-permalink"):
                self.listing_permalink_count += 1
        if "thing" in class_tokens and not self._thing_depth:
            self._open_thing(attr_map, class_tokens)
            self._thing_depth = 1
            return
        if self._thing_depth and tag not in self._VOID_TAGS:
            self._thing_depth += 1

        if self._current is None:
            return
        if "linkflairlabel" in class_tokens:
            # Old Reddit renders flair as <span class="linkflairlabel" title="X">X</span>;
            # the title attribute is the clean value, text capture is the fallback.
            if self._current.get("flair") is None:
                title_attr = attr_map.get("title", "").strip()
                if title_attr:
                    self._current["flair"] = title_attr
                else:
                    self._capturing_flair_depth = self._thing_depth
        if tag == "a" and _is_title_anchor(class_tokens):
            href = attr_map.get("href", "")
            if self._current.get("thread_url") is None:
                self._current["thread_url"] = canonical_old_reddit_thread_url(href)
            if self._current.get("title") is None:
                self._capturing_title_depth = self._thing_depth
        elif "score" in class_tokens and "unvoted" in class_tokens:
            if self._current.get("score") is None:
                self._capturing_score_depth = self._thing_depth
        elif tag == "a" and "comments" in class_tokens:
            if self._current.get("comments") is None:
                self._capturing_comments_depth = self._thing_depth

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if self._capturing_number_for is not None and value:
            if self._capturing_number_for == "active_users":
                self.visible_active_user_count = _append_fragment(
                    self.visible_active_user_count,
                    value,
                    separator="",
                )
            else:
                self.visible_subscriber_count = _append_fragment(
                    self.visible_subscriber_count,
                    value,
                    separator="",
                )
        if self._current is None or not value:
            return
        if self._capturing_title_depth is not None:
            self._current["title"] = _append_fragment(
                _str_or_none(self._current.get("title")),
                value,
                separator=" ",
            )
        elif self._capturing_score_depth is not None:
            self._current["score"] = _append_fragment(
                _str_or_none(self._current.get("score")),
                value,
                separator="",
            )
        elif self._capturing_comments_depth is not None:
            self._current["comments"] = _append_fragment(
                _str_or_none(self._current.get("comments")),
                value,
                separator=" ",
            )
        elif self._capturing_flair_depth is not None:
            self._current["flair"] = _append_fragment(
                _str_or_none(self._current.get("flair")),
                value,
                separator=" ",
            )

    def handle_endtag(self, tag: str) -> None:
        if tag in self._VOID_TAGS:
            return
        if not self._open_tags or self._open_tags[-1] != tag:
            # A stray or misnested closer must not corrupt every active scope.
            return
        self._open_tags.pop()
        if (
            tag == "span"
            and self._capturing_number_depth is not None
            and self._capturing_number_depth == self._titlebox_depth
        ):
            self._capturing_number_for = None
            self._capturing_number_depth = None
        if tag not in self._VOID_TAGS:
            if self._capturing_title_depth == self._thing_depth:
                self._capturing_title_depth = None
            if self._capturing_score_depth == self._thing_depth:
                self._capturing_score_depth = None
            if self._capturing_comments_depth == self._thing_depth:
                self._capturing_comments_depth = None
            if self._capturing_flair_depth == self._thing_depth:
                self._capturing_flair_depth = None
            if self._titlebox_depth:
                self._titlebox_depth -= 1
            if self._users_online_depth:
                self._users_online_depth -= 1
            if self._age_span_depth:
                self._age_span_depth -= 1
            if self._thing_depth:
                self._thing_depth -= 1
                if not self._thing_depth:
                    self._close_thing()

    def _advance_titlebox(self, tag: str, class_tokens: set[str]) -> None:
        if "titlebox" in class_tokens:
            self._titlebox_depth += 1
        elif self._titlebox_depth and tag not in self._VOID_TAGS:
            self._titlebox_depth += 1

    def _open_thing(self, attr_map: dict[str, str], class_tokens: set[str]) -> None:
        permalink = attr_map.get("data-permalink", "")
        self._current = {
            "thread_url": canonical_old_reddit_thread_url(permalink) if permalink else None,
            "subreddit": attr_map.get("data-subreddit", "") or self.declared_subreddit,
            "title": None,
            "score": attr_map.get("data-score") or None,
            "comments": attr_map.get("data-comments-count") or None,
            "promoted": "promoted" in class_tokens or attr_map.get("data-promoted", "") == "true",
            "timestamp": attr_map.get("data-timestamp") or None,
            "stickied": "stickied" in class_tokens,
            "flair": None,
        }

    def _close_thing(self) -> None:
        current = self._current
        self._current = None
        self._capturing_title_depth = None
        self._capturing_score_depth = None
        self._capturing_comments_depth = None
        self._capturing_flair_depth = None
        if current is None:
            return
        thread_url = current.get("thread_url")
        if not isinstance(thread_url, str) or thread_url is None:
            return
        self.thread_rows.append(
            GridThreadRow(
                thread_url=thread_url,
                subreddit=str(current.get("subreddit") or self.declared_subreddit),
                visible_title_or_none=_str_or_none(current.get("title")),
                visible_score_or_none=_str_or_none(current.get("score")),
                visible_comment_count_or_none=_extract_leading_count(current.get("comments")),
                promoted=bool(current.get("promoted")),
                timestamp_utc_ms_or_none=_str_or_none(current.get("timestamp")),
                stickied=bool(current.get("stickied")),
                flair_or_none=_str_or_none(current.get("flair")),
            )
        )


def _is_title_anchor(class_tokens: set[str]) -> bool:
    return "title" in class_tokens


def _str_or_none(value: object) -> str | None:
    # helper-delta: str-only vs harness_utils.string_or_none, which also
    # int-coerces; this copy returns None for a non-str (no coercion).
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _append_fragment(existing: str | None, value: str, *, separator: str) -> str:
    if existing is None:
        return value
    return f"{existing}{separator}{value}"


def _extract_leading_count(value: object) -> str | None:
    """``"128 comments"`` -> ``"128"``; ``"comment"`` -> None; passthrough digits."""
    text = _str_or_none(value)
    if text is None:
        return None
    match = re.match(r"^\s*(\d[\d,\s]*)", text)
    if match is not None:
        digits = match.group(1).replace(",", "").replace(" ", "")
        if digits.isdigit():
            return digits
    return None
