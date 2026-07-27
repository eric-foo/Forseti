# Summer Fridays Meta Ad Library Capture Return — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Capture return artifact
scope: >
  Bounded acquisition return for active Summer Fridays commercial creative
  visible on the public Meta Ad Library surface under the recorded United
  States, All ads, active-status, exact-advertiser-page parameters. Preserves
  the first 60 unique library IDs after identity binding and ten continuation
  actions, deduplicated creative records, product-family coverage, route
  failures, evidence bindings, and claim limits. Supplemental acquisition
  input for later Deliver-side competitive-intelligence work.
use_when:
  - Reading the first-60 Summer Fridays Meta Ad Library inventory captured on 2026-07-26.
  - Checking which creative, offer, and product-family signals were source-visible.
  - Planning a later cross-source join without re-running this capture.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/handoffs/summer_fridays_meta_ad_library_capture_handoff_20260726_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
stale_if:
  - Meta Ad Library filters, sorting, identity, card, or continuation behavior materially changes.
  - The exact advertiser page, portfolio authority, or raw lake is recaptured or superseded.
  - A dedicated Forseti Meta Ad Library recipe supersedes this first-probe route.
```

## 1. Executive acquisition conclusion

The public Meta Ad Library exact-page surface returned **about 200 active
results** for the independently bound Summer Fridays advertiser page under
United States / All ads / Active ads. Ten bounded scroll continuations exposed
**118 unique library IDs**. Per the handoff ceiling, this return enumerates the
**first 60 unique IDs** in the resolved source-default order and is therefore
**PARTIAL**, not an exhaustive advertiser inventory.

Those 60 IDs resolve to **29 deduplicated creative records**: 59 rows name
`Summer Fridays`; one names `JADE LILY with Summer Fridays` and carries explicit
creator/ad language. The retained window contains 48 static-image rows and 12
video rows. Repetition is substantial inside this window: the same creative
record appears under multiple unique library IDs, sometimes with Meta's
source-visible “multiple versions” or “N ads use this creative and text”
annotation. Those annotations are retained as source state and are not expanded
into inferred campaigns.

The strongest source-visible creative concentration is around limited or
seasonal lip and summer-set offers. That is a description of this capped,
default-ordered window only. It is not spend, performance, targeting, campaign
objective, market-priority, or strategy evidence.

## 2. Route and parameter receipt

- **Primary surface:** public anonymous Meta Ad Library.
- **Advertiser page:** `Summer Fridays`.
- **Exact page locator:** `https://www.facebook.com/summerfridaysbeauty/`.
- **Meta page ID:** `1898638280462729`.
- **Country/market filter:** `United States` / URL value `country=US`.
- **Commercial category:** `All ads` / URL value `ad_type=all`.
- **Status:** `Active ads` / URL value `active_status=active`.
- **Media filter:** `all`.
- **Target-country toggle:** `is_targeted_country=false`; this is a source
  parameter, not a claim about where any ad was delivered.
- **Search type:** exact advertiser page via `search_type=page` and
  `view_all_page_id=1898638280462729`.
- **Requested order:** source default. The retained final URL resolved this to
  `sort_data[mode]=total_impressions` and `sort_data[direction]=desc`. This
  source-supplied sort label does **not** expose impression counts.
- **Capture time:** `2026-07-26T11:05:28Z`.
- **Continuation ceiling:** ten automated scroll passes.
- **Observed surface size:** `~200 results`.
- **Exposed after the ceiling:** 118 unique library IDs.
- **Enumerated here:** first 60 unique IDs.
- **Status:** `PARTIAL` because the source showed more than the 60-row ceiling.
- **Session posture:** anonymous; no stored Meta login, cookies, profile, or
  paid-ad session.
- **Proxy posture:** none requested or loaded. No physical-US-local claim is
  made.

Exact retained URL:

`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=1898638280462729`

### Route non-claims

- `country=US` is a Meta filter, not proof of a physically US-local browser.
- “Active” is the library's capture-time label, not proof of continuous
  delivery, impressions, or spend.
- Source-default order is not performance rank or advertiser priority.
- About 200 source results does not mean 200 unique campaigns or creatives.
- The 118 exposed IDs and the first-60 window are not an exhaustive inventory.

## 3. Advertiser identity proof

Identity was bound before the exact-page inventory was accepted:

1. Company-owned packet `01KYF1EJBRGRZK5PMMND4N9F3C` retained the
   `summerfridays.com` homepage. Its footer directly links
   `http://facebook.com/summerfridaysbeauty`.
2. Public Meta Page packet `01KYF1J1HPM3J2HK44AHC22AV6` retained the vanity
   page `https://www.facebook.com/summerfridaysbeauty/`, visible name `Summer
   Fridays`, category `Health/beauty`, company-domain locator
   `summerfridays.com`, and Meta's underlying delegate-page ID
   `1898638280462729`.
