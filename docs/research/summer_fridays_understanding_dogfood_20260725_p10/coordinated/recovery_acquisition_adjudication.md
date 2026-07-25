# Summer Fridays p10 Recovery Acquisition Adjudication

```yaml
retrieval_header_version: 1
artifact_role: Summer Fridays p10 post-seal recovery acquisition adjudication
scope: >
  Records the separately authorized recovery of the Sephora review/Q&A
  companion route, owner-directed exact-PDP materiality correction, bounded
  COV-006 reconciliation, whole-gate CI-fitness adjudication, and
  Target/Amazon prior-corpus inventory.
use_when:
  - Determining the current gate after the original blocked p10 seal.
  - Deciding whether the preserved p10 Sephora PDP corpus must be recollected.
  - Assessing prior Target or Amazon evidence for later Deliver use.
authority_boundary: recovery_adjudication
open_next:
  - docs/workflows/summer_fridays_understanding_dogfood_20260725_p10/coordinated/acquisition_seal.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/turn_a_acquisition_record.md
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
stale_if:
  - Any successful recovery companion packet or its parent changes.
  - Any claim-bearing COV-006 packet or the materiality rule changes.
```

## Current Gate

```yaml
recovery_state: SEALED_READY_FOR_DELIVER
acquisition_gate: passed
deliver_allowed: true
ci_fitness:
  materially_complete_for_bound_decision: true
  consequential_flaw_exposure: sufficient
  exhaustive_web_or_customer_corpus: false
  production_ci_readiness_claimed: false
cov_006:
  status: closed
  disposition: contextual_non_decision_bearing_monitor_only
  causation_between_notice_and_later_product_change: unproven
delegated_ci_fitness_review:
  reviewed_revision: 47eb324db57d079f4aa4178e798f7dccb084fa56
  returned_verdict: READY_FOR_DELIVER_AFTER_PATCH
  adjudication: accepted
  adjudicated_at: "2026-07-26T00:22:37.8401234+08:00"
  accepted_findings:
    - CODE-01
    - CODE-02
    - ART-01
    - ART-02
    - ART-03
    - ART-04
    - ART-05
adjudicated_at: "2026-07-25T21:26:28.6389180+08:00"
```

The recovery closes both material acquisition failures. The corpus is
materially complete for the bound Summer Fridays Understanding decision: it
can support useful synthesis and expose consequential weaknesses,
contradictions, and uncertainty without pretending to be an exhaustive web,
customer, legal, or product-safety corpus. This authorizes Deliver; it does
not itself perform Deliver or establish production-CI readiness.

## Sephora Composition Recovery

The p10 PDP corpus did not need recollection. Each of the 40 admitted canonical
parents retained:

- `retail_pdp_sephora_aggregate_content_v4`;
- the exact Sephora product and variant/SKU binding;
- a hash-verified successful US/USD capture-metadata record; and
- the parent source locator.

The companion now composes with that canonical parent. It first attempts a live
target-bound configuration refresh. When Sephora blocks that browser refresh, a
separately hash-verified, successfully pinned Sephora US packet may supply only
the public tenant-level Bazaarvoice read configuration. The retained p10 parent
and exact API `ProductId` filter remain the product binding. Read tokens are
used only in memory and are not persisted. A failed live refresh fails closed
before any packet is written, so the per-packet configuration receipts (five
live refreshes, 35 preserved-source contexts) are the observable record of
which route ran; route-level blocking remains an operator adjudication rather
than a per-parent receipt.

