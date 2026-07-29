# SERP full-bank analysis derivations

Every number in
`docs/research/serp_lane_competitor_scout_20260728/fullbank_analysis_findings_v0.md`
and in the re-judged cells of `serp_lane_v0.md` comes from these scripts.
They were authored in a session scratchpad and produced the 2026-07-28
(888/986) and 2026-07-29 (986/986) passes from there; promoted here
2026-07-29 so the findings stay reproducible after that scratchpad is
collected.

## Why these are here rather than in the research folder

The research folder holds the *judgments*. These are the *derivations*.
The judgments go stale whenever the corpus grows; the derivations do not.
Regenerating is the intended way to refresh a cell, which is why the
findings note cites JSON outputs rather than restating them as prose.

## Running

Each script is standalone stdlib and writes one `analysis/fullbank_*.json`
under the capture store. Run order does not matter except that
`candidates.py` and `adjudicate.py` read `mediators.py`'s ledger output.

```bash
python coverage.py          # -> fullbank_coverage.json
python fullbank_shape.py    # -> fullbank_shape_value.json
python fixed_design.py      # -> fullbank_fixed_design.json
python fullbank_social.py   # -> fullbank_social_and_axes.json
python mediators.py         # -> fullbank_competitor_ledger.json
python candidates.py        # candidate-rung listing for hand adjudication
python adjudicate.py        # -> fullbank_candidate_adjudication.json
python emitter_defects.py   # -> fullbank_emitter_defects.json
```

Set `PYTHONIOENCODING=utf-8` — creator handles and titles carry
non-cp1252 characters and Windows consoles will otherwise raise.

## Known limits — read before trusting a re-run

- **The capture store path is hardcoded** to
  `C:\tmp\forseti-serp-megadogfood-20260727` in each script. Raw capture
  data stays outside Git by lane rule, so these cannot be run in CI as
  written and are not machine-portable. Change `ROOT` to move them.
- **`extracted_v2` is the analysis store, `extracted` is not.** The
  orchestrator writes `extracted/`; `extracted_v2/` is produced by a
  separate stage-1 pass (`bin/refresh_status.py` in the run directory).
  New captures are invisible to every script here until that pass runs,
  and stage 1 SKIPS any packet that already has an `extracted_v2` entry —
  so a re-probed job keeps its stale extraction unless the old one is
  moved aside first. This bit the 2026-07-29 pass.
- **`extracted/` holds job_ids from earlier bank versions.** File counts
  there exceed the bank and must never be read as coverage.
- **`adjudicate.py` carries hand-entered verdicts** for the 111
  candidate-rung entries adjudicated 2026-07-28. A re-run on a larger
  corpus will surface entries nobody has adjudicated; the counts it
  reports are only valid for the set actually judged.
- **No test coverage.** These are analysis scripts, not runners with a
  fixture. A committed fixture plus a shape test is the obvious next step
  if any of them starts feeding a durable consumer.
