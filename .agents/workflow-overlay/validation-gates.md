# Validation Gates

```yaml
retrieval_header_version: 1
artifact_role: Forseti overlay authority
scope: Validation gates required before Forseti completion claims.
use_when:
  - Checking whether a Forseti completion, prompt, or artifact claim has required evidence.
  - Defining validation expectations for docs/decision work, explicitly authorized implementation work, prompts, and artifacts.
authority_boundary: retrieval_only
```

**Routine read shape** (owned by `.agents/workflow-overlay/source-loading.md`,
Targeted Read Protocol): closeout checks read the preamble below (evidence
economy and failure-visibility buckets) plus "Current Gates"; prompt
authoring reads "Prompt Orchestration Gates"; product-proof work reads
"Product Proof Gates"; enforcement-placement decisions read "Enforcement
Placement"; a full-file read is for editing validation doctrine.

Validation must be able to fail. Missing evidence is not a pass.

Validation evidence is claim-scoped and remains reusable until relevant
changed bytes or mutable external state could falsify the supported claim. Run
focused local checks for affected behavior and use required CI for broad
integration. Do not duplicate a broad suite locally when required CI exercises
the same behavior unless a focused failure, cross-cutting uncertainty, or an
unavailable CI environment makes broader local diagnosis necessary. A focused
failure blocks broader runs until it is diagnosed. Relevant implementation,
test, dependency, checker, PR-head, or lake/index/writer changes invalidate only
the evidence they can affect; mutable external and durable lifecycle claims
still require fresh readback. A gate's evidence is its exit code plus its
bucketed findings. Do not re-run a passing gate to improve the readability,
formatting, or completeness of its output; capture the run once and read the
captured output. Re-run only when changed bytes could falsify the claim.

Validation reports must preserve failure visibility by bucket:

- `GATE PASS` / `GATE FAIL` are exit-code-bearing checks required for the claim.
- `INFO` / `DEBT` is explicit allowlisted non-gating output; it never changes the gate exit code.
- `OUT OF SCOPE` must name the owning lane or source surface; it cannot mean inconvenient or ignored.
- Unknown nonzero exits, unknown findings, and wrapper-internal errors default to `GATE FAIL`, never
  `INFO`. A future wrapper may encode this policy, but bucket membership is owned here; any wrapper
  script that encodes it must exit nonzero iff any `GATE FAIL` exists.

Throughout Forseti workflow doctrine, a `status claim` asserts acceptance or
approval; validation, readiness, or completion (including `PASS` or
`ADEQUATE_NOW`); implementation, deployment, installation, or resolver state;
source-of-truth promotion; or buyer pull / willingness to pay. A `strict status
claim` uses one of those states to clear a gate or authorize movement. Domain
owners may bind narrower tokens, but compressed references to status claims
inherit this floor.

## Current Gates

- Required Forseti files exist before claiming bootstrap completion.
- Diff-scoped CI gates bind one exact event base SHA: pull requests use
  `github.event.pull_request.base.sha`; pushes to `main` use
  `github.event.before`. `.github/workflows/ci.yml` exports that value as
  `FORSETI_DIFF_BASE` and fails closed before policy gates when it is absent,
  all-zero, malformed, or unresolvable after full-history checkout. Checker
  resolution priority is `FORSETI_DIFF_BASE`, then `$GITHUB_BASE_REF`, then
  an explicit CLI base, then local `origin/main`. The local pre-push mirror
  deliberately leaves the CI variable unset and scans outgoing
  `origin/main...HEAD`; this event contract changes CI scope, not hook scope.
- Harness coupling contract preflight: when the exact CI event diff (or local
  outgoing `origin/main...HEAD` diff) touches `forseti-harness/**/*.py` or the
  generated `forseti-harness/data_lake/lake_touchpoint_inventory_v0.json`,
  `.agents/hooks/check_harness_coupling.py --strict` runs the existing
  `test_data_lake_inventory_gate.py` and `test_policy_module_version_pins.py`
  contract files before the full suite. Diff-resolution and launch errors fail
  closed. The adapter adds no test rule and a pass is not full-suite validation,
  readiness, approval, or proof that every CI failure is prevented.
- No software implementation directories are present unless explicitly authorized.
- `AGENTS.md` and overlay files do not encode `jb` project-specific authority as Forseti rules.
- Material authority, source-scope, edit-permission, and repository-state checks
  occur before repo-aware work. A `forseti_start_preflight` receipt is required
  only at the durable/cross-lane and portable strict-claim boundaries in
  `.agents/workflow-overlay/source-loading.md`; missing receipt evidence blocks
  that portable handoff or claim, not ordinary interactive work.
- Doctrine-changing source work must carry direction-change propagation
  evidence under `.agents/workflow-overlay/source-of-truth.md` before claiming
  completion. The PR body or final closeout is the default; an inline receipt or
  blocker is exceptional under that owner. Missing propagation evidence blocks
  strict success or status claims that depend on the changed doctrine; it
  authorizes no adjacent cleanup or tooling.
