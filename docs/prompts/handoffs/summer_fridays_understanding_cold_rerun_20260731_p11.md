# Summer Fridays Understanding Confirmation Cycle p11 — Cold Execution Handoff

```yaml
retrieval_header_version: 1
artifact_role: Execution-ready cold handoff
scope: >
  Executes one fresh Summer Fridays Understanding confirmation cycle using the
  current SERP Phase 1 -> CO1/CO2/CO3 fan-out -> SERP Phase 2 sequence. It
  preserves Acquire & Seal and Deliver as separate turns, but commissions both:
  Deliver begins in fresh context only after a valid passing acquisition seal.
use_when:
  - Confirming whether the enhanced Understanding acquisition process produces
    complete, provenance-bearing, decision-useful competitive intelligence for
    the same question used in p10, without reading or reusing the p10 answer.
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

## Load Contract

```yaml
packet_version: 1
mode: max
created_at: 2026-07-31T22:25:52+08:00
created_by_lane: codex/summer-fridays-confirmation-handoff-20260731
workspace: Forseti repository at the receiver's clean dedicated worktree
handoff_path: docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md
authoring_baseline: 099eba5fd4b2714d475c39ad91088370abceea3c
expected_branch: receiver-owned branch created from the couriered handoff commit
expected_head: couriered_handoff_commit
expected_dirty_state: clean before execution; afterward only the named p11 output roots may be dirty
load_rule: >
  confirm-don't-trust; re-verify the handoff, current authority, branch, HEAD,
  dirty state, capabilities, and every load-bearing source before acting
```

## Goal Handoff

```yaml
goal_handoff:
  long_term_goal: >
    Make Forseti's Understanding phase consistently produce complete,
    decision-useful competitive intelligence that earns decisions through
    evidence rather than description or price-war advice.
  anchor_goal: >
    Re-run the same Summer Fridays company-Understanding question cold through
    the strengthened acquisition process, then produce the complete p11
    Understanding deliverable from only the sealed p11 evidence.
  success_signal: >
    A cold receiver earns a valid phase_acquisition_seal_v2 after fresh SERP
    Phase 1, the mandatory CO1/CO2/CO3 fan-out, and targeted SERP Phase 2, then
    a fresh Deliver context produces an evidence-cited, uncertainty-bounded,
    commercially useful company report without reusing p10 facts or proposing
    price competition.
