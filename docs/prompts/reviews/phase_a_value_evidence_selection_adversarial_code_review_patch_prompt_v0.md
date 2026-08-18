# Phase A Value Evidence Selection Adversarial Code Review-And-Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated code review-and-patch prompt
scope: Cross-vendor adversarial review and bounded patch of the Phase A v3 value-only evidence-selection policy at commit a054a74d5e11c209bc2247cb8103cf3b78a1cd7a.
use_when:
  - Couriering the value-only selection change for its required post-implementation review.
  - Attacking false positive-value evidence, complaint selection, engagement ordering, label overclaim, and quote clipping before landing.
authority_boundary: retrieval_only
branch_or_commit: codex/phase-a-selection-quotes @ a054a74d5e11c209bc2247cb8103cf3b78a1cd7a
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - .agents/workflow-overlay/safety-rules.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
stale_if:
  - The reviewed target files move off a054a74d5e11c209bc2247cb8103cf3b78a1cd7a before the reviewer captures an exact worktree.
  - The owning claim-support, semantic-integration, review, or prompt authority changes before review.
```

## Commission And Receiver Binding

Run a de-correlated `delegated_code_review_and_patch` pass on the exact target
revision. Inspect the repository directly. The author/home family is OpenAI;
the controller must be from a different upstream vendor/model lineage. This is
a who-constraint, not a runtime-model recommendation. The operator selects the
controller. If the controller cannot prove different-vendor lineage and direct
repository access, return `BLOCKED_REVIEW_ROUTE` without substituting a
same-vendor, self, no-repo, or context-pack review.

```yaml
delivery: operator_courier_only
receiver_class: receiver_to_bind
access: repo
revision_mode: exact
required_revision: a054a74d5e11c209bc2247cb8103cf3b78a1cd7a
reviewed_diff: 6f98f50c37099ff3fb35385c7121788895ec42d5..a054a74d5e11c209bc2247cb8103cf3b78a1cd7a
expected_branch: codex/phase-a-selection-quotes
dirty_state_allowed_at_start: false
output_mode: review-report
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
review_lane: workflow-code-review
mode: base-subagent
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_value_evidence_selection_delegated_code_review_v0.md
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

Do not push, merge, publish, change packet schema, modify completed production
outputs, rerun extraction/reconciliation, or broaden capture. Patch only these
four files; everything else is read-only and flag-only:

- `[consumer]` `forseti-harness/judgment/phase_a_evidence_selection.py`
- `[tests]` `forseti-harness/tests/unit/test_phase_a_evidence_selection.py`
- `[workflow]` `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`
- `[contract]` `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`

Source-read-only review is insufficient because the load-bearing defect class
is a shared-assumption false green: structurally exact model output can still
place a highly engaged formula/scent post in a value box, invert comparator
direction, overclaim “despite price,” or clip a materially reversing quote.
Tests and implementation can agree on the wrong commercial meaning. The
controller may patch this bounded file set, but the home/Chief Architect must
adjudicate every returned change before it is kept.

## Fitness Reference

Goal: a `value_and_quantity` evidence box should lead with the strongest direct
positive value signals, retain at most one comparable ordinary complaint, and
show exact source words without allowing engagement to manufacture relevance.

Observable success:

- the 599-point Strawberry-duo post remains accounted but is not displayed as
  value evidence because its admitted value-axis meanings are gift-card
  purchase and trial, while its real substance belongs to formula, hydration,
  scent, and a general purchase warning;
- the 204-point quote about cringing at the price and repurchasing Vanilla and
  Vanilla Beige is eligible positive value evidence;
- purchase, repeated ownership, and repurchase without an explicit price
  premise use plain behavior labels, never invented `despite_price` wording;
- quantity efficiency without an explicit price judgment uses “a little
  product goes a long way,” not “benefits justify the price”;
- subject-better and comparator-better value are impossible to encode with the
  same relation/reason pair;
- positive origins fill first, then at most one ordinary counter is selected
  from the primary positive signal's same venue/role/native-metric bucket;
- protected safety/costly rows remain mandatory; origin caps, source grouping,
  creator isolation, exact quote checks, and the full disposition inventory are
  unchanged; and
- the packet remains `phase_a_evidence_packet_v3`; there is no v4, cross-platform
  score, prevalence estimate, or commercial-pull score.

The smallest-complete seam is the existing v3 consumer. Do not propose a packet
version, producer migration, new evidence authority, or semantic replay unless
you return `NEEDS_ARCHITECTURE_PASS` and leave no patch.

## Required Adversarial Attacks

1. `[consumer]` Try to admit formula, scent, hydration, gift-card, trial-only,
   or generic purchase evidence as value through companion meanings. Check both
   high- and low-engagement cases.
2. `[consumer]` Attack relation/reason alignment, especially
   `better_value_than_comparator` versus `comparator_better_value`, and verify
   both schema-time and deterministic finalizer rejection.
3. `[consumer]` Find cases where `*_despite_price` is emitted without an
   explicit price/cost premise, or where `benefits_justify_price` is used for
   quantity efficiency alone.
