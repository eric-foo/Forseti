---
name: forseti-loss-first-implement
description: "Implement an authorized Forseti change by binding the highest-loss plausible false green, the minimum authority/transition/closure invariants that prevent it, one loss-first falsifier, and the repository-owned validation route. Use only when the user explicitly invokes $forseti-loss-first-implement, /forseti-loss-first-implement, or instructs 'loss-first implement' for a Forseti change. Do not trigger for ordinary implementation, planning-only work, review-only work, discussion of the method, mechanical edits that do not use the instruction, or work without implementation authority."
---

# Forseti Loss-First Implement

## Status and authority

Use this owner-authorized Forseti-local candidate only for an explicitly invoked,
already-authorized implementation. It is not accepted, frozen, deployed, or
repository authority. It does not grant implementation, protected-action,
review, validation, merge, or deployment permission.

Load and obey `AGENTS.md` and `.agents/workflow-overlay/README.md`. Let their
owning sources control Forseti facts, Smallest Complete Intervention, isolation,
safety, validation, review routing, and lifecycle actions. If the requested
outcome or implementation authority is missing, stop and name the gap.

## Failure to prevent

Prevent an implementation from choosing an easy falsifier while a more damaging
false green remains possible. Also prevent unnecessary broad validation and
receipt machinery from making a focused, well-bound implementation slower
without catching a distinct defect class.

## Entry boundary

Proceed only when the owner-visible outcome, implementation authority, target
work unit, controlling sources, and observable validation route are sufficiently
bound to edit safely. Return the unresolved owner decision instead of inventing
intent.

For a purely mechanical change, retain the ordinary project fast path and record
`not_required_mechanical`; do not manufacture authority, transition, closure, or
falsifier ceremony.

## Bind the loss-first contract

Before editing, write the smallest useful equivalent of:

```yaml
LOSS_FIRST_CONTRACT:
  success: <owner-visible outcome>
  max_loss_false_green: <most damaging plausible way the work could look successful while failing>
  authority: <source, identity, or bytes that establish truth; not applicable when irrelevant>
  transition: <legal source state/revision/identity -> target state; not applicable when irrelevant>
  closure: <authoritative representations, projections, or consumers that must agree; not applicable when irrelevant>
  falsifier: <cheapest controlled violation of the highest-loss applicable invariant>
  validation_route: <focused checks plus only repository-required broader gates>
  claim_ceiling: <largest conclusion the planned observations can support>
```

Keep this contract transient unless another authorized consumer genuinely needs
a durable artifact. Use one line or a compact paragraph when that preserves the
same decisions.

### Bind only applicable integrity surfaces

- **Authority:** Identify what independently establishes truth. When a decision,
  admission, identity, or eligibility claim is content-addressed, recompute it
  from the controlling source or bytes; do not accept a stored self-assertion as
  its own proof.
- **Transition:** Name the exact admissible starting state, stable identity,
  revision or generation, target state, replay behavior, and mutable fields that
  must not become identity guards.
- **Closure:** Name every authoritative representation or consumer whose
  disagreement would leave the requested outcome false. Do not equate one
  updated view with semantic closure across human, machine, generated, indexed,
  or runtime surfaces.

Mark an inapplicable surface `not_applicable` rather than inventing content.

## Choose the falsifier by loss

1. List the plausible false greens exposed by the applicable integrity
   surfaces.
2. Rank them by consequence to the owner-requested outcome, not by ease of
   demonstration.
3. Choose the cheapest falsifier that attacks the highest-loss plausible false
   green at the intended boundary.
4. Make a wrong-cause check prove that an earlier unrelated guard is not what
   rejects the mutation.
5. Prefer one focused table-driven test or recomputation containing the minimum
   near-miss variants over several orchestration passes.

For authority or durable-state work, prefer tampering, stale revision, illegal
state, identity substitution, replay, or partial-write variants over a generic
missing-record check when those variants carry greater loss. For multi-view
work, falsify semantic agreement across the named closure set rather than an
easier minor receipt.

If no affordable observation can distinguish the highest-loss false green,
narrow `claim_ceiling` or stop for missing observability. Do not substitute an
easier test and retain the stronger claim.

## Implement falsifier-first

1. Inspect only the bounded authority and implementation seams.
2. Author or identify the focused falsifier before production edits when
   practical.
3. Observe a controlled pre-change failure caused by the missing behavior. If
   the surface does not yet exist, record that fact and use the smallest
   controlled post-build mutation that proves fail capability.
4. Make the Smallest Complete Intervention. Trace every changed line to the
   success outcome, an applicable invariant, or required validation.
5. Run the falsifier green after implementation. Keep the violating and restored
   controls inside the focused test or recomputation when that avoids extra
   mutation-and-restoration commands.

Preserve real failure visibility. Do not add a fallback, registry, framework,
standing checklist, review pass, or durable receipt merely to make the method
look rigorous.

## Validate once at the owning boundary

Run, in order:

1. the loss-first falsifier and its wrong-cause control;
2. the owner-visible happy path;
3. focused tests for the named authority, transition, closure, and affected
   integration surfaces; and
4. only the broader gates required by the repository's controlling validation
   predicate.

Do not interpret "broader required gate" as an automatic full test suite. Run a
full suite only when the repository requires it or the change is sufficiently
cross-cutting that focused ownership cannot cover the affected surface. Run it
once, after focused checks are green. If an earlier required broad run fails and
the fix changes behavior, rerun it; do not rerun successful validation merely to
produce a different receipt shape.

Prefer native command output over a custom wrapper whose only purpose is to
reformat evidence. Preserve actual exits and outputs. Record `NOT_OBSERVED` for
unavailable tool duration, billed cost, live state, or other unmeasured claims.

## Review and closeout

Apply only the repository's controlling review predicate. Do not infer that this
candidate commissions self-review, delegated review, or review-and-patch. Report
an unavailable required lane as a blocker rather than silently changing the
review method.

Close out with observed facts only:

```yaml
LOSS_FIRST_CONTRACT:
IMPLEMENTATION:
FALSIFIER_RESULT:
VALIDATION:
RESIDUALS:
REVIEW_ROUTING_STATUS:
CLAIM_CEILING:
```

Use `IMPLEMENTED_AND_VALIDATED` only when the owner-visible result and required
validation were observed. Otherwise report the precise incomplete or blocked
state; never convert missing evidence into success.

## Candidate metadata

- Source boundary: Forseti-local `.agents` candidate source only.
- Positive triggers: `$forseti-loss-first-implement`; `/forseti-loss-first-implement`;
  `loss-first implement this authorized Forseti change`.
- Negative triggers: ordinary implementation, planning-only requests,
  review-only requests, method discussion, non-invoked mechanical edits, and
  work without implementation authority.
- Collision check: no same-name Forseti project, Claude project, user
  Codex/Agents/Claude, or installed plugin-cache skill directory observed on
  2026-08-11 before creation.
- Rollback: remove this candidate directory and its entry from
  `.agents/workflow-overlay/skill-adoption.md`; revert its behavioral-changelog
  entry. Do not modify upstream Success Implement, plugin, cache, user-level, or
  Claude deployment copies.
