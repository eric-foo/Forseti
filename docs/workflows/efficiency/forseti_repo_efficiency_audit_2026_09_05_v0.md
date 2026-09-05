# Forseti Repository Efficiency Audit — 2026-09-05

```yaml
retrieval_header_version: 1
artifact_role: Observed repository efficiency audit and advisory findings
scope: Repository coverage, measured local costs, historical finding revalidation, and bounded optimization candidates at c683477a.
use_when:
  - Choosing an evidence-backed Forseti efficiency or bloat reduction work unit.
  - Checking whether a July efficiency finding still applies.
  - Reproducing the dated repository census or offline performance probes.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/forseti_repo_efficiency_audit_2026_09_05_evidence.json
  - .agents/workflow-overlay/source-loading.md
```

## Outcome and boundary

The strongest opportunities are repeated work in scoped lake consumption,
transcript quote verification, validation discovery, and contradictory workflow
triggers. Blanket file deletion or instruction compression is not supported by
this audit. Many July recommendations have already landed or lost their premise.

This is the completed repository investigation and an advisory change queue;
it does not implement or authorize the proposed runtime, doctrine, security, or
retention changes. Each candidate below carries the proof needed before claiming
an improvement. Actual production savings, billed cost, and deployment frequency
remain unobserved.

Source snapshot: `c683477a5b6f0eb2998a3bac1d547ae92552a77a`, a clean worktree of
local `main`. All source line references below are at that revision. The original
planning checkout was detached at `e2e3a41b` with unrelated edits; its 3,835-file
inventory is not the audit baseline. The later observed `origin/main`
`a785f96a714a854c71bdf8223978fd2cee311170` adds the Phase A collection/consolidation
change, including source-loading and judgment code. This report is pinned
evidence, not a claim to cover every subsequently merged commit. Reconfirm the
owning source before applying a finding.

The existing July wave plan remains historical tracking evidence. This report
supplies the newer, explicitly scoped audit observations; it does not rewrite
frozen reviews, grant source authority, or declare every old item closed.

## Success contract and evidence

The authorized outcome was a full repository efficiency audit: account for each
major area, revalidate earlier material findings, measure plausible costs where
affordable, and produce actionable recommendations without sacrificing correctness,
provenance, failure visibility, or protected actions.

| Signal | Observation and near-miss rejected |
| --- | --- |
| Complete inventory membership | All 4,488 tracked files reconcile across area totals. An independent `git ls-tree -r -l` census agrees with the index/`cat-file` census on file count and 192,563,705 logical bytes. This rejects a vocabulary-limited or Markdown-only inventory. |
| Scratch stays outside source | 4,106 actual synthetic/audit JSON files under ignored runtime scratch contribute no indexed audit-source paths. The baseline is the pinned Git tree, not a physical directory crawl. |
| Costs have observable mechanisms | Nine scoped-pickup repetitions record actual JSON reads with scope held at one. Quote probes compare sampled outputs before reporting timing. ASR uses an explicitly fake dependency and claims constructor count only. |
| Measurements can fail | Decrementing one read count inside an already-admitted availability measurement makes the consistency check fail with `availability read-count mismatch`; the intact evidence passes. This validates evidence consistency, not the semantic completeness of a future optimization. |
| Historical claims are challenged | Revalidation distinguishes resolved, remaining, superseded, and unproven old items. Byte-identical snapshots are checked for distinct consumers rather than labelled disposable. |
| Failures and limitations survive | Raw gate exits, fixture warnings, first-read variability, scratch setup failures, and missing production observations remain in the evidence. No elapsed-time estimate is labelled a token or monetary saving. |

The adjacent `forseti_repo_efficiency_audit_2026_09_05_evidence.json` is a frozen
evidence companion: aggregate census, raw command results, synthetic samples,
source notes, and exact one-shot measurement source. It is not a standing tool,
required audit step, global telemetry system, or routine read-pack input.

## Coverage

