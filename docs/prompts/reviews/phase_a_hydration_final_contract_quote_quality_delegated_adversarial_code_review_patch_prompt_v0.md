# Phase A Hydration Final-Contract Quote Quality Delegated Adversarial Code Review + Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated adversarial code review-and-patch prompt
scope: >
  Cross-vendor attack on the context-complete exact-quote prompt correction and
  its fresh matched serial/parallel hydration proof.
use_when:
  - Reviewing the post-batching hydration final-contract proof before merge.
  - Attacking exact-quote completeness, false unavailability, and the measured parallel latency claim.
authority_boundary: retrieval_only
branch_or_commit: codex/phase-a-hydration-pack-cap-pilot @ 2186312c1c5bd70068995dc32b8e871a468dcbce
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
stale_if:
  - The reviewed implementation moves off 2186312c1c5bd70068995dc32b8e871a468dcbce.
  - Any exact target file changes after the reviewed commit other than this later courier prompt.
  - The final proof receipt no longer hashes to dc9420c0a43e07fa6df66b1b45b8a193759f6908b2ba7ac8c4b7fbc117c6dde3.
```

## Commission

Run a de-correlated, different-vendor `delegated_code_review_and_patch` pass on
the exact implementation commit. The author family is OpenAI; the reviewer must
come from a different upstream vendor/model lineage and inspect the repository
directly. If either condition is unavailable, return `BLOCKED_REVIEW_ROUTE`
without substituting a same-vendor review.

```yaml
output_mode: review-report
template_kind: review
edit_permission: patch-only
review_routing_status: routed
target_revision: 2186312c1c5bd70068995dc32b8e871a468dcbce
reviewed_diff: 390f7bdcf290e6929f541fe63fd50f5060c7236c..2186312c1c5bd70068995dc32b8e871a468dcbce
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_hydration_final_contract_quote_quality_adversarial_code_review_v0.md
patch_destination: a clean reviewer-owned branch/worktree created from the exact target revision
author_home_model_family: OpenAI
controller_model_family: operator_to_fill_different_vendor_required
de_correlation_bar: cross_vendor_discovery
```

Do not push, merge, publish, edit the receipt, edit historical or production
outputs, rerun source capture or semantic extraction/reconciliation, create a
packet v4, change the fifteen-origin hydration cap, change value policy, or add
a standing quote-retry stage. Patch only the four exact targets below. A report
may be written at the bound report destination. Other files are read-only
evidence; if correct closure requires a broader design, report
`NEEDS_ARCHITECTURE_PASS` rather than widening the patch.

## Goal And Success Boundary

The customer-facing hydration pack must preserve all 836 admitted candidates
while presenting fifteen independent truth origins with exact quotes that:

- directly substantiate every material part of the normalized meaning;
- retain nearby reversals, comparisons, formula/variant distinctions, and
  usage or timing conditions when they fit within 220 characters;
- do not begin with an unresolved pronoun when its nearby antecedent fits;
- do not become unavailable merely because optional non-reversing context does
  not fit; and
- never use a generic display label as evidence meaning.

The final parallel arm must remain exactly accountable, preserve stored source
facts, and keep creator influence separate. The latency claim is active
provider wall time for three relation calls genuinely issued together plus one
downstream quote call—not a serial estimate. The token comparison is
descriptive and must not be promoted into a concurrency saving.

## Exact Review Targets

```yaml
targets:
  - path: forseti-harness/judgment/phase_a_evidence_selection.py
    sha256: 7239f033077c85f5ae77d957a65ee2c6ca70e9d190affd175db4f0fa3a7b21c0
  - path: forseti-harness/tests/unit/test_phase_a_evidence_selection.py
    sha256: 6b7434f0334d18c22196cabeb34636bc9f22f010fa3aa7c7df35da34509e0a53
  - path: docs/workflows/phase_a_customer_evidence_completion_path_v0.md
    sha256: 42ebdbea5d2c7229951c8cdf9577971904044ac267a79f60e48ec3680ba1ac1b
  - path: forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
    sha256: e50ee7aca9498ef450b40251161c38a07b91c198fed0a2d970abc74a32a8156f
