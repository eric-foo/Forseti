# Capture Spine Core Migration Adversarial Artifact Review Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Review prompt
scope: >
  Historical filed prompt for PR #316's Capture spine core migration review;
  recover its packet before inspection and retain its source-context blocker.
use_when:
  - Inspecting or recovering the historical Capture spine core migration review commission.
  - Checking whether the migration correctly re-homed current Capture spine docs under `capture/core/`.
  - Checking moved-path correctness, reference rewrites, DCP honesty, and scope containment.
authority_boundary: retrieval_only
open_next:
  - docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/README.md
  - docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md
input_hashes:
  docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/diff_u80.patch: 4F2DDD6E5D2AD3C9124BD9E380AD6BBDDB566C2ECAFD1D6173A4B70FB31E3EFB
  docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/name_status.tsv: 087D8B18BD2AF27378188E95A2B1F8429C6E94EDE1761583A00FCE88107DF939
  docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/refs.txt: 711105F253DAF841D71112086F060048D1BF6FDCB456137241732DD04F7A090B
  docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/head_snapshot_files.txt: 7829ED278143AE0FA85B685C0B72C5F3966C3732D610792926B193A120FBF47E
  docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/base_snapshot_files.txt: A43A6D684FDB0526C2485D8EF8D0834D72FFEE7E473C43B01A6F756128AC0E8A
stale_if:
  - PR #316's migration commit changes from `a75c337b3497d530f9b7fbfb25acb0fd230d3616`.
  - The review-input packet is regenerated.
  - A later Capture spine migration review prompt supersedes this prompt.
```

## Historical Status — 2026-09-05

The snapshots and patch are retired from the current checkout. Recover them
through the packet README before historical inspection. All five `input_hashes`
above fail against both the recovery revision
`6d62b05aef99d541110b818157ec0ca10b85c305` and original packet commit
`8df13cbd2ee3b655d94e315dc8cf1e258c3a9c70`; these original claims are preserved,
not replaced with new pins. This prompt remains `BLOCKED_SOURCE_CONTEXT` under
its own mismatch rule. Exact restoration of committed bytes does not clear that
gate. Do not rerun the old instructions or overwrite the historical report as a
fresh commission; resolve the discrepancy or bind a separate current review.

## Prompt Authoring Preflight

```yaml
orca_start_preflight:
  agents_read: yes - AGENTS.md supplied in current task context
  overlay_read: yes - .agents/workflow-overlay/README.md read in current task context
  source_pack: custom Capture spine migration review packet
  edit_permission: docs-write for this prompt and review-input packet; downstream reviewer is read-only
  target_scope: filed adversarial artifact review prompt plus greppable review-input packet for PR #316 migration commit
  dirty_state_checked: yes - lane worktree was clean before review-package generation; the review packet and prompt are the intentional new files in this unit
  blocked_if_missing: none