4. `[consumer]` Attack the ten-origin cap, one-origin/multiple-meaning display,
   protected rows, a protected counter plus an ordinary counter, zero positive
   support, and more protected origins than the cap.
5. `[consumer]` Attack native engagement parsing and ordering with Reddit
   strings, retailer counts/maps, unavailable and malformed values. Confirm no
   raw cross-platform comparison and no silent unsupported shape.
6. `[consumer]` Attack the “one complaint” rule: wrong venue/role/metric bucket,
   lower-engagement complaint winning inside a valid bucket, a counter silently
   displacing the primary positive, and two ordinary counter origins displayed.
7. `[consumer]` Attack creator/customer laundering and ensure creator-authored
   popularity never enters truth support or supplies the ordinary complaint.
8. `[consumer]` Attack quote-label fit. In particular, reproduce a 224-character
   overlength response and a shorter exact substring that clips a trailing
   “the dupes may be better” qualification. Exact substring alone is not a
   semantic-quality pass.
9. `[consumer]` Attack candidate accounting, output order, stale packet/bundle
   hashes, body identity, evidence/source-ref attachment, deterministic
   rehydration, and overwrite guards.
10. `[workflow] [contract]` Compare prose to executable behavior, including
    plain behavior labels, one comparable ordinary counter, protected-row
    exceptions, quote-unavailable behavior, and the explicit no-v4 boundary.
11. `[tests]` Identify any important failure above that shares the production
    implementation's assumption and therefore is not independently falsified.
12. Consider and defend plausible attacks that do not become findings; do not
    silently discard them.

`NEEDS_ARCHITECTURE_PASS` is the escalation valve. On a design-level problem,
stop patching, revert any partial diff, and return findings only.

## Evidence To Confirm, Not Trust

- Exact implementation commit:
  `a054a74d5e11c209bc2247cb8103cf3b78a1cd7a`.
- Real 940-candidate receipt:
  `C:\tmp\forseti-phase-a-selection-full-value-20260818-v3\success_implementation_receipt_v1.json`,
  raw SHA-256
  `25a0c478d63e579f72b667e59812c38ba9a890f983feeb576b70c64b7184c599`.
- Final artifact SHA-256:
  `e97c410f5806d5ee043b8638c9a6974d7111d487fd7ce547d4c9647c7bc526b5`.
- Inventory: 940 candidates, same frozen inventory hash as the baseline; final
  dispositions were 280 support, 323 counter, 319 adjacent, 18 exclude.
- Display: ten truth origins, eleven rows, ten support rows, one ordinary
  complaint origin, seven exact quotes, four typed quote-unavailable rows.
- The 599-point post has two adjacent dispositions and zero displayed rows.
- The 204-point repurchase account is displayed with its full exact quote.
- Focused selection/consumer/semantic suite: 294 passed.
- Full `python -m pytest -q forseti-harness`: exited 0; existing seven skips and
  warnings only.
- Harness-coupling contracts: 18 passed. Placement, map links, prompt output
  mode, and `git diff --check` were green.
- Final production-shaped run: eight provider calls, 711,774 input tokens,
  45,145 output tokens, 756,919 logical tokens, 283,624 ms parallel end-to-end
  provider wall time. Cached input was zero; reasoning output is included in
  output and was not added again.
- Prior baseline: 714,778 logical tokens and 341,151 ms. The new run used 5.90%
  more logical tokens and was 16.86% faster on this workload. Adoption is for
  evidence quality, not token savings; latency is descriptive, not p95.
- Total current-change validation spend across the failed v1 ambiguity run,
  v2 wording run, and final v3 run was 2,175,189 logical tokens. Do not hide or
  reinterpret this as production savings.

Accepted pre-review residuals: four selected rows are visibly
`quote_unavailable` rather than paraphrased; the provider runs are same-vendor;
quote semantic fit still needs quality adjudication beyond deterministic
substring checks; the latency sample is one parallel workload.

## Validation And Return Contract

After any patch, run at minimum:

```powershell
python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py
python -m pytest -q forseti-harness
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --changed --strict --base origin/main
python .agents/hooks/check_repo_map_freshness.py --changed --strict
python .agents/hooks/check_map_links.py --strict
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_harness_coupling.py --base origin/main --strict
git diff --check
```

Write the bound report destination and then run:

```powershell
python .agents/hooks/check_review_output_provenance.py --strict docs/review-outputs/adversarial-artifact-reviews/phase_a_value_evidence_selection_delegated_code_review_v0.md
```

The report must record `reviewed_by`, `authored_by`, the two vendor families,
and whether cross-vendor de-correlation was satisfied. Return findings first
with severity, confidence, exact file/line evidence, source citations,
`minimum_closure_condition`, and `next_authorized_action`; include
`considered_and_defended`, one overall verdict, any per-target sub-verdicts,
the uncommitted unified diff, and residual risk. Prefix findings, citations,
and diff notes with the target labels above.

Do not commit the patch. The diff, citations, and verdict are claims to
adjudicate, not premises to inherit. The home/Chief Architect may accept,
modify, or reject each change and owns all commit, push, PR, merge, publish,
and lifecycle actions after adjudication.
