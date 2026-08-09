---
retrieval_header_version: 1
artifact_role: Operator-couriered delegated code review-and-patch closure commission
scope: Product-identity catalog reach and mixed-product semantic binding in Phase A method v4
use_when:
  - Couriering the frozen product-catalog implementation to an eligible different-vendor repository controller.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/review-lanes.md
---

# Delegated code review and patch: Phase A product-catalog closure

This prompt is preparation-only until an external direct-write receiver proves
the binding below. Do not load target sources before that binding passes.

```yaml
delivery: operator_courier_only
access: repo
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: operator_to_fill
output_mode: chat-only
output_destination: courier conversation
edit_permission: patch-only
target_kind: delegated_code_review_and_patch
template_kind: none
doctrine_change: none
receiver_binding:
  receiver_class: receiver_to_bind
  binding_state: receiver_to_bind
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-phase-a-product-catalog-v4-20260809
  required_revision: fd265689c169b746803a35bf1e5355b9e61b8f24
  revision_mode: ancestor
  capability_proof: receiver_to_observe
  no_concurrent_writer_state: receiver_to_observe
```

## Goal and success signal

Review the full `origin/main...reviewed_revision` implementation and patch any
confirmed defect inside the named set. The capability succeeds only when a
method-v4 final-acquisition run can use one verified, hash-bound product catalog
to identify a product semantically from preserved leaf and context—even when a
Reddit leaf has no upstream product candidate—without using catalog names as
evidence, inventing identities for variants or mentioned comparators, merging
separate products in a mixed conversation, or crediting one customer twice.

The material shared-assumption risk is that the builder, validator, prompt,
tests, and bounded proof may agree with one another while still assigning an
empty-candidate or mixed-product leaf to the wrong product, accepting an
unverified catalog, or silently losing the catalog on the real full-run path.
Ordinary author validation cannot independently close that class, so this is a
commissioned full-diff discovery-and-patch pass.

## Closure context

One different-vendor receiver reviewed the earlier revision but could not load
the commissioned `workflow-code-review` method. Its findings were useful but did
not close this review gate. Home adjudication then:

- fixed duplicate product-binding artifacts in bounded-proof projection;
- barred identity-bearing `product_version_ids` under catalog v1 while keeping
  variant language in statements and conditions;
- recorded that only the sanctioned run-spec materializer is spec-verified;
- recorded the method-v4 prompt-hash discontinuity; and
- reran the four-leaf proof through cold extraction and reconciliation.

Re-derive these closures from code and artifacts; do not inherit the prior
reviewer's findings as premises. If `workflow-code-review` is unavailable, stop
with `BLOCKED_METHOD_UNAVAILABLE`: do not substitute another method or emit a
clean/patched verdict.

## Binding intake

Before source review:

1. Record the observed delegate vendor and stop as ineligible if it is OpenAI,
   unknown, or undisclosed, or if direct repository write access is absent.
2. Verify the effective target exists and is clean; verify
   `git merge-base --is-ancestor fd265689c169b746803a35bf1e5355b9e61b8f24 HEAD`.
3. Prove direct write capability without a synthetic mutation when ordinary
   commissioned patching already proves it; verify no concurrent writer.
4. Record the current `HEAD` as immutable `reviewed_revision`, then inspect
   `origin/main...reviewed_revision`. If the branch advanced after capture, use
   a separate clean worktree at the captured revision.

Read `AGENTS.md` and `.agents/workflow-overlay/README.md` at intake. For the
review method, load `workflow-code-review` and follow the Review Prompt Defaults
in `.agents/workflow-overlay/prompt-orchestration.md`. Apply the code-diff target
kind, de-correlation, escalation, and adjudication-closeout sections in
`.agents/workflow-overlay/delegated-review-patch.md`. Review Doctrine is owned by
`.agents/workflow-overlay/review-lanes.md`.

Delegate-facing environment baseline: Windows host, PowerShell-first; use
PowerShell syntax for shell/test commands; use absolute paths resolvable from
any cwd; invoke `python`, never `python3`; do not pass Windows drive-letter paths
or heredocs through bash.

