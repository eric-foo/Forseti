# Source Capture Agent Runbook

This runbook is for agents operating the Source Capture Armory from
`forseti-harness/`. It tells an agent how to run the existing packet writers and
how to report what happened without deciding source meaning.

Use this when an agent is given concrete capture inputs. Do not use it for
source discovery, evidence selection, credibility judgment, Cleaning, ECR field
design, or autonomous crawling.

## Agent Boundary

The agent may:

- run the local-file packet runner against already-local source files;
- run Direct HTTP against one explicitly supplied ordinary HTTP URL;
- run Media / Asset capture against explicitly supplied asset URLs;
- run Archive.org capture against one explicitly supplied original URL;
- run Browser Snapshot capture against one explicitly supplied URL that needs
  anonymous browser rendering or screenshot preservation;
- run CloakBrowser Snapshot capture against one explicitly supplied URL that
  needs anonymous anti-blocking browser rendering without stored session,
  profile, proxy, or credential injection;
- bootstrap a permitted browser session manually into ignored local Playwright
  storage-state JSON;
- run Authenticated Browser Snapshot capture against one explicitly supplied URL
  using a previously bootstrapped storage-state label and an allowed session
  mode;
- run the TikTok one-creator live probe against explicitly supplied public
  creator/video URLs using the TikTok playbook posture, then optionally chain
  its sanitized staging output through the existing TikTok batch admission gate;
- run the Creator Registry match preflight runner against candidate social
  creator/account identities before starting new social creator/account
  capture;
- inspect `manifest.json`, `receipt.md`, and `raw/`;
- report packet path, exit code, preserved files, warnings, and limitations.

When the source exposes engagement/resonance facts such as visible rank/order,
comments, likes, views, shares, helpful votes, source-native scores, or official
response markers, the agent may preserve and report them as source-visible facts
only.

The agent must not:

- decide whether evidence is true, important, credible, duplicative, or useful;
- infer source meaning beyond reporting preserved source-visible text or files;
- choose targets through broad search or crawling;
- discover hidden media, parse galleries, recurse through pages, or run OCR;
- use methods that do not have an implemented runner in this runbook, including
  password-driven login automation, direct browser profile/cookie import, broad
  crawler/spider frameworks, proxy behavior, standalone CAPTCHA-solving
  services, or commercial fetch services;
- use no-entitlement login bypass, credential misuse, undisclosed session/cookie
  use, or any method Orca would refuse to disclose internally;
- claim validation, readiness, ECR receipt, Cleaning output, Judgment output,
  buyer proof, demand proof, credibility, independence, Action Ceiling, source
  quality, commercial readiness, or that engagement/resonance changed the
  authorized route.

If the requested capture needs ordinary anonymous browser-rendered content,
JavaScript rendering, or screenshot preservation for one supplied URL, use the
Honest Browser Snapshot runner. If an ordinary browser may pass after visible
launch, a local Chromium channel, or a bounded post-navigation settle delay, use
the Browser Snapshot controls first (`--headed`, `--browser-channel`,
`--settle-seconds`). If those controls are expected to fail or have failed
because the source blocks ordinary browser capture, use the CloakBrowser
Snapshot runner for one supplied URL. If it requires
login-visible or entitled content, use Authenticated Browser Snapshot only when
the operator has supplied an allowed session mode and a previously bootstrapped
local storage-state label. If the operator asks for password automation, direct
profile/cookie import, credentials in flags or environment variables,
no-entitlement bypass, proxy behavior, or CAPTCHA solving through these existing
runners, stop with `visible_capture_limitation`.

For all browser routes, diagnose rendered access from visible text and title
before treating full-DOM challenge markers as decisive. Hidden or residual
Cloudflare/Akamai/Kasada/DataDome/PerimeterX script/template text can remain in
the DOM after source content is visible; record that as a limitation/warning,
not as `access_failed`. If the visible text/title is still an interstitial,
CAPTCHA, or access-block shell, report `access_failed` / PARTIAL even when DOM
and screenshot artifacts were preserved.

The agent cannot reliably know browser-rendering or login-wall posture before
running a byte-preserving adapter. A Direct HTTP, Media / Asset, or Archive.org
exit code `0` proves only that bytes were preserved into a packet. It does not
prove source-meaningful content was captured. If the decision question targets
content that is commonly JavaScript-rendered, login/entitlement-gated, or
browser-visible only, or if the preserved body appears to be an app shell,
consent wall, cookie wall, auth/login wall, bot-block page, or other
non-content shell, report `visible_capture_limitation` and consider Browser
Snapshot only when the operator authorized that next runner. Do not describe any
packet as a clean content capture merely because bytes or browser artifacts were
preserved.

If preserved or fetched content is obviously private, confidential,
cross-account, admin-only, or workspace/team spillover, stop and flag it for the
operator. Do not report it as a clean capture. The boundary call belongs to the
operator/owner, not the agent.

## Required Inputs

Before running anything, the agent must have:

- `decision_question`: the capture question supplied by the operator;
- `output_directory`: a new, empty packet directory path;
- one concrete source input:
  - local file path for local-file packets;
  - ordinary HTTP URL for Direct HTTP;
  - explicit media/asset URL list for Media / Asset;
  - original URL plus optional 14-digit `YYYYMMDDhhmmss` cutoff timestamp for
    Archive.org;
  - ordinary URL for Browser Snapshot;
  - ordinary URL for CloakBrowser Snapshot;
  - ordinary URL, storage-state label, and allowed session mode for
    Authenticated Browser Snapshot;
- enough context to set `cutoff_posture` or explain why cutoff posture is
  unknown.

For the local-file packet runner only, the agent must also have:

- `source_family`: operator-supplied source-family label. If the operator did
  not supply one, do not infer it from file contents; stop or use an explicitly
  authorized neutral value such as `operator_unspecified`.
- `source_locator` or `source_locator_unknown_reason`: operator-supplied
  provenance pointer, or a visible reason no stable locator was supplied.

Direct HTTP, Media / Asset, Archive.org, Browser Snapshot, CloakBrowser
Snapshot, and Authenticated Browser Snapshot runners have default source-family
labels and URL-derived locators; do not ask for local-file-only fields when
those runners are used.

For Archive.org, preflight the cutoff timestamp before running. If supplied, it
must be exactly 14 digits in `YYYYMMDDhhmmss` form. If the operator supplies a
conflicting, too-short, too-long, or malformed timestamp, stop and ask for a
corrected value. Do not silently repair the timestamp by guessing the intended
date.

For social creator/account capture where the operator intends to start a new
creator capture, run the Creator Registry match preflight before capture and
carry its receipt in the agent report or handoff. Use
`forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_registry_match_preflight_usage_v0.md`
for candidate JSON shape, receipt outcomes, and the runner command. Do not start
`new_capture` unless the candidate batch was preflighted with
`intended_action: new_capture` and the resulting receipt row shows `decision:
new_candidate` and `can_start_new_capture: true` (`action_status: allowed`). A
row that only shows `decision: new_candidate` and `action_status: allowed` from
a `classify` or `update_existing` query does not clear `new_capture`; check
`can_start_new_capture` directly rather than reconstructing the condition.
`existing_match` routes to updating or working against the matched
registry identity; `ambiguous_match` and `invalid_candidate` stop the capture
until resolved. A manual visual scan of the registry or projection is useful
orientation, but it is not a substitute for the preflight receipt.

Routine TikTok onboarding must use the default
`creator_intent=new_onboarding` for an exact Creator Registry match whose
`onboarding.onboarding_state` is `not_onboarded`. A missing or ambiguous match,
an invalid onboarding marker, or `onboarding_state=onboarded` blocks before the
browser phase. Use `new_capture` only to capture profile/grid assessment evidence
for an identity absent from the registry; it never deep-captures videos or
enqueues audience work. Use `update_existing` only for recapture, supplement
provenance, or an existing-creator regression.

`new_capture` and full `new_onboarding` apply the standing owner US-market gate
to the captured profile bio. For `new_capture`, the runner writes the bounded
profile/grid assessment and stops before any deep capture; an explicit non-US
country flag appends the corresponding Frontier defer when `--data-root` is
supplied. Full `new_onboarding` retains its earlier pre-grid gate. With no
explicit non-US flag the runner continues; that is not proof of a US creator or
audience and is not an eligibility decision. Do not infer geography from
profile language or TikTok `webapp.app-context.region`.

For Authenticated Browser Snapshot, `session_mode` must be exactly one of:

- `free_account_created_session`
- `paid_entitled_session`
- `client_provided_session`
- `consenting_coworker_session`

Manual auth-state labels retain the legacy worktree-local
`forseti-harness/_auth_state/` default. A logical `--session-profile` instead
resolves auth state from the explicit runner root, then
`FORSETI_AUTH_STATE_ROOT`, then the stable user-local Forseti root
(`%LOCALAPPDATA%\Forseti\auth_state` on Windows), so profile-backed state does
not depend on the current worktree. Do not paste, print, stage, commit, or copy
storage-state JSON, cookies, credentials, or session values into a packet or
report.

