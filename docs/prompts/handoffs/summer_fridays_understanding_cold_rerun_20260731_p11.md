# Summer Fridays Understanding Cold Rerun p11 — Acquire & Seal Handoff

```yaml
retrieval_header_version: 1
artifact_role: Execution-ready cold handoff
scope: >
  Executes one fresh Summer Fridays Understanding Acquire & Seal run using the
  current SERP Phase 1 -> CO1/CO2/CO3 fan-out -> SERP Phase 2 sequence, then
  stops before Deliver.
use_when:
  - Confirming whether the enhanced Understanding acquisition process produces
    a complete, provenance-bearing substrate for the same question used in p10.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
  - docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md
  - docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md
stale_if:
  - The company Understanding acquisition sequence, phase-acquisition seal,
    SERP Phase 1 boards, or Phase 2 lifecycle contract changes.
  - The couriered handoff commit is not the receiver's execution base.
```

## Prompt Preflight

```yaml
prompt_preflight:
  output_mode: file-write
  edit_permission: implementation-authorized
  targets:
    - C:\tmp\forseti-summer-fridays-understanding-p11-20260731\
    - docs/research/summer_fridays_understanding_dogfood_20260731_p11/
    - docs/workflows/summer_fridays_understanding_dogfood_20260731_p11/
  branch: >
    one clean receiver-owned branch/worktree at the couriered handoff commit;
    only the named p11 outputs may become dirty
  input_prompt_source: >
    docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md
    at the couriered handoff commit
  write_destination:
    raw_root: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\
    evidence_root: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/
    seal: docs/workflows/summer_fridays_understanding_dogfood_20260731_p11/coordinated/acquisition_seal.md
```

Shared prompt constants remain owned by
`docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`.

```yaml
receiver_binding:
  receiver_class: receiver_to_bind
  binding_state: receiver_to_bind
  launch_checkout: receiver_to_observe
  effective_target_worktree: receiver_to_select_or_create
  required_revision: couriered_handoff_commit
  revision_mode: exact
  capability_proof: verify direct write capability in the selected worktree
  no_concurrent_writer_state: verify before the first write
```

The receiver may select or create any clean dedicated worktree at the couriered
handoff commit. A different launch checkout, branch name, or manager-prefixed
path is not a blocker. Stop only for ambiguous target identity, revision
mismatch, unexpected dirt, another writer, or an observed required-tool or
guard denial.

## Bound Commission

```yaml
commission:
  subject: Summer Fridays
  mode: forward
  commission_profile: company_competitive_intelligence
  time_posture: recency_first
  cycle_id: summer_fridays_understanding_p11_20260731
  commission_id: summer_fridays_understanding_cold_confirmation_p11
  phase: understanding
  turn: acquire_and_seal
  bound_question: >
    What does current public evidence show about Summer Fridays as a company
    and brand system—its identity, ownership, leadership, proposition,
    offering architecture, markets and channels, chronology and material
    events, customer and community response, and bounded outside-in
    context—and which observable tensions warrant later Problem Framing?
  intended_consumer: Forseti Intelligence Cycle Deliver turn
  intended_use: >
    Decision-neutral broad company understanding that is
    Problem-Framing-ready.
  phase_scope: Current outside-in company and brand model acquired cold.
```

This is the same Understanding question and use as p10. The question is
commission input, not permission to reuse any p10 answer, source, competitor,
query, or conclusion.

## Goal And Success Signal

**Goal:** acquire the fullest decision-useful evidence substrate that the
current bounded process can support, using the enhanced search, official,
retail, review, Q&A, community, and comment venues before any synthesis turn
chooses what matters most.

**Success:** `CO0` can truthfully issue `SEALED_READY_FOR_DELIVER` only after:

- the validated commission board precedes a fresh SERP Phase 1 scout;
- Phase 1's typed outputs feed all three mandatory specialists;
- `CO1`, `CO2`, and `CO3` have terminal returns and their durable evidence has
  been dereferenced;
- targeted SERP Phase 2 consumes the combined findings and seals its decision
  lifecycle;
- every material information job is supported, contradicted, meaningfully
  bounded, or honestly blocked/gapped; and
- the complete cost record and provenance index exist.

A truthful `BLOCKED_ACQUISITION_INCOMPLETE` is a valid run result. A passing
seal obtained by narrowing the question, dropping an evidence family, treating
blocked access as absence, or reusing prior Summer Fridays evidence is not.

