---
retrieval_header_version: 1
artifact_role: Delegated code review-and-patch prompt
scope: Phase A bundle-v4 semantic work units, three-worker execution, slim reconciliation, and bounded Summer Fridays proof at implementation checkpoint 1f1b1fbe
use_when:
  - Couriering the frozen bundle-v4 implementation to an eligible Anthropic controller with direct access to the bound worktree.
authority_boundary: retrieval_only
---

# Phase A semantic work units v4 — delegated code review and patch

Review the frozen implementation adversarially, patch only material defects
inside the named set, rerun the named validation and bounded dogfood checks,
and return a decision-ready report. Done means every admitted evidence leaf has
one work-unit owner, repeated context is shared without changing meaning,
three no-API workers can resume honestly, reconciliation does not copy expanded
lineage into agent prompts, parallel workers cannot make overlapping axis-label
decisions, historical bundle-v3 reproduction remains exact, and Phase A emits
structured evidence rather than a Deliver conclusion.

```yaml
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
delivery: operator_courier_only
access: repo
target_kind: delegated_code_review_and_patch
delegate_eligibility: different_vendor_lineage_with_direct_repo_access
author_vendor: OpenAI
delegate_vendor: Anthropic
output_mode: paste-ready-chat
edit_permission: patch-only
required_revision: 1f1b1fbea1b1da60167814996b57cbb4d41d6fa0
revision_mode: ancestor
branch: codex/phase-a-semantic-work-units-v4-20260808
receiver_binding:
  receiver_class: external_direct_write
  launch_checkout: receiver_to_observe
  effective_target_worktree: C:\tmp\forseti-phase-a-semantic-work-units-v4-20260808
  required_revision: 1f1b1fbea1b1da60167814996b57cbb4d41d6fa0
  revision_mode: ancestor
  clean_at_bind: required
  direct_write_capability: receiver_to_verify
  no_concurrent_writer: receiver_to_verify
dirty_state_allowance: clean at bind; afterward only delegate-authored edits inside the named patch set
historical_seal_write: forbidden
commit_push_pr_merge_stash_reset_clean: forbidden
```

Before review, read `AGENTS.md`, `.agents/workflow-overlay/README.md`, the
code-target section of `.agents/workflow-overlay/delegated-review-patch.md`,
and the code-review lane in `.agents/workflow-overlay/review-lanes.md`. On the
first repository read, verify the receiver binding, prove the required revision
is an ancestor of clean current `HEAD`, record that `HEAD` as
`reviewed_revision`, confirm direct write capability without a synthetic
mutation probe, and confirm no concurrent writer. Stop if the receiver is
OpenAI, unknown-lineage, cannot read the repository, or cannot bind the target.

Use PowerShell on the Windows host, absolute paths where cwd ambiguity exists,
and `python`, not `python3`. Do not commit, push, open/update a PR, merge,
stash, reset, clean, rewrite the historical acquisition seal, or touch files
outside the patchable set.

## Authority and patch boundary

Read `origin/main...reviewed_revision`, then these owning sources:

- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v1/README.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v2/README.md`
- the implementation and tests in the named patch set below.

Patch authority is limited to exactly:

1. `forseti-harness/judgment/phase_a_semantic_run.py`
2. `forseti-harness/judgment/semantic_evidence_integration.py`
3. `forseti-harness/runners/run_semantic_evidence_integration.py`
4. `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
5. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
6. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
7. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v2/README.md`

Everything else is read-only and flag-only. Do not add a queue, lease,
daemon, dashboard, embeddings, vector database, sampling path, model/provider
API, headless model driver, new source acquisition, prompt-ceiling increase,
market conclusion, recommendation, or new seal claim. Preserve source v3 and
exact historical bundle-v3 reproduction. The active agent task—not a new
runtime controller—owns at most three no-API workers.

## Required attacks

At minimum attack:

- exact bijection: missing, duplicate, or multiply assigned evidence IDs;
  projection/hash forgery; accounting rows whose reference resolves to no
  evidence; shared-context identity with divergent text;
- semantic fidelity: context references expanding differently than bundle v3,
  parent/product context loss, deterministic fields being omitted from prompts
  before the compiler can restore them, or Phase A inventing a conclusion;
- actual scale: quadratic prompt rerendering, an oversized rendered prompt,
  context copied once per reply/work unit, or the 513-work-unit result being
  obtained by sampling rather than all 59,225 assessable leaves;
- execution honesty: static 171/171/171 partition mismatch, stale/duplicate
  response acceptance, missing partitions hidden by status, final-path writes
  before validation, non-atomic publication, overwrite, or partial response
  compilation;
- identity credit: exact normalized public handles across scoped venues must
  conservatively receive one credited origin and `possible_same_actor` for the
  rest, without asserting unique-person identity or changing source v3;
- slim reconciliation: agent prompts must omit expanded `leaf_relations` and
  `condition_lineage` while compiler lineage remains exact; the one-terminal-
  batch gate and 150,000-byte ceiling remain fail-closed;
- global emerging axes: bundle v4 declares exactly one owner batch per level,
  supplies it the complete unique new-label set, requires other batches to
  return no consolidations, carries frozen decisions unchanged, and never uses
  a lexical/compiler choice to resolve semantic overlap;
- backward compatibility: historical bundle-v3 and regression dogfood bytes
  must remain exact; current validation must not back-claim old route fields;
- receipt accuracy and non-claims, including `0 / 513` full-corpus semantic
  responses and the bounded calibration's 206 leaves / 440 units / two levels /
  six propositions / 428 unmerged units / 78 axis candidates.

If a defect requires changing the frozen architecture constraints above,
return `NEEDS_ARCHITECTURE_PASS`, leave no partial diff, and explain the
minimum decision needed. Otherwise author the smallest complete patch inside
the named set and add regression coverage for every accepted defect.

## Required validation and real checks

Run every command separately and report observed pass/fail/blocked/not-run:

```powershell
python -m compileall -q forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/judgment/phase_a_semantic_run.py forseti-harness/runners/run_semantic_evidence_integration.py
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

The real external lineage is under
`C:\tmp\forseti-phase-a-semantic-work-units-v4-dogfood-20260808`. Verify, do
not merely copy, these bounded facts without overwriting existing artifacts:

- full bundle: 60,901 captured, 59,225 admitted, 513 work units, largest
  rendered prompt 149,672 bytes before file newline, exact 171/171/171 worker
  partition, bundle SHA-256
  `b3d88c8e910be1b22496222ea9c5e8e8bc6579c4c6e4ae7aa3af87f10324002c`;
- calibration: three valid extraction responses, 440 compiled units; level 1
  has two batches and exactly one global axis owner; level 2 has one batch and
  omits expanded lineage; terminal view SHA-256
  `3d9af1b55649faabfdd3d0f63750eeb0afeb3046509cb95f7d7ecddc978eeb9f`;
- evidence packet SHA-256
  `14a092219a60556ebf2ece2ddebab1a49ba44b8feab82426c77cce2b06bd4a78`
  and two exact underlying SK-II evidence items with their provenance.

Do not treat the existing ignored `forseti-harness/.venv` generated during the
calibration as a target artifact or patch surface. The home lane attempted its
exact removal after proving containment, but the protected-action policy
rejected the delete; it is an environment residue, not implementation output.

## Return

Return: receiver binding and reviewed revision; severity-ordered findings with
file/line evidence, impact, and closure condition; the exact bounded diff (or
explicit no-patch); authority citations; all validation and real-check results;
verdict `clean_for_architect_adjudication`,
`patched_for_architect_adjudication`, `NEEDS_ARCHITECTURE_PASS`, or `blocked`;
and residual risk. State explicitly that your return is decision input only
and that the home architect must adjudicate every finding and changed line
before anything is kept.
