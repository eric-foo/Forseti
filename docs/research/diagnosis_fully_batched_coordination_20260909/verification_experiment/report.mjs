import {read,write} from './experiment.mjs';
const m=await read('measurement.json'),a=await read('adjudication.json'),batch=await read('completed-batch.json');
const num=x=>x.toLocaleString('en-US'),min=x=>(x/60000).toFixed(2);
const report=`# Source-backed diagnosis verification experiment

\`\`\`yaml
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
\`\`\`

${a.conclusion}

## Quality outcomes

The prior observed failure changed A13's hydration **without causing congestion** into **less congestion**. Its source index retained the correct qualifier. This experiment tests a source-backed check of final claims; it does not recover the generator's hidden internal cause or establish a universal prevention mechanism.

| Cohort | Pairs | Raw judge material errors before | Raw judge material errors after |
| --- | ---: | ---: | ---: |
| Fresh generations | ${m.raw_outcomes.fresh.pairs} | ${m.raw_outcomes.fresh.before_material_errors} | ${m.raw_outcomes.fresh.after_material_errors} |
| Historical positive control | ${m.raw_outcomes.positive_control.pairs} | ${m.raw_outcomes.positive_control.before_material_errors} | ${m.raw_outcomes.positive_control.after_material_errors} |

Author adjudication: ${a.summary} Full first-pass judge findings remain in [judge-results.json](judge-results.json), including any rejected flags. Final dispositions and decisive evidence are in [adjudication.json](adjudication.json). No generated answer, verifier response or judge response was edited or semantically rerun.

${a.findings.map(f=>`- **${f.run_id}: ${f.disposition}.** ${f.reason}\n  - Before: ${JSON.stringify(f.before_excerpt)}\n  - After: ${JSON.stringify(f.after_excerpt)}\n  - Source: ${JSON.stringify(f.source_excerpt)}\n  - Evidence: ${f.evidence}`).join('\n')}

The guard returned ${batch.result.reduce((s,r)=>s+r.corrections,0)} exact text corrections across ${batch.result.filter(r=>r.corrections).length} answers, with ${batch.result.reduce((s,r)=>s+r.unresolved,0)} explicitly unresolved material issues. Corrections are not themselves proof of quality: the fresh paired judges assess both the before and after answers, including lost information and introduced errors.

## Method and isolation

Three repetitions each of hydration, buying and packaging use the existing complete real-evidence sets and the byte-identical full-update generation prompts. Hydration exposes benefit/non-worsening and texture qualifications; buying exposes completed behavior, intention and adverse outcomes alongside loyalty; packaging exposes favorable reception alongside leaks, remedies and retention. These are three purposive cases with overlapping accounts, not nine independent populations or a new market sample.

Every fresh baseline is generated normally using gpt-6-astra / medium / CLI 0.153.4, matching the existing commissioned reader comparability exception. Exact source retrieval remains available under the unchanged two-round resource boundary. Each baseline then gets one fresh verifier using gpt-6-astra / high / CLI 0.153.4 and the complete actual reader input, original answer and retrieval-round count. The verifier receives no prior answer keys, judgment or known-error label. It may propose exact-once substring replacements in string fields only, each linked to source evidence; it cannot silently rewrite unrelated content or structured counts. Unrepairable material issues stay explicit. Host application is deterministic and validated independently.

The historical hydration answer is included once as a separate positive control. Its earlier generation cost is not charged again. It is not a fresh-run error-rate observation, and success on it alone cannot establish fresh-case prevention efficacy.

Three fresh case judges using gpt-6-astra / high / CLI 0.153.4 receive the exact before/after answers under opaque pair IDs and deterministic hash-swapped A/B labels. They receive neither verifier rationales nor method identity. Each answer is assessed against actual reader evidence; historical split boundaries absent from the reader are not imposed by the judge. Exact retrieval provenance is supplied to avoid the earlier procedural-history grading error. Both labels are assessed independently; a matching answer is not a truth key. This pairing isolates observed text changes, but stochastic judging and shared model-family blind spots remain.

The frozen scripts and quality prompts are [freeze.json](freeze.json), [verifier.txt](verifier.txt) and [judge.txt](judge.txt). The preparation plan and success standard were frozen before calls. [experiment.mjs](experiment.mjs) supervises six concurrent workers for generation/verification. Four first-pass applications stopped because the verifier used the actual input's /answer/report pointer while the host assumed /report. Every exact substring matched once. [resume.mjs](resume.mjs) removes only that unambiguous wrapper prefix, applies the original responses, and launches the three originally planned judges. The original frozen script, first-pass failures and responses remain untouched; no model was rerun. This mechanical adapter recovery and its freeze are preserved in recovery.json and recovery-freeze.json. Routine operations stay in code; coordinator substantive input is restricted to compact outcomes and decisive excerpts.

## Native cost and latency

| Component | Input | Cached subset | Output | Reasoning subset | Input + output |
| --- | ---: | ---: | ---: | ---: | ---: |
${['generators','verifiers','judges','coordinator'].map(k=>{const t=m.totals[k];return `| ${k} | ${num(t.input_tokens)} | ${num(t.cached_input_tokens)} | ${num(t.output_tokens)} | ${num(t.reasoning_output_tokens)} | ${num(t.total_tokens)} |`;}).join('\n')}
| **Combined at cutoff** | | | | | **${num(m.totals.combined)}** |

The fresh nine-answer generation cost is ${num(m.cohort_costs.fresh.generators.total_tokens)} tokens. Their added verification costs ${num(m.cohort_costs.fresh.verifiers.total_tokens)} tokens (${(100*m.cohort_costs.fresh.verifiers.total_tokens/m.cohort_costs.fresh.generators.total_tokens).toFixed(1)}% of generation cost). The separate positive-control verification costs ${num(m.cohort_costs.positive_control.verifiers.total_tokens)} tokens. Experimental judges cost ${num(m.totals.judges.total_tokens)} tokens and remain included in total experimental cost; they are not hidden as coordinator savings. No claim is made that an eventual operating guard can dispense with outcome assessment on this evidence alone.

Actual model launches: ${m.totals.generators.launches} generator calls including retrieval, ${m.totals.verifiers.launches} verifiers and ${m.totals.judges.launches} judges. Their settings and native IDs/start/finish times, exits, counters, model-call proxies and byte sizes are preserved per call in [measurement.json](measurement.json). Cached input is included once within input; reasoning is included once within output. Bytes are recorded separately and are not token savings. Semantic retries: zero.

Supervised model work took ${min(m.elapsed.supervised_ms)} minutes. Current user turn through the available counter cutoff took ${min(m.elapsed.turn_to_cutoff_ms)} minutes. Per-role summed process durations, which are not concurrent elapsed time, are in measurement.json.

## Validation and measured boundary

[measure.mjs](measure.mjs) verifies frozen identity; all nine fresh generator prompt identities against the previous full-update construction; exact complete source/context inputs; baseline source-index participation; unique cold native sessions and actual stdin; no tool/history contamination; observed model/effort/CLI; real exits and native event/counter agreement; complete before/after pairs and masking; and exact correction-only changes. Material quality remains a source-backed judgment rather than a string/count check. Saved totals are reproduced with \`node docs/research/diagnosis_fully_batched_coordination_20260909/verification_experiment/measure.mjs --check\` against the pinned cutoff.

Coordinator measurement begins with this experiment's user turn at **${m.coordinator.turn_started_at}**, subtracting the immediately preceding native cumulative counter. Prior experiments and intervening discussion are excluded; any reprocessing of their context during this turn remains charged. Preparation, script work, waiting, grading and report/publication preparation are mixed intervals included through the cutoff, not causally allocated phases.

**One final available counter cutoff: ${m.coordinator.last_counter.timestamp}.** Native session: \`${m.coordinator.session}\`. Subsequent publication, recovery and final-response costs remain explicit unallocated residual for parent finalization through the turn's task_complete event. Do not recursively rewrite reports chasing the final token. All generator, verifier and judge costs are complete.

This is a bounded sample experiment, not a production guard, doctrine change, rollout, whole-corpus continuation, causal proof or general non-inferiority claim. The semantic operating contract's supported route remains unchanged. The existing draft PR remains held for different-vendor operator-courier review and author adjudication before merge; these same-vendor experimental graders do not satisfy that lane. No merge or automatic continuation.
`;
await write('report.md',report);console.log(JSON.stringify({report:'verification_experiment/report.md',conclusion:a.conclusion,totals:m.totals,cutoff:m.coordinator.last_counter.timestamp}));
