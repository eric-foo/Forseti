# Summer Fridays Search-Interest Capture Return — 2026-08-05

```yaml
retrieval_header_version: 1
artifact_role: One-shot Google Trends search-interest capture return (Deliver target-screen input)
scope: >
  COMPLETE return of the bounded one-shot Google Trends capture commissioned
  by the 2026-08-05 search-interest capture handoff: relative-attention
  trajectories for Summer Fridays products, head-to-heads against Phase A
  named switching destinations, dupe-demand terms, related/rising queries,
  and seasonality. All 13 batches and 5 related panels captured across three
  same-day sessions. Relative search attention only.
use_when:
  - Ranking Summer Fridays products by attention level and direction for the Deliver target screen.
  - Reading destination head-to-head, dupe-demand, or seasonality search-interest evidence for Summer Fridays.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_series.json
stale_if:
  - A newer Summer Fridays search-interest pull supersedes this one-shot capture.
  - Google materially changes Trends normalization, comparison limits, or export fields.
  - The Summer Fridays Deliver run this capture feeds is completed or re-commissioned.
```

- Commission: `docs/prompts/handoffs/summer_fridays_search_interest_capture_handoff_20260805_v0.md`
  (bounded owner authorization for exactly one one-shot pull, 2026-08-05).
- Status: **COMPLETE** — all 13 planned batch timelines and all five
  related/rising panels (brand queries, brand topics, and the three
  hero-product panels) captured. Capture spanned three same-day sessions:
  morning automation pane (8 timelines + brand panels), real Chrome 14:22 UTC
  (b06), VPN egress 14:44–20:41 UTC (b05, b03, b10, b07, and the three
  hero-product panels). The capture stayed inside the 14-batch cap and
  public human-rate access throughout.
- Raw root: `C:\tmp\forseti-sf-search-interest-discovery-20260805\data`
  (verbatim API response bodies plus `manifest.jsonl` with size/sha256/UTC
  receipt per file; raw exports stay outside Git).
- Machine-readable series:
  `docs/research/summer_fridays_ci_inputs_20260805/search_interest_series.json`
  — one record per (term, geo, window, batch) with the relative-index series,
  batch id, anchor term, threshold/null flag, and capture parameters; the
  anchor term recurs across batches by design, each under its own
  batch-normalized 0–100 scale.
- Value semantics: every number below is the Google Trends **0–100 relative
  search-interest index, normalized to the peak of its own batch and window**.
  Nothing here is a count, sales figure, demand size, prevalence, or market
  share.

## 1. Executive capture conclusion (relative attention only)

1. **Lip Butter Balm is the brand's attention center of gravity, but every
   captured Phase A switching destination holds a level-or-rising curve — none
   is decaying — and most out-level the SF product they compete with.** In the
   lip head-to-head (b04, 5-y, US), Laneige Lip Mask's recent-quarter relative
   level is roughly 4× Lip Butter Balm's (9.4 vs 2.4), while Rhode, Aquaphor
   Lip Repair, and Lanolips sit at approximately Lip Butter Balm's own level
   (2.0–3.0). In the tint head-to-head (b06, 5-y, US), every named destination
   out-levels SF Sheer Skin Tint in the recent quarter — Ilia ~5× (30.1 vs
   5.6), Saie ~3× (17.3), Hourglass ~2.5× (13.8) — and all three are rising
   half-over-half; Armani Luminous Silk is ~14× on the b12 12-m scale.
2. **Brand-level attention peaked in 2024 and has drifted down through 2026
   year-to-date, with a holiday—not summer—seasonal shape.** Yearly means of
   the brand curve fall 36.8 → 33.2 → 29.0 (2024→2026 YTD, all categories,
   b09) and 39.0 → 29.9 → 23.5 within Beauty & Fitness (b11). Monthly means
   peak in November–December (b11: 35.7/45.5) and trough in July–August
   (16.2/13.4). The worldwide curve (b10) shares the holiday shape but
   declines more gently (39.2 → 32.7 YTD) — the fall-off is US-led. The
   capture records these curves; it does not attribute cause.
