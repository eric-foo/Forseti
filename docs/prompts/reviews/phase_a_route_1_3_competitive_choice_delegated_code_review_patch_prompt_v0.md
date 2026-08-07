# Phase A Route 1.3 Competitive-Choice Delegated Code Review + Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Review prompt artifact (delegated code review-and-patch commission, repo access mode)
scope: >
  Paste-ready operator-courier commission for a different-vendor, repo-mode
  review and bounded patch of the Phase A route 1.3 competitive-choice,
  public-identity, semantic-value, and two-scope competitor-retailer change.
use_when:
  - Couriering the success-implement review for implementation commit 83713ffa37cb8e77d590dbef59d3746a22cb9d51.
  - Adjudicating whether route 1.3 stays evidence-only and fail-closed across code, tests, authority, prompt, playbook, and handoff.
authority_boundary: retrieval_only
stale_if:
  - Commit 83713ffa37cb8e77d590dbef59d3746a22cb9d51 is not an ancestor of the target branch.
  - Any named target changes before the delegate binds the reviewed revision.
  - The receiver lacks different-vendor lineage or direct repository write access.
```

## Prompt Preflight

```yaml
output_mode: paste-ready-chat
edit_permission: docs-write
targets:
  - docs/prompts/reviews/phase_a_route_1_3_competitive_choice_delegated_code_review_patch_prompt_v0.md
branch: codex/phase-a-competitive-choice-20260807
input_prompt_source: docs/prompts/reviews/phase_a_route_1_3_competitive_choice_delegated_code_review_patch_prompt_v0.md
output_artifact: operator-couriered chat return; no durable delegate report
review: findings-first code review with bounded patch; no runtime-model recommendation, ranking, or implication
doctrine_change: none; this prompt reviews the already-authored route change
```

## Paste-Ready Commission

````markdown
You are an external controller receiving a REPO-MODE DELEGATED CODE REVIEW AND
BOUNDED PATCH commission. This is preparation-only until the receiver binding
below is observed and the who-constraint passes.

### Goal and success signal

Review the Phase A route 1.3 implementation at
`83713ffa37cb8e77d590dbef59d3746a22cb9d51` for the material failure class that
can survive its own tests: the authority, execution prompt, seal schema,
validator, and author-built fixtures may all share the same mistaken assumption
and therefore agree while either (a) a final competitor label still substitutes
for evidence of why customers choose, (b) aliased public actors receive false
independence credit, (c) semantic price/value language escapes the required
two-product context, or (d) actor-strategy positioning is silently treated as
customer evidence.

Done means you have inspected the whole named diff against its owning sources,
patched only accepted material defects inside the named set, run the named
validation, and returned findings, the actual bounded diff, neutral citations,
verdict, and residual risk. This remains Phase A evidence acquisition: no
recommendation, market conclusion, competitor-response strategy, or Deliver
work may be introduced.

### Receiver binding and who-constraint

```yaml
receiver_binding:
  receiver_class: receiver_to_bind
  preparation_only_until_bound: true
  delivery: operator_courier_only
  access: repo
  repository: C:\Users\vmon7\Desktop\projects\orca
  effective_target_worktree: C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\forseti-phase-a-choice-20260807
  target_branch: codex/phase-a-competitive-choice-20260807
  required_revision: 83713ffa37cb8e77d590dbef59d3746a22cb9d51
  revision_mode: ancestor
  receiver_to_observe:
    - launch_root
    - resolved_target_root
    - target_branch_and_head
    - required_revision_is_ancestor
    - target_dirty_state
    - direct_write_capability_to_named_targets
    - no_concurrent_writer
author_vendor: OpenAI
delegate_vendor: operator_to_fill
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
```

Bind only if the upstream model vendor differs from OpenAI, its lineage is
known, it can directly read and patch the target worktree, the required revision
is an ancestor of the checked target head, the worktree is clean, and no other
writer is active. If any condition fails, return `BLOCKED_RECEIVER_BINDING`
with the observed mismatch and stop. Same-vendor, unknown-lineage, no-repo,
self, and Codex-managed substitutes are invalid.

Environment baseline: Windows host, PowerShell-first: use PowerShell syntax for
shell/test commands; use absolute paths resolvable from any cwd; invoke
`python`, never `python3`; do not pass Windows drive-letter paths or heredocs
through bash.

Lifecycle hard stop: A delegate or receiver does not commit, push, open or
update a PR, merge, stash, reset, clean the worktree, or run
repository-hygiene actions unless the commission explicitly grants that action.

De-correlation commission: `delivery: operator_courier_only` · `access: repo` ·
`delegate_eligibility: different_vendor_lineage_with_direct_repo_access`;
same-vendor, unknown-lineage, no-repo, self, and Codex-managed controller
substitutes are invalid; a manager-prefixed target path is neutral; if no
eligible controller is available the prompt remains unexecuted.

### Intake and review method

First read `AGENTS.md` and `.agents/workflow-overlay/README.md`, then the
targeted sections **When it applies**, **The loop**, **De-correlation**, and
**Code-diff target kind — delegated_code_review_and_patch** in
`.agents/workflow-overlay/delegated-review-patch.md`. Use the code-review lane
owned by `.agents/workflow-overlay/review-lanes.md`; review findings-first.
Perform the binding intake before broader source loading. By the second
latency-bearing tool call, inspect the actual diff for
`origin/main..83713ffa37cb8e77d590dbef59d3746a22cb9d51`.

Owning sources to judge against:

- `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
- `.agents/workflow-overlay/source-of-truth.md` — doctrine propagation contract
- the historical Summer Fridays artifacts cited in the playbook example, for
  factual attribution only; never patch historical research evidence

