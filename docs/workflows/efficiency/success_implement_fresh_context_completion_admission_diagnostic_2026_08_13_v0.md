# Success Implement Fresh-Context Completion-Admission Diagnostic 2026-08-13 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency diagnostic record
scope: >
  Records the three-repetition PR #1267 comparison of unchanged Success
  Implement with the same method followed by one fresh completion-admission
  check and at most one return to the original builder.
use_when:
  - Evaluating whether a fresh completion checker should follow complex Success Implement work.
  - Interpreting the repeated PR #1267 premature-completion failure.
  - Designing a cheaper follow-on test of completion admission.
authority_boundary: retrieval_only
open_next:
  - docs/review-outputs/adversarial-artifact-reviews/success_implement_fresh_context_completion_admission_diagnostic_adversarial_artifact_review_v0.md
  - docs/workflows/efficiency/success_implement_transparent_acceptance_example_diagnostic_2026_08_12_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
  - AGENTS.md
stale_if:
  - A scored finding, completion decision, or metric in this diagnostic is re-adjudicated.
  - A later controlled replay supersedes this mechanism result.
```

## Decision

**Reject E3. Keep Success Implement unchanged and do not install a standing
fresh-context completion check.**

The check approved all three incomplete treatment patches. Oracle-backed
decision adjudication said all three approvals should instead have been
`CONTINUE`. Because every check returned `ADMIT_COMPLETE`, no builder received
the planned continuation and every E3 final patch was byte-identical to its
initial patch. The mechanism therefore caused zero implementation change.

E3's initial builders happened to have a lower pooled weighted-harm score,
median token count, and median active-phase time than the fresh P1 builders.
Those differences are ordinary model variance, not E3 gains: they existed
before the check and the check changed no bytes. The pre-registered gate also
failed on E3 critical defects, checker accuracy, broad-completion collapse, a
repeated `missing_required_seam` major regression, and a frozen end-to-end
latency condition that became `NOT_OBSERVED` after the controller repair.

Because both initial builders used unchanged Success Implement and the checker
changed zero bytes, the P1/E3 initial difference is also A/A measurement
evidence: accepted criticals differed `3` versus `1`, weighted harm differed
`111` versus `80`, median comparison tokens differed by `41.04%`, and median
active wall differed by `28.04%`. Those initial implementation-quality
differences are non-causal and cannot count as checker harm or baseline
strength. They warn that earlier two- or three-run candidate deltas may sit
inside an unmeasured noise floor. The later measurement-calibration record
passed a fixed-assertion severity screen and then completed the required
three-draw builder stage. It found major-tier quality variation in three of
four cases, token spread above 15% in three, and wall-time spread above 15% in
all four.

Actual billed cost was `NOT_OBSERVED`. Token counters are comparison measures,
not billed-cost claims.

## ELI5

We hired a second person to ask, “Is the whole job really finished?”

But the second person looked at the builder's smaller version of the job and
said yes three times. Later, a judge compared those answers with the original
job and found missing work every time. Since the second person never said “go
back,” the builder never fixed anything.

Fresh eyes were not enough in this design. Each checker derived a smaller list
of obligations that matched its builder's narrowed story. Seeing the patch and
closeout before fixing that list is one plausible reason, but this experiment
did not isolate the cause.

## Frozen intervention

The diagnostic ran three randomized P1/E3 repetitions on
[#1267](https://github.com/eric-foo/forseti/pull/1267).

| Arm | Initial implementation | Post-closeout behavior |
| --- | --- | --- |
| P1 | Exact unchanged tuning-selected Success Implement | Stop after normal implementation and validation closeout |
| E3 | The same exact source and author contract | A fresh read-only checker sees the solution-free request, initial patch, validation, residuals, and closeout; `CONTINUE` permits one same-session builder continuation, while `ADMIT_COMPLETE` stops |

Both arms used the same normalized-LF Success Implement source: `15,483`
bytes, SHA-256
`818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383`.
Initial P1 and E3 builders received byte-identical method and case instructions
with the same neutral method label. Treatment began only after E3's initial
patch and closeout froze.

Every authored run used `gpt-5.6-sol` at high reasoning in a fresh auth-only
home and a contained repository at exact parent
`12c1469e07bc49aae8d1216846cb715ab069c592`, with no refs or remotes.
Historical patches, hidden oracles, later history, arm identities, peer
outputs, and resources were withheld. The fresh checker also saw no oracle or
historical solution.

The full raw evidence is retained outside the merged navigation surface at
`C:\tmp\forseti-e3-completion-admission-evidence-2026-08-13`.

## Pre-registered gate

E3 could advance only if it had zero accepted criticals; every completion
decision was correct; all three final E3 patches avoided broad completion
collapse; pooled weighted harm was lower than P1; no new major regression
family repeated twice; and median tokens and end-to-end latency were each no
more than 25% above P1.

The diagnostic used the owner-requested comparison convention
`25*critical + 5*major + minor`. Raw severity counts remain primary evidence;
the weighting is an owner preference, not a general conversion law.

## Aggregate result

| Arm | Accepted defects C/M/m | Weighted harm | Median comparison tokens | Median active-phase wall |
| --- | ---: | ---: | ---: | ---: |
| P1 | `3/7/1` | `111` | `9,838,750` | `1,107.234s` |
| E3 | `1/11/0` | `80` | `5,801,288` | `796.719s` |

E3 used `41.04%` fewer median comparison tokens and `28.04%` less median
active-phase wall time. These are descriptive differences between the initial
stochastic builder runs. They are not causal benefits of the completion check,
which approved every patch and caused no continuation or patch change.

| Advancement condition | Result |
| --- | --- |
| Zero E3 accepted criticals | **Fail** — one |
| Every completion decision correct | **Fail** — zero of three |
| All three final E3 patches avoid broad completion collapse | **Fail** — final home adjudication found collapse in repetitions 1 and 3 |
| E3 weighted harm below P1 | Pass — `80 < 111` |
| No repeated new E3 major-regression family | **Fail** — `missing_required_seam` regressed in repetitions 1 and 3 |
| Median tokens within +25% | Pass |
| Median end-to-end wall within +25% | **Not observed; cannot pass** — the preserved controller repair interrupted E3 end-to-end timing |

The frozen endpoint is `E3_REJECTED`.

## Repetition results

| Repetition | P1 C/M/m | E3 C/M/m | Checker | Correct decision | P1 / E3 tokens | P1 / E3 active wall |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| r1 | `1/3/1` | `1/4/0` | `ADMIT_COMPLETE` | `CONTINUE` | `9,838,750 / 5,801,288` | `992.563s / 772.157s` |
| r2 | `1/1/0` | `0/1/0` | `ADMIT_COMPLETE` | `CONTINUE` | `9,161,497 / 7,260,763` | `1,107.234s / 1,218.783s` |
| r3 | `1/3/0` | `0/6/0` | `ADMIT_COMPLETE` | `CONTINUE` | `9,958,882 / 5,771,423` | `1,379.500s / 796.719s` |

The checkers themselves used `24,824`, `34,863`, and `26,337` comparison
tokens and `35.078s`, `36.079s`, and `25.422s`. Those costs are included in
E3 totals. No continuation ran.

## What failed and why

The checker was independent from the builder, but all three checker returns
echoed a smaller task definition found in their corresponding patches and
closeouts:

- r1 treated capture of one known posting page as the requested four-provider
  board-capture capability;
- r2 treated one Workday list page as complete Workday capture despite missing
  pagination and detail requests; and
- r3 treated one operator-supplied response per provider as complete board
  capture, again omitting Workday traversal, detail capture, and projection.

The exact fresh-check design therefore did not prevent the builder's narrowed
success framing from carrying into the admission decision. Patch/closeout
anchoring is one plausible mediator because the checker derived obligations
after receiving both. The study did not compare before-patch versus after-patch
derivation, so task evidence, claim calibration, evaluator framing, ordinary
judgment variance, or another mediator remain possible.

This result does **not** show that independent review is useless. It rejects
this exact one-pass completion-admission design, whose checker derived
obligations after seeing the candidate patch and had no separately frozen
pre-patch obligation anchor.

## Scoring disagreement retained

The final-patch home adjudicator classified E3 repetitions 1 and 3 as broad
completion collapse and repetition 2 as incomplete but not broad collapse.
The separate completion-decision adjudicator classified all three as broad
collapse. This diagnostic does not erase that same-family judgment variance.

It does not change the completion decision: both scoring routes found
meaningful owner-requested Workday behavior absent in repetition 2, and the
frozen checker contract required `CONTINUE` for any meaningful missing or
unknown owner obligation. All three `ADMIT_COMPLETE` decisions were therefore
wrong under the tested contract.

## Unranked low-cost sensitivity screen

If the owner wants another probe, one low-cost candidate is an
**obligation-first blinded check**:

1. Before seeing any patch or closeout, a fresh actor reads only the original
   request and permitted pre-implementation authority and freezes the smallest
   owner-visible obligation set.
2. Only then does the same actor receive an already-frozen candidate patch and
   validation evidence and decide `ADMIT_COMPLETE` or `CONTINUE` against that
   unchanged set.
3. First test only whether the staging change makes the checker reject the
   existing frozen incomplete patches without inventing obligations. Run no
   builders or continuations for that sensitivity screen.

That probe would test sensitivity to staging, not establish why E3 failed,
admission accuracy, false-continue behavior on complete work, or adoption
economics. A real accuracy study would need both incomplete and complete
opportunities plus an explicit process-cost bound. This candidate is unranked,
untested, and not selected or authorized by the E3 result. It is named because
it reuses frozen patches and installs no standing obligation artifact or
Success Implement change.

## Integrity and limits

- All six final patches regenerated to their frozen identities before blind
  evaluation; every proposed evaluator finding received a home disposition.
- Every E3 final patch matched its frozen initial patch byte-for-byte.
- Exact evaluator prompt bytes and hashes were retained. Direct P1/E3 path
  strings and some markdown-shaped method labels survived scrubbing in every
  dispatched evaluator packet, so evaluator and home-adjudicator arm blindness
  is false, not merely unproven. The counts remain traceable same-family study
  judgments, but comparative quality, weighted-harm, collapse, and regression
  claims are de-blinded evidence. Whether the leak changed any judgment is
  `NOT_PROVEN`.
- The first checker launches were rejected before a model turn because the
  controller omitted `--skip-git-repo-check` in an empty directory. Empty event
  streams and stderr were preserved. One corrected launch per checker used a
  fresh auth-only home; no authored implementation was rerun.
- Active-phase wall sums builder, checker, and any continuation time. The
  external controller-repair pause is excluded, so exact uninterrupted E3
  end-to-end latency is `NOT_OBSERVED` and its pre-registered gate fails.
- Two home findings used out-of-contract failure-family names; analysis
  normalized them to `other` without changing severity or accepted counts.
- Same-family blind evaluation and adjudication are controlled study audits,
  not different-vendor delegated review.
- The aggregate JSON SHA-256 is
  `2d5ab6e20bb69460fb947ecbfd0eca22ca3ff7f584910d2fb20c90f9dfd96dd6`.
- One exposed historical case and three stochastic repetitions do not establish
  transfer to other tasks, models, or completion surfaces.
- No production skill, Forseti-local skill, plugin, package, cache, installed
  copy, user shadow, or current workflow authority changed.

## Adversarial review adjudication

The same-vendor advisory review independently reproduced every patch identity,
accepted count, weighted score, token and active-phase wall median, ratio,
checker decision, and frozen endpoint. It proposed three findings; home
adjudication accepted and patched all three:

- `AR-01`: exact evaluator packets retained P1/E3 paths and some method-label
  forms, so arm blindness is false and comparative scoring is bounded as
  de-blinded same-family evidence;
- `AR-02`: the frozen latency condition is one end-to-end condition whose value
  became `NOT_OBSERVED`, not an active-phase pass plus a new eighth gate; and
- `AR-03`: patch/closeout anchoring is one plausible mediator, while the
  obligation-first replay is only an unranked sensitivity screen and cannot by
  itself prove cause or admission accuracy.

These corrections change no patch identity, accepted count, resource metric,
checker-decision result, endpoint, or non-deployment disposition. See the
[adversarial review](../../review-outputs/adversarial-artifact-reviews/success_implement_fresh_context_completion_admission_diagnostic_adversarial_artifact_review_v0.md).
