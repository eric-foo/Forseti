# Summer Fridays p10 CO2 Retail Portfolio And Corpus Identity Return

```yaml
retrieval_header_version: 1
artifact_role: Summer Fridays p10 cold Understanding Turn A CO2 terminal return
scope: Official-first selected-retailer grids, owned-candidate reconciliation, exact non-bundle PDP baselines, and listing-to-review-corpus accounting.
use_when:
  - Acquiring p10 review windows for every selected-retailer corpus.
  - Integrating or sealing the Summer Fridays p10 cold Understanding acquisition.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co1_company_core_identity.md
  - docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/commission_board.md
downstream_consumers:
  - p10 CO3 customer/community and review-corpus acquisition
  - p10 CO0 acquisition record and seal adjudication
stale_if:
  - A consumer needs current retailer assortment, PDP, provider, tenant/store, collection, or sort state after the retrieval window below.
```

## Retrieval And Run Header

- Run boundary: p10 cold Understanding Turn A Acquire & Seal only.
- Coldness: no prior Summer Fridays prompt, packet, board, specialist return, acquisition record, seal, review, selection, conclusion, or comparison output was read. All subject facts below come from CO1's fresh p10 terminal/raw evidence or CO2's fresh p10 capture.
- Runtime base observed: `af7629692b6a2457fc5574f1cd4a96c585933a43`.
- Branch observed: `codex/sf-understanding-p10-cold-phase-a`.
- Exclusive raw evidence root: `C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co2`.
- Capture window: `2026-07-24T20:56:57Z` through `2026-07-24T21:25:12Z`.
- Terminal state: `CO2_COMPLETE_WITH_MATERIAL_SEPHORA_PDP_RESIDUALS`.

## Upstream CO1 Identity And Authorization

The controlling upstream is
`docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co1_company_core_identity.md`.
CO2 fresh-read its final `CO1_COMPLETE_WITH_TYPED_RESIDUALS` state before reconciliation.

- Official-retailer authority: CO1 packet `01KYAY2KHJSNHBWYM1FH3HG3TC`, raw SHA-256 `ca8d4b43ed66e455126d1a0681828cd9800118d0d3cdba1fa802db11199a9eac`.
- Owned denominator: 149 exposed company-owned parents normalized by CO1 to 34 families.
- Exact owned disposition ledger:
  `C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co1\13_portfolio_parent_disposition_v1\portfolio_parent_disposition_v1.json`,
  SHA-256 `8b4be38929b167a1eb1aebffe5ea2813a0172dfedd3525188f534e634e2bd212`.

## Locked Selected-Retailer Job Set

The job set was locked once after the supported CO1 authorization board:

| Candidate | Locked disposition | Rationale |
| --- | --- | --- |
| Sephora | Selected; mandatory primary candidate | Company-owned authority explicitly names the US; the current route has an admitted complete grid and PDP profile. |
| REVOLVE | Selected; non-duplicative fallback-primary candidate | Company-owned authority names REVOLVE; the admitted route independently binds US/USD and exposes a distinct retailer/provider corpus. |
| Space NK | Not selected; not probed | Official locator is US-facing, but the current registry has no admitted complete brand-grid/PDP route. It also adds less distinct retail context than the working REVOLVE route. |
| Amazon | Not selected; not probed | Authorization is bounded to the dedicated storefront. The admitted Amazon grid is query-bound and cannot prove that storefront's complete authorized denominator. |
| Mecca | Not selected; not probed | CO1's locator is Australia-facing. |
| Cult Beauty; Apotheca | Not selected; not probed | Company-owned authorization supports identity but does not state a US market. |

No Target, Ulta, Nordstrom, or other uncommissioned retailer was probed.

## Primary Decision

**REVOLVE is the working primary.** Its current US/USD grid reconciled 37/37 rows and every one of its 33 exact non-bundle listings has a verified PDP baseline.

Sephora remains selected but is not route-complete: its US grid reconciled 44/44 rows, while only 40/42 exact non-bundle PDP baselines admitted. `P525609` and `P525633` redirected to Sephora search and lost target identity under the bounded attempt/retry policy. Making Sephora primary would therefore be false.

The repository portfolio compositor was not run. Its current primary constraint keys only on `GRID_CAPTURED_COMPLETE` and would force a grid-complete Sephora primary even when required PDP baselines are missing. The inputs could not honestly satisfy that narrower schema while preserving this run's route-completeness rule.

## Grid And PDP Reconciliation Board

The complete 81-row board is
`C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co2\portfolio_corpus_board_v1.json`,
SHA-256 `3676feef0246ca2fe1ee4ed13108f38c92e3c64dfca4cdfed1c2d04968e495bc`.
Every row carries its grid row ID, retailer listing ID/URL, title, kind, normalized family, every CO1 owned-candidate ID and ledger JSON pointer, PDP status and hashes, provider/store/collection fields, sort capability, corpus status, overlap ceiling, and typed failure.

