# Summer Fridays Understanding p07 — Acquisition Seal

```yaml
retrieval_header_version: 1
artifact_role: evidence-layer acquisition seal
scope: Manual adjudication of the p06 control plus p07 REVOLVE/TSG and p08 Sephora four-family completion evidence.
use_when:
  - Checking whether Summer Fridays Understanding may proceed from Phase A acquisition into Turn B.
  - Verifying the sealed Phase A evidence layer before any separately authorized Turn B.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260725_p07/evidence_layer_completion.md
  - docs/research/summer_fridays_understanding_dogfood_20260724_p06/coordinated/turn_a_acquisition_record.md
stale_if:
  - The p06 control, p07 completion receipt, TSG capture, or p08 Sephora packets change.
  - The Jet Lag grouped-family adjudication or any required-family packet is re-adjudicated.
```

```yaml
subject: Summer Fridays
cycle_id: sf_understanding_20260725_p07_evidence_completion
seal_owner: current_home_actor
adjudication_mode: manual_after_fresh_read
state: SEALED_READY_FOR_DELIVER
gate: pass
deliver_allowed: true
phase_a_complete: true
phase_b_started: false
turn_b_started: false
company_report_exists: false
```

## Decision

The complete Phase A acquisition passes after the bounded p08 Sephora
four-family completion.

Closed since the p06 control:

1. All 37 admitted REVOLVE listings now resolve to a completed bounded Yotpo
   review collection or source-declared zero-row outcome. The 607 captured
   occurrences deduplicate to 576 native review IDs and 35 observed overlap
   components.
2. The official TSG Consumer announcement is durably captured and can bear the
   dated 2024 transaction, retained-founder-stake, continued-founder-leadership,
   and Prelude-exit claims.
3. Sunlit Vanilla is no longer an acquisition blocker.

4. Lip Butter Balm, Dream Lip Oil, and Flushed Lip Stain have standard
   source-specific Sephora onboarding summaries.
5. Jet Lag Mask has two standard US/USD PDP parents and two standard onboarding
   packets preserving all three raw roles. The summary adapter correctly
   retained a typed failure because Sephora/Bazaarvoice interleaves full-size,
   mini, and historical-mini IDs. Fresh manual adjudication verified 100/100
   native-ID overlap for Q&A, Helpful, and Recent across the two parent queries
   and admits the grouped `jet-lag-mask` family corpus without relabelling the
   parser failures.

The four-family Sephora customer-depth job and durable company-event job are
complete. No material Phase A acquisition blocker remains.

## Seal statement

`SEALED_READY_FOR_DELIVER`.

This seal authorizes no automatic next phase. Turn B and the company report
remain unstarted and require a separate owner instruction. Do not rerun
completed identity, retailer, event, Reddit, or customer-depth work by default.