- Writable-root acceptance follows the one-time binding owned by
  `.agents/workflow-overlay/decision-routing.md`:

  | Commission state | Acceptance result | Required evidence or recovery |
  | --- | --- | --- |
  | Current actor in its selected branch/worktree | `accepted` after one snapshot | Observe exact target, revision and dirty state, and no competing writer. Continue unless a required tool actually denies access; launch-root mismatch alone is not failure. No synthetic write/index probe or hook canary. |
  | New managed-worktree receiver | `accepted` once after creation | The task is created and rooted in its app-managed worktree under explicit task-creation authority; exact/ancestor and dirty-state rules still apply. |
  | User-authorized multi-task group | `accepted` after all required members launch | Same-root roles use collaboration; each independent role has one uniquely titled managed task with an executable initial prompt. Member-local recovery stays in that task, or replaces only an unusable member once. Unaffected members continue. |
  | External controller targeting another worktree | `accepted` once after verification | Unique commissioned target under exact or explicitly permitted ancestor semantics; demonstrated direct write; target-rooted operation; no concurrent writer. A `.codex`, `.claude`, or other manager-prefixed target path is neutral: the commission supplies authority and observed capability supplies the route. |
  | Delayed delegated review of an advancing clean lane | `accepted` under `ancestor` | Verify `required_revision` is an ancestor of current `HEAD`, then record current `HEAD` as immutable `reviewed_revision` before source review. Return both revisions. If the author continues, review and patch only in a separate clean worktree/branch at the captured revision; never share a moving worktree. |
  | Collaboration subagent pointed at a separate worktree | `blocked` | Collaboration is same-root only; use a separately bound receiver rather than treating a named path as rerooting. |
  | Same actor targeting its selected worktree from another launch checkout | `accepted` after the target snapshot | A directory override does not expand a collaboration subagent's sandbox, but launch-root mismatch alone is not failure. Reroot only after an observed required-tool denial or root-bound feature mismatch. |
  | Unknown future/manual courier | `preparation_allowed`, dispatch and source loading `blocked` | Keep `receiver_class: receiver_to_bind`; bind and verify a concrete receiver before claiming dispatch readiness. |
  | Observed target ambiguity, required-tool denial, or root-bound feature mismatch | route or `BLOCKED_RECEIVER_REROOT_REQUIRED` | Reroot only when the mismatch is real and no already-authorized capable route exists. |
  | Ambiguous, unexpectedly dirty, or concurrently written target | `blocked` | Freeze uncommitted work into a commit and re-pin, or resolve the ambiguity and eliminate concurrent writing; missing evidence is not a pass. |

  The binding is re-resolved only when receiver/task/root or material target
  state changes, capability is genuinely unknown, or an observed mismatch or
  dirty-state change invalidates it. This matrix accepts semantic user
  authorization for a new task or handoff when the visible instruction
  explicitly requests it; generic `proceed` alone is
  not task-creation authority. Receipt fields remain evidence pointers, not self-certifying proof.
  For clean repo-changing receivers, the `revision_mode` assertions are exact:
  `exact` requires a clean worktree and `HEAD == required_revision`; `ancestor`
  requires a clean worktree and a zero exit from
  `git merge-base --is-ancestor <required_revision> HEAD`. `ancestor` is valid
  only where the commission explicitly permits an advancing lane; delayed
  delegated reviews of such lanes default to it. Their receiving preflight
  captures the then-current `HEAD` as `reviewed_revision`, which becomes exact
  for that review run. It never satisfies an existing exact gate. Live
  hook-adoption probing is reserved for a commission whose purpose is that
  adoption test, never routine lane proof.
- Multi-task conservation is a resident acceptance judgment. A full-group
  restart is accepted only for cross-member contamination, a changed common
  contract or controlled variable, a required revision change after evidence or
  output was produced, or material timing drift under an explicitly timing-
  controlled commission. Setup, transport, VPN, path, hash, launch-root, and
  ordinary member-preflight failures recover in the same task; an unusable task
  may be replaced once without replacing unaffected members. Superseded tasks
  are archived after the authoritative replacement or group is bound.
- Review-routing disposition gate: a change that touches code roots
  (`forseti-harness/`, `.agents/hooks/`) must carry its review disposition in the
  same change — either a review artifact added under `docs/prompts/reviews/`
  or `docs/review-outputs/`, or a shape-valid `review_routing_status:` line in
  one of the change's commit messages:
  `review_routing_status: routed <existing docs/prompts/reviews/... or docs/review-outputs/... path>`,
  `review_routing_status: routed -- chat_only_adjudicated: <review return and adjudication disposition>`,
  `review_routing_status: blocked -- <reason>`, or
  `review_routing_status: not_needed -- <reason>`.
  A carried recommended or required adversarial review may close only as
  `routed` or `blocked`, never `not_needed` (the fused/review contracts own
  that vocabulary; this gate does not weaken it). The disposition is routing
  shape only: it is not review quality, review truth, severity authority,
  validation, or readiness, and the gate never decides whether review SHOULD
  have been recommended — that stays resident scoping judgment. Enforced
  diff-scoped and forward-only by `.agents/hooks/check_review_routing.py`
  (local `--commit-msg` advisory; CI `--strict`).
- Handoff-pointer resolution gate: a changed durable `.md` file must not
  reference a handoff-packet path (`docs/workflows/*handoff*.md`,
  `docs/prompts/handoffs/*.md`) that does not resolve in the same tree,
  unless the pointer line carries an explicit resolution pin (the word
  `branch`, `PR #<n>`, or an `origin/<ref>` token — a fetch handle for a cold
  reader) or an exemption marker (`does not exist yet`, `created on first`,
  `not retrieval-indexed`, `nonresolving:`, or superseded/removed/deleted
  wording for retired packets). Practical consequence: a handoff packet
  merges no later than the first main-bound artifact that points at it (the
  same PR is fine), or the pointer pins the authoring branch explicitly — a
  cold receiving lane resolves required reads from `origin/main`, not from
  unmerged authoring branches. The gate is pointer shape only: it never
  proves a packet's content is current, that a pinned branch still exists, or
  that the cited packet was the right source — that stays resident judgment.
  Couriers that never land in the repo (chat bodies, PR comments, ignored
  `docs/_inbox/` scratch) are outside its reach and stay governed by
  `.agents/workflow-overlay/prompt-orchestration.md`. Enforced diff-scoped
  and forward-only by `.agents/hooks/check_handoff_pointers.py` (CI
  `--strict`; whole-corpus backlog via `--audit`, never gated).
- Source-input hash freshness gate: changed repo-local JSON `source_inputs[]`
  records that carry `source_pointer` + `sha256` must match current file bytes
  (CRLF-normalized), and source-capture packet manifests (top-level
  `manifest_version`) must have top-level `preserved_files[]` records whose
  `relative_packet_path` + `sha256` match current raw stored bytes resolved
  against the manifest's own directory, when the JSON artifact or referenced
  file changed. This is provenance freshness only: it is not semantic
  validation, generated-artifact completeness, readiness, source quality,
  capture freshness, or metric validity. Enforced diff-scoped and forward-only
  by `.agents/hooks/check_source_input_hashes.py` (CI `--strict`; local
  pre-push mirror; whole-repo advisory via `--audit`, never gated).
