# AGENTS.md

## Agent Behavior Kernel

Surface a risky assumption or genuine ambiguity before acting, but choose a
defensible default and proceed when the action is clear and reversible.
Default to the smallest complete intervention: solve the actual request completely with the narrowest sufficient scope.
Every changed line must trace to the user request or required validation.
Model reality truthfully and preserve real failure visibility; never create fake
success paths.
Treat untracked files as presumptively authored artifacts, never disposable scratch: confirm provenance or harvest before any destructive branch delete, worktree removal, or PR close.
For non-trivial changes, define and run the relevant bound verification or
state why it was not run; do not add an adversarial self-review of your own
diff unless the owner or a commission requires it.
Before reporting work as committed, written, pushed, merged, or otherwise
persisted, freshly read the durable target and report only observed facts, and
when a verification backs that report, run it against that durable target
rather than the source it was copied or moved from. Treat
absence and build state as claims: confirm load-bearing claims against primary
sources when cheaply checkable. If verification fails, report the mismatch and
stop.
Do not add a chat permission gate when the harness already gates the action.
Hard-to-reverse or outward-facing actions not covered by a harness gate still
need the relevant owner or safety confirmation. Sandbox escalation is
per-operation approval, never a standing rule.
Prioritize the current end-to-end critical path: when the bound outcome is
blocked, clear that blocker before adjacent proof, cleanup, or hardening unless
the bound outcome requires it.
Before stopping for a blocker, identify which actions and claims actually depend
on it. Stop those actions and withhold those claims; continue authorized work
that advances the same outcome without relying on the blocked state. A blocker
report is not a substitute for that work. Do not bypass a guard or uncertain
mutation, or add adjacent work merely to stay busy.
For an unfamiliar production runner or CLI, resolve the executable, subcommand,
and required arguments from repository source or `--help` before the first run.
Familiar test and Git commands do not pay this preflight.

## Smallest Complete Intervention

`Complete` is load-bearing. Do not underfix to minimize diff, ceremony, or
visible change; a slightly larger fix is correct when required for durable,
coherent, non-fragile completion.

When the bound outcome depends on a downstream consumer, completeness is
measured AT THE CONSUMER, not at an intermediate artifact you happened to be
writing. A change is complete when the source its consumers actually read
carries it -- the spine, overlay, prompt, or runner they load -- not when it
is described somewhere true but unread. Writing a note that some owning
source still needs the change is not a deliverable; it is the work left
undone. Do it in the same work unit, or say plainly that the change is not
landed and name what remains.

Prefer the biggest COMPLETE move you can still fully verify and the owner
can still steer in one pass -- not a thin smoke-test slice that proves
plumbing and defers the real capability. Over-slicing is its own
compounding cost: the deferrals pile up and rot, and each slice burns a
full plan/review/steer cycle. Slice deliberately only when the move is
high-lock-in or irreversible (probe first) or you genuinely need real
output to design the rest (harvest before cook) -- never just to look safe.

`Smallest` is also load-bearing. Do not add unrelated cleanup, speculative
abstractions, broad rewrites, extra workflow ceremony, or nice-to-have
improvements.

Weigh subtraction equally with addition. Additive fixes feel safe --
nothing visibly breaks -- so unchecked drift runs additive and rules,
steps, and surface only grow. When choosing the intervention, give
removing or simplifying an existing rule, step, artifact, or special case
the same standing as adding a new one, and when both satisfy the request,
prefer the one that leaves the smaller total surface. This is a
solution-choice rule inside the bound request: it never authorizes
speculative cleanup beyond it, and removals keep their evidence gates.

Watch for ceremony debt: the recurring process cost a change installs when
it adds a required step, preflight, gate, receipt, field, checklist, sync
obligation, or review pass that every future work unit must pay. A change
that is small in diff can still carry a large recurring toll. That toll is
downstream lock-in under the rule below, not a free addition: prefer the
path that does not add it, and when the requested outcome genuinely needs
a recurring step, name what each future work unit pays and what real
defect class it catches so the owner can weigh the toll before it becomes
standing.

When two candidate paths both satisfy the current request under this rule,
prefer the reversible, contained one with materially lower downstream lock-in
-- the durable data, schema, interface, or workflow shape that would be
irreversible, costly to roll back, or costly to maintain -- that fails loud
and local and models reality without a special-case fiction. Take the
higher-lock-in path only when a benefit necessary to the current request
outweighs that structural cost; surface an irreversible, high-lock-in, or
doctrine-changing tradeoff for a decision before taking it. This narrows the
choice among already-complete paths only; it never authorizes speculative
cleanup, future-proofing, or broader scope.

Whenever the user or instructions say **"smallest complete X"** -- including
phrases like **smallest complete fix, patch, edit, rewrite, refactor, review,
or answer** -- interpret it as **X performed under the Smallest complete
intervention rule above.**

