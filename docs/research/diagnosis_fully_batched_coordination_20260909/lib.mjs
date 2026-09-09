import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
export const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(dir,'../../..');
export const sha=b=>createHash('sha256').update(b).digest('hex');
export const read=async n=>JSON.parse(await fs.readFile(path.join(dir,n),'utf8'));
export const write=async(n,v)=>fs.writeFile(path.join(dir,n),typeof v==='string'?v:JSON.stringify(v,null,2));
export const assert=(v,m)=>{if(!v)throw Error(m);};
export const executable='C:/Users/vmon7/AppData/Local/OpenAI/Codex/bin/fd4c151a749f3ab4/codex.exe';
export async function command(label,exe,args,{cwd=dir,input}={}){
 const out=await fs.open(path.join(dir,label+'.stdout.log'),'wx'),err=await fs.open(path.join(dir,label+'.stderr.log'),'wx');
 const started_at=new Date().toISOString();
 const p=spawn(exe,args,{cwd,windowsHide:true,stdio:[input===undefined?'ignore':'pipe',out.fd,err.fd]});
 if(input!==undefined){p.stdin.on('error',()=>{});p.stdin.end(input);}
 const exit=await new Promise(resolve=>{p.on('error',e=>resolve({code:null,error:e.message}));p.on('close',(code,signal)=>resolve({code,signal}));});
 await out.close();await err.close();
 const receipt={label,exe,args,started_at,finished_at:new Date().toISOString(),...exit};await write(label+'.exit.json',receipt);return receipt;
}
export async function files(at=dir){const result=[];for(const e of await fs.readdir(at,{withFileTypes:true})){const p=path.join(at,e.name);if(e.isDirectory())result.push(...await files(p));else result.push(p);}return result;}
export async function native(file,cutoff){
 const es=(await fs.readFile(file,'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse).filter(e=>!cutoff||e.timestamp<=cutoff);
 const counters=es.filter(e=>e.type==='event_msg'&&e.payload?.type==='token_count'&&e.payload.info?.total_token_usage).map(e=>({timestamp:e.timestamp,usage:e.payload.info.total_token_usage}));
 const meta=es.find(e=>e.type==='session_meta')?.payload,tc=es.find(e=>e.type==='turn_context')?.payload;
 const complete=es.findLast(e=>e.type==='event_msg'&&e.payload?.type==='task_complete');
 return {es,file,first:es[0]?.timestamp,last:es.at(-1)?.timestamp,complete:complete?.timestamp,counters,last_counter:counters.at(-1),settings:{model:tc?.model,effort:tc?.effort,cli_version:meta?.cli_version,originator:meta?.originator,service_tier:tc?.service_tier??'unavailable'},id:meta?.id,tool_calls:es.filter(e=>e.type==='response_item'&&/^(function_call|custom_tool_call)$/.test(e.payload?.type)).length,tool_outputs:es.filter(e=>e.type==='response_item'&&/^(function_call_output|custom_tool_call_output)$/.test(e.payload?.type)).length,model_calls:counters.filter((c,i)=>i===0||JSON.stringify(c.usage)!==JSON.stringify(counters[i-1].usage)).length};
}
export async function sessionPath(id){for(const date of ['2026/09/09','2026/09/10']){const d='C:/Users/vmon7/.codex/sessions/'+date;for(const n of await fs.readdir(d).catch(()=>[]))if(n.includes(id))return d+'/'+n;}throw Error('Session missing '+id);}
