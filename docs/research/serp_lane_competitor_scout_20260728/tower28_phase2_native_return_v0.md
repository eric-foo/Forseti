# Tower 28 phase-2 native return — consolidated v0 (2026-07-28)

Durable routed record of the phase-2 native-return consolidation for
subject Tower 28, executing the consolidation half of
`docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`.
Consolidates two operator-staging documents
(`j3_settlement_v0.md`, `phase2_native_return_findings_v0.md`) plus the
curated ledger JSON (`competitor_ledger_phase2_consolidated_v0.json`)
into one coherent record. This unit is **LOCAL COMPUTE ONLY — zero new
captures**: at execution time the full-bank megadogfood run was live on
the Google stream, and the one-Google-stream-at-a-time rule makes any
new capture an owner pause-decision, not a lane decision.

## What phase 2 is

Phase 1 (already routed in `tower28_scout_trial_findings_v0.md`)
produced the SERP-side scout harvest: 8 phase-1 + 2 phase-2 vs probes,
a typed competitor ledger, journey-lever reads (J1-J5), and — via the
Reddit lane — 14/14 native r/Sephora-cluster thread captures (Channel
3), a Sephora-PDP Channel-4 comparison carousel, verified prices, and
a provenance-ranked unmet-value map. Phase 2 (this record) is the
**native-return consolidation**: it takes those 14 already-captured
threads and (a) settles the J3 rendered-vs-native tag for every
vs/contrarian surface, and (b) merges the phase-1 SERP ledger, the
burst-test ledger, and the Channel-3 thread bodies into one curated,
deduplicated competitor ledger with an updated promotion ladder and J5
price state.

## What was captured (counts)

- **Native captures consumed (already on disk, not recaptured this
  unit):** 14/14 r/Sephora-cluster Reddit threads via the Reddit lane
  (`forseti-tower28-reddit-20260728\thread_composition_v0.json`), zero
  access failures.
- **This unit's output:** a J3 tag for all 14 captured threads (7
  vs/contrarian-class + 7 remaining-class), and a curated ledger of
  **19 entries** consolidating the phase-1 SERP emitter ledger (63 raw
  entries — a documented **3x duplication artifact**: 63 = 21x3, an
  instrument bug in the emitter queue that does not affect the
  underlying evidence), the burst-harvest ledger, and Channel-3 thread
  bodies.
- **New captures this unit: 0** (local compute only).

## J3 settlement — rendered-vs-native tags

J3 compares, per SERP surface, the **rendered snippet stance** (what
Google's phase-1/burst extraction showed) against the **native
top-voted in-thread stance** (the captured thread's actual top-voted
comment). Tags are from the subject's (Tower 28's) perspective:
RENDERED_BETTER = Google's snippet treats Tower 28 better than the
thread's voted verdict does. Counts of observed cards/comments only.

### vs / contrarian threads — the J3-bearing class (n=7)

| slot | thread | class | rendered stance | native top-voted stance | tag |
|---|---|---|---|---|---|
| 001 | `1r3pq3q` | contrarian | Pro-T28 comment rendered ("I LOVE it. No more dry and patchy") | Mixed (kw 6/5); top substitute comment (3 pts) is the NARS/T28 texture-fork | RENDERED_BETTER |
| 002 | `1c87nxw` | vs (NYX) | Neutral OP question rendered | Balanced "love both" (3 pts): NYX fuller coverage, T28 natural days | ALIGNED |
| 003 | `1ifn3jc` | contrarian | Negative rendered ("never fully dries … heavy and messy") | Mixed lean-positive (kw 4/3); substitutes only at 1 pt | NATIVE_BETTER |
| 005 | `1o4bgp7` | vs (Hourglass) | Negative rendered ("I regret getting the Tower 28") | Negative-lean (kw 1/2); regret comment + NARS recommendations | ALIGNED |
| 009 | `17vbauc` | vs (Hourglass) | Pro-T28 video snippet ("The Tower 28 is just so much better") | 7 pts prefers Hourglass ("Tower 28 just doesn't look good on me") | RENDERED_BETTER |
| 010 | `1apyzrd` | contrarian | Negative rendered ("It separates so badly") | Mixed-negative (kw 3/3); 5-pt Kosas-adjacent "just not for me" | ALIGNED |
| 012 | `1jibdsy` | vs (Haus Labs) | Neutral rendered ("I can't decide. I tried them both on in store!") | Decisive Haus Labs win: 35-pt color-variety, 14-pt, 8-pt pro-Haus; kw 10 pos / 15 neg | RENDERED_BETTER |

