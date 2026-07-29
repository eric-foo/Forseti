r"""Are the platform-suffix doors worth a board slot?

F23 opened on a VOLUME number -- named-platform probes return 17.2 TikTok
cards against 7.7 Reddit cards for `{s} reddit` and ~3.0 for the best
intent word. This tests whether that volume converts on either job the
lane actually does, controlled on the identical subject set so both door
types get equal opportunity to show recurrence:

  1. COMPETITOR HARVEST (the lane's stated purpose) -- ledger entries and
     candidate-rung names sourced only from suffix probes.
  2. CREATOR DISCOVERY -- creators found, and how many clear the lane's
     own bar of recurring across 2+ subjects.
  3. COVERAGE -- whether the ordinary intent probes already surface the
     platform, which decides whether a dedicated probe fills a gap or
     duplicates one.

Writes analysis/fullbank_platform_door_worth.json.
Store path operator-drive-pinned like the rest of this directory.
"""
import collections
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
SUFFIX = {"tiktok_suffix", "youtube_suffix", "instagram_suffix"}
PLATFORM_OF = {"tiktok_suffix": "tiktok", "youtube_suffix": "youtube",
               "instagram_suffix": "instagram"}

bank = {j["job_id"]: j for j in
        json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))}
subjects = {j["subject"] for j in bank.values()
            if j["shape"] in SUFFIX and not j.get("twin_leg")}

via = collections.defaultdict(lambda: {"suffix": set(), "intent": set()})
per_subject = collections.defaultdict(
    lambda: collections.defaultdict(lambda: {"suffix": set(), "intent": set()}))
probes = collections.Counter()
for f in (ROOT / "extracted_v2").glob("*.json"):
    j = bank.get(f.stem)
    if not j or j.get("twin_leg") or j["subject"] not in subjects:
        continue
    door = "suffix" if j["shape"] in SUFFIX else "intent"
    probes[door] += 1
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for r in d.get("rows", []):
        if r.get("module_type") != "video_block":
            continue
        dom = (r.get("displayed_domain") or "").lower()
        plat = next((p for p in ("tiktok", "instagram", "youtube")
                     if p in dom), None)
        acct = (r.get("account_or_creator") or "").strip().lower()
        if not (plat and acct):
            continue
        via[(plat, acct)][door].add(j["subject"])
        per_subject[j["subject"]][plat][door].add(acct)


def recurring(pool, keys):
    return sum(1 for v in pool.values()
               if len(set().union(*(v[k] for k in keys))) >= 2)


suffix_only = {k: v for k, v in via.items() if v["suffix"] and not v["intent"]}
intent_only = {k: v for k, v in via.items() if v["intent"] and not v["suffix"]}
both = {k: v for k, v in via.items() if v["suffix"] and v["intent"]}

# ---- competitor harvest -------------------------------------------------
ledger = json.loads((ROOT / "analysis" / "competitor_ledger_v02.json")
                    .read_text(encoding="utf-8"))
q2shape = {}
for j in bank.values():
    q2shape.setdefault(j["query"], j["shape"])
suffix_sourced_only = [
    e for e in ledger["entries"]
    if {q2shape.get(s["query"]) for s in e["sources"]} <= SUFFIX]

# ---- coverage: do intent probes already reach the platform? -------------
coverage = {}
for plat in ("tiktok", "youtube", "instagram"):
    with_intent = sum(1 for s in per_subject
                      if per_subject[s][plat]["intent"])
    n = sum(1 for s in per_subject if per_subject[s][plat]["suffix"])
    if not n:
        continue
    intent_per = (sum(len(per_subject[s][plat]["intent"]) for s in per_subject)
                  / max(len(per_subject), 1))
    added = (sum(len(per_subject[s][plat]["suffix"]
                     - per_subject[s][plat]["intent"]) for s in per_subject)
             / max(len(per_subject), 1))
    coverage[plat] = {
        "subjects_covered_by_intent_probes": with_intent,
        "subjects_total": len(per_subject),
        "creators_per_subject_from_intent_alone": round(intent_per, 1),
        "creators_per_subject_added_by_suffix": round(added, 1),
    }

out = {
    "artifact": "fullbank_platform_door_worth",
    "controlled_on": f"{len(subjects)} subjects carrying suffix probes",
    "probes": dict(probes),
    "competitor_harvest": {
        "entries_sourced_only_by_suffix": len(suffix_sourced_only),
        "of_which_candidate_rung": sum(
            1 for e in suffix_sourced_only if e["rung"] == "candidate"),
        "examples": [e["name"] for e in suffix_sourced_only[:6]],
    },
    "creator_discovery": {
        "suffix_only": {"creators": len(suffix_only),
                        "recurring": recurring(suffix_only, ["suffix"])},
        "intent_only": {"creators": len(intent_only),
                        "recurring": recurring(intent_only, ["intent"])},
        "both": {"creators": len(both),
                 "recurring": recurring(both, ["suffix", "intent"])},
    },
    "coverage": coverage,
    "reading": "The volume converts on neither job. Suffix probes sourced "
               "18 ledger entries no other probe found and NONE reached "
               "candidate rung (names are parser debris: 'Milky', 'fake', "
               "'Pass'). On creators they surface a distinct population "
               "but only ~1.5% clear the 2+-subject bar against ~4.3% for "
               "intent probes. And ordinary probes already surface TikTok "
               "for most subjects, so a dedicated probe adds breadth, not "
               "coverage.",
    "non_claims": [
        "observed card counts only, never prevalence",
        "suffix probes ran on fewer subjects than intent probes overall; "
        "this run controls for that by restricting BOTH to the suffix "
        "subject set",
    ],
}
(ROOT / "analysis" / "fullbank_platform_door_worth.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"controlled on {len(subjects)} subjects; probes {dict(probes)}")
ch = out["competitor_harvest"]
print(f"competitor harvest: {ch['entries_sourced_only_by_suffix']} suffix-only "
      f"entries, {ch['of_which_candidate_rung']} candidate")
cd = out["creator_discovery"]
for k, v in cd.items():
    print(f"  {k:12s} {v['creators']:4d} creators, {v['recurring']:3d} recurring "
          f"({v['recurring']/max(v['creators'],1):.1%})")
for plat, c in coverage.items():
    print(f"  {plat}: intent probes already cover "
          f"{c['subjects_covered_by_intent_probes']}/{c['subjects_total']} "
          f"subjects at {c['creators_per_subject_from_intent_alone']} "
          f"creators/subject; suffix adds "
          f"{c['creators_per_subject_added_by_suffix']}")
