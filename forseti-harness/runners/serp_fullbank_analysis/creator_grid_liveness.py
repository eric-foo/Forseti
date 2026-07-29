r"""Creator grid liveness: cadence, dormancy, and reach trajectory.

Reads the TikTok assessment captures (profile + 30-video grid, no video
opens) and derives three things the SERP lane needs and was not recording:

  cadence_days_per_video  how much CALENDAR a 30-video grid covers. Spans
                          0.9 to 47.5 days/video across our creators -- a
                          53x range -- which decides whether a SERP-
                          referenced video from N days ago falls inside
                          the captured window at all.
  activity_state          ACTIVE / SLOWING / DORMANT from the newest
                          video's age. Grid SPAN measures cadence, not
                          life; only newest-video age measures life.
  reach_trend             median plays in the grid's oldest third vs its
                          newest third -- the creator's own trajectory,
                          measured within one capture so it carries no
                          cross-era comparison.

Why reach_trend matters beyond curiosity: the ratified engagement rule
weights a row against "the creator's own recent-grid median". If that
median is itself collapsing, the weight is a function of capture date
rather than of the row. This derivation exists to make that testable.

Writes analysis/creator_grid_liveness.json to the dogfood store.
Operator-drive-pinned like the rest of this directory.
"""
import json
import statistics
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STORE = Path(r"C:\tmp\forseti-creator-dogfood-20260729")
DORMANT_DAYS = 90.0
SLOWING_DAYS = 30.0
FALL_RATIO = 0.5
RISE_RATIO = 2.0

now = time.time()
rows = []
for d in sorted(p for p in STORE.iterdir() if p.is_dir()):
    grid = d / "tiktok_grid_window.json"
    if not grid.exists():
        rows.append({"handle": d.name, "status": "no_grid_captured"})
        continue
    j = json.loads(grid.read_text(encoding="utf-8"))
    items = [it for it in (j.get("items") or []) if it.get("createTime")]
    if not items:
        rows.append({"handle": d.name, "status": "grid_without_timestamps"})
        continue
    items.sort(key=lambda it: it["createTime"])
    ts = [it["createTime"] for it in items]
    newest_age = (now - max(ts)) / 86400
    span = (max(ts) - min(ts)) / 86400
    cadence = span / max(len(ts) - 1, 1)
    state = ("DORMANT" if newest_age > DORMANT_DAYS
             else "SLOWING" if newest_age > SLOWING_DAYS else "ACTIVE")

    def med_plays(sub):
        v = [int((it.get("stats") or {}).get("playCount") or 0) for it in sub]
        v = [x for x in v if x]
        return statistics.median(v) if v else None

    third = max(len(items) // 3, 1)
    old, new = med_plays(items[:third]), med_plays(items[-third:])
    ratio = (new / old) if (old and new) else None
    trend = (None if ratio is None else
             "FALLING" if ratio < FALL_RATIO else
             "RISING" if ratio > RISE_RATIO else "STEADY")
    author_ids = sorted({it.get("author", {}).get("id")
                         for it in items if it.get("author")} - {None})
    prof = (j.get("profile_metrics") or {}).get("follower_count", {})
    rows.append({
        "handle": d.name, "status": "ok",
        "author_id": author_ids[0] if author_ids else None,
        "followers": prof.get("exact_value_or_none"),
        "grid_rows": len(items),
        "newest_video_age_days": round(newest_age, 1),
        "grid_span_days": round(span, 1),
        "cadence_days_per_video": round(cadence, 2),
        "activity_state": state,
        "median_plays_oldest_third": old,
        "median_plays_newest_third": new,
        "reach_ratio_new_over_old": round(ratio, 3) if ratio else None,
        "reach_trend": trend,
    })

ok = [r for r in rows if r["status"] == "ok"]
trends = [r["reach_trend"] for r in ok if r["reach_trend"]]
out = {
    "artifact": "creator_grid_liveness",
    "derivation": "creator_grid_liveness.py over the TikTok assessment "
                  "captures (new_capture intent: profile + grid metadata, "
                  "no video opens)",
    "thresholds": {"dormant_days": DORMANT_DAYS, "slowing_days": SLOWING_DAYS,
                   "fall_ratio": FALL_RATIO, "rise_ratio": RISE_RATIO},
    "n_creators": len(rows), "n_with_grid": len(ok),
    "activity_states": {s: sum(1 for r in ok if r["activity_state"] == s)
                        for s in ("ACTIVE", "SLOWING", "DORMANT")},
    "reach_trends": {t: trends.count(t)
                     for t in ("FALLING", "STEADY", "RISING")},
    "cadence_range_days_per_video": [
        min(r["cadence_days_per_video"] for r in ok),
        max(r["cadence_days_per_video"] for r in ok)],
    "distinct_author_ids": len({r["author_id"] for r in ok if r["author_id"]}),
    "non_claims": [
        "observed counts from one capture per creator; never prevalence",
        "reach_trend is the creator's own within-grid trajectory, not a "
        "comparison against other creators or platforms",
        "this population recurs across 2+ SERP subjects and is therefore "
        "BIASED toward active creators by construction; dormant creators "
        "are likelier among the single-subject population never captured",
    ],
    "creators": rows,
}
(STORE / "creator_grid_liveness.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"creators: {len(rows)} ({len(ok)} with grids, "
      f"{out['distinct_author_ids']} distinct accounts)")
print(f"activity: {out['activity_states']}")
print(f"reach   : {out['reach_trends']}")
print(f"cadence : {out['cadence_range_days_per_video'][0]} to "
      f"{out['cadence_range_days_per_video'][1]} days/video")
for r in rows:
    if r["status"] != "ok":
        print(f"  !! {r['handle']}: {r['status']}")
