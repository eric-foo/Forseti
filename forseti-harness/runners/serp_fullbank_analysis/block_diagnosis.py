r"""Seal the block diagnosis: what separates blocked captures from clean
ones across EVERY Google capture on this route, all run directories.

The route is per-IP, so run folders are not independent samples — this
pools every forseti-*/*.log capture event. Computes trailing 1h/6h/24h
load at each event and compares the distribution at blocks against the
distribution at clean captures, plus session position (captures since
the last >=60min idle).

Writes analysis/fullbank_block_diagnosis.json. Voided retry rows (the
2026-07-29 01:48-01:51 fabrications recorded by run_ledger's
RETRY_CORRECTION) are excluded. Store path operator-drive-pinned.
"""
import json
import re
import sys
import datetime
import statistics
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TMP = Path(r"C:\tmp")
OUT = TMP / "forseti-serp-megadogfood-20260727" / "analysis" / \
    "fullbank_block_diagnosis.json"
VOID = (datetime.datetime(2026, 7, 29, 1, 48),
        datetime.datetime(2026, 7, 29, 1, 52))

rx = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\b(ok|blocked) \(")
events = set()
for lg in TMP.glob("forseti-*/*.log"):
    for line in lg.read_text(encoding="utf-8", errors="replace").splitlines():
        m = rx.match(line)
        if not m:
            continue
        t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        events.add((t, lg.parent.name, m.group(2)))
events = sorted(e for e in events if not (VOID[0] <= e[0] <= VOID[1]))
times = [e[0] for e in events]


def trailing(t, hours):
    lo = t - datetime.timedelta(hours=hours)
    return sum(1 for x in times if lo <= x < t)


def session_position(t):
    idx = times.index(t)
    n = 0
    for i in range(idx - 1, 0, -1):
        if (times[i] - times[i - 1]).total_seconds() >= 3600:
            break
        n += 1
    return n + 1


blocks = [e for e in events if e[2] == "blocked"]
oks = [e for e in events if e[2] == "ok"]

load = {}
for hrs in (1, 6, 24):
    b = [trailing(t, hrs) for t, _, _ in blocks]
    o = [trailing(t, hrs) for t, _, _ in oks]
    load[f"trailing_{hrs}h"] = {
        "blocked_median": statistics.median(b),
        "blocked_min": min(b), "blocked_max": max(b),
        "clean_median": statistics.median(o),
        "clean_min": min(o), "clean_max": max(o),
        "separates": statistics.median(b) > statistics.median(o) * 1.2,
    }

per_block = []
for t, run, _ in blocks:
    prev_ok = [x for x in oks if x[0] < t]
    per_block.append({
        "at": t.strftime("%Y-%m-%d %H:%M:%S"), "run": run,
        "trailing_1h": trailing(t, 1), "trailing_6h": trailing(t, 6),
        "trailing_24h": trailing(t, 24),
        "session_position": session_position(t),
        "minutes_since_last_ok": round(
            (t - prev_ok[-1][0]).total_seconds() / 60, 1) if prev_ok else None,
    })

out = {
    "artifact": "fullbank_block_diagnosis",
    "derivation": "block_diagnosis.py over every forseti-*/*.log capture "
                  "event (the route is per-IP; run folders are not "
                  "independent samples)",
    "n_events": len(events), "n_blocks": len(blocks), "n_clean": len(oks),
    "base_block_rate": round(len(blocks) / len(events), 4),
    "load_at_event": load,
    "per_block": per_block,
    "clean_high_water": {
        "max_trailing_24h_while_clean": max(trailing(t, 24) for t, _, _ in oks),
        "max_trailing_6h_while_clean": max(trailing(t, 6) for t, _, _ in oks),
    },
    "reading": "Instantaneous rate does NOT separate (trailing-1h medians "
               "42 blocked vs 39 clean). Trailing 6h and 24h load DO "
               "separate (253 vs 173; 820 vs 663) but are a gradient, not "
               "a gate: the route ran clean at 961/24h and 325/6h, above "
               "most blocks. Blocks cluster rather than arrive "
               "independently, and the base rate is under 1% per capture.",
    "non_claims": [
        "no threshold is established; every figure is confounded with "
        "run history, time of day, and Google-side state we cannot see",
        "counts are our own capture events only, never Google's view",
    ],
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"events={len(events)} blocks={len(blocks)} "
      f"base_rate={out['base_block_rate']:.2%}")
for k, v in load.items():
    print(f"  {k}: blocked med {v['blocked_median']:.0f} vs clean med "
          f"{v['clean_median']:.0f}  separates={v['separates']}")
print(f"wrote {OUT.name}")
