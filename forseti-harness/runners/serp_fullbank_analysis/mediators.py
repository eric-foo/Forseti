"""F12: outlet mediators only — platforms, retailers and marketplaces excluded
(spec: 'retailers, marketplaces and ingredient INCI names are excluded at
harvest'; creators/outlets go to the F12/F19/F21 mediator lists)."""
import json
import re
from pathlib import Path

AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis")
d = json.loads((AN / "fullbank_social_and_axes.json").read_text(encoding="utf-8"))
doms = d["f12_domains_multi_subject"]

PLATFORM = re.compile(r"reddit|youtube|facebook|instagram|tiktok|pinterest|"
                      r"twitter|x\.com|quora|linkedin|threads\.net", re.I)
RETAIL = re.compile(r"amazon|walmart|target|sephora|ulta|costco|nordstrom|cvs|"
                    r"walgreens|ebay|etsy|kohls|macys|bestbuy|shop|store|"
                    r"boots\.com|iherb|thriftbooks|rei\.com|dermstore|"
                    r"lookfantastic|yesstyle|stylevana|olivey", re.I)
BRANDSITE = re.compile(r"cerave|aquaphor|eucerin|olaplex|laneige|rhode|dyson|"
                       r"aeropress|breville|hoka|brooks|purple|helix|supergoop|"
                       r"paulaschoice|drunkelephant|beautyofjoseon|anua|torriden|"
                       r"skin1004|medicube|kosas|dieux|byoma|glowrecipe|"
                       r"summerfridays|phlur|ritual|quip|revlon|shark|fellow|"
                       r"soldejaneiro|bloomnu|drinkag1|ynab|notion", re.I)

outlets = {k: v for k, v in doms.items()
           if not PLATFORM.search(k) and not RETAIL.search(k)
           and not BRANDSITE.search(k)}
print(f"organic domains on 2+ subjects (all)          : {len(doms)}")
print(f"  after excluding platforms/retail/brand sites: {len(outlets)}")
for n in (10, 8, 6, 4, 3, 2):
    k = sum(1 for v in outlets.values() if len(v) >= n)
    print(f"    outlets on >={n:<3} subjects: {k}")
print("\ntop outlet mediators (distinct subjects):")
for k, v in sorted(outlets.items(), key=lambda kv: -len(kv[1]))[:30]:
    print(f"  {len(v):>3}  {k}")
print("\nlivethatglow.com (the F12 specimen):",
      len(doms.get("livethatglow.com", [])), "subjects")
print(" ", ", ".join(doms.get("livethatglow.com", []))[:200])