## Coldness Quarantine

Every p11 evidence actor, including `CO0`, `CO1`, `CO2`, and `CO3`, is forbidden
from reading:

- `docs/workflows/serp_scout_pass_calibration_predeclaration_v0.md`;
- every prior Summer Fridays artifact under `docs/research/`,
  `docs/workflows/`, and `docs/prompts/`, including every `summer_fridays*`
  path from p05 through p10;
- the prior Summer Fridays files inside
  `docs/research/serp_lane_competitor_scout_20260728/`, including the
  retroactive Summer Fridays ledger and Phase 2 native return; the folder's
  method, spec, and board authority remain readable where the current SERP
  handoffs require them;
- prior Summer Fridays Data Lake packets, including p05-p10 and the 2026-07-26
  company-intelligence inputs; and
- pre-dispatch operator staging under `C:\tmp` matching `forseti-sf-*` or
  containing prior Summer Fridays runs.

This handoff and the newly created p11 roots named in Prompt Preflight are
exempt. The normal lake-first reuse clause is overridden for this subject.
SERP Phase 1 must run fresh.

Coldness is fact-level, not merely file-level. Current method sources may
contain Summer Fridays examples; their mechanics are reusable, but no
Summer Fridays fact from those examples may enter a query, job, finding,
comparison, or seal. Record the actual allowed-source reads and p11 evidence
roots in `coldness_provenance.md`; do not claim proof of unread files that the
environment cannot observe.

Only the dispatcher and a separately authorized post-seal adjudicator may read
the quarantined material. The cold actors do not compare p11 with p10.

## Required Method Reads

After binding the receiver and before source-heavy work, read:

1. `AGENTS.md` and `.agents/workflow-overlay/README.md`;
2. the Commission Signal Board playbook and prompt structure named in
   `open_next`;
3. `docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md`;
4. `docs/research/serp_lane_competitor_scout_20260728/README.md` and
   `competitor_ledger_spec_v0.md`, while respecting the subject-fact quarantine;
5. `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`;
6. `.agents/workflow-overlay/safety-rules.md`; and
7. the Retailer PDP Information-Extraction Standard plus only the source-family
   recipes reached through the selected jobs.

Resolve runner arguments and lifecycle behavior from current source or
`--help`, never from old run commands.

## Required Output Map

```yaml
durable_outputs:
  coldness_provenance: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/coldness_provenance.md
  commission_board: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/commission_board.md
  phase1_return: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/scout_return.md
  phase1_ledger: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/competitor_ledger.json
  phase1_cost_log: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/cost_log.md
  co1_terminal: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md
  co2_terminal: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md
  co3_terminal: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md
  phase2_return: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/targeted_return.md
  phase2_decision_receipt: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json
  phase2_lifecycle_provenance: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/lifecycle_provenance.json
  run_cost_log: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/run_cost_log.md
  acquisition_record: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/turn_a_acquisition_record.md
  acquisition_seal: docs/workflows/summer_fridays_understanding_dogfood_20260731_p11/coordinated/acquisition_seal.md
raw_roots:
  phase1: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1\
  specialists: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\specialists\
  phase2: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2\
  phase2_lifecycle_store: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2_store\
```

Raw captures stay outside Git. Durable outputs cite them with stable packet
identities, hashes where the owning contract requires them, and honest
availability limits. Do not edit current authority, runtime code, schemas,
historical artifacts, or the calibration note during this run. Record a
method defect for a separate work unit instead of patching around it.

## Execution Sequence

### 1. Bind And Validate The Commission

1. Verify the receiver, couriered commit, clean state, target-path
   non-collision, write capability, and absence of another writer.
2. Create `coldness_provenance.md` with the allowed-source ledger and p11 roots.
3. Write a commission-stage company board with
   `run_boundary: COMMISSION_SEALED_PRE_SCAN`.
4. Validate it before any source-heavy acquisition:

   ```powershell
   python -B .agents\hooks\check_commission_signal_board_output.py docs\research\summer_fridays_understanding_dogfood_20260731_p11\coordinated\commission_board.md
   ```

Do not proceed from a failing board.

### 2. Run Fresh SERP Phase 1

Run the current Phase 1 handoff exactly once for Summer Fridays:

- bind `{s}` to the company subject `Summer Fridays`, not to each product or
  SKU; do not multiply the Phase 1 query set across the catalog;