| Accounting unit | Sephora | REVOLVE | Total |
| --- | ---: | ---: | ---: |
| Verified grid rows | 44 | 37 | 81 |
| Exact non-bundle listings | 42 | 33 | 75 |
| Verified PDP baselines | 40 | 33 | 73 |
| Route-failed PDP baselines | 2 | 0 | 2 |
| Bundles/sets retained without a required PDP baseline | 2 | 4 | 6 |

Owned reconciliation across all 81 rows:

- 32 rows resolve to one exact CO1 owned candidate.
- 41 rows resolve exactly at normalized-family level but span multiple CO1 source-parent candidates; those candidates remain separate rather than being collapsed into a false single parent.
- Four bundles/sets resolve to a CO1 bundle/set object.
- Four rows remain unmatched to the current 149-parent CO1 ledger:
  Sephora `P469189` (`Summer Silk Nourishing Body Lotion`);
  REVOLVE `SUMR-WU93` (`Sweet Pink Lip Butter Balm Birthday Duo`);
  `SUMR-WU11` (`Summer Skin Nourishing Body Lotion`);
  and `SUMR-WU87` (`The Holiday Trio`).
  Their current retailer presence is proven; current company-owned-parent identity is not.

Duplicate and variant placements remain visible. Examples include separate full/mini Sephora and REVOLVE listings for Jet Lag Mask, Sunlit Vanilla, Pink Dew, Cloud Dew, Body Butter Balm, and Body Fragrance Mist. They were not collapsed merely because titles, families, or review counts overlap.

## Listing-To-Corpus / Provider Board

### Sephora

The 40 verified PDPs observe Bazaarvoice configuration and source sort controls. The compact baseline does not expose a trustworthy tenant/store or provider collection key, so every listing remains a provisional context and **none is collapsed**. Actual source labels observed are `Most Helpful`, `Highest Rating`, `Lowest Rating`, `Oldest`, and `Newest`; this does not replace Sephora's source-specific CO3 onboarding policy.

Verified provisional contexts:
`P455936`, `P520759`, `P515210`, `P518147`, `P522826`, `P520074`,
`P509439`, `P522685`, `P429952`, `P501777`, `P480630`, `P520746`,
`P521692`, `P522831`, `P511756`, `P518150`, `P511987`, `P517935`,
`P510508`, `P520770`, `P506690`, `P520744`, `P520734`, `P520819`,
`P520793`, `P520764`, `P471283`, `P449180`, `P525593`, `P480192`,
`P476028`, `P525660`, `P525642`, `P469189`, `P525613`, `P525641`,
`P525652`, `P525665`, `P525659`, and `P503827`.

Typed non-baseline outcomes:

- Bundles/sets pending a provider/collection identity or typed CO3 terminal:
  `P525302`, `P516163`.
- Route blocked after the bounded PDP path:
  `P525609`, `P525633`.

Claim ceiling: the board proves 40 provider-observed listing contexts, not 40 independent corpora. CO3 must bind the actual tenant/store and collection key before any collapse or independence claim.

### REVOLVE

All 33 verified PDPs observe provider `yotpo`, store
`b4k4hvSXVzfPzX41MmcY1NO4yJyOAtVxDGEh4bxA`, and a retailer-native product ID equal to the listing style ID. The 26 positive-review contexts therefore form 26 distinct observed collection keys. Seven additional PDPs source-declare zero reviews: `SUMR-WU120`, `SUMR-WU123`, `SUMR-WU122`, `SUMR-WU95`, `SUMR-WU84`, `SUMR-WU89`, and `SUMR-WU90`.

The 26 positive-review listing IDs are:
`SUMR-WU102`, `SUMR-WU121`, `SUMR-WU74`, `SUMR-WU23`, `SUMR-WU110`,
`SUMR-WU61`, `SUMR-WU76`, `SUMR-WU53`, `SUMR-WU1`, `SUMR-WU14`,
`SUMR-WU117`, `SUMR-WU83`, `SUMR-WU111`, `SUMR-WU59`, `SUMR-WU60`,
`SUMR-WU49`, `SUMR-WU11`, `SUMR-WU77`, `SUMR-WU16`, `SUMR-WU71`,
`SUMR-WU4`, `SUMR-WU92`, `SUMR-WU25`, `SUMR-WU91`, `SUMR-WU21`,
and `SUMR-WU39`.

Observed nonzero-corpus sort labels are `Highest rating`, `Lowest rating`,
`Most relevant`, and `Most recent`; CO3 should use source-labelled
`Most recent`. Q&A is not exposed on the 33 verified baselines.

Bundles/sets pending a provider/collection identity or typed CO3 terminal:
`SUMR-WU118`, `SUMR-WU93`, `SUMR-WU75`, and `SUMR-WU87`.

Overlap ceiling: shared provider/store does not establish shared customers or shared corpora. REVOLVE listings were collapsed only when provider, store, and product collection key matched; no two positive-review listings matched all three.

## Raw Evidence And Provenance Index

