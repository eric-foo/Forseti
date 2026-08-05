# Capture Source Family: Retail PDP

```yaml
retrieval_header_version: 1
artifact_role: Forseti Capture source-family README
scope: >
  Directory entrypoint for Retail/PDP source-family artifacts under the Capture
  core acquisition layer.
use_when:
  - Starting Retail/PDP capture source-family work.
  - Checking the Capture-vs-Scanning phase placement for Retail/PDP artifacts.
  - Finding the first Retail/PDP capture contracts, probes, or playbooks to open.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/README.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/amazon_demand_signal_route_candidates_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_silver_producer_contract_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_typed_envelope_probe_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retail_storefront_pin_registry_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/amazon_us_vpn_regression_recovery_playbook_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_site_registry_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_row_contract_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_row_capture_pilot_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_widget_expansion_probe_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_focused_coverage_mgt_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_rendered_companion_probe_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/sokoglam_okendo_retail_review_capture_recon_v0.md
  - forseti/product/spines/data_lake/README.md
  - docs/workflows/data_capture_spine_consolidation_map_v0.md
```

This directory is the current Capture home for Retail/PDP source-family
artifacts. It does not imply a Scanning sibling exists.

Phase sibling status: no accepted
`forseti/product/spines/scanning/source_families/retail_pdp/` directory exists in
this worktree. If a Scanning Retail/PDP source family is later created, add the
cross-pointer here and in the Scanning family entrypoint.

## Capture-To-Lake Route Map

| Layer | Current home | What to confirm |
| --- | --- | --- |
| Access / method | `retailer_information_extraction_standard_v0.md`; `retail_pdp_content_cleaning_contract_v0.md` | Cross-retailer evidence categories and discovery behavior; retailer-owned extraction, retention, target binding, residuals, Cleaning, and Silver handoff. |
| Storefront pins | `retail_storefront_pin_registry_v0.md`; `amazon_us_vpn_regression_recovery_playbook_v0.md`; supporting recon and live receipts linked there | Session, storefront-country, currency, and delivery-location state independently; a working route, VPN geography, or observed context is not a confirmed pin. |
| Retail/PDP packet/content | `run_source_capture_cloakbrowser_packet.py`; `source_capture/retail_pdp_content.py`; `cleaning/retail_pdp.py` | Five admitted profiles default to canonical content after retailer-owned pin/access/sufficiency/extraction gates. Amazon remains an explicit raw-unflipped route consumed through the legacy raw decoder into the same Cleaning/Silver floor. Shallow ladder profiles derive the commissioned PDP/search identity from the URL and require their exact US pin input; historical canary names are not target evidence. |
| Retail grid packet/projection | `run_source_capture_cloakbrowser_packet.py`; `source_capture/sephora_brand_grid.py`; `source_capture/retail_grid_projection.py`; `docs/research/forseti_sephora_brand_grid_capture_live_proof_v0.md` | Raw remains authoritative. Sephora, Ulta, and Target have admitted brand/assortment-grid projections with retailer-specific bounds; Amazon has an admitted query-bound ranked-search projection complete only for its declared query and reachable result window, never as a guaranteed complete or authorized-only brand denominator. Projection capability does not admit a live route. |
| Portfolio breadth composition | `run_retail_portfolio_onboarding.py`; `source_capture/retail_portfolio_onboarding.py` | Compose the owned source-parent census, company-owned official retailer board, selected retailer set and working primary, every verified grid row's explicit parent/listing reconciliation, and one hash-verified raw Retail/PDP packet per exact non-bundle retailer listing. Optional evidence-backed family mappings distinguish normalized product families, variant-as-parent objects, bundles/sets, and non-products without name/category inference. The derived record preserves duplicate placements, ambiguity, unmatched rows, missing material variants, unresolved family identity, and route failures without granting false parent or family coverage. |
| Review-corpus breadth | `retailer_information_extraction_standard_v0.md`; `run_revolve_review_corpus_completion.py`; `source_capture/revolve_review_corpus_completion.py` | After baseline PDP coverage, bind every listing to provider tenant/store plus collection context, collapse only proven shared corpora, and acquire one bounded onboarding window or typed terminal outcome for every distinct corpus. The REVOLVE implementation uses Yotpo `Most Recent`, the shared 30-day/30-row onboarding bound, native-ID accounting, and no environment proxy. Complete bounded acquisition does not imply a full historical corpus or require interpretation of every row. |
| Retail/PDP Silver | `retail_pdp_silver_producer_contract_v0.md`; `run_retail_pdp_silver_producer.py`; `source_capture/retail_pdp_silver.py` | Cleaning-owned source anchors, retailer-local identity, and source-visible offer/review observations only. |
| Fragrance purchase-review row capture | `fragrance_purchase_review_*` docs in this folder; `run_fragrance_review_coverage.py`; `run_fragrance_review_discovery.py`; `run_fragrance_review_lake_packet.py`; `forseti-harness/source_capture/fragrance_review_lake.py` | Retailer review-positive PDP discovery, rendered/widget companion preservation, focused coverage, and preserved-body lake tee boundaries. |
| Soko Glam public storefront pin | `retail_storefront_pin_registry_v0.md`; `sokoglam_okendo_retail_review_capture_recon_v0.md`; `retailer_information_extraction_standard_v0.md` | Capture-proven Direct HTTP routes for tested PDP/Okendo review surfaces and the 137-product best-selling collection. Routine review monitoring is one bounded recent API response; understanding cycles may paginate to declared reconciliation. Bestseller capture uses the compressed Shopify product-grid section because the cheaper-looking products feed does not preserve best-selling order. This is not production-runner admission or retailer-wide durability. |
| Data Lake authority | `forseti/product/spines/data_lake/README.md` -> `authority/` | Raw admission, path grammar, derived layout, and Silver semantics. The family index does not own them. |

