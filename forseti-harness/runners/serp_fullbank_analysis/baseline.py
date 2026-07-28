import json
from pathlib import Path
AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis")

d = json.loads((AN / "unique_contribution.json").read_text(encoding="utf-8"))
for field in ("questions", "domains"):
    print(f"=== unique_contribution {field} (PANEL-ERA baseline) ===")
    for sh, v in sorted(d[field].items(), key=lambda kv: -kv[1]["mean_unique_share"]):
        print(f"  {sh:<16} uniq={v['mean_unique_share']:<7} excl={v['mean_exclusive_items']:<7} "
              f"cov={v['mean_coverage_of_union']:<7} greedy={v['mean_greedy_pick_position']} n={v['n_subjects']}")
    print()

s = json.loads((AN / "social_surface_analysis.json").read_text(encoding="utf-8"))
print("=== social_surface (PANEL-ERA) cells:", len(s["cells"]))
for label in ("per_shape_all", "per_shape_beauty"):
    print(f"--- {label} ---")
    for sh, v in sorted(s[label].items(), key=lambda kv: -kv[1]["mean_social_share"]):
        print(f"  {sh:<16} n={v['n']:<4} share={v['mean_social_share']:<7} vid={v['video_rows']:<6} "
              f"tt={v['tiktok']:<6} ig={v['instagram']:<6} yt={v['youtube']:<6} rd={v['reddit']}")
    print()
print("recurring creators (2+ subjects):", len(s["recurring_creators"]))
for cr, subs in sorted(s["recurring_creators"].items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(subs)}x {cr}")