```

## Open Decision / Fork

None open. The owner has selected a complete confirmation cycle. Acquire & Seal
remains the hard gate; a passing seal authorizes a fresh Deliver turn, while a
blocked seal ends the commission without manufacturing a report.

## Drift Guard

- Do not stop at the acquisition substrate when the seal validly passes; the
  commissioned outcome is the complete Understanding deliverable.
- Do not start Deliver when acquisition is blocked, incomplete, or unvalidated.
- Do not read or reuse p10 Summer Fridays facts, competitors, queries,
  conclusions, or prose during acquisition or Deliver. A later owner-controlled
  calibration may compare p11 with p10 only after the p11 report is frozen.
- Do not turn price evidence into price-cut advice. Forseti competes on
  observable value: differentiation, experience, confidence, fit, proof, and
  reasons customers would willingly pay more—not a race to charge less.
- Do not perform Problem Framing, prescribe a company strategy, add a Phase-A
  whitespace-opportunity gate, or install new doctrine/runtime during this run.

## Inherited Context (Does Not Flow To A New Lane)

### Source-loading state to re-establish

- Overlay policy: `.agents/workflow-overlay/source-loading.md`.
- Enter the ladder through this handoff, the current Commission Signal Board
  playbook/prompt authority, and the two current SERP handoffs named in
  `open_next`.
- Prior chat, this packet, and old Summer Fridays artifacts are orientation at
  most; none is authority for strict or actionable claims.
- Before capture, fresh-read the current runtime help/contracts for every
  selected route, especially the Google queue, acquisition-seal validator,
  Reddit weekly reader, paid-ad routes, and any conditionally triggered native
  or TikTok Shop route.

### Earlier-decided concepts and behaviors

- Company Understanding acquisition order is commission board and capability
  preflight -> fresh SERP Phase 1 -> exactly CO1/CO2/CO3 -> targeted SERP Phase
  2 -> acquisition seal -> fresh-context Deliver.
  - Verify in: `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`.
  - Compare target: the section `Forseti Intelligence Cycle Operating Contract`
    at the couriered handoff commit.
- The mandatory high-value venue set includes Google Ads Transparency Center,
  Meta Ads Library, the current Reddit weekly lake read, the bounded Reddit
  community scout, official-retailer authorization, full selected-retailer PDP
  breadth, and conditional native-social/TikTok Shop trigger assessment.
  - Verify in: `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`.
  - Compare target: `Default US Consumer-Beauty Understanding Route` and the
    `phase_acquisition_seal_v2` block at the couriered handoff commit.
- PR #1403 hardened Google block recovery, real-Chrome Reddit packet admission,
  commission coverage, and exact acquisition accounting.
  - Verify in: Git commit `099eba5fd4b2714d475c39ad91088370abceea3c`
    and the current source/tests; the commit message is orientation, not proof.

## Exact Next Authorized Action

1. Bind a clean receiver at the couriered handoff commit and return one load
   outcome: `REUSE`, `PARTIAL_REUSE`, `STALE_REREAD_REQUIRED`,
   `BLOCKED_DRIFT`, `BLOCKED_MISSING_PACKET`, or `BLOCKED_UNVERIFIABLE`.
2. If reusable, execute Turn A exactly as commissioned below and validate the
   resulting `phase_acquisition_seal_v2`.
3. If and only if Turn A seals ready, start Turn B in fresh context and produce
   the p11 company Understanding report from the sealed p11 evidence.
4. Stop after the validated Understanding report; Problem Framing and p10/p11
   calibration remain separate owner-controlled work.

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
    deliverable: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/deliver/company_understanding_report.md
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
  turns:
    - acquire_and_seal
    - deliver_if_sealed
  bound_question: >
    What does current public evidence show about Summer Fridays as a company
    and brand system—its identity, ownership, leadership, proposition,
    offering architecture, markets and channels, chronology and material
    events, customer and community response, and bounded outside-in
    context—and which observable tensions warrant later Problem Framing?
  intended_consumer: owner and later Forseti Intelligence Cycle Problem Framing turn
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
current bounded process can support, then turn that sealed substrate into a
complete, readable competitive-intelligence deliverable using the enhanced
search, official, retail, review, Q&A, community, comment, and paid-ad venues.

**Turn-A success:** `CO0` can truthfully issue `SEALED_READY_FOR_DELIVER` only after:

- the validated commission board precedes a fresh SERP Phase 1 scout;
- Phase 1's typed outputs feed all three mandatory specialists;
- `CO1`, `CO2`, and `CO3` have terminal returns and their durable evidence has
  been dereferenced;
- targeted SERP Phase 2 consumes the combined findings and seals its decision
  lifecycle;
- every material information job is supported, contradicted, meaningfully
  bounded, or honestly blocked/gapped; and
- the complete cost record and provenance index exist.

**Commission success:** after that gate passes, a fresh Deliver context produces
the company Understanding report at the bound path, with decisive conclusions,
competitive structure, observable value and threats to it, customer-choice
mechanisms, portfolio/retail architecture, uncertainty, counterevidence, and
next observables all traceable to sealed p11 evidence. It does not recommend a
price cut, invent strategy, or start Problem Framing.

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

Only a separately authorized post-report calibration adjudicator may read the
quarantined material. Neither the acquisition actors nor the Deliver context
compares p11 with p10.

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
  completed_company_board: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/deliver/completed_company_board.md
  understanding_deliverable: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/deliver/company_understanding_report.md
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

### Turn A — Acquire & Seal

### 1. Bind And Validate The Commission

1. Verify the receiver, couriered commit, clean state, target-path
   non-collision, write capability, and absence of another writer.
2. Create `coldness_provenance.md` with the allowed-source ledger and p11 roots.
3. Before network capture, record the route-capability preflight for Google
   queue state/recovery, the Reddit weekly reader, Google and Meta paid-ad
   routes, and typed native-social/TikTok Shop trigger decisions.
4. Write a commission-stage company board with
   `run_boundary: COMMISSION_SEALED_PRE_SCAN`, top-level `CO0`, three available
   worker slots, required Google/Meta/Reddit-weekly rows, and conditional
   native-social/TikTok Shop trigger-assessment rows.
5. Validate it before any source-heavy acquisition:

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
  outside-in calibration. After binding exact advertiser identity, attempt both
  Google Ads Transparency Center and Meta Ads Library; a typed zero-yield or
  blocked result remains visible and never becomes omission. Publish whether company-owned evidence makes Amazon
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
- **CO3 — customer and community:** begin with the read-only current weekly
  Reddit lake result, then consume the Phase 1 trigger-thread, mediator,
  grid-capture, ledger, and cited-substitute inputs; bounded Reddit and qualified
  community capture; retailer review/Q&A corpus accounting; customer language,
  complaints, use contexts, switching, objections, workarounds, and
  discriminating interpretation.

For native TikTok, Instagram, or YouTube items, record a separate trigger for
each platform. Deep capture is required only when the listing is ambiguous and
opening the native item could change the bound answer. For TikTok Shop, trigger
capture only when Summer Fridays is shown to be creator/influencer-led or the
shop is commercially material. When triggered, use the verified US-egress
browser route and preserve typed wrong-country, route-blocked, or unhealthy-
session failures; proxy availability by itself is not readiness.

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

### 6. Integrate And Seal Turn A

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

If the seal is blocked, stop without a company report. If the seal passes,
freeze the Turn-A artifacts and start the separately bounded Deliver turn below.

### Turn B — Fresh-Context Deliver

Start in fresh context from the validated acquisition seal. Re-hash and
dereference the p11 acquisition record, three specialist terminals, Phase 1 and
Phase 2 returns, decision receipt, provenance, and material gaps. Do not read
p10 or rely on the acquiring controller's chat memory.

First settle the commission-stage board into `completed_company_board.md`, with
every selected venue carrying its observed checked, blocked, zero-yield, or
typed not-applicable result. Then write `company_understanding_report.md` for
the owner. It must answer the bound question and make the most decision-useful
judgments easy to find. Include:

1. an Executive Intelligence Brief of three to seven conclusions, each with
   claim, evidence bound, commercial consequence, confidence, and next
   observable;
2. identity, ownership, leadership, proposition, chronology, and material
   events;
3. Portfolio And Retail Architecture: owned denominator, product/claim/price
   architecture, official-retailer board, complete attempted PDP breadth,
   review-corpus identity, selected interpretive depth, markets, and channels;
4. customer/community evidence: choice reasons, delight, complaints, objections,
   use contexts, workarounds, switching, comment corroboration, and sample or
   representativeness limits;
5. competitive structure: named fidelity threats, adjacent alternatives,
   mechanical-but-weak candidates, and where comparison would be incoherent;
6. observable value: where customers appear to find value, what strengthens or
   weakens it, what threatens it, and which evidence would change that view;
   price evidence may diagnose value pressure but must not become price-cut
   advice; and
7. material tensions and next observables that later Problem Framing should
   evaluate, without selecting a problem or prescribing strategy now.

Every load-bearing claim must cite the sealed p11 evidence. Put uncertainty,
counterevidence, and reversal conditions beside the judgment they qualify.
Separate facts, inference, and unknowns. Do not infer sales, share, trend,
prevalence, representative demand, willingness to pay, internal intent, or
causality beyond the captured evidence.

Stop after validating the report. Do not perform Problem Framing, recommend a
strategic response, compare p11 with p10, or turn a value finding into a price
war. The next owner-controlled act is post-report p10/p11 calibration.

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
- Stop before Deliver unless the validated seal says
  `SEALED_READY_FOR_DELIVER`, `acquisition_gate: pass`, and
  `deliver_allowed: true`.

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
7. the completed company board validator plus the final report's
   citation/provenance checks;
8. a final clean-scope check showing only the named p11 output roots changed and
   raw captures remained outside Git.

Return:

```yaml
status: UNDERSTANDING_DELIVERED | BLOCKED_ACQUISITION_INCOMPLETE | BLOCKED_DRIFT
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
completed_company_board:
understanding_deliverable:
deliver_validation:
material_gaps_or_blocks: []
problem_framing_started: false
```

Report only observed paths, hashes, counts, validation outcomes, and states.
Do not claim that the cycle is exhaustive or that p11 is better than p10 without
the later blind calibration. This commission produces the p11 evidence and
deliverable; comparison remains outside it.

## Authority And Source Ledger

- `AGENTS.md` and `.agents/workflow-overlay/README.md`
  - Role: repository and workflow authority.
  - Load-bearing: yes.
  - Compare target: reread-required at the couriered handoff commit.
  - Last checked by sender: 2026-07-31.
  - Reuse rule: never rely on this packet's summary for current instructions.
- Commission Signal Board playbook and prompt-structure authority named above
  - Role: sequence, evidence, seal, and Deliver contract.
  - Load-bearing: yes.
  - Compare target: Git blob at the couriered handoff commit.
  - Last checked by sender: 2026-07-31 at authoring baseline `099eba5f`.
  - Reuse rule: reread if HEAD differs or either file changed.
- Current SERP Phase 1 and Phase 2 handoffs named in `open_next`
  - Role: lane-local execution contracts.
  - Load-bearing: yes when those phases execute.
  - Compare target: Git blobs at the couriered handoff commit.
  - Last checked by sender: current paths verified 2026-07-31; content remains
    receiver-reread-required.
  - Reuse rule: resolve current runner arguments from source or `--help`.
- Prior Summer Fridays p05-p10 artifacts
  - Role: quarantined calibration evidence.
  - Load-bearing: no for this execution; forbidden input.
  - Compare target: path-pattern quarantine in `Coldness Quarantine`.
  - Last checked by sender: 2026-07-31.
  - Reuse rule: do not read until separately authorized post-report calibration.

## Current Task And Workspace State

- Completed: acquisition-process hardening merged through PR #1403; this packet
  updated to commission the full confirmation cycle.
- Partially completed: none of p11 acquisition or Deliver has run.
- Broken or uncertain: live Google/browser, retailer, ads, native-social, and
  TikTok Shop availability remain runtime observations, not predeclared facts.
- Authoring branch: `codex/summer-fridays-confirmation-handoff-20260731`.
- Authoring baseline: `099eba5fd4b2714d475c39ad91088370abceea3c`.
- Dirty state before handoff edit: clean.
- Dirty state after handoff edit: only
  `docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md`
  modified.
- Expected receiver state: clean at the couriered handoff commit; only named
  p11 output roots may become dirty.

## Changed / Inspected / Tested Files

- `docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md`
  - Status: modified by this authoring lane.
  - Role: sole execution handoff for the p11 confirmation cycle.
  - Important change: passing acquisition now leads to a separately gated
    fresh-context Deliver turn; current mandatory route/preflight/accounting
    requirements are explicit.
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
  - Status: inspected, unedited.
  - Role: current acquisition and company-report playbook.
  - Sections: default US consumer-beauty route, acquisition seal v2, retailer
    breadth/depth, native-social/TikTok Shop triggers.
- `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
  - Status: inspected, unedited.
  - Role: Intelligence Cycle Acquire/Deliver and completed-report authority.
  - Sections: Forseti Intelligence Cycle Operating Contract and completed
    company report shape.
