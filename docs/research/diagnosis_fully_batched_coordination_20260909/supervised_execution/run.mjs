// One reusable entrypoint: launch exact frozen verifier work, supervise, validate, return a compact receipt.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {supervise} from './supervisor.mjs';
import {sha,assert,executable,native,sessionPath} from '../lib.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),parent=path.dirname(dir);
export async function runVerifier(output,{reviewAfterMs=120000,onReview=()=>{}}={}){
 const source=parent+'/verification_experiment/runs/hydration-control';
 const prompt=await fs.readFile(source+'/verifier/stdin.txt','utf8'),input=JSON.parse(await fs.readFile(source+'/verifier-input.json','utf8'));
 const frozen=JSON.parse(await fs.readFile(dir+'/freeze.json','utf8'));for(const f of frozen.files)assert(sha(await fs.readFile(path.resolve(dir,f.path)))===f.sha256,'Frozen input/construction mismatch '+f.path);
 await fs.mkdir(output,{recursive:true});await fs.writeFile(output+'/stdin.txt',prompt,{flag:'wx'});
 const args=['exec','--json','--model','gpt-6-astra','-c','model_reasoning_effort="high"','-C',output,'--disable','shell_tool','--output-schema',parent+'/verification_experiment/verifier.schema.json','--output-last-message',output+'/response.json','-'];
 await fs.writeFile(output+'/invocation.json',JSON.stringify({executable,args,stdin_sha256:sha(prompt),no_resume:true},null,2),{flag:'wx'});
 const result=await supervise({executable,args,cwd:output,output,stdin:prompt,reviewAfterMs,onReview});assert(result.process_success,'Verifier process failed; inspect preserved receipt');
 const es=(await fs.readFile(output+'/stdout.log','utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse),id=es.find(e=>e.type==='thread.started')?.thread_id;assert(id,'Missing native session');
 assert(!es.some(e=>['error','turn.failed'].includes(e.type)),'Native failure');assert(!es.some(e=>e.item&&/command_execution|mcp_tool_call|web_search/.test(e.item.type)),'Unexpected verifier tools');
 const n=await native(await sessionPath(id)),u=n.last_counter?.usage;assert(u&&n.settings.model==='gpt-6-astra'&&n.settings.effort==='high'&&n.settings.cli_version==='0.153.4','Unmeasured or changed settings');
 const pi=n.es.findIndex(e=>e.type==='response_item'&&e.payload?.role==='user'&&e.payload.content?.some(c=>c.text===prompt));assert(pi>=0&&!n.es.slice(0,pi).some(e=>e.type==='response_item'&&['assistant','tool'].includes(e.payload?.role))&&n.tool_calls===0,'Coldness/input boundary');
 const turnUsage=es.filter(e=>e.type==='turn.completed').reduce((a,e)=>({input_tokens:a.input_tokens+e.usage.input_tokens,output_tokens:a.output_tokens+e.usage.output_tokens}),{input_tokens:0,output_tokens:0});assert(turnUsage.input_tokens===u.input_tokens&&turnUsage.output_tokens===u.output_tokens,'Native counter agreement');
 const answer=JSON.parse(await fs.readFile(output+'/response.json','utf8')),corrected=structuredClone(input.answer);
 for(const c of answer.corrections){const pointer=c.pointer.startsWith('/answer/')?c.pointer.slice('/answer'.length):c.pointer;assert(pointer.startsWith('/'),'Invalid pointer');const ks=pointer.slice(1).split('/').map(s=>s.replaceAll('~1','/').replaceAll('~0','~'));assert(!ks.some(k=>['__proto__','constructor','prototype'].includes(k)),'Unsafe pointer');let at=corrected;for(const k of ks.slice(0,-1)){assert(at&&Object.hasOwn(at,k),'Missing pointer');at=at[k];}const k=ks.at(-1);assert(typeof at[k]==='string'&&c.old_text&&at[k].split(c.old_text).length===2,'Correction must match exactly once');at[k]=at[k].replace(c.old_text,c.new_text);}
 await fs.writeFile(output+'/corrected.json',JSON.stringify(corrected,null,2),{flag:'wx'});
 const receipt={id,native_session:n.file,settings:n.settings,usage:u,total_tokens:u.input_tokens+u.output_tokens,model_calls:n.model_calls,tool_calls:n.tool_calls,corrections:answer.corrections.length,unresolved:answer.unresolved_material_issues,cold_input_verified:true,prompt_sha256:sha(prompt),review_events:result.review_events,wall_ms:result.wall_ms,claim_boundary:'Execution/input/accounting verified. Semantic outcome requires inspecting the saved original response and exact source evidence; process success is not diagnosis-quality approval.'};
 await fs.writeFile(output+'/result.json',JSON.stringify(receipt,null,2),{flag:'wx'});return receipt;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const output=process.argv[2];if(!output||!path.isAbsolute(output))throw Error('Usage: node run.mjs ABSOLUTE_NEW_OUTPUT_DIRECTORY');
 const result=await runVerifier(output,{onReview:e=>console.error(JSON.stringify(e))});console.log(JSON.stringify({status:'completed',...result}));
}
