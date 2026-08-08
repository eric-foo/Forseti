---
retrieval_header_version: 1
artifact_role: delegated adversarial review-and-patch commission
scope: Frozen Route 1.7 full-corpus source materialization, real shadow receipt, and observed no-API execution-capacity boundary
use_when:
  - Running the de-correlated review-and-patch checkpoint for the Summer Fridays Route 1.7 full shadow candidate.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/review-lanes.md
---

# Adversarial code-and-artifact review/patch — Summer Fridays Route 1.7 full shadow

You are the de-correlated controller for one bounded review-and-patch
commission. Treat your findings, citations, diff, and verdict as claims for the
OpenAI home model to adjudicate; they authorize no merge, readiness claim, or
continued implementation.

## Forseti Prompt Preflight

Read `AGENTS.md` and `.agents/workflow-overlay/README.md` first. Apply the
project-owned source hierarchy, review doctrine, delegated-review-patch rules,
validation gates, and communication style by pointer; do not import policy from
another repository or a summary. Inspect the named target worktree directly.
No context pack, alternate checkout, or recreated source may substitute for
the pinned target. If binding fails, stop with the nearest overlay-owned
blocker.

## Receiver binding

```yaml
receiver_class: external_direct_write
launch_checkout: observe at receiver intake
effective_target_worktree: C:\tmp\forseti-sf-route-1-7-full-shadow-run-20260808
expected_branch: codex/sf-route-1-7-full-shadow-run-20260808
required_revision: 27d1de44d76afc769346e06db0a4dea7f927ee08
revision_mode: ancestor
dirty_state_required_at_bind: clean
direct_write_capability: prove once before review/patch
concurrent_writer_allowed: false
receiver_creation_authorization: not_applicable_external_direct_write
```

Before reading sources, record `reviewed_revision` as the clean current HEAD,
prove `required_revision` is its ancestor, prove this branch is checked out in
only the named target worktree, and prove direct write capability without
leaving a synthetic artifact. A later descendant is outside this run.

## Actor receipt and dispatch

```yaml
author_vendor: OpenAI
home_adjudicator_vendor: OpenAI
required_controller_vendor: Anthropic
current_receiving_actor_role: controller
dispatch_mode: external_direct_write_base_subagent
decorrelation_requirement: different_vendor
patch_executor: controller_direct_bounded_patch
```

If you are not an Anthropic-family controller, or cannot prove the different-
vendor constraint, return `BLOCKED_DECORRELATION_RECEIPT` before review or
patch work. Do not launch a replacement controller.

## Bound target and why patch authority is included

Review the implementation diff `origin/main...reviewed_revision` and the real
external artifacts it claims to summarize. Source-read-only review is
insufficient because defects in enumeration, hashing, identity de-duplication,
placeholder accounting, path containment, or batch separation should be fixed
in the same bounded pass when the correct fix is local and non-architectural.

Patchable files are exactly:

1. `[phase-run]` `forseti-harness/judgment/phase_a_semantic_run.py`
2. `[semantic-core]` `forseti-harness/judgment/semantic_evidence_integration.py`
3. `[runner]` `forseti-harness/runners/run_semantic_evidence_integration.py`
4. `[phase-tests]` `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
5. `[semantic-tests]` `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
6. `[contract]` `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
7. `[receipt]` `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v1/README.md`

Everything else is read-only. Do not patch this commission prompt. Do not add a
route/schema version, provider API, new acquisition, Deliver conclusion,
semantic response, product registry, scheduler, or alternative architecture.
Do not rewrite/restamp the historical seal. If the smallest correct fix needs
any such change or an off-scope file, return `NEEDS_ARCHITECTURE_PASS`, revert
your partial patch, and leave findings only.

## Authority and real evidence to inspect

Read the current versions of:

- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json`
- the seven patchable targets above.

