# CO2 — Dieux Official Retailer Breadth

```yaml
retrieval_header_version: 1
artifact_role: CO2 retailer-breadth terminal return
scope: Fresh p03 US official-retailer grid and bounded review-corpus onboarding outcomes.
use_when:
  - Integrating CO2 evidence into BEAUTY-DIEUX-PHASEA-COMPLETION-003.
authority_boundary: evidence_only_no_deliver
stale_if:
  - The Dieux FAQ official-retailer answer or any observed retailer surface changes.
```

## Success contract and gates

```yaml
commission_id: BEAUTY-DIEUX-PHASEA-COMPLETION-003
cycle_id: DIEUX-UNDERSTANDING-20260805-003
bound_revision: 3e0ade5f0dadb690b2209ee7b527cfdad42b3a2b
goal: >-
  Attempt every freshly authorized third-party US retailer, reconcile the
  visible grid/listing boundary, and return one real bounded review corpus or a
  typed terminal outcome per retailer without granting unsupported
  cross-retailer independence.
invariants:
  - prior p02 work receives no evidence or route credit
  - Dieux DTC is owned and is not an independent retailer corpus
  - Trustpilot remains CO3 service evidence and is not a retailer corpus
  - search and AI summaries are discovery only, not review-body evidence
  - no prevalence, demand, sales, or market-consensus inference
  - Dieux Deliver does not start
positive_signal: all three fresh official third-party groups have terminal onboarding outcomes
forbidden_near_miss: counting a visible review total, blocked shell, or provider difference as an independent review corpus
wrong_cause_check: >-
  Review bodies, native IDs, retailer/provider namespace, grouping,
  syndication fields, and exact overlap were checked separately; HTTP success
  or a visible headline count alone received no corpus credit.
terminal_status: complete
deliver_started: false
```

The required p03 gate was freshly read before retailer capture:

- `route_capability_preflight.json` had
  `checked_before_network_capture=true`, commission/cycle `-003`, and status
  `ready_for_first_real_serp_phase1_seed`.
- `serp_phase1_ledger.json` had status `terminal`, the same IDs, and SHA-256
  `9f2509bfdfd404eae15b36c0980d7204fdb354f2bfb1255abd3bfa7a272fc6ef`.
- CO1 published the fresh official-retailer authorization section and then
  completed `co1_official_and_source_neutral.md`; its current durable terminal
  was freshly re-read at SHA-256
  `a6467a463a061936b5bd04a90b58e1ed967af58832fdacd81f4d0c4b137bd73b`.
  Its source-native FAQ answer named Sephora U.S./Sephora.com, SokoGlam.com,
  and the Dieux TikTok Shop storefront. Three qualifying third-party groups is
  fewer than four, so all three were selected. Dieux DTC was excluded as owned.

## Admission correction

The initial ad hoc HTTP/browser outputs under
`C:\tmp\forseti-dieux-phase-a-completion-20260805-p03\co2\` were preserved,
but they are scouting/diagnostic material with **zero evidence credit**. This
includes the root-level `sephora_*`, `sokoglam_*`, and `tiktok_*` bodies,
headers, and the derived TikTok review-window JSON. No claim below depends on
them. Credited fresh units were recaptured through the Source Capture Armory
runner ladder and are identified by packet ID, manifest, receipt, and hash. The
separately pinned Soko six-product corpus is not p02 work; it receives credit
only through the hash, identity, snapshot, and row-level reuse adjudication
below.

## Terminal retailer board

| Retailer group | Admitted fresh grid/listing boundary | Admitted review onboarding | Terminal outcome | Evidence credit |
| --- | --- | --- | --- | --- |
| Sephora | Source-specific CloakBrowser grid packet reconciled 12 extracted placements, 12 unique parents, and the page-declared 12 results on the US country route. | Hash-verified Instant Angel PDP parent plus Bazaarvoice companion preserved 100 Most Helpful and 100 Most Recent non-incentivized review rows, all with bodies; the union contains 183 unique native IDs. | `CORPUS_CAPTURED_BOUNDED_WINDOWS` | One Sephora/Bazaarvoice retailer-specific corpus unit. |
| Soko Glam | Armory direct-HTTP collection packet exposed six Dieux products in the source-rendered Shopify collection state; the pinned corpus has the same six provider product IDs. | Fresh Okendo capture preserved 32 Instant Angel bodies and native IDs. Pinned reuse adds 45 unique body rows across the other five products; its 32 Instant Angel rows are typed duplicates of the fresh packet. | `CORPUS_CAPTURED_AND_PINNED_REUSE_ADJUDICATED` | One Soko/Okendo retailer-specific corpus unit containing 77 unique bodies; native IDs are absent for the 45 reused additions. |
| TikTok Shop | No admissible grid packet. The current route authority requires an operator-supervised, routed, headed real-Chrome session with US egress and storefront-native navigation; that route was unavailable in this lane. | No admissible body-bearing packet. Prior direct-HTTP material is explicitly withdrawn and cannot substitute for the required route. | `ROUTE_BLOCKED_REQUIRED_ROUTED_HEADED_SESSION_NOT_AVAILABLE` | None. This is not `NO_REVIEWS`. |

No fourth qualifying US retailer was named by the fresh official source.

## Admitted corpus facts

### Sephora / Bazaarvoice

- Grid packet `01KZ99D0TP8K4WZMAGJ7Q3C37S` used the
  `sephora_grid_aggregate` profile on
  `https://www.sephora.com/brand/dieux/skincare?country_switch=us`. Its
  mechanical projection is `complete`: 12 extracted placements, 12 unique
  parent products, page-declared result count 12, no duplicate placements, and
  termination `retailer_serialized_count_reconciled`. The grid certifies the US
  country route, not a currency or delivery-location pin.
