# TikTok Capture Lane Spec v0

```yaml
retrieval_header_version: 1
artifact_role: Capture spec
scope: Behavior/contract spec for the TikTok public creator-momentum + top-comment capture lane and the bounded TikTok Shop US access-egress gate. Prioritizes (1) lowest practical bot detectability and (2) horizontal scalability. Sessioned/cookied real-browser, ride-the-page's-own-requests.
use_when:
  - Implementing or reviewing the TikTok capture lane.
  - Deciding the anti-detection + scale design before any build.
  - Accessing the bounded TikTok Shop US account or surface.
authority_boundary: retrieval_only
status: spec only — no build authority; survivability-at-scale UNMEASURED (see Validation + Non-claims)
derived_from:
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_first_slice_probe_recon_v0.md   # N=1 evidence
  - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_logged_out_first_slice_probe_plan_v0.md
  - docs/review-outputs/tiktok_capture_calibration_architecture_review_v0.md   # routes + non-claims
  - orca-harness/source_capture/  # reuse substrate (models, cadence, writer, browser_snapshot)
priorities: [lowest_bot_detectability, scalable]
capture_mode: sessioned_cookied (owner decision 2026-06-22; supersedes the logged-out-primary posture in C8)
```

## Direction Change Propagation - 2026-07-04 Live Runner Bronze Admission Chain

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok live runs can now be asked to produce bronze/data-lake packets by
    chaining the one-creator live runner's sanitized staging output through the
    existing TikTok batch admission gate with `--admit-output` or an explicit
    `--data-root`, while default live behavior remains staging-only and all
    challenge/failure/no-secret gates still fail closed.
  trigger: workflow_authority
  related_triggers:
    - product_doctrine
    - validation_philosophy
    - output_authority
  controlling_sources_updated:
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - orca-harness/runners/run_source_capture_tiktok_live_batch_probe.py
    - orca-harness/tests/unit/test_tiktok_live_batch_probe.py
    - orca-harness/docs/source_capture_agent_runbook.md
    - orca-harness/README.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - docs/workflows/orca_repo_map_v0.md
    - orca/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/safety-rules.md
    - .agents/workflow-overlay/validation-gates.md
    - orca/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md
    - docs/workflows/tiktok_logged_out_x_close_test_handoff_v0.md
    - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/safety-rules.md
      reason: >
        The Source Capture Armory Runner Ladder rule already routes online
        capture through armory runners; this change binds a TikTok runner path
        inside that ladder and does not change the global safety rule.
    - path: orca/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
      reason: >
        The index already says TikTok is partial rather than absent and that
        parsed Funmi N30 batch packet admission is proven; this patch updates
        execution/runbook surfaces, not the underlying recon verdict.
  stale_language_search: >
    rg -n "TikTok still has no technical recon|live staging only|does not write a SourceCapturePacket directly|explicit remaining TikTok recon gap|ORCA_DATA_ROOT"
    orca-harness/README.md orca-harness/docs/source_capture_agent_runbook.md
    docs/workflows/orca_repo_map_v0.md docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    orca/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
  stale_language_search_result: >
    Executed 2026-07-04 after edits. No stale "TikTok still has no technical
    recon", "does not write a SourceCapturePacket directly", "live staging
    only", or "explicit remaining TikTok recon gap" hits remained. The
    remaining `ORCA_DATA_ROOT` hits are intentional non-use notes: the live
    runner requires explicit `--data-root` for lake writes.
  non_claims:
    - not validation
    - not readiness
    - not live capture success
    - not no-proxy provenance proof
    - not authorization to solve or bypass CAPTCHA/slider challenges
    - not cross-creator, scale, account-safety, or promotion proof