- Review-summary shape gate: a changed durable review output under
  `docs/review-outputs/` carrying a real (non-template) `review_summary`
  YAML block must keep the block's mechanically checkable shape from
  `.agents/workflow-overlay/communication-style.md`: none of the forbidden
  process keys, a `report_path` that resolves in the same tree, the bound
  failed-write shape when `status: failed` (no `report_path`,
  `recommendation: blocked`, `review_location: chat_only_current_thread`),
  and a non-blank `recommendation` when the key is present. Full
  `recommendation` vocabulary membership is advisory only (`--audit`):
  delegated-review-patch lanes carry an extended vocabulary that
  `communication-style.md` does not bind, and the owner accepted
  (2026-07-10) keeping enum membership advisory — the extended vocabulary
  stays unbound, the 5-value enum remains the canonical target for new
  summaries, and drift is tracked, never gated. The gate is
  summary shape only: it is not review quality, finding truth, severity
  authority, validation, or readiness; retrieval-header, provenance, and
  fencing checks stay with `check_review_output_provenance.py`. Enforced
  diff-scoped and forward-only by `.agents/hooks/check_review_summary.py`
  (CI `--strict`; whole-corpus advisory via `--audit`, never gated).
- Hash-pin freshness gate: markdown freshness hash pins in changed durable
  docs — labeled `path:` + `sha256:` bullet pairs (e.g. the skill-adoption
  source pins) and `source_captures/**/receipt.md` preserved-file bullets —
  must match the current CRLF-normalized bytes of their repo-local targets
  when the pin-carrying doc or the pinned target changed. Provenance-style
  records (package-manifest tables, source-read ledgers, external-repo
  bootstrap tables) are deliberately not parsed as pins: they record a past
  observation, and gating them would false-block working-as-intended
  history. This is pin freshness only: not semantic validity, source
  quality, capture freshness, skill correctness, validation, or readiness.
  The markdown sibling of the source-input hash freshness gate above.
  Enforced diff-scoped and forward-only by
  `.agents/hooks/check_hash_pin_freshness.py` (CI `--strict`; local pre-push
  mirror; whole-repo advisory via `--audit`, never gated).
- Shared-helper adoption gate: an added line in `forseti-harness/**/*.py`
  (excluding `forseti-harness/tests/**` and `harness_utils.py` itself) or
  `.agents/hooks/*.py` (excluding `_hooklib.py` and
  `guard_protected_actions.py`, whose import-free duplication is the
  documented deliberate exception) that privately re-defines a shared helper
  — `_utc_now` / `_now_utc` / `_utc_now_z` / `_utc_now_iso` / `_sha256*` /
  `_as_dict` / `_hash_file` / `_string_or_none` / `_non_empty_string_or_none` /
  `_int_or_none` / `_bool_or_none` anywhere in scope, plus
  `_is_forbidden_field_name` / `_first_match` / `_dedupe_preserve_order` /
  `_read_packet_directory` in `forseti-harness/` only, plus `repo_root` / `_git` /
  `_git_lines` / `porcelain_paths` in `.agents/hooks/` only — must either use
  the owning shared home (`forseti-harness/harness_utils.py` /
  `forseti-harness/source_capture/projection_shared.py` /
  `.agents/hooks/_hooklib.py`) or carry, on the def line or the line
  immediately above, a comment naming the delta vs the shared home (any
  comment containing `harness_utils`, `_hooklib`, `projection_shared`, or
  `helper-delta`). The
  rule itself is owned by the adoption-rule paragraphs in
  `.agents/hooks/README.md` and `forseti-harness/README.md`; this gate is
  their mechanical backstop and is forward-only: pre-existing private copies
  are never gated. Shape only: never helper correctness, divergence
  justification, validation, or readiness. Enforced diff-scoped by
  `.agents/hooks/check_shared_helper_duplication.py` (CI `--strict`; dormant
  `--hook` compatibility is not registered interactively).
- Ontology-tag validity gate: changed tracked Markdown files are scanned against
  the ontology SSOT roster over the CI event base (or local pre-push
  `origin/main...HEAD`); an additive annotation
  that looks like an ontology type but names no roster type fails. Deletions,
  untracked files, scratch, and nested worktrees are outside strict diff scope;
  `--check` retains the explicit whole-tree advisory scan. Enforced by
  `.agents/hooks/check_ontology_tag_validity.py` in CI and the local pre-push
  mirror. An unresolvable diff base fails open with a loud infrastructure-gap
  warning, never a pass claim. Tag-shape only: not ontology correctness,
  semantic validity, validation, readiness, or approval.
- Receipt-field provenance gate (non-self-certification): a gate, predicate,
  acceptance check, or completion claim must not clear on a self-asserted field
  value. A field clears only when it is owner-produced and provenance-bound or
  independently verifiable — computed, re-derivable, audited, or produced by an
  authorized process. A value a by-hand, unauthorized, dry-runner,
  local-fixture, manually normalized, or operator-authored record could simply
  assert is not self-certifying and does not clear, even when it reads `proven`,
  `pass_valid`, `valid`, or `complete`. Where no owner-produced or verifiable
  field exists yet, the check is `indeterminate_until_authored` (blocked, not
  passed); do not clear on a paraphrase and do not invent the field. Corollaries:
  (a) fix the whole class of such checks in one pass, not one instance; (b)
  verify a cited source actually defines the field before binding a check to it;
  (c) single-source any value otherwise enumerated in multiple places (enumerate
  once; reference it). This gate is a check, not validation or readiness
  evidence; its presence does not prove any artifact passes it. Lifecycle:
  Forseti-local adoption of general authoring/review discipline, not Forseti-owned
  doctrine; it is a candidate for future skill-source adoption and becomes
  stale here if an equivalent accepted skill-source rule is adopted.
- New or materially touched durable human-authored workflow artifacts follow
  `.agents/workflow-overlay/retrieval-metadata.md` or are clearly outside that
  contract.
