# Success Implement Instruction-Budget Causal Screen 2026-08-12 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency causal-screen record
scope: >
  Records the randomized repeated P1/P2/P3 screen of unchanged Success
  Implement, an inert appended placebo, and budget-neutral obligation coverage.
use_when:
  - Evaluating whether obligation coverage should change Success Implement.
  - Distinguishing baseline variance from append-only instruction interference.
  - Designing a later implementation-method experiment after this Stage A stop.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_per_axis_mechanism_screen_2026_08_12_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
  - docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md
stale_if:
  - A scored finding or metric in this screen is re-adjudicated.
  - A later untouched holdout supersedes this causal screen.
```

## Decision

**Stop after Stage A. Keep the tuning-selected Success Implement source
unchanged. Reject P3, do not run Stages B or C, and do not deploy or create a
new skill from this study.**

P3 reduced the pooled critical count, but it did not solve the failure it was
designed to solve. Both P3 runs on broad feature case
[#1267](https://github.com/eric-foo/forseti/pull/1267) still omitted several
owner obligations and still presented a narrowed implementation as complete.
P3 also introduced repeated major-regression families across cases. Its median
tokens and time stayed within the 15% guards, but both were higher than P1.

No weighted-severity rescue was applied. Actual billed cost was not observed;
token counters are comparison measures, not billed-cost claims.

## Arm disposition and current conclusion

- **P1 — retain only as the incumbent control.** P1 is the unchanged current
  Success Implement source. It remains the least-disproven operating choice
  because no tested candidate reliably improved it, not because this screen
  validated it. Its two #1267 collapses are a material reliability warning.
- **P2 — reject.** P2 is deliberately inert and supplies no behavior worth
  adopting. Its lower critical count cannot be attributed to a mechanism;
  baseline variance was observed, while P2 added 5.5% median tokens, 32.2%
  median time, and more major/minor defects than P1.
- **P3 — reject.** P3 failed its diagnostic obligation and repeated-regression
  gates despite a lower pooled critical count.

**No reliable improvement to Success Implement has been found.** The current
evidence rejects the tested appended, per-axis, Loss-First, and budget-neutral
obligation-coverage changes as replacements. Success Implement remains the
least-disproven incumbent, not a proven optimum.

**Subsequent diagnostic:** the budget-neutral owner-outcome-conservation
hypothesis named below was later tested twice on #1267 and rejected. It was
cheaper and slightly faster in median but worse on pooled quality; both runs
still collapsed the owner outcome. See
[`success_implement_goal_conservation_diagnostic_2026_08_12_v0.md`](success_implement_goal_conservation_diagnostic_2026_08_12_v0.md).

## ELI5

We wanted to know why adding a sensible reminder had previously made the
builder worse. Was the builder simply inconsistent? Was any extra paragraph a
distraction? Or was the reminder itself bad?

The answer is mostly **inconsistency, not paragraph length**. The unchanged
instructions also failed the big case in both repeats. Adding a harmless
paragraph did not create a clean new failure pattern, so “extra text caused
it” is not supported. Rewriting the instructions to fit the reminder into the
same space produced fewer catastrophic misses overall, but it still failed the
exact big-case obligations twice and made more serious ordinary mistakes. It
was a different failure mix, not a reliable improvement.

## Frozen arms and design

The exact normalized-LF sources were frozen before dispatch:

| Arm | Method | Bytes | o200k tokens | SHA-256 |
| --- | --- | ---: | ---: | --- |
| P1 | Unchanged tuning-selected Success Implement | 15,483 | 3,110 | `818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383` |
| P2 | P1 plus an inert, shape-matched 505-byte placebo | 15,988 | 3,205 | `65b29749a7884981466ed352b78cebfd28b6cae7bd5a65aa1e6f373433239a49` |
| P3 | Budget-neutral obligation-to-seam-to-evidence mapping | 15,463 | 3,102 | `12efb49eec35ee65e54b9ba939ddc1b619b9074955f1d08397c9bbcc19c675c8` |

P3 was 20 bytes and eight tokenizer tokens smaller than P1. A pre-dispatch
clause audit found obligation coverage to be its only behavioral delta; all
existing authority, invariant, signal, falsifier, safety, validation, and
review requirements remained.

Stage A used two independent randomized repetitions per arm on:

- feature/system [#1267](https://github.com/eric-foo/forseti/pull/1267);
- mechanical/local [#1271](https://github.com/eric-foo/forseti/pull/1271);
- stateful/cross-module [#1301](https://github.com/eric-foo/forseti/pull/1301); and
- review hardening [#1424](https://github.com/eric-foo/forseti/pull/1424).

That produced 24 authored runs, eight blind three-way evaluations, and eight
home adjudications. Every authored run used `gpt-5.6-sol` at high reasoning in
a fresh auth-only home and a contained exact-base repository with no refs or
remotes. Authored arms could not see historical patches, hidden oracles, later
history, arm identities, resources, prior repetitions, or peer outputs.

## Aggregate result

Quality is the frozen lexicographic `critical → major → minor` vector. Lower is
better.

| Arm | Accepted defects C/M/m | Median comparison tokens | Median wall time | Versus P1 |
| --- | ---: | ---: | ---: | --- |
| P1 | 3/10/1 | 5,457,988 | 804.649s | Control |
| P2 | 2/15/4 | 5,760,476.5 | 1,063.641s | Fewer criticals, more majors/minors, 5.5% more tokens, 32.2% slower |
| P3 | 1/17/4 | 5,621,782 | 859.477s | Lexicographically better, but 70% more majors, 3.0% more tokens, 6.8% slower |

P3 therefore passed the pooled lexicographic-quality comparison and both 15%
resource guards. It nevertheless failed the non-negotiable reliability gates:

- one accepted critical defect remained;
- both #1267 repetitions had `NOT_ALL_COVERED` owner obligations;
- both #1267 repetitions had broad completion collapse;
- `missing_required_seam` major regressions repeated across #1301 and #1424;
- `omitted_owner_obligation` major regressions repeated across #1267 and #1424.

Passing three gates cannot compensate for failing four. The pre-registered
endpoint is `STOP_AFTER_STAGE_A`.

## Causal finding

### Baseline variance: supported

P1 itself produced broad completion collapse in both #1267 repetitions. That
meets the pre-registered support condition and shows the earlier Q1 collapse
was not uniquely caused by the added obligation wording.

This does not mean the baseline is good. It means one run of a stochastic
model was too weak a basis for blaming the new clause.

### Append interference: not supported

Both P2 #1267 runs also collapsed, but the causal rule required both P1 runs
not to collapse. They did. P2 was worse in aggregate resources and ordinary
defects, but this experiment does not support the specific claim that the
505-byte inert append caused the broad-completion failure.

### Budget-neutral obligation coverage: rejected

P3 changed the severity distribution rather than fixing completion. It cut
critical defects from three to one, which is why it wins the pooled
lexicographic comparison, but majors rose from ten to seventeen. More
importantly, it failed the two repeated #1267 obligations it explicitly aimed
to protect. A reminder that names obligations is not enough if the receiver
can still narrow the goal before constructing those obligations.

The smallest defensible conclusion is: **instruction budget was not the main
problem demonstrated here, and this obligation-coverage wording is not a
reliable cure.** A later hypothesis should target how the goal is bound before
decomposition, not add or reshuffle more standing clauses without a new causal
mechanism.

## Historical next quality-axis hypothesis: conserve the owner outcome before decomposition

The strongest remaining hypothesis is not another obligation list. It is one
earlier mechanism: freeze a lossless owner-outcome anchor before repository
interpretation, then prevent later implementation choices from narrowing it.

The candidate behavior would be:

1. Before source exploration can redefine the task, preserve the requested
   owner-visible act and the condition under which it must hold.
2. Treat fixtures, operator-supplied inputs, manual prerequisites, existing
   partial code, and unavailable live state as evidence or residual facts;
   none may silently replace a requested production capability.
3. Before a complete claim, compare the implementation boundary back to that
   anchor. If a requested act became supplied input, fixture-only behavior,
   manual work, or a residual, the claim stays incomplete.

This differs from P3 at the decisive point. P3 mapped obligations from the
model-authored `Goal`; in #1267 that goal had already been narrowed from
four-vendor acquisition to local-payload ingestion. Goal conservation would
make the owner request, not the model's summary, the comparison anchor.

At this screen's close, this was a plausible quality-axis hypothesis rather
than a validated improvement. The subsequent P1/P4 diagnostic tested it alone
and budget-neutrally, with quality as the target and tokens/latency as guards;
P4 failed and was rejected. A claim-honesty-only rule remains insufficient
because it would label incomplete work correctly without making the
implementation complete.

## Block results

| Case/repetition | P1 C/M/m | P2 C/M/m | P3 C/M/m | P3 coverage / collapse |
| --- | ---: | ---: | ---: | --- |
| #1267 r1 | 1/3/1 | 1/3/1 | 1/3/1 | Not all / yes |
| #1267 r2 | 1/3/0 | 0/4/1 | 0/4/2 | Not all / yes |
| #1271 r1 | 0/0/0 | 0/0/0 | 0/0/0 | All / no |
| #1271 r2 | 0/1/0 | 0/0/0 | 0/0/0 | All / no |
| #1301 r1 | 0/0/0 | 0/1/0 | 0/1/0 | Not all / no |
| #1301 r2 | 0/2/0 | 0/1/1 | 0/3/0 | Not all / no |
| #1424 r1 | 0/1/0 | 0/5/0 | 0/3/0 | Not all / yes |
| #1424 r2 | 1/0/0 | 1/1/1 | 0/3/1 | Not all / yes |

## Integrity and limits

- All 24 raw patches, four copied dossiers/oracles, and four historical gold
  diffs regenerated exactly before evaluation.
- All evaluator findings received a home disposition and all accepted counts
  recomputed exactly.
- One P1 #1424-r2 receiver self-blocked after attempting `git log --all`.
  Its contained repository had zero refs/remotes, so no later history was
  exposed. Its empty-patch outcome was retained and scored; no rerun occurred.
- The outer shell stopped waiting during the final P3 run, but the original
  controller and exact session remained live and completed; no replacement
  session occurred.
- Evaluators were anonymous but same-family. This is a controlled study audit,
  not different-vendor delegated review.
- The active aggregate SHA-256 is
  `51fabe628d855a8f846e5b64e70d19a02cb775bbe7b57ddaa581f300e79ca95e`.
  Full run evidence is preserved outside merged navigation at
  `C:\tmp\forseti-p123-evidence-2026-08-12`.
- No production skill, Forseti-local skill, plugin, package, cache, installed
  copy, or user shadow changed. Stages B and C did not run.
