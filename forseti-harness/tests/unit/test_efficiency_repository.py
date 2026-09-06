from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from reports.efficiency_repository import repository_size


def git(repo, *arguments, input=None):
    environment = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    return subprocess.run(["git", "-C", str(repo), "-c", "core.autocrlf=false",
                           "-c", "core.hooksPath=nonexistent-hooks", "-c", "user.name=Fixture",
                           "-c", "user.email=fixture@example.invalid", *arguments],
                          input=input, check=True, capture_output=True, env=environment).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    root = tmp_path / "repo with spaces"
    root.mkdir()
    git(root, "init")
    contents = {"AGENTS.md": b"rules\n", "CLAUDE.md": b"shim\n",
                ".agents/workflow-overlay/README.md": b"overlay\n",
                "source with spaces/caf\u00e9.txt": "perfume \u2728\n".encode(),
                "copy.txt": "perfume \u2728\n".encode(),
                ".gitignore": b"forseti-harness/memory/logs/efficiency/\n"}
    for name, body in contents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    git(root, "add", ".")
    git(root, "commit", "--no-gpg-sign", "-m", "fixture")
    return root, contents


def test_exact_commit_bytes_ignore_working_tree_and_untracked_content(repo):
    root, contents = repo
    commit = git(root, "rev-parse", "HEAD").decode()
    scratch = root / "untracked.bin"
    scratch.write_bytes(b"preserve me" * 100)
    (root / "AGENTS.md").write_bytes(b"uncommitted rules" * 100)
    result = repository_size(root)
    assert result["revision"] == commit
    assert result["tracked_bytes"] == sum(map(len, contents.values()))
    assert result["tracked_file_count"] == len(contents)
    assert result["regular_file_count"] == len(contents)
    assert result["instruction_source_bytes"] == len(b"rules\nshim\noverlay\n")
    assert result["instruction_source_file_count"] == 3
    assert result["symlink_count"] == result["gitlink_count"] == 0
    assert scratch.read_bytes() == b"preserve me" * 100
    assert "not measured input tokens" in " ".join(result["notes"])


def test_selected_history_stays_fixed_and_logs_are_current_only(repo):
    root, contents = repo
    baseline = git(root, "rev-parse", "HEAD").decode()
    (root / "AGENTS.md").write_bytes(b"longer rules\n")
    git(root, "add", "AGENTS.md")
    git(root, "commit", "--no-gpg-sign", "-m", "new instruction bytes")
    log = root / "forseti-harness/memory/logs/efficiency/subdir/log.json"
    log.parent.mkdir(parents=True)
    log.write_bytes(b'{"run":1}')
    before = repository_size(root, baseline)
    after = repository_size(root)
    assert before["tracked_bytes"] == sum(map(len, contents.values()))
    assert after["tracked_bytes"] - before["tracked_bytes"] == len(b"longer rules\n") - len(b"rules\n")
    assert before["measurement_log_bytes"] == after["measurement_log_bytes"] == len(b'{"run":1}')
    assert before["measurement_log_file_count"] == after["measurement_log_file_count"] == 1
    assert log.read_bytes() == b'{"run":1}'
    assert git(root, "check-ignore", str(log))


def test_git_symlink_and_gitlink_are_explicit_without_following_them(repo):
    root, contents = repo
    head = git(root, "rev-parse", "HEAD").decode()
    blob = git(root, "hash-object", "-w", "--stdin", input=b"AGENTS.md").decode()
    # Index entries are portable even on Windows hosts without symlink creation privileges.
    git(root, "update-index", "--add", "--cacheinfo", f"120000,{blob},rules-link")
    git(root, "update-index", "--add", "--cacheinfo", f"160000,{head},external-submodule")
    git(root, "commit", "--no-gpg-sign", "-m", "special entries")
    result = repository_size(root)
    assert result["tracked_bytes"] == sum(map(len, contents.values())) + len(b"AGENTS.md")
    assert result["tracked_file_count"] == len(contents) + 1
    assert result["regular_file_count"] == len(contents)
    assert result["symlink_count"] == result["gitlink_count"] == 1
    assert result["symlink_blob_bytes"] == len(b"AGENTS.md")


def test_log_symlink_is_not_followed(repo, tmp_path):
    root, _ = repo
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "large.json").write_bytes(b"private" * 1000)
    logs = root / "forseti-harness/memory/logs/efficiency"
    logs.mkdir(parents=True)
    try:
        (logs / "outside-link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("host does not allow symlink creation")
    result = repository_size(root)
    assert result["measurement_log_bytes"] == result["measurement_log_file_count"] == 0
    assert result["measurement_log_symlink_count"] == 1
    assert (outside / "large.json").read_bytes() == b"private" * 1000


@pytest.mark.parametrize("revision", ["no-such-revision", "--all", "HEAD:AGENTS.md"])
def test_invalid_or_noncommit_revision_fails_loud(repo, revision):
    with pytest.raises(subprocess.CalledProcessError):
        repository_size(repo[0], revision)
