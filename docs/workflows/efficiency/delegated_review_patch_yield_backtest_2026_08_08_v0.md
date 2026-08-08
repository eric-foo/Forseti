# Delegated Review-and-Patch Yield Backtest 2026-08-08 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency backtest and admission record
scope: >
  Aggregates the adjudicated yield of delegated review-and-patch episodes
  across a fixed recent PR corpus to test whether the lane's bound opt-in
  status is supported by more than the single pr1111 case.
use_when:
  - Deciding whether the delegated review-and-patch lane's standing shape
    should be retained, narrowed, or reconsidered.
  - Aggregating adjudicated delegated-review outcomes, as the pr1111 case
    record requires before any standing routing change.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/delegated-review-patch.md
  - docs/workflows/efficiency/pr1111_success_implement_vs_delegated_review_case_v0.md
stale_if:
  - A later adjudication changes a counted episode disposition.
```

## Decision

PENDING at freeze. The predeclaration below is frozen in this commit before
any sweep, extraction, or scoring. Selection results, the episode table,
metrics, and the adjudicated decision are appended in a later commit and must
not modify the predeclaration hunks; only this Decision placeholder changes.

## Bound outcome and admission bar (frozen)

The lane was bound 2026-07-25 on sustained commissioned use plus one
adjudicated within-change comparison (pr1111), with cost explicitly
unmeasured. The pr1111 record requires aggregating multiple comparable
adjudicated cases before proposing any standing routing change. This backtest
is that aggregation for the recent window. It asks: across the corpus, what
did commissioned delegated review-and-patch episodes actually yield at CA
adjudication?

Predeclared decision interpretation, computed over **adjudicated cross-vendor
episodes** (definitions below):

- **Pay-rate** = episodes with at least one accepted (including
  accepted-with-modification) **material** finding / all adjudicated
  cross-vendor episodes.
- **RETAIN-as-bound supported** iff pay-rate >= 1/3 AND the all-rejected
  episode rate <= 1/3.
- **NARROW-consideration flagged** iff pay-rate < 1/3.
- **EXPAND-consideration flagged** (advisory observation only) iff pay-rate
  >= 2/3 AND at least 2 episodes carry a blocking or critical accepted
  finding.

Rationale for 1/3: one material intercepted defect per three commissions,
given the severity classes historically caught (wrong-cause-green tests,
contradictory gates, unexecutable required steps), is judged worth the
commission overhead. The cost side (wall-clock, tokens) remains unmeasured —
the same accepted residual named in the lane's binding record; this backtest
does not resolve it and no threshold here depends on it. Whatever the
outcome, this record installs no standing change: the lane stays explicit
CA-commission-only, and any shape change is a separately made owner decision.

## Corpus and selection predicate (frozen)

Corpus: the 100 most recent pull requests **numbered at or below #1454**
(self-exclusion: PRs created by this backtest branch, #1455 and above, are
out of window by construction), listed via

```text
gh pr list --state all --limit 150 --json number,title,body
```

filtered to number <= 1454, then the 100 highest numbers kept.

Selection predicate (mechanical union of two arms; a PR is selected iff
either holds):

- **Arm 1:** title+body matches, case-insensitive, `delegated` AND
  (`review` OR `patch`).
- **Arm 2:** the PR's squash-merge commit on `main` (found by subject
  suffix `(#<number>)`) **adds** at least one file under
  `docs/review-outputs/`.

## Episode definition (frozen)

An **episode** is one commissioned delegated review or review-and-patch
return together with its recorded Chief Architect adjudication, identified
by its reviewed target (revision, PR, or artifact). Rules:

- Episodes are deduplicated across PRs (a review commissioned in one PR and
  adjudicated in another is one episode).
- Every selected PR lands in exactly one bucket: contributes one or more
  episodes; `NO_EPISODE` (predicate matched but no delegated return exists
  in it, e.g. the word appears in doctrine text); or `OPEN_OR_UNRETURNED`
  (a commission or courier prompt exists in-window with no recorded return
  or adjudication anywhere in the current tree or PR history).
- `OPEN_OR_UNRETURNED` items are disclosed and excluded from the pay-rate
  denominator.
- Episodes whose records show a same-vendor reviewer are recorded and
  disclosed but excluded from the primary pay-rate, which covers the lane's
  own definition (different vendor lineage). A sensitivity recount including
  them is disclosed and never governs.
- Gold-only rule: every counted disposition (accepted / modified / rejected /
  verdict / escalation) must trace to adjudication text recorded in a
  durable source — a PR body, a `docs/review-outputs/` artifact, or a
  workflow record. Nothing is re-adjudicated; findings without a recorded
  adjudication are counted as `UNADJUDICATED` and excluded from pay-rate
  numerator and denominator alike.

## Materiality definition (frozen)

When the episode's own adjudication labels a finding (blocking, critical,
material, minor), that label governs. Absent a label, a finding is material
iff its accepted closure changes runtime behavior or classification
correctness, test discrimination, evidence admissibility, validation
semantics, a doctrine gate, a claim ceiling, or a cross-artifact operating
verdict. Spelling, style, pointer hygiene, and unrelated cleanup are not
material.

