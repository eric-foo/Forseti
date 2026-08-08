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

**Do not adopt** the falsifiable-invariant authoring clause from this
backtest. The hit bar was met — the blind lane recovered 3 of 7 (case-scoped
reading) or 4 of 7 (literal reading) accepted in-family architecture defects
across both fix PRs — but the false-flag bound failed decisively: 8 of 11
audited document-instances exceeded the predeclared limit of 1 false flag per
document, with roughly 27 false flags total, overwhelmingly on deliberately
judgment-reserved rules ("material", "equal-or-better", "ambiguous",
"genuinely required"). Installing the clause would convert resident-judgment
doctrine into a standing noise surface while the delegated-review lane
already catches these defects. The delegated-review lane remains the
catching mechanism.

This record is current as of **2026-08-08 Asia/Singapore**. Adjudication and
results were appended after the freeze commit; the predeclaration sections
below are unchanged from freeze except this Decision placeholder, as the
freeze text provided.

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

---

# Results (appended post-freeze)

## Selection results

Sweep executed 2026-08-08 with the frozen command. Realized window:
PR numbers **#1352–#1454**, 100 PRs returned (number gaps in that range are
issues or never-created numbers, not exclusions). Selected fix PRs:

- **#1434** "Apply adjudicated structure-review fixes (AR-01..08) to
  Intelligence Cycle architecture" — pre-review revision `5b293e97`
  (stated in the PR body); merge commit `ddebe55a`.
- **#1424** "Cycle phase restructure (re-applied) + adjudicated
  delegated-review fixes DRP-01..06" — `reviewed_revision` `bb7e134e`
  (stated in the PR body); merge commit `3e0ade5f`.

No other PR in the window satisfied the predicate. Both cases were blindable.
Both cases audit the same Commission Signal Board doctrine set at different
revisions; the frozen scoring text did not case-scope hit matching, so both
the literal and case-scoped readings are computed below.

## Frozen blind inputs (all verified with `git cat-file -e`)

