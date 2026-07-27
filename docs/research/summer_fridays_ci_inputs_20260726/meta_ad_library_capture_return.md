# Summer Fridays Meta Ad Library Capture Return — 2026-07-26

```yaml
retrieval_header_version: 1
artifact_role: Acquisition capture return
scope: >
  Typed inventory and provenance record of the first Summer Fridays Meta Ad
  Library acquisition under the 2026-07-26 capture handoff: verified advertiser
  identity, bounded page-scoped enumeration (PARTIAL), creative/message
  clusters, product-family coverage, and route recipe evidence.
use_when:
  - Consuming Summer Fridays Meta paid-creative evidence in a later Deliver run.
  - Reusing or extending the Meta Ad Library capture route.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/handoffs/summer_fridays_meta_ad_library_capture_handoff_20260726_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
stale_if:
  - Meta materially changes Ad Library access, filters, or result fields.
  - A dedicated Meta Ad Library recipe card or runner supersedes this first probe.
  - The Summer Fridays portfolio authority is superseded for family normalization.
```

## 1. Executive Acquisition Conclusion

Route verdict **GO, enumeration PARTIAL**. The Meta Ad Library is publicly
viewable logged-out; the verified Summer Fridays page (`1898638280462729`,
alias `summerfridaysbeauty`) had a source-declared **~200 active-ad surface**
under `country=US`, all ad types, active-only. Four packets were admitted:
first-party identity, page identity, initial ad state (22 unique library IDs),
and scroll-continued ad state (**99 unique library IDs** after 8 of the 10
permitted continuation actions). Per the handoff cap, **60 unique ads were
typed** in observed order; 39 retained IDs remain raw-preserved but untyped.

