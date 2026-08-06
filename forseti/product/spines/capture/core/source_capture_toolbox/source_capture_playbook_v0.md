```yaml
retrieval_header_version: 1
artifact_role: Capture-investigation method playbook (v0, REVIEW-HARDENED + RISK-POSTURE-AMENDED, non-authorizing doctrine)
scope: >
  The repeatable method for deciding whether and how a NEW source can be captured — within the
  owner-authorized capture boundary, and by the cheapest route. Converts the old runner "ladder"
  into a problem-indexed route catalog: read the problem, then point to the route. MVP scope is the
  risk posture + the read + the route catalog + the pointer + the guardrails. Per-source recipe
  cards are a growing tail authored BY probes, not here.
use_when:
  - Onboarding a new source/platform and deciding the cheapest working capture route.
  - Commissioning a capture probe lane (the probe runs this method, returns a recipe card, NO-GO, or CATALOG_GAP).
  - Checking whether a "blocked"/NO-GO call was made honestly (re-probed, logged, access-bounded).
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - forseti/product/spines/capture/core/source_families/README.md
stale_if:
  - A probe surfaces a route the catalog lacks (CATALOG_GAP) -> amend the catalog.
  - The owner changes the risk posture (e.g. commercial/licensed phase begins, or the access-control line moves).
  - The existing per-source playbooks are formally re-homed as recipe cards under this method.
status: RISK_POSTURE_AMENDED_V0
review_provenance: >
  De-correlated adversarial artifact review by a non-Anthropic (GPT-family) controller against
  playbook v0 @ sha256 7FDA9AFDB16BCC6768A247C1F0E433D3503016D72052D49B261B5C65DDBEBA22, recon index
  @ sha256 ECDE5452...B7532 as context. Verdict ACCEPT_WITH_CHANGES; AR-01..AR-07 + 2 faithfulness
  items adjudicated-ACCEPTED and applied (hardened @ sha256 D5B4DCCE...18B388).
  POST-REVIEW OWNER AMENDMENT: the entitlement-first / never-bypass-ToS posture that the review
  covered was deliberately changed by an owner risk decision — see "Risk posture". That amendment is
  an owner's-prerogative risk acceptance, OUTSIDE the de-correlated review's scope; the review
  validated the method's structure under the prior (stricter) posture, not this one.
```

# Capture-Investigation Playbook (v0, review-hardened + risk-posture-amended)

## What this is — and is not

This is the **method** for one question about any new source: *can we get the real content, within
what we're allowed to take, by the cheapest route?* You hand it a target, it walks a diagnosis, and
a probe banks a reusable cheat-sheet for that source type.

It is **not** code, not a harness, not a guarantee any source is capturable. It can honestly
conclude **NO-GO**, **PARTIAL**, or **CATALOG_GAP** — those are successful diagnoses. It is
non-authorizing: it grants no capture/build/merge authority; each probe runs under its own bounded
authorization and per-operation network approval.

**MVP scope:** the risk posture + the read + the route catalog + the pointer + the guardrails.
Per-source **recipe cards** are authored BY probes and accumulate over time. TikTok now has
partial technical recon and admitted Funmi N30 parsed-batch packet evidence, but cross-creator
durability, account safety, durable media, and scale remain unproven. Instagram now has
several probed public-web routes, including a
route-specific 2026-06-29 live diagnostic: standalone anonymous `yt-dlp` can return an empty media
response while the browser-rendered deep-capture route still exposes a transient media handle that
can be downloaded immediately for ASR. That is a route residual, not an Instagram transcript NO-GO.

**Known-source routing:** If the target source/platform is already listed in
`forseti/product/spines/capture/core/source_families/README.md`, open that family index before
re-probing or searching the whole repo. This playbook owns the access gate and method; the
source-family index owns the route home that ties access route, runner, projection, lake, ECR,
and Cleaning pointers together. Data Lake contracts remain in the Data Lake spine and are not
restated here.

**Lake-first radar preflight:** Before external capture in a recurring or
actively radarred source family, inspect the existing Data Lake through the
highest-trustworthy current read surface available: relevant Silver/current view
first, then packet or catalog inventory, then raw material when necessary.
Reuse an appropriate existing packet unless recapture materially improves
currentness, fidelity, provenance, cutoff compliance, inspectability, or fills a
named gap. The lake is reuse/freshness/coverage context, not proof of current
external reality. Absence from Silver is not absence from the lake or external
world, and a missing read model does not block acquisition.

## Risk posture (owner-authorized, pre-commercial)

The owner authorizes, for the pre-commercial proving phase, **capturing publicly-viewable content
even where a site's ToS forbids automation** — including **circumventing anti-bot measures**
(fingerprint / challenge handling, proxies, geo congruence) and **automated capture**. The owner
accepts the ToS / civil risk and will pursue licensed or commercial routes once the signal is proven
and resources justify it.

This authorization is **bounded — not blanket**:

- **Human-rate, targeted, and directed only.** No mass scraping, no crawl-at-scale, no DoS-level
  volume. One source, one bounded question at a time, at roughly the request rate a human reader
  would generate.
- **The access-control line still holds.** Do NOT defeat authentication or access control to reach
  content that is not publicly viewable, or that you are not entitled to (no logging in as someone
  else, no paywall / private-account / private-API bypass). Use your OWN entitled access where you
  hold it; otherwise that content stays out. *ToS-against-scraping is now accepted risk; defeating an
  auth gate is not — that is the line between civil/ToS exposure and unauthorized-access exposure.*
- **No private personal data of individuals / no surveillance-grade harvesting** (unchanged separate
  legal line — see `data_capture_spine_future_exploration_lanes_v0.md`). Market-level signal
  (product/brand/hashtag/aggregate counts) is fine; building dossiers on individuals is not
  (exception: internal wind-caller calibration per `docs/decisions/wind_caller_calibration_carveout_v0.md`
  — bounded to ≤10 own operating/capture accounts (starting ≤5); subject-creator roster uncapped
  within the vertical; active capture: attended (human-initiated), faster-than-human pace;
  passive monitoring: human-initiated, time-bounded, self-terminating (no discovery during);
  public data only, pre-commercial, internal only; that carve-out does not change the general
  dossier prohibition).
