# Subagent Model-Tiering Doctrine v0

```yaml
retrieval_header_version: 1
artifact_role: Orca decision/doctrine (delegation model-tiering)
scope: >
  How Orca chooses which model tier a spawned subagent runs on across Claude Code
  and Codex, so mechanical / ordinary delegable work defaults below the chief
  architect tier and the strongest tier is reserved for genuine judgment -- without
  over-restraining escalation.
use_when:
  - Spawning a subagent and choosing its model or runtime tier.
  - Authoring or reviewing custom agent definitions under `.claude/agents/`.
  - Deciding whether a delegated task needs the strongest available judgment tier.
  - Defining what source context a spawned subagent must load or receive.
authority_boundary: retrieval_only
open_next:
  - .claude/agents/worker.md          # Claude Code Sonnet default workhorse
  - .claude/agents/mechanical.md      # Claude Code Haiku trivial-rote tier
  - .agents/workflow-overlay/decision-routing.md   # delegation routing owner
  - .agents/workflow-overlay/prompt-orchestration.md # subagent source-readiness and return-shape owner
  - .agents/workflow-overlay/source-loading.md       # source-pack and capture-method load owner
stale_if:
  - Claude Code changes the subagent model-resolution order or the agent-definition `model` field.
  - Codex changes the `multi_agent_v1.spawn_agent` model override names or semantics.
  - Codex adds repo/project-level automatic source loading for spawned agents.
  - The tier mapping is re-decided by the owner.
```

## Problem this fixes

A subagent spawned via the Agent/Task tool with **no `model` set** falls through
to the parent's model. When the parent (main loop) is Opus, ordinary delegated
work — captures, builds, rote edits — silently runs on **Opus**, which is
expensive overkill. The failure is an expensive *default*, not a missing gate.

Codex has the same class of failure in a different shape. The
`multi_agent_v1.spawn_agent` tool inherits the parent model when `model` is
omitted, but it also exposes explicit model overrides. If the chief architect
does not classify the delegated task before spawning, mechanical work can run
on a judgment tier or judgment work can be accidentally underpowered.

## Assumption gate (Codex, observed 2026-06-16)

Before applying any Codex model override, check the actual spawn surface
available in the current session:

- **Subagent spawning available:** yes, via `multi_agent_v1.spawn_agent`.
- **Model override available:** yes, `model` is an optional override; omission
  inherits the parent model.
- **Observed Codex override values on 2026-06-16:** `gpt-5.3-codex-spark`,
  `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`.
- **Reasoning/service overrides:** the owner's 2026-08-30 high-only launch rule
  below governs all new agents and provider attempts, including in-session
  subagents. Omit service-tier overrides.
- **Stop condition:** if the tool schema no longer exposes these exact model
  names, do not invent replacements. Omit the model override or stop for an
  owner/tooling decision. The dated list above is a dispatch aid, not a durable
  availability claim.

## Decision

Tier by task, default cheap, keep Opus an easy opt-in:

- **Default delegated work → Sonnet.** Most delegable work (build to a stated
  pattern, capture/gather + verify, multi-step research, doc drafting) is
  Sonnet-grade. Route it to the **`worker`** agent type (pinned `model: sonnet`).
- **Trivial rote → Haiku.** Run-a-command, move/rename, precise find-replace →
  the **`mechanical`** type (pinned `model: haiku`).
- **Genuine judgment → Opus.** Novel design, compounding multi-step reasoning,
  subtle correctness on shared/contract-bearing surfaces, adversarial review →
  `general-purpose` (which inherits the main Opus tier) or an explicit
  `model: opus`. This stays available; it is a conscious choice, not the default.

**Do not collapse "mechanical" to Haiku.** Most delegated work needs Sonnet-grade
judgment (e.g. the Wayback capture builds had to pin domains, choose cutoffs,
handle rate-limits). Forcing Haiku there causes wrong results and redo — a false
economy worse than the Opus it avoids. Sonnet is the workhorse; Haiku is only
for genuinely trivial rote.

