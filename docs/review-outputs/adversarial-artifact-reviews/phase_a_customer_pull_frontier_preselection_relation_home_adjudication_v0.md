---
retrieval_header_version: 1
artifact_role: Home adjudication of the cross-vendor Phase A customer-pull frontier and v7 preselection relation review
scope: Findings and uncommitted patch returned against implementation revision 74865c03
use_when:
  - Auditing which delegated findings were kept, modified, rejected, or deferred before landing the customer-pull frontier.
authority_boundary: retrieval_only
open_next:
  - docs/review-outputs/adversarial-artifact-reviews/phase_a_customer_pull_frontier_preselection_relation_delegated_review_v0.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
---

# Phase A customer-pull frontier and v7 preselection relation — home adjudication

reviewed_by: Anthropic controller
authored_and_adjudicated_by: OpenAI Codex
reviewed_revision: `74865c03d44c55d2c1e3c125461c757c3f5c414e`

The delegated findings, citations, diff, and verdict are decision input only.
They are not inherited as approval or premises.

## Verdict

**Accept with bounded home modification.** Keep the delegated CR-01 runtime
guard and falsifier and the AR-01 v6/v7 documentation correction. Close CR-02
by recording and verifying every subject-filtered proposition plus reconciled
input, matched, and filtered counts. Close CR-03 by limiting the new explicit
relation definitions to `bounded_point` selections; a default v6 selection now
reproduces the exact pre-change prompt hash. Do not alter discovery ordering for
CR-04 without a separate product decision. CR-05 requires no action.

The operator explicitly excluded the review-return latency discussion from this
adjudication. It changed no code, tests, workflow, contract, or decision.

## Finding dispositions

| Finding | Decision | Reason |
|---|---|---|
| CR-01: confirmation bypassed first-pass row guards | Keep | A replacement label must pass the same creator-layer, relation-word, and reason-length checks as the label it replaces. |
| CR-02: subject filtering was invisible | Keep diagnosis; modify closure | Preserve subject scoping, but expose every excluded proposition and reconcile input, matched, and filtered counts. No historical production artifact is rewritten. |
| CR-03: shared prompt edit changed legacy replay hashes | Keep diagnosis; modify closure | The extra definitions are needed for frontier-bound points, not default legacy routes. Scoping them restores the parent prompt hash without weakening v7. |
| CR-04: every reported behavior sorts first | Defer as explicit product residual | This is a real priority question, but the current contract does not rank the earning signals and the review supplied no safe subtype distinction between weak trial and strong purchase behavior. |
| CR-05: constant corpus hash in one origin-count tuple | No action | It is dead within a single packet but does not change the counted independence keys or behavior. |
| AR-01: documents called live v6 routes historical | Keep | The live runner still stamps v6 outside the frontier route; the operating text must say so. |

## Kept boundary

The kept change is limited to the evidence-selection runtime, its focused tests,
the owning Phase A workflow, and the semantic-evidence contract. Packet v3, the
thirteen-origin cap, source-role separation, existing production outputs, and
provider behavior are unchanged. The prior dogfood frontier is superseded only
as an ephemeral verification artifact because the accounting fields change its
hash; no completed production output is modified.

## Observed checks before final landing validation

- focused selection, consumer, and semantic-integration suites pass;
- the real 105-proposition Summer Fridays packet rebuilds as 8 retailer-first,
  93 community-discovery, 4 nonpromoted, and 0 subject-filtered propositions;
- the rebuilt frontier hash is
  `b54bfdd2939554e62c273484769e6f765eed93ae2b95158ba4a23f0d35a9510f`;
- an identical default selection produces prompt SHA-256
  `50ce4b31dbe69db5de2419a0fdc31b5648043d1b5792f9c4bda0de84a4fdd472`
  at both the pre-change parent and the adjudicated worktree;
- module compilation and `git diff --check` pass;
- the complete `python -m pytest -q forseti-harness` run exits zero with only
  the existing skips; and
- the repository documentation gate matrix passes 24/24 after both review
  records are present.

## Accepted residuals

- `reported_behavior` still sorts ahead of stronger recurrence or engagement
  even when it describes weak behavior such as trial; changing that requires a
  product-owned distinction among behavior types rather than a blind reorder.
- The first-pass guard set is reused conceptually, not through one shared helper;
  a future new guard could be added to one pass only. Current regression coverage
  catches the three observed omissions.
- Confirmation-frontier membership and final display eligibility remain two
  expressions of the same policy. Drift fails loudly at finalization, but late.
- Delegate-authored lines are independently discovered but not independently
  adjudicated; home-authored closures are validated locally and still rely on
  normal landing review and CI.