3. **Dupe-demand exists at brand level and persists; the rising-query panel is
   dominated by flavor-drop breakouts plus two products.** "summer fridays
   dupe" emerged in 2024, peaked April 2025 (24 vs anchor peak 100), and stays
   non-zero but past peak — the 12-m window (b07) shows it flat-to-cooling
   (half-window means 6.0 → 4.3). Product-specific dupe phrasings are below the Google Trends
   reporting threshold under the recorded geo/window. Rising brand queries are
   mostly flavor drops (birthday cake, pink sugar, hot cocoa, toasted
   marshmallow, iced coffee, pink guava, cherry) plus Sheer Skin Tint
   (+2,750%) and Dream Lip Oil (Breakout); `rhode` (+4,100%) and `laneige`
   also appear inside the brand's own related-query panels.

## 2. Capture-parameter receipt per batch and anchor-bridging map

Frozen parameters for all batches: property = web search, tz parameter =
`-480`, capture host = Google Trends web UI API endpoints (`/trends/api/explore`
+ `/trends/api/widgetdata/*`) from an in-page browser session, capture date
2026-08-05 UTC. Geo, window, and category per batch below. Anchor term for
every multi-term batch: **"summer fridays lip butter balm"**.

| Batch | Family | Terms | Geo | Window | Cat | Timeline captured (UTC) | Timeline sha256 (12) | Points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b01 | SF vs SF | anchor + skin tint, jet lag mask, lip oil, cloud dew | US | 12-m | 0 | 09:42:53 | 8e80ca8cd977 | 53 |
| b02 | SF vs SF | same as b01 | US | 5-y | 0 | 09:50:29 | f1ad931d64c0 | 262 |
| b03 | Lip head-to-head | anchor + laneige lip mask, rhode lip treatment, aquaphor lip repair, lanolips | US | 12-m | 0 | 15:38:48 (VPN session) | 561e753e8c5d | 53 |
| b04 | Lip head-to-head | same as b03 | US | 5-y | 0 | 09:58:51 | 4c46756e6580 | 262 |
| b05 | Tint head-to-head A | anchor + sf skin tint, saie slip tint, ilia skin tint, hourglass skin tint | US | 12-m | 0 | 14:44:09 (VPN session) | 7c81de05187f | 53 |
| b06 | Tint head-to-head A | same as b05 | US | 5-y | 0 | 14:22:53 (real-Chrome session) | see manifest | 262 |
| b07 | Dupe demand | anchor + summer fridays dupe, lip butter balm dupe, jet lag mask dupe, sf skin tint dupe | US | 12-m | 0 | 18:04:47 (VPN session) | 2ac61142a57a | 53 |
| b08 | Dupe demand | same as b07 | US | 5-y | 0 | 10:15:16 | f911f40d52c9 | 262 |
| b09 | Brand seasonality | summer fridays (single term) | US | 5-y | 0 | 10:28:41 | dcead5e0fd42 | 262 |
| b10 | Brand worldwide check | summer fridays (single term) | Worldwide | 5-y | 0 | 17:06:51 (VPN session) | 7f58d425987b | 262 |
| b11 | Brand category check | summer fridays (single term) | US | 5-y | 44 (Beauty & Fitness) | 09:40:47 | 933dec0b12b5 | 262 |
| b12 | Tint head-to-head B | anchor + sf skin tint, kosas skin tint, armani luminous silk | US | 12-m | 0 | 10:19:29 | 7279ee1e11d2 | 53 |
| b13 | Secondary SF products | anchor + shadedrops, dream oasis, rich cushion | US | 12-m | 0 | 10:21:55 | a5b984100097 | 53 |

Explore-request receipts (widget-token responses) were retained for **all 13
batches** including the five whose timelines failed (b03 09:51:35, b05
09:59:58, b06 10:03:57, b07 10:08:17, b10 10:37:19 UTC; sha256s in
`manifest.jsonl`). Related-panel receipts: brand related queries 10:31:27,
brand related topics 10:34:16 UTC.

Anchor-bridging map — the anchor's batch-relative level lets a reader rescale
across the captured multi-term batches (all values are within-batch indices):

