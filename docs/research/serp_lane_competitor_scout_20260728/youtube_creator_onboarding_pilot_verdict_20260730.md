# YouTube Creator Onboarding Pilot Verdict — 2026-07-30

```yaml
retrieval_header_version: 1
artifact_role: pilot verdict note
scope: >
  Findings from the four-creator YouTube onboarding pilot commissioned by
  youtube_creator_onboarding_lane_execution_handoff_v0.md, plus the
  owner-authorized Dr Dray Judgment and Creator Registry admission follow-up.
authority_boundary: evidence_report_only
current_as_of: 2026-07-30
next_source: >
  The live Creator Registry account and admission receipts, the bound
  creator-audience Judgment outcome, and later monitoring observations.
```

## Verdict

The assessment lane is usable for owner review: all four requested public
channels resolved to an immutable channel ID and canonical handle in fresh,
logged-out browser contexts, and uploads and Shorts were captured as separate
formats. The assessment did not license admission by itself. After an explicit
owner decision, Dr Dray alone advanced through the new YouTube
creator-audience Judgment route and was admitted to the live Creator Registry.
The other three pilot creators remain assessment-only.

The 73 recurring YouTube feed rows now export as unresolved display-name
frontier candidates. The claimed additional 301 suffix-door creators cannot
yet be identity-wired from the surviving evidence: the sealed analysis stores
the count but not the named set, while the current row-level extract yields 321
feed-absent names under the adapter's explicit normalization. Truncating that
set to 301 would fabricate the boundary, so the runner fails closed on the
mismatch.

## Dr Dray admission follow-up

Dr Dray (`UCnxmUrGMtpQT844Yd_l7Zyg` / `@DrDrayzday`) was admitted as
`acct_youtube_fd84b8243e33337a`. The live account-admission receipt is
`cra_fcbbffa1febc727142444d39`; an immediate idempotency rerun returned
`already_current` and the same receipt.

The admission is bound to:

- assessment packet `01KYSA1HSB0QAG9B5MPT7RQM09`;
- two selected videos (`HN42G3X9obE` and `8s8NiiVTjCg`);
- 572 usable transcript cues and 80 bounded comments;
- evidence bundle `caeb_9ed57403eeb137c915d7`,
  `sha256:04ec6fcc4753e99329a6c27209772d81351a0ea05142fb4f77e42f0ecf3a0499`;
- validated Judgment outcome
  `derived/d31/01KYSA1HSB0QAG9B5MPT7RQM09/creator_audience_judgment_outcome/cajo_88f9b23c740277bafaeb`;
- capability snapshot `cats_04e547382fb8d3cd2dd8`;
- eligible frontier disposition `cfd_fca1adda2725798735cbfeb6`; and
- candidate-admission record `crc_f5d4b447fbd65613601d07ec`.

Fresh post-admission reads showed 85 internal registry accounts and 77 public
profiles, each exactly one above its pre-admission baseline. Dr Dray appeared
exactly once in the internal index, public projection, and frontier, with
`onboarding_state=onboarded`, `monitoring_eligible=true`, and
`monitoring_scheduled=false`.

The Judgment supports five conservative capability claims: value translation,
recommendation adoption, odor-objection contradiction, practical safety/use
boundaries, and retail-walkthrough demand. It does not establish audience
demographics, verified purchases, product outcomes, or engagement-weighted
salience. Evidence is limited to two selected videos and bounded comment
samples.

## Pilot observations

All medians are same-format view-count medians over the observed bounded grid.
They must not be compared across formats as one aggregate.

| Creator | Resolved identity | Subscribers | Long-form grid | Shorts grid | Description/caption mention candidates | Native transcripts |
|---|---|---:|---:|---:|---|---:|
| Dr Dray | `UCnxmUrGMtpQT844Yd_l7Zyg` / `@DrDrayzday` | 2,670,000 | 30 rows; 11,000 median views | 30 rows; 28,000 median views | Brand-like candidates include Amlactin, Aveeno, Cetaphil, Costco, and Neutrogena | 0 |
| Doctorly | `UCHCZnC9akNA9pBP7aJGNKdg` / `@Doctorly` | 3,570,000 | 30 rows; 121,500 median views | 30 rows; 76,500 median views | none in the selected description/caption text | 0 |
| SkinZone | `UCyK4n2FRJrLUhrj-oGcSOxw` / `@SkinZoneTV` | 81,900 | 30 rows; 3,000 median views | 0 rows; median unavailable | `dralthea` is a brand-like candidate; the remaining extracted tokens are topical/self tags | 0 |
| Dr. Daniel Sugai | `UCUHuCyM-tBTVrTrwylOanSw` / `@danielsugaimd` | 718,000 | 30 rows; 24,000 median views | 30 rows; 11,500 median views | AlphaRet is a brand-like candidate; the remaining extracted tokens are topical/self tags | 0 |

The selected-video policy was captions first, triggered only when a selected
video was at or above its own format median and its title was ambiguous or
stance-bearing. Dr Dray triggered 2 of 4 selected videos, Doctorly 2 of 4,
SkinZone 0 of 2, and Dr. Daniel Sugai 4 of 4. YouTube exposed caption tracks for
the triggered videos but returned empty caption bodies to this public route.
Those rows are therefore explicit ASR-fallback candidates; no blanket ASR run
or transcript claim was made.

The mention field is deliberately named
`description_caption_mention_candidates`: extraction from descriptions and
captions supplies review candidates, not adjudicated competitors, sponsorship,
or independence evidence.

## Stops and limits

- SkinZone's public Shorts surface yielded zero rows. This is preserved as an
  observed absence, not converted to a zero-engagement claim.
- One deliberately wrong Doctorly evidence-video locator was rejected because
  its observed channel display name did not match the requested creator. The
  correct source-observed locator then resolved normally.
- Earlier superseded capture directories remain in operator scratch as defect
  evidence. They are not the final pilot packets and are not repository
  artifacts.
- Observed counts only. SERP recurrence evidences reach, not independence or
  sponsorship.

## Assessment artifacts

Final source-capture packets are operator scratch, not canonical repository
authority:

- `C:\tmp\forseti-youtube-creator-onboarding-20260730\dr_dray_v4\source_capture_packet`
- `C:\tmp\forseti-youtube-creator-onboarding-20260730\doctorly_v4\source_capture_packet`
- `C:\tmp\forseti-youtube-creator-onboarding-20260730\skinzone_v2\source_capture_packet`
- `C:\tmp\forseti-youtube-creator-onboarding-20260730\dr_daniel_sugai_v2\source_capture_packet`
- `C:\tmp\forseti-youtube-creator-onboarding-20260730\youtube_recurring_frontier_73_v0.json`

The implementation and tests under `forseti-harness/` own the durable adapter
contract. The live registry and Judgment receipts own Dr Dray's durable creator
status; this note is an evidence report, not registry authority.
