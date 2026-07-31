# Summer Fridays Phase 2 Evidence Discussion Handoff

```yaml
retrieval_header_version: 1
artifact_role: Cold-lane discussion handoff
scope: Re-verify and dissect the sealed Summer Fridays p11r3 Phase A evidence, then discuss whether and how a separately commissioned Deliver should proceed.
use_when:
  - Starting a fresh task to evaluate the Summer Fridays Phase A evidence pack.
  - Discussing the intended Deliver before authorizing or producing it.
authority_boundary: retrieval_only
```

## Load Contract

```yaml
packet_version: workflow_handoff_v1
mode: max
source_loading_mode: repo-overlay-bound
created_at: 2026-08-01
created_by_lane: codex/sf-deliver-discussion-handoff-20260801
workspace: C:\Users\vmon7\Desktop\projects\orca
handoff_path: docs/prompts/handoffs/summer_fridays_understanding_phase2_evidence_discussion_20260801_p12.md
expected_branch: codex/sf-deliver-discussion-handoff-20260801
expected_head: couriered packet commit; parent revision is d02e5bebbb26173685773d828ae7df59d55430cb
expected_dirty_state_including_handoff_file: clean at dispatch; this file was the only new path before its handoff-only commit
load_rule: confirm-don't-trust; re-verify every load-bearing fact against its compare target before making strict or actionable claims
```

```yaml
forseti_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom
  edit_permission: docs-write for this packet; receiver is read-only
  target_scope: Summer Fridays p11r3 Phase A evidence fitness and a possible future Deliver commission
  dirty_state_checked: yes
  blocked_if_missing: acquisition seal, acquisition record, specialist returns, raw packet roots, or a resolvable packet revision
```

```yaml
forseti_prompt_preflight:
  output_mode: chat-only
  report_destination: receiving task chat
  template_kind: handoff
  edit_permission: read-only
  targets:
    - Summer Fridays p11r3 acquisition seal and evidence pack
    - raw acquisition roots named below
    - discussion of a possible Deliver commission
  branch: receiver may use any clean checkout that resolves the couriered commit; do not edit it
  reviews: findings-first advisory discussion; no formal verdict, severity contract, or patch queue
  doctrine_change: none authorized
  input_source: this handoff packet at the couriered commit
  output_artifact: none
```

## Goal Handoff

- long_term_goal: Produce a trustworthy, decision-useful Summer Fridays understanding from evidence whose provenance, limits, and coverage are visible.
- anchor_goal: Independently test whether the sealed p11r3 Phase A evidence is fit for Deliver, then help the owner choose the smallest complete Deliver shape.
- success_signal: The receiving task separates verified facts from claims and gaps, explains whether the evidence is sufficient, offers a concrete Deliver boundary and options, and stops without producing or starting Deliver.

## Open Decision / Fork

- decision: Is the p11r3 evidence pack good enough for Deliver, and if so what should Deliver actually produce?
  - options:
    1. Recommend a full Deliver from the sealed evidence.
    2. Recommend a bounded Deliver that carries specific evidence limitations or excludes weak claim classes.
    3. Recommend reopening acquisition only if a re-verified material gap makes the intended Deliver misleading or unusable.
  - already constrained / off the table:
    - Do not start Deliver in this task.
    - Do not create a Deliver, synthesis, judgment, comparison, or downstream report artifact.
    - Do not recapture sources or rerun acquisition jobs.
    - Do not rewrite, delete, or “clean up” raw evidence or blocked-seal provenance.
    - Do not treat the passing seal as proof that the future Deliver will be decision-useful.
  - trade-offs:
    - Proceeding too easily can turn technically valid evidence into an overconfident report.
    - Reopening acquisition without a material decision gap wastes time and weakens the pending-only discipline.
    - A bounded Deliver may be the honest middle path when evidence is strong for some questions and weak for others.
  - owner of the call: user
  - recommendation and why: First dissect evidence fitness by source family and intended claim. Prefer a bounded Deliver over new acquisition unless a concrete missing fact would materially change the owner’s decision.

## Drift Guard

- Discussion-only boundary:
  - why it matters: This packet is for evidence evaluation and Deliver design, not execution.
  - what violating it would break: It would bypass the user’s separate-commission requirement and make a new Deliver artifact look authorized.
