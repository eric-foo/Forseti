# TikTok Cold-Agent Capture Enforcement Goal v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow goal and implementation batching record
scope: >
  Reference goal, code-enforcement batches, and doctrine split for making cold
  agents able to run TikTok capture with low-latency blocker handling, source-access
  provenance, no raw secrets, and honest admission boundaries.
use_when:
  - Planning or implementing TikTok cold-agent capture hardening.
  - Deciding whether a TikTok blocker rule belongs in code or doctrine.
  - Preparing fused implementation batches for the TikTok live runner and admission path.
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/source-loading.md
  - .agents/workflow-overlay/decision-routing.md
  - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
  - docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md
  - forseti-harness/docs/source_capture_agent_runbook.md
  - docs/review-outputs/tiktok_capture_enforcement_batches_1_4_post_adjudication_delegated_adversarial_code_review_v0.md
  - forseti-harness/runners/run_source_capture_tiktok_live_batch_probe.py
  - forseti-harness/source_capture/tiktok/live_batch_probe.py
  - forseti-harness/source_capture/tiktok/blocker_triage.py
  - forseti-harness/source_capture/source_access_provenance.py
branch_or_commit: PR #709 / codex/tiktok-session-provenance-implementation; use the containing commit for this document, with implementation review target fb078dd08539c1392002dc0ca145a41a02656ddc.
stale_if:
  - PR #709 is merged, closed, or rebased without this document being checked against the final branch head.
  - The TikTok live runner, blocker triage, admission gate, or source-access provenance schema changes.
  - The owner changes no-secret, no-solve, owner-attention, or bronze-write policy.
  - A later TikTok probe proves a different browser/backend route is the packet-grade path.
authority_boundary: retrieval_only
```

## Orca Start Preflight

```yaml
orca_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom
  edit_permission: docs-write now; implementation-authorized only for later fused batches after their gates clear
  target_scope: workflow_authority plus validation_philosophy for TikTok cold-agent capture hardening
  dirty_state_checked: yes
  blocked_if_missing: blocker playbook, provenance ADR, TikTok lane spec, live runner, blocker triage, source-access provenance source
```

## Goal Establishing

Long-term goal: cold agents should be able to access and capture public TikTok creator/video/comment/subtitle evidence through the sanctioned Orca harness route without re-diagnosing known blockers, leaking secrets, or overclaiming source-access posture.

Anchor goal: convert the known TikTok cold-agent failure modes into deterministic runner/admission behavior where the machine can decide setup action, owner-attention, admissible capture, or fail-closed stop from flags and sanitized receipts.

Success signal:

- Core success:
  - Owner-observable: a cold agent can load one goal/playbook surface, run the sanctioned TikTok runner with a warmed dedicated session, and see a clear proceed/setup-click/owner-attention/admit/fail-closed outcome.
  - Output fit: future implementation batches should make fewer decisions depend on model memory; code should own mechanically checkable route, blocker, provenance, and admission gates.
  - Boundary: success is not a live capture guarantee, scale proof, account-safety proof, full-network no-proxy proof, CAPTCHA-solving authorization, or creator-registry promotion.
  - Drift cue: the work is drifting if it adds more prose reminders without moving a mechanically checkable blocker or admission rule into code.
- Secondary success signals:
  - The first controlled sessioned probe can resolve `chowdakr_sg_tiktok` to its configured retained-session browser and required harness proxy posture, select one usable loopback browser endpoint whose root Chrome process was launched with the configured retained profile when Chrome CDP is selected, then use named blocker actions and local `--admit-output` before any bronze write.
  - A failed close, unsupported subtitle host, missing provenance sidecar, or owner-attention condition stops with a typed reason that future agents can act on.

```yaml
goal_handoff:
  long_term_goal: Cold agents should be able to access and capture public TikTok creator/video/comment/subtitle evidence through the sanctioned Orca harness route without re-diagnosing known blockers, leaking secrets, or overclaiming source-access posture.
  anchor_goal: Convert the known TikTok cold-agent failure modes into deterministic runner/admission behavior where the machine can decide setup action, owner-attention, admissible capture, or fail-closed stop from flags and sanitized receipts.
  success_signal:
    core_success:
      owner_observable: A cold agent can load one goal/playbook surface, run the sanctioned TikTok runner with a warmed dedicated session, and see a clear proceed/setup-click/owner-attention/admit/fail-closed outcome.
      output_fit: Future implementation batches should make fewer decisions depend on model memory; code should own mechanically checkable route, blocker, provenance, and admission gates.
      boundary: Not live capture guarantee, scale proof, account-safety proof, full-network no-proxy proof, CAPTCHA-solving authorization, or creator-registry promotion.
      drift_cue: The work is drifting if it adds more prose reminders without moving a mechanically checkable blocker or admission rule into code.
    secondary_success_signals:
      - First controlled sessioned probe can resolve chowdakr_sg_tiktok to its configured retained-session browser and required harness proxy posture, select one usable loopback browser endpoint whose root Chrome process was launched with the configured retained profile when Chrome CDP is selected, then use named blocker actions and local admit-output before bronze.
      - Failed close, unsupported subtitle host, missing provenance sidecar, or owner-attention condition stops with a typed reason future agents can act on.
  status: user_stated
