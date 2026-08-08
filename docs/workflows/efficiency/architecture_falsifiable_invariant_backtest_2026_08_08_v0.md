# Architecture Falsifiable-Invariant Backtest 2026-08-08 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency backtest and admission record
scope: >
  Tests whether requiring architecture docs to state every invariant, gate,
  and mandatory step as a falsifiable observation would have flagged, at
  authoring time, the defects that delegated architecture reviews later
  caught across a fixed recent PR corpus.
use_when:
  - Deciding whether the workflow-architecture-planning skill should adopt a
    falsifiable-invariant clause.
  - Rechecking the evidence behind keeping architecture-defect detection in
    the delegated-review lane.
authority_boundary: retrieval_only
stale_if:
  - A later adjudication changes a scored hit, miss, or false-flag disposition.
```

## Decision

PENDING at freeze. The predeclaration below is frozen in this commit before
any blind-lane execution; selection, blind returns, scoring, and the
adjudicated decision are appended in a later commit and must not modify the
predeclaration hunks.

## Bound outcome and admission bar (frozen)

The backtest asks: would a one-clause authoring rule — state every invariant,
gate, seal, and mandatory step as a concrete observation that would show it
violated — have flagged, at authoring time, the in-family architecture defects
that cross-vendor delegated reviews later caught after merge?

Before any blind execution or scoring, adoption of the clause (as a proposed
edit to the `workflow-architecture-planning` source candidate in the external
`agent-workflow` repository) is bound to ALL of the following:

- the blind lane scores **at least 3 hits** on accepted in-family findings
  **across at least 2 distinct fix PRs**;
- **at most 1 false flag per document** in the blind returns;
- adopting the clause requires **no new recurring artifact, receipt, checker,
  status, or pass** beyond the single authoring clause itself.

Strict definitions in the Scoring section govern. If the bar fails, the
recorded decision is do-not-adopt and this record prevents re-litigation from
the same evidence.

## Corpus and selection predicate (frozen)

Corpus: the 100 most recently created pull requests returned at freeze time by

```text
gh pr list --state all --limit 100 --json number,title,body
```

run in the `eric-foo/forseti` repository. The realized number range and any
non-PR gaps are recorded in Results.

Selection predicate (mechanical; a PR is selected iff its title+body
concatenation satisfies ALL three, case-insensitive for (a) and (c)):

- (a) matches regex `adjudicat` (adjudicated / adjudication / adjudicate);
- (b) matches regex `\b[A-Z]{2,4}-0\d\b` (typed finding IDs such as `XX-01`);
- (c) matches regex `architecture|structure review|NEEDS_ARCHITECTURE_PASS`.

Each selected PR is a **fix PR**: a PR that closes adjudicated findings from a
delegated architecture/structure review. Its adjudicated findings (accepted
and accepted-with-modification only; rejected findings excluded) are the gold
units. The predicate is fully re-runnable from this record; no
resident-judgment exclusions are permitted (closing the prior backtest's F5
reproducibility defect).

## Defect family definitions (frozen)

A gold finding is **in-family** iff its accepted defect is one of:

- **FAM-1 unexecutable:** a required step, gate input, or consumed artifact
  that cannot be executed or produced as written (missing authority, missing
  production chain).
- **FAM-2 mechanically satisfiable:** a gate or seal that can pass without
  the semantic outcome it stands for.
- **FAM-3 unobservable:** a rule or label with no defined observation that
  could show violation.
- **FAM-4 contradictory:** rules that cannot be simultaneously satisfied.

Out-of-family (never scored for or against the bar): vocabulary drift,
naming, pointer/manifest/router hygiene, selector wording precision, scope
boundary choices, and lifecycle bookkeeping. Family classification of each
gold finding is recorded with one-sentence rationale in Results.

## Blind protocol (frozen)

For each selected fix PR:

- **Pre-review revision:** the `reviewed_revision` (or equivalent reviewed-at
  revision) stated in the fix PR body. If none is stated, the case is
  recorded as `NOT_BLINDABLE` and excluded, with the exclusion disclosed.
- **Blind input set (mechanical):** the durable `.md` and `.yaml` doctrine
  files changed by the fix PR's merge commit, filtered to `docs/decisions/`
  and `forseti/product/`, excluding `migrations/` and `docs/review-outputs/`,
  and restricted to files that already exist at the pre-review revision.
  Inputs are pinned as `<revision>:<path>` — in-repo, durable, verifiable via
  `git cat-file` (closing the prior backtest's F7 off-target-proof defect).
- **Blind reader:** one fresh subagent per fix PR with no conversation
  context. The prompt is exactly the frozen template below plus the revision
  and file list. The prompt must contain no finding IDs, finding content, fix
  content, or PR identifiers.

Frozen blind prompt template:

```text
You are reviewing architecture/doctrine documents from a repository at a
pinned historical revision. Read each file with: git show <REV>:<PATH>
(run from the repository root; read-only task, change nothing).

