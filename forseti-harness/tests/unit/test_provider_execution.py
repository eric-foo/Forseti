from __future__ import annotations

import io
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import provider_execution
from runners import run_codex_provider_attempt
from harness_utils import sha256_bytes
from provider_attempts import publish_provider_attempt, reserve_provider_attempt
from provider_execution import execute_provider_attempt


USAGE = {"input_tokens": 120, "cached_input_tokens": 40, "output_tokens": 25, "reasoning_output_tokens": 9}


@pytest.mark.parametrize("effort", [None, "high", "xhigh", "max", "medium"])
def test_provider_runner_high_only_before_reservation_or_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
    effort: str | None,
) -> None:
    prompt, schema = tmp_path / "prompt.md", tmp_path / "schema.json"
    prompt.write_text("test")
    schema.write_text("{}")
    root = tmp_path / "attempts"
    argv = ["runner", "--attempt-root", str(root), "--attempt-id", "test-001",
            "--prompt-file", str(prompt), "--output-schema", str(schema),
            "--worktree", str(tmp_path), "--model", "test-model", "--timeout-seconds", "5",
            "--codex-executable", sys.executable]
    if effort is not None:
        argv += ["--reasoning-effort", effort]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(run_codex_provider_attempt, "_local_codex_check",
                        lambda *args: SimpleNamespace(returncode=0, stdout="codex-cli 0.153.1\n", stderr=""))
    launches = []

    def capture(**kwargs):
        launches.append(kwargs["command"])
        return {"outcome": "PROCESS_COMPLETED"}

    monkeypatch.setattr(run_codex_provider_attempt, "execute_provider_attempt", capture)
    if effort in (None, "high"):
        assert run_codex_provider_attempt.main() == 0
        assert len(launches) == 1
        assert 'model_reasoning_effort="high"' in launches[0]
    else:
        with pytest.raises(SystemExit) as error:
            run_codex_provider_attempt.main()
        assert error.value.code == 2
        assert "--reasoning-effort: invalid choice" in capsys.readouterr().err
        assert launches == []
        assert not root.exists()


def _setup(tmp_path: Path, name: str = "attempt-001") -> tuple[Path, Path]:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("exact prompt", encoding="utf-8")
    attempt = Path(reserve_provider_attempt(attempt_root=tmp_path / "attempts", attempt_id=name)["attempt_dir"])
    return prompt, attempt


def _response_script(attempt: Path) -> str:
    return (
        "import json,sys,time; from pathlib import Path; sys.stdin.buffer.read(); "
        f"Path({str(attempt / 'response.json')!r}).write_text('{{\"answer\":42}}',encoding='utf-8'); "
        f"print(json.dumps({{'type':'turn.completed','usage':{USAGE!r}}}),flush=True); "
    )


def _publish(attempt: Path, tmp_path: Path) -> dict:
    return publish_provider_attempt(
        attempt_dir=attempt, response_dir=tmp_path / "canonical",
        canonical_response_name="answer.json", usage_schema_version="test_usage_v1",
        validate_response=lambda response: {"validated_answer": response["answer"]},
    )


def test_success_preserves_exact_output_usage_and_stage_acceptance(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    result = execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)],
        prompt_path=prompt, attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    assert result["outcome"] == "PROCESS_COMPLETED"
    assert result["acceptance_status"] == "NOT_VALIDATED"
    assert result["usage"] == USAGE
    assert result["usage_status"] == "COMPLETED_TURN_REPORTED"
    assert result["useful_compute_seconds"] is None
    assert "provider_active_seconds" not in result
    published = _publish(attempt, tmp_path)
    assert published["validated_answer"] == 42
    assert Path(published["response_path"]).read_bytes() == (attempt / "response.json").read_bytes()


