"""Full-bank coverage reconciliation: run_ledger x query_bank x extracted_v2.

The bank is the authority on what SHOULD exist; the ledger records outcomes;
extracted_v2 is what analysis can actually read. extracted/ holds job_ids from
earlier bank versions and must not be trusted as a coverage count.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
EX = ROOT / "extracted_v2"

bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
ledger_rows = [json.loads(l) for l in
               (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()]
ledger = {r["job_id"]: r for r in ledger_rows}  # last wins

bank_ids = {j["job_id"] for j in bank}
print(f"bank jobs           : {len(bank)}  (distinct ids {len(bank_ids)})")
print(f"ledger rows         : {len(ledger_rows)}  (distinct ids {len(ledger)})")
print(f"extracted_v2 files  : {len(list(EX.glob('*.json')))}")

orphan = sorted(set(ledger) - bank_ids)
print(f"ledger ids NOT in current bank (stale bank versions): {len(orphan)}")

# ---- job-level outcome against the CURRENT bank ----
oc = Counter()
for j in bank:
    r = ledger.get(j["job_id"])
    if r is None:
        oc["pending_never_run"] += 1
    else:
        oc[r["outcome"]] += 1
print("\n=== current-bank job outcomes ===")
for k, v in oc.most_common():
    print(f"  {k:<22}{v:>5}")

# a job is USABLE if outcome ok, not a twin, and a v2 extraction exists
usable, missing_ex = [], []
for j in bank:
    r = ledger.get(j["job_id"])
    if not r or r["outcome"] != "ok":
        continue
    if (EX / f"{j['job_id']}.json").exists():
        usable.append(j)
    else:
        missing_ex.append(j["job_id"])
print(f"\nusable (ok + v2 extraction): {len(usable)}   ok-but-no-extraction: {len(missing_ex)}")

# ---- per-subject completeness ----
bank_shapes = defaultdict(set)
subj_meta = {}
for j in bank:
    # twins are repeat captures of the same shape; they don't widen shape coverage
    bank_shapes[j["subject"]].add(j["shape"])
    subj_meta[j["subject"]] = (j["category"], j["stratum"], j["subject_maturity"])

got_shapes = defaultdict(set)
for j in usable:
    got_shapes[j["subject"]].add(j["shape"])

rows = []
for s, want in sorted(bank_shapes.items()):
    have = got_shapes.get(s, set())
    cat, strat, mat = subj_meta[s]
    rows.append({
        "subject": s, "category": cat, "stratum": strat, "maturity": mat,
        "shapes_in_bank": len(want), "shapes_captured": len(have),
        "frac": round(len(have) / len(want), 3),
        "missing": sorted(want - have),
    })

print(f"\nsubjects in bank: {len(rows)}")
comp = [r for r in rows if r["frac"] == 1.0]
part = [r for r in rows if 0 < r["frac"] < 1.0]
absent = [r for r in rows if r["frac"] == 0]
print(f"  complete (all bank shapes): {len(comp)}")
print(f"  partial                   : {len(part)}")
print(f"  absent (0 captured)       : {len(absent)}")

print("\n=== bank shape-count distribution per subject ===")
print(Counter(r["shapes_in_bank"] for r in rows).most_common())

print("\n=== subjects at >=N captured shapes ===")
for n in range(1, 13):
    k = sum(1 for r in rows if r["shapes_captured"] >= n)
    if k:
        print(f"  >={n:<3} shapes: {k:>3} subjects")

print("\n=== by category: complete / partial / absent ===")
bycat = defaultdict(lambda: Counter())
for r in rows:
    key = "complete" if r["frac"] == 1 else ("absent" if r["frac"] == 0 else "partial")
    bycat[r["category"]][key] += 1
    bycat[r["category"]]["subjects"] += 1
for c, v in sorted(bycat.items()):
    print(f"  {c:<16} n={v['subjects']:<4} complete={v['complete']:<4} "
          f"partial={v['partial']:<4} absent={v['absent']}")

print("\n=== absent subjects (never captured) ===")
for r in absent:
    print(f"  {r['subject'][:44]:<45} {r['category']:<12} bank_shapes={r['shapes_in_bank']}")

print("\n=== partial subjects ===")
for r in sorted(part, key=lambda r: r["frac"]):
    print(f"  {r['subject'][:40]:<41} {r['shapes_captured']}/{r['shapes_in_bank']}  "
          f"missing={','.join(r['missing'])[:60]}")

out = ROOT / "analysis" / "fullbank_coverage.json"
out.write_text(json.dumps({
    "bank_jobs": len(bank), "ledger_rows": len(ledger_rows),
    "ledger_ids_not_in_bank": len(orphan),
    "extracted_v2_files": len(list(EX.glob("*.json"))),
    "outcomes": dict(oc), "usable_jobs": len(usable),
    "subjects": rows,
}, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nwrote {out}")