Case A (`5b293e97`, for the #1434 gold): the four changed durable doctrine
files of `ddebe55a` — `authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`,
`spine.yaml`, `workflows/commission_signal_board_playbook_v0.md`,
`workflows/deliver_decision_memorandum_method_v0.md` (all under
`forseti/product/spines/commission_signal_board/`).

Case B (`bb7e134e`, for the #1424 gold): the six changed durable doctrine
files of `3e0ade5f` after the frozen filter (handoff prompt and migration
note excluded) — the four case A files plus `README.md` and
`prompts/forseti_commission_signal_board_prompt_structure_v0.md`.

One fresh subagent per case received the frozen template verbatim plus
revision and file list; neither prompt contained finding IDs, finding
content, or PR identifiers.

## Gold family classification

In-family (7): AR-01 unexecutable mandatory rubric review, FAM-1. AR-02
supplement consumption gate with no production chain, FAM-1. AR-04
Synthesize entry gate opened by a mechanically passing seal, FAM-2. AR-05
cold read with no observable completion disposition, FAM-3. DRP-01
contradictory Deliver acquisition gate, FAM-4. DRP-02 entry gate prohibiting
what Rules 2/12 require, FAM-4. DRP-03 unverifiable "schema-consistent"
label, FAM-3.

Out-of-family (7, excluded from all counts): AR-03 under-specified ceiling
composition; AR-06 ownership decision; AR-07 lifecycle bookkeeping; AR-08
vocabulary drift; DRP-04 contract binding choice; DRP-05 selector wording;
DRP-06 manifest listing.

## Scoring

Blind returns: case A produced 24 flags (12 rules-doc / 1 spine / 5 playbook
/ 6 method) with ~109 rules successfully restated; case B produced 21 flags
(3 README / 5 rules-doc / 5 prompt-doc / 4 playbook / 4 method / 0 spine)
with ~80 rules restated.

Hits (strict; flag names the same rule and the same defect character):

| Gold | Blind flag | Class map | Reading |
| --- | --- | --- | --- |
| AR-04 FAM-2 | Case A playbook: seal validity for the Synthesize turn is mechanically satisfiable while the honesty condition is judged by the sealing actor | b→FAM-2 | both |
| AR-05 FAM-3 | Case A method: "the cold read gates ready-to-show" with no pass/fail disposition defined | c→FAM-3 | both |
| DRP-02 FAM-4 | Case B method: entry gate "never reinterprets the sealed corpus" vs Rule 12 mandatory grain recomputation | d→FAM-4 | both |
| AR-01 FAM-1 | Case B playbook: required post-seal adversarial review whose rubric "authority is deferred until separately adopted" | a→FAM-1 | literal only (cross-case) |

Strict hits: **4 literal / 3 case-scoped — both readings meet the ≥3-hit,
≥2-PR condition** (AR findings are #1434 gold; DRP-02 is #1424 gold).
Lenient recount (same rule, different class): adds no further gold match.

Misses (3): AR-02 (the only supplement flag targeted ceiling-change
judgment, class c, on the out-of-family AR-03 rule), DRP-01 (no flag named
the Deliver acquisition-gate contradiction), DRP-03 (Rule 11's
"schema-consistent" label was not flagged; the reader restated the adjacent
format-drift rule as falsifiable).

False flags and novel candidates per document-instance (dispositions applied
per the frozen definitions; matched-duplicate flags on already-hit or
out-of-family gold excluded from both counts):

| Case:document | Flags | Hits | False flags | Novel | Bound (≤1 FF) |
| --- | --- | --- | --- | --- | --- |
| A:rules-doc | 12 | 0 (2 dup of AR-04 seam) | 8 | 2 | FAIL |
| A:spine.yaml | 1 | 0 (on out-of-family AR-03; excluded) | 0 | 0 | pass |
| A:playbook | 5 | 1 (AR-04) | 4 | 0 | FAIL |
| A:method | 6 | 1 (AR-05) | 4 | 1 | FAIL |
| B:README | 3 | 0 | 2 | 1 | FAIL |
| B:rules-doc | 5 | 0 (1 dup AR-04 seam) | 2 | 2 | FAIL |
| B:prompt-doc | 5 | 0 | 5 | 0 | FAIL |
| B:playbook | 4 | 1 literal (AR-01; dup AR-04) | 2 | 0 | FAIL |
| B:method | 4 | 1 (DRP-02) | 0 | 3 | pass |
| B:spine.yaml | 0 | 0 | 0 | 0 | pass |

Totals: ~27 false flags; 8 of 11 audited document-instances (case A README
not in scope) exceed the bound. The dominant false-flag class is flags on
deliberately judgment-reserved rules — materiality triggers, "equal-or-better"
parsimony, capture-ambiguity licenses, scope boundaries — which this
repository's validation doctrine intentionally keeps resident rather than
mechanical.

Novel candidates (observations only, not adjudicated defects; several may
merit owner attention): unlisted-material-job seal completeness (case A
rules-doc — an area later hardened by the Phase A accounting PRs
#1451–#1454); delegated semantic spot-check sampling coverage and missing
spot-check receipts (both cases); lake-first preflight leaves no artifact;
blocked-to-pass reseal fresh-read leaves no artifact; anchor-product scoring
lacks a combination rule (flagged independently by both readers); cold-read
reviewer-independence and fresh-context verification are self-certified.

## Adjudication

The bar required hit-recall AND per-document precision AND no new recurring
surface. Recall passed under both readings; precision failed in 8 of 11
document-instances. Under the frozen bar the decision is **do-not-adopt**.

Interpretation within this record's scope: the falsifiable-restatement
discipline can surface roughly half of the in-family defect classes that
delegated architecture reviews later caught, but it cannot distinguish
deliberately judgment-reserved rules from genuinely unfalsifiable ones
without repo-doctrine context that an authoring-time clause does not carry.
Applied as a standing authoring rule it would tax every architecture pass
with a high false-positive load. The observed value concentrates in the
delegated-review lane, which already catches these defects with adjudication
context.

## Signal results

- S1 freeze-before-execute: freeze commit `3c6a65b3` precedes all blind-lane
  execution; this results commit appends results and replaces only the
  Decision placeholder the freeze text named. PASS.
- S2 blind integrity: both prompts were the frozen template plus revision
  and file list; no finding IDs or finding content present. PASS.
- S3 mechanical selection: the frozen command and predicate selected exactly
  #1434 and #1424; re-runnable from this record. PASS.
- S4 durable inputs: all ten revision:path pins verified with
  `git cat-file -e` (exit 0 each). PASS.
- S5 strict-bar adjudication: strict counts governed; the literal vs
  case-scoped matching ambiguity was disclosed and computed both ways with
  an invariant bar outcome; the lenient recount was computed and added no
  gold match. PASS with disclosed predeclaration gap (scoring text did not
  anticipate the two cases sharing one document set).
