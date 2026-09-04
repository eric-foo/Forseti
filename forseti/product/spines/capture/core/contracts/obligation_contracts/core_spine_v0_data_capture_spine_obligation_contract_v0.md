# Core Spine v0 Data Capture Spine Obligation Contract

```yaml
retrieval_header_version: 1
artifact_role: Product-method contract
scope: V0 obligation contract for commissioned Data Capture Spine captures before Evidence Candidate Record, Cleaning Spine, and Judgment Spine.
use_when:
  - Running or reviewing commissioned Data Capture Spine work.
  - Checking whether a captured public/external signal is ready to hand categorically to Evidence Candidate Record.
  - Pressure-testing Data Capture obligations against real commissioned captures.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md
  - forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_context_preservation_note_v0.md
  - forseti/product/spines/foundation/product_contract/core_spine_v0_data_and_cleaning_spine_boundary_v0.md
  - forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md
  - forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md
stale_if:
  - Forseti authorizes standing/opportunistic corpus capture as part of Data Capture Spine.
  - Evidence Candidate Record architecture changes the handoff boundary.
  - A pressure-test revision supersedes these v0 obligations.
  - `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md` materially amends or supersedes the source-access boundary for Obligation 2.
  - `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md` materially changes method planning for the current source-access boundary.
```

- Status: CONTRACT_DRAFT_V0_AMENDED_2026_09_04
- Artifact type: Product-method contract
- Scope: Commissioned Data Capture Spine obligations, discharge states, mode rules, re-capture rules, and pressure-test checks
- Source basis: `docs/product/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md`, `docs/product/core_spine_v0_data_capture_context_preservation_note_v0.md`, `docs/product/core_spine_v0_data_and_cleaning_spine_boundary_v0.md`, `docs/product/data_capture_source_access_boundary_decision_v0.md`, `docs/product/data_capture_spine_obligation_contract_patch_proposal_v0.md`, `docs/decisions/data_capture_spine_obligation_contract_patch_proposal_owner_decision_v0.md`, `docs/product/data_capture_spine_posture_vocabulary_enforcement_proposal_v0.md`, `docs/review-outputs/adversarial-artifact-reviews/data_capture_spine_posture_vocabulary_enforcement_proposal_adversarial_review_v0.md`
- Implementation authorized: no
- Feature planning authorized: no
- Runtime/source-system design authorized: no

## Purpose

This contract defines what Data Capture Spine must satisfy for a
decision-framed public/external signal to be treated as captured well enough
for categorical handoff to Evidence Candidate Record.

It answers one question:

```text
Was this commissioned signal captured well enough that downstream layers can
inspect it, understand its limits, and proceed without recollecting source
history?
```

This is a product-method contract. It is not an Evidence Candidate Record
schema, Cleaning Spine design, Judgment Spine ruleset, source inventory,
runtime source-system plan, scraper/API plan, storage design, dashboard, test
plan, or implementation authorization.

## Scope

This contract applies only to **commissioned capture**.

Commissioned capture means the capture is performed for an existing Decision
Frame. The decision question, owner or owner-context, consequence, allowed
decision verbs, cutoff posture, and intended downstream use must be known
enough for capture obligations to be evaluated.

Standing or opportunistic corpus capture is out of scope for Data Capture
Spine v0. If Forseti later collects public signals before a Decision Frame exists,
that should be handled by a separate Candidate Signal Intake or Corpus Intake
contract (now the owner-ratified sibling
`forseti/product/spines/capture/core/contracts/corpus_intake/data_capture_spine_corpus_intake_obligation_contract_proposal_v0.md`,
owner-ratified 2026-06-15). Those items are not ECR-ready evidence until rebound
or recaptured under a Decision Frame.

## Contract Rule

Every commissioned capture must make each core obligation explicit as one of:

- `met`: the obligation is satisfied enough for categorical handoff.
- `partial`: the obligation is partly satisfied, and the limitation is visible.
- `assessed_not_met`: the obligation is required and attempted, and the
  available capture is sufficient to assess that the obligation was not
  satisfied. The failure reason must be visible.
- `cannot_assess`: the obligation is required and attempted, but the captured
  observable is not faithful, complete, or inspectable enough to assess whether
  the obligation was satisfied. The limitation and reason must be visible.
- `access_failed`: the source material appears within the allowed Forseti
  source-access boundary, and capture attempted access, but the capture method,
  tool, host, archive, or origin failed to return the needed observable. The
  failed path, fallback path if any, and visible limitation must be recorded.
- `blocked`: the obligation is required, but capture cannot satisfy it under
  the allowed Forseti boundary, project boundary, or hard-stop exclusion. It must
  not be used as the generic label for ordinary tool, host, origin,
  archive-content, or method failure against otherwise in-bound material.
- `unavailable_by_source`: the source does not expose the needed fact or state.
- `not_applicable`: the obligation does not apply to this signal or source.
- `not_attempted`: the obligation was not attempted and must carry a reason.

Silent omission is not allowed. Unknowns are acceptable only when the unknown
state and reason are visible.

## Core Obligations

### 1. Commissioning Gate

The capture must be tied to a Decision Frame.

Minimum obligation:

- the capture is connected to a specific decision question;
- the decision consequence or owner-context is known enough to keep capture
  from becoming free-floating source collection;
- the cutoff posture is known or explicitly marked unknown;
- standing or opportunistic capture is rejected or routed outside this contract.

Failure mode: if there is no Decision Frame, Data Capture Spine has not started.

