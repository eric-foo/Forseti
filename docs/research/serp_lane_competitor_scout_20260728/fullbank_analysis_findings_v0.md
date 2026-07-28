# Full-Bank Analysis — Findings v0 (2026-07-28)

Re-judgment of the SERP lane's findings ledger against the full capture
store, commissioned by
`docs/prompts/handoffs/serp_lane_fullbank_analysis_execution_handoff_v0.md`.
Analysis only — no captures were taken; the capture route was
flag-suspended when this ran.

Standing non-claims: counts of observed result cards only, never
prevalence, volume, or share of anything real; US-parameterized is not
physically US-local; raw capture data stays outside Git.

## Coverage — read this before any number below

The capture run HALTED before completing, so this is not the n≈100
complete-subject pass the ledger's triggers anticipated:

- bank 986 jobs; **888 ok, 3 blocked, 95 never run**
- **88 of 98 subjects complete** (every bank job ok); 841 analysable cells
- the store holds 1036 extraction files, MORE than the 986-job bank,
  because 145 ledger ids come from earlier bank versions — file count is
  not coverage, and the pass reconciled against the current bank
- fixed-design comparisons run on far smaller n than the headline: the
  11-shape product design is **n=12 subjects**, the 9-shape product
  design n=19, issue designs n=20–21, the 14-shape deep design **n=5**

One methodological caveat carried from the analysis itself: unique-share
is computed within-subject then averaged, so it is **depressed by a larger
competing shape set**. Strata with different shape-set sizes are not
directly comparable, and panel-vs-fullbank comparisons are only valid
inside a fixed design.

## Cell-by-cell

**F4 — `vs {rival}` is the highest-value shape. HELD, number revised
down.** Unique question share 0.889 (panel, n=3) → **0.812** (full bank,
n=12) in the fixed 11-shape design. It remains #1 by a wide margin — next
best is `side_effects` 0.579, then `dupe` 0.564. The claim survives; the
headline "~0.90" should be restated as ~0.81.

**F5 — the review family is ~one probe, not four. HELD.** `review` 0.396,
`worth_it` 0.396, `honest_review` 0.382, `reviews_plural` 0.375 — still
tightly clustered and mutually duplicative. Boards continue to carry one
review-family probe.

**F6 — pain shapes carry high exclusive yield. CHANGED (weakened).**
Panel put the family at 0.63–0.71. Full bank: `side_effects` 0.722 →
**0.579**, `not_working` 0.639 → **0.544**, `complaints` 0.411 →
**0.271**. Pain shapes still beat the review family, but the range is now
~0.27–0.58 and `complaints` fell hardest. Restate the cell without the
0.63–0.71 band.

**F7 — efficient frontier ≈6 probes. HELD.** Questions reach 80% of the
union at 6.21 shapes (9-shape product design) to 7.42 (11-shape); issue
designs reach it at 4.86–5.30. Domains reach 80% at 3.10–4.33 shapes. The
original "80% of domains in ~4 shapes, 80% of questions in ~6–7" survives
the scale-up nearly unchanged.

**F11 — issue-led queries are richer per probe. HELD, upgrade from lead.**
Issue designs saturate faster than product designs on the same measure
(80% of questions at 4.86–5.30 shapes vs 6.21–7.42), now on n=20–21 issue
subjects rather than a handful. Note precisely what this supports: fewer
probes needed per issue subject. It is not evidence about twin stability,
which this pass did not measure.

