# Agent enforcement hooks — and how to wire them in any harness

This directory contains Forseti's interactive protection and portable mechanical
checkers. Active interactive wiring is deliberately small: Claude and Codex run
only the protected-action guard before tools; Claude also runs one lean
SessionStart state read. Durable artifact-shape checks run at commit/CI. Script
presence and dormant `--hook` compatibility modes do not prove activation;
tracked configuration is authoritative.

## The hooks

| Script | When | Effect |
|---|---|---|
| `guard_protected_actions.py` | **pre-tool** (before a shell/write tool runs) | **HARD-blocks** (exit 2) direct push-to-main, force-push, `reset --hard`, `git clean`, protected external-root writes, explicit rebase starts on a mechanically confirmed published lane, and `gh pr merge --admin`. A direct `gh pr merge <N>` is allowed only for the current lane branch when the PR targets `main`, is same-repo, `CLEAN`, all checks are green, carries `agent-automerge`, and has no `risk/blocked-for-merge-policy` hold. `risk/manual-review-required` keeps the unattended bot out but does not choose a human actor after the resident completion/review and home/Chief Architect adjudication gate closes; that judgment completion is not mechanically certified by the label. Benign lane pushes, published-lane fetch-plus-merge updates, and rebase recovery remain allowed. Fires in **all** permission modes. Non-merge probes fail open on internal error; merge authorization fails closed. |
| `.codex/hooks/forseti_guard_codex_adapter.py` | Codex **PreToolUse** adapter | Runs `guard_protected_actions.py`, converts guard denials into Codex's native JSON `permissionDecision: deny` response, maps every Codex `apply_patch` target through the existing EP-01 protected-path check, blocks raw shell durable-write primitives for repo source/docs files, and exposes the fail-closed live adoption probe below. |
| `pre_push_guard.py` | local Git **pre-push** adapter policy | Blocks pushes targeting `main`, branch deletes, non-fast-forward updates, and unverifiable update safety when `.githooks/pre-push` is installed through `core.hooksPath`; for allowed lane pushes it mirrors ten selected strict CI gates over local `origin/main...HEAD`, including the conditional harness coupling contracts. CI runs the same gate modes against its exact event base SHA. A gate failure or launch error blocks the push. Bypassable with `--no-verify`; misses GitHub API merges; CI stays authoritative. |
| `check_harness_coupling.py` | manual + **CI** (`--strict`) + local pre-push | Diff-scoped adapter over existing inventory and policy-pin contract tests. It runs only when the outgoing change touches `forseti-harness/**/*.py` or `forseti-harness/data_lake/lake_touchpoint_inventory_v0.json`; an unresolvable diff or unlaunchable test fails closed. Coupling preflight only: not the full harness suite, validation, readiness, or proof that every CI failure is prevented. `--selftest` present. |
| `check_source_input_hashes.py` | manual + **CI** (`--strict`) + local pre-push | Diff-scoped, forward-only: list-style JSON `source_inputs[]` records with repo-local `source_pointer` + `sha256` must match current file bytes (CRLF-normalized), and source-capture packet manifests (top-level `manifest_version`) must have top-level `preserved_files[]` records whose `relative_packet_path` + `sha256` match current raw stored bytes resolved against the manifest's own directory, when the artifact or referenced file changed. Provenance freshness only; never semantic validation, generated-artifact completeness, readiness, or source quality. Backlog via `--audit`; `--selftest` present. |
| `check_retrieval_header.py` | manual + dormant `--hook` compatibility | Advisory (exit 0): warns if an in-scope artifact is missing its retrieval header. Forward-only; never blocks. The active changed-doc gate is `header_index.py --strict` in CI. |
| `check_dcp_receipt.py` | **CI** (`--strict`) + manual maintenance | Diff-scoped strict gate validates the shape of exceptional durable DCP receipts/blockers present in changed Markdown files. It never requires a receipt or verifies its truth. |
| `check_review_output_provenance.py` | manual + **CI** (`--diff "$FORSETI_DIFF_BASE" --strict`) | Advisory by default; `--strict` fails on changed review outputs missing retrieval-header shape, `reviewed_by`, `authored_by`, review-use boundary/non-approval wording, balanced/valid fences, proper `diff` fencing, non-collapsed diffs, observed-check wording, or whitespace hygiene. Shape/integrity only; never reviewer identity verification, de-correlation truth, approval, validation, or review quality. |
| `check_csb_scanning_artifact.py` | manual + **CI** (`--diff "$FORSETI_DIFF_BASE" --strict`) | Diff-scoped, forward-only for Capture batch handoffs and CSB-first scan artifacts under `docs/research/`: targets any YAML Capture marker in that artifact lane, rejects ambiguous/nested Capture identity and collection-completion or terminal-consolidation claims in any state/status field across the receipt, then validates minimum scan receipt shape including capture-request accounting and the Creator Registry preflight block (`not_applicable` for non-social requests; receipt-backed `can_start_new_capture` for new social creator/account capture). Shape only; never proves saturation, scan quality, buyer proof, registry truth, or Capture route authorization. |
| `check_review_routing.py` | **commit-msg** (advisory) + **CI** (`--strict`) | Diff-scoped, forward-only: a change touching code roots (`forseti-harness/`, `.agents/hooks/`) must add a review artifact under `docs/prompts/reviews/`/`docs/review-outputs/` or carry a shape-valid `review_routing_status:` commit-message line (`routed <existing path>` / `blocked -- reason` / `not_needed -- reason`). Disposition presence/shape only; never review quality, reason truth, or whether review should have been recommended. |
| `check_handoff_pointers.py` | **CI** (`--strict`) | Diff-scoped, forward-only: handoff-packet paths (`docs/workflows/*handoff*.md`, `docs/prompts/handoffs/*.md`) referenced in changed durable `.md` files must resolve in the same tree, or the pointer line must carry an explicit pin (`branch` / `PR #N` / `origin/<ref>`) or exemption marker. Pointer shape only; never packet content freshness, pin truth, or source-choice correctness. Backlog via `--audit` (never gated). |
| `check_prompt_output_mode.py` | **CI** (`--strict`) | Diff-scoped, forward-only: changed prompt artifacts under `docs/prompts/**` (templates and READMEs excluded) must carry an output-mode declaration naming at least one closed-set token (`chat-only` / `file-write` / `review-report` / `paste-ready-chat` / `patch-queue`). Additionally validates the EP-38 managed-receiver creation-authorization shell when its trigger appears (implementation-authorized `codex_managed_worktree` commissions). The EP-19 delegated-patch courier-shell check was retired 2026-07-25 with the lane binding — EP-19 eligibility is resident enforcement (`delegated-review-patch.md` who-constraint plus CA adjudication). Presence + token/shell shape only; "exactly one, correctly scoped" and all runtime truth stay resident judgment. Backlog via `--audit` (never gated); `--validate-stdin` gates one rendered prompt. |
| `check_review_summary.py` | **CI** (`--strict`) | Diff-scoped, forward-only over changed `docs/review-outputs/**` files: real `review_summary` blocks must not carry forbidden process keys, `report_path` must resolve on disk, failed-write blocks keep the bound failed shape, and `recommendation` is non-blank when present. Full `recommendation` enum membership is `--audit` advisory only (known extended vocabulary in delegated-review-patch lanes). Shape only; never review quality or truth. Non-overlap: header/provenance/fencing stays with `check_review_output_provenance.py`. |
| `check_hash_pin_freshness.py` | manual + **CI** (`--strict`) + local pre-push | Diff-scoped, forward-only: markdown freshness hash pins (labeled `path:` + `sha256:` bullet pairs; `source_captures/**/receipt.md` preserved-file bullets) must match current CRLF-normalized file bytes when the pin-carrying doc or its target changed. The markdown analog of `check_source_input_hashes.py` (JSON); provenance-style manifest tables and source-read ledgers are deliberately not parsed as pins. Pin freshness only; never semantic validity, source quality, or skill correctness. Backlog via `--audit` (never gated). |
| `check_shared_helper_duplication.py` | manual + **CI** (`--strict`); dormant `--hook` compatibility | Diff-scoped, forward-only: an added line privately re-defining a shared helper (`_utc_now` / `_now_utc` / `_utc_now_z` / `_utc_now_iso` / `_sha256*` / `_as_dict` / `_hash_file` / `_string_or_none` / `_non_empty_string_or_none` / `_int_or_none` / `_bool_or_none` anywhere in scope; `_is_forbidden_field_name` / `_first_match` / `_dedupe_preserve_order` / `_read_packet_directory` in `forseti-harness/` only; `repo_root` / `_git` / `_git_lines` / `porcelain_paths` in `.agents/hooks/` only) is flagged toward the owning home (`forseti-harness/harness_utils.py` / `forseti-harness/source_capture/projection_shared.py` / `.agents/hooks/_hooklib.py`) unless the def line, the line immediately above, or the first body line below carries a comment naming the delta (any comment containing `harness_utils`, `_hooklib`, `projection_shared`, or `helper-delta`). Scope excludes `forseti-harness/tests/**`, `harness_utils.py`, `_hooklib.py`, and `guard_protected_actions.py` (its duplication is the documented deliberate exception). Adoption-rule shape only; never helper correctness, divergence justification, validation, or readiness. `--selftest` present. |
| `check_repo_map_freshness.py` | manual; dormant `--hook` compatibility | Reports structural drift vs the repo map and retains strict/manual modes. It is not registered on an interactive boundary. |
| `check_search_surface_google_route.py` | manual + **CI**; dormant `--hook` compatibility | Strict CI enforcement for the checkable Google search-surface route shell: Google Search URLs use `hl=en&gl=us&pws=0`, US-parameterized artifacts carry the physical-locality non-claim, and Google sorry/IP pages are not preserved in durable docs. |
| `header_index.py` | manual + **CI** (`--strict`) | Generates the on-demand retrieval index, advisory health/backlog views, and the diff-scoped forward-only header/orphan gate. Inventory and shape only; never readiness or source authority. |
| `check_map_links.py` | manual + **CI** (`--strict`) | Checks map/submap paths, `open_next` targets, folder reachability, inline path shape, and direct target existence for the Artifact Roles and product-spine Doctrine Index live-router tables. Path existence only; never route truth, currentness, authority, or completeness proof. |
| `check_deletion_evidence.py` | **CI** (`--strict`) | Diff-scoped: deleting (or renaming out of every governed root) a governed artifact under the product tree requires a complete evidence record (`reverse_ref_check`, `successor`, `semantic_delta`, `rollback`) in the deletion-evidence register. Record shape/coverage only; never whether the deletion was wise. |
| `check_fragrance_reference.py` | **CI** (`--strict`) | Validates `fragrance_reference_v0.yaml` against the invariants its own header declares: bare-fact provenance, vocabulary conformance, accord-to-note-family derivation consistency, dupe-reference resolution. Data-file integrity only. |
| `check_ontology_ssot.py` | **CI** (`--strict`) | Validates `ontology.yaml` as a faithful, self-consistent promotion of the ontology backbone doc (type roster, namespaces, typed-link endpoints, deferred-list parity with the expansion backlog, runtime-binding references, type_cap). Consistency shape only. |
| `check_ontology_tag_validity.py` | **CI** (`--selftest` + `--strict`) | Flags changed-markdown `Word (Capitalized)` parentheticals whose capitalized token looks type-like but is not in the ontology roster (allowlist-aware). Tag-mode shape only; never prose meaning. |
| `check_ontology_drift.py` | **CI** (`--strict`) | Verifies scoped alignment between the ontology SSOT `runtime_bindings` and the runtime Pydantic classes for exactly the three bound overlaps (CapturePacket, EvidenceUnit, Case). Never full field conformity. |
| `check_silver_lane_registry.py` | manual + **CI** (`--strict`) | Enforces the Data Lake silver-lane write contract (the no-blur binding): full-tree AST scan of `forseti-harness/` raw lake-write call sites plus the lane registry's own `validate_registry()` invariant. |
| `check_placement.py` | **CI** (`--changed --strict`) + manual compatibility | Checks only A/M/C paths and R destinations against the CI event base, ignores deletions, and runs lightweight map↔top-level freshness. Internal Git timeout 20 seconds; unavailable strict diff fails visibly. Placement shape only; never authority, validation, or readiness. |
| `check_full_gt_claims.py` | **CI** (`--changed --strict`); dormant `--hook` compatibility | Flags added `.md` lines whose full-GT claim language is not bounded by ballast wording and does not sit in a claim-owning surface. Shape/placement only; never claim truth. |
| `session_context_capsule.py` | Claude **SessionStart** | One `git --no-optional-locks status --porcelain=v2 --branch` child (2-second internal timeout; 5-second host cap). Emits only repo, branch, and modified/untracked counts; Git failure emits `UNKNOWN`, never false-clean state. |

