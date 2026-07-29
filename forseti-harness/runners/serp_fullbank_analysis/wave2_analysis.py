r"""Wave-2 analysis: complaint tournament, twin stability, platform doors.

Three questions, one pass over the durable store:

 1. TOURNAMENT -- rank the 6 new failure-intent shapes against the 3
    proven ones, within-subject on the complaint_ext subjects (every
    subject carries all 9, so each subject is its own controlled
    comparison).
 2. TWINS -- the lane's first SERP noise floor: 60 queries captured
    twice ~4.5h apart (A/B) plus their wave-1 original. Question overlap
    and domain overlap between captures of the SAME query bound how much
    of any cross-shape difference is just churn.
 3. PLATFORM SUFFIX -- do "{s} tiktok/youtube/instagram" behave like
    "{s} reddit" (platform door) or not.

Writes analysis/wave2_analysis.json. Store path operator-drive-pinned.
"""
import json
import sys
import collections
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
EX = ROOT / "extracted_v2"

bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
by_id = {j["job_id"]: j for j in bank}


def load(jid):
    p = EX / f"{jid}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if not d.get("rows"):
        return None
    return d


def questions(pkt):
    return {r["title"].strip().lower() for r in pkt["rows"]
            if r["module_type"] in ("people_also_ask", "related_search")
            and r.get("title")}


def domains(pkt):
    return {r["displayed_domain"].lower().removeprefix("www.")
            for r in pkt["rows"] if r.get("displayed_domain")}


def social_stats(pkt):
    rows = pkt["rows"]
    n = len(rows)
    plat = collections.Counter()
    social = 0
    for r in rows:
        d = (r.get("displayed_domain") or "").lower()
        hit = next((p for p in ("tiktok", "instagram", "youtube", "reddit")
                    if p in d), None)
        if hit:
            plat[hit] += 1
            social += 1
    return {"rows": n, "social_share": round(social / n, 3) if n else None,
            **{p: plat[p] for p in ("tiktok", "instagram", "youtube", "reddit")}}


# ---- 1. complaint tournament -------------------------------------------
TOURNAMENT = ["side_effects", "not_working", "complaints",           # proven
              "regret", "dont_buy", "bad_for_you", "why_stopped_working",
              "made_it_worse", "waste_of_money"]                     # new

subj_shape = collections.defaultdict(dict)   # subject -> shape -> jid
for j in bank:
    if j["shape"] in TOURNAMENT and not j.get("twin_leg"):
        subj_shape[j["subject"]][j["shape"]] = j["job_id"]

tour_subjects = [s for s, sh in subj_shape.items()
                 if all(t in sh for t in TOURNAMENT)]
uni = collections.defaultdict(list)          # shape -> per-subject unique share
for s in tour_subjects:
    qs = {}
    for t in TOURNAMENT:
        pkt = load(subj_shape[s][t])
        if pkt:
            qs[t] = questions(pkt)
    if len(qs) < len(TOURNAMENT):
        continue
    for t in TOURNAMENT:
        others = set().union(*(v for k, v in qs.items() if k != t))
        mine = qs[t]
        if mine:
            uni[t].append(len(mine - others) / len(mine))

tournament = {t: {"mean_unique_share": round(sum(v) / len(v), 3),
                  "n_subjects": len(v)}
              for t, v in uni.items()}

# ---- 2. twin stability --------------------------------------------------
pairs = collections.defaultdict(dict)        # twin_of -> leg -> jid
for j in bank:
    if j.get("twin_leg"):
        pairs[j["twin_of"]][j["twin_leg"]] = j["job_id"]


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else None


twin_rows = []
for orig, legs in pairs.items():
    if "A" not in legs or "B" not in legs:
        continue
    pa, pb, po = load(legs["A"]), load(legs["B"]), load(orig)
    if not (pa and pb):
        continue
    row = {"orig": orig, "shape": by_id[orig]["shape"],
           "subject": by_id[orig]["subject"],
           "q_jaccard_AB": jaccard(questions(pa), questions(pb)),
           "d_jaccard_AB": jaccard(domains(pa), domains(pb))}
    if po:
        row["q_jaccard_origA"] = jaccard(questions(po), questions(pa))
        row["d_jaccard_origA"] = jaccard(domains(po), domains(pa))
    twin_rows.append(row)