- **No secrets, no exit-IP leak, per-operation network approval** (unchanged operational hygiene).

**The hard line moved from "ToS forbids it" to "it's behind an access-control gate you can't
legitimately pass."**

## The core shift: ladder -> catalog

The old "runner ladder" implied climbing rungs in order. This playbook replaces that with
**read the problem, then point to the route.** Routes are a menu indexed by the problem each
solves; the diagnosis selects the route. Blind climbing wastes probes and can mis-stop — a headless
403 is *not* "a browser won't help" (see Daimler in the recon index).

## Guardrails (these frame everything; non-negotiable)

1. **Access-control gate — first for external technical work (executable as Step 0).** After the
   lake-first preflight when it applies, and before any external technical attempt,
   classify whether the content is **publicly viewable** vs. **behind an access-control / auth
   gate**. Public content is in scope even against ToS, with anti-bot circumvention, under the Risk
   posture (human-rate, bounded). An auth/access-control gate is only passable with your own entitled
   access; never defeat it. No secrets recorded — endpoints-as-secrets, credentials, exit-IP never
   captured.
2. **Two-axis bar.** "Did we get through?" is the necessary **gate**; "is what we grabbed the real
   thing?" is the **win**. GO requires *checkable* source-native evidence (see Step 3) — reachable
   -but-paraphrase (WebFetch on M&I/BIWS) is **PARTIAL, not GO**. Never let the foot-in-the-door, or
   an asserted-but-unverifiable capture, pass as the real grab. Packet creation, HTTP 200,
   preserved screenshots/DOM, and a generic detail-sufficiency flag are not source-useful success
   by themselves: the caller must name the required visible/DOM details for the run, and extraction
   may use the packet only when those named details are present and recorded.
3. **The receipt.** Every run logs the full receipt (see Step 3) — access classification, routes
   tried *and skipped-with-reason*, evidence locators, fidelity evidence, why it stopped, the
   verdict, and the routes now forbidden without a new fact. An honest NO-GO records *what failed*.
   No receipt -> the verdict is not trustworthy and escalation is unbounded.
4. **"Blocked" is a symptom, not a verdict — but re-probing is bounded.** A 403 / empty body /
   failed headless / missing lazy content / anti-bot challenge is a hypothesis to re-probe at another
   route — not a NO-GO. Re-probe **only when the next route tests a different hypothesis**: repeating
   the same route class requires a new fact, changed approach, or a changed environment; stay
   human-rate; and never cross the access-control line. The recurring expensive error is a premature
   "blocked" that abandons capturable material (Daimler, Sephora, Teal, WSO); the opposite error is
   thrashing the same route forever, or escalating volume past human rate. Before promoting an
   empty or erroring probe result into NO-GO, "blocked", or an empty-source verdict, prove the
   instrument first — run the same probe method against a known-positive control, or confirm with a
   second independent method, inside the same re-probe bounds above (different hypothesis,
   human-rate, access-control line intact). An erroring probe supports only "probe failed
   (tooling)", never "target absent": the recorded false negatives in this class are a broken
   scroll capture misread as anti-bot obliteration (Sephora) and an archive CDX timeout misread as
   an empty archive.

**Screening-side consumer (reverse pointer, 2026-06-12; updated 2026-06-21).**
These read-escalation patterns (Guardrail 4 + the Step 2 pointer) are distilled
for *screening posture* - public pages, no logins, URLs + short quotes - in the
Walker Equipment Kit
(`forseti/product/spines/foundation/vertical_exploration/forseti_vertical_exploration_guide_v0.md`).
Keep them in sync: when a route-escalation pattern here changes, the kit's READ
ESCALATION / KNOWN WALLS block may need a dated note. Packet-grade capture still
routes through this method; the kit is screening-read only.

The bounded screening-read service now gives the orchestrator a read-only
capture-harness path for public screening reads:
`source_capture.screening_read.screening_read(...)` for Reddit/direct/anti-block
HTTP routes and `source_capture.screening_browser_read.screening_browser_read(...)`
for public browser/interstitial reads. These entries return screen-light records
or visible text; they do not stage packets, write manifests, or touch ECR. Walkers
must not call them directly; they record the need and let the orchestrator invoke
the bounded read.

## Step -1 — Lake reuse and freshness preflight

Run this step before external capture when the source family is recurring or
actively radarred:

1. inspect the relevant Silver/current view when one exists;
2. inspect packet or catalog inventory when Silver is absent, stale, incomplete,
   conflicting, or insufficiently faithful;
3. inspect raw material only when needed to resolve reuse, freshness, coverage,
   or source-fidelity questions;
4. identify the existing packet, the named information job, and whether reuse
   satisfies the bounded request;
5. recapture only for a recorded material improvement in currentness, fidelity,
   provenance, cutoff compliance, inspectability, or a named gap.

Do not infer current external reality from lake state. Absence from Silver is
not absence from the lake or the world. Lack of a relevant read model does not
block the external route.

## Step 0 — The access-control gate (run before any external technical probe)

Classify the target as one of: **publicly-viewable · publicly-viewable-but-ToS-restricted ·
authenticated/access-controlled · operator-supplied/manual-only · unknown.**

- **publicly-viewable** and **publicly-viewable-but-ToS-restricted**: **in scope.** Anti-bot
  circumvention and automated capture are authorized under the Risk posture (human-rate, targeted,
  bounded). ToS-against-automation is accepted risk, not a stop.
- **authenticated / access-controlled**: use only your OWN entitled access (your logged-in account,
  an API key you hold); do NOT defeat the gate. If you have no entitled access, that content is out.