- `forseti-harness/runners/run_phase_acquisition_seal_validation.py` and
  `forseti-harness/runners/run_google_serp_queue.py`
  - Status: current merged runtime targets, unedited by this lane.
  - Role: executable seal and Google block/recovery controls the receiver must
    invoke from current source/help rather than copy from this packet.

## Frozen Decisions

- Same p10 question, acquired cold; no p10 fact reuse.
- One top-level `CO0` plus exactly three specialists; no serialization fallback.
- SERP Phase 1 -> specialist fan-out -> SERP Phase 2 is mandatory.
- Google and Meta ad transparency plus Reddit weekly lake are mandatory routes;
  native social and TikTok Shop use typed evidence-driven triggers.
- Selected retail attempts at least four qualified third-party retailers when
  four exist; Sephora is primary when officially named and route-complete.
- Full baseline PDP breadth remains required for every reconciled exact listing;
  expensive interpretation remains evidence-selected.
- Deliver is separate and fresh-context, but is part of this commissioned
  confirmation cycle when—and only when—the acquisition seal passes.
- No price-war advice and no Problem Framing in this handoff.

## Mutable Questions

- Which native-social or TikTok Shop routes trigger: determined only by fresh
  Phase 1/specialist evidence.
- Which products receive Phase 2 queries or expensive interpretation: determined
  only by named decision-material seams in fresh p11 evidence.
