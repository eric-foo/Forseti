# Full-Bank Analysis — Findings v0 (2026-07-29)

Re-judgment of the SERP lane's findings ledger against the full capture
store, commissioned by
`docs/prompts/handoffs/serp_lane_fullbank_analysis_execution_handoff_v0.md`.

**Revision 2 (2026-07-29): the bank is now COMPLETE and every number below
was recomputed.** Revision 1 ran at 888/986 with 88 of 98 subjects and
carried a prominent incomplete-coverage caveat; the tail was captured
2026-07-28 23:42 – 2026-07-29 01:55 and the derivations re-run. Several
cells moved, and two of revision 1's own judgments were themselves
coverage artifacts — see F6 and F17.

Standing non-claims: counts of observed result cards only, never
prevalence, volume, or share of anything real; US-parameterized is not
physically US-local; raw capture data stays outside Git.

## Coverage

Reconciled against the durable extraction store, not orchestrator log
lines:

- bank 986 jobs; **986 ok, 0 blocked, 0 zero-row, 0 missing**
- **98 of 98 subjects complete**; 931 analysable probe cells
- the 3 jobs blocked in revision 1 (all `rice water for hair growth`)
  were re-probed successfully on 2026-07-29; their original blocked
  packets are archived, not overwritten
- fixed designs still run on subsets of the bank, and this is the main
  remaining n limit: 11-shape product design **n=12**, 10-shape n=12,
  9-shape n=19, 8-shape issue **n=28**, 7-shape issue **n=29**, 14-shape
  deep design **n=5**. The issue designs roughly doubled (were n=20–21);
  the product and deep designs did not grow, because the tail was
  issue-heavy

One methodological caveat carried from the analysis itself: unique-share
is computed within-subject then averaged, so it is **depressed by a larger
competing shape set**. Strata with different shape-set sizes are not
directly comparable, and panel-vs-fullbank comparisons are only valid
inside a fixed design.

## Cell-by-cell

**F4 — `vs {rival}` is the highest-value shape. HELD, number revised
down, margin much narrower than revision 1 reported.** Unique question
share 0.889 (panel, n=3) → **0.782** (complete bank). It is still #1, but
"by a wide margin" is now wrong: `not_working` **0.651** and
`alternatives` **0.626** sit close behind, and `best_products` 0.626
matches. Restate the headline as ~0.78 and drop the wide-margin framing.

**F5 — the review family is ~one probe, not four. HELD.** `review` 0.377,
`worth_it` 0.376, `honest_review` 0.368, `reviews_plural` 0.323 — still
tightly clustered and mutually duplicative, and the cluster tightened at
full coverage. Boards continue to carry one review-family probe.

**F6 — pain shapes carry high exclusive yield. HELD; revision 1's
"weakened" call was largely a coverage artifact.** Revision 1 read
`not_working` 0.544 and `complaints` 0.271 off an issue-light 888. At
986: `side_effects` **0.586**, `not_working` **0.651**, `complaints`
**0.322**. `not_working` recovered by 0.107 and is now the #2 shape
overall. The honest statement: the family sits ~0.32–0.65 against the
panel's 0.63–0.71 — genuinely below panel at the low end, but
`not_working` is at panel level, and the sharp fall revision 1 described
did not survive completion. `complaints` remains the weak member and is
the one to drop.

**F7 — efficient frontier ≈6 probes. HELD.** Across all complete
subjects, questions reach 80% of the union at **6.36 shapes** and domains
at **3.92**. Inside fixed designs: product 6.21 (9-shape) to 7.42
(11-shape); issue **4.83–5.36**. The original "80% of domains in ~4
shapes, 80% of questions in ~6–7" survives the scale-up nearly unchanged
and is now the best-supported cell in the ledger.

**F11 — issue-led queries are richer per probe. HELD, materially
stronger.** Issue designs saturate faster than product designs (80% of
questions at 4.83–5.36 shapes vs 6.21–7.42), and the issue n roughly
doubled at completion — **n=28 and n=29**, not the n=20–21 revision 1
had. This is now a well-powered comparison. Note precisely what it
supports: fewer probes needed per issue subject. It is not evidence about
twin stability, which this pass did not measure.

**F12 — mediation concentration is a category property. HELD, grew
again.** **113** creators recur across 2+ subjects (96 at revision 1).
The panel's specimen (one outlet anchoring two subjects) is far off the
low end: `youtube:Dr Dray` now spans **11** subjects, `youtube:Doctorly`
8, `youtube:SkinZone` and `youtube:Dr. Daniel Sugai` 7. On the domain
side `livethatglow.com` spans 11 subjects.

