# Capture Spine Core Migration Adversarial Artifact Review v0

```yaml
retrieval_header_version: 1
artifact_role: Adversarial artifact review output
scope: >
  Read-only adversarial artifact review of PR #316's Capture spine core
  migration at commit a75c337b3497d530f9b7fbfb25acb0fd230d3616. Verdict,
  findings, non-findings, and not-proven boundaries for the move of the current
  Capture spine docs into orca/product/spines/capture/core/.
use_when:
  - Deciding whether PR #316's Capture spine core migration is safe to accept or merge.
  - Checking move completeness, reference repointing, DCP-receipt honesty, and scope containment of the capture/core migration.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/reviews/capture_spine_core_migration_adversarial_artifact_review_prompt_v0.md
  - docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/README.md
  - docs/decisions/orca_spine_first_target_structure_binding_v0.md
reviewed_commit: a75c337b3497d530f9b7fbfb25acb0fd230d3616
merge_base: 35066b1528c7b8a75476ded14461674e76fe8b51
stale_if:
  - PR #316's migration commit changes from a75c337b3497d530f9b7fbfb25acb0fd230d3616.
  - The review-input packet is regenerated.
  - A later Capture spine migration review supersedes this review.
```

## Current Retrieval Notice — 2026-09-05

The original findings below are preserved as historical claims. The packet's
snapshots and patch are now recovered through its retained README. Rechecking
the five recorded input hashes against both the original packet commit
`8df13cbd2ee3b655d94e315dc8cf1e258c3a9c70` and recovery revision
`6d62b05aef99d541110b818157ec0ca10b85c305` found five mismatches. Consequently,
the source-context-pass claim below is not reproduced; the old prompt remains
`BLOCKED_SOURCE_CONTEXT`. Exact recovery of committed files preserves evidence
but does not revalidate this report. Resolve that discrepancy or commission a
new review with freshly bound inputs before relying on its hash certification.

The preserved findings are decision input, not approval, validation, mandatory
remediation, or executor-ready patch authority.

## review_summary

```yaml
review_summary:
  status: completed
  commission: Read-only adversarial artifact review of PR #316 Capture spine core migration
  review_target_commit: a75c337b3497d530f9b7fbfb25acb0fd230d3616
  merge_base: 35066b1528c7b8a75476ded14461674e76fe8b51
  reviewed_by: anthropic/claude-opus-4-8 (Claude Code)
  authored_by: openai-gpt-5-codex
  de_correlation_bar: cross_vendor_discovery
  recommendation: accept_with_friction
  findings_count: 3
  blocking_findings: []
  advisory_findings: [AR-01, AR-02, AR-03]
  summary: >
    The migration is complete and correct: all 103 current Capture spine files
    moved 1:1 under capture/core/ (verified against the real commit, not only the
    normalized packet), destinations are right, live routing surfaces are
    repointed, the DCP receipt is honest and its central stale-path claim
    reproduces, no scope creep / empty future dirs / authority leak / checker
    weakening / whitespace defects were found. Three minor disclosure-and-
    completeness frictions remain, none blocking merge.
```

## Method And Readiness

- Method skills REFERENCE-LOADED then APPLIED in order: `workflow-deep-thinking`
  (boundary framing, failure-mode and anti-anchoring discipline) and
  `workflow-adversarial-artifact-review` (two-phase correctness-then-friction
  flow, source-read-only boundary, finding schema).
- Deep-thinking discipline status: applied. Verification pass actively tried to
  defeat the "clean migration" reading by re-running the receipt's own searches
  against the byte-exact commit and by hunting short-form path residuals the
  receipt regex cannot catch. That pass converted an initial "plan born stale"
  alarm into a correctly-scoped minor (the binding DCP receipt discloses it) and
  surfaced AR-02.
- `SOURCE_CONTEXT_READY`: declared after the source-context gate passed.
- Source-context gate (prompt requirement): all five packet hashes recomputed and
  matched the prompt header exactly (`diff_u80.patch`, `name_status.tsv`,
  `refs.txt`, `head_snapshot_files.txt`, `base_snapshot_files.txt`). Target
  commit and merge-base both present. Not `BLOCKED_SOURCE_CONTEXT`; not
  `BLOCKED_REPO_ACCESS_UNAVAILABLE`.
- Trigger gate: explicit `workflow-adversarial-artifact-review` lane requested by
  the filed prompt. Pass.
