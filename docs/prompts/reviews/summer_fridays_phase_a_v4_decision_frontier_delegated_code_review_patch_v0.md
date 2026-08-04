# Summer Fridays Phase A v4 delegated code review-and-patch commission

```yaml
retrieval_header_version: 1
artifact_role: operator-courier delegated code review-and-patch prompt
scope: Review and, only where warranted, patch the frozen Phase A v4 decision-maturity implementation.
use_when:
  - Couriering the frozen Phase A v4 implementation to an eligible different-vendor controller with direct repository access.
authority_boundary: retrieval_only
output_mode: paste-ready-chat
edit_permission: patch-only
delivery: operator_courier_only
access: repo
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
target_kind: delegated_code_review_and_patch
required_revision: 29d9783fd9f6749129cab21fa0223b5759f4c9ba
revision_mode: exact
expected_branch: operator_to_fill
review_return_destination: commissioning Chief Architect in chat or the lane PR/comment
```

## Commission

Review the frozen Phase A v4 decision-maturity and decision-frontier change for
false-positive closure, false-negative continuation, legacy-audit regression,
and divergence between the validator, report renderer, tests, and owning
workflow contract. Patch only the four named patch targets when a finding is
real and locally correctable.

Done means the actual frozen diff has been inspected; every material finding is
reported; any warranted patch is confined to the named targets; the named
validation is run with real pass/fail/not-run results; and the return contains
findings, the bounded diff, neutral decision-sufficient citations, a verdict,
and residual risk for Chief Architect adjudication.

The concrete correlated-risk class is multi-axis false closure: the author-built
validator and tests share a mostly single-axis synthetic fixture, so incorrect
query-family scope, material-addition attribution, or per-axis frontier reset
logic could pass the authored tests. Closely inspect that class rather than
assuming green fixtures prove the multi-axis contract.

## Receiver binding — preparation only

```yaml
receiver_binding:
  receiver_class: receiver_to_bind
  binding_state: receiver_to_bind
  launch_checkout: receiver_to_observe
  effective_target_worktree: receiver_to_observe
  required_revision: 29d9783fd9f6749129cab21fa0223b5759f4c9ba
  revision_mode: exact
  capability_proof: receiver_to_observe
  no_concurrent_writer_state: receiver_to_observe
```

This prompt is not dispatch-ready until the operator-selected controller proves
a different upstream vendor/model lineage from OpenAI, direct write access to a
separate clean worktree at the exact required revision, and no concurrent
writer. Do not use the author's dirty acquisition worktree as the review target.
Bind one external-direct-write receiver, record the concrete target and branch,
then load sources. Same-vendor, unknown-lineage, no-repo, self, and
Codex-managed receiver substitutes are ineligible.

## Required operating sources

Read `AGENTS.md`, `.agents/workflow-overlay/README.md`,
`.agents/workflow-overlay/review-lanes.md` (Current Lanes and Review Doctrine),
`.agents/workflow-overlay/delegated-review-patch.md` (When it applies, The loop,
Access selection rule, De-correlation, the code-diff target kind, Adjudication
closeout, and Overlay Interface), and
`.agents/workflow-overlay/prompt-orchestration.md` (Lane-Scoped Delegated Patch
Prompt Default and Review Prompt Defaults). Use the code-review lane
(`workflow-code-review` when resolver-available) as the review method. Read the
actual target diff and target sources before forming findings.

The owning semantic source is:

- `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`

Propagation references to inspect read-only are:

- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
- `forseti/product/spines/commission_signal_board/README.md`
- `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`

## Patch boundary

Only these files are patchable:

- `forseti-harness/runners/run_phase_acquisition_seal_validation.py`
- `forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py`
- `forseti-harness/reports/phase_a_acquisition_yield.py`
- `forseti-harness/tests/unit/test_phase_a_acquisition_yield.py`

All other paths, including the semantic authority and propagation references,
are read-only and flag-only. Do not widen the target set. If the defect is
design-level, requires changing authority, or cannot be fixed wholly inside the
patch boundary, return `NEEDS_ARCHITECTURE_PASS`, stop patching, and quarantine
any partial diff for Chief Architect adjudication.

