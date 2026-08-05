# Soko Glam / Okendo Retail Review Capture Recon v0

```yaml
retrieval_header_version: 1
artifact_role: Bounded Retail/PDP capture recon record
scope: >
  Records the 2026-08-05 lower-rung replay of the frozen Soko Glam Dieux
  collection's six Okendo-backed product fixtures, its raw/runtime evidence,
  parity result, economics, capability boundary, and re-probe triggers.
use_when:
  - Reusing or challenging the tested Soko Glam Dieux/Okendo route.
  - Distinguishing fixture-level capture proof from retailer-, template-, or brand-wide reliability.
authority_boundary: retrieval_only; evidence ledger, not live-capture authorization or a production route contract
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md
stale_if:
  - A tested PDP no longer exposes the same public Okendo configuration or response shape.
  - Any of the six provider product IDs, collection membership, response fields, or pagination semantics changes.
  - A cross-brand or cross-template replay establishes a broader or conflicting capability boundary.
```

## Decision

`GO_BOUNDED_SOKOGLAM_DIEUX_OKENDO_FIXTURE`.

Capture-proven for the public Soko Glam Dieux collection's six Okendo-backed
product fixtures under the tested route and observation date; cross-brand,
cross-template, and future-cadence durability remain unproven.

The cheapest complete route is Direct HTTP for the served collection and PDP
HTML plus one public, page-owned Okendo `limit=100` response per product. The
PDPs expose the subscriber ID, provider product ID, first five rows, aggregate,
source-native review IDs, and their own next-response URL. The same exposed
route accepted a bounded `limit=100` request and returned each tested product's
complete declared corpus in one response. No browser, cookie, credential,
authentication bypass, CAPTCHA handling, or manual interaction was used.

## Evidence and currentness

- Frozen oracle: `C:\tmp\forseti-dieux-sokoglam-retailer-corpus-20260805`.
- Replay root: `C:\tmp\forseti-sokoglam-okendo-lower-rung-calibration-20260805`.
- Replay observation: Direct HTTP documents were fetched from approximately
  `2026-08-05T10:42:23Z` through `10:42:28Z`; the six complete Okendo responses
  were fetched from approximately `10:44:21Z` through `10:44:26Z`.
- Replay manifest: `manifest.json`, SHA-256
  `97ffa9da5e2c9d591b08d0e1eef1020d95b531c9fe76a3dd516188ec634812eb`;
  57 listed files, all byte counts and hashes re-read successfully.
- Capture receipt: `capture_receipt.json`, SHA-256
  `65dd6751ebffc02c70ea3bf9777bfd1ac82fe0ef9bd1df6aa3826472651ef6a3`.
- Mechanical projection: `projection/reviews_projection.json`, SHA-256
  `599a338796c83d402e2e3b03b4a31069aa299f0cdf77a33bdda73479341ab987`.
- Reconciliation: `projection/reconciliation.json`, SHA-256
  `ad9d2dc9b2e6c78ef8666b5f8913cd39b0cb7ee2f63e715b99da4b39d642e420`.

The runtime root is machine-local evidence, not repository authority. Raw
served HTML and Okendo JSON remain canonical. `rebuild_projection.py` performs
an offline-only mechanical projection; a second run under a socket-denying
Python audit hook produced byte-identical hashes for all five primary outputs.
No production capture code changed and no capture-time Projection packet was
introduced.

One required-read path in the commission,
`retail_pdp_projection_contract_v0.md`, does not exist at the required revision:
commit `bc1f33023b7e969277636dfc3d851e3b78fcf97e` deleted it on 2026-07-20 when
post-hoc Capture Projection was retired. The current
`retail_pdp_content_cleaning_contract_v0.md` was used as its canonical successor.

## Route ladder and measured verdict

| Route | Requests / loads | Status and block posture | Bytes | Wall clock | Manual interactions | Verdict |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| Direct HTTP collection + six PDPs | 7 HTTP document fetches, 0 browser loads | Seven `200`; no challenge or block | 3,695,582 | 4.451 s | 0 | `PARTIAL_ALONE`: product/config/aggregate and first five rows; three corpora exceed five. |
| Public page-owned Okendo response | 6 HTTP API fetches | Six `200`; no auth, challenge, cookie, or next page | 111,896 | 3.148 s | 0 | `COMPLETE`: 77 source-native rows and required fields. |
| Headless rendered browser | not run | Lower route was complete | — | — | — | stopped before escalation |
| Headed browser | not run | No mismatch needed a control | — | — | — | stopped before escalation |

The winning replay therefore cost 13 requests, 3,807,478 bytes, 7.599 seconds
of summed request wall time, zero browser page loads, and zero manual
interactions. The frozen rendered-Chrome capture's observed interval was
180.748 seconds across the collection and six PDPs; its manual-interaction
count was not recorded, so no fabricated click count is compared.

A preserved diagnostic batch under `okendo_api_failed_pid_collision/` sent six
wrong product IDs because a local PowerShell `$PID` variable was mistakenly
reused. Those `200`/40-byte empty responses are a tooling failure, not source
evidence. The corrected batch was run once and is the only batch used for the
verdict.

## Frozen recomputation

