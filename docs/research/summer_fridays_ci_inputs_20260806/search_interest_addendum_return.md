# Summer Fridays Search-Interest Addendum Return — 2026-08-06

```yaml
retrieval_header_version: 1
artifact_role: One-shot Google Trends addendum capture return (Deliver target-screen input)
scope: >
  Return of the bounded 2026-08-06 Google Trends addendum commissioned to
  answer two questions the 2026-08-05 capture could not: (A) is Summer
  Fridays' post-2024 attention decline brand-specific or category-wide, and
  (B) do the destination head-to-heads survive under Shopping-property
  search. Relative search attention only.
use_when:
  - Reading the category-vs-brand trajectory verdict for the Summer Fridays Deliver target screen.
  - Reading the Shopping-property check on the 2026-08-05 destination head-to-heads.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_series.json
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md
stale_if:
  - A newer Summer Fridays search-interest pull supersedes this addendum.
  - The Summer Fridays Deliver run this feeds is completed or re-commissioned.
```

- Commission:
  `docs/prompts/handoffs/summer_fridays_search_interest_addendum_capture_handoff_20260806_v0.md`
  (bounded owner authorization for exactly one one-shot addendum pull,
  2026-08-06).
- Status: **COMPLETE — all 6 pulls captured** (the lip Shopping pull landed
  12:04:57 UTC on the third round of an owner-instructed 1/minute retry).
  Batch cap honored: 5 term-set batches per the handoff (batch 5 spare:
  **unused**).
- Raw root: `C:\tmp\forseti-sf-search-interest-discovery-20260806\data`
  (verbatim API bodies + sha256/UTC receipt manifest; outside Git).
- Machine-readable series:
  `docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_series.json`
  — mirrors the 2026-08-05 record shape and **adds a `property` field**
  (`web_search` | `shopping`); this is the shape delta for the schema
  bootstrap.
- Value semantics: Google Trends **0–100 relative index normalized to each
  batch's peak**. Not counts, sales, demand size, prevalence, or share. This
  addendum is a **separate normalization** from the 2026-08-05 pull;
  cross-pull comparison goes only through the shared anchor term
  ("summer fridays lip butter balm") and is approximate.

## 1. Executive conclusion (three findings, relative attention only)

1. **Part A verdict — brand-specific decline.** Against the commissioned
   decision rule: every captured category curve is rising through 2026 in
   both geos while the Summer Fridays brand curve (2026-08-05 capture)
   declines from its 2024 peak. US yearly means: "skin tint" 9.1 → 15.1 →
   35.0 (2024 → 2025 → 2026 YTD), "tinted sunscreen" 7.1 → 8.9 → 21.5,
   "lip balm" 32.1 → 32.1 → 50.3, "lip oil" 14.8 → 11.7 → 22.1, "lip
   butter" 2.2 → 2.5 → 6.3. Worldwide agrees. The categories are rising or
   holding; none is deflating. **The prize is growing while the brand's
   share of attention shrinks — and the tint category the brand just entered
   is the fastest-growing curve captured.**
2. **Part B outcome — inconclusive-below-threshold on both axes.** As
   pre-stated in the handoff, Shopping-property volume is thin: every term
   in both head-to-heads is below or intermittently below the reporting
   threshold (93–99% zero weeks). The sparse non-zero weeks order Ilia
   (peak 100) > Saie (45) > Hourglass (39) ≫ SF Sheer Skin Tint (15) on the
   tint side, and Laneige (100) > Aquaphor (45) > anchor (29) > Rhode (27) >
   Lanolips (10) on the lip side — directionally consistent with the
   web-search reads, but a bound, not a finding. The purchase-leaning check
   neither confirms nor contradicts the destination reads.
3. **The anchor is a category minnow.** On category scales the anchor term
   "summer fridays lip butter balm" never exceeds 5% of the category peak
   (yearly means ≤ 1.3). This is expected — a brand-product term against
   head terms — and is why the Part A read rests on **category curve shape**,
   not anchor levels. It also bounds cross-pull anchor bridging on these
   batches as weak.

## 2. Capture-parameter receipt per batch

Frozen for all pulls: window `today 5-y` (262 weekly points), category
filter 0, tz `-480`, capture host = Google Trends web endpoints in-page
(banked browser-route method), capture date 2026-08-06 UTC. Two same-day
sessions: app-embedded pane and the owner's real Chrome (per-file
`capture_session` in the raw-root manifest).