def test_retry_is_on_disk_and_mirrored_before_completion(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    echo = io.BytesIO()
    result: dict = {}
    errors: list[BaseException] = []
    script = "import sys,time; print('retrying sampling request (1/5)',file=sys.stderr,flush=True); time.sleep(1.5)"

    def run() -> None:
        try:
            result.update(execute_provider_attempt(
                command=[sys.executable, "-c", script], prompt_path=prompt,
                attempt_dir=attempt, timeout_seconds=5, stderr_echo=echo,
            ))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    deadline = time.monotonic() + 3
    while b"retrying sampling request" not in echo.getvalue() and time.monotonic() < deadline:
        time.sleep(0.02)
    observed_while_running = thread.is_alive()
    on_disk = (attempt / "stderr.log").read_bytes()
    thread.join(timeout=5)
    assert not errors
    assert observed_while_running
    assert b"retrying sampling request" in echo.getvalue()
    assert b"retrying sampling request" in on_disk
    assert result["observed_retry_events"] == 1
    assert result["usage"] is None
    assert result["usage_status"] == "UNOBSERVED_OR_INCOMPLETE"


def test_repeated_events_do_not_reset_deadline_or_allow_partial_publication(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    script = _response_script(attempt) + "\nwhile True:\n print('retrying sampling request (1/5)',file=sys.stderr,flush=True)\n time.sleep(0.05)\n"
    started = time.monotonic()
    result = execute_provider_attempt(
        command=[sys.executable, "-c", script], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=0.6, stderr_echo=io.BytesIO(),
    )
    assert time.monotonic() - started < 5
    assert result["outcome"] == "TIMED_OUT"
    assert result["observed_retry_events"] >= 2
    # A parseable answer AND reported usage cannot bypass a failed execution.
    assert result["usage"] == USAGE
    assert json.loads((attempt / "response.json").read_text()) == {"answer": 42}
    with pytest.raises(ValueError, match="execution did not complete successfully"):
        _publish(attempt, tmp_path)
    assert not (tmp_path / "canonical").exists()


def test_process_failure_is_preserved_and_cannot_publish(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    result = execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt) + "sys.exit(7)"],
        prompt_path=prompt, attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    assert result["outcome"] == "PROCESS_FAILED"
    assert result["exit_code"] == 7
    with pytest.raises(ValueError, match="execution did not complete successfully"):
        _publish(attempt, tmp_path)


def test_silent_but_healthy_process_is_allowed_to_finish(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    result = execute_provider_attempt(
        command=[sys.executable, "-c", "import time; time.sleep(0.4)"],
        prompt_path=prompt, attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    assert result["outcome"] == "PROCESS_COMPLETED"
    assert result["observed_retry_events"] == 0
    assert result["useful_compute_seconds"] is None


def test_timeout_stops_spawned_child_before_it_can_write_later(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    ready, later = tmp_path / "child-ready", tmp_path / "child-later"
    child = (
        "import time; from pathlib import Path; "
        f"Path({str(ready)!r}).write_text('ready'); time.sleep(2); "
        f"Path({str(later)!r}).write_text('still running')"
    )
    parent = f"import subprocess,time; subprocess.Popen([{sys.executable!r},'-c',{child!r}]); time.sleep(30)"
    result = execute_provider_attempt(
        command=[sys.executable, "-c", parent], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=1, stderr_echo=io.BytesIO(),
    )
    assert ready.exists(), "the child must have started, not failed incidentally"
    assert result["outcome"] == "TIMED_OUT"
    time.sleep(1.5)
    assert not later.exists()


def test_launch_failure_has_a_durable_receipt(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    result = execute_provider_attempt(
        command=[str(tmp_path / "missing-executable")], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    assert result["outcome"] == "LAUNCH_FAILED"
    durable = json.loads((attempt / "execution_receipt.json").read_text())
    assert durable["outcome"] == "LAUNCH_FAILED"
    assert durable["usage"] is None


def test_unfinished_execution_cannot_publish_even_with_complete_response(tmp_path: Path) -> None:
    _, attempt = _setup(tmp_path)
    (attempt / "execution_started.json").write_text("{}")
    (attempt / "response.json").write_text('{"answer":42}')
    (attempt / "events.jsonl").write_text(json.dumps({"type": "turn.completed", "usage": USAGE}))
    with pytest.raises(ValueError, match="execution is unfinished"):
        _publish(attempt, tmp_path)


def test_reuse_is_refused_and_new_attempt_preserves_prior_outputs(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    before = {path.name: path.read_bytes() for path in attempt.iterdir()}
    with pytest.raises(ValueError, match="refusing to overwrite"):
        execute_provider_attempt(
            command=[sys.executable, "-c", "raise Exception('must not launch')"],
            prompt_path=prompt, attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
        )
    with pytest.raises(ValueError, match="refusing to reuse provider attempt"):
        reserve_provider_attempt(attempt_root=attempt.parent, attempt_id=attempt.name)
    reserve_provider_attempt(attempt_root=attempt.parent, attempt_id="attempt-002")
    assert before == {path.name: path.read_bytes() for path in attempt.iterdir()}


def test_changed_output_cannot_publish(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    (attempt / "response.json").write_text('{"answer":43}')
    with pytest.raises(ValueError, match="execution output changed: response.json"):
        _publish(attempt, tmp_path)


def test_publication_reuses_the_receipt_checked_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prompt, attempt = _setup(tmp_path)
    execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    response_path, events_path = attempt / "response.json", attempt / "events.jsonl"
    response_bytes, event_bytes = response_path.read_bytes(), events_path.read_bytes()
    read_bytes = Path.read_bytes

    def read_then_change(path: Path) -> bytes:
        captured = read_bytes(path)
        if path == response_path:
            path.write_text('{"answer":43}', encoding="utf-8")
        elif path == events_path:
            path.write_text(json.dumps({"type": "turn.completed", "usage": {**USAGE, "input_tokens": 999}}), encoding="utf-8")
        return captured

    # Deterministically change each source immediately after its first read,
    # rather than relying on a subprocess scheduling race.
    monkeypatch.setattr(Path, "read_bytes", read_then_change)

    def validate(response: dict) -> dict:
        assert response == {"answer": 42}
        return {"validated_answer": 42}

    published = publish_provider_attempt(
        attempt_dir=attempt, response_dir=tmp_path / "canonical",
        canonical_response_name="answer.json", usage_schema_version="test_usage_v1",
        validate_response=validate,
    )
    assert read_bytes(Path(published["response_path"])) == response_bytes
    usage = json.loads((attempt / "usage.json").read_text())
    assert usage["response_sha256"] == sha256_bytes(response_bytes)
    assert usage["events_sha256"] == sha256_bytes(event_bytes)
    assert usage["usage"] == USAGE
    assert published["usage"] == USAGE


def test_publication_does_not_reread_response_after_validation(tmp_path: Path) -> None:
    prompt, attempt = _setup(tmp_path)
    execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=io.BytesIO(),
    )
    response_path = attempt / "response.json"
    expected = response_path.read_bytes()

    def validate(response: dict) -> dict:
        assert response == {"answer": 42}
        response_path.write_text('{"answer":43}', encoding="utf-8")
        return {}

    published = publish_provider_attempt(
        attempt_dir=attempt, response_dir=tmp_path / "canonical",
        canonical_response_name="answer.json", usage_schema_version="test_usage_v1",
        validate_response=validate,
    )
    assert Path(published["response_path"]).read_bytes() == expected


class _BrokenEcho(io.BytesIO):
    """A console stream that has gone away mid-attempt."""

    def write(self, data: object) -> int:  # type: ignore[override]
        raise ValueError("I/O operation on closed file")


@pytest.mark.parametrize("finish_before_poll", [False, True])
def test_broken_stderr_echo_preserves_the_attempt_its_receipt_and_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, finish_before_poll: bool,
) -> None:
    if finish_before_poll:
        launch = provider_execution.subprocess.Popen

        def finished_process(*args: object, **kwargs: object) -> subprocess.Popen:
            process = launch(*args, **kwargs)
            process.wait(timeout=5)
            return process

        # Skip the polling loop deterministically: the echo fails in finally.
        monkeypatch.setattr(provider_execution.subprocess, "Popen", finished_process)
    prompt, attempt = _setup(tmp_path)
    script = _response_script(attempt) + "print('retrying sampling request (1/5)',file=sys.stderr,flush=True)"
    result = execute_provider_attempt(
        command=[sys.executable, "-c", script], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=5, stderr_echo=_BrokenEcho(),
    )
    # A dead console is not a failed model attempt, and the log stays authoritative.
    assert result["outcome"] == "PROCESS_COMPLETED"
    assert result["stderr_echo_status"] == "FAILED"
    assert "ValueError" in result["stderr_echo_error"]
    assert b"retrying sampling request" in (attempt / "stderr.log").read_bytes()
    durable = json.loads((attempt / "execution_receipt.json").read_text())
    assert durable["outcome"] == "PROCESS_COMPLETED"
    assert durable["observed_retry_events"] == 1
    assert _publish(attempt, tmp_path)["validated_answer"] == 42


def test_absent_console_stream_does_not_block_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prompt, attempt = _setup(tmp_path)
    monkeypatch.setattr(provider_execution.sys, "stderr", None)
    result = execute_provider_attempt(
        command=[sys.executable, "-c", _response_script(attempt)],
        prompt_path=prompt, attempt_dir=attempt, timeout_seconds=5,
    )
    assert result["outcome"] == "PROCESS_COMPLETED"
    assert result["stderr_echo_status"] == "UNAVAILABLE"
    assert result["stderr_echo_error"] is None


def test_stop_process_tree_reports_faults_instead_of_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(provider_execution.subprocess, "run", lambda *a, **k: None)
    # killpg is POSIX-only; the stub must exist without asserting the platform.
    monkeypatch.setattr(provider_execution.os, "killpg", lambda *a, **k: None, raising=False)

    class Stuck:
        pid, returncode = 999_999_999, None

        def wait(self, timeout: float | None = None) -> int:
            raise subprocess.TimeoutExpired(cmd="child", timeout=timeout or 0)

        def kill(self) -> None:
            raise PermissionError("kill denied")

        def poll(self) -> int | None:
            return None

    failure = provider_execution._stop_process_tree(Stuck())
    assert failure is not None
    assert "PermissionError" in failure
    assert "process tree may still be running" in failure


def test_cleanup_failure_does_not_relabel_a_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prompt, attempt = _setup(tmp_path)
    stop = provider_execution._stop_process_tree
    monkeypatch.setattr(
        provider_execution, "_stop_process_tree",
        lambda process: (stop(process), "taskkill timed out")[1],
    )
    result = execute_provider_attempt(
        command=[sys.executable, "-c", "import time; time.sleep(30)"], prompt_path=prompt,
        attempt_dir=attempt, timeout_seconds=0.5, stderr_echo=io.BytesIO(),
    )
    # The deadline breach is the terminal fact; a cleanup fault is recorded, not substituted.
    assert result["outcome"] == "TIMED_OUT"
    assert result["error"] == "cleanup failed: taskkill timed out"
    with pytest.raises(ValueError, match="execution did not complete successfully"):
        _publish(attempt, tmp_path)


def test_failed_windows_tree_stop_is_reported_even_if_parent_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(provider_execution, "os", SimpleNamespace(name="nt"))

    def failed_taskkill(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        result = subprocess.CompletedProcess(command, returncode=1)
        if kwargs.get("check"):
            result.check_returncode()
        return result

    monkeypatch.setattr(provider_execution.subprocess, "run", failed_taskkill)
    process = SimpleNamespace(pid=999_999_999, wait=lambda **kw: 0, poll=lambda: 0)
    failure = provider_execution._stop_process_tree(process)
    assert failure is not None
    assert "CalledProcessError" in failure


def test_failed_execution_without_a_start_record_cannot_publish(tmp_path: Path) -> None:
    _, attempt = _setup(tmp_path)
    (attempt / "response.json").write_text('{"answer":42}')
    (attempt / "events.jsonl").write_text(json.dumps({"type": "turn.completed", "usage": USAGE}))
    (attempt / "execution_receipt.json").write_text(json.dumps({"outcome": "TIMED_OUT"}))
    with pytest.raises(ValueError, match="execution did not complete successfully"):
        _publish(attempt, tmp_path)
    assert not (tmp_path / "canonical").exists()


def test_unusable_execution_receipt_cannot_publish(tmp_path: Path) -> None:
    _, attempt = _setup(tmp_path)
    (attempt / "execution_started.json").write_text("{}")
    (attempt / "response.json").write_text('{"answer":42}')
    (attempt / "events.jsonl").write_text(json.dumps({"type": "turn.completed", "usage": USAGE}))
    (attempt / "execution_receipt.json").write_text("[]")
    with pytest.raises(ValueError, match="receipt is unusable"):
        _publish(attempt, tmp_path)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout_is_rejected_before_launch(tmp_path: Path, timeout: float) -> None:
    prompt, attempt = _setup(tmp_path)
    with pytest.raises(ValueError, match="finite and positive"):
        execute_provider_attempt(command=[sys.executable, "-c", "pass"], prompt_path=prompt,
                                 attempt_dir=attempt, timeout_seconds=timeout, stderr_echo=io.BytesIO())
    assert list(attempt.iterdir()) == []