### 2. Boundary Compliance

Capture must stay inside the current Forseti source-access boundary. The
controlling interpretation of that boundary for Obligation 2 is
`forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md`; if this
section and that boundary decision differ, the boundary decision controls until
amended or superseded.

The current boundary is discoverable-or-entitled source material plus
disclosable access method, with hard stops for explicitly illegal,
nonconsensual, exploit-style, obvious cross-account/private/admin spillover
once noticed, confidential, or otherwise too morally compromising access.

Free or account-created access is allowed. Entitled paid, client, or
consenting-coworker access is allowed. If access visibly spills into
cross-account, private, or admin material, Capture must not use that spillover
once noticed.

For community sources, an owner's existing entitled/logged-in membership may
be used within the permissions actually visible to that session, including
private Facebook groups, Discord servers, and other login-gated communities.
Capture must not obtain new credentials, create or borrow another identity,
join a community, bypass controls, or exceed those permissions for the
collection.

Capture must not use stolen credentials or cookies, nonconsensual sessions,
security exploits, malware, credential stuffing, no-entitlement payment/access
gate bypass, obvious cross-account/private/admin spillover once noticed,
private/confidential account areas without consent,
ordinary-person dossiers, or source acquisition that violates the current Forseti
boundary.

Failure mode: boundary-violating material is not a Data Capture blocker to be
worked around. It is out of bounds for this contract.

Access failure against otherwise in-bound source material is a capture
limitation, not a source-access boundary expansion. It should be discharged as
`access_failed`, not `blocked`, unless the failure is caused by the current
Forseti boundary, project boundary, or a hard-stop exclusion.

### 3. Capture-Event Provenance

Capture must make the capture event auditable at the product-method level.

Minimum obligation:

- who or what performed the capture is knowable at the operator/category level;
- the capture session is distinguishable from other sessions;
- the capture mode is disclosed;
- the obligation-contract version or equivalent rule surface is knowable;
- material mode changes inside the session are visible.

Why: downstream review must be able to audit capture-quality drift across
operators, agents, modes, and contract versions.

### 4. Capture Mode Disclosure

Capture must disclose how the signal was captured.

Allowed capture-mode categories:

- human-led;
- agent-assisted;
- structured access;
- archive/history;
- automated extraction;
- multimodal;
- mixed.

The mode category does not decide quality. It only exposes the capture path so
downstream layers can inspect limits and repeatability.

### 5. Mode-Change Rule

If a capture changes mode inside a session, the change must be visible.

Examples:

- human-led capture uses an agent to enumerate source candidates;
- agent-assisted capture escalates to human review for related-chain context;
- structured access fails and capture switches to archive/history;
- text capture escalates to multimodal capture because layout carries signal.

Mode changes do not invalidate capture. Hidden mode changes do.

### 6. Raw Observable Fidelity

Capture must preserve the raw observable enough for downstream inspection.
Capture should make visible which fidelity dimensions were preserved, limited,
not applicable, not attempted, access-failed, or unable to be assessed when
the Decision Frame caused Capture to seek those dimensions or those dimensions
were visibly encountered during capture.

Minimum obligation:

- fact or content-claim preservation: preserve what the source showed or said,
  not only Forseti's summary;
- source-language preservation: keep source language separate from Forseti
  interpretation and preserve domain-native wording when it carries signal;
- visible-structure preservation: preserve layout, headings, tables, nesting,
  ordering, grouping, proximity, emphasis, packaging cues, and other visible
  structure when those carry signal;
- public-reaction engagement preservation: for public-reaction surfaces,
  preserve source-visible upvotes, helpful votes, likes, views, shares, comment
  counts, reply counts, source-native score state, visible sort/rank/order,
  pinned/hearted/official-response markers, metric posture, and missingness
  when the source exposes them; these are context facts, not demand, credibility,
  independence, or action labels;
- modality preservation: preserve screenshots, images, gallery/media state,
  page chrome, audio, video, dynamic rendering, or interaction state when
  text-only capture would lose signal meaning;
- frame-keyed fidelity context: record which fidelity dimensions the Decision
  Frame caused Capture to seek, preserve, limit, fail to access, or be unable
  to assess.

Capture may add short context notes, but it must not replace the observable
with interpretation.

Capture reports fidelity state by dimension. Downstream Judgment decides which
dimensions are decision-material. This obligation does not create a universal
requirement to screenshot or media-capture every source regardless of Decision
Frame materiality.

Source-read ledgers, summaries, and title/date/claim rows are provenance aids.
They do not by themselves preserve the raw observable when source meaning
depends on thread context, modality, layout, edits, related replies, or visible
source structure.

### 7. Source Identity And Actor Context

Capture must preserve source identity and source-actor context where knowable.

Minimum obligation:

- identify the source surface or source family categorically;
- preserve actor or audience category where knowable;
- mark when actor specificity is unavailable, ambiguous, or source-limited;
- separate source carrier from source actor when they differ.

Capture records what is visible. It does not decide whether the actor is
credible, representative, independent, or decision-useful.

### 8. Decomposed Timing

Capture must preserve timing as separate visible categories where available.

Timing categories:

- source publication or event timing;
- source last-edit or version timing;
- capture timing;
- re-capture timing, if any;
- cutoff posture for the commissioned decision.

For live or mutable threaded pages, distinguish thread creation timing from
relevant comment, reply, update, edit, capture, and cutoff timing where visible.
If the related chain may include post-cutoff accretion or edits, mark the chain
as mixed or unknown unless item-level timing makes the boundary clear.

