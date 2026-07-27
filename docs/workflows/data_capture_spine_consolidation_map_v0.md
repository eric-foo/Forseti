# Data Capture Spine Repo Submap v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow navigation artifact (Data Capture Spine repo submap)
scope: Single repo submap that orients a reader across Data Capture Spine, Source Capture Armory, source-access authority, source-quality support, and harness implementation surfaces. Map only; not source-of-truth.
use_when:
  - Orienting to Data Capture Spine or Source Capture Armory before source-access, packet, runner, source-quality, or capture-lane work.
  - Finding which owner doc owns a capture area, source-access method, armory component, packet lifecycle, or implementation surface.
  - Checking current Reddit pre-commercial capture routing without bulk-loading every capture artifact.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/README.md
  - forseti/product/spines/capture/core/source_families/README.md
  - docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md
  - forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2_acceptance_decision_v0.md
stale_if:
  - The source-access tooling authorization changes build tranches, selected backend, or Reddit ordering.
  - The Source Capture Armory README changes component status, runner set, or gap list.
  - The Capture source-family lane catalog changes known-family route homes, source-family indexes, or family route posture.
  - The Data Capture obligation contract changes capture obligations or forbidden outputs.
  - The Candidate URL Intake parent contract changes candidate locator rows, run envelopes, promotion gates, caps, or traversal stops.
  - The Reddit Candidate URL Intake default-policy decision changes caps, candidate-surface defaults, outbound policy, monitoring posture, promotion ownership, or implementation-scoping gates.
  - The Reddit Candidate URL Intake contract changes candidate-row outputs, promotion gates, or broad-crawling stops.
  - The Reddit Graph Frontier Lane changes hop gates, register fields, same-run traversal boundary, semantic/frontier ownership, or implementation-scoping boundary.
  - The LinkedIn Lane changes optional POC-risk mode, people/business candidate fields, bounded-watch posture, promotion gates, or Outreach Lane separation.
  - Source Capture Packet lifecycle, retention, or fixture-admission rules move to a new owner.
  - Data Capture operating-model, obligation-baseline, lane-thesis, or commissioning-plan ownership moves.