- New or materially touched durable artifacts close against `AGENTS.md`
  ("Artifact-Level Smallest Complete Intervention"): resident judgment must
  confirm a distinct future consumer, outcome, or lifecycle; standalone
  usability without authoring-chat reconstruction; the material authority,
  currentness, and next-source facts; no duplicated authority or speculative
  registry; and reconciliation of affected supersession, retirement, and live
  routers. Deterministic tooling may check objective router-target existence,
  but a green path check does not establish semantic completeness.
- Report-only retrievability checks may use
  `docs/workflows/artifact_retrievability_guide.md` for artifact body-opening
  shape, stale/recheck clarity, repo-map/index treatment, and hygiene anti-rot.
  Findings are routing or hygiene defects only; they do not prove validation
  failure, validation success, approval, readiness, lifecycle completion,
  implementation authorization, or edit permission.
- Repo-map T1 admission gate: a change that adds or materially expands a row in
  `docs/workflows/forseti_repo_map_v0.md` must identify which T1 class in
  `docs/decisions/forseti_repo_map_architecture_mgt_v0.md` it serves and why an
  existing area row, submap, retrieval header, or generated
  `header_index.py --index` route is insufficient. A valid path, passing link
  check, or freshness trigger is not admission evidence. Reviewers reject
  per-file inventory, historical chronology, embedded operating manuals, and
  duplicated owner-source descriptions. This gate is resident judgment: the
  existing retrieval checkers continue to enforce existence, reachability,
  freshness, and header shape only; none claims semantic T1 admission.
- Source hashes for migration-governance inputs are recorded in `docs/workflows/orca_bootstrap_record.md`.
- Resolver-visible skill-name snapshots are recorded before any skill adoption or promotion work.
- Git status is reported when this workspace is a Git repo.

## Prompt Orchestration Gates

- Behavioral-mechanism admission gate: a new or materially expanded standing
  prompt field, preflight, gate, receipt, review pass, hook, checker, artifact,
  or sync obligation must satisfy the overlay Behavioral Admission rule. Name
  the bound outcome, defect class, trigger, recurring cost, and why an existing
  lower-cost boundary is insufficient. If that case cannot be made, exclude
  the mechanism.
- Overlay authority gate: `AGENTS.md` and `.agents/workflow-overlay/README.md`
  must be read before prompt-orchestration work. Routine prompts carry the
  complete inline core; escalated prompts carry the portable start receipt and
  fields owned by `.agents/workflow-overlay/source-loading.md` and
  `.agents/workflow-overlay/prompt-orchestration.md`.
- Artifact role gate: every prompt role must be bound in `.agents/workflow-overlay/artifact-roles.md` or another accepted Forseti overlay file.
- Source-resolution gate: external workflow sources do not provide Forseti authority; installed skills are deployment copies; `jb` project policy must not be imported.
- Effective-target gate: same-lane prompts point to the active one-time target
  snapshot and do not repeat root receipts, probes, canaries, or capability
  recitals. The current actor may continue against its selected worktree when
  launch and target roots differ. New/external receivers carry class-specific
  evidence; collaboration remains same-root and unknown couriers preparation-
  only. Reroot only after observed ambiguity, required-tool denial, root-bound
  feature mismatch, or writer conflict leaves no authorized capable path.
- Multi-task conservation gate: a multi-task commission must choose
  collaboration for same-root roles and create only the independent
  worktree/lifecycle members the outcome requires. Those members launch as one
  uniquely titled group with executable initial prompts. Preparation-only
  members followed by routine release turns, synthetic mutation probes,
  per-member shared-prompt hash ceremonies, duplicate role tasks, a new group or
  attempt ID for a member-local failure, and full-group restart without a named
  shared invalidator are prompt-quality defects. Replacement is limited to one
  unusable member while unaffected tasks continue.

  The mechanically checkable commission shell is enforced by the existing
  `.agents/hooks/check_prompt_output_mode.py`: changed filed prompts use its
  diff-scoped `--strict` mode, and chat/courier authoring gates the frozen
  rendered body through `--validate-stdin` before use. This check covers only
  exact authorization shape, binding consistency, prohibited manual/repeated
  creation directives, and typed source-load failure. It does not prove live
  receiver identity, vendor truth, capability, source freshness, or writer
  isolation. The former delegated-patch courier-shell check was retired
  2026-07-25 with the lane binding: the courier who-constraint (operator-only
  delivery, direct repo access, different-vendor eligibility) is owned by
  `.agents/workflow-overlay/delegated-review-patch.md` and enforced at CA
  adjudication, not by a self-declared prompt token.
- Control-plane source-state gate: repository-aware prompts, prompt-policy
  patches, workflow patches, and CA handoffs must classify controlling Forseti
  sources as clean, modified, untracked, stale, or not checked when those
  sources affect strict claims. Modified or untracked controlling sources may
  support advisory work, but strict status claims remain blocked unless owner
  acceptance or controlling authority is explicit.
- Output-mode gate: prompts must name exactly one output mode from `.agents/workflow-overlay/prompt-orchestration.md`.
  The mechanically checkable shell — an output-mode declaration naming at
  least one closed-set token in a changed `docs/prompts/**` artifact
  (templates and READMEs excluded) — is enforced diff-scoped and forward-only
  by `.agents/hooks/check_prompt_output_mode.py` (CI `--strict`; backlog via
  `--audit`, never gated). Whether the mode is exactly one and correctly
  scoped to this artifact rather than a nested dispatch/receiver role stays
  resident judgment; multi-declaration and compound-token shapes are
  advisory INFO, never gate failures.
