from __future__ import annotations

import pytest

from source_capture.access_gate import detect_login_gate


@pytest.mark.parametrize(
    ("final_url", "body_text", "expected_signal"),
    [
        (
            "https://example.test/login?dest=%2Fsource",
            "<html><body>redirected</body></html>",
            "login_redirect",
        ),
        (
            "https://example.test/source",
            '<html><form action="/signin" method="post">Sign in</form></html>',
            "login_page",
        ),
        (
            "https://example.test/source",
            "<html><body>Please log in to continue.</body></html>",
            "login_page",
        ),
    ],
)
def test_detect_login_gate_requires_high_confidence_signal(
    final_url: str, body_text: str, expected_signal: str
) -> None:
    detection = detect_login_gate(final_url=final_url, body_text=body_text)

    assert detection is not None
    assert detection.signal == expected_signal


def test_detect_login_gate_does_not_reject_normal_login_navigation() -> None:
    detection = detect_login_gate(
        final_url="https://example.test/articles/source",
        body_text=(
            '<html><nav><a href="/login">Log in</a></nav>'
            "<main>Source-visible article content.</main></html>"
        ),
    )

    assert detection is None


def test_detect_login_gate_allows_visible_old_reddit_thread_with_onboarding_form() -> None:
    detection = detect_login_gate(
        final_url="https://old.reddit.com/r/orca_test/comments/abc/visible_thread/",
        body_text=(
            '<html><form action="https://www.reddit.com/r/orca_test/post/login">'
            "Log in</form>"
            '<div class="thing link" id="thing_t3_abc" data-fullname="t3_abc">'
            '<a class="title">Visible thread</a></div>'
            '<div class="thing comment" data-fullname="t1_comment">'
            '<div class="usertext-body">Visible comment</div></div></html>'
        ),
    )

    assert detection is None


def test_detect_login_gate_allows_deleted_op_old_reddit_thread_via_comment_listing() -> None:
    # A deleted self-post drops the thing_t3/data-fullname post div while the
    # thread page stays public (observed live 2026-07-26 on
    # /r/Sephora/comments/19eo5it/): the thread-id-bound comment-listing
    # container must count as envelope proof.
    detection = detect_login_gate(
        final_url="https://old.reddit.com/r/orca_test/comments/abc/visible_thread/",
        body_text=(
            '<html><form action="https://www.reddit.com/r/orca_test/post/login">'
            "Log in</form>"
            '<div id="siteTable_t3_abc" class="sitetable nestedlisting">'
            '<div class="thing comment" data-fullname="t1_comment">'
            '<div class="usertext-body">[deleted] OP, visible comment</div>'
            "</div></div></html>"
        ),
    )

    assert detection is None


@pytest.mark.parametrize(
    "marker",
    [
        "",
        '<div class="thing link" data-fullname="t3_different"></div>',
        '<div id="siteTable_t3_different" class="sitetable nestedlisting"></div>',
    ],
)
def test_detect_login_gate_requires_matching_old_reddit_thread_evidence(
    marker: str,
) -> None:
    detection = detect_login_gate(
        final_url="https://old.reddit.com/r/orca_test/comments/abc/visible_thread/",
        body_text=(
            '<html><form action="https://www.reddit.com/r/orca_test/post/login">'
            f"Log in</form>{marker}</html>"
        ),
    )

    assert detection is not None
    assert detection.signal == "login_page"


def test_detect_login_gate_still_refuses_old_reddit_thread_with_explicit_gate_language() -> None:
    # The thread-marker exception is scoped to the login-form-action branch only.
    # Explicit access-gate language must keep failing closed on old Reddit too.
    detection = detect_login_gate(
        final_url="https://old.reddit.com/r/orca_test/comments/abc/visible_thread/",
        body_text=(
            '<html><form action="https://www.reddit.com/r/orca_test/post/login">'
            "Log in</form>"
            '<div class="thing link" id="thing_t3_abc" data-fullname="t3_abc"></div>'
            "<p>Please log in to continue.</p></html>"
        ),
    )

    assert detection is not None
    assert detection.signal == "login_page"


def test_detect_login_gate_does_not_reject_public_auth_documentation_url() -> None:
    detection = detect_login_gate(
        final_url="https://example.test/docs/auth/guide",
        body_text="<html><main><h1>Authentication guide</h1><p>Public documentation.</p></main></html>",
    )

    assert detection is None


def test_detect_login_gate_allows_canonical_content_redirect() -> None:
    detection = detect_login_gate(
        final_url="https://example.test/articles/canonical-source",
        body_text="<html><main>Canonical source content.</main></html>",
    )

    assert detection is None
