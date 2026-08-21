# Phase A Point-Pack v6 — Delegated Code Review-and-Patch

```yaml
retrieval_header_version: 1
artifact_role: Operator-couriered delegated code review-and-patch prompt
scope: >
  Cross-vendor adversarial review and bounded patching of the Phase A v6
  point-pack origin cap, disclosure, and selected-row confirmation change.
use_when:
  - Couriering the frozen Phase A point-pack v6 implementation to an eligible different-vendor reviewer with direct repository access.
authority_boundary: retrieval_only
```

```yaml
output_mode: paste-ready-chat
delivery: operator_courier_only
access: repo
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
preparation_state: receiver_to_bind
```

You are receiving one bounded `delegated_code_review_and_patch` commission.
Do not begin source review until the receiver binding below is verified. If you
cannot establish different-vendor lineage and direct repository access, return
`BLOCKED_INELIGIBLE_DELEGATE` without reviewing or patching.

## Goal and success bar

Goal: make each new Phase A presentation artifact one bounded evidence-point
pack that defaults to at most 13 distinct customer truth origins, truthfully
discloses the full candidate-to-display funnel, and cannot finalize until a
separate hidden-label pass confirms every displayed relation.

Done looks like:

- the default cap is 13 truth origins per bounded point, while creator influence remains separate and protected evidence still fails visibly if the cap is insufficient;
- the final artifact distinguishes candidate semantic rows, distinct evidence items, candidate truth origins, displayed rows, displayed truth origins, displayed origins by relation, and displayed creator influence;
- the confirmation workload receives no first-pass relation, reason code, display label, engagement, selection priority, or quote-writing task;
- missing, duplicate, foreign, reordered, stale-bound, or disagreeing confirmation rows fail at their intended boundary;
- exact-quote extraction remains behaviorally separate and historical v1/v3/v4/v5 artifacts still replay under their stamped contracts;
- no broad axis can be mislabeled as a sufficiently bounded point merely because the runtime field is named `bounded_claim` or `point_id`;
- validation demonstrates the owner-visible behavior rather than only schema consistency.

The two highest-risk false greens are:

1. author code and author tests may share the assumption that an operator's `bounded_claim` is semantically one point, allowing an axis-wide claim to pass and receive point-pack disclosure;
2. a second response may mechanically agree with the first while not being meaningfully independent or may reuse enough leaked first-pass state that `passed` overstates what was checked.

Attack those first. Also attack count definitions, v4/v5 compatibility, quote/confirmation separation, confirmation-manifest binding, runner no-overwrite behavior, explicit-cap exceptions, creator/customer separation, protected evidence, and any wrong-cause test.

## Receiver binding and target

```yaml
receiver_binding:
  receiver_class: receiver_to_bind
  binding_state: receiver_to_bind
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\Users\vmon7\.codex\worktrees\e4f8\orca
  managed_starting_ref: not_applicable
  required_revision: 1aa3607c
  revision_mode: ancestor
  capability_proof: receiver_to_observe
  no_concurrent_writer_state: receiver_to_observe
branch: codex/phase-a-hydration-pack-cap-pilot
implementation_parent: 887e78de11181d814bc7b4a200d472fffe1bd298
implementation_commit: 1aa3607c
clean_at_bind_required: true
```

Verify that `1aa3607c` is an ancestor of the clean current `HEAD`, record that
current `HEAD` as `reviewed_revision`, and review the exact implementation diff
`887e78de11181d814bc7b4a200d472fffe1bd298..1aa3607c`. The later courier-prompt
commit is transport only and is outside the implementation review target.

Patch authority is limited exactly to these five files:

- `forseti-harness/judgment/phase_a_evidence_selection.py`
- `forseti-harness/runners/run_semantic_evidence_integration.py`
- `forseti-harness/tests/unit/test_phase_a_evidence_selection.py`
- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else is read-only and flag-only. Do not modify completed production
outputs or the data lake. Do not perform new extraction, semantic replay, broad
refactoring, packet v4 work, engagement scoring, prevalence estimation, or
unrelated cleanup.

## Required authority and method

Read `AGENTS.md` and `.agents/workflow-overlay/README.md` first. Then read:

- `.agents/workflow-overlay/delegated-review-patch.md`: **When it applies**, **The loop**, **Access selection rule**, **De-correlation**, **Code-diff target kind**, and **Adjudication closeout**;
- `.agents/workflow-overlay/review-lanes.md`: code-review method and rules;
- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`;
- the five named target files and the exact implementation diff.

Invoke `workflow-code-review` as the review method after source readiness. This
is full-target discovery plus bounded patch authorship, not a review of only the
changed lines. Report every finding; do not silently discard low-confidence or
low-severity failure modes. List defeated candidates under
`considered_and_defended`.

Delegate-facing constants, restated faithfully from
`docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`:

- `environment_baseline`: Windows host, PowerShell-first: use PowerShell syntax for shell/test commands; use absolute paths resolvable from any cwd; invoke `python`, never `python3`; do not pass Windows drive-letter paths or heredocs through bash.
- `lifecycle_hard_stop`: A delegate or receiver does not commit, push, open or update a PR, merge, stash, reset, clean the worktree, or run repository-hygiene actions unless the commission explicitly grants that action.
- `decorrelation_commission`: `delivery: operator_courier_only` · `access: repo` · `delegate_eligibility: different_vendor_lineage_with_direct_repo_access`; same-vendor, unknown-lineage, no-repo, self, and Codex-managed controller substitutes are invalid; a manager-prefixed target path is neutral; if no eligible controller is available the prompt remains unexecuted.

## Patch and validation contract

Patch only findings whose smallest complete closure sits inside the named file
set. Preserve failure visibility; do not weaken a gate to make tests pass. If a
finding is design-level or requires files outside scope, return
`NEEDS_ARCHITECTURE_PASS`, quarantine any partial design patch, and stop.

Run and report, in order:

1. the selected-row confirmation falsifiers, including one seeded support/counter flip, incomplete result set, stale/rebound manifest, and quote-task separation;
2. `python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py`;
3. `python -m py_compile forseti-harness/judgment/phase_a_evidence_selection.py forseti-harness/runners/run_semantic_evidence_integration.py`;
4. `python -m pytest -q forseti-harness`;
5. `python .agents/hooks/check_harness_coupling.py --strict`;
6. `python .agents/hooks/header_index.py --strict`;
7. `python .agents/hooks/check_map_links.py --strict`;
8. `python .agents/hooks/check_placement.py --changed --strict --base origin/main`;
9. `python .agents/hooks/check_hash_pin_freshness.py --strict`;
10. `python .agents/hooks/check_shared_helper_duplication.py --strict`;
11. `git diff --check` and an exact changed-file check against the commissioned set.

If a command cannot run, report it as not run with the concrete reason. A
baseline failure cannot excuse a candidate failure.

The home dogfood receipt is
`C:\tmp\forseti-phase-a-point-pack-v6-dogfood-20260821-v0\dogfood_receipt_v1.json`
with raw SHA-256
`6113212dfd6d3b755e3d382dd7d00536c92719e797a48d1263557a13a9bfe8ea`.
Treat it as evidence, not authority. It records a same-vendor, different-model-
family confirmation over the historical 15-origin broad hydration artifact;
it does not prove cross-vendor confirmation or the new 13-origin point default.

## Return

Return:

1. receiver binding, author vendor, delegate vendor, required revision, and reviewed revision;
2. findings first, with severity, confidence, evidence, minimum closure condition, and next authorized action;
3. `considered_and_defended`;
4. the bounded patch diff and neutral source citations for every change;
5. exact validation commands, exit results, and any not-run checks;
6. verdict: `PATCHED`, `NO_PATCH_NEEDED`, `BLOCKED_INELIGIBLE_DELEGATE`, or `NEEDS_ARCHITECTURE_PASS`;
7. residual risks, including the non-independent sliver in the delegate's own edited lines;
8. a reminder that the commissioning Chief Architect must adjudicate every finding, patch, verdict, and residual under `.agents/workflow-overlay/delegated-review-patch.md` **Adjudication closeout** before any returned change is kept.

Do not commit, push, open/update a PR, merge, stash, reset, clean, or perform
repository hygiene.
