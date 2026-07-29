"""Fixed-design shape value: panel vs full bank, same competing shape set.

unique_share is mechanically depressed by a larger competing shape set, so the
only honest panel-vs-fullbank comparison holds the shape set FIXED. The panel's
own cells (panel_shape_analysis.json, stratum=="panel") are re-scored under the
same restricted designs, so both sides of every number come from one method.

Designs, read off the panel's actual composition:
  P11  the 11-shape product board (panel: 3 subjects; laneige lacks `dupe`)
  P10  P11 minus `dupe`            (panel: 4 subjects — the widest product set
                                    the panel supports)
  P9   the 9 product shapes shared by beauty_subject + adjacent + far
  I8   the 8-shape beauty-issue design (panel: 1 subject at 8; 1 at 7)
  I7   I8 minus `why`              (panel: 2 subjects)
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
sys.path.insert(0, str(ROOT / "bin"))
import analyze_megadogfood as A

EX = ROOT / "extracted_v2"
AN = ROOT / "analysis"
BASE = ROOT / "analysis_panel_era_baseline"

P11 = ["alternatives", "complaints", "dupe", "honest_review", "not_working",
       "reddit_suffix", "review", "reviews_plural", "side_effects",
       "vs_rival", "worth_it"]
P10 = [s for s in P11 if s != "dupe"]
P9 = [s for s in P11 if s not in ("dupe", "vs_rival")]
I8 = ["bare", "before_after", "best_products", "how_to_fix", "normal",
      "reddit_suffix", "what_causes", "why"]
I7 = [s for s in I8 if s != "why"]
D14 = ["deep_does_work", "deep_how_to_use", "deep_ingredients_specs",
       "deep_is_good", "deep_mistakes", "deep_overrated", "deep_problems",
       "deep_pros_cons", "deep_results", "deep_review_year",
       "deep_sensitive_ctx", "deep_should_buy", "deep_stopped_using",
       "deep_vs_cheaper"]
DESIGNS = {"P11": P11, "P10": P10, "P9": P9, "I8": I8, "I7": I7, "D14": D14}

# ---------- full-bank cells (complete subjects only, non-twin) ----------
bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
ledger = {json.loads(l)["job_id"]: json.loads(l)
          for l in (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()}
by_subj_jobs = defaultdict(list)
for j in bank:
    by_subj_jobs[j["subject"]].append(j)
complete = {s for s, js in by_subj_jobs.items()
            if all((ledger.get(j["job_id"]) or {}).get("outcome") == "ok" for j in js)}

full = defaultdict(dict)   # subject -> shape -> {domains, questions}
for j in bank:
    if j["subject"] not in complete or j.get("twin_of"):
        continue
    p = EX / f"{j['job_id']}.json"
    if not p.exists():
        continue
    pkt = json.loads(p.read_text(encoding="utf-8"))
    full[j["subject"]][j["shape"]] = {"domains": sorted(A.domains(pkt)),
                                      "questions": A.qrows(pkt)}

# ---------- panel cells ----------
pcells = [c for c in json.loads((BASE / "panel_shape_analysis.json")
                                .read_text(encoding="utf-8"))["cells"]
          if c["stratum"] == "panel"]
panel = defaultdict(dict)
for c in pcells:
    panel[c["subject"]][c["shape"]] = {"domains": c["domains"],
                                       "questions": c["questions"]}


def score(store, shapes, field):
    """Unique-share etc. restricted to `shapes`; subjects must have ALL of them."""
    uniq, excl, cov, greedy = (defaultdict(list) for _ in range(4))
    subs = [s for s, d in store.items() if all(sh in d for sh in shapes)]
    for s in subs:
        sets = {sh: set(store[s][sh][field]) for sh in shapes}
        union = set().union(*sets.values())
        for sh, items in sets.items():
            others = set().union(*[v for k, v in sets.items() if k != sh])
            e = items - others
            uniq[sh].append(len(e) / len(items) if items else 0.0)
            excl[sh].append(len(e))
            cov[sh].append(len(items) / len(union) if union else 0.0)
        rem, pool, pos = set(union), dict(sets), 1
        while rem and pool:
            best = max(pool, key=lambda k: len(pool[k] & rem))
            if not (pool[best] & rem):
                break
            greedy[best].append(pos)
            rem -= pool[best]
            del pool[best]
            pos += 1
    tbl = {sh: {"uniq": round(sum(v) / len(v), 3),
                "excl": round(sum(excl[sh]) / len(excl[sh]), 1),
                "cov": round(sum(cov[sh]) / len(cov[sh]), 3),
                "greedy": (round(sum(greedy[sh]) / len(greedy[sh]), 2)
                           if greedy.get(sh) else None)}
           for sh, v in uniq.items()}
    return tbl, subs


def sat(store, shapes, field):
    out = {0.8: [], 0.95: []}
    subs = [s for s, d in store.items() if all(sh in d for sh in shapes)]
    for s in subs:
        sets = {sh: set(store[s][sh][field]) for sh in shapes}
        union = set().union(*sets.values())
        if not union:
            continue
        got, pool, n, hits = set(), dict(sets), 0, {}
        while pool:
            best = max(pool, key=lambda k: len(pool[k] - got))
            if not (pool[best] - got):
                break
            got |= pool[best]
            del pool[best]
            n += 1
            f = len(got) / len(union)
            for t in (0.8, 0.95):
                if t not in hits and f >= t:
                    hits[t] = n
        for t, v in hits.items():
            out[t].append(v)
    return {str(t): (round(sum(v) / len(v), 2) if v else None) for t, v in out.items()}, len(subs)


report = {}
for dname, shapes in DESIGNS.items():
    entry = {"shapes": shapes}
    for field in ("questions", "domains"):
        ft, fsubs = score(full, shapes, field)
        pt, psubs = score(panel, shapes, field)
        entry[field] = {"fullbank": ft, "fullbank_n": len(fsubs),
                        "fullbank_subjects": sorted(fsubs),
                        "panel": pt, "panel_n": len(psubs),
                        "panel_subjects": sorted(psubs)}
        fs, fn = sat(full, shapes, field)
        ps, pn = sat(panel, shapes, field)
        entry[f"saturation_{field}"] = {"fullbank": fs, "fullbank_n": fn,
                                        "panel": ps, "panel_n": pn}
    report[dname] = entry

    print(f"\n{'='*84}\n### DESIGN {dname} ({len(shapes)} shapes)")
    for field in ("questions", "domains"):
        e = entry[field]
        print(f"  --- {field}: panel n={e['panel_n']}  ->  full-bank n={e['fullbank_n']} ---")
        print(f"  {'shape':<18}{'panel_uq':>10}{'full_uq':>9}{'delta':>8}"
              f"{'p_excl':>8}{'f_excl':>8}{'p_grdy':>8}{'f_grdy':>8}")
        def cell(v, fmt):
            return format(v, fmt) if v is not None else "-"

        for sh in sorted(shapes, key=lambda s: -(e["fullbank"].get(s, {}).get("uniq", 0))):
            f = e["fullbank"].get(sh)
            p = e["panel"].get(sh)
            if not f:
                continue
            pu = p["uniq"] if p else None
            dl = (f["uniq"] - pu) if pu is not None else None
            print(f"  {sh:<18}{cell(pu, '.3f'):>10}{f['uniq']:>9.3f}"
                  f"{cell(dl, '+.3f'):>8}"
                  f"{cell(p['excl'] if p else None, '.1f'):>8}{f['excl']:>8.1f}"
                  f"{cell(p['greedy'] if p else None, '.2f'):>8}"
                  f"{cell(f['greedy'], '.2f'):>8}")
        s = entry[f"saturation_{field}"]
        print(f"  saturation: panel(n={s['panel_n']}) {s['panel']}   "
              f"full(n={s['fullbank_n']}) {s['fullbank']}")

(AN / "fullbank_fixed_design.json").write_text(
    json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote analysis/fullbank_fixed_design.json")
