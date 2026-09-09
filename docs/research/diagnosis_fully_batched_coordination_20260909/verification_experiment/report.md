# Source-backed diagnosis verification experiment

```yaml
retrieval_header_version: 1
artifact_role: bounded paired verification experiment report
scope: Three fixed real-evidence cases, three fresh repetitions each, and one separate historical positive control.
authority_boundary: retrieval_only
use_when:
  - Assessing whether one source-backed verification pass repairs material diagnosis errors without introducing new ones.
open_next:
  - adjudication.json
  - measurement.json
  - plan.json
stale_if:
  - Frozen inputs, prompts, first-pass outputs, adjudication or the measured cutoff changes.
```

One source-backed verification pass fixed the known congestion error and a fresh no-redness-to-less-redness overstatement. Fresh paired judge material-error counts fell from five to two, with no newly introduced material error found. Two unsupported historical-support reconstructions survived, and the verifier also proposed two clearly nonmaterial wording changes. The safeguard helped in this sample but did not meet the strict all-errors-corrected success condition.

## Quality outcomes

The prior observed failure changed A13's hydration **without causing congestion** into **less congestion**. Its source index retained the correct qualifier. This experiment tests a source-backed check of final claims; it does not recover the generator's hidden internal cause or establish a universal prevention mechanism.

| Cohort | Pairs | Raw judge material errors before | Raw judge material errors after |
| --- | ---: | ---: | ---: |
| Fresh generations | 9 | 5 | 2 |
| Historical positive control | 1 | 1 | 0 |

Author adjudication: Retain the first-pass paired findings, while distinguishing present product diagnosis from unsupported claims about earlier evidence stages. The two surviving packaging issues do not change current product findings or counts; they concern asserted history of how support developed without a supplied historical boundary. The inferred partitions happen to match the owning prior experiment's actual split, but that external fact was not in these full-update reader inputs and does not establish that the reader had support for the historical assertions. The source-scope defect is therefore retained; the report must not portray it as invented leakage events or wrong current counts. Two verifier alarms are nonmaterial: wash-associated absence versus cessation of breakouts, and softer/calmer versus soft/no-irritation wording. Neither correction introduced an observed material error. No semantic retries or changes to first-pass model outputs were made. Full first-pass judge findings remain in [judge-results.json](judge-results.json), including any rejected flags. Final dispositions and decisive evidence are in [adjudication.json](adjudication.json). No generated answer, verifier response or judge response was edited or semantically rerun.

- **hydration-control: Known material benefit overstatement corrected.** The verifier restored the source's non-causation qualifier. The blinded paired judge found the original error and no material error in the corrected answer. This is a historical positive control, not a fresh error-rate observation.
  - Before: "plus less irritation, congestion and perceived oil production."
  - After: "plus less irritation and perceived oil production, without causing forehead congestion."
  - Source: "It has not caused the congestion on my forehead that results in textured skin and bumps"
  - Evidence: runs/hydration-control/verifier/response.json; runs/hydration-control/corrected.json; judges/hydration/response.json pair-18ee2c6373; parent sources.json A13
- **hydration-r1: Fresh specific benefit overstatement corrected.** No redness after joint use with moisturizer became a specific comparative reduction in redness. The source does not establish the prior-redness baseline for that comparison. The correction preserves the actual reported result and joint-use context, with no new material error found.
  - Before: "soft, less red skin"
  - After: "soft skin with no redness"
  - Source: "I have rosacea and I've been adding a drop of this to my moisturizer at night and I wake up with super soft skin with no redness, irritation, or clogged pores."
  - Evidence: runs/hydration-r1/verifier/response.json; judges/hydration/response.json pair-8ff855b660; parent sources.json A14
- **packaging-r2: Unsupported independence/corroboration credit corrected; historical-support inference survives.** The correction preserves descriptive retailer leakage evidence while withdrawing independence credit not established by the supplied cross-platform identities. The answer still reconstructs an unavailable historical partition. Current leakage counts and reported behaviors remain correct; the residual concerns how support supposedly developed across stages.
  - Before: "R01 independently reports"
  - After: "R01 reports"
  - Source: "R01 actor_identity: 215817888; P06 author_url: /@jasminesingh1102; P13 author_url: /@betterxthanxnew"
  - Evidence: runs/packaging-r2/verifier/response.json; judges/packaging/response.json pair-9838fe726d; parent sources.json R01/P06/P13