**F15 — contrarian anchors are rare. HELD, promoted lead → active.**
(Corrected 2026-07-28: an earlier revision of this note said the pass
produced no count. It did — `fullbank_social_and_axes.json` →
`f15_contrarian` — and the cell was re-judged against it.) **42
contrarian titles across 22 subjects, on 40 of 931 probes (4.3%), out of
1889 community cards (2.2%).** Rare confirmed; the panel's 0-in-8 is now
a measured low rate rather than an absence. Completing the bank added
community cards but no new contrarian titles, which tightens the rate
rather than moving it. Concentrated, not uniform: `milia from eye cream`
carries 8 of the 42, `retinol purge` 4.

**F16 — the social axis ranks shapes differently from the question axis.
HELD, strongly.** Social share spans **6.6x** across shapes:
`reddit_suffix` **0.736** at the top; `ingredients_specs` **0.111** at
the bottom. And the question-rich shapes really are social-poor —
`what_causes` 0.241, `bare` 0.279, `normal` 0.299, `why` 0.305. A board
optimised purely for questions still surfaces almost no native content.

**F17 — `vs {rival}` is #1 on BOTH axes. WITHDRAWN — the pass's biggest
correction, and completion deepened it.** `vs_rival` remains the
question-axis leader (0.782) but at full coverage it does not even reach
the **top ten** on the social axis in beauty. The social ranking is
`reddit_suffix` 0.736, then `how_to_use` **0.533**, `does_work`
**0.517**, `mistakes` 0.482, `honest_review` 0.478, `alternatives`
0.475, `not_working` 0.461, `is_good` 0.448, `worth_it` 0.445, `dupe`
0.442. Revision 1 put `alternatives` at the head of that group on 888;
completion showed two demonstration-intent shapes above it that the
issue-light partial bank had under-sampled. Panel-era numbers for
vs_rival in beauty (0.60 social share, 8.3 video rows, 4.2 TikTok cards)
do not reproduce. Replace the universal-door claim with: **vs_rival is
the question door; `reddit_suffix` is the community door; the video door
is demonstration intent — `how_to_use`, `does_work`, `honest_review`.**

**F18 — platform doors are shape-specific. HELD, numbers materially
updated, one sub-claim withdrawn.** Beauty per-shape card counts at full
coverage: TikTok → `alternatives` 3.00, `honest_review` 3.00,
`how_to_use` 2.82; Instagram → `how_to_use` **3.36**, `does_work` 3.09,
`honest_review` 2.89, `mistakes` 2.89; YouTube → `how_to_fix` 2.56,
`mistakes` 2.56, `worth_it` 2.38, `does_work` 2.36; Reddit →
`reddit_suffix` 7.79, dominant and unrivalled. Total video rows are led
by `honest_review` **9.79**, `mistakes` 8.89, `how_to_use` 8.73.
Revision 1's Instagram leader (`worth_it` 2.48) is now fifth.
**Withdrawn:** the panel claim that `before_after` is an Instagram-only
door with zero YouTube — the bank shows before_after on YouTube 1.31
against Instagram 1.58.

**F19 — a recurring creator layer mediates across subjects. HELD, grew as
predicted, twice.** Panel saw 15+ sources on 2+ subjects; revision 1 saw
96; the complete bank sees **113** (73 YouTube, 24 TikTok, 16 Instagram).
The cell's own trigger said to expect growth rather than shrinkage, and
that is what happened at both scale-ups.

**F21 — cross-scope professional layer. HELD, now quantified and
larger.** Of the 113 recurring creators: **60 product-only, 39 bridging
product and issue scopes, 14 issue-only**. **34.5%** operate across both
scopes, up from revision 1's 29% — completing the issue-heavy tail added
proportionally more bridging creators than product-only ones, which is
the direction the cell predicted.

**F20 — competitor ledger. HELD as a mechanism; the candidate rung is
weaker than assumed.** 649 probes yielded 463 entries and 14 mediators
(panel era: 206 probes, 173 entries). Hand-adjudication of all 111
candidate-rung entries: **35 USABLE, 39 JUNK, 11 SELF_VARIANT, 26
RECOVERABLE.** Only ~32% are usable as-is and ~35% are junk. The ladder
still does its job — junk is supposed to accumulate at the low rungs —
but "candidate" should not be read as "probably real"; it is roughly a
one-in-three shot before adjudication. Unchanged at full coverage: the
ledger runs only on rival-bearing shapes, and every subject carrying
those shapes was already complete in revision 1.