- The review companion is bound to hash-verified PDP parent packet
  `01KZ99GS7BYP0ZC7MQ4AY8260N`, Instant Angel product `P510288`, selected SKU
  `2767168`, market `US/USD`. The onboarding companion packet is
  `01KZ99M6NETJD7TD68HR6CBVZ4`.
- Provider: Bazaarvoice. Captured rows report `SourceClient=sephora` and
  `IsSyndicated=false` in both windows.
- The source reports 2,286 unfiltered reviews and 915 exact non-incentivized
  reviews for the requested product group. The bounded capture preserved 100
  Most Helpful and 100 Most Recent rows, 100 non-empty bodies and 100 unique
  IDs in each window; their union has 183 unique IDs because the two orderings
  overlap.
- The 30-day recency accounting proves 16 rows within that window. This is a
  bounded onboarding capture, not the full 915-row non-incentivized corpus.
- Provider-returned product IDs are `P510288` and `P517955`; 21 captured rows
  carry historical or no-longer-current product ID `P517955`. They remain in
  the provider-defined product-group capture and are not misclassified as a
  current SKU.

### Soko Glam / Okendo

- Collection packet `01KZ999K9Z8CGDEE0AKMNQXV7Y` and Instant Angel PDP packet
  `01KZ999Q4K7XHY6EV98Z50QWH3` both returned HTTP 200 through the authorized
  direct-HTTP route. The collection state contains six Dieux products:
  Baptism, Air Angel, Instant Angel, Forever Eye Masks, Auracle, and
  Deliverance.
- Review packet `01KZ999SXRB1637ZJZJJPEVQVY` captured the page-owned Okendo
  response. Tenant/store is `d701ae47-bc16-4e09-9fa4-afb68ffdd61c`;
  product/group is `shopify-6897431216197`; the composite binding is
  `d701ae47-bc16-4e09-9fa4-afb68ffdd61c:shopify-6897431216197`; and
  `areReviewsGrouped=false`.
- Requested and returned order is newest-first (`date desc`) with requested
  limit 100. The response contains 32 rows, 32 non-empty bodies, 32 unique
  native review IDs, and zero exact duplicate-body groups.
- Source-visible attributes: 20 verified-buyer rows and 16 incentivized rows.
  Four rows expose `externalProvider=shopify-shop`; the other 28 expose no
  external-provider field. Those four remain part of this Soko corpus and gain
  no extra-origin credit.

### Pinned Soko six-product reuse adjudication

