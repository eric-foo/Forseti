---
retrieval_header_version: 1
artifact_role: review commission
authority_boundary: retrieval_only
status: current
owner: Judgment / claim support
---

# Delegated code review and patch — semantic method v6 fidelity correction

```yaml
output_mode: chat-only
delivery: operator_courier_only
access: repo
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
receiver_class: receiver_to_bind
edit_permission: patch-only
effective_target_worktree: C:\tmp\forseti-semantic-selective-verifier-v1-20260810
branch: codex/semantic-meaning-v6
required_revision: b60c205b
revision_mode: ancestor
clean_at_bind: required
```

Goal: adversarially review the bounded method-v6 fidelity correction and patch
only confirmed defects. Done means the general rules distinguish an asserted
desire from its unmet object, prevent nearby preference from inventing a reason,
axis, or comparison, let cold repeats differ in supported atomic decomposition,
and let one reply mix attributed and personal meanings without weakening
attribution. The reviewed state must preserve method-v5 bytes, existing schemas,
real failure visibility, and the recorded `SEMANTIC_CALIBRATION_FAIL` boundary.

## Receiver binding and intake

Before source review, bind the receiver to the target above. Stop without source
loading if different-vendor lineage is not established, repository access is
absent, the required revision is not an ancestor, the target is dirty before
receiver-owned work, direct write capability is absent, or another writer is
active. Then read `AGENTS.md`, `.agents/workflow-overlay/README.md`, the code-diff
target kind and adjudication closeout in
`.agents/workflow-overlay/delegated-review-patch.md`, and the code-review lane in
`.agents/workflow-overlay/review-lanes.md`. Invoke `workflow-code-review` if it
is available; otherwise apply the repository review doctrine directly and name
the method gap.

Delegate-facing constants:

- Windows host and PowerShell-first; use absolute paths and `python`, not
  `python3`.
- Do not commit, push, update a PR, merge, stash, reset, clean, or run repository
  hygiene.
- Delivery is operator-courier-only. Same-vendor, unknown-lineage, no-repo,
  self, and Codex-managed substitutes are ineligible.

## Review and bounded patch scope

Inspect `origin/main...HEAD`, including the two review-prompt-only commits. Only
these five implementation files are patchable:

1. `forseti-harness/judgment/semantic_evidence_integration.py`
2. `forseti-harness/judgment/semantic_calibration.py`
3. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
4. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
5. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else, including this prompt, external calibration artifacts, earlier
runs, generated hashes, and acquisition seals, is read-only and flag-only. Do
not add a schema, API, classifier, score, conclusion, recommendation, full-corpus
run, or readiness claim. Do not convert the failed dogfood into a pass.

Attack at least these questions:

- Is desire polarity defined from the asserted proposition rather than the
  absence of the desired state, without turning sentiment into polarity?
- Does the nearby-context rule block unsupported causal, axis, and comparative
  inferences while retaining genuinely linked context?
- Does cold-repeat adjudication allow different supported atom boundaries but
  still fail when a material meaning, attribution, axis, or direction differs?
- Can a reply retain attributed parent claims and its own personal reaction
  without crediting the parent experience to the reply author?
- Is the retailer peeling correction truth-complete when the source supports
  weeks-long peeling and repeated-use worsening as separate facts?
- Are method-v5 bytes unchanged, method-v6/hash lineage fail-closed, and the
  method-v6 amendment still general rather than Summer-Fridays-specific?
- Does the completion-path record match the real v5 report and clearly retain
  the full-corpus pause?

Fresh-read the bounded run at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-review-fix-20260810-v5`
when it exists. Recompute the canonical hashes instead of trusting prose. The
expected observed boundary is: two production prompts, largest 89,958 bytes;
7/7 core and 121/121 production leaves accounted; all seven relations
satisfied; 15/17 evaluator case results, 5/7 cold repeats, and 8/10 density rows;
status `SEMANTIC_CALIBRATION_FAIL`; canonical report hash
`b3e1477c4596fc0da38fbc9e048ba64f8e2519b357e06072262f16877a724a26`.
If the external lineage is absent, report it as not run.

## Validation

Run each command separately and report the actual result. The owner explicitly
stopped the broad full-unit-suite run; do not run it.

```powershell
python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/judgment/semantic_calibration.py
python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_a_semantic_run.py -q
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

## Return

Return binding facts, severity-ordered findings, `considered_and_defended`, the
exact bounded diff, neutral citations, every validation result, verdict, and
residual risk. This is decision input only: it asserts no approval, readiness,
merge authority, or permission to keep a changed line. The home Chief Architect
must adjudicate every finding and delegate-authored patch before it is kept.