For Codex sessions, use the same three-way dispatch discipline, but treat model
names as a current tool-surface choice rather than durable doctrine:

- **Mechanical / trivial rote.** Use for exact, low-judgment work:
  grep/inventory, command output collection, line lookup, format-only edits,
  precise find/replace, or verification against explicit acceptance criteria.
  If the 2026-06-16 observed override set is still current, the preferred
  mechanical override is `gpt-5.3-codex-spark`.
- **Ordinary delegated work.** Use for bounded implementation, source synthesis,
  ordinary doc drafting, focused review, and anything that is not clearly
  mechanical or judgment-heavy. If the 2026-06-16 observed override set is still
  current, the preferred ordinary override is `gpt-5.4`.
- **Genuine judgment.** Use when the task materially depends on architecture,
  doctrine, irreversible tradeoffs, adversarial reasoning, cross-surface
  reconciliation, or subtle correctness on shared contracts. If the 2026-06-16
  observed override set is still current, the preferred judgment override is
  `gpt-5.5`.

Do not silently substitute `gpt-5.4-mini` for the ordinary Codex workhorse under
the 2026-06-16 observed override set. More generally, do not substitute any
unreviewed current-session model name merely because it looks adjacent. If the
expected override is unavailable, omit the override or stop for an owner/tooling
decision.

If a delegated task mixes tiers, split it when the outputs can be cleanly
separated. If it cannot be split without losing the point of the delegation,
route to the highest tier required by any material part of the task. If the
classification is merely uncertain, choose the ordinary workhorse; if the
uncertainty is about doctrine, lock-in, review authority, or irreversible
product/workflow impact, choose the judgment tier.

## Enforcement: pinned agent definitions, NOT a global cap

Verified Claude Code model-resolution order (highest → lowest):

1. `CLAUDE_CODE_SUBAGENT_MODEL` env var
2. per-call `model` arg on the Agent/Task tool
3. the agent definition's `model` frontmatter
4. inherit the parent (main loop) model

Enforcement is **(3)**: pin the model in the agent definition. Once work is
routed to `worker`/`mechanical`, the tier holds even if the orchestrator passes
no `model` — it can no longer silently inherit Opus.

**Rejected: `CLAUDE_CODE_SUBAGENT_MODEL` as a global default.** It sits at the
TOP of resolution and overrides even an explicit `model: opus` request, so
setting it to `sonnet` would make Opus subagents *impossible*. That is
over-restraint (it removes the escalation path), so Orca does **not** set it.
The control we want is "cheap by default, easy to escalate," not "block Opus."

**Hooks (optional, not adopted now).** A PreToolUse hook on the Agent tool can
inspect and even rewrite the model. Reserve it for a future *soft* signal (e.g.
log Opus spawns) if routing discipline proves insufficient — not a hard block,
which would re-introduce the over-restraint this doctrine avoids.

## Enforcement: Codex dispatch payloads, not hooks

In Codex, tiering is applied at the `spawn_agent` call boundary when delegation
is actually authorized. The chief architect classifies the subtask first, checks
the current tool surface, then sets the `model` override only when the selected
override is available and the classification intentionally differs from
inheriting the parent model.

Codex `agent_type` is role selection (`default`, `explorer`, `worker`), not the
model tier. Do not set `agent_type` to `default`, `null`, empty, or same-as-parent
to express model inheritance. Use `agent_type` only when the role matters:
`explorer` for specific read-only codebase questions, `worker` for bounded
repo-changing execution, and omit it otherwise.

This preserves `.agents/workflow-overlay/decision-routing.md` Subagent Runtime
Payload Safety: inherited runtime defaults are omitted fields; explicit
runtime fields are used only for a real override, never as decorative defaults.

## Source context is explicit, not implied by tier

