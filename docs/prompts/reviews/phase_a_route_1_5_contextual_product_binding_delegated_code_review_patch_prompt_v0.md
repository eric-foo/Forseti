# Phase A Route 1.5 Contextual Product Binding Delegated Review + Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Review prompt artifact (delegated code review-and-patch commission, repo access mode)
scope: >
  Paste-ready operator-courier commission for a different-vendor review and
  bounded patch of Phase A Route 1.5 contextual product binding, exact
  comparator proposition binding, and the comparative Summer Fridays dogfood.
use_when:
  - Couriering the success-implement review for implementation commit 7dab89615bdde8ef86dc392846c699e8e9e9a98f.
  - Testing whether ambiguous public language or a wrong-product proposition can survive the new seal.
authority_boundary: retrieval_only
stale_if:
  - Commit 7dab89615bdde8ef86dc392846c699e8e9e9a98f is not an ancestor of the target branch.
  - A named target changes after the delegate captures the reviewed revision.
  - The receiver lacks different-vendor lineage or direct repository write access.
```

## Prompt Preflight

```yaml
output_mode: paste-ready-chat
edit_permission: docs-write
targets:
  - docs/prompts/reviews/phase_a_route_1_5_contextual_product_binding_delegated_code_review_patch_prompt_v0.md
branch: codex/semantic-product-context-20260807
input_prompt_source: docs/prompts/reviews/phase_a_route_1_5_contextual_product_binding_delegated_code_review_patch_prompt_v0.md
output_artifact: operator-couriered chat return; no durable delegate report
review: findings-first mixed code/evidence review with bounded patch authority
doctrine_change: review only; do not invent a different Phase A architecture
```

## Paste-Ready Commission

````markdown
You are an external controller receiving a REPO-MODE DELEGATED CODE REVIEW AND
BOUNDED PATCH commission. This prompt is preparation-only until the receiver
binding and different-vendor who-constraint below pass.

### Goal and success signal

Adversarially review Phase A Route 1.5 at
`7dab89615bdde8ef86dc392846c699e8e9e9a98f`. The intended behavior is:

1. An upstream product-candidate label is only a hypothesis. A semantic agent
   may bind an exact product only from the evidence text plus source-pinned
   surrounding context; otherwise the item remains unresolved or out of scope.
2. A material comparator carries distinct stable subject and competitor
   product IDs. Each competitive-choice proposition it cites must bind exactly
   that pair in that orientation, so an e.l.f. finding cannot cite a Rhode
   proposition.
3. The entire admitted Phase A corpus can still stack support, opposition, and
   adjacent context into shared propositions and axes. This step structures
   evidence; it does not produce a market conclusion or recommendation.
4. The workflow makes no model-provider API call. A capable agent supplies the
   semantic judgment in separate file-return turns; deterministic code owns
   completeness, hashes, allowed shapes, and seal rejection.
5. Route 1.5 owns the new requirements. Historical Route 1.4 keeps its original
   semantic-integration obligation and does not retroactively owe method v2 or
   stable comparator product IDs.

Done means the whole named diff has been inspected against the owning sources;
accepted material defects are patched only inside the named set; all named
validation is reported from observed output; and the return contains findings,
actual diff, neutral citations, verdict, and residual risk. Do not expand into
new acquisition, Deliver, recommendations, APIs, embeddings, a vector store, a
product graph, a catalog-wide identity resolver, or a new evidence-scoring
system.

### Receiver binding and who-constraint

```yaml
receiver_binding:
  receiver_class: receiver_to_bind
  preparation_only_until_bound: true
  delivery: operator_courier_only
  access: repo
  repository: C:\Users\vmon7\Desktop\projects\orca
  effective_target_worktree: C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\forseti-phase-a-choice-20260807
  target_branch: codex/semantic-product-context-20260807
  required_revision: 7dab89615bdde8ef86dc392846c699e8e9e9a98f
  revision_mode: ancestor
  receiver_to_observe:
    - launch_root
    - resolved_target_root
    - target_branch_and_head
    - required_revision_is_ancestor
    - reviewed_revision_captured_before_source_review
    - target_dirty_state
    - direct_write_capability_to_named_targets
    - no_concurrent_writer