Do not collapse these into one generic timestamp. Divergence between them is
often the point.

### 9. Cutoff Posture

Capture must record cutoff posture as a first-class capture fact.

Minimum obligation:

- whether the signal appears pre-cutoff, post-cutoff, mixed, or unknown for the
  commissioned decision;
- whether the capture itself occurred before or after the cutoff;
- whether the capture includes any post-window material that downstream packet
  builders must exclude.

The cutoff posture is a closed capture fact: when its status is `known`, its
value is one of `pre_cutoff`, `post_cutoff`, `mixed`, or `unknown`, enforced at
write-time by the Source Capture packet schema. Capture-context narrative — why a
value was chosen, local-packetization limits, source notes — does not belong in
this field; record it in `capture_context`. When the posture cannot be stated as
one closed value, use the fact's `unknown_with_reason`, `not_attempted`, or
`not_applicable` status with a reason rather than a free-text value.

Capture does not decide whether the signal is admissible for a backtest or
decision. It makes cutoff posture visible enough for downstream exclusion and
Judgment rules to operate.

### 10. Archive / Historical Posture

Every capture must record archive/history posture. When a capture has only one
relevant source slice or the archive/history state is uniform, the posture may
be recorded at capture level.

The posture is a closed capture fact, enforced at write-time by the Source
Capture packet schema. When its status is `known`, its value is one of:

- `archived` — an archived or historical copy was obtained;
- `attempt_failed` — an archive/history copy was sought but not obtained.

`not_attempted` and `not_applicable` are carried by the fact's status with a
reason, not as posture values. The selected snapshot timestamp and the specific
non-preservation reason are recorded in the preserved archive metadata and in
packet limitations — not as free text in the posture value.

When cutoff, deletion, edit, cache, prior-window, archive-only, migration,
fallback, or visibility-shift risk is load-bearing, capture-level posture is
not enough if multiple states coexist. Capture must preserve archive/history
posture per relevant source slice, source locator, archive/cache attempt, or
fallback access path when those states differ.

Relevant source slices and locators include the original live locator,
historical or archive locator, cache locator, current locator, migrated
locator, mirror or fallback locator, and failed access attempt when any of
them changes visibility, cutoff posture, raw observable, source-state history,
or recapture relationship.

A rollup archive posture is allowed only when it does not hide a failed,
degraded, unavailable, not-attempted, fallback, migrated, or conflicting
source state. A successful archive or fallback does not erase a failed exact
access attempt, failed cache attempt, or non-attempted archive route.

Archive success is not required for every source. Visible archive posture is
required. Sufficiency belongs downstream.

When cutoff, deletion, edit, cache, or version risk is load-bearing, a missing
archive attempt should be treated as a visible limitation, not silently ignored.

### 11. Source Visibility And Access Limits

Capture must expose source visibility and access limits.

Minimum obligation:

- whether the source was publicly visible under the allowed Forseti boundary;
- whether visibility was gated, ephemeral, archive-only, deleted, edited,
  cached, dynamic, vendor-moderated, or otherwise constrained where visible;
- whether exact access failed, degraded, or required a fallback mode;
- for private or login-gated communities, the visibility class,
  entitlement/session provenance without secrets, actual permission scope, and
  any source-visible privacy, quotation, attribution, retention, or
  redistribution constraint material to downstream use;
- when source visibility shifts, preserve the relationship among the original
  locator, current locator, migrated locator, archive/cache locator, fallback
  locator, and failed access attempt where visible.

Capture does not convert visibility limits into credibility effects.

### 12. Related Context Preservation

Capture must preserve the smallest source context that keeps the signal
inspectable and fairly represented.

Two tests:

- ECR reconstruction floor: could Evidence Candidate Record reconstruct what
  the source was claiming from this slice without re-fetching?
- fairness ceiling: would a reasonable observer agree the slice represents
  what was said?

For threaded sources, preserve the related chain, not the entire forum. A
related-chain capture is not satisfied by a title/date/claim ledger row alone
when thread context carries meaning. Preserve the original post or parent claim,
the signal-bearing comment or reply path, direct corrections, rebuttals,
confirmations, official or moderator responses where visible, resolution, lock,
edit, or deletion posture where visible, and the boundary reason for excluding
unrelated thread branches or forum material.

For review surfaces, preserve rating, text, recency posture, visible
experience timing, moderation/incentive/sorting posture where available, and
long-context positive or negative detail when it carries signal. Helpful-vote
or reaction counts are preserved as source-visible engagement context when
available, not as review quality or demand labels.

For public-reaction sources such as comments, replies, reviews, or social/video
surfaces, preserve the relationship between the reaction metric and the evidence
unit it belongs to. A count without the comment/review it ranks is not enough;
a comment/review without its visible engagement context is a visible limitation
when that context was source-exposed and material to the Decision Frame.

For docs, changelogs, pricing pages, API docs, policies, and versioned pages,
preserve version, edit, deprecation, future/current, cache, archive, and
backfill posture where visible.

### 13. Bundled-Offer Structure Observables

When source material presents a counterparty offer, package, settlement,
public-sector deal, regulatory bargain, or similar multi-term proposal, Capture
must preserve the source-visible bundle structure instead of flattening it into
an unordered list of terms.

Minimum obligation:

- preserve which terms appear together in the same offer, package, draft, vote,
  memo, or negotiation artifact;
