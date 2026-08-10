# Forseti Repo Map v0

```yaml
retrieval_header_version: 1
artifact_role: Repository map
scope: Curated T1 navigation map for Forseti source loading and cold routing; not a per-file inventory.
use_when:
  - Choosing a bounded source pack before a CA prompt, review prompt, or product artifact.
  - Orienting a new thread without bulk-loading the repository.
  - Finding a decisive file, major area, active-hook owner, submap, or compatibility route.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/source-loading.md
  - .agents/workflow-overlay/source-of-truth.md
  - docs/decisions/forseti_repo_map_architecture_mgt_v0.md
stale_if:
  - A top-level repo or docs area is added, removed, or repurposed.
  - A direct forseti-harness/ area or major product spine is added, removed, or reorganized.
  - A registered submap moves or no longer provides its delegated route.
  - Active-hook ownership or activation surfaces move.
  - .agents/workflow-overlay/source-of-truth.md changes source hierarchy or doctrine propagation.
  - A later repo-map artifact supersedes this file.
```

- Status: `ACTIVE_RETRIEVAL_MAP`
- Refreshed: 2026-07-20
- Implementation authorized: no
- Architecture: `docs/decisions/forseti_repo_map_architecture_mgt_v0.md`

## Start Here

Use this map to choose the smallest source pack. It is high-level authority plus
a router, not product authority and not a ledger of repository contents.

1. For source precedence, open `.agents/workflow-overlay/source-of-truth.md`.
2. For read budgets and recurring packs, open
   `.agents/workflow-overlay/source-loading.md`.
3. For a common fact lookup, use the Decisive-File Quick Index below.
4. For dense Capture, ECR, or Judgment routing, open the registered submap and
   do not reconstruct its inventory here.
5. For a complete file-level catalog, run
   `python .agents/hooks/header_index.py --index`; do not add those rows here.

Detailed low-conflict change context may live under
`docs/workflows/repo_map_recent_changes/`. Those notes are satellites, not route
truth, and do not replace a required map, submap, or retrieval-header update.

## T1 Admission Control

The central map owns only the T1 classes bound by
`docs/decisions/forseti_repo_map_architecture_mgt_v0.md`: decisive fast routes,
major areas, active-hook discovery, source-pack entry points, the submap
registry, compatibility/migration routes needed for cold resolution, and map
non-claims.

Before adding or materially expanding a central-map row, the author and reviewer
must identify the T1 class it serves and explain why an existing submap,
retrieval header, area row, or generated `header_index.py --index` route is not
sufficient. A valid path is not sufficient admission evidence. Per-file
inventory, runner lists, historical status chronology, embedded operating
manuals, and descriptions duplicated from an owning source stay out of T1.

This is a judgment gate. `check_map_links.py`, `header_index.py`, and
`check_repo_map_freshness.py` continue to enforce only their documented
mechanical boundaries; a green check does not admit a row to T1.

## Decisive-File Quick Index

Open the named file directly when the question matches. These are shortcuts,
not changes to source precedence.

