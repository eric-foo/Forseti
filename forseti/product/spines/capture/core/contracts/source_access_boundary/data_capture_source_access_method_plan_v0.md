# Data Capture Source-Access Method Plan v0

```yaml
retrieval_header_version: 1
artifact_role: Product artifact
scope: Method plan comparing candidate source-access methods against the loosened discoverable-or-entitled + disclosable boundary standard and recommending approaches per blocked source. Build authority now comes from the separate bounded source-access tooling authorization decision.
use_when:
  - Evaluating or selecting source-access methods for Orca Data Capture.
  - Scoping a build of source-access tooling after receiving explicit owner authorization for a bounded implementation scope.
  - Checking which methods are in-bounds under the discoverable-or-entitled + disclosable standard.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/README.md
  - forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md
  - forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md
  - forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_commissioning_plan_v0.md
stale_if:
  - The boundary decision is amended or superseded.
  - The obligation contract's Obligation 2 is materially revised.
  - The source-access tooling build authorization is amended or superseded.
  - Pressure-test evidence surfaces access patterns this plan did not anticipate.
```

---

## Status

`ACCEPTED_SOURCE_ACCESS_METHOD_PLAN_V0` — patched 2026-05-30 to reflect the discoverable-or-entitled + disclosable standard with materiality-gated provenance cleanup; patched 2026-06-01 to add API cost/sequence preference without changing boundary permission; patched 2026-06-02 to link the bounded first-tranche source-access tooling build authorization; patched 2026-06-05 to reflect third-tranche anti-blocking authorization, CloakBrowser-first selection, Reddit pre-commercial ordering, old Reddit HTML preference, and `.json` unreliability; patched 2026-06-08 to set exact old Reddit Direct HTTP as the current operator default for supplied thread URLs while retaining CloakBrowser as the primary anti-blocking backend; patched 2026-09-04 to bind existing-entitlement community access without authorizing credential acquisition or community joining.

Artifact type: Product artifact — method plan and build-scope input.
Produced: 2026-05-28. Patched: 2026-05-28, 2026-05-30, 2026-06-01,
2026-06-02, 2026-06-05, 2026-06-08, and 2026-09-04.
Phase: bounded source-access tooling build authorized only through `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`, including the first, second, and third tranches recorded there.
Edit permission: docs-write (this file only).
Controlling standard: `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md`.

---

## Source Readiness

`SOURCE_CONTEXT_READY`

```text
orca_start_preflight:
  agents_read: yes — AGENTS.md read
  overlay_read: yes — .agents/workflow-overlay/README.md + safety-rules.md read
  source_pack: source-access method planning pack
  workspace: C:\Users\vmon7\Desktop\projects\orca
  dirty_state_allowance: dirty/untracked expected; not treated as validation
  edit_permission: docs-write (plan artifact only)
  target_scope:
    - docs/product/data_capture_source_access_method_plan_v0.md
  sources_loaded:
    - docs/product/data_capture_source_access_boundary_decision_v0.md
    - docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md
    - docs/_inbox/data_capture_pressure_test_subagent_outputs_2026_05_28/README.md
    - docs/product/data_capture_spine_pressure_test_commissioning_plan_v0.md
```

---

## The Controlling Standard

From `forseti/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md` (amended through 2026-09-04 under `LOOSEN_SOURCE_ACCESS_TO_DISCOVERABLE_OR_ENTITLED_DISCLOSABLE`):

A method is **in-bounds** when **all** hold:

1. The material is discoverable through non-exploit source paths, visible through free / account-created access, or visible through entitled paid, client, or consenting-coworker access.
2. Obvious cross-account, private, or admin spillover is not used once noticed.
3. Orca would fully disclose exactly how the data was obtained if asked — no method Orca would need to conceal.
4. The method avoids the hard stops: stolen credentials/cookies, nonconsensual sessions, exploits, malware, credential stuffing, no-entitlement gate bypass, using obvious cross-account/private/admin spillover once noticed, private/confidential account areas without consent, and methods Orca would refuse to disclose internally.

**This permits:** scraping of public or discoverable pages; free or account-created login access; entitled paid, client, or consenting-coworker access; JS-rendering headless browsers; rate-limited or aggressive fetching; official or sanctioned APIs; archive/cache/mirror access; logged-in capture or browser automation; convenience shortcuts for discovery; **and anti-blocking techniques — anti-detect / "cloaked" browsers, user-agent and fingerprint configuration, residential or rotating proxies, and CAPTCHA / JS-challenge handling — used to reach source material inside this boundary.**

For community collection, this includes private Facebook groups, Discord
servers, and other login-gated communities already visible through the owner's
existing entitled/logged-in session. It does not authorize obtaining new
credentials, creating or borrowing another identity, joining a community,
bypassing controls, or exceeding the session's actual permissions. Preserve
visibility, entitlement/access provenance without secrets, and material
community privacy constraints.

**This still excludes (hard line, not risk-tolerance):** no-entitlement gate bypass, stolen credentials or cookies, nonconsensual sessions, security exploits, malware, credential stuffing, using obvious cross-account/private/admin spillover once noticed, and private/confidential account areas without consent.

**Owner-accepted risk posture:** anti-blocking techniques carry real Terms-of-Service, reputational, and (for actively-enforcing sources) litigation risk. The owner has accepted this as a deliberate, disclosable posture. Accepted risk is not a boundary question — it is recorded as an explicit owner decision and must be visible in Orca's provenance. Real legal counsel is advisable before commercializing.

**Materiality gate:** fast discovery output becomes evidence-grade only when Judgment relies on it by citing it, changing confidence, changing Action Ceiling or Decision Strength, using it in a decision claim, or including it in a client-facing or durable corpus output. If that happens, Orca must reacquire or verify through a normal disclosable path or an entitlement-clean path before final evidence use. Mere capture, storage, routing inspection, or queueing is not material use.

## Operating Preference / Cost Discipline

The boundary above permits APIs when they stay inside the discoverable-or-entitled + disclosable standard. Permission is not default sequence.

Before sale, before repeated operational pressure, or before a source-specific need is proven, Orca's default Data Capture posture is manual / subscription / local-first: human-led capture, existing subscriptions or legitimate account access, browser-visible source inspection, local files, local deterministic helpers, and explicit limitation reporting.

API use, API registration, commercial fetch services, or source-access tooling must earn its way in through an explicit owner decision, a concrete post-sale operating need, repeated scale pressure, or a source-specific reason that makes API access cleaner, cheaper, or more faithful than manual/local capture. This preference does not prohibit APIs; it prevents "API is allowed" from becoming default API sequencing or "go build/use API now."

