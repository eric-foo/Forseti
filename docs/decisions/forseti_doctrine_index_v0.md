# Forseti Doctrine Index v0 (router, not authority)

```yaml
retrieval_header_version: 1
artifact_role: Doctrine index (router only — on conflict, each doctrine's own record wins and this index is the stale party)
scope: >
  One place to find every binding Forseti doctrine: cross-cutting rules, lenses,
  and contracts agents and the owner must follow, scattered across the kernel,
  the overlay, decision records, and product lanes. Derived from a repo-wide
  sweep 2026-06-11. Lists and points; binds nothing itself.
use_when:
  - Finding whether a doctrine exists before authoring or re-deciding one.
  - Loading the owning doctrine for doctrine-changing work.
  - Registering a newly adopted doctrine (one row; owner-gated by the adoption itself).
authority_boundary: retrieval_only
open_next:
  - AGENTS.md                                   # kernel triggers (smallest complete; mini god tier)
  - .agents/workflow-overlay/README.md          # overlay authority entry
  - .agents/workflow-overlay/source-of-truth.md # source hierarchy + DCP contract
stale_if:
  - A doctrine is adopted, superseded, or dropped without a row update here.
  - review_by 2026-12-11 passes without an owner review of this index.
```

## Why an index of doctrines is allowed when a venue registry was not

This is a maintained list — the genus the venue-registry rejection killed. It
survives on a different profile: doctrines are few, change rarely, and every
change already requires targeted propagation through its owning source, so a
row update is part of that bounded change rather than a separate lifecycle.
Owner: Eric. Review_by: 2026-12-11.

## Kernel triggers (AGENTS.md — load every session automatically)

| Doctrine | Trigger | Full statement |
| --- | --- | --- |
| Smallest Complete Intervention Doctrine | "smallest complete X" | AGENTS.md (self-contained) |
| Mini God Tier Doctrine | "mini god tier" / "god tier but small" | docs/decisions/forseti_mini_god_tier_doctrine_v0.md |

## Overlay-bound doctrine (`.agents/workflow-overlay/` — authority files; read per AGENTS.md before project work)

| Doctrine | File | Binds |
| --- | --- | --- |
| Source hierarchy + DCP | source-of-truth.md | Source precedence; doctrine-change propagation contract; checkpoint rules |
| Artifact Folders Doctrine | artifact-folders.md | Accepted folders + placement rules. Decision layer (subset): `docs/decisions/forseti_repo_structure_binding_v0.md` |
| Retrievability Doctrine | retrieval-metadata.md | The `retrieval_header_version: 1` header schema on every durable artifact |
| Validation gates | validation-gates.md | Required gates before completion claims |
| Safety + authorization | safety-rules.md | Forbidden drift; implementation boundaries |
| Decision Routing Doctrine | decision-routing.md | Cynefin pre-planning regime routing for non-trivial work |
| Prompt Orchestration Doctrine | prompt-orchestration.md | Prompt families, output modes |
| Review Lanes Doctrine | review-lanes.md | Review lanes, reviewer permissions |
| Communication style | communication-style.md | Response style, chat topology |
| Template registry | template-registry.md | Prompt template registry |
| Product-proof semantics | product-proof.md | Buyer-proof definitions, non-claims |
| Source Loading Doctrine | source-loading.md | Read packs, context budgets |
| Skill Adoption Doctrine | skill-adoption.md | Skill source boundaries |
| Artifact roles | artifact-roles.md | Role bindings, freshness markers |
| Delegated review-patch (bound, opt-in commission) | delegated-review-patch.md | High-stakes artifact hardening lane |

## Decision-record doctrine (docs/decisions/)

