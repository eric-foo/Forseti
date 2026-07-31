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

Measured completeness constraint (r/Sephora thread ``1v87d9j``, 2026-08-01):

- 35 of 198 comments are present on first paint;
- clicking every in-place expansion control reaches 152 and leaves zero
  controls, converging in two rounds;
- the remaining 46 sit below the in-place depth bound (max captured depth 4)
  behind 90 ``Continue this thread`` anchors, each ``rel="nofollow"`` and each
  pointing at a SEPARATE per-comment permalink page.

This projection therefore never follows a continuation link: the source marks
them nofollow, and following them would turn one bounded thread capture into an
unbounded page crawl, which the runner's non-claims exclude.  The shortfall is
not hidden.  ``shreddit-comment-tree[totalcomments]`` states the thread's own
declared total, so every record carries the declared total, what was actually
captured, the arithmetic gap, and the count of continuation links left
unfollowed.  A consumer that needs the deep tail can see exactly how much of it
is missing; a consumer that treats the record as complete is contradicted by
its own numbers rather than misled by their absence.
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
WWW_REDDIT_THREAD_PARSER_VERSION = "www-1"

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

    comment_nodes = [node for node in root.descendants() if node.tag == _COMMENT_TAG]
    comments = [
        _parse_comment(node, row_index=index)
        for index, node in enumerate(comment_nodes, start=1)
    ]

    declared_total = _declared_total_comments(root)
    continuation_links = _count_continuation_links(root)
    captured_depths = [c.depth for c in comments if c.depth is not None]

    warnings: list[str] = []
    limitations: list[str] = []
    if declared_total is None:
        limitations.append(COMPLETENESS_BASIS_ABSENT)
    elif declared_total > len(comments):
        warnings.append(
            f"thread declares {declared_total} comments; {len(comments)} captured "
            f"({declared_total - len(comments)} not captured)"
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
                max(declared - captured, 0) if declared is not None else None
            ),
            "capture_is_complete": (
                None if declared is None else captured >= declared
            ),
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
    if "is-author-deleted" in node.attrs or author == "[deleted]" or text == "[deleted]":
        return "deleted"
    if "is-comment-deleted" in node.attrs or author == "[removed]" or text == "[removed]":
        return "removed"
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


def _declared_total_comments(root: HtmlNode) -> int | None:
    tree = _first_tag(root, _COMMENT_TREE_TAG)
    if tree is None:
        return None
    return _int_or_none(tree.attrs.get(_COMMENT_TREE_TOTAL_ATTR))


def _count_continuation_links(root: HtmlNode) -> int:
    count = 0
    for node in root.descendants():
        if node.tag != "a":
            continue
        if _CONTINUATION_MARKER in node.text_content().casefold():
            count += 1
    return count


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
