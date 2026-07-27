# Summer Fridays phase-2 native return — findings v0 (2026-07-28)

Durable record of the completed Summer Fridays (SF) phase-2 native-return
execution, promoted from operator staging into the repo. This is the
second application of the two-phase shape (`competitor_ledger_spec_v0.md`):
phase 1 is the SERP scout pass (typed ledger, trigger-thread queue); phase 2
is the existing Reddit lane consuming that queue — native thread capture,
Channel-3 complaint-borne names, and per-surface J3 tagging (rendered
snippet stance vs top-voted native stance). Companion trial: see
`tower28_scout_trial_findings_v0.md` for the first (Tower 28) application.

SF's phase 1 was retroactive, not fresh: SF predates the competitor-ledger
spec, so the typed ledger was seeded by a **Channel-0** pass over the two
existing SF SERP row stores (`bin\channel0_harvest.py` ->
`channel0_hits_v0.json`, 92 rows) rather than new Google captures, and the
trigger-thread queue was the owner-authored
`forseti-sf-serp-pass1v1-dogfood-20260727\analysis\reddit_capture_queue_v0.md`
(13 threads, read externally to verify the queue's true size — not itself
part of this folder's inventory).

Standing non-claims carried throughout: counts of observed cards/comments
only, never prevalence/volume/share; US-parameterized is not physically
US-local; raw capture data stays outside Git, on the operator drive.

## Folder inventory (`C:\tmp\forseti-sf-phase2-native-return-20260728\`)

- **Root markdown:** `phase2_native_return_findings_v0.md` (the phase's own
  findings note), `j3_settlement_v0.md` (the J3 rendered-vs-actual table).
- **Root JSON:** `batch_summary.json` (9-capture Reddit batch run record),
  `channel0_hits_v0.json` (92-row Channel-0 harvest), `thread_composition_v0.json`
  (per-thread comment counts, keyword pos/neg, substitute mentions with vote
  scores and quotes for the 9 batch threads q02-q10),
  `competitor_ledger_phase2_consolidated_v0.json` (the typed ledger),
  `url_list_v0.json` (the 9 batch URLs) and `url_list_ret01.json` (the 1
  return-leg URL).
- **`bin\`** (5 scripts): `channel0_harvest.py` (Channel-0 emitter),
  `pilot_eligibility.py` (unrelated megadogfood calibration scan — not
  SF-specific), `probe_vs_oh.py` (one-shot return-leg dispatcher for the
  Ole Henriksen probe), `read_ret01_thread.py` and `thread_composition.py`
  (composition readers).
- **`extracted\sf-ret-01.json`**: parsed Google SERP rows for the executed
  return-leg probe.
- **`packets\sf-ret-01\`**: CloakBrowser snapshot packet (manifest, receipt,
  4 raw files: rendered DOM, visible text, viewport screenshot, snapshot
  metadata) for the Google SERP `summer fridays vs ole henriksen lip
  treatment`.
- **`q02_allergy_packet\` through `q10_review_finally_packet\`** (9 packet
  folders, old-Reddit HTTP capture: manifest, receipt, raw HTTP body +
  metadata each).
- **`return_leg\`**: `batch_summary.json` (1-capture run record),
  `r01_composition.json` (the r01 thread's 21 comments by vote), and
  `r01_vs_ole_henriksen_packet\` (manifest, receipt, raw HTTP body +
  metadata).
- The anchor thread (queue item #1, `r/Sephora/19eo5it`) is **not** in this
  folder — it was captured 2026-07-27 into a separate folder,
  `forseti-sf-reddit-anchor-20260727\`, and is referenced, not duplicated,
  here.

## What was captured

**9/9 located batch threads** captured via the Reddit lane
(`reddit_old_http_batch`, fixed 20s cadence, raw retention): `capture_success_count: 9`,
`content_extraction_failure_count: 0`, `access_diagnostic_failure_count: 0`
(`batch_summary.json`). Plus the anchor (captured 2026-07-27, external
folder) and **1 return-leg capture** (`return_leg\batch_summary.json`,
`capture_success_count: 1`) executed 2026-07-28 via CloakBrowser (Google
SERP, `packets\sf-ret-01\`) and old-Reddit HTTP (the r01 thread,
`return_leg\r01_vs_ole_henriksen_packet\`). **0 blocks across all
captures.**

**Queue accounting (correcting the audit's "13-thread queue consumed"):**
the owner-authored queue in `forseti-sf-serp-pass1v1-dogfood-20260727\
analysis\reddit_capture_queue_v0.md` lists exactly 13 items. Of those:
- **10 were captured**: item 1 (anchor, captured 2026-07-27, external
  folder) + items 2-10 (this folder's 9 batch packets, q02-q10).
- **3 were NOT captured** — items 11, 12, and 13 are marked in the source
  queue as unlocatable without a fresh Google search (item 11: "Worth-it
  thread... canonical URL not source-visible in packet; locate by title";
  items 12-13: `owner_observed`, no URL). `phase2_native_return_findings_v0.md`
  itself says "Queue #11-13 are unlocatable... deferred behind the
  full-bank run, probes authored below."
- Of those 3, **only #12 and #13 have an authored locator probe** in the
  return-leg table below (probes 9 and 10: `is summer fridays worth the
  splurge reddit` locates #13; `summer fridays not an influencer reddit`
  locates #12). **Queue item #11 has no authored locator probe** in this
  folder — an apparent gap, reported here rather than silently closed.

So the queue was **not fully consumed**: 10/13 items captured, 3/13
deferred, and one of those three (#11) currently has no return path
authored at all. `serp_lane_v0.md`'s in-progress line ("the SF
reddit_capture_queue_v0 (13 threads) is now consumed") overstates this —
it is optimistic phrasing written before this fuller check; the files show
10/13 captured, not 13/13.

## J3 — rendered-vs-actual settlement

**The audit's claim ("J3 settled n=10, 2 RENDERED_BETTER / 6 ALIGNED / 2
NATIVE_BETTER") is CORRECT for the 10-thread batch (rows 01-10 of
`j3_settlement_v0.md`) but is now STALE.** The file's true, current
headline — after the return-leg capture (row r01) was folded in on
2026-07-28 — is:

> **Headline (n=11): 2 RENDERED_BETTER / 7 ALIGNED / 2 NATIVE_BETTER.**

Per-thread tags (from `j3_settlement_v0.md`):

| q | thread | class | tag |
|---|---|---|---|
| 01 | anchor `19eo5it` | contrarian | ALIGNED |
| 02 | `166j6zu` allergy | claim-attack | RENDERED_BETTER |
| 03 | `1pf427h` reaction | claim-attack | RENDERED_BETTER |
| 04 | `1nv3pda` Amazon legit | trust/channel | ALIGNED |
| 05 | `1h0wfao` vs Laneige | vs | ALIGNED (anti-subject) |
| 06 | `1arhbj9` balm vs oil | self_variant | ALIGNED |
| 07 | `1qiwlyp` lipstains | launch/contrarian | ALIGNED |
| 08 | `1rzd5vw` sunlit vanilla | portfolio (fragrance) | NATIVE_BETTER (mild) |
| 09 | `1qrcg5i` perfume launch | portfolio | ALIGNED |
| 10 | `1oh26y0` review | review | NATIVE_BETTER |
| r01 | `1r9vw38` vs Ole Henriksen (return-leg, 2026-07-28) | vs | ALIGNED (anti-subject) |

The added row (r01) is itself ALIGNED-anti-subject, so it does not change
the RENDERED_BETTER or NATIVE_BETTER counts — it moves one thread from
"not yet counted" into ALIGNED, taking ALIGNED from 6 to 7 and n from 10
to 11. Both RENDERED_BETTER cells (q02, q03) are reaction/claim-attack
queries "PADDED by brand shopping cards" per the file. Contrast noted in
the file against Tower 28 (3 RENDERED_BETTER / 3 ALIGNED / 1 NATIVE_BETTER,
n=7): "SF's rendered layer is largely FAITHFUL — including faithfully
rendering losses."

## The competitor answer

From `phase2_native_return_findings_v0.md`, with source numbers verified
against `thread_composition_v0.json` and `competitor_ledger_phase2_consolidated_v0.json`:

- **The head-to-head is lost on wear-time.** q05 (vs Laneige, 23 captured
  comments): a **17-point** top comment ("Laneige!!!! ... lasts longer
  than summer Fridays imo") and an **8-point** comment ("Laneige and it's
  not even a question") both pick Laneige; axis is longevity. Google's
  rendered snippet already carries this loss (J3 ALIGNED-anti-subject).
- **Ole Henriksen is the stealth rival.** Never probed in phase 1, it
  entered 3 of the 10 batch threads uninvited (q03 **4-pt** "Ole Henriksen
  is GREAT"; q05 **9-pt** third-name entry; q10 **10-pt** both-liked).
  Text: "Promoted finding-grade (SERP snippet + complaint bodies)." The
  **return-leg capture (r01, r/MakeupAddiction/1r9vw38, 21 comments)**
  then settled a dedicated head-to-head: Ole Henriksen **wins**, top
  comment **7-pt "Ole 100%."**, two more explicit "100%" votes; SF's
  losses land on wear-time/moisturization ("too thin, doesn't last long",
  "does absolutely nothing to moisturize"); dissent is sensory
  (sticky/heavy). The ledger calls this "Calibration case n=3" (referring
  to the 3-comment 100%-vote cluster, not thread count).
  - Corroboration history: closed 2026-07-28 as author-diverse (3 distinct
    authors) but venue-concentrated (all r/Sephora); the return-leg probe
    then surfaced a dedicated r/MakeupAddiction thread plus a Substack
    editorial ("The Great Lip Balm Showdown," rating Ole Henriksen the
    winner) and a comparison-video carousel, closing the venue gap too.
- **SF is the anchor being duped, not the duper-of-anchors** (the ledger's
  stated inverse of the Tower 28 shape): **7 named cheap dupes** render on
  SF's dupe surfaces — **e.l.f., Trader Joe's, Naturium, MCoBeauty,
  Vitamasques, Dionis, Lazy Days** (`dupe_association` entries in the
  consolidated ledger; this list matches the audit's 7 names exactly).
  Google itself renders per-unit floor math for one of them: "SF $48/oz
  vs Trader Joe's about $6.73/oz." **Correction to the audit's phrasing:**
  only Trader Joe's carries this rendered floor math in the files; the
  other 6 dupes are named on dupe surfaces without an attached price/floor
  figure — "7 named cheap dupes with floor math" over-generalizes a
  single specimen to all 7.
- **...while simultaneously read as duping downward:** q07 (52 captured
  comments) carries a **123-point** top comment — "Summer Fridays, the
  brand copied by all, is now duping Huda and Covergirl" — plus a
  **16-point** price-double critique ("not really a dupe for covergirl if
  these lip liners cost double the amount"). Huda Beauty and Covergirl
  both "enter finding-grade with an inverted-direction note" (SF is the
  duper here, not the duped).
- **Retailer own-brand substitution:** the anchor thread's **79-point**
  comment names Sephora Collection's overnight hydrating mask as "a GREAT
  dupe" for the Jet Lag mask.
- **Commodity floor:** Vaseline/Aquaphor recur across 3 threads as the
  derm-endorsed baseline (anchor **18-pt** "dermatologists tell you that
  vaseline or aquaphor is best").

## Ledger promotions (correcting/confirming the audit's "3 ledger
promotions")

The consolidated ledger's `finding_grade` rung holds **4** entries after
phase 2: Laneige, Ole Henriksen, Huda Beauty, Covergirl. Of those, the
findings note's prose explicitly frames **3** as promoted/newly-entering
finding-grade during this phase-2 pass:

1. **Ole Henriksen** — "Promoted finding-grade (SERP snippet + complaint
   bodies)."
2. **Huda Beauty** — "enter finding-grade with an inverted-direction
   note."
3. **Covergirl** — same sentence as Huda Beauty.

**Laneige is NOT counted as a phase-2 promotion** in the source text —
it was already `finding_grade` from the retroactive Channel-0 seed (its
SF phase-1 equivalent), and phase 2 only added native corroboration (the
decisive q05 win), not a rung change. So the audit's "3 ledger
promotions" is confirmed as-written if read as "3 entries promoted during
this native-return phase" — but the ledger's total finding-grade count is
4, not 3, and the source files never use the literal word "promotion" as
a formal ladder-transition record; this is an inference from the prose
"Promoted finding-grade" / "enter finding-grade."

## Return-leg probes: 10 AUTHORED, NOT RUN + 1 EXECUTED

The audit's "10 return-leg probes authored-not-run" is confirmed for
probes #1-10 below. There is an 11th row in the same table
(`phase2_native_return_findings_v0.md`) that **was executed** on
2026-07-28 — do not conflate it with the still-unrun 10, and do not
confuse its table position ("#11") with queue item #11 above (the
"worth-it" thread) — these are two different numbered lists in two
different source files that happen to share the numeral 11.

| # | probe | derived from | status |
|---|---|---|---|
| 1 | `laneige lip glowy balm price` | J5 floor for the head-to-head winner (q05) | NOT RUN |
| 2 | `ole henriksen peptide lip treatment price` | J5 for the stealth rival (q03/q05/q10) | NOT RUN |
| 3 | `summer fridays lip butter balm how long does it last` | unmet-value axis 1 — does Google render the longevity complaint? | NOT RUN |
| 4 | `covergirl lip liner price` | verifies the q07 'costs double' denominator | NOT RUN |
| 5 | `sephora collection overnight hydrating mask` | retailer own-brand dupe check (anchor 79-pt) | NOT RUN |
| 6 | `summer fridays flushed lip stain dupe` | does the reverse-dupe narrative render beyond Reddit? (echo guard: SF's own echo bears no rung) | NOT RUN |
| 7 | `lip balm for sensitive lips` | reaction-axis category surface — who owns it (derm floor?) | NOT RUN |
| 8 | `summer fridays perfume` | portfolio-expansion surface check (q09 EdP tease) | NOT RUN |
| 9 | `is summer fridays worth the splurge reddit` | locates queue #13 (owner_observed, unlocated) | NOT RUN |
| 10 | `summer fridays not an influencer reddit` | locates queue #12 | NOT RUN |
| 11 | `summer fridays vs ole henriksen lip treatment` | promoted-rival-with-no-captured-head-to-head rule | **EXECUTED 2026-07-28** (single owner-directed capture interleaved into the full-bank run's inter-job gap, 0 blocks): probe `sf-ret-01` (Google, CloakBrowser) + native capture `return_leg\r01` (Reddit). Result folded into the J3 table (row r01) and the ledger (Ole Henriksen entry) above. |

**0 blocks in 9 batch captures** + **0 blocks in the 1 return-leg
capture.** The Google stream was not otherwise touched during the batch
(one-stream rule; the full-bank megadogfood run was live throughout).

## Unmet-value map (competitor-facing, from `phase2_native_return_findings_v0.md`)

Owning source for concern evidence remains
`forseti-sf-serp-pass1v1-dogfood-20260727\analysis\concern_ledger_v0.json`
(external to this folder; not re-verified here). This map is the
competitor-side reading added by phase 2:

1. **Wear-time/longevity** — cleanest one-directional axis, zero
   durability defenses observed: "lasted 5 mins" (anchor), Laneige's
   17-pt win-reason, "rubs off after 30 seconds" (q10 render), "feeling
   is gone sooo quickly" (anchor). Laneige owns this axis in the captured
   head-to-head.
2. **Burning/reaction** — live claim-attack surface (q02: 50 comments,
   kw 4 pos/24 neg; q03 OP exits to Ole Henriksen). Lanolin named
   in-thread as a trigger candidate; Merit/Lanolips are shared-defect
   peers, not exits.
3. **Worth-value at $24** — "$48/oz" rendered math; 7 cheap dupes $7-10;
   "slightly better vaseline"; anchor's 295-pt top comment concedes
   "probably overhyped" even while praising.
4. **Authenticity/counterfeit (Amazon)** — concern-ledger finding-grade;
   scam-warning mediator content renders on the legit query; q04 native
   stays cautious (6 comments, no verdict flip).
5. **Originality erosion** — new axis from q07: launches read as copies
   at double price (123-pt mockery). Brand-equity attack, not a product
   defect.

## Mediators and retailers accrued

- **Mediator delta:** SKINSKOOL (ingredient-based dupe aggregator,
  rendered on the dupe probe), beautyybylucyy (TikTok dupes review),
  Kristen Marie (YouTube "PERFECT SF dupe" video), "Sarah" (expert
  real-vs-fake video, "DO NOT GET SCAMMED", 14.7K+ views), Michael Park,
  MD (Instagram — AIO-cited twice, meets recurrence bar).
- **Retailer-set delta:** Target (MCoBeauty/Vitamasques/Dionis dupe
  shelf), Trader Joe's (dupe duo), Amazon (counterfeit-risk channel),
  Sephora (primary; own-brand dupe of Jet Lag).
- **Open J5 (price-architecture) triggers, per the ledger** — none of
  these have been captured yet: Laneige Lip Glowy Balm floor, Ole
  Henriksen Peptide Lip Treatment floor, Covergirl lip liner price
  (the "costs double" denominator), e.l.f./Naturium/MCoBeauty exact
  prices. "SF standing-floor check: no refill/jumbo per-unit answer
  observed in captured surfaces (contrast Tower 28's refill floor) —
  absence is an observation about captured surfaces only" (ledger's own
  phrasing, not a claim that no such SKU exists).
- **Rendered price lines observed:** Lip Butter Balm $24.00 (3 shopping
  cards: 4.7 stars x 3,995 / 4.9 x 10 / 4.8 x 1,012 ratings); $48/oz via
  source-rendered math; Flushed Lip Stain $22 (q07 render); Sheer Skin
  Tint $42 (shade-finder row); SoftLine Lip Liner priced in the q07
  render but the value is cut off in the captured row.

## Ambiguities and open gaps (reported, not resolved)

1. **Queue item #11** (the "worth-it" thread, distinct from queue items
   #12/#13) has no authored return-leg locator probe in this folder's
   table — the queue's own text flags it as unlocatable "without a Google
   search," but unlike #12 and #13 it was not given a follow-up query.
2. **`serp_lane_v0.md`'s in-progress summary is stale** on two points:
   it states J3 settled at n=10 (2/6/2) and "10 return-leg probes
   authored NOT run," both true only before the r01 return-leg capture
   was executed and folded in on 2026-07-28. The files now show n=11
   (2/7/2) and 10 authored-not-run + 1 executed. This is the normal
   staging-ahead-of-repo relationship, not an error, but the two numbers
   should not be read as the current state.
3. **Two different "#11" numberings collide** across source files
   (queue item #11 vs return-leg probe table row #11, see above) — a
   readability trap for anyone skimming both files together, named here
   rather than silently renumbered.
4. **"Calibration case n=3"** in the ledger's Ole Henriksen entry refers
   to the 3-comment 100%-vote cluster in the r01 thread, not a 3-thread
   sample — the phrase is easy to misread as a thread count given the
   3-thread/3-author corroboration language used two sentences earlier
   for a different claim (author-diversity of the pre-return-leg
   evidence).

## Authority and currentness

The **living surface** is the operator staging folder
`C:\tmp\forseti-sf-phase2-native-return-20260728\` (plus its external
dependencies `C:\tmp\forseti-sf-serp-pass1v1-dogfood-20260727\` for the
queue and concern ledger, and `C:\tmp\forseti-sf-reddit-anchor-20260727\`
for the anchor thread's own findings). This file is the **durable routed
record as of 2026-07-28**. If the two diverge, staging is ahead — as it
already is relative to `serp_lane_v0.md`'s pre-return-leg summary line
(see Ambiguities above). Raw capture data (packets, HTML, screenshots)
stays outside Git on the operator drive; this file preserves only the
extracted findings, counts, and quotes.
