# Loss-First Implement 36-Case Post-Hoc Backtest 2026-08-11 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed post-hoc workflow comparison and candidate disposition
scope: >
  Compares Forseti Loss-First Implement with the frozen revised Success
  Implement and Full Chain outputs over the same 12 older and 24 recent cases.
use_when:
  - Evaluating whether Loss-First Implement combined the quality, token, and latency advantages of the two earlier arms.
  - Tracing the evidence and limitations behind the Loss-First candidate disposition.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_vs_full_chain_36_case_retrospective_2026_08_11_v0.md
  - docs/workflows/efficiency/forseti_behavioral_contract_changelog_v0.md
  - .agents/skills/forseti-loss-first-implement/SKILL.md
stale_if:
  - An active three-way adjudication is superseded.
  - A fresh untouched holdout tests this or a successor method.
```

## Decision

**Loss-First Implement does not win the three-way comparison. Do not promote it
to Forseti's default implementation method.**

Across all 36 cases, revised Success Implement had the best quality, Loss-First
used the fewest median tokens, and Full Chain had the lowest median latency:

| Measure | Success Implement (A) | Full Chain (B) | Loss-First (C) | Winner |
| --- | ---: | ---: | ---: | --- |
| Accepted defects, critical/major/minor | **1 / 52 / 13** | 2 / 68 / 18 | 1 / 59 / 16 | A: critical ties C, then 7 fewer majors |
| Median comparison tokens | 3,390,523.5 | 5,470,002.5 | **2,839,481.5** | C: 16.3% below A, 48.1% below B |
| Median end-to-end latency | 757.0925s | **667.219s** | 817.9535s | B: C is 22.6% slower |

Loss-First therefore did not produce the requested singular method that wins
on every front. It improved token economy but regressed both controlling
quality versus Success Implement and latency versus both competitors.

This result is **retrospective regression evidence, not a fresh confirmatory
holdout**. Loss-First was designed after reading the earlier 36-case result and
was replayed on that exposed corpus. It cannot establish general superiority.

## ELI5

Loss-First carried the lightest backpack, but it did not reach the destination
best or fastest. Success Implement made fewer serious ordinary mistakes. Full
Chain reached the finish sooner. So Loss-First found a real saving, but it did
not combine all three strengths into one winner.

## Arms and frozen route

- **A — revised Success Implement:** the recognition-shape decisive-falsifier
  revision selected on the older 12 cases and frozen before the earlier recent
  holdout.
- **B — Full Chain:** Assumption Gate → Fused → Implementation Scoping → Spec
  Writing → Micro-decision Locking → implementation and validation.
- **C — Forseti Loss-First Implement:** bind the smallest complete outcome,
  identify the highest-loss plausible false green, test one loss-bearing
  invariant, and stop after required validation plus that loss test.

Arm C used the exact original dossiers and pre-merge bases, fresh detached
worktrees, fresh auth-only runner homes, `gpt-5.6-sol`, high reasoning, and the
same historical external-state restrictions. It saw no oracle, historical
implementation, peer output, prior finding, or earlier study conclusion.

The three-way evaluator received randomly labelled `P/Q/R` candidate patches,
validation evidence, the hidden oracle, and a controller-regenerated landed
diff. A separate fresh home adjudicator accepted, downgraded, or rejected every
proposed finding without seeing arm identity or resource metrics. These are
same-vendor study audits, not Forseti's different-vendor delegated-review lane.

## Corpus split

| Set | A defects C/M/m | B defects C/M/m | C defects C/M/m | A median tokens / wall | B median tokens / wall | C median tokens / wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Older 12 | **0/26/8** | 1/31/7 | 0/31/8 | **3,780,896 / 813.213s** | 7,783,607 / 917.964s | 3,980,481 / 905.1745s |
| Recent 24 | **1/26/5** | 1/37/11 | 1/28/8 | 2,634,797.5 / 677.854s | 2,999,737 / **516.8765s** | **2,099,761 / 613.9455s** |
| All 36 | **1/52/13** | 2/68/18 | 1/59/16 | 3,390,523.5 / 757.0925s | 5,470,002.5 / **667.219s** | **2,839,481.5 / 817.9535s** |

The recent 24 are not confirmatory for C: the method was derived from the
earlier study that included them. The split is diagnostic only.

## Owner-proposed critical weighting

The frozen primary rule remains lexicographic: critical first, then major,
then minor. As a sensitivity check, the owner proposed treating one critical
as either three or five majors:

| Sensitivity | A major-equivalents | B major-equivalents | C major-equivalents | Result |
| --- | ---: | ---: | ---: | --- |
| 1 critical = 3 majors | **55** + 13 minor | 74 + 18 minor | 62 + 16 minor | A |
| 1 critical = 5 majors | **57** + 13 minor | 78 + 18 minor | 64 + 16 minor | A |

Success Implement wins under both suggested weights as well as the frozen
lexicographic rule. The sensitivity does not rescue Loss-First.

## Per-case adjudicated quality

| PR | A C/M/m | B C/M/m | C C/M/m | Lexicographic best |
| ---: | ---: | ---: | ---: | --- |
| 485 | 0/0/1 | 0/0/2 | 0/2/1 | A |
| 539 | 0/0/0 | 0/1/0 | 0/0/1 | A |
| 555 | 0/1/1 | 1/1/1 | 0/2/1 | A |
| 589 | 0/1/1 | 0/5/0 | 0/3/0 | A |
| 873 | 0/3/0 | 0/4/0 | 0/3/0 | A/C |
| 896 | 0/4/0 | 0/3/0 | 0/4/1 | B |
| 921 | 0/4/1 | 0/3/0 | 0/4/0 | B |
| 980 | 0/3/0 | 0/3/0 | 0/3/0 | A/B/C |
| 984 | 0/0/0 | 0/1/0 | 0/2/0 | A |
| 1004 | 0/6/3 | 0/4/4 | 0/4/3 | C |
| 1019 | 0/1/1 | 0/2/0 | 0/1/1 | A/C |
| 1039 | 0/3/0 | 0/4/0 | 0/3/0 | A/C |
| 1254 | 0/6/0 | 0/6/0 | 0/5/0 | C |
| 1263 | 0/0/1 | 0/3/1 | 0/3/1 | A |
| 1267 | 0/0/0 | 0/4/2 | 0/3/1 | A |
| 1270 | 0/0/0 | 0/1/0 | 0/0/0 | A/C |
| 1271 | 0/0/0 | 0/0/0 | 0/0/0 | A/B/C |
| 1275 | 0/0/0 | 0/1/0 | 0/0/0 | A/C |
| 1280 | 0/4/0 | 0/4/0 | 0/5/0 | A/B |
| 1290 | 0/0/0 | 0/0/0 | 0/0/0 | A/B/C |
| 1291 | 0/0/0 | 0/0/0 | 0/0/0 | A/B/C |
| 1300 | 0/5/0 | 0/4/0 | 1/3/0 | B |
| 1301 | 0/1/1 | 0/1/1 | 0/1/1 | A/B/C |
| 1303 | 1/3/0 | 0/3/1 | 0/3/1 | B/C |
| 1315 | 0/1/0 | 0/1/1 | 0/0/1 | C |
| 1317 | 0/4/0 | 0/2/1 | 0/2/0 | C |
| 1321 | 0/1/0 | 0/1/0 | 0/1/0 | A/B/C |
| 1333 | 0/0/0 | 0/0/0 | 0/0/1 | A/B |
| 1361 | 0/1/0 | 0/1/1 | 0/2/0 | A |
| 1368 | 0/0/0 | 0/1/0 | 0/0/0 | A/C |
| 1400 | 0/0/1 | 0/0/1 | 0/0/1 | A/B/C |
| 1424 | 0/0/0 | 1/2/0 | 0/0/0 | A/C |
| 1434 | 0/0/1 | 0/2/1 | 0/0/0 | C |
| 1435 | 0/0/0 | 0/0/0 | 0/0/0 | A/B/C |
| 1443 | 0/0/1 | 0/0/1 | 0/0/0 | C |
| 1452 | 0/0/0 | 0/0/0 | 0/0/1 | A/B |

Pairwise, A beat C in 13 cases, C beat A in 8, and 15 tied. Across the
three-way comparison, A was an individual or joint quality winner in 26 cases,
C in 22, and B in 15. Pair counts are descriptive and do not replace aggregate
quality.

## What the experiment teaches

The static fusion hypothesis was wrong:

- **Maximum-loss focus saved tokens** but did not preserve Success Implement's
  broad completeness. One chosen catastrophic false green can coexist with
  several material omissions elsewhere; C accumulated seven more majors and
  three more minors than A.
- **Fewer tokens did not mean less elapsed time.** C often spent its narrower
  reasoning budget constructing a deep falsifier, fixture, or proof. Test/tool
  duration and sequential proof work dominate wall time in some cases.
- **Full Chain's latency lead is not clean efficiency proof.** It also had the
  worst quality, and sometimes finished sooner by producing a narrower or more
  defective answer. A future method must not buy speed by lowering completion.

The next plausible hypothesis is therefore not another fixed chain. It is a
budgeted implementation method that keeps Success Implement's complete-outcome
contract, then chooses validation by **expected loss reduction per unit proof
cost**, subject to a hard floor that all applicable critical authority,
transition, and closure invariants are covered. That hypothesis is untested and
is not installed by this record.

## Evidence integrity and corrections

- Arm C: `36/36` immutable raw replay records; exact base and current retained
  patch identity reverified before judging; zero source-isolation hits.
- Active judging: `36/36` blind evaluations and `36/36` home adjudications;
  267 proposed finding IDs all have a home disposition; every active final
  status is `COMPLETE`.
- Three initial evaluators (#485, #589, #980) blocked because the isolated judge
  could not itself run the oracle's Git regeneration instruction. The
  controller had already verified the gold. Their blocked records were
  preserved and superseded by fresh judges carrying an explicit byte/hash
  certificate.
- Eight recent cases (#1254, #1267, #1300, #1317, #1361, #1400, #1434,
  #1435) and two older cases (#873, #896) exposed a durable-evidence flaw:
  retained A/B worktrees had become clean or drifted after their original
  receipts. Invalid three-way judgments were preserved and excluded. Exact A/B
  patches were recovered from the original blind-evaluator session packets and
  accepted only after matching the frozen byte count and SHA-256; fresh judges
  then superseded the invalid ones.
- Active-version rule: v3 for #873/#896; v2 for #485/#589/#980/#1254/#1267/
  #1300/#1317/#1361/#1400/#1434/#1435; v1 for the other 23 cases.
- Evidence inventory: 36 Arm C raws, 49 evaluator artifacts, and 49 home
  artifacts. The 26 superseded judge artifacts remain as failure history.

The correction establishes a future study rule: an exact candidate diff must
be frozen as an immutable byte artifact before evaluation. A retained worktree
is only a convenience, never the evidence authority.

## Disposition

- Keep Forseti Loss-First Implement explicit-only and experimental.
- Do not make it the default implementation entry or claim it beat Success
  Implement or Full Chain.
- Do not alter the earlier Success Implement versus Full Chain deployment
  result: this post-hoc three-way evaluator uses a new calibration and an
  exposed corpus.
- Preserve the candidate and this negative result for designing a future fresh
  holdout; do not tune and relabel these 24 recent cases as confirmation.
- Actual billed cost remains `NOT_OBSERVED`; token counts are observed resource
  counters, not currency.

## Reproduction boundary

The authorized workflow-run evidence root preserves the frozen case/oracle
packets, 36 Arm C raw results, every evaluator and adjudicator return (including
superseded incidents), prompt/event hashes, token snapshots, elapsed times, and
retained worktrees. Mutable local paths are evidence locations, not Forseti
authority; this report is the durable decision-grade aggregate.
