# SERP Lane Full-Bank Analysis — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded commission to re-run the SERP lane's analysis suite over the
  full-bank capture store and re-judge the findings-ledger cells whose
  change-trigger names a full-bank re-run. Analysis only: no captures,
  no emitter edits.
use_when:
  - The megadogfood full-bank capture run has enough coverage to re-judge
    lane cells previously decided on a 6-subject panel.
stale_if:
  - The findings ledger is re-judged by a later analysis pass.
  - The emitter changes materially (its ledger output would need re-running).
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    docs/research/serp_lane_competitor_scout_20260728/ in the repo -- the lane
    is authored in-repo (authority inverted 2026-07-28). Analysis JSON outputs
    stay on the operator drive with their store.
  input_prompt_source: docs/prompts/handoffs/serp_lane_fullbank_analysis_execution_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    Local compute over an existing capture store only. NO captures of any
    kind -- not Google, not Reddit, not retail. The capture route is
    flag-suspended as of 2026-07-28; this work is deliberately independent
    of it. If you believe a capture is needed, stop and say so instead.
  targets: >
    serp_lane_v0.md (findings ledger cells) plus one new findings note in
    the routed folder. No emitter, runner, or spine edits.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** most of the lane's findings were decided on a 6-subject panel.
Re-decide them against the full capture store, and say plainly which ones
survived, which changed, and which are still too thin to call.
**Done looks like:** every findings cell whose trigger names a full-bank
re-run carries an updated status, the number it now rests on, and a one-line
reason; anything that moved has its old and new values side by side. This is
the executor target and a review axis-to-attack, not a review pass bar.

## Inputs (all local; nothing to capture)

- Store: `C:\tmp\forseti-serp-megadogfood-20260727\`
  - `extracted\` — 1036 extraction JSONs (as of 2026-07-28)
  - `run_ledger.jsonl` — per-job outcomes; `query_bank.json` — the 986-job bank
  - `analysis\` — the PRIOR results you are re-judging against, notably
    `unique_contribution.json`, `social_surface_analysis.json`,
    `panel_shape_analysis.json`, `saturation_curves.json`,
    `shape_value_table.json`, `competitor_ledger_v0.json`,
    `issue_question_graph.json`, `analysis_summary.md`
  - `bin\` — the analysis scripts: `analyze_megadogfood.py`,
    `unique_contribution.py`, `social_surface_analysis.py`,
    `creator_scope.py`, `panel_shape_analysis.py`, `coverage_check.py`,
    `twin_timing.py`, `show_twins.py`
- Competitor emitter, now canonical in-repo:
  `forseti-harness/runners/serp_competitor_ledger_emitter.py`, with its
  pinned-fixture suite at
  `forseti-harness/tests/unit/test_serp_competitor_ledger_emitter.py`.
  RUN THE FIXTURE SUITE FIRST; if it fails, stop and report — a broken
  emitter invalidates the ledger pass. A skip is not a pass.

## Required reads

1. `docs/research/serp_lane_competitor_scout_20260728/serp_lane_v0.md` —
   the findings ledger. It is the target of this work and the authority on
   each cell's current status, evidence, and change-trigger.
2. `docs/research/serp_lane_competitor_scout_20260728/README.md` — reading
   order and the standing non-claims.
3. `competitor_ledger_spec_v0.md` — types, promotion ladder, and the known
   emitter v0.2 defect queue, before you judge the ledger output.

## Coverage first — this is the load-bearing step

The run HALTED at 890 of 986 jobs (96 pending), so coverage is uneven and
the bank was captured subject-clustered. Before any cross-subject claim:

1. Compute per-subject capture completeness from `run_ledger.jsonl` against
   `query_bank.json`. Some subjects are likely complete; some may be missing
   entirely or partially.
2. Decide and STATE a coverage bar for cross-subject comparisons, and apply
   it consistently. A subject captured at 4 of 11 shapes is not comparable to
   one captured at 11 of 11 and must not silently enter a per-shape average.
3. Report the real n everywhere: "n=NN subjects at >=X shapes", never
   "n~100". The earlier plan assumed ~100 complete subjects; that is not what
   exists, and a claim written as though it were is the main way this pass
   could go wrong.
4. `extracted\` holds 1036 files, MORE than the 986-job bank, because it
   includes job_ids from earlier bank versions. Reconcile against the current
   bank rather than trusting the file count.

## Method

Run each analysis over the full store and compare to its panel-era result.
For every findings cell whose change-trigger names a full-bank re-run
(there are ~12; work from the ledger file itself, not from memory), decide:
**held / changed / still-thin / withdrawn**, with the new number beside the
old one. Cells to expect, by the analysis that decides them: shape-value and
unique-contribution cells (F4-F7), issue-strata (F11), mediator concentration
(F12), contrarian-anchor frequency (F15), the social-axis cells (F16-F19),
and the competitor-ledger cells (F20-F21). Verify that mapping against the
file; do not assume it.

Rules that keep this honest:

- A finding that gets WEAKER at higher n is the most valuable output here.
  Panel-era numbers came from 6 subjects and several are probably optimistic.
  Do not preserve a cell because it is load-bearing elsewhere; say it moved.
- Withdrawn cells stay in the file, marked, with the evidence that killed
  them. Never silently drop one.
- Do not fix the emitter. Known v0.2 defects (name+context compounds,
  beauty-centric context vocabulary, scout-mode subject bleed, comma-list
  names invisible to the pattern matcher) are REPORTED with their observed
  frequency at full-bank scale, so the owner can size the fix. Reporting how
  often each defect fires is the useful deliverable.
- Standing non-claims on every artifact: counts of observed cards only,
  never prevalence, volume, or share; US-parameterized is not physically
  US-local; raw capture data stays outside Git.

## Return contract (schema-bound; one line per field; `unknown` if absent)

- `coverage`: subjects at full shape coverage / partial / absent, and the
  bar you applied.
- `fixture_suite`: pass / fail / skipped, with the count.
- `cells_held`: cell ids with the number each now rests on.
- `cells_changed`: cell id, old value, new value, one-line cause.
- `cells_still_thin`: cell ids and what evidence would settle them.
- `emitter_defects`: each known defect with its observed frequency at scale.
- `new_observations`: anything the panel was too small to show.
- `artifacts`: the findings note path and the ledger cells edited.