Files: <LIST>

Task - falsifiable restatement audit:
For every invariant, gate, seal, mandatory step, or binding rule these
documents state, attempt to restate it as a concrete observation that would
show it violated ("this rule is broken when you can observe X").

Flag every rule you cannot restate that way. Classify each flag:
(a) unexecutable - a required step that cannot be executed as written
    (missing authority, missing input, missing production path);
(b) mechanically satisfiable - a gate or seal that can pass without the
    outcome it stands for;
(c) unobservable - a rule or label with no defined observation that could
    show violation;
(d) contradictory - rules that cannot be simultaneously satisfied.

Rules:
- Do not flag vocabulary, naming, formatting, cross-reference, or pointer
  issues.
- Do not propose fixes.
- Quote the exact rule text (short excerpt) and name the file for each flag.
- If a document states no such rules, say so.

Return raw data only: per file, a list of flags
{quoted rule excerpt, obstruction class a|b|c|d, one-sentence reason},
plus the count of rules you successfully restated per file.
```

## Scoring definitions (frozen, strict)

- **Hit:** a blind flag that names the same rule, gate, or step as an
  accepted in-family gold finding AND the same defect character (its a-d
  class maps to the finding's FAM class: a→FAM-1, b→FAM-2, c→FAM-3,
  d→FAM-4). Partial or adjacent matches are misses.
- **Miss:** an accepted in-family gold finding with no qualifying blind flag.
- **False flag:** a blind flag matching no gold finding, where scoring —
  using the gold record and the document text — judges the flagged rule
  actually executable, outcome-bearing, observable, or consistent as written.
- **Novel candidate:** a blind flag matching no gold finding that scoring
  cannot dismiss as a false flag. Recorded and disclosed; counts neither
  toward the hit bar nor against the false-flag bound. Novel candidates are
  observations only, never adjudicated defects in this record.
- Out-of-family gold findings and blind flags on them are excluded from all
  counts.
- The strict counts above govern the bar. A lenient recount (hits including
  same-rule/different-class matches) is disclosed for comparison and never
  governs (closing the prior backtest's F1 strict/lenient ambiguity in
  advance).

## Contamination and residuals (frozen disclosure)

- The predeclaring author had read the adjudicated finding summaries in the
  candidate fix-PR bodies before designing this predicate and bar. Mitigation:
  the predicate and blind-input selection are mechanical, and the blind
  readers are fresh subagents that receive only the frozen template. The
  residual is that the family definitions were written by a contaminated
  author; it is named, not removed.
- Hindsight residual: a blind reader told to hunt unfalsifiable rules knows a
  hunt is on, which real authoring time does not. The bar's per-document
  false-flag bound limits, but does not eliminate, this inflation.
- Small-corpus residual: the selected fix-PR count is expected to be small.
  The bar's cross-PR requirement limits single-document generalization; no
  population estimate is claimed.

## Non-claims

This record does not validate the success-implement skill, does not install
any authoring rule, gate, or checker in this repository, does not claim the
delegated-review lane is replaceable, does not re-adjudicate any gold
finding, and does not claim its blind subagent returns generalize across
models or vendors. A passing bar supports proposing one clause in the
external `agent-workflow` source candidate; it authorizes no edit by itself.
