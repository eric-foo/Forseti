# Experiment Beauty Phase A Acquisition Seal

```yaml
retrieval_header_version: 1
artifact_role: Consumer-brand Understanding acquisition seal
scope: Experiment Beauty Phase A route accounting, material-saturation evidence, and independent-review gate state.
use_when:
  - Determining whether a separately commissioned Experiment Beauty Deliver may start.
  - Auditing Phase A collection coverage, source provenance, material saturation, or residual blockers.
authority_boundary: retrieval_only
open_next:
  - docs/research/experiment_beauty_collection_20260904_v0/coordinated/evidence_depth_ledger.json
  - docs/research/experiment_beauty_collection_20260904_v0/coordinated/semantic_evidence_integration_view.json
  - docs/research/experiment_beauty_collection_20260904_v0/coordinated/semantic_source_family_census.json
```

```yaml
phase_acquisition_seal:
  schema_version: phase_acquisition_seal_v3
  cycle_id: EXPERIMENT-BEAUTY-UNDERSTANDING-20260905-001
  commission_id: OWNER-EXPERIMENT-MATERIAL-SATURATION-20260905-001
  subject: Experiment Beauty
  authority_revision: a5861738c9ebe6a273075189cdf5acafd2e801c0
  acquisition_gate: blocked
  seal_state: BLOCKED_ACQUISITION_INCOMPLETE
  deliver_allowed: false
  deliver_started: false
  bound_question_preserved: true
  controller_placement:
    controller_actor: CO0
    placement: top_level
    worker_slots_required: 3
    worker_slots_available: 3
  route_capability_preflight:
    checked_before_network_capture: true
    google_serp:
      mode: persistent_fallback
      primary_route_ready: true
      queue_state_writable: true
      persistent_fallback_ready: true
    reddit_weekly_lake:
      reader_status: ready
    paid_ad_transparency:
      google_ads_transparency: ready
      meta_ads_library: ready
    tiktok_shop:
      trigger: required
      route_status: ready
    native_social:
      tiktok:
        trigger: required
        route_status: ready
      instagram:
        trigger: not_required
        route_status: not_checked_until_trigger
      youtube:
        trigger: required
        route_status: ready
  specialist_returns:
  - actor: CO1
    terminal_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
    status: TERMINAL_EXTERNAL_SOCIAL_COMPLETE
  - actor: CO2
    terminal_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co2_retailer_terminal.md
    sha256: c504b9d68510d6bd762e1084a53ce41a6f3962963cb285a296723cacd273f960
    status: TERMINAL_RETAILER_CORPUS_COMPLETE
  - actor: CO3
    terminal_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co3_community_terminal.md
    sha256: 97159d98f45ee9c5dbccab3371a1abf168d6bf7cedb53cec608bf48252f50c77
    status: TERMINAL_COMMUNITY_CORPUS_COMPLETE
  post_phase1_continuation_mode: full
  route_job_accounting:
  - route_id: serp_phase1
    phase: serp_phase1
    required: true
    material: true
    planned_job_ids: &id001
    - P1-BALANCED
    - P1-BEHAVIOR
    - P1-BRANDLESS
    - P1-CONDITION
    planned_count: 4
    completed_job_ids: *id001
    completed_count: 4
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/serp_phase1_ledger.json
    terminal_artifact_sha256: 2f5248dacf4716928311e69b096d3dd81c26fdbe182a701ac2cbc76de257eb2e
  - route_id: official_retailer_authorization
    phase: co1
    required: true
    material: true
    planned_job_ids: &id002
    - CO1-AUTH
    planned_count: 1
    completed_job_ids: *id002
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    terminal_artifact_sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
  - route_id: google_ads_transparency
    phase: co1
    required: true
    material: true
    planned_job_ids: &id003
    - CO1-GOOGLE-ADS-TERMINAL
    planned_count: 1
    completed_job_ids: *id003
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    terminal_artifact_sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
  - route_id: meta_ads_library
    phase: co1
    required: true
    material: true
    planned_job_ids: &id004
    - CO1-META-ADS-TERMINAL
    planned_count: 1
    completed_job_ids: *id004
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    terminal_artifact_sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
  - route_id: retailer_full_pdp
    phase: co2
    required: true
    material: true
    planned_job_ids: &id005
    - CO2-JUNIP
    - CO2-SEPHORA
    planned_count: 2
    completed_job_ids: *id005
    completed_count: 2
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co2_retailer_terminal.md
    terminal_artifact_sha256: c504b9d68510d6bd762e1084a53ce41a6f3962963cb285a296723cacd273f960
  - route_id: reddit_weekly_lake
    phase: co3
    required: true
    material: true
    planned_job_ids: &id006
    - CO3-REUSE
    planned_count: 1
    completed_job_ids: *id006
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co3_community_terminal.md
    terminal_artifact_sha256: 97159d98f45ee9c5dbccab3371a1abf168d6bf7cedb53cec608bf48252f50c77
  - route_id: reddit_community_scout
    phase: co3
    required: true
    material: true
    planned_job_ids: &id007
    - RFD-BALANCED
    - RFD-BEHAVIOR
    - RFD-BRANDLESS
    - RFD-CONDITION
    - CONT-RETAILER
    - CONT-SOCIAL
    planned_count: 6
    completed_job_ids: *id007
    completed_count: 6
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co3_community_terminal.md
    terminal_artifact_sha256: 97159d98f45ee9c5dbccab3371a1abf168d6bf7cedb53cec608bf48252f50c77
  - route_id: tiktok_shop
    phase: co3
    required: true
    material: true
    planned_job_ids: &id008
    - CO2-TIKTOK-SHOP
    planned_count: 1
    completed_job_ids: *id008
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co2_retailer_terminal.md
    terminal_artifact_sha256: c504b9d68510d6bd762e1084a53ce41a6f3962963cb285a296723cacd273f960
  - route_id: native_tiktok
    phase: co3
    required: true
    material: true
    planned_job_ids: &id009
    - CO1-NATIVE-TIKTOK
    planned_count: 1
    completed_job_ids: *id009
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    terminal_artifact_sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
  - route_id: native_youtube
    phase: co3
    required: true
    material: true
    planned_job_ids: &id010
    - CO1-NATIVE-YOUTUBE
    planned_count: 1
    completed_job_ids: *id010
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/specialists/co1_official_external_social_terminal.md
    terminal_artifact_sha256: a99270cc58ab4778f83fec1a4984886d300c248f3e11356a99ed497c0b28610c
  - route_id: campaign_evidence_integration
    phase: campaign_integration
    required: true
    material: true
    planned_job_ids: &id011
    - CEI-001
    planned_count: 1
    completed_job_ids: *id011
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/campaign_evidence_view.json
    terminal_artifact_sha256: 42fb33963497d976ed82e139cdef621614b14ec1d3636ea5598f7466aeaad9e0
  - route_id: semantic_evidence_integration
    phase: semantic_integration
    required: true
    material: true
    planned_job_ids: &id012
    - SEI-001
    planned_count: 1
    completed_job_ids: *id012
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/semantic_evidence_integration_view.json
    terminal_artifact_sha256: ddf045818050471fc4b88ec717d37b2228ab014fb813e879533e2dbbea08335d
  - route_id: category_benchmark_search_interest
    phase: category_benchmark
    required: true
    material: true
    planned_job_ids: &id013
    - GT-001
    planned_count: 1
    completed_job_ids: *id013
    completed_count: 1
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/category_benchmark_search_interest.json
    terminal_artifact_sha256: aadbf5be65147ee1bf154e51d91134cdcb9817102cd67be2efbc90b277a0d1f4
  - route_id: serp_phase2
    phase: serp_phase2
    required: true
    material: true
    planned_job_ids: &id014
    - P2-A01-C
    - P2-A01-V
    - P2-A01-D
    - P2-A02-C
    - P2-A02-V
    - P2-A02-D
    - P2-A03-C
    - P2-A03-V
    - P2-A03-D
    - P2-A04-C
    - P2-A04-V
    - P2-A04-D
    - P2-A05-C
    - P2-A05-V
    - P2-A05-D
    - P2-A06-C
    - P2-A06-V
    - P2-A06-D
    - P2-A07-C
    - P2-A07-V
    - P2-A07-D
    - P2-A08-C
    - P2-A08-V
    - P2-A08-D
    planned_count: 24
    completed_job_ids: *id014
    completed_count: 24
    blocked_job_ids: []
    blocked_count: 0
    unrun_job_ids: []
    unrun_count: 0
    terminal_artifact_locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/consumer_brand_phase2_search.json
    terminal_artifact_sha256: 70326e9fba609a1755f1a6557a4c2b359a0d3585a77d8d93a360f1a743318984
  serp_phase2_decision_receipt:
    locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/consumer_brand_phase2_search.json
    sha256: 70326e9fba609a1755f1a6557a4c2b359a0d3585a77d8d93a360f1a743318984
    entries: 24
  evidence_depth_ledger:
    locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/evidence_depth_ledger.json
    sha256: 657c118c27b56cb5556ef6d6542c8461391c0c0c1be6d22d341e553bd29a370d
  understanding_route:
    route_version: 1.9.0
    comparator_closure:
      state: phase_a_competitor_context_closed
      candidate_frame:
        locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/serp_phase1_comparator_frame.md
        sha256: 69fe23e925e2cb24b9d47a751a8d308637eb163183a6c3dc4bb8e48b069165f9
      adjudicated_set:
        locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/serp_phase2_adjudicated_set.md
        sha256: 618f41cff62ca270b3c79f22aec5cb361335ed316466d8fb26fa3c3271d35ea6
      frame_candidate_ids:
      - cand-generic-glycerin-serum
      candidates:
      - candidate_id: cand-generic-glycerin-serum
        name: generic glycerin serum alternatives
        material: false
        disposition: rejected
        decision_ready: false
        claim_ceiling: Search and discussion pointer only; not a decision-ready product
          comparator.
        prefanout_qualification:
          posture: rejected_before_fanout
          comparator_role: non_competitor
          open_comparator_search_refs:
          - P2-A05-V
          identity_evidence_refs:
            subject:
            - junip:Super Saturated
            competitor: []
          independent_comparison_origins: []
          gap_reason: No exact competitor product identity cleared repeated comparison
            across two independent source roles.
    campaign_evidence_integration:
      status: completed
      view:
        locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/campaign_evidence_view.json
        sha256: 42fb33963497d976ed82e139cdef621614b14ec1d3636ea5598f7466aeaad9e0
      targeted_capture_requests: []
    semantic_evidence_integration:
      status: completed
      view:
        locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/semantic_evidence_integration_view.json
        sha256: ddf045818050471fc4b88ec717d37b2228ab014fb813e879533e2dbbea08335d
      corpus_sha256: 8f3acf1b29ea327828f5871f39913a5dbc21e4e510d60a8d3c279182fc2da9f3
      unresolved_material_evidence_ids: []
      emerging_axis_dispositions: []
    verification_requests: []
    retailer_state_accounting:
      claims: []
  resume_contract:
    pending_job_ids: []
    reusable_artifacts:
    - locator: docs/research/experiment_beauty_collection_20260904_v0/coordinated/evidence_depth_ledger.json
      sha256: 657c118c27b56cb5556ef6d6542c8461391c0c0c1be6d22d341e553bd29a370d
      invalid_if:
      - Any pinned evidence body or coding artifact changes bytes.
  independent_semantic_review:
    status: required_not_executed_courier_prompt_returned
    required_before_acceptance: true
    review_routing_status: blocked
    blocker: Forseti requires operator-courier review prompt authoring; this implementation
      lane may not dispatch or execute the different-vendor semantic review.
  blocker: Different-vendor source-native semantic review and owner adjudication remain
    required before acceptance; acquisition evidence and material-saturation accounting
    are complete.
```
