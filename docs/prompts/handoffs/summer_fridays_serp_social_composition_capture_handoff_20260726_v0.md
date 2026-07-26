# Summer Fridays SERP-to-Social Composition Capture Handoff — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission the primary Summer Fridays search-surface acquisition: a bounded,
  US-parameterized Google SERP composition map synchronized to retained
  platform-native TikTok, Instagram, and YouTube evidence where consequential.
  The output is a supplemental acquisition input for later Deliver-side CI.
use_when:
  - Capturing how Summer Fridays is mediated across Google Search and social/video sources.
  - Extending the existing Summer Fridays social-search discovery lake without duplicating it.
  - Producing a provenance-safe discovery queue and native-platform evidence bundle for Deliver.
authority_boundary: retrieval_only
open_next:
  - docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/instagram/README.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/README.md
  - forseti/product/spines/capture/core/source_families/social_media/youtube/README.md
stale_if:
  - Google Search parameters, AI Overview, result-card, or social-index behavior materially changes.
  - A dedicated Forseti SERP composition runner or accepted search-surface recipe supersedes this route.
  - TikTok, Instagram, or YouTube source-family routes materially change.
  - The existing discovery lake is recaptured or superseded.
```

## Load Contract

- `packet_version`: `20260726_v0`
- `mode`: `max`
- `priority`: primary of the three 2026-07-26 Summer Fridays acquisition handoffs.
- `load_rule`: **confirm-don't-trust**. Confirm all named paths, packet IDs,
  manifests, source-family routes, and query parameters before claims.
- output_mode: `file-write`
- `template_kind`: `none`
- `edit_permission`: `docs-write` for the exact return artifact; bounded external
  capture writes are authorized at the named raw-lake root. Repository
  implementation/runtime code is read-only.
- `reviews`: findings-first; no formal review verdict, severity contract, or patch queue.
- `doctrine_change`: none.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_serp_social_composition_capture_handoff_20260726_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260726/serp_social_composition_capture_return.md`
- `raw_lake_root`: `C:\tmp\forseti-sf-serp-social-composition-20260726\data`
- `existing_discovery_lake`:
  `C:\tmp\forseti-sf-social-search-discovery-20260726\data`
- `existing_tiktok_shop_probe`:
  `C:\tmp\forseti-summer-fridays-tiktok-shop-continuation-20260726\data`
- `workspace`: use a clean receiver-owned Forseti worktree off current
  `origin/main`; do not work in another active Summer Fridays lane.
- `minimum_repository_checkpoint`: `6c5da01ef024f71c33013c10bec05ac65e232c9d`
  must be an ancestor of the receiver's clean `HEAD`, and this handoff must exist
  at that `HEAD`.
- `dirty_state_allowance`: clean initially; only the named return artifact may
  become modified/untracked in the repo. Raw capture data stays outside Git.
- `untracked_files_in_scope`: only the named return artifact if its destination
  directory does not yet exist.
- `repo_map_decision`: not needed; exact prompt, output, method, route, platform,
  and lake paths are bound.
- `controlling_source_state`: re-read and record current state; modified or
  missing controlling sources block strict route claims.

```yaml
forseti_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom
  edit_permission: docs-write
  target_scope: Summer Fridays SERP composition plus bounded TikTok/Instagram/YouTube native follow-through and one return artifact
  dirty_state_checked: yes
  blocked_if_missing: handoff, Google route decision, capture playbook, social source-family routes, existing discovery lake, or writable new raw-lake root
```

If the receiver cannot directly access the repository and both named Windows
lakes, stop and request a source capsule or a correctly placed receiver. Do not
recreate the old lake from chat summaries.

## Goal Handoff

- **Long-term goal:** help Forseti build unusually strong company intelligence
  by observing not only what sources say, but which sources mediate each
  consumer question and then preserving the underlying content.
- **Active objective:** produce a decision-usable composition map of Summer
  Fridays Google Search surfaces across brand, product, review, complaint,
  comparison, and retailer jobs; connect selected TikTok, Instagram, and
  YouTube results to platform-native retained evidence.
