# Forseti Workflow Efficiency

This directory is the front door for reusable Forseti workflow and tool
efficiency material: methods, fixed cases, measurements, and dogfood records.
It does not own workflow doctrine, product behavior, validation status, or a
claim that any documented result has been reproduced.

## Route by need

| Need | Open |
| --- | --- |
| Read the 2026-09-05 repository efficiency audit, measured local costs, and revalidated change candidates | `forseti_repo_efficiency_audit_2026_09_05_v0.md` |
| Follow the active five-fix tool-calling improvement sequence and its dogfood gates | `tool_calling_efficiency_improvement_sequence_2026_07_15_v0.md` |
| Run the fixed cold-agent vendor-admission tool-calling case | `tool_calling_dogfood_case_v0.md` |
| Review the observed 2026-07-15 three-run baseline and efficiency diagnosis | `tool_calling_dogfood_run_2026_07_15_v0.md` |
| Compare an in-session Success Implement review with a strict cross-vendor delegated review-and-patch on PR #1111 | `pr1111_success_implement_vs_delegated_review_case_v0.md` |
| Review the 100-PR backtest that admitted a scoped cold-operability signal and rejected a universal dogfood protocol | `cold_operability_signal_pr_backtest_2026_08_07_v0.md` |
| Review the frozen backtest that met its recall bar but failed its false-flag bound and declined the falsifiable-invariant authoring clause | `architecture_falsifiable_invariant_backtest_2026_08_08_v0.md` |
| Review the frozen aggregation showing delegated review-and-patch episodes paid at 10/11, the lane's bound status supported, and the open-commission triage that found no backlog | `delegated_review_patch_yield_backtest_2026_08_08_v0.md` |
| Review the 12-case tuning plus 24-case confirmatory comparison that returned NO_WIN for Success Implement versus the Full Chain | `success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md` |
| Review the post-hoc three-way replay where Loss-First saved tokens, Full Chain had the lowest latency, and Success Implement's reported quality lead depends on that replay's post-hoc three-way scorer | `loss_first_implement_36_case_posthoc_backtest_2026_08_11_v0.md` |
| Review the per-axis screen where none of 12 narrow Success Implement additions cleared its frozen Stage 1 gate and no combination was tested | `success_implement_per_axis_mechanism_screen_2026_08_12_v0.md` |
| Review the repeated P1/P2/P3 causal screen that supported baseline variance, did not support append interference, and stopped budget-neutral obligation coverage at Stage A | `success_implement_instruction_budget_causal_screen_2026_08_12_v0.md` |
| Review the repeated P1/P4 diagnostic that rejected the exact budget-neutral owner-outcome wording package after it worsened quality despite lower two-run median resources | `success_implement_goal_conservation_diagnostic_2026_08_12_v0.md` |
| Review the repeated controller-boundary-probe diagnostic that stopped after E1 failed coverage, completion-collapse, and executable-probe gates twice | `success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md` |
| Review the three-repetition transparent-acceptance diagnostic where E2 passed the exact provider request three times but was rejected after broad-completion collapse repeated three times | `success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md` |
| Review the three-repetition fresh-context completion-admission diagnostic where every checker wrongly approved an incomplete #1267 patch and caused no continuation or patch change | `success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md` |
| Review the severity-ruler reproducibility pass and the completed identical-method screen that found high quality, token, and latency variance | `success_implement_measurement_calibration_2026_08_13_v0.md` |
| Review the 24-run matched screen where an 11% clause-preserving Success Implement trim improved accepted quality but failed token and wall-time gates | `success_implement_hot_path_trim_screen_2026_08_13_v0.md` |
| Trace current owners and cited material history for named Forseti actor/workflow behavior contracts | `forseti_behavioral_contract_changelog_v0.md` |
| Record an observed recurring tooling or workflow failure and its corrective pointers | `../technical_difficulties_log_v0.md` |
| Follow the dated 2026-07-09 hygiene-audit checklist and its execution waves | `../../hygiene/efficiency_audit_wave_plan_v0.md` |

## Ownership boundary

- **Technical Diagnostics** is the append-only record for observed recurring
  tooling or workflow failures, their impact, and corrective pointers.
- **This efficiency surface** holds reusable efficiency methods, cases,
  measurements, and dogfood records. Each child artifact owns only the case or
  method it defines.
- **The efficiency-audit wave plan** is a dated hygiene tracking checklist. It
  does not own this directory or general workflow/tool efficiency practice.

Currentness is per child artifact. On conflict, open the linked owning source;
this README is a directory router, not independent authority. For the current
fixed case, open `tool_calling_dogfood_case_v0.md` next.
