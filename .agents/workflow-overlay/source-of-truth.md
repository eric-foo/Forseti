# Source Of Truth

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Source hierarchy, conflict rules, doctrine-change propagation, and known source documents.
use_when:
  - Resolving Forseti source precedence.
  - Checking whether a document is a known Forseti source.
  - Changing product, architecture, workflow, validation, review, output, or lifecycle doctrine.
authority_boundary: retrieval_only
```

## Current Source Hierarchy

1. Explicit user instruction for the current turn.
2. Forseti `AGENTS.md`.
3. This overlay under `.agents/workflow-overlay/`.
4. Forseti docs under `docs/`, when they do not conflict with the overlay.
5. Explicitly invoked or resolver-loaded skills may provide task-local mechanics only; they are not Forseti project authority.

## Conflict Rules

- Forseti overlay wins for Forseti project facts.
- External workflow sources do not own Forseti project authority. Skills may provide task-local mechanics only when explicitly invoked or resolver-loaded.
- Installed global/user/plugin skills are runtime copies or external tools, not Forseti project authority.
- If a required source is missing, report a visible failure and name the missing file or decision.
- Source hierarchy is not a read-all list. Use `.agents/workflow-overlay/source-loading.md` and `docs/workflows/forseti_repo_map_v0.md` to choose bounded source packs.

## Checkpoint Artifacts

Checkpoint artifacts capture transient lane state for recovery or transfer:
precompact working packets (`workflow-precompact`, under `docs/hygiene/`), cold
cross-lane handoff packets (`workflow-handoff`), and any equivalent lane-state
resume/snapshot note. They are convenience copies, never a Forseti source of truth.

- Non-authoritative. A checkpoint's volatile claims — what is built, what is
  authorized, current doctrine, or "where we are" — are orientation only.
  Re-confirm any such claim against the canonical source (the owning
  decision/contract/overlay), or against disk for build state, before relying on
  it. The source hierarchy above governs; a checkpoint never overrides it, even
  when more recent.
- Single-consumption, one live instance per lane. A checkpoint exists to be consumed once; the consuming lane deletes it after recovery checks run and live state is re-established. Refresh by overwriting in place under a stable name — do not accumulate `_v2`/`_v3` copies. A checkpoint whose work has landed (committed/settled) is retired by deletion. A transport-only commit that stabilizes packet bytes for a receiver does not mean the underlying work has landed.
- Point, do not copy. When a checkpoint must carry a volatile fact, record a
  pointer plus a re-confirm instruction (for example "authorization -> <decision>;
  build state -> glob disk"), not a copied snapshot that silently goes stale.

This binds how Forseti uses the `workflow-precompact` and `workflow-handoff` skills:
the skills supply mechanics, this overlay owns the lifecycle. It does not apply to
Forseti source-of-truth artifacts (decisions, contracts, architecture records) or to
pointer-indexes (the repo map, this overlay) — those are the canonical sources a
checkpoint points to and must never be deleted as "consumed." It also does not
apply to authored handoff *prompts* under `docs/prompts/handoffs/` (the
Planning/Implementation handoff prompt role): those are docs-only prompt
artifacts, not lane-state checkpoints, and keep their own role lifecycle.

## Doctrine Change Propagation Contract

Doctrine-changing work is any source-changing edit that changes a durable rule
future agents may follow for product doctrine, architecture doctrine, workflow
authority, validation philosophy, review authority, output authority, or a
lifecycle boundary.

Before claiming completion for doctrine-changing work, update the controlling
source and check the downstream source-loaded surfaces that could continue to
route agents by stale doctrine. At minimum, consider:

- top-level agent instructions such as `AGENTS.md` and `CLAUDE.md`;
- the controlling overlay file under `.agents/workflow-overlay/`;
- start-route and source-loading surfaces such as
  `.agents/workflow-overlay/source-loading.md` and
  `docs/workflows/forseti_repo_map_v0.md`;
- executor, prompt, validation, review, and closeout surfaces when the doctrine
  affects them.

Keep propagated restatements faithful to the controlling source's strength. A
restatement in a downstream surface must not soften or narrow the controlling
rule — for example a `required`/`must` weakened to "add when known" — nor
silently fork it. Where the same wording would otherwise be copied across
surfaces, prefer pointing them at the single controlling source over duplicating
it, so the copies cannot desynchronize.

Record propagation evidence in the PR body or final closeout by default: name
the controlling source, downstream routers checked, any intentionally unchanged
surface, and the targeted stale-language search. This is lifecycle evidence for
the current change, not new source authority.

Do not add an inline receipt merely because doctrine changed. A durable
`direction_change_propagation` receipt is exceptional: create one only when a
distinct future consumer or lifecycle cannot use the PR/closeout evidence
without reconstructing the authoring work. Keep it compact and colocated with
that consumer; never create a standalone receipt file or append the frozen
legacy archive. Existing receipts are historical provenance, not live rules.

When an exceptional durable receipt is required, use the seven controlled
trigger values in this shape:

```yaml
direction_change_propagation:
  doctrine_changed: "<one sentence>"
  trigger: product_doctrine | architecture_doctrine | workflow_authority | validation_philosophy | review_authority | output_authority | lifecycle_boundary
  related_triggers: [] # optional
  controlling_sources_updated: ["<path>"]
  downstream_surfaces_checked: ["<path>"]
  intentionally_not_updated:
    - {path: "<path>", reason: "<why unchanged>"}
  stale_language_search: "<query, or not_run + why — not_run only for a purely additive change>"
  non_claims: ["not validation", "not readiness"]
