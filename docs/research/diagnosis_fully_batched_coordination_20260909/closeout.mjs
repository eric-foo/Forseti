// Fail-visible, sequential publication. No file writers overlap Git staging.
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {dir,root,read,write,sha,assert,files} from './lib.mjs';
const scope='docs/research/diagnosis_fully_batched_coordination_20260909',index='docs/research/README.md',branch='codex/diagnosis-fully-batched-coordination-20260909';
const run=(exe,args)=>execFileSync(exe,args,{cwd:root,windowsHide:true,maxBuffer:32*1024*1024});
const git=(...args)=>run('git',args);
function scoped(names){for(const name of names)assert(name===index||name.startsWith(scope+'/'),'Out-of-scope diff '+name);}
async function verifyCommit(){
 const names=git('ls-tree','-r','--name-only','HEAD','--',scope,index).toString().trim().split(/\r?\n/);
 const disk=(await files()).map(p=>path.relative(root,p).replaceAll('\\','/'));
 for(const name of [...disk,index]){assert(names.includes(name),'Untracked/ignored experiment artifact '+name);assert(sha(git('show','HEAD:'+name))===sha(await fs.readFile(root+'/'+name)),'Committed byte mismatch '+name);}
 return {tracked_files:names.length,report_sha256:sha(git('show','HEAD:'+scope+'/report.md'))};
}
try{
 assert(git('branch','--show-current').toString().trim()===branch,'Wrong branch');
 // Freeze one final available counter at entry, then reproduce it without advancing it.
 run(process.execPath,[dir+'/measure.mjs']);run(process.execPath,[dir+'/report.mjs']);
 run(process.execPath,[dir+'/measure.mjs','--check']);
 const judges=await read('judge-results.json');
 const adjudication=await read('author-adjudication.json');
 const m=await read('measurement.json');
 const firstBody=`Execute the commissioned three-case experiment with batched readers and isolated bounded case adjudication. Native input/output accounting includes readers, judges and the coordinator through an explicit cutoff.\n\nQuality findings after author adjudication: ${adjudication.accepted_material_errors} material error in full hydration update (non-congestion becomes congestion improvement); zero material errors found in incremental answers. Three raw judge candidates preserved, two rejected with decisive input/support evidence. Combined native tokens: ${m.totals.combined}. Strict error-free success condition not met. Frozen source identity, cold input isolation, actual settings, complete native accounting and exact scope validated. First-pass outputs and empty logs preserved.\n\nResearch only. Different-vendor operator-courier review and author adjudication remain required before merge. No merge or automatic continuation. Report: ${scope}/report.md.\n`;
 await write('pr-body.md',firstBody);
 await write('validation.json',{verified_at:new Date().toISOString(),checks:['frozen script/input/quality hashes','six raw source hashes','exact account/context splits','unique cold sessions and actual input identity','observed reader medium and judge high settings on CLI 0.153.4','native reader/judge/coordinator totals and both earlier baselines','saved first-pass judgments with materiality standard','complete logs including empty files'],semantic_quality:'judge-results.json',cutoff:m.coordinator.last_counter.timestamp});
 git('add','--',scope,index);
 scoped(git('diff','--cached','--name-only').toString().trim().split(/\r?\n/));
 git('diff','--cached','--check');
 git('commit','-m','research: execute fully batched diagnosis with bounded case judges');
 const initial_head=git('rev-parse','HEAD').toString().trim();await verifyCommit();
 git('push','-u','origin',branch);
 assert(git('ls-remote','--heads','origin',branch).toString().slice(0,40)===initial_head,'Initial remote hash mismatch');
 const url=run('gh',['pr','create','--draft','--base','main','--head',branch,'--title','research: fully batched diagnostic coordination with bounded judges','--body-file',dir+'/pr-body.md']).toString().trim();
 const pr=JSON.parse(run('gh',['pr','view',url,'--json','url,isDraft,state,headRefOid,headRefName']).toString());
 assert(pr.isDraft&&pr.state==='OPEN'&&pr.headRefOid===initial_head&&pr.headRefName===branch,'Draft PR readback mismatch');
 await write('publication.json',{url:pr.url,initial_head,branch,initial_remote_verified:true,draft_observed:true,observed_at:new Date().toISOString(),final_head:'Read final remote hash from closeout receipt; this file precedes the final commit.'});
 run(process.execPath,[dir+'/report.mjs']);
 // All writes are complete before staging. No log/receipt writer mutates the tree below.
 git('add','--',scope,index);git('diff','--cached','--check');
 git('commit','-m','research: record draft publication and final measured experiment report');
 const head=git('rev-parse','HEAD').toString().trim(),readback=await verifyCommit();
 scoped(git('diff','--name-only','46fbf6ffdc576b20014fab8ceea3fcedbf837a0c','HEAD').toString().trim().split(/\r?\n/));
 git('push','origin',branch);
 assert(git('ls-remote','--heads','origin',branch).toString().slice(0,40)===head,'Final remote hash mismatch');
 const finalPr=JSON.parse(run('gh',['pr','view',pr.url,'--json','url,isDraft,state,headRefOid']).toString());
 assert(finalPr.isDraft&&finalPr.state==='OPEN'&&finalPr.headRefOid===head,'Final PR mismatch');
 assert(git('status','--porcelain').toString().trim()==='','Dirty after publication');
 console.log(JSON.stringify({status:'GATE PASS',head,...readback,pr:finalPr,totals:m.totals,elapsed:m.elapsed,cutoff:m.coordinator.last_counter.timestamp,session:m.coordinator.file,completed_at:new Date().toISOString(),post_cutoff:'Final closeout and final reply remain for parent mechanical finalization; no further report rewrite.'}));
}catch(e){console.error(JSON.stringify({status:'GATE FAIL',message:e.message,stdout:e.stdout?.toString().slice(-1200),stderr:e.stderr?.toString().slice(-1800)}));process.exitCode=1;}