For TikTok sessioned live probes that need a source-access provenance check,
use the CloakBrowser user-data warmup/export path so the local ignored
auth-state sidecar can carry category-only provenance. The live runner flag
`--require-harness-proxy-posture no_proxy_profile_loaded` attests only that
the Source Capture harness did not load a proxy profile for that warmed user-data
label; it is not full-network no-proxy egress proof, is not a forgery-proof producer-identity ledger against deliberate local sidecar edits, and does not authorize
printing, copying, or reporting cookies, storage-state JSON, proxy endpoints,
exit IPs, profile paths, or device identifiers.

For cold-agent TikTok work, open
`docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md` and
`docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md` before
patching or re-diagnosing blockers. The runner already owns the current setup
actions: benign intro/OK prompts, one visible retry, the comments -> `You may
like` / `More like this` -> comments route, challenge kind receipts, pre-action
owner handoff, optional explicitly requested X/Close follow-through, and
fail-closed admission. Under the `chowdakr_sg_tiktok` session profile, a visible
slider/captcha opens the owner prompt before any scripted pointer action. If the
marker does not clear, scripted actions stay suppressed and capture fails closed.
The agent must not drag or solve the puzzle, and any manual owner action is
source-access intervention rather than clean capture.

The session profile may select the retained Chrome CDP backend. In that case the
live runner checks that the retained browser profile is nonempty and selects
exactly one usable loopback CDP endpoint whose root Chrome process was launched
with that profile path. A different live Chrome or CloakBrowser endpoint does not
qualify. The runner then passes the bound engine into the same sanitized staging
and packet-admission path. Do not add
`--allow-diagnostic-browser-backend`; that flag is for manually selected
diagnostic backends, not for a validated retained-session profile.

Before implementing or revising a live-browser route whose correctness depends
on a new or changed UI transition (selector, control, navigation mode, or
post-action state), run a bounded retained-session transition probe before
patching runtime. Independently prove that the exact action target materializes
and that its required postcondition holds without acting on an unrelated
control. Do not begin end-to-end dogfood until every changed transition passes;
a failed probe returns to diagnosis, not a partial runtime patch followed by
repeated dogfood. This gate does not apply to pure parsing or ranking changes, or
to a route whose target and postcondition already have current successful
evidence.

An account-risk warning, unexpected logged-out/comment-auth wall, or `/login`
redirect is different from a CAPTCHA. It is a terminal account-safety stop:
scripted actions are suppressed before the next pointer action, automatic retry
is forbidden, Chrome remains open, and the operator checks TikTok Security
Alerts before starting a new run. Check Account Status only when login remains
restricted or another account capability appears limited. A CAPTCHA that the
owner clears successfully may continue the current batch; CAPTCHA presence
alone is not this circuit breaker.

For supervised creator onboarding with an already-running retained Chrome CDP
session, invoke the onboarding runner directly. It owns the Creator Registry
preflight and session-alias resolution; do not precede it with separate registry,
alias, browser, or CDP probes unless it emits a blocker. Those duplicate checks
add operator latency without improving the runner's failure visibility.

On its first CDP capture, the runner adopts the most recently enumerated
non-closed TikTok page even when it shows another creator/path. It never infers
active focus, never adopts a cross-platform page, and creates one page only when
no TikTok page exists. The adopted page navigates to the requested creator when
needed; when normalized TikTok host/path already matches, scheme/query/fragment
differences do not trigger another `goto`. The runner reuses that page and
detaches without closing operator Chrome. Read `page_acquisition_policy`,
`initial_platform_match_count`, `initial_exact_match_count`,
`page_adoption_count`, `page_creation_count`, `page_navigation_count`, and
`same_url_navigation_suppression_count` from the receipt. Duplicate TikTok pages
use the disclosed latest-enumerated policy.

Suggested-account discovery is modal-primary. The runner clicks the visible
creator `Followers` count through `BrowserPagePointerAction`, waits for the
visible relationship dialog, clicks that dialog's `Suggested` tab through the
same action routing, and extracts profile rows only from that visible dialog.
The retained CDP context is patched with CloakBrowser
`resolve_config("careful")`; outer action `move_steps` disclose routing input,
not CloakBrowser's internal humanized pointer path. Only when the modal route is
not visible may the runner use the visible `Suggested accounts` heading plus
exact `View All` fallback. Preserve `captured`, `visible_empty`, and
`not_visible` distinctly. Never click Follow, open a candidate profile, like,
or message.

Establish the creator grid once on the acquired page. Suggested primary,
fallback, relationship-modal close, grid collection, and every onboarding deep
capture stay on that page; do not reload an already matching creator path or
click Latest, Popular, or Oldest during grid acquisition or deep capture. After
a successful full new-onboarding deep capture only, the runner performs one
bounded `Oldest` sort observation on the same page, verifies the exact control's
`data-active=true` state, and chooses the minimum exact creator-owned
`createTime` from the first returned batch. It retains only the typed canonical
observation in the existing grid/batch evidence; a missing control is
`oldest_sort_not_exposed`, a verified empty profile is `no_public_posts`, and an
exposed but unverifiable selection or creator identity fails onboarding. This is
not part of profile refresh, never claims account creation time, and restores
the shared page to a mechanically verified `Latest` state after a successful
observation. Grid
acquisition reads the initial exact-creator DOM order. If at least 27 videos are already loaded, it performs zero
wheel actions; otherwise it uses bounded adaptive normal 20-35 percent viewport
mouse-wheel bursts only until the first positive exact-video-ID batch delta.
After the sufficient initial window or first new batch is identified, perform no
further wheel action and use passive DOM reads until the exact ordered video-ID
sequence is unchanged for two consecutive polls. It does not scroll to page
bottom, repeat wheel bursts to reach a response count, accept a sub-27 one-batch
window, or require all 30 rows. Freeze up to the 30-row cap from that stabilized
DOM order and fail if fewer than the selected count are usable. Read the
collection receipt for policy, the 27-video sufficiency threshold, whether the
initial window was sufficient, initial/final/new DOM counts, whether a new batch
appeared, bounded wheel count and action receipts, passive-poll count, two-poll
stability, and stop reason.

After grid acquisition and selection, wait a randomized 8-13 seconds before the
first deep capture. The onboarding receipt records planned and actual wait, UTC
`observed_at`, and elapsed-seconds phase chronology. Select the top eight
eligible videos by reach rank. Prefer structured profile-grid `playCount`; when
it is absent, the exact tile's compact view-count footer may supply an explicitly
rounded/approximate DOM reach value with raw text and field provenance. Likes,
comments, shares, and saves are preserved when naturally available but do not
gate fixed-count reach membership. Record pinned state, but pinning never
displaces reach ranking.

For every selected video, intersect the pending selection with tiles that are
CSS-visible and intersect the current viewport, randomly click one through
`BrowserPagePointerAction` on the retained CloakBrowser-`careful` context,
capture its matching video overlay, then click the overlay X to return to the
creator grid. Resolve the chosen tile's link-routed view-count footer immediately
before the pointer action and click a randomized point within that footer's
15-85 percent inset on both axes. Treat the tile as actionable only when that
footer itself intersects the viewport; partial thumbnail visibility is not
enough. Do not click the thumbnail body after the
humanized move activates TikTok's hover-preview `<video>`; that surface may
consume the click as playback without opening an overlay. Remember stable video
IDs and logical grid positions, never absolute
screen coordinates. If no pending selected tile is visible, compare those
positions with the freshly observed visible range and use bounded small mouse-
wheel bursts covering 20-35 percent of the viewport in the required direction.
Before wheeling through a frozen logical range, compare the live loaded video-ID
order with the frozen window. Once the live grid has loaded through that
window's bound, zero identity overlap is `frozen_window_identity_drift` and must
stop immediately. A non-consecutive repeated grid-state fingerprint is
`progress_cycle` and must also stop rather than reverse direction indefinitely.
The wheel receipt distinguishes the CloakBrowser-humanized cursor move from the
raw wheel burst. Do not use
`scrollIntoView`, otherwise
target-scroll a tile, or navigate to a selected video URL directly. If a click
does not materialize the matching overlay, wait 60 seconds, recompute the visible
subset, and retry once; a second failure stops loudly. Read
`grid_deep_entry_or_none` for visible candidates, random choices, grid positions,
pointer receipts, pagination/retry timing, final URLs,
`logical_grid_positions_remembered=true`,
`absolute_pixel_positions_cached=false`,
`targeted_tile_scroll_performed=false`, and
`direct_video_navigation_count=0`.

After Suggested extraction, close the surface through its own route-specific
control before grid collection: the relationship-dialog close control for the
primary route, or the exact profile `Suggested accounts` toggle for the View All
fallback. Never use a page-wide generic Close/X search or geometric X fallback
for this transition. No grid wheel burst or tile click is allowed while the
route surface remains expanded, any blocking modal remains, or the page remains
scroll-locked. Read `suggested_surface_close_before_grid_or_none` for the outer
route, route-specific close action, expanded/modal state, blocking-modal count,
and scroll-lock state. Any required close that does not click or clear all of
those gates stops loudly before the first grid interaction.

