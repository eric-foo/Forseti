# Delegated Review-and-Patch For High-Stakes Authored Artifacts

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: >
  Bound opt-in delegated review-and-patch lane for high-stakes authored
  Forseti artifacts and bounded code diffs, plus the overlay-interface fields
  a future skill implementation may read.
use_when:
  - A Chief Architect is deciding whether to commission a delegated
    review-and-patch hardening pass on a high-stakes authored artifact.
  - Checking the overlay-interface fields (status, operating-contract pointer,
    protected paths, model ladder, preflight, source context, output
    destinations) this convention exposes.
authority_boundary: retrieval_only
```

**Routine read shape** (owned by `.agents/workflow-overlay/source-loading.md`,
Targeted Read Protocol): commissioning reads "When it applies", "The loop",
"Access selection rule", "De-correlation", and the "Overlay Interface" block;
code-diff commissioning also reads "Code-diff target kind — the
`delegated_code_review_and_patch` sibling target kind"; return adjudication reads
"Adjudication closeout"; a full-file read is for editing this convention or
resolving a novel dispute about it.

**Status — bound opt-in lane.** This convention is bound Forseti review
doctrine (owner binding decision, 2026-07-25), on sustained commissioned use
recorded in Git/PR history plus the adjudicated within-change comparison in
`docs/workflows/efficiency/pr1111_success_implement_vs_delegated_review_case_v0.md`
(see *Evidence* below). Bound does not mean mandatory or machine-routable: the
lane activates only under an explicit Chief Architect commission (below), and
no category, label, or risk tier ever routes into it automatically.

**What it is — and what it is not.** This is a distinct commissioned,
bounded-executor lane with an integrated hardening review — not one of the
source-read-only review lanes in `.agents/workflow-overlay/review-lanes.md`.
Those lanes and the `AGENTS.md` reviewer-thread rule are unchanged: a reviewer
still does not edit sources, and "Reviewer threads are source-read-only unless
explicitly assigned patch execution" still holds. The actor here is an executor
the Chief Architect has commissioned with a bounded patch scope; its review is
the internal analysis it uses to decide its own patches. Patch authority comes
from the executor rule "edit only inside accepted scope" — the commission is the
accepted scope.

**When it applies — by commission, not by category.** This lane is available
only under an explicit Chief Architect commission that (1) names the target
required by the applicable target kind — one authored artifact or one explicit
multi-file code set — (2) states why ordinary source-read-only review is
insufficient, and (3) declares the bounded patch scope. Absent such a commission
it does not apply. The default target kind is for high-stakes *authored*
artifacts — doctrine, operating contracts, and eval/scoring/validation
instruments — where the author encodes guardrails and can reintroduce the exact
failure mode those guardrails exist to prevent; but the category alone never
triggers it. Trivial edits, routine prose, mechanical patches, and ordinary
review continue to use the cheap inline path — the author edits directly, or
the standard source-read-only review lane applies. This is never a mandatory
front door.

An owner instruction to `success implement` is an explicit **conditional**
commission for this lane, not a universal review gate. At implementation
closeout, before merge, it activates only when the Chief Architect can name a
material failure mode specific to the diff that could still pass every bound
test and required CI because the implementation and validation share the same
assumption, or because the decisive path has no independent oracle. The
commission must name that failure class, the validation gap, and the bounded
editable target. Generic author bias and labels of size, importance, novelty,
production proximity, or high stakes alone never satisfy this trigger. If that
concrete case cannot be made, delegation is not commissioned and the ordinary
validated path continues.

If delegation is explicitly commissioned for a work unit, freeze an
implementation commit inside the open PR, delegate, adjudicate and incorporate
accepted patches in that same PR, rerun validation, then merge.

**Direct invocation is courier-prompt authoring only.** An explicit user request
such as `delegate patch`, `write the delegate patch prompt`, or an invocation of
the delegated-review-patch skill requires the authoring agent to immediately
render exactly one paste-ready commission for the operator to courier from
target and commission fields safely inferable from the current context;
genuinely operator-owned values remain `operator_to_fill`. It must not first
search for or probe installed models, CLIs, plugins, controllers, or fallback
routes. The request does **not** authorize the authoring agent to create or
dispatch a task, fork a thread, spawn a subagent, or send the prompt.
The rendered prompt binds an unknown future receiver as
`receiver_to_bind` until the operator-selected controller proves
different-vendor lineage and direct repository access. If no eligible controller
is available, the prompt remains unexecuted; never substitute a same-vendor
model, self-review, no-repo reviewer, or Codex managed task.

**The loop.** The Chief Architect authors or specifies the artifact, then
commissions a single combined review-and-patch pass from a de-correlated model
(see *De-correlation* below), bounded to the named target file. The delegate:
(1) reviews the artifact for material failure modes; (2) patches the target file
directly within the commissioned scope; (3) treats all canonical,
compiler-emitted, test, hash-pinned, and other protected or generated paths as
read-only — it flags issues there, it does not patch them; (4) returns a unified
diff, source citations for each change, a verdict, and a residual-risk note. The
Chief Architect then adjudicates the returned diff before any of it is accepted
or kept — the diff and verdict are claims to adjudicate, not premises to
inherit. The delegate's citations and changes are decision input only; the Chief
Architect reserves final authority over what is kept and may veto any change it
judges to add no benefit or net-negative value, even when individually
defensible.

**Delegate lifecycle hard stop.** The rule text is the `lifecycle_hard_stop`
constant in `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
(single owner — do not fork or paraphrase it here). All lifecycle actions
remain with the Chief Architect after adjudication. A commission prompt that
omits this stop is incomplete.

