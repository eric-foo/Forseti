# Summer Fridays Understanding p07 — Evidence-Layer Completion Dogfood

```yaml
retrieval_header_version: 1
artifact_role: evidence-layer dogfood record and p06-to-p08 comparison
scope: REVOLVE completion, durable TSG capture, and bounded Sephora four-family closure; no Turn B or company report
use_when:
  - Evaluating whether complete bounded review-corpus acquisition improves Phase A decision usefulness.
  - Verifying the completed Summer Fridays Phase A evidence layer without rerunning completed work.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/summer_fridays_understanding_dogfood_20260725_p07/acquisition_seal.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
stale_if:
  - The p07 completion receipt, TSG packet, p08 Sephora packets, or p06 control artifacts change.
```

## Bound question

Does acquiring one bounded `Most Recent` onboarding window for every distinct
accessible non-Sephora review corpus produce a more complete and reusable
customer-evidence layer than selecting a few products for deep capture first?

The p06 acquisition is the historical control. It was not modified or rerun.
This p07 completion reused its verified 37-PDP REVOLVE corpus and added no new
retailer. It did not start Turn B or author a company report.

## Dogfood execution

The p07 runner loaded all 37 retained REVOLVE PDP packets, verified their
manifests, bound each listing to the observed Yotpo store and product collection
context, and requested only source-labelled `Most Recent` ordering. Each
collection stopped at the shared onboarding bound: the complete source-ordered
30-day cohort when reachable within the cap, otherwise the 30 most recent rows
or source exhaustion. Native review IDs were deduplicated.

```yaml
retailer: revolve
provider: yotpo
requested_listings: 37
verified_listings: 37
distinct_collection_contexts: 37
completed_collection_contexts: 37
failed_collection_contexts: 0
row_positive_contexts: 30
source_declared_zero_row_contexts: 7
captured_occurrences: 607
unique_native_review_ids: 576
cross_context_duplicate_native_ids: 31
observed_overlap_components: 35
status: complete
```

Two overlap edges matter:

- the Jet Lag Mask and Mini Jet Lag Mask contexts shared 30 native review IDs;
- the Pink Dew Gel Cleanser and Mini Pink Dew Gel Cleanser contexts shared one
  native review ID.

Those overlaps are evidence that the displayed collections are related. They
do not make the run fail, and they do not justify collapsing unrelated products
merely because the retailer and Yotpo tenant are shared.

Primary receipt:

- `C:\tmp\forseti-sf-review-corpus-completion-20260725-p07-r3\completion-receipt.json`
- SHA-256:
  `93f738e4a7cf8702cc3b38f918364fd56e9efb8d3f5de7de0d5282d85c13dcf3`

## What the larger board actually contains

The 576 unique native rows contain 78 rows with text other than REVOLVE's
rating-only placeholder and 498 rating-only rows. Normalizing substantive text,
source date, and rating yields 76 unique substantive fingerprints. Of the 78
substantive native rows, 69 are source-marked non-incentivized. Twelve carry
employee-review metadata. Across all unique rows, nine are source-marked
incentivized and 262 carry sweepstakes metadata; none of the sweepstakes rows
contains substantive text in this bounded window.

This is a decision-useful result, including where the yield is thin:

- the board adds non-lip skincare, body, complexion/color, tool, set, and newer
  low-volume contexts that the three-product p06 sample could not represent;
- REVOLVE's admitted 37-listing grid contains no fragrance listing, so this
  retailer cannot close fragrance customer depth;
- high declared review totals often resolve to recent rating-only or campaign
  rows, so review count is not a defensible proxy for narrative yield; and
- native-ID overlap exposes shared or grouped feeds that would otherwise be
  double-counted as independent evidence.

The completed board is reusable acquisition, not a command to interpret all
576 rows. Category-balanced interpretation should prefer substantive,
non-incentivized rows and retain employee, sweepstakes, grouping, and
syndication metadata as claim ceilings.

## p06 control versus p07 completion

| Measure | p06 control | p07 completion | Meaning |
| --- | ---: | ---: | --- |
| REVOLVE collection contexts captured | 3 selected products | 37 / 37 listings | removes hero-product selection from raw acquisition |
| Native review occurrences | 150 | 607 | broader bounded evidence surface |
| Unique native review IDs | 150 | 576 | overlap is removed before evidence counts |
| Substantive native rows | 20 | 78 | materially more usable customer language |
| Unique substantive fingerprints | 19 | 76 | about 4x the distinct narrative substrate |
| Rating-only native rows | 130 | 498 | larger capture does not manufacture narrative evidence |
| Cross-context duplicate IDs | not tested across the full grid | 31 | reveals two shared-feed relationships |
| Zero-row contexts | not inventoried across the full grid | 7 | preserves real no-review outcomes |

The p07 run is better because it moves the selection decision after bounded
acquisition. A later consumer can choose categories or decision-specific
products without reacquiring the unselected catalog. The gain is not that every
row is useful; the gain is that absence, thinness, incentives, overlap, and
available narrative are now known across the admitted retailer denominator.

The bounded cost is also visible: 607 occurrences produced only 76 unique
substantive fingerprints. That is still worthwhile for Phase A because
reacquisition is the expensive, route-sensitive step; interpretation remains
selective. It would not be worthwhile as a full historical crawl or as a rule
to summarize every row.

## Durable company-event closure

