# Review Lanes

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Forseti review lanes, reviewer permissions, and executor boundaries.
use_when:
  - Selecting or checking a Forseti review lane.
  - Confirming whether a reviewer may write reports or apply patches.
  - Resolving review prompt template retrieval without turning templates into model routing.
authority_boundary: retrieval_only
```

**Routine read shape** (owned by `.agents/workflow-overlay/source-loading.md`,
Targeted Read Protocol): routine review work reads "Current Lanes" plus the
one section the task touches ("Review Doctrine" for formal lane bindings,
"Template Retrieval Binding" when retrieving a template, "Rules" for reviewer
conduct); a full-file read is for editing lane doctrine or adjudicating a
lane-authority conflict.

## Current Lanes

- Artifact review: read-only review of docs, decisions, prompts, and migration artifacts. Reviewers may write reports only under `docs/review-outputs/` unless a prompt authorizes a different Forseti-owned report path.
- Adversarial artifact review: read-only adversarial review of docs, decisions,
  prompts, product-proof artifacts, and migration artifacts. Reports should go
  under `docs/review-outputs/adversarial-artifact-reviews/` unless a prompt
  names another Forseti-owned report path. Formal adversarial artifact review must
  invoke `workflow-adversarial-artifact-review` after source context is ready.
  If that skill is unavailable, unresolved, or not applied, the run may return
  only a blocked or advisory-only result and must not emit strict review
  claims.
- Prompt review: read-only review of prompt artifacts, thin wrappers, source maps, output modes, and validation gates. Reports go under `docs/review-outputs/` unless the prompt names another Forseti-owned report path.
- Patch-queue review: read-only review that produces ordered patch units. Applying those patches requires a separate patch or integration execution assignment.
- Patch or integration execution: applies accepted documentation patches inside Forseti and reports changed files plus validation.
- Skill adoption review: deferred until a later turn authorizes adoption or shadow validation.
- Delegated review-and-patch (bound, opt-in commission): a distinct Chief Architect-commissioned bounded-executor lane for hardening high-stakes authored artifacts — and, in its `delegated_code_review_and_patch` mode, bounded multi-file implementation/code diffs reviewed via the code review lane (`workflow-code-review`) — defined in `.agents/workflow-overlay/delegated-review-patch.md`. Every commissioning entry, including an automatic skill or workflow checkpoint, returns one owner-courier prompt only; the commissioning agent does not discover or dispatch a controller or execute the review. It is NOT one of the source-read-only review lanes and NOT machine-routable; direct repository access is required, and `no_repo` routes outside this convention to an ordinary read-only review. The reviewer-read-only rule and the review-lane model-neutrality below are unchanged.

## Review Doctrine

Forseti review mechanics are Forseti-owned here: findings-first review output,
advisory critique from visible evidence, and strict authority boundaries for
formal review claims. Forseti-local overlay files own concrete lane names,
destinations, result vocabulary, severity labels, validation gates, patch
routing, and Chief Architect consumption rules.

- Review target and review purpose are commission-bound. A reviewer must not
  silently retarget a review, widen the target, or treat an adjacent artifact as
  the actual review object unless the prompt or current user instruction binds
  that change.
- Within the commission-bound target and purpose, adversarial reviewers should
  be maximally adversarial and coverage-first: report every failure mode found,
  including uncertain and low-severity ones. Materiality, severity, and
  confidence are labels the reviewer attaches to a finding, never a threshold
  for reporting it; filtering for importance belongs to the downstream
  adjudication, not the find stage. This does not widen the target; it means
  the reviewer must not soften, skip, or silently drop a failure mode because
  remediation would be awkward, confidence is low, or the finding seems minor.
- For intent-bearing review targets -- artifacts whose correctness is judged by
  fitness to an upstream goal (proofs, fixtures, calibration gates, plans,
  operating structures, runbooks, product-proof artifacts) rather than by
  internal or technical consistency alone -- the decision criteria the review
  applies should be anchored to a bound `fitness_reference`: a stated goal plus
  an observable success signal, pointer-preferred (cite the controlling upstream
  contract, decision, or gate that already carries the signal; write compact
  prose only when none exists). The fitness reference is an added alignment axis
  the reviewer must also attack -- the reviewer asks whether the goal and signal
  are themselves right -- never a pass-if-matches bar. It does not narrow the
  commission-bound adversarial posture and creates no approval, validation, or
  readiness.
- If an intent-bearing target arrives with no bound fitness reference, the
  review names the gap (`no checkable success bar bound`) as a finding rather
  than silently inventing the goal. This is review-side back-pressure, not new
  verdict authority, and it stays findings-first.
- The fitness-reference rule applies to adversarial artifact review. Code or
  implementation review is not extended here; its fitness bar (spec, tests,
  ground-truth substrate) is governed separately. The authoring home for the
  goal and success signal is framing/scoping (reuse `workflow-goal-framing`
  output); this doctrine routes that output and does not relocate or fork it.
  Owning decision: `docs/decisions/work_unit_fitness_reference_v0.md`.
- Review lanes emit findings by default. Formal verdicts, severity taxonomies,
  blocked/ready status, validation pass/fail claims, approval, readiness,
  mandatory remediation, and executor-ready patch queues are strict-shaped
  outputs and require Forseti overlay or prompt binding.
- Forseti adversarial artifact reviews may use `critical`, `major`, and `minor`
  severity labels for finding priority when the prompt or template names those
  labels. Those labels do not by themselves create approval, rejection,
  readiness, validation, or mandatory remediation authority.
- Findings carry a `confidence` label (`high` / `medium` / `low`) alongside
  severity: the reviewer's own certainty that the finding is real. Like
  severity, it is a priority label only and creates no approval, rejection,
  readiness, or remediation authority. Low confidence is never a reason to
  omit a finding; low-confidence or minor findings may use a compact one-line
  form instead of the full finding shape.
- A candidate finding the reviewer defeats with a steelman defense is not
  silently discarded: it is listed one line each in a `considered_and_defended`
  section (candidate plus the defense that held). These entries are not
  findings and carry no severity, closure, or action fields; they exist so the
  adjudicator can see the discard pile instead of inheriting the reviewer's
  self-filter.
- Actionable review findings should state the `minimum_closure_condition`:
  what must become true before the failure mode can be treated as resolved. The
  closure condition states the required end state, not how to implement it.
- Actionable review findings should state the `next_authorized_action`: what
  the current review authority allows next, such as owner decision, rerun,
  patch authorization request, or no action.
- Optional hardening may be identified only when clearly labeled optional and
  non-required. Optional hardening is not a blocker, mandatory remediation,
  patch authority, or readiness condition.
- `patch_queue_entry` means executor-ready how-to. It is allowed only in a
  patch-queue review or separately authorized patch/integration execution lane.
  Ordinary read-only artifact, adversarial artifact, prompt, and implementation
  reviews must not emit `patch_queue_entry`; they may provide advisory
  remediation direction only.
- Chief Architect consumption of review reports follows this order:
  commission -> target -> authority -> decision criteria -> evidence ->
  reviewer verdict or recommendation. Reviewer verdicts and recommendations
  are decision input, not the first anchor.
- No synthesis lane is added by this doctrine. Multi-review reconciliation
  remains Chief Architect adjudication unless a later Forseti overlay decision
  explicitly binds another owner.
- Review lane routing must never recommend, prescribe, rank, or imply runtime
  model choice. Review lanes may bind review type, method/skill, target,
  authority, output mode, destination, and prompt-template target. Runtime
  model choice is outside Forseti review-lane authority and remains an
  operator/tooling decision.
- Review outputs record two provenance fields, operator/tooling-supplied and
  set by the operator/CA on the durable review record (including when ingesting
  a no-repo or portable reviewer's returned findings -- the reviewer is not
  required to self-emit them): `reviewed_by` (the model and version that
  performed the review) and `authored_by` (the model and version that authored
  the artifact under review), for example `claude-opus-4.8`, `gpt-5.5`. Each is
  a required (present) field on new or materially touched review outputs (not
  backfilled); its value is `unrecorded` when the identity was not supplied, and
  it is never fabricated. These are factual provenance records -- the
  ordinary-review analogue of the delegated-review-patch actor/model-family
  receipt -- and must never be used to select, recommend, rank, or imply a
  runtime model; the model-neutrality rule above is unchanged.
- The purpose of `reviewed_by` / `authored_by` is to make reviewer attribution
  and same-family-vs-cross-family coverage measurable. Same-vs-cross is computed
  by relating the two families, so it is measured only when both fields carry
  real values: a present `unrecorded` value satisfies the schema but records a
  visible measurement gap, not a captured measurement, and is never treated as
  success. The measurement is realized only when tooling actually populates the
  real values.
- **Two-bar de-correlation (review tier; family = vendor).** A **cross-vendor**
  delegate (different vendor / model lineage, e.g., Claude <-> GPT; vendor =
  upstream developer/provider, not host / reseller / wrapper) is the **discovery**
  bar, required to claim the no-new-seam standard for a full or doctrine-surface
  pass. A **same-vendor** delegate (typically a lower/mechanical tier, e.g.,
  Opus -> Sonnet) is the **bounded sanity / verification** tier: it **may only
  claim bounded verification/sanity, never discovery / no-new-seam** -- appropriate
  for a bounded authored change or a post-patch recheck, run **advisory** (findings
  adjudicated by the CA). Tier is not family; the de-correlation definition is
  owned by `.agents/workflow-overlay/delegated-review-patch.md`. **When the
  same-vendor bar is chosen, the review record must record `de_correlation_bar`**
  (`cross_vendor_discovery` | `same_vendor_sanity` | `self_fallback`) **plus, for
  `same_vendor_sanity`, a `same_vendor_rationale`** (why the cross-vendor bar was
  not needed: e.g., bounded change; no doctrine/seam surface; no no-new-seam
  claim) -- recorded alongside `reviewed_by` / `authored_by` so a missing
  justification is mechanically detectable.
  This general same-vendor sanity tier does not satisfy an explicitly
  commissioned delegated review-and-patch lane. That narrower convention
  requires a different-vendor controller with direct repo access and forbids
  same-vendor substitution; same-vendor sanity remains available only for
  ordinary bounded review outside that commissioned lane.

## Template Retrieval Binding

Forseti does not bind executor or reviewer lanes to runtime model identifiers.
Prompt authors may retrieve templates by registry ID from
`.agents/workflow-overlay/template-registry.md`, but a template target is prompt
posture only. It does not select, rank, recommend, or require the runtime model.
Model-target templates (`_generic/`) were retired 2026-06-13 (unused; owner decision);
only model-neutral templates remain registered.

```yaml
template_retrieval_binding:
  status: active
  registry: .agents/workflow-overlay/template-registry.md
  template_ids_authority: registry_registered_templates
  authority_order:
    - current_turn_explicit_user_instruction
    - template_registry_entry
    - accepted_forseti_handoff_or_prior_thread_state
    - reusable_workflow_kernel_advisory_template_guidance
  conflict_rule: use the highest listed source that explicitly selects a prompt template target, without expanding source-changing authority or runtime model choice.
