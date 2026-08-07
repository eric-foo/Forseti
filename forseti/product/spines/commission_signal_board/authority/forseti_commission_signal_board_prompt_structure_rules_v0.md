# Forseti Commission Signal Board Prompt Structure Rules v0

```yaml
retrieval_header_version: 1
artifact_role: Prompt Structure Rules
scope: >
  Durable rules for the Commission Signal Board Prompt Structure: the board is
  a signal and evidence routing structure, not a gate, demand check, proof step,
  classifier, retrieval process, or implementation authorization.
use_when:
  - Checking the durable rules behind the Commission Signal Board Prompt Structure.
  - Commissioning or checking a Forseti Intelligence Cycle phase.
  - Checking which prompt sections are adopted, modified, deferred, or rejected under the evidence/signals-only boundary.
  - Preparing owner sign-off on commission signal-board naming, source-routing, and classifier handoff.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - forseti/product/spines/scanning/admissibility_checkability/forseti_demand_scan_gate_adjudication_packet_v0.md
  - forseti/product/spines/commission_signal_board/dispatch_rules/forseti_demand_gate_run_commission_criteria_v0.md
  - forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md
stale_if:
  - The owner chooses a different durable name for the commission signal/evidence object.
  - A later Commission Signal Board Prompt Structure supersedes this rules doc.
  - A demand-classifier handoff contract supersedes this evidence/signals-only boundary.
```

## Start Preflight

```text
forseti_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom S2 product anchor plus target prompt, adjacent classifier/proof context, and historical gate-named artifacts
  edit_permission: docs-write
  target_scope: product-lead Prompt Structure Rules artifact; no prompt artifact, no implementation, no runtime authorization
  dirty_state_checked: yes
  blocked_if_missing: AGENTS.md, overlay README, source-loading, prompt-orchestration, buyer-proof packet, adjacent demand/gate context artifacts, temporary prompt
```

## Decision Question

Should the temporary file
`C:/Users/vmon7/AppData/Local/Temp/orca_commission_gate_prompt (1).md`
become a durable Level 1 commission prompt, be rewritten through Forseti prompt
orchestration, or be deferred?

## Owner Correction

The commission object should not be a **gate**.

The commission object should be a **signal board**: a structured evidence and
signal surface that organizes what is known, where it came from, how strong or
weak the signal coverage is, what contradicts it, and what remains missing.

It should not decide whether demand exists. The demand-classification layer owns
the demand check. Commission should prepare clean evidence and signal inputs for
that layer, not pre-judge them.

This means the commission output should be a board or packet of signals, not an
`admit` / `hold` / `fail` verdict.

## Adjudication

Do **not** install the temporary prompt as-is.

Use it as a strong decision-prep draft for a future signal-board prompt, but
strip out the gate semantics. The valuable parts are source routing, mode/cutoff
discipline, provenance discipline, creator/non-creator separation, redirect
rules, and output shape. The wrong parts are any demand decision, pass/fail
gate, proof claim, or classifier-like judgment.

The recommended direction is:

- Adopt **Commission Signal Board** as the working object name unless the owner
  picks a better noun.
- Commission owns evidence and signals only: collect, route, tag, compare,
  preserve provenance, expose conflicts, and name gaps.
- The demand classifier owns demand judgment.
- Buyer-proof and client-facing claims remain downstream and separately gated.
- Durable prompt authoring still goes through prompt-orchestration.

Current prompt amendment: the durable CSB prompt now records recency/currentness
as source-route attention metadata (`recency_status` and `recency_attention`).
The manual/local CSB validator now enforces those row-shape fields and enum
values, but only as output shape: same-strength newer/current URL-backed rows
can deserve more scan attention, and that attention is not buyer proof, demand
classification, classifier mapping, evidence weighting, or graph weight.

Current prompt amendment (2026-07-17): the company competitive-intelligence
completion ledger now carries commission-stage vocabulary. A company board
sealed before its scan uses `run_boundary: COMMISSION_SEALED_PRE_SCAN` — valid
only while the coverage ledger still contains `not_checked` rows — and may set
`reddit_scout_status` / `quora_scout_status` to `commissioned_not_yet_run` at
that stage only. This exists so a truthful pre-scan commission never has to
borrow the completed-report boundary (origin: adversarial-review finding AR-07
against the Tower 28 Phase 1 commission). It changes lifecycle vocabulary only:
no scan, capture, classification, or proof semantics change, and a completed
company report must still carry earned checked/blocked scout values.
Each completion-ledger scout value must agree with its corresponding coverage
row's status and yield; the completion ledger cannot claim a checked, blocked,
pending, or not-required result that the coverage ledger does not show.

## Forseti Intelligence Cycle Operating Contract

The future-facing operating name is **Forseti Intelligence Cycle**. Its
canonical phases are:

1. **Understanding** — produce a decision-neutral understanding of the subject.
2. **Deliver** — frame the consequential problem or decision from that
   understanding and produce the commissioned decision-bearing artifact.
   `Problem Framing` is this phase's historical name (`Problem` its informal
   shorthand); problem framing survives as the phase's first synthesis step.

Do not commission future work with an unqualified `Phase 1` or `Phase 2` label.
Reading rule for this document: a bare `Phase 2` always denotes the internal
SERP Phase 2 lane, never the Deliver phase. Historical filenames, reports,
handoffs, and receipts retain their original phase language because changing
it would falsify provenance.

Each phase has two possible operator/model turns, but a phase name does not
commission both. Within the Forseti Intelligence Cycle, an owner instruction
that says **Understanding** or uses historical **Phase A** language without
also naming a synthesis deliverable commissions **Acquire & Seal only**. The
task stops after the acquisition seal whether it passes or blocks. A passing
seal makes a later Synthesize turn eligible; it does not authorize or start
that turn. Synthesis requires an explicit current commission or a separately
authorized follow-up.

The two possible turns are:

1. **Acquire & Seal.** Bind the phase-specific question, intended consumer and
   use, scope, and outcome signals. Complete prerequisite and authority checks
   and seal the phase-specific CSB before source-heavy work. Before capture,
   require `CO0` to be the top-level controller with three worker slots and
   record a capability preflight for Google recovery state, the Reddit weekly
   lake reader, both paid-ad transparency routes, and conditional TikTok Shop.
   `BLOCKED_CONTROLLER_CAPACITY` stops before dispatch; it never licenses a
   serialized or checkpoint-only substitute. The first real SERP Phase 1 seed,
   not a sacrificial query, is the Google route-health observation. Then
   resolve every selected source to the current source-family authority and its
   banked recipe-card or recon-index route when one exists. An established
   source-specific route is not replaced by generic fallback browsing: Ulta and
   Quora must be resolved through their existing source-specific records, with
   the recorded route scope, maturity, and typed limitations preserved.
   Scanning and Capture then execute under their own authority and return
   inspectable receipts or typed failures. The turn finishes only by writing a
   durable phase acquisition seal that carries the commission identity,
   canonical phase, bound question and use, resolved route identities,
   scan/capture receipts, source/provenance identifiers, material gaps and
   failures, and seal state. Live chat memory is not part of the seal.
   Before sealing, a material load-bearing route/capture failure with a
   plausible owner-controlled remedy triggers one compact, consolidated
   owner-unblock escalation naming the affected question or success signal,
   attempted route, observed blocker, smallest owner action needed, and what
   remains blocked. This is event-triggered, not a checkpoint for every route
   issue. A resolved escalation resumes acquisition and records the real
   receipt. An unresolved one leaves acquisition blocked unless the owner
   explicitly narrows the commission; it is never carried forward merely as a
   final-report caveat, silent omission, or inferred absence.
2. **Synthesize.** Start in fresh context from the phase's governing
   acquisition gate: Understanding synthesis requires its own passing phase
   seal; Deliver synthesis requires the passing Understanding seal plus a
   typed capture return for every consumed supplement (a supplement that would
   change a sealed claim ceiling requires a Deliver-phase seal first). Verify
   that gate before synthesis. Then craft, validate, and hand off the phase
   deliverable without making an evidence, route-exhaustion, provenance, or
   coverage claim that the governing seal and returns do not support.

The two turns optimize differently. Acquire & Seal maximizes decision-useful
completeness under the integrity floor: every material information job is
supported, contradicted, meaningfully bounded, or honestly blocked/gapped before
the seal can pass. Compactness, actor count, and token minimization do not lower
that acquisition standard. The Synthesize turn applies Smallest Complete
Intervention to the human artifact after the gate passes, preserving the
decisive evidence, counter-case, uncertainty, provenance, reversal conditions,
and next action.

Every company Understanding uses this internal Acquire & Seal order: bind the
question, validate the commission-stage board, and complete the capability
preflight; run or validly reuse SERP Phase 1; feed its typed ledger and queues
into the `CO1`-`CO3` specialist
fan-out; wait for their terminal returns; run SERP Phase 2 from the combined
findings; then seal. Reddit/community capture is `CO3` fan-out work, not a
SERP Phase 2 responsibility. A missing or materially blocked SERP Phase 2 result remains
visible in the existing route, receipt, provenance, and gap fields and forces
the blocked seal state; a non-material typed Phase 2 limitation stays honestly
recorded without being promoted into a material blocker. The SERP phase
labels are lane-local and do not replace the canonical Understanding and
Deliver phase names.

Treat the Phase 1-to-fan-out boundary as a hard dispatch lock. `CO1`-`CO3` work
must not be dispatched or started until `CO0` fresh-reads durable artifacts for
the same commission and cycle and verifies all of the following: the capability
preflight says it preceded the first network capture; SERP Phase 1 is terminal
or has a validly adjudicated reuse receipt; and its typed ledger plus every
required role queue are present and non-empty. Role descriptions elsewhere in a
commission or handoff are future work, not authority to bypass this lock. If
specialist work starts early, interrupt it, quarantine its outputs, and record
the sequencing incident. Excluding those outputs prevents their admission but
does not make the preflight chronologically prior; that cycle cannot receive a
passing seal under a false pre-capture claim.

The commission-stage coverage ledger always carries required rows for Google
Ads Transparency Center, Meta Ads Library, and the current Reddit weekly Data
Lake read. Paid-ad attempts execute after `CO1` binds the exact advertiser
identity. `CO3` reads the weekly lake before new Reddit discovery. Native
TikTok, Instagram, and YouTube capture is conditional on an ambiguous listing
whose native content could change the bound answer. TikTok Shop is conditional
on a creator-led subject or evidence that the venue is commercially material;
its route failures remain typed as wrong country, TikTok-specific block, or
unhealthy egress session.

Use the playbook's default four-evidence-actor route unless the owner explicitly
overrides it: `CO0` plus exactly `CO1`, `CO2`, and mandatory `CO3`. The
dispatcher is mechanical and is not a fifth evidence actor. `CO3` always owns
customer/community evidence and selected depth; adaptive depth controls how far
it continues, never whether the actor or customer-understanding job exists.
Each specialist terminal is single-writer. `CO0` consumes its returned hash but
does not edit the file; corrections return to the owning actor, which publishes
a replacement hash.

Broad decision-neutral company Understanding uses
`broad_company_understanding_v1`. It separates evidence-family coverage from
independent depth within each material family. Before a passing seal, its
current entry floors are:

- 12 outside-in units from 12 independent origins;
- 750 deduplicated retailer-review rows across at least two distinct corpora,
  five product contexts, three categories, and observed low/mid/high rating
  bands;
- 20 independent Reddit/forum threads across at least four communities and
  three topic categories; and
- 30 source-native social posts from at least 20 creators, at least two
  platforms, and at least two observed perspectives among positive, neutral,
  critical, and mixed.

