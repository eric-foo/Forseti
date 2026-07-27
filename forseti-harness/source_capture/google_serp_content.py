"""Capture-time content extraction for the US-parameterized Google SERP surface.

Extraction is visible-text-primary.  Google serves opaque ``/goto?url=<encrypted>``
anchors on AI-Overview-heavy SERPs, so DOM hrefs are not a reliable locator
surface; the rendered visible text carries displayed domain, path breadcrumb,
price, rating, date, engagement, and module structure consistently.  DOM anchors
enrich a row only where a direct external href exists.  Where a canonical URL is
not source-visible, the row records that fact rather than reconstructing one.

Ported from the SERP lane's ``extract_serp_v2.py`` reference extractor, which was
written against BeautifulSoup/lxml.  This module parses anchors with the stdlib
``html.parser`` the way every other capture adapter in this package does, so the
SERP lane's retention flip does not add a hard third-party parser dependency to
the harness.  The port is behaviour-checked against the reference extractor by
the parity gate (``source_capture/google_serp_parity.py``); the anchor surface is
the only place the two implementations can diverge.

Anomalies raise :class:`GoogleSerpContentAnomaly`.  The capture runners treat a
raising extractor as a content-extraction failure and preserve the rendered DOM
and visible text for that capture, so an unusual-traffic interstitial or a
structurally implausible parse always stays re-extractable instead of being
banked as a thin content record.
"""

from __future__ import annotations

import re
import urllib.parse as up
from html.parser import HTMLParser

GOOGLE_SERP_CONTENT_RECORD_VERSION = "google_serp_content_v2"

MODULE_HEADINGS = {
    "AI Overview": "ai_overview",
    "Web results": "organic",
    "Short videos": "video_block",
    "More short videos": "video_block",
    "Videos": "video_block",
    "People also ask": "people_also_ask",
    "Related searches": "related_search",
    "People also search for": "related_search",
    "Discussions and forums": "forum_block",
    "Top stories": "news_block",
    "Shopping results": "retailer_product",
    "Sponsored": "sponsored",
    "Things to know": "google_synthesis_other",
    "Search Results": "_start",
    "Page Navigation": "_end",
    "Footer Links": "_end",
}

CHROME_LINES = {
    "Skip to main content", "Accessibility help", "Sign in", "AI Mode", "All",
    "Shopping", "Images", "News", "Videos", "Short videos", "More", "Tools",
    "Show all", "Show more", "Read more", "Feedback", "Next", "Help",
    "Send feedback", "Privacy", "Terms", "Books", "Forums", "Web",
}

PLATFORM_HOSTS = {
    "tiktok.com": "tiktok", "instagram.com": "instagram",
    "youtube.com": "youtube", "youtu.be": "youtube",
    "reddit.com": "reddit", "sephora.com": "sephora",
    "amazon.com": "amazon", "ulta.com": "ulta",
    "summerfridays.com": "brand_official", "target.com": "target",
    "nordstrom.com": "nordstrom", "walmart.com": "walmart",
    "facebook.com": "facebook", "pinterest.com": "pinterest",
}

PLATFORM_NAMES = {
    "tiktok": "tiktok", "instagram": "instagram", "youtube": "youtube",
    "reddit": "reddit", "sephora": "sephora", "amazon.com": "amazon",
    "amazon": "amazon", "ulta": "ulta", "facebook": "facebook",
    "pinterest": "pinterest", "target": "target", "walmart": "walmart",
}

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "sca_esv", "ved", "usg", "sa", "fbs", "gclid", "fbclid", "igshid",
    "ref", "ref_src", "si", "feature", "pp", "_r", "is_from_webapp",
    "sender_device", "web_id", "_t",
}

RE_URLLINE = re.compile(r"^https?://([^\s/›]+)\s*(?:›(.*))?$")
RE_DURATION = re.compile(r"^(\d{1,2}:\d{2}|\d+[hm])$")
RE_PLATFORM = re.compile(r"^([A-Za-z][\w.\- ]{1,24})\s*·\s*(.+)$")
RE_ENGAGE = re.compile(r"([\d.,]+[KM]?\+?)\s*(followers|likes|views|comments|votes)", re.I)
RE_DATE = re.compile(
    r"(\d+\s+(?:minute|hour|day|week|month|year)s?\s+ago"
    r"|[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})")
