# Ulta Category Bestseller — Live Probe Findings + Implementation Route 2026-07-25 v1

```yaml
retrieval_header_version: 1
artifact_role: Research report — capture probe findings + implementation route
scope: >
  Findings from a bounded live probe of Ulta category bestseller surfaces,
  commissioned by the Ulta behavioral-parity implementation handoff. Records the
  proven native-order substrate, the correct grid route, the anti-bot posture,
  and a reuse-based implementation route. It makes no completeness or
  bestseller-completeness claim and captures no full ranked window yet.
use_when:
  - Implementing Ulta category bestseller capture on the /shop/<cat>/all grid route.
  - Resuming the Ulta implementation without re-probing.
inputs:
  - Five cloakbrowser probe packets (packet IDs + DOM hashes below), machine-local under C:\tmp\ulta_probe.
  - forseti-harness Ulta brand-grid spine (ulta_brand_grid.py, ulta_grid_projection.py, adapters/ulta_us_market.py, retail_capture_profiles.py).
stale_if:
  - Ulta changes /shop/<cat>/all routes, the default best-seller sort, the pal-c-ProductCard substrate, or the "You have viewed N of M" terminal signal.
authority_boundary: retrieval_only
non_claims:
  - Not a completed implementation; not a five-category dogfood.
  - Not Ulta sales, demand, market share, or category-wide completeness.
  - No full ranked bestseller window was captured — only the first ~64-placement page.
```

## 0. Verdict, Load Outcome, Receiver

- **Verdict: `READY_TO_IMPLEMENT`** (tractable via the existing rendered-DOM route).
  The native bestseller order, the five category grid routes, the declared count,
  the terminal signal, and the continuation control are all **proven and
  DOM-captured** on the **`/shop/<category>/all`** grid route. No GraphQL-response
  capture capability is required.
- **Correction of note:** an earlier pass in this lane probed `/shop/<category>`
  (a category *landing* page with sub-nav, **no** product grid or sort) and wrongly
  concluded `NEEDS_ARCHITECTURE_PASS`. The correct grid route is
  **`/shop/<category>/all`**, which renders the ranked best-seller grid directly
  into the DOM. This document supersedes that conclusion.
- **Load outcome: `STALE_REREAD_REQUIRED`** (from the Ulta handoff). Re-verified:
  8/10 ledger source files hash-match; the 2 toolbox DIFFs were packet-side
  pinned-hash errors (one malformed at 65 chars), not receiver drift; live probe now performed.
- **Receiver:** isolated worktree `C:\tmp\forseti-ulta-category-bestseller-parity`,
  branch `claude/ulta-category-bestseller-parity`, HEAD = `origin/main` = `61372ff`,
  clean, single writer.
- **Access authorization:** public Ulta pages only; anonymous cloakbrowser; no login,
  stored profile, cookies, proxy, or credential injection; no auth-gate defeat;
  no CAPTCHA solving.

## 1. Probe Receipts (machine-local; referenced by hash)