**Adjudication closeout.** The delegated return is not complete merely because
it names a verdict, diff, findings, or residual risk. The return/courier prompt
must instruct the commissioning Chief Architect to close the adjudication with
`.agents/workflow-overlay/communication-style.md` -> **Review Adjudication Next
Step**: first adjudicate the findings, diff, verdict, and residuals as claims;
close any self-closable material issue -- one whose closure sits inside the
adjudicator's own authority and the commissioned scope, such as applying the
adjudicator's own modify/reject adjudications to the target -- in the same
turn; route a smallest-complete closure step only for an issue that genuinely
needs another review round, another lane, an architecture pass, or an owner
decision; once clean, batch admin/lifecycle follow-ups into exactly one land
step. Then, when a visible active goal or accepted next objective exists, state
the best next material move in the same turn so the owner does not need a
separate "what next?" round. Add further moves only when the immediate sequence
is genuinely needed to make that first move usable. A material move must
substantively advance the goal; commit, push, PR, merge, and other admin or
lifecycle work never qualify. When no goal or objective is visible, close
normally without inventing a roadmap or emitting an empty-result placeholder.
Closeout also retires transport artifacts: a courier prompt that was committed
to the repository solely for operator transport is deleted in the same lane PR
once its return is adjudicated (Git history preserves it); the default carrier
for a lane-scoped courier prompt remains the lane PR body/comment or ignored
scratch per `.agents/workflow-overlay/prompt-orchestration.md` filing rules.
This is an adjudicator obligation, not permission for the delegate to decide
what is kept or widen review scope.

**Delegated review-output finalization gate.** Any delegated review output
written under `docs/review-outputs/` blocks final chat closeout until, after the
final report write, `python .agents/hooks/check_review_output_provenance.py --strict <report-path>`
exits 0. If the report is changed after that command, rerun it and report only
the final observed result. Embedded live diffs must be inside a proper
standalone `diff` fence and must be generated/read back as real multiline text,
not hand-collapsed into prose; use `.github/scripts/review-report-mechanics.py`
to generate and verify an embedded diff instead of hand-pasting one. Future-tense placeholders such as "must be
checked after this report is written" are not allowed in the durable report.
This gate is mechanical shape/integrity only: it is not approval, validation,
readiness, review quality, or acceptance of the delegated findings.

**Access selection rule.** Delegated review-and-patch is `repo` only. The
delegate must have direct repository/worktree access and patch the named target
inside that repository. `no_repo` is not a weaker execution mode for this lane;
it is ineligible. When repository access is unavailable, author a different,
read-only review prompt under the ordinary review contract or leave the delegated
patch prompt unexecuted. Do not relabel advisory findings plus home-lane patching
as delegated patch authorship.

**Couriered multi-round review loops.** The authoring agent may mechanically
verify that an accepted diff applied cleanly and that named validation passed,
but it must not commission a same-vendor model as a delegated-patch closure
reviewer. If independent closure review is required, author another courier
prompt for an eligible different-vendor controller with direct repo access. If
that controller is unavailable, report the review as not run; do not manufacture
a lower-tier or same-family substitute.

