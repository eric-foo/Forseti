# Complaint-Axis → Head-to-Head Outcome Calibration — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded analysis commission to test and calibrate the hypothesis that a
  subject's top community complaint axes predict which rival wins its
  head-to-head comparisons (and on what axis), using the megadogfood
  SERP archive - a blind two-pass backtest with a pre-registered
  prediction protocol, run as a pilot on already-complete subjects now
  and extended to the full bank at run completion.
use_when:
  - The owner dispatches the calibration decision (2026-07-28).
stale_if:
  - The megadogfood store layout or extractor version changes materially.
  - Three additional live cases contradict the hypothesis before the
    backtest runs (re-scope rather than calibrate).
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging - a calibration work folder under C:\tmp (alongside
    the megadogfood store); repo docs only if the owner later routes a
    findings snapshot.
  input_prompt_source: docs/prompts/handoffs/complaint_axis_vs_outcome_calibration_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    NONE NEEDED - this commission is pure local compute over
    already-captured extractions. Zero new captures on any host. If a
    check seems to need a fresh capture, record it as an open probe for
    the SERP lane's return-leg queue instead.
  targets: the staging calibration folder only; no code, spine, or
    overlay edits.
  branch: no repo writes by default.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** find out whether "who beats you" is predictable from "what your
customers complain about" — and if so, how reliably and under what
conditions — so the claim can be sold with a measured hit-rate instead
of anecdotes.
**Done looks like:** a per-subject table (predicted winner + predicted
axis vs observed comparison-surface verdict), an overall hit-rate, the
counterexample list with a reason class per miss, and a stated verdict
on the price-tier boundary condition. This is the executor target and a
review axis-to-attack, not a review pass bar.

## Standing evidence (why this is worth calibrating; n=3 live cases)

1. Tower 28: top complaint axes shade range + crease predictability;
   Haus Labs wins the captured or-thread citing color variety (35-pt)
   and "won't crease" (16-pt).
   (`forseti-tower28-scout-20260727\tower28_scout_trial_findings_v0.md`)
2. Summer Fridays vs Laneige: top complaint axis wear-time; Laneige
   wins 17-pt/8-pt explicitly on "lasts longer".
   (`forseti-sf-phase2-native-return-20260728\`)
3. Summer Fridays vs Ole Henriksen: same axis; OH wins 7-pt "Ole 100%",
   losses cited as "too thin, doesn't last long", "does absolutely
   nothing to moisturize". (same folder, `return_leg\r01_composition.json`)

## Required reads (pointer-first)

1. `C:\tmp\forseti-serp-lane\competitor_ledger_spec_v0.md` — types,
   ladder, J-lever definitions, standing non-claims.
2. `C:\tmp\forseti-serp-lane\serp_lane_v0.md` — method rules
   (pre-registration rule 1; order-independence rule 3), findings F4-F21.
3. `C:\tmp\forseti-serp-megadogfood-20260727\` — query bank (shape
   labels per query), run ledger (which subjects are complete),
   extraction store, `bin\extract_serp_v2.py` provenance.

## Method

1. **Subject eligibility.** From the run ledger, list subjects whose
   captures are COMPLETE (subject-clustered scheduling means early
   subjects finish before the bank does) and that have BOTH (a)
   complaint-bearing shapes (complaints / not working / side effects /
   reddit) and (b) comparison-bearing shapes (vs / alternatives / dupe)
   captured. Pilot = all such subjects available today; full pass =
   re-run at bank completion (~2026-07-30).
2. **Blind pass A - complaint axes.** For each subject, derive the
   ranked complaint-axis list ONLY from complaint-shape extractions
   (titles, PAA, rendered snippets). Do not open comparison-shape
   extractions in this pass. Record a predicted winning axis and, where
   a rival is visible on non-comparison surfaces, a predicted winner.
   Freeze pass-A output (hash it) before pass B.
3. **Blind pass B - comparison verdicts.** Independently, read ONLY
   comparison-shape extractions: which rival dominates the rendered
   comparison surface, and what axis does the rendered language cite?
   (SERP-rendered verdicts are a noisier stand-in for native thread
   verdicts - carry this as a stated limitation, not a hidden one.)
4. **Match and score.** Axis hit = pass-B's cited winning axis appears
   in pass-A's top-2 complaint axes. Winner hit = predicted winner
   matches pass-B's dominant rival. Report hit-rates separately; never
   collapse them into one number.
5. **Counterexample autopsy.** Every miss gets one reason class:
   value-exit (equivalence claim x price gap - originally registered as
   "cross-price-tier exit"; pilot 2026-07-28 refined it: the
   equivalence claim, not cheapness, is load-bearing - a bare
   cheaper-mention without an equivalence claim produced no dominant
   rival), delight-axis (positive preference invisible to complaint
   surfaces), axis-not-complained-about (other),
   no-dominant-rival, surface-too-thin. The value-exit boundary is the
   pre-registered secondary hypothesis - score it explicitly, and
   record whether each value-exit carries an explicit equivalence claim.
6. **Strength read (if axis hit-rate > chance).** Test whether BIGGER
   complaint dominance predicts MORE decisive comparison verdicts
   (vote/row margins), per lane method rule 2 (within-subject
   comparability only).

## Scoring rubric (installed 2026-07-28 after two-run pilot reconciliation)

Two independent pilot executions replicated the headline direction but
diverged on 4 of 9 per-subject scores, all from scoring judgment
(reconciliation: `C:\tmp\forseti-calibration-pilot-20260728\pilot_reconciliation_v0.md`).
The full pass binds these four rules:

1. Score editorial-rendered and community-rendered comparison verdicts
   SEPARATELY; never merge them into one dominant rival (the Breville
   specimen: editorial layer votes a value-exit clone, community layer
   votes fix-the-complaint — same surface, opposite scores).
2. Pre-register the axis vocabulary per category before pass A (or run
   dual scorers with adjudication limited to disagreements).
3. Dominant-rival threshold: a rival must be named on 2+ independent
   rows or carry an explicit switching/preference statement; below
   that, verdict is `none`, never a weak single quote.
4. Winner-hit is two metrics: exact-name match, and the softer
   "predicted winner is an occupant of the winning axis" (multiple
   products can co-own an axis: CeraVe AND Vaseline on lanolin-free).

## Blindness discipline

Pass A and pass B must not share working notes. Single-agent execution
runs pass A for ALL subjects, freezes and hashes the output, then runs
pass B; two-agent execution is cleaner if available. The freeze
timestamp and hash go in the return.

## Return contract (one line per field; `unknown` if absent)

- `subjects_scored`: pilot count now / full count at bank completion.
- `axis_hit_rate`: with numerator/denominator, pilot and full.
- `winner_hit_rate`: same shape.
- `counterexamples`: per miss - subject, predicted, observed, reason class.
- `price_tier_verdict`: holds / breaks / undetermined, with cases.
- `strength_read`: correlation direction or `not_run` with reason.
- `freeze_evidence`: pass-A hash + timestamp.
- `open_probes`: native-capture candidates the SERP archive could not
  settle (routed to the SERP lane's return-leg queue, not captured here).

Standing non-claims: counts of observed cards only; US-parameterized is
not physically US-local; SERP-rendered verdicts are not composition
evidence - the backtest calibrates a SERP-level signal and says so.
