import json
from pathlib import Path
AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis")
led = json.loads((AN / "fullbank_competitor_ledger.json").read_text(encoding="utf-8"))
cands = [e for e in led["entries"] if e["rung"] == "candidate"]
print(f"candidate-rung entries: {len(cands)}")
for e in sorted(cands, key=lambda e: (e["subject"], -e["distinct_queries"])):
    print(f"{e['distinct_queries']:>3} {e['subject'][:30]:<31} {e['type'][:16]:<17} {e['name']}")
