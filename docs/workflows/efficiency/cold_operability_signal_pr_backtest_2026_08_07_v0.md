# Cold-Operability Signal PR Backtest 2026-08-07 v0

```yaml
retrieval_header_version: 1
artifact_role: Observed workflow-efficiency backtest and admission record
scope: >
  Tests whether a structured cold-consumer signal improves next-action
  decisions over ordinary PR reading across a fixed recent PR corpus.
use_when:
  - Deciding whether cold-operability claims need a context-starved consumer signal.
  - Reviewing why a universal dogfood protocol was not adopted.
  - Rechecking the evidence behind the validation-gates rule.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/validation-gates.md
stale_if:
  - The cold-operability signal or its Behavioral Admission basis changes.
```

## Decision

Adopt one **claim-scoped cold-operability signal**. Do not adopt a general
dogfooding protocol or skill.

The signal applies only when the bound outcome says a future actor can execute,
route, hand off, or reuse the result without author context. It requires a
context-starved consumer against the exact final revision and intended entry
point. An edit caused by the signal invalidates that signal and requires a
fresh-actor replay. Evidence that exists only on an unmerged branch or local
machine does not prove the durable target.

This record is current as of **2026-08-07 Asia/Singapore**. The owning live rule
is `.agents/workflow-overlay/validation-gates.md`; this record does not override
it.

## Bound outcome and admission bar

The backtest asked whether adding the cold-consumer structure to ordinary PR
evidence would materially improve the next action for cold-operability claims.
Before gold adjudication, adoption was bound to all of the following:

- at least three gold-confirmed decision corrections across eight independent
  cold-operability cases;
- no decision regression relative to the ordinary-reading baseline; and
- no new per-run artifact, status, receipt, checker, template, or universal pass.

The candidate named four defects: author-knowledge leakage, false currentness,
reuse of evidence invalidated by its own repair, and proof existing off the
durable target. Its recurring cost is one fresh consumer run, and another only
when that run causes relevant edits. Work that does not claim cold operability
pays no new step.

## Corpus and controls

The frozen screen was the latest 100 merged or closed PRs available at the
start of the backtest: **#1346 through #1447**, spanning 2026-07-24 through
2026-08-07. The screen did not equate the word `dogfood` with an executed test:
35 PR bodies used the term, while planned-only, incidental, retrospective, and
future-only mentions were excluded; executed cold evidence without that label
remained eligible. The eight newest independent cold-operability cases were
#1439, #1398, #1392, #1383, #1381, #1372, #1370, and #1353.

Two historical controls bounded the proposal:

- PR #921 introduced a conditional cold-agent dogfood gate.
- PR #1039 removed it because applicability classification, an extra agent
  turn, status packets, adjudication, and replays imposed standing ceremony
  without a sufficiently narrow defect class.

Accordingly, this backtest could admit only the non-overlapping cold-operability
boundary. Existing Success Implement signals already cover representative
success, forbidden cases, perturbation, wrong-cause green, cardinality,
identity, ordering, precedence, persistence, repeatability, inventory, and
scratch-state risks.

## Blind comparison method

Three views were kept separate:

1. The baseline reader saw each frozen PR body and head diff and chose the next
   action without a protocol wrapper.
2. A formatter converted only those same observations into six Success
   Implement-compatible fields: tested risk, reproducibility, falsifier,
   first-pass failure visibility, repair/replay lineage, and claim ceiling.
   Missing facts stayed unknown. The blind protocol reader saw only that frozen
   file.
3. The gold lane could inspect repository and Git history, including later
   evidence, and adjudicated whether the changed recommendation was correct.

The protocol-reader input was 21,622 bytes with SHA-256
`0513629f26ee37dad43e749f4a98e90f5524eb7f7e0715c0447925ffad016992`.
It was kept outside the repository at
`C:\tmp\dogfood-protocol-reader-input-20260807.md`; the hash identifies the
frozen comparison input without creating a recurring run-artifact convention.

## Results