```

## Direction Change Propagation - 2026-07-04 Auth-State Provenance Enforcement

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok sessioned live capture can now require a typed local auth-state
    provenance sidecar before browser launch. Warmup emits category-only
    browser user-data provenance, export merges it into auth-state metadata,
    and the live runner may require harness_proxy_profile_posture such as
    no_proxy_profile_loaded; this remains harness proxy-profile posture only,
    not full-network no-proxy egress proof or a forgery-proof producer-identity ledger against deliberate local sidecar edits.
  trigger: validation_philosophy
  related_triggers:
    - workflow_authority
    - output_authority
    - lifecycle_boundary
  controlling_sources_updated:
    - docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
    - forseti/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - orca-harness/source_capture/source_access_provenance.py
    - orca-harness/source_capture/auth_state.py
    - orca-harness/source_capture/browser_user_data.py
    - orca-harness/runners/run_source_capture_cloakbrowser_profile_warmup.py
    - orca-harness/runners/run_source_capture_browser_user_data_export.py
    - orca-harness/runners/run_source_capture_tiktok_live_batch_probe.py
    - orca-harness/source_capture/tiktok/live_batch_probe.py
    - orca-harness/docs/source_capture_agent_runbook.md
    - orca-harness/tests/unit/test_source_capture_authenticated_browser_snapshot.py
    - orca-harness/tests/unit/test_tiktok_live_batch_probe.py
  downstream_surfaces_checked:
    - .agents/workflow-overlay/validation-gates.md
    - .agents/workflow-overlay/safety-rules.md
    - orca-harness/docs/source_capture_packet.md
    - docs/workflows/forseti_repo_map_v0.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/validation-gates.md
      reason: >
        The non-self-certification gate already owns the general provenance rule;
        this patch implements it for TikTok auth-state sidecars without changing
        the overlay rule.
    - path: .agents/workflow-overlay/safety-rules.md
      reason: >
        Source-access safety boundaries and CAPTCHA/proxy restrictions did not
        change; the patch only adds fail-closed provenance checks inside the
        existing authorized runner path.
    - path: orca-harness/docs/source_capture_packet.md
      reason: >
        The new sidecar witnesses are local ignored auth-state metadata and are
        intentionally not copied into SourceCapturePacket payloads or bronze
        records, so the packet contract does not change.
    - path: docs/workflows/forseti_repo_map_v0.md
      reason: >
        No new durable human-authored artifact or top-level source area was
        added; the architecture ADR is already map-reachable from PR #685.
  stale_language_search: >
    rg -n "no_proxy|no-proxy|no proxy|harness_proxy_profile_posture|require-harness-proxy-posture|source_access_provenance"
    orca-harness/source_capture orca-harness/runners orca-harness/docs/source_capture_agent_runbook.md
    forseti/product/spines/capture/core/source_families/social_media/tiktok
    docs/decisions/tiktok_auth_state_provenance_sidecar_architecture_v0.md
  stale_language_search_result: >
    Executed 2026-07-04 after edits. Expected hits are the ADR, this spec, the
    runbook, the new source_access_provenance/auth-state/browser-user-data code,
    the TikTok live runner, and focused tests. Unrelated no-proxy hits remain in
    non-TikTok adapters or historical logged-out probe docs. No checked live
    TikTok surface claims that an auth-state label or no_proxy_profile_loaded is
    full-network no-proxy egress proof.
  non_claims:
    - not validation
    - not readiness
    - not live capture success
    - not full-network no-proxy egress proof
    - not forgery-proof local sidecar producer-identity proof
    - not CAPTCHA or slider-solving authorization
    - not account-safety or scale proof
```

## Direction Change Propagation - 2026-07-03 Challenge-X Follow-Through

```yaml
direction_change_propagation:
  doctrine_changed: >
    TikTok capture doctrine now allows owner-authorized X-able public challenge
    modal follow-through as a receipt-visible source-access intervention for
    post-close page-owned comment capture, while preserving no-drag/no-solve,
    unresolved-challenge stop, diagnostic-only close mode, and non-clean-route
    limitations.
  trigger: product_doctrine
  related_triggers:
    - workflow_authority
    - validation_philosophy
  controlling_sources_updated:
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
  downstream_surfaces_checked:
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md
    - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    - docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
    - orca-harness/source_capture/tiktok/live_batch_probe.py
    - orca-harness/source_capture/tiktok/batch_packet.py
  stale_language_search: >
    rg -n "challenge-close diagnostics are never capture success|never solve a challenge|stop-on-challenge|challenge-close diagnostic only|closeability" docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md orca/product/spines/capture/core/source_families/social_media/tiktok orca-harness/source_capture/tiktok
  non_claims:
    - not validation
    - not readiness
    - not legal sufficiency
    - not unchallenged clean capture
```

## Direction update (2026-06-22) — sessioned/cookied

Owner decision: **logged-out capture is too brittle** (highly session-trust-dependent; captchas observed, see recon addendum). The lane now captures via an **authenticated session** (cookied), which TikTok generally trusts more and challenges less. This **supersedes C8** (logged-out-only) with the account invariants in **C8'** below. Everything else (real browser, ride the page's own requests, ≤3 requests/video, cadence, identity distribution, secret hygiene) is unchanged and applies to the authenticated session. **Tradeoff accepted:** the failure mode shifts from captcha/throttle (recoverable) to **account ban** (loses the account + its accumulated trust) — mitigated by dedicated burnable accounts, conservative pacing, and human-performed login.

## Purpose

