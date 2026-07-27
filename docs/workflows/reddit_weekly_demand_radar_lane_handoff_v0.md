# Reddit Weekly Demand Radar Lane — Cold Handoff Packet v0

```yaml
retrieval_header_version: 1
artifact_role: Cross-lane handoff packet (continuation state, not readiness evidence)
scope: >
  Cold-reader state transfer for the Reddit weekly demand radar lane as of
  2026-07-23: what is built and merged, what the live corpus contains, the
  capture blocker (Reddit automation detection), the open decision on how or
  whether to restore capture, and the guardrails a receiving lane must not
  violate.
use_when:
  - Resuming the Reddit weekly demand radar lane in a fresh lane, thread, or worktree.
  - Deciding how to respond to the 2026-07-22 Reddit capture block.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/reddit/README.md
  - docs/decisions/forseti_product_thesis_decision_adjudication_v0.md
stale_if:
  - Capture is restored or the lane is formally paused by an owner decision.
  - The open decision below is resolved (a route is selected).
  - A later weekly pass changes the corpus coverage numbers recorded here.
```

> **HISTORICAL / SUPERSEDED FOR CURRENT ROUTING (2026-07-28).** This packet
> preserves 2026-07-23 continuation state. Its pinned revisions, corpus counts,
> open capture decision, and operating assumptions are stale. Do not use it to
> select captured Reddit threads or infer current runner behavior. Start with
> `reddit_listing_efficiency_policy_v0.md` for deep-dive triage and the Reddit
> source-family `README.md` for the current lane route.

## Load Contract

- packet_version: v0
- mode: max
- created_at: 2026-07-23
- created_by_lane: `claude/reddit-graphing-lane-d07de4` (provenance only; not an authority claim)
- workspace: `C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\reddit-graphing-lane-d07de4`
- handoff_path: `docs/workflows/reddit_weekly_demand_radar_lane_handoff_v0.md`
- expected_branch: `claude/reddit-graphing-lane-d07de4`
- expected_head: `e8859a7c38f26f95fba85886607715215d81f2b7`
- expected_origin_main: `ace3b23ea1617abb519c5000ddf39fc52f739d0c`
- expected_dirty_state_before_handoff: clean (no modified, no untracked)
- expected_dirty_state_including_handoff_file: this file is **new and untracked** after writing; nothing else dirty
- load_rule: confirm-don't-trust. Re-verify every load-bearing fact against its
  compare target before acting. Sender claims are hypotheses, not authority.

## Goal Handoff

- long_term_goal: `not supplied` — no `workflow-goal-framing` output was produced
  in the sending thread. Do not invent one. Nearest owner-ratified anchor is the
  controlling product thesis (see Inherited Context); it is context, not a goal frame.
- anchor_goal: `not supplied`
- success_signal: `not supplied`

**Warning:** `success_signal`-based output-fit checking is unavailable. The
receiver cannot mechanically check whether its output fits an agreed goal; get a
goal frame from the owner before treating any output as fit-for-purpose.

## Open Decision / Fork

**Decision: how (or whether) to restore Reddit listing capture after the
2026-07-22 automation block.**

Options:

1. **Test headed Playwright** (untried). The capture spine's browser runner has
   `--headed`. Headless is detectably a stripped automation harness; running
   headed removes that difference rather than disguising it. One request settles it.
