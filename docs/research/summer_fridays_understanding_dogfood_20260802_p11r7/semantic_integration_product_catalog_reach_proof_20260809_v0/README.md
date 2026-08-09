---
retrieval_header_version: 1
artifact_role: Summer Fridays product-catalog reach and cross-source stacking proof
scope: Complete bounded method-v4 shadow proof over real empty-candidate Reddit leaves and Sephora reviews; evidence structuring only
use_when:
  - Auditing semantic product binding when an admitted customer leaf has no upstream product candidate.
  - Preparing or reviewing the full Summer Fridays customer-corpus method-v4 run.
authority_boundary: evidence_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_product_catalog_reach_proof_20260809_v0/receipt.json
---

# Summer Fridays product-catalog reach proof v0

## Observed result

This bounded no-provider shadow run accounted for four preserved customer
leaves: two Reddit comments whose upstream `product_candidates` were empty and
two Sephora Lip Butter Balm reviews. A hash-bound catalog supplied the verified
product vocabulary once in the reading assignment. The semantic worker used
the leaf plus its preserved conversation or product-page context to bind all
four leaves to `summer-fridays-lip-butter-balm`; the catalog name alone was not
treated as evidence.

The run produced one bounded cross-source proposition on
`wear_and_longevity`. It links:

- Reddit `reddit:171ciwt:k3r1zda`: the commenter reports needing to reapply,
  especially after drinking; and
- Sephora `retailer:sephora_product_group_reviews:207164623`: the reviewer
  reports that the product does not last and needs reapplication.

The proposition retains two independent origins and two source roles
(`community_post` and `retailer_review`). The axis evidence packet returns both
source items with `truncated: false`. Eighteen non-equivalent semantic units
remain explicitly unmerged. This is a retrieval structure, not a prevalence
estimate, product conclusion, causal claim, or Deliver recommendation.

## Mixed-product restraint

The Reddit evidence also contains variant and comparator language. `Poppy`,
`Vanilla Beige`, and `Brown Sugar` remain conditions or statement content;
`Glossier Balm Dotcom` remains comparison language. The run did not invent
stable product IDs for them and did not credit them as separate customer
origins. Product assignment came from the preserved leaf and context, while
the catalog constrained the identifiers the worker was allowed to emit.

## Exact observed lineage

Large artifacts remain external under
`C:\tmp\forseti-summer-fridays-product-catalog-reach-dogfood-20260809-v2`.
The machine-readable receipt beside this file records the exact evidence IDs,
hashes, counts, and selected proposition.

- Source SHA-256: `9b3823bfe8f46f6afc2c18f328da38de8d3ea88b9ef16edfb64dd3a4498cfa22`.
- Catalog SHA-256: `a95c1a57a30c8e82c832762e98038d02fddfaee8dcf378c1798be075d613dcda`.
- Bundle SHA-256: `7d1124161fc5af150d7451cb89a9bfcd0accb0d21ecde97f96b253b48837e08e`.
- Method SHA-256: `6338a5f787ccb437db8b18905aa55987872f60fece570d5394ba1539ee6dca9c`.
- Final view SHA-256: `7266649618bb6daab7214a92b59c946d5e0f12fa45cdbd51b7f7f030aeb41a1f`.
- Axis packet SHA-256: `910c4eb714aedaf3664129282d2cbd5da9b133a4a7243818a20e35cb3faa4499`.

One 9,746-byte prompt covered all four leaves. Extraction and reconciliation
were each performed by a cold agent from the bound artifacts. Model/provider
API calls were zero. Rebuilding the earlier 300-leaf bounded proof under the
current code reproduced its historical source SHA-256 exactly:
`540b5f9211a44da915ad32ea22f6f6e3c28f663dc783904c76683c15d2b3ee2f`.

## Boundary and next step

This proves the missing-candidate product-binding path and a real
Reddit-to-retailer evidence stack on a bounded slice. It does not prove that
all 59,225 assessable Summer Fridays leaves complete under the new method. The
next step is different-vendor delegated review and home adjudication of this
revision. Only then should cold workers execute the full customer corpus.

