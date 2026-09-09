// Sample-local fixed experiment; no production or doctrine changes.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn,execFileSync} from 'node:child_process';
import {sha,assert,executable,native,sessionPath} from '../lib.mjs';
export const dir=path.dirname(fileURLToPath(import.meta.url)),parent=path.dirname(dir);
export const read=async n=>JSON.parse(await fs.readFile(dir+'/'+n,'utf8'));
export const write=async(n,v)=>fs.writeFile(dir+'/'+n,typeof v==='string'?v:JSON.stringify(v,null,2));
const str={type:'string'},arr=items=>({type:'array',items}),obj=properties=>({type:'object',additionalProperties:false,properties,required:Object.keys(properties)});
const cases=['hydration','buying','packaging'];
const checkpoint=async name=>{const n=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'));delete n.es;await write(name+'-checkpoint.json',n);};
export async function freezeCheck(){for(const f of(await read('freeze.json')).files)assert(sha(await fs.readFile(dir+'/'+f.path))===f.sha256,'Frozen mismatch '+f.path);}
async function prepare(){
 assert(execFileSync(executable,['--version'],{encoding:'utf8',windowsHide:true}).trim()==='codex-cli 0.153.4','CLI comparability');
 const n=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'));
 const start=n.es.findLast(e=>e.type==='event_msg'&&e.payload?.type==='task_started');assert(start,'Experiment turn start missing');
 const before=n.counters.filter(c=>c.timestamp<start.timestamp).at(-1);assert(before,'Prior cumulative counter missing');
 await write('coordinator-start.json',{session:n.file,turn_started_at:start.timestamp,base_counter:before,capture_at:new Date().toISOString(),accounting:'Current experiment turn from its start, including preparation before this capture. Prior experiment and intervening discussion are excluded; their reprocessed context charged in this turn remains included.'});
 await write('verifier.schema.json',obj({corrections:arr(obj({pointer:str,old_text:str,new_text:str,source_keys:arr(str),source_excerpt:str,reason:str})),unresolved_material_issues:arr(str),summary:str}));
 const error=obj({label:str,answer_excerpt:str,source_keys:arr(str),source_excerpt:str,reason:str});
 await write('judge.schema.json',obj({case:str,summary:str,pairs:arr(obj({pair_id:str,answers:arr(obj({label:str,material_errors:arr(error),nonmaterial_notes:arr(str)}))}))}));
 const plan={created_at:new Date().toISOString(),cases,repeats:3,fresh_generations:9,positive_control:{case:'hydration',answer:'../runs/hydration-full-update/final.json',role:'Known earlier error, separate from fresh-run error rate; unlabeled to verifier and judge.'},reader_settings:{model:'gpt-6-astra',effort:'medium',cli:'0.153.4',authority:'Inherited commissioned baseline-reader comparability exception'},verifier_and_judge_settings:{model:'gpt-6-astra',effort:'high',cli:'0.153.4'},intervention:'One fresh source-backed verifier per answer; host applies only exact-once substring patches to string fields. No semantic retries. Unrepairable material issues remain explicit.',assessment:'Three independent fresh case sessions assess blinded A/B pairs against actual full-reader inputs and retrieved-history receipts. Host unblinds after assessment.',success:'All independently accepted material errors corrected, none introduced, no material information lost; fresh-run and positive-control outcomes reported separately. Zero fresh baseline errors is inconclusive for fresh-case prevention efficacy, even if positive control is fixed.',measurement:'All nine generations, ten verifiers, three judges and current-turn coordinator native input+output separately and combined. Cached-input/reasoning subsets counted once. Incremental verifier tokens and paired outcomes are primary; byte sizes and latency separate. No claim of guaranteed prevention or general non-inferiority.',scope:'This verification_experiment subfolder plus nearest research index/PR description; existing experimental artifacts remain unchanged.'};
 await write('plan.json',plan);
 const paths=['experiment.mjs','verifier.txt','judge.txt','verifier.schema.json','judge.schema.json','plan.json','../common.txt','../authority-context.txt','../response.schema.json','../sources.json','../count-definitions.json',...cases.map(c=>'../runs/'+c+'-full-update/input.json'),'../runs/hydration-full-update/final.json'];
 await write('freeze.json',{frozen_at:new Date().toISOString(),source_parent_head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),files:await Promise.all(paths.map(async p=>({path:p,sha256:sha(await fs.readFile(dir+'/'+p))})))});
 console.log(JSON.stringify({frozen:true,generations:9,verifiers:10,judges:3,turn_started_at:start.timestamp,base_native_total:before.usage.input_tokens+before.usage.output_tokens}));
}
async function call(base,prompt,schema,role,effort){
 await fs.mkdir(dir+'/'+base,{recursive:true});await write(base+'/stdin.txt',prompt);
 const args=['exec','--json','--model','gpt-6-astra','-c','model_reasoning_effort="'+effort+'"','-C',dir+'/'+base,'--disable','shell_tool','--output-schema',schema,'--output-last-message',dir+'/'+base+'/response.json','-'];
 await write(base+'/invocation.json',{executable,args,role,effort,no_resume:true,stdin_sha256:sha(prompt)});
 const out=await fs.open(dir+'/'+base+'/events.jsonl','wx'),err=await fs.open(dir+'/'+base+'/stderr.log','wx');const started_at=new Date().toISOString();
 const child=spawn(executable,args,{cwd:dir+'/'+base,windowsHide:true,stdio:['pipe',out.fd,err.fd]});child.stdin.on('error',()=>{});child.stdin.end(prompt);
 const exit=await new Promise(resolve=>{child.on('error',e=>resolve({code:null,error:e.message}));child.on('close',(code,signal)=>resolve({code,signal}));});await out.close();await err.close();
 const events=(await fs.readFile(dir+'/'+base+'/events.jsonl','utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);
 const turns=events.filter(e=>e.type==='turn.completed'),usage=turns.reduce((a,e)=>{for(const[k,v]of Object.entries(e.usage??{}))if(typeof v==='number')a[k]=(a[k]??0)+v;return a;},{});
 const id=events.find(e=>e.type==='thread.started')?.thread_id;
 await write(base+'/receipt.json',{base,role,effort,started_at,finished_at:new Date().toISOString(),...exit,id,usage,turns:turns.length});
 assert(exit.code===0&&id&&turns.length>0&&!events.some(e=>['error','turn.failed'].includes(e.type)),'Model call failed '+base);
 assert(!events.some(e=>e.item&&/command_execution|mcp_tool_call|web_search/.test(e.item.type)),'Unexpected tools '+base);
 return read(base+'/response.json');
}
const pack=(fixture,keys,c)=>{const records=keys.map(k=>{const r=fixture.records.find(r=>r.key===k);assert(r,'Unknown retrieval '+k);return r;});const refs=new Set(records.flatMap(r=>r.context_refs??[]));return {records,contexts:fixture.contexts.filter(x=>refs.has(x.context_id)),...(c==='packaging'?{source_limits:fixture.packaging_limits}:{})};};
function patch(answer,corrections){const out=structuredClone(answer);for(const c of corrections){assert(c.pointer.startsWith('/'),'Invalid JSON pointer');const parts=c.pointer.slice(1).split('/').map(s=>s.replaceAll('~1','/').replaceAll('~0','~'));assert(!parts.some(s=>['__proto__','constructor','prototype'].includes(s)),'Unsafe pointer');let at=out;for(const p of parts.slice(0,-1)){assert(at&&Object.hasOwn(at,p),'Missing pointer');at=at[p];}const key=parts.at(-1);assert(typeof at[key]==='string'&&c.old_text.length>0,'String-only correction');assert(at[key].split(c.old_text).length===2,'Correction must match exactly once '+c.pointer);at[key]=at[key].replace(c.old_text,c.new_text);}return out;}
async function run(){
 await freezeCheck();const started_at=new Date().toISOString(),plan=await read('plan.json'),fixture=JSON.parse(await fs.readFile(parent+'/sources.json','utf8'));
 const authority=await fs.readFile(parent+'/authority-context.txt','utf8'),common=await fs.readFile(parent+'/common.txt','utf8'),verifier=await fs.readFile(dir+'/verifier.txt','utf8'),judge=await fs.readFile(dir+'/judge.txt','utf8');
 const result=[],queue=[];
 for(const c of cases)for(let r=1;r<=plan.repeats;r++)queue.push({case:c,id:c+'-r'+r,positive_control:false});queue.push({case:'hydration',id:'hydration-control',positive_control:true});
 // Six supervised workers; the tenth job is the separate historical positive control.
 async function job(j){
  const base='runs/'+j.id,input=JSON.parse(await fs.readFile(parent+'/runs/'+j.case+'-full-update/input.json','utf8'));await fs.mkdir(dir+'/'+base,{recursive:true});await write(base+'/reader-input.json',input);
  let answer,retrievals=0;
  if(j.positive_control){answer=JSON.parse(await fs.readFile(parent+'/runs/hydration-full-update/final.json','utf8'));retrievals=1;}
  else {let prompt=common+'\nClaim-support authority:\n'+authority+'\nSaved stage input:\n'+JSON.stringify(input);
   for(let round=0;round<=2;round++){answer=await call(base+'/generation-'+round,prompt,parent+'/response.schema.json','generator','medium');if(!answer.retrieval_requests.length){retrievals=round;break;}await write(base+'/generation-'+round+'/retrieval.json',{requested:answer.retrieval_requests});assert(round<2,'Retrieval bound reached');const requested=answer.retrieval_requests.map(k=>{if(input.focal_keys.includes(k))return {key:k,...pack(fixture,[k],j.case)};const ctx=fixture.contexts.find(x=>x.context_id===k);assert(ctx&&input.sources.contexts.some(x=>x.context_id===k),'Unauthorized retrieval');return ctx;});prompt+='\nYour source retrieval request (not an answer):\n'+JSON.stringify(answer)+'\nExact requested frozen sources:\n'+JSON.stringify(requested)+'\nNow answer the same diagnostic question and count definitions. Request further sources only if necessary.';}
  }
  await write(base+'/baseline.json',answer);await write(base+'/provenance.json',{...j,retrievals,semantic_retries:0});
  const vInput={reader_input:input,answer,retrieval_rounds:retrievals};await write(base+'/verifier-input.json',vInput);
  const v=await call(base+'/verifier',verifier+'\n'+authority+'\nInput:\n'+JSON.stringify(vInput),dir+'/verifier.schema.json','verifier','high');
  const corrected=patch(answer,v.corrections);await write(base+'/corrected.json',corrected);
  result.push({...j,retrievals,corrections:v.corrections.length,unresolved:v.unresolved_material_issues.length});
 }
 const failures=[];await Promise.all(Array.from({length:6},async()=>{while(queue.length){const j=queue.shift();try{await job(j);}catch(e){failures.push({id:j.id,error:e.message});}}}));
 await write('batch-result.json',{started_at,finished_at:new Date().toISOString(),result,failures});await checkpoint('verification');
 assert(!failures.length,'First-pass job failure; no semantic retries');console.log(JSON.stringify({checkpoint:'verification_complete',jobs:result.length,corrections:result.reduce((s,r)=>s+r.corrections,0)}));
 const mapping={},judged=await Promise.allSettled(cases.map(async c=>{
  const pairs=[];for(const j of result.filter(r=>r.case===c).sort((a,b)=>a.id.localeCompare(b.id))){const before=await read('runs/'+j.id+'/baseline.json'),after=await read('runs/'+j.id+'/corrected.json');const id='pair-'+sha(j.id).slice(0,10),swap=parseInt(sha(j.id).slice(-2),16)%2===1;mapping[id]={run_id:j.id,case:c,positive_control:j.positive_control,baseline_label:swap?'B':'A',corrected_label:swap?'A':'B'};pairs.push({pair_id:id,reader_input:await read('runs/'+j.id+'/reader-input.json'),retrieval_rounds:j.retrievals,answers:[{label:'A',answer:swap?after:before},{label:'B',answer:swap?before:after}]});}
  const input={case:c,pairs};await fs.mkdir(dir+'/judges/'+c,{recursive:true});await write('judges/'+c+'/input.json',input);
  return call('judges/'+c,judge+'\n'+authority+'\nPairs:\n'+JSON.stringify(input),dir+'/judge.schema.json','judge','high');
 }));
 await write('blind-mapping.json',mapping);await write('judge-results.json',judged.map(x=>x.status==='fulfilled'?x.value:{error:x.reason?.message}));await checkpoint('judges');
 await write('supervision.json',{started_at,finished_at:new Date().toISOString(),semantic_retries:0,job_failures:failures,judge_failures:judged.filter(x=>x.status==='rejected').map(x=>x.reason.message)});
 assert(judged.every(x=>x.status==='fulfilled'),'Judge failure preserved');console.log(JSON.stringify({checkpoint:'judges_complete',cases:judged.length,finished_at:new Date().toISOString()}));
}
if(process.argv[2]==='prepare')await prepare();else if(process.argv[2]==='run')await run();