2. **Warm same-context capture** using the owner's real browser profile
   (`--browser-user-data-label`, plus `run_source_capture_browser_user_data_export.py`).
   The lane README reserves this path and its stated precondition ("only after
   exact old Reddit HTML is visible") is met. Puts the owner's browsing identity
   in the blast radius — owner's call, not the agent's.
3. **Sanctioned track**: Reddit Data API (approval-gated, no published timeline)
   or data licensing. The lane README's dual-track posture says commercial-grade
   product use lands here.
4. **Accept the 32-subreddit corpus** and stop capturing. Analysis work is not
   blocked, only its breadth.

Already constrained / off the table:

- Anti-detection tooling (CloakBrowser `stealth_args` / `humanize`, fingerprint
  spoofing, UA spoofing on a non-browser client) is **excluded**. It would very
  likely work, which is exactly why it was refused. See Drift Guard.
- Solving bot challenges or CAPTCHAs is excluded.
- Reddit Data API as a near-term unblock was dropped by the owner 2026-07-22
  (approval-gated, no timeline). It remains open as a longer-horizon track.

Trade-offs: option 1 is one request and settles the technical question. Option 2
is the only option likely to work soon but carries owner-identity exposure and an
*agreed* ToS (a User Agreement clicked through) rather than an advisory
robots.txt. Option 3 is slow but has no detection question. Option 4 costs
nothing and loses breadth.

Owner of the call: the repository owner. Options 2 and 3 are explicitly owner
decisions; the agent may run option 1 on request.

Recommendation: run option 1 first (single request, settles the question), then
route to option 3 if it fails. Do not slide up rungs until something works —
that converts a measured-risk posture into an unmeasured one.

## Drift Guard

- **Do not use anti-detection tooling against Reddit or Google.** CloakBrowser
  with `stealth_args`/`humanize`, fingerprint spoofing, or UA spoofing on a
  non-browser client. Violating this crosses from capture into evasion, contradicts
  a line held consistently across the sending thread, and would make the lane's
  source-policy receipts false.
  - The distinction that was used: a real browser *being* a browser is fine; a
    non-browser *pretending* to be one is not.
- **Do not solve bot challenges or CAPTCHAs.** When Google gated the SERP sweep,
  the agent stopped and the owner cleared it. Keep that split.
- **Do not ledger the 86 login-wall packets from the 2026-07-22 full-roster pass.**
  They contain Reddit login pages, not listings. They were deliberately NOT
  refreshed into the registry. Running
  `run_reddit_subreddit_registry_refresh.py` over them would write 86 junk
  observations that append-only storage cannot cleanly retract.
- **Do not hard-delete registry records for retired subreddits.** Each carries a
  migration baseline binding `legacy_baseline_sha256 3e51ba47…`; a partial
  baseline set is a fail-closed condition in `migrate_legacy_registry`, so
  deletion permanently breaks the migration/rollback path. Tombstoning packets is
  the sanctioned alternative if removal is genuinely wanted. Owner asked about
  deleting 6 of these; the recommendation given was "don't", and no deletion was performed.
- **Region rule (owner, 2026-07-22): US/general/product-category subreddits only.**
  Country-audience subreddits (India, PH, UK, AU, CA) are excluded. Korean and
  Asian beauty stay — they are product categories with large US demand, not
  geographic audiences.
- **Do not select a decision family from Reddit evidence alone.** Owner correction,
  2026-07-23: decision families are invoked when the full evidence picture is
  assembled, not derived from whichever evidence family happens to be built.
  The sender made this inversion once; do not repeat it.
- **Sub count is not a quality metric.** This is doctrine, quoted from the beauty
  product profile. Roster expansion beyond current size has sharply diminishing
  returns and does not improve Reddit's evidence class for market prevalence.
- **Reddit is one evidence family, not the product.** Owner's read: it serves
  decision family #2 (positioning/messaging/claims) and feeds AEO
  (answer-engine optimisation) strongly. It is weak evidence of market prevalence
  at any roster size.

## Inherited Context (does NOT flow to a new lane)

### Source-loading state to re-establish (follows overlay doctrine)

- overlay source-loading policy: `.agents/workflow-overlay/source-loading.md`
  (read `.agents/workflow-overlay/README.md` first — it routes to the owning section).
- targets to enter the ladder:
  - `forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md` (this lane's contract)
  - `forseti/product/spines/capture/core/source_families/social_media/reddit/README.md` (stage owners, dual-track access posture, hard stops)
  - `forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_subreddit_registry_spec_v0.md` (row shape and vocabularies)
- already loaded (weak orientation, freshness-marked 2026-07-23; **not** authority):
  the three files above, plus `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md`
  and `forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md`.
- must load first (before strict or actionable steps): the weekly demand radar
  spec and the Reddit lane README. The README owns the access posture that the
  open decision turns on.
- load rule: the receiver re-runs progressive source loading per the overlay.
  This packet's loaded-set only seeds the ladder; it does not satisfy it.

### Earlier-decided concepts and behaviors (inline gist plus verify pointer)

- **Controlling product thesis**: Forseti is a decision-adjudication product;
  beauty is the first application; the product form is a bounded Decision Sprint
  around one decision and its deadline. "The buyer does not buy source volume…
  the buyer buys a better-defended action."
  - decided in: `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md`
  - compare target: status line reads `OWNER_LOCKED_PRODUCT_DIRECTION`, adopted 2026-07-14
  - verify before: any claim about what this lane is for
- **Beauty application profile**: eight admitted decision families; first family
  explicitly unselected; "Source count is not a quality metric."
  - decided in: `forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md`
  - compare target: status line reads `FIRST_APPLICATION_BOUND_DECISION_FAMILY_UNSELECTED`
  - verify before: any decision-family selection or roster-sizing argument
- **Dual-track access posture**: bounded public capture under measured-risk ToS
  posture AND a sanctioned commercial/licensing path in parallel;
  commercial-grade product use lands on the sanctioned path.
  - decided in: Reddit lane README, "Radar Cadence and Access Posture"
  - compare target: phrase "commercial-grade product use lands on the sanctioned path"
  - verify before: choosing among the open-decision options
- **Measured-ToS-risk posture**: owner accepted ToS risk "just not at an absurd
  level (e.g. Brightdata)".
  - decided in: `docs/decisions/forseti_consumer_demand_ratification_decision_memo_v0.md` (Owner Decision Record)
  - compare target: quoted owner words in that memo
  - verify before: any posture escalation
- **SERP sweep pacing contract**: Google bot-gates on request *velocity*, not
  volume — 30 rapid navigations tripped it; 13 paced at 4–6s did not.
  Single-anchor `r/<X> reddit` queries; one query already returns 5–8 communities.
  - decided in: weekly demand radar spec, section F
  - compare target: git blob `c28e25117e16b388e4fd642463f9cc327edfa18d`
  - verify before: any further roster discovery sweep

## Active Objective

Restore or formally close Reddit listing capture for the 86-subreddit roster,
after the 2026-07-22 full-roster pass was blocked by Reddit automation detection.
The built pipeline, the 32-subreddit corpus, and all analysis tooling are intact
and merged; only capture is blocked.

## Exact Next Authorized Action

1. **Open a pull request for the two unmerged commits on this branch.** They are
   pushed to `origin/claude/reddit-graphing-lane-d07de4` with **no open PR**:
   - `823abdc6` retired roster state + SERP pacing contract
   - `e8859a7c` raw-sample projection validation guard
   Both carry `review_routing_status` lines in their commit messages.
2. **Then**, on owner instruction only, resolve the Open Decision above. If option 1
   (headed Playwright) is chosen, the exact test is a single request:
   `run_source_capture_browser_packet.py --headed --url
   'https://old.reddit.com/r/30plusskincare/top/?sort=top&t=week&limit=100'`
   and inspect the resulting packet's `04_browser_snapshot_metadata.json` for
   `access_blocked` and `final_url`.
3. **Stop condition:** if the headed test is also blocked, do not try further
   transports. Report that the automated path is closed and route to the
   sanctioned track (option 3).

## Authority And Source Ledger

- Repository instructions: `AGENTS.md` (root), imported by `CLAUDE.md`.
- Overlay authority: `.agents/workflow-overlay/README.md` and the sections it names.
- User constraints (all from the sending thread, 2026-07-22/23):
  - US/general/product-category subreddits only; Korean/Asian beauty allowed.
  - Roster target was 100; after the prune the capture roster is 86.
  - `fragrances` kept in the roster at owner request (it was on the original cut list).
  - Reddit serves decision family #2 and feeds AEO.
  - Decision families require the full evidence picture first.
  - Owner solves bot challenges; the agent pings and stops.

Source-read ledger:

- `forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md`
  - Role: this lane's controlling contract (capture params, retention, pacing, dive gate)
  - Load-bearing: yes
  - Compare target: git blob `c28e25117e16b388e4fd642463f9cc327edfa18d`
  - Last checked: 2026-07-23
  - Reuse rule: reread before changing any capture parameter
- `forseti-harness/data_lake/reddit_subreddit_registry.py`
  - Role: registry authority — fold, `capture_roster`, `retired` state, writers
  - Load-bearing: yes
  - Compare target: git blob `1f7c162427f5163436aa2f6ba04f6f383fc13c96`
  - Last checked: 2026-07-23
  - Reuse rule: reread before any registry write
- `forseti-harness/runners/run_reddit_grid_capture.py`
  - Role: capture runner (`--roster`, `--listing`, `--limit`, retention rules)
  - Load-bearing: yes
  - Compare target: git blob `2eaa7ffca183aab4dcff2881c518aaddddc4b38c`
  - Last checked: 2026-07-23
  - Reuse rule: reread before re-running any pass
- `forseti-harness/runners/run_reddit_weekly_demand_read.py`
  - Role: reader — candidate gate, tripwire, coverage report
  - Load-bearing: yes
  - Compare target: git blob `0d3b6221f48f7b6d1458f1190036c138d71b6024`
  - Last checked: 2026-07-23
  - Reuse rule: reread before interpreting reader output
- `forseti-harness/source_capture/content_extraction.py`
  - Role: `ContentExtractionSpec`, including `validate_in_raw_mode`
  - Load-bearing: yes
  - Compare target: git blob `3464b8a655a86837425d0c5eebbfe3016af287be`
  - Last checked: 2026-07-23
  - Reuse rule: reread before changing retention behavior
- `forseti/product/spines/capture/core/source_families/social_media/reddit/README.md`
  - Role: stage owners, dual-track access posture, hard stops
  - Load-bearing: yes
  - Compare target: `reread-required` (no hash captured)
  - Last checked: 2026-07-22
  - Reuse rule: reread before choosing among the open-decision options
- Lake state (`F:\forseti-data-lake`)
  - Role: live corpus and registry
  - Load-bearing: yes
  - Compare target: re-derive by running `capture_roster` / `known_subreddits`;
    expected census 106, capture roster 86, retired 20, 32 with top/week packets
  - Last checked: 2026-07-23
  - Reuse rule: re-derive; do not trust the numbers in this packet

Source gaps:

- No goal frame exists for this lane (see Goal Handoff).
- The Reddit lane README was read but no content hash was captured; treat as `reread-required`.
- Whether the Reddit block is durable or transient is **unknown**; only three
  transports were tested (see Blockers).

Strict-only blockers: none beyond the capture blocker below.

Not-proven boundaries:

- The dissent-elicitation pattern (13 threads, 3,821 comments) is **not** proven
  corpus-wide. It was measured on 32 of 86 subreddits and those 32 are
  fragrance-heavy, which is where the pattern lives. Do not restate it as a
  corpus-wide finding.
- No claim is made that any capture route will work; the headed test is untried.

## Current Task State

Completed:

- Weekly demand radar evidence layer built, dogfooded, delegated-reviewed,
  adjudicated, and merged (PR #1300, merged 2026-07-22T17:31:46Z; PR #1299 merged earlier).
- `observe` verb (agent-read reach observations), grid projection v3
  (timestamp / stickied / flair / venue created_utc + listing diagnostics),
  grid runner `--roster`/`--limit`/retention rules, materializer top-week surface
  stamping, committed weekly reader.
- Roster built to 106 census / 86 capture roster across three SERP sweeps, then
  20 retired via the new `retired` discovery state.
- One problem brief produced from 5 deep-dived threads (705 comment bodies).
- First-touch pain census over 601 candidates from the 32-subreddit corpus.

Partially completed:

- Corpus coverage: **32 of 86** subreddits have a `top/week` packet; **54 have none**.
  The 54 include every subreddit added on 2026-07-22 (all nails, hair-colour,
  brows/lashes, deep-skin, sunscreen, most makeup).

Broken or uncertain:

- Capture is blocked (see Blockers).
- Two commits are pushed with no open PR.

## Workspace State

- Branch: `claude/reddit-graphing-lane-d07de4`
- Head: `e8859a7c38f26f95fba85886607715215d81f2b7`
- origin/main: `ace3b23ea1617abb519c5000ddf39fc52f739d0c`
- Dirty or untracked before handoff: clean
- Dirty or untracked after writing this file: this handoff file is **new and untracked**
- Unmerged commits on branch (pushed, no PR): `823abdc6`, `e8859a7c`
- Data lake root: `F:\forseti-data-lake` (external drive; must be mounted)

## Changed / Inspected / Tested Files

- `forseti-harness/data_lake/reddit_subreddit_registry.py`
  - Status: merged + modified after merge (in `823abdc6`)
  - Role: registry authority
  - Important observations: `DISCOVERY_STATES` now includes `retired`;
    `capture_roster()` is the retired-excluding read; `known_subreddits()` stays
    the exhaustive census used by fold/parity/history.
- `forseti-harness/runners/run_reddit_grid_capture.py`
  - Status: merged + modified after merge (`823abdc6`, `e8859a7c`)
  - Role: capture runner
  - Important observations: uses `capture_roster` for `--roster`;
    `check_grid_projection_anomaly` raises so a bad projection falls back to raw;
    rotating raw sample selected by absolute Monday-ordinal week index.
- `forseti-harness/runners/run_reddit_weekly_demand_read.py`
  - Status: merged + modified after merge (`823abdc6`)
  - Role: reader
  - Important observations: uses `capture_roster`; disposition classes that grow
    with the packet corpus report count+sample, not exhaustive IDs.
- `forseti-harness/source_capture/content_extraction.py`
  - Status: modified after merge (`e8859a7c`)
  - Role: retention contract
  - Important observations: `validate_in_raw_mode` (default `False`) makes
    raw-retention captures still run the extractor as a shape check.
- `forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md`
  - Status: merged + modified after merge (`823abdc6`)
  - Role: lane contract
  - Important observations: section F carries the SERP sweep pacing contract.

## Frozen Decisions

- **`retired` discovery state added**, with `capture_roster()` as the narrower read.
  - Evidence: `823abdc6`; registry spec Vocabularies section documents the semantics.
  - Consequence: retirement is reversible and non-destructive; history is preserved.
- **Weekly capture shape: `top/?sort=top&t=week&limit=100`, single page.**
  - Evidence: page 2 measured — 100 posts, top score 3, 2 posts ≥15 comments; page-1
    floor was 2–3. Recorded in the spec's empirical basis table.
  - Consequence: no pagination; the reader's floor tripwire escalates if a
    subreddit's page-1 floor exceeds 50.
- **Reddit Data API dropped as a near-term route** (owner, 2026-07-22): approval-gated,
  no published timeline, self-service registration replaced by "contact us".
- **Region rule: US/general/product-category only** (owner, 2026-07-22).
- **20 subreddits retired** (non-US country-audience, professional/career,
  style-not-product, redundant, too-small). `fragrances` kept at owner request.

## Mutable Questions

- Is the Reddit block durable or transient?
  - Why still mutable: only three transports tested, all within ~40 minutes of the
    triggering pass. No test has been run on a different day.
  - What would resolve it: the headed Playwright test, and/or a single probe on a later day.
- Is dissent-elicitation a cross-category pattern or a fragrance ritual?
  - Why still mutable: measured on 32 of 86 subreddits, and those 32 are fragrance-heavy.
  - What would resolve it: a full-roster pass, which is blocked.
- Which decision family should this lane eventually serve?
  - Why still mutable: owner ruled that decision families require the full evidence
    picture; Reddit alone cannot select one.
  - What would resolve it: assembling additional evidence families.

## Superseded / Dangerous-To-Reuse Context

- **"Wait for the rate-limit cooldown."**
  - Why stale: the block is automation detection, not an IP rate limit. A real
    browser on the same machine and IP reached the content at the same time.
  - Replacement: the Open Decision above.
- **"It's a client-signature gate — browsers work, non-browsers don't."**
  - Why stale: refuted. Headless Playwright Chromium (a real browser) was blocked
    *harder* than urllib — `access_blocked: True`, "You've been blocked by network security."
  - Replacement: it is automation detection; headed-vs-headless is the untested variable.
- **"There is no non-evasive automated path."**
  - Why stale: too broad. Headed Playwright is untested and is not evasion.
  - Replacement: option 1 in the Open Decision.
- **Dissent-elicitation presented as a corpus-wide finding.**
  - Why dangerous: it was measured on 37% of the roster, fragrance-skewed.
  - Replacement: treat as a fragrance-subreddit observation pending full coverage.
- **The 86 packets from the 2026-07-22 full-roster pass.**
  - Why dangerous: they are Reddit login pages, not listings. They sit in the lake
    raw-preserved but were never ledgered.
  - Replacement: none — do not ledger them; re-capture when capture works.
- **Browser pane (`mcp__Claude_Browser__*`) as a Reddit capture route.**
  - Why dangerous: blocked by harness policy for both `navigate` and page reads on
    reddit.com. This is a harness restriction, unrelated to Reddit's own blocking;
    do not confuse the two when diagnosing.
  - Replacement: the capture spine's own Playwright runner, which is not harness-blocked.

## Commands And Verification Evidence

- Full-roster capture pass (the failure):
  ```bash
  python forseti-harness/runners/run_reddit_grid_capture.py --roster \
    --data-root 'F:\forseti-data-lake' --listing top --time-window week --limit 100
  ```
  Result:
  - Failed: 86 subreddits, 1 "success" (the raw sample, which also captured a login page), 85 extraction failures.
  - Important output: every response redirected to
    `https://old.reddit.com/login/?reason=lor2&dest=...`, title `Welcome to Reddit`.
  - Re-run target: inspect packet `01KY5PH3VA8816SCKKAX31HMCD` metadata `final_url`.
- Single direct-HTTP probe after the pass: same `lor2` login redirect
  (packet `01KY5QAW4QF4WV0GSM6V5K7R90`).
- Single headless browser probe: `access_blocked: True`, visible text
  "You've been blocked by network security" (packet `01KY5QH8R7Y9XH0G0C1HTF7D7S`).
- Test suites (passing at head `e8859a7c`):
  ```bash
  python -m pytest forseti-harness/tests/unit -q -k reddit
  python -m pytest forseti-harness/tests/contract -q -k "seam or inventory or capture"
  ```
  Result: passed. Re-run target: re-run both before any strict claim about the build.

## Blockers And Risks

- **Blocker: Reddit automation detection blocks listing capture.**
  - Evidence: three transports, all blocked, all on 2026-07-22 within ~40 minutes:
    urllib → `lor2` login wall; headless Playwright → "blocked by network security";
    (separately, the browser pane is blocked by harness policy, which is not Reddit).
    The same content was reachable in a real browser on the same machine.
  - Likely next action: the headed Playwright test (Open Decision option 1).
- **Risk: escalating transports until one works.** Each additional transport tried
  moves closer to anti-detection tooling. The stop condition in Exact Next
  Authorized Action step 3 exists to prevent this.
- **Risk: two commits with no PR.** They are pushed but unreviewed and unmerged;
  they will drift from main.
- **Risk: the data lake is on `F:\`**, a removable drive. `DataLakeRoot.resolve`
  fails closed if it is not mounted.

## Confirm-Don't-Trust Load Checklist

Load-bearing facts the receiver must re-verify before acting, and how:

- Branch / head / dirty state → `git status --short --untracked-files=all`,
  `git rev-parse HEAD`; expect head `e8859a7c…` and this handoff file untracked.
- Two unmerged commits with no open PR → `git log --oneline origin/main..HEAD`
  and `gh pr list --head claude/reddit-graphing-lane-d07de4`.
- Corpus coverage (census 106 / roster 86 / 32 with top-week packets) → re-derive
  via `known_subreddits` and `capture_roster` against `F:\forseti-data-lake`.
- The five source files → compare git blob hashes recorded in the ledger.
- Capture blocker still in force → **only** by running the single headed test, and
  only if the owner authorizes it. Do not re-probe blocked transports to confirm.
- Test suites → re-run rather than trust.

Load outcomes:

- `REUSE`: all of the above verified; continue from Exact Next Authorized Action.
- `PARTIAL_REUSE`: only non-load-bearing facts drifted.
- `STALE_REREAD_REQUIRED`: head, dirty state, corpus numbers, or file hashes
  drifted but can be re-derived safely.
- `BLOCKED_DRIFT`: drift conflicts with the Drift Guard or owner constraints.
- `BLOCKED_MISSING_PACKET`: this file absent or unreadable.
- `BLOCKED_UNVERIFIABLE`: a load-bearing claim cannot be re-derived — most likely
  the lake numbers if `F:\` is not mounted. Report the precise source-loading
  blocker rather than proceeding.

Sources that must be reread if drift is detected: the weekly demand radar spec and
the Reddit lane README.

## Do Not Forget

- The owner solves bot challenges; the agent stops and pings. This split was used
  successfully when Google gated the SERP sweep and must be preserved.
- The 86 login-wall packets are in the lake but deliberately unledgered. Leaving
  them unledgered is a decision, not an oversight.
