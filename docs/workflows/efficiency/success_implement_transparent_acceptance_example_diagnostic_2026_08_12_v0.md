# Success Implement Transparent Acceptance Example Diagnostic 2026-08-12 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency diagnostic record
scope: >
  Records the three-repetition PR #1267 comparison of unchanged Success
  Implement with the same exact method plus one transparent executable
  Greenhouse request example.
use_when:
  - Evaluating whether a concrete owner-boundary example should change Success Implement.
  - Interpreting the earlier E1 controller-probe failure and later implementation-quality hypotheses.
  - Choosing whether to run a broader transparent-acceptance study.
authority_boundary: retrieval_only
open_next:
  - docs/review-outputs/adversarial-artifact-reviews/success_implement_transparent_acceptance_example_diagnostic_adversarial_artifact_review_v0.md
  - docs/workflows/efficiency/success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A scored finding or metric in this diagnostic is re-adjudicated.
  - A later controlled replay supersedes this mechanism result.
```

## Decision

**Reject E2 under its pre-registered gate. Keep Success Implement unchanged and
do not install a standing acceptance-example or probe lifecycle.**

E2 succeeded at a narrow predicate E1 failed: all three independently executed
examples observed the exact public Greenhouse board `GET` from the submitted
repository-Python command. No existing payload file was named in the command's
post-entrypoint arguments; internal use of embedded or otherwise saved data was
not observed by the probe. E2 also had no accepted critical defect, lowered the
owner-frozen weighted harm score from `84` to `77`, used `4.10%` fewer median
comparison tokens, and stayed within the time guard at `3.05%` slower.

It still failed the completion-discipline gate. All three E2 runs left several
major owner obligations incomplete while making a completion-like closeout.
Pooled raw counts were E2 `0 critical / 15 major / 2 minor` versus unchanged P1
`1 / 11 / 4`. The frozen weighted score counted one critical as five majors
and one major as five minors: `25*critical + 5*major + minor`. Raw severity
counts remain visible because the weighted convention is an owner preference,
not a general severity law.

Actual billed cost was `NOT_OBSERVED`. Token counters are comparison measures,
not billed-cost claims.

## ELI5

We showed the builder one exact doorway and let them choose among several
Python tools, flag names, and internal shapes. Three times, the submitted
program made the matching request. That is real progress over E1, whose hidden
alarm could not recognize the alternative Python commands it was given.

But each builder still called the whole house finished while several important
rooms were missing. So the example is useful evidence for one boundary, but it
did not fix Success Implement's broader “done too early” failure. It is not yet
a better general method.

## Frozen arms and observation

| Arm | Method source | Added treatment |
| --- | --- | --- |
| P1 | Unchanged tuning-selected Success Implement; 15,483 normalized-LF bytes; SHA-256 `818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383` | None |
| E2 | The same exact source and hash | A transparent example requiring an exact Greenhouse public-board `GET`; the submitted repository-Python entrypoint could choose supported HTTP libraries, CLI flags, internal modules, and output shape |

The E2 addition was 1,280 bytes, SHA-256
`abf246c283653ddfcf5154baf81bcc4ab129de4c74d64d8d42d48b7c98b5a650`.
The observation tool was 7,974 bytes, SHA-256
`1a48226c8c10468c1c23a837dd1e06be99fb7107417920f0022678d005fbef36`.
Before dispatch, it passed an exact `GET`, failed the wrong host, failed `POST`,
failed a command that referenced a saved payload, passed the retained historical
accepted implementation, and failed the known local-payload shortcut.

That controlled evidence discriminates the tested Python request boundary more
directly than E1's filename/flag/socket predicate and admits several Python HTTP
and CLI shapes. It does not admit every valid runtime or entrypoint, observe
internal payload reads, prove that every possible HTTP stack is visible, or
show that the one request proves the whole task.

## Design and pre-registered gate

The diagnostic ran three randomized P1/E2 repetitions on
[#1267](https://github.com/eric-foo/forseti/pull/1267): six authored runs, three
blind evaluations, and three home adjudications. Every authored run used
`gpt-5.6-sol` at high reasoning in a fresh auth-only home and a contained
repository at exact parent
`12c1469e07bc49aae8d1216846cb715ab069c592`, with no refs or remotes.
Historical patches, hidden oracles, later history, arm identities, resources,
prior repetitions, and peer outputs were withheld.

E2 could advance only if all seven conditions held: zero accepted criticals;
three observation passes; no broad completion collapse in any E2 run; lower
pooled weighted harm than P1; no major regression family newly repeated in two
cases; and median tokens and time each no more than 10% above P1. A failed
condition rejected E2 without qualitative rescue.

## Aggregate result

| Arm | Accepted defects C/M/m | Frozen weighted harm | Median comparison tokens | Median wall time |
| --- | ---: | ---: | ---: | ---: |
| P1 | `1/11/4` | `84` | `8,557,416` | `1,080.047s` |
| E2 | `0/15/2` | `77` | `8,206,316` | `1,113.016s` |

| Advancement condition | Result |
| --- | --- |
| Zero E2 criticals | Pass |
| All three E2 examples pass | Pass |
| No E2 broad-completion collapse in all three runs | **Fail** |
| E2 weighted harm below P1 | Pass |
| No repeated new E2 major-regression family | Pass |
| Median tokens within +10% | Pass |
| Median time within +10% | Pass |

The pre-registered endpoint is `E2_REJECTED`.

## Repetition results

| Repetition | P1 C/M/m | E2 C/M/m | E2 observation | E2 coverage | E2 collapse | P1 / E2 tokens | P1 / E2 wall |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| r1 | `0/3/3` | `0/6/1` | Pass | Not all | Yes | `6,924,187 / 8,206,316` | `1,080.047s / 1,142.781s` |
| r2 | `0/5/1` | `0/6/1` | Pass | Not all | Yes | `14,172,843 / 9,509,077` | `1,093.500s / 914.109s` |
| r3 | `1/3/0` | `0/3/0` | Pass | Not all | Yes | `8,557,416 / 6,588,522` | `966.344s / 1,113.016s` |

All deterministic mappings happened to be `X=P1`, `Y=E2`. Evaluator returns
used anonymous labels, and the controller removed method labels, study paths,
the explicit command, the independent observation block, and much of the
treatment wording. Its line-level scrub retained treatment-adjacent cues joined
by underscores or phrased without the filtered tokens, including status,
method, payload-expectation, URL-mutation, and entrypoint-hash fragments. Exact
dispatched evaluator-input bytes were not retained. Treatment blindness and
absence of evaluator inference are therefore `NOT_PROVEN`.

## Overall finding and why

E2 separates two problems that E1 blurred together:

1. **Can this transparent, Python-bound example make one matching request
   happen?** On these three submitted commands, yes. All three exact provider
   requests were observed, while the earlier E1 mechanism passed zero of two.
2. **Does satisfying one example make the overall implementation complete?**
   No. Every E2 run still omitted several owner-visible seams and claimed broad
   completion.

The bounded lesson is not “examples do not work.” This example repeatedly
elicited its matching request, but it did not prevent the broader completion
collapse. The study did not isolate why: task complexity, ordinary variance,
actor attention, claim calibration, evaluator framing, or some other mediator
remain plausible. Adding more examples might cover more obligations, but it
would also begin to create a task-specification and acceptance-suite lifecycle;
the current study provides no evidence that such recurring ceremony is worth
installing in a general implementation skill.

**Completion admission** is one unranked, untested candidate suggested by the
repeated pattern, alongside better task evidence, claim calibration, and
ordinary variance. E2 did not manipulate completion admission and supplies no
causal reason to prefer it. No next experiment or new completion gate is
selected or authorized by this record.

## Adversarial review adjudication

The same-vendor advisory review independently reproduced every count, weighted
score, median, ratio, regression-family result, and gate truth. It proposed
three findings; home adjudication accepted all three:

- `AR-01`: narrow observation claims to the submitted repository-Python
  commands and stop claiming general implementation neutrality or categorical
  absence of internally used saved data;
- `AR-02`: disclose the retained treatment-adjacent evaluator cues and mark
  exact treatment blindness `NOT_PROVEN`; and
- `AR-03`: remove causal and directional selection of completion admission.

These corrections change no result, metric, gate, or deployment disposition.
See the [adversarial review](../../review-outputs/adversarial-artifact-reviews/success_implement_transparent_acceptance_example_diagnostic_adversarial_artifact_review_v0.md).

## Integrity and limits

- All six authored patches regenerated to their frozen identities before blind
  evaluation; every proposed evaluator finding received a home disposition.
- The scorer stopped once on an unrecognized but valid home-JSON layout, wrote
  no aggregate, then was widened to normalize the three observed layouts. It
  recomputed every finding ID and severity count before writing the decision.
- The aggregate JSON SHA-256 is
  `63f928816ffe3ddacfed105e75c26e46ca9d63e2ec0bc5ab2fd5529b184aa301`.
- Same-family blind evaluation is a controlled study audit, not a
  different-vendor delegated review.
- Exact treatment blinding, absence of evaluator inference, and unbiased
  adjudication are `NOT_PROVEN`; all mappings were `X=P1`, `Y=E2`, and exact
  evaluator-input bytes were not retained.
- The evidence packet at
  `C:\tmp\forseti-e2-acceptance-evidence-2026-08-12` imports frozen dossier,
  oracle, method, and controller dependencies from
  `C:\tmp\forseti-goal-conservation-evidence-2026-08-12`; it is not a
  self-contained immutable archive. Durable packet replay is `NOT_PROVEN`.
- One exposed historical case and three stochastic repetitions do not establish
  transfer to other tasks, models, or acceptance surfaces.
- No production skill, Forseti-local skill, plugin, package, cache, installed
  copy, or user shadow changed.