**Citations.** The delegate's citations are neutral in tone — factual source
evidence, no advocacy or editorializing — but decision-sufficient in substance,
so the Chief Architect's veto stays informed rather than blind. The delegate's
argument belongs in the verdict and residual, not the citations. Neutral tone is
not thinness: thin citations would push the Chief Architect back onto its own
priors and defeat the de-correlation.

**De-correlation — observable criterion and no fallback.** "Family" here means
**vendor / model lineage** (e.g., Claude vs GPT), **not tier**. **Vendor** = the upstream model
developer/provider (e.g., Anthropic, OpenAI) — **not** the hosting platform, API
reseller, deployment surface, or wrapper/fine-tune owner; **unknown or undisclosed
lineage cannot satisfy the delegated-review-and-patch bar**. The commission
must record the author vendor and the delegate vendor; the **cross-vendor
discovery** bar is satisfied only when they **differ**. A same-vendor delegate —
**even a different or lower tier** (e.g., an Opus author with a Sonnet delegate)
— is **ineligible** for this commissioned lane, including under a `sanity`,
`verification`, `fallback`, or lower-tier label. A self pass is likewise
ineligible. The general two-bar vocabulary in
`.agents/workflow-overlay/review-lanes.md` remains available for ordinary
review outside this lane; it cannot be used to convert a delegated patch
commission into same-vendor review. If a cross-vendor repo delegate cannot be
established, leave the courier prompt unexecuted or route a separately named
read-only review. Never claim or perform a delegated patch fallback.

This is a who-constraint recorded in the commission, not a model-quality
recommendation and not runtime model routing. It does not belong in review
prompts as model-selection advice, and it does not alter Forseti review-lane
model-neutrality: `.agents/workflow-overlay/review-lanes.md` and
`.agents/workflow-overlay/prompt-orchestration.md` still forbid review lanes,
review prompts, wrappers, handoffs, and closeouts from recommending,
prescribing, ranking, or implying runtime model choice. Model choice remains an
operator, tooling, and commission decision; this convention names model
*families* only to express the difference constraint, never to select or rank a
runtime model.

**Escalation.** When the artifact's problem is design-level rather than
patch-level, the delegate returns `NEEDS_ARCHITECTURE_PASS`, stops patching, and
returns findings only; any partial diff is quarantined and is not kept.
Escalation routes the artifact back to an architecture pass; it never forces a
patch onto a broken design, and a partial patch must never survive by inertia.

**Why.** De-correlation catches the author's own blind spots that self-review
structurally misses. Combining review and patch into one commissioned pass, with
the Chief Architect adjudicating the resulting diff, collapses the
Chief-Architect-thread context bursts that a review -> adjudicate -> instruct ->
patch -> re-read round-trip would otherwise spend; the saving scales with context
size times the round-trips collapsed. A cheap de-correlated pass before the Chief
Architect commits prevents an expensive wasted run on a correlated error.

**Strict-claim boundary.** A delegated diff plus verdict is decision input only.
Formal `PASS`, severity authority, readiness, and validation status still follow
the Review Doctrine in `.agents/workflow-overlay/review-lanes.md` and the prompt
validation gates in `.agents/workflow-overlay/prompt-orchestration.md`; this
convention creates none of them.

**Incomplete commission route-out.** When the user invokes this convention but
the commission is missing operator-owned fields (for example delegate vendor,
controller identity, access mode, report destination, or provenance values),
do not end on an inert blocker if the target and review purpose are inferable.
Route under `.agents/workflow-overlay/prompt-orchestration.md`: an eligible
current-lane, operator-couriered prompt uses **Lane-Scoped Delegated Patch Prompt
Default** and is carried in the lane PR/comment or ignored scratch; a prompt
matching the **Full orchestration** predicate in
`.agents/workflow-overlay/prompt-orchestration.md` uses the full
`workflow-prompt-orchestrator` contract. Missing
operator-owned values are clearly marked `operator_to_fill`; delegation or patch
authorization alone does not trigger the full route. Block only when the target,
review purpose, patch authority, or safe target state cannot be inferred, or
when the applicable prompt contract cannot be applied. If the inferred target
is a multi-file implementation/code diff rather than a single authored artifact,
do not force it into the authored-artifact target kind: route it to the
**`delegated_code_review_and_patch`** sibling target kind below, which keeps the code
review lane as its review method and bounds the patch to an explicitly named
file set. When no patch authority is commissioned, route via prompt-orchestrator
to read-only implementation/code review instead; patch authority is never
assumed from the target category.

