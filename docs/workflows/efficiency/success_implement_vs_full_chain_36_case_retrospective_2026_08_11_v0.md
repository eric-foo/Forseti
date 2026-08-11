# Success Implement vs Full Chain 36-Case Retrospective 2026-08-11 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency retrospective and deployment decision record
scope: >
  Records the 12-case tuning comparison and 24-case recent confirmatory
  holdout between Success Implement and the full implementation chain.
use_when:
  - Evaluating whether Success Implement has measured superiority over the full chain.
  - Tracing the evidence behind the decisive-falsifier candidate and its deployment disposition.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
stale_if:
  - A scored finding or metric in the frozen 36-case corpus is re-adjudicated.
  - A later controlled comparison supersedes this result.
```

## Decision

**NO WIN. Do not deploy the candidate from this study.**

On the untouched 24-case holdout, Success Implement used fewer median tokens
but was worse on the first lexicographic quality tier and slower in median wall
time:

| Primary measure | Success Implement | Full Chain | Result for Success Implement |
| --- | ---: | ---: | --- |
| Accepted defects | **1 critical** / 27 major / 10 minor | **0 critical** / 40 major / 12 minor | Worse at the controlling quality tier |
| Median comparison tokens | 2,634,797.5 | 2,999,737 | Better by 364,939.5 (12.2%) |
| Median end-to-end latency | 677.854s | 516.8765s | Worse by 160.9775s (31.1%) |

The frozen rule required Success Implement to be no worse on all three primary
dimensions. It was worse on quality and latency, so neither `CRUSH` nor
`OPERATIONAL_WIN` applies. Lower major/minor totals and lower tokens do not
explain away a critical defect.

The owner may still prefer Success Implement as the ordinary implementation
entry because it is simpler and materially lowers workflow burden. That is an
operating preference, recorded separately from the measured result. This study
does not establish that Success Implement beat the full chain.

## ELI5

Success Implement usually carried a smaller backpack and made fewer ordinary
mistakes. But once, on PR #1254, it left a serious hole that could let altered
authority data look valid. The Full Chain made more ordinary mistakes overall,
but none scored critical. Success Implement also finished more slowly in the
middle of the distribution. Under the rules fixed before testing, that means it
did not win.

## The two frozen arms

- **Arm A — Success Implement:** bind the owner-visible result; make the
  smallest complete change; validate wrong-cause paths; for non-trivial work,
  name one decisive falsifier and show controlled red, restoration, and green;
  preserve `CLAIM_CEILING`, `NOT_OBSERVED`, and repository-owned review routing.
- **Arm B — Full Chain:** Assumption Gate, then Fused, with Implementation
  Scoping, Spec Writing, Micro-decision Locking, implementation, and validation.

Both arms used fresh contexts, independent clean historical worktrees,
`gpt-5.6-sol`, high reasoning, randomized order, the same case dossier, and the
same base revision. Neither arm saw the historical implementation, hidden
oracle, peer output, prior conclusions, or post-build findings. Anonymous
same-family evaluators proposed findings; the home controller adjudicated every
finding. This does not satisfy Forseti's different-vendor delegated-review lane.

## Evidence layers kept distinct

### Birth pilot: four cases, eight blinded implementations

The original task, `Evaluate fused skill purpose`
(`019f7079-6084-7e90-95b8-1dce9348a275`), ran paired blinded implementations
over PRs [#485](https://github.com/eric-foo/forseti/pull/485),
[#539](https://github.com/eric-foo/forseti/pull/539),
[#555](https://github.com/eric-foo/forseti/pull/555), and
[#896](https://github.com/eric-foo/forseti/pull/896). The durable adoption record
is [PR #1104](https://github.com/eric-foo/forseti/pull/1104). That pilot is birth
evidence, not the 36-case comparison reported here.

### Separate eight-PR mechanism backtest

The decisive-falsifier mechanism was retrospectively checked against five
defect-bearing cases—[#1111](https://github.com/eric-foo/forseti/pull/1111),
[#1286](https://github.com/eric-foo/forseti/pull/1286),
[#1396](https://github.com/eric-foo/forseti/pull/1396),
[#1425](https://github.com/eric-foo/forseti/pull/1425), and
[#1460](https://github.com/eric-foo/forseti/pull/1460)—plus one clean
non-trivial control ([#1402](https://github.com/eric-foo/forseti/pull/1402))
and two mechanical controls
([#1354](https://github.com/eric-foo/forseti/pull/1354),
[#1356](https://github.com/eric-foo/forseti/pull/1356)). That backtest supported
the mechanism; it did not compare Success Implement with the full chain.

### Twelve-case tuning set

Cases: `#485, #539, #555, #589, #873, #896, #921, #980, #984, #1004,
#1019, #1039`. PR #921 replaced #1060 and PR #984 replaced #1097 because the
originals depended on lost live retailer state.