author_vendor: OpenAI
delegate_vendor: operator_to_fill
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
```

Bind only if the upstream model vendor differs from OpenAI, its lineage is
known, it can directly read and patch the target worktree, the required
revision is an ancestor of the checked target head, the worktree is clean, and
no other writer is active. Capture current `HEAD` as immutable
`reviewed_revision` before broader source review. If any condition fails,
return `BLOCKED_RECEIVER_BINDING` with the observed mismatch and stop.
Same-vendor, unknown-lineage, no-repo, self, and Codex-managed substitutes are
invalid.

Windows baseline: use PowerShell syntax, absolute paths where launch-root
ambiguity matters, and `python`, never `python3`. Do not commit, push, open or
update a PR, merge, stash, reset, clean, or run repository hygiene.

### Intake and authority

First read `AGENTS.md` and `.agents/workflow-overlay/README.md`, then the
code-diff review-and-patch parts of
`.agents/workflow-overlay/delegated-review-patch.md` and the code-review lane in
`.agents/workflow-overlay/review-lanes.md`. Perform receiver binding before
broad source loading. By the second latency-bearing tool call inspect the
actual implementation diff from `origin/main` through `reviewed_revision`.

Owning sources:

- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
- `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `.agents/workflow-overlay/validation-gates.md` for version-symmetric historical audit behavior
- the cited Summer Fridays community coding artifact and the four dogfood JSON/Markdown artifacts for factual and hash verification

### Named writable target set

Only these files are writable:

1. `forseti-harness/judgment/semantic_evidence_integration.py`
2. `forseti-harness/runners/run_phase_acquisition_seal_validation.py`
3. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
4. `forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py`
5. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
6. `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
7. `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
8. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_dogfood_20260807_v0/source.json`
9. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_dogfood_20260807_v0/batch_response.json`
10. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_dogfood_20260807_v0/reconciliation_response.json`
11. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_dogfood_20260807_v0/view.json`
12. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_dogfood_20260807_v0/README.md`

Everything else, including this courier prompt, is read-only/flag-only. Do not
widen the set.

### Adversarial focus

Review the whole diff, not only these likely seams:

- Can a v2 evidence item omit, empty, malform, or smuggle unusable product
  context while still producing product evidence? Are the allowed context
  types sufficient without installing a broad identity system?
- Does the semantic prompt clearly distinguish context that identifies the
  product from claims actually made by the evidence author? Does it fail closed
  when pronouns, parent/reply relationships, formulas, variants, or products
  remain ambiguous?
- Are legacy v1 bundles genuinely reproducible while new Route 1.5 seals require
  the exact v2 method version and canonical method hash? Can a declared v2
  method with different instructions pass?
- Does the seal fail safely—not crash—on malformed proposition product lists,
  missing IDs, duplicate IDs, reversed orientation, extra product IDs, or a
  proposition about a different competitor? Does exact pairing accidentally
  reject a valid directly comparative proposition shape the contract intends?
- Are stable IDs required only where load-bearing, without confusing them with
  human-readable product identity or back-claiming onto Route 1.4?
- Is the Route 1.5 changelog append-only and version-symmetric in code, tests,
  prompt rules, playbook, and historical-audit behavior?
- Does the comparative Summer Fridays dogfood's thread-title context actually
  resolve the ambiguous word “These” from a source-native pointer? Verify every
  stored bundle, compilation, method, corpus, and view hash and reproduce the
  four no-API stages. Do not treat 2 comments, 10 semantic units, or 8
  propositions as prevalence or independent-customer proof.
- Can support still stack across retailer reviews, Reddit/community language,
  creator/audience evidence, owned facts, and other competent roles without
  collapsing role competence, origin independence, counterevidence, or causal
  ceilings?
- Does the implementation remain the smallest complete intervention? Flag
  recurring ceremony or a broader schema surface that does not catch the named
  wrong-product defects.

Patch the smallest complete correction for any accepted material finding. If
the problem requires a different architecture or route contract, return
`NEEDS_ARCHITECTURE_PASS`, stop patching, and quarantine any partial diff.

### Validation

Run and report observed output for:

```powershell
python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/runners/run_phase_acquisition_seal_validation.py
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Also reproduce the dogfood from `source.json` through `finalize` in a fresh
temporary output location and compare its observed hashes/counts with the
tracked README and view. Each check may pass, fail, be blocked, or be not run;
never hide a failure.

### Return contract

Return, in order:

1. `review_summary`: required revision, immutable reviewed revision,
   receiver/model lineage if disclosable, access mode, and target binding.
2. Findings ordered by materiality with file/line evidence, impact, and minimum
   closure condition; explicitly state if there are no material findings.
3. The bounded diff actually left in the target worktree with neutral citations,
   or `NO_PATCH`.
4. Validation commands and observed results, including dogfood reproduction.
5. Verdict: `clean_for_architect_adjudication | material_issue_remaining |
   NEEDS_ARCHITECTURE_PASS`, plus residual risk.

Your findings, patch, citations, and verdict are decision input only. They do
not authorize merge, readiness, a market conclusion, Deliver, or further scope.
````