The overlay URL plus clicked grid identity bind each video. Preserve structured
metadata naturally present in profile-grid responses, the raw/parsed rounded DOM
view footer when used, initially exposed comments from page-owned comment
responses or visible overlay DOM, and source-native
subtitle tracks when available. Direct-page `itemStruct` is optional on this
route. Record field provenance and preserve unavailable optional values as
unavailable; do not manufacture zeroes. Direct-video capture remains a separate
diagnostic/future collector capability and is never an onboarding fallback.
Capture initially exposed top comments only: no comment pagination and no sticker
reverse-image feature. Silent like/follow failure is operator-observed
soft-restriction evidence only; do not run an automated state-changing probe or
retry.

With `--data-root`, a captured non-empty suggested result must return a non-null
written frontier path; any packet or frontier write failure stops loudly.
Validated external profile links may create sibling-channel linkage only through
the existing Creator Registry identity contracts; this discovery runner does not
infer those edges. A historical recapture requires `--prior-capture-pointer` and
writes a separate Bronze supplement with
`re_capture_relationship=supplement`; it never rewrites prior provenance.

The runner emits flushed `tiktok_creator_onboarding_progress_json=` phase events
and a `tiktok_creator_onboarding_blocker_json=` event before a fail-loud exit.
Treat those events as the live status source. The runner returns from every
captured overlay to the creator grid before choosing the next visible pending
tile; it never simulates address-bar typing, spoofs a referrer, or directly loads
a selected video URL. After the final capture, CDP detaches without closing the
operator-owned Chrome; the final selected overlay remains open unless a blocker
requires the page to remain at its supervised stop surface.

The separate alias check below remains a diagnostic command for a blocker or an
explicit session-health check; it is not a required preamble to onboarding.

For recurring TikTok grid monitoring, use the daily heartbeat operator instead
of creator onboarding. The input is an explicit active roster; each row must
name `platform: tiktok`, a stable `platform_account_id`, the current public
`handle`, `monitoring_status: active`, and `cadence: daily`. This runner captures
only the bounded creator grid, freezes it before packet admission, and reports
completion only after verified Bronze admission. It does not collect suggested
accounts, comments, subtitles, or deep captures, and it does not run Silver or
install a scheduler.

```powershell
python runners/run_source_capture_tiktok_daily_heartbeat_operator.py `
  --active-roster "<active-tiktok-roster.json>" `
  --run-control-root "<run-control-root>" `
  --plan-date "<YYYY-MM-DD>" `
  --bucket 1 `
  --lane-id lane_1 `
  --lane-count 1 `
  --data-root "<verified-data-root>" `
  --session-profile "chowdakr_sg_tiktok"
```

Run additional bucket/lane invocations externally as needed. Reusing the same
date plan is idempotent for terminal creators; retries require an explicit
`--retry-status` and `succeeded` is never retryable. A missing or malformed
receipt, attempt mismatch, or unverified success packet makes the operator exit
nonzero. After an account-safety or unresolved-challenge stop, remaining
creators are recorded as skipped-before-attempt rather than fabricated failures.

Validate the machine-local alias without opening a browser:

```powershell
python runners/check_source_capture_session_profile.py `
  --session-profile "chowdakr_sg_tiktok"
```

Recommended one-fixture sessioned TikTok command for a cold agent:

```powershell
python runners/run_source_capture_tiktok_live_batch_probe.py `
  --creator-handle "<handle>" `
  --creator-profile-url "https://www.tiktok.com/@<handle>" `
  --video-url "https://www.tiktok.com/@<handle>/video/<video-id>" `
  --session-profile "chowdakr_sg_tiktok" `
  --output-dir ".\_test_runs\tiktok_live_<handle>" `
  --admit-output ".\_test_runs\tiktok_live_<handle>_packet"
```

Read the runner's `tiktok_live_probe_summary_json=` lines first. A staging
summary with `outcome=staging_complete` and `admission_target=local_admit_output`
means the local packet path was requested; `admission_target=bronze_data_root`
means explicit data-lake admission was requested. `outcome=owner_attention_required`
means a manual slider/captcha handoff is needed or was attempted; it is a
source-access intervention, not clean capture. Any `fail_closed_*` outcome or
admission summary with `fail_closed=true` stops the lane until the typed reason
is resolved.

The live-probe runner's internal cadence applies only inside that one process.
When a bounded acquisition uses separate one-creator commands, leave at least
90 seconds between commands and inspect each summary before starting the next.
Stop the sequence on a visible block, captcha, or fail-closed outcome; do not
launch the next creator while the prior result is still unknown.

If any required input is missing, do not invent it. Stop and report the smallest
missing input.

## Runner Selection

Use the narrowest runner that matches the supplied input.

| Supplied input | Runner | Use when |
| --- | --- | --- |
| Already-local raw source files | `run_source_capture_packet.py` | The operator already preserved files and only needs a packet. |
| One ordinary URL | `run_source_capture_http_packet.py` | A single page/file may be fetched through normal Direct HTTP. |
| Two or more ordinary URLs on one exact host | `run_source_capture_same_host_http_batch.py` | A small supplied list needs enforced serial pacing and stop-on-first-refusal behavior. |
| Explicit asset URLs | `run_source_capture_media_packet.py` | The operator supplied image/media/gallery-frame URLs directly. |
| Original URL plus archive need | `run_source_capture_archive_packet.py` | The operator needs Archive.org availability and maybe snapshot body. |
| Browser-rendered or screenshot-needed page | `run_source_capture_browser_packet.py` | One supplied URL needs anonymous browser rendering or screenshot preservation. |
| Login-visible or entitled browser session content | `run_source_capture_browser_session_bootstrap.py`, then `run_source_capture_authenticated_browser_packet.py` | The operator authorizes an allowed manual-login storage-state session. |
| Anti-blocking browser-rendered page | `run_source_capture_cloakbrowser_packet.py` | One supplied URL needs anonymous CloakBrowser rendering because ordinary Browser Snapshot controls (`--headed`, `--browser-channel`, `--settle-seconds`) are expected to fail or have failed. |
| Retail/PDP anti-blocking capture plus local projection | `run_source_capture_cloakbrowser_packet.py --source-family retail_pdp --retail-pdp-projection-output <path>` | One supplied retailer PDP URL needs a Source Capture Packet and a separate no-network Retail/PDP projection JSON. For the current Amazon/Sephora/Ulta smoke commands, use `docs/product/source_capture_toolbox/retail_pdp_sidecar_operator_playbook_v0.md`. |
| Reddit pre-commercial anti-blocking capture | `run_source_capture_cloakbrowser_packet.py` for one supplied old Reddit/thread URL only | The runner can preserve one supplied browser-visible URL through CloakBrowser; it does not discover Reddit targets, monitor threads, parse/consolidate comments, use credentials, or authorize broad crawling. |

### Conditional Page-Owned Response Observation

When the required signal is absent from static HTML and embedded page state but
the page obtains it through a page-owned JSON, XHR, Fetch, or GraphQL response,
use an existing source-specific runner that calls
`fetch_browser_page_observation_capture(...)`. This is a conditional substrate
route, not a preflight for every capture and not authority to create a generic
traffic recorder.

The source-specific route must bind one exact page URL and decision question, a
narrow `response_url_predicate`, bounded load/click/scroll actions, response
count and byte caps, and a requested-versus-served subject check. Preserve only
the response bodies and provenance fields required by that route. Do not
preserve request headers, cookies, tokens, raw signed URLs, or unrelated page
traffic. A missing, oversized, ambiguous, access-gated, or subject-mismatched
response stays a visible capture limitation; it is never an empty-source
success.

Replay the endpoint through Direct HTTP only after a bounded calibration proves
that the same source-visible fields and subject binding survive without copied
credentials, session material, browser-generated signatures, or access-control
bypass. Otherwise keep the request page-issued and observe its matching
response inside the entitled or public browser context.

If a supplied URL points directly to a source-meaningful asset, prefer Media /
Asset. If it points to a page or file whose whole response body is the capture
target, prefer Direct HTTP. If unclear, stop and ask for the operator's intended
runner rather than guessing from URL shape.

For Reddit thread JSON, do not treat a cold `.json` URL as the default Direct
HTTP or browser-navigation target. Current bounded probes show cold `.json`
requests can return Reddit network-security blocks even when the matching old
Reddit HTML thread is capturable. The useful JSON shape is a specialized warm
same-context flow: load the exact old Reddit HTML thread first in CloakBrowser,
confirm it is not access-blocked, then fetch the same thread's `.json` inside
that same browser context and preserve both bodies. Use that only when a
specialized runner or explicitly bounded diagnostic authorizes it; do not use it
to follow links, discover targets, crawl subreddits, capture users/profiles, or
monitor threads.

For supplied exact old Reddit thread URLs where current old Reddit HTML is the
capture target, use the bounded Direct HTTP batch runner first. CloakBrowser is
the anti-blocking/browser-visible route when Direct HTTP is unsuitable, blocked,
or explicitly requested; do not skip a working Direct HTTP capture merely
because CloakBrowser exists.

For bounded old Reddit Direct HTTP batches, prefer the batch runner's
budget-window cadence over a mechanical fixed delay when running more than a
tiny smoke list:

```powershell
python runners/run_reddit_old_http_batch.py `
  --url-list "<json list of exact old.reddit.com thread URLs>" `
  --output-root "<scratch output directory>" `
  --decision-question "<bounded capture question>" `
  --max-urls 9 `
  --cadence-mode bounded_jitter `
  --cadence-window-seconds 900 `
  --cadence-min-gap-seconds 20 `
  --cadence-max-gap-seconds 180