RE_PRICE = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")
RE_RATING = re.compile(r"(\d\.\d)\s*\(([\d,]+)\)")
RE_SPONSORED = re.compile(
    r"\b(sponsored|paid partnership|affiliate|commission|#ad)\b", re.I)
RE_BLOCK_INTERSTITIAL = re.compile(r"unusual traffic|not a robot", re.I)

CARRY_FIELDS = ("visible_date", "engagement_snippet", "price", "rating",
                "rating_count", "duration", "account_or_creator",
                "displayed_domain", "displayed_source", "canonical_url")

# Surface invariants.  A rendered SERP that clears the block tripwire but parses
# to nothing is an extractor defect or an unrecognized layout, not a real empty
# result page -- the class of failure that content-only retention would otherwise
# bank silently.  Both bounds are deliberately loose: they exist to catch a
# structural break, not to police normal result-count variation.
MINIMUM_VISIBLE_TEXT_CHARS = 500
MINIMUM_ROW_COUNT = 3


class GoogleSerpContentAnomaly(Exception):
    """The rendered SERP did not yield an admissible content record."""


class GoogleSerpRouteBlocked(GoogleSerpContentAnomaly):
    """Google served an unusual-traffic interstitial instead of a result surface."""


def canonicalize(url: str) -> str:
    try:
        parts = up.urlsplit(url)
    except ValueError:
        return url
    kept = [(k, v) for k, v in up.parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS]
    return up.urlunsplit((parts.scheme, parts.netloc, parts.path, up.urlencode(kept), ""))


def platform_for(domain: str | None, source_label: str | None) -> str:
    host = (domain or "").lower().removeprefix("www.")
    for suffix, name in PLATFORM_HOSTS.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    label = (source_label or "").strip().lower()
    for key, name in PLATFORM_NAMES.items():
        if label == key or label.startswith(key):
            return name
    return "other"


def dependency_label(module: str, platform: str) -> str:
    if module in {"ai_overview", "people_also_ask", "related_search",
                  "google_synthesis_other"}:
        return "google_synthesis_only"
    if platform in {"tiktok", "instagram", "youtube"}:
        return "platform_native_unverified"
    return "google_composition_primary"


def norm_title(value: str) -> str:
    """Collapse to a comparable key: lowercase alphanumerics, ellipses dropped."""
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


class _AnchorTextParser(HTMLParser):
    """Collect ``normalized anchor text -> direct external href`` pairs.

    Mirrors the reference extractor's BeautifulSoup pass: for every anchor with
    an absolute non-Google href, key the href by the normalized text of the
    anchor and, separately, by the normalized text of an ``h3`` inside it.
    First writer wins, matching ``key not in out``.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: dict[str, str] = {}
        self._anchor_depth = 0
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self._h3_depth = 0
        self._h3_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            if self._anchor_depth == 0:
                self._href = self._external_href(dict(attrs))
                self._anchor_text = []
                self._h3_text = []
                self._h3_depth = 0
            self._anchor_depth += 1
        elif tag == "h3" and self._anchor_depth > 0:
            self._h3_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_depth > 0:
            self._anchor_depth -= 1
            if self._anchor_depth == 0:
                self._flush_anchor()
        elif tag == "h3" and self._h3_depth > 0:
            self._h3_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._anchor_depth == 0 or self._href is None:
            return
        stripped = data.strip()
        if not stripped:
            return
        self._anchor_text.append(stripped)
        if self._h3_depth > 0:
            self._h3_text.append(stripped)

    def _flush_anchor(self) -> None:
        href, self._href = self._href, None
        if href is None:
            return
        for pieces in (self._anchor_text, self._h3_text):
            key = norm_title(" ".join(pieces))
            if len(key) >= 8 and key not in self.hrefs:
                self.hrefs[key] = href
        self._anchor_text = []
        self._h3_text = []

    @staticmethod
    def _external_href(attrs: dict[str, str | None]) -> str | None:
        href = attrs.get("href")
        if not href or not href.startswith("http"):
            return None
        host = (up.urlsplit(href).netloc or "").lower()
        if "google.com" in host or "gstatic.com" in host:
            return None
        return href


def direct_hrefs(rendered_dom: str) -> dict[str, str]:
    """Map normalized anchor text -> direct external href, when Google exposes one."""
    parser = _AnchorTextParser()
    try:
        parser.feed(rendered_dom)
        parser.close()
    except Exception:
        # A malformed tail must not lose the anchors already collected; the row
        # simply records that its destination URL was not source-visible.
        pass
    return parser.hrefs


def match_href(title: str, href_map: dict[str, str]) -> str | None:
    """Exact then prefix match; Google truncates titles with an ellipsis."""
    key = norm_title(title)
    if len(key) < 8:
        return None
    if key in href_map:
        return href_map[key]
    for candidate, href in href_map.items():
        if candidate.startswith(key) or key.startswith(candidate):
            return href
    return None


def is_metadata_only(title: str) -> bool:
    """True when a 'title' is really a card's metadata strip that a blank line split off."""
    rest = title
    for pattern in (RE_ENGAGE, RE_DATE, RE_PRICE, RE_RATING, RE_DURATION):
        rest = pattern.sub(" ", rest)
    rest = re.sub(r"(?i)\b(in stock|out of stock|free delivery|free \d+-day returns?|"
                  r"returns?|ago|and|over|votes?|reviews?)\b", " ", rest)
    rest = re.sub(r"[^A-Za-z]+", "", rest)
    return len(rest) < 3