The pinned source is
`C:\tmp\forseti-dieux-sokoglam-retailer-corpus-20260805\corpus.json`.
Its SHA-256 is exactly
`40618a42445188bf9c87aef02dfd9351be49a22e22f6231a8b64e76f294d2922`;
`manifest.json` is exactly
`2530f4eb3d85c7afe79ab4afd2bd8abfad351a9f8cfd2693acd01101524f84c1`.
All 22 manifest entries exist and freshly match their declared byte counts and
hashes. Corpus, receipt, and manifest agree on capture ID
`DIEUX-SOKOGLAM-RETAILER-CORPUS-20260805`, subject Dieux, retailer Soko Glam,
provider Okendo, and collection URL `https://sokoglam.com/collections/dieux`.
The pinned provider-product-ID set exactly equals the six IDs in the fresh p03
collection packet.

Primary-row recomputation found 77 rows, 77 non-empty bodies, 77 unique
whitespace-normalized bodies, zero internal duplicate-body groups, 58 verified
buyers, six product groups, and **zero preserved native review-ID fields**.
Every reused row is dispositioned here; counts sum to 77:

| Product group | Provider product ID | Snapshot time (UTC) | Body rows | Native IDs preserved | Current-cycle disposition |
| --- | --- | --- | ---: | ---: | --- |
| Instant Angel | `shopify-6897431216197` | `2026-08-05T09:30:52.532Z` | 32 | 0 | `TYPED_EXCLUDED_DUPLICATE_OF_FRESH_P03_PACKET` |
| Baptism | `shopify-7605350400069` | `2026-08-05T09:30:54.639Z` | 4 | 0 | `ADMITTED_PINNED_SNAPSHOT_BODY_ROWS` |
| Forever Eye Masks | `shopify-6897431117893` | `2026-08-05T09:30:59.052Z` | 15 | 0 | `ADMITTED_PINNED_SNAPSHOT_BODY_ROWS` |
| Auracle | `shopify-6897431085125` | `2026-08-05T09:32:15.860Z` | 13 | 0 | `ADMITTED_PINNED_SNAPSHOT_BODY_ROWS` |
| Deliverance | `shopify-6905276989509` | `2026-08-05T09:32:35.430Z` | 10 | 0 | `ADMITTED_PINNED_SNAPSHOT_BODY_ROWS` |
| Air Angel | `shopify-7605360787525` | `2026-08-05T09:33:21.532Z` | 3 | 0 | `ADMITTED_PINNED_SNAPSHOT_BODY_ROWS` |

Deduplication against the fresh 32-row Instant Angel API packet found 29 exact
whitespace-normalized body matches. The remaining three body pairs differ only
where the DOM projection removed paragraph-break whitespace; source order,
reviewer, trimmed title, rating, and equality after whitespace elision bind
them to the corresponding fresh rows. Thus all 32 pinned Instant Angel rows
map to 32 fresh native IDs and receive no additive row credit. The other 45
pinned rows have no body match in the fresh Instant Angel packet and are
admitted as additional product-bound snapshot bodies, not as native-ID-bearing
records.

The pinned corpus is a snapshot from `2026-08-05T09:30:52.532Z` through
`2026-08-05T09:33:53.280Z`. Its relative review-date labels, availability,
prices, ratings, and denominators are valid only as observed then; reuse does
not promote them to current state or exact review publication dates. Raw files
remain unchanged.

## Provider, syndication, and overlap adjudication

The admitted Sephora and Soko windows use different provider surfaces and
retailer/product namespaces. Exact whitespace-normalized body comparison
between Soko's 77 unique bodies and the 183-unique-ID union of Sephora's two
100-row windows found **zero** overlaps. Sephora's captured rows explicitly
report `IsSyndicated=false`; Soko exposes an external-provider value on only
four of the 32 fresh Instant Angel rows, and the 45 additional pinned rows
preserve neither a native ID nor a corresponding origin field.

Therefore the evidence supports **two retailer/provider-specific corpus
units**, but not independent author populations, market-wide consensus, or a
cross-retailer recurrence claim. Zero exact overlap is absence of recurrence
inside these captured windows; it is not proof about paraphrased, historical,
deleted, or outside-window content.

## Admitted packet ledger