```

If propagation cannot be completed, report the blocking surface and allowed
next step in the PR/closeout instead of claiming completion. Use a durable
blocker only when the same distinct-consumer test above requires one:

```yaml
direction_change_propagation_blocker:
  doctrine_changed: "<one sentence>"
  trigger: product_doctrine | architecture_doctrine | workflow_authority | validation_philosophy | review_authority | output_authority | lifecycle_boundary
  related_triggers: [] # optional
  blocking_surface: "<missing, conflicting, or unchecked path/source>"
  attempted_check: "<what was attempted>"
  allowed_next_step: "<narrow action that would unblock propagation>"
  non_claims:
    - "not validation"
    - "not readiness"
```

The receipt or blocker is propagation evidence only. It is not validation,
readiness, approval, acceptance, proof, implementation authorization, or source
promotion.

## Known Source Documents

- `README.md`: intentionally non-authoritative front page; not a workspace entrypoint. Use `docs/workflows/forseti_repo_map_v0.md` or `.agents/workflow-overlay/README.md` for real entry.
- `AGENTS.md`: agent operating instructions.
- `CLAUDE.md`: Claude Code instruction shim that imports `AGENTS.md`; no Forseti project authority of its own.
- `.agents/workflow-overlay/README.md`: overlay entrypoint.
- `.agents/workflow-overlay/artifact-roles.md`: Forseti artifact role bindings, permissions, freshness markers, and paired artifacts.
- `.agents/workflow-overlay/source-loading.md`: Forseti source-loading budgets, read packs, and context-bloat controls.
- `.agents/workflow-overlay/decision-routing.md`: Forseti Cynefin Routing Layer for work where uncertainty about decomposition, authority, source truth, or sequencing could materially change the next move.
- `.agents/workflow-overlay/retrieval-metadata.md`: Forseti retrieval-header contract for durable human-authored workflow artifacts.
- `.agents/workflow-overlay/prompt-orchestration.md`: Forseti prompt artifact, wrapper, preflight, output mode, validation, and rerun bindings.
- `.agents/workflow-overlay/template-registry.md`: Forseti-owned prompt template registry for project-local templates.
- `.agents/workflow-overlay/product-proof.md`: Forseti buyer-proof semantics, trust-objection handling, pull signals, and product-proof non-claims.
- `.agents/workflow-overlay/communication-style.md`: Forseti response style for Chief Architect sequencing, review closeouts, and prompt handoffs.
- `.agents/workflow-overlay/delegated-review-patch.md`: bound opt-in Delegated Review-and-Patch commission lane; activates only by explicit Chief Architect commission, and its returns stay decision input under the strict-claim boundary.
- `docs/STRUCTURE.md`: docs-folder usage guide for future agents; subordinate to this overlay if conflicts appear.
- `docs/workflows/orca_bootstrap_record.md`: Turn 6 bootstrap record.
- `docs/workflows/forseti_repo_map_v0.md`: compact repo map for source-pack selection and prompt setup.
- `docs/workflows/data_capture_spine_consolidation_map_v0.md`: retrieval-only entry map for Data Capture Spine and Source Capture Armory navigation; routes to owner sources, no source-access/validation/readiness/implementation authority.
- `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md`: retrieval-only entry map for Judgment Spine navigation; routes to owner sources, no validation/readiness/buyer-proof/scoring/model-execution/judgment-quality authority.
- `docs/migration/import_queue.md`: read-only import queue state.
- `docs/decisions/dcp_receipts_archive_v0.md`: frozen legacy receipt history; retrieval-only, no source authority, no new writes, and not part of ordinary doctrine work.
- `docs/decisions/forseti_rename_migration_policy_v0.md`: rename policy binding Forseti as the canonical project/product name and Orca as the legacy alias; controls live-vs-historical rename classes and compatibility migration sequencing.
- `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md`: current Forseti product thesis (owner-ratified direction 2026-07-14): a decision-adjudication product, beauty first application, bounded Decision Sprint initial form, exact buyer and first decision family deferred to GTM, and later product forms gated on repeated decisions and outcomes.
- `docs/decisions/forseti_product_thesis_evidence_adjudication_v0.md`: superseded 2026-07-12 capability-reset thesis, retained as historical product input; its decision-relative evidence-weighting and human-judgment-now principles continue through the successor.
- `docs/decisions/forseti_product_thesis_consumer_demand_v0.md`: superseded consumer-demand / beauty-first thesis, retained as historical product input rather than current direction.
- `forseti/product/spines/judgment/claim_ladder/judgment_spine_evidence_ladder_architecture_v0.md`: Judgment Spine claim-tier architecture for Product-Learning, Buyer-Proof, and Judgment-Quality evidence boundaries.
- `forseti/product/spines/judgment/conductor/judgment_spine_gate_ownership_map_v0.md`: Judgment Spine gate ownership map for source identity, packet freeze, no-tools isolation, memorization probe, sealed output, scoring, reveal/calibration, classification, and closeout blockers.
- `forseti/product/spines/judgment/conductor/judgment_spine_reveal_calibration_owner_contract_v0.md`: JSG-08 owner contract for outcome reveal/calibration receipt shape, satisfaction states, scoring relationship, and claim caps.
- `docs/workflows/turn_08_workflow_bedrock_maximization.md`: docs-first maximization plan for `workflow-deep-thinking`, future `workflow-product-ultraplan`, and future `workflow-feature-ultraplan`.
