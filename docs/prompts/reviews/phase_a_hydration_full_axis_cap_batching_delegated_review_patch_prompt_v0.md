# Phase A Hydration Full-Axis Cap And Batching Delegated Review Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated code review-and-patch prompt
scope: Cross-vendor adversarial review of the Phase A full-axis origin-cap and exact named-row relation batching change.
use_when:
  - Reviewing the measured fifteen-origin hydration presentation setting.
  - Attacking exact candidate accounting and named-row batch rehydration before landing.
authority_boundary: retrieval_only
branch_or_commit: codex/phase-a-hydration-pack-cap-pilot @ 9cf9f2ccfc350447754beee9f4b700935ce219ed
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
stale_if:
  - The reviewed implementation moves off 9cf9f2ccfc350447754beee9f4b700935ce219ed.
  - Any exact target file changes after the reviewed commit other than this later courier prompt.
  - The owning claim-support, semantic-integration, or delegated-review authority changes before review.
```

## Commission

Run a de-correlated, different-vendor `delegated_code_review_and_patch` pass on
the exact implementation commit. The author family is OpenAI; the reviewer must
come from a different upstream vendor/model lineage and must inspect the
repository directly. If either condition is unavailable, return
`BLOCKED_REVIEW_ROUTE` without substituting a same-vendor review.

```yaml
output_mode: review-report
edit_permission: patch-only
review_routing_status: routed
target_revision: 9cf9f2ccfc350447754beee9f4b700935ce219ed
reviewed_diff: 1c886a723c853f91490d1fd3b3531a1abca19bc7..9cf9f2ccfc350447754beee9f4b700935ce219ed
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_hydration_full_axis_cap_batching_review_v0.md
patch_destination: a clean reviewer-owned branch/worktree created from the exact target revision
author_home_model_family: OpenAI
controller_model_family: operator_to_fill_different_vendor_required
de_correlation_bar: cross_vendor_discovery
```

Do not push, merge, publish, edit historical production outputs, rerun source
capture or semantic extraction/reconciliation, create packet v4, or change the
value-selection policy. Patch only the five exact targets below. Other files
are read-only evidence or scope blockers.

## Goal And Bound Success

Goal: a commercially useful full hydration-axis pack uses the smallest measured
sufficient number of independent customer origins and accounts for every
admitted Phase A candidate without a long model response silently losing tail
rows.

The implementation keeps packet v3 and the ordinary ten-origin default. One
selection may explicitly bind one through twenty customer origins; the measured
full-axis hydration spec binds fifteen because both mirrored judgments found
fifteen materially better than ten and twenty tied with fifteen. Creator
influence remains separately capped at three.

Large non-value relation work may opt into hash-bound batches of at most 300
candidates. Each response returns one required `row_NNNN` relation property per
ordered batch candidate. The no-provider finalizer reattaches literal candidate
identity and facts, requires the exact batch and row-key sets plus contiguous
complete coverage, and then uses the ordinary deterministic origin selection
and exact-quote path. Value selection remains literal-ID based.

Success requires:

- all 836 hydration candidates accounted exactly once;
- no missing, invented, duplicated, cross-batch, or wrongly reattached row;
- exact source quote, ref, date, engagement, product/variant, and origin facts;
- fifteen origin slots, not fifteen evidence rows;
- protected customer evidence visible or a loud cap failure;
- creator-authored evidence unable to become customer support/counter;
- engagement used only within source-native venue/role/metric buckets;
- ten remaining the default outside an explicitly configured selection; and
- no token-saving claim for batching.

## Exact Targets

- `forseti-harness/judgment/phase_a_evidence_selection.py`
- `forseti-harness/runners/run_semantic_evidence_integration.py`
- `forseti-harness/tests/unit/test_phase_a_evidence_selection.py`
- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Review Python with `workflow-code-review` and the two owning documents with
`workflow-adversarial-artifact-review`. Load the repository's delegated-review
authority before patching. Do not emulate a strict verdict if a required review
method is unavailable.

## Required Attacks

1. Mutate the batch manifest, embedded selection manifest, source files,
   candidate inventory, batch order, start indexes, counts, row keys, and
   response set. Find any mutation that still finalizes with a missing, foreign,
   duplicated, or wrongly attached candidate.
2. Test 299/300, 300/300, 236/236, empty, extra, reordered, and wrong-batch
   responses. Confirm object-key order cannot change identity and every required
   named slot is enforced by both schema and deterministic validation.
3. Attack the configurable cap with booleans, strings, zero, twenty-one,
   protected origins over cap, same-origin support/counter/adjacent rows, and
   creator rows. Confirm the cap counts origins rather than display rows.
4. Prove literal-ID behavior and value reason-code semantics remain unchanged;
   positional or batched value work must fail before provider use.
5. Challenge whether generic derived non-value reason labels weaken a downstream
   consumer or leak internal support/counter wording into customer display.
6. Attack runner no-overwrite behavior and response-directory completeness.
   Confirm the runner itself makes zero provider calls.
7. Challenge the measured cap claim: it is hydration-specific, fifteen is not a
   global default, and twenty adding rows without decision value cannot be
   rewritten as general evidence sufficiency.
8. Attack token and latency accounting. Cached tokens are not subtracted,
   reasoning is an output subset, and parallel critical-path latency must not be
   presented as the actual serial wall time or as a token saving.
9. Check whether the implementation is the smallest complete extension of the
   existing v3 consumer rather than a second evidence authority or packet v4.

The highest-loss plausible false green is a complete-looking fifteen-origin
artifact built after one batch silently omits or shifts the last candidate.
Aggregate quality or latency may never waive candidate, lineage, quote, role,
or protected-lane correctness.

## Evidence To Confirm, Not Trust

- Full `python -m pytest -q forseti-harness` exited zero at the author worktree;
  existing skips and warnings only.
- Focused selection/consumer/semantic tests passed.
- Real receipt:
  `C:\tmp\forseti-phase-a-hydration-cap-pilot-20260820-v0\experiment_result_v1.json`,
  raw SHA-256
  `74149af3d24c8ba742d38ec75bb9e5e2bd075570fd29d68f31189d143608b2e9`.
- Long response falsification: one 836-row positional array returned 824;
  two 418-row arrays returned 417 and 418; 300/300/236 arrays returned
  299/299/236. Required named slots returned 300/300/236 exactly.
- Accepted artifact SHA-256:
  `32a54b1dfd93fdd298fe4b5374160df73c7c720b417c3253d127c868f4223a06`.
  It carries 836 dispositions, fifteen origins, seventeen exact quotes, ten
  support origins, six counter origins, and Reddit/Amazon/Sephora venues.
- The production route used 212,140 input plus 32,563 output = 244,703 logical
  tokens across four provider calls; cached input was zero and reasoning was an
  output subset. Relation batching used 35.092% more logical tokens than the
  exact literal-ID relation arm, while its parallel relation critical path was
  51.736% lower. It is a completeness/parallel-latency trade.
- The named-batch pack shared sixteen of seventeen displayed rows with the
  prior cap-fifteen pack. One valid counter changed from a 368-point
  variant-specific Pink Guava comparison to a 276-point generic drying report.
  A mirrored same-vendor preference check was position-unstable and is not a
  quality pass.

Accepted pre-review residuals: same-vendor provider/judge; hydration-only cap
evidence; no TikTok audience evidence in this full-corpus hydration packet;
35.092% relation-token increase; high-reasoning provider calls; and
position-unstable named-versus-prior pack preference.

## Validation And Return

After any patch, run the focused selection/consumer/semantic tests, the complete
`forseti-harness` suite, Python compilation, the changed-path placement,
retrieval-header, map-link, prompt-output, harness-coupling, and review-routing
gates, plus `git diff --check`.

Return findings first with severity, confidence, exact evidence, minimum closure
condition, and next authorized action. If patching, return the patch commit and
validation evidence, but do not call it accepted or merge-ready. Home
adjudication owns final acceptance and landing.
