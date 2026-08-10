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
  - Commissioning or executing an Understanding or Deliver phase.
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
| Phase deliverable | Understanding or Deliver synthesis produced only from its governing acquisition gate: Understanding requires its own passing phase seal; Deliver requires the passing Understanding seal plus a typed capture return for every consumed supplement | Profile-dependent |
| Scanning, Capture, or classifier work | Downstream execution under its owning spine | No |

CSB owns the commission profile, source-family requirements, time posture, and
typed gaps/requests. Scanning owns the intelligent walk. Capture owns venue
access and preservation adapters. This playbook does not authorize downstream
runtime. CSB defines decision-material information jobs and candidate routes; it
does not freeze the participant packet, decide final inclusion, or declare
acquisition complete.

## Forseti Intelligence Cycle

Commission future one-company intelligence work as a **Forseti Intelligence
Cycle**. The phases are **Understanding** followed by **Deliver**. `Problem
Framing` is the Deliver phase's historical name (`Problem` was its informal
shorthand); problem framing survives as the Deliver phase's first synthesis
step. Do not use bare `Phase 1` / `Phase 2` language for a future commission.
Reading rule for this document set: a bare `Phase 2` always denotes the
internal SERP Phase 2 lane, never the Deliver phase; `Phase A` appears only in
historical names and glosses, never as a live phase. Historical artifacts keep
their original names and phase labels.

Each phase has two possible operator/model turns. Scope does not auto-expand:
an owner instruction that says **Understanding** or uses historical **Phase A**
language without also naming a synthesis deliverable commissions **Acquire &
Seal only** and stops after the seal. A passing seal makes the Synthesize turn
eligible but does not authorize or start it. Synthesis requires an explicit
current commission or a separately authorized follow-up.

### Turn Objectives

The turns optimize different things:

- **Turn A — Acquire & Seal:** maximize decision-useful completeness under the
  integrity floor. Continue until every material information job is supported,
  contradicted, meaningfully bounded, or honestly blocked/gapped. Compactness,
  actor count, and token minimization are not acquisition success criteria.
- **Turn B — Synthesize:** after the acquisition gate passes, apply Smallest
  Complete Intervention to the human artifact. Preserve decisive evidence,
  counterevidence, uncertainty, provenance, reversal conditions, and the next
  action while removing repetition and audit detail that does not belong in the
  decision surface.

Turn A/Turn B are turns inside each canonical phase; they do not rename
Understanding and Deliver as unqualified Phase A/Phase B.

### Turn A — Acquire & Seal

#### Default US Consumer-Beauty Understanding Route

The default coordinated route has exactly four evidence actors:

- `CO0`: whole-run Chief Architect, integration, durable-record owner, and
  acquisition-seal owner;
- `CO1`: owned company and high-yield core — identity, ownership, leadership,
  offering/portfolio architecture, official authorization, chronology,
  material events, mandatory Google Ads Transparency Center and Meta Ads
  Library attempts after exact advertiser identity is bound, and one bounded
  current outside-in check of company scale or market/channel position when a
  credible source can materially calibrate the company core;
- `CO2`: unified official-first portfolio and selected-retailer corpus —
  authorization board, grids, union/reconciliation, exact PDP baselines,
  retailer-native facts, failures, overlap, and provider/corpus identity; never
  split retailers by actor; and
- `CO3`: mandatory customer/community, complete bounded review-corpus
  acquisition, and selected interpretation — retailer reviews and Q&A, bounded
  Reddit and qualified community routes, the current weekly Reddit lake read,
  conditionally licensed native TikTok/Instagram/YouTube items and TikTok Shop,
  customer language, pain points, objections, complaints, usage contexts,
  workarounds, response patterns, syndication ceilings, and discriminating
  depth checks.

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

For broad decision-neutral company Understanding, apply
`broad_company_understanding_v1` from the prompt-structure authority. Its
numeric values are anti-token entry floors only. The seal still requires the
Scanning closure test, independence/echo adjudication, material-seam
dispositions, and two final practical batches with no material incremental
value. Do not copy the profile into a run-specific quota or stop when a floor is
first reached.

For a consumer brand where product/customer experience is material, select
`broad_consumer_brand_understanding_v3` instead and record that choice in the
commission receipt before scanning, then retain it in the completed company
record. Its v4 depth ledger applies the same
aggregate anti-token floors except for a 40-thread Reddit/forum floor, but
completion is organized around material product pain/delight axes. Forty
threads are a minimum floor, never a completion target. Every passing run
terminally accounts the bounded candidate set in `reddit_candidate_frontier`.
Separately, every material axis must be decision-mature through either strong
evidence or route-bounded source exhaustion. The latter permits only bounded
observation, never a strong qualitative claim. A usable new thread stays visible
but does not reopen an axis unless it changes a decision through a typed material
addition. Each axis closes on two later, genuinely different live continuation
families with no material addition affecting that axis. Fewer than 40 usable
unique threads additionally requires the proven floor exception; reaching 40
never stops an axis that remains materially open. `CO3` codes the eligible
deduplicated retailer rows
to axis-specific and overall explicit choice outcomes, tags social-source
relationship, and returns source IDs rather than prose-only counts. `CO0`
integrates those rows with distinct-origin external, community, and creator
support. Multiple posts from one creator and multiple units from one publisher
receive one corroboration-strength credit. Do not promote
official direction, retailer-operated content, disclosed paid/affiliate posts,
or relationship-unknown posts as independent creator corroboration. External
axis support also requires an explicit apparently-independent relationship and
a consumer-editorial or trade-press source type; company and transaction
profiles remain context, not customer corroboration.

Any pair/group dispatcher is mechanical and is not another evidence actor.
`CO1`-`CO3` use same-root collaboration under `CO0` unless a separately
authorized independent worktree is genuinely required. They create no further
actors. Company-owned authorization precedes retailer probing. `CO2` supplies
the reconciled breadth and selected-product pointers that `CO3` needs for depth.

Run those four actors through this lean execution protocol:

`CO0` must be the top-level controller with three worker slots available before
dispatch. If that placement or capacity is absent, stop before capture with
`BLOCKED_CONTROLLER_CAPACITY`; do not serialize the specialists or accept an
interim checkpoint as a terminal return. After the question and commission
board are bound, but before the first network capture, record the route
capability preflight in the acquisition seal: Google primary plus durable
cooldown state and any ready persistent fallback; the read-only Reddit weekly
lake reader; both mandatory ad-transparency routes; and the conditional TikTok
Shop route. The first real Phase 1 seed is the Google health observation; do
not spend a separate sacrificial query.

1. `CO0` validates the commission-stage board once, including required Google
   Ads Transparency Center, Meta Ads Library, and Reddit weekly-lake rows,
   binds the shared roots and terminal output paths, completes the capability
   preflight above, and completes or validly reuses the SERP Phase 1
   competitor scout. Under route 1.2.0, `CO0` first terminally dispositions
   every surfaced frame row as `core_fanout`, `bounded_watch`, or
   `rejected_before_fanout`. Core rows require exact product/job binding and
   two independent comparison origins across two source roles; SERP supplies
   discovery, never one of those confirmation origins. It then dispatches
   `CO1`-`CO3` together with thin
   role-specific source capsules. `CO1` receives the relevant subject,
   competitor-identity, and claim questions; `CO2` receives the priced
   comparator and retail-relevance rows; `CO3` receives the full typed ledger,
   trigger-thread queue, mediator map, grid-capture queue, and cited-substitute
   watch list. A capsule also contains the bound question, the role's jobs and
   claim ceilings, the few owning-source pointers it needs, its upstream
   artifact dependencies, and its terminal return contract. Do not copy the
   controller's full conversation or unrelated source pack into every actor.
   This is a mechanical dispatch gate, not a narrative ordering preference.
   Immediately before dispatch, fresh-read the same-cycle capability-preflight
   and Phase 1 artifacts and verify `checked_before_network_capture: true`, a
   terminal or validly reused Phase 1 receipt, and non-empty typed ledger and
   role queues. Without all three, do not start any specialist. If one already
   started, interrupt it and quarantine its output; exclusion does not repair
   preflight chronology or authorize a passing seal for that cycle.
