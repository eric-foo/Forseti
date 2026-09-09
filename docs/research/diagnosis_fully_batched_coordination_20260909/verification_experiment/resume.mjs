// Mechanical recovery only: verifier pointers may be rooted at the actual input's /answer.
// Preserve the original frozen runner, responses and first-pass failure receipt.
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {dir,parent,read,write,freezeCheck} from './experiment.mjs';
import {sha,assert,executable,native,sessionPath} from '../lib.mjs';
await freezeCheck();
await write('recovery-freeze.json',{frozen_at:new Date().toISOString(),scope:'Accept input-rooted /answer pointers by removing only the wrapper prefix; exact-once patch checks unchanged. Launch the three originally planned judges. No generator/verifier or semantic retries.',files:await Promise.all(['resume.mjs','judge.txt','judge.schema.json'].map(async path=>({path,sha256:sha(await fs.readFile(dir+'/'+path))})))});
const batch=await read('batch-result.json'),result=[...batch.result],recovered=[];
for(const failure of batch.failures){
 const base='runs/'+failure.id,before=await read(base+'/baseline.json'),input=await read(base+'/verifier-input.json'),v=await read(base+'/verifier/response.json'),after=structuredClone(before);
 assert(JSON.stringify(input.answer)===JSON.stringify(before),'Input answer identity');
 const pointers=[];for(const c of v.corrections){assert(c.pointer.startsWith('/answer/'),'Recovery is limited to input-rooted answer pointers');const pointer=c.pointer.slice('/answer'.length),keys=pointer.slice(1).split('/').map(x=>x.replaceAll('~1','/').replaceAll('~0','~'));assert(!keys.some(x=>['__proto__','constructor','prototype'].includes(x)),'Unsafe pointer');let at=after;for(const k of keys.slice(0,-1)){assert(Object.hasOwn(at,k),'Missing normalized pointer');at=at[k];}const k=keys.at(-1);assert(typeof at[k]==='string'&&c.old_text&&at[k].split(c.old_text).length===2,'Exact-once normalized correction');at[k]=at[k].replace(c.old_text,c.new_text);pointers.push({original:c.pointer,normalized:pointer});}
 await write(base+'/corrected.json',after);const p=await read(base+'/provenance.json');result.push({...p,corrections:v.corrections.length,unresolved:v.unresolved_material_issues.length});recovered.push({id:failure.id,original_error:failure.error,pointers,verifier_response_sha256:sha(await fs.readFile(dir+'/'+base+'/verifier/response.json')),generator_and_verifier_reruns:0});
}
await write('recovery.json',{reason:'Four verifiers rooted pointers at /answer/report in their actual input; the host incorrectly assumed answer-relative pointers. Every exact substring matched once. Normalize only that wrapper prefix, with no semantic edits, dropped corrections or model retries.',recovered});
await write('completed-batch.json',{...batch,result,first_pass_failures:batch.failures,failures:[],recovery:'recovery.json'});
console.log(JSON.stringify({checkpoint:'mechanical_recovery_complete',recovered:recovered.length,semantic_retries:0}));
const authority=await fs.readFile(parent+'/authority-context.txt','utf8'),judge=await fs.readFile(dir+'/judge.txt','utf8'),mapping={};
const judged=await Promise.allSettled(['hydration','buying','packaging'].map(async c=>{
 const pairs=[];for(const j of result.filter(r=>r.case===c).sort((a,b)=>a.id.localeCompare(b.id))){const before=await read('runs/'+j.id+'/baseline.json'),after=await read('runs/'+j.id+'/corrected.json'),id='pair-'+sha(j.id).slice(0,10),swap=parseInt(sha(j.id).slice(-2),16)%2===1;mapping[id]={run_id:j.id,case:c,positive_control:j.positive_control,baseline_label:swap?'B':'A',corrected_label:swap?'A':'B'};pairs.push({pair_id:id,reader_input:await read('runs/'+j.id+'/reader-input.json'),retrieval_rounds:j.retrievals,answers:[{label:'A',answer:swap?after:before},{label:'B',answer:swap?before:after}]});}
 const base='judges/'+c,input={case:c,pairs};await fs.mkdir(dir+'/'+base,{recursive:true});await write(base+'/input.json',input);
 const prompt=judge+'\n'+authority+'\nPairs:\n'+JSON.stringify(input);await write(base+'/stdin.txt',prompt);
 const args=['exec','--json','--model','gpt-6-astra','-c','model_reasoning_effort="high"','-C',dir+'/'+base,'--disable','shell_tool','--output-schema',dir+'/judge.schema.json','--output-last-message',dir+'/'+base+'/response.json','-'];
 await write(base+'/invocation.json',{executable,args,role:'judge',effort:'high',no_resume:true,stdin_sha256:sha(prompt)});
 const out=await fs.open(dir+'/'+base+'/events.jsonl','wx'),err=await fs.open(dir+'/'+base+'/stderr.log','wx'),started_at=new Date().toISOString();
 const child=spawn(executable,args,{cwd:dir+'/'+base,windowsHide:true,stdio:['pipe',out.fd,err.fd]});child.stdin.on('error',()=>{});child.stdin.end(prompt);
 const exit=await new Promise(resolve=>{child.on('error',e=>resolve({code:null,error:e.message}));child.on('close',(code,signal)=>resolve({code,signal}));});await out.close();await err.close();
 const events=(await fs.readFile(dir+'/'+base+'/events.jsonl','utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse),turns=events.filter(e=>e.type==='turn.completed'),usage=turns.reduce((a,e)=>{for(const[k,v]of Object.entries(e.usage??{}))if(typeof v==='number')a[k]=(a[k]??0)+v;return a;},{}),id=events.find(e=>e.type==='thread.started')?.thread_id;
 await write(base+'/receipt.json',{base,role:'judge',effort:'high',started_at,finished_at:new Date().toISOString(),...exit,id,usage,turns:turns.length});assert(exit.code===0&&id&&turns.length>0&&!events.some(e=>['error','turn.failed'].includes(e.type)),'Judge failure');return read(base+'/response.json');
}));
await write('blind-mapping.json',mapping);await write('judge-results.json',judged.map(x=>x.status==='fulfilled'?x.value:{error:x.reason?.message}));const n=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'));delete n.es;await write('judges-checkpoint.json',n);
await write('supervision.json',{started_at:batch.started_at,finished_at:new Date().toISOString(),semantic_retries:0,first_pass_job_failures:batch.failures,recovery:'recovery.json',job_failures:[],judge_failures:judged.filter(x=>x.status==='rejected').map(x=>x.reason.message)});assert(judged.every(x=>x.status==='fulfilled'),'Judge failure preserved');console.log(JSON.stringify({checkpoint:'judges_complete',cases:judged.length}));
