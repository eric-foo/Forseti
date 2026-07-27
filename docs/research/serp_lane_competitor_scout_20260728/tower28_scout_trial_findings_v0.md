# Tower 28 Competitor-Scout Trial — findings v0 (2026-07-27)

Live trial of the Understanding-cycle scout pass + journey levers
(`understanding_cycle_competitor_scout_step_v0.md`,
`competitor_ledger_spec_v0.md`). 8 phase-1 probes + 2 phase-2 vs probes,
210s cadence, main run paused (owner-approved), zero blocks.
US-parameterized logged-out route; US-parameterized is not physically
US-local. Counts of observed result cards only — never prevalence,
volume, or share claims. Raw packets: `packets\`; extractions:
`extracted_v2\`; typed ledger: `competitor_ledger.json`.

## Harvest result (phase 1, 8 probes)

Typed ledger: 14 entries. The clean names, all from dupe-door surfaces:

- **Hourglass — anchor_up** ("Tower 28 Concealer: The Affordable Dupe
  for Hourglass"): Tower 28 rides Hourglass demand at the premium end.
- **NYX — dupe_association** ("Is the NYX concealer a dupe for the
  Tower28?"): the SAME NYX pairing the Tower 28 CI chain-card recorded
  (the $12 NYX substitute on dupe surfaces, OBS-023 pattern),
  independently resurfacing in a fresh 2026 SERP. (Emitter mistyped the
  direction — bug logged below.)
- **Haus Labs — rival** (manual read: "Tower 28 concealer or Haus Labs
  by Lady Gaga…" on the reddit surface; the emitter's vs-pattern misses
  "X or Y" phrasing — lesson below).
- **Hypochlorous-acid category — commoditization exit** (AIO, both dupe
  probes): Google's AI Overview reframes "tower 28 dupe" into "Top
  Hypochlorous Acid Dupes/Alternatives" — the rendered exit from the SOS
  hero is the INGREDIENT, not a rival brand. Any HOCl spray substitutes.
- Zero rivals from phase-1 titles (no vs-language on seed SERPs) —
  confirms the ordering rule: vs probes require harvest first.
- Native follow-through queue (mediators, not ledger entries): r/Sephora
  thread cluster, javonford16 (TikTok), **Dr Aamna Adel (IG derm — F21
  cross-scope professional layer)**, megansheley, You Beauty, Byrdie.

## Journey levers on the same 8 probes

**J1 — claim-x-dupe cross: the highest-consequence cell is LIVE.**
The `broke me out` SERP is claim-attack surface end to end: "Tower 28
Concealer Made Me Breakout" (TikTok), "tower 28 concealer acne safe?"
(r/MakeupAddiction), "are your tower 28 products acne safe?!" (IG),
"…it broke my husband [out]" — doubt aimed at the acne-safe positioning
itself. The brand is visibly defending on the same surface ("File Swipe
Serum Concealer under: makeup that won't break you out" — brand TikTok).
Cross that with the pre-built cheap exit (NYX dupe pairing, harvest
above): a repeating claim attack with a named cheaper substitute already
rendered is exactly the J1 top cell. The 2024 chain-card's consequence
line ("pressure-test the claim surface before leaning on acne-safe
positioning") is re-confirmed by fresh surface evidence. Counts of
observed cards; composition claims would need native capture.

**J2 — exit-door read: Tower 28's complaint SERP is a RETENTION
surface, not an exit.** `not working` renders repair content ("try it
like this", "How to Fix", "prep your skin first") — zero competitor
cards. Contrast CeraVe, whose `not working` SERP renders "Amazon Basics
vs CeraVe" (megadogfood ledger). J2's value is exactly this contrast:
WHERE the exit renders is subject-specific — Tower 28's exits sit on
dupe/brand surfaces (Hourglass, NYX, HOCl category), not at the
complaint moment.

**J3 — contrarian anchors: the reddit door is dense with them.**
One `{s} reddit` SERP carries 3+ contrarian-titled community anchors
("I can't be the only one who doesn't like…", "Am I the only one who's
not a fan…", "What am I doing wrong…"). Lane F15 measured contrarian
anchors as rare (0 in 8) on NATURAL queries — the reddit-suffix shape
appears to be the contrarian door specifically. F15 needs a shape
qualifier, not a withdrawal. Native capture of these threads (Reddit
lane) is the composition follow-through.

## Phase 2 (harvested-rival vs probes, t28-09/t28-10 — both clean)

The cycle N->N+1 loop closed: both vs probes used HARVESTED names, and
both opened exactly the door F17 predicts — the vs shape is the social
carousel: 10+ comparison videos per SERP (TikTok/IG/YouTube), plus
community threads ("Hourglass vs. Tower 28 concealers" r/Sephora,
"Nyx bare with me or Tower 28 concealer?" — the or-pattern again).

Price-tier structure now typed, both directions observed:
- **UP: Hourglass** — dense creator comparison surface; rendered
  snippets lean Tower 28 ("The Tower 28 is just so much better…") —
  Tower 28 competes upward successfully in rendered content. AIO
  present on this probe.
- **DOWN: NYX** — framed as the budget exit in the surface's own words
  ("A Budget-Friendly Showdown", "this one is a little bit high end and
  this one is drugs[tore]") — confirming NYX as the substitute-down
  pressure the 2024 chain-card recorded.
- New mediators accrued: SkinSort (ingredient-comparison outlet, BOTH
  vs probes — F12 candidate), creator "Lexie" (IG concealer showdowns).

Harvest totals after phase 2: 30 probes scanned, 55 entries
(41 rival-typed from the two vs probes alone). Candidate-rung noise
(You Beauty, "Recommend") unchanged — the v0.1 emitter queue stands.

## Native follow-through (2026-07-28): 14 threads + price surfaces

14/14 r/Sephora-cluster threads captured via the Reddit lane (raw
retention, zero access failures — first live exercise of the deleted-OP
gate fix). Composition read: `forseti-tower28-reddit-20260728\
thread_composition_v0.json`. Key results:

- **Channel 3 works and changes the answer.** Complaint bodies name a
  DIFFERENT consideration set than SERP surfaces: Kosas, NARS, Haus
  Labs, Tarte Shape Tape recur across threads; SERP gave Hourglass/
  NYX/Saie. **Haus Labs = first finding-grade competitor** (SERP or-
  pattern + complaint bodies = 2 surface classes). **Kosas reaches
  finding-grade via Channel 4**: Sephora renders a Kosas/Hourglass/NARS
  comparison carousel on Tower 28's OWN PDP (captured, t28-pdp-04).
- **J3 divergence specimen:** on `vs hourglass`, Google's rendered
  snippet leans Tower 28 ("just so much better") while the captured
  thread's top-voted comment (7 pts) prefers Hourglass. One thread,
  counts-only — but exactly the rendered-vs-actual gap J3 measures.
  Contrarian-titled threads carry mixed bodies (kw-hits 6 pos/5 neg),
  so contrarian TITLE is a door, not a composition verdict.
- **Prices verified (rendered 2026-07-28):** Swipe $24 (brand +
  Sephora agree); SOS Rescue Spray $28 standard. Tier confirmed on
  Sephora's own carousel: Kosas $17-32, Hourglass Vanish $20-39,
  NARS $17-36. And the commoditization defense is ALREADY LIVE on the
  brand site: tagline "The Original Hypochlorous Acid Spray"
  (originality anchor), Jumbo/Travel/Duo formats, and a 4-bottle
  refill at $68 (≈$17/bottle) — their own price-per-ml answer. The
  constructed SOS PDP slug 404'd (recorded); price taken from the
  captured collection page.

## Unmet-value map (provenance-corrected, 2026-07-28)

Ranked by ONE-DIRECTIONAL evidence weight in the 14 captured threads
(provenance pull: `forseti-tower28-reddit-20260728\bin\
provenance_pull.py`); an earlier chat-level ranking put creasing first
— the full pull corrected it:

1. **Shade range** — the cleanest unanimous defect: "I wish they had a
   better shade range" (slot_013, 15 pts) + 35-pt Haus Labs
   color-variety comment (slot_012) + "definitely not wide enough"
   (slot_008) + "pulls yellow on those I shade match" (slot_013, MUA)
   + zero defenses observed. Brand partially responding ("They
   expanded the shade range slightly now"). New Channel-3 rival:
   **Kulfi** ("better shade range imo", slot_003) — a shade-range
   specialist entrant already recommended in-thread.
2. **Crease predictability** — CONTESTED, not one-directional:
   high-voted failures (9 pts "creased terribly", 8 pts "creased way
   too much", the 5-pt MUA return) sit beside high-voted successes
   (13 pts prefers it over Natasha Denona, 9 pts "minimal creasing").
   T28 is polarizing on the category's #1 argument axis; Haus Labs
   holds the direct voted comparative ("won't crease like the t[ower]",
   16 pts). The entrant's win condition is PREDICTABILITY, not just
   "doesn't crease".
3. **Dark-circle coverage / grey cast** — "doesn't cover my dark
   circles... still look grey" (slot_003, 6 pts), "greyish tint"
   (slot_013, 4 pts).
4. **Packaging reliability** — SERP-level: "How to Open Tower 28
   Concealer Wont Open" / "How to Fix Broken Tower 28 Concelar"
   (t28-05 organic titles).
5. HOCl potency/stability — DOMAIN KNOWLEDGE, not captured evidence;
   flagged as the one unevidenced axis in the value thesis.

## Emitter lessons from this trial (v0 -> v0.1 queue)

1. Outlet/creator leak: "You Beauty on Instagram" entered the ledger;
   add source-name patterns ("<name> on <platform>") to the mediator
   routing, not the competitor ledger.
2. Direction bug: "Is the NYX concealer a dupe for the Tower28?" typed
   as anchor_up of the subject because the generic token "concealer"
   matched the wrong side. Subject matching needs brand-token priority
   over category tokens.
3. Missing pattern: community "X or Y" phrasing (Haus Labs) — add an
   or-pattern for question/community titles.
4. Junk names ("Recommend", "Find Your Perfect") from imperative title
   prefixes — extend QUESTION_START-style rejection to imperatives.

## Verdict input for the step-shape question

The scout pass produced, from 8 probes: one anchor, one dupe (matching
2024 CI evidence), one rival, one category-commoditization read, a
claim-attack surface check, an exit-door classification, and a native
follow-through queue — before any specialist was commissioned. The
ordering rule (vs waits for harvest) was validated by phase 1 itself
(zero rivals available before harvest). Step framing vs pass framing:
see lane discussion — substance favors "scout pass + ordering rule".