- **operator-supplied/manual-only**: the owner supplies the bytes (entitled docs/PDF).
- **unknown** (after a good-faith look): determine public-vs-gated before running routes; if you
  genuinely cannot tell whether content is public, treat as gated and stop.
- Record the classification in the receipt. This gate fires first; nothing in Steps 1–3 runs before
  it.

## Step 1 — The read (substrate-first)

Locate **where the signal actually lives**, and name the blocker — *before* picking a tool.

- **Where does the signal live?** vendor API rendered first-party (Bazaarvoice); embedded
  page-state (`__APOLLO_STATE__` / `__NEXT_DATA__` / a JSON blob); rendered DOM; a download
  (PDF button); raw JSON (Reddit); an internal web API the page calls; **mobile/app-only** (no useful
  public web surface — flag loudly; the catalog may have no route -> CATALOG_GAP, not NO-GO).
- **What's blocking?** 403 / empty / lazy-load-not-fired / anti-bot challenge / login-wall /
  paraphrase-only. (A **login-wall** is an access-control gate — Step 0 governs it; an **anti-bot
  challenge** on public content is now a route problem, not a stop.)
- **Rendered browser access check.** For browser routes, distinguish **visible source content** from
  **residual challenge artifacts** in the full DOM. A passed anti-bot page can retain hidden
  `/cdn-cgi/`, challenge-platform, CAPTCHA, or interstitial script/template text after real source
  content is visible. Classify access-block posture from rendered **visible text + title** first;
  full-DOM challenge markers alone are a warning/residual signal unless the visible text is empty or
  challenge-only. Conversely, a visible interstitial ("Just a moment", "verify you are human",
  access-block copy, etc.) is `access_failed` even when the browser returned artifacts.
- **Output:** a one-line problem statement — `<signal> lives in <substrate>; blocked by <symptom>`.

## Step 2 — The pointer (problem -> route)

Pick the cheapest route that fits the located substrate. A symptom quick-reference — a shortcut
**under** the substrate read, never instead of it:

| Symptom | Likely cause | First re-probe |
|---|---|---|
| 403 on direct fetch | headless/bot signature, or host block | real browser context; then visible browser + user action; then anti-bot route |
| empty / sparse body | content lazy-loads or is JS-rendered | progressive scroll to fire observers; locate embedded state |
| content present but reworded | tool returned paraphrase (fidelity fail) | a route that preserves bytes (browser page content / embedded-state extract) |
| 403 *and* headless also 403 | NOT "browser won't help" — visible-context / anti-bot detection | standard browser controls (headed / local channel / settle); then visible browser + user action; then anti-bot fingerprint/challenge route |
| anti-bot challenge on PUBLIC content | bot detection (Cloudflare/Kasada/Akamai/etc.) | browser-rendered access diagnosis; standard browser controls first when plausible; then anti-bot route (fingerprint/challenge handling, proxy/geo) — authorized, human-rate |
| route-specific empty media response (e.g. IG standalone `yt-dlp`) | media resolver route is stale, brittle, or lacks the page-rendered handle; not proof the source item lacks audio | browser-rendered item deep-capture; extract the route-native transient media handle from the rendered DOM and use it immediately, or record `no_audio_handle` / render posture |
| login-wall | access-control gate (Step 0) | use OWN entitled access, or stop — do NOT defeat it |
| reviews/section missing | IntersectionObserver lazy-load not fired | progressive/incremental scroll (Sephora) |

## Step 2b — The route catalog (the de-laddered ladder)

Each route by what it solves / cost / fidelity it preserves / access note. **Not an order — a
menu.** Cheapest fit wins.

| Route | Solves | Cost | Fidelity preserved | Access note |
|---|---|---|---|---|
| archive.org / Wayback (cross-archive ladder rung 1) | historical / pre-cutoff state; current page gone/blocked | low | snapshot bytes, served-time-verified <= cutoff (availability != body — check both) | public |
| archive.today / Memento (ladder rung 2) | pre-cutoff state when Wayback misses; closes the single-archive SPOF for ordinary brand/retailer pages | low-med | memento bytes, served-time-verified <= cutoff (mirror-family host-anchored) | public; no-gate-defeat (CF/CAPTCHA challenge -> STOP; HTTP 429 -> retry/backoff) |
| publisher version-history (MediaWiki / GitHub) | pre-cutoff state of a doc/wiki/repo from the publisher's OWN version history | low | the publisher's exact revision bytes, served-time-verified <= cutoff | public API (needs explicit wiki/repo coordinates) |
| direct-HTTP | static first-party HTML/JSON | lowest | raw bytes | public |
| real browser (headless) | JS-rendered DOM | med | rendered bytes; visible text used for access-block diagnosis | public |
| standard browser controls (headed / local channel / settle) | headless/browser-channel/settle-sensitive interstitials before anti-detect escalation | med | rendered bytes; visible text/title separated from residual DOM challenge markers | public |
| visible browser + user action | headless-detected 403; user-gated download (PDF) | med-high | real bytes via the real UI path | public; own entitled access if gated |
| progressive / incremental scroll | lazy-load / IntersectionObserver content (reviews) | med | first-party-rendered bytes | public |
| rendered social item deep-capture (transient media handle) | source item where comments and/or audio handle live in rendered DOM, especially when a standalone media resolver returns empty/unavailable | med-high | visible comments plus immediate ASR from a route-native transient handle; signed media URL is redacted and not durable evidence | public browser render; no auth-gate defeat; human-rate |
| anti-bot / cloakbrowser + proxy/geo | anti-bot challenge on public content; geo friction | high | rendered bytes *(bounded evidence exists for persistent-profile Quora; proxy/geo remains unproven — see route maturity)* | public; authorized under Risk posture; human-rate; no secrets/exit-IP |
| vendor-API first-party render | reviews/widgets a vendor API renders into the DOM (Bazaarvoice) | low-med | the API's real values | public via the page |
| embedded-state / internal-API extract | signal in `__APOLLO_STATE__` / `__NEXT_DATA__` / a JSON blob / a public page's own internal API | low | exact embedded values (cite field+value) | public via the page (not an auth-gated private API) |
| operator-supplied | owner provides the bytes (entitled docs/PDF) | n/a | as-supplied (verify hash / magic bytes) | entitled |

