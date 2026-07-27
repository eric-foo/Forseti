# Reddit Weekly Demand Radar Spec (Proposal v0)

```yaml
retrieval_header_version: 1
artifact_role: source_capture_family_architecture_contract
scope: >
  Evidence-layer spec for the weekly Reddit demand radar: one top/?t=week
  listing capture per tracked subreddit (project-default, sampled raw), lake
  registry coupling, agent-written reach observations, and the density-gated
  thread deep-dive that feeds problem briefs. Owns the weekly method's
  parameters and their empirical basis; does not own analysis or brief format.
use_when:
  - Implementing or reviewing the weekly top/week capture runner, its
    materializer coupling, or the observe verb.
  - Changing listing depth, retention mode, density gate, or dive gate.
  - Onboarding reach observations for new roster subreddits.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_radar_grid_capture_maintenance_design_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_lake_cutover_architecture_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/README.md
stale_if:
  - The registry spec changes its observation row shape or two-speed rule.
  - The radar grid design changes the declared per-subreddit page bound.
  - Reddit's old-web listing markup drops the data-* machine attributes this
    method projects from.
  - The evidence-layer decisions below are implemented and ratified (this
    proposal becomes the record or is superseded).
```

## Status

`IMPLEMENTED — DOGFOOD-REFINED 2026-07-25`. The engagement-head plus title-tail
selection landed in PR #1319. Subsequent lower-tail dogfoods retained the head
and rotating audit, added the absolute engagement rescue, and bound
post-capture resonance to the post or comments that actually carry the claim.
Generic thread archetypes neither route capture nor justify exclusion by
themselves.

## Goal binding

Surface latent problems a company could tackle (GTM + CI), by mining weekly
consolidated traction on tracked subreddits. The evidence layer captures and
ledgers; judgment (thread selection beyond the gate, brief writing) stays
human/agent work outside this spec. Condensed judgment packs are a later,
separate layer; nothing here persists analysis output to the lake.

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
- Two raw-retention rules, no schedule, no decay curve:
  1. One rotating subreddit per weekly pass keeps raw (audit sample).
  2. Any packet whose projection returns an anomaly keeps raw (row count
     mismatch vs things seen, zero timestamps, zero permalinks).
- Accepted residual: a projection gap not caught by either rule loses at most
  the sub-50-point tail for the affected weeks; the head stays recoverable
  via a one-shot `t=month` capture for a month.
- Fleet cost basis: at 250 subreddits, raw-always is ~9.1 GB/yr for this lane;
  project-default with samples is roughly 0.5-0.6 GB/yr.

### C. Registry coupling (extend materializer)

- The refresh accepts grid-family packets of either listing and records an
  observation per packet: `source_surface` is `old_reddit_grid_packet` for hot
  and `old_reddit_top_week_packet` for top/week, provenance pointer to the
  packet manifest, capture_state advance per the registry spec.
- The materializer learns to project raw-preserved grid packets in-read (today
  it only accepts pre-projected content records).
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
- Within each subreddit, rank by comments descending, then score descending,
  then thread URL. Select the top half (rounding up) unconditionally.
- In the lower half, compute a transparent title-rescue score. Pain/failure,
  praise/success, comparison/choice, experience/outcome, or review/update earns
  2 points. A generic question, routine, haul, recommendation, or discussion
  signal earns 1 point. Concrete listing-visible product/ingredient, technique,
  price/value, or variant/constraint context adds 1 point.
- At 1+ listing comments, rescue a title scoring at least 2. At zero comments,
  require 3 points so a thread with no observed discussion carries both a
  strong signal and concrete context. These signals route capture only; they
  are not proof of pain, praise, causation, prevalence, or entity involvement.
- In the lower half, after title rescue, also select every remaining thread
  with at least 5 listing comments or a listing score of at least 25. This
  absolute engagement rescue preserves the relative head while recovering
  resonant threads from unusually active subreddits whose titles hide the
  useful evidence.
- From every remaining lower-tail row, select one deterministic rotating 10%
  audit sample, rounded up with a minimum of one when that tail is non-empty.
  Preserve `opaque_tail_audit` for genuinely opaque titles and
  `weak_signal_tail_audit` for listing-visible signals that did not clear the
  rescue gate. The weekly date, subreddit, and thread URL seed the rotation.
- Emit both the selected rows with their selection reason and a
  `run_reddit_old_http_batch.py`-compatible capture list. The weekly output
  always states eligible threads versus selected threads and reason counts; no
  silent truncation.
- Once selected, capture the complete exposed thread and analyse all captured
  comments. Comment points order evidence for presentation; they are not a
  within-thread stopping rule. Record explicitly named brands, products, and
  ingredients in their stated context (alleged problem/cause, proposed
  solution, recommendation, comparison, praise, or neutral mention).