| Batch | Anchor mean | Anchor max | Bridge note |
| --- | --- | --- | --- |
| b01 (12-m) | 21.6 | 100 | anchor is batch peak |
| b02 (5-y) | 9.0 | 96 | lip oil's Jan-2024 spike is batch peak |
| b03 (12-m) | 13.7 | 64 | Laneige Lip Mask is batch peak (100); VPN session |
| b04 (5-y) | 1.4 | 15 | Laneige Lip Mask is batch peak (100) |
| b05 (12-m) | 11.4 | 53 | Ilia skin tint is batch peak (100); VPN session |
| b06 (5-y) | 5.8 | 61 | Ilia skin tint is batch peak (100); captured in the second (real-Chrome) session |
| b07 (12-m) | 21.4 | 100 | anchor is batch peak; VPN session |
| b08 (5-y) | 9.4 | 100 | anchor is batch peak |
| b12 (12-m) | 4.0 | 18 | Armani Luminous Silk is batch peak (100) |
| b13 (12-m) | 21.6 | 100 | anchor is batch peak |

Example bridge: b04's scale ≈ b02's scale × (1.4/9.0); b12's scale ≈ b01's ×
(4.0/21.6). The three brand batches (b09/b10/b11) are single-term and carry no
anchor; they are not numerically bridgeable to the product batches within this
capture.

## 3. Trajectory read per SF product

