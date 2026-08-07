# Intelligence Claim Support + Phase A Route 1.3 Delegated Code Review + Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Review prompt artifact (delegated code review-and-patch commission, repo access mode)
scope: >
  Paste-ready operator-courier commission for a different-vendor, repo-mode
  review and bounded patch of the cycle-wide intelligence claim-support
  contract and its Phase A route 1.3 competitive-choice consumer.
use_when:
  - Couriering the success-implement review for implementation commit b4c9e2ca9a594ddb46f718ef6f4477768303e20b.
  - Adjudicating whether the shared contract and route 1.3 consumer stay evidence-only and fail-closed across routing, authority, code, tests, dogfood, prompt, and playbook.
authority_boundary: retrieval_only
stale_if:
  - Commit b4c9e2ca9a594ddb46f718ef6f4477768303e20b is not an ancestor of the target branch.
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

Review the cycle-wide intelligence claim-support contract and its Phase A route
1.3 implementation at `b4c9e2ca9a594ddb46f718ef6f4477768303e20b`
for material failure classes that can survive their own tests: the shared
contract, cold-agent routing, execution prompt, seal schema, validator,
author-built fixtures, and dogfood may all share the same mistaken assumption.
In particular, test whether they can (a) mistake one testimonial for a
directional finding, (b) treat likes as independent experiences or discard
zero-engagement evidence entirely, (c) combine repetitions that do not bind the
same product, axis, condition, formula, or time, (d) award cross-venue support
to duplicated or incompetent source roles, (e) suppress counterevidence, (f)
turn repeated reported reasons into general causal truth, or (g) conflate the
new subject-claim support contract with the existing Judgment run-quality
evidence ladder.

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
  required_revision: b4c9e2ca9a594ddb46f718ef6f4477768303e20b
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
`origin/main..b4c9e2ca9a594ddb46f718ef6f4477768303e20b`.

Owning sources to judge against:

- `AGENTS.md` — cold-agent trigger and project behavior kernel
- `.agents/workflow-overlay/source-loading.md` — claim-support read-pack route
- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
- `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md`
- `forseti/product/spines/judgment/evidence_ladder/forseti_judgment_evidence_ladder_v0.md`
  — read-only comparator for run-quality proof; do not collapse the two ladders
- `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
- `.agents/workflow-overlay/source-of-truth.md` — doctrine propagation contract
- the historical Summer Fridays artifacts cited in the playbook example, for
  factual attribution only; never patch historical research evidence

### Named patchable target set

Only these files are writable:

1. `AGENTS.md`
2. `.agents/workflow-overlay/source-loading.md`
3. `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md`
4. `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
5. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/intelligence_claim_support_dogfood_20260807_v0.md`
6. `forseti-harness/runners/run_phase_acquisition_seal_validation.py`
7. `forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py`
8. `forseti/product/spines/commission_signal_board/README.md`
9. `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
10. `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
11. `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
12. `docs/prompts/handoffs/phase_acquisition_validator_malformed_enum_hardening_handoff_20260807_v0.md`

Everything else is read-only/flag-only, including this courier prompt,
the pre-existing Summer Fridays source evidence, generated/hash-pinned
artifacts, other overlay authority, and other repository maps. Do not widen the
set.

### Review focus

Review the whole named diff, not only likely defects:

- A cold Forseti actor that turns evidence into a finding, explanation, memo,
  comparison, or recommendation is routed to one shared claim-support contract
  across the intelligence cycle. Capture may preserve and nominate evidence but
  cannot silently award corroboration or causal force.
- The shared contract binds one exact proposition before support is counted:
  subject, comparator if any, axis, direction, condition, formula/version, and
  time. Repetitions that do not match that proposition stay separate.
- `directly_observed` can establish a bounded official or measured fact without
  pretending that a single testimonial establishes a customer tendency.
  `isolated` evidence cannot set a directional choice advantage.
- Engagement is represented as resonance or pseudo-corroboration, not an
  independent-person count. Zero or negligible engagement supplies no resonance
  credit but does not erase a raw observation, safety signal, or counterexample.
- Independent repetition de-duplicates actor and syndicated origin.
  Cross-venue corroboration requires at least two competent source roles that
  can actually support the same proposition; source prestige is not a static
  substitute for proposition fit.
- Counterevidence is actively checked. Mixed evidence remains split or
  conditional; contradicted evidence remains parity/unresolved. Repeated
  self-attributions can support a repeated reported reason, never general causal
  truth without a stronger design.
- The new contract governs support for subject claims. The existing Judgment
  evidence ladder governs proof that a Forseti run changed a decision. Neither
  overwrites, duplicates, or silently scores the other.
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
- The Summer Fridays dogfood accurately traces every support posture to the
  cited historical evidence. It does not promote engagement points to unique
  experience counts, combine formula/time mismatches, use broad retailer wear
  mentions as exact product-to-product corroboration, or turn price facts into
  value/premium conclusions. Examples do not become current competitor verdicts
  or representative sentiment.
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
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
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
