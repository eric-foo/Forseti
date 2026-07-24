# Summer Fridays Phase A Cold Run p10 — Execution Handoff

```yaml
retrieval_header_version: 1
artifact_role: Execution-ready cold handoff
scope: >
  Executes one fresh Summer Fridays Understanding Turn A Acquire & Seal run
  under the current default coordinated route, then stops before Turn B.
use_when:
  - Testing whether the landed Phase A seal-hardening contract can reach a
    decision-useful acquisition seal from cold context.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
stale_if:
  - The Intelligence Cycle acquisition contract or default US consumer-beauty
    Understanding route changes.
  - The couriered commit is not an ancestor of the receiver's execution base.
```

## Load Contract

```yaml
packet_version: 1
mode: max
created_at: 2026-07-25T04:37:30.2998549+08:00
created_by_lane: codex/sf-phase-a-cold-run-handoff
source_loading_mode: repo-overlay-bound
workspace: C:\Users\vmon7\Desktop\projects\orca
handoff_path: docs/prompts/handoffs/summer_fridays_phase_a_cold_run_20260725_p10.md
expected_branch: a new controller-owned codex/sf-understanding-p10-cold-phase-a branch
expected_head: the couriered handoff commit, whose parent is ffd8bf9db485ed8716095cff27b24289484de24c
expected_dirty_state_including_handoff_file: clean at receiver binding
load_rule: >
  Confirm, do not trust. Re-verify every load-bearing fact against the
  couriered revision and current workspace before acting. This packet is
  orientation and commission transport, not evidence that the run succeeded.
```

## Prompt Preflight

```yaml
output_mode: file-write
write_destination:
  commission_board: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/commission_board.md
  co1_terminal: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co1_company_core_identity.md
  co2_terminal: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co2_retail_portfolio.md
  co3_terminal: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/specialists/co3_customer_community_depth.md
  acquisition_record: docs/research/summer_fridays_understanding_dogfood_20260725_p10/coordinated/turn_a_acquisition_record.md
  acquisition_seal: docs/workflows/summer_fridays_understanding_dogfood_20260725_p10/coordinated/acquisition_seal.md
edit_permission: implementation-authorized
input_prompt_source: docs/prompts/handoffs/summer_fridays_phase_a_cold_run_20260725_p10.md at the couriered commit
target_scope: one p10 cold Phase A run, its named durable outputs, and its isolated data root
required_revision: couriered handoff commit
revision_mode: required_revision_is_ancestor_and_runtime_base
repository_state_allowance: only the named p10 outputs may become dirty
data_root: C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data
later_company_output_validation: future_only
turn_b: forbidden
company_report: forbidden
control_comparison: deferred_until_p10_seal_exists
doctrine_change: none
```

Shared preflight constants remain owned by
`docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`.

## Goal Handoff

```yaml
long_term_goal: >
  Make Forseti's Understanding evidence layer reliably produce a complete,
  provenance-bearing, decision-useful company substrate before synthesis.
anchor_goal: >
  Run Summer Fridays Phase A once from cold context under the landed
  seal-hardening contract, maximizing decision-useful completeness without
  using prior Summer Fridays conclusions or evidence packets.
success_signal: >
  CO0 can honestly issue SEALED_READY_FOR_DELIVER after the canonical attempt
  and at most one retry per failed material route, with all material company,
  portfolio/retailer, customer/community, chronology, provenance, and
  uncertainty jobs supported, contradicted, meaningfully bounded, or honestly
  gapped; no evidence family is dropped to make the seal pass and Turn B has
  not started.
```

## Open Decision / Fork

None open. Evidence determines the selected authorized retailers and expensive
interpretive depth. The receiver must not impose a fixed retailer count,
preselect hero products as the raw-acquisition boundary, or lower the
acquisition standard to force a passing seal.

## Drift Guard

- **Coldness is load-bearing.** Before the p10 seal exists, no evidence actor
  may read prior Summer Fridays prompts, raw packets, commission boards,
  specialist returns, acquisition records, seals, reviews, selections,
  conclusions, or comparison outputs. Reusing them would convert the run into a
  replay and invalidate the baseline comparison.
