# YouTube Creator Onboarding Lane — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded implementation commission: give the Creator Registry a YouTube
  admission path — assessment capture, qualification evidence, and
  registry admission — modeled on the TikTok onboarding lane's mechanism,
  so the SERP lane's YouTube-recurring creators stop being a typed gap.
use_when:
  - The owner routes the YouTube creator-lane build (this handoff IS that
    routing; accepted execution is the bounded authorization).
stale_if:
  - The TikTok onboarding lane's admission flow or the Creator Registry
    schema changes materially before this executes.
  - serp_recurring_creator_feed_v0.json is superseded by a newer feed.
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    forseti-harness (capture_spine/, data_lake/creator_registry.py,
    runners/) for code; docs/research/serp_lane_competitor_scout_20260728/
    for the pilot verdict note; operator staging under C:\tmp for pilot
    capture output.
  input_prompt_source: docs/prompts/handoffs/youtube_creator_onboarding_lane_execution_handoff_v0.md
  edit_permission: code-write (registry + capture spine + runners), docs-write
  runtime_authorization: >
    This accepted handoff is the bounded runtime authorization (AGENTS.md):
    YouTube PUBLIC-surface captures for the named pilot creators only
    (profile/about, uploads grid, Shorts grid, selected video pages,
    captions). No engagement actions ever (no subscribe, like, comment,
    or watch-history manipulation), no CAPTCHA interaction, no other
    capture surface.
  targets: creator registry admission path, YouTube assessment runner,
    pilot captures. No overlay, spine-contract, or unrelated edits.
  reviews: code-root changes route per validation-gates; findings-first
    on the pilot verdict.