```

> **What this is.** A retrieval-only repo submap. It tells a cold reader which owner source
> to open for a Data Capture / Source Capture Armory question. It is the map, not
> the authority: on any conflict, the pointed-to owner source wins.
>
> **Do not use** this map as validation, readiness, source-access permission,
> implementation authorization, fixture admission, source-quality proof, ECR,
> Cleaning, Judgment, or buyer proof.

## Fast Route

| I need to... | Open |
| --- | --- |
| Understand current Source Capture Armory components and gaps | `forseti/product/spines/capture/core/source_capture_toolbox/README.md` |
| Start known-source capture-to-lake lane routing | `forseti/product/spines/capture/core/source_families/README.md` |
| Classify incumbent source-family/source-surface pairs without rewriting packets | `forseti/product/spines/capture/core/source_taxonomy/source_classification_compatibility_contract_v0.md` |
| Check fragrance-native database capture routes (Fragrantica/Parfumo/Basenotes) | `forseti/product/spines/capture/core/source_families/fragrance_native_database/README.md` |
| Check Retail/PDP source-family route map | `forseti/product/spines/capture/core/source_families/retail_pdp/README.md` |
| Check vendor pricing-page source-family route map | `forseti/product/spines/capture/core/source_families/vendor_pricing_page/README.md` |
| Check Instagram public creator/reels capture route map | `forseti/product/spines/capture/core/source_families/social_media/instagram/README.md` |
| Check TikTok public/sessioned capture, admission, and projection route map | `forseti/product/spines/capture/core/source_families/social_media/tiktok/README.md` |
| Check shared Instagram/TikTok daily grid-heartbeat control and operator routing | `forseti-harness/source_capture/social_heartbeat_run_control.py`, then the platform README (`social_media/instagram/README.md` or `social_media/tiktok/README.md`) and `forseti-harness/docs/source_capture_agent_runbook.md` |
| Check YouTube public watch/Shorts/transcript capture route map | `forseti/product/spines/capture/core/source_families/social_media/youtube/README.md` |
| Check bounded Reddit candidate/capture/consolidation route map | `forseti/product/spines/capture/core/source_families/social_media/reddit/README.md` |
| Check Meta Ad Library paid-creative capture route map | `forseti/product/spines/capture/core/source_families/ad_transparency/meta_ad_library/README.md` |
| Check whether a source-access build or backend is authorized | `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md` |
| Check source-access boundary / hard stops | `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md` |
| Compare source-access methods and Reddit ordering | `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md` |
| Check operating-model / commissioning-plan authority | `forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2_acceptance_decision_v0.md`, then `forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2.md` or `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_commissioning_plan_v0.md` as needed |
| Check generic Candidate URL Intake boundaries | `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_candidate_url_intake_contract_v0.md` |
| Check standing-capture / Corpus Intake obligations (recurring capture before a Decision Frame) | `forseti/product/spines/capture/core/contracts/corpus_intake/data_capture_spine_corpus_intake_obligation_contract_proposal_v0.md` |
| Check bounded Reddit candidate URL intake / crawler boundaries | `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_reddit_candidate_url_intake_crawler_architecture_v0.md` |
| Check accepted Reddit graph/frontier scouting boundaries | `forseti/product/spines/scanning/source_families/reddit/data_capture_spine_reddit_graph_frontier_lane_architecture_v0.md` |
| Check bounded Reddit candidate URL intake default policy | `docs/decisions/data_capture_spine_reddit_candidate_url_intake_default_policy_decision_v0.md` |
| Use bounded screening-read service / browser-rung screening read | `docs/workflows/screening_read_service_build_receipt_v0.md`, `docs/workflows/screening_read_reusable_findings_v0.md`, `orca-harness/source_capture/screening_read.py`, and `orca-harness/source_capture/screening_browser_read.py` |
| Check LinkedIn Lane discovery, bounded watch, people/business candidate boundaries, and optional POC-risk mode | `forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_discovery_planning_lane_architecture_v0.md` |
| Check public-handle creator account linkage across IG/TikTok/YouTube | `forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_public_handle_linkage_ledger_spec_v0.md`, `forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_public_handle_linkage_ledger_v0.json`, `orca-harness/capture_spine/creator_public_handle_linkage/`, and `orca-harness/tests/unit/test_creator_public_handle_linkage.py` (static ledger/validator only; empty until source-backed public-handle evidence; no live capture, no contact/outreach, no SQLite) |
| Check live Creator Registry authority, TikTok admission, monitoring eligibility, or client-safe current profiles | `forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_registry_lake_authority_contract_v1.md`, `forseti-harness/data_lake/creator_registry.py`, and `forseti-harness/runners/run_creator_registry_lake.py` (append-only lake authority plus rebuildable generated views; onboarding eligibility is not scheduling; no data-only onboarding PR) |
| Check YouTube Shorts creator/channel observations from the 200-row fragrance pool | `forseti/product/spines/capture/core/source_families/social_media/youtube/youtube_creator_observation_ledger_spec_v0.md`, `forseti/product/spines/capture/core/source_families/social_media/youtube/youtube_shorts_fragrance_creator_observation_ledger_v0.json`, `orca-harness/capture_spine/youtube_creator_observation/`, and `orca-harness/tests/unit/test_youtube_creator_observation_ledger.py` (source-backed YouTube-only observation ledger plus rebuild verifier and archived-lake evidence check — the seed ledger is bound to the retired `orca-canonical` v0 root per the lake-identity-drift decision packet; no cross-platform linkage, no metric rollups, no transcript bodies, no SQLite) |
| Check the one-stop creator profile current view / dashboard-ready creator intelligence boundary | `forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_profile_current_view_spec_v0.md` (derived view over identity, metric observations, metric rollups, and ideal-audience snapshots; no one giant ledger, no SQLite adoption, no dashboard implementation, no live capture) |
| Check TikTok creator discovery frontier scans from suggested-account surfaces | `forseti/product/spines/scanning/source_families/tiktok/tiktok_creator_discovery_frontier_register_v0.md`, `forseti/product/spines/scanning/source_families/tiktok/tiktok_creator_discovery_enforcement_placement_v0.md`, `forseti-harness/capture_spine/tiktok_creator_discovery_frontier/`, and `forseti-harness/tests/unit/test_tiktok_creator_discovery_frontier.py` (receipt-backed weak discovery graph only; no live runner, registry mutation, metric rollups, or standing crawler) |
| Check product/buyer presentation over the current creator profile | `forseti/product/spines/creator_signal/creator_intelligence_profile_surface_v0.md` (Creator Signal surface contract; presentation/claim language over Capture-owned records; no storage, dashboard runtime, outreach, or public directory) |
| Handle old Reddit search/listing HTML for Candidate URL Intake pilots | `docs/workflows/reddit_candidate_intake_old_reddit_search_surface_handling_v0.md` |
| Plan bounded pre-commercial Reddit capture/consolidation | `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_planning_thread_v0.md` |
| Check Reddit capture/consolidation success-signal hardening rationale | `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_success_signal_architecture_v0.md` |
| Check Capture obligations / forbidden outputs | `forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md` |
| Check tenant/source-family payload attachment boundary | `forseti/product/spines/capture/core/packet_schema/source_capture_tenant_payload_attachment_boundary_v0.md` |
| Explain the core-facts vs typed-attachment split in plain language | `forseti/product/spines/capture/core/packet_schema/source_capture_core_payload_split_explainer_v0.md` |
| Check logical data-lake mechanics from Capture through canonical content, ECR/SCR, Cleaning, and Judgment | `forseti/product/spines/data_lake/workflows/core_spine_v0_data_lake_mechanics_map_v0.md` |
| Check Retail/PDP as the first non-IG typed-envelope probe | `forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_typed_envelope_probe_v0.md` |
| Check Capture-to-Cleaning authority and adaptation boundary | `forseti/product/spines/foundation/product_contract/core_spine_v0_data_and_cleaning_spine_boundary_v0.md` |
| Check Retail/PDP content and Cleaning contract | `forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md` |
| Produce Retail/PDP Silver from a committed packet through Cleaning-owned content adaptation | `forseti-harness/runners/run_retail_pdp_silver_producer.py`, `forseti-harness/cleaning/retail_pdp.py`, and `forseti-harness/tests/unit/test_retail_pdp_content_cleaning_silver.py` |
| Check fragrance purchase-review focused coverage MGT | `forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_focused_coverage_mgt_v0.md` (Luckyscent pinned-route receipt, row-selection policy, adaptive cap, drift fallback contract, accepted residuals; no raw review bodies in tracked docs) |
| Build a local fragrance purchase-review focused coverage receipt from saved widget/PDP files | `orca-harness/runners/run_fragrance_review_coverage.py`, `orca-harness/source_capture/fragrance_review_coverage.py`, and `orca-harness/tests/unit/test_fragrance_review_coverage.py` (offline helper; selected reader bodies plus skipped metadata/hashes; no live capture, ECR, Cleaning, Judgment, or integrity scoring) |
| Project an existing IG creator-momentum packet directory into local projection JSON | `orca-harness/runners/run_ig_creator_momentum_projection.py`, `orca-harness/source_capture/ig_projection.py`, and `orca-harness/tests/unit/test_source_capture_ig_projection.py` (offline, view-only, no live IG capture, scheduler, production store, or momentum score) |
| Project an existing IG reels-grid packet directory into source-surface-preserving local projection JSON | `orca-harness/source_capture/ig_reels_grid_projection.py` and `orca-harness/tests/unit/test_source_capture_ig_reels_projection.py` (offline, view-only, no live IG capture, Cleaning, ECR, Judgment, scheduler, or production store) |
| Check whether Reddit capture output lands usefully in ECR (real-data probe; resolved by-design) | `docs/workflows/reddit_capture_to_ecr_consumption_probe_finding_v0.md` |
| Check packet lifecycle, retention, sensitivity, or fixture movement | `docs/decisions/source_capture_packet_fixture_retention_sensitivity_decision_v0.md` |
| Run existing capture tools safely | `orca-harness/docs/source_capture_agent_runbook.md` |
| Author a new adapter against existing conventions | `orca-harness/docs/adapter_author_contract.md` |
| Inspect actual implemented adapters/runners/projection helpers | `orca-harness/source_capture/` and `orca-harness/runners/` |
| Inspect bounded live Reddit Candidate URL Intake runner | `orca-harness/runners/run_reddit_candidate_intake_live.py` and `orca-harness/tests/unit/test_reddit_candidate_intake_live_runner.py` |
| Inspect Reddit Graph Frontier / crawling graph local support | `orca-harness/capture_spine/reddit_graph_frontier/`, `orca-harness/runners/run_reddit_graph_frontier_register.py`, `orca-harness/tests/unit/test_reddit_graph_frontier.py`, `orca-harness/tests/unit/test_reddit_graph_frontier_runner.py`, and `orca-harness/tests/contract/test_reddit_graph_frontier_contract.py` |
| Inspect CloakBrowser anonymous v0 adapter/runner | `orca-harness/source_capture/adapters/cloakbrowser_snapshot.py`, `orca-harness/runners/run_source_capture_cloakbrowser_packet.py`, and `orca-harness/tests/unit/test_source_capture_cloakbrowser_snapshot.py` |
| Choose or escalate an anti-block rung against a 403 bot-block (honestly) | `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_anti_block_ladder_usage_guide_v0.md` |
| Check source-quality pass/report conventions | `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md` and `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md` |
| Assemble existing source-quality rows and packet state | `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_state_assembler_v0.md` |

## Current Reality Snapshot

- **Armory is the entrypoint.** `forseti/product/spines/capture/core/source_capture_toolbox/README.md`
  indexes components, build order, current gaps, and non-claims.
- **Anti-block HTTP ladder has a rung-1 arm + usage guide.** A header-complete
  stdlib anti-blocking HTTP fetch (`anti_blocking_http`, rung-1) plus a
  `block_shell` honest-success guard were built and live-proven against one
  Akamai 403 wall (Daimler IR PDFs) — container-level retrieval, one data point,
  not a settled capability. Introduced on the `feat/anti-block-http-ladder`
  branch (confirm merge state in git before assuming it is on main). See the
  anti-block ladder usage guide and the rung-resolution closeout in Areas.
- **Screening-read service is wired on PR branch.**
  `source_capture.screening_read.screening_read(...)` gives the screen
  orchestrator bounded public reads over Reddit/direct/anti-block HTTP without
  packets or ECR. `source_capture.screening_browser_read.screening_browser_read(...)`
  wraps CloakBrowser for public interstitial/browser reads and classifies
  `block_shell` on visible text. Same-shaped listing extraction uses
  `StructuredListingExtractionSpec` with row-local locators and range sanity.
  Start from `docs/workflows/screening_read_service_build_receipt_v0.md` and
  `docs/workflows/screening_read_reusable_findings_v0.md`.
- **Build authority is bounded.** The source-access tooling authorization owns
  first/second/third-tranche build scope. It now selects CloakBrowser as the
  primary anti-blocking backend.
- **Reddit pre-commercial route is source-specific.** Use the implemented
  anonymous CloakBrowser Snapshot runner for one supplied old Reddit/thread URL
  when anti-blocking browser capture is needed, prefer old Reddit HTML where
  available, keep capture low-volume and subreddit/thematic/thread-family
  bounded, then use archive capture where live capture is unnecessary or fails
  visibly.
- **CloakBrowser anonymous v0 is implemented.**
  `orca-harness/source_capture/adapters/cloakbrowser_snapshot.py` and
  `orca-harness/runners/run_source_capture_cloakbrowser_packet.py` preserve
  rendered DOM, visible text, a viewport screenshot, and method-provenance
  metadata for one supplied URL. This is not Reddit discovery/consolidation,
  parser execution, proxy/session behavior, storage, production runtime, or
  commercial use.
- **Reddit consolidation now has a planning thread.**
  `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_planning_thread_v0.md`
  is the durable architectural planning artifact for packet-before-parser
  handoff, BeautifulSoup parser role, provenance-first consolidation shape, and
  implementation stop lines. It now carries Decision-Frame-or-candidate
  classification, non-promoting success tiers, Armory vocabulary reuse,
  packet-contamination stops, no source-discovery expansion, and the current
  candidate-intake destination gap.
- **Reddit Candidate URL Intake is separate from Armory capture.**
  `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_reddit_candidate_url_intake_crawler_architecture_v0.md`
  specializes the parent Candidate URL Intake contract for the operator-facing
  Reddit "crawler" under Capture Spine. It emits candidate
  subreddit/thread/outbound URL rows with provenance only. It does not capture
  bodies/comments/profiles, emit Source Capture Packets, invoke Armory by
  default, auto-promote URLs into capture units, or authorize broad crawling.
  The bounded live first-contact runner
  `orca-harness/runners/run_reddit_candidate_intake_live.py` may fetch one
  declared source URL under a run envelope and live-access authorization, then
  persist only candidate rows, provenance, and a live-run receipt. For promoted
  Reddit capture, the lane records the existing
  source-backed posture: old Reddit first, CloakBrowser as the approved primary
  anti-blocking route, and residential or rotating proxies not blanket stop
  conditions in the pre-commercial/free anti-blocking posture. That is
  downstream access context, not Armory execution in intake.
- **Reddit Graph Frontier Lane is accepted as a separate bounded planning lane.**
  `forseti/product/spines/scanning/source_families/reddit/data_capture_spine_reddit_graph_frontier_lane_architecture_v0.md`
  owns the Graph Frontier Register shape. It may use a semantic/frontier agent
  to choose the next candidate seed and prepare the next bounded run, but every
  hop needs a new `run_id`, caps, exclusions, access mode, source-policy
  posture, and stop condition. It is not same-run traversal,
  Graph Frontier-owned live Reddit fetch, automatic capture, broad crawling,
  Source Capture, Data Capture, storage, scheduler, dashboard, or production
  runtime. Local register support exists under
  `orca-harness/capture_spine/reddit_graph_frontier/` for building a register
  from existing candidate output and preparing a next-run envelope with
  `execution_authorized: false`. Live first-contact fetch belongs to the
  Candidate URL Intake runner, not to the register. The operator-facing
  "crawling graph" runner
  `orca-harness/runners/run_reddit_graph_frontier_register.py` writes the
  register and optional non-executing next-run envelope from an existing
  Candidate URL Intake artifact.
- **LinkedIn Lane discovery planning is accepted as a bounded planning lane.**
  `forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_discovery_planning_lane_architecture_v0.md`
  owns the LinkedIn Lane boundary for candidate businesses, organizations,
  senior decision makers, public professional actors, creators, and influential
  people. It treats supervised browser-assist as green for Orca personal /
  pre-commercial POC only when tagged `optional_poc_risk_mode`, bounded,
  operator-supervised, provenance-recorded, non-commercial, and minimized; under
  that mode it may use anti-blocking techniques (anti-detect/cloaked browser,
  residential/rotating proxies, in-browser JS-challenge handling) to reach
  discoverable or entitled surfaces, consistent with the unchanged source-access
  boundary. The lane emits candidate rows, Graph Frontier planning structure, and
  promotion receipts only; it does not authorize live LinkedIn runners,
  autonomous scraping, no-entitlement gate bypass to non-entitled data, contact
  harvesting, lead-list creation, follower/connection/commenter graph capture,
  profile body harvesting, Source Capture Packets, Data Capture handoff, storage,
  scheduler, dashboard, production runtime, commercial use, or Outreach Lane
  execution.
- **Reddit success-signal routing is preserved.**
  `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_success_signal_architecture_v0.md`
  records the advisory architecture rationale for the success-signal patch and
  is not itself validation, readiness, capture authorization, storage
  authorization, source-quality scoring, ECR, Cleaning, Judgment, or commercial
  Reddit authority.
- **Reddit cold `.json` is not the spine.** Treat cold anonymous `.json`
  endpoints as downgraded; current official guidance, developer reports, and
  Orca's 2026-06-08 bounded probes indicate cold `.json` access can fail with
  403/network-security blocks. The useful JSON path is warm same-context JSON:
  load the exact old Reddit HTML thread first, then fetch the same thread's
  `.json` in that same browser context, preserving both bodies and provenance.
- **BeautifulSoup is parser-only.** It can parse retrieved old Reddit HTML or
  archived HTML after preservation; it does not fetch, bypass blocking, solve JS,
  or replace packet provenance.
- **No broad crawling.** Subreddit/thematic/thread-family bounding is allowed for
  Reddit pre-commercial capture, but site-wide walking, generic harvesting,
  production monitoring, storage, dashboards, deployment, and production runtime
  remain outside this map.

## Areas

### Capture obligations

- summary: What a Data Capture packet must preserve and what it must not decide.
- owner: `forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md`

### Tenant payload attachment boundary

- summary: Accepted target boundary for tenant/source-family typed payloads:
  current `SourceCaptureSlice` payload fields are transitional/incumbent; new
  payload families target packet/slice-keyed logical extension envelopes.
- owner: `forseti/product/spines/capture/core/packet_schema/source_capture_tenant_payload_attachment_boundary_v0.md`
- plain-language companion: `forseti/product/spines/capture/core/packet_schema/source_capture_core_payload_split_explainer_v0.md`

### Data-lake mechanics map

- summary: Planning-only logical mechanics map for how raw
  `SourceCapturePacket` truth, stable core facts, typed payload envelopes,
  projection, ECR/SCR, Cleaning, and Judgment flow by key without selecting
  physical storage, schema migration, or projection cache.
- owner: `forseti/product/spines/data_lake/workflows/core_spine_v0_data_lake_mechanics_map_v0.md`

### Retail/PDP typed-envelope probe

- summary: First non-IG logical fit check for the packet/slice-keyed typed-
  envelope boundary. Retail/PDP source-family payload can live outside direct
  `SourceCaptureSlice` fields while raw packet truth stays canonical and
  projection stays derived. It does not select storage or authorize runtime.
- owner: `forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_typed_envelope_probe_v0.md`

### Source-access boundary

- summary: Discoverable-or-entitled + disclosable standard, owner-accepted
  anti-blocking risk posture, and hard stops.
- owner: `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md`

### Source-access build authority

- summary: Bounded first/second/third-tranche build authority, CloakBrowser
  selection, Reddit ordering, deferred commercial/runtime surfaces, non-claims.
- owner: `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`

### Method planning

- summary: Candidate methods, source-family recommendations, Reddit `.json`
  posture, old Reddit HTML preference, BeautifulSoup parser position.
- owner: `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md`

### Operating model / commissioning

- summary: Owner-accepted v2 Data Capture operating-model architecture,
  obligation baseline, lane thesis, and bounded pressure-test commissioning
  plan. These are pressure-test planning authorities, not validation,
  hardening, product readiness, runtime, ECR, Cleaning, or Judgment design.
- owners: `forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2_acceptance_decision_v0.md`,
  `forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2.md`,
  `forseti/product/spines/capture/core/operating_model/data_capture_harness_product_goal_direction_signal_decision_v0.md`,
  `forseti/product/spines/capture/core/operating_model/data_capture_obligation_baseline_decision_v0.md`,
  `forseti/product/spines/capture/core/operating_model/data_capture_spine_lane_product_thesis_v0.md`,
  `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_commissioning_plan_v0.md`

### Candidate URL Intake

- summary: Generic Capture Spine parent contract for bounded candidate locator
  intake before promotion: run envelopes, candidate locator rows, outbound
  locator rows, provenance receipts, cap/coverage semantics, no-same-run
  traversal, subagent boundaries, promotion gates, and explicit non-outputs.
  It is not Source Capture Armory, Data Capture handoff, ECR, Cleaning,
  Judgment, fixture admission, source-quality scoring, or implementation
  authorization.
- owner: `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_candidate_url_intake_contract_v0.md`

### Corpus Intake (standing-capture)

- summary: Owner-ratified standing-capture sibling of the v0 commissioned
  obligation contract: the obligation home for recurring capture of an approved
  public signal into an append-only corpus BEFORE a Decision Frame (S1 standing
  charter gate, S2 series identity/pins, S3 declared-capped-stop-bounded cadence,
  S4 append-only integrity, S5 rebind gate, S6 manipulability flags ride forward,
  S7 never-a-feed lock). Inherits the v0 obligations (Ob.2-16) unchanged. Ratified,
  not pressure-tested; authorizes no build, scheduler, runtime, or source access.
- owner: `forseti/product/spines/capture/core/contracts/corpus_intake/data_capture_spine_corpus_intake_obligation_contract_proposal_v0.md`

### Reddit pre-commercial planning thread

- summary: Architectural planning route for bounded Reddit capture and
  consolidation: exact old Reddit Direct HTTP first for supplied thread URLs
  when current old Reddit HTML is the capture target, CloakBrowser
  anti-blocking when Direct HTTP is unsuitable or blocked, packet-before-parser
  handoff, provenance-first consolidation fields, Decision-Frame-or-candidate
  classification, non-promoting success tiers, Armory vocabulary reuse, archive
  fallback, `.json` fallback posture, and implementation stop lines.
- owner: `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_planning_thread_v0.md`

### Reddit Candidate URL Intake

- summary: Capture Spine candidate-intake contract for the operator-facing
  bounded Reddit "crawler": candidate subreddit/thread/outbound URL rows plus
  provenance only, declared-and-capped related-surface candidate discovery
  without same-run traversal, CloakBrowser as approved primary downstream
  anti-blocking route, proxies not blanket stop conditions for pre-commercial
  capture, bounded live first-contact intake under a run envelope, no
  body/comment/profile capture, no Source Capture Packet
  output, and no automatic Data Capture handoff.
- owner: `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_reddit_candidate_url_intake_crawler_architecture_v0.md`

### Reddit Graph Frontier Lane

- summary: Accepted bounded graph/frontier scouting lane downstream of Reddit
  Candidate URL Intake. It writes a Graph Frontier Register of candidate nodes,
  edges, prior pointers, source surfaces, caps, source-policy posture, stop
  reasons, and non-claims; semantic/frontier selection may choose the next seed
  only by preparing a fresh bounded run. It does not authorize same-run
  traversal, Graph Frontier-owned live Reddit fetch, automatic capture, Source Capture Packets, Data
  Capture handoff, broad crawling, storage, scheduler, dashboard, production
  runtime, source-quality scoring, ECR, Cleaning, Judgment, fixture admission, or
  commercial use. Operator-facing nickname: "crawling graph."
- owner: `forseti/product/spines/scanning/source_families/reddit/data_capture_spine_reddit_graph_frontier_lane_architecture_v0.md`

### LinkedIn Lane Discovery Planning

- summary: Bounded LinkedIn-adjacent discovery and candidate-frontier lane for
  businesses, organizations, senior decision makers, public professional actors,
  creators, and influential people. It records candidate rows, provenance,
  visible influence numbers, privacy/minimization flags, bounded-watch posture,
  optional POC-risk mode guardrails, Graph Frontier planning structure, and
  promotion requirements. It does not authorize LinkedIn scraping, no-entitlement
  gate bypass to non-entitled data, contact harvesting, lead lists,
  follower/connection/commenter graph capture, profile
  body harvesting, Source Capture Packets, Data Capture handoff, Outreach Lane
  execution, storage, scheduler, dashboard, production runtime, or commercial
  use.
- owner: `forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_discovery_planning_lane_architecture_v0.md`

### Reddit Candidate URL Intake Defaults

- summary: Recommended source-family default policy for bounded Reddit Candidate
  URL Intake: caps by `probe`, `working_batch`, and `high_recall_pass`;
  default-on/default-off candidate surfaces; outbound-link opt-in; monitored
  scopes default-off before a Decision Frame; continuation/widening rules;
  operator-owned promotion receipt; listing-provenance defaults; old-Reddit-
  first URL posture; downstream CloakBrowser/proxy setup not repeated in this
  lane; and bounded live runner scoping under a per-run envelope after owner
  acceptance. Pending owner acceptance; not validation, runtime authorization,
  Source Capture Packet output, or broad implementation execution.
- owner: `docs/decisions/data_capture_spine_reddit_candidate_url_intake_default_policy_decision_v0.md`

### Reddit Candidate URL Intake Search-Surface Handling

- summary: Lane-side handling note for no-live operator-supplied old Reddit
  search/listing HTML pilots. Records the `search-title` title-anchor rule,
  empty-result sanity checks, the difference between operator browser access and
  Candidate URL Intake access, and the separate candidate-subreddit discovery
  success signal for recommended/correlated subreddits with visible volume.
- owner: `docs/workflows/reddit_candidate_intake_old_reddit_search_surface_handling_v0.md`

### Reddit success-signal routing object

- summary: Advisory routing object explaining the Reddit success-signal
  hardening structure, including the candidate/scouting handoff gap and the
  reason the planning thread reuses existing Armory vocabulary instead of
  creating a Reddit-local ladder.
- owner: `forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_success_signal_architecture_v0.md`

### Source Capture Armory

- summary: Product-facing component index, build order, current gaps, non-claims,
  and source-quality entrypoints.
- owner: `forseti/product/spines/capture/core/source_capture_toolbox/README.md`

### IG creator-momentum projection helper

- summary: Offline packet-directory projection surface for existing IG Source Capture
  Packets. Materializes the view-only `metric_observations` row index from a
  packet directory or `manifest.json`; not live IG capture, scheduler, production
  store, momentum score, ECR, Cleaning, Judgment, or at-scale readiness.
- owners: `forseti/product/spines/capture/core/source_families/social_media/instagram/ig_capture_findings_consolidated_v0.md`,
  `orca-harness/source_capture/ig_projection.py`, `orca-harness/runners/run_ig_creator_momentum_projection.py`

### Creator profile current view

- summary: Product/view contract for the one-stop current creator profile. It
  joins public-handle identity, per-content metric observations, aggregate
  influence rollups, and ideal-audience snapshots without turning the identity
  ledger into one giant ledger.
- owner: `forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_profile_current_view_spec_v0.md`

### Creator Signal cross-spine surface

- summary: Product-facing creator intelligence surface over the Capture-owned
  `creator_profile_current` view. It owns operator/buyer presentation, aggregate
  influence display, ideal/content-fit audience display, freshness, limitations,
  and source drill-back. It does not own Capture identity rows, metric
  observations, metric rollup computation, ideal-audience inference schemas,
  SQLite/data-lake storage, dashboard runtime, live capture, outreach, lead-list
  export, or a public creator directory.
- owner: `forseti/product/spines/creator_signal/creator_intelligence_profile_surface_v0.md`

### Retail/PDP Content and Cleaning Contract

- summary: Current Retail/PDP capture-to-Cleaning contract: admitted aggregate
  profiles retain one retailer-owned canonical content record after their gates
  pass; failures and unflipped routes retain raw evidence; no new sample or
  Projection packet is admitted; historical raw and Projection-era packets stay
  readable through legacy compatibility. The Sephora normal deep-page route is
  `sephora_pdp_aggregate` content v3.
- owner: `forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md`

### Anti-block capture ladder

- summary: How to choose and honestly escalate anti-block rungs (0 `direct_http`
  control → 1 header-complete `anti_blocking_http` → 2 `curl_cffi` TLS/JA3
  (gated) → 3 `browser_snapshot` → heavier rungs) against 403 bot-blocks; how to
  judge success honestly (`block_shell` + a container-level discriminator); and
  the live Daimler/Akamai rung-1 result. Cost-ordered, not capability-ordered;
  browser rungs do not capture file bytes; one data point, not a settled
  capability.
- owners: `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_anti_block_ladder_usage_guide_v0.md`,
  `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_anti_blocking_http_ladder_daimler_rung_resolution_closeout_v0.md`

### Packet lifecycle / retention

- summary: Scratch packet lifecycle, durable citation, retention/sensitivity
  handling, and separate fixture admission boundaries.
- owner: `docs/decisions/source_capture_packet_fixture_retention_sensitivity_decision_v0.md`

### Harness implementation

- summary: Current runnable packet writers, adapters, runner docs, and tests.
  Implementation reality must be checked in code; docs may be ahead of runners.
  Capture Spine local support includes Reddit Candidate URL Intake, Reddit
  Graph Frontier register/receipt helpers under `orca-harness/capture_spine/`,
  and TikTok Creator Discovery receipt/register helpers under
  `forseti-harness/capture_spine/tiktok_creator_discovery_frontier/`, plus the
  bounded live Candidate URL Intake runner under
  `orca-harness/runners/run_reddit_candidate_intake_live.py` and the Graph
  Frontier register runner under `orca-harness/runners/run_reddit_graph_frontier_register.py`; these are not
  source-capture packet runners, Source Capture Armory execution, storage,
  scheduler, dashboard, or production runtime.
  CloakBrowser anonymous non-persistent v0 has a live engine and packet runner
  for one explicitly supplied URL; proxy/session behavior, Reddit
  discovery/consolidation, storage, production runtime, and commercial use are
  not implemented by that runner.
- owners: `orca-harness/docs/source_capture_agent_runbook.md`,
  `orca-harness/docs/adapter_author_contract.md`, `orca-harness/source_capture/`,
  `orca-harness/runners/`

### Source-quality support

- summary: Mini God-Tier source-quality posture, queue/report template,
  state assembler, and operational closeouts. These do not validate sources or
  admit fixtures.
- owners: `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md`,
  `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md`,
  `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_state_assembler_v0.md`

## Non-Claims

This map is not validation, readiness, source-access boundary amendment, legal
sufficiency, implementation execution, source completeness proof, fixture
admission, source-quality scoring, ECR design, Cleaning implementation, Judgment
design, buyer proof, commercial fetch authorization, broad crawler authorization,
storage/dashboard/deployment authorization, or production-runtime authorization.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: "Data Capture Spine and Source Capture Armory now have a thin workflow consolidation map, and Reddit capture routing records old Reddit HTML as the preferred pre-commercial browser-visible surface while treating anonymous `.json` as opportunistic fallback and BeautifulSoup as parser-only."
  trigger: workflow_authority
  related_triggers:
    - product_doctrine
    - architecture_doctrine
    - lifecycle_boundary
  controlling_sources_updated:
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
    - "docs/workflows/orca_repo_map_v0.md"
    - ".agents/workflow-overlay/source-loading.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
    - "forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md"
    - "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/artifact-folders.md"
    - "orca-harness/docs/source_capture_agent_runbook.md"
    - "orca-harness/docs/adapter_author_contract.md"
    - "forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md"
    - "forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
  intentionally_not_updated:
    - path: "AGENTS.md"
      reason: "Top-level project instructions do not enumerate per-spine repo maps or Reddit source-access method ordering."
    - path: ".agents/workflow-overlay/artifact-folders.md"
      reason: "docs/workflows already owns repo maps and workflow navigation artifacts; no new folder convention was introduced."
    - path: "forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md"
      reason: "Boundary permission and hard stops already permit disclosable anti-blocking; this patch changes route/order and navigation, not the boundary."
    - path: "forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
      reason: "Capture obligations and forbidden outputs did not change."
    - path: "orca-harness/docs/source_capture_agent_runbook.md"
      reason: "Historical note from the prior map patch; superseded by the later anonymous CloakBrowser v0 implementation and runbook update."
    - path: "orca-harness/docs/adapter_author_contract.md"
      reason: "Adapter author conventions already mention the selected CloakBrowser route; this map does not change adapter implementation conventions."
  stale_language_search: "rg -n \"Judgment Spine entry map|Data Capture Spine entry map|data_capture_spine_consolidation_map|Reddit official API.*cleanest|human-led/browser-visible capture by default pre-sale|anonymous `.json`.*primary|BeautifulSoup.*access method|old Reddit\" docs/workflows/orca_repo_map_v0.md .agents/workflow-overlay/source-loading.md .agents/workflow-overlay/source-of-truth.md docs/workflows/data_capture_spine_consolidation_map_v0.md docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_method_plan_v0.md forseti/product/spines/capture/core/source_capture_toolbox/README.md"
  stale_language_search_result: "Executed 2026-06-05 after this patch. Remaining hits are this map, the main repo-map pointer, source-loading pointer, source-of-truth known-document entry, current old Reddit / `.json` / BeautifulSoup posture text, and historical receipt text. No live route makes anonymous `.json` primary or BeautifulSoup an access method."
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source-access boundary amendment"
    - "not legal sufficiency"
    - "not implementation execution"
    - "not CloakBrowser installed"
    - "not Reddit live-run authorization"
    - "not commercial fetch, broad crawling, storage, dashboard, deployment, or production-runtime authorization"
    - "not ECR, Cleaning, or Judgment design"
```