| Question | Open directly |
| --- | --- |
| Source hierarchy or doctrine-change propagation | `.agents/workflow-overlay/source-of-truth.md` |
| Source packs and read budgets | `.agents/workflow-overlay/source-loading.md` |
| Artifact folders and placement | `.agents/workflow-overlay/artifact-folders.md` |
| Validation gates and checker boundaries | `.agents/workflow-overlay/validation-gates.md` |
| Technical diagnostics for recurring workflow or tooling failures | `docs/workflows/technical_difficulties_log_v0.md` |
| General workflow and tool efficiency methods, cases, measurements, and dogfood records | `docs/workflows/efficiency/README.md` |
| Fixed cold-agent vendor-admission tool-calling dogfood case | `docs/workflows/efficiency/tool_calling_dogfood_case_v0.md` |
| Prompt or review-prompt work | `.agents/workflow-overlay/prompt-orchestration.md` |
| Current product direction and initial form | `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md` |
| Beauty product application, decision admission, and proof boundary | `forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md` |
| One-company intelligence information requirements, paid-access choice, decision modules, and Company Surface boundary | `docs/decisions/forseti_company_intelligence_information_architecture_v0.md` |
| Commission or execute a Forseti Intelligence Cycle | `forseti/product/spines/commission_signal_board/README.md`, then `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md` |
| Offer, ICP/wedge, buyer proof, or GTM | For the current US Beauty discovery run, start with `forseti/product/spines/product_lead/gtm/forseti_beauty_us_problem_discovery_to_wedge_contract_v0.md`; otherwise start with the current thesis above, then the matching `forseti/product/spines/product_lead/` area. Buyer-specific bindings remain suspended until GTM rebinds them. |
| Fragrance facts and per-fact provenance | `forseti/product/spines/foundation/ontology/fragrance_reference_v0.yaml` |
| Ontology roster, namespaces, and typed links | `forseti/product/spines/foundation/ontology/ontology.yaml` |
| Scanning, answer-engine, or search-interest work | `forseti/product/spines/scanning/README.md` |
| Any LinkedIn task | `forseti/product/spines/scanning/source_families/linkedin/data_capture_spine_linkedin_lane_index_v0.md` |
| Data Capture or source-access orientation | `docs/workflows/data_capture_spine_consolidation_map_v0.md` |
| Known source capture-to-lake route | `forseti/product/spines/capture/core/source_families/README.md` |
| Silver/Vault authoritative records, retrieval, or reader rules | `docs/decisions/silver_vault_goal_frame_ratification_v0.md`, then `forseti/product/spines/data_lake/authority/core_spine_v0_data_lake_silver_vault_record_contract_v0.md` and `forseti/product/spines/data_lake/authority/core_spine_v0_data_lake_consumption_seam_contract_v0.md` |
| Source-capture access / anti-blocking components | `forseti/product/spines/capture/core/source_capture_toolbox/README.md` |
| ECR source-side orientation | `docs/workflows/ecr_spine_submap_v0.md` |
| Judgment Spine orientation or claim/gate routing | `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md` |
| Creator ideal audience or commercial creator-fit method | `forseti/product/spines/creator_signal/creator_ideal_audience_distillation_deck_v0.md` |
| Pack a judgment view or author a packing adapter | `forseti/product/spines/packing/README.md`, then `forseti/product/spines/packing/authority/packing_spine_v0_serialization_contract_v0.md` |
| Cross-spine research-engine grouping | `docs/workflows/forseti_research_engine_map_v0.md` |
| Repo-map architecture and T1/T2/T3 boundary | `docs/decisions/forseti_repo_map_architecture_mgt_v0.md` |
| Rename compatibility boundary | `docs/decisions/forseti_compatibility_migration_boundary_v0.md` |

The Silver/Vault row is a decisive-fast-route T1 entry. The generic Data Lake
area row is insufficient for a cold reader because it does not distinguish
Silver Authority from generated Silver Retrieval or from other derived artifacts.

The two workflow-efficiency rows are decisive-fast-route T1 entries. The
directory route resolves a real ownership ambiguity among general efficiency,
technical diagnostics, the dated hygiene plan, and the temporary overlay pilot;
the direct case route lets a cold operator reach the fixed dogfood case without
mistaking the generated file index or the directory boundary for its oracle.

## Active Hooks

Active-hook discoverability belongs in T1; hook manuals do not. Open the owning
surface, then confirm activation in tracked configuration. Script presence alone
does not prove activation.

| Need | Owning surface |
| --- | --- |
| Rule semantics, gate boundaries, and non-claims | `.agents/workflow-overlay/validation-gates.md` |
| Per-rule substrate classification and build authority | `docs/decisions/overlay_enforcement_placement_classification_v0.md` |
| Script behavior, modes, wiring, and self-tests | `.agents/hooks/README.md` |
| Portable checker implementations | `.agents/hooks/` |
| Claude activation | `.claude/settings.json` |
| Codex activation | `.codex/hooks.json` |
| CI activation | `.github/workflows/ci.yml` |
| Local Git activation | `.githooks/` and `.github/scripts/install-local-hooks.ps1` |