Bytes below are indexed Git-blob sizes summed once per tracked path, including
duplicate paths. They are expanded logical bytes, not filesystem allocation,
packed history, bytes loaded into an agent, or tokenizer units.

| Area | Files | Logical bytes | Inspection depth and disposition |
| --- | ---: | ---: | --- |
| `docs/` | 2,484 | 119,022,686 | Complete inventory; workflow, prompt, map, review, historical-audit and selected retention consumers inspected. Research/capture bodies outside those questions remain metadata-only. |
| `forseti-harness/` | 1,538 | 62,771,228 | Complete inventory; executable paths across capture, ASR, cleaning/ECR, creator/judgment, lake/retrieval and scoring followed; bounded probes and five existing fixture modules executed. Not line-by-line semantic review of every module. |
| `forseti/` | 380 | 9,449,976 | Every spine and remaining product area inventoried; owning interfaces inspected; deeper CSB, capture, scanning, ECR/Judgment and Company Surface routing traced. |
| `.agents/` | 57 | 1,173,209 | Overlay/skill/tool boundaries and hook implementations inspected. |
| `.github/` | 12 | 93,942 | Workflow, helper and validation routes inspected; local hook commands timed. |
| Root files | 7 | 21,839 | Instructions, Git attributes/ignore rules, package update and structure configuration inspected. |
| `.claude/` | 5 | 19,299 | Tracked activation and skill-copy boundaries inspected. |
| `.codex/` | 3 | 10,811 | Tracked adapter/registration inspected; synthetic direct adapter events timed. |
| `.githooks/` | 2 | 715 | Pre-push and commit-message routes inspected. |
| **Total** | **4,488** | **192,563,705** | Every tracked top-level area accounted for. |

Product coverage includes all eleven spines: Capture (189 files), Judgment (31),
Data Lake (29), Foundation (24), Creator Signal (20), Scanning (16), Product Lead
(16), CSB (12), ECR (5), Cleaning (3), and Packing (3). Information, Beauty,
Fragrance, case families and the shared registry were also included. Schema and
fixture-configuration coverage is inventory/interface-level; it is not schema
semantic certification. Private configuration, credentials, sealed outcomes,
other worktrees' authored contents, and the external lake were not read. Worktree
and external-lake metadata do not constitute a content audit of those stores.

## Measurements

### Local validation and tool boundaries

All 24 CI-registered hook commands returned exit 0 within their 30-second child
timeouts. They ran sequentially on Windows/Python 3.12.7, with
`FORSETI_DIFF_BASE=c683477a5b6f0eb2998a3bac1d547ae92552a77a`, an empty source diff.
Sum of child wall times: **40.171 seconds**. These are single local samples;
filesystem warming, order and concurrent machine activity were uncontrolled.
They are not GitHub Ubuntu timings or predicted savings.

| Gate | Seconds | Decisive observation |
| --- | ---: | --- |
| Map links | 12.127 | C2 and C4 separately enumerate/read the Markdown corpus. |
| Silver lane registry | 9.704 | Recursive discovery filters excluded directories after traversal. |
| Source-input hashes | 6.200 | Discovers records before resolving the diff; finally checks 0 of 288 records. |
| Hash-pin freshness | 4.239 | Discovers pins before resolving the diff; finally checks 0 of 265 pins. |
| Remaining 20 commands | 7.901 | Raw results and exits are retained in the companion. |

The four largest account for **32.270 seconds / 80.3%** of the measured battery.
Map output retained 37 annotated nonresolving debt items; the Silver gate retained
an unresolved lane argument at `forseti-harness/ecr/lake.py:136`. These were
explicit non-gating output, not suppressed failures. Coupling strict skipped its
runtime tests because the fixed diff was empty.

Three direct, non-mutating Codex adapter samples returned exit 0: shell status
0.388 seconds, one patch path 0.474 seconds, ten patch paths 1.899 seconds. This
establishes direct invocation cost only. Tracked configuration is not proof of
current host adoption; an advisory observed during this task's scratch writes
also cautions against equating target-worktree configuration with host state.

