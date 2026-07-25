---
retrieval_header_version: 1
artifact_role: >
  Docs-only commission/handoff prompt — commissions a gated, reviewed edit to the
  workflow-deep-thinking workflow-kernel skill's OWN canonical source. Not an Orca
  doctrine source; not edit authority; the deliverable is this prompt, not the edit.
scope: >
  Paste-ready commission for a downstream agent operating in the workflow-deep-thinking
  skill's own source + deployment lane (external to Orca). It asks that agent to encode
  two bounded domain-agnostic reasoning rules (deductive standing-rule vs empirical
  generalization; proportionality / stop when adequately supported)
  into the skill's Strict-Claims / decision discipline, route them through the skill's own
  adversarial review + deployment gate, and never treat the installed copy or the Orca
  repo as the skill's source of truth.
use_when:
  - Executing the commissioned workflow-deep-thinking kernel-skill edit in that skill's own source lane.
authority_boundary: retrieval_only
output_mode: file-write (this artifact) + paste-ready-chat (courier copy for the receiving lane)
open_next:
  - docs/product/judgment_spine/judgment_spine_demand_read_grading_rubric_v0.md  # Orca's own (non-kernel) application of the rule; provenance only — do NOT import into the skill
provenance: >
  Rule 1 surfaced in the Orca demand-read judgment lane (2026-06-15) while establishing a
  demand-read grading standing rule. Rule 2 surfaced in the Forseti Smallest-Complete
  assessment of AGENTS.md and the deep-think lane (2026-07-25). Both encoded rules are
  general epistemics/decision discipline; the project applications stay in the project
  repo and are not imported into the kernel skill.
stale_if:
  - workflow-deep-thinking's Strict-Claims / decision-discipline structure is restructured before this lands.
  - The owner withdraws the kernel-skill change in favor of Orca-doctrine-only capture.
---

# Commission — encode two decision-discipline rules ("deductive standing-rule vs empirical generalization"; "proportionality / stop when adequately supported") into the `workflow-deep-thinking` kernel skill (kernel-skill source edit; gated + reviewed)

## Role and target

You are operating in the **canonical source repository of the `workflow-deep-thinking`
workflow-kernel skill** — wherever that skill's source-of-truth actually lives. Your job
is to make two small, domain-agnostic additions to that skill's reasoning discipline,
then route them through the skill's own review and deployment process.

**Before editing, confirm the target:**

- Edit the skill's **canonical source**, not a runtime copy. The installed user-level
  copy at `~/.claude/skills/workflow-deep-thinking` is a deploy target, **not** the
  source of truth — do not edit it as if it were.
- This rule does **not** live in the Orca repo. Orca holds only an application of it.
  Do not add this change to Orca.
- If you cannot positively identify the skill's canonical source, **stop and report**
  `BLOCKED_SOURCE_UNCONFIRMED` rather than editing a copy.

## What to encode — rule 1 (domain-agnostic — no project facts)

Add a rule to `workflow-deep-thinking`'s **Strict Claims** handling (or its decision
discipline, wherever the skill stabilizes "what is proven vs not proven"). The skill
currently distinguishes proven from not-proven but does **not** carve out claims that
need no empirical evidence because they are deductively entailed. Encode that carve-out:

> **Distinguish a deductive standing-rule from an empirical generalization.**
>
> - A claim **entailed by already-adopted premises/doctrine** is a *standing rule*: it
>   needs **no empirical proof-case**. The case or observation that surfaced it makes us
>   *notice* it, not *establish* it — so demanding cases to "prove" it is a category
>   error. Its authority is **derived** from the premises it follows from.
> - A **contingent claim about how something behaves across the world** is an *empirical
>   generalization*: it needs **sufficient cases (N≥K)**; a single instance cannot carry
>   it. Its authority is **evidential**.
>
> **Classifying test:** *Could the claim be false even if the governing premises/doctrine
> are internally consistent?* **No → standing rule** (entailed; no proof-case needed).
> **Yes → empirical** (needs cases). When a claim mixes both, split it: grade the
> entailed part as a standing rule and the contingent part as empirical.

Keep it **project-agnostic**: state it in general terms (premises, claims, cases). Do
**not** import any domain example (no demand-reads, no grading, no Orca vocabulary). Use
the smallest wording that fits the skill's existing voice and section structure; do not
restructure the skill or expand its scope.

## What to encode — rule 2 (added 2026-07-25; domain-agnostic — no project facts)

Add a proportionality stop to the skill's decision discipline. The skill currently
maximizes rigor — option comparison, assumption inventories, verification — but has no
rule bounding that machinery to what the decision needs, so a full pass can itself
become ceremony on narrow decisions. Encode:

> **Proportion the pass to the decision; stop when it is adequately supported.**
>
> - Scale option generation, evidence demands, and verification depth to the stakes,
>   reversibility, and lock-in of the decision itself — not to the importance or
>   breadth of the surrounding system.
> - Once the recommendation is adequately supported, stop: deliver the decision and the
>   decisive rationale, plus at most the assumptions or reversal conditions that would
>   change it. Do not append roadmaps, policies, fallbacks, checklists, or standing
>   mechanisms unless the request asks for them.
> - Weigh subtraction equally with addition: an option that removes or simplifies an
>   existing rule, step, or mechanism competes on equal standing with additive options.
>   Among adequately supported options, prefer the smaller durable surface and lower
>   lock-in; surface the tradeoff when a higher-lock-in option genuinely serves the
>   request better.

Same discipline as rule 1: general terms only, smallest wording that fits the skill's
existing voice and section structure, no restructuring, no scope expansion. If the
skill already carries an equivalent proportionality rule, report that instead of
duplicating it.

## Hard constraints

- **Global blast radius.** This skill is used across every project that loads it. Treat
  the change as high-lock-in: minimal, voice-matching, reviewed before it lands.
- **Deployment-gated.** Route the change through the skill's own review and deployment
  process. Do not self-deploy, promote, shadow, or install. If the skill is "source-only
  until an explicit deployment turn," respect that — produce the source edit and stop at
  the deployment gate.
- **Adversarial review recommended before landing.** Given the blast radius, have an
  independent reviewer check that (a) each rule is correct general epistemics/decision
  discipline, (b) it does not contradict or duplicate the skill's existing Strict-Claims
  or decision-discipline language, and (c) it carries no domain leakage. Findings-first;
  the reviewer holds no deployment authority.
- **No project leakage.** Nothing from the originating project (paths, examples, lifecycle
  labels, product facts) enters the skill text.

## Process

1. **Locate + confirm** the skill's canonical source (else `BLOCKED_SOURCE_UNCONFIRMED`).
2. **Draft** the smallest domain-agnostic edits (both rules) into the Strict-Claims /
   decision-discipline section, matching the skill's existing voice.
3. **Adversarial review** the draft (correctness, non-duplication, no leakage — for
   each rule); revise.
4. **Route to deployment** through the skill's own gate; stop at the gate if deployment is
   not authorized this turn.
5. **Report** the source path edited, the diff, the review outcome, and the deployment
   state (landed vs awaiting gate) — observed, not assumed.

## Boundaries / non-claims

- The deliverable for the Orca side was **this prompt**, not the edit. Nothing here grants
  Orca authority over the skill or claims the edit is done.
- This is an advisory commission. It is not validation, readiness, approval, or deployment
  authorization for the skill.
- The provenance pointer to Orca's grading-rubric doc is **context only** — its content
  must not be copied into the skill.
