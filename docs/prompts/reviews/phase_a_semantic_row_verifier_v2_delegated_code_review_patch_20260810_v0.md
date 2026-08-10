---
retrieval_header_version: 1
artifact_role: Operator-couriered delegated code review-and-patch commission
scope: Phase A whole-row verifier-v2 meaning coverage and customer-attribute boundaries
use_when:
  - Couriering the frozen verifier-v2 implementation to an eligible different-vendor repository controller.
authority_boundary: retrieval_only
---

# Delegated code review and patch: Phase A whole-row verifier v2

This prompt remains preparation-only until an eligible external receiver proves
the binding below. Do not inspect target sources before the binding passes.

```yaml
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
delivery: operator_courier_only
access: repo
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
output_mode: chat-only
output_destination: courier conversation
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
template_kind: none
doctrine_change: none
review_routing_status: adjudicated_patched
receiver_binding:
  receiver_class: receiver_to_bind
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-semantic-parent-coverage-v7-20260810
  required_revision: 3dc4fbb4bae6f482b38bf27facef349a134109f8
  revision_mode: ancestor
  clean_at_bind: required
  direct_write_capability: receiver_to_verify
  no_concurrent_writer: receiver_to_verify
```

## Goal and success signal

Review `origin/main...reviewed_revision` and patch confirmed defects only inside
the named set. Success means the existing whole-row verification pass reliably:

- recovers every material standalone meaning before checking fields;
- resolves an elliptical short answer from supplied parent context without
  erasing a simultaneous explanation, comparison, preference, or qualification;
- keeps axes clause-local;
- treats a customer attribute as a result condition only when it states or
  unambiguously entails the same baseline, or the source explicitly scopes the
  result to it; and
- retains a relevant caveat or reaction as a separate meaning instead of either
  deleting it or attaching it to an unrelated result.

The smallest-complete boundary is load-bearing. This change must not add a
response field, parser, phrase table, product-specific rule, provider API,
mandatory second verifier, conclusion, recommendation, or full-corpus resume.

## Binding and operating instructions

Before review:

1. Record the delegate vendor and stop as ineligible if it is OpenAI, unknown,
   undisclosed, lacks direct repository access, or cannot patch the bound root.
2. Read `AGENTS.md`, `.agents/workflow-overlay/README.md`, the code-diff target
   section of `.agents/workflow-overlay/delegated-review-patch.md`, and the code
   review lane in `.agents/workflow-overlay/review-lanes.md`.
3. Verify the worktree exists and is clean; verify
   `git merge-base --is-ancestor 3dc4fbb4bae6f482b38bf27facef349a134109f8 HEAD`.
4. Prove direct write capability without a synthetic mutation when ordinary
   patching will prove it, confirm no concurrent writer, and record current
   `HEAD` as immutable `reviewed_revision`. If the branch advanced, use a
   separate clean worktree at that captured revision.

Delegate-facing environment baseline: Windows host, PowerShell-first; use
PowerShell syntax, absolute paths where cwd is ambiguous, and `python`, never
`python3`; do not pass drive-letter paths or heredocs through bash.

Lifecycle hard stop: do not commit, push, open or update a PR, merge, stash,
reset, clean the worktree, or run repository-hygiene actions.

De-correlation commission: this is operator-courier-only with direct repository
access. The delegate must have a different upstream vendor/model lineage from
the OpenAI author. Same-vendor, unknown-lineage, no-repo, self, and Codex-managed
controller substitutes are invalid. If no eligible controller is available,
leave the commission unexecuted.

## Named patchable set

Patch only:

1. `forseti-harness/judgment/semantic_evidence_integration.py`
2. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
3. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
4. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else, including this prompt and external calibration artifacts, is
read-only/flag-only. A required schema, architecture, or out-of-set change must
return `NEEDS_ARCHITECTURE_PASS`, with no partial design-level patch.

## Required attacks

- Reconstruct the actual verifier-v2 prompt and challenge the execution order:
  inventory standalone meanings, resolve ellipsis, map meanings to units, then
  check fields. Confirm this is operational rather than documentation-only.
- Attack omission: a leading answer about value must not disappear merely
  because later text compares the item with a gloss, states a hydration result,
  names a favorite shade, or gives an overall preference.
- Attack cancellation: later context may narrow an earlier judgment, but may not
  silently withdraw it. Conversely, do not preserve a judgment the source
  explicitly corrects or retracts.
- Attack attribute overbinding and erasure with fresh examples. Dry/dehydrated
  may establish a moisture baseline; sensitivity alone does not. A product-linked
  sensitivity/reaction statement may still be valuable separate evidence. Check
  analogous non-lip scenarios so the rule is not secretly product-specific.
- Attack axis leakage: nearby hydration, shade, value, quantity, or product text
  must not donate its axis to a separate overall preference, ownership,
  repurchase, switching, or comparison statement.
- Attack false completeness: one unit on the same product, axis, or topic must
  not stand in for a materially different meaning.
- Attack historical binding: verifier-v1 artifacts must remain distinct and may
  not be silently accepted or relabelled as v2. Verify method text/hash binding.
- Attack packing and ceremony cost. Reconstruct the preserved 91-row preparation
  when the external root is available and confirm all prompts remain within the
  unchanged 90,000-byte ceiling. Do not solve overflow by raising the ceiling or
  adding another mandatory pass.
- Inspect tests for overfitting. The durable method must encode general semantic
  boundaries, not Summer Fridays, Vanilla Beige, `$24`, balm, or gloss phrases.
- Check contract v24 and the workflow record against code and real artifacts.
  Preserve the explicit nonclaims: no final-method 91-row submission proof,
  semantic readiness, full-corpus resume, prevalence, Deliver, or seal.

## External dogfood lineage

Read-only roots, if present:

- initial 91-row pass:
  `C:\tmp\forseti-summer-fridays-row-verification-v2-20260810-v0`
- final method and targeted three-reader proof:
  `C:\tmp\forseti-summer-fridays-row-verification-v2-20260810-v5`

Re-derive material counts, prompt sizes, method hash, row order, replacement
shape, statements, axes, and conditions from primary artifacts. If a root is
unavailable, mark each dependent claim `not run`; do not infer it from prose.

## Validation

Run focused checks only; the owner explicitly excludes the full unit suite from
this commission. Report every command separately after any patch:

```powershell
python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py
python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_a_semantic_run.py -q
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

For every patch, add or strengthen a focused regression that fails on the
frozen implementation for the intended reason and passes afterward. Surface
failures and not-run checks; never convert them into a clean result.

## Return contract

Return, in order:

1. receiver binding, author/delegate lineage, required and reviewed revisions;
2. severity-ordered findings with confidence, decisive evidence, minimum
   closure condition, and next authorized action;
3. `considered_and_defended` candidates;
4. the exact bounded diff with neutral source citations for each change;
5. every validation command and observed result, plus dogfood checks;
6. one of `patched_for_architect_adjudication`,
   `clean_for_architect_adjudication`, or `NEEDS_ARCHITECTURE_PASS`; and
7. residual risk, including the non-independent delegate-authored patch lines.

The return is decision input only. The home Chief Architect adjudicates every
finding and changed line before anything is kept. Nothing authorizes lifecycle
action.
