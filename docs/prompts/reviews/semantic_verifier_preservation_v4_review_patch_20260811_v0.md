# Delegated review-and-patch — semantic verifier preservation v4

```yaml
retrieval_header_version: 1
artifact_role: Operator-couriered delegated code review-and-patch commission
scope: >
  Different-vendor review and bounded patch hardening of the semantic verifier
  preservation v4 implementation frozen at the required revision below.
use_when:
  - Couriering this exact commission to one eligible external direct-write receiver.
authority_boundary: retrieval_only
```

This prompt is preparation-only until the operator-selected receiver proves the
binding below. It authorizes no Codex-managed or same-vendor substitute.

## Commission

```yaml
output_mode: chat-only
write_destination: named_patch_scope_only
template_kind: none
edit_permission: patch-only
delivery: operator_courier_only
access: repo
target_kind: delegated_code_review_and_patch
review_method: workflow-code-review
author_vendor: OpenAI
delegate_vendor: operator_to_fill
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.

receiver_binding:
  receiver_class: receiver_to_bind
  required_class: external_direct_write
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-semantic-verifier-preservation-v4-review-20260811
  branch: codex/semantic-verifier-preservation-v4-review-target
  remote_source_ref: codex/semantic-verifier-preservation-v4
  required_revision: 87123330c60c0fdcc772739688e44a14609c939b
  revision_mode: ancestor
  reviewed_revision: receiver_to_observe
  clean_at_bind: required
  direct_write_capability: receiver_to_observe
  no_concurrent_writer: required
  allowed_dirty_state_after_bind: controller_owned_changes_inside_named_patch_scope_only

environment_baseline: >
  Windows host, PowerShell-first: use PowerShell syntax for shell/test commands;
  use absolute paths resolvable from any cwd; invoke python, never python3; do
  not pass Windows drive-letter paths or heredocs through bash.
lifecycle_hard_stop: >
  A delegate or receiver does not commit, push, open or update a PR, merge,
  stash, reset, clean the worktree, or run repository-hygiene actions unless
  the commission explicitly grants that action.
decorrelation_commission: >
  delivery: operator_courier_only · access: repo · delegate_eligibility:
  different_vendor_lineage_with_direct_repo_access; same-vendor,
  unknown-lineage, no-repo, self, and Codex-managed controller substitutes are
  invalid; a manager-prefixed target path is neutral; if no eligible controller
  is available the prompt remains unexecuted.
```

Do not begin source loading until the binding is proven. As the first action,
record the observed delegate vendor lineage, launch checkout, effective target,
branch, clean state, required-revision ancestry, exact reviewed `HEAD`, direct
write capability, and absence of a concurrent writer. A launch-root mismatch
alone is not a blocker. Once bound, keep the reviewed snapshot immutable except
for your own commissioned edits.

## Goal and done condition

Review the full `origin/main...reviewed_revision` implementation diff and its
real operating seams, then patch only confirmed material defects inside the
named scope. Done means the verifier preserves supported proposed evidence while
correcting only source-proven defects; semantic boundary rules do not erase or
invent meaning; agreement remains usable support without becoming a new
first-hand independent origin; historical semantic methods remain exact; stale
verifier authority fails closed; and all named focused checks report their real
result. A clean review does not authorize a full-corpus run or readiness claim.

The concrete reason ordinary correlated validation is insufficient is that the
author, method text, tests, and bounded ruler may share the same interpretation.
Such agreement can still admit a destructive whole-row rewrite, count
`personal_agreement` as independent experience through another path, or preserve
the wrong product/axis binding while every authored test stays green.

## Authority and source intake

Read, in this order:

1. `AGENTS.md` and `.agents/workflow-overlay/README.md`.
2. `.agents/workflow-overlay/delegated-review-patch.md`: **When it applies**,
   **The loop**, **Access selection rule**, **De-correlation**, the code-diff
   target kind, and **Adjudication closeout**.
3. `.agents/workflow-overlay/review-lanes.md` Review Doctrine and the installed
   `workflow-code-review` instructions. This is code review, not adversarial
   artifact review.
4. The actual diff and every named patchable file. Treat the implementation,
   tests, contract, workflow note, dogfood outputs, and this prompt as claims to
   verify rather than premises to inherit.

This prompt is run-authoritative. It is read-only and is not in the patch scope.
External workflow sources and `jb` are not Forseti authority.

## Named patch scope

Only these files may be changed:

1. `forseti-harness/judgment/semantic_evidence_integration.py`
2. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
3. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
4. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else is read-only and flag-only, including this prompt, generated or
hash-pinned evidence, external dogfood artifacts, canonical captures, and
protected paths. Do not widen scope. If a material defect requires another file
or a design decision, return `NEEDS_ARCHITECTURE_PASS` or the exact bounded
route-out; quarantine any partial design-level patch.

## Required attacks

Coverage-first, inspect the entire target behavior, not only the new lines. At
minimum, try to falsify each of these:

- a verifier-v3 manifest or receipt is accepted as current verifier-v4 authority;
- any historical semantic method, route-1.6 dogfood, bundle, prompt, compilation,
  or view changes when the new rules should not apply;