This preference does not authorize any build, runtime, API call, app registration, credential setup, scraper, crawler, fetch service, or source-access system.

Recency/current-state handoff markers from Commission Signal Board or Scanning do not change this access-method sequence. They may increase urgency to preserve the current visible state once the target is otherwise inside the source-access boundary and route-matched, but they do not authorize a new source-access method, bypass the access gate, or select a route by themselves.

---

## Blocked Sources and Root Problems

Identified in `docs/_inbox/data_capture_pressure_test_subagent_outputs_2026_05_28/README.md`:

| Source | Block type | Root problem |
|---|---|---|
| tealhq.com | HTTP 403 to all WebFetch attempts | Active bot-blocking by Teal's server |
| reddit.com / www.reddit.com / old.reddit.com | Host-level block in WebFetch | Claude Code's WebFetch tool blocks Reddit hosts entirely (tool constraint, not internet restriction) |
| wallstreetoasis.com | HTTP 403 on WebFetch | Active bot-blocking by WSO |
| web.archive.org (content) | Tool-layer block in WebFetch | Claude Code's WebFetch blocks archive.org content fetches; the availability JSON API still works |
| mergersandinquisitions.com | Not blocked; fetches OK | WebFetch returns paraphrase, not verbatim content — violates Obligation 6 (Raw Observable Fidelity) |

Note on the archive.org block: the Wayback Machine availability API (`archive.org/wayback/available`) is not blocked and successfully returns snapshot metadata. Only the snapshot content URLs are blocked at the WebFetch tool layer. This is a Claude Code tooling constraint, not an archive.org access restriction. The archive is publicly accessible via any standard HTTP client or browser.

---

## Candidate Methods — Boundary Analysis

### Method 1: Official / Sanctioned APIs

**What it is:** Using a source's own publicly documented API with registered credentials. For this source pack, Reddit has an official public API; Teal and WSO do not.

**Boundary test:**
1. Source material inside boundary: YES — the Reddit API provides read access to public subreddit content.
2. Full disclosure: YES — "We accessed this source via its official API with registered app credentials" is fully defensible and disclosable.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Reddit (r/FinancialCareers, r/CFA, and any public subreddit). No known sanctioned API for Teal or WSO.

**Practical notes:** Reddit's API provides a free tier (approximately 100 requests/minute, 1,000/day). This tier may be sufficient for pressure-test-scale capture if API access is separately owner-authorized. Bulk commercial use at scale may require Reddit's data licensing program. The official API remains the cleanest Reddit method when API access is justified by owner decision, post-sale need, repeated scale pressure, or source-specific fidelity need; it is not Orca's pre-sale default.

**Risk:** Low for pressure-test use. Medium for commercialization — Reddit's data licensing terms should be reviewed before any product that surfaces Reddit content at scale.

---

### Method 2: Honest JS-Rendering Headless Browser

**What it is:** Automated browser (Playwright, Puppeteer, Selenium) configured with an honest user-agent that identifies as a bot, respects robots.txt, and applies crawl delays. Does not spoof fingerprints.

**Boundary test:**
1. Source material inside boundary: YES — rendering public pages inside the current source-access boundary.
2. Full disclosure: YES — "We used an automated browser with honest identification to fetch public pages."

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Potentially Teal and WSO if their 403 responses are user-agent-based rather than fingerprint- or IP-based. Solves the M&I verbatim problem if configured to return raw HTML. Does not solve the archive.org WebFetch tool constraint (that block is in the tool, not the destination).

**Practical notes:** An honest headless browser may still be blocked by sites detecting headless browser signatures (Chrome DevTools Protocol flags). It is uncertain without testing whether Teal or WSO's 403s would respond to an honest UA. Worth testing before escalating to anti-detect methods.

**Risk:** Low-Medium. Some sites' ToS prohibit any automated access; hiQ v. LinkedIn provides meaningful protection for honest automated access to public data.

---

### Method 3: Anti-Detect / Stealth Browser

**What it is:** Browser automation that actively spoofs fingerprints — user-agent, canvas, WebGL, automation flags (`window.webdriver`), timing signatures — to make a bot look like a human browsing session. Tools include Playwright-Stealth, undetected-chromedriver, Browserless stealth mode.

**Boundary test:**
1. Source material inside boundary: YES — accesses public pages inside the current source-access boundary.
2. Full disclosure: YES under the updated standard — "We used a browser configured to bypass bot detection to scrape your public site" is a complete and disclosable answer. Orca's accepted posture is that obtaining *public* data is defensible including with anti-blocking techniques.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Most effective against Teal and WSO, where the 403 blocks are likely fingerprint- or UA-based. The primary tool for breaking through aggressive bot-detection on public pages.

**Risk:** Medium-High. Carries real ToS, reputational, and potential litigation risk (CFAA-adjacent arguments in some jurisdictions when circumventing active anti-bot measures). The owner has explicitly accepted this risk posture. Must be disclosed in Orca's capture provenance — capture mode should record "automated extraction / anti-detect browser" under Obligation 4. Real legal counsel recommended before commercializing against actively-enforcing sources.

---

### Method 4: Residential Proxy Rotation

**What it is:** Routing HTTP requests through a pool of residential IP addresses (Bright Data, Oxylabs, Smartproxy, similar) so that traffic appears to originate from residential connections rather than a datacenter or identified bot operator.

**Boundary test:**
1. Source material inside boundary: YES — if used only for source material inside the current boundary.
2. Full disclosure: YES under the updated standard — "We routed requests through residential proxies to reach your public site" is a disclosable method. Orca's accepted posture covers this explicitly.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Directly addresses IP-based blocking. Teal and WSO's 403s may be IP-range blocks (datacenter IPs) as much as bot detection — residential proxies route around this. Most effective when combined with an honest or anti-detect browser.

