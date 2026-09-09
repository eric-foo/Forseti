// Sample-local cold diagnostic runner, adapted from the commissioned subscription CLI reference.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(dir,'../../..');
const sha=x=>createHash('sha256').update(x).digest('hex');
const read=async n=>JSON.parse(await fs.readFile(path.join(dir,n),'utf8'));
const write=async(n,v)=>fs.writeFile(path.join(dir,n),typeof v==='string'?v:JSON.stringify(v,null,2),{flag:'wx'});
const fixture=await read('sources.json'),plan=await read('experiment.json');
const [caseName,arm,stage]=process.argv.slice(2);
if(!plan.cases[caseName]||!['incremental','full'].includes(arm)||!['initial','update'].includes(stage))throw Error('Use CASE incremental|full initial|update');
for(const f of (await read('freeze.json')).files)if(sha(await fs.readFile(path.join(dir,f.name)))!==f.sha256)throw Error('Frozen mismatch '+f.name);
const c=plan.cases[caseName],all=[...c.initial,...c.additions];
const records=keys=>keys.map(k=>{const r=fixture.records.find(x=>x.key===k);if(!r)throw Error('Unknown source '+k);return r;});
const pack=keys=>{const rs=records(keys);const refs=new Set(rs.flatMap(r=>r.context_refs??[]));return {records:rs,contexts:fixture.contexts.filter(c=>refs.has(c.context_id)),...(caseName==='packaging'?{source_limits:fixture.packaging_limits}:{})};};
const initial=stage==='initial';
let payload={case:caseName,question:c.question,count_definitions:(await read('count-definitions.json'))[caseName],products:fixture.products,stage:initial?'initial':'updated',focal_keys:initial?c.initial:all};
if(initial)payload.sources=pack(c.initial);
else if(arm==='full'){payload.method='Reread the complete initial and added source set and construct the current diagnosis.';payload.sources=pack(all);}
else {payload.method='Update your own initial findings using additions. Preserve still-supported findings and revise affected conclusions. Earlier sources remain retrievable by key if the prior findings are insufficient.';payload.prior_findings=await read('runs/'+caseName+'-'+arm+'-initial/final.json');payload.additions=pack(c.additions);payload.earlier_source_catalog=records(c.initial).map(({key,id,actor_identity,context_refs})=>({key,id,actor_identity,context_refs}));}
const base='runs/'+caseName+'-'+arm+'-'+stage;await fs.mkdir(path.join(dir,base),{recursive:false});
let prompt=await fs.readFile(path.join(dir,'common.txt'),'utf8')+'\nClaim-support authority:\n'+await fs.readFile(path.join(dir,'authority-context.txt'),'utf8')+'\nSaved stage input:\n'+JSON.stringify(payload);
await write(base+'/input.json',payload);
const stageStart=new Date().toISOString();
const attemptReceipts=[];
for(let round=0;round<=2;round++){
 const callBase=base+'/call-'+round;await fs.mkdir(path.join(dir,callBase));await write(callBase+'/stdin.txt',prompt);
 const executable='C:/Users/vmon7/AppData/Local/OpenAI/Codex/bin/codex.exe';
 const args=['exec','--json','-C',path.join(dir,callBase),'--disable','shell_tool','--output-schema',path.join(dir,'response.schema.json'),'--output-last-message',path.join(dir,callBase,'response.json'),'-'];
 const started_at=new Date().toISOString();const clock=performance.now();
 await write(callBase+'/invocation.json',{executable,args,cwd:path.join(dir,callBase),started_at,stdin_sha256:sha(prompt),no_resume:true,model_override:null,reasoning_override:null,retrieval_round:round});
 const stdout=await fs.open(path.join(dir,callBase,'events.jsonl'),'wx'),stderr=await fs.open(path.join(dir,callBase,'stderr.log'),'wx');
 console.log(JSON.stringify({started:caseName,arm,stage,round,started_at}));
 const child=spawn(executable,args,{cwd:path.join(dir,callBase),windowsHide:true,stdio:['pipe',stdout.fd,stderr.fd]});child.stdin.on('error',()=>{});child.stdin.end(prompt);
 const exit=await new Promise(resolve=>{child.on('error',e=>resolve({code:null,error:e.code??e.name}));child.on('close',(code,signal)=>resolve({code,signal}));});
 await stdout.close();await stderr.close();
 const lines=(await fs.readFile(path.join(dir,callBase,'events.jsonl'),'utf8')).split(/\r?\n/).filter(Boolean);
 const events=lines.map(l=>{try{return JSON.parse(l);}catch{return {type:'unparsed',text:l};}});
 const turns=events.filter(e=>e.type==='turn.completed');const usage=turns.length?turns.reduce((s,e)=>{for(const[k,v]of Object.entries(e.usage??{}))if(typeof v==='number')s[k]=(s[k]??0)+v;return s;},{}):null;
 const tools=events.filter(e=>e.item&&/command_execution|mcp_tool_call|web_search/.test(e.item.type));
 const receipt={case:caseName,arm,stage,round,started_at,finished_at:new Date().toISOString(),wall_ms:performance.now()-clock,...exit,thread_id:events.find(e=>e.type==='thread.started')?.thread_id??null,usage,turn_count:turns.length,unexpected_tools:tools,errors:events.filter(e=>['error','turn.failed','unparsed'].includes(e.type)),stdin_sha256:sha(prompt)};
 await write(callBase+'/receipt.json',receipt);attemptReceipts.push(receipt);
 console.log(JSON.stringify({finished:caseName,arm,stage,round,code:exit.code,usage,tools:tools.length}));
 if(exit.code!==0||!usage||tools.length||receipt.errors.length)throw Error('Failed/unmeasured/contaminated call '+callBase);
 const response=await read(callBase+'/response.json');
 if(!response.retrieval_requests.length){await write(base+'/final.json',response);await write(base+'/stage-receipt.json',{started_at:stageStart,finished_at:new Date().toISOString(),calls:attemptReceipts.length,retrievals:round,complete:true});break;}
 await write(callBase+'/retrieval.json',{requested:response.retrieval_requests});
 if(round===2)throw Error('Documented two-round retrieval resource boundary reached');
 const allowed=initial?c.initial:all;const requested=response.retrieval_requests;
 const retrieved=requested.map(k=>{if(allowed.includes(k))return {key:k,...pack([k])};const ctx=fixture.contexts.find(x=>x.context_id===k);if(ctx&&records(allowed).some(r=>r.context_refs?.includes(k)))return ctx;throw Error('Unauthorized retrieval '+k);});
 prompt+='\nYour source retrieval request (not an answer):\n'+JSON.stringify(response)+'\nExact requested frozen sources:\n'+JSON.stringify(retrieved)+'\nNow answer the same diagnostic question and count definitions. Request further sources only if necessary.';
}
