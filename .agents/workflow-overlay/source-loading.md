# Source Loading

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Source-loading budgets, pre-dispatch receiver readiness, read packs, and context-bloat controls for Forseti prompts and workflow artifacts.
use_when:
  - Preparing Chief Architect prompts, review prompts, product prompts, or handoffs that cite Forseti source.
  - Deciding which files to read before producing a Forseti artifact.
  - Preventing context blow-up before a first artifact or first CA output.
  - Preventing source loading into a repo-changing receiver that cannot write its commissioned worktree.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/source-of-truth.md
  - .agents/workflow-overlay/retrieval-metadata.md
  - docs/workflows/forseti_repo_map_v0.md
  - docs/workflows/artifact_retrievability_guide.md
```

## Rule

Source hierarchy decides authority. Source loading decides what to read.

Do not convert the source hierarchy into a read-all list. Load the smallest
source pack that can answer the current question, then expand only when a
missing source could materially change the output.

Use Forseti-owned source-loading mechanics: claim-level source loading, narrow
reads, source-read ledgers, evidence labels, strict/not-proven boundaries,
targeted excerpts, and context-budget discipline. Forseti overlay and repo map
choose Forseti source files and source precedence.

This file is the canonical Forseti owner for source-loading budgets, source-pack
tiers, source-capsule rules, and Data Capture Spine CA read-pack limits. Repo maps,
prompt artifacts, wrappers, and review requests may point here or summarize the
current rule for convenience, but they must not fork the rule. If another
retrieval or navigation artifact conflicts with this file, load
`.agents/workflow-overlay/source-of-truth.md` and resolve the conflict before
claiming readiness.

## Current Operating Boundary

Forseti is no longer globally docs-first by default. Documentation remains the
authority layer for project facts, decisions, prompts, reviews, migration notes,
and overlay maintenance, but implementation is permitted when a current turn or
accepted handoff explicitly authorizes a bounded implementation scope.

Architecture and product-method work may be future-runtime-aware when the user
asks for it. That means prompts may discuss eventual APIs, scraping, agents,
screenshots, archives, media, or source systems as conceptual requirements.
They must not authorize building, deploying, testing, or operating those
systems unless the current turn or accepted handoff explicitly grants bounded
implementation authority.

## Forseti Start Preflight

Preflight is the act of checking authority, source scope, edit permission, and
material repository state before work. A receipt is required only when that
start state must survive the current interaction:

- a durable or cross-lane prompt, handoff, wrapper, rerun, or patch prompt;
- a source capsule or lane transfer another actor will consume; or
- a portable strict lifecycle/readiness claim intended to survive outside the
  current chat and whose consumer cannot inspect the originating lane state.

Interactive source reads, reviews, bounded edits, source-changing work, and
ordinary closeouts do not owe a receipt merely because they are repo-aware. Run
the material checks, surface a risky assumption or blocker, and proceed. Current
chat and fresh repository evidence carry the state; do not manufacture a form.

Start-route cue: when `target_scope` would change product doctrine,
architecture doctrine, workflow authority, validation philosophy, review
authority, output authority, or a lifecycle boundary, route through the
Doctrine Change Propagation Contract in
`.agents/workflow-overlay/source-of-truth.md`. If more than one doctrine
dimension applies, use the source-of-truth primary `trigger` plus
`related_triggers` grammar. Start preflight never substitutes for the
propagation evidence that contract requires at closeout: PR/closeout evidence
by default, with a durable `direction_change_propagation` receipt or blocker
only in its exceptional case.

When a durable receipt is required, use:

```text
forseti_start_preflight:
  agents_read: yes/no
  overlay_read: yes/no
  source_pack: S0/S1/S2/S3/S4/custom
  edit_permission: read-only/docs-write/patch-only/implementation-authorized
  target_scope:
  dirty_state_checked: yes/no/not_applicable
  blocked_if_missing:
```

`orca_start_preflight` is a legacy compatibility alias for historical,
pre-rename, or provenance artifacts. New or materially touched artifacts that
require a receipt use `forseti_start_preflight`; do not rewrite history.

Use the smallest source pack that can support the task. `agents_read: yes`
means `AGENTS.md` was read or supplied in the current task context.
`overlay_read: yes` means `.agents/workflow-overlay/README.md` was read or
supplied in the current task context. If either field is `no` for a task that
requires Forseti project authority, stop and load the missing source before
continuing.

The receipt records the declared start route only. Evidence and the owning gates
still decide whether later claims are supportable.

### Ordinary Interactive Path

For bounded work that stays in the current interaction:

1. Read the current user instruction.
2. Use `AGENTS.md` and `.agents/workflow-overlay/README.md` only when project
   authority is needed for the answer or edit.
3. Skip the repo map unless choosing among multiple possible source files would
   otherwise require broad search.
4. Run the full Cynefin router only when
   `.agents/workflow-overlay/decision-routing.md` triggers it.
5. Before an independent repo-changing delegate loads task sources, establish
   its one-time writable-root binding under `decision-routing.md`. Same-lane
   work points to the active binding; it does not repeat root or capability
   proof unless the binding changed or became genuinely uncertain.
6. Check repository state, isolation, and validation only to the depth material
   to the task and its claims.
7. Add a durable start receipt only when the work crosses one of the receipt
   boundaries above.

This path changes reporting ceremony, not source hierarchy, validation,
implementation authorization, doctrine propagation, or failure visibility.

## Default Read Order

Use this order unless the user gives a narrower source pack:

1. Current user instruction.
2. `AGENTS.md`.
3. `.agents/workflow-overlay/README.md`.
4. `.agents/workflow-overlay/source-of-truth.md`.
5. This file, when source budgeting or prompt setup matters.
6. `docs/workflows/forseti_repo_map_v0.md`, when choosing among many docs.
7. The one to four target artifacts named by the request, repo map, retrieval
   headers, or nearest accepted product artifact.

Stop when the next file would only add background instead of changing the
decision, prompt, or artifact.

If more than four target artifacts appear necessary, switch to a source capsule
or new-thread handoff instead of bulk-reading.

## Source Pack Tiers

Use source packs instead of whole-folder reads.

| Tier | Use when | Default contents |
| --- | --- | --- |
| `S0 overlay` | Any Forseti project work. | Current instruction, `AGENTS.md`, overlay README, source-of-truth, and source-loading when relevant. |
| `S1 map` | Choosing files or preventing context bloat. | `S0` plus `docs/workflows/forseti_repo_map_v0.md`. |
| `S2 product anchor` | Product architecture, value proposition, offer, or CA setup. | `S1` plus the current product thesis, `.agents/workflow-overlay/product-proof.md`, Core Spine product contract, and the nearest application or boundary note. For beauty, add the beauty decision-adjudication product profile. Add the offer hypothesis and buyer-proof packet only after GTM binds a current buyer and decision family; their historical consumer-demand bindings are not anchors. |
| `S3 target deepening` | A specific artifact family needs details. | `S2` plus only the named target artifact, its `open_next` files, and targeted sections from adjacent artifacts. |
| `S4 historical/review` | Reviewing prior outcomes, adversarial reports, replays, or method-validation history. | Explicitly named review, replay, research, or historical files only. Never default. |

Do not load `S4` material unless the request explicitly depends on prior
reviews, method-validation history, contaminated outputs, or research corpus
details.

## Targeted Read Protocol

Prefer targeted sections over full files whenever a file is long, historical,
or adjacent rather than controlling. A controlling file is not an exemption:
the overlay's own high-traffic files carry the routine read shapes below, and
the bounded read is the compliant act for routine work — full reads of these
files are for their named full-read cases, not a safe default.
This is not a strict-claim shortcut: reopen any unlisted section when it could
materially change the current claim, route, blocker, or edit boundary.

### Routine Read Shapes (overlay high-traffic files)

- `.agents/workflow-overlay/prompt-orchestration.md` — routine prompt
  authoring (per the `AGENTS.md` routine-vs-full authoring split) reads
  "Forseti Prompt Preflight" plus the single section for the prompt family at
  hand. Eligible lane-scoped delegated review-and-patch prompt authoring also
  reads "Lane-Scoped Delegated Patch Prompt Default" plus the targeted
  commissioning sections below. Full read: the **Full orchestration** predicate
  in prompt-orchestration.md applies, or the prompt contract itself is being
  edited.
- `.agents/workflow-overlay/delegated-review-patch.md` — commissioning reads
  "When it applies", "The loop", "Access selection rule", "De-correlation",
  and the "Overlay Interface" block; code-diff commissioning also reads
  "Code-diff target kind — `delegated_code_review_and_patch`"; return
  adjudication reads "Adjudication closeout". Full read:
  editing the convention or resolving a novel dispute about it.
- `.agents/workflow-overlay/review-lanes.md` — routine review work reads
  "Current Lanes" plus the one section the task touches ("Review Doctrine"
  for formal lane bindings, "Template Retrieval Binding" when retrieving a
  template, "Rules" for reviewer conduct). Full read: editing lane doctrine
  or adjudicating a lane-authority conflict.
- `.agents/workflow-overlay/validation-gates.md` — closeout checks read the
  preamble (evidence economy and failure-visibility buckets) plus
  "Current Gates"; prompt authoring reads "Prompt Orchestration Gates";
  product-proof work reads "Product Proof Gates"; enforcement-placement
  decisions read "Enforcement Placement". Full read: editing validation
  doctrine.
- This file — routine Forseti work reads "Rule", "Forseti Start Preflight", and
  the one pack or protocol section the task names; prompt or capsule
  authoring adds "Prompt Source Capsules". Full read: editing source-loading
  doctrine.

### High-Context Guard

Before the route, blocker, edit boundary, source-loading unit, or strict claim is
known, do not widen source loading to prove general familiarity.

Use cheap orientation first:

- scan headings before opening long files;
- read exact section windows instead of full adjacent artifacts;
- cap search output to the smallest hit set that can identify the next source;
- summarize repository state by branch, HEAD, dirty/untracked status, and affected
  target paths when those paths are known;
- avoid broad whole-worktree status dumps unless whole-worktree state is itself
  decision-bearing;
- record plausible background sources as `available not read` or `not loaded
  because not decision-bearing` instead of opening them.

This guard does not weaken source authority. Strict claims still require the
controlling source, and skipped sources must be reopened when they could
materially change the current claim, route, blocker, or edit boundary.

### Named Artifact Missing Fast Path

When the current instruction names an exact repository path, treat that path as
the search boundary until evidence proves otherwise. Do not turn a missing named
file into a broad repository or all-worktree search by default.

Use this ladder:

1. Check the exact path once.
2. If the path is inside a named worktree, search only that worktree for the
   basename and at most two unique target tokens.
3. In that same worktree, read the branch state with targeted Git evidence:
   `git status --short --branch`, recent `git log --stat`, and
   `git diff --name-status <base>...HEAD` when a base is known or inferable.
4. If the missing path is under `docs/review-outputs/` or a review-output child
   folder, and no source prompt/report exists there, classify it as a likely
   intended output path rather than an input source. Then identify the review
   target from the named worktree's branch diff, nearby review inputs, or
   commission artifacts.
5. If no unique target is visible after those checks, stop as
   `BLOCKED_MISSING_SOURCE` or ask for the actual prompt/target. Do not infer a
   different adjacent artifact just because it is visible.

All-worktree searches under `.claude/worktrees`, `.codex/worktrees`, or similar
roots are last resort only: use them when the named worktree itself is missing,
the targeted branch evidence points outside the named worktree, or the owner
explicitly asks for broad recovery. Record such a broad search as an expansion,
not routine orientation.

For each source read, keep a compact ledger entry:

- file or source;
- why it was read;
- exact section or line range when targeted;
- what claim or decision it supports;
- status: clean, dirty, untracked, stale, user-stated, or not checked.

Apply source loading at the claim level:

- advisory claims may use repo-visible evidence with labels and gaps;
- strict claims about acceptance, readiness, validation, proof, authority,
  source-of-truth status, deployment, install, resolver behavior, or
  implementation authorization require controlling source;
- reading more source can improve confidence, but it cannot create missing
  authority.

Treat prior-thread memory, summaries, and context packets as orientation unless
they point to fresh source-visible artifacts. Do not let them carry strict
claims into a new CA prompt.

## Prompt Source Capsules

Chief Architect and model-lane prompts should not paste full Forseti history.

Prefer a source capsule with:

- task objective;
- one-paragraph product anchor;
- boundary rules;
- source pack file list;
- short excerpts only for decisive lines;
- explicit source gaps and owner decisions;
- instructions to read named local files when the lane has filesystem access.

When a lane cannot access the repo, include a curated source capsule instead of
full documents. Keep the capsule focused on the decision the CA must make, not
on preserving every prior artifact.

Capsules should be shorter than the prompt's task instructions. If the capsule
becomes the dominant artifact, stop and create a narrower read pack or new
thread handoff.

### Source Capsule Contract

A source capsule must be a bounded decision aid, not a pasted archive.

Required fields:

```text
source_capsule:
  task_objective:
  source_pack_name:
  files_read:
  targeted_sections_read:
  sources_available_not_read:
  sources_excluded_by_default:
  decisive_excerpts:
  source_gaps:
  dirty_or_untracked_notes:
  non_claims:
```

Default budget targets:

- Use at most four full-file reads.
- Use at most eight targeted section reads.
- Include at most ten decisive excerpts.
- Each excerpt should be the shortest quote or paraphrase that can carry the
  decision.
- Prefer paraphrase plus file path over long quotation.
- Exceed a target only when omitting the additional source would make the
  decision aid incomplete; state the decisive reason and keep the exception
  local. Do not compress a broad archive into the capsule and call it bounded.

These budgets are also the ratified cold-lane retrievability bar (owner-ratified 2026-06-13): a cold lane navigating from the standard entry points should reach its decisive sources within this same budget. Exceeding it on a routine task is a retrievability defect signal, not a license to read more.

`sources_available_not_read` should name files that were relevant but skipped
because they would add background rather than change the current decision.

`sources_excluded_by_default` should name high-risk or high-volume areas such
as `_inbox`, review outputs, method-validation replays, proof-run packets, all
prompts, all research corpus files, or all product files.

`dirty_or_untracked_notes` must say when a source is modified or untracked. Such
sources may support advisory work, but strict claims about acceptance,
source-of-truth status, validation, readiness, or proof remain `not proven`
unless controlling authority accepts them.

When the receiving lane has repo access, the capsule should point to files and
sections instead of carrying long excerpts. When the receiving lane has no repo
access, the capsule may include short excerpts, but should still avoid full
documents.

Every CA or model-lane handoff using a source capsule must state whether the
receiving lane has repo access. Repo-access capsules should use paths, section
names, and short paraphrases. No-repo-access capsules may carry short decisive
excerpts, but must still honor the same budgets and exclusions.

## Data Capture Spine CA Read Pack

This section is the canonical read-pack rule for Data Capture Spine setup CA
prompts. Older prompts may call this the Data Spine CA read pack; treat that as
a deprecated shorthand for Data Capture Spine. Repo maps and prompt artifacts
should reference this section instead of restating the full pack.

Start with:

- `docs/workflows/data_capture_spine_consolidation_map_v0.md` — the
  `retrieval_only` front door. It routes one hop to capture obligations,
  source-access authority, armory components, packet lifecycle, harness
  implementation, and source-quality support without bulk-loading every artifact.

Then open only the targeted sections needed for the CA prompt:

- `docs/decisions/forseti_product_thesis_decision_adjudication_v0.md`: current
  product direction, decision admission contract, Decision Sprint form,
  decision-relevant evidence posture, learning path, and non-claims sections.
- `forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md`:
  beauty admission universe, evidence model, current assets and ownership,
  same-decision proof contract, and transfer test when beauty is in scope.
- `forseti/product/spines/product_lead/offer/forseti_offer_hypothesis_v0.md` and
  `forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md`
  only after GTM explicitly rebinds a buyer and decision family; their generic
  proof grammar remains reusable, but their consumer-demand buyer and offer
  bindings are historical and suspended.
- `forseti/product/spines/foundation/product_contract/core_spine_v0_data_and_cleaning_spine_boundary_v0.md`:
  purpose, decision, layer rules, and future ECR/Evidence Unit boundaries.
- `forseti/product/spines/foundation/product_contract/core_spine_v0_product_contract.md`: product bet,
  core rule, frozen primitives, and explicit non-goals only.
- `forseti/product/spines/foundation/product_contract/core_spine_v0_information_production_foundation_v0.md`:
  Evidence Unit standard and boundary rules only.

Do not read these files in full by default. Use the targeted sections above,
then expand only when a specific source gap would change the CA prompt. Do not
include method-validation replays, proof-run packets, review outputs, or
research corpus files by default.

### Data Capture Spine CA Capsule Limit

A Data Capture Spine CA prompt should include only: one paragraph on Forseti's
value proposition; one paragraph on the current Data Capture / ECR / Cleaning /
Judgment boundary; one paragraph on the bounded-implementation authorization
boundary; the targeted source pack above; the exact files and sections to read;
the default exclusions; and the owner decisions or source gaps the CA should
surface. Do not paste the full offer, proof packet, Core Spine contract,
boundary note, or IPF. Do not include method-validation history unless the CA
task explicitly asks how prior cases affected Data Capture Spine source loading.

## Data Capture Intake Surface / MSP Pressure-Test Target Pack

Use this pack when the task is to prepare, review, route, or verify the bounded
Data Capture pressure-test gate around Raw Capture, Mechanical Source
Projection, categorical ECR receipt, and Cleaning handoff.

Start with:

- `docs/workflows/data_capture_spine_consolidation_map_v0.md` — the
  `retrieval_only` front door for Data Capture Spine / Source Capture Armory.
  It routes one hop to capture obligations, source-access authority, armory
  components, packet lifecycle, harness implementation, source-quality support,
  and current Reddit pre-commercial ordering without bulk-loading every artifact.

Then open the intake surface consolidation as the pressure-test anchor:

- `forseti/product/spines/capture/core/contracts/candidate_intake/data_capture_spine_intake_surface_consolidation_v0.md`

Then open only the controlling source for the current claim. Key owners:

- **Pressure-test closeout state and authorization-chain walk** (slot status,
  RQ status, CloakBrowser selection, Reddit ordering, tranche build authority):
  `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_closeout_synthesis_v0.md`
  — the "Intake Surface / MSP Pressure-Test State" section carries the verbatim
  authorization-chain narrative relocated from this pack on 2026-06-13.
- **Source-observability scoping / RQ boundary**: open the requirements-boundary
  decision and source-access tooling authorization named by the consolidation map.
- **Post-batch patch planning, obligation-contract patch, adversarial review**:
  open the post-batch patch plan, patch proposal, owner decision, and review
  output named by the consolidation map.
- **Slot 3 WSO continuation or cross-venue synthesis**: open
  `forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_slot3_reddit_subbatch_control_note_v0.md`
  before treating Reddit capture as complete venue coverage.
- **Source Capture Packet lifecycle / fixture admission**:
  `docs/decisions/source_capture_packet_fixture_retention_sensitivity_decision_v0.md`
- **Source Quality State Assembler boundary**:
  `forseti/product/spines/capture/core/source_capture_toolbox/source_quality_state_assembler_v0.md`

Capsule note: embedded state narrative (slot-by-slot history, authorization
boundaries, CloakBrowser selection, Reddit ordering) now lives in the closeout
synthesis. Do not use this pack to design ECR schema, Cleaning implementation,
or Judgment behavior.

## Source Capture Method (auto-load for capture-spine activity)

Any capture-spine activity — onboarding a source, running or commissioning a capture probe,
choosing or judging a capture route, or checking a "blocked" / NO-GO call — starts with the
**canonical capture-method playbook**
`forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md` and its `open_next`
`forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md`. It is the canonical method (the
retired `capture_investigation_playbook_v0.md` is its pre-rename name); load it before picking a
route, and do not re-derive the access-control gate (Step 0) or the route catalog from scratch.

Scanning / screening activity reads the screening-side distillation of this method — the **Walker
Equipment Kit** in `forseti/product/spines/foundation/vertical_exploration/forseti_vertical_exploration_guide_v0.md` (public pages,
no logins, URLs + short quotes) — and escalates to the full playbook only for packet-grade capture.

For capture retention and content-to-Cleaning ownership, also open
`forseti/product/spines/foundation/product_contract/core_spine_v0_data_and_cleaning_spine_boundary_v0.md`
and the Cleaning foundation it names. Analytical cross-packet projections use
their own source-family contracts; there is no shared capture Projection
doctrine or capture-Projection read pack.

## ECR Source-Side Spine Read Pack

Use this pack when the task touches the ECR source-side derived-record spine —
the integrity postures (ECR SP-1/2/3/6) or the Signal Content Record
(deprecated/dormant as a default standalone pre-Judgment layer; retained for
compatibility/history or explicit future revival) — including their plans,
models, or deriver code.

Start with:

- `docs/workflows/ecr_spine_submap_v0.md` for orientation. It is the
  `retrieval_only` front door: it states the cross-kind invariants and routes one
  hop to every owner (the SCR deprecation/direction + deriver plan, the ECR frame
  + SP-1/2/3 and SP-6 slices, the receipt-translator origin, the
  schema-evolution doctrine, and the built `forseti-harness/ecr/` + retained
  `forseti-harness/signal_content/` code).

Then open only the controlling owner doc named by the submap for the current
claim. Do not bulk-load every ECR/SCR plan or all derived-record code from this
pack. This is a navigation pointer only; it does not claim ECR/SCR is validated,
ratified, ready for Evidence-Unit binding, or that JSG-01 is unfrozen (the gate
stays FROZEN). This pack must not fork the source-loading rule; the submap
routes, the owner docs decide.

## Intelligence Claim-Support Read Pack

Use this pack whenever evidence is synthesized, compared, weighted, or promoted
into a finding, explanation, memo input, or recommendation anywhere in the
intelligence cycle. Capture-only work does not need this pack until it interprets
what captured material proves.

Start with:

- `forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`
  for provenance, engagement-as-resonance, independent recurrence, cross-venue
  corroboration, counterevidence, scope, and causal ceilings.
- `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`
  for compiling one completed acquisition corpus into the meaning-aware
  proposition view; it defers claim-support semantics to the contract above.

Then open only the source that owns the consuming schema or decision. This pack
does not replace source-family capture rules or the Judgment Spine Evidence
Ladder Read Pack below. The claim-support contract governs what sources support
about the subject; the evidence ladder governs what a completed Forseti run or
proof artifact may claim about its own tier.

## Judgment Spine Evidence Ladder Read Pack

Use this pack when classifying what a Judgment Spine run, case, model answer,
memo, deck, or proof artifact can claim, or when checking whether a lower-tier
signal is being overclaimed.

Start with:

- `docs/research/judgment-spine/judgment_spine_consolidation_map_v0.md` — the
  `retrieval_only` front door. It orients across thesis, cases, manifest,
  conductor, gate ownership, evidence ladder, JSG-08, and harness surfaces, and
  routes one hop to each owner without bulk-loading the corpus. Per-claim-type
  owner pointers (evidence ladder, gate ownership map, reveal/calibration
  contract, conductor) live in that map's Fast Route table.

Then open only the controlling source for the claim being considered:

- **Claim-tier classification or overclaim check**: evidence ladder at
  `forseti/product/spines/judgment/claim_ladder/judgment_spine_evidence_ladder_architecture_v0.md`.
- **Gate ownership (source identity, packet freeze, no-tools, scoring, reveal,
  closeout, or promotion blockers)**: gate ownership map at
  `forseti/product/spines/judgment/conductor/judgment_spine_gate_ownership_map_v0.md`.
- **JSG-08 reveal/calibration receipt**: owner contract at
  `forseti/product/spines/judgment/conductor/judgment_spine_reveal_calibration_owner_contract_v0.md`.
- **Running or planning a case through JSG-01→JSG-10**: conductor at
  `forseti/product/spines/judgment/conductor/judgment_quality_promotion_operating_model_v0.md`.
- **Buyer-proof claims**: `.agents/workflow-overlay/product-proof.md` and
  `forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md`.
- **Judgment-quality, blind-use, fixture-admission, scoring, or calibration
  claims**: `docs/research/judgment-spine/harness/v0_14/contestant_no_tools_execution_contract_v0.md`
  and the specific case/run artifact.
- **Pre-sale manual subscription/chat routing claims**:
  `docs/decisions/judgment_spine_pre_sale_execution_evidence_tier_policy_v0.md`.

Do not bulk-load all Judgment Spine research, all harness specs, all proof-run
packets, all review outputs, or all case artifacts by default. Strict Buyer-Proof
or Judgment-Quality claims remain not proven until the controlling tier gate is
satisfied.

## Expansion Rules

Expand source loading only when one of these is true:

- a named artifact's retrieval header says to open another file;
- a material source conflict appears;
- a strict claim depends on authority, validation, readiness, acceptance, or
  proof status;
- a source gap could change the recommendation;
- the user explicitly asks for a broader source review.

When expanding, prefer targeted section reads over full-file reads.

Do not follow every retrieval-header `open_next` automatically. Open it only
when it can change the current task; otherwise list it as an available source
not read.

If expansion materially exceeds the capsule targets or pulls `S4` history,
narrow the question or use a handoff only when the current lane can no longer
hold the decisive evidence without losing source identity or claim integrity.

## Artifact Body Shape

When creating or materially touching a durable human-authored workflow
artifact, use `.agents/workflow-overlay/retrieval-metadata.md` for the header
contract and `docs/workflows/artifact_retrievability_guide.md` for operational
body-shape guidance.

For long or decision-bearing artifacts, put a compact source-loading surface
near the top: purpose, use when, do not use for, authority boundary, next source
when material, stale conditions, recheck recipe when provenance matters, and
strict claims that remain not proven.

The guide is subordinate to this overlay. It may help shape artifact bodies,
fresh-agent checks, and report-only retrieval findings, but it does not change
source hierarchy, accepted folders, validation gates, artifact roles,
implementation authorization, or the rule that `open_next` is conditional.

## Context Boundary

Continue in the current lane while the decisive sources, authority, and target
state remain reconstructable. Start a new thread or create a compact handoff
only when the current context can no longer hold those facts safely, a no-repo
receiver needs a portable capsule, or an independent concurrent actor is
actually required. Artifact counts, phase labels, or approaching compaction do
not by themselves force a new lane.

When a handoff is needed, name the source pack, target output, non-goals, and
files excluded from default loading.

## Files Not To Bulk-Load By Default

Do not bulk-load these by default:

- `docs/_inbox/`, especially contaminated method-validation outputs;
- all method-validation replays;
- all proof-run packets;
- all review outputs;
- all prompts;
- all research corpus files;
- all product files.

Use the repo map to select a narrow source pack instead.

## Not-Proven Boundaries

Source loading supplies context, not status or authority. A status claim, as
defined in `.agents/workflow-overlay/validation-gates.md`, requires its
controlling source and evidence; otherwise mark it `not proven`.