```

This is a bounded low-load schedule, not a stealth or human-impersonation claim.
The runner records the cadence mode, random seed, planned waits, planned
offsets, and actual per-slot timestamps in `batch_summary.json`. Keep
`--max-urls` as the hard ceiling, choose a window that can fit the minimum gap,
and stop on visible blocks instead of adding retries or proxy/browser fallback
inside the same runner. Use `--delay-seconds` only when a fixed mechanical
cadence is intentionally desired.

When a downstream agent needs to read Reddit outputs, generate two local view
states from the existing JSON artifact instead of feeding the durable artifact
blindly into context:

```powershell
python runners/run_reddit_agent_view.py `
  --input "<reddit_thread_consolidation.json | reddit_candidate_url_intake.json | reddit_graph_frontier_register.json>" `
  --output-dir "<fresh scratch output directory>"
```

The runner writes:

- `reddit_agent_view_full.json`: a full copy of the input JSON for audit and
  fallback.
- `reddit_agent_view_stripped.json`: an agent-context view that removes repeated
  packet provenance, per-row receipts, direct author handles, scores,
  timestamps, generated identifiers, and repeated non-claims while preserving
  source meaning such as thread/post/comment text, graph shape, candidate
  values, postures, counts, stop reasons, and promotion-relevant fields.
- `reddit_agent_view_receipt.md`: a local receipt for the view-generation step.

The stripped view is not a replacement for the durable artifact and is not a
source-capture, validation, readiness, source-completeness, Data Capture, ECR,
Cleaning, or Judgment claim. Do not remove strings inside `body_text` merely
because they look like HTML or CSS; those may be real user content.

Before making stripped views the default read surface for agents, build a local
A/B probe pack from one or more existing view directories:

```powershell
python runners/run_reddit_agent_view_ab_probe.py `
  --view-dir "<directory containing reddit_agent_view_full.json and reddit_agent_view_stripped.json>" `
  --view-dir "<another view directory, optional>" `
  --output-dir "<fresh scratch output directory>"
```

The A/B probe runner verifies that each full/stripped pair describes the same
Reddit artifact type, then writes paired prompts and a comparison worksheet for
agent or owner review. It does not call a model, fetch Reddit, evaluate answers,
choose the default view, promote candidates, or replace the durable artifact.
Treat its `needs_agent_or_owner_outputs` status as the next human/agent
comparison step, not as a pass/fail result.

The current Reddit agent read-surface rule is:

- The agent reads the **cleaned view** we prepare upstream (emitted today as
  `reddit_agent_view_stripped.json`). Cleaning runs AFTER projection, on the
  projected artifact, and is **content-lossless**: it preserves all substantive
  content (thread/post/comment text, visible candidate values, bounds/caps/
  exclusions, stop reasons, selected frontier decisions, parser warnings that
  affect interpretation, non-claims) and removes only worthless noise (repeated
  packet provenance, hashes, paths, generated identifiers, score/timestamp
  cruft, repeated non-claims). The agent gets all the data at a fraction of the
  token/context cost. It is not an agent toggle between two surfaces; it is the
  one view we hand over.
- The verbatim copy (`reddit_agent_view_full.json`) is **provenance/audit only**
  -- open it for packet/source provenance, raw artifact lineage, exact
  reconstruction, or any decision that could be confused with promotion,
  validation, source completeness, fixture admission, commercial readiness, Data
  Capture handoff, ECR, Cleaning, or Judgment.
- Because cleaning is content-lossless, dropping any decision-relevant field is a
  **bug**, not aggressive cleaning (e.g. the caps/exclusions regression caught
  this session). Guard the retained fields with regression tests, not this rule
  alone.

This rule began as a three-case local A/B probe and is now framed as a
content-lossless cleaning step for token/context efficiency. It is a read-surface
operating rule -- not validation, readiness, source-completeness proof, canonical
evidence replacement, or a claim that byte reduction proves quality.

Do not chain runners unless the operator explicitly asks for multiple packets.
For example, do not run Archive.org automatically after Direct HTTP fails unless
that fallback was requested.

When the operator requests archive fallback for a bounded blocked URL, keep the
fallback inside the same source unit. For a single blocked URL:

1. preserve the live/current block packet when the runner wrote one;
2. run Archive.org against the exact supplied URL;
3. for Reddit thread URLs only, if the exact old/new host has no snapshot,
   optionally run Archive.org against the same-thread canonical host variant
   (`old.reddit.com` <-> `www.reddit.com`) without changing subreddit, thread
   id, slug, or query scope;
4. report `snapshot_count`, selected snapshot timestamp, whether a snapshot body
   was preserved, and any `archive_body_not_preserved` or equivalent limitation;
5. stop.

Do not use archive fallback to broaden into subreddit crawl, source discovery,
related URLs, user/profile pages, comment links, recommendations, or "more like
this" surfaces. `snapshot_count=0` is a real fallback result, not permission to
search wider.

## Capture Retention Posture

Every capture runner has a stated retention default. `content` projects a
structured record in flight and discards the source bodies after hashing them;
`raw` preserves the bodies. Extraction failure or an anomaly tripwire ALWAYS
falls back to preserving raw for that capture (`retention_outcome=raw_failure`,
nonzero exit) -- content retention never turns a broken parse into a thin
success. Where a runner exposes `--retention-mode`, `raw` stays selectable per
run as an explicit operator evidence posture.

Read this table as the current default, not as permission: flipping a lane to
content requires its parity gate first (below).

| Lane / surface | Runner | Retention default |
| --- | --- | --- |
| Google SERP (US-parameterized) | `run_source_capture_cloakbrowser_packet.py --source-surface google_serp_us_parameterized` | `content` |
| Reddit old-HTML batch | `run_reddit_old_http_batch.py` | `content` |
| Reddit subreddit grid | `run_reddit_grid_capture.py` | `content` (one per-run raw canary subreddit) |
| Basenotes MGT | `run_basenotes_mgt_capture.py` | `content` |
| Fragrantica MGT | `run_fragrantica_mgt_capture.py` | `content` rendered; `raw` on the Direct HTTP leg |
| Parfumo MGT | `run_parfumo_mgt_capture.py` | `content` targeted-rendered; `raw` on the Direct HTTP leg |
| Retail PDP aggregates (Sephora, Ulta, Nordstrom, Target, Amazon, REVOLVE, Luckyscent) | `run_source_capture_cloakbrowser_packet.py --retail-capture-profile <name>_pdp_aggregate` | `content` |
| Retail grid aggregates (Sephora brand/catalog, Ulta brand/category, Target, Amazon, REVOLVE) | same runner with a `*_grid_aggregate` profile | `content` (Target/Amazon grids require it) |
| Nordstrom brand corpus | `run_nordstrom_brand_corpus.py` | `raw` (passes `--retention-mode raw` explicitly) |
| TikTok video / grid | `run_source_capture_tiktok_video_packet.py`, `run_source_capture_tiktok_grid_packet.py` | content-shaped by construction (`raw_response_bodies_excluded:sanitized_admission_only`) |
| YouTube watch | `run_source_capture_youtube_watch_packet.py` | content-shaped by construction (`retention=selected_observables_only`) |
| Generic packet runners (Direct HTTP, browser, CloakBrowser without a content profile, archive, media, anti-block HTTP, real-Chrome CDP, authenticated browser, historical, price payload, ATS job posting, IG calls / reels grid) | `run_source_capture_*_packet.py` | `raw` -- `no_extractor_exists` for an arbitrary surface |

`run_source_capture_http_packet.py` has no `--retention-mode` flag: it takes a
`ContentExtractionSpec` from a calling lane runner and is `raw` when called
without one.

The Google SERP surface label is a route assertion, not a free-form tag. Its
`--url` must be an HTTPS `google.com/search` URL with exactly one non-empty `q`
and exactly `hl=en`, `gl=us`, and `pws=0`; the runner rejects a mislabeled route
before capture. The content record retains the visible AI Overview text as well
as typed result rows because the discarded DOM is not a later recovery source.

### Parity gate before a flip

A lane flips to content only after `run_capture_retention_parity_gate.py`
passes for its surface. The gate is a cheap local script -- no network, no
model tokens, run once per lane over captures the lane already made:

```powershell
python runners/run_capture_retention_parity_gate.py packets `
  --surface google_serp_us_parameterized `
  --packet-root "<packets with raw/ preserved>" `
  --baseline-record-dir "<the lane's pre-flip extracted records>" `
  --output "<verdict json>"
```

It re-extracts the preserved bytes with the current in-flight extractor,
field-diffs against the record the lane banked, checks surface invariants, and
exercises the anomaly tripwires synthetically. If a lane cannot be gated by a
cheap script, record `gate_not_cheap` and flip without it rather than building
ceremony.

For Google SERPs, the independent invariants require contiguous per-module
ranks, retained AI Overview content when that module is present, coherent URL
presence metadata, and agreement between a retained URL and the row's visible
domain/platform. In rolling-sample mode, an incomplete sample or a sample that
the current extractor now rejects fails `rolling_sample_integrity`; it cannot
produce a passing gate through `not-run`.

### Rolling raw sample

Content retention forecloses re-extraction, so a flipped surface keeps a
*recent* ground truth instead of a permanent corpus. Pass `--raw-sample-root`
(and `--raw-sample-run-key` for a batch campaign) and the FIRST content
capture of that surface per UTC day -- or per run -- copies its rendered bytes
and the banked content record to an operator-drive sample store outside Git.
Use a unique run key for each campaign; reusing one suppresses another sample
until the prior key ages out.
Samples older than 30 days are pruned on the next claim. Nothing is pinned
forever and none of it is durable evidence.

After ANY extractor edit, re-run the window:

```powershell
python runners/run_capture_retention_parity_gate.py rolling-sample `
  --surface google_serp_us_parameterized `
  --raw-sample-root "<operator-drive sample root>"
```

This replaces re-extraction of history as the defect-catching mechanism.
Extractor fixes apply FORWARD ONLY for captures made under content retention.

## Restricted Network Permission Discipline

In Codex or another restricted sandbox, launch live network-backed runners with
per-operation network permission before the first attempt. This applies to:

- Direct HTTP;
- Media / Asset capture for remote URLs;
- Archive.org availability/body capture;
- Browser Snapshot or Authenticated Browser Snapshot against a remote URL;
- CloakBrowser Snapshot against a remote URL.

The local-file packet runner does not need network permission.

On Windows, `WinError 10061` before any HTTP response is usually sandbox network
refusal, not a source-access result. Do not record that as a source limitation
or spend a doomed first attempt when the runner is known to require network
access. Run the same bounded command with per-operation network permission, or
report an operational blocker if permission is unavailable.

If a packet exists and its preserved response metadata shows an HTTP status such
as `403 Blocked`, treat that as a source-access outcome rather than a sandbox
network refusal. Inspect the preserved body enough to distinguish source content
from an interstitial, but do not infer source meaning from the block page. A
visible Reddit "network security" block is a hard content-capture failure for
that method and should route only to an explicitly requested bounded fallback.

Do not request broad standing Python or network permission for source capture.
The approval request should name the exact runner class and the single bounded
source packet attempt. If a denied or timed-out attempt leaves no packet
directory, the same fresh output path may be reused; otherwise choose a new
output path or ask the operator before clearing anything.

## Output Directory Discipline

Use a fresh directory under `_test_runs/` for smoke tests or under
`reports/source_capture/` for local review evidence. Do not overwrite existing
packet directories.

`_test_runs/` is ignored local scratch. `reports/source_capture/` is not
ignored by default and may be git-tracked. Packets can contain copied raw
third-party source files, media, archive snapshot bodies, and machine-specific
provenance paths. Do not stage or commit generated packet directories or raw
packet contents without an explicit owner decision.

Generated packets are discovery-grade capture outputs. They are not rights,
retention, sensitivity, material-use, client-use, or durable-evidence clearance.
If downstream Judgment or client-facing work would make a packet material,
follow the source-access boundary decision and perform clean
reacquisition/verification through the normal disclosed path before relying on
it materially.

For packet lifecycle, retention, durable citation, and sensitivity handling,
open
`docs/decisions/source_capture_packet_fixture_retention_sensitivity_decision_v0.md`.
That decision keeps generated packets scratch by default and distinguishes
durable closeout summaries from fixture admission.

Recommended naming:

```text
_test_runs/source_capture_<runner>_<short_slug>
reports/source_capture/<case_or_slot>_<runner>_<short_slug>
```

Generated packet directories are not canonical fixtures unless a separate
fixture-admission decision says so.

## Commands

Run from `forseti-harness/`.

Local file packet:

```powershell
python runners/run_source_capture_packet.py `
  --source-family "<source family>" `
  --source-locator "<source locator or local provenance pointer>" `
  --decision-question "<operator-supplied decision question>" `
  --input-file "<local raw file>" `
  --cutoff-posture "<operator-supplied cutoff posture>" `
  --access-posture "local_file_only" `
  --archive-history-not-attempted-reason "local packet runner does not query archives" `
  --media-modality-not-attempted-reason "local packet runner does not retrieve additional media" `
  --output "<packet directory>"
```

Use repeated `--input-file` flags when the operator supplies multiple already
local files for the same bounded source packet. If no stable source locator was
supplied, replace `--source-locator` with:

```powershell
--source-locator-unknown-reason "<operator-supplied reason no stable locator is available>"
```

Direct HTTP:

```powershell
python runners/run_source_capture_http_packet.py `
  --url "<ordinary http or https URL>" `
  --decision-question "<operator-supplied decision question>" `
  --cutoff-posture "<operator-supplied cutoff posture>" `
  --output "<packet directory>"
```

The single-URL runner's intended-cadence fields describe operator intent in the
packet; they do not wait or coordinate separate processes. For two or more
ordinary URLs on one exact hostname, use the same-host batch runner instead of
starting independent commands:

```powershell
python runners/run_source_capture_same_host_http_batch.py `
  --job-list "<JSON list of job_id, url, and decision_question objects>" `
  --output-root "<scratch output directory>" `
  --minimum-gap-seconds 90
```

The batch runner requires a gap of at least 60 seconds, defaults to 90 seconds,
and waits after one response completes before issuing the next request. It
records every attempted and unrun job, preserves `Retry-After` when the source
returns it, never retries automatically, and stops the remaining queue on the
first non-2xx response, access shell, or capture failure. A later attempt needs
separate acquisition authority and must not precede a source-supplied
`Retry-After` interval.

Media / Asset:

```powershell
python runners/run_source_capture_media_packet.py `
  --asset-url "<explicit asset URL>" `
  --decision-question "<operator-supplied decision question>" `
  --cutoff-posture "<operator-supplied cutoff posture>" `
  --output "<packet directory>"
```

Archive.org:

```powershell
python runners/run_source_capture_archive_packet.py `
  --url "<original URL>" `
  --cutoff-timestamp "<YYYYMMDDhhmmss or omit if latest is intended>" `
  --decision-question "<operator-supplied decision question>" `
  --output "<packet directory>"
```

The Archive.org runner derives cutoff posture from `--cutoff-timestamp` when
the operator does not pass an explicit cutoff-posture flag. If latest snapshot
selection is intended, omit `--cutoff-timestamp` and report that no cutoff bound
was supplied. If a cutoff timestamp is supplied, check that it is exactly 14
digits in `YYYYMMDDhhmmss` form before executing; malformed timestamps are
operator-input defects, not archive-access failures.

Browser Snapshot:

The Browser Snapshot runner requires the optional browser dependency and a local
Chromium browser binary before live use:

```powershell
python -m pip install -e .[browser]
python -m playwright install chromium
```

```powershell
python runners/run_source_capture_browser_packet.py `
  --url "<ordinary http or https URL>" `
  --decision-question "<operator-supplied decision question>" `
  --cutoff-posture "<operator-supplied cutoff posture>" `
  --output "<packet directory>"
```

The Browser Snapshot runner defaults to an anonymous/headless browser path.
It preserves rendered DOM, visible text, a viewport screenshot, and browser
metadata. For one supplied URL, `--headed` runs visibly, `--browser-channel`
selects a local Playwright Chromium channel such as Chrome or Edge, and
`--settle-seconds` waits after navigation before artifact capture. It does not
use stored sessions, browser profiles, cookies, credentials, storage-state
files, anti-detect behavior, proxy behavior, CAPTCHA solving, crawling, OCR, or
source-meaningfulness classification. Its rendered-access posture is a guard
against fake success, not content sufficiency proof: visible text/title decide
whether the browser is still showing a block shell; residual challenge markers
in the full DOM alone are preserved as limitations.

On Windows, a failure containing `WinError 5` or `Access is denied` during
Playwright startup usually means the environment blocked Playwright's browser
driver subprocess launch. Treat this as visible capture failure: exit `3`, no
normal packet, and rerun only in an environment with subprocess-launch
permission. Do not switch methods or claim the adapter is broken from this error
alone.

Authenticated Browser Snapshot:

First bootstrap storage state through a visible manual login. This writes no
packet and stores only local ignored Playwright storage-state JSON under
`forseti-harness/_auth_state/`, plus a small local ignored metadata sidecar binding
the saved state file to the declared session mode:

```powershell
python runners/run_source_capture_browser_session_bootstrap.py `
  --login-url "<ordinary login or target URL>" `
  --state-label "<local state label>" `
  --session-mode "<allowed session mode>"
```

The runner opens a headed Chromium window. Complete only the permitted login in
that window, then press Enter in the terminal to save storage state. Do not pass
passwords, usernames, cookies, tokens, or profile paths to the runner. If the
label already exists, choose a new label or ask the operator before deleting
anything. Choose a non-sensitive state label; the label is later recorded in
packet metadata.

Then capture one explicit URL with that saved state:

```powershell
python runners/run_source_capture_authenticated_browser_packet.py `
  --url "<ordinary http or https URL>" `
  --state-label "<local state label>" `
  --session-mode "<allowed session mode>" `
  --decision-question "<operator-supplied decision question>" `
  --cutoff-posture "<operator-supplied cutoff posture>" `
  --output "<packet directory>"
```

The Authenticated Browser Snapshot runner preserves rendered DOM, visible text,
a viewport screenshot, and browser metadata. It records the session mode and
state label, and it refuses to run if the capture-time session mode does not
match the bootstrap sidecar. It does not copy, hash, print, or preserve the
storage-state file, metadata sidecar, or cookie/session values. It does not
prove login-wall absence or content sufficiency. If a login wall or auth
challenge remains visibly present, preserve that as a limitation and do not call
the packet a clean unlocked capture.

## Post-Run Inspection

After a runner returns exit code `0`, inspect:

```powershell
Get-Content <packet directory>\receipt.md
Get-Content <packet directory>\manifest.json
Get-ChildItem <packet directory>\raw
```

The agent report must include:

- runner used;
- command exit code;
- packet path;
- whether `manifest.json`, `receipt.md`, and `raw/` exist;
- preserved file list from `raw/`;
- source slice ids from `manifest.json`;
- access, archive/history, media/modality, cutoff, and re-capture posture from
  `manifest.json` when present, even when `limitations` is empty;
- warnings and limitations from `manifest.json`;
- any visible access, archive, media, or cutoff limitations;
- for new social creator/account capture, the Creator Registry match preflight
  receipt path and row decision/action status;
- receipt non-claims from `receipt.md` or manifest receipt metadata when
  present.

When the operator commissioned a source-quality pass, the agent report must also
include a `mini_god_tier_source_quality_report` block. Use result tokens from
`docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md`
and queue row-status vocabulary from
`docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md`.
Do not redefine those vocabularies in the runbook report.

For this runbook, an operator-commissioned source-quality pass means the
operator explicitly asked for source-quality improvement or mini god-tier
classification for a bounded source unit. Ordinary packet smoke tests, adapter
checks, local packaging tests, and generic capture runs do not trigger this
block unless the operator says they are source-quality passes.

The mini god-tier block reports the observed packet state and visible limits. It
does not validate the source, admit a fixture, prove source completeness, score
source quality, or decide Judgment meaning.

For source-quality passes, agents may use the report-skeleton helper after a
packet has already been written:

```powershell
python runners/run_source_quality_report_skeleton.py `
  --packet "<packet directory or manifest.json>" `
  --source-id "<operator-supplied source id>" `
  --output "<skeleton yaml>"
```

The helper is local and deterministic. It reads existing packet manifest and
packet-side metadata only, then emits a Mini God-Tier report skeleton for
operator completion. It does not fetch sources, parse source bodies for meaning,
infer source-language anchors, discover sources, admit fixtures, score source
quality, or finalize `mini_god_tier_met`. Treat `suggested_result_token` as
conservative guidance, not the final `result_token`.

For multi-row source-quality passes, agents may use the Source Quality State
Assembler after queue rows and packet paths already exist:

```powershell
python runners/run_source_quality_state_assembler.py `
  --queue "<queue yaml with explicit rows>" `
  --output "<state census yaml>"
```

The assembler is a read-only state census helper. It reads explicit rows,
existing packet paths, and existing packet manifests, then surfaces skeleton
state, visible stops, lifecycle posture, and operator-finalization requirements
per row. It does not run Source Capture tools, discover sources, fetch data,
rank rows, score source quality, auto-advance row status, or finalize
`mini_god_tier_met`. Missing packet paths and invalid manifests must remain
visible row stops, not hidden batch failures or clean passes.

For Archive.org packets, report that `snapshot_count` reflects
`collapse=digest` unique-content snapshot rows returned by the availability
endpoint, not every historical capture timestamp that Archive.org may hold.

For Browser Snapshot packets, report that the screenshot is viewport-only and
that browser artifacts do not prove content sufficiency, login-wall absence, or
source completeness.

For Authenticated Browser Snapshot packets, report the session mode and state
label, but do not report storage-state file contents, cookie values, tokens, or
credentials. Also report that storage-state use does not prove entitlement
sufficiency, login-wall absence, or source completeness.

Do not summarize the source as true or false. Do not say the capture is ready,
validated, complete, or sufficient for Judgment.

## Exit Handling

Exit code `0` means a packet was written. It does not mean source-meaningful
content was captured, nor that capture is complete or validated.

Exit code `2` means CLI/config/user input error. Report the exact missing or
invalid input and do not retry with guessed values.

Exit code `3` means capture failed visibly and no normal packet was written for
the current network runners. Report the error, the runner used, and the fact
that no normal packet exists.

Current runner exit-code shape:

| Runner | Exit codes | Notes |
| --- | --- | --- |
| Local file packet | `0`, `2` | Missing files, overwrite refusal, and CLI/config errors are exit `2`. |
| Direct HTTP | `0`, `2`, `3` | Network/no-body/size-cap capture failure is exit `3`; no packet. |
| Media / Asset | `0`, `2`, `3` | At least one preserved asset can write a packet with visible failed-asset limitations; all assets failed is exit `3`; no packet. |
| Archive.org | `0`, `2`, `3` | Availability lookup failure is exit `3`; no packet. Metadata-only states can still be exit `0` packets with limitations. |
| Browser Snapshot | `0`, `2`, `3` | Missing Playwright package, missing Chromium/local channel binary, navigation failure, or artifact failure is exit `3`; no packet. Exit `0` preserves browser artifacts only, not content sufficiency; rendered access-block pages are packets with visible limitations, not successful source-content capture. |
| Browser Session Bootstrap | `0`, `2`, `3` | Exit `0` writes ignored local storage-state JSON only; no packet. Missing/invalid labels are exit `2`; Playwright/browser/manual interaction failures are exit `3`. |
| Authenticated Browser Snapshot | `0`, `2`, `3` | Missing/invalid auth state is exit `2`; missing Playwright package, missing Chromium binary, navigation failure, or artifact failure is exit `3`; no normal packet. Exit `0` preserves browser artifacts only, not content sufficiency or login-wall absence. |

If a network runner reports a staging-collision or "clear it before rerunning"
message, clear or choose a new output parent only after operator approval. Do
not delete unrelated files.

If a runner writes a packet with limitations, preserve those limitations in the
agent report. Do not patch them away by rerunning a different method unless the
operator authorizes the next method.

## Minimal Agent Report Template

```text
source_capture_agent_report:
  runner: <local_file|direct_http|media_asset|archive_org|browser_snapshot|cloakbrowser_snapshot|authenticated_browser_snapshot>
  exit_code: <observed exit code>
  packet_path: <path or none>
  packet_written: <yes|no>
  inspected:
    manifest_json: <yes|no>
    receipt_md: <yes|no>
    raw_dir: <yes|no>
  preserved_files:
    - <raw file path or none>
  source_slices:
    - <slice id or none>
  postures:
    access: <manifest access posture or none>
    archive_history: <manifest archive/history posture or none>
    media_modality: <manifest media/modality posture or none>
    cutoff: <manifest cutoff posture or none>
    recapture: <manifest re-capture posture or none>
  warnings:
    - <manifest warning or none>
  limitations:
    - <manifest limitation or none>
  archive_snapshot_count_caveat: <if archive packet, collapse=digest unique-content rows; otherwise none>
  browser_snapshot_caveat: <if browser packet, viewport screenshot and no content-sufficiency proof; otherwise none>
  authenticated_browser_caveat: <if authenticated browser packet, session mode/state label reported but no state contents or login-wall absence proof; otherwise none>
  visible_stop_if_any: <missing input, access failure, browser-needed, no packet, or none>
  creator_registry_match_preflight:
    required_when: <new_social_creator_account_capture if this capture request is a new social creator/account capture, otherwise not_applicable; never omit this block>
    receipt_path: <path to preflight receipt JSON, or not_applicable>
    intended_action: <new_capture|classify|update_existing|not_applicable>
    decision: <existing_match|new_candidate|ambiguous_match|invalid_candidate|not_applicable>
    action_status: <allowed|blocked|not_applicable>
    can_start_new_capture: <true|false|not_applicable; must be true before starting new_capture>
  non_claims:
    - <receipt non-claim or none>
  mini_god_tier_source_quality_report:
    required_when: <operator commissioned a source-quality pass; otherwise omit>
    source_id: <operator-supplied source id or unknown_with_reason>
    result_token: <token from source_quality_mini_god_tier_profile_v0.md>
    packet_path: <path or none>
    best_in_bound_body:
      posture: <preserved|not_preserved|metadata_only|current_only|not_applicable>
      preserved_body_path: <packet-relative path or none>
      sha256: <hash or none>
      byte_count: <bytes or none>
      source_or_snapshot_time: <timestamp or unknown_with_reason>
    provenance:
      original_locator: <locator or unknown_with_reason>
      final_or_snapshot_locator: <locator or unknown_with_reason>
      access_status: <status or unknown_with_reason>
      content_type: <content type or unknown_with_reason>
      capture_time: <timestamp or unknown_with_reason>
    source_language_anchors:
      - <bounded source-visible anchor or not_applicable_with_reason>
    coverage_or_drift_note: <improves|replaces|supplements|conflicts|standardizes|unknown_with_reason>
    visible_limitations:
      - <limitation or none>
    lifecycle_state: <scratch|candidate_evidence|recommended_fixture_admission|separately_admitted>
    lifecycle_decision_reference: <required if separately_admitted; otherwise none>
    non_claims:
      - not validation
      - not source completeness proof
      - not fixture admission unless separately decided
      - not Judgment scoring
```