- Acquisition and reusable capture code are different questions:
  - why it matters: PR #1414 corrected future capture behavior; it did not manufacture or replace the final p11r3 packets.
  - what violating it would break: Treating the earlier code defects as automatic evidence invalidation, or treating the code fix as proof of evidence quality, would both be wrong.
- Preserve diagnostic provenance:
  - why it matters: The first p11r3 owned-page pair is a known classifier false-positive diagnostic and is excluded from completion credit.
  - what violating it would break: Counting it as terminal evidence or deleting it would corrupt the acquisition history.
- No positive certification from `content_unverified`:
  - why it matters: That label means no known access shell was detected, not that arbitrary content is true or complete.
  - what violating it would break: It would overstate the capture spine’s guarantee.
- Stop on drift:
  - why it matters: The seal and raw roots are load-bearing.
  - what violating it would break: Missing files, hash changes, a new Deliver artifact, or unresolved repository drift require `STALE_REREAD_REQUIRED` or `BLOCKED_DRIFT`, not silent reuse.

## Inherited Context (does NOT flow to a new lane)

### Source-loading state to re-establish

- overlay source-loading policy: `.agents/workflow-overlay/source-loading.md`
- targets to enter the ladder:
  - `docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/acquisition_seal.md`
  - `docs/research/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/turn_a_acquisition_record.md`
  - the three specialist terminal returns named in the source ledger
  - the four raw acquisition roots named in the source ledger
- already loaded: sender task read these at `origin/main=d02e5bebbb26173685773d828ae7df59d55430cb`; this is weak prior-task orientation only
- must load first: `AGENTS.md`, `.agents/workflow-overlay/README.md`, the source-loading policy, this packet, and the final acquisition seal
- load rule: Re-run progressive source loading. The prior loaded set does not satisfy strict claims in the receiving task.

### Earlier-decided concepts and behaviors

- Phase A is Acquire and Seal; Deliver is a separate lifecycle action.
  - decided in: `docs/prompts/handoffs/summer_fridays_understanding_cold_rerun_20260731_p11.md`
  - compare target: current canonical SHA256 `bcc08bda390a29c6da18a24ade47aeec8665c517e71e128cfe9e03365d69dd55`
  - verify before: discussing authority or starting any execution
- p11r3 ended with a passing acquisition seal and no pending jobs.
  - decided in: final p11r3 acquisition seal
  - compare target: canonical SHA256 `dc584868879d9f6f8a243d3985f3b89e67f82c8d3eccc9c0e4fd87a496f149f6`
  - verify before: saying Phase A is reusable or Deliver-eligible
- The capture-spine correction is durable for future runs, but the final evidence still needs source-specific evaluation.
  - decided in: merge commit `d02e5bebbb26173685773d828ae7df59d55430cb` and the amended acquisition record
  - compare target: `origin/main` contains PR #1414 and the acquisition record hash below
  - verify before: using the implementation correction as context

## Active Objective

Re-verify the Summer Fridays p11r3 evidence pack, distinguish strong evidence from limitations and internal route residuals, and discuss the smallest complete Deliver commission the owner could authorize next. Return analysis and options in chat only.

## Exact Next Authorized Action

1. Run the Confirm-Don't-Trust Load Checklist and return exactly one load outcome.
2. If the outcome permits reuse, validate the acquisition seal and re-hash the four raw roots’ declared packet files.
3. Inspect the terminal evidence by source family:
   - company-owned pages;
   - authorized retailer and exact-product evidence;
   - customer/community evidence across Reddit, retailer review corpora, TikTok, Instagram, and YouTube;
   - SERP Phase 1 and targeted Phase 2 evidence.
4. Dissect what each evidence family can and cannot support in a future Deliver. Do not simply repeat the acquisition accounting.
5. Discuss:
   - the intended reader and decision;
   - candidate Deliver structure;
   - which claims need caveats or exclusion;
   - whether comparison to prior p10 output is useful;
   - whether any material evidence gap truly requires new acquisition.
6. Recommend the smallest complete Deliver boundary and list the decisions the user must make before commissioning it.
7. Stop. Do not write files or begin Deliver.

## Authority And Source Ledger

- Repository instructions:
  - `AGENTS.md`
  - Role: global project behavior and authorization boundary.
  - Load-bearing: yes
  - Compare target: reread-required at receiver HEAD
  - Last checked: 2026-08-01
  - Reuse rule: orientation only until reread