def merge_metadata_rows(rows: list[dict]) -> list[dict]:
    """Fold metadata-only rows back into the card they were split from, then
    renumber order_in_module so the counts stay faithful."""
    merged: list[dict] = []
    for row in rows:
        if (merged and row["module_type"] == merged[-1]["module_type"]
                and is_metadata_only(row["title"])):
            prev = merged[-1]
            for field in CARRY_FIELDS:
                if prev.get(field) is None and row.get(field) is not None:
                    prev[field] = row[field]
            if row.get("canonical_url") and not prev.get("canonical_url"):
                prev["canonical_url_source_visible"] = True
                prev["canonical_url_absent_reason"] = None
            prev["snippet"] = " | ".join(
                x for x in (prev.get("snippet"), row["title"], row.get("snippet")) if x)[:600]
            continue
        merged.append(row)

    # Backfill domain/platform from a recovered canonical URL, then renumber.
    order: dict[str, int] = {}
    for row in merged:
        if not row.get("displayed_domain") and row.get("canonical_url"):
            row["displayed_domain"] = (
                up.urlsplit(row["canonical_url"]).netloc or "").lower().removeprefix("www.") or None
        if row["platform"] == "other":
            row["platform"] = platform_for(row.get("displayed_domain"),
                                           row.get("displayed_source"))
            row["dependency_label"] = dependency_label(row["module_type"], row["platform"])
        order[row["module_type"]] = order.get(row["module_type"], 0) + 1
        row["order_in_module"] = order[row["module_type"]]
    return merged


