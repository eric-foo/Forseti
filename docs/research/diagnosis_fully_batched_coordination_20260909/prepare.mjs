import fs from 'node:fs/promises';
import {dir,root,sha,read,write,assert,sessionPath,native,executable} from './lib.mjs';
const prior='C:/Users/vmon7/.codex/worktrees/72b7/orca/docs/research/diagnosis_batched_coordination_20260909';
const copied=['sources.json','experiment.json','count-definitions.json','common.txt','authority-context.txt','response.schema.json','run.mjs','source-validation.json'];
for(const n of copied)assert(sha(await fs.readFile(dir+'/'+n))===sha(await fs.readFile(prior+'/'+n)),'Copied mismatch '+n);
const sv=await read('source-validation.json');
const refs=[];for(const r of sv.pins){assert(sha(await fs.readFile(r.path))===r.sha256,'Raw changed '+r.path);refs.push(r);}
const sourceKeys=Object.keys(sv); // Preserve schema discovery without source bodies.
const str={type:'string'},strings={type:'array',items:str};
const issue={type:'object',additionalProperties:false,properties:{material:{type:'boolean'},answers:strings,source_keys:strings,answer_excerpt:str,source_excerpt:str,rationale:str},required:['material','answers','source_keys','answer_excerpt','source_excerpt','rationale']};
await write('judge.schema.json',{type:'object',additionalProperties:false,properties:{case:str,material_errors:{type:'integer'},summary:str,issues:{type:'array',items:issue},answer_verdicts:{type:'array',items:{type:'object',additionalProperties:false,properties:{answer:str,material_errors:{type:'integer'},diagnostic_quality:str},required:['answer','material_errors','diagnostic_quality']}}},required:['case','material_errors','summary','issues','answer_verdicts']});
const frozen=[...copied,'quality-standard.txt','judge.schema.json','lib.mjs','prepare.mjs','supervise.mjs'];
await write('freeze.json',{frozen_at:new Date().toISOString(),files:await Promise.all(frozen.map(async name=>({name,sha256:sha(await fs.readFile(dir+'/'+name))}))),prior,root,base:'46fbf6ffdc576b20014fab8ceea3fcedbf837a0c',settings:{executable,readers:'gpt-6-astra / medium / CLI 0.153.4',judges:'gpt-6-astra / high / CLI 0.153.4'},quality_standard:'quality-standard.txt',semantic_retries:0,source_validation_keys:sourceKeys,raw_reverified:refs});
const baseline=[];
for(const [name,id,cutoff,expected] of [['original','01a08635-c16b-7b22-99ea-c175d65209db',null,11194579],['partial_batch','01a0865a-240b-73c2-8028-45fea9d93369','2026-09-09T13:43:56.221Z',6017382]]){
 const n=await native(await sessionPath(id),cutoff);delete n.es;const total=n.last_counter.usage.input_tokens+n.last_counter.usage.output_tokens;assert(total===expected,'Baseline mismatch '+name+' '+total);baseline.push({name,cutoff,...n,readers:name==='original'?518066:444917,coordinator:total,combined:total+(name==='original'?518066:444917)});
}
await write('baselines.json',baseline);
const coordinator=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'));delete coordinator.es;await write('preparation-checkpoint.json',coordinator);
console.log(JSON.stringify({frozen:true,baseline_totals:baseline.map(b=>({name:b.name,total:b.combined})),source_validation_keys:sourceKeys,raw_hashes_verified:refs.length,coordinator_tokens:coordinator.last_counter?.usage}));