```yaml
recovery_raw_roots:
  - C:\tmp\forseti-sf-p10-deliver-recovery-data\sephora_lake
  - C:\tmp\forseti-sf-p10-deliver-recovery-data\sephora_lake_2
  - C:\tmp\forseti-sf-p10-deliver-recovery-data\sephora_lake_3
  - C:\tmp\forseti-sf-p10-deliver-recovery-data\sephora_lake_4
configuration_source:
  packet_id: 01KY4KPKD6MW2G2BASBPYMHM2Z
  manifest_sha256: 8928a83c725bd67e0462d0e20726d67ec89f2ca0bce180e38d67d68de41ac0f5
  source_locator: https://www.sephora.com/brand/summer-fridays?country_switch=us
  captured_at: "2026-07-22T09:49:52Z"
  capture_window_note: >
    Captured before the p10 execution window; admitted only as tenant-level
    read configuration, not as Summer Fridays subject evidence.
  role: tenant_read_configuration_only
  current_viability_probe:
    questions_status: 200
    reviews_status: 200
    has_errors: false
successful_companions:
  packet_count: 40
  unique_parent_count: 40
  duplicate_success_parent_count: 0
  live_target_bound_refresh_count: 5
  preserved_configuration_source_count: 35
  positive_question_contexts: 31
  source_declared_zero_question_contexts: 9
  positive_review_contexts: 32
  source_declared_zero_review_contexts: 8
direct_success_packet_verification:
  preserved_file_count: 200
  missing_file_count: 0
  hash_mismatch_count: 0
  size_mismatch_count: 0
```

Failed adaptation packets from intermediate recovery attempts remain
append-only diagnostic evidence. They receive no success credit.

### Source-declared zero-Q&A parents

These nine exact companion requests returned `TotalResults: 0`,
`HasErrors: false`. The PDP labels below are shortened for readability; each
link preserves the exact captured parent and SKU binding.

