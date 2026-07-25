# Forseti Preflight Defaults v0

```yaml
retrieval_header_version: 1
artifact_role: Preflight defaults (repo-constant prompt preflight bindings)
scope: >
  Repo-constant field values that any Forseti prompt cites rather than
  restates. Per-prompt deltas (pins, targets, dirty state, validation route)
  are never bound here; the escalated delta list is owned by
  `.agents/workflow-overlay/prompt-orchestration.md` -> Escalated Preflight
  Fields.
use_when:
  - Authoring any Forseti prompt that relies on a repo-constant value below.
  - Checking which preflight values are constant vs. per-prompt.
authority_boundary: retrieval_only
```

Usage line a prompt includes when it relies on any constant below:

```
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
```

Restating a constant owned here in a new or materially touched prompt is a
prompt-quality defect (`.agents/workflow-overlay/prompt-orchestration.md`,
Forseti Prompt Preflight), with one exception owned there: an
operator-couriered cross-vendor delegate prompt restates the delegate-facing
constants (`environment_baseline`, `lifecycle_hard_stop`,
`decorrelation_commission`) inline, faithful to this artifact, so the courier
body is self-contained for its external receiver.

---

## CONSTANTS bound by this artifact (verbatim, single source)

These values do not need restating when a prompt cites this artifact.

| Field | Value |
| --- | --- |
| `agents_md_read` | Required on intake |
| `overlay_readme_read` | `.agents/workflow-overlay/README.md` — required on intake |
| `external_source_boundary` | External workflow source is read-only from Forseti work; `jb` is not Forseti authority |
| `source_hierarchy` | Owned by `.agents/workflow-overlay/source-of-truth.md`; do not restate per prompt |
| `retrieval_header_version` | `1` (for new durable artifacts) |
| `authority_boundary` | `retrieval_only` (for new durable artifacts) |
| `environment_baseline` | Windows host, PowerShell-first: use PowerShell syntax for shell/test commands; use absolute paths resolvable from any cwd; invoke `python`, never `python3`; do not pass Windows drive-letter paths or heredocs through bash |
| `lifecycle_hard_stop` | A delegate or receiver does not commit, push, open or update a PR, merge, stash, reset, clean the worktree, or run repository-hygiene actions unless the commission explicitly grants that action |
| `decorrelation_commission` | `delivery: operator_courier_only` · `access: repo` · `delegate_eligibility: different_vendor_lineage_with_direct_repo_access`; same-vendor, unknown-lineage, no-repo, self, and Codex-managed controller substitutes are invalid; a manager-prefixed target path is neutral; if no eligible controller is available the prompt remains unexecuted |

The REFERENCE-LOAD / SOURCE-LOAD / SOURCE_CONTEXT_READY / APPLY gate language
is owned by `.agents/workflow-overlay/prompt-orchestration.md`'s
Source-Gated Method Contract (pointer, not restatement here).

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Lane-scoped delegated review-and-patch prompts now carry mechanically
    checkable execution-route and report-diff-route fields: eligible bounded
    work uses the proven five-phase fast path, and durable reports embedding a
    target diff use the existing zero-context review-report mechanics runner.
  trigger: workflow_authority
  related_triggers: [review_authority, validation_philosophy, output_authority]
  controlling_sources_updated:
    - .agents/workflow-overlay/prompt-orchestration.md
    - docs/prompts/templates/shared/forseti_preflight_defaults_v0.md
    - .agents/hooks/check_prompt_output_mode.py
    - forseti-harness/tests/unit/test_ci_hook_wiring.py
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/delegated-review-patch.md
    - .agents/workflow-overlay/review-lanes.md
    - .agents/workflow-overlay/validation-gates.md
    - .github/scripts/review-report-mechanics.py
    - .github/scripts/README.md
    - docs/workflows/efficiency/tool_calling_efficiency_improvement_sequence_2026_07_15_v0.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        The kernel already owns and defines both the five-phase eligibility
        route and the first-stall circuit; this change makes delegated prompts
        select those existing rules rather than duplicating them.
    - path: .github/scripts/review-report-mechanics.py
      reason: >
        The runner already generates exact zero-context diffs, performs atomic
        assembly, and verifies provenance; the observed defect was failure to
        route eligible reports through it.
    - path: .agents/workflow-overlay/validation-gates.md
      reason: >
        Required focused, broad, documentation, and provenance gates remain
        unchanged; this changes execution composition, not validation scope.
  stale_language_search: >
    rg -n -i "five_phase_fast_path_if_eligible|review_report_mechanics_if_durable_report_embeds_diff|hand-paste.{0,40}diff|normal-context diff"
    AGENTS.md .agents docs/prompts/templates .github/scripts
    forseti-harness/tests/unit/test_ci_hook_wiring.py
  non_claims:
    - not validation or readiness
    - not a native apply_patch repair
    - not permission to skip or shorten required tests
    - not proof that an external delegate followed the selected route
```

---

## PER-PROMPT DELTAS

Not bound here. The single owner of the escalated per-prompt field list
(source pack, workspace, branch/revision pins, receiver binding, dirty-state
allowance, controlling-source state, doctrine-change decision, targets, edit
permission, output mode, validation gates) is
`.agents/workflow-overlay/prompt-orchestration.md` -> Escalated Preflight
Fields; the `forseti_start_preflight` receipt shape and its `edit_permission`
enum are owned by `.agents/workflow-overlay/source-loading.md`. Routine
prompts state only the non-default preflight core defined in
`.agents/workflow-overlay/prompt-orchestration.md` -> Forseti Prompt
Preflight.
