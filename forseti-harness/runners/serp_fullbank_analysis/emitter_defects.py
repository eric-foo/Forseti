"""Observed frequency of the known emitter v0.2 defects at full-bank scale.

Reporting only. The emitter is NOT edited by this pass; each defect is counted
with auditable rules so the owner can size the fix.

Defect classes (from competitor_ledger_spec_v0.md "Known v0.2 items"):
  A  name+context compound that should collapse to its parent
  B1 CONTEXT_GENERIC is beauty-centric: use-context phrases it does not know
  B2 residual prose-fragment noise at presence rung
  C  comma/conjunction list artifacts (comma-list names the matcher mangles
     or misses entirely)
  D  self_variant entries pending the owner vocabulary call
  E  scout-mode subject cross-product bleed
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(r"C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\serp-lane-fullbank-analysis-d4b5a1")
sys.path.insert(0, str(REPO / "forseti-harness" / "runners"))
import serp_competitor_ledger_emitter as E

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
AN = ROOT / "analysis"
led = json.loads((AN / "fullbank_competitor_ledger.json").read_text(encoding="utf-8"))
base = json.loads((ROOT / "analysis_panel_era_baseline" / "competitor_ledger_v0.json")
                  .read_text(encoding="utf-8"))
entries = led["entries"]

print(f"PANEL-ERA ledger : probes={base['probes_scanned']} entries={len(base['entries'])} "
      f"candidates={sum(1 for e in base['entries'] if e['rung']=='candidate')} "
      f"mediators={len(base['mediators'])}")
print(f"FULL-BANK ledger : probes={led['probes_scanned']} entries={len(entries)} "
      f"candidates={sum(1 for e in entries if e['rung']=='candidate')} "
      f"mediators={len(led['mediators'])}")
bt = Counter(e["type"] for e in entries)
bb = Counter(e["type"] for e in base["entries"])
print(f"  by type  panel={dict(bb)}  full={dict(bt)}")

toks = E.sig_tokens

# ---- A: subsumed compounds ------------------------------------------------
by_subject = defaultdict(list)
for e in entries:
    by_subject[e["subject"]].append(e)
A_hits = []
for subj, es in by_subject.items():
    tsets = {e["name"]: toks(e["name"]) for e in es}
    for e in es:
        n = e["name"]
        for m, mt in tsets.items():
            if m != n and mt and mt < tsets[n]:
                A_hits.append({"subject": subj, "name": n, "parent": m,
                               "q": e["distinct_queries"], "type": e["type"]})
                break

# ---- B1: use-context phrases CONTEXT_GENERIC does not know ---------------
EXTRA_CONTEXT = {
    "irritated", "korean", "japanese", "french", "asian", "american",
    "skincare", "haircare", "makeup", "routine", "beginner", "textured",
    "curly", "straight", "fine", "thick", "aging", "wrinkles", "redness",
    "eczema", "psoriasis", "rosacea", "dandruff", "tattoo", "lips",
    "cheeks", "scalp", "nails", "lashes", "brows", "generic", "viral",
    "cheap", "cheaper", "expensive", "luxury", "premium", "affordable",
    "drugstore", "espresso", "coffee", "running", "mattress", "sleep",
    "pads", "wound", "healing", "sensitive", "combination",
}
GENERIC_VERDICT = {
    "real", "fake", "bad", "good", "nah", "yes", "no", "there", "here",
    "overhyped", "overrated", "hype", "worth", "splurge", "just", "best",
    "better", "worse", "same", "different", "original", "originals",
    "alternative", "legit", "scam", "true", "false", "honest", "actually",
    "still", "much", "more", "less", "one", "two", "both",
}
B1, B2 = [], []
for e in entries:
    t = toks(e["name"])
    if not t:
        continue
    if t <= (E.CONTEXT_GENERIC | E.GENERIC_PRODUCT | EXTRA_CONTEXT):
        B1.append(e)
    elif t <= (GENERIC_VERDICT | E.CONTEXT_GENERIC | E.GENERIC_PRODUCT | E.STOP):
        B2.append(e)

# ---- C: comma / conjunction artifacts ------------------------------------
C_hits = [e for e in entries if "," in e["name"]
          or re.match(r"^(better|worse|best)\b", e["name"], re.I)]

# invisible comma-lists: titles carrying a 3+ comma-separated name list that
# produced no entry at all
bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
ledger_rows = {json.loads(l)["job_id"]: json.loads(l) for l in
               (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()}
issue_subjects = {j["subject"] for j in bank if j["subject_maturity"] == "issue"}
COMMA_LIST = re.compile(
    r"[A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*){0,3}\s*,\s*"
    r"[A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*){0,3}\s*,")
comma_titles_total = comma_titles_no_entry = 0
comma_examples = []
scout_true, scout_probe_texts = {}, []
for row in ledger_rows.values():
    if row["outcome"] != "ok" or row.get("twin_of") or row["subject"] in issue_subjects:
        continue
    p = ROOT / "extracted_v2" / f"{row['job_id']}.json"
    if not p.exists():
        continue
    pkt = json.loads(p.read_text(encoding="utf-8"))
    texts = E.packet_texts(pkt)
    scout_probe_texts.append((row["subject"], row["query"], texts))
    bt_ = E.brand_tokens(row["subject"])
    for surface, text in texts:
        if not text or not COMMA_LIST.search(text):
            continue
        if not E.matches_subject(text, bt_):
            continue
        comma_titles_total += 1
        got = list(E.harvest([(surface, text)], row["subject"], row["query"]))
        if not got:
            comma_titles_no_entry += 1
            if len(comma_examples) < 12:
                comma_examples.append({"subject": row["subject"], "text": text[:120]})

# ---- D: self-variant candidates -------------------------------------------
# A self-variant is the SUBJECT'S OWN line surfacing as a rival. Two auditable
# signatures, kept separate so neither leans on a prose heuristic:
#   D1 the emitted name itself carries a subject brand token
#      ("Cerave Healing Ointment" on cerave moisturizing cream)
#   D2 every evidence text places the name immediately after a subject brand
#      token ("AeroPress Premium" -> name "Premium")
D_hits = []
for e in entries:
    nt = toks(e["name"])
    bt_ = E.brand_tokens(e["subject"])
    if nt & bt_:
        D_hits.append({**{k: e[k] for k in ("subject", "name", "type",
                                            "distinct_queries")},
                       "why": "D1 name carries a subject brand token"})
        continue
    # contiguous "<subject brand> <name>" somewhere in the evidence: that is
    # the self-variant signature ("AeroPress Premium"). A comparison split
    # ("quip vs Sonicare") never produces a contiguous brand+name string.
    nm = re.escape(e["name"].lower())
    adjacent = any(
        re.search(rf"\b{re.escape(tok)}\s+{nm}", (s.get("evidence") or "").lower())
        for s in e["sources"] for tok in bt_)
    if adjacent:
        D_hits.append({**{k: e[k] for k in ("subject", "name", "type",
                                            "distinct_queries")},
                       "why": "D2 evidence carries contiguous '<subject brand> <name>'"})

# ---- E: scout-mode subject cross-product bleed ----------------------------
# Faithful simulation: run the scout-mode cross product over the same probes,
# then count entries whose evidence came from a packet belonging to a DIFFERENT
# subject than the one they were attributed to.
subjects = sorted({s for s, _, _ in scout_probe_texts})
bound_keys, scout_keys, bled = set(), set(), Counter()
for true_subj, query, texts in scout_probe_texts:
    for item in E.harvest(texts, true_subj, query):
        if item[0] != "MEDIATOR":
            bound_keys.add((true_subj, item[0].lower(), item[1]))
for true_subj, query, texts in scout_probe_texts:
    for cand in subjects:
        for item in E.harvest(texts, cand, query):
            if item[0] == "MEDIATOR":
                continue
            scout_keys.add((cand, item[0].lower(), item[1]))
            if cand != true_subj:
                bled[cand] += 1
bleed_only = scout_keys - bound_keys

# ---- report ---------------------------------------------------------------
n = len(entries)
def pct(k):
    return f"{k} ({k/n*100:.1f}% of {n} entries)"

print("\n=== emitter v0.2 defect frequency at full-bank scale ===")
print(f"A  name+context compounds subsumed by a parent entry : {pct(len(A_hits))}")
for h in sorted(A_hits, key=lambda h: -h["q"])[:12]:
    print(f"     q={h['q']:<3} {h['subject'][:26]:<27} '{h['name']}'  ->  '{h['parent']}'")
print(f"B1 use-context phrases CONTEXT_GENERIC misses        : {pct(len(B1))}")
for e in sorted(B1, key=lambda e: -e["distinct_queries"])[:12]:
    print(f"     q={e['distinct_queries']:<3} {e['subject'][:26]:<27} '{e['name']}'")
print(f"B2 residual prose-fragment noise                     : {pct(len(B2))}")
for e in sorted(B2, key=lambda e: -e["distinct_queries"])[:12]:
    print(f"     q={e['distinct_queries']:<3} {e['subject'][:26]:<27} '{e['name']}'")
print(f"C  comma/conjunction artifacts in emitted names      : {pct(len(C_hits))}")
for e in sorted(C_hits, key=lambda e: -e["distinct_queries"])[:12]:
    print(f"     q={e['distinct_queries']:<3} {e['subject'][:26]:<27} '{e['name']}'")
print(f"   comma-list titles matching the subject           : {comma_titles_total}")
print(f"   of those, producing ZERO entries (invisible)     : {comma_titles_no_entry}"
      + (f" ({comma_titles_no_entry/comma_titles_total*100:.1f}%)"
         if comma_titles_total else ""))
for c in comma_examples[:8]:
    print(f"     [{c['subject'][:24]:<25}] {c['text']}")
print(f"D  self-variant candidates pending vocabulary call   : {pct(len(D_hits))}")
for h in sorted(D_hits, key=lambda h: -h["distinct_queries"])[:12]:
    print(f"     q={h['distinct_queries']:<3} {h['subject'][:26]:<27} '{h['name']}'  [{h['why']}]")
flagged = ({(h["subject"], h["name"]) for h in A_hits}
           | {(e["subject"], e["name"]) for e in B1 + B2 + C_hits}
           | {(h["subject"], h["name"]) for h in D_hits})
print(f"   distinct entries carrying >=1 defect flag        : {pct(len(flagged))}")
print(f"E  scout-mode subject bleed (cross-product simulation over the same "
      f"{len(scout_probe_texts)} probes x {len(subjects)} subjects):")
print(f"     ledger-bound distinct (subject,name,type) keys  : {len(bound_keys)}")
print(f"     scout-mode distinct keys                        : {len(scout_keys)}")
print(f"     keys that exist ONLY under scout mode (bleed)   : {len(bleed_only)} "
      f"({len(bleed_only)/max(len(scout_keys),1)*100:.1f}% of scout output)")

(AN / "fullbank_emitter_defects.json").write_text(json.dumps({
    "entries_total": n,
    "panel_era": {"probes": base["probes_scanned"], "entries": len(base["entries"])},
    "full_bank": {"probes": led["probes_scanned"], "entries": n},
    "A_subsumed_compounds": A_hits,
    "B1_context_leak": [{k: e[k] for k in ("subject", "name", "type", "distinct_queries")} for e in B1],
    "B2_prose_noise": [{k: e[k] for k in ("subject", "name", "type", "distinct_queries")} for e in B2],
    "C_comma_artifacts": [{k: e[k] for k in ("subject", "name", "type", "distinct_queries")} for e in C_hits],
    "C_invisible_comma_lists": {"titles_matching_subject": comma_titles_total,
                                "zero_entry": comma_titles_no_entry,
                                "examples": comma_examples},
    "D_self_variant": D_hits,
    "E_scout_bleed": {"probes": len(scout_probe_texts), "subjects": len(subjects),
                      "bound_keys": len(bound_keys), "scout_keys": len(scout_keys),
                      "bleed_only_keys": len(bleed_only)},
}, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote analysis/fullbank_emitter_defects.json")
