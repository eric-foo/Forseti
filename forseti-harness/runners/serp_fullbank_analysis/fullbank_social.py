"""Full-bank social axis (F16-F19, F21), issue strata (F11), mediator
concentration (F12), contrarian anchors (F15).

Same coverage bar as the shape pass: current bank only, complete subjects only,
twins excluded from shape statistics (twins are used separately for F11
steadiness, which is what they exist for).
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
sys.path.insert(0, str(ROOT / "bin"))
import analyze_megadogfood as A

EX = ROOT / "extracted_v2"
AN = ROOT / "analysis"
BASE = ROOT / "analysis_panel_era_baseline"

PLATFORMS = {
    "tiktok": re.compile(r"tiktok", re.I),
    "instagram": re.compile(r"instagram", re.I),
    "youtube": re.compile(r"youtube|youtu\.be", re.I),
    "reddit": re.compile(r"reddit", re.I),
    "facebook": re.compile(r"facebook", re.I),
    "pinterest": re.compile(r"pinterest", re.I),
}
# displayed_source sometimes carries the platform NAME rather than an account;
# those are not creators and must not enter a recurrence table.
PLATFORM_PLACEHOLDER = {"youtube", "tiktok", "instagram", "facebook",
                        "pinterest", "reddit", "youtube shorts",
                        "tiktok  · ", "instagram  · "}


def platform_of(r):
    blob = " ".join(str(r.get(k) or "") for k in
                    ("platform", "displayed_source", "displayed_domain",
                     "canonical_url"))
    for name, rx in PLATFORMS.items():
        if rx.search(blob):
            return name
    return None


bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
ledger = {json.loads(l)["job_id"]: json.loads(l)
          for l in (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()}
by_subj_jobs = defaultdict(list)
for j in bank:
    by_subj_jobs[j["subject"]].append(j)
complete = {s for s, js in by_subj_jobs.items()
            if all((ledger.get(j["job_id"]) or {}).get("outcome") == "ok" for j in js)}
issue_subjects = {j["subject"] for j in bank if j["subject_maturity"] == "issue"}

CONTRARIAN = re.compile(
    r"\b(overrated|not worth|isn'?t worth|waste of money|stop using|"
    r"don'?t buy|do not buy|ruined|broke me out|breaking me out|hate|"
    r"disappointed|disappointing|scam|hype|overhyped|regret|worst|"
    r"returned it|threw (?:it )?away|never again|avoid)\b", re.I)

cells, aio_by_subject, contrarian_hits, community_cards = [], defaultdict(list), [], 0
domain_queries = defaultdict(set)          # domain -> {(subject, query)}
domain_subjects = defaultdict(set)         # domain -> {subject}
aio_label_queries = defaultdict(set)
aio_label_subjects = defaultdict(set)

for j in bank:
    if j["subject"] not in complete or j.get("twin_of"):
        continue
    p = EX / f"{j['job_id']}.json"
    if not p.exists():
        continue
    pkt = json.loads(p.read_text(encoding="utf-8"))
    cards = [r for r in pkt["rows"]
             if r["module_type"] not in ("people_also_ask", "related_search")]
    plat = Counter(platform_of(r) for r in cards)
    video = sum(1 for r in cards if r["module_type"] == "video_block")
    social = sum(v for k, v in plat.items() if k)
    creators = set()
    for r in cards:
        pl = platform_of(r)
        if pl not in ("tiktok", "instagram", "youtube"):
            continue
        nm = r.get("account_or_creator") or r.get("displayed_source")
        if not nm or nm.strip().lower() in PLATFORM_PLACEHOLDER:
            continue
        creators.add((pl, nm.strip()))
    cells.append({
        "job_id": j["job_id"], "subject": j["subject"],
        "shape": j["shape"].replace("deep_", ""), "raw_shape": j["shape"],
        "category": j["category"], "stratum": j["stratum"],
        "is_issue": j["subject"] in issue_subjects,
        "cards": len(cards), "video_rows": video,
        "tiktok": plat.get("tiktok", 0), "instagram": plat.get("instagram", 0),
        "youtube": plat.get("youtube", 0), "reddit": plat.get("reddit", 0),
        "social_total": social,
        "social_share": round(social / len(cards), 3) if cards else 0.0,
        "creators": sorted(f"{a}:{b}" for a, b in creators),
        "q_rows": len(A.qrows(pkt)),
    })

    # F12 mediator concentration
    for r in pkt["rows"]:
        if r["module_type"] != "organic":
            continue
        dom = (r.get("displayed_domain") or "").lower().strip()
        if dom:
            domain_queries[dom].add((j["subject"], j["query"]))
            domain_subjects[dom].add(j["subject"])
    aio = pkt.get("ai_overview") or {}
    if aio.get("present"):
        for lab in aio.get("cited_source_labels") or []:
            lab = re.sub(r"\s*\+\d+$", "", (lab or "").strip())
            if lab:
                aio_label_queries[lab].add((j["subject"], j["query"]))
                aio_label_subjects[lab].add(j["subject"])

    # F15 contrarian community anchors
    for r in pkt["rows"]:
        blob = ((r.get("displayed_source") or "") + (r.get("displayed_domain") or ""))
        if "reddit" not in blob.lower():
            continue
        community_cards += 1
        if CONTRARIAN.search(r.get("title") or ""):
            contrarian_hits.append({"subject": j["subject"], "query": j["query"],
                                    "title": r["title"]})

print(f"social cells: {len(cells)} (panel-era: 136)")


def shape_table(rows, label):
    agg, n = defaultdict(Counter), Counter()
    for c in rows:
        n[c["shape"]] += 1
        for k in ("video_rows", "tiktok", "instagram", "youtube", "reddit",
                  "social_total"):
            agg[c["shape"]][k] += c[k]
        agg[c["shape"]]["share_sum"] += c["social_share"] * 1000
    out = {}
    for s in agg:
        a, k = agg[s], n[s]
        out[s] = {m: round(a[m] / k, 2) for m in
                  ("video_rows", "tiktok", "instagram", "youtube", "reddit",
                   "social_total")}
        out[s]["mean_social_share"] = round(a["share_sum"] / k / 1000, 3)
        out[s]["n"] = k
    print(f"\n=== per-shape mean social yield ({label}) ===")
    print(f"{'shape':<18}{'n':>4}{'share':>8}{'video':>7}{'tt':>6}{'ig':>6}"
          f"{'yt':>6}{'reddit':>8}")
    for s, v in sorted(out.items(), key=lambda kv: -kv[1]["mean_social_share"]):
        print(f"{s:<18}{v['n']:>4}{v['mean_social_share']:>8.3f}{v['video_rows']:>7}"
              f"{v['tiktok']:>6}{v['instagram']:>6}{v['youtube']:>6}{v['reddit']:>8}")
    return out


all_tbl = shape_table(cells, "all categories, full bank")
beauty_tbl = shape_table([c for c in cells if c["category"] == "beauty"],
                         "beauty only, full bank")

# --- F16: question-rich vs social-poor, measured directly ---
print("\n=== F16 axis divergence: question yield vs social share (all cells) ===")
qy = defaultdict(list)
for c in cells:
    qy[c["shape"]].append((c["q_rows"], c["social_share"]))
print(f"{'shape':<18}{'n':>4}{'mean_q_rows':>13}{'mean_soc_share':>16}")
f16 = {}
for s, v in sorted(qy.items(), key=lambda kv: -sum(x[0] for x in kv[1]) / len(kv[1])):
    mq = sum(x[0] for x in v) / len(v)
    ms = sum(x[1] for x in v) / len(v)
    f16[s] = {"n": len(v), "mean_q_rows": round(mq, 2), "mean_social_share": round(ms, 3)}
    print(f"{s:<18}{len(v):>4}{mq:>13.2f}{ms:>16.3f}")

# --- F19 / F21: creator recurrence ---
by_creator = defaultdict(set)
for c in cells:
    for cr in c["creators"]:
        by_creator[cr].add(c["subject"])
recurring = {cr: sorted(s) for cr, s in by_creator.items() if len(s) >= 2}
print(f"\n=== F19: creators on 2+ subjects (placeholders excluded) ===")
print(f"distinct platform-attributed sources: {len(by_creator)}; recurring on 2+: {len(recurring)}")
for cr, subs in sorted(recurring.items(), key=lambda kv: -len(kv[1]))[:40]:
    print(f"  {len(subs):>2}x  {cr:<44} {', '.join(subs)[:64]}")

# F21 classification: products-only / issues-only / bridging
klass = Counter()
bridging = []
for cr, subs in recurring.items():
    kinds = {"issue" if s in issue_subjects else "product" for s in subs}
    k = ("bridging" if kinds == {"issue", "product"}
         else ("issues_only" if kinds == {"issue"} else "products_only"))
    klass[k] += 1
    if k == "bridging":
        bridging.append((cr, subs))
print(f"\n=== F21: recurring-creator classification (n={len(recurring)}) ===")
for k, v in klass.most_common():
    print(f"  {k:<16}{v:>4}")
print("  bridging (problem-space AND brand-space):")
for cr, subs in sorted(bridging, key=lambda kv: -len(kv[1]))[:25]:
    print(f"    {len(subs)}x {cr:<40} {', '.join(subs)[:60]}")

# --- F11: issue vs product, steadiness (twins) and richness ---
print("\n=== F11: issue-led vs brand-led ===")
twin_pairs = []
for j in bank:
    if not j.get("twin_of"):
        continue
    a, b = j["job_id"], j["twin_of"]
    if (ledger.get(a) or {}).get("outcome") != "ok" or (ledger.get(b) or {}).get("outcome") != "ok":
        continue
    pa, pb = EX / f"{a}.json", EX / f"{b}.json"
    if not (pa.exists() and pb.exists()):
        continue
    qa = set(A.qrows(json.loads(pa.read_text(encoding="utf-8"))))
    qb = set(A.qrows(json.loads(pb.read_text(encoding="utf-8"))))
    if not (qa or qb):
        continue
    ov = len(qa & qb) / len(qa | qb)
    twin_pairs.append({"job": a, "twin_of": b, "subject": j["subject"],
                       "shape": j["shape"],
                       "is_issue": j["subject"] in issue_subjects,
                       "jaccard": round(ov, 3)})
for kind in (True, False):
    v = [t["jaccard"] for t in twin_pairs if t["is_issue"] is kind]
    lab = "issue" if kind else "product"
    if v:
        print(f"  twin question overlap ({lab}): n={len(v)} mean={sum(v)/len(v):.3f} "
              f"min={min(v):.3f} max={max(v):.3f}")
iq = [c["q_rows"] for c in cells if c["is_issue"]]
pq = [c["q_rows"] for c in cells if not c["is_issue"]]
print(f"  mean question rows: issue n={len(iq)} {sum(iq)/len(iq):.2f}  |  "
      f"product n={len(pq)} {sum(pq)/len(pq):.2f}")
isoc = [c["social_share"] for c in cells if c["is_issue"]]
psoc = [c["social_share"] for c in cells if not c["is_issue"]]
print(f"  mean social share : issue {sum(isoc)/len(isoc):.3f}  |  "
      f"product {sum(psoc)/len(psoc):.3f}")

# --- F12: mediator concentration ---
print("\n=== F12: mediator concentration ===")
med_multi_subject = {d: sorted(s) for d, s in domain_subjects.items() if len(s) >= 2}
print(f"organic domains seen: {len(domain_subjects)}; on 2+ subjects: {len(med_multi_subject)}")
print("  top organic domains by distinct subjects:")
for d, s in sorted(med_multi_subject.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"    {len(s):>3} subjects  {d}")
aio_multi_q = {l: sorted(q) for l, q in aio_label_queries.items() if len(q) >= 2}
print(f"\n  AIO cited-source labels: {len(aio_label_queries)}; "
      f"on 2+ independent queries: {len(aio_multi_q)}")
print("  top AIO cited sources by distinct subjects:")
for l, s in sorted(aio_label_subjects.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"    {len(s):>3} subjects  {l}")

# --- F15: contrarian anchors ---
print(f"\n=== F15: contrarian-titled community anchors ===")
print(f"community (reddit) cards scanned: {community_cards}")
print(f"contrarian-titled: {len(contrarian_hits)} "
      f"({len(contrarian_hits)/community_cards*100:.2f}% of community cards)")
subs_with = {h["subject"] for h in contrarian_hits}
qs_with = {(h["subject"], h["query"]) for h in contrarian_hits}
n_probes = len(cells)
print(f"probes with >=1 contrarian community title: {len(qs_with)} / {n_probes} "
      f"({len(qs_with)/n_probes*100:.1f}%)")
print(f"subjects with >=1: {len(subs_with)} / {len(complete)}")
for h in contrarian_hits[:25]:
    print(f"    [{h['subject'][:26]:<27}] {h['title'][:78]}")

(AN / "fullbank_social_and_axes.json").write_text(json.dumps({
    "coverage_bar": "current bank, complete subjects only, twins excluded",
    "n_cells": len(cells), "per_shape_all": all_tbl,
    "per_shape_beauty": beauty_tbl, "f16_question_vs_social": f16,
    "recurring_creators": recurring, "f21_classification": dict(klass),
    "f21_bridging": {cr: subs for cr, subs in bridging},
    "twin_pairs": twin_pairs,
    "f12_domains_multi_subject": {d: s for d, s in
                                  sorted(med_multi_subject.items(),
                                         key=lambda kv: -len(kv[1]))},
    "f12_aio_labels_multi_subject": {l: sorted(s) for l, s in
                                     sorted(aio_label_subjects.items(),
                                            key=lambda kv: -len(kv[1]))
                                     if len(s) >= 2},
    "f15_contrarian": {"community_cards": community_cards,
                       "hits": contrarian_hits,
                       "probes_with_hit": len(qs_with), "probes": n_probes},
    "cells": cells,
}, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote analysis/fullbank_social_and_axes.json")
