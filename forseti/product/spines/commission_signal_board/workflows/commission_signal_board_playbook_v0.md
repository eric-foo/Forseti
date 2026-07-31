# Commission Signal Board And Forseti Intelligence Cycle Playbook v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow playbook
scope: >
  Operating sequence for standard signal-board and one-company competitive-
  intelligence commissions, plus the two-phase/two-turn Forseti Intelligence
  Cycle contract, without confusing CSB profiling with retrieval, capture,
  classification, or proof.
use_when:
  - Dispatching or rerunning the Commission Signal Board prompt.
  - Commissioning or executing an Understanding or Problem Framing phase.
  - Deciding whether a standard board is ready for classifier-handoff routing or a company report is mechanically complete.
  - Diagnosing validator failures on Commission Signal Board outputs.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
  - .agents/hooks/check_commission_signal_board_output.py
  - forseti-harness/tests/fixtures/commission_signal_board_outputs/
stale_if:
  - The Commission Signal Board prompt output contract changes.
  - The Commission Signal Board validator changes its required sections, fields, or finding codes.
  - Commission boards gain a durable artifact location or CI enforcement path.
```

- Playbook path: `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`.
- Prompt Structure path: `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`.
- Prompt Structure Rules path: `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`.
- Validator path: `.agents/hooks/check_commission_signal_board_output.py`.
- Validator fixture path: `forseti-harness/tests/fixtures/commission_signal_board_outputs/`.
- Current enforcement posture: manual/local checker. Not CI, not pre-commit, not a write hook.

## Purpose

This playbook keeps these objects distinct:

| Object | What it is | Validator applies? |
| --- | --- | --- |
| Intake scaffold | A request for missing commission inputs | No |
| Standard signal board | Existing standard Sections 1-10 with classifier handoff | Yes |
| Commission-stage company board | Conditional company Sections 1-10 sealed before scanning: `run_boundary: COMMISSION_SEALED_PRE_SCAN`, `not_checked` coverage rows as the commissioned scan routes, scout statuses may be `commissioned_not_yet_run` | Yes |
| Company competitive-intelligence report | Conditional company Sections 1-10 with typed ledgers, earned scout statuses, and no classifier handoff | Yes |
| Phase acquisition seal | Durable fresh-context handoff for one Intelligence Cycle phase; binds routes, receipts, provenance, failures, and acquisition-gate state | No |
| Phase deliverable | Understanding or Problem Framing synthesis produced only from a passing phase acquisition seal | Profile-dependent |
| Scanning, Capture, or classifier work | Downstream execution under its owning spine | No |

CSB owns the commission profile, source-family requirements, time posture, and
typed gaps/requests. Scanning owns the intelligent walk. Capture owns venue
access and preservation adapters. This playbook does not authorize downstream
runtime. CSB defines decision-material information jobs and candidate routes; it
does not freeze the participant packet, decide final inclusion, or declare
acquisition complete.

## Forseti Intelligence Cycle

Commission future one-company intelligence work as a **Forseti Intelligence
Cycle**. The phases are **Understanding** followed by **Problem Framing**;
`Problem` is informal shorthand only. Do not use bare `Phase 1` / `Phase 2`
language for a future commission. Historical artifacts keep their original
names and phase labels.

Each phase normally consumes two completed operator/model turns:

### Turn Objectives

The turns optimize different things:

- **Turn A — Acquire & Seal:** maximize decision-useful completeness under the
  integrity floor. Continue until every material information job is supported,
  contradicted, meaningfully bounded, or honestly blocked/gapped. Compactness,
  actor count, and token minimization are not acquisition success criteria.
- **Turn B — Deliver:** after the acquisition gate passes, apply Smallest
  Complete Intervention to the human artifact. Preserve decisive evidence,
  counterevidence, uncertainty, provenance, reversal conditions, and the next
  action while removing repetition and audit detail that does not belong in the
  decision surface.

Turn A/Turn B are turns inside each canonical phase; they do not rename
Understanding and Problem Framing as unqualified Phase A/Phase B.

### Turn A — Acquire & Seal

#### Default US Consumer-Beauty Understanding Route

The default coordinated route has exactly four evidence actors:

- `CO0`: whole-run Chief Architect, integration, durable-record owner, and
  acquisition-seal owner;
- `CO1`: owned company and high-yield core — identity, ownership, leadership,
  offering/portfolio architecture, official authorization, chronology,
  material events, and one bounded current outside-in check of company scale
  or market/channel position when a credible source can materially calibrate
  the company core;
- `CO2`: unified official-first portfolio and selected-retailer corpus —
  authorization board, grids, union/reconciliation, exact PDP baselines,
  retailer-native facts, failures, overlap, and provider/corpus identity; never
  split retailers by actor; and
- `CO3`: mandatory customer/community, complete bounded review-corpus
  acquisition, and selected interpretation — retailer reviews and Q&A, bounded
  Reddit and qualified community routes, customer language, pain points,
  objections, complaints, usage contexts, workarounds, response patterns,
  syndication ceilings, and discriminating depth checks.

For review depth, keep Sephora on its existing source-specific capture policy.
For every selected non-Sephora retailer, default to source-labelled `Most
Recent`/newest when supported and record the actual ordering plus fallback. Bind
each corpus to observed provider evidence, tenant/store, and collection context;
never infer `Yotpo` from REVOLVE alone. Same-corpus sort windows are one corpus,
not independent customer evidence, and duplicate native IDs collapse to one
unique review. After baseline PDP coverage, account for every retailer listing
on a distinct-corpus board. Acquire one bounded onboarding window for each
distinct accessible corpus or record its typed no-review, not-exposed, blocked,
or unresolved identity outcome. Then select category-balanced corpora for
expensive interpretation; do not make hero selection the boundary of raw
customer-evidence acquisition.

Any pair/group dispatcher is mechanical and is not another evidence actor.
`CO1`-`CO3` use same-root collaboration under `CO0` unless a separately
authorized independent worktree is genuinely required. They create no further
actors. Company-owned authorization precedes retailer probing. `CO2` supplies
the reconciled breadth and selected-product pointers that `CO3` needs for depth.

Run those four actors through this lean execution protocol:

1. `CO0` validates the commission-stage board once, binds the shared roots and
   terminal output paths, and completes or validly reuses the SERP Phase 1
   competitor scout. It then dispatches `CO1`-`CO3` together with thin
   role-specific source capsules. `CO1` receives the relevant subject,
   competitor-identity, and claim questions; `CO2` receives the priced
   comparator and retail-relevance rows; `CO3` receives the full typed ledger,
   trigger-thread queue, mediator map, grid-capture queue, and cited-substitute
   watch list. A capsule also contains the bound question, the role's jobs and
   claim ceilings, the few owning-source pointers it needs, its upstream
   artifact dependencies, and its terminal return contract. Do not copy the
   controller's full conversation or unrelated source pack into every actor.
2. `CO1` resolves the company core and publishes its official-retailer
   authorization outcome and supporting evidence pointers at the bound terminal
   path; a typed absence or blocked result is a valid published outcome, not a
   probe blocker. `CO2` may prepare its locked retailer job set concurrently
   but does not probe a retailer until that published outcome is available.
   `CO3` begins its mandatory bounded customer/community scout concurrently,
   consuming the Phase 1 trigger-thread and mediator queues; its
   evidence-selected retailer depth waits for `CO2`'s reconciled breadth and
   selection pointers. Reddit/community capture is part of this specialist
   fan-out, not SERP Phase 2.
3. Each specialist plans its bounded work once, locks the deterministic job
   list that follows from the evidence, and runs compatible capture/projection
   jobs as a batch or bounded local loop without a model turn between ordinary
   items. Per-item raw packets, provenance, typed outcomes, and failures remain
   distinct. Existing commission producers such as retail portfolio onboarding,
   depth selection, and review linkage should consume the resulting manifests;
   this protocol creates no parallel evidence schema or orchestration runtime.
   Before retrying a review/Q&A adaptation failure, apply the grouped-family
   raw-corpus adjudication in the Retailer PDP Information-Extraction Standard;
   do not spend the retry when the preserved raw parents already satisfy that
   acceptance rule.
4. Specialists persist evidence as it is produced, then write one terminal
   role return that indexes the durable artifacts, completed and unresolved
   jobs, material failures, and follow-ups. They do not paste raw corpora into
   chat or send routine progress, readiness, hash, or release handshakes.
   Notify `CO0` early only when an observed blocker requires a controller or
   owner decision that would change the locked work.
5. `CO0` waits on completion or decision-requiring blocker events, not polling
   dialogue. After all terminal returns exist, `CO0` reads the load-bearing
   artifacts themselves once, resolves any actor-local correction in the same
   actor task, and runs SERP Phase 2 from the combined findings. Phase 2 owns
   only the targeted SERP return and decision lifecycle; it does not repeat the
   fan-out's native/community capture. `CO0` then writes the integrated
   acquisition record and seal. Only `CO0` owns user-facing run progress.

This protocol removes orchestration work, not evidence work. It does not cap
sources, jobs, tokens, or elapsed time; weaken route-specific failure
visibility; make a specialist return evidence without dereferencing its durable
artifacts; or turn a zero-yield customer/community route into permission to omit
`CO3`.

`CO3` is mandatory even when prior customer/community routes yielded nothing:
zero yield and blocked access are typed route results, not reasons to omit the
customer-understanding job. Its depth is adaptive. It always runs the bounded
customer/community scout and then expands only while another route or
discriminating check has positive expected decision value. Stop on supported,
contradicted, meaningfully bounded, or honestly blocked/gapped material seams —
not on a token or compactness target.

This is the default route for company Understanding. The detailed company-core,
retail-breadth, and customer/community role mapping below is the current US
consumer-beauty mapping. A materially different subject may rebind the
specialists' subject-specific jobs instead of pretending the selected-retailer
role applies, but it does not skip the Phase 1 -> fan-out -> Phase 2 ordering or
the mandatory customer/community job.

1. Bind `cycle_id`, `commission_id`, canonical phase, phase-specific question,
   intended consumer/use, scope, and the six outcome signals below.
2. Complete prerequisite and authority checks. Generate and validate the
   phase-specific commission-stage CSB before source-heavy work.
3. Resolve the selected sources through the repo map into Scanning/Capture
   authority. Before capture starts, pin each route to the current source-family
   contract and the banked recipe card or recon-index record when one exists.
   Resolve Ulta and Quora through their existing source-specific records,
   preserving each route's scope, maturity, and typed limitations; do not
   silently substitute generic browsing or rediscovery.
   For a company Understanding commission where offerings, retail presentation,
   or customer experience are material, preserve the prompt's bounded sequence:
   owned identity seed binding subject, categories, franchises, and known
    parents -> company-owned official retailer board and selected retailers'
    available grid surfaces -> deterministic union and reconciliation of exact listings with the
   owned candidates -> return to owned surfaces to close the complete publicly
   exposed denominator and typed gaps -> one baseline PDP for every reconciled
   exact retailer listing at each selected retailer -> complete bounded
   distinct-review-corpus onboarding board -> evidence-selected interpretive and
   Q&A depth. Owned evidence remains canonical identity authority;
    retailer grids are discovery and channel-expression evidence. Resolve
    Sephora explicitly, then select any officially named, route-admissible
    retailers that add material evidence; preserve exact typed failure instead
    of inventing a listing or completion credit. Use the common lean baseline,
    preserve full raw material, and retain source-visible retailer-native
    extensions. When Sephora is officially named and route-complete, include it
    and make it primary. Keep its typed outcome but use another complete working
    primary when it is blocked, unpinned, or incomplete. A named
   non-duplicative job must justify each expensive interpretive deepening, and
   there is no fixed interpreted-product count. The bounded onboarding board is
   a breadth obligation, not universal historical review capture. Do not
   require a full global SKU graph or an all-retailer/source-count quota.
   Preserve calibrated
   review-volume semantics, accepted residuals, non-claims, and upgrade trigger.
   Before selecting depth, run the portfolio breadth compositor (or prove the
   same fields through the existing coverage ledger): one owned-parent
    denominator, the company-owned retailer-authorization board, one typed
    outcome per selected retailer, one reconciliation per
   verified grid row, and one attempted exact-parent PDP disposition per
   non-bundle listing. Preserve every admitted baseline and every typed miss.
   A miss blocks acquisition only when that listing is strategic or
   decision-bearing for the bound question, carries a distinct material seam or
   corpus identity that the remaining baselines cannot support, or reveals a
   route-wide failure. A non-strategic middle-of-curve miss may be accepted as a
   named residual when the remaining evidence still supports the commissioned
   answer; no coverage percentage alone decides materiality. Duplicate
   placements, variant URLs, bundles/sets, ambiguity, unmatched rows, missing
   material variants, and route failures stay distinct.
   The compositor output is derived acquisition accounting, not a new ledger
   schema or product-role assignment.
4. Run authorized scanning and capture. For company Understanding, the internal
   order is mandatory: SERP Phase 1 after the validated board; `CO1`-`CO3`
   specialist fan-out using Phase 1's typed outputs; all specialist terminal
   returns; then the targeted SERP Phase 2 return. Record every selected route,
   route result, scan/capture receipt, source/provenance locator, and real failure.
   Scanning's current MGT operating model owns continuation and closure against
   the bound phase question. Apply its lead-to-angle-to-material-seam rule:
   evidence-revealed, decision-relevant angles receive a discriminating check,
   and every material seam is supported, contradicted, meaningfully bounded, or
   honestly blocked/gapped before sealing.
5. If a material required-route or capture failure is load-bearing and a
   plausible owner action can materially unblock it, issue one consolidated
   owner-unblock escalation during the run, before sealing:

   ```yaml
   owner_unblock_escalation:
     affected_question_or_success_signal:
     route_attempted:
     observed_blocker:
     smallest_owner_action_needed:
     remains_blocked:
   ```

   This is event-triggered, not a checkpoint for every route issue. If the owner
   resolves it, resume acquisition and record the real route receipt, using at
   most one retry for each failed material route. If it remains unresolved,
   keep acquisition blocked or record the owner's explicit narrowing of the
   commission. Never carry a fixable load-bearing capture failure forward
   merely as a final-report caveat, silently omit it, infer absence from it, or
   proceed as complete. A repair may stay delta-scoped, but any transition from
   a blocked acquisition seal to a passing seal requires `CO0` to fresh-read
   the current specialist artifacts and integrated record and re-adjudicate the
   whole acquisition gate. Every material residual remains load-bearing until
   supported, contradicted, meaningfully bounded, or honestly blocked/gapped;
   this includes newly exposed or unmatched rows, URL-only material claims,
   machine-readable failures, and evidence-revealed contradictions, not only
   the last repaired blocker.
6. Write the phase acquisition seal below. Context compaction may discard chat,
   but not this artifact.

```yaml
phase_acquisition_seal:
  cycle_id:
  commission_id:
  phase: understanding | problem_framing
  turn: acquire_and_seal
  bound_question:
  intended_consumer:
  intended_use:
  phase_scope:
  commission_board_locator:
  outcome_signals:
    - question_fit
    - evidence_foundation
    - reasoning_quality
    - honest_uncertainty
    - implications_and_foresight
    - communication_efficiency
  resolved_routes:
    - source_or_venue:
      information_job:
      required: true | false
      route_identity:
      route_authority:
      recipe_or_recon_pointer:
      disposition: used | reused_evidence | skipped_with_rationale | blocked
  scan_receipts: []
  capture_receipts: []
  provenance_index: []
  material_gaps_and_failures: []
  seal_state: SEALED_READY_FOR_DELIVER | BLOCKED_ACQUISITION_INCOMPLETE
  acquisition_gate: pass | blocked
  deliver_allowed: true | false
  sealed_at:
```

The seal is valid for Deliver only when `seal_state:
SEALED_READY_FOR_DELIVER`, `acquisition_gate: pass`, and `deliver_allowed:
true`, and when every required route has a supported disposition and receipt or
an honestly typed non-material blocking result. Any material blocking result,
or a required route that was skipped, silently substituted, incompletely
captured, or described as exhausted without the matching route evidence,
forces the blocked state.

For company Understanding, the required route accounting includes SERP Phase 1
and SERP Phase 2. Phase 2's disposition, decision receipt, consumed specialist
artifact provenance, and any material block must resolve through the existing
`resolved_routes`, receipt, `provenance_index`, and
`material_gaps_and_failures` fields. Phase 1 output or specialist completion
alone cannot authorize the seal.

For selected-retailer PDP breadth, `incompletely captured` is a materiality
judgment, not an automatic all-or-nothing denominator rule. Every exact listing
still requires an attempted disposition. A typed miss may remain an accepted
route residual only when fresh evidence shows that it is non-strategic for the
bound question, adds no distinct decision-bearing seam or required corpus
identity, does not indicate a route-wide defect, and the retained baselines can
still support the intended answer. Strategic, decision-bearing,
corpus-identity-bearing, or route-systemic misses remain blocking.

Route disposition is necessary but not sufficient. A touched lens, zero-yield
route, exhausted route list, or absence of a promotable candidate cannot
authorize Deliver. If a material seam remains unresolved because a commission
limit or source boundary stops acquisition, or if the assembled evidence cannot
support a decision-useful answer to the bound question, use
`BLOCKED_ACQUISITION_INCOMPLETE`; do not lower the answer standard to pass the
seal.

### Turn B — Deliver

Start in fresh context and load the phase acquisition seal, not the accumulated
capture chat. Verify its identity, canonical phase, bound question/use, seal
state, route receipts, provenance, and material gaps before synthesis. If the
gate is blocked or the artifact is incomplete, stop and return to Acquire &
Seal; do not issue a nominal deliverable.

Deliver compresses and communicates the acquired evidence. Its succinctness
discipline is never grounds to under-acquire during Acquire & Seal.

When the gate passes, synthesize the phase deliverable, craft the human report
or framing artifact, validate it under the owning contract, and hand off the
next phase or step. Every evidence, coverage, provenance, and route-exhaustion
claim must resolve to the seal. Preserve the final deliverable as the sealed
phase output before commissioning post-delivery review.

For company Understanding where offerings or retail are material, Deliver makes
the breadth-first substrate visible in Section 5, `Portfolio And Retail
Architecture`. Its ordered subsections and compact matrices show the owned
denominator, product/claim/price structure, selected-retailer corpus,
evidence-selected depth, outside-in portfolio interpretation, and strategic
positioning/markets/channels. The section synthesizes the sealed ledgers; it does
not replace acquisition accounting or award completion from headings.

For Understanding, derive the prompt's optional retailer-review approval signal
only when the commissioned question gives it a named decision-material job and
the seal resolves to row-level ratings, source-visible incentive posture, and a
reproducible corpus boundary. Preserve disclosed incentivized rows in raw
capture but exclude them from the primary derived view. Report the eligible
denominator and excluded count; call unlabelled rows `not marked
incentivized`, never organic. Express both percentage fields to one decimal
using round-half-up. If the route yields only a headline aggregate or an
unreproducible slice, omit the signal and preserve the gap. This is
conditional synthesis, not a mandatory acquisition step or completion gate.

When the retailer evidence exposes age, skin type, skin concern, or similar
attributes, distinguish retailer-authored product metadata from reviewer
self-report. Any reviewer-attribute summary states the captured-corpus and
attribute-reporting denominators, missingness or coverage, selection/filter
basis, and visible incentive posture. It describes the reporting subgroup only;
sample size does not convert that subgroup into a customer-population estimate.

Understanding Deliver produces the decision-neutral company-intelligence
artifact. Problem Framing may acquire only decision-specific supplements to the
Understanding substrate, never a general re-scan; its eventual human output
shape remains separately review-bound and is not defined here.

Two turns are the normal operating budget, not a hard completion cap. A blocked
Acquire & Seal remains blocked and may require another acquisition attempt; it
does not count as a successful Deliver.

### Six Outcome Signals

The cycle optimizes toward these signals without turning them into a score,
required report sections, six extra gates, or repeated receipt fields:

1. **Question fit** — answer the bound question for the intended reader/use; do
   not drift toward whatever was easiest to collect.
2. **Evidence foundation** — trace load-bearing judgments to dated evidence,
   check critical independence/currentness, and record required routes and
   failures honestly.
3. **Reasoning quality** — make the evidence-to-judgment chain reconstructable;
   separate facts, assumptions, and judgments; address serious alternatives and
   disconfirming evidence when relevant.
4. **Honest uncertainty** — put confidence and material gaps where they affect
   judgments and name useful change conditions; do not force probability
   language onto descriptive facts.
5. **Implications and foresight** — explain what findings mean and which
   observable developments would change the view; do not force unsupported
   forecasts or recommendations.
6. **Communication efficiency** — make key judgments easy to find, order the
   body by importance, remove repetition/padding, and keep audit detail
   available without dominating the narrative.

Production priority:

1. **Non-negotiable foundations:** question fit, trustworthy evidence, and
   honest uncertainty. Do not trade them for prose, apparent decisiveness,
   speed, or implications. A real acquisition or evidence failure stays
   visible and may block Deliver.
2. **Primary value focus:** once the foundations hold, spend the largest
   analytical effort on sound reasoning and useful meaning/implications.
3. **Delivery discipline:** only then compress and clarify. Communication
   efficiency must not manufacture substance or dominate effort.

In one line: **optimize for decision usefulness under an integrity floor:
secure the question/evidence/uncertainty foundations; then maximize reasoning
and useful implications; then compress for clear delivery.**

Satisfy the signals through real task evidence and function, not headings,
labels, citation volume, ritual sections, forced forecasts, repeated confidence
labels, or padding. Production receives these targets and this priority order,
never numerical weights, bands, caps, or score-optimization instructions.

## Post-Delivery Adversarial Review Handoff

After a phase deliverable is sealed, commission an independent adversarial
review against the accepted post-delivery six-dimension rubric and its
applicable hard caps. The rubric authority is deferred until separately
adopted; do not reconstruct it from this production contract or create a
duplicate rubric here.

The review package must include:

- the final phase deliverable;
- the phase acquisition seal and provenance index;
- the bound question, intended consumer, and intended use;
- material gaps and failures; and
- the route receipts needed to verify evidence and exhaustion claims.

The reviewer evaluates actual function and evidence, not the presence of
headings, labels, citation volume, or ritual content, and explicitly tests for
rubric gaming. The evaluation includes the Forseti-specific rule that a report
presenting required capture routes as exhausted when the canonical route was
skipped or silently substituted is flagged as rubric gaming rather than scored
as a clean report. Any resulting numeric cap is applied only by the separately
adopted post-delivery rubric; no cap value belongs in this production contract.

Return the total number, the six-dimension profile, and all triggered flags or
caps; never return a lone number. Weights, bands, and caps remain provisional
working evaluation authority, not production instructions or a permanent
readiness gate unless separately adopted. This handoff defines only the seam
and required inputs; it does not create the numerical rubric, authorize the
reviewer to patch, or change the report layout.

## Operating Sequence

Use this sequence to create the CSB inside Acquire & Seal. The broader cycle
gate above controls whether Deliver may begin.

1. Read the prompt and this playbook.
2. Preserve `mode: backtest | forward`. Determine `commission_profile`:
   - default a one-company Brand or Org subject, including unresolved Brand/Org
     identity, to `company_competitive_intelligence`;
   - otherwise use `standard_signal_board` unless explicitly overridden.
3. Default `time_posture` to `recency_first`. Use `longitudinal` only when the
   commission explicitly asks about change, recurrence, or trajectory and
   declares both a period and rationale.
4. Check profile-specific required inputs. Return the prompt's intake scaffold
   if any are missing; intake-only output is not a validator target.
5. Include an item only when its named job can materially change the action,
   action ceiling, rival assessment, or hold condition and no equal-or-better
   included item performs that job. Use exclusion or `not_applicable` records
   for dominated routes.
6. Generate exactly the selected profile's Sections 1-10. A commission-stage
   company board uses `COMMISSION_SEALED_PRE_SCAN` and cannot claim acquired
   evidence; a completed company report later carries the prompt-defined
   `## Executive Intelligence Brief` preamble before Section 1. Save the exact
   output to a temporary file or bound durable artifact and run the validator.
   For an Intelligence Cycle, this is the commission-board input to the phase
   acquisition seal, not the completed seal itself. If validation fails, repair
   the output or report its finding codes. Do not run downstream work from a
   failing board.