Each active guard/checker documents its boundary and validation mode; tracked
configuration and CI are the activation authorities.
## Run the CI hook-gate set locally (before pushing)

CI runs every strict hook command registered in `.github/workflows/ci.yml`.
The local pre-push guard mirrors ten selected strict gates, so CI still has
additional hook commands that can fail after a push. Run the complete CI hook
set locally with:

```powershell
pwsh .github/scripts/run-doc-gates.ps1          # run each registered CI hook command
pwsh .github/scripts/run-doc-gates.ps1 -List    # list the commands derived from ci.yml
```

The runner parses both one-line steps and commands inside multiline `run: |`
blocks directly from `.github/workflows/ci.yml`, so the workflow remains the
command source. It intentionally excludes non-hook steps such as
`python -m pytest` and `.github/scripts/*`; run relevant tests separately when
you touch code. This is convenience tooling, not validation or readiness; CI
remains the authoritative gate.

**Shared helpers:** `_hooklib.py` (same directory) owns the helpers the wired
checkers share -- repo-root/path normalization, tool-event parsing (incl. Codex
`apply_patch` headers), the git wrapper, porcelain parsing, shell-segment
splitting, the durable-docs scope base, and the once-per-session marker. The
scripts pin their own directory onto `sys.path` before importing it, so they
still run from any cwd; a harness port must copy the whole `.agents/hooks/`
directory, not individual scripts. **Deliberate exception:**
`guard_protected_actions.py` stays import-free -- an ImportError in an advisory
checker costs one advisory, but in the hard guard it would disable the gate
(including its fail-closed merge path). Do not refactor the guard onto
`_hooklib`.

