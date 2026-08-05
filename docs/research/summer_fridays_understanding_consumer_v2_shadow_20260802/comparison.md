# Summer Fridays Consumer-Brand v2 Shadow Comparison

```yaml
retrieval_header_version: 1
artifact_role: Non-authoritative shadow-dogfood comparison
scope: >
  Read-only comparison of the sealed Summer Fridays p11r4 v1 evidence-depth
  result with the new consumer-brand v2 completion contract.
use_when:
  - Checking what the consumer-brand product-axis contract changes in practice.
  - Distinguishing preserved historical v1 completion from a future v2 run.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260801_p11r4/coordinated/evidence_depth_ledger.json
  - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
  - forseti-harness/tests/unit/test_summer_fridays_consumer_v2_shadow.py
stale_if:
  - The consumer-brand v2 profile, validator, or p11r4 historical artifacts change.
```

## Boundary

This dogfood performed no live capture, did not modify the historical p11r4
ledger or seal, and did not start Deliver. The test loaded the real p11r4 seal
and ledger, confirmed v1 first, then constructed a temporary v2 shadow. It
mechanically renamed the external-context family, classified its source types,
and marked the obvious official Summer Fridays account as owned. It did not
invent product-axis, retailer-coding, official-date, or saturation evidence
that the historical ledger does not contain.

## Observed comparison

| Contract | Observed result | Meaning |
| --- | --- | --- |
| Historical `broad_company_understanding_v1` | `PASS` | The preserved p11r4 seal still satisfies the contract under which it was written. |
| Shadow `broad_consumer_brand_understanding_v1` | `BLOCKED` | Aggregate family depth remains sufficient, but the evidence cannot receive v2 product-axis completion credit. |

The v2 shadow produced these exact findings:

- `missing_consumer_brand_product_axes`
- `missing_retailer_axis_coding`
- `missing_owned_social_published_at`
- `invalid_owned_social_direction_event_tags`
- `invalid_saturation_batch_new_product_axes`
- `invalid_saturation_batch_changed_axis_strengths`
- `invalid_saturation_batch_changed_axis_incidence`
- `passing_consumer_brand_seal_without_axis_closure`
- `passing_seal_without_saturation_closure`

It produced no `passing_seal_below_depth_floor:*` finding. The comparison
therefore isolates the actual process difference: p11r4 has enough aggregate
external, retailer, forum, and social material, but its seal does not prove how
that material stacks around each material product pain or strongest delight.

## Before and after

| Phase A behavior | v1 Summer Fridays run | Future consumer-brand v2 run |
| --- | --- | --- |
| Completion unit | Evidence-family totals plus generic material seams | Material product axes backed by those families |
| Retailer result | 975 deduplicated rows reported as corpus depth | Every eligible text row coded to axes and explicit choice outcomes; incidence recomputed per corpus |
| Community/social result | Thread, post, creator, platform, and perspective totals | Source IDs attached to axes; owned/paid/unknown relationships excluded from independent corroboration |
| Official posts | Twelve content units and one creator | Owned rows also carry dates and direction-event tags for a derived timeline |
| Focused search | Specialist-derived Phase 2 queries | Two adaptive goals per material axis; material source pointers must be captured or terminally dispositioned |
| Saturation | No new generic seam or changed seam disposition in the final two batches | Also no new product axis, changed axis strength, or changed retailer incidence |
| Prevalence ceiling | Qualitative, non-representative | Recurrence plus captured-retailer-sample incidence; still not customer-population prevalence |

## Interpretation

V2 does not say the Summer Fridays evidence is worthless or that its historical
seal was false. It says the existing pack cannot be promoted retroactively into
an axis-complete consumer-brand substrate. Several likely pain and delight axes
exist in the prose and raw evidence, but the historical run did not preserve the
row coding, source-to-axis links, relationship eligibility, focused job pairs,
or axis-aware dry batches needed to verify their strength mechanically.

Reconstructing those fields from existing raw evidence would be a new bounded
acquisition-analysis work unit. Any remaining material focused-source jobs
would then require their own authority before capture. This shadow comparison
does not authorize either action.
