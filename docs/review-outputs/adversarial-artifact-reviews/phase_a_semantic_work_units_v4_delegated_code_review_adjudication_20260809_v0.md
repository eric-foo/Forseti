---
retrieval_header_version: 1
artifact_role: Home-architect adjudication of the cross-vendor Phase A semantic work-units v4 delegated code review and patch
scope: Findings and working-tree patch returned against reviewed revision 8c4022ca, including the home correction for cross-platform no-replace publication
use_when:
  - Auditing why the delegated patch was kept, modified, or rejected before landing the bundle-v4 work unit.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/reviews/phase_a_semantic_work_units_v4_delegated_code_review_patch_prompt_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v2/README.md
---

# Phase A semantic work units v4 — delegated review adjudication

reviewed_by: Anthropic Claude Opus 5
authored_by: OpenAI Codex / GPT-5

Review findings are decision input only. They are not approval, validation,
mandatory remediation, or executor-ready patch authority.

## Binding and verdict

The eligible Anthropic delegate reviewed clean revision
`8c4022cac83b5a9361f3f1668727cf95716149dc`, with required implementation
revision `1f1b1fbea1b1da60167814996b57cbb4d41d6fa0` proven as an ancestor, and
left an uncommitted patch inside the named set.

Home verdict: **accept with bounded home modification**. Findings 1–4 and 6
and their delegate-authored patches are kept. Finding 5's diagnosis is kept,
but its proposed residual-only disposition is rejected because repository CI
and automation run on Ubuntu while the contract made an unqualified
no-overwrite claim. The home patch replaces platform-dependent `os.rename`
with atomic same-directory no-replace hard-link creation and fails closed when
the filesystem cannot provide it. No architecture expansion was required.

## Finding dispositions

| Finding | Decision | Reason |
|---|---|---|
| F1: optional source-v3 fields caused a v4 `KeyError` | Keep | The v3 validator explicitly admits their absence with defaults. V4 must render the same admitted source rather than fail ugly. |
| F2: context index rebuilt once per expanded leaf | Keep | The real 59,225-leaf path was quadratic. One shared immutable index preserves exact bytes and reduces observed rematerialization from a 388.4-second upper-bound baseline to 4.3 seconds. |
| F3: dangling/duplicate accounting references | Keep | Accounting-by-reference is new in v4 and must be an exact bijection over admitted evidence at every bundle-consuming validator. |
| F4: blocked-row inspection text dropped | Keep | Source v3 permits retained inspection text; accounting-by-reference has no other carrier for a non-assessable row. |
| F5: POSIX rename can overwrite an accepted response | Keep diagnosis; modify closure | Ubuntu is an active repository runtime. Atomic no-replace hard-link creation is the smallest cross-platform closure; unsupported filesystems fail closed. |
| F6: worker manifest hard-coded `3` | Keep | The manifest must report the hash-bound projection's observed worker count rather than restate a constant. |

The delegate's statement that no receipt patch was needed is rejected. Finding
2 made the v2 receipt's claim that combined rematerialization still takes
minutes false. The receipt now separates slow source reconstruction from the
fixed 4.3-second v4 rematerialization path and records the measurement caveat.

## Kept patch boundary

Delegate-authored changes are limited to:

- `forseti-harness/judgment/semantic_evidence_integration.py`;
- `forseti-harness/runners/run_semantic_evidence_integration.py`;
- `forseti-harness/tests/unit/test_semantic_evidence_integration.py`.

Home modifications are limited to the portable publication closure, its test
and contract wording, the corrected v2 dogfood receipt, and this adjudication
record. Historical source v3, bundle-v3 reproduction, the acquisition seal,
the 150,000-byte ceiling, and the one-terminal-batch gate are unchanged.

## Observed validation

After combining the delegate patch and home modifications:

- focused semantic-integration and Phase A run suites passed;
- the complete `forseti-harness/tests/unit` sweep passed with four skips;
- module compilation passed;
- the delegate independently reproduced the 60,901 / 59,225 / 513 full-bundle
  accounting, 171 / 171 / 171 worker split, every stored prompt byte, the
  206-leaf calibration, both reconciliation levels, terminal view hash, and
  evidence-packet hash;
- the optimized rematerializer preserved source SHA-256
  `156cb1659e418f8ba2e7e4534cceeacac880f2f0e2efe3f7ccea2f6933bad252`.

Final repository gates remain required after this record is added and before
commit/landing.

## Accepted residuals

- Full-corpus semantic judgment remains `0 / 513`; the completed 206-leaf
  calibration proves the method, not full execution.
- Convergence of the full corpus to the required one terminal prompt batch is
  unproven and remains fail-closed.
- Source reconstruction still rereads and rehashes large pinned acquisition
  artifacts and remains the material latency surface.
- Cross-venue exact-public-handle credit collapse is tested but was not
  live-demonstrated by the Summer Fridays corpus.
- A rehashed bundle that removes matching accounting rows, evidence units, and
  counters together is not detected by the new v4 reference-bijection check;
  that broader denominator-integrity class predates v4 and is unchanged.

The delegate-authored patch lines and the home-modified publication lines do
not gain independent discovery merely by being retained. Their support is the
cross-vendor defect discovery, regression coverage, complete unit sweep, real
artifact reproduction, this explicit adjudication, and the normal CI/branch
protection path.