**Adoption rule:** before writing a private helper in a checker, check
`_hooklib.py`; if the shared home already has it, import it. When touching a
checker, migrate a stale private copy in the same work unit only when the bound
change already touches or depends on that helper contract (behavior-preserving
only); otherwise leave the unrelated migration for a separately scoped work
unit. A deliberately divergent copy stays, with a one-line comment naming the
delta.

## The contract (harness-agnostic)

- **CI diff base:** `.github/workflows/ci.yml` exports `FORSETI_DIFF_BASE`
  as the pull request base SHA or push event `before` SHA, then rejects a
  missing, zero, malformed, or unresolvable value before any policy gate.
  Diff-scoped resolvers prefer that exact SHA, then `$GITHUB_BASE_REF`, an
  explicit CLI base, and finally local `origin/main`. Local pre-push does
  not set the CI variable and retains outgoing `origin/main...HEAD` scope.

- **Input:** the harness passes the tool event as **JSON on stdin** — at minimum
  `tool_name` and `tool_input` (with `command` for shell tools, `file_path` for writes).
- **Output / exit code:** for the raw Forseti guard, **`2` = block** the tool call
  (stderr explains why); **`0` = allow**.
  On any internal error the guard **exits 0 (fails open)** so a hook bug never bricks the agent.