## Extraction protocol (frozen)

Extraction is performed by worker subagents over disjoint chunks of the
selected PRs. Each extractor receives PR numbers only, reads PR bodies via
`gh pr view` and referenced durable artifacts from the current tree, and
returns per-episode field rows in which **every disposition field carries a
short verbatim quote of the adjudication line it came from**. Extractors
classify nothing beyond quoting; family/materiality mapping where a label is
absent is done at scoring against the frozen definition above.

Fields per episode: identifier; durable source pointers; reviewed target;
author vendor; delegate vendor; cross-vendor (yes / no / unrecorded);
verdict; findings total; accepted; accepted-with-modification; rejected;
accepted material count; blocking/critical accepted count; patch hunks
accepted or kept; escalations (e.g. `NEEDS_ARCHITECTURE_PASS`); baseline
comparison result when the record itself contains one; disposition quotes.

## Integrity signals (frozen)

- S1 freeze-before-execute: this predeclaration commit precedes all sweep and
  extraction; the results commit appends and changes only the Decision
  placeholder.
- S2 gold-only with spot-check: at least 3 episodes are re-verified by the
  scoring author directly against their primary sources; any extractor
  mismatch is corrected and disclosed, and a second sample is drawn if any
  mismatch is found.
- S3 mechanical selection: predicate and window re-runnable from this record;
  self-exclusion is by the <= #1454 window cap.
- S4 bucket accounting: selected-PR count equals the sum over buckets;
  every episode carries at least one durable pointer.
- S5 strict-bar adjudication: the primary pay-rate over adjudicated
  cross-vendor episodes governs; sensitivity recounts (including same-vendor
  episodes; counting any accepted finding regardless of materiality) are
  disclosed and never govern.

## Residuals (frozen disclosure)

- The predeclaring author has read two episode adjudications in this window
  (#1434, #1424) and the pr1111 case before freezing; thresholds were set
  with that contamination. Mitigation: predicate and window are mechanical,
  extraction is delegated with verbatim-quote traceability, and the bar was
  fixed before any sweep.
- Survivorship: episodes adjudicated only in chat with no durable record are
  invisible to this method; the count of `OPEN_OR_UNRETURNED` items bounds
  but does not eliminate this gap.
- Selection-frame residual: an episode whose landing PR body avoids the word
  `delegated` and whose return was never filed under `docs/review-outputs/`
  escapes both arms; no such episode class is known, but absence is not
  proven.
- Cost remains unmeasured; this record makes no cost claim.

## Non-claims

This record does not validate or invalidate any individual review, does not
re-adjudicate findings, does not measure review cost, does not compare
vendors' review quality, does not create or retire any gate, and does not
change the lane's commission-only activation. Its decision output is owner
decision input only.