**Practical notes:** Residential proxies are typically combined with a browser or HTTP client. As a standalone transport layer they do not render JS; pair with a headless browser for JS-heavy pages. Many commercial services offer both proxy pools and managed browser rendering in one product (e.g., Bright Data's Web Unlocker).

**Risk:** Medium-High. Same owner-accepted risk posture as anti-detect browsers. ToS violation likely for actively-blocking sources. Disclosure to Orca's provenance chain required. Proxy provider costs are per-GB or per-request at commercial scale. Real legal counsel recommended before commercializing.

---

### Method 5: Rate-Limited Polite Fetching with Honest Identification

**What it is:** Direct HTTP GET requests with an honest user-agent string (identifying Forseti source capture), crawl delay, and robots.txt compliance. No browser rendering.

**Boundary test:**
1. Source material inside boundary: YES.
2. Full disclosure: YES — trivially defensible.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Works for sources that do not block bots (M&I for non-JS pages). Will not break through 403 blocks. Does not solve Teal, Reddit (WebFetch tool block), or WSO. Does solve the verbatim problem for static M&I pages (raw HTTP returns raw HTML, not a paraphrase).

**Practical notes:** The simplest programmatic method and the correct starting point for sources that allow bot access. For M&I production use, this may be sufficient for static pricing and product pages.

**Risk:** Very Low.

---

### Method 6: Archive / Cache Access

**What it is:** Accessing publicly available snapshots through archival services:
- Wayback Machine (archive.org): availability API works now; content accessible via browser or any standard HTTP client (only blocked in Claude Code's WebFetch tool)
- archive.ph / archive.today: User-submitted snapshots; useful for some URLs, not systematic
- Common Crawl: Open public dataset; monthly snapshots, not real-time
- Bing Cache (`cache:` operator): Occasionally available, unreliable; Google Cache largely eliminated as of 2024

**Boundary test:**
1. Source material inside boundary: YES — accessing publicly available archival copies.
2. Full disclosure: YES — "We accessed historical snapshots via the Wayback Machine / archive.ph" is fully disclosable.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:**
- Teal: Wayback Machine has snapshots of tealhq.com. Useful for historical pricing/feature state (Obligation 10).
- Reddit: Coverage of specific thread chains may be incomplete. The official API is a better route for current content.
- WSO: Wayback Machine has extensive WSO thread coverage. Useful for historical thread state, edit/deletion posture.
- archive.org content (tool block): Accessible via human browser or any HTTP client; the WebFetch tool constraint does not apply outside Claude Code.
- M&I: Wayback Machine snapshots provide the 12-24 month pricing history required by the commissioning plan's slot 1 (essential for Obligation 10).

**Practical notes:** Archive access is a complement to live fetching, not a replacement. For current-state captures, archives may lag. For historical window obligations (Obligation 10), archives are often the only option.

**Risk:** Very Low. The Internet Archive's ToS supports research and non-commercial use; commercial use is generally tolerated.

---

### Method 7: Commercial Fetch / Scraping Services

**What it is:** Third-party API services that fetch and parse web content on the operator's behalf. Includes:
- **Firecrawl**: API-based scraper, honest operation, raw content or structured data
- **Diffbot**: Structured web data extraction, self-identified crawler
- **ScrapingBee, Bright Data Web Unlocker, Zyte Smart Proxy**: Services that bundle browser rendering, proxy rotation, and anti-detect into managed APIs

**Boundary test:**
1. Source material inside boundary: YES if configured for source material inside the current boundary.
2. Full disclosure: YES — "We used [service] to fetch this source page" is disclosable. Under the updated standard, services that include anti-detect or proxy features are in-bounds when the underlying technique stays inside the current boundary.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** May break through 403 blocks if the service's IP infrastructure or anti-detect handling bypasses what blocked WebFetch. For Teal and WSO specifically, managed services that include anti-detect and proxy rotation are likely the most operationally reliable production path.

**Practical notes:** Verify: (a) the service's own ToS permits Orca's use case; (b) the service's methods are logged in Orca's capture provenance as a third-party dependency (Obligation 3, Obligation 4). Reliance on a managed service means the access method is partially opaque — Orca should be able to describe at the category level what the service does (browser rendering + proxy rotation) even if exact implementation details are the service's own.

**Risk:** Medium. Cost (per-request or subscription). Third-party supply-chain dependency in the provenance chain. ToS risk inherited from the underlying techniques. Choose a service that can be named and described in Orca's provenance without requiring concealment.

---

### Method 8: Manual Human-Browser Capture

**What it is:** A human operator opens URLs in a standard web browser, reads the content, and copies verbatim text into the capture artifact. No automation.

**Boundary test:**
1. Source material inside boundary: YES — viewing source material inside the current boundary.
2. Full disclosure: YES — trivially and completely defensible. "A person read and copied the publicly visible content."

**Boundary verdict: IN-BOUNDS** — the most defensible method available.

**Works for which sources:** ALL blocked sources. Teal, Reddit, WSO, archive.org content, and M&I are all accessible in a standard browser. Solves both the access problem and the verbatim problem.

**Practical notes:** The obligation contract designates "human-led capture as allowed and expected for v0 bootstrap." This is not a fallback — it is the canonical mode for the current phase. The operator naturally preserves verbatim language, can capture modality (screenshots where layout matters), and directly observes page structure.

**Risk:** Very Low. Operator time is the cost. No legal, ToS, or reputational risk beyond what any reader of a public webpage incurs.

---

### Method 9: SERP APIs (Search-Engine Result Pages)

**What it is:** Services (SerpAPI, Serper.dev, etc.) providing programmatic access to search engine results. Returns snippets, titles, and URLs — not full page content.

**Boundary test:**
1. Source material inside boundary: YES — search results are discoverable source material.
2. Full disclosure: YES.

**Boundary verdict: IN-BOUNDS** for URL enumeration and snippet access.

**Works for which sources:** Partial. Useful for enumerating target URLs across all source families. Already used functionally in the pressure-test via WebSearch. Not suitable as a primary capture method — search snippets cannot satisfy Obligation 6 (Raw Observable Fidelity).

**Risk:** Low. Cost is per-search for most SERP API providers.

---

### Method 10: Chrome Automation via MCP (Browser-Driven)

**What it is:** An MCP tool driving a real Chrome browser instance to navigate pages, render JavaScript, and extract content. Uses a full real Chrome instance rather than a headless rendering engine.

**Boundary test:**
1. Source material inside boundary: YES if accessing source material inside the current boundary.
2. Full disclosure: YES — "We used automated Chrome to access this public page" is disclosable and defensible under the updated standard.

**Boundary verdict: IN-BOUNDS**

**Works for which sources:** Potentially Teal and WSO. A real Chrome instance may not expose headless browser signatures (Chrome DevTools Protocol flags are browser-controlled), making it more likely to succeed against fingerprint-based blocking than a standard Playwright headless browser.

**Practical notes:** Whether the `window.webdriver` flag is suppressed depends on the specific MCP implementation. If it is suppressed, this is substantively equivalent to anti-detect browser automation (Method 3) and inherits the same risk profile. If it is not suppressed, it behaves like an honest headless browser (Method 2). Orca should note which behavior the specific implementation exhibits in the capture provenance.

**Risk:** Low-Medium depending on implementation. Automation flag suppression moves this toward the anti-detect risk profile.

---

### Method 11: Free / Account-Created And Entitled Gated Access

**What it is:** Using a free account, normal login, subscription, client/coworker entitlement, an owner's existing entitled community membership, account export, browser session, headless browser, API, cached copy, mirror, or faster endpoint for source material.

**Boundary test:**
1. Discoverable, free/account-created, or entitlement-visible material: YES.
2. Obvious spillover handling: YES, if cross-account/private/admin spillover is not used once noticed.
3. Full disclosure: YES, if Orca can say "we accessed this through an entitled account / consenting collaborator / client-provided access path" and describe any automation or convenience path used.
4. Hard stops avoided: YES, if no stolen credentials/cookies, nonconsensual session, exploit, malware, credential stuffing, no-entitlement gate bypass, or use of obvious cross-account/private/admin spillover once noticed occurs.

**Boundary verdict: IN-BOUNDS for free/account-created access and for paid/client/coworker entitlement; OUT-OF-BOUNDS for no-entitlement gate bypass and obvious spillover once noticed**

**Works for which sources:** Any source where access is free/account-created, or where the client, Forseti, or a consenting collaborator has legitimate access. For an owner's existing private Facebook-group, Discord-server, or other login-gated community membership, collection stays within the permissions and privacy constraints of that supplied session and does not include credential acquisition, identity creation/borrowing, or joining a new community. For WSO-style email/social unlocks or other paid/community-gated pages, this permits a later owner-authorized capture path if the access holder consents.

**Practical notes:** Convenience paths are discovery tools, not final provenance by themselves. If we do not know access is spilling into cross-account/private/admin material, proceed. If obvious spillover appears, do not use that spillover once noticed. If Judgment relies on the material, reacquire or verify through the normal or entitled path before final client-facing or durable evidence use. If clean reacquisition is impossible, carry the limitation visibly downstream.

**Risk:** Medium. Access entitlement reduces the boundary problem, but ToS, account-sharing, privacy, and commercial-use constraints may still matter. This is not legal sufficiency.

---

## Candidate Methods Summary Table

| Method | Boundary Verdict | Access Blocked Sources? | Verbatim Content? | Risk |
|---|---|---|---|---|
| Official/Sanctioned API (Reddit) | **IN-BOUNDS** | Yes (Reddit only) | Yes | Low |
| Honest Headless Browser | **IN-BOUNDS** | Maybe (UA-based blocks only) | Yes (raw HTML) | Low-Medium |
| Anti-Detect / Stealth Browser | **IN-BOUNDS** | Yes (most blocks) | Yes | Medium-High (owner-accepted) |
| Residential Proxy Rotation | **IN-BOUNDS** | Yes (IP-based blocks) | Yes (with browser) | Medium-High (owner-accepted) |
| Rate-Limited Polite Fetching | **IN-BOUNDS** | No (still blocked) | Yes (raw HTML) | Very Low |
| Archive / Cache Access | **IN-BOUNDS** | Partial (historical state) | Yes | Very Low |
| Commercial Scraping Service | **IN-BOUNDS** | Likely (managed anti-detect) | Yes | Medium |
| Manual Human-Browser Capture | **IN-BOUNDS** | Yes (all sources) | Yes (operator copies) | Very Low |
| SERP API | **IN-BOUNDS** (enumeration only) | Partial (snippets) | No (snippets only) | Low |
| Chrome MCP Automation | **IN-BOUNDS** | Likely | Yes | Low-Medium |
| Free / Account-Created And Entitled Gated Access | **IN-BOUNDS for free/account-created access and entitlement** | Yes (free or entitled gated sources) | Yes | Medium |

---

## Method-to-Source Recommendations

### Slot 1 — M&I (mergersandinquisitions.com) — paraphrase, not verbatim

**Root problem:** WebFetch returns paraphrased content, not verbatim source language. This is a tool-layer rendering and post-processing behavior, not a bot-blocking issue.

**Recommended method for pressure-test:**
1. **Human-led browser capture** (primary) — operator opens M&I pages in browser, copies verbatim pricing and product language directly into capture Markdown. Solves the verbatim problem completely.
2. **Archive/Wayback Machine** (required complement) — the slot-1 commissioning plan requires 12-24 month pricing history. The operator navigates archive.org snapshots in a browser to capture historical state for Obligation 10.

**Recommended method for production:**
- Direct HTTP client (Python requests / Node.js fetch) — returns raw HTML without post-processing; parse with BeautifulSoup or equivalent. Honest, in-bounds, solves the verbatim problem programmatically.
- Rate-limited polite fetching with honest UA for static pages.
- Honest headless browser for JS-rendered pages if needed.

---

### Slot 2 — Teal (tealhq.com) — full 403 block

**Root problem:** Teal's server actively blocks all bot-identified requests with HTTP 403. No public API exists.

**Recommended method for pressure-test:**
1. **Human-led browser capture** (primary) — Teal is publicly accessible in any standard browser. Operator opens pricing pages, feature pages, and related public docs; copies verbatim.
2. **Archive/Wayback Machine** (complement) — navigate archive.org Teal snapshots in browser for Obligation 10 (historical pricing/feature changes).

**Recommended method for production (ranked by defensibility and reliability):**
1. **Honest headless browser** — test first. If Teal's 403 is UA-based, this succeeds without requiring anti-detect tooling.
2. **Anti-detect headless browser (Playwright-Stealth) or managed commercial service** — if honest headless fails, anti-detect is the next step. Owner-accepted risk. Record access method in capture provenance.
3. **Residential proxy + headless browser** — if IP-blocking is the mechanism (datacenter IP ranges being blocked). Combine with anti-detect for robustness.
4. **Human capture** — valid for infrequent high-value Teal state checks regardless of tooling.

---

### Slot 3 — Reddit (r/FinancialCareers, r/CFA) — tool-layer block

**Root problem:** Claude Code's WebFetch tool blocks Reddit hosts entirely. This is a tool constraint, not a network restriction. Reddit is accessible via any standard HTTP client, browser, or the Reddit API.

**Recommended method for pre-commercial / personal-project capture:**
1. **Anti-blocking browser capture first** — use the selected CloakBrowser route once implemented for public/discoverable Reddit material, because ordinary browser or tool-layer capture is expected to fail on large actively blocking sites.
2. **Old Reddit HTML surface first where available** — prefer `old.reddit.com` browser-visible HTML for posts, comment trees, and listing context because it is simpler to preserve and parse than the modern app surface when it renders.
3. **Low-volume bounded capture** — keep capture purpose-bounded by subreddit, theme, query, thread family, or a small monitored thread set; record the bound and method provenance visibly.
4. **Archive capture** — use archive capture for historical thread posture or when live capture is not necessary or fails visibly.

Do not make cold legacy `.json` endpoint requests the primary Reddit capture
spine. Online spot checks on 2026-06-05 showed Reddit's official help now says
clients must authenticate with registered OAuth tokens and non-OAuth/login
traffic will be blocked, while current developer reports describe anonymous
`.json` reads returning 403/network-security failures. Orca's bounded 2026-06-08
probes saw direct cold `.json`, browser cold `.json`, and CloakBrowser+proxy
cold `.json` fail with network-security blocks.

The useful pre-commercial JSON shape is different: load the exact old Reddit
HTML thread first in a no-proxy CloakBrowser context, confirm it is not blocked,
then fetch the same thread's `.json` URL inside that same browser context. A
bounded 2026-06-08 probe returned HTTP 200 JSON with this warm same-context
shape. Treat it as `old_reddit_html_warmup_then_same_context_json`: HTML remains
the visible provenance/warm-up surface, JSON is the structured extraction body,
and the unit remains one supplied thread unless a separate bounded runner is
implemented.

**Recommended method for production:**
- When Orca goes commercial / enterprise on Reddit, move to the sanctioned commercial / enterprise API or data-licensing path and stop relying on anti-blocking as the primary method.
- Before that threshold, do not treat Reddit official API access as realistic default sequencing if the source is not approving the current personal/research use. Use bounded anti-blocking capture and preserve the owner-accepted ToS / reputational / litigation risk in provenance.
- If data licensing for commercial use is required at scale, review before productizing Reddit content and obtain legal counsel.

Note: Reddit API app registration remains build-authorized by the second tranche, but it is not the default Reddit operating route for the current pre-commercial phase because approval/access practicality is source-controlled. The commercial/API path becomes the expected route once client money or enterprise use enters the loop.

---

### Slot 3 — Wall Street Oasis (wallstreetoasis.com) — 403 Forbidden

**Root problem:** WSO actively blocks bot requests with HTTP 403.

**Recommended method for pressure-test:**
1. **Human-led browser capture** (primary) — WSO is publicly accessible in any browser. Operator opens enumerated thread URLs, copies verbatim thread content including original post, signal-bearing replies, and related chain context per Obligation 12.
2. **Archive/Wayback Machine** (complement) — the Wayback Machine has extensive WSO thread coverage. Essential for Obligation 10 (editing, deletion, locking posture) and prior-window content.

**Recommended method for production (ranked):**
1. **Honest headless browser** — test first.
2. **Anti-detect headless browser or managed commercial service** — if honest headless fails. Owner-accepted risk. Record in provenance.
3. **Residential proxy + browser** — if IP-based blocking is the mechanism.
4. **Human capture** — appropriate for high-value thread capture regardless of tooling.

---

### web.archive.org content — tool-layer block

**Root problem:** Claude Code's WebFetch tool blocks archive.org content URLs. This is a tooling constraint only — the Internet Archive has no bot-detection posture.

**Recommended method:**
1. **Human browser access to archive.org** (immediate) — operator navigates archive.org in a standard browser; accesses snapshot content directly.
2. **Direct HTTP client in production** — archive.org is accessible via standard HTTP without any anti-bot measures. A direct HTTP fetch completely bypasses the WebFetch tool constraint.

---

## What a Build Would Entail (Build Catalogue)

This section is a method catalogue, not the build authorization by itself. As of
2026-06-02, `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`
authorizes a bounded first tranche: Source Capture Packet core/CLI, direct HTTP
fetch, media/asset preservation, Archive.org availability/body retrieval, and
honest browser snapshot support. Later owner decisions authorize the Reddit API
adapter and third-tranche anti-blocking surface. Commercial fetch services, SERP
APIs, storage, dashboards, schedulers, deployment, and broad production runtime
remain separately gated.

### Build 1: Reddit API Access

**Dependencies:**
- Reddit account (free) with app registration at `reddit.com/prefs/apps`
- OAuth2 "script" app type for server-side read-only access
- PRAW (Python Reddit API Wrapper) — `pip install praw` — or direct HTTP with `requests` + OAuth2 token flow

**What the build does:**
- Authenticate with Reddit OAuth2 using client credentials
- Enumerate subreddit posts by time range and keyword
- Fetch specific thread IDs including full comment trees
- Return verbatim post text and comment text

**Rough effort:** Low — 2 to 4 hours.
**Rough cost:** Free at pressure-test scale. Commercial bulk access at scale likely requires Reddit's data licensing.
**Legal / ToS flags:** Reddit Developer Terms reviewed before commercializing. Real legal counsel recommended before any product that surfaces Reddit content.

---

### Build 2: Honest Headless Browser (Playwright)

**Dependencies:**
- Node.js or Python environment
- `npm install playwright` or `pip install playwright`
- Playwright browser binaries — `playwright install chromium`

**What the build does:**
- Launch Chromium with honest user-agent identifying as an automated crawler
- Navigate to target URL; wait for page load including JS execution
- Extract `document.body.innerText` or specific DOM elements for verbatim content
- Apply crawl delay; close browser

**Rough effort:** Medium — 4 to 8 hours per source family.
**Rough cost:** Free (open source).
**Legal / ToS flags:** ToS violation risk per source; hiQ v. LinkedIn provides meaningful protection for honest access to public data. Evaluate per source before production.

**Note:** An honest headless browser will not break through IP-based blocks. Test against Teal and WSO before deciding whether to escalate to anti-detect.

---

### Build 3: Direct HTTP Client (M&I Verbatim Fix)

**Dependencies:**
- Python `requests` or `httpx`; or Node.js `node-fetch`
- HTML parser (BeautifulSoup for Python; Cheerio for Node.js)

**What the build does:**
- GET request to target URL with honest user-agent
- Parse raw HTML to extract verbatim pricing text, course names, bundle structures
- No LLM post-processing (the source of the WebFetch paraphrase problem)

**Rough effort:** Low — 2 to 4 hours per source family.
**Rough cost:** Free.
**Legal / ToS flags:** Lowest risk of any programmatic method. Static HTTP GET to public pages.

---

### Build 4: Archive.org CDX API + Content Fetch

**Dependencies:**
- Python `requests` or equivalent
- CDX API at `cdx.api.web.archive.org/cdx/search/cdx` (no authentication required)

**What the build does:**
- Query CDX API for snapshot availability and timestamps for a given URL
- Fetch snapshot content from `web.archive.org/web/{timestamp}/{url}` via direct HTTP GET
- Parse archived HTML for verbatim historical content

**Rough effort:** Low — 2 to 3 hours.
**Rough cost:** Free.
**Legal / ToS flags:** Very low. Internet Archive terms support research and non-commercial use; commercial use is generally tolerated.

---

### Build 5: Transparent Commercial Scraping Service Integration

**Dependencies:**
- API key for chosen service (Firecrawl, Diffbot, or equivalent)
- Service-provided SDK or direct HTTP API

**What the build does:**
- Submit target URLs to the service's API
- Receive structured or raw content in response
- Service handles browser rendering, network transport, and content extraction

**Rough effort:** Low to Medium — 2 to 6 hours depending on the service's SDK quality.
**Rough cost:** Per-request or subscription pricing. Low at pressure-test scale; material at production scale.
**Legal / ToS flags:** Verify: (a) service ToS permits Orca's use case; (b) access method is described in Orca's capture provenance at category level ("managed scraping service with browser rendering and proxy rotation"); (c) service can be named without concealment.

---

### Build 6: CloakBrowser Anti-Blocking Browser

**Dependencies:**
- Node.js or Python environment, depending on the wrapper used
- CloakBrowser package and pinned custom Chromium binary
- Existing Source Capture Packet writer and browser-capture packet conventions

**What the build does:**
- Launch CloakBrowser as the primary anti-blocking / cloaked Chromium backend
- Bypass bot-detection checks on Reddit, Teal, WSO, and similar actively-blocking public/discoverable sources
- Capture visible HTML/text/screenshot artifacts and method provenance into the Source Capture Packet shape
- For Reddit, prefer old Reddit HTML where available and support low-volume capture over named subreddit, thematic, query, thread-family, or small monitored-thread bounds rather than URL-only capture units
- Parse retrieved old Reddit HTML with a structured HTML parser such as BeautifulSoup only after preserving the raw HTML/body-equivalent; the parser is not the access method

**Rough effort:** Low-Medium — 3 to 8 hours for first bounded adapter integration. CloakBrowser pinning and packet provenance are the main implementation costs.
**Rough cost:** Open-source package plus compute cost for browser instances.
**Legal / ToS flags:** Owner-accepted risk. ToS violation likely for actively-blocking sources. Potential CFAA-adjacent exposure in some jurisdictions. Must be disclosed in capture provenance as "automated extraction / anti-blocking CloakBrowser." Real legal counsel recommended before commercializing against actively-enforcing sources.

---

### Build 7: Residential Proxy + Browser Integration

**Dependencies:**
- Account and API credentials with a residential proxy provider (Bright Data, Oxylabs, Smartproxy, or similar)
- A browser or HTTP client that routes traffic through the proxy endpoint
- Managed services (e.g., Bright Data Web Unlocker) bundle both proxy and browser rendering in one API

**What the build does:**
- Routes HTTP or browser traffic through residential IP pool
- Bypasses IP-range blocks (datacenter IP blacklisting) on Teal, WSO, and similar sources
- Combined with a headless or anti-detect browser for JS rendering and fingerprint handling

**Rough effort:** Low-Medium — 2 to 4 hours to integrate a proxy endpoint; more if building a managed rotation layer.
**Rough cost:** Per-GB or per-request pricing. Residential proxies are materially more expensive than datacenter proxies ($5-15/GB retail for residential vs. $0.50-2/GB for datacenter). Factor into production economics.
**Legal / ToS flags:** Owner-accepted risk. Same risk profile as anti-detect browsers. Proxy provider's own ToS review required. Must be disclosed in capture provenance. Real legal counsel recommended before commercializing.

---

## Legal / ToS / Reputational Risk Flags Per Source

These are risk flags, not legal opinions. Real legal counsel is advisable before commercializing any automated web-access capability.

### Reddit

- **API ToS:** Reddit's Developer Terms prohibit large-scale automated access except via the API. The free API tier permits public data access at rate limits appropriate for research. Bulk commercial redistribution likely requires a data license.
- **Direct scraping:** Reddit's `robots.txt` restricts scrapers. Anti-detect and proxy methods bypass this; under the updated standard this is in-bounds, but litigation risk (Reddit has shown willingness to enforce) is real.
- **Reputational:** Disclosing "official API with registered credentials" is stronger provenance when sanctioned access is actually available. For current pre-commercial use, the owner has decided that API approval is not a realistic default and anti-blocking capture is the practical bridge.
- **`.json` posture:** Do not depend on cold anonymous `.json` endpoints as the spine. Current official guidance requires OAuth/login credentials for Data API traffic, and current developer reports plus Orca's 2026-06-08 probes show cold `.json` can fail with 403/network-security blocks. If JSON is used pre-commercially, prefer the observed warm same-context pattern: load the exact old Reddit HTML thread first, then fetch that same thread's `.json` in the same browser context, preserving both bodies and method provenance.
- **Recommendation:** Use old Reddit Direct HTTP first for supplied exact-thread URLs when current old Reddit HTML is the capture target and the bounded batch runner accepts the URL. Use CloakBrowser anti-blocking for one supplied URL when Direct HTTP is unsuitable, blocked, or browser-visible anti-blocking capture is explicitly needed; CloakBrowser remains the primary anti-blocking backend. Keep capture low-volume and subreddit/thematic/thread-family scoped, parse with BeautifulSoup-style tooling only after raw HTML/body preservation, and record method provenance plainly. Move to the official commercial / enterprise API or licensing path when client-paid or commercial use begins. Legal counsel before commercializing content sourced from Reddit at scale.

### Teal

- **ToS:** Standard SaaS ToS prohibits automated scraping. Active 403 responses signal enforcement intent.
- **Data type:** Public pricing and feature data. Low sensitivity.
- **Anti-detect / proxy risk:** Teal's small size means litigation risk is low, but ToS violation is likely. Owner-accepted posture applies.
- **Recommendation:** Honest headless browser first; anti-detect if needed. Legal counsel before commercializing.

### Wall Street Oasis

- **ToS:** Likely prohibits bulk automated access. Active 403 enforcement.
- **Data type:** Public forum posts on career topics. No private data.
- **Community posture:** WSO is a known community. Capture use is market research / competitive intelligence, not AI training on their content — this distinction may matter in any disputes.
- **Recommendation:** Human capture for pressure tests; honest headless then anti-detect for production. Archive access for historical content. Legal counsel before commercializing at scale.

### Mergers & Inquisitions / BIWS

- **ToS:** Standard ToS likely prohibits automated copying.
- **Data type:** Public pricing and product structure — standard competitive intelligence.
- **Verbatim problem:** WebFetch paraphrases; direct HTTP or human capture solves this without needing anti-detect.
- **Recommendation:** Human capture for pressure tests; direct HTTP client for production. Very low risk given data type.

### web.archive.org / Wayback Machine

- **ToS:** Nonprofit providing public archival access. Terms support research and analysis.
- **Risk:** Very Low.

---

## Sequencing Recommendation

**Recommendation: build the authorized first tranche before selecting higher-risk
or higher-cost adapters.**

The earlier pressure-test sequence correctly deferred runtime tooling while the
obligation architecture was still untested. That phase is now superseded for the
bounded first tranche by
`docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`.
The prior API/admin cost discipline still holds: API use may be in-bounds and
the Reddit API adapter is build-authorized, but source-controlled approval
practicality can make the API a poor pre-commercial default. Reddit now has its
own pre-commercial order: exact old Reddit Direct HTTP first for supplied
thread URLs when current old Reddit HTML is the capture target; CloakBrowser
anti-blocking when Direct HTTP is unsuitable or blocked; warm same-context JSON
enrichment after exact-thread HTML
loads, low-volume bounded capture, then archive capture; commercial/API route
when client-paid or enterprise use begins. Cold legacy `.json` endpoints remain
downgraded and are not the capture spine.

**Reasons to sequence the first tranche first:**

1. **Pressure-test lessons are now available.** The critical near-term pressure
   is source observability and source preservation, not ECR/Cleaning/Judgment
   design. The first tranche builds directly against that pressure.

2. **Packet discipline should precede adapters.** Direct HTTP, archive, media,
   and browser adapters should share the same capture packet shape before more
   source-specific methods are added.

3. **Source-specific approval practicality matters.** Creating a Reddit account
   and registering an app may be build-authorized, but if the source is not
   approving narrow personal/research use, it should not remain the practical
   default for pre-commercial capture.

4. **Higher-risk adapters stay bounded.** CloakBrowser anti-blocking is now the
   selected Reddit pre-commercial route, but commercial scraping services, SERP
   APIs, broad crawler/spider frameworks, storage, dashboards, schedulers,
   deployment, and production runtime remain outside this method plan's build
   route unless separately authorized.

**Recommended sequence:**

```
Step 1 (authorized now): Build Source Capture Packet core and CLI.

Step 2 (authorized now): Add direct HTTP, media/asset, Archive.org, and honest
                         browser snapshot adapters against the same packet shape.

Step 3 (authorized later): Build or use Reddit API only when that source route
                           is practical and appropriate; use CloakBrowser as
                           the selected pre-commercial anti-blocking route for
                           bounded Reddit capture.

Step 4 (still separately gated): Evaluate whether commercial fetch services,
                                 SERP, broad crawling, storage, dashboard, or
                                 production runtime should receive separate
                                 owner authorization.
```

---

## Validation Gates

- [x] Preflight complete: AGENTS.md read, overlay read, safety-rules read, source pack loaded, edit permission is docs-write for this file only, target scope named, dirty state acknowledged.
- [x] Boundary standard (discoverable-or-entitled + disclosable) applied to all 11 candidate methods.
- [x] All 11 candidate methods are in-bounds when they avoid the hard stops; free/account-created access is allowed, paid/client/coworker entitlement is allowed, and obvious cross-account/private/admin spillover is not used once noticed.
- [x] Owner-accepted risk posture for anti-blocking techniques recorded explicitly and not treated as a boundary question.
- [x] API cost/sequence preference recorded explicitly without prohibiting APIs and without authorizing API registration, calls, or deferred runtime surfaces.
- [x] First-tranche build authority is routed to `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`, not silently implied by this method plan alone.
- [x] Non-claims stated explicitly below.

---

## Non-Claims

This artifact does not claim:

- Standalone implementation authorization. This plan does not by itself authorize
  building, installing, running, testing, or deploying source-access tooling; the
  separate first-tranche authorization decision does.
- API execution authorization. This plan does not authorize API calls, API app registration, credential setup, commercial fetch service use, scraper execution, crawler execution, or deferred source-access runtime setup.
- Blanket exit from bounded authorization. Orca may now build the separately
  authorized first tranche, but this plan does not authorize production runtime
  or every candidate method in the catalogue.
- Legal sufficiency. The legal/ToS flags above are not legal opinions. Orca should obtain real legal counsel before commercializing any capability that relies on automated web access.
- Data-rights sufficiency. Access to source material does not resolve questions about rights to process, store, or commercially use that content.
- Authorization of any specific source access. Each method/source pair must still pass the standard; this plan names recommendations but does not execute or authorize them.
- Source-access method validation or hardening. These recommendations are based on pre-build analysis. Testing may surface access realities that change the recommendations.
- Pressure-test discharge. This plan informs how source access should work for the pressure tests; it does not discharge or validate the pressure-test batch.
- Readiness claims of any kind.
- Authorization for commits, pushes, PRs, stages, or installs.

---

## Next Authorized Step

Proceed to implementation scoping for the bounded source-access tooling build
authorized by
`docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`.
Use `forseti/product/spines/capture/core/source_capture_toolbox/README.md` as the armory entrypoint
before writing implementation-facing specs or code.

Do not include commercial fetch services, SERP APIs, broad crawler/spider
frameworks, storage, dashboards, schedulers, deployment, or production runtime
unless a later owner authorization names that scope. Anti-blocking/CloakBrowser
and Reddit API work are bounded by the source-access tooling authorization
decision and still must stay inside its hard stops and non-claims.

---

## Human Summary

**What changed in this patch series:**

The boundary decision is now updated to `LOOSEN_SOURCE_ACCESS_TO_DISCOVERABLE_OR_ENTITLED_DISCLOSABLE`. This plan has been patched to match. The standard is now discoverable source material, free/account-created access, entitled paid/client/coworker access, disclosability, obvious spillover avoidance once noticed, and hard-stop avoidance. Anti-detect browsers, residential proxy rotation, Chrome automation with fingerprint handling, and free or entitled authenticated/paywalled access are in-bounds when they stay inside that standard.

**What this means after the pressure tests:** the first-tranche tooling build is
now authorized as a bounded implementation route. This does not retroactively
make the pressure tests validation, readiness, or production proof.

**What changes for production tooling:** the full in-bound method set remains available inside the boundary, and later owner decisions have now authorized Reddit API plus anti-blocking/proxy/JS-challenge support as bounded build surfaces. CloakBrowser is the selected primary anti-blocking backend. Free/account-created access is okay. If authenticated or paywalled access is legitimately available through Orca, the client, or a consenting collaborator, headless/browser/API/convenience access can be used. The remaining question is risk management, cost discipline, provenance, and owner/post-sale/scale justification — not a blanket in/out gate.

**The hard line that stays:** no-entitlement gate bypass, stolen credentials/cookies, nonconsensual sessions, security exploits, malware, credential stuffing, using obvious cross-account/private/admin spillover once noticed, private/confidential account areas without consent, and methods Orca would refuse to disclose internally. Free logins, account-created access, authentication, and paywalls are not automatic stop signs.

---

## Path / Status Receipt

```text
artifact_written_to: docs/product/data_capture_source_access_method_plan_v0.md
status: ACCEPTED_SOURCE_ACCESS_METHOD_PLAN_V0
patch_date: 2026-06-01
patch_reason: API cost/sequence preference added; boundary permission unchanged from discoverable-or-entitled + disclosable standard with materiality-gated provenance cleanup
patch_2026_06_02_reason: linked bounded first-tranche source-access tooling build authorization
patch_2026_06_05_reason: aligned to third-tranche anti-blocking authorization, CloakBrowser-first backend selection, and Reddit pre-commercial ordering
patch_2026_06_08_reason: aligned current operator default to observed exact old Reddit Direct HTTP success while retaining CloakBrowser as primary anti-blocking backend
phase: bounded source-access tooling build authorized by separate decision
boundary_standard_applied: yes, to all 11 candidate methods
methods_out_of_bounds: no-entitlement gate bypass, stolen credentials/cookies, nonconsensual sessions, security exploits, malware, credential stuffing, using obvious cross-account/private/admin spillover once noticed, private/confidential account areas without consent, and methods Orca would refuse to disclose internally
hard_line_exclusions: narrowed from blanket auth/paywall/private labels to no-entitlement, nonconsensual, exploit-style, obvious-spillover-once-noticed, confidential, internally non-disclosable, or clearly illegal / morally compromising methods
recommended_for_reddit_pre_commercial: exact old Reddit Direct HTTP first for supplied thread URLs where current old Reddit HTML is the capture target; CloakBrowser anti-blocking when Direct HTTP is unsuitable or blocked; prefer old Reddit HTML where available; then low-volume bounded capture; then archive capture
reddit_json_posture: warm same-context enrichment after exact old Reddit HTML loads; cold json downgraded; not standalone primary capture spine
api_preference: APIs remain in-bounds, but manual/subscription/local-first is the pre-sale default; API/admin/tooling requires owner/post-sale/scale/source-specific justification
build_authorization: FIRST_TRANCHE_GRANTED_BY docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md
commits_pushes_prs: NOT authorized — docs-write only
legal_counsel_advisory: recommended before commercializing any automated web-access capability
original_patch_produced_by: Claude Sonnet 4.6 under source-access method planning prompt v0
patch_2026_06_01_produced_by: Codex under user-authorized source-access API preference patch route
patch_2026_06_02_produced_by: Codex under user-authorized source-access tooling build authorization docs route
```

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: "Source-access method planning now records API cost/sequence discipline: APIs remain in-bounds, but manual/subscription/local-first capture is the pre-sale default and API/admin/tooling requires explicit owner/post-sale/scale/source-specific justification."
  trigger: product_doctrine
  controlling_sources_updated:
    - "docs/product/data_capture_source_access_method_plan_v0.md"
  downstream_surfaces_checked:
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/workflows/orca_repo_map_v0.md"
    - "docs/product/data_capture_source_access_boundary_decision_v0.md"
  intentionally_not_updated:
    - path: "docs/product/data_capture_source_access_boundary_decision_v0.md"
      reason: "Boundary permission is unchanged; APIs and other in-bound methods remain permitted under the discoverable-or-entitled + disclosable standard."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "The canonical source-loading surface already identifies this as a source-access method plan and does not route agents by API-default sequencing."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "The repo map entry already describes the artifact as a docs-only source-access method plan with no build/runtime authorization; no discoverability/status change was needed."
  stale_language_search: "rg -n \"never API|API.*disallowed|APIs.*out-of-bounds|API-first|Reddit API registration.*parallel|highest-priority build|API registration.*can proceed|official API.*primary|API.*authorized now|build.*authorized|runtime.*authorized|tooling.*authorized\" docs/product/data_capture_source_access_method_plan_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
```

## Direction Change Propagation - 2026-06-02 Build Authority Patch

```yaml
direction_change_propagation:
  doctrine_changed: "The method plan now recognizes that a separate owner decision authorizes bounded first-tranche source-access tooling builds while keeping API registration/calls, commercial fetch services, anti-detect, proxies, SERP APIs, storage, dashboards, schedulers, deployment, and production runtime separately gated."
  trigger: lifecycle_boundary
  controlling_sources_updated:
    - "docs/product/data_capture_source_access_method_plan_v0.md"
    - "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
    - "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/workflows/orca_repo_map_v0.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
    - "docs/product/data_capture_source_access_boundary_decision_v0.md"
    - "docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
    - "docs/decisions/data_capture_spine_source_observability_requirements_boundary_decision_v0.md"
    - "docs/decisions/data_capture_spine_source_observability_local_support_implementation_execution_authorization_v0.md"
  intentionally_not_updated:
    - path: "docs/product/data_capture_source_access_boundary_decision_v0.md"
      reason: "Boundary permission and hard stops did not change."
    - path: "docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
      reason: "Capture obligations did not change; runtime work remains allowed only when separately authorized."
    - path: "docs/decisions/data_capture_spine_source_observability_requirements_boundary_decision_v0.md"
      reason: "That decision remains accurate for requirements classification and already requires separate authorization for implementation; this later decision supplies separate authorization for source-access tooling, not a requirements reclassification."
    - path: "docs/decisions/data_capture_spine_source_observability_local_support_implementation_execution_authorization_v0.md"
      reason: "The local source-observability helper authorization remains bounded to that helper and is not the new source-access tooling authority."
  stale_language_search: "rg -n \"No build authorization|No build, no install, no runtime authorized|Nothing here authorizes building|build_authorization: NOT GRANTED|That authorization is not granted here|not build tools now|defer_until_separate_owner_authorization\" docs/product/data_capture_source_access_method_plan_v0.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md docs/product/data_capture_spine_pressure_test_closeout_synthesis_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source-access boundary amendment"
    - "not API, commercial-scraper, anti-detect, proxy, or production-runtime authorization"
    - "not ECR, Cleaning, or Judgment design"
```