Do not use `separately_admitted` unless `lifecycle_decision_reference` cites the
separate fixture-admission or equivalent lifecycle decision. After completing
the mini god-tier report block for a queued source-quality row, update the queue
row from `packet_written_needs_report` to `reported` when the queue is part of
the commissioned work.

Do not collapse an exit-code-0 packet with empty limitations into "clean
capture." Packet postures may still carry current-capture, cutoff, archive,
media, browser, or access caveats that matter downstream.

## Testing Before Agent Reuse

Before treating a changed runner as reusable by agents, run the relevant focused
tests and the source-capture stack:

```powershell
python -m pytest -p no:cacheprovider tests/unit/test_source_capture_packet.py tests/contract/test_source_capture_packet_no_runtime_imports.py tests/unit/test_source_capture_direct_http.py tests/contract/test_source_capture_direct_http_contract.py tests/unit/test_source_capture_media_asset.py tests/contract/test_source_capture_media_asset_contract.py tests/unit/test_source_capture_archive_org.py tests/contract/test_source_capture_archive_org_contract.py tests/unit/test_source_capture_browser_snapshot.py tests/unit/test_source_capture_authenticated_browser_snapshot.py tests/contract/test_source_capture_browser_snapshot_contract.py
```

For a new adapter, add focused unit tests, contract tests, one manual dry-run,
and adversarial implementation review before committing it as an agent-facing
primitive.

For the source-quality report-skeleton helper, run:

```powershell
python -m pytest -p no:cacheprovider tests/unit/test_source_quality_report_skeleton.py tests/contract/test_source_quality_report_skeleton_contract.py
```

For the Source Quality State Assembler helper, run:

```powershell
python -m pytest -p no:cacheprovider tests/unit/test_source_quality_state_assembler.py tests/contract/test_source_quality_report_skeleton_contract.py
```

## Direction Change Propagation - Reddit Agent View Default Read Surface

```yaml
direction_change_propagation:
  doctrine_changed: >
    After a three-case local A/B probe, Reddit stripped agent views are now the
    default agent-read surface for semantic thread, Candidate URL Intake, and
    Graph Frontier reasoning, with full JSON required for audit, provenance,
    reconstruction, promotion, validation, source-completeness, fixture,
    commercial, Data Capture, ECR, Cleaning, or Judgment-adjacent decisions.
  trigger: output_authority
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/workflows/orca_repo_map_v0.md"
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
  intentionally_not_updated:
    - path: "AGENTS.md"
      reason: "Root behavior does not enumerate runner-specific read surfaces."
    - path: ".agents/workflow-overlay/README.md"
      reason: "Overlay routing owners are unchanged."
    - path: ".agents/workflow-overlay/source-of-truth.md"
      reason: "Source hierarchy is unchanged; the runbook owns the operator rule."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-pack budgets are unchanged; this is a Reddit runner read-surface rule."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already routes implementation status to this runbook."
    - path: "docs/workflows/data_capture_spine_consolidation_map_v0.md"
      reason: "Data Capture submap already routes safe capture-tool use to this runbook."
  stale_language_search: >
    rg -n "Before making stripped views the default|stripped_default_for_agent_context|make_stripped_default|reddit_agent_view_stripped|default agent-read surface|full JSON required"
    AGENTS.md .agents/workflow-overlay docs/workflows/orca_repo_map_v0.md
    docs/workflows/data_capture_spine_consolidation_map_v0.md
    forseti-harness/docs/source_capture_agent_runbook.md
  stale_language_search_result: >
    Executed on 2026-06-08 after this patch. Hits were confined to the intended
    Reddit agent-view runbook section and this DCP receipt. No checked downstream
    surface retained stale language saying stripped views are still undecided as
    the default agent-read surface.
  non_claims:
    - not validation
    - not readiness
    - not source completeness proof
    - not canonical evidence replacement
    - not Data Capture handoff
```

## Direction Change Propagation - Agent Read Surface Reframed To Content-Lossless Cleaning

```yaml
direction_change_propagation:
  doctrine_changed: >
    The Reddit agent read-surface rule is reframed: the agent reads a single
    CLEANED view we prepare upstream (after projection, on the projected
    artifact), not a stripped-versus-full toggle. Cleaning is content-lossless --
    it preserves all substantive content and decision-relevant fields and removes
    only worthless noise (repeated provenance, hashes, paths, generated ids,
    score/timestamp cruft, repeated non-claims), giving the agent all the data at
    a fraction of the token/context cost. The verbatim copy is provenance/audit
    only. Dropping any decision-relevant field is a bug, not cleaning, and is
    guarded by regression tests rather than this rule alone.
  trigger: output_authority
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
    - "docs/product/source_capture_toolbox/reddit_capture_operator_playbook_v0.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/workflows/data_capture_spine_consolidation_map_v0.md"
  intentionally_not_updated:
    - path: "forseti-harness/source_capture/reddit_agent_view.py"
      reason: >
        Code still emits the cleaned view as reddit_agent_view_stripped.json via
        the _strip_* functions. This reframe changes the read-surface doctrine and
        docs, not the artifact filenames; a stripped->cleaned code rename is an
        optional later refactor with reference lock-in, not part of this patch.
    - path: "AGENTS.md"
      reason: "Root behavior does not enumerate runner-specific read surfaces."
  non_claims:
    - not validation
    - not readiness
    - not a code rename
    - not source completeness proof
    - not canonical evidence replacement
```

## Direction Change Propagation - Archive Timestamp And Posture Reporting

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now requires agents to preflight Archive.org cutoff timestamps as exact 14-digit YYYYMMDDhhmmss values and to report manifest postures even when limitations are empty."
  trigger: lifecycle_boundary
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/product/source_capture_toolbox/README.md"
    - "forseti-harness/README.md"
  intentionally_not_updated:
    - path: "docs/product/source_capture_toolbox/README.md"
      reason: "Armory component status, adapter boundaries, and deferred gaps did not change."
    - path: "forseti-harness/README.md"
      reason: "It already points agents to this runbook; no new entrypoint or component status changed."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading routes were not changed; this is runner-use guidance inside the existing runbook."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already indexes the armory/runbook path through the harness and product docs; no new durable source family was added."
  stale_language_search: "rg -n \"cutoff-timestamp|YYYYMMDDhhmmss|empty limitations|clean capture|postures\" forseti-harness/docs/source_capture_agent_runbook.md docs/product/source_capture_toolbox/README.md forseti-harness/README.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source completeness"
    - "not source-access boundary amendment"
    - "not adapter implementation"
```

## Direction Change Propagation - Restricted Network Runner Permission

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now tells agents to request per-operation network permission before running live network-backed source-capture runners in restricted sandboxes, and to treat pre-response WinError 10061 as an operational sandbox refusal rather than a source limitation."
  trigger: lifecycle_boundary
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/product/source_capture_toolbox/README.md"
    - "forseti-harness/README.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/workflows/orca_repo_map_v0.md"
  intentionally_not_updated:
    - path: "docs/product/source_capture_toolbox/README.md"
      reason: "The armory component set, adapter boundaries, hard stops, and deferred gaps did not change; it already points to the runbook for agent-facing runner use."
    - path: "forseti-harness/README.md"
      reason: "The harness README already points to the runbook for agent-facing runner selection and report format; detailed sandbox permission sequencing belongs in the runbook."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading routes were not changed; this is runner-use guidance inside the existing runbook."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already indexes the armory implementation and runbook surfaces; no new durable source family or component path was added."
  stale_language_search: "rg -n \"WinError 10061|network permission|restricted sandbox|standing Python|source limitation\" forseti-harness/docs/source_capture_agent_runbook.md docs/product/source_capture_toolbox/README.md forseti-harness/README.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source-access boundary amendment"
    - "not broad standing permission"
    - "not adapter implementation"
    - "not source-quality proof"
```

