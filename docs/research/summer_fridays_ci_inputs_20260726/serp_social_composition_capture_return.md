# Summer Fridays SERP-to-Social Composition Capture Return — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Capture return artifact
scope: >
  Acquisition return for the Summer Fridays Google SERP composition board and
  its bounded platform-native follow-through. Reports captured search-surface
  composition as counts of observed result cards, the route and locality
  receipt, existing-lake reuse decisions, and the native follow-through
  selection ledger. Supplemental acquisition input for later Deliver-side CI.
use_when:
  - Reading what Google Search surfaced for Summer Fridays on 2026-07-26.
  - Deciding which social results merit platform-native verification.
  - Planning the Deliver-side join without re-running the search capture.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/handoffs/summer_fridays_serp_social_composition_capture_handoff_20260726_v0.md
  - docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
stale_if:
  - Google Search parameters, AI Overview, result-card, or social-index behavior materially changes.
  - The composition lake is recaptured or superseded.
  - A dedicated Forseti SERP composition runner supersedes this route.
  - Platform-native follow-through completes and supersedes the selection ledger.
```

## 1. Executive Acquisition Conclusion

Fourteen Google SERP composition packets were captured on 2026-07-26 through the
bound US-parameterized, logged-out route, plus one network-egress observation
packet. All fourteen returned source-useful rendered result surfaces; none were
blocked. Combined with one reused packet from the existing discovery lake, the
frozen 15-job query board is complete.

Normalized extraction produced **391 typed result cards** across the fourteen
fresh packets. The dominant observation is structural: across every job on the
board, **Google's own synthesis modules and creator-social sources occupy more
result cards than the brand's official properties or its retailers do**. Official
brand cards appear at a count of 1–3 per query on every query where they appear
at all. That is a mediation observation about this captured surface, not a
market measurement.

Platform-native follow-through verified three selected YouTube items and
preserved typed blockers for the selected TikTok and Instagram routes. The
YouTube packets verify source identity and source-native framing; they do not
turn creator or retailer statements into product truth. The platform outcomes
and route blockers are recorded in sections 10–12.

**US-parameterized is not physically US-local.**

## 2. Route And Locality Receipt

- **Route:** US-parameterized, logged-out-visible Google Search, per
  `docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md`.
- **URL parameters:** `hl=en`, `gl=us`, `pws=0` on every request.
- **Runner:** `forseti-harness/runners/run_source_capture_cloakbrowser_packet.py`
  (CloakBrowser rendered snapshot: DOM, visible text, viewport screenshot,
  snapshot metadata).
- **Session posture:** no stored Google session; logged-out.
- **Observed egress:** packet `01KYEZGMDV4EVD39Z6KTPE2Z8F` recorded
  `country: SG` (Singapore, residential fixed-line ISP) at run start. **No proxy
  or VPN profile was requested or loaded.** The proxy/VPN path is an explicit
  escalation under the route decision and this commission did not require
  physical locality, so the default parameterized-only route was used.
- **Google-reported locality:** the rendered SERP footer reported that location
  could not be determined, on every captured query.
- **Query rewriting:** none. Requested and rendered query matched on all 14.
- **Scroll/pagination depth:** single rendered viewport pass, no scroll passes
  and no pagination. Page-2+ results were not requested and are not represented.
- **Asset posture:** the CloakBrowser route blocked image, media, and font
  network resources to bound bandwidth. Thumbnail and image-only evidence is
  therefore not preserved.

### Route non-claims

- **US-parameterized is not physically US-local.** Observed egress was Singapore.
- Google did not return, and this capture does not represent, what a
  physically US-located user would see.
- One capture is composition at a moment: not complete, stable, representative,
  or a prevalence measure.
- Result order is observed source state only. No demand or importance is
  inferred from rank.

### Route efficacy observation

The parameterized-only route returned a source-useful surface on **14 of 14**
attempts. In the prior discovery run retained in the existing lake, the
US-egress (VPN) comparison batch drew Google unusual-traffic interstitials on
**2 of 8** attempts. This is consistent with the route decision's finding that
proxy/VPN should not be the default, and is offered as route evidence only — not
as a general reliability rate. The interstitial bodies carry visible exit-IP
strings; they remain in the raw lake and are deliberately withheld here.

## 3. Existing-Lake Inventory And Reuse Decisions

`C:\tmp\forseti-sf-social-search-discovery-20260726\data` was verified with
`run_data_lake_doctor.py`: **19/19 raw packets verified, 0 read failures, 0 stale
or orphan availability entries, lake epoch v4.1**.

Inventory: 19 packets, two runs on 2026-07-25 — Run A (18:57–19:02, 10 packets:
2 `anti_blocking_http` attempts classified `content_unverified`, then 8
CloakBrowser) and Run B (20:21–20:24, 9 packets: 1 egress check + 8 CloakBrowser
repeats of the same 8 queries under owner-asserted US VPN).

Because the lake is one day old, **currentness was not a recapture
justification**. Recapture was decided on question fidelity against the frozen
board.

| Board job | Lake state | Decision |
| --- | --- | --- |
| 1 `site:tiktok.com "summer fridays"` | exact normalized-query match | **Reuse** `01KYDF25SK6XZ4AG7EAA8J6D03` (Run B) with `01KYDAC0HAY9MQ6DDS3D05YS52` (Run A) as second observation |
| 2, 3 | lake queries are *broader* (no `reel` / `review` term) | **Capture board wording; retain lake packets as complements**, not duplicates — different queries |
| 5, 6 | lake used unquoted `lip butter balm` | **Capture** — quoting changes recall and reproducibility |
| 7 | lake used `summer fridays vs laneige` | **Capture** — the board's open `vs` reveals which competitors Google surfaces rather than presupposing one |
| 15 | lake used `site:tiktok.com "summer fridays" shop` | **Capture** — the board's open form reveals who mediates the TikTok Shop question; a site-restricted query structurally cannot |
| 4, 8, 9, 10, 11, 12, 13, 14 | no lake coverage | **Capture** |

Net: 14 fresh captures, 1 reuse, 2 complementary lake packets retained.

The lake also holds an off-board query, `summer fridays official tiktok account`
(`01KYDF5PXVR662VB02V9AX43HQ`, 25 cards), retained as identity-job context.

### Complement caveat

The intended job-3 complement `01KYDF37A185SS84YRAC8CBM7F` (broad
`site:youtube.com "summer fridays"`, Run B) is **not usable as content**: it is a
Google unusual-traffic interstitial, not a result surface. It is recorded as a
typed route failure. The job-2 complement `01KYDF2MEWFS9YE64FSG32VNSC` (16 cards)
is source-useful.

## 4. Query-Board Completion Matrix

| Job | Query | Packet ID | Cards | AI Overview | Canonical URLs source-visible |
| --- | --- | --- | --- | --- | --- |
| 1 | `site:tiktok.com "summer fridays"` | `01KYDF25SK6XZ4AG7EAA8J6D03` (reuse) | 19 | no | 11 |
| 2 | `site:instagram.com "summer fridays" reel` | `01KYEZJBV1XX9GRQ86AJDQ2TWN` | 19 | no | 12 |
| 3 | `site:youtube.com "summer fridays" review` | `01KYEZM24WHGM9HM2MEP4F8EQC` | 20 | no | 12 |
| 4 | `"summer fridays" review` | `01KYEZMNHJ1TECF5B3VS65SK50` | 26 | yes | 7 |
| 5 | `"summer fridays" "lip butter balm" review` | `01KYEZN9JTGN2NFQ4JJE4SP0GG` | 26 | yes | 0 |
| 6 | `"summer fridays" "lip butter balm" burning OR reaction` | `01KYEZNWVFNTA7ZGXBS7ZYYQKX` | 24 | yes | 8 |
| 7 | `"summer fridays" "lip butter balm" vs` | `01KYEZPFBK98NMDGRAJCENMFFB` | 35 | no | 18 |
| 8 | `"summer fridays" "jet lag mask" review OR reaction` | `01KYEZQ1TY8KGPN4SFR65T2QR7` | 26 | no | 6 |
| 9 | `"summer fridays" "sheer skin tint" review` | `01KYEZQNQ7M85FNN41ETA00BC9` | 25 | yes | 6 |
| 10 | `"summer fridays" "flushed lip stain" review` | `01KYEZRBT44ATC5MDWDCT8TK2T` | 23 | yes | 8 |
| 11 | `"summer fridays" "cloud dew" OR "rich cushion" review` | `01KYEZS027WTWEJG70BA5DXA8M` | 34 | no | 10 |
| 12 | `"summer fridays" body fragrance review` | `01KYEZSK4SZ1RNDH1CY2KF8Q7B` | 36 | no | 18 |
| 13 | `"summer fridays" sephora review` | `01KYEZT68QMTEE705XCG7CKPSX` | 36 | no | 19 |
| 14 | `"summer fridays" amazon review` | `01KYEZTS8Z1X242QHJ91JB1HW4` | 33 | no | 16 |
| 15 | `"summer fridays" tiktok shop` | `01KYEZVC6HK8S4CR9JVW7MMD2J` | 28 | no | 7 |

15/15 board jobs resolve to a retained packet. Card counts are counts of
extracted result cards in that one capture.

## 5. Per-Query Composition

Modules observed per query (card counts within that query):

| Job | organic | video block | People Also Ask | related search | forum block |
| --- | --- | --- | --- | --- | --- |
| 2 | 5 | 14 | — | — | — |
| 3 | 1 | 19 | — | — | — |
| 4 | 9 | 5 | 4 | 8 | — |
| 5 | 9 | 4 | 4 | 8 | 1 |
| 6 | 7 | 4 | 4 | 8 | 1 |
| 7 | 9 | 13 | 4 | 8 | 1 |
| 8 | 10 | 4 | 4 | 8 | — |
| 9 | 8 | 4 | 4 | 8 | 1 |
| 10 | 10 | 5 | — | 7 | 1 |
| 11 | 13 | 9 | 4 | 8 | — |
| 12 | 12 | 14 | 4 | 8 | 1 |
| 13 | 12 | 14 | 4 | 8 | 1 |
| 14 | 12 | 9 | 4 | 8 | — |
| 15 | 5 | 8 | 8 | 8 | — |

Every open (non-`site:`) query carried a People Also Ask and/or related-search
block of Google-generated text. The two `site:`-restricted queries carried
neither.

## 6. Cross-Query Source And Platform Composition

Reported **per query**, as counts of observed result cards. These are deliberately
not pooled into a single cross-board total: a pooled number reads as prevalence
regardless of labelling, and this lane may not report prevalence or share.

| Job | official brand | retailer | creator social | community | Google synthesis | other publisher |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 0 | 17 | 0 | 0 | 2 |
| 3 | 0 | 0 | 19 | 0 | 0 | 1 |
| 4 | 1 | 1 | 3 | 1 | 12 | 8 |
| 5 | 1 | 2 | 3 | 1 | 12 | 7 |
| 6 | 3 | 0 | 4 | 2 | 12 | 3 |
| 7 | 1 | 0 | 13 | 2 | 12 | 7 |
| 8 | 1 | 2 | 3 | 0 | 12 | 8 |
| 9 | 2 | 2 | 3 | 0 | 12 | 6 |
| 10 | 2 | 1 | 4 | 1 | 8 | 7 |
| 11 | 2 | 3 | 4 | 0 | 12 | 13 |
| 12 | 2 | 1 | 14 | 2 | 12 | 5 |
| 13 | 1 | 2 | 14 | 2 | 12 | 5 |
| 14 | 1 | 7 | 9 | 0 | 12 | 4 |
| 15 | 1 | 1 | 9 | 0 | 16 | 1 |

**Counts only. Not prevalence, share of voice, market share, or importance.**

## 7. Product And Problem Coverage

Counts of cards mentioning each product family, per query. The board was
deliberately unanchored from any single launch, and coverage confirms the
portfolio breadth is observable rather than hero-only:

| Job | Dominant family (card count) | Also present |
| --- | --- | --- |
| 5 | lip butter balm (13) | lip oil/gloss (2) |
| 6 | lip butter balm (12) | jet lag mask (1), body/fragrance (1) |
| 7 | lip butter balm (18) | lip oil/gloss (1) |
| 8 | jet lag mask (24) | body/fragrance (1) |
| 9 | sheer skin tint (21) | — |
| 10 | flushed lip stain (21) | — |
| 11 | cloud dew (18), rich cushion (10) | jet lag mask (1) |
| 12 | body/fragrance (24) | lip butter balm (2) |
| 13 | lip butter balm (9) | lip oil/gloss (3), jet lag mask (1) |
| 14 | lip butter balm (7) | lip oil/gloss (4), flushed lip stain (1) |

Each non-hero product family (jet lag mask, sheer skin tint, flushed lip stain,
cloud dew, rich cushion, body/fragrance) has its own observable review surface.
Product-specific pain observed on job 6 stays bound to the Lip Butter Balm and
is **not** generalized to the brand.

## 8. Official / Retailer / Community / Creator Mediation Map

Read from section 6, the captured mediation shape is:

- **Identity and channel jobs (2, 3):** effectively wholly creator-social.
  Official brand accounts appear as individual cards but do not dominate the
  surface for their own brand-name queries.
- **Comparison job (7):** creator-social heavy (13 cards). The competitor set
  Google surfaced, by count of cards mentioning each: Laneige 8, Rhode 4,
  Glossier 1, e.l.f. 1, Topicals 1. The board's open `vs` form produced this
  set; the prior lake query presupposed Laneige and could not have.
- **Retailer-journey jobs (13, 14):** on the Sephora query, creator-social
  cards (14) outnumber retailer cards (2), and the top displayed domains are
  `instagram.com` (7) and `tiktok.com` (6) ahead of `sephora.com` (2). The
  Amazon query is the only job on the board where retailer cards (7) approach
  creator-social (9).
- **Google as mediator:** People Also Ask plus related searches contribute a
  consistent 8–16 Google-authored cards on every open query. On the TikTok Shop
  job (15) Google synthesis (16) is the largest single class.
- **Official brand presence is thin and flat** — 1–3 cards on every query where
  present, never the largest class on any job.

This describes the captured surface. It does not establish why, and does not
support a claim about the brand's actual search performance.

## 9. AI Overview And Google Synthesis

AI Overview was present on **6 of 14** captured queries: jobs 4, 5, 6, 9, 10 and
(per module detection) not on the `site:`-restricted or most portfolio queries.

Cited-source labels visible in the AI Overview panels, by job:

| Job | Visible cited-source labels |
| --- | --- |
| 4 | Live That Glow (+4, +5), Camille Styles (+4), Rachel's Edit (+3), Reddit |
| 5 | Reddit, Instagram, YouTube, Michael Park MD (+2), Holly Ward (+3), Lydia Emily |
| 6 | Reddit (+1) |
| 9 | Reddit (+7), BeautyCrew.com.au (+3), Summer Fridays (+4) |
| 10 | Reddit, Instagram, YouTube, Sephora, Milana Bajic (+4, +5) |

Reddit is a visible cited source in every AI Overview captured. The full
synthesis prose is preserved in the raw packets and is deliberately not
reproduced here.

**Non-claims.** AI Overview, People Also Ask, related searches, and snippets are
Google mediation and synthesis. They are **not** independent corroboration of the
sources they summarize. No ingredient, efficacy, prevalence, or
consumer-consensus statement from an AI Overview is promoted to fact in this
artifact. The `+N` markers indicate additional cited sources Google did not
expose by name in the rendered surface.

## 10. Native Follow-Through Selection Ledger

**Status: partial by source, contract-complete.** Three selected YouTube items
were captured natively. The selected TikTok and Instagram items have typed
pre-source blockers; their Google rows remain discovery/mediation evidence only.
The cap remains six items per platform.

Candidates with source-visible canonical URLs: **Instagram 44, YouTube 27,
TikTok 27**.

Selection and outcome ledger:

| Platform | Selected item | Leverage rationale | Native outcome |
| --- | --- | --- | --- |
| Instagram | `instagram.com/summerfridays/` | official identity anchor | **Blocked before source access.** A separate `chowdakr_sg_instagram` state was required; the permitted manual-login bootstrap could not be launched with its required visible helper terminal in this execution environment. No TikTok state was reused and no Instagram auth state was created. |
| TikTok | `@marinabarnoo/video/7381649202134207786` | specific Lip Butter Balm burning/reaction claim from job 6 | **Blocked before source access.** `chowdakr_sg_tiktok` validated, but resolves to `chrome_cdp`; the packet runner rejects non-CloakBrowser backends as diagnostic-only and forbids the diagnostic override with a session profile. |
| TikTok | `@alejayofficial/video/7531929760675466526` | visible e.l.f. price-comparison mechanic | **Blocked by the same Chowdakr/backend admission mismatch.** |
| TikTok | `@jess.einaudi/video/7427497483489561902` | Rhode competitor pair surfaced independently | **Blocked by the same Chowdakr/backend admission mismatch.** |
| TikTok | `@marewiththehair/video/7482167773292989727` | dominant Laneige comparison pairing | **Blocked by the same Chowdakr/backend admission mismatch.** |
| YouTube | Holly Ward, `aJNT3Mo6hHg` | Lip Butter Balm range review cited inside Google's job-5 synthesis | **Verified** by packet `01KYF0S4G76GFXC2NB7PQBKCJK`: playable, Holly Ward channel identity, title/description preserve range-review framing, 2,715 observed views, 32 observed likes, and 4 sampled comments from 2 pages. The description also preserves a Summer Fridays discount-code mechanic. |
| YouTube | Space NK, `5s1fZlH22dM` | retailer-operated Flushed Lip Stain review; under-covered family | **Verified** by packet `01KYF0SJBF7V8WCXH1BYG446SF`: playable, Space NK channel identity, title preserves a six-hour wear-review framing, 3,807 observed views, 47 observed likes, and 1 sampled comment. |
| YouTube | Gorgeously Aging, `mPjJwVDTrjE` | independent Sheer Skin Tint review; under-covered family | **Verified** by packet `01KYF0SNVTX99FKCFGBPW3DMZV`: playable, Gorgeously Aging channel identity, title and creator-pinned comment preserve the light-coverage/hydration/oily-skin qualification, 456 observed views, 8 observed likes, and 1 sampled comment. |

The YouTube route retains selected source-visible metadata and bounded comments,
not video bytes, complete comment graphs, transcripts, or the enclosing served
responses. Counts are capture-time observations, not popularity comparisons.

Rejection reasoning to preserve: rank alone was not used; official brand
re-posts of the same asset were treated as one identity item; and the
VaynerMedia Instagram result was rejected as an entity mismatch (section 12).

## 11. Independent-Source And Dependency Ledger

Every extracted card carries a dependency label:

- `google_composition_primary` — the card is primary evidence of what Google
  composed. Applies to organic, retailer, and publisher cards.
- `google_synthesis_only` — AI Overview, People Also Ask, related searches.
  Google-authored; not evidence of any underlying source.
- `platform_native_unverified` — a TikTok/Instagram/YouTube card observed only
  as a Google-indexed result. This remains the default for unselected social
  rows; the snippet is Google's rendering, which may be stale or partial.
- `platform_native_verified` — the three selected YouTube rows in section 10,
  each bound to its platform packet.
- `platform_native_blocked` — the selected Instagram identity row and four
  selected TikTok rows in section 10.

Only the YouTube items' source identity and retained source-native framing are
verified. Their product statements are attributed source claims, not product
truth. No TikTok or Instagram content claim is verified.

## 12. Failures, Omissions, Quiet Leads, And Misleading Matches

**Route failures.** None in this run: 14/14 captures returned result surfaces.
Two packets in the *prior* lake's US-egress batch
(`01KYDF37A185SS84YRAC8CBM7F`, `01KYDF57N11JDZECXARTXPFEPF`) are unusual-traffic
interstitials. Their bodies contain visible exit-IP strings and are retained in
the raw lake only, withheld from this artifact per the route decision.

**Canonical URLs not source-visible.** On AI-Overview-heavy SERPs Google serves
result links as opaque `/goto?url=<encrypted>` redirects whose payload is not a
decodable URL. Canonical destinations were recoverable for **147 of 391** cards.
Job 5 recovered **zero**. Affected rows record the absence and its reason; no URL
was reconstructed or inferred.

**Coverage omissions.** Single viewport pass only — no scroll, no pagination,
page 2+ not represented. Images, media, and fonts were blocked at the network
layer, so thumbnail and image-only SERP evidence is absent. The SERP pass
captured no comment bodies; the three native YouTube packets later retained
bounded selected comment rows.

**Misleading match.** One entity collision: a VaynerMedia Instagram reel
("Summer Fridays > Winter Fridays") uses *summer fridays* as the workplace
scheduling concept, not the brand. Retained as a typed misleading match, excluded
from brand mediation reasoning.

**Stage 2 blocker — TikTok Shop US egress gate.** Commit `878c263b` added a gate
to `tiktok_capture_lane_spec_v0.md` requiring the browser context to freshly
observe US country egress before **each** access session to the bounded TikTok
Shop US surface, and to stop if US egress is absent. Observed egress for this
machine is **SG**. Any Stage 2 TikTok Shop access therefore requires its own
fresh egress observation and, absent US egress, must stop. The egress check
recorded in section 2 does **not** satisfy that gate: it is a different session
and a different surface.

**Selected TikTok blocker — Chowdakr/backend admission mismatch.**
`check_source_capture_session_profile.py --session-profile
chowdakr_sg_tiktok` passed with validated auth state, `chrome_cdp`, a configured
persistent profile, required `no_proxy_profile_loaded` posture, and no exposed
secret values. The current arbitrary-video packet runner then failed closed
before browser launch: its packet-grade guard accepts CloakBrowser only, while
session-profile mode supplies `chrome_cdp` and prohibits the diagnostic-backend
override. No TikTok page was contacted and no packet was admitted. This is a
runner/profile compatibility blocker, not evidence that any selected item is
unavailable.

**Selected Instagram blocker — manual-login bootstrap boundary.** No registered
Instagram state existed. The separate labels `chowdakr_sg_instagram` and
`chowdakr_sg_instagram_cloak_v1` were reserved conceptually; TikTok state was
not reused. The current bootstrap requires a visible browser plus a human Enter
signal after login, but this execution environment blocked launching the
required visible helper process before browser start. No credentials were
entered, no Instagram auth state was written, and the official profile was not
claimed as natively verified.

**Quiet leads.** Cloud Dew and Rich Cushion (job 11) drew the highest
other-publisher count on the board (13) with only 4 creator-social cards — an
inverted mediation shape versus every other product query. Not interpreted here.

## 13. Source Evidence Bundle

**New composition lake:** `C:\tmp\forseti-sf-serp-social-composition-20260726\data`
(root UUID recorded in `.forseti-data-root`, lake epoch v4.1). 18 packets:
1 egress observation + 14 CloakBrowser SERP packets + 3 YouTube native packets.
SERP packet IDs are listed per job in section 4; the egress packet is
`01KYEZGMDV4EVD39Z6KTPE2Z8F`; YouTube packet IDs are listed in section 10.

**Existing discovery lake:** `C:\tmp\forseti-sf-social-search-discovery-20260726\data`,
19 packets, verified 19/19. Reused and complementary packet IDs are named in
section 3.

**Existing TikTok Shop probe:** `C:\tmp\forseti-summer-fridays-tiktok-shop-continuation-20260726\data`,
5 files, treated as route/coverage context only. It does not prove a full TikTok
Shop grid, PDP, review-body, creator-attribution, or US-local capture.

Each packet carries a `manifest.json` with per-file SHA-256 over stored bytes,
plus an availability-index entry with `manifest_sha256`. Manifest-to-file
verification is reported in section 14.

**Request URL shape** (identical across all 14, differing only in the `q` value).
Job 15 as the worked example:
`https://www.google.com/search?q=%22summer%20fridays%22%20tiktok%20shop&hl=en&gl=us&pws=0`