Observed paid posture at capture time: heavy lip-franchise rotation (Lip
Butter Balm flavors, Flushed Lip Stain restock, lip kits/sets), one SPF/bundle
push, one subscription-program ad, one creator-partnership ad ("JADE LILY with
Summer Fridays"), and **all 60 typed destinations on `summerfridays.com`** —
no observed Sephora/Amazon/retailer destination in the typed set. The 8/6 body
launch families (Body Butter Balm, Body Fragrance Mist) had **no observed
active creative** on the captured surface (bounded claim; see §8 and §11).

## 2. Route Verdict And Recipe-Card Section

- **Step 0 access class:** publicly-viewable (logged-out). A "Log in" nav item
  is present but does not gate the result surface. The `facebook.com/<alias>`
  page render carries a login nag while page content remains visible.
- **Step 1 substrate:** JS-rendered SPA. Result cards live in rendered DOM;
  the page's own `POST /api/graphql/` calls carry typeahead and result data.
  Direct HTTP to `facebook.com/summerfridaysbeauty` returns **400** (route
  evidence, not a content block). `summerfridays.com` serves static HTML to
  direct HTTP (200).
- **Step 2 routes used, cheapest-first:**
  1. direct-HTTP (`run_source_capture_http_packet.py`) — company-site identity
     packet;
  2. real browser headless (`run_source_capture_browser_packet.py`,
     `--settle-seconds 10`) — initial ad state, 22 cards; page identity render;
  3. progressive scroll via `run_source_capture_cloakbrowser_packet.py`
     (`--scroll-passes 8 --settle-seconds 10`) — escalated on the observed
     symptom that continuation requires scroll, which the plain browser runner
     does not implement. No proxy profile; no session; human-rate.
- **Identity resolution recipe:** the Ad Library search box typeahead fires a
  GraphQL request whose response exposes `page_id`, `page_alias`, verification,
  likes, and linked `ig_username` per candidate — the cheapest advertiser-
  disambiguation surface found (observed in diagnosis; see §9 ledger).
- **Enumeration recipe:** page-scoped URL
  `.../ads/library/?active_status=active&ad_type=all&country=US&view_all_page_id=<id>&search_type=page&media_type=all`;
  Facebook rewrites the final URL to `sort_data[mode]=total_impressions`,
  `sort_data[direction]=desc`, `is_targeted_country=false` — recorded as the
  source-declared default sort state, not chosen by this run.
- **Field extraction recipe:** visible-text card blocks are anchored by
  `Library ID: <n>` lines (strip zero-width characters); destination URLs are
  `l.facebook.com/l.php?u=` wrappers per card in DOM order (strip
  `utm_*`/`fbclid`/`bc_*` params). Platform placement indicators are icon-only
  with **no accessible names** — not extractable from this surface (§9).

## 3. Capture-Parameter Receipt And Enumeration Ceiling

| Parameter | Frozen value |
| --- | --- |
| Advertiser | page `1898638280462729`, alias `summerfridaysbeauty`, name "Summer Fridays" |
| Country/market | `country=US`; `is_targeted_country=false` (source-added) |
| Category / ad type | `ad_type=all`, `media_type=all` |
| Status filter | `active_status=active` (active-only; US surface exposes no inactive non-political ads) |
| Sort | source default; rewritten by Meta to `total_impressions desc` |
| Session posture | logged-out; no cookies/profile/proxy |
| Capture window | 2026-07-26 11:37:39 – 11:40:39 (+08:00 local machine time) |
| Declared surface | "~200 results" (visible declaration; exhaustion signal **not** observed) |
| Continuation actions | 8 scroll passes of 10 permitted |
| Unique IDs retained | 99 (P3) ∪ 22 (P2) = 99 (P2 ⊂ P3) |
| Typed inventory cap | 60 unique library IDs, observed order; 39 retained untyped |
| Verdict | **PARTIAL** — typed 60 < retained 99 < declared ~200 |

## 4. Advertiser-Identity Proof

Three admitted legs plus one diagnostic observation:

1. **Company site → alias** (P1): `summerfridays.com` HTML declares
   `facebook.com/summerfridaysbeauty` and `instagram.com/summerfridays`.
2. **Alias → page_id** (P4): the logged-out render of
   `facebook.com/summerfridaysbeauty` shows name "Summer Fridays", "Page ·
   Health/beauty", `hello@summerfridays.com`, `summerfridays.com`, and the
   rendered DOM contains `1898638280462729`.
3. **page_id → ad surface** (P2/P3): the page-scoped Ad Library URL renders
   advertiser "Summer Fridays" ads for that page_id.
4. *Diagnostic (unadmitted):* the typeahead GraphQL response bound
   `page_id 1898638280462729` ↔ alias `summerfridaysbeauty` ↔
   `ig_username summerfridays` (IG-verified, ~1.46M followers) in one record.

**Rejected ambiguities** (typeahead candidates, name collisions): a stylized
"𝐒𝐮𝐦𝐦𝐞𝐫 𝐅𝐫𝐢𝐝𝐚𝐲𝐬" page (6 likes, no alias), "Summer Fridays Photography",
"Summer VIBE Fridays SOHO" (pub), "Summer Crush Fridays at The Standard"
(nightclub), two Ibiza concert pages, and one unrelated IG ads identity. None
carries the company alias, domain, or category; all rejected.

## 5. Unique-Ad Inventory (typed 60)

Full row data: `derived/meta_ads_typed_rows.json` in the raw lake (fields:
library_id, status, started_running_on, multiple_versions,
creative_reuse_count, advertiser, media, video_duration, body, headline,
description, cta, destination_url_canonical, also_in_initial_packet). Summary:

- 60/60 status **Active**; start dates 2026-03-10 → 2026-07-15.
- Advertiser: 59 "Summer Fridays"; 1 "JADE LILY with Summer Fridays".
- CTA: 59 "Shop Now"; 1 none-visible (the JADE LILY partnership card).
- Media: 12 video (durations 0:06–2:35 visible); 48 not source-stated in the
  text layer (static/carousel not distinguishable without opening detail views).
- Destinations: 60/60 bound; **all on `summerfridays.com`** — 44 product/
  collection/pages URLs, 16 Black Crow personalization storefront URLs
  (`/apps/blackcrow/storefronts/crowlink/<uuid>` with `bc_source`/`bc_campaign`/
  `bc_adid` macros) — a source-visible ad-tech mechanic (Black Crow AI).
- 22 of the 60 also appear in the independent initial render (P2), giving a
  two-render stability cross-check.

## 6. Creative/Message Clusters (19 distinct creatives across 60 ads)

| Cluster (headline) | Ads | Earliest start | Product typing (see §7) |
| --- | ---: | --- | --- |
| Sunlit Summer Essentials | 10 | 2026-06-29 | bundle: ShadeDrops SPF 50 + Lip Butter Balm Vanilla + Sunlit Vanilla EdP travel |
| NEW Strawberry Soft Serve | 7 | 2026-07-07 | Lip Butter Balm (new flavor, ad-declared) |
| Dewy Travel Trio is Back | 5 | 2026-06-18 | bundle (authority-listed) |
| Essential Lip Kit is BACK | 5 | 2026-06-19 | kit: Flushed Lip Stain + SoftLine Lip Liner + Lip Butter Balm + pouch (kit name not in p10 authority) |
| Lip Stains are Back | 5 | 2026-06-22 | Flushed Lip Stain |
| Back in Stock | 4 | 2026-06-22 | Flushed Lip Stain |
| Limited-Edition Lip Set | 4 | 2026-07-07 | Summer Fruits Set (authority-listed) |
| Summer Essentials Pouch | 4 | 2026-06-30 | Summer Essentials Terry Pouch (merch-with-samples) |
| NEW! Sweet Summer Minis | 3 | 2026-07-02 | bundle (authority-listed; Lip Butter Balm minis) |
| CC Me Serum with Vitamin C + Niacinamide | 2 | 2026-03-10 | CC Me Serum |
| The Essentials Trio | 2 | 2026-05-14 | set `skincare-essentials-trio` (name not in p10 authority) |
| NEW! Neapolitan Lip Trio | 2 | 2026-07-07 | The Neapolitan Lip Trio (authority-listed) |
| Subscribe + Save | 1 | 2026-05-28 | brand-only; subscription program, 15% off |
| NEW! Jumbo Pack: 15 Pairs | 1 | 2026-07-13 | Jet Lag Eye Patches (jumbo pack) |
| NEW! ShadeDrops SPF 50 | 1 | 2026-06-26 | ShadeDrops SPF 50 |
| Lip Butter Balm Vanilla | 1 | 2026-06-03 | Lip Butter Balm |
| JADE LILY | 1 | 2026-07-15 | Flushed Lip Stain (Mocha/Maple; creator partnership, "ad" disclosure) |
| NEW! Toasted Marshmallow | 1 | 2026-07-13 | Lip Butter Balm (limited-edition flavor) |
| The Nighttime Routine | 1 | 2026-06-03 | bundle (authority-listed) |

Message texture: restock ("BACK", "Back in Stock"), newness ("NEW!"),
limited-edition flavor drops, value bundles with strikethrough-style pricing
("$75 ($92 value)"), evergreen brand copy ("Vegan, cruelty-free skincare in
recyclable packaging…"), and one subscription-economics ad. Counts are
observed-card counts, never spend or emphasis weights.

## 7. Product-Family Coverage Matrix

Normalized against the freshly read p10 CO1 family authority (34 families; 27
current/exposed). "Observed" means the family name appears in a typed row or
in the retained card text of P2/P3 (99+22 cards scanned, wider than the typed
60).

**Families with observed active creative:** Lip Butter Balm; Flushed Lip
Stain; SoftLine Lip Liner (kit component); Jet Lag Eye Patches; CC Me Serum;
ShadeDrops SPF 50; Sunlit Vanilla Eau de Parfum (bundle component); Cloud Dew
(single retained-text mention).

**Families with no observed active creative on the captured surface** (18 of
27 current/exposed): Babymoon Belly Balm; Gentle Reset Daily Exfoliating Pads;
Heavenly Sixteen All-In-One Face Oil*; Jet Lag Deep Hydration Serum; Jet Lag
Mask; Jet Lag Overnight Eye Serum; Jet Lag Skin Soothing Hydration Mist; Light
Aura Eye Cream; Pink Dew Gel Cleanser†; Rich Cushion Cream; Blush Butter Balm;
Bronzer Butter Balm; Bronzing Drops; Dream Lip Oil; Illuminating Drops; Sheer
Skin Tint; Body Butter Balm; Body Fragrance Mist; Midnight Ritual Retinol.

For each such family the exact bounded phrase applies: **"No active Summer
Fridays commercial creative was observed on the captured Meta Ad Library
surface under the recorded market/filter/window."** This is additionally
bounded by the PARTIAL ceiling: ~101 of ~200 declared results were never
rendered, so absence here is absence from the captured subset, not from the
full declared surface.

\* Heavenly Sixteen appeared in an **unadmitted diagnostic render** under a
different sort state but in neither admitted packet — see §9.
† Pink Dew matched retained text only inside "Dewy"-bundle copy
("The Dewy Pink Set" context was not present; the two mentions are bundle
descriptions naming Pink Dew Gel Cleanser as a component), so it is typed as
bundle-component-only, not standalone creative.

Notable for Deliver: the **2026-08-06 body-launch families carry no observed
Meta air cover** in this window on the captured subset, while lip franchises
dominate observed rotation.

## 8. Failure / Omission Ledger

1. **PARTIAL enumeration:** ~200 declared vs 99 retained vs 60 typed; no
   exhaustion signal observed; 39 retained IDs untyped (listed in
   `derived/meta_ads_typed_rows.json` under `overflow_library_ids`).
2. **Platform/placement fields not extractable:** icon-only, no accessible
   names in DOM; absence of a placement label is unknown, not unused.
3. **Per-ad detail panes not opened:** "See ad details/summary details" modals
   (which may expose platform lists, versions, EU fields) were outside the
   bounded run; all fields come from the card surface.
4. **Media not durably preserved:** viewport screenshots only; video/image
   assets were not downloaded; 48 rows have unstated media type.
5. **Direct-HTTP 400** on `facebook.com/summerfridaysbeauty` (route evidence).
6. **Runner metadata gap:** P3 `scroll_passes_completed` is empty /
   `before_scroll_steps_completed=false` in snapshot metadata although 99
   cards render (the scroll clearly fired); recorded as a harness metadata
   defect, not a capture defect.
7. **Sort not operator-chosen:** Meta rewrote sort to `total_impressions`;
   composition under other sorts was not captured (see Heavenly Sixteen, §9).
8. **US surface limits:** active-only; no spend/reach/demographics/targeting
   fields exist on this surface for non-political ads.
9. **Coverage ceiling — independent creator pages:** partnership ads in the
   paired byline format ("X with Summer Fridays") do appear page-scoped (one
   observed); branded-content ads run solely from a creator's own page would
   not. Keyword-scoped enumeration was not commissioned.

## 9. Misleading Matches And Diagnostic-Only Observations

- The **keyword** search `"summer fridays"` (~1,400 results) is dominated by
  unrelated advertisers (Whatnot, Amazon, venues) matching the phrase — do not
  use keyword counts for brand claims.
- **Heavenly Sixteen All-In-One Face Oil** and several "SUMMERFRIDAYS.COM
  domain-card" creatives were observed in the diagnostic pane render (default
  relevancy sort) but are absent from both admitted packets (impressions-sort
  renders). Composition is sort-dependent; treat any single render as one
  observed state.
- The typeahead GraphQL identity record (§4.4) was observed in diagnosis but
  not admitted as a packet; identity claims rest on the three admitted legs.

## 10. Source Packet Bundle

Raw lake: `C:\tmp\forseti-sf-meta-ads-discovery-20260726\data` (epoch v4.1;
packets under `raw/`, manifests+receipts per packet).

**Co-resident packets from a parallel receiver (correction + purge).** At
capture time the lake was NOT empty: a separate receiver lane accidentally
wrote five packets into this root at 11:01–11:05 (+08:00), ~30 minutes before
this run (session IDs `sf-meta-*-20260726`, operator `research`). This run's
earlier statement that the lake was "initialized this run" was wrong — the
parallel lane initialized it, and this run's `DataLakeRoot.initialize`
verified the existing markers idempotently. No packet was overwritten
(ULID-unique directories). On owner direction (2026-07-26, same session), the
five foreign packets and their availability-index entries were **purged from
the lake**; the lake now contains only this run's nine packets. Their
inventory is preserved here as the purge record:

| Packet ID | Surface | Capture (+08:00) |
| --- | --- | --- |
| `01KYF1CHHG7X5JGHP0CPH0ZCAY` | Ad Library keyword search (US active) | 11:01:27 |
| `01KYF1EJBRGRZK5PMMND4N9F3C` | summerfridays.com homepage | 11:02:34 |
| `01KYF1H1PFWC53Z2XM2BDJMZ2B` | Ad Library page search (US active) | 11:03:55 |
| `01KYF1J1HPM3J2HK44AHC22AV6` | facebook.com/summerfridaysbeauty page | 11:04:27 |
| `01KYF1KWVQZR4ZN4NZVE8DZJ0R` | Ad Library page-scoped inventory (US active, same `view_all_page_id=1898638280462729`) | 11:05:28 |

Before the purge, the parallel lane's packets independently resolved the same
advertiser page ID — noted as an unplanned cross-receiver observation of §4,
now historical only (the underlying packets no longer exist in this lake).

| # | Packet ID | Surface | Capture time (+08:00) | manifest SHA-256 |
| --- | --- | --- | --- | --- |
| P1 | `01KYF3ETJDH85G4VCKERPR0AX2` | `summerfridays.com` homepage (direct HTTP) | 2026-07-26 11:37:39 | `0925be5db61f1ff988a1a46e295f71ae085b1a87402d649805defc747567f1dc` |
| P2 | `01KYF3FW49NDWKZQ6V9JDF1C8X` | Ad Library page-scoped, initial render (22 IDs) | 2026-07-26 11:38:14 | `4922f01d950cd984c88e82c7b0f267fcd9b29288cae502960c7874f95a56ff62` |
| P3 | `01KYF3JGKH4EF7C06QY9799A3K` | Ad Library page-scoped, 8-pass scrolled render (99 IDs) | 2026-07-26 11:39:40 | `c835462ebc52daa7206f1884750785e6d2d61c64b1c52f52cb59eef17921369b` |
| P4 | `01KYF3MAFCS8J9020VTHN5T5WN` | `facebook.com/summerfridaysbeauty` identity render | 2026-07-26 11:40:39 | `9d003165b0bb04fa2be3cf840aba8c5009f61401dce1d8c9ef8cbbedf20cd61d` |

Derived (non-packet) extraction: `derived/meta_ads_typed_rows.json` (typed 60
rows + 39 overflow IDs), produced deterministically from P2/P3 text and DOM by
the extraction script; regeneration requires only the retained packets.

Source URLs (canonical): the page-scoped Ad Library URL in §2; the alias page;
the company homepage. All capture parameters are in §3.

## 11. Non-Claims And Safe Deliver-Side Uses

**Non-claims.** No spend, budget, impressions (the sort label is Meta's, no
values are exposed), reach, targeting, audience, performance, conversion,
campaign objective, market priority, or executive intent. Active-only US
surface; one capture window; composition is sort- and render-dependent.
Family typing is family-level; SKU/variant only where the creative names it.
Absence rows use the exact bounded phrase in §7 and never mean "not spending."
The 39 untyped retained IDs and ~101 unrendered declared results mean **counts
here are floors of the observed subset, not totals**.

**Safe later joins (not performed here):** paid-claim vs organic-claim
comparison (which claims the company pays to amplify vs what community
sources say); paid destination routing (all-DTC in the typed set) vs retailer
review evidence; restock/launch messaging vs retailer availability; the
Black Crow personalization mechanic vs DTC funnel observations; the JADE LILY
partnership vs creator-signal evidence; body-launch air-cover timing vs the
8/6 launch narrative.

## 12. Owner-Commissioned Full-Corpus Extension (same day, 2026-07-26)

Commissioned directly in-session after the bounded run closed; caps lifted to
"visible exhaustion." Five further packets were admitted (raw truth only;
**typed projection of these packets is deliberately deferred** — the typed
inventory in §5–§7 still describes the original 60-row bounded run).

| # | Packet ID | Surface | Capture (+08:00) | manifest SHA-256 | Result |
| --- | --- | --- | --- | --- | --- |
| E1 | `01KYF4W3C4SJJYFFBCW6VNAX12` | US active, page-scoped, 25-pass exhaustion | 12:02:23 | `3017d8d5d9342223dddd8375930dc06817193a72f7f2bb729a001b82e3d515dc` | **185 unique library IDs**, footer-terminal state; "~200" declared was Meta rounding. One card carries a "Low impression count" label. |
| E2 | `01KYF4YWGV8HRM8AYCVE475MXP` | `country=DE`, `active_status=all` (DSA view) | 12:03:54 | `6798dcdca8b9a4db6eaee840da30e8743f399869a80427986a7e5b0d269de5d1` | **Empty**: "This advertiser isn't running ads in the selected country and ad category at this time." Params confirmed un-rewritten. |
| E3 | `01KYF514VR7SZ2R7Y6P0JXR4CW` | `country=DE` keyword `zalando` control | 12:05:08 | `e92ad938a4e680e6985065cd863cafec404929820ceed477c88192f88de62bde` | **Instrument GO**: >50,000 declared, 49 cards rendered, 43 Inactive with date ranges, per-card "EU transparency" sections. |
| E4 | `01KYF52WQXSNFZGAMGB5VS07JZ` | `country=FR`, `active_status=all`, 2-pass probe | 12:06:05 | `2af91b17cb54b2e7090b90d554fce711fa152a3b67d277df65da19b548af8dac` | **Positive**: 11 cards render — DE absence is country-specific reach, not EU-wide absence. |
| E5 | `01KYF55JPSJJ2HXM1YWQJC5YSD` | `country=FR`, `active_status=all`, 25-pass exhaustion | 12:07:33 | `88cb29c2f39e20ae1b0e8ad3334a028ad74c5c553348dd5fc49304cb4e482ae5` | 11 unique IDs of "~16" declared, footer-terminal; 7 Active, 4 Inactive with date ranges; 6 "EU transparency" sections. |

Extension findings (acquisition-level, raw-backed):

1. **US active corpus is now fully captured at the card level**: 185 unique
   library IDs, exhaustion observed. The §3 PARTIAL verdict is superseded at
   the card level by E1; grouped "N ads use this creative" versions and detail
   panes remain unexpanded (residual ceiling).
2. **EU/DSA view**: no Summer Fridays brand-page ads are viewable under
   `country=DE` (instrument-proven by E3), while `country=FR` exposes a small
   corpus (11 cards, ~1-year DSA retention, incl. inactive with date ranges).
   Absence phrasing per country: "No Summer Fridays ad creative was observed
   in the Meta Ad Library `country=<X>` all-status view at capture time."
3. **Channel-routing contrast (raw observation, not yet typed):** the FR
   creative is French-language and states "Uniquement disponible chez
   Sephora" — FR paid routes to the retailer, while all 60 typed US rows
   route DTC to `summerfridays.com`. High-leverage Deliver join.
4. Non-claims unchanged (§11); the EU view covers EU-reaching ads only, one
   country view at a time; a country-view absence is not "not spending."

## 13. Depth Probe And Market Extension (2026-07-26, later same session)

Three further packets close the two open depth/breadth questions.

| # | Packet ID | Surface | Result |
| --- | --- | --- | --- |
| E6 | `01KYFJ14GQR27Q8NZ6A0Z4SMX1` | single-ad permalink `?id=1175398888105507` | Empty under the run's geo/session ("No ads match") — permalink is viewer-geo-sensitive; the same URL rendered one card in a browser resolving to `country=SG`. |
| E7 | `01KYFJ24KS4NCVWWX82TQKYFGB` | permalink with `active_status=all` | Renders the page grid (23 cards), not an isolated ad — no URL-addressable per-ad detail route exists. |
| E8 | `01KYFK6EHXRCZ5C9VKTZ4APXGH` | `country=IT`, `active_status=all`, 25-pass exhaustion | **11 unique IDs** of "~16" declared, footer-terminal, 4 Inactive with date ranges, 6 EU-transparency sections. Captured by a cold receiver following only the route card. |

**Detail panes are a closed question — do not sweep them.** The "See ad
details" pane was opened live for Library ID `1175398888105507`. Every field it
shows is already in the grid card; the only addition is a version counter
(`1 of 5`). The version carousel does **not** advance under synthetic clicks or
full pointer-event sequences (pointerdown/mousedown/pointerup/click) — it
requires trusted input, which is the anti-bot boundary. The pane's DOM holds
only 3 unique creative images for that 5-version ad, so even DOM scraping gives
partial version coverage. Platform/placement icons carry no accessible names in
the pane either. No CAPTCHA was encountered. Cost/benefit is decisively
negative: ~30 human-rate interactions plus challenge risk for one integer
already implied by the card's "N ads use this creative" text.

**Per-market corpora are genuinely distinct.** IT (11 ads) and FR (11 ads)
share **zero library IDs**. Each EU country view is its own corpus, not a
re-slice of one EU set — so market breadth, not per-ad depth, is where
remaining value sits (~25 scroll passes per additional country).

Deferred (not performed): typed projection of E1/E5/E8 rows, EU countries
beyond DE/FR/IT, media-asset preservation.
