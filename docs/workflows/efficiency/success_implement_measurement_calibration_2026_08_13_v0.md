# Success Implement Measurement Calibration 2026-08-13 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-measurement calibration and stop record
scope: >
  Tests whether the severity ruler used in Success Implement comparisons can
  reproduce fixed boundary judgments, then records the incomplete attempt to
  measure identical-method builder variance.
use_when:
  - Interpreting prior Success Implement challenger non-promotions.
  - Deciding whether a new Success Implement challenger study is measurable.
  - Tracing the calibration-sensitive critical tier in the 36-case records.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md
  - docs/workflows/efficiency/success_implement_fresh_context_completion_admission_diagnostic_2026_08_13_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - The fixed severity docket is independently cross-vendor adjudicated.
  - The blocked three-repetition builder-variance screen completes.
  - A later calibration supersedes this measurement boundary.
```

## Decision

**The concretized severity ruler passed a narrow same-family reproducibility
screen. Builder variance remains `NOT_OBSERVED`; do not run or interpret a new
Success Implement challenger yet.**

Three fresh isolated judges independently rated the same 12 fixed assertions
over six exact frozen patches from the three cases where prior decision-driving
critical labels had moved. All three agreed on defect presence and severity for
all 12 assertions, and on the docket-limited winner for all three cases. The
three verdict-driving items were unanimously critical. That passes the frozen
severity screen.

It does not prove that the ratings are true or that historical defect discovery
was complete. All three judges were `gpt-5.6-sol` at high reasoning. The result
only shows that a more concrete impact rubric plus fixed assertions can make
this model family repeat the boundary on this docket.

The next stage required three identical Success Implement runs on each of four
untouched cases. One valid run completed per case. The next four launches were
rejected before model action by the account usage ceiling and changed zero
bytes; the final four were not attempted after the shared ceiling was known.
None was scored or substituted. One draw per case cannot estimate
within-case spread, so no builder-variance, noise-floor, or minimum-detectable-
effect claim is made.

## ELI5

First we checked the ruler. Three people used the same clearer ruler on the
same twelve scratches, and all three gave the same answers. Good: the ruler can
repeat itself in this small test.

Then we tried to learn how much the builder naturally wobbles by asking it to
build the same thing three times. We only got the first build for each job
before the run allowance ended. One build cannot show wobble. So the next new
improvement experiment must wait; otherwise we still would not know whether a
small difference came from the method or from ordinary variation.

## Why calibration was necessary

The frozen 24-case comparison assigned Success Implement a critical defect on
case #1254, assigned none to Full Chain, and returned `NO_WIN`. A later
three-way re-adjudication of the same frozen patches assigned no critical to
Success Implement on #1254, assigned Success Implement a critical on #1303,
and assigned Full Chain a critical on #1424. The controlling tier therefore
did not reproduce under the earlier broad wording.

The old evaluator did define severity. The problem was not missing labels; the
definitions were broad enough that materially similar boundary failures moved
between `major` and `critical`.

## Stage S — fixed-assertion severity screen

### Frozen packet

- Cases: #1254, #1303, and #1424, relabelled `C1`–`C3`.
- Candidates: the six exact frozen A/B patches, relabelled `N1`–`N6`.
- Docket: 12 preselected assertions. This tested severity consistency, not
  defect-discovery recall.
- Verdict-driving assertions: mutable content-addressed authority (#1254),
  unbound current SQLite authority (#1303), and the omitted central vocabulary
  restructure (#1424).
- Rubric: severity follows normal-use impact, never fix effort, patch size,
  historical label, method identity, or similarity to the landed diff.
- Isolation: fresh auth-only homes, packet-only directories, no repository
  history, network, oracle, prior scores, method labels, or peer returns.

The first judging pass was excluded before comparison because two judges
enumerated a controller directory and one read its manifest despite the read
boundary. That manifest contained patch hashes but no method identities or old
scores. The incident still violated the protocol, so all three returns were
discarded. Three replacement judges ran from separate packet-only directories
where the controller artifacts did not exist.

### Result

| Measure | Result |
| --- | ---: |
| Exact presence-and-severity unanimity | `12/12` |
| Critical/non-critical three-way unanimity | `12/12` |
| Verdict-driving disputed items unanimous | `3/3` |
| Binary critical/non-critical agreement | `1.00` |
| Ordinal four-level severity agreement | `1.00` |
| Docket-limited case-winner agreement | `3/3` |

Because every rating was identical, observed agreement is `1.00` and
chance-corrected agreement is also `1.00`. No resampling interval is reported:
on a fully unanimous docket every bootstrap resample returns `1.00` by
construction, so such an interval would restate the point estimate rather than
bound its uncertainty. With only 12 assertions clustered inside three cases,
this study does not estimate an out-of-sample disagreement rate. It shows that
the ruler repeated here; it does not bound how often it would repeat elsewhere.

Replacement return SHA-256:

- `K1`: `7c354be6b916c567a35dc3f1a05b4fd9a92c36d442c273bf04035bfdd8542537`
- `K2`: `e3035245b468213b81afb0cafe6fcf8309d5556a40e2aa283fafc93b7fb8c36e`
- `K3`: `4587dd945673d99de132fec21734d4466ceaaee1dc544e171ac0cf1f113f5101`

This is a passed reproducibility screen, not an independent truth audit. A
different-vendor review remains valuable precisely because identical models
can share a blind spot.

## Stage V — builder variance stopped incomplete

The frozen source was unchanged Success Implement: `15,483` normalized-LF
bytes, SHA-256
`818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383`.

The four untouched cases were #1470 (mechanical/local), #1472 (bounded fix),
#1465 (stateful/cross-module), and #1474 (feature/system). #1463 was rejected
before dispatch because its final squash combined evolving implementation and
review work without one reconstructable solution-free request. #1474 replaced
it and had repository-resident media fixtures, so no lost live state was
required.

| Case | Valid draws / required | Comparison tokens | Wall | Patch bytes / SHA-256 |
| --- | ---: | ---: | ---: | --- |
| #1470 | `1/3` | `1,730,214` | `396.456s` | `10,950` / `d47fb66f…c44d38` |
| #1472 | `1/3` | `2,557,896` | `393.416s` | `12,566` / `5bb302ef…9998d40` |
| #1465 | `1/3` | `1,729,209` | `390.204s` | `12,935` / `0078438d…66b2c` |
| #1474 | `1/3` | `2,886,540` | `346.346s` | `15,963` / `b28edc55…43bf47` |

These patches and raw counters are preserved but unscored. They are not a
four-case quality sample and cannot be compared with each other because the
tasks differ. The four rejected launches reached no model action and are not
runs; four additional planned launches never started.

## Consequences for the existing record

- Keep frozen historical endpoints as historical endpoints; do not rewrite a
  preregistered `NO_WIN` after the fact.
- Do not use that `NO_WIN` as evidence that Success Implement is weak or use
  later non-promotions as evidence that it is strong. The old controlling
  critical assignment was calibration-sensitive.
- P2, P3, P4, E1, and E2 did not clear their exact frozen advancement gates.
  That is package-level adoption evidence, not proof that their mechanism
  families are ineffective.
- E3 remains an exact-design failure independently of comparative quality: its
  checker was wrong `3/3` and caused zero continuation and zero patch changes.
- Suspend new challenger selection until Stage V obtains three valid identical-
  method draws per frozen case or a superseding variance design is accepted.

## Evidence boundary

Run evidence is retained outside the merged navigation surface at:

- `C:\tmp\forseti-si-severity-calibration-2026-08-13`
- `C:\tmp\forseti-si-builder-variance-2026-08-13-v2`

Mutable temporary paths are evidence locations, not Forseti authority. Actual
billed cost is `NOT_OBSERVED`; token counters are comparison measures.