Fresh packet paths are under
`C:\tmp\forseti-dieux-phase-a-completion-20260805-p03\co2\`; the pinned reuse
row carries its separate absolute root.

| Evidence unit | Packet ID / locator | Manifest SHA-256 | Receipt or projection SHA-256 |
| --- | --- | --- | --- |
| Sephora US grid | `packets/sephora_grid`, `01KZ99D0TP8K4WZMAGJ7Q3C37S` | `35c6ed25f292c0162fdb603aeaa8fe202eb3faec67be066e3c1a3f868d7447dd` | receipt `d65ba26c99c2aef830ec35fe6929006d4fd0c171dd3b1536ac784d696eef3803`; projection `91175f5a6aaf31d1a0cc7a82f92a38fe1021afe8af26db56f16046bf1095dfbd` |
| Sephora PDP parent | `lake/raw/891/01KZ99GS7BYP0ZC7MQ4AY8260N` | `fa1d22eae9bc66b0c586b2cb3ee30e9264054ea03e6d60d6f67414348767ff3b` | `0aefdb5861e017dc6e03c0b2f8f690f5730a44fc57bb1f725dcf47c731c33b93` |
| Sephora Bazaarvoice companion | `lake/raw/bc8/01KZ99M6NETJD7TD68HR6CBVZ4` | `30bae6cc30d9a0ba7365a8882c3e0a116931818d1b615557962a1fb8d04f795c` | receipt `4b7af6919efd5837df256e2ff84d9c8630fa305b761142cc1a627481442839ae`; summary `894b054142f377849a338d5ed55418503b84850fc466c14eead4acbcb3e18d94` |
| Soko collection | `packets/sokoglam_collection`, `01KZ999K9Z8CGDEE0AKMNQXV7Y` | `7cbd577a4ed5b871261d84effc6465baa02877167fc4e050433634d7f4e58ddd` | `64db9aed2df40037186db1cff20e038561fa244a9a6fadddac983a16765a4d5b` |
| Soko Instant Angel PDP | `packets/sokoglam_instant_angel_pdp`, `01KZ999Q4K7XHY6EV98Z50QWH3` | `6db74063841dd3d444e231964a6ed326c51f03eb02362b0f424d7438a7e5d2a4` | `56a01b4ae4b417bebb2f32683e46d52c0ad01571ac668b7efc0f1f45acc10c3f` |
| Soko Okendo reviews | `packets/sokoglam_instant_angel_reviews`, `01KZ999SXRB1637ZJZJJPEVQVY` | `27ac8d516783aaa496840ac1f35d83ee8728240870ef4768e42f4e8827332f38` | `56faa5634fc2c94323e6c0770e5f5ff3ab17ca8c7c4defbd7b1f6650ec3c5fca` |
| Pinned Soko six-product corpus | `C:\tmp\forseti-dieux-sokoglam-retailer-corpus-20260805`, `DIEUX-SOKOGLAM-RETAILER-CORPUS-20260805`; corpus `40618a42445188bf9c87aef02dfd9351be49a22e22f6231a8b64e76f294d2922` | `2530f4eb3d85c7afe79ab4afd2bd8abfad351a9f8cfd2693acd01101524f84c1` | capture receipt `69239813c4875a4a9bc53430338eaa66a839b4da13bf529ff0b5eafc30464d52` |

## Return

```yaml
status: completed
official_third_party_groups_attempted: 3
official_third_party_groups_terminal: 3
real_review_corpora_or_windows: 2
soko_unique_body_rows_available: 77
soko_pinned_reuse_admitted_additional_rows: 45
typed_reuse_exclusions:
  TYPED_EXCLUDED_DUPLICATE_OF_FRESH_P03_PACKET: 32
typed_failures:
  ROUTE_BLOCKED_REQUIRED_ROUTED_HEADED_SESSION_NOT_AVAILABLE: [TikTok Shop]
independence_ceiling: two_retailer_specific_corpora_no_author_population_or_cross_retailer_recurrence_claim
residuals:
  - Sephora capture is bounded to two 100-row orderings, not all 915 non-incentivized reviews
  - Soko's 45 additional pinned rows preserve no native IDs or origin fields
  - Soko exposes explicit external-provider provenance on only 4 of the 32 fresh Instant Angel rows
  - Pinned Soko state is bounded to its 2026-08-05T09:30:52.532Z through 09:33:53.280Z snapshot
  - TikTok Shop has no admissible p03 packet
next_operator_action: CO0 may admit Sephora and the 77-unique-body Soko snapshot as separate retailer-specific corpus units, count only 45 pinned rows as additive to the fresh Soko packet, and preserve the stated identity and time ceilings.
deliver_started: false
```