The external run root is read-only evidence:
`C:\tmp\forseti-summer-fridays-route-1-7-full-semantic-shadow-20260808-v1`.
Use `run_spec_complete_v2.json`, the two `_v3_1` family sources,
`source_audit_complete_v2.json`, `phase_a_semantic_source_v3_1.json`,
`phase_a_materialization_receipt_v2.json`, `semantic_bundle_v3.json`,
`batch_prompts\`, and the three SERP review/reconciliation artifacts. Older
non-suffixed/v1 source attempts in that directory are superseded diagnostics,
not owning lineage.

## Review method and attack goals

After `SOURCE_CONTEXT_READY`, invoke `workflow-code-review` for code/change
claims and `workflow-adversarial-artifact-review` for the contract/receipt
claims. If either required review lane is unavailable, return
`BLOCKED_REVIEW_LANE_UNAVAILABLE`; do not emulate a formal pass inline.

Findings first. At minimum, attack these false-pass paths:

- a captured Reddit target, root, reply, legacy packet, empty body, or exact
  `[deleted]`/`[removed]` placeholder disappears or becomes assessable;
- a title is substituted for missing customer language, reply ancestry is
  misbound, or engagement/self-vote becomes independence credit;
- any of the 37 Revolve source files, 607 occurrences, 576 unique native IDs,
  31 repeated IDs, 78 readable reviews, or 498 real-ID rating placeholders is
  lost, doubled, or count-only fabricated;
- repeated Bazaarvoice/Amazon identities are doubled or product-context edges
  are silently discarded;
- an uncoded readable retailer review, changed source hash, duplicate identity,
  repository-absolute internal locator, or external locator escape passes;
- SERP reconciliation links by fuzzy URL/title instead of exact native object
  identity, or implies fresh acquisition for an unavailable historical link;
- `materialize_source_v3` still renders provisional prompt batches, or
  `_pack_batches=False` creates a public false-success route;
- source/audit/bundle hashes, counts, arithmetic, raw-vs-canonical conventions,
  or external artifact statements in the receipt do not recompute exactly;
- 716 generated prompts, 0 accepted responses, and the absence of compilation,
  reconciliation, view, packets, conclusions, or seal readiness are blurred;
- the performance correction changes ordinary `build_bundle` batching or any
  historical Route 1.4–1.6 behavior.

Recompute every stated count and hash from the owning rows/bytes. Dereference
source IDs semantically, not merely by existence. Date fields must retain their
actual anchor type. Preserve the receipt's evidence-only boundary.

## Patch and validation contract

Patch only blocker/major correctness defects and directly necessary regression
tests/docs inside the named scope. Optional hardening is flag-only. Use
`apply_patch`; do not commit, push, open/close a PR, stash, reset, clean, or
delete artifacts.

Run and report every command separately:

```powershell
python -m pytest forseti-harness/tests/unit/test_phase_a_semantic_run.py forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m compileall -q forseti-harness/judgment/phase_a_semantic_run.py forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/runners/run_semantic_evidence_integration.py
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Also rerun the two family builders to fresh delegate-owned output paths and
recompute the combined denominator, but do not overwrite or mutate the owning
external run artifacts. If runtime prevents a real rerun, state exactly what
was and was not independently reproduced.

## Required return

Return:

1. receiver/lineage receipt including `required_revision` and
   `reviewed_revision`;
2. severity-ordered findings with `[label]`, exact file/line, failure scenario,
   impact, source citation, and closure condition;
3. `considered_and_defended` coverage for attacked paths that held;
4. the exact bounded diff left in the target worktree, with per-change source
   citations;
5. observed validation and real-run results, including any blocked/not-run
   command;
6. one verdict: `clean_for_architect_adjudication`,
   `patched_for_architect_adjudication`, or `NEEDS_ARCHITECTURE_PASS`;
7. residual risk, explicitly retaining the `0 / 716` semantic-response block.

Do not call your verdict approval, readiness, acceptance, or merge authority.