def parse_visible_text(
    text: str, href_map: dict[str, str]
) -> tuple[list[dict], list[str], dict]:
    lines = [ln.strip() for ln in text.splitlines()]
    module = "_pre"
    modules_seen: list[str] = []
    rows: list[dict] = []
    order: dict[str, int] = {}
    aio_lines: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        """Turn the accumulated card buffer into one typed row."""
        nonlocal buf
        block = [b for b in buf if b and b not in CHROME_LINES]
        buf = []
        if not block or module.startswith("_"):
            return

        domain = path_hint = None
        url_idx = None
        for index, line in enumerate(block):
            match = RE_URLLINE.match(line)
            if match:
                domain = match.group(1)
                path_hint = (match.group(2) or "").strip()
                url_idx = index
                break

        title = None
        source_label = account = duration = None
        for line in block:
            if RE_DURATION.match(line):
                duration = duration or line
                continue
            match = RE_PLATFORM.match(line)
            if match and not RE_URLLINE.match(line):
                source_label = source_label or match.group(1).strip()
                account = account or match.group(2).strip()
                continue
            if title is None and not RE_URLLINE.match(line) and len(line) > 2:
                title = line
        if title is None:
            return

        joined = " | ".join(block)
        engagement = RE_ENGAGE.search(joined)
        date = RE_DATE.search(joined)
        price = RE_PRICE.search(joined)
        rating = RE_RATING.search(joined)
        snippet = " ".join(block[url_idx + 1:]) if url_idx is not None else " ".join(block[1:])

        if source_label is None and url_idx is not None and url_idx > 0:
            source_label = block[url_idx - 1]

        platform = platform_for(domain, source_label)
        href = match_href(title, href_map)
        canonical = canonicalize(href) if href else None

        order[module] = order.get(module, 0) + 1
        rows.append({
            "module_type": module,
            "order_in_module": order[module],
            "title": title[:300],
            "displayed_source": source_label,
            "displayed_domain": domain,
            "displayed_path_hint": path_hint or None,
            "account_or_creator": account,
            "canonical_url": canonical,
            "canonical_url_source_visible": canonical is not None,
            "canonical_url_absent_reason": (
                None if canonical
                else "Google served an opaque /goto?url= redirect; destination URL "
                     "not source-visible in the rendered SERP"),
            "snippet": snippet[:600] or None,
            "visible_date": date.group(1) if date else None,
            "engagement_snippet": (
                f"{engagement.group(1)} {engagement.group(2).lower()}"
                if engagement else None
            ),
            "duration": duration,
            "price": price.group(0) if price else None,
            "rating": rating.group(1) if rating else None,
            "rating_count": rating.group(2) if rating else None,
            "sponsored_or_affiliate_label": bool(RE_SPONSORED.search(joined)),
            "platform": platform,
            "dependency_label": dependency_label(module, platform),
        })

    def _metadata_shaped(value: str) -> bool:
        return bool(RE_PLATFORM.match(value) or RE_URLLINE.match(value)
                    or RE_DURATION.match(value) or value.lower() in PLATFORM_NAMES)

    for index, line in enumerate(lines):
        nxt = lines[index + 1] if index + 1 < len(lines) else None
        if line in MODULE_HEADINGS:
            flush()
            module = MODULE_HEADINGS[line]
            if not module.startswith("_") and module not in modules_seen:
                modules_seen.append(module)
            continue
        if module == "ai_overview":
            if line:
                aio_lines.append(line)
            continue
        if module == "people_also_ask" and line and line not in CHROME_LINES \
                and not line.rstrip().endswith("?"):
            # PAA block ended without a heading; organic content resumes here.
            module = "organic"
            if "organic" not in modules_seen:
                modules_seen.append("organic")
            buf.append(line)
            continue
        if module in {"people_also_ask", "related_search"}:
            if line and line not in CHROME_LINES:
                order[module] = order.get(module, 0) + 1
                rows.append({
                    "module_type": module, "order_in_module": order[module],
                    "title": line[:300], "displayed_source": "Google",
                    "displayed_domain": None, "displayed_path_hint": None,
                    "account_or_creator": None, "canonical_url": None,
                    "canonical_url_source_visible": False,
                    "canonical_url_absent_reason":
                        "Google-generated query suggestion; no destination URL",
                    "snippet": None, "visible_date": None,
                    "engagement_snippet": None, "duration": None, "price": None,
                    "rating": None, "rating_count": None,
                    "sponsored_or_affiliate_label": False,
                    "platform": "google", "dependency_label": "google_synthesis_only",
                })
            continue
        if not line:
            # A lone title whose metadata block follows the blank stays open
            # ([title][blank][Source · x]... layout).
            next_non_empty = next((x for x in lines[index + 1:] if x), None)
            if (len([b for b in buf if b]) == 1 and next_non_empty is not None
                    and _metadata_shaped(next_non_empty)):
                continue
            flush()
            continue
        # Video tiles are not blank-line separated: a duration line opens a new tile.
        if RE_DURATION.match(line) and any(b for b in buf if b not in CHROME_LINES):
            flush()
        # A title-like line directly before a blank starts a NEW tile; without
        # this, [snippet][NEXT_TITLE] merge into one row.
        if (nxt == "" and buf and line not in CHROME_LINES
                and not _metadata_shaped(line) and len(line) >= 12):
            flush()
        buf.append(line)
    flush()

    rows = merge_metadata_rows(rows)

    # Pair a source-less title row with the pure-metadata row that follows it
    # (title == displayed_source), so domains attach to titles.
    paired: list[dict] = []
    for row in rows:
        prev = paired[-1] if paired else None
        if (prev is not None
                and row["module_type"] == prev["module_type"] == "organic"
                and row.get("displayed_source")
                and row["title"] == row["displayed_source"]
                and not prev.get("displayed_source")):
            for key in ("displayed_source", "displayed_domain", "canonical_url",
                        "visible_date", "engagement_snippet", "snippet",
                        "account_or_creator"):
                if not prev.get(key) and row.get(key):
                    prev[key] = row[key]
            if prev.get("canonical_url"):
                prev["canonical_url_source_visible"] = True
                prev["canonical_url_absent_reason"] = None
            continue
        paired.append(row)
    rows = paired

    ai_overview: dict[str, object] = {}
    if aio_lines:
        cited: list[str] = []
        for index, line in enumerate(aio_lines):
            key = line.strip().lower().rstrip(":")
            if key in PLATFORM_NAMES or (0 < len(line) < 40 and line.startswith("·")):
                cited.append(line.strip("· "))
            elif re.match(r"^\+\d+$", line) and index > 0:
                cited.append(f"{aio_lines[index - 1].strip('· ')} {line}")
        ai_overview = {
            "present": True,
            "visible_line_count": len(aio_lines),
            "visible_char_count": sum(len(x) for x in aio_lines),
            "cited_source_labels": sorted(set(cited)),
            "section_headings": [x for x in aio_lines if x.endswith(":") or
                                 (len(x) < 46 and not x.endswith(".") and " " in x
                                  and x[0].isupper() and "·" not in x)][:12],
        }
    return rows, modules_seen, ai_overview