| Parent | Sephora PDP | Q&A response |
| --- | --- | --- |
| `P522831` | [The Bronzer Brush](https://www.sephora.com/product/the-bronzer-brush-P522831?skuId=2968881&country_switch=us&lang=en) | Source-declared zero |
| `P525593` | [Vanilla Hair + Body Fragrance Mist](https://www.sephora.com/product/hair-body-fragrance-mist-vanilla-P525593?skuId=2996726&country_switch=us&lang=en) | Source-declared zero |
| `P525613` | [Pink Guava Body Butter Balm](https://www.sephora.com/product/body-butter-balm-pink-guava-P525613?skuId=2995512&country_switch=us&lang=en) | Source-declared zero |
| `P525641` | [Pistachio Milk Body Butter Balm](https://www.sephora.com/product/body-butter-balm-pistachio-milk-P525641?skuId=2995504&country_switch=us&lang=en) | Source-declared zero |
| `P525642` | [Pistachio Milk Body Fragrance Mist](https://www.sephora.com/product/body-fragrance-mist-pistachio-milk-full-size-P525642?skuId=2996684&country_switch=us&lang=en) | Source-declared zero |
| `P525652` | [Mini Pink Guava Body Butter Balm](https://www.sephora.com/product/body-butter-balm-pink-guava-travel-size-P525652?skuId=2995488&country_switch=us&lang=en) | Source-declared zero |
| `P525659` | [Pink Guava Hair + Body Fragrance Mist](https://www.sephora.com/product/hair-body-fragrance-mist-pink-guava-P525659?skuId=2996700&country_switch=us&lang=en) | Source-declared zero |
| `P525660` | [Vanilla Body Butter Balm](https://www.sephora.com/product/body-butter-balm-vanilla-P525660?skuId=2995496&country_switch=us&lang=en) | Source-declared zero |
| `P525665` | [Mini Pistachio Milk Body Butter Balm](https://www.sephora.com/product/body-butter-balm-pistachio-milk-travel-size-P525665?skuId=2995470&country_switch=us&lang=en) | Source-declared zero |

## Exact PDP Materiality Adjudication

All 42 exact non-bundle Sephora listings received an attempted disposition.
Forty admitted canonical baselines. The two misses are:

| Product | Listing | Grid position | Grid reviews | Materiality |
| --- | --- | ---: | ---: | --- |
| `P525609` | Mini Pink Guava Hair + Body Fragrance Mist | 38 | 0 | Non-strategic middle-of-curve size expression in the already represented Body Fragrance Mist family |
| `P525633` | Mini Pistachio Milk Hair + Body Fragrance Mist | 40 | 0 | Non-strategic middle-of-curve size expression in the already represented Body Fragrance Mist family |

Both failures remain typed target-identity redirects. Neither carries a
distinct strategic product family, material seam, or required customer corpus;
the retained full-size and sibling family evidence supports the broad company
question. Under the owner-directed materiality rule, 40/42 is therefore an
accepted residual, not an acquisition blocker. This does not create a numeric
threshold or permission to skip attempts.

## COV-006 Reconciliation

The category-aware hidden-venue job is now performed and bounded. Seven
claim-bearing packets preserve the two California Proposition 65 notice
records, their PDFs, one current defendant-filtered registry result view, and
the relevant later company-owned product-state pages.

| Role | Packet | Manifest SHA-256 |
| --- | --- | --- |
| Notice 2024-02857 registry | `01KYCPQQMG1S28QA3RTQYMG6F0` | `264b2cc66f02ac6fd184fead9931aeb9cf8578af88755737e9a24a92a26df5f3` |
| Notice 2024-02857 PDF | `01KYCPQTPZK6XD8W08PQB0TZCE` | `1a2e70842b117f97d3e3653d3a2e68be1e46ba8633241c8101b232aea0e05688` |
| Notice 2024-03063 registry | `01KYCPQWXHM2NJ43Q6DCS9GAP0` | `35a4c6872ef80b798e5c794ea7aefb2a59007062542cb45def452a76c33bade0` |
| Notice 2024-03063 PDF | `01KYCPQZ670Z08047WTHRT3RR9` | `2720c074e1c1cf6c4e68dbb1548984ad0851bc53eab7009687b9a688441fa52c` |
| Later Cloud Dew formula statement | `01KYCPR0M5ZR4ZAZJJ7J5AKAHP` | `2960fa96f8d74fbe8cb5f3b15d2f94e482ce5dfbfc749b364488f4a457a640b1` |
| Current Rich Cushion product page | `01KYCPR29GBC32FJVXEGVQ0TGD` | `27b10cf8d24bd8fc8309f998a6c30673b52590cca2fdaab9aedbd6ff2d7ae0a7` |
| Current Summer Fridays registry results | `01KYCQ84THK86S9FDZVRRNKFN6` | `7a97a36ecf73d6a68bd9aec72fe2bfcc69f23f17d3f9444fdf7183c634d5ad41` |

```yaml
cov_006_raw_root: C:\tmp\forseti-sf-p10-deliver-recovery-data\cov006_lake
claim_bearing_packet_count: 7
claim_bearing_preserved_file_count: 14
whole_lake_direct_verification:
  manifest_count: 12
  preserved_file_count: 24
  missing_file_count: 0
  hash_mismatch_count: 0
  size_mismatch_count: 0
diagnostic_result_index_packets_without_target_binding: 5
diagnostic_packet_claim_credit: 0
```

The five diagnostic packets remain append-only failure evidence. Although each
returned HTTP 200, its result body did not bind the requested notice record.
The defendant-filtered packet above contains both target rows and is the only
result-index packet receiving claim credit.

The typed adjudication is:

- Notice `2024-02857` names Summer Fridays and Sephora in connection with Mini
  Cloud Dew and an alleged diethanolamine exposure. Notice `2024-03063` names
  Summer Fridays and Revolve in connection with Rich Cushion Cream and the
  same alleged chemical.
- These are private-party notices, not findings of violation, liability,
  product contents, safety, or remediation.
- At capture time, the public defendant-filtered registry row for each notice
  displayed `Complaint (0)`, `Settlement (0)`, and `Judgment (0)`, with no
  withdrawal record displayed. That is a bounded public-index observation,
  not proof that no private resolution or later unindexed event exists.
- Summer Fridays later described Cloud Dew as having an updated formula,
  updated ingredients, and new packaging. That chronology does not establish
  that the notice caused the change.
- Rich Cushion remains a current product. Its current online ingredient list
  does not name diethanolamine, but the page itself says packaging controls
  and the online list may be incomplete or stale. It does not prove the
  noticed product's historical composition or a remediation.
- Both company-owned product-state packets carry the shared Shopify
  challenge-classifier residual: their runner metadata records
  `access_failed`/`block_shell (hcaptcha)` although the exact source-native
  blog and product-page text is present and was manually inspected. The two
  statements above therefore carry the same
  `SUPPORTED_WITH_CLASSIFIER_RESIDUAL` ceiling as the p10 company-owned
  packets.

COV-006 is therefore closed as contextual, non-decision-bearing, and
monitor-only on current evidence. It belongs in Deliver as a bounded risk
signal and claim ceiling, not as a lead conclusion or a blocker.

The same probe surfaced candidate venues for a Gap collaboration, National
Eczema Association product listings, USPTO proceedings, current
careers/community claims, and a PETA assurance-program discrepancy. Of these,
only the National Eczema Association reference is durably preserved, inside
the captured Cloud Dew statement body; the others are unpreserved probe
observations and monitor pointers, not durable evidence. On the preserved
packets plus those typed observations, no additional decision-changing
missing evidence family is presently exposed. Zero-result FDA/FTC queries
remain query negatives, not certified absence.

## Target And Amazon Prior-Corpus Inventory

p06 and p07 contain no Target or Amazon subject packets.

| Retailer | Prior preserved substrate | Reuse ceiling |
| --- | --- | --- |
| Target | Five exact Summer Fridays PDPs in `C:\tmp\forseti-sf-target-null-safe-smoke`; one unique review for one TCIN; zero Q&A | Dated third-party listing or contradiction evidence only. Target is absent from the current company-owned authorized-retailer board, so these packets cannot receive authorized-channel credit. |
| Amazon | Thirty owned-parent-matched p05 PDP candidates; one 13-row bounded top-review companion for one ASIN; zero Q&A | `B0C5GF7YT6` is the strongest immediately reusable identity/provenance packet because it intersects the current official storefront evidence. The other candidates require current storefront/seller binding; the review packet supports only a dated bounded observation. |

Code capability is broader than preserved subject coverage. Reuse must retain
the original packet provenance, currentness ceiling, authorization boundary,
and exact product identity; it must not silently become fresh or complete
corpus credit.

## Gate Rationale And Next Move

The current corpus covers the commissioned company, portfolio/retailer,
customer/community, chronology, provenance, uncertainty, and hidden-venue
jobs at a materiality level sufficient for Deliver. It includes supportive,
negative, contradictory, and unresolved evidence, so a downstream
synthesizer can make useful decisions and expose consequential flaws rather
than merely summarize favorable material.

Accepted residuals remain explicit: two non-strategic Sephora mini-size PDP
misses, six bundle/set corpus-identity gaps, four unmatched retailer rows,
bounded non-representative community evidence, sparse REVOLVE review bodies,
one byte-identical viewport screenshot shared by the two verified mini Body
Butter Balm parents (`P525652`, `P525665`) whose content records, final URLs,
and US/USD capture metadata remain distinct and hash-verified, and attributed
company/market/currentness ceilings. None currently removes a strategic
product family, selected-retailer evidence family, material customer signal,
or decision-changing risk category.

Phase A acquisition is complete and Deliver is authorized. The commissioned
different-vendor CI-fitness review returned
`READY_FOR_DELIVER_AFTER_PATCH`; its seven accepted findings are incorporated
and its bound validation gates reproduce locally. This recovery lane stops
here. The review did not demand exhaustive provenance as the objective or
promote this seal into a production-CI readiness claim.
