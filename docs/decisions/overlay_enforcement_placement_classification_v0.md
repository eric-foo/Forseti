# Overlay Enforcement-Placement Classification v0

```yaml
retrieval_header_version: 1
artifact_role: Orca decision record
scope: >
  Prepare-only classification of the Orca overlay's resident rules by enforcement
  placement (deterministic substrate vs genuine judgment), with proposed substrate
  for the code-enforceable rules and a proposed (not bound) overlay pointer to the
  shared enforcement-placement principle. Builds, installs, and authorizes nothing.
use_when:
  - Deciding which overlay rules to harden in a deterministic substrate vs keep resident.
  - Scoping owner authorization to build a governance hook / test / schema / lint.
  - Later binding the shared enforcement-placement doctrine to Orca (separate task).
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/safety-rules.md        # owner gate for building any substrate
  - .agents/workflow-overlay/validation-gates.md    # current (resident) gate set
  - .agents/workflow-overlay/retrieval-metadata.md  # the jb-exemplar domain (header rule)
stale_if:
  - A governance substrate is actually built/installed (proposed rows become moved).
  - A cross-repo shared home for the enforcement-placement doctrine is created (the Step-4 pointer can then bind).
  - The overlay's resident rules materially change.
```

## Status

Prepare-only **proposal + classification**. It inventories and classifies rules that already exist in the overlay and proposes where each could be enforced. It **builds nothing, installs nothing, wires nothing into `.claude/settings.json`, edits no overlay-authority file, and authorizes no implementation.** It is **not a doctrine change** (no durable rule was edited; this is a classification of existing rules), so **no `direction_change_propagation` receipt is owed**. No readiness, validation, or proof claim is made. Building any proposed substrate is **owner-gated** under `.agents/workflow-overlay/safety-rules.md`.

Scope guard: this is the **enforcement-placement step only**. Binding the shared distillation doctrine to Orca is a separate later task and is explicitly out of scope here (see § Step 4).

## Update — 2026-07-17: interactive hook subtraction and EP-04 relocation

Forseti now uses the lowest-cost boundary that still catches each named defect
before irreversible harm. Interactive hooks are reserved for prevention:
Claude retains the 10-second protected-action guard and one 5-second
SessionStart state read; Codex retains only its 10-second protected-action
adapter. Claude `PostToolUse` and `Stop`, Codex `PostToolUse`, and the SCI commit
reminder are removed. The SessionStart read now launches one internally
2-second-capped Git status process and reports `UNKNOWN` on Git failure instead
of false-clean state.

EP-04 artifact placement moves to CI as
`.agents/hooks/check_placement.py --changed --strict`. It uses the exact CI event
base, checks A/M/C paths and rename destinations, ignores deletions, performs
the lightweight map↔top-level-tree freshness check, and fails visibly when the
strict diff or map is unavailable. It is not added to pre-push. Retained checker
`--hook` modes are dormant compatibility only. The four true hook-only scripts
(`remind_sci.py`, `check_prompt_provenance.py`, `check_shared_files_dirty.py`,
`check_token_burn.py`) are retired rather than consolidated into a dispatcher.
This subtraction mitigates hook amplification; it does not claim to repair the
Codex Desktop sandbox transport defect.

## Update — 2026-07-16: EP-38 managed-receiver commission shell built

EP-38 classifies the deterministic shell of the already-landed Implementation
Commission Receiver-Creation Clause as **PARTIAL**. The trigger is limited to a
prompt's own declared `implementation-authorized`, `codex_managed_worktree`, and
not-yet-verified binding fields. Exact single-use authorization tokens, binding
field equality, absence from read-only commissions, prohibited positive manual
or repeated creation directives, and typed source-load failure are substrate
shape. Whether those declarations truthfully classify the act, whether source
loading really failed, and whether a future receiver is correctly rooted,
writable, current, or writer-isolated remain resident/runtime judgment.

The build extends the existing diff-scoped prompt checker
`.agents/hooks/check_prompt_output_mode.py` and adds a gating `--validate-stdin`
mode for frozen chat/courier bodies. It does not create the standalone checker,
registry, task API, or persisted receiver state prohibited by
`.agents/workflow-overlay/decision-routing.md`. The existing CI and pre-push
commands inherit the filed-prompt check without new wiring. Placement is not
authority: green proves only the parsed shell, never receiver validity,
dispatch, task count in the product runtime, source freshness, or readiness.

## Update — 2026-07-11: Batch 2 closeout-obligation placement decision (no build)

Batch 2 examined two independent consequential misses before choosing an
enforcement placement:

1. **WU-02 / PR #860 — review-economics receipt omitted.** The material review
   was CA-adjudicated, but its Batch 0 receipt was not filed. The valid counter
   remained at one until owner direction caused recovery in PR #863. Evidence:
   `docs/workflows/process_improvement_batch0/resident_rule_firing_audit_v0.md`
   and
   `docs/workflows/process_improvement_batch0/review_receipts/forseti_data_root_runner_enforcement_review_v0.json`.
