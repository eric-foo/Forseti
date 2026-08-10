---
retrieval_header_version: 1
artifact_role: Summer Fridays Route 1.7 full-corpus and SERP-linking shadow receipt
scope: Real customer-corpus census, retailer-source proof, and bounded SERP-link census; not a completed semantic integration view
use_when:
  - Auditing whether the Summer Fridays shadow run used the complete captured customer corpus and bounded SERP surfaces.
  - Continuing the external no-API semantic assessment from its exact denominator.
authority_boundary: evidence_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json
---

# Summer Fridays Route 1.7 full-corpus and SERP-linking shadow receipt v0

## Observed result

The reusable full-corpus controller and census were exercised against the real
Summer Fridays Phase A acquisition. The customer-corpus census completed with
no model API calls and reproduced the full captured denominator rather than the
historical 577-thread `used` family.

The retailer proof now pins all 95 source files by raw-byte SHA-256 and verifies
review membership through the source-native structures for Bazaarvoice,
Amazon, and Revolve. The bounded SERP dogfood covered 32 preserved unique
packet artifacts: all 12 sealed Phase 1 jobs, all 8 sealed Phase 2 jobs, and 12
later product-axis packets. The producer-backed correction represents them as
56 job surfaces because each of the 36 focused product-axis jobs keeps its
exact packet edge even when three jobs reuse one packet. It enumerated 371 external-source-bearing result
rows. The pre-hardening review record produced 315 unique native or
locator-recovery targets, 54 repeated-locator duplicates, and 2 explicit
exclusions. It used one routed default for the other 369 rows, so these are
mechanical-output observations, not a compliant per-row Route 1.7 semantic
review. Google people-also-ask and related-search prompts were not counted as
external sources. No pagination or wider web crawl ran.

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
- Exact accounting for every route in the final acquisition seal as semantic
  source, structured reference, discovery, control, duplicate, or blocked.
- Hash verification for the seal, every terminal route artifact, and every v3
  source fragment.
- Fail-closed v3 fragment merging with a separate lineage receipt.
- A source-native Reddit/retailer census that distinguishes captured,
  readable, mechanically excluded, and formerly screened-out leaves.
- A raw-byte retailer source manifest with structural review-ID verification.
- A repeatable producer-derived job-to-packet SERP surface spec, complete row inventory,
  agent-semantic review, deterministic locator de-duplication, and emitted
  target-reconciliation work.
- Validation of one extraction or reconciliation response as soon as it
  returns.
- Honest resumability status for valid, missing, duplicate, and invalid batch
  responses. Partial responses never compile into a complete view.

## Current boundary

This receipt does **not** claim that all 59,780 readable customer-language
items have already been semantically judged. Owned, paid-ad, PDP,
creator/native-social, and external-editorial materials remain verified
structured references; they do not owe customer-language corpus conversion.
The real audit accounted for all 20 sealed routes and correctly reported only
the two exhaustive semantic sources blocked: `reddit_community_scout` and
`retailer_review_qa_corpus`. Until both v3 fragments exist,
`materialize-phase-a-v3` must refuse to produce a final source. The 315 emitted
SERP recovery targets are retrospective work candidates, not claims that native
capture has completed.

The recorded SERP review must also be redone with one explicit decision for
each of the 371 inventory rows before it can support Route 1.7 linkage claims;
the controller now rejects its routed default. The captured target counts do
not prove that individual review or target-to-row binding.

The first shadow frontier reconciled sealed job IDs but relied on an
operator-declared packet set. The producer-backed correction closes that
specific gap: six terminal-return-selected queue-state receipts generated 20
Phase 1/2 job-to-packet edges (12 Phase 1 and 8 Phase 2), including two
explicit one-to-one recovery aliases. The 36 focused-search records generated
their own exact job edges. All 56 edges reconcile to the same 32 unique packet
artifacts and the same 371 eligible result rows; the evidence denominator did
not change. Removing the successful `p1_07_dupe` surface made the real builder
fail with `successful SERP producer job lacks a source surface` (exit 2).

