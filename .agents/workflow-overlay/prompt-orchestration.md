# Prompt Orchestration

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Prompt artifact families, receiver routing, output modes, preflight fields, and prompt validation gates.
use_when:
  - Creating or reviewing Forseti prompt artifacts.
  - Checking prompt output mode, preflight, or review-report rules.
  - Dispatching cross-lane or repo-changing work to a receiver with a matching write root.
authority_boundary: retrieval_only
```

This file defines Forseti's lightweight prompt-orchestration layer: Forseti-owned prompt mechanics, output modes, preflight, and validation gates, without importing `jb` project policy and preserving Forseti's explicit-authorization boundary for implementation and runtime work.

**Routine read shape** (owned by `.agents/workflow-overlay/source-loading.md`,
Targeted Read Protocol): for routine prompt authoring, read the "Forseti Prompt
Preflight" section below plus the single section for your prompt family.
Lane-scoped delegated review-and-patch prompt authoring also reads "Lane-Scoped
Delegated Patch Prompt Default" below and the targeted commissioning sections
named in `delegated-review-patch.md`; delegation alone is not a full-file-read
trigger. A full-file read is for a prompt matching the **Full orchestration**
predicate below, and for editing this contract.

## Forseti Prompt Preflight

Routine Forseti prompts apply this core inline — no skill reload. For an
ordinary, already-scoped, single-target prompt, this core is the complete
preflight contract; it does not inherit the Escalated Preflight Fields or require
a `forseti_start_preflight` receipt. Review Prompt Defaults and Output Modes still
govern when their task-specific triggers apply. The field vocabulary, per prompt:

1. **Output mode** — exactly one of `chat-only` · `file-write` · `review-report` · `paste-ready-chat` · `patch-queue`, plus its write/report destination.
2. **Template kind** — the bound template from `.agents/workflow-overlay/template-registry.md`, or `none`; template targets are prompt-shaping labels, never runtime-model routing.
3. **Edit permission · targets · branch** — `read-only` | `docs-write` | `patch-only` | `implementation-authorized`; target files or dirs; workspace, branch, and dirty-state allowance when repository state matters. Planning or scoping is a phase, not an authority downgrade: preserve `implementation-authorized` when the commissioning instruction grants it, and apply the receiver-creation clause below when that commission selects a not-yet-verified Codex managed receiver.
4. **Reviews** — findings-first by default; bind any formal verdict, severity, or patch queue explicitly; no runtime-model recommendation, ranking, or implication.
5. **Doctrine change** — name the controlling source and propagation route when
   the prompt itself changes durable doctrine. Evidence belongs in the
   resulting PR/closeout by default; do not add a prompt-local receipt unless a
   distinct future consumer requires it
   (`.agents/workflow-overlay/source-of-truth.md`).
6. **Destinations** — the input prompt source the receiver treats as run-authoritative (canonical artifact path, lane PR body/comment, or ignored scratch path), and the exact output-artifact path it writes when the mode writes a durable artifact.

**Default elision.** A prompt states only fields whose value differs from the
named default; an omitted field asserts that default. Defaults: template kind
`none`; reviews findings-first with no formal verdict, severity contract, or
patch queue bound and no runtime-model routing; doctrine change `none`. Fields
1 and 3 are always stated. Field 6 is stated when the prompt is handed to
another model, agent, thread, or worktree, or when the mode writes a durable
artifact; otherwise it is elided. Elision never overrides an applicable
trigger: a prompt needing a non-default value states that field explicitly.

**Constants by pointer, deltas inline.** Repo-constant values — intake reads,
external-source boundary, environment baseline, retrieval-header defaults,
delegate lifecycle hard stop, de-correlation commission constants — are owned
by `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`. A prompt
that relies on one cites that artifact instead of restating it; restating a
constant owned there in a new or materially touched prompt is a prompt-quality
defect. Exception: an operator-couriered cross-vendor delegate prompt is
written self-contained for its external receiver and restates the
delegate-facing constants (`environment_baseline`, `lifecycle_hard_stop`,
`decorrelation_commission`) inline; that restatement must stay faithful to the
owning artifact, and every other constant stays pointer-cited. Per-prompt deltas — revision pins, named targets, repository-state
allowance, workspace root, validation route, and any content hashes required
outside the couriered repo-bound receiver rule below — are always stated
inline and never replaced by a pointer. Routine prompts state only the
non-default core above; do not add unused field placeholders or a start
receipt for form completeness. The Prompt Validation Gates below are applied
by the author before use; the prompt body does not carry a validation receipt,
gate checklist, or self-graded gate result. Fused and genuinely escalated
prompt work author through `workflow-prompt-orchestrator` and use the
escalated contract below. A lane-scoped delegated review-and-patch prompt uses
the compact default below when its eligibility conditions hold; delegation or
patch authorization alone does not escalate it.

## Source Boundary

Forseti-specific facts, product constraints, artifact paths, review lanes, validation gates, and safety rules must come from `AGENTS.md`, this overlay, or accepted Forseti docs named in `.agents/workflow-overlay/source-of-truth.md`. Prompt mechanics come from those same sources; see Escalated Preflight Fields below when the routine core is insufficient.

Prompt-policy, handoff, wrapper, review, output-mode, or execution-contract
changes that alter durable agent behavior are doctrine-changing when they touch
product doctrine, architecture doctrine, workflow authority, validation
philosophy, review authority, output authority, or lifecycle boundaries. They
must follow the Doctrine Change Propagation Contract in
`.agents/workflow-overlay/source-of-truth.md`.

Product-proof prompts and customer-discovery prompts must read
`.agents/workflow-overlay/product-proof.md` when they define buyer
qualification, trust objections, disqualifiers, kill criteria, pull grading, or
graduation rules. Do not redefine trust-objection semantics locally when the
overlay applies.

`prompt_orchestrator.yaml`, `product-ultraplan.yaml`, and `feature-ultraplan.yaml` are non-executable queue records unless later accepted source creates real workflow skills and Forseti validates adoption. Do not create `SKILL.md`, install skills, or copy `jb` templates from Forseti prompt-orchestration work.

## Prompt Orchestrator Binding

```yaml
prompt_orchestrator:
  source_loading_policy: .agents/workflow-overlay/source-loading.md
