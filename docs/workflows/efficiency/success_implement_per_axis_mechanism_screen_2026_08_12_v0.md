# Success Implement Per-Axis Mechanism Screen 2026-08-12 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency mechanism-screen record
scope: >
  Records the exposed-corpus latency, token, and quality screens of narrow
  additions to the tuning-selected Success Implement method.
use_when:
  - Evaluating whether any tested per-axis mechanism should change Success Implement.
  - Designing the next causal test after the per-axis screen returned no winner.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A scored finding or metric in this screen is re-adjudicated.
  - A later controlled comparison supersedes this mechanism screen.
```

## Decision

**Keep the tuning-selected Success Implement source unchanged. None of the 12
tested additions advances. Do not create, combine, or deploy a new skill from
this screen.**

Testing one axis at a time was the right correction. It showed that the
apparently sensible additions did not compose into a stronger method because
none first survived alone:

- all four latency mechanisms failed at least one frozen advancement gate;
- all four token mechanisms introduced one or more critical defects and were
  lexicographically worse than their common control;
- all four quality mechanisms introduced a critical defect and were
  lexicographically worse than their common control;
- therefore Stage 2, cross-axis combination, and a fresh confirmatory holdout
  did not run.

Actual billed cost was not observed. Token counters are comparison measures,
not billed-cost claims.

## ELI5

We tried improving the car by changing one thing at a time: make it quicker,
make it use less fuel, or make it safer. Some changes used less fuel, but every
candidate either missed its target or made the car less safe. So we keep the
original car. The next useful test is not another accessory; it is checking
whether merely adding more instructions distracts the driver.

## Frozen method and corpus

`S0` was the exact tuning-selected Success Implement champion, normalized to
LF. The latency screen used 12 exposed historical cases, two per stratum:

| Stratum | Cases |
| --- | --- |
| Mechanical/local | `#1271`, `#1361` |
| Bounded fixes | `#1275`, `#1400` |
| Stateful/cross-module | `#1301`, `#1317` |
| Feature/system | `#1267`, `#1280` |
| Review hardening | `#1424`, `#1434` |
| Doctrine/workflow | `#1315`, `#1435` |

Token and quality Stage 1 used the first case in each stratum: `#1271,
#1275, #1301, #1267, #1424, #1315`. Every arm began at the exact historical
base in an independent repository, received the same solution-free dossier,
and was hidden from the oracle, historical implementation, peer outputs, later
history, and study conclusions. Anonymous same-family evaluators proposed
findings; home adjudicators accepted or rejected every finding. This is a
mechanism screen and regression record, not a fresh holdout or a
different-vendor delegated review.

The full frozen contracts and byte identities are preserved in the local
run-scoped evidence root
`.workflow-runs/per-axis-implementation-2026-08-11/`. That operational corpus
is not a merged Forseti navigation surface; this report carries the durable
decision-grade aggregate.

## Latency axis: no advancing arm

Each arm appended exactly one narrow operating rule to `S0`:

| Arm | Mechanism | Defects C/M/m | Median token ratio | Median wall ratio | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| S0 | Unchanged control | 1/7/7 | 1.000 | 1.000 | Control |
| L1 | Implement before bespoke proof construction | 1/17/4 | 0.853 | 0.891 | Rejected: worse quality and repeated feature/system majors |
| L2 | Consolidate equivalent near-miss variants | 0/11/5 | 0.715 | 0.940 | Rejected: missed the 10% speed bar and repeated feature/system majors |
| L3 | Batch independent validation invocations | 2/11/7 | 0.670 | 1.121 | Rejected: new critical, worse quality, and slower |
| L4 | Do not rerun unchanged successful checks | 1/12/7 | 0.850 | 0.958 | Rejected: worse quality and missed the speed bar |

Ratios below `1.0` are lower than `S0`. The active corrected aggregate is
`results/latency-axis-aggregate-v2.json` inside the run-scoped evidence root.
It supersedes the provisional aggregate. Four original records that observed
post-base history were excluded and replaced by contained exact-base replays
before the active result was computed.

## Token axis Stage 1: no advancing arm