Subject-owned native posts may contribute source-native content-unit depth when
their relationship to the subject is explicit in the ledger or its pinned
terminal evidence. They count as one creator after creator-ID deduplication,
must be reported separately from non-owned posts, and cannot support an
independent-creator-landscape claim. The creator floor remains the independent
distribution counterweight to repeated posts from any one account.

When the subject is a consumer brand and product/customer experience is
material, the commission receipt selects
`broad_consumer_brand_understanding_v3`, and the acquisition seal binds an
`understanding_evidence_depth_v4` ledger. The selected completion profile stays
in the company record through completion; it is not a commission-only field.
The profile retains the aggregate entry floors
above except that Reddit/forum depth rises to 40 usable unique threads. Forty
is a minimum floor, never a completion target. The mechanical
`reddit_candidate_frontier` remains complete only when every discovered
candidate thread has a terminal disposition and an accounted discovery job,
the captured set equals the ledgered independent threads, non-captured
candidates carry reasons, and each independent thread pins its own source-native
artifact. This proves bounded route accounting, never that the whole internet
was searched.

V4 separates evidence strength from decision maturity. `strength` remains
`signal`, `recurring`, or `strong`; every material axis separately declares
`decision_maturity`, `closure_basis`, and `claim_ceiling`. A source-rich axis may
close `decision_mature` with `evidence_supported` and
`strong_qualitative`. A source-limited axis may also close `decision_mature`
after `route_bounded_source_exhaustion`, but only with
`bounded_observation_only`; scarcity never becomes affirmative attack/defend
authority. Fewer than 40 Reddit/forum threads additionally requires the explicit
floor exception after every selected target and planned family is terminal.
Forty never closes a materially open axis.

Decision maturity also requires a compact `decision_usefulness` block on the
existing product-axis ledger row; do not create a parallel score or report. The
block records `status`, the customer tension, segment/condition, behavior or
purchase consequence, competitor destination, strongest counterevidence, the
competitive decision that changes, decision-bearing support references, and
limitations. `evidence_supported` may close only as `decision_useful` or
`strategically_material`. `route_bounded_source_exhaustion` closes as
`source_exhausted_but_weak`: it is decision-mature because the selected routes
are exhausted, not because the sparse evidence licenses a strong attack or
defend claim. `evidence_covered_but_not_decision_useful` remains open for a
passing seal. Decision-bearing references must already be valid support
references for that axis; the validator proves shape and traceability, while
human review judges whether the synthesis is strategically warranted.

Before a broad consumer-brand Understanding Acquire & Seal artifact
(historically a "Phase A seal") is accepted for synthesis or landed,
commission the final delegated review-and-patch under the project-owned
delegated-review convention. This requirement is deliberately bound to the
broad consumer-brand completion profile, whose citation surface motivated it;
extending it to another completion profile is an owner decision taken when
that profile first carries decision-bearing source-native citations. The reviewer reads every
`decision_bearing_support_ref` in its source-native body and verifies that the
subject product or brand is locally anchored, the cited body supports the
assigned axis and role, alternative-product returns/repurchases/preferences are
not attributed to the subject, and the named counterevidence genuinely tests
the competitive decision. The reviewer then reads two independent
source-native spot checks per material axis from outside that axis's cited
decision-bearing bundle. One load-bearing mismatch expands only the affected
axis to a stratified ten-reference sample. Expand beyond that axis only when at
least two of those ten references fail load-bearing checks, the mismatch cannot
be resolved, or the same defect class appears across at least three axes. Full
corpus rereading is not the default. Any bounded patch must be revalidated
against the acquisition seal and separately adjudicated by the Chief Architect.
This semantic review catches valid-but-misattributed citations that mechanical
shape and hash checks cannot.

The same semantic pass scans decision-bearing axis labels and prose for a
price, affordability, usable-quantity, or value comparison even when the
machine-visible axis ID does not contain `price`, `value`, `quantity`, or
`cost`. Signals include cheaper, premium, worth it, better deal, cost per use,
more product, less product, lasts longer, and needing less product. When one is
present, the reviewer verifies that both products carry the required
`price_size_context`, or an explicit unavailable/not-directly-normalized
disposition. This is a language-model semantic catch for missed concepts, not
permission to invent a conversion, infer equal value from sticker price, or
upgrade a validator pass into semantic proof.

When an adjudicated re-derivation or semantic remediation proves that no
subject-owned counterevidence survives on an axis, that axis records
`counterevidence_absent_verified: true` in its decision usefulness beside
prose naming the disposition; the counterevidence-role reference requirement
is waived for exactly that axis, which otherwise keeps its evidence-supported
closure and true strength. Fabricating a counterevidence reference, or
downgrading a strong axis to `source_exhausted_but_weak` solely to evade the
requirement, are both defects; carrying the marker while also citing a
counterevidence-role reference is a contradiction the validator rejects.

Call this terminal boundary the **decision frontier**. Do not call it a value
frontier: `value` remains the customer-facing product proposition (benefit,
quantity, durability, and performance for price). Do not call it a discovery
frontier either; more relevant pages can exist after decisions are mature.

Before Phase 2, `CO3` runs two pipelined customer-discovery lanes. The
**source-neutral corroboration lane** starts with a bounded unrestricted-domain
brand/product review baseline, then uses retailer-review coding and other
captured evidence to run claim-directed editorial, specialist, retailer, and
comparison checks. A search result, featured snippet, or AI-generated search
summary is a discovery pointer only; evidence credit requires the source-native
body, relationship classification, and an admitted evidence unit. Company-owned
and DTC pages establish product identity, availability, price, ingredients, and
official claims, but never independently corroborate customer outcomes.

The **candid community lane** groups Reddit discovery into named query families
and runs the proven high-yield set in this order: balanced brand-plus-axis
baseline; behavior/consequence/displacement; a bounded consumer-native
product-name or shorthand probe without the brand where the identity remains
unambiguous; and condition/post-use. Qualify generic product names with the
category or use case rather than issuing ambiguous or blindly copied long-title
queries. This probe tests whether brand-term search missed insider language. By
default, it covers only a bounded set of hero products. Admit a non-hero product
only when already captured evidence exposes a material axis, condition, behavior
consequence, competitor destination, contradiction, or sampling-risk question
for it; never turn the family into a catalog-wide crawl. It remains the third
mandatory family and is still recorded under the existing
`brandless_exact_product` family kind; that kind name is historical slot
identity, not a demand for exact official product titles. Community-diversity
probing is conditional on observed concentration.

The two lanes may run concurrently. A material signal in either lane launches
only a bounded counterpart check for the same axis, segment, condition,
consequence, or competitor destination; it does not duplicate every query
across sources or wait for a whole discovery cycle to finish. Every community
family records kind, role, axis scope, planned time, jobs, and terminal status;
job `executed_at` timestamps prove actual family order, while `planned_at`
remains planning lineage. The validator compares mandatory family completion
with the actual hash-pinned Phase 2 search-job timestamps, not a self-declared
query-family role. A run that predates this ordering rule may preserve one
exact, run-scoped `pre_contract_historical_run` exception with the observed
boundary timestamps, matching cycle ID, reason, and
`future_runs_covered: false`; the exception records the defect and never becomes
a reusable waiver. Every batch records useful-thread yield separately from
structured material additions. The validator reconciles the family, job,
artifact, candidate, and batch accounting rather than accepting prose closure.
That family, candidate, and batch reconciliation covers the community lane
only. Source-neutral lane work carries no separate query-family or candidate
frontier: its selected pointers stay inside the existing planned-job and owning
route accounting, and its admitted units stay inside the existing evidence-unit,
relationship-typing, and family-depth rules. No mechanical check proves the
source-neutral lane ran, so its coverage and gaps stay honestly stated in the
existing route, receipt, and gap fields rather than inferred from a passing
seal.

The profile renames the human-facing outside source
family to **External company, editorial and industry context** and adds the
cross-family product-axis contract below. Historical consumer v1/v2 ledgers are
audit-only through `--allow-legacy-consumer-v1` and
`--allow-legacy-consumer-v2`; they do not satisfy a new run.

The v4 ledger inventories every observed material product-experience axis as
`pain`, `delight`, or `mixed`, with a terminal disposition. `signal` establishes
possible existence. `recurring` requires at least three qualifying independent
origins across two non-retailer evidence families. `strong` additionally
requires axis mentions in two deduplicated retailer corpora, at least six
qualifying distinct non-retailer origins across at least two families with at
least two origins in each, and an explicit retailer choice consequence
appropriate to the axis polarity. Reddit threads are discussion origins;
social posts deduplicate to creator; external units deduplicate to publisher or
institution. Same-origin items remain citable but add no
corroboration-strength credit. These are hybrid entry bars, not stopping
quotas. Same-topic independent sources remain useful. Owned,
retailer-operated, disclosed paid/affiliate, and relationship-unknown social
posts do not satisfy independent axis corroboration. External support must be
typed as consumer editorial or trade press, carry an explicit
`apparently_independent` relationship, and come from an independent origin;
company profiles, corporate/transaction records, paid or affiliate material,
and relationship-unknown external units do not qualify.

Axis cardinality is evidence-derived, not fixed. A prior brand's axis count is
not a template quota for the next brand. Preliminary mechanical or semantic
coding may nominate a provisional inventory so Phase 2 and continuation work
know what to test; final adjudication may merge, split, rename, add, or exclude
those nominations when the source-native evidence warrants it.

V3 hash-pins a `retailer_product_axis_coding_v1` view. It covers every eligible
unique text-bearing review in each admitted corpus, reconciles excluded
no-usable-text rows to the corpus denominator, and preserves native review ID,
product context, incentive state, axis codes with axis-specific choice outcomes,
overall choice outcomes, and a source-row reference. Separating the outcomes
prevents a consequence attributed to one product issue from being copied onto
every issue mentioned in the review. Every product context must belong to its
declared retailer corpus. The validator recomputes per-corpus axis mentions,
negative/positive choice rows, and disclosed-incentive counts. Cross-retailer
pooling is allowed only when corpus boundaries, selection, and deduplication are
comparable; otherwise report providers separately. These are captured-sample
incidences, never market return rates or customer-population prevalence.

Every material v4 axis receives three adaptive Phase 2 goals after a hash-pinned
axis inventory exists: `corroborate_or_segment`, `compare_switch_or_value`, and
`disconfirm_or_strongest_delight`. Search results are discovery pointers, not
evidence; a `captured` job must resolve to a source-native body and a ledgered
evidence unit. Every selected target is reconciled as `used`,
`captured_excluded`, `no_material_yield`, `blocked`, or `unavailable`. Every
material axis needs at least three usable non-retailer support units, whether
or not they add a new distinct-origin credit, unless that axis records proven
source exhaustion. Related same-topic sources remain as sharpening volume;
exact duplicates collapse and do not inflate distinct-origin spread.

Community support is comment-coded: thread and comment identity, product
context, axis, contribution, choice, alternative brand when present, explicit
outcome, source reference, source-native creation timestamp
(`comment_created_utc`, read from the preserved raw body or source metadata at
coding time, never inferred), and parser limitation. The timestamp is an
acquisition-time obligation because the coder is already reading the raw body;
it is what lets later synthesis attribute evidence to eras (formula
generations, attention cycles) without reopening raw files. Synthesis
deliverables may consume dates but are not required to display them. Every
usable independent Reddit/forum thread has at least one such row, and an axis
support reference into a community thread must be backed by a coding row for
that axis and thread carrying the same contribution, choice, and alternative
brand; a support claim no coded comment states is invalid. SERP or search-registry
artifacts never satisfy a native-body reference. A useful new thread is
informational yield, not an automatic reopen. A material addition is limited to
a new axis, evidence-tier change, mechanism, segment or condition, behavior
consequence, competitor destination, contradiction, sampling-risk change, or
competitive-action change, and must name its affected axes, evidence references,
and decision effect. It reopens only those axes and directly adjacent axes when
the recorded decision effect justifies adjacency. Each material axis closes on
two later live continuation families that include it in scope, use different
family kinds, queries, and artifacts, occur after the mandatory high-yield set,
and add no material addition affecting that axis. The two families may still add
usable threads. Each batch declares `new_usable_reddit_threads`, and the
validator recomputes that count against captured candidates. "Later" and reset
ordering use observed job execution time, not merely when a family was planned.

