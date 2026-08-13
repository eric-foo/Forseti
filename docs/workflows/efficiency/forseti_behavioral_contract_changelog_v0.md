# Forseti Behavioral Contract Changelog v0

```yaml
retrieval_header_version: 1
artifact_role: Historical provenance and current-authority router for named Forseti agent and workflow behavior contracts
scope: >
  Actor and workflow behavior governed by the Forseti kernel, overlay, and
  intentionally separate reusable workflow mechanics. Product, data, and
  runtime semantics are out of scope.
use_when:
  - Tracing why a current behavior exists or changed.
  - Finding the live owner before proposing another behavior change.
  - Separating owner preference, measured evidence, and current authority.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - docs/decisions/forseti_doctrine_index_v0.md
  - docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md
  - docs/workflows/efficiency/success_implement_per_axis_mechanism_screen_2026_08_12_v0.md
  - docs/workflows/efficiency/success_implement_instruction_budget_causal_screen_2026_08_12_v0.md
  - docs/workflows/efficiency/success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md
  - docs/workflows/efficiency/success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md
  - docs/workflows/efficiency/success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md
  - .agents/skills/forseti-loss-first-implement/SKILL.md
stale_if:
  - A named in-scope behavior changes owner, status, or operating shape without an update here.
```

## Reading rule

This is a router and history, never behavioral authority. Open and fresh-read
the current owner before acting. A historical PR explains a transition but
cannot override current source.