Current interactive topology is intentionally protection-only: Claude runs the
10-second protected-action guard plus one 5-second SessionStart capsule; Codex
runs its 10-second protected-action adapter only. Claude has no `PostToolUse` or
`Stop` registration and Codex has no `PostToolUse` registration. Durable shape
checks, including placement, activate through CI; dormant `--hook` modes are not
live registrations.

A passing hook or checker establishes only its documented shape boundary. It is
not validation, readiness, approval, source authority, or semantic truth.

## Registered Dense-Area Submaps

| Area | Open first | Central-map boundary |
| --- | --- | --- |
| Data Capture and source access | `docs/workflows/data_capture_spine_consolidation_map_v0.md` | Capture contracts, source families, access methods, and runner detail stay in the submap and owning indexes. |
| ECR source-side spine | `docs/workflows/ecr_spine_submap_v0.md` | Integrity/content posture owners and implementation detail stay in the submap. |
| Judgment Spine | `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md` | Claim ladder, gates, conductor, cases, and corpus routes stay in the consolidation map. |

Create another submap only when an area is too dense for cold routing through
its current front door. A submap is not justified merely by file count.

## Repository And Documentation Areas

These rows declare stable areas and their role. Leaf discovery is through the
nearest index/submap, retrieval headers, or generated header index.

| Path | Role |
| --- | --- |
| `AGENTS.md` | Canonical root behavior kernel and Forseti triggers. |
| `CLAUDE.md` | Thin Claude compatibility shim importing `AGENTS.md`. |
| `.agents/workflow-overlay/` | Forseti workflow authority: source rules, folders, routing, prompts, validation, review, and safety. |
| `.agents/hooks/` | Portable guards and mechanical checkers; use the Active Hooks routes above and tracked configuration to distinguish live wiring from dormant compatibility modes. |
| `.agents/tools/` | Bounded agent-operated utilities; currently the exact-text fallback editor used only after the native patch route stalls. |
| `.github/` | CI workflows and local operational scripts. |
| `.githooks/` | Tracked local Git hook adapters; bypassable and not server-side protection. |
| `.codex/` | Codex-local tracked hook configuration and adapters. |
| `repo-structure.yaml` | Machine-readable placement router; authority remains in the overlay. |
| `docs/decisions/` | Accepted decision records and doctrine. Use retrieval headers or `header_index.py --index` for file-level discovery. |
| `docs/workflows/` | Workflow records, navigation maps, receipts, and operational guides. |
| `docs/prompts/` | Durable prompts, templates, wrappers, and handoffs governed by prompt orchestration. |
| `docs/research/` | Research and evidence artifacts; not product authority by default. |
| `docs/review-inputs/` | Pinned review inputs and source bundles. |
| `docs/review-outputs/` | Advisory review reports, including typed adversarial, method-validation, and proof areas. |
| `docs/migration/` | Migration manifests and moved-path indexes for historical path resolution. |
| `docs/hygiene/` | Temporary retention, cleanup, checkpoint, and queue artifacts; not canonical product authority. |
| `docs/_inbox/` | Non-authoritative scratch; open only for explicit contamination, recovery, hygiene, or promotion work. |
| `forseti/` | Product-tree root. Product substance lives under `forseti/product/`. |
| `forseti-harness/` | Bounded implementation root; area routes are below. |

## Product Axes And Major Areas

`forseti/product/information/` is admitted here as a T1 product-area front door.
The existing spine routes are insufficient because Company Surface is shared,
decision-agnostic information rather than an operational owner; `shared/` is a
transitional registry/doctrine area, not a durable home for this contract.