The fresh hash-verification index is
`C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co2\raw_provenance_index_v1.json`,
SHA-256 `f67fb55d0682559f1c425c94eb27551ba66338d74f201aa9b58a07a84ff721cd`.
It covers 78 packet manifests and seven projection/board/log artifacts. Every one of the manifest-declared raw file hashes fresh-matched; mismatch count is zero.

Key roots:

| Evidence | Packet / hash |
| --- | --- |
| Sephora grid | Packet `01KYAYNFMA67422JRWZTXSEFMS`; manifest SHA-256 `73051ed740c3d1b4987165ee0044535c2943dbba78d234e420d9e78b6857913a`; projection SHA-256 `b856440473052b010ca644916edfc89595c369f235c5f0df22d69af9260e5cb3`. |
| Sephora PDP corpus | `data\co2\sephora\pdp`; 42 canonical packet directories, including 40 admitted baselines and two typed failures. |
| Sephora `P525633` retry | Packet `01KYAZYDFC4YF5HCBT6T6D9MJ3`; manifest SHA-256 `57d086cb81f06eb88847fe680db4df61187a5d37acf035ef147d9c13fed37a70`. |
| REVOLVE grid | Packet `01KYAZZSTSE1N2JAJHSMQH6PCD`; manifest SHA-256 `4a887f9e0a2549d4f9f078b3750e2f7cb3911b3828763dcf031ae233139e5dc6`; projection SHA-256 `b0ad85ee77e6e9829a1122c08f027d970520640f76362fd19d5e90dae9e7d0b7`. |
| REVOLVE PDP corpus | `data\co2\revolve\pdp`; 33/33 admitted exact non-bundle baselines. |
| Capture logs | `data\co2\logs`; the foreground timeout and background terminal results remain distinct in this return. |

## Attempts And Retries

- Sephora grid: two local no-write CLI corrections (`content` retention required; `country_switch=us` required), then the first material capture succeeded.
- Sephora PDPs: an initial reusable-browser foreground call exceeded the tool transport window after three completed packets. CO2 fresh-inspected and stopped only that process tree, retained the three complete packets, and continued through one observable background route without double-writing.
- Sephora canonical PDP outcomes: 40 admitted; `P525609` and `P525633` each preserved a target-identity/search-redirect failure packet.
- `P525609` retry: the one retry capture failed local recapture-metadata closed-vocabulary validation and wrote no packet. The retry budget is exhausted; no success is inferred.
- `P525633` retry: packet `01KYAZYDFC4YF5HCBT6T6D9MJ3` again redirected to search and failed target identity. Retry budget is exhausted.
- REVOLVE grid and all 33 required PDP baselines succeeded on their canonical material attempts. No REVOLVE retry was used.

## Completed And Unresolved Jobs

Completed:

- Official-first retailer selection and explicit Sephora resolution.
- Two complete current admitted brand grids, accounting for all 81 rows.
- 73 verified exact non-bundle PDP baselines.
- Row-by-row reconciliation to CO1 owned candidates or an explicit unmatched result.
- One 81-row provider/corpus identity board with typed bundle, zero-review, blocked, and unresolved outcomes.
- Fresh manifest/raw-file hash verification with zero mismatches.

Unresolved:

- Sephora `P525609` and `P525633` have no admitted PDP baseline.
- Six bundle/set listings lack baseline-bound tenant/store and collection identity.
- Sephora's 40 successful baseline listings expose Bazaarvoice but not a trustworthy tenant/store or collection key; CO3 must resolve them before collapse.
- Four current retailer rows do not match the current CO1 149-parent ledger.

## Material Failures And Exact Claim Ceilings

1. Sephora is grid-complete but not route-complete. No claim of complete selected-retailer PDP coverage, complete Sephora corpus identity, or Sephora primary status is supported.
2. `P525609` and `P525633` source rows remain valid grid evidence, but their failed/redirected packets are not evidence for the commissioned PDP target.
3. A complete grid is current retailer assortment evidence only. It does not prove nationwide stock, sales, inventory quantity, or DTC denominator equivalence.
4. Shared review count, product family, provider, or store never grants corpus collapse. Sephora has no independent-corpus count from CO2.
5. The 26 REVOLVE keys are distinct provider collection contexts, not proof of independent customers, representative sentiment, or a complete historical review corpus.
6. Source-declared zero reviews is bounded to the observed retailer product context and capture time; it is not proof of no customer evidence elsewhere.

## Follow-Ups

- CO3 should consume the exact 81-row board, acquire the required Sephora source-specific Helpful/Recent/Q&A views only after resolving tenant/store and collection identity, use REVOLVE `Most recent`, and retain typed outcomes for the six bundle/set contexts and two exhausted Sephora routes.
- CO3 must not collapse the 40 Sephora provisional contexts from provider name, title, family, or review-count similarity.
- CO0 should carry the two missing Sephora PDP baselines and four unmatched owned-parent rows as material seal inputs rather than masking them with REVOLVE's complete route.
