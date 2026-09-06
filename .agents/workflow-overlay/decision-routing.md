# Cynefin Routing Layer

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Lightweight Cynefin-based pre-planning router and receiver-mechanism selector for uncertainty-sensitive Forseti work.
use_when:
  - A material uncertainty could change decomposition, authority, source truth, or safe sequencing.
  - The user explicitly asks for Cynefin or uncertainty-regime classification.
  - Recovering a drifting or messy workstream before more agents act.
  - Selecting a writable receiver before delegated or parallel repo-changing work.
  - Moving from executing or repairing an accepted process to proposing or testing a method change.
authority_boundary: retrieval_only
```

This file owns Forseti's lightweight Cynefin Routing Layer. It regulates work
when uncertainty about decomposition, authority, source truth, or sequencing
could materially change the next move.

## Rule

Run the full router only when the task is plausibly `complex`, `chaotic`, or
`mixed or unclear`, or when a `complicated` task contains a concrete unresolved
choice that could materially change decomposition, authority, or safe sequence.
Clear work and ordinary complicated work with a bound outcome, authority, and
route proceed directly.

Use the smallest complete router. This is not a full Bayesian planning system,
audit log, review lane, validation gate, or project-management ritual. It is a
short preflight that constrains the next move.

## Before Method-Change Proposals Or Experiments

When moving from operating or repairing an accepted process to proposing or
testing a change to its evidence selection, comparison, retention, or completion
rules, first read the owning operating contract's supported route and recorded
rejected or deferred alternatives, including any conditions for reopening them.
An efficiency proposal or offline experiment crosses this boundary too; code
availability and run-local observations do not establish an approved method.
Apply the current user instruction and existing authority without inventing a
new approval requirement.

Use a targeted read at this transition, not a full-history search or a repeated
check for every batch. An execution fix that preserves the method follows the
bounded-change path below. This source check requires no new artifact or full
Cynefin router when the route is otherwise clear.

## Trigger Conditions

Run the full router when either condition is true:

- the user explicitly invokes Cynefin routing or asks for uncertainty-regime
  classification; or
- a material unknown could change the route, such as an unverified assumption
  that controls architecture or infrastructure, conflicting source/authority,
  an unclear ownership or dirty-state boundary, competing decompositions with
  different lock-in, or a drifting workstream with no visible bottleneck or
  stop condition.

Architecture, planning, scoping, delegation, cross-thread continuity, review,
patching, doctrine work, and messy worktrees are escalation cues because they
often contain those unknowns. They are not sufficient triggers by themselves.
If the outcome, authority, sources, touch points, and validation route are
already bounded, proceed without a full-router artifact. An explicit `/fused`
invocation supersedes the bounded-change fast path below for that work unit;
a continuation that only executes already-cleared fused lanes runs under the
fast path.

## Bypass Conditions

Do not run the full router for clear or ordinary complicated work whose route is
already bounded, including:

- tiny edits, typo fixes, or mechanical formatting;
- direct command answers;
- already accepted implementation steps with bounded touch points and validation;
- narrow doc cleanup where ownership is obvious;
- simple bug fixes with an obvious test path;
- bounded review, doctrine, delegation, or prompt work whose controlling source,
  authority, target, and stop condition are already known.

Do not emit a bypass receipt. Surface a routing assumption only when it is risky
or genuinely ambiguous under `AGENTS.md`.

## Router Output

When the full router triggers, use compact headed prose:

```text
Smallest complete outcome: What fully satisfies the request without extra scope.
Regime and why: Complex / Chaotic / Mixed or Unclear / materially unresolved Complicated.
Current bottleneck and riskiest assumption: The constraint and unknown governing WIP.
Allowed next move: The next probe, source read, decision, or bounded action.
Stop or pivot condition: The evidence that would make the current route wrong.
Disallowed next move: What must not happen next.
```

Keep this internal when it only regulates the current actor. Put it in chat or a
durable prompt when the route itself is decision-bearing, another lane must
inherit it, or the user asks to see it.

## Regimes

`clear`: the task is understood, bounded, and mechanically executable.
Use functional decomposition or direct execution.

`complicated`: the task needs expertise, source hierarchy, or layered ownership,
but the target can be reasoned through from current sources.
Use layer-based decomposition.

`complex`: key assumptions are uncertain, evidence could change the route, or
building first would create fragile infrastructure.
Use risk-first probes. Resolve the highest-uncertainty assumption before
expanding implementation or delegation.

`chaotic`: state is too unstable to plan safely, usually because scope, source
truth, repo state, or authority is disordered.
Stabilize first: classify dirty state, bind authority, narrow the target, or
name the hard stop before any broader task tree.

`mixed or unclear`: the request contains multiple regimes, or the regime cannot
be classified without first separating the work.
Split the task into regime-specific parts before planning. Do not force one
label when the first safe move is to separate the problem.

## Execution Contract

When the full router triggers, it must produce an allowed next move and a
disallowed next move before planning continues. The disallowed move prevents
spare capacity from becoming non-bottleneck work.

The smallest complete outcome is also load-bearing. It names what would satisfy
the actual request, so correct classification does not become permission for
extra cleanup, adjacent refactors, broader prompt sweeps, or infrastructure.

The bottleneck and stop-or-pivot condition must be concrete enough to govern
action. Do not write vague bottlenecks such as "uncertainty" or vague stops such
as "if it seems too hard." Name the specific unknown, evidence, failure signal,
owner decision, source gap, or boundary breach that changes the route.

For complex work, the allowed next move should normally be a probe, source read,
owner decision, scoped contract, or narrow adapter/surface step that resolves
the riskiest assumption. Do not estimate end dates or build infrastructure
around unproven assumptions.

For chaotic work, do not assign parallel work until the bottleneck is visible.
Idle agents are acceptable when non-bottleneck work would increase WIP or blur
claim boundaries.

## One-Time Writable-Root Binding

At the first repo-changing act, select and bind one effective target: neither
branch nor worktree for read-only work; a current-checkout branch for clean
solo/sequential writing; and a worktree off the required base for dirty-base,
concurrent, or independent work.

For Codex Desktop, launch each new concurrent repo-changing task directly in its
own small worktree. Do not launch new lanes from legacy or aggregate checkouts,
cache parents, or directories that contain multiple worktrees; those broad roots
can amplify Windows sandbox ACL setup latency. This is performance containment,
not a correctness or authority rule: launch-root mismatch alone remains not a
blocker. If a correctly rooted Desktop lane still stalls or needs sustained
shell-heavy parallelism, standalone CLI or WSL2 is an explicit fallback, not the
standing default.

### Task-Local Tool-Stall Circuit

After one silent sandboxed tool stall, open a circuit for that
tool-plus-permission route in the current task. Use a realistic,
operation-specific timeout. On Windows, absent stronger operation-specific
evidence, allow a full 60 seconds for reads or patches before declaring
`sandboxed_tool_stall`. A yielded or deferred running handle alone is not a
stall before that budget expires; give the owner a concise progress update
around 30 seconds while it continues. Longer operations such as tests keep
their operation-specific expected runtime and are not forced into the 60-second
budget. Wait at most once for any remaining original budget, then terminate the
call. Do not retry the same route merely because the command or conversation
turn changed.

If the stalled operation might have written, inspect only its intended targets
once. Retry a safe in-scope operation at most once through a distinct approved
route and reuse that route for the task. Stop when the mutation outcome is
unknown, target state drifted, another writer appeared, a real guard denied the
action, or the alternate route also stalls. A fresh task is a fresh route even
when carried context reports an earlier task's stall. Verify the final diff;
alternate-route completion is mitigation, not proof that the ordinary route is
repaired.

### Bounded-Change Fast Path

For a named handoff with a small candidate-authority set, one bound edit unit,
and known validation, use at most five latency-bearing rounds:

1. receiver instructions;
2. one read-only intake containing the handoff, bounded candidate authority,
   status/inventory, likely targets, edit-helper usage, and relevant untracked
   baseline, resolving authority and binding the edit only after that output;
3. one isolated mutation;
4. one ordered validation call that preserves each exit/output, runs focused
   before broad, and skips broad after focused failure; and
5. one read-only closeout containing diff check, exact diff, status, failure
   attribution, and untracked verification.

Never hide a retry or external action inside a phase. Do not use this fast path
when the intake cannot be safely bounded before launch.

The current actor may continue the same commissioned work unit directly in its
selected worktree after one fresh snapshot records the exact target path,
revision and dirty state, and whether another writer is active. Launch checkout
and target worktree need not match. Launch-root mismatch alone is not a blocker.
A separate receiver is required only for an independent concurrent actor or
after an observed tool, sandbox, hook, or guard denial proves the current task
cannot perform a required target operation.

For an `external_direct_write` receiver, controller identity and target-path
namespace are separate facts. The commission authorizes the bounded act; finding
the named effective target and verifying its revision, target set, write
capability, and writer isolation establishes the route. A `.codex`, `.claude`,
or other manager-prefixed worktree path neither grants authority nor disqualifies
an otherwise eligible controller. A prohibition on a Codex-managed *receiver
fallback* forbids replacing the commissioned different-vendor controller with a
Codex task; it does not forbid that controller from using the named target
worktree. Do not infer inability from the path prefix or launch root: preserve
and route only an observed access denial.

Reuse this binding through authoring, review, validation, commit, push, and
landing. Do not repeat root receipts, chat choreography, hook canaries, synthetic
write/index probes, or capability recitals while material state is unchanged.
Re-resolve only when the actor or target changes, revision or dirty state changes
materially, another writer appears, or a real required-tool failure invalidates
the binding. Preserve that failure.

Receiver classes remain available where another actor needs a binding:

- `codex_managed_worktree`: a new independent Codex task explicitly authorized
  and created in its managed worktree with the commission in its initial prompt;
- `external_direct_write`: an independent external controller verified once for
  its frozen target under exact or expressly permitted ancestor semantics,
  direct write capability, and no concurrent writer;
- `collaboration_same_root`: an in-session subagent inside the caller's writable
  root; naming another path cannot expand it; and
- `receiver_to_bind`: preparation-only until a concrete receiver is authorized.

For `codex_managed_worktree`, creation means invoking the Codex product's
new-task managed-worktree surface (currently `create_thread` with
`environment.type: worktree`); `git worktree add` may isolate the current actor
but cannot create that receiver. Only invoking the bound managed-task surface
consumes the one authorized receiver-creation attempt. A rejected
wrong-mechanism operation may be corrected once through the bound surface only
after a fresh read proves that it created no task, worktree, or Git metadata.
If either route may have created state, or its outcome is unknown or partial,
stop without retry.

An independent delegate writing a separate worktree needs its own capable
receiver. This does not apply when the current actor creates or selects isolation
for the same commissioned work unit. Stop or reroot only for ambiguous target
identity, revision mismatch, unexpected dirt, concurrent writing, an observed
required-tool denial or root-bound feature mismatch, or a protected-action or
server-side guard.

For a genuinely new, external, or changed receiver, record one compact
`receiver_binding`; unchanged same-lane prompts point to the active binding:

```yaml
receiver_binding:
  receiver_class: codex_managed_worktree | external_direct_write | collaboration_same_root | receiver_to_bind
  binding_state: receiver_to_bind | receiver_to_verify | receiver_verified | blocked
  launch_checkout: "<observed path | receiver_to_observe>"
  effective_target_worktree: "<observed path>"
  managed_starting_ref: "<bound ref, only before a managed task exists>"
  required_revision: "<commit>"
  revision_mode: exact | ancestor
  capability_proof: "<only when new or genuinely unknown>"
  no_concurrent_writer_state: "<required for an independent writer>"