| Path | Role / front door |
| --- | --- |
| `forseti/product/spines/foundation/` | Product contract, evidence foundation, ontology, demand-read taxonomy, and vertical exploration. |
| `forseti/product/spines/scanning/` | Discovery-side scanning; open its `README.md` first. |
| `forseti/product/spines/capture/` | Data Capture contracts, source families, packet schema, and source-access ownership; use the Capture submap. |
| `forseti/product/spines/data_lake/` | Cross-layer storage contracts and logical lake mechanics. |
| `forseti/product/spines/packing/` | Model-facing serialization contracts: packing boundary, invariants, envelope versioning, adapter contract, capability declarations. |
| `forseti/product/spines/cleaning/` | Cleaning-layer contracts and transforms. |
| `forseti/product/spines/ecr/` | ECR integrity and retained Signal Content contracts; use the ECR submap. |
| `forseti/product/spines/judgment/` | Judgment claim ladder, conductor, demand read, and toolkit gaps; use the Judgment consolidation map. |
| `forseti/product/spines/creator_signal/` | Creator Signal presentation and promotion-bound surface contracts. |
| `forseti/product/spines/product_lead/` | Product thesis, offer, ICP/wedge, buyer proof, positioning, and GTM front door. |
| `forseti/product/spines/commission_signal_board/` | Commission Signal Board product-side contracts and the Forseti Intelligence Cycle operating contract. |
| `forseti/product/satellites/beauty/` | Beauty satellite artifacts and venue-card surfaces. |
| `forseti/product/satellites/fragrance/` | Fragrance satellite and Judgment Level 1 product-learning artifacts. |
| `forseti/product/case_families/product_learning/` | Product-learning case families across fragrance and other verticals. |
| `forseti/product/information/` | Reusable, decision-agnostic product information; open `forseti/product/information/README.md`, then the current `company_surface/README.md` domain front door. |
| `forseti/product/shared/engagement_registry/` | Shared engagement registry and logic. |

## Forseti Harness Areas

These are implementation-area routes, not a per-module or per-runner inventory.
Inspect the area, its README, or `git ls-files` only when implementation work is
authorized.