Snapshot basis: Forseti `main` at
[`cd49c600`](https://github.com/eric-foo/forseti/commit/cd49c600ee347bf6c25c50cc351a2c131c9fee04),
observed 2026-08-13. External Agent Workflow and installed resolver state
require their own fresh check when load-bearing.

## Current behavioral authority inventory

| Behavior | Status | Current owner | Controls |
| --- | --- | --- | --- |
| Smallest Complete Intervention, Problem Integrity, artifact-level SCI, ceremony debt, and downstream lock-in | Active kernel | [`AGENTS.md`](../../../AGENTS.md) | Narrowest complete owner-visible outcome, no speculative process or underfixing |
| Mini God Tier | Active owner-invoked lens | [`forseti_mini_god_tier_doctrine_v0.md`](../../decisions/forseti_mini_god_tier_doctrine_v0.md) via [`AGENTS.md`](../../../AGENTS.md) | Capability-target design with explicit residuals; no readiness claim |
| Project identity and unknown facts | Active overlay | [`project-authority.md`](../../../.agents/workflow-overlay/project-authority.md) | Forseti identity boundary and unknown-fact handling |
| Source hierarchy and doctrine-change propagation | Active overlay | [`source-of-truth.md`](../../../.agents/workflow-overlay/source-of-truth.md) | Precedence, conflict resolution, propagation |
| Source loading | Active overlay | [`source-loading.md`](../../../.agents/workflow-overlay/source-loading.md) | Task-shaped read packs and context economy |
| Decision routing, isolation, fast path, and delegated task topology | Active overlay | [`decision-routing.md`](../../../.agents/workflow-overlay/decision-routing.md) | Cynefin trigger, writable-root choice, bounded execution route |
| Artifact placement | Active overlay | [`artifact-folders.md`](../../../.agents/workflow-overlay/artifact-folders.md) | Accepted durable locations and new-artifact admission |
| Artifact roles | Active overlay | [`artifact-roles.md`](../../../.agents/workflow-overlay/artifact-roles.md) | Authority/evidence/handoff/router roles and freshness |
| Retrieval metadata | Active overlay | [`retrieval-metadata.md`](../../../.agents/workflow-overlay/retrieval-metadata.md) | Durable retrieval header and stale/open-next semantics |
| Prompt orchestration | Active overlay | [`prompt-orchestration.md`](../../../.agents/workflow-overlay/prompt-orchestration.md) | Prompt families, compact/full route, preflight, output and rerun lifecycle |
| Template selection | Active overlay | [`template-registry.md`](../../../.agents/workflow-overlay/template-registry.md) | Forseti-local prompt-template registry and fallback |
| Communication | Active overlay | [`communication-style.md`](../../../.agents/workflow-overlay/communication-style.md) | Owner-facing sequencing, closeout, handoff, and claim form |
| Validation and real failure visibility | Active overlay | [`validation-gates.md`](../../../.agents/workflow-overlay/validation-gates.md) | Evidence required before completion claims |
| Review lanes | Active overlay | [`review-lanes.md`](../../../.agents/workflow-overlay/review-lanes.md) | Reviewer authority, read/patch boundaries, output/adjudication |
| Delegated review-and-patch | Active explicit commission | [`delegated-review-patch.md`](../../../.agents/workflow-overlay/delegated-review-patch.md) | Bound different-family reviewer-patcher and home adjudication |
| Safety and authorization | Active overlay | [`safety-rules.md`](../../../.agents/workflow-overlay/safety-rules.md) | Protected actions, destructive boundaries, implementation authority |
| Skill adoption | Active overlay | [`skill-adoption.md`](../../../.agents/workflow-overlay/skill-adoption.md) | External source, shadow, collision, adoption, and project precedence |
| Loss-First Implement | Owner-authorized explicit-only candidate; post-hoc backtest did not support promotion | [`forseti-loss-first-implement/SKILL.md`](../../../.agents/skills/forseti-loss-first-implement/SKILL.md) via [`skill-adoption.md`](../../../.agents/workflow-overlay/skill-adoption.md) | Experimental mechanic: select the highest-loss false green and avoid unrequired broad validation; not the default implementation entry |
| Deletion evidence | Active decision/gate | [`deletion_evidence_doctrine_v0.md`](../../decisions/deletion_evidence_doctrine_v0.md) | Governed deletion evidence and fail-closed enforcement |
| Ontology/runtime drift checking | Active decision/gate | [`ontology_runtime_drift_check_contract_v0.md`](../../decisions/ontology_runtime_drift_check_contract_v0.md) | W2b leak-surface drift semantics |
| Repo-map architecture and reachability | Active owner-locked stack | [`forseti_repo_map_architecture_mgt_v0.md`](../../decisions/forseti_repo_map_architecture_mgt_v0.md) | Map/submap/header tiers, generated health, link coverage |
| Code-slop taxonomy | Active reference; binds no new gate | [`forseti_code_slop_taxonomy_v0.md`](../../decisions/forseti_code_slop_taxonomy_v0.md) | Names existing catch-layer decisions without duplicating them |

Product-proof semantics remain owned by
[`product-proof.md`](../../../.agents/workflow-overlay/product-proof.md) and are
excluded from this actor/workflow changelog.

## Success Implement: preference versus measurement

**Owner operating preference:** Success Implement remains the preferred single
entry for ordinary implementation because one invocation binds the visible
result, makes the smallest complete change, validates success and wrong-cause
paths, names one decisive falsifier for non-trivial work, and defers review
applicability to Forseti's controlling predicate.

**Measured result:** the 24-case confirmatory holdout did **not** show that
Success Implement beat the Full Chain. It had one accepted critical defect
versus zero and slower median latency, despite fewer major/minor defects and
lower median tokens. The candidate tested in that study was not deployed. See
[`success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md`](success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md).

That frozen `NO_WIN` remains the historical endpoint, but its controlling
critical assignment did not reproduce in a later re-adjudication: Success
Implement's critical moved from #1254 to #1303, and Full Chain gained a
critical at #1424. A concretized fixed-assertion severity screen later reached
`12/12` three-judge agreement; the identical-method builder-variance stage
stopped after one of three draws per case and remains unmeasured. Therefore
Success Implement is the deployment incumbent by owner preference, not a
validated strong baseline. See
[`success_implement_measurement_calibration_2026_08_13_v0.md`](success_implement_measurement_calibration_2026_08_13_v0.md).

Fused, Assumption Gate, Implementation Scoping, Spec Writing, and
Micro-decision Locking are preserved. They are not erased, retired, or claimed
inferior by the owner preference.

The owner-authorized Forseti-local
[`forseti-loss-first-implement`](../../../.agents/skills/forseti-loss-first-implement/SKILL.md)
candidate tests the next hypothesis directly: keep one implementation method,
choose the decisive falsifier by maximum plausible loss, bind only applicable
authority/transition/closure invariants, and run no broader validation than the
repository requires. Its exposed-corpus 36-case replay used the fewest median
tokens and Full Chain had the lowest latency. Success Implement's reported
quality lead is specific to that replay's post-hoc three-way scorer and is not
independent proof of baseline strength. Loss-First remains explicit-only and
experimental; it has
not demonstrated superiority on an untouched holdout. See
[`loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md`](loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md).

The later exposed-corpus per-axis screen tested four latency, four token, and
four quality additions independently. None cleared its frozen Stage 1 gate. The
token and quality additions all produced a new critical defect on PR #1267,
while the latency additions each missed at least one frozen resource or quality
gate. No new skill was created and current behavior did not change. See
[`success_implement_per_axis_mechanism_screen_2026_08_12_v0.md`](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md).

The follow-on P1/P2/P3 causal screen then ran two repetitions across four
cases. It supported baseline variance because unchanged Success Implement also
collapsed twice on PR #1267; it did not support append interference because
the required stable P1 contrast was absent. Budget-neutral obligation coverage
reduced criticals but increased majors, still collapsed in both #1267 runs,
and cost slightly more median tokens and time. It stopped at Stage A; Success
Implement remains unchanged. See
[`success_implement_instruction_budget_causal_screen_2026_08_12_v0.md`](success_implement_instruction_budget_causal_screen_2026_08_12_v0.md).

The next controller-owned boundary-probe diagnostic also stopped. E1 avoided
P1's one critical defect and stayed inside the resource guards, but both E1
runs still missed owner obligations, claimed broad completion, and failed the
independently executed probe. This rejects the exact external-probe mechanism
as a standing Success Implement addition; it does not reject repository-owned
task acceptance tests used as ordinary validation. See
[`success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md`](success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md).

The transparent E2 follow-on then improved E1's literal discrimination: all
three submitted repository-Python commands made the exact Greenhouse request
under the supported observation shim. E2 removed P1's one pooled critical,
lowered the owner-frozen weighted harm score, and used fewer median tokens, but
it accumulated four more majors and repeated broad completion collapse in all
three runs. The pre-registered gate rejected E2; Success Implement remains
unchanged. See
[`success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md`](success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md).

The E3 follow-on kept Success Implement unchanged and added a fresh
completion-admission check after the initial closeout. All three checkers
approved; oracle-backed decision adjudication said all three should have
returned `CONTINUE`; and no continuation or patch change occurred. E3's lower
weighted harm and resource medians therefore describe initial-run variance,
not a causal mechanism gain. Exact evaluator packets also disclosed arm paths,
so comparative quality scoring is de-blinded same-family evidence, not blind
proof. The exact checker is rejected; Success Implement remains unchanged. See
[`success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md`](success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md).

Current disposition: retain unchanged Success Implement as the deployment
incumbent, not as a validated strong baseline. P2 was inert. The exact P3, P4,
E1, and E2 packages did not clear their frozen advancement gates; those
package-level non-promotions do not establish that the mechanism families are
ineffective or that Success Implement is locally or globally optimal. E3 is
rejected independently because its checker was wrong `3/3` and caused zero
continuation and zero patch changes. P4 made
the two-run diagnostic lower in median comparison tokens and wall time but
worsened quality, still collapsed both #1267 completions, and repeated a
`missing_required_seam` regression. The result rejects the exact P4 wording
package on those two runs; it does not isolate the anchor or generalize across
cases or model versions. The exact controller-owned boundary probe is also
rejected after two runs. One transparent task-owned acceptance example was
subsequently tested as E2: it observed its matching request in all three
submitted Python commands but did not prevent broader premature completion. It
is rejected as a general Success Implement improvement. The later E3
fresh-context checker also failed: it admitted all three incomplete patches and
caused zero patch changes. No current behavior or authority changed. See
[`success_implement_goal_conservation_diagnostic_2026_08_12_v0.md`](success_implement_goal_conservation_diagnostic_2026_08_12_v0.md).

## Twelve separate evidence records

1. **Birth pilot — four cases/eight blinded implementations.** Task
   `019f7079-6084-7e90-95b8-1dce9348a275`; PRs
   [#485](https://github.com/eric-foo/forseti/pull/485),
   [#539](https://github.com/eric-foo/forseti/pull/539),
   [#555](https://github.com/eric-foo/forseti/pull/555), and
   [#896](https://github.com/eric-foo/forseti/pull/896); durable adoption record
   [#1104](https://github.com/eric-foo/forseti/pull/1104).
2. **Decisive-falsifier mechanism backtest — eight PRs.** Defect cases
   [#1111](https://github.com/eric-foo/forseti/pull/1111),
   [#1286](https://github.com/eric-foo/forseti/pull/1286),
   [#1396](https://github.com/eric-foo/forseti/pull/1396),
   [#1425](https://github.com/eric-foo/forseti/pull/1425),
   [#1460](https://github.com/eric-foo/forseti/pull/1460); clean control
   [#1402](https://github.com/eric-foo/forseti/pull/1402); mechanical controls
   [#1354](https://github.com/eric-foo/forseti/pull/1354) and
   [#1356](https://github.com/eric-foo/forseti/pull/1356). This supports the
   mechanism, not comparative superiority.
3. **Tuning set — 12 older cases.** One recognition-shape falsifier revision
   reduced accepted defects and both medians within tuning. Tuning selected the
   holdout candidate; it did not decide deployment.
4. **Confirmatory holdout — 24 recent cases.** Frozen rule result `NO_WIN`;
   candidate not deployed.
5. **Loss-First post-hoc replay — the same 36 exposed cases.** Loss-First had
   the lowest median token count, Full Chain had the lowest median latency, and
   that replay's post-hoc three-way scorer ranked Success Implement best on
   quality. This is scorer-specific regression evidence, not a new holdout.
   [Three-way record](loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md)
6. **Per-axis mechanism screen — 12 latency cases plus six-case token and
   quality Stage 1 screens.** None of the 12 narrow additions cleared Stage 1;
   no Stage 2, combination, or deployment followed. [Per-axis
   record](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md)
7. **Instruction-budget causal screen — four cases, two repeated three-arm
   blocks per case.** Baseline variance was supported, append interference was
   not supported, and budget-neutral obligation coverage failed its Stage A
   gate. [Causal-screen
   record](success_implement_instruction_budget_causal_screen_2026_08_12_v0.md)
8. **Owner-outcome-conservation diagnostic — one broad case, two repeated
   P1/P4 blocks.** P4 lowered median tokens and time but worsened pooled quality,
   failed coverage and collapse checks twice, and stopped before the contrasting
   exposed cases. [Diagnostic
   record](success_implement_goal_conservation_diagnostic_2026_08_12_v0.md)
9. **Controller-owned boundary-probe diagnostic — one broad case, two repeated
   P1/E1 blocks.** E1 removed P1's one critical defect and lowered two-run median
   resources, but missed obligations, collapsed completion, and failed the
   executable boundary probe twice. It stopped before contrasting cases.
   [Boundary-probe record](success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md)
10. **Transparent acceptance-example diagnostic — one broad case, three
    repeated P1/E2 blocks.** E2 passed the exact provider-request example three
    times, removed P1's pooled critical, lowered weighted harm and median tokens,
    but repeated broad completion collapse three times. The frozen gate rejected
    it. [E2 record](success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md)
11. **Fresh-context completion-admission diagnostic — one broad case, three
    repeated P1/E3 blocks.** Every E3 checker wrongly returned
    `ADMIT_COMPLETE`; no builder continuation or patch change occurred. The
    exact mechanism was rejected. [E3
    record](success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md)
12. **Measurement calibration — 12 fixed assertions plus an incomplete
    identical-method variance stage.** Three replacement judges agreed on all
    12 concretized severity ratings. The builder stage produced one valid draw
    on each of four untouched cases before the usage ceiling rejected the next
    four launches; the final four were not attempted, so builder variance
    remains unmeasured.
    [Calibration record](success_implement_measurement_calibration_2026_08_13_v0.md)

## External reusable mechanics and Forseti binding

| Mechanic | Reusable source | Forseti binding |
| --- | --- | --- |
| Success Implement | [Agent Workflow source](https://github.com/eric-foo/agent-workflow/blob/main/skills/candidates/promote-now/success-implement/SKILL.md) | Task-local mechanic; SCI, safety, validation, and review applicability remain Forseti-owned |
| Fused | [source](https://github.com/eric-foo/agent-workflow/blob/main/plugin/skills/fused/SKILL.md) | Explicit-only sequence coordinator; owns none of the lane decisions |
| Assumption Gate | [source](https://github.com/eric-foo/agent-workflow/blob/main/plugin/skills/workflow-assumption-gate/SKILL.md) | Triggered readiness ledger, not a standing prerequisite |
| Implementation Scoping | [source](https://github.com/eric-foo/agent-workflow/blob/main/plugin/skills/workflow-implementation-scoping/SKILL.md) | Read-only route mechanic |
| Spec Writing | [source](https://github.com/eric-foo/agent-workflow/blob/main/plugin/skills/workflow-spec-writing/SKILL.md) | Thin behavior contract only when invoked or returned to |
| Micro-decision Locking | [source](https://github.com/eric-foo/agent-workflow/blob/main/plugin/skills/micro-decision-locking/SKILL.md) | Triggered pre-edit lock; not automatic ceremony |
| Deep Thinking | [source](https://github.com/eric-foo/agent-workflow/blob/main/skills/candidates/promote-now/deep-thinking/SKILL.md) | Explicit reasoning lens; cannot expand the requested act |
| Delegated Review-and-Patch renderer | [source](https://github.com/eric-foo/agent-workflow/blob/main/skills/candidates/split-major/workflow-delegated-review-patch/SKILL.md) | Generic mechanics subordinate to the explicit Forseti commission owner |

## Material behavioral history

### 2026-08

- **2026-08-13 — Severity ruler reproduced; builder variance remains
  unmeasured.** Three isolated replacement judges agreed on all 12 fixed
  presence-and-severity assertions, including the three historical critical
  boundaries. The first judging trio was excluded for a packet-boundary
  violation. The subsequent identical-method stage completed only one of three
  required draws on four untouched cases before the account usage ceiling
  rejected the next four launches before model action; the final four were not
  attempted. New challenger studies
  remain suspended; no skill or runtime behavior changed. [Calibration
  record](success_implement_measurement_calibration_2026_08_13_v0.md)
- **2026-08-13 — Fresh-context E3 completion admission rejected.** Three
  repeated P1/E3 blocks on PR #1267 found every fresh checker approving an
  incomplete initial patch. Oracle-backed decision adjudication required
  `CONTINUE` all three times, but no continuation ran and no E3 patch changed.
  Lower weighted harm and resource medians were therefore initial-run variance,
  not an intervention gain. No standing checker or Success Implement change was
  installed. [Diagnostic
  record](success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md)
- **2026-08-12 — Transparent E2 acceptance example rejected.** Three repeated
  P1/E2 blocks on PR #1267 showed that a constrained transparent request
  example can elicit its matching boundary: E2 passed all three
  observations, removed P1's pooled critical, lowered the owner-frozen weighted
  harm score, and used fewer median tokens. It nevertheless left several major
  obligations incomplete and repeated broad completion collapse in every run.
  The pre-registered gate rejected E2; no standing acceptance lifecycle or
  Success Implement change was installed. [Diagnostic
  record](success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md)
- **2026-08-12 — Controller-owned boundary probe rejected.** Two repeated
  P1/E1 blocks on PR #1267 found E1 lexicographically better only because it
  avoided P1's one critical defect; E1 had two more majors, and both E1 runs
  still missed owner obligations, collapsed broad completion, and failed the
  controller's final executable probe. E1 used fewer median comparison tokens
  and time, but the mechanism-defining gates failed. Contrasting cases and all
  deployment correctly did not run; Success Implement remains unchanged.
  [Diagnostic record](success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md)
- **2026-08-12 — Exact budget-neutral P4 package rejected.** Two
  repeated P1/P4 blocks on PR #1267 found P4 lower in two-run median comparison
  tokens and wall time but worse on quality: two accepted critical defects
  versus one, more majors, two broad completion collapses, and a repeated
  `missing_required_seam` regression. The diagnostic stopped before its three
  contrasting exposed cases. A same-vendor adversarial audit then narrowed the
  causal claim: the experiment rejects the exact P4 package, not the anchor in
  isolation or every outcome-conservation mechanism. Success Implement and all
  runtime/install copies remain unchanged. [Diagnostic
  record](success_implement_goal_conservation_diagnostic_2026_08_12_v0.md)
- **2026-08-12 — Instruction-budget causal screen stopped at Stage A.** Two
  repeated P1/P2/P3 blocks on four cases showed that unchanged Success
  Implement itself can reproduce the broad PR #1267 completion collapse.
  Append interference was not supported. Budget-neutral obligation coverage
  reduced pooled criticals but increased majors, failed both #1267 obligation
  checks, and used slightly more median tokens and time. Stages B/C and
  deployment did not run. P1 remains only the least-disproven incumbent; P2
  and P3 are rejected, and no reliable Success Implement improvement is
  claimed. [Causal-screen record](success_implement_instruction_budget_causal_screen_2026_08_12_v0.md)
- **2026-08-12 — No per-axis Success Implement addition cleared Stage 1.** Four
  latency mechanisms failed their frozen gates; four token and four quality
  mechanisms all introduced a critical defect on the broad PR #1267 case.
  Stage 2, combination, and deployment correctly did not run. Success
  Implement remains unchanged; the next proposed experiment isolates
  instruction-budget interference rather than adding another standing chain.
  [Per-axis record](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md)
- **2026-08-11 — Loss-First Implement post-hoc replay did not support
  promotion.** Over the same exposed 36 cases, it saved median tokens while
  Full Chain had the lowest latency; that replay's post-hoc three-way scorer
  ranked Success Implement best on quality. That quality rank is
  scorer-specific, not independent baseline-strength evidence. Ten stale/drifted
  A/B worktree cases also established that future studies must freeze exact
  candidate diff bytes before judging. [Three-way record](loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md)
- **2026-08-11 — Loss-First Implement added as a Forseti-local candidate.** It
  converts the 36-case study's critical false-pass and latency-outlier lessons
  into an explicit-only source without replacing upstream Success Implement or
  claiming deployment. [Candidate source](../../../.agents/skills/forseti-loss-first-implement/SKILL.md),
  [adoption boundary](../../../.agents/workflow-overlay/skill-adoption.md)
- **2026-08-11 — Success Implement vs Full Chain returned NO_WIN.** The
  12-case tuning revision improved within-tuning performance, but the untouched
  24-case holdout found Success Implement worse on critical defects and median
  latency. The candidate was not deployed. [36-case record](success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md)
- **2026-08-08 — delegated review-and-patch retained on measured yield.** Ten
  of 11 primary episodes paid; no universal review expansion was installed.
  [PR #1456](https://github.com/eric-foo/forseti/pull/1456)

### 2026-07

- **2026-07-27 — durable prompt lifecycle closed:** delete consumed one-shots,
  retain with a return pointer when needed, or mark superseded.
  [PR #1372](https://github.com/eric-foo/forseti/pull/1372)
- **2026-07-26 — ineffective delegated-patch token gate retired:** vendor
  separation and write capability moved to the lane owner and home
  adjudication. [PR #1357](https://github.com/eric-foo/forseti/pull/1357)
- **2026-07-25 — SCI and Deep Thinking narrowed to the requested act.**
  [PR #1355](https://github.com/eric-foo/forseti/pull/1355)
- **2026-07-23 — created tasks gained one terminal return, not monitoring
  machinery.** [PR #1315](https://github.com/eric-foo/forseti/pull/1315)
- **2026-07-21 — Success Implement delegation became conditional on a named
  shared-assumption false-pass risk.**
  [PR #1274](https://github.com/eric-foo/forseti/pull/1274)
- **2026-07-19 — implementation handoffs inherited Success Implement.**
  [Agent Workflow PR #7](https://github.com/eric-foo/agent-workflow/pull/7)
- **2026-07-18 — Success Implement moved from local experiment to upstream
  reusable mechanic.**
  [Forseti #1104](https://github.com/eric-foo/forseti/pull/1104),
  [#1106](https://github.com/eric-foo/forseti/pull/1106),
  [Agent Workflow #6](https://github.com/eric-foo/agent-workflow/pull/6),
  [Forseti #1124](https://github.com/eric-foo/forseti/pull/1124)
- **2026-07-17 — standing mechanisms gained an SCI admission test.**
  [PR #1039](https://github.com/eric-foo/forseti/pull/1039)
- **2026-07-16 — SCI became the dominant kernel rule; standalone Operating
  Economy and Decision Priority were subsumed into SCI or overlay owners.**
  [PR #1019](https://github.com/eric-foo/forseti/pull/1019)
- **2026-07-16 — prompt preflight was cut to its measured core.**
  [PR #1004](https://github.com/eric-foo/forseti/pull/1004)
- **2026-07-15 — repo-changing work gained one-time writable-root binding.**
  [PR #980](https://github.com/eric-foo/forseti/pull/980)
- **2026-07-14 — Fused gained conditional cold-dogfood sequencing; Forseti
  later removed the standing obligation.**
  [Agent Workflow #3](https://github.com/eric-foo/agent-workflow/pull/3),
  [Forseti #921](https://github.com/eric-foo/forseti/pull/921),
  [#1039](https://github.com/eric-foo/forseti/pull/1039)
- **2026-07-12 — the decision-gate economics pilot stopped below its own
  comparison minimum.** [PR #873](https://github.com/eric-foo/forseti/pull/873)

### Earlier roots

- **2026-06-19 — Operating Economy introduced.** Its objective survives under
  SCI; the old standalone heading does not.
  [PR #283](https://github.com/eric-foo/forseti/pull/283)
- **2026-06-06 — Cynefin routing entered as an explicit layer.**
  [Introduction commit](https://github.com/eric-foo/forseti/commit/4ef9928427fa20f069aa4ab21f4596b56491d75e)
- **2026-06-05 onward — delegated review-and-patch evolved from overlay
  governance into a bounded code-capable sibling lane.**
  [Bootstrap commit](https://github.com/eric-foo/forseti/commit/c0294d9489aefe33f4fe2cf6e84fc714aa6aeb1c),
  [PR #425](https://github.com/eric-foo/forseti/pull/425)
- **2026-06-02 — Micro-decision Locking became reusable.**
  [Source commit](https://github.com/eric-foo/agent-workflow/commit/19be63410d2dd45f0b389a5c5b0f95fc18c18cb2)
- **2026-05-24/25 — simplest-sufficient routing and “smallest complete” entered
  upstream workflow vocabulary.**
  [Routing](https://github.com/eric-foo/agent-workflow/commit/db52d7999bc831d69e5def48a94ca03d45f64d5d),
  [terminology](https://github.com/eric-foo/agent-workflow/commit/90b6da0be5ed5c29c6fc6733b91e9051c254183b)
- **2026-05-24 — retrieval metadata entered the overlay.**
  [Commit](https://github.com/eric-foo/forseti/commit/fd14875db5585f961029c01123cba766efa4e93d)
- **2026-05-13 — initial overlay sources were bootstrapped.**
  [Commit](https://github.com/eric-foo/forseti/commit/59d8ca9bb7a93db482389d6badb19164803791ca)

## Update rule

Update this record when an in-scope behavior is adopted, materially changed,
superseded, or retired. Add the current owner and transition evidence; do not
copy the live rule here. Ordinary uses and wording-only edits do not earn rows.