Model tier, agent type, branch name, and lane label do **not** automatically load
Orca source context. A spawned subagent only has the context supplied by the
harness: forked thread history, explicit `message` / `items`, attached files, or
sources the prompt instructs it to read.

Therefore, the spawning chief architect must bind source readiness at dispatch
time whenever the subagent's output will be acted on. Do one of these:

- use `fork_context: true` only when the parent thread already loaded the
  controlling sources and the task can safely inherit that context;
- provide a compact source capsule with the controlling excerpts and paths; or
- require the subagent to read named sources first and report
  `SOURCE_CONTEXT_READY` before analysis, patching, or verdicts.

The source-loading rule is harness-neutral. In Codex it is especially important
because `agent_type: explorer` / `worker` is only a role selector and the
`model` override is only a runtime tier; neither one carries lane playbooks,
repo maps, or overlay files by itself.

For capture-spine activity, the dispatch must name the capture read pack instead
of relying on "capture lane" as a magic role. Start with:

- `AGENTS.md`
- `.agents/workflow-overlay/README.md`
- `.agents/workflow-overlay/source-loading.md`
- `docs/product/source_capture_toolbox/source_capture_playbook_v0.md`
- `docs/product/source_capture_toolbox/capture_recon_index_v0.md`

If the subagent has concrete runner inputs and is operating the Source Capture
Armory from `orca-harness/`, also require:

- `.agents/workflow-overlay/safety-rules.md`
- `docs/workflows/data_capture_spine_consolidation_map_v0.md`
- `orca-harness/docs/source_capture_agent_runbook.md`

This is not a prompt-artifact exception. Durable prompts, wrappers, handoffs,
reruns, and patch prompts remain owned by `workflow-prompt-orchestrator`. An
in-session subagent dispatch that only gathers, verifies, or performs a bounded
worker task may be written directly, but it still needs explicit source
readiness and the return-shape contract from
`.agents/workflow-overlay/prompt-orchestration.md`.

## Operating rule (for the orchestrator)

When spawning from Claude Code, default delegated work to `worker` (Sonnet). Use
`mechanical` (Haiku) for trivial rote. Reach for Opus (`general-purpose` /
explicit `model: opus`) only when the task earns it -- and when it does, do so
without hesitation.

When spawning from Codex, classify every delegated task before the call:

| Dispatch class | Codex override guidance | Use for |
| --- | --- | --- |
| `mechanical` | Use the current-session mechanical override; with the 2026-06-16 observed set, `gpt-5.3-codex-spark` | trivial rote, exact extraction, explicit verification, format-only work |
| `ordinary` | Use the current-session ordinary workhorse; with the 2026-06-16 observed set, `gpt-5.4` | default delegated work; implementation, synthesis, ordinary review |
| `judgment` | Use the current-session strongest judgment tier; with the 2026-06-16 observed set, `gpt-5.5` | doctrine, architecture, irreversible tradeoffs, adversarial reasoning |

Record the classification in the subagent prompt when it would help later
review: `dispatch_class`, `model_override`, and the one-sentence reason. Do not
turn that receipt into a runtime-model recommendation inside model-neutral
review-lane artifacts; this doctrine governs spawn-time operator/tooling
choice, not review-lane prompt content.

For Codex subagents whose output will be consumed by the chief architect, include
these dispatch fields unless the task is a trivial mechanical command:

```text
dispatch_class: mechanical | ordinary | judgment
model_override: <Codex model, if intentionally set>
source_context_mode: forked_context | required_reads | source_capsule
required_reads_or_capsule: <paths or capsule summary>
source_ready_signal: SOURCE_CONTEXT_READY before acting
return_shape: exact requested fields, file:line cites for load-bearing claims,
  unknown for absent facts
stop_conditions: <task-specific stops>
```

## Session-lane tier defaults (operator-owned)

The same tiering applies to whole delegated session lanes — the worktree lanes
the operator opens — not only to spawned subagents. Defaults, chosen by the
operator when opening the lane:

- **All new agents and provider attempts → `high` reasoning effort (owner rule,
  2026-08-30).** Explicitly select `thinking: high`, `reasoning_effort: high`, or
  the equivalent supported launch option. Never launch `xhigh` or higher; never
  inherit an unknown or higher effort. This includes diagnostic calls and cold
  receiving/handoff tasks. A full-history fork that cannot accept the override
  uses a bounded source capsule instead. Keep model tier selection separate.
  If the selected surface cannot establish `high`, stop and report that limit
  rather than silently substituting another effort. A move alone cannot change
  an existing task's effort; confirm or select `high` before resuming work.

- **CA / orchestrator threads → judgment tier (Opus).** Adjudication, doctrine
  authoring, cross-lane reconciliation, and anything that decides what is kept.
- **Home-side review lanes → workhorse tier (Sonnet).** Under the two-bar rule,
  cross-family discovery review runs on a de-correlated external model by
  construction, so the home-side lane's model never carries the discovery bar.
  Home-side review lanes — verification and post-patch rechecks,
  closure-of-findings, receipt/shape/inventory checks, and same-vendor
  sanity-tier code review — default to the Sonnet workhorse. This matches the
  `no_repo` post-patch recheck who-constraint in
  `.agents/workflow-overlay/delegated-review-patch.md` (same-family,
  lower/mechanical tier), extended to repo-mode verification lanes.
- **Escalate to the judgment tier** when the lane authors or adjudicates
  doctrine or contract-bearing surfaces, or the commission explicitly requires
  top-tier judgment. Escalation stays an easy conscious choice, never blocked.
- **Escalation guard:** a verification-tier lane that surfaces a new
  blocker/major outside its closure scope stops and returns it for a
  judgment-tier or freshly commissioned discovery pass; it does not adjudicate
  the new finding in-lane.
- Commissions may record `intended_tier: discovery | verification` as an
  operator_to_fill who-constraint so the operator knows which tier to pick when
  opening the receiving lane. Like `dispatch_class`, this is lane-time
  operator/tooling choice and must never appear as a runtime-model
  recommendation inside model-neutral review-lane artifacts.

## Non-claims

Advisory delegation doctrine. Not validation, readiness, a cost guarantee, or a
hard gate. It does not change any project's source hierarchy, review lanes, or
lifecycle authority; it governs only which model tier delegated subagents use.
It is not a Codex PreToolUse/PostToolUse hook and does not claim deterministic
runtime enforcement beyond the observed `spawn_agent` payload fields. Dated
model-name examples are not durable availability claims. It also does not create
automatic lane-playbook loading for Codex or Claude Code subagents.

The high-only rule does not retroactively change existing tasks or historical
receipts. The shared Codex provider runner rejects non-high launches before
attempt reservation; other launch surfaces remain actor-enforced under the
rule above. No global client configuration or service-tier setting is changed.

## Direction Change Propagation (2026-07-12: cold handoff effort)

```yaml
direction_change_propagation:
  doctrine_changed: >
    Newly created Codex cold receiving/handoff threads explicitly use high
    reasoning effort instead of inheriting or defaulting to xhigh; model choice
    remains unchanged unless separately requested. Existing-thread handoff
    cannot rewrite effort because that tool surface exposes no such field.
  trigger: workflow_authority
  controlling_sources_updated:
    - docs/decisions/subagent_model_tiering_doctrine_v0.md
    - .agents/workflow-overlay/decision-routing.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/prompt-orchestration.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: Already routes delegation and handoff behavior to the overlay.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: This is a spawn-time runtime rule, not prompt-body content.
  non_claims:
    - not a model override
    - not a service-tier override
    - not retroactive for existing threads
    - not enforceable through handoff_thread
```

## Propagation

