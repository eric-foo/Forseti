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

**F2b. A block is not a rate signal, and the ladder currently treats it
as one.** lead (new 2026-07-29). Evidence: after the 07-03 block the
orchestrator stepped 60 → 55 → 50 → 45 → 40 → 36 → 32.7/hr, and **every
single step-down was followed by another block on the first capture
after the pause** — six blocks, six rungs, zero clean captures between.
Rate reduction did nothing because the constraint was a live flag, and a
flagged route rejects the first request regardless of how slowly it
arrives. An 82-minute episode cooldown also failed to clear it.
Consequence: the block handler conflates two failure modes and spends
rungs on the wrong one. The correct response to a block is IDLE TIME
(F3), not a slower cadence; the rung step-down should be reserved for
blocks that follow a rung increase. Trigger: implement a split response
and observe whether flags clear faster, or a counter-case where stepping
down alone clears a block.

**F3. Once flagged, recovery is slow — bracketed at >26 min and ≤3h25m;
prevention beats reaction.** active — SHARPENED 2026-07-29. Evidence:
75-min cooldown failed to clear the 07-26 flag; on 07-28 waits of ~12 and
~26 min each drew a block on the first capture after the gap; on 07-28/29
a ~3h25m idle cleared it completely (95/95 clean at 45/hr, then 3 clean
re-probes of previously-blocked jobs). This is the lane's first positive
decay observation — before it, every data point was a failure to clear.
The bracket is wide because nothing between 26 min and 3h25m was tested,
and the operating rule stays "idle for hours, not minutes". Non-claim:
the clean resume evidences decay, not that 45/hr is a safe rate —
escalation was frozen throughout. Trigger: a block after ≥4h idle
(would break the upper bound), or a clean first capture under 1h (would
tighten the lower).

**F4. `X vs {rival}` is the highest-value shape (~0.78 unique share).**
active — RE-JUDGED 2026-07-29 COMPLETE bank: HELD, revised down from
0.889 (panel, n=3) to **0.782**. **The "by a wide margin" framing is
withdrawn**: `not_working` 0.651 and `alternatives`/`best_products` 0.626
sit close behind. Evidence: `fullbank_analysis_findings_v0.md`;
`analysis/fullbank_shape_value.json`. Trigger: any shape overtaking it on
the question axis, or the 11-shape fixed design growing past n=12.

**F5. The review family (`review`/`reviews`/`honest review`/`worth it`)
is ~one probe of information, not four.** active — RE-JUDGED 2026-07-29:
HELD and tightened. `review` 0.377, `worth_it` 0.376, `honest_review`
0.368, `reviews_plural` 0.323. Consequence: boards carry ONE
review-family probe. Trigger: any member separating by >0.15 from the
cluster.

**F6. Pain shapes carry elevated exclusive yield (~0.32–0.65).** active —
RE-JUDGED 2026-07-29 COMPLETE bank: HELD. `side_effects` **0.586**,
`not_working` **0.651**, `complaints` **0.322**. The 2026-07-28
"weakened" call was largely a coverage artifact of an issue-light 888 —
`not_working` recovered to panel level and is now the #2 shape overall.
`complaints` is the weak member and is the one to drop from boards.
Evidence: `fullbank_analysis_findings_v0.md`. Trigger: `complaints`
rising above 0.45 in any stratum, or `not_working` falling below 0.55.

**F7. Efficient frontier ≈ 6 probes/subject (80% of domains in ~4 shapes,
80% of questions in ~6–7).** active — RE-JUDGED 2026-07-29 COMPLETE bank:
HELD, best-supported cell in the ledger. Across all 98 complete subjects,
80% of questions at **6.36 shapes**, 80% of domains at **3.92**; issue
designs 4.83–5.36, product designs 6.21–7.42. Consequence: default boards
below. Trigger: a stratum needing >9 shapes for 80% of questions.

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
active — RE-JUDGED 2026-07-29 COMPLETE bank: HELD, promoted lead →
active on its own trigger. The panel specimen (livethatglow.com anchoring
Rhode AND Laneige) is far off the low end: **livethatglow.com spans 11
subjects**; 113 creators recur across 2+ subjects, led by
`youtube:Dr Dray` at 11. Recurring-AIO-citation bar (2+ independent
queries) marks a mediator for native follow-through. Evidence:
`analysis/fullbank_social_and_axes.json`. Trigger: the top mediator
falling below 5 subjects in a later pass.

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
Routing (owner-decided 2026-07-29): the layer feeds the TikTok
discovery-frontier funnel as CANDIDATE INPUT, never direct registry
insertion — `serp_recurring_creator_feed_v0.json` (this folder) carries
all 113 with the why (subjects, counts, scope) and recovered TikTok
handles (20/24). The frontier's scan-receipt register and owner
disposition batches are NOT written by this lane: a SERP-recurrence
observation is not a TikTok scan, and dispositions are owner acts.
YouTube (73) and Instagram (16) have no admission path — typed gap.

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
- **Wave 2 PARTIAL — flagged 2026-07-29 07:03 at 290/572.** Ran clean
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
