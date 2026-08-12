# Success Implement Goal-Conservation Diagnostic Adversarial Artifact Review Prompt v0

```yaml
retrieval_header_version: 1
artifact_role: Review prompt
scope: >
  Read-only adversarial review of the decision-grade P4 goal-conservation
  diagnostic: its evidence accounting, causal claims, stopping decision, and
  evidence-supported directions for a genuinely different next mechanism.
use_when:
  - Auditing the merged P4 diagnostic before using it to choose another Success Implement experiment.
  - Re-running this review against the exact pinned target and evidence packet.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/review-lanes.md
  - .agents/workflow-overlay/prompt-orchestration.md
  - .agents/workflow-overlay/communication-style.md
  - docs/prompts/templates/review/adversarial_artifact_review_v0.md
```

This is a model-neutral prompt artifact. It does not recommend or route a
runtime model.

## Bound review commission

```yaml
forseti_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom_p4_diagnostic_and_frozen_evidence
  output_mode: review-report
  template_kind: adversarial-artifact-review
  edit_permission: docs-write_only_exact_review_report
  review_target: docs/workflows/efficiency/success_implement_goal_conservation_diagnostic_2026_08_12_v0.md
  review_target_commit: e9552a7495b37a858a75496684c435c5c7c4ab75
  review_target_sha256: 2e9d7e9ff70eadbbe5a2cd89a7dcc3f6f453f28102d79eeab5339aa98a4ce09f
  review_target_git_blob: b57f44cf295dedf72f2e7af81166f2c57b153d4d
  workspace: C:\tmp\forseti-si-p4-doc-review
  branch: codex/review-si-p4-diagnostic
  required_review_report_path: docs/review-outputs/adversarial-artifact-reviews/success_implement_goal_conservation_diagnostic_adversarial_artifact_review_v0.md
  prompt_artifact_path: docs/prompts/reviews/success_implement_goal_conservation_diagnostic_adversarial_artifact_review_prompt_v0.md
  findings_first: true
  priority_vocabulary: [critical, major, minor]
  patch_queue_authorized: false
  doctrine_change_decision: no
  dirty_state_checked: yes_by_dispatcher_before_prompt_authorship
  blocked_if_missing:
    - the target bytes do not match the pinned SHA-256 and Git blob
    - the frozen external evidence packet cannot be read
    - workflow-adversarial-artifact-review is unavailable after SOURCE_CONTEXT_READY
```

The review target is read-only. You may create or replace only the exact review
report path named above. Do not edit the diagnostic, evidence packet, indexes,
changelog, skills, runtime state, or any other file. Do not commit, push, open a
PR, or create a patch queue.

## Fitness reference

Goal: leave a decision-grade record that says exactly what the P4 experiment
observed, distinguishes observation from explanation, justifies its stop
decision, and points toward genuinely different improvement mechanisms without
pretending the two-run diagnostic proved more than it did.

Observable success: every material unsupported inference, evidence-accounting
error, scope/generalization error, and next-experiment design gap is reported
with precise evidence and a minimum closure condition. Advisory future
directions are limited to mechanisms that are causally distinct from another
prose reminder and are falsifiable with a smallest sufficient experiment.

## Source pack and read sequence

First classify each source as `full`, `targeted <section>`, `grep <token>`, or
`skip: <reason>`. Under-reading a source that can change a finding is worse than
expanding the read.

1. Load the review method before opening the target:
   `workflow-adversarial-artifact-review` for method only.
2. Load project authority:
   - `AGENTS.md`;
   - `.agents/workflow-overlay/README.md`;
   - `.agents/workflow-overlay/review-lanes.md`;
   - `.agents/workflow-overlay/prompt-orchestration.md`, targeted to Review
     Prompt Defaults and Output Modes;
   - `.agents/workflow-overlay/communication-style.md`, targeted to durable
     review output and adjudication shape;
   - `.agents/workflow-overlay/source-loading.md`, targeted to source budgets.
