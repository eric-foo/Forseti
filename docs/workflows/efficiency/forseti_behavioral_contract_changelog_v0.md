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
  - .agents/skills/forseti-loss-first-implement/SKILL.md
stale_if:
  - A named in-scope behavior changes owner, status, or operating shape without an update here.
```

## Reading rule

This is a router and history, never behavioral authority. Open and fresh-read
the current owner before acting. A historical PR explains a transition but
cannot override current source.

Snapshot basis: Forseti `main` at
[`536768a5`](https://github.com/eric-foo/forseti/commit/536768a58f77bbb1aa9559e2add8c600f2277231),
observed 2026-08-12. External Agent Workflow and installed resolver state
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

Fused, Assumption Gate, Implementation Scoping, Spec Writing, and
Micro-decision Locking are preserved. They are not erased, retired, or claimed
inferior by the owner preference.

The owner-authorized Forseti-local
[`forseti-loss-first-implement`](../../../.agents/skills/forseti-loss-first-implement/SKILL.md)
candidate tests the next hypothesis directly: keep one implementation method,
choose the decisive falsifier by maximum plausible loss, bind only applicable
authority/transition/closure invariants, and run no broader validation than the
repository requires. Its exposed-corpus 36-case replay used the fewest median
tokens but lost quality to Success Implement and latency to Full Chain. It
remains explicit-only and experimental; it has not demonstrated superiority on
an untouched holdout. See
[`loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md`](loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md).

The later exposed-corpus per-axis screen tested four latency, four token, and
four quality additions independently. None advanced. The token and quality
additions all produced a new critical defect on PR #1267, while the latency
additions each missed at least one frozen resource or quality gate. No new
skill was created and current behavior did not change. The next hypothesis is
an unrun causal test of baseline variance versus append-length interference
versus budget-neutral integration. See
[`success_implement_per_axis_mechanism_screen_2026_08_12_v0.md`](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md).

## Six separate evidence records

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
   the lowest median token count, Success Implement had the best quality, and
   Full Chain had the lowest median latency. This is regression evidence, not a
   new holdout. [Three-way record](loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md)
6. **Per-axis mechanism screen — 12 latency cases plus six-case token and
   quality Stage 1 screens.** All 12 narrow additions were rejected; no Stage
   2, combination, or deployment followed. [Per-axis
   record](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md)

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

- **2026-08-12 — Per-axis Success Implement additions all rejected.** Four
  latency mechanisms failed their frozen gates; four token and four quality
  mechanisms all introduced a critical defect on the broad PR #1267 case.
  Stage 2, combination, and deployment correctly did not run. Success
  Implement remains unchanged; the next proposed experiment isolates
  instruction-budget interference rather than adding another standing chain.
  [Per-axis record](success_implement_per_axis_mechanism_screen_2026_08_12_v0.md)
- **2026-08-11 — Loss-First Implement post-hoc replay did not support
  promotion.** Over the same exposed 36 cases, it saved median tokens but lost
  quality to Success Implement and latency to Full Chain. Ten stale/drifted
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
