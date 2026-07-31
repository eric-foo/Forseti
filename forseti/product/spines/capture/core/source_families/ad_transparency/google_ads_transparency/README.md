# Capture Source Family: Google Ads Transparency Center

```yaml
retrieval_header_version: 1
artifact_role: Capture source-family lane index and recipe card
scope: >
  Cold-start route for public Google Ads Transparency Center advertiser
  inventory: exact-advertiser identity binding, bounded rendered capture, and
  deterministic source-native creative-ID projection with visible partiality.
use_when:
  - Capturing a company's observable Google Ads Transparency Center inventory.
  - Replaying or projecting a retained Google advertiser-inventory packet.
  - Deciding whether a Google transparency result can support a paid-creative claim.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_capture_return.md
  - docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_observed_creative_ids_20260726.json
  - forseti/product/spines/data_lake/README.md
stale_if:
  - Google changes advertiser URL grammar, advertiser identity markup, card aria labels, filters, or continuation behavior.
  - The generic CloakBrowser packet seam or Google projection CLI changes materially.
non_claims:
  - not validation, not readiness, not standing-capture authorization
  - not spend, targeting, delivery, performance, or complete creative-content evidence
```

## Route Card

| Field | Value |
| --- | --- |
| **source** | Google Ads Transparency Center, `adstransparency.google.com` |
| **access class observed** | Public, logged-out advertiser inventory. Some age-restricted ads may require sign-in; that notice is a coverage limit, not proof that a named advertiser has hidden ads. |
| **substrate** | JS-rendered application. Creative IDs and card positions live in rendered DOM attributes; direct HTTP and visible text are insufficient for enumeration. |
| **capture seam** | `run_source_capture_cloakbrowser_packet.py`; no Google-specific browser stack. |
| **projection seam** | `run_google_ads_transparency_projection.py`; local and network-free after packet capture. |
| **identity anchor** | Exact advertiser URL `/advertiser/<AR_ID>?region=<CC>` plus the source-rendered advertiser/legal name in the same DOM. A company-domain search is discovery only because one domain can surface multiple advertisers. |
| **creative anchor** | Exact-advertiser card links with `creative/<CR_ID>` and source `Advertisement (position of denominator)` labels. That denominator grows with rendered continuation depth; it is not the full source inventory total. |
| **completeness posture** | `PARTIAL` / source exhaustion `NOT_PROVEN` unless a later route proves a source-visible terminal state. The rounded header, rendered card positions, and distinct creative IDs are different counts and remain separate. |

## Cold-Start Procedure

### 1. Resolve the advertiser before capture

1. Start at `https://adstransparency.google.com/?region=US`.
2. Search the company-owned domain only to discover candidate advertisers.
3. Open the candidate and bind the source-rendered legal/advertiser name and
   exact `AR...` advertiser ID. Reject shared-domain candidates that do not
   match the company identity authority.
4. Freeze the exact advertiser locator and `region=US`. Keep `Any time`, `All
   platforms`, `All formats`, and source-default order for this v1 route.

### 2. Capture one bounded advertiser inventory

PowerShell:

```powershell
python forseti-harness/runners/run_source_capture_cloakbrowser_packet.py `
  --url 'https://adstransparency.google.com/advertiser/<AR_ID>?region=US' `
  --source-family 'google_ads_transparency_center' `
  --source-surface 'Google Ads Transparency Center advertiser inventory' `
  --decision-question 'What source-native creative IDs are visible for <LEGAL_NAME> under the recorded US/all-time/all-platform/all-format state?' `
  --data-root '<lake-root>' `
  --settle-seconds 8 --scroll-passes 10 --wait-until load `
  --timeout-seconds 60 --max-artifact-bytes 40000000 `
  --limitation 'Bounded to 10 continuation actions; source exhaustion is not proven.' `
  --warning 'Public source visibility only; no spend, targeting, delivery, performance, or strategy inference.'
```

Use a human-rate, single-advertiser run. If the surface requires authentication
and no entitled session exists, or presents a challenge, stop for owner
handling. Do not bypass it.

### 3. Project the retained packet

```powershell
python forseti-harness/runners/run_google_ads_transparency_projection.py `
  --packet-id '<PACKET_ID>' --data-root '<lake-root>' `
  --advertiser-name '<SOURCE-RENDERED LEGAL NAME>' `
  --advertiser-id '<AR_ID>' --region US `
  --output '<projection.json>'
```

The projector fails closed when the packet family/surface, exact locator,
rendered advertiser name, source filters, retained-file hashes, metadata final
URL, or creative-card anchors do not agree. It deduplicates creative IDs by
first DOM occurrence while retaining every source card position associated
with each ID. Re-running the same packet produces byte-identical UTF-8 JSON.

## Safe Use

The projection supports:

- verified advertiser-bound inventory enumeration for the retained packet;
- source-native creative-ID joins and direct-detail locators;
- rounded source header, rendered card-position denominator/count, and
  creative-ID reuse;
- exact packet, manifest, DOM, metadata, capture-time, and hash provenance.

It does not support:

- spend, budget, delivery, reach, impressions, targeting, performance, or
  strategy;
- serving placement inferred from format or aspect ratio;
- complete copy, media, destination, product, collaboration, or offer fields;
- source exhaustion, all ads, or absence outside the exact
  advertiser/region/date/platform/format state.

## Probe And Dogfood Receipt

Summer Fridays first probe, 2026-07-26:

- verified advertiser `Summer Fridays, LLC`,
  `AR00430838150965755905`, region `US`;
- packet `01KYF2MS14047RNMVTE3K5RZFA`;
- DOM SHA-256
  `3c6d8548be0e43ca43b9b07f799dd2f8f1cc62f3f52471d23c9fd31a3c689963`;
- 456 rendered source card positions, 416 distinct creative IDs after
  first-occurrence deduplication, 10 continuation actions;
- rounded source header `~500 ads`;
- source exhaustion not proven.

Fresh live dogfood, 2026-07-31: the same route with two continuation actions
produced packet `01KYVNYRMKW5DMF8ANGCFND3NP`, 160 rendered card positions,
and 120 distinct creative IDs while the header still displayed `~500 ads`.
This confirms that the card-label denominator grows with captured render depth
and must not be described as the source-declared inventory total.

The controlling capture return and full observed-ID projection are the two
research artifacts listed in `open_next`; this card does not replace their
dated evidence.
