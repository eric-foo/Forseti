import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {supervise} from './supervisor.mjs';
import {runVerifier} from './run.mjs';
import {assert} from '../lib.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),start=new Date().toISOString();
// Fast deterministic failure/progress checks; all children are created and owned by this test.
const events=[];
const quiet=await supervise({executable:process.execPath,args:['-e','setTimeout(()=>process.exit(0),250)'],cwd:dir,output:dir+'/tests/overdue',reviewAfterMs:60,onReview:e=>events.push(e)});
assert(quiet.process_success&&events.length===1&&quiet.launches===1&&quiet.restarts===0&&!quiet.termination_requested&&quiet.wall_ms>=200,'Review interval must not kill/restart or claim stall');
const failure=await supervise({executable:process.execPath,args:['-e','process.stderr.write("intentional failure");process.exit(7)'],cwd:dir,output:dir+'/tests/nonzero',reviewAfterMs:10000});assert(!failure.process_success&&failure.exit===7&&failure.stderr_bytes>0,'Real nonzero exit must survive');
const missing=await supervise({executable:path.join(dir,'intentionally-nonexistent.exe'),cwd:dir,output:dir+'/tests/spawn-error',reviewAfterMs:10000});assert(!missing.process_success&&missing.error==='ENOENT','Spawn failure must survive');
console.log(JSON.stringify({checkpoint:'deterministic_checks_passed',overdue_review:events.length,nonzero_exit:failure.exit,spawn_error:missing.error}));
// Real frozen evidence verifier, plus a controlled 70-second quiet process to exercise host waiting.
const reviews=[];
const [verifier,waitPath]=await Promise.allSettled([
 runVerifier(dir+'/real-verifier',{reviewAfterMs:120000,onReview:e=>{reviews.push({job:'verifier',...e});console.error(JSON.stringify({job:'verifier',...e}));}}),
 supervise({executable:process.execPath,args:['-e','setTimeout(()=>process.exit(0),70000)'],cwd:dir,output:dir+'/tests/quiet-70s',reviewAfterMs:120000,onReview:e=>reviews.push({job:'quiet-70s',...e})})
]);
const result={started_at:start,finished_at:new Date().toISOString(),deterministic:{overdue_review_without_kill_or_restart:true,nonzero_exit:failure.exit,spawn_error:missing.error},verifier:verifier.status==='fulfilled'?verifier.value:{error:verifier.reason.message},quiet:waitPath.status==='fulfilled'?waitPath.value:{error:waitPath.reason.message},reviews,semantic_retries:0,supervision_model_calls:0,native_measurement_boundary:'Verifier tokens charged separately. Main implementation conversation and mandatory status updates are not hidden; measured separately at closeout.'};
await fs.writeFile(dir+'/dogfood.json',JSON.stringify(result,null,2),{flag:'wx'});assert(verifier.status==='fulfilled'&&waitPath.status==='fulfilled'&&waitPath.value.process_success,'Dogfood failed; first-pass outputs preserved');
console.log(JSON.stringify({checkpoint:'dogfood_complete',verifier_tokens:verifier.value.total_tokens,supervision_model_calls:0,quiet_ms:waitPath.value.wall_ms,reviews:reviews.length}));
