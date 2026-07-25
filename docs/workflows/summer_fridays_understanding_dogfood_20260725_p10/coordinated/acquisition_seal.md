# Summer Fridays p10 Understanding Acquisition Seal

```yaml
retrieval_header_version: 1
artifact_role: Intelligence Cycle acquisition seal
scope: >
  Manual CO0 whole-gate closeout for the cold Summer Fridays p10 Understanding
  Acquire & Seal run, plus the current separately authorized recovery
  adjudication.
use_when:
  - Verifying whether Summer Fridays p10 Deliver is authorized.
  - Auditing the material routes that block the p10 acquisition gate.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/recovery_acquisition_adjudication.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/turn_a_acquisition_record.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/commission_board.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co1_company_core_identity.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co2_retail_portfolio.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co3_customer_community_depth.md
stale_if:
  - Any p10 acquisition artifact or preserved evidence byte changes.
  - A separately commissioned recovery acquisition supersedes a blocked route.
```

```yaml
current_lifecycle_status: ACQUISITION_BLOCKED_COV006_UNCAPTURED
intelligence_cycle_phase_status: UNDERSTANDING_RECOVERY_ACQUISITION_PARTIAL
resume_allowed: true_for_cov006_recovery_acquisition
correct_intake_result: BLOCKED_ACQUISITION_INCOMPLETE
original_seal_state: BLOCKED_ACQUISITION_INCOMPLETE
recovery_adjudication_locator: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/recovery_acquisition_adjudication.md
```

The `phase_acquisition_seal` block below is the preserved original p10 seal.
Its Sephora blocker has been superseded by the recovery adjudication; its
historical observations and packet accounting remain unchanged.