```yaml
direction_change_propagation:
  doctrine_changed: "The Data Capture submap now routes to the accepted LinkedIn Lane discovery-planning architecture, including optional_poc_risk_mode for supervised personal/pre-commercial POC browser-assist and the separation of future Outreach Lane contact/lead handling."
  trigger: workflow_authority
  related_triggers:
    - architecture_doctrine
    - product_doctrine
    - output_authority
  controlling_sources_updated:
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
    - "forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_discovery_planning_lane_architecture_v0.md"
    - "forseti/product/spines/capture/core/source_capture_toolbox/linkedin_reddit_source_capture_armory_concurrent_structure_architecture_v0.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - ".agents/workflow-overlay/artifact-folders.md"
    - "forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_candidate_url_intake_contract_v0.md"
    - "forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md"
  intentionally_not_updated:
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "The top-level repo map already routes Data Capture detail through this submap; adding LinkedIn Lane details there would duplicate the submap."
    - path: "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
      reason: "LinkedIn Lane discovery is upstream of Source Capture Armory and does not emit Source Capture Packets."
  stale_language_search: "rg -n \"LinkedIn Lane|optional_poc_risk_mode|POC-risk|browser-assist|lead-list|contact harvesting|follower/connection\" docs/workflows/data_capture_spine_consolidation_map_v0.md forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_discovery_planning_lane_architecture_v0.md forseti/product/spines/capture/core/source_capture_toolbox/linkedin_reddit_source_capture_armory_concurrent_structure_architecture_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not legal sufficiency"
    - "not live LinkedIn authorization"
    - "not Outreach Lane authorization"
    - "not commercial authorization"
```

