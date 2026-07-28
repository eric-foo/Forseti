# Evidence Reading & Weighting Calibration Handoff v0 (2026-07-28)

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff (owner-commissioned)
scope: >
  Two bound outcomes. (A) Encode the proven cold-agent calibration
  protocol for the evidence-reading doctrine so any future cycle can
  rerun it without the authoring chat. (B) Commission an EMPIRICAL
  weighting calibration on full-bank data: evidence weights are to be
  measured against outcomes, not designed a priori.
use_when:
  - Extending or auditing the reading doctrine
    (docs/research/serp_lane_competitor_scout_20260728/:
    competitor_ledger_spec_v0.md, complaints_axis_v0.md,
    delight_axis_v0.md).
  - Running the weighting calibration after the megadogfood bank
    completes (its dispatch order already queues the complaint-axis
    and delight re-scores this pass rides on).
stale_if:
  - The weighting calibration has run and its results are installed.
  - The reading doctrine docs are superseded.
authority_boundary: retrieval_only
next_source: the three reading-doctrine docs; calibration evidence in
  C:\tmp\forseti-axis-delight-calibration-20260728\second_leg_native\
  (dogfood_*_v0.md files, 5 scored cold runs at commits
  aaa97d28..61793775).
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging - the calibration evidence folder under C:\tmp
    (alongside the prior dogfood records); repo docs only if the
    owner later routes a findings snapshot or ratifies an amendment.
  input_prompt_source: docs/prompts/handoffs/evidence_reading_weighting_calibration_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    Part A needs only cold-agent dispatch over already-captured
    evidence and doctrine files - zero new captures. Part B is pure
    local compute over the completed megadogfood store and existing
    native settlements; zero new captures on any host. If a check
    seems to need a fresh capture, record it as an open probe for
    the SERP lane's return-leg queue instead.
  targets: the staging calibration folder only; doctrine installs
    (Part A step 6) land in the three reading docs per their
    consumer rule; no code, spine, or overlay edits.
  branch: doctrine installs ride the owning lane's branch; all other
    output stays in staging.
  reviews: findings-first; no formal verdict bound. Doctrine
    authority stays with the three reading docs; owner rulings stay
    with the owner - this handoff licenses no doctrine edits beyond
    Part A's one-install-per-repeatable-gap rule.
```

## Part A — the reading-calibration protocol (proven, 5 runs, 2026-07-28)

Run this whenever the doctrine changes materially or a new evidence
class enters scope.

1. **Pick uncontaminated evidence.** Any thread/SERP named as a
   specimen inside the doctrine is DISQUALIFIED as test evidence (a
   cold agent would pattern-match it). Prefer: a fresh category, an
   inverse-direction case (e.g. a CONFIRMED resolution when the
   specimen shows DEFUSED), and one case per rule cluster under test.
2. **Freeze the register BEFORE launch.** Row-level expectations
   where the register author has read the evidence; rule-level
   (which constructs must fire, which traps must be avoided) where
   not. Name 2–4 LOAD-BEARING discriminators per case; the case
   passes only if those hit.
3. **Neutral prompt.** Hand the agent ONLY: the three doctrine paths,
   the subject, the evidence paths, and the generic task ("produce
   the evidence rows this evidence contributes, applying the
   doctrine exactly; do not invent rows the doctrine does not
   license"). Never name a rule, construct, or expected finding.
4. **Tier:** worker (Sonnet) is the default test tier — it matches
   the bank-scale harvest profile and is the stricter test of the
   doctrine text. A/B a synthesis tier (Opus) only when the question
   is tiering itself; freeze the doctrine version for the A/B (git
   show the pinned commit into a temp dir) so doc improvements don't
   confound the model comparison.
5. **Score hit/partial/miss against the frozen register.** Record
   beyond-register finds separately — cold agents out-scouting the
   register is signal, not noise.
6. **Patch rule:** ONE doctrine install per REPEATABLE gap (a miss
   that recurs across agents or traces to a missing/misplaced rule).
   Single-agent variance is not a gap until a second run reproduces
   it. Installs land at the consumer (the spec for operative rules;
   the axis docs for orientation/deltas) — completeness is measured
   at the source cold agents actually load.
7. **Open edges route to the owner.** When cold agents hit an open
   vocabulary question and correctly hold rows, that is the doctrine
   working — collect the question for owner ruling; never install an
   answer the owner has not given.

Calibration state at authoring: 5 cold runs, all passes (round 1:
9 hits/1 partial; round 2: 3/3 cases; Opus A/B: strict superset,
no overthink symptoms). Installed from gaps: axis-forfeiture alert,
read contract, ENGAGEMENT-THIN symmetry. Tiering finding: Sonnet for
bank-scale row harvest, Opus for per-subject synthesis reads.

## Part B — the weighting calibration (commissioned, runs on full-bank data)

**Principle: weights are measured, not designed.** The current
weighting machinery (corroboration tiers 2/3+/cross-venue;
engagement-alongside-authors with post-as-comment and
ENGAGEMENT-THIN on both axis sides; one-directional evidence
ranking; glance-value priority; choice-over-adjective;
assertion-only gates) was installed from owner rulings and pilot
specimens. None of its RELATIVE weights has been tested against
outcomes. Do not install numeric weights ahead of this calibration.

**Ground truth:** comparison outcomes and native settlements from
the full-bank pass (the same outcome set the complaint-axis
calibration scores against), under blind two-pass protocol:
freeze-and-hash every scoring artifact before any comparison
artifact is opened; pre-registered scoring rules; outcome-free
intake for any praise-side pass (commit 9075822f rules apply:
exact-SKU, no-axis-joining, outcome-free pass-P intake).

**Pre-registered questions (score each, add none mid-run):**
1. Does engagement weighting improve WHERE-loss prediction over
   distinct-author counts alone? (Score both weightings blind on
   the same subjects; compare hit rates.)
2. Does the cross-venue STRONGEST tier out-predict same-venue 3+
   author STRONG — i.e., does venue diversity earn its rank?
3. Post-as-comment: do post-carried statements (scored at post
   engagement) predict outcomes as well as comment statements at
   equal score, or does the post score inflate?
4. Is there a category-relative engagement normalization (score
   percentile within venue) that beats absolute scores? (Venue
   baselines differ; absolute points are not comparable across
   subreddits — the Fellow/OXO vs SKIN1004 asymmetry is the
   motivating specimen.)
5. Does the ENGAGEMENT-THIN flag mark genuinely less-predictive
   axes, or is low-engagement support as predictive as high?
   (The flag's continued existence is contingent on this answer.)

**Return contract:** per question — the blind hit-rate comparison,
counts of scorable cases, and a KEEP / DROP / AMEND recommendation
per weighting rule with the evidence line. Amendments are proposals
for owner ruling, not installs. Freeze hashes and per-case tables
ride in the evidence directory, pointer in the return.

## Standing non-claims

Pilot dogfood results are pilot results, not rates. No numeric
engagement bar exists until Part B lands. Counts of observed
evidence only; venue baselines are never compared across categories.
