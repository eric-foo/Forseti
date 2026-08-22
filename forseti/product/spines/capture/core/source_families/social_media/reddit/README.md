# Capture Source Family: Reddit

```yaml
retrieval_header_version: 1
artifact_role: Capture source-family lane index
scope: >
  Cold-start lane index for bounded Reddit candidate intake, graph/frontier
  planning, exact-thread capture, consolidation, and ECR consumption seams.
use_when:
  - Starting or reviewing bounded Reddit capture or candidate-intake work.
  - Routing a "capture Reddit" request from the Source Capture Playbook into source-specific contracts and runners.
  - Checking where Reddit discovery/select/capture/read responsibilities split.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_lake_cutover_architecture_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_radar_grid_capture_maintenance_design_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/reddit_capture_operator_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/reddit_precommercial_capture_consolidation_planning_thread_v0.md
  - docs/workflows/reddit_capture_to_ecr_consumption_probe_finding_v0.md
  - forseti/product/spines/scanning/source_families/reddit/data_capture_spine_reddit_graph_frontier_lane_architecture_v0.md
  - forseti/product/spines/data_lake/README.md
stale_if:
  - Old Reddit HTML, Reddit Direct HTTP batch, warm same-context JSON, CloakBrowser/proxy posture, or commercial Reddit policy changes.
  - Candidate URL Intake or Reddit Graph Frontier contracts change promotion, traversal, or output boundaries.
  - Reddit consolidation/projection/ECR consumption behavior changes.
```

## Stage Split

Reddit has separate stage owners. Do not collapse them into one crawler.

| Stage | Owner / route | Runner / code | Output boundary |
| --- | --- | --- | --- |
| Discover | Candidate URL Intake contracts and old Reddit search/listing handling docs | `run_reddit_candidate_intake_live.py` | Candidate subreddit/thread/outbound URL rows only; no bodies and no Source Capture Packet. |
| Select | Reddit Graph Frontier lane | `run_reddit_graph_frontier_register.py` | Frontier/register receipts and fresh bounded run envelopes; no same-run traversal. |
| Radar grid | `reddit_radar_grid_capture_maintenance_design_v0.md` + registry spec | `run_reddit_grid_capture.py`; `run_reddit_subreddit_registry_refresh.py` | One `reddit_subreddit_grid` listing packet per tracked subreddit (local or `--data-root` Bronze); read-only registry refresh from committed packets. |
| Deep-dive selection | `reddit_listing_efficiency_policy_v0.md` + `reddit_weekly_demand_radar_spec_v0.md` | `run_reddit_weekly_demand_read.py` | A fail-closed model-review queue from hash-verified old-Reddit or `www_reddit_realchrome_cdp` content-mode listing packets; no exact-thread capture authorization before commission-conditioned adjudication. |
| Capture | `reddit_capture_operator_playbook_v0.md` | `run_reddit_old_http_batch.py` (supports `--data-root` Bronze commit); `run_reddit_consolidation.py`; `run_reddit_batch_quality_summary.py` | Exact old Reddit thread packets plus derived consolidation outputs. |
| Weekly completion | `reddit_weekly_demand_radar_spec_v0.md` | `run_reddit_weekly_finalizer.py` | A dated `run.json` plus one agent-filterable thread catalog; final yes/no remains run-scoped Judgment and is not written into the neutral Data Lake. |
| Fallback | Source Capture Playbook archive route and Reddit operator playbook | `run_source_capture_archive_packet.py`; one-URL CloakBrowser runner when explicitly needed | Same-thread archive/capture only; no discovery, profile capture, or broad crawl. |
| ECR / downstream | `docs/workflows/reddit_capture_to_ecr_consumption_probe_finding_v0.md` plus ECR authority | `orca-harness/ecr/deriver.py`; Reddit consolidation/projection helpers | ECR consumes packets source-agnostically; no automatic cleared posture without a Decision Frame/cutoff posture. |

## Known-Venue Preflight

Before opening discovery, graph-frontier, or capture work on a subreddit,
check `reddit_subreddit_registry_v0.json` (contract:
`reddit_subreddit_registry_spec_v0.md`, same folder): known rows are
refreshed, not re-explored, and dated size observations append there. The
registry is routing/dedupe state only — it authorizes nothing and scores
nothing.

## Current Operator Default

For exact old Reddit thread URLs, use old Reddit Direct HTTP first when current
old Reddit HTML is the capture target and the runner accepts the URL. Use
CloakBrowser only for one supplied URL when browser-visible anti-blocking
capture is explicitly needed or Direct HTTP is unsuitable/blocked.

The source family string used by the old HTTP batch runner is `reddit_thread`
with source surface `old_reddit_direct_http`.

