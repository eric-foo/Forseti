# TikTok UI Movement Blocker Substrate Playbook v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow playbook
scope: >
  Cold-agent map for using Forseti's bounded browser pointer-action substrate on
  TikTok logged-out and live-run UI blockers without converting challenge
  interaction into capture success.
use_when:
  - A TikTok logged-out limit-mapping lane needs to dismiss benign overlays
    while measuring public creator/video/comment access limits.
  - A TikTok live/sessioned lane hits benign overlays, comment-surface routing
    misses, slider/captcha close diagnostics, or visually present controls that
    are not exposed as DOM buttons.
  - A cold agent needs to know which UI movement action is allowed for each
    blocker class before running or patching the live probe.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/source-loading.md
  - .agents/workflow-overlay/safety-rules.md
  - docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md
  - forseti-harness/docs/source_capture_agent_runbook.md
  - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
  - forseti-harness/source_capture/adapters/browser_snapshot.py
  - forseti-harness/source_capture/tiktok/live_batch_probe.py
  - forseti-harness/source_capture/tiktok/blocker_triage.py
  - forseti-harness/tests/unit/test_source_capture_browser_snapshot.py
  - forseti-harness/tests/unit/test_tiktok_live_batch_probe.py
stale_if:
  - `BrowserPagePointerAction`, `_run_pointer_action`, or the visual-X fallback changes materially.
  - `live_batch_probe.py` action names, ordering, stop semantics, or CLI flags change materially.
  - TikTok blocker-triage challenge/auth-wall policy changes materially.