```

All Forseti prompt-orchestrator work must use the source-loading policy above; do not substitute generic, `jb`, plugin, or installed-skill defaults.

## Source-Gated Method Contract

Repo-aware prompts that orchestrate one or more workflow methods as an explicit
reasoning pipeline over task sources must separate method reference loading from
method application. An eligible **Lane-Scoped Delegated Patch Prompt Default**
may point to its already-bound review lane or skill as routing shorthand: the
receiver still reads the operating instructions and real target sources before
forming findings, but the prompt need not require the named
`REFERENCE-LOAD`/`APPLY` phases or a `SOURCE_CONTEXT_READY` phrase. Adding a
multi-method pipeline, Mini God Tier, or another full-orchestration condition
re-enables this contract.

Use these terms precisely:

- `REFERENCE-LOAD` a method: read the method or skill instructions as
  procedural guidance only. The receiver may prepare neutral source-reading
  questions or checklists, but must not use the method to analyze, frame,
  critique, rank, synthesize, decide, or recommend.
- `SOURCE-LOAD`: read the task-specific source material and build the working
  source context under `.agents/workflow-overlay/source-loading.md`.
- `SOURCE_CONTEXT_READY`: declare that the required source context has been
  loaded, or declare `SOURCE_CONTEXT_INCOMPLETE` with missing sources, source
  gaps, excluded sources, and conflicts.
- `APPLY` a method: use the method to analyze, frame, classify, reason,
  evaluate, synthesize, decide, recommend, or produce findings from the loaded
  source context.

Required sequence when this contract triggers:

1. Read authority and operating instructions.
2. `REFERENCE-LOAD` required method or skill instructions.
3. Do not `APPLY` any method yet. Before source readiness, only neutral
   source-reading lenses are allowed.
4. `SOURCE-LOAD` task-specific source material.
5. Declare `SOURCE_CONTEXT_READY` or `SOURCE_CONTEXT_INCOMPLETE`.
6. Only after that declaration, `APPLY` the methods to the loaded source
   context.
7. Synthesize and verify against the source context.

Before `SOURCE_CONTEXT_READY`, a prompt must not ask the receiver to produce a
problem frame, architecture recommendation, review finding, option ranking,
root-cause claim, verdict, conclusion, or recommendation unless the method
itself is the source-loading task.

Generated prompts should avoid vague instructions such as "use these skills"
before source loading. Use explicit wording such as:

```text
REFERENCE-LOAD the following method instructions. Do not APPLY them yet. Use
them only to prepare a neutral source-reading lens. After task sources are
loaded and SOURCE_CONTEXT_READY is declared, APPLY the methods to the loaded
source context.
```

Subagents, model-facing prompts, and blind contestant prompts for which this
contract triggers must satisfy the same sequence. Do not send such a subagent
only the method and question when the task requires source-backed reasoning;
provide the same source pack or a bounded source capsule, or require the
subagent to perform its own source-readiness gate.

For an orientation or research subagent whose output returns to an agent, bind
the return shape, not just the source side. Require a terse, schema-bound verdict
— the exact fields named in the dispatch prompt, one line per field, a `file:line`
cite for every load-bearing claim, and `unknown` for an absent field — not a
prose dump. For an execution or source-changing subagent — one that edits,
installs, commits, pushes, or opens a PR — extend that return with
lifecycle-verification fields: branch, base and commit SHA, push/PR state, and
`merged` state, plus a per-surface change list carrying one `file:line` cite
each, so the dispatching CA can verify the durable target on a fresh read per
`AGENTS.md` rather than trust a `done`; a raw diff dump is not a substitute (it
is a prose dump in another form), and `merged` must reflect observed state,
never an assumption. Source-readiness stays governed by the rule above and
`.agents/workflow-overlay/source-loading.md` (the load-side owner); here the
spawning CA names that load in the dispatch, escalates minimally, and validates
the return on receipt: reject or re-prompt a non-conforming or citation-less
reply rather than consuming it. "Returns to an agent" covers any output an agent
will act on, summarize, or route — even output later shown to a human; the only
exception is a deliverable meant directly for a human with no agent acting on it.
The return dimension is distinct from subagent source-readiness (above) and from
forked-context runtime-payload safety (`decision-routing.md`).

For a subagent that introduces or materially changes a validation hook, checker,
or CI gate, bind a validation-probe timeout in the dispatch and return contract.
The subagent must smoke-run the new or changed command under a child-scoped
30-second timeout before any raw full-run, repeated retry, or completion claim.
If the smoke probe times out, the subagent stops and returns
`VALIDATION_HOOK_TIMEOUT` with command, cwd, touched files, and observed process
state; it must not invoke the same hung command again. The 30-second limit is a
hang detector for new/custom validation surfaces, not the timeout for known
repo-wide gates or CI jobs. After the smoke probe passes, run the normal required
gate with its ordinary timeout. Cleanup may target only a process tree launched
by the current actor; otherwise stop for owner/tooling intervention rather than
killing inferred unrelated system processes.

## Project Template Registry

Forseti-local prompt templates live under `docs/prompts/templates/`.
The active Forseti template registry is
`.agents/workflow-overlay/template-registry.md`.

The registry binds template kinds, template targets, output modes, and template
paths for Forseti. Template targets are prompt-shaping labels only; they are not
runtime model routing. Check the registry before using any generic
prompt-orchestration template.

## Supported Prompt Families

| Family | Purpose | Default artifact destination | Default output mode |
| --- | --- | --- | --- |
| Product planning | Frame product bets, evidence standards, kill criteria, and handoff boundaries | `docs/prompts/product-planning/` | `chat-only` or `file-write` |
| Feature planning | Turn an accepted product bet into evidence-producing capability plans | `docs/prompts/feature-planning/` | `chat-only` or `file-write` |
| Deep reasoning | Compare options, downgrade weak candidates, preserve assumptions, and recommend | `docs/prompts/deep-thinking/` | `chat-only` |
| Implementation handoff | Prepare a source-changing unit after implementation is explicitly authorized | `docs/prompts/handoffs/` | `file-write` |
| Review | Ask a read-only or patch-authorized reviewer to inspect artifacts | `docs/prompts/reviews/` or `docs/review-inputs/` | `review-report` |
| Rerun or patch | Retry an unresolved finding without reopening settled decisions | `docs/prompts/reruns/` or `docs/prompts/patches/` | `patch-queue` |

Typed child folders under `docs/prompts/` may be created when the first prompt of that family is authored. Source-changing handoff prompts may target implementation only when the current turn or an accepted handoff explicitly authorizes bounded implementation; otherwise they must target documentation or overlay work only.

Goal-fitness-judged source-changing work must bind a concrete goal and observable success signal before edits begin; technical or consistency-judged work is exempt; when ambiguous prefer binding a pointer but do not block absent the trigger. Owning decision: `docs/decisions/work_unit_fitness_reference_v0.md`.

Prompt templates may also use `paste-ready-chat` when the intended output is a
single prompt, wrapper, or handoff body meant to be pasted into another model,
agent, thread, or worktree.

## Author Through The Prompt Orchestrator

Every durable Forseti prompt, handoff, wrapper, rerun, or patch prompt applies the
prompt contract; authoring one that skips it is a prompt-quality defect even when
the surface text looks complete — the defect is the skipped contract, not the
surface. The contract is applied at two depths, with the compact delegated path
as an unnamed specialization of routine depth:

- **Routine prompts** apply the **Forseti Prompt Preflight** core (above) inline — no
  skill reload. The core fully satisfies the contract for an ordinary,
  already-scoped, single-target prompt; it owes no escalated fields or durable
  start receipt solely because it is repo-aware.
- **Lane-scoped delegated review-and-patch prompts** use the compact default
  below when eligible. Delegation, adversarial wording, patch authorization,
  executor-ready wording, multiple named files in one bounded technical diff,
  or a high-stakes label alone is not an escalation trigger.
- **Full orchestration** applies when explicitly invoked by `/fused` or
  owner-invoked Mini God Tier, or when the prompt genuinely needs a portable
  no-repo source capsule, multiple independent receivers or output lifecycles,
  or resolution of material authority, target, dirty-state, or output-routing
  ambiguity before it can be used safely. Reusable, canonical, novel,
  cross-lane, source-heavy, doctrine-changing, high-stakes, or first-of-kind
  labels do not escalate by themselves. When those prompts are otherwise
  bounded, use the routine core plus the targeted family section.

An unchanged same-lane prompt points to the active one-time writable-root
binding in `decision-routing.md`; it does not repeat root, capability, or writer-
isolation details. New/external receivers and changed bindings carry the exact
details required below.

### Implementation Commission Receiver-Creation Clause

Every durable or cross-recipient commission with edit permission
`implementation-authorized` that selects a new `codex_managed_worktree` and may
begin in a task that is not the receiver must make the task-creation request
explicit in the visible commission. Include this bounded block next to that new
receiver's single `receiver_binding` receipt. A prompt continuing the active
binding includes neither block merely for lifecycle continuity. The current
actor selecting or creating a Git worktree for the same commissioned work unit
is not a new receiver and continues there unless an actual required capability
is denied.

```yaml
receiver_creation_authorization:
  authorization: create_exactly_one_fresh_codex_managed_worktree_task
  condition: current_task_not_receiver_verified
  managed_starting_ref: "<bound ref>"
  required_revision: "<commit>"
  revision_mode: exact | ancestor
  initial_prompt: this_frozen_commission_verbatim
  dispatch: immediate_same_turn
