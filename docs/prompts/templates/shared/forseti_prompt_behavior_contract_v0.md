# Forseti Prompt Behavior Contract v0

```yaml
retrieval_header_version: 1
artifact_role: Prompt template
scope: Shared Forseti behavior contract for project-local prompt templates.
use_when:
  - A prompt template needs common Forseti source, boundary, and non-claim rules.
authority_boundary: retrieval_only
```

Use this contract only when a prompt explicitly references it.

## Source Authority

- Current user instruction for the turn wins.
- Forseti `AGENTS.md` and `.agents/workflow-overlay/` own Forseti project facts.
- Forseti docs under `docs/` are subordinate to the overlay when conflicts appear.
- Explicitly invoked or resolver-loaded skills may provide task-local mechanics
  only; external workflow source is not Forseti authority.
- `jb` paths, product rules, lifecycle mechanics, templates, validation habits,
  and handoffs are not Forseti authority.

## Source-Gated Method Use

Follow `.agents/workflow-overlay/prompt-orchestration.md`'s Source-Gated Method
Contract for its trigger, sequence, and compact-path exception. Read material
sources before applying methods or forming findings even when explicit phases
and readiness declarations do not apply.

## Cynefin Routing Layer

Repo-aware prompts, wrappers, handoffs, review prompts, patch prompts, and
reruns include `.agents/workflow-overlay/decision-routing.md` only when its
full-router conditions trigger: a material uncertainty could change
decomposition, authority, source truth, or safe sequencing. Task category alone
does not trigger it. When triggered, run it before planning or delegation and
include the allowed and disallowed next moves; otherwise proceed without a
bypass receipt.

## Output Discipline

- Name exactly one output mode.
- For decision-bearing chat, follow the chat-output topology in
  `.agents/workflow-overlay/communication-style.md`: human summary first,
  agent-readable detail second, and compact courier state last only when useful
  or required. Use clear headed prose by default; YAML is not required unless
  the user requests it, the output mode requires machine-shaped fields, or
  lane switching / handoff routing would materially benefit from compact
  courier YAML.
- Use `.agents/workflow-overlay/prompt-orchestration.md` for output-mode
  exceptions, including `review-report`, `file-write`, `paste-ready-chat`, and
  `patch-queue`.
- For substantial decision-bearing `file-write` artifacts, require a concise
  headed human summary plus artifact receipt. Do not let "do not paste the full
  artifact" collapse into path/hash/status-only chat.
- Keep missing source fields as `not_found`, `not_bound`, or `UNKNOWN - requires owner input`.
- Do not turn evidence collection into synthesis unless the prompt is a synthesis template.
- Make status claims, as defined in
  `.agents/workflow-overlay/validation-gates.md`, only when an accepted Forseti
  source and current evidence bind the exact status; otherwise name the
  unsupported claim once.
- For review prompts and reports, prefer a review-use boundary over a broad
  non-claims catalog: the review is decision input only and must not be treated
  as approval, validation, mandatory remediation, or executor-ready authority
  without separate acceptance. Add product-proof non-claims only when the review
  target or source authority makes those claims in scope.
- Review prompts should be findings-first by default. Formal verdicts,
  blocked/ready status, validation pass/fail claims, approval, readiness,
  mandatory remediation, patch queues, and executor-ready handoffs require Forseti
  overlay or prompt binding. Actionable findings should state
  `minimum_closure_condition` and `next_authorized_action`. Do not request or
  emit `patch_queue_entry` unless a patch-queue review or patch/integration
  execution lane is explicitly bound.
- Adversarial artifact review prompts must invoke
  `workflow-adversarial-artifact-review` after `SOURCE_CONTEXT_READY`. If that
  skill is unavailable, unresolved, or not applied, the output must be blocked
  or advisory-only and must not emit strict review claims.
- In adversarial artifact reviews, `minimum_closure_condition` states what must
  become true for a failure mode to be resolved, not how to implement the fix.
  Optional hardening may be named only when labeled optional and non-required.
- CA-facing review prompts and handoffs should preserve Forseti's review
  consumption order: commission, target, authority, decision criteria,
  evidence, then reviewer verdict or recommendation. Do not create a synthesis
  lane unless a later Forseti overlay decision binds one.
- When dispatching an orientation or research subagent whose output an agent
  will consume — act on, summarize, or route, even if later shown to a human —
  apply the subagent return contract in
  `.agents/workflow-overlay/prompt-orchestration.md` rather than a local
  prose-output rule: validate the return against that contract's named-field,
  one-line, `file:line`-cite, `unknown`-for-absent, and reject-or-re-prompt
  requirements. Do not request a prose dump for an agent-facing return.

## Source-Heavy Work

For public web or source-heavy tasks:

- define the unit of work before source loading starts;
- keep evidence URLs stable and citeable;
- avoid long pasted source text;
- separate evidence, synthesis, backtestability, and anonymous marketing claims;
- stop rather than continue if source loading becomes unbounded.

## Report Shape

Prefer compact outputs that preserve:

- objective;
- scope and date boundary;
- source list or source URL table;
- missing-field labels;
- blocker states;
- non-claims or review-use boundary;
- next authorized step.

Compactness means omit unnecessary fields and full source echoes. It does not
mean hiding a decision-bearing answer in YAML-only or agent-only structure.
Artifact-native tables, paste-ready prompt bodies, and post-artifact receipts
remain valid when the output mode permits them. For substantial file-written
decision artifacts, post-artifact receipts must be preceded by enough headed
human summary for the owner to understand the result without opening the file.