```

Primary proof receipt:

```yaml
path: C:\tmp\forseti-phase-a-hydration-final-contract-20260820-v0\experiment_result_v1.json
raw_sha256: dc9420c0a43e07fa6df66b1b45b8a193759f6908b2ba7ac8c4b7fbc117c6dde3
payload_sha256: fc3d96cf6b51d5ec2a9b5ab003b62948ac69c662d99c1230d7b5b694dcfc31fe
```

Read the raw artifacts and event JSONL named by the receipt. Do not accept the
chat summary or receipt arithmetic without re-deriving it.

## Required Attacks

1. **Quote completeness versus exactness.** Find cases where an exact substring
   can pass while omitting the claimed outcome, comparator, condition,
   reformulation baseline, reversal, or necessary antecedent. Also attack the
   opposite failure: a stricter prompt returning unavailable despite a valid
   under-220 source span.
2. **One-call prompt robustness.** Determine whether the locate-expand-verify
   instruction is the smallest complete boundary or merely overfits the two
   hydration false-unavailable examples. Try at least one distinct behavior
   family such as a comparator, third-person report, temporal condition,
   formula change, or mixed praise/criticism. Do not add a retry surface unless
   the current one-call design is actually falsified.
3. **Semantic authority.** Prove that `display_label` cannot make an irrelevant
   quote acceptable and that source-owned normalized meaning and companion
   qualifications remain the only semantic basis.
4. **Transport and source integrity.** Re-run the swapped equal-size batch,
   missing named row, same-length quote mutation, creator laundering, and
   packet/bundle/body-hash boundaries. Wrong-cause failures must reach the
   intended boundary first.
5. **Quality adjudication.** Inspect both final artifacts and the sealed mirrored
   judge inputs/outputs. Challenge the claim that the parallel artifact is
   materially better, including the judge's same-vendor and rubric dependence.
   A blind preference cannot waive an objective quote/ref/fact error.
6. **Economics and timing.** Re-derive all per-arm inputs, outputs, reasoning
   subsets, cached inputs, active call spans, the parallel relation critical
   path, 47.491% latency delta, −1.144% descriptive logical-token delta, and
   the separately excluded 408,351-token experiment overhead. Do not subtract
   cache or double-count reasoning.
7. **Committed provenance.** Verify that the committed implementation
   regenerates the exact final serial and parallel quote prompts/manifests used
   by the provider run. Reject a dirty-parent or stale-manifest claim.

## Known Observations To Attack, Not Trust

- Both final arms report 836 dispositions, fifteen truth origins, seventeen
  exact quotes, zero unavailable quotes, and zero influence origins.
- Serial reports 248,014 logical tokens and 742,019.840 ms active provider
  time. Parallel reports 245,176 logical tokens and 389,626.940 ms.
- Relation prompts and schemas are byte-identical between arms, but provider
  variation changed one selected origin and yielded thirteen versus twelve
  long-body quote rows. Token comparison is therefore descriptive.
- A rejected broad “self-contained” prompt made seven usable quotes
  unavailable. A later strict prompt still missed two known 181/184-character
  spans. The final one-call instruction returned all seventeen.
- Both final mirrored blind orderings preferred the parallel artifact, but the
  provider and judge were the same vendor and the run is one hydration sample.

## Validation Obligation

At minimum run:

```text
python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py
python -m pytest -q forseti-harness
python -m py_compile forseti-harness/judgment/phase_a_evidence_selection.py
git diff --check
```

Run the applicable strict documentation, placement, retrieval, map,
prompt-output, review-routing, and review-provenance gates. Provider reruns are
not required. If a patch materially changes the model-facing quote instruction,
report that a fresh matched provider recheck is required; do not inherit the
old receipt as proof of the changed prompt.

## Required Return

Return findings first, each with severity, confidence, exact source location,
failure mechanism, evidence, minimum closure condition, and next authorized
action. Include `considered_and_defended` for attacked candidates that held.
Then provide:

```yaml
review_summary:
  route_status:
  target_revision_verified:
  receipt_hash_verified:
  findings_count:
  patch_commit:
  validation:
  residuals:
  review_routing_status:
  user_action_needed:
```

The report and patch are advisory inputs for home-lane adjudication. They are
not approval, validation, mandatory remediation, merge authority, or
executor-ready authority outside this bounded commission. Do not push or merge.