7. For company Understanding, run the SERP competitor scout pass before
   authoring specialist commissions:
   `docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md`
   (its post-fan-out targeted return is
   `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`).
   The ordering is load-bearing, not ceremonial: `vs {rival}` cannot run
   without a harvested name, so seeds must land and be harvested before
   fan-out; skipping the pass forces specialists back onto hand-picked
   rivals, which is the confirmation loop the scout exists to kill.
   The typed ledger and queues feed the role-specific fan-out capsules. The
   commission-stage Section 8 carries the information job or typed gap; a
   completed Section 8 consumes the final Phase 2 ledger and decision receipt,
   not the interim Phase 1 ledger. The pass is skippable only when a current
   scout ledger for this subject already exists — record that reuse — and its
   absence is a typed gap, never a silent omission.
   Temporary Summer Fridays constraint: before authoring any Summer Fridays
   company commission, the dispatcher must read
   `docs/workflows/serp_scout_pass_calibration_predeclaration_v0.md` and bind
   its obligations into the commission handoff; remove this constraint when
   that note's adjudication is appended.
   Bind the following requirements into the role capsules; their execution
   begins at step 9. Route retail, customer, and claims research first.
   Before optional deepening, resolve the prompt's small high-yield core through
   the existing ledgers. A material unresolved core job blocks the acquisition
   seal; other remainders stay typed gaps and non-claims. When retail is material,
    commission an owned identity seed, establish the company-owned official
    retailer board, classify Amazon authorization separately from marketplace
    presence, resolve Sephora explicitly, and select and attempt at least four
    company-authorized, target-market, route-admissible third-party retailers
    when four exist. Favor distinct evidence venues; do not count the
    company-owned DTC site or fill the floor with an unauthorized, duplicate,
    or market-unpinned venue. If fewer than four qualify, select all and record
    `AUTHORIZED_RETAILER_SHORTFALL` with the observed count and reasons. Acquire
    each selected grid surface,
    reconcile its listing union with owned candidates, then return to owned
    evidence to close the denominator. Owned
   evidence remains canonical identity authority. Attempt one common-floor
   baseline PDP for every reconciled exact retailer listing and preserve each
   admitted baseline or typed miss. Apply the prompt's
    Sephora-primary rule when it is officially named and route-complete, but do
    not let primary status excuse another selected retailer's baseline. Preserve typed route failures without
   completion credit and retain retailer-native fields when source-visible.
   A typed non-strategic middle-of-curve miss may be sealed as an accepted
   residual only under the materiality rule above; strategic, distinct-seam,
   required-corpus, and route-systemic misses still block. Only after
   exact-parent PDP breadth is sealed, bind every selected-retailer
   listing to its observed review-corpus identity and acquire one bounded
   onboarding window per distinct accessible corpus, or preserve a typed
   no-review/not-exposed/blocked/unresolved result. Then select expensive
   interpretive and Q&A depth for category-balanced evidence jobs. Each
   interpretive deepening needs a named non-duplicative job, there is no fixed
   interpreted-product count, and retailer counts remain separate rather than
    becoming sales. Only company-owned authorization lets Amazon count toward
   the four-retailer floor. A verified-but-not-company-authorized Amazon route
   may supplement evidence with that limitation attached; an unverified route
   remains a discovery pointer. Treat Amazon, when selected, as a query-bound
   ranked-search window, not a guaranteed complete or authorized-only catalog;
   projection capability never substitutes for route admission. Point-in-time
   retailer metrics are traction proxies, not sales, share, or trend. Preserve analysis-enablement inputs,
   stop-or-gap rules, review-
   volume claim guards, accepted residuals, non-claims, and upgrade trigger. This
   orders attention; it is a bounded retailer-selection floor, not an
   all-retailer crawl, proof hierarchy, full historical review crawl,
   full-SKU-graph requirement, new ledger schema, or Scanning execution
   instruction. Commission archives, supply, ads/creators,
   competitors, search trends, and similar deepening only for a named unresolved
   inference job.