Do not perform final semantic adjudication while acquisition is still capable
of changing the corpus. Use the provisional axis inventory and a lightweight
maturity scan to identify open axes, run the evidence-floor plus material-
exhaustion loop (including only targeted follow-ups), terminally account the
frontier, and only then finalize decision usefulness and run the delegated
semantic check. The early scan guides acquisition; it is not the final verdict.
Owned social rows carry a normalized `YYYY-MM-DD` observed date and
direction-event tags so synthesis can derive a factual direction timeline without
a separate Phase A artifact. Preserve the source's original date text in the
pinned source artifact.

These are anti-token entry floors, not completion quotas, prevalence samples,
or market-representativeness claims. A passing seal additionally requires
explicit echo/syndication adjudication, every material seam dispositioned,
every material axis to be `decision_mature` under one of the two truthful
closure bases, the aggregate Phase A decision frontier to have no open axes,
and every remaining move to be typed as dominated, source-exhausted,
unsafe/prohibited, blocked with no route, or non-material. Same-family
independent evidence is welcome when it corroborates, contradicts, sharpens,
segments, explains, or changes confidence. Specialists may lock a deterministic
batch for execution efficiency, but they must not freeze the whole adaptive job
set before evidence reveals the next material frontier.

The phase acquisition seal uses `phase_acquisition_seal_v3` accounting and is
validated by `run_phase_acquisition_seal_validation.py`. Every planned job is
present exactly once in completed, blocked, or unrun state, including every
licensed SERP Phase 2 query. A valid empty Phase 2 decision receipt does not
erase unrun acquisition. The seal also carries artifact hashes, pending jobs,
reusable artifacts and their invalidation conditions, and the Phase 1
continuation mode (`full`, `bounded_salvage`, or `stop`). Bounded salvage and
stop remain blocked. Resume re-hashes reusable artifacts and executes only
pending jobs unless the question, bytes, currentness, or owning authority
changed.

For `broad_company_understanding_v1`, v3 also hash-pins an
`understanding_evidence_depth_v1` ledger. The validator recomputes the profile's
family-depth and distribution metrics from that ledger, requires its subject
and cycle identity to match the seal, and checks the closure receipt. Job
completion without that evidence-depth and saturation accounting cannot
authorize synthesis. Historical `phase_acquisition_seal_v2` artifacts are
preserved and may be checked only with the validator's explicit
`--allow-legacy-v2` audit switch; they do not satisfy the current broad-
Understanding completion contract.

For `broad_consumer_brand_understanding_v3`, v4 instead hash-pins an
`understanding_evidence_depth_v4` ledger and applies the product-axis,
row-derived retailer-incidence, comment-coding, source-native capture,
target-reconciliation, focused-search, candidate-frontier accounting, proven
query-family, decision-maturity, and axis-aware closure checks above. A passing
family-count ledger without those
checks is invalid. Repository-tracked evidence artifacts must be pinned with
repo-relative locators; absolute locators are reserved for machine-local
raw-lake roots outside the repository, and the validator rejects a
repo-internal absolute locator as nonportable.

For company Understanding, the seal must carry non-empty job accounting for
`serp_phase1`, `official_retailer_authorization`,
`google_ads_transparency`, `meta_ads_library`, `retailer_full_pdp`,
`reddit_weekly_lake`, `reddit_community_scout`, and `serp_phase2`, and must
represent all five execution phases: `serp_phase1`, `CO1`, `CO2`, `CO3`, and
`serp_phase2`. A typed no-work decision is still a planned job; omission is not.
Triggered TikTok Shop and native TikTok, Instagram, or YouTube capture inherit
the same accounting rule.

When both turns are explicitly commissioned, two turns are the normal budget,
not a fake-success cap. A blocked, skipped, silently substituted, or
incompletely captured required route leaves Acquire & Seal blocked. It does not
manufacture a Synthesize turn. Context growth or compaction never excuses losing
route choices or evidence: those facts live in the durable seal.

The cycle optimizes toward six outcome signals:

1. **Question fit:** answer the bound question for the intended reader and use,
   rather than drifting toward the easiest available data.
2. **Evidence foundation:** trace every load-bearing judgment to dated evidence;
   check critical independence/currentness; record required routes and failures
   honestly.
3. **Reasoning quality:** make the evidence-to-judgment chain reconstructable;
   distinguish facts, assumptions, and judgments; address serious alternatives
   and disconfirming evidence when relevant.
4. **Honest uncertainty:** place confidence and material gaps beside the
   judgments they affect and name useful change conditions; do not force
   probability language onto descriptive facts.
5. **Implications and foresight:** explain what findings mean for the intended
   reader and what observable developments would change the view; do not force
   unsupported forecasts or recommendations.
6. **Communication efficiency:** make key judgments easy to find, order the
   body by importance, remove repetition and padding, and keep audit detail
   available without letting it dominate the narrative.

These are compact outcome checks, not a numerical score, six report sections,
six additional workflow gates, or six repeated receipts. The working score,
weights, caps, bands, acceptance thresholds, and scoring automation remain
outside this contract.

Production priority is explicit: optimize for decision usefulness under an
integrity floor. First secure question fit, trustworthy evidence, and honest
uncertainty; these foundations may not be traded for prose, apparent
decisiveness, speed, or implications. Once they hold, put the largest analytical
effort into sound reasoning and useful implications. Only then compress for
clear delivery. Communication efficiency clarifies supported intelligence; it
cannot manufacture substance.

Satisfy the signals through real task evidence and function, not headings,
labels, citation volume, ritual sections, forced forecasts, repeated confidence
labels, or padding. The producing actor receives this priority order but no
numerical weights, bands, caps, or score-optimization instructions. Independent
post-delivery evaluation remains a separate playbook-owned handoff.

Public-reaction engagement belongs in the board as resonance context, not
judgment. CSB may ask rows to preserve source-visible upvotes, helpful votes,
likes, views, shares, comment counts, reply counts, score state, visible
sort/rank/order, pinned/hearted/official-response markers, direction, visible
audience-fit basis, baseline context, and discount reasons when supplied or
source-backed. Every engagement snapshot used during acquisition-record
construction or analysis preserves its observation date at minimum and an ISO
8601 `observed_at` timestamp when available, together with the source locator;
relative source labels remain in the pinned body. The final human deliverable
may omit the displayed date when it is not decision-relevant, but its working
provenance may not. CSB must not turn those engagement facts into demand proof,
Commit/Scale support, credibility, independence, graph weight, classifier
mapping, final resonance weight, or Action Ceiling.

The temporary prompt is too high-lock-in to adopt wholesale because it mixes
five different objects in one artifact: commission intake, venue playbook,
source registry, forecast-target schema, and graph retrieval schema. Installing
that bundle as authority would silently decide product, Judgment, Data Capture,
and prompt-packaging questions that are not all settled.

## Understanding Acquire & Seal Route Revision Contracts (Route 1.1.0+)

These contracts bind the versioned company-Understanding route revision whose
operating sequence, version block, and append-only changelog live in the CSB
playbook (`understanding_acquire_seal_route`). The acquisition seal records
the route version actually used in an `understanding_route` block, and
`run_phase_acquisition_seal_validation.py` enforces the deterministic shapes
below at the seal boundary. Relationship interpretation, campaign clustering,
and competitor directness remain evidence-backed judgment under the existing
review lanes; the validator proves shape and traceability, never semantic
truth.

### Campaign-Evidence Integration View

One controller-owned post-fan-out integration job (route
`campaign_evidence_integration`, phase `campaign_integration`) joins already
captured evidence — CO1 owned posts and Google/Meta ad observations, CO3
creator-authored units with separately preserved audience comments, CO2
canonical product/SKU, retailer/market, and landing-destination identity —
into one hash-pinned `campaign_evidence_view_v1` JSON artifact. There is no
standing `CO4` specialist, no creator crawl, no second evidence lake, and no
standing monitor. Creator-registry records contribute identity and
source-visible metric inputs only, never campaign membership or
commercial-effect proof. The view is derived run-scoped acquisition
accounting over already captured typed evidence (ledger social/external rows,
ad-transparency projections, CO2 identity); it is not a Silver Vault entity
type, a campaign object contract, or a coordination/manufactured-demand
judgment, which the data-lake Silver Vault contract reserves for
Gold/Judgment.

The route-accounting row is required and material. A passing seal requires its
planned integration job set to be fully completed, not merely named alongside
a completed-looking view block.

Each view unit carries: `unit_id`; `source_role` from
`owned_post | paid_ad | creator_authored | audience_comment | retailer_review
| retailer_qa | community_post` — creator-authored content and audience or
customer evidence never merge into one role, and a post's engagement never
transfers to its comments; publisher/creator/account identity; the brand
binding plus product/SKU and claim bindings as string lists (empty when none
were observed); source surface
and raw source references; `published_at`, `observed_at`, and `captured_at`
(`captured_at` required; unknown source timestamps stay null, never
invented); `relationship_posture` from
`owned | retailer_operated | disclosed_paid_or_affiliate |
partnership_byline_observed | apparently_independent | relationship_unknown`
— missing disclosure stays `relationship_unknown` and is never treated as
organic; a creative/message fingerprint or bounded cluster reference when
derived; ad/creator/landing-page `linkage_posture` from
`direct | inferred | unknown`; `independent_origin_key`;
`independent_origin_credit`; and claim ceiling, conflicts, and missingness.

Independence rules: `independent_origin_credit: true` requires
`apparently_independent`, and one `independent_origin_key` receives at most
one credit regardless of repeated units — same-origin echoes are citable but
never independence. Engagement facts remain observation context and never
become evidence weight.

Clusters: do not force a durable `campaign_id` that public evidence cannot
establish. A message/episode cluster is `basis: direct` only when every
member unit's linkage posture is `direct`; otherwise it is `basis: inferred`
and must carry explicit provenance and a reversal condition. Each cluster's
member list contains unique unit IDs.

The integrator may emit targeted capture requests for exact posts, ads,
landing pages, or dates that would resolve a material link; each request is
terminally dispositioned (`captured | blocked | no_longer_material`) before a
passing seal, and fulfilled requests run as ordinary jobs in the owning
routes. The integrator does not launch broad crawls, infer spend or
conversion, or issue market conclusions: campaign integration is post-fan-out
synthesis for acquisition control, not Deliver synthesis.

### Competitor-Set Closure

The route installs three explicit comparator states; no separate standing
competitor lane is created:

1. `candidate_comparator_frame` after SERP Phase 1: typed, provisional, and
   sufficient to guide fan-out. The frame's candidate and competing-product
   identities scope the existing `CO1`-`CO3` fan-out capsules. The frame is
   never frozen: complaint-, retailer-, creator-, and substitute-borne
   candidates remain discoverable during fan-out.
2. `adjudicated_comparator_set` after specialist returns plus SERP Phase 2:
   exact subject/product identities, evidence origins, axis-level explanation
   of why and under which observed conditions customers choose either product,
   price/size context where observed, an evidence-derived terminal comparator
   role, and claim ceiling.
3. `phase_a_competitor_context_closed` at the acquisition seal: every
   material candidate is terminally dispositioned; no candidate silently
   disappears.

