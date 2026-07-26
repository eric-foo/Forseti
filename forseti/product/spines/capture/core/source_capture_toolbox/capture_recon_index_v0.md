```yaml
retrieval_header_version: 1
artifact_role: Capture recon consolidation index (non-authorizing)
scope: >
  Consolidates the scattered per-source capture RECON / INVESTIGATION findings across
  the toolbox, data-capture-spine pressure tests, research receipts, and worktree-resident
  lane findings into one index. Records, per source probed, what was found capturable, at
  which runner rung, where the signal actually lives, and any corrected false-diagnosis.
  This index is the evidence base the capture-investigation doctrine + runbook distil from.
use_when:
  - Drafting the source-agnostic capture-investigation doctrine and per-archetype recipe cards.
  - Checking whether a source archetype already has a worked recon before re-probing it.
  - Locating the highest-signal real probe receipts (captured bytes / live-verified verdicts).
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/operating_model/data_capture_harness_operating_model_architecture_v2.md
stale_if:
  - A new source recon lands (this index is append-only until the doctrine supersedes it as the home).
  - The worktree-resident findings (Sephora/Bazaarvoice reviews; Ulta Apollo embedded-JSON) merge to main.
  - The capture-investigation doctrine is authored and adopts the cross-cutting patterns below as its spine.
```

# Capture Recon Consolidation Index (v0)

## What this is — and is not

This is a **non-authorizing index** of the capture RECON / INVESTIGATION findings already
in the repo — the docs that probed a real source to learn **whether and how it can be
captured**. It exists so the capture-investigation doctrine and its per-archetype recipe
cards are **distilled from real probe evidence, not invented**.

It is **not** a build spec, not validation, not an acceptance claim, and not legal advice.
Verdicts below are **as reported by each source doc**, not re-observed here. It governs
nothing; it feeds the doctrine.

## Cross-cutting patterns — the doctrine seed (highest-value section)

These six patterns recur across independent probes. They are the spine the investigation
doctrine should encode.

1. **"Blocked" is a hypothesis, not a verdict — and it is the dominant false-diagnosis.**
   A 403 / empty body / "anti-bot gated" read was *wrong or imprecise* in multiple
   independent cases: Daimler PDFs (direct-HTTP 403 **and** headless 403, yet **visible
   Chrome + the PDF-viewer download button succeeded**); Sephora reviews (worktree:
   "anti-bot gated" → actually a **scroll-overshoot** that never fired the lazy-load
   observer); Teal/WSO (403 first recorded as "content unavailable," later re-diagnosed as
   an anti-bot gate). **Escalate the interaction (real browser context → user-initiated
   action → progressive scroll → proxy/geo) and re-probe before recording NO-GO.** A false
   "blocked" abandons a capturable source.
2. **Locate the signal substrate first; pick the tool second.** Reddit = raw JSON;
   reviews = a first-party-rendered vendor API (Bazaarvoice); SPA state =
   `__APOLLO_STATE__` / `__NEXT_DATA__` (Ulta, worktree); PDF body = a download button.
   The cheapest working rung is a function of **where the signal lives**, so step 1 of
   diagnosis is finding the substrate, not choosing a runner.
3. **Verbatim-vs-paraphrase is a separate axis from reachable-vs-blocked.** WebFetch
   *reaches* M&I/BIWS but returns **paraphrase**, losing layout/packaging fidelity. A
   recipe must record whether a rung preserves source **bytes**, independent of whether it
   gets through.
4. **The entitlement/legal gate is orthogonal to the technical gate and comes first.**
   LinkedIn policy forbids automated capture **regardless** of technical reachability;
   Reddit's API has a commercial-use gate. A NO-GO can be *legal*, not technical. Never
   bypass an unentitled gate even when it is technically trivial.
5. **NO-GO and PARTIAL are first-class, honest outcomes.** Daimler pre-cutoff archive
   returned **no memento exists** → an honest NO-GO; archive *availability* ≠ body
   *retrieval* → PARTIAL. Concluding "not cleanly capturable within boundary" is a
   *successful* diagnosis, not a failure.
6. **The runner ladder is empirically real and cheapest-first.** archive.org →
   direct-HTTP → **(visible) browser** → cloakbrowser+proxy. "Visible browser + a
   user-initiated action" is a genuine escalation rung that defeats headless-detection
   where both direct-HTTP and headless fail (Daimler).

## Index — by archetype (verdicts as reported by each source)

### Reviews
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Sephora PDP reviews **(worktree, pending-merge)** | `orca-cloak-scroll-wt/orca-harness/docs/source_capture_review_rendering_findings_v0.md` | Bazaarvoice API, first-party-rendered into DOM, lazy-load on **progressive scroll**; bot wall **passed** legitimately | **GO via incremental scroll** (corrects a prior false "anti-bot-gated" claim) | HIGH ⭐ |
| ClickUp on Trustpilot / G2 | `forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_pressure_test_review_surface_v0.md` | Live public review text; rating+text+date coupling, reviewer-status labels | Captured; review-surface satellite guidance formalized | MODERATE |
| Niche fragrance purchase-review PDPs (Luckyscent, Twisted Lily, ZGO, Indigo, Ministry of Scent) | `forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_retailer_recon_v0.md` | Retailer-specific substrate: Luckyscent/Twisted Lily row-level reviews need CloakBrowser render+scroll; Ministry and the selected ZGO fixture expose rows via Direct HTTP; selected Indigo fixture exposes rendered JSON-LD / Judge.me `Review` rows | Five row-positive fixtures after known-reviewed ZGO/Indigo re-probe; not source-wide completeness proof | HIGH |

### Forums / threads
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Reddit r/financialcareers (10 threads, 563 rows) | `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_slot3_reddit_capture_session_v0.md` | Raw JSON → Mechanical Source Projection; row/parent_id/depth; `more_placeholder` visibility | `categorical_handoff_to_ECR` (limited) | HIGH |
| Reddit ECR-consumption probe (old.reddit r/b2bmarketing) | `docs/workflows/reddit_capture_to_ecr_consumption_probe_finding_v0.md` | `run_source_capture_http_packet`, HTTP 200 ~104 KB, 14 comments; `cutoff_posture` param | GO / residual by-design (missing Decision Frame, not a capture defect) | HIGH |
| Wall Street Oasis (7 pages) | `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_slot3_wso_capture_session_v0.md` | Browser visible-page + Wayback availability; email-unlock prompts visible, **not used** | `categorical_handoff_to_ECR` (partial; no full comment graph) | HIGH |
| Reddit API-pricing threads (r/reddit, r/Devvit, r/apolloapp) | `forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_pressure_test_threaded_forum_reddit_api_pricing_v0.md` | Public pages (live fetch blocked → recorded as source-access failure, not boundary); related-chain + package segmentation | Related-chain/bundle preserved; discharge specificity needs tightening | HIGH |
| Reddit offline packet consolidation (parser spec) | `forseti/product/spines/capture/core/source_capture_toolbox/reddit_packet_consolidation_runner_structural_spec_v0.md` | Packet reader; flat comment list + parent_id; closed comment-posture vocab | Packet-first boundary locked; raw packet > parsed text | HIGH (spec) |
| Slot-3 source-quality closeout (Reddit b1/b2 + WSO) | `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_slot3_post_recapture_closeout_v0.md` | Raw JSON + visible HTML (~200 KB cap) | `mini_god_tier_with_visible_limitations` (bounded GO) | MODERATE |
| Reddit thread **DISCOVERY** (screening seam) - find thread URLs without an external index | this row + `docs/workflows/reddit_candidate_intake_old_reddit_search_surface_handling_v0.md` (parse) + `docs/workflows/reddit_capture_to_ecr_consumption_probe_finding_v0.md` (live receipt) + `docs/workflows/screening_read_service_build_receipt_v0.md` (screening-read build receipt) | Reddit-native search/listing surface (`search-title`/`title` -> `/comments/` anchors), direct-HTTP rung; an external search-engine index is the wrong surface | **GO for bounded screening-read service** - listing/thread live-fetch GO; first-act old.reddit search-surface receipt closed 2026-06-21 via `screening_read`; `.json` rate posture remains a human-rate/backoff note | HIGH |

