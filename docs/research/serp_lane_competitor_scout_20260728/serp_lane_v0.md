# SERP Lane v0 — living state — updated 2026-07-27

The single current surface for the Google SERP capture lane. Detailed
evidence records stay in their run folders; THIS file owns current truth.
When a finding changes: flip its cell's Status, add one line under
Supersessions, point Evidence at the new source. Do not fork this file.

Staging location (owner decision 2026-07-27): C:\tmp, not the repo. Routing
into the repo capture toolbox happens via the proper lane when the owner
calls it.

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

**F1. Safe sustained rate is 15–20/hour; blocks at 28–40/hour.** active.
Evidence: egress reconstruction + 99 consecutive clean captures at
13–18/hr (`megadogfood analysis/egress_budget_finding_v0.md`, recipe §1).
Owner set operating band 15–20/hr. Trigger: any block at ≤20/hr → drop
band, re-measure; 3 clean days at 20/hr → raise floor.

**F2. No daily cap observed (~185/day reached clean).** active, thin.
Evidence: same reconstruction; note an earlier ~100/day claim was
withdrawn same-day as contradicted by our own run. Trigger: a block that
correlates with cumulative volume rather than rate.

**F3. Once flagged, recovery is slow (>75 min); prevention beats reaction.**
active. Evidence: 75-min cooldown failed to clear the 07-26 flag.
Trigger: a measured flag-decay time from any future block.

**F4. `X vs {rival}` is the highest-value shape (~0.90 unique share).**
active. Evidence: order-independent unique-contribution analysis
(`analysis/unique_contribution.json`), 6-subject panel. Trigger: full-bank
re-run of the same analysis at n≈100 subjects (in progress, ETA 2026-07-30).

**F5. The review family (`review`/`reviews`/`honest review`/`worth it`)
is ~one probe of information, not four.** active. Evidence: unique shares
0.34–0.40, mutual duplication in panel. Consequence: boards carry ONE
review-family probe. Trigger: same as F4.

**F6. Pain shapes (`side effects`, `not working`, `how to fix`) carry high
exclusive yield (0.63–0.71).** active. Evidence: panel unique-contribution.
Trigger: same as F4.

**F7. Efficient frontier ≈ 6 probes/subject (80% of domains in ~4 shapes,
80% of questions in ~6–7).** active. Evidence: greedy set-cover per panel
subject. Consequence: default boards below. Trigger: full-bank set-cover
at n≈100 subjects.

**F8. Cluster a subject's probes into one session.** active. Evidence:
same-hour twins ~95% question-layer agreement (n=3) vs ~71% at 4h apart
(n=6). Consequence: banks are subject-clustered, never day-spread
round-robin. Trigger: larger twin sample separating hour/day scales.

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

**F11. Issue-led queries are steadier and richer than brand-led.** lead.
Evidence: issue twins 85–100% question overlap; issue shapes high unique
share — but small n. Trigger: full-bank issue strata results.

**F12. Mediation concentration is a category property; track outlets.**
lead. Evidence: livethatglow.com anchoring Rhode AND Laneige;
recurring-AIO-citation bar (2+ independent queries) marks a mediator for
native follow-through. Trigger: full-bank mediator frequency table.

**F13. Maturity-scaled question-layer trust.** WITHDRAWN 2026-07-27.
Was protocol v1.2 rule 3. Failed direct replication (Byoma 41% vs 100%
same-hour, same entity, same instrument). Replacement: twin-capture any
claim-bearing query regardless of entity age. Trigger to revisit: ≥3 twin
pairs per entity per maturity class.

**F14. Quoted-operator AIO suppression.** WITHDRAWN 2026-07-27 (ruleset
dogfood: identical AIOs with and without quotes, both entities).

**F15. Contrarian-titled community anchors are rare and precious.** lead.
Evidence: 0 in 8 non-SF natural queries; the SF anchor is the exception.
Consequence: title-vs-AIO polarity contradiction = top native-follow-through
trigger. Trigger: full-bank frequency count.

### Social-SEO axis (the lane's original purpose: SERP -> social doors)

**F16. The social axis ranks shapes DIFFERENTLY than the question axis —
boards must mix by goal.** active. Evidence: 136-cell social-surface
analysis (`analysis/social_surface_analysis.json`). Question-rich shapes
(`what causes`, `bare`, `is X normal`) are social-POOR (0.07–0.17 social
share); a board optimized purely for questions surfaces almost no native
content. Trigger: full-bank re-run at n≈100 subjects.

