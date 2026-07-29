import json
from pathlib import Path
from collections import Counter
EX = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\extracted_v2")

mt = Counter()
aio_keys = Counter()
row_keys = Counter()
n_aio = 0
sample_aio = None
for p in sorted(EX.glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for r in d.get("rows", []):
        mt[r["module_type"]] += 1
        for k in r:
            row_keys[k] += 1
    a = d.get("ai_overview") or {}
    if a.get("present"):
        n_aio += 1
        for k in a:
            aio_keys[k] += 1
        if sample_aio is None:
            sample_aio = (p.name, a)
print("module_types:", mt.most_common())
print()
print("row keys:", row_keys.most_common())
print()
print("packets with AIO present:", n_aio)
print("aio keys:", aio_keys.most_common())
print()
name, a = sample_aio
print("sample AIO from", name)
print(json.dumps(a, indent=1, ensure_ascii=False)[:2000])
