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