**Reddit thread discovery (screening seam) — working read shape.** *[discovery-spine cross-lane commission, 2026-06-11]*
- **Substrate (pattern 2):** Reddit's *own* search/listing is the discovery surface; the external search-engine index is the wrong surface — the discovery walk's zero-result on `site:reddit.com` queries is expected, **not** a capture gap. Native surfaces: `old.reddit.com/r/<sub>/search?q=…&restrict_sr=on` (+ `&sort=`/`&t=` window), subreddit listings `/new`, `/top?t=`, and their `.json` variants.
- **Rung (pattern 6, cheapest-first):** **direct-HTTP** is already GO on old.reddit *listing* (prior live run: HTTP 200 → 10 candidate thread URLs) and *thread body* (ECR-consumption probe: HTTP 200 ~104 KB). Parse with the documented `search-title`/`title`→`/comments/` anchors, then run the empty-result surface-shape check before any NO-GO (pattern 1: "blocked" is a hypothesis).
- **Entitlement (pattern 4, gate first):** logged-out public old.reddit page reads sit under the owner-authorized public-content posture; the licensed Reddit **Data API** (commercial-use gate) is a *separate* route not needed for discovery. The existing intake doc's "do not call `.json`" hard stop is that lane's *no-live-mode* discipline, **not** a global entitlement bar — but unauthenticated `.json` is rate-limited / ToS-bounded, so treat it as a direct-HTTP-rung route at human rate with backoff.
- **Residual closed / remaining note:** the search surface live receipt was closed 2026-06-21 by the bounded screening-read service (`old.reddit.com/r/beauty/search?q=skincare+moisturizer&restrict_sr=on&sort=new`: HTTP 200, 112317 bytes, 75 `/comments/` markers, no packet/ECR). The `.json` rate ceiling remains a human-rate/backoff note, not a blocker for old Reddit HTML screening reads.
- **Consumer:** the beauty card-set cards 4-6 access caveat. **Update 2026-06-21:** WebFetch-based walkers still cannot fetch `reddit.com` directly, but the orchestrator can invoke `source_capture.screening_read.screening_read(...)` for bounded public Reddit screening reads. Walkers record the need; they do not call the service directly. For public challenge-walled pages, `source_capture.screening_browser_read.screening_browser_read(...)` returns visible text and classifies `block_shell` on visible text, not full DOM.

### Pricing
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| OpenAI price payload **(worktree/lane, rung-1.5)** | `orca-rung15-wt` (branch `capture-rung15-openai-payload`, unmerged) | Embedded price payload + token-list certification | Committed-not-merged; narrowed "internally-consistent as-served" claim | HIGH ⭐ (lane) |
| M&I / BIWS | `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_slot1_mi_biws_capture_session_v0.md` | WebFetch → **paraphrase, not verbatim**; archive metadata known, bodies failed | `visible_stop` + re-capture posture (fidelity loss) | HIGH |
| Teal (tealhq.com) | `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_slot2_teal_capture_session_v0.md` | **HTTP 403 full-host block** → WebSearch fallback (non-verbatim) | `visible_blocker` + re-capture posture (anti-block/auth needed) | HIGH |

### Docs / changelog
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Kubernetes v1.32 deprecation guide / release blog | `forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_pressure_test_docs_changelog_versioned_page_v0.md` | Live docs + GitHub raw + static snapshot; version-page + last-modified coupling | Passed; docs-changelog satellite guidance | MODERATE |

### Archive / history
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Daimler DSU PDFs (pre-cutoff identity) | `docs/research/daimler_advisory_001_source_body_capture_dsu_001_003_receipt_v0.md` | Direct-HTTP **403**; archive.org CDX = **no pre-cutoff memento** | **NO-GO** on pre-cutoff version identity (honest) | HIGH ⭐ |
| Unity Runtime Fee (announce + recapture) | `forseti/product/spines/capture/core/operating_model/core_spine_v0_data_capture_spine_pressure_test_archive_history_recapture_v0.md` | Live + archive.org availability (bodies not fetched); recapture-delta | Archive availability ≠ body; recapture timing posture | MODERATE |

### Docs / PDF body (anti-bot escalation)
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Daimler DSU-001/002/003 PDFs (body capture) | `docs/research/daimler_advisory_001_browser_source_body_capture_dsu_001_003_receipt_v0.md` | direct-HTTP 403 + headless 403 → **visible Chrome + download button = captured bytes** (2.6/1.3/4.1 MB, `%PDF`, SHA256) | **GO via visible browser + user action** (corrected anti-bot diagnosis) | HIGH ⭐ |
| Daimler S1–S7 source acquisition | `docs/research/judgment-spine/harness/v0_14/fixtures/.../source_acquisition_receipt_v0.md` | Canonical issuer 403 → public-mirror + owner-supplied PDF fallback (SHA256 verified) | MIXED GO/NO-GO (canonical-domain bytes residual) | HIGH |

### SPA embedded-state
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Ulta product / Apollo cache **(worktree/lane, DP-002)** | demand-projection lane (`orca-demand-projection-wt`, unmerged) | `__APOLLO_STATE__` cache node; needle from field+value `"productId":"<id>"` | Provenance fix (a) applied in-lane; keep-gate pending | HIGH ⭐ (lane) |