def agg(key):
    vals = [r[key] for r in twin_rows if r.get(key) is not None]
    vals.sort()
    return {"n": len(vals), "mean": round(sum(vals) / len(vals), 3),
            "median": round(vals[len(vals) // 2], 3),
            "p10": round(vals[len(vals) // 10], 3)} if vals else None


by_shape_q = collections.defaultdict(list)
for r in twin_rows:
    if r.get("q_jaccard_AB") is not None:
        by_shape_q[r["shape"]].append(r["q_jaccard_AB"])

# F13's revisit trigger: >=3 twin pairs per maturity class. The withdrawn
# cell claimed question-layer trust scales with entity maturity; with the
# classes now covered, this either revives it or refutes it positively
# instead of resting on one failed replication.
by_maturity = collections.defaultdict(list)
for r in twin_rows:
    if r.get("q_jaccard_AB") is None:
        continue
    by_maturity[by_id[r["orig"]].get("subject_maturity")].append(
        r["q_jaccard_AB"])
maturity_stability = {
    m: {"n": len(v), "median": round(sorted(v)[len(v) // 2], 3),
        "mean": round(sum(v) / len(v), 3)}
    for m, v in sorted(by_maturity.items()) if v}

twins = {
    "same_run_4p5h_apart": {"questions": agg("q_jaccard_AB"),
                            "domains": agg("d_jaccard_AB")},
    "f13_stability_by_maturity": maturity_stability,
    "cross_day_vs_original": {"questions": agg("q_jaccard_origA"),
                              "domains": agg("d_jaccard_origA")},
    "per_shape_q_jaccard_AB": {k: round(sum(v) / len(v), 3)
                               for k, v in sorted(by_shape_q.items())},
}

# ---- 3. platform suffixes ----------------------------------------------
SUFFIX = ["tiktok_suffix", "youtube_suffix", "instagram_suffix",
          "reddit_suffix"]
plat = collections.defaultdict(list)
for j in bank:
    if j["shape"] in SUFFIX and not j.get("twin_leg"):
        pkt = load(j["job_id"])
        if pkt:
            plat[j["shape"]].append(social_stats(pkt))


def platagg(rows):
    n = len(rows)
    out = {"n_probes": n}
    for k in ("social_share", "tiktok", "instagram", "youtube", "reddit"):
        vals = [r[k] for r in rows if r.get(k) is not None]
        out[k] = round(sum(vals) / len(vals), 2) if vals else None
    return out


platform = {s: platagg(rows) for s, rows in plat.items()}

out = {"tournament": tournament, "twins": twins, "platform_suffix": platform,
       "tournament_n_subjects": len(tour_subjects)}
(ROOT / "analysis" / "wave2_analysis.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"### TOURNAMENT (n={len(tour_subjects)} subjects, all 9 shapes)")
for t, v in sorted(tournament.items(), key=lambda kv: -kv[1]["mean_unique_share"]):
    tag = "proven" if t in ("side_effects", "not_working", "complaints") else "NEW"
    print(f"  {t:20s} {v['mean_unique_share']:.3f}  n={v['n_subjects']}  [{tag}]")
print("\n### TWINS")
print(json.dumps(twins["same_run_4p5h_apart"], indent=1))
print("cross-day:", json.dumps(twins["cross_day_vs_original"]))
print("per-shape A/B question jaccard:",
      json.dumps(twins["per_shape_q_jaccard_AB"]))
print("F13 stability by maturity:",
      json.dumps(twins["f13_stability_by_maturity"]))
print("\n### PLATFORM SUFFIX")
for s in SUFFIX:
    if s in platform:
        print(f"  {s:18s} {json.dumps(platform[s])}")
