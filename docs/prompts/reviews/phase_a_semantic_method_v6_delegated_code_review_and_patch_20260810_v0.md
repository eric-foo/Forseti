---
retrieval_header_version: 1
artifact_role: review commission
authority_boundary: retrieval_only
status: current
owner: Judgment / claim support
---

# Delegated code review and patch — semantic method v6

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
required_revision: 97eb63e3bfc2b87a926db66f14638ba006c000b9
revision_mode: ancestor
clean_at_bind: required
```

Goal: adversarially review the semantic-method-v6 implementation and apply only
the smallest complete patches needed to make its general meaning-preservation
rules durable without changing the frozen method-v5 behavior or the existing
bundle/response/view schemas. Done means the reviewed diff fails closed on
wrong method/run bindings, preserves method-v5 bytes, keeps the new rules
general rather than Summer-Fridays-specific, passes the named validation, and
states the controlled-dogfood boundary honestly.

The material failure class that triggers this commission is a shared-assumption
false pass: author-written routing, tests, and controlled replay could all agree
while a real run silently selects method v5, changes a frozen interface, or
encodes the observed examples instead of the general rule. The replay is not an
independent oracle because the home author corrected its affected responses.

## Receiver binding and intake

Before source review, bind this unknown courier receiver to the target above:

```yaml
receiver_binding:
  receiver_class: external_direct_write
  launch_root: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-semantic-selective-verifier-v1-20260810
  branch: codex/semantic-meaning-v6
  required_revision: 97eb63e3bfc2b87a926db66f14638ba006c000b9
  revision_mode: ancestor
  clean_at_bind: required
  direct_write_capability: receiver_to_observe
  no_concurrent_writer: receiver_to_observe
```

Stop without source loading if vendor lineage differs neither from OpenAI nor
is known, repository access is absent, the required revision is not an ancestor,
the target is dirty before receiver-owned work, or another writer is active.
After binding, read `AGENTS.md`, `.agents/workflow-overlay/README.md`, the
code-diff target kind and adjudication closeout in
`.agents/workflow-overlay/delegated-review-patch.md`, and the code-review lane
in `.agents/workflow-overlay/review-lanes.md`. Invoke `workflow-code-review` if
available; if unavailable, apply the repository's code-review doctrine directly
and report that method gap without claiming it was invoked.

Delegate-facing constants, restated from
`docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`:

- Environment: Windows host, PowerShell-first; use PowerShell syntax, absolute
  paths resolvable from any cwd, and `python`, never `python3`; do not pass
  Windows drive-letter paths or heredocs through bash.
- Lifecycle hard stop: A delegate or receiver does not commit, push, open or
  update a PR, merge, stash, reset, clean the worktree, or run
  repository-hygiene actions unless the commission explicitly grants that
  action.
- Decorrelation: delivery is operator-courier-only, access is repo, and
  eligibility requires different-vendor lineage with direct repository access.
  Same-vendor, unknown-lineage, no-repo, self, and Codex-managed substitutes
  are invalid. If no eligible controller is available, leave this prompt
  unexecuted.

## Review and bounded patch scope

Inspect `origin/main...HEAD`, including the later prompt-only commit. Only these
seven implementation files are patchable:

1. `forseti-harness/judgment/semantic_evidence_integration.py`
2. `forseti-harness/judgment/semantic_calibration.py`
3. `forseti-harness/judgment/phase_a_semantic_run.py`
4. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
5. `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
6. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
7. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Everything else, including this prompt, external calibration artifacts, frozen
historical outputs, generated hashes, and acquisition seals, is read-only and
flag-only. Do not add a schema, second semantic pass, classifier, score, API,
recommendation, full-corpus run, or route/seal readiness claim.

Attack at least these questions:

- Can run v4 or calibration v6 silently fall back to method v5?
- Are method-v5 text and historical generation behavior byte-reproducible?
- Does method v6 reuse bundle v5 and response/compilation v3 coherently in both
  directions, rejecting impossible combinations?
- Do the new instructions preserve causes, qualifications, connected behavior,
  outcome-directed axes, relevant customer attributes, category/value
  separation, and unmerged evidence without becoming a phrase list or encoding
  the Summer Fridays examples?
- Are named-shade preference, healed pre-existing peeling, non-drying,
  advertised-balm value, experienced-gloss category, and ownership-plus-go-to
  represented at the claimed evidence stage without manufacturing fit,
  repurchase, or a Deliver recommendation?
- Does calibration project the spec-bound method into every primary and cold
  slice, with method/hash lineage preserved?
- Does the completion-path record accurately distinguish a controlled 128-leaf
  replay from fresh independent semantic proof?

Patch confirmed defects only inside the named set. For a design-level blocker,
return `NEEDS_ARCHITECTURE_PASS`, quarantine any partial patch, and stop.

## Validation

Run and report actual results separately; never mask a failure or infer a
not-run result:

```powershell
python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/judgment/semantic_calibration.py forseti-harness/judgment/phase_a_semantic_run.py
python -m pytest forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_a_semantic_run.py -q
python -m pytest forseti-harness/tests/unit -q
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Fresh-read the controlled report at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-replay-20260810-v1\report-v2.json`
when that external lineage exists. Recompute its canonical hash and check the
reported 17/17 cases, 7/7 repeats, 7/7 relations, ten reviewed density rows,
zero blockers, and zero hard failures. If the lineage is absent, say not run;
do not copy its README or this prompt as proof.

## Return

Return findings in severity order, `considered_and_defended`, the exact bounded
diff, neutral source citations, every validation result, a verdict, and residual
risk. Identify the reviewed revision and all binding facts. Your return is
decision input only: it is not approval, validation, readiness, merge authority,
or permission to keep your changes. The home Chief Architect must adjudicate
every finding, changed line, verdict, and residual before anything is kept,
close self-closable issues in that adjudication turn, and route only genuinely
external blockers.