**Root cause of the junk rung (added 2026-07-29).** The emitter splits
titles on four cues — ` vs `, ` or `, `better than`, `X dupes for Y` —
and treats both sides as brand names. ` or ` is the dominant failure:
English uses it for any either/or question, so "Splurge **or** Worth
It?" yields "Just a Splurge", "real **or** fake?" yields "real", "yay
**or** nah?" yields "nah". `dupes for` fails symmetrically because the
left side is usually a question stem — "Anyone know any good dupes for
the Dyson Airwrap" emits "Anyone know any good". Nothing downstream ever
asks whether the extracted string is plausibly a brand.

The promotion ladder then **amplifies** this rather than filtering it:
promotion is by recurrence across distinct queries, and common English
recurs far more reliably than any single rival brand. Junk is not
randomly distributed at the candidate rung — it is selected for. Any
v0.2 must therefore validate BEFORE promoting, not after.

## Emitter defects at scale (reported, not fixed)

Frequencies across 463 entries, for sizing the v0.2 work:

| defect | count | example |
| --- | --- | --- |
| A — name+context compounds not collapsed to parent | 163 | "Vaseline for baby" → Vaseline |
| B1 — vertical context leak into names | 16 | "French Press" as a rival of AeroPress |
| B2 — prose-fragment names | 22 | "real" (q=10) for medicube collagen mask |
| C — comma artifacts in extracted names | 20 | — |
| C — comma-list titles the matcher cannot see | 93 titles, **70 producing zero entries** | "Korean Sunscreen Reviews: Beauty of Joseon, Isntree, …" |
| D — self-variant names pending a vocabulary call | 5 | "Barista Express" as a rival of breville barista express |
| E — scout-mode subject bleed (simulated) | 172 keys, 27.1% of scout output | keys that exist only when the same probes run unbound to a subject |

The invisible-comma-list class is the largest recall gap: 70 titles that
name competitors in enumerated form produced no ledger entry at all. It
has the same root as the junk rung — a comma series carries none of the
four split cues, so the matcher emits nothing rather than something
wrong. Category A dominates by count but is precision noise rather than
lost signal: those entries exist, they just fail to merge into their
parent.

Sequencing this implies: **fix recall (C) and add a validation stage
before promotion first**; category A is cosmetic by comparison.

## Wave-2 addendum (2026-07-29) — everything above's open questions

Wave 2 (572 jobs: P11 fill, failure-intent tournament, platform
suffixes, twins) completed 572/572 after one flag episode. It settled
all three of revision 2's open items; full numbers in
`analysis/wave2_analysis.json` and re-judged cells F4, F6, F8, F23, F24.

- **P11 grew n=12 → 33** and `vs_rival` re-sharpened to **0.821 with a
  real margin** (next: 0.624) — revision 2's "wide margin withdrawn" was
  an artifact of the cross-stratum blend, not the fixed design.
- **Failure-intent tournament (9 shapes × 34 subjects):** `side_effects`
  0.547 leads; new shapes `made_it_worse` 0.480 and `bad_for_you` 0.461
  enter at the top alongside `not_working` 0.469 (2nd–4th
  indistinguishable at the noise floor); `complaints` 0.368 and `regret`
  0.358 are cut.
- **Platform-named suffixes are the strongest doors in the lane (F23):**
  tiktok 17.2 / instagram 13.5 / youtube 11.9 platform cards per probe
  vs reddit's 7.7. The "Reddit-only door" hypothesis is refuted.
- **The noise floor exists and is measured (F24):** same-run question
  agreement 0.863, cross-day 0.809, cross-day domains 0.734; `vs_rival`
  most volatile (0.69), `side_effects` most stable (0.943). Gaps under
  ~0.08 in a fixed design are ties; domain-presence findings need
  2+ captures on different days.

## What remains unsettled after wave 2

- The 14-shape deep design is still n=5; the 10/11-shape designs are
  n=33 — fixed-design n is no longer the binding limit anywhere except
  the deep set.
- Twin decay beyond one day (a 7-day twin batch would extend the curve).
- F15's per-stratum contrarian threshold has no stratum near trigger.