- Selection routes capture; it does not itself qualify a finding. Post-capture
  qualification binds an explicit decision question and an explicit human
  judgment for decision relevance, signal kind, context kind, whether the post
  itself contains evidence, wedge membership, and any comments that contain
  evidence. Thread archetypes such as showcase, haul, collection, meme, or
  appearance request are not exclusion reasons by themselves. A question-only
  post can route discovery but does not count as an independent observation.
  Missing judgment remains `needs_judgment`.
- Exclusion requires one explicit reason: no transferable claim, appearance
  reaction only, transaction only, entertainment only, or outside the bound
  decision question. A concrete but weakly engaged claim is a `low_lead`, not
  an exclusion. When the decision question does not settle scope, preserve
  `needs_judgment` rather than inventing an off-question decision.
- A decision-relevant, low-engagement thread without independent
  corroboration is a `low_lead`. Multiple low-engagement threads may become a
  `stacked_emerging_signal` only after independent-source checks.
- Count repeated observations conservatively. The same author, a near-identical
  title/body, a crosspost, or the same incident reposted across subreddits
  cannot inflate independent recurrence. Unknown or deleted authors do not
  prove independence.
- A decision-relevant finding with strong audience resonance is a
  `priority_signal`. Resonance belongs to the declared evidence source. The
  thread's relative rank, listing comments, and listing score count only when
  the post itself carries the claim. Comment points count only for comments
  explicitly identified as evidence; an unrelated high-point joke or visual
  reaction cannot promote a buried claim. A declared evidence comment with at
  least 5 points is resonant. These thresholds prioritize audience response;
  they are not truth or prevalence claims.
- `critical_signal` requires all three: explicit decision relevance, resonance,
  and at least two independent evidence sources after author and
  near-duplicate deduplication. High-point comments lead presentation while
  lower-point independent corroboration may still sharpen the wedge.
- Explicitly off-question evidence is `excluded_not_decision_relevant`.
  Missing or failed content remains `access_or_processing_gap`; never score an
  access or processing failure as low value or useless.
- When direct HTTP returns a body classified as `block_shell`, the bounded batch
  writes a diagnostic PNG and JSON receipt from the exact preserved response
  bytes. The derivation performs no URL re-fetch, browser access, retry, CAPTCHA
  interaction, proxy use, or alternate access. It is a readable diagnostic
  rendering, not a claim of pixel-faithful browser appearance.
- Bare reCAPTCHA widget markup inside an otherwise visible Reddit login form is
  not a challenge-page signal. Visible human-verification language and the
  existing provider-specific block-shell signals continue to fail closed.

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

Admission gate per find (adds are effectively permanent — `--roster` captures
every tracked subreddit forever, and there is no paused capture state yet):

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

- Weekly digest / condensed judgment pack: later layer; trigger is the
  evidence layer running for real. Nothing analysis-shaped persists to the
  lake (candidates are pure functions of packets; recompute beats persist
  until cross-week recurrence work makes recomputation materially expensive).
- Columnar or compressed serialization: rejected on measurement (1.06x).
- Daily cadence: trigger-based escalation only (existing radar design
  language), driven by the same activity-anomaly trigger as re-observation.
- New-Reddit capture rungs: closed. www is bot-gated; the sanctioned path for
  commercial-grade needs is the licensing track per the lane README.
- Reddit Data API: dropped 2026-07-22 (approval-gated, no published timeline).
- Roster expansion beyond 100: the owner set the first target at 100
  (reached 2026-07-22, 38 -> 100 across two sweeps). Further growth uses
  section F unchanged; it is owner-paced and bounded, never a crawler.
- Roster pruning / a paused capture posture: no vocabulary value exists for
  "tracked but not captured", so a dropped subreddit today means living with
  its weekly request. Trigger to add one: the first prune pass that wants to
  keep a subreddit's history while stopping its capture.

## Verification bound to implementation

- Unit: observe verb vocabulary and fold behavior; listing mapping; retention
  rules (rotating sample selection, anomaly triggers); materializer surface
  stamping for both listings; projection fields (timestamp, stickied, flair)
  against a stored fixture page.
- Live dogfood in the implementing session: backfill the six observations via
  observe and read them back from the fold; run one real top_week roster pass;
  confirm ledger lines (observation + capture_state) for every roster
  subreddit; run the reader over the pass output and confirm the candidate
  list and floor tripwire emit.
- Flair caveat carried honestly: flair extraction returned zero on the
  30PlusSkinCare test page and is unverified against a page known to carry
  flairs; the fixture for the projection test must be a SkincareAddiction page
  (tagged posts confirmed present in its weekly listing).