**Route selection (not table order).** A route is "in catalog" for this probe only when its
Solves/Access cells match the **Step 0 classification** AND the **Step 1 substrate/problem**.
Do not advance by table order. If a route fails, that's a symptom -> re-read -> the next *matching*
route (under the Guardrail 4 bound, human-rate). If **no row matches**, stop as **CATALOG_GAP**
(record the missing-route candidate) — *unless* it's behind an access-control gate you can't pass,
which is NO-GO. Reach NO-GO only after the matching routes are exhausted, with the receipt.

### Local preprojection economy (owner direction, 2026-08-05)

For a public route whose signal can be narrowed before broad-page acquisition,
the local default is to **preproject the transport**: request the smallest
source-native section, embedded-state object, or page-owned API response that
still preserves the commissioned identity, order, fields, and coverage bound;
request transfer compression; then perform deterministic local extraction
before retention. Do not download a full storefront shell merely because it is
the easiest document to locate.

The first pin for a new or materially changed narrow route pays one calibration
cost: compare it with the broader source surface and prove that subject binding,
ordering, field fidelity, and the declared denominator agree. Bank the narrow
route only after that parity check. Routine captures then go directly to the
pin; they do not repay broad-page capture or parity calibration unless a route,
template, denominator, required field, or reconciliation check drifts.

"Preprojection" here is transport economy plus local mechanical extraction. It
does not create a Capture Projection packet, authorize Cleaning or Judgment,
or permit a compact feed that silently changes order or coverage. Preserve the
compressed source response or admitted canonical content under the retention
contract. If narrowing or extraction cannot prove the commissioned bound,
preserve diagnostic raw evidence, report the typed residual, and use the
broader matching route only as the explicit fallback.

**Route maturity (faithful to the recon index).** Progressive-scroll is *capture-proven* (Sephora
reviews; worktree-pending). CloakBrowser persistent-profile capture has one source-specific
end-to-end success for a Quora B2B search packet after lower-rung pressure, with a local ignored
profile, no proxy, and caller-bound detail sufficiency recorded in
`docs/workflows/quora_b2b_postmerge_capture_calibration_v0.md`; treat that as bounded Quora
evidence, not broad Quora reliability, session durability, buyer proof, or proof that the
proxy/geo variant works. The `anti-bot / cloakbrowser + proxy/geo` route remains
setup/architecture-ready where proxy/geo behavior is concerned. Don't cite an unproven route as
evidence of capturability.

**IG live media-route diagnostic (2026-06-29).** For public Instagram Reels, a standalone
anonymous `yt-dlp` media fetch can fail before ASR with Instagram's empty-media response even when
the reel page renders publicly. Treat that as failure of the standalone media-resolver route. The
next matching route is rendered reel deep-capture: one browser render yields comments plus a
transient IG-CDN media handle for immediate ASR. The observed diagnostic does **not** prove durable
media/video preservation, canonical-lake persistence, logged-in access, or scale cadence; it only
prevents the empty-media failure from being promoted into an IG transcript NO-GO.

Proxy profiles are shared Source Capture browser-route configuration, not CloakBrowser-owned
state. A runner may opt into a registered proxy profile by label while keeping endpoint,
credentials, exit IP, and store path out of packets; CloakBrowser remains one possible
browser backend rather than the owner of proxy semantics.

**Rendered-access honesty rule (browser routes).** Browser artifacts are not source success by
themselves. A route GO requires source-native visible content or route-native embedded values, not
merely a non-error browser run. When visible text/title show an access block, CAPTCHA, or
interstitial, record `access_failed` / PARTIAL even if DOM and screenshot were preserved. When
visible text shows source content but the DOM still contains residual challenge scripts/templates,
record the residual marker as a limitation/warning, not as the verdict. This is source-agnostic:
Cloudflare, Akamai, Kasada, DataDome, PerimeterX, or other challenge families may leave artifacts in
the DOM after the human-visible page has advanced. The safe error is under-claiming source success;
the unsafe error is calling a visible block shell content.

### Cross-archive historical capture (the ladder + the runner)

For **pre-cutoff historical state**, the three archive rows above are wired into one bounded,
cheapest-first **LOCATE ladder** so a single archive is no longer a single point of failure:
`runners/run_source_capture_historical_packet.py` (orchestrator: `source_capture/historical_capture.py`).

- **Ladder order:** Wayback CDX -> archive.today TimeMap -> publisher version-history (the last *only*
  when the source is a doc/wiki/repo — it needs explicit MediaWiki/GitHub coordinates, not a plain URL).
  Stop at the **first served-time-verified pre-cutoff body**; a locate-hit whose body fails (transport,
  non-2xx, or served-time/identity verification) is a **PARTIAL that escalates** to the next rung,
  never a fake-success rollup.
- **No-lookahead (served-time, per rung):** selection filters to memento/revision timestamp <= cutoff,
  AND the *served* snapshot is re-verified <= cutoff (a replay redirect can serve a post-cutoff capture
  for a pre-cutoff request — that leak is rejected). A non-2xx body is not body-honesty and is rejected.
- **No-gate-defeat:** archive.today's anti-bot **challenge -> STOP** (never solved); a plain HTTP 429
  rate-limit -> retry/backoff (in-posture). Wayback is not Cloudflare-fronted; it simply throttles.
- **Honest NO-GO:** when every rung misses (or yields no clean pre-cutoff body), the run still writes
  a packet whose receipt records the full ladder trace, so exhaustion is auditable.