Half-window means (first half vs second half of the window's completed weeks)
and the last-quarter mean, from b01/b02/b13:

| Product | 5-y read (b02) | 12-m read (b01/b13) | Trajectory label |
| --- | --- | --- | --- |
| Lip Butter Balm | 6.2 → 11.7; peak 96 @ Dec 2023 | 10.9 → 32.2; peak 100 @ Apr 12–18 2026; last 4 wk 17/7/4/7 | **Rising (5-y); post-April-peak fall-off into the seasonal trough (12-m)** |
| Sheer Skin Tint | 1.4 → 4.3; peak 33 @ Apr 2026 | 1.6 → 12.6; 37% of weeks at 0 | **Rising from a low, threshold-intermittent base** |
| Jet Lag Mask | 1.7 → 8.6; peak 25 @ Apr 2026 | 13.5 → 12.8 | **Rising (5-y); flat (12-m)** |
| Dream Lip Oil ("summer fridays lip oil") | 3.2 → 10.8; peak 100 @ Jan 2024 (launch-shaped spike) | 7.3 → 14.9 | **Rising after spike-and-retreat** |
| Cloud Dew | 0.2 → 0.9; 90% of weeks at 0 | 0.0 → 5.4; 69% at 0 | **Intermittent; mostly below the Google Trends reporting threshold under the recorded geo/window** |
| ShadeDrops | — (12-m only) | 0.2 → 2.5; peak 9 @ May 2026; 77% at 0 | **Emerging spikes from a below-threshold base** |
| Dream Oasis | — | all completed weeks 0 | **Below the Google Trends reporting threshold under the recorded geo/window** |
| Rich Cushion | — | 0.0 → 0.3; 96% at 0 | **Intermittent; effectively below threshold** |

Prize read for the target screen (attention level and direction, within-batch
relative index only): Lip Butter Balm ≫ Jet Lag Mask ≈ Dream Lip Oil > Sheer
Skin Tint (rising fastest from the smallest base) ≫ Cloud Dew / ShadeDrops /
Rich Cushion / Dream Oasis (at or below threshold). A synchronized attention
spike across nearly all SF terms occurred in the weeks of Apr 5–18, 2026.

## 4. Destination head-to-head table

Captured head-to-heads (within-batch relative index; "recent" = last-quarter
mean of completed weeks):

| Comparison (batch) | SF term recent | Destination recent | Peak in window | Read |
| --- | --- | --- | --- | --- |
| Lip Butter Balm vs Laneige Lip Mask (b04, 5-y US) | 2.4 | 9.4 | Laneige 100 @ Oct–Nov 2024 | Laneige holds ~4× SF's recent relative attention; both decline from holiday peaks |
| Lip Butter Balm vs Rhode lip treatment (b04) | 2.4 | 2.6 | Rhode 14 @ Apr 2026 | Comparable recent levels; Rhode rising (1.4 → 2.3 half-over-half) |
| Lip Butter Balm vs Aquaphor Lip Repair (b04) | 2.4 | 2.9 | Aquaphor 15 @ Apr 2026 | Comparable recent levels; the price-floor staple neither dominates nor fades |
| Lip Butter Balm vs Lanolips (b04) | 2.4 | 3.0 | Lanolips 7 @ Dec 2024 | Comparable recent levels; Lanolips flatter, steadier |
| SF Sheer Skin Tint vs Armani Luminous Silk (b12, 12-m US) | 1.9 | 26.2 | Armani 100 @ Apr 2026 | Armani ~14× SF tint's recent relative attention |
| SF Sheer Skin Tint vs Kosas skin tint (b12) | 1.9 | 0.5 | Kosas 1 | SF tint above this destination phrasing; Kosas term mostly below threshold |
| SF Sheer Skin Tint vs Ilia skin tint (b06, 5-y US) | 5.6 | 30.1 | Ilia 100 @ Apr 2026 | Ilia ~5× SF tint's recent relative attention; rising (9.2 → 14.8 half-over-half) |
| SF Sheer Skin Tint vs Saie slip tint (b06) | 5.6 | 17.3 | Saie 62 @ Apr 2026 | Saie ~3× SF tint; rising (2.0 → 6.6) |
| SF Sheer Skin Tint vs Hourglass skin tint (b06) | 5.6 | 13.8 | Hourglass 51 @ Apr 2026 | Hourglass ~2.5× SF tint; rising (0.9 → 7.8) |

Phase A's qualitative switching-destination signal is now testable for both
axes: every captured named destination (lip: Laneige, Rhode, Aquaphor,
Lanolips; tint: Ilia, Saie, Hourglass, Armani, Kosas) shows a level-or-rising
curve — none is decaying — supporting the read that the destinations are
gaining attention independently of our qualitative evidence. The 12-m windows
(b03/b05, VPN session) confirm the 5-y reads at finer granularity: Laneige's
12-m mean (~47) dwarfs the anchor's (~14) on the shared scale, and Ilia leads
the tint set (second-half mean 32.9 vs SF tint 6.7) with Saie and Hourglass
also above SF tint; all destinations rising or holding within the year.

## 5. Dupe-demand read

From b08 (5-y US, anchored): "summer fridays dupe" was at 0 for essentially all
of 2021–2023 (half-1 mean 0.6), emerged with the brand's late-2023/2024 rise,
peaked at 24 in the week of Apr 6–12, 2025 (vs anchor peak 100), and remains
intermittently non-zero through 2026 (last-quarter mean 4.6). Product-specific
dupe phrasings — "lip butter balm dupe" (single week at 4, otherwise 0), "jet
lag mask dupe", and "summer fridays skin tint dupe" — are below the Google
Trends reporting threshold under the recorded geo/window. The capture records
that dupe-seeking search phrasing exists and persists at brand level; it does
not attribute motive or estimate dupe-purchase behavior. The 12-m window
(b07, VPN session) adds a direction read: within the last year "summer
fridays dupe" is flat-to-cooling (half-window means 6.0 → 4.3 on the
anchored scale), i.e. brand-level dupe demand persists but is past its
April-2025 peak. Product-specific dupe phrasings remain below the Google
Trends reporting threshold under the recorded geo/window in the 12-m batch
as well — with one cross-check: "summer fridays jet lag mask dupe" does
surface inside the Jet Lag Mask related-query panel (§6), so product-level
dupe intent exists but at panel-only volume.

## 6. Related and rising query inventory

Brand term, US, 5-y (b09 panels). Top (index vs top query = 100):
`summer fridays lip` 100 · `lip balm` 74 · `summer fridays lip balm` 73 ·
`summer fridays set` 17 · `summer fridays sephora` 17 · `sephora` 16 ·
`mini summer fridays` 14 · `summer fridays lip butter` 12 ·
`summer fridays butter balm` 11 · `lip gloss` 11 · `summer fridays lip gloss`
11 · `summer fridays lip butter balm` 11 · `summer fridays ulta` 11 ·
`summer fridays mask` 10 · `pink summer fridays` 10 · `summer fridays lip set`
9 · `summer fridays jet lag` 9 · `summer fridays lip balm set` 8 ·
`summer fridays lip oil` 8 · `jet lag mask summer fridays` 7 · **`rhode` 6** ·
`mini summer fridays lip balm` 6 · `new summer fridays` 5 ·
`summer fridays vanilla` 5 · **`laneige` 5**.