Current CI can skip full pytest for classified docs-only PRs and runs it on main
pushes (`.github/workflows/ci.yml:42,152`). The lifecycle document's opening CI
description still says full suite on every PR (`docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md:113`).
Do not infer executable CI behavior from that older summary. This audit ran the
relevant offline fixtures; required CI remains the publication integration gate.

### Runtime probes

| Probe | Observation | Limit |
| --- | --- | --- |
| Scoped pickup, scope = 1 | At 100 / 1,000 / 3,000 available packets: exactly 100 / 1,000 / 3,000 JSON reads on all three repetitions; medians 0.0353 / 0.2007 / 0.5217 seconds. | First-read observations included 7.038s at 1,000 and 15.298s at 3,000. Synthetic test roots; no production extrapolation. |
| Quote verification, 5,000 cues / 100 quotes | Current median 2.405s; scratch shared-index median 0.03146s; sampled outputs equal. Smaller samples also agreed. | Alternative is a measurement probe, not a shipped or fully verified replacement. This is CPU/allocation work, not model-token savings. |
| ASR reuse | Five transcriptions constructed five model objects. | Fake `faster_whisper`; no real initialization time, memory, inference cost or concurrency behavior measured. |

Five existing fixture modules covering transcript extraction, anti-blocking HTTP,
Reddit API, captions and ASR passed with process exit 0 in 5.508 seconds. Existing
`datetime.utcnow` deprecation warnings are retained. The probe's initial wrong
import-root calculation and invalid obligation envelope failed visibly before
successful measures; they are recorded in `runtime_source_notes`.

### Context, tokens and workflow evidence

AGENTS plus overlay entrypoint occupy 14,637 bytes / 236 lines. The complete
overlay is 317,184 bytes / 4,959 lines, but is not a required read pack. Prompt
Preflight occupies 51 lines / 4,293 normalized-LF UTF-8 bytes. Existing targeted
read shapes remain the first applicable control (`.agents/workflow-overlay/source-loading.md:177`).
No current full-task token totals or task frequencies were observed.

Two cold source traces reached sufficient answers within the targeted budget:

1. Company Surface temporal authority: repo map -> Information boundary ->
   Company Surface ownership -> Silver mapping contract; four targeted document
   reads. Runtime `forseti-harness/data_lake/company_surface.py:551,562` confirms
   generated views are non-authoritative. No second-authority defect established.
2. JSG-01 state: repo map -> ECR submap -> unfreeze decision -> conductor gate;
   three targeted sources after the map. The route resolves UNFROZEN/evaluable,
   without authorizing a case run; the recurring read-pack contradiction remains
   finding A01 below. No elapsed-time benchmark was conducted for these traces.

The recorded August trim screen is relevant counterevidence to treating shorter
instructions as an efficiency win. This audit matched all 24 raw resource values
to the published arm columns and recomputed 3/12 lower-token pairs, median matched
token ratio 1.412737 and wall ratio 1.177375. These remain historical observations
under the published labels; independent arm assignment, patch quality, model
effects and billed cost were not revalidated. An initial assumption that `x`
always named the baseline failed before the evidence file was written; the final
recheck uses explicit published labels and preserves that limitation. Source:
`docs/workflows/efficiency/success_implement_hot_path_trim_screen_2026_08_13_v0.md:27,91`.

## Prioritized change candidates

Ordering weighs observed mechanism, recurring exposure, boundedness and risk.
It is a recommendation, not measured ROI or implementation authority. A01-A04
are the first complete units worth scoping; security and retention changes remain
separate choices with their own evidence requirements.

### A01 — Reconcile recurring workflow rules at their owners