- **Receipt:** the selected rung's existing Source Capture Packet, plus a thin preserved
  `archive_locate_metadata.json` side-file recording `archives_tried` / `archive_selected` /
  `body_rung_used` as **neutral mechanical facts** (no scores or verdicts — INV-1).
- **Cutoff form:** the runner takes an ISO-8601 cutoff (e.g. `2024-06-01T00:00:00Z`).

Spec + provenance: `archive_org_refinement_and_source_family_gap_spec_v0.md` (slice E). This subsection
is a `stale_if` catalog amendment documenting landed code (added 2026-06-16); it is outside the
original de-correlated review's scope.

## Recency / Current-State Preservation Priority

When a scanning or CSB handoff marks a URL or venue as recent/current-state
high-attention, or when a handoff or the source itself exposes source-visible
public-reaction engagement/resonance facts, Capture treats that as preservation
urgency and source-drift risk. Prefer preserving the current visible state before
older context when the request is otherwise within scope and route-matched.
Same-strength newer/current source states, or source states with more
source-visible reaction context, may deserve earlier capture than older or
lower-context source states, especially for stockout/restock, waitlist, review
text, availability, price, or changing PDP / social / forum surfaces.

This priority does not prove demand, change the access-control gate, select a
route by itself, or let scanning bind Capture's route. Engagement counts,
source-native scores, visible rank/order, comments, likes, views, shares,
helpful votes, or official-response markers stay source facts. Capture still
runs Step 0, chooses the cheapest matching route, and records the captured state
as source facts, not proof.

## Capture retention — canonical content or raw (owner direction, 2026-07-20)

Content-eligible routes extract their family-owned canonical
`content_record.json` during capture. Only after access, route pin, source
sufficiency, secret rejection, and deterministic extraction succeed may the
runner hash and discard declared disposable DOM, visible text, or HTTP response
bytes. `content_extraction_metadata.json` records
`requested_retention_mode`, `retention_outcome`, `extractor_version`,
`extraction_status`, and each input's role, filename, SHA-256, byte count, and
preservation state.

The public retention modes are `content` and `raw`. `raw` preserves the original
source evidence. Any admission or extraction failure preserves all supplied
original artifacts, writes no `content_record.json`, records a typed failure,
and returns nonzero. A packet therefore carries a canonical content record only
when its `retention_outcome` is `content`; because extraction runs before
admission is decided, an admission failure discards an already-parsed record,
which the preserved inputs re-derive at the recorded `extractor_version`.
Capture does not write a Projection packet, and post-hoc capture Projection is
not an operating path.

There is no admitted sample mode. Extractor qualification uses explicit
operator scratch inputs and `run_content_qualification.py`; it compares current
deterministic extraction with a retained content record without creating a
packet. Match releases only the named scratch DOM/text and leaves a report.
Drift or failure preserves scratch for diagnosis. This is a release gate, not a
standing capture or lake lane.

Seams:

- `forseti-harness/source_capture/content_extraction.py`
- `forseti-harness/source_capture/content_qualification.py`
- `forseti-harness/cleaning/content.py`

Family schemas and parsers remain family-owned. Cleaning validates current
content records and binds rows to real packet identity and JSON pointers.
Historical raw, sample-era, content, and Projection-era artifacts remain
readable only through explicit read-only legacy decoders. Cross-packet
analytical projections are unaffected.

Screenshot acquisition remains route-triggered. Exact URL and route-specific
locale, currency, ZIP, challenge-free, and source-sufficiency checks remain the
access gate; a screenshot is not access proof.

## Rendered overlays and screenshot economy

For rendered-browser capture, **preserve a screenshot when supplied** is a
packet-retention rule, not an instruction to create a screenshot on every run.
A screenshot is optional source-media evidence. Request one only when the
capture needs to establish or inspect a visual fact that DOM, visible text,
route provenance, and the projected content record do not independently carry:

- the first active-Capture baseline for a new or materially changed rendered
  route after that route has been selected for capture;
- source-visible image, layout, placement, or other visual content is part of
  the information job;
- access state, rendered-route drift, projection ambiguity/failure, or a UI
  overlay needs diagnosis; or
- the owner explicitly requests current visual evidence.

Screenshot production belongs to **Capture**, not to CSB or Scanning/radaring.
CSB may name a visual-evidence requirement in the commission, and Scanning may
return a `capture_request` whose information job requires that evidence, but
neither lane takes or preserves the screenshot as ordinary output. Capture
creates it only while executing the selected `capture_request`. A transient
operator view used to route or diagnose a scan is not a capture artifact and
must not be packetized or admitted to the lake.

A repeat semantic refresh with the same working route, capture plan, and
projector does **not** request a screenshot merely because an earlier packet
contained one. When no visual trigger applies, omit the screenshot at
acquisition; do not create it and then rely on content-mode retention to remove
it. When a screenshot is requested, the capture plan or receipt names the
trigger. Existing packets and any screenshot already supplied to a packet
writer remain immutable and preserved.

Rendered UI overlays use a shared classification contract with route-owned
actions:

- A `benign_dismissible_overlay` is a non-content UI layer such as a cookie or
  teaching prompt with no CAPTCHA, challenge/security, login/auth, payment, or
  account-risk marker.
- The shared runner may execute only a **named, route-owned action spec** that
  binds the overlay markers, exact allowed control or bounded control sequence,
  forbidden controls, and post-click verification. CloakBrowser, Chrome CDP,
  or another browser backend is the transport; it does not decide what to
  click.
- For cookie consent, prefer an exact `Reject`, `Decline`, `Necessary only`, or
  `Continue without accepting` path. A settings path is allowed only when the
  complete route-owned sequence deterministically reaches the same
  non-consent outcome. Never select `Accept`, `Accept all`, or an equivalent
  consent-granting control to make capture easier.
- A free-form model/vision guess, generic X, broad text match, or coordinate
  click is not an action spec. An unknown or ambiguous overlay is not
  auto-dismissed; stop, preserve a diagnostic receipt, and request a mapped
  route or owner intervention.
