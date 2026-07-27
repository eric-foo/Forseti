"""Reddit thread composition reader (J3) + Channel-3 substitute harvest.

Parses raw old-Reddit HTML from captured slot packets to extract, per
thread: title, comment count, score-visible counts, and every comment
naming a potential substitute/competitor (the Channel-3 inbound wire:
complaint-borne names -> substitute_down candidates).

Consumes: `batch_summary.json` (slot manifest) and each slot's raw
`01_http_response_body.bin` HTML, under --packets-root.
Emits: `thread_composition_v0.json` (per-thread report) under
--output (default: <packets-root>/thread_composition_v0.json), plus a
per-thread summary printed to stdout.

Counts of captured comments only — threads may truncate at page 1; no
prevalence claims.

Fixture data (the Tower 28 Reddit capture packets) lives on the
operator drive, not in this repo; pass --packets-root to point at a
different location.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Reddit comment text carries emoji; a cp1252 console (Windows default)
# raises UnicodeEncodeError mid-print and kills the run after the JSON is
# already written, so the crash looks like a failure of work that in fact
# succeeded. Degrade unprintable characters instead of dying.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_PACKETS_ROOT = r"C:\tmp\forseti-tower28-reddit-20260728"

# names to watch: harvested ledger + common drugstore/prestige concealer
# brands + HOCl rivals (watch-list, not a claim of relevance)
WATCH = ["nyx", "hourglass", "saie", "haus labs", "e.l.f", "elf ",
         "maybelline", "l'oreal", "loreal", "la girl", "catrice",
         "kosas", "rare beauty", "ilia", "merit", "glossier",
         "tarte", "nars", "it cosmetics", "revolution", "essence",
         "magic molecule", "active skin repair", "briotech", "sos",
         "drugstore"]
POS_RX = re.compile(r"\b(love|amazing|holy grail|obsessed|great|perfect|"
                    r"the best|so good)\b", re.I)
NEG_RX = re.compile(r"\b(hate|awful|terrible|broke me out|breaking me out|"
                    r"creas\w+|dry|dries|patchy|cakey|oxidiz\w+|"
                    r"disappoint\w+|returned|return it|not for me|"
                    r"didn'?t work|doesn'?t work)\b", re.I)


def main():
    ap = argparse.ArgumentParser(
        description="Reddit thread composition read (J3) + Channel-3 "
                     "substitute harvest from captured slot packets.")
    ap.add_argument("--packets-root", default=DEFAULT_PACKETS_ROOT,
                     help="dir containing batch_summary.json and slot "
                          "packets, operator drive "
                          f"(default: {DEFAULT_PACKETS_ROOT})")
    ap.add_argument("--output",
                     help="output JSON path override "
                          "(default: <packets-root>/thread_composition_v0.json)")
    args = ap.parse_args()

    root = Path(args.packets_root)
    summary_path = root / "batch_summary.json"
    if not summary_path.exists():
        sys.exit(
            f"ERROR: batch_summary.json not found at {summary_path}\n"
            "This script requires the Tower 28 Reddit capture fixture "
            "(slot packets + batch_summary.json) on the operator drive. "
            "Pass --packets-root to point at a different location.")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = []
    for slot in summary["results"]:
        pdir = Path(slot["packet_dir"])
        html = (pdir / "raw" / "01_http_response_body.bin").read_bytes()
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.select_one("a.title")
        title = title_el.get_text(" ", strip=True) if title_el else "?"
        comments = []
        for thing in soup.select("div.thing.comment"):
            body_el = thing.select_one("div.md")
            if not body_el:
                continue
            body = body_el.get_text(" ", strip=True)
            score_el = thing.select_one("span.score.unvoted")
            score = score_el.get_text(strip=True) if score_el else None
            comments.append({"body": body, "score": score})
        mentions = []
        for c in comments:
            low = c["body"].lower()
            hits = sorted({w.strip() for w in WATCH if w in low})
            if hits:
                mentions.append({"names": hits, "score": c["score"],
                                 "quote": c["body"][:200]})
        pos = sum(1 for c in comments if POS_RX.search(c["body"]))
        neg = sum(1 for c in comments if NEG_RX.search(c["body"]))
        report.append({
            "slot": slot["slot_id"], "url": slot["url"], "title": title,
            "captured_comments": len(comments),
            "keyword_pos": pos, "keyword_neg": neg,
            "substitute_mentions": mentions,
        })

    out_path = Path(args.output) if args.output else (
        root / "thread_composition_v0.json")
    out_path.write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    for r in report:
        print(f"\n=== {r['slot']} {r['title'][:70]}")
        print(f"    comments={r['captured_comments']} kw_pos={r['keyword_pos']} "
              f"kw_neg={r['keyword_neg']} sub_mentions={len(r['substitute_mentions'])}")
        for m in r["substitute_mentions"][:4]:
            print(f"    [{m['score']}] {m['names']} :: {m['quote'][:110]}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