## 14. Validation, Safe Deliver-Side Uses, And Non-Claims

### Validation results

| Check | Result |
| --- | --- |
| Fresh-read of this artifact before closeout | pass |
| Every board query resolves to a retained packet | pass — 15/15 |
| Every `platform_native_verified` row resolves to a platform packet | pass — 3/3 YouTube rows |
| Counts recomputed from normalized rows | pass |
| Canonical-URL deduplication and dependency labels | pass |
| Raw-lake manifests verified against preserved files | pass — new lake 18/18, existing lake 19/19, via `run_data_lake_doctor.py` |
| `check_search_surface_google_route.py --check <this file>` | pass — 0 findings, inspected this path directly |
| `check_search_surface_google_route.py --strict` | pass — 0 findings |
| `header_index.py --strict` | exit 0, **but vacuous** — see note |
| `header_index.py --health` | pass for this file — not listed under MISSING-HEADER or ORPHAN |
| `check_prompt_output_mode.py --strict` | exit 0, **but vacuous** — see note |
| `git diff --check` | pass — exit 0 |

**Note on the diff-scoped gates.** `header_index.py --strict` and
`check_prompt_output_mode.py --strict` resolve their changed set via
`git diff --name-only <base>...HEAD`. This artifact is uncommitted and `HEAD`
equals `origin/main`, so the three-dot diff is empty and both gates report zero
in-scope files. Their exit-0 results are therefore **not** evidence about this
file and must be re-run once it is committed. To get real header coverage now,
`header_index.py --health` was run across the repository: this file is absent
from both the MISSING-HEADER and ORPHAN lists, so its retrieval header is valid
and its folder is map-covered. The one repository-wide MISSING-HEADER entry
(`docs/hygiene/jb_handoff_registration_integrity_hardening_v0.md`) is pre-existing
and unrelated to this work.

### Safe Deliver-side uses

1. Treat every table here as **counts of observed result cards in one capture**.
2. Use section 8 to decide which consumer questions are creator-mediated before
   weighting retailer-review or Reddit evidence in the join.
3. Use section 10's three YouTube packet bindings as native-source inputs; keep
   the selected TikTok/Instagram and all unselected social rows unverified.
4. Use section 7 to keep product families separate; the job-6 pain is a Lip
   Butter Balm observation only.
5. Use section 9 to identify which sources *Google* elevated, then go to those
   sources — never cite the AI Overview as corroboration.

### Non-claims

- **US-parameterized is not physically US-local.** Observed egress was Singapore.
- Not prevalence, market share, share of voice, demand, or importance.
- Not complete, stable, or representative; one capture at one moment, one
  viewport deep.
- Not a ranking measurement, SEO assessment, content-optimization
  recommendation, keyword-volume study, or standing monitor.
- Not verification of any TikTok or Instagram content claim; for YouTube, only
  the retained source-native identity and framing are verified, not product truth.
- Not the Deliver-side join, and not a CI recommendation.
- Not validation, readiness, buyer proof, Judgment evidence, or Product Lead
  evidence.
