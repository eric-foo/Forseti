"""v2: extract_serp with the PAA-exit fix (EXTRACTOR_VERSION = "2").

Google resumes organic results after a "People also ask" block WITHOUT a new
module heading on many layouts (observed megadogfood j0000/j0002). v1 typed
everything until the next heading as PAA. v2 exits the PAA module at the
first non-question line and reprocesses it as organic content. Related
searches keep v1 behavior (their rows are not question-shaped).

Original doc: Normalize SERP composition packets into typed result rows.

Extraction is visible-text-primary. Google serves opaque `/goto?url=<encrypted>`
anchors on AI-Overview-heavy SERPs, so DOM hrefs are not a reliable locator
surface; the rendered visible text carries displayed domain, path breadcrumb,
price, rating, date, engagement, and module structure consistently. DOM anchors
are used only to enrich rows where a direct external href exists.

Where a canonical URL is not source-visible, the row records that fact rather
than reconstructing one.
"""

import json
import re
import urllib.parse as up
from pathlib import Path

from bs4 import BeautifulSoup

LAKE = Path(r"C:\tmp\forseti-sf-serp-social-composition-20260726\data")

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


def canonicalize(url: str) -> str:
    try:
        p = up.urlsplit(url)
    except ValueError:
        return url
    kept = [(k, v) for k, v in up.parse_qsl(p.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS]
    return up.urlunsplit((p.scheme, p.netloc, p.path, up.urlencode(kept), ""))


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


def norm_title(s: str) -> str:
    """Collapse to a comparable key: lowercase alphanumerics, ellipses dropped."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def direct_hrefs(soup: BeautifulSoup) -> dict[str, str]:
    """Map normalized anchor text -> direct external href, when Google exposes one."""
    out: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            continue
        host = (up.urlsplit(href).netloc or "").lower()
        if "google.com" in host or "gstatic.com" in host:
            continue
        for candidate in (a.get_text(" ", strip=True),
                          (a.find("h3").get_text(" ", strip=True) if a.find("h3") else "")):
            key = norm_title(candidate)
            if len(key) >= 8 and key not in out:
                out[key] = href
    return out


def match_href(title: str, href_map: dict[str, str]) -> str | None:
    """Exact then prefix match; Google truncates titles with an ellipsis."""
    key = norm_title(title)
    if len(key) < 8:
        return None
    if key in href_map:
        return href_map[key]
    for cand, href in href_map.items():
        if cand.startswith(key) or key.startswith(cand):
            return href
    return None


CARRY_FIELDS = ("visible_date", "engagement_snippet", "price", "rating",
                "rating_count", "duration", "account_or_creator",
                "displayed_domain", "displayed_source", "canonical_url")


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


def parse_visible_text(text: str, href_map: dict[str, str]) -> tuple[list[dict], list[str], dict]:
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
        for i, ln in enumerate(block):
            m = RE_URLLINE.match(ln)
            if m:
                domain, path_hint, url_idx = m.group(1), (m.group(2) or "").strip(), i
                break

        title = None
        source_label = account = duration = None
        for ln in block:
            if RE_DURATION.match(ln):
                duration = duration or ln
                continue
            m = RE_PLATFORM.match(ln)
            if m and not RE_URLLINE.match(ln):
                source_label = source_label or m.group(1).strip()
                account = account or m.group(2).strip()
                continue
            if title is None and not RE_URLLINE.match(ln) and len(ln) > 2:
                title = ln
        if title is None:
            return

        joined = " | ".join(block)
        eng = RE_ENGAGE.search(joined)
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
                else "Google served an opaque /goto?url= redirect; destination URL not source-visible in the rendered SERP"),
            "snippet": snippet[:600] or None,
            "visible_date": date.group(1) if date else None,
            "engagement_snippet": f"{eng.group(1)} {eng.group(2).lower()}" if eng else None,
            "duration": duration,
            "price": price.group(0) if price else None,
            "rating": rating.group(1) if rating else None,
            "rating_count": rating.group(2) if rating else None,
            "sponsored_or_affiliate_label": bool(RE_SPONSORED.search(joined)),
            "platform": platform,
            "dependency_label": dependency_label(module, platform),
        })

    def _metadata_shaped(s):
        return bool(RE_PLATFORM.match(s) or RE_URLLINE.match(s)
                    or RE_DURATION.match(s) or s.lower() in PLATFORM_NAMES)

    for i, ln in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if ln in MODULE_HEADINGS:
            flush()
            module = MODULE_HEADINGS[ln]
            if not module.startswith("_") and module not in modules_seen:
                modules_seen.append(module)
            continue
        if module == "ai_overview":
            if ln:
                aio_lines.append(ln)
            continue
        if module == "people_also_ask" and ln and ln not in CHROME_LINES \
                and not ln.rstrip().endswith("?"):
            # PAA block ended without a heading; organic content resumes here.
            module = "organic"
            if "organic" not in modules_seen:
                modules_seen.append("organic")
            buf.append(ln)
            continue
        if module in {"people_also_ask", "related_search"}:
            if ln and ln not in CHROME_LINES:
                order[module] = order.get(module, 0) + 1
                rows.append({
                    "module_type": module, "order_in_module": order[module],
                    "title": ln[:300], "displayed_source": "Google",
                    "displayed_domain": None, "displayed_path_hint": None,
                    "account_or_creator": None, "canonical_url": None,
                    "canonical_url_source_visible": False,
                    "canonical_url_absent_reason": "Google-generated query suggestion; no destination URL",
                    "snippet": None, "visible_date": None,
                    "engagement_snippet": None, "duration": None, "price": None,
                    "rating": None, "rating_count": None,
                    "sponsored_or_affiliate_label": False,
                    "platform": "google", "dependency_label": "google_synthesis_only",
                })
            continue
        if not ln:
            # v2: a lone title whose metadata block follows the blank stays
            # open ([title][blank][Source · x]... layout, megadogfood j0000).
            nxt_ne = next((x for x in lines[i + 1:] if x), None)
            if (len([b for b in buf if b]) == 1 and nxt_ne is not None
                    and _metadata_shaped(nxt_ne)):
                continue
            flush()
            continue
        # Video tiles are not blank-line separated: a duration line opens a new tile.
        if RE_DURATION.match(ln) and any(b for b in buf if b not in CHROME_LINES):
            flush()
        # v2: a title-like line directly before a blank starts a NEW tile;
        # without this, [snippet][NEXT_TITLE] merge into one row.
        if (nxt == "" and buf and ln not in CHROME_LINES
                and not _metadata_shaped(ln) and len(ln) >= 12):
            flush()
        buf.append(ln)
    flush()

    rows = merge_metadata_rows(rows)

    # v2: pair a source-less title row with the pure-metadata row that
    # follows it (title == displayed_source), so domains attach to titles.
    paired = []
    for r in rows:
        prev = paired[-1] if paired else None
        if (prev is not None
                and r["module_type"] == prev["module_type"] == "organic"
                and r.get("displayed_source")
                and r["title"] == r["displayed_source"]
                and not prev.get("displayed_source")):
            for k in ("displayed_source", "displayed_domain", "canonical_url",
                      "visible_date", "engagement_snippet", "snippet",
                      "account_or_creator"):
                if not prev.get(k) and r.get(k):
                    prev[k] = r[k]
            if prev.get("canonical_url"):
                prev["canonical_url_source_visible"] = True
                prev["canonical_url_absent_reason"] = None
            continue
        paired.append(r)
    rows = paired

    aio = {}
    if aio_lines:
        cited = []
        for i, ln in enumerate(aio_lines):
            key = ln.strip().lower().rstrip(":")
            if key in PLATFORM_NAMES or (0 < len(ln) < 40 and ln.startswith("·")):
                cited.append(ln.strip("· "))
            elif re.match(r"^\+\d+$", ln) and i > 0:
                cited.append(f"{aio_lines[i-1].strip('· ')} {ln}")
        aio = {
            "present": True,
            "visible_line_count": len(aio_lines),
            "visible_char_count": sum(len(x) for x in aio_lines),
            "cited_source_labels": sorted(set(cited)),
            "section_headings": [x for x in aio_lines if x.endswith(":") or
                                 (len(x) < 46 and not x.endswith(".") and " " in x
                                  and x[0].isupper() and "·" not in x)][:12],
        }
    return rows, modules_seen, aio


def extract_packet(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet_dir = manifest_path.parent
    dom_path = packet_dir / "raw" / "01_cloakbrowser_rendered_dom.html"
    txt_path = packet_dir / "raw" / "02_cloakbrowser_visible_text.txt"

    locator = manifest.get("source_locator", {}).get("value", "")
    requested_q = up.parse_qs(up.urlsplit(locator).query).get("q", [""])[0]
    warnings = manifest.get("warnings", []) or []
    final_url = ""
    for w in warnings:
        m = re.search(r"landed at (\S+) from requested URL", w)
        if m:
            final_url = m.group(1)
    rendered_q = (up.parse_qs(up.urlsplit(final_url).query).get("q", [""])[0]
                  if final_url else requested_q)

    base = {
        "packet_id": manifest["packet_id"],
        "manifest_relpath": str(manifest_path.relative_to(LAKE)).replace("\\", "/"),
        "source_surface": manifest.get("source_surface"),
        "requested_query": requested_q,
        "rendered_query": rendered_q,
        "query_rewritten": requested_q.replace("+", " ") != rendered_q.replace("+", " "),
        "requested_url": locator,
        "final_url": final_url or locator,
        "capture_timestamp": manifest.get("timing", {}).get("capture_time", {}).get("value"),
        "limitations": manifest.get("limitations", []),
        "warnings": warnings,
    }

    if not txt_path.exists():
        return {**base, "rows": [], "modules_present": [], "ai_overview": {"present": False},
                "note": "non-browser packet (no rendered visible text)"}

    text = txt_path.read_text(encoding="utf-8", errors="replace")

    # A Google unusual-traffic interstitial is a typed route failure, not content.
    # Its body carries a visible exit IP, which must never reach a durable artifact.
    if re.search(r"unusual traffic|not a robot", text, re.I):
        return {
            **base, "rows": [], "modules_present": [],
            "ai_overview": {"present": False},
            "route_verdict": "blocked_google_unusual_traffic",
            "route_blocker": (
                "Google served an unusual-traffic interstitial instead of a result surface. "
                "The interstitial body contains a visible exit IP and is retained in the raw "
                "lake only; it is withheld from durable artifacts per the route decision."),
            "visible_text_chars": len(text),
        }

    soup = BeautifulSoup(dom_path.read_text(encoding="utf-8", errors="replace"), "lxml")
    hrefs = direct_hrefs(soup)
    rows, modules, aio = parse_visible_text(text, hrefs)

    location_note = None
    if "Can't determine location" in text:
        location_note = "Google footer reported \"Unknown - Can't determine location\""

    return {
        **base,
        "modules_present": modules,
        "ai_overview": aio or {"present": False},
        "visible_text_chars": len(text),
        "direct_href_count": len(hrefs),
        "google_location_note": location_note,
        "rows": rows,
    }


def main() -> None:
    out = []
    for avail in sorted((LAKE / "indexes" / "availability").glob("*.json")):
        entry = json.loads(avail.read_text(encoding="utf-8"))
        out.append(extract_packet(LAKE / entry["manifest_relpath"]))
    dest = Path(__file__).parent / "serp_rows.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(len(p["rows"]) for p in out)
    print(f"packets={len(out)} rows={total}")
    for p in out:
        vis = sum(1 for r in p["rows"] if r["canonical_url_source_visible"])
        print(f"  rows={len(p['rows']):>3} url_visible={vis:>3} "
              f"aio={str(p['ai_overview'].get('present', False)):>5} "
              f"mods={len(p['modules_present'])} q={p.get('requested_query', '')[:50]}")
    print("wrote", dest)


if __name__ == "__main__":
    main()
