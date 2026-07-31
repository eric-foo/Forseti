from __future__ import annotations

from dataclasses import dataclass, field

from source_capture.reddit_consolidation.html_dom import HtmlNode, parse_html_document


# Bump on ANY behavior change to this parser so content packets written under
# the old behavior stay distinguishable from re-projections under the new one
# (qualification compares records only within one version).
OLD_REDDIT_THREAD_PARSER_VERSION = "1"

COMMENT_POSTURES = {
    "present",
    "deleted",
    "removed",
    "collapsed",
    "media_only",
    "missing_dom",
    "unavailable",
}


class RedditParseFailure(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ParsedComment:
    row_id: str
    comment_id: str | None
    parent_id: str | None
    depth: int | None
    author_state: str
    timestamp_state: str
    score_state: str
    body_text: str
    comment_posture: str
    parser_warnings: list[str] = field(default_factory=list)


@dataclass
class ParsedThread:
    thread_id: str | None
    subreddit: str | None
    title: str | None
    permalink: str | None
    author_state: str
    timestamp_state: str
    score_state: str
    post_body_text: str
    comments: list[ParsedComment]
    observable_comment_node_count: int
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    # Completeness facts the www surface can state and the old surface cannot.
    # Defaulted to None/0 so the old-Reddit parser is unaffected: on old.reddit
    # the served page carries the whole exposed tree, so there is no declared
    # total to reconcile against and no continuation link to leave unfollowed.
    declared_total_comments: int | None = None
    continuation_links_not_followed: int = 0
    max_captured_depth: int | None = None


def parse_old_reddit_html(html: str) -> ParsedThread:
    root = parse_html_document(html)
    post_node = _find_post_node(root)
    if post_node is None:
        raise RedditParseFailure(
            "required_thread_envelope_missing",
            "could not identify an old-Reddit-like thread/post envelope",
        )

    comment_nodes = _find_comment_nodes(root)
    comments: list[ParsedComment] = []
    for node in comment_nodes:
        parsed = _parse_comment(node, row_index=len(comments) + 1)
        comments.append(parsed)

    # Reconciliation holds by construction: the loop above appends exactly one ParsedComment per
    # observed node (malformed/bodyless nodes become postures + warnings, never silent drops), so
    # len(comments) == len(comment_nodes) here. The former `len(comments) < len(comment_nodes)`
    # hard-raise guard was structurally unreachable (dead) and gave false assurance; the real,
    # reachable reconciliation check is the batch quality flag `comment_reconciliation_mismatch`
    # in run_reddit_batch_quality_summary.py (comments_parsed != observable_comment_nodes). (RE-HARN-9)

    return ParsedThread(
        thread_id=_normalize_reddit_id(post_node.attrs.get("data-fullname") or post_node.attrs.get("id")),
        subreddit=_first_text_attr(post_node, "data-subreddit"),
        title=_text_or_none(post_node.first_descendant(class_name="title")),
        permalink=_first_text_attr(post_node, "data-permalink") or _first_permalink(post_node),
        author_state=_author_state(post_node),
        timestamp_state=_timestamp_state(post_node),
        score_state=_score_state(post_node),
        post_body_text=_body_text(post_node),
        comments=comments,
        observable_comment_node_count=len(comment_nodes),
        warnings=[],
        limitations=[],
    )


def _find_post_node(root: HtmlNode) -> HtmlNode | None:
    for node in root.descendants():
        classes = node.classes()
        if "thing" in classes and "link" in classes:
            return node
    return None


def _find_comment_nodes(root: HtmlNode) -> list[HtmlNode]:
    return [
        node
        for node in root.descendants()
        if "thing" in node.classes() and "comment" in node.classes()
    ]


def _parse_comment(node: HtmlNode, *, row_index: int) -> ParsedComment:
    body_node = _body_node(node)
    body = _body_text_from_node(body_node)
    posture = _comment_posture(node, body_node=body_node, body_text=body)
    warnings: list[str] = []
    if posture == "present" and body_node is None:
        posture = "missing_dom"
        warnings.append("observable comment node had no visible usertext body; body_text left empty")
    elif posture == "present" and not body:
        posture = "media_only"
        warnings.append("observable comment body had no extractable text; non-text media may be present")
    if posture in {"collapsed", "media_only", "missing_dom", "unavailable"}:
        warnings.append(f"comment body carried as {posture}")

    return ParsedComment(
        row_id=f"comment_{row_index:04d}",
        comment_id=_normalize_reddit_id(node.attrs.get("data-fullname") or node.attrs.get("id")),
        parent_id=_normalize_reddit_id(node.attrs.get("data-parent")),
        depth=_comment_depth(node),
        author_state=_author_state(node),
        timestamp_state=_timestamp_state(node),
        score_state=_score_state(node),
        body_text=body,
        comment_posture=posture,
        parser_warnings=warnings,
    )


def _comment_posture(node: HtmlNode, *, body_node: HtmlNode | None, body_text: str) -> str:
    classes = node.classes()
    text = body_text.lower()
    author = (node.attrs.get("data-author") or "").strip().lower()
    if "collapsed" in classes:
        return "collapsed"
    if "unavailable" in classes or _own_text_contains(node, "unavailable"):
        return "unavailable"
    if "missing-dom" in classes or "missing_dom" in classes:
        return "missing_dom"
    if "removed" in classes or author == "[removed]" or text == "[removed]":
        return "removed"
    if "deleted" in classes or author == "[deleted]" or text == "[deleted]":
        return "deleted"
    return "present"


def _comment_depth(node: HtmlNode) -> int | None:
    raw_depth = node.attrs.get("data-depth")
    if raw_depth:
        try:
            return int(raw_depth)
        except ValueError:
            return None
    depth = 0
    parent = node.parent
    while parent is not None:
        if "child" in parent.classes():
            depth += 1
        parent = parent.parent
    return depth


def _author_state(node: HtmlNode) -> str:
    author = node.attrs.get("data-author")
    if author:
        return author
    author_node = node.first_descendant(class_name="author")
    author_text = _text_or_none(author_node)
    if author_text:
        return author_text
    return "unknown_with_reason: author not visible in preserved DOM"


def _timestamp_state(node: HtmlNode) -> str:
    time_node = node.first_descendant(tag="time")
    if time_node is None:
        return "unknown_with_reason: timestamp not visible in preserved DOM"
    return time_node.attrs.get("datetime") or time_node.text_content() or "unknown_with_reason: empty time element"


def _score_state(node: HtmlNode) -> str:
    score = node.attrs.get("data-score")
    if score:
        return score
    score_node = node.first_descendant(class_name="score")
    score_text = _text_or_none(score_node)
    if score_text:
        return score_text
    return "unknown_with_reason: score not visible in preserved DOM"


def _body_text(node: HtmlNode) -> str:
    return _body_text_from_node(_body_node(node))


def _body_node(node: HtmlNode) -> HtmlNode | None:
    for child in _own_descendants(node):
        if child.has_class("usertext-body"):
            return child
    return None


def _body_text_from_node(body_node: HtmlNode | None) -> str:
    if body_node is None:
        return ""
    return body_node.text_content()


def _own_text_contains(node: HtmlNode, needle: str) -> bool:
    lowered = needle.lower()
    return any(lowered in part.lower() for part in node.text_parts)


def _own_descendants(node: HtmlNode):
    for child in node.children:
        classes = child.classes()
        if "thing" in classes and "comment" in classes:
            continue
        yield child
        yield from _own_descendants(child)


def _first_permalink(node: HtmlNode) -> str | None:
    for child in node.descendants():
        if child.tag != "a":
            continue
        href = child.attrs.get("href")
        if href and "/comments/" in href:
            return href
    return None


def _text_or_none(node: HtmlNode | None) -> str | None:
    if node is None:
        return None
    text = node.text_content()
    return text or None


def _first_text_attr(node: HtmlNode, attr_name: str) -> str | None:
    value = node.attrs.get(attr_name)
    return value.strip() if value and value.strip() else None


def _normalize_reddit_id(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    for prefix in ("thing_", "t1_", "t3_"):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text