3. Full-read the review target.
4. Read the frozen P4 evidence needed to verify its load-bearing claims:
   - `C:\tmp\forseti-goal-conservation-evidence-2026-08-12\protocol.md`;
   - `C:\tmp\forseti-goal-conservation-evidence-2026-08-12\integrity\clause-preservation-audit.md`;
   - `C:\tmp\forseti-goal-conservation-evidence-2026-08-12\state\diagnostic-aggregate.json`;
   - both `results\pr-1267-r*-blind-evaluation.md` files;
   - both `results\pr-1267-r*-home-adjudication.md` files.
   Open raw arm records only when a specific target claim cannot be resolved
   from those decision-grade artifacts.
5. Target-read these comparison records only where the diagnostic relies on
   them to define what was already tested or rejected:
   - `docs/workflows/efficiency/success_implement_instruction_budget_causal_screen_2026_08_12_v0.md`;
   - `docs/workflows/efficiency/success_implement_per_axis_mechanism_screen_2026_08_12_v0.md`;
   - `docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md`.
6. Declare `SOURCE_CONTEXT_READY`, frame the boundary problem and failure modes,
   then apply `workflow-adversarial-artifact-review`. Do not formalize findings
   before this point.

## Review attack surface

Attack correctness before prose friction. In particular:

- Recompute or trace all aggregate counts, medians, ratios, stop predicates,
  source identities, and claim ceilings used by the target.
- Separate observed outcomes from causal interpretation. Challenge especially
  any claim that the model "ignored", "reinterpreted", or was harmed by a weak
  anchor unless the evidence actually distinguishes that explanation from
  variance or another mechanism.
- Test whether two repetitions support the report's resource narrative and
  generalization; require explicit scope wherever they do not.
- Test whether `no reliable improvement found` is scoped to the mechanisms and
  cases actually tested, rather than Success Implement improvements generally.
- Test whether the Stage D stop follows the frozen protocol and whether the
  document accurately preserves negative results and residual uncertainty.
- Test whether provenance, retrieval metadata, links, and external-evidence
  pointers let a future reader reproduce the decision without this chat.
- Challenge each suggested next direction: is it a genuinely different causal
  mechanism, or the same instruction expressed with different words?

For at most three ranked advisory mechanism hypotheses, include:

- the specific observed failure family it targets;
- the causal mechanism, stated independently of wording style;
- what changes in the actor's observable state or action, if anything;
- the smallest A/B experiment and decisive falsifier;
- token, latency, ceremony, and quality risks;
- why existing P1-P4 evidence has not already falsified it.

Do not invent a standing checklist, mandatory artifact, review pass, checker,
or lifecycle merely because it could be safer. If no new mechanism is yet
supported, say so.

## Output contract

Write the exact bound report. Start with compact `review_summary` YAML and
record:

- `reviewed_by: unrecorded` and `authored_by: unrecorded` unless launch metadata
  supplies a fact you can observe;
- `de_correlation_bar: same_vendor_sanity`;
- `same_vendor_rationale: bounded adversarial sanity only; no cross-vendor or no-new-seam claim`;
- the target commit, target SHA-256, access mode, and review status.

List findings first, ordered critical, major, minor. Every finding must include
severity, confidence, location, issue, evidence, impact,
`minimum_closure_condition`, `next_authorized_action`, and an advisory
correction direction. Report all in-scope findings; home adjudication filters
them. Do not include a patch queue.

Then include:

- `considered_and_defended`, one line for each candidate issue defeated by its
  strongest steelman, or `none`;
- `ranked_mechanism_hypotheses`, bounded as above;
- one-line read-budget audit;
- this review-use boundary: the report is decision input only, not approval,
  validation, product proof, mandatory remediation, or executor authority.

If the exact report cannot be written, return a blocked result and do not imply
that chat output substituted for the durable report.