- Success requires the expected overlay to be absent after the action and the
  intended page content to remain reachable. Record the classification, named
  action, sanitized target identity, outcome, and postcondition without cookie,
  storage-state, credential, or clearance-token values. Only then capture the
  normal DOM/text and any independently triggered screenshot. A failed
  dismissal may preserve one diagnostic screenshot, labeled as overlay
  evidence rather than unobstructed source-content evidence.

This contract is site-agnostic at the classification, action, receipt, and
failure boundaries. Detection selectors, control sequences, and postconditions
stay source/CMP-owned until repeated implementations prove a safe shared
adapter. It does not authorize CAPTCHA solving, challenge closing, login-wall
handling, or generic visual clicking.

## Step 3 — The verdict + receipt

- **GO:** source-native content captured AND independently checkable — raw bytes/hash, magic bytes
  for files, a DOM/source excerpt with URL+timestamp, an embedded field+value anchor, or equivalent
  route-native evidence. Paraphrased / summarized / reconstructed / only-asserted -> **PARTIAL**.
- **PARTIAL:** reachable but fidelity-limited (paraphrase / asserted-only) or partial coverage
  (availability without body; first page only; bounded enumeration).
- **NO-GO:** not capturable within the access boundary — record *why* (matching routes tried; or the
  auth/access-control gate that can't be legitimately passed). When the terminal failure mode was
  empty or erroring probe output, the receipt must show the Guardrail 4 instrument check
  (known-positive control or second independent method).
- **CATALOG_GAP:** capture is in-scope (public, not auth-gated) but this playbook has no matching
  route for the substrate/problem (e.g. mobile/app-only). Record the missing-route candidate; do
  **not** call it NO-GO.
- **Receipt (every run):** access classification · routes tried · routes considered-but-skipped and
  why · lake preflight surface and reusable packet decision when applicable ·
  named decision-material information job · recapture reason when reuse was
  rejected · caller-bound detail requirements and sufficiency result · evidence
  locator for each attempt · fidelity evidence · request rate / volume · why it
  stopped · current/recent state preserved when relevant · verdict · routes now
  forbidden without a new fact.

GO, PARTIAL, NO-GO, and CATALOG_GAP describe fulfillment of the bounded capture
request only. They do not decide evidence-world completeness, Scanning closure,
or final packet inclusion. No capture count or target count establishes
completion.

## The output: a recipe card (the growing tail — authored by probes, not here)

A probe banks a card: `{source, substrate, route that worked, triggers, content-anchor, candidate
adapter shape, access posture, request-rate ceiling, known false-diagnoses}`. Cards compound; the
method stays stable. TikTok is the first *intended* probe target — its card (or NO-GO / PARTIAL /
CATALOG_GAP) is authored by that probe, not here.

### Recipe card — Google Trends search-interest, browser route (banked 2026-08-06)

Probe-authored card from the 2026-08-05/06 Summer Fridays bounded one-shot pulls (13/13 + 6/6
COMPLETE). This subsection is a probe-banked catalog amendment; it is outside the original
de-correlated review's scope. Semantics and limits (relative index, pins, thresholds) are owned by
`forseti/product/spines/capture/core/demand_durability_indicators/search_interest/demand_durability_indicator_search_interest_capture_profile_v0.md`
and are not restated here.

- **source:** Google Trends web UI (`trends.google.com`), web-search and Shopping properties.
- **substrate:** the page's own internal API — `POST /trends/api/explore` mints per-widget tokens
  (cheap; never rate-limited across ~25 same-day calls); `GET /trends/api/widgetdata/multiline|relatedsearches?req=…&token=…`
  returns the data (aggressively quota'd; the scarce resource). Responses carry an XSSI prefix
  (`)]}'`) to strip. Multi-term explores emit indexed related-query widget ids
  (`RELATED_QUERIES_0..N` with `keywordName`); single-term explores emit unsuffixed ids. Shopping
  property (`froogle`) rides the same endpoints, token scheme, and quota pool.
- **route that worked:** embedded-state / internal-API extract via an in-page browser session —
  homepage-first to establish the session (direct `/trends/explore` navigation without one 429s),
  then in-page `fetch()` of explore + widgetdata with session cookies, driven by an injected
  sequential runner.
- **access posture:** publicly-viewable-but-ToS-restricted; human-rate under the Risk posture.
  Google stamps `userType: USER_TYPE_SCRAPER` into its own tokens by **IP reputation, not browser
  environment** — an automation pane, the owner's real signed-in Chrome, and a datacenter VPN
  egress all received the same flag same-day. Datacenter/VPN ranges (observed: AS60068) are
  pre-flagged; a residential IP is the meaningful variable, not the browser.
- **request-rate ceiling (observed 2026-08-05/06, one machine — engineering priors, not stable
  Google behavior):** a fresh day grants the first 1–2 `widgetdata` pulls instantly, then drip
  recovery with successes ~20 min–2.5 h apart. 55–75s pacing ran too hot; the working pattern was
  paced first attempts, one 120–150s-cooloff retry, then escalating patient rounds (7–45 min).
  One observed case: an owner-instructed 1/min burst landed on round 3 after ~10-min rounds had
  failed for ~40 min — recovery windows may be short enough for slow polling to miss; single case,
  not yet method.
- **content-anchor:** `default.timelineData[].value[i]` per term (weekly points; `isPartial` on the
  trailing week), keyword order pinned by the paired explore receipt; related panels under
  `default.rankedList[]`.
- **extraction paths by surface:** app-embedded browser pane → POST raw bodies to a localhost
  receiver (works; append-only sha256 manifest). Real Chrome via extension → localhost is gated
  behind the local-network permission (fetch hangs) and the extension blocks base64 tool returns
  (exfiltration guard); the working path is bundling all captures into **one** JSON blob-download
  per session — Chrome silently blocks a tab's second programmatic download until the operator
  allows multiple downloads.
- **known false-diagnoses:** an undisplayed automation pane never fires the page's own chart
  requests (lazy rendering) — absent widget traffic is not a block; `pytrends` 429-on-first-probe
  is a dead route symptom, not source absence; a mostly-zero Shopping series is threshold sparsity
  plus an apparent trailing ~5–7-week reporting lag (right-truncation) — never read trailing
  Shopping zeros as decline; below-threshold rows are threshold artifacts, never "no interest."
- **provenance:** `docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md`
  (§2 receipts, §9 ledger) and
  `docs/research/summer_fridays_ci_inputs_20260806/search_interest_addendum_return.md` (§7 method
  lessons); verbatim raw bodies with sha256 manifests at the machine-local raw roots named there.
- **authorization note:** this card is method, not sourcing authority — Trends pulls run only under
  a bounded owner authorization (the per-run Phase A category-benchmark class, or an explicit
  one-shot commission); the standing series remains unsourced (AR-04).

## Reuse the pin: probe once, then go direct (capture economy)

The banked recipe card / recon-index entry **is the pin**. Once a probe finds the working route for a
source (or the per-archive rung for historical capture), steady-state fetches go **direct to the
pinned route** — do not re-walk the catalog or re-climb rungs on every fetch. Re-probe (re-run the
method) when the pinned route fails **or its output degrades** (slice-G verification / quality
sub-floor — not just transport; a stale pin can still return HTTP 200) — then it is a fresh symptom
under Guardrail 4.
The catalog is a discovery tool, not a per-fetch cost. Distilled cell: `probe-then-pin-rung` in
`docs/decisions/distillation_binding_data_capture_v0.md` (held; the automated dispatcher form is
capture-spine spec slice F, pending build).

Route reuse and evidence reuse are separate. The pin chooses the capture method;
the lake-first preflight decides whether capture is needed at all. Reuse an
appropriate existing packet before recapture unless the bounded request records
a material currentness, fidelity, provenance, cutoff-compliance, inspectability,
or named-gap reason to reacquire.

### Launch and session economy

Once the target, access classification, authorization, entitled session or
logged-out posture, working pinned route, output destination, and challenge
stop/handoff policy are confirmed, the live operation is **ready to launch**.
Start it then. Branch/PR archaeology, broad repository history, downstream
ranking, and other non-blocking orientation must not delay the live start. If
another read is claimed to be blocking, name the launch invariant it verifies;
otherwise run it after launch, concurrently where safe, or omit it.

A bounded multi-page rendered-browser run leases **one browser, one context, and
one tab** for the run. Navigate that tab forward and detach per-capture
listeners or routes between pages; navigation is not a reason to relaunch.
Per-item
browser isolation is allowed only when a source-specific safety or correctness
requirement names why reuse is unsafe; the receipt must record that policy.
Multi-page receipts record browser-launch count, context-creation count,
page-creation count, page-reuse policy, capture attempt/success counts, and
close state. A runner that silently creates one
browser per item is a lifecycle defect, not a conservative default. Single-page
runs are unaffected.

Cadence stays source- and route-specific: reuse the measured recipe-card value
instead of inheriting a slower discovery/probe default. A faster measured
cadence never weakens challenge stops, owner handoff, access boundaries, or
failure visibility.

In a multi-host run, the first confirmed challenge pauses the affected host and
surfaces an owner handoff immediately; unrelated healthy hosts may finish their
already-authorized work. A fresh owner-attested egress or route change is a new
environment and may release that host without spending its fallback cooldown.
The controller never rotates VPN endpoints automatically and never records an
endpoint, server, credential, or exit IP. If the owner makes no route change,
the source-specific cooldown remains the bounded recovery path. Either recovery
must be an explicit state transition, never a hot retry hidden inside the
capture loop.

## Known gaps (honest)

- **No route for mobile/app-only substrate.** If a probe finds the signal lives only in a phone app
  with no public web surface, that's a **CATALOG_GAP / catalog amendment** (a new route), not a
  default NO-GO.
- **TikTok is partial, not absent.** First-slice and Funmi N30 parsed-batch admission evidence
  exist, with live-runner blocker/admission doctrine now pinned in the TikTok playbook; cross-
  creator durability, detection ceiling, account safety, durable media/video, and scale remain
  unproven. Instagram public-web capture is no longer an absent-recon surface: grid, profile-feed,
  discovery, and deep-capture routes have probe evidence in the recon index. Remaining IG media
  residual: durable full media/video preservation is still unproven, and standalone anonymous
  `yt-dlp` audio may return an empty media response even when rendered deep-capture can still
  produce ASR from a transient handle. Login-walled/private IG surfaces remain access-gated.
- **Anti-bot capability is authorized but not yet proven.** Authorization (Risk posture) is not the
  same as a working defeat of a given anti-bot system; whether a specific challenge can be passed
  at human-rate is an engineering question a probe answers.
- **Rate-limited / commercial / entitled APIs** are entitlement / API-contract routes, not anti-bot
  routes; use your own entitled access, don't defeat the auth.
- **Recipe cards: one banked.** The Google Trends browser-route card above (2026-08-06) is the
  first; the tail is otherwise still unauthored.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    New capture routes now default to source-native narrowing plus deterministic
    local extraction before retention, with one broad-surface parity calibration
    per new or materially changed pin and direct narrow-route reuse thereafter.
  trigger: product_doctrine
  related_triggers:
    - architecture_doctrine
    - validation_philosophy
  controlling_sources_updated:
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-loading.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/README.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/source-loading.md
      reason: It already routes Capture work to this playbook; source ownership did not move.
    - path: forseti/product/spines/capture/core/source_families/retail_pdp/retail_pdp_content_cleaning_contract_v0.md
      reason: >
        Its canonical-content, raw-fallback, and no-current-PDP-Projection rules
        already match the new transport economy; no schema or runtime changed.
  recurring_cost: >
    One parity calibration for each new or materially changed narrow route;
    routine captures pay no broad-page or repeated-calibration cost while the pin holds.
  defect_class_caught: >
    Compact feeds or sections that silently alter subject binding, order,
    fields, or coverage, as observed when Soko Glam products.json ignored the
    requested best-selling order.
  non_claims:
    - not runtime implementation
    - not validation or readiness
    - not permission to discard failure evidence
```

```yaml
direction_change_propagation:
  doctrine_changed: >
    Screenshots are now trigger-based source media produced only by active
    Capture, never ordinary CSB or Scanning/radar output, while the
    site-agnostic benign-overlay contract keeps actions deterministic and
    route-owned.
  trigger: product_doctrine
  related_triggers:
    - architecture_doctrine
    - output_authority
  controlling_sources_updated:
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    - docs/workflows/parfumo_targeted_capture_contract_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/orca_repo_map_v0.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/scanning/README.md
    - docs/workflows/forseti_research_engine_map_v0.md
    - forseti-harness/runners/run_parfumo_mgt_capture.py
    - forseti-harness/source_capture/adapters/browser_snapshot.py
  intentionally_not_updated:
    - path: .agents/workflow-overlay/source-loading.md
      reason: >
        It already binds capture-spine work to this playbook; no read-pack owner
        or route changed.
    - path: docs/workflows/orca_repo_map_v0.md
      reason: >
        The repo map routes to this playbook at file level; no new artifact home
        or anchor is needed.
    - path: docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
      reason: >
        Its source-owned benign-overlay and challenge actions already satisfy
        the shared split; no TikTok action or challenge authority changed.
    - path: CSB and Scanning controlling sources
      reason: >
        They already route CSB commission requirements through Scanning
        `capture_request`s into Capture and grant neither upstream lane
        preservation-adapter ownership; no duplicate screenshot rule added.
    - path: runtime browser and Parfumo capture code
      reason: >
        This doctrine unit does not add a generic visual actor or pretend the
        local-artifact Parfumo packet writer owns live page interaction. A
        route-owned executable action remains separate implementation work.
  stale_language_search: >
    rg -n -i "CSB.*screenshot|Scanning.*screenshot|radar.*screenshot|active.Capture|capture_request.*visual"
    forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    docs/workflows/parfumo_targeted_capture_contract_v0.md
    forseti/product/spines/commission_signal_board
    forseti/product/spines/scanning
  stale_language_search_result: >
    Executed 2026-07-18. Hits are the corrected active-Capture rules, their DCP
    search literals, and unrelated existing active-capture risk-posture wording;
    no CSB or Scanning controlling source claims screenshot production or
    preservation-adapter ownership.
  non_claims:
    - not validation
    - not readiness
    - not capture authorization
    - not overlay-action implementation
    - not live-route validation
```

```yaml
direction_change_propagation:
  doctrine_changed: >
    Guardrail 4 now requires an instrument check before promoting an empty or
    erroring probe result into NO-GO, "blocked", or an empty-source verdict
    (same probe method against a known-positive control, or a second
    independent method, inside the existing re-probe bounds); Step 3 NO-GO
    receipts must show that check when the terminal failure mode was
    empty/erroring output.
  trigger: product_doctrine
  related_triggers:
    - validation_philosophy
  controlling_sources_updated:
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    - forseti/product/spines/foundation/vertical_exploration/orca_vertical_exploration_guide_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-loading.md
    - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
    - docs/workflows/orca_repo_map_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/source-loading.md
      reason: >
        Its auto-load binding of capture-spine activity to this playbook is
        unchanged; the new clause is method content owned here.
    - path: forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
      reason: >
        Its lessons already push escalation and re-probe before recording
        NO-GO ("Blocked is a hypothesis, not a verdict"); the verdict-promotion
        precondition is a method rule owned by this playbook, per the
        anti-fork rule.
    - path: docs/workflows/orca_repo_map_v0.md
      reason: >
        The repo map routes to this playbook at file level; no section
        renumbering or anchor change (Guardrail 4 extended in place).
  stale_language_search: >
    rg -in "known-positive|instrument check|second independent method"
    forseti/product/spines .agents/workflow-overlay/
  stale_language_search_result: >
    Executed 2026-07-02 after edits. Hits are the new Guardrail 4 clause, the
    Step 3 NO-GO reference, and this receipt only — no conflicting or
    duplicated verdict-promotion rule elsewhere. The Walker-kit dated sync note
    carries the screening-posture restatement in its own vocabulary
    ("sanity-check the instrument on a known-good public page"). The retired
    demand-read term "hollow" was deliberately avoided in the new clause.
  non_claims:
    - not validation
    - not readiness
    - not capture authorization
    - no claim that past NO-GO receipts are invalidated
```

Earlier inline receipts remain in Git/PR history. The legacy
`docs/decisions/dcp_receipts_archive_v0.md` archive is frozen and receives no
new writes.

## Non-claims

Method doctrine, MVP, review-hardened + owner-risk-amended draft. Not validation/readiness/
acceptance, not legal advice. The Risk posture is an owner risk decision, not a legal opinion;
legal/ToS exposure is real and owner-accepted for the pre-commercial phase. Grants no
capture/build/merge authority; per-operation network approval still required per probe. Distilled
from `capture_recon_index_v0.md`; worktree-pending recon is weaker than merged primary artifacts.

```yaml
direction_change_propagation_note_2026-06-15: >
  Downstream surface of carve-out 2026-06-15 cap-redefinition: cap now counts own
  operating/capture accounts (≤10, starting ≤5), not subject creators; subject-creator
  roster uncapped within the vertical; active capture = attended (human-initiated),
  faster-than-human pace; passive monitoring = human-initiated, time-bounded,
  self-terminating (no discovery during). Risk-posture footer (dossier carve-out
  exception line) updated accordingly. "That carve-out does not change the general
  dossier prohibition" preserved verbatim.
```