One revision was admitted: when claiming completeness or closure, the single
decisive falsifier must introduce or mutate a plausible authoritative member
outside the implementation's initial recognition shape—for example path,
directory depth, type, syntax, import, or API. Another already-recognized
instance does not prove closure.

That revision improved the tuning result:

| Tuning measure | Baseline Success Implement | Revised Success Implement |
| --- | ---: | ---: |
| Accepted defects | 1 critical / 41 major / 9 minor | 1 critical / 34 major / 8 minor |
| Median tokens | 4,757,076.5 | 3,780,896 |
| Median latency | 884.462s | 813.213s |

The revision was frozen before the recent holdout. No post-holdout tuning is
included in this report.

### Twenty-four-case confirmatory holdout

| PR | A defects C/M/m | B defects C/M/m | A tokens | B tokens | A wall | B wall | Quality |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1254 | 1/2/2 | 0/4/1 | 7,916,733 | 20,217,179 | 982.803s | 1,669.993s | B |
| 1263 | 0/0/2 | 0/3/2 | 5,630,568 | 2,991,617 | 972.872s | 492.108s | A |
| 1267 | 0/1/0 | 0/5/0 | 10,793,944 | 7,342,519 | 1,162.889s | 960.801s | A |
| 1270 | 0/0/0 | 0/0/0 | 2,104,144 | 2,808,483 | 569.788s | 550.868s | Tie |
| 1271 | 0/0/0 | 0/0/0 | 897,515 | 2,047,646 | 219.756s | 332.820s | Tie |
| 1275 | 0/1/0 | 0/2/0 | 2,400,489 | 2,750,186 | 443.572s | 438.576s | A |
| 1280 | 0/3/0 | 0/4/0 | 26,864,862 | 8,152,271 | 2,136.800s | 898.544s | A |
| 1290 | 0/0/0 | 0/0/0 | 2,482,316 | 3,007,857 | 601.423s | 527.387s | Tie |
| 1291 | 0/0/0 | 0/0/0 | 2,146,861 | 1,626,290 | 768.927s | 405.281s | Tie |
| 1300 | 0/5/0 | 0/5/0 | 10,352,186 | 8,489,864 | 1,209.947s | 1,146.769s | Tie |
| 1301 | 0/2/2 | 0/3/3 | 8,228,609 | 14,461,700 | 936.800s | 1,149.066s | A |
| 1303 | 0/5/0 | 0/5/0 | 17,856,086 | 26,838,063 | 1,420.804s | 1,970.311s | Tie |
| 1315 | 0/2/1 | 0/2/1 | 2,337,525 | 1,823,622 | 556.870s | 383.038s | Tie |
| 1317 | 0/3/0 | 0/2/0 | 4,058,266 | 6,308,643 | 508.532s | 593.347s | B |
| 1321 | 0/0/0 | 0/0/0 | 1,515,575 | 1,865,929 | 274.771s | 341.744s | Tie |
| 1333 | 0/0/0 | 0/0/0 | 807,323 | 1,698,156 | 250.254s | 344.053s | Tie |
| 1361 | 0/1/0 | 0/1/1 | 1,148,432 | 2,876,317 | 382.688s | 419.824s | A |
| 1368 | 0/0/1 | 0/1/1 | 1,656,720 | 3,182,880 | 414.837s | 506.366s | A |
| 1400 | 0/0/1 | 0/0/1 | 1,514,656 | 1,463,091 | 350.676s | 270.715s | Tie |
| 1424 | 0/0/0 | 0/1/0 | 5,696,584 | 9,321,067 | 942.522s | 996.721s | A |
| 1434 | 0/1/0 | 0/2/0 | 6,483,055 | 8,893,256 | 1,014.367s | 877.947s | A |
| 1435 | 0/0/0 | 0/0/0 | 956,890 | 2,065,317 | 281.299s | 332.624s | Tie |
| 1443 | 0/1/0 | 0/0/1 | 2,787,279 | 1,600,158 | 769.975s | 486.555s | B |
| 1452 | 0/0/1 | 0/0/1 | 3,454,917 | 7,603,971 | 754.285s | 710.068s | Tie |