Route 1.2.0 makes "sufficient to guide fan-out" falsifiable. Every Phase 1
frame candidate carries a `prefanout_qualification` posture:
`core_fanout | bounded_watch | rejected_before_fanout`, plus its comparator
role from `direct_peer | value_substitute | adjacent | unresolved |
non_competitor`. SERP is the discovery map, not confirmation. Every frame row
points to the open-comparator SERP observation that surfaced it. A
`core_fanout` candidate additionally binds both exact product identities, the
shared customer job, exact-product identity evidence recorded separately for
the subject and for the competitor from an owned page or exact PDP, and at
least two independent comparison origins across at least two
of these source roles: Reddit/community, retailer review, creator-authored, or
independent editorial. Two rows from one origin, two origins from only one
source role, and two origins that re-cite the same evidence unit under
different keys do not meet the core bar. SERP snippets, retailer co-placement,
owned comparison claims, and ad positioning never count as those independent
comparison origins.

Candidates that fit the product shape but do not meet that recurrence and
source-role bar remain `bounded_watch` with the exact gap; obvious entity,
format, or job mismatches close as `rejected_before_fanout`. This is bounded
shortlist confirmation inside Phase 1, not a miniature competitor commission
and not a second Phase A. Later lanes may still add or correct candidates.
Route 1.2.0 does not add a creator-coverage parity gate. The creator-value
assessment handoff tests whether the existing route changes any material
judgment before a recurring creator obligation is considered.

Route 1.3.0 adds one light public-identity check to the origins used for that
core bar. Each origin records a source-visible `public_actor_key` (for example,
a normalized platform handle, retailer reviewer ID, or publication/author
key) and its posture relative to the other credited origins from
`no_match_observed |
possible_same_actor | confirmed_same_actor | unavailable`. Only
`no_match_observed` with a non-placeholder key earns independence credit;
duplicate keys, possible/confirmed overlap, and unavailable identity remain
usable evidence but cannot together manufacture two independent origins.
The semantic pass compares exact/normalized usernames, profile URLs, and
source-visible disclosed links or codes. A display name alone can raise a
possible overlap but cannot prove one. This is deliberately a light public
check, not a complete cross-platform identity graph.

For every material candidate, the existing lanes owe comparator evidence or a
typed gap — never silence: `CO2` retailer/category adjacency and exact
product identity (retailer co-placement alone is never directness proof);
`CO3` retailer-review and Reddit/community comparison evidence, kept as two
separate evidence roles — explicit comparisons, substitutes,
switch/return/repurchase destinations, and complaint-borne alternatives;
campaign-integration creator comparison
evidence — head-to-heads, dupe claims, and repeated claim propagation,
relationship-typed; and `CO1` owned/advertiser positioning and named
comparisons as actor-strategy evidence, never independent customer proof.
An `observed` lane points to its evidence references. `None_found` and
`blocked` are valid bounded outcomes only with a gap reason. Retailer reviews
and Reddit/community observations are public customer-language samples, not
representative sentiment or population polling.

For a `core_fanout` competitor, retailer work has two scopes inside the same
Phase A and the same `CO2`/`CO3` fan-out; it is not a separate rival Phase A:

1. **Exact competing product** — capture the full selected,
   comparable-retailer corpus for that product: exact PDP/product state in
   `CO2` and the exposed retailer-review/Q&A corpus in the separate `CO3`
   customer role. A blocked or unavailable selected retailer remains a typed
   gap.
2. **Relevant franchise** — map the source-visible sibling products and their
   retailer/owned prominence only far enough to establish whether the exact
   product is hero, likely major, supporting, or unclear. A sibling receives
   full exact-product capture only when its observed role or customer-choice
   evidence could change the comparison.

A full rival-company assortment is not a standing third scope. It is licensed
only when the bound question is itself brand/portfolio-level. This rule changes
acquisition volume, not phase count. No percentage-of-focal quota substitutes
for the evidence need.

Each material candidate also binds an evidence-backed local portfolio-role
assessment for the exact competitor product or named franchise:
`explicit_hero | likely_major | supporting | unclear`. `Explicit_hero`
requires an explicit source; `likely_major` requires a multi-source inference;
`supporting` requires positive evidence rather than absence; and `unclear`
preserves the unresolved gap. Where a source exposes an ordered position, the
seal records the source or retailer, list/category scope, market, observation
time, evidence references, and either the numeric rank plus list size or the
source-visible relative label. An empty observation set carries its gap reason.
No source-local observation may be promoted into a universal product rank,
sales rank, market share, or cross-retailer league table. Review volume alone
does not establish portfolio role. A promoted direct competitor binds at least
one shared axis so its stronger evidence is decision-comparable to the subject
product rather than merely voluminous.

Observable brand positioning is context, not the primary competitor verdict.
`CO1` owned/ad evidence and relationship-typed campaign evidence show what each
actor emphasizes; customer and retailer-review lanes show whether people
repeat, reject, or ignore it. Phase 2 may use that context to explain an axis,
but must not relabel actor strategy as customer choice. The highest-value
comparator record therefore joins exact-product choice, franchise importance,
and observable positioning without collapsing those evidence roles.

When price parity, value, or usable quantity is compared, the cited observation
must carry price, currency, size, unit, market, and observation time for both
products, or state which element is unavailable. Different mass and volume
units remain `not_directly_normalized` unless a source-backed conversion is
licensed, and a posture that licenses direct comparison (`same_unit` or
`source_normalized`) cannot span two currencies. Equal sticker price alone is
never equal quantity or equal value.

The seal validator mechanically requests this context only on a material
candidate whose `shared_axis_ids` contains `price`, `value`, `quantity`, or
`cost`. Alternative axis names and price/value comparisons outside that
machine-visible shape are caught by the final semantic review described above;
validator pass does not prove that every semantic price comparison was detected.

SERP Phase 2 first consolidates the specialist and campaign-integration
returns into an evidence-only `competitive_choice_explanation` for every
material candidate. Its primary output is the axis-level answer: what observed
evidence favors the subject, favors the competitor, splits by condition, or
remains unresolved; why; under which conditions; and the exact evidence
references. Only then does it derive the terminal comparator role from
`direct_peer | value_substitute | adjacent | unresolved | non_competitor`.
The role is a compact consequence of the explanation, not a substitute for it.

Each axis finding consumes the intelligence-cycle-wide contract at
`forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`.
The finding binds one bounded proposition and records its support posture,
independent-origin count, source roles, engagement and behavior references,
counterevidence, conflict posture, and causal ceiling. `Isolated` testimonial
or interpretive evidence cannot set a directional advantage. A competent
`directly_observed` trace may establish only its bounded descriptive fact.
`Resonance_supported` requires source-native engagement evidence and may claim
audience endorsement, never an independent-experience count. `Mixed` evidence
must remain `split_or_conditional`, and an unchecked conflict posture cannot
carry a directional finding.

Route 1.4.0 adds the Judgment-owned Semantic Evidence Integration closure job
after every selected acquisition and Phase 2-triggered job is terminal and
before the seal. Follow
`forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`.
The controller verifies and hash-pins the admitted evidence set, renders
bounded prompts, and gives them to a fresh agent; no runner calls a model API.
The agent reads for meaning, splits multi-product or multi-axis statements,
preserves conditions and opposition, and reconciles paraphrases. Deterministic
code alone accounts every alias, resolves source artifacts, de-duplicates
origins, checks source-role competence, derives support posture, and writes
`semantic_evidence_integration_view_v1`.

Route 1.5.0 keeps the 1.4 closure job but requires
`semantic_evidence_source_v2` and method v2.
Every admitted unit carries surrounding product context that cites one of the
bundle's hash-pinned source artifacts;
`product_candidates` are search/coding hypotheses, never identity proof. The
semantic pass binds an exact subject and comparator from the item plus its
context or leaves the item unresolved/out of scope. Context may identify the
product but may not be rephrased as though the evidence author made its
claims.

Route 1.6.0 keeps that source-pinned product binding and widens the admitted
denominator to the declared final captured Phase A corpus. The controller uses
`semantic_evidence_source_v3` to account every captured source-native leaf as
semantically assessed, mechanically excluded with an exact reason, or blocked.
It preserves conversations, creator/audience threads, individual retailer
reviews, and published objects as containers with capture-envelope facts.

Route 1.7.0 keeps the full-corpus method but corrects its acquisition boundary.
Only Reddit/community conversation text and retailer review text are exhaustive
semantic sources. Owned pages, PDP facts, advertising, creator posts,
editorial, and other acquired materials stay hash-verified structured
references and remain available to judgment without pretending they are one
customer-language denominator. Retailer membership is proven from source-native
review records under raw-byte-pinned files, never from a whole-file substring.

The evidence-depth ledger also carries one `phase_a_serp_source_frontier_v1`.
For the exact jobs sealed in SERP Phase 1 and Phase 2, plus every bounded
focused-search packet, a fresh agent reads each source-bearing result row for
meaning and marks it `routed`, `duplicate`, or `excluded`. Deterministic code
checks exact row coverage and target resolution; it does not infer relevance
from keywords. Routed rows bind to an existing native-capture or
locator-recovery target. Google people-also-ask and related-search prompts are
not external sources. This is a bounded search-surface census, not permission
to paginate or crawl the web.

The semantic runner bounds actual rendered UTF-8 bytes, including prompt
instructions, schemas, axes, context, and formatting. It may reconcile in
child-referenced levels. At every level deterministic code owns exact child
accounting, product/comparator/version binding, condition and polarity lineage,
stale hashes, acyclic provenance, and duplicate-credit prevention; the agent
owns meaning equivalence. Batch response v2 distinguishes first-hand report,
personal agreement, attribution/echo, question, speculation, observable fact,
and actor strategy while keeping uncertainty separate. Echoes, questions,
creator framing, and unknown or overlapping actors cannot manufacture
independent customer experience.

Before seal, the agent consolidates meaning-equivalent emerging labels and the
compiler preserves every original label. Every parent preserves the exact
union of its children's emerging labels, and every validated consolidation is
carried unchanged through later levels. A lower-level blocker therefore stays
visible and blocks seal. Every stage and node compilation also carries the
root batch-compilation hash, which finalization must match exactly.
Integration view v2 exposes separate
semantic-unit, evidence-item, container, independent-origin, source-role,
engagement, support, opposition, and mixed-container counts. A seven-thread
count is therefore never silently restated as seven independent people. This
is evidence structuring only, not prevalence, safety, market conclusion,
causation, or recommendation.

Current axes guide but do not cap discovery. A material emerging axis reopens
only the affected work and invalidates the prior view; a nonmaterial candidate
is explicitly dispositioned. Route-1.4-and-later axis findings carry `proposition_refs`
to the view. Each material comparator carries distinct stable
`subject_product_id` and `competitor_product_id` values at route 1.5.0, and each referenced
competitive-choice proposition must bind exactly those IDs in that
orientation. Any retained inline claim-support display is a mechanically
derived compatibility projection and never a second authority. A passing seal
requires a current view whose admitted and accounted evidence counts match,
no unresolved material evidence, and terminal dispositions for emerging axes.

Phase 2 runs targeted/J5 delta probes only for a named material gap left by the
combined returns; it does not reacquire the fan-out corpus. A `promoted`
(decision-ready) candidate requires both exact product identities and an
`observed` choice explanation with at least one shared axis. `Partial` and
`unresolved` records preserve their gap and cannot be promoted. The seal's
comparator closure gives every frame or lane-emitted candidate one terminal
disposition from
`promoted | rejected | watch_listed | role_bounded | explicit_gap`.
Watch/validate-once/parked decision outcomes map to `watch_listed`;
harvest-junk and adjudicated non-competitors map to `rejected`;
self-variants, mediators, and corroborative-only surfaces map to
`role_bounded`; sub-finding-grade or unresolved candidates close as
`explicit_gap`. This remains acquisition evidence, not a recommendation,
market conclusion, or Deliver artifact. Phase A promises decision-usable
comparator context, never an
exhaustive-direct-competitor claim, representative market sentiment, or
rival-by-rival depth; a separate competitor commission is triggered only when
a named downstream decision needs depth beyond the closed Phase A context.