8. For a recurring or actively radarred source family, put a lake-first
   preflight in the downstream request: relevant Silver/current view, then
   packet or catalog inventory, then raw material when necessary. Treat the
   result as reuse/freshness/coverage context, not current-world proof.
9. Route the role-specific requests to `CO1`-`CO3`, and route their typed source
   requests to Scanning or Capture under those lanes' own authority. Do not
   execute retrieval from this playbook. Scanning decides marginal acquisition,
   dominance, and closure; Capture fulfills the bounded request or returns typed
   failure/route exhaustion. Reddit/community acquisition runs inside `CO3`.
10. After every specialist reaches a terminal return, `CO0` dereferences the
    load-bearing artifacts and runs the post-fan-out targeted SERP return:
    `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`.
    Phase 2 derives each query from a named specialist finding, applies the
    decision lifecycle, and returns the consolidated ledger, decision receipt,
    provenance, and material blocks. It does not repeat native capture.
11. For an Intelligence Cycle, assemble the phase acquisition seal only after
    the Phase 2 terminal result and all owning Scanning/Capture work return. A
    typed acquisition failure remains visible and blocks Deliver when material;
    it is not converted into completion.

## Validator Command

From the repo root:

```powershell
python -B .agents\hooks\check_commission_signal_board_output.py <board-output-file>
```

