# Success Implement Measurement Calibration 2026-08-13 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-measurement calibration and stop record
scope: >
  Tests whether the severity ruler used in Success Implement comparisons can
  reproduce fixed boundary judgments, then measures identical-method builder
  variance across three independent draws on four cases.
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
  - A later identical-method replication materially changes the observed spread.
  - A later calibration supersedes this measurement boundary.
```

## Decision

**The concretized severity ruler passed a narrow same-family reproducibility
screen. The completed identical-method screen returned `HIGH_VARIANCE`; do not
interpret a small one-run challenger difference as a skill effect.**

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

The next stage ran three identical Success Implement builds on each of four
untouched cases. The resumed eight runs used the same frozen method, prompt,
model, reasoning level, exact bases, and isolation route as the first four.
Blind three-way evaluation plus home adjudication found material major-tier
quality variation in three of four cases. Token max/min spread exceeded `1.15`
in three cases and wall-time spread exceeded `1.15` in all four. Each of those
resource results independently triggers the frozen `HIGH_VARIANCE` stop rule.

## ELI5

First we checked the ruler. Three people used the same clearer ruler on the
same twelve scratches, and all three gave the same answers. Good: the ruler can
repeat itself in this small test.

Then we asked the same builder to do each of four jobs three times. The answers
really did wobble. Three jobs changed at the major-defect level. Three jobs used
over 15% more or fewer tokens between repetitions, and all four varied by over
15% in time. That means a small apparent challenger win can easily be ordinary
run-to-run variation rather than a better instruction.

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

## Stage V — identical-method builder variance

The frozen source was unchanged Success Implement: `15,483` normalized-LF
bytes, SHA-256
`818beb339467e52b70d236b40a74c4cc07369a8b56e10fe38a698af54f25b383`.

The four untouched cases were #1470 (mechanical/local), #1472 (bounded fix),
#1465 (stateful/cross-module), and #1474 (feature/system). #1463 was rejected
before dispatch because its final squash combined evolving implementation and
review work without one reconstructable solution-free request. #1474 replaced
it and had repository-resident media fixtures, so no lost live state was
required.

The frozen stop rule returned `HIGH_VARIANCE` if any case flipped critical
presence, at least two cases changed materially at the major tier, or at least
two cases had a token or wall max/min ratio above `1.15`.

| Case | Historical PR | Accepted majors across three draws | Token max/min | Wall max/min |
| --- | ---: | --- | ---: | ---: |
| V1 | #1470 | `1 / 0 / 1` | `1.119x` | `1.484x` |
| V2 | #1472 | `0 / 2 / 2` | `1.363x` | `1.335x` |
| V3 | #1465 | `0 / 0 / 0` | `1.772x` | `1.322x` |
| V4 | #1474 | `0 / 0 / 4` | `1.447x` | `2.429x` |

There were no accepted critical or minor defects. V1 varied between a clean
run, unbound lineage provenance, and missing controlled manifest-tamper proof.
V2 varied between a clean run and two runs that retained the `go-to-market`
selector error plus the missing binding test. V3 was quality-stable. One V4
run narrowed the implementation to the www parser and omitted the supported
old-Reddit path; the other two covered both paths.

| Case | Run | Comparison tokens | Wall | Patch bytes / SHA-256 |
| --- | --- | ---: | ---: | --- |
| V1 | B01 | `1,730,214` | `396.456s` | `10,950` / `d47fb66f…c44d38` |
| V1 | B05R | `1,546,419` | `339.778s` | `3,896` / `6cb81955…787e96` |
| V1 | B09 | `1,690,914` | `267.102s` | `4,207` / `6dfe8d08…b70c5c` |
| V2 | B02 | `2,557,896` | `393.416s` | `12,566` / `5bb302ef…9998d40` |
| V2 | B06R | `2,748,830` | `500.709s` | `15,697` / `89f59634…1b0755` |
| V2 | B10 | `2,017,439` | `525.350s` | `20,034` / `43b8baa0…37717` |
| V3 | B03 | `1,729,209` | `390.204s` | `12,935` / `0078438d…66b2c` |
| V3 | B07R | `1,159,088` | `303.092s` | `8,898` / `04556e8e…425ca7` |
| V3 | B11 | `2,053,557` | `400.699s` | `9,390` / `f4592d0b…6c86df` |
| V4 | B04 | `2,886,540` | `346.346s` | `15,963` / `b28edc55…43bf47` |
| V4 | B08R | `3,962,795` | `841.265s` | `17,544` / `eb8d06e4…d4a32b` |
| V4 | B12 | `2,738,087` | `437.116s` | `17,005` / `735aede7…aa2df` |

Across the twelve authored runs, comparison tokens totaled `26,820,988` with
a `2,035,498` median. Wall time totaled `5,141.532s` with a `394.936s` median.
Input was `26,639,952` tokens (`25,236,736` cached and `1,403,216` uncached),
output was `181,036`, and reasoning was `78,119`.

The four original B05-B08 launches were usage-ceiling rejections before agent
work and changed zero bytes. Their receipts remain preserved. B05R-B08R are
fresh successful replacements and the only replacement outputs scored. Blind
evaluators received anonymous patches, validation evidence, fixed assertions,
and hidden historical oracles. Home adjudication disposed every finding. The
same-family evaluator remains a limitation, not a different-vendor review.

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
- The observed baseline spread is larger than many earlier candidate deltas.
  A future challenger needs repeated blocked runs and a predeclared effect bar
  above that spread; another one-run or tiny-delta screen is not decision-grade.
- Do not edit Success Implement merely to chase one repetition's omission. This
  measurement changes the experiment design, not the production skill.

## Evidence boundary

Run evidence is retained outside the merged navigation surface at:

- `C:\tmp\forseti-si-severity-calibration-2026-08-13`
- `C:\tmp\forseti-si-builder-variance-2026-08-13-v2`

Mutable temporary paths are evidence locations, not Forseti authority. Actual
billed cost is `NOT_OBSERVED`; token counters are comparison measures. The
machine aggregate is `success_implement_builder_variance_aggregate_v1`,
SHA-256
`8b1abb436c15f2d6f862940758cf756abd8900375d8b127a3134b8247c0042e3`.