**Structural, recurring; absolute cost unknown.** Source loading requires a
receipt for durable/cross-lane prompts (`.agents/workflow-overlay/source-loading.md:57`;
validation mirror `validation-gates.md:74`), while prompt orchestration exempts
eligible bounded routine prompts (`prompt-orchestration.md:27,236`). The same
source-loading file forces a capsule/new task above four artifacts (`:148`) but
says counts alone do not force a lane (`:596`). Its JSG-01 pack says FROZEN
(`:492`) against `docs/decisions/jsg01_unfreeze_decision_v0.md:37` and the
Judgment conductor (`forseti/product/spines/judgment/conductor/judgment_quality_promotion_operating_model_v0.md:209`).
The shared prompt behavior include broadens the source-readiness phase trigger
(`docs/prompts/templates/shared/forseti_prompt_behavior_contract_v0.md:26`) beyond
its owner (`.agents/workflow-overlay/prompt-orchestration.md:104`).

Smallest complete remedy: point each restatement to its owning trigger/state;
reconcile the validation mirror and shared include in the same unit. Verify a
bounded durable prompt, five small decisive sources, a genuine context-integrity
failure, a full reasoning pipeline, and the JSG route. Routine cases must avoid
extra ceremony; escalated portable-state and source-before-finding requirements
must still hold. Do not translate UNFROZEN into run authorization.

### A02 — Reuse transcript-local quote indexing

**Measured synthetic alternative; low/medium correctness risk.**
`forseti-harness/cleaning/transcript_product_extractor.py:92` rebuilds normalized
text and cue mapping per quote; mention parsing (`:215`) and rating validation
(`:179`) repeat it. The sampled reduction is documented above.

Build one index per transcript parse and share it across lookups. Verify exact
first occurrence, cross-cue spans, normalization, empty cues/quotes, bad timestamps
and rejected fabricated quotes; retain provider/lake output identity. Prove both
output equivalence and index-build count. The scratch implementation has not
passed that complete behavior matrix.

### A03 — Make scoped lake pickup scale with scoped work

**Measured operation count; medium freshness/integrity risk.**
`forseti-harness/data_lake/consumption.py:393` calls the full public snapshot even
for one packet; `data_lake/root.py:1186` reads every availability JSON. Cadence
consumers repeat scoped pickup (`runners/run_seam_cadence.py:411,651`).

Choose a validated cadence snapshot or selected-key checks only after binding
currentness semantics. Verify equality with existing public filtering for missing,
corrupt and tombstoned packets, root changes and concurrent arrivals, with operation
counts at growing corpus sizes. Disabling reconciliation is not a valid shortcut.

### A04 — Reduce validation discovery work while preserving findings

**Measured gates, partially unmeasured attribution; medium detection risk.**
`check_map_links.py:575,683,795` repeats Markdown enumeration/reads;
`check_silver_lane_registry.py:292` descends before excluding scratch/tests/caches;
`check_source_input_hashes.py:312` and `check_hash_pin_freshness.py:323` discover
the corpus before resolving the diff. All paths are under `.agents/hooks/`.

Share per-invocation map input reads while retaining independent predicates;
prune already-excluded Silver directories before descent; resolve the diff early
and short-circuit only a successfully resolved empty changed set. For nonempty
diffs, unchanged manifests may refer to changed targets, so changed-file-only
scanning is insufficient. Verify identical findings/exits/counters, malformed
changed data, changed referenced targets, deletions, unresolved bases, migration
redirects and excluded-subtree non-traversal. Re-measure matched cases after the
change; 32.270 seconds is current gate time, not proven avoidable time.

### A05 — Restore current-runtime output ignore rules

**Verified path behavior; small contained change.** `.gitignore:37` retains
legacy output rules while the live shorts writer uses its current harness
directory (`forseti-harness/youtube_capture/shorts_scroll_capture_v0.py:16,77,89`).
Current shorts, scores, memory-log and capture-report JSON paths all return
`git check-ignore` exit 1; current scratch and legacy shorts controls return 0.
The harness README still promises scores/logs are ignored (`:552`).

