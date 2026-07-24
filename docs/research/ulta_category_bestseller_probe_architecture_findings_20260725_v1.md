# Ulta Category Bestseller — Live Probe + Architecture-Pass Findings 2026-07-25 v1

```yaml
retrieval_header_version: 1
artifact_role: Research report — capture probe + architecture-pass findings
scope: >
  Findings from a bounded live probe of Ulta category bestseller surfaces,
  commissioned by the Ulta behavioral-parity implementation handoff. Records the
  proven native-order substrate, the confirmed five category routes, the anti-bot
  posture, and the one architecture gap that blocks a truthful five-category
  dogfood. It does not implement capture code and makes no completeness or
  bestseller-completeness claim.
use_when:
  - Deciding how to capture Ulta's client-fetched ranked category grid.
  - Resuming the Ulta category bestseller implementation without re-probing.
inputs:
  - Four cloakbrowser probe packets (packet IDs + DOM hashes below), machine-local under C:\tmp\ulta_probe.
  - forseti-harness Ulta brand-grid spine (ulta_brand_grid.py, ulta_grid_projection.py, adapters/ulta_us_market.py).
stale_if:
  - Ulta changes /shop category routes, the sort request parameter, or the Apollo/SSR render substrate.
  - A capture capability for client-fetched grid responses lands and supersedes this gap.
authority_boundary: retrieval_only
non_claims:
  - Not a completed implementation; not a five-category dogfood.
  - Not Ulta sales, demand, market share, or category-wide completeness.
  - No claim that the ranked bestseller grid was captured — it was not.
```

## 0. Verdict, Load Outcome, Receiver

- **Verdict: `NEEDS_ARCHITECTURE_PASS`.** The native bestseller order, the five
  category routes, and anti-bot feasibility are **proven**. The commissioned
  five-category dogfood is **blocked** by one architecture gap: Ulta's **ranked
  category grid is fetched client-side via an internal GraphQL API and does not
  appear in the rendered-DOM snapshot** the current cloakbrowser route captures,
  nor in the initial SSR Apollo state. Closing it needs a capture-capability
  decision that is an owner-level call (see §5).
- **Load outcome: `STALE_REREAD_REQUIRED`** (from the Ulta handoff). Re-verified:
  8/10 ledger source files hash-match; the 2 toolbox DIFFs were packet-side pinned-hash
  errors (one malformed at 65 chars), not receiver drift; and the lane required a
  fresh live probe, now performed.
- **Receiver:** isolated worktree `C:\tmp\forseti-ulta-category-bestseller-parity`,
  branch `claude/ulta-category-bestseller-parity`, HEAD = `origin/main` = `61372ff`,
  clean, single writer.
- **Access authorization:** public Ulta pages only; anonymous cloakbrowser; no
  login, stored profile, cookies, proxy, or credential injection; no auth-gate
  defeat; no CAPTCHA solving. Per the capture playbook risk posture.

## 1. Probe Receipts (machine-local; referenced by hash)

All four via `run_source_capture_cloakbrowser_packet.py`, anonymous, no proxy,
under `C:\tmp\ulta_probe\`. Capture window 2026-07-24T18:2x UTC, human-rate.

| Probe | URL | Packet ID | DOM bytes | DOM SHA-256 | Result |
|---|---|---|---:|---|---|
| makeup_probe_02 | `/makeup` (redirect path) | `01KYANS2JA4B0TZ7XR6FR3H2MQ` | 21320 | `e49f791fb8b55e276f2528780af3459b90f5aec6e2f537d92d303423c6d0ecef` | **BLOCKED** — "Be Right Back" anti-bot shell (15-byte visible text) |
| ulta_home_01 | `/` | `01KYANWERABXG575V1727E8BFJ` | 1762810 | `968a17ff75c83a367a665600a05fb501d7406ca36ca4f31b6fd6b006c2e8caed` | **RENDERED** — full homepage nav; anti-bot passed |
| shop_makeup_bs_01 | `/shop/makeup?sort=best_sellers` | `01KYANZKY0N52C2JXYY38PAD0K` | 1854686 | `53052ed0725fc957c65a4f32bec9d02d2fb29135f456db7b460d2aa69f14b4f9` | **RENDERED** — category shell + carousels + native sort state; ranked grid absent |
| shop_makeup_bs_hydrate_01 | `/shop/makeup?sort=best_sellers` (12s settle, 8 scrolls) | `01KYAPAS5HH3C4HEEQBHFDVBJ5` | 1856394 | `140fd0a6e2bfd111cc23be8154eea5c0355f8e31201f866a959bb8236d8e8f78` | **RENDERED** — ranked grid still absent after heavy scroll |
| control_example_01 | `https://example.com/` | — | — | — | **Instrument check PASS** — real content rendered |

