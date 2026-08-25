# Phase A Hype/Trust Decision-State Adversarial Delegated Code Review-And-Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated adversarial code review-and-patch prompt
scope: Cross-vendor bounded recheck and patch of the Phase A hype/trust Decision State ownership repair at 961e3e29.
use_when:
  - Couriering the post-review, post-dogfood hype/trust implementation for final de-correlated review.
  - Rechecking exact parent-context authority, quote routing, compact-reader joins, and evidence accounting before landing.
authority_boundary: retrieval_only
branch_or_commit: codex/hype-trust-axis @ 961e3e29ba6c6d5fee1c4055c810e3306ddf13a5
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
  - Any implementation target changes after 961e3e29ba6c6d5fee1c4055c810e3306ddf13a5 other than this later courier prompt.
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
required_revision: 961e3e29ba6c6d5fee1c4055c810e3306ddf13a5
prior_reviewed_revision: d669777ac1e42a0ff330c649f76bdeb37f6f300c
implementation_diff: d669777ac1e42a0ff330c649f76bdeb37f6f300c..961e3e29ba6c6d5fee1c4055c810e3306ddf13a5
repair_diff: 699bdeff7ac8a2bb31537b0f6018a47e57782541..961e3e29ba6c6d5fee1c4055c810e3306ddf13a5
expected_branch: codex/hype-trust-axis
dirty_state_allowed_at_start: false
output_mode: review-report
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
review_lane: workflow-code-review
mode: base-subagent
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_adversarial_delegated_code_review_recheck_v1.md
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

Read the returned report completely at
`docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_adversarial_delegated_code_review_recheck_v0.md`
(raw SHA-256
`921c78345bdd0f0590bd3c7bb8748d42c9c06d12ae8099474c5eeb14996adc02`).
Its architecture valve fired on four majors. Home adjudication accepted all
four defects but rejected the claim that broad architecture or a source-schema
re-freeze was necessary. The repair recomputes the full source-shaped candidate
inventory against the selector's existing hash when linked parent context is
enabled; adds primary-plus-companion semantic ownership and a state-partition
digest to the compact row; mechanically binds compact accounting rule
identities; and versions the incompatible compact shape as reader v3. Old v2
outputs remain untouched.

Recheck closure of the prior blocker and majors first:

1. A made-up, altered, sibling, neighboring-point, right-text/wrong-source, or
   manually spec-authored parent must fail before projection at the candidate
   inventory boundary. Confirm the test reaches this boundary after the outer
   artifact and manifest hashes are honestly repinned.
2. Legacy quote prompting must not receive parent text; only the context-complete
   quote route may receive it, and output quotes must remain literal child text.
3. Every semantic and state row handle in the compact reader must be
   identity-bound to the exact selected evidence row, including plausible
   in-range swaps that preserve valid ranges and semantic membership.
4. Parent context must not silently lend source role, date, engagement, or
   customer/creator status to the child. Its exact source reference and text
   remain visible context, not evidence.
5. Exact per-point hype meanings must survive without forcing a speculative
   cross-axis hype enum or widening the decision object.
6. The compact accounting contract must fail if its rule identities diverge
   from the authoritative contract, and the emitted reader must identify as v3
   rather than sharing v2 with an incompatible historical shape.

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
- Repeated reader-v3 compact views:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\post_review_validation\consolidated_view_9_v3.json`
  and `consolidated_view_10_v3.json`; both raw SHA-256
  `0151893391d762a85e09fa41830bad17cd9543a618c97096aee96c03f68b9b80`
  and stored logical view SHA-256
  `7873ee464108381014dbff117479470a47e7e6ce062a80f5f5f31315bedb8bbc`.
  Each contains all five points, 2,145 candidate dispositions, 65 placements,
  210 state assertions, and 32 unique evidence items. Historical v2 views 7
  and 8 remain byte-unchanged at raw SHA-256
  `2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714`.
- Final reader-v3 dogfood receipt:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\dogfood_post_review_v3\final_receipt.json`,
  raw SHA-256
  `c0cc199deb5fa59b78bc57dfd24558bf0348edfe1893f01d5b79934a15f44bad`.
- Three alternating opaque-label comparisons produced 42 ties, six compact
  wins, zero full-input wins, zero compact critical errors, no recurring
  material point regression, and no direct mirror reversal. The full arm had
  one critical parent-context omission in repetition 3; the compact arm exposed
  that dependency.
- Compact used 165,000 logical tokens versus 197,879 for full input: 32,879
  fewer (16.616%), lower in every repetition. Compact input was 158,772 with
  zero cached input; compact output was 6,228, with 960 reasoning tokens already
  included in output. Full cached input was 13,056 and was disclosed without
  subtraction.
- Per-repetition compact/full logical totals were 55,107/66,250,
  55,017/65,406, and 54,876/66,223.
- Affected unit suite: 254 passed. Harness coupling contracts: 18 passed.

Accepted pre-review residuals: the dogfood actor and judges are same-vendor;
the unchanged full arm was reused only after input, prompt, response schema, and
payload hashes matched byte-for-byte; one frozen product axis cannot prove every
future Decision State category; parent context is exact provenance-bound context
but not evidence and does not carry independently captured role/date/engagement
metadata; the reader-v3 surface is 15,565 bytes larger than the final v2 surface
while still avoiding a duplicate placement table; no claim is made about
prevalence, market representativeness, causality, or delivery recommendations.

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