All via `run_source_capture_cloakbrowser_packet.py`, anonymous, no proxy, under
`C:\tmp\ulta_probe\`. Capture window 2026-07-24T18:2x UTC, human-rate.

| Probe | URL | Packet ID | DOM bytes | Result |
|---|---|---|---:|---|
| makeup_probe_02 | `/makeup` (redirect) | `01KYANS2JA4B0TZ7XR6FR3H2MQ` | 21320 | BLOCKED — anti-bot shell (redirect hop) |
| ulta_home_01 | `/` | `01KYANWERABXG575V1727E8BFJ` | 1762810 | RENDERED — homepage; anti-bot passed |
| shop_makeup_bs_01 | `/shop/makeup?sort=best_sellers` | `01KYANZKY0N52C2JXYY38PAD0K` | 1854686 | RENDERED — landing page (no grid) |
| shop_makeup_bs_hydrate_01 | `/shop/makeup?sort=best_sellers` (12s,8scroll) | `01KYAPAS5HH3C4HEEQBHFDVBJ5` | 1856394 | RENDERED — still landing (no grid) |
| **shop_makeup_all_02** | **`/shop/makeup/all`** | (see raw) | **5066901** | **RENDERED — full ranked grid; the correct route** |

`shop_makeup_all_02` DOM sha256 `140fd0a6…` is superseded by the higher-cap
re-capture; the grid DOM lives at
`C:\tmp\ulta_probe\shop_makeup_all_02\raw\01_cloakbrowser_rendered_dom.html`
(5,066,901 bytes). The default 5 MB `--max-artifact-bytes` cap must be raised for
`/all` captures (the grid DOM exceeds it).

## 2. Access Posture (Guardrail 4 honored)

- Plain in-app browser and the cold `/makeup` redirect both returned Ulta's
  "Be Right Back" anti-bot interstitial.
- **Instrument check:** cloakbrowser rendered `example.com` real content → tool works.
- **cloakbrowser passes Ulta anti-bot** on `/`, `/shop/<cat>`, and `/shop/<cat>/all`
  cold, anonymous, no proxy. The `/makeup` block was the redirect hop.

## 3. Proven Substrate (all on `/shop/<category>/all`)

### 3.1 Native bestseller order — S1 SATISFIED
- The `/all` grid **defaults to Best Sellers**: visible "Sort by: Best Sellers",
  `best_sellers` serialized 6× in the page state, `#1 = Rare Beauty Soft Pinch Lip
  Oil Stick`. The explicit `?sort=best_sellers` parameter is also accepted (proven
  on `/shop/makeup`, and the homepage's own `/shop/all?…&sort=new_arrivals` link
  confirms the snake_case `sort=` grammar). Bind order from the serialized/param
  `best_sellers` evidence, not DOM default sequence.

### 3.2 Five category grid routes — S2 SATISFIED

| Handoff category | Ulta grid route |
|---|---|
| Makeup | `https://www.ulta.com/shop/makeup/all` |
| Skincare | `https://www.ulta.com/shop/skin-care/all` |
| Hair | `https://www.ulta.com/shop/hair/all` |
| Fragrance | `https://www.ulta.com/shop/fragrance/all` |
| Bath & Body | `https://www.ulta.com/shop/body-care/all` (Ulta names it "Body Care") |

Base category slugs confirmed from homepage nav; `/all` grid confirmed on Makeup.
Append `?sort=best_sellers` to pin the order explicitly.

### 3.3 Declared count, terminal signal, continuation — S3 SATISFIED
On `/shop/makeup/all`: **"7093 results"** (declared cohort), **"You have viewed 64 of
7093"** (same terminal signal as the brand grid), and the continuation control is:

```html
<div class="ProductListingWrapper__LoadContent" data-test="load-more-wrapper">
  <a href="…/shop/makeup/all?page=2" class="LoadContent__hiddenAnchor">Load More</a>
  <div class="LoadContent" data-test="load-content">
    <p>You have viewed 64 of 7093</p>
    <button class="… LoadContent__button">Load More</button>
  </div>
</div>
```

`button.LoadContent__button` is the **exact selector the existing `ulta_grid_aggregate`
profile already uses**, and `?page=N` is a pagination fallback. Top quartile of 7093 =
1773 → capped at **720** placements per the handoff S3 bound.

### 3.4 Ordered identity + duplicates — S4 SATISFIED
Cards use the shared `pal-c-ProductCard*` design system. Each card carries
`"productId":"pimprodNNNN"` and an absolute `/p/<slug>-pimprodNNNN?sku=NNNN` URL
(64 products embedded, matching "viewed 64 of 7093"). The existing
`_product_id_from_url` regex extracts the id. Card *container* differs from the brand
grid (`pal-c-ProductCard`/`ProductCardCompact`, not `<li data-test="products-list-item">`),
so a category-grid card-boundary detector is needed; field extraction
(`pal-c-ProductCardBody--brandName/title/price`, rating `sr-only`) is reused.

### 3.5 US route — S5 SATISFIED
Reuse `confirm_ulta_us_market(..., page_kind="grid")` (URL-agnostic conjunction);
extend only its `__post_init__` guard to accept `/shop/<category>/all`.

