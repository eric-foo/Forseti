"""Keep CI and the local pre-push mirror mechanically aligned."""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PRE_PUSH_PATH = REPO_ROOT / ".agents" / "hooks" / "pre_push_guard.py"
HOOKS_DIR = REPO_ROOT / ".agents" / "hooks"
HARNESS_COUPLING_PATH = HOOKS_DIR / "check_harness_coupling.py"
CLAUDE_SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
CODEX_HOOKS_PATH = REPO_ROOT / ".codex" / "hooks.json"
CODEX_ADAPTER_PATH = REPO_ROOT / ".codex" / "hooks" / "forseti_guard_codex_adapter.py"
PLACEMENT_PATH = HOOKS_DIR / "check_placement.py"
ATOMIC_EXACT_EDIT_PATH = REPO_ROOT / ".agents" / "tools" / "atomic_exact_edit.py"
DECISION_ROUTING_PATH = REPO_ROOT / ".agents" / "workflow-overlay" / "decision-routing.md"
PROMPT_ORCHESTRATION_PATH = (
    REPO_ROOT / ".agents" / "workflow-overlay" / "prompt-orchestration.md"
)
PROMPT_GATE_PATH = REPO_ROOT / ".agents" / "hooks" / "check_prompt_output_mode.py"
HOOK_README_PATH = REPO_ROOT / ".agents" / "hooks" / "README.md"
HOOK_ADOPTION_ADOPTED = "FORSETI_CODEX_HOOK_ADOPTION=ADOPTED"
HOOK_ADOPTION_NOT_INTERCEPTED = "FORSETI_CODEX_HOOK_ADOPTION=NOT_INTERCEPTED"
EVENT_BASE_SHA = "1" * 40
DIFF_BASE_RESOLVERS = (
    ("check_source_input_hashes.py", "resolve_base_ref", False),
    ("check_placement.py", "resolve_base_ref", False),
    ("check_harness_coupling.py", "resolve_base_ref", False),
    ("header_index.py", "resolve_base_ref", True),
    ("check_search_surface_google_route.py", "resolve_base", False),
    ("check_csb_scanning_artifact.py", "resolve_base_ref", False),
    ("check_ontology_tag_validity.py", "resolve_base_ref", False),
    ("check_deletion_evidence.py", "resolve_base_ref", False),
    ("check_dcp_receipt.py", "resolve_base_ref", False),
    ("check_review_routing.py", "resolve_base_ref", False),
    ("check_handoff_pointers.py", "resolve_base_ref", False),
    ("check_prompt_output_mode.py", "resolve_base_ref", False),
    ("check_review_summary.py", "resolve_base_ref", False),
    ("check_hash_pin_freshness.py", "resolve_base_ref", False),
    ("check_shared_helper_duplication.py", "resolve_base_ref", False),
    ("check_full_gt_claims.py", "resolve_base_ref", False),
)