| Path | Role |
| --- | --- |
| `forseti-harness/capture_spine/` | Capture-spine implementation packages, plus lane-level modules shared across a family's runners (e.g. Reddit request pacing). |
| `forseti-harness/containers/` | Reusable container definitions for bounded unattended capture; currently the private real-Chrome-under-Xvfb browser host. |
| `forseti-harness/source_capture/` | Packet, adapter, source-family, derived source-classification, transcript, and capture orchestration code, plus capture retention posture (content-vs-raw extraction specs, parity checking, rolling raw sample). A source family may carry one projection PER SURFACE (e.g. Reddit threads project from both old.reddit and www markup), emitting the same record kind and distinguished by `parser_version`. |
| `forseti-harness/youtube_capture/` | Bounded YouTube public-metadata capture helpers. |
| `forseti-harness/data_lake/` | Filesystem lake, catalog, availability, and retrieval helpers. |
| `forseti-harness/cleaning/` | Bounded Cleaning models, transforms, and lake writers. |
| `forseti-harness/ecr/` | ECR source-side integrity derivers and models. |
| `forseti-harness/signal_content/` | Retained compatibility implementation for the deprecated/dormant Signal Content Record. |
| `forseti-harness/evidence_binding/` | JSG-01-scoped evidence binding and composition. |
| `forseti-harness/judgment/` | Judgment-stage prompt construction, response validation, and bounded profile assembly. |
| `forseti-harness/packing/` | Packing Spine model-facing serialization: payload-agnostic columnar packing core plus per-consumer adapters; encoding only, never selection. |
| `forseti-harness/schemas/` | Shared typed models. |
| `forseti-harness/scoring/` | Deterministic scoring and calibration helpers. |
| `forseti-harness/runners/` | CLI entry points; enumerate only on demand with `git ls-files forseti-harness/runners/*.py`. Subdirectories are NOT entry points and are missed by that glob — use `git ls-files forseti-harness/runners/` to see them. Current: `serp_fullbank_analysis/` (research derivations and the wave-2 bank builder backing the SERP lane's findings ledger; operator-drive-pinned, not CI-runnable — see its README). |
| `forseti-harness/cases/` | Tracked deterministic case fixtures. |
| `forseti-harness/config/` | Static harness configuration. |
| `forseti-harness/reports/` | Report rendering code; generated outputs are not map authority. |
| `forseti-harness/source_observability/` | Local operator-record posture and limitation reporting. |
| `forseti-harness/docs/` | Harness operating documentation. |
| `forseti-harness/tests/` | Unit, contract, integration tests, and fixtures. |

Generated or gitignored scratch — do not enumerate or treat as authoritative:
`forseti-harness/_test_runs/` (does not exist yet on a fresh clone),
`forseti-harness/_auth_state/` (does not exist yet until local auth setup), `pytest_*`,
`reports/source_observability/*_dry_run.*`, `cases/*/*/scores/`, and
`memory/logs/`.

## Compatibility And Migration Routes

| Need | Open |
| --- | --- |
| Project-name and legacy-alias policy | `docs/decisions/forseti_rename_migration_policy_v0.md` |
| Remaining compatibility boundary | `docs/decisions/forseti_compatibility_migration_boundary_v0.md` |
| Live repo-map successor and legacy pointer decision | `docs/decisions/forseti_repo_map_successor_migration_decision_v0.md` |
| Legacy repo-map path | `docs/workflows/orca_repo_map_v0.md` (compatibility pointer only) |
| Harness identity migration | `docs/decisions/forseti_harness_identity_migration_plan_v0.md` |
| Current migration status | `docs/workflows/forseti_post_harness_migration_status_v0.md` |
| Historical path lookup | Open the relevant `docs/migration/` moved-path index; do not copy all index rows into T1. |
| Bootstrap record | `docs/workflows/orca_bootstrap_record.md` |
| Migration import queue | `docs/migration/import_queue.md` |

Compatibility paths and moved-path indexes are resolution aids. They do not
promote historical artifacts, prove migration completeness, or authorize a new
rename batch.

## Recommended Source Packs

Use the exact pack rules in `.agents/workflow-overlay/source-loading.md`; this
section only selects the entry point.

| Work | Start |
| --- | --- |
| Data Capture setup, source access, or pressure testing | `docs/workflows/data_capture_spine_consolidation_map_v0.md`, then the matching source-loading pack. |
| Product direction or initial form | `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md`, the Core Spine product contract, and `.agents/workflow-overlay/product-proof.md`. |
| Beauty product application | `forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md`, then the current thesis and nearest evidence-owner maps. |
| Offer, ICP/wedge, buyer proof, or GTM | For the current US Beauty discovery run, open `forseti/product/spines/product_lead/gtm/forseti_beauty_us_problem_discovery_to_wedge_contract_v0.md`; otherwise start with the current thesis, then the matching `forseti/product/spines/product_lead/` area and `.agents/workflow-overlay/product-proof.md`. Do not reactivate historical buyer bindings without a current GTM decision. |
| Judgment run, evidence tier, or gate ownership | `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md`. |
| Prompt or review-prompt work | `.agents/workflow-overlay/prompt-orchestration.md`, `.agents/workflow-overlay/template-registry.md`, then the target. |
| Artifact retrievability or hygiene | `docs/workflows/artifact_retrievability_guide.md` and the owning overlay section. |

## Non-Claims

This map does not prove source authority, acceptance, validation, readiness,
buyer pull, buyer proof, implementation authorization, runtime state, route
freshness, migration completion, or completeness of any artifact family.

Area and file rows are navigation only. Open the target and its controlling
source before making a strict claim. A generated index is a catalog, not route
truth; a passing retrieval checker establishes only its documented mechanical
boundary.
