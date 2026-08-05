# CO2 — Retailer Evidence Floor Continuation Return

```yaml
retrieval_header_version: 1
artifact_role: CO2 retailer hard-floor continuation terminal return
commission_id: BEAUTY-DIEUX-PHASEA-COMPLETION-003
cycle_id: DIEUX-UNDERSTANDING-20260805-003
authority_boundary: evidence_only_no_phase_a_closure_no_deliver
terminal_status: floor_met_source_exhausted
```

## Outcome

The retailer evidence floor is closed at **990 effective source-visible text
reviews**, 240 above the required 750:

| Unit | Effective text reviews | Accounting |
| --- | ---: | --- |
| Sephora / Bazaarvoice | 913 | Full non-incentivized Instant Angel product-group walk, source exhausted at 915 native IDs; two ratings-only rows excluded |
| Soko Glam / Okendo | 77 | Existing six-product corpus after its prior fresh/pinned deduplication |
| Combined | **990** | Zero exact whitespace-normalized body overlaps across the two retailer corpora |

The prior Sephora windows contained 183 distinct text-bearing native review
IDs. All 183 occur in the full walk, so the continuation contributes exactly
**730 additional distinct non-incentivized text reviews**, not 913. Native-ID
deduplication therefore moves the baseline from 260 to 990.

## Terminal Sephora walk

Successful packet `01KZ9DS86EQDMDZM0NCED14YQ4` used the already verified
hash-bound PDP parent `01KZ99GS7BYP0ZC7MQ4AY8260N`, Bazaarvoice filter
`ContextDataValue_IncentivizedReview:eq:False`, `SubmissionTime:desc`, and
100-row pages. Ten contiguous pages covered offsets 0 through 900; the final
page contained 15 rows and the runner certified `source_exhausted` at
`TotalResults=915`.

Exact terminal accounting:

- 915 rows and 915 unique native review IDs.
- 913 rows with source-visible text, 913 unique text-bearing IDs, and 913
  unique whitespace-normalized bodies; zero internal duplicate-body groups.
- Two ratings-only rows (`328608204`, `303942650`) are excluded from the text
  floor.
- Every row carries raw `IncentivizedReview=False`, `IsSyndicated=false`, and
  `SourceClient=sephora`.
- Product-group rows: `P510288` has 880 rows / 878 text bodies; historical or
  unlisted Mini Instant Angel member `P517955` has 35 rows / 35 text bodies.
  The latter remains provider-group evidence, not a current-SKU claim.
- Source dates span `2024-02-07T05:24:41Z` through
  `2026-08-04T15:34:47Z`.

The first attempt, packet `01KZ9DQ7XC63VSX5VXRE5QDTWN`, failed closed with
`IncompleteRead` on terminal offset 900 after preserving 11/12 response
documents. It receives no row credit. The retry completed, and both packets
remain append-only audit evidence.

## Rating and context reconciliation

Sephora's 913 text reviews have this exact distribution:

| Rating | Reviews |
| ---: | ---: |
| 1 | 82 |
| 2 | 64 |
| 3 | 53 |
| 4 | 58 |
| 5 | 656 |

Bands are 146 low (1–2), 53 mid (3), and 714 high (4–5). Combined with the
77-row Soko corpus, the mechanical distribution is 86 / 66 / 55 / 67 / 716
for ratings 1 through 5; bands are 152 low, 55 mid, and 783 high. These counts
are corpus accounting, not prevalence or market consensus.

The profile requirement passes with six truthful product contexts and five
source-visible categories from the fresh Soko collection:

| Product context | Source-visible category |
| --- | --- |
| Baptism | Water Cleanser |
| Air Angel | Facial Moisturizer |
| Instant Angel | Facial Moisturizer |
| Forever Eye Masks | Eye Mask |
| Auracle | Eye cream |
| Deliverance | Serum/Ampoule |

Instant Angel is one cross-retailer product context while the Sephora and Soko
corpora remain separate evidence units. Sephora's grid did not expose a
category field, so it adds no category credit. `P517955` is retained as a
distinct provider product identifier for Mini Instant Angel but is not inflated
into a new canonical category or product-context count.

## Incentive, syndication, and overlap ceiling

The 913 admitted Sephora text rows are all explicitly non-incentivized and
non-syndicated. Soko is not recoded: its fresh Instant Angel response has 16
incentivized and 16 non-incentivized rows, while incentive state is unavailable
for the 45 other pinned rows. Soko origin is explicit as
`externalProvider=shopify-shop` for 4/32 fresh Instant Angel rows and absent for
the remaining 28 plus the 45 pinned additions.

Exact normalized-body comparison between all 913 Sephora text rows and all 77
Soko bodies found zero overlaps. This supports separate retailer-specific
corpora only; it does not prove author-population independence, prevalence,
consensus, paraphrase absence, or recurrence outside the captured surfaces.

## Packet and raw-hash receipts

| Attempt | Packet status | Manifest SHA-256 | Receipt SHA-256 |
| --- | --- | --- | --- |
| `01KZ9DQ7XC63VSX5VXRE5QDTWN` | Failed closed; 11 responses preserved; no evidence credit | `69d27b05bae2fe509d101c489c1013f5c281e6ce88c3334ea2bbb0c85454bddc` | `9ec277581df64c451223fb4bff28db1e1077587d15b341efa1ee2e6ab66490f0` |
| `01KZ9DS86EQDMDZM0NCED14YQ4` | Complete; source exhausted | `934742be480fb423acfc9cd44e89021af7b76f54eb3786268293e62a6c2c894c` | `9b7f848011e6f1719aeb51e513559c0878831c857b9c4b04c7f4b91af2955587` |

The successful packet is rooted at
`C:\tmp\forseti-dieux-phase-a-completion-20260805-p03\co2\lake\raw\62b\01KZ9DS86EQDMDZM0NCED14YQ4`.
Its manifest freshly verifies all 14 preserved files. The complete per-response
byte counts and hashes—including every recent-order page, the request manifest,
the 4,368,559-byte summary, and the failed attempt's preserved responses—are in
`co2_retailer_floor_continuation.json`.

```yaml
retailer_hard_floor: passed
required_effective_unique_reviews: 750
terminal_effective_unique_reviews: 990
margin_above_floor: 240
additional_distinct_non_incentivized_text_reviews: 730
phase_a_closed: false
deliver_started: false
commit_created: false
push_performed: false
pull_request_created: false
```