Rising: Breakouts — `summer fridays birthday cake`, `pink sugar`, `minis`,
`hot cocoa`, `toasted marshmallow`, `iced coffee`, **`sheer skin tint`**,
`shop summer fridays lip butter balm`, `pink guava`, `cherry lip balm`,
**`dream lip oil`**, `owala`, `does ulta have summer fridays`,
`is summer fridays at ulta`, `does ulta sell summer fridays`,
`lip balm set`, `pr email`, `shade drops`, `mini lip balm`, `lip set`;
percent-risers — **`rhode` +4,100%**, `summer fridays lip oil` +2,800%,
`summer fridays skin tint` +2,750%, `summer fridays vanilla` +2,550%,
`summer fridays mini set` +2,450%.

Per-product panels (12-m US, VPN session; all thin, no rising rows —
consistent with product-term volumes near the reporting floor):

- **Jet Lag Mask** (3 rows): `how to use` 100 · `review` 42 · **`dupe` 38** —
  usage-intent leads, and the product-level dupe query appears here despite
  its standalone timeline being below threshold.
- **Lip Butter Balm** (6 rows): `set` 100 · `mini` 52 · `vanilla` 28 ·
  `for hydration & shine` 20 · `pink sugar` 13 · `brown sugar` 9 — entirely
  brand-owned navigation (sets, minis, flavors); no dupe or competitor row.
- **Sheer Skin Tint** (1 row): `review` 100 — pure evaluation intent, the
  thinnest panel, consistent with a new product still building attention.

Comparison-shaped queries: **no literal "x vs y" query appears in any
captured panel.** The comparison-priority signal present is destination-brand co-search:
`rhode` (top 6, rising +4,100%) and `laneige` (top 5) inside the brand's own
panel. Distribution-shaped rising queries (`does ulta have/sell summer
fridays`) are flagged as availability questions, not comparisons. `owala` (a
water-bottle brand) is a likely generic-phrase contamination row, retained
as-captured. Related topics returned an empty ranked list (retained verbatim).
Per-product related panels (Lip Butter Balm, Sheer Skin Tint, Jet Lag Mask)
were **not captured** (blocked; §9).

## 7. Seasonality read

Brand term, 5-y US, monthly means of weekly completed values:

| Curve | Nov | Dec | Jan | Feb | Jul | Aug | Shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| All categories, US (b09) | 33.8 | 38.6 | 21.5 | 24.4 | 16.5 | 12.7 | Holiday peak, summer trough |
| Beauty & Fitness only, US (b11) | 35.7 | 45.5 | 22.6 | 22.7 | 16.2 | 13.4 | Same shape, sharper Dec peak |
| All categories, worldwide (b10, VPN session) | 35.4 | 40.0 | 22.8 | 25.8 | 19.0 | 15.1 | Same holiday shape worldwide |

Yearly means: 2021 2.1 → 2022 4.3 → 2023 16.3 → 2024 36.8 → 2025 33.2 → 2026
YTD 29.0 (b09); the Beauty-only curve shows the same 2024 peak and steeper
2026 decline (39.0 → 23.5 YTD, where YTD excludes the seasonally strong
Nov–Dec months). Despite the brand name, **November–December is the annual
attention peak and July–August the trough** in both curves; the two curves
agree closely, indicating the beauty-brand sense dominates the all-categories
term. The worldwide check (b10) shows the same holiday shape but a **gentler
post-2024 decline** (39.2 → 38.1 → 32.7 YTD), i.e. the attention fall-off is
sharper in the US than in the brand's worldwide aggregate.

## 8. Threshold and null ledger