The official TSG Consumer announcement was captured as a durable HTTP 200
packet. Its preserved body establishes the dated 2024 strategic growth
investment, the co-founders' retained significant stake and continued
leadership, and Prelude Growth Partners' exit. It also records John Heffner as
Chairman and CEO and Kim Natale as President in the transaction announcement.
Those titles are event-dated facts, not evidence of current 2026 leadership.

The earlier Business Wire route returned an HTTP 403 block shell and is not
evidence. The TSG-owned page is the admitted source.

Primary packet:

- manifest:
  `C:\tmp\forseti-sf-review-corpus-completion-20260725-p07-r3\company-events\tsg-consumer-announcement\manifest.json`
  (`60843928758834abae59bdd036f39a5d9d610f5369bc29038284903fb944acac`);
- body:
  `C:\tmp\forseti-sf-review-corpus-completion-20260725-p07-r3\company-events\tsg-consumer-announcement\raw\01_http_response_body.bin`
  (`e1b34ce4034b83a3ca9c4f8414d80a793cfdf307bfd742aba90f3512474b7d00`);
- response metadata:
  `C:\tmp\forseti-sf-review-corpus-completion-20260725-p07-r3\company-events\tsg-consumer-announcement\raw\02_http_response_metadata.json`
  (`48c4cb00c373cbb64b903a7d9363e6d4f9ff7b6087089728e383ef73e5d2fa81`).

Sunlit Vanilla is not treated as an acquisition blocker in this completion.

## Sephora four-family closure

The p08 completion captured normal US/USD Sephora PDP parents and standard
three-role onboarding packets for Lip Butter Balm, Dream Lip Oil, and Flushed
Lip Stain:

- Lip Butter Balm `P455936`: packet `01KYAKYRC9VZEA4X6K1QTX9Q6T`,
  manifest SHA-256
  `20aff7024cd5a5008d41cca0337e6948c5c9ff297fe0552034141f57354f38b4`;
- Dream Lip Oil `P509439`: packet `01KYAMHHHX43P6G86F2MZ68T3E`,
  manifest SHA-256
  `212639645fb3d199502bb594203313fa3abdf85d51eb784fb744ca8c8e3f8f6e`;
- Flushed Lip Stain `P520759`: packet `01KYAMHKJVYMXX27NVJBJVQZSW`,
  manifest SHA-256
  `4651b913a2fb6b4aefc499c688b6bcf5cd7a73abb41b1c7600136d288cd6bd29`.

Each carries `sephora_bazaarvoice_onboarding_summary_v4`. The remaining Jet
Lag family required explicit manual adjudication:

- full-size PDP `P429952` passed the standard Sephora US/USD profile in packet
  `01KYAPMN9M09NBVWKB2QGDV3MD` (manifest SHA-256
  `c4388a17eda66aaebd717dc790dfd7bd5e616e718fa3857f6c55ac00e40ce8e8`);
- mini PDP `P480630` passed the same profile in packet
  `01KYAPS9KZ0YM7GBAP4189CXQS` (manifest SHA-256
  `924eb51100c530bce8ad6f6b433c870dcf3223798949f38bb4d3231465413cf3`);
- the corresponding standard onboarding packets
  `01KYAPP8P40FRBYNH7EWF9YA7N` and
  `01KYAPSPP8ZSEPSKVDXQE6Z4VP` each preserved all three requested raw roles
  before the summary adapter failed closed.

The adapter failure is a conservative identity mismatch, not missing source
data. Both parent queries returned the same native family corpus:

| Role | Captured rows | Declared total | Native-ID overlap across parents | Observed source product IDs |
| --- | ---: | ---: | ---: | --- |
| Most Answers Q&A | 100 | 241 | 100 / 100 | `P429952`, `P480630`, historical mini `P443825` |
| non-incentivized Most Helpful | 100 | 2,393 | 100 / 100 | `P429952`, `P480630`, historical mini `P443825` |
| non-incentivized Most Recent | 100 | 2,393 | 100 / 100 | `P429952`, `P480630` |

The full-size and mini listings are already normalized to the owned
`jet-lag-mask` family. The provider's mixed IDs and byte-identical
question/helpful responses therefore establish a source-native grouped family
corpus. Manual seal adjudication admits that bounded family evidence while
preserving both `sephora_bazaarvoice_onboarding_adaptation_failure_v4`
outcomes. It does not relabel either parser result as success and does not
weaken the global product-identity check.

Raw role SHA-256 values from the full-size onboarding packet:

- Q&A: `4ea01de73c665dbe38afab77e15f1c5899fc2d35049f1494a13c2358916e7f12`;
- Helpful/statistics:
  `f4d70fa398b5538dd8bc617a33cc981a027045763d36ab5a45ea1d2dd50be9f2`;
- Recent:
  `ea9129abf34ec0eda3724cfd19c4dd4c0039d7441e3a8b3e588f48862e23169a`.

This closes the exact four-family Sephora job named by the p07 seal. The
separate 44-product direct-provider experiment remains test-only and is not
needed for this closure.

## Adjudication

The implementation and dogfood succeed for the bounded non-Sephora corpus-board
goal. They materially improve the Phase A evidence layer, close the durable TSG
transaction-event gap, and now close the bounded four-family Sephora job.

```yaml
implementation_dogfood: pass
revolve_review_corpus_board: complete
tsg_transaction_event_capture: complete
sunlit_vanilla_blocker: false
sephora_required_family_count: 4
sephora_standard_summary_success_families: 3
sephora_manually_adjudicated_grouped_family_fallbacks: 1
sephora_review_corpus_board: complete
phase_a_complete: true
phase_b_started: false
turn_b_started: false
company_report_exists: false
```