3. Exact-page inventory packet `01KYF1KWVQZR4ZN4NZVE8DZJ0R` used that numeric
   page ID. Its header rendered `Summer Fridays`, `Ads`, United States, All ads,
   and Active ads.
4. The accepted creative cards link back to the same
   `facebook.com/summerfridaysbeauty` page and overwhelmingly land on
   `summerfridays.com`.

The earlier keyword probes are not identity authority. A bare `Summer Fridays`
keyword search returned about 1,400 results with many unrelated advertisers;
name matching alone was therefore rejected.

## 4. Inventory row contract and shared fields

Every row below inherits these source fields unless explicitly overridden:

- page identity/locator: `Summer Fridays`,
  `facebook.com/summerfridaysbeauty`, page ID `1898638280462729`;
- capture parameters/time: section 2;
- source status: `Active`;
- evidence pointer: packet `01KYF1KWVQZR4ZN4NZVE8DZJ0R`,
  `raw/02_cloakbrowser_visible_text.txt` plus the corresponding retained DOM;
- placement field: Meta rendered a source platform-icon set per card, but the
  retained visible text and DOM did not resolve those icons to stable textual
  platform labels. **Placement is therefore recorded as
  `source icons retained; labels not text-resolved` for all 60 rows.** No
  Facebook-versus-Instagram-versus-other placement claim is made.

`Creative` points to the deduplicated record in section 5, which carries body
copy, headline/landing label in source order, CTA, canonical destination,
format/media state, family binding, and offer language. Tracking parameters
were stripped from reported destinations; meaningful Shopify `variant`
parameters were retained. Source-linked media bytes were not independently
downloaded.

| # | Library ID | Started | Advertiser label | Creative |
|---:|---|---|---|---|
| 1 | `1175398888105507` | 29 Jun 2026 | Summer Fridays | C01 |
| 2 | `1643744106704060` | 18 Jun 2026 | Summer Fridays | C02 |
| 3 | `936688215440544` | 10 Mar 2026 | Summer Fridays | C03 |
| 4 | `27478943508382182` | 7 Jul 2026 | Summer Fridays | C04 |
| 5 | `1354103216642374` | 3 Jun 2026 | Summer Fridays | C05 |
| 6 | `1079543094415868` | 14 May 2026 | Summer Fridays | C06 |
| 7 | `1995557377753931` | 12 May 2026 | Summer Fridays | C05 |
| 8 | `1523144412489876` | 3 Jun 2026 | Summer Fridays | C05 |
| 9 | `2186209455493601` | 13 Jul 2026 | Summer Fridays | C07 |
| 10 | `3998893666911478` | 7 Jul 2026 | Summer Fridays | C08 |
| 11 | `2314307526189579` | 7 Jul 2026 | Summer Fridays | C04 |
| 12 | `1348437356636900` | 2 Jul 2026 | Summer Fridays | C09 |
| 13 | `3648060232000072` | 29 Jun 2026 | Summer Fridays | C01 |
| 14 | `1356852486340421` | 18 Jun 2026 | Summer Fridays | C02 |
| 15 | `911206448673863` | 14 Jul 2026 | Summer Fridays | C10 |
| 16 | `2144636779792062` | 7 Jul 2026 | Summer Fridays | C11 |
| 17 | `2187399302052086` | 30 Jun 2026 | Summer Fridays | C12 |
| 18 | `2171959403364171` | 7 Jul 2026 | Summer Fridays | C08 |
| 19 | `858385367029059` | 7 Jul 2026 | Summer Fridays | C04 |
| 20 | `2514332795685650` | 23 Jun 2026 | Summer Fridays | C13 |
| 21 | `1739759233835433` | 13 Jul 2026 | Summer Fridays | C14 |
| 22 | `2136306663605958` | 29 Jun 2026 | Summer Fridays | C15 |
| 23 | `1802387080560240` | 14 Jul 2026 | Summer Fridays | C10 |
| 24 | `1346486990753456` | 29 Jun 2026 | Summer Fridays | C15 |
| 25 | `889930200210931` | 7 Jul 2026 | Summer Fridays | C16 |
| 26 | `1865784317714042` | 29 Jun 2026 | Summer Fridays | C15 |
| 27 | `27874996442118410` | 19 Jun 2026 | Summer Fridays | C04 |
| 28 | `977706755055639` | 28 May 2026 | Summer Fridays | C17 |
| 29 | `1319388780302888` | 22 Jun 2026 | Summer Fridays | C18 |
| 30 | `1703660564116657` | 2 Jul 2026 | Summer Fridays | C19 |
| 31 | `1016042407839353` | 13 Jul 2026 | Summer Fridays | C20 |
| 32 | `4049000368733660` | 2 Jul 2026 | Summer Fridays | C19 |
| 33 | `2502925050155631` | 7 Jul 2026 | Summer Fridays | C16 |
| 34 | `2509310942878400` | 20 Jul 2026 | Summer Fridays | C21 |
| 35 | `1030178939943928` | 7 Jul 2026 | Summer Fridays | C04 |
| 36 | `1029701023319984` | 20 Jul 2026 | Summer Fridays | C01 |
| 37 | `2567191980366685` | 18 Jun 2026 | Summer Fridays | C02 |
| 38 | `1009076801898863` | 13 Jul 2026 | Summer Fridays | C22 |
| 39 | `1036690345420778` | 14 Jul 2026 | Summer Fridays | C10 |
| 40 | `2120467905178382` | 22 Jun 2026 | Summer Fridays | C13 |
| 41 | `1794571941529400` | 7 Jul 2026 | Summer Fridays | C23 |
| 42 | `1021549470370480` | 7 Jul 2026 | Summer Fridays | C08 |
| 43 | `1377410611271574` | 29 Jun 2026 | Summer Fridays | C01 |
| 44 | `1496739955533655` | 7 Jul 2026 | Summer Fridays | C24 |
| 45 | `2817328171962265` | 18 Jun 2026 | Summer Fridays | C02 |
| 46 | `2110208639841430` | 20 Jul 2026 | Summer Fridays | C21 |
| 47 | `934357659665182` | 7 Jul 2026 | Summer Fridays | C23 |
| 48 | `2221518491967774` | 14 Jul 2026 | Summer Fridays | C25 |
| 49 | `2491822771266461` | 30 Jun 2026 | Summer Fridays | C12 |
| 50 | `1011312561890157` | 13 Jul 2026 | Summer Fridays | C26 |
| 51 | `1614930776869359` | 26 Jun 2026 | Summer Fridays | C27 |
| 52 | `1902336790437623` | 14 Jul 2026 | Summer Fridays | C25 |
| 53 | `3695374633947514` | 7 Jul 2026 | Summer Fridays | C21 |
| 54 | `2510676656117995` | 22 Jun 2026 | Summer Fridays | C28 |
| 55 | `1523308379436521` | 30 Jun 2026 | Summer Fridays | C12 |
| 56 | `2404000430122820` | 13 Jul 2026 | Summer Fridays | C07 |
| 57 | `27496407443350705` | 7 Jul 2026 | Summer Fridays | C15 |
| 58 | `996817423340639` | 7 Jul 2026 | Summer Fridays | C24 |
| 59 | `1054551390359878` | 15 Jul 2026 | JADE LILY with Summer Fridays | C29 |
| 60 | `904391208641453` | 7 Jul 2026 | Summer Fridays | C21 |

