import json
from collections import defaultdict
from pathlib import Path
AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis_panel_era_baseline")
d = json.loads((AN / "panel_shape_analysis.json").read_text(encoding="utf-8"))
cells = [c for c in d["cells"] if c["stratum"] == "panel"]
print("panel cells:", len(cells))
bysub = defaultdict(list)
for c in cells:
    bysub[c["subject"]].append(c["shape"])
for s, sh in sorted(bysub.items()):
    print(f"  {s:<34} {len(sh):>2} shapes: {sorted(sh)}")
print()
print("all strata in panel-era cells:", sorted({c['stratum'] for c in d['cells']}))
from collections import Counter
print(Counter(c['stratum'] for c in d['cells']))