- preserve source-visible framing such as concession, requirement, restriction,
  safeguard, sweetener, penalty, condition, optionality, sunset, or fallback;
- preserve source-visible dependencies, including what must be accepted
  together, what appears severable, what is conditional, and what expires;
- preserve the source's own language for why a term is included when that
  language is visible;
- preserve visible packaging cues where they carry meaning, including headings,
  labels, bullet order, nesting, emphasis, table placement, grouping, and
  proximity;
- preserve sequence where visible: when a term entered, changed, moved, or
  disappeared across drafts, votes, memos, or negotiations.

The atomic unit is the bundle as presented, not the extracted term. A term may
still be captured separately for downstream inspection, but separate term
capture must not erase the source-visible package it came from.

Capture records observed structure and framing. It must not infer counterparty
motive, price concessions, recommend negotiation moves, or decide whether the
bundle is good, bad, credible, acceptable, or decision-useful.

### 14. Capture Failure And Blocker Visibility

Capture must make failure visible.

Examples:

- source inaccessible under allowed boundary;
- source disappeared or changed;
- archive attempt failed;
- exact source access failed but an archive, cache, mirror, migrated page, or
  other fallback succeeded;
- source actor could not be identified;
- publication timing could not be established;
- source context could not be fairly bounded;
- bundle membership, source-visible framing, or term dependency could not be
  established for a multi-term proposal;
- visible packaging cues could not be preserved where they carry meaning;
- modality could not be captured enough to preserve meaning.

Failure is allowed. Silent failure is not.

### 15. Re-Capture Semantics

Re-capture is required or should be considered when source state, archive
state, Decision Frame, cutoff posture, or capture-mode confidence materially
changes.

A re-capture must preserve its relationship to the earlier capture:

- why re-capture happened;
- what source state changed, if known;
- whether the new capture supersedes, supplements, or conflicts with the prior
  capture;
- whether cutoff posture changed or became clearer.

The re-capture relationship is a closed capture fact: when its status is
`known`, its value is one of `supersede`, `supplement`, `conflict`, or `mixed`,
enforced at write-time by the Source Capture packet schema. `mixed` is the value
for a capture that supersedes the prior one for current-state posture while
supplementing or conflicting with it for a prior-window or cutoff question; use
it instead of forcing one global label.

When re-capture involves changed, migrated, archived, cached, fallback, or
failed-access source states, that relationship must be preserved per material
source slice or locator. The relationship must distinguish the original
locator, archive or historical locator, current or migrated locator, failed
access attempt, and changed source state where those are visible.

A later capture may supersede the earlier capture for current-state posture
while supplementing or conflicting with it for a prior-window or cutoff
question. Capture must preserve that mixed relationship instead of forcing one
global supersede, supplement, or conflict label. Later successful access does
not overwrite earlier failed access, archive attempt failure, fallback use, or
prior-window uncertainty.

Re-capture does not erase prior capture history.

### 16. Categorical Handoff Readiness

Capture must make enough categorical context available for ECR, Cleaning, and
Judgment to proceed without recollecting source history.

This obligation assesses Capture-owned handoff readiness. It does not require
that ECR has already receipted the material, and it does not define ECR fields,
keys, IDs, tables, data types, receipt structures, storage, schema, or file
formats.

Minimum handoff accomplishments:

- the captured signal is inspectable;
- raw observable and related context are preserved, or their limitations are
  visible;
- source claim is separate from Forseti interpretation;
- source identity, actor category, timing, modality, visibility, and
  cutoff/archive posture are visible where knowable;
- when archive/history or recapture states differ, the original locator,
  historical/archive/cache locator, current or migrated locator, fallback path,
  failed access attempt, changed source state, and supersede/supplement/conflict/mixed
  relationship remain visible at the relevant source-slice level;
- bundled-offer structure, source-visible framing, and visible packaging cues
  are preserved when the source is a multi-term proposal;
- capture obligations and limitations are visible;
- Cleaning can proceed without reconstructing collection history;
- Judgment can inspect capture limits without Capture making judgment calls.

Capture-owned handoff readiness is readiness of the captured target or batch,
not acquisition closure. A Capture-authored summary may report that its bounded
targets are captured and ready for allowed downstream preparation, including
the lightweight provisional maturity scan, but it must not assert
`COLLECTION_COMPLETE_READY_FOR_CONSOLIDATION`, `SEALED_READY_FOR_DELIVER`,
material saturation, or an equivalent terminal state. Those claims belong to
the current Commission Signal Board phase acquisition seal and its validator.
A completed URL list, capture job set, agent allocation, or source-access
allowance cannot substitute for that seal. Any downstream consumer presented
with such a Capture-only terminal claim must treat it as a non-terminal batch
handoff and keep acquisition open.

### 17. Demand-Durability Series Facts (Conditional)

This obligation applies ONLY to a commissioned demand-durability proxy series
(price, availability, search-interest, review) that observes a source repeatedly
over time, per `capture_envelope_durability_delta_spec_v0.md`. It does not apply
to one-shot captures, which leave these facts unset.

For such a series, Capture must record:

- the comparability pins held across the series — `session_visibility_pin`,
  `locale_pin`, `currency_pin`, `variant_pin` (Element 1), per observed slice. A
  pin the source does not expose is `unknown_with_reason` / `not_applicable`, and
  its capture obligation is discharged `unavailable_by_source` — never written as
  a fact status.