- **Fitness reference:** the later Deliver lane can tell who owns each search
  journey, which product/problems are highly mediated by social/community
  sources, where official or retailer sources are absent/present, and which
  social claims survive native-source verification.
- **Done signal:** the existing packets are inventoried rather than duplicated;
  a frozen query board is captured with one packet per query; result cards are
  normalized and deduplicated; selected high-leverage social URLs have native
  capture packets or typed route blockers; AI Overview and snippets remain
  attributed to Google; all source dependencies are explicit.

## Open Decision / Fork

The SERP is both evidence and a pointer:

- It is **primary evidence of the captured Google result composition**.
- It is **not primary evidence of the underlying TikTok/Instagram/YouTube claim**.
  Consequential content claims require platform-native verification.

Use a bounded native follow-through cap rather than trying to capture every
indexed result:

- up to **six TikTok items, six Instagram items, and six YouTube items** across
  the whole query board;
- select by decision leverage, not only rank: official identity, high-engagement
  praise/pain/comparison, an under-covered product family, or visible
  affiliate/paid/retailer mechanics;
- preserve the selection and rejection reasons.

If a platform route is access-gated or fails, return the typed blocker and keep
the SERP row as discovery/mediation evidence only.

## Drift Guard

- Summer Fridays only. Multi-company generalization is future work.
- This is search composition and bounded native verification, not SEO advice,
  content optimization, keyword-volume research, rank tracking, or a standing monitor.
- Do not anchor the query board to the 2026-08-06 body launch. The company and
  portfolio are broader than one event.
- Acquisition only. Do not perform the Deliver join with retailer reviews,
  Reddit, ingredients, paid ads, company claims, legal notices, or the Phase A seal.
- **US-parameterized is not physically US-local.** State this exact non-claim in
  every durable Google search-surface artifact.
- One query capture is composition at a moment. It is not complete, stable,
  representative, or a market-share/prevalence measure.
- Result rank/order is observed source state only. Do not infer demand or
  importance from rank without later typed analysis.
- Google snippets, People Also Ask, related searches, and AI Overview are Google
  mediation/synthesis. They are not independent corroboration of the sources
  they summarize.
- An indexed TikTok/Instagram/YouTube result may be stale or partial. Platform
  native evidence supersedes the snippet for content claims.
- Never turn one product-specific pain into a brand-wide pain. Keep product,
  variant, use condition, and claim separate.
- Preserve failed access, omitted media/comments, removed pages, quiet sources,
  and unavailable native follow-through as typed evidence.
- Public, targeted, human-rate capture only; no auth defeat, private-person
  dossier, secrets, or exit-IP retention.

## Inherited Context

### Existing discovery lake — reuse before recapture

`C:\tmp\forseti-sf-social-search-discovery-20260726\data` contains admitted
Google Search packets from the bound route. Confirm every manifest and source
locator before reuse. The known useful packet IDs include:

| Information job | Packet ID |
| --- | --- |
| official TikTok identity | `01KYDAFTG3TCX73BXX70ENFMQE` |
| Instagram footprint | `01KYDADMPGSGA8NSRRX5FS6MRD` |
| YouTube footprint | `01KYDADZF6S01W5P0N6GSZZNWC` |
| Lip Butter Balm review journey | `01KYDAEB9XYC20752Y9X8EN8QN` |
| TikTok Shop search surface | `01KYDAENGB9DNZK3N6XNFW75MR` |
| Summer Fridays versus Laneige | `01KYDAF1T63NED17PRB0AWMZ0V` |
| Lip Butter Balm burning/reaction | `01KYDAFEGK8Y8PBEWF0A111QCX` |

The lake also contains later repeat packets. Inventory the full availability
index and deduplicate by normalized query plus capture time before deciding
which packets are current/reusable. Direct-HTTP attempts produced Google
JavaScript shells; the rendered browser/CloakBrowser route produced the
source-useful pages in the retained run. This is inherited route evidence, not
permission to skip fresh sufficiency checks.

