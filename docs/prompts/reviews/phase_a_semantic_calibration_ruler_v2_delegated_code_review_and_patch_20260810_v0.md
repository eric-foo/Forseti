---
retrieval_header_version: 1
artifact_role: review commission
authority_boundary: retrieval_only
status: current
owner: Judgment / claim support
---

# Delegated code review and patch — semantic calibration ruler v2

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
required_revision: a9e572fe039e9c2d6d3d79c75cc6b421f8ad6ac4
revision_mode: ancestor
clean_at_bind: required
```

Goal: adversarially review the smallest-complete ruler-lineage correction and
patch confirmed defects only. Done means every new calibration preparation and
report binds the exact adjudication ruler by stable ID and full SHA-256, unknown
or receipt-mismatched sidecars fail closed, and historical preparation-v1 and
report-v1 evaluation remains exact without rewriting preserved artifacts. No
semantic extraction method, prompt, response, evidence, or view schema may
change.

## Receiver binding and intake

Bind the receiver before source loading. Stop if different-vendor lineage is
not established, repository access or direct write capability is absent, the
required revision is not an ancestor, the target is dirty before receiver-owned
work, or another writer is active. Read `AGENTS.md`,
`.agents/workflow-overlay/README.md`, the code-diff target kind and adjudication
closeout in `.agents/workflow-overlay/delegated-review-patch.md`, and the code
review lane in `.agents/workflow-overlay/review-lanes.md`. Invoke
`workflow-code-review` when available; otherwise apply the repository doctrine
directly and report the method gap.

Use Windows PowerShell, absolute paths, and `python`, never `python3`. Do not
commit, push, modify a PR, merge, stash, reset, clean, or run repository hygiene.
Same-vendor, unknown-lineage, no-repo, self, and Codex-managed substitutes are
ineligible.

## Review and bounded patch scope

Inspect `origin/main...HEAD`. Only these five files are patchable:

1. `forseti-harness/judgment/semantic_calibration.py`
2. `forseti-harness/runners/run_semantic_evidence_integration.py`
3. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
4. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
5. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else, including this prompt and external proof artifacts, is
read-only and flag-only. Do not change method-v5 or method-v6 text, prompt
packing, calibration gold, evidence schemas, provider behavior, the full-corpus
pause, or any preserved report.

Attack at least these questions:

- Can a v2 receipt or report omit, forge, or disagree with the ruler sidecar's
  stable ID or SHA-256 and still evaluate?
- Does the implementation distinguish raw sidecar-byte hashing from canonical
  JSON artifact hashing correctly?
- Can an arbitrary sidecar pass merely by declaring a known version string?
- Are both exact historical v1 hashes accepted while every unknown hash fails?
- Does a legacy v1 receipt deterministically compare against the exact expected
  v1 shape rather than the newly generated v2 receipt?
- Does legacy evaluation reproduce the preserved v5 report object and canonical
  report hash exactly, without adding v2 fields?
- Do new v2 preparation and report artifacts carry the same ruler ID/hash and
  fail when the sidecar is absent or receipt-mismatched?
- Can the ruler text drift without the hard-pinned v2 hash test failing?
- Did contract v22 change no extraction method, prompt bytes, response schema,
  full-corpus state, or readiness posture?

When present, independently verify these external proofs rather than trusting
the workflow prose:

- Historical compatibility output:
  `C:\tmp\forseti-calibration-ruler-v2-compat-20260810-v2\report.json`
  must be object-equal to the preserved v5 `report.json`, remain report v1, and
  retain canonical hash
  `b3e1477c4596fc0da38fbc9e048ba64f8e2519b357e06072262f16877a724a26`.
- New binding proof:
  `C:\tmp\forseti-calibration-ruler-v2-proof-20260810` must carry preparation
  v2 and report v2, ruler ID
  `semantic_calibration_adjudication_contract_v2`, SHA-256
  `186a0022397d35ca5ee6a464742155a6e55e606d1ad0da636611d404c838ab78`,
  and status `SEMANTIC_CALIBRATION_BLOCKED` because no new adjudication ran.

If an external root is absent, report that check as not run. Patch confirmed
defects only inside the named set. Return `NEEDS_ARCHITECTURE_PASS` for a true
design blocker rather than inventing a compatibility path.

## Validation

Run each command separately and report its actual result. The owner explicitly
stopped the broad full-unit-suite run; do not run it.

```powershell
python -m compileall -q forseti-harness/judgment/semantic_calibration.py forseti-harness/runners/run_semantic_evidence_integration.py
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
residual risk. This is decision input only and asserts no approval, readiness,
merge authority, or permission to keep a changed line. The home Chief Architect
must adjudicate the return before retaining delegate-authored changes.