- the series origin — `series_id`, `cold_start_at`, `pre_coverage_history_posture`
  (Element 2), marking that history before the first observation is uncovered by
  construction.
- the declared sampling cadence — `intended_cadence` (Element 4), with realized
  timings available via per-observation `capture_time` / `recapture_time` and gaps
  recorded as visible limitations (an un-sampled gap is never "no change").

These are observed facts that fix comparability and coverage extent; they can
support or falsify a later durability projection, but they are never weights,
scores, or a durable / transient / manufactured demand verdict (INV-1). The
series-level recapture-diff (Element 3) is a separate cross-observation record and
is **deferred** — not named here; when built it keys change on the EXTRACTED
demand-relevant values, with the raw `PreservedFile.sha256` only a coarse
inspect-flag (data-capture distillation binding, A1c). All Element 1/2/4 fields
are **additive and optional**: existing manifests stay valid with them unset (no
`SOURCE_CAPTURE_MANIFEST_VERSION` bump).

## Capture Modes

### Human-Led

Human-led capture is allowed and expected for v0 bootstrap, training,
governance, quality control, and high-ambiguity capture.

Human-led capture still must disclose capture-event provenance, timing, mode,
context, cutoff, archive posture, and limitations. "A human looked at it" is
not a substitute for obligation discharge.

### Agent-Assisted

Agents may:

- enumerate;
- fetch;
- archive;
- transcribe;
- link;
- mechanically group exact URLs or identical locators.

Agents must not:

- rank relevance;
- filter candidates before presentation;
- summarize for admissibility;
- decide missing context;
- classify credibility;
- exclude signals;
- decide downstream use.

Agent-assisted sessions should preserve query/session context, result batches,
fetched candidates, discarded candidates, and discard reason categories.

### Structured Access

Structured access may be used when official, clean, or orderly source surfaces
exist.

Structured access must not define what counts as evidence. It is one capture
path. Availability does not equal validity.

### Archive / Historical

Archive/history capture is required as a conceptual posture and used when
cutoff, deletion, edit, cache, version, or prior-window visibility matters.

Runtime archive tooling is not authorized by this contract.

### Automated Extraction

Automated extraction is allowed only as a future bounded mode after obligations
are testable and the current turn or accepted handoff authorizes runtime work.

Until then, automated extraction is a conceptual mode, not a build plan.

### Multimodal

Multimodal capture is required when text alone loses the signal.

Examples include layout-dependent pages, screenshots where visual state carries
meaning, audio/video statements, dynamic rendering, and interaction-dependent
signals.

## Captured But Unusable

A signal can satisfy Data Capture obligations and still be unusable downstream.

Capture success does not imply:

- credibility;
- independence;
- audience fit;
- costly behavior;
- demand evidence;
- valid signal use;
- inclusion;
- Decision Strength;
- Action Ceiling.

If Capture discharged obligations and exposed limits, downstream unusability is
not a Data Capture failure. It is a downstream judgment, receipt, cleaning, or
decision-use result.

## Forbidden Outputs From Capture

Data Capture must not emit:

- credibility labels;
- integrity classifications;
- discounting decisions;
- exclusion decisions;
- Signal Use Classification;
- Decision Strength;
- Action Ceiling;
- semantic dedupe or clustering effects;
- Cleaning transformations;
- final ECR field architecture;
- source-quality scores;
- source maps as core architecture;
- runtime implementation plans.

Capture may record visible facts that downstream layers later use. It must not
decide downstream effects.

## Checker Vocabulary And Comparability

Checker vocabulary, when used in pressure-test or review artifacts, must carry
explicit glosses:

- `capture_closure_blocker`: a checker-visible reason the capture artifact
  should not be treated as cleanly closed under the current contract posture.
  It is not the discharge state `blocked`, not validation failure, and not a
  mandatory rerun command by itself.
- `visible_capture_limitation`: a checker-visible limitation that must remain
  visible to downstream layers. It is not proof that capture is adequate.
- `vocabulary_divergence`: a checker-visible mismatch between contract
  vocabulary and artifact language that is not clearly labeled as a proposal.
- `vocabulary_consistent`: checker-visible contract vocabulary appears
  consistent for the checked surface. It is not capture adequacy, validation,
  readiness, approval, source adequacy, or proof.

During pressure-test patching, a second vocabulary-consistency check may be
used to distinguish unlabeled vocabulary drift from clearly labeled proposal
language. The check may expose contract-language pressure. It must not certify
capture quality, source adequacy, validation, readiness, approval, or handoff
sufficiency.

Pressure-test or checker-bearing artifacts must disclose checker posture
categorically when the posture is compared, synthesized, or used to explain a
review result: separate checker invocation, artifact-internal self-check, or
missing checker pass. Checker posture supports comparability only. It must not
become a quality rank, validation rule, approval rule, readiness rule,
model-agreement rule, or proof of source adequacy.

## Source-Family Promotion

Source-family heuristics begin as satellite rules unless they are obvious core
invariants or are explicitly accepted by the owner as core.

Promotion to core requires one of:

- comparison across at least two non-overlapping source families; or
- owner sign-off for one specific invariant claim.

Owner override must attach to the specific invariant claim, not a broad
category such as "forums" or "review surfaces."

## Pressure-Test Requirement

This v0 contract should not be treated as hardened until tested against 3-5
real commissioned captures.

Pressure-test each capture against:

- whether the Decision Frame was sufficient to start capture;
- which obligations were `met`, `partial`, `assessed_not_met`,
  `cannot_assess`, `access_failed`, `blocked`, `unavailable_by_source`,
  `not_applicable`, or `not_attempted`;
- whether related context was too thin, too broad, or fair;
- whether cutoff and archive posture were clear enough;
- whether agent/human mode boundaries held;
- whether Capture stayed out of ECR, Cleaning, and Judgment;
- whether checker vocabulary, if used, was glossed and kept separate from
  validation, readiness, approval, source adequacy, and proof;
- whether checker posture, if compared or synthesized, was disclosed
  categorically and treated as comparability only;
- whether the signal was captured but later unusable, and why that was not a
  Capture failure;
- which obligation should be tightened, relaxed, split, or moved to satellite.

Recommended pressure-test source mix:

- one threaded forum or community chain;
- one review surface with recency and long-context tension;
- one bundled or multi-term offer, settlement, public-sector deal, regulatory
  bargain, or counterparty package with source-visible framing;
- one changelog, docs, pricing, API, or policy page with version/timing risk;
- one archive/history case with deleted, edited, cached, or prior-window risk;
- one multimodal or dynamic-page case if available.

Before locking or tightening core obligations, review accumulated tactical
primitives from cases for upstream capture requirements they imply. If a
downstream primitive cannot be recovered after capture flattening, that is
capture-obligation evidence, not only Judgment training material.

The pressure test should update the contract only after failures are compared.
Do not harden this contract from abstract reasoning alone.

## Open Design Knobs

Carry these forward explicitly:

- which source families require an archive attempt rather than recorded
  per-slice archive/history posture only;
- which source families require human-led capture by default until the engine
  is trained and checked;
- what minimum agent-assisted logging is feasible without creating source-log
  bloat;
- where ECR draws the line between related-chain context and irrelevant source
  exhaust;
- whether Snapshot Integrity Class belongs in Data Capture, ECR, or later
  Judgment/ECR consolidation;
- what recapture threshold is high enough to avoid churn but low enough to
  preserve meaningful source changes.

## Rejected Patterns

Reject:

- standing/opportunistic corpus capture inside this v0 contract;
- generic "hybrid" mode mixing without obligation discharge;
- checker vocabulary as obligation discharge;
- checker output, checker agreement, or checker posture as validation,
  readiness, approval, source adequacy, proof, or model authority;
- source volume as evidence validity;
- source maps or inventories as Data Capture core;
- capture-time credibility scoring;
- ECR-by-stealth;
- Cleaning-by-stealth;
- Judgment-by-stealth;
- paper contract hardening before real signal pressure tests;
- capture as adversarial defense rather than downstream judgment enablement;
- runtime design as this contract.

## Non-Claims

This contract does not prove buyer validation, willingness to pay, repeatable
demand, product readiness, feature readiness, implementation readiness,
commercial readiness, source-system feasibility, data rights, runtime
feasibility, Core Spine validation, Judgment Spine validation, Evidence
Candidate Record completion, or Evidence Unit (EvidenceUnit) design completion.

It does not authorize implementation, runtime design, source maps, schemas,
scrapers, APIs, storage, dashboards, automation, tests, deployment, proof runs,
feature planning, commits, pushes, PRs, or readiness claims.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: "The Data Capture obligation contract now operationalizes the accepted PCP-01 through PCP-08 package: expanded discharge vocabulary, narrowed blocked/access_failed distinction, raw-observable fidelity dimensions, Capture-owned handoff readiness, and checker vocabulary/comparability limits."
  trigger: product_doctrine
  trigger_chain_note: "Earlier proposal and owner-gate artifacts used lifecycle_boundary because they sequenced authority for a later amendment; this operative contract amendment uses product_doctrine because it changes the durable Data Capture obligation contract."
  controlling_sources_updated:
    - docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/orca_repo_map_v0.md
    - docs/product/data_capture_source_access_boundary_decision_v0.md
    - docs/product/data_capture_source_access_method_plan_v0.md
    - docs/product/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md
    - docs/product/core_spine_v0_data_capture_context_preservation_note_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - CLAUDE.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/orca_repo_map_v0.md
    - docs/product/data_capture_spine_obligation_contract_patch_proposal_v0.md
    - docs/decisions/data_capture_spine_obligation_contract_patch_proposal_owner_decision_v0.md
    - docs/product/data_capture_source_access_boundary_decision_v0.md
    - docs/product/data_capture_source_access_method_plan_v0.md
    - docs/product/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md
    - docs/product/core_spine_v0_data_capture_context_preservation_note_v0.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: "Top-level Orca project instructions already permit bounded docs/decision work and require separate explicit authorization for implementation/runtime work."
    - path: CLAUDE.md
      reason: "Claude shim remains subordinate to AGENTS.md and the Orca overlay; no Claude-specific instruction changed."
    - path: .agents/workflow-overlay/source-of-truth.md
      reason: "Source hierarchy and propagation mechanics did not change; this amendment applies the existing propagation contract."
    - path: docs/product/data_capture_spine_obligation_contract_patch_proposal_v0.md
      reason: "The proposal remains historical candidate-language input; the controlling contract now consumes the accepted package."
    - path: docs/decisions/data_capture_spine_obligation_contract_patch_proposal_owner_decision_v0.md
      reason: "The owner decision remains the amendment authority and is now consumed by this contract amendment."
  stale_language_search: "rg -n \"which obligations were met, partial, blocked, unavailable|Categorical Handoff Sufficiency|Raw Observable Preservation|blocked, unavailable, not applicable|public, market-level, non-deceptive boundary compliance|public, market-level, and non-deceptive|Public data only:|LOOSEN_SOURCE_ACCESS_TO_PUBLIC_DATA_DISCLOSABLE|later bounded Data Capture obligation-contract amendment drafting|later docs-only obligation-contract amendment drafting|still does not amend the controlling contract|Draft Data Capture Spine v0 obligation contract for setup and pressure testing|checker output as validation|checker agreement as validation|validation-ready|ready for implementation|ECR schema now authorized|Cleaning implementation now authorized|Judgment rules now authorized|runtime/source-system implementation now authorized\" docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md docs/product/core_spine_v0_data_capture_spine_architecture_blueprint_v0.md docs/product/core_spine_v0_data_capture_context_preservation_note_v0.md docs/product/data_capture_source_access_method_plan_v0.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source-access method-plan amendment"
    - "not ECR design"
    - "not Cleaning implementation"
    - "not Judgment design"
    - "not runtime authorization"