### Retail/PDP storefront context
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| Amazon US delivery ZIP with conditional VPN recovery | `forseti/product/spines/capture/core/source_families/retail_pdp/amazon_us_vpn_regression_recovery_playbook_v0.md`; implementation at `forseti-harness/source_capture/adapters/amazon_delivery_location.py`; verified packet `F:\forseti-data-lake\raw\4f4\01KXVF7398CQY2GA4947KW0AAV` | Direct anonymous CloakBrowser remains first. A typed final `amazon.sg` redirect authorizes one owner-bounded Surfshark US / New York retry with the same subject and admission checks. Instrumented re-probe showed Amazon's location anchor hydrating about 3.6 seconds after `DOMContentLoaded`, beyond the former 2.5-second cap; one combined-selector visibility wait plus bounded click now stays inside the shared setup window. | `GO_CONDITIONAL_RECOVERY_WITH_AMAZON_OWNED_CONFIRMATION`; patched MakeWaves retry preserved Amazon.com, exact delivery ZIP `10001`, US marketplace markers, bound subject, no access block, and `pin_confirmed=true`. Earlier failed retry `01KXVBT44YJ2JGKZ9JZ5HRD1A5` remains typed evidence of the too-short readiness cap. VPN geography alone remains inadmissible. | HIGH ⭐ |
| Nordstrom US storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/nordstrom_country_preference.py` and `run_source_capture_cloakbrowser_packet.py --nordstrom-country US` | Retailer-owned country-preference UI before target navigation; confirmation requires selected US/USD plus one shopper context with `CountryCode=US`, `CurrencyCode=USD`, `IsInternationalShopping=false` | `US_USD_STOREFRONT_CONFIRMED_DELIVERY_LOCATION_UNPINNED`; live PDP and grid packets passed with `pin_confirmed=true`, no proxy/profile/storage-state/geo-IP/credential; PDP still showed `Shipping to 518225` | HIGH ⭐ |
| Luckyscent US storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/luckyscent_us_market.py` and `run_source_capture_cloakbrowser_packet.py --luckyscent-market US` | Luckyscent exposes no country selector. Its canonical route is admitted only when one serialized storefront `i18n` object binds `country=US`, `market=market-us`, and `currency=USD`; loose dollar, offer, or `buyerCountry` signals do not count. The route may close only the exact known first-order promotional modal through its exact `Close dialog` control; changed or unresolved state is a typed raw-preserving failure. | `US_USD_DEFAULT_STOREFRONT_CONFIRMED_DELIVERY_LOCATION_UNPINNED`; live Pearfat PDP packet `01KXRG2C722GPTCVF6V8MFR4Y5` and post-cut isolated content canary `01KXZV2VDX31YPFD25N30P42TT` passed with `pin_confirmed=true`, no proxy/profile/storage-state/geo-IP/credential. The content canary retained three offers and all eight reviews in 241,332 total bytes versus the 610,541-byte historical raw packet. Separate origin-derived `buyerCountry=SG` remained visible. | HIGH ⭐ |
| Sephora US storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/sephora_us_market.py` and `run_source_capture_cloakbrowser_packet.py --sephora-market US` | `country_switch=us` is request intent only. Admission requires the final Sephora page to bind `Sephora.renderQueryParams.country=US` and a Sephora-sold JSON-LD `Offer` with `priceCurrency=USD`; the plugin performs no preference mutation. | `US_USD_STOREFRONT_CONFIRMED_DELIVERY_LOCATION_UNPINNED`; live Tower 28 LipSoftie packet `01KXRZQJBKNKC91SXH2C7MKF1C` passed with `pin_confirmed=true`, no proxy/profile/storage-state/geo-IP/credential. Projection anchored product `P509397` and USD offer SKU `2843068`; the known Sephora review-count residual remained explicit. | HIGH ⭐ |
| Ulta US storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; failed live packet `F:\forseti-data-lake\raw\d52\01KXSSJBMN6T4Z480ZX1RHA3MB` | Anonymous CloakBrowser on the canonical Night Shift PDP with `ulta_pdp_aggregate`, five-second settle, and one scroll pass. The commissioned assertion required `window.__LOCALE__='en-US'`, one source node binding `data-locale="en_US"` with `data-currency="USD"`, and JSON-LD Product SKU `2645443` with a nonempty USD offer. | `NO_GO_REQUIRED_RENDERED_MARKET_SIGNALS_ABSENT`; the bound product, SKU, USD offer, price, and 671-review state rendered, but the locale assignment and `data-locale` signal did not. The typed packet was preserved with `pin_confirmed=false`; the unproven adapter/flag was removed and no projection or pin was promoted. | HIGH ⭐ |
| Ulta US/USD storefront assertion recovery without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/ulta_us_market.py` and `run_source_capture_cloakbrowser_packet.py --ulta-market US`; verified PDP packet `F:\forseti-data-lake\raw\b6e\01KXWQW45J2C17RX4397Z27KYJ` | Fresh read of the historical raw DOM identified the actual first-party names: root `lang=en-US`, `window.__APP_LOCALE__='en-US'`, GraphQL `ultasite=en-us`, and a product `square-placement` joining `data-consumer-locale=en_US`, `data-currency=USD`, and amount. Admission additionally binds exact URL SKU `2645443` to its Product JSON-LD nonempty USD offer. The assertion mutates no preference. | `GO_US_USD_STOREFRONT_CONFIRMED_OFF_VPN`; the canonical Night Shift PDP retained exact `www.ulta.com`, `pin_confirmed=true`, no access block, subject/price/review sufficiency, and four fresh-matched hashes. Retail/PDP projection anchored the exact SKU/USD offer and 671-review / 4.3-rating substrate with zero residuals. `.com`, dollar glyph, HTML language alone, and VPN geography remain inadmissible substitutes. | HIGH ⭐ |
| Walmart US storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; failed live packet `F:\forseti-data-lake\raw\1cf\01KXSV9HFFEPNEXVA407318KW1` | Anonymous Direct HTTP on canonical Vitamasques item `2150828728` with `walmart_pdp_aggregate`. Admission required one `initialData.data` object to bind URL/product item, exact USD currency, equal page/product postal state, and an immediate targeting scalar `countryCode=="US"`. | `NO_GO_REQUIRED_SIGNAL_SHAPE_MISMATCH`; item, USD, postal `95829`, and profile sufficiency passed, but the retailer serialized immediate `countryCode=["US"]`. The typed packet was preserved with `pin_confirmed=false`; list membership was not substituted for scalar equality, the unproven flag was removed, and no pin or projection was promoted. | HIGH ⭐ |
| Walmart US/USD storefront assertion recovery without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/walmart_us_market.py` and `run_source_capture_http_packet.py --walmart-market US`; verified PDP packet `F:\forseti-data-lake\raw\920\01KXWY75J4419N85NAXPXGZG8Q` | Fresh read of the historical raw `__NEXT_DATA__` confirmed Walmart serializes the immediate module targeting country as exact `["US"]`. Recovery admits scalar `"US"` or only that exact single-item list, while retaining the same item-ID, exact USD, equal-postal, final-host, and profile gates. The assertion mutates no preference or location. The generic Retail/PDP projector now recognizes Direct HTTP's preserved body as HTML input. | `GO_US_USD_STOREFRONT_CONFIRMED_OFF_VPN_ORIGIN_LOCATION_UNPINNED`; the canonical Vitamasques PDP retained exact `www.walmart.com`, HTTP 200, `pin_confirmed=true`, slice pins `US` / `USD`, item `2150828728`, and fresh-matched raw hashes. Projection `01KXWY7K99EPG92XW2GZ6BTTH0` anchored one product and one item `2150828728` offer at `2.97` USD. Postal `95829` remains origin-derived, and inventory, sold-units, delivery-pin, and review-substrate residuals remain explicit. | HIGH ⭐ |
| Target US delivery ZIP without proxy | Live Naturium grid packets `F:\forseti-data-lake\raw\27d\01KXRK26RMXSBSEGVP8BKRG9GX` and `F:\forseti-data-lake\raw\3d6\01KXRKJNQZCMKM6ATV55B0AYG5` | Generic homepage setup could not open the public ZIP control. A bounded retry on the commissioned grid completed the retailer-UI steps and rendered header `Ship to location: 10001`, but the same page retained top-level and nested `serverLocationVariables` ZIP `52404` with country `US`. | `NO_GO_SPLIT_LOCATION_SIGNAL`; header-only application does not confirm the commissioned conjunction. Both typed packets were preserved, the PDP was not attempted, the unproven adapter was reverted, and the registry remains `OBSERVED_US_CONTEXT_UNPINNED` / `OBSERVED_LOCATION_UNPINNED` / `OBSERVED_USD_UNPINNED`. | HIGH ⭐ |
| Target US delivery ZIP recovery without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; failed grid packets `F:\forseti-data-lake\raw\66c\01KXSX9FXXEVTFSXF9DKYWKW1T` and `F:\forseti-data-lake\raw\bd9\01KXSXGCKNJQCRKNPYDPY944HY` | Recovery correctly separated shipping header state from store/pickup ZIP. Anonymous ephemeral CloakBrowser attempted the public grid header control with a 30-second setup window; the corrected attempt added a five-second render settle, six-second capture settle, and one scroll pass. | `NO_GO_PUBLIC_ZIP_CONTROL_NOT_INTERACTABLE_DURING_BOUNDED_SETUP`; both attempts stopped at `open_zip_control`. The final captured DOM later contained `#zip-code-id-btn` with shipping `52404` and country/store context `US` / `52404`, so this is an interaction-timing/interactability failure, not control absence. The PDP and projections were not attempted, the unproven route was removed, and no pin was promoted. | HIGH ⭐ |
| Target US delivery ZIP with bounded readiness and scoped form submission | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/target_delivery_location.py` and `run_source_capture_cloakbrowser_packet.py --target-zip 10001`; verified grid/PDP packets `F:\forseti-data-lake\raw\a37\01KXWMQWHRABBSA5HN3CMR9TNS` / `F:\forseti-data-lake\raw\981\01KXWMXEYB58SMVSJT80XJAP9D` | Instrumented retries separated three phases: the earlier route missed the late control; the first new packet opened it but missed the visible input; the second filled the scoped input but found no recognized visible action. The admitted route waits once for visible `#zip-code-id-btn`, scopes visible ZIP input/action selectors to Target's dialog/ZipCode component, and permits Enter only on that already-scoped input. Post-submit admission still requires completed UI setup, exact shipping header/child ZIP `10001`, and Target-owned country `US`; store ZIP remains separate. | `GO_TARGET_US_ZIP_10001_CONFIRMED_OFF_VPN`; both commissioned Naturium surfaces retained `www.target.com`, exact shipping/server ZIP `10001`, `country=US`, separate store ZIP `10011`, subject/product/price sufficiency, no access block, and `pin_confirmed=true`. Existing grid/PDP projections anchored 24 Naturium products plus the bound Target offer/review substrate. Currency remains `OBSERVED_USD_UNPINNED`. The owner-commissioned VPN homepage differential was not triggered because the direct off-VPN route confirmed the pin. | HIGH ⭐ |
| Kohl's US/USD storefront access diagnosis | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; Direct HTTP PDP `F:\forseti-data-lake\raw\fbe\01KXT0245PZBHZSYJHM5376BCA`, cold CloakBrowser PDP `F:\forseti-data-lake\raw\64f\01KXT04HA0TT33RH7BAWQ38H58`, Direct HTTP FAQ `F:\forseti-data-lake\raw\e64\01KXT09ERZ6584J7M4J07WS706`, humanized homepage-warmed FAQ/PDP `F:\forseti-data-lake\raw\ace\01KXT3432PEF0NXEZE0VWEWMMD` / `F:\forseti-data-lake\raw\039\01KXT38WKZMXVMMY18CDX3SC66`, header-complete HTTP PDP/policy `F:\forseti-data-lake\raw\f77\01KXTZ76J5BGQJTEP2QDCZDYHY` / `F:\forseti-data-lake\raw\037\01KXTZ77WYTPH15N1F8XNK87HC`, owner-operated US consumer-VPN CloakBrowser block PDP/policy `F:\forseti-data-lake\raw\2d3\01KXXBP2HTK718ZS9CZ11CQJX0` / `F:\forseti-data-lake\raw\ba1\01KXXBVY7RTBSHN651P124X0E8`, warmed-real-browser CDP GO PDP/policy `F:\forseti-data-lake\raw\b99\01KXXHBKF2GPK4M96SAV1VQKM3` / `F:\forseti-data-lake\raw\661\01KXXHC3BZ27D3WWDJ8QPV8004` | Packet-backed ordinary and header-complete HTTP returned typed 403 block shells on both bound routes. Canonical/bare/mobile host, `/api/amp`, typeahead, and anonymous first-party app/config candidates were explored only as unpreserved scouting and carry no Capture Spine verdict. Cold and homepage-warmed anonymous CloakBrowser also rendered Akamai `Access Denied`. A separate scouting browser reached both commissioned routes, proving route liveness but not isolating exit IP from browser/TLS identity. A 2026-07-19 owner-operated US consumer-VPN run (Surfshark WireGuard, US/New York datacenter exit `AS60068 Datacamp`) preserved CloakBrowser Akamai block packets on both bound routes; a matched in-app visible-browser control on the SAME exit was also Akamai-denied, which was read at the time as isolating exit-IP reputation as the block cause (CORRECTED 2026-07-19, below). Owner-directed follow-up headed-CloakBrowser scouting (stealth+humanize) was Akamai-denied on both the US datacenter VPN and the normal SG residential connection; but a warmed real Chrome (personal profile via CDP) then reached full content over the SG residential IP — the bound LipSoftie PDP at `$16.00` / `priceCurrency USD` and the US-shipping-only policy — falsifying the exit-IP/browser-independent reading. The discriminator is the warmed real-browser Akamai session; cold/automation browsers are denied on every egress tested and the reproducible Capture Spine route stays NO_GO (not runner-reproducible, no pin). No registered US residential profile or entitled retailer feed was available. | `NO_GO_CAPTURE_SPINE_RUNNER_AKAMAI_BOT_BLOCKED_ANY_EGRESS; SUBJECT_CONTENT_REACHED_ONLY_VIA_WARMED_REAL_BROWSER_NOT_RUNNER_REPRODUCIBLE` (2026-07-19; retracts the earlier `...EXIT_IP_REPUTATION_BROWSER_INDEPENDENT` token, which a warmed real-browser session falsified). The reproducible armory-runner route was NOT promoted (no projection, adapter, or API surface). Owner-directed 2026-07-19, a route-specific pin WAS promoted via the warmed-real-browser CDP path: live GO packets PDP `01KXXHBKF2GPK4M96SAV1VQKM3` and policy `01KXXHC3BZ27D3WWDJ8QPV8004` (HTTP 200, cache disabled) bind schema.org `Offer` `price=16`/`priceCurrency=USD` on the Tower 28 LipSoftie PDP plus Kohl's own US-shipping-only policy, so the storefront-pin registry records `CONFIRMED_US` / `CONFIRMED_USD` (delivery `UNPINNED`). On 2026-07-20 this was promoted to a committed **rung-7** capture runner, `run_source_capture_realchrome_cdp_packet.py` (attach to an operator-provided real Chrome over CDP, homepage warm hop, standard packet seam), with runner-backed GO packets PDP `01KXXK9PJTA2KBRS2CM1MZDV1H` and policy `01KXXKA9RJBP6SVT455DTR0K08`. A cold fresh real-Chrome context also cleared the wall, so the route depends on the real-browser fingerprint, not pre-warming or a personal profile. Search-indexed pages, `.com`, dollar glyphs, archive/cache, and proxy geography remain non-pin. The headless armory runners stay Akamai-blocked; the rung-7 runner is reproducible but operator-gated (needs a real Chrome running under CDP). A fully-unattended route (headless-new real Chrome, or a US residential / entitled / paid egress) remains an open follow-up. | HIGH ⭐ |
| Credo US/USD default storefront without proxy | `docs/research/forseti_beauty_retailer_surface_probe_results_v0.md`; implementation at `forseti-harness/source_capture/adapters/credo_us_market.py` and `run_source_capture_http_packet.py --credo-market US`; verified Tower 28 PDP packet `F:\forseti-data-lake\raw\7dd\01KXX1S3VYWQM3NNM23VYK3EPW`; bounded Yotpo packet `F:\forseti-data-lake\raw\db5\01KXX5M6BGQ6CM9XJ1752F7N2Y` | Direct HTTP returned the exact requested/final/canonical Credo product route. A fail-closed assertion joined only `Shopify.country=US`, only active `Shopify.currency=USD`, and exactly one route-bound Product JSON-LD object with named Tower 28 brand and nonempty priced USD offers. The generic Retail/PDP projector selects the Product-SKU-matching offer from a valid JSON-LD `offers` array and recognizes the exact server-rendered Yotpo block. Raw PDP state separately preserves all three variants, subscription allocations, ingredients, and packaging language. The existing rendered-widget companion passively preserved Yotpo's five-row `sort=rating,date,images,badge` response and one bounded ten-row `sort=date` response; no new runner was added. | `GO_US_USD_DEFAULT_STOREFRONT_CONFIRMED_WITHOUT_VPN_DELIVERY_UNPINNED`; corrected PDP projection `01KXX3P3PPQV3625JKFDGA3JY7` anchored selected SKU `210000007835` at `12.0` USD, aggregate `4.705247/5` from 648, and 10/10 server-rendered bodies. Coverage-v1 review projection `01KXX6RCN8C2XTH3JZF055RMSJ` preserved ten date-sorted bodies, nine verified flags, five loyalty-points incentivized flags, and nine reviewer-declared age ranges. Both ten-row views remain bounded subsets; the review packet's legacy `fragrance_review` family name is typed and makes no category claim. No new runner, projection schema, or retailer enum was added. | HIGH ⭐ |

