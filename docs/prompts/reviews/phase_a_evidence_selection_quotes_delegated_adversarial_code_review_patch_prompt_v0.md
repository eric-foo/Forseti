# Phase A Evidence Selection And Exact Quotes Delegated Review-And-Patch Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated code review-and-patch prompt
scope: Cross-vendor adversarial review and bounded patch of the Phase A v3 evidence-selection and exact-quote consumer at commit fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c.
use_when:
  - Couriering the Phase A evidence-selection and exact-quote consumer for its required post-implementation review.
  - Attacking candidate accounting, source-role separation, engagement ordering, origin grouping, and quote exactness before acceptance.
authority_boundary: retrieval_only
branch_or_commit: codex/phase-a-selection-quotes @ fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
stale_if:
  - The reviewed implementation moves off fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c.
  - Any target file changes after that commit, other than this later review prompt.
  - The owning claim-support, semantic-integration, or delegated-review authority changes before review.
```

## Commission

Run a de-correlated, different-vendor `delegated_code_review_and_patch` pass on
the exact implementation commit. Inspect the repository directly. The author
family is OpenAI; the controller must be a different upstream vendor/model
lineage. This is a who-constraint, not a runtime-model recommendation. If that
constraint or direct repository access is unavailable, return
`BLOCKED_REVIEW_ROUTE` without substituting same-vendor review.

```yaml
output_mode: review-report
edit_permission: patch-only
review_routing_status: routed
target_revision: fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c
reviewed_diff: 7b0cf24087faadd1f20314264feb3eacaebdda1d..fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c
report_destination: docs/review-outputs/adversarial-artifact-reviews/phase_a_evidence_selection_quotes_delegated_review_v0.md
patch_destination: a clean reviewer-owned branch/worktree created from the exact target revision
author_home_model_family: OpenAI
controller_model_family: operator_to_fill_different_vendor_required
de_correlation_bar: cross_vendor_discovery
```

Do not push, merge, publish, modify historical production outputs, rerun the
60,901-item semantic extraction/reconciliation, or create packet v4. Patch only
the five target files below. Other sources are read-only and may be cited as a
scope blocker.

## Fitness Reference And Success Contract

Goal: Phase A presents the strongest commercially useful, source-grouped
customer evidence—including relevant Amazon/Revolve and qualified TikTok
audience material—with exact verified quotes, while creator-authored popularity
stays separate influence context and no admitted evidence silently disappears.

The smallest-complete design is an optional consumer over immutable
`phase_a_evidence_packet_v3`, not a new evidence authority. It must:

- account for every admitted candidate exactly once before display selection;
- keep customer truth support separate from creator-authored influence;
- cap display at ten independent customer origins and three creator-influence
  origins while retaining the complete disposition inventory and hash;
- preserve support, counter, a distinct quiet item when available,
  unknown-engagement and nominated safety/costly-behavior lanes;
- group by source role and venue, with one Reddit section and separate retailer
  sections;
- use engagement only inside one source-native venue/role/metric bucket;
- preserve raw engagement literally and never create a cross-platform score;
- bind source bodies by packet/bundle hash, evidence ID, artifact ID, and source
  ref, then accept only a contiguous exact quote of at most 220 characters;
- keep missing bodies visibly `quote_unavailable`; and
- make zero provider calls inside repository runners.

Non-goals: Deliver calibration, new capture, editorial capture, full semantic
replay, token/latency optimization, storage work, prevalence/causal/commercial-
pull claims, or estimated similar-experience counts.

## Exact Targets

- `forseti-harness/judgment/phase_a_evidence_selection.py`
- `forseti-harness/runners/run_semantic_evidence_integration.py`
- `forseti-harness/tests/unit/test_phase_a_evidence_selection.py`
- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
- `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

Review the Python implementation/tests with `workflow-code-review`. Review the
two owning documents for behavioral consistency, duplication, and false claims
with `workflow-adversarial-artifact-review`. Load and apply the repository's
delegated-review instructions before patching. If either required review method
is unavailable, report that limitation rather than emulating a strict verdict.

## Required Attacks

1. Find any path that omits, duplicates, reorders, or cross-attaches an admitted
   candidate while still finalizing.