**vs/contrarian headline: 3 RENDERED_BETTER / 3 ALIGNED / 1
NATIVE_BETTER (n=7).**

### Remaining captured threads (tagged for completeness; n=7)

| slot | thread | class | rendered stance | native | tag |
|---|---|---|---|---|---|
| 004 | `1iv6pkm` | claim-attack (acne-safe) | Doubt-question rendered | Reassuring bodies (kw 2/0, no exits named) | NATIVE_BETTER |
| 006 | `1g9fh5i` | dupe request | Off-topic glitch snippet | Thin; no concealer dupes produced | ALIGNED |
| 007 | `15zihlb` | general | Neutral question rendered | Mixed (kw 7/5) with high-voted pros; 27-pt shade complaint | ALIGNED |
| 008 | `17tc5tz` | general | Pro rendered ("lightweight and hydrating") | Positive (kw 9/3) | ALIGNED |
| 011 | `1fbtwxi` | repair/technique | Negative OP complaint rendered | Negative-lean (kw 4/9) incl. 5-pt MUA return; technique fixes present | ALIGNED |
| 013 | `1pxepp2` | review | **SPLIT RENDER** — same thread, opposite polarity on two surfaces: t28-04 forum block leads pro (35-vote top answer); t28-07 organic leads negative ("greyish tint") | Split (kw 20/19); top captured comment 33-pt pro | per-surface: ALIGNED (t28-04) / NATIVE_BETTER (t28-07) |
| 014 | `1ltb4ci` | dupe (SOS spray) | Ingredient-comparison snippet | Dense cheap exits: 28-pt Magic Molecule $8, Briotech supplier reveal, 31-pt HOCl-commodity explainer | RENDERED_BETTER |

Together these 14 rows are all 14 captured threads (7 + 7); the J3
headline above (n=7) covers only the vs/contrarian class, which is the
class the spec treats as J3-bearing.

### Consequences (per spec `competitor_ledger_spec_v0.md` § J3, counts-only)

- **RENDERED_BETTER surfaces** — where the subject should NOT drive
  attention (a rival would): the Haus Labs vs-thread (`1jibdsy`), the
  vs-Hourglass thread (`17vbauc`), and the SOS dupe thread
  (`1ltb4ci`). Google currently flatters Tower 28 relative to the
  threads' voted verdicts on all three.
- **NATIVE_BETTER surfaces** — where the subject should drive clicks:
  the acne-safe claim thread (`1iv6pkm`; bodies reassure, zero exits)
  and `1ifn3jc` (thread body friendlier than the rendered complaint).
- **Split-render specimen (`1pxepp2`), corrective lesson:** one
  thread, two SERP surfaces, opposite rendered polarity. Snippet
  stance is a property of the **query surface**, not the thread. This
  corrects a natural misreading of the J3 table: a thread ID does not
  carry one fixed rendered stance. **J3 tags must stay per-surface,
  not per-thread.**

## Ledger delta — `competitor_ledger_phase2_consolidated_v0.json`

Curated parent-brand merge (consolidated 2026-07-28) of the phase-1
emitter ledger (63 raw entries, the 3x/instrument-bug duplication
noted above), the burst harvest, and Channel-3 thread bodies. Ladder
per `competitor_ledger_spec_v0.md`. Use-context mentions (tools,
primers, powders — e.g. a Rare Beauty brush, elf/glossier primers, a
Hourglass powder in slot_011) are excluded per emitter lesson 1.
Counts of observed cards/comments only.

**Curated ledger total: 19 entries**, by rung:
- **finding_grade (7):** Haus Labs, Kosas, NARS, Tarte (Shape Tape),
  Hourglass, NYX (Bare With Me), Saie.
- **candidate (3):** Kulfi (Main Match), Natasha Denona, Hypochlorous-
  acid category.
