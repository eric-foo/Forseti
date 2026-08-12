# Success Implement Goal-Conservation Diagnostic 2026-08-12 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency diagnostic record
scope: >
  Records the repeated P1/P4 diagnostic of unchanged Success Implement against
  a budget-neutral pre-decomposition owner-outcome anchor.
use_when:
  - Evaluating whether owner-outcome conservation should change Success Implement.
  - Interpreting the PR #1267 broad-completion failure after the P1/P2/P3 screen.
  - Choosing a later isolated Success Implement quality experiment.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_instruction_budget_causal_screen_2026_08_12_v0.md
  - docs/review-outputs/adversarial-artifact-reviews/success_implement_goal_conservation_diagnostic_adversarial_artifact_review_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A scored finding or metric in this diagnostic is re-adjudicated.
  - A later controlled replay supersedes this mechanism result.
```

## Decision

**Reject P4 and stop after the diagnostic amplifier. Keep Success Implement
unchanged. Do not run the three contrasting exposed cases, create a skill, or
deploy this wording.**

P4 had lower two-run median comparison tokens and wall time, but it was worse
on the study's only target: quality. Across two repetitions of broad feature case
[#1267](https://github.com/eric-foo/forseti/pull/1267), unchanged P1 had accepted
defects `1 critical / 11 major / 1 minor`; P4 had `2 / 13 / 0`. Both P4 runs
still omitted owner obligations and still claimed a narrowed substitute as a
broad completion. The same `missing_required_seam` major-regression family
appeared in both repetitions.

No weighted-severity rescue was applied. Actual billed cost was not observed;
token counters are comparison measures, not billed-cost claims.

## ELI5

We put a label on the original destination before the builder looked at the
code: “Do not swap this destination for an easier one.” In both trials, the
builder still delivered a local-file intake tool in place of the requested
four-provider acquisition capability.

That exact rewrite did not work well enough to keep testing. We cannot tell
whether the new label was ineffective, the nearby compressed wording changed
how the model behaved, ordinary run-to-run variance mattered, or several of
those things happened together. The experiment rejects this complete P4
wording package; it does not isolate the label by itself.

## Frozen arms

| Arm | Method | Normalized-LF bytes | o200k tokens | SHA-256 |
| --- | --- | ---: | ---: | --- |
| P1 | Unchanged tuning-selected Success Implement | 15,483 | 3,110 | `818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383` |
| P4 | P1 with a pre-decomposition owner-outcome anchor and pre-edit boundary comparison | 15,514 | 3,110 | `e8fdcfb451796af4df4c9ce973dc37fe9396c4dbf538d8d6899f47e7d7385a4c` |

P4 was 31 bytes larger (`+0.20%`) and had the same tokenizer count as P1. Its
only *intended* behavioral delta was:

- preserve the owner-visible act and holding condition before repository
  interpretation;
- compare the proposed implementation boundary back to that anchor before
  editing; and
- treat any requested act left as fixture, supplied input, manual work,
  existing partial behavior, or residual as unmet, requiring implementation or
  a lowered claim/status.

Nearby prose was compressed to fund the change. The pre-dispatch audit judged
the existing authority, invariant, signal, falsifier, safety, validation, and
review requirements semantically preserved; P4 added no section, artifact,
checklist, reviewer, checker, second falsifier, or lifecycle step. That audit
did not prove that the exact wording changes were behaviorally inert for a
stochastic model, so the anchor was not component-isolated.

## Design and pre-registered gate

The diagnostic ran two independent randomized P1/P4 repetitions on #1267:
four authored runs, two blind two-way evaluations, and two home adjudications.
Every authored run used `gpt-5.6-sol` at high reasoning in a fresh auth-only
home and a contained exact-parent repository with no refs or remotes. Authored
arms could not see historical patches, hidden oracles, later history, arm
identities, resources, prior repetitions, or peer outputs.

P4 could advance to one P1/P4 pair on #1271, #1301, and #1424 only if it met
all seven conditions: zero criticals; full owner-obligation coverage twice; no
broad collapse twice; pooled lexicographic quality better than P1; no repeated
new major-regression family; and median tokens and time each within 15% of P1.

## Aggregate result

| Arm | Accepted defects C/M/m | Median comparison tokens | Median wall time |
| --- | ---: | ---: | ---: |
| P1 | 1/11/1 | 8,328,878.5 | 1,079.688s |
| P4 | 2/13/0 | 7,134,469 | 1,019.274s |

P4 used `14.34%` fewer median comparison tokens and was `5.60%` faster. Those
resource guards passed, but resources were guards rather than optimization
targets. P4 failed every quality/reliability condition:

- two accepted critical defects, not zero;
- `NOT_ALL_COVERED` in both runs;
- broad completion collapse in both runs;
- pooled quality worse than P1 at the first lexicographic dimension; and
- a repeated `missing_required_seam` major regression.

The pre-registered endpoint is therefore `STOP_AFTER_STAGE_D`.

## Block results

| Repetition | P1 C/M/m | P4 C/M/m | P4 coverage | P4 broad collapse | P4/P1 tokens | P4/P1 wall |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| #1267 r1 | 0/6/1 | 1/7/0 | Not all | Yes | 4,859,852 / 10,202,418 | 704.610s / 1,272.469s |
| #1267 r2 | 1/5/0 | 1/6/0 | Not all | Yes | 9,409,086 / 6,455,339 | 1,333.937s / 886.907s |

The repetitions also show why the median efficiency result cannot rescue the
mechanism. P4 used far fewer tokens and time once and materially more once.
With only two stochastic blocks, the quality failure is decisive while the
direction of the resource effect is unstable. Actual billed cost was not
observed.

## Finding and next boundary

The experiment rejects the **exact frozen P4 wording package** for
`gpt-5.6-sol` at high reasoning on two repetitions of broad feature case #1267.
Both runs failed the pre-registered coverage and collapse gates, so the
protocol-mandated stop is supported. The result does not estimate cross-case
reliability, generalize to other model versions, isolate the anchor from its
companion wording changes, or reject other outcome-conservation mechanisms.
P4's internal failure cause remains undetermined.

No reliable Success Implement improvement has been found *among the mechanisms
tested* across Loss-First, 12 isolated per-axis additions, the P2 placebo,
budget-neutral P3 obligation coverage, and the exact P4 package. Success
Implement remains only the least-disproven incumbent. A later experiment must
introduce a genuinely different causal mechanism rather than another
synonymous reminder; this record selects no next mechanism and creates no
standing process.

## Ranked next hypotheses — experiment only

These are not supported improvements, deployment recommendations, or standing
workflow additions. They are the two smallest mechanisms the adversarial
review found that change the actor's observable environment or authority rather
than merely changing prose.

1. **Controller-owned boundary probe.** Before implementation, freeze one
   solution-neutral black-box check of the owner-visible act. For #1267 it must
   exercise acquisition from provider coordinates, so an already-supplied
   payload or local fixture cannot pass. Compare unchanged P1 with P1 plus that
   probe in two randomized repetitions. Reject the hypothesis if obligation
   coverage and pooled quality do not improve; a more honest incomplete status
   alone is not success. Main risk: the probe can leak the historical solution
   or overfit one boundary.
2. **Immutable owner-obligation state.** Freeze only the distinct owner-visible
   acts before repository interpretation; let the implementer attach direct
   evidence or report an unmet residual, but not rename or delete an obligation.
   Compare this controller-owned state with P1's actor-editable success contract
   on #1267. Reject it if it merely blocks completion without increasing
   implemented coverage, or if accepted defects are no better. Main risk:
   ceremony, false blocking, and solution leakage during obligation extraction.

Neither mechanism has been tested. The first is the cleaner next experiment
because one external boundary observation adds less standing process than a
controller-owned obligation lifecycle.

## Integrity and limits

- All four candidate patches regenerated to their frozen byte counts and
  SHA-256 identities before evaluation; dossier, oracle, base, and gold-diff
  identities also matched.
- Every evaluator finding received a home disposition, and accepted severity
  counts were recomputed from those decisions before aggregation.
- Two P1/P4 mappings were deterministically randomized and hidden from the
  evaluators. Evaluators were same-family, so this is a controlled study audit,
  not different-vendor delegated review.
- Two otherwise successful authored runs did not emit the controller's optional
  parseable final-status token. Their exact patches, validation evidence,
  closeouts, token counters, and durations were retained and scored; neither
  was rerun.
- The aggregate JSON SHA-256 is
  `a75d69d788d5e9b78324cf5abea4e61b41213ba0528b8ce359ca80a6f98a333d`.
  The full packet was freshly readable during the 2026-08-12 adversarial review
  at `C:\tmp\forseti-goal-conservation-evidence-2026-08-12`, but that temporary
  path is not an immutable archive and the aggregate hash is not a packet-wide
  manifest. Durable packet reproducibility is therefore `NOT_PROVEN`.
- No production skill, Forseti-local skill, plugin, package, cache, installed
  copy, or user shadow changed. Stage X did not run.
