import json
from pathlib import Path
AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis")
led = json.loads((AN / "fullbank_competitor_ledger.json").read_text(encoding="utf-8"))
want = {("aeropress", "Premium"), ("hoka clifton 9", "Bondi 9"),
        ("breville barista express", "Bambino Plus"), ("olaplex no 3", "original"),
        ("aeropress", "ORB")}
for e in led["entries"]:
    if (e["subject"], e["name"]) in want:
        print(f"--- {e['subject']} / {e['name']} (q={e['distinct_queries']}, {e['type']}) ---")
        for s in e["sources"][:6]:
            print(f"    [{s['surface_class']}] {s['evidence'][:110]}")
