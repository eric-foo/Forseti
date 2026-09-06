"""Exercise the public launch boundary without provider access or real credentials."""
from __future__ import annotations

import json
import hashlib
import io
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import provider_execution
from provider_attempts import publish_provider_attempt
from runners import run_codex_provider_attempt as runner


@pytest.fixture
def launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    executable = tmp_path / "selected-codex.exe"
    executable.write_bytes(b"selected installation")
    prompt, schema = tmp_path / "prompt.md", tmp_path / "schema.json"
    prompt.write_text("exact prompt", encoding="utf-8")
    schema.write_text('{"type":"object"}', encoding="utf-8")
    for name in runner.AUTH_ROUTE_OVERRIDES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "auth-home"))
    argv = ["runner", "--codex-executable", str(executable), "--require-chatgpt",
            "--attempt-root", str(tmp_path / "attempts"), "--attempt-id", "test-001",
            "--prompt-file", str(prompt), "--output-schema", str(schema),
            "--worktree", str(tmp_path), "--model", "test-model", "--timeout-seconds", "5"]
    monkeypatch.setattr(sys, "argv", argv)
    state = SimpleNamespace(argv=argv, root=tmp_path, executable=executable, checks=[],
                            launches=[], status="Logged in using ChatGPT\n", status_code=0, status_stdout="")

    def local_check(command, **kwargs):
        state.checks.append((command, kwargs))
        assert command[0] == str(executable.resolve())
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 10
        if command[1:] == ["--version"]:
            return SimpleNamespace(returncode=0, stdout="codex-cli 0.153.1\n", stderr="")
        assert command[-2:] == ["login", "status"]
        return SimpleNamespace(returncode=state.status_code, stdout=state.status_stdout, stderr=state.status)

    def execute(**kwargs):
        state.launches.append(kwargs)
        return {"outcome": "PROCESS_COMPLETED"}

    monkeypatch.setattr(runner.subprocess, "run", local_check)
    monkeypatch.setattr(runner, "execute_provider_attempt", execute)
    return state


def test_selected_installation_auth_environment_and_native_restriction(launch, monkeypatch):
    # A competing PATH installation must never affect any check or generation.
    stale = launch.root / "stale"
    stale.mkdir()
    (stale / "codex.exe").write_bytes(b"wrong installation")
    monkeypatch.setenv("PATH", str(stale))
    assert runner.main() == 0
    assert len(launch.checks) == 2
    assert len(launch.launches) == 1
    call = launch.launches[0]
    assert call["command"][0] == str(launch.executable.resolve())
    assert 'forced_login_method="chatgpt"' in call["command"]
    assert '--ignore-user-config' in call["command"]
    assert call["command"][call["command"].index("--sandbox") + 1] == "read-only"
    for setting in runner.CHATGPT_CONFIG:
        assert setting in call["command"]
        assert setting in launch.checks[1][0]
    assert all(check[1]["env"] == call["env"] for check in launch.checks)
    assert call["launch_metadata"] == {
        "codex_version": "codex-cli 0.153.1", "authentication_policy": "chatgpt_only",
        "authentication_observed": "chatgpt",
    }


def test_required_context_is_verbatim_without_shell_or_prompt_mutation(launch):
    source = launch.root / "authority.md"
    original = '# Required rules\r\nPreserve "quoted" meaning, café, and  two spaces.\r\n'
    source.write_bytes(original.encode("utf-8"))
    context, manifest = runner.preloaded_context([source])
    launch.argv += ["--preload-context", str(source), "--expected-context-sha256",
                    hashlib.sha256(context.encode()).hexdigest()]
    assert runner.main() == 0
    call = launch.launches[0]
    setting = next(p for p in call["command"] if p.startswith("developer_instructions="))
    assert json.loads(setting.split("=", 1)[1]) == context
    assert original in context
    assert call["prompt_path"].read_text(encoding="utf-8") == "exact prompt"
    disabled = [call["command"][i+1] for i, value in enumerate(call["command"][:-1]) if value == "--disable"]
    assert {"shell_tool"}.issubset(disabled)
    assert json.loads(call["launch_metadata"]["preloaded_context_files"]) == manifest
    assert manifest[0]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert "project_doc_max_bytes=0" not in call["command"]