2. `CO1` resolves the company core and exact paid-advertiser identities,
   attempts both mandatory public ad-transparency routes, and publishes its official-retailer
   authorization outcome and supporting evidence pointers at the bound terminal
   path; a typed absence or blocked result is a valid published outcome, not a
   probe blocker. `CO2` may prepare its locked retailer job set concurrently
   but does not probe a retailer until that published outcome is available.
   `CO3` begins with the read-only current weekly Reddit lake result, then runs
   its mandatory bounded customer/community scout, consuming the Phase 1
   trigger-thread and mediator queues. Before Phase 2 it pipelines two discovery
   lanes. The source-neutral lane runs a bounded unrestricted-domain
   brand/product review baseline and then claim-directed editorial, specialist,
   retailer, and comparison checks. Search results and AI-generated search
   summaries remain pointers until their source-native bodies are captured and
   admitted. The candid community lane runs the proven high-yield Reddit query
   families in this order: balanced brand-plus-axis;
   behavior/consequence/displacement; a bounded consumer-native product-name or
   shorthand probe without the brand where identity is unambiguous; and
   condition/post-use. Generic names receive a category or use-case qualifier.
   Run the brandless probe for a bounded set of hero products by default; admit
   a non-hero product only when already captured evidence exposes a material
   axis, condition, behavior consequence, competitor destination,
   contradiction, or sampling-risk question for it. Never turn the family into
   a catalog-wide crawl. Add a community-diversity family only when the admitted
   evidence is concentrated.

   `CO3` may begin its unrestricted source-neutral baseline immediately. It
   begins retailer-review-seeded claim-directed checks only after `CO2`
   publishes reconciled breadth and selection pointers. A material signal in
   either discovery lane launches only a bounded counterpart check for the same
   axis, segment,
   condition, consequence, or competitor destination. It never mirrors every
   query across sources or waits for a whole lane to finish before queueing a
   qualified source-native capture. Each family and candidate remains separately
   accounted. Company-owned and DTC pages provide official facts and claims, not
   independent customer corroboration. Reddit/community and source-neutral
   customer capture are part of this specialist fan-out, not SERP Phase 2.
3. Each specialist plans and locks one deterministic batch at a time, then runs
   compatible capture/projection jobs without a model turn between ordinary
   items. After each batch, it applies the Scanning continuation test and may
   add the next bounded batch when acquired evidence exposes a material
   frontier. Reaching the initially planned list or a numeric floor is not a
   terminal condition. Per-item raw packets, provenance, typed outcomes, and
   failures remain distinct. Existing commission producers such as retail
   portfolio onboarding, depth selection, and review linkage should consume the
   resulting manifests; this protocol creates no parallel evidence schema or
   orchestration runtime.
   Before retrying a review/Q&A adaptation failure, apply the grouped-family
   raw-corpus adjudication in the Retailer PDP Information-Extraction Standard;
   do not spend the retry when the preserved raw parents already satisfy that
   acceptance rule.
   For the consumer-brand profile, the customer-evidence return also includes
   the hash-pinned row coding view. Its denominator reconciles every admitted
   corpus into eligible text-bearing rows plus excluded no-usable-text rows;
   its row records carry review identity, a product context declared by that
   corpus, incentive state, normalized axis codes with axis-specific choice
   outcomes, overall choice outcomes, and source-row references.
   Same-corpus and cross-corpus deduplication precede incidence. Keep retailer
   results separate unless their boundaries and methods are comparable.
   The same return comment-codes every usable independent Reddit/forum thread
   to product context, axes, contribution, choice, alternative, explicit
   outcome, source reference, and parser limitation. Exact duplicate threads
   collapse. Related same-topic threads remain visible as corroborating or
   sharpening volume even when they add no distinct-origin strength credit.
4. Specialists persist evidence as it is produced, then write one terminal
   role return that indexes the durable artifacts, completed and unresolved
   jobs, material failures, and follow-ups. They do not paste raw corpora into
   chat or send routine progress, readiness, hash, or release handshakes.
   A specialist terminal is single-writer: after its hash is returned, `CO0`
   reads but never edits it. An actor-local correction goes back to that same
   specialist, which replaces its own terminal and returns the new hash.
   Notify `CO0` early only when an observed blocker requires a controller or
   owner decision that would change the locked work.
5. `CO0` waits on completion or decision-requiring blocker events, not polling
   dialogue. After all terminal returns exist, `CO0` reads the load-bearing
   artifacts themselves once, resolves any actor-local correction in the same
   actor task, runs the controller-owned campaign-evidence integration job
   (route `campaign_evidence_integration`, phase `campaign_integration`; see
   the route-1.1.0 subsection below), and then runs SERP Phase 2 from the
   combined findings, including the integration view's relationship-typed
   creator-comparison emissions. Phase 2 owns only the targeted SERP return
   and decision lifecycle. Its primary competitor output explains, axis by
   axis, why the observed evidence favors the subject, the competitor, a
   conditional split, or no conclusion; the final comparator role is derived
   after that explanation. It does not repeat the fan-out's native/community
   capture or produce a recommendation, market conclusion, or Deliver
   artifact. First hash-pin the complete axis
   inventory. For each material consumer-brand axis, Phase 2 then runs one
   adaptive corroboration/segmentation goal, one comparison/switch/value goal,
   and one disconfirmation/strongest-delight goal. A concrete material source
   found by those
   queries becomes an ordinary job in the existing owning route accounting;
   the owning specialist or Capture route publishes its separate focused
   terminal artifact. Phase 2 itself does not acquire native evidence. `CO0`
   may seal only after every selected target is reconciled and every such job is
   source-natively captured or terminally dispositioned,
   then writes the integrated acquisition record and seal. Only `CO0` owns
   user-facing run progress.

   The inventory at this point is provisional and has no fixed axis count.
   Use its lightweight maturity scan to choose the material-exhaustion work;
   do not build the shared semantic proposition view before the admitted
   corpus is terminal. After the evidence-floor plus material-exhaustion loop
   closes, Route 1.4 accounts for every claim-bearing evidence unit and groups
   semantically equivalent or opposing observations without losing their
   product, comparator, condition, provenance, or source role. Final
   adjudication then consumes that view and may merge, split, rename, add, or
   exclude provisional axes before binding decision-usefulness conclusions for
   the seal.

   A cold executor follows this order without reconstructing the authoring
   conversation:

   1. Build the provisional axis inventory from the captured retailer,
      community, editorial, creator, and owned-source evidence, and hash-pin it
      as the single axis inventory this phase's Phase 2 jobs reference; do not
      create a second inventory beside it. Use as many or as few axes as the
      evidence requires; record each axis's pain, delight, or mixed posture,
      affected segment or condition, observed behavior, competitor destination,
      counterevidence, and known gap. This inventory is a routing map, not a
      conclusion.
   2. Run the lightweight maturity scan as a gap audit over that inventory, not
      a second transcription of it. Its input is step 1's record; its output is,
      per axis, which of the authority's support requirements remain unmet —
      distinct-origin independent support above all — plus the next source or
      query that could still change a competitive decision, or an explicit
      `none` with the reason no productive source remains. Mark the axis `open`,
      `provisionally_covered`, or `source_limited`. These three are scan-local
      routing labels with no seal or ledger field: they assign no final decision
      maturity, and `source_limited` does not pre-establish the authority's
      `route_bounded_source_exhaustion` closure basis, which keeps its own
      evidence requirement.
   3. Run only the evidence-floor and targeted material-exhaustion work named
      by the scan. An ordinary corroboration does not reopen other axes. A
      typed material addition reopens its affected axis and only a directly
      adjacent axis when the evidence explains why.
   4. Recompute the scan after each genuinely different continuation family.
      Stop acquisition for an axis only when the Prompt Structure Rules
      authority's closure test is met — two later live continuation families of
      different kinds, queries, and artifacts that add no material addition
      affecting that axis — closing on either `evidence_supported` or
      `route_bounded_source_exhaustion`, never because an axis count, thread
      count, or elapsed-time target was reached.
   5. Terminally reconcile every selected target and candidate before treating
      the corpus as closed, including every comparator candidate from the
      Phase 1 frame and the lane emissions.
   6. For Route 1.4, compile the terminal admitted corpus into the shared
      semantic evidence integration view. Every claim-bearing unit must be
      accounted for, and every proposition must retain its product/comparator
      binding, conditions, counterevidence, support posture, and provenance.
   7. Only then bind decision usefulness, close the comparator set with
      terminal dispositions, record the route version actually used in the
      seal's `understanding_route` block, run the delegated source-native
      check, and validate the seal.

