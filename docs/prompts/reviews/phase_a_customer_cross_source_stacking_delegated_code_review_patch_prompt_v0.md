---
retrieval_header_version: 1
artifact_role: Delegated code review-and-patch prompt
scope: Phase A run-local product binding and customer-side community-plus-retailer evidence stacking as landed at merge revision 87fd7f5
use_when:
  - Couriering the landed customer cross-source stacking implementation to an eligible different-vendor controller with direct access to the bound worktree.
authority_boundary: retrieval_only
---

# Phase A customer cross-source stacking — delegated code review and patch

Review the frozen implementation adversarially, patch only confirmed defects
inside the named set, rerun the required checks, and return a decision-ready
report. Done means a future Phase A run can bind the same product across
Reddit/community and retailer evidence, stack compatible customer evidence by
meaning and axis without using mere word matches, preserve provenance and
unmerged evidence, and hand structured evidence—not a recommendation—to
Deliver. Company-side campaign and ad evidence remains a separate later bridge.

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
required_revision: 87fd7f5625745f0ab9e8800703e971291c2b7e92
revision_mode: ancestor
branch: claude/cross-vendor-review-routing-ykb4js
receiver_binding:
  receiver_class: external_direct_write
  launch_checkout: receiver_to_observe
  effective_target_worktree: receiver_to_bind
  required_revision: 87fd7f5625745f0ab9e8800703e971291c2b7e92
  revision_mode: ancestor
  clean_at_bind: required
  direct_write_capability: receiver_to_verify
  no_concurrent_writer: receiver_to_verify
dirty_state_allowance: clean at bind; afterward only delegate-authored edits inside the named patch set
historical_seal_write: forbidden
commit_push_pr_merge_stash_reset_clean: forbidden
```

Before review, read `AGENTS.md`, `.agents/workflow-overlay/README.md`, the
code-diff target section of `.agents/workflow-overlay/delegated-review-patch.md`,
and the code-review lane in `.agents/workflow-overlay/review-lanes.md`. On the
first repository read, verify the receiver binding, prove the required
revision is an ancestor of clean current `HEAD`, record that `HEAD` as
`reviewed_revision`, confirm direct write capability without a synthetic
mutation probe, and confirm no concurrent writer. Stop if the receiver is
OpenAI, unknown-lineage, cannot read the repository, or cannot bind the target.

Use PowerShell on the Windows host, absolute paths where cwd ambiguity exists,
and `python`, not `python3`. Do not commit, push, open or update a PR, merge,
stash, reset, clean, rewrite a historical seal, or touch files outside the
patchable set.

## Outcome and architecture boundary

The accepted outcome is the smallest complete customer-side cross-source
stacking layer at the tail of Phase A:

- bind source-specific product identifiers and aliases to one stable product
  for this run only;
- bring community and retailer evidence about that product into the same
  semantic work while retaining source role, container, author, engagement,
  product context, axis candidates, uncertainty, and evidence lineage;
- allow compatible customer observations to corroborate or stack across
  venues by meaning, direction, conditions, and uncertainty;
- keep incompatible or unresolved evidence explicitly unmerged;
- expose the resulting evidence packet for later retrieval by product and
  axis without deciding the business recommendation.

This is not a global product ontology, a lexical mention classifier, a market
conclusion, a causal claim, a Deliver recommendation, campaign intelligence,
or a customer-versus-company evidence merger. Meta Ads Library, Google Ads
Transparency, owned claims, and creator/campaign evidence remain separate
company-side lanes. A later, explicit bridge may compare those claims with
customer complaints or language; this commission must not build that bridge.

The bounded Summer Fridays proof is regression evidence, not a replacement for
the later full cold run and not seal eligible. Preserve historical run-spec v1,
semantic method v3, bundle v3, and existing Route 1.6/1.7 behavior exactly.

## Authority and patch boundary

Read `origin/main...reviewed_revision`, then these owning sources:

- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_customer_cross_source_proof_20260809_v0/README.md`
- `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_customer_cross_source_proof_20260809_v0/run_spec_v2.json`
- the implementation and tests in the named patch set below.

Patch authority is limited to exactly:

1. `forseti-harness/judgment/phase_a_semantic_run.py`
2. `forseti-harness/judgment/semantic_evidence_integration.py`
3. `forseti-harness/runners/run_semantic_evidence_integration.py`
4. `forseti-harness/tests/unit/test_phase_a_semantic_run.py`
5. `forseti-harness/tests/unit/test_semantic_evidence_integration.py`
6. `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
7. `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`
8. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_customer_cross_source_proof_20260809_v0/README.md`
9. `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_customer_cross_source_proof_20260809_v0/run_spec_v2.json`