## 5. Deduplicated creative catalog

Copy below is preserved in source order. The `⟂` separator marks a visible
line/field boundary; it does not join text that Meta represented as one field.

| Creative | IDs in window | Format / media state | Family binding | Offer / collaboration |
|---|---:|---|---|---|
| C01 | 4 | static image retained | Lip Butter Balm; ShadeDrops SPF 50; Sunlit Vanilla Eau de Parfum | free items; `$75 ($92 value)` |
| C02 | 4 | static image retained | bundle/set; named families not resolved in copy | back in stock; limited edition; `$44 ($55 value)` |
| C03 | 1 | static image retained | bundle/set; named families not resolved in copy | trio label only |
| C04 | 5 | static image retained | Flushed Lip Stain; SoftLine Lip Liner; Lip Butter Balm | back in stock; exclusive pouch; `$52 ($66 value)` |
| C05 | 3 | static image retained | Lip Butter Balm | none explicit |
| C06 | 1 | static image retained | CC Me Serum | none explicit |
| C07 | 2 | video; `0:38` source duration | Lip Butter Balm; ShadeDrops SPF 50; Sunlit Vanilla Eau de Parfum | free items; `$75 ($92 value)` |
| C08 | 3 | static image retained | Lip Butter Balm | new flavor/variant language |
| C09 | 1 | video; `0:06` source duration | bundle/set; named family not explicit in copy | limited edition; `$22`; while supplies last |
| C10 | 3 | static image retained | Flushed Lip Stain | back in stock |
| C11 | 1 | static image retained | bundle/set; named families not resolved in copy | trio label only |
| C12 | 3 | static image retained | merchandise-with-samples; named families not resolved | four samples |
| C13 | 2 | static image retained | Flushed Lip Stain | back in stock |
| C14 | 1 | static image retained | Lip Butter Balm | limited edition; new flavor/variant |
| C15 | 4 | static image retained | Lip Butter Balm; ShadeDrops SPF 50; Sunlit Vanilla Eau de Parfum | free items; `$75 ($92 value)` |
| C16 | 2 | static image retained | Lip Butter Balm | new flavor/variant language |
| C17 | 1 | static image retained | brand-wide | subscribe and save; `15% off` |
| C18 | 1 | static image retained | Flushed Lip Stain | back in stock |
| C19 | 2 | video; `0:09` source duration | Lip Butter Balm | limited edition; `$22`; while supplies last |
| C20 | 1 | video; `0:46` source duration | bundle/set; named families not resolved in copy | back in stock; limited edition; `$44 ($55 value)` |
| C21 | 4 | static image retained | Lip Butter Balm | limited edition; `$78 ($96 value)` |
| C22 | 1 | video; `0:22` source duration | merchandise-with-samples; named families not resolved | four samples |
| C23 | 2 | static image retained | Lip Butter Balm | limited edition; new flavor/variant |
| C24 | 2 | static image retained | Lip Butter Balm | limited edition; `$60 ($72 value)` |
| C25 | 2 | video; `0:49` source duration | Flushed Lip Stain | back in stock |
| C26 | 1 | static image retained | Jet Lag Eye Patches | new jumbo format; 15 pairs |
| C27 | 1 | video; `0:37` source duration | ShadeDrops SPF 50 Mineral Milk Sunscreen | new-product language |
| C28 | 1 | video; `0:08` source duration | Flushed Lip Stain | back in stock |
| C29 | 1 | video; `0:50` source duration | Flushed Lip Stain | advertiser label `JADE LILY with Summer Fridays`; `ad` disclosure |