Selftest:

```powershell
python -B .agents\hooks\check_commission_signal_board_output.py --selftest
```

Focused pytest suite:

```powershell
cd forseti-harness
python -B -m pytest -q -p no:cacheprovider tests\unit\test_commission_signal_board_output_validator.py
```

## Validator Applicability

Run the validator only against a full output with profile-specific Sections
1-10 in canonical order.

- `standard_signal_board` requires the existing `Signal Board Rows`,
  `Demand-Classifier Handoff Packet`, and `Board Status And Run Boundary`.
- `company_competitive_intelligence` requires `Company Commission And Identity
  Receipt` through `Completion Ledger And Run Boundary` and must not contain a
  classifier handoff. This includes commission-stage company boards
  (`run_boundary: COMMISSION_SEALED_PRE_SCAN`): they are full ten-section
  outputs and are validated; the validator enforces that the commission-stage
  boundary coexists with `not_checked` coverage rows and that
  `commissioned_not_yet_run` scout statuses appear only at that stage. It also
  cross-checks each Reddit/Quora scout status against the corresponding
  coverage-row status and yield so the completion ledger cannot claim a result
  the route ledger did not earn. For a completed report, the contract-required
  `## Executive Intelligence Brief` before Section 1 is compatible with the
  validator: the checker scans only numbered `###` Sections 1-10 and
  deliberately does not enforce synthesis quality.