### Existing TikTok Shop probe

`C:\tmp\forseti-summer-fridays-tiktok-shop-continuation-20260726\data` contains
the intake receipt and indexed-shop extracts. Treat it as route/coverage context.
It does not prove a full TikTok Shop grid, PDP, review-body, creator-attribution,
or US-local capture.

### Lifecycle boundary

The Summer Fridays Phase A corpus and its acquisition seal are separate. The
recovery worktree may be dirty and advancing. Re-read current accepted sources
only to normalize products; do not edit, reopen, or claim to reseal Phase A.
This supplemental evidence is intended for later Deliver.

## Source And Authority Ledger

Re-read these before strict claims:

1. `docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md`
   - authoring compare target SHA-256:
     `5a079e37f9311709c10d0d329386cc4588b2fab4a4b43f8daafa1dd28e2a0b94`
   - role: exact Google Search parameters and locality/coverage non-claims.
2. `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md`
   - authoring compare target SHA-256:
     `aac268200599b047c1a1a8096ed2f683197f484475761c20649a86740494d3f5`
   - role: lake reuse, access gate, route selection, receipts, verdicts.
3. `forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md`
   - authoring compare target SHA-256:
     `22ba2475317a731fc1aeb55ce7ab8004ad39bdc82d44dfb5e0f14c4c68244d58`
   - role: empirical route and social-platform context.
4. Platform route owners:
   - `forseti/product/spines/capture/core/source_families/social_media/tiktok/README.md`
   - `forseti/product/spines/capture/core/source_families/social_media/instagram/README.md`
   - `forseti/product/spines/capture/core/source_families/social_media/youtube/README.md`
   - follow each `open_next` route; do not invent platform capture from this packet.
5. Current accepted Summer Fridays company/portfolio sources under
   `docs/research/summer_fridays_understanding_dogfood_20260725_p10/`
   - role: entity and product-family normalization only;
   - re-read fresh because adjacent recovery sources may advance independently.
6. Existing lake manifests and receipts:
   - role: primary provenance for old query captures;
   - compare by packet ID, source locator, manifest hash, and preserved-file hashes.

## Frozen Query Board

First inventory and reuse exact normalized-query matches from the existing lake.
Recapture an old query only for a recorded currentness, fidelity, provenance, or
coverage improvement. Then capture the missing jobs below, keeping one admitted
packet per query/run:

### Identity and channel composition

1. `site:tiktok.com "summer fridays"`
2. `site:instagram.com "summer fridays" reel`
3. `site:youtube.com "summer fridays" review`
4. `"summer fridays" review`

### Hero product, pain, and comparison

5. `"summer fridays" "lip butter balm" review`
6. `"summer fridays" "lip butter balm" burning OR reaction`
7. `"summer fridays" "lip butter balm" vs`
8. `"summer fridays" "jet lag mask" review OR reaction`

### Portfolio breadth — deliberately unanchored from one launch

9. `"summer fridays" "sheer skin tint" review`
10. `"summer fridays" "flushed lip stain" review`
11. `"summer fridays" "cloud dew" OR "rich cushion" review`
12. `"summer fridays" body fragrance review`

### Retailer/search-journey controls

13. `"summer fridays" sephora review`
14. `"summer fridays" amazon review`
15. `"summer fridays" tiktok shop`

Use the route-owned URL parameters `hl=en`, `gl=us`, and `pws=0`. Record exact
query text, encoded URL, capture timestamp, logged-out/session posture, final URL,
result modules present, and scroll/pagination depth. If Google rewrites a query,
record requested and rendered query separately.

## Exact Next Authorized Action

1. Bind a clean receiver worktree and verify every named path and lake.
2. Inventory the existing discovery lake by packet ID, normalized query,
   capture time, source locator, manifest hash, and route verdict.
3. Freeze a reuse/recapture board against the 15 jobs above. Do not launch
   duplicates without a recorded improvement reason.
4. Capture each missing or justified-refresh query through the bound
   US-parameterized, logged-out-visible route. Use a source-useful browser route;
   keep direct-HTTP shell failures as route evidence, not content.