- Lane-collision: this is a non-code artifact migration (docs/markdown +
  retrieval metadata + one hook self-test fixture line). Implementation/runtime
  behavior is out of lane and excluded by the prompt. No undeclared collision.
- Output binding: `filesystem-output` with bound `required_output_path` (this
  file). Read-only on all reviewed source; the report is the only write.

## Source-Read Ledger

Evidence was taken from the pinned packet **and** from the byte-exact Git objects
at the merge-base and target commit (`git ls-tree` / `git grep` / `git diff` at
`35066b15` and `a75c337b`), because the packet snapshots are whitespace-
normalized. Where a claim is load-bearing, it was confirmed against the real
commit, not only the snapshot.

| Source | Why read | Decision it supports | State |
| --- | --- | --- | --- |
| packet `manifest/name_status.tsv`, `refs.txt`, README | Enumerate the 226-row change set (A=1, M=122, R=103) and confirm packet integrity | Move map; gate pass | clean; hashes matched |
| `git ls-tree a75c337b / 35066b15 -- .../capture/**` | Byte-exact move completeness | Q1 (103→103, none outside core) | clean (committed) |
| head_files / base_files snapshots | Old vs new full-file context; rename semantic check | Q1–Q3 | normalized (disclosed) |
| `capture_spine_core_source_family_migration_plan_v0.md` (added) | Keystone plan artifact; future-reserved discipline | Q8, Q12, AR-03 | in-tree at HEAD; `stale_if` fired |
| `orca_spine_first_target_structure_binding_v0.md` (amended) | Amendment accuracy + DCP receipt | Q6, Q7, AR-01 | amended in-range |
| `git grep` receipt regex @ a75c337b | Reproduce DCP `stale_language_search` claim | Q5, Q7 | verified |
| `git grep` short-form old paths @ a75c337b | Catch residuals the receipt regex cannot | Q5, AR-02 | residuals found |
| `git diff` of `check_map_links.py` | Checker weakening / fixture correctness | Q10 | clean |
| `git diff` of `safety-rules.md`, `source-loading.md` | Authority-leak check | Q9 | clean |
| `data_capture_spine_consolidation_map_v0.md`, `orca_repo_map_v0.md` @ a75c337b | Routing usefulness post-move | Q4, Q11 | clean |
| `moved_paths_index.md`, `moves_manifest.csv` @ a75c337b | Moved-path index updated | Q4 | clean |
| `git diff --check 35066b15..a75c337b` | Whitespace/CRLF | Q13 | clean |

Dirty/untracked notes: the review-target commit `a75c337b` is **not** the branch
tip; the branch HEAD (`8df13cbd`) adds the review prompt + packet. Per the prompt,
those review-package files are excluded from the change under review and were not
treated as migration content. The codex worktree tree was clean at review time.
The reviewer operated from a separate `.claude` worktree but read and wrote only
the codex workspace named by the prompt.

## Review Boundary And Excluded Scope

- In scope: moved-path correctness, reference repointing on live surfaces, DCP /
  binding honesty, scope containment, hook-fixture and overlay-authority
  integrity, retrieval-metadata and whitespace hygiene — for the pinned commit.
- Excluded (per prompt): runtime/harness behavior, source-access implementation,
  browser/scraping/scanning design, the owner accept/merge decision, patch
  execution, broad `docs/review-outputs/`, broad `docs/prompts/`, `docs/research/`,
  `docs/_inbox/`, external web research, and the later review-package commit.

## Decision Criteria

- **Move completeness/correctness (critical class):** every current Capture file
  re-homed under `capture/core/`, no loss, no duplicate destination, no accidental
  non-Capture move, no hidden semantic change inside renames.
- **Live-routing integrity (critical/major class):** no live map/overlay/product/
  harness/open_next surface routes agents to a retired path; the hook is not
  weakened; overlays grant no new authority.
- **Honesty (major class):** the binding amendment and DCP receipt accurately
  describe what changed, what did not, and what is deferred; no validation/
  readiness/merge overclaim.
- **Containment (major class):** no empty future dirs, no false satellite/Search/
  TikTok/YouTube/source-quality/cadence claims, no scope creep.
- **Friction/disclosure (minor class):** stated conventions match the executed
  tree; residual old-path mentions are either disclosed-historical or cleaned.

---

## Findings (correctness first, then friction)