### C01

- **Copy / headline:** For that endless summer feeling. Sunlit Summer
  Essentials includes ShadeDrops® SPF 50 Mineral Milk Sunscreen, Lip Butter
  Balm Vanilla and our travel size Sunlit Vanilla™ Eau de Parfum—plus a free
  Sunlit Mini Tote in Vanilla and On-The-Go Fragrance Keychain for $75 ($92
  value). ⟂ Sunlit Summer Essentials
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/sunlit-summer-essentials`

### C02

- **Copy / headline:** Back in stock: mini hydration essentials to take with
  you, wherever you are. This limited-edition set is perfect for on-the-go
  moments and effortless travel for $44 ($55 value). ⟂ Dewy Travel Trio is Back
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/dewy-travel-trio`

### C03

- **Copy / headline / landing label:** Vegan, cruelty-free skincare in
  recyclable packaging—to bring beauty, efficacy and simplicity to your daily
  routine. ⟂ SUMMERFRIDAYS.COM ⟂ The Essentials Trio ⟂ Shop the Summer Fridays
  skincare collection. View all products, including eye care, lip care, body
  care and makeup.
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/skincare-essentials-trio?variant=32278677815373`

### C04

- **Copy / headline:** Your everyday lip combo is back in stock. Choose your
  favorite shades of Flushed Lip Stain, SoftLine Lip Liner and Lip Butter
  Balm—plus, receive the exclusive Lip Combo Pouch in the color of your choice.
  For effortless reapplication wherever you are 💋 $52 ($66 value). ⟂ Essential
  Lip Kit is BACK
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/pages/essential-lip-kit`

### C05

- **Copy / headline / landing label:** Vegan, cruelty-free skincare in
  recyclable packaging—to bring beauty, efficacy and simplicity to your daily
  routine. ⟂ SUMMERFRIDAYS.COM ⟂ Lip Butter Balm Vanilla ⟂ Shop Summer Fridays
  skincare products. Our collection includes face masks, treatments and serums
  to leave your skin glowing, with vegan and clean ingredients.
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/lip-butter-balm?variant=39408922853453`

### C06

- **Copy / headline / landing label:** Vegan, cruelty-free skincare in
  recyclable packaging—to bring beauty, efficacy and simplicity to your daily
  routine. ⟂ SUMMERFRIDAYS.COM ⟂ CC Me Serum with Vitamin C + Niacinamide ⟂
  Shop Summer Fridays skincare products. Our collection includes face masks,
  treatments and serums to leave your skin glowing, with vegan and clean
  ingredients.
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/cc-me-serum?variant=28908339658829`

### C07

- **Copy / headline:** For that endless summer feeling. Sunlit Summer
  Essentials includes ShadeDrops® SPF 50 Mineral Milk Sunscreen, Lip Butter
  Balm Vanilla and our travel size Sunlit Vanilla™ Eau de Parfum—plus a free
  Sunlit Mini Tote in Vanilla and On-The-Go Fragrance Keychain for $75 ($92
  value). ⟂ Sunlit Summer Essentials
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/sunlit-summer-essentials`

### C08

- **Copy / headline:** A taste of summer in every swipe 🍓 Meet Lip Butter Balm
  Strawberry Soft Serve—our award-winning formula with a new creamy strawberry
  flavor and a baby pink tint. ⟂ NEW Strawberry Soft Serve
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/03d34cc1-c061-45f4-aa60-3d42b52831e4`