## Direction Change Propagation - Anti-Block Capture Ladder Navigation

```yaml
direction_change_propagation:
  doctrine_changed: "The Data Capture submap and repo map now route to the anti-block capture ladder: a header-complete anti_blocking_http rung-1 adapter plus a block_shell honest-success guard (introduced on feat/anti-block-http-ladder, live-proven against one Akamai 403 wall — one data point, container-level retrieval, not settled), with a usage guide and a rung-resolution closeout."
  trigger: workflow_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
    - "docs/workflows/orca_repo_map_v0.md"
  downstream_surfaces_checked:
    - "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
    - "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
  intentionally_not_updated:
    - path: "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
      reason: "The README reflects committed-main armory state; the rung-1 arm is on feat/anti-block-http-ladder and not yet merged. Index it from the README in a separate pass when the arm lands on main."
    - path: "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
      reason: "Build authority is unchanged; the header-complete stdlib rung is within the authorized bounded anti-blocking scope and adds no new gated surface."
  non_claims:
    - "not validation"
    - "not readiness"
    - "not a settled anti-block capability"
    - "not merged to main"
    - "not source-access boundary amendment"
    - "not ECR, Cleaning, or Judgment design"
```

## Direction Change Propagation - Corpus Intake (Standing-Capture) Registration

```yaml
direction_change_propagation:
  doctrine_changed: "The Data Capture submap now registers the owner-ratified Corpus Intake (standing-capture) obligation contract as the obligation home for recurring capture of an approved public signal into an append-only corpus before a Decision Frame (the standing sibling of the v0 commissioned obligation contract), with a Fast Route row and an Areas subsection."
  trigger: workflow_authority
  related_triggers:
    - product_doctrine
    - lifecycle_boundary
  controlling_sources_updated:
    - "forseti/product/spines/capture/core/contracts/corpus_intake/data_capture_spine_corpus_intake_obligation_contract_proposal_v0.md"
    - "forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
    - "docs/decisions/company_aggregate_forward_signal_capture_lane_scope_decision_v0.md"
    - "forseti/product/spines/capture/core/operating_model/data_capture_spine_lane_product_thesis_v0.md"
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
    - "docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not contract hardening"
    - "not pressure-tested"
    - "not a build, scheduler, runtime, or source-access authorization"
```