Do not run it against `NEEDS_COMMISSION_INTAKE` or `NEEDS_CUTOFF_DATE`.

## What The Validator Checks

For `standard_signal_board`, the established structure, row vocabulary,
backtest cutoff, engagement-overclaim, and classifier-handoff checks remain
unchanged.

For `company_competitive_intelligence`, the validator checks:

- one-company identity and default profile routing;
- `mode` and orthogonal `time_posture`;
- deterministic recency tiers and age-use rules;
- declared period and rationale for `longitudinal`;
- source-family coverage, the Reddit `mandatory_bounded_scout` compatibility
  row, the initial-proving Quora compatibility row, category-aware forum
  discovery, typed gaps, and justified `not_applicable`. The Reddit/Quora rows
  are search-hygiene considerations: they may document non-selection and do not
  authorize acquisition or earn completion credit without a named
  non-dominated information job;
- observation-level URL, publisher, publication/event/access dates, evidence
  status, source class, fact domain, and syndication group;
- shared source-family vocabulary, typed `effective_time_precision` and
  `age_anchor_basis`, current-page versus dated-event separation, and no old
  evidence relabeled current;
- community evidence as external/customer evidence only;
- decision-neutral company lenses and prohibited GTM keys;
- Company Surface rows as `candidate_only` and `not_imported`;
- completion ledger, explicit gaps/requests, no arbitrary caps, typed
  `run_boundary` and `next_authorized_step`, Reddit/Quora scout-status
  consistency with their coverage rows, and no classifier handoff;
