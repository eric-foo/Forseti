# Value-Lens Review of the Understanding Cycle — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Owner-commissioned review of the Understanding cycle through two
  bound lenses: (1) a competitive-intelligence lens — does each cycle
  stage produce decision-grade CI, and (2) the no-price-war lens —
  Forseti clients never fight on price; at $19-vs-$19 the move is
  never $18, it is making the product one consumers WANT to pay
  $20-21+ for. The deliverable is a findings note on where the cycle
  serves or fails these lenses, plus a candidate operational
  definition of "value" as willingness-to-pay premium earned by
  material value - proposed for owner ratification, never installed
  by this commission.
use_when:
  - The owner dispatches this review (commissioned 2026-07-29).
stale_if:
  - The owner ratifies a value definition (this handoff's central
    open then closes).
  - The Understanding-cycle stages are materially restructured.
authority_boundary: retrieval_only
next_source: competitor_ledger_spec_v0.md (value doctrine, J5);
  complaints_axis_v0.md (strategy section); the Deliver-lane repair
  note for the playbook boundary.
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging - a value-lens work folder under C:\tmp; repo
    docs only if the owner later ratifies the proposed definition or
    routes a findings snapshot.
  input_prompt_source: docs/prompts/handoffs/value_lens_understanding_cycle_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    NONE NEEDED - pure doctrine/artifact review over already-committed
    sources and already-captured evidence. Zero new captures.
  targets: the staging folder only; no doctrine installs - the value
    definition is proposed, not installed.
  reviews: findings-first; no formal verdict bound.
```

## The two lenses (owner statement, 2026-07-29)

1. **CI lens.** Walk the Understanding cycle stage by stage (capture
   -> harvest/typing -> axes -> ledger -> consolidation -> Deliver
   inputs) and assess each stage as competitive intelligence: does
   its output change what a client would DO against a named
   competitor? Name stages that produce description rather than
   decision-grade CI.
2. **No-price-war lens.** Standing doctrine: Forseti reads VALUE
   competition and never helps a subject compete on price. The owner
   sharpened the direction: at price parity ($19 vs $19) the answer
   is never cutting to $18 - it is identifying and building the
   material value that makes consumers WANT to pay $20-21+. Audit
   every cycle output that touches price (J5 floors, response-trap,
   value-exit reads, equivalence claims) for whether it feeds
   premium-direction moves (defensible differentiation, axis
   ownership, equivalence refutation) or could be misread as
   price-move advice. Flag every misreadable surface.

## Bound deliverables

1. Stage-by-stage findings under both lenses, evidence-cited (the
   calibrated instruments and pilot specimens are the evidence base;
   no new capture).
2. A CANDIDATE operational definition of "value" in the
   willingness-to-pay-premium direction, with: what evidence the
   cycle already captures that speaks to it (choice statements with
   stated causes, delight axes, value-exit reads, J5 per-unit
   normalization), what it would additionally need, and 2-3 rejected
   alternative formulations with reasons. Proposed for owner
   ratification - the doctrine's "value is deliberately left
   undefined" line stays until the owner ratifies.
3. Named boundary risks: places where a client could read our
   deliverables as price advice, each with the smallest wording or
   structure change that closes the misreading.

## Standing non-claims

This commission installs nothing. Counts of observed evidence only.
The value definition remains owner-gated; prior over-anchored
formulations (retired 2026-07-28) are cautionary specimens - do not
re-derive a definition from a single pilot's evidence.