Every term below or intermittently below the reporting floor, with the exact
required phrasing — these are threshold artifacts, not absence of interest:

| Term | Batch (geo/window) | Status |
| --- | --- | --- |
| jet lag mask dupe | b08 (US/5-y); b07 (US/12-m) | below the Google Trends reporting threshold under the recorded geo/window (all completed weeks 0) |
| summer fridays skin tint dupe | b08 (US/5-y); b07 (US/12-m) | below the Google Trends reporting threshold under the recorded geo/window (all completed weeks 0) |
| summer fridays dream oasis | b13 (US/12-m) | below the Google Trends reporting threshold under the recorded geo/window (all completed weeks 0) |
| summer fridays rich cushion | b13 (US/12-m) | intermittently below threshold (96% of weeks 0) |
| summer fridays cloud dew | b02 (US/5-y); b01 (US/12-m) | intermittently below threshold (90% / 69% of weeks 0) |
| summer fridays shadedrops | b13 (US/12-m) | intermittently below threshold (77% of weeks 0) |
| lip butter balm dupe | b08 (US/5-y) | intermittently below threshold (99% of weeks 0) |
| kosas skin tint | b12 (US/12-m) | intermittently below threshold (63% of weeks 0) |
| summer fridays skin tint | b02 (US/5-y); b01 (US/12-m); b12 (US/12-m); b06 (US/5-y) | intermittently below threshold in early window (46% / 37% / 40% / 43% of weeks 0) |
| summer fridays dupe | b08 (US/5-y) | intermittently below threshold before 2024 (48% of weeks 0 across the window) |
| summer fridays lip butter balm | b02, b08 (US/5-y) | 26% of weeks 0 (pre-2023 cold period) |
| rhode lip treatment / aquaphor lip repair | b04 (US/5-y) | 18% / 8% of weeks 0 in early window |

## 9. Failure and omission ledger

Access-route failures (all preserved as receipts or logs; no rate-limit
defeat was attempted):

1. `pytrends` (fresh install, Python 3.12) returned HTTP 429 on the first
   `interest_over_time` probe — automated route recorded as blocked; capture
   moved to the UI surface per the handoff's stated preference.
2. Direct navigation to `/trends/explore` without a session returned HTTP 429
   once; the homepage-first flow then loaded normally.
3. Google issued this browser session `userType: USER_TYPE_SCRAPER` in its
   own widget tokens; the `widgetdata` endpoints applied an aggressive quota
   throughout. The Trends UI page itself never fired its widget requests in
   the undisplayed automation pane, so widget data was fetched via the page's
   own API endpoints in-session (same requests the chart UI makes).
4. Timeline (`multiline`) captures for b03, b05, b06, b07, b10 failed with
   persistent HTTP 429 in the automation-pane session across: an initial pass
   (55–75s pacing), a retry pass (150–210s pacing, 3 attempts each, 180s
   cooloffs), a 30-minute quiet period, a 20-minute extended quiet, and a
   final single attempt (13:45 UTC) after a further ~53-minute quiet.
   Per-product related-query panels for b01 (3 requests) failed identically.
   Full request-level logs: `run_log.json`, `run_log_fix.json`,
   `run_log_final.json` in the raw root.
