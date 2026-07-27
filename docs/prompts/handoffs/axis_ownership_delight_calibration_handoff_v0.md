# Axis Ownership + Delight-Axis Calibration — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded analysis commission with two joined jobs over the megadogfood
  archive: (1) calibrate the DELIGHT-AXIS mirror hypothesis - that a
  rival's praised axes (mined from the rival's own surfaces) predict
  comparison outcomes complaint axes cannot - and measure the combined
  complaint+praise model against comparison verdicts; (2) compute the
  first systematic AXIS-OWNER table (same rival winning the same axis
  across 2+ subjects) with occupancy (vacant/occupied) per subject
  top-axis.
use_when:
  - The owner dispatches axis-ownership/delight calibration; pilot-now
    on complete subjects, full pass at bank completion (~2026-07-30).
stale_if:
  - The complaint-axis calibration handoff's scoring rubric changes.
  - The axis-ownership doc or spec axis reads are superseded.
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging - a work folder under C:\tmp alongside the
    calibration pilot folder; repo docs only if the owner routes a
    snapshot.
  input_prompt_source: docs/prompts/handoffs/axis_ownership_delight_calibration_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    NONE NEEDED - pure local compute over already-captured extractions
    and thread packets. Zero new captures on any host; unresolvable
    checks become open probes for the SERP lane return-leg queue.
  targets: staging work folder only; no code, spine, or overlay edits.
  branch: no repo writes by default.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** find out whether mining a rival's praise fills the delight
blind spot the complaint-axis pilot exposed, and name who currently
owns which axes across the bank — so "where you lose AND to whom the
axis belongs" becomes one measured deliverable.
**Done looks like:** a scored delight-prediction table for eligible
subject pairs, a combined-model hit-rate (complaint ∪ praise vs
complaint-only), an axis-owner table with per-axis occupants and
vacant-axis flags per subject, and the counterexample list. This is
the executor target and a review axis-to-attack, not a review pass
bar.

## Standing evidence (why; keep honest about n)

- Complaint-only calibration: 5/8 and 7/9 blind (two model families),
  raised further by native settlement; its two named blind spots are
  the VALUE exit and the DELIGHT axis
  (`C:\tmp\forseti-calibration-pilot-20260728\pilot_reconciliation_v0.md`,
  `native_settlement_v0.md`).
- Delight specimens (n=2): SKIN1004 lightweight/no-white-cast; OXO
  one-touch. Axis-owner concept + observed table:
  `C:\tmp\forseti-serp-lane\axis_ownership_v0.md`.

## Required reads (pointer-first)

1. `C:\tmp\forseti-serp-lane\competitor_ledger_spec_v0.md` — delight-
   axis read, axis-occupancy read, verdict-source typing, corroboration
   strength, standing non-claims.
2. `C:\tmp\forseti-serp-lane\axis_ownership_v0.md` — concept, kinds,
   detection bar, current table to extend/correct.
3. `docs/prompts/handoffs/complaint_axis_vs_outcome_calibration_handoff_v0.md`
   — the scoring rubric (4 bound rules) and blindness discipline; this
   commission inherits both wholesale.
4. `C:\tmp\forseti-serp-megadogfood-20260727\` — bank, ledger,
   extraction store.

## Method

1. **Pair eligibility.** From the bank, find subject pairs where BOTH
   sides are bank subjects with captures (e.g. Aquaphor AND Vaseline;
   the K-beauty set) plus single subjects whose promoted rivals have
   any owned surface in holdings. The rival's praise must be minable
   from the RIVAL's own non-comparison surfaces (its review-family /
   reddit captures) — that keeps the delight pass blind to the
   comparison surfaces being predicted.
2. **Pass P (praise, blind).** Per rival: rank its top praised axes
   from its own surfaces only; verbatim evidence + job_id cites.
   Freeze with hash alongside the complaint pass-A output.
3. **Combined prediction.** Per subject pair: predicted decisive axis
   set = subject's top-2 complaint axes ∪ rival's top-2 praised axes,
   each tagged with its source model.
4. **Score (inherit the 4-rule rubric).** Against comparison surfaces,
   editorial and community typed separately: complaint-only hit,
   praise-only hit, combined hit. The claim under test: combined >
   complaint-only, with praise catching specifically the delight-class
   misses.
5. **Axis-owner table.** Mechanical aggregation across ALL scored
   subjects: rival x axis x subjects-won/cited. Owner candidate at 2+
   subjects (spec bar). Per subject: top-2 complaint axes marked
   OCCUPIED (by whom) or VACANT. Type owners by kind
   (product-superiority / trust-floor / value / category-level).
6. **Counterexample autopsy** per the inherited reason classes, plus
   one new class this commission may emit: `praise-axis-not-decisive`
   (rival praised for X, comparison decided elsewhere).

## Blindness discipline

Inherited from the complaint-axis handoff: pass P must not read
comparison surfaces; freeze-and-hash before scoring; the scorer may be
controller-side (mechanical matching only). Category-known
hypothesis-generating pairs (Aquaphor/Vaseline was natively settled
2026-07-28) are scored but flagged `settled_prior` and excluded from
the headline rate.

## Return contract (one line per field; `unknown` if absent)

- `pairs_scored`: eligible pairs pilot / full.
- `complaint_only_hit_rate`, `praise_only_hit_rate`,
  `combined_hit_rate`: each with numerator/denominator.
- `delight_recovery`: of the complaint-model misses, how many the
  praise model caught.
- `axis_owner_table`: rival x axis x subject-count, kind-typed;
  owners (2+) listed first.
- `vacancy_map`: per subject, top-2 axes occupied/vacant.
- `counterexamples`: per miss, reason class.
- `freeze_evidence`: pass-P hash + timestamp.
- `open_probes`: native-capture candidates routed to the return-leg
  queue, never captured here.

Standing non-claims: counts of observed cards only; US-parameterized
is not physically US-local; SERP-rendered verdicts are not composition
evidence; ownership claims are recurrence counts, never market share.
