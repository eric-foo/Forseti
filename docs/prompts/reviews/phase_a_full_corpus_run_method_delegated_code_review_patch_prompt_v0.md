---
retrieval_header_version: 1
artifact_role: Delegated code review-and-patch prompt
scope: Route 1.6 reusable full-corpus run method at implementation checkpoint 377541e7
use_when:
  - Couriering the frozen Route 1.6 full-corpus implementation to an eligible different-vendor controller with direct repository access.
authority_boundary: retrieval_only
---

# Route 1.6 reusable full-corpus run — delegated code review and patch

Review the frozen Route 1.6 full-corpus implementation adversarially, patch
only material defects inside the named file set, rerun the named validation,
and return a decision-ready report. Done means the implementation cannot call a
selected Phase A subset “full corpus,” cannot compile partial agent responses
as complete, preserves exact source and seal lineage, remains backward
compatible for historical Route 1.4–1.6 callers, and truthfully reports the
unfinished Summer Fridays semantic workload.

```yaml
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
delivery: operator_courier_only
access: repo
target_kind: delegated_code_review_and_patch
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
output_mode: paste-ready-chat
edit_permission: patch-only
required_revision: 377541e7b22ebc97087ea2988c41d84b8fa883f6
revision_mode: ancestor
branch: codex/phase-a-full-corpus-run-method-20260808
receiver_binding:
  receiver_class: external_direct_write
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-phase-a-full-corpus-run-method-20260808
  required_revision: 377541e7b22ebc97087ea2988c41d84b8fa883f6
  revision_mode: ancestor
  clean_at_bind: required
  direct_write_capability: receiver_to_verify
  no_concurrent_writer: receiver_to_verify
dirty_state_allowance: clean at bind; afterward only delegate-authored edits inside the named patch set
historical_seal_write: forbidden
commit_push_pr_merge_stash_reset_clean: forbidden
```

Before source review, read `AGENTS.md` and
`.agents/workflow-overlay/README.md`, then the code-target section of
`.agents/workflow-overlay/delegated-review-patch.md` and the code-review lane
owned by `.agents/workflow-overlay/review-lanes.md`. On the first repository
read, verify the receiver binding, confirm the required revision is an ancestor
of clean current `HEAD`, record that clean `HEAD` as `reviewed_revision`, prove
direct write capability without a synthetic mutation probe, and confirm no
concurrent writer. Do not begin source review if the delegate vendor is OpenAI,
unknown, or undisclosed.

Delegate-facing constants:

- `environment_baseline`: Windows host, PowerShell-first. Use PowerShell syntax
  for shell and test commands; use absolute paths resolvable from any cwd;
  invoke `python`, never `python3`; do not pass Windows drive-letter paths or
  heredocs through bash.
- `lifecycle_hard_stop`: do not commit, push, open or update a PR, merge,
  stash, reset, clean the worktree, or run repository-hygiene actions.
- `decorrelation_commission`: operator courier only, direct repository access,
  and different upstream vendor/model lineage from the OpenAI author are
  mandatory. Same-vendor, unknown-lineage, no-repo, self, and Codex-managed
  substitutes are invalid.

## Authority and target

Read the actual `origin/main...reviewed_revision` diff before reconstructing
the broader source history. Then use these authority pointers only as needed:

- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
- `docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r5/coordinated/retailer_product_axis_coding.json`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v0/README.md`

Patch authority is limited to this exact set:

1. `forseti-harness/judgment/phase_a_semantic_run.py`
2. `forseti-harness/judgment/semantic_evidence_integration.py`
3. `forseti-harness/runners/run_semantic_evidence_integration.py`
4. `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
5. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
6. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v0/README.md`

Everything else is read-only and flag-only. Do not add an adapter framework,
database, model API, embeddings, custom ML, new web acquisition, market
conclusion, or historical seal rewrite. Do not convert the current blocked
Summer Fridays source audit into a pass unless every evidence route truly has a
hash-pinned complete v3 fragment.

## Review attacks

Use the code-review lane. At minimum attack:

- denominator laundering: 577 `used` threads or 1,371 previously coded items
  passing as the full captured corpus;
- missing target-reconciliation or six-legacy-thread union, title/body
  substitution, double counting, and retailer rating-only loss;
- stale or platform-dependent hashes, unverified nested source artifacts,
  locator escape, duplicate/conflicting fragment identities, and route/source
  binding gaps;
- a discovery/control route donating evidence, an evidence route carrying no
  binding, an unused binding, or a blocked route materializing a final source;
- one-batch validation weakening all-batch compilation, partial reconciliation
  laundering, stale responses, duplicate responses, or status falsely claiming
  completion;
- regressions to historical complete-submit callers and Route 1.6 view
  semantics;
- refusal-to-overwrite, external-run-root behavior, and failure visibility;
- whether the dogfood prose overstates what is proven. The observed customer
  census is 804 Reddit conversations, 57,203 Reddit leaves, 56,580 readable,
  623 mechanical exclusions; 221 formerly excluded conversations with 18,476
  leaves and 18,266 readable; six legacy threads; `1gti140` at 186 readable
  leaves; and 3,698 retailer reviews with 3,200 readable plus 498 rating-only.
  These numbers are evidence to verify, not constants to force.

If the defect is design-level, return `NEEDS_ARCHITECTURE_PASS`, stop patching,
and quarantine any partial diff rather than leaving it in the target.

## Required validation

Run and report each command separately. A failure, block, timeout, or not-run
state remains visible.

```powershell
python -m pytest forseti-harness/tests/unit/test_phase_a_semantic_run.py -q
python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m compileall -q forseti-harness/judgment/phase_a_semantic_run.py forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/runners/run_semantic_evidence_integration.py
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Re-run the real customer census to a fresh delegate-owned external filename and
confirm the observed counts rather than copying them from the receipt. Re-run
the blocked source audit to a fresh filename and confirm all 20 sealed routes
are accounted and that missing v3 fragments remain visibly blocked. The
existing external inputs are under
`C:\tmp\forseti-summer-fridays-route-1-6-full-corpus-20260808`.

The author attempted the entire `forseti-harness/tests/unit` suite, but the
local command was terminated at the 60-second execution budget before a result.
Do not report that sweep as passed. You may run it if your route permits a real
result; it is not a substitute for the named focused suites.

## Return

Return:

1. receiver binding, `required_revision`, and captured `reviewed_revision`;
2. severity-ordered findings with exact file/line evidence, failure impact, and
   closure condition;
3. the bounded diff you authored, or an explicit no-patch statement;
4. neutral authority/source citations for each material finding;
5. every validation result, including the two real-run outputs;
6. verdict: `clean_for_architect_adjudication`,
   `patched_for_architect_adjudication`, `NEEDS_ARCHITECTURE_PASS`, or
   `blocked`; and
7. residual risk, especially which Phase A source fragments and semantic
   judgments remain unexecuted.

Your return is decision input only. The Chief Architect must adjudicate every
finding and diff before any returned change is kept.