The earlier Kohl's diagnosis row is historical sequence evidence. Its final
operator-gated/open-follow-up statement is superseded by the completion record
below.

### Unattended browser route completion

| Source probed | Path | What ran | Verdict | Confidence |
|---|---|---|---|---|
| Kohl's unattended Xvfb real-Chrome route | `docs/workflows/forseti_unattended_akamai_headful_capture_route_handoff_v0.md`; implementation at `forseti-harness/runners/run_kohls_unattended_capture.py` and `forseti-harness/containers/realchrome_xvfb/`; verified PDP `F:\forseti-data-lake\raw\897\01KXXV920Z8PQVHP6DN16335DF` and policy `F:\forseti-data-lake\raw\950\01KXXVA8B5EHY86N4EJZ7Y6360` | The one-shot built the real-Chrome image, started a temporary headful Chrome under Xvfb with a private loopback-only CDP port, captured both bound surfaces through the rung-7 packet seam, and stopped the container. Both packets recorded unattended provisioning and a persistent profile, returned HTTP 200, were not access-blocked, and passed exact product/policy gates. The passing browser exposed no usable WebGL context, retracting the earlier “real GPU required” explanation without isolating the exact Akamai discriminator. | `GO_KOHLS_UNATTENDED_REALCHROME_XVFB`; the admitted route is no longer operator-gated for the bound Kohl's PDP + policy. No recurring schedule was registered because no owner-approved frequency exists and every run writes two durable packets. The generic operator-provided rung-7 path remains available for other sources; arbitrary Akamai sites, Linux sandbox behavior, and datacenter egress remain unproven. | HIGH ⭐ |

