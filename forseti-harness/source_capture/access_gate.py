from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import ParseResult, unquote, urlparse


LoginGateSignal = Literal["login_redirect", "login_page"]


@dataclass(frozen=True)
class LoginGateDetection:
    signal: LoginGateSignal
    detail: str


_AUTH_PATH_SEGMENTS = frozenset({"login", "register", "sign-in", "signin"})
_LOGIN_FORM_ACTION = re.compile(
    r"""<form\b[^>]*\baction\s*=\s*["'][^"']*(?:/login|/signin|/sign-in|/register)(?:[/?#][^"']*)?["']""",
    re.IGNORECASE,
)
_EXPLICIT_LOGIN_PAGE_MARKERS: tuple[str, ...] = (
    "please log in",
    "please sign in",
    "log in to continue",
    "sign in to continue",
)
_OLD_REDDIT_THREAD_PATH = re.compile(
    r"^/r/[^/]+/comments/(?P<thread_id>[a-z0-9]+)/",
    re.IGNORECASE,
)


def detect_login_gate(*, final_url: str, body_text: str) -> LoginGateDetection | None:
    """Detect a high-confidence post-fetch login gate without certifying content.

    Ordinary pages may contain navigation links such as ``Log in``. Those are
    deliberately insufficient: URL-path detection requires an auth-specific
    segment, and body detection requires a login form action or explicit
    access-gate language. Old Reddit thread pages also carry an onboarding
    login form alongside the public thread; a URL-matched ``t3`` post marker
    proves that source envelope is present, so that form alone is not a gate.
    A missing or mismatched marker still fails closed.
    """

    parsed = urlparse(final_url)
    path_segments = {
        unquote(segment).strip().lower()
        for segment in (parsed.path or "").split("/")
        if segment.strip()
    }
    matched_segments = sorted(path_segments & _AUTH_PATH_SEGMENTS)
    if matched_segments:
        return LoginGateDetection(
            signal="login_redirect",
            detail=(
                f"final URL landed on an auth path segment {matched_segments[0]!r}: "
                f"{final_url!r}"
            ),
        )

    if _LOGIN_FORM_ACTION.search(body_text) and not _has_visible_old_reddit_thread(
        parsed_url=parsed,
        body_text=body_text,
    ):
        return LoginGateDetection(
            signal="login_page",
            detail="response body contains a login/sign-in form action",
        )

    body_lower = body_text.lower()
    for marker in _EXPLICIT_LOGIN_PAGE_MARKERS:
        if marker in body_lower:
            return LoginGateDetection(
                signal="login_page",
                detail=f"response body matched explicit access-gate language {marker!r}",
            )
    return None


def _has_visible_old_reddit_thread(*, parsed_url: ParseResult, body_text: str) -> bool:
    if (parsed_url.hostname or "").lower() != "old.reddit.com":
        return False
    match = _OLD_REDDIT_THREAD_PATH.match(parsed_url.path or "")
    if match is None:
        return False

    # A deleted self-post drops the ``thing_t3``/``data-fullname`` post div
    # while the thread page (title, comment listing) stays public, so the
    # thread-id-bound comment-listing container is accepted as equal envelope
    # proof. All markers stay bound to the URL's thread id; a login-wall
    # interstitial carries none of them.
    thread_id = re.escape(match.group("thread_id"))
    return (
        re.search(
            rf"""\b(?:id=["'](?:thing_t3_{thread_id}|siteTable_t3_{thread_id})["']"""
            rf"""|data-fullname=["']t3_{thread_id}["'])""",
            body_text,
            re.IGNORECASE,
        )
        is not None
    )


__all__ = ["LoginGateDetection", "LoginGateSignal", "detect_login_gate"]