- Overlay:
  - `.agents/workflow-overlay/README.md`
  - `.agents/workflow-overlay/source-loading.md`
  - `.agents/workflow-overlay/validation-gates.md`
  - Role: source precedence, bounded loading, and strict-claim gates.
  - Load-bearing: yes
  - Compare target: reread-required at receiver HEAD
  - Last checked: 2026-08-01
  - Reuse rule: reread the sections relevant to evidence/readiness discussion
- User constraint:
  - Exact carried instruction: “We will use this evidence pack, dissect it and discuss Deliver there.”
  - Role: current task scope.
  - Load-bearing: yes
  - Compare target: this packet’s Goal Handoff, Active Objective, and Drift Guard
  - Last checked: 2026-08-01
  - Reuse rule: do not broaden from discussion to execution
- Final acquisition seal:
  - Path: `docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/acquisition_seal.md`
  - Role: final Phase A accounting and Deliver-eligibility record.
  - Load-bearing: yes
  - Compare target: canonical SHA256 `dc584868879d9f6f8a243d3985f3b89e67f82c8d3eccc9c0e4fd87a496f149f6`
  - Last checked: 2026-08-01 at `d02e5bebbb26173685773d828ae7df59d55430cb`
  - Reuse rule: rerun `run_phase_acquisition_seal_validation.py`; do not trust the sender’s PASS
- Acquisition record:
  - Path: `docs/research/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/turn_a_acquisition_record.md`
  - Role: intake, pending-only execution, raw closure, and capture-spine correction history.
  - Load-bearing: yes
  - Compare target: canonical SHA256 `d4022b04a1078ea5b85e56486370f56de249392ee0daf854da0ea57f7181ff32`
  - Last checked: 2026-08-01
  - Reuse rule: targeted-read Confirm-Don't-Trust Intake, Pending-Only Execution, and Terminal Acquisition State; read the correction section when evaluating process history
- CO1 final return:
  - Path: `docs/research/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/specialists/co1_company_core_final_recovery.md`
  - Role: terminal company-owned-page recovery evidence.
  - Load-bearing: yes
  - Compare target: canonical SHA256 `f7e6204ceef7b76b8f72e3e3f75a3e6dd4e7c410731f66ddea6be6bab82265e9`
  - Last checked: 2026-08-01
  - Reuse rule: verify the two final packet manifests and body signals; exclude the diagnostic pair
- CO2 terminal return:
  - Path: `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md`
  - Role: authorized retailer, exact-PDP, reconciliation, provider, and corpus-pointer evidence.
  - Load-bearing: yes
  - Compare target: canonical SHA256 `b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880`
  - Last checked: 2026-08-01
  - Reuse rule: do not equate its `BLOCKED_TERMINAL` label with pending work; inspect its completed accounting and typed residuals
- CO3 final return:
  - Path: `docs/research/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/specialists/co3_customer_community_final_recovery.md`
  - Role: final TikTok recovery evidence and limitations.
  - Load-bearing: yes
  - Compare target: canonical SHA256 `27ac0fdc72ac4a52e531ab91da97289f57e4ae0c27dee79b16c4441f580c45dc`
  - Last checked: 2026-08-01
  - Reuse rule: verify final manifest and sanitized batch hash; keep its non-census and non-judgment limits
- Raw acquisition roots:
  - `C:\tmp\forseti-summer-fridays-understanding-p11-20260731`
  - `C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801`
  - `C:\tmp\forseti-summer-fridays-understanding-p11r2-20260801`
  - `C:\tmp\forseti-summer-fridays-understanding-p11r3-20260801`
  - Role: primary packet bytes and manifests.
  - Load-bearing: yes
  - Compare target: reread-required; expected closure is respectively 232 manifests/933 declared files, 11/40, 11/19, and 5/9, with zero size/hash failures
  - Last checked: 2026-08-01
  - Reuse rule: re-enumerate every `manifest.json`, resolve every `relative_packet_path`, and recompute size and SHA256 before strict reuse
- Source gaps:
  - The acquisition seal proves accounting and integrity, not whether the eventual narrative answers the owner’s real decision well.
  - TikTok is not a full comment census; several retail routes carry typed terminal residuals; `content_unverified` is not source-truth certification.
- Strict-only blockers:
  - missing or changed seal/artifact hash;
  - raw closure failure;
  - any new Deliver artifact;
  - material repository drift that changes authority or evidence;
  - unclear intended Deliver reader or decision when that ambiguity would change the report shape.