- **presence (9):** Magic Molecule, Briotech, Caliray, e11ement, Laura
  Mercier, Too Faced, Dior, YSL (Touche Eclat), Giorgio Armani.

### Promotions to finding-grade (7 total)

**Carried from trial/burst notes (3):** Haus Labs, Kosas, NARS —
already finding-grade before this consolidation.

**NEW this consolidation (4):** **Tarte (Shape Tape), Hourglass, NYX,
Saie.** The mechanical ladder promotes a name to finding-grade once
thread bodies supply a second surface class beyond the SERP class;
prior notes had not applied that rule to these four even though the
qualifying evidence already existed. Per-entry surface classes and
citations, from the ledger JSON:

- **Tarte (Shape Tape)** — `serp_question_layer` + `complaint_body`.
  Cites: related search "Tarte vs Tower 28 concealer" + PAA "Is Tower
  28 or Tarte concealer better?"; slot_007 14-pt ("usually go for the
  tarte shape tape... unlike shape tape"); slots 005/008/013.
- **Hourglass** — `serp_question_layer` + `complaint_body` (also typed
  `anchor_up`). Cites: 7 distinct phase-1 queries incl. dupe-door
  "Affordable Dupe for Hourglass"; slot_009 7-pt prefers-Hourglass;
  slots 005/008/012/013.
- **NYX (Bare With Me)** — `serp_question_layer` + `complaint_body`.
  Cites: "Is the NYX concealer a dupe for the Tower28?" (dupe probes,
  direction-corrected v0.1); slot_002 3-pt both-fine verdict (NYX
  fuller coverage); slots 001/003/008.