5. A same-day second session in the owner's real, signed-in Chrome (owner
   instruction, this lane) re-attempted the five missing timelines and three
   related panels at 45–75s pacing with one 120s-cooloff retry each. Google
   assigned that session the same `USER_TYPE_SCRAPER` token flag, indicating
   the classification and quota are keyed to the shared IP address (heated by
   the day's earlier attempts), not the browser environment. Result: **b06
   captured** (14:22:53 UTC, first attempt); b03, b05, b07, b10 and the three
   related panels still 429. Log: `run_log_chrome.json`; raw bodies were
   extracted via a single file download (`sf_trends_chrome_capture_20260805_bundle.json`)
   because the extension blocks base64 tool returns and localhost POSTs would
   have required a local-network permission grant. The morning b06 explore
   receipt is preserved as `b06_explore_scraper_session.json`; Chrome-session
   explore receipts for the still-missing batches carry a `_chrome` suffix.
   A third same-day session through a VPN egress (84.17.35.84, AS60068
   Datacamp — owner-initiated) received the same `USER_TYPE_SCRAPER` flag
   (datacenter ranges are pre-flagged), but persistent retry loops at 7- to
   30-minute rounds recovered, in order: **b05** (14:44:09), **b03**
   (15:38:48), **b10** (17:06:51), the **Jet Lag Mask related panel**
   (17:24:17), and **b07** (18:04:47 UTC) — completing all 13 timeline
   batches. Logs: `run_log_vpn.json`, `run_log_vpn_finisher.json`,
   `run_log_vpn_slow.json`; VPN-session explore receipts carry a `_vpn`
   suffix, and superseded morning explore bodies for recovered batches are
   preserved with the `_scraper_session` suffix. The final two hero-product
   panels (Lip Butter Balm, Sheer Skin Tint) landed at 20:38:57 and 20:41:32
   UTC after a ~2.5-hour quiet stretch (`run_log_night.json`), completing
   the capture.
6. Related-topics panel for the brand term returned an empty ranked list
   (valid HTTP 200; retained verbatim as a source-side null).

Omissions and deviations:

7. **Cut list: none.** All 13 timeline batches and all five related/rising
   panels were ultimately captured; the PARTIAL states earlier in the day
   were fully recovered by 20:41 UTC. The only capture-shaped residue is
   that the three per-product panels returned no "rising" rows (source-side
   nulls, retained verbatim).
8. The handoff file itself was staged-but-uncommitted in the sender lane, so
   the load-contract clause "this handoff must exist at that HEAD" was not
   literally satisfiable; the owner supplied the packet path directly in-chat
   and the packet content was read verbatim from the sender worktree. Recorded
   as a provenance deviation, not a blocker.
9. An early reduced reconstruction of `b09_explore.json` (rebuilt from a tool
   log, marked as such in-body) was superseded by a verbatim re-capture at
   10:25:48 UTC; the manifest shows both receipts.
10. GEO_MAP (interest-by-subregion) widgets were not captured — outside the
    commissioned families.
11. Brand batches (b09/b10/b11) are single-term by design and therefore not
    numerically bridgeable to the product batches (see §2).
12. `connectivity_test.txt` in the raw root is a local receiver test file,
    not a capture. Batches span two same-day capture sessions (morning
    automation pane; b06 at 14:22 UTC in real Chrome); each batch is
    internally consistent, and cross-batch comparison goes through the
    anchor map as designed.

## 10. Non-claims: what the Deliver target screen may and may not conclude

May conclude (within relative-attention semantics):

- Relative attention ranking and direction among SF products under the
  recorded geo/window (§3), including that Lip Butter Balm carries the bulk of
  product-level search attention.
- That captured lip destinations hold level-or-rising curves, with Laneige
  Lip Mask well above and Rhode/Aquaphor/Lanolips comparable to Lip Butter
  Balm's recent relative level.
- That brand-level dupe phrasing exists, emerged with the 2024 rise, and
  persists.
- That the brand's search-attention seasonality peaks Nov–Dec and troughs
  Jul–Aug, and that the 2024 annual peak has not been re-attained since.

May NOT conclude:

- Any sales, revenue, demand size, market share, prevalence, or population
  rate — Google Trends values are a source-declared 0–100 relative index.
- Motive behind branded search (curiosity, dupe-hunting, and purchase intent
  are mixed and not separable here).
- "No interest" or "no demand" for any below-threshold term — those rows are
  threshold artifacts under the recorded geo/window.
- Cross-pull comparability: this is a single 2026-08-05 pull; a future pull
  re-normalizes the entire series and is not directly comparable without
  re-anchoring (entity/topic IDs were unavailable; freeform query strings
  were used).
- Any change to the sealed Phase A corpus, its axis conclusions, or its seal.

## Validation

- Fresh-read of both return artifacts: see closeout report in the delivery
  message (performed after write).
- Every series record in `search_interest_series.json` names its raw export
  file and sha256; the export resolves in the raw root manifest.
- Batch/term counts recomputed from the series file at build time: 51 series
  records across all 13 timeline batches; 5 related panels.