Capture public TikTok videos under a dedicated authenticated session, at human-rate, with the lowest practical detection footprint: (a) per-video/creator **momentum metadata**, and (b) a bounded set of **top/relevant comments** with commenter identity and exact timestamps — sufficient for downstream anti-bot / data-integrity analysis. The 30/60-minute comment-window requirement is **dropped** (not needed for bot detection); comments are a top/relevant *sample*, not a chronological census.

## Design spine (resolves the detectability-vs-scale tension)

**Minimize footprint per target; scale horizontally by distributing identity.** Each video is captured with ~2–3 requests by a realistic browser context; throughput comes from many paced, identity-distinct contexts — never from hammering one context.

## Capture contract (what must be true)

### C1 — Real browser context, never headless (priority-1 invariant)
Capture MUST run in a non-headless / anti-detect browser context with a genuine fingerprint and a **warmed device-cookie session** (`ttwid` etc.). Headless and bare HTTP are FORBIDDEN as capture transports — both were served a stripped/no-data page in recon. (Harness: `cloakbrowser_snapshot` / a real-browser context, NOT `direct_http` or headless `browser_snapshot`.)

### C2 — Ride the page's own signed requests; never forge signatures
The lane MUST obtain data by loading the public page and reading what the page itself produces:
- **Metadata** from the server-rendered blob `#__UNIVERSAL_DATA_FOR_REHYDRATION__` → `__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct` (zero extra requests).
- **Comments** by letting the page issue its own signed `GET /api/comment/list` and **intercepting the response** (hook `fetch`/`XHR`).
Forging or replaying `msToken` / `X-Bogus` / `X-Gnarly` / `verifyFp` is FORBIDDEN (brittle, adversarial, higher-detection). No synthetic/cold API calls.

### C3 — Bounded request footprint per target (priority-1 invariant)
Per video: metadata = 0 extra (in the page); comments = the first page + **at most ONE** pagination. **Hard cap ≈ 3 page-emitted requests per video.** No deep pagination, no full-comment census.

### C4 — Human-rate cadence with jitter
Inter-target and inter-request timing MUST use bounded jitter (harness `cadence.build_cadence_plan(mode="bounded_jitter")`). Starting hypothesis ~2.5–4 s, never sub-2 s (carried from IG, **re-measure for TikTok**). No bursts.

### C5 — Identity distribution + per-context volume cap (scale invariant)
Scale by running N contexts in parallel, each with its **own** fingerprint + residential/mobile proxy + warmed cookies, each under a **per-context window volume cap**. Throughput = contexts × paced-rate. A single context MUST NOT exceed its window cap.

### C6 — Real-block detection → cooldown (and distinguish infra noise)
Detect a genuine TikTok block — its own 403 HTML, unresolved captcha/verify interstitial, `msToken` rejection, or an empty/stripped shell — and on it: stop the context, cool down, do not hammer. Owner-authorized X-able public challenge modals are a narrower route case: the runner may click X/Close exactly as a bounded source-access intervention, never drag/solve the puzzle, then continue only if challenge text clears and a page-owned `/api/comment/list` response is captured. This is recorded as post-close follow-through, not unchallenged clean capture. The lane MUST distinguish a **true TikTok signal** from **transport/infra glitches** (e.g., an extension/proxy `[BLOCKED: JWT token]` `chrome-error` page is NOT a TikTok block — retry once before treating as detection).

### C7 — Secret hygiene (G-2 contamination stop)
No cookies, storage-state, `msToken`, signature params, proxy endpoints/credentials, exit IPs, or device IDs may be written into any packet. Packets record category-only provenance. A packet containing any of these is contaminated scratch, not admissible.