### C09

- **Copy / headline:** Limited-edition flavors inspired by your favorite summer
  treats. Our new Sweet Summer Minis feature three new shades: Peach Granita,
  Berry Sorbet and Sea Salt Caramel. Available for $22 while supplies last. ⟂
  NEW! Sweet Summer Minis
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/1f30b244-4f02-4fac-ab14-e88a79cdd515`

### C10

- **Copy / headline:** Flushed Lip Stain is finally back in stock. Lightweight,
  comfortable and made to last. Available in six shades for the perfect lip
  look. ⟂ Lip Stains are Back
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/flushed-lip-stain-almond`

### C11

- **Copy / headline / landing label:** Vegan, cruelty-free skincare in
  recyclable packaging—to bring beauty, efficacy and simplicity to your daily
  routine. ⟂ SUMMERFRIDAYS.COM ⟂ The Essentials Trio ⟂ Shop Summer Fridays
  skincare products. Our collection includes face masks, treatments and serums
  to leave your skin glowing, with vegan and clean ingredients.
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/skincare-essentials-trio?variant=32278677815373`

### C12

- **Copy / headline:** Made for wherever summer takes you. Discover our
  travel-ready terry pouch, designed to take your everyday favorites with you
  on the go, featuring four samples of summer essentials. ⟂ Summer Essentials
  Pouch
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/summer-essentials-terry-pouch`

### C13

- **Copy / headline:** Back in stock: Flushed Lip Stain 💋 Our weightless lip
  stain enhances your natural tone and lasts all day. Buildable,
  transfer-proof, effortless—just swipe and go. ⟂ Back in Stock
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/collections/flushed-lip-stains`

### C14

- **Copy / headline:** Lip care that feels like butter. Discover our
  limited-edition Lip Butter Balm Toasted Marshmallow—featuring golden shimmer,
  marshmallow sweetness and nourishing hydration in every swipe. ⟂ NEW! Toasted
  Marshmallow
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/85d86e01-2aff-4418-85b6-f79c3b0f72eb`

### C15

- **Copy / headline:** The summer set we’ll be taking with us everywhere—made
  for sweet, sun-warmed skin and buttery lips. ⟂ The set includes: ⟂ ☀️
  ShadeDrops® SPF 50 Mineral Milk Sunscreen ⟂ 🤍 Lip Butter Balm Vanilla ⟂ ✨
  Sunlit Vanilla™ Eau de Parfum Travel Size ⟂ 👜 Free Sunlit Mini Tote in
  Vanilla ⟂ 🔑 Free On-The-Go Fragrance Keychain ⟂ $75 ($92 value) ⟂ Sunlit
  Summer Essentials
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/sunlit-summer-essentials`

### C16

- **Copy / headline:** The same award-winning formula you love, now in our
  most-wanted flavor 🍓 Lip Butter Balm Strawberry Soft Serve features a cool
  baby pink tint, creamy strawberry sweetness and nourishing hydration in every
  swipe. ⟂ NEW Strawberry Soft Serve
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/03d34cc1-c061-45f4-aa60-3d42b52831e4`

### C17

- **Copy / headline:** Never worry about running out of your skincare and
  hybrid-makeup essentials. Get your favorites delivered automatically and
  enjoy 15% off. Cancel, pause or edit anytime. ⟂ Subscribe + Save
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/pages/subscription`

### C18

- **Copy / headline:** Flushed Lip Stain is finally back in stock. Lightweight,
  comfortable and made to last. Available in six shades for the perfect lip
  look. ⟂ Lip Stains are Back
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/flushed-lip-stain-maple`

### C19

- **Copy / headline:** The award-winning Lip Butter Balm formula you love, now
  in three new summer-inspired flavors. The Sweet Summer Minis include Peach
  Granita, Berry Sorbet and Sea Salt Caramel, bundled in one limited-edition
  set. Available for $22 while supplies last. ⟂ NEW! Sweet Summer Minis
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/1f30b244-4f02-4fac-ab14-e88a79cdd515`

### C20

- **Copy / headline:** Back in stock: mini hydration essentials to take with
  you, wherever you are. This limited-edition set is perfect for on-the-go
  moments and effortless travel for $44 ($55 value). ⟂ Dewy Travel Trio is Back
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/dewy-travel-trio`

### C21