Route-out is authoring only: it returns the paste-ready prompt to the operator
and does not inspect local controller availability or dispatch any receiver.
The prompt records `delivery: operator_courier_only`, `access: repo`,
`delegate_eligibility: different_vendor_lineage_with_direct_repo_access`, the
observed author vendor, and either a different observed delegate vendor or
`delegate_vendor: operator_to_fill`. `operator_to_fill` is preparation state,
not evidence that the eligibility condition passed.

**Code-diff target kind — `delegated_code_review_and_patch`.**
The default loop above targets a single *authored* artifact and uses the
delegate's own adversarial analysis as the review. A bounded multi-file
implementation/code diff is handled by this **sibling target kind**: the same
commissioned convention with exactly two binding deltas. Everything else —
explicit commission, the de-correlation who-constraint, the repo-only access
obligation, CA adjudication of the returned diff before any keep, the
`NEEDS_ARCHITECTURE_PASS` escalation, the strict-claim boundary, and the
no-runtime-model-recommendation rule — is inherited unchanged. The code-review
lane is the review method; `no_repo` remains outside this convention.

1. **The review method is the code review lane, not artifact review.** The
   delegate's review portion is `workflow-code-review` run under the Review
   Prompt Defaults. The code review lane stays the
   review method for code; this convention only adds commissioned bounded patch
   authorship plus CA adjudication on top of it, and never replaces, weakens, or
   relabels code review, nor merges it with artifact review (those remain
   separate lanes per `.agents/workflow-overlay/review-lanes.md`). The
   `fitness_reference` rule stays artifact-review-only; code's fitness bar —
   spec, tests, ground-truth substrate — governs here.
2. **The target is an explicitly named multi-file set, not one file.** The
   commission names the bounded set of code files in scope (one or more). That
   named set replaces the single-file bound as the only patchable surface;
   everything outside it — all other code, all canonical / generated / hash-pinned
   paths, and every path the safety rules forbid — stays read-only / flag-only.
   The named set is the whole patch scope and **cannot silently widen**: touching
   a file the commission did not name requires a re-commission, never a
   delegate-side expansion.

Two obligations are stated explicitly here because code carries them:

- **Validation/test obligations are named and can fail.** The commission names
  the tests and gates the touched code must satisfy (tests inside the touched set
  are part of the named target). The delegate runs them and reports real results;
  a failing test or gate is surfaced, never masked or routed around, and the
  returned diff asserts no `PASS`, readiness, or settled status — failure
  visibility holds exactly as under the executor rule.
- **Patch authority stays subordinate to implementation authorization.** A
  commissioned code patch is an explicit bounded source-changing authorization
  under `.agents/workflow-overlay/safety-rules.md` and `AGENTS.md`; this target kind
  supplies the *shape*, never a standing authorization, and never bypasses the
  implementation-authorization boundary. By commission, not by category — the
  code-diff category alone never triggers this target kind; an un-commissioned diff
  routes to read-only code review.