Lifecycle hard stop: do not commit, push, open or update a PR, merge, stash,
reset, clean the worktree, or run repository-hygiene actions.

De-correlation commission: delivery is operator-courier-only; access is direct
repo; the delegate must have a different upstream vendor/model lineage from the
OpenAI author. Same-vendor, unknown-lineage, no-repo, self, and Codex-managed
controller substitutes are invalid. A manager-prefixed target path is neutral.
If no eligible controller is available, leave this commission unexecuted.

## Named patchable set

Patch only these files:

- `forseti-harness/judgment/phase_a_semantic_run.py`
- `forseti-harness/judgment/semantic_evidence_integration.py`
- `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
- `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_product_catalog_reach_proof_20260809_v0/README.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_product_catalog_reach_proof_20260809_v0/receipt.json`

Everything else, including this commission and all external run artifacts, is
read-only/flag-only. Do not alter historical seals or generated/hash-pinned
artifacts. If a material closure requires another file or a design change,
return `NEEDS_ARCHITECTURE_PASS`; quarantine any partial design-level diff.

## Required attacks

- Trace catalog construction through the actual final source materializer,
  bundle builder, prompt packing, response validation, reconciliation, and
  evidence-packet path. Attack missing-marker and silent-fallback paths.
- Construct conforming empty-candidate and mixed-product conversations: one
  brand-level root with replies about different products, one product with
  multiple variants, and a reply mentioning a comparator. Verify semantic
  ownership uses leaf plus context, not lexical/catalog matching.
- Attack catalog integrity: stale or missing authority artifacts, tampered hash,
  duplicate stable IDs, alias/source-ID collisions, reordered or omitted rows,
  unknown response product IDs, and a catalog removed after materialization.
- Attack accounting: the same public actor or leaf must not gain independent
  credit twice merely because product contexts overlap.
- Re-derive the bounded real proof from
  `C:\tmp\forseti-summer-fridays-product-catalog-reach-dogfood-20260809-v3`
  when available.
  Dereference all four evidence IDs, verify that both Reddit rows truly have
  empty candidates, and recompute every count and hash claimed by the receipt.
  Verify the preserved three failed finalization attempts as well as the final
  accepted response. If that external root is unavailable, mark each real-proof
  claim not run; do not infer it from the README.
- Prove historical method-v3 behavior and the earlier 300-leaf bounded proof
  remain byte/hash exact where claimed.
- Check that the docs say only what the code and real artifacts establish and
  do not turn evidence structure into a conclusion or seal claim.

## Validation

Run and report each command separately after any patch:

```powershell
python -m compileall -q forseti-harness/judgment/phase_a_semantic_run.py forseti-harness/judgment/semantic_evidence_integration.py
python -m pytest forseti-harness/tests/unit/test_phase_a_semantic_run.py forseti-harness/tests/unit/test_semantic_evidence_integration.py -q
python -m pytest forseti-harness/tests/unit -q
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Surface failures and not-run checks exactly; never hide or route around them.
Run a focused regression demonstrating each patched defect fails on the frozen
shape and passes after the patch. Do not claim that bounded dogfood proves the
59,225-leaf full run.

## Return contract

Return, in order:

1. receiver binding, author/delegate lineage, required and reviewed revisions;
2. severity-ordered findings with confidence, decisive evidence, minimum
   closure condition, and next authorized action;
3. `considered_and_defended` candidates;
4. the exact bounded diff and neutral source citations for every change;
5. every validation command and observed result, including real proof checks;
6. one of `patched_for_architect_adjudication`,
   `clean_for_architect_adjudication`, or `NEEDS_ARCHITECTURE_PASS`; and
7. residual risk, including the non-independent sliver of delegate-authored
   patch lines.

The return is decision input only. The home Chief Architect must adjudicate
every finding, changed line, verdict, and residual before any returned patch is
kept. Closeout follows `.agents/workflow-overlay/delegated-review-patch.md` ->
Adjudication closeout, including same-turn closure of self-closable material
issues and the next material move. Nothing here authorizes lifecycle action.