- Any harness that can run a command with the tool event on stdin and honor a
  blocking exit code can use these as-is (adapt field names with a tiny shim if yours differ).
- Harnesses with their own denial protocol should use a small adapter rather than
  assuming stderr + exit code is the only blocking contract. Codex uses
  `.codex/hooks/forseti_guard_codex_adapter.py` for that translation.

## Wiring per harness

### Claude Code (current)
Register in the repo's tracked `.claude/settings.json`. The live wiring (see
that file for the authoritative registration) is:

- **PreToolUse** `Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit` →
  `guard_protected_actions.py` with a 10-second host timeout.
- **SessionStart** (no matcher) → `session_context_capsule.py --hook` with a
  5-second host timeout.
- No Claude `PostToolUse` or `Stop` hooks are registered.
Hooks load at session start — **restart the session** after editing settings.
Verify:
```powershell
python .agents/hooks/_hooklib.py --selftest
python .agents/hooks/guard_protected_actions.py --selftest
python .agents/hooks/check_review_output_provenance.py --selftest
python .agents/hooks/check_review_output_provenance.py --diff origin/main --strict
python .agents/hooks/check_review_routing.py --selftest
python .agents/hooks/check_handoff_pointers.py --selftest
python .agents/hooks/check_source_input_hashes.py --selftest
python .agents/hooks/check_source_input_hashes.py --strict
python .agents/hooks/check_prompt_output_mode.py --selftest
python .agents/hooks/check_review_summary.py --selftest
python .agents/hooks/check_hash_pin_freshness.py --selftest
python .agents/hooks/check_hash_pin_freshness.py --strict
python .agents/hooks/check_shared_helper_duplication.py --selftest
python .agents/hooks/check_shared_helper_duplication.py --strict
python .agents/hooks/check_repo_map_freshness.py --selftest
python .agents/hooks/check_search_surface_google_route.py --selftest
python .agents/hooks/check_search_surface_google_route.py --strict --base main
python .agents/hooks/check_retrieval_header.py --selftest
python .agents/hooks/check_placement.py --selftest
python .agents/hooks/check_placement.py --changed --strict --base origin/main
python .agents/hooks/check_full_gt_claims.py --selftest
python .agents/hooks/session_context_capsule.py --selftest
```