Native TikTok, Instagram, or YouTube capture is licensed only when the SERP or
social listing is ambiguous and opening the native item could change the bound
answer; a vague title alone is not evidence. TikTok Shop is licensed when the
subject is creator/influencer-led or acquired evidence makes the shop a
material commercial venue. A live TikTok Shop attempt must type route failure
as `EGRESS_COUNTRY_WRONG`, `TTSHOP_ROUTE_BLOCKED`, or
`EGRESS_SESSION_UNHEALTHY`; proxy availability alone never licenses capture.

Every Phase 1 block selects and records one continuation mode before the
fan-out spends more acquisition: `full` when completion remains feasible,
`bounded_salvage` when only reusable evidence should be banked, or `stop`.
Bounded salvage remains acquisition-blocked. Automated Google queues use
`run_google_serp_queue.py`: a first block transfers the exact held job to a
ready persistent route or a durable 60-minute cooldown; there is no hot retry,
and a second consecutive or third run block writes `OWNER_PING.json` before
the queue stops.

For the concurrent Reddit customer-evidence controller, the first confirmed
challenge immediately pauses Reddit and returns an owner-action-required state;
healthy Google work may finish. The owner may release Reddit early with a fresh
changed-egress attestation, or release it after the existing 20-minute fallback
cooldown. The controller never changes or cycles VPN endpoints itself, and the
run record stores no server or exit-IP identity. A second capture does not begin
until that explicit host recovery is recorded.

For the current controller, record early changed-egress recovery with
`run_phase_a_customer_evidence_pipeline.py recover-reddit --run-root <root>
--mode operator_changed_egress --operator-attested-at <ISO-8601>`. If no change
is made, use `--mode cooldown_elapsed` only after the recorded fallback deadline.

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
role applies, but it does not skip the SERP Phase 1 -> fan-out -> SERP Phase 2
ordering or the mandatory customer/community job. Rebinding is a
commissioning-time decision: the commissioning Chief Architect proposes the
rebound job set and the owner accepts it in the commission, and the rebound
route still satisfies the same completion-profile discipline (every material
information job supported, contradicted, bounded, or honestly blocked). A
dedicated completion profile for a new subject class is authored only when
that class recurs, not speculatively.

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
    Sephora explicitly, then select and attempt at least four
    company-authorized, target-market, route-admissible third-party retailers
    when four exist, favoring venues that add distinct material evidence; the
    company-owned DTC site does not count. When fewer than four qualify, select
    all that qualify and record `AUTHORIZED_RETAILER_SHORTFALL` with the
    observed count and reasons; preserve exact typed failure instead
    of inventing a listing or completion credit. Use the common lean baseline,
    preserve full raw material, and retain source-visible retailer-native
    extensions. When Sephora is officially named and route-complete, include it,
    count it as one of the four, and make it primary. Keep its typed outcome but
    use another complete working
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
  schema_version: phase_acquisition_seal_v3
  cycle_id:
  commission_id:
  phase: understanding | deliver
  turn: acquire_and_seal
  bound_question:
  intended_consumer:
  intended_use:
  phase_scope:
  commission_board_locator:
  controller_placement:
    controller_actor: CO0
    placement: top_level
    worker_slots_required: 3
    worker_slots_available:
  route_capability_preflight:
    checked_before_network_capture: true
    google_serp:
      primary_route_ready:
      queue_state_writable:
      mode: persistent_fallback | cooldown_only
      persistent_fallback_ready:
    reddit_weekly_lake:
      reader_status: ready | blocked
    paid_ad_transparency:
      google_ads_transparency: ready | identity_pending | blocked
      meta_ads_library: ready | identity_pending | blocked
    tiktok_shop:
      trigger: required | not_required | unknown
      route_status: ready | not_checked_until_trigger | EGRESS_SESSION_UNHEALTHY | TTSHOP_ROUTE_BLOCKED | EGRESS_COUNTRY_WRONG
    native_social:
      tiktok:
        trigger: required | not_required | unknown
        route_status: ready | not_checked_until_trigger | blocked
      instagram:
        trigger: required | not_required | unknown
        route_status: ready | not_checked_until_trigger | blocked
      youtube:
        trigger: required | not_required | unknown
        route_status: ready | not_checked_until_trigger | blocked
  post_phase1_continuation_mode: full | bounded_salvage | stop
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
  specialist_returns:
    - actor: CO1 | CO2 | CO3
      terminal_locator:
      sha256:
      status:
  route_job_accounting:
    - route_id:
      phase: serp_phase1 | co1 | co2 | co3 | campaign_integration | serp_phase2 | semantic_integration
      required: true | false
      material: true | false
      planned_job_ids: []
      planned_count:
      completed_job_ids: []
      completed_count:
      blocked_job_ids: []
      blocked_count:
      unrun_job_ids: []
      unrun_count:
      terminal_artifact_locator:
      terminal_artifact_sha256:
  serp_phase2_decision_receipt:
    locator:
    sha256:
    entries:
  evidence_depth_ledger:
    locator:
    sha256:
  understanding_route:
    route_version: "1.7.0"
    comparator_closure:
      state: phase_a_competitor_context_closed | blocked_open_comparator_candidates
      candidate_frame:
        locator:
        sha256:
      adjudicated_set:
        locator:
        sha256:
      frame_candidate_ids: []
      candidates:
        - candidate_id:
          name:
          material: true | false
          prefanout_qualification:
            posture: core_fanout | bounded_watch | rejected_before_fanout
            comparator_role: direct_peer | value_substitute | adjacent | unresolved | non_competitor
            shared_job:
            open_comparator_search_refs: []
            identity_evidence_refs:
              subject: []
              competitor: []
            independent_comparison_origins:
              - origin_key:
                source_role: reddit_community | retailer_review | creator_authored | independent_editorial
                public_actor_key:
                identity_overlap_posture: no_match_observed | possible_same_actor | confirmed_same_actor | unavailable
                evidence_refs: []
            gap_reason:
          disposition: promoted | rejected | watch_listed | role_bounded | explicit_gap
          decision_ready: true | false
          subject_product_id:
          competitor_product_id:
          subject_product_identity:
          competitor_product_identity:
          claim_ceiling:
          portfolio_role:
            scope: product | franchise
            assessed_identity:
            status: explicit_hero | likely_major | supporting | unclear
            basis: explicit_source | multi_source_inference | observed_position | unresolved
            evidence_refs: []
            gap_reason:
          observed_positions:
            - position_id:
              scope_kind: brand_portfolio | retailer_category | retailer_collection | market_list
              source_or_retailer:
              market_scope:
              observed_at:
              rank:
              list_size:
              label:
              evidence_refs: []
          position_gap_reason:
          shared_axis_ids: []
          competitive_choice_explanation:
            status: observed | partial | unresolved
            summary:
            axis_findings:
              - axis_id:
                proposition_refs: []
                choice_posture: subject_advantage | competitor_advantage | split_or_conditional | parity_or_unresolved
                why:
                conditions: []
                evidence_refs: []
                claim_support:
                  bounded_proposition:
                  support_posture: isolated | directly_observed | resonance_supported | independently_repeated | cross_venue_corroborated
                  independent_origin_count:
                  source_roles: []
                  engagement_evidence_refs: []
                  behavior_evidence_refs: []
                  counterevidence_refs: []
                  conflict_posture: not_checked | none_observed | mixed | contradicted
                  causal_ceiling:
            final_comparator_role: direct_peer | value_substitute | adjacent | unresolved | non_competitor
            role_rationale:
            role_evidence_refs: []
            gap_reason:
          price_size_context:
            status: observed | partial | unavailable
            normalization_posture: same_unit | source_normalized | not_directly_normalized | unavailable
            subject:
              product_identity:
              price_amount:
              currency:
              size_value:
              size_unit:
              market_scope:
              observed_at:
              evidence_refs: []
            competitor:
              product_identity:
              price_amount:
              currency:
              size_value:
              size_unit:
              market_scope:
              observed_at:
              evidence_refs: []
            normalization_evidence_refs: []
            gap_reason:
          lane_evidence:
            co1_owned_ad_positioning:
              status: observed | none_found | blocked
              evidence_refs: []
              gap_reason:
            co2_retailer_product:
              status: observed | none_found | blocked
              evidence_refs: []
              gap_reason:
            co3_retailer_review:
              status: observed | none_found | blocked
              evidence_refs: []
              gap_reason:
            co3_reddit_community:
              status: observed | none_found | blocked
              evidence_refs: []
              gap_reason:
            campaign_creator_comparison:
              status: observed | none_found | blocked
              evidence_refs: []
              gap_reason:
    campaign_evidence_integration:
      status: completed | blocked
      view:
        locator:
        sha256:
      targeted_capture_requests:
        - request_id:
          target:
          disposition: captured | blocked | no_longer_material
    semantic_evidence_integration:
      status: completed | blocked
      view:
        locator:
        sha256:
      corpus_sha256:
      unresolved_material_evidence_ids: []
    verification_requests:
      - request_id:
        product_identity:
        trigger_kind: material_axis | contradiction | condition_or_consequence | competitor_destination | sampling_risk
        trigger_evidence_refs: []
        claim:
        status: completed | blocked | not_run
        return:
          locator:
          sha256:
    retailer_state_accounting:
      claims:
        - claim_id:
          kind: retailer_state_snapshot | retailer_state_change | movement_unresolved_baseline_only
          retailer:
          product_identity:
          market_scope:
          current_observation_ref:
          prior_observation_ref:
          change_summary:
  resume_contract:
    pending_job_ids: []
    reusable_artifacts:
      - locator:
        sha256:
        invalid_if: []
  material_gaps_and_failures: []
  seal_state: SEALED_READY_FOR_DELIVER | BLOCKED_ACQUISITION_INCOMPLETE
  acquisition_gate: pass | blocked
  deliver_allowed: true | false
  sealed_at:
```

The seal is valid for the Synthesize turn only when `seal_state:
SEALED_READY_FOR_DELIVER`, `acquisition_gate: pass`, and `deliver_allowed:
true` (the seal-state and field spellings are stable vocabulary; they read as
"ready for the Deliver phase / synthesis"), and when every required route has a supported disposition and receipt or
an honestly typed non-material blocking result. Any material blocking result,
or a required route that was skipped, silently substituted, incompletely
captured, or described as exhausted without the matching route evidence,
forces the blocked state.

Validate the v3 block with
`forseti-harness/runners/run_phase_acquisition_seal_validation.py`. The planned
job set must equal the disjoint completed, blocked, and unrun sets; counts and
artifact hashes must match. Hash comparison canonicalizes line endings for
Markdown, JSON, and YAML artifacts so an unchanged cross-platform checkout
does not look like content drift; other artifact types remain exact-byte
checks. A valid empty SERP Phase 2 decision receipt never gives completion
credit to licensed-but-unrun SERP Phase 2 queries. Resume re-hashes every
reusable artifact and runs only pending jobs unless the bound question changes,
an artifact hash drifts, its source-specific currentness expires, or owning
authority becomes incompatible. The validator also enforces the
`understanding_route` block: a known `route_version`; at `1.1.0` and later the
campaign-integration route accounting, view binding and per-unit shape,
independent-origin credit and cluster rules, terminal comparator dispositions
with exact-identity binding for promoted candidates and
per-material-candidate lane evidence; at `1.2.0`, pre-fanout qualification for
every Phase 1 frame candidate, including the core two-origin/two-source-role
bar and the per-product identity-evidence and price/size shape; at `1.3.0`,
light public-actor de-duplication for credited origins and an evidence-backed
axis-level competitive-choice explanation whose terminal role is derived only
after the explanation; at `1.4.0`, a complete versioned semantic-integration
view over the admitted claim-bearing corpus, proposition references on each
material axis finding, source-role competence, counterevidence visibility, and
artifact/hash binding; at `1.5.0`, contextual semantic method v2, distinct
stable product IDs for material comparators, and exact
candidate-to-proposition product binding; at `1.6.0`, full captured-corpus
accounting, capture envelopes, rendered-prompt byte bounds, root-batch-bound
hierarchical leaf lineage, semantic posture, immutable consolidated emerging
axes (including carried blockers), and separately computed
evidence-item/container/origin/role/engagement counts;
at `1.7.0`, exhaustive semantic processing is limited to Reddit/community
conversation text and retailer review text, while other evidence routes remain
verified structured references; terminal-return-selected, hash-pinned Phase 1
and Phase 2 queue-state receipts generate the successful job-to-packet inventory, focused-search records
own their exact packet sets, and every source-bearing row from those surfaces has one explicit
row-identified semantic route, duplicate, or exclusion before seal (never a
bulk/default route);
verification-request triggers and
terminal statuses, and the two-observation retailer-movement rule. A seal
sealed before route versioning began (2026-08-07) carries no stamped version
and is audited with `--allow-preversion-route`. A seal stamped with a known
older route version (a recorded route retention) is likewise
historical-audit-only under the same switch; neither case satisfies the
current route contract. An authorized historical audit is version-symmetric:
the seal still owes everything its own stamped version introduced, and owes
nothing a later version introduced.

The mechanical price/size check is limited to material candidate rows whose
`shared_axis_ids` contains `price`, `value`, `quantity`, or `cost`. Different
axis labels and price/value language outside that shape remain semantic review
obligations and are not proven complete by validator pass. The final delegated
semantic pass scans axis labels and prose for affordability, premium, worth-it,
deal, cost-per-use, quantity, duration, and use-rate language; when detected it
requires the same two-product price/size context or an explicit
unavailable/not-directly-normalized disposition. It may flag missing context,
but may not invent a conversion or infer equal value from sticker price.

The v3 ledger uses schema `understanding_evidence_depth_v1` and profile
`broad_company_understanding_v1`. It repeats the seal's subject and cycle ID;
the validator requires both identities to match before the ledger can support
that seal. It hash-pins the evidence artifacts used for depth accounting;
enumerates outside-in units, retailer-review corpora, Reddit/forum threads, and
native-social posts with their independence and distribution fields; and
carries echo adjudication, material-seam dispositions, the acquisition-batch
yield sequence, and remaining-move dispositions. The validator derives the
anti-token floor metrics from those rows. It cannot judge whether prose is
insightful or whether a semantic independence claim is true; `CO0` still owns
that evidence judgment and must block rather than fill fields with unsupported
labels. Historical v2 seals require
`--allow-legacy-v2` for audit and do not authorize a new broad-Understanding
synthesis under the current contract.

Consumer brands with material product/customer experience use
`understanding_evidence_depth_v4` and
`broad_consumer_brand_understanding_v3`. The v4 ledger preserves the v1 family
and closure accounting while using `external_context` for the human-facing
External company, editorial and industry context family. It also carries the
pre-Phase-2 product-axis inventory, the hash-pinned retailer and community
coding references, per-corpus recomputed incidence, social relationship and
owned-direction tags, the 40-thread minimum floor plus a proven
`reddit_candidate_frontier` accounting block with every discovered candidate
terminally accounted, its discovery query and captured result packet pinned,
the mandatory high-yield query-family set, and the additional floor exception
when below 40,
per-thread source-native artifacts, comment-coding-backed support-ref fields,
three focused Phase 2 jobs per material axis, and target reconciliation from
search pointer through native body to evidence unit — a SERP artifact never
doubles as the native body. Each material axis declares evidence strength
separately from decision maturity, closure basis, claim ceiling, and the two
later live continuation families that form its decision frontier. Those two
families must differ in kind, query, and result artifact and add no material
addition affecting that axis. They may add usable Reddit threads; each batch's
`new_usable_reddit_threads` is recomputed and reported separately from its typed
material additions.

The same axis row carries the smallest-complete decision-usefulness synthesis:
customer tension; segment/condition; behavior or purchase consequence;
competitor destination; strongest counterevidence; changed competitive
decision; a small set of already-valid decision-bearing support references;
and limitations. This is the review index for the axis, not a substitute for
its evidence. Mechanical validation checks that the fields and references are
present and coherent. Reviewers test the strategic judgment by reading those
references plus risk-triggered samples; they do not reread the full corpus by
default. A mismatch expands review only for the affected axis.

At the final broad consumer-brand Understanding Acquire & Seal closeout
(historically "Phase A"), the delegated review-and-patch commission must apply
the authority's semantic source check before the seal is accepted for
synthesis or landed. It reads every decision-bearing reference and two independent spot
checks per material axis, verifies local subject anchoring, axis/role fit,
competitor-event attribution, and genuine counterevidence, then uses the
authority's affected-axis-first escalation rule. The delegate patches only the
bound Phase A target set; the Chief Architect adjudicates the return and reruns
the acquisition-seal validation. This is a bounded fitness check of the review
index, not a second full-corpus analysis.

Before each continuation query family starts, the acquisition-view input records
one short round rationale: why another round is warranted and how its query
design differs from the prior round. The renderer requires complete job coverage
and refuses a query family split across round records. The completed Phase A acquisition record renders a
deterministic human view from the evidence-depth ledger and community coding:
the evidence-family scorecard, per-round funnel and yield, per-axis decision
support, exact query register, and final decision-frontier observation. Search
pages receive no usefulness credit without an admitted source-native body and
coding row; repeated sightings remain visible but never inflate unique-source
counts. Any engagement snapshot used to construct or analyze this record retains
its observation date, ISO 8601 `observed_at` timestamp when available, and source
locator in working provenance; the final human deliverable need not display the
date when it is not decision-relevant. This view is part of the existing
acquisition record, not a new evidence authority, seal field, or per-run report
artifact.

Historical consumer v1 and v2 profiles require
`--allow-legacy-consumer-v1` and `--allow-legacy-consumer-v2` respectively and
are never upgraded by assertion.

For company Understanding, non-empty route accounting is required for
`serp_phase1`, `official_retailer_authorization`,
`google_ads_transparency`, `meta_ads_library`, `retailer_full_pdp`,
`reddit_weekly_lake`, `reddit_community_scout`, and `serp_phase2`, with explicit
`serp_phase1`, `CO1`, `CO2`, `CO3`, and `serp_phase2` phase coverage. Under
route version `1.1.0` and later, `campaign_evidence_integration` (phase
`campaign_integration`) joins that required set. A typed
no-work decision may be the planned job when a route truly has no work; silence
is not accounting. Triggered TikTok Shop or native TikTok, Instagram, or YouTube
capture adds its route to the same accounting requirement.

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
authorize the Synthesize turn. If a material seam remains unresolved because a commission
limit or source boundary stops acquisition, or if the assembled evidence cannot
support a decision-useful answer to the bound question, use
`BLOCKED_ACQUISITION_INCOMPLETE`; do not lower the answer standard to pass the
seal.

#### Route 1.1.0+ — Campaign Integration, Comparator Closure, Verification, Retailer State

Field contracts, enums, and claim ceilings for these obligations live in the
Prompt Structure Rules authority ("Understanding Acquire & Seal Route Revision
Contracts"). Operating rules:

- **Campaign-evidence integration** is one controller-owned post-fan-out job
  (route `campaign_evidence_integration`, phase `campaign_integration`) run
  after all specialist terminal returns and before the seal, feeding SERP
  Phase 2. It joins existing CO1 owned/ad, CO3 creator/audience, and CO2
  identity evidence into one hash-pinned `campaign_evidence_view_v1` artifact
  and may emit targeted capture requests that run as ordinary jobs in the
  owning routes and are terminally dispositioned before a passing seal. Its
  route-accounting row is required and material; a passing seal requires every
  planned integration job to be completed. Campaign integration is
  acquisition-control synthesis: no standing `CO4`, no creator crawl, no
  standing monitor, no spend/conversion inference, no market conclusion, and
  no merging of creator-authored and audience/customer evidence roles.
- **Competitor-set closure** runs through three states:
  `candidate_comparator_frame` (SERP Phase 1; provisional; scopes the
  `CO1`-`CO3` fan-out capsules and is never frozen),
  `adjudicated_comparator_set` (after specialist returns plus SERP Phase 2,
  which first explains the observed product choice by axis and only then
  derives the terminal comparator role), and
  `phase_a_competitor_context_closed` (at the seal: every material
  candidate `promoted | rejected | watch_listed | role_bounded | explicit_gap`;
  no candidate silently disappears). Every material candidate owes lane
  comparator evidence or a typed gap from CO2 (retailer/product with exact
  identity), CO3 (retailer-review and Reddit/customer comparison), the
  campaign view (creator comparison, relationship-typed), and CO1 (owned/ad
  positioning as actor strategy). A `promoted` candidate requires both exact
  subject and competitor product identities. Phase A closes decision-usable
  comparator context only — never an exhaustive-direct-competitor claim,
  representative market sentiment, or a standing competitor lane.
  Every material candidate also records the observed competitor product or
  franchise's portfolio role as `explicit_hero | likely_major | supporting |
  unclear`, with the evidence basis and exact assessed identity. `Likely_major`
  requires a multi-source inference; `supporting` requires positive evidence;
  `unclear` records the unresolved gap rather than forcing a role. Ordered
  source positions are recorded only as source-local observations with the
  retailer/list scope, market, observation time, and evidence reference. A
  numeric position carries both rank and list size; otherwise a source-visible
  relative label may be recorded. These observations never become a universal
  brand rank, sales rank, market share, or cross-retailer league table. A
  promoted direct competitor names at least one shared comparison axis.
  Retailer-review evidence and Reddit/community evidence remain separate:
  both are public customer-language samples, not representative sentiment or
  population polling. Each observed lane points to evidence; `none_found` or
  `blocked` records why.
  Route 1.2.0 hardens the first state: every frame row records an open-comparator
  discovery reference and a pre-fanout posture. `Core_fanout` requires exact
  subject and competitor products, identity evidence recorded separately per
  product, one shared customer job, and two independent
  comparison origins drawn from two distinct source roles among community,
  retailer review, creator-authored, and independent editorial. Two origins
  that re-cite the same evidence unit are one origin under two keys. SERP
  snippets,
  retailer co-placement, owned claims, and ads remain discovery or actor-strategy
  evidence, not independent confirmation. `Bounded_watch` and
  `rejected_before_fanout` preserve their gap reason. Consistent qualification
  means the same bounded competitor question and typed outcome for every frame
  row; it does not impose equal creator posts, customer rows, or a new creator
  parity gate.
  Route 1.3.0 adds a light public-identity pass: each credited origin carries a
  normalized source-visible actor key plus its overlap posture. Exact duplicate,
  possible-same-actor, confirmed-same-actor, and unavailable identities cannot
  jointly satisfy the two-origin bar. The semantic pass checks normalized
  handles, profile URLs, and disclosed links/codes; it does not attempt a full
  cross-platform identity graph.
  For every material candidate, Phase 2 records an evidence-only
  `competitive_choice_explanation`: the axis, which side the evidence favors or
  whether it splits, why, conditions, and evidence references. The final role
  is derived afterward. A promoted row requires an observed explanation; a
  partial or unresolved row preserves its exact gap. This does not authorize a
  recommendation, market conclusion, or Deliver work.
  Every axis finding consumes
  `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`.
  It binds one proposition and preserves its support posture, exact independent
  origin count, source roles, engagement and behavior evidence, counterevidence,
  conflict posture, conditions, and causal ceiling. An isolated testimonial
  cannot set an advantage; a directly observed bounded fact may. Resonance
  support requires source-native engagement evidence and never becomes an
  independent-experience count. Mixed evidence stays split or conditional.
  Serious competitor retailer work has two scopes, both inside this one Phase A:
  the exact competing product receives full capture across the selected
  comparable retailers (CO2 product/PDP state and separately typed CO3
  review/Q&A evidence), while the relevant franchise receives a bounded
  owned/retailer map sufficient to establish local portfolio role. A sibling
  expands to full exact-product capture only if it could change that role or the
  customer-choice explanation. A full rival-company assortment is commissioned
  only for a brand/portfolio-level question; there is no percentage-of-focal
  quota.
  Observable brand positioning remains context. CO1 and campaign evidence show
  what the brand and its messengers emphasize; customer evidence shows whether
  people repeat, reject, or ignore it. Phase 2 may join those facts but never
  relabel actor strategy as customer choice.
  When price or value is compared, both products' cited price and size units
  travel together; unequal or non-normalized units remain explicit, and a
  posture that licenses direct comparison cannot span two currencies.

  **Summer Fridays dogfood grounding (historical evidence, not a current
  competitor verdict).** The p11 Phase 1 ledger selected e.l.f. Glow Reviver
  Melting Lip Balm and Rhode Peptide Lip Treatment after each appeared in two
  fresh subject queries. It observed Summer Fridays Lip Butter Balm at USD 24
  for 15 g, e.l.f. at USD 9 for 0.52 oz, and Rhode at USD 20 for 10 ml; the
  Rhode comparison correctly remained unnormalized across mass and volume.
  The same run's Phase 2 kept both brands watch-only because its admitted
  evidence showed zero first-hand authors, threads, or venues. That was a sound
  evidence result, but it did not yet explain customer choice.

  The later p11r7 customer corpus shows why claim-level support matters more
  than a label or broad axis count. Fresh claim-support dogfood found the
  Summer-Fridays-versus-e.l.f. hydration comparison independently repeated but
  mixed: two low-engagement authors favored Summer Fridays and one favored
  e.l.f. Three separate Reddit authors reported a wear/reapplication
  disadvantage versus Ole Henriksen, which supports a repeated community
  signal but not current-formula certainty or cross-venue corroboration. The
  single one-point statement that bundled flavors, older formulas, shorter wear,
  and continued buying remains isolated and cannot establish flavor as a
  repurchase cause. The dated sticker-price comparison remains a bounded direct
  observation. The full provenance and claim-support blocks are in
  `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/intelligence_claim_support_dogfood_20260807_v0.md`.

  The focal retailer work also shows the difference between phase count and
  retailer scope: the p11 Summer Fridays CO2 return captured 52 owned Shop All
  rows, a complete 46-row Sephora brand grid with 44 exact non-bundle PDP
  baselines, a 96-placement Amazon query window with 26 valid exact baselines,
  and a blocked Space NK US route that rendered GBP. Under route 1.3.0, a core
  e.l.f. comparison would not rerun a second Phase A or capture all e.l.f.
  cosmetics. It would fully capture the exact Glow Reviver Melting Lip Balm
  across the selected comparable retailers, then map only the relevant e.l.f.
  lip franchise far enough to establish that product's local role. The
  Phase 1 “premium anchor versus lower-price dupe surface” is positioning
  context; the customer rows above test whether that context affects choice.

  Source artifacts for this example:
  `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/competitor_ledger.json`,
  `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json`,
  `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md`, and
  `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/community_axis_coding.json`, with the
  claim-support adjudication in
  `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/intelligence_claim_support_dogfood_20260807_v0.md`.
- **Conditional product/claim verification** triggers only on
  reconciled product identity × material axis or contradiction × publicly
  verifiable unresolved claim. It is a conditional adjustment job, never
  catalog-wide; a completed return attaches instrument-level verdicts,
  provenance, failures, and claim ceilings, and may reopen the affected axis
  but never starts Deliver. An emitted request left `not_run` blocks a
  passing seal.
- **Retailer state and movement**: one comparable CO2 observation is a
  `retailer_state_snapshot`; a `retailer_state_change` requires two
  observations with stable retailer/product/market/scope identity and old/new
  evidence references plus a non-empty change summary; otherwise
  `movement_unresolved_baseline_only`. The validator proves distinct reference
  and summary shape; stable comparability remains an evidence-backed review of
  the cited CO2 observations. Proxies
  (stockout, review velocity, assortment, promotion) never become sales or
  productivity, and refresh is event-commissioned, never a standing monitor.

#### Understanding Acquire & Seal Route Version And Changelog

The operating-sequence authority for this route stays in this playbook; do
not create a parallel Phase A manual. The acquisition seal records the route
version actually used; a run started under an older route retains that
version unless an explicit migration/restart is applied and recorded.

```yaml
understanding_acquire_seal_route:
  current_version: 1.7.0
  versioning_started: 2026-08-07
  baseline_revision: 1aa3a833edbb8425a4ca2eee91bd850feec4e32c
  version_semantics:
    major: phase order, authority boundary or seal meaning changes
    minor: required/conditional evidence lane, integration job or closure gate changes
    patch: non-semantic clarification or validation hardening
  changelog:
    - version: 1.0.0
      date: 2026-08-07
      owning_change: retrospectively recorded baseline; no owning PR
      changed_behavior: >
        Records the pre-versioning current-main route: validated board ->
        SERP Phase 1 -> CO1/CO2/CO3 fan-out -> SERP Phase 2 -> adaptive
        consumer-depth and category-benchmark work -> acquisition seal, with
        its known gaps: no campaign-evidence integration job, no explicit
        competitor-set closure, no conditional verification accounting, no
        retailer snapshot/change semantics, and no recorded route version.
      affected_gate: none; baseline record only
      migration_note: >
        1.0.0 is a retrospectively recorded baseline, not a version
        historically stamped at the time. Seals from pre-versioning runs are
        audited with --allow-preversion-route; historical artifacts are never
        rewritten to claim a version.
    - version: 1.1.0
      date: 2026-08-07
      owning_change: Phase A campaign/competitor integration implementation (this change's PR)
      changed_behavior: >
        Adds the controller-owned post-fan-out campaign-evidence integration
        job and campaign_evidence_view_v1; three-state competitor closure with
        the Phase 1 frame scoping the fan-out, per-material-candidate lane
        comparator evidence, and pre-seal SERP Phase 2 direct-competitor
        adjudication; evidence-backed product/franchise portfolio role,
        source-local observed positions, separate retailer-review and
        Reddit/community customer-language lanes, and shared axes for promoted
        competitors; conditional product/claim verification accounting;
        retailer snapshot/change/baseline-only movement semantics; and the
        seal-recorded route version with this append-only changelog.
      affected_gate: >
        Acquisition seal: understanding_route block enforced by
        run_phase_acquisition_seal_validation.py.
      migration_note: >
        A run started under 1.0.0 retains 1.0.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.1.0.
    - version: 1.2.0
      date: 2026-08-07
      owning_change: PR #1445 — Phase A pre-fanout comparator qualification hardening
      changed_behavior: >
        Keeps the 1.1.0 phase order and existing CO1-CO3 lanes, but makes the
        Phase 1 candidate frame decision-usable before fan-out. Every frame row
        receives a pre-fanout posture, role, and open-comparator discovery
        reference. Core fan-out candidates require
        exact product and shared-job binding, per-product identity evidence,
        plus two independent comparison
        origins across two source roles that do not re-cite the same evidence
        unit; SERP remains discovery-only. Weaker
        candidates remain bounded watch rows or explicit pre-fanout rejections.
        Price/value comparisons must carry both products' size units or state
        that they are not directly normalized, and a posture that licenses
        direct comparison cannot span two currencies.
      affected_gate: >
        Acquisition seal: route 1.2.0 comparator frame candidates are enforced
        by run_phase_acquisition_seal_validation.py.
      migration_note: >
        A run started under 1.1.0 retains 1.1.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.2.0. An authorized
        historical audit of a 1.1.0 seal enforces the full 1.1.0 obligation set
        and none of the 1.2.0 additions.
    - version: 1.3.0
      date: 2026-08-07
      owning_change: Phase A competitive-choice evidence implementation (this change's PR)
      changed_behavior: >
        Keeps the existing SERP Phase 1 -> CO1/CO2/CO3 fan-out -> SERP Phase 2
        order, but makes the Phase 2 primary comparator output an axis-level
        explanation of why and under which observed conditions customers choose
        either exact product; the terminal comparator role is derived afterward.
        Core pre-fanout origins receive a light public-identity de-duplication
        check. Serious rival retailer acquisition uses two scopes inside the
        existing fan-out: full selected-retailer capture for the exact competing
        product and a bounded relevant-franchise map. Observable brand
        positioning remains a separate context input. The final semantic review
        also detects price/value concepts that machine-visible axis names miss.
        Each axis finding consumes the intelligence-cycle claim-support contract
        so an isolated comment, audience resonance, independent recurrence,
        cross-venue corroboration, behavior, counterevidence, and causal ceiling
        cannot be silently collapsed into one directional claim.
      affected_gate: >
        Acquisition seal: route 1.3.0 requires public-actor identity fields for
        credited pre-fanout origins and a competitive_choice_explanation for
        every material comparator candidate; each axis finding carries and
        satisfies the shared claim-support block.
      migration_note: >
        A run started under 1.2.0 retains 1.2.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.3.0. An authorized
        historical audit of a 1.2.0 seal enforces the full 1.2.0 obligation set
        and none of the 1.3.0 additions.
    - version: 1.4.0
      date: 2026-08-07
      owning_change: Phase A semantic evidence integration implementation (this change's PR)
      changed_behavior: >
        Keeps the existing acquisition lanes and SERP sequence, then adds one
        controller-owned evidence-structuring step after the admitted corpus is
        terminal and before final judgment. A no-provider-API agent pass groups
        evidence by meaning into shared propositions while retaining exact
        product/comparator binding, conditions, provenance, source role,
        counterevidence, and support posture. Every claim-bearing admitted unit
        must be used or explicitly left unmerged; emerging axes stay visible.
        Final comparator axis findings reference those propositions instead of
        silently selecting a few convenient observations from the corpus.
      affected_gate: >
        Acquisition seal: route 1.4.0 requires a hash-bound
        semantic_evidence_integration_view_v1 with complete admitted-evidence
        accounting and proposition references for material comparator findings.
      migration_note: >
        A run started under 1.3.0 retains 1.3.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.4.0. An authorized
        historical audit of a 1.3.0 seal enforces the full 1.3.0 obligation set
        and none of the 1.4.0 additions.
    - version: 1.5.0
      date: 2026-08-07
      owning_change: Phase A contextual product binding implementation (this change's PR)
      changed_behavior: >
        Keeps route 1.4's semantic evidence integration step and evidence
        accounting, but requires every admitted unit to carry source-pinned
        product context tied to a hash-pinned source artifact and makes
        upstream product candidates hypotheses rather
        than identity proof. Every material comparator also carries distinct
        stable subject and competitor product IDs; a competitive-choice axis
        may cite only propositions bound to that exact product pair in that
        orientation.
      affected_gate: >
        Acquisition seal: route 1.5.0 requires context-aware semantic method v2
        with its exact method hash, stable product IDs for material comparator
        candidates, and exact candidate-to-proposition product binding.
      migration_note: >
        A run started under 1.4.0 retains 1.4.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.5.0. An authorized
        historical audit of a 1.4.0 seal enforces the full 1.4.0 obligation set
        and none of the 1.5.0 additions.
    - version: 1.6.0
      date: 2026-08-08
      owning_change: Phase A full captured-corpus semantic integration implementation (this change's PR)
      changed_behavior: >
        Keeps the existing Phase A sequence and claim-support authority, but
        replaces screen-bounded semantic closure for new runs with one
        explicitly declared final captured corpus. Every captured source-native
        leaf is semantically assessed, mechanically excluded with an exact
        reason, or blocks. Containers preserve conversation/review/published-
        object context and capture envelopes. Extraction and reconciliation
        prompts are bounded by actual rendered UTF-8 bytes; reconciliation may
        repeat through child-referenced levels while the compiler preserves
        exact leaf, condition, polarity, product/version, and provenance
        lineage. Emerging labels are agent-consolidated with original lineage.
        View v2 separates semantic-unit, evidence-item, container, independent-
        origin, source-role, engagement, support, opposition, and mixed counts.
      affected_gate: >
        Acquisition seal: route 1.6.0 requires semantic integration view v2,
        exact method v3/hash, complete final-corpus accounting with no blocked
        leaf, exact container/capture-envelope accounting, terminal consolidated
        axes, and proposition evidence-stack shape.
      migration_note: >
        A run started under 1.5.0 retains 1.5.0 unless an explicit
        migration/restart is recorded. New runs seal under 1.6.0. An authorized
        historical audit of a 1.5.0 seal enforces view v1/method v2 and none of
        the 1.6.0 additions. The existing 80-item Summer Fridays migration is a
        bounded regression slice, not final-corpus proof; the full shadow run is
        separately commissioned after this architecture lands.
    - version: 1.7.0
      date: 2026-08-08
      owning_change: Phase A semantic-source boundary and SERP linking implementation (this change's PR)
      changed_behavior: >
        Keeps Route 1.6's full-corpus semantic method, but limits the exhaustive
        customer-language denominator to Reddit/community conversations and
        retailer review text. Other acquired evidence remains hash-verified as
        structured references. Every source-bearing result row from the sealed
        Phase 1 and Phase 2 jobs and every focused-search SERP packet receives
        exactly one explicit row-identified agent-semantic routed, duplicate,
        or excluded disposition; a bulk/default route is invalid. Routed rows
        bind to native capture or locator recovery. Retailer source
        files are raw-byte pinned and review membership is structurally checked.
        A same-day correction makes terminal-return-selected, hash-pinned SERP queue states the
        owner of Phase 1/2 packet membership and rejects a surface map that
        drops or adds a successful packet; focused-search records reconcile
        their packet sets exactly.
      affected_gate: >
        Acquisition seal: route 1.7.0 requires a complete embedded
        phase_a_serp_source_frontier_v1 and exact customer-language source
        accounting before semantic materialization.
      migration_note: >
        A run started under 1.6.0 retains 1.6.0 unless explicitly restarted.
        Historical seals are never restamped. New runs seal under 1.7.0.
  append_only_rule: >
    Every future semantic route change appends one row with version, date,
    owning change/PR when known, changed behavior, affected gate, and
    migration or compatibility note. Rows are never rewritten or deleted, and
    historical body artifacts are never rewritten to pretend they used a
    later route.
```

### Turn B — Synthesize

Use this section only when a synthesis deliverable is explicitly commissioned.
Do not enter it from an unqualified Understanding or historical Phase A request
merely because the acquisition seal passes.

Start in fresh context and load the phase acquisition seal, not the accumulated
capture chat. Verify its identity, canonical phase, bound question/use, seal
state, route receipts, provenance, and material gaps before synthesis. Where
the completion profile requires a semantic source review (currently the broad
consumer-brand profile), also verify that a durable semantic-review
disposition — the adjudicated review return or a dated adjudication note —
exists and is cited by the synthesis commission; a mechanically passing seal
without that disposition is a blocked gate for those profiles. If the gate is
blocked or the artifact is incomplete, stop and return to Acquire & Seal; do
not issue a nominal deliverable.

The Synthesize turn compresses and communicates the acquired evidence. Its
succinctness discipline is never grounds to under-acquire during Acquire &
Seal.

When the gate passes, synthesize the phase deliverable, craft the human report
or framing artifact, validate it under the owning contract, and hand off the
next phase or step. Every evidence, coverage, provenance, and route-exhaustion
claim must resolve to the seal. Preserve the final deliverable as the sealed
phase output before commissioning post-delivery review.

When a consumer-brand v2 substrate is present, Understanding synthesis may
derive a product value battle map from the sealed axis strengths: material
pains remain visible, while only `strong` delights enter the foreground. Any
later defend/avoid-attacking or competitive-opening judgment belongs to the
Deliver phase; Phase A records only evidence strength, captured-sample
incidence, choice consequences, counterevidence, and claim ceilings.

For company Understanding where offerings or retail are material, the
Understanding synthesis makes the breadth-first substrate visible in Section 5,
`Portfolio And Retail Architecture`. Its ordered subsections and compact matrices show the owned
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

Understanding synthesis produces the decision-neutral company-intelligence
artifact as the substrate deliverable. The Deliver phase then produces the
explicitly commissioned decision-bearing artifact — a competitive decision
memorandum for a named or declared-proxy decision owner, in challenger or
defender framing — from that sealed substrate under
`forseti/product/spines/commission_signal_board/workflows/deliver_decision_memorandum_method_v0.md`,
opening with the problem-framing step (decision frame and target screen). The
Deliver phase's Acquire & Seal turn is bounded to decision-specific
supplements to the Understanding substrate, never a general re-scan. The
Deliver phase's governing acquisition gate is the passing Understanding seal
plus a durable, bounded capture-return artifact for every supplement the
synthesis consumes; supplements never alter sealed claim ceilings. A
supplement that would change a sealed claim ceiling requires a full
Deliver-phase Acquire & Seal with its own phase seal before synthesis; that
Deliver seal **augments** the Understanding seal — synthesis then requires
both, the Deliver seal's re-adjudicated ceilings govern the claims it names,
and every other claim stays under the Understanding ceilings. The supplement
production chain itself is owned by the Deliver method doc's Supplement Chain
section.

When both turns are explicitly commissioned, two turns are the normal operating
budget, not a hard completion cap. A blocked Acquire & Seal remains blocked and
may require another acquisition attempt; it does not count as a successful
synthesis.

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
   visible and may block synthesis.
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

This seam is **dormant until the post-delivery six-dimension rubric authority
is separately adopted**. While dormant, post-delivery review routes through
the bound review lanes instead — the Deliver method's cold adversarial read
for decision memoranda, and the ordinary review lanes for other phase
deliverables — with findings-first output and no numeric rubric return. Once
the rubric authority is adopted, commission an independent adversarial review
against it and its applicable hard caps; do not reconstruct the rubric from
this production contract or create a duplicate rubric here.

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

Under the adopted rubric, return the total number, the six-dimension profile,
and all triggered flags or caps; never return a lone number; while the seam is
dormant no numeric return is required or permitted. Weights, bands, and caps remain provisional
working evaluation authority, not production instructions or a permanent
readiness gate unless separately adopted. This handoff defines only the seam
and required inputs; it does not create the numerical rubric, authorize the
reviewer to patch, or change the report layout.

## Operating Sequence

Use this sequence to create the CSB inside Acquire & Seal. The broader cycle
gate above controls whether the Synthesize turn may begin.

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
    Sephora-primary rule when it is officially named and route-complete,
    counting Sephora as one of the four rather than in addition to them, but do
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
    load-bearing artifacts, runs the controller-owned campaign-evidence
    integration job (route 1.1.0 and later), and then runs the post-fan-out targeted
    SERP return:
    `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`.
    Phase 2 derives each query from a named specialist or integration finding,
    applies the decision lifecycle, explains competitive choice by shared axis
    from the lane returns, derives the terminal comparator role afterward, and
    returns the consolidated ledger, decision receipt, provenance, and material
    blocks. It does not repeat native capture or start Deliver.
11. For an Intelligence Cycle, assemble the phase acquisition seal only after
    the Phase 2 terminal result and all owning Scanning/Capture work return. A
    typed acquisition failure remains visible and blocks synthesis when material;
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

If an agent sees "Forseti Intelligence Cycle", "Understanding phase", "Deliver
phase", historical "Problem Framing phase", "Acquire & Seal", or "Synthesize",
it should open this playbook before commissioning or executing the phase. An
unqualified Understanding or historical Phase A request follows the
acquisition-only default above; it does not enter the Synthesize turn.

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
