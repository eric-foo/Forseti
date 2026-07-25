# Forseti Workflow Overlay

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Overlay entrypoint and binding rule for Forseti project work.
use_when:
  - Starting Forseti project work.
  - Resolving which overlay section owns a project rule.
authority_boundary: retrieval_only
```

This overlay is the project authority for Forseti. Skills may provide task-local mechanics, but Forseti-specific facts and constraints must come from this folder or another Forseti-owned source named here.

## Behavioral Admission

Every behavioral rule in this overlay is subordinate to the Smallest Complete
Intervention doctrine in `AGENTS.md`. A standing step, field, receipt, gate,
review pass, hook, checker, artifact, or synchronization obligation earns a
place here only when removing it would make the bound outcome false or
materially fragile and it catches a named defect class at the lowest-cost
effective boundary.

Importance, novelty, doctrine impact, cross-lane wording, or a desire for more
evidence does not by itself justify recurring ceremony. Prefer a scoped trigger
or deterministic boundary check over a universal actor-carried obligation.
Retire temporary mechanisms when their stop condition fires or their own
evidence shows that the collection burden does not affect the decision it was
meant to improve. Preserve historical evidence in its workflow record and Git
history; do not keep it resident in live authority.

## Overlay Sections

- `project-authority.md`: project identity, boundary, and unknown facts.
- `source-of-truth.md`: Forseti source hierarchy, conflict rules, and doctrine-change propagation contract.
- `source-loading.md`: source-loading budgets, read packs, and context-bloat controls.
- `decision-routing.md`: Cynefin Routing Layer for work where uncertainty about decomposition, authority, source truth, or sequencing could materially change the next move.
- `artifact-folders.md`: accepted Forseti artifact locations.
- `artifact-roles.md`: role bindings, permissions, freshness markers, and paired artifacts.
- `retrieval-metadata.md`: lightweight retrieval-header contract for durable human-authored workflow artifacts.
- `prompt-orchestration.md`: lightweight Forseti prompt artifact, wrapper, preflight, output mode, and rerun rules.
- `template-registry.md`: Forseti-owned prompt template registry for project-local templates.
- `product-proof.md`: buyer-proof semantics, trust-objection handling, pull signals, zero-spoiler backtest behavior, and product-proof non-claims.
- `communication-style.md`: Forseti response style for Chief Architect sequencing, review closeouts, and prompt handoffs.
- `validation-gates.md`: checks required before claiming completion.
- `review-lanes.md`: read-only review lanes, patch/integration execution boundaries, and template retrieval rules.
- `batch0-process-pilot.md`: retired compatibility pointer to the preserved Batch 0 evidence record.
- `delegated-review-patch.md`: bound, opt-in Delegated Review-and-Patch commission lane for high-stakes authored artifacts and bounded code diffs, and the overlay-interface fields a future skill implementation may read. Activates only by explicit Chief Architect commission; never mandatory or machine-routable.
- `safety-rules.md`: project-specific safety and forbidden drift.
- `skill-adoption.md`: skill source, shadow, and adoption status.

## Binding Rule

If external workflow guidance or skill mechanics conflict with this overlay for Forseti project facts, this overlay wins unless a later accepted Forseti decision supersedes it.

Missing required project facts are `UNKNOWN - requires owner input`; do not fill them from `jb` or generic defaults.