Reconcile current writer output directories and ignore entries. Verify intended
outputs are ignored, adjacent source/fixtures remain trackable, and tracked
historical material is unaffected. Use repository-only probes with
`git -c core.excludesFile= check-ignore --no-index -v` to avoid conflating the
inaccessible user-global ignore file with repository behavior. Do not untrack
existing content as part of this fix.

### A06 — Reuse ASR initialization within a bounded batch

**Constructor count proven; real cost unknown; medium resource risk.**
`forseti-harness/source_capture/transcript/audio_asr.py:81` initializes per call;
batch consumers include `runners/run_asr_transcript_catchup.py:523` and cadence
`:105`. Lazily reuse one model per batch/configuration. Verify constructor count,
cue/posture/provenance equivalence, changed model/compute settings, initialization
failure recovery and bounded memory/concurrency. Do not cache failed outcomes.

### A07 — Reconcile live execution routing and map-checker coverage

**Structural route omission and measured checker selection; medium authority risk.**
CSB `forseti/product/spines/commission_signal_board/spine.yaml:34` lists SERP Phase 2
then sealing, omitting final-corpus Semantic Evidence Integration required by its
README (`:113`), playbook (`workflows/commission_signal_board_playbook_v0.md:806`)
and runner (`forseti-harness/runners/run_phase_acquisition_seal_validation.py:4382`).
Replace the redundant sequence with its owner pointer unless a real machine
consumer requires an enum; then reconcile that consumer. A search finding no
Python reader is not proof of no consumer.

Separately, map checker discovery (`.agents/hooks/check_map_links.py:527`) includes
the central and ECR maps but excludes the registered Capture/Judgment consolidation
maps (`docs/workflows/forseti_repo_map_v0.md:146`). Explicit C1 execution found zero
broken targets in each excluded map. Include the existing registered set and seed
a missing link in an already-registered map to prove coverage. This is a coverage
gap, not an observed broken-link incident. Keep these two repairs separable.

### A08 — Keep the Codex security guard fail-closed while assessing batch cost

**Measured direct invocation; security-sensitive candidate.**
`.codex/hooks/forseti_guard_codex_adapter.py:72,124` launches a guard child for
each unique patch path. A single batch invocation could amortize launch cost,
but must reject any protected path and fail on child errors. Verify all payload
forms, move destinations, duplicate paths, mixed safe/protected paths and unknown
failures. Do not import the guard into shared helper code or bypass it. No host
activation or production timeout failure is claimed.

### A09 — Add a total metadata attempt deadline only with visible failure

**Source-visible residual; no hang reproduced.**
`forseti-harness/source_capture/transcript/youtube_captions.py:46` calls in-process
metadata extraction with a socket timeout, unlike the bounded caption/audio
subprocesses. A killable total-attempt subprocess can bound multiple socket
operations/retries. Verify a controlled stalled child terminates, success output
is unchanged, and error classification/child cleanup remain visible. This is the
still-valid RE-HARN-4b residual, not evidence of current dominant latency.

### A10 — Repair cold discovery and historical status without broad migration

**Structural; lower priority than measured runtime work.**

| Surface | Evidence and bounded remedy | Verification / risk |
| --- | --- | --- |
| Skill provenance | `.agents/workflow-overlay/skill-adoption.md:106` directs strict provenance to historical package 0.1.52 despite its runtime caveats (`:34,113`). Resolve the selected runtime package; retain the dated snapshot as history. | Different selected/recorded versions stay distinct; no mandatory global installation census for ordinary use. Actual installed mismatch was not inspected. |
| Shared template discovery | `review-lanes.md:181` duplicates five IDs; `template-registry.md:38` has eight; the capture commissioning plan separately binds a local template (`forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_commissioning_plan_v0.md:197`). Keep one inventory and delimit lane-local scope. | Cold discovery reaches both shared and local consumers without importing capture authority or model routing. |
| Completed Aphrodite handoff | `docs/prompts/handoffs/aphrodite_depth_layer_build_handoff_v1.md:5` still presents dispatch authorization; the current charter calls it historical (`forseti/product/spines/creator_signal/aphrodite_carveout_charter_v0.md:392`). Add an entry banner pointing to the current charter. | Direct arrival sees historical status before old authorization; no claim that D-1 readiness is established. Preserve historical links unless live routing requires repair. |
| Historical malformed retrieval entries | Four `open_next` entries in three Product Lead ICP/wedge artifacts retain prose as filename: target-selection brief `:22`, ratification runbook `:20`, Batch 0 brief `:26`. The actual parser reproduces it. | Delimit annotations with `#`; parsed paths resolve; old product direction is not promoted. Exact paths are under `forseti/product/spines/product_lead/icp_wedge/`. |
| Retail review design input | `forseti/product/spines/capture/source_families/retail_pdp/retail_pdp_review_capture_spec_v0.md:37` has Beauty/Judgment/batch-handoff consumers but no capture-index route. Add a labelled design-input pointer at the retail index. | Reach the design without searching its consumers; do not imply implemented capture capability. |