```

**Goal:** the Creator Registry can admit a YouTube creator through the
same candidate → judgment → account flow TikTok uses, and the SERP
lane's YouTube-recurring creators (73 in the feed; 301 more surfaced by
the suffix doors) have a funnel instead of a typed gap.
**Done looks like:** an assessment capture exists for each pilot
creator; at least one YouTube creator is registry-admitted end to end;
the feed's YouTube rows are consumable as frontier candidates; the gap
lines in `serp_lane_v0.md` (F19 routing note) and
`serp_recurring_creator_feed_v0.json` (`consumers.youtube`) are updated
in the same work unit.

## Required reads (pointer-first)

1. `forseti-harness/runners/run_source_capture_tiktok_creator_onboarding.py`
   — THE worked example. Read for its mechanism, not its letter: registry
   match preflight before any browser work; supervised one-creator
   one-browser-context; explicit creator intents (`new_onboarding` /
   `new_capture` assessment-only / `update_existing`); frozen grid window
   with a minimum acquisition bar; market gate; humanized input preset;
   receipts for everything; fail-closed session alias that never silently
   downgrades.
2. `forseti-harness/data_lake/creator_registry.py` — the admission flow to
   mirror: `deterministic_platform_account_id` (already platform-generic),
   `admit_tiktok_creator_candidate` → judgment snapshot →
   `admit_tiktok_creator_account`. The registry schema is platform-shaped
   already; DO NOT fork it — add YouTube admission functions of the same
   shape (or generalize the existing ones, whichever is the smaller
   complete change against current callers).
3. `forseti-harness/capture_spine/tiktok_creator_discovery_frontier/models.py`
   — frontier node/receipt shapes, for what a non-TikTok analog must and
   must not claim.
4. `docs/research/serp_lane_competitor_scout_20260728/serp_recurring_creator_feed_v0.json`
   — the candidate input: 73 YouTube creators with subjects and scope
   (`youtube:Dr Dray` spans 11 subjects), plus
   `analysis/fullbank_suffix_quality.json` on the operator drive for the
   301 suffix-door discoveries.
5. `forseti-harness/runners/run_asr_transcript_catchup.py` and
   `runners/_youtube_cli.py`, `run_youtube_creator_metric_rollup_producer.py`
   — existing YouTube-side machinery; extend, don't duplicate.

## Method (deltas from the TikTok example — the reads own the mechanics)

1. **Identity.** A YouTube creator is (handle `@name`, channel_id); the
   channel_id is the native id for
   `deterministic_platform_account_id("youtube", ...)`. Handles rename;
   channel_ids don't. The SERP feed carries display names only — the
   assessment capture resolves display name → handle/channel_id and
   records the resolution as evidence (mismatch = flag, not guess).
2. **Session posture — decide explicitly, once.** The TikTok lane is
   logged-in fail-closed because TikTok's surfaces demand it. YouTube's
   profile/uploads/Shorts/captions surfaces are publicly reachable, so
   logged-out is the expected posture (smaller account risk, no
   personalization bleed). Whichever posture is chosen: name it in the
   runner's contract and fail closed on its absence — never silently
   downgrade or upgrade, mirroring the TikTok alias behavior.
3. **The Shorts/long-form split is a typed axis, not a nuisance.**
   YouTube carries two content economies with incomparable engagement
   semantics (Shorts views inflate ~an order of magnitude vs long-form).
   Requirements: the assessment grid captures BOTH the uploads tab and
   the Shorts tab; every captured video row carries `format:
   short|long`; per-format counts and per-format engagement live in the
   grid window receipt; NO metric that averages across formats without
   both per-format inputs surviving beside it. The SERP-lane evidence
   for why both matter: F22 (YouTube = the evaluative/explainer layer —
   that is long-form) while Shorts is where YouTube competes with the
   TikTok-style substitution layer.
4. **Assessment before admission, same as TikTok.** Build the
   `new_capture` analog first: profile metrics + dual grids, no registry
   write. That alone unblocks CI qualification (engagement reality,
   caption/description competitor mining). Admission (`new_onboarding`
   analog with judgment snapshot) lands second, and only after the
   pilot's assessment output has been owner-reviewed.
5. **Transcripts: captions first, ASR fallback.** YouTube carries native
   captions for most target content; fetch those in assessment-mode deep
   capture where cheap, and route caption-absent videos to the existing
   ASR catch-up pattern. Transcript triggers follow the owner's standing
   rule: selective disambiguation of high-engagement ambiguous titles —
   never blanket, never sponsorship-hunting.
6. **Pilot.** 3–5 creators from the feed's YouTube top (Dr Dray 11
   subjects, Doctorly 8, SkinZone 7, Dr. Daniel Sugai 7) — assessment
   mode only, then the owner reviews before any admission. Report the
   same CI axes the TikTok dogfood proved: engagement separation,
   description/caption competitor yield, plus the Shorts/long split per
   creator.

## Boundaries (hard)

- Public surfaces only; no engagement actions; no CAPTCHA; respect any
  block/interstitial as a stop signal on that stream.
- One browser context per creator, supervised cadence like the TikTok
  lane; no parallel creator captures.
- Registry writes only through the admission flow with receipts; no
  direct index edits. Frontier dispositions remain owner acts.
- Standing non-claims travel on every artifact: observed counts only;
  recurrence evidences reach, not independence or sponsorship.

## Return contract (schema-bound; one line per field; `unknown` if absent)

- `admission_path`: functions added/generalized, with the registry
  test evidence.
- `assessment_runner`: path + the contract it enforces (posture, grids,
  format axis, receipts).
- `pilot`: per creator — channel_id resolved, follower/sub count,
  per-format video counts and median engagement, competitor names
  yielded, transcript count (and trigger used).
- `admitted`: creator(s) admitted end to end, or `none` with the blocker.
- `feed_wiring`: how the 73 + 301 become frontier candidates.
- `docs_reconciled`: the F19 routing line and feed `consumers.youtube`
  updates (same work unit, per completeness-at-the-consumer).
- `blocks`: any stop signals hit, or `0`.
- `artifacts`: paths written.