```

This block is the commission's explicit user request to create at most one task;
`implementation-authorized` by itself is not task-creation authority. When the
condition is observed, create and dispatch that one managed-worktree task in the
same turn with the frozen commission as its initial prompt, then stop repo-
changing work in the original task. Do not ask for a confirmation phrase. If
creation fails or the created receiver fails its bound preflight, return the
observed blocker and do not create a second task unless the commission is one
member of an explicitly user-authorized multi-task group governed by the
conservation fast path below.

When the created receiver's result will be consumed by the source task, its
frozen initial prompt also carries the one-shot completion-return contract from
`decision-routing.md` -> **Created-Task Completion Return**. This is inherited
behavior, not a new commission field or receipt. Omit it only when the created
task is intentionally user-owned with no source-task consumer, or when the
product supplies the native source-task terminal callback named by that
contract.

The block is commission-local, conditional, and single-use. It grants no
standing task-creation permission and must not appear in a truly read-only,
scoping-only, or review-only commission. Planning or scoping inside an
implementation-authorized commission does not change its declared authority:
route and status output must retain the implementation authorization. The
status `current_turn_authorization: read_only_scoping_only` is valid only when
the current user instruction or accepted handoff is actually read-only; it is a
prompt-quality defect when emitted merely because planning or scoping happened
before the authorized implementation.

### Multi-Task Commission Fast Path

Apply the group-level conservation rule in `decision-routing.md` whenever one
visible user instruction authorizes multiple Codex tasks. Each independent
member still receives its own single-use `receiver_creation_authorization`
block and complete role-specific commission. Launch the required members as one
batch before waiting, and assign each a unique title in the form
`<work unit> — <role>`. Keep the controller's member-to-role mapping transient;
do not create a registry, manifest, wrapper artifact, or standing coordination
surface solely to manage the group.

The initial prompt authorizes execution. Do not default to a preparation-only
turn followed by `READY`, `PAIR_RELEASE`, a mutation probe, per-member
recomputation of a shared prompt hash, or another controller release. A
commission may require a separate release or synchronized start only when that
condition is an explicit, load-bearing controlled variable; name the defect it
prevents and accept the resulting extra turn for every member.

Recover a member in the existing task, use the product's task-handoff surface to
move that same task when only its managed root is wrong, and create at most one
replacement for an unusable member. The replacement uses the same role,
commission, and group identity; unaffected members continue. Archive the failed
predecessor after replacement binding, and archive any earlier superseded group
once the authoritative group is established. Full-group reruns are limited to
the shared invalidators named in `decision-routing.md`.

**Forseti precedence bridge.** A resolver-loaded generic prompt or
delegated-review skill supplies task-local method mechanics, not Forseti routing
authority. Its generic requirement to render every strict controller prompt
through the full orchestrator is satisfied, for an eligible Forseti lane, by the
compact renderer below. The skill's review, de-correlation, scope, validation,
and adjudication safeguards still apply. If a receiver cannot honor this
project binding, return a visible routing blocker instead of silently taking the
generic heavy route. This bridge changes no installed skill artifact and makes
no deployment claim.

### Lane-Scoped Delegated Patch Prompt Default

This is the unnamed default, not a mode selector. Use it only when all of these
conditions hold:

- the deliverable is one current-lane, operator-couriered, paste-ready prompt;
- the future delegate must have direct `repo` access and a different upstream
  vendor/model lineage from the author;
- the visible request supplies or safely determines a goal and success signal,
  one matching target worktree or managed starting ref, branch, required commit
  pin and `revision_mode` (freezing any uncommitted authoring work as the last
  authoring act before courier), named file set, bounded patch authority, and
  validation route;
- the rendered prompt binds an external controller under
  `.agents/workflow-overlay/decision-routing.md`; an already selected controller
  carries the two-root preflight, and an unknown future courier receiver stays
  preparation-only as `receiver_to_bind`;
- none of the **Full orchestration** routing conditions immediately above apply;
  and
- there is no unresolved authority, target, state, or scope conflict.

The author records the single inline `receiver_binding` receipt owned
by `.agents/workflow-overlay/decision-routing.md`. A bound active receiver uses
one combined target-state and authority-pointer intake, then inspects the actual
diff by its second latency-bearing tool call. Full overlay or source loading
before diff inspection is a routing defect unless a named authority or target
ambiguity blocks diff resolution. An unknown courier completes the same intake
plus its external direct-write proof as its first action. The author does not
pre-load target sources, reconstruct the source ledger, or traverse the template
registry before the binding is verified.

An explicit `delegate patch` invocation is an authoring request: return exactly
one paste-ready prompt for the operator to courier. Do not inspect installed
controllers, create or dispatch a task, fork or spawn another agent, or execute
the review. The commission includes `delivery: operator_courier_only`,
`access: repo`, and
`delegate_eligibility: different_vendor_lineage_with_direct_repo_access`.
Same-vendor, unknown-lineage, no-repo, self, and Codex-managed controller
substitutes are invalid. A manager-prefixed target-worktree path is not a
controller substitute and does not make an otherwise eligible external
controller invalid. If no eligible controller is available, the prompt remains
unexecuted.

Render one compact pointer-first prompt containing:

1. the plain goal and what done looks like;
2. the exact worktree or managed starting ref, branch, required commit pin and
   `revision_mode`; delayed review of an advancing lane defaults to `ancestor`,
   while an intentionally frozen historical diff or artifact uses `exact`; a
   clean-at-bind requirement with only controller-owned commissioned edits
   allowed afterward; named targets and patch scope; plus the single
   `receiver_binding` receipt (using `receiver_to_observe` only for facts the
   not-yet-launched receiver must observe);
3. the different-vendor controller constraint plus author/home family and
   delegate family, using `operator_to_fill` only for an inferable but genuinely
   operator-owned value;
4. pointers to `AGENTS.md`, `.agents/workflow-overlay/README.md`, the targeted
   sections of `.agents/workflow-overlay/delegated-review-patch.md`, and the
   relevant review skill or lane; the delegate-facing `environment_baseline`,
   `lifecycle_hard_stop`, and `decorrelation_commission` constants from
   `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md` are
   restated inline, faithful to that owning artifact, so the courier body is
   self-contained for its external receiver;
5. named validation expectations with real failure and not-run reporting,
   selected under `.agents/workflow-overlay/validation-gates.md` — that file
   owns which checks a commission may require locally, and a commission does
   not name a broad local suite it already covers by required CI;
6. the controller return: findings, bounded diff, neutral citations, validation
   evidence, verdict, and residual risk; and
7. Chief Architect adjudication before any returned change is kept, plus
   `NEEDS_ARCHITECTURE_PASS` for design-level blockers.

Prompt rendering and execution are separate states. A prompt with
`receiver_class: receiver_to_bind` may be returned for a manual unknown courier,
but it must label itself preparation-only, must not claim dispatch readiness,
and must block receiver source loading until rebound to a verified concrete
class. A delegated review-and-patch courier prompt must not carry
`receiver_creation_authorization` and must not select `codex_managed_worktree`;
that restriction selects the receiver class, not the target path namespace. An
eligible `external_direct_write` controller may use the commissioned effective
target even when its path is manager-prefixed, after the normal target,
revision, capability, and writer-isolation checks. The general receiver-creation
clause above remains available for other explicit implementation commissions
but is not a fallback for this lane. Generic `proceed`, implementation
authority, unavailable external tooling, or a same-vendor sanity label never
authorizes dispatch.

The default receiving output is chat or the lane PR/comment. Do not require a
durable review report, `review_summary` courier, provenance checker, full source
pack receipt, template-registry traversal, or `SOURCE_CONTEXT_READY` phrase
solely because the task is delegated, adversarial, or patch-authorized. The
receiver still reads the actual target diff and sources, performs the real
review, and runs relevant validation. Pointer over copy: if an eligibility
condition fails, use full orchestration or block on the missing authority.

### Owner-Invoked Mini God Tier Uplift

Mini God Tier is the only named assurance uplift for this prompt family. It is
owner-invoked only and never inferred. It selects the bounded capability target
defined by `docs/decisions/forseti_mini_god_tier_doctrine_v0.md`; it does not
widen scope, establish readiness, or create a claim tier. Use full orchestration
and add source-gated method sequencing, durable reporting, and
provenance evidence only to the degree necessary for that target, remaining
pointer-first and naming every accepted residual.

The compact default deliberately retains four residuals: the receiver must
still read the real diff and sources and run validation; cases matching the
Full orchestration predicate (portable no-repo capsule, multiple independent
receivers or output lifecycles, or material unresolved ambiguity) still take
the full route; eligibility remains a judgment rather than new
standing infrastructure; and Mini God Tier cannot guarantee cross-vendor
availability or prove quality. Revisit the first two if repeated work shows
duplicate receiver reads, the third after three confirmed misroutes or omitted
guards, and the fourth if an actor treats the label as validation.

**Prompt filing is classified by source role, not by recipient count.** A
prompt, handoff, wrapper, rerun, review request, or patch prompt must still apply
the prompt contract at the correct depth before use; the filing question is
separate:

- **Canonical prompt artifacts** are filed under the accepted `docs/prompts/**`
  family. This includes reusable templates, doctrine-bearing prompts,
  first-of-kind workflow prompts, standard handoffs/wrappers/reruns/review
  requests meant to be reused beyond the current lane, and any prompt promoted
  as a Forseti source artifact. For these prompts, `paste-ready-chat` carries a
  copy of the filed body for pasting and is **not a substitute for filing**.
- **Lane-scoped execution prompts** are not standalone prompt artifacts. A
  one-off review dispatch, adversarial prompt, rerun launcher, patch prompt,
  wrapper, courier, or model/agent/thread/worktree message whose only job is to
  advance one work-unit lane is attached to the overall lane PR body/comment or
  kept in ignored `docs/_inbox/` scratch when a disk handoff is useful. Do not
  open a separate prompt-only PR for that material, and do not commit it solely
  to manufacture a durable prompt artifact. The durable record is the lane PR
  plus the downstream artifact the prompt asks the receiver to write. A
  lane-scoped courier prompt committed to the repository despite this default
  (for example, for cross-machine transport) is retired — deleted in its lane
  PR — once its return is consumed;
  `.agents/workflow-overlay/delegated-review-patch.md` binds that retirement at
  adjudication closeout. Closeout
  notes and other lane-continuity docs follow the same filing rule: they ride
  the originating work-unit lane PR or stay in ignored scratch until consumed,
  and get a standalone PR only when the doc itself is the bounded publication
  work unit. Handoff-only packets follow the transport/publication split
  immediately below; commissioning the packet alone does not make it a bounded
  publication work unit.
- If a lane-scoped prompt later becomes reusable, doctrine-bearing, or otherwise
  source-like, promote it through the canonical `docs/prompts/**` path in the
  same lane PR when that lane owns the change, or in a dedicated prompt PR only
  when the prompt artifact itself is the work unit.

### Durable Prompt Lifecycle Closeout

When a durable one-shot prompt produces its commissioned return, a durable
prompt's return is consumed, or its `stale_if` condition is observed to have
fired, the lane observing that transition must not leave the prompt silently
looking live. Close it in the same lane by choosing one disposition:

- delete an unreferenced one-shot prompt in that state; or
- when deletion would break provenance or a downstream reference, retain it
  with a prominent body notice naming that state — completed, consumed, or
  stale — and pointing to the durable return, PR, or commit when one exists.

When another durable artifact replaces a retained prompt, also add the
retrieval-header `superseded_by` pointer and name that successor in the same
notice.

A still-live prompt receives no lifecycle label. Use repository-relative
pointers for in-repository successors and returns. Do not create a prompt
registry, closeout receipt, checklist, or standing validation gate for this
transition, and do not backfill untouched historical prompts solely to
normalize them.

### Handoff Transport Versus Publication

For a bounded cold handoff, the receiving task's initial prompt is the default
authoritative handoff. It carries the objective, exact target and revision,
allowed dirty state, bounded source pointers, edit authority, validation route,
and real stop conditions. Create a durable packet only for a distinct
persistence, reuse, or separate-consumer need. A courier is transport-only: it
points to the prompt or packet and does not restate its body.

When a durable handoff-only packet is needed:

- **Dispatch-ready / transport.** Verify the receiver can resolve the packet by
  its actual route once. For clean tracked sources, the packet commit SHA pins
  the bytes; add per-file hashes only for dirty, external, generated, or
  ambiguous content. A couriered SHA is not rewritten during the packet's
  transport lifetime; a required history change re-couriers the new SHA. Push
  only when the receiver cannot reach the local worktree
  or ref. Stop visibly if no route exists.
- **Publication-ready / landing.** Open a packet PR only when the packet
  independently merits publication, another landing artifact requires it, or
  the owner requests landing. A PR is not a discoverability mechanism.

A packet riding an implementation, doctrine, code, or other publication work
unit lands in that work unit's normal PR.

Canonical filed prompts and lane-scoped prompts carry the applicable preflight
by contract; no write-time advisory hook injects it. Changed durable prompt
shape is checked at CI by the prompt gates, while selection of routine, compact
delegated, or full orchestration depth remains resident judgment. An eligible
delegated review-and-patch prompt carries the compact default above rather than
the escalated receipt. Missing applicable preflight remains a prompt-quality
defect.

If `workflow-prompt-orchestrator` is not resolver-available when a case needs it,
apply this file's full contract or return a visible blocker; this routing default
does not claim the skill is an adopted or resolver-validated executable.

## Default Path Assignment

The user is not responsible for naming routine Forseti artifact paths.

When a user asks for a canonical prompt artifact without naming a path, choose
the narrowest accepted Forseti folder from
`.agents/workflow-overlay/artifact-folders.md` and the Supported Prompt Families
table above, and create a deterministic, descriptive versioned filename.
Example: a reusable review prompt goes to
`docs/prompts/reviews/<descriptive_slug>_prompt_vN.md` with a downstream report
at `docs/review-outputs/adversarial-artifact-reviews/<descriptive_slug>_review_vN.md`
(or `docs/review-outputs/<descriptive_slug>_review_vN.md` when no narrower child
folder is bound).

When the request is for a lane-scoped execution prompt and no reusable prompt
artifact is requested, default to attaching the prompt to the lane PR
body/comment. If the lane PR is not open yet and a file handoff is useful, use
ignored `docs/_inbox/` scratch and carry the prompt into the lane PR at PR prep.
Do not create a standalone prompt PR for that default. A handoff-only packet
that must remain findable across a cold lane uses the dispatch-ready transport
contract above instead of this scratch default.

Repo-aware prompts handed to another model, agent, thread, or worktree must
state both:

- the input prompt source the reviewer or downstream agent should treat as
  authoritative for that run: a canonical prompt artifact path, a lane PR
  body/comment location, or an ignored `docs/_inbox/` scratch path; and
- the exact output artifact path the reviewer or downstream agent should write,
  when the output mode writes a durable artifact.

In-repository source, successor, and output-artifact locators in durable or
cross-recipient prompts must be repository-relative and carry the revision or
hash required by this file when stability matters. A machine-local absolute
path may supplement that portable locator as a runtime binding delta, but must
not be the sole locator for an in-repository artifact. This does not prohibit
absolute workspace roots, external data roots, or command paths required by the
environment baseline.

For a handoff-only packet, those fields are insufficient by themselves: the
courier also carries the verified transport route, repository-relative path,
branch/ref, commit SHA, and explicit revision-read fallback required by
"Handoff Transport Versus Publication" above.

Ask the user for a path only when the destination cannot be determined from the
artifact role, accepted folders, requested workflow, or collision state. If a
chosen path already exists, choose the next version suffix or return a visible
collision blocker when versioning would change the intended target.

## Full Prompt Versus Thin Wrapper

A full prompt is the durable artifact. It must include:

- the retrieval header from `.agents/workflow-overlay/retrieval-metadata.md`
  when the prompt is new or materially touched;
- objective and intended decision;
- Forseti source hierarchy and required reads;
- source paths plus hashes or revisions when stability matters;
- hard constraints and forbidden imports;
- output mode and exact output contract;
- target artifact roles and write permissions;
- validation gates and required verdicts;
- assumptions, unknowns, and blocked conditions.

A thin wrapper is a short invocation of a full prompt. It must include:

- referenced full prompt path and hash or revision;
- workspace path, branch or revision, and dirty-state allowance;
- target files or directories;
- output mode and edit permission;
- only the delta needed for this run.

Thin wrappers must not restate or fork project policy. If policy changes are needed, update the full prompt or overlay first.
Use a retrieval header for a wrapper only when the wrapper is durable and
expected to route future work.

## Fitness-Reference Surfacing (Durable / Cross-Recipient Prompts)

For durable or cross-recipient prompts — handoffs, commissions, reviews, and patch
prompts (the saved or `paste-ready-chat` families), not trivial inline `chat-only`
prompts — surface the work unit's `fitness_reference` (goal + observable success
signal, the object owned by `docs/decisions/work_unit_fitness_reference_v0.md`),
**reusing that concept; do not mint a new goal/success vocabulary.** Surface it in
two places:

- **Chat return (for the dispatcher):** show the goal + success signal beside the
  prompt path or link, in **plain language a non-expert reads at a glance** — no
  skill jargon, no internal vocabulary. If it cannot be stated plainly, that is a
  prompt-quality defect, not a styling nit.
- **Prompt body (for the receiving executor):** carry it **pointer-preferred**
  (cite the controlling upstream goal/signal when one exists; fresh compact prose
  only when none does) as a clearly-labeled "what this is for / done looks like"
  entry. A cross-recipient prompt travels without this chat, so the body is the
  only place its executor sees the target; this extends, and does not duplicate,
  the already-required "objective and intended decision."

Label the carried reference **executor target + review axis-to-attack, not a review
pass bar.** This preserves `prompt_body_injection: no` and the alignment-axis
guardrail from `work_unit_fitness_reference_v0`: a later review of the commissioned
work treats the goal/signal as a pointer-preferred axis it must attack, never as a
conformance bar graded against the generating prompt. Carrying the target for the
executor is not making it the review bar.

Generic shape (illustrative only — keep your wording specific to the work; do not
anchor to this):

> **Goal:** the one outcome this work must achieve, in plain words.
> **Done looks like:** the observable check that says it worked — what a good result
> shows, not a restatement of the task.

This **extends the surfacing** of `work_unit_fitness_reference_v0` (scope-locked at
enactment to adversarial artifact review plus the fused gate) to durable and
cross-recipient prompts generally. It changes none of that decision's substance:
not its review back-pressure, not the scoped fused gate, not `prompt_body_injection:
no`, and not the alignment-axis-not-pass-bar guardrail.

## Review Prompt Defaults

After source readiness, a review prompt invokes the relevant review method.
Before listing findings, that method frames the boundary problem, identifies
failure modes, and establishes decision criteria. This does not widen review
scope, authorize patching, or turn a narrow review into product planning.

Review prompts should still return the requested review output shape. The final
answer remains a review result with findings, non-findings, not-proven
boundaries, and next authorized step.

Every Forseti delegated-review prompt and any delegated review-return or courier
prompt must point the commissioning adjudicator to the closeout and same-turn
material-continuation rule in `delegated-review-patch.md`. That file owns the
rule; prompt artifacts may expose the needed output slot but must not fork its
semantics.

Delegated review-and-patch commissions require direct repo access. `no_repo` is
outside that lane and routes to a separately named ordinary read-only review;
it must not be presented as delegated patch authorship. Couriered or paste-ready
delivery changes transport only, never the direct-repo requirement.

Review prompts, wrappers, handoffs, and closeouts must not recommend,
prescribe, rank, or imply runtime model choice; they may route by review lane,
method/skill, target, authority, output mode, destination, and prompt-template
target only. Model-neutrality semantics for review lanes and template
retrieval are owned by `.agents/workflow-overlay/review-lanes.md` (Review
Doctrine; Template Retrieval Binding); do not restate them here or in prompts.

The receiver-facing review mechanics a review prompt binds are owned by
`.agents/workflow-overlay/review-lanes.md` (Review Doctrine); prompts and this
file point, never restate. That owner defines: the findings-first default and
the strict-output catalog requiring explicit binding; severity
(`critical`/`major`/`minor`) and `confidence` as priority-only labels;
`minimum_closure_condition` and `next_authorized_action` on actionable
findings; the coverage-first find stage with `considered_and_defended`;
optional-hardening labeling; the `patch_queue_entry` exclusion for read-only
reviews; the CA consumption order (exact order owned by
`.agents/workflow-overlay/communication-style.md`) with no synthesis lane; the
`reviewed_by`/`authored_by` provenance contract; and fitness-reference
anchoring for intent-bearing targets (decision owner:
`docs/decisions/work_unit_fitness_reference_v0.md`). A review prompt states
only its prompt-specific deltas: which formal outputs, if any, it explicitly
binds, and a prompt-specific severity contract when it departs from the
Forseti-bound severity set.

Every Forseti adversarial artifact review prompt must invoke
`workflow-adversarial-artifact-review` after `SOURCE_CONTEXT_READY`. If that
skill is unavailable, unresolved, or not applied, the run may return only a
blocked or advisory-only result and must not emit formal verdicts, severity
authority, blocked/ready status, validation claims, readiness claims, mandatory
remediation, patch queues, executor-ready handoffs, or alignment-complete
claims.

When the review target is an evidence-bearing artifact (a report, scan
receipt, board, or ledger whose claims cite sources, ids, dates, or figures),
the review prompt must name provenance accuracy as an explicit goal with
observable success signals: every internal cross-reference id dereferenced to
its ledger row and checked for semantic match, not just existence; every
stated count, sum, and range recomputed from the rows it claims to summarize;
every quoted price or figure traced to a cited excerpt or named untraceable;
and every date checked for anchor-type laundering (page-read or publication
dates presented as event dates). A review that did not perform these checks
must say so rather than imply them. This pass exists because arithmetic,
pointer, and traceability defects empirically survive reviews prompted only
for overclaim and contract compliance.

Review prompts using `review-report` output mode must bind a durable report
destination under `docs/review-outputs/` or a typed child folder unless the
review is explicitly chat-only before review work starts. The human-readable
review value belongs in the durable report; chat-YAML validity after a
successful write and the failed-write blocked shape are owned by the Output
Modes section below and `.agents/workflow-overlay/communication-style.md`.

## Escalated Preflight Fields

Prompts matching the **Full orchestration** predicate above include or reference
the `forseti_start_preflight` receipt owned by
`.agents/workflow-overlay/source-loading.md`. These cases must make their start
state portable because another actor or later lane will rely on it. Constants
bind by citing
`docs/prompts/templates/shared/forseti_preflight_defaults_v0.md` — intake
reads, external-source boundary, environment baseline, retrieval-header
defaults, lifecycle hard stop, de-correlation commission constants — and are
not restated. This section is the single owner of the per-prompt escalated
delta list; the defaults artifact holds constant values only. Routine prompts
stop at the core above.

An eligible lane-scoped delegated review-and-patch prompt instead uses the
compact default above: core prompt fields plus one fresh target-state read and
the eight pointer-first commission fields. It does not inherit this escalated
receipt solely from delegation, adversarial wording, patch authorization,
executor-ready wording, or a bounded multi-file target.

Every escalated prompt must state:

- selected source pack from `.agents/workflow-overlay/source-loading.md`, or a
  bounded custom source pack;
- `repo_map_decision: loaded | not_needed | unavailable`, plus `repo_map_reason`. Source-loading (`.agents/workflow-overlay/source-loading.md`) owns the read-pack rule; this field records the prompt author's routing decision and must not make the repo map a mandatory read;
- workspace path or repository identifier;
- expected branch, detached revision, or commit hash when source stability matters;
- a pointer to the active one-time writable-root binding for same-lane work, or
  the single inline `receiver_binding` from `decision-routing.md` when the
  prompt creates a new/external receiver or materially changes the binding;
- the commission-local `receiver_creation_authorization` block above when an
  implementation-authorized managed receiver may need to be created from the
  visible commission;
- dirty-state allowance and whether untracked files are in scope;
- controlling-source state when strict claims depend on Forseti overlay,
  source-loading, repo-map, prompt-policy, validation, or artifact-role files:
  clean, modified, untracked, stale, or not checked;
- whether the work changes product doctrine, architecture doctrine, workflow
  authority, validation philosophy, review authority, output authority, or a
  lifecycle boundary, and if so which propagation surfaces must be checked
  before closeout;
- target files or directories;
- edit permission: `read-only`, `patch-only`, `docs-write`, or
  `implementation-authorized` (enum owned by `forseti_start_preflight` in
  `.agents/workflow-overlay/source-loading.md`);
- output mode: `chat-only`, `file-write`, `review-report`,
  `paste-ready-chat`, or `patch-queue`;
- required validation gates and where evidence is recorded.

### Repo-Bound Review Target Resolution

Repo-bound review and delegated-review prompts first bind the receiver class
under `.agents/workflow-overlay/decision-routing.md`. Only
`external_direct_write` uses two distinct roots: its `launch_checkout` and the
commissioned `effective_target_worktree`; a mismatch is a resolution trigger,
not an automatic blocker. `codex_managed_worktree` requires the task's launch
checkout and effective target to be the same app-created managed worktree.
`collaboration_same_root` remains in the calling task's root.
`receiver_to_bind` is preparation-only. Prompts may render before a future
launch checkout is observable, but they must not claim dispatch readiness or
begin receiver source loading until the binding is verified.

Target identity is an exact revision/hash pin or required commit ancestry.
Working-tree bytes are never a binding surface for a couriered receiver:
uncommitted work is frozen into a commit as the last authoring act before
courier, and the commission pins that frozen commit. A target that cannot be
frozen blocks to the Chief Architect rather than binding a weaker identity.
Exact pins remain exact. A delayed delegated review or review-and-patch of an
advancing lane defaults to explicit ancestry semantics: `required_revision`
binds the minimum checkpoint, and receiving preflight verifies it is an ancestor
of the clean current `HEAD`, then records that `HEAD` as `reviewed_revision`
before source review. `reviewed_revision` is the exact immutable byte identity
for that run and both revisions travel in the return. Later descendants remain
outside scope. If the author continues after capture, the receiver reviews a
separate clean worktree at `reviewed_revision` and applies any patch on its own
review branch; the receiver must not review or patch a concurrently changing
worktree. Use `exact` instead when the commissioned subject is intentionally one
frozen historical diff, commit, or artifact.

Receiving preflight establishes one binding, then stops repeating it:

1. Reuse the active work-unit binding when receiver, task, root, target, and
   material state are unchanged.
2. For a new managed receiver, bind the app-created worktree as that task's root;
   do not inspect, create, or select a nested worktree as an alternate target.
3. For a new `external_direct_write` receiver only, resolve the unique target and
   establish direct write capability plus no-concurrent-writer state once.
4. Same-root collaboration stays inside the caller's active binding.
5. Re-resolve only on a receiver/root/target change, genuinely unknown
   capability, or observed mismatch/dirty-state drift. Synthetic write/index
   probes and hook canaries are not routine preflight.
6. On a pre-edit mismatch, execute an already-authorized managed-task route when
   available. Return `BLOCKED_RECEIVER_REROOT_REQUIRED` only when no capable
   authorized route exists or the new binding cannot be established.

This resolver is discovery of the commissioned source, not permission to use an
alternate branch, recreated copy, context pack, or summary as review evidence.
It does not weaken exact hash/revision pins, dirty-state rules or write guards;
it prevents both an unrelated launch checkout from being mistaken for the
target and a valid external controller from blocking solely on its launch path.

Rerun and patch prompts must also name the prior artifact, prior hash or revision, frozen decisions, mutable fields, and unresolved finding being retried.

## Source-Heavy Evidence Preservation

Preflight is allowed to continue into the next step when it is limited to
authority reads, path existence checks, hashes, branch state, and target-scope
checks. Do not split a prompt solely because preflight exists.

Source-heavy work uses bounded questions and targeted reads. Persist a unit
artifact or checkpoint only when the evidence must survive compaction, cross a
receiver boundary, or is itself the requested deliverable. Do not require a
write-and-hash cycle between ordinary source reads.

If compaction or handoff would otherwise lose load-bearing evidence, preserve
the smallest reconstructable packet: source identities, decisive findings,
unresolved gaps, and any required hash. If the evidence remains cheaply
re-readable from its controlling source, point to it instead. Compaction does
not automatically contaminate prior work; a claim becomes blocked only when
its evidence can no longer be reconstructed or verified.

## Output Modes

- `chat-only`: return analysis, options, recommendations, and blocked assumptions without writing files.
- `file-write`: write only authorized Forseti documentation or overlay files;
  report changed files and validation evidence. For substantial
  decision-bearing artifacts, chat closeout must include a concise headed human
  summary before the artifact receipt.
- `review-report`: perform read-only review unless a patch-execution lane is explicitly assigned; write reports under `docs/review-outputs/` or a typed child folder, then return the compact YAML review summary in chat only after the report write succeeds. If the required report write fails, return `status: failed`, `review_location: chat_only_current_thread`, and `recommendation: blocked` in chat without `report_path`, name the failed path, and include enough human-readable failure detail to route.
- `paste-ready-chat`: return one prompt, wrapper, handoff, or review request
  body in chat for copying into another model, agent, thread, or worktree. For a
  canonical prompt artifact the durable artifact of record is the filed
  `docs/prompts/**` file (see "Author Through The Prompt Orchestrator"); the chat
  body is a copy for pasting, not a substitute for filing. For a lane-scoped
  execution prompt, `paste-ready-chat` may be the prompt body that is attached to
  the overall lane PR body/comment or kept in ignored `docs/_inbox/` scratch; it
  does not create source authority and must not produce a standalone prompt PR.
  Any surrounding Chief Architect, planning, overlay gate, or routing decision
  should still use the human-readable chat shape from
  `.agents/workflow-overlay/communication-style.md`.
- `patch-queue`: produce stable patch units, target files, authority basis, and validation gates. Applying patches requires separate execution authority.

The general human-summary / agent-detail / optional courier-state chat shape is owned by `.agents/workflow-overlay/communication-style.md`. This file owns output-mode exceptions to that shape:

- `review-report` may use YAML-only chat only after the required durable report has been successfully written; failed durable writes must use `review_location: chat_only_current_thread`, `status: failed`, `recommendation: blocked`, name the failed path, and include enough human-readable routing detail.
- `file-write` may return a compact path/hash/status receipt when the durable artifact carries the human-readable value; substantial decision-bearing writes must close with a headed human summary first (recommendation, why it matters, material boundaries, next authorized step), then receipt. If the write fails or the chat carries a decision, return readable blocker detail. Doctrine-changing writes record propagation evidence in the PR or closeout by default under `.agents/workflow-overlay/source-of-truth.md`.
- `paste-ready-chat` may prioritize the paste-ready body when that body is the deliverable; do not use this mode to hide a Chief Architect, planning, scoping, overlay gate, or completion decision.
- `patch-queue` may use stable structured units, but applying patches requires separate execution authority and readable blocker routing.

## Prompt Validation Gates

Authoring-route precondition: the prompt, handoff, wrapper, rerun, or patch
prompt must have applied the prompt contract at the correct depth (see "Author
Through The Prompt Orchestrator") — the **Forseti Prompt Preflight** core for a
routine prompt, the **Lane-Scoped Delegated Patch Prompt Default** for an
eligible current-lane commission, or the full `workflow-prompt-orchestrator`
contract for a prompt matching the **Full orchestration** predicate above. An
artifact that skipped the applicable contract is a prompt-quality
defect; reconstruct it at the correct depth before use. A durable start receipt
is required only for the full-orchestration cases.

Before using a generated Forseti prompt, apply these gates:

1. Applicable preflight complete: `AGENTS.md` and
   `.agents/workflow-overlay/README.md` were read or supplied in the current
   task context. Routine prompts carry the preflight core (required fields
   stated, defaults elided, constants by pointer) and no start receipt;
   eligible compact delegated prompts carry that core, one fresh target-state
   read, and the eight commission fields above; escalated prompts carry the
   portable start receipt and fields above.
   Repository-state fields are stated only when material.
   Modified or untracked controlling sources block strict readiness,
   acceptance, validation, proof, `PASS`, or `ADEQUATE_NOW` claims unless owner
   acceptance or controlling authority is explicit.
2. Artifact roles bound: every prompt role maps to `.agents/workflow-overlay/artifact-roles.md` or another accepted overlay file.
3. Source resolution clean: external workflow sources do not provide Forseti authority; installed skills are deployment copies; `jb` project policy is not imported.
4. Writable-root binding present when repository state matters: same-lane prompts point to the active one-time binding without repeating its root/capability recital; new/external receivers and materially changed bindings carry the single `receiver_binding`, and a not-yet-created managed receiver also carries the exact one-task `receiver_creation_authorization`. Collaboration remains same-root and unknown receivers remain preparation-only. The same actor may target its selected worktree when launch and target roots differ; a command `workdir` neither expands a collaboration subagent's sandbox nor proves failure by itself. A delegated review-and-patch courier remains operator-courier-only, direct-repo, and different-vendor, with no Codex-managed receiver fallback; that receiver-class prohibition does not reject an explicitly commissioned manager-prefixed target worktree. A delayed advancing-lane review uses `ancestor`, captures `reviewed_revision` before source review, and keeps that snapshot immutable; an intentionally frozen review remains `exact`. A prompt fails this gate when it invents task-creation authority, infers denial from launch root or target namespace, ignores an observed capability denial, permits concurrent mutation of the reviewed snapshot, claims dispatch readiness before a new binding exists, or repeats capability ceremony as if it were required for an unchanged active binding.
   Multi-task commissions also satisfy the conservation rule: same-root actors
   use collaboration; independent members launch as one role-named group with
   executable initial prompts; recoverable member failures stay in the same
   task; only an unusable member may be replaced once; unaffected members
   continue; and a full-group rerun occurs only for a named shared invalidator.
   Routine preparation-only members, release turns, mutation probes,
   shared-prompt hash ceremonies, replacement groups for member-local failures,
   and duplicate role titles fail this gate unless an explicit load-bearing
   experimental control requires the extra synchronization.
5. Output mode explicit: exactly one output mode is named, with write destination and report destination if applicable.
6. Required checks named: validation gates can fail and include pass, fail, blocked, and not-run semantics.
7. Source capsule remains decision-bounded under
   `.agents/workflow-overlay/source-loading.md`; its default budgets are
   exceeded only when omitting the additional source would make the prompt
   incomplete, and the reason is stated.
8. Source-gated method sequencing satisfied when triggered: prompts that
   orchestrate workflow methods as an explicit reasoning pipeline distinguish
   `REFERENCE-LOAD` from `APPLY`, include a `SOURCE_CONTEXT_READY` /
   `SOURCE_CONTEXT_INCOMPLETE` gate, and do not ask for method-derived
   conclusions before source readiness. An eligible lane-scoped delegated patch
   prompt may use its targeted review-lane or skill pointer without the magic
   phrase, while still requiring the receiver to read the real target sources
   before findings.
9. Retrieval metadata bounded: new or materially touched durable prompt
   artifacts use retrieval metadata only for source loading and do not create
   authority, validation proof, approval, readiness, lifecycle completion,
   deployment/install/resolver status, or edit permission.
10. Review doctrine satisfied (per Review Prompt Defaults above): the prompt
    invokes `workflow-adversarial-artifact-review` after source readiness or
    blocks strict claims as advisory-only; explicitly binds any formal output it
    requests; states only its prompt-specific severity/output deltas; and
    otherwise binds its receiver to the review mechanics owned by
    `.agents/workflow-overlay/review-lanes.md` (Review Doctrine) by pointer —
    finding fields, coverage-first find stage with `considered_and_defended`,
    optional-hardening labeling, `patch_queue_entry` exclusion,
    `reviewed_by`/`authored_by` provenance, fitness-reference anchoring, CA
    consumption order, and model-neutrality — without restating them.
11. Doctrine propagation satisfied: prompt, handoff, wrapper, review,
    output-mode, or execution-contract changes that alter durable doctrine name
    the controlling source and record targeted propagation evidence in the PR
    or closeout under `.agents/workflow-overlay/source-of-truth.md`.
12. Rerun economy satisfied: retry prompts preserve frozen decisions and avoid scope reset.

## Prompt Verdicts

- `PASS`: all required prompt gates are satisfied.
- `PASS_WITH_WARNINGS`: prompt may be used, but named assumptions or unknowns must travel with it.
- `BLOCKED`: required authority, role binding, source, or preflight data is missing.
- `FAILED`: the prompt violates a hard constraint, imports forbidden policy, or changes output mode without authority.

## Anti-Import Rules

- Do not copy `jb` prompt templates, skill files, GAP/CV Engine policy, compiler paths, handoff rules, product-lead rules, or repo-local lifecycle mechanics.
- Do not claim `workflow-product-ultraplan`, `workflow-feature-ultraplan`, or `workflow-prompt-orchestrator` are executable unless a real resolver-visible `SKILL.md` exists and Forseti source-resolution/adoption checks pass.
- Generic layout ideas may be reused only after binding to Forseti paths, artifact roles, output modes, and validation gates.