- document-wide `OBS-###` references resolve to observation-ledger rows
  (`dangling_observation_reference`);
- the shared engagement/resonance overclaim ban, which applies to both profiles.

## What A Pass Means

A standard pass means its classifier-handoff rows are mechanically eligible
under the board's own row table. A company pass means the report is mechanically
complete under the conditional company planning contract. Neither pass means:

- evidence is true;
- evidence was retrieved;
- demand exists;
- the board is exhaustive;
- graph construction is complete;
- acquisition is complete or the participant packet is frozen;
- classifier mapping is correct;
- buyer proof, validation, readiness, forecast, or client-facing claims are allowed.

## How Agents Discover This Lane

Agents should discover this playbook from:

- the Commission Signal Board prompt `open_next`;
- the repo map Product Anchor Files section;
- the repo map Active Hooks / Manual Checkers section;
- downstream wrappers or handoffs that name this playbook before board generation.

If an agent sees "Commission Signal Board", "commissioning board", or
"commission board output", it should open this playbook before running or
validating the board.

If an agent sees "Forseti Intelligence Cycle", "Understanding phase", "Problem
Framing phase", "Acquire & Seal", or "Deliver", it should open this playbook
before commissioning or executing the phase.

## Current Non-Goals

- Do not add CI or pre-commit enforcement until board artifact paths are
  standardized.