Everything else, including this prompt and the external proof directory, is
read-only and flag-only. Do not add a global registry, embeddings, vector
database, provider API, automatic lexical grouping, new acquisition lane,
campaign bridge, Deliver conclusion, recommendation, or new seal claim.

## Required attacks

At minimum attack:

- product binding integrity: duplicate stable IDs, one source ID or normalized
  alias mapped to multiple products, unmapped relevant source IDs, silent
  alias collisions, and evidence refs whose bytes no longer match their pins;
- ownership versus mention: evidence from another product page must not become
  focal-product evidence merely because its text mentions the focal product;
  page/source product ownership must survive Amazon, Bazaarvoice/Sephora,
  Revolve, and Reddit projection;
- context provenance: human-readable product context must remain hash-pinned
  and traceable without changing the evidence owner or fabricating a product
  match;
- method integrity: run-spec v2 must actually reach semantic method v4 where
  intended; a missing, stripped, substituted, or forged method marker must not
  silently fall back to v3 semantics;
- historical compatibility: run-spec v1 and method-v3 outputs and hashes must
  remain exact; current fields must not be back-claimed on historical routes;
- bounded proof completeness: the 300 selected leaves must be an exact
  accounting/container projection of the mapped product and two requested
  axes, not a lexical sample or a single-retailer shortcut;
- cross-source semantic competence: community and retailer rows may combine
  only when stable product, meaning, direction, relevant conditions, and
  uncertainty are compatible; source diversity alone is not corroboration;
- evidence preservation: incompatible, weak, unresolved, or unmerged evidence
  must remain retrievable and counted rather than disappearing behind the 53
  propositions;
- provenance and origin credit: engagement is corroborating resonance, not an
  independent-experience count; duplicate or possibly-same actors must not gain
  false independence;
- receipt accuracy: rederive material counts and hashes from the external
  proof rather than trusting README prose or copied receipts;
- CLI and write safety: reject stale inputs, duplicate output, partial output,
  invalid axes/products, malformed specs, or proof overwrite without leaving a
  fake success artifact;
- doctrine boundaries: reject any campaign, causal, universal-sentiment,
  recommendation, readiness, seal-eligibility, or Deliver overclaim;
- test validity: ensure new tests fail for the intended defect and cannot pass
  because fixtures omit the dangerous state.

## Prior rounds — context only, not accepted findings

Two earlier passes touched this work. Neither filed a durable review report;
treat both as context and re-derive everything from primary sources.

**Prior different-vendor round (Anthropic).** A delegated round ran against
the pre-merge revision `b3f62cba` and was adjudicated in chat only. The sole
durable record is the merge-commit trailer of `87fd7f5`:

> `review_routing_status: routed -- chat_only_adjudicated: Anthropic review
> accepted F1 and F2, rejected F3 after Windows real-proof rebuild`

The accepted fixes landed as `fix(phase-a): preserve v4 method and verify
proof lineage` inside the merged revision you are now reviewing. No filed
artifact records what F1, F2, and F3 actually were, and their mapping onto the
three same-vendor leads below is **not** recorded anywhere — do not assume one.
That round is therefore not a substitute for this review and grants no finding
immunity: a defect it may have missed is still in scope, and an area it may
have cleared still needs your own evidence.

**Prior same-vendor leads (OpenAI, unadjudicated).** An in-session OpenAI
reviewer was launched by mistake and stopped when the owner clarified that the
delegated patch must be performed by a different model vendor. Its patch was
removed completely; the target was restored to the then-required revision.
Nothing below is an accepted finding or an authorized fix. Note that these
leads were written against `b3f62cba`, before the accepted fixes landed, so
some may already be closed in your target. Independently reproduce or reject
each lead from primary sources:

1. **Proof-input integrity.** It suspected
   `build_phase_a_product_axis_proof_source` accepts a rehashed or tampered full
   source without checking the stored `source_sha256` and hash-pinned
   `source_artifacts` before projection. Determine whether the surrounding
   materialization path already proves those bindings; patch only if a real
   false-pass path remains.
2. **Replay duplication/conflict.** It suspected rebuilding a bounded proof
   from an already projected proof can duplicate the product-binding context
   and append a conflicting or duplicate `source_artifact` with the same ID.
   Test idempotent replay and artifact-ID conflict explicitly; do not assume
   replay is required if the contract forbids it.
3. **Method-marker loss.** It suspected `materialize_phase_a_v3` with run-spec
   v2 may emit no `semantic_method_version`, causing downstream bundle creation
   to use method v3 even though the run requested v4. Trace the actual full-run
   path and distinguish the bounded proof builder from full materialization.

Do not inherit the stopped reviewer's proposed code. A reproduced finding
needs its own evidence, impact, closure condition, smallest complete patch, and
regression test. A rejected lead should be listed under
`considered_and_defended` with the decisive evidence.