- Not-proven boundaries:
  - buyer usefulness of a future Deliver;
  - completeness of every public discussion or review;
  - product-truth adjudication from any single captured source;
  - whether comparison with p10 helps rather than distracts.

## Current Task State

- Completed:
  - Phase A acquisition is sealed with `acquisition_gate: pass`.
  - `pending_job_ids: []`.
  - The last three pending jobs completed: CO1-J10, CO1-J11, and CO3-NATIVE-TT-7527741844298435895.
  - PR #1414 corrected the reusable same-host capture path and amended the historical overclaim.
  - Sender-side seal validation returned `PASS` with no findings.
  - Sender-side raw closure found zero mismatches across 259 manifests and 1,001 declared files.
- Partially completed:
  - Evidence fitness for the owner’s intended Deliver has not been dissected source-by-source in a fresh task.
  - The Deliver audience, decision, structure, comparison posture, and claim ceiling are not yet bound.
- Broken or uncertain:
  - None known in acquisition integrity after the 2026-08-01 audit.
  - Decision usefulness remains intentionally unproven.

## Workspace State

- Branch: `codex/sf-deliver-discussion-handoff-20260801`
- Parent head: `d02e5bebbb26173685773d828ae7df59d55430cb`
- Dirty or untracked state before handoff: clean
- Dirty or untracked state after writing the handoff file: only this new handoff path before commit; clean at dispatch after the packet commit
- Target files or artifacts: this packet only
- Related worktrees or branches:
  - `C:\tmp\forseti-capture-spine-adjudication-20260801` contains the merged PR #1414 tree.
  - The original p11 acquisition worktrees are historical execution roots; do not write to them.

## Changed / Inspected / Tested Files

- This handoff path
  - Status: new durable handoff-only packet
  - Role: cold-reader state transfer
  - Important observations: discussion-only; no Deliver authorization
- Final p11r3 acquisition seal
  - Status: inspected, unchanged
  - Important observations: `SEALED_READY_FOR_DELIVER`, `deliver_allowed: true`, `deliver_started: false`, no pending jobs
- Acquisition record and three specialist returns
  - Status: inspected, unchanged
  - Important observations: hashes match the seal; limitations and diagnostic exclusions remain active
- Raw acquisition roots
  - Status: inspected, unchanged
  - Important observations: all declared files matched size and SHA256 in the sender audit

## Frozen Decisions

- Decision: This receiving task is read-only discussion.
  - Evidence: current user instruction and this packet’s preflight.
  - Consequence: no Deliver artifact, recapture, patch, commit, push, or PR.
- Decision: Phase A terminal accounting remains passing unless confirm-don’t-trust checks find drift.
  - Evidence: final seal plus validator and raw closure.
  - Consequence: do not reopen acquisition merely because the earlier reusable runner had defects.
- Decision: The first p11r3 owned-page pair is diagnostic provenance, not completion evidence.
  - Evidence: CO1 final return.
  - Consequence: inspect only the `owned_pages_direct_http_validated` pair for terminal CO1-J10/J11 evidence.
- Decision: Deliver requires a new explicit commission.
  - Evidence: p11 handoff and the user’s repeated boundary.
  - Consequence: a recommendation to proceed is not execution authority.

## Mutable Questions

- What decision should the Deliver help the owner make?
- Who is the intended reader, and how much source detail should remain visible?
- Should Deliver compare p11 with p10, or should it stand alone?
- Which source families support confident findings, and which support only caveated observations?
- Are CO2’s wrong-market, exact-PDP miss, and Amazon `?th=1` readback residuals relevant to the narrative?
- Does the evidence support a full Deliver, a bounded Deliver, or a narrow acquisition reopen?
- What would count as a useful final output rather than merely a complete synthesis?

## Superseded / Dangerous-To-Reuse Context

- Earlier p11, p11r1, and p11r2 blocked seals:
  - Why stale or dangerous: They preserve interruption provenance but do not describe the final terminal state.
  - Current replacement: p11r3 final acquisition seal.
- First p11r3 owned-page packet pair under `owned_pages_direct_http`:
  - Why stale or dangerous: Full pages were falsely classified from dormant hCaptcha markup and receive no completion credit.
  - Current replacement: `owned_pages_direct_http_validated`.