- Do not make the validator run on chat-only intake scaffolds.
- Do not turn the validator into demand classification, graph scoring, evidence
  weighting, retrieval, or proof review.
- Do not treat validator pass as approval or readiness.
- Do not implement or infer a numerical report score from the six outcome
  signals.
- Do not redesign the company-report section order while its external structure
  review remains open.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Commission Signal Board operation now routes two conditional profiles while
    preserving mode backtest|forward. Agents default one-company Brand/Org work
    to company_competitive_intelligence, default time posture to recency_first,
    use longitudinal only with period and rationale, and validate only a complete
    profile-specific output. Company reports have no classifier handoff.
  trigger: workflow_authority
  related_triggers:
    - validation_philosophy
  controlling_sources_updated:
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - .agents/hooks/check_commission_signal_board_output.py
    - forseti-harness/tests/unit/test_commission_signal_board_output_validator.py
    - forseti-harness/tests/fixtures/commission_signal_board_outputs/
    - docs/workflows/forseti_repo_map_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/hooks/check_commission_signal_board_output.py
    - forseti-harness/tests/fixtures/commission_signal_board_outputs/
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        AGENTS.md already routes Forseti project rules to the overlay and durable
        docs; adding a Commission Signal Board special case would fork the
        playbook.
    - path: .agents/workflow-overlay/validation-gates.md
      reason: >
        The validator remains manual/local, not a CI or hook gate. The
        enforcement-placement principle already lives here; no active validation
        gate is being registered yet.
    - path: .agents/workflow-overlay/source-loading.md
      reason: >
        Source-loading packs are unchanged; this playbook is a run sequence for
        an existing prompt and checker.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        Prompt-orchestration mechanics are unchanged; the canonical prompt
        applies the full contract without forking prompt-policy.
  stale_language_search: >
    rg -n "Commission Signal Board|commission_signal_board|check_commission_signal_board|NEEDS_COMMISSION_INTAKE|validator target|classifier handoff"
    docs .agents forseti-harness -S
    and
    rg -n "run the validator|validator applies|manual/local|NOT hook-wired|intake-only"
    docs .agents forseti-harness -S
    (refresh during implementation validation)
  stale_language_search_result: >
    Executed 2026-07-16. The scoped profile/posture/venue/classifier search
    returned expected live-contract and non-claim hits; the exact forbidden
    posture search returned only quoted receipt literals, not live contract
    usage. Live instructions preserve the standard classifier handoff, omit it
    from company reports, and do not treat validator pass as truth, demand
    classification, proof, graph weight, recency proof, or readiness.
  non_claims:
    - not validation
    - not readiness
    - not CI enforcement
    - not pre-commit enforcement
    - not demand classification
    - not evidence retrieval
```

## Direction Change Propagation — Exact PDP Materiality

```yaml
direction_change_propagation:
  doctrine_changed: >
    Exact retailer-listing breadth remains an attempt-and-disposition
    obligation, but a typed PDP miss blocks only when it is strategic,
    decision-bearing, distinct-seam, required-corpus, or route-systemic. A
    freshly supported non-strategic middle-of-curve miss may be an accepted
    residual; percent coverage alone is not the decision rule.
  trigger: workflow_authority
  related_triggers: [architecture_doctrine]
  controlling_sources_updated:
    - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  downstream_surfaces_checked:
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
    - docs/workflows/summer_fridays_understanding_dogfood_20260725_p10/coordinated/acquisition_seal.md
  intentionally_not_updated:
    - path: prompt structure, validator, and historical raw packets
      reason: >
        The prompt surfaces require typed acquisition accounting without
        encoding the former mechanical denominator rule, and historical packet
        observations remain immutable.
  stale_language_search: >
    rg -n "one verified raw PDP baseline|full-raw common-floor|every reconciled
    exact retailer listing|complete selected-retailer exact PDP" forseti docs
    .agents
  non_claims:
    - not permission to skip attempts
    - not a numerical threshold
    - not validation or readiness
```

Older receipts archived verbatim in `docs/decisions/dcp_receipts_archive_v0.md`.