### Named patchable target set

Only these files are writable:

1. `forseti-harness/runners/run_phase_acquisition_seal_validation.py`
2. `forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py`
3. `forseti/product/spines/commission_signal_board/README.md`
4. `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
5. `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
6. `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
7. `docs/prompts/handoffs/phase_acquisition_validator_malformed_enum_hardening_handoff_20260807_v0.md`

Everything else is read-only/flag-only, including this courier prompt,
historical Summer Fridays research, generated/hash-pinned artifacts, overlay
authority, and repository maps. Do not widen the set.

### Review focus

Review the whole named diff, not only likely defects:

- Phase order stays `SERP Phase 1 -> pre-fanout qualification -> CO1/CO2/CO3
  fan-out -> post-return Phase 2 -> acquisition seal`; competitor status is
  sufficiently confirmed before core fan-out, while later role adjudication is
  secondary to axis-level evidence.
- `competitive_choice_explanation` is required for every material route-1.3
  candidate; promoted rows require observed, sourced shared-axis findings; weak
  rows can remain partial/unresolved without fake completion; older route 1.2
  seals owe none of the new fields.
- The public-identity check is small but honest: normalized duplicate keys and
  possible/confirmed/unavailable overlap cannot manufacture two origins; valid
  route-1.2 behavior remains symmetric; malformed values fail visibly rather
  than crashing or passing.
- Retailer acquisition has exactly two scopes inside one Phase A: full selected
  comparable-retailer evidence for the exact competing product, plus a bounded
  relevant-franchise map. It does not create a percentage quota, second Phase
  A, or default full rival-company corpus.
- Product choice, franchise importance, and observable brand positioning join
  one evidence model without collapsing source roles. Owned/ad/campaign
  positioning is context, never customer-choice proof.
- The final semantic language-model pass catches price/value concepts outside
  tokenized axis IDs but cannot invent normalization, currency conversion, or
  equal-value claims.
- The Summer Fridays example accurately reflects its cited historical files:
  e.l.f./Rhode Phase 1 selection, the old Phase 2 watch-only result, the named
  customer comments, price/size facts, and focal retailer counts. Examples do
  not become current competitor verdicts or representative sentiment.
- The malformed-enum handoff remains a separate mechanical implementation
  commission and does not silently perform or authorize schema changes.
- Diff scope is the smallest complete route change; reject extra ceremony,
  duplicate authority, or fields that do not catch the named failure classes.

Patch the smallest complete correction for any accepted material finding. If
the problem is design-level, return `NEEDS_ARCHITECTURE_PASS`, stop patching,
and quarantine any partial diff.

### Validation

Run and report observed output for:

```powershell
python -m pytest forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m compileall -q forseti-harness/runners/run_phase_acquisition_seal_validation.py
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
git diff --check
```

Each check can pass, fail, be blocked, or be not run. Do not hide failures or
claim a check you did not observe.

### Return contract

Return, in order:

1. `review_summary` with reviewed revision, receiver/model lineage if
   disclosable, access mode, and target-state binding.
2. Findings ordered by materiality: title, priority, file/line, evidence,
   impact, and minimum closure condition. Say explicitly when there are no
   material findings.
3. The bounded diff actually left in the target worktree, with neutral,
   decision-sufficient source citations for each change. If no patch was
   needed, say `NO_PATCH`.
4. Validation commands and observed results.
5. Verdict: `clean_for_architect_adjudication | material_issue_remaining |
   NEEDS_ARCHITECTURE_PASS`, plus residual-risk note.

Your findings, diff, citations, test claims, and verdict are decision input
only. The commissioning Chief Architect must independently adjudicate each as
accept/modify/reject/defer/escalate before anything is kept, close any
self-closable issue in the same turn, rerun validation, and keep lifecycle work
as one later land step. You authorize no readiness, approval, merge, or extra
scope.
````