### Conditional Product/Claim Verification

```text
verification_request = reconciled product identity
                     × material evidence axis or contradiction
                     × publicly verifiable unresolved claim
```

Candidate products before CO2 are discovery anchors only. CO2 breadth plus
customer/creator/external evidence selects material product contexts; a
non-hero product enters only through a material axis, condition, consequence,
competitor destination, contradiction, or sampling-risk trigger. Verification
is a conditional adjustment job, not a catalog-wide first-wave specialist and
not a requirement to run every instrument for every product. Each request
carries the reconciled product identity, its trigger kind
(`material_axis | contradiction | condition_or_consequence |
competitor_destination | sampling_risk`), the trigger's evidence references,
and the unresolved claim; a request without that material trigger is a
defect. A completed return attaches instrument-level verdicts, provenance,
failures, and claim ceilings to the shared evidence model and may reopen the
affected acquisition axis; it may not start Deliver. An emitted request left
`not_run` blocks a passing seal.

### Retailer State And Movement Semantics

CO2 captures the point-in-time current-state baseline. Route semantics, with
no new schema for terminology alone:

- one comparable observation = `retailer_state_snapshot`;
- two observations with stable retailer/product/market/scope identity —
  stable retailer-local product identity plus confirmed storefront, currency,
  and variant pins under the retail-PDP capture authorities — may derive a
  `retailer_state_change` carrying distinct old and new evidence references
  plus a non-empty change summary;
- no prior comparable observation = `movement_unresolved_baseline_only`;
- stockout, review velocity, assortment presence, and promotion remain
  proxies, never sales or productivity;
- refresh is commissioned by a material event or change question, never a
  standing monitoring obligation.

A movement or trend event from one observation is a defect: one observation
is a state snapshot.

### Seal Accounting For The Versioned Route

The v3 seal's `understanding_route` block carries `route_version`,
`comparator_closure`, `campaign_evidence_integration`,
`semantic_evidence_integration`, `verification_requests`, and
`retailer_state_accounting`; the playbook's seal
template shows the field shapes. The seal validator enforces: known route
version; the `campaign_evidence_integration` route accounting and
`campaign_integration` phase at route 1.1.0 and later; at route 1.2.0,
per-frame-candidate pre-fanout posture, open-comparator discovery references,
and the core exact-identity/shared-job/two-origin/two-source-role bar; at route
1.3.0, public-actor identity de-duplication for credited origins and one
axis-level competitive-choice explanation for every material candidate; at
route 1.4.0, a material terminal semantic-integration job, current hash-pinned
view, exact evidence coverage, proposition-to-axis resolution, source-role
competence, and material unresolved/emerging-axis closure; at route 1.5.0,
contextual semantic method v2, distinct stable product IDs for material
comparators, and exact candidate-to-proposition product binding; at route
1.6.0, view v2/method v3, complete captured-item accounting with no blocked
leaf, exact capture-envelope/container shape, consolidated emerging-axis
lineage, and per-proposition evidence-stack counts; view schema/subject/cycle
binding; at route 1.7.0, the semantic-source/structured-reference boundary,
raw-byte retailer source manifest, and exact bounded SERP-row frontier;
binding and per-unit enums; independent-origin credit rules; cluster
linkage/provenance rules; terminal comparator dispositions with exact-product
identity binding and shared axes for `promoted` candidates;
per-material-candidate product/franchise role, source-local observed-position
or explicit-gap accounting, and separately sourced retailer-review and
Reddit/community lane evidence; verification triggers and terminal statuses;
and distinct old/new retailer-observation references plus a non-empty change
summary. Stable retailer/product/market/scope comparability remains
evidence-backed judgment over the cited CO2 observations; the validator does
not prove it from opaque reference strings. A seal sealed before route
versioning began
(2026-08-07) has no stamped version and is audited with
`--allow-preversion-route`; recording `1.0.0` retrospectively never claims it
was historically stamped. A seal stamped with a known older route version (a
recorded route retention) is likewise audit-only under the same switch and
never satisfies the current route contract. That audit is version-symmetric in
both directions: the older seal still owes every obligation its own stamped
version introduced — a `1.1.0` seal owes the full 1.1.0 accounting above, not
only its campaign-integration row — and owes no obligation a later version
introduced. Route 1.2.0's pre-fanout and price/size checks are therefore never
back-claimed onto a `1.1.0` or `1.0.0` seal, and route 1.3.0's identity and
choice-explanation fields are never back-claimed onto a 1.2.0 seal. Route
1.4.0's semantic-integration job and proposition references are never
back-claimed onto a 1.3.0 seal, and 1.5.0's contextual product-binding
requirements are never back-claimed onto a 1.4.0 seal. Route 1.6.0's full-
corpus, hierarchy, capture-envelope, consolidated-axis, and evidence-stack
requirements are never back-claimed onto a 1.5.0 seal.
Route 1.7.0's source boundary, retailer manifest, and SERP frontier are never
back-claimed onto a 1.6.0 seal.

## Company Competitive-Intelligence Extension

The canonical representation is:

```yaml
mode: backtest | forward
commission_profile: standard_signal_board | company_competitive_intelligence
time_posture: recency_first | longitudinal
```

These axes are orthogonal. A one-company subject whose identity is a Brand or
Org defaults to `company_competitive_intelligence`, including when the
Brand/Org identity remains unresolved. Preserve one-company-at-a-time:
comparators may interpret the subject, but deep competitor treatment requires a
separately named follow-up commission.

`recency_first` is the universal default. It uses the deterministic `0-30`,
`31-90`, `91-180`, and `>180` day ladder. `longitudinal` is an explicit
override only for change, recurrence, or trajectory across a declared period,
and it requires both the period and rationale. A named event is a route or
query inside the selected posture. Historical observations may be primary only
inside the declared longitudinal period and must never be relabeled current.
Aligned signals across independent venues at one point in time are spatial
alignment, not `co-movement`; `co-movement` is reserved for a future
longitudinal product, requires at least two observation dates, and is not
emitted by this contract.

The one-company report is decision-neutral. Its required lenses are portfolio
and retail architecture; observable positioning; offerings and claims; markets
and channels; recent strategic and operating moves; customer and community
response; bounded competitor or substitute context; contradictions; and
evidence gaps. It must not infer pain,
buyer, ICP, priority, urgency, willingness to pay, outreach, offer, or wedge.

Before optional deepening, resolve the small high-yield core through the existing
ledgers: current offering and portfolio architecture; exact current commercial
and retail expression where material; channel, distribution, and geography
posture; strategic and operating chronology; and applicable material events.
This creates no new section, field, or source quota and does not replace another
material lens. A material unresolved core job blocks the acquisition seal; other
remainders stay typed gaps and non-claims. Commission archives, supply, ads or
creators, competitors, search trends, and similar deepening only for a named
unresolved inference job.

When offerings, retail presentation, or customer experience are material, the
company route acquires bounded portfolio breadth before product depth. Begin
with enough owned evidence to bind the subject, categories, franchises, known
parents, and canonical product identity. Owned surfaces remain canonical for
company portfolio and franchise expression. Preserve bundles and sets without
counting them as ordinary parents. This does not require hidden SKUs, immaterial variant
permutations, an automated identity resolver, or a complete global SKU graph. Capture source-visible target/use-case, price-tier,
channel, and geography differentiation; owned/retailer prominence, new/launch,
and distribution state; product/franchise concentration and overlap evidence;
explicit strategic statements or moves; and shared capability or dependency
evidence where exposed. These inputs authorize an evidence-bounded outside-in interpretation of visible
portfolio roles, positioning, channel posture, and dependencies. They do not
authorize claims about internal management intent, revenue, margin, cash
generation, sell-through, or undisclosed operations.

Use company-owned evidence to establish the officially named US retailer board
before probing retailer surfaces. When at least four company-authorized,
target-market, route-admissible third-party retailers exist, select and attempt
at least four, favoring venues that add distinct assortment, commercial, or
customer evidence. The company-owned DTC site does not count. When fewer than
four qualify, select all that qualify and record
`AUTHORIZED_RETAILER_SHORTFALL` with the observed count and reasons; never fill
the floor with an unauthorized, duplicate, or market-unpinned venue. Resolve
Sephora explicitly. When it is officially named and route-complete, it counts as
one selected retailer and remains subject to the primary rule below. When
another qualified retailer is available, replace a blocked selected route to
restore four usable venues while preserving the block. Use the existing
coverage-ledger requirement, rationale, status, yield, access, and typed-gap
fields to preserve each authorization and route test with its exact result.
Current result types include `NOT_LISTED`, `ROUTE_BLOCKED`, `MARKET_UNPINNED`,
`SURFACE_NOT_EXPOSED`, and `AUTHORIZED_RETAILER_SHORTFALL`; never infer a
listing or award completion credit for a failed or unobserved route.

For every selected retailer, acquire its available grid surface,
deterministically union and reconcile exact listings with the owned candidates,
then return to owned evidence to close the complete publicly exposed denominator
and typed gaps. Retailer listings do not become canonical owned identity merely
by appearing in a grid. Then acquire one baseline PDP for each reconciled exact
retailer listing with
exact identity and parent/variant/listing relation, price and promotion,
availability, aggregate rating/review state, assortment/exclusive cues,
timestamp, and residuals. Preserve the full raw source. Retain source-visible
retailer-native extensions such as merchandising, badges, fulfilment,
seller/authenticity, related products, Q&A availability, review provider, and
native identifiers or metadata. The common baseline does not require a complete
global franchise -> parent-product -> variant/SKU -> retailer-listing graph.

Sephora, Ulta, and Target expose brand or assortment grids. Before selecting
Amazon, classify it separately from marketplace presence:
`COMPANY_AUTHORIZED` requires a company-owned source that explicitly names or
links the target-market Amazon store or retailer;
`MARKETPLACE_IDENTITY_VERIFIED_NOT_COMPANY_AUTHORIZED` requires exact branded
storefront or seller/listing identity but carries no company authorization; and
`MARKETPLACE_PRESENCE_UNVERIFIED` means exact identity is not proven. Only
`COMPANY_AUTHORIZED` counts toward the four-retailer floor. A
verified-but-not-company-authorized route may supplement marketplace, price, or
customer evidence with that limitation attached; an unverified route remains a
discovery pointer. Amazon exposes a query-bound ranked-search window complete
only for its declared query and reachable result window, never a guaranteed
complete or authorized-only catalog. Projection capability is not route
admission. Point-in-time retailer metrics are traction proxies, never sales,
share, or trend.

Only after the qualified-grid and exact-parent PDP baseline may expensive review
or Q&A depth be selected. Evidence-selected depth may resolve established
prominence; founding, strategic, promoted, or new centrality; concentrated
complaint or customer friction; a plausible contrasting extension or weak link;
a material contradiction; or an incident. One product may perform multiple jobs,
there is no fixed product count, and a named non-duplicative job must justify
every deepening. Hero status is an earned conclusion, never a selection premise.
Use calibrated labels such as `prominence candidate` and `observed weak-link
candidate`; do not call a selection a sales leader, best-performing product, or
worst product.