- use every current rival-free Board v2.2 seed and no hand-picked competitor;
- harvest names from the fresh p11 captures while packets land;
- adjudicate promotions fail closed;
- run the merged versus-plus-J5 queue under the current owner egress policy;
- preserve blocks and never retry a blocked transport hot; and
- return the typed ledger, priced comparator rows, trigger-thread queue,
  mediator maps, grid-capture queue, blocks, and artifact paths.

Do not invoke the existing-ledger reuse clause. Do not perform native
Reddit/community capture in Phase 1.

Preserve the emitted mediator interface without reshaping it:
`mediators` remains `name -> sorted subjects`, and `mediator_classes` remains
the parallel `name -> class` map. An uncached class stays
`pending_classification`.

### 3. Dispatch The Mandatory Specialist Fan-Out

After the fresh Phase 1 return exists, `CO0` dispatches exactly `CO1`, `CO2`,
and `CO3` as same-root collaboration subagents. They create no further actors.
Each receives the bound question, its thin role capsule, its Phase 1 inputs,
its authority pointers, claim ceilings, dependencies, output path, and terminal
return contract.

- **CO1 — company core:** identity, ownership, current leadership, proposition,
  owned offering/portfolio denominator, official retailer authorization,
  markets/channels, chronology, material events, and one bounded credible
  outside-in calibration. Publish whether company-owned evidence makes Amazon
  `COMPANY_AUTHORIZED`, with its exact locator. Otherwise publish that company
  authorization was not established; marketplace presence alone cannot change
  CO1's result.
- **CO2 — portfolio and retail:** officially authorized, route-admissible
  retailers; complete admitted brand grids; owned-to-retail reconciliation;
  exact non-bundle PDP baselines; retailer-native facts; corpus/provider
  identity; prices and comparator relevance. Select and attempt at least four
  company-authorized, US-market, route-admissible third-party retailers when
  four exist, favoring distinct evidence venues. The brand DTC site does not
  count; Sephora counts as one and is primary when route-complete. If fewer
  than four qualify, select all and record `AUTHORIZED_RETAILER_SHORTFALL` with
  the observed count and reasons. Never use an unauthorized, duplicate, or
  market-unpinned route as filler. When CO1 does not establish Amazon
  authorization, CO2 may separately classify an exact observed route as
  `MARKETPLACE_IDENTITY_VERIFIED_NOT_COMPANY_AUTHORIZED`; otherwise it remains
  `MARKETPLACE_PRESENCE_UNVERIFIED`. Neither status counts toward the four.
- **CO3 — customer and community:** the Phase 1 trigger-thread, mediator,
  grid-capture, ledger, and cited-substitute inputs; bounded Reddit and qualified
  community capture; retailer review/Q&A corpus accounting; customer language,
  complaints, use contexts, switching, objections, workarounds, and
  discriminating interpretation.

`CO2` may prepare concurrently but cannot probe retailers before `CO1`
publishes the official-retailer outcome. `CO3` begins community acquisition
immediately and waits for `CO2` only where reconciled retailer breadth is a
real dependency.

Each specialist locks one evidence-derived job set, persists evidence as it is
produced, and writes one terminal return. A blocked result remains terminal
evidence of a gap; it is not converted into an empty result.

### 4. Apply The Comment-Evidence Rule

Keep comment-derived evidence separate from the creator or post that contains
it. A comment theme may become decision-bearing only when at least one of these
is true:

- the comment carries its own engagement context and that context is preserved
  without treating it as prevalence; or
- the same theme is independently corroborated by distinct, non-duplicated
  comments, authors, threads, or venues.

Syndicated, copied, or repeated comments count once. Creator/post engagement
does not automatically transfer to a comment. Where a social engagement number
is used, compare it with that creator's own recent-grid baseline or label it
`UNBASELINED`. Preserve unsupported themes as observations or gaps, not
customer-consensus claims.

### 5. Run Targeted SERP Phase 2

Only after all three specialist terminal returns exist:

1. `CO0` dereferences their durable evidence and typed blockers.
2. Derive each targeted query from a named specialist finding, contradiction,
   competitor, claim, or unmet-value seam that Phase 1 could not have authored.
   Product-specific queries are licensed here only after exact product identity
   and a decision-material seam exist. A tail SKU receives no query merely
   because it is in the portfolio; query it only when the specialist evidence
   shows that omitting it could change the answer.
