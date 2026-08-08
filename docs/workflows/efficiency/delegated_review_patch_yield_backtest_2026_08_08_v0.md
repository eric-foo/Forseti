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

**RETAIN-as-bound supported.** Across the frozen window, adjudicated
cross-vendor delegated review-and-patch episodes paid at **10 of 11**
(pay-rate 0.91 against a 1/3 bar), with **zero all-rejected episodes** and a
low delegate false-positive burden (3 rejected findings across ~60+
adjudicated findings). The lane's bound opt-in status is supported by
aggregated adjudicated evidence, not just the single pr1111 case.
EXPAND-consideration was **not** flagged under the strict reading: the
pay-rate condition passed (>= 2/3) but only one primary episode (#1424,
DRP-01) carries an explicitly labeled blocking/critical accepted finding.
NARROW-consideration was not flagged.

One owner-relevant observation falls outside the bar: **11 of 28 selected
PRs are open or unreturned commissions**, and at least two (#1454, #1403)
merged despite their own "do not merge before the return" text — returns
systematically trail merges, with at least one adjudication landing
post-merge (#1452).

**Post-publication correction (same day, before merge).** This record
initially reported a second observation — that #1391 and #1407 assert
completed adjudications with no recorded disposition content. That was an
extraction-scope defect in this backtest, not a defect in the corpus.
#1391's dispositions are recorded in full in its **commit-message
trailers** (`review_routing_status: routed -- chat_only_adjudicated:
accepted F1-F7, modified Unicode identity matching, closed F8 F9 F11 F13,
deferred F10 F12 F14 with residuals`), exactly where the review-routing
gate requires them for a code-root change; its extractors read PR bodies
only. #1391 is reclassified below as a recorded episode. #1407 is
unmerged, therefore ungated, and nothing has landed from it. The
content-free-assertion concern is withdrawn; the recording mechanism is
working where it applies. Primary metrics are unaffected (see Metrics).

This record is current as of **2026-08-08 Asia/Singapore**. Results were
appended after the freeze commit; only this Decision placeholder changed in
the predeclaration.

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

---

# Results (appended post-freeze)

## Selection results

Sweep executed 2026-08-08. Realized window: #1352–#1454 (100 PRs; the
identical window to the sibling architecture backtest). Arm 1 selected 28
PRs. Arm 2 selected zero: the last file addition under `docs/review-outputs/`
on `main` predates the window (PR #1116) — this window's returns are carried
in PR bodies, consistent with the courier-retirement filing rules. Selected
set: 1454, 1453, 1452, 1451, 1449, 1447, 1445, 1443, 1436, 1432, 1430,
1429, 1425, 1424, 1421, 1420, 1419, 1417, 1415, 1407, 1403, 1402, 1396,
1394, 1391, 1384, 1360, 1357.

**Selection-frame residual realized:** PR #1434 (the AR-01..08 structure
review, 8/8 findings accepted including one critical) contains a real
in-window cross-vendor episode but its body never uses the word `delegated`,
so it escapes both frozen arms. Per S3 the predicate governs: #1434 stays
out of the primary metric and appears only in the disclosed sensitivity
recount below.

## Bucket accounting (S4)

28 selected PRs = 13 episode-bearing (14 episode rows) + 4 `NO_EPISODE` +
11 `OPEN_OR_UNRETURNED`. Reconciles exactly. (Pre-correction: 12 + 5 + 11;
#1391 moved from `NO_EPISODE` to episode-bearing.)

- Episode-bearing: 1452, 1451, 1443, 1430, 1425, 1424, 1391, 1419 (two distinct
  targets: the p11r7 decision-frontier pass, `PASS_PATCHED`; and the
  community-coding semantic pass, `NEEDS_ARCHITECTURE_PASS` then
  re-derivation with AR-01..04 corrections accepted — the extractor's
  possible-merge caveat is disclosed; merging them changes the pay-rate from
  10/11 to 9/10 and no bar outcome), 1417, 1415, 1402, 1396, 1394.
- `NO_EPISODE`: 1429, 1357, 1420, plus 1407 — which asserts "Three
  delegated cross-vendor reviews were commissioned and adjudicated" with no
  disposition content in its body, but is **unmerged**, so no gate applies
  and nothing has landed. Not counted; not a corpus defect.
- `OPEN_OR_UNRETURNED` (11): 1454, 1453, 1449, 1447, 1445, 1436, 1432,
  1421, 1384, 1360, 1403. Excluded from the pay-rate denominator per the
  frozen rule. Observed discipline gap: #1454 and #1403 are merged despite
  body text "Do not merge before that return" / "Keep this PR draft and
  unmerged until the operator-courier return is adjudicated"; #1452 records
  an explicitly post-merge adjudication.

## Episode table (dispositions traced to verbatim adjudication quotes)

| Episode | Cross-vendor | Findings | Accepted (+modified) | Rejected | Material pay | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1452 | yes (recorded) | 8 | 5 | 0 (F5/F8 non-material; F2 unresolved) | yes | `NEEDS_ARCHITECTURE_PASS` on F2 |
| 1443 | yes | 6 | 4 (+2) | 0 | yes | evidence-claim corrections |
| 1425 | yes (OpenAI author / Anthropic delegate) | >=5 | 4 (+1) | 0 | yes | controller defects, wrong-cause tests |
| 1424 | yes (Anthropic author / OpenAI delegate) | 6 | 3 (+3) | 0 | yes | DRP-01 blocking; escalation hard stop honored |
| 1402 | yes (Claude Opus 5 delegate) | 0 | 0 | 0 | no (clean PASS) | zero hunks required |
| 1396 | yes (Claude Opus 5 delegate) | 5 | 4 | 1 | yes | type-exact/fail-closed runtime fixes |
| 1394 | yes | 5 | 5 | 0 | yes | runtime binding fixes; named architecture residual |
| 1419-a | yes | >=2 | 2 | 0 | yes | `PASS_PATCHED`; wear-axis evidence replaced |
| 1419-b | yes | 4 (+ systemic re-derivation) | 4 | 0 | yes | `NEEDS_ARCHITECTURE_PASS`; 355 rows re-coded |
| 1417 | yes | 8 | 5 (+2) | 1 (delegate claim rejected as incomplete) | yes | F8 deferred |
| 1415 | yes ("different-family" = vendor lineage per the overlay's own definition; vocabulary note disclosed) | 7 | 2 (+3) | 1 | yes | F-03 bounded residual |
| 1451 | unrecorded ("de-correlated" does not establish vendor lineage) | 2 | 2 | 0 | yes | sensitivity bucket only |
| 1430 | unrecorded | 13 | 10 (+2) | 0 | yes | sensitivity bucket only |
| 1391 | unrecorded (delegated, lineage not named) | 14 (F1-F14) | 7 (+1 modified), 4 closed, 3 deferred | 0 | yes | dispositions in commit trailers; sensitivity bucket only |

Materiality where unlabeled was scored against the frozen definition; every
pay entry traces to an accepted closure changing runtime behavior, test
discrimination, evidence admissibility, validation semantics, a doctrine
gate, or a claim ceiling.

## Metrics and bar application (S5)

Primary (adjudicated cross-vendor episodes): denominator 11, pay 10,
**pay-rate 10/11 = 0.91** — far above the 1/3 RETAIN bar. All-rejected
episodes: 0/11 (bar: <= 1/3). **RETAIN-as-bound supported.**

EXPAND-consideration: pay-rate condition met (>= 2/3), but only #1424
carries an explicitly labeled blocking/critical accepted finding in the
primary set — the >= 2 episode condition fails under strict labels. Not
flagged. (Blocking/critical labeling is sparse in this corpus; several
accepted findings — the #1451 false-pass paths, the #1419-b systemic
misattribution — are plausibly critical but unlabeled. Recorded as a
labeling-practice observation, never upgraded at scoring.)

Primary metrics are unaffected by the #1391 correction: its vendor lineage
is unrecorded, so under the frozen rule it enters the sensitivity bucket,
not the primary denominator.

Sensitivity recounts (disclosed, never govern): including unrecorded-vendor
episodes (1451, 1430, 1391): 13/14. Including the known-missed #1434 (8/8
accepted, AR-01 critical): 14/15, which would also satisfy the
EXPAND-consideration episode count — noted only; the frozen predicate
governs. Counting any accepted finding regardless of materiality: unchanged
(every paying episode already has a material accepted finding).

Delegate false-positive burden: 3 rejected findings total (1396
settlement-global uniqueness; 1417 exhaustion-enforcement claim; 1415 F-06
as completion blocker) across roughly 60+ adjudicated findings.

## Signal results

- S1 freeze-before-execute: freeze commit precedes all sweep/extraction;
  this commit appends results and the Decision replacement only. PASS.
- S2 gold-only with spot-check: 3 sampled episodes (1396, 1417, 1402)
  re-verified verbatim against PR bodies, plus 1424 independently read by
  the scoring author before extraction — all concordant; no second sample
  triggered. **PASS with a disclosed scope defect found post-publication:**
  the frozen extraction protocol named PR bodies and referenced durable
  artifacts as sources but not **commit-message trailers**, where this
  repository's review-routing grammar actually lives for code-root changes.
  The S2 sample could not surface this because all three sampled episodes
  carried body content. One misclassification resulted (#1391) and is
  corrected above. A future repeat must read `git log --format=%B` over each
  PR's merge commit as a third source.
- S3 mechanical selection: predicate re-runnable; arm-2 emptiness verified
  against `git log --diff-filter=A` history; self-exclusion held (#1455+
  out of window). PASS, with the #1434 selection-frame residual realized
  and disclosed.
- S4 bucket accounting: 12 + 5 + 11 = 28 reconciles; every episode row
  carries PR-body or durable-doc pointers. PASS, with 1391/1407
  reclassification disclosed.
- S5 strict-bar adjudication: primary bar computed as frozen; sensitivity
  recounts disclosed and non-governing. PASS.

## Adjudication

The lane's bound opt-in status now rests on aggregated adjudicated evidence:
10 of 11 cross-vendor episodes returned at least one accepted material
finding, rejection burden is low, and both `NEEDS_ARCHITECTURE_PASS`
escalations in the window honored the hard stop rather than forcing patches.
The aggregation the pr1111 case required before standing routing changes now
exists, and it points the same direction as pr1111.

The material owner-facing finding of this backtest is operational, not
doctrinal: the return pipeline lags merges — 11 open commissions, two
merged-despite-hold PRs, one explicitly post-merge adjudication. The data
does not establish whether those open commissions represent unreviewed risk
that landed or intent the Chief Architect later judged unnecessary, and
that distinction decides whether any mechanism is warranted. A one-time
triage of the 11 resolves the backlog and produces exactly that evidence;
no standing mechanism is justified before it. This record installs nothing.

The withdrawn second finding is itself instructive: the recording mechanism
that already exists (the `review_routing_status` trailer grammar, gated at
CI for code roots) was working, and the apparent gap was an artifact of
looking in the wrong place. Confirm where a record actually lives before
concluding it is absent.