- **Methods are reusable; subject evidence is not.** Actors may use current
  accepted source contracts, recon recipes, runners, schemas, and generic
  fixtures. Every Summer Fridays fact used in p10 must come from a fresh p10
  capture or a fresh-read public source durably preserved for p10.
- **No Turn B.** Do not write a company report, Problem Framing artifact, or
  synthesis deliverable. A passing seal authorizes nothing automatically.
- **Real failures remain visible.** At most one retry follows an observed
  failed material route. Do not silently substitute browsing, infer absence
  from access failure, or count a URL/summary as durable evidence when the
  underlying material claim requires preservation.
- **US-facing is not nationwide stock proof.** A `.com` US surface, US/USD
  shell, VPN state, ZIP, or delivery context can bind the observed US-facing
  surface and local fulfillment context. None independently proves nationwide
  availability, stock, or absence.
- **Exactly four analytic actors.** CO0 plus CO1-CO3 are the entire analytic
  topology. Any release mechanism is mechanical, not a fifth analytic actor.
  CO3 is mandatory.

## Inherited Context (Does Not Flow To A New Lane)

### Source-loading state to re-establish

- Overlay source-loading policy:
  `.agents/workflow-overlay/source-loading.md`.
- Enter the ladder through:
  `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
  and
  `forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md`.
- Already loaded here, as weak orientation only: the two owning sources above,
  the historical p06 execution prompt, the p07 evidence-completion record and
  seal, and the p07 coverage-review commission.
- Must load first before actionable work: `AGENTS.md`,
  `.agents/workflow-overlay/README.md`, the two owning sources above, then the
  capture playbook and retailer source-family READMEs or recipe pointers those
  sources actually route to.
- Load rule: rerun progressive source loading. The loaded-set above seeds the
  ladder but satisfies no strict claim.

### Earlier-decided concepts and behaviors

- Turn A maximizes decision-useful completeness; Turn B applies smallest
  complete compression only after a passing seal.
  - Decided in:
    `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`.
  - Compare target: the couriered commit; read `Forseti Intelligence Cycle`,
    `Turn A — Acquire & Seal`, and the acquisition-seal contract.
  - Verify before: validating the commission board or adjudicating the seal.
- The default US consumer-beauty route is CO0 plus CO1-CO3; CO3 owns mandatory
  customer/community and complete bounded review-corpus acquisition.
  - Decided in the same playbook.
  - Compare target: the couriered commit; read `Default US Consumer-Beauty
    Understanding Route`.
  - Verify before: dispatch.
- Retail customer evidence is acquired breadth-first: baseline PDP coverage,
  one typed outcome for every distinct accessible review corpus, then
  evidence-selected interpretation. Sephora retains its source-specific
  policy; selected non-Sephora retailers default to source-labelled Most
  Recent/newest.
  - Decided in the playbook and
    `retailer_information_extraction_standard_v0.md`.
  - Compare target: the couriered commit.
  - Verify before: CO2/CO3 lock their jobs.
- The p07 corrected evidence layer is the historical control, but it is
  contamination for p10 acquisition.
  - Verify pointer after p10 seals:
    `docs/research/summer_fridays_understanding_dogfood_20260725_p07/evidence_layer_completion.md`
    and
    `docs/workflows/summer_fridays_understanding_dogfood_20260725_p07/acquisition_seal.md`.
  - Compare target: the couriered commit.
  - Verify before: only a separately commissioned post-seal comparison.

## Active Objective

Execute one fresh Summer Fridays Understanding Turn A Acquire & Seal run in an
isolated worktree. Produce the six named durable p10 artifacts and the p10 raw
evidence root, then stop after CO0's manual whole-gate adjudication.

## Exact Next Authorized Action

1. Bind a clean controller-owned worktree and branch from the couriered commit.
   Return `BLOCKED_DRIFT` if the exact handoff file is absent, the couriered
   commit is not an ancestor, or another writer owns the target.
2. Re-run the source-loading ladder, create the p10 commission-stage board with
   `run_boundary: COMMISSION_SEALED_PRE_SCAN`, and validate it before
   source-heavy work:

   ```powershell
   python -B .agents\hooks\check_commission_signal_board_output.py docs\research\summer_fridays_understanding_dogfood_20260725_p10\coordinated\commission_board.md
   ```

3. Dispatch CO1-CO3 together as same-root collaboration subagents. Each actor
   plans once, locks its evidence-derived deterministic job set, persists raw
   evidence as it is produced, and writes one terminal return. Actor-local
   failures stay in the same task; do not restart unaffected actors.
4. CO0 fresh-reads the durable evidence and terminal returns, integrates the
   acquisition record, and manually adjudicates the whole seal. If a material
   owner-fixable route fails, issue the playbook's one consolidated owner
   unblock and use at most one retry after the owner action.
5. Run prompt/output, retrieval-header, diff, and artifact-presence checks
   applicable to the changed p10 files. Stop with either a truthful passing seal
   or `BLOCKED_ACQUISITION_INCOMPLETE`; do not start Turn B or compare p10 with
   p07.

## Execution Contract

### CO0 — controller, integrator, and seal owner

- Validate the commission-stage board once.
- Dispatch exactly CO1-CO3 and keep their briefs thin and role-specific.
- Wait on terminal completion or a decision-requiring blocker, not routine
  progress dialogue.
- Treat specialist returns as pointers, never evidence. Fresh-read every
  seal-bearing artifact and disposition.
- Write the integrated acquisition record and manually adjudicate the whole
  gate after any retry or correction.

### CO1 — owned company and high-yield core

- Fresh-capture company identity, ownership, current leadership, proposition,
  owned portfolio denominator, markets/channels, chronology, material events,
  trust-relevant incidents/responses, and one bounded outside-in scale or
  market/channel calibration when credible evidence can materially calibrate
  the core.
- Capture the company-owned official retailer surface before retailer probing.
  Publish a supported authorization board with typed unknowns and failures.
- Normalize products at the real family level: shade, flavor, and sellable-size
  variants are not automatically separate products; bundles, samples,
  merchandise, and historical objects remain typed separately. Resolve every
  exposed owned parent exactly once or preserve the unresolved identity.

### CO2 — unified official-first portfolio and retailer corpus

- Prepare concurrently, but do not probe retailers before CO1 publishes the
  company-owned authorization outcome.
- Include Sephora and make it primary when it is officially named,
  US-admissible, and route-complete. Otherwise retain its typed outcome and use
  another complete working primary.
- Select officially named, route-admissible retailers that add material,
  non-duplicative evidence. There is no fixed four-retailer quota and no credit
  for probing Target, Amazon, Ulta, or any other retailer merely to fill a slot.
- For every selected retailer: refresh the complete admitted brand grid,
  reconcile every verified grid row to owned candidates, and preserve one
  verified raw PDP baseline for every exact non-bundle listing. Preserve
  duplicates, variants, bundles, unmatched rows, ambiguity, and typed route
  failures rather than collapsing them.
- Bind review provider, tenant/store, collection context, sort capability, and
  overlap ceilings from observed evidence. Never infer Yotpo, Bazaarvoice, or
  authorization from retailer identity alone.

### CO3 — mandatory customer/community and review-corpus acquisition

- Begin the bounded customer/community scout immediately. Preserve customer
  language, pain points, purchase drivers, objections, complaints, usage,
  workarounds, response patterns, zero-yield routes, and claim ceilings.
- After CO2's baseline PDP board exists, account for every selected-retailer
  listing on a distinct-corpus board.
- Acquire one bounded onboarding window for every distinct accessible corpus,
  or record a typed no-review, not-exposed, blocked, or unresolved-identity
  outcome. Do not select hero products first and leave the rest unobserved.
- Sephora keeps its current source-specific dual-window/Q&A policy where source
  volume supports it. For selected non-Sephora retailers, use source-labelled
  Most Recent/newest when supported and record the actual ordering and fallback.
- Deduplicate native review IDs; otherwise use provider plus normalized
  text/date/rating fingerprints. Shared or syndicated placements remain
  visible but count as one independent evidence family.
- After breadth acquisition, select category/exposure-balanced corpora for
  expensive interpretation. Interpretation depth follows company exposure and
  includes discriminating high- and low-performing evidence where the source
  supports it; it is not an artificial 50/50 category split and not universal
  row-by-row interpretation.

## Authority And Source Ledger

- Repository instructions: `AGENTS.md`.
- Overlay authority: `.agents/workflow-overlay/README.md` and the source-loading
  policy it names.
- User constraints: cold Phase A only; p07 is the control; maximize decision
  usefulness; CO3 is mandatory; no Turn B or company report.
- Source-read ledger:
  - `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`
    - Role: owning Intelligence Cycle, actor-route, acquisition, retry, and seal
      contract.
    - Load-bearing: yes.
    - Compare target: couriered commit; reread required.
    - Last checked: 2026-07-25 on base
      `ffd8bf9db485ed8716095cff27b24289484de24c`.
    - Reuse rule: receiver must reread targeted controlling sections.
  - `forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md`
    - Role: owning retail grid/PDP/review extraction and failure semantics.
    - Load-bearing: yes.
    - Compare target: couriered commit; reread required.
    - Last checked: 2026-07-25 on the same base.
    - Reuse rule: receiver must reread before CO2/CO3 lock jobs.
  - `docs/research/summer_fridays_understanding_dogfood_20260725_p07/evidence_layer_completion.md`
    - Role: historical control evidence completion.
    - Load-bearing: no during p10 acquisition; yes only in later comparison.
    - Compare target: couriered commit.
    - Last checked: 2026-07-25 on the same base.
    - Reuse rule: forbidden before p10 seals.
  - `docs/workflows/summer_fridays_understanding_dogfood_20260725_p07/acquisition_seal.md`
    - Role: historical control seal.
    - Load-bearing: no during p10 acquisition; yes only in later comparison.
    - Compare target: couriered commit.
    - Last checked: 2026-07-25 on the same base.
    - Reuse rule: forbidden before p10 seals.
- Source gaps: live public-route state is intentionally unknown until p10
  capture; prior success is not current route proof.
- Strict-only blockers: missing owning sources, dirty receiver root, absent
  capture authority, or a material route that remains unresolved after its
  canonical attempt and one retry.
- Not-proven boundaries: a passing p10 seal, method superiority, exhaustive web
  coverage, and p10-versus-p07 improvement are not proven by this handoff.

## Current Task State

- Completed: Phase A hardening landed on `origin/main` as
  `ffd8bf9db485ed8716095cff27b24289484de24c`; p07 remains the historical
  corrected control.
- Partially completed: none for p10; no p10 acquisition has started.
- Broken or uncertain: current public route accessibility and the evidence-
  derived selected-retailer set are intentionally unresolved until the run.

## Workspace State

- Branch: `codex/sf-phase-a-cold-run-handoff`.
- Head before handoff commit:
  `ffd8bf9db485ed8716095cff27b24289484de24c`.
- Dirty or untracked state before handoff: clean.
- Dirty or untracked state after writing the handoff: this one new untracked
  handoff file only.
- Target artifacts: the six p10 paths in Prompt Preflight plus the isolated p10
  data root.
- Related worktrees or branches: the receiver creates a new p10 execution
  worktree; it must not write in the handoff-authoring worktree.

## Changed / Inspected / Tested Files

- `docs/prompts/handoffs/summer_fridays_phase_a_cold_run_20260725_p10.md`
  - Status: newly authored handoff.
  - Role: sole bounded change in this handoff-only transport unit.
- The two owning sources in the Authority And Source Ledger
  - Status: inspected, unchanged.
  - Role: execution and seal contracts.
- The p07 evidence-completion record and seal
  - Status: inspected, unchanged.
  - Role: control identity only; prohibited acquisition inputs.

## Frozen Decisions

- p10 is coordinated CO0-CO3; CO3 cannot be removed or merged away.
- p10 is cold with respect to all prior Summer Fridays evidence and outputs.
- Phase A optimizes decision-useful completeness; compactness is not a success
  criterion.
- Raw review-corpus acquisition is breadth-first across the selected retailer
  denominator; interpretation remains evidence-selected.
- Official-retailer discovery precedes probing. Sephora is primary when
  officially named and route-complete; there is no arbitrary retailer quota.
- Canonical attempt plus at most one retry per failed material route.
- No Turn B, company report, or p07 comparison in the p10 execution task.

## Mutable Questions

- Which officially named retailers add material non-duplicative evidence?
  - Why still mutable: only fresh CO1 authorization evidence can answer it.
  - Resolution: CO1's supported official-retailer board plus current route
    outcomes.
- Which product/category corpora merit expensive interpretation?
  - Why still mutable: selection must follow current breadth, exposure,
    narrative yield, performance spread, and material seams.
  - Resolution: CO2's reconciled portfolio and CO3's complete bounded
    distinct-corpus board.

## Superseded / Dangerous-To-Reuse Context

- The p06 execution prompt is historical design evidence, not the p10
  commission. Its fixed selections, raw manifest, revision, paths, and output
  counts must not be copied into p10.
- The p07 evidence-completion record and seal are the comparison control, not
  acquisition inputs. Reading them before p10 seals contaminates the run.
- ZIP `10001` as a national-availability proxy is rejected. It may bind only
  the observed local fulfillment context.
- Fixed retailer quotas and hero-first raw review selection are superseded by
  official-first material selection and complete bounded distinct-corpus
  onboarding.

## Commands And Verification Evidence

- Receiver commission-board gate:

  ```powershell
  python -B .agents\hooks\check_commission_signal_board_output.py docs\research\summer_fridays_understanding_dogfood_20260725_p10\coordinated\commission_board.md
  ```

  - Passed/failed/not run: not run; p10 board does not yet exist.
  - Re-run target: the receiver's p10 worktree.
- Handoff validation:
  - Passed/failed/not run: run by the sender after authoring; see the courier
    commit's validation evidence, not this pre-write statement.
  - Re-run target: retrieval header, prompt output mode, placement, and
    `git diff --check` for this file.

## Blockers And Risks

- Route accessibility can change between runs.
  - Evidence: not checked by this handoff author.
  - Likely next action: use the current canonical route, preserve the exact
    result, and spend at most one retry only after an observed material failure.
- A model may try to improve seal probability by narrowing the commission.
  - Evidence: this is the primary integrity risk the hardening change addresses.
  - Likely next action: retain the original decision-useful question and issue a
    truthful blocked seal if a material evidence family cannot be closed.

## Confirm-Don't-Trust Load Checklist

- Re-verify the couriered commit, branch ancestry, clean receiver worktree,
  handoff readability, owning playbook sections, retailer standard, output-path
  non-collision, and absence of another writer.
- `REUSE`: all load-bearing facts verified; start with the Exact Next Authorized
  Action.
- `PARTIAL_REUSE`: only optional control pointers drifted; acquire p10 without
  using them and report the drift.
- `STALE_REREAD_REQUIRED`: an owning source or execution base changed but can be
  safely rebound; reread and reconcile before work.
- `BLOCKED_DRIFT`: target collision, dirty-state conflict, changed authority, or
  another writer.
- `BLOCKED_MISSING_PACKET`: this handoff is absent or unreadable.
- `BLOCKED_UNVERIFIABLE`: a load-bearing authority or revision claim cannot be
  re-derived.

## Do Not Forget

The test is whether current Phase A can close honestly from cold context within
its bounded retry policy—not whether p10 can reproduce p07's exact facts,
counts, retailer set, or route luck.