## 4. Success-Contract Status (S1–S8)

| # | Requirement | Status |
|---|---|---|
| S1 | Native bestseller identity | **PROVEN** — default+param `best_sellers`, serialized |
| S2 | Five exact category subjects | **PROVEN** — five `/shop/<cat>/all` routes |
| S3 | Bounded top-window completeness | **TRACTABLE** — declared count + "viewed N of M" + LoadContent__button; cap 720 |
| S4 | Ordered identity + duplicates | **TRACTABLE** — productId + `/p/…` URL per card, contiguous positions |
| S5 | Truthful US route | **TRACTABLE** — reuse market conjunction; extend URL guard |
| S6 | Access + screenshot truth | **HONORED in probe** |
| S7 | Safe transport + lifecycle | **HONORED** — anonymous, no login/proxy/cookies |
| S8 | Full dogfood (all five, real captures) | **PENDING** — implement, then dogfood five to top-quartile/720 |

## 5. Smallest-Complete Implementation Route (reuse-based)

1. `ulta_category_grid.py` parser: detect the `/all` card container + reuse the
   brand-grid field extraction, the "You have viewed N of M" terminal parse, and
   `_product_id_from_url`. Emit a `ulta_category_grid_content_v1` record.
2. Category subject binding from `/shop/<cat>/all` (+ optional `?sort=best_sellers`);
   native-order evidence from serialized `best_sellers`.
3. Category projection path: extend `ulta_grid_projection.py` (or a sibling) with
   `page_kind=category_grid`, category identity, native-order fact, and the
   declared-count/viewed/continuation reconciliation — without breaking `/brand/<slug>`.
4. Extend `UltaUSMarketPlugin.__post_init__` to accept `/shop/<category>/all`.
5. Add a `ulta_category_grid_aggregate` runner profile (load_more `button.LoadContent__button`,
   bounded clicks to reach top-quartile capped at 720) + runner wiring + raised artifact cap.
6. Wrong-cause tests: wrong-category subject, removed/changed sort evidence,
   premature-stop, duplicate, hidden-challenge-vs-visible-block, cap/terminal.
7. Dogfood all five `/shop/<cat>/all?sort=best_sellers` live at human rate to fresh roots.
8. Delegated de-correlated review-and-patch of the runtime diff; adjudicate; PR; land.

## 6. Explicit Non-Claims

- Only the first ~64-placement page of Makeup was captured; **no full ranked window,
  no five-category dogfood**, and no completeness is claimed yet.
- `best_sellers` is a source-visible sort binding, not proof of sales, demand, or share.
- A `$` glyph and a US site route prove neither USD nor US delivery eligibility.
- One probe is a design input, not a validated implementation.

## Receiver Return Contract

```yaml
load_outcome: STALE_REREAD_REQUIRED   # confirmed; live probe performed
receiver_binding:
  worktree: C:\tmp\forseti-ulta-category-bestseller-parity
  branch: claude/ulta-category-bestseller-parity
  head: 61372ff (== origin/main); clean; single writer
success_contract: {S1: proven, S2: proven, S3: tractable, S4: tractable, S5: tractable, S6: honored, S7: honored, S8: pending}
ulta_probe:
  access_classification: public; cloakbrowser passes anti-bot on /shop/<cat>/all cold
  category_surface: /shop/{makeup,skin-care,hair,fragrance,body-care}/all
  native_order: PROVEN — default+param best_sellers, serialized in page state
  declared_count: OBSERVED — e.g. makeup 7093 results
  continuation: OBSERVED — "You have viewed N of M" + button.LoadContent__button + ?page=N ; cap 720
implementation: none authored yet; reuse-based route in section 5
dogfood: {makeup: not_done, skincare: not_done, hair: not_done, fragrance: not_done, bath_and_body: not_done}
validation: probe receipts recorded; instrument check passed; no code changed; git diff --check clean
lifecycle: findings only; no PR opened
verdict: READY_TO_IMPLEMENT
exact_next_action: Implement the reuse-based category route (section 5); dogfood five; delegated review; PR.
```