2. **WU-03 / PR #866, clean replacement PR #873 — DCP accounting ambiguity.** The
   Batch 1 branch changed the doctrine index, repo map, and case ledger while
   its DCP recorded those
   files only under `downstream_surfaces_checked`. Delegated review recovered
   their local disposition; CA kept the clarity patch but rejected the
   reviewer's stronger universal partition inference. Evidence is pinned to
   PR #873, branch `codex/process-improvement-batch1-clean` at `df3df48d`
   (the original review commission is preserved on closed PR #866):
   `docs/review-outputs/adversarial-artifact-reviews/process_improvement_batch1_decision_gate_economics_pilot_delegated_adversarial_artifact_review_v0.md`
   and `docs/review-outputs/adversarial-artifact-reviews/process_improvement_batch1_decision_gate_economics_pilot_adjudication_v0.md`.
   PR #873 was open and unmerged at this decision's commission time; if it
   closes or its branch is deleted before merging, this citation becomes
   unresolvable from `main` and would need re-pinning to wherever the
   evidence lands.

```yaml
batch2_enforcement_placement:
  cynefin_regime: complicated
  scoping_gate: cleared
  substrate_build_gate: not_cleared
  comparison_level: consequential actor-carried closeout obligations
  shared_mechanical_predicate: not_proven
  current_decision: no_build_bounded_feasibility_probe
  stop_condition: >
    Stop before automation whenever the proposed check would infer receipt truth,
    doctrine-change status, DCP-list meaning, material-review status, or completed
    CA adjudication from self-asserted or unbound fields.
```

The events are independent enough to justify a placement decision: they occurred
in different work units, concerned different receipt types, and each required a
separate recovery action. They are not similar enough to justify one checker.
Their only established common class is an actor-carried closeout obligation.

### Placement decision

| Option | Decision | Basis |
| --- | --- | --- |
| Add another template, reminder, or resident copy | reject | The governing rules already existed; duplicating prose repeats the mechanism that missed. |
| Extend `.agents/hooks/check_dcp_receipt.py` strictly now, or add a non-gating `--audit`-only variant | reject for now | EP-09 and EP-29 bind shape to substrate and receipt truth to judgment. `source-of-truth.md` does not state the proposed invariant that every branch-changed downstream file must appear under `controlling_sources_updated`, so a strict check would overclaim. An audit-only heuristic could surface a candidate mismatch without deciding truth, but this evidence contains one DCP event and does not yet prove enough recurring decision value to justify another maintained surface. |
| Add a write-time hook | reject | Both events depend on closeout or commit-diff state; a second hook would duplicate the existing CI boundary and still invent semantic truth. |
| Record a no-build decision and probe feasibility | keep | It preserves the evidence and exact reversal conditions without greenwashing an unbound judgment as deterministic enforcement. |

The bounded feasibility probe is read-only: determine whether a future durable
review/adjudication record can expose a provenance-bound completion marker from
which the temporary Batch 0 receipt could be derived, and whether the DCP owner
can bind a mechanically decidable list invariant without false positives. This
record does not create that marker or invariant.

Re-open substrate implementation only when at least one of these becomes true:

- an owning source binds a deterministic DCP disposition invariant that can be
  checked against the commit diff without deciding whether an edit is
  doctrine-changing or whether a semantic check was truthful; or
- material-review completion and CA adjudication gain an independently
  verifiable durable marker from which a temporary measurement receipt can be
  derived without self-certification. No current source names an owning
  surface for creating that marker; establishing one is itself a future
  decision, not assumed here.

If the first condition clears, extend the existing diff-scoped DCP checker
rather than add a competing hook. If the second clears, prefer derivation at
adjudication closeout over another reminder.

This update classifies observed evidence and builds or binds nothing. It changes
no overlay authority, validation gate, hook, CI workflow, template, review
requirement, or notification rule; no Direction Change Propagation receipt is
owed. It is not proof that resident rules generally fail, not receipt-truth
validation, not readiness, and not authorization for automation.

## Update — 2026-07-10: EP-10 + EP-11 + EP-15 built and wired (receipt-shape gate wave)

Three rows from the original EP-01..EP-31 table — EP-10, EP-11, EP-15 — built
and wired under explicit current-turn owner authorization (the approved
"receipt-shape gate wave" plan, 2026-07-10). All three follow the EP-36/EP-37
house pattern: diff-scoped forward-only checkers with `--strict` CI mode,
`--audit` advisory backlog (never gated), `--selftest`,
`--force-internal-error`, infra-gap fail-open, GATE FAIL on internal error in
gating modes.

- **EP-11 (`check_prompt_output_mode.py`) — classification CORRECTED:
  SUBSTRATE → PARTIAL.** Build-time corpus measurement falsified the row's
  literal "token-in-set ∧ count == 1" claim: the `output_mode:` field shape
  is legitimately reused for receiver/reviewer/dispatch roles within one
  prompt (13/370 corpus files carry two keys), and legitimate compound
  two-token values exist ("file-write (this artifact) + paste-ready-chat
  (courier prompt)"). The checkable shell is declaration presence plus
  at-least-one closed-set token in changed `docs/prompts/**` files
  (templates/READMEs excluded); exactly-one and role-scoping stay resident.
  Born-green: 8/10 most-recently-changed prompt files pass; whole-corpus
  `--audit` at build: 357 in-scope files — 242 pass, 97 no-declaration, 18
  legacy/no-valid-token (forward-only backlog, surfaced, never gated).
  Selftest 24/24, including a token-drift assertion parsing the owning
  prompt-orchestration § Output Modes section. The EP-11 table row below is
  amended in place and moved out of the "clear SUBSTRATE wins" list.
- **EP-10 (`check_review_summary.py`) — built as the born-green subset.**
  Strict: the six forbidden process keys, `report_path` resolution, the
  bound failed-write shape, non-blank `recommendation`. NOT strict: the
  5-value `recommendation` enum — measured ~40% failure across one recent
  week's real closeouts (an undocumented extended vocabulary in
  delegated-review-patch lanes), so enum membership runs `--audit`-only.
  **Owner decision 2026-07-10 (follow-up, same day): the narrowed gate is
  accepted as the standing shape.** Enum membership stays `--audit`-only
  advisory; the delegated-review-patch extended vocabulary stays unbound
  (no `communication-style.md` widening); the 5-value enum remains the
  canonical target vocabulary for new review summaries, with conformance
  resident judgment — the acceptance covers enforcement placement, it does
  not endorse drift. Drift is tracked by `--audit` (23 advisories at
  decision time, re-measured at decision), never gated. Re-opening later is
  cheap: bind a widened vocabulary in `communication-style.md` (DCP owed)
  and flip the checker's enum sub-check from drift-advisory to a strict
  finding. The EP-10 table row below is annotated in place; it stays a
  SUBSTRATE win for its strict core, unlike EP-11's falsified-claim
  correction. Build `--audit`: 306 in-scope files, 0 strict findings
  (whole-corpus green), 23 template blocks skipped, 23 enum-drift
  advisories. Selftest 44/44. One corpus-driven refinement:
  `report_path: null` (YAML null, "no path") is recognized rather than read
  as a dead path. Non-overlap: header/provenance/fencing stays with
  `check_review_output_provenance.py`.
- **EP-15 (`check_hash_pin_freshness.py`) — built for the freshness families
  only.** Corpus survey found six markdown sha256 grammars; only the two
  freshness grammars are parsed: labeled `path:` + `sha256:` bullet pairs
  (the skill-adoption source pins) and `source_captures/**/receipt.md`
  preserved-file bullets. Manifest tables, source-read ledgers, and the
  external-path bootstrap-record table are provenance records and
  deliberately unparsed (gating them would false-block working-as-intended
  history). Hashes compare CRLF-normalized, case-insensitive. Shipping
  prerequisite landed in the same change: the two `skill-adoption.md` pins
  were raw-CRLF Get-FileHash values — passing on CRLF checkouts, permanently
  failing on LF CI checkouts — re-pinned to the normalized convention. Build
  `--audit`: 1733 md files scanned, 266 pins (2 grammar-1 + 264 grammar-2),
  266 pass, 0 missing, 0 mismatch, 4 non-repo-local pointers skipped.
  Selftest 31/31. Mirrored into `pre_push_guard.py` (EP-37 parity). The
  markdown sibling of EP-37 — file-extension partition, zero overlap.
- Wired: three `ci.yml` steps (single-line `run:` format, discoverable by
  the PR #815 local doc-gate runner), three
  `test_hook_internal_error_gating.py` CASES rows, the `pre_push_guard.py`
  mirror (EP-15 only), hooks README rows, repo-map Active Hooks notes, and
  validation-gates Current Gates bullets + Enforcement Placement registry +
  inline DCP receipt (the two prior inline receipts rotated verbatim to
  `docs/decisions/dcp_receipts_archive_v0.md` under the ≤2-inline rule).

This trips `stale_if` (further substrates built). PLACEMENT IS NOT AUTHORITY:
green runs are shape/freshness only — never validation, readiness, review
quality, prompt quality, or approval.

## Update — 2026-07-10: EP-37 extended to source-capture packet preserved_files[]

Not a new EP handle — a matched-shape extension of the already-built EP-37
substrate, landed under the current-turn owner instruction to close the
`preserved_files[]` coverage gap.

- **Gap provenance:** the EP-15 build survey (PR #842, open at authoring time,
  branch `claude/sub-agent-spawning-plan-2dc064`) and that PR's owner-flag
  list: source-capture packet manifests at
  `forseti-harness/cases/**/source_captures/**/manifest.json` record preserved
  raw files under `preserved_files[]` (`relative_packet_path` + `sha256`), a
  shape matched by neither EP-37 (JSON `source_inputs[]` with
  `source_pointer`) nor EP-15 (markdown pin grammars only; the sibling
  `receipt.md` bullets ARE covered there).
- **What it enforces now:** a JSON document with a top-level
  `manifest_version` string has its top-level `preserved_files[]` records
  checked: `relative_packet_path` resolves against the manifest's own
  directory and the recorded `sha256` must match current **raw stored bytes**
  (the manifests' `hash_basis: raw_stored_bytes`; `.gitattributes` pins
  `**/source_captures/** -text`) — unlike the CRLF-normalized `source_inputs[]`
  basis. Non-packet-local paths (absolute, drive, parent traversal) fail loud
  as `preserved_file_path_not_packet_local`. Nested `preserved_files` blocks
  (review-input fixtures describing machine-local packets outside the repo)
  are deliberately not matched — they would false-positive as missing.
- **Born-green measurement first:** `--audit` green over all 281 records
  (17 `source_inputs[]` + 264 `preserved_files[]` across 88 manifests; 0
  missing, 0 raw-basis mismatches). Live probes: one flipped byte in a
  preserved `.bin` → `preserved_file_hash_mismatch` in `--audit`, and the same
  drift committed on a temp branch → `--strict` exit 1 via the real diff
  scope.
- **Wiring unchanged:** rides EP-37's existing `.github/workflows/ci.yml`
  step, `.agents/hooks/pre_push_guard.py` mirror, and
  `test_hook_internal_error_gating.py` CASES row; selftest grown to 32 cases.

Same classification and boundary as EP-37 (PARTIAL/SUBSTRATE shell). PLACEMENT
IS NOT AUTHORITY: a green run is provenance hash freshness, never archive
completeness, source-state truth, capture freshness, validation, or readiness.
The DCP receipt lives in `validation-gates.md`.

## Update — 2026-07-10: EP-37 (source-input hash freshness gate) built and wired

A new Enforcement Placement handle — **EP-37, beyond the EP-01..EP-36 set** —
built and wired under explicit current-turn owner authorization to reduce the
chance that future agents repeat PR #817's stale source-input hash miss.

- **What it enforces:** repo-local JSON list-style `source_inputs[]` records
  that carry `source_pointer` + `sha256` must match current file bytes when the
  artifact or referenced source changed. Rule owner:
  `.agents/workflow-overlay/validation-gates.md` (Source-input hash freshness
  gate, with inline DCP receipt); the checker references it.
- **Provenance:** in PR #817, a Creator Registry ledger merge changed the
  source ledger hash while the YouTube metric seed still carried the old
  `source_inputs[].sha256`; full pytest caught it late. The defect class is
  deterministic hash drift, not agent judgment.
- **Classification: PARTIAL/SUBSTRATE shell.** JSON discovery, repo-local
  pointer filtering, diff scoping, file existence, and CRLF-normalized SHA-256
  comparison are SUBSTRATE (diff-scoped, forward-only). The over-edges stay
  resident: whether the generated artifact is semantically current or complete,
  whether the cited source is high quality, whether capture is fresh, and
  whether any metric is valid. PLACEMENT IS NOT AUTHORITY: a green run is
  provenance freshness, never validation or readiness.
- **Built:** `.agents/hooks/check_source_input_hashes.py` (`--strict` CI gate,
  `--check`, `--audit`, `--selftest`, `--force-internal-error`; infra-gap
  fail-open, GATE FAIL on internal error in gating modes). Wired:
  `.github/workflows/ci.yml` step, `.agents/hooks/pre_push_guard.py` local
  mirror, and `test_hook_internal_error_gating.py` CASES row.

This trips `stale_if` (a further substrate built). The DCP receipt lives in
`validation-gates.md`. Not validation, readiness, source quality, capture
freshness, metric validity, or approval.

## Update — 2026-07-03: EP-36 (handoff-pointer resolution gate) built and wired

A new Enforcement Placement handle — **EP-36, beyond the EP-01..EP-35 set** —
built and wired under explicit current-turn owner authorization ("Design and
land the smallest complete enforcement", the handoff-resolution turn).

- **What it enforces:** a changed durable `.md` file must not reference a
  handoff-packet path (`docs/workflows/*handoff*.md`, `docs/prompts/handoffs/*.md`)
  that does not resolve in the same tree, unless the pointer line carries an
  explicit resolution pin (`branch` / `PR #<n>` / `origin/<ref>` vocabulary) or
  an exemption marker. Rule owner:
  `.agents/workflow-overlay/validation-gates.md` (Handoff-pointer resolution
  gate, with inline DCP receipt); the checker references it.
- **Provenance:** handoff packets referenced by courier prompts twice failed
  cold-agent resolution because they lived only on unmerged authoring branches
  (observed: `docs/workflows/yt_shorts_grid_tier_assessment_handoff_v0.md`, reachable only on its authoring branch
  — both the receiving agent and a delegated reviewer failed to find it from
  `main`). A build-time corpus measurement showed the class is systemic:
  `--audit` found 17 unresolved handoff-family pointers across at least six
  distinct packets (forward-only backlog, surfaced, never gated), while the
  broader all-paths rot backlog (~883 unresolved references in filed prompts)
  ruled out any whole-corpus gate.
- **Classification: PARTIAL.** Pointer extraction + in-tree resolution +
  pin/exemption vocabulary presence are SUBSTRATE (diff-scoped, forward-only).
  The over-edges stay resident: whether a pinned branch still exists, whether
  packet content is current, whether the cited packet was the right source,
  and couriers that never land in the repo (chat bodies, PR comments,
  `docs/_inbox/` scratch — governed by prompt-orchestration.md). Referenced
  output DESTINATIONS (e.g. `docs/review-outputs/**` report paths) are
  deliberately out of the checked family: they legitimately do not exist at
  authoring time, so gating them would false-block (measured: nearly all 35
  review-io unresolved references were destinations). PLACEMENT IS NOT
  AUTHORITY: a green run is pointer shape, never proof the packet is fresh or
  correct.
- **Built:** `.agents/hooks/check_handoff_pointers.py` (`--strict` CI gate,
  `--check`, `--audit`, `--selftest`, `--force-internal-error`; infra-gap
  fail-open, GATE FAIL on internal error in gating modes, mirroring
  `check_review_routing.py`). Wired: `.github/workflows/ci.yml` step +
  `test_hook_internal_error_gating.py` CASES row. A write-time PostToolUse
  advisory was intentionally NOT built: the defect is a merge-topology
  property (packet on a different unmerged branch), invisible at the write
  boundary where the packet usually exists in the author's own tree.

This trips `stale_if` (a further substrate built). The DCP receipt lives in
`validation-gates.md` (an overlay rule was added there — like EP-35, this one
IS a doctrine change). Not validation, readiness, or approval.

## Update — 2026-07-03: strict doc gates mirrored into the local pre-push guard

Not a new EP handle — a placement extension of already-built substrates
(`header_index.py --strict`, `check_review_routing.py --strict`,
`check_map_links.py --strict`), mirrored into
`.agents/hooks/pre_push_guard.py` (the `.githooks/pre-push` adapter policy)
under explicit current-turn owner authorization (the PR #613 red-round
follow-up turn).

- **What changed:** for a push whose update lines pass the guard's existing
  safety checks, the guard now runs the three strict doc gates CI runs
  (diff-scoped base `origin/main`, same as CI) and blocks the push on any
  nonzero, unlaunchable, or timed-out gate (the GATE FAIL bucket); the
  checkers' own infra-gap fail-opens (e.g. unresolvable `origin/main`) are
  unchanged, so CI stays the backstop for infra gaps.
- **Provenance:** PR #613 — a delegated-review report under
  `docs/review-outputs/**` missing its retrieval header reached CI and cost a
  red round. The write-time advisory (the EP-06 hook, wired and verified
  firing on exactly that miss shape this session) is non-blocking and
  harness-local, so the miss class needed a harness-agnostic local boundary
  before CI. Named residual: the Codex PostToolUse wiring does not include the
  EP-06 header advisory (and the checker does not parse `apply_patch`
  payloads), so Codex-side writes see no write-time reminder; they are caught
  by this pre-push mirror and CI.
- **Verified this session:** `pre_push_guard.py --selftest` 8/8 PASS (5
  pre-existing update-line cases + 3 injected-runner gate cases); live allow
  fire (clean lane payload → 3 gates run, exit 0, ~5s combined) and live block
  fire (temp commit with a headerless `docs/review-outputs/` probe → exit 1
  carrying the `header_index` MISSING-HEADER finding).
- No overlay rule changed (the validation-gates "Enforcement Placement"
  section gained registry documentation only); placement is not authority, so
  no `direction_change_propagation` receipt is owed. Bypassable with
  `--no-verify`; not validation, readiness, or approval.

## Update — 2026-07-02: EP-35 (review-routing disposition gate) built and wired

A new Enforcement Placement handle — **EP-35, beyond the EP-01..EP-34 set** —
built and wired under explicit current-turn owner authorization ("Do the B and
C", the fused-lane audit turn).

- **What it enforces:** a change touching code roots (`orca-harness/`,
  `.agents/hooks/`) must carry its review disposition — a review artifact added
  under `docs/prompts/reviews/` / `docs/review-outputs/` in the same change, or
  a shape-valid `review_routing_status: routed <existing path> | blocked --
  <reason> | not_needed -- <reason>` line in the change's commit messages. Rule
  owner: `.agents/workflow-overlay/validation-gates.md` (Review-routing
  disposition gate, with inline DCP receipt); the checker references it.
- **Provenance:** the 2026-07-02 fused-lane audit found only ~2 of 8 assessable
  fused implementation lanes filed their carried delegated-review handoff
  same-turn; four claimed it in commit prose without filing it; the
  `review_routing_status` closeout field lived only in chat, so nothing durable
  was checkable. The 06-17 prose hardening of the fused skill did not hold —
  enforcement moves to a commit-visible substrate. `--audit` at build time:
  51 of 67 code-root landings in the trailing 120 first-parent main commits
  carried no disposition (forward-only backlog, never gated).
- **Classification: PARTIAL.** Disposition presence + token shape + `routed`
  path existence are SUBSTRATE (diff-scoped, forward-only). The truth of a
  `not_needed`/`blocked` reason, the quality of a filed review, and — the
  over-edge — *whether review should have been recommended at all* stay
  resident judgment (the fused/scoping/review contracts). PLACEMENT IS NOT
  AUTHORITY: a green run is disposition shape, never proof a review happened
  or was sufficient.
- **Built:** `.agents/hooks/check_review_routing.py` (`--strict` CI gate,
  `--report`/`--check`, `--commit-msg` local advisory, `--audit`, `--selftest`;
  fail-open only on infra gaps, mirroring `check_dcp_receipt.py`). Wired:
  `.github/workflows/ci.yml` step + `.githooks/commit-msg` advisory line.
  Verified this session: `--selftest` 21/21 PASS; `--audit --limit 120`
  reproduced the audit findings (e.g. PR #577 flagged; PRs #575/#555, which
  filed review artifacts, pass); `--strict` OK on the build lane itself.
- **Companion (out of Orca scope):** the fused skill closeout edit (rendering
  default-authorized; durable stamp obligation) is user-level skill source
  (`~/.claude/skills/fused/SKILL.md`), protected from agent edit; the owner
  applies it separately.

This trips `stale_if` (a further substrate built). The DCP receipt lives in
`validation-gates.md` (an overlay rule was added there — unlike the EP-06/32/04
builds, this one IS a doctrine change). Not validation, readiness, or approval.

## Update — 2026-06-28: EP-34 (session HEAD-drift guard) considered → kept resident (premise verified-false; owner-declined the stateful version)

A new Enforcement Placement handle — **EP-34, beyond the EP-01..EP-33 set** — recorded as
**considered and NOT built.** Proposed this session as a `PreToolUse` warn when the worktree
HEAD has drifted since session start, to harden the recurring confirm-don't-trust freshness
miss (a stale session snapshot let a concurrent lane-rewrite go unnoticed before a commit).

- **A pre-build assumption gate found the premise false.** The guard was scoped to compare the
  current HEAD against the session-start snapshot from `session_context_capsule.py`. But that
  hook **prints** HEAD to stdout and **persists nothing** (`run_hook` -> `print(gather(...))`; no
  file write), and a `PreToolUse` hook cannot read session context. There is **no stored
  session-start HEAD** for a write-time guard to read — the cheap mechanical proxy the proposal
  assumed does not exist (the canonical "reference computed in memory and discarded" failure).
- **Classification: JUDGMENT (kept resident).** Coding it would require the guard to **own** a
  persisted per-session HEAD baseline (a state file written at SessionStart, read at `PreToolUse`,
  plus resume/compact re-fire and cross-worktree staleness handling) — standing state inside a
  currently-stateless, fail-open governance layer. Per **PLACEMENT IS NOT AUTHORITY** and the
  mini-god-tier line, that stateful substrate is the rejected maximal shape, not a free
  always-fires check; the rule stays resident.
- **Owner decision (2026-06-28): not worth the lock-in — keep as doctrine.** **Named residual:**
  no coded HEAD-drift guard; *re-verify HEAD before a write/commit/push* remains a judgment rule
  (confirm-don't-trust), and the capsule already re-emits HEAD on resume/compact. **Revisit
  trigger:** if stale-HEAD / concurrent-edit damage recurs materially, reconsider a stateful
  version (a session-keyed HEAD state file, or a "last HEAD I acted on" guard).
- Like EP-33 (deferred) and EP-02 (declined), this records a *not-built* decision: no overlay
  rule changed, placement is not authority, so **no `direction_change_propagation` receipt is
  owed.** Not validation, readiness, or approval.

## Update — 2026-06-25: "zero governance substrate" finding superseded; EP-07 + EP-09 built; live-registry pointer

This record's **§ "Method and the load-bearing finding" claim that "Orca has
zero governance substrate today" is STALE and superseded.** Since it was written,
a substantial deterministic substrate was built and wired. A census this session,
cross-checked against `.claude/settings.json`, `.github/workflows/ci.yml`, and the
repo map's "Active Hooks" note, observed:

- **9 wired Claude Code hooks** (`.claude/settings.json`): PreToolUse
  `guard_protected_actions.py` (EP-01/03, the one blocking guard) + `remind_sci.py`;
  PostToolUse `check_retrieval_header.py` (EP-06/07), `check_repo_map_freshness.py`
  (EP-32), `check_placement.py` (EP-04), `check_prompt_provenance.py`; Stop
  `check_shared_files_dirty.py` + `check_token_burn.py`; SessionStart
  `session_context_capsule.py`.
- **7 governance `--strict` CI gates** (`.github/workflows/ci.yml`):
  `check_map_links`, `header_index`, `check_ontology_ssot`,
  `check_ontology_tag_validity`, `check_ontology_drift`, `check_deletion_evidence`,
  and (new this update) `check_dcp_receipt`; plus the `orca-harness` `pytest`
  contract suite (~18 `tests/contract/` governance tests, e.g. the no-LLM-import
  and no-runtime-import boundary bans).

So the "the moved column is empty by construction" framing no longer holds:
several SUBSTRATE/PARTIAL rows are now built. The **EP-01..EP-33 table below stays
the point-in-time inventory it declares itself to be — it is not the live
registry.** The authoritative current registry is `.claude/settings.json` +
`.github/workflows/ci.yml` + the repo map's "Active Hooks" note + validation-gates
"Enforcement Placement".

Built this update (owner-authorized: the "rule-change form checker" + "upgrade the
header checker" picks):

- **EP-09 (shape subset) — `.agents/hooks/check_dcp_receipt.py`**: a diff-scoped,
  forward-only CI gate (sibling to the deletion-evidence gate) validating the
  SHAPE of any real `direction_change_propagation` receipt or `_blocker` in
  changed `.md` files — required keys, the trigger vocabulary, non-empty
  `non_claims`. It does NOT decide doctrine-ness (so it never requires a receipt
  to be *present* — the EP-09 over-edge stays resident) and never asserts a
  surface was truly checked; contract templates and note-markers are skipped; the
  inline-cap / archive-pointer / no-standalone-files rules are intentionally NOT
  gated (not born-green — several controlling files already hold >2 inline
  receipts). A `--audit` pass surfaced a small genuine forward-only backlog
  (~7 files: an invalid `trigger` such as `implementation_boundary`, a missing
  `non_claims`/`controlling_sources_updated`, or a YAML-quoting bug) — left for
  forward-only cleanup, flagged when those files are next touched, not fixed here.
- **EP-07 (forbidden-field subset, previously deferred) —
  `.agents/hooks/check_retrieval_header.py`**: the shared header predicate now
  also rejects status-leak header keys (approval / validation / readiness /
  lifecycle / deployment / install / resolver / publication / source-of-truth),
  flowing through both the write-time `--hook` and the `header_index --strict` CI
  gate. Born-green. `edit_permission` / `verdict` / `status` are intentionally
  allowed (review and prompt frontmatter use them). The `use_when` 1–3 count and
  a closed allowed-key set were assessed and intentionally NOT enforced: the
  corpus mixes retrieval-header fields with required review/prompt-provenance
  frontmatter in one block, so neither is born-green.

This is built substrate (advisory + CI tooling), not a doctrine change — no
overlay rule changed and placement is not authority — so no
`direction_change_propagation` receipt is owed (consistent with the
EP-06/EP-32/EP-04 builds below). Not validation, readiness, or approval.

## Update — 2026-06-09: EP-06 substrate built and wired

The retrieval-header substrate proposed here (EP-06) has since been
built and wired under explicit current-turn owner authorization (the
`safety-rules.md` owner gate named in § Owner gate):

- checker: `.agents/hooks/check_retrieval_header.py` — advisory + `--strict`
  CI/commit mode, forward-only, references `retrieval-metadata.md`; **EP-06
  presence/shape only** (EP-07 forbidden-field scan deferred);
- hook: a `PostToolUse` (`Write|Edit`) entry in `.claude/settings.json`;
- doctrine: a thin Enforcement Placement principle in
  `.agents/workflow-overlay/validation-gates.md` (cross-referenced from
  `decision-routing.md`), with discoverability + reinstall in the repo map's
  "Active Hooks" note.

This trips the `stale_if` "a governance substrate is actually built/installed":
EP-06 is now built; the remaining rows stay proposals, each still owner-gated.
See the `direction_change_propagation` receipt in
`.agents/workflow-overlay/source-of-truth.md`. This update adds no new claim;
the substrate is advisory tooling, not validation, readiness, or approval.

## Update — 2026-06-09: EP-01 + EP-03 floor built (config, no script)

The smallest-complete safety floor proposed here (EP-01 protected paths, EP-03
git lifecycle) is now built under explicit current-turn owner authorization, as
Claude Code `permissions` rules — deliberately config, not a script (the
bad-minimizing form):

- **`ask` — git lifecycle** (`git push`/`commit`/`remote`, `gh pr`,
  `git reset --hard`, `git clean`) for both the `Bash` and `PowerShell` tools,
  shared/tracked in `.claude/settings.json`. The approval prompt is the
  authorization (`safety-rules.md` "...unless explicitly authorized").
- **`deny` — protected paths** (writes/edits to `agent-workflow`, `jb*`,
  `~/.codex/{plugins,skills}`, `~/.claude/{plugins,skills}`, `~/.agents/skills`),
  machine-local in `.claude/settings.local.json` (machine-specific absolute
  paths; a fresh clone re-adds its own).
- **EP-02 deliberately excluded** from the floor (impl-dir blocking would
  false-block legitimate `orca-harness/` work; lower value).
- Discoverability: the repo map "Active Hooks" note was extended. Authority:
  `safety-rules.md` + validation-gates "Enforcement Placement".

This trips `stale_if` "a governance substrate is actually built/installed":
EP-01 and EP-03 are now built; the remaining rows stay proposals. **No new
doctrine** (no overlay rule changed; placement is not authority —
`safety-rules.md` already carried these rules and validation-gates already
carries the principle), so no new `direction_change_propagation` receipt is
owed. **Not yet live-verified:** Claude Code loads permissions at session start,
so the floor activates only after a restart, and PowerShell-tool matching is per
the Claude Code permissions reference, not live-fired in this session. Config
tooling, not validation, readiness, or approval.

## Update — 2026-06-09: EP-01 + EP-03 also enforced by a PreToolUse hook (auto-mode)

Live verification of the config floor showed the `ask` rules are **inert in auto
/ bypass mode** (no human to prompt — the agent's own `git remote -v` ran with no
gate). So under explicit current-turn authorization, EP-01 + EP-03 are now also
enforced by a **`PreToolUse` hook** that fires in ALL permission modes:

- `.agents/hooks/guard_protected_actions.py` (matcher
  `Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit` in `.claude/settings.json`);
  exit-2 blocks protected-path writes (`agent-workflow`, `jb*`, user-level
  plugin/skill caches) and dangerous git (`push`, `reset --hard`, `clean`) via
  either shell. Narrow: `commit` and generic deletion are not blocked. Fails open
  on internal error; has `--selftest`.
- The config `ask`/`deny` rules stay as interactive-mode belt-and-suspenders; the
  hook is the primary, mode-independent enforcement.
- **Logic verified this session** (selftest 15/15; live `git push` payload → exit
  2, `git status` → exit 0). **Hook wiring goes live after a Claude Code restart**
  (hooks load at session start); per the Claude Code docs, PreToolUse hooks run
  and block even under auto / bypass mode.
- No overlay rule changed → still no doctrine change / no DCP receipt. Config and
  hook tooling, not validation, readiness, or approval.

## Update — 2026-06-09: EP-32 repo-map freshness substrate built and wired

A new Enforcement Placement substrate — **EP-32, a handle beyond the EP-01..EP-31
overlay-rule table above** — is now built and wired under explicit current-turn
owner authorization. Unlike EP-06 (a rule already classified in the table), EP-32
hardens a rule that was **not** part of this record's overlay-rule classification:
the **repo map's own `stale_if:` block** in `docs/workflows/orca_repo_map_v0.md`
(a navigation artifact's freshness property, not an overlay-authority rule). It is
assigned the next stable handle here for traceability and later owner gating; the
EP-01..EP-31 table is left unchanged as the point-in-time classification it
declares itself to be.

- checker: `.agents/hooks/check_repo_map_freshness.py` — advisory + `--strict`
  commit/CI gate, forward-only, fails open; reads the repo map **as its own spec**
  and references the map's `stale_if` as authority, never restating it;
- hook: a second `PostToolUse` (`Write|Edit`) entry in `.claude/settings.json`,
  beside the EP-06 retrieval-header hook;
- discoverability + reinstall + acknowledgment + recheck recipe: the repo map's
  "Active Hooks" note was extended.

**Classification (stated inline, since EP-32 had no prior table row): PARTIAL.**
The mechanically-detectable structural subset is SUBSTRATE — a new top-level area
(`stale_if` #1) and a new `orca-harness/` runner/adapter (#2) are high-precision
gate triggers; a `source-of-truth.md` edit (#5) is an advisory nudge only. The
judgment-shaped staleness — "a spine was materially reorganized" (#3) and "routing
doctrine changed" (#4) — stays **resident**, owned by the Doctrine Change
Propagation contract in `.agents/workflow-overlay/source-of-truth.md` (which
already lists the repo map as a downstream surface). Per **PLACEMENT IS NOT
AUTHORITY** (the EP-29 over-edge rule), the substrate enforces map **shape, never
the truth or completeness of any route** — a clean run is not proof the map is
complete. A legitimate non-map change is acknowledged by a `repo-map-ack:`
commit-message token or by the map's "do not enumerate" exclusion list; updating
the map or a consolidation submap in the same change also satisfies the gate.

This is a further substrate built under the already-tripped `stale_if` "a
governance substrate is actually built/installed" (first tripped by EP-06, then
EP-01/EP-03); the remaining proposed rows stay proposals, each still owner-gated.
**No new doctrine** (no overlay rule changed; the Enforcement Placement principle
in `validation-gates.md` is unchanged; placement is not authority), so **no new
`direction_change_propagation` receipt is owed by this record** — the build's
receipt already lives in `.agents/workflow-overlay/source-of-truth.md` (trigger
`workflow_authority`, related `validation_philosophy`). **Live-verified this
session:** the `PostToolUse` hook fired on an actual edit (the advisory `stale_if`
#5 nudge) and `--selftest` passes; the `--strict` commit gate is
wired-but-not-installed by design (gate-on-demand, mirroring EP-06). Advisory
tooling, not validation, readiness, or approval.

## Update — 2026-06-09: guard re-placed to gate `main` (the merge), not the lane push

A coherence fix to the EP-03 guard (handoff from the CI/dev-workflow lane,
adjudicated here — I own this surface). The guard had been blocking the
*reversible* act (lane-branch `git push`) but **not** the *irreversible* one
(`gh pr merge` → `main`, which lived only in the auto-mode-inert `ask` config —
shown this session when PR #9 merged unblocked). Re-placed so the hard block
lands on the main-change:

- **now blocks** (exit 2, both shells): `gh pr merge` (+ `gh api .../merge`),
  push to `main`, force-push, bare/ambiguous push, plus `reset --hard` / `clean`;
- **now allows** an explicit non-main, non-force lane push
  (`git push -u origin <lane>`) — per-lane PR flow in
  `docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md` (verified on
  `main`; its server-side merge gate is 403-blocked on this private/free repo, so
  this hook is the local stand-in);
- also fixed a false-positive: a *mention* of these phrases inside a quoted
  string / echo no longer blocks;
- design: the simple/string fork (no `gh` API call) — preserves the guard's
  fast / fail-open / no-network design; under the missing server gate, blocking
  all `gh pr merge` (human/authorized action lands the PR) is the safe reading.
- **Verified live**: guard already active (fired in auto mode, no restart);
  selftest 32/32; live `gh pr merge` → exit 2, `git push -u origin <lane>` → exit 0.
- **Flagged for owner:** the doctrine's literal interim wording is "lane
  *self*-merges when green"; this guard implements the stricter
  "human/authorized action lands to `main`" as a compensating control for the
  403-blocked server gate. If you intend agent self-merge-when-green, relax the
  `gh pr merge` block.

## Update — 2026-06-11: EP-04 substrate built (placement check) — hook wiring pending owner

The folder-allowlist substrate proposed in the EP-04 row is now built under
explicit current-turn owner authorization ("do all phases", the repo-structure
binding turn), following the EP-32 house pattern:

- checker: `.agents/hooks/check_placement.py` — advisory `--hook` (PostToolUse,
  always exit 0), `--strict` commit/CI gate (exit 1 on non-legacy violations,
  map<->tree inconsistency in either direction, or a missing/unparseable map —
  a missing spec must not read as a pass), `--check`, `--selftest`; fail-open
  on internal error in advisory paths; references authority, never restates it;
- rule source: `repo-structure.yaml` (the machine map; router only) — the
  checker hardcodes no homes or tolerances. The map's `legacy_tolerated` list
  carries the declared pre-move debt (flat `docs/product/*.md`,
  `orca-harness/**`) as WARN-only; a tolerance-breadth sanity guard rejects
  blanket globs so the tolerance cannot quietly become a fake pass;
- binding + parameters: `docs/decisions/forseti_repo_structure_binding_v0.md`
  (invariant core restated as Orca doctrine; product lanes; surface tiering);
  DCP receipt inline in `.agents/workflow-overlay/artifact-folders.md`;
- the EP-04 PARTIAL judgment edge stays resident: a new folder/lane is allowed
  only by a recorded decision, and the checker enforces placement SHAPE, never
  the truth, value, or authority of any artifact (PLACEMENT IS NOT AUTHORITY).

**Verified this session:** `--selftest` 16 cases + 6 fake-pass guards green
(one real bug caught and fixed during build: bare `fnmatch` let `*` cross `/`,
which would have silently tolerated lane subfolders under the flat-product
debt glob); live tree `--strict` exited 1 on the 3 root strays, then 0 after
their `docs/_inbox/` quarantine; `--hook` payload tests produced the WARN /
lane-nudge / silent behaviors. **NOT wired:** the `.claude/settings.json`
PostToolUse edit was permission-denied this session (self-modification
requires specific owner authorization), so the write-boundary hook is
build-complete but inactive; the registration snippet is in the repo map's
"Active Hooks" note and the Phase-2 runbook, and activation requires a session
restart after wiring. This trips `stale_if` (a further substrate built); the
remaining proposed rows stay proposals. Advisory tooling — not validation,
readiness, or approval.

## Update — 2026-06-09: EP-33 (secrets-in-plaintext write guard) proposed — deferred until production

A new Enforcement Placement substrate handle — **EP-33, beyond the EP-01..EP-32
set** — is recorded here as a **proposal only**, surfaced while assessing an
external Claude Code PreToolUse-guardrails write-up against this repo. Every
load-bearing recommendation in that write-up was already covered by EP-01/EP-03
(`guard_protected_actions.py`), EP-06 (`check_retrieval_header.py`), and EP-32
(`check_repo_map_freshness.py`); the **one** idea not covered anywhere in the
EP-01..EP-32 set was a secrets-in-plaintext write guard.

- **What it would be:** a `PreToolUse` content check on `Write`/`Edit` that
  blocks saving a high-confidence credential shape (e.g. `BEGIN … PRIVATE KEY`,
  `sk-…`/`ghp_…`/`AKIA…`-style tokens, `.env` assignments) and names a
  non-tracked destination instead — a sibling to `guard_protected_actions.py`,
  fail-open.
- **Classification: PARTIAL.** High-confidence shapes → substrate; "is this
  actually a secret vs a test fixture / example key?" stays resident judgment
  (PLACEMENT IS NOT AUTHORITY — a green scan is not proof no secret leaked).
- **Owner decision this turn: deferred until production.** Rationale: this is a
  docs/decisions/prompts repo not handling live credentials, so the base rate is
  low; the residual risk (lane-branch pushes are allowed and a pushed secret is
  effectively irreversible) was judged not worth the substrate yet. **Revisit
  trigger: heading into production.**

This does **not** trip the `stale_if` "a governance substrate is actually
built/installed": EP-33 is **proposed, not built** — nothing was authored,
wired, or installed. No overlay rule changed (placement is not authority), so
**no `direction_change_propagation` receipt is owed**. Not validation,
readiness, or approval; recording a deferred proposal, nothing more.

## Update — 2026-06-12: guard relaxed to CLEAN-gated agent self-merge (fail-closed + opt-in label)

A behavioral change to the EP-03 guard, **adjudicated and recorded here because
this record is the guard's owning surface** (the 2026-06-09 "guard re-placed"
update established that), under explicit owner authorization (proceed-with-
conditions, 2026-06-12). This **acts on the owner flag** raised in that earlier
update — *"if you intend agent self-merge-when-green, relax the gh pr merge
block."* The owner intends it, with conditions:

- The guard had **hard-blocked all** `gh pr merge` (the human landed every
  merge). It now **conditionally allows** a direct `gh pr merge <N>` self-merge
  **only** when a single repo-scoped `gh pr view` lookup confirms the PR is
  `mergeStateStatus == CLEAN`, every `statusCheckRollup` entry is completed-green,
  and it carries the opt-in `agent-automerge` label.
- **Fail-closed is the deliberate exception to the guard's fail-open default.**
  The merge-authorization path blocks (exit 2) on any lookup error, timeout
  (the `gh` call is self-limited to `GH_TIMEOUT=6s`, below the hook's own 10s
  budget, so the guard returns its own block before any harness timeout-kill —
  which the Claude Code docs do not specify as fail-open or fail-closed), JSON
  parse failure, non-CLEAN state, empty/non-green check set, missing label,
  missing/ambiguous PR number, the no-arg form, the `gh api .../merge` form, or a
  foreign `--repo`. The guard's outer fail-OPEN is preserved for the non-merge
  paths (a guard bug must not brick all of the agent's tools); only the merge
  path fails closed.
- The block message **always prints the repo-scoped manual command**
  (`gh pr merge <N> --squash --delete-branch --repo eric-foo/forseti`) so a human
  can land from any directory.
- **Classification: PARTIAL → still substrate-appropriate.** `mergeStateStatus`,
  check conclusions, and label presence are deterministic API shape the guard can
  verify at the tool boundary; the *judgment* of removing the human from the
  irreversible step is the owner's, exercised once here (PLACEMENT IS NOT
  AUTHORITY — the guard checks the mergeability *shape*, it does not assert the
  diff is correct). **EP-01 and EP-03 push-to-main / force-push / destructive-
  clean are UNCHANGED.**
- **Why CLEAN + green + label, not bare CLEAN:** branch protection is 403-blocked,
  so no check is *required* and an empty/early check set can read CLEAN before CI
  starts; requiring the rollup present-and-green plus an explicit opt-in label
  closes that false-green race and keeps self-merge deliberate and auditable.

**Verified this session:** `--selftest` 46/46 PASS (exit 0), including the new
allow/fail-closed merge cases and all pre-existing EP-01/EP-03 cases; live
payload render of the block message + manual command (exit 2) and a benign allow
(exit 0). The doctrine carries the `direction_change_propagation` receipt and the
downstream-surface reconciliation (AGENTS.md kernel clause, `safety-rules.md`,
`.claude/settings.json` scope); **a human lands the PR**, because the pre-
amendment guard blocks the agent from self-merging its own guard-change PR. This
record's EP-01..EP-33 classification table is the point-in-time inventory it
declares itself to be and is unchanged; this update records a behavior change to
an already-built substrate, not a new EP handle. Advisory record — not
validation, readiness, or approval.

## Problem (Orca-bound)

The Orca overlay (`.agents/workflow-overlay/`, the always-on governance layer loaded for project work) carries many rules as **resident model instructions** that a deterministic substrate could enforce at a boundary instead. Each such rule (a) fires only when the model attends to it — unreliable — and (b) spends a slot of the scarce, reliability-bounded always-on instruction budget that a genuinely judgment-based rule needs. The recurring miss is reaching for a "be careful to…" instruction by reflex when a hook, gate, schema, or test could enforce the rule by construction.

## Goal

The overlay enforces, in a deterministic substrate at a boundary, every rule that can be — reserving the resident instruction budget for genuinely judgment-based rules. Concretely: each overlay rule classified (code-enforceable → substrate; judgment-only → resident); the code-enforceable ones moved to or **proposed** for a hook/gate/schema/test; the judgment remainder kept resident and subject to VERIFY FIRING; the overlay pointing at the shared principle as a single source, not a restated fork.

## The enforcement-placement core (referenced, not forked)

Provenance: this core is the agnostic principle supplied with the task, derived from jb's `docs/doctrine/enforcement_placement_doctrine.md` (candidate). It is repo-invariant and carries no jb specifics. It is carried inline **only because the cross-repo shared home is TBD** (see § Step 4); the intent is to reference it as a single source, never to fork or weaken it. It is cited as provenance, not imported as Orca authority.

- **ENFORCEMENT PLACEMENT** — when a rule must hold at a boundary, prefer enforcing it in a deterministic substrate (tool-boundary hook · gate/assertion · schema/typed boundary token · deterministic test) over a resident model instruction. Code-enforced fires always at zero model budget; actor-carried is flexible but unreliable and competes for budget.
- **CLASSIFY SUBSTRATE-FIRST** — before installing any rule as a resident instruction, ask whether a deterministic substrate can enforce it at its boundary; if yes, harden it there and don't also carry it in the model.
- **RESERVE THE BUDGET** — the always-on budget is scarce and degrades with rule count/position; reserve it for judgment rules with no deterministic check.
- **ACTOR-CARRIED REMAINDER OWES FIRING** — carry as an instruction only the remainder with no deterministic check; it still owes VERIFY FIRING (present in the prompt ≠ fired).
- **PLACEMENT IS NOT AUTHORITY (over-edge)** — this decides WHERE a rule is enforced, never WHETHER it's correct/validated. Forcing a judgment rule into brittle code to "always fire" is the over-edge failure.

Decision rule, applied per overlay rule R:

```text
INPUT: an overlay rule R that must hold.
TEST:  is there a deterministic substrate that can enforce R at its boundary
       (tool-boundary hook / gate / schema·typed token / deterministic test)?
  → YES: enforce R in that substrate; do NOT also carry it as an instruction.
  → NO (genuine judgment): keep R resident; it owes VERIFY FIRING.
```

## Method and the load-bearing finding

The verdicts use four values:

- **SUBSTRATE** — fully code-enforceable at a boundary; deterministic; a clear win to propose.
- **PARTIAL** — the checkable shell (presence / shape / path / count / enum / hash) goes to a substrate; the judgment core stays resident. The substrate enforces **shape, never truth**.
- **JUDGMENT** — no deterministic check; stays resident; owes VERIFY FIRING.
- **OVER-EDGE** flag — a brittle check is technically possible but would manufacture false confidence; keep resident (PLACEMENT IS NOT AUTHORITY).

Substrate types: `hook` (Pre/PostToolUse tool-boundary guard — the only always-fires/zero-budget option; needs `.claude/settings.json` wiring), `test` (deterministic pytest, e.g. an `orca-harness` governance target), `schema` (typed-token / receipt-shape validation), `lint` (forbidden-token / forbidden-key / exact-string scan). These overlap (a forbidden-token scan can run as a hook or a test).

**Load-bearing finding — Orca has zero governance substrate today.** Verified this turn:

- **No hooks configured.** `.claude/settings.json` is plugin/marketplace config only; `.claude/settings.local.json` is a permission allowlist; there is no `PreToolUse`/`PostToolUse` block anywhere in-repo.
- **The only deterministic code (`orca-harness/`) is domain-scoped** (Judgment Spine v0.14 + Source Capture: `pytest`, a `Makefile`, fail-closed runners). It proves Orca *can* host deterministic tests and fail-closed assertions, but nothing in it enforces overlay governance.
- Every overlay "gate / contract / boundary" is therefore a **resident instruction**. None fires by construction.

Consequence: in Orca **right now**, every SUBSTRATE/PARTIAL verdict names a substrate that **does not exist yet**, and building it is **owner-gated**. So the "moved" column is empty by construction — this deliverable is inventory + classification + **proposals**, with one explicit owner gate. (This is exactly the prepare-only, owner-gated boundary the task set.)

## Per-rule classification

IDs are stable handles for later owner gating. Where a rule appears in several overlay files, the row cites the controlling one and notes the others. "Win" marks the clear code-enforceable proposals.

| ID | Rule (overlay source) | Boundary | Verdict | Proposed substrate (does not exist yet — owner-gated) |
| --- | --- | --- | --- | --- |
| EP-01 | Do not edit `jb` / external reference folders / installed-user-plugin-external skills (`safety-rules`; also `artifact-roles` Protected Roles, `skill-adoption` Protected Skill Boundary, `delegated-review-patch` protected_path_list) | write/edit/delete tool call | **SUBSTRATE** · Win | `PreToolUse` path-deny hook → `BLOCKED_PROTECTED_PATH`. Collapses 4 rules into one boundary. **Sampled, App A.** |
| EP-02 | No implementation dirs (`src`/`app`/`packages`/`tests`/runtime) unless authorized (`artifact-folders`; also `validation-gates`, `safety-rules`) | write / mkdir | **SUBSTRATE** · Win | `PreToolUse` path guard + `test`; "unless authorized" = a flag the guard reads → `BLOCKED_IMPL_DIR_UNAUTHORIZED`. **Sampled, App A.** |
| EP-03 | No commit/push/remote/PR/destructive cleanup unless authorized (`safety-rules`) | Bash `git`/`gh` call | **SUBSTRATE** · Win | `PreToolUse` command-pattern deny → `BLOCKED_GIT_LIFECYCLE_UNAUTHORIZED`. **Sampled, App A.** |
| EP-04 | Durable writes land in accepted folders (`artifact-folders` accepted list) | write path | **PARTIAL** | `hook`/`test` folder-allowlist; judgment edge: new folders allowed by a later decision. |
| EP-05 | No `jb` / forbidden-import leakage in prompts & artifacts (`validation-gates` leakage gate; `prompt-orchestration` anti-import; `template-registry`; `project-authority` forbidden drift) | artifact content at write | **SUBSTRATE** (token/path patterns) / PARTIAL ("as authority" semantics) · Win | `lint` forbidden-token scan (jb paths, GAP/CV Engine, compiler paths) as hook or test. |
| EP-06 | Retrieval header present on in-scope durable artifacts (`retrieval-metadata` applicability; also `validation-gates`, `artifact-folders`) | durable doc write | **SUBSTRATE** (presence) / PARTIAL ("in scope?" edge) · Win | `lint`/`test`. **The jb exemplar.** **Sampled, App B.** |
| EP-07 | Header well-formed: `retrieval_header_version: 1`, `authority_boundary: retrieval_only` exact, no forbidden fields, core ≤5 unless justified (`retrieval-metadata`) | header block | **SUBSTRATE** (exact-value + forbidden-key + count) / PARTIAL ("triggered field justified") · Win | `lint`/`test`. **Sampled, App B.** |
| EP-08 | `orca_start_preflight` receipt present + required fields on repo-aware / docs-write / source-change / completion (`source-loading`; also `validation-gates`, `prompt-orchestration`) | prompt / closeout | **PARTIAL** | `schema` presence/shape. Truth of `agents_read`/`overlay_read` → resident (non-self-cert, EP-29). |
| EP-09 | `direction_change_propagation` receipt or blocker present on doctrine-changing edits (`source-of-truth` DCP contract; also `validation-gates`, `prompt-orchestration` gate 12, `communication-style`) | doctrine-change closeout | **PARTIAL** · OVER-EDGE | `schema` receipt presence/shape; the `stale_language_search` field is a literal `rg` → re-runnable by `test`. But "is this edit doctrine-changing?" and "are downstream surfaces really checked?" stay resident — a hook must **not** decide doctrine-ness. |
| EP-10 | `review_summary` shape + forbidden-keys + `recommendation` enum + `report_path` valid only if the file exists (`communication-style`) | review summary YAML | **SUBSTRATE** · Win — enum sub-check accepted `--audit`-only (owner decision 2026-07-10; see the EP-10/11/15 Update) | Built: `check_review_summary.py` — forbidden keys, `report_path` existence (real file check), failed-write shape, non-blank `recommendation` are strict; enum membership is advisory by owner acceptance, never gated. |
| EP-11 | Exactly one output mode from the closed set (`prompt-orchestration`; `validation-gates` output-mode gate) | prompt artifact | **PARTIAL** — corrected 2026-07-10 (see the EP-10/11/15 Update) | Built: `check_prompt_output_mode.py` — declaration presence + token-in-set is SUBSTRATE; exactly-one / role-scoping is resident (the field shape is legitimately reused for dispatch/receiver roles). |
| EP-12 | Typed tokens valid: `BLOCKED_*`, `SOURCE_CONTEXT_READY`, prompt verdicts, `access` enum (`artifact-roles` failure states; `prompt-orchestration`; `delegated-review-patch`) | artifact | **PARTIAL** | `schema` token-spelling / enum membership; correct application → resident. |
| EP-13 | Every prompt role bound in `artifact-roles` (`validation-gates` artifact-role gate; `prompt-orchestration` gate 2) | prompt | **SUBSTRATE** (existence lookup) / PARTIAL ("right role") | `test`/`schema` role-table lookup → `BLOCKED_UNBOUND_ARTIFACT_ROLE`. |
| EP-14 | Default path assignment: versioned filename in accepted folder; collision → next version (`prompt-orchestration`) | write path | **PARTIAL** | `hook`/`test` exists-check + folder allowlist; "narrowest / descriptive" → judgment. |
| EP-15 | Hash pins verifiable: skill-source sha256, migration input hashes (`skill-adoption`; `validation-gates`) | pinned artifact | **SUBSTRATE** · Win | `test` recomputes and compares the hash — fully deterministic. |
| EP-16 | Source-capsule budget counts (≤4 full / ≤8 targeted / ≤10 excerpts) (`source-loading`; `validation-gates`) | capsule artifact | **PARTIAL** | `schema` count check; "right narrowing" → judgment. |
| EP-17 | Template-registry integrity: each registry path exists; unbound kinds (`direct-implementation`/`repo-code-review`/`automation-runtime`) unused absent authorization (`template-registry`) | registry + template use | **SUBSTRATE** (path-existence test) / PARTIAL (use-guard) | `test` registry integrity; `hook` use-guard. |
| EP-18 | Subagent runtime payload safety: no explicit `default`/`null`/same-as-parent `agent_type`/`model`/etc. on forked spawns (`decision-routing`) | spawn payload | **PARTIAL → SUBSTRATE** if the spawn passes a checkable boundary | `schema` payload reject. |
| EP-19 | Delegated-patch eligibility: author vendor ≠ delegate vendor, direct repo access, operator-courier-only rendering, and no same-vendor/task-creation fallback (`delegated-review-patch`) | commission record | **JUDGMENT** (resident) — checker retired 2026-07-25 | The former `check_prompt_output_mode.py` courier-shell check triggered only on a self-declared `target_kind` token, real courier prompts never declared it, and it had zero observed catches; retired with the lane binding. Eligibility is enforced by `delegated-review-patch.md` and CA adjudication; reinstate as a structural path-based trigger if adjudication misses a same-vendor substitution. |
| EP-20 | Historical delegated-patch `no_repo` package | review package | **RETIRED for delegated patch** | Delegated review-and-patch now requires direct repo access; no_repo routes to an ordinary read-only review and cannot claim delegated patch authorship. |
| EP-21 | Reviewer threads source-read-only unless assigned patch execution (`review-lanes`; AGENTS kernel) | write in a review lane | **PARTIAL** · OVER-EDGE-adjacent | enforceable as `hook` only if the lane is machine-tagged (it is not today) → resident/partial now. |
| EP-22 | No runtime-model recommendation / ranking in review prompts/closeouts (`review-lanes`; `prompt-orchestration`) | review artifact content | **PARTIAL** · OVER-EDGE | `lint` phrase tripwire is brittle/advisory; do not hard-block on a phrase match. Mostly judgment. |
| EP-23 | Source-hierarchy precedence & conflict resolution (`source-of-truth`) | reasoning | **JUDGMENT** (PARTIAL only for "referenced required source missing → fail" = missing-file check) | resident; owes VERIFY FIRING. |
| EP-24 | Cynefin routing: run-vs-bypass, regime, bottleneck, riskiest assumption, stop/pivot, allowed/disallowed (`decision-routing`) | pre-planning | **JUDGMENT** | resident; owes VERIFY FIRING. Output-shape presence = weak partial only. |
| EP-25 | Smallest complete intervention / scope discipline (`AGENTS.md`; `safety-rules`) | every change | **JUDGMENT** | resident; owes VERIFY FIRING. |
| EP-26 | Source-gated method contract: `REFERENCE-LOAD` vs `APPLY`; no method-derived conclusions before `SOURCE_CONTEXT_READY` (`prompt-orchestration`) | prompt sequencing | **JUDGMENT** (token presence = weak partial) | resident; owes VERIFY FIRING. |
| EP-27 | Product-proof semantics: `trust_objection` vs `trust_refusal`; kill-criteria; pull-vs-praise; claim tier; weakest-cleared-gate; non-claims (`product-proof`; `validation-gates` product gates) | proof reasoning | **JUDGMENT** (non-claims presence = weak partial) | resident; owes VERIFY FIRING. |
| EP-28 | Zero-spoiler backtest: no reveal of decision/recommendation/outcome in participant-facing material (`product-proof`; `validation-gates`) | participant artifact | **JUDGMENT** · OVER-EDGE | resident. A keyword leak-scan is at best a noisy advisory tripwire and must never be treated as a pass/clear. |
| EP-29 | Receipt-field provenance / non-self-certification (`validation-gates`) | any gate clearing on a field | **JUDGMENT** (PARTIAL corollary: "single-source duplicated enumerations" = dup-enumeration lint) | resident. **This rule is itself the formalization of PLACEMENT IS NOT AUTHORITY for receipts: a substrate checks a field's shape, never its truth.** |
| EP-30 | Chat-output topology / communication style: human-summary-first, decision-first, readability (`communication-style`) | chat output | **JUDGMENT** | resident; owes VERIFY FIRING. |
| EP-31 | Checkpoint-artifact lifecycle: non-authoritative; single-consumption/burn; one live instance per lane; point-don't-copy (`source-of-truth`) | checkpoint files | **PARTIAL** | `test` can detect "one live instance / no `_v2`/`_v3`"; "re-confirm volatile claims / burn after consumption" → judgment/behavioral. |

Distribution: **clear SUBSTRATE wins** — EP-01, EP-02, EP-03, EP-05, EP-06, EP-07, EP-10 (enum sub-check accepted `--audit`-only, owner decision 2026-07-10), EP-13, EP-15, EP-20. **PARTIAL (shape→substrate, core→resident)** — EP-04, EP-08, EP-09, EP-11 (corrected 2026-07-10), EP-12, EP-14, EP-16, EP-17, EP-18, EP-21, EP-22, EP-29(corollary), EP-31. **JUDGMENT (resident, owes VERIFY FIRING)** — EP-19 (moved from PARTIAL 2026-07-25; checker retired with the lane binding), EP-23, EP-24, EP-25, EP-26, EP-27, EP-28, EP-29(core), EP-30.

## The clear code-enforceable wins (proposed, prioritized)

These are the proposals worth the owner's authorization first, highest leverage downward. None exists yet.

1. **One `PreToolUse` protected-path guard** (EP-01, EP-02, EP-03; partial EP-21). A single tool-boundary hook collapses the largest cluster of "do not edit X / do not run Y unless authorized" rules into one always-fires check at zero model budget. Highest leverage; smallest surface. Sample in App A.
2. **Retrieval-header lint** (EP-06, EP-07). The jb exemplar, near-verbatim for Orca: presence + `version: 1` + exact `authority_boundary: retrieval_only` + forbidden-field scan. Pure shape; runs as a `PostToolUse` hook or an `orca-harness` test. Sample in App B.
3. **Forbidden-import / `jb`-leakage lint** (EP-05). A forbidden-token scan enforces "do not copy jb templates/paths/Engine/compiler paths" by construction.
4. **Receipt-shape schemas** (EP-08, EP-09, EP-10, EP-11, EP-12, EP-13). Validate presence/shape/enum of `orca_start_preflight`, `direction_change_propagation`, `review_summary`, output mode, typed tokens, bound roles. **Shape only — truth stays resident (EP-29).**
5. **Hash-pin verification** (EP-15, EP-20). A test recomputes pinned sha256s (skill source, migration inputs, no_repo attachments) and fails on drift.

## Over-edge cautions (PLACEMENT IS NOT AUTHORITY, in Orca)

Do not push these into brittle code to "always fire" — doing so manufactures false confidence:

- **Zero-spoiler leak detection (EP-28).** A keyword scan cannot reliably tell a spoiler from clean pre-cutoff evidence; a green scan would falsely read as "no leak." Keep resident; a scan may exist only as a noisy advisory tripwire, never a clear.
- **"Is this edit doctrine-changing?" (EP-09 trigger).** A hook may demand the DCP receipt once doctrine-ness is asserted, but must not be the thing that decides doctrine-ness.
- **Receipt truthfulness (EP-29).** Already Orca doctrine: a self-asserted field value does not clear a gate. Substrate enforces a receipt's shape; it never certifies the value is true.
- **Runtime-model phrasing (EP-22), reviewer-lane writes (EP-21).** Enforceable only as advisory/partial until lanes are machine-tagged; a hard block on phrase-match or untagged lane is over-edge today.

## Step 4 — proposed overlay pointer (blocked-on; not bound this turn)

Step 4 ("point the overlay at the shared principle as its single source") is **blocked by design** and is therefore proposed, not performed:

- The cross-repo **shared home is TBD** (per the task, part of the later distillation change) — there is no canonical source to point at yet.
- **Binding the doctrine to Orca is the separate later task**, explicitly out of scope here.
- Editing an overlay-authority file to add a new resident rule is itself **doctrine-changing** (it would owe a DCP receipt and likely owner gating) — and adding a *resident* restatement of an enforcement-placement principle would also spend budget, the very thing the principle warns against.

Proposed binding, to be lifted **verbatim** by the later task once a shared home exists (reference, do not fork):

> **ENFORCEMENT PLACEMENT (referenced).** When an overlay rule must hold at a boundary, prefer enforcing it in a deterministic substrate (tool-boundary hook · gate/assertion · schema/typed token · deterministic test) over a resident instruction; classify substrate-first; reserve the resident budget for judgment rules; the actor-carried remainder still owes VERIFY FIRING; placement decides WHERE, never WHETHER. Single source: `<shared doctrine path — TBD>`.

Proposed landing site: one short pointer (≈4 lines) — most naturally a sub-note under `validation-gates.md` (it governs what clears a gate) cross-referenced from `decision-routing.md`. It should be a **pointer to the shared source**, not a copy. Until the shared home and an owner decision exist, this stays a proposal here.

## Owner gate — what authorization would move propose → build

Each item is bounded and independent; none is implied by this record.

- **Authorize the `PreToolUse` protected-path guard** (App A) and its `.claude/settings.json` wiring (EP-01/02/03). This is "deployed automation" under `safety-rules` and needs explicit bounded authorization.
- **Authorize the retrieval-header lint** (App B) as an `orca-harness` governance test target or a `PostToolUse` hook (EP-06/07).
- **Authorize the leakage lint and the receipt-shape schemas** (EP-05, EP-08–EP-13) as tests/hooks.
- **Create (elsewhere) the shared doctrine home**, then run the separate binding task to add the Step-4 pointer.

## Non-claims

- Not validation, readiness, acceptance, approval, or proof of anything.
- Not a doctrine change and not an overlay edit; no DCP receipt owed.
- Not implementation, deployment, install, or resolver authorization; the sample drafts in App A/B are illustrative and run/install nothing.
- Not a binding of the shared doctrine to Orca (that is the separate later task).
- The classification is of Orca's **real** overlay rules as read this turn; substrate availability is reported as found (none exists), not assumed.

---

## Sample Substrate Drafts (removed)

The two prepare-only SAMPLE drafts that illustrated possible substrates — a
`PreToolUse` protected-path guard (EP-01/EP-03) and a retrieval-header lint
(EP-06/EP-07) — have been removed: those substrates are now BUILT and live in
`.agents/hooks/` (`guard_protected_actions.py` for EP-01/EP-03;
`check_retrieval_header.py` for EP-06). The built scripts are the durable
reference and enforce shape only, never the truth of any field. EP-02
(implementation-directory blocking) remains deliberately owner-declined with no
hook (see the classification body above).