**Repo-mode discovery discharges a downstream independent-review gate.** When a
cross-vendor delegate runs the `repo`-mode loop — full-target discovery under
the target kind's bound review method (the delegate's own adversarial analysis
for an authored artifact per loop step 1, the code review lane for a named
code set; not only the patched lines) plus authorship of the bounded fix — and
the CA adjudicates and independently verifies closure (a class-level sweep for
the finding's leak class plus byte/scope checks), that pass
**satisfies** a `cross_vendor_discovery` independent-review requirement for the
*patched* artifact (for example, a pre-freeze leakage gate). A separate
standalone post-patch re-scan is **not** additionally required to clear that gate.
The one non-independent sliver — the delegate's own edited lines — must be
mechanically verifiable (e.g. a class sweep), and the CA records that limitation
on the durable disposition. *Proportionality, owner-set by assurance tier:* a
higher tier (e.g. buyer-proof) may still require a separate independent pass;
product-learning / N-case-batch tiers may rely on the delegated pass. *Residual,
named:* a **novel** leak class shared across vendors and absent from the swept
set is caught by neither the class sweep (which catches known systematic classes)
nor batch averaging (which cancels random misses) — bounded and acceptable below
buyer-proof, not zero. `no_repo` is outside this lane because it loses delegated
patch authorship; it must route to an ordinary read-only review rather than a
same-vendor or home-authored patch fallback.

**Delegate-authored capability work does not inherit discovery.** A commission
may include owner-directed capability work — a redesign or feature the owner
has already decided, executed by the delegate inside the bounded patch scope.
The cross-vendor discovery bar then covers only the delegate's review of the
pre-existing diff; it does not extend to the lines the delegate itself
authored. Those lines receive the same treatment as the non-independent sliver
above — mechanical verifiability plus CA adjudication, with the limitation
recorded on the durable disposition — and when authored capability work
dominates the returned diff, the pass discharges no independent-review gate
for that work: route it as an implementation handoff with its own separate
review instead of relabeling authorship as review.

## Overlay Interface (fields a future skill implementation may read)

This is the seam to handoff 2 (a skill implementation, authored separately - not in
this overlay binding). The fields below defer to existing Forseti overlay authority
and do not fork or restate it.

The prose sections above are the single semantic owner of every rule in this
convention. The interface below carries only routing facts a skill needs to
resolve — field names, renderers, and pointers — never a second statement of a
rule; where a value summarizes prose, the prose section named in the comment
wins.

```yaml
delegated_review_patch_overlay_interface:
  status: bound_opt_in_commission   # explicit CA commission only; never mandatory or machine-routable
  operating_contract_pointer: .agents/workflow-overlay/delegated-review-patch.md
  prompt_routing:
    full_renderer: workflow-prompt-orchestrator
    compact_renderer: .agents/workflow-overlay/prompt-orchestration.md#lane-scoped-delegated-patch-prompt-default
    selection_rule: compact renderer when its predicate holds; otherwise full renderer; depth never grants dispatch authority
  target_kinds:
    authored_artifact: single CA-named authored artifact; review method is the delegate's own adversarial analysis   # semantics: "The loop" above
    delegated_code_review_and_patch: explicitly named multi-file code set; review method is the code review lane   # semantics: "Code-diff target kind" above
  incomplete_commission_route_out: .agents/workflow-overlay/prompt-orchestration.md   # semantics: "Incomplete commission route-out" above
  protected_path_list: .agents/workflow-overlay/safety-rules.md   # delegate patches only the CA-named target set; semantics: "The loop"; "Code-diff target kind"
  delegate_lifecycle_hard_stop: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md   # lifecycle_hard_stop constant
  de_correlation_commission_constants: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md   # semantics: "De-correlation" above; no fallback of any kind
  access_modes: repo_only   # semantics: "Access selection rule" above
  output_destinations: chat or lane PR/comment by default   # semantics: "The loop"; "Adjudication closeout"; prompt-orchestration.md filing rules
```

```yaml
direction_change_propagation:
  doctrine_changed: Direct delegate-patch invocations immediately render one operator-courier prompt without discovery or dispatch preflight.
  trigger: workflow_authority
  related_triggers: [review_authority]
  controlling_sources_updated: [.agents/workflow-overlay/delegated-review-patch.md]
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - .agents/workflow-overlay/review-lanes.md
  intentionally_not_updated:
    - {path: .agents/workflow-overlay/prompt-orchestration.md, reason: "Already requires exactly one courier prompt and forbids controller inspection, task creation or dispatch, and fork or spawn."}
    - {path: installed and plugin skills, reason: "Deployment copies do not control this Forseti direct-invocation rule."}
    - {path: hooks, tests, and registries, reason: "No mechanical gate or registry behavior changes."}
  stale_language_search: rg -n -i "separate explicit execution request|discover a controller|inspect installed controllers|delegate patch" AGENTS.md .agents/workflow-overlay
  non_claims: [not validation, not readiness]
```

## Evidence And Non-Claims

**Evidence.** Origin: replicated 2026-06 from jb's provisional convention
(cross-project provenance only; jb authority, paths, and lifecycle mechanics
are not imported). Forseti-side evidence at binding (2026-07-25): sustained
commissioned use across lanes recorded in Git/PR history, and one adjudicated
within-change comparison —
`docs/workflows/efficiency/pr1111_success_implement_vs_delegated_review_case_v0.md`
— where the cross-vendor pass contributed one unique accepted material finding
(a wrong-cause-green test gap) beyond a same-vendor in-session review. This
supports binding the lane as an opt-in commission; it is not a statistical
result and the lane's cost remains unmeasured (accepted residual — capture
wall-clock/token cost on future runs only if a routing decision comes to
depend on it).

**Non-claims.** This lane is not validation, not readiness, not a mandatory or
machine-routable front door, not patch authorization beyond an explicit
bounded CA commission, and not runtime model routing.
