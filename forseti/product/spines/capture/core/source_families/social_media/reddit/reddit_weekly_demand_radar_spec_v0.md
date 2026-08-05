# Reddit Weekly Demand Radar Spec v0

```yaml
retrieval_header_version: 1
artifact_role: source_capture_family_architecture_contract
scope: >
  Evidence-layer spec for the weekly Reddit demand radar: one top/?t=week
  listing capture per tracked subreddit (project-default, sampled raw), lake
  registry coupling, agent-written reach observations, and the listing-policy-gated
  thread deep-dive that feeds problem briefs. Owns the weekly method's
  parameters, empirical basis, and the boundary on what a weekly batch may
  trigger; does not own axis semantics, material-addition typing, competitive
  conclusions, or brief format.
use_when:
  - Implementing or reviewing the weekly top/week capture runner, its
    materializer coupling, or the observe verb.
  - Changing listing depth, retention mode, listing review, or dive gate.
  - Onboarding reach observations for new roster subreddits.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_radar_grid_capture_maintenance_design_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_lake_cutover_architecture_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/README.md
stale_if:
  - The registry spec changes its observation row shape or two-speed rule.
  - The radar grid design changes the declared per-subreddit page bound.
  - Reddit's old-web listing markup drops the data-* machine attributes this
    method projects from.
  - The owner changes the commission frame, universal engagement floor, or
    model-adjudication boundary.
  - Phase A changes what a typed material addition may trigger, or retires the
    axis-map prior this handoff reads.
```

## Status

`IMPLEMENTED — OWNER-RECALIBRATED 2026-08-05`. The former engagement-head,
title-rescue, and rotating-tail rule landed in PR #1319 and was then superseded
after owner calibration plus a full-corpus application. The reader now produces
a fail-closed listing-review queue governed by
`reddit_listing_efficiency_policy_v0.md`; it does not authorize capture. The
2026-08-05 recalibration adds the incremental weekly materiality handoff as an
agent/model procedure, not runner behavior, and without turning a weekly batch
into Phase A closure or Judgment authority.

## Goal binding

Surface decision-changing evidence a scaling challenger could use for GTM and
CI while spending exact-thread reads where expected contribution is highest.
The evidence layer captures and ledgers; commission-conditioned selection and
brief writing stay model/agent work outside the neutral lake. Title keywords
may describe visible context but never substitute for that judgment. Condensed
judgment packs are a later, separate layer; nothing here persists analysis
output to the lake.

## Empirical basis (2026-07-22 packets, r/30PlusSkinCare unless noted)

| Finding | Evidence |
|---|---|
| Weekly engagement is head-concentrated: top-10 posts carry 65% of weekly score; only 27 posts clear 50 pts | top/week limit=100 packet `01KY4YP3WA9KBVXW7QVYR04VZF` |
| One page at limit=100 is complete: page 1 floor 2-3 pts; page 2 ceiling 3 pts, 2 of 100 posts >=15 comments | page-2 packet `01KY57ERG6PRHF5K5HR0XCW0F0` |
| Concentration is not a top-filter artifact: every hot post >=4 pts appears in top/week-100 at consistent scores; hot's 8 absentees all scored 0-2 | hot packet `01KY4TGJTEX7AY1VN9RP4BF8KT` cross-reference |
| hot page 1 is non-selective on this size class (median 3.5 pts) and unusable for traction ranking | same hot packet |
| Score is the rot-proof witness sample; follower counts rot (age anti-correlates with density 14y/0.4 vs 3y/30.9 across the 5-sub set) | five top/week packets + SERP bands |
| Discussion density (comments over score, smoothed) separates unmet-need threads from broadcast virality; the week's top-scored post ranked last on density | brief cycle, 5 thread packets, 705 comment bodies |
| Projection is ~25x smaller than raw (27,925 B vs 697,139 B, real packet, full field set) | storage test over `01KY4YP3WA9KBVXW7QVYR04VZF` |
| Columnar serialization saves nothing material once compressed (1.06x); condensation value is presentational, not storage | same test |

