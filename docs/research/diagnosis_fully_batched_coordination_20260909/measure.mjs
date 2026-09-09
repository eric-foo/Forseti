// Code-only audit. It never emits source bodies, answer packs or session messages.
import fs from 'node:fs/promises';
import path from 'node:path';
import {dir,root,sha,read,write,assert,files,native,sessionPath} from './lib.mjs';
const checking=process.argv.includes('--check');
const prior=checking?await read('measurement.json'):null;
for(const f of(await read('freeze.json')).files)assert(sha(await fs.readFile(dir+'/'+f.name))===f.sha256,'Frozen mismatch '+f.name);
const freeze=await read('freeze.json');for(const p of freeze.raw_reverified)assert(sha(await fs.readFile(p.path))===p.sha256,'Raw identity '+p.path);
const plan=await read('experiment.json'),fixture=await read('sources.json'),calls=[],cold=[];
const allFiles=await files();
const invocations=allFiles.filter(p=>p.endsWith('invocation.json'));
for(const file of invocations){
 const base=path.dirname(file),rel=path.relative(dir,base).replaceAll('\\','/'),judge=rel.startsWith('judges/');
 const inv=JSON.parse(await fs.readFile(file,'utf8')),stdin=await fs.readFile(base+'/stdin.txt','utf8');
 assert(sha(stdin)===inv.stdin_sha256,'Saved input '+rel);
 const eventPath=base+(judge?'/call.stdout.log':'/events.jsonl');
 const events=(await fs.readFile(eventPath,'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);
 const id=events.find(e=>e.type==='thread.started')?.thread_id;assert(id,'Session ID '+rel);
 const n=await native(await sessionPath(id));
 const turns=events.filter(e=>e.type==='turn.completed'),usage=turns.reduce((s,e)=>{for(const[k,v]of Object.entries(e.usage??{}))if(typeof v==='number')s[k]=(s[k]??0)+v;return s;},{});
 const receipt=JSON.parse(await fs.readFile(base+(judge?'/call.exit.json':'/receipt.json'),'utf8'));
 assert(receipt.code===0&&turns.length>0,'Exit/turn '+rel);
 assert(!events.some(e=>['error','turn.failed','unparsed'].includes(e.type)),'First-pass failure '+rel);
 assert(n.last_counter.usage.input_tokens===usage.input_tokens&&n.last_counter.usage.output_tokens===usage.output_tokens,'Native accounting '+rel);
 assert(n.settings.model==='gpt-6-astra'&&n.settings.effort===(judge?'high':'medium')&&n.settings.cli_version==='0.153.4','Observed settings '+rel);
 const promptIndex=n.es.findIndex(e=>e.type==='response_item'&&e.payload?.role==='user'&&e.payload.content?.some(c=>c.text===stdin));
 assert(promptIndex>=0,'Exact actual input '+rel);
 assert(!n.es.slice(0,promptIndex).some(e=>e.type==='response_item'&&(['assistant','tool'].includes(e.payload?.role)||/function_call/.test(e.payload?.type??''))),'Warm history '+rel);
 assert(n.tool_calls===0&&!events.some(e=>e.item&&/command_execution|mcp_tool_call|web_search/.test(e.item.type)),'Unexpected tools '+rel);
 assert(!inv.args.some(a=>a==='resume'||a==='fork'),'Resume/fork '+rel);
 const extras=n.es.filter(e=>e.type==='response_item'&&e.payload?.role==='user').flatMap(e=>e.payload.content??[]).filter(c=>c.text&&c.text!==stdin).map(c=>c.text);
 assert(!extras.some(t=>/expected_judgments|prior-sample\/|diagnosis_cold_comparison_20260909\/report\.md|judge-results\.json/.test(t)),'Automatic context contamination '+rel);
 const item={role:judge?'judge':'reader',path:rel,id,native_session_path:n.file,settings:n.settings,started_at:receipt.started_at,finished_at:receipt.finished_at,wall_ms:Date.parse(receipt.finished_at)-Date.parse(receipt.started_at),exit:receipt.code,retrieval_round:judge?0:receipt.round,semantic_retry:false,usage:n.last_counter.usage,native_counter_at:n.last_counter.timestamp,model_calls:n.model_calls,tool_calls:n.tool_calls,tool_outputs:n.tool_outputs,stdin_bytes:Buffer.byteLength(stdin),stdout_bytes:(await fs.stat(eventPath)).size,stderr_bytes:(await fs.stat(base+(judge?'/call.stderr.log':'/stderr.log'))).size};calls.push(item);
 cold.push({path:rel,id,exact_input:true,no_prior_assistant_or_tool:true,no_resume_or_fork:true,automatic_user_context_hashes:extras.map(sha),native_session_sha256:sha(await fs.readFile(n.file))});
}
assert(new Set(calls.map(c=>c.id)).size===calls.length,'Session reuse');
const sourceChecks=[];
for(const [c,p]of Object.entries(plan.cases)){
 const a=await fs.readFile(dir+'/runs/'+c+'-incremental-initial/call-0/stdin.txt'),b=await fs.readFile(dir+'/runs/'+c+'-full-initial/call-0/stdin.txt');assert(a.equals(b),'Initial unequal '+c);
 for(const arm of ['incremental','full'])for(const stage of ['initial','update']){
  const base='runs/'+c+'-'+arm+'-'+stage,inp=await read(base+'/input.json'),ans=await read(base+'/final.json'),keys=stage==='initial'?p.initial:[...p.initial,...p.additions];
  assert(JSON.stringify(ans.source_index.map(r=>r.key).sort())===JSON.stringify([...keys].sort()),'Complete source index '+base);
  const pack=stage==='update'&&arm==='incremental'?inp.additions:inp.sources;
  const expectedKeys=stage==='update'&&arm==='incremental'?p.additions:keys;
  assert(JSON.stringify(pack.records.map(r=>r.key))===JSON.stringify(expectedKeys),'Input split '+base);
  for(const r of pack.records)assert(JSON.stringify(r)===JSON.stringify(fixture.records.find(s=>s.key===r.key)),'Exact record '+base+' '+r.key);
  const contextIds=new Set(pack.records.flatMap(r=>r.context_refs??[]));
  assert(JSON.stringify(pack.contexts)===JSON.stringify(fixture.contexts.filter(r=>contextIds.has(r.context_id))),'Complete contexts '+base);
  if(stage==='update'&&arm==='incremental'){assert(!inp.sources,'Full corpus leak');assert(JSON.stringify(inp.prior_findings)===JSON.stringify(await read('runs/'+c+'-'+arm+'-initial/final.json')),'Own findings only');}
  else assert(!inp.prior_findings,'Prior leak '+base);
  sourceChecks.push({path:base,source_keys:keys,complete_source_index:true,exact_pack:true});
 }
 const ji=await read('judges/'+c+'/input.json');assert(ji.records.length===p.initial.length+p.additions.length,'Judge complete '+c);
 for(const [key,value] of Object.entries(ji.answers))assert(JSON.stringify(value)===JSON.stringify(await read('runs/'+c+'-'+key+'/final.json')),'Judge exact answer '+key);
}
assert(calls.filter(c=>c.role==='judge').length===3,'Three judges');
const sum=cs=>({input_tokens:cs.reduce((s,c)=>s+c.usage.input_tokens,0),cached_input_tokens:cs.reduce((s,c)=>s+(c.usage.cached_input_tokens??0),0),output_tokens:cs.reduce((s,c)=>s+c.usage.output_tokens,0),reasoning_output_tokens:cs.reduce((s,c)=>s+(c.usage.reasoning_output_tokens??0),0),total_tokens:cs.reduce((s,c)=>s+c.usage.input_tokens+c.usage.output_tokens,0),launches:cs.length,model_calls:cs.reduce((s,c)=>s+c.model_calls,0),serial_wall_ms:cs.reduce((s,c)=>s+c.wall_ms,0)});
const baselines=await read('baselines.json');
for(const b of baselines){
 const n=await native(b.file,b.cutoff);assert(n.last_counter.usage.input_tokens+n.last_counter.usage.output_tokens===b.coordinator,'Baseline coordinator recheck');
 const ref=b.name==='original'?'C:/Users/vmon7/.codex/worktrees/8efc/orca/docs/research/diagnosis_cold_comparison_20260909':'C:/Users/vmon7/.codex/worktrees/72b7/orca/docs/research/diagnosis_batched_coordination_20260909';
 let total=0,measured=0,unmetered=0;
 for(const f of(await files(ref+'/runs')).filter(f=>f.endsWith('receipt.json')&&!f.endsWith('stage-receipt.json'))){const r=JSON.parse(await fs.readFile(f,'utf8'));if(!r.usage){unmetered++;continue;}const ns=await native(await sessionPath(r.thread_id));assert(ns.last_counter.usage.input_tokens===r.usage.input_tokens&&ns.last_counter.usage.output_tokens===r.usage.output_tokens,'Baseline reader receipt');total+=r.usage.input_tokens+r.usage.output_tokens;measured++;}
 assert(total===b.readers,'Baseline readers mismatch '+b.name+' '+total);b.reader_verification={measured,unmetered_launches:unmetered,native_total:total};
 b.elapsed_ms=Date.parse(b.cutoff??b.complete??b.last)-Date.parse(b.first);
}
const coordinator=await native(await sessionPath('01a0867d-6954-7e30-bac7-2c28f7cc3400'),prior?.coordinator.last_counter.timestamp);delete coordinator.es;
const checkpoints=[];for(const label of ['preparation','readers','judges']){const n=await read(label+'-checkpoint.json');checkpoints.push({label,timestamp:n.last_counter.timestamp,total:n.last_counter.usage.input_tokens+n.last_counter.usage.output_tokens});}
let previous=0;for(const p of checkpoints){p.delta_tokens=p.total-previous;previous=p.total;}
const ct=coordinator.last_counter.usage.input_tokens+coordinator.last_counter.usage.output_tokens;checkpoints.push({label:'final_available_cutoff',timestamp:coordinator.last_counter.timestamp,total:ct,delta_tokens:ct-previous});
const totals={readers:sum(calls.filter(c=>c.role==='reader')),judges:sum(calls.filter(c=>c.role==='judge')),coordinator:{...coordinator.last_counter.usage,total_tokens:ct}};totals.combined=totals.readers.total_tokens+totals.judges.total_tokens+ct;
const bytes={frozen_sources:(await fs.stat(dir+'/sources.json')).size,model_stdin:calls.reduce((s,c)=>s+c.stdin_bytes,0),model_stdout:calls.reduce((s,c)=>s+c.stdout_bytes,0),model_stderr:calls.reduce((s,c)=>s+c.stderr_bytes,0),final_answers:0};for(const f of allFiles.filter(f=>f.endsWith('final.json')||f.endsWith('response.json')))bytes.final_answers+=(await fs.stat(f)).size;
const supervision=await read('supervision.json');
const measurement={measured_at:new Date().toISOString(),freeze_verified:true,raw_hashes_verified:freeze.raw_reverified.length,coldness:cold,source_checks:sourceChecks,calls,totals,arm_totals:Object.fromEntries(['incremental','full'].map(a=>[a,sum(calls.filter(c=>c.path.includes('-'+a+'-')))])),baselines,coordinator,checkpoints,bytes,elapsed:{coordinator_to_counter_ms:Date.parse(coordinator.last_counter.timestamp)-Date.parse(coordinator.first),batch_and_judges_ms:Date.parse(supervision.finish)-Date.parse(supervision.start)},comparisons:baselines.map(b=>({name:b.name,combined_tokens:b.combined,saved_tokens:b.combined-totals.combined,reduction_percent:100*(1-totals.combined/b.combined),elapsed_ms:b.elapsed_ms})),accounting_boundary:'Native input + output; cached input included once within input; reasoning included once within output. All reader and judge calls included. Coordinator measured from session start to one last available native counter. Phase checkpoint deltas are mixed cumulative input costs, not causal attribution. Post-cutoff publication/code-only validation and final response remain explicitly unallocated until parent finalization. model_calls counts distinct native cumulative-usage updates, not network attempts or output messages. No dollar comparison; bytes are not tokens.'};
if(checking){assert(JSON.stringify(prior.totals)===JSON.stringify(totals),'Durable totals differ');assert(JSON.stringify(prior.coldness)===JSON.stringify(cold),'Durable coldness differs');console.log(JSON.stringify({status:'GATE PASS',native_calls:calls.length,scope:'freeze, source identity, cold inputs, native accounting; semantic quality in judges'}));}
else{await write('measurement.json',measurement);console.log(JSON.stringify({status:'GATE PASS',totals,comparisons:measurement.comparisons,elapsed:measurement.elapsed}));}
