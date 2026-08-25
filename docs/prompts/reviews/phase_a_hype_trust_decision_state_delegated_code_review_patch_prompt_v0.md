# Phase A Hype/Trust Decision-State Delegated Code Review-And-Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated code review-and-patch prompt
scope: Cross-vendor adversarial review and bounded patch of the Phase A hype/trust Decision State projection at commit 03b7fee9.
use_when:
  - Couriering the complete frozen hype/trust axis for its post-implementation review.
  - Attacking hype-state conflation, decision-object widening, terse-reply context loss, and compact-reader joins before landing.
authority_boundary: retrieval_only
branch_or_commit: codex/hype-trust-axis @ 03b7fee9e380c305be6e8a370f58113edf8c8486
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
  - Any implementation target changes after 03b7fee9e380c305be6e8a370f58113edf8c8486 other than this later courier prompt.
  - The owning claim-support, review, prompt, or validation authority changes before review.
```

## Commission And Receiver Binding

Run a de-correlated `delegated_code_review_and_patch` pass on the exact
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
revision_mode: exact
required_revision: 03b7fee9e380c305be6e8a370f58113edf8c8486
reviewed_diff: 215ef97155f1fddda1ebb2e0c13418aacf798d04..03b7fee9e380c305be6e8a370f58113edf8c8486
expected_branch: codex/hype-trust-axis
dirty_state_allowed_at_start: false
output_mode: review-report
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
review_lane: workflow-code-review
mode: base-subagent
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_delegated_code_review_v0.md
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
- a terse Reddit reply may use only its exact hash-bound parent to recover an
  omitted premise or referent, while the quote remains literal child text;
- the compact reader exposes direct evidence, quote, semantic-unit, and parent-
  context row handles with identity rechecks;
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
   duplicated, altered, or right-text/wrong-source parent. Confirm the quote
   cannot borrow or splice parent wording.
5. `[projector]` Mutate each direct reader row ID while leaving its text ID
   plausible. Confirm evidence, quote, semantic, and parent-context mismatches
   fail at `decision_state_reader_evidence_binding`.
6. `[projector]` Attack missing/duplicate decision bindings, state/object/stage/
   direction drift, companion-state attachment, re-projection, idempotency, and
   legacy-v1 isolation.
7. `[projector] [selector]` Attack source role/venue, Reddit post/comment
   surface, date, engagement kind/raw value, origin identity, relation, quote,
   and hash lineage. Confirm no creator/customer laundering.
8. `[tests]` Identify any load-bearing test that repeats production logic or
   fails at an earlier identity/hash guard instead of the intended semantic
   boundary.
9. `[workflow]` Compare prose with executable behavior, especially exact-parent
   use, object-scope adjacency, hype premise requirements, and the Phase A/
   Deliver boundary.
10. Consider and defend plausible attacks that do not become findings; do not
    silently discard them.

`NEEDS_ARCHITECTURE_PASS` is the escalation valve. On a design-level problem,
stop patching, revert any partial diff, and return findings only.

## Evidence To Confirm, Not Trust

- Frozen source packet raw SHA-256:
  `51e8f2ea1a071594b792a0132ed176a20adc4021aeade271e03c4916e62980b2`.
- Frozen bundle raw SHA-256:
  `fdb0803e5e5199bc2d6d7e75c866142f4b4f81a1cc42676a8bbcab84f8ae7ff6`.
- Build receipt:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\build_receipt_postfix2.json`,
  raw SHA-256
  `0cc9791b5c1d187724eeab8287333fbe6afb905b4dcf807ee4810ddf07c71936`.
- Exact repeated axis-pack raw SHA-256:
  `34c78ca112a2f734166019e1669fa27afd4739295eac1cc9ec967e51c6a9c8c7`.
- Exact repeated compact-view raw SHA-256:
  `49f23acf73f496bfa6744d5109286d9e0e6c10300d4a8bc5e5c71c1e34ec7837`.
- Dogfood receipt:
  `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2\dogfood\final_receipt.json`,
  raw SHA-256
  `0745ea3dcaf1334ffc7f637bf17cfaaf9a0179dd0309f8846a7562d1a49fd4da`.
- Three alternating opaque-label comparisons produced 43 ties, four compact
  wins, one full-input win, zero critical errors, no direct mirror reversals,
  and one disclosed non-gating tie drift.
- Compact used 176,015 logical tokens versus 195,646 for full input: 19,631
  fewer (10.034%), lower in every repetition. Cached compact input was 13,056
  and is not subtracted; reasoning is already a subset of output.
- Affected unit suite: 251 passed. Harness coupling contracts: 18 passed.

Accepted pre-review residuals: the dogfood actor and judges are same-vendor;
one mirror comparison drifted between a full-input win and a tie; the evidence
is one frozen product axis; the object-scope rule is prompt-enforced and should
not be mistaken for a new semantic authority; no claim is made that every
future Decision State category is complete.

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