- Chat-output topology gate: prompt-policy patches, workflow patches, and
  reusable prompt templates touching chat output shape must check for
  contradictions between the general human-summary / agent-detail /
  optional courier-state rule in
  `.agents/workflow-overlay/communication-style.md` and output-mode exceptions
  in `.agents/workflow-overlay/prompt-orchestration.md`.
  This is a collision gate, not a required-key checklist: decision-bearing chat
  should start with human-readable prose; agent detail should stay separate;
  courier state should stay compact and last when used; YAML should not be
  defaulted unless the user asks, an output mode requires it, an explicit
  output contract needs machine-shaped fields, or lane switching / handoff
  routing would materially benefit from compact courier YAML;
  `review-report` YAML-only chat remains tied to successful durable report
  writes; `file-write` receipts remain valid only when the durable artifact
  carries the human value and no material decision must be understood from chat;
  `paste-ready-chat` must be classified
  before template propagation; task-native structured outputs such as evidence
  tables must not be naively rewritten into verbose closeouts; already-correct
  active `review-report` prompts and stale one-offs must not be broad-synced;
  and extra courier keys or ritual non-claim fields must not be added merely to
  satisfy process metrics.
- Review-report topology gate: prompts and prompt-policy patches touching
  `review-report` must check that the saved-report exception is adjacent to the
  owning output-mode rule; the durable report remains the review artifact; chat
  YAML remains courier output; YAML-only chat is valid only after successful
  report write, explicit chat-only selection, or pre-write blockage; failed
  durable writes use `status: failed`, `recommendation: blocked`,
  `review_location: chat_only_current_thread`, and no `report_path`; the failed
  path is named in human-readable routing detail; no extra YAML keys are added
  for process metrics; retrieval metadata stays retrieval-only; active
  templates/prompts are patched or stale one-offs are queued for hygiene; and
  no validation, approval, readiness, resolver, lifecycle, install, deploy,
  merge-safety, or product-readiness claim is introduced.
- Review-doctrine gate: review prompts, review templates, review-output
  closeouts, and CA-facing review handoffs must keep review output
  findings-first by default; require adversarial artifact review prompts to
  invoke `workflow-adversarial-artifact-review` after source readiness or block
  strict claims as advisory-only; bind any formal verdict, severity contract,
  blocked/ready status, validation claim, readiness claim, mandatory
  remediation, patch queue, or executor-ready handoff; include
  `minimum_closure_condition` and `next_authorized_action` for actionable
  findings; define closure conditions as required end states rather than
  implementation instructions; label optional hardening as optional and
  non-required; exclude `patch_queue_entry` unless the lane is patch-queue
  review or patch/integration execution; preserve the Chief Architect
  consumption order from `.agents/workflow-overlay/communication-style.md`; and
  avoid creating a synthesis lane. Missing or contradictory doctrine binding
  blocks strict `PASS`, readiness, acceptance, validation, or
  alignment-complete claims.
- Source-evidence preservation gate: source-heavy work persists a unit only
  when its evidence must survive compaction, cross a receiver boundary, or is
  itself the requested deliverable. Otherwise use targeted reads and source
  pointers. A claim blocks only when its evidence cannot be reconstructed or
  verified; compaction alone is not contamination.
- Readback economy gate: prompt validation must use targeted existence, hash,
  marker, status, and count checks. It must not require full artifact echo, full
  ledger-row echo, pasted Evidence Units, or broad source dumps unless a
  targeted failure makes that exact excerpt necessary.
- Document-pinned projection falsifier: when a delegated code target changes a
  builder or projector whose bytes could affect a frozen artifact that an
  in-scope document explicitly uses for identity, compatibility, or proof, the
  commission must name a baseline rebuild or reprojection of each affected pin
  from its bound inputs at immutable `reviewed_revision` and compare the result
  with the pinned artifact or semantics. If the controller then changes
  builder, projector, input, or pin bytes that could affect that result or
  claim, rerun once after those patch bytes settle and report the final result
  as working-tree evidence tied to the returned diff, not as evidence from
  `reviewed_revision`; otherwise reuse the baseline evidence. This does not
  require a repository-wide artifact census or a check when no in-scope
  document carries such a pin. Missing tooling or inputs is `not-run` and
  blocks only the compatibility or proof claim that depends on the pin; it is
  never a generic review failure.
- Retrieval-metadata gate: new or materially touched durable prompt artifacts
  must follow `.agents/workflow-overlay/retrieval-metadata.md` without using
  retrieval metadata as authority, validation proof, approval, readiness,
  lifecycle completion, deployment/install/resolver status, or edit permission.
- Rerun economy gate: retry prompts must name the prior artifact, frozen decisions, mutable fields, and unresolved finding.
- Leakage gate: prompt artifacts must not copy `jb` templates, GAP/CV Engine paths, compiler paths, handoff rules, product-lead rules, or repo-local lifecycle mechanics.

## Product Proof Gates

- Judgment Spine claim-tier gate: Judgment Spine product-learning,
  buyer-proof, advisory, backtest, fixture, model-run, scoring, memo, deck,
  calibration, architecture, spec, prompt, wrapper, and runbook artifacts must
  classify the claim tier and closeout state using
  `forseti/product/spines/judgment/claim_ladder/judgment_spine_evidence_ladder_architecture_v0.md` before
  making proof, readiness, validation, fixture-admission, scoring,
  blind-use-readiness, or judgment-quality claims. Product-Learning evidence
  cannot be reused as Buyer-Proof or Judgment-Quality evidence without the
  explicit promotion gate for the stronger tier. Classifications must apply the
  ladder's weakest-cleared-gate rule: source-quality and execution-quality gaps
  cap the claim at the lowest cleared gate, and missing evidence is not a pass.
  If no durable evidence exists for the evaluated run, answer, proof, scoring,
  or judgment-quality claim, the closeout state is `no_durable_evidence`.
  The classification must appear inline in the artifact being classified or
  co-reference a durable classification record with a path, hash, or equivalent
  retrieval handle.
  Architecture, spec, prompt, wrapper, and runbook artifacts are design or
  product-learning inputs by default; they are not Buyer-Proof or
  Judgment-Quality evidence unless the stronger tier's receipt is satisfied.

- Objection/refusal gate: product-proof, customer-discovery, buyer-proof, memo,
  deck, and readback artifacts must not treat initial buyer skepticism as a
  kill criterion. They must classify skepticism as `trust_objection` unless
  the buyer refuses the evidence type regardless of evidence quality, examples,
  numbers, mechanism, case logic, or proof experience.