- `personal_agreement` gains independent-origin credit through reconciliation,
  finalization, mixed support, duplicate evidence refs, or a non-v7 path;
- replacement wording permits a verifier to delete a supported proposed
  meaning, axis, product, condition, posture, direction, or provenance field;
- preservation wording instead forces a union and retains unsupported meanings;
- generic ownership is over-axed as shade, or incidental past sale language is
  over-axed as value;
- named-shade/all-shade behavior or explicitly price-conditioned intended
  purchase loses its supported shade/value axis;
- drying/non-drying is misrouted to reaction, while peeling/burning/irritation/
  breakout/damage is incorrectly moved out of reaction;
- nearby sensitivity is invented as a product reaction or a hydration condition;
- comparator-only or adjacent-product text is bound to the target product;
- string-derived method construction can drift or silently misbind when its v3
  base changes;
- the 50,000-byte verifier ceiling fails a single legitimate row or installs an
  unnecessary recurring prompt-cost burden; and
- contract or workflow claims are stronger than what code and tests enforce.

Use the bounded Summer Fridays evidence to test semantics, not to tune around a
single gold row. The remaining observed failures are material review input:

- primary omitted the explicit “less deeply moisturizing than Lanolips” meaning;
- primary invented a separate product-linked sensitivity reaction, yielding
  eight units where the frozen ruler allowed four through seven;
- cold repeat remained inconsistent on three of seven cases; and
- the evaluator still reports `PREPARATION_RECEIPT_MISMATCH` even though the
  rebound receipt and stored spec expose the same `spec_sha256`. Do not conceal,
  relabel, or patch around that independent mechanical residual outside scope.

## Read-only real-check lineage

Inspect, but never modify or regenerate, the bounded run at:

`C:\tmp\forseti-summer-fridays-semantic-verifier-v4-dogfood-20260811-v1`

Re-derive rather than copy these claimed anchors where the files are available:

- 103 verified rows: 86 accept, 17 replace, 0 unresolved;
- final verifier prompts: 2 semantic-core, 3 cold-repeat, 19 production;
  maximum sizes 47,335, 47,716, and 49,900 bytes respectively;
- semantic-core compilation SHA-256
  `a4a56aaf2400ffe670cf1f1d45f1569a22ad3bcbacfbd25eed6a8a68e8e09a47`;
- production compilation SHA-256
  `d85142112dc2850cf98fd39278046a9efc7a59f3ac5ea7515a6cdf78ba9f046e`;
- blind adjudication: 15/17 gold, 7/7 relations, 4/7 cold consistency,
  10/10 density, status `SEMANTIC_CALIBRATION_FAIL`;
- adjudication SHA-256
  `70b2c42d54882a1744bc2138e9105b97e427400106e1c5b1eddda0a64e3c7bd3`;
- evaluator report SHA-256
  `77f81bcd069f80108b497392fcbcea2a94ab33649d51cdce2a7466daf0b00774`.

If the external lineage is absent, mark each real check `not_run`; do not infer
it from repository prose. No finding may turn the failed bounded calibration
into a pass by weakening the ruler or suppressing failure visibility.

## Patch and validation rules

Patch a finding only when it is confirmed, material, inside the named scope, and
the smallest complete closure. Add focused regression coverage for every code
change. Do not add a new phase, schema, API/model call, broad abstraction, full
corpus execution, or unrelated cleanup. Preserve the user's explicit validation
economy: do **not** run the full unit suite.

Run separately and report exact outputs or `blocked`/`not_run`:

1. `python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/tests/unit/test_semantic_evidence_integration.py`
2. `python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py -q`
3. `python .agents/hooks/check_retrieval_header.py --changed --strict`
4. `python .agents/hooks/check_placement.py --strict --base origin/main`
5. `python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main`
6. `python .agents/hooks/check_handoff_pointers.py --strict --base origin/main`
7. `python .agents/hooks/check_review_routing.py --strict --base origin/main`
8. `python .agents/hooks/check_map_links.py --strict --base origin/main`
9. `git diff --check`

Never mask a failure or substitute an easier check. Do not alter historical
seals or the external dogfood root.

## Return contract

Return in chat:

1. receiver binding, lineage, required and reviewed revisions;
2. severity-ordered findings with decisive evidence, impact, minimum closure,
   patch status, and next authorized action;
3. `considered_and_defended` for required attacks that held;
4. the exact bounded diff, with neutral source citations for every change;
5. every validation command and observed result, including every real check
   that was unavailable;
6. one verdict: `clean_for_architect_adjudication`,
   `patched_for_architect_adjudication`, or `NEEDS_ARCHITECTURE_PASS`; and
7. residual risk, including the non-independent sliver of delegate-authored
   lines and the truthful full-corpus readiness boundary.

The return is decision input only. It asserts no approval, `PASS`, readiness,
seal eligibility, full-corpus authorization, merge authority, or mandatory
remediation. The home Chief Architect must adjudicate every finding, changed
line, verdict, and residual before anything is kept; close self-closable issues
in that same adjudication turn, route only genuinely external/design blockers,
and batch lifecycle work into one final land step once clean.
