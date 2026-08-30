from __future__ import annotations

import io
import json
import sys
import threading
import time
from pathlib import Path

import pytest

from provider_attempts import publish_provider_attempt, reserve_provider_attempt
from provider_execution import execute_provider_attempt


USAGE = {"input_tokens": 120, "cached_input_tokens": 40, "output_tokens": 25, "reasoning_output_tokens": 9}


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


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout_is_rejected_before_launch(tmp_path: Path, timeout: float) -> None:
    prompt, attempt = _setup(tmp_path)
    with pytest.raises(ValueError, match="finite and positive"):
        execute_provider_attempt(command=[sys.executable, "-c", "pass"], prompt_path=prompt,
                                 attempt_dir=attempt, timeout_seconds=timeout, stderr_echo=io.BytesIO())
    assert list(attempt.iterdir()) == []
