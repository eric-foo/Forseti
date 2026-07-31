from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RenderedAccessClass(StrEnum):
    ACCESS_BLOCKED = "access_blocked"
    RESIDUAL_CHALLENGE_MARKER = "residual_challenge_marker"
    NO_BLOCK_MARKER = "no_block_marker"


@dataclass(frozen=True)
class RenderedAccessClassification:
    classification: RenderedAccessClass
    signal: str | None
    detail: str


_VISIBLE_CLOUDFLARE_INTERSTITIAL_MARKERS = (
    "enable javascript and cookies to continue",
    "checking if the site connection is secure",
    "checking your browser before accessing",
    "please enable javascript and cookies",
    "verify you are human by completing the action below",
    "verifying you are human",
)

_CLOUDFLARE_CHALLENGE_ONLY_VISIBLE_MARKERS = (
    *_VISIBLE_CLOUDFLARE_INTERSTITIAL_MARKERS,
    "just a moment",
    "cloudflare",
    "ray id",
    "performance & security by cloudflare",
)

_VISIBLE_TIKTOK_CHALLENGE_MARKERS = (
    "drag the slider to fit the puzzle",
    "drag the slider",
    "verify to continue",
    "complete the puzzle",
)

_AKAMAI_ACCESS_DENIED_MARKERS = (
    "you don't have permission to access",
    "errors.edgesuite.net",
)


def classify_rendered_access(
    *,
    title: str | None,
    visible_text: str,
    rendered_dom: str,
) -> RenderedAccessClassification:
    title_text = (title or "").strip().lower()
    body_text = visible_text.strip().lower()
    dom_probe = rendered_dom[:20_000].lower()
    visible_probe = f"{title_text}\n{body_text}"
    combined_probe = f"{visible_probe}\n{dom_probe}"
    if body_text == "local_rate_limited":
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="local_rate_limited",
            detail="rendered visible text is the local rate-limit marker",
        )
    if any(marker in visible_probe for marker in _VISIBLE_TIKTOK_CHALLENGE_MARKERS):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="tiktok_slider_or_captcha",
            detail="rendered visible text matches a TikTok slider or captcha challenge",
        )

    if (
        title_text == "access denied"
        and all(marker in combined_probe for marker in _AKAMAI_ACCESS_DENIED_MARKERS)
    ):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="akamai_access_denied",
            detail="rendered title/text/DOM match an Akamai EdgeSuite access-denied page",
        )

    if _looks_like_cloudflare_interstitial(
        title_text=title_text,
        body_text=body_text,
        combined_probe=combined_probe,
    ):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="cloudflare_interstitial",
            detail="rendered title/text/DOM match a Cloudflare browser challenge or JavaScript-required interstitial",
        )
    if (
        "you've been blocked by network security" in combined_probe
        and "file a ticket" in combined_probe
    ):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="reddit_network_security_block",
            detail="rendered page is Reddit's network-security block shell",
        )
    if "click the button below to continue shopping" in combined_probe:
        return RenderedAccessClassification(
            classification=RenderedAccessClass.ACCESS_BLOCKED,
            signal="amazon_continue_shopping_interstitial",
            detail="rendered page is Amazon's continue-shopping bot-mitigation interstitial",
        )
    if _has_cloudflare_challenge_marker(dom_probe):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER,
            signal="residual_cloudflare_challenge_marker",
            detail=(
                "rendered DOM still contains Cloudflare challenge markers, but the rendered "
                "title/text do not match an access-block interstitial"
            ),
        )
    if any(marker in dom_probe for marker in _VISIBLE_TIKTOK_CHALLENGE_MARKERS):
        return RenderedAccessClassification(
            classification=RenderedAccessClass.RESIDUAL_CHALLENGE_MARKER,
            signal="residual_tiktok_challenge_marker",
            detail=(
                "rendered DOM contains TikTok challenge markers, but visible text "
                "does not show the challenge"
            ),
        )
    return RenderedAccessClassification(
        classification=RenderedAccessClass.NO_BLOCK_MARKER,
        signal=None,
        detail="no rendered access-block marker detected",
    )


def _looks_like_cloudflare_interstitial(
    *,
    title_text: str,
    body_text: str,
    combined_probe: str,
) -> bool:
    visible_probe = f"{title_text}\n{body_text}"
    if any(marker in visible_probe for marker in _VISIBLE_CLOUDFLARE_INTERSTITIAL_MARKERS):
        return True
    if "just a moment" in body_text and "cloudflare" in combined_probe:
        return True
    if not body_text and _has_cloudflare_challenge_marker(combined_probe):
        return any(
            marker in combined_probe for marker in _VISIBLE_CLOUDFLARE_INTERSTITIAL_MARKERS
        )
    if "just a moment" in title_text and _has_cloudflare_challenge_marker(combined_probe):
        return _visible_text_is_empty_or_challenge_only(body_text)
    return False


def _visible_text_is_empty_or_challenge_only(body_text: str) -> bool:
    remainder = body_text
    for marker in _CLOUDFLARE_CHALLENGE_ONLY_VISIBLE_MARKERS:
        remainder = remainder.replace(marker, " ")
    return len("".join(char for char in remainder if char.isalnum())) < 20


def _has_cloudflare_challenge_marker(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "__cf_chl_tk",
            "/cdn-cgi/challenge-platform",
            "cdn-cgi/challenge-platform",
            "cf-chl-widget",
            "cf_chl_opt",
        )
    )
