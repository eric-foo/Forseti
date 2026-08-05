# Summer Fridays Understanding p11 Coldness Provenance

```yaml
retrieval_header_version: 1
artifact_role: Cold-run provenance ledger
scope: Records the allowed method reads, newly created p11 roots, and fact-level quarantine for the Summer Fridays Understanding p11 Acquire & Seal run.
use_when:
  - Auditing whether p11 acquisition inputs were obtained cold.
authority_boundary: retrieval_only
```

## Run Binding

```yaml
run:
  cycle_id: summer_fridays_understanding_p11_20260731
  commission_id: summer_fridays_understanding_cold_confirmation_p11
  subject: Summer Fridays
  effective_target_worktree: C:\tmp\forseti-summer-fridays-understanding-p11-dogfood-20260731
  required_revision: aa92073b51c3a4259fbc800e98a06770ec21fb8b
  branch: codex/sf-understanding-p11-dogfood-20260731
  source_context_ready: true
```

## Allowed Source Reads Before Acquisition

- `AGENTS.md`
- `.agents/workflow-overlay/README.md`
- `.agents/workflow-overlay/decision-routing.md`
- `.agents/workflow-overlay/safety-rules.md`
- `docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md`
- `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
- `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md`
- `forseti-harness/tests/fixtures/commission_signal_board_outputs/valid_company_commission_stage_output.txt` (structure-only validator fixture; no Summer Fridays facts)
- `docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md`
- `docs/research/serp_lane_competitor_scout_20260728/README.md` (method and authority only)
- `docs/research/serp_lane_competitor_scout_20260728/competitor_ledger_spec_v0.md` (method only)
- `docs/research/serp_lane_competitor_scout_20260728/serp_lane_v0.md` (current Board v2.2 and cadence authority only)
- `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`
- `forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md` (method only)
- `docs/workflows/forseti_repo_map_v0.md`
- `docs/workflows/data_capture_spine_consolidation_map_v0.md`
- `forseti-harness/docs/source_capture_agent_runbook.md`
- `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md`
- `forseti-harness/runners/run_source_capture_cloakbrowser_packet.py` and its observed `--help`
- `forseti-harness/runners/serp_egress_cadence.py`
- `forseti-harness/source_capture/google_serp_queue_policy.py`

## Resume Authority And Validation Reads

The interrupted artifacts were loaded under the amended handoff's confirm-don't-trust contract. Their names, prior terminal labels, and the earlier blocked seal were discovery aids only. Before any pending acquisition job ran, CO0 recomputed all manifest-declared file sizes and SHA256 values, schema-validated the packets, validated the current commission board, and rechecked the p11 roots for Deliver artifacts. The pre-resume census covered 110 unique packet manifests and 404 preserved files with no size, hash, schema, or packet-ID collision failure.

```yaml
resume:
  authority_revision: aa92073b51c3a4259fbc800e98a06770ec21fb8b
  prior_blocked_seal_sha256: C22D78D00BB47E8353BCE090F8D843894B294D43B9810BFC639EEB857D3C7667
  prior_blocked_seal_completion_credit: none
  load_outcome: PARTIAL_REUSE
  reuse_rule: only_manifest_schema_size_and_sha256_validated_artifacts
  pending_job_rule: run_only_jobs_not_already_terminal_under_current_authority
  deliver_artifact_scan_before_resume: clear
```

Additional current method and runtime sources fresh-read for the resumed acquisition were:

- `.agents/hooks/check_commission_signal_board_output.py`
- `forseti-harness/runners/run_phase_acquisition_seal_validation.py`
- `forseti-harness/runners/run_google_serp_queue.py` and its observed `--help`
- `forseti-harness/runners/run_reddit_weekly_demand_read.py` and its observed `--help`
- `forseti-harness/runners/run_source_capture_browser_packet.py` and its observed `--help`
- `forseti-harness/runners/run_google_ads_transparency_projection.py` and its observed `--help`
- `forseti-harness/source_capture/models.py`
- `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md`
- `forseti/product/spines/capture/core/source_families/ad_transparency/google_ads_transparency/README.md`
- `forseti/product/spines/capture/core/source_families/ad_transparency/meta_ad_library/README.md`
- `forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md`
- `forseti/product/spines/capture/core/source_families/retail_pdp/README.md`

After their dependency gates opened, CO0 also fresh-read the current p11 Phase 1 return and each CO1/CO2/CO3 terminal return as retrieval/provenance maps, then dereferenced their named p11 raw locators for validation. Those p11 outputs are acquired evidence, not pre-acquisition seed facts.

## P11 Evidence Roots

```yaml
p11_roots:
  raw_root: C:\tmp\forseti-summer-fridays-understanding-p11-20260731
  phase1_raw: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase1
  specialist_raw: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\specialists
  phase2_raw: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2
  phase2_lifecycle_store: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2_store
  durable_evidence_root: docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated
  durable_seal_root: docs/workflows/summer_fridays_understanding_dogfood_20260731_p11/coordinated