- Whether the seal passes: determined by observed route/job outcomes and the
  current validator, never by schedule or desire to reach Deliver.

## Commands And Verification Evidence

- Authoring baseline and scope:
  ```powershell
  git rev-parse HEAD
  git status --short
  ```
  - Observed before editing: `099eba5fd4b2714d475c39ad91088370abceea3c`,
    clean.
  - Receiver re-run target: the couriered handoff commit and its own worktree.
- Prompt/handoff contract checks and `git diff --check`:
  - Observed authoring result: explicit prompt output-mode check reported zero
    findings; strict retrieval-header check exited 0; all nine YAML fences
    parsed; `git diff --check` exited 0.
  - Receiver re-run target: current gates at the couriered handoff commit; do
    not inherit the sender's result.

## Blockers And Risks

- `BLOCKED_CONTROLLER_CAPACITY`: fewer than three worker slots or non-top-level
  `CO0`; stop before capture rather than serialize.
- Live route availability is not pre-proven. Google, retailer, paid-ad,
  Reddit, native-social, and TikTok Shop failures remain typed observed outcomes.
- A load-bearing owner-remediable route failure gets one consolidated owner
  unblock request and at most the owning route's permitted recovery. If still
  material and unresolved, acquisition remains blocked.
- A passing seal does not prove the final report is useful; Deliver must still
  dereference evidence, answer the bound question, expose uncertainty, and pass
  its completed-board/citation checks.

## Superseded / Dangerous-To-Reuse Context

- The earlier version of this packet stopped after Acquire & Seal. That stop is
  superseded: a valid passing seal now leads to fresh-context Deliver under this
  same commission; a blocked seal still stops.
- Prior Summer Fridays handoffs and reports remain historical/calibration
  artifacts, not execution authority or evidence input for p11.
- Any generic-browser fallback that bypasses a current source-specific route is
  dangerous and unauthorized.

## Confirm-Don't-Trust Load Checklist

Before acting, verify the handoff path, couriered commit, clean receiver state,
three available worker slots, output-path non-collision, current authority
blobs, Google queue state writeability, Reddit weekly reader, paid-ad routes,
and typed conditional-route posture. Return `REUSE` only when every
load-bearing item matches. Re-derive safe drift as `STALE_REREAD_REQUIRED`;
stop on authority, ownership, dirty-state, or target conflicts as
`BLOCKED_DRIFT`; never proceed on sender say-so.

## Do Not Forget

No additional reminder beyond the front-loaded Drift Guard and Frozen
Decisions; do not duplicate them into a new local checklist.
