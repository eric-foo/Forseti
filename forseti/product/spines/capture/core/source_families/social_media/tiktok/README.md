# Capture Source Family: TikTok

```yaml
retrieval_header_version: 1
artifact_role: Capture source-family lane index
scope: >
  Cold-start lane index for TikTok public/sessioned creator capture, daily
  grid heartbeat control, TikTok Shop storefront/PDP capture, packet admission,
  batch projection, and current residuals.
use_when:
  - Starting or reviewing TikTok capture-to-lake work.
  - Checking whether TikTok has a landed route, batch packet, projection, or unresolved residual.
  - Routing a "capture TikTok" request from the Source Capture Playbook into the TikTok lane.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_shop_capture_lane_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_first_slice_probe_recon_v0.md
  - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
  - docs/workflows/tiktok_funmi_n30_comment_subtitle_cadence_analysis_v0.md
  - forseti/product/spines/data_lake/README.md
stale_if:
  - TikTok sessioned/live runner admission, auth-state provenance, or challenge follow-through posture changes.
  - TikTok Shop store-card, PDP, seller-return, creator-shelf, or route-gate behavior changes.
  - TikTok batch admission/projection helpers change source_surface, packet, or data-root behavior.
  - Cross-creator coverage, account-safety, durable media, or product extraction moves from residual to landed capability.
```

## Canonical Route Homes

For TikTok creator/profile/video capture, the owning source-family route is:

`forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md`

For TikTok Shop brand-storefront and PDP capture, the owning route is:

`forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_shop_capture_lane_spec_v0.md`

The parent TikTok spec owns shared access and the Shop US-egress gate. The Shop
spec owns native store/PDP navigation, dwell and microbatch behavior, offer and
creator-shelf fields, challenge handoff, claim limits, and lake admission. The
Source Capture Playbook owns the general access-method doctrine; this README is
the TikTok lane map.

## Current Route Shape

| Layer | Current home | What to confirm |
| --- | --- | --- |
| Access / method | `tiktok_capture_lane_spec_v0.md`; `tiktok_ui_movement_blocker_substrate_playbook_v0.md` | Sessioned/cookied real-browser posture, no forged signatures, no secret persistence, stop-on-unresolved-challenge, and owner-authorized X-able follow-through boundaries. |
| TikTok Shop storefront/PDP | `tiktok_shop_capture_lane_spec_v0.md` | Fresh same-browser US-egress check; owner-selected routed real Chrome; native store-card and seller-return navigation; non-metronomic dwell; 8–10 PDP microbatches; operator CAPTCHA handoff; PDP offer plus complete product-linked creator-shelf capture; claim limits; packet admission. |
| Live staging | `orca-harness/source_capture/tiktok/live_batch_probe.py`; runner `run_source_capture_tiktok_live_batch_probe.py` | One creator per invocation; headed/sessioned or logged-out page-owned observation; sanitized staging by default. |
| Daily grid heartbeat | `forseti-harness/source_capture/social_heartbeat_run_control.py`; runners `run_source_capture_tiktok_daily_heartbeat.py`, `_control.py`, and `_operator.py` | Explicit active/daily roster; stable `platform_account_id` plan key; deterministic bucket/lane; attempt-bound frozen grid window, verified Bronze completion, and two exact-or-explicitly-unavailable profile metrics persisted to Silver for data-root runs. No suggested accounts, deep capture, comments, subtitles, or standing scheduler. |
| Canonical packet admission | `forseti-harness/source_capture/tiktok/batch_packet.py`; runner `run_source_capture_tiktok_batch_packet.py` | Network-free canonical parsed-batch admission; explicit `--data-root` / `--admit-output` for lake output; preserves transcript/comment/grid/selection evidence while excluding raw response, session, signed-URL, subtitle-body, and media material; fail closed on challenge/failure/diagnostic markers. |
| Coverage/projection | `orca-harness/source_capture/tiktok/batch_coverage.py`, `batch_projection.py`; runners `run_tiktok_batch_coverage.py`, `run_tiktok_batch_projection.py` | Text-free admitted-batch coverage/projection only; not product extraction, Cleaning, or Judgment. |
| Data Lake authority | `forseti/product/spines/data_lake/README.md` -> `authority/` | Raw admission, path grammar, derived layout, and Silver semantics. Do not restate them here. |

## Current Evidence And Residuals

- TikTok is no longer absent. First-slice recon, sessioned warm/profile/comment
  receipts, a lane spec, and Funmi N30 parsed-batch admission evidence exist.
- TikTok Shop has one complete brand-storefront proving run: 30 of 30 PDPs,
  569 product-linked creator cards, and three authoritative `tiktok_shop`
  packets covering offers, creator shelves, and sanitized route diagnostics.
  Cross-brand selector stability and unattended survivability remain unproven.
- Funmi N30 parsed-batch admission is source-specific evidence: 30 videos,
  parsed comments, source-native WebVTT where `subtitleInfos` existed, and
  deterministic typed extraction seeds are recorded in the TikTok sources.
- Full new onboarding, after deep capture, performs one bounded verified
  `Oldest`-sort observation and retains the earliest exact creator-owned public
  post date plus minimal source binding inside the existing canonical grid/batch
  evidence, then restores the shared page to a verified `Latest` state. Profile
  refresh does not repeat it; absence and verified no-post
  states remain typed, and the field never claims account creation time.
- Daily multi-creator grid-heartbeat mechanics are implemented, but live
  throughput, higher-volume account safety, and 2,500-creator scale remain
  unproven. The served grid verifies the planned public handle/video relation,
  not the numeric `platform_account_id`; stale roster handle binding remains a
  visible identity residual.
- Other residuals include durable media/video preservation, full comment
  census, platform-wide subtitle availability, and final product extraction.

## Non-Claims

Not validation, readiness, live capture success for a new account/creator,
source completeness, account-safety proof, durable media/video preservation,
CAPTCHA/slider solving authorization, TikTok Shop creator census or reach,
Cleaning, ECR, Judgment, buyer proof, or commercial-readiness evidence.
