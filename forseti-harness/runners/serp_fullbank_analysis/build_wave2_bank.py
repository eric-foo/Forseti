r"""Build wave-2 jobs and append them to query_bank.json.

Four streams, chosen against the open cells in serp_lane_v0.md:

  p11_fill        the 11-shape product design is n=12 and is now the BINDING
                  limit on F4/F5/F6/F17 -- capture coverage no longer is.
                  Filling gaps on subjects that already carry most of P11 is
                  the cheapest possible n gain.
  complaint_ext   F6 held at full coverage with not_working at 0.651 (#2
                  shape overall). Six new failure-intent shapes probe whether
                  the family has more depth than the three we have.
  platform_suffix `reddit_suffix` is the only platform-named shape ever run.
                  Whether it is a PLATFORM door or a REDDIT door is untested.
  twin            every number in the ledger rests on single captures and the
                  lane has never measured SERP volatility. Without a noise
                  floor, close rankings (0.782 vs 0.651) cannot be called
                  distinguishable.

Ordering is ROUND-ROBIN across streams, not clustered by stream. The
2026-07-28 halt landed subject-clustered and skewed the issue/product
balance, which is what made two of revision 1's judgments coverage
artifacts. Interleaving means a run that dies at 70% yields 70% of EVERY
stream instead of 100% of three and 0% of one.

Twin B jobs are forced into the back half so each pair is separated by
roughly two hours of run time.

vs_rival is filled ONLY where the competitor ledger supplies a
hand-adjudicated USABLE rival. F20 says rival inputs come from harvest,
not operator priors; a subject with no harvested rival keeps vs_rival as
a typed gap rather than getting a hand-picked one.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
BANK = ROOT / "query_bank.json"
ANALYSIS = ROOT / "analysis"

bank = json.loads(BANK.read_text(encoding="utf-8"))
existing_ids = {j["job_id"] for j in bank}
have = defaultdict(set)
meta = {}
for j in bank:
    have[j["subject"]].add(j["shape"])
    meta[j["subject"]] = (j["stratum"], j["category"], j.get("subject_maturity"))

P11 = ["alternatives", "complaints", "dupe", "honest_review", "not_working",
       "reddit_suffix", "review", "reviews_plural", "side_effects",
       "vs_rival", "worth_it"]

TEMPLATES = {
    "alternatives": "{s} alternatives",
    "complaints": "{s} complaints",
    "dupe": "{s} dupe",
    "honest_review": "{s} honest review",
    "not_working": "{s} not working",
    "reddit_suffix": "{s} reddit",
    "review": "{s} review",
    "reviews_plural": "{s} reviews",
    "side_effects": "{s} side effects",
    "worth_it": "is {s} worth it",
    # wave-2 platform doors
    "tiktok_suffix": "{s} tiktok",
    "youtube_suffix": "{s} youtube",
    "instagram_suffix": "{s} instagram",
    # wave-2 failure-intent family
    "regret": "regret buying {s}",
    "dont_buy": "don't buy {s}",
    "bad_for_you": "is {s} bad for you",
    "why_stopped_working": "why did {s} stop working",
    "made_it_worse": "{s} made it worse",
    "waste_of_money": "is {s} a waste of money",
}

COMPLAINT_EXT = ["regret", "dont_buy", "bad_for_you", "why_stopped_working",
                 "made_it_worse", "waste_of_money"]
PLATFORM = ["tiktok_suffix", "youtube_suffix", "instagram_suffix"]

# ---- harvested rivals (hand-adjudicated USABLE only) --------------------
rivals = {}
ledger = json.loads((ANALYSIS / "fullbank_competitor_ledger.json")
                    .read_text(encoding="utf-8"))
adj = json.loads((ANALYSIS / "fullbank_candidate_adjudication.json")
                 .read_text(encoding="utf-8"))
usable = {(v["subject"], v["name"]) for v in adj["verdicts"]
          if v["verdict"] == "USABLE"}
best = defaultdict(list)
for x in ledger["entries"]:
    key = (x["subject"], x["name"])
    if x.get("rung") == "candidate" and key in usable and x.get("type") == "rival":
        best[x["subject"]].append((len(x.get("sources", [])), x["name"]))
for s, cands in best.items():
    rivals[s] = sorted(cands, reverse=True)[0][1]

products = [s for s, (st, _c, _m) in meta.items()
            if st not in ("beauty_issue", "nonbeauty_issue")]
issues = [s for s, (st, _c, _m) in meta.items()
          if st in ("beauty_issue", "nonbeauty_issue")]

streams = defaultdict(list)


def emit(stream, subject, shape, query, **extra):
    st, cat, mat = meta[subject]
    streams[stream].append({
        "query": query, "stratum": st, "category": cat, "subject": subject,
        "subject_maturity": mat, "shape": shape, "deep_set": False,
        "wave": 2, "wave2_stream": stream, "twin_of": None, **extra})


# ---- stream 1: P11 fill -------------------------------------------------
no_rival = []
# Subjects captured only in the deep_ namespace carry none of P11 (11
# missing). Three strong beauty products and one far anchor are worth the
# full 11 each: they are already deeply covered on the other axis, so
# adding them to P11 buys a well-characterised subject, not a blank one.
DEEP_ONLY_WORTH_FILLING = ["cerave moisturizing cream",
                           "laneige lip sleeping mask",
                           "rhode peptide lip treatment",
                           "aeropress"]

for s in sorted(products):
    missing = [sh for sh in P11 if sh not in have[s]]
    if not missing:
        continue
    if len(missing) > 5 and s not in DEEP_ONLY_WORTH_FILLING:
        continue                      # deep-only namespace, not worth 11 probes
    for sh in missing:
        if sh == "vs_rival":
            if s not in rivals:
                no_rival.append(s)
                continue
            emit("p11_fill", s, "vs_rival", f"{s} vs {rivals[s]}",
                 rival_source="harvested_ledger_candidate_usable")
        else:
            emit("p11_fill", s, sh, TEMPLATES[sh].format(s=s))

# ---- stream 2: failure-intent expansion ---------------------------------
# Subjects that already carry the existing pain family, so the new shapes
# are comparable against side_effects / not_working / complaints.
pain_ready = [s for s in sorted(products)
              if {"side_effects", "not_working"} <= have[s]][:34]
for s in pain_ready:
    for sh in COMPLAINT_EXT:
        emit("complaint_ext", s, sh, TEMPLATES[sh].format(s=s))

# ---- stream 3: platform doors -------------------------------------------
# Beauty first (that is where reddit_suffix was measured), then adjacent/far
# so the answer is not beauty-only.
plat_subj = [s for s in sorted(products) if meta[s][1] == "beauty"]
plat_subj += [s for s in sorted(products) if meta[s][1] != "beauty"]
plat_subj += [s for s in sorted(issues) if meta[s][1] == "beauty"][:12]
plat_subj = plat_subj[:45]
for s in plat_subj:
    for sh in PLATFORM:
        emit("platform_suffix", s, sh, TEMPLATES[sh].format(s=s))

# ---- stream 4: twin stability -------------------------------------------
# 60 already-captured queries, re-run TWICE inside this run. Gives a
# same-run variance estimate (A vs B) and a cross-day one (vs the original).
TWIN_SHAPES = ["vs_rival", "not_working", "side_effects", "reddit_suffix",
               "alternatives", "dupe", "worth_it", "review", "bare",
               "what_causes", "how_to_fix", "best_products"]
# Dedupe by query: a few queries exist under two job_ids (deep_set and the
# normal set carry the same string). Twinning both would give that query 4
# captures and silently over-weight it in any variance estimate keyed on
# query text.
pool, seen_q = [], set()
for j in bank:
    if j["shape"] in TWIN_SHAPES and j["query"] not in seen_q:
        seen_q.add(j["query"])
        pool.append(j)
pool.sort(key=lambda j: (j["shape"], j["subject"]))
by_shape = defaultdict(list)
for j in pool:
    by_shape[j["shape"]].append(j)
twin_src = []
i = 0
while len(twin_src) < 60:
    added = False
    for sh in TWIN_SHAPES:
        if i < len(by_shape[sh]) and len(twin_src) < 60:
            twin_src.append(by_shape[sh][i])
            added = True
    if not added:
        break
    i += 1
for j in twin_src:
    for leg in ("A", "B"):
        streams[f"twin_{leg}"].append({
            **{k: v for k, v in j.items() if k != "job_id"},
            "wave": 2, "wave2_stream": "twin", "twin_leg": leg,
            "twin_of": j["job_id"]})

# ---- interleave ---------------------------------------------------------
order = ["p11_fill", "complaint_ext", "platform_suffix", "twin_A"]
front, back = [], []
lists = {k: list(v) for k, v in streams.items()}
while any(lists[k] for k in order):
    for k in order:
        if lists[k]:
            front.append(lists[k].pop(0))
# twin_B goes in the back half, interleaved with the tail of everything else
back = lists["twin_B"]
half = len(front) // 2
merged = front[:half]
tail = front[half:]
step = max(1, len(tail) // max(1, len(back)))
bi = 0
for n, job in enumerate(tail):
    merged.append(job)
    if bi < len(back) and n % step == 0:
        merged.append(back[bi])
        bi += 1
merged.extend(back[bi:])

# ---- assign ids and append ----------------------------------------------
nid = 2000
for job in merged:
    while f"j{nid}" in existing_ids:
        nid += 1
    job["job_id"] = f"j{nid}"
    existing_ids.add(job["job_id"])
    nid += 1

BACKUP = ROOT / "query_bank_pre_wave2.json"
if not BACKUP.exists():
    BACKUP.write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
BANK.write_text(json.dumps(bank + merged, ensure_ascii=False), encoding="utf-8")

print(f"wave-2 jobs: {len(merged)}  (bank {len(bank)} -> {len(bank) + len(merged)})")
counts = defaultdict(int)
for j in merged:
    counts[j["wave2_stream"]] += 1
for k, v in sorted(counts.items()):
    print(f"  {k:18s} {v}")
print(f"\nestimated runtime at 60/hr: {len(merged)/60:.1f} h")
print(f"vs_rival skipped for lack of a harvested rival: {len(set(no_rival))} subjects")
print(f"  {sorted(set(no_rival))}")
