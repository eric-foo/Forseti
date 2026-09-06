# Forseti Harness

Compatibility note: the repository path, package metadata, and CI/check
identifiers now use Forseti naming. Historical `orca-harness` references resolve
through `docs/migration/forseti_harness_runtime_migration_v0/moved_paths_index.md`.
Python import roots remain top-level packages such as `source_capture`,
`data_lake`, `ecr`, `schemas`, and `runners`; this is not a Python namespace
rename.

Step A rebuild of the v0.14 deterministic judgment harness.

This package is intentionally narrow:

- deterministic mapping and scoring only;
- fixed disk-backed TR/Casetext plumbing fixture only;
- local source-observability support checks only, not source acquisition;
- local dry memorization-probe receipt normalization only, not provider
  execution;
- opt-in raw-API no-tools memorization-probe execution plumbing only, not
  probe authorization;
- append-only scoring results and failure-event logging;
- explicit non-claim boundary: `plumbing works only; not judgment quality`.

The source-observability helper reports visible capture limitations in local
records. It does not fetch sources, retrieve archives, automate browsers, call
APIs, score source quality, validate Data Capture, or authorize downstream ECR,
Cleaning, or Judgment behavior.

## Unattended Model Attempts

Current method-v12 semantic reconciliation preparation writes each prompt's
`.schema.json` alongside its `.md` file. Current response v3 requires keyed
candidate decisions and original-label assignments. The model chooses nodes,
relations and wording; code carries child-owned identities, literal conditions,
emerging labels, polarity composition and lineage. Use that exact sidecar.
Native validation rejects missing, foreign, duplicate or prohibited decisions;
a schema pass is not semantic proof. `prepare-reconciliation-level
--existing-stage <stage.json>` resumes unchanged stage membership. Explicit
`--response-version semantic_evidence_reconciliation_response_v2` preserves
historical preparation, and stored v2 responses remain consumable unchanged.
For a verified method-v7 continuation, explicitly select
`--response-version semantic_evidence_reconciliation_response_v3` on a fresh
stage to use the same decision compiler and source-role constraints. This
retains method v7 and its verified inputs; the older-method default and stored
legacy responses keep their original replay. Explicit v3 also defaults to
`exact_identity_namespaces_v3`. Never rebind an old answer to this new request.
Normal method-v12 response-v3 requests default to
`--authoring-revision exact_identity_namespaces_v3`: opaque node-key prefixes
separate exact subject/comparator/version identity classes without choosing
meanings, and code supplies exact groups of candidates sharing original evidence.
Each output node may use at most one member of each group; overlapping groups
do not prohibit unrelated combinations. An empty list means no shared-source
restrictions in that batch. The model need not reconstruct hidden source IDs;
native validation still rejects duplicate source paths. These restrictions are
included in the rendered byte budget. Fresh
current stages cap each batch at 96 candidates as well as the prompt-byte limit.
Use `--authoring-revision exact_identity_namespaces_v2` for prior capped requests,
`--authoring-revision exact_identity_namespaces_v1` for prior namespaced
packing or `--authoring-revision legacy` for older normal v3 replay.
Low-level Python preparation retains legacy defaults; current callers select
`RECONCILIATION_AUTHORING_IDENTITY_V3` explicitly. Preserve completed request and
response bindings; prepare future work separately under the new revision.
Definition recovery and local
repair keep their previously fitting historical requests and existing keys.
Oversized local repairs try a lossless table layout before enforcing the same
byte limit; all sources and connected attachments remain present, and the
response schema is unchanged. When a freshly rederived diagnostic contains only
complete cross-child `duplicate_leaf` issues, pass that report with
`prepare-reconciliation-repair --diagnostic <diagnostic.json>` to use the
structural repair rendering. It includes the affected validated child meanings,
identities, conditions, provenance paths, decisions, and parent definitions but
no raw evidence or source-context bodies. Mixed, stale, incomplete, clean, or
within-one-child diagnostics fail closed, as does a convergence-mode stage whose
repeated-source-row retention this projection cannot expose. This adds no
provider stage or semantic clearance. The semantic-integration contract v107 owns
this boundary.

For authorized unattended Codex jobs whose retries, elapsed time, or failure
history matter, use the shared executor rather than a task-local buffered
subprocess wrapper. It is usable by any intelligence-cycle stage:

```powershell
python runners/run_codex_provider_attempt.py --codex-executable <absolute-native-codex-path> --require-chatgpt --attempt-root <attempts> --attempt-id <new-id> --prompt-file <prompt.md> --output-schema <schema.json> --worktree <repo> --model <model> --reasoning-effort high --timeout-seconds <seconds>
```