### C8' — Sessioned/cookied via a dedicated account (supersedes logged-out-only; priority-1 + safety invariant)
Capture runs under an **authenticated session** whose cookies authenticate it. Required posture:
- **Dedicated, non-personal account(s) only** — never a personal/primary account. Accounts are treated as **burnable** (a ban costs that account, not the operator).
- **Human-performed login** via a headed session bootstrap; the agent **never enters credentials** (harness: `run_source_capture_browser_session_bootstrap.py` → `run_source_capture_authenticated_browser_packet.py`).
- **No credentials, cookies, storage-state, or tokens in any packet** (C7 / G-2) — even more load-bearing now that secrets exist.
- **Provenance labeled `entitled_session`**, not `public_logged_out`. The comment data is still real public comments; only the access path is authenticated.
- **Harness proxy-profile posture, not egress proof.** Warmed CloakBrowser user-data exports may carry a local ignored auth-state sidecar attesting `harness_proxy_profile_posture` such as `no_proxy_profile_loaded`; the live runner may require it with `--require-harness-proxy-posture no_proxy_profile_loaded`. This attests only the Source Capture harness did not load a proxy profile for that warmed profile, not that the whole machine/network had no proxy/VPN/upstream egress layer, and not that a deliberate local actor could not forge or edit the ignored sidecar.
- **TikTok Shop US egress gate.** Before each access session to the bounded TikTok Shop US account or surface, the active browser context MUST freshly observe `US` country egress through an external IP-country check. For this bounded access gate, either a VPN or proxy is acceptable; C5's residential/mobile-proxy rule continues to govern scalable capture contexts, and provider or profile identity is not the requirement. If US egress is absent or cannot be confirmed, stop before accessing TikTok Shop. Do not persist the check's exit IP, proxy/VPN credentials, endpoint, cookies, local profile path, or machine-specific launcher (C7). The check proves only observed country egress at that time, not physical location, future continuity, account safety, or capture success.
- **Public content only** — no private/DM/access-controlled surfaces; authentication buys trust/stability, not access to non-public data.
- **Account-level stop-on-unresolved-challenge** (per C6): on ban, auth-wall, challenge text that remains after an authorized X/Close follow-through, or any non-closeable captcha/challenge signal, stop that account, cool down, rotate; never drag or solve a challenge.

## Data contract (fields)

**Per video/creator (from blob, raw integers):** `video_id`, `desc`, `createTime` (raw unix → exact), `stats{diggCount, shareCount, commentCount, playCount, collectCount}`, `author{id, uniqueId, nickname, verified, privateAccount}`, `authorStats{followerCount, followingCount, heart, videoCount}`, `music{id,title,authorName,original}`, `textExtra` (mentions/hashtags). Video post time also derivable independently via `video_id >> 32`.

**Per video, top/relevant comments (first page + ≤1 pagination), from `/api/comment/list`:** per comment `cid`, `text`, `create_time` (raw unix → exact), `digg_count`, `reply_comment_total`, `user{uid, unique_id, nickname}`. Envelope: `total`, `has_more`, `cursor`. Order is TikTok's default **relevance** sort (no web time-filter exists — confirmed); capture the source order verbatim, do not re-rank.

**Receipts (every capture):** source URL at runtime; persisted receipts carry URL path/hash only, retrieval timestamp, response body sha256/size, parsed public fields, captured-from posture (`entitled_session`), request count used, limitations, non-claims, and no-secret confirmation. Raw response bodies, signed URLs, cookies/tokens, and storage-state paths are excluded per C7.

**Source text / transcript boundary:** TikTok description (`desc`), hashtags/mentions (`textExtra`), music metadata, and captured public comments are source text. A later Funmi/session N=30 cadence receipt measured source-native subtitle metadata plus WebVTT body admission when `video.subtitleInfos` exists (`26/30` metadata present; `26/26` WebVTT parse success when present). Treat this as `source_native_subtitle_webvtt` evidence for that creator/session, labeled with TikTok's source field such as `ASR` when present. It is not owner-generated ASR, not durable audio/video preservation, not cross-creator subtitle coverage, and not a platform-wide transcript guarantee.


**Implementation note (2026-07-01; amended 2026-07-04):** Network-free parsed-batch admission now exists for the Funmi N30 staging shape via `orca-harness/source_capture/tiktok/batch_packet.py` and `orca-harness/runners/run_source_capture_tiktok_batch_packet.py`, with focused tests in `orca-harness/tests/unit/test_tiktok_batch_admission.py`. The verified data-lake packet is `F:\orca-data-lake\raw\97c\01KWCYZ9P72W4SJD7NDPRQT0DB` (`tiktok_creator_batch_comment_subtitle_admission`): 30 videos, 596 parsed comments, 26 transcript-bearing source-native WebVTT captures, 1044 cues, and deterministic typed extraction seeds. The one-creator live producer exists via `orca-harness/source_capture/tiktok/live_batch_probe.py` and `orca-harness/runners/run_source_capture_tiktok_live_batch_probe.py`, with fake-engine tests in `orca-harness/tests/unit/test_tiktok_live_batch_probe.py`; it runs one creator per invocation, uses headed/sessioned or logged-out page-owned comment-list observation, and writes sanitized grid/cadence staging JSON by default. When the owner asks for packet/bronze output, the same runner can now chain the existing batch admission gate with `--admit-output` or an explicit `--data-root`; it intentionally does not read ambient `ORCA_DATA_ROOT`, and admission fails closed on challenge/failure/diagnostic contract markers before any packet or lake write. The existing batch runner already writes to the data lake through `--data-root`; the live runner now uses that same admission function rather than duplicating lake logic. Follow-through clicks are preserved as source-access interventions and can admit only post-close page-owned comment responses; diagnostic close mode remains stop-only. The code is not itself a successful live run, profile-grid automation proof, cross-creator ceiling proof, non-proxy provenance proof, durable media/video preservation, final product extraction, Cleaning, ECR, or Judgment. The same live runner can now fail closed before browser launch when `--require-harness-proxy-posture` is set and the auth-state metadata is legacy-only, missing, mismatched, or contaminated; the requirement records category-only posture in staging receipts and still does not prove blanket no-proxy egress.