- **Copy / headline:** Treat your lips to buttery, nourishing hydration with
  our new Summer Fruits Set. Featuring four award-winning flavors of Lip Butter
  Balm for $78 ($96 Value). ⟂ 🍓 Strawberry Soft Serve ⟂ 🌺 Pink Guava ⟂ 🍒
  Cherry ⟂ 🍊 Poppy ⟂ Limited-Edition Lip Set
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/summer-fruits-set`

### C22

- **Copy / headline:** Made for wherever summer takes you. Discover our
  travel-ready terry pouch, designed to take your everyday favorites with you
  on the go, featuring four samples of summer essentials. ⟂ Summer Essentials
  Pouch
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/summer-essentials-terry-pouch`

### C23

- **Copy / headline:** Complete your Lip Butter Balm collection with Strawberry
  Soft Serve, the flavor you've been waiting for. Limited edition, creamy and
  fruity, plus a sheer baby pink tint. It's the strawberry treat you'll reach
  for every day 🍓 ⟂ NEW Strawberry Soft Serve
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/03d34cc1-c061-45f4-aa60-3d42b52831e4`

### C24

- **Copy / headline:** NEW! This decadent, limited-edition set features our
  award-winning Lip Butter Balm in three sweet flavors: Strawberry Soft Serve,
  Vanilla and Hot Cocoa for $60 ($72 value). ⟂ NEW! Neapolitan Lip Trio
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/products/the-neapolitan-lip-trio`

### C25

- **Copy / headline:** Back in stock: Flushed Lip Stain 💋 Our weightless lip
  stain enhances your natural tone and lasts all day. Buildable,
  transfer-proof, effortless—just swipe and go. ⟂ Back in Stock
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/products/flushed-lip-stain-almond`

### C26

- **Copy / headline:** Our award-winning Jet Lag Eye Patches visibly de-puff,
  smooth, and refresh the undereye area—for instant hydration anytime,
  anywhere. Now available in a jumbo pack featuring 15 pairs of eye patches per
  box. ⟂ NEW! Jumbo Pack: 15 Pairs
- **CTA:** Shop Now
- **Destination:**
  `https://summerfridays.com/apps/blackcrow/storefronts/crowlink/995bd6c2-0b80-4f03-8ecf-a924a91481d5`

### C27

- **Copy / headline:** Sunscreen that actually feels good on your skin.
  ShadeDrops SPF 50 Mineral Milk Sunscreen is non-comedogenic, gentle enough for
  sensitive skin and layers effortlessly under makeup. ⟂ NEW! ShadeDrops SPF 50
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/collections/best-sellers`

### C28

- **Copy / headline:** Flushed Lip Stain is finally back in stock. Lightweight,
  comfortable and made to last. Available in six shades for the perfect lip
  look. ⟂ Lip Stains are Back
- **CTA:** Shop Now
- **Destination:** `https://summerfridays.com/collections/flushed-lip-stains`

### C29

- **Advertiser label:** JADE LILY with Summer Fridays
- **Copy / headline / landing label:** My everyday lip combo is finally back ⟂
  @summerfridays Flushed Lip Stain in Mocha is the lip I'm most loyal to.
  Available at SummerFridays.com ad #lipstain #lipcombo ⟂ SUMMERFRIDAYS.COM ⟂
  JADE LILY
- **CTA:** Shop now
- **Destination:** `https://summerfridays.com/products/flushed-lip-stain-maple`
- **Mismatch preserved:** the visible copy names `Mocha`; the retained
  destination resolves to the `maple` product route. This is not corrected or
  interpreted.

## 6. Creative clusters in the first-60 window

Cluster counts below count unique library IDs in this retained window. They are
not source-wide shares or campaign counts.

| Cluster | IDs | Source-visible shape |
|---|---:|---|
| Sunlit Summer Essentials | 10 | SPF + Lip Butter Balm + travel fragrance set; free accessories; value framing |
| Flushed Lip Stain restock / creator variant | 10 | back-in-stock, lasting/transfer-proof copy; one JADE LILY collaboration-labelled row |
| Strawberry Soft Serve Lip Butter Balm | 7 | new/limited flavor and tint |
| Evergreen catalog/product ads | 6 | broad skincare collection, Lip Butter Balm Vanilla, CC Me Serum |
| Essential Lip Kit | 5 | three named lip families, exclusive pouch, value framing |
| Dewy Travel Trio | 5 | restock, limited-edition travel set, value framing |
| Sweet Summer Minis / Neapolitan Lip Trio | 5 | limited-edition flavor sets and price/value framing |
| Summer Fruits Set | 4 | four Lip Butter Balm flavors, price/value framing; one multi-link carousel |
| Summer Essentials Pouch | 4 | travel-ready pouch with four samples |
| Subscribe + Save | 1 | recurring delivery and 15% discount |
| Toasted Marshmallow Lip Butter Balm | 1 | limited-edition flavor |
| Jet Lag Eye Patches jumbo pack | 1 | 15-pair format |
| ShadeDrops SPF 50 | 1 | standalone product-benefit creative |

This grouping uses the visible copy, landing labels, destinations, and retained
media state. It does not infer internal campaign structure or creative-testing
intent.