## Portfolio Breadth Composition

The portfolio compositor is a local, no-network coverage gate. Its JSON
commission names the owned census packet and parents; a company-owned
authorization row for each retailer considered, including an explicit Sephora
resolution; any nonempty selected subset of officially named retailers; the
working primary; one explicit reconciliation for every row in each captured grid
packet; and the raw Retail/PDP packet directory for every exact non-bundle
retailer listing. A route-complete, officially named Sephora must be selected and
primary. An officially named but blocked, unpinned, or incomplete Sephora remains
a typed selected outcome while another route-complete retailer may be the
working primary. Captured outcomes point to packet
directories, not trusted projection summaries: the compositor re-hashes raw
bytes and rebuilds the retailer projection. Baseline packet locators must bind
the stable retailer-native product identity and any explicitly commissioned
retailer variant; fulfillment, market, or tracking parameters are not product
identity. The HTTPS scheme and matching retailer host remain part of the route
binding. Retailer-variant binding is currently admitted only where the route
exposes a stable selected identifier (Sephora, Target, and Ulta); commissions
that bind it for another retailer fail closed.

Source-parent count is never a normalized product-family count. A commission
may supply evidence-referenced family members and non-family dispositions for
the compositor to validate, but the compositor does not infer them from names,
URLs, or categories. Unmapped parents remain typed unresolved objects. They do
not block portfolio composition, but they keep the family denominator
`PARTIAL` and the complete normalized-family count unavailable.

Run `python runners/run_retail_portfolio_onboarding.py --commission <json>
--output <json>` from `forseti-harness/`. The derived output is
write-once and does not alter Raw. It is a coverage-composition record, not a
new CSB ledger schema, global SKU graph, sales estimate, or product-role
selection.

## Review-Corpus Breadth

The default evidence-layer unit is a distinct review corpus, not a retailer
listing and not a hand-selected hero product. After the portfolio compositor
binds the baseline listings, route-specific adapters inventory provider
tenant/store and collection context, acquire one bounded onboarding window per
distinct accessible corpus, and preserve a typed outcome for everything else.
Interpretation remains category-balanced and evidence-selected.

REVOLVE's admitted implementation consumes a verified PDP packet root and
writes one `Most Recent` receipt per distinct Yotpo corpus plus a terminal
listing-to-corpus completion receipt:

```powershell
python runners/run_revolve_review_corpus_completion.py `
  --pdp-root <verified-revolve-pdp-root> `
  --output-root <new-output-root>
```

The runner never overwrites an output root, uses no environment proxy, limits
concurrency to an explicit maximum of eight workers, and continues independent
corpora so one typed failure does not erase completed evidence. Its completion
claim is bounded onboarding coverage only, not all historical rows, customer
representativeness, approval, or demand.

## Non-Claims

This entrypoint is not live capture authorization, validation, readiness,
source completeness, ECR, Cleaning, Judgment, buyer proof, demand proof, or
commercial-readiness evidence.
