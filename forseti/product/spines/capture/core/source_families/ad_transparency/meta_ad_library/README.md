# Capture Source Family: Meta Ad Library

```yaml
retrieval_header_version: 1
artifact_role: Capture source-family lane index and recipe card
scope: >
  Cold-start lane index and banked route card for public, logged-out Meta Ad
  Library capture: advertiser identity resolution, page-scoped enumeration to
  exhaustion, US-vs-EU corpus classes, field extraction, and known
  false-diagnoses. Authored by the 2026-07-26 Summer Fridays first probe.
use_when:
  - Capturing a brand's observable Meta/Facebook/Instagram ad creative.
  - Deciding whether a Meta Ad Library "empty" or "blocked" call was made honestly.
  - Routing a "capture Meta ads" request from the Source Capture Playbook.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - forseti/product/spines/data_lake/README.md
stale_if:
  - Meta changes Ad Library URL grammar, filters, result fields, or access class.
  - The card grammar (`Library ID:` anchors, `l.facebook.com/l.php?u=` destinations) changes.
  - A dedicated Meta Ad Library runner supersedes the generic browser/CloakBrowser transports.
non_claims:
  - not validation, not readiness, not standing-capture authorization
  - single-brand probe evidence; scale and account-safety envelope unmeasured
```

## Route Card

| Field | Value |
|---|---|
| **source** | Meta Ad Library, `facebook.com/ads/library/` |
| **access class** | **publicly-viewable, logged-out.** A "Log in" nav item exists but gates nothing. Step 0 passes; no entitled session needed. |
| **substrate** | JS-rendered SPA. Ad cards live in rendered DOM; the page drives its own `POST /api/graphql/` calls. Direct HTTP returns a shell — **never** a content route. |
| **route that worked** | `run_source_capture_cloakbrowser_packet.py` with `--settle-seconds 10 --scroll-passes 25 --max-artifact-bytes 40000000`. Plain `run_source_capture_browser_packet.py` works for a single unscrolled render but has **no scroll support**, so it cannot enumerate. |
| **request-rate ceiling** | human-rate, one page-scoped URL per run, attended. No keyword crawling, no multi-brand sweeps. |
| **content-anchor** | `Library ID: <digits>` lines in visible text; one card per anchor. |
| **corpus classes** | **US** = active ads only (expired US commercial ads are unobtainable). **EU country** (`country=FR` etc.) with `active_status=all` = ~1 year DSA retention incl. inactive ads with date ranges and per-card "EU transparency" sections. |

## Cold-Start Procedure

### Step 1 — Resolve advertiser identity (never skip; name collisions are common)

Three admitted legs, cheapest first:

1. **Company site → page alias.** Direct-HTTP the brand's own homepage
   (`run_source_capture_http_packet.py`); extract `facebook.com/<alias>` from the
   footer. This is the first-party binding.
2. **Alias → numeric page_id.** Browser-render `facebook.com/<alias>`
   (`run_source_capture_browser_packet.py --settle-seconds 6`). The numeric
   page_id appears in the rendered DOM; visible text carries name, category,
   contact email, and site — enough to reject collisions.
3. **page_id → ad surface.** Use the page-scoped URL below and confirm the
   rendered advertiser byline matches.

*Optional fast path (diagnostic, not a packet):* typing the brand into the Ad
Library search box fires a GraphQL typeahead whose response exposes `page_id`,
`page_alias`, `verification`, `likes`, and linked `ig_username` per candidate —
the cheapest disambiguation surface. Read it via browser network inspection.
Identity **claims** must still rest on the three admitted legs above.

### Step 2 — Freeze parameters, then enumerate

Page-scoped URL grammar:

```
https://www.facebook.com/ads/library/?active_status=<active|all>&ad_type=all&country=<CC>&view_all_page_id=<PAGE_ID>&search_type=page&media_type=all
```

Meta rewrites the final URL to add `is_targeted_country=false` and
`sort_data[mode]=total_impressions&sort_data[direction]=desc`. **Record this as
source-declared default sort, not an operator choice** — composition is
sort-dependent (see false-diagnoses).