```

## Coldness Attestation Boundary

The p11 actors may reuse mechanics from the allowed method sources, but no Summer Fridays fact appearing in a method example may seed or support a p11 query, information job, finding, comparison, or seal. Prior Summer Fridays p05-p10 artifacts, earlier Summer Fridays Data Lake packets, the calibration predeclaration, and pre-dispatch `C:\tmp` Summer Fridays staging remain quarantined. This ledger records actual allowed reads and does not claim environment-level proof that every prohibited file remained unread.

## Final Confirm-Don't-Trust Closure

After the last Phase 2 packet and lifecycle receipt were written, CO0 repeated the manifest-model, size, and SHA256 validation over the entire p11 runtime root rather than inheriting any specialist count or terminal label.

```yaml
final_runtime_validation:
  runtime_root: C:\tmp\forseti-summer-fridays-understanding-p11-20260731
  manifest_locations: 232
  unique_packet_ids: 188
  exact_alias_manifest_locations: 44
  exact_alias_boundary: declared CO3 validated-parent import lake
  preserved_file_declarations_rehashed: 933
  all_runtime_files_observed: 1641
  manifest_schema_errors: 0
  preserved_file_size_or_hash_errors: 0
  packet_id_collisions: 0
  acquisition_artifact_reuse_result: validated
  deliver_artifact_scan_at_closeout: clear
```

The census counts manifest locations, not independent sources. The 44 byte-identical aliases are retained because the CO3 onboarding lake records validated parent imports; they are neither discarded nor double-counted as new evidence.

## TikTok Shop Session Gate Observation

```yaml
tiktok_shop_egress_gate:
  country: US
  method: proxy
  observed_at: "2026-07-31T11:20:10Z"
  session_state: released_after_check
  scope: licenses only an immediate same-session TikTok Shop access; reconnect, identity change, or materially later access requires a fresh same-session country check
```

No IP, provider/profile identity, endpoint, credential, cookie, or local-path detail is retained.

## TikTok Shop Mandatory-Trigger Adjudication

```yaml
tiktok_shop_mandatory_trigger:
  adjudicated_from: fresh_p11_evidence_only
  decision: NOT_REQUIRED
  evidence_basis:
    - CO1-E1 supports the owned phrase community born but does not establish creator/influencer-led acquisition or channel importance.
    - CO1-E2 establishes the company-owned authorized-retailer board and does not name TikTok Shop.
    - CO1-E6 supports public-facing co-founders and a fragrance category extension but does not establish creator/influencer-led status or TikTok Shop importance.
    - Fresh Phase 1 and CO3 native-item acquisition licensed TikTok, Instagram, and YouTube item work but did not establish TikTok Shop as a commercially material channel.
  access_performed: false
  capability_observation_used_as_trigger: false
  recheck_condition: Re-adjudicate only if fresh allowed CO2 or CO3 evidence establishes creator/influencer-led status or TikTok Shop as a high-importance channel; any subsequent access requires a newly fresh same-session US check.
```

Native TikTok, Instagram, and YouTube acquisition is a separate trigger family from TikTok Shop. Phase 1 licensed five TikTok, four Instagram, and one YouTube exact-item jobs. CO3 completed three Instagram items and the YouTube item, preserved one Instagram setup-recovery failure, and applied one shared prelaunch TikTok route-incompatibility result to all five exact-video jobs. None of that authorized TikTok Shop access or Deliver work.