2. Try to launder `creator_authored` into customer support/counter or collapse
   TikTok audience and creator material into one source role.
3. Attack product/variant/axis admission, scalar versus list columns, explicit
   semantic/unresolved refs, multiple packet lineages, and source/corpus-scoped
   independence keys.
4. Attack the cap: support/counter/quiet/unknown/safety/costly lanes, multiple
   meanings from one origin, and more protected groups than available slots.
5. Attack engagement ordering with Reddit strings, Sephora
   `{negative,positive,total}` helpful-vote maps, unavailable values, malformed
   maps, and incomparable platform metrics. Confirm only Sephora `positive`
   helps order the Sephora bucket and raw objects stay unchanged.
6. Attack venue grouping with Reddit host variants, TikTok host/ID variants,
   Sephora/Amazon/Revolve identifiers, Windows source refs, and unknown venues.
7. Attack bundle and quote binding with stale files, wrong bundle hash,
   evidence/artifact/ref mismatch, missing bodies, one-character mutations,
   non-contiguous inserted ellipses, source-native ellipses, overlength quotes,
   duplicates, foreign IDs, and quote-result reordering.
8. Challenge whether exact-but-irrelevant quotes can be mistaken for semantic
   quality. Runtime must not use lexical overlap as truth; quality adjudication
   must remain visible.
9. Challenge deterministic/idempotent finalization and runner overwrite guards.
10. Check whether the new module is genuinely the smallest complete extension
    of the existing consumer or has created parallel authority/avoidable
    ceremony.

The most plausible false green is structurally exact output whose selected
quote is irrelevant or whose engagement sorter silently ignores a valid native
shape. Do not let aggregate blind preference waive any factual, lineage, role,
relation, quote, or candidate-accounting failure.

## Evidence To Confirm, Not Trust

- Focused selection/consumer/semantic suites: 249 passed.
- Full `forseti-harness` suite: passed at the target worktree; existing warnings
  only.
- Retrieval-header, placement, repo-map freshness, and map-link checks passed;
  repo-map freshness emitted only its advisory for the two new files.
- Real pilot receipt:
  `C:\tmp\forseti-phase-a-selection-quotes-20260818-v0\pilot_receipt_v2.json`,
  raw SHA-256
  `9e3e8d8af6c8772b7fbf23a5ad8fbf26960edd7c66878ada2632d734f6286503`.
- Pilot artifacts and hashes are recorded inside that receipt. It records 836
  authoritative hydration semantic units (784 Reddit; 43 Sephora; 8 Amazon; 1
  Revolve), a 13-row provider slice, all 61 reaction candidates, and the exact
  finish/repurchase quote.
- Blind quality used three mirrored target comparisons plus six identical-arm
  calibration pairs. Calibration was 6/6 ties; quote-enriched hydration and
  reaction won both positions; finish/repurchase tied. This isolates quote
  enrichment on selected rows and does not prove selected membership beats
  every legacy proposition presentation.
- Provider total in the final receipt: 203,517 input tokens, 4,970 output
  tokens, zero cached input, 1,011 reasoning-output subset, and 123,231 ms wall
  time across seven calls. These are descriptive, not adoption economics.

Accepted pre-review residuals: 823 of the 836 hydration candidates were
deterministically admitted/accounted but not provider-relabeled in the bounded
pilot; provider and blind judge were same-vendor; quote semantic relevance is a
quality-adjudication obligation rather than a deterministic lexical gate.

## Validation And Return

After any patch, rerun:

```powershell
$env:PYTHONPATH='forseti-harness'
python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py
python -m pytest -q forseti-harness
python .agents/hooks/check_retrieval_header.py --changed --strict
python .agents/hooks/check_repo_map_freshness.py --changed --strict
python .agents/hooks/check_placement.py
python .agents/hooks/check_map_links.py --strict
git diff --check
```

Return findings first with severity, confidence, exact evidence, minimum closure
condition, and next authorized action. Include considered-and-defended attacks.
If patching, report the patch commit and validation evidence, but do not call it
accepted or merge-ready. The home/Chief Architect must adjudicate the review,
diff, verdict, and residuals as claims before any landing decision.