- Added: `.claude/agents/worker.md` (sonnet), `.claude/agents/mechanical.md` (haiku).
- Pointer added in `.agents/workflow-overlay/decision-routing.md` (delegation routing owner).
- Amended for Codex: `multi_agent_v1.spawn_agent` assumption gate,
  mechanical/ordinary/judgment dispatch classes, dated observed override
  examples, and the recheck-at-dispatch rule.
- Amended for source context: lane/playbook reads are explicit dispatch inputs,
  with capture-spine required-read examples routed through source-loading.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Orca subagent dispatch keeps the mechanical/ordinary/judgment source-context
    discipline but treats Codex model names as current-session tool-surface
    choices, not durable doctrine; dated observed model names are examples that
    must be rechecked at dispatch time.
  trigger: workflow_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - docs/decisions/subagent_model_tiering_doctrine_v0.md
    - .agents/workflow-overlay/decision-routing.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/prompt-orchestration.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        Already routes delegated/cross-thread work to the overlay and does not
        carry concrete model-name policy.
    - path: .agents/workflow-overlay/README.md
      reason: >
        Already names decision-routing as the Cynefin/delegation owner; no new
        overlay section was added.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        Source-readiness and prompt/handoff mechanics are unchanged; this patch
        only clarifies dispatch-time model override selection.
  stale_language_search: >
    rg -n "gpt-5\\.3-codex-spark|gpt-5\\.4|gpt-5\\.5|model map|owner-selected Codex rule|model override"
    docs/decisions/subagent_model_tiering_doctrine_v0.md .agents/workflow-overlay/decision-routing.md
  non_claims:
    - not validation
    - not readiness
    - not runtime enforcement
    - not durable model availability
    - not automatic source loading
```

```yaml
direction_change_propagation:
  doctrine_changed: >
    Tiering now covers whole delegated session lanes, not only spawned
    subagents: CA/orchestrator threads default to the judgment tier; home-side
    review lanes (verification/recheck, closure-of-findings, receipt/shape
    checks, same-vendor sanity-tier code review) default to the Sonnet
    workhorse, since cross-family discovery runs on a de-correlated external
    model by construction; a verification-tier lane that finds a new
    blocker/major outside closure scope escalates instead of adjudicating
    in-lane; commissions may carry intended_tier as an operator_to_fill
    who-constraint.
  trigger: workflow_authority
  related_triggers:
    - review_authority
  controlling_sources_updated:
    - docs/decisions/subagent_model_tiering_doctrine_v0.md
    - .agents/workflow-overlay/decision-routing.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/delegated-review-patch.md
    - .agents/workflow-overlay/review-lanes.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - AGENTS.md
  intentionally_not_updated:
    - path: .agents/workflow-overlay/delegated-review-patch.md
      reason: >
        Its no_repo recheck who-constraint and model-ladder ownership already
        state the lower-tier verification pattern this section extends; the
        session-lane default points at it rather than restating it.
    - path: .agents/workflow-overlay/review-lanes.md
      reason: >
        Review-lane model-neutrality is preserved: this doctrine governs
        operator lane-time choice, never review-prompt model content; the
        two-bar rule wording is unchanged.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        No prompt mechanics change; intended_tier is a commission
        operator_to_fill field, not a new preflight field.
    - path: AGENTS.md
      reason: >
        Already routes delegation and doctrine work to the owning overlay
        sources; carries no model policy.
  stale_language_search: >
    rg -in "session-lane|sanity tier|verification/sanity|lower/mechanical|intended_tier"
    .agents/workflow-overlay/ docs/decisions/subagent_model_tiering_doctrine_v0.md AGENTS.md
  stale_language_search_result: >
    Executed 2026-07-02 after edits. Hits are the new section, its
    decision-routing pointer, and the pre-existing two-bar verification-tier
    language in delegated-review-patch.md and review-lanes.md ("lower/mechanical
    tier, e.g., Opus -> Sonnet") that this section formalizes — consistent, no
    fork or contradiction.
  non_claims:
    - not validation
    - not readiness
    - not a review-prompt model recommendation
    - no measured cost-savings claim
```
