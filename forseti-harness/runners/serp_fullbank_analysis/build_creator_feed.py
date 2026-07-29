"""Build the SERP-recurrence creator feed in the ratified grid_capture shape.

The spec (competitor_ledger_spec_v0.md, owner-ratified 2026-07-29) says a
mediator-list entry meeting a deep-dive trigger carries a `grid_capture`
tag with profile URL at emission, and the existing social capture runners'
input queue consumes tagged entries. Its first trigger -- "creator recurs
on 2+ subjects" -- is CROSS-SUBJECT, so it cannot fire inside a
single-subject phase-1 pass; this lane-level derivation is where it does
fire, and therefore where the tag is emitted.

Phase 1 itself never visits a platform and never weights a raw social
count. This file emits targets and locators only.
"""
import json
import sys
import collections
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
OUT = Path(r"C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees"
           r"\ulta-powerreviews-adapter-9c4df6\docs\research"
           r"\serp_lane_competitor_scout_20260728"
           r"\serp_recurring_creator_feed_v0.json")

sa = json.loads((RUN / "analysis" / "fullbank_social_and_axes.json")
                .read_text(encoding="utf-8"))
handles = json.loads((RUN / "analysis" / "creator_handles_tiktok.json")
                     .read_text(encoding="utf-8"))
bank = json.loads((RUN / "query_bank.json").read_text(encoding="utf-8"))
maturity = {}
for j in bank:
    maturity[j["subject"]] = j.get("subject_maturity")

rows = []
for key, subjects in sa["recurring_creators"].items():
    plat, name = key.split(":", 1)
    scopes = {("issue" if maturity.get(s) == "issue" else "product")
              for s in subjects}
    scope = "bridging" if len(scopes) == 2 else scopes.pop()
    hs = handles.get(name, []) if plat == "tiktok" else []
    profile = f"https://www.tiktok.com/@{hs[0]}" if hs else None
    rows.append({
        "platform": plat,
        "display_name": name,
        "grid_capture": True,          # trigger met: recurs on 2+ subjects
        "trigger": "recurs_on_2plus_subjects",
        "profile_url_or_none": profile,
        "locator_status": ("derived_from_card_url" if profile
                           else "unavailable_at_emission"),
        "tiktok_handles": hs,
        "n_subjects": len(subjects),
        "subjects": sorted(subjects),
        "scope": scope,
    })
rows.sort(key=lambda r: (-r["n_subjects"], r["platform"], r["display_name"]))

feed = {
    "artifact": "serp_recurring_creator_feed_v0",
    "generated": "2026-07-29",
    "source": "google_serp_us_parameterized megadogfood corpus "
              "(986-job wave-1 complete; counts refresh when the corpus grows)",
    "derivation": "forseti-harness/runners/serp_fullbank_analysis/"
                  "fullbank_social.py -> recurring_creators; handles from "
                  "video_block canonical_urls",
    "shape": "grid_capture tags per competitor_ledger_spec_v0.md "
             "(owner-ratified 2026-07-29); consumed by the existing social "
             "capture runners' input queue",
    "why_these": "each creator's account surfaced on Google SERPs for 2+ "
                 "DISTINCT subjects in the corpus (video/social result "
                 "cards) - the spec's first deep-dive trigger. The other "
                 "three triggers (row carries a statement a read would "
                 "weight; row is an axis/answer-slot's only occupant; "
                 "#ad-convergence needs checking) are read-time judgments "
                 "and are added by a reader, not here",
    "non_claims": [
        "recurrence evidences SERP reach, not audience size, independence, "
        "or sponsorship status",
        "counts are observed result cards, never prevalence or share of "
        "anything real",
        "this feed is capture-queue INPUT: nothing here is "
        "registry-admitted, qualified, or an owner disposition",
        "phase 1 never visits a platform and never weights a raw social "
        "count; any engagement read is weighted ONLY against the creator's "
        "own recent-grid median and is UNBASELINED otherwise (spec, "
        "owner-ratified 2026-07-29) - no cross-creator or cross-platform "
        "engagement comparison is licensed by this feed",
        "profile_url_or_none is derived from an observed card URL where "
        "one existed; unavailable is recorded, never guessed",
    ],
    "consumers": {
        "tiktok": "discovery-frontier ranking / supervised onboarding lane "
                  "(admission path exists)",
        "youtube": "NO admission path exists (typed gap); metric-rollup "
                   "machinery exists",
        "instagram": "NO admission path exists (typed gap)",
    },
    "n_creators": len(rows),
    "creators": rows,
}
OUT.write_text(json.dumps(feed, ensure_ascii=False, indent=1),
               encoding="utf-8")
c = collections.Counter(r["platform"] for r in rows)
h = sum(1 for r in rows if r["tiktok_handles"])
print(f"wrote {OUT.name}: {len(rows)} creators {dict(c)}; "
      f"tiktok with handle: {h}/{c['tiktok']}")