### Retain, measure first, or defer

- **Historical duplicates:** 117 identical-blob groups represent 4,920,068 excess
  logical bytes (2.56%); review-input groups account for 2,497,251 bytes. Migration
  snapshots and no-repository review bundles have distinct provenance/consumer
  needs. There are no exact whole-file duplicate groups internal to the harness.
  Neither fact proves absence of near-duplicate code. Do not delete snapshots or
  distinct fixtures to improve a storage statistic.
- **Tracked inbox:** 40 files / 21,692,284 bytes are tracked despite the existing
  ignore entry. Individual capture admission/retention was not adjudicated. A
  consumer-aware disposition is needed before removal; another ignore rule cannot
  untrack them. No tracked precompact filename remains.
- **CSB document size:** rules/prompt are 1,861/1,934 lines with 66 matching lines
  in blocks of at least eight. The standalone prompt is a distinct consumer; the
  repo-aware path also reads a 1,839-line playbook. Map duplicated explanations to
  consumers before subtraction; token benefit remains unmeasured. Never replace
  a required standalone body with inaccessible repo pointers.
- **Scanning proposal pins:** four renamed source pins remain mismatched in
  `forseti/product/spines/scanning/scan_core/forseti_demand_scan_core_spec_v0.md:36,48,51,57`.
  Reconcile semantics when the rich schema is next commissioned; mechanical
  repinning could launder changed or suspended product bindings.
- **Already efficient or intentional:** incremental retrieval reuses unchanged
  bodies and avoids no-op publication; creator audience prompts already deduplicate
  and pack evidence; acknowledgements suppress unchanged extraction; duplicate
  diagnostics are not healthy-path quadratic joins. Same-host waits are explicit
  access policy (90-second default / ten-job cap), not removable idle time.
  Optional/staged LinkedIn, ASR and scoring surfaces must not be deleted as unwired.
- **Guard isolation:** shared hook helpers already exist; the hard guard's local
  copy avoids an import-failure dependency. Broad selftest-body coverage remains
  partly unproven; commission actual security-case coverage only if that distinct
  assurance outcome is wanted, rather than adding a universal second battery.

## July findings revalidated

Source: `docs/hygiene/efficiency_audit_wave_plan_v0.md`. Statuses below describe
the identified premise at the pinned source. An old checklist with no precise
per-ID target cannot support a fabricated closure claim.