- Trust-refusal gate: only `trust_refusal` may disqualify on public-signal
  trust grounds. `trust_objection` is proof material and must be captured,
  tested, and read back when other qualification gates pass.
- Pull-versus-praise gate: product-proof artifacts must distinguish observable
  decision or budget-adjacent behavior from approval language, praise,
  curiosity, generic research interest, or requests for source volume.
- Zero-spoiler backtest gate: case-study, consulting-case, preflight,
  participant-packet, and backtest artifacts must not expose actual decisions,
  consulting recommendations, implementation actions, post-cutoff facts,
  outcomes, result quality, or leaking source titles/snippets/URLs before the
  owner or participant blind judgment is sealed. If leakage occurs, the
  participant-facing packet is contaminated and must be rebuilt from clean
  pre-cutoff sources before blind use.

## Enforcement Placement

Use the lowest-cost deterministic boundary that still catches the named defect
before irreversible harm. Interactive hooks are reserved for prevention where
a later commit/CI failure would be too late (for example protected actions).
Durable artifact-shape rules belong at commit/CI when that boundary can reject
the landing change without losing work; do not install advisory per-tool fanout
merely because a rule is mechanically checkable. A checker references its rule
authority rather than restating it, and a green substrate proves shape only,
never truth, readiness, or approval. Judgment-based rules (claim discipline,
scope, lifecycle reasoning) stay resident and must actually fire. The per-rule
classification and build history live in
`docs/decisions/overlay_enforcement_placement_classification_v0.md`.

Active placement instance: `.agents/hooks/check_placement.py --changed --strict`
runs in CI against the exact event base. It checks added/modified/copied paths
and rename destinations, ignores deletions, and runs the lightweight
map↔top-level-tree freshness check. Unavailable strict diff or invalid map fails
visibly. It is not registered as a pre-push or interactive hook.

Receiver selection is one such judgment rule: whether a commission is read-only,
a same-actor work unit in selected isolation, or an independent repo-changing
lane depends on the requested act and live capability. Deterministic enforcement
remains at protected actions, frozen-pin identity under exact or explicitly
permitted ancestor semantics, and actual tool or sandbox denial; do not add a
blanket path-location guard that treats a valid selected worktree as an error.
An independent external controller still proves direct access to the bound
target once.

Multi-task conservation is also resident judgment. Repository CI cannot observe
Codex task identity, titles, handoffs, archive state, or whether a controller
unnecessarily recreated an unaffected member. Do not add a registry, daemon,
prompt field, or repository checker to simulate that state. The task API is the
operating boundary; the controller applies the conservation and archive rules
there, while ordinary repository gates continue to validate each member's
durable output.

The Codex live adoption probe remains available only when hook adoption testing
is itself commissioned. In that test it is a fail-closed runtime assertion:
the live `PreToolUse` adapter denies one exact harmless top-level command with
the stable adopted marker, while absent/unloaded wiring executes the adapter's
direct fallback and exits nonzero with the stable not-intercepted marker. This
proves only adoption for that live task; it is not routine work-unit preflight,
persisted state, trust metadata, or a Forseti-owned substitute for Codex's
project-hook trust UI.

The managed-receiver commission shape check is EP-38 and reuses
`.agents/hooks/check_prompt_output_mode.py` rather than adding a standalone
checker. It rejects a filed or stdin-rendered prompt that self-declares the
mechanically decidable trigger but omits or contradicts the exact bounded
authorization shell owned by `prompt-orchestration.md`. Its positive trigger is
the prompt's own declared fields, not an inference about the requested act; a
green result never certifies those fields or any future receiver state.

Active retrieval-header enforcement is the diff-scoped
`.agents/hooks/header_index.py --strict` CI gate. The retained
`check_retrieval_header.py --hook` mode is dormant compatibility, not live
wiring. Placement decides where a rule is enforced, not whether it is correct:
a passing check is not validation, readiness, approval, or source-of-truth
promotion.

**Live-router direct-target check** (`.agents/hooks/check_map_links.py`, C5).
The existing map/link gate also checks the authoritative-target column of the
Artifact Roles `Role Bindings` table and the Doctrine Index product-spine table.
Each live row must carry a repo-rooted target that exists directly in the
current tree; moved-path indexes do not satisfy a live router. This is objective
path existence only — not authority, currentness, semantic completeness,
validation, readiness, or proof that the routed source is the right one.

**Retrieval-header index + forward-only CI gate** (`.agents/hooks/header_index.py`).
Companion to EP-06. Adds three non-blocking surfaces and one CI gate:
- `--index`: full retrieval view of all header-bearing durable docs (human use).
- `--health [--verbose]`: whole-repo advisory counts of MISSING-HEADER and ORPHAN
  docs; exit 0 always (backlog surfaced, not gated).
- `--health --oneline`: compact manual advisory health output; it is not emitted
  by the lean SessionStart capsule.
- `--strict`: **CI gate — diff-scoped, forward-only.** For changed durable `.md`
  files only (vs the CI event base, PR branch fallback, or local
  `origin/main`): fails (exit 1) if a
  changed doc is MISSING-HEADER or is an ORPHAN (not substring-found in the repo
  map or any submap).  Pre-existing backlog is never gated — only new/changed docs
  are in scope.  Fails OPEN (exit 0) if diff-scoping is unavailable; never falls
  back to whole-repo strict.
Registered in `.github/workflows/ci.yml` after the existing link-check step.

**Google search-surface route guard**
(`.agents/hooks/check_search_surface_google_route.py`). Diff-scoped CI gate for
the mechanically checkable shell of
`docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md`:
Google Search capture URLs in changed durable docs carry the bound route
parameters; artifacts using the route carry the physical-locality non-claim; and
blocked Google pages with visible exit-IP content are not preserved in durable
docs. This is route-shape enforcement only. It is not physical-locality proof,
source sufficiency, validation, readiness, demand proof, Judgment evidence, or
Product Lead evidence.