| Doctrine | File | Status |
| --- | --- | --- |
| Mini God Tier Doctrine (record; kernel trigger above) | forseti_mini_god_tier_doctrine_v0.md | OWNER-ADOPTED 2026-06-11 |
| Artifact Folders Doctrine — decision layer (subset) | forseti_repo_structure_binding_v0.md | OWNER-AUTHORIZED v0 |
| Distillation Doctrine — adoption index + spine bindings | distillation_doctrine_orca_spine_bindings_v0.md | PREPARE-ONLY |
| Distillation Doctrine subset — enforcement-placement classification | overlay_enforcement_placement_classification_v0.md | PREPARE-ONLY (EP-01/03/06 substrates built) |
| Distillation Doctrine subset — overlay-governance binding | distillation_binding_overlay_governance_v0.md | PREPARE-ONLY DRAFT |
| Pre-sale execution evidence tiers | judgment_spine_pre_sale_execution_evidence_tier_policy_v0.md | ACTIVE |
| Deletion-Evidence Doctrine (governed-deletion safety; register + strict gate) | deletion_evidence_doctrine_v0.md | ACTIVE — `check_deletion_evidence.py --strict` in ci.yml; register `deletion_evidence_register_v0.yaml` |
| Ontology<->Runtime Drift-Check Contract (W2b leak-surface semantics) | ontology_runtime_drift_check_contract_v0.md | OWNER-RATIFIED 2026-06-19 — `check_ontology_drift.py --strict` in ci.yml |
| Repo-Map Architecture (Mini God Tier) — map/submap/header tiers, generated index/health, recent-change satellite, promotion-on-touch + coverage invariant | forseti_repo_map_architecture_mgt_v0.md | OWNER-LOCKED STACK 2026-07-02 (design lens; reachability gated by `check_map_links`; generated inventory/health by `header_index`) |
| Code-Slop Taxonomy (reference model + catch-layer decisions) | forseti_code_slop_taxonomy_v0.md | OWNER-DIRECTED 2026-07-18 (reference model; records decisions already embodied in the landed duplication gate, the SCI kernel, and the review lane; binds nothing new) |

## Product-spine doctrine (`forseti/product/`)

| Doctrine | File | Status |
| --- | --- | --- |
| Claim defense (external claims policy) | `forseti/product/spines/product_lead/proof_charter/forseti_claim_defense_doctrine_v0.md` | OWNER_SIGNED_OPERATIVE 2026-06-11 |
| Judgment-spine evidence ladder | `forseti/product/spines/judgment/claim_ladder/judgment_spine_evidence_ladder_architecture_v0.md` | ACTIVE (claim-tier architecture) |
| Data-capture obligation contract | `forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md` | CONTRACT_DRAFT_V0_AMENDED_2026_06_05 (doctrine-adjacent) |

## Dropped (do not re-open without a dated owner decision)

| Doctrine | File | Status |
| --- | --- | --- |
| Deleted-comment signal retrieval | docs/decisions/data_capture_spine_deleted_comment_signal_retrieval_scoped_doctrine_decision_v0.md | DROPPED 2026-06-08 (re-open guard) |

## Naming Note (owner-directed, 2026-06-11)

Rows above carry explicit "Doctrine" names per owner direction (SCI, MGT,
artifact folders, retrievability, decision routing, prompt orchestration,
review lanes, source loading, skill adoption; repo-structure binding subsumed
as the Artifact Folders Doctrine's decision layer; distillation grouped with
its subsets). Index-label renames only: the underlying FILES are not renamed —
overlay paths are load-bearing (hook configs, AGENTS.md, dozens of open_next
pointers reference them); a physical rename would be a propagation pass of its
own, owner-gated.

## Non-Claims

Router only: registration here is not adoption, validation, or authority —
each doctrine's own record and the overlay govern. Statuses above are as
reported by the 2026-06-11 sweep plus this lane's own session verifications
(MGT, retrieval-metadata, distillation index, folder binding, plus a 2026-06-20
reconciliation that added the deletion-evidence, ontology<->runtime drift-check,
and repo-map-architecture (MGT) rows from primary-source reads, with their gates
confirmed in `.github/workflows/ci.yml`); verify a status
against its record before relying on it for a strict claim.