Descriptively, A won quality in 9 cases, B in 3, and 12 tied. Those pair
counts do not replace the frozen aggregate rule. Aggregate quality is compared
critical first, then major, then minor.

The accepted critical defect was in #1254: Arm A failed to recompute
content-addressed Frontier/Registry authority identities, allowing a stored
defer/reject decision to be altered into an eligible decision without the
verification failing. Arm B had no accepted critical defect across the 24.

## Integrity incidents and adjudication

- The account usage ceiling paused execution after 18 completed pairs. All
  worktrees and evidence were preserved; execution resumed only after reset.
  No rejected launch was scored and no model was substituted.
- One resumed #1443 Full Chain attempt read updated installed skill sources.
  It was rejected, preserved as invalid evidence, and rerun from a fresh exact
  base using an auth-only isolated runner home. The valid rerun and every later
  resumed arm had zero non-appended reusable-source reads.
- Twelve Full Chain prompts embedded the source-candidate copy of Spec Writing
  while eleven embedded the plugin copy. The files differ by nine
  role/packaging labels (`skill` versus `source candidate`) and by no trigger,
  gate, step, status, output, prohibition, or validation rule. An independent
  audit inspected all nine changed lines, 540 tool calls, and 135 visible
  assistant messages; no decision or action depended on the distinction.
  Behavioral equivalence passed; the byte-level deviation remains disclosed.
- The final evidence inventory contained `96/96` holdout artifacts with 96
  unique fresh hashes. Raw metrics reconciled to every home adjudication.

## Resource interpretation

Success Implement reduced median token consumption, but wall time did not
follow tokens. It was slower in 13 of 24 cases and faster in 11. Decisive
falsifiers sometimes drove additional fixtures, test construction, and
validation; the Full Chain sometimes reached a narrower or more defective
patch sooner. Tool and test duration, not only model tokens, controls wall time.

Actual billed cost was not observed and is not inferred from tokens.

## Deployment disposition and residuals

- The frozen candidate is **not** copied to canonical, package, cache, or user
  shadow by this study.
- No plugin version is advanced and no superiority claim is published.
- Fused, Assumption Gate, Implementation Scoping, Spec Writing, and
  Micro-decision Locking remain available and retain their provenance.
- Success Implement may remain the owner's preferred ordinary entry, but that
  preference is not a measured win.
- Same-family evaluators and home adjudication are a study limitation; they are
  not the different-vendor delegated-review lane.
- Historical replay cannot reproduce every live external state. Cases without
  preserved fixtures were replaced before either arm ran.

## Reproduction boundary

The source run preserved the exact case dossiers, hidden-oracle identities,
anonymous patches, evaluator returns, home adjudications, token snapshots,
latencies, retry counts, and worktrees. The report carries the decision-grade
aggregate; it does not make mutable local execution paths into Forseti
authority.
