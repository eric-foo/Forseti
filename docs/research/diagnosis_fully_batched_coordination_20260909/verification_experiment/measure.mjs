import fs from 'node:fs/promises';
import path from 'node:path';
import {dir,parent,read,write,freezeCheck} from './experiment.mjs';
import {sha,assert,files,native,sessionPath} from '../lib.mjs';
const checking=process.argv.includes('--check'),saved=checking?await read('measurement.json'):null;
await freezeCheck();
const disk=await files(dir),calls=[];
for(const f of disk.filter(f=>f.endsWith('/invocation.json')||f.endsWith('\\invocation.json'))){
 const base=path.dirname(f),rel=path.relative(dir,base).replaceAll('\\','/'),inv=JSON.parse(await fs.readFile(f,'utf8')),r=JSON.parse(await fs.readFile(base+'/receipt.json','utf8')),stdin=await fs.readFile(base+'/stdin.txt','utf8');
 const events=(await fs.readFile(base+'/events.jsonl','utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);
 const n=await native(await sessionPath(r.id)),u=n.last_counter?.usage;assert(u&&r.code===0,'Unmetered/failed call '+rel);
 assert(u.input_tokens===r.usage.input_tokens&&u.output_tokens===r.usage.output_tokens,'Native totals '+rel);
 assert(sha(stdin)===inv.stdin_sha256,'stdin hash '+rel);
 const pi=n.es.findIndex(e=>e.type==='response_item'&&e.payload?.role==='user'&&e.payload.content?.some(c=>c.text===stdin));assert(pi>=0,'Exact actual input '+rel);
 assert(!n.es.slice(0,pi).some(e=>e.type==='response_item'&&['assistant','tool'].includes(e.payload?.role)),'Warm history '+rel);
 assert(n.tool_calls===0&&!events.some(e=>e.item&&/command_execution|mcp_tool_call|web_search/.test(e.item.type)),'Unexpected tool '+rel);
 assert(!inv.args.includes('resume')&&!inv.args.includes('fork'),'Resumed call '+rel);
 assert(n.settings.model==='gpt-6-astra'&&n.settings.effort===(r.role==='generator'?'medium':'high')&&n.settings.cli_version==='0.153.4','Actual settings '+rel);
 const extras=n.es.filter(e=>e.type==='response_item'&&e.payload?.role==='user').flatMap(e=>e.payload.content??[]).filter(c=>c.text&&c.text!==stdin).map(c=>c.text);
 assert(!extras.some(t=>/author-adjudication\.json|judge-results\.json|blind-mapping\.json|verification_experiment\/report\.md/.test(t)),'Automatic context contamination '+rel);
 calls.push({...r,path:rel,native_session:n.file,actual_settings:n.settings,usage:u,counter_at:n.last_counter.timestamp,model_calls:n.model_calls,tool_calls:n.tool_calls,tool_outputs:n.tool_outputs,cold:{exact_stdin:true,no_prior_history:true,extra_user_context_hashes:extras.map(sha),native_session_sha256:sha(await fs.readFile(n.file))},bytes:{stdin:Buffer.byteLength(stdin),events:(await fs.stat(base+'/events.jsonl')).size,stderr:(await fs.stat(base+'/stderr.log')).size},wall_ms:Date.parse(r.finished_at)-Date.parse(r.started_at)});
}
assert(new Set(calls.map(c=>c.id)).size===calls.length,'Session reuse');
for(const f of(await read('recovery-freeze.json')).files)assert(sha(await fs.readFile(dir+'/'+f.path))===f.sha256,'Recovery freeze mismatch');
const batch=await read('completed-batch.json');assert(!batch.failures.length,'Job failures');
assert(batch.result.length===10&&calls.filter(c=>c.role==='verifier').length===10&&calls.filter(c=>c.role==='judge').length===3,'Job/call cardinality');
const promptHashes={};
for(const j of batch.result){
 const base='runs/'+j.id,input=await read(base+'/reader-input.json'),ref=JSON.parse(await fs.readFile(parent+'/runs/'+j.case+'-full-update/input.json','utf8'));
 assert(JSON.stringify(input)===JSON.stringify(ref),'Complete unchanged reader input '+j.id);
 const before=await read(base+'/baseline.json'),after=await read(base+'/corrected.json'),v=await read(base+'/verifier/response.json'),vi=await read(base+'/verifier-input.json');
 assert(JSON.stringify(vi.reader_input)===JSON.stringify(input)&&JSON.stringify(vi.answer)===JSON.stringify(before),'Verifier exact input '+j.id);
 assert(before.source_index.length===input.focal_keys.length&&JSON.stringify(before.source_index.map(x=>x.key).sort())===JSON.stringify([...input.focal_keys].sort()),'Source index completeness '+j.id);
 const rebuilt=structuredClone(before);for(const c of v.corrections){let p=rebuilt;const pointer=c.pointer.startsWith('/answer/')?c.pointer.slice('/answer'.length):c.pointer;const keys=pointer.slice(1).split('/').map(x=>x.replaceAll('~1','/').replaceAll('~0','~'));for(const k of keys.slice(0,-1))p=p[k];const k=keys.at(-1);assert(typeof p[k]==='string'&&c.old_text&&p[k].split(c.old_text).length===2,'Patch match '+j.id);p[k]=p[k].replace(c.old_text,c.new_text);}
 assert(JSON.stringify(rebuilt)===JSON.stringify(after),'Only exact specified corrections '+j.id);
 if(j.positive_control)assert(JSON.stringify(before)===JSON.stringify(JSON.parse(await fs.readFile(parent+'/runs/hydration-full-update/final.json','utf8'))),'Positive control unchanged');
 else {const stdin=await fs.readFile(dir+'/'+base+'/generation-0/stdin.txt');const original=await fs.readFile(parent+'/runs/'+j.case+'-full-update/call-0/stdin.txt');assert(stdin.equals(original),'Unchanged baseline construction '+j.id);(promptHashes[j.case]??=[]).push(sha(stdin));}
}
for(const hashes of Object.values(promptHashes))assert(hashes.length===3&&new Set(hashes).size===1,'Three identical input repetitions');
const map=await read('blind-mapping.json'),judges=await read('judge-results.json'),pairs=[];
for(const j of judges){const ji=await read('judges/'+j.case+'/input.json');assert(j.pairs.length===ji.pairs.length,'Judge omitted pair');for(const p of j.pairs){
 const mapping=map[p.pair_id];assert(mapping&&mapping.case===j.case,'Blind pair identity');const inputPair=ji.pairs.find(x=>x.pair_id===p.pair_id);assert(inputPair,'Judge pair missing input');
 assert(p.answers.length===2&&new Set(p.answers.map(a=>a.label)).size===2&&p.answers.every(a=>['A','B'].includes(a.label)),'Judge labels');
 for(const label of ['A','B']){const expected=await read('runs/'+mapping.run_id+'/'+(label===mapping.baseline_label?'baseline':'corrected')+'.json');assert(JSON.stringify(inputPair.answers.find(a=>a.label===label).answer)===JSON.stringify(expected),'Blind exact answer');}
 const b=p.answers.find(a=>a.label===mapping.baseline_label),a=p.answers.find(a=>a.label===mapping.corrected_label);
 pairs.push({...mapping,pair_id:p.pair_id,before_material_errors:b.material_errors,after_material_errors:a.material_errors,before_notes:b.nonmaterial_notes,after_notes:a.nonmaterial_notes});
}}
assert(pairs.length===10&&new Set(pairs.map(p=>p.run_id)).size===10,'All paired outcomes');
const summary=ps=>({pairs:ps.length,before_material_errors:ps.reduce((s,p)=>s+p.before_material_errors.length,0),after_material_errors:ps.reduce((s,p)=>s+p.after_material_errors.length,0),answers_with_errors_before:ps.filter(p=>p.before_material_errors.length).length,answers_with_errors_after:ps.filter(p=>p.after_material_errors.length).length});
const sum=cs=>({launches:cs.length,model_calls:cs.reduce((s,c)=>s+c.model_calls,0),input_tokens:cs.reduce((s,c)=>s+c.usage.input_tokens,0),cached_input_tokens:cs.reduce((s,c)=>s+(c.usage.cached_input_tokens??0),0),output_tokens:cs.reduce((s,c)=>s+c.usage.output_tokens,0),reasoning_output_tokens:cs.reduce((s,c)=>s+(c.usage.reasoning_output_tokens??0),0),total_tokens:cs.reduce((s,c)=>s+c.usage.input_tokens+c.usage.output_tokens,0),serial_wall_ms:cs.reduce((s,c)=>s+c.wall_ms,0)});
const start=await read('coordinator-start.json'),coord=await native(start.session,saved?.coordinator.last_counter.timestamp);delete coord.es;
const usage={};for(const k of ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens'])usage[k]=(coord.last_counter.usage[k]??0)-(start.base_counter.usage[k]??0);usage.total_tokens=usage.input_tokens+usage.output_tokens;
const totals={generators:sum(calls.filter(c=>c.role==='generator')),verifiers:sum(calls.filter(c=>c.role==='verifier')),judges:sum(calls.filter(c=>c.role==='judge')),coordinator:usage};totals.combined=totals.generators.total_tokens+totals.verifiers.total_tokens+totals.judges.total_tokens+usage.total_tokens;
const byCohort=positive=>({generators:sum(calls.filter(c=>c.role==='generator'&&c.path.includes('control')===positive)),verifiers:sum(calls.filter(c=>c.role==='verifier'&&c.path.includes('control')===positive))});
const sup=await read('supervision.json');
const measurement={measured_at:new Date().toISOString(),frozen:true,calls,pairs,raw_outcomes:{fresh:summary(pairs.filter(p=>!p.positive_control)),positive_control:summary(pairs.filter(p=>p.positive_control))},totals,cohort_costs:{fresh:byCohort(false),positive_control:byCohort(true)},coordinator:{session:coord.file,turn_started_at:start.turn_started_at,base_counter:start.base_counter,last_counter:coord.last_counter,turn_counters:coord.counters.filter(c=>c.timestamp>=start.turn_started_at),session_settings:coord.settings},elapsed:{supervised_ms:Date.parse(sup.finished_at)-Date.parse(sup.started_at),turn_to_cutoff_ms:Date.parse(coord.last_counter.timestamp)-Date.parse(start.turn_started_at)},coldness:'Actual native prompt equals saved stdin; no prior assistant/tool messages or tool use; fresh unique native sessions. Nine normal generator prompts are byte-identical to earlier full-update construction. Judges receive neither method labels nor verifier rationales.',accounting:'Current turn baseline native counter subtracted; context reprocessing remains charged. Input+output; cached and reasoning are subsets. Includes all fresh generation, verifier and judge calls. Positive-control generation is historical and excluded; its verifier cost is included separately. Costs after one pinned final available counter remain for parent finalization, with no recursive report rewrite. No token savings inferred from bytes.'};
if(checking){assert(JSON.stringify(saved.totals)===JSON.stringify(totals),'Durable token totals');assert(JSON.stringify(saved.raw_outcomes)===JSON.stringify(measurement.raw_outcomes),'Durable outcomes');console.log(JSON.stringify({status:'GATE PASS',calls:calls.length,pairs:pairs.length}));}
else {await write('measurement.json',measurement);await write('compact-results.json',{raw_outcomes:measurement.raw_outcomes,totals,elapsed:measurement.elapsed,pairs:pairs.filter(p=>p.before_material_errors.length||p.after_material_errors.length),verifier_flags:await Promise.all(batch.result.filter(j=>j.corrections||j.unresolved).map(async j=>({run_id:j.id,...await read('runs/'+j.id+'/verifier/response.json')})))});console.log(JSON.stringify({status:'GATE PASS',raw_outcomes:measurement.raw_outcomes,totals,elapsed:measurement.elapsed}));}