```

The receipt below records the DCS-POSTURE-VOCAB-R2 posture-vocabulary closure
amendment (2026-06-05: §9/§10/§15 stated closed and write-time-enforced to match
the landed Source Capture schema enforcement). It is propagation evidence only and
explicitly does **not** claim the change is settled — that requires the owner-run
cross-family implementation+doctrine review named in its non_claims.

```yaml
direction_change_propagation:
  doctrine_changed: "Ob.9 cutoff, Ob.10 archive/history, and Ob.15 re-capture posture vocabularies are now stated as closed and write-time-enforced (known value ∈ the named closed set; not_attempted/not_applicable carried by VisibleFact status), matching the Source Capture schema enforcement landed for DCS-POSTURE-VOCAB-R2."
  trigger: product_doctrine
  related_triggers: []
  controlling_sources_updated:
    - docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md
  downstream_surfaces_checked:
    - orca-harness/source_capture/models.py
    - orca-harness/source_capture/writer.py
    - orca-harness/source_capture/source_quality.py
    - orca-harness/runners/run_source_capture_archive_packet.py
    - orca-harness/docs/source_capture_packet.md
    - orca-harness/docs/source_capture_agent_runbook.md
    - orca-harness/docs/adapter_author_contract.md
    - docs/product/data_capture_spine_posture_vocabulary_enforcement_proposal_v0.md
    - docs/review-outputs/adversarial-artifact-reviews/data_capture_spine_posture_vocabulary_enforcement_proposal_adversarial_review_v0.md
  intentionally_not_updated:
    - path: orca-harness/source_capture/models.py
      reason: "Already IS the enforcement this amendment describes; the closed sets and validators landed under bounded implementation. The contract now states what the schema does — no code change is part of the doctrine amendment."
    - path: orca-harness/docs/source_capture_packet.md
      reason: "Describes archive availability/body OUTCOMES in behavioral prose (metadata-only / metadata+body / body-failed packet), not the posture field VALUE; the outcomes are unchanged, so there is no off-vocab value to correct."
    - path: orca-harness/docs/source_capture_agent_runbook.md
      reason: "References cutoff_posture as operator-set context and the separate coverage_or_drift_note field; carries no off-vocab posture value contradicting the closed sets."
    - path: orca-harness/docs/adapter_author_contract.md
      reason: "References the posture axes by name in terms of STATUS (unknown_with_reason/not_attempted/not_applicable) per the AR-05 split, not off-vocab values; hash_basis is writer-set, outside adapter-author scope."
    - path: docs/product/jsg01_source_side_receipt_translator_v0.md
      reason: "JSG-01 source-side consumer is FROZEN per AR-01 and is ECR/JSG-lane-owned. Coordination is by re-courier if a build stop-condition changes the contract, not by editing the consumer from this lane. (Applies to the jsg01_sp6_* derivation docs as well.)"
    - path: docs/review-outputs/source_capture_archive_org_adapter_adversarial_code_review_v0.md
      reason: "Point-in-time review record documenting the pre-migration free-text posture values as they existed then; editing it would falsify the historical record. (Applies to the other review-outputs that quote old posture strings.)"
    - path: forseti/product/spines/capture/core/source_capture_toolbox/source_quality_cw_p1_end_to_end_pass_closeout_v0.md
      reason: "Point-in-time end-to-end pass closeout recording the posture values that specific packet carried at that pass; historical record, not a live contract surface. (Applies to the sibling cw_p4 / cw_p6 closeouts.)"
  stale_language_search: "rg -n \"cutoff_posture|archive_history_posture|re_capture_relationship|hash_basis\" + rg -n \"snapshot body preserved|no eligible snapshot|availability metadata preserved|archive_org snapshot body\" over docs/ orca-harness/docs/. Triage: live harness docs (packet/runbook/adapter-contract) describe behavior or STATUS, not off-vocab values; review-outputs and source_quality_cw_p* closeouts are historical point-in-time records; jsg01_* is frozen consumer. No live contract surface carries an off-vocab posture value after this amendment."
  non_claims:
    - "not validation"
    - "not readiness"
    - "not settled — settled requires the owner-run cross-family review at docs/prompts/reviews/data_capture_spine_posture_vocabulary_enforcement_implementation_adversarial_review_prompt_v0.md; a same-family self-review does not satisfy that bar"
    - "not a commit/push authorization"
    - "not JSG-01 unfreeze"
    - "not ECR/Cleaning/Judgment design"
    - "not runtime authorization"
