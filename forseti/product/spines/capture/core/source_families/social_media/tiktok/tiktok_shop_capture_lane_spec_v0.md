# TikTok Shop Storefront and PDP Capture Lane v0

```yaml
retrieval_header_version: 1
artifact_role: Capture spec
scope: >
  Operator-supervised, routed-real-browser capture of a public TikTok Shop US
  brand storefront, its complete visible PDP denominator, and product-linked
  creator-video shelves.
use_when:
  - Capturing or reviewing a TikTok Shop brand storefront and its PDPs.
  - Interpreting TikTok Shop creator-shelf counts, hearts, offers, or route failures.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
  - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
  - forseti/product/spines/data_lake/README.md
stale_if:
  - TikTok Shop changes its store-card, PDP offer, seller-return, creator-shelf, or challenge surfaces.
  - The shared TikTok humanized browser-input substrate or data-lake packet contract changes.
```

## Bound Outcome

Capture the current public product denominator exposed by one official TikTok
Shop US brand storefront. For every unique listing reached from that storefront,
preserve the PDP offer state and the complete product-linked creator shelf that
the page exposes. Admit the results to the Forseti Data Lake as inspectable
Source Capture Packets.

This is a distinct route from TikTok creator onboarding. It reuses the shared
TikTok browser-input and challenge-observation substrate but owns the Shop
storefront, PDP, seller-return, offer, and creator-shelf sequence.

## Evidence Boundary

The first proving run was the official Summer Fridays storefront on 2026-07-26:

- 30 of 30 unique storefront listings reached through native store-card
  navigation;
- 569 product-linked creator cards captured across those PDPs;
- 307 distinct displayed creator-name strings;
- 555 cards explicitly displayed `Creator earns commission`;
- 889,220 gross visible hearts;
- one slider challenge, cleared manually by the operator after the agent
  stopped; and
- one transient `ERR_TUNNEL_CONNECTION_FAILED` while the routed profile
  remained enabled.

The authoritative raw packets are:

| Packet | Source surface | What it preserves |
| --- | --- | --- |
| `01KYFJPW9SMCJAE1EFS4ZGRHFC` | `tiktok_shop_listing` | Corrected 30-PDP offer capture and the run-order timing-policy transition. |
| `01KYFJJXWCDFH2GCCZGEJ3MXF5` | `tiktok_shop_creator_video` | Product-linked creator shelves across all 30 PDPs. |
| `01KYFJPWN8VAVMHB8TME5RV3ZV` | `tiktok_shop_capture_route_receipt` | Sanitized timing, challenge, failure, and recovery evidence. |

This N=1 brand run proves the route and data shape, not unattended operation,
cross-brand selector stability, scale safety, or a stable challenge ceiling.

## Route and Session Contract

1. Use the owner-selected, headed, routed real-Chrome profile reserved for the
   TikTok lane. Do not use headless or a cold ad-hoc browser.
2. Do not reuse an egress or browser profile reserved for another platform
   lane. In particular, a Meta-reserved route is not a TikTok Shop route.
3. Before opening TikTok Shop for each access session, freshly observe `US`
   country egress in that same browser context under the parent TikTok lane's
   US-egress gate. Country is retained; exit IP, provider/profile identity,
   credentials, endpoints, cookies, and local profile paths are not.
4. Begin from the official brand storefront. A direct store URL is an allowed
   session entry or recovery anchor; direct PDP `goto` navigation is not the
   collection route.
5. Treat a tunnel error as transport evidence, not proof that the proxy was
   disabled and not proof of a TikTok block. Inspect only category-level route
   posture, attempt one bounded recovery, and freshly recheck US egress after a
   reconnect or identity change.

## Shared Humanized Interaction

Use the current TikTok creator-onboarding humanized input substrate as the
single owner of pointer curves, target insets, wheel chunks, and CloakBrowser
`careful` behavior:

- select visible semantic targets, not cached absolute pixels;
- use native store cards, seller links, back controls, carousel controls, and
  other page-owned navigation;
- prefer the shared `BrowserPagePointerAction` / humanized pointer layer when
  the active controller exposes it;
- if that exact layer is unavailable, record the fallback and use the current
  routed-Chrome controller against visible semantic targets; never claim that
  CloakBrowser `careful` behavior ran when it did not;
- do not add decorative wheel actions: after the first receipt proves zero
  actual scroll movement for that surface, suppress further no-op wheels; and
- never interact faster merely because the DOM extraction is complete.

The Shop lane must not fork the creator-onboarding pointer implementation or
freeze its numeric motion internals here.

## Timing and Volume Envelope

Choose each page interval independently; do not target a fixed median:

- absolute minimum: `4.9 s`;
- ordinary band: `4.9–36.5 s`;
- long-tail band: `36.5–66.0 s`;
- long-tail probability: `10%`.

Apply variation to PDP dwell, store return, and the next native card selection.
Do not use a fixed three-second seller-return settle.

Run in microbatches of 8–10 successful PDPs, then linger or cool down on the
storefront before continuing. The first proving run's challenge appeared after
17 successful PDPs and on the 19th native PDP entry when one retained failed
attempt is counted, just beyond an observed ten-minute sticky-session window.
That correlation supports microbatching and fresh route-continuity checks; it
does not prove causation or a universal limit.

## Storefront-to-PDP Sequence

1. Read the official storefront's complete visible product-card set and retain
   its unique listing identifiers as the run denominator.
2. Select an unvisited card from the store and open it through the card's native
   interaction. Random order is allowed; listing-ID deduplication is required.
