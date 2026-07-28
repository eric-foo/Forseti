"""Full-bank shape-value analysis (F4-F7), scoped by the stated coverage bar.

Coverage bar (applied consistently, stated in the findings note):
  * universe = the CURRENT 986-job query_bank (ledger ids outside it come from
    superseded bank versions and are excluded);
  * a job enters analysis iff outcome==ok, not a twin, and a v2 extraction
    exists;
  * a SUBJECT enters cross-subject statistics only if COMPLETE — every job the
    current bank holds for it came back ok. 88 of 98 subjects are complete;
    10 are absent entirely; ZERO are partial, so no partial-subject averaging
    risk exists in this store.
  * shape comparisons are computed WITHIN a stratum, because the bank gives
    each stratum a different shape set. Unique-share is mechanically depressed
    by a larger competing shape set, so cross-stratum pooling of unique_share
    is not a like-for-like comparison and is reported separately/labelled.
"""
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
sys.path.insert(0, str(ROOT / "bin"))
import analyze_megadogfood as A  # loaders/metrics only

EX = ROOT / "extracted_v2"
AN = ROOT / "analysis"

bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
ledger = {json.loads(l)["job_id"]: json.loads(l)
          for l in (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()}

# --- complete subjects ---
by_subj_jobs = defaultdict(list)
for j in bank:
    by_subj_jobs[j["subject"]].append(j)
complete = {s for s, js in by_subj_jobs.items()
            if all((ledger.get(j["job_id"]) or {}).get("outcome") == "ok" for j in js)}
print(f"complete subjects: {len(complete)} / {len(by_subj_jobs)}")

# --- cells ---
cells = []
for j in bank:
    if j["subject"] not in complete or j.get("twin_of"):
        continue
    p = EX / f"{j['job_id']}.json"
    if not p.exists():
        continue
    pkt = json.loads(p.read_text(encoding="utf-8"))
    org = [r for r in pkt["rows"] if r["module_type"] == "organic"]
    cells.append({
        "job_id": j["job_id"], "subject": j["subject"], "shape": j["shape"],
        "stratum": j["stratum"], "category": j["category"],
        "maturity": j["subject_maturity"],
        "q_rows": len(A.qrows(pkt)), "paa_rows": len(A.paa_rows(pkt)),
        "organic": len(org),
        "aio": int(bool((pkt.get("ai_overview") or {}).get("present"))),
        "domains": sorted(A.domains(pkt)), "questions": A.qrows(pkt),
    })
print(f"analysis cells (complete subjects, non-twin): {len(cells)}")

by_subj = defaultdict(dict)
for c in cells:
    by_subj[c["subject"]][c["shape"]] = c


def unique_contribution(subjects, field, min_shapes=3):
    uniq, excl_n, cover, greedy = (defaultdict(list) for _ in range(4))
    for subj in subjects:
        sets = {s: set(c[field]) for s, c in by_subj[subj].items()}
        if len(sets) < min_shapes:
            continue
        union = set().union(*sets.values())
        for s, items in sets.items():
            others = set().union(*[v for k, v in sets.items() if k != s])
            ex = items - others
            uniq[s].append(len(ex) / len(items) if items else 0.0)
            excl_n[s].append(len(ex))
            cover[s].append(len(items) / len(union) if union else 0.0)
        remaining, pool, pos = set(union), dict(sets), 1
        while remaining and pool:
            best = max(pool, key=lambda k: len(pool[k] & remaining))
            if not (pool[best] & remaining):
                break
            greedy[best].append(pos)
            remaining -= pool[best]
            del pool[best]
            pos += 1
    return {s: {
        "mean_unique_share": round(sum(v) / len(v), 3),
        "mean_exclusive_items": round(sum(excl_n[s]) / len(excl_n[s]), 1),
        "mean_coverage_of_union": round(sum(cover[s]) / len(cover[s]), 3),
        "mean_greedy_pick_position": (round(sum(greedy[s]) / len(greedy[s]), 2)
                                      if greedy.get(s) else None),
        "picked_in_n_subjects": len(greedy.get(s, [])),
        "n_subjects": len(v),
    } for s, v in uniq.items()}


def saturation(subjects, field, min_shapes=3):
    need = {0.8: [], 0.95: []}
    for subj in subjects:
        sets = {s: set(c[field]) for s, c in by_subj[subj].items()}
        if len(sets) < min_shapes:
            continue
        union = set().union(*sets.values())
        if not union:
            continue
        got, pool, n = set(), dict(sets), 0
        hits = {}
        while pool:
            best = max(pool, key=lambda k: len(pool[k] - got))
            if not (pool[best] - got):
                break
            got |= pool[best]
            del pool[best]
            n += 1
            frac = len(got) / len(union)
            for t in (0.8, 0.95):
                if t not in hits and frac >= t:
                    hits[t] = n
        for t, v in hits.items():
            need[t].append(v)
    return {str(t): {"mean_shapes": round(sum(v) / len(v), 2) if v else None,
                     "n_subjects": len(v)} for t, v in need.items()}


strata = defaultdict(set)
for c in cells:
    strata[c["stratum"]].add(c["subject"])

results = {}
for label, subs in [("ALL_complete", set(by_subj))] + sorted(
        (k, v) for k, v in strata.items()):
    results[label] = {
        "n_subjects_with_ge3_shapes": sum(1 for s in subs if len(by_subj[s]) >= 3),
        "questions": unique_contribution(subs, "questions"),
        "domains": unique_contribution(subs, "domains"),
        "saturation_questions": saturation(subs, "questions"),
        "saturation_domains": saturation(subs, "domains"),
    }

for label in ["beauty_subject", "adjacent", "far", "beauty_issue",
              "nonbeauty_issue", "deep_set", "ALL_complete"]:
    r = results[label]
    print(f"\n{'='*72}\n=== {label}  (subjects with >=3 shapes: "
          f"{r['n_subjects_with_ge3_shapes']}) ===")
    for field in ("questions", "domains"):
        print(f"  --- {field} ---")
        print(f"  {'shape':<24}{'uniq':>7}{'excl':>7}{'cov':>7}{'greedy':>8}{'n':>5}")
        for s, v in sorted(r[field].items(), key=lambda kv: -kv[1]["mean_unique_share"]):
            gp = v["mean_greedy_pick_position"]
            print(f"  {s:<24}{v['mean_unique_share']:>7.3f}{v['mean_exclusive_items']:>7.1f}"
                  f"{v['mean_coverage_of_union']:>7.3f}"
                  f"{(f'{gp:.2f}' if gp else '-'):>8}{v['n_subjects']:>5}")
    print(f"  saturation questions: {r['saturation_questions']}")
    print(f"  saturation domains  : {r['saturation_domains']}")

(AN / "fullbank_shape_value.json").write_text(
    json.dumps({"coverage_bar": {
        "universe": "current 986-job query_bank",
        "subject_bar": "complete subjects only (every bank job ok)",
        "complete_subjects": len(complete), "total_subjects": len(by_subj_jobs),
        "cells": len(cells),
        "note": "unique_share is computed within-subject then averaged; it is "
                "depressed by a larger competing shape set, so strata with "
                "different shape-set sizes are not directly comparable.",
    }, "results": results}, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote analysis/fullbank_shape_value.json")

# shape-set size per stratum, for the comparability caveat
print("\nshape-set size per stratum (distinct shapes in bank):")
ss = defaultdict(set)
for j in bank:
    ss[j["stratum"]].add(j["shape"])
for k, v in sorted(ss.items()):
    print(f"  {k:<18} {len(v)} shapes, {len(strata.get(k, []))} complete subjects")
