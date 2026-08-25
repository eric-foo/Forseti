# Phase A Hype/Trust Decision-State Adversarial Delegated Code Review-And-Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated adversarial code review-and-patch prompt
scope: Cross-vendor bounded recheck and patch of the sealed Phase A hype/trust Decision State implementation at d669777a.
use_when:
  - Couriering the post-review, post-dogfood hype/trust implementation for final de-correlated review.
  - Rechecking exact parent-context authority, quote routing, compact-reader joins, and evidence accounting before landing.
authority_boundary: retrieval_only
branch_or_commit: codex/hype-trust-axis @ d669777ac1e42a0ff330c649f76bdeb37f6f300c
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - .agents/workflow-overlay/safety-rules.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
stale_if:
  - Any implementation target changes after d669777ac1e42a0ff330c649f76bdeb37f6f300c other than this later courier prompt.
  - The owning claim-support, review, prompt, or validation authority changes before review.
```

## Commission And Receiver Binding

Run a de-correlated `delegated_code_review_and_patch` recheck on the exact
implementation commit. Inspect the repository directly. The author/home family
is OpenAI; the controller must be from a different upstream vendor/model
lineage. This is a who-constraint, not a runtime-model recommendation. The
operator selects the controller. If the controller cannot prove different-
vendor lineage and direct repository access, return `BLOCKED_REVIEW_ROUTE`
without substituting a same-vendor, self, no-repo, or context-pack review.

```yaml
delivery: operator_courier_only
receiver_class: receiver_to_bind
access: repo
worktree: C:\Users\vmon7\.codex\worktrees\phase-a-hype-trust-axis
revision_mode: exact
required_revision: d669777ac1e42a0ff330c649f76bdeb37f6f300c
prior_reviewed_revision: 03b7fee9e380c305be6e8a370f58113edf8c8486
implementation_diff: e455231eecb82f47c5c1ec9acd3de29512e061be..d669777ac1e42a0ff330c649f76bdeb37f6f300c
recheck_patch_diff: 3edaa585aaa87c7ef2e1fc78a01d4422ca6ec6b8..d669777ac1e42a0ff330c649f76bdeb37f6f300c
expected_branch: codex/hype-trust-axis
dirty_state_allowed_at_start: false
output_mode: review-report
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
review_lane: workflow-code-review
mode: base-subagent
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_adversarial_delegated_code_review_recheck_v0.md
author_home_model_family: OpenAI
controller_model_family: operator_to_fill_different_vendor_required
current_receiving_actor_role: controller
dispatch_mode: external-controller-courier
de_correlation_status: verify_before_source_review
review_routing_status: routed
```

Read the exact target and authorities before findings. Do not dispatch another
controller: the receiving actor is the controller. Invoke `workflow-code-review`
after source context is ready. If that lane is unavailable, return
`BLOCKED_REVIEW_LANE_UNAVAILABLE` and do not patch.

Do not push, merge, publish, edit frozen inputs or outputs, rerun capture or
semantic extraction, or broaden the axis. Patch only these five files; all
other repository and frozen-source files are read-only and flag-only:

- `[projector]` `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py`
- `[selector]` `forseti-harness/judgment/phase_a_evidence_selection.py`
- `[projector-tests]` `forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py`
- `[selector-tests]` `forseti-harness/tests/unit/test_phase_a_evidence_selection.py`
- `[workflow]` `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

## Prior Review And Bound Adjudication

Read the prior report if it is present at
`docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_delegated_code_review_v0.md`.
Its architecture valve fired at the old revision because manual
`parent_contexts` could pass without an artifact cross-check. The home
adjudication accepted the defect but rejected a schema re-freeze: the existing
hash-pinned candidate dispositions already contain the exact parent source and
text needed to derive context. The patch therefore removes spec-authored parent
contexts and derives them only from the matching pinned candidate.

Recheck closure of the prior blocker and majors first:

1. A made-up, altered, sibling, neighboring-point, right-text/wrong-source, or
   manually spec-authored parent must fail before projection.
2. Legacy quote prompting must not receive parent text; only the context-complete
   quote route may receive it, and output quotes must remain literal child text.
3. Every semantic row handle in the compact reader must be identity-bound to the
   exact selected evidence row, including plausible in-range swaps.
4. Parent context must not silently lend source role, date, engagement, or
   customer/creator status to the child. Its exact source reference and text
   remain visible context, not evidence.
5. Exact per-point hype meanings must survive without forcing a speculative
   cross-axis hype enum or widening the decision object.

Then scan only the touched patch scope for patch-caused or newly visible
blocker/major issues. Exclude unrelated structural review, minor/nit findings,
and pre-existing issues outside the touched scope. If a design-level problem
still prevents a truthful bounded patch, stop patching, revert partial edits,
and return `NEEDS_ARCHITECTURE_PASS` with findings only.

## Fitness Reference

Goal: the complete frozen hype/trust axis must compact exact actor judgments
without turning neighboring judgments or neighboring objects into each other,
while keeping every literal evidence join recoverable for a cold reader.

Observable success:

- all five accepted points and all 2,145 candidate dispositions participate;
- formula preference, overall praise, overhype, failure to meet hype, and love
  despite viral popularity remain distinct Decision States;
- generic performance or praise cannot become hype-fit evidence;
- formula-, variant-, attribute-, and overall-product judgments are not silently
  widened across object scope;
- a terse Reddit reply may use only its exact hash-pinned candidate parent to
  recover an omitted premise or referent, while the quote remains literal child
  text;
- the compact reader exposes direct evidence, quote, semantic, state, and
  parent-context row handles with exact identity rechecks, without duplicating
  the whole placement table;
