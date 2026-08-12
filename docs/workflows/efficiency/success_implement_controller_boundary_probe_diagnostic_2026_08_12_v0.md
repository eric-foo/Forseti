# Success Implement Controller-Owned Boundary Probe Diagnostic 2026-08-12 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency diagnostic record
scope: >
  Records the repeated PR #1267 comparison of unchanged Success Implement with
  the same method plus one immutable controller-owned executable boundary probe.
use_when:
  - Evaluating whether an external black-box boundary observation should change Success Implement.
  - Interpreting the PR #1267 broad-completion failures after the P1/P2/P3 and P1/P4 studies.
  - Choosing the locus of a later isolated implementation-quality experiment.
authority_boundary: retrieval_only
open_next:
  - docs/review-outputs/adversarial-artifact-reviews/success_implement_controller_boundary_probe_diagnostic_adversarial_artifact_review_v0.md
  - docs/workflows/efficiency/success_implement_goal_conservation_diagnostic_2026_08_12_v0.md
  - docs/workflows/efficiency/success_implement_instruction_budget_causal_screen_2026_08_12_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A scored finding or metric in this diagnostic is re-adjudicated.
  - A later controlled replay supersedes this mechanism result.
```

## Decision

**Reject E1 and stop after the two-run diagnostic. Keep Success Implement
unchanged. Do not run the three contrasting cases, create a skill, or deploy a
standing boundary-probe step.**

E1 avoided the one critical defect produced by unchanged P1, so it was better
under the frozen lexicographic severity comparison. That is not enough to say
the mechanism worked. Both E1 runs still omitted owner obligations, both still
claimed broad completion, and the controller's executable boundary check
failed on both final patches. E1 had `0 critical / 11 major / 0 minor` accepted
defects versus P1's `1 / 9 / 0`.

E1 also used `13.88%` fewer median comparison tokens and was `6.25%` faster.
Those resource guards passed, but the mechanism-defining reliability gates did
not. No weighted-severity rescue was applied. Actual billed cost was not
observed; token counters are comparison measures, not billed-cost claims.

## ELI5

We gave the builder a custom alarm that the builder could not rewrite. The alarm
went off before building and still went off afterward. The builder nevertheless
said the house was done while important rooms were missing.

The alarm helped expose a problem, but it did not reliably help the builder fix
the problem. Making every future builder carry this alarm would add work without
solving the failure it was meant to prevent.

## Frozen comparison

| Arm | Method | Method source | Added treatment |
| --- | --- | --- | --- |
| P1 | Unchanged tuning-selected Success Implement | 15,483 normalized-LF bytes; SHA-256 `818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383` | None |
| E1 | Exact P1 source | Same exact source and hash | Access to one immutable external executable probe before and after implementation |

The probe started from a company/vendor board coordinate and no captured
payload. It first admitted only a runner whose source and `--help` output
matched its exact four-vendor CLI vocabulary. It then invoked that runner and
passed when any socket attempt reached its interceptor before live I/O. It did
not verify the socket destination, request URL, protocol, or request shape. The
actor could execute it but could not read, import, copy, or modify its source.

The frozen probe was 5,546 bytes with SHA-256
`27cb61fa0f8e4cd83916a2a656d74fc253c6fcc154aa5661d73e11c64af4f74e`.
Before dispatch it failed on the clean exact parent with
`NO_BEHAVIORALLY_DISCOVERABLE_FOUR_VENDOR_RUNNER` and passed on the retained
historical accepted implementation. That controlled red/green established
compatibility with the probe's exact discovery interface and socket-attempt
predicate. It did not establish solution-neutral or Greenhouse-specific
discrimination, and it did not establish that every valid alternative
implementation would satisfy the same interface.

## Design and pre-registered gate

The diagnostic ran two independent randomized P1/E1 repetitions on
[#1267](https://github.com/eric-foo/forseti/pull/1267): four authored runs, two
blind evaluations, and two home adjudications. Every authored run used
`gpt-5.6-sol` at high reasoning in a fresh auth-only home and a contained
repository at exact parent
`12c1469e07bc49aae8d1216846cb715ab069c592` with no refs or remotes. Historical
patches, hidden oracles, later history, arm identities, resources, prior
repetitions, and peer outputs were withheld.

E1 could advance to one frozen P1/E1 pair on #1271, #1301, and #1424 only if
all eight conditions held: zero E1 criticals; full obligation coverage twice;
no broad collapse twice; two final probe passes; pooled lexicographic quality
better than P1; no repeated new E1 major family; and median tokens and time each
within 15% of P1.

## Aggregate result

| Arm | Accepted defects C/M/m | Median comparison tokens | Median wall time |
| --- | ---: | ---: | ---: |
| P1 | 1/9/0 | 10,580,179 | 1,088.961s |
| E1 | 0/11/0 | 9,111,543.5 | 1,020.9435s |

E1 passed four gates: no accepted critical, lexicographically better pooled
quality, no repeated new major-regression family, and both resource guards. It
failed four decisive gates:

- owner obligations were `NOT_ALL_COVERED` in both E1 runs;
- broad completion collapse was accepted in both E1 runs;
- the independently executed final probe failed in both E1 runs; and
- therefore the complete conjunction required for advancement was false.

The pre-registered endpoint is `STOP_AFTER_DIAGNOSTIC_AMPLIFIER`.

## Repetition results

| Repetition | P1 C/M/m | E1 C/M/m | E1 coverage | E1 collapse | E1 probe | E1/P1 tokens | E1/P1 wall |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| #1267 r1 | 0/3/0 | 0/4/0 | Not all | Yes | Fail | 4,606,263 / 10,184,276 | 836.918s / 1,125.375s |
| #1267 r2 | 1/6/0 | 0/7/0 | Not all | Yes | Fail | 13,616,824 / 10,976,082 | 1,204.969s / 1,052.547s |

Both mappings were deterministically frozen as `X=E1`, `Y=P1`; the retained
evaluator returns use only the anonymous labels. The live controller scrub was
checked before dispatch, but the exact evaluator-input bytes are not retained
inside this packet and therefore cannot be independently re-audited from it.
In repetition 1, P1 narrowed the request to one response page while E1 narrowed
it to one posting. In repetition 2, P1
substituted local payload admission for acquisition while E1 built a useful
live-acquisition subset but omitted Workday details, posting-level slices,
projection, the reusable registry, CSRF/pacing behavior, and typed failures.

The two blocks also show why the lower medians are not a general efficiency
claim. E1 was dramatically cheaper and faster once, then more expensive and
slower once. With two stochastic runs on one exposed case, resources only show
that E1 stayed inside its guard.

## Overall finding and why

The external probe changed what the actor could observe, but it supplied only a
coarse red signal tied to one exact discovery interface. It did not bind the
distinct owner obligations or identify why the predicate stayed red. Both E1
actors produced candidate acquisition routes, yet their `--provider` runner
interfaces did not satisfy the probe's `--vendor` admission vocabulary. The
probe therefore remained red before invocation while the candidates ranged
from a one-posting primitive to a broader but incomplete board acquisition
route.

This produces two separate negative findings:

1. **As an implementation aid, E1 did not work.** The red signal did not prevent
   omitted obligations or premature completion in either run.
2. **As a generic acceptance boundary, this exact probe was both narrow and
   under-specific.** It could reject alternative runner interfaces that
   attempted real acquisition, while an admitted runner could pass after an
   unrelated socket attempt. That makes it unsafe to install as standing
   Success Implement ceremony.

The result strengthens one narrow conclusion: the recurring #1267 failure was
not reliably fixed by more skill prose, a budget-neutral reminder, or this
opaque external signal. One remaining hypothesis is that task-owned executable
behavior covering a distinct owner obligation would supply more actionable
evidence. This study did not isolate transparency, obligation granularity,
feedback quality, actor attention, interface shape, or ordinary variance, so it
does not identify which of those causes matters. When acceptance behavior
already belongs to the repository or commission, Success Implement can consume
it as ordinary validation. This study does **not** support making the skill
invent a new controller, probe lifecycle, or obligation registry for every
task.

## Next experimental boundary

No reliable Success Implement improvement has been found among the mechanisms
tested so far, and this record selects no next experiment. One unranked
candidate hypothesis would compare P1 with P1 given a **task-owned, transparent
executable acceptance example** that states observable inputs and outputs for
one owner obligation while leaving architecture open. It is viable for later
consideration only where that acceptance surface is already legitimate task
evidence; otherwise creating it would be new ceremony and solution design
rather than a skill improvement.

That hypothesis is untested and is not selected as standing behavior. A later
study must first show that the acceptance example admits multiple valid
interfaces, fails the known substitution, and does not encode the historical
patch. The alternate controller-owned obligation-state hypothesis from the P4
record also remains untested, but this result increases its ceremony risk: an
immutable ledger may block claims without increasing implemented coverage.

## Adversarial review adjudication

The independent same-vendor sanity review recomputed the arithmetic and all
eight advancement gates exactly, then proposed four findings. Home adjudication
accepted all four:

- `AR-01`: narrow the probe claim from Greenhouse acquisition to its literal
  discovery-interface-plus-socket predicate;
- `AR-02`: demote the proposed internal cause and next experiment to unranked,
  unisolated hypotheses;
- `AR-03`: disclose that exact evaluator-input anonymity and full packet replay
  are not independently reproducible from the current temporary packet; and
- `AR-04`: align the primary record and changelog on “no selected next
  experiment.”

The corrections changed no count, metric, gate truth, endpoint, or current
behavior. The review was same-vendor and advisory; it did not satisfy the
cross-vendor discovery/no-new-seam bar. See the
[adversarial review](../../review-outputs/adversarial-artifact-reviews/success_implement_controller_boundary_probe_diagnostic_adversarial_artifact_review_v0.md).

## Integrity and limits

- All four patches regenerated to their frozen byte counts and SHA-256
  identities before evaluation. The dossier, oracle, exact base, and historical
  gold identities also matched.
- A live pre-dispatch controller check found no arm labels, study paths, or
  probe/controller wording in the generated evaluator evidence. The retained
  evaluator returns use anonymous labels, and every finding received a home
  disposition. Exact dispatched evaluator-input bytes are not present in the
  named packet, so treatment blinding is not independently reproducible from
  that packet alone.
- Same-family blind evaluation is a controlled study audit, not different-vendor
  delegated review.
- One E1 authored result was recovered from its single preserved completed
  session after a controller-only source-isolation false positive. Fresh command
  inspection found no forbidden source read; the arm was not rerun.
- The aggregate JSON SHA-256 is
  `aac3bbed87e5c64581b2fe01261b93f6623ec802efe0c6767f0c7b60b68a9a4f`.
  The current packet and its imported controller, prompt, dossier, and method
  dependencies in `C:\tmp\forseti-goal-conservation-evidence-2026-08-12` were
  freshly readable during the study, but neither temporary path is an immutable
  archive and the current packet is not self-contained. Durable packet and
  evaluator-input reproducibility are `NOT_PROVEN`.
- No production skill, Forseti-local skill, plugin, package, cache, installed
  copy, or user shadow changed. The contrasting-case stage did not run.