```

Template retrieval does not produce language such as "run this on [model]",
"recommended model", or "reviewer model". It does not create implementation
permission, prompt-routing authority, validation success, executor-ready
instructions, or a paste-ready handoff. Executor-ready prompts and routed
handoffs remain prompt-orchestration work.

## Rules

- Reviewer threads are source-read-only unless explicitly assigned patch execution.
- Adversarial artifact review prompts must explicitly invoke
  `workflow-adversarial-artifact-review` after source readiness. If the skill is
  unavailable or not invoked, the prompt must block strict review claims or
  return advisory-only critique with the missing skill invocation named.
- Review prompts and review reports should close with a review-use boundary,
  not an expanded product-proof non-claims catalog unless the review target
  itself requires product-proof claim checking. The boundary is: review
  findings are decision input only; they are not approval, validation,
  mandatory remediation, or executor-ready patch authority until separately
  accepted or authorized.
- Adversarial artifact review prompts should request the compact
  `review_summary` YAML shape from
  `.agents/workflow-overlay/communication-style.md` before detailed findings,
  and should return a courier-ready fenced YAML block plus a short findings
  summary in chat.
- Reviews of new or materially touched durable human-authored workflow
  artifacts should check `.agents/workflow-overlay/retrieval-metadata.md`
  when retrieval metadata is in scope. Retrieval metadata defects are routing
  and authority-hygiene issues; they do not create approval, validation proof,
  readiness, lifecycle completion, or edit permission.
- Batch 0's temporary process-economics receipt obligation is retired. Its
  preserved evidence and final disposition are recorded in
  `.agents/workflow-overlay/batch0-process-pilot.md`; no current review closeout
  owes a Batch 0 receipt.
- Executor threads must not report success without file and validation evidence.
- Installed global `review`, implementation/code review, and artifact review remain separate lanes until Forseti accepts more specific routing.
- Runtime model recommendations for review lanes: forbidden. Template target
  retrieval is allowed only as prompt-shaping guidance.
- Prompt output contracts are bound in `.agents/workflow-overlay/prompt-orchestration.md`.
