"""Mechanical projection of one new-Reddit (www) thread page.

Sibling of ``parser`` for the ``www.reddit.com`` surface, written because
``old.reddit.com`` stopped serving this client on 2026-07-30.  It deliberately
emits the SAME ``ParsedThread``/``ParsedComment`` shape and the same
``record_kind`` as the old-Reddit projection, distinguished only by
``parser_version`` and by the packet's ``source_surface`` -- the consolidation
record, the batch quality summary, and every downstream deep-read consumer take
the old shape, and a second record kind would force changes through that whole
chain for a set of identical fields.

The www thread DOM is strictly more machine-readable than the old-Reddit markup
it replaces.  Every field this projection needs is a NAMED attribute on
``<shreddit-comment>`` -- ``thingid``, ``parentid``, ``depth``, ``author``,
``created``, ``score``, ``permalink`` -- so nothing is read positionally.  That
is deliberate: an earlier www listing projection read two abutting sidebar
numbers by position and mislabelled weekly visitors as subscribers.

Measured capture constraint (r/Sephora thread ``1v87d9j``, 2026-08-01):

- 35 of 198 comments are present on first paint;
- clicking every in-place expansion control reaches 152 and leaves zero
  controls, converging in two rounds;
- the source-declared count remains 46 above the captured count; the rendered
  tree also carries ``Continue this thread`` anchors below the in-place depth
  bound (max captured depth 4), each ``rel="nofollow"`` and pointing at a
  separate per-comment permalink page.

This projection therefore never follows a continuation link: the source marks
them nofollow, and following them would turn one bounded thread capture into an
unbounded page crawl, which the runner's non-claims exclude.  The shortfall is
not hidden.  ``shreddit-comment-tree[totalcomments]`` states the source's own
declared count, so every record carries that count, what was actually captured,
the non-negative arithmetic gap when the two reconcile, and the count of unique
continuation targets left unfollowed.  The declared count is not an independent
completeness oracle: an exact match is recorded as a match, never promoted to a
claim that the live thread was captured completely.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from source_capture.reddit_consolidation.consolidator import (
    NON_CLAIMS,
    THREAD_CONTENT_RECORD_KIND,
)
from source_capture.reddit_consolidation.html_dom import HtmlNode, parse_html_document
from source_capture.reddit_consolidation.parser import (
    ParsedComment,
    ParsedThread,
    RedditParseFailure,
)


# Bump on ANY behavior change to this projection so records written under the
# old behavior stay distinguishable from re-projections under the new one.
WWW_REDDIT_THREAD_PARSER_VERSION = "www-2"

_POST_TAG = "shreddit-post"
_POST_BODY_TAG = "shreddit-post-text-body"
_COMMENT_TAG = "shreddit-comment"
_COMMENT_TREE_TAG = "shreddit-comment-tree"
_COMMENT_TREE_TOTAL_ATTR = "totalcomments"
_COMMENT_BODY_SLOT = "comment"
_CONTINUATION_MARKER = "continue this thread"

# Completeness basis, carried in the record so a reader never has to guess which
# number the shortfall was measured against.
COMPLETENESS_BASIS = "shreddit-comment-tree[totalcomments]"
COMPLETENESS_BASIS_ABSENT = (
    "www_thread_declares_no_comment_tree_total; captured count stands alone"
)
COMPLETENESS_BASIS_LIMITATION = (
    "www_thread_declared_total_is_not_independent_completeness_oracle"
)
CONTINUATION_NOT_FOLLOWED_REASON = (
    "www_continuation_links_are_nofollow_separate_pages_and_are_not_followed"
)


def parse_www_reddit_html(html: str) -> ParsedThread:
    root = parse_html_document(html)
    post_node = _first_tag(root, _POST_TAG)
    if post_node is None:
        raise RedditParseFailure(
            "required_thread_envelope_missing",
            "could not identify a www-Reddit <shreddit-post> thread envelope",
        )

    comment_tree = _first_tag(root, _COMMENT_TREE_TAG)
    # Keep the counted nodes and the declared-total attribute on the same DOM
    # envelope. A sidebar/recommendation component may carry another
    # <shreddit-comment>; including it would inflate the completeness numerator.
    comment_scope = comment_tree if comment_tree is not None else root
    comment_nodes = [
        node for node in comment_scope.descendants() if node.tag == _COMMENT_TAG
    ]
    comments = [
        _parse_comment(node, row_index=index)
        for index, node in enumerate(comment_nodes, start=1)
    ]

    declared_total = _declared_total_comments(comment_tree)
    continuation_links = _count_continuation_links(comment_scope)
    captured_depths = [c.depth for c in comments if c.depth is not None]

    warnings: list[str] = []
    limitations: list[str] = []
    if declared_total is None:
        limitations.append(COMPLETENESS_BASIS_ABSENT)
    else:
        limitations.append(COMPLETENESS_BASIS_LIMITATION)
        if declared_total > len(comments):
            warnings.append(
                f"thread declares {declared_total} comments; {len(comments)} captured "
                f"({declared_total - len(comments)} not captured)"
            )
        elif declared_total < len(comments):
            warnings.append(
                f"captured comment count {len(comments)} exceeds the source-declared "
                f"count {declared_total}; completeness is unknown"
            )
    if continuation_links:
        limitations.append(
            f"{continuation_links} continuation link(s) left unfollowed: "
            f"{CONTINUATION_NOT_FOLLOWED_REASON}"
        )

    return ParsedThread(
        thread_id=_normalize_thing_id(post_node.attrs.get("id")),
        subreddit=_attr_or_none(post_node, "subreddit-name"),
        title=_attr_or_none(post_node, "post-title"),
        permalink=_attr_or_none(post_node, "permalink"),
        author_state=_author_state(post_node),
        timestamp_state=_state_from_attr(
            post_node, "created-timestamp", "timestamp not stated on the post element"
        ),
        score_state=_state_from_attr(
            post_node, "score", "score not stated on the post element"
        ),
        post_body_text=_post_body_text(root, post_node),
        comments=comments,
        observable_comment_node_count=len(comment_nodes),
        warnings=warnings,
        limitations=limitations,
        declared_total_comments=declared_total,
        continuation_links_not_followed=continuation_links,
        max_captured_depth=max(captured_depths) if captured_depths else None,
    )


def build_www_thread_content_record(
    *, html_text: str, source_url: str
) -> dict[str, Any]:
    """Project one www Reddit thread page into the deterministic content record.

    Pure function of ``(html_text, source_url)`` -- no timestamps, no packet
    references, no environment reads -- so ephemeral qualification can
    re-project sampled raw bytes and compare byte-for-byte against the stored
    record, exactly as the old-Reddit counterpart does.
    """
    parsed = parse_www_reddit_html(html_text)
    posture_counts = Counter(comment.comment_posture for comment in parsed.comments)
    captured = len(parsed.comments)
    declared = parsed.declared_total_comments
    declared_gap = declared - captured if declared is not None else None
    captured_matches_declared = declared is not None and captured == declared
    if declared is None:
        capture_is_complete: bool | None = None
    elif captured < declared or parsed.continuation_links_not_followed:
        # Either signal disproves completeness relative to the rendered source.
        capture_is_complete = False
    else:
        # Equality cannot prove the meaning/exhaustiveness of the source's
        # declared count; an overcount is a reconciliation failure, not success.
        capture_is_complete = None
    return {
        "record_kind": THREAD_CONTENT_RECORD_KIND,
        "parser_version": WWW_REDDIT_THREAD_PARSER_VERSION,
        "source_url": source_url,
        "thread": {
            "thread_id": parsed.thread_id,
            "subreddit": parsed.subreddit,
            "title": parsed.title,
            "permalink": parsed.permalink,
        },
        "post": {
            "author_state": parsed.author_state,
            "timestamp_state": parsed.timestamp_state,
            "score_state": parsed.score_state,
            "body_text": parsed.post_body_text,
        },
        "comments": [
            {
                "row_id": comment.row_id,
                "comment_id": comment.comment_id,
                "parent_id": comment.parent_id,
                "depth": comment.depth,
                "author_state": comment.author_state,
                "timestamp_state": comment.timestamp_state,
                "score_state": comment.score_state,
                "body_text": comment.body_text,
                "comment_posture": comment.comment_posture,
                "parser_warnings": comment.parser_warnings,
            }
            for comment in parsed.comments
        ],
        "counts": {
            "observable_comment_nodes": parsed.observable_comment_node_count,
            "comments_parsed": captured,
            "comment_postures": dict(sorted(posture_counts.items())),
        },
        # The honesty surface. A reader must be able to see how much of the
        # thread is NOT here without re-deriving it from the comment list.
        "comment_completeness": {
            "basis": COMPLETENESS_BASIS if declared is not None else None,
            "declared_total_comments": declared,
            "comments_captured": captured,
            "comments_not_captured": (
                declared_gap
                if declared_gap is not None and declared_gap >= 0
                else None
            ),
            "captured_matches_declared_total": (
                captured_matches_declared if declared is not None else None
            ),
            "capture_is_complete": capture_is_complete,
            "continuation_links_not_followed": parsed.continuation_links_not_followed,
            "continuation_reason": (
                CONTINUATION_NOT_FOLLOWED_REASON
                if parsed.continuation_links_not_followed
                else None
            ),
            "max_captured_depth": parsed.max_captured_depth,
        },
        "warnings": parsed.warnings,
        "limitations": parsed.limitations,
        "non_claims": NON_CLAIMS,
    }


def _parse_comment(node: HtmlNode, *, row_index: int) -> ParsedComment:
    body_node = _comment_body_node(node)
    body = body_node.text_content() if body_node is not None else ""
    posture = _comment_posture(node, body_text=body)
    warnings: list[str] = []
    if posture == "present" and body_node is None:
        posture = "missing_dom"
        warnings.append(
            "observable comment node had no slot=\"comment\" body; body_text left empty"
        )
    elif posture == "present" and not body:
        posture = "media_only"
        warnings.append(
            "observable comment body had no extractable text; non-text media may be present"
        )
    if posture in {"collapsed", "media_only", "missing_dom", "unavailable"}:
        warnings.append(f"comment body carried as {posture}")

    return ParsedComment(
        row_id=f"comment_{row_index:04d}",
        comment_id=_normalize_thing_id(node.attrs.get("thingid")),
        parent_id=_normalize_thing_id(node.attrs.get("parentid")),
        depth=_int_or_none(node.attrs.get("depth")),
        author_state=_author_state(node),
        timestamp_state=_state_from_attr(
            node, "created", "timestamp not stated on the comment element"
        ),
        score_state=_state_from_attr(
            node, "score", "score not stated on the comment element"
        ),
        body_text=body,
        comment_posture=posture,
        parser_warnings=warnings,
    )


def _comment_posture(node: HtmlNode, *, body_text: str) -> str:
    # Read the source's own stated markers by name. "collapsed" is checked
    # after the deleted/removed markers because a deleted comment is also
    # served collapsed, and the stronger fact is that it is gone.
    author = (node.attrs.get("author") or "").strip().lower()
    text = body_text.strip().lower()
    author_deleted = "is-author-deleted" in node.attrs or author == "[deleted]"
    if "is-comment-deleted" in node.attrs or text == "[deleted]":
        return "deleted"
    if text == "[removed]" or (author == "[removed]" and not text):
        return "removed"
    # is-author-deleted says who is gone, not that a still-rendered body is.
    if author_deleted and not text:
        return "deleted"
    if "collapsed" in node.attrs:
        return "collapsed"
    return "present"


def _comment_body_node(node: HtmlNode) -> HtmlNode | None:
    for child in _own_descendants(node):
        if child.attrs.get("slot") == _COMMENT_BODY_SLOT:
            return child
    return None


def _own_descendants(node: HtmlNode) -> Iterable[HtmlNode]:
    """Descend but stop at a nested comment.

    www nests replies as real ``<shreddit-comment>`` children, so an unguarded
    walk would fold a reply's body into its parent's body_text.
    """
    for child in node.children:
        if child.tag == _COMMENT_TAG:
            continue
        yield child
        yield from _own_descendants(child)


def _post_body_text(root: HtmlNode, post_node: HtmlNode) -> str:
    # Scope to the post's own body element. Comments carry their own
    # ``*-post-rtjson-content`` divs, so a document-wide id search would pull a
    # comment's text into the post body.
    body_tag = _first_tag(post_node, _POST_BODY_TAG) or _first_tag(root, _POST_BODY_TAG)
    if body_tag is None:
        return ""
    return body_tag.text_content()


def _declared_total_comments(tree: HtmlNode | None) -> int | None:
    if tree is None:
        return None
    return _int_or_none(tree.attrs.get(_COMMENT_TREE_TOTAL_ATTR))


def _count_continuation_links(comment_scope: HtmlNode) -> int:
    targets: set[str] = set()
    for node in comment_scope.descendants():
        if node.tag != "a":
            continue
        href = (node.attrs.get("href") or "").strip()
        rel = (node.attrs.get("rel") or "").casefold().split()
        if (
            href
            and "nofollow" in rel
            and _CONTINUATION_MARKER in node.text_content().casefold()
        ):
            # Reddit can render the same continuation target twice in one
            # subtree. Count the unfollowed destination, not duplicate chrome.
            targets.add(href)
    return len(targets)


def _first_tag(root: HtmlNode, tag: str) -> HtmlNode | None:
    for node in root.descendants():
        if node.tag == tag:
            return node
    return None


def _author_state(node: HtmlNode) -> str:
    author = (node.attrs.get("author") or "").strip()
    if author:
        return author
    return "unknown_with_reason: author not stated on the element"


def _state_from_attr(node: HtmlNode, attr: str, absent_reason: str) -> str:
    value = (node.attrs.get(attr) or "").strip()
    if value:
        return value
    return f"unknown_with_reason: {absent_reason}"


def _attr_or_none(node: HtmlNode, attr: str) -> str | None:
    value = (node.attrs.get(attr) or "").strip()
    return value or None


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _normalize_thing_id(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    for prefix in ("thing_", "t1_", "t3_"):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text
