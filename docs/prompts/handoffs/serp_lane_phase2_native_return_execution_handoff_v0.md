# SERP Lane Phase 2 — Post-Fan-Out Targeted Return Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded runtime commission to execute phase 2 of the SERP-lane competitor
  cycle for a subject whose phase 1 (scout pass: seed -> harvest -> vs -> J5)
  and specialist fan-out are complete: consume the specialists' durable
  findings, derive targeted SERP probes, run the J5 delta on promotions,
  apply the fail-closed decision lifecycle, and consolidate the typed ledger
  plus unmet-value map.
use_when:
  - A company Understanding has a phase-1 ledger plus terminal CO1, CO2, and
    CO3 returns, and CO0 dispatches the post-fan-out targeted SERP return.
stale_if:
  - The competitor-ledger spec section this handoff points to is superseded
    (next expected supersession: the full-bank megadogfood re-judgment,
    ~2026-07-30).
  - The Phase-2 decision contract, lifecycle adapter, or owner egress band
    changes.
authority_boundary: retrieval_only
```

The filename retains `native_return` for stable routing. That wording is
legacy: current Phase 2 does not own native Reddit/community capture.
Historical native-return dogfoods remain accurate records of their revisions.

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging (subject work folder under C:\tmp, alongside the phase-1
    scout and specialist folders) for targeted SERP/J5 packets, lifecycle
    state, and findings notes; repo docs-write only to refresh the routed
    snapshot folder docs/research/serp_lane_competitor_scout_20260728/ in its
    lane PR when the owner routes.
  input_prompt_source: docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    This accepted handoff is the bounded runtime authorization (AGENTS.md):
    J5 price captures (1-2 URLs per promoted name) and evidence-targeted Google
    SERP probes for this subject only. Reddit/community capture belongs to CO3
    and is not authorized here. No other capture surfaces, no clicks, no proxy,
    no CAPTCHA interaction, no account state.
  targets: >
    operator staging folders for this subject; the routed snapshot folder
    above (refresh-only). No code, spine, or overlay edits.
  branch: the open SERP-lane routing branch/PR when snapshots are refreshed;
    otherwise no repo writes.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** turn the completed fan-out into the focused search return the seed
grammar could not have guessed: which newly surfaced names, claims,
contradictions, and unmet-value axes deserve one bounded SERP follow-up, and
what the consolidated competitor answer now supports.
**Done looks like:** every targeted query traces to a specialist finding; the
J5 delta covers every promoted name; the final ledger and unmet-value map cite
their source artifacts; automatic weak-signal validation is claimed once
through the lifecycle store; and the sealed decision receipt and provenance
make material blocks visible. This is the executor target and a review
axis-to-attack, not a review pass bar.

For `broad_consumer_brand_understanding_v4`, first hash-pin the provisional axis
inventory in the v5 depth ledger. Before this handoff, `CO3` must have run the
balanced brand-plus-axis, behavior/consequence/displacement, bounded
consumer-native product-name/shorthand without-brand, and condition/post-use
query families in that order. The without-brand family covers hero products by
default and admits a non-hero product only when already captured evidence
exposes a material question; it remains recorded under the historical
`brandless_exact_product` family kind. Community-diversity probing follows only
when concentration justifies it. The targeted queue then covers every material
product axis with one `corroborate_or_segment` job, one
`compare_switch_or_value` job, and one `disconfirm_or_strongest_delight` job.
Each job binds the axis-inventory hash and its later planning time. Phase 2 still
does not acquire native evidence: every concrete selected source pointer becomes
a job in the existing owning route accounting and must reconcile to a
source-native captured body plus ledgered evidence unit, or a typed terminal
outcome, before the acquisition seal can pass. A SERP artifact never doubles as
the captured native body. The 40-thread community floor is a minimum, not a
completion target. The seal terminally accounts every discovered candidate in
`reddit_candidate_frontier`, reports `new_usable_reddit_threads` separately
from typed material additions, and closes each material axis only after two
later live continuation families of different kinds, queries, and artifacts add
no material decision change affecting that axis. A useful thread may therefore
sharpen the record without reopening it. Source-limited axes may close only with
a bounded-observation claim ceiling. Before final adjudication, the v5 Material
Axis Discovery Closure must open-code every admitted source-native unit,
terminally disposition every residual candidate, and run two later diverse dry
open-taxonomy probes; Phase 2 may consume the provisional inventory but cannot
convert it into a closed vocabulary. This proves exhaustion of the executed
routes; it does not claim that the whole internet was searched.

## Required reads (pointer-first; the spec owns the method)

1. `docs/research/serp_lane_competitor_scout_20260728/README.md` — reading
   order, authority note. That folder is CANONICAL: lane prose and
   instruments are authored there, in the repo. The operator drive holds
   raw capture data and in-flight scratch only. Write your findings into
   the repo folder, never only into a `C:\tmp` note.
2. `docs/research/serp_lane_competitor_scout_20260728/competitor_ledger_spec_v0.md`
   — specifically: competitor types + promotion ladder; the Phase 1 ->
   fan-out -> Phase 2 shape; the cycle-loop schedule (targeted-return rules
   and echo guard); the decision contract and lifecycle boundary; and the
   `### J5` section (procedure, floor rules, egress settlement).