Review volume is a channel-, tenure-, assortment-, and syndication-sensitive
prominence prior, not sales, demand, or commercial-performance evidence. Keep
counts separate by retailer and corpus; never sum them unless exact corpus
identity and deduplication justify the operation. Sephora retains its existing
source-specific review capture policy. For each selected non-Sephora retailer,
default the analytical review window to source-labelled `Most Recent`/newest
when supported; record requested and actual ordering plus any fallback. Before a second retailer
review capture receives independent-customer-evidence credit, bind its retailer
collection context, observed provider plus its evidence reference, provider
tenant/store, product/grouping scope, origin/syndication identifiers, and
measured row overlap against already
captured corpora. A different provider is neither necessary nor sufficient for
independence, and a provider name is never inferred from the retailer alone.
Same-corpus sort windows are not independent. When two requested sort windows
substantially overlap, dedupe by source-native review identity, report captured occurrences and unique rows
separately, and redirect further depth to a materially different corpus,
category, or product when available. Review volume alone must not optimize the
selected set. After exact-parent baseline coverage, map every selected-retailer
listing to its observed provider tenant/store and product/grouping collection
context. Collapse duplicate listings, variants, sets, or placements only when
that evidence proves one shared corpus. Acquire one bounded onboarding window
for every distinct accessible review corpus, or preserve a typed
`NO_REVIEWS`, `NOT_EXPOSED`, `ROUTE_BLOCKED`, or identity-unresolved outcome.
This corpus-board completion is a breadth obligation: it prevents hero-product
or review-volume selection from defining the reusable customer evidence layer.
It is not a full historical crawl and does not require manual interpretation of
every captured corpus. Expensive interpretive and Q&A depth remains
category-balanced and evidence-selected; stop when its named jobs and material
seams are supported, contradicted, bounded, or typed as gaps. If missing grid
pages or category totals, identity conflicts, or review comparability could
change the corpus board or analysis selection, emit a portfolio-coverage or
selection gap and continue acquisition or block; never silently select from a
partial list.

The working primary is chosen from the officially named retailer board,
target-market relevance, assortment breadth, structured evidence depth, and
route admissibility. When Sephora is officially named for the target market and
its US grid is route-complete, it must be selected and is the retail primary for
normalized product, assortment, and review controls. If it is officially named
but blocked, unpinned, or incomplete, preserve Sephora in the selected outcomes
and use the strongest complete selected retailer as the working primary; do not
fake Sephora coverage. Another retailer may supply a product- or franchise-level
baseline when Sephora omits that material product or variant, or may supply a
separate non-duplicative information job, without displacing a usable
company-level Sephora primary. Primary status selects the richest
normalization/reference surface; it does not excuse baseline coverage at any
other selected retailer. This official-first rule uses the existing coverage
ledger and creates no automatic completion credit. Retailer evidence does not
become internal company fact.

This MGT portfolio-selection method explicitly accepts that listings which do
not expose a distinct review corpus may remain at parent-PDP baseline, while
every distinct accessible corpus receives a bounded onboarding window or typed
gap. Review volume remains channel/tenure/syndication biased and supports
prominence ordering only; observed complaint or weak-link candidates are not
market-wide worst-product conclusions; and a full historical review crawl,
global SKU graph, and automated identity resolver remain out of scope. Upgrade
when unresolved breadth, identity, syndication, or comparability could
materially change the corpus board or selected analysis. Assortment and review
evidence alone cannot establish sales, cash generation, growth, cannibalization,
internal intent, control, competitive strategy, or operational leverage.

A completed report carries this substrate in a first-class
`Portfolio And Retail Architecture` section. It exposes, in order: the owned
portfolio denominator; product, claim, and price architecture; the qualified
retailer corpus; evidence-selected product depth; outside-in portfolio
interpretation; and strategic positioning, markets, and channels. Compact
matrices summarize the denominator, selected retailer board, selected depth, and
portfolio roles with observation IDs and typed gaps. Headings do not establish
completion: the evidence and coverage ledgers remain the audit floor.

When a decision-material retailer-review corpus has row-level ratings,
source-visible incentive posture, and a reproducible boundary, the company
report may derive the prompt-defined retailer-review approval signal. Preserve
all rows in raw capture; exclude explicitly disclosed incentivized rows only
from the derived primary view, including labels such as sponsored, gifted,
complimentary, free sample, sweepstakes, or paid partnership; group four/five
stars as positive and one/two/three stars as below-positive; and disclose the
eligible denominator, excluded count, selection basis, and whether the corpus
is complete or bounded. Express both percentage fields to one decimal using
round-half-up. Rows lacking an incentive marker are `not marked
incentivized`, never confirmed organic.
Neither this view nor an explicit-non-incentivized sensitivity establishes
representative demand, market consensus, prevalence beyond the defined corpus,
causal incentive distortion, nor a comparison without a comparable method and
denominator. Omit the signal when its row-level or corpus-boundary inputs are
not reproducible.

Retailer-authored product suitability/taxonomy and reviewer-self-reported
attributes are separate evidence classes. Age, skin type, skin concern, or
similar reviewer distributions must carry the captured-corpus denominator, the
attribute-reporting denominator, missingness or coverage, selection/filter
basis, and visible incentive posture. Precision within a large reporting
subgroup does not make that subgroup representative of all reviewers,
purchasers, or customers. Cross-product comparison requires comparable methods
and missingness boundaries. This is guidance-bound narrative using existing
observation provenance and ambiguity fields, not a new schema or validator.

A completed company report additionally carries the synthesis layer as
guidance-bound narrative (no schema or validator fields): an Executive
Intelligence Brief preamble of three to seven five-field conclusions (claim /
evidence bound / commercial consequence / confidence / next observable) at
maximum decisive directness in consequence and plainly stated,
evidence-calibrated confidence inside the decision-neutral boundary — with
inference worded as inference even at full directness, and small or
uncorroborated samples supporting existence rather than concentration, rate,
or comparative claims absent a cited comparator base — at most three chain
cards for the evidence-selected representative franchises, using one
representative parent product per franchise and never padding or presupposing
hero status, that do not imply willingness-to-pay, representative demand,
defection, or demand capture — and the central-promise voice plus internal
adjudication frame (where observable value resides, what drives it, whether it
is strengthening, weakening, or not proven, and what threatens it) with
invalidation conditions;
this frame does not replace decision adjudication as the product center.
Publicly visible concentration appears in the channels lens; invalidation
signals appear in the chronology lens; the customer-choice mechanism chain with
the five-way complaint classification and stated-sample proportionality rules
appears in the community lens; and defensibility raw material (collected,
never judged) in the
comparator lens. Understanding collects generic defensibility raw material once;
the Deliver phase may request only decision-specific fresh supplements, never a
general re-scan. Retail, customer, and claims research routes receive first attention,
subject to the named-job and substitution rules rather than quotas. The
linked-commercial-claim admission principle governs what the narrative
foregrounds; plain-language section leads plus SKU/item-reception and
known/inferred/unknown Markdown matrices keep the ledgers behind the narrative;
lens-status `complete` means covered for the commissioned purpose with typed
gaps, never exhaustive. Conclusions gain strength only from evidence bounds,
next observables, and calibrated confidence, never from overclaiming evidence,
certainty, or representativeness.

Every included CSB item must perform a named, decision-material information job:
it must have a credible route to changing the action, action ceiling, rival
assessment, or hold condition. Do not include a source, row, observation, venue,
or capture target when an equal-or-better included item performs the same job.
Structural rows that document a rejected, dominated, unavailable, or
`not_applicable` route are exclusion/accountability records, not evidence
inclusion and not completion credit.

Every material observation preserves source URL, publisher, publication date,
event date, access date, evidence status, source class, fact domain, and
syndication group. A current page is not evidence that every claim on it is a
current event. Community observations remain external/customer evidence and
cannot establish representative demand or internal company fact. Syndicated
copies are not independent corroboration.

Reddit and Quora remain explicit search-hygiene considerations in the company
coverage ledger so their selection or rejection is visible. External scouting
is commissioned only when the venue performs a named decision-material job and
is not dominated by an equal-or-better included route. Zero yield is a route
result, never completion. Generic and specialist forums use category-aware
hidden-venue discovery rather than a universal platform list. Blocked, missing,
dominated, or non-material coverage becomes a typed gap, exclusion, or
`not_applicable` record with rationale.

For Reddit, the current weekly Data Lake read is mandatory and precedes new
external discovery; it is not a substitute for exact thread/comment capture.
Valid content-mode `www_reddit_realchrome_cdp` packets and admitted old-Reddit
packets feed the same weekly reader. Capture Spine preserves a source block; it
does not bypass one.

CSB owns profiles, source-family requirements, time posture, and typed
gaps/requests. Scanning owns intelligent-walk selection. Capture owns venue
access and preservation adapters. CSB does not contain either runtime.
Company Surface references are `candidate_only` and `not_imported`. The report
has no arbitrary length, page, source-count, or observation cap. No numeric
source, row, observation, venue, or capture target establishes completion.
CSB completion means the material information jobs and candidate routes are
defined, not that acquisition is complete or a participant packet is frozen.

For a recurring or actively radarred source family, CSB should route Scanning
or Capture to inspect the existing Data Lake before external acquisition:
relevant Silver/current view first, then packet or catalog inventory, then raw
material when necessary. This is a reuse, freshness, and coverage preflight,
not proof of current external reality. Absence from Silver is not absence from
the lake or the external world, and a missing read model does not block
external acquisition.

## Current Source State

The controlling product thesis says Forseti is outside-in consumer-demand decision
intelligence for distinguishing durable demand from transient or manufactured
demand; beauty/personal-care is the first vertical (Vertical) and the engine remains
vertical-portable (`docs/decisions/forseti_product_thesis_consumer_demand_v0.md`).

The offer hypothesis narrows the first proof offer to US-market indie/DTC beauty
or personal-care operators facing live 30-90 day consumer-demand allocation
decisions (DecisionEvent), while preserving Forseti's broader offer boundary
(`forseti/product/spines/product_lead/offer/forseti_offer_hypothesis_v0.md`).

The buyer-proof packet binds proof requirements, not commission-board behavior.
For this commission layer, those requirements are downstream context: they say
why clean signal provenance matters, but they do not turn commission into a
proof or demand-decision surface
(`forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md`).

The current gate-run criteria and demand-scan adjudication packet are adjacent
historical/context artifacts. Under this correction, their gate language should
not be copied into the commission object. Any future durable prompt should
separate signal-board generation from demand classification
(`forseti/product/spines/commission_signal_board/dispatch_rules/forseti_demand_gate_run_commission_criteria_v0.md`,
`forseti/product/spines/scanning/admissibility_checkability/forseti_demand_scan_gate_adjudication_packet_v0.md`).

Data Capture doctrine already treats source-family adaptation as satellite
work: source-family feasibility, blind spots, capture-fidelity heuristics,
threaded-community conventions, review-platform conventions, and
human-assisted-capture requirements stay source-family-specific until they
survive comparison across non-overlapping families or the owner accepts an
exception (`forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md`).

Adjacent source-family records support subfamily separation. Reddit Graph
Frontier separates Reddit-native discovery surfaces from external web/SERP
discovery and keeps web-discovered subreddit candidates distinct rather than
laundering them into Reddit-source intake
(`docs/workflows/reddit_graph_frontier_b2b_marketing_traversal_record_v0.md`).
Quora has one bounded post-merge capture proof: a profile-backed CloakBrowser
Quora search-packet capture with caller-bound detail sufficiency
(`docs/workflows/quora_b2b_postmerge_capture_calibration_v0.md`); the capture
playbook's route-maturity note treats that as bounded Quora evidence, not broad
Quora reliability, session durability, or proxy/geo proof
(`forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md`).
AEO is currently non-origin visibility corroboration only, not a gate-recordable
or independent demand-origin surface
(`forseti/product/spines/scanning/source_families/answer_engine/demand_search_interest_sourcing_and_gate_delta_spec_v0.md`).
Creator monitoring is designed as core machinery plus per-platform profiles:
IG fills first, while TikTok, YouTube, and Reddit creator profiles are
named-deferred seams
(`forseti/product/spines/capture/core/source_families/social_media/instagram/forseti_creator_monitoring_policy_architecture_v0.md`).
LinkedIn is no-live, planning-only under strict privacy rails; it is not news,
not consumer signal capture, and not live graph capture by default
(`forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_lane_index_v0.md`).