3. Use one shared lifecycle store at the path in `raw_roots`.
4. Retain the earlier receipt and claim every licensed automatic validation
   before capture. Do not accept another store root, capture-before-claim
   ordering, or caller-supplied prior receipt as a substitute.
5. Run the bounded targeted Google SERP and J5 delta under the current egress
   policy. Phase 2 performs no native Reddit/community capture.
6. Seal through the lifecycle adapter and persist the final decision receipt,
   claims, consumed specialist provenance, material blocks, consolidated ledger,
   prices, and unmet-value map.

A missing or invalid lifecycle record, an unconsumed terminal return, or a
material Phase 2 block forces the blocked acquisition state.

### 6. Integrate, Seal, And Stop

`CO0` fresh-reads every load-bearing artifact, writes the acquisition record,
and manually adjudicates the whole acquisition gate. Specialist returns are
pointers, never evidence by themselves.

Issue one consolidated owner-unblock escalation only when an observed,
load-bearing failure has a plausible small owner action. Use at most the owning
route's one permitted recovery after that action. Otherwise preserve the gap.

Write exactly one of:

- `SEALED_READY_FOR_DELIVER`, `acquisition_gate: pass`,
  `deliver_allowed: true`; or
- `BLOCKED_ACQUISITION_INCOMPLETE`, `acquisition_gate: blocked`,
  `deliver_allowed: false`.

Then stop. Do not write a company report, recommendation, strategic response,
Problem Framing artifact, value proposition, pricing response, or Deliver
handoff. Do not read or compare p10. The next authorized action is an
owner-controlled post-seal calibration adjudication in a separate context.

## Cost-Log Obligation

For the scout pass specifically, record capture counts, block/failure counts,
wall-clock time, which sub-steps ran as scripts versus needed human or agent
judgment, and any rerun step that waited on the pass.

For every commissioned unit, record `started_at` and `ended_at`, with active,
waiting, and blocked segments typed separately so the timeline can be
reconstructed. Phase 1, specialist community work, and Phase 2 must remain
separate cost units. Record observed counts only.

At minimum, each cost row includes:

```yaml
unit:
actor:
started_at:
ended_at:
active_segments:
waiting_segments:
blocked_segments:
scripted_steps:
judgment_steps:
capture_count:
block_or_failure_count:
downstream_waits_caused:
```

## Failure And Stop Conditions

- Never lower evidence requirements to obtain a passing seal.
- Never infer absence, authorization, nationwide availability, prevalence,
  share, sales, or trend from a blocked route, one local shell, SERP counts,
  raw engagement, or point-in-time retailer metrics.
- Preserve every selected route, packet, receipt, typed miss, contradiction,
  accepted residual, material blocker, and provenance locator.
- Use at most one retry after an observed failed material route unless its
  owning source contract is stricter. Google blocks follow the current SERP
  block-recovery contract and never enter a hot retry.
- Stop with `BLOCKED_DRIFT` before work if receiver identity, revision,
  cleanliness, target ownership, or write capability cannot be established.
- Stop with `BLOCKED_ACQUISITION_INCOMPLETE` when a material evidence job or
  Phase 2 lifecycle obligation remains unresolved after its permitted route.

## Validation And Return

Run, in order:

1. the commission-board validator before acquisition;
2. each selected runner's current schema/contract validation as its artifact is
   produced;
3. Phase 2 decision-contract and lifecycle checks, including receipt hashes and
   claim/provenance resolution;
4. artifact-presence and citation-resolution checks for every path in
   `durable_outputs`;
5. retrieval-header checks for the new durable Markdown artifacts;
6. `git diff --check`; and
7. a final clean-scope check showing only the named p11 output roots changed and
   raw captures remained outside Git.

Return:

```yaml
status: SEALED_READY_FOR_DELIVER | BLOCKED_ACQUISITION_INCOMPLETE | BLOCKED_DRIFT
bound_question_preserved: true | false
coldness_attestation: compliant | violated | unverifiable
commission_board:
phase1_return:
specialist_returns:
  co1:
  co2:
  co3:
phase2_return:
decision_receipt:
lifecycle_provenance:
cost_logs:
acquisition_record:
acquisition_seal:
material_gaps_or_blocks: []
deliver_started: false
```

Report only observed paths, hashes, counts, validation outcomes, and states.
Do not claim that this run confirms the final Deliver's decision usefulness:
this commission confirms the acquisition substrate only.