- First merged capture-spine guarantee claims:
  - Why stale or dangerous: A de-correlated review reproduced admission, header, Retry-After, and partial-summary gaps.
  - Current replacement: PR #1414 at `d02e5beb...` and the amended acquisition record.
- `content_unverified` interpreted as “real content confirmed”:
  - Why stale or dangerous: The classifier explicitly makes no positive content certification.
  - Current replacement: corroborate expected locator, title, body signals, provenance, and source-specific limitations.
- CO2 `status: BLOCKED_TERMINAL` read as unfinished acquisition:
  - Why stale or dangerous: Its accounting has all seven jobs complete with no pending, blocked, or unrun jobs; the label carries typed internal residuals.
  - Current replacement: final seal route accounting plus the CO2 return’s accounting note.

## Commands And Verification Evidence

- Seal validation:
  ```powershell
  python forseti-harness/runners/run_phase_acquisition_seal_validation.py --seal docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/acquisition_seal.md --repo-root .
  ```
  - Passed/failed/not run: passed in sender task
  - Important output: `status: PASS`, `findings: []`
  - Re-run target: receiver checkout at the couriered commit or a clean descendant
- Raw closure:
  - Passed/failed/not run: passed in sender task
  - Important output: p11 `232/933`; p11r1 `11/40`; p11r2 `11/19`; p11r3 `5/9`; zero failures
  - Re-run target: all four raw roots; recompute every declared size and SHA256
- Deliver-artifact check:
  - Passed/failed/not run: passed in sender task
  - Important output: no Deliver-, delivery-, Turn-B-, or Phase-B-named artifact in the p11 repository trees or four raw roots
  - Re-run target: current repository tree and all four raw roots
- PR #1414:
  - Passed/failed/not run: merged with green CI
  - Important output: merge commit `d02e5bebbb26173685773d828ae7df59d55430cb`
  - Re-run target: `git show --stat d02e5bebbb26173685773d828ae7df59d55430cb`

## Blockers And Risks

- Risk: A technically passing seal may still support a weak or unfocused Deliver.
  - Evidence: the seal validates accounting, integrity, and lifecycle state, not user usefulness.
  - Likely next action: bind the intended decision and test each candidate conclusion against cited evidence.
- Risk: Reopening acquisition becomes an easy response to discomfort.
  - Evidence: all required material jobs are complete and raw closure is clean.
  - Likely next action: require a named missing fact and explain how it could change the Deliver before recommending recapture.
- Risk: Internal route residuals become hidden or over-amplified.
  - Evidence: CO2 has wrong-market and exact-PDP residuals; TikTok is not a full census.
  - Likely next action: decide whether each residual changes a conclusion, belongs in limitations, or is irrelevant to the owner’s decision.
- Blocker: None on packet creation. Receiver must still earn `REUSE`.

## Confirm-Don't-Trust Load Checklist

- Re-verify:
  1. Couriered branch/ref and commit resolve, and this packet is readable.
  2. Current repository instructions and overlay do not conflict with this packet.
  3. Final seal canonical hash matches and the seal validator returns no findings.
  4. Acquisition record and CO1/CO2/CO3 return hashes match.
  5. Every declared raw file exists and matches size and SHA256.
  6. No Deliver artifact exists.
  7. Final CO1 packets are the validated pair, not the diagnostic pair.
  8. No current user instruction expands this task from discussion to execution.
- Load outcomes:
  - `REUSE`: all load-bearing facts verified; proceed with evidence dissection and Deliver discussion.
  - `PARTIAL_REUSE`: only optional context drifted; re-derive it and continue with verified evidence.
  - `STALE_REREAD_REQUIRED`: material facts can be re-derived safely but are not current.
  - `BLOCKED_DRIFT`: drift conflicts with authority, evidence integrity, scope, or Deliver state.
  - `BLOCKED_MISSING_PACKET`: packet or couriered revision is unavailable.
  - `BLOCKED_UNVERIFIABLE`: a load-bearing claim cannot be confirmed from available sources.
- Sources to reread if drift is detected:
  - final acquisition seal;
  - acquisition record;
  - affected specialist return;
  - affected raw root;
  - p11 lifecycle boundary in the current handoff.

## Do Not Forget

The next useful act is not to summarize everything acquired. It is to decide what the evidence can honestly support for the owner, then design the smallest Deliver that answers that decision without hiding limitations.