**Retrieval-header forbidden-field scan** (`.agents/hooks/check_retrieval_header.py`,
EP-07 forbidden-field subset — the part previously deferred). The shared header
predicate (`header_problems_for_lines`, used by the dormant compatibility mode
and the active `header_index.py --strict` CI gate) rejects status-leak keys in a
retrieval header — approval / validation / readiness / lifecycle / deployment /
install / resolver / publication / source-of-truth status — referencing
`retrieval-metadata.md` ("Forbidden Header Fields"), never restating it.
Born-green (no current in-scope header uses these keys). `edit_permission` /
`verdict` / `status` are intentionally NOT banned: review-output and prompt
frontmatter legitimately carry them. A `use_when` 1–3 count and a closed
allowed-key set were assessed and intentionally NOT enforced — the corpus mixes
retrieval-header fields with required review/prompt-provenance frontmatter in one
block, so neither is born-green. Placement enforces header shape, never truth.

**Exceptional doctrine-change receipt-shape gate**
(`.agents/hooks/check_dcp_receipt.py`, EP-09 shape subset). Diff-scoped,
forward-only CI validates the shape of any exceptional durable
`direction_change_propagation` receipt or blocker present in changed Markdown.
It never requires a receipt, decides that one is justified, or verifies the
truth of its propagation claims. Registered in `.github/workflows/ci.yml`;
`--audit` is maintenance-only and `--selftest` is present.

**Review-routing disposition gate** (`.agents/hooks/check_review_routing.py`,
EP-35). Diff-scoped, forward-only CI gate plus a local commit-msg advisory: a
change touching code roots must carry its review disposition — a review
artifact filed in the same change, or a shape-valid `review_routing_status`
line (grammar owned by the Current Gates bullet above), with path-routed targets
verified to exist and chat-only adjudication carrying a non-empty durable
disposition rather than duplicated findings. Born from the 2026-07-02 fused-lane audit: most fused
implementation lanes closed without filing the delegated-review handoff their
contract carried, several claimed it in commit prose without filing it, and
the disposition lived only in chat where nothing durable could check it
(51 of 67 code-root landings in the trailing 120 main commits carried no
disposition at build time — advisory backlog via `--audit`, never gated).
The gate checks disposition PRESENCE and SHAPE only — never the truth of a
`not_needed` reason, the quality of a filed review, or whether review should
have been recommended (resident judgment; cf. the receipt-field provenance
gate). Registered in `.github/workflows/ci.yml` and `.githooks/commit-msg`;
`--selftest` present.

**Local pre-push selected-gate mirror** (`.agents/hooks/pre_push_guard.py`, the
policy behind the `.githooks/pre-push` adapter). For a push whose update lines
pass the guard's safety checks, the guard runs ten selected strict CI gates over the
outgoing `origin/main...HEAD` change: retrieval links and headers, review
routing and review-output provenance, source-input and markdown hash freshness,
prompt output mode, handoff-pointer resolution, ontology tag validity, and the
conditional harness coupling contracts.
The same checker modes run in `.github/workflows/ci.yml`; CI supplies its
exact event base while pre-push supplies local `origin/main`; the mirror adds
no rule. A
nonzero or unlaunchable gate blocks the push (the GATE FAIL bucket above); the
checkers' documented infra-gap fail-opens remain loud and unchanged. The four
gates added 2026-07-11 were selected from observed CI failure frequency and
measured locally before adoption: prompt output mode, review provenance, and
handoff pointers completed in under 0.2 seconds each; ontology tag validity was
first converted from an 18-second whole-worktree walk that captured untracked
nested worktrees to a tracked, diff-scoped gate. Local Git hook only: bypassable
with `--no-verify`; it does not see GitHub API merges; CI remains the
authoritative boundary. A green pre-push is not validation, readiness, approval,
or proof that every CI step will pass.

**Harness coupling contract preflight**
(`.agents/hooks/check_harness_coupling.py`). This is a conditional adapter over
the two existing contract files named in Current Gates, not a new validation
rule. It runs in CI immediately before the full suite and in the local pre-push
selected-gate mirror. The trigger is deliberately broad across harness Python
because policy-module pins can be affected through imports and deliberately
narrow across non-Python data to the generated inventory snapshot. A 2026-07-15
sample of the latest 100 `ci` workflow runs found 96 completed runs and six
failures; three of the six failures were stale generated-inventory or
policy-module-pin coupling. No SHA in the sample both failed and later passed,
so blanket retry had no supporting evidence. The two contract files completed
in about 8.6 seconds locally versus about 79 seconds for the full harness suite.
This placement is the smallest complete response to the repeated fast coupling
class; other isolated failures remain visible in the authoritative full suite.


