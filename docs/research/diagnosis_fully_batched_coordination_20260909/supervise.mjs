import fs from 'node:fs/promises';
import path from 'node:path';
import {dir,read,write,sha,assert,command,executable,native,sessionPath} from './lib.mjs';
for(const f of(await read('freeze.json')).files)assert(sha(await fs.readFile(dir+'/'+f.name))===f.sha256,'Freeze '+f.name);
const start=new Date().toISOString(),plan=await read('experiment.json'),fixture=await read('sources.json'),results=[];
await fs.mkdir(dir+'/runs',{recursive:true});await fs.mkdir(dir+'/judges',{recursive:true});
async function checkpoint(phase){const n=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'));delete n.es;await write(phase+'-checkpoint.json',n);}
async function stage(c,a,s){const r=await command('batch-'+c+'-'+a+'-'+s,process.execPath,[dir+'/run.mjs',c,a,s]);results.push(r);assert(r.code===0,'Reader failed '+r.label);}
const outcomes=await Promise.allSettled(Object.keys(plan.cases).flatMap(c=>['incremental','full'].map(async a=>{await stage(c,a,'initial');await stage(c,a,'update');})));
await write('batch-result.json',{start,finish:new Date().toISOString(),results,outcomes:outcomes.map(o=>({status:o.status,error:o.reason?.message??null}))});await checkpoint('readers');
assert(outcomes.every(o=>o.status==='fulfilled'),'Reader batch failure; first-pass logs preserved');
console.log(JSON.stringify({checkpoint:'readers_complete',stages:results.length,finish:new Date().toISOString()}));
const judged=await Promise.allSettled(Object.entries(plan.cases).map(async([c,p])=>{
 const keys=[...p.initial,...p.additions],records=fixture.records.filter(r=>keys.includes(r.key)),refs=new Set(records.flatMap(r=>r.context_refs??[]));
 const answers={};for(const a of ['incremental','full'])for(const s of ['initial','update'])answers[a+'-'+s]=await read('runs/'+c+'-'+a+'-'+s+'/final.json');
 const input={case:c,question:p.question,initial_keys:p.initial,addition_keys:p.additions,count_definitions:(await read('count-definitions.json'))[c],products:fixture.products,records,contexts:fixture.contexts.filter(x=>refs.has(x.context_id)),...(c==='packaging'?{source_limits:fixture.packaging_limits}:{}),answers};
 const base='judges/'+c;await fs.mkdir(dir+'/'+base);await write(base+'/input.json',input);
 const prompt=await fs.readFile(dir+'/quality-standard.txt','utf8')+'\n'+await fs.readFile(dir+'/authority-context.txt','utf8')+'\nCase input:\n'+JSON.stringify(input);await write(base+'/stdin.txt',prompt);
 const args=['exec','--json','--model','gpt-6-astra','-c','model_reasoning_effort="high"','-C',dir+'/'+base,'--disable','shell_tool','--output-schema',dir+'/judge.schema.json','--output-last-message',dir+'/'+base+'/response.json','-'];
 await write(base+'/invocation.json',{executable,args,stdin_sha256:sha(prompt),no_resume:true});
 const r=await command(base+'/call',executable,args,{cwd:dir+'/'+base,input:prompt});assert(r.code===0,'Judge failed '+c);
 const answer=await read(base+'/response.json');return {case:c,material_errors:answer.material_errors,summary:answer.summary,issues:answer.issues,answer_verdicts:answer.answer_verdicts};
}));
await write('judge-results.json',judged.map(j=>j.status==='fulfilled'?j.value:{error:j.reason?.message}));await checkpoint('judges');
await write('supervision.json',{start,finish:new Date().toISOString(),reader_stages:results.length,judge_outcomes:judged.map(j=>({status:j.status,error:j.reason?.message??null})),semantic_retries:0});
assert(judged.every(j=>j.status==='fulfilled'),'Judge failure; saved first pass');console.log(JSON.stringify({checkpoint:'judges_complete',cases:judged.map(j=>({case:j.value.case,material_errors:j.value.material_errors})),finish:new Date().toISOString()}));