- **packaging-r3: Unsupported historical-support reconstruction removed.** The verifier removed an asserted initial/addition split and dependent historical counts from a full-update answer whose input provides only the current complete set. Supported current findings and structured counts remain. The inferred split matches the actual older plan, but its derivation was not supplied to this reader; removal repairs that source-scope problem without changing current reported product behavior.
  - Before: "Stage comparison treats P00–P42 in the supplied pre-addition list as initial evidence, and P08–P13 plus R01 as additions."
  - After: "Across the complete supplied source set:"
  - Source: "method: Reread the complete initial and added source set and construct the current diagnosis. Input fields: case, question, count_definitions, products, stage, focal_keys, method, sources; no historical split fields."
  - Evidence: runs/packaging-r3/reader-input.json; runs/packaging-r3/verifier/response.json; judges/packaging/response.json pair-b8e18222bd; parent experiment.json for actual split comparison
- **packaging-r1: Verifier missed an unsupported historical-support reconstruction.** The verifier returned no corrections. The paired answers are identical. Their current counts and source-owned product diagnosis are supported; the unresolved source-scope issue is an asserted earlier single-report state and later support gains without a supplied historical partition. Do not inflate this into false current leakage events.
  - Before: "Initial stage is reconstructed as the supplied focal set before additions P08–P13 and R01; no separate initial-stage record was supplied."
  - After: "Initial stage is reconstructed as the supplied focal set before additions P08–P13 and R01; no separate initial-stage record was supplied."
  - Source: "The actual full-update input contains stage=updated and complete focal_keys, but no initial_keys/addition_keys or prior findings."
  - Evidence: runs/packaging-r1/reader-input.json; runs/packaging-r1/verifier/response.json; judges/packaging/response.json pair-d8b100092b
- **buying-r1 and hydration-control: Two unnecessary verifier alarms; no material regression observed.** The blinded judge accepts both absence and cessation wording for the wash-associated outcome in context. It also accepts softer/calmer skin as a broad paraphrase supported by the calming/soothing title and soft skin without irritation, while distinguishing that from a specific less-red comparison. These alarms show that the verifier can demand unnecessary edits even when its replacements remain supported.
  - Before: "wash-associated absence of breakouts; with softer, calmer skin."
  - After: "wash-associated cessation of breakouts; with soft skin and no redness, irritation or clogged pores."
  - Source: "A04: bam… no more breakouts. A14 title: Calming, Soothing, Buttery Soft Sorcery; body reports super soft skin with no redness, irritation, or clogged pores."
  - Evidence: runs/buying-r1/verifier/response.json; judges/buying/response.json pair-725682e9ae; runs/hydration-control/verifier/response.json; judges/hydration/response.json pair-18ee2c6373

The guard returned 11 exact text corrections across 5 answers, with 0 explicitly unresolved material issues. Corrections are not themselves proof of quality: the fresh paired judges assess both the before and after answers, including lost information and introduced errors.

## Method and isolation

Three repetitions each of hydration, buying and packaging use the existing complete real-evidence sets and the byte-identical full-update generation prompts. Hydration exposes benefit/non-worsening and texture qualifications; buying exposes completed behavior, intention and adverse outcomes alongside loyalty; packaging exposes favorable reception alongside leaks, remedies and retention. These are three purposive cases with overlapping accounts, not nine independent populations or a new market sample.

Every fresh baseline is generated normally using gpt-6-astra / medium / CLI 0.153.4, matching the existing commissioned reader comparability exception. Exact source retrieval remains available under the unchanged two-round resource boundary. Each baseline then gets one fresh verifier using gpt-6-astra / high / CLI 0.153.4 and the complete actual reader input, original answer and retrieval-round count. The verifier receives no prior answer keys, judgment or known-error label. It may propose exact-once substring replacements in string fields only, each linked to source evidence; it cannot silently rewrite unrelated content or structured counts. Unrepairable material issues stay explicit. Host application is deterministic and validated independently.

The historical hydration answer is included once as a separate positive control. Its earlier generation cost is not charged again. It is not a fresh-run error-rate observation, and success on it alone cannot establish fresh-case prevention efficacy.