### Codex (tracked project hook)
Codex does not read `.claude/settings.json`. Forseti wires Codex through the
tracked project-local `.codex/hooks.json`, which registers:

- `PreToolUse` for `Bash|PowerShell|apply_patch|Edit|Write`;
- `.codex/hooks/forseti_guard_codex_adapter.py` as the command hook.
- `.codex/hooks/orca_guard_codex_adapter.py` remains only as a legacy shim for already-loaded Codex hook sessions; active config should use the Forseti path.
- no Codex `PostToolUse` hook is registered.

The adapter preserves the shared guard logic but returns Codex's native denial
shape:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

Run the live-adoption probe only when hook adoption testing is itself the
commissioned task. It is not routine work-unit preflight. For that test, use
this exact top-level command from the task root without a command-level
`workdir` override:

```powershell
python .codex/hooks/forseti_guard_codex_adapter.py --live-adoption-probe
```

- A live adopted `PreToolUse` hook denies the tool call with exactly
  `FORSETI_CODEX_HOOK_ADOPTION=ADOPTED`; the command body does not run.
- An absent or unloaded hook allows direct argv execution, which exits `3` and
  emits exactly `FORSETI_CODEX_HOOK_ADOPTION=NOT_INTERCEPTED`.
- Any allowed execution, wrapper invocation, different marker, or inferred
  latency result is a failed adoption gate. The observed probe result is the
  state; do not persist a trust/adoption record.

Do not place the probe in a wrapper: `PreToolUse` sees the wrapper command, not
its grandchild. Codex owns project-hook trust/adoption for managed and existing
worktree tasks. If it requires review, use only the normal Codex trust/hooks UI
and reload flow, then rerun the probe; Forseti cannot synthesize trust and must
not edit Codex trust metadata.

It also parses Codex `apply_patch` headers (`*** Add/Update/Delete File:` and
`*** Move to:`) from the supported `tool_input.command`, `.patch`, and `.input`
payload fields and checks those paths through the EP-01 protected-path rule,
because Codex reports patch edits as `tool_name: "apply_patch"` rather than
Claude-style `Write` / `Edit` events.

The adapter does not reject a valid selected worktree merely because the hook
launched from another checkout. Every `apply_patch` target and direct write event
still reaches the EP-01 protected-path guard. Target identity, revision or dirty-
byte state, writer isolation, and any actual tool, sandbox, hook, or guard denial
remain owned by `.agents/workflow-overlay/decision-routing.md`. Collaboration
subagents do not gain write scope merely by naming another path.

For `Bash` / `PowerShell`, the adapter blocks raw durable-write primitives when
the command text names repo source/docs file types (`.md`, `.py`, `.yml`,
`.yaml`, `.json`, `.toml`, `.ps1`). This is a prevention guard for the known
failure class, not universal shell-write detection; use `apply_patch` from the
active worktree for source edits.