**Source-input hash freshness gate** (`.agents/hooks/check_source_input_hashes.py`,
EP-37). Diff-scoped, forward-only CI gate plus local pre-push mirror for the
Current Gates bullet above: list-style JSON `source_inputs[]` records with
repo-local `source_pointer` + `sha256` must match current file bytes when the
JSON artifact or referenced source changed. Born from PR #817: a Creator
Registry ledger merge changed the ledger hash while the YouTube metric seed's
source-input hash stayed stale, and full pytest caught it late. Extended
2026-07-10 to source-capture packet manifests: a JSON document with a
top-level `manifest_version` string has its top-level `preserved_files[]`
records (`relative_packet_path` + `sha256`) checked against current **raw
stored bytes**, with the path resolved against the manifest's own directory
(the manifests' `hash_basis: raw_stored_bytes`; `.gitattributes` pins
`**/source_captures/** -text`). Non-packet-local paths fail loud; nested
`preserved_files` blocks (review-input fixtures describing machine-local
packets outside the repo) are deliberately not matched. Gap surfaced by the
EP-15 build survey (PR #842): the packet-manifest shape was matched by
neither the `source_inputs[]` JSON gate nor the markdown pin-grammar gate.
Registered in `.github/workflows/ci.yml` and `.agents/hooks/pre_push_guard.py`;
`--audit` and `--selftest` present. Provenance shape/freshness only — a green
run never proves semantic validity, completeness, readiness, source quality,
capture freshness, or metric validity.

**Handoff-pointer resolution gate** (`.agents/hooks/check_handoff_pointers.py`,
EP-36). Diff-scoped, forward-only CI gate for the Current Gates bullet above:
handoff-packet paths referenced in changed durable docs must resolve in the
same tree, or the pointer line must carry an explicit pin or exemption marker.
Born from repeated cold-agent resolution failures: packets authored on
unmerged lane branches — e.g. `docs/workflows/yt_shorts_grid_tier_assessment_handoff_v0.md`, reachable only on its authoring branch — were
referenced by filed courier/patch prompts that landed on `main`, so receiving
agents and delegated reviewers starting cold from `main` could not find them
(both the receiving agent and a delegated reviewer failed on that packet; the
`--audit` backlog at build time showed 17 unresolved pointers across at least
six distinct packets — surfaced, never gated). Because the gate runs on the
landing PR's tree, it mechanically enforces the merge-ordering rule without
needing to see lane starts. A write-time PostToolUse advisory was
intentionally NOT built: the defect is a merge-topology property (packet on a
different unmerged branch), invisible at the write boundary where the packet
usually exists in the author's own tree. Registered in
`.github/workflows/ci.yml`; `--selftest` present. Pointer shape only — a
green run never proves packet content, freshness, or pin truth.

**Prompt output-mode gate** (`.agents/hooks/check_prompt_output_mode.py`,
EP-11 shape subset). Diff-scoped, forward-only CI gate for the Output-mode
gate bullet (Prompt Orchestration Gates above): a changed prompt artifact
under `docs/prompts/**` (templates and READMEs excluded) must carry an
output-mode declaration naming at least one token from the closed set in
`.agents/workflow-overlay/prompt-orchestration.md` § Output Modes,
referencing that owner, never restating it. Build-time corpus measurement
falsified the literal "exactly one" substrate reading — the `output_mode:`
field shape is legitimately reused for receiver/reviewer/dispatch roles
within one prompt, and legitimate compound two-token values exist — so the
gate checks presence + token-in-set only, multi-declaration and multi-token
shapes are INFO (never gated), and the EP-11 classification row moved
SUBSTRATE→PARTIAL. Registered in `.github/workflows/ci.yml`; `--selftest`
present, including a token-drift assertion that parses the owning section.
Prompt contract shape is enforced at CI; no prompt advisory is registered on a
write boundary.

**Review-summary shape gate** (`.agents/hooks/check_review_summary.py`,
EP-10 born-green subset). Diff-scoped, forward-only CI gate for the
Review-summary shape gate bullet above (shape source
`.agents/workflow-overlay/communication-style.md`, referenced never
restated). Strict scope is deliberately the born-green subset: forbidden
process keys, `report_path` resolution, failed-write consistency, and
non-blank `recommendation`; full `recommendation` enum membership runs
`--audit`-only because delegated-review-patch lanes carry an extended
vocabulary `communication-style.md` never bound (measured on roughly 40% of
one recent week's real closeouts at build time) — the owner decided
(2026-07-10) to keep the narrowed gate as standing: the vocabulary stays
unbound, enum membership stays advisory, and re-widening is a future
doctrine change, not a checker default. Non-overlap:
retrieval-header, provenance, and fencing checks stay with
`check_review_output_provenance.py`. No write-time hook by design: review
outputs are frequently authored by other harnesses that never fire this
harness's hooks, so CI on the landing tree is the boundary. Registered in
`.github/workflows/ci.yml`; `--selftest` present.

**Hash-pin freshness gate** (`.agents/hooks/check_hash_pin_freshness.py`,
EP-15 freshness subset). Diff-scoped, forward-only CI gate plus local
pre-push mirror for the Hash-pin freshness gate bullet above. Build-time
corpus survey found six markdown sha256 grammars; only the two freshness
grammars are parsed — labeled `path:` + `sha256:` bullet pairs (the
skill-adoption source pins) and `source_captures/**/receipt.md`
preserved-file bullets — while package-manifest tables, source-read
ledgers, and the external-path bootstrap-record table are provenance
records and deliberately unparsed (gating them would false-block
working-as-intended history). Hashes compare CRLF-normalized and
case-insensitive; the two skill-adoption pins were re-pinned in the same
change from raw-CRLF Get-FileHash values (which would pass on CRLF checkouts
and permanently fail on LF CI checkouts) to the normalized convention. The
markdown sibling of the EP-37 JSON gate. Registered in
`.github/workflows/ci.yml` and `.agents/hooks/pre_push_guard.py`;
`--selftest` present.

**Shared-helper duplication gate**
(`.agents/hooks/check_shared_helper_duplication.py`). Diff-scoped,
forward-only CI gate for the Shared-helper adoption gate bullet above. The
mechanical backstop for the
helper-adoption rule adopted by the 2026-07-16 helper-dedup lane (PRs
#988–#992): the wired checkers and harness modules had accumulated diverged
private copies of the same helpers, and the adopted rule — check the shared
home first, import it when it already has the helper, and keep a deliberately
divergent copy only with a one-line comment naming the delta — lived only in
the two README paragraphs where nothing mechanical could catch the next
private copy. Forward-only by design: only newly added def lines are gated;
the escape hatch is the rule's own delta-comment convention (`harness_utils`
/ `_hooklib` / `helper-delta` in a comment on the def line or the line
above). `guard_protected_actions.py` stays excluded — its import-free
duplication is the documented deliberate exception in the `_hooklib.py`
docstring — as do `harness_utils.py`, `_hooklib.py`, and
`forseti-harness/tests/**`. Registered in `.github/workflows/ci.yml` only;
`--selftest` present. Its dormant `--hook` mode is not active wiring.
Adoption-rule shape only — a green run never proves imports are correct, a
kept divergence is justified, validation, or readiness.


## Future Gates

- Forseti independence dry run: UNKNOWN - requires owner input.
- Product/domain validation: UNKNOWN - requires owner input.
- Runtime or integration validation: UNKNOWN - requires owner input.
