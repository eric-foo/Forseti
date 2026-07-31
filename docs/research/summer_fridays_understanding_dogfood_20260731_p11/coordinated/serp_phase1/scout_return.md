# Summer Fridays p11 SERP Phase 1 Scout Return

```yaml
retrieval_header_version: 1
artifact_role: SERP Phase 1 terminal return
scope: Typed terminal state of the fresh p11 Phase 1 scout and its specialist fan-out inputs.
use_when:
  - Dispatching or refreshing the p11 CO1, CO2, and CO3 specialists.
  - Auditing the fresh Phase 1 seed, comparator, price, recovery, and trigger accounting.
authority_boundary: retrieval_only
```

```yaml
status: COMPLETE
phase_a_job_set_terminal: true
subject: Summer Fridays
ledger: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/competitor_ledger.json
selected_for_vs:
  - name: e.l.f.
    product_scope: Glow Reviver Melting Lip Balm
    type: dupe_association
    rung: candidate
    basis: two distinct fresh seed queries
  - name: Rhode
    product_scope: Peptide Lip Treatment
    type: rival
    rung: candidate
    basis: two distinct fresh seed queries
j5_prices:
  - name: Summer Fridays
    product_scope: Lip Butter Balm, 15 g
    standing_price_usd: 24.00
    source_packet_id: 01KYWMC8ZSWS6K6ZRZR3VVERWA
  - name: e.l.f.
    product_scope: Glow Reviver Melting Lip Balm, 0.52 oz
    standing_price_usd: 9.00
    source_packet_id: 01KYWMN6SF5QAM2QJ1HT9120T9
  - name: Rhode
    product_scope: Peptide Lip Treatment, 10 ml
    standing_price_usd: 20.00
    source_packet_id: 01KYWMZN86YHEG430NA3FH6KV5
levers:
  j1_cross: e.l.f. occupies a lower-price rendered dupe surface; switching remains unproven pending native evidence.
  j2_exit_door_class: retention_or_value_proof
  j3_tags:
    - clean_or_non_toxic_claim
    - temporary_irritation_or_redness
    - packaging_or_applicator_failure
    - discontinued_or_reformulated_product
    - lip_balm_value_and_duration
    - elf_dupe_comparison
    - rhode_texture_and_hydration_comparison
trigger_thread_queue_count: 7
trigger_thread_queue:
  - https://www.reddit.com/r/Sephora/comments/19eo5it/can_we_all_just_admit_that_summer_fridays_isnt/
  - https://www.reddit.com/r/Sephora/comments/1oh26y0/review_finally_got_around_to_trying_summer/
  - https://www.reddit.com/r/beauty/comments/1fvevie/summer_fridays_is_lying_to_you/
  - https://www.reddit.com/r/Sephora/comments/1al8aby/summer_fridays_applicator_clogged/
  - https://www.reddit.com/r/LipBalm/comments/1slrvyj/summer_fridays/
  - https://www.reddit.com/r/Sephora/comments/1ahn26w/how_do_yall_feel_about_the_summer_fridays_lip_balm/
  - https://www.reddit.com/r/LipBalm/comments/1qdk0gq/cheaper_dupes_for_summer_fridays_type_balms/
mediator_count: 9
mediators:
  Ale Jay: [Summer Fridays]
  Carly Rivlin: [Summer Fridays]
  Christi Rose: [Summer Fridays]
  Eli Leimer: [Summer Fridays]
  Karly Alane: [Summer Fridays]
  Michael Park MD: [Summer Fridays]
  Mursal | Toronto: [Summer Fridays]
  by.erinmarie: [Summer Fridays]
  goforthandgrow: [Summer Fridays]
mediator_classes:
  Ale Jay: pending_classification
  Carly Rivlin: pending_classification
  Christi Rose: pending_classification
  Eli Leimer: pending_classification
  Karly Alane: pending_classification
  Michael Park MD: professional_creator
  Mursal | Toronto: pending_classification
  by.erinmarie: pending_classification
  goforthandgrow: pending_classification
grid_capture_queue_count: 10
grid_capture_queue:
  - platform: tiktok
    url: https://www.tiktok.com/@karlyalane_/video/7232313070897483051
    trigger: safety_statement_could_change_bound_answer
  - platform: tiktok
    url: https://www.tiktok.com/@by.erinmarie/video/7527741844298435895
    trigger: clean_brand_statement_could_change_bound_answer
  - platform: instagram
    url: https://www.instagram.com/reel/DWE8EFkDHes/
    trigger: clean_or_non_toxic_statement_could_change_bound_answer
  - platform: instagram
    url: https://www.instagram.com/reel/DPrnH9Cj6qI/?hl=en
    trigger: clean_at_sephora_challenge_could_change_bound_answer
  - platform: instagram
    url: https://www.instagram.com/reel/DXb1FcNhdXP/?hl=en
    trigger: professional_worth_hype_statement_could_change_bound_answer
  - platform: tiktok
    url: https://www.tiktok.com/@makeup2themaxx/video/7379382940272217386?lang=en
    trigger: discontinued_product_statement_could_change_bound_answer
  - platform: tiktok
    url: https://www.tiktok.com/@walkingtower/video/7354686188327832833
    trigger: packaging_or_applicator_statement_could_change_bound_answer
  - platform: tiktok
    url: https://www.tiktok.com/@micahlambeth/video/7496318205502246190
    trigger: packaging_or_applicator_statement_could_change_bound_answer
  - platform: instagram
    url: https://www.instagram.com/reel/DQLAZt7DSav/?hl=en
    trigger: exact_elf_dupe_statement_could_change_bound_answer
  - platform: youtube
    url: https://www.youtube.com/watch?v=nkKjxEQgBp8
    trigger: exact_elf_head_to_head_could_change_bound_answer
official_source_doors:
  - url: https://summerfridays.com/pages/jet-lag-mask-statement
    source_job: p1_02_side_effects
    status: locator_and_snippet_only_pending_specialist_adjudication
  - url: https://summerfridays.com/pages/sustainability
    source_job: p1_03_bad_for_you
    status: locator_and_snippet_only_pending_specialist_adjudication
jobs:
  planned_count: 12
  completed_count: 12
  blocked_count: 0
  unrun_count: 0
  pending_count: 0
  completed:
    - p1_01_review
    - p1_02_side_effects
    - p1_03_bad_for_you
    - p1_04_made_worse
    - p1_05_not_working
    - p1_06_reddit
    - p1_07_dupe
    - p1_j5_subject_price
    - p1_vs_elf
    - p1_j5_elf_lip_balm
    - p1_vs_rhode
    - p1_j5_rhode_lip_balm
block_attempts:
  count: 3
  detail:
    - job_id: p1_01_review
      packet_id: 01KYVY835H2M9T6NQBKCVFPWF0
      disposition: preserved interrupted-run block; final job later completed
    - job_id: p1_01_review
      packet_id: 01KYWCE84EVSV7B1QY6KRW6NR5
      disposition: preserved resume block; cooldown recovery completed the job
    - job_id: p1_03_bad_for_you
      packet_id: 01KYWG6CYRCSM233P3VJY6SF63
      disposition: preserved resume block; cooldown recovery completed the job
owner_ping_written: false
recovery_observation:
  ttshop_profile_borrowed: false
  dedicated_logged_out_cdp_ready: false
  cooldown_recoveries_completed: 2
  hot_retry_performed: false
  terminal_lower_route_status: healthy_after_permitted_recoveries
artifacts:
  raw_root: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1
  seed_queue_state: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1\queue_state_resume.json
  subject_price_queue_state: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1\merged_queue_state_resume.json
  competitor_queue_state: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1\competitor_queue_state_resume.json
  durable_ledger: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/competitor_ledger.json
  cost_log: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/cost_log.md
claim_ceiling:
  - Observed cards are point-in-time rendered surfaces, never prevalence, volume, share, sales, or trend.
  - US-parameterized Google results are not proof of physical US locality or nationwide availability.
  - Reddit and native-social locators are discovery doors only until the authorized specialist preserves native evidence.
  - Google synthesis and snippets are not substitutes for dereferenced owned, retailer, community, or native evidence.
  - Phase 1 performed no native Reddit or social capture and weighted no raw social engagement count.
```

The final job set is terminal even though its provenance retains three block
attempts. Two route blocks during this resumption were recovered only after the
required one-hour cooldown; the earlier interrupted-run block remains preserved.
No blocked attempt has been converted into a zero-yield claim or deleted.

The ten native-item rows are trigger inputs, not native evidence. Their separate
platform decisions belong to `CO3`; the two owned-page rows belong to `CO1`.
