"""Explicit simulated executions; no provider calls or production success receipts."""
import json
from pathlib import Path
import pytest
from harness_utils import hash_file
from provider_jobs import run_provider_job, transient_failure, _lock


@pytest.fixture
def job(tmp_path):
    for name in ('prompt','schema','runner','codex'):
        (tmp_path/name).write_text(name,encoding='utf-8')
    binding = {k+'_path':str(tmp_path/k) for k in ('prompt','schema','runner')}
    binding.update({k+'_sha256':hash_file(tmp_path/k) for k in ('prompt','schema','runner','codex')})
    binding.update(codex_executable=str(tmp_path/'codex'),model='test-model',worktree=str(tmp_path))
    calls=[]; outcomes=[]; sleeps=[]
    def launch(aid):
        calls.append(aid); outcome=outcomes.pop(0)
        p=tmp_path/'attempts'/aid; p.mkdir(parents=True)
        events=json.dumps({'type':'error','message':'Selected model is at capacity. Please try a different model.'}) if outcome=='capacity' else ''
        (p/'events.jsonl').write_text(events,encoding='utf-8'); (p/'stderr.log').write_text('',encoding='utf-8')
        (p/'response.json').write_text('{"simulated":true}',encoding='utf-8')
        receipt=dict(outcome='PROCESS_FAILED' if outcome=='capacity' else outcome,
            command=[binding['codex_executable'],'exec','--model',binding['model'],'-C',binding['worktree']],
            prompt_sha256=binding['prompt_sha256'],response_schema_sha256=binding['schema_sha256'],
            events_sha256=hash_file(p/'events.jsonl'),stderr_sha256=hash_file(p/'stderr.log'),
            response_sha256=hash_file(p/'response.json'),launch_metadata={'authentication_observed':'chatgpt'},usage=None)
        (p/'execution_receipt.json').write_text(json.dumps(receipt),encoding='utf-8')
    args=dict(job_dir=tmp_path/'job',attempt_root=tmp_path/'attempts',binding=binding,launch=launch,
        retry_budget_dir=tmp_path/'budget',run_retry_limit=1,sleep=sleeps.append)
    return args,calls,outcomes,sleeps


def test_capacity_recovers_once_and_restart_does_not_generate_or_recount(job):
    args,calls,outcomes,sleeps=job; outcomes.extend(['capacity','PROCESS_COMPLETED'])
    result=run_provider_job(**args)
    assert result['status']=='PROCESS_COMPLETED_NOT_VALIDATED' and len(calls)==2 and sleeps==[10]
    assert run_provider_job(**args)==result and len(calls)==2
    assert len(list(args['retry_budget_dir'].glob('claim-*.json')))==1
    assert result['execution_receipt']['usage'] is None


@pytest.mark.parametrize('outcome',['TIMED_OUT','PROCESS_FAILED'])
def test_unknown_failure_is_not_retried(job,outcome):
    args,calls,outcomes,_=job; outcomes.append(outcome)
    assert run_provider_job(**args)['status']=='JOB_FAILED' and len(calls)==1
    assert run_provider_job(**args)['status']=='JOB_FAILED' and len(calls)==1


def test_budget_is_shared_and_zero_budget_is_not_a_free_retry(job):
    args,calls,outcomes,_=job; outcomes.extend(['capacity','PROCESS_COMPLETED','capacity'])
    run_provider_job(**args)
    args['job_dir']=args['job_dir'].with_name('other-job')
    with pytest.raises(ValueError,match='budget exhausted'): run_provider_job(**args)
    assert len(calls)==3
    with pytest.raises(ValueError,match='budget exhausted'): run_provider_job(**args)
    assert len(calls)==3


def test_source_drift_and_unknown_launch_cannot_restart(job):
    args,calls,outcomes,_=job; outcomes.append('PROCESS_COMPLETED')
    result=run_provider_job(**args)
    Path(args['binding']['prompt_path']).write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='input changed'): run_provider_job(**args)
    assert len(calls)==1
    Path(args['binding']['prompt_path']).write_text('prompt',encoding='utf-8')
    (Path(result['attempt_dir'])/'execution_receipt.json').unlink()
    with pytest.raises(ValueError,match='outcome unknown'): run_provider_job(**args)
    assert len(calls)==1