All three findings are `minor`. No `critical` or `major` finding was found.

### AR-01 — Re-asserted "must carry a README" convention is unmet and undisclosed

- **finding id:** AR-01
- **severity:** minor
- **phase:** correctness
- **commissioned target/purpose:** PR #316 Capture spine core migration; semantic
  preservation of source families (Q2) and convention-vs-tree consistency (Q6).
- **artifact role:** accepted target-structure binding (authority) + executed tree.
- **location / search key:** `docs/decisions/orca_spine_first_target_structure_binding_v0.md`
  Convention 1 ("Each populated `source_families/<family>/` or
  `source_families/social_media/<platform>/` directory **must carry a README that
  cross-points to its phase sibling**"); executed dirs
  `orca/product/spines/capture/core/source_families/retail_pdp/` and
  `.../social_media/instagram/`.
- **source evidence:** `git ls-tree a75c337b` of both family dirs returns only
  content files (6 retail_pdp `*.md`; 15 instagram `ig_*`/`orca_creator_*`); no
  README exists anywhere under `core/source_families/`. The convention text is
  pre-existing and was **extended** by this migration to cover
  `social_media/<platform>/` (diff line `+...social_media/<platform>/ directory
  must carry a README...`).
- **strongest defense, and why it only partly holds:** (a) the convention
  pre-existed and was already unmet, so the migration did not introduce the
  violation; (b) `scanning/source_families/instagram/` — the phase sibling the
  instagram README would cross-point to — does not exist at the target, so the
  cross-pointer is not yet actionable; (c) the plan is explicitly move-only with
  index creation deferred. The defense holds enough to keep this minor, but does
  not fully close it: the migration **re-asserted and broadened** a "must" rule in
  the same commit while leaving it unmet, and neither the plan's deferred queue
  nor the DCP receipt's `intentionally_not_updated` lists the missing source-family
  READMEs (it lists the plan, the inventory, and the empty future placeholder
  folders, but not this).
- **impact:** low routing risk; affects directory-level self-documentation of the
  scanning-vs-capture phase separation and leaves a stated convention readable as
  satisfied when it is not. Distorts future Capture work only mildly and only if
  carried silently.
- **minimum_closure_condition:** either (i) add the cross-pointer READMEs to the
  populated families, or (ii) record the README convention as an explicit deferral
  in the DCP receipt `intentionally_not_updated` / plan deferred queue with the
  "phase sibling not yet created" rationale.
- **next_authorized_action:** report only; this lane cannot edit the binding or
  create READMEs.
- **patch_queue_entry:** not authorized (read-only review); advisory only.
- **red-green proof:** not_applicable (non-executable artifact convention).
- **not proven:** whether Orca intends the README rule to bind at this wave or only
  when both phase siblings are populated — that is an owner/authority call.

### AR-02 — Short-form old-path residuals survive in actively-repointed migration docs

- **finding id:** AR-02
- **severity:** minor
- **phase:** correctness
- **commissioned target/purpose:** reference repointing completeness (Q4, Q5) and
  DCP search thoroughness (Q7).
- **artifact role:** migration/proposal records (historical), touched by this commit.
- **location / search key:**
  `docs/migration/orca_second_pass_consolidation_plan_v0.md:96`
  (`...IG docs at \`capture/source_families/instagram/\``, B6 CLOSED row) and
  `docs/migration/phase2_proposals/capture_toolbox_families_w3a_proposal_v0.md:8,109`
  (`...capture/source_families/ (21 files...)`; finding header "SubNiche used as
  ontology-shaped term in source_families/instagram/").
- **source evidence:** `git diff 35066b15..a75c337b` shows both docs were
  **actively repointed** on many lines (`capture/...` → `capture/core/...`,
  including `source_families/instagram/...` → `core/source_families/social_media/
  instagram/...`), yet these short-form mentions were left old. They are invisible
  to the DCP receipt's verification because its `stale_language_search` regex
  requires the fully-qualified `orca/product/spines/capture/` prefix; a `git grep`
  for short-form `capture/(...subdir...)/` at the target surfaces them.
- **strongest defense, and why it only partly holds:** both lines are point-in-time
  historical content (a CLOSED status row; a prior-finding header), so they are
  arguably "intentionally historical." But unlike the two docs the receipt *does*
  disclose, these were partially rewritten in the same pass — neighboring lines in
  the *same files* were updated to `core/`. That makes the residual an inconsistent
  repoint, not a deliberate historical preservation, and it is undisclosed.
- **impact:** low — a reader of these migration records could be pointed at a
  retired short-form path, but no live map/overlay/product/harness/open_next surface
  is affected (confirmed: the receipt's fully-qualified search returns only the two
  disclosed docs).
- **minimum_closure_condition:** either finish the repoint on lines 96 / 8 / 109,
  or broaden the DCP `stale_language_search` to short-form `capture/<subdir>/` and
  record these as intentionally-historical.
- **next_authorized_action:** report only.
- **patch_queue_entry:** not authorized; advisory only.
- **red-green proof:** the broadened `git grep -nE "capture/(contracts|operating_model|packet_schema|demand_durability_indicators|source_capture_toolbox|source_families)/" | grep -v capture/core/`
  at the target is the natural check — it currently lists these residuals and would
  go quiet (for non-historical docs) after a fix.
- **not proven:** whether the migration author intends these specific lines to be
  frozen historical text; if so, the fix is disclosure, not rewrite.

### AR-03 — Added migration-plan doc presents as plan-only at a HEAD where the move is executed

- **finding id:** AR-03
- **severity:** minor
- **phase:** friction
- **commissioned target/purpose:** DCP/plan honesty and merge-readiness signalling
  (Q6, Q12, Q14).
- **artifact role:** Orca migration plan (docs-only), added in this range.
- **location / search key:**
  `docs/migration/capture_spine_core_source_family_migration_plan_v0.md` header
  (`branch_or_commit: ... @ 35066b15`, `Status: MIGRATION_PLAN_ONLY`,
  `stale_if: Any file under orca/product/spines/capture/ is moved...`) and body
  ("No execution is authorized here"; "proposed future paths ... not current
  accepted placement").
- **source evidence:** the plan is added by commits `9c3d5871`/`3c110745`/`0550790d`;
  the moves execute in the final commit `a75c337b` — all inside the reviewed range.
  At the reviewed HEAD the plan sits in-tree unchanged while the tree shows the
  move done, so its own `stale_if` has already fired and its header still points at
  the pre-move base.
- **strongest defense, and why it largely holds:** the binding amendment's DCP
  receipt explicitly lists this plan under `intentionally_not_updated` with the
  rationale "Retains the pre-execution planning table and old-path evidence; the
  follow-on execution state is recorded by this receipt and the git rename diff,"
  and the fired `stale_if` is Orca's sanctioned staleness signal. So a reader who
  follows the controlling source is not misled. The defense holds enough to keep
  this a friction-class minor rather than a correctness defect; the residual is only
  that the plan **read in isolation** still says "no execution authorized" with no
  forward pointer to the executed state.
- **impact:** low — confined to a cold read of the plan alone; the controlling
  binding and the git history both carry the executed truth.
- **minimum_closure_condition:** optional one-line "EXECUTED 2026-06-21 — see the
  binding amendment DCP receipt and the git rename diff" note (or an `executed_by`
  field) in the plan; otherwise explicitly accept that `stale_if` + DCP disclosure
  is the intended signal.
- **next_authorized_action:** report only.
- **patch_queue_entry:** not authorized; advisory only.
- **red-green proof:** not_applicable (provenance-language finding).
- **not proven:** nothing material; this is disclosed by design and flagged only
  for completeness.

---

## Non-Findings That Matter (verified clean)

- **Move completeness (Q1) — verified against the real commit.** `git ls-tree`
  at `a75c337b` returns **zero** Capture files outside `core/`; base 103 → target
  103 under `core/` (1:1), no pre-existing `core/`, no loose root files. Counts by
  old subdir (contracts 8, demand_durability_indicators 8, operating_model 35,
  packet_schema 3, source_capture_toolbox 28, source_families 21) reconcile exactly.
- **Instagram (Q2) and Retail/PDP (Q3).** Instagram moved
  `source_families/instagram/` → `core/source_families/social_media/instagram/`
  (15 files); Retail/PDP stayed a capture source family at
  `core/source_families/retail_pdp/` (6 files), not a satellite or contract layer.
- **Rename semantic integrity (Q1).** The lowest-similarity rename (R072,
  `capture_recon_index_v0.md`, ~28% changed) is, after filtering path-repoint lines,
  a **pure path repoint** — no hidden semantic change. Low similarity indices reflect
  dense in-file path references, not content drift.
- **Live-surface repointing (Q4, Q5, Q11).** The consolidation map and repo map
  route entirely through `capture/core/` (repo map names `core/` and
  `social_media/instagram` explicitly); `moved_paths_index.md` and
  `moves_manifest.csv` (105 `core/` rows) record the moves; source-loading and
  safety-rules read packs are repointed. The receipt's own
  `stale_language_search` reproduced at the target returns **only** the two
  disclosed historical docs (8 plan + 3 inventory) — no live map/overlay/product/
  harness/open_next surface retains a fully-qualified old path.
- **DCP receipt honesty (Q7).** `controlling_sources_updated` (5),
  `downstream_surfaces_checked` (10), `intentionally_not_updated` (plan, inventory,
  future placeholder folders), and the `stale_language_search_result` are accurate
  for the surfaces they scope; the central "no live surface retained old paths"
  claim was independently reproduced.
- **Binding amendment accuracy (Q6).** The 2026-06-21 amendment correctly states
  103 files re-homed, Retail/PDP and Instagram destinations, and disclaims satellite/
  Search/TikTok/YouTube/source-quality/cadence/harness/source-access. The accepted
  target tree marks future-reserved families "no current Capture files."
- **Containment / no false futures (Q8).** Only one file was added (the plan);
  `git ls-tree` shows **no** empty placeholder dirs or `.gitkeep` for
  tiktok/youtube/web_search_capture/source_quality/cadence. `source_quality_*`
  files correctly stayed under `core/source_capture_toolbox/` (extraction deferred),
  matching the plan's "deliberate second wave."
- **Authority preservation (Q9).** `safety-rules.md` and `source-loading.md` diffs
  are pure path repoints; authority language and `non_claims` (e.g. "not new capture
  authorization") are byte-identical. No new capture/browser/scraping/source-access/
  runtime/validation/readiness authority.
- **Hook integrity (Q10).** `check_map_links.py` changed exactly one `selftest()`
  fixture string (`capture/operating_model` → `capture/core/operating_model`); the
  ancestor-coverage assertion stays `True` and the link-validation logic is
  untouched. Not weakened.
- **Overclaim (Q12).** Plan and binding carry explicit non-claims; commit message
  ("docs: migrate capture spine under core") is modest and accurate. No validation/
  readiness/source-of-truth/merge-readiness overclaim.
- **Hygiene (Q13).** `git diff --check 35066b15..a75c337b` is clean — no whitespace/
  CRLF/path-separator defects in the committed change.

## Not-Proven Boundaries

- **Out-of-scope pre-existing residuals.** Unmodified records still reference old
  capture paths at the target —
  `docs/decisions/orca_search_product_lane_binding_v0.md:55`
  (`capture/demand_durability_indicators/search_interest/`, a moved path),
  `docs/decisions/orca_spine_first_blocker_authorization_v0.md:49,75`,
  `docs/migration/spine_first_target_move_table_v0.md`,
  `docs/migration/spine_first_untagged_file_inventory_v0.md`. These were not touched
  by this migration; the plan explicitly defers non-Capture-surface reference
  updates to a future pass, and the search-lane binding is already a recorded
  spine-first deferral. Whether any of these should ride this PR is an owner-scope
  call, not a defect introduced here. Not proven that leaving them is wrong.
- **Convention-binding timing (AR-01).** Not proven whether the README rule binds at
  this wave.
- **Byte-exact body content** was confirmed via Git objects where load-bearing; the
  packet snapshots are whitespace-normalized and were not used as the basis for any
  whitespace/encoding claim.

## Final Recommendation

```text
accept_with_friction
```

The migration is complete, correct, honestly receipted, and contained; no finding
blocks merge. The three minor frictions (AR-01 README-convention disclosure, AR-02
short-form residuals, AR-03 plan executed-signal) are carryable and can be closed in
a small optional follow-up or explicitly accepted as disclosed. Answer to Q14: the
migration does **not require** a targeted patch to be safe to take PR #316 out of
draft; a minor DCP-completeness patch is advisable but optional.

## Review-Use Boundary

These findings are decision input for the owner, not mandatory remediation. This
read-only lane did not patch the migration, the binding, the plan, the hook, or any
source; it made no owner accept/merge decision and authorized no source-access,
runtime, validation, or readiness. Owner acceptance, any patch, and any
implementation work require separate explicit authorization.