The frozen oracle's three core hashes and every one of its 22 manifest-listed
files passed byte/hash verification before use. Recomputed facts were: six
products; 77 declared reviews; 77 captured rows; 77 bodies; 58 verified buyers;
ratings `1★=4, 2★=2, 3★=2, 4★=9, 5★=60`; six explicit "do not recommend"
rows; zero observed helpful-yes and helpful-no votes; observation interval
`2026-08-05T09:30:52.532Z` through `2026-08-05T09:33:53.280Z`.

Source-native review UUIDs were recovered from the frozen Okendo helpful-vote
anchors. All 77 were unique; ordinal was used only to bind each UUID back to
the already ordered frozen row, never as identity.

## Six-fixture parity

| Fixture | Frozen | Live | Frozen recovered | Removed | Added | Edited | Extraction misses | Duplicates | Live rating distribution | Verified | Do not recommend |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Instant Angel | 32 | 32 | 32 | 0 | 0 | 0 | 0 | 0 | `1★=3, 2★=2, 3★=2, 4★=2, 5★=23` | 20 | 5 |
| Baptism | 4 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | `5★=4` | 4 | 0 |
| Forever Eye Masks | 15 | 15 | 15 | 0 | 0 | 0 | 0 | 0 | `4★=5, 5★=10` | 12 | 0 |
| Air Angel | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | `5★=3` | 2 | 0 |
| Auracle | 13 | 13 | 13 | 0 | 0 | 0 | 0 | 0 | `4★=2, 5★=11` | 12 | 0 |
| Deliverance | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | `1★=1, 5★=9` | 8 | 1 |
| **Total** | **77** | **77** | **77** | **0** | **0** | **0** | **0** | **0** | `1★=4, 2★=2, 3★=2, 4★=9, 5★=60` | **58** | **6** |

There was no live source drift during this replay. Seven apparent text
mismatches were only frozen rendered-DOM paragraph boundaries collapsed without
a space; whitespace-insensitive comparison was byte-content equivalent. One
Auracle body was visibly ellipsis-truncated in the frozen rendered DOM and was
complete in the source-native API. These are recorded transformations and a
recovered frozen-capture limitation, not edits or extraction losses.

## Projection and field posture

Each projected row preserves product name and canonical URL; Okendo review UUID;
rating/scale; verbatim title and body; displayed reviewer; exact source-created
datetime plus capture timestamp; verified label when exposed; recommendation;
reviewer skin-type/age attributes; retailer reply; helpful yes/no; provider
product ID; raw JSON pointer; and typed residuals for absent optional fields.
The public response exposes a more precise source datetime than the PDP's
relative display label. Raw remains canonical.

Eight rows expose `externalProvider=shopify-shop`; 69 expose no external-provider
field. No exact duplicate bodies occur inside the 77-row fixture. An imported or
syndicated review seen at another retailer remains one evidence origin, not
independent recurrence; this replay establishes no cross-retailer independence.

## Competitive-intelligence value

This bounded route makes source-native retailer review language cheap enough to
compare with other retailer origins. Independent recurrence can strengthen a
pain/delight hypothesis; contradictions can reveal channel or segment
conditions; explicit verified-buyer labels add behavior context; assortment and
availability reveal channel positioning; and provider diversity reduces
single-platform capture bias. Counts remain fixture observations, never
population prevalence.

## Residuals, non-claims, and re-probe triggers

- The public response's acceptance of `limit=100` is observed only for six
  corpora whose largest denominator is 32. Pagination beyond 100 is untested.
- Cross-brand, cross-template, collection-change, and future-cadence durability
  are unproven. This is not a claim that Soko Glam is reliably capturable.
- Review visibility/moderation policy, deletions, edits, and new provider fields
  may change independently of transport success.
- Re-probe if the subscriber/product IDs disappear or conflict, any response is
  challenged/non-`200`, `reviewsNextUrl` returns, the response count disagrees
  with the source aggregate, required fields disappear, or identity/field
  reconciliation reports unexplained loss.
- Do not infer demand, prevalence, authenticity, sentiment, buyer proof, source-
  wide completeness, or a complete Dieux catalog from this fixture.
- Future Phase A remains hero-product-first; this six-product replay was the
  promotion test for frozen evidence, not a standing full-catalog requirement.

## Direction change propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    The existing recon ledger now records a fixture-bounded Soko Glam Dieux/Okendo
    direct-HTTP capability pin; no general capture method or production route changed.
  trigger: product_doctrine
  controlling_sources_updated:
    - forseti/product/spines/capture/core/source_families/retail_pdp/sokoglam_okendo_retail_review_capture_recon_v0.md
    - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  downstream_surfaces_checked:
    - forseti/product/spines/capture/core/source_families/retail_pdp/README.md
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_site_registry_v0.md
  intentionally_not_updated:
    - path: forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
      reason: The winning composite is already covered by direct HTTP plus a public page-owned vendor/internal response route.
    - path: forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_site_registry_v0.md
      reason: Soko Glam is outside that fragrance-specific operating set.
  stale_language_search: >
    rg -n -i "Soko Glam|SokoGlam|Okendo|Soko.*captur|Okendo.*captur"
    forseti/product/spines/capture docs .agents
  non_claims:
    - not production-route validation
    - not retailer-wide reliability
    - not cross-brand or cross-template proof
    - not buyer proof or population prevalence
```