def test_diagnostics_are_typed_and_auth_errors_do_not_become_network_retries():
    receipt={'outcome':'TIMED_OUT'}
    reset='2026-09-05T19:15:41.785887Z  WARN codex_core::responses_retry: stream disconnected - retrying sampling request (1/5 in 199ms)... sampling_error=stream disconnected before completion: WebSocket protocol error: Connection reset without closing handshake\n'
    assert transient_failure(receipt,'',reset)=='connection_reset'
    assert transient_failure(receipt,json.dumps({'type':'error','message':'authentication failed'}),reset) is None
    assert transient_failure(receipt,json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Selected model is at capacity.'}}),'') is None
    assert transient_failure({'outcome':'PROCESS_COMPLETED'},'',reset) is None
    completed = json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'preserved answer'}})
    assert transient_failure(receipt,completed,reset) is None
    assert transient_failure(receipt,json.dumps({'type':'turn.completed'}),reset) is None


def test_concurrent_job_and_changed_completed_response_fail_before_launch(job):
    args,calls,outcomes,_=job
    with _lock(args['job_dir']/'job.lock'):
        with pytest.raises(ValueError,match='already in use'): run_provider_job(**args)
    outcomes.append('PROCESS_COMPLETED'); result=run_provider_job(**args)
    (Path(result['attempt_dir'])/'response.json').write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='response bytes changed'): run_provider_job(**args)
    assert len(calls)==1


def test_budget_contention_serializes_without_losing_a_claim(tmp_path):
    import threading
    from provider_jobs import _claim_retry
    ready = threading.Event()
    failures = []
    def claim():
        ready.set()
        try:
            _claim_retry(tmp_path/'budget', 1, tmp_path/'job', 'retry-2')
        except Exception as exc:
            failures.append(exc)
    with _lock(tmp_path/'budget/budget.lock'):
        worker = threading.Thread(target=claim)
        worker.start()
        assert ready.wait(1)
    worker.join(6)
    assert not worker.is_alive() and not failures
    assert len(list((tmp_path/'budget').glob('claim-*.json'))) == 1


def test_unrelated_job_cannot_adopt_an_existing_attempt(job):
    args,calls,outcomes,_=job; outcomes.append('PROCESS_COMPLETED')
    run_provider_job(**args)
    args['job_dir'] = args['job_dir'].parent/'another-parent'/'job'
    with pytest.raises(ValueError,match='does not belong'): run_provider_job(**args)
    assert len(calls)==1


@pytest.mark.parametrize('after_capacity', [False, True])
def test_refused_launch_is_not_reported_as_a_preserved_unknown_attempt(job, after_capacity):
    args,calls,outcomes,_=job
    original_launch = args['launch']
    if after_capacity:
        outcomes.append('capacity')
    def refuse(aid):
        if after_capacity and aid.endswith('-001'):
            original_launch(aid)
        else:
            calls.append(aid)
    args['launch']=refuse
    with pytest.raises(ValueError,match='no execution receipt'): run_provider_job(**args)
    index = 2 if after_capacity else 1
    assert not (args['attempt_root']/(args['job_dir'].name+f'-attempt-{index:03d}')).exists()
    intent = args['job_dir']/f'launch-{index:03d}.json'
    before_intent = intent.read_bytes()
    before_claims = {p.name:p.read_bytes() for p in args['retry_budget_dir'].glob('claim-*.json')}
    with pytest.raises(ValueError,match='launch intent exists but its attempt directory is missing; execution is unconfirmed') as failure:
        run_provider_job(**args)
    assert 'clear' not in str(failure.value)
    assert len(calls)==index
    assert intent.read_bytes() == before_intent
    assert len(before_claims) == int(after_capacity)
    assert {p.name:p.read_bytes() for p in args['retry_budget_dir'].glob('claim-*.json')} == before_claims
