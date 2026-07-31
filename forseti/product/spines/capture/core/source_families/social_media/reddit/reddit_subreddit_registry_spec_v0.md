# Reddit Subreddit Registry Spec v0

```yaml
retrieval_header_version: 1
artifact_role: source_capture_family_registry_index
scope: >
  Small subreddit registry contract: canonical venue identity, dedupe, routing
  state, update-on-change descriptive facts, and append-only dated size
  observations for Reddit subreddits Forseti tracks. Defines what discovery,
  graph-frontier, capture, and radar work may check before opening duplicate
  exploration and where dated subscriber/activity observations accumulate.
  Not metric authority, not demand proof, not a monitor, not capture
  authorization, and not venue quality/fit scoring.
use_when:
  - Checking whether a discovered subreddit is already known before spending a discovery or graph-frontier hop.
  - Recording or reading dated subscriber/active-user observations for a tracked subreddit.
  - Filtering tracked venues by niche path or venue role for radar or GTM routing.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_v0.json
  - forseti/product/spines/capture/core/source_families/social_media/reddit/README.md
  - forseti/product/spines/scanning/source_families/reddit/reddit_beauty_fragrance_subreddit_inventory_v0.md
  - forseti/product/spines/scanning/source_families/reddit/data_capture_spine_reddit_graph_frontier_lane_architecture_v0.md
stale_if:
  - The registry JSON adopts a different schema_version or moves to a generated/lake-native projection.
  - The Reddit Graph Frontier or Candidate URL Intake contracts change the observation fields this registry mirrors.
  - The subreddit inventory or lead-lane scope changes the niche-path or venue-role vocabulary in a way rows must follow.
```

## Status

`SMALL_VENUE_REGISTRY_CONTRACT_V0`. Modeled on the Creator Registry index
contract, minus the identity machinery Reddit does not need: a subreddit's
canonical name is globally unique and stable, so there is no handle-linkage
ledger, no normalization layer, and no cross-platform identity state.

The registry answers one question before work opens, plus one accumulation
job:

```text
Have we already got this subreddit down — and what do we currently know
about it (liveness, bio, posture, niche, size history, prior runs)?
```

It does not answer whether a venue is high-quality, high-fit, or demand-rich.
Venue-value judgment stays with CSB-first scans and their broad-scout
miss-check; the registry supplies raw material only.

## Stable Key

`subreddit`: the canonical lowercase subreddit name without the `r/` prefix
(e.g. `fragranceclones`). It is the row key and the dedupe key. `url` is the
derived canonical public URL.

## Row Shape

Each `subreddits[]` row carries:

- Identity and liveness: `subreddit`, `url`, `status`
  (`active` | `unverified` | `private` | `banned` | `quarantined`),
  `status_observed_at`, `created_utc_or_none`.
- Descriptive (update-on-change): `title_or_none`,
  `public_description_or_none`, `posting_posture_or_none`,
  `descriptive_observed_at`, `descriptive_changes[]`.
- Routing: `niche_paths[]`, `venue_roles[]`, `discovery_state`
  (`known_subreddit` | `candidate_new_subreddit` | `retired`), `capture_state`
  (`no_packet_recorded` | `grid_packets_recorded` |
  `thread_packets_recorded`; grid never downgrades thread).
- Time series (append-only): `observations[]`, each
  `{ observed_at, subscriber_count_or_none, active_user_count_or_none,
  source_surface, provenance_pointer, absent_reason_or_none }`, plus
  `weekly_visitor_count_or_none` and `weekly_contribution_count_or_none` on the
  surfaces that state weekly reach. Those two keys are nullable additions with
  no migration: a surface that does not state weekly reach omits them, and an
  omitted key equals an explicit null.
- Provenance: `first_seen_at`, `register_pointers[]`, `source_pointers[]`.

File-level `registry_non_claims` apply to every row; rows do not repeat them.

### Known bad values: www subscriber counts at parser `www-2`

`www.reddit.com` states WEEKLY REACH and never states subscribers. Parser
`www-2` read the sidebar's two abutting numbers positionally and wrote them into
`subscriber_count_or_none`. Three observations carry that error and cannot be
corrected in place, because the lake is append-only and observations dedupe by
provenance pointer, so a corrected record for the same pointer fails closed:

| subreddit | observed_at | `subscriber_count_or_none` (actually weekly visitors) |
|---|---|---|
| `30plusskincare` | 2026-07-31 | `701K` |
| `fragrance` | 2026-07-31 | `476K` |
| `newinbeauty` | 2026-07-31 | `34K` |