`Accept` and `narrow` preserve a bounded claim. `Repair/replay` withholds the
cold-operability claim until a final-state consumer signal exists. `Block`
preserves a truthful terminal failure.

| PR | Baseline action | Structured action | Gold adjudication | Decision delta |
| --- | --- | --- | --- | --- |
| #1439 | Repair/replay | Repair/replay | Final repair still had no live replay; an earlier repair was non-executable because its named artifacts lacked the required category terms. | No change |
| #1398 | Accept narrowly | Accept | Cold reconstruction corrected sequencing ambiguities; later execution exercised the fail-closed consequence. | No change |
| #1392 | Repair/replay | Repair/replay | A later cold run blocked truthfully; the keep/narrow/retire adjudication remained open. | No change |
| #1383 | Unknown | Narrow | Repeated fresh readers exposed the same silent omission; the final bounded doctrine discriminator became exact-clean. | **Corrected** |
| #1381 | Repair/replay | Repair/replay | The reader found routing friction, but the record did not show a material false pass. | No change |
| #1372 | Accept narrowly | Block | A cold reader prevented stale prompts being treated as live; later review edits had no final-state cold replay. | **Corrected** |
| #1370 | Narrow to serial use | Repair/replay | The second replay succeeded only on commit `6bef3c82`, which is not an ancestor of current `main`; merged authority did not contain its evidence. | **Corrected** |
| #1353 | Block | Block | The cold downstream consumer correctly prevented Deliver while a material retailer route remained incomplete. | No change |

The structured signal produced **three gold-confirmed corrections in eight
cases (37.5%)**, no differential regression, and no new durable per-run
surface. It therefore met the predeclared admission bar exactly. This is not a
statistical generalization: the value was concentrated in cold-operability
claims, and the universal-protocol hypothesis was rejected.

## Frozen identities

These hashes bind the inputs seen by the blind readers; they do not assert that
the PR head later became the merge commit.

| PR | Frozen head SHA | PR-body SHA-256 |
| --- | --- | --- |
| #1439 | `18496c931f9cc4ccf46dd8eb185c58209934a7fc` | `aec5d09e353c95f581c9574cb7ee1258b911b9e79e7d634d068c230c657f231e` |
| #1398 | `5ed6de23085c9e63ef3d63ed2e098c1affd1d0af` | `bfb2523f812ccf98c4e0a72a1d909920beeec389299a2327d65a0cc564f51596` |
| #1392 | `489cf230c75ad26db459266ea7604d93c6aadcb5` | `1992cb534ba058278469ea4d15efe7dfeaab0bb9fad7570c26f900d7a6dc08c6` |
| #1383 | `97d2cb0f97fe60310b78f885149fcc08f6475bc5` | `807aa320a424e13f11eeca6e837bcb151e202d0786b30b35d1f0bf8ed0858331` |
| #1381 | `3e96d689f3e54a3faf027619e5e20bd6e70c04a2` | `e59f5045bd30e430a1d793908d856f5029578b2d9ac1eccae62e208f0294138e` |
| #1372 | `b184c288c6bdb91047f332ddc3a697347fc7c59f` | `40a0dfe94637be4fd6951309e612a15df65d51a841a5573e726003652325e248` |
| #1370 | `2b3b3d8798c37262744cf7d6a68bf77d784722e0` | `6cb2b48d71cf9bd123447f3919846eaa67952f684d16e9d941dae1fc790d81f5` |
| #1353 | `8cebfc9c9ced50acad6afa7572c6a2e512eadcbd` | `de9bc708d4e276c0b347e68dd2ae40f40247302154460a77abd9ea1b5a61fdc3` |

## Non-claims and reversal condition

This backtest does not validate a generic dogfood skill, require dogfood on
ordinary implementation, prove that cold agents are always better reviewers,
or make a blocked run successful. It does not claim that eight selected cases
estimate a population effect.

Retire or narrow the signal if a later comparable sample shows fewer than
three net decision corrections per eight cases, any repeated regression, or a
lower-cost existing signal reliably catches the same four defects.