## 2. Access Posture (Guardrail 4 honored)

- The **plain in-app browser** (no anti-detect) and the **cold deep link `/makeup`**
  both returned Ulta's **"ULTA.com :: Our Apologies / Be Right Back"** anti-bot
  interstitial.
- **Instrument check:** cloakbrowser rendered `example.com` real content → the tool
  is not globally broken; the block is Ulta-specific.
- **Different-hypothesis re-probe:** the Ulta **homepage rendered fully** (1.76 MB),
  and the **canonical grid path `/shop/makeup` rendered cold** (1.85 MB). So the
  `/makeup` block was the **redirect hop**, not a blanket block. **cloakbrowser passes
  Ulta's anti-bot on `/shop/<category>` from this environment, anonymous, no proxy.**
- Classification per the playbook's rendered-access honesty rule: `/shop/<cat>` is
  **not** access-failed (visible source content present); `/makeup` cold **is**
  `access_failed` (visible interstitial).

## 3. Proven Substrate

### 3.1 Native bestseller order — S1 SATISFIABLE
Ulta binds sort in its own serialized render-query state. The captured
`__APOLLO_STATE__` (871 KB) `ROOT_QUERY` field key is **literally**:

```
Page({"moduleParams":{"sort":"best_sellers"},"url":{"path":"/shop/makeup"}})
```

`best_sellers` appears 62× in the serialized state. This is a retailer-owned
request-parameter + serialized-state binding of the order — directly analogous to
Sephora's `BEST_SELLING` PageJSON. The URL parameter form is confirmed by the
homepage's own link `…/shop/all?…&sort=new_arrivals` (snake_case `sort=` values).
**Not** an inferred DOM default order.

### 3.2 Five category routes — S2 SATISFIABLE (all confirmed from homepage nav)

| Handoff category | Ulta route | Note |
|---|---|---|
| Makeup | `https://www.ulta.com/shop/makeup` | |
| Skincare | `https://www.ulta.com/shop/skin-care` | |
| Hair | `https://www.ulta.com/shop/hair` | |
| Fragrance | `https://www.ulta.com/shop/fragrance` | |
| Bath & Body | `https://www.ulta.com/shop/body-care` | Ulta names it **"Body Care"** — closest semantic analog; there is no `/shop/bath-body` |

Category identity is echoed in `dataCapture.metaData` (`pageName=makeup`,
`pageGroup=shop`) and the `Page(...url.path=/shop/<cat>)` query key.

### 3.3 US route — S5 SATISFIABLE
The existing `confirm_ulta_us_market(..., page_kind="grid")` conjunction
(`html lang=en-US` + `window.__APP_LOCALE__=en-US` + `ultasite=en-us`) is URL-agnostic
and reusable. Only its `__post_init__` guard (which hard-requires `/brand/<slug>`)
needs extension to accept `/shop/<category>`.

## 4. The Architecture Gap (why the dogfood is blocked)

**The ranked bestseller grid is client-fetched and not captured.**