For a self-contained job whose required project reads would otherwise trigger
blocked shell calls, both the attempt and job runners accept repeatable
`--preload-context <required-instruction-file>` arguments. The selected UTF-8
files are supplied verbatim as additional developer context and the native
`shell_tool` feature is disabled for that job. Project instructions remain
active; select every required source for the bounded task, and report missing
context rather than manufacturing an answer. Do not use this mode for a task
that needs further file discovery or shell execution.

For reconciliation, the observed required reads are the worktree's
`.agents/workflow-overlay/README.md` and
`forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`.
Pass both explicitly. The launcher reads them before generation and records their
paths, byte hashes, and combined context hash. The job pins that context across
retries; drift fails before generation, and a reused receipt must carry the same
context and shell restriction. Context files are checked before launch intent,
including after a retry delay; drift preserves any existing retry claim without
creating a false unknown-execution record. Restore the bound files to resume.
Changing context or launcher code creates a different job binding: use a new job
identity for new work, and preserve completed results under their original
bindings rather than relaunching them to update instructions. Disabling
`shell_tool` does not assert that every other tool feature is unavailable.
Existing prompt/schema bytes and default launches
are unchanged. Additional context consumes input tokens (about 20 KB for these
two files); measure whole-job usage and denied-tool events rather than assuming
a saving. This opt-in removes repeated blocked reads, not the underlying host
policy. API authentication and spend boundaries are unchanged.

Select a compatible installed native executable explicitly (`codex.exe` on
Windows), including after an installation moves during an update. The runner
never searches PATH, selects a different installation, or upgrades it. Its local
version check records the version in the existing execution records; a version
string alone does not establish that the server supports the requested model.