```

`exact` means a clean worktree whose `HEAD` equals `required_revision`.
`ancestor` means a clean advancing lane where
`git merge-base --is-ancestor <required_revision> HEAD` succeeds. For a delayed
delegated review or review-and-patch commission against an advancing lane,
`ancestor` is the default unless the commission explicitly requires a frozen
historical diff or artifact. The receiver verifies ancestry and clean/no-writer
state, then records the current `HEAD` as `reviewed_revision` before source
review; that captured commit becomes the immutable review target. The original
`required_revision` remains the minimum lineage checkpoint, not the reviewed
byte identity, and the return records both revisions.

Uncommitted work is not bindable for an independent receiver: freeze it into a
commit before courier. Existing `exact` gates remain exact. After
`reviewed_revision` is captured, later descendant changes stay outside review
scope. If the author continues concurrently, the reviewer must use a separate
clean worktree at `reviewed_revision` and, when patching, its own review branch;
two writers must not share the advancing target worktree.

Creating a user-visible Codex task still requires explicit product/user
authorization. A visible instruction to create, start, spin up, or hand off to a
new managed task is sufficient. A durable commission may carry the bounded
`receiver_creation_authorization` owned by `prompt-orchestration.md`. Generic
`proceed`, ordinary implementation authority, and read-only/scoping/review work
do not create that authority; a task's mere existence is never authority.

### Created-Task Completion Return

When a user-visible Codex task is created and its result will return to the
creating source task, completion ownership remains with that source task. The
created task's initial prompt must name the source task and require exactly one
terminal return through `send_message_to_thread` after the receiver freshly
verifies its outcome. The return carries the created task's identity, terminal
state (`completed`, `blocked`, `failed`, or `needs_attention`), a result pointer
or concise result, and any user action needed. Do not rely on the owner noticing
completion in the sidebar.

This is resident task-API behavior, not a repository-state surface. Do not
create a polling loop, monitor task, automation, registry, repeated progress
callback, or standing completion surface solely for this return. If the product
exposes a native source-task terminal callback, use it instead and omit the
duplicate receiver message. A receiver that terminates before it can send
remains a product-level notification residual; do not claim the resident rule
covers that failure.

When a real pre-edit mismatch invalidates the binding, route to an already-
authorized capable receiver when one exists.
An already-authorized capable worktree-backed task is such a receiver. A valid
one-task creation authorization may be used without chat-double-asking. Return
`BLOCKED_RECEIVER_REROOT_REQUIRED` only when target identity, revision, writer
isolation, or required capability cannot be established,
no authorized capable route exists, or the one allowed creation fails. Capable
means able to perform the required operation against the exact target while the
state checks hold; it does not require launch-root equality.

### Multi-Task Conservation Fast Path

When one user-authorized work unit needs multiple actors, first separate
same-root collaboration from independent worktree ownership. Use in-session
collaboration subagents for actors that can safely share the caller's bound
root. Create user-visible Codex tasks only for actors that need independent
worktrees, durable user follow-up, or separate lifecycle ownership.

For `N` required independent receivers, authorize and launch exactly `N`
role-named tasks as one group. Give every member its complete
execution-authorized commission in the initial prompt; do not create
preparation-only members and then add a routine `READY`, `PAIR_RELEASE`, or
equivalent release turn. Launch all members before waiting on any one member.
Record observed creation and start timestamps when timing matters, but do not
require literal simultaneous release unless the commission identifies timing as
a load-bearing experimental variable.

The task is the conserved recovery unit. Resolve a member-local setup,
transport, VPN, path, hash, or ordinary preflight failure in this order:

1. continue or correct the existing task;
2. when its root is wrong but the task remains usable, move that same task to
   the intended managed worktree through the product handoff surface; then
3. replace only that member once when the task itself is unusable, preserving
   the group identity and every unaffected member.

A replacement inherits the failed member's role and frozen commission. Archive
the predecessor after the replacement is bound. Do not assign a new pair,
group, or attempt identity merely because one member needed recovery.

Restart the whole group only when a shared invalidator makes the existing
outputs incomparable or unsafe: cross-member contamination; a changed common
contract or controlled variable; a required revision change after evidence or
output was produced; or timing drift that the commission explicitly made
load-bearing. A member-local blocker, tool stall, route failure, VPN change,
wrong launch root, or recoverable preflight error is not a group-restart
condition. Superseded user-visible tasks are archived, and surviving tasks keep
stable, role-bearing titles so the authoritative set remains obvious.

This fast path conserves already-authorized tasks; it does not grant task-
creation authority. The authorization rules above still govern initial members
and the one allowed replacement.

The live-adoption canary remains documented in `.agents/hooks/README.md` only
for work commissioned to test hook adoption; ordinary work does not run it.

This rule does not authorize automatic task creation without product/user
authority, destructive Git, concurrent writers, ignored dirty state, weakened
revision pins, or bypass of protected-action or server-side guards.

## Enforcement Placement

Routing also governs *how* a rule is enforced, not only how the next move is
chosen: a load-bearing rule that is mechanically checkable at a tool boundary
belongs in a deterministic substrate (hook, gate, or checker) at that boundary,
not in an actor-carried instruction that fires only when the model attends to
it. This principle, the per-rule classification, and the active instances are
owned by `.agents/workflow-overlay/validation-gates.md` (-> "Enforcement
Placement") and
`docs/decisions/overlay_enforcement_placement_classification_v0.md`; reserve
resident instruction for genuinely judgment-based rules.

## Subagent Runtime Payload Safety

For forked-context subagents, inherited runtime defaults mean omitted fields.
Do not set `agent_type`, `model`, `reasoning_effort`, `service_tier`, or
equivalent runtime fields to `default`, `null`, empty, or same-as-parent. If a
forked spawn is rejected for explicit type/model fields, retry with only
`fork_context: true` and the task `message` or `items`; if an override is
required, use a bounded source capsule instead of full-history fork or stop for
the owner/tooling decision.

## Prompt Propagation

Repo-aware prompts, wrappers, handoffs, review prompts, patch prompts, and
reruns include Cynefin routing only when the full-router conditions above
trigger. Prompt artifacts should reference this file instead of restating the
router.

## Subagent Model Tiering

When delegating to a spawned subagent, choose the model tier per
`docs/decisions/subagent_model_tiering_doctrine_v0.md`. The same doctrine also
owns the session-lane tier defaults for delegated review lanes (its
"Session-lane tier defaults" section).

For every new agent, receiving/handoff task, or model-provider attempt, apply
the owner's high-only launch rule in that doctrine: explicitly select `high`,
never `xhigh` or a higher effort. Do not inherit an unknown or higher setting.
If a full-history fork cannot accept the required effort override, use a bounded
source capsule with explicit `high` instead. Keep model choice separate. Moving
an existing task does not change its effort; do not resume it without confirming
or explicitly selecting `high` on a surface that supports that setting.

In Claude Code, default delegable work to the Sonnet `worker` agent type;
trivial rote to the Haiku `mechanical` type; reserve Opus (`general-purpose`,
which inherits the main tier, or an explicit `model: opus`) for genuine
judgment. A subagent spawned with no model silently inherits the parent (Opus)
tier, so route to a pinned type to avoid paying Opus for non-judgment work. Do
not set `CLAUDE_CODE_SUBAGENT_MODEL` (it hard-caps all subagents and blocks
Opus escalation — over-restraint).

In Codex, classify the delegated task before the `spawn_agent` call:
mechanical/trivial rote, ordinary delegated work, or genuine judgment. Choose
any explicit model override from the current tool surface only after checking
that the name is actually available in the current session; otherwise omit the
override or stop for an owner/tooling decision. `agent_type` remains a role
selector (`explorer`, `worker`, or omitted), not the model tier. Do not turn a
dated observed model list into durable routing doctrine.

Model tiering does not imply source loading. A spawned subagent does not
automatically read lane playbooks or overlay sources because it is called a
capture worker, explorer, or judgment lane. For any subagent output the chief
architect will consume, the dispatch must provide forked context, a bounded
source capsule, or explicit required reads plus the source-readiness and
return-shape contract in `.agents/workflow-overlay/prompt-orchestration.md`.

## Orchestrator Context Economy

In a long-running orchestrator or Chief Architect thread, every token that
enters the context is re-read by every subsequent call: orchestrator cost is
context size times remaining calls, so bulk output that lands early is paid
for hundreds of times.

Dispatch, do not inline, any mechanical work loop expected to take more than a
few (~4+) tool round-trips whose success is verifiable by exit code, diff, or
test count — test-fix loops, batch normalizations, CI polling, bulk file edits.
First apply Receiver Mechanism And Write-Root Selection above: read-only or safe
same-root work may use a pinned `worker` or `mechanical` subagent (per Subagent
Model Tiering above), while an independent repo-changing lane uses a receiver
launched in its worktree or an independent external controller that completes
the two-root capability preflight. Give the selected receiver a narrow contract:
target path(s), exact commands, acceptance condition, and return shape. Bulk
intermediate output (test dumps, batch listings, poll output) stays in the
receiver; only a compact summary returns to the orchestrator context. This is a
heuristic for context economy, not a mechanical gate.

Judgment work — adjudication, doctrine wording, contract design, anything
where the orchestrator's accumulated context materially improves the output —
stays inline. The binding constraint on dispatch is judgment fidelity, not
token math.

## Non-Claims

Cynefin routing chooses a safe next-move posture. It is not review or proof that
the route will work, and it does not validate, establish readiness, authorize,
or promote the underlying work to source-of-truth status.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Codex-managed receiver creation now binds the product-managed task/worktree
    surface explicitly, distinguishes it from current-actor Git worktree
    isolation, and counts only a real managed-surface invocation as the single
    authorized creation attempt while preserving fail-closed handling for any
    unknown, partial, or state-producing outcome.
  trigger: workflow_authority
  related_triggers: [lifecycle_boundary]
  controlling_sources_updated:
    - .agents/workflow-overlay/decision-routing.md
  downstream_surfaces_checked:
    - AGENTS.md
    - CLAUDE.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/hooks/check_prompt_output_mode.py
    - docs/workflows/forseti_repo_map_v0.md
  intentionally_not_updated:
    - path: AGENTS.md and CLAUDE.md
      reason: >
        The kernel already routes receiver selection to decision-routing.md,
        and CLAUDE.md remains its import shim; duplicating mechanism details
        would create a second authority.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        It already requires the app-created managed worktree, forbids nested
        worktree substitution, and routes receiver selection to this file.
    - path: .agents/workflow-overlay/validation-gates.md and .agents/hooks/check_prompt_output_mode.py
      reason: >
        They already accept a managed receiver only after app creation and
        reject positive manual Git-worktree substitution; runtime attempt
        accounting depends on observed state and remains judgment-based.
    - path: .agents/workflow-overlay/source-loading.md and docs/workflows/forseti_repo_map_v0.md
      reason: >
        Their existing pointers already route receiver-mechanism decisions to
        decision-routing.md; no source pack or owner path changed.
  stale_language_search: >
    rg -n -i "codex_managed_worktree|managed[- ]worktree|manual.*worktree|git
    worktree add|one allowed creation|retry.*receiver|receiver.*retry|app-created"
    AGENTS.md CLAUDE.md .agents/workflow-overlay/source-loading.md
    .agents/workflow-overlay/prompt-orchestration.md
    .agents/workflow-overlay/validation-gates.md
    .agents/hooks/check_prompt_output_mode.py
    docs/workflows/forseti_repo_map_v0.md
  stale_language_search_result: >
    Existing live hits consistently require app-managed creation, accept a new
    receiver once after creation, or reject positive manual Git-worktree
    substitution; no checked surface conflicts with the new state-aware
    attempt-accounting rule.
  non_claims:
    - not validation
    - not readiness
    - not proof that a managed task was created
```