## 7. Product-family coverage

The comparison authority was freshly read from
`C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co1\13_portfolio_parent_disposition_v1\portfolio_parent_disposition_v1.json`,
SHA-256
`8B4BE38929B167A1EB1AEBFFE5EA2813A0172DFEDD3525188F534E634E2BD212`.
It resolves **27 current/exposed families** and **7 historical-only families**.

Counts are the number of first-60 inventory rows whose retained copy names the
family. A row may name more than one family, so these counts are not additive.
Bundle, set, merchandise, and sample objects remain typed separately rather
than being promoted to product families.

| Current/exposed family | Rows observed |
|---|---:|
| Lip Butter Balm | 34 |
| Flushed Lip Stain | 15 |
| ShadeDrops SPF 50 Mineral Milk Sunscreen | 11 |
| Sunlit Vanilla Eau de Parfum | 10 |
| SoftLine Lip Liner | 5 |
| CC Me Serum | 1 |
| Jet Lag Eye Patches | 1 |

No first-60-window mention was observed for these 20 other current/exposed
families: Babymoon Belly Balm; Blush Butter Balm; Body Butter Balm; Body
Fragrance Mist; Bronzer Butter Balm; Bronzing Drops; Cloud Dew Gel Cream
Moisturizer; Dream Lip Oil; Gentle Reset Daily Exfoliating Pads; Heavenly
Sixteen All-In-One Face Oil; Illuminating Drops; Jet Lag Deep Hydration Serum;
Jet Lag Mask; Jet Lag Overnight Eye Serum; Jet Lag Skin Soothing Hydration
Mist; Light Aura Vitamin C + Peptide Eye Cream; Midnight Ritual Retinol Renewal
Serum; Pink Dew Gel Cleanser; Rich Cushion Cream; Sheer Skin Tint.

No first-60-window mention was observed for the seven historical-only families:
Blush Balm Sticks; Dream Oasis Deep Hydration Serum; Overtime Mask; R+R Mask;
ShadeDrops SPF 30 Mineral Milk Sunscreen; Soft Reset AHA Exfoliating Solution;
Super Amino Gel Cleanser.

These are **window-bounded no-observed statements**, not claims that a family is
absent from the full Meta library or from Summer Fridays advertising.

## 8. Probe sequence, failures, and omissions

1. **Lower browser-runner preflight:** the first command supplied
   `--scroll-passes` to a runner that does not accept that option. Argument
   parsing failed before network contact and before packet creation.
2. **Keyword probe:** packet `01KYF1CHHG7X5JGHP0CPH0ZCAY` returned a
   source-useful surface, but the approximately 1,400 keyword results included
   unrelated advertisers. It proved transport and card detail, not advertiser
   identity.
3. **First-party identity capture:** packet `01KYF1EJBRGRZK5PMMND4N9F3C`
   retained the company homepage and its Facebook-page link.
4. **Page-search probe:** packet `01KYF1H1PFWC53Z2XM2BDJMZ2B` used
   `search_type=page&q=Summer%20Fridays`, but Meta still rendered the broad
   approximately 1,400-result keyword surface. It was rejected as inventory
   authority.
5. **Public Page identity probe:** packet `01KYF1J1HPM3J2HK44AHC22AV6`
   bound the vanity locator to page ID `1898638280462729`.
6. **Exact-page capture:** packet `01KYF1KWVQZR4ZN4NZVE8DZJ0R` used
   `view_all_page_id=1898638280462729`; Meta rendered the Summer Fridays page
   header and about 200 results. Ten scroll continuations exposed 118 unique
   IDs, and the first 60 were retained in this return.

No login handoff was required because the anonymous surface returned ad-level
detail. A known-positive advertiser canary was not required because the
commissioned advertiser surface itself passed the card-detail sufficiency
checks.

### Omissions and typed limits

- The 60-ID ceiling was hit before source exhaustion. IDs 61–118 exposed by the
  same capture are retained raw but intentionally not enumerated here.
- The source showed about 200 results, so at least some results were not exposed
  by the ten continuation actions.
- Platform icons were retained visually but their labels were not stably
  serialized into text; placement is unresolved.
- Viewport screenshot, DOM, and visible text were retained. Linked image/video
  bytes and full video playback were not independently preserved.
- Meta's grouped-version annotations were not expanded by opening every summary
  or detail drawer.
- Destination tracking parameters were stripped in this report. Raw hrefs
  remain in the packet DOM.
- Media-format typing is based on retained duration text, multi-link structure,
  and DOM media elements. It is not a frame-level creative analysis.
- The public source did not expose a campaign objective, audience definition,
  spend, budget, impressions count, conversion result, ROAS, or advertiser
  rationale.

## 9. Source evidence bundle

