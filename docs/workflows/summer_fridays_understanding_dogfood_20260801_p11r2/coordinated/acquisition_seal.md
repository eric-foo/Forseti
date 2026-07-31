# Summer Fridays Understanding p11r2 — Acquisition Seal

```yaml
retrieval_header_version: 1
artifact_role: Acquire-and-seal lifecycle decision
scope: Records the validator-backed p11r2 acquisition gate and whether a later Deliver turn is licensed.
use_when:
  - Checking p11r2 acquisition readiness before any Deliver work.
authority_boundary: retrieval_only
```

```yaml
phase_acquisition_seal:
  schema_version: phase_acquisition_seal_v2
  cycle_id: summer_fridays_understanding_p11r2_20260801
  commission_id: summer_fridays_understanding_p11r2_acquisition_recovery
  subject: Summer Fridays
  authority_revision: cf37c213bfa3a7c05a3e6b8c7658fb5104de4c1a
  parent_authority_revision: aa92073b51c3a4259fbc800e98a06770ec21fb8b
  acquisition_gate: blocked
  seal_state: BLOCKED_ACQUISITION_INCOMPLETE
  deliver_allowed: false
  deliver_started: false
  bound_question_preserved: true
  coldness_attestation: compliant
  controller_placement:
    controller_actor: CO0
    placement: top_level
    worker_slots_required: 3
    worker_slots_available: 3
  route_capability_preflight:
    checked_before_network_capture: true
    google_serp:
      mode: cooldown_only
      primary_route_ready: true
      queue_state_writable: true
      persistent_fallback_ready: false
    reddit_weekly_lake:
      reader_status: ready
    paid_ad_transparency:
      google_ads_transparency: ready
      meta_ads_library: ready
    tiktok_shop:
      trigger: not_required
      route_status: not_checked_until_trigger
    native_social:
      tiktok: {trigger: required, route_status: blocked}
      instagram: {trigger: required, route_status: ready}
      youtube: {trigger: required, route_status: ready}
  specialist_returns:
    - actor: CO1
      terminal_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co1_company_core_recovery.md
      sha256: 705171d5122200a269c7c85fba337fd10c1e4b5a637d5db445c272af4380d4c6
      status: BLOCKED_TERMINAL
    - actor: CO2
      terminal_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md
      sha256: b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880
      status: REUSED_TERMINAL_ALL_PLANNED_JOBS_COMPLETE
    - actor: CO3
      terminal_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/specialists/co3_customer_community_recovery.md
      sha256: 20e15896e6b147bce06fac3c32bcd37dd32721024d1f0c76e423b4fca392e1d8
      status: BLOCKED_TERMINAL
  post_phase1_continuation_mode: full
  route_job_accounting:
    - route_id: serp_phase1
      phase: serp_phase1
      required: true
      material: true
      planned_job_ids: [p1_01_review, p1_02_side_effects, p1_03_bad_for_you, p1_04_made_worse, p1_05_not_working, p1_06_reddit, p1_07_dupe, p1_j5_subject_price, p1_vs_elf, p1_j5_elf_lip_balm, p1_vs_rhode, p1_j5_rhode_lip_balm]
      planned_count: 12
      completed_job_ids: [p1_01_review, p1_02_side_effects, p1_03_bad_for_you, p1_04_made_worse, p1_05_not_working, p1_06_reddit, p1_07_dupe, p1_j5_subject_price, p1_vs_elf, p1_j5_elf_lip_balm, p1_vs_rhode, p1_j5_rhode_lip_balm]
      completed_count: 12
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/scout_return.md
      terminal_artifact_sha256: c411b00df7952a86de7983f9e3d4138fe249e695719fa31247738aeb73354ce7
    - route_id: official_retailer_authorization
      phase: co1
      required: true
      material: true
      planned_job_ids: [CO1-J4]
      planned_count: 1
      completed_job_ids: [CO1-J4]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md
      terminal_artifact_sha256: 42fdf0f8c89ff573b62ce250e94e521a1ead8b9b6f5142ad0184a63799d0fb80
    - route_id: google_ads_transparency
      phase: co1
      required: true
      material: true
      planned_job_ids: [CO1-J8]
      planned_count: 1
      completed_job_ids: [CO1-J8]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md
      terminal_artifact_sha256: 42fdf0f8c89ff573b62ce250e94e521a1ead8b9b6f5142ad0184a63799d0fb80
    - route_id: meta_ads_library
      phase: co1
      required: true
      material: true
      planned_job_ids: [CO1-J9]
      planned_count: 1
      completed_job_ids: [CO1-J9]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md
      terminal_artifact_sha256: 42fdf0f8c89ff573b62ce250e94e521a1ead8b9b6f5142ad0184a63799d0fb80
    - route_id: company_core_identity
      phase: co1
      required: true
      material: true
      planned_job_ids: [CO1-J1, CO1-J2, CO1-J3, CO1-J5, CO1-J6, CO1-J7, CO1-J10, CO1-J11]
      planned_count: 8
      completed_job_ids: [CO1-J1, CO1-J2, CO1-J3, CO1-J5, CO1-J6, CO1-J7]
      completed_count: 6
      blocked_job_ids: [CO1-J10, CO1-J11]
      blocked_count: 2
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co1_company_core_recovery.md
      terminal_artifact_sha256: 705171d5122200a269c7c85fba337fd10c1e4b5a637d5db445c272af4380d4c6
    - route_id: retailer_full_pdp
      phase: co2
      required: true
      material: true
      planned_job_ids: [CO2-J1, CO2-J2, CO2-J3, CO2-J4, CO2-J5, CO2-J6]
      planned_count: 6
      completed_job_ids: [CO2-J1, CO2-J2, CO2-J3, CO2-J4, CO2-J5, CO2-J6]
      completed_count: 6
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md
      terminal_artifact_sha256: b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880
    - route_id: tiktok_shop_trigger_adjudication
      phase: co2
      required: false
      material: false
      planned_job_ids: [CO2-J7]
      planned_count: 1
      completed_job_ids: [CO2-J7]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md
      terminal_artifact_sha256: b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880
    - route_id: reddit_weekly_lake
      phase: co3
      required: true
      material: true
      planned_job_ids: [J-CO3-00]
      planned_count: 1
      completed_job_ids: [J-CO3-00]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md
      terminal_artifact_sha256: 6fa6f693e30f2a7c1fb11ba2e848d4d6cbaf04e42ae48918f83ed6bec862847b
    - route_id: reddit_community_scout
      phase: co3
      required: true
      material: true
      planned_job_ids: [J-CO3-01, J-CO3-02, J-CO3-03]
      planned_count: 3
      completed_job_ids: [J-CO3-01, J-CO3-02, J-CO3-03]
      completed_count: 3
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/specialists/co3_customer_community_recovery.md
      terminal_artifact_sha256: 20e15896e6b147bce06fac3c32bcd37dd32721024d1f0c76e423b4fca392e1d8
    - route_id: retailer_review_qa_corpus
      phase: co3
      required: true
      material: true
      planned_job_ids: [J-CO3-04]
      planned_count: 1
      completed_job_ids: [J-CO3-04]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md
      terminal_artifact_sha256: 6fa6f693e30f2a7c1fb11ba2e848d4d6cbaf04e42ae48918f83ed6bec862847b
    - route_id: native_tiktok
      phase: co3
      required: true
      material: true
      planned_job_ids: [CO3-NATIVE-TT-7232313070897483051, CO3-NATIVE-TT-7527741844298435895, CO3-NATIVE-TT-7379382940272217386, CO3-NATIVE-TT-7354686188327832833, CO3-NATIVE-TT-7496318205502246190]
      planned_count: 5
      completed_job_ids: [CO3-NATIVE-TT-7232313070897483051, CO3-NATIVE-TT-7379382940272217386, CO3-NATIVE-TT-7354686188327832833, CO3-NATIVE-TT-7496318205502246190]
      completed_count: 4
      blocked_job_ids: [CO3-NATIVE-TT-7527741844298435895]
      blocked_count: 1
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/specialists/co3_customer_community_recovery.md
      terminal_artifact_sha256: 20e15896e6b147bce06fac3c32bcd37dd32721024d1f0c76e423b4fca392e1d8
    - route_id: native_instagram
      phase: co3
      required: true
      material: true
      planned_job_ids: [CO3-NATIVE-IG-DWE8EFkDHes, CO3-NATIVE-IG-DPrnH9Cj6qI, CO3-NATIVE-IG-DXb1FcNhdXP, CO3-NATIVE-IG-DQLAZt7DSav]
      planned_count: 4
      completed_job_ids: [CO3-NATIVE-IG-DWE8EFkDHes, CO3-NATIVE-IG-DPrnH9Cj6qI, CO3-NATIVE-IG-DXb1FcNhdXP, CO3-NATIVE-IG-DQLAZt7DSav]
      completed_count: 4
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co3_customer_community_recovery.md
      terminal_artifact_sha256: d3be3ceccbb5fe389ff384abde8352b663a0044960b3957454493dd677024de0
    - route_id: native_youtube
      phase: co3
      required: true
      material: true
      planned_job_ids: [CO3-NATIVE-YT-nkKjxEQgBp8]
      planned_count: 1
      completed_job_ids: [CO3-NATIVE-YT-nkKjxEQgBp8]
      completed_count: 1
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md
      terminal_artifact_sha256: 6fa6f693e30f2a7c1fb11ba2e848d4d6cbaf04e42ae48918f83ed6bec862847b
    - route_id: serp_phase2
      phase: serp_phase2
      required: true
      material: true
      planned_job_ids: [p2_q01_ownership, p2_q02_spacenk_us, p2_q03_shadedrops_succession, p2_q04_cloud_dew_reformulation, p2_q05_lip_balm_stability, p2_q06_jet_lag_statement, p2_q07_sustainability_bht, p2_q08_lip_balm_packaging]
      planned_count: 8
      completed_job_ids: [p2_q01_ownership, p2_q02_spacenk_us, p2_q03_shadedrops_succession, p2_q04_cloud_dew_reformulation, p2_q05_lip_balm_stability, p2_q06_jet_lag_statement, p2_q07_sustainability_bht, p2_q08_lip_balm_packaging]
      completed_count: 8
      blocked_job_ids: []
      blocked_count: 0
      unrun_job_ids: []
      unrun_count: 0
      terminal_artifact_locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/serp_phase2/targeted_recovery_return.md
      terminal_artifact_sha256: f19e295cf58b2457f6fb2b8d93fdffe72dc4056cedb3515e1aee77c45e3a9c74
  serp_phase2_decision_receipt:
    locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json
    sha256: 3e814232972ecedec7c563f79c78bfca70f9618fae5b5a6c17446345f1dc95bf
    entries: 2
  resume_contract:
    pending_job_ids: [CO1-J10, CO1-J11, CO3-NATIVE-TT-7527741844298435895]
    reusable_artifacts:
      - locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/parent_reuse_validation.md
        sha256: cc7d64d3862421816ca431648c4d7c617eae6025de3d87963a24c6efc6dd18b4
        invalid_if: [artifact hash changes, parent authority changes, parent raw closure fails]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/commission_board.md
        sha256: 81a2f3b0a64c5258a2643429f72e4ddbaf4813ae3bc8b0cef60f6fded933ebbf
        invalid_if: [artifact hash changes, bound question changes, commission changes]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co1_company_core_recovery.md
        sha256: 705171d5122200a269c7c85fba337fd10c1e4b5a637d5db445c272af4380d4c6
        invalid_if: [artifact hash changes, terminal accounting changes, packet validation fails]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md
        sha256: b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880
        invalid_if: [artifact hash changes, authorization set changes, packet validation fails]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/specialists/co3_customer_community_recovery.md
        sha256: 20e15896e6b147bce06fac3c32bcd37dd32721024d1f0c76e423b4fca392e1d8
        invalid_if: [artifact hash changes, terminal accounting changes, packet validation fails]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/serp_phase2/targeted_recovery_return.md
        sha256: f19e295cf58b2457f6fb2b8d93fdffe72dc4056cedb3515e1aee77c45e3a9c74
        invalid_if: [artifact hash changes, queue accounting changes, packet validation fails]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json
        sha256: 3e814232972ecedec7c563f79c78bfca70f9618fae5b5a6c17446345f1dc95bf
        invalid_if: [artifact hash changes, decision contract fails, lifecycle provenance changes]
      - locator: docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/turn_a_acquisition_record.md
        sha256: bdc6fd9409e72f2585c6015be66b34b8e15542938136fff9360cd6f6afd31b67
        invalid_if: [artifact hash changes, acquisition adjudication changes, Deliver artifact appears]
```

## Seal Decision

The p11r2 recovery completed six of the nine jobs that p11r1 left pending. The
two Summer Fridays-owned page bodies and one packet-grade TikTok item remain
unavailable, so three required-and-material job IDs are still incomplete and
the acquisition gate remains blocked.

The earlier p11 and p11r1 blocked seals are preserved as provenance and receive
no completion credit. This p11r2 seal is the final artifact of the commissioned
Acquire & Seal turn. It does not authorize Deliver, another acquisition retry,
post-seal calibration, comparison to p10, or downstream synthesis.

## Owning Evidence

- Acquisition record: `docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/turn_a_acquisition_record.md`
- CO3 recovery return: `docs/research/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/specialists/co3_customer_community_recovery.md`
- New raw root: `C:\tmp\forseti-summer-fridays-understanding-p11r2-20260801\`