- **Saie** — `serp_question_layer` + `complaint_body`. Cites: PAA "Is
  the Saie or Tower 28 concealer better?" (2 queries, phase-1
  candidate); slot_012 4-pt ("loved the Saie one as well, but it was
  just too light in color"). **Thinnest promotion in this pass:** a
  slot_011 Saie mention is a primer and is excluded as use-context, so
  the complaint-body leg of this promotion rests on slot_012 alone.

### New Channel-3 names (complaint-body-only surface, n=8)

Kulfi (candidate rung; "shade-range specialist entrant," slot_003
"better shade range imo," slot_013 6-pt "Bought Kulfi after trying a
sample and love it") + Natasha Denona (candidate; slot_007 13-pt "like
it even more than the Natasha Denona"), and at presence rung: Magic
Molecule, Briotech, Caliray, e11ement, Laura Mercier, Too Faced, Dior.

**Sharpest single find: Briotech — supplier-as-substitute** (slot_014,
SOS-spray thread): "Briotech supplies Tower28 with their hypochlorous
acid! I buy their huge jugs" (7 pts) plus an 8-pt Walmart screw-top
note. The thread names Tower 28's own claimed upstream supplier as the
direct cheap exit — the sharpest commoditization evidence held in this
ledger. Adjacent in the same thread: Magic Molecule (28-pt "Try magic
molecule's hypochlorous acid, at ulta and a small bottle is $8"; 2-pt
"same exact thing as tower 28") — the highest-voted cheap exit for the
SOS hero, $8 vs. Tower 28's $28 list.

**Mediator delta:** MECCA Chit Chat (Facebook group, rendered on
t28-09) — community mediator candidate.

**Retailer-set delta:** Ulta (Magic Molecule), Walmart (Briotech),
Walgreens (store-brand HOCl, ingredient-list dupe in the t28-03
snippet), Amazon (e11ement).

**Stale flags:** none.

**Open J5 triggers (6):** Tarte Shape Tape (new promotion, no line),
Kosas dedicated floor, NARS dedicated floor, Hourglass dedicated
floor, NYX re-verify, Saie floor.

**Unmet-value map:** unchanged this unit. Owning source remains
`tower28_scout_trial_findings_v0.md` (shade range > crease
predictability > dark-circle coverage > packaging; provenance-cited).

## J5 state per promoted name

| name | line | state |
|---|---|---|
| Haus Labs Triclone | $32.00 list, $4.57/ml | settled (burst b02) |
| Kulfi Main Match | $26.00 list, $5.20/ml | settled (burst b04) |
| Kosas Revealer | $17-32 carousel range | dedicated floor OPEN |
| NARS Radiant Creamy | $17-36 carousel range | dedicated floor OPEN |
| Hourglass Vanish | $20-39 carousel range | dedicated floor OPEN |
| Tarte Shape Tape | none | OPEN (new promotion) |
| NYX Bare With Me | ~$12 (2024 chain-card, unverified this cycle) | OPEN |
| Saie | none | OPEN |

Reference floor: Tower 28 Swipe $24 / 6 ml = $4.00/ml (per-ml value
leader of the settled three); SOS $28 list, ~$17/bottle refill floor
vs. Magic Molecule $8.

## Targeted-probe queue — return leg (AUTHORED, NOT YET RUN)

**Status: none of the 9 probes below have been run.** They are queued
behind the full-bank megadogfood run per the one-Google-stream-at-a-
time rule; band cadence and the echo guard apply throughout (a probed
name's own appearance bears no new rung).

| # | probe | derived from | status |
|---|---|---|---|
| 1 | `kulfi vs tower 28` | entrant check; unmet-value axis 1 (shade range), slot_003/slot_013 | NOT YET RUN |
| 2 | `tarte shape tape price` | J5 for new promotion (no line held) | NOT YET RUN |
| 3 | `kosas revealer concealer price` | J5 dedicated floor (carousel range only) | NOT YET RUN |
| 4 | `nars radiant creamy concealer price` | J5 dedicated floor (carousel range only) | NOT YET RUN |
| 5 | `caliray concealer vs tower 28` | slot_012 35-pt names Caliray best-in-thread | NOT YET RUN |
| 6 | `magic molecule vs tower 28` | slot_014 28-pt $8 exit; commoditization axis | NOT YET RUN |
| 7 | `briotech hypochlorous acid spray` | supplier-as-substitute check (slot_014) | NOT YET RUN |
| 8 | `tower 28 shade range` | unmet-value axis 1 claim follow-up: does Google render the complaint or the brand's expansion response? | NOT YET RUN |
| 9 | `concealer that doesn't crease` | unmet-value axis 2 shape — who owns the category's #1 argument surface | NOT YET RUN |

## Blocks

0 blocks in 0 new captures this unit. Prior phase-2 capture record: 0
blocks in 14 (Reddit lane), 0 in 4 (burst). No stop events.

## Standing non-claims

- Counts of observed cards/comments only — **never** prevalence,
  volume, or share.
- US-parameterized route is not physically US-local.
- One capture per thread (J3 source, 2026-07-28); prices are
  rendered-at-capture 2026-07-28.
- Raw capture data stays on the operator drive, **outside Git**.

## Authority and currentness

The **living surface** is operator staging:
`C:\tmp\forseti-tower28-scout-20260727\phase2_native_return_v0\`
(`j3_settlement_v0.md`, `phase2_native_return_findings_v0.md`,
`competitor_ledger_phase2_consolidated_v0.json`), backed by the raw
native captures at `C:\tmp\forseti-tower28-reddit-20260728\`
(`thread_composition_v0.json`) and the scout-trial packets at
`C:\tmp\forseti-tower28-scout-20260727\`. **This file is the durable
routed record as of 2026-07-28.** If the two diverge, staging is
ahead. This record does not supersede
`tower28_scout_trial_findings_v0.md` (the phase-1 capture record); it
fills the phase-2 consolidation gap that previously existed only on
the operator drive.

## Source-material ambiguity (reported, not resolved)

The phase-1 raw emitter ledger held 63 entries, documented as a 3x
duplication artifact (63 = 21x3). The curated phase-2 ledger holds 19
entries. Neither source document (`j3_settlement_v0.md`,
`phase2_native_return_findings_v0.md`, or the ledger JSON's own `note`
field) itemizes the reconciliation from 21 (the deduplicated
instrument count) down to 19 (curated, parent-brand-merged,
use-context-excluded) — plausible causes are visible (parent-brand
merges such as folding a bare "NYX" mention into "NYX (Bare With
Me)", and use-context exclusions per emitter lesson 1) but the exact
arithmetic is not shown in either source. Reported here rather than
resolved.