**F17. `X vs {rival}` is the universal door — #1 on BOTH axes.** active.
Evidence: 0.90 unique question share AND top true-social yield (beauty:
0.60 social share, 8.3 video rows, 4.2 TikTok + 3.0 IG cards per SERP).
Comparison intent is where Google routes short-video carousels. Trigger:
full-bank re-run.

**F18. Platform doors are shape-specific.** active, thin. Evidence
(beauty): TikTok surfaces on `vs` (4.2), `side effects` (2.0), `dupe`
(1.75), `review` (1.75); Instagram on `worth it` (4.0), `vs` (3.0),
`dupe` (2.5), `before and after` (1.8, its only strong door, 0 YT);
YouTube broadly on review-family and `dupe`; `X reddit` is purely the
community door (8.8 reddit cards, ~0 video). Consequence: pick the probe
by which platform's creators you need. Trigger: full-bank per-platform
table.

**F19. A recurring creator layer mediates across subjects.** active.
Evidence: 15+ sources on 2+ subjects each in 136 cells — skin-derm
YouTube (Dr. Jenny Liu, Dr. Daniel Sugai, Doctorly, Cassandra Bankson,
James Welsh) recurring across brands AND issues; parallel niche layers in
other verticals (Tom's Coffee Corner across both coffee subjects).
Consequence: the 2+-subject recurrence bar auto-generates the native
follow-through candidate list, extending F12 from outlets to creators.
Trigger: full-bank recurrence table (expect the list to grow, not shrink).

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
Balm). Trigger: full-bank ledger; owner typing-vocabulary review
(incl. self_variant); first live cycle running the pass.

**F21. The recurring creator layer splits into two kinds.** active, thin.
Evidence (n=13 recurring): 9 brand-recurring niche reviewers (comparison
venues within a category: James Welsh across Olaplex+Rhode) and 4
professional/derm creators bridging problem-space and brand-space
(Dr. Sugai across CeraVe + damaged skin barrier). None recurred on
problems alone. Consequence: cross-scope professionals are the priority
native-follow-through targets — they mediate the problem->product journey
that is the Understanding-phase entry point. Trigger: full-bank
recurrence table re-classification.

## Current default boards (from F4–F8, F16–F18)

Product subject (6 probes, one session) — covers both axes:
`{s} review` · `{s} vs {rival}` · `{s} side effects` (or `not working`) ·
`{s} reddit` · `{s} dupe` (or `alternatives`) · `is {s} worth it`
Axis note: `vs`/`dupe`/`worth it` carry the TikTok/IG door, `review` the
YouTube door, `reddit` the community door — the board is social-complete
as-is. Swap in `{s} before and after` when Instagram specifically matters.

Issue subject (6 probes, one session) — question-rich but social-poor
(F16): `{i}` · `what causes {i}` · `how to fix {i}` ·
`best products for {i}` · `{i} reddit` · `{i} before and after`
When an issue needs its creator layer, add ONE product-side social probe
(`vs` or `dupe` on the issue's leading product) rather than more issue
phrasings.

Twin-capture the probe whose composition will bear a claim. At 15–20/hr:
~2.5 subjects/hour, ~16+ subjects/working day. Creator recurrence (F19)
accrues automatically; review the 2+-subject list each analysis pass for
native follow-through.

## Instruments (current versions)

- Capture: `run_source_capture_cloakbrowser_packet.py`, `--output` packet
  mode (lake-free, ~3–5s/capture). Lake mode only when doctrine requires.
- Orchestrator: `megadogfood-20260727/bin/megadogfood_orchestrator.py` —
  ledger-checkpointed, resume-safe, absolute deadline, persisted 3-strike
  block policy, rest breaks.
- Extractor: `extract_serp_v2.py` (PAA-exit fix, tile grouping,
  title/source pairing). v1 rankings of organic rows are known-degraded;
  re-extract rather than trust old extractions.
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
5. Preserve raw DOM; version extractors; re-extraction must always be
   possible.

## In progress

- Full-bank run: 986 jobs, subject-clustered core-first, ~15.7/hr, started
  2026-07-27 15:32, ETA ~2026-07-30. Refreshes F4–F8, F11, F12, F15 at
  n≈100 subjects. Status: `megadogfood-20260727/STATUS.md` (worker-tended).
- Reddit capture queue (13 threads) awaits the Reddit lane; harness
  access-gate fix sits uncommitted on this branch.

## Supersessions

- 2026-07-27: F13, F14 withdrawn (see cells). "~100/day cap" withdrawn
  same-day (F2). Protocol v1.2 + recipe v2.0 remain as evidence records;
  this file is the living surface.