5. Extract and normalize result composition.
6. Select up to six platform-native items per TikTok/Instagram/YouTube under the
   decision-leverage rule above.
7. Load each platform's current source-family route and capture the selected item
   natively. One failed platform item does not invalidate other queries/items.
8. Write only the named return artifact. Do not edit the Phase A record/seal or
   the two paid-ad handoffs.

## SERP Extraction Contract

For each query and visible result/module, retain when source-visible:

- normalized query, packet ID, manifest path/hash, capture timestamp, route state;
- module type: organic result, video block, social card, People Also Ask,
  related search, retailer/product result, AI Overview, or other typed module;
- observed order within its module and page/scroll depth;
- title, snippet, displayed source/domain, canonical/click URL, visible date/freshness;
- platform, account/creator/publisher, product/family, claim/topic, format;
- visible engagement snippet, price, offer, affiliate/sponsored/commission label,
  retailer/channel, and media-availability state;
- canonical URL after tracking removal;
- dependency label:
  `google_composition_primary`, `google_synthesis_only`,
  `platform_native_verified`, `platform_native_unverified`, or
  `platform_native_blocked`.

For AI Overview:

- preserve the exact visible Google synthesis within source-quotation limits;
- capture the visible cited-source links when exposed;
- never promote its ingredient, efficacy, prevalence, or consumer-consensus text
  into fact without the cited primary evidence.

Deduplicate repeated cards, canonical URLs, cross-module duplicates, and repeated
captures. Preserve changes across capture times as separate observations rather
than overwriting.

## Platform-Native Follow-Through Contract

For each selected social result:

- verify canonical URL, account/channel identity, product/entity, and source item;
- use the current platform-owned capture route;
- retain source-native caption/title/description/transcript when available;
- retain visible publication time, engagement, comments required for the
  specific claim, sponsorship/affiliate labels, and media-omission state;
- keep source-native claims separate from Google snippet wording;
- bind platform packet ID/manifest/source-record pointer back to the SERP row;
- if the platform item is unavailable, access-gated, deleted, or route-failed,
  preserve that state and do not fill the gap from the snippet.

Do not capture every commenter or build creator dossiers. Comments are bounded
to what is necessary to verify the selected claim and its visible resonance.

## Return Artifact Contract

The return artifact must include:

1. executive acquisition conclusion;
2. route and locality receipt;
3. existing-lake inventory and reuse/recapture decisions;
4. query-board completion matrix;
5. per-query composition tables;
6. cross-query source/platform share as **counts of observed result cards only**,
   never prevalence or market share;
7. product/problem coverage matrix;
8. official/retailer/community/creator mediation map;
9. AI Overview and Google-synthesis section;
10. native follow-through selection ledger and platform packet results;
11. independent-source/dependency ledger;
12. failures, omissions, quiet/isolated leads, and misleading matches;
13. complete source evidence bundle with packet IDs, URLs, hashes, and pointers;
14. safe Deliver-side uses and explicit non-claims.

The return may highlight promising joins, but it must not perform the final
retailer/Reddit/ingredient/paid-ad/company synthesis or issue a CI recommendation.

## Validation And Stop Conditions

Before closeout:

- fresh-read the return artifact;
- verify each query row resolves to a retained packet;
- verify each `platform_native_verified` row resolves to a platform packet;
- recompute query, card, domain/platform, product, and follow-through counts;
- verify canonical-URL deduplication and dependency labels;
- verify raw-lake manifests against preserved files using current lake tools;
- run `python -B .agents/hooks/check_search_surface_google_route.py`;
- run `python -B .agents/hooks/header_index.py --strict`;
- run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
- run `git diff --check`.

Report every check as pass, fail, blocked, or not run. A successful browser run
without the required visible result details is not source-useful success.
Failure of one platform route is a typed partial result, not permission to claim
the indexed content as verified. Stop with the nearest explicit blocker if the
Google route, old-lake provenance, packet admission, or output write cannot be
verified.