```

### R2 closure note (2026-06-05)

The owner-run cross-family implementation+doctrine review ran
(`docs/review-outputs/adversarial-artifact-reviews/data_capture_spine_posture_vocabulary_enforcement_implementation_adversarial_review_v0.md`,
SHA256 `F6C669B0A4C04E7AC01EC1BA4BA33E62AC2FEAEF53065A9210BD0162367BDB9C`),
recommendation `patch_before_acceptance`. The code-side remediations (AR-03/04/05 for new
writes) held; both blockers were **pre-R2 on-disk packets**, not the code: R2-01 (existing
manifests lack the now-required `hash_basis`) and R2-02 (existing manifests carry
off-vocabulary `known` `cutoff_posture` narratives) — both in the three
`orca-harness/reports/source_capture/slot3_reddit_batch1_*` dry-run packets, which are
hash-pinned review evidence and the off-vocab examples this proposal itself cites.

Owner resolution (the review sanctioned "closed OR scoped out by owner decision"):
- **Scope-out:** the three pre-R2 packets are frozen `v0` review evidence, read-exempt from
  the R2 schema, left byte-for-byte untouched (prior reviews' hash-pins and the cited
  off-vocab "before" evidence stay intact). Mutating or deleting them was rejected as
  destroying review-evidence integrity.
- **Honest versioning:** R2 is a backward-incompatible packet-schema change, so
  `SOURCE_CAPTURE_MANIFEST_VERSION` is bumped `source_capture_packet_manifest_v0` → `_v1`.
  New writes carry `v1`; old packets remain `v0`. The scope-out is therefore
  version-grounded: a `v0` packet is not required to satisfy the `v1` schema.

Status: R2-01/R2-02 are resolved on the scope-out path; R2 code + doctrine is settled to the
`v1` manifest schema (new-write correctness verified: `v1` + `hash_basis=raw_stored_bytes` +
closed `cutoff_posture`; full suite green). This supersedes the "not settled, pending review"
non_claim above.

The broader packet schema-evolution structure (where strict validation belongs — every-read
vs admission/consume gate vs version-aware read-back; upgrade-on-load vs clear-reject design;
the build trigger) is NOT part of this R2 closure. It is routed to a standard architectural
pass (`docs/prompts/architecture/source_capture_packet_schema_evolution_architecture_prompt_v0.md`),
3 subagents, owner-run.

```yaml
# Demand-durability conditional obligation (Ob.17) + additive-optional schema fields. 2026-06-15.
direction_change_propagation:
  doctrine_changed: "The Data Capture obligation contract now names Demand-Durability Series Facts as Ob.17 — a CONDITIONAL obligation for commissioned demand-durability proxy series (Element 1 pins, Element 2 cold-start/series_id, Element 4 cadence) — matched by additive-optional fields on SourceCaptureSlice (4 pins) and SourceCapturePacket (series_id, cold_start_at, pre_coverage_history_posture, intended_cadence) in models.py. Backward-compatible: existing manifests stay valid with the fields unset; no SOURCE_CAPTURE_MANIFEST_VERSION bump (unlike the R2 backward-incompatible change). Series-diff (Element 3) deferred."
  trigger: product_doctrine
  controlling_sources_updated:
    - forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md
    - orca-harness/source_capture/models.py
  downstream_surfaces_checked:
    - forseti/product/spines/capture/core/demand_durability_indicators/capture_envelope_durability_delta_spec_v0.md
    - forseti/product/spines/capture/core/demand_durability_indicators/price_timeseries/demand_durability_indicator_price_timeseries_capture_profile_v0.md
    - forseti/product/spines/capture/core/demand_durability_indicators/availability_restock/demand_durability_indicator_availability_restock_capture_profile_v0.md
    - docs/decisions/distillation_binding_data_capture_v0.md
    - orca-harness/source_capture/writer.py
    - orca-harness/runners/run_source_capture_http_packet.py
  intentionally_not_updated:
    - path: orca-harness/source_capture/writer.py
      reason: "Additive-optional fields default to None; writer/runners construct valid packets without setting them. A demand-durability series writer populates them — that integration is the real-series step, not this schema/contract hardening."
    - path: SOURCE_CAPTURE_MANIFEST_VERSION (orca-harness/source_capture/models.py)
      reason: "Additive-optional + backward-compatible (unlike R2); existing v1 manifests validate unchanged, so no version bump. Mirrors the archive_snapshot_time additive precedent."
    - path: forseti/product/spines/capture/core/demand_durability_indicators/capture_envelope_durability_delta_spec_v0.md
      reason: "Already DESCRIBES Elements 1-5 as capture facts; Ob.17 hardens Elements 1/2/4 into a conditional obligation + schema fields per its own owner-gated 'contract hardening' note. The Element-3 series-diff spec-text sharpen (extracted-values anchor) folds into the deferred Element-3 hardening, not here."
  non_claims:
    - "not validation"
    - "not readiness"
    - "not a real over-time series (the pilot was a single window)"
    - "not series-diff (Element 3) hardening — deferred (cross-packet record + extracted-value extractor)"
    - "not a demand verdict (INV-1 preserved)"
    - "not ECR/Cleaning/Judgment design"
    - "not runtime/scheduler authorization"
    - "schema verified by the offline suite (861 passed, 2 skipped); broader doctrine-settledness not claimed beyond that"
```
