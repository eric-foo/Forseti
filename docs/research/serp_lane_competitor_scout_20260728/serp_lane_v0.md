# SERP Lane v0 — living state — updated 2026-07-30

The single current surface for the Google SERP capture lane. Detailed
evidence records stay in their run folders; THIS file owns current truth.
When a finding changes: flip its cell's Status, add one line under
Supersessions, point Evidence at the new source. Do not fork this file.

Authored in the repo (owner decision 2026-07-28, superseding the
2026-07-27 C:\tmp staging rule). The operator drive holds raw capture data
and in-flight scratch only — never the sole copy of a decision, rule,
finding, or instrument.

Cold-start index — THIS file is the entry point; satellites in/near this
folder: `competitor_ledger_spec_v0.md` (competitor types, ladder,
channels, cycle installation, journey levers J1-J5, glancer-vs-clicker
J3 tag); `deliver_note_repair_room_retention_v0.md` (Deliver-lane
retention method + offense addendum); evidence folders
`..\forseti-serp-megadogfood-20260727\` (bank run + emitter + fixture
test in `bin\`), `..\forseti-tower28-scout-20260727\` (scout trial,
one-pager, PDP prices), `..\forseti-tower28-reddit-20260728\` (native
threads + composition read).

## Mission

Feed the Understanding phase: find the doors (venues, questions, mediators,
concerns) around a subject with the fewest probes. SERP finds doors; native
capture opens them. SERP output is never composition evidence by itself.

## Standing constraints (non-negotiable)

- US-parameterized logged-out route (`hl=en&gl=us&pws=0`); every durable
  artifact carries "US-parameterized is not physically US-local".
- Counts of observed result cards only; never prevalence/volume/share.
- Blocks are stop signals: back off or stop; never CAPTCHA, never IP
  rotation to escape a flag, never auth. Block pages carry visible exit
  IPs and are never quoted into durable docs.
- No person-targeted queries; no standing monitor without owner direction.

## Findings ledger

Format: F# | status: active / lead / withdrawn | evidence | change-trigger.

**F-numbers are allocated HERE and only here.** This file owns the cells;
satellites (the spec, axis docs, handoffs) POINT at them and must not mint
or restate them. Two lanes minted F23 independently on 2026-07-29 — this
ledger for the platform doors, `competitor_ledger_spec_v0.md` for an
`alternatives` under-crediting claim — because nothing said where numbers
come from. **Next free: F29.**

**Full-bank re-judgment 2026-07-29 (revision 2, COMPLETE bank)** — cells
carrying a full-bank trigger were re-decided against **986/986 captures /
98 of 98 complete subjects**; see `fullbank_analysis_findings_v0.md` for
the full cell-by-cell. Summary: F4, F5, F6, F7, F11, F12, F15, F16, F18,
F19, F20, F21 HELD (most with revised numbers); **F17 WITHDRAWN**.

Revision 1 ran at 888/986 and two of its own judgments were coverage
artifacts: it called **F6 weakened** (completion recovers `not_working`
to 0.651, at panel level) and it put `alternatives` at the head of the
social axis (completion shows `how_to_use` and `does_work` above it).
Capture coverage is no longer the binding limit; the fixed *designs*
are — the 11-shape product design is still n=12 and the deep design n=5,
because the captured tail was issue-heavy.

**F1. Safe sustained rate is 15–20/hour; blocks at 28–40/hour.** active.
Evidence: egress reconstruction + 99 consecutive clean captures at
13–18/hr (`megadogfood analysis/egress_budget_finding_v0.md`, recipe §1).
Owner set operating band 15–20/hr. Trigger: any block at ≤20/hr → drop
band, re-measure; 3 clean days at 20/hr → raise floor.

**F2. No daily cap observed; ~365 clean in 7.2h is the new high-water
mark, and the lane's first volume-shaped block sits just past it.**
active — SHARPENED 2026-07-29, its own trigger fired. Evidence: the
prior figure was ~185/day. On 2026-07-28 23:42 → 2026-07-29 06:53 the
route ran **365 consecutive clean captures over 7.18h (50.8/hr average,
constant frozen 60/hr for the last 4.4h of it)** and then blocked at
07:03 with **no rate change** — the ladder was frozen and the cadence
identical either side of the boundary. That is this lane's first block
that correlates with cumulative session volume rather than rate, which
is exactly what this cell asked for. Read it as ONE observation, not a
threshold: the 07-28 block WAS rate-shaped (41 captures in 30 min), so
the two failure modes both appear to exist. Trigger: a second
volume-shaped block, which would let the two be separated; or a clean
run materially past 365 in a session, which would withdraw the volume
reading.

**F2b. A block is not a rate signal; step-down is now restricted to
escalation probation.** active — IMPLEMENTED 2026-07-29. Evidence: after
the 07:03 block the old handler stepped 60 → 55 → 50 → 45 → 40 → 36 →
32.7/hr. The operator log does **not** support the earlier claim that all
six step-downs re-blocked on the first capture with zero clean captures
between: some did re-block immediately, while others admitted clean
captures before the next block, and the final step-down preceded a clean
continuation after cooldown. The defensible conclusion is narrower:
because every rung change was confounded with a still-live flag and a
different idle interval, the sequence did not show that step-down alone
cleared the flag. Landed response: step back only when the block falls
within five attempted jobs of a rung increase; otherwise freeze the
current rung. Then idle 60 minutes and make one recovery attempt; a
second consecutive block or third block in the run writes
`OWNER_PING.json` and stops for owner routing. Evidence:
`analysis/fullbank_block_decay.json` (sealed; derivation
`serp_fullbank_analysis/block_decay.py`). Trigger: a counter-case where
a probation step-back plus the fixed idle separates rate from flag
decay.

**F2c. Sustained TRAILING LOAD is the variable that separates blocks
from clean captures — instantaneous rate is not.** active (new
2026-07-30). Evidence: pooled diagnosis over **all 1714 Google capture
events across every run directory** (the route is per-IP, so run folders
are not independent samples), 14 blocks, base rate **0.82%/capture**:
- **trailing 1h: blocked median 42 vs clean median 39 — no separation.**
  Rate is definitively not the variable, closing what F1 assumed.
- **trailing 6h: 249 vs 172. trailing 24h: 818 vs 660 — both separate.**
It is a GRADIENT, not a gate: the route ran clean at **961 captures/24h
and 325/6h**, above most blocks, so no threshold is established and none
should be quoted. Blocks also cluster rather than arrive independently.
Consequence: budget the DAY, not the minute — a slower cadence at the
same daily total buys nothing, while a lighter day does.
Evidence: `analysis/fullbank_block_diagnosis.json` (sealed; derivation
`serp_fullbank_analysis/block_diagnosis.py`). Trigger: a block at
trailing-24h under ~200, or a clean run materially past 961/24h.

**The 2026-07-30 00:14 block, diagnosed.** Ruled OUT: the runner
(`dogfood10_runner.py`'s capture invocation is byte-identical to the
orchestrator's, which took 1558 clean captures); the rate (trailing 1h =
**1 capture**); a hot retry (4h06m idle before it). Confirmed: the
packet landed on `google.com/sorry/index` — the interstitial, not a
degraded page. What is left is unsatisfying and worth stating plainly:
it fired at **capture #1 of its session** with the LOWEST trailing-6h
load (121) of any recent block, on a route carrying 650 captures/24h
after three consecutive high-volume days. Best available reading — the
route's standing reputation is depressed by sustained load, so a cold
start now trips where it used to pass; ordinary stochasticity (0.82%
base rate) covers the rest. **Not established**, and the cheap test is
free: a genuinely quiet day (<100 captures/24h) followed by a cold
start. If that starts clean, reputation-recovery is real and the
operating rule becomes a daily budget with recovery days.

**F28. Visual provenance stops at the fold, exactly where the
social-SEO modules begin.** active (new 2026-07-30). Every packet stores
the full rendered DOM (~1.2MB), so WHAT was on the page is fully
evidenced. But the screenshot is `screenshot_mode: viewport` at
**1280x720 with `scroll_passes: 0`** — the top 720px only. Google's
video carousels and social blocks generally sit BELOW that fold, so the
lane's visual record does not cover the region F18/F22/F23 make claims
about, and `rendered prominence` — which the ratified engagement rule
now leans on harder after the F27 amendment — has DOM evidence but no
picture. This matters because Google changes SERP layout: the DOM proves
the module existed, a screenshot proves how it was presented, and only
the second survives a re-render of what the page looked like. Fix is a
knob, not a build: the capture runner already accepts `scroll_passes` /
`scroll_step_px` / `scroll_target_selector`, but they are currently
driven only by the retail capture profiles and are not reachable for the
SERP route. Routed to the capture lane (owner of
`run_source_capture_cloakbrowser_packet.py`, and the runner PR #1386
touches). Cost estimate: full-page SERP screenshots run several hundred
KB to ~1.5MB against the current 125KB, and raw capture data lives on
the operator drive. **Non-claim: existing captures are NOT re-shootable**
— a screenshot cannot be recovered post-hoc, so everything captured
before this is fixed keeps fold-limited visual provenance permanently.
**FIXED 2026-07-30, same turn** (owner-authorized): the capture runner
now takes `--full-page-screenshot`, threaded through
`cloakbrowser_snapshot.py` (Protocol, engine impl, entry point, call
site) to Playwright's `full_page`, and the packet metadata records
`screenshot_mode: full_page` rather than the previously hardcoded
`"viewport"` — so provenance states the mode used instead of leaving it
to be inferred from file size. Proof capture (`laneige lip sleeping mask
tiktok`, `C:	mporseti-fullpage-proof-20260730`): **1280x3833 px
against the old 1280x720 — 5.3x the vertical page**, 735KB vs 125KB,
with 41 `tiktok.com` references in the same packet's content record.
The carousel that had DOM evidence and no picture now has both. Default
stays `viewport`, so nothing changes for callers that do not ask.
Trigger: a SERP page taller than one full-page screenshot can hold.

**F26. A 30-video creator grid covers 1 month or 4 years depending on
the creator; cadence, not grid depth, decides whether an old SERP hit is
comparable.** active (new 2026-07-30). Evidence: 22 TikTok assessment
captures of the recurring-creator layer. Posting cadence spans **0.89 to
49.5 days per video — 53x**. So a fixed 30-row grid covers ~26 days for
`careclarkbsn` and **~3.8 years** for `zakheath`. Consequence, with
arithmetic instead of judgement: **videos needed = referenced video's age
÷ creator cadence.** A one-year-old SERP hit needs ~8 rows of depth for a
monthly poster (already captured) and ~400 for a daily poster (do not
buy it — mark `UNBASELINED`). Test per referenced video: is its timestamp
inside the captured grid span? Inside → baselined; outside → deepen with
`--window-size` only when the arithmetic is cheap. Also: **grid span
measures cadence, NOT life** — every one of the 22 is ACTIVE (newest
video ≤2 days), including all the multi-year-span grids. Evidence:
`creator_grid_liveness.json` in the dogfood store (derivation
`serp_fullbank_analysis/creator_grid_liveness.py`). Trigger: a DORMANT
creator appearing (newest video >90 days), which inverts the problem —
a dormant creator's grid is contemporaneous with the ranked video by
construction.

**F27. Creator reach is collapsing for most of the recurring layer, which
makes "the creator's own recent-grid median" an unstable baseline.**
active (new 2026-07-30). Evidence: within-grid trajectory (median plays,
oldest third vs newest third — one capture, no cross-era comparison) for
22 creators: **15 FALLING, 6 STEADY, 1 RISING**. Falls are steep, not
marginal: `slaybyjess` 1,140,550 → 12,150 (−99%), `rogerwh0` 426,150 →
9,488 (−98%), `skin.ken` 225,950 → 7,924 (−96%), `natalie_oneillll`
398,450 → 160,850 (−60%). **Consequence for the ratified engagement
rule** (`competitor_ledger_spec_v0.md`, 2026-07-29 — engagement weighted
only against the creator's own recent-grid median): for two-thirds of
this layer that median is falling fast enough that the same row scores
differently depending on WHEN the grid was captured, so the weight
measures capture date as much as the row. **Proposed amendment (owner
call, and it is the concurrent lane's rule to change): record raw counts,
never weight them** — which is most of what that rule already says; the
change is dropping the weighting clause rather than adding anything.
Replacement signals, all already held: the video ranked on Google
(relevance, already proven), its rendered prominence, creator recurrence
across 2+ subjects (prioritisation), and the transcript (the only
composition-grade evidence here). Reach trend survives as a CREATOR
state, not a row weight: a creator in −98% decline is a poor partner and
a good displacement target. Evidence:
`creator_grid_liveness.json`. Trigger: owner ruling on the amendment, or
a stratum where reach trend is majority STEADY.

**F25. `vs` / `dupe` / `alternatives` do NOT cannibalise each other;
the apparent effect is a shape-set-size artifact.** active (new
2026-07-30; homes a claim that arrived from the concurrent lane without
a cell of its own). The claim was that the three shapes eat each other
when co-present, leaving `alternatives` under-credited. Tested two ways
on 33 subjects carrying all three:
- **Mutual overlap refutes the mechanism.** Pairwise question-set
  Jaccard among the trio is **0.096** against **0.092** for all other
  shape pairs (n=99 vs n=8280). They duplicate each other no more than
  any two unrelated shapes — the opposite of the F5 review-family
  signature, which is how mutual duplication actually looks.
- **The number that started it is real, and design-relative.**
  `alternatives` unique share is **0.476 in the 11-shape design** and
  **0.747 in the 9-shape design** (which carries neither `vs_rival` nor
  `dupe`). The concurrent lane's "0.749" was the P9 figure quoted
  without its design. Unique share is depressed by a larger competing
  shape set — the methodology caveat this ledger already carries — so
  removing ANY two shapes lifts the rest, and the lift is not evidence
  of cannibalisation by those two specifically.
**Board consequence: none.** All three keep their slots; nothing is
under-credited once compared within a fixed design. Evidence:
`analysis/fullbank_shape_cannibalisation.json` (sealed; derivation
`serp_fullbank_analysis/shape_cannibalisation.py`). Trigger: trio
pairwise overlap exceeding the all-pairs baseline by >0.05 in any
stratum.

**F2b consumer audit (2026-07-30) — first reading WITHDRAWN, corrected
same turn.** The doctrine was landed in the megadogfood orchestrator
only, and the very next run proved that insufficient: `dogfood10_runner`
still carried the old 12–15-min re-probe policy and used it on its first
block. Patched, and the policy moved to a shared home
(`serp_egress_cadence.rung_after_block` / `should_ping_owner` /
`write_owner_ping`, 13 contract tests).

**The alarming part of the first audit was false and is withdrawn.** It
claimed 9 runners "would re-probe a live flag," inferred from a marker
grep rather than from reading their block branches. Reading them: every
one stops immediately — `return_leg_runner` and `tower28_scout` break on
the stop signal, `run_capture_queue` returns 2 "without retry",
`window_probe_runner` stops on first block, `beauty_ext_runner` is
strictest of all ("a block is the answer to the experiment, not a
failure to work around"), `probe_vs_oh` and `retry_blocked` are
supervised one-shots, and the two extractors only classify. **Pause-and-
continue existed in exactly two runners — the two long-running
orchestrators — and both now carry the policy.** There was never a fleet
foot-gun.

What survives: the shared helper earns its place by de-duplicating the
policy across the only two runners that need it and giving the next
long-running orchestrator a tested one to import — not by averting a
danger that did not exist. The two existing runners keep their
equivalent inline policy until next touched; rewiring live capture code
for zero behavior change is churn. Method note worth keeping: a marker
grep is not a behavior audit, and this cell asserted a fleet-wide risk
from one before reading a single block branch.

**F3. Once flagged, recovery is slow and stochastic; prevention beats
reaction.** active — CORRECTED 2026-07-29; series SEALED same day.
Evidence, full decay series (every block → next-attempt gap, voided
retries excluded): cleared at **12.5, 14.7, 83.4, 110.8, and 207.6
minutes**; failed at 10.3–16.6 (x6), **77.5, and 81.8 minutes**. Gaps of
12–15 minutes cleared twice the same morning an 81.8-minute wait failed,
so elapsed idle alone does not separate the outcomes — the earlier
deterministic >26 min / ≤3h25m bracket is refuted, not refined.
Operationally: never retry hot; after the commissioned 60-minute maximum
idle, make one recovery attempt and route a repeated block to the owner.
Non-claim: a clean resume evidences decay on that occasion, not that its
cadence is a safe rate. Evidence: `analysis/fullbank_block_decay.json`
(sealed; derivation `serp_fullbank_analysis/block_decay.py`). Trigger: a
controlled decay series that can distinguish elapsed idle from run/rung
history.

**F4. `X vs {rival}` is the highest-value shape (~0.82 unique share,
wide margin).** active — RE-JUDGED 2026-07-29 wave 2, its own trigger
(design past n=12) fired: the 11-shape fixed design at **n=33** gives
`vs_rival` **0.821**, with a REAL margin — next is `not_working` 0.624.
The same-day "wide margin withdrawn" call is itself withdrawn: it came
from the cross-stratum ALL_complete blend (0.782 with close seconds),
which mixes different shape sets and blurs the gap; the fixed design is
the honest comparison and is now well-powered. Note from F24: vs_rival
is also the most VOLATILE shape between captures (A/B question Jaccard
0.69) — its content churns while its unique-share rank holds. Evidence:
`analysis/fullbank_fixed_design.json`. Trigger: any shape within 0.10 of
it in a fixed design at n≥30.

**F5. The review family (`review`/`reviews`/`honest review`/`worth it`)
is ~one probe of information, not four.** active — RE-JUDGED 2026-07-29:
HELD and tightened. `review` 0.377, `worth_it` 0.376, `honest_review`
0.368, `reviews_plural` 0.323. Consequence: boards carry ONE
review-family probe. Trigger: any member separating by >0.15 from the
cluster.

**F6. Pain shapes carry elevated exclusive yield; the family is now
tournament-ranked.** active — RE-JUDGED 2026-07-29 wave 2. The
9-shape failure-intent tournament (3 proven + 6 new, all on the same 34
subjects, so every subject is its own controlled comparison):
`side_effects` **0.547** #1; **`made_it_worse` 0.480 (NEW)** beats
`not_working` 0.469; **`bad_for_you` 0.461 (NEW)** ties it (gaps of
0.02 are inside the F24 noise floor — 2nd through 4th are
indistinguishable); then `why_stopped_working` 0.421, `dont_buy` 0.404,
`waste_of_money` 0.387, `complaints` 0.368, `regret` 0.358.
**Board consequence: the complaint slots are `side_effects` +
`made_it_worse`/`not_working`/`bad_for_you`; `complaints` and `regret`
are CUT** (both under the review family's ambient level). Numbers are
within-tournament (9 competing shapes) and not comparable to
11-design numbers. Evidence: `analysis/wave2_analysis.json`. Trigger:
any cut shape beating a kept one at n≥30 in a later design.

**F7. Efficient frontier ≈ 6 probes/subject (80% of domains in ~4 shapes,
80% of questions in ~6–7).** active — RE-JUDGED 2026-07-29 COMPLETE bank:
HELD, best-supported cell in the ledger. Across all 98 complete subjects,
80% of questions at **6.36 shapes**, 80% of domains at **3.92**; issue
designs 4.83–5.36, product designs 6.21–7.42. Consequence: default boards
below. Trigger: a stratum needing >9 shapes for 80% of questions.

**F8. Cluster a subject's probes into one session — decay is real but
milder than the panel showed.** active — RE-JUDGED 2026-07-29, its own
trigger (larger twin sample) fired. At n=60 pairs: 4.5h-apart agreement
is **0.863** mean question Jaccard (median 0.917), not the panel's ~0.71
(n=6); cross-day vs the wave-1 original is **0.809**, and domains decay
faster cross-day (**0.734**). Consequence softened: same-session
clustering still buys ~5pp of agreement and stays the default, but 4h
separation is no longer disqualifying for claim comparison; cross-DAY
domain reads are the fragile thing. Full noise-floor doctrine: F24.
Evidence: `analysis/wave2_analysis.json`. Trigger: a twin batch at
7+ days separation.

**F9. AIO is a cached per-intent-cluster object; sample once per cluster.**
active. Evidence: ruleset dogfood (identical AIO across plural/quotes/most
reorders; "honest"/"worth it" are separate clusters); panel showed 1–2
distinct AIO objects per subject across 3+ shapes. Trigger: any twin pair
showing different AIOs for the identical query minutes apart.

**F10. AIO sentiment over community threads = vote-mass read, not census.**
active. Evidence: anchor thread `19eo5it` ground truth (50/50 by count,
~7:1 by votes; `forseti-sf-reddit-anchor-20260727/analysis/`). Consequence:
label AIO-derived sentiment "rendered-surface sentiment"; composition
claims require native capture. Trigger: a second thread audit disagreeing.

**F11. Issue-led queries are richer per probe than product-led.** active
— RE-JUDGED 2026-07-29 wave 2, promoted lead → active on its own
trigger (full-bank issue strata). Evidence: issue designs saturate
faster than product designs on the same measure — 80% of questions at
**4.83–5.36 shapes vs 6.21–7.42** — on **n=28 and n=29** issue subjects
(roughly double revision 1's n=20–21), so this is now well-powered.
`analysis/fullbank_fixed_design.json` (I7/I8 vs P9/P11).
**Scope correction:** the panel headline said "steadier AND richer" on
the strength of issue twins showing 85–100% question overlap. Only the
RICHER half is re-judged here. F24 measured twin stability directly and
found no issue-vs-product split worth claiming, so **"steadier" is
withdrawn** — this cell supports fewer probes per issue subject, nothing
about stability. Trigger: a stratum needing more shapes than the product
designs for the same saturation.

**F12. Mediation concentration is a category property; track outlets.**
active — RE-JUDGED 2026-07-29 COMPLETE bank: HELD, promoted lead →
active on its own trigger. The panel specimen (livethatglow.com anchoring
Rhode AND Laneige) is far off the low end: **livethatglow.com spans 11
subjects**; 113 creators recur across 2+ subjects, led by
`youtube:Dr Dray` at 11. Recurring-AIO-citation bar (2+ independent
queries) marks a mediator for native follow-through. Evidence:
`analysis/fullbank_social_and_axes.json`. Trigger: the top mediator
falling below 5 subjects in a later pass.

**F13. Maturity-scaled question-layer trust.** WITHDRAWN 2026-07-27,
**revisit trigger fired and the withdrawal is now POSITIVE 2026-07-30.**
Was protocol v1.2 rule 3. Failed direct replication (Byoma 41% vs 100%
same-hour, same entity, same instrument). The trigger asked for ≥3 twin
pairs per maturity class; wave 2's 60 pairs deliver 5–22 per class, and
the claim does not merely fail to replicate — the ordering is inverted
and flat. Median A/B question stability: **young 1.000, very_new 1.000,
issue 1.000, mass_mature 0.917, established 0.846**. The youngest
entities are the MOST stable, and every class sits inside the F24 noise
floor, so maturity is not a trust axis at all. Replacement stands:
twin-capture any claim-bearing query regardless of entity age. Evidence:
`analysis/wave2_analysis.json` → `twins.f13_stability_by_maturity`.
Trigger to revisit: a class separating by more than the F24 floor.

**F14. Quoted-operator AIO suppression.** WITHDRAWN 2026-07-27 (ruleset
dogfood: identical AIOs with and without quotes, both entities).

**F15. Contrarian-titled community anchors are rare and precious.**
active (promoted from lead 2026-07-28 by the full-bank frequency count
its own trigger called for). Evidence: **42 contrarian titles across 22
subjects, on 40 of 841 probes (4.8%), out of 1704 community cards
(2.5%)** (`analysis/fullbank_social_and_axes.json` → `f15_contrarian`);
panel era saw 0 in 8 non-SF natural queries. Rare confirmed, and the
lead's implicit "roughly never" is now a measured floor, not zero.
Concentration is real: `milia from eye cream` alone carries 8.
Consequence: title-vs-AIO polarity contradiction = top native-follow-through
trigger. Trigger: a stratum where contrarian rate exceeds ~10% of
community cards → the anchor stops being a rarity signal there.

### Social-SEO axis (the lane's original purpose: SERP -> social doors)

**F16. The social axis ranks shapes DIFFERENTLY than the question axis —
boards must mix by goal.** active — RE-JUDGED 2026-07-29 COMPLETE bank:
HELD strongly. Social share spans **6.6x**: `reddit_suffix` 0.736 top,
`ingredients_specs` 0.111 bottom. Question-rich shapes are social-POOR
(`what_causes` 0.241, `bare` 0.279, `normal` 0.299, `why` 0.305); a board
optimized purely for questions surfaces almost no native content.
Evidence: `analysis/fullbank_social_and_axes.json`. Trigger: any
question-leading shape exceeding 0.45 social share.

**F17. `X vs {rival}` leads the QUESTION axis only — the universal-door
claim is WITHDRAWN.** RE-JUDGED 2026-07-29 COMPLETE bank: withdrawal
deepens. vs_rival is still #1 for questions (0.782) but does **not reach
the top ten** on the social axis in beauty. Ranking: `reddit_suffix`
0.736, `how_to_use` 0.533, `does_work` 0.517, `mistakes` 0.482,
`honest_review` 0.478, `alternatives` 0.475, `not_working` 0.461,
`is_good` 0.448, `worth_it` 0.445, `dupe` 0.442. The 2026-07-28 revision
put `alternatives` at the head of this group; completion showed two
demonstration-intent shapes above it. Panel-era vs_rival social figures
did not reproduce (0.60 social share, 8.3 video rows, 4.2 TikTok cards).
Replacement: **question door `vs_rival`; community door `reddit_suffix`;
video door = demonstration intent (`how_to_use`, `does_work`,
`honest_review`).** Evidence: `fullbank_analysis_findings_v0.md`.
Trigger: vs_rival re-entering the social top 5 in any stratum.

**F18. Platform doors are shape-specific.** active — RE-JUDGED
2026-07-29 COMPLETE bank, numbers replaced. Beauty per-shape cards:
TikTok → `alternatives` 3.00, `honest_review` 3.00, `how_to_use` 2.82;
Instagram → `how_to_use` 3.36, `does_work` 3.09, `honest_review` 2.89,
`mistakes` 2.89; YouTube → `how_to_fix` 2.56, `mistakes` 2.56,
`worth_it` 2.38, `does_work` 2.36; Reddit → `reddit_suffix` 7.79,
dominant and unrivalled. Total video rows led by `honest_review` 9.79.
**Withdrawn:** `before_after` as an Instagram-only door with zero YouTube
(actual: YouTube 1.31 vs Instagram 1.58). Consequence: pick the probe by
which platform's creators you need. Trigger: any platform's leader
changing across two consecutive full-bank passes.

**F22. Video-card CONTENT differs by platform — but less than titles
alone suggested.** active — RE-JUDGED 2026-07-29 after full
classification (keyword tiers + a cached one-shot semantic pass over the
441-card residue; only 10 of 1488 cards remained truly unclassifiable).
The trigger fired as written: the earlier "Instagram is 57% non-review
caption content" was a CLASSIFIER LIMIT, not a platform property, and is
withdrawn — IG's residue resolved overwhelmingly into how-to,
educational, and review content wearing caption phrasing. At full
classification all three platforms are majority evaluative/instructional
(review+how-to: YT 59%, TT 49%, IG 44%). What genuinely differs:
- **TikTok is the substitution layer** — dupe/alternative 12.7% +
  head-to-head 12.4% = **25%**, double IG (12.7%) and well above YT
  (15.7%). HELD from the first pass.
- **Instagram is the credentialed-explainer + brand layer** —
  educational-science 8.2% (derm/stylist explainers), praise 8.0%,
  promo/brand-copy 4.5%, myth-debunk 2.2% — each the highest of the
  three platforms.
- **YouTube is the deepest evaluative layer** (review 31%, how-to 27%)
  and the only platform where non-beauty verticals appear in volume.
Two semantic-pass discoveries: **myth-debunk/corrective** content (15
cards: targeting a specific viral false claim — CeraVe cancer cycle,
"lips get addicted to balm") is its own genre and a native
follow-through candidate class; explicit sponsorship markers are rare
and structurally skewed (13/441; **YouTube 0 — its disclosure lives in
descriptions, invisible at title level**), so title-level sponsorship
detection undercounts badly and transcript-level qualification (the
capture-spine dogfood) is the only honest read. Consequence: for
competitor NAMES prefer TikTok; for claims and evidence prefer YouTube;
Instagram is where brands and credentialed professionals broadcast.
Evidence: `analysis/fullbank_video_card_kinds.json`
(`serp_fullbank_analysis/video_card_kinds.py`, semantic cache
`analysis/video_residue_classified.json`, report
`analysis/video_residue_report.md`). Trigger: UNCACHED_RESIDUE > 0 in a
re-run (semantic cache stale for a grown corpus), or any platform's
substitution share moving by >5 points.

**F23. Naming the platform returns the most CARDS — and that volume
converts on neither job the lane does. Board slots WITHDRAWN.** active —
RE-JUDGED 2026-07-30, one day after opening, against its own corpus.

The volume finding HOLDS: `{s} tiktok` returns 17.2 TikTok cards per
probe, `{s} instagram` 13.5, `{s} youtube` 11.9, against `reddit_suffix`
7.7 and ~3.0 for the best intent word, with clean platform pull. The
**conversion** claim — that this made them the lane's strongest doors —
is **WITHDRAWN**. Controlled on the 45 subjects carrying both door types:
- **Competitor harvest (the lane's stated purpose): zero.** 18 ledger
  entries were sourced only by suffix probes and **none reached candidate
  rung** — the names are parser debris (`Milky`, `to Clean`, `fake`,
  `Pass`).
- **Creator discovery: a distinct population, three times noisier.**
  Suffix-only creators 674, of which **10 (1.5%)** clear the lane's
  2+-subject bar; intent-only 819, of which **35 (4.3%)** clear it. Per
  probe the suffix door is ~1.8x more efficient at surfacing a recurring
  creator (0.074 vs 0.041) — but only by making a reader sift 674
  accounts to find 10.
- **Coverage: the ordinary probes already reach these platforms.** Intent
  probes surface YouTube for **44 of 45** subjects, TikTok for 34,
  Instagram for 35, at 7.5–9.0 creators per subject, as a by-product of
  asking about dupes, reviews and comparisons. A dedicated probe adds
  ~5.4 more creators per subject — breadth, not coverage.

**Sealing correction (2026-07-30), raised by the YouTube onboarding
pilot:** the feed-absent creator figures (311 TikTok / 301 YouTube / 431
Instagram) were originally sealed as bare COUNTS with the normalisation
unstated, so the pilot could not turn them into candidates and its own
extract disagreed. A count that cannot be reconstructed into the thing it
counts is a claim, not evidence. `fullbank_suffix_quality.json` now seals
the **named sets** alongside the counts (each verified to reconstruct
exactly), and states the normalisation it used — `norm_creator()`:
collapse internal whitespace, strip, casefold. Membership is decided by
string equality, so a consumer normalising differently WILL get a
different total; that function is the reconciliation point.

**How the error happened, because the pattern repeats:** F23 measured
cards-per-probe and read a volume number as a value number — the same
failure as the competitor ladder's junk rung, where recurrence-of-
anything was mistaken for quality, and made the day after fixing that
one. A volume metric needs a conversion test before it earns a
consequence.

**Board consequence: the three platform doors leave the default board**
(v2.2, 11 → 8 probes). `{s} tiktok` survives as a CONDITIONAL follow-up,
fired after phase-1 harvest only when a subject's ordinary probes
returned little or no TikTok AND its social layer is load-bearing
(~11 of 45 subjects, not all). `{s} youtube` (44/45 already covered) and
`{s} instagram` are cut outright.

**What the SERP route still has that native capture does not:** it is
logged-out, reproducible, and carries no account risk, where TikTok's own
search is personalized and needs a live session. That property — not the
card count — is what would earn a slot back. Evidence:
`analysis/fullbank_platform_door_worth.json` (sealed; derivation
`serp_fullbank_analysis/platform_door_worth.py`). Trigger: a stratum
where suffix probes clear the 2+-subject bar at intent-probe rates, or a
consumer needing reproducible logged-out social enumeration.

**F24. The SERP noise floor is measured: ~0.86 same-run, ~0.81
cross-day question agreement.** active (new 2026-07-29, wave 2, 60 twin
pairs re-captured twice 4.2–5.2h apart plus their wave-1 originals).
Same-run A/B: questions Jaccard mean **0.863** (median 0.917, p10
0.636); domains 0.843. Cross-day vs original: questions **0.809**,
domains **0.734** — the agreement drop is 0.109 for domains versus
0.054 for questions, ~2x the drop.
Per-shape volatility spans 0.69–0.94: `vs_rival` **0.69** (most
volatile), `side_effects` **0.943** (most stable), `reddit_suffix`
0.925. **Mechanism not yet measured:** the cited JSON contains aggregate
set overlap, not rank-position persistence, so it cannot establish a
head-stable/tail-auditioning mechanism, a 7–15 audition zone, or greater
top-3 stability. Those remain hypotheses until a position-stratified
twin analysis exists. **Doctrine this installs:** (a) unique-share gaps under ~0.08
within a fixed design are NOT distinguishable — treat such rankings as
ties (applied in F6); (b) any finding resting on a specific DOMAIN's
presence needs 2+ captures on different days before it is
finding-grade; (c) vs_rival conclusions about specific content need
recurrence, though its RANK is stable. This settles the twin-stability
question F11/F13 left open. Evidence: `analysis/wave2_analysis.json` →
`twins`. Trigger: a 7-day twin batch (extends the decay curve), or any
shape's A/B Jaccard falling below 0.5.

**F19. A recurring creator layer mediates across subjects.** active —
RE-JUDGED 2026-07-29 COMPLETE bank: HELD, grew as predicted at both
scale-ups (panel 15+ → 96 at 888 → **113** at 986). Composition: 73
YouTube, 24 TikTok, 16 Instagram; **no editorial outlets** — the layer is
individual creators, and it is medically weighted (Dr Dray 11 subjects,
Doctorly 8, SkinZone 7, Dr. Daniel Sugai 7). Parallel niche layers exist
in other verticals (Tom's Coffee Corner, Mattress Nerd, The Run Testers),
so this is not a beauty artifact. Consequence: the 2+-subject recurrence
bar auto-generates the native follow-through candidate list, extending
F12 from outlets to creators. **Non-claim: recurrence evidences reach,
not independence — sponsorship is not observable from titles.**
Evidence: `analysis/fullbank_social_and_axes.json`. Trigger: the list
shrinking at a larger corpus, or an editorial outlet entering the top 10.
Routing (RECONCILED 2026-07-30 to the ratified spec route): the layer
emits **`grid_capture` tags** per `competitor_ledger_spec_v0.md`
(owner-ratified 2026-07-29) — the spec's first deep-dive trigger IS this
cell's criterion, "creator recurs on 2+ subjects". That trigger is
CROSS-SUBJECT, so it cannot fire inside a single-subject phase-1 pass;
this lane-level derivation is where it fires, and
`serp_recurring_creator_feed_v0.json` is its emission (113 entries with
subjects, scope, and profile URL where an observed card URL supplied one
— 20 of 24 TikTok). **Known defect (2026-07-30): handle recovery keys on
the card's DISPLAY NAME, so distinct accounts sharing a display name
collapse into one entry** — `careclarkbsn`, `skincarewithshelbs`, and
`skinwithhav` were emitted as three handles of one creator and are three
separate accounts (distinct author ids, confirmed by capture). Handles
must be keyed on the account locator, not the rendered name; until fixed,
treat multi-handle entries as multiple creators. The existing social capture runners' input queue
consumes tagged entries; **phase 1 never visits a platform and never
weights a raw social count.** The other three triggers (a statement a
read would weight, an axis/answer-slot's only occupant, #ad-convergence)
are read-time judgments a reader adds. Never direct registry insertion. The frontier's scan-receipt register and owner
disposition batches are NOT written by this lane: a SERP-recurrence
observation is not a TikTok scan, and dispositions are owner acts.
YouTube's admission path is IMPLEMENTED, PILOT-ASSESSMENT COMPLETE, AND
OWNER-REVIEW GATED (2026-07-30):
`forseti-harness/runners/run_source_capture_youtube_creator_onboarding.py`
exports all 73 recurring rows as display-name frontier candidates and
captures public logged-out assessment evidence before the generalized
candidate → judgment → account registry flow is invoked. No pilot creator
has been admitted before owner review. The sealed suffix analysis reports
301 creators outside the 113-row feed, but it preserves only the aggregate;
the current row extract produces a different named set, so those identities
remain unwired rather than guessed or truncated. Shorts and long-form remain
typed, separately baselined axes. Instagram (16) remains an unrouted typed
gap.
**Capture-spine dogfood 2026-07-29 (3 creators, `new_capture`
assessment mode, owner session):** the feed→spine pipe works end to end.
Per creator the lane returned profile metrics + a 30-video grid with
play counts and full descriptions. CI yield on the three questions:
(1) engagement separates cleanly — natalie_oneillll median
plays/follower 0.204 vs drdrayzday 0.049 and skincarewithshelbs 0.047,
so recurrence rank ≠ audience pull. **UNBASELINED under the ratified
engagement rule** (spec, 2026-07-29): social engagement may be weighted
only against the creator's own recent-grid median, never compared across
creators or platforms. These figures are raw observation about who to
prioritise for capture, and license no corroboration weight on any row; (2) video DESCRIPTIONS already
carry competitor names the SERP harvest never saw (Goodal, Purito,
Billie, Athena Club) plus dense in-corpus mentions (innisfree ×9,
bubble ×8, byoma ×7 in one creator's window) — a fifth competitor
channel, pre-transcript; (3) sponsorship markers in descriptions are
near-absent (2/90), consistent with F22's title-level finding —
@-brand-tagging is the visible commercial signal.
**Owner decision 2026-07-29 (refined same day): sponsorship
identification is DEPRIORITIZED** — record disclosure when it appears,
spend nothing hunting it. The transcript pass survives with a different
rationale: **selective disambiguation** — transcribe a video only when
its engagement is high AND its title is ambiguous or complaint/praise-
coded (resonating content whose direction the title can't settle).
Trigger-based, never blanket. Store:
`C:\tmp\forseti-creator-dogfood-20260729\`.

**F20. Competitor identification is an instrument without a step; rival
inputs must come from harvest, not operator priors.** active (gap).
Evidence: no competitor-identification step exists in the Understanding
cycle; comparison/dupe probes surfaced competitor sets in both the SF
return (job 7) and the MGT pilot, but the harvest is untyped and the
`vs {rival}` probe — #1 shape on both axes — currently takes hand-picked
rivals. Consequence: every analysis pass emits a typed competitor ledger
(rival / dupe_association / substitute_down / anchor_up; presence-only
until recurrence x surface-independence promotes, per the ladder); cycle
N+1 `vs` probes draw from cycle N's ledger. Full strategy, type
definitions, and claims-to-complaints wiring:
`competitor_ledger_spec_v0.md` (this folder). Emitter v0
(`bin/competitor_ledger.py`) ran 2026-07-27: 95 probes -> 74 typed
entries, 9 candidates; lessons recorded in the spec (self_variant
question, dupe names need bodies). Cycle installation (owner-ratified
2026-07-28, Tower 28 trial): a scout PASS + one ordering rule (seed ->
harvest -> vs; fan-out waits for the ledger), carried in the spec's
"Cycle installation" section — the separate step doc was collapsed into
the spec and retired. Emitter v0.1 dogfooded on both stores; candidate
rung now promotes real names (NYX, Saie, Summer Fridays Lip Butter
Balm). **v0.4 parent collapse, 2026-07-30 (owner-directed loose end).** A
`RECOVERABLE` name is EVIDENCE for a parent entity, not an entity of its
own: "better AG1" is a vote for AG1. The verdicts cache now carries a
`parent` per RECOVERABLE name (36 of 37 resolved; 1 left `null` with a
stated reason and it stays at presence — unresolved fails visible rather
than being guessed). The emitter merges a collapsed name's sources into
its parent BEFORE rung assignment, so the parent promotes on the evidence
it actually has, and records `collapsed_from` for auditability. Result on
the current corpus: **31 names merged, candidate rung 62 → 74, still 0
pending and 0 junk.** The recovered entries were real rivals hiding
behind mangled strings — AG1 (9 distinct queries, vs bloom greens
powder), Trader Joe's (8, vs Supergoop), CeraVe (7, vs Eucerin), plus
Wholier, Dyson, Cetaphil, Essence, e.l.f., MCoBeauty, Anytype, Haruharu,
and one self-variant (Hoka Bondi 9). Three contract tests pin it,
including that an unresolved parent is never silently merged. This closes
F20's "RECOVERABLE parent-collapse still manual" trigger.

**v0.2 dogfooded 2026-07-29** (owner-directed): two changes,
both from the full-bank adjudication's root-cause read. (1) Enumeration
recall — comma-series titles carried no split cue and 70 of 93 yielded
nothing; a subject-anchored enumeration branch now harvests them
(Isntree entered the ledger from exactly the poster-child title). (2)
Brand-or-not promotion gate (`--verdicts`) — recurrence AMPLIFIES
common English, so the candidate rung is only reachable through a
cached adjudication verdict; unadjudicated recurrers hold at
`pending_adjudication`, fail closed. Dogfood on the grown corpus (1022
probes incl. partial wave 2): ungated candidate rung would be 212
entries; gated run held 101 new recurrers at the door, a model pass
adjudicated them (24 USABLE / 57 JUNK / 11 SELF_VARIANT / 9
RECOVERABLE — the splitter's attribute-list junk died at the gate as
designed), and the final rung is **59 candidates, 100% adjudicated
USABLE, 0 junk**. Verdicts cache:
`analysis/candidate_verdicts_v0.json` (213 entries; the 111 hand labels
are the seed). 16/16 fixture tests pass, incl. 4 new v0.2 contracts
(enum recall, all-candidates-usable, junk-never-candidate,
fails-closed-on-unadjudicated). Trigger: owner typing-vocabulary review
(incl. self_variant); first live cycle running the gated pass;
RECOVERABLE parent-collapse still manual.

**F21. The recurring creator layer splits into two kinds.** active —
RE-JUDGED 2026-07-29 COMPLETE bank: HELD, quantified, and one panel
sub-claim corrected. Of the 113 recurring creators: **60 product-only,
39 bridging product and issue scopes, 14 issue-only** — so **34.5%**
are cross-scope (29% at 888; completing the issue-heavy tail raised it,
as the cell predicted). **Corrected:** the panel's "none recurred on
problems alone" is false at scale — 14 issue-only creators exist.
Consequence unchanged: cross-scope professionals are the priority
native-follow-through targets — they mediate the problem->product journey
that is the Understanding-phase entry point. Evidence:
`analysis/fullbank_social_and_axes.json` → `f21_classification`.
Trigger: bridging share falling below 25%.

## Current default boards (v2.2, 2026-07-30 — from F4–F8, F16–F18, F22,
F23, F24, and the F6 tournament; owner-ratified: run all three tied
complaint shapes. **v2.2 removes the three platform doors** — F23's
re-judgment found the ordinary probes already surface those platforms,
and the dedicated probes convert on neither competitor harvest nor
creator quality.)

Product subject — CORE (8 probes, one session):
`{s} vs {rival}` (harvested rival only, F20; fills from phase-1 rolling
harvest, refreshed again by phase-2 Reddit names) · `{s} review` ·
`{s} side effects` · `{s} made it worse` · `{s} not working` ·
`is {s} bad for you` · `{s} reddit` · `{s} dupe` (or `alternatives`).

These eight already surface the social platforms as a by-product —
YouTube for 44 of 45 subjects, TikTok for 34, Instagram for 35, at
7.5–9.0 creators per subject (F23). The social layer is covered by
default and does not need its own probes.

CONDITIONAL follow-up (not a slot): `{s} tiktok`, fired after harvest
only when a subject's eight probes returned little or no TikTok AND its
social layer is load-bearing. Discount its 31% brand-own-account share
before reading cards as third-party sentiment.
Cut from boards permanently: `{s} complaints`, `regret buying {s}`
(tournament losers), and `{s} youtube` / `{s} instagram` (F23 — already
covered by the core eight).

Issue subject (6 probes, one session) — question-rich but social-poor
(F16): `{i}` · `what causes {i}` · `how to fix {i}` ·
`best products for {i}` · `{i} reddit` · `{i} before and after`
When an issue needs its creator layer, add ONE product-side social probe
(`vs` or `dupe` on the issue's leading product) rather than more issue
phrasings.

Twin-capture the probe whose composition will bear a claim (F24: any
domain-presence claim needs sightings on 2+ days; unique-share gaps
<0.08 are ties). Creator recurrence (F19) accrues automatically; review
the 2+-subject list each analysis pass for native follow-through. The
platform doors surface 301–431 feed-absent creators per platform
(sealed: `analysis/fullbank_suffix_quality.json`), so the recurrence
pool grows substantially every pass that includes them.

## Instruments (current versions)

- Capture: `run_source_capture_cloakbrowser_packet.py`, `--output` packet
  mode (lake-free, ~3–5s/capture). Lake mode only when doctrine requires.
- Orchestrator: `megadogfood-20260727/bin/megadogfood_orchestrator.py` —
  ledger-checkpointed, resume-safe, absolute deadline, persisted 3-strike
  block policy, rest breaks.
- Extractor: `forseti-harness/source_capture/google_serp_content.py` — the
  in-repo, in-flight port of `extract_serp_v2.py` (PAA-exit fix, tile
  grouping, title/source pairing), stdlib-only so the harness gains no bs4
  dependency. Proved identical to the bs4 reference on 291/291 packets.
  `bin/extract_serp_v2.py` is now the reference the port was checked
  against; do not edit the two in parallel. v1 rankings of organic rows are
  known-degraded; re-extract PRE-FLIP packets rather than trust old
  extractions — captures made under content retention cannot be re-extracted
  at all (Method rule 6).
- Analysis: `analyze_megadogfood.py` (7 tables) +
  `panel_shape_analysis.py` (tie-averaged within-subject ranks) +
  `unique_contribution.py` (order-independent shape value) +
  `social_surface_analysis.py` (per-shape platform yield, creator
  recurrence). Order-dependent yield metrics are forbidden for shape
  comparisons. Run the social axis in every analysis pass — it is the
  lane's original purpose and the axis that drifted once already.
- Native follow-through: TikTok/IG/YT capture runners from the original
  SF handoff remain the reference implementations
  (`run_source_capture_tiktok_video_packet.py`, IG calls/reels packet
  runners, YouTube watch/caption runners); the F19 recurrence list is
  their input queue. TikTok Shop US surface stays gated on fresh US
  egress per standing rule. Owner routing 2026-07-28: the competitor
  scout's trigger-thread queue (contrarian/claim-attack/vs threads)
  belongs to the REDDIT LANE after phase-1 SERP — the lane's existing
  fan-out consumes it as one more discovery source, and the J3
  glancer-vs-clicker comparator (snippet stance vs top-voted native
  stance -> ALIGNED / RENDERED_BETTER / NATIVE_BETTER) runs in the
  Reddit lane's analysis step, consuming phase-1 snippets.

## Method rules (paid for in errors this week)

1. Pre-register predictions before capture; judge against them.
2. Shape value is only comparable within subject, with ties averaged.
3. Never rank shapes by capture-order-dependent metrics.
4. Re-measure before shipping a finding: four plausible findings died on
   re-measurement this week (review-wins, fixed question layer, ~100/day
   cap, maturity gradient).
5. RETIRED 2026-07-28 (was: "Preserve raw DOM; version extractors;
   re-extraction must always be possible"). Replaced by the retention
   decision below. Version extractors still.

6. Content retention is the lane's default; re-extraction is FORWARD ONLY.
   The capture runner projects the typed row record in flight and discards
   the rendered DOM after hashing it (`--source-surface
   google_serp_us_parameterized`, `--retention-mode raw` still selectable
   per run for an explicit evidence posture). A blocked or structurally
   empty page trips an anomaly and auto-preserves raw for that capture.
   Extractor defects can no longer be repaired by re-extracting history —
   the v1 mis-ranking repair path is closed for anything captured under
   this rule. What replaces it: (a) the one-time parity gate that proved
   the in-flight extractor reproduces v2 exactly (285/285 packets, zero
   field diffs, 2026-07-28); (b) a rolling raw sample — first capture per
   day or per batch run, 30-day window, auto-pruned — re-checked after ANY
   extractor edit. Instruments: `run_capture_retention_parity_gate.py`,
   `--raw-sample-root`. Measured on this lane's own store: 390.9 MB ->
   37.6 MB (90.4%); the retained-body portion alone drops 98.1%.
   Trigger to revisit: any extractor defect found that the rolling window
   cannot diagnose.

## BLOCKER (partially mitigated 2026-07-28) — read before the next orchestrator run

`megadogfood_orchestrator.py` extracts POST-HOC from `raw/` and must be
updated before it is pointed at a repo checkout carrying the retention
flip. Under content retention the packet has no
`raw/02_cloakbrowser_visible_text.txt`, so `extract_serp.extract_packet`
takes its `if not txt_path.exists()` branch, returns `rows: []` with a
"non-browser packet" note, and the orchestrator scores that as
`outcome="ok"` with `row_count: 0` — a SILENT ZERO-ROW SUCCESS, not a
visible failure.

Required change (lane-side, NOT done by the retention commission — its
bound was `forseti-harness/*`): read `content_record.json` from the packet
instead of re-extracting `raw/`, and treat a missing content record as a
hard failure. Also note the orchestrator still imports `extract_serp` (v1),
not v2, for its in-run row counts.

The in-flight route already emits the same typed rows the post-hoc
extractor produced, so this is a read-path change, not a re-parse.

Not currently firing: the live full-bank run pins
`REPO = ...\worktrees\ulta-powerreviews-adapter-9c4df6`, which does not
carry the flip. The run in flight is unaffected.

Mitigation installed 2026-07-28 (lane-side): `extract()` in the
orchestrator now fails LOUDLY (`content_only_packet_no_raw_dom`) when a
packet carries no raw DOM, killing the silent zero-row fake-pass path.
Backward compatible — never fires on raw-preserving packets, so the
live run is unchanged across restarts. STILL OPEN before pointing the
orchestrator at a flipped checkout: consume `content_record.json` as
the row source (read-path change) and retire the v1 `extract_serp`
import for in-run counts.

## In progress

- Full-bank run: **COMPLETE 2026-07-29 01:55 — 986/986 ok, 98/98
  subjects.** The tail (95 jobs) ran 2026-07-28 23:42 – 2026-07-29 01:44
  at a frozen 45/hr with **zero blocks**, after the IP sat idle ~3h25m
  from the last block; the 3 previously-blocked `rice water for hair
  growth` jobs were then re-probed successfully. F4–F7, F11, F12, F15,
  F16, F18–F21 were re-judged at full coverage (revision 2 of
  `fullbank_analysis_findings_v0.md`); F17 stayed withdrawn and deepened.
  **Two lane lessons from the resume:**
  (a) 3+ hours idle cleared a flag that 12–26 minute waits had not — the
  first F3-consistent *positive* decay observation.
  (b) A retry helper that reuses the orchestrator's `capture()` inherits
  its crash-recovery path, which reuses an existing packet directory and
  re-reads the OLD blocked packet in 0s without contacting Google. That
  produced 3 fabricated "blocked" ledger rows before it was caught; they
  are voided by an explicit `RETRY_CORRECTION` row in `run_ledger.jsonl`,
  and `bin/retry_blocked.py` now archives the prior packet before
  re-probing. Any future retry path must move the old packet aside first.
  **Halt history (2026-07-28 20:00, at 889/986):** two blocks 14 minutes
  apart. The first was
  load-driven and self-inflicted — a restart to change cadence config
  began capturing 2.1 minutes after the previous burst instead of the
  scheduled 10, producing 41 captures in 30 minutes where the schedule
  allows ~32. The second landed on the FIRST capture after a ~26-minute
  gap at a rate two rungs lower, with zero successful captures between:
  that one is flag persistence, not a rate signal (consistent with F3,
  recovery >75 min). Continuing to probe every 14 minutes mostly
  re-confirms a flag, so all capture processes were stopped.
  **What the resume confirmed:** the "idle for hours, not minutes"
  prescription was correct — ~3h25m idle then a frozen rung 5 (45/hr)
  produced 95/95 clean. Escalation stayed frozen throughout, so the run
  is evidence about flag decay, not about 45/hr being a ceiling or a
  floor.
  **What the run established before the blocks:** a clean walk from 27.1
  to 60/hr sustained — 151 consecutive clean captures at 60/hr alone —
  and the observation that clean and blocked stretches were identical at
  10- and 20-minute windows and diverged only at 30 minutes (32 captures
  = 64/hr clean vs 41 = 82/hr blocked). Working hypothesis: the
  half-hour total is the discriminating variable, not the instantaneous
  spike. Cadence, evidence per rung, and the 72/hr-sustained (~77/hr
  peak-30min) rungs authored for the next attempt live in
  `forseti-harness/runners/serp_egress_cadence.py`.
- **Wave 2 COMPLETE 2026-07-29 20:07 — 572/572 ok** (verified against
  the durable extraction store; the 6 flag-window blocked jobs re-probed
  clean at 19:59–20:07 after the archive-first retry path). Analysis
  landed same evening: F4 re-sharpened (n=33), F6 tournament-ranked, F8
  revised at n=60, F23 (platform-named doors) and F24 (noise floor)
  opened. Mid-run flag history kept below for the egress record.
- Wave-2 flag history — flagged 2026-07-29 07:03 at 290/572. Ran clean
  02:39 → 07:03 (264 captures at a constant frozen 60/hr), then six
  blocks in 2.4h that no rung step-down and no 82-min cooldown cleared;
  the orchestrator is in its episode-2 backoff and self-terminates at
  three episodes. What it produced before the flag, and the reason this
  partial is still usable: **the round-robin ordering worked.** Every
  stream landed between 37% and 65% rather than one stream at 100% and
  the rest at zero —
  `p11_fill 74/113 (65%)`, `twin 67/120 (56%)`,
  `platform_suffix 74/135 (55%)`, `complaint_ext 75/204 (37%)`.
  Every stream has enough for a first read; none is empty. Wave-1's
  clustered halt is what made two revision-1 judgments coverage
  artifacts, and this ordering rule was written to prevent exactly that.
  Resume needs hours of idle (F3), not a lower rate (F2b). Remaining 282
  jobs stay pending in the bank and the orchestrator resumes from its
  ledger.

  Design as launched (owner-set 60/hr for ~10h): 572 jobs appended to
  `query_bank.json` by
  `bin/build_wave2_bank.py`; bank 986 → 1558. Pre-wave-2 bank preserved at
  `query_bank_pre_wave2.json`. Rung 8 (60/hr) frozen — no escalation, so
  the run is not rate evidence. ETA ~9.5h of capture time.
  Allocation, chosen against the cells this ledger leaves open:
  - **p11_fill 113** — the 11-shape product design is n=12 and is now the
    BINDING limit on F4/F5/F6/F17; capture coverage no longer is. Fills
    P11 gaps on 32 subjects that already carry most of it, plus the full
    11 for four deeply-covered products that carry none (CeraVe
    moisturizing cream, Laneige lip sleeping mask, Rhode peptide lip
    treatment, AeroPress). Expected n=12 → ~47.
  - **complaint_ext 204** — six new failure-intent shapes (`regret`,
    `dont_buy`, `bad_for_you`, `why_stopped_working`, `made_it_worse`,
    `waste_of_money`) × 34 subjects that already carry `side_effects` and
    `not_working`, so the new shapes are directly comparable against the
    proven family. F6 held at full coverage with `not_working` at 0.651.
  - **platform_suffix 135** — `{subject} tiktok` / `youtube` / `instagram`
    × 45 subjects. `reddit_suffix` is the only platform-named shape ever
    run, so F18's "platform door" language is untested outside Reddit.
    Beauty-first then adjacent/far/issue so the answer is not beauty-only.
  - **twin 120** — 60 already-captured queries re-run twice inside this
    run, 4.2–5.2h apart, `twin_of` pointing at the original. The ledger
    has ~20 findings resting on single captures and the lane has NEVER
    measured SERP volatility; without a noise floor, close rankings
    (0.782 vs 0.651) cannot be called distinguishable. Also yields a
    cross-day comparison against the wave-1 capture.

  Two design rules applied, both from wave-1 failures:
  (a) **Ordering is round-robin across streams, not clustered.** The
  07-28 halt landed subject-clustered and that is what made two of the
  revision-1 judgments coverage artifacts. A wave-2 run that dies at 70%
  yields 70% of every stream.
  (b) **`vs_rival` is filled only from harvest.** 23 subjects got a rival
  from the hand-adjudicated USABLE candidate rung — the cycle-N-ledger →
  cycle-N+1-`vs` flow F20 specifies, running for the first time. The 15
  subjects with no harvested rival keep `vs_rival` as a typed gap rather
  than receiving an operator-picked one.
- Stage 6 merged vs+J5 completion: **COMPLETE and sealed 2026-07-30.**
  The curated scope is 163 base jobs plus two dynamic Shopping reserves;
  130 jobs are analysis-eligible and 35 are quarantined without deleting
  evidence. The integrity seal checked 148 packet manifests, 592 preserved
  file hashes, 17 reused extractions, and all query identities with zero
  failures. The BR540 unnamed-equivalence return leg completed and supplies
  nine rendered named-rival observations for native follow-through. See
  `megadogfood_stage6_queue_completion_v0.md`.
- Queued behind the bank, both built, validated, and gated (no captures
  taken, processes stopped with the bank): the 10-brand scout dogfood
  (`C:\tmp\forseti-scout-dogfood10-20260728\`) and the 120-job beauty
  corpus extension (`C:\tmp\forseti-beauty-ext-20260728\`, 12 new
  subjects, pools into the megadogfood store via its own pooling
  script). The bank gate is now satisfied; this Stage 6 work unit did not
  re-verify either queue's independent execution state.
- Tower 28 phase-2 native return: captures complete (14/14 threads +
  4-capture burst, 0 blocks) and consolidation done 2026-07-28 —
  J3 settlement (3 RENDERED_BETTER / 3 ALIGNED / 1 NATIVE_BETTER on
  vs/contrarian, n=7), consolidated typed ledger (7 finding-grade:
  Haus Labs, Kosas, NARS, Tarte, Hourglass, NYX, Saie), Channel-3
  entrants (Kulfi, Magic Molecule, Briotech supplier-as-substitute),
  9-probe targeted return-leg list AUTHORED NOT RUN (queued behind the
  full-bank run; one-stream rule). See
  `..\forseti-tower28-scout-20260727\phase2_native_return_v0\`.
  Open: 6 dedicated J5 floor reads (Tarte has no line at all).
  (Correction note: an earlier edit today wrongly retired the "13
  threads await" line as Tower 28's — that queue was Summer Fridays'.)
- Summer Fridays phase-2 native return EXECUTED 2026-07-28: the SF
  reddit_capture_queue_v0 (13 threads) is now consumed — anchor was
  already captured; 9/9 remaining located threads captured via the
  Reddit lane (20s fixed, raw retention, 0 blocks); #11-13 unlocatable
  without a Google search, locator probes authored for #12/#13 only —
  #11 has no authored probe (open gap). J3 settled n=11 after the r01
  return-leg row folded in (this SUPERSEDES the n=10 first pass):
  2 RENDERED_BETTER / 7 ALIGNED / 2 NATIVE_BETTER — SF's rendered
  layer is largely faithful, including faithfully rendering the
  Laneige loss and the reverse-dupe mockery; both RENDERED_BETTER
  cells are reaction SERPs padded by brand shopping cards. Ledger:
  Laneige + Ole Henriksen + Huda/Covergirl (inverted direction)
  finding-grade; 7 named cheap dupes with Google-rendered floor math
  ($48/oz vs $6.73/oz); Sephora Collection own-brand dupe (79-pt);
  Vaseline/Aquaphor derm floor. Of the 11 authored return-leg probes,
  #1-10 remain NOT run; the 11th (`summer fridays vs ole henriksen lip
  treatment`) WAS run 2026-07-28 and produced the r01 capture folded in
  above. Floor math: only Trader Joe's carries a rendered figure
  ($48/oz vs $6.73/oz); the other six dupe names have no attached
  price. Durable record:
  `docs/research/serp_lane_competitor_scout_20260728/summer_fridays_phase2_native_return_v0.md`
  (staging source: `..\forseti-sf-phase2-native-return-20260728\`).

## Supersessions

- 2026-07-27: F13, F14 withdrawn (see cells). "~100/day cap" withdrawn
  same-day (F2). Protocol v1.2 + recipe v2.0 remain as evidence records;
  this file is the living surface.
- 2026-07-28: Method rule 5 ("Preserve raw DOM") retired and replaced by
  rule 6 (content retention default, forward-only re-extraction). Gate
  evidence: `parity_gate_google_serp_v0.json` (this folder). Existing raw
  stores are NOT deleted by this change — historical cleanup is a separate
  owner decision. Extractor v2 is now ported into the repo as
  `forseti-harness/source_capture/google_serp_content.py`; `bin/extract_serp_v2.py`
  remains the reference the port was proved against, not a second
  implementation to maintain in parallel.
- 2026-07-29 (wave 1, full bank 986/986): **F17 WITHDRAWN** — `vs {rival}`
  leads the question axis only; it does not reach the social top ten.
  F4 revised 0.889 → 0.782 → **0.821** at n=33 (the intermediate
  "wide margin withdrawn" call came from a cross-stratum blend and is
  itself withdrawn). F6 re-judged: revision 1's "weakened" was a
  coverage artifact of an issue-light 888. F5, F7, F12, F15, F16, F18,
  F19, F20, F21 held with revised numbers; F12 and F15 promoted
  lead → active. **F22 opened** (video-card content differs by platform).
  Evidence: `fullbank_analysis_findings_v0.md` rev 2.
- 2026-07-29 (wave 2, 572/572): **F23 and F24 opened** — naming the
  platform IS the door (TT 17.2 / IG 13.5 / YT 11.9 cards per probe vs
  reddit 7.7), and the SERP noise floor is measured (0.863 same-run,
  0.809 cross-day question agreement). F6 tournament-ranked:
  `made_it_worse` and `bad_for_you` enter the board, **`complaints` and
  `regret` cut**. F8 revised at n=60 (4h decay 0.86, not the panel's
  0.71). F2 sharpened, F2b opened.
- 2026-07-30: **F2c opened** (trailing load separates blocks, rate does
  not — 1714 pooled events). F2b's own consumer-audit claim WITHDRAWN
  (asserted a fleet-wide re-probe risk from a marker grep; reading the
  block branches showed every other runner already stops dead).
  **F11 unstaled** — it sat at `lead` with panel-era evidence while the
  findings note had re-judged it; now active at n=28/29, and its
  "steadier" half is withdrawn because F24 measured stability directly.
  **F13's revisit trigger fired and its withdrawal turned positive** —
  maturity does not scale question-layer trust; the ordering is inverted
  and inside the noise floor. **F25 opened**, homing a claim that arrived
  from the concurrent lane without a cell: the vs/dupe/alternatives trio
  does NOT cannibalise (pairwise overlap 0.096 vs 0.092 baseline); the
  0.749 that prompted it is the real P9-design figure quoted without its
  design.
- 2026-07-30 (boards v2.2): **F23's board consequence WITHDRAWN one day
  after opening.** Platform-door card volume converts on neither
  competitor harvest (18 suffix-only ledger entries, 0 candidate-rung)
  nor creator quality (1.5% clear the 2+-subject bar vs 4.3% for intent
  probes), and ordinary probes already surface these platforms for 34–44
  of 45 subjects. Default board 11 → 8; `{s} tiktok` becomes conditional,
  `{s} youtube` and `{s} instagram` are cut. Root error recorded in the
  cell: a volume metric read as a value metric without a conversion test.
- 2026-07-30 (cross-lane): PR #1383 landed 20+ owner-ratified rulings on
  this folder from a concurrent lane after #1384 merged. Reconciled:
  the creator layer now emits the spec's ratified `grid_capture` shape
  rather than a parallel feed; social engagement figures carry
  `UNBASELINED`; the phase-1 handoff return contract carries the tag and
  the URL-rot rule. Cause fixed at source — **F-number allocation is now
  stated to live in this file only**, and the spec's restated figures
  were replaced by pointers rather than policed by a new sync step.