```

preflight_defaults: `docs/prompts/templates/shared/orca_preflight_defaults_v0.md` v0 - constants bound; deltas stated here.

Template source: `docs/prompts/templates/review/adversarial_artifact_review_v0.md` with Orca prompt-orchestration and review-lane overlays applied.

## Historical Prompt — Source Context Blocked

You are performing a **read-only adversarial artifact review** for Orca.

Review target:

```text
PR #316 Capture spine core migration at commit:
a75c337b3497d530f9b7fbfb25acb0fd230d3616
```

Review-input packet:

```text
docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/
```

Required durable report path:

```text
docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md
```

Review purpose:

```text
Determine whether PR #316 correctly migrates the current Capture spine docs into
`orca/product/spines/capture/core/`, repoints live references, records the
architecture/DCP consequences honestly, and avoids smuggling in scope that was
explicitly deferred.
```

This is not delegated-review-patch with patch authority. It is a read-only adversarial artifact review over a multi-file migration packet. Do not patch source files. Write only the required review report.

## Workspace And Revision

Workspace:

```text
C:\Users\vmon7\Desktop\projects\orca\.codex\worktrees\capture-spine-core-migration-plan
```

Expected branch and target revision:

```text
branch: codex/capture-spine-core-migration-plan
review target commit: a75c337b3497d530f9b7fbfb25acb0fd230d3616
target merge-base: 35066b1528c7b8a75476ded14461674e76fe8b51
```

The branch may contain a later commit that adds this prompt and review packet. Do not treat review-package files as part of the migration under review. The migration target is the pinned commit above and the review-input packet generated from it.

Dirty-state allowance:

- The reviewer may use the review-input packet even if the branch contains later review-package additions.
- If the review-input packet hashes do not match the prompt header, return `BLOCKED_SOURCE_CONTEXT`.
- If the target commit is unavailable and the packet is missing or incomplete, return `BLOCKED_REPO_ACCESS_UNAVAILABLE`.

Output mode:

```text
review-report
```

Edit permission:

```text
read-only review; write only the required review report path
```

## Required Method Sequence

REFERENCE-LOAD these method instructions first. Do not APPLY them yet:

- `workflow-deep-thinking`
- `workflow-adversarial-artifact-review`

Before `SOURCE_CONTEXT_READY`, prepare only neutral source-reading lenses. Do not produce findings, verdicts, rankings, recommendations, or architecture conclusions before source readiness.

Then SOURCE-LOAD the required Orca sources and review packet below.

After declaring `SOURCE_CONTEXT_READY`, APPLY `workflow-deep-thinking` to frame the boundary problem, likely failure modes, and decision criteria.

Then APPLY `workflow-adversarial-artifact-review` to produce the findings-first review report.

If `workflow-adversarial-artifact-review` is unavailable, unresolved, or cannot be applied after `SOURCE_CONTEXT_READY`, return a blocked or advisory-only result. Do not emit formal verdicts, severity authority, readiness claims, validation claims, mandatory remediation, patch queues, executor-ready handoffs, or alignment-complete claims.

## Required Sources

Authority and review-lane sources:

- `AGENTS.md`
- `.agents/workflow-overlay/README.md`
- `.agents/workflow-overlay/source-of-truth.md`
- `.agents/workflow-overlay/source-loading.md`
- `.agents/workflow-overlay/artifact-roles.md`
- `.agents/workflow-overlay/review-lanes.md`
- `.agents/workflow-overlay/prompt-orchestration.md`
- `.agents/workflow-overlay/communication-style.md`
- `.agents/workflow-overlay/validation-gates.md`
- `.agents/workflow-overlay/retrieval-metadata.md`
- `.agents/workflow-overlay/template-registry.md`

Review packet:

- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/README.md`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/diff_u80.patch`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/name_status.tsv`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/diff_stat.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/numstat.tsv`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/summary.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/head_files.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/head_snapshot_files.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/base_files.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/manifest/base_snapshot_files.txt`
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/head_files/` - target-side `.snapshot.txt` evidence files
- `docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/base_files/` - merge-base `.snapshot.txt` evidence files

Live repo sources for spot checks:

- `docs/decisions/orca_spine_first_target_structure_binding_v0.md`
- `docs/workflows/orca_repo_map_v0.md`
- `docs/workflows/data_capture_spine_consolidation_map_v0.md`
- `.agents/workflow-overlay/source-loading.md`
- `.agents/workflow-overlay/safety-rules.md`
- `.agents/hooks/check_map_links.py`

Excluded by default:

- broad `docs/review-outputs/`
- broad `docs/prompts/` outside this prompt and named templates
- broad `docs/research/`
- `docs/_inbox/`
- implementation/runtime behavior not touched by the migration
- external web research

Expand only if a missing source could materially change a finding. If expansion would exceed a bounded review source pack, report `SOURCE_CONTEXT_INCOMPLETE` with the exact missing source and why it matters.

## Grep-First Review Instructions

Use the packet as the primary greppable surface. Suggested probes, not an exhaustive checklist:

```powershell
rg -n "social_video|capture/source_families/instagram|capture/contracts|capture/operating_model" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0
rg -n "source_quality|cadence|missingness|satellite|web_search_capture|youtube|tiktok" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0
rg -n "orca/product/spines/capture/" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/head_files
rg -n "open_next:|source_capture_toolbox|source_families/social_media/instagram|source_families/retail_pdp" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/head_files
```

Use `diff_u80.patch` to inspect the change with surrounding context. Use `base_files/` and `head_files/` when you need to compare old and new full-file context or verify a rename did not hide a semantic change. The packet is whitespace-normalized for repository hygiene; use the pinned Git refs when byte-exact source matters.

## Review Questions

Attack the migration against these questions:

1. Did every current Capture spine file move to the intended `capture/core/` destination, with no missing files, duplicate destinations, or accidental non-Capture moves?
2. Did Instagram move from the old social-video shape into `core/source_families/social_media/instagram/` without losing source-family semantics?
3. Did Retail/PDP remain a source family at `core/source_families/retail_pdp/` without being turned into a satellite or unrelated contract layer?
4. Were live references repointed to `capture/core/` correctly across maps, prompts, decisions, overlay files, harness docs, moved-path indexes, and retrieval headers?
5. Are remaining old-path hits limited to intentionally historical migration records, or do any live surfaces still route agents to retired paths?
6. Is the `docs/decisions/orca_spine_first_target_structure_binding_v0.md` amendment accurate about what changed and what did not?
7. Is the DCP receipt honest about controlling sources updated, intentionally-not-updated surfaces, and stale-language search results?
8. Did the migration avoid creating empty future directories or false claims for satellites, Search/web-search capture, TikTok, YouTube, source-quality extraction, cadence/missingness, runtime/browser behavior, harness behavior, or source-access authorization?
9. Did the source-loading and safety-rules edits preserve authority boundaries rather than granting new capture, browser, scraping, source-access, runtime, validation, readiness, or implementation authority?
10. Did hook fixture updates, especially `.agents/hooks/check_map_links.py`, match the new path reality without weakening the checker?
11. Do repo maps and consolidation maps remain useful entrypoints after the move, or did the migration make retrieval worse despite passing link checks?
12. Does any changed artifact overclaim validation, source-of-truth promotion, architecture readiness, migration completeness, or PR merge readiness?
13. Are line-ending, CRLF, encoding, path separator, or generated snapshot artifacts likely to mislead future validation or review?
14. Does this migration need a targeted patch before PR #316 moves out of draft?

## Required Finding Severity

Use these priority labels only:

- `critical`: continued use of the migration would likely route agents to wrong live authority, lose Capture files, create false implementation/source-access/runtime authority, or make PR #316 unsafe to merge without architectural correction.
- `major`: continued use would materially distort future Capture work because of stale live paths, misleading DCP language, missed map/retrieval surfaces, unbounded scope creep, or weakened link/checker behavior.
- `minor`: wording, provenance, reviewability, or operator-friction issue that should be patched but does not materially distort future Capture work if explicitly carried.

These labels are finding priority only. They do not create approval, rejection, readiness, validation, mandatory remediation, or patch authority.

## Recommendation Vocabulary

Use exactly one:

- `accept`
- `accept_with_friction`
- `patch_before_acceptance`
- `reject`
- `blocked`

Do not use generic `pass`, `fail`, `approved`, `ready`, or `validated`.

## Output Report Requirements

Write the full durable report to:

```text
docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md
```

The report must include:

- retrieval header;
- `review_summary` YAML at the top;
- `reviewed_by` and `authored_by` provenance fields, using `unrecorded` if the operator/tooling did not supply a real value;
- `de_correlation_bar`: `cross_vendor_discovery`, `same_vendor_sanity`, `self_fallback`, or `unrecorded`;
- source readiness declaration;
- source-read ledger with dirty/untracked notes;
- review boundary and excluded scope;
- decision criteria;
- findings first, ordered by severity;
- non-findings that matter;
- not-proven boundaries;
- final recommendation from the allowed vocabulary;
- review-use boundary.

For each finding include:

- finding id;
- severity;
- phase: `correctness` or `friction`;
- target location or stable search key;
- issue;
- source evidence;
- impact;
- minimum_closure_condition;
- next_authorized_action;
- advisory remediation direction, not a patch queue.

Do not emit `patch_queue_entry`. This is read-only review.

## Chat Closeout

After successfully writing the durable report, return only a compact human sentence plus this courier YAML:

```yaml
review_summary:
  status: completed
  report_path: docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md
  recommendation: <accept | accept_with_friction | patch_before_acceptance | reject | blocked>
  reviewed_by: <actual reviewer model+version, or unrecorded>
  authored_by: openai-gpt-5-codex
  summary: "<one sentence>"
  findings_count: <number>
  blocking_findings: []
  advisory_findings: []
  prior_findings_remediated: []
  next_action: "<one concrete next step>"
```

If report writing fails after `review-report` is selected, do not use `report_path`. Return:

```yaml
review_summary:
  status: failed
  review_location: chat_only_current_thread
  recommendation: blocked
  reviewed_by: <actual reviewer model+version, or unrecorded>
  authored_by: openai-gpt-5-codex
  summary: "Failed to write required report to docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md."
  findings_count: 0
  blocking_findings: []
  advisory_findings: []
  prior_findings_remediated: []
  next_action: "Resolve report write failure, then rerun the review-report prompt."
```

## Hard Boundaries

Do not:

- patch the migration;
- patch source artifacts;
- patch prompt, overlay, repo-map, hook, migration, or product files;
- make the owner decision;
- merge, close, approve, or mark PR #316 ready;
- authorize source-access implementation;
- design browser behavior, scraping, source systems, runtime, schemas, tools, dashboards, APIs, packages, deployment, commits, pushes, or CI changes;
- claim validation, hardening, readiness, buyer proof, product readiness, source-of-truth promotion, implementation authority, or commercial readiness.

Review findings are decision input only. Owner acceptance, patch authorization, source-access implementation, and any runtime work require separate explicit authorization.