Run to exhaustion. **PowerShell** (this repo's default shell — use backtick
continuations; a bash-style `\` continuation is a parse error here):

```powershell
python forseti-harness/runners/run_source_capture_cloakbrowser_packet.py `
  --url '<page-scoped URL>' `
  --source-family 'meta_ad_library' `
  --source-surface 'ads_library_page_scoped_<status>_<market>[_exhaustion]' `
  --decision-question '<what this run must answer>' `
  --data-root '<lake-root>\data' `
  --settle-seconds 10 --scroll-passes 25 --wait-until load `
  --timeout-seconds 280 --max-artifact-bytes 40000000
```

Argument authoring notes (each of these cost a cold receiver time):

- **`--data-root` is the directory carrying the `.forseti-data-root` marker** —
  i.e. the `…\data` directory itself, not its parent. Verify with
  `Test-Path '<root>\.forseti-data-root'` before the run. If the root does not
  exist yet, create it with
  `python -c "from data_lake.root import DataLakeRoot; DataLakeRoot.initialize(r'<abs path>', label='<label>')"`.
  Note `initialize` is **idempotent** — it silently verifies an existing root
  rather than failing, so it will not tell you the lake was already populated
  by someone else. Inventory `raw/` yourself before assuming a fresh lake.
- **`--source-surface`** is free text; keep the observed convention
  `ads_library_page_scoped_<status>_<market>`, suffixed `_exhaustion` when the
  run scrolled to the terminal state (e.g.
  `ads_library_page_scoped_all_status_fr_exhaustion`).
- **`--decision-question`** is a full question naming brand/page, market,
  status filter, and depth. Pattern: *"What is the complete visible `<CC>`
  `<status>` ad corpus for `<brand>` page `<page_id>` in the Meta Ad Library,
  scrolled to exhaustion?"*
- **No `PYTHONPATH` setup is required** — the runner self-inserts its parent on
  `sys.path` when invoked as a script. Setting it is harmless.

`--max-artifact-bytes` matters: the adapter default is 5,000,000 and a scrolled
Ad Library DOM exceeds it (observed 4.65 MB at 185 cards, and it grows with
card count). A truncated DOM silently loses destination URLs.

### Step 3 — Verify exhaustion before claiming completeness

A run is exhausted only when the visible text **ends with the Meta footer**
(`System status` / `Ad Library API…` / `Meta © <year>`) rather than mid-card.
Then count anchors and read the declared total — PowerShell:

```powershell
$vt = (Get-ChildItem '<packet>\raw' -Filter '*visible_text*').FullName
$t  = Get-Content $vt -Raw
"unique_ids=$((([regex]::Matches($t,'Library ID: (\d+)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)).Count)"
"declared=$(([regex]::Match($t,'~\d+ results')).Value)"
"footer_terminal=$($t.TrimEnd().EndsWith('English (UK)'))"
```

The declared total matches the regex `~\d+ results` and sits **above the first
card**, before the `Filters` / `Sort by` block; there is no other `results`
string in the chrome. Declared counts are **rounded** (a declared "~200"
exhausted at 185 real IDs; "~16" exhausted at 11), so a shortfall against a
rounded figure is not automatically PARTIAL — the footer-terminal state is the
authority. If scrolling stops mid-card, raise `--scroll-passes` and re-run.

## Field Extraction

Per card, from visible text (strip zero-width chars `\u200B\uFEFF\u200E\u200F`
first — they separate every UI element):

- `Library ID: <n>` (anchor), status line **immediately above** the anchor
  (`Active` / `Inactive`) — when chunking, exclude the next card's status line;
- `Started running on <date>`, or for EU inactive ads a `<date> - <date>` range;
- `This ad has multiple versions`; `N ads use this creative and text`;
- advertiser byline: the line **after** `See ad details` / `See summary details`
  (a byline of the form `<Creator> with <Brand>` marks a partnership ad);
- body text after `Sponsored`; then optional visible domain (`BRAND.COM`),
  headline, description, and a trailing CTA (`Shop Now`, `Learn More`, …);
- `M:SS / M:SS` lines indicate video media and give duration.

Destination URLs come from the **rendered DOM**, not visible text: each card
carries an `l.facebook.com/l.php?u=<encoded>` wrapper. URL-decode, then strip
`utm_*`, `fbclid`, and vendor macros. This field is the highest-value one — it
exposes retailer-vs-DTC routing and ad-tech vendors.

A worked extractor (Python, deterministic, network-free) is preserved at
`derived/meta_ads_extraction_script.py` inside any lake produced by this route.

## Known False-Diagnoses

1. **Direct HTTP 400 on `facebook.com/<alias>`** — route evidence, not a block.
   Use a browser route.
2. **`?id=<library_id>` permalink is viewer-geo-sensitive.** It rendered one
   card in a browser resolving to `country=SG`, and returned "No ads match your
   search criteria" from the CloakBrowser run under different geo/session
   state. Do not read that empty state as ad absence.
3. **An empty country result is not absence until instrument-proven.** Re-run
   the same country with a known-positive commercial keyword; if that renders
   cards with inactive history, the empty brand result is real. (Observed:
   `country=DE` empty for the brand while a `zalando` control returned >50,000
   declared / 49 cards / 43 inactive.)
4. **Absence is per-country.** `country=DE` empty while `country=FR` had a live
   corpus for the same page. Never generalize one country view to "EU".
5. **Detail panes add almost nothing.** "See ad details" repeats the card and
   adds only a version counter (`1 of 5`). The version carousel does **not**
   advance under synthetic clicks or full pointer-event sequences — it needs
   trusted input, which is the anti-bot boundary. Do not build a detail sweep;
   the DOM also holds fewer unique creative images than the version count.
6. **Platform/placement icons have no accessible names.** Placement is *not*
   extractable from the card surface. Absence of a placement label is unknown,
   never "placement unused".
7. **Snapshot metadata does not confirm scrolling.** In schema_version 3 there
   is **no** `scroll_passes_completed` key (do not grep for it); `scroll_passes`
   echoes the *requested* count and `capture_phase_timing.scroll_passes` holds
   per-pass timings, while `before_scroll_steps_completed` reads `false` even on
   runs that demonstrably scrolled to 185 cards. Judge scroll success by unique
   card count and footer-terminal state, never by these fields.
8. **Keyword search is not brand evidence.** A `"<brand>"` keyword query returns
   any advertiser whose copy contains the phrase (observed: ~1,400 results
   dominated by unrelated advertisers). Always enumerate page-scoped.

## Honest Envelope

- No spend, budget, impressions, reach (outside EU transparency sections),
  targeting, performance, or objective exists on this surface for non-political
  ads. The impressions **sort** exposes no values.
- One capture is one observed state; composition is sort- and render-dependent.
- Absence phrasing: **"No active <brand> commercial creative was observed on the
  captured Meta Ad Library surface under the recorded market/filter/window."**
  Never shorten to "not spending".
- Branded-content ads run solely from a creator's own page are outside
  page-scoped enumeration; paired-byline partnership ads do appear.
- No CAPTCHA or challenge was encountered logged-out at human rate across nine
  probe runs; that is bounded observation, not an anti-bot guarantee.
- Media assets (video/image files) are not preserved by this route — viewport
  screenshot only.

## Probe Receipts

First probe: Summer Fridays, 2026-07-26. Nine admitted packets in
`C:\tmp\forseti-sf-meta-ads-discovery-20260726\data`; return artifact at
`docs/research/summer_fridays_ci_inputs_20260726/meta_ad_library_capture_return.md`.
Observed: 185 unique US active IDs (exhausted), 11 FR all-status IDs
(exhausted, 4 inactive with date ranges), DE empty with passing control.

**Cold-receiver validation, 2026-07-26.** A receiver with no prior context was
given only this card and asked to capture `country=IT`. It completed the
capture in **one run, no retries, no CAPTCHA**: packet
`01KYFK6EHXRCZ5C9VKTZ4APXGH`, 11 unique IDs against a declared "~16 results",
footer-terminal, 4 inactive with date ranges, 6 EU-transparency sections,
manifest hashes verified, IDs fully disjoint from the FR set. The URL grammar,
run parameters, Meta rewrite behavior, `Library ID:` anchor, and exhaustion
criterion all held as written. Its audit produced the PowerShell command block,
the `--data-root` / `--source-surface` / `--decision-question` authoring notes,
the declared-count extraction recipe, and the correction to false-diagnosis #7
now present above. **Per-market counts are genuinely per-market**: IT and FR
each return 11 distinct ads with zero overlap.