def _as_text(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _query_of(url: str) -> str:
    try:
        return up.parse_qs(up.urlsplit(url).query).get("q", [""])[0]
    except ValueError:
        return ""


def build_google_serp_content_record(
    *,
    rendered_dom: bytes | str,
    visible_text: bytes | str,
    final_url: str,
    requested_url: str | None = None,
) -> dict:
    """Project one rendered US-parameterized Google SERP into typed result rows.

    Raises :class:`GoogleSerpRouteBlocked` when Google served an unusual-traffic
    interstitial, and :class:`GoogleSerpContentAnomaly` when the rendered surface
    is too thin or too structureless to be a real result page.  Both leave the
    capture raw-preserving through the runner's extraction-failure fallback: a
    block body carries a visible exit IP that must stay diagnosable rather than
    be re-derived, and a structural miss is exactly the defect class that
    content-only retention can no longer repair after the fact.
    """
    text = _as_text(visible_text)
    dom = _as_text(rendered_dom)

    if RE_BLOCK_INTERSTITIAL.search(text):
        raise GoogleSerpRouteBlocked(
            "Google served an unusual-traffic interstitial instead of a result "
            "surface; the interstitial body carries a visible exit IP and is "
            "preserved raw rather than projected into a content record"
        )
    if len(text) < MINIMUM_VISIBLE_TEXT_CHARS:
        raise GoogleSerpContentAnomaly(
            f"rendered visible text was {len(text)} characters, below the "
            f"{MINIMUM_VISIBLE_TEXT_CHARS}-character floor for a result surface"
        )

    href_map = direct_hrefs(dom)
    rows, modules_present, ai_overview = parse_visible_text(text, href_map)

    if len(rows) < MINIMUM_ROW_COUNT:
        raise GoogleSerpContentAnomaly(
            f"extractor produced {len(rows)} typed rows from "
            f"{len(text)} characters of rendered visible text, below the "
            f"{MINIMUM_ROW_COUNT}-row floor; the layout is unrecognized or the "
            "extractor is broken"
        )
    if not modules_present:
        raise GoogleSerpContentAnomaly(
            "no known SERP module heading was found in the rendered visible "
            "text; the layout is unrecognized or the extractor is broken"
        )

    rendered_query = _query_of(final_url)
    requested_query = _query_of(requested_url) if requested_url else rendered_query
    return {
        "content_record_version": GOOGLE_SERP_CONTENT_RECORD_VERSION,
        "requested_url": requested_url or final_url,
        "final_url": final_url,
        "requested_query": requested_query,
        "rendered_query": rendered_query,
        "query_rewritten": (
            requested_query.replace("+", " ") != rendered_query.replace("+", " ")
        ),
        "modules_present": modules_present,
        "ai_overview": ai_overview or {"present": False},
        "visible_text_chars": len(text),
        "direct_href_count": len(href_map),
        "google_location_note": (
            "Google footer reported \"Unknown - Can't determine location\""
            if "Can't determine location" in text
            else None
        ),
        "rows": rows,
    }


__all__ = [
    "GOOGLE_SERP_CONTENT_RECORD_VERSION",
    "GoogleSerpContentAnomaly",
    "GoogleSerpRouteBlocked",
    "MINIMUM_ROW_COUNT",
    "MINIMUM_VISIBLE_TEXT_CHARS",
    "build_google_serp_content_record",
    "canonicalize",
    "dependency_label",
    "direct_hrefs",
    "match_href",
    "parse_visible_text",
    "platform_for",
]