```yaml
phase_acquisition_seal:
  cycle_id: summer_fridays_understanding_dogfood_20260725_p10
  commission_id: summer_fridays_understanding_p10_20260725
  phase: understanding
  turn: acquire_and_seal
  bound_question: What does current public evidence show about Summer Fridays as a company and brand system—its identity, ownership, leadership, proposition, offering architecture, markets and channels, chronology and material events, customer and community response, and bounded outside-in context—and which observable tensions warrant later Problem Framing?
  intended_consumer: Forseti Intelligence Cycle Deliver turn
  intended_use: decision-neutral broad company understanding that is Problem-Framing-ready
  phase_scope: Current outside-in company model acquired cold under the p10 seal-hardening contract.
  commission_board_locator: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/commission_board.md
  acquisition_record_locator: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/turn_a_acquisition_record.md
  outcome_signals:
    - question_fit
    - evidence_foundation
    - reasoning_quality
    - honest_uncertainty
    - implications_and_foresight
    - communication_efficiency
  resolved_routes:
    - source_or_venue: company-owned Summer Fridays surfaces
      information_job: identity, proposition, authorization, public parent denominator, markets, channels, chronology, and incident response
      required: true
      route_identity: fresh p10 direct HTTP, clean public products JSON, and one bounded archive retry
      route_authority: current Capture method and company-owned source boundary
      recipe_or_recon_pointer: forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
      disposition: used
    - source_or_venue: current company and trade sources
      information_job: ownership, leadership, financing chronology, and bounded outside-in calibration
      required: true
      route_identity: fresh p10 exact-source captures with attributed claim ceilings
      route_authority: current Intelligence Cycle source and uncertainty contract
      recipe_or_recon_pointer: forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
      disposition: used
    - source_or_venue: Sephora US
      information_job: complete selected-retailer grid, exact non-bundle PDP baseline, provider/corpus identity, Helpful/Recent reviews, and Q&A onboarding
      required: true
      route_identity: admitted Sephora grid/PDP capture plus canonical onboarding companion
      route_authority: forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
      recipe_or_recon_pointer: forseti/product/spines/capture/core/source_families/retail_pdp/README.md
      disposition: blocked
    - source_or_venue: REVOLVE
      information_job: complete selected-retailer grid, exact non-bundle PDP baseline, provider/corpus identity, and Most Recent onboarding breadth
      required: true
      route_identity: admitted REVOLVE grid/PDP capture and review-corpus completion
      route_authority: forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
      recipe_or_recon_pointer: forseti/product/spines/capture/core/source_families/retail_pdp/README.md
      disposition: used
    - source_or_venue: Reddit
      information_job: mandatory bounded customer/community scout
      required: true
      route_identity: three subreddit-scoped discovery surfaces and 13 exact old-Reddit threads
      route_authority: current Reddit source-family route and Capture method
      recipe_or_recon_pointer: forseti/product/spines/capture/core/source_families/social_media/reddit/README.md
      disposition: used
  scan_receipts:
    - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co1_company_core_identity.md
    - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co2_retail_portfolio.md
    - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co3_customer_community_depth.md
  capture_receipts:
    - role: company_owned_portfolio
      locator: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co1
      result: 149 parent objects accounted exactly; 34 normalized beauty-product families; typed residuals retained
    - role: selected_retailer_portfolio
      locator: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co2\portfolio_corpus_board_v1.json
      result: 81 grid rows; 73 of 75 required exact non-bundle PDP baselines; two blocked Sephora targets
    - role: customer_community
      locator: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co3\community\reddit_batch_001\batch_summary.json
      result: 13 fresh thread families; 202 comment rows after consolidation; bounded non-representative interpretation
    - role: revolve_review_corpora
      locator: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co3\retailer_reviews\revolve_completion_002\completion-receipt.json
      result: 33 of 33 contexts terminal; 559 occurrences; 528 unique native IDs; 31 independent evidence families
    - role: sephora_review_and_qa
      locator: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co3\retailer_reviews\sephora_onboarding_route_failure.md
      result: blocked before live companion acquisition for all 40 verified contexts because parent configuration was not retained
  provenance_index:
    - C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co1
    - C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co2\raw_provenance_index_v1.json
    - C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co3
  material_gaps_and_failures:
    - Sephora `P525609` and `P525633` lack admitted exact PDP parents after bounded attempts.
    - All 40 verified Sephora non-bundle contexts lack canonical Helpful, Recent, and Q&A onboarding responses.
    - Sephora tenant/store, collection identity, overlap, deduplication, and syndication remain unresolved.
    - Six selected-retailer bundles/sets lack baseline-bound corpus identity.
    - Four retailer rows do not match the current company-owned parent ledger.
    - Company leadership, ownership, incident, and outside-in calibration retain the explicit ceilings in CO1.
    - REVOLVE review bodies are sparse and community evidence is bounded and non-representative.
    - Commission-stage coverage row `COV-006` commissioned category-aware hidden-venue `search_discovery`, but no specialist terminal or integrated artifact records a route or disposition; p10 coverage accounting leaves that row gapped.
  blocked_requirements:
    - complete selected-retailer exact PDP baseline coverage
    - complete bounded Sephora distinct-corpus onboarding
    - complete selected-retailer customer-evidence acquisition
  accepted_route_residuals:
    - Company-owned HTML packets retain challenge-classifier residuals; strict portfolio counting comes from the clean public products JSON.
    - The single bounded outside-in Forbes calibration packet is also runner-`access_failed` behind a `datadome` block shell; its article text was manually inspected from the preserved body and remains attributed to Forbes/YipitData rather than promoted to audited fact.
    - REVOLVE complete breadth does not compensate for the blocked Sephora route.
    - Six bundle/set corpus identities and four unmatched retailer rows remain typed without false completion credit.
  direct_manifest_verification:
    manifest_count: 158
    preserved_file_count: 556
    missing_file_count: 0
    hash_mismatch_count: 0
    size_mismatch_count: 0
  seal_state: BLOCKED_ACQUISITION_INCOMPLETE
  acquisition_gate: blocked
  deliver_allowed: false
  sealed_at: "2026-07-25T05:46:06.7088499+08:00"
  delegated_review_adjudication:
    controller_family: Anthropic Claude
    reviewed_revision: 899c9d081a726a6a905755073dbdcd21589bbd75
    adjudication: accepted_with_home_modifications
    accepted_findings: [AR-01, AR-02, AR-03, AR-04]
    reported_not_patched: [AR-05, AR-06]
    gate_effect: none
    adjudicated_at: "2026-07-25T15:20:13.6213385+08:00"
  next_authorized_step: Stop this p10 run. A separately authorized recovery acquisition may repair the Sephora parent/companion route; Turn B, a company report, and p07 comparison remain forbidden.
```

`BLOCKED_ACQUISITION_INCOMPLETE`.

The run reached a truthful, evidence-backed stop. Deliver is not authorized.
REVOLVE completion, community evidence, and a verified raw corpus do not erase
the material selected-Sephora PDP and onboarding failures.

## Current Recovery Adjudication

The Sephora route is recovered: all 40 admitted canonical parents now have one
successful Helpful/Recent/Q&A companion disposition, including honestly
preserved source-declared zero-result contexts. The two missing mini fragrance
PDPs are accepted non-strategic middle-of-curve residuals under the current
materiality rule.

Deliver remains blocked because the COV-006 probe found two material California
Proposition 65 notices that have not yet been preserved and adjudicated into
the acquisition record. The current controlling state is therefore
`BLOCKED_ACQUISITION_INCOMPLETE`, with COV-006 as the remaining blocker.