## Explicitly out of scope

30/60-minute comment windows; full-comment pagination / chronological census; personal account use; agent-entered credentials; private or access-controlled content; media/video/audio bytes; owner-generated ASR unless separately authorized; source-native subtitle claims when `subtitleInfos` is absent; cross-creator subtitle coverage unless separately measured; signature forging; reply-thread expansion beyond the first-page `reply_comment_total` count.

## Validation plan

1. **Offline / no-live:** fixture tests for the blob parser and the comment-list JSON parser; receipt-assertion tests; secret-hygiene tests (C7); a no-live smoke mode. All green before any live run.
2. **Detection-ceiling measurement gate (owner-gated, BEFORE bulk):** a controlled, escalating volume probe that measures where (if anywhere) a *real* TikTok block appears under this design — distinct from infra noise (C6). Bulk scale is NOT authorized until this measures an acceptable ceiling. This spec designs for low detectability; it does not assert survivability.
3. **First-party-anchor option:** if bulk volume is later sourced from a vendor, a small self-captured set under this lane is the provenance-clean anchor to validate vendor fidelity.

## Harness fit (reuse, minimal new surface)

If a cold lane is confounded by TikTok UI movement or blocker behavior, open
`docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md` before any
browser action. It maps blocker classes to the bounded `BrowserPagePointerAction`
substrate and separates three cases: benign dismissals, owner-authorized
X-able challenge follow-through, and diagnostic-only challenge close. The no-
drag/no-solve boundary remains; post-close admission must preserve the source-
access intervention.

- **Reused substrate, lightly extended browser seam:** packet `models.py` (+ typed `MetricObservation` for stats), `cadence.py` (C4), `writer.py`/`packet_assembly.py`, `block_shell.py`/`rendered_access.py` (C6), `proxy_profiles.py` (C5), and `auth_state.py` / authenticated browser session bootstrap only for the C8' dedicated-account session boundary. The reusable browser response seam is `browser_snapshot.py::fetch_browser_page_observation_capture`: attach a response predicate before navigation, run headed/sessioned, execute a bounded post-load page action to open comments, then preserve only matching page-emitted `/api/comment/list` responses. `fetch_browser_context_responses` is not the TikTok C2 mechanism because it performs explicit in-page `fetch(url)` calls.
- **New (TikTok satellite):** `source_capture/tiktok/admission.py` (network-free parsers/sanitizers), `video_packet.py`, `batch_packet.py`, `batch_coverage.py`, `batch_projection.py`, and `live_batch_probe.py` plus `run_source_capture_tiktok_live_batch_probe.py` for one-creator live staging and optional admission chaining (C1-C3, C6: headed/sessioned, request cap, comment-panel post-load action, comment/list response predicate, sanitized staging by default, `--admit-output` / explicit `--data-root` through the existing batch gate when owner-requested). The required change vs the failed recon runs is **running the existing browser observation seam non-headless/sessioned with assets allowed**, not forged request logic.

## Open decisions (owner-owned) / Non-claims

- **Volume + provenance target** (how many creators/videos/comments, freshness, first-party-required?) is unset and **flips the scale design** (self-capture vs vendor-for-bulk + first-party-anchor).
- **Proxy strategy** (residential vs mobile, pool size) is a cost-vs-detectability owner decision.
- **Detection ceiling is PARTIALLY MEASURED, not settled** - one Funmi/session cadence run completed N=30 with zero challenges and clean page-owned comment/subtitle capture. Cross-creator coverage, higher-volume survivability, longer-run account safety, and selector/signature/field drift remain unmeasured.
- This is a spec only: no build authority, no validation/readiness, no deployment. **Authenticated (sessioned) or logged-out public capture via owner-authorized bounded browser actions** under the owner Risk posture; X-able public challenge follow-through carries ToS/account-risk exposure and is not unchallenged clean capture. Commenter handles/uids are public comment metadata for aggregate integrity analysis, not individual dossiers. Not legal advice.
```