Raw lake:
`C:\tmp\forseti-sf-meta-ads-discovery-20260726\data`

Lake identity: epoch `v4.1`, root UUID
`01KYF1BRNBR0P8AYJCJCN92ZY2`.

| Packet | Role | Accepted use |
|---|---|---|
| `01KYF1CHHG7X5JGHP0CPH0ZCAY` | broad keyword probe | transport/card-detail proof and collision evidence only |
| `01KYF1EJBRGRZK5PMMND4N9F3C` | company homepage | first-party Facebook locator |
| `01KYF1H1PFWC53Z2XM2BDJMZ2B` | broad page-query probe | rejected route evidence only |
| `01KYF1J1HPM3J2HK44AHC22AV6` | public Facebook Page | vanity, visible identity, company domain, numeric page ID |
| `01KYF1KWVQZR4ZN4NZVE8DZJ0R` | exact advertiser-page inventory | primary 60-row inventory and creative catalog |

Every packet contains a `manifest.json`, receipt, stored source artifacts, and
per-file SHA-256 values. The primary packet retains:

- rendered DOM SHA-256
  `02d0c617840c4fd38cd1d3197728400fae3da19c16ba7244597e4452c5876b6d`;
- visible text SHA-256
  `57a5fa53e4a8a8e5d033e3e824eca1fa8c81ce9575a95f47b28d0deaf6c23f4a`;
- viewport screenshot SHA-256
  `106172877e06b51f8f1fbdf47a38c6f75c009422c3cd5f7b7c5be0658710f6f7`;
- snapshot metadata SHA-256
  `c86804d6dbfee39a28e09953e9f4b1a1b329212f5697fbbe4f0306c951b13f32`.

## 10. Validation

| Check | Result |
|---|---|
| First-60 inventory count | pass — 60 rows |
| Library-ID uniqueness in inventory | pass — 60/60 unique |
| Every inventory ID exists in the primary packet visible text | pass — 60/60 |
| Raw exact-page unique-ID recomputation | pass — 118 |
| Creative-reference integrity | pass — 29 references / 29 definitions |
| Creative-copy source binding | pass — 29/29 normalized copy sequences occur in retained source order |
| Canonical destination source binding | pass — 18/18 unique reported destinations decode from retained Meta outbound hrefs |
| Media-format recomputation | pass — 12 rows with visible video duration / 48 static-image rows |
| Cluster arithmetic | pass — cluster counts sum to 60 inventory rows |
| Advertiser-label recomputation | pass — 59 Summer Fridays / 1 JADE LILY with Summer Fridays |
| Exact page/filter/order/capture-time receipt | pass |
| First-party locator + public-page numeric-ID binding | pass |
| Portfolio authority fresh hash | pass — SHA-256 named in section 7 |
| Forbidden `not spending` formulation | absent |
| Placement limitation | present and inherited by all 60 rows |
| Raw-lake manifest verification | pass — 5/5 packets, 0 read failures, 0 missing/stale/orphan availability rows |

Repository-scoped header, output-mode, and diff validation is reported after
the artifact is committed so changed-file gates receive a non-vacuous diff.

## 11. Safe later joins and non-claims

### Safe later joins

1. Join on unique library ID for source-row identity and creative ID for
   deduplicated copy/media analysis.
2. Keep Meta's active/status/start-date fields as source-time observations.
3. Treat prices, value comparisons, discounts, and restock/limited language as
   advertiser copy, not independently verified offer truth.
4. Use the 27-family portfolio authority only for family normalization. Keep
   bundles, sets, samples, merchandise, flavors, and variants at their retained
   types.
5. Preserve C29 as a collaboration-labelled source row and its copy/destination
   mismatch; do not silently normalize it into a plain brand ad.
6. If later work needs full advertiser coverage, resume from the raw 118-ID
   exposure or recapture under a separately commissioned ceiling. Do not treat
   this first-60 window as exhaustive.

### Non-claims

- Not spend, budget, impressions, ROAS, conversion, targeting, audience,
  campaign-objective, market-priority, or executive-intent evidence.
- Not a claim that any ad was delivered to a particular person, placement, or
  physical location.
- Not a campaign count. Unique library IDs, deduplicated creative records, and
  Meta's grouped-version annotations are different source objects.
- Not a prevalence, share-of-voice, performance, or creative-effectiveness
  measurement.
- Not an exhaustive current inventory; the return is partial at 60 IDs.
- Not historical coverage. The commercial active-ad surface was captured, not
  a complete inactive or deleted-ad history.
- Not independent verification of advertiser efficacy, ingredient, product,
  offer, stock, discount, or value statements.
- Not the Deliver-side competitive-intelligence synthesis or recommendation.
- Not Judgment evidence, buyer proof, Product Lead evidence, readiness, or
  validation of Forseti.