- The initial SSR `__APOLLO_STATE__` contains only the page shell + **promotional
  carousels** (`content/modules[1]/modules[10]/items` = 12 "Deals for you" items,
  `modules[11]/items` = 7) — **not** the ranked ~90-per-page bestseller list.
- After 12 s settle + 8 heavy scrolls the rendered DOM still showed
  `products-list-item: 0`, `/p/` product anchors: 120 (carousel/nav baseline,
  unchanged), `productId: 38` (unchanged), and visible text unchanged at ~20 KB.
  The ranked grid never hydrated into the captured DOM.
- Ulta category grids therefore render the ranked list via an **internal GraphQL
  API call after hydration** (the `NonCachedPage`/module query referenced in the
  Apollo `sessionAction.graphql`), which the current rendered-DOM-snapshot route
  neither triggers into the DOM nor records.
- Consequently the **declared category count** and the **continuation/terminal
  state** (pagination vs load-more) for the ranked grid are **inside that
  un-captured fetch** — so S3 (bounded top-window completeness) and S4 (ordered
  identity) **cannot be satisfied by the current route**.

This is exactly the handoff's blocker: *"No trustworthy declared count or terminal
state: return partial or `NEEDS_ARCHITECTURE_PASS`; do not call a click cap
complete."* It is also a **shared-runner capability question**, which the handoff
routes to the owner: *"Required shared abstraction or weakened success claim: stop
for owner decision."*

## 5. Owner Decision Required — Route Forward

Two candidate ways to reach the ranked grid; both are owner-level because they
change a shared capability or touch the access line:

- **Option A — Add rendered-response / XHR capture to the cloakbrowser route.**
  Capture the internal GraphQL **response** for the category module (products, the
  declared total, and pagination cursor) as a preserved artifact, then project from
  it (Sephora-PageJSON-analogous). This is a **shared-runner architecture change**
  (a new capability on `run_source_capture_cloakbrowser_packet.py` /
  `cloakbrowser_snapshot.py`), and it must stay on the page's own public fetch — not
  a hand-constructed private API call.
- **Option B — Force DOM hydration of the ranked grid**, e.g. `--wait-until networkidle`
  plus an interaction that triggers the grid render, then parse rendered cards with a
  **new category-grid DOM parser** (the brand-grid `products-list-item` markers are
  absent here, so the card substrate differs and must be re-derived). Lower lock-in,
  but only viable if the grid actually renders headless — this probe suggests it does
  not without additional triggering, so this needs its own bounded probe.