## Required real checks

The external proof lineage is read-only and, on the authoring machine, lived at:

`C:\tmp\forseti-phase-a-customer-cross-source-proof-20260809`

**Operator precondition — this path is machine-local and is not in the
repository.** The in-repo proof directory carries only `README.md` and
`run_spec_v2.json`; every large artifact the checks below reference (the five
prompts, the level-one/level-two responses, the preserved failed response, the
final view, and the evidence packet) lives outside the repo. The operator must
supply that directory to the receiver before this section can be executed.

If the directory is not available to you, do **not** infer these facts from the
README prose, and do not treat the README's own recitation of them as
verification — the README is the claim under test, not evidence for it. Report
every item in this section as `blocked`, name the missing path, and continue
with the rest of the review. A return that marks this section blocked is a
valid return; a return that silently reports these facts as verified from the
README is not.

With the directory available, rebuild or independently inspect enough primary
artifacts to verify, rather than merely copy, these recorded facts:

- deterministic proof selection: 300 assessable leaves, 216 community and 84
  retailer, across 255 containers;
- retailer ownership split: 75 Sephora `P455936`, 7 Amazon `B0C42HJRBF`, and 2
  Revolve `SUMR-WU76`;
- 15 reviews owned by other product pages mention the balm and stay excluded,
  including 6 Dream Lip Oil `P509439` reviews;
- 5 prompts, largest 126,308 bytes before file newline, with no provider API;
- all 300 items accounted: 254 claim-bearing, 4 context-only, 42 out-of-scope,
  yielding 576 semantic units;
- terminal result: 53 propositions and 477 explicitly unmerged semantic units;
- 8 genuine community-plus-retailer propositions, each carrying both customer
  source roles and cross-venue support without becoming a conclusion;
- two-axis evidence packet: 26 selected propositions, 55 linked evidence
  items, 54 containers, 52 credited origins, 229 axis-relevant unmerged units,
  248 unscoped unmerged units, and no truncation.

Check the hashes recorded in the proof README against the actual objects. Do
not overwrite or regenerate the preserved failed level-2 response; it is
evidence that the competence gate rejected an `actor_strategy` and an
`observable_fact` overclaim before the corrected response preserved both
children as explicitly unmerged.

## Required validation

Run every command separately and report observed pass, fail, blocked, or not
run. Use a realistic timeout for the full unit suite; do not conceal a retry.

```powershell
python -m compileall -q forseti-harness/judgment/phase_a_semantic_run.py forseti-harness/judgment/semantic_evidence_integration.py forseti-harness/runners/run_semantic_evidence_integration.py
python -m pytest forseti-harness/tests/unit/test_phase_a_semantic_run.py forseti-harness/tests/unit/test_semantic_evidence_integration.py forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m pytest forseti-harness/tests/unit -q
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_placement.py --strict --base origin/main
python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
python .agents/hooks/check_handoff_pointers.py --strict --base origin/main
python .agents/hooks/check_review_routing.py --strict --base origin/main
python .agents/hooks/check_map_links.py --strict --base origin/main
git diff --check
```

Observed baseline at `87fd7f5` before any patch of yours, so you can separate a
pre-existing failure from one you introduce: the three targeted test files pass
(323 tests); the full `tests/unit` suite collects 4751 tests with exactly one
failure, `test_install_local_hooks.py::test_installer_repairs_foreign_worktree_hook_binding`,
which fails only where `pwsh` is absent and is outside the patchable set. On a
Windows host with PowerShell present that test is expected to pass — if it fails
there, that is a real finding, not this disclosure. The six hook gates above and
`git diff --check` were observed green against the landed diff. This baseline was
taken on Linux with Python 3.12; the harness requires Python >= 3.12, and the
teardown path uses `shutil.rmtree(onexc=...)`, which does not exist on 3.11.

If a confirmed defect requires changing the frozen architecture boundary,
return `NEEDS_ARCHITECTURE_PASS`, leave no partial diff for that defect, and
name the minimum owner decision. Otherwise author the smallest complete patch
inside the named set and add regression coverage for every accepted defect.

## Return

Return:

1. receiver binding, lineage, and reviewed revision;
2. severity-ordered findings with file/line evidence, impact, and closure
   condition;
3. the exact bounded diff, or explicit no-patch;
4. each same-vendor lead as independently confirmed, rejected, or unresolved;
5. all validation and real-check observations;
6. verdict `clean_for_architect_adjudication`,
   `patched_for_architect_adjudication`, `NEEDS_ARCHITECTURE_PASS`, or
   `blocked`;
7. residual risk.

State explicitly that the return is decision input only and that the home
architect must adjudicate every finding and every changed line before anything
is kept. The return asserts no approval, readiness, seal eligibility, or merge
authority.
