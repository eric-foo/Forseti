// Sample-local process supervision. Timers nominate review; they never kill or restart.
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
export async function supervise({executable,args=[],cwd,output,stdin,reviewAfterMs,onReview=()=>{}}){
 if(!cwd||!output||!Number.isSafeInteger(reviewAfterMs)||reviewAfterMs<1)throw Error('cwd, output and positive reviewAfterMs required');
 await fs.mkdir(output,{recursive:true});
 const stdout=await fs.open(path.join(output,'stdout.log'),'wx'),stderr=await fs.open(path.join(output,'stderr.log'),'wx');
 const started_at=new Date().toISOString(),started=performance.now();let bytesOut=0,bytesErr=0,lastOutput=null,exitSeen=false,code=null,signal=null,error=null,timer;
 const events=[],p=spawn(executable,args,{cwd,windowsHide:true,stdio:[stdin===undefined?'ignore':'pipe','pipe','pipe']});
 const writes={stdout:Promise.resolve(),stderr:Promise.resolve()};let review=Promise.resolve();
 const observation=()=>({pid:p.pid??null,state:exitSeen?'exited_waiting_for_streams':'running',elapsed_ms:Math.round(performance.now()-started),stdout_bytes:bytesOut,stderr_bytes:bytesErr,last_output_elapsed_ms:lastOutput,exit:code,signal,error});
 const append=(handle,chunk,stream)=>{if(stream==='stdout')bytesOut+=chunk.length;else bytesErr+=chunk.length;lastOutput=Math.round(performance.now()-started);writes[stream]=writes[stream].then(()=>handle.write(chunk)).catch(e=>{error??=e.message;});};
 p.stdout.on('data',b=>append(stdout,b,'stdout'));p.stderr.on('data',b=>append(stderr,b,'stderr'));
 if(stdin!==undefined){p.stdin.on('error',()=>{});p.stdin.end(stdin);}
 const finished=new Promise(resolve=>{p.on('error',e=>{error=e.code??e.message;});p.on('exit',(c,s)=>{exitSeen=true;code=c;signal=s;});p.on('close',(c,s)=>{code=c;signal=s;resolve();});});
 timer=setTimeout(()=>{const e={type:'review_required',...observation(),meaning:'Expected-duration review interval elapsed. This is not proof of a stall. No restart, cancellation or success is inferred.'};events.push(e);review=Promise.resolve().then(()=>onReview(e)).catch(e=>{error??=e.message;});},reviewAfterMs);
 await finished;clearTimeout(timer);await Promise.all([...Object.values(writes),review]);await stdout.close();await stderr.close();
 const result={started_at,finished_at:new Date().toISOString(),executable,args,cwd,pid:p.pid??null,exit:code,signal,error,wall_ms:Math.round(performance.now()-started),stdout_bytes:bytesOut,stderr_bytes:bytesErr,last_output_elapsed_ms:lastOutput,review_events:events,launches:1,restarts:0,termination_requested:false,process_success:code===0&&signal===null&&error===null};
 await fs.writeFile(path.join(output,'receipt.json'),JSON.stringify(result,null,2));return result;
}