Therefore this is a successful implementation and real denominator dogfood,
not a completed Summer Fridays integration view, Route 1.7 SERP-linking
review, acquisition reseal, market conclusion, or Deliver artifact.

## Lineage

- Implementation base: `b55508300bf2bd76dcd07a37e4e4dbb8ac44ea17`.
- Acquisition seal raw SHA-256:
  `d7346ff8bcdd827a93516cca791c35b10f7218d0e262ca09904ecac9e55350f6`.
- Evidence-depth ledger raw SHA-256:
  `20a5141d51698c01cce36586071f21a2aa91b6c5463251da28fd01c3368a18b5`.
- Retailer coding raw SHA-256:
  `28a1f92661cd2e75c40cbcea8adbf51206c15b418be2561e8dce17b6770a7cf6`.
- External retailer source manifest:
  `C:\tmp\forseti-summer-fridays-route-1-7-full-corpus-20260808\retailer_source_manifest_v1.json`
  (raw SHA-256 `92e346401bf75e5ce7ae3d46b991848f9678e60f5c22873b80aec53f54d9a04c`;
  content manifest SHA-256 `3f1209dac10c69777cb5969fcb0388c4db29269a5a91b8afbb3a81ae582dcc1e`).
- External census:
  `C:\tmp\forseti-summer-fridays-route-1-7-full-corpus-20260808\customer_corpus_census_v1.json`
  (raw SHA-256 `60f291fec5e3b6a0aa73457ca015631c55f802a10f0b90e1e6b7969fded0abe9`;
  content SHA-256 `82a89ca73572ed99fe7bb766aabe46741323b230464735b3382404c9e1946b74`).
- External blocked run spec:
  `C:\tmp\forseti-summer-fridays-route-1-7-full-corpus-20260808\run_spec_blocked_v1.json`
  (raw SHA-256
  `6e9420e29865c62c270cd55462383acf5f8a8db5c06bdcaebc312da0f27e0225`).
- External source audit:
  `C:\tmp\forseti-summer-fridays-route-1-7-full-corpus-20260808\source_audit_blocked_v1.json`
  (raw SHA-256
  `d5229fcf3018e14018d3fa499cfd91512a210c535f63a52832cb7a73ef39b611`;
  content SHA-256
  `0bc695c529fe211be37568118b832ba0bc9eb6cfdf743d50b80b2667904b764c`).
- External SERP surface spec, inventory, semantic review, and result live under
  `C:\tmp\forseti-summer-fridays-route-1-7-full-corpus-20260808\`; their raw
  SHA-256 values are respectively
  `5bcff9c9aafc6f0e3c04e56d5f61d55766abd6ca70667d9564cc86530fa68590`,
  `c028ba0422c2e5363c043fd80c147333f0dfd23bcba64f87acab37b68ce10799`,
  `67cfed6bbf318d021e9dbeb7895470b82ab0a513fb465889bfd37024cbac3fa9`,
  and `94a237874419cc81721ec849d9eebde46c64c3d7d929cb56251dc99d3d34053e`.
- Producer-backed correction artifacts live under
  `C:\tmp\forseti-summer-fridays-route-1-7-packet-inventory-20260808\`.
  The surface map, generated surface spec, and row inventory raw SHA-256 values
  are respectively
  `23f6deeb4ff76c19d4cec55883824931ac492c08341d9ebfb40c03005e41baac`,
  `e3f35b228790cee1c425052bb11e3acf819493ab58bf393096803b3b4a0b1158`,
  and `834f2b67191a380ad6133d8918e8342dafd24f17d2d3d7a56164a163759908c7`.
  The producer inventory content SHA-256 is
  `413b6112919563b8140d18bf8d2596e802fb6d4273c0790eddd77c923edc1931`;
  the surface-spec and inventory content SHA-256 values are
  `a18adc8d6015ad487fc37ed327277e5a943c3c3edde95f77f957e08c7cf1e852`
  and `57b7c4614358023e7caf26a77eb6c13584c22f3e442f9ce459cbbb43f10c0a74`.
- Historical acquisition seal restamped: `false`.
- Model API calls: `0`.