Codex only loads project-local hooks after the project `.codex/` layer is
trusted. In a Codex session, open `/hooks` if Codex reports new or changed hooks
that need review.

Verify:
```powershell
python .agents/hooks/guard_protected_actions.py --selftest
python .agents/hooks/check_review_output_provenance.py --selftest
python .agents/hooks/check_review_output_provenance.py --diff origin/main --strict
python .agents/hooks/check_review_routing.py --selftest
python .agents/hooks/check_handoff_pointers.py --selftest
python .agents/hooks/check_source_input_hashes.py --selftest
python .agents/hooks/check_source_input_hashes.py --strict
python .agents/hooks/check_prompt_output_mode.py --selftest
python .agents/hooks/check_review_summary.py --selftest
python .agents/hooks/check_hash_pin_freshness.py --selftest
python .agents/hooks/check_hash_pin_freshness.py --strict
python .agents/hooks/check_shared_helper_duplication.py --selftest
python .agents/hooks/check_shared_helper_duplication.py --strict
python .agents/hooks/check_repo_map_freshness.py --selftest
python .agents/hooks/check_search_surface_google_route.py --selftest
python .agents/hooks/check_search_surface_google_route.py --strict --base main
python .codex/hooks/forseti_guard_codex_adapter.py --selftest
```

### Another harness
`.claude/settings.json` is **not read** by other harnesses, so:
1. If your harness has a **pre-tool command-hook** mechanism, register
   `guard_protected_actions.py` on shell + write tools and honor **exit 2 =
   block**. Do not register advisory post-tool fanout by default; run the
   repository's strict checkers at commit/CI instead.
2. If your harness has no equivalent hook API, install the tracked local Git
   hook adapters:
   ```powershell
   pwsh .github/scripts/install-local-hooks.ps1
   ```
   This sets the effective `core.hooksPath` to `.githooks` in the active
   worktree's config when `extensions.worktreeConfig` is enabled, otherwise in
   clone-local config. Verification reads the effective value, so a foreign
   higher-precedence worktree binding fails with both roots named. It enables:
   - `.githooks/pre-push` — blocks pushes targeting `main`, branch deletes, and
     non-fast-forward updates at Git's pre-push boundary, then mirrors the
     selected strict CI gates over the outgoing change (see the `pre_push_guard.py`
     row above).
   - `.githooks/commit-msg` — runs `check_repo_map_freshness.py --commit-msg`.
3. Confirm with:
   ```powershell
   python .agents/hooks/guard_protected_actions.py --selftest
   python .agents/hooks/check_repo_map_freshness.py --selftest
   python .agents/hooks/pre_push_guard.py --selftest
   pwsh .github/scripts/install-local-hooks.ps1 -VerifyOnly
   ```

### If your harness has no hook mechanism
The scripts can't auto-fire, so fall back to **enforcement outside the agent**:
- the tracked Git hooks under `.githooks/`, installed with
  `.github/scripts/install-local-hooks.ps1`, to catch `git push` and commit-time
  repo-map freshness — note they **miss `gh pr merge`** (a GitHub API call) and
  are **bypassable** with `--no-verify`;
- **CI** (already runs the test gate on every PR);
- the **merge-when-green discipline** in `docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md`.

## Scope boundary (read this)

These hooks enforce **only where they are wired.** A harness without them wired is
**not** protected by them. Two durability notes carry over from the dev-workflow doctrine:
- the **git-lifecycle protection (EP-03** — merge/push-to-main/force/destructive) is
  **portable** — wire it in any harness and it behaves the same;
- the **protected-path protection (EP-01)** is tuned to a machine's external layout, so
  it stays **per-machine** — other clones adjust their own externals.

The only **harness-agnostic, unbypassable** gate is the active **server-side branch
protection** on main (see the dev-workflow doctrine). Per-harness and local Git hooks
remain defense in depth: they fail earlier and cover destructive local actions, but they
do not weaken or replace the server gate.

---
*Navigation / setup doc only. These are advisory + enforcement tooling, not validation,
readiness, or source-of-truth promotion.*