Recommendation: **Option A** if the internal fetch is a plain page-driven GraphQL
call (it is the retailer's own render path, echoing the `best_sellers` sort) — it
gives the count, order, and continuation directly and matches the Sephora success
shape. Confirm the fetch is page-native (not an auth-gated private API) before
building, and treat the runner capability as the owner-visible lock-in.

## 6. Success-Contract Status (S1–S8)

| # | Requirement | Status |
|---|---|---|
| S1 | Native bestseller identity | **PROVEN** — serialized `moduleParams.sort=best_sellers` |
| S2 | Five exact category subjects | **PROVEN** — five `/shop/<cat>` routes confirmed |
| S3 | Bounded top-window completeness | **BLOCKED** — ranked grid + declared count not captured |
| S4 | Ordered identity + duplicates | **BLOCKED** — ranked list not captured |
| S5 | Truthful US route | **SATISFIABLE** — reuse `confirm_ulta_us_market` (grid), extend URL guard |
| S6 | Access + screenshot truth | **HONORED in probe** — visible-text classification; instrument check + re-probe |
| S7 | Safe transport + lifecycle | **HONORED** — anonymous, no login/proxy/cookies; one browser/context/tab |
| S8 | Full dogfood (all five, real captures) | **NOT DONE** — blocked by the S3/S4 capture gap |

Most-plausible false success (from the handoff) is explicitly **avoided**: no cards
were projected and nothing was labelled bestselling or complete.

## 7. Smallest-Complete Implementation Route (after the S5 owner decision)

1. Resolve §5 (owner): pick Option A (response capture) or B (forced DOM render) and
   accept the named lock-in.
2. Capture the ranked grid for one category; from its response/DOM extract the
   ordered products, the declared category count, and the continuation cursor.
3. Add a category subject + native-order binding (parse the `Page(... sort=best_sellers ...)`
   evidence), a category-aware projection path (extend `ulta_grid_projection.py`
   without breaking `/brand/<slug>` behavior), and extend `UltaUSMarketPlugin.__post_init__`
   to accept `/shop/<category>`.
4. Add a `ulta_category_grid_aggregate` runner profile + wiring.
5. Bound the window to the declared top quartile, capped at 720; reconcile declared
   count, captured placements, unique parents, duplicates, ranks, and terminal state.
6. Add wrong-cause tests: wrong-category subject, removed/changed sort evidence,
   premature-stop, duplicate, hidden-challenge-vs-visible-block, cap/terminal.
7. Dogfood all five categories live at human rate to fresh roots.
8. Delegated de-correlated review-and-patch of the runtime diff; adjudicate; PR; land.

## 8. Explicit Non-Claims

- The ranked bestseller grid was **not captured**; no product, rank, count, or
  completeness is claimed for it.
- `best_sellers` is a source-visible sort binding, **not** proof of sales, demand,
  or market share.
- The five `/shop/<cat>` routes are the current public category surfaces; only
  `/shop/makeup` was rendered this probe. The other four are confirmed as routes,
  not yet captured.
- A `$` glyph and a US site route prove neither USD nor US delivery eligibility.
- One probe is a design input, not a validated implementation.

## Receiver Return Contract

```yaml
load_outcome: STALE_REREAD_REQUIRED   # confirmed; 8/10 source hash-match, 2 packet-side pinned-hash errors, live probe performed
source_context_status:
  overlay_read: AGENTS.md + workflow-overlay README/source-loading/validation-gates
  playbook_read: source_capture_playbook_v0 (access gate, human-rate, rendered-access honesty)
  ulta_spine_read: ulta_brand_grid.py, ulta_grid_projection.py, adapters/ulta_us_market.py, retail_capture_profiles.py, runner CLI
receiver_binding:
  worktree: C:\tmp\forseti-ulta-category-bestseller-parity
  branch: claude/ulta-category-bestseller-parity
  head: 61372ff (== origin/main); clean; single writer
success_contract: {S1: proven, S2: proven, S3: blocked, S4: blocked, S5: satisfiable, S6: honored, S7: honored, S8: not_done}
ulta_probe:
  access_classification: public; cloakbrowser passes anti-bot on /shop/<cat> cold; /makeup redirect blocks; homepage renders
  category_surface: /shop/makeup, /shop/skin-care, /shop/hair, /shop/fragrance, /shop/body-care
  native_order: PROVEN — Apollo ROOT_QUERY "Page({moduleParams:{sort:best_sellers},url:{path:/shop/makeup}})"
  declared_count: NOT OBSERVED — ranked grid is client-fetched, not in SSR/DOM snapshot
  continuation: NOT OBSERVED — pagination-vs-load-more lives in the un-captured fetch
implementation: none authored; route in section 7
dogfood: {makeup: not_done, skincare: not_done, hair: not_done, fragrance: not_done, bath_and_body: not_done, transport: anonymous_no_proxy}
validation: probe receipts hashed (section 1); instrument check passed; no code changed; git diff --check clean
wrong_cause_checks: not_applicable_yet (no implementation); probe honored access classification + instrument check
delegated_review: not_applicable_yet (no runtime diff)
residuals:
  - ranked category grid not captured by current rendered-DOM route (architecture gap)
  - four of five categories confirmed as routes but not rendered
lifecycle: findings only; no PR opened; owner decision required before build
verdict: NEEDS_ARCHITECTURE_PASS
exact_next_action: Owner decides section 5 route (response-capture vs forced-render); then execute section 7.
```