```

## Core Rule

Use the shared pointer-action substrate for TikTok UI movement. Do not hand-roll
ad hoc Playwright clicks in a live lane unless the substrate itself is missing a
needed bounded capability and the patch adds tests plus a receipt.

Known targetability diagnostics are not useful work once pinned. The 2026-07-03
TikTok slider/challenge work produced three durable lessons future lanes must not
re-litigate:

- A benign TikTok teaching/scroll overlay is not the same blocker as the slider /
  captcha / security modal.
- `visual_fallback_geometric_target=true` is only a guessed coordinate; it is not
  proof that an X was detected or clicked. TikTok challenge-close actions must keep
  geometric fallback disabled.
- The latest authoritative live receipt proves a real DOM close target can be
  clicked (`target_kind=button`, `page_text_gate_matched=true`, `clicked=true`),
  but post-click visual candidates remained and the close was not accepted
  (`challenge_close_accepted=false`). Matched comment responses after failed close
  are diagnostic only; admitted count must stay zero.

Future lanes must spend run budget on accepted-close proof and real comment yield,
not on re-proving pointer delivery.

## Cold-Agent Fast Path

For an ordinary sessioned TikTok capture attempt, do not start by re-diagnosing
Chrome, Playwright, or blocker targetability. Use the runbook command for
`run_source_capture_tiktok_live_batch_probe.py` with
`--session-profile chowdakr_sg_tiktok` and local `--admit-output`. The profile
binds the retained-session browser backend, machine-local auth state, required
harness proxy posture, and owner handoff before scripted pointer actions; it
does not enable X/Close. When the profile selects Chrome CDP, the runner requires
exactly one usable loopback endpoint whose root Chrome process was launched with
the configured retained profile; a different live browser endpoint is rejected.
Then classify the result from `tiktok_live_probe_summary_json=` before
opening larger JSON files.

Treat these blocker classes as setup or owner-attention states, not generic
stops:

- onboarding, teaching, `OK`, `Got it`, app, cookie, and continue-in-browser
  prompts are benign setup when no challenge/security marker is present;
- visible `Retry`, `Retry again`, `Try again`, or `Reload` controls are clicked
  once as setup;
- no comments after the first route pass is not terminal until comments ->
  `You may like` / `More like this` -> comments has run, including the bounded
  repeat;
- `platform_challenge_observed` is incomplete by itself. Read `matched_marker`
  and `challenge_kind`; for `slider`/captcha/security cases, attempt only the
  named X/Close follow-through when the lane has enabled the flag;
- if a slider/captcha remains after the allowed X/Close path, use the owner
  handoff when enabled. If no handoff is possible, fail closed. In both cases
  the receipt is owner attention / source-access intervention, not clean
  capture or admission success.

Do not add a human-login-only instruction here. The lane requires dedicated
non-personal accounts and already forbids agent-entered credentials. The
operator-owned login/bootstrap/export mechanics stay in the runbook and auth
state tooling, not in this blocker playbook.

## 2026-07-04 Browser Surface Pin

Cold agents must not collapse all "Chrome" or "Playwright" routes into one
browser surface. The observed surfaces are materially different:

- The Codex Chrome connector can use the owner's existing Chrome profile and
  reached the Funmi fixture comments after the bounded
  comments -> `You may like` -> comments route. It is useful for observation and
  owner-visible diagnosis, but its read-only page scope is not packet-grade:
  it exposed `subtitleInfos` but did not expose `fetch`, and it must not inspect
  or persist cookies, tokens, auth state, raw signed subtitle URLs, or personal
  Chrome profile data.
- The current Playwright `--browser-channel chrome` route launches a new
  Playwright-controlled Chrome context. It is not the owner's already-open Chrome
  session. On 2026-07-04, the same Funmi route exposed the tab controls but
  ended with final `drag the slider` and zero visible comment bodies.
- A visible CloakBrowser route with `humanize=True` on the same fixture completed
  comments -> `You may like` -> comments with no final challenge/security marker
  and 12 visible comment-body nodes in the viewport.
- The post-patch runner receipt
  `tiktok_logged_out_cloakbrowser_probe_20260704_02` completed logged-out with
  `completed_count=1`, `challenge_count=0`, one admitted page-owned
  `/api/comment/list/` response, 20 assessed comments, no human handoff attempt,
  and no transcript capture because the subtitle host was rejected by the live
  probe allowlist.

Use this historical logged-out pin as routing evidence, not admission evidence.
That run's surface was `--browser-backend cloakbrowser`; do not combine it with
`--browser-channel`. A validated session profile may bind the distinct retained
Chrome CDP surface without making it a diagnostic run.
For TikTok slider/captcha handoff, `--human-challenge-handoff` fires at
page load before scripted pointer actions. If the marker remains after the owner
handoff window, the runner suppresses those actions and fails closed. The
`chowdakr_sg_tiktok` profile enables this policy without enabling X/Close.
Any manual solve is source-access intervention in the receipt, not clean
capture. CloakBrowser `0.4.7` removed the old `backend=` launch argument;
adapter smoke-test `--browser-backend cloakbrowser` after wrapper upgrades before
spending TikTok probe budget. This does not prove cross-creator durability,
page-owned `/api/comment/list` response capture, subtitle transcript capture
across creators, account safety at volume, or creator-registry promotion.

Current owner default: use `--session-profile chowdakr_sg_tiktok`. A visible
slider/captcha/security marker triggers owner handoff before scripted pointer
actions; the agent does not close, drag, or solve it, and uncleared markers
suppress the remaining action sequence. Do not add
`--allow-diagnostic-browser-backend` to make the profile work; a profile-bound
Chrome CDP route must pass its own retained-profile process-binding and
loopback-endpoint checks.

The explicit X/Close route remains available only when the current lane
separately uses `--allow-challenge-close-followthrough`. The runner
may attempt the X/Close control, then attempt the page-owned comment route only
if post-click verification proves the close was accepted. `clicked=true` means
only that a pointer click was delivered; accepted follow-through requires
challenge/security text absence and centered visual-X absence on the action-level
after-click receipt, with `post_click_visual_target_absent=true` only when no
post-click visual X candidates remain. Final blocker triage must still report no
challenge/security marker. If final triage still sees `drag the slider`, `verify
to continue`, `captcha`, or equivalent challenge/security text,
`challenge_close_accepted=false` even when earlier click-delivery fields are true.
This is not CAPTCHA solving, not puzzle dragging, and not an unchallenged clean
route. It is an owner-authorized source-access intervention
that must be preserved in the receipt and batch payload. Continue only if the
rendered page no longer shows challenge/security text, the close receipt has
`challenge_close_accepted=true`, and either at least one page-owned
`/api/comment/list` response is captured or bounded DOM-visible comment
candidates are captured after the named comments -> `You may like` / `More
like this` -> comments route, including the bounded second route pass when the
first pass yields zero comments. DOM-visible comments are lower-tier `captured_visible_dom` evidence, not
page-owned response evidence; count-only/tab text such as `303`, `1.2K comments`,
`Comments`, or `Log in to comment` is not a comment body and cannot admit. If the
final visual close follow-through fails post-click verification, the pointer
sequence must stop before comment-route
actions; failed-close receipts must not carry `challenge_close_followthrough=true`
or label the close action as `comment_action`. A `visual_fallback_geometric_target=true`
receipt is a coordinate guess, not proof that an X was detected or clicked, and
must not be cited as X-click evidence. If the challenge marker remains,
close acceptance is false/missing, and neither response yield nor DOM-visible
comment yield is present, stop visibly. The older
`--allow-challenge-close-diagnostic` flag remains diagnosis-only and still forces
stop.

The substrate is:

- `BrowserPagePointerAction` in `forseti-harness/source_capture/adapters/browser_snapshot.py`.
- `_run_pointer_action(...)` in the same file.
- Movement execution via `page.mouse.move(..., steps=...)` followed by
  `page.mouse.click(...)`, with randomized bounded target fractions and step
  counts from the action config.
- Sanitized receipts under `metadata.post_load_pointer_actions`; receipts must
  not include raw cookie/storage contents, raw endpoint URLs, or raw response
  bodies.

## Blocker Map

| Blocker / UI state | Action substrate | Allowed in clean run? | Success semantics |
| --- | --- | --- | --- |
| Benign TikTok onboarding/app prompt such as `Got it`, `OK`, `Not now`, `Continue in browser` | `tiktok_dismiss_benign_overlay_pointer_v0` | Yes | Setup action only; excluded from comment-action count; `OK` is matched as an exact button/control target, not as a broad page-text blocker marker. |
| Logged-out login upsell modal with a dismiss/close control and no challenge/security text | `tiktok_dismiss_benign_overlay_pointer_v0` or a named logged-out dismiss action if added later | Yes for logged-out limit mapping only | Setup action only; record the receipt and continue measuring public access. Do not enter credentials. |
| Comment surface does not load comments until tab shuffle | `comment_surface_toggle_pointer_sequence_v0`: `tiktok_open_comments_pointer_v0` -> `tiktok_open_more_like_this_pointer_v0` (`You may like` / `More like this`) -> `tiktok_reopen_comments_pointer_v0`, repeated once before zero-yield classification | Yes | Clean response-tier capture if at least one page-owned `/api/comment/list` response is admitted; lower-tier fallback if bounded DOM-visible comment candidates are captured after the route. First-pass zero response is not terminal; zero response and zero DOM-visible candidates after the repeated bounded route remains zero evidence, not success. |
| Visible slider/captcha under `chowdakr_sg_tiktok` | `human_challenge_handoff_v0` at `page_load_before_pointer_actions_v0` | Owner-only source-access intervention; never clean by itself | Keep the browser open and prompt the owner before any scripted pointer action. Continue only when the marker clears; otherwise record the handoff and suppress the pointer-action sequence. |
| DOM-exposed slider/captcha close control | `tiktok_challenge_modal_close_followthrough_pointer_v0` for follow-through; `tiktok_challenge_modal_close_diagnostic_pointer_v0` for diagnosis | Yes only with `--allow-challenge-close-followthrough`; diagnostic flag remains stop-only | Attempt X/Close, do not solve/drag, then continue only if post-click verification plus final blocker triage accepts the close (`challenge_close_accepted=true`) and page-owned comments or DOM-visible comment candidates are captured; carry `source_access_intervention`. |
| Screenshot-visible but DOM-invisible slider/captcha X | `tiktok_challenge_modal_visual_close_followthrough_pointer_v0` for follow-through; `tiktok_challenge_modal_visual_close_diagnostic_pointer_v0` for diagnosis | Yes only with `--allow-challenge-close-followthrough`; diagnostic visual-X remains visible-challenge-text gated and stop-only | Follow-through visual-X may run before comment routing even when TikTok exposes the challenge marker only as hidden/residual DOM text. Continue only if post-click text/visual verification plus final blocker triage accepts the close and page-owned comments or DOM-visible comment candidates are captured, with the intervention preserved. |
| Slider/captcha puzzle itself | None | Never | Do not drag, solve, or attempt puzzle interaction. |
| Login/auth wall redirect, credential prompt, or account risk wall | None unless separately mapped as benign logged-out upsell | Never by default | Stop and report blocker. Do not enter credentials or manipulate account state. |
| Unknown dismiss/reload blocker | None until mapped | No | Stop or patch a named substrate action with tests; do not generic-click around blockers. |

Do not collapse TikTok's benign new-user education / scroll prompt into the
slider/captcha blocker class. A scroll/onboarding prompt is benign-overlay
dismissal when it has no challenge/security marker. The slider/captcha blocker
is the modal whose copy includes markers such as `Drag the slider to fit the
puzzle`; its only authorized follow-through target is the modal's internal
X/Close control, never the puzzle, browser tab, or browser/window close chrome.
TikTok challenge visual-X actions use the `center_modal` visual target zone so
they prefer the centered captcha modal close control over unrelated far
top-right page controls.
When no centered X component is detected, the same target zone may use a
bounded geometric center-modal close estimate and record
`visual_fallback_geometric_target=true`.

## Logged-Out Limit-Mapping Mode

Logged-out runs are allowed to measure TikTok's public creator/video/comment
surface limits before any sessioned retry. They must use the same pointer-action
substrate and receipts.

Allowed logged-out movement:

- dismiss benign onboarding, app, cookie, continue-in-browser, and login-upsell
  overlays when they expose a close/dismiss control and no challenge/security
  marker;
- open comments through the named comment-surface route action;
- capture public stats and comment bodies only through the armory runner/output
  path chosen for the lane, without pagination unless the current owner
  explicitly authorizes it.

Not allowed in logged-out capture:

- dragging, solving, or interacting with slider/captcha puzzles;
- treating a slider/captcha X click by itself as capture success;
- entering credentials, preserving auth state, or upgrading to a sessioned run
  without a fresh owner gate;
- repeating targetability diagnostics after the same challenge/security X has
  already been pinned.

If a logged-out run hits a closeable login upsell, dismiss once and continue. If
it hits an X-able public slider/captcha/security modal and the current owner has
authorized follow-through, use `--allow-challenge-close-followthrough` once and
continue only when `challenge_close_accepted=true` includes no final challenge/security
triage marker and there is post-close page-owned comment response yield or DOM-visible
comment candidate yield. If
follow-through is not authorized, if close acceptance is unproven, or if the
challenge remains after the close click, stop and record the blocker state. Do
not run a close diagnostic merely to re-prove X targetability.

## Cold-Agent Blocker Taxonomy

Use these classes before naming a TikTok state as a stop condition:

- `benign_overlay`: teaching, scroll, app, cookie, `OK`, `Got it`, `Not now`, or
  continue-in-browser prompts with no challenge/security marker. Use
  `tiktok_dismiss_benign_overlay_pointer_v0`; this is setup, not admission.
- `retry_visible_error`: visible `Retry`, `Retry again`, `Try again`, or `Reload`
  controls. Use `tiktok_retry_visible_error_pointer_v0` once before treating the
  page as failed; this is setup, not admission.
- `comment_route_zero_yield`: no admitted page-owned comment response and no
  DOM-visible comment-body candidate after the full bounded route. This is only
  valid after the runner has attempted comments -> `You may like` / `More like
  this` -> comments, repeated once. A first zero response is not terminal.
- `challenge_or_security`: visible or final-triage challenge/security text such
  as `drag the slider`, `verify to continue`, `captcha`, or `security check`.
  If follow-through is owner-authorized, click only the X/Close control through
  the named pointer-action substrate. Never drag or solve the puzzle.
- `challenge_close_not_accepted`: an X/Close pointer click was delivered, but
  post-click visual candidates remain, challenge/security text remains, or final
  triage still sees the challenge. This is a real stop with zero admission even
  when a `/api/comment/list` response was observed.
- `login_or_auth_wall`: login redirect, credential prompt, account-risk wall, or
  auth wall. Stop unless a separate owner-gated sessioned lane has been loaded;
  never enter credentials in this lane.

For classification, do not stop at the top-level reason string. Inspect
`blocker_triage.blocker_class`, `matched_marker`, `challenge_kind`,
`comment_action.sequence_name`, `comment_action.action_sequence[*].action_name`,
`pointer_action_chronology[*].action_name`, `challenge_close_attempts[*]`, and the post-click visual counts (`post_click_visual_candidate_count`, `post_click_visual_zone_candidate_count`) when present.
`platform_challenge_observed` must break down into at least marker and kind;
`drag the slider` maps to `challenge_kind=slider`. The filtered
`comment_action` field intentionally omits retry, benign overlay, and
challenge-close actions; use `pointer_action_chronology` for exact chronology.

## Cold-Agent Procedure

1. Load the active handoff and this playbook. Re-read the current
   `browser_snapshot.py`, `live_batch_probe.py`, and `blocker_triage.py` before
   making strict claims.
2. From `forseti-harness/`, preflight the default live/sessioned route before
   browser action: `python runners/check_source_capture_session_profile.py --session-profile
   chowdakr_sg_tiktok`. Continue only when the sanitized receipt reports
   `status=available`, `auth_state_validated=true`, and
   `secret_values_exposed=false`. Invoke the live runner with
   `--session-profile chowdakr_sg_tiktok`; do not combine it with manual
   session, browser, proxy-posture, or challenge-policy flags, and do not copy
   the stable machine-local auth state into the worktree. Use logged-out limit
   mapping only when explicitly selected: no auth state, no credential entry,
   benign dismissals allowed, and challenge/security stops.
3. For an unchallenged route-yield gate, run without challenge-close flags. The
   runner may press visible retry controls, dismiss benign overlays, and perform
   comments -> `You may like` / `More like this` -> comments twice before
   treating zero response plus zero DOM-visible candidates as zero evidence.
4. If the current owner authorizes X-able challenge follow-through, run with
   `--allow-challenge-close-followthrough`. The runner uses only named pointer
   actions: it attempts challenge X/Close controls and the bounded comments ->
   `You may like` / `More like this` -> comments route, with close attempts
   interleaved after route clicks when configured. Continue only if the first
   video has `completed_count=1`, `challenge_count=0`, no failures, and either
   `admitted_comment_response_count >= 1` or
   `dom_visible_comment_candidate_count >= 1`. Any close action must be
   preserved as `challenge_close_action` / `source_access_intervention`.
5. If the owner explicitly authorizes challenge-close diagnosis instead, run with
   `--allow-challenge-close-diagnostic`. A DOM close click or visual-X close click
   must stop the run and must not admit, expand, or claim capture success. The
   diagnostic path is retained only for changed-condition checks.
6. Scan the runner's `tiktok_live_probe_summary_json=` lines before opening
   larger JSON files. `stage=staging` distinguishes `staging_complete`,
   `owner_attention_required`, and `fail_closed_*`; `stage=admission`
   distinguishes `local_packet_admitted`, `bronze_packet_admitted`, and
   `fail_closed_admission_*`. A manual slider/captcha handoff is owner attention
   and source-access intervention, not clean capture.
7. Scan outputs for forbidden markers before any admission claim. Auth-state files
   copied for a legacy manual-state run must be removed and verified absent
   after the run; machine-local state resolved by a session profile is not a
   worktree copy and must not be deleted by cleanup. When the owner asks for a
   packet or bronze/data-lake write, prefer the live
   runner's own `--admit-output` or explicit `--data-root` chain so staging feeds
   the existing TikTok batch admission gate directly; do not hand-copy staging
   JSON into a packet. Batch admission is code-gated to reject challenge/
   diagnostic cadence: nonzero `challenge_count`, non-empty `failures`,
   `first_failure_reason`, `captcha_solving=true`,
   `challenge_close_counts_as_success=true`, or
   `challenge_close_diagnostic_allowed=true` cannot be admitted.

## Receipt Fields To Inspect

For benign overlay:

- `capture_receipt.benign_overlay_action.action_name`
- `target_found`, `clicked`, `candidate_count`, `matched_count`, `wait_ms`

For comment routing:

- `pointer_action_chronology[*].action_name=tiktok_retry_visible_error_pointer_v0` when a visible retry control was clicked
- `capture_receipt.comment_action.sequence_name`
- `action_count`
- `action_sequence[*].action_name`
- `clicked_all_targets`
- `admitted_comment_response_count`
- `dom_visible_comment_candidate_count`
- `comment_capture_fallback`

For challenge-close diagnostics:

- `capture_receipt.challenge_close_action.action_name` for follow-through rows
- `blocker_triage.challenge_close_diagnostic.action_name` for diagnostic stops
- `target_found`, `clicked`, `target_kind`, `selection_strategy`
- visual-only fields: `visual_fallback_attempted`,
  `visual_fallback_target_found`, `visual_fallback_candidate_count`,
  `visual_fallback_zone_candidate_count`, `visual_fallback_confidence`,
  `visual_fallback_crop_box`,
  `visual_fallback_screenshot_sha256`, `visual_fallback_target_zone`,
  `visual_fallback_geometric_target`,
  `target_box`, `click_point`
- close-acceptance fields: `challenge_close_accepted`,
  `post_click_absence_verified`, `post_click_absence_matched_marker`,
  `post_click_visual_target_absent`, `post_click_visual_candidate_count`,
  `post_click_visual_zone_candidate_count`, `post_click_visual_screenshot_sha256`

A clicked diagnostic receipt is evidence that a pointer click was delivered to a
candidate close target; it is not capture success and does not prove the modal
closed. A follow-through receipt is admissible only when the action-level post-click
checks satisfy the current close-acceptance predicate (`challenge_close_accepted=true`)
and final blocker triage still reports no challenge/security marker. The zone
candidate counts are diagnostic: `post_click_visual_zone_candidate_count=0` can
show the centered modal X disappeared, but it does not override
`post_click_visual_target_absent=false` or a final `drag the slider` marker.
The capture claim then comes only from post-close page-owned comment response
evidence or lower-tier DOM-visible comment fallback evidence in the sanitized
admission payload. For the current TikTok slider/challenge X, close-targeting is
already pinned and should not be re-diagnosed; close acceptance is the material
receipt field.

## Patch Rule For New Blockers

If a new blocker needs UI movement:

1. Add a named `BrowserPagePointerAction` config, not an inline click.
2. Gate it by visible page text or by an explicit diagnostic flag when it touches
   challenge/auth-risk UI.
3. Preserve sanitized receipt fields that explain what was attempted and why.
4. Add unit tests in `test_source_capture_browser_snapshot.py` for substrate
   behavior and `test_tiktok_live_batch_probe.py` for TikTok ordering/stop
   semantics.
5. Update this playbook and the active handoff.

Never add a path where closing or dismissing a challenge can produce a completed
capture row, admission, batch expansion, product extraction, or success claim.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok challenge-close acceptance now fails closed when final blocker triage
    still sees challenge/security text, even if the action-level immediate
    post-click absence checks were true; action-level fields remain observations,
    not sufficient acceptance by themselves.
  trigger: workflow_authority
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    - docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
    - docs/workflows/tiktok_logged_out_followthrough_live_receipt_v0.md
    - orca-harness/source_capture/tiktok/live_batch_probe.py
    - orca-harness/tests/unit/test_tiktok_live_batch_probe.py
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/safety-rules.md
    - orca/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  stale_language_search: >
    rg -n "post-click receipt checks|challenge_close_accepted|final blocker triage|drag the slider"
    docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
    docs/workflows/tiktok_logged_out_followthrough_live_receipt_v0.md
  stale_language_search_result: >
    Executed 2026-07-03 after edits. Remaining hits are intentional: acceptance
    requires both action-level post-click absence checks and no final challenge
    marker; historical live receipts that predate the patch are explicitly
    labeled as overclaiming acceptance when final triage still saw `drag the slider`;
    the older DCP block below is historical and superseded by this one.
  non_claims:
    - not validation
    - not readiness
    - not capture success
    - not authorization to solve or drag CAPTCHA/slider challenges
```

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok lanes now treat owner-authorized X-able public challenge modals as
    close-follow-through access interventions rather than hard blockers only
    when post-click receipt checks prove close acceptance; bounded DOM-visible
    comment candidates remain lower-tier fallback evidence after the named
    comments route, while retaining no-solve/no-drag limits, diagnostic-only
    stop mode, post-close challenge-text stop behavior, and receipt-visible
    source-tier labels.
  trigger: workflow_authority
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    - docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
    - orca-harness/source_capture/adapters/browser_snapshot.py
    - orca-harness/source_capture/tiktok/live_batch_probe.py
    - orca-harness/source_capture/tiktok/batch_packet.py
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/safety-rules.md
    - orca/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/safety-rules.md
      reason: >
        The external source-data capture rule already routes captures through
        the Source Capture Armory Runner Ladder; this playbook only narrows
        TikTok UI movement and source-tier admission behavior.
    - path: orca/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md
      reason: >
        This patch changes the TikTok runner/playbook lane mechanics for an
        owner-authorized source route; the broader source-access boundary already
        forbids credential/session leakage, direct forged APIs, and CAPTCHA
        solving.
    - path: orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
      reason: >
        Current execution lanes load this playbook and handoff for the updated
        route gate; the capture-lane spec remains a broader boundary and was not
        needed to encode the DOM-visible fallback mechanics.
    - path: orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md
      reason: >
        Current execution lanes load this playbook and handoff for the updated
        route gate; the warm-probe plan remains a broader account/session posture
        source and was not needed to encode the logged-out DOM-visible fallback.
  stale_language_search: >
    rg -n "proven.*close|closeability|re-prove X close|clicked=true|challenge_close_accepted|post_click"
    docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
  stale_language_search_result: >
    Executed 2026-07-03 after edits. No stale "proven closeable" or
    "closeability" claims remained. Hits for `clicked=true`,
    `challenge_close_accepted`, and `post_click` are intentional negative-proof
    language or historical diagnostic receipt facts paired with explicit "not
    close proof" wording.
  non_claims:
    - not validation
    - not readiness
    - not capture success
    - not authorization to solve or bypass CAPTCHA/slider challenges
```

Older receipts for this file live verbatim in `docs/decisions/dcp_receipts_archive_v0.md`.