## Evidence-layer components

### A. Weekly listing capture (extend `run_reddit_grid_capture.py`; no new runner)

- `--listing` parameter; `top_week` maps to `top/?sort=top&t=week&limit=100`;
  `hot` remains available for trigger-based escalation. Primary pass is
  `top_week`. The declared bound stays one listing page per subreddit per pass.
- Roster comes from the lake registry fold (`known_subreddits`), never a
  hand-typed list.
- Single page only. The reader emits a floor tripwire: if a subreddit's
  page-1 score floor exceeds 50, that subreddit genuinely overflows one page
  and the next pass captures page 2 for it. No standing pagination.
- Packets are `source_family="reddit_subreddit_grid"` with the listing kind
  recorded in the manifest. top/week is a listing of the existing family, not
  a new source family.

### B. Retention: project-default with smallest burn-in (retail v4.1 pattern)

- Default `capture_artifact_mode=content`: project in flight, preserve the
  content record, hash and drop raw. Projection row carries: fullname,
  permalink, title, score, comments, timestamp_utc_ms, stickied,
  flair_or_none; venue envelope carries created_utc.
- **Never raw-only** (owner direction, 2026-07-31). Every admitted packet
  carries a content record. There is no operator-selectable raw-only mode on
  this lane, and no screenshot is captured at all — the projection reads DOM and
  visible text, the access classifier reads the response, and nothing consumes
  the image.
- Both Reddit capture runners call the shared rendered-retention decision helper
  on the `www_realchrome` transport and refuse a raw-only request at the lane
  boundary. Admission or extraction failure preserves raw evidence but withholds
  the content record and returns a non-success capture result.
- Two raw-retention rules, no schedule, no decay curve:
  1. One rotating subreddit per weekly pass keeps raw **in addition to** its
     content record (audit sample; DOM and visible text only). Raw *instead of*
     content is what the earlier rule said and is now forbidden: on 2026-07-30
     the rotating raw-only packet was the single capture in a 91-subreddit pass
     that banked a Reddit login wall and still exited 0, because with no
     projection to fail there was nothing to fail. A content-bearing sample
     cannot do that.
  2. Any packet whose projection returns an anomaly keeps raw (row count
     mismatch vs things seen, zero timestamps, zero permalinks). This is the
     fail-loud fallback, not a retention choice, and it stays.
- Extraction or admission failure is not an admitted packet. Exact DOM and
  visible-text inputs survive; when extraction itself succeeded, the attempted
  content-record digest also survives, but its bytes are withheld so downstream
  readers cannot consume a clean projection of a block shell as source content.
- Accepted residual: a projection gap not caught by either rule loses at most
  the sub-50-point tail for the affected weeks; the head stays recoverable
  via a one-shot `t=month` capture for a month.
- Fleet cost basis, measured on a real 102-row www capture (2026-07-31):
  content record 48.7 KB; DOM + visible text 2.62 MB; the discarded viewport
  screenshot was 9.40 MB, 78% of raw bytes, and contributed nothing to a
  projection audit. At the current 91-subreddit roster that is 0.231 GB/yr for
  content plus 0.136 GB/yr for the weekly audit sample — 0.367 GB/yr against a
  0.5-0.6 GB/yr target. Raw-always on this surface would be 56.9 GB/yr.
- Scope: this never-raw-only rule binds the Reddit lane only. Extending it to
  other rendered capture surfaces is a separate owner decision.

### C. Registry coupling (extend materializer)

- The refresh accepts grid-family packets of either listing and records an
  observation per packet. `source_surface` is `old_reddit_grid_packet` or
  `old_reddit_top_week_packet` on `old.reddit.com`, and
  `www_reddit_grid_packet` or `www_reddit_top_week_packet` on
  `www.reddit.com`; the durable label makes the host cutover visible.
  `source_surface` is provenance, not a grid-observation type discriminator:
  downstream readers must not use the `old_reddit_` prefix as that proxy.
  Each observation also carries the packet-manifest provenance pointer and
  capture-state advance required by the registry spec.