3. On the PDP, bind the served listing/product identity before recording any
   fields.
4. Capture the offer aggregate and creator shelf under the contracts below.
5. Return through `Sold by <brand>` when it is visible. Otherwise use the
   browser back action only when the run arrived from that storefront and the
   returned store identity is verified.
6. Continue from the store. Do not substitute direct PDP URLs for failed card
   navigation.
7. Stop only when every denominator listing is captured or every unresolved
   listing has a typed failure with an explicit reason.

The storefront's `Shop review` rail is discovery context, not PDP price
authority. Product price, discount, shipping, availability, and product-linked
creator evidence come from the served PDP.

## PDP Offer Contract

Preserve the following source-observed fields per unique listing:

1. listing ID and bound product title;
2. `Striked price`;
3. `Current price`;
4. visible discount text or rate;
5. shipping text, including free-shipping text when displayed;
6. availability text;
7. rating aggregate;
8. review-count aggregate;
9. sold aggregate; and
10. capture time, storefront binding, visible missingness, and limitations.

The downstream display order is deliberately `Striked price` above `Current
price`. Preserve source text separately from normalized numeric values; do not
invent a struck value when the PDP exposes only a current price.

TikTok Shop review bodies are excluded by default. Rating and review-count
aggregates remain useful descriptive PDP fields, but review-body collection
requires a separate commission.

## Product-Linked Creator-Shelf Contract

Treat `Videos for this product` as a PDP-bound shelf, not a shop-wide creator
census.

1. Inspect the rendered DOM first.
2. If the DOM already contains the complete shelf, capture it without redundant
   carousel clicks.
3. If the shelf is lazy or only partially rendered, advance its native `>`
   control with the same timing/interaction posture until a complete cycle
   produces no new card identity.
4. Deduplicate by canonical video ID/URL when exposed. When TikTok exposes
   neither, retain each card's source order plus a composite of displayed
   creator name, caption, visible hearts, and commission label; record the
   identifier limitation.

Preserve per card:

- bound listing ID;
- shelf order;
- displayed creator name exactly as shown;
- creator handle or creator ID only when source-exposed;
- caption/snippet exactly as shown;
- visible heart count;
- exact `Creator earns commission` presence/absence;
- canonical video ID/URL when source-exposed; and
- typed missingness and capture limitations.

Never infer commission from shelf membership. Never convert a displayed name
into a handle or creator identity without source evidence.

## Challenge and Failure Behavior

- On any slider/CAPTCHA or unresolved challenge, stop all agent interaction and
  alert the operator immediately.
- The agent does not drag, solve, or dismiss a slider. It may wait while the
  operator acts manually.
- Continue only after the challenge is visibly absent and the same PDP or
  storefront identity is rebound. Record the challenge phase, operator-pause
  boundary, and resumed route separately; operator time is not active dwell.
- A transport/tunnel failure, DOM-read timeout, missing shelf, and TikTok
  challenge are distinct typed outcomes.
- Retry at most once through the same native route after a bounded recoverable
  failure. Keep the failed attempt and mark a later successful record as its
  supersession; never erase failure visibility.
- After the run, compare dwell and transition distributions with the challenge
  point. Report metronomicity, proxy/session continuity, cumulative native-entry
  volume, and interaction effectiveness as ranked hypotheses, never as causal
  proof.

## Data-Lake Admission

Use an explicit, verified Forseti data root and the standard packet writer.
Keep three concerns separate when present:

1. PDP offers under `source_family: tiktok_shop` and
   `source_surface: tiktok_shop_listing`;
2. creator shelves under `source_family: tiktok_shop` and
   `source_surface: tiktok_shop_creator_video`; and
3. sanitized route/challenge diagnostics under `source_family: tiktok_shop`
   and `source_surface: tiktok_shop_capture_route_receipt`.

Packetize only after storefront/PDP identity binding and a sensitive-data scan.
Exclude exit IPs, provider/profile names, credentials, proxy endpoints, cookies,
storage state, local browser-profile paths, signed media URLs, and tracking
query material. Preserve raw source observations, capture policy version,
typed failures/supersession, hashes, and packet IDs.

## Claim Discipline

- Distinct displayed creator names are a captured-shelf identity count, not the
  shop's total number of creators.
- Gross visible hearts are an engagement proxy, not reach, impressions, unique
  viewers, conversion, attributed sales, or audience size.
- Product shelf coverage is complete only for the captured PDP denominator and
  the shelf state TikTok exposed during the run.
- Canonical video reach requires a separately source-bound video route; do not
  manufacture it from hearts or creator-card presence.
- A displayed sold aggregate is TikTok's current PDP claim, not independently
  verified transactions.
- The route does not prove physical US presence, future egress continuity,
  account safety, unattended survivability, or cross-brand selector stability.

## Completion Condition

A Shop run is complete when:

- the storefront denominator and every unique listing outcome reconcile;
- every successful PDP has the full offer contract in the required label order;
- every product-linked creator shelf is exhausted or carries explicit
  source-visible missingness;
- challenges, tunnel failures, retries, and supersessions remain visible;
- claim limitations accompany creator-name and heart aggregates;
- admissible outputs are committed to verified Data Lake packets; and
- no secret, route identity, signed media URL, or local-profile material is
  present.

This spec is behavior and capture-contract authority only. It does not authorize
an unattended crawler, CAPTCHA solving, credential automation, account or proxy
rotation, bulk scale, ECR, Cleaning, Judgment, or commercial-readiness claims.
