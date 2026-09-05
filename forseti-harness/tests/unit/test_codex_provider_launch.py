"""Exercise the public launch boundary without provider access or real credentials."""
from __future__ import annotations

import json
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
                            launches=[], status="Logged in using ChatGPT\n", status_code=0)

    def local_check(command, **kwargs):
        state.checks.append((command, kwargs))
        assert command[0] == str(executable.resolve())
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 10
        if command[1:] == ["--version"]:
            return SimpleNamespace(returncode=0, stdout="codex-cli 0.153.1\n", stderr="")
        assert command[-2:] == ["login", "status"]
        return SimpleNamespace(returncode=state.status_code, stdout="", stderr=state.status)

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