3. `.agents/workflow-overlay/safety-rules.md` — authorization boundaries.
4. `forseti-harness/runners/serp_phase2_decision_contract.py` and
   `forseti-harness/runners/serp_phase2_decision_lifecycle.py`, including the
   lifecycle runner's `--help` before first use — resolve exact inputs and
   commands from source, not memory.

## Inputs (supplied by the dispatching lane per subject)

- Phase-1 scout folder path (typed ledger JSON, extractions, scout ledger).
- Phase-1 J5 price lines for the subject and harvest-set names.
- `CO1`, `CO2`, and `CO3` terminal-return paths, including their durable
  artifact indices and typed blockers.
- Dereferenced fan-out evidence: company/claim findings, retail/commercial
  findings, and `CO3`'s Reddit/community composition, Channel-3, J3,
  mediator, and unmet-value results.
- For the consumer-brand profile, the hash-pinned product-axis inventory and the
  hash-pinned retailer row-coding view, including per-corpus denominators and
  explicit choice outcomes, plus comment-level community coding and the current
  target-reconciliation ledger.
- The run's one shared lifecycle `--store-root`, plus any earlier decision
  receipt that licenses a `validate_once` probe. Do not accept a caller-supplied
  prior receipt at seal time.

## Method (deltas only; spec sections above own the mechanics)

1. **Consolidate fan-out findings.** Dereference all three specialist artifact
   indices. Build one cited set of newly surfaced competitors, claims,
   contradictions, substitutions, and unmet-value axes. A terminal blocked
   result stays visible as a gap; it is never silently treated as an empty
   finding.
2. **Derive the targeted queue.** For every proposed query, record the
   specialist artifact and exact finding that caused it. Include the spec's
   required head-to-head checks and bounded entrant, claim-attack, or
   unmet-value probes. The query must add a discriminating check that Phase 1
   could not have authored before fan-out. Echo guard applies: the probed
   name's own appearance bears no new rung.
   For each material consumer-brand axis, record exactly the three profile goals
   above and bind the pre-Phase-2 inventory hash. Query wording is adaptive.
   The three goals deliberately separate recurrence/segments,
   comparison/switch/value choice, and the strongest counter-case or delight.
3. **Claim automatic validation before capture.** Before any automatic
   `validate_once` probe, validate and retain its earlier decision receipt
   byte-for-byte in the shared store, then use the lifecycle adapter to claim
   the licensed entity. A second claim, another store root, a caller-supplied
   prior receipt, or capture-before-claim ordering is not an allowed substitute.
4. **Run the targeted SERP return and J5 delta.** Capture the derived Google
    queue at the current owner cadence. For every fan-out promotion, run the
    spec's J5 procedure, 1-2 URLs per name, zero clicks, no proxy. Sponsored
    rows never floor-bearing.
5. **Resolve material source pointers.** SERP cards and snippets are discovery
   only. Put every concrete material source into the existing route-job
   accounting for its owning Scanning/Capture lane. Phase 2 performs no native
   capture and does not convert an unrun follow-up into no yield. `CO0` waits
   for the captured or typed terminal artifact before sealing. Reconcile every
   selected candidate as `used`, `captured_excluded`, `no_material_yield`,
   `blocked`, or `unavailable`; `captured` requires a native body and a final
   evidence-unit reference, never a SERP artifact alone.
6. **Seal and consolidate.** Seal through the lifecycle adapter using only the
   persisted claims and store-supplied prior receipts. Persist the decision
   receipt and lifecycle provenance. Update the typed ledger, unmet-value map
   (one-directional evidence weight, provenance-cited, defenses counted), J5
   prices, retailer set, and mediator list in staging.

## Egress boundaries (hard)

- Read the CURRENT owner cadence from the spec/orchestrator comments before
  the first capture — do not assume the historical 15-20/hr band, and do not
  exceed whatever the owner has currently set. One Google-stream capture at a
  time; a block is a stop signal for that stream (finish the
  writeup with what you have, report the block prominently, never retry hot).
- Standing non-claims on every artifact: counts of observed cards only, never
  prevalence/volume/share; US-parameterized is not physically US-local; raw
  capture data stays on the operator drive, outside Git.

## Return contract (schema-bound; one line per field; `unknown` if absent)

- `fanout_inputs_consumed`: one terminal path and dereferenced artifact index
  for each of `CO1`, `CO2`, and `CO3`, including typed blockers.
- `targeted_probe_derivations`: each query with the specialist finding and
  artifact cite that caused it.
- `product_axis_probe_derivations`: for the consumer-brand profile, each axis
  with all three goal-labelled jobs, the bound inventory hash, planning time,
  search artifact, selected target IDs, and source findings.
- `focused_source_jobs`: every material source pointer with owning route, job
  ID, reconciled terminal state, native-body artifact when captured, final
  evidence-unit references, and artifact provenance; `0` only when all three
  searches returned no material source.
- `ledger`: final consolidated names with type, ladder rung, and provenance.
- `j5_prices`: per promoted name — list price, standing floor, response-trap
  note, source URL class.
- `unmet_value_map`: ranked axes, each with strongest quote + score + slot.
- `decision_receipt`: sealed receipt path and SHA-256.
- `lifecycle_provenance`: shared store root, claim ids, prior-receipt digests,
  and outcome provenance path.
- `blocks`: count and detail, or `0 blocks in N captures`.
- `artifacts`: staging paths written; snapshot refresh commit if routed.