@pytest.mark.parametrize("mutation", ["changed", "missing", "empty", "invalid_utf8"])
def test_bad_or_changed_context_fails_before_auth_and_reservation(launch, mutation):
    source = launch.root / "authority.md"
    source.write_text("required rule", encoding="utf-8")
    context, _ = runner.preloaded_context([source])
    launch.argv += ["--preload-context", str(source), "--expected-context-sha256",
                    hashlib.sha256(context.encode()).hexdigest()]
    if mutation == "missing":
        source.unlink()
    else:
        source.write_bytes({"changed": b"different rule", "empty": b"", "invalid_utf8": b"\xff"}[mutation])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert not launch.checks and not launch.launches
    assert not (launch.root / "attempts").exists()


def test_default_launch_does_not_add_context_or_remove_tools(launch):
    assert runner.main() == 0
    command = launch.launches[0]["command"]
    assert not any(value.startswith("developer_instructions=") for value in command)
    assert "--disable" not in command


def test_job_passes_frozen_context_to_the_real_attempt_boundary(launch, monkeypatch):
    from runners import run_codex_provider_job as job_runner
    source = launch.root / "authority.md"
    source.write_text("required authority", encoding="utf-8")
    argv = ["job", "--job-dir", str(launch.root / "job"), "--attempt-root", str(launch.root / "attempts"),
            "--retry-budget-dir", str(launch.root / "budget"), "--run-retry-limit", "1",
            "--prompt-file", str(launch.root / "prompt.md"), "--output-schema", str(launch.root / "schema.json"),
            "--worktree", str(launch.root), "--codex-executable", str(launch.executable),
            "--model", "test-model", "--timeout-seconds", "5", "--preload-context", str(source)]
    monkeypatch.setattr(sys, "argv", argv)
    commands = []
    monkeypatch.setattr(job_runner.subprocess, "run", lambda command, **kwargs: commands.append(command))
    observed = {}

    def run_job(**kwargs):
        observed.update(kwargs['binding'])
        kwargs['launch']('job-attempt-001')
        return {'status': 'PROCESS_COMPLETED_NOT_VALIDATED', 'context': '\ufeff café 中文'}

    monkeypatch.setattr(job_runner, "run_provider_job", run_job)
    captured = io.BytesIO()
    console = io.TextIOWrapper(captured, encoding='cp1252')
    monkeypatch.setattr(sys, 'stdout', console)
    assert job_runner.main() == 0
    console.flush()
    assert json.loads(captured.getvalue().decode('cp1252'))['context'] == '\ufeff café 中文'
    command = commands[0]
    assert command[command.index('--preload-context') + 1] == str(source.resolve())
    assert command[command.index('--expected-context-sha256') + 1] == observed['preloaded_context_sha256']
    assert observed['preloaded_context_files'][0]['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert '--require-chatgpt' in command


def test_completed_attempt_is_reported_on_a_windows_ansi_console(launch, monkeypatch):
    # The receipt echoes the command, so preloaded context puts document bytes on
    # this console. A required overlay source starts with a BOM, and losing the
    # report of a completed, quota-consuming attempt to the encoder would also make
    # its exit code indistinguishable from a real generation failure.
    source = launch.root / "authority.md"
    source.write_bytes("\ufeff# Required rules\r\ncafé 中文\r\n".encode("utf-8"))
    context, _ = runner.preloaded_context([source])
    launch.argv += ["--preload-context", str(source), "--expected-context-sha256",
                    hashlib.sha256(context.encode()).hexdigest()]
    monkeypatch.setattr(runner, "execute_provider_attempt", lambda **kwargs: {
        "outcome": "PROCESS_COMPLETED", "command": list(kwargs["command"]),
        "launch_metadata": dict(kwargs["launch_metadata"])})
    captured = io.BytesIO()
    console = io.TextIOWrapper(captured, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", console)
    assert runner.main() == 0
    console.flush()
    reported = json.loads(captured.getvalue().decode("cp1252"))
    setting = next(p for p in reported["command"] if p.startswith("developer_instructions="))
    assert json.loads(setting.split("=", 1)[1]) == context
    assert reported["launch_metadata"]["preloaded_context_sha256"] == hashlib.sha256(context.encode()).hexdigest()


@pytest.mark.parametrize("name", runner.AUTH_ROUTE_OVERRIDES)
def test_override_rejected_before_checks_or_reservation(launch, monkeypatch, capsys, name):
    monkeypatch.setenv(name, "SECRET_DO_NOT_PRINT")
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    output = capsys.readouterr().err
    assert "rejects credential/endpoint overrides: " + name in output
    assert "SECRET_DO_NOT_PRINT" not in output
    assert not launch.checks and not launch.launches
    assert not (launch.root / "attempts").exists()


@pytest.mark.parametrize("status,code", [
    ("Logged in using an API key: SECRET_DO_NOT_PRINT", 0),
    ("Not logged in", 1), ("Logged in using ChatGPT", 1),
    ("WARNING: unknown auth\nLogged in using ChatGPT", 0), ("", 0),
])
def test_unverified_auth_stops_at_auth_boundary(launch, capsys, status, code):
    launch.status, launch.status_code = status, code
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert len(launch.checks) == 2  # Valid executable and files reached the auth guard.
    output = capsys.readouterr().err
    assert "ChatGPT authentication was not verified" in output
    assert "SECRET_DO_NOT_PRINT" not in output
    assert not launch.launches and not (launch.root / "attempts").exists()


def test_config_load_failure_is_not_reported_as_authentication(launch, capsys):
    # Observed natively: `login status` has no --ignore-user-config, so it loads
    # CODEX_HOME/config.toml and fails on a file the selected build cannot parse.
    # That is a configuration fault, not evidence about the sign-in method.
    launch.status = "Error loading configuration: config.toml:10:1: invalid type SECRET_DO_NOT_PRINT"
    launch.status_code = 1
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    output = capsys.readouterr().err
    assert "could not load its configuration" in output
    assert "authentication was not verified" not in output
    assert "SECRET_DO_NOT_PRINT" not in output
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("stdout,stderr,code,reason", [
    ("", "WARNING: SECRET_DO_NOT_PRINT\nLogged in using ChatGPT", 0,
     "unexpected_output_with_chatgpt_verdict"),
    ("", "Logged in using ChatGPT", 1, "local_check_nonzero_exit"),
    ("", "Logged in using an API key: SECRET_DO_NOT_PRINT", 0, "chatgpt_verdict_missing"),
    ("", "Not logged in", 1, "local_check_nonzero_exit"),
    ("Logged in using ChatGPT", "Logged in using ChatGPT", 0, "chatgpt_verdict_ambiguous"),
    ("", "", 0, "chatgpt_verdict_missing"),
    ("", "Error loading config: SECRET_DO_NOT_PRINT", 1, "configuration_load_failed"),
])
def test_refused_login_preserves_safe_diagnostic_in_job_log(launch, capsys, stdout, stderr, code, reason):
    launch.status_stdout, launch.status, launch.status_code = stdout, stderr, code
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    output = capsys.readouterr().err
    marker = "FORSETI_CODEX_AUTH_CHECK_FAILED "
    diagnostic, = [json.loads(line[len(marker):]) for line in output.splitlines() if line.startswith(marker)]
    assert diagnostic["reason"] == reason
    assert diagnostic["exit_code"] == code
    assert diagnostic["generation_started"] is False
    for name, raw in (("stdout", stdout), ("stderr", stderr)):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        assert diagnostic["streams"][name]["chatgpt_verdict_count"] == lines.count("Logged in using ChatGPT")
    assert "SECRET_DO_NOT_PRINT" not in output
    assert not launch.launches and not (launch.root / "attempts").exists()
    assert len(launch.checks) == 2  # No retry or change to the authentication guard.


# Observed natively from codex-cli 0.153.1: `login status` writes its verdict to
# stderr, so that stream also carries Codex's own non-fatal notices. A signed-in
# ChatGPT account still reports exit 0 behind one.
NATIVE_NOTICE = (
    "WARNING: proceeding, even though we could not create PATH aliases: Refusing to "
    'create helper binaries under temporary dir "C:\\\\Temp\\\\"\n'
)


def test_native_nonfatal_notice_does_not_defeat_verified_chatgpt_auth(launch):
    launch.status = NATIVE_NOTICE + "Logged in using ChatGPT\n"
    assert runner.main() == 0
    assert launch.launches[0]["launch_metadata"]["authentication_observed"] == "chatgpt"


def test_native_nonfatal_notice_never_admits_a_non_chatgpt_verdict(launch, capsys):
    # Tolerating the notice must not tolerate the verdict printed behind it.
    launch.status = NATIVE_NOTICE + "Logged in using an API key: SECRET_DO_NOT_PRINT\n"
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    output = capsys.readouterr().err
    assert "ChatGPT authentication was not verified" in output
    assert "SECRET_DO_NOT_PRINT" not in output
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("notice", [
    "WARNING: proceeding, even though authentication could not be verified\n",
    "WARNING: proceeding, even though we could not create PATH aliases: unknown failure\n",
])
def test_unproven_continuation_notice_still_rejects(launch, capsys, notice):
    launch.status = notice + "Logged in using ChatGPT\n"
    with pytest.raises(SystemExit):
        runner.main()
    assert "ChatGPT authentication was not verified" in capsys.readouterr().err
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("stdout,stderr,code", [
    ("", NATIVE_NOTICE, 0),
    ("", NATIVE_NOTICE + "Logged in using ChatGPT\n", 1),
    (NATIVE_NOTICE.rstrip(), "Logged in using ChatGPT\n", 0),
    ("Logged in using an API key", NATIVE_NOTICE + "Logged in using ChatGPT\n", 0),
    ("Logged in using ChatGPT", NATIVE_NOTICE + "Logged in using ChatGPT\n", 0),
    ("", NATIVE_NOTICE.rstrip() + " unexpected suffix\nLogged in using ChatGPT", 0),
])
def test_notice_cannot_hide_missing_conflicting_or_failed_auth(launch, capsys, stdout, stderr, code):
    launch.status_stdout, launch.status, launch.status_code = stdout, stderr, code
    with pytest.raises(SystemExit):
        runner.main()
    assert "ChatGPT authentication was not verified" in capsys.readouterr().err
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("suffix", [".cmd", ".BAT"])
def test_shim_rejection_uses_resolution_without_symlink_privilege(launch, monkeypatch, capsys, suffix):
    shim = launch.root / ("codex" + suffix)
    shim.write_text("not executable")
    original = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == launch.executable:
            return shim
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(SystemExit):
        runner.main()
    assert ".cmd/.bat shim" in capsys.readouterr().err
    assert not launch.checks and not launch.launches


def test_shim_rejection_judges_the_resolved_executable(launch, capsys):
    # The guard must inspect the path that actually runs, not the name given.
    shim = launch.root / "codex.cmd"
    shim.write_text("not executable")
    link = launch.root / "codex-link.exe"
    try:
        link.symlink_to(shim)
    except (OSError, NotImplementedError) as exc:  # unprivileged Windows host
        pytest.skip(f"symlink creation unavailable: {exc}")
    launch.argv[2] = str(link)
    with pytest.raises(SystemExit):
        runner.main()
    assert ".cmd/.bat shim" in capsys.readouterr().err
    assert not launch.checks and not launch.launches


@pytest.mark.parametrize("kind", ["missing", "relative", "shim", "omitted"])
def test_executable_never_falls_back_to_path(launch, capsys, kind):
    if kind == "missing":
        launch.executable.unlink()
    elif kind == "relative":
        launch.argv[2] = "selected-codex.exe"
    elif kind == "shim":
        shim = launch.root / "codex.cmd"
        shim.write_text("not executable")
        launch.argv[2] = str(shim)
    else:
        del launch.argv[1:3]
    with pytest.raises(SystemExit):
        runner.main()
    assert "--codex-executable" in capsys.readouterr().err
    assert not launch.checks and not launch.launches


def test_unrunnable_executable_keeps_its_operating_system_diagnosis(launch, monkeypatch, capsys):
    # A spawn failure happens before the child exists, so the only detail available
    # is operating-system text naming why the selected executable cannot run.
    def broken(command, **kwargs):
        raise OSError(8, "%1 is not a valid Win32 application")

    monkeypatch.setattr(runner.subprocess, "run", broken)
    with pytest.raises(SystemExit):
        runner.main()
    output = capsys.readouterr().err
    assert "%1 is not a valid Win32 application" in output
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("fault", ["timeout", "permission", "bad-version"])
def test_diagnostic_failures_never_launch_or_expose_output(launch, monkeypatch, capsys, fault):
    def broken(command, **kwargs):
        if fault == "timeout":
            raise subprocess.TimeoutExpired(command, 10, output="SECRET_DO_NOT_PRINT")
        if fault == "permission":
            raise PermissionError("SECRET_DO_NOT_PRINT")
        return SimpleNamespace(returncode=0, stdout="unexpected SECRET_DO_NOT_PRINT", stderr="")
    monkeypatch.setattr(runner.subprocess, "run", broken)
    with pytest.raises(SystemExit):
        runner.main()
    output = capsys.readouterr().err
    assert "SECRET_DO_NOT_PRINT" not in output
    assert "local check failed" in output or "did not report a Codex CLI version" in output
    assert not launch.launches and not (launch.root / "attempts").exists()


@pytest.mark.parametrize("filename", ["prompt.md", "schema.json"])
def test_existing_but_unreadable_input_stops_before_auth(launch, monkeypatch, capsys, filename):
    original = Path.open
    def denied(path, *args, **kwargs):
        if path == launch.root / filename:
            raise PermissionError("different execution identity")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(SystemExit):
        runner.main()
    assert "unreadable in this execution context" in capsys.readouterr().err
    assert not launch.checks and not launch.launches


def test_output_creation_failure_stops_before_process(launch, monkeypatch, capsys):
    monkeypatch.setattr(runner, "execute_provider_attempt", provider_execution.execute_provider_attempt)
    original = Path.open
    def denied(path, *args, **kwargs):
        if path.name == "execution_started.json":
            raise PermissionError("output permission denied")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    monkeypatch.setattr(provider_execution.subprocess, "Popen",
                        lambda *a, **kw: pytest.fail("must not launch before output creation"))
    with pytest.raises(SystemExit):
        runner.main()
    error = capsys.readouterr().err
    assert "execution file access failed" in error
    assert "PermissionError: output permission denied" in error  # real cause, not a generic label
    assert len(launch.checks) == 2
    assert (launch.root / "attempts/test-001").is_dir()


def test_public_command_preserves_environment_receipts_and_native_publication(launch, monkeypatch):
    monkeypatch.setattr(runner, "execute_provider_attempt", provider_execution.execute_provider_attempt)
    real_popen = subprocess.Popen
    captured = []
    usage = {"input_tokens": 12, "cached_input_tokens": 0, "output_tokens": 4, "reasoning_output_tokens": 1}
    def process(command, **kwargs):
        captured.append((command, kwargs))
        response = command[command.index("--output-last-message") + 1]
        script = (
            "import json,os,sys; from pathlib import Path; "
            "assert sys.stdin.read() == 'exact prompt'; "
            f"assert os.environ['CODEX_HOME'] == {str(launch.root / 'auth-home')!r}; "
            f"Path({response!r}).write_text('{{\"answer\":42}}'); "
            f"print(json.dumps({{'type':'turn.completed','usage':{usage!r}}}))"
        )
        return real_popen([sys.executable, "-c", script], **kwargs)
    monkeypatch.setattr(provider_execution.subprocess, "Popen", process)
    assert runner.main() == 0
    attempt = launch.root / "attempts/test-001"
    receipt = json.loads((attempt / "execution_receipt.json").read_text())
    assert receipt["command"][0] == str(launch.executable.resolve())
    assert receipt["launch_metadata"]["authentication_observed"] == "chatgpt"
    assert receipt["usage"] == usage
    assert "env" not in receipt
    published = publish_provider_attempt(
        attempt_dir=attempt, response_dir=launch.root / "accepted",
        canonical_response_name="answer.json", usage_schema_version="test_usage_v1",
        validate_response=lambda value: {"validated_answer": value["answer"]},
    )
    assert published["validated_answer"] == 42
    before = {path.name: path.read_bytes() for path in attempt.iterdir()}
    with pytest.raises(SystemExit):
        runner.main()
    assert len(captured) == 1
    assert before == {path.name: path.read_bytes() for path in attempt.iterdir()}
