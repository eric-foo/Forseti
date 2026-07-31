from __future__ import annotations

from source_capture.rendered_access import RenderedAccessClass, classify_rendered_access


def test_classify_rendered_access_flags_cloudflare_interstitial() -> None:
    result = classify_rendered_access(
        title="Just a moment...",
        visible_text="Enable JavaScript and cookies to continue",
        rendered_dom="<html><script>window.__cf_chl_tk='token'</script></html>",
    )

    assert result.classification == RenderedAccessClass.ACCESS_BLOCKED
    assert result.signal == "cloudflare_interstitial"


def test_classify_rendered_access_flags_exact_local_rate_limit_marker() -> None:
    result = classify_rendered_access(
        title=None,
        visible_text="  local_rate_limited\n",
        rendered_dom="<html><body>local_rate_limited</body></html>",
    )

    assert result.classification == RenderedAccessClass.ACCESS_BLOCKED
    assert result.signal == "local_rate_limited"


def test_classify_rendered_access_does_not_flag_source_text_that_mentions_marker() -> None:
    result = classify_rendered_access(
        title="Incident report",
        visible_text="The old capture returned local_rate_limited before recovery.",
        rendered_dom="<html><body>Incident report</body></html>",
    )

    assert result.classification == RenderedAccessClass.NO_BLOCK_MARKER


def test_classify_rendered_access_flags_akamai_access_denied() -> None:
    result = classify_rendered_access(
        title="Access Denied",
        visible_text=(
            "You don't have permission to access this page on this server. "
            "Reference #18.abc https://errors.edgesuite.net/18.abc"
        ),
        rendered_dom="<html><body>Access Denied</body></html>",
    )

    assert result.classification == RenderedAccessClass.ACCESS_BLOCKED
    assert result.signal == "akamai_access_denied"


def test_classify_rendered_access_does_not_flag_source_article_mentions() -> None:
    result = classify_rendered_access(
        title="Troubleshooting Access Denied errors",
        visible_text="This source article explains why access can be denied.",
        rendered_dom="<html><body>Article content</body></html>",
    )

    assert result.classification == RenderedAccessClass.NO_BLOCK_MARKER
    assert result.signal is None


def test_classify_rendered_access_akamai_requires_both_markers() -> None:
    """Matching title alone, with only one of the two Akamai markers, must not flag."""
    result = classify_rendered_access(
        title="Access Denied",
        visible_text="You don't have permission to access this resource.",
        rendered_dom="<html><body>Access Denied</body></html>",
    )

    assert result.classification == RenderedAccessClass.NO_BLOCK_MARKER
    assert result.signal is None


def test_classify_rendered_access_akamai_requires_exact_title() -> None:
    """Both Akamai markers present, with a non-matching title, must not flag."""
    result = classify_rendered_access(
        title="403 Forbidden",
        visible_text=(
            "You don't have permission to access this page on this server. "
            "Reference #18.abc https://errors.edgesuite.net/18.abc"
        ),
        rendered_dom="<html><body>Forbidden</body></html>",
    )

    assert result.classification == RenderedAccessClass.NO_BLOCK_MARKER
    assert result.signal is None


def test_classify_rendered_access_keeps_residual_cloudflare_marker_separate() -> None:
    result = classify_rendered_access(
        title="Mojave Ghost by Byredo",
        visible_text="Reviews 1 2 3 Basenotes source content",
        rendered_dom=(
            "<html><body>Reviews 1 2 3 Basenotes source content"
            "<script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script>"
            "</body></html>"
        ),
    )

    assert result.classification == RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER
    assert result.signal == "residual_cloudflare_challenge_marker"


def test_classify_rendered_access_keeps_hidden_residual_cloudflare_text_separate() -> None:
    result = classify_rendered_access(
        title="Just a moment...",
        visible_text="Reviews 1 2 3 Basenotes source content and comments remain visible",
        rendered_dom=(
            "<html><body>Reviews 1 2 3 Basenotes source content"
            "<template>Enable JavaScript and cookies to continue</template>"
            "<script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script>"
            "</body></html>"
        ),
    )

    assert result.classification == RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER
    assert result.signal == "residual_cloudflare_challenge_marker"


def test_classify_rendered_access_reports_no_block_marker_for_source_content() -> None:
    result = classify_rendered_access(
        title="Rendered Source",
        visible_text="Visible source language",
        rendered_dom="<html><body>Visible source language</body></html>",
    )

    assert result.classification == RenderedAccessClass.NO_BLOCK_MARKER
    assert result.signal is None


def test_classify_rendered_access_flags_visible_tiktok_slider() -> None:
    result = classify_rendered_access(
        title="TikTok",
        visible_text="Creator profile\nDrag the slider to fit the puzzle",
        rendered_dom="<html><body>Creator profile</body></html>",
    )

    assert result.classification == RenderedAccessClass.ACCESS_BLOCKED
    assert result.signal == "tiktok_slider_or_captcha"


def test_classify_rendered_access_keeps_hidden_tiktok_marker_residual() -> None:
    result = classify_rendered_access(
        title="TikTok creator",
        visible_text="Creator profile and public source text",
        rendered_dom="<html><template>verify to continue</template></html>",
    )

    assert result.classification == RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER
