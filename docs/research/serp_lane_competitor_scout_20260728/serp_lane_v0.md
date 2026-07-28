# SERP Lane v0 — living state — updated 2026-07-28

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

**Full-bank re-judgment 2026-07-28** — cells carrying a full-bank trigger
were re-decided against 888 captures / 88 complete subjects; see
`fullbank_analysis_findings_v0.md` for coverage caveats and the full
cell-by-cell. Summary: F4, F5, F7, F11, F12, F16, F18, F19, F20, F21
HELD (several with revised numbers); **F6 weakened**; **F17's
universal-door claim withdrawn**; F15 promoted lead → active on its own
trigger. The run halted at 888/986, so this is not the n≈100
complete-subject pass the triggers anticipated — fixed-design comparisons
rest on n=5–21.

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

**F4. `X vs {rival}` is the highest-value shape (~0.81 unique share).**
active — RE-JUDGED 2026-07-28 full bank: HELD, number revised down from
0.889 (panel, n=3) to 0.812 (n=12, fixed 11-shape design). Still #1 by a
wide margin (next: `side_effects` 0.579, `dupe` 0.564). Evidence:
`fullbank_analysis_findings_v0.md`; `analysis/fullbank_fixed_design.json`.
Trigger: re-run once the 95 uncaptured jobs land (fixed-design n is only 12).

**F5. The review family (`review`/`reviews`/`honest review`/`worth it`)
is ~one probe of information, not four.** active. Evidence: unique shares
0.34–0.40, mutual duplication in panel. Consequence: boards carry ONE
review-family probe. Trigger: same as F4.

**F6. Pain shapes carry elevated exclusive yield (~0.27–0.58).** active —
RE-JUDGED 2026-07-28 full bank: CHANGED, weakened. `side_effects`
0.722→0.579, `not_working` 0.639→0.544, `complaints` 0.411→0.271. Still
above the review family, but the panel-era 0.63–0.71 band does not hold and
is withdrawn. Evidence: `fullbank_analysis_findings_v0.md`. Trigger: same
as F4.

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
boards must mix by goal.** active. Evidence: 136-cell social-surface
analysis (`analysis/social_surface_analysis.json`). Question-rich shapes
(`what causes`, `bare`, `is X normal`) are social-POOR (0.07–0.17 social
share); a board optimized purely for questions surfaces almost no native
content. Trigger: full-bank re-run at n≈100 subjects.

**F17. `X vs {rival}` leads the QUESTION axis only — the universal-door
claim is WITHDRAWN 2026-07-28.** Full bank: vs_rival is still #1 for
questions (0.812) but mid-pack on the social axis in beauty —
`alternatives` 0.475, `worth_it` 0.445, `dupe` 0.442, `vs_rival` 0.414,
with `reddit_suffix` 0.739 far above all. Panel-era vs_rival social
figures did not reproduce (0.60→0.414 social share, 8.3→3.61 video rows,
4.2→2.11 TikTok cards); `alternatives` now leads TikTok at 3.00.
Replacement: the question door is `vs_rival`, the community door is
`reddit_suffix`, and the video door is `alternatives`/`dupe`. Evidence:
`fullbank_analysis_findings_v0.md`. Trigger: re-run after the remaining
captures land.

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

- Full-bank run: **HALTED 2026-07-28 20:00 at 889/986 (97 pending)** —
  owner decision, resume later. Refreshes F4–F8, F11, F12, F15 at n≈100
  subjects when it completes; the analyses can also be re-run on the 889
  already captured if the remainder slips.
  **Why halted:** two blocks 14 minutes apart. The first was
  load-driven and self-inflicted — a restart to change cadence config
  began capturing 2.1 minutes after the previous burst instead of the
  scheduled 10, producing 41 captures in 30 minutes where the schedule
  allows ~32. The second landed on the FIRST capture after a ~26-minute
  gap at a rate two rungs lower, with zero successful captures between:
  that one is flag persistence, not a rate signal (consistent with F3,
  recovery >75 min). Continuing to probe every 14 minutes mostly
  re-confirms a flag, so all capture processes were stopped.
  **On resume:** the IP should sit idle for hours, not minutes. Then
  restart the orchestrator, which resumes from its ledger automatically;
  `rate_state.json` is pre-set to rung 0 (27.1/hr) frozen so it starts
  at the most-proven rate with no escalation. Earn a clean baseline of a
  few dozen captures before reading any rate as evidence, and do not
  unfreeze escalation until that baseline exists.
  **What the run established before the blocks:** a clean walk from 27.1
  to 60/hr sustained — 151 consecutive clean captures at 60/hr alone —
  and the observation that clean and blocked stretches were identical at
  10- and 20-minute windows and diverged only at 30 minutes (32 captures
  = 64/hr clean vs 41 = 82/hr blocked). Working hypothesis: the
  half-hour total is the discriminating variable, not the instantaneous
  spike. Cadence, evidence per rung, and the 72/hr-sustained (~77/hr
  peak-30min) rungs authored for the next attempt live in
  `forseti-harness/runners/serp_egress_cadence.py`.
- Queued behind the bank, both built, validated, and gated (no captures
  taken, processes stopped with the bank): the 10-brand scout dogfood
  (`C:\tmp\forseti-scout-dogfood10-20260728\`) and the 120-job beauty
  corpus extension (`C:\tmp\forseti-beauty-ext-20260728\`, 12 new
  subjects, pools into the megadogfood store via its own pooling
  script). Both gate on the bank writing a completion state, so neither
  can fire onto a flagged IP; both pay a full rest at chain hand-off.
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