| Old group | Current disposition |
| --- | --- |
| HOOK-1/2/3/4/5/7/8 | Source repair or retirement confirmed: path normalization, product/map paths, six edit advisories, duplicate CI command and Stop hook are already addressed; dormant claim-checker compatibility code remains. |
| HOOK-6/9/10 | Selftest coverage partial; helper consolidation partial with deliberately differing resolvers; hard-guard isolation retained. |
| CER-1/3 | Repeated review mechanics and conflicting enum/receipt defaults materially repaired. |
| CER-4/5/6 | Prompt-family navigation omissions remain low impact; template inventory conflict remains; alias retirement is verification-bound, so calendar deletion is not justified. |
| OVL-6 / T1; Batch 0/1 | Standing inline-receipt/pilot collection retired. Other OVL grouped duplication is materially reduced, but unspecified individual IDs remain unproven. A01 records current contradictions. |
| APH-HAND-1/2/3/5, APH-CORE-2 | Delivered/stale banners, shipped reference, fence and v1-pointer repairs present. APH-HAND-1 map-row closure was not independently established. |
| APH-HAND-4 | Dead historical pointer persists; active-commission premise superseded. Retire at entry rather than revive the packet. |
| APH-RSCH-1/3/4/5 | README routing, design/field-map pointers, extraction completion and stale ontology banner repaired. |
| APH-RSCH-2/7 | Two grade updates verified; unspecified third site and dormant/split target remain unproven. |
| APH-IMPL-1/3/4 | Heartbeat key/receipt pointer repaired; similar recomputation retains meaningful field differences and no measured benefit. |
| RE-HARN-1/2/3/4/4b | Error handling, package declarations and subprocess deadlines present; metadata total deadline remains. Fixtures passed; wheel build not revalidated. |
| RE-HARN-5/6/7/8/9/10 | Shared recursive validator now exists; ordering/integer behavior intentional; blanket unwired/deletion premise rejected; reconciliation flag reachable; small enum helpers remain without measured bottleneck. |
| NAV-1/2/3/4/7/8 | Central map reduced to 284 lines / 2,482 words; selected routes meet budget. No general closure claim from two samples. NAV-5 repeated navigation remains lower priority. |
| RE-CAP-1/3/4/6/7/8 | Missing README repaired; Armory catalog pointer improves duplication; substrate-specific indexes retained; retail design route gap remains; unspecified migration/deletion proposals unproven. |
| RE-CSB-2/3/4/5/6 | Standalone duplication and pins remain; role-specific engagement boundaries retained; retirement banner fixed; unspecified remaining target unproven. |
| REF-1/2/3/4/5/6/7/11 | Malformed historical entries remain; hardware-area row repaired; consolidation-map discovery gap remains; “intentionally uncreated” parser limitation has no observed current use in searched surfaces. |
| DEC-1/2 | Doctrine-index route and retired-pointer annotation repaired. |
| DUP-1/2/3/4/5 | No case for stripping headers. Constant/delta ownership improved; shared-contract residual remains. Twenty-six migration indexes retain distinct purposes; ten coexisting numeric-version stems do not prove deletion candidates. |

## Reproduction, publication checks and remaining limits

Use the evidence companion only when checking a specific measurement. Its
`reproduction_sources` contains the exact scripts as UTF-8 plus SHA-256. Extract
them to the recorded scratch layout in a worktree at the audit SHA, inspect
machine-specific paths/interpreter settings, and run with bounded child timeouts.
The runtime script creates synthetic test-mode data; it is not suitable for a
production lake. Timing will vary. The full 1.48 MB per-file inventory was left
in task scratch; compact area/extension/section totals are retained, and the Git
revision reproduces complete membership without a new repository registry.

Observed audit validation: independent census and aggregate reconciliation
passed; seeded existing-row mismatch rejected; actual scratch exclusion passed;
24 hook commands exited 0; five existing runtime fixture modules exited 0.
Publication checks apply to the final changed artifacts and are reported in the
PR/closeout, rather than being inferred from the earlier empty-diff gate run.

The remaining observation gaps are full-task and delegated-token accounting,
current model effects, cold/resumed task latency distributions, live review/handoff
traces, real browser/ASR/model timings, production lake scale/frequency, GitHub
runner phase timings, near-duplicate code analysis, packed Git history, and
individual historical retention admissibility. Reusing raw provider telemetry
where available is preferable to inventing a general measurement service.

This report is sufficient to choose and scope bounded changes. It is not a
performance release, permission to weaken a gate, an exhaustive semantic code
review, or proof that every proposed optimization preserves its consumers.
