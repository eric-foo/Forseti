# Success Implement Hot-Path Trim Screen 2026-08-13 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed matched implementation screen and stop record
scope: >
  Tests whether a clause-preserving reduction of Success Implement's
  explanatory hot path lowers implementation-session token use without
  worsening accepted quality or materially increasing wall time.
use_when:
  - Evaluating Success Implement wording compression or instruction trimming.
  - Interpreting why a shorter skill source did not earn promotion.
  - Tracing the current unchanged Success Implement disposition.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_measurement_calibration_2026_08_13_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A later clause-preserving trim is tested under a superseding frozen protocol.
  - A different model or broader corpus materially changes the matched result.
```

## Decision

**`NO_ADVANCE`. Keep Success Implement unchanged and do not run the untouched
holdout.**

The trim improved accepted quality in this screen, but failed the mechanism's
reason for existing. It used fewer comparison tokens in only `3/12` matched
pairs. Its median matched token ratio was `1.412737` and its median matched
wall-time ratio was `1.177375`, so it cost about 41% more tokens and 18% more
time on the pre-registered paired measures.

The result rejects this exact trim as an efficiency improvement. It does not
show that all compression is harmful or that unchanged Success Implement is
globally optimal.

## ELI5

We shortened the instruction sheet by about eleven percent without deleting
any rule. Then we gave the short and normal sheets the same four jobs, three
times each.

The shorter sheet produced fewer judged mistakes. But it usually made the
builder spend *more* tokens and take longer. Since the experiment was asking
whether trimming saves work without hurting quality, it failed even though the
quality side looked promising.

## Frozen arms

| Arm | Normalized-LF bytes | `o200k_base` construction tokens | SHA-256 |
| --- | ---: | ---: | --- |
| Current baseline | `13,144` | `2,642` | `6068aa00295a39530fe8c24c446cbae33a42ededcc408048357885aad2ae5b57` |
| Clause-preserving trim | `11,739` | `2,351` | `36cca1081b4e91d1ee4e2fde16d50fc9936c8c18fe2034df721cba0bd7185601` |

The candidate removed `1,405` bytes (`10.689%`) and `291` tokenizer units
(`11.014%`). The tokenizer count is a construction measure, not observed
session usage or billed cost.

Before dispatch, a 43-clause audit mapped every baseline duty to the candidate.
Frontmatter, planning composition, and everything from `Implement` through
validation, delegated-review routing, closeout, and trigger boundaries were
byte-identical. The changed surface was limited to compressing the explanatory
purpose, entry, success-contract, and pressure-test wording. No artifact,
checker, reviewer, reference, status, or lifecycle step was added.

## Screen design

The repeated matched screen followed the earlier
[measurement calibration](success_implement_measurement_calibration_2026_08_13_v0.md)
rather than relying on one build per method.

- Cases: [#1470](https://github.com/eric-foo/forseti/pull/1470),
  [#1472](https://github.com/eric-foo/forseti/pull/1472),
  [#1465](https://github.com/eric-foo/forseti/pull/1465), and
  [#1474](https://github.com/eric-foo/forseti/pull/1474).
- Three independent baseline/trim blocks per case: `24` authored runs.
- `gpt-5.6-sol`, high reasoning, fresh auth-only homes, exact sealed bases,
  clean detached repositories, and zero refs/remotes.
- Randomized arm order and separately randomized evaluator labels.
- Hidden later history, oracles, arm identity, resources, prior results, and
  peer outputs during authorship.
- Twelve blind paired evaluations and twelve home adjudications.
- Same-family evaluation is disclosed; it is not different-vendor delegated
  review.

All 24 authored runs exited `0`. All patches were non-empty, regenerated to
their recorded bytes and SHA-256, and had unique hashes. The 24 builder command
traces contained zero forbidden source reads.

## Results

Defects are accepted critical/major/minor counts after home adjudication.

| Block | Baseline C/M/m | Trim C/M/m | Baseline tokens | Trim tokens | Baseline wall | Trim wall |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| V1-r1 | 0/1/0 | 0/0/0 | 1,054,207 | 1,500,262 | 256.221s | 366.889s |
| V1-r2 | 0/1/0 | 0/0/0 | 613,670 | 890,117 | 163.293s | 252.958s |
| V1-r3 | 0/0/0 | 0/0/0 | 2,724,898 | 1,323,101 | 415.502s | 274.138s |
| V2-r1 | 0/1/0 | 0/1/0 | 2,136,904 | 4,382,599 | 383.667s | 591.177s |
| V2-r2 | 0/1/0 | 0/1/0 | 1,607,989 | 4,424,600 | 332.030s | 565.372s |
| V2-r3 | 0/2/0 | 0/1/0 | 1,504,678 | 1,677,305 | 317.613s | 378.194s |
| V3-r1 | 0/0/0 | 0/0/0 | 806,062 | 1,322,188 | 280.410s | 269.567s |
| V3-r2 | 0/0/0 | 0/0/0 | 1,145,261 | 1,396,371 | 337.864s | 357.032s |
| V3-r3 | 0/0/0 | 0/0/0 | 1,281,858 | 1,260,173 | 322.428s | 332.585s |
| V4-r1 | 0/1/0 | 0/0/0 | 1,924,190 | 1,427,450 | 375.799s | 334.315s |
| V4-r2 | 0/0/0 | 0/0/0 | 2,413,590 | 3,384,709 | 413.468s | 481.281s |
| V4-r3 | 0/0/0 | 0/0/0 | 1,941,857 | 3,025,700 | 366.067s | 485.381s |

Pooled quality was baseline `0C/7M/0m` versus trim `0C/3M/0m`. There was no
trim-only critical defect and no repeated trim-only major family.

| Gate | Required | Observed | Result |
| --- | --- | --- | --- |
| Trim-only criticals | zero | zero | pass |
| Repeated trim-only major family | none in two cases | none | pass |
| Pooled quality | lexicographically no worse | trim better | pass |
| Lower tokens by matched pair | at least `10/12` | `3/12` | **fail** |
| Median matched token ratio | at most `0.95` | `1.412737` | **fail** |
| Median matched wall ratio | at most `1.10` | `1.177375` | **fail** |
| Post-result wording tuning | none | none | pass |

The ordinary across-run token medians were baseline `1,556,333.5` and trim
`1,463,856.0`. That unpaired comparison looks like a saving because it mixes
different easy and hard draws. The pre-registered within-block comparison is
the relevant one: trim lost nine of twelve token pairs and used 41.3% more at
the median matched ratio.

Observed comparison-token totals were `19,155,164` baseline versus
`26,014,575` trim. Authored wall totals were `3,964.363s` versus `4,688.888s`.
Actual billed cost is `NOT_OBSERVED`.

## Interpretation and boundary

This screen does not identify why the shorter instruction cost more. A
plausible hypothesis is that the expanded wording cheaply supplies distinctions
the model otherwise rediscovers during source reading and validation; that
mechanism was not directly measured. The decision needs no causal rescue: the
exact candidate missed all three efficiency gates by wide margins.

No current, installed, packaged, cached, or user-shadow Success Implement copy
changed. The untouched holdout and deployment did not run. Run evidence stays
outside the merged navigation surface at
`C:\tmp\si-matched-screen-20260813-v2`; the frozen candidate and construction
audit remain at `C:\tmp\forseti-si-hot-path-trim-2026-08-13-v1`. Those mutable
temporary locations are evidence roots, not Forseti authority.