Prompt policy requires any durable Forseti prompt to be authored through
prompt-orchestration or to apply that contract in full. The temporary prompt is
not yet a durable prompt artifact.

Fresh exact-term search in this worktree found no durable hits for the temporary
prompt's schema names: `commission_gate_brief`, `future_information_policy`,
`graph_family_plan`, `forecast_targets_for_downstream`, `backtesting-first`, or
`evidence_cutoff_at`. Existing code provides lower-level capture/provenance,
cutoff posture, projections, graph-frontier patterns, and action-band Judgment
scoring, but not a commission signal-board schema, runner, or output contract.

## Mini God Tier Target

Owner direction sets a **mini god tier** bar for the future commission signal
board. Under Forseti's mini-god-tier doctrine, that is a capability-target lens
with mandatory visible limitations, not a validation, readiness, proof, or scope
expansion claim (`docs/decisions/forseti_mini_god_tier_doctrine_v0.md`).

For this board, mini god tier means: most of the value of a heavier signal
intelligence and graph-prep system, at prompt-first/manual-first speed and cost.
The board should create a materially better handoff to retrieval, graph,
demand-classifier, forecasting, and judgment lanes than an unstructured scan.

Required MGT output shape (a structural contract, not a collection minimum):

- hierarchical source-family and subfamily map;
- source posture per subfamily: available now, planned lane, deferred,
  manual-only, not authorized, or noisy/deferred;
- graph retrieval brief;
- graph-ready signal rows;
- mandatory counterevidence paths;
- campaign-overlap and duplication risks;
- cutoff-safe chronology for backtests;
- visible limitations.

Visible limitations:

- not exhaustive web monitoring;
- not a standing source registry;
- not automated crawling or platform scraping authorization;
- not Discord scraping by default;
- not LinkedIn live access or relationship-graph analytics;
- not a graph database;
- not graph scoring;
- not a demand classifier;
- not buyer proof;
- not validation or readiness;
- not client-facing output.

## Source-Family Map

The source map should be hierarchical:

```text
source_family -> subfamily -> surface -> observable -> signal_role -> graph_role
```

The board should preserve subfamily identity rather than collapsing everything
into broad buckets. This avoids mixing source families with different access,
noise, provenance, independence, and graph behavior.

| Source family | Subfamilies / surfaces | Signal role / content | Capture posture |
| --- | --- | --- | --- |
| Forums / community | Reddit; Quora; category-relevant generic or specialist forums discovered for the subject | external/customer language, comparisons, objections, corrections, and response context | Keep Reddit/Quora as explicit search-hygiene considerations, but commission external scouting only for a named decision-material job with no equal-or-better included substitute. Record dominated, non-material, blocked, and zero-yield routes without treating them as completion. Other forums use category-aware hidden-venue discovery, not a fixed universal platform list. Community evidence is never representative demand or internal company fact. Execution stays with Scanning/Capture. |
| Reviews | retailer reviews, marketplace reviews, brand-site reviews, specialist fragrance reviews | experience claims, recency, complaints, repeat-use hints, contradiction checks | Do not collapse to aggregate stars. Preserve recency, source conventions, row-level incentive labels, corpus size, captured count, selection route, and truncation. |
| Creator / social video | Instagram, TikTok, YouTube, shorts/reels, affiliate/creator posts, later Reddit creator/community personalities | attention spread, creator clusters, campaign risk, audience language, propagation timing | IG has current adjacent capture/discovery work; TikTok/YouTube/Reddit creator profiles are planned/deferred seams. |
| Retail / PDP | Sephora, Ulta, Amazon, Nordstrom, brand PDPs, retailer search/category pages | availability, assortment, stock/discounting posture, review context, retailer corroboration | Retail/PDP is corroborative and operationally useful; it is not consumer-origin by itself. |
| Search / discovery | Google Trends, search-volume provider, SERP, preserved SERP packets, marketplace search, on-site search | interest traces, query language, discovery routes, hidden-venue pointers, counterevidence queries | Search-interest can carry attention/interest signal. Search-Surface MGT is a source-route scout only; methodology and pins stay with the answer-engine/search-interest source-family spec, while execution routes to Scanning frontier/exact-query work or Capture direct-source requests. |
| AEO / answer engines | Google AI Overviews, Gemini, ChatGPT, other answer-engine surfaces | answer visibility, cited-source ecosystem, entity association, visibility gaps | Visibility annotation only unless a later owner-approved schema amendment changes this; never an independent demand-origin surface today. |
| News / editorial / trade | trade publications, editorial, newsletters, specialist blogs, press | launch chronology, industry framing, awareness, third-party narrative | News is a distinct family; LinkedIn reposts of news point back to the actual source. |
| Professional / org-motion | ATS/careers pages, hiring pages, founder/executive public posts, partnership announcements, LinkedIn when explicitly routed | hiring/movement, organizational intent, operator-side propagation | ATS/careers pages are better movement sources than LinkedIn. LinkedIn remains no-live/planning-only unless separately authorized. |
| Owned channels | brand site, brand socials, email archive, product pages, press releases | official chronology, brand claims, launch framing | High chronology value, low independence. |

Answer-engine/search-interest/AEO route note: for source-class or routing questions,
open `forseti/product/spines/scanning/README.md`, then
`forseti/product/spines/scanning/source_families/answer_engine/demand_search_interest_sourcing_and_gate_delta_spec_v0.md`,
then `docs/research/answer_engine/` as research/probe evidence only. Do not route
through legacy search-lane history, and do not treat AEO as product authority,
gate-recordable, validation/readiness/proof, capture authorization, scraping,
scaling, or implementation authorization.

### Search-Surface MGT Standing Route Card

Standing behavior: when a commission has an open question about market language,
comparison/confusion, hidden venues, or counterevidence queries, the board should
consider a Search-Surface MGT route row rather than leaving search discovery as
background prose.

Use this row pattern:

```yaml
source_family: search_discovery
source_subfamily: search_surface_mgt
signal_role: search_interest
row_purpose: source_route
evidence_status: provided | source_backed | to_retrieve | gap
```

CSB may point to preserved SERP packets as routing evidence, but it does not run
Google capture, score search demand, or treat query count, rank, repeated SERP
presence, PAA/PAS, product modules, or autocomplete as proof.

Preferred handoff:

```text
CSB source-route row
-> Scanning exact-query / frontier selection
-> Capture P1 direct-source acquisition when concrete URLs or surfaces exist
```

### Category-Benchmark Search-Interest Read (Consumer-Brand Phase A)

Owner decision (2026-08-06): every future broad consumer-brand Phase A run
includes one bounded category-benchmark search-interest read, so Deliver can
separate brand-specific attention decline from category-wide decline instead
of assuming the difference. Shape: one one-shot pull in the run's primary geo
plus a worldwide check, 5-year window, **web-search property**, comparing the
subject brand term against the head terms of each product category the
subject competes in.

Category terms must be bound from the run's own artifacts before capture; this
card does not authorize the operator to coin a head term. In the run's
`coordinated/` directory, use the acquisition record's product-specific search
coverage rows for hero and secondary product names, `community_axis_coding.json`
`product_context` values when present, and
`evidence_depth_ledger.json` `product_axes[].decision_usefulness` for named
alternatives and the product conditions they serve. The hash-pinned
`consumer_brand_axis_inventory.json` `axes[]` is a customer pain/delight-axis
inventory, not a product or category-term source.

Before the pull, record in the run commission or capture handoff a
term-derivation table with product family, exact candidate term, the source
phrase that supports it, and artifact locator. A term is usable only when that
exact generic category phrase appears in a run artifact or the run's explicit
commission binds it; a product name or alternative brand name alone is not
permission to invent an adjacent synonym. If any material product family lacks
a bound head term, record the read as `unresolved — category terms unbound` and
do not pull. The founding commission bound lip balm / lip mask / lip butter /
lip oil and skin tint / tinted sunscreen / tinted moisturizer; those examples
are not a reusable derivation rule.

Record the verdict explicitly against this decision rule: subject curve
declining while its category curves rise or hold → brand-specific decline;
category curves deflating alongside the subject → category-wide decline;
mixed or below-threshold → unresolved, never forced. Founding instance,
decision rule, and report shape:
`docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_return.md`.

Boundaries: this is a bounded per-run one-shot authorization class only — the
standing search-interest series, cadence machinery, and vendor selection
remain unsourced (AR-04 open); capture obligations and limits-visibility
follow
`forseti/product/spines/capture/core/demand_durability_indicators/search_interest/demand_durability_indicator_search_interest_capture_profile_v0.md`;
values are the source's 0–100 relative index only (no sales, share,
prevalence, or population claims; below-threshold rows use the exact phrase
"below the Google Trends reporting threshold under the recorded geo/window").
Shopping-property purchase-leaning checks are not part of this read (it is
web-search property, above) and are not relied upon until a run demonstrates
above-threshold coverage (2026-08-06 outcome:
inconclusive-below-threshold).

Before capture, the run commission or term-derivation table must bind one exact
subject-plus-hero-product query as the anchor and cite the source product name;
the operator does not choose it ad hoc. Carry that exact query in every batch
so cross-batch comparison is bridgeable. If it is unbound, record the read as
`unresolved — anchor unbound` and do not pull. The founding anchor was "summer
fridays lip butter balm"; it sat near the reporting threshold against category
head terms, so the resulting bridge was weak.

## Graph-Light Contract

Graphing belongs in the commission ecosystem, but the signal board should carry
only the lightest complete graph responsibility.

The board owns:

- seed entities;
- adjacent brands (Brand)/products (Product)/formats;
- source families and subfamilies to check;
- creator slices and planned/deferred creator platforms;
- counterevidence paths;
- node types to retrieve;
- edge types to retrieve;
- campaign-overlap and duplication checks;
- cutoff-date rule for backtesting;
- graph-ready signal rows.

The board does **not** own:

- graph construction;
- graph database or persistent graph infrastructure;
- graph scoring;
- centrality or clustering algorithms;
- evidence weighting;
- demand classification;
- forecast probabilities;
- judgment or recommendation.

Most important: **graph weight is not signal weight**.

`graph_weight` means a source or row is useful for relationships, propagation,
duplication, chronology, campaign clustering, or counterevidence routing. It
does not mean the source is strong evidence of demand. AEO can be graph-useful
while remaining non-origin visibility. LinkedIn can be graph-useful for
professional/org-motion relationships while remaining weak as consumer demand
evidence. Creator surfaces can be graph-rich while still requiring
non-creator confirmation downstream.

The future prompt should therefore separate:

```yaml
source_family: <family>
source_subfamily: <subfamily>
surface: <specific venue or route>
observable: <what can be seen>
capture_posture: available_now | planned_lane | deferred | manual_only | not_authorized | noisy_deferred
row_purpose: chronology | source_route | signal_unit | contradiction | gap | classifier_handoff | recency_priority
graph_role: seed | node_candidate | edge_candidate | propagation_path | campaign_overlap_check | counterevidence_path | none
graph_weight_hint: high | medium | low | none   # relation utility only, never signal strength
signal_role: consumer_language | review_experience | creator_attention | retail_corroboration | search_interest | aeo_visibility | org_motion | owned_claim | none
```

Two board-local clarifications keep this taxonomy from leaking into the lanes it
feeds:

- **Board labels are board-local; they are not demand-classifier families.** The
  source families and `signal_role` values above organize evidence for handoff;
  they do not map one-to-one onto the demand classifier's existing families. In
  particular, `org_motion` here means professional / hiring / partnership
  movement, with retail presence filed separately under Retail / PDP — it is
  **not** the existing G4 demand-classifier label, where "org-motion
  corroboration" refers to retail presence
  (`forseti/product/spines/scanning/source_families/answer_engine/demand_search_interest_sourcing_and_gate_delta_spec_v0.md`).
  The demand classifier owns the board-`signal_role` -> classifier-family mapping; the
  board only labels and routes, consistent with the owner correction that the
  classifier owns the demand check.
- **`row_purpose` and `signal_role` are distinct fields.** In the source-family
  map, `signal_role` records the *signal content* a family yields. The schema's
  separate `row_purpose` field records the job of the row inside the board
  (`chronology | source_route | signal_unit | contradiction | gap |
  classifier_handoff | recency_priority`). A future prompt and the Owner
  Decision 2 field set should
  not conflate the two.

## Section Adjudication Matrix

| Prompt section | Decision | Rationale | Owner / next handling |
| --- | --- | --- | --- |
| 3. Required mode contract | Adopt with modification | The `backtest` cutoff and future-information exclusion are directionally right and align with zero-spoiler backtest doctrine. For a board, the mode controls evidence admissibility and chronology, not verdict authority. | Carry into future prompt as required evidence preflight; client-facing mode stays deferred. |
| 4. Intake schema | Modify | The schema is useful, but it should become a signal-board brief: candidate, decision context, time window, source families/subfamilies, known unknowns, and evidence constraints. It should not decide buyer proof or demand. | Rewrite through prompt-orchestration if owner accepts the direction. |
| 5. Gate decision / allocation | Reject gate decision; keep allocation as collection guidance | Effort allocation is search hygiene only. No ratio, count, or coverage target establishes inclusion, acquisition closure, or a demand outcome. | Rename this section in any future prompt to signal-collection allocation. |
| 6. Decision-type playbooks | Adopt as signal-route cards | The playbooks are useful venue-routing cards for fragrance/beauty cases, but they are not proof doctrine or demand-classifier logic. | Keep as route cards that identify likely signal families. |
| 7. Source registry | Adopt with guardrails | The public/repeatable/provenance admission rule fits Forseti's public-first posture and Data Capture source-family discipline. The registry should preserve family/subfamily/surface distinctions and capture posture. | Bind each source family and subfamily to capture/provenance fields before any implementation. |
| 8. Creator routing | Adopt with guardrails | Manual creator routing is acceptable for v1 and the non-creator confirmation guardrail is important. Creator evidence should be tagged by platform, origin, graph role, and relation to non-creator signals, not treated as demand proof. | Use as source routing; IG can be first, TikTok/YouTube/Reddit creator profiles stay planned/deferred until their profiles are accepted. |
| 9. Outcome labels | Defer as downstream vocabulary | The labels are valuable for forecast/evaluation design, but the signal board should prepare evidence for downstream evaluation, not score outcomes. | Owner decides whether these labels become a downstream forecast-target registry. |
| 10. Graph-family retrieval plan | Adopt as lightweight graph retrieval brief; defer graph construction/scoring | The graph vocabulary is useful and should carry graphing weight: source relationships, duplication, propagation, counterevidence, chronology, and campaign-overlap risks. Graph weight must remain separate from signal weight. | Future prompt should require graph-ready rows and a graph retrieval brief; runtime schema and graph artifact construction require separate authorization. |
| 11. Redirect and stop rules | Adopt with modification | The rules correctly prevent tunnel vision, weak provenance, campaign-cluster false positives, and unavailable private-data chases. For a board, they control evidence collection quality, not demand outcome. | Carry into future prompt as signal-collection control policy. |
| 12. Required gate output | Replace | The output should be a signal board: source-family/subfamily coverage, signal units, provenance, chronology/cutoff posture, origin/de-duplication notes, graph retrieval brief, graph-ready rows, conflicts, gaps, and classifier handoff notes. It should not output `admit`, `hold`, or `fail`. | Future prompt output contract after owner approval. |
| 13. Standalone sufficiency | Accept only as evidence/signal collection sufficiency | The prompt may be standalone enough to generate a first-pass signal board, but not enough for demand classification, buyer proof, runtime implementation, or client-facing use. | Keep the boundary explicit. |

## Owner Decisions Needed

1. Ratify or replace the working name **Commission Signal Board**.
2. Decide the required structural board fields for handoff to the demand classifier and
   graph/retrieval lanes: source-family/subfamily coverage, signal units,
   provenance, chronology, graph retrieval brief, graph-ready rows, conflicts,
   gaps, and handoff notes are the recommended schema.
3. Ratify the initial source-family/subfamily map, including ATS/careers pages
   as the preferred movement source, Reddit as a forums/community subfamily,
   AEO as visibility annotation, and Discord as noisy/deferred unless a public
   repeatable bounded slice exists.
4. Decide whether the temporary prompt's fragrance-specific playbooks are the
   first signal-board satellite or only an example deck for a broader beauty
   signal board.
5. Authorize a durable signal-board prompt artifact through
   prompt-orchestration, or explicitly defer prompt authoring.

## Recommended Owner Sign-Off Option

Recommended: **adopt-as-modified direction under the name Commission Signal
Board, do not adopt-as-is**.

This preserves the valuable parts of the prompt while avoiding four failure
modes:

- calling commission a gate;
- turning signal collection into demand judgment;
- collapsing graph weight into signal weight;
- turning search quotas or playbooks into proof rules;
- creating a graph/forecast/runtime contract before the owning lanes accept it.

If the owner accepts this option, the next authorized step is a
prompt-orchestrated durable signal-board prompt that references this packet and
the current classifier/proof boundaries. If the owner does not accept it, no
prompt artifact or implementation should be created from the temp file.

## Direction Change Propagation — Axis Decision Usefulness

```yaml
direction_change_propagation:
  doctrine_changed: >
    Consumer-brand Phase A decision maturity now requires an axis-local,
    traceable decision-usefulness synthesis in the existing evidence ledger;
    evidence strength alone cannot close an axis. Actual Phase 2 timestamps,
    rather than query-family labels, enforce the mandatory-family ordering,
    with only an exact run-scoped historical migration exception.
  trigger: validation_philosophy
  related_triggers: [workflow_authority, output_authority]
  controlling_sources_updated:
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/README.md
    - forseti-harness/runners/run_phase_acquisition_seal_validation.py
    - forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/validation-gates.md
    - docs/workflows/forseti_repo_map_v0.md
    - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json
    - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/turn_a_consumer_brand_v3_acquisition_record.md
    - docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md
  intentionally_not_updated:
    - path: AGENTS.md and .agents/workflow-overlay/
      reason: >
        Project-wide workflow and validation mechanics are unchanged; this is
        the consumer-brand Phase A domain contract they already route to.
    - path: docs/workflows/forseti_repo_map_v0.md
      reason: No canonical path, owner, or retrieval route changed.
    - path: historical completed consumer-brand runs
      reason: >
        The contract is forward-facing. Only the still-unlanded Summer Fridays
        p11r7 dogfood is regenerated to exercise it.
  stale_language_search: >
    rg -n "decision_usefulness|evidence_covered_but_not_decision_useful|source_exhausted_but_weak|mandatory_high_yield_query_family_not_pre_phase2"
    forseti/product/spines/commission_signal_board forseti-harness
  stale_language_search_result: >
    Executed 2026-08-04 after implementation. Hits are the owning authority,
    canonical prompt, renderer, validator, and focused tests. No checked live
    surface still treats evidence strength alone as decision maturity, and the
    Phase 2 ordering finding now comes from actual pinned search timestamps.
  non_claims:
    - not proof that an axis synthesis is strategically correct
    - not population prevalence
    - not a new evidence family, scoring system, or per-run report
    - not authorization to acquire sources or start Deliver
```

## Direction Change Propagation — Phase A Semantic Source Review

```yaml
direction_change_propagation:
  doctrine_changed: >
    Broad consumer-brand Phase A now requires a bounded final delegated
    semantic review of every decision-bearing citation plus two independent
    source-native spot checks per material axis. The review verifies local
    subject anchoring, axis/role fit, competitor-event attribution, and genuine
    counterevidence, with affected-axis-first escalation rather than a default
    full-corpus reread.
  trigger: validation_philosophy
  related_triggers: [workflow_authority, output_authority]
  controlling_sources_updated:
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/README.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/delegated-review-patch.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - .agents/workflow-overlay/review-lanes.md
    - docs/prompts/templates/review/delegated_review_return_adjudication_v0.md
    - forseti-harness/runners/run_phase_acquisition_seal_validation.py
  intentionally_not_updated:
    - path: .agents/workflow-overlay/
      reason: >
        Generic delegated-review mechanics, vendor separation, patch bounds,
        and Chief Architect adjudication are unchanged; the new sampling and
        attribution checks are consumer-brand Phase A domain requirements.
    - path: forseti-harness/runners/run_phase_acquisition_seal_validation.py
      reason: >
        Source-body meaning and competitor attribution require semantic review;
        the validator continues to enforce shape, hashes, and reference
        resolution without pretending to judge prose meaning.
    - path: docs/prompts/templates/review/delegated_review_return_adjudication_v0.md
      reason: >
        Return adjudication mechanics are unchanged; the Phase A commission,
        not the generic return template, owns what evidence the delegate reads.
  stale_language_search: >
    rg -n "decision_bearing_support_ref|source-native spot checks|Full corpus rereading|competitor-event attribution"
    forseti/product/spines/commission_signal_board
  non_claims:
    - not a requirement to reread the full captured corpus
    - not mechanical proof of semantic correctness
    - not population prevalence or buyer proof
    - not authorization to start Deliver
```

## Direction Change Propagation — Understanding Scope Default

```yaml
direction_change_propagation:
  doctrine_changed: >
    Within the Forseti Intelligence Cycle, an unqualified Understanding or
    historical Phase A instruction commissions Acquire & Seal only; Deliver
    must be explicitly commissioned and never starts merely because a seal
    passes.
  trigger: lifecycle_boundary
  related_triggers:
    - workflow_authority
    - output_authority
  controlling_sources_updated:
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
  downstream_surfaces_checked:
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/README.md
    - docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md
    - AGENTS.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - docs/workflows/forseti_repo_map_v0.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        The root already routes Intelligence Cycle behavior to the owning
        product authority; repeating this subject-specific default would fork it.
    - path: .agents/workflow-overlay/source-loading.md
      reason: >
        Source selection is unchanged; the amendment changes commission scope
        after the Commission Signal Board sources are loaded.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        Generic prompt mechanics are unchanged; the canonical Commission Signal
        Board prompt now carries the scope default.
    - path: docs/workflows/forseti_repo_map_v0.md
      reason: >
        Canonical entry points and paths are unchanged.
    - path: docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md
      reason: >
        The live handoff already explicitly commissions Acquire & Seal only and
        stops after the seal.
  stale_language_search: >
    rg -n "Turn B — Deliver|Deliver turn|makes Deliver eligible|naming \*\*Deliver\*\*|phases are \*\*Understanding\*\* and \*\*Problem Framing\*\*"
    forseti/product/spines/commission_signal_board
  non_claims:
    - not validation
    - not readiness
    - not authorization to run acquisition or Deliver
    - not a rename of historical artifacts
```

## Non-Claims

- Not owner ratification.
- Not a prompt artifact.
- Not a gate.
- Not a demand classifier.
- Not graph construction or graph scoring.
- Not buyer proof.
- Not validation or readiness.
- Not a scoring engine.
- Not implementation authorization.
- Not authorization to run a scan, capture sources, contact buyers, or produce a client-facing artifact.
- Not acquisition closure, final packet inclusion, or a frozen participant packet.