| Pull | Family | Terms | Geo | Property | Captured (UTC) | sha256 (12) |
| --- | --- | --- | --- | --- | --- | --- |
| a1_us | Lip category vs brand | lip balm, lip mask, lip butter, lip oil, anchor | US | web | 10:22:36 | 9d3a8da19ec8 |
| a1_ww | Lip category vs brand | same | Worldwide | web | 10:47:10 | 8331b2f3541e |
| a2_us | Tint category vs brand | skin tint, tinted sunscreen, tinted moisturizer, anchor | US | web | 10:30:04 | 8e92a1155a4a |
| a2_ww | Tint category vs brand | same | Worldwide | web | 11:37:56 (real Chrome) | 0ef3eb571fde |
| b3_us_shop | Lip head-to-head | anchor, laneige lip sleeping mask, rhode peptide lip treatment, aquaphor lip repair, lanolips | US | shopping | 12:04:57 (real Chrome) | 9a08a3e567d2 |
| b4_us_shop | Tint head-to-head | sf skin tint, ilia skin tint, saie slip tint, hourglass skin tint, anchor | US | shopping | 10:45:39 | f7aea90308c3 |
| (5) spare | — | — | — | — | **unused** (no Part A ambiguity demanded it) | — |

## 3. Category trajectory read (Part A)

Yearly means (completed weeks; 2026 = YTD through early August) and
half-over-half (first 130 vs last 131 completed weeks):

**Lip category — US (a1_us):**

| Term | 2022 | 2023 | 2024 | 2025 | 2026 YTD | h1 → h2 | Shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lip balm | 19.0 | 24.1 | 32.1 | 32.1 | 50.3 | 21.4 → 36.0 | Rising, accelerating |
| lip mask | 5.2 | 6.1 | 7.7 | 6.1 | 9.5 | 5.4 → 7.5 | Rising with a 2025 dip |
| lip butter | 1.1 | 2.0 | 2.2 | 2.5 | 6.3 | 1.5 → 3.3 | Rising, 2026 acceleration |
| lip oil | 9.4 | 14.6 | 14.8 | 11.7 | 22.1 | 11.1 → 15.1 | Rising with a 2025 dip |

**Tint category — US (a2_us):**

| Term | 2022 | 2023 | 2024 | 2025 | 2026 YTD | h1 → h2 | Shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| skin tint | 4.4 | 6.1 | 9.1 | 15.1 | 35.0 | 4.9 → 17.4 | Rising steeply every year |
| tinted sunscreen | 5.2 | 6.6 | 7.1 | 8.9 | 21.5 | 5.3 → 11.1 | Rising, 2026 acceleration |
| tinted moisturizer | 9.7 | 10.3 | 9.5 | 10.3 | 19.4 | 9.4 → 12.1 | Flat-to-rising |

Worldwide checks (a1_ww, a2_ww) show the same shapes with steeper rises
(worldwide "skin tint" 13.1 → 21.1 → 43.1; "lip balm" 44.1 → 50.9 → 64.9).
No captured category term deflates 2024 → capture date.

**Verdict against the commissioned decision rule:** SF brand curve declining
(2026-08-05 capture: US all-categories 36.8 → 33.2 → 29.0; Beauty-only
39.0 → 29.9 → 23.5) while every category curve rises or holds →
**brand-specific decline.** Not mixed; no forcing was needed. Caveats: 2026
values are YTD means (part-year), and category-term seasonality differs from
the brand's (e.g., "tinted sunscreen" summer-peaks; "lip balm"
winter-peaks); the year-over-year direction is consistent across every full
year, so the verdict does not rest on the partial year.

## 4. Shopping head-to-head (Part B)

**Tint (b4_us_shop, captured):** all five terms below or intermittently
below the reporting threshold — this pull is primarily a null ledger (§5).
Sparse non-zero weeks (mostly 2025–2026): Ilia peak 100 / h2 mean 4.0 >
Saie 45 / 1.9 > Hourglass 39 / 1.1 ≫ SF Sheer Skin Tint peak 15 with 99% of
weeks at zero; the anchor registers (peak 46, h2 2.4). **Outcome:
inconclusive-below-threshold.** The sparse ordering is directionally
consistent with the web-search head-to-heads and is reported as texture
only, not a finding.

**Lip (b3_us_shop, captured):** same pattern — every term below or
intermittently below the reporting threshold (93–96% zero weeks). Sparse
non-zero weeks (mostly 2025–2026): Laneige Lip Sleeping Mask peak 100 / h2
mean 3.2 > Aquaphor Lip Repair 45 / 1.9 > anchor Lip Butter Balm 29 / 1.5 >
Rhode Peptide Lip Treatment 27 / 1.0 > Lanolips 10 / 0.5. **Outcome:
inconclusive-below-threshold**, with the sparse ordering directionally
consistent with the web-search head-to-heads (Laneige leads; the anchor
sits mid-pack among the rest) — texture, not a finding.

**Part B combined outcome: inconclusive-below-threshold on both axes.** The
purchase-leaning check neither confirms nor contradicts the web-search
destination reads; it bounds them.

## 5. Threshold and null ledger

Exact phrasing applies: each row is **below the Google Trends reporting
threshold under the recorded geo/window** for the flagged share of weeks —
threshold artifacts, not absence of interest.