## Radar Cadence and Access Posture

Registry-scoped radar grid capture is an accepted direction
(owner-directed 2026-07-16; design:
`reddit_radar_grid_capture_maintenance_design_v0.md`): roughly daily grid
passes per tracked subreddit, stepped to 2–4x daily for trending subs,
following the TikTok grid→deep-dive pattern. Access is dual-track: bounded
public capture under the measured-risk ToS-gated posture AND a sanctioned
commercial/enterprise API or data-licensing path pursued in parallel;
commercial-grade product use lands on the sanctioned path. Every pass
still records its per-run robots/source-policy posture receipt, and the
lane must be built before anything runs.

## Deep-Dive Selection Posture

The Data Lake preserves neutral Reddit listing evidence. The Reddit
source-family lane owns the judgment about which exact threads are worth the
next read; do not persist a universal valuable/not-valuable label in the lake.

`reddit_listing_efficiency_policy_v0.md` is the governing selection contract.
Read the current weekly Data Lake before starting new Reddit discovery. A valid
real-Chrome packet is admitted only when its manifest, content-record hash,
real-browser metadata, source slice, subreddit, requested/final locator, and
listing URL agree; this admission reuses preserved evidence and does not turn
Capture Spine into an access bypass.
Mechanically, a fresh visible count of 0–9 comments suppresses a thread from
the general deep-dive queue, while 10+ comments routes it to
commission-conditioned model review. The governing policy's bounded sub-floor
failure/adverse-reaction/authenticity/discontinuation/dupe and discussion-venue
engagement exceptions still route qualifying 0–9 rows to review; neither
exception admits a thread by itself. A zero score is not a veto, and a missing
count is unparsed rather than zero. Title, flair, score, and engagement rank are
review cues only. The weekly reader therefore emits no capture slots until a
model records `yes`, `borderline`, or `no` against a named Decision Frame.

The reader preserves methodology ID `reddit_weekly_top100_per_subreddit_v0` and
separately exposes read policy `reddit_weekly_value_bounded_read_v1`. That policy
reads the post and high-engagement comments first, then spends attention in
25-comment batches until corpus exhaustion or a two-batch decision-relevant
novelty plateau. Identical recurrence support stops accumulating after five
distinct direct reporters, while new conditions, mechanisms, consequences,
behaviors, better evidence, and counters remain discoverable. Engagement and
corroboration thresholds order effort; they do not establish truth, prevalence,
or safety. The governing policy owns the receipt and expansion-cap details.

## Silver Envelope Subject Shaping (lake-map courier note, 2026-07-17)

No Reddit Silver envelope writer exists yet. When one is built, shape subjects
so creators file automatically in the lake map (courier note from the
silver-entity-read-layer lane, merged PR #1031; governing plan:
`docs/decisions/forseti_lake_map_scaling_and_hygiene_plan_v0.md`):

- Authors -> `platform_public_account` subjects: namespace exactly lowercase
  `reddit`, the stable id in `native_id`, and the id's kind in
  `native_id_kind` when known (`reddit_fullname` vs username — usernames are
  less stable).
- Posts/comments-as-content -> `public_content_object` with
  `published_by_account_native_id` (+ `published_by_account_native_id_kind`)
  naming the author.
- The same work unit adds `"reddit"` to `KNOWN_PLATFORM_NAMESPACES` in
  `forseti-harness/data_lake/derived_retrieval_views.py` (a deliberate
  one-line vocabulary extension, deferred until Reddit Silver records exist).
  Until it lands, Reddit author records surface in the by_creator view's
  residuals as `unrecognized_platform_namespace` — visible, never silently
  lost. Product mentions on Reddit have no product-page anchor yet; that is a
  `NATIVE_PRODUCT_PAGE_SOURCES` registry entry when needed, not a blocker.

## Hard Stops

- No broad subreddit crawling beyond registry-tracked grid passes and
  their selected deep dives; no source-discovery expansion outside bounded
  runs; no user/profile capture; no dashboards.
- Candidate URL Intake rows do not auto-promote into Capture units.
- A weekly listing-review row does not auto-promote into an exact-thread
  capture slot. An unadjudicated capture-list request fails closed.
- Do not write a commission-agnostic valuable/not-valuable label into the
  neutral Data Lake.
- Cold anonymous `.json` is not the default target; warm same-context JSON is a
  future/specialized path only after exact old Reddit HTML is visible.

## Non-Claims

Not validation, readiness, source completeness, fixture admission, commercial
Reddit authority, monitoring authorization, ECR/Judgment proof, Cleaning
authority, buyer proof, or legal advice.
