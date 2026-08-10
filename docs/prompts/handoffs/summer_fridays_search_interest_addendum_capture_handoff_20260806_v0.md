# Summer Fridays Search-Interest Addendum Capture Handoff — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission one bounded Google Trends addendum to the completed 2026-08-05
  Summer Fridays search-interest capture: (A) category-benchmark curves to
  separate brand decline from category decline, and (B) Shopping-property
  head-to-heads as a purchase-intent-leaning check on the web-search
  destination reads. One sitting, five term-set batches maximum, using the
  browser-route method banked from the 2026-08-05 run.
use_when:
  - Capturing the category-vs-brand trajectory read for the Summer Fridays Deliver target screen.
  - Testing whether the 2026-08-05 destination head-to-heads survive under Shopping-property search.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/handoffs/search_interest_browser_capture_refinement_handoff_20260806_v0.md
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md
  - docs/prompts/handoffs/summer_fridays_search_interest_capture_handoff_20260805_v0.md
stale_if:
  - Google materially changes Trends access, comparison limits, property filters, or export fields.
  - The Summer Fridays Deliver run this feeds is completed or re-commissioned with a different target screen.
```

**What this is for:** the Deliver target screen currently cannot tell whether
Summer Fridays' post-2024 attention decline is brand-specific or
category-wide, and whether the destination attention advantage survives when
search is filtered toward purchase intent.
**Done looks like:** a small addendum return plus machine-readable series
answering both, with the category decision rule below applied honestly, every
below-threshold row phrased exactly, and the 2026-08-05 artifacts untouched.

## Load Contract

- `packet_version`: `20260806_v0`
- `load_rule`: **confirm-don't-trust**. Confirm every named repo path and
  source surface before strict or actionable claims.
- output_mode: `file-write`
- `edit_permission`: `docs-write` for the exact return artifacts below; bounded
  external capture writes at the named raw root. Repository implementation or
  runtime code is read-only.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_search_interest_addendum_capture_handoff_20260806_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_return.md`
- `output_series`:
  `docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_series.json`
- `raw_root`: `C:\tmp\forseti-sf-search-interest-discovery-20260806\data`
- `workspace`: clean receiver-owned Forseti worktree; do not work in another
  active Summer Fridays lane.
- `dirty_state_allowance`: clean initially; only the two named return artifacts
  may become modified/untracked. Raw exports stay outside Git.
- `repo_map_decision`: not needed; exact prompt, output, and method paths are bound.

## Sourcing Authorization Boundary

This commission carries a **bounded owner authorization for exactly one
one-shot addendum pull** (owner instruction, 2026-08-06, this lane), scoped to
the Summer Fridays Deliver target screen. It does not authorize the standing
demand-durability series, a cadence, or any other subject. The search-interest
capture profile's limits-visibility obligations apply as in the 2026-08-05
commission.

## Method

Start from the banked browser-route method: the capture-parameter receipt and
rate-limit lessons in the 2026-08-05 return (§2, §9) and the sibling
refinement handoff in `open_next`. Do not re-learn the route. Freeze per batch:
property, geo, window, category filter, capture timestamps, and the anchor
term `summer fridays lip butter balm` where the batch includes it. If a new
method lesson emerges (especially Shopping-property endpoint behavior), record
it in the return's method section for the refinement lane to bank — this run
should leave the route smoother than it found it.

## Bounded Query Batches

Hard cap: **five term-set batches**, each pulled in at most two geos (US
primary; worldwide check only where named). If a batch cannot complete, return
`PARTIAL` with the cut list rather than silently dropping terms.

**Part A — category vs. brand (web search property):**

1. **Lip category:** `lip balm`, `lip mask`, `lip butter`, `lip oil`, anchor —
   5-year, US + worldwide check.
2. **Tint category:** `skin tint`, `tinted sunscreen`, `tinted moisturizer`,
   anchor — 5-year, US + worldwide check.

Expected and acceptable: category terms dwarf the anchor on the 0–100 scale.
The read is the **shape and direction of the category curves** (rising, flat,
or deflating 2024 → capture date), not their level against the anchor.

**Decision rule (state the verdict against it explicitly in the return):**
- SF brand curve declining while its category curve still rises or holds →
  brand-specific decline.
- Category curve deflating alongside the brand → category-wide decline; the
  prize itself is shrinking.
- Mixed or below-threshold → report as unresolved; do not force a verdict.

**Part B — purchase-leaning check (Shopping search property):**

3. **Lip head-to-head:** `summer fridays lip butter balm` (anchor), `laneige
   lip sleeping mask`, `rhode peptide lip treatment`, `aquaphor lip repair`,
   `lanolips` — 5-year, US.
4. **Tint head-to-head:** `summer fridays skin tint`, `ilia skin tint`, `saie
   slip tint`, `hourglass skin tint`, anchor — 5-year, US.

Expected complication, stated in advance: Shopping-property volume is far
lower than web search; many or most terms may fall below the reporting
threshold. A mostly-null result is a valid, reportable outcome — it bounds the
check as inconclusive; it is never stretched into a finding.

5. **Spare batch** — held for one confirming cut only if a Part A category
   curve materially demands it (e.g., a category term ambiguity). Unused is
   the default; record `unused` explicitly if so.

## Drift Guard

- All 2026-08-05 drift-guard rules apply verbatim: relative 0–100 index only;
  no sales, demand-size, prevalence, share, or population claims; below
  threshold uses exactly **"below the Google Trends reporting threshold under
  the recorded geo/window"**; record curves, never attribute motive; sealed
  Phase A corpus untouched.
- Cross-pull comparability: this addendum is a separate normalization from the
  2026-08-05 pull. Direct level comparison across pulls goes only through the
  shared anchor term and is labeled approximate; within-pull comparisons are
  the primary read.
- The 2026-08-05 artifacts are read-only; the addendum stands beside them in a
  new dated directory.

## Return Contract

The addendum return must include: (1) executive conclusion — the Part A
verdict against the decision rule and the Part B outcome (confirmed /
contradicted / inconclusive-below-threshold), three findings max; (2)
capture-parameter receipt per batch; (3) category trajectory read with yearly
and half-over-half means; (4) Shopping head-to-head table or its null ledger;
(5) threshold and null ledger; (6) failure/omission ledger including spare-batch
disposition; (7) method-lesson section for the refinement lane; (8) non-claims.
The series file mirrors the 2026-08-05 record shape (one record per term, geo,
window, property, batch, with threshold flags and raw-export sha256s) and adds
a `property` field; note this shape delta explicitly for the schema bootstrap.

## Validation And Stop Conditions

Before closeout: fresh-read both written artifacts; verify every series record
resolves to a retained raw export; recompute batch and term counts;
run `python -B .agents/hooks/header_index.py --strict`;
run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
run `git diff --check`. Report each as pass, fail, blocked, or not run. Stop
with the nearest explicit blocker if the method sources, the Trends surface,
or output writing cannot be verified.
