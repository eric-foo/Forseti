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
(`community_post` and `retailer_review`). The axis evidence packet returns this
stack plus one other wear proposition: three evidence items across two selected
propositions, with `truncated: false`. One non-equivalent semantic unit remains
explicitly unmerged. This is a retrieval structure, not a prevalence estimate,
product conclusion, causal claim, or Deliver recommendation.

## Mixed-product restraint

The Reddit evidence also contains variant and comparator language. `Poppy`,
`Vanilla Beige`, and `Brown Sugar` remain conditions or statement content;
`Glossier Balm Dotcom` remains comparison language. The run did not invent
stable product IDs for them and did not credit them as separate customer
origins. Product assignment came from the preserved leaf and context, while
the catalog constrained the identifiers the worker was allowed to emit. All
terminal propositions have an empty `product_version_ids` list.

## Failure visibility

The first three reconciliation responses passed response-shape validation but
failed final compilation. A Sephora recommendation was first labeled company
strategy, then customer experience, then reported behavior. None was supportable
under both the retailer source role and its upstream evidence posture, so the
final accepted response left that unit explicitly unmerged. All failed response
and compilation artifacts remain in the external run.

## Exact observed lineage

Large artifacts remain external under
`C:\tmp\forseti-summer-fridays-product-catalog-reach-dogfood-20260809-v3`.
The machine-readable receipt beside this file records the exact evidence IDs,
hashes, counts, and selected proposition.

- Source SHA-256: `9b3823bfe8f46f6afc2c18f328da38de8d3ea88b9ef16edfb64dd3a4498cfa22`.
- Catalog SHA-256: `a95c1a57a30c8e82c832762e98038d02fddfaee8dcf378c1798be075d613dcda`.
- Bundle SHA-256: `ac9846d824fa803c72b123ed93716969bf1e50fb4b23f1c9cda7079c239bf15d`.
- Method SHA-256: `27fbb4a367c3d2decffca495c28b36e2807fb626ff5bd5d9e1891f573c76b016`.
- Final view SHA-256: `6576320d88ce2032241e1681f014f5dd03803f220ddecb788cb1869f8216acb2`.
- Axis packet SHA-256: `7543ec72a65c8ed7b6a41a25c2cebf74972033a1c6b568f93fd1dcb37c762178`.

One 9,898-byte prompt covered all four leaves. Extraction and reconciliation
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