thread_operating_target:
  activation_policy: latest_non_blocked_goal_frame_wins
  lifecycle_status: active_thread_local
  optimize_toward: goal_handoff.anchor_goal
  output_fit_check: goal_handoff.success_signal.core_success.output_fit
  target_delta_from_prior:
    status: changed
    changed_fields: [anchor_goal, success_signal]
    summary: The active target now emphasizes code-enforced cold-agent behavior before more handoff/probe work.
  drift_guard: Do not substitute another prose-only handoff for deterministic TikTok runner/admission enforcement where the rule is mechanically checkable.
  conflict_behavior: call_out_conflict_before_proceeding
```

## Cold-Agent Operating Contract

If a future agent is asked to run TikTok capture, start here, then open the
playbook and runbook named in `open_next`. Do not reconstruct the route from
older handoffs.

Use the sanctioned one-fixture path:

1. Use `--session-profile chowdakr_sg_tiktok` with the TikTok
   one-creator live runner. The machine-local profile binds the dedicated
   auth-state label, configured session mode and required harness proxy posture,
   retained-session browser backend, and pre-action owner handoff. A profile-bound
   Chrome CDP route must also prove a nonempty retained profile and exactly one
   usable loopback endpoint whose root Chrome process was launched with that
   profile before capture; it is not a diagnostic downgrade.
2. Run `check_source_capture_session_profile.py --session-profile
   chowdakr_sg_tiktok` when cold-start availability is uncertain. Missing,
   invalid, or provenance-mismatched profile state blocks before browser launch;
   never downgrade to logged-out capture.
3. Treat the bound required-posture value as harness proxy-profile
   posture only, not full-network no-proxy proof.
4. On a visible slider/captcha, prompt the owner before any scripted pointer
   action. Continue only after the marker clears; otherwise suppress scripted
   actions and fail closed. X/Close follow-through remains a separate explicit
   route and is not enabled by `chowdakr_sg_tiktok`. The runner never drags or
   solves slider/captcha puzzles.
5. Prefer local `--admit-output` first. Use explicit `--data-root` only when the
   owner asks for immediate bronze/data-lake admission.
6. Read `tiktok_live_probe_summary_json=` before opening larger JSON. It tells
   the cold agent whether the run stopped at staging, owner attention,
   fail-closed admission, local packet admission, or bronze admission.

Known blockers are not all terminal:

- intro/teaching/OK/Got-it/app prompts are benign setup actions;
- Retry/Try again/Reload is clicked once as setup;
- first-pass no-comments is not terminal until comments -> `You may like` /
  `More like this` -> comments has run, including the bounded repeat;
- `platform_challenge_observed` must be read with `matched_marker` and
  `challenge_kind`; an X-able slider/captcha may attempt only X/Close when
  follow-through is authorized;
- if slider/captcha remains, hand off to the owner when possible; otherwise fail
  closed. Owner/manual intervention is source-access intervention and never
  clean capture.

Code enforcement for BATCH-01 through BATCH-04 is implemented on PR #709 and
was cross-vendor reviewed in
`docs/review-outputs/tiktok_capture_enforcement_batches_1_4_post_adjudication_delegated_adversarial_code_review_v0.md`
with recommendation `keep` and `patches_applied: 0`. The review is decision
input, not validation, readiness, live TikTok success, account-safety proof,
full-network no-proxy proof, CAPTCHA bypass, scale proof, or merge authority.

## Code-Enforced Findings

These belong in deterministic runner, blocker-triage, provenance, receipt, test, or admission code. A cold agent should not need to remember them.

1. **Packet-grade TikTok route posture.** The sanctioned packet-grade route should be explicit and hard to misuse: logged-out or manually configured live capture defaults to `--browser-backend cloakbrowser`; a validated `--session-profile` may instead bind the retained Chrome CDP backend. Chrome CDP requires a nonempty retained profile and exactly one usable loopback endpoint whose root Chrome process was launched with that profile before capture. Manual non-CloakBrowser selection remains diagnostic-only, and `--browser-channel` remains incompatible with CloakBrowser.
2. **Session provenance gate.** A sessioned run that requests posture must validate local auth-state sidecar provenance before browser launch. A label containing `noproxy` never clears the gate by itself.
3. **Harness proxy-posture vocabulary.** Code may require `no_proxy_profile_loaded` or `proxy_profile_loaded`; it must not expose that as full-network no-proxy proof.
4. **Secret scan.** Sidecars, packets, staging, receipts, docs, and admission payloads must reject raw cookies, storage-state contents, tokens, proxy endpoints, exit IPs, profile paths, device identifiers, and raw signed URLs.
5. **Benign overlay setup.** TikTok onboarding, teaching, `OK`, `Got it`, app, cookie, or continue-in-browser prompts without challenge/security markers are setup actions through named pointer actions, not terminal blockers.
6. **Visible retry setup.** `Retry`, `Retry again`, `Try again`, or `Reload` controls should be clicked once through a named pointer action before classifying failure.
7. **Comment route zero-yield.** `no_challenge_but_no_comments` is not terminal until the full comments -> `You may like` / `More like this` -> comments route has run, including the bounded second route pass when configured.
8. **Challenge breakdown.** `platform_challenge_observed` must break down into marker, kind, and receipt fields. Slider/captcha/security/auth-wall should not collapse into one undifferentiated stop string.
9. **X-able challenge follow-through.** When follow-through is authorized, code clicks only the modal X/Close through the named pointer-action substrate. It never drags or solves a puzzle.
10. **Close acceptance gate.** `clicked=true` means pointer delivery only. Admission requires close acceptance plus no final challenge/security triage marker. Failed close means zero admission even if comment traffic appears.
11. **Owner-attention state.** If a slider/captcha remains and manual solve is the only possible continuation, the runner should produce an owner-attention state or prompt when possible. If owner-attention/prompting is not available, it must fail closed with a typed reason rather than solving or pretending capture success.
12. **Human handoff receipt boundary.** Any owner/manual intervention is source-access intervention in receipts. It is not clean capture and must not silently satisfy clean-route assertions.
13. **Admission chaining.** Cold agents should use runner-owned `--admit-output` or explicit `--data-root` only. Hand-copying staging JSON into packets should remain out of the path.
14. **Admission fail-closed contract.** Nonzero challenge count, failures, first-failure reason, diagnostic close, challenge-close-as-success, captcha-solving markers, forbidden secret material, or missing source provenance when required must reject before packet/lake write.
15. **Subtitle/transcript capture.** Source-native captions should be captured only through explicit allowlisted subtitle hosts and sanitized WebVTT/cue payloads. Unsupported hosts should stop or mark a typed non-capture reason; raw signed subtitle URLs/bodies must not persist.
16. **Receipt inspectability.** The runner should preserve enough sanitized fields for a cold agent to classify: blocker class, matched marker, challenge kind, retry/benign/comment action chronology, close attempts, close accepted/not accepted, owner-attention state, admitted response count, DOM fallback count, subtitle status, provenance requirement status.

## Doctrine-Only Findings

These remain prose because they explain intent, risk, or interpretation rather than a deterministic runtime decision.

1. **Dedicated-account risk posture.** TikTok sessioned capture uses dedicated non-personal accounts and accepts burnable-account risk for that lane. The goal doc does not repeat human-login-only mechanics; agents already must not enter credentials.
2. **No full-network no-proxy claim.** `no_proxy_profile_loaded` means the harness did not load a proxy profile. It does not prove OS, VPN, corporate, ISP, or upstream egress state.
3. **Owner-attention preference.** If manual CAPTCHA/slider action becomes the only continuation, ping/hand off to the owner when possible; if not possible, fail closed. This is not permission to automate solving.
4. **Chrome connector boundary.** Owner Chrome may help observe UI and login state, but it is not packet-grade unless it can produce the same durable sanitized response receipts and no-secret guarantees.
5. **Playwright diagnostic boundary.** A manually selected Playwright/Chrome launch remains diagnostic-only. That is distinct from a profile-bound Chrome CDP engine that attaches to the validated retained session and preserves the packet-grade response and admission path.
6. **Manual intervention interpretation.** Owner/manual solve can support source-access diagnosis or a clearly labeled intervention receipt; it is not unchallenged clean capture.
7. **One probe is not scale.** One successful fixture does not prove cross-creator durability, account safety, platform stability, or promotion readiness.
8. **Transcript interpretation.** TikTok subtitles are source-native subtitle evidence when present; not owner-generated ASR and not platform-wide transcript coverage.
9. **Bronze caution.** Prefer local `--admit-output` before data-lake `--data-root` unless the owner explicitly wants immediate bronze.

## Implementation Batches

Batches are intentionally materially large enough to reduce repeated cold-agent failures, but small enough to validate and review.

### BATCH-01 - Runner Posture, Provenance Preflight, And Owner-Attention Skeleton

Purpose: make the runner hard to invoke in the wrong TikTok capture posture and make pre-browser failures explicit.

Code scope:

- `forseti-harness/runners/run_source_capture_tiktok_live_batch_probe.py`
- `forseti-harness/source_capture/tiktok/live_batch_probe.py`
- `forseti-harness/source_capture/source_access_provenance.py` only if needed for exported helper messages
- focused tests in `forseti-harness/tests/unit/test_tiktok_live_batch_probe.py` and `forseti-harness/tests/unit/test_source_capture_authenticated_browser_snapshot.py`

Expected behavior:

- Resolve the machine-local `chowdakr_sg_tiktok` profile before browser launch; bind CloakBrowser, auth-state label, session mode, required proxy posture, and challenge policy without exposing secret paths or values.
- Keep a diagnostic route possible, but require explicit diagnostic intent when using non-CloakBrowser backend for TikTok.
- Fail closed with `BLOCKED_SESSION_PROFILE_UNAVAILABLE` for missing/invalid profile configuration or missing/legacy/mismatched auth-state provenance; never downgrade to logged-out capture.
- Prompt for owner attention at page load before scripted pointer actions. If the visible challenge does not clear, suppress those actions and preserve owner-attention/source-access-intervention receipt state.
- Preserve current no-solve/no-drag behavior, no-secret sidecar rules, and explicit-only X/Close follow-through.

Validation target:

- Unit tests that non-CloakBrowser packet-grade invocation is rejected or explicitly diagnostic.
- Unit tests that required harness proxy posture rejects before browser launch on legacy/missing/mismatched sidecar.
- Unit tests that owner-attention state is emitted/handled without classifying as clean capture.
- Existing provenance and live-runner tests remain green.

### BATCH-02 - Blocker State Machine And Low-Latency Setup Actions

Purpose: move the known cold-agent blocker taxonomy from memory/prose into deterministic triage and action sequencing.

Code scope:

- `forseti-harness/source_capture/tiktok/blocker_triage.py`
- `forseti-harness/source_capture/tiktok/live_batch_probe.py`
- pointer-action configs/tests in `forseti-harness/source_capture/adapters/browser_snapshot.py` only if missing
- focused tests in `forseti-harness/tests/unit/test_tiktok_live_batch_probe.py`, `forseti-harness/tests/unit/test_source_capture_browser_snapshot.py`, and blocker-triage tests

Expected behavior:

- Benign onboarding/teaching/OK/Got-it overlays trigger setup action, not terminal blocker.
- Visible Retry/Try again/Reload controls trigger exactly one setup retry action before failure.
- Comment route zero-yield requires the full bounded comment-tab route and repeat before terminal classification.
- Challenge classifier emits marker and `challenge_kind` instead of only `platform_challenge_observed`.
- X-able slider challenge attempts X/Close when authorized; failed close remains typed zero-admission stop.

Validation target:

- Fixture tests for each blocker class and action sequence.
- Receipt tests proving `pointer_action_chronology` contains setup actions and `comment_action` remains filtered to comment-route actions.
- Regression tests for `challenge_close_not_accepted` with zero admission.

### BATCH-03 - Admission, Receipt, And Transcript Enforcement

Purpose: make optional packet/bronze output reliable and ensure comments/subtitles are either admitted safely or rejected with typed reasons.

Code scope:

- `forseti-harness/source_capture/tiktok/batch_packet.py`
- `forseti-harness/source_capture/tiktok/admission.py`
- `forseti-harness/source_capture/tiktok/live_batch_probe.py`
- live runner admission chain
- tests for TikTok batch admission and live batch probe

Expected behavior:

- Admission rejects all challenge/failure/diagnostic/owner-manual-clean-claim violations before writing.
- Source-native subtitle allowlist and sanitized WebVTT/cue capture are explicit and tested.
- Unsupported subtitle host emits typed non-capture reason; raw signed URL/body never persists.
- Staging-to-packet receipts carry enough sanitized provenance to explain why a row did or did not admit.

Validation target:

- Batch admission rejection tests for every fail-closed marker.
- Subtitle allowlist tests and no-raw-url/no-raw-body tests.
- Local `--admit-output` success-path test for comment + subtitle-bearing fixture.

### BATCH-04 - Cold-Agent Command Surface And Probe Receipts

Purpose: make the operator-facing route simple enough that cold agents run the right command and stop after the right receipt.

Code/docs scope:

- runner `--help`
- `forseti-harness/README.md`
- `forseti-harness/docs/source_capture_agent_runbook.md`
- `docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md`
- optional new receipt template/checker if needed

Expected behavior:

- The recommended one-fixture sessioned command is copyable and uses the code-enforced defaults/gates.
- The runner prints typed result summaries that distinguish staging, local admit-output, bronze data-root, owner-attention, and fail-closed.
- Docs remove stale ambiguity but do not claim validation, scale, or full-network no-proxy.

Validation target:

- `--help` snapshot/behavior tests where practical.
- DCP/header/handoff pointer gates if docs change.
- Post-batch review for BATCH-01..04 is filed at `docs/review-outputs/tiktok_capture_enforcement_batches_1_4_post_adjudication_delegated_adversarial_code_review_v0.md`; new code changes still require their own review routing.

## First Batch Assumption-Gate Target

Accepted direction for first gate: **BATCH-01 - Runner Posture, Provenance Preflight, And Owner-Attention Skeleton**.

Load-bearing assumptions to verify before implementation:

1. Current tests can exercise runner pre-browser exits without launching a real browser.
2. The live runner has a clean place to reject wrong backend/posture before calling `write_tiktok_live_batch_probe_outputs`.
3. Existing sidecar validators expose enough typed failure signals to distinguish missing/legacy/mismatch without printing secret-adjacent payloads.

If these are verified, BATCH-01 is the right first fused target. If not, route to a smaller preflight-only patch or a spec slice before implementation.

## Non-Claims

- This document is not validation, readiness, merge approval, PR acceptance, live capture success, or implementation completion.
- This document does not authorize CAPTCHA/slider solving or secret inspection.
- This document does not prove TikTok source access, account safety, subtitle coverage, bronze correctness, or scale.
- The batches are implementation targets; each still needs source reads, tests, and review routing under the Orca overlay.

## Direction Change Propagation - 2026-07-05 Cold-Agent Doctrine Pickup

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok cold-agent capture doctrine now has one mergeable entry contract:
    this goal document points agents to the sanctioned live-runner path, blocker
    playbook, runbook command, provenance ADR, lane spec, and completed
    cross-vendor review report, and removes the branch-local PR689 handoff as a
    load-bearing required read.
  trigger: workflow_authority
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - orca-harness/docs/source_capture_agent_runbook.md
    - orca-harness/README.md
    - docs/workflows/forseti_repo_map_v0.md
    - docs/review-outputs/tiktok_capture_enforcement_batches_1_4_post_adjudication_delegated_adversarial_code_review_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/workflow-overlay/safety-rules.md
    - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/safety-rules.md
      reason: >
        The Source Capture Armory Runner Ladder rule already routes online
        capture through armory runners; this change only makes the TikTok
        runner/playbook entry route easier for a cold agent to find.
    - path: forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
      reason: >
        The lane spec already states the sessioned CloakBrowser route,
        source-access intervention boundary, no-solve rule, provenance
        limitation, transcript boundary, and admission non-claims; the patch
        changes cold-agent pickup/navigation rather than lane contract.
    - path: docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
      reason: >
        The architecture decision already owns the typed sidecar design and
        no-proxy non-claim; this patch points agents to it without changing the
        architecture.
  stale_language_search: >
    rg -n "tiktok_session_provenance_pr689_handoff|BATCH-01..03|human-login-only|no_proxy_profile_loaded|full-network no-proxy|CAPTCHA bypass|captcha bypass"
    docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md
    docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    orca-harness/docs/source_capture_agent_runbook.md orca-harness/README.md
    docs/workflows/forseti_repo_map_v0.md
    forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
  stale_language_search_result: >
    Executed 2026-07-05 after edits. Hits are intentional: the new non-claim
    saying this is not CAPTCHA bypass, the explicit instruction not to add a
    human-login-only doctrine, and this receipt's own query string. No live
    `open_next` or repo-map row still requires the branch-local PR689 handoff,
    and no checked surface claims `no_proxy_profile_loaded` is full-network
    no-proxy proof.
  non_claims:
    - not validation
    - not readiness
    - not live TikTok success
    - not account-safety proof
    - not full-network no-proxy proof
    - not CAPTCHA or slider-solving authorization
```
```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok cold-agent session pickup now uses the machine-local logical profile
    chowdakr_sg_tiktok: profile and auth-state provenance validate before browser
    launch with no logged-out downgrade, and a visible challenge triggers owner
    handoff before scripted pointer actions while X/Close remains explicit-only.
  trigger: workflow_authority
  related_triggers:
    - output_authority
  controlling_sources_updated:
    - docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md
  downstream_surfaces_checked:
    - forseti-harness/docs/source_capture_agent_runbook.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/workflow-overlay/safety-rules.md
  intentionally_not_updated:
    - path: forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
      reason: >
        The lane spec already requires authenticated session provenance,
        fail-closed unresolved challenges, no secret leakage, and no agent
        CAPTCHA solving; the logical alias and earlier owner prompt narrow cold
        invocation without changing those lane invariants.
    - path: docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
      reason: >
        The provenance schema and validation semantics are unchanged; the new
        profile resolver selects and validates an existing sidecar from stable
        user-local storage.
    - path: .agents/workflow-overlay/safety-rules.md
      reason: >
        The Runner Ladder, bounded implementation, and no-ad-hoc-capture rules
        are unchanged.
  stale_language_search: >
    rg -n "human-challenge-handoff.*requires|fires only after scripted X/Close|storage-state label resolves only|--state-label.*dedicated|--allow-challenge-close-followthrough.*--human-challenge-handoff|client_provided_session.*no_proxy_profile_loaded"
    forseti-harness/docs/source_capture_agent_runbook.md
    docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md
    docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
  stale_language_search_result: >
    Executed 2026-07-11 after edits. The only hit is this receipt's own quoted
    query at line 405; no live contract prose retains the stale coupling.
    Remaining X/Close language is explicitly scoped to the separate route.
  non_claims:
    - not validation
    - not readiness
    - not live TikTok capture success
    - not CAPTCHA solving authorization
    - not full-network proxy or egress proof
```

Older receipts for this file live verbatim in `docs/decisions/dcp_receipts_archive_v0.md`.