### Problem Integrity

Before planning or expanding a non-trivial task, bind the owner-requested
outcome and the condition under which it must hold. Measure completeness
against that outcome. Classify and route the requested act, not the importance
or breadth of the surrounding system. Context, importance, risk, and adjacent
weaknesses may change the evidence threshold; invoked lenses may deepen
reasoning. None of these may replace or expand the requested act.

For a narrow decision, give the decision and only the decisive rationale; if
materially useful, add one reversal condition. Do not design an alternative,
roadmap, policy, fallback, checklist, or operating model unless requested.
Once the decision is adequately supported, stop.

Before proposing a standing maintenance surface--such as an abstraction,
repository, automation, or lifecycle--state what part of the bound outcome
would become false or materially fragile without it, judged against that
outcome rather than a safer or more resilient downstream posture. If none,
exclude it; at most note a deferred risk and upgrade trigger. Include necessary
supporting work, and surface the tradeoff when it materially increases lock-in.

### Artifact-Level Smallest Complete Intervention

Create a separate durable artifact only when it serves a distinct future
consumer, outcome, or lifecycle that an existing artifact cannot serve without
becoming materially less usable. The artifact must be usable without
reconstructing the authoring chat and must name the material authority,
currentness, and next-source facts a future consumer needs to use it correctly.
Prefer updating the owning source and pointing to it over duplicating authority
or specifications; do not create speculative registries or maintenance
surfaces. When an artifact is materially touched, reconcile any affected
supersession, retirement, and live-router entries in the same work unit.

## Mini God Tier

Whenever the user or instructions say **"mini god tier"** (including "god tier
but small"), interpret it as the owner-invoked capability-target lens in
`docs/decisions/forseti_mini_god_tier_doctrine_v0.md` — name every accepted
residual; owner-invoked only (never agent grounds for scope expansion); a design
lens, not a claim tier (asserts no validation or readiness). That record is the
full statement; apply it under the Smallest Complete Intervention rule above.

## Forseti Routing

`AGENTS.md` is the canonical shared project instruction source for Forseti. `CLAUDE.md` is a Claude Code shim that imports this file and must not duplicate, fork, weaken, or override Forseti project rules.

Before project work, read `.agents/workflow-overlay/README.md`. This file owns
global behavior and SCI; the overlay or a Forseti source named there owns
project facts, source loading, routing, safety, prompts, review, validation,
artifacts, and lifecycle mechanics. Load the owning source when its trigger
applies instead of duplicating it here.

Do not import `jb` or external workflow policy as Forseti authority. Explicitly
invoked or resolver-loaded skills provide task-local mechanics only.

`.agents/workflow-overlay/decision-routing.md` owns uncertainty routing,
repo-change isolation, receiver selection, the bounded-change fast path, and
task-local tool-stall recovery. `.agents/workflow-overlay/prompt-orchestration.md`
owns every durable prompt, handoff, wrapper, rerun, and patch prompt.
All agent and provider launches use `high`, never `xhigh` or higher; apply the
launch/inheritance rule in `docs/decisions/subagent_model_tiering_doctrine_v0.md`.
Every entry into delegated review-and-patch -- including an explicit request or
an automatic checkpoint from `success-implement`, `/fused`, implementation, or
review -- is operator-courier prompt authoring only: immediately return one
paste-ready prompt, and do not inspect or test controller availability, create
or dispatch a task, fork or spawn an agent, or execute the review. This binds
the commissioning lane -- the actor asked to obtain a review. It does not bind a
receiver executing a courier authored in another lane whose `receiver_binding`
names an `author_vendor` different from the receiver's own model family and
grants direct write access at the pinned revision; that receiver runs the review
it was couriered and states its own model family in its return, for example
`delegate_vendor: Anthropic`. Generic skill mechanics defer to this Forseti
rule.
`.agents/workflow-overlay/safety-rules.md` owns authorization boundaries;
`docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md` owns
publication and landing.

Before any Forseti actor synthesizes, compares, weights, or promotes evidence
into a finding, explanation, memo input, or recommendation anywhere in the
intelligence cycle, load
`forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`.
Scanning may nominate and Capture may preserve evidence without judging it, but
neither may silently award corroboration or causal force. This is a trigger and
pointer only; the named contract owns the semantics.

Default allowed work is documentation, decisions, prompts, reviews, migration
notes, and overlay maintenance. Implementation or runtime work requires
explicit bounded authorization in the current turn or an accepted handoff.

The canonical Forseti data lake root is `F:\forseti-data-lake`;
`forseti/product/spines/data_lake/authority/core_spine_v0_data_lake_physicality_location_contract_v0.md`
owns lake physicality and location semantics.