## Review focus

Verify from code and tests, not prose alone, that:

1. evidence strength is independent from `decision_maturity`;
2. `evidence_supported` cannot pass below strong or above its qualitative
   ceiling, while `route_bounded_source_exhaustion` cannot overclaim beyond
   bounded observation;
3. the four mandatory high-yield family kinds are present and occur before any
   Phase 2 family;
4. every discovery job belongs to exactly one family and family/job/artifact/
   candidate/batch accounting reconciles;
5. useful retained threads are counted and reported but do not reopen an axis
   without a typed material addition;
6. a material addition reopens every affected axis, and no axis can close on a
   frontier that starts before its latest material addition;
7. each material axis closes only on two chronological, later continuation
   families that scope that axis and differ in family kind, exact queries, and
   pinned artifacts;
8. aggregate Phase A maturity cannot pass while a material axis remains open;
9. historical consumer v2 ledgers remain audit-only behind the explicit flag;
   and
10. the human report does not imply prevalence, product-value conclusions, or
    zero useful yield when the ledger proves only decision maturity.

Include at least one genuinely multi-axis adversarial fixture or equivalent
direct proof. Try to falsify axis-local reopening, cross-axis material
attribution, and two-family closure; do not add tests merely to mirror the
implementation.

## Validation

Run from the clean bound worktree using PowerShell syntax:

```powershell
python -m py_compile forseti-harness/runners/run_phase_acquisition_seal_validation.py forseti-harness/reports/phase_a_acquisition_yield.py
python -m pytest forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py forseti-harness/tests/unit/test_phase_a_acquisition_yield.py -q
Push-Location forseti-harness
python -m pytest tests/contract/test_data_lake_inventory_gate.py tests/contract/test_policy_module_version_pins.py -q
Pop-Location
git diff --check
```

Report every command, exit code, and whether it ran before or after the patch.
Failures remain failures. The author-side full harness suite was attempted twice
and timed out at 62.6 seconds and 184 seconds without a reported test failure;
do not relabel those attempts as passes. A broad rerun is optional; if not run
or if it times out, report that exactly and leave full-suite authority to CI.

## Self-contained delegate constants

`environment_baseline`: Windows host, PowerShell-first: use PowerShell syntax
for shell/test commands; use absolute paths resolvable from any cwd; invoke
`python`, never `python3`; do not pass Windows drive-letter paths or heredocs
through bash.

`lifecycle_hard_stop`: A delegate or receiver does not commit, push, open or
update a PR, merge, stash, reset, clean the worktree, or run repository-hygiene
actions unless the commission explicitly grants that action.

`decorrelation_commission`: `delivery: operator_courier_only` · `access: repo` ·
`delegate_eligibility: different_vendor_lineage_with_direct_repo_access`;
same-vendor, unknown-lineage, no-repo, self, and Codex-managed controller
substitutes are invalid; a manager-prefixed target path is neutral; if no
eligible controller is available the prompt remains unexecuted.

## Required return

Return findings first under the mechanics owned by
`.agents/workflow-overlay/review-lanes.md`, including
`considered_and_defended`. For every actionable finding include severity,
confidence, exact `file:line` evidence, the violated contract or observable
failure, and `minimum_closure_condition`. Then return:

```yaml
status: complete | blocked | needs_architecture_pass
reviewed_revision: 29d9783fd9f6749129cab21fa0223b5759f4c9ba
reviewed_by_vendor: <actual upstream vendor>
authored_by_vendor: OpenAI
verdict: NO_PATCH | PATCHED | NEEDS_ARCHITECTURE_PASS | BLOCKED
patched_files: []
validation:
  - command: <exact command>
    result: pass | fail | not_run
    exit_code: <integer or null>
residual_risk:
  - <specific residual or none>
```

Include the actual bounded unified diff when patched, with neutral
decision-sufficient source citations for each change. The return is decision
input only. The commissioning Chief Architect must adjudicate every finding,
diff hunk, verdict, and residual before any change is kept, follow
`.agents/workflow-overlay/delegated-review-patch.md`'s same-turn material
continuation/closeout rule, and retain all commit/push/PR/merge authority.