| Arm | Mechanism | Defects C/M/m | Median token ratio | Median wall ratio | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| S0 | Unchanged common control | 0/5/4 | 1.000 | 1.000 | Control |
| T1 | Bound broad observation before reading | 1/9/5 | 0.990 | 1.052 | Rejected: new critical, worse quality, and missed token bar |
| T2 | Reuse unchanged evidence in-run | 2/8/5 | 0.879 | 0.821 | Rejected: two new criticals and worse quality |
| T3 | Load more sources only for a named unresolved question | 2/8/3 | 0.851 | 0.890 | Rejected: two new criticals and worse quality |
| T4 | Use concise output for successful validation | 1/11/5 | 0.961 | 0.926 | Rejected: new critical, worse quality, and missed token bar |

The controlling run-scoped evidence is
`results/token-axis-stage1-aggregate.json`.

## Quality axis Stage 1: no advancing arm

| Arm | Mechanism | Defects C/M/m | Median token ratio | Median wall ratio | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| S0 | Unchanged common control | 0/8/2 | 1.000 | 1.000 | Control |
| Q1 | Map owner obligations to seams and evidence | 1/9/2 | 0.955 | 0.859 | Rejected: new critical and worse quality |
| Q2 | Trace applicable cross-boundary seams | 1/10/2 | 0.938 | 0.887 | Rejected: new critical and worse quality |
| Q3 | Challenge the highest-risk state transition | 1/13/1 | 1.041 | 0.843 | Rejected: new critical and worse quality |
| Q4 | Reconcile obligations and interfaces against the diff | 1/14/1 | 0.978 | 0.868 | Rejected: new critical and worse quality |

The controlling run-scoped evidence is
`results/quality-axis-stage1-aggregate.json`.
The token and quality screens used separate blind-evaluation packets, so their
control defect totals are decision-local and must not be merged.

## What the common failure suggests

All eight token and quality additions independently failed the same broad
feature/system case, [PR #1267](https://github.com/eric-foo/forseti/pull/1267),
with a new accepted critical defect. In that case, `S0` authored a
104,628-byte patch. The eight appended candidates authored patches between
27,000 and 39,241 bytes and left substantial required behavior unimplemented.

That concentration supports a stronger hypothesis: **standing additions may
dilute the implementation-completeness signal and encourage premature
narrowing on broad work.** It does not prove that explanation. The screen has
no repeated-`S0` variance control and no inert length-matched placebo, so the
same pattern could still be ordinary model variance or a case-specific effect.

## Stronger next hypothesis: instruction-budget interference

Do not test another three-axis bundle. First run a small causal screen on the
exposed corpus:

1. **P0 — replication control:** two fresh exact-`S0` runs per case. This
   estimates whether `S0` itself sometimes collapses to the same incomplete
   shape.
2. **P1 — inert appended placebo:** append non-behavioral text matched to the
   candidate's length, position, and formatting. If P1 degrades while P0
   holds, added instruction load or placement is the likely cause.
3. **P2 — budget-neutral integration:** install one mechanism only by replacing
   or compressing existing overlapping text, keeping total source length
   approximately constant. If P2 holds while P1 fails, integration rather
   than append-only growth is the promising route.

Start with the failure amplifier `#1267` and three contrasting exposed cases:
`#1271` (mechanical), `#1301` (stateful), and `#1424` (review hardening).
Pre-register exact sources and thresholds before dispatch. Only a P2 mechanism
that preserves quality and improves its named resource axis should receive the
remaining exposed cases; only then should a frozen candidate see a new
untouched holdout.

This design can distinguish variance, instruction-load interference, and
mechanism value. The current screen cannot. Until that test exists, `S0`
remains the least disproven method and the smallest complete operating choice.

## Integrity and disposition

- The latency aggregate was corrected only after excluding four
  history-exposed records and running contained replacements.
- All 48 downstream token/quality authored patches regenerated exactly from
  their retained repositories; all 12 downstream blind evaluations and 12
  home adjudications completed.
- Controller transport/preparation failures that occurred before model action
  were corrected without scoring a run. No failed or contaminated record is
  active evidence.
- Stage 2 and combination were not omitted for convenience: the frozen design
  forbade them when Stage 1 selected no candidate.
- No Success Implement, Forseti-local skill, plugin, package, cache, or user
  shadow is changed by this study.

The run-scoped
`integrity/downstream-stage1-artifact-adjudication.md` records the active
evidence boundary.