**F12 — mediation concentration is a category property. HELD, grew.**
96 creators recur across 2+ subjects. The panel's specimen (one outlet
anchoring two subjects) is now the low end: `youtube:Dr Dray` spans 9
subjects (Beauty of Joseon, blackheads, castor oil, damaged barrier,
Eucerin, heat damage, lip balm dependency, Neutrogena, Paula's Choice).

**F15 — contrarian anchors are rare. HELD, promoted lead → active.**
(Corrected 2026-07-28: an earlier revision of this note said the pass
produced no count. It did — `fullbank_social_and_axes.json` →
`f15_contrarian` — and the cell was re-judged against it.) **42
contrarian titles across 22 subjects, on 40 of 841 probes (4.8%), out of
1704 community cards (2.5%).** Rare confirmed; the panel's 0-in-8 is now
a measured low rate rather than an absence. Concentrated, not uniform:
`milia from eye cream` carries 8 of the 42, `retinol purge` 4.

**F16 — the social axis ranks shapes differently from the question axis.
HELD, strongly.** Social share spans 5.6x across shapes: `reddit_suffix`
0.730 at the top; `ingredients_specs` 0.131 at the bottom. And the
question-rich shapes really are social-poor — `what_causes` 0.261, `bare`
0.289, `normal` 0.293. A board optimised purely for questions still
surfaces almost no native content.

**F17 — `vs {rival}` is #1 on BOTH axes. CHANGED — this is the pass's
biggest correction.** It remains #1 on the question axis (0.812), but on
the social axis in beauty it is **mid-pack**: `alternatives` 0.475,
`worth_it` 0.445, `dupe` 0.442, then `vs_rival` 0.414 — with
`reddit_suffix` 0.739 far above all of them. Panel-era numbers for
vs_rival in beauty (0.60 social share, 8.3 video rows, 4.2 TikTok cards)
do not reproduce: full bank shows 0.414, 3.61 video rows, 2.11 TikTok.
`alternatives` now leads TikTok at 3.00. The universal-door claim should
be withdrawn and replaced with: vs_rival is the question-axis leader;
the social door is `reddit_suffix`, with `alternatives`/`dupe` leading
video platforms.

**F18 — platform doors are shape-specific. HELD, numbers updated, one
sub-claim withdrawn.** Beauty per-shape card counts: TikTok →
`alternatives` 3.00, `vs_rival` 2.11, `dupe` 2.00; Instagram →
`worth_it` 2.48, `dupe` 1.75, `before_after` 1.58; YouTube →
`worth_it` 2.38, `how_to_fix` 2.31, `review` 1.65; Reddit →
`reddit_suffix` 7.81, dominant and unrivalled. **Withdrawn:** the panel
claim that `before_after` is an Instagram-only door with zero YouTube —
full bank shows before_after YouTube 1.31 against Instagram 1.58.

**F19 — a recurring creator layer mediates across subjects. HELD, grew as
predicted.** Panel saw 15+ sources on 2+ subjects; full bank sees **96**.
The cell's own trigger said to expect growth rather than shrinkage, and
that is what happened.

**F21 — cross-scope professional layer. HELD, now quantified.** Of the 96
recurring creators: **63 product-only, 28 bridging product and issue
scopes, 5 issue-only**. So roughly 29% operate across both scopes — the
layer the panel identified from a single specimen is a measurable
population.

**F20 — competitor ledger. HELD as a mechanism; the candidate rung is
weaker than assumed.** 649 probes yielded 463 entries and 14 mediators
(panel era: 206 probes, 173 entries). Hand-adjudication of all 111
candidate-rung entries: **35 USABLE, 39 JUNK, 11 SELF_VARIANT, 26
RECOVERABLE.** Only ~32% are usable as-is and ~35% are junk. The ladder
still does its job — junk is supposed to accumulate at the low rungs —
but "candidate" should not be read as "probably real"; it is roughly a
one-in-three shot before adjudication.

## Emitter defects at scale (reported, not fixed)

Frequencies across 463 entries, for sizing the v0.2 work:

| defect | count | example |
| --- | --- | --- |
| A — name+context compounds not collapsed to parent | 163 | "Vaseline for baby" → Vaseline |
| B1 — vertical context leak into names | 16 | "French Press" as a rival of AeroPress |
| B2 — prose-fragment names | 22 | "real" (q=10) for medicube collagen mask |
| C — comma artifacts in extracted names | 20 | — |
| C — comma-list titles the matcher cannot see | 93 titles, **70 producing zero entries** | "Korean Sunscreen Reviews: Beauty of Joseon, Isntree, …" |

The invisible-comma-list class is the largest recall gap: 70 titles that
name competitors in enumerated form produced no ledger entry at all.
Category A dominates by count but is precision noise rather than lost
signal — those entries exist, they just fail to merge into their parent.

## What this pass did not settle

- Twin stability (F8, F13's replacement rule) — not measured here.
- The 95 uncaptured jobs are not random: the run halted subject-clustered,
  so the missing tail is concentrated in specific subjects rather than
  spread thinly. Re-running after those complete is cheap and would
  mainly firm up the fixed-design comparisons, several of which rest on
  n=12 or fewer.
