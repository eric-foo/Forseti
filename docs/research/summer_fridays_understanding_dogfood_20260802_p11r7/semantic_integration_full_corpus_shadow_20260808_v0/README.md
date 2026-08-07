---
retrieval_header_version: 1
artifact_role: Summer Fridays Route 1.6 full-corpus shadow receipt
scope: Real customer-corpus census and reusable-run implementation proof; not a completed semantic integration view
use_when:
  - Auditing whether the Summer Fridays Route 1.6 run used the complete captured customer corpus.
  - Continuing the external no-API semantic assessment from its exact denominator.
authority_boundary: evidence_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json
---

# Summer Fridays Route 1.6 full-corpus shadow receipt v0

## Observed result

The reusable full-corpus controller and census were exercised against the real
Summer Fridays Phase A acquisition. The customer-corpus census completed with
no model API calls and reproduced the full captured denominator rather than the
historical 577-thread `used` family.

| Corpus | Captured | Readable / assessable | Mechanical exclusion |
|---|---:|---:|---:|
| Reddit conversations | 804 containers | — | — |
| Reddit roots plus comments | 57,203 leaves | 56,580 | 623 |
| Former `captured_excluded` Reddit conversations | 221 containers / 18,476 leaves | 18,266 | 210 |
| Retailer reviews | 3,698 | 3,200 | 498 rating-only rows |
| Combined customer-language leaves | 60,901 | 59,780 | 1,121 |

The six pre-reconciliation legacy Reddit packets are included. The
`1gti140` sentinel is included with 186 captured and readable root-plus-comment
leaves. This is the thread that the old selected-family path would have lost.

The first live census attempt returned only 577 threads and 38,642 leaves. It
was rejected because it had inherited the old `families.reddit_forum.threads`
subset. The corrected census uses the union of all target-reconciliation rows
with native packet bindings plus the explicitly named legacy parent packets.
That perturbation is retained here because it proves the new gate catches the
specific false-success path it was built to prevent.

## What is implemented

- An immutable `phase_a_semantic_integration_run_v1` control spec.
- Exact accounting for every route in the final acquisition seal as evidence,
  discovery, control, duplicate, or blocked.
- Hash verification for the seal, every terminal route artifact, and every v3
  source fragment.
- Fail-closed v3 fragment merging with a separate lineage receipt.
- A source-native Reddit/retailer census that distinguishes captured,
  readable, mechanically excluded, and formerly screened-out leaves.
- Validation of one extraction or reconciliation response as soon as it
  returns.
- Honest resumability status for valid, missing, duplicate, and invalid batch
  responses. Partial responses never compile into a complete view.

## Current boundary

This receipt does **not** claim that all 59,780 readable customer-language
items have already been semantically judged. It also does not claim that the
owned, paid-ad, PDP, creator/native-social, and external-editorial families
have been converted into their final v3 source fragments. Until every sealed
evidence route has a hash-pinned fragment, `audit-phase-a-source` must report a
blocked run and `materialize-phase-a-v3` must refuse to produce a final source.
The real audit accounted for all 20 sealed routes and correctly reported 11
evidence routes blocked on missing final v3 fragments; it verified no source
binding because none was falsely supplied.

Therefore this is a successful implementation and real denominator dogfood,
not a completed Summer Fridays integration view, acquisition reseal, market
conclusion, or Deliver artifact.

## Lineage

- Implementation base: `b55508300bf2bd76dcd07a37e4e4dbb8ac44ea17`.
- Acquisition seal raw SHA-256:
  `d7346ff8bcdd827a93516cca791c35b10f7218d0e262ca09904ecac9e55350f6`.
- Evidence-depth ledger raw SHA-256:
  `20a5141d51698c01cce36586071f21a2aa91b6c5463251da28fd01c3368a18b5`.
- Retailer coding raw SHA-256:
  `28a1f92661cd2e75c40cbcea8adbf51206c15b418be2561e8dce17b6770a7cf6`.
- External census:
  `C:\tmp\forseti-summer-fridays-route-1-6-full-corpus-20260808\customer_corpus_census_v4.json`.
- External census raw SHA-256:
  `fce86afed6bc50e4568e5ead2ccc5f09d16794b187f5b515b0eb1a5c70d2c48f`.
- Census content SHA-256:
  `523fc3c48a86fee45ee55f6c0329237b954fd114cd40b58e87e23c090a60c934`.
- External blocked run spec:
  `C:\tmp\forseti-summer-fridays-route-1-6-full-corpus-20260808\run_spec_blocked_v0.json`
  (raw SHA-256
  `2ee558cd6dc88b0ef17a13c5aa9df624d9d3833657ccb3eadc1aa11388d45039`).
- External source audit:
  `C:\tmp\forseti-summer-fridays-route-1-6-full-corpus-20260808\source_audit_blocked_v1.json`
  (raw SHA-256
  `e6a7b80ebe86b92137daea3b296c905005e10aeb15f6e00150c95ce9488eb089`;
  content SHA-256
  `6e4e008b6cd91c00fcedf7be50ef27692e7d6cf073368a5f58dd5be7e4a6f813`).
- Historical acquisition seal restamped: `false`.
- Model API calls: `0`.
