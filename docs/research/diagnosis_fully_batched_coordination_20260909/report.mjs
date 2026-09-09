import fs from 'node:fs/promises';
import {dir,read,write} from './lib.mjs';
const m=await read('measurement.json'),judges=await read('judge-results.json'),freeze=await read('freeze.json');
const publication=await read('publication.json').catch(()=>null);
const n=x=>x.toLocaleString('en-US'),minutes=x=>(x/60000).toFixed(2);
const adjudication=await read('author-adjudication.json');
const material=adjudication.accepted_material_errors;
let report=`# Fully batched diagnostic coordination — 2026-09-09

\`\`\`yaml
retrieval_header_version: 1
artifact_role: bounded real-evidence experiment report
scope: Three fixed diagnostic cases; six cold arm/case runs with initial and update stages and three isolated case judges.
authority_boundary: retrieval_only
use_when:
  - Comparing this sample's diagnostic quality and complete native costs with the two earlier experiments.
open_next:
  - measurement.json
  - judge-results.json
  - freeze.json
stale_if:
  - Frozen inputs, generated answers, quality standard, or measured counter boundary changes.
\`\`\`

${material===0?'No material diagnostic errors remain after author adjudication.':'One material diagnostic overstatement remains after author adjudication: the full hydration update turns hydration without causing congestion into reduced congestion. No material errors were found in the incremental arm. The strict no-new-material-error condition across all generated answers is not met; token reduction does not override that result.'} This is a practical stochastic before/after comparison on selected real evidence, not causal proof, general non-inferiority, market coverage or production scalability. No method rollout or stopped whole-corpus work was performed.

## Material diagnostic findings

The quality standard was frozen before calls in [quality-standard.txt](quality-standard.txt). It follows the owner’s decision-effect test and explicitly accepts the prior Softwear manufacturer/reluctance omission and understandable stopping-versus-replacement classification issue. Neither is an automatic blocker. Actual behavioral invention, unsupported attribution, or material loss of support/conditions remains a defect. Review updated_at is not engagement observed_at; functional redundancy alone is not actual discontinuation/substitution. No separate routine_stopped count was requested.

The three first-pass judges flagged three material candidates. [Author adjudication](author-adjudication.json) accepts one and rejects two with bounded saved evidence: the full-update reader did not receive the historical split that the judge assumed it had; and the buying answer explicitly retains community stock-up evidence while withholding formal cross-venue corroboration because independent-origin credit is unavailable. Its support-posture difference does not erase reported buying behavior. Saved retrieval receipts also defeat the judge's nonmaterial procedural-history criticism. No judge or reader was rerun or edited. The following case sections preserve the raw first-pass assessments; the author dispositions above and in author-adjudication.json are the final experiment findings.
`;
for(const j of judges){report+=`\n### ${j.case}\n\n${j.summary}\n\n`;for(const i of j.issues)report+=`- **${i.material?'Material':'Nonmaterial'} — ${i.answers.join(', ')}; ${i.source_keys.join(', ')}.** ${i.rationale}\n  - Answer excerpt: ${JSON.stringify(i.answer_excerpt)}\n  - Source excerpt: ${JSON.stringify(i.source_excerpt)}\n`;report+=`\nFull saved case assessment: [judges/${j.case}/response.json](judges/${j.case}/response.json); complete relevant inputs: [judges/${j.case}/input.json](judges/${j.case}/input.json).\n`;}
report+=`
## Native token comparison

| Experiment | Readers | Judges | Coordinator | Combined |
| --- | ---: | ---: | ---: | ---: |
${m.baselines.map(b=>`| ${b.name} | ${n(b.readers)} | 0 separately launched | ${n(b.coordinator)} | ${n(b.combined)} |`).join('\n')}
| Fully batched, measured cutoff | ${n(m.totals.readers.total_tokens)} | ${n(m.totals.judges.total_tokens)} | ${n(m.totals.coordinator.total_tokens)} | ${n(m.totals.combined)} |

${m.comparisons.map(c=>`Combined reduction against ${c.name}: **${c.reduction_percent.toFixed(2)}%**, or ${n(c.saved_tokens)} native tokens.`).join(' ')} Quality has priority over tokens, then latency. ${material===0&&m.comparisons.every(c=>c.reduction_percent>0)?'The observed sample meets the commissioned quality-and-token target at this cutoff.':'The commissioned combined quality-and-token success condition is not established.'}

| Component | Input | Cached subset | Output | Reasoning subset |
| --- | ---: | ---: | ---: | ---: |
${['readers','judges','coordinator'].map(k=>{const t=m.totals[k];return `| ${k} | ${n(t.input_tokens)} | ${n(t.cached_input_tokens)} | ${n(t.output_tokens)} | ${n(t.reasoning_output_tokens)} |`;}).join('\n')}

Input plus output is the total. Cached input is counted once within input; reasoning is counted once within output. Native sessions mechanically verify both earlier reader totals and coordinator totals. Partial-batch accounting ends at the original completed turn, **2026-09-09T13:43:56.221Z**, excluding later explanatory turns. Earlier failed launches without exposed usage remain identified in measurement.json, with no invented token estimate.

Current readers: ${m.totals.readers.launches} launches, ${m.totals.readers.model_calls} distinct native usage updates. Judges: ${m.totals.judges.launches} launches, ${m.totals.judges.model_calls} distinct native usage updates. Coordinator: ${m.coordinator.model_calls} distinct native usage updates, ${m.coordinator.tool_calls} tool-call items, ${m.coordinator.tool_outputs} tool-output items. These are native-counter model-call proxies, not network-attempt counts. The coordinator’s code invocations do not create model calls except the explicitly launched readers and judges. Retrieval rounds are separately identified per call; semantic retries: zero.

Reader arm totals including initial findings and retrieval: incremental ${n(m.arm_totals.incremental.total_tokens)}, full ${n(m.arm_totals.full.total_tokens)}. These arm totals exclude shared judges and coordinator; only the combined comparison includes whole-task measured costs.

## Latency and cumulative coordination boundary

Original session start through completion: ${minutes(m.baselines[0].elapsed_ms)} minutes. Partial batch through its bound original-turn completion: ${minutes(m.baselines[1].elapsed_ms)} minutes. Current coordinator session start through final available token counter: ${minutes(m.elapsed.coordinator_to_counter_ms)} minutes. Current supervised readers plus judges: ${minutes(m.elapsed.batch_and_judges_ms)} minutes. Summed reader process duration: ${minutes(m.totals.readers.serial_wall_ms)} minutes; summed judge duration: ${minutes(m.totals.judges.serial_wall_ms)} minutes. Summed concurrent durations are not elapsed latency. Current cutoff precedes final publication completion, so final end-to-end latency remains for parent finalization.

A single [supervise.mjs](supervise.mjs) launches the six independent arm/case sequences, preserves stdout/stderr/events and exits, handles retrieval through the reused run.mjs, waits for the batch, and launches three fresh isolated case judges. It returns compact completion receipts. Each judge receives only its complete relevant account set, exact generated answers, diagnostic question/count definitions and frozen materiality rules. Judges are source-backed experimental graders, not the mandatory different-vendor review-and-patch lane.

This coordinator did not ingest complete source accounts or all reader answers. It received selected machinery, instruction passages, mechanical receipts and compact case verdicts with decisive excerpts. Instruction/navigation output during preparation was larger than intended and included truncated reads subsequently narrowed; that real preparation cost is included. Bounding each output alone would not bound cumulative input: coordinator native input is therefore counted from session start, and the three relocated judgments are charged separately and included in the combined total. This is substantive bounded coordination for the diagnostic payload, not a fixed token cap on the coordinator or a claim that all overhead is eliminated.

| Coordinator checkpoint | Counter timestamp (UTC) | Cumulative tokens | Delta from prior checkpoint |
| --- | --- | ---: | ---: |
${m.checkpoints.map(p=>`| ${p.label} | ${p.timestamp} | ${n(p.total)} | ${n(p.delta_tokens)} |`).join('\n')}

Checkpoints are mixed intervals: preparation, script authoring, recovery, waiting, assessment, report construction and publication preparation overlap. They are accounting boundaries, not causal phase attribution. No savings are attributed to bytes: frozen sources ${n(m.bytes.frozen_sources)} bytes; model stdin ${n(m.bytes.model_stdin)}; model stdout/events ${n(m.bytes.model_stdout)}; model stderr ${n(m.bytes.model_stderr)}; response/final files ${n(m.bytes.final_answers)} (includes preserved duplicate final copies).

## Validation, scope and residuals

[measure.mjs](measure.mjs) verifies the frozen construction, six raw-source hashes, exact selected account/context packs and initial/addition splits, identical initial prompts across arms, own-findings-only incremental updates, complete-set full updates, source-index participation, unique fresh native sessions, actual input equality and absence of tool/history contamination, actual settings, real exits and native event/counter agreement. Actual readers use gpt-6-astra / medium / CLI 0.153.4; actual judges use gpt-6-astra / high / CLI 0.153.4. The reader exception is commissioned comparability, not a changed project default. All reader and judge stdout/stderr/events, including empty files, are retained by the sample-local .gitignore exceptions.

Semantic assessment is recorded per answer and source in the three first-pass judgments; it is not reduced to mechanical count agreement. Judges see no earlier experiment answers, answer key, grading or originating conversation. Same-vendor judges can share blind spots; no different-vendor review has occurred. The sample is purposive, three cases overlap in sources, arrival splits are experimental rather than chronological, and repeated local context is not a new origin. No production/runtime, doctrine, collection ledger or saturation-state changes are authorized or made. The sample’s scripts/data under research are the explicit exception authorized by this commission.

The method authority remains the semantic evidence integration contract’s Supported operating route and owner-only reopen boundary. Claim judgments follow the intelligence claim-support contract. Frozen reference input provenance is in freeze.json and source-validation.json; owning sources remain read-only. Prior report quality verdicts are superseded only to the extent explicitly stated by the owner in this commission.

**One final available counter cutoff:** ${m.coordinator.last_counter.timestamp}. Native coordinator session: \`${m.coordinator.file}\`. Parent finalization should read counters mechanically through the final task_complete event and add the difference to the reported coordinator/combined totals; do not import messages or recursively revise this report to chase the final token. Code-only closeout after the cutoff and the final coordinator response are explicitly unallocated. Reader/judge costs are complete. The saved measurement is reproduced with \`node docs/research/diagnosis_fully_batched_coordination_20260909/measure.mjs --check\` using its pinned cutoff.

Publication: ${publication?`Draft PR ${publication.url}; initial published commit ${publication.initial_head}. Final report and measurement are committed and pushed by the same closeout sequence after this metadata is written; exact final remote hash is returned by the sequence.`:'Closeout will commit, read back durable bytes, push and create a draft PR after validation.'} No merge or automatic continuation. Different-vendor operator-courier review and author adjudication remain mandatory before merge; the case judges do not satisfy that requirement.
`;
await write('report.md',report);
console.log(JSON.stringify({report:'report.md',material_errors:material,combined_tokens:m.totals.combined,cutoff:m.coordinator.last_counter.timestamp}));
