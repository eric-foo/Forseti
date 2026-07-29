# Capture Retention Content-Only Cutover — Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded commission to flip the default capture retention posture across
  Forseti capture lanes from raw-preserving to content-only (project the
  structured content record in flight, hash and discard raw), with a
  per-lane parity gate BEFORE each flip, a permanent pinned golden-raw
  regression corpus, and automatic raw-preservation fallback on extraction
  failure or anomaly.
use_when:
  - The owner dispatches the disk-at-scale retention decision (2026-07-28)
    for execution.
stale_if:
  - The Source Capture Armory runner ladder or packet schema changes
    materially.
  - A parity gate fails in a way that revises the owner decision.
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    forseti-harness capture-path source (bounded implementation below);
    lane docs for the retention runbook deltas; parity evidence to the
    lane PR, raw fixtures to an operator-drive golden corpus folder
    (outside Git).
  input_prompt_source: docs/prompts/handoffs/capture_retention_content_only_cutover_execution_handoff_v0.md
  edit_permission: implementation-authorized
  implementation_bound: >
    Only: (a) content-retention modes / ContentExtractionSpec wiring for
    capture runners that lack them (the Google SERP cloakbrowser packet
    runner first), mirroring the existing Reddit-lane content mode; (b)
    per-surface extraction-parity checkers and anomaly tripwires; (c)
    rolling-raw-sample retention plus extractor regression tests over
    the current sample window (reconciled 2026-07-28 with revised
    Method 3 after the executing lane flagged the contradiction — the
    earlier permanent golden-corpus wording here was stale; Method 3
    governs). No proxy/anti-detect work, no storage
    services, no dashboards, no deployment.
  targets: >
    forseti-harness/runners/* and forseti-harness/source_capture/* for (a)
    and (b); forseti-harness/tests/* for (c); docs updates named under
    Doctrine change.
  branch: fresh lane branch off main for this work unit.
  doctrine_change: >
    Yes - retires the SERP lane's standing "Preserve raw DOM" method rule
    once its parity gate passes. Controlling sources to update at
    completion: the SERP-lane living state file (staging
    C:\tmp\forseti-serp-lane\serp_lane_v0.md, Method rules) and
    forseti-harness/docs/source_capture_agent_runbook.md where retention
    posture is stated. Propagation per
    .agents/workflow-overlay/source-of-truth.md; evidence in the lane PR.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** make content-only the default retention for capture lanes so
disk stops scaling with raw page weight (measured: 10 Google SERPs =
9.8 MB raw vs 0.2 MB projected rows, ~98% reduction; the current
megadogfood store is 389 MB at 312/986 jobs), without silently losing
the ability to catch extractor defects.
**Done looks like:** every audited lane has a stated retention default;
lanes flipped to content-only did so only after their parity gate
passed; a pinned golden-raw corpus and regression test exist per flipped
surface type; extraction failure still auto-preserves raw; the two
doctrine sources above reflect the new posture. This is the executor
target and a review axis-to-attack, not a review pass bar.

## Why the guardrails are load-bearing (the v1 specimen)

The SERP v1 extractor produced rows that looked healthy — real titles,
real URLs — while silently mis-ranking organic rows, mis-pairing
titles with sources, and letting People-Also-Ask content bleed into
organic parsing. No per-capture content inspection catches this class:
every row is individually plausible; the defect is in arrangement.
It was caught and repaired ONLY because raw DOM existed to re-extract
(v2). Content-only retention forecloses that repair path for every
capture made under it — extractor fixes apply forward only. The owner
accepts that cost for scale; the gates below are what make it
survivable. (Precedent: the Reddit lane already runs content-mode as
its fleet default with in-flight extraction and raw discard.)

## Required reads (pointer-first)

1. `.agents/workflow-overlay/safety-rules.md` — capture routes through
   the Source Capture Armory Runner Ladder.
2. `forseti-harness/docs/source_capture_agent_runbook.md` — runner
   inventory and current retention postures.
3. `forseti-harness/runners/run_reddit_old_http_batch.py` +
   `source_capture/content_extraction.py` — the existing content-mode
   pattern to mirror (retention modes, CONTENT_EXTRACTION_FAILED path,
   block-shell diagnostics).
4. `C:\tmp\forseti-serp-megadogfood-20260727\bin\test_competitor_ledger.py`
   — the pinned-fixture regression pattern to follow for golden corpora.

## Method

1. **Inventory.** Table every capture lane/runner with its CURRENT
   retention default, observed from source, not memory (retailer lanes
   are believed content-first — verify; mark `unknown` where source is
   ambiguous). No flip without an inventory row.
2. **Parity gate (per lane/surface, ONE TIME, before its flip).**
   Owner condition 2026-07-28: this gate survives only because it is
   near-zero marginal cost — it is a SCRIPT (re-extract raw, field-diff
   against the in-flight record, invariant checks), pure local compute,
   no model tokens, run once per lane ever, over captures the lane is
   already making. If a lane's gate cannot be run as a cheap script,
   report `gate_not_cheap` and flip WITHOUT it rather than building
   ceremony — the owner accepts the risk. Checks when run: (a)
   field-diff raw-re-extraction vs in-flight record — zero unexplained
   diffs; (b) surface invariants (module presence, row-count bands);
   (c) failure path exercised once (synthetic). Verdict in the lane PR:
   pass / fail / not-run per check.
3. **Rolling raw sample (owner decision 2026-07-28 — NOT a permanent
   corpus).** Keep raw for the FIRST capture per surface type per day
   (or per run start for batch campaigns), auto-pruned after a 30-day
   window. This preserves a recent ground-truth sample for extractor
   regression at bounded disk cost; nothing is pinned forever. The
   regression check re-extracts the current window's sample after any
   extractor edit.
4. **Flip.** Change the lane's default retention to content. Raw stays
   selectable per-run as an explicit operator evidence posture (the
   Reddit lane already models this). Auto-fallback stays wired:
   extraction failure or tripwire anomaly preserves raw for that
   capture.
5. **Doctrine propagation.** Update the two controlling sources named in
   preflight; note per-lane status. Existing raw stores are NOT deleted
   by this commission — historical cleanup is a separately named owner
   decision.

## Stop conditions

- A parity gate fails: stop that lane's flip, report the diff class,
  leave the lane raw-preserving; do not weaken the gate to pass it.
- A runner has no viable in-flight extractor: report as
  `no_extractor_exists`, leave raw-preserving; writing a new extractor
  from scratch is outside this commission's bound.

## Return contract (one line per field; `unknown` if absent)

- `lane_inventory`: per lane — runner, prior default, new default, gate
  verdict.
- `parity_evidence`: per flipped lane — N, diff result, invariant
  result, failure-path result.
- `rolling_sample`: sampling rule implemented per lane (first-per-day /
  per-run-start), window length, prune mechanism, regression test names.
- `doctrine_updates`: files touched for the retention posture change.
- `not_flipped`: lanes left raw-preserving and why.
- `disk_delta`: measured before/after for at least one live lane.
