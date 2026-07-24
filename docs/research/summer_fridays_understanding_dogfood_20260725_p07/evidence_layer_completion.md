# Summer Fridays Understanding p07 — Evidence-Layer Completion Dogfood

```yaml
retrieval_header_version: 1
artifact_role: evidence-layer dogfood record and p06-to-p09 comparison
scope: REVOLVE completion, durable company/event capture, Sephora customer-depth closure, and whole-gate reconciliation; no Turn B or company report
use_when:
  - Evaluating whether complete bounded review-corpus acquisition improves Phase A decision usefulness.
  - Verifying the completed Summer Fridays Phase A evidence layer without rerunning completed work.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/summer_fridays_understanding_dogfood_20260725_p07/acquisition_seal.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
stale_if:
  - The p07 completion receipt, company/event packets, p08 Sephora packets, p09 body-launch packets, or p06 control artifacts change.
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

## Whole-gate reconciliation

A fresh whole-gate read after the earlier blocked-to-pass transition exposed
three material bases that the last-blocker-only adjudication had missed. The
p06 artifacts remain the historical control; this section records the
supplemental correction.

### Current body-category expansion

The admitted p06 Sephora grid already contained ten new, zero-review launch
placements that the onboarding had retained as `UNMATCHED_MATCH`. A current
company-owned body collection independently exposes six products as coming
August 6: Vanilla, Pink Guava, and Pistachio body fragrance mists plus the same
three scents as Body Butter Balms.

The ten grid placements reconcile to six launch families rather than ten
independent products:

| Normalized family | Sephora placements | PDP result |
| --- | --- | --- |
| `body-fragrance-mist-vanilla` | `P525593` | admitted baseline |
| `body-fragrance-mist-pink-guava` | `P525659`, mini `P525609` | parent admitted; mini route failed twice |
| `body-fragrance-mist-pistachio-milk` | `P525642`, mini `P525633` | parent admitted; mini route failed twice |
| `body-butter-balm-vanilla` | `P525660` | admitted baseline |
| `body-butter-balm-pink-guava` | `P525613`, mini `P525652` | both admitted |
| `body-butter-balm-pistachio-milk` | `P525641`, mini `P525665` | both admitted |

Eight exact US/USD PDP baselines passed the Sephora aggregate profile. The two
mist travel-size URLs redirected to search on both the canonical attempt and
the one exact-SKU retry and are not admitted as successful PDP packets. Their
grid rows remain typed placements; the corresponding admitted full-size
parents expose a two-size choice and bind the same scent/product family. The
failures therefore remain visible exact-placement residuals without creating
two additional product families or erasing the material body/fragrance
expansion.

Primary packets:

| Evidence | Packet | Manifest SHA-256 |
| --- | --- | --- |
| Official body collection | `01KYATGMXV504G5C4YDA5NVMS9` | `bb3adebc0fa8227b5ce34fad328bc77c69abda10e68f860116bd35038d3f9876` |
| `P525593` | `01KYATPF3C10Z5HGHQYGHH85GG` | `a30e3a9afdc231ed5d022ed34d03487cae4f46b76832a0e277e51719b4aca7df` |
| `P525613` | `01KYATRDM1AF7FKTGE6QD8RQCN` | `2b08307f9af8558ef2be7fb020bf7c5ea9a8300594bba74589e9218f60e4aede` |
| `P525641` | `01KYATTBGM5883XFJVV1GXA8WV` | `6fb2dcca4e44203a80451e614c131d14d1dcb471aa3018699faaffcff8e1b852` |
| `P525642` | `01KYATVCS70HA001G3T9YV369J` | `6848e46ea6926eb1d904c093240106460929561fe78119ceeb77c56036ef5726` |
| `P525652` | `01KYATWFQRRF8MKE3CZV9G0SJ3` | `c0969ebde92ae50a69ef26997e57eeef9ef90de0c37c3c64d1cc934890d04579` |
| `P525659` | `01KYATXKNP2QGXAA1DP551GS14` | `c97b0f4e1f559d6e748ed860ee5920988eeec673e63dc940f2eb1436c7d3ea22` |
| `P525660` | `01KYATYKK1SSE5MG4EKDR8DN0R` | `26130dc79f69dceedc287b93ce457f8dd19d855cf1ef58a0f5d3fc2177297633` |
| `P525665` | `01KYATZKFF42RQXNK551S2M40Z` | `10f76f713bb90adf91e6e4b2d75e28001b481ff9d2bfe5b75e04dad349c796c5` |
| `P525609` failed retry | `01KYAV1FQRAN4993RFXCCFSEPP` | `e0b19f858b22e017f9428c83c2bec05fa0970970840d95cc81252f0543ef42cd` |
| `P525633` failed retry | `01KYAV2CDPNWJTK0KP82KTZHB4` | `e3068ca696736295b564231ea725b521019b9eb3d01b23a2e8df36f415326d4f` |

All packets are under
`C:\tmp\forseti-sf-phase-a-seal-hardening-20260725\`.

### Outside-in scale and channel position

A current Forbes contributor profile reports that Summer Fridays ranked first
among skincare brands at Sephora in YipitData's 2025 US sales rankings, held
seven of Sephora's top ten skincare SKUs, and recorded double-digit global
retail-sales growth in 2025 after expansion to more than 830 Sephora EU doors
across 15 countries. These are publisher-reported traction and channel-position
claims, not audited company financials, present sales, market share, or a
guarantee of future rank.

The browser packet is `01KYATGW3NF39N6RD6MPC8JRY5`; manifest SHA-256
`d630dbecfb63288a7a9e4f44cdb20aac1e406d65c69a05f827d44d22aa91b2e2`.

### Jet Lag production incident

The official historical statement says certain third-party-manufacturer
production batches were compromised. It records stricter manufacturing
protocols, a minor reformulation including removal of essential oils, returns
of specified retailer lot codes, refunds, and patch-test guidance. This is
evidence of a historical production and response event. It does not establish
that current product or current customer complaints come from an affected
batch.

The browser packet is `01KYATH20TG6KSZHD4EWAQ1QR4`; manifest SHA-256
`986090638cb6b39bcbf37c4b5ed37f538f4349d1f855065ca22e9ea2d75cfb36`.

### Sunlit Vanilla official review-provider probe

The official PDP visibly reports 961 reviews and loads a Yotpo widget for
Shopify product `7633970888781` using store identifier
`hAnCQ8TdC1im1AlyOrM2vMEn3Fdg8zmmdzJ4M32n`. The rendered DOM also carries
alternate/legacy Okendo metadata with a count of 26, so the aggregate is not
treated as provider-clean merely because Yotpo is the active widget. No review
rows were captured and no native-ID overlap was measured. This probe therefore
adds no independent customer-row credit and establishes no dedupe relationship
with REVOLVE's separate Yotpo tenant.

The browser packet is `01KYATH7GMH5CGHRPN6G3C2JP6`; manifest SHA-256
`1f51bf8951d8b3d9c19ef1e42a600aa1acaca4b6989a3c648a7bb7448e93519b`.

### Preserved access failures

The first direct-HTTP attempt for each of the four pages was preserved as a
typed access shell and is not source evidence: body collection
`9d0e966939bcd96ea11ae707be43bd34e053c5b1732d19b76accd606c426240a`,
Forbes `9eda5b4050e0a96cbb9569044e64d892c29a050f63e463ddeb5ae812614cd60e`,
Jet Lag statement
`c43289391328cb0b98eaaf8ea7c0412bd96ef1550277f06029f01991476e0999`,
and Sunlit PDP
`d0b39aee3c7d32b7f54326f733062d458a85f7726dff1b0ae0562179e4bf66b1`.

## Adjudication

The implementation and dogfood succeed for the bounded non-Sephora corpus-board
goal. The fresh whole-gate reconciliation also closes the material company
scale/position, body-launch trajectory, and production-incident bases that the
earlier last-blocker-only pass missed. The two failed travel-size PDP routes and
Sunlit row-level provider overlap remain explicit non-material residuals.

```yaml
implementation_dogfood: pass
revolve_review_corpus_board: complete
tsg_transaction_event_capture: complete
company_scale_position_check: complete_with_claim_ceiling
jet_lag_incident_capture: complete_historical_event
body_launch_grid_placements: 10
body_launch_normalized_families: 6
body_launch_pdp_baselines_admitted: 8
body_launch_exact_placement_route_failures: 2
sunlit_vanilla_blocker: false
sunlit_dtc_provider_probe: aggregate_only_no_row_credit
sephora_required_family_count: 4
sephora_standard_summary_success_families: 3
sephora_manually_adjudicated_grouped_family_fallbacks: 1
sephora_review_corpus_board: complete
whole_acquisition_gate_re_adjudicated: true
phase_a_complete: true
phase_b_started: false
turn_b_started: false
company_report_exists: false
```