The standing command above requires file-backed ChatGPT sign-in under
`CODEX_HOME` (default `~/.codex`). It rejects `OPENAI_API_KEY`, `CODEX_API_KEY`,
`CODEX_ACCESS_TOKEN`, and `OPENAI_BASE_URL` overrides without printing values.
The selected executable checks `login status` against the same credential store
and environment used for generation. A nonzero or unrecognized result stops
before generation; check access in the real execution context before concluding
that sign-in is missing. Codex prints that verdict on stderr, the same stream it
uses for its own notices. Only the reproduced stderr notice beginning
`WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir `
and ending with a quoted directory is excluded from the authentication verdict.
Other warnings, unexpected stdout, duplicate or conflicting verdicts, and nonzero
exits still stop the launch. `login status` has no
`--ignore-user-config`, so unlike generation it also loads
`CODEX_HOME/config.toml`; a file the selected build cannot parse stops the launch
as a reported configuration fault rather than as an authentication result.
Keyring-only sign-in is not supported by this mode.
Codex's native `forced_login_method="chatgpt"` restriction also applies during
generation: if credentials change to another method after the check, Codex exits
and may clear that mismatching login. The runner does not copy credentials,
sign in, modify global configuration, or fall back to API billing. ChatGPT
sign-in uses subscription access; subscription limits and service failures still
apply ([OpenAI authentication](https://learn.chatgpt.com/docs/auth)). Omitting
`--require-chatgpt` leaves authentication caller-managed and requires separate
authorization if the selected route incurs API charges.

Prepare prompt, schema, and attempt files in an ignored workspace run directory
readable by the account that will execute the command. Avoid sandbox-private
temporary directories when execution crosses into another permission context.
The runner opens the actual inputs and creates the actual attempt records before
generation; access failures stop locally, without changing ACLs or retrying.
Keep each attempt ID new, including after a local failure reserves a directory.

For a network-restricted agent shell, launch this command through the harness's
per-operation network approval route. The outer shell controls the provider's
connection; the child's `--sandbox read-only` restricts model tools and cannot
grant that connection. Do not change global sandbox settings to make a run work.
Use the first required batch to confirm a new installation or execution context
before expanding to authorized parallel batches; no extra model diagnostic or
per-batch network probe is required. Permission denials, model/client
incompatibility, and provider failures retain their real errors in the attempt
logs. Local version/login checks precede the generation budget, have ten-second
limits, and make no model call;
each attempt pays only these local checks and the existing file I/O.

The timeout is one finite, workload-appropriate budget for the entire attempt;
reconnects and additional client turns do not reset it. Logs go directly to
`events.jsonl` and `stderr.log`; stderr is also mirrored while the process runs.
The mirror is best effort over an authoritative on-disk log: a console that is
absent or breaks mid-attempt is recorded in `stderr_echo_status` and never ends
the attempt or suppresses its receipt.
An idle process is not evidence of useful model work. On timeout the executor
stops its local process tree and preserves the attempt; a stop that fails is
recorded in `error` and does not relabel the timeout. It cannot prove remote
cancellation or unreported provider usage.

`execution_started.json` reserves execution and `execution_receipt.json` records
its terminal outcome. The receipt separates wall time, recognized retry/fallback
events, and exact completed-turn token fields; useful compute time stays
`UNOBSERVED`. Reported turn usage does not establish complete hidden-retry cost.
Do not subtract cached input or add reasoning tokens to output tokens.

Process completion is not semantic acceptance. The stage-specific validator and
publisher still own acceptance. `provider_attempts.py` refuses publication for
unfinished or unsuccessful executor attempts and changed executor outputs;
either executor record is enough to hold an attempt to that boundary.
Receipt checks, usage accounting, stage validation, and publication use one
captured response/events snapshot; later writes cannot replace the checked answer.
Publication rejects duplicate JSON object keys at any depth before the caller's
validator runs, using the same decoder hook as the semantic runner. Raw outputs
and exact usage remain preserved on rejection; no earlier decision is silently
replaced by a later key.
After a stage-validator rejection, publication may reuse that completed answer
without a new model call only if any saved usage receipt matches the exact
rederived bytes. Conflicting receipts fail; canonical outputs are never replaced.
Historical attempts with no executor record retain their existing
execution-record exemption, not an exemption from duplicate-key rejection.
A retry gets a new attempt ID; the executor launches no
automatic retry and never changes prompts, models, or evidence to obtain a pass.

When a timed-out attempt contains a completed structured `agent_message`, do not
weaken the normal publisher or relabel the attempt. Reconciliation may use the
separate recovery command with one or more chronological retry candidates:

```powershell
python runners/run_semantic_evidence_integration.py recover-reconciliation-provider-attempt --bundle <bundle.json> --stage <stage.json> --response-schema <batch.schema.json> --attempt-dir <attempt-1> --attempt-dir <attempt-2> --recovery-dir <new-recovery-dir>
```

The command verifies the execution start and terminal receipts, their bound
prompt/schema/output hashes, and a strict complete LF-delimited JSONL stream
that preserves Unicode separators inside JSON string values. It requires one
distinct completed `agent_message` per attempt, collapsing only exact identical
retransmissions, then applies the bound JSON schema and unchanged native
reconciliation consumer. JSON decoding rejects non-finite constants. Among
eligible attempts it selects the earliest parsed UTC `started_at`, accepting
canonical whole-second or fractional-second timestamps; it never compares answer
quality. Zero or multiple distinct messages, malformed JSON, hash drift, schema or native rejection, and any
non-timeout outcome fail closed. The new response and recovery receipt are
no-replace artifacts. Missing completed-turn usage remains `UNOBSERVED`, the
original attempt remains `TIMED_OUT`, and the command makes no provider call.

The shared runtime lives in `provider_execution.py`; immutable storage and
publication remain in `provider_attempts.py`. This is not a mandatory wrapper
around interactive conversations, capture tools, or unrelated processes.

For a standing run that needs bounded automatic recovery, use the job entry
point over that same executor:

```powershell
python runners/run_codex_provider_job.py --job-dir <run/jobs/unique-batch-id> --retry-budget-dir <run/retry-budget> --run-retry-limit <total-extra-attempts> --attempt-root <run/attempts> --prompt-file <prompt.md> --output-schema <schema.json> --worktree <repo> --codex-executable <absolute-native-codex-path> --model <model> --reasoning-effort high --timeout-seconds <seconds>
```

This entry point always requires ChatGPT authentication. Each job freezes its
input hashes, executable and executor hashes, model, timeout, paths and retry
policy. Repeating the same command reuses a completed immutable attempt without
generation; the stage validator and publisher must still accept that answer.
Jobs sharing a run use the same retry-budget directory and limit. Default
`--max-retries 1` allows one extra attempt after a ten-second delay, only for
recognized capacity or connection-reset diagnostics. `--retry-delay-seconds`
sets a finite delay up to sixty seconds. Concurrent budget claims serialize;
concurrent execution of the same job fails locally.

An authentication error, changed input, unknown timeout, unknown launch outcome,
exhausted budget, or semantic rejection remains visible and does not trigger
automatic generation. A crash after launch intent without a terminal receipt
requires inspection of the preserved attempt; restarting cannot prove that
remote work stopped. A recorded launch intent whose attempt directory is missing
is reported separately. Absence does not prove that no work started; preserve
the intent and inspect launch diagnostics before deciding how to recover.
Automatic relaunch remains refused, and an existing retry claim is not returned.
Retry claims are retained even if usage is missing or a
subsequent launch fails. Recovery neither edits answers nor changes model,
credentials or evidence. Completed answer or turn events suppress fresh retries
even when a timed-out process logged a reconnect warning; use the existing
validator-owned recovery route where applicable. Token and latency accounting
stays in the executor's
per-attempt receipts; missing usage is unknown, and subscription usage is not an
inferred dollar charge. The recurring cost is local hash/lock/receipt work plus
only the explicitly budgeted extra provider attempts.

Complete frontier point readers use named relation and preselection-confirmation
batches when necessary. Both preparation commands accept `--max-request-bytes`
(CLI default 50000), measured as UTF-8 prompt plus compact JSON response schema,
and `--batch-size` bounds the required row decisions. Preparation partitions
contiguous complete inventories; an indivisible oversized row fails
`request_capacity` before generation. This is a request-size bound, not a claim
about hidden provider context or response tokens. Literal candidate IDs and
reasons survive assembly. A source-bound complete point may exceed the ordinary
configurable origin ceiling only at its exact derived origin count; arbitrary
selections cannot borrow that exception. Use both bounded preparation stages,
then `finalize-batched-preselection-relation-confirmation-full-source` to validate
the complete response set and copy full bound source bodies into the reader.

## Screening Reads

Use the screening-read entries when a screen orchestrator needs one bounded
public read without creating a Source Capture Packet:

```python
from source_capture.screening_read import ScreeningReadDispatch, ScreeningReadRoute, screening_read

dispatch = ScreeningReadDispatch(screen_id="screen-123", question="one bounded source question")
result = screening_read(
    url="https://old.reddit.com/r/beauty/search?q=moisturizer&restrict_sr=on&sort=new",
    route=ScreeningReadRoute.REDDIT_SCREENING_READ,
    dispatch=dispatch,
)
```

For public pages that need the browser/interstitial rung:

```python
from source_capture.screening_browser_read import screening_browser_read

result = screening_browser_read(url="https://example.com/public-page", dispatch=dispatch)
```

These entries are orchestrator-invoked, public-only, human-rate, and screen-light
only. They do not stage packets, write manifests, return packet paths, touch ECR,
or run as a standing service/crawler/scheduler. Browser screening reads classify
`block_shell` on visible text, not full DOM. Same-shaped listing pages can reuse
`StructuredListingExtractionSpec` and `extract_structured_listing_candidates(...)` for
row-local title/date extraction. Build receipt:
`docs/workflows/screening_read_service_build_receipt_v0.md`; reusable findings:
`docs/workflows/screening_read_reusable_findings_v0.md`.

## Source Capture Packet

Use the source-capture runner when an operator already has local source files
and needs a no-network packet directory with a manifest, preserved raw files,
SHA256 hashes, posture metadata, and a human-readable receipt:

```powershell
python runners/run_source_capture_packet.py --source-family "docs_page" --source-locator "C:\capture\vendor_pricing_page.html" --decision-question "What did the pricing page show before the decision cutoff?" --input-file "C:\capture\vendor_pricing_page.html" --source-publication-or-event "pricing page date visible in local artifact" --cutoff-posture "pre-decision local capture artifact" --access-posture "local_file_only" --archive-history-not-attempted-reason "local CLI does not query archives" --media-modality-not-attempted-reason "local CLI does not retrieve additional media" --output ".\_test_runs\example_source_capture_packet"
```

This first checkpoint is local-file-only. It does not fetch URLs, call APIs,
query archives, automate browsers, preserve additional media, or decide
credibility, inclusion, Signal Use, Decision Strength, Action Ceiling, buyer
proof, or commercial readiness.

Optional metadata flags let the operator carry already-known source timing,
cutoff, archive, media, actor, mode-change, access, and re-capture posture into
the packet. Omitted fields stay visible as unknown, not attempted, or not
applicable rather than disappearing.

For the packet directory shape and receipt details, see
[`docs/source_capture_packet.md`](docs/source_capture_packet.md).
For agent-facing runner selection, stop conditions, and report format, see
[`docs/source_capture_agent_runbook.md`](docs/source_capture_agent_runbook.md).

Build a local Mini God-Tier source-quality report skeleton from an existing
packet after an operator has commissioned a source-quality pass:

```powershell
python runners/run_source_quality_report_skeleton.py --packet ".\_test_runs\example_source_capture_packet" --source-id "SOURCE-ID" --output ".\_test_runs\example_source_quality_skeleton.yaml"
```

The skeleton helper is manifest/metadata-only. It gives conservative
`suggested_result_token` guidance and keeps final source-language anchors,
coverage/drift notes, lifecycle admission, and `mini_god_tier_met` finalization
with the operator. It does not fetch sources, parse source bodies for meaning,
score source quality, admit fixtures, or run Judgment logic.

Build a read-only Source Quality state census from explicit queue rows and
existing packet paths:

```powershell
python runners/run_source_quality_state_assembler.py --queue ".\_test_runs\example_source_quality_queue.yaml" --output ".\_test_runs\example_source_quality_state_census.yaml"
```

The State Assembler surfaces packet existence, manifest inspectability,
report-skeleton state, visible stops, and operator-finalization requirements
per row. It does not discover sources, run capture tools, fetch data, score
source quality, auto-advance queue rows, or finalize `mini_god_tier_met`.

Use the Direct HTTP runner when one ordinary HTTP URL should be captured into
the same packet shape:

```powershell
python runners/run_source_capture_http_packet.py --url "https://example.com/page" --decision-question "What did the page return before the decision cutoff?" --cutoff-posture "pre-cutoff direct HTTP capture requested by operator" --output ".\_test_runs\example_source_capture_http_packet"
```

This runner is still deliberately narrow. It uses stdlib `urllib` only, follows
normal redirects, preserves the raw response body plus provenance-safe response
metadata, and fails visibly on timeout, DNS/TLS failure, empty-body response,
or byte-cap breach. It does not use browser automation, API SDKs, archive
retrieval, media fetching, scraper frameworks, proxy/auth/session injection,
ECR logic, Cleaning, Judgment, buyer proof, or commercial-readiness logic.

Use the Media / Asset runner when an operator already has explicit
source-meaningful asset URLs, such as image or gallery-frame URLs, and wants
them preserved into the same packet shape:

```powershell
python runners/run_source_capture_media_packet.py --asset-url "https://example.com/source-image.png" --decision-question "Which source-meaningful media asset was visible before cutoff?" --cutoff-posture "pre-cutoff explicit asset capture requested by operator" --output ".\_test_runs\example_source_capture_media_packet"
```

This runner is explicit-URL-only. It reuses the Direct HTTP helper, preserves
asset bodies plus provenance-safe metadata, writes mixed-success packets when
at least one asset is preserved, and carries failed assets as visible
limitations. It does not discover assets, parse galleries, parse HTML, recurse
through linked media, run OCR or image analysis, query archives, automate a
browser, call APIs, use scraper frameworks, inject auth/session/proxy behavior,
or perform ECR, Cleaning, Judgment, buyer-proof, or commercial-readiness logic.

Use the Archive.org runner when an operator wants archive availability metadata
and, when available, a selected Wayback snapshot body preserved into the same
packet shape:

```powershell
python runners/run_source_capture_archive_packet.py --url "https://example.com/page" --cutoff-timestamp "20240501000000" --decision-question "What archived source state was visible before cutoff?" --output ".\_test_runs\example_source_capture_archive_packet"
```

This runner distinguishes archive availability from archive-body preservation.
If availability metadata is preserved but no eligible snapshot or retrievable
body is available, the packet keeps that limitation visible. If availability
lookup itself fails and no metadata is preserved, the runner writes no normal
packet. Snapshot body retrieval reuses the Direct HTTP helper. It does not use
browser automation, Archive.org packages, API SDKs, scraper frameworks,
proxy/session behavior, archived-HTML meaning extraction, OCR, ECR, Cleaning,
Judgment, buyer-proof, or commercial-readiness logic.

Use the TikTok SCI admission runner when page-owned TikTok artifacts have
already been captured and need parser/sanitizer enforcement before packet
admission:

```powershell
python runners/run_source_capture_tiktok_video_packet.py --video-id "7629774409762442526" --video-url "https://www.tiktok.com/@funmimonet/video/7629774409762442526" --comment-list-json ".\_test_runs\tiktok_comment_list_sanitized.json" --video-item-json ".\_test_runs\tiktok_video_item_sanitized.json" --subtitle-webvtt ".\_test_runs\tiktok_subtitle.vtt" --output ".\_test_runs\tiktok_video_admission_packet"
```

This runner is the lean code-enforced slice only: it admits sanitized
single-video comment/subtitle/profile-list fields, keeps raw signed URLs,
cookies, tokens, storage-state, and raw response bodies out of the packet, and
prints the complete-lane note on successful runs and in `--help`.

Use the TikTok one-creator live runner when the page-owned artifacts still need
to be produced by the browser route. Cold agents should first open
`../docs/workflows/tiktok_cold_agent_capture_enforcement_goal_v0.md` and
`../docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md`; those
files bind the current blocker/action doctrine and no-solve owner-handoff
boundary. The runner writes sanitized staging JSON by default; add
`--admit-output` for a local SourceCapturePacket or explicit `--data-root` for
owner-authorized bronze/data-lake admission. The live runner chains the existing
TikTok batch admission gate rather than duplicating lake logic, and it does not
read ambient `ORCA_DATA_ROOT`.

When the named session profile selects Chrome CDP, this runner *reuses* an
already-bound visible retained Chrome profile and verifies the exact loopback
process binding before navigation; it does not cold-start Chrome itself. If no
bound endpoint is live, start one first with
`runners/ensure_source_capture_retained_chrome.py --session-profile <alias>`
rather than asking the owner to launch the browser by hand. The harness never
closes operator Chrome; an already-open profile without CDP fails visibly with
`BLOCKED_RETAINED_PROFILE_OPEN_WITHOUT_CDP`, and a CAPTCHA remains an owner
handoff.

```powershell
python runners/run_source_capture_tiktok_live_batch_probe.py `
  --creator-handle "funmimonet" `
  --creator-profile-url "https://www.tiktok.com/@funmimonet" `
  --video-url "https://www.tiktok.com/@funmimonet/video/7629774409762442526" `
  --state-label "<dedicated-tiktok-auth-state-label>" `
  --session-mode client_provided_session `
  --require-harness-proxy-posture no_proxy_profile_loaded `
  --allow-challenge-close-followthrough `
  --human-challenge-handoff `
  --output-dir ".\_test_runs\tiktok_live_funmi" `
  --admit-output ".\_test_runs\tiktok_live_funmi_packet"
```

The runner prints `tiktok_live_probe_summary_json=` lines after staging and,
when requested, admission. Use those typed summaries to distinguish staging-only,
local packet admission, bronze admission, owner-attention, and fail-closed
admission rejection before reading larger JSON files. `--data-root` is the
immediate bronze/lake path and should be used only when the owner explicitly asks
for it.

The complete TikTok lane still requires owner-authorized account posture,
creator batch cadence, projection bridging, and recon/playbook updates before
scale or promotion claims.

Use the Browser Snapshot runner when one supplied URL needs anonymous browser
rendering or screenshot preservation:

Install the optional browser dependency and Chromium browser binary before live
use:

```powershell
python -m pip install -e .[browser]
python -m playwright install chromium
```

```powershell
python runners/run_source_capture_browser_packet.py --url "https://example.com/page" --decision-question "What browser-rendered source was visible before cutoff?" --cutoff-posture "pre-cutoff browser snapshot requested by operator" --output ".\_test_runs\example_source_capture_browser_packet"
```

This runner preserves rendered DOM, visible text, a viewport screenshot, and
browser metadata into the packet shape. It defaults to a fresh anonymous/headless
browser context. For one supplied URL, operators may choose ordinary visible
browser mode (`--headed`), a local Chromium channel such as Chrome or Edge
(`--browser-channel`), and a bounded post-navigation settle delay
(`--settle-seconds`). It does not accept stored sessions, browser profiles,
cookies, credentials, storage-state files, anti-detect behavior, proxy behavior,
CAPTCHA solving, crawling, OCR, ECR, Cleaning, Judgment, buyer-proof, or
commercial-readiness logic.

Use the CloakBrowser Snapshot runner when one supplied URL needs anonymous
anti-blocking browser rendering because ordinary Browser Snapshot controls
(`--headed`, `--browser-channel`, `--settle-seconds`) are expected to fail or
have failed:

Install the optional CloakBrowser dependency before live use:

```powershell
python -m pip install -e .[cloakbrowser]
```

```powershell
python runners/run_source_capture_cloakbrowser_packet.py --url "https://example.com/page" --decision-question "What anti-blocking browser-visible source was present before cutoff?" --cutoff-posture "pre-cutoff CloakBrowser snapshot requested by operator" --output ".\_test_runs\example_source_capture_cloakbrowser_packet"
```

This runner preserves rendered DOM, visible text, a viewport screenshot, and
CloakBrowser method-provenance metadata into the packet shape. It uses an
anonymous non-persistent CloakBrowser launch and does not accept stored
sessions, browser profiles, cookies, credentials, storage-state files, proxy
behavior, CAPTCHA solving, crawling, Reddit target discovery, OCR, ECR,
Cleaning, Judgment, buyer-proof, or commercial-readiness logic.

Use the Authenticated Browser Snapshot runner when one supplied URL requires a
permitted manually bootstrapped browser session:

```powershell
python runners/run_source_capture_browser_session_bootstrap.py --login-url "https://example.com/login" --state-label "example-session" --session-mode "free_account_created_session"
python runners/run_source_capture_authenticated_browser_packet.py --url "https://example.com/page" --state-label "example-session" --session-mode "free_account_created_session" --decision-question "What authenticated browser-visible source was present before cutoff?" --cutoff-posture "pre-cutoff authenticated browser snapshot requested by operator" --output ".\_test_runs\example_authenticated_browser_packet"
```

The bootstrap command opens a headed browser for manual login and writes ignored
local Playwright storage-state JSON plus a session-mode metadata sidecar under
`_auth_state/`. After a permitted direct CloakBrowser profile warmup,
`run_source_capture_browser_user_data_export.py` can export the dedicated
ignored `_browser_user_data/` label to `_auth_state/` without re-running the
login flow; it accepts only labels plus session mode and prints no browser URL,
paths, cookies, or tokens. If the warmup used a proxy, the exported state may
later be tried in a non-proxy source-access run, but the egress switch can
still produce an invalid session or challenge; do not call that a clean
non-proxy capture proof until a non-proxy receipt validates under the normal
gates. The packet runner loads that state into a browser context,
refuses mismatched session-mode declarations, and preserves rendered DOM,
visible text, a viewport screenshot, and metadata. It records session mode and
state label, but never copies, hashes, prints, or preserves storage-state JSON,
sidecar metadata, cookies, tokens, or credentials. It does not automate
passwords, import browser profiles or raw cookies, bypass entitlement, use
anti-detect or proxy behavior, solve CAPTCHA, crawl, run OCR, ECR, Cleaning,
Judgment, buyer-proof, or commercial-readiness logic.

Dry-run packet outputs under `reports/source_capture/` are local review evidence
unless a separate fixture-admission decision says otherwise. They can include
machine-specific `original_path` provenance values and copied raw source files;
do not treat them as canonical fixtures merely because they sit under
`reports/`.

## Fragrance Review Coverage Runner

Use the fragrance review coverage runner when an operator already has saved
Judge.me widget JSON responses and optional PDP HTML for one fragrance product
and needs a no-network focused coverage receipt:

```powershell
python runners/run_fragrance_review_coverage.py --widget-response ".\_test_runs\luckyscent_widget_page_1.json" --pdp-html ".\_test_runs\luckyscent_pdp.html" --product-url "https://www.luckyscent.com/products/example-fragrance" --output ".\_test_runs\fragrance_review_coverage.json" --as-of-date "2026-06-29"
```

The runner preserves source-visible review row metadata, PDP JSON-LD aggregate
rating/count, selected/skipped row ids, rating/month/length/media/verified
counts, and route residuals. Only selected reader rows keep verbatim body text;
skipped rows keep metadata, body hashes, word counts, and skip reasons. Keep
outputs that contain review text in ignored/local paths unless a later lane
authorizes durable review-body storage.

This runner follows the focused review-coverage policy in
`forseti/product/spines/capture/core/source_families/retail_pdp/fragrance_purchase_review_focused_coverage_mgt_v0.md`.
It does not fetch network sources, discover products, crawl reviews, create
Source Capture Packets or durable Attachment Records, score review integrity,
label pain/pleasure/sentiment, or run ECR, Cleaning, Judgment, buyer-proof, or
commercial-readiness logic.

## Source Observability Runner

Use the source-observability report runner when an operator has already authored
local posture records and wants a structured list of visible capture
limitations:

```powershell
python runners/run_source_observability_report.py <records.yaml> --output <report.json>
```

The input must be local YAML or JSON containing either a list of
`SourceObservabilityRecord`-compatible records or a mapping with `records`.
Those records are operator-authored observations, not extracted source truth.
The report output is support evidence for reviewing source-language,
source-structure, archive-body, media, access, locator, and cutoff limitations.

The report is not capture validation, capture readiness, categorical ECR
receipt, Cleaning output, Judgment output, source acquisition, archive
retrieval, browser automation, or source-quality scoring. Do not treat it as a
required capture gate or as proof that the underlying capture is complete.

For record-authoring guidance, see
[`docs/source_observability_operator_records.md`](docs/source_observability_operator_records.md).

## Shared Helpers

`harness_utils.py` (package root) is the owning home for helpers shared across
this package — hashing, UTC timestamps, staged directory publish, scalar
coercion (`string_or_none` / `int_or_none` / `bool_or_none`), and version
constants. `runners/_scaffold.py` is the owning home for runner-CLI scaffolding:
new runners import `resolve_output_root` (the `--output`/`--data-root`/env
target resolution) and `exit_on_failure` (the exception→`parser.exit` exit-code
wrapper) instead of re-copying those blocks. Before writing a private helper in a `forseti-harness/` module,
check it; if the shared home already has it, import it. When touching a module,
migrate a stale private copy in the same work unit only when the bound change
already touches or depends on that helper contract (behavior-preserving only);
otherwise leave the unrelated migration for a separately scoped work unit. A
deliberately divergent copy stays, with a one-line comment naming the delta.
Deliberate exception:
the injected `sleep_fn` / `monotonic_fn` / `utc_now_fn` seams in the capture
modules are what make them testable without real time or network pacing — do
not remove them as bloat.

## Writing tests

Test-authoring discipline for this suite is bound in
`docs/decisions/harness_test_authoring_discipline_v0.md` (from the 2026-07-20
test-stock audit). In short: extend an existing parametrized table instead of
adding a near-duplicate sibling file; probe a hook/checker's exit-code contract
in-process via `runpy.run_path(..., run_name="__main__")` rather than a
subprocess spawn (real spawns only when the entrypoint itself is under test);
scope or share heavyweight fixtures so a caller that asserts on one record does
not materialize the whole seed; and give a validator's test file a roster check
that fails when a declared finding-code has no covering test. It is resident
discipline, not a CI gate, and sets no test-count target.

## Commands

Run the full suite with the committed dependency lock and test group (parallel;
`--dist=loadfile` matches CI's scheduling so a file's tests stay on one worker):

```powershell
uv run --locked --group test python -m pytest -n auto --dist=loadfile
```

Default validation for a change is the affected test files plus required CI for
the broad suite, per `.agents/workflow-overlay/validation-gates.md`; a full
local run is for cross-cutting changes or diagnosing a red CI, not routine
closeout.

Run the TR/Casetext plumbing fixture from this directory:

```powershell
python -m runners.run_case cases/plumbing/tr_casetext_2023_v0_14
```

The script-style entrypoint is also supported:

```powershell
python runners/run_case.py cases/plumbing/tr_casetext_2023_v0_14
```

If a score already exists for the same `(case_id, run_id, contestant_id)`, the
runner refuses to write a duplicate unless `--allow-duplicate-score` is passed.
Mapping-version mismatches are a separate override:
`--allow-mapping-version-mismatch`.

Build a local dry memorization-probe receipt from pre-supplied probe input and
response files:

```powershell
python runners/run_memorization_probe.py --probe-input <probe_input.yaml> --raw-response <raw_response.yaml> --output <probe_receipt.yaml>
```

This runner does not call a model, provider SDK, browser, network, search, or
participant packet. It only normalizes local inputs into the v0.14
`contestant_execution_isolation` receipt shape and applies local gate
interpretation. A clean gate still requires structural no-tools evidence under
the v0.14 no-tools execution contract; prompt-only "do not search" language is
not enough.

Run an explicitly authorized raw-API no-tools memorization probe:

```powershell
python runners/run_memorization_probe_raw_api.py --probe-input <probe_input.yaml> --output <probe_receipt.yaml> --provider <openai_responses|anthropic_messages> --api-url <provider_url> --api-key-env <ENV_NAME> --allow-live-provider-call
```

The raw-API runner uses no provider SDK and requires the live-call flag so an
operator cannot accidentally call a model while doing local validation. Clean
no-tools isolation is limited to the standard OpenAI Responses endpoint and
Anthropic Messages endpoint named by the runner; arbitrary proxy or provider
URLs are rejected for clean isolation. The runner rejects request bodies with
tool, search, retrieval, browser, file, attachment, workspace, system,
developer, or hidden-context fields, and the receipt `raw_response_hash` covers
the full provider response body. The runner is still only execution plumbing;
using it for a real probe requires separate owner authorization for the exact
model/case pair.

No-case provider smoke tests are also non-gate-clearing. Before passing
`--allow-live-provider-call` for a synthetic smoke test, follow
`../docs/research/judgment-spine/harness/v0_14/no_case_smoke_test_authorization_checklist_v0.md`
and capture the required out-of-band execution provenance. A smoke receipt must
not be cited as a clean memorization-probe pass for any real model/case pair.

## Generated TR/Casetext Scores

The runner writes score files under
`cases/plumbing/tr_casetext_2023_v0_14/scores/` and failure-event logs under
`memory/logs/`. Those paths are local generated outputs and are ignored by git.

If a generated score already exists for the same `(case_id, run_id,
contestant_id)` tuple, the runner refuses to write another score unless
`--allow-duplicate-score` is passed. Commit generated scores only under a
separate fixture-admission decision.


### Compact Phase A acquisition status

For routine operator or agent checks, use:

```powershell
python runners/run_phase_a_customer_evidence_pipeline.py status --run-root <run-root> --summary
```

`--summary` is available on every pipeline subcommand and preserves its exit code.
It reports acquisition status, candidate and queue counts, circuits, active work,
and paths to full details. Omit it for the existing full JSON response. Acquisition
completion does not imply evidence judgment or research readiness. `updated_at`
records the last state write; unchanged idle polls do not refresh it as a heartbeat.


Each Google or Reddit capture has a 300-second outer deadline, including runner
startup. This backstop allows headroom over the existing navigation, startup,
settle, and scroll budgets; it is not a new retry budget. An optional finite,
positive `capture_timeout_seconds` in each route config overrides it (set before
initialization, since running configurations are hash-bound). Operator interruption
cancels owned capture processes and waits for the workers before releasing the run
lock. Retained Chrome is outside the capture process group/job and stays open.
Timeouts and uncertain cleanup block the run and retain in-flight claims for the
existing resume inspection; they do not silently retry or credit partial output.


### Tombstone verification cost

Public lake reads still inspect the derived tree for tombstones. Within each
anchor, verification can reuse one raw packet under an 8 MiB retained-object
budget (body bytes plus manifest objects); target packets and oversized anchors
remain uncached. Every public read creates fresh caches and still validates all
encountered records. This reduces repeated raw reads, not the global directory
walk, and does not provide an atomic snapshot against concurrent physical tampering.