## Direction Change Propagation - Mini God-Tier Report Block

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now requires agents to include a mini_god_tier_source_quality_report block when an operator commissions a source-quality pass, while leaving result-token vocabulary in the Mini God-Tier profile and row-status vocabulary in the source-unit queue template."
  trigger: output_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
    - "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
    - "docs/product/source_capture_toolbox/README.md"
    - "forseti-harness/README.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/workflows/orca_repo_map_v0.md"
  intentionally_not_updated:
    - path: "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
      reason: "The profile already owns mini god-tier criteria, result tokens, and report-block fields; this runbook patch references that vocabulary without changing it."
    - path: "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
      reason: "The queue template already owns row-status vocabulary; this runbook patch references that vocabulary without changing it."
    - path: "docs/product/source_capture_toolbox/README.md"
      reason: "The README already indexes the profile, queue template, and runbook; no new component or entrypoint was added."
    - path: "forseti-harness/README.md"
      reason: "The harness README already points agents to this runbook for report format; detailed source-quality report fields belong in the runbook."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading routes were not changed; this is report-format guidance inside the existing runbook."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already indexes the armory/runbook path through the harness and product docs; no new durable source family was added."
  stale_language_search: "rg -n \"mini_god_tier_source_quality_report|source_quality_mini_god_tier_profile_v0|source_quality_source_unit_queue_template_v0|operator-commissioned source-quality pass|source-quality scoring|validated|ready|fixture admission|Judgment scoring|Commissioning Gate|Decision Frame|recommended_fixture_admission|separately_admitted\" forseti-harness/docs/source_capture_agent_runbook.md docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md docs/product/source_capture_toolbox/README.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source completeness proof"
    - "not fixture admission"
    - "not source-quality scoring"
    - "not ECR, Cleaning, or Judgment authority"
```

## Direction Change Propagation - Source Quality Report-Skeleton Helper

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now exposes a local Source Quality report-skeleton helper for existing Source Capture Packets; the helper emits conservative operator-completion skeletons and does not finalize result tokens, fetch sources, parse source meaning, admit fixtures, or score source quality."
  trigger: output_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
    - "forseti-harness/README.md"
    - "docs/product/source_capture_toolbox/README.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
    - "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
    - "docs/product/source_capture_toolbox/source_quality_mixed_source_trial_closeout_v0.md"
    - "docs/product/source_capture_toolbox/README.md"
    - "forseti-harness/README.md"
    - "docs/workflows/orca_repo_map_v0.md"
  intentionally_not_updated:
    - path: "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
      reason: "Profile tokens, lifecycle vocabulary, required criteria, and report-block fields did not change."
    - path: "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
      reason: "Queue fields and row-status vocabulary did not change; the helper does not mutate queues."
    - path: "docs/product/source_capture_toolbox/source_quality_mixed_source_trial_closeout_v0.md"
      reason: "The closeout already supplies the helper requirements and remains trial evidence rather than helper API documentation."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading already routes Data Capture source-access tooling through the armory README and runbook; no new read-pack entry is needed."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already indexes the armory and runbook entrypoints; detailed helper command routing belongs in the README/runbook."
  stale_language_search: "rg -n \"run_source_quality_report_skeleton|report-skeleton|mini_god_tier_met|source-quality scoring|validated|ready|fixture admission|Judgment scoring|source discovery|source selection\" forseti-harness/docs/source_capture_agent_runbook.md forseti-harness/README.md docs/product/source_capture_toolbox/README.md docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md docs/product/source_capture_toolbox/source_quality_mixed_source_trial_closeout_v0.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source completeness proof"
    - "not fixture admission"
    - "not source-quality scoring"
    - "not source-access boundary amendment"
    - "not ECR, Cleaning, or Judgment authority"
```

## Direction Change Propagation - Source Quality State Assembler Helper

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now exposes a local read-only Source Quality State Assembler helper for explicit source-quality rows and existing packet manifests; the helper emits a state census and does not run capture tools, discover sources, score source quality, auto-advance queue rows, or finalize mini_god_tier_met."
  trigger: output_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
    - "forseti-harness/README.md"
    - "docs/product/source_capture_toolbox/README.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/product/source_capture_toolbox/source_quality_state_assembler_v0.md"
    - "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
    - "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
    - "docs/product/source_capture_toolbox/README.md"
    - "forseti-harness/README.md"
    - "docs/workflows/orca_repo_map_v0.md"
  intentionally_not_updated:
    - path: "docs/product/source_capture_toolbox/source_quality_state_assembler_v0.md"
      reason: "The architecture boundary already authorizes only a read-only state census over explicit rows and existing packets; implementation follows that boundary without changing it."
    - path: "docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md"
      reason: "Result tokens, criteria, lifecycle states, and finalization ownership did not change."
    - path: "docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md"
      reason: "Queue row fields and row-status vocabulary did not change; the assembler echoes rows and does not mutate queues."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading already routes multi-row state-census questions to the State Assembler architecture boundary."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already indexes the State Assembler architecture and armory entrypoint; detailed helper invocation belongs in the runbook and harness README."
  stale_language_search: "rg -n \"run_source_quality_state_assembler|Source Quality State Assembler|mini_god_tier_met|source-quality scoring|validated|ready|fixture admission|Judgment scoring|source discovery|source selection|runner dispatch|all rows passed|ladder complete\" forseti-harness/docs/source_capture_agent_runbook.md forseti-harness/README.md docs/product/source_capture_toolbox/README.md docs/product/source_capture_toolbox/source_quality_state_assembler_v0.md docs/product/source_capture_toolbox/source_quality_mini_god_tier_profile_v0.md docs/product/source_capture_toolbox/source_quality_source_unit_queue_template_v0.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source completeness proof"
    - "not fixture admission"
    - "not source discovery"
    - "not runner dispatch"
    - "not source acquisition"
    - "not source-quality scoring"
    - "not ECR, Cleaning, or Judgment authority"
```

## Direction Change Propagation - Creator Registry Match Preflight

```yaml
direction_change_propagation:
  doctrine_changed: "The Source Capture Agent Runbook now requires Creator Registry match preflight receipts before starting new social creator/account capture; visual registry/projection scans are orientation only and do not replace the receipt."
  trigger: lifecycle_boundary
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - "forseti-harness/docs/source_capture_agent_runbook.md"
    - "orca/product/spines/capture/core/source_families/social_media/creator_registry/creator_registry_match_preflight_usage_v0.md"
    - "docs/workflows/orca_repo_map_v0.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "forseti-harness/README.md"
    - "orca/product/spines/capture/core/source_capture_toolbox/README.md"
    - "orca/product/spines/capture/core/source_families/social_media/creator_registry/README.md"
    - "docs/workflows/orca_repo_map_v0.md"
  intentionally_not_updated:
    - path: "AGENTS.md"
      reason: "Root instructions do not enumerate source-family preflight details."
    - path: ".agents/workflow-overlay/source-loading.md"
      reason: "Source-loading routes did not change; the existing runbook remains the cold-agent entrypoint."
    - path: "forseti-harness/README.md"
      reason: "It already points agents to this runbook for source-capture runner use."
    - path: "orca/product/spines/capture/core/source_capture_toolbox/README.md"
      reason: "Armory component status and capture-tool boundaries did not change."
    - path: "orca/product/spines/capture/core/source_families/social_media/creator_registry/README.md"
      reason: "Registry architecture and source split did not change; usage-note/runbook binding owns operator sequencing."
  stale_language_search: "rg -n \"Creator Registry match preflight|creator_registry_match_preflight|run_creator_registry_match_preflight|visual registry|projection scan|new social creator\" forseti-harness/docs/source_capture_agent_runbook.md orca/product/spines/capture/core/source_families/social_media/creator_registry/creator_registry_match_preflight_usage_v0.md orca/product/spines/capture/core/source_families/social_media/creator_registry/README.md forseti-harness/README.md orca/product/spines/capture/core/source_capture_toolbox/README.md docs/workflows/orca_repo_map_v0.md"
  stale_language_search_result: >
    Executed 2026-07-04 after edits. Hits are only the new runbook/usage-note/
    repo-map text itself (Required Inputs, Agent Boundary, agent-report
    template, and the runners-index entry) plus this receipt's own quoted
    search string. forseti-harness/README.md, the source_capture_toolbox README,
    and the creator_registry README carry no hits, consistent with the
    intentionally_not_updated reasons above.
  non_claims:
    - "not validation"
    - "not readiness"
    - "not fuzzy duplicate detection"
    - "not cross-platform identity proof"
    - "not silver metric refresh"
    - "not registry mutation"
    - "not live social search"
```
