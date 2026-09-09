import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {dir,read,write} from './experiment.mjs';
import {root,sha,assert,files} from '../lib.mjs';
const scope='docs/research/diagnosis_fully_batched_coordination_20260909/verification_experiment',index='docs/research/README.md',branch='codex/diagnosis-fully-batched-coordination-20260909';
const run=(exe,args)=>execFileSync(exe,args,{cwd:root,windowsHide:true,maxBuffer:32*1024*1024});
const git=(...args)=>run('git',args);
const gh=(...args)=>run('gh',args);
try{
 assert(git('branch','--show-current').toString().trim()===branch,'Wrong branch');
 run(process.execPath,[dir+'/measure.mjs',...(process.argv.includes('--retain-cutoff')?['--check']:[])]);run(process.execPath,[dir+'/report.mjs']);run(process.execPath,[dir+'/measure.mjs','--check']);
 const m=await read('measurement.json'),a=await read('adjudication.json');
 const body=`The fixed-evidence experiment tests batched diagnosis with bounded case judges, then a paired source-backed verification safeguard.\n\nVerification result: ${a.conclusion}\n\nThree fresh generations per case (nine total), plus the original congestion error as a separate positive control. Exact first-pass outputs, verifier corrections and blinded paired assessments are preserved. Verification experiment native tokens at cutoff: generators ${m.totals.generators.total_tokens}; verifiers ${m.totals.verifiers.total_tokens}; judges ${m.totals.judges.total_tokens}; coordinator ${m.totals.coordinator.total_tokens}; combined ${m.totals.combined}. Post-cutoff publication/final response remain explicit for parent finalization.\n\nValidation: frozen sources/prompts; unchanged complete generation inputs; exact corrections only; coldness and actual settings; complete native accounting; source-backed paired quality assessment; exact diff scope.\n\nReports: docs/research/diagnosis_fully_batched_coordination_20260909/report.md and ${scope}/report.md. Research only, no rollout or production changes. Different-vendor operator-courier review and author adjudication remain required before merge. No merge or automatic continuation.\n`;
 await write('pr-body.md',body);
 await write('validation.json',{verified_at:new Date().toISOString(),status:'GATE PASS',native_calls:m.calls.length,paired_answers:m.pairs.length,checks:['frozen identity and unchanged source/prompt input','native coldness, actual settings and complete accounting','all baseline and corrected pairs plus deterministic masking','exact-once correction replay, no unrelated mutation','first-pass source-backed quality with author adjudication'],cutoff:m.coordinator.last_counter.timestamp,publication:'Existing draft PR #1587; final durable and remote readback returned by closeout.'});
 git('add','--',scope,index);
 const staged=git('diff','--cached','--name-only').toString().trim().split(/\r?\n/);for(const f of staged)assert(f===index||f.startsWith(scope+'/'),'Out-of-scope diff '+f);
 git('diff','--cached','--check');git('commit','-m','research: test source-backed diagnosis verification on paired repetitions');
 const head=git('rev-parse','HEAD').toString().trim(),tracked=git('ls-tree','-r','--name-only','HEAD','--',scope).toString().trim().split(/\r?\n/);
 for(const f of await files(dir)){const rel=path.relative(root,f).replaceAll('\\','/');assert(tracked.includes(rel),'Untracked/ignored artifact '+rel);assert(sha(git('show','HEAD:'+rel))===sha(await fs.readFile(f)),'Committed bytes '+rel);}
 const durableIndex=git('show','HEAD:'+index).toString(),localIndex=await fs.readFile(root+'/'+index,'utf8');assert(durableIndex.replaceAll('\r\n','\n')===localIndex.replaceAll('\r\n','\n'),'Index content');
 console.log(JSON.stringify({checkpoint:'committed_readback',head,files:tracked.length}));
 git('push','origin',branch);assert(git('ls-remote','--heads','origin',branch).toString().slice(0,40)===head,'Remote head');
 gh('pr','edit','1587','--title','research: test bounded diagnosis and source-backed verification','--body-file',dir+'/pr-body.md');
 let pr;for(let attempt=0;attempt<5;attempt++){pr=JSON.parse(gh('pr','view','1587','--json','url,isDraft,state,headRefOid').toString());if(pr.headRefOid===head)break;await new Promise(r=>setTimeout(r,2000));}
 assert(pr.isDraft&&pr.state==='OPEN'&&pr.headRefOid===head,'Draft PR readback');assert(git('status','--porcelain').toString().trim()==='','Dirty after publication');
 console.log(JSON.stringify({status:'GATE PASS',head,pr,tracked_files:tracked.length,conclusion:a.conclusion,totals:m.totals,cohort_costs:m.cohort_costs,elapsed:m.elapsed,cutoff:m.coordinator.last_counter.timestamp,session:m.coordinator.session,completed_at:new Date().toISOString(),residual:'Post-cutoff closeout and final response are unallocated; parent can finalize from native counters.'}));
}catch(e){console.error(JSON.stringify({status:'GATE FAIL',message:e.message,stdout:e.stdout?.toString().slice(-900),stderr:e.stderr?.toString().slice(-1200)}));process.exitCode=1;}