def _load_pre_push_guard():
    spec = importlib.util.spec_from_file_location("pre_push_guard", PRE_PUSH_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_harness_coupling():
    spec = importlib.util.spec_from_file_location("check_harness_coupling", HARNESS_COUPLING_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_prompt_gate():
    spec = importlib.util.spec_from_file_location("check_prompt_output_mode", PROMPT_GATE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_atomic_exact_edit():
    spec = importlib.util.spec_from_file_location("atomic_exact_edit", ATOMIC_EXACT_EDIT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the module resolves its PEP 563 dataclass
    # annotations through sys.modules[__module__] at class-creation time.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_codex_adapter():
    spec = importlib.util.spec_from_file_location(
        "forseti_guard_codex_adapter", CODEX_ADAPTER_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_placement():
    spec = importlib.util.spec_from_file_location("check_placement", PLACEMENT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ci_python_commands() -> list[str]:
    commands: list[str] = []
    for raw in CI_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("run: python "):
            commands.append(line.removeprefix("run: "))
        elif line.startswith("python "):
            commands.append(line)
    return commands


def test_ci_has_no_duplicate_python_commands() -> None:
    commands = _ci_python_commands()
    duplicates = sorted(command for command, count in Counter(commands).items() if count > 1)
    assert duplicates == []


def test_active_interactive_hook_topology_is_protection_only() -> None:
    claude = json.loads(CLAUDE_SETTINGS_PATH.read_text(encoding="utf-8"))["hooks"]
    assert set(claude) == {"PreToolUse", "SessionStart"}
    assert len(claude["PreToolUse"]) == 1
    claude_guard = claude["PreToolUse"][0]["hooks"]
    assert len(claude_guard) == 1
    assert "guard_protected_actions.py" in claude_guard[0]["command"]
    assert claude_guard[0]["timeout"] == 10
    session = claude["SessionStart"][0]["hooks"]
    assert len(session) == 1
    assert "session_context_capsule.py" in session[0]["command"]
    assert session[0]["timeout"] == 5

    codex = json.loads(CODEX_HOOKS_PATH.read_text(encoding="utf-8"))["hooks"]
    assert set(codex) == {"PreToolUse"}
    assert len(codex["PreToolUse"]) == 1
    codex_guard = codex["PreToolUse"][0]["hooks"]
    assert len(codex_guard) == 1
    assert "forseti_guard_codex_adapter.py" in codex_guard[0]["commandWindows"]
    assert codex_guard[0]["timeout"] == 10

    registered = CLAUDE_SETTINGS_PATH.read_text(encoding="utf-8") + CODEX_HOOKS_PATH.read_text(encoding="utf-8")
    for retired in (
        "remind_sci.py",
        "check_prompt_provenance.py",
        "check_shared_files_dirty.py",
        "check_token_burn.py",
        "check_placement.py",
        "check_repo_map_freshness.py",
        "check_search_surface_google_route.py",
    ):
        assert retired not in registered


def test_placement_ci_mode_is_registered_without_pre_push_expansion() -> None:
    command = "python .agents/hooks/check_placement.py --changed --strict"
    assert command in _ci_python_commands()
    guard = _load_pre_push_guard()
    assert all(command[0] != ".agents/hooks/check_placement.py" for _name, command in guard.SELECTED_GATES)


def test_placement_diff_parser_checks_rename_destination_and_ignores_deletion() -> None:
    placement = _load_placement()
    output = "\0".join(
        (
            "A", "docs/decisions/new.md",
            "M", "AGENTS.md",
            "C100", "docs/old.md", "docs/workflows/copied.md",
            "R087", "old-root.md", "mystery/new.md",
            "D", "docs/decisions/deleted.md",
            "",
        )
    )
    paths, error = placement.parse_name_status(output)
    assert error == ""
    assert paths == [
        "docs/decisions/new.md",
        "AGENTS.md",
        "docs/workflows/copied.md",
        "mystery/new.md",
    ]


def test_placement_changed_gate_covers_valid_unknown_and_freshness(
    monkeypatch, capsys
) -> None:
    placement = _load_placement()
    mapdata = {
        "known_top_level": {"dirs": ["docs"], "files": ["AGENTS.md"]},
        "docs_roles": [{"home": "docs/decisions"}],
        "scratch_rules": {},
        "legacy_tolerated": [],
        "excluded": [],
    }
    monkeypatch.setattr(placement, "load_map", lambda root: (mapdata, ""))
    monkeypatch.setattr(placement, "freshness_findings", lambda root, data: [])

    monkeypatch.setattr(
        placement,
        "changed_paths",
        lambda root, base: (["docs/decisions/new.md", "AGENTS.md"], ""),
    )
    assert placement.run_changed(REPO_ROOT, "base") == 0

    monkeypatch.setattr(
        placement,
        "changed_paths",
        lambda root, base: (["mystery/new.md", "docs/notarole/new.md"], ""),
    )
    assert placement.run_changed(REPO_ROOT, "base") == 1
    assert "unknown top-level area" in capsys.readouterr().out

    monkeypatch.setattr(placement, "changed_paths", lambda root, base: ([], ""))
    monkeypatch.setattr(
        placement,
        "freshness_findings",
        lambda root, data: ["map-stale: declared top-level dir missing from tree: docs"],
    )
    assert placement.run_changed(REPO_ROOT, "base") == 1


def test_placement_diff_uses_internal_twenty_second_timeout(monkeypatch) -> None:
    placement = _load_placement()

    def fake_run(command, **kwargs):
        assert kwargs["timeout"] == 20
        assert command[-1] == "abc123...HEAD"
        assert "--diff-filter=ACMR" in command
        return subprocess.CompletedProcess(command, 0, "M\0AGENTS.md\0", "")

    monkeypatch.setattr(placement.subprocess, "run", fake_run)
    paths, error = placement.changed_paths(REPO_ROOT, "abc123")
    assert (paths, error) == (["AGENTS.md"], "")


def test_codex_live_hook_adoption_probe_fails_closed() -> None:
    config = json.loads(CODEX_HOOKS_PATH.read_text(encoding="utf-8"))
    pre_tool = config["hooks"]["PreToolUse"]
    matching_entries = [
        entry
        for entry in pre_tool
        if {"Bash", "PowerShell"} <= set(entry["matcher"].split("|"))
    ]
    assert len(matching_entries) == 1
    configured_hook = matching_entries[0]["hooks"][0]
    assert "forseti_guard_codex_adapter.py" in configured_hook["commandWindows"]

    direct = subprocess.run(
        [sys.executable, str(CODEX_ADAPTER_PATH), "--live-adoption-probe"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert direct.returncode == 3
    assert direct.stderr.strip() == HOOK_ADOPTION_NOT_INTERCEPTED

    event = {
        "tool_name": "PowerShell",
        "tool_input": {
            "command": (
                "python .codex/hooks/forseti_guard_codex_adapter.py "
                "--live-adoption-probe"
            )
        },
    }
    intercepted = subprocess.run(
        [sys.executable, str(CODEX_ADAPTER_PATH)],
        cwd=REPO_ROOT,
        input=json.dumps(event),
        text=True,
        capture_output=True,
        timeout=10,
    )
    denial = json.loads(intercepted.stdout)
    assert intercepted.returncode == 0
    assert denial["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert (
        denial["hookSpecificOutput"]["permissionDecisionReason"]
        == HOOK_ADOPTION_ADOPTED
    )


def test_one_time_binding_preserves_guard_and_limits_canary() -> None:
    routing = DECISION_ROUTING_PATH.read_text(encoding="utf-8")
    hook_readme = HOOK_README_PATH.read_text(encoding="utf-8")
    adapter = CODEX_ADAPTER_PATH.read_text(encoding="utf-8")
    probe_command = (
        "python .codex/hooks/forseti_guard_codex_adapter.py "
        "--live-adoption-probe"
    )

    assert "## One-Time Writable-Root Binding" in routing
    assert "revision_mode: exact | ancestor" in routing
    assert "`HEAD` equals `required_revision`" in routing
    assert "git merge-base --is-ancestor <required_revision> HEAD" in routing
    assert "one effective target" in routing
    assert "Launch-root mismatch alone is not a blocker" in routing
    assert "ordinary work does not run it" in routing
    assert probe_command in hook_readme
    assert "only when hook adoption testing is itself" in hook_readme
    assert "_nested_worktree_reason" not in adapter
    assert "registered non-current worktree" not in adapter

    guard = _load_codex_adapter()
    other_target = REPO_ROOT.parent / "forseti-worktrees" / "other-lane" / "docs" / "x.md"
    patch_text = (
        "*** Begin Patch\n"
        f"*** Update File: {other_target}\n"
        "@@\n-old\n+new\n"
        "*** End Patch\n"
    )
    assert guard._check_apply_patch_paths({"command": patch_text}) == ""
    protected_target = Path.home() / ".codex" / "skills" / "x" / "SKILL.md"
    protected_patch = patch_text.replace(str(other_target), str(protected_target))
    assert "EP-01 protected-path write" in guard._check_apply_patch_paths(
        {"command": protected_patch}
    )
    shell_reason = guard._check_shell_durable_write(
        {"command": "Set-Content docs/x.md 'x'"}
    )
    assert "raw shell durable-write blocked" in shell_reason
    assert "created and rooted there" not in shell_reason

    direct = subprocess.run(
        [sys.executable, str(CODEX_ADAPTER_PATH)],
        cwd=REPO_ROOT,
        input=json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(protected_target)},
            }
        ),
        text=True,
        capture_output=True,
        timeout=10,
    )
    denial = json.loads(direct.stdout)
    assert direct.returncode == 0
    assert denial["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "EP-01 protected-path write" in denial["hookSpecificOutput"][
        "permissionDecisionReason"
    ]

def test_codex_apply_patch_guard_checks_all_payload_fields() -> None:
    guard = _load_codex_adapter()
    protected_target = Path.home() / ".codex" / "skills" / "x" / "SKILL.md"
    patch_text = f"""*** Begin Patch
*** Update File: {protected_target}
@@
-old
+new
*** End Patch
"""

    for payload_key in ("command", "patch", "input"):
        reason = guard._check_apply_patch_paths({payload_key: patch_text})
        assert "EP-01 protected-path write" in reason

    # Allow path: a benign repository target must pass through every payload
    # field, so a regression that denies all apply_patch calls cannot pass.
    benign_target = REPO_ROOT / "docs" / "x.md"
    benign_patch = patch_text.replace(str(protected_target), str(benign_target))
    for payload_key in ("command", "patch", "input"):
        assert guard._check_apply_patch_paths({payload_key: benign_patch}) == ""


def test_implementation_commission_authorizes_one_immediate_managed_reroot() -> None:
    routing = DECISION_ROUTING_PATH.read_text(encoding="utf-8")
    prompt_contract = PROMPT_ORCHESTRATION_PATH.read_text(encoding="utf-8")

    for required in (
        "receiver_creation_authorization:",
        "authorization: create_exactly_one_fresh_codex_managed_worktree_task",
        "condition: current_task_not_receiver_verified",
        "initial_prompt: this_frozen_commission_verbatim",
        "dispatch: immediate_same_turn",
        "current_turn_authorization: read_only_scoping_only",
    ):
        assert required in prompt_contract

    assert "already-authorized capable worktree-backed task" in routing
    assert "a task's mere existence is never authority" in routing
    assert "does not require launch-root equality" in routing
    assert "read-only/scoping/review work" in routing
    assert "Creating a user-visible Codex task still requires explicit product/user" in routing
    assert "do not create that authority" in routing


def test_managed_receiver_commission_gate_rejects_contradictions() -> None:
    gate = _load_prompt_gate()
    receiver = [
        "output_mode: paste-ready-chat",
        "edit_permission: implementation-authorized",
        "receiver_binding:",
        "  receiver_class: codex_managed_worktree",
        "  binding_state: receiver_to_verify",
        "  managed_starting_ref: origin/main",
        "  required_revision: 8cb44d080334453c384e39bc88fce510cbccfcde",
        "  revision_mode: ancestor",
    ]
    corrected_authorization = [
        "receiver_creation_authorization:",
        "  authorization: create_exactly_one_fresh_codex_managed_worktree_task",
        "  condition: current_task_not_receiver_verified",
        "  managed_starting_ref: origin/main",
        "  required_revision: 8cb44d080334453c384e39bc88fce510cbccfcde",
        "  revision_mode: ancestor",
        "  initial_prompt: this_frozen_commission_verbatim",
        "  dispatch: immediate_same_turn",
    ]

    defective = receiver + [
        "If this current task is not the receiver, stop; do not create another worktree.",
        "If the controlling prompt contract cannot be freshly loaded, fall back to project-owned prompt rules.",
    ]
    defective_findings = gate.evaluate_managed_receiver_lines("defective.md", defective)
    defective_kinds = {finding.kind for finding in defective_findings}
    assert "managed_receiver_creation_authorization_count" in defective_kinds
    assert "source_context_failure_not_typed" in defective_kinds
    assert "stale_source_fallback" in defective_kinds
    assert any("wrong-task stop" in finding.detail for finding in defective_findings)

    corrected = receiver + corrected_authorization + [
        "If a controlling source cannot be freshly loaded, declare SOURCE_CONTEXT_INCOMPLETE and stop.",
        "Do not manually create, discover, or target a Git worktree.",
        "Do not create a second receiver.",
    ]
    assert gate.evaluate_managed_receiver_lines("corrected.md", corrected) == []

    read_only = [line.replace("implementation-authorized", "read-only") for line in receiver]
    assert gate.evaluate_managed_receiver_lines("read_only.md", read_only) == []
    assert any(
        finding.kind == "receiver_creation_authority_on_read_only_commission"
        for finding in gate.evaluate_managed_receiver_lines(
            "read_only_bad.md", read_only + corrected_authorization
        )
    )

    manual = corrected + ["Run `git worktree add ../receiver origin/main` and continue there."]
    assert any(
        finding.kind == "manual_git_worktree_substitution"
        for finding in gate.evaluate_managed_receiver_lines("manual.md", manual)
    )

    mixed_clause_manual = corrected + [
        "Do not pause; run `git worktree add ../receiver origin/main` and continue there."
    ]
    assert any(
        finding.kind == "manual_git_worktree_substitution"
        for finding in gate.evaluate_managed_receiver_lines(
            "mixed_clause_manual.md", mixed_clause_manual
        )
    )

    mixed_clause_repeat = corrected + [
        "Do not wait; create another managed receiver task."
    ]
    assert any(
        finding.kind == "repeat_receiver_creation_authority"
        for finding in gate.evaluate_managed_receiver_lines(
            "mixed_clause_repeat.md", mixed_clause_repeat
        )
    )

    orphan_authorization = [
        "output_mode: paste-ready-chat",
        "edit_permission: implementation-authorized",
        *corrected_authorization,
    ]
    assert any(
        finding.kind == "managed_receiver_binding_count"
        for finding in gate.evaluate_managed_receiver_lines(
            "orphan_authorization.md", orphan_authorization
        )
    )

    conflicting_binding = corrected + [
        "receiver_binding:",
        "  receiver_class: codex_managed_worktree",
        "  binding_state: receiver_to_verify",
        "  managed_starting_ref: other/ref",
        "  required_revision: deadbeef",
        "  revision_mode: exact",
    ]
    assert any(
        finding.kind == "managed_receiver_binding_count"
        for finding in gate.evaluate_managed_receiver_lines(
            "conflicting_binding.md", conflicting_binding
        )
    )

    preparation_only_state = [
        line.replace("receiver_to_verify", "receiver_to_bind")
        for line in corrected
    ]
    assert any(
        finding.kind == "managed_receiver_binding_state"
        for finding in gate.evaluate_managed_receiver_lines(
            "preparation_only_state.md", preparation_only_state
        )
    )

    duplicate_authorization = corrected.copy()
    duplicate_authorization.insert(
        duplicate_authorization.index(
            "  authorization: create_exactly_one_fresh_codex_managed_worktree_task"
        ),
        "  authorization: create_many_tasks",
    )
    assert any(
        finding.kind == "managed_receiver_duplicate_field"
        for finding in gate.evaluate_managed_receiver_lines(
            "duplicate_authorization.md", duplicate_authorization
        )
    )

    broadened_authorization = corrected.copy()
    broadened_authorization.insert(
        broadened_authorization.index("  dispatch: immediate_same_turn") + 1,
        "  allow_repeat: true",
    )
    assert any(
        finding.kind == "managed_receiver_authorization_field"
        for finding in gate.evaluate_managed_receiver_lines(
            "broadened_authorization.md", broadened_authorization
        )
    )

    multiline_stale = corrected + [
        "If the controlling prompt contract cannot be freshly loaded,",
        "continue from remembered rules.",
    ]
    assert any(
        finding.kind == "stale_source_fallback"
        for finding in gate.evaluate_managed_receiver_lines(
            "multiline_stale.md", multiline_stale
        )
    )


def test_every_pre_push_gate_is_the_same_command_ci_runs() -> None:
    guard = _load_pre_push_guard()
    ci_commands = {
        command.replace('"$FORSETI_DIFF_BASE"', "origin/main")
        for command in _ci_python_commands()
    }
    mirrored = {
        "python " + " ".join((script, *args))
        for _name, (script, *args) in guard.SELECTED_GATES
    }
    assert mirrored <= ci_commands


def test_observed_fast_failure_classes_are_mirrored_pre_push() -> None:
    guard = _load_pre_push_guard()
    names = {name for name, _command in guard.SELECTED_GATES}
    assert {
        "prompt contract shape",
        "review-output provenance",
        "handoff-pointer resolution",
        "ontology tag validity",
        "harness coupling contracts",
    } <= names


def test_ci_derives_and_verifies_exact_event_base_sha() -> None:
    ci_text = CI_PATH.read_text(encoding="utf-8")
    assert "github.event.pull_request.base.sha" in ci_text
    assert "github.event.before" in ci_text
    assert '[[ "$FORSETI_DIFF_BASE" =~ ^0+$ ]]' in ci_text
    assert 'git cat-file -e "${FORSETI_DIFF_BASE}^{commit}"' in ci_text
    assert ci_text.count('--diff "$FORSETI_DIFF_BASE" --strict') == 3


def test_ci_uses_public_runner_cpu_capacity_without_splitting_test_files() -> None:
    ci_text = CI_PATH.read_text(encoding="utf-8")
    assert '"pytest-xdist==3.8.0"' in ci_text
    assert (
        "python -m pytest --durations=50 --durations-min=0.25 "
        "-n 4 --dist=loadfile"
    ) in ci_text


def test_harness_coupling_trigger_scope() -> None:
    coupling = _load_harness_coupling()
    assert coupling.path_triggers_gate("forseti-harness/src/forseti_harness/example.py")
    assert coupling.path_triggers_gate(
        "forseti-harness/data_lake/lake_touchpoint_inventory_v0.json"
    )
    assert not coupling.path_triggers_gate("forseti-harness/data_lake/other.json")
    assert not coupling.path_triggers_gate("docs/decisions/example.md")


def test_harness_coupling_preserves_pytest_failure() -> None:
    coupling = _load_harness_coupling()

    class FailedResult:
        returncode = 7

    def failed_runner(_command, *, cwd, timeout):
        assert cwd == REPO_ROOT / "forseti-harness"
        assert timeout == coupling.TIMEOUT_SECONDS
        return FailedResult()

    assert coupling.run_contracts(REPO_ROOT, runner=failed_runner) == 7


def test_harness_coupling_fails_closed_on_unresolvable_diff_base(
    monkeypatch, capsys
) -> None:
    coupling = _load_harness_coupling()
    zero_sha = "0" * 40
    monkeypatch.setattr(coupling, "resolve_base_ref", lambda _base=None: zero_sha)

    assert coupling.main(["--strict"]) == 2
    captured = capsys.readouterr()
    assert "GATE FAIL harness coupling contracts" in captured.err
    assert f"{zero_sha}...HEAD" in captured.err


def test_event_base_sha_precedes_github_branch_and_cli(
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(HOOKS_DIR))
    monkeypatch.setenv("FORSETI_DIFF_BASE", EVENT_BASE_SHA)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")

    for filename, function_name, needs_root in DIFF_BASE_RESOLVERS:
        module = importlib.import_module(Path(filename).stem)
        resolver = getattr(module, function_name)
        args = (REPO_ROOT, "cli-base") if needs_root else ("cli-base",)
        assert resolver(*args) == EVENT_BASE_SHA, filename


def test_github_pr_base_precedes_cli_when_event_sha_absent(
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(HOOKS_DIR))
    monkeypatch.delenv("FORSETI_DIFF_BASE", raising=False)
    monkeypatch.setenv("GITHUB_BASE_REF", "develop")

    for filename, function_name, needs_root in DIFF_BASE_RESOLVERS:
        module = importlib.import_module(Path(filename).stem)
        resolver = getattr(module, function_name)
        args = (REPO_ROOT, "cli-base") if needs_root else ("cli-base",)
        assert resolver(*args) == "origin/develop", filename


def test_atomic_exact_edit_recovers_after_hard_exit(tmp_path: Path, monkeypatch) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"alpha\n")
    second.write_bytes(b"bravo\n")
    command = [
        sys.executable,
        str(ATOMIC_EXACT_EDIT_PATH),
        "--root",
        str(tmp_path),
        "--replace",
        "first.txt",
        "alpha",
        "changed-alpha",
        "--replace",
        "second.txt",
        "bravo",
        "changed-bravo",
        "--apply",
    ]
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS", "1")
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES", "1")
    crashed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert crashed.returncode == 86
    assert first.read_bytes() == b"changed-alpha\n"
    assert second.read_bytes() == b"bravo\n"
    journal = tmp_path / ".atomic_exact_edit_journal_v1.json"
    assert journal.is_file()

    monkeypatch.delenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS")
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES")
    recovered = subprocess.run(
        [sys.executable, str(ATOMIC_EXACT_EDIT_PATH), "--root", str(tmp_path), "--recover"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert recovered.returncode == 0
    assert "RECOVERY=ROLLED_BACK_INTERRUPTED_APPLY" in recovered.stdout
    assert first.read_bytes() == b"alpha\n"
    assert second.read_bytes() == b"bravo\n"
    assert not journal.exists()

    monkeypatch.setenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS", "1")
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES", "1")
    assert subprocess.run(command, capture_output=True, check=False).returncode == 86
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS")
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES")
    first.write_bytes(b"third-party-state\n")
    refused = subprocess.run(
        [sys.executable, str(ATOMIC_EXACT_EDIT_PATH), "--root", str(tmp_path), "--recover"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 1
    assert "match neither" in refused.stderr
    assert first.read_bytes() == b"third-party-state\n"
    assert journal.is_file()


def test_atomic_exact_edit_finalizes_commit_after_hard_exit(
    tmp_path: Path, monkeypatch
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"alpha\n")
    second.write_bytes(b"bravo\n")
    command = [
        sys.executable,
        str(ATOMIC_EXACT_EDIT_PATH),
        "--root",
        str(tmp_path),
        "--replace",
        "first.txt",
        "alpha",
        "changed-alpha",
        "--replace",
        "second.txt",
        "bravo",
        "changed-bravo",
        "--apply",
    ]
    # Crash after the committed journal write but before journal cleanup.
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS", "1")
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES", "3")
    crashed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert crashed.returncode == 86
    assert first.read_bytes() == b"changed-alpha\n"
    assert second.read_bytes() == b"changed-bravo\n"
    journal = tmp_path / ".atomic_exact_edit_journal_v1.json"
    assert journal.is_file()

    monkeypatch.delenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS")
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES")
    recovered = subprocess.run(
        [sys.executable, str(ATOMIC_EXACT_EDIT_PATH), "--root", str(tmp_path), "--recover"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert recovered.returncode == 0
    assert "RECOVERY=FINALIZED_COMMIT" in recovered.stdout
    assert first.read_bytes() == b"changed-alpha\n"
    assert second.read_bytes() == b"changed-bravo\n"
    assert not journal.exists()


def test_atomic_exact_edit_lock_excludes_concurrent_invocations(
    tmp_path: Path, monkeypatch
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"alpha\n")
    second.write_bytes(b"bravo\n")
    command = [
        sys.executable,
        str(ATOMIC_EXACT_EDIT_PATH),
        "--root",
        str(tmp_path),
        "--replace",
        "first.txt",
        "alpha",
        "changed-alpha",
        "--replace",
        "second.txt",
        "bravo",
        "changed-bravo",
        "--apply",
    ]
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS", "1")
    monkeypatch.setenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES", "1")
    assert subprocess.run(command, capture_output=True, check=False).returncode == 86
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_ENABLE_TEST_FAULTS")
    monkeypatch.delenv("ATOMIC_EXACT_EDIT_TEST_CRASH_AFTER_REPLACES")
    journal = tmp_path / ".atomic_exact_edit_journal_v1.json"
    assert journal.is_file()

    module = _load_atomic_exact_edit()
    lock_path = module._lock_path(tmp_path)
    assert lock_path.parent != tmp_path
    assert module._lock_path(tmp_path) == lock_path
    assert not (tmp_path / ".atomic_exact_edit_journal_v1.lock").exists()
    lock = module._acquire_lock(tmp_path)
    try:
        # While a live invocation holds the lock, a second recover or apply
        # must fail loudly instead of rolling back the live transaction.
        for blocked_command in (
            [sys.executable, str(ATOMIC_EXACT_EDIT_PATH), "--root", str(tmp_path), "--recover"],
            command,
        ):
            blocked = subprocess.run(
                blocked_command, capture_output=True, text=True, check=False
            )
            assert blocked.returncode == 1
            assert "holds the transaction lock" in blocked.stderr
            assert first.read_bytes() == b"changed-alpha\n"
            assert second.read_bytes() == b"bravo\n"
            assert journal.is_file()
    finally:
        module._release_lock(lock)

    recovered = subprocess.run(
        [sys.executable, str(ATOMIC_EXACT_EDIT_PATH), "--root", str(tmp_path), "--recover"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert recovered.returncode == 0
    assert "RECOVERY=ROLLED_BACK_INTERRUPTED_APPLY" in recovered.stdout
    assert first.read_bytes() == b"alpha\n"
    assert second.read_bytes() == b"bravo\n"
    assert not journal.exists()


def test_external_actions_are_sha_pinned_and_renovate_managed() -> None:
    ci_text = CI_PATH.read_text(encoding="utf-8")
    uses = re.findall(r"^\s*- uses: (.+)$", ci_text, flags=re.MULTILINE)
    assert uses
    for use in uses:
        assert re.fullmatch(r"[^@]+@[0-9a-f]{40}\s+#\s+v\d+(?:\.\d+){0,2}", use), use

    renovate = json.loads((REPO_ROOT / "renovate.json").read_text(encoding="utf-8"))
    assert "github-actions" in renovate.get("enabledManagers", [])

    # A blanket wildcard packageRule can silently re-disable every manager it
    # does not carve back out; assert a later rule actually re-enables the
    # github-actions manager instead of just declaring it in enabledManagers.
    rules = renovate.get("packageRules", [])
    reenabled_at = None
    for index, rule in enumerate(rules):
        if rule.get("enabled") is True and "github-actions" in rule.get("matchManagers", []):
            reenabled_at = index
    assert reenabled_at is not None, "no packageRule re-enables the github-actions manager"

    disabled_wildcard_indexes = [
        index
        for index, rule in enumerate(rules)
        if rule.get("enabled") is False and rule.get("matchPackageNames") == ["*"]
    ]
    assert disabled_wildcard_indexes, "expected the blanket wildcard disable rule to still exist"
    assert reenabled_at > max(disabled_wildcard_indexes), (
        "github-actions re-enable rule must come after the blanket wildcard disable "
        "(Renovate packageRules merge in array order; an earlier re-enable would be "
        "overridden by the later blanket disable)"
    )