Three fresh case judges using gpt-6-astra / high / CLI 0.153.4 receive the exact before/after answers under opaque pair IDs and deterministic hash-swapped A/B labels. They receive neither verifier rationales nor method identity. Each answer is assessed against actual reader evidence; historical split boundaries absent from the reader are not imposed by the judge. Exact retrieval provenance is supplied to avoid the earlier procedural-history grading error. Both labels are assessed independently; a matching answer is not a truth key. This pairing isolates observed text changes, but stochastic judging and shared model-family blind spots remain.

The frozen scripts and quality prompts are [freeze.json](freeze.json), [verifier.txt](verifier.txt) and [judge.txt](judge.txt). The preparation plan and success standard were frozen before calls. [experiment.mjs](experiment.mjs) supervises six concurrent workers for generation/verification. Four first-pass applications stopped because the verifier used the actual input's /answer/report pointer while the host assumed /report. Every exact substring matched once. [resume.mjs](resume.mjs) removes only that unambiguous wrapper prefix, applies the original responses, and launches the three originally planned judges. The original frozen script, first-pass failures and responses remain untouched; no model was rerun. This mechanical adapter recovery and its freeze are preserved in recovery.json and recovery-freeze.json. Routine operations stay in code; coordinator substantive input is restricted to compact outcomes and decisive excerpts.

## Native cost and latency

| Component | Input | Cached subset | Output | Reasoning subset | Input + output |
| --- | ---: | ---: | ---: | ---: | ---: |
| generators | 379,914 | 60,160 | 25,194 | 1,490 | 405,108 |
| verifiers | 367,565 | 17,664 | 6,351 | 4,664 | 373,916 |
| judges | 205,473 | 0 | 4,907 | 1,664 | 210,380 |
| coordinator | 1,989,393 | 1,951,488 | 26,232 | 7,968 | 2,015,625 |
| **Combined at cutoff** | | | | | **3,005,029** |

The fresh nine-answer generation cost is 405,108 tokens. Their added verification costs 334,899 tokens (82.7% of generation cost). The separate positive-control verification costs 39,017 tokens. Experimental judges cost 210,380 tokens and remain included in total experimental cost; they are not hidden as coordinator savings. No claim is made that an eventual operating guard can dispense with outcome assessment on this evidence alone.

Actual model launches: 11 generator calls including retrieval, 10 verifiers and 3 judges. Their settings and native IDs/start/finish times, exits, counters, model-call proxies and byte sizes are preserved per call in [measurement.json](measurement.json). Cached input is included once within input; reasoning is included once within output. Bytes are recorded separately and are not token savings. Semantic retries: zero.

Supervised model work took 8.71 minutes. Current user turn through the available counter cutoff took 15.46 minutes. Per-role summed process durations, which are not concurrent elapsed time, are in measurement.json.

## Validation and measured boundary

[measure.mjs](measure.mjs) verifies frozen identity; all nine fresh generator prompt identities against the previous full-update construction; exact complete source/context inputs; baseline source-index participation; unique cold native sessions and actual stdin; no tool/history contamination; observed model/effort/CLI; real exits and native event/counter agreement; complete before/after pairs and masking; and exact correction-only changes. Material quality remains a source-backed judgment rather than a string/count check. Saved totals are reproduced with `node docs/research/diagnosis_fully_batched_coordination_20260909/verification_experiment/measure.mjs --check` against the pinned cutoff.

Coordinator measurement begins with this experiment's user turn at **2026-09-09T14:28:30.859Z**, subtracting the immediately preceding native cumulative counter. Prior experiments and intervening discussion are excluded; any reprocessing of their context during this turn remains charged. Preparation, script work, waiting, grading and report/publication preparation are mixed intervals included through the cutoff, not causally allocated phases.

**One final available counter cutoff: 2026-09-09T14:43:58.348Z.** Native session: `C:/Users/vmon7/.codex/sessions/2026/09/09/rollout-2026-09-09T22-06-01-01a0867d-6954-7e30-bac7-2c28f7cc3400.jsonl`. Subsequent publication, recovery and final-response costs remain explicit unallocated residual for parent finalization through the turn's task_complete event. Do not recursively rewrite reports chasing the final token. All generator, verifier and judge costs are complete.

This is a bounded sample experiment, not a production guard, doctrine change, rollout, whole-corpus continuation, causal proof or general non-inferiority claim. The semantic operating contract's supported route remains unchanged. The existing draft PR remains held for different-vendor operator-courier review and author adjudication before merge; these same-vendor experimental graders do not satisfy that lane. No merge or automatic continuation.
