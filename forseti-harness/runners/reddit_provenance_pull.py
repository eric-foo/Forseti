"""Exact provenance lookup for the Tower 28 value-playbook claims.

Cross-references `thread_composition_v0.json` substitute-mention quotes
and the underlying raw Reddit comment HTML against claim-matching
regexes (crease/dry-skin failure, shade-range complaints), and checks
one scout-mode SERP extraction (t28-05.json) for packaging-failure
titles.

Consumes: `thread_composition_v0.json` and raw slot packet HTML under
--packets-root; one extract_serp_v2 JSON (`t28-05.json`) under
--scout-extractions.
Emits: a provenance report printed to stdout only (no file output).

Fixture data (the Tower 28 Reddit capture packets and scout SERP
extractions) lives on the operator drive, not in this repo; pass
--packets-root / --scout-extractions to point at different locations.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Reddit comment text carries emoji; a cp1252 console (Windows default)
# raises UnicodeEncodeError mid-print and kills the run partway through the
# provenance dump, truncating output that had otherwise succeeded. Degrade
# unprintable characters instead of dying.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_PACKETS_ROOT = r"C:\tmp\forseti-tower28-reddit-20260728"
DEFAULT_SCOUT_EXTRACTIONS = r"C:\tmp\forseti-tower28-scout-20260727\extracted_v2"

CLAIMS = {
    "1. crease/dry-skin failure": re.compile(
        r"emphasiz|creas|dried down|dry.{0,40}(return|regret)|"
        r"returning the concealer", re.I),
    "3. shade range (Haus Labs 35pt)": re.compile(
        r"color variety|shade match|shade range", re.I),
}


def main():
    ap = argparse.ArgumentParser(
        description="Exact provenance lookup for the Tower 28 "
                     "value-playbook claims.")
    ap.add_argument("--packets-root", default=DEFAULT_PACKETS_ROOT,
                     help="dir containing thread_composition_v0.json and "
                          "raw slot packets, operator drive "
                          f"(default: {DEFAULT_PACKETS_ROOT})")
    ap.add_argument("--scout-extractions", default=DEFAULT_SCOUT_EXTRACTIONS,
                     help="dir of scout-mode extract_serp_v2 JSONs "
                          "(e.g. t28-05.json), operator drive "
                          f"(default: {DEFAULT_SCOUT_EXTRACTIONS})")
    args = ap.parse_args()

    r = Path(args.packets_root)
    s = Path(args.scout_extractions)

    threads_path = r / "thread_composition_v0.json"
    if not threads_path.exists():
        sys.exit(
            f"ERROR: thread_composition_v0.json not found at {threads_path}\n"
            "Run reddit_thread_composition.py first to produce it, or pass "
            "--packets-root to point at a location where it already exists.")
    threads = json.loads(threads_path.read_text(encoding="utf-8"))

    for label, rx in CLAIMS.items():
        print(f"\n##### {label}")
        for t in threads:
            for m in t["substitute_mentions"]:
                if rx.search(m["quote"]):
                    print(f"  [{t['slot']}] {t['url']}")
            # also scan full comments file? composition kept only mention quotes;
            # rescan raw for the pattern with scores
        for t in threads:
            pdir = r / f"{t['slot']}_packet"
            raw = (pdir / "raw" / "01_http_response_body.bin").read_bytes()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw, "html.parser")
            for thing in soup.select("div.thing.comment"):
                body_el = thing.select_one("div.md")
                if not body_el:
                    continue
                body = body_el.get_text(" ", strip=True)
                if rx.search(body):
                    score_el = thing.select_one("span.score.unvoted")
                    score = score_el.get_text(strip=True) if score_el else "?"
                    print(f"  [{t['slot']} | {score}] \"{body[:150]}\"")
                    print(f"      {t['url']}")

    print("\n##### 2. packaging failure (SERP titles, job t28-05)")
    pkt_path = s / "t28-05.json"
    if not pkt_path.exists():
        sys.exit(
            f"ERROR: t28-05.json not found at {pkt_path}\n"
            "This script requires the Tower 28 scout SERP extraction "
            "fixture on the operator drive. Pass --scout-extractions to "
            "point at a different location.")
    pkt = json.loads(pkt_path.read_text(encoding="utf-8"))
    print("  query:", pkt["requested_query"])
    for row in pkt["rows"]:
        t = row.get("title") or ""
        if re.search(r"wont open|won't open|broken|fix", t, re.I):
            print(f"  [{row['module_type']}] \"{t[:90]}\"")


if __name__ == "__main__":
    main()
