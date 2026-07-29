# Megadogfood Queue Completion — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Complete the analysis and capture queue gated behind the
  100-subject megadogfood bank run (COMPLETE 2026-07-29: 1127/1127
  ok, all blocks recovered by retry). Staged: the Channel-0 emitter
  repair runs FIRST (owner order, 2026-07-29) because the repaired
  harvest feeds most downstream stages. Receiver: the full-bank
  executor lane (branch codex/serp-lane-competitor-scout-20260728),
  which owns the analysis store, the emitter, and its tests.
use_when:
  - The owner dispatches queue completion (2026-07-29).
stale_if:
  - The stages below have returned and their results are recorded in
    the lane ledger.
  - The bank store layout or extractor version changes materially.
authority_boundary: retrieval_only
next_source: serp_lane_v0.md (lane ledger, executor branch);
  competitor_ledger_spec_v0.md, complaints_axis_v0.md,
  delight_axis_v0.md (reading doctrine, branch
  claude/serp-lane-phase2-native-return-840d51 until converged);
  the three pointed handoffs in stages 3-4.
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging - the executor lane's analysis folders under
    C:\tmp and its own branch for lane-ledger/findings updates; no
    edits to the reading-doctrine docs (they live on the other
    branch until convergence).
  input_prompt_source: docs/prompts/handoffs/megadogfood_queue_completion_handoff_v0.md
  edit_permission: docs-write plus the bounded stage-0 code scope
    below; no runner, spine, or overlay edits outside it.
  runtime_authorization: >
    Stage 0 carries explicit bounded implementation authorization
    (owner, 2026-07-29) for exactly two files:
    forseti-harness/runners/serp_competitor_ledger_emitter.py and
    forseti-harness/tests/unit/test_serp_competitor_ledger_emitter.py.
    Stages 5-6 carry capture authorization at the 15-20/hr band on
    the now-free Google stream; blocks are stop-signals; never
    CAPTCHA/proxy/IP-rotation. All other stages are local compute
    over the completed store - zero captures.
  targets: stage-0 files above; analysis staging; executor-branch
    lane docs. Nothing else.
  reviews: findings-first per stage; stage 0 additionally runs its
    unit test - a SKIP is not a PASS.
```

## Stage 0 — Channel-0 emitter repair (FIRST; owner order)

Bounded scope: the three adjudicated parse classes plus one test
case, in the emitter + its unit test only.
1. Compound collapse: name+context compounds fold to the parent
   entity ("Vaseline for baby" -> "Vaseline"), re-uniting split
   recurrence counts.
2. Comma-list recall: comma-separated list titles currently produce
   zero entries in 70 of 93 observed cases - parse them (recall
   recovery, new entries).
3. CONTEXT_GENERIC leak: the beauty-centric context filter admits
   condition phrases ("Irritated Skin") as names - fail closed.
4. Regression case: possessive-apostrophe brand tokens ("Paula's
   Choice") in subject matching.
Then re-run the Channel-0 harvest over the complete bank and report
the before/after: usable ratio (baseline 31.5%, adjudicated ceiling
~65% incl. self_variant typing) and absolute usable-entry count
(baseline ~146). Counts only; the 111-candidate hand adjudication is
the scoring reference. self_variant typing per the ratified type
(same-brand token heuristic is acceptable; hand-flag residue).

## Stage 1 — store completion

Delta pass over the 10 formerly-never-started beauty_issue subjects
(captured in the bank tail): extend every 88-subject analysis to
98/98 and re-state any cell whose number moves. Close F22's 5-subject
base if the delta admits more deep-set subjects. Tune the candidate
threshold (2+ queries) and stale window (2 passes) empirically
against the repaired stage-0 harvest (owner folded this here,
2026-07-29) - propose, do not silently change.

## Stage 2 — the two untouched analyses

Wave-2 covered neither (verified against the findings note,
2026-07-29):
1. Position-drift test: dupe-economy position statements across all
   subjects; drift or two-positions-at-once is a headline finding
   (evidence base to date n=3: T28 dupe-side, SF anchor-side + drift
   specimen, BR540 anchor-side).
2. J3 split-render/skew tiers: per-surface ALIGNED /
   RENDERED_BETTER / NATIVE_BETTER at bank scale, where a paired
   native side exists; name the unpaired remainder honestly.

## Stage 3 — the two calibration handoffs (existing, by pointer)

1. Full complaint-axis calibration per
   docs/prompts/handoffs/complaint_axis_vs_outcome_calibration_handoff_v0.md
   (the four bound rubric rules; pilot rates 5/8 and 7/9 are the
   frozen priors).
2. Full delight re-score per the AMENDED
   docs/prompts/handoffs/axis_ownership_delight_calibration_handoff_v0.md
   (commit 9075822f rules: exact-SKU, no-axis-joining, outcome-free
   pass-P intake) PLUS the doctrine ratified since: choice-statement
   bar, engagement + post-as-comment, ENGAGEMENT-THIN both sides.

## Stage 4 — weighting calibration (existing, by pointer)

Part B of
docs/prompts/handoffs/evidence_reading_weighting_calibration_handoff_v0.md
- dispatches only AFTER stage 3 returns (it consumes those outcome
sets). Five pre-registered questions; amendments return as proposals
for owner ruling, never installs.

## Stage 5 — ledger-riding outputs

On the repaired harvest + stage-3 outputs: the axis-owner /
vacancy table at full width (currently zero strict owners) and the
clarification-demand column (free by-product of posture typing).

## Stage 6 — capture-side (Google stream now free)

At band cadence, blocks-are-stop-signals: (1) the merged vs+J5
queue generated from the repaired stage-0 harvest per the spec's
queue rule (this settles the F4/F17 thin-subject problem); (2) the
BR540 unnamed-equivalence return-leg probe (the 309-pt post's
unnamed rivals; evidence:
C:\tmp\forseti-axis-delight-calibration-20260728\second_leg_native\).

## Return contract

Per stage: what ran, the numbers with their basis, what changed in
the lane ledger, defects found, and what is held for owner ruling.
Stage 0 additionally returns the before/after emitter comparison and
test results. Standing non-claims throughout: counts of observed
cards only; pilot rates are priors, not truths; no prevalence/share;
US-parameterized is not physically US-local.
