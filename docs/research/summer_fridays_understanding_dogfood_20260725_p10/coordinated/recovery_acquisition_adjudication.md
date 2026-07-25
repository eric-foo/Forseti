# Summer Fridays p10 Recovery Acquisition Adjudication

```yaml
retrieval_header_version: 1
artifact_role: Summer Fridays p10 post-seal recovery acquisition adjudication
scope: >
  Records the separately authorized recovery of the Sephora review/Q&A
  companion route, owner-directed exact-PDP materiality correction, bounded
  COV-006 probe, and Target/Amazon prior-corpus inventory.
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
  - COV-006 receives preserved acquisition and a new whole-gate adjudication.
```

## Current Gate

```yaml
recovery_state: SEPHORA_ROUTE_RECOVERED
acquisition_gate: blocked
deliver_allowed: false
remaining_blocker:
  route: COV-006
  reason: >
    The bounded hidden-venue probe found a material regulatory/product-safety
    category that p10 did not acquire: two California Proposition 65 notices
    naming Summer Fridays products. The probe is discovery evidence only; the
    source records have not yet been preserved and adjudicated into p10.
adjudicated_at: "2026-07-25T16:05:48.3911911+08:00"
```

The Sephora acquisition failure is cleared. Deliver is still not authorized
because COV-006 found a whole material category that remains probe-only.

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
used only in memory and are not persisted.

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

## COV-006 Probe

The bounded category-aware hidden-venue probe found a material
regulatory/product-safety category absent from p10:

- California Proposition 65 notice
  [2024-02857](https://oag.ca.gov/prop65/60-Day-Notice-2024-02857), naming
  Summer Fridays, Sephora, Mini Cloud Dew, and an alleged diethanolamine
  exposure;
- California Proposition 65 notice
  [2024-03063](https://www.oag.ca.gov/prop65/60-Day-Notice-2024-03063), naming
  Summer Fridays, Revolve, Rich Cushion Cream, and an alleged diethanolamine
  exposure.

These are private-party notices, not findings of violation, product contents,
liability, or current-formula status. The same probe also found official or
specialist venues for a Gap collaboration, National Eczema Association product
listings, USPTO proceedings, current careers/community claims, and a PETA
assurance-program discrepancy. Those surfaces may bound later claims but do not
erase the regulatory-category gap. Zero-result FDA/FTC queries are query
negatives, not certified absence.

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

## Next Required Move

Preserve and adjudicate the two COV-006 Proposition 65 notice records, including
their procedural status and claim ceiling, then rerun the whole acquisition
gate. Do not start Deliver before that adjudication.