| Term | Pull (geo/property) | Status |
| --- | --- | --- |
| summer fridays lip butter balm | a1_us, a1_ww, a2_us, a2_ww (web) | intermittently below threshold (69–86% of weeks 0) — expected against category head terms |
| summer fridays skin tint | b4_us_shop (US/shopping) | 99% of weeks 0 |
| ilia skin tint | b4_us_shop | 93% of weeks 0 |
| saie slip tint | b4_us_shop | 96% of weeks 0 |
| hourglass skin tint | b4_us_shop | 96% of weeks 0 |
| summer fridays lip butter balm | b4_us_shop | 93% of weeks 0 |
| summer fridays lip butter balm | b3_us_shop (US/shopping) | 93% of weeks 0 |
| laneige lip sleeping mask | b3_us_shop | 93% of weeks 0 |
| rhode peptide lip treatment | b3_us_shop | 96% of weeks 0 |
| aquaphor lip repair | b3_us_shop | 94% of weeks 0 |
| lanolips | b3_us_shop | 96% of weeks 0 |

No all-zero rows in captured pulls.

## 6. Failure and omission ledger

1. All 2026-08-05 access-route conditions recurred: `USER_TYPE_SCRAPER` on
   every session (including the owner's real Chrome), `widgetdata` 429s
   after 1–2 successes per quiet period, drip-recovery thereafter. Fresh-day
   quota gave the first pull (a1_us) instantly, consistent with the banked
   method's expectations.
2. **b3_us_shop (lip Shopping) was the day's straggler and ultimately
   landed**: blocked through paced attempts + 150s-cooloff retries in two
   sessions and ~10-minute finisher rounds, then captured at 12:04:57 UTC on
   the **third round of an owner-instructed 1/minute retry** in the
   real-Chrome session. Extraction hit one new obstacle: Chrome silently
   blocked the session's second programmatic download (multiple-downloads
   permission) until the owner allowed it; the raw body stayed safely in
   page memory meanwhile. Cut list: **none** — the addendum is complete.
3. Spare batch 5: **unused** — no Part A category ambiguity demanded a
   confirming cut.
4. Owner-instructed deviation from banked pacing: the 1/minute b3 retry
   burst (owner instruction, 2026-08-06, this lane) is faster than the
   banked method's recovered-cadence guidance; recorded here and in §7.
5. Workspace deviation: as with the 2026-08-05 run, the receiver worktree
   already carried the (untracked, unlanded) 2026-08-05 deliverables and the
   2026-08-06 handoff pair; only the two addendum return artifacts were
   added by this run.

## 7. Method lessons for the refinement lane

1. **Shopping property (`property: "froogle"`) works identically through the
   same explore → widgetdata route** — same token scheme, same multiline
   shape, same quota pool as web-search pulls (429s hit both alike). No
   separate endpoint behavior observed.
2. **Shopping data is sparse and appears right-truncated**: in b4_us_shop
   every term reads zero for the final ~5–7 weeks despite non-zero spikes
   weeks earlier — consistent with reporting lag on the Shopping property.
   Treat trailing Shopping weeks as unreliable; do not read them as decline.
3. **Fresh-day quota confirmed**: first pull of the day succeeded instantly
   on the same IP that ended 2026-08-05 hard-blocked — overnight reset is
   real and worth planning around (schedule pulls early, priorities first).
4. **Category head terms vs brand terms in one batch**: workable, but the
   brand anchor pins near zero (≤5% of batch peak), making anchor bridging
   weak; if a future pull needs strong bridging to category scales, use an
   intermediate-volume bridge term instead of a brand-product term.
5. **1/minute retries landed a success on the third attempt** in one
   observed case (owner-instructed experiment, §6.2/§6.4) where slower
   ~10-minute rounds had failed for ~40 minutes prior. One case is not a
   cadence rule, but it suggests the quota's recovery moments are short
   windows that slow polling can miss — worth one bounded fast-poll
   experiment in a future run before it is banked as method.
6. **Chrome blocks a tab's second programmatic download by default**
   (multiple-downloads permission). For real-Chrome bundle extraction:
   either bundle everything into one download at session end, or have the
   operator pre-allow multiple downloads for trends.google.com.

## 8. Non-claims

- No sales, demand-size, prevalence, share, or population claims; all values
  are batch-normalized relative indices.
- The Part A verdict is about **search attention composition**: it says the
  categories' attention grows while the brand's declines; it does not say
  why, and it does not measure revenue or units.
- Shopping-property results bound, and do not confirm or deny, purchase
  intent; the tint Shopping check is inconclusive-below-threshold.
- Cross-pull comparisons to the 2026-08-05 capture are approximate and go
  only through the shared anchor; on these category batches the anchor is
  near-threshold, so such bridging is weak (§1.3).
- Nothing here reopens the sealed Phase A corpus or amends the 2026-08-05
  artifacts, which remain read-only beside this addendum.

## Validation

- Fresh-read of both written artifacts: performed after final write (see
  delivery message for check results).
- Every series record names its raw export and sha256; resolution verified
  at build time against the raw-root manifest.
- Counts recomputed from the series file: 28 records across all 6 pulls.