### Certifier / accreditation "seal" directories (JS-rendered landing → public data endpoint)
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| NEA (National Eczema Association) Seal of Acceptance | Tower 28 v2 CI scan `docs/research/forseti_beauty_tower28_company_intelligence_scan_v2.md` (merged PR #1087); packets `01KXRMFR7P8QSKPQM66XTVXW46` (landing), `01KXRMGB4WEVBF19G464PSHZNJ` (REST) | Landing `https://nationaleczema.org/eczema-products/` is a JS-rendered **zero-yield** page; the product list lives in the **WordPress REST API on the CMS host**: `https://cms.nationaleczema.org/wp-json/wp/v2/eczema-products?search=<term>&per_page=20` | **GO** via direct fetch of the REST endpoint (9 Tower 28 titles; one record binds to tower28beauty.com) | HIGH |
| NRS (National Rosacea Society) Seal of Acceptance | same scan; packet `01KXRM4HZJVVRVFAGFFX6VY5DD` | The **Drupal Views fulltext-filter URL** returns the list directly: `https://www.rosacea.org/seal-of-acceptance/information?search_api_fulltext=<Term+With+Plus>` | **GO** (7 "by Tower 28" products; reproduced by re-loading the filter URL) | HIGH |
| NPF (National Psoriasis Foundation) Seal of Recognition | same scan; packets `01KXRMHRKJEZ9TJYXBYFB78514` (landing→redirect), `01KXRMJBBSE3BP9RF0PAEQ3B7H` (feed) | Landing `https://www.psoriasis.org/seal-of-recognition/` redirects to `/seal-of-recognition-program/` and is **zero-yield**; data is a **Gatsby `page-data.json` feed per category**: `https://www.psoriasis.org/page-data/seal-of-recognition/<category>/page-data.json` (e.g. `skin-care`), client-side filter on `product_company` | **GO** via direct fetch of the page-data feed (7 `product_company "Tower 28 Beauty"` products) | HIGH |

**Certifier "seal" directories — working read shape (Tower 28 v2 CI, 2026-07-18).** All three
health-org product directories (NEA eczema, NRS rosacea, NPF psoriasis) serve a **zero-yield
landing page** and hold the real product list behind a **public, unauthenticated JSON/data
endpoint** — textbook **Pattern 2** (locate the substrate first) plus **Pattern 1** (the empty
landing is not "blocked"). The endpoint shape is stable per CMS engine: **WordPress REST**
(`/wp-json/wp/v2/<type>?search=`), **Drupal Views fulltext** (`?search_api_fulltext=`), **Gatsby
page-data** (`/page-data/<route>/page-data.json`). **Prefer `get_page_text` / direct fetch of the
data endpoint; screenshots time out on the rendered landing pages** and returned only the
zero-yield view. Directory presence verifies **seal acceptance/recognition only — not efficacy or
comedogenicity**. Next certifier-directory read (any subject with health-org / clean / cruelty-free
seals; silent-pain class 9): hit these endpoints directly and skip the landing page and
screenshots.

### Browser-automation runner
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| CloakBrowser local setup | `forseti/product/spines/capture/core/source_capture_toolbox/cloakbrowser_local_setup_probe_receipt_v0.md` | Local binary (Chromium 146) + API introspection; smoke test | `READY_FOR_ADAPTER_CONTRACT_SCOPING` | HIGH |
| CloakBrowser packet-runner architecture | `forseti/product/spines/capture/core/source_capture_toolbox/cloakbrowser_packet_runner_architecture_v0.md` | API shape from public docs + introspection; no-secret/anonymous seam | `TARGET_RECOMMENDED` (adapter-contract-first) | HIGH (arch) |
| Screening browser read wrapper | `docs/workflows/screening_read_service_build_receipt_v0.md`; code at `orca-harness/source_capture/screening_browser_read.py` | CloakBrowser render -> visible text only; `block_shell` classified on visible text to avoid residual Cloudflare DOM-script false positives | Implemented on PR branch; no packet / no manifest / no ECR | HIGH |
| Quora B2B search (post-merge PR #825 calibration) | `docs/workflows/quora_b2b_postmerge_capture_calibration_v0.md`; review report `docs/review-outputs/adversarial-artifact-reviews/quora_b2b_postmerge_capture_calibration_delegated_adversarial_review_patch_v0.md` | CloakBrowser persistent local ignored profile; lower-rung auth-browser probe hit Cloudflare interstitial; signal lives in rendered Quora search-result visible text; caller-bound detail gate required B2B result details and stable question-title markers | GO for one bounded Quora B2B search packet; not session durability, broad Quora reliability, proxy/geo proof, or buyer proof | HIGH |

### Social networks (policy boundary; technical route coverage uneven)
| Source probed | Path | Rung / where signal lives | Reported verdict | Signal |
| --- | --- | --- | --- | --- |
| LinkedIn official policy | `forseti/product/spines/capture/core/source_capture_toolbox/linkedin_reddit_source_capture_armory_concurrent_structure_architecture_v0.md` | Policy docs (2026-06-05): scraping/automation forbidden absent authorization | **Boundary-only** — official/API/manual/entitled routes only; no scraping | MODERATE-HIGH |
| Instagram wind-caller — own `@foo_yu_quan` + third-party `@hyram` *(2026-06-14)* | `forseti/product/spines/capture/core/source_families/social_media/instagram/ig_wind_caller_capture_feasibility_recon_v0.md` | Attended logged-in browser (own + 1 public third-party, no wall). **Grid = index only**; capture is **per-item: each `/p/` AND `/reel/` page, one-by-one**. Per item → **full verbatim caption in the rendered DOM node** (meta `og:description` truncates ~59% on a post, ~86% on a reel) + **likes/comments/date/`#ad` sponsorship flag**. Enumerate via **scroll pagination** (12 → 48 / 3 passes). Stats → profile `og:description`/header + Social Blade free (recent daily window; deep history premium) + `web_profile_info` JSON (counts only). `direct_http` NO-GO for signal (200 shell; API **429 cookieless** → **200 logged-in**). | **GO (demonstrated, n=2)** — self-capture calls via DOM (moat), **buy** stats series (Social Blade free). Residual: sustained cadence (H5), full enumeration, robust caption selector, **reel view/play count (in GraphQL JSON, not page DOM)**. Harness-native authenticated capture **already exists** (browser_snapshot + auth_state + runners + cadence, authorized/reviewed); IG = compose + small delta (loop runner, extraction, reel warm-JSON, block markers) — see ig_wind_caller_calls_capture_build_architecture_v0.md. | HIGH ⭐ |
| Instagram reel **view/play count** — `@hyram` 3 reels *(2026-06-14)* | `forseti/product/spines/capture/core/source_families/social_media/instagram/ig_reel_viewcount_capture_feasibility_recon_v0.md` | **Profile-feed JSON** (`web_profile_info` + grid `graphql/query` pagination), **logged-out 200**, `video_view_count` per media keyed by `shortcode` — **not** on the reel permalink page (surfaces A/B/C empty there). | **GO logged-out — incl. deep history.** `video_view_count` reachable **cookieless in a browser context** (refines prior "API 429 cookieless"); cursor-following the grid `end_cursor` paginated **25 pages, all `200`, 365 media back to 2017**, **no wall / no `429`**; **session run byte-identical → unnecessary**. Residual: sustained cadence at scale (H5 / multi-account-over-time). | HIGH ⭐ |
| Instagram Reels **deep-capture transcript route** *(2026-06-29 no-write live diagnostics)* | `docs/workflows/ig_behavioral_live_validation_receipt_v0.md`; code route `orca-harness/runners/run_source_capture_ig_reels_deep_capture.py` + `orca-harness/source_capture/ig_reels_deep_capture.py` | Standalone anonymous `yt-dlp` media fetch returned Instagram empty-media responses for a prior legacy-success shortcode and a grid-selected shortcode. The rendered reel page still exposed a transient IG-CDN media handle; the one-render deep-capture route downloaded that handle immediately and ASR'd it while also parsing comments from the same render. | **GO for route-specific public deep-capture ASR diagnostic.** Standalone `yt-dlp` empty media is a route residual, not an IG transcript NO-GO. Residuals: no canonical F-lake write in this diagnostic, no durable media/video preservation claim, no cookies/login/proxy, and route cadence/stability remain open. | HIGH ⭐ |
| Instagram creator **discovery** — suggested/related-accounts edge — `@jeremyfragrance` / `@nikkietutorials` / `@hyram` *(2026-06-15)* | `forseti/product/spines/capture/core/source_families/social_media/instagram/ig_creator_discovery_suggested_accounts_recon_v0.md` | **`web_profile_info` JSON** `data.user.edge_related_profiles` — the tolerant **200-cookieless** surface (same as calls/stats/reel-views); node = `username`+`id`+`full_name`+`is_verified`+`is_private`+`profile_pic_url`; sub-niche-coherent | **GO (logged-out, n=3)** — edge populated logged-out (19 / 32 related accounts for two seeds; `hyram` empty via crawler-strip/opt-out variant). Snowball feasible (`username`+`id` → next wpi). 6 reqs all 200, no 401/429. Residual: snowball depth / coherence / follower-bands / crawler-strip retry / wpi own ceiling = Phase 2. | HIGH ⭐ |
| YouTube long-form + Shorts — 5 creators *(2026-06-21)* | `forseti/product/spines/capture/core/source_families/social_media/youtube/youtube_capture_recon_v0.md` | **Embedded `ytInitialPlayerResponse`** in served HTML (logged-out, no JS): exact `viewCount`/`lengthSeconds`/absolute-ISO `publishDate`/`channelId`/`author`/description. **Comments** via `youtubei/v1/next` panel-scoped continuation — same route both surfaces, paginated, `publishedTime` **relative-only**. | **GO (n=10 logged-out)** — long-form & Shorts share substrate + field paths + comments route → **unified one-runner + `surface_type` switch** (no split trigger fires). Residual: `comments_disabled` posture (NASA), surface_type discriminator = serving-surface not duration, like abbreviated at scale, live/age-restricted/EU-consent unsampled; **capture not yet persisted (recon only)**. | HIGH ⭐ |
| TikTok creator/profile grid + video metadata + top comments *(2026-06-21/22; public+sessioned diagnostics 2026-06-30)* | `forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_first_slice_probe_recon_v0.md`; `forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md`; `forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md`; `docs/workflows/tiktok_public_route_live_diagnostic_receipt_v0.md`; `docs/workflows/tiktok_sessioned_warm_probe_receipt_v0.md`; `docs/workflows/tiktok_sessioned_profile_grid_dom_receipt_v0.md` | Real/non-headless cookied browser; profile grid DOM selectors (`user-title`, `user-bio`, `user-link`, `user-post-item`, `video-views`); page-owned embedded blobs for profile/video metadata/stats/author/music/textExtra; page-emitted `/api/comment/list` responses for public top/relevant comments with exact `create_time`, `cid`, and commenter ids in the first slice. The 2026-06-30 sessioned profile-grid pass loaded `@tiktok` without visible login/challenge signals, parsed `webapp.user-detail`, observed 31 `user-post-item` / `video-views` nodes, and captured 24 unique video anchors in a bounded structured sample. The 2026-06-30 sessioned video pass rendered comment DOM but did not capture the `/api/comment/list` response body. Direction update pivots sustained capture to **sessioned/cookied dedicated account** because logged-out/public route is brittle. | **PARTIAL / first-slice GO, scale unmeasured.** Profile-grid DOM is now sessioned N=1 clean for the locked fixture; video metadata is sessioned N=1 clean; visible comment DOM is sessioned N=1 clean. Exact sessioned `cid`/`uid`/`create_time` packet fields, exact grid-view-count normalization, grid pagination/depth, and per-account ceiling remain unmeasured. Public diagnostic parsed metadata but stopped on a visible slider challenge before comment capture. Sessioned warm-probe plan still requires dedicated non-personal account, human login, per-operation network approval, account-ban risk acceptance, no secrets in packets, public content only, packet-grade response capture, and stop-on-challenge. Transcript/audio/ASR and durable media/video are not proven. | HIGH ⭐ |
| TikTok Shop official brand storefront + complete PDP denominator *(Summer Fridays, 2026-07-26)* | `forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_shop_capture_lane_spec_v0.md`; Data Lake packets `01KYFJPW9SMCJAE1EFS4ZGRHFC`, `01KYFJJXWCDFH2GCCZGEJ3MXF5`, and `01KYFJPWN8VAVMHB8TME5RV3ZV` | Owner-selected routed real Chrome after a fresh same-context US-country egress check; official storefront card → PDP → `Sold by Summer Fridays` return loop; DOM-first offer and `Videos for this product` shelf capture; non-metronomic 4.9–36.5 s ordinary dwell with 10% 36.5–66.0 s tail; operator-supervised challenge handoff; separate sanitized offer, creator-shelf, and route-diagnosis packets. | **GO for one complete brand run / PARTIAL as a general lane.** All 30 unique storefront listings were reached natively; 569 product-linked creator cards, 307 distinct displayed creator names, 555 explicit commission labels, and 889,220 gross visible hearts were preserved. One slider challenge was manually cleared by the operator after the agent stopped, and one transient tunnel failure recovered. Hearts are not reach; displayed names are not a total creator census; cross-brand selectors, canonical video identity, unattended survivability, and a stable challenge ceiling remain unproven. | HIGH ⭐ |

**IG reel view/play count (2026-06-14).** Closes part of the prior IG recon's "reel view/play count (in GraphQL JSON, not page DOM)" residual and **refines** its "`web_profile_info` API 429 cookieless → 200 logged-in" line: in a real browser context (IG's `X-IG-App-ID`/web headers) `web_profile_info` returned **200 cookieless** carrying `video_view_count` per media, keyed by `shortcode`; the earlier 429 was the **header-less `direct_http`** rung, not a browser-context XHR. The signal lives in the **profile feed**, not the reel page, so a build folds into the **existing logged-out grid load** — not a per-reel or session capture. **IG reel view/play count — corrected (2026-06-14).** First reported "walls early" from a UI-scroll probe; that was an **artifact** (a DOM login-heuristic that fired regardless of auth, and `mouse.wheel` never triggering IG's infinite-scroll — identical logged-out/session results were the tell — recon **Pattern 1**). The valid method, **following the grid's own `end_cursor` via the `graphql/query`**, paginated **25 pages all `200`, 365 media back to 2017-08-22**, **logged-out**, no wall / no `429`; the **session run was byte-identical** → session buys nothing. Net: `video_view_count` is reachable **logged-out incl. deep history**; the session lane is **retired** for this purpose. **One residual:** sustained cadence at scale (H5 / multi-account-over-time).

**IG creator discovery — suggested-accounts edge (2026-06-15).** Discovery mechanism 1 (the
rising-creator spine) for the IG creator-momentum pipeline is **GO logged-out**: the
related-accounts graph is `data.user.edge_related_profiles` in `web_profile_info` — the **same
tolerant 200-cookieless surface** as calls/stats/reel-views — so the whole pipeline runs on
**one IG substrate**, no off-IG discovery DB and no session. Populated logged-out (19 and 32
related accounts for two seeds; **sub-niche-coherent** — a fragrance seed returns fragrance
accounts), each node carrying `username`+`id` so the **snowball is feasible**. One empty seed
(`hyram`) coincided with the **crawler-strip / login-wall variant** (bundle flag
`should_remove_related_profiles_for_crawlers`) or an account opt-out — a known empties source
for Phase 2 to detect-and-retry, **not** a reachability failure. **Phase 2 (bounded snowball,
2026-06-15): GO mechanics, two design requirements.** Pure-wpi (no profile nav) sidesteps the
strip; 15 reads all 200 (wpi ceiling ≥15); 15 fetches → **243 unique accounts**, 69 multi-set →
bounded community. But (a) **sub-niche coherence degrades at depth** via bridge nodes (one
`@Bible` relation injected a religious cluster) → a **sub-niche filter is now GATING**, not
polish; and (b) a **mega seed surfaces only mid-tier** (≥184k), so the rising tier (~10k–100k)
needs deeper snowball. Production at-scale + the discovery-read posture remain open.
`ig_creator_discovery_suggested_accounts_recon_v0.md` is the finding;
`ig_creator_discovery_spec_v0.md` is the capability spec.

**TikTok sessioned DOM/hydration update (2026-06-30).** A later same-lane
receipt, `docs/workflows/tiktok_sessioned_dom_hydration_profile_comments_receipt_v0.md`,
extends the partial TikTok state: one sessioned Chrome TikTok tab, no duplicate
TikTok tabs, public content only, no session-secret reads/writes, profile
hydration + stable DOM selectors, 95 `user-post-item` / `video-views` nodes, 94
unique profile-grid video anchors, pinned-video `webapp.video-detail` hydration,
and 20 visible top-level comment DOM rows without visible login/slider/verify
markers. It still does **not** capture `/api/comment/list` response bodies, so
sessioned packet fields (`cid`, `uid`, exact comment `create_time`, cursor,
`has_more`), exact grid-view normalization, per-account ceiling, transcript/ASR,
and durable media remain unproven. A same-day existing-Chrome follow-up confirmed
the pinned video and comments render cleanly in the logged-in user Chrome
session, but the current Chrome-extension surface exposes only `pageAssets`
(static/media asset inventory), not XHR/fetch response bodies, and its read-only
page scope lacks resource-timing access. Treat more Chrome-extension DOM probing
as non-packet-grade; the next proof must use a supported response-body capture
surface for the page-owned `/api/comment/list` request.

**TikTok Funmi N30 comment/subtitle cadence + batch admission update (2026-07-01).**
`docs/workflows/tiktok_funmi_n30_comment_subtitle_cadence_analysis_v0.md`
supersedes the response-body-unmeasured part of the prior Funmi sessioned
state for one creator/session: 30/30 videos completed with page-owned
`/api/comment/list` parsed fields, 0 challenges, 0 failures, and no raw
response body or endpoint persistence. Source-native WebVTT subtitles parsed
for 26/26 videos where `subtitleInfos` existed; the other 4/30 lacked
`subtitleInfos`. A durable sanitized parsed-batch SourceCapturePacket now exists
at `F:\orca-data-lake\raw\97c\01KWCYZ9P72W4SJD7NDPRQT0DB` with source surface
`tiktok_creator_batch_comment_subtitle_admission`, preserving 596 parsed comment
rows, 1044 WebVTT cues, and deterministic typed extraction seeds. This does not
prove cross-creator coverage, higher-volume account safety, full comment census,
durable media/video preservation, final product extraction, or platform-wide
subtitle availability.

## Coverage map

- **Well-covered:** forums/threads (Reddit ×4, WSO), pricing (M&I, Teal, OpenAI-lane), archive/history (Daimler, Unity), docs-PDF body (Daimler — the strongest anti-bot escalation case), browser runner (CloakBrowser), reviews (ClickUp + Sephora-pending).
- **Thin / single-fixture:** docs-changelog (Kubernetes only), reviews (one merged fixture; the strong one is worktree-pending), SPA embedded-state (Ulta worktree-pending only), certifier/accreditation directories (NEA/NRS/NPF, one run — JS-landing→public-JSON pattern).
- **ABSENT / PARTIAL — directly relevant to the stated multi-source product direction:**
  **TikTok is no longer absent, but remains partial.** First-slice TikTok recon and a sessioned
  capture spec/warm-probe plan now exist (see Social networks table), proving route existence for
  public page-owned metadata and top/relevant comment responses in a real cookied browser while
  leaving sessioned detection ceiling, scale reliability, durable media/video, cross-creator subtitle coverage,
  final product extraction, and projection implementation unproven. Parsed batch packet admission is now proven for Funmi N30. **YouTube is now probed** (2026-06-21 — **GO**,
  n=10 logged-out; long-form + Shorts unified, served-HTML embedded state + `youtubei` comments;
  see the Social networks table). **Instagram is now probed** (own-account
  wind-caller recon, reel view/play count, creator discovery, and a 2026-06-29 public deep-capture
  transcript diagnostic; see the Social networks table). The only other social probe is the
  LinkedIn *policy* boundary. Social surfaces carry the heaviest ToS/auth-wall/anti-bot posture
  (entitlement gate, Pattern 4, applies before any technical attempt). Full durable media/video
  preservation is still unprobed for IG; the deep-capture diagnostic proves only transient handle
  use for immediate ASR, not stored media bytes.

## Pending-merge / external (not on main; include before the doctrine finalizes)

- **Sephora/Bazaarvoice reviews finding** — worktree `orca-cloak-scroll-wt`, in squash `0faf262`, force-push pending. The single best **reviews** diagnosis (and the canonical "blocked was wrong" lesson).
- **Ulta Apollo embedded-JSON (DP-002)** — demand-projection lane worktree, unmerged. The single best **SPA-embedded-state** diagnosis.
- **OpenAI price payload (rung-1.5)** — `orca-rung15-wt`, unmerged. Best **pricing-embedded** diagnosis.
- **Operator-supplied / gitignored scratch** (evidence, not tracked): `docs/_inbox/data_capture_pressure_test_operator_supplied_2026_05_29/...`; `orca-harness/_test_runs/{cloakbrowser_api_probe,source_quality_slot3_*}/`.

## Non-claims

Not an authorization, not a build spec, not validation/readiness/acceptance, not legal
advice. Verdicts are as reported by each source doc. TikTok's first-slice route is no
longer absent, but scale reliability, sessioned detection ceiling, cross-creator
subtitle/transcript coverage, durable media/video, final product extraction, and
projection remain unproven. Parsed Funmi N30 batch packet admission is proven.
Worktree-resident findings are
