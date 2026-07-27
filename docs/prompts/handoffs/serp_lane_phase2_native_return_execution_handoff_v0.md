# SERP Lane Phase 2 — Native Return Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded runtime commission to execute phase 2 of the SERP-lane competitor
  cycle for a subject whose phase 1 (scout pass: seed -> harvest -> vs -> J5)
  is complete: consume the trigger-thread queue through the Reddit lane,
  harvest Channel-3 names, settle J3 rendered-vs-actual, run the J5 delta on
  promotions, author evidence-targeted return probes, and consolidate the
  typed ledger + unmet-value map.
use_when:
  - A phase-1 scout pass has emitted a typed ledger and trigger-thread queue
    and the owner dispatches the native-return half of the cycle.
stale_if:
  - The competitor-ledger spec section this handoff points to is superseded
    (next expected supersession: the full-bank megadogfood re-judgment,
    ~2026-07-30).
  - The Reddit lane runner, its access gate, or the owner egress band changes.
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging (subject work folder under C:\tmp, alongside the phase-1
    scout folder) for all capture packets, composition reads, and findings
    notes; repo docs-write only to refresh the routed snapshot folder
    docs/research/serp_lane_competitor_scout_20260728/ in its lane PR when the
    owner routes.
  input_prompt_source: docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    This accepted handoff is the bounded runtime authorization (AGENTS.md):
    Reddit-lane thread captures for the supplied trigger queue, J5 price
    captures (1-2 URLs per name), and evidence-targeted SERP probes for this
    subject only. No other capture surfaces, no clicks, no proxy, no CAPTCHA
    interaction, no account state.
  targets: >
    operator staging folders for this subject; the routed snapshot folder
    above (refresh-only). No code, spine, or overlay edits.
  branch: the open SERP-lane routing branch/PR when snapshots are refreshed;
    otherwise no repo writes.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** turn phase-1's SERP-side competitor answer into the community-side
answer — who complaint threads actually name, whether Google's rendered
verdicts hold up inside the threads, and what every promoted name costs.
**Done looks like:** an updated typed ledger with new finding-grade
promotions (or an explicit "none"), a J3 tag per captured vs/contrarian
thread, a price line per promoted name, a provenance-cited unmet-value map,
and a targeted-probe list for the return leg — all counts-only, all in
staging, blocks reported as stop events. This is the executor target and a
review axis-to-attack, not a review pass bar.

## Required reads (pointer-first; the spec owns the method)

1. `docs/research/serp_lane_competitor_scout_20260728/README.md` — reading
   order, authority note. That folder is CANONICAL: lane prose and
   instruments are authored there, in the repo. The operator drive holds
   raw capture data and in-flight scratch only. Write your findings into
   the repo folder, never only into a `C:\tmp` note.
2. `docs/research/serp_lane_competitor_scout_20260728/competitor_ledger_spec_v0.md`
   — specifically: competitor types + promotion ladder; Channel 3
   (complaint-borne names) and Channel 4 (retail-shelf corroboration); the
   two-phase shape; the cycle-loop schedule (return-leg rules and the
   targeted-probe echo guard); and the `### J5` section (procedure, floor
   rules, egress settlement).
3. `.agents/workflow-overlay/safety-rules.md` — authorization boundaries.
4. The Reddit lane runner's `--help` and source before first run
   (`run_reddit_old_http_batch.py`, in the forseti-harness runners tree) —
   resolve exact args from source, not memory.

## Inputs (supplied by the dispatching lane per subject)

- Phase-1 scout folder path (typed ledger JSON, extractions, scout ledger).
- Trigger-thread queue (URL list JSON) and mediator list.
- Phase-1 J5 price lines for the subject and harvest-set names.
- Worked example of every step: the Tower 28 trial
  (`tower28_scout_trial_findings_v0.md` in the routed snapshot folder;
  evidence folders named in the README).

## Method (deltas only; spec sections above own the mechanics)

1. **Native capture.** Feed the trigger queue to the Reddit lane runner
   (raw retention; set `--max-urls` to the queue size). Reddit is a
   different host from the Google stream — concurrent operation is
   owner-accepted; any access failure is recorded, never retried hot.
2. **Composition read + Channel 3.** Parse captured threads (see the Tower 28
   `thread_composition` pattern in the trial evidence folder): substitute
   mentions with quotes and scores, keyword pos/neg counts. Every
   complaint-borne competitor name enters the ledger; a name already holding
   one other surface class promotes to finding-grade.
3. **J3 settlement.** Per vs/contrarian thread: rendered snippet verdict vs
   top-voted in-thread verdict; tag ALIGNED / RENDERED_BETTER / NATIVE_BETTER.
   Contrarian titles are doors, not composition verdicts.
4. **J5 delta.** For every phase-2 promotion: the spec's J5 procedure, 1-2
   URLs per name, zero clicks, no proxy. Sponsored rows never floor-bearing.
5. **Return leg.** Author evidence-targeted probes from what steps 2-4
   surfaced (entrant checks, unmet-value-axis shapes, claim follow-ups).
   Echo guard applies: the probed name's own appearance bears no new rung.
6. **Consolidate.** Update the typed ledger, unmet-value map (one-directional
   evidence weight, provenance-cited, defenses counted), retailer set, and
   mediator list in staging; note any J5 re-run triggers left open.

## Egress boundaries (hard)

- Read the CURRENT owner cadence from the spec/orchestrator comments before
  the first capture — do not assume the historical 15-20/hr band, and do not
  exceed whatever the owner has currently set. One Google-stream capture at a
  time; a block on any surface is a stop signal for that stream (finish the
  writeup with what you have, report the block prominently, never retry hot).
- Standing non-claims on every artifact: counts of observed cards only, never
  prevalence/volume/share; US-parameterized is not physically US-local; raw
  capture data stays on the operator drive, outside Git.

## Return contract (schema-bound; one line per field; `unknown` if absent)

- `ledger_delta`: names added, with type and ladder rung, each with one
  provenance cite (slot/packet id).
- `promotions`: names newly finding-grade, with both surface classes named.
- `j3_tags`: per-thread tag list with thread URL.
- `j5_prices`: per promoted name — list price, standing floor, response-trap
  note, source URL class.
- `unmet_value_map`: ranked axes, each with strongest quote + score + slot.
- `targeted_probe_list`: return-leg queries with the evidence line each is
  derived from.
- `blocks`: count and detail, or `0 blocks in N captures`.
- `artifacts`: staging paths written; snapshot refresh commit if routed.