- one displayed evidence row, one origin, and two observations from that same
  origin remain three different counts;
- Reddit comments do not become posts, creator resonance does not become
  customer truth, engagement does not manufacture relevance, and quiet evidence
  remains displayable without promotion;
- v1 rebuild bytes and Direct Outcome behavior remain unchanged; and
- Phase A packs evidence only and makes no prevalence, causal, market,
  positioning, pricing, or delivery recommendation.

The highest-loss plausible false green is a traceable, compact output that
looks exact while treating “overhyped,” “did not live up to hype,” “worth the
hype,” and “love despite going viral” as positive/negative synonyms—or attaches
a terse reply to the wrong parent. Tests and implementation can agree on that
wrong meaning, so attack semantics as well as structure.

## Required Adversarial Attacks

1. `[selector]` Try to promote generic praise, disappointment, recommendation,
   comparison, value, and behavior into hype-fit support or counterevidence.
2. `[selector]` Try to collapse overhype into exact hype shortfall, worth-the-
   hype into viral love, and love-plus-overhype into a contradiction.
3. `[selector]` Try to widen formula, ingredient-safety, shade, scent, variant,
   or attribute judgments into overall-product judgments, and the reverse.
4. `[selector]` Attach a terse reply to an unknown, sibling, neighboring-point,
   duplicated, altered, or right-text/wrong-source parent. Confirm the spec
   cannot author parent context and the quote cannot borrow parent wording.
5. `[projector]` Mutate every direct reader row ID to a plausible in-range row
   owned by another selected item. Confirm evidence, quote, semantic, state, and
   parent-context mismatches fail at `decision_state_reader_evidence_binding`.
6. `[projector]` Attack omission of the removed placement table: confirm the
   relation row joins still recover all selected evidence, meanings, states,
   contexts, quotes, relations, source surfaces, engagement, and hash lineage.
7. `[projector]` Attack missing/duplicate decision bindings, state/object/stage/
   direction drift, companion-state attachment, re-projection, idempotency, and
   legacy-v1 isolation.
8. `[projector] [selector]` Attack source role/venue, Reddit post/comment
   surface, date, engagement kind/raw value, origin identity, relation, quote,
   and hash lineage. Confirm no creator/customer laundering.
9. `[tests]` Confirm wrong-cause tests reach the intended semantic boundary
   rather than an earlier hash, range, or identity guard, and do not repeat the
   production implementation as their oracle.
10. `[workflow]` Compare prose with executable behavior, especially exact-parent
    derivation, object-scope adjacency, compact evidence accounting, hype premise
    requirements, and the Phase A/Deliver boundary.
11. Consider and defend plausible attacks that do not become findings; do not
    silently discard them.

## Evidence To Confirm, Not Trust

- Frozen source packet raw SHA-256:
  `51e8f2ea1a071594b792a0132ed176a20adc4021aeade271e03c4916e62980b2`.
- Frozen bundle raw SHA-256:
  `fdb0803e5e5199bc2d6d7e75c866142f4b4f81a1cc42676a8bbcab84f8ae7ff6`.
- Frozen axis-pack raw SHA-256:
  `34c78ca112a2f734166019e1669fa27afd4739295eac1cc9ec967e51c6a9c8c7`.
- Repeated final compact views:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\post_review_validation\consolidated_view_7.json`
  and `consolidated_view_8.json`; both raw SHA-256
  `2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714`
  and stored logical view SHA-256
  `a73fdc0807e72d281745e7a0ed96fc208a3231fad003eaa5a3317631b764baa2`.
- Final dogfood receipt:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\dogfood_post_review_no_duplicate_placement\final_receipt.json`,
  raw SHA-256
  `e6d511ac467d278b79b50e37d7c00c888f20bd16df540a0ad932952a8abe2b11`.
- Three alternating opaque-label comparisons produced 46 ties, two compact
  wins, zero full-input wins, zero critical errors, no recurring material point
  regression, no direct mirror reversal, and two disclosed tie-to-compact mirror
  drifts.
- Compact used 154,345 logical tokens versus 197,879 for full input: 43,534
  fewer (22.0%), lower in every repetition. Compact input was 147,885 with
  14,080 cached input disclosed and not subtracted; compact output was 6,460,
  with 1,225 reasoning tokens already included in output.
- Per-repetition compact/full logical totals were 51,768/66,250,
  51,858/65,406, and 50,719/66,223.
- Affected unit suite: 252 passed. Harness coupling contracts: 18 passed.

Accepted pre-review residuals: the dogfood actor and judges are same-vendor;
two mirrored judgments drifted from tie to compact rather than directly
reversing; one frozen product axis cannot prove every future Decision State
category; parent context is exact provenance-bound context but not evidence and
does not carry independently captured role/date/engagement metadata; no claim
is made about prevalence, market representativeness, causality, or delivery
recommendations.

## Validation And Return Contract

After any patch, run at minimum:

```powershell
python -m pytest -p no:cacheprovider -q forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py forseti-harness/tests/unit/test_phase_a_evidence_selection.py
python .agents/hooks/check_harness_coupling.py --strict
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --changed --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
git diff --check
```

Write the bound report destination and run its applicable review-output
provenance gate. Return findings first with severity, confidence, exact
file/line evidence, `minimum_closure_condition`, and
`next_authorized_action`; include `considered_and_defended`, one overall
verdict, the uncommitted unified diff, and residual risk. Prefix findings,
citations, and diff notes with the target labels above.

Do not commit the patch. The home/Chief Architect adjudicates every returned
change and owns commit, push, PR, merge, publish, and lifecycle actions.