- The materializer may re-project legacy raw-preserved `old.reddit.com` grid
  packets in-read. A `www.reddit.com` packet must carry an admitted content
  record; a raw failure is retained as diagnostic evidence but cannot ledger an
  observation. The packet locator, successful source slice, response final URL,
  and content-record listing URL must all name the same host, path, and query.
- The grid runner's `www_realchrome` transport supplies the rendered caller and
  packet path. The packet reader requires the matching real-Chrome metadata,
  successful access posture, exact final listing identity, and an admitted
  content record before a www packet may ledger an observation.
- The five 2026-07-22 experiment packets (family `reddit_subreddit_venue`)
  stay unledgered as an accepted residual; the first real weekly pass
  supersedes them.

### D. Reach observations: agent-written `observe` verb

- New registry verb writing the existing observation row shape; counts are
  strings, so SERP bands like `"135.3K+"` are legal values. Two nullable row
  fields added: `weekly_visitor_count_or_none`,
  `weekly_contribution_count_or_none` (fold treats absent keys as null; no
  migration).
- The agent is the only writer. Surfaces:
  - `agent_browser_serp_read` — agent reads the Google result band in the
    browser pane.
  - `same_context_browser_panel_read` — agent reads the new-Reddit community
    panel (weekly visitors / contributions) via the operator's logged-in
    Chrome; this is the warm same-context path the lane README reserves, used
    only with the operator present.
- Provenance: session-style string (`agent_browser_session_<date>_serp_q=r/X`),
  matching the existing `operator_browser_session_2026-07-16_no_packet`
  precedent.
- Cadence: none standing. Onboarding pass records a band once when a
  subreddit enters the roster. Re-observe triggers:
  1. A subreddit's measured weekly comments exceed 2x its trailing median
     from prior weekly packets (activity anomaly implies reach may have
     moved), or
  2. A brief's finding needs a current exposure denominator.
- Backfill on implementation: the five test-set bands (5M+, 2.4M+, 135.3K+,
  59.2K+, 14.8K+) and the 30PlusSkinCare panel reading (702K weekly visitors,
  7.6K weekly contributions, operator screenshot 2026-07-22), which currently
  exist only in session chat.

### E. Thread deep-dive gate

- The selection pool is every non-stickied, non-promoted listing row with
  parseable score and comment count. Listing evidence remains preserved whether
  or not a thread is selected.
- Apply only the stable mechanical floor in code. A fresh visible count of
  0–9 comments is suppressed from the general deep-dive queue. A fresh visible
  count of 10+ comments enters model review (raised from 4+ by owner decision
  2026-08-01 on measured dive yield; the policy owns the rationale and the
  do-not-raise-further bound). A zero or negative score is not a
  veto, and an absent/unparseable comment or score cell is recorded as
  unparsed, never coerced to zero.
- Rank review rows within each subreddit by comments descending, then score
  descending, then thread URL. Expose title-signal class, listing-visible
  context reasons, and context sufficiency as non-binding review cues. Do not
  calculate a numeric title-rescue score or auto-select an engagement head.
- The model applies the governing policy in
  `reddit_listing_efficiency_policy_v0.md` against a named Decision Frame and
  records `yes`, `borderline`, or `no` plus reason codes and priority. This
  radar's standing frame is `weekly_latent_problem_gtm_discovery_v0`, defined
  in that policy; it owns the frame-scoped gate readings and the dive budget.
  Opaque/deictic/image-dependent rows remain `borderline` until a cheap
  listing-level preview resolves the missing context; opacity is a reason, not
  a fourth disposition.
- A recorded `yes` or `borderline` may become a
  `run_reddit_old_http_batch.py`-compatible capture slot. The weekly reader
  emits `capture_slots=[]` and
  `capture_list_status=blocked_pending_commission_model_adjudication`.
  Its `--capture-list-output` option fails loudly while that status holds.
  This prevents a mechanical shortlist from masquerading as authorization;
  after adjudication, only a recorded `no` suppresses capture under the governing
  listing-efficiency policy.