A reader treating `subscriber_count_or_none` as a subscriber count on a
`www_reddit_*` surface is off by roughly 3.5x, which matters most for the
deferred breakout rule that uses the series as its normalizer. Two things limit
the exposure: those subreddits also carry correct `www-4`+ observations on the
same date, so the contradiction is visible rather than silent; and from `www-3`
onward the www projection reports subscriber counts as absent with the reason
`www_venue_envelope_exposes_weekly_reach_not_subscriber_counts`. The subscriber
series continues to depend on the `about.json` surface, not on www.

## Update Semantics (the two-speed rule)

- **Descriptive fields are update-on-change.** A check that re-confirms the
  current value refreshes `descriptive_observed_at` only — no append. A check
  that finds a different value updates the field and appends one
  `descriptive_changes[]` record: `{ field, changed_at, previous_value }`.
  `status` follows the same rule via `status_observed_at`.
- **Observations are append-per-event.** Every run or check that sees a
  subscriber/active-user reading (or a meaningful absence) appends one
  observation record. Growth and breakout velocity are derived on read from
  the series; the registry never stores a computed growth or trend claim.

Observation field names deliberately mirror the Graph Frontier node fields
(`visible_subscriber_count_or_none`, `visible_active_user_count_or_none`,
`visible_volume_signal_absent_reason_or_none`) so frontier runs feed the
registry without translation. Counts are strings to carry honest precision
(`approx_270000`); a null count with `absent_reason_or_none` set is a valid
observation.

## Vocabularies

- `niche_paths`: hierarchical slash paths, multi-valued —
  `beauty`, `beauty/fragrance`, `beauty/skincare`, `beauty/makeup`,
  `beauty/hair`, `beauty/nails`. One registry file spans all niches; per-niche
  views are prefix filters on read. Shard into per-vertical files only if
  scale ever demands it, keeping this logical row shape.
- `venue_roles`: functional dimension, orthogonal to niche, multi-valued —
  `hub`, `dupe_value`, `exchange`, `retailer`, `deal`, `creator_watch`,
  `counterevidence`, `regional`, `demographic`, `specialist`.
- Both vocabularies are extended by adding a value here first, then using it
  in rows.
- `discovery_state`: `known_subreddit` (confirmed tracked),
  `candidate_new_subreddit` (discovered, not yet confirmed by packet
  evidence), `retired` (deliberately no longer captured).

  `retired` is a **roster decision, not a judgement and not a Reddit-side
  status** — a banned, private, or quarantined venue is `status`, which is
  observed, whereas `retired` is chosen. The lake is append-only, so a retired
  subreddit keeps its full history and folds normally; it is excluded only
  from the capture roster, so it stops costing one request per pass.
  Reversing it is an ordinary roster change back to a tracked state.

  Readers must pick deliberately: `known_subreddits()` is the exhaustive
  anchor census (fold, parity, history), `capture_roster()` is the
  retired-excluding list a capture pass or coverage report should use.

## Feed Contract

Writers are radar grid passes (cadenced per
`reddit_radar_grid_capture_maintenance_design_v0.md`), other bounded runs,
and operator refreshes; once grid capture exists, registry state is
materialized read-only from committed Bronze packets rather than
hand-edited by capture runners:

- Grid evidence flows through the one authorized materializer,
  `forseti-harness/runners/run_reddit_subreddit_registry_refresh.py`: it
  hash-verifies committed `reddit_subreddit_grid` packets, appends one
  observation per packet (deduped by provenance pointer, so re-runs are
  no-ops), confirms liveness, and upgrades `capture_state` — capture runners
  themselves never flip registry state. It reports unknown subreddits and
  never silently adds rows. It deliberately does not touch
  `public_description_or_none` (grid sidebar text and `about.json`
  descriptions are different surfaces; cross-surface diffs would append
  spurious change records).
- Other bounded runs and operator refreshes apply the same two-speed rule by
  hand where no materializer path exists yet.
- Graph-frontier and discovery work check `subreddit` presence first and
  route repeat sightings as refreshes, not duplicate rows or duplicate work
  queues.

## Boundaries

- May be source of truth for: which subreddits Forseti knows, their canonical
  identity, observed liveness/descriptive facts with dates, niche/role
  routing tags, and the dated observation series.
- Is not: metric authority, demand or resonance proof, venue quality or fit
  scoring (forbidden in the frontier lane), capture/monitoring/engagement
  authorization, a crawl queue, or a substitute for CSB venue evaluation and
  the broad-scout miss-check.
- Observation counts are source-visible readings with provenance; conflicting
  or inflated web claims are recorded as null counts with an absent reason,
  never silently averaged.