- Once selected, capture the complete exposed thread and analyse all captured
  comments. Comment points order evidence for presentation; they are not a
  within-thread stopping rule. Record explicitly named brands, products, and
  ingredients in their stated context (alleged problem/cause, proposed
  solution, recommendation, comparison, praise, or neutral mention).
- When direct HTTP returns a body classified as `block_shell`, the bounded batch
  writes a diagnostic PNG and JSON receipt from the exact preserved response
  bytes. The derivation performs no URL re-fetch, browser access, retry, CAPTCHA
  interaction, proxy use, or alternate access. It is a readable diagnostic
  rendering, not a claim of pixel-faithful browser appearance.
- Bare reCAPTCHA widget markup inside an otherwise visible Reddit login form is
  not a challenge-page signal. Visible human-verification language and the
  existing provider-specific block-shell signals continue to fail closed.

### E.1 Weekly semantic and materiality handoff

The weekly dive is an incremental radar, not a miniature Phase A rerun. Its
agent/model handoff applies the following procedure after source-native thread
capture; the result stays outside the neutral lake unless another owning layer
has separately authorized an analysis artifact.

1. Load the current commission or company axis map as a prior, never as a fixed
   quota. If a decision-relevant customer tension does not fit, nominate a new
   provisional axis instead of forcing it into the old map.
2. For each admitted thread, preserve the listing capture date and available
   engagement counts, then classify its incremental contribution as
   `excluded_after_read`, `usable_only`, `ordinary_corroboration`, or
   `material_addition`. A `material_addition` imports the contract beginning "A
   material addition is limited to" from
   `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`;
   that owning contract determines both the allowed kind and the mandatory
   affected-axis, evidence-reference, and decision-effect fields. Do not restate
   or extend its list here. Content that merely repeats something the current
   axis map already carries is `ordinary_corroboration`, not a material
   addition. A thread may carry more than one contribution when each is
   supported by source-native text.
3. Ordinary corroboration updates the radar's recency and support volume but
   opens no new acquisition. Corroboration becomes a material addition only
   when it changes confidence enough to alter a competitive decision or
   evidence tier; volume alone never does, and same-origin items add no
   independent credit. A weekly contribution is radar state: it does not become
   Phase A axis support until it satisfies that authority's applicable
   source-native coding and independent-origin rules.
4. A typed material addition may open a bounded counterpart or source-native
   follow-up for its affected axis and a directly adjacent axis only when the
   relationship is stated. Do not restart a full search cycle or duplicate the
   query across every source.
5. End the weekly batch with a compact handoff naming: material additions with
   their typed kind, affected axes, and decision effect; ordinary
   corroboration; provisional new axes; affected follow-ups; and `none` where
   no field applies. A zero-material-addition week is a valid radar result; it
   is not proof of Phase A source exhaustion.

This weekly procedure reuses Phase A's discovery discipline without importing
its evidence floors, two-family material-exhaustion test, final semantic
adjudication, delegated seal review, or authority to close/reopen Phase A.
Weekly counts are captured-sample observations, never customer-population
prevalence.

### F. Roster discovery sweep (SERP), and its pacing contract

Discovery is agent-run in the in-app browser pane, never headless and never
stealth: the gate below is a real ceiling, and reaching for an anti-detection
launch profile to pass it is evasion, not capture. CloakBrowser `humanize`
is additionally not wired for arbitrary URLs (it is coupled to the retail
pre-capture profiles), so it is not the tool for this surface.

Query shape:

- `r/<anchor> reddit` on a SINGLE anchor. The related-communities block
  returns 5-8 subreddits with follower bands per query, so **one query is
  already a batch** — the lever is fewer, denser queries, not more queries.
- Multi-`r/` queries suppress the block to one card; keyword-only queries
  usually render no cards at all. Both are wasted requests.

**Pacing contract (measured 2026-07-22):** Google bot-gates on request
*velocity*, not volume.

- Sweep 1 ran ~30 rapid back-to-back navigations and tripped the
  "unusual traffic / not a robot" interstitial.
- Sweep 2 ran 13 navigations with a 4-6 second pause between each and did
  not re-trip it once.
- Therefore: **pause 4-6 seconds between navigations**, and prefer ~5-8
  high-yield anchors per session over many narrow queries.
- Every extraction checks the page for the interstitial before parsing, so a
  gated page is never silently read as an empty result.
- On a gate: STOP the sweep, bank everything already gathered, and ping the
  owner to clear the challenge. The agent never solves it.

Admission gate per find (an add costs one request per weekly pass until it is
retired; `discovery_state: retired` drops a subreddit from `capture_roster`
without deleting its history):

- **Add** on clear beauty-topic fit plus a visible band. No follower floor —
  the density finding says small subreddits punch above their size.
- **Park** (report, do not add) on ambiguous fit, employee/worker subreddits,
  or effectively dead ones (a few hundred members).
- **Skip** on non-beauty (outside the `NICHE_PATHS` vocabulary) or meme
  subreddits.
- **Region:** US/general/product-category only. Country-audience subreddits
  (India, PH, UK, AU, CA) are excluded by owner decision 2026-07-22. Korean
  and Asian beauty stay: they are product categories with large US demand,
  not geographic audiences.

Each find lands as two records: `add` (niche path, venue role,
`candidate_new_subreddit`) and `observe` (the band, surface
`agent_browser_serp_read`). New subreddits enter the next weekly pass
automatically because the runner reads `--roster` from the fold.

## Explicitly out of scope / deferred, with triggers

- Cross-week digest or persisted condensed judgment pack: later layer. E.1's
  non-persisted per-batch handoff is not that artifact. Nothing analysis-shaped
  persists to the lake (candidates are pure functions of packets; recompute
  beats persist until cross-week recurrence work makes recomputation materially
  expensive).
- Columnar or compressed serialization: rejected on measurement (1.06x).
- Daily cadence: trigger-based escalation only (existing radar design
  language), driven by the same activity-anomaly trigger as re-observation.
- New-Reddit capture is bounded to the operator-provided real-Chrome CDP
  transports implemented by the grid and exact-thread runners. It is not a
  headless fallback, crawler, standing schedule, or substitute for the licensing
  track when commercial-grade access is required.
- Reddit Data API: dropped 2026-07-22 (approval-gated, no published timeline).
- Roster expansion beyond 100: the owner set the first target at 100
  (reached 2026-07-22, 38 -> 100 across two sweeps). Further growth uses
  section F unchanged; it is owner-paced and bounded, never a crawler.
- Roster pruning: no longer deferred. The trigger fired on the 2026-07-22
  prune, and `discovery_state: retired` plus `capture_roster` landed with it
  (21 rows retired as of 2026-07-30). See the admission gate in section F.

## Verification bound to implementation

- Unit: observe verb vocabulary and fold behavior; listing mapping; retention
  rules (rotating sample selection, anomaly triggers); materializer surface
  stamping for both listings; projection fields (timestamp, stickied, flair)
  against a stored fixture page.
- Reader policy: verify `0–9` comments are omitted from the model-review queue,
  exactly ten comments enter it, score zero does not veto, listing cues remain
  non-binding, `capture_slots` stays empty, and `--capture-list-output` fails
  closed before writing.
- Live dogfood in the implementing session: backfill the six observations via
  observe and read them back from the fold; run one real top_week roster pass;
  confirm ledger lines (observation + capture_state) for every roster
  subreddit; run the reader over the pass output and confirm the review queue,
  general-floor counts, blocked capture status, and floor tripwire emit.
- Flair caveat carried honestly: flair extraction returned zero on the
  30PlusSkinCare test page and is unverified against a page known to carry
  flairs; the fixture for the projection test must be a SkincareAddiction page
  (tagged posts confirmed present in its weekly listing).
