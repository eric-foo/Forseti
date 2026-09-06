"""The silver-lane write-path guard enforces the no-blur binding.

Runs the guard's own selftest (its pass/fail fixtures), proves the live repo has
no silver-lane write violations, and pins the registry's load-bearing facts (the
envelope lanes and the named FRONT_DOOR_PENDING baseline). Also pins the
hardening invariants: strict mode fails unresolvable lanes, conflicting aliases
stay unresolved, and the front-door exemption is scoped to append_silver_record.
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".agents" / "hooks" / "check_silver_lane_registry.py"
REGISTRY_PATH = REPO_ROOT / "forseti-harness" / "data_lake" / "lane_registry.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # register so @dataclass can resolve cls.__module__
    spec.loader.exec_module(module)
    return module


def _load_registry():
    return _load_module("lane_registry_under_test", REGISTRY_PATH)


def _load_hook():
    return _load_module("silver_lane_guard_under_test", HOOK)


def test_guard_selftest_passes() -> None:
    result = _run("--selftest", "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SELFTEST OK" in result.stdout


def test_live_repo_has_no_silver_lane_write_violations() -> None:
    result = _run("--strict")
    assert result.returncode == 0, result.stdout + result.stderr


def test_producer_discovery_ignores_generated_test_scratch(tmp_path: Path) -> None:
    guard = _load_hook()
    harness = tmp_path / "forseti-harness"
    production = harness / "source_capture" / "producer.py"
    generated = harness / "_test_runs" / "run_123" / "copied_producer.py"
    scratch = harness / "_scratch" / "probe" / "scratch_producer.py"
    for path in (production, generated, scratch):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def produce():\n    return None\n", encoding="utf-8")

    discovered = guard._producer_files(tmp_path)

    assert discovered == [production]


def test_generated_install_copies_are_pruned_but_new_source_still_fails(tmp_path, monkeypatch):
    guard = _load_hook()
    harness = tmp_path / "forseti-harness"
    source = harness / "new_producer.py"
    nested_source = harness / "package" / "build" / "producer.py"
    generated = [harness / ".venv" / "lib" / "producer.py",
                 harness / "build" / "lib" / "producer.py"]
    for path in [source, nested_source, *generated]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("root.append_record(lane='silver__seeded_bypass')\n", encoding="utf-8")
    real_walk = guard.os.walk
    visited = []

    def observed_walk(*args, **kwargs):
        for row in real_walk(*args, **kwargs):
            visited.append(Path(row[0]))
            yield row

    monkeypatch.setattr(guard.os, "walk", observed_walk)
    discovered = guard._producer_files(tmp_path)
    assert discovered == sorted([source, nested_source])
    assert not any(path.is_relative_to(harness / name)
                   for path in visited for name in (".venv", "build"))
    findings, _ = guard.scan(tmp_path, discovered, _load_registry())
    assert len(findings) == 2
    assert all(f.code == "undeclared_silver_lane" for f in findings)


def test_discovery_prunes_before_descent_and_preserves_sorted_membership(tmp_path, monkeypatch):
    guard = _load_hook()
    harness = tmp_path / "forseti-harness"
    for name in ("z.py", "package/a.py", "package/case.PY", "package/test_runs_allowed.py",
                 "_scratch/deep/hidden.py", "package/tests/deep/hidden.py",
                 "__pycache__/deep/hidden.py", "_test_runs/deep/hidden.py"):
        path = harness / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass\n", encoding="utf-8")
    # rglob also admits matching directory names; keep that membership unchanged.
    (harness / "directory.py").mkdir()
    expected = [path for path in sorted(harness.rglob("*.py"))
                if not set(path.relative_to(harness).parts).intersection(
                    guard._PRODUCER_DISCOVERY_EXCLUDED_DIRS)]
    real_walk = guard.os.walk
    visited = []

    def observed_walk(*args, **kwargs):
        for dirpath, dirnames, filenames in real_walk(*args, **kwargs):
            visited.append(Path(dirpath))
            yield dirpath, dirnames, filenames

    monkeypatch.setattr(guard.os, "walk", observed_walk)
    assert guard._producer_files(tmp_path) == expected
    assert visited
    assert all(not set(path.relative_to(harness).parts).intersection(
        guard._PRODUCER_DISCOVERY_EXCLUDED_DIRS) for path in visited)




def test_strict_mode_fails_unresolved_lane_arguments() -> None:
    result = _run(
        "--strict",
        "forseti-harness/tests/fixtures/silver_lane_guard/fail_unresolved_lane_strict.py",
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "unresolved_lane_argument" in result.stdout


def test_strict_mode_notes_dynamic_members_without_failing() -> None:
    # A dynamic members dict is a coverage NOTE, not a strict failure: legitimate
    # record-set producers (e.g. the ecr deriver) build members dynamically.
    result = _run(
        "--strict",
        "forseti-harness/tests/fixtures/silver_lane_guard/note_unresolved_members.py",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "not statically resolved" in result.stdout
    assert "unresolved_lane_argument" not in result.stdout


def test_alias_constant_conflicts_are_unresolved() -> None:
    guard = _load_hook()
    parsed = {
        Path("a.py"): ast.parse('LANE_A = "cleaning_fragrantica_silver"\nLANE = LANE_A\n'),
        Path("b.py"): ast.parse('LANE_B = "projection_ig"\nLANE = LANE_B\n'),
    }
    consts = guard._build_global_consts(parsed)
    assert "LANE" not in consts


def test_front_door_exemption_is_limited_to_validating_front_door_functions() -> None:
    guard = _load_hook()
    registry = _load_registry()
    tree = ast.parse(
        "def append_silver_record(data_root, lane):\n"
        "    data_root.append_record(lane=lane)\n"
        "\n"
        "def append_silver_record_set(data_root, lane):\n"
        "    data_root.append_record_set(members={lane: b'x'}, completion_lane='done')\n"
        "\n"
        "def other_helper(data_root):\n"
        '    data_root.append_record(lane="cleaning_fragrantica_silver")\n'
    )
    findings, unresolved = guard._scan_tree(
        registry.SILVER_ENVELOPE_FRONT_DOOR_MODULE,
        tree,
        {},
        registry,
        is_front_door_module=True,
    )
    # Both validating front doors are exempt (not flagged unresolved);
    # a sibling raw writer in the same module is NOT exempt.
    assert not unresolved
    assert [finding.code for finding in findings] == ["envelope_lane_bypass"]


def test_ack_subtree_exemption_is_static_and_subtree_scoped() -> None:
    # The consumption-seam exemption: a write whose subtree STATICALLY resolves to
    # "acknowledgements" is an ack record, not a silver record — even with a dynamic
    # lane (the shared helper's ack_namespace parameter) or an envelope lane NAME as
    # the ack namespace. The same write under derived/ keeps full scrutiny.
    guard = _load_hook()
    registry = _load_registry()
    tree = ast.parse(
        '_ACK_SUBTREE = "acknowledgements"\n'
        "\n"
        "def append_ack(data_root, ack_namespace):\n"
        "    data_root.append_record(subtree=_ACK_SUBTREE, lane=ack_namespace)\n"
        "\n"
        "def ack_envelope_name(data_root):\n"
        '    data_root.append_record(subtree="acknowledgements", lane="cleaning_fragrantica_silver")\n'
        "\n"
        "def derived_bypass(data_root):\n"
        '    data_root.append_record(subtree="derived", lane="cleaning_fragrantica_silver")\n'
        "\n"
        "def derived_dynamic(data_root, lane):\n"
        '    data_root.append_record(subtree="derived", lane=lane)\n'
    )
    consts = guard._build_global_consts({Path("consumption.py"): tree})
    findings, unresolved = guard._scan_tree(
        "consumption.py", tree, consts, registry, is_front_door_module=False
    )
    # only the derived/ writes are scrutinized: one resolved bypass, one strict gap.
    assert [finding.code for finding in findings] == ["envelope_lane_bypass"]
    assert [(item.lineno, item.excerpt) for item in unresolved] == [(13, "lane")]


def test_registry_pins_envelope_lanes_and_pending_baseline() -> None:
    registry = _load_registry()
    assert "cleaning_fragrantica_silver" in registry.SILVER_ENVELOPE_LANES
    # FRONT_DOOR_PENDING is EMPTY since the Batch-3 creator-metric migration: every
    # silver_envelope lane now writes through the validating front-door, so nothing is
    # exempt. The exact-set check (pending == baseline) still guards a silent re-add.
    assert registry.FRONT_DOOR_PENDING == {}
    assert set(registry.FRONT_DOOR_PENDING_BASELINE) == set()
    assert registry.validate_registry() == []
    assert all(reason.strip() for reason in registry.FRONT_DOOR_PENDING.values())
    # The creator-metric lanes are real envelope lanes but are NOT pending (migrated).
    assert "creator_metric_silver" in registry.SILVER_ENVELOPE_LANES
    assert "creator_metric_silver" not in registry.FRONT_DOOR_PENDING
    # Every pending lane (none) is a real envelope lane.
    assert set(registry.FRONT_DOOR_PENDING) <= set(registry.SILVER_ENVELOPE_LANES)


def test_registry_freezes_legacy_lineage_lanes() -> None:
    registry = _load_registry()
    assert registry.SILVER_LINEAGE_LANES == registry.SILVER_LINEAGE_LEGACY_BASELINE
    assert registry.SILVER_LINEAGE_LANES == set()
    assert {
        "silver__capture__audience_comments",
        "silver__capture__reel_transcript",
    } <= registry.SILVER_ENVELOPE_LANES
    assert registry.LANE_ROLES["silver__capture__reel_deep_capture__set"] is registry.LaneRole.COMPLETION_MARKER
    assert {
        lane
        for lane, role in registry.LANE_ROLES.items()
        if role is registry.LaneRole.RETIRED_SILVER_LINEAGE
    } == registry.RETIRED_SILVER_LINEAGE_BASELINE
    assert {
        "transcript_product_mentions_silver",
    } <= registry.SILVER_ENVELOPE_LANES
    assert {
        "tiktok_audience_evidence_completion",
        "tiktok_audience_profile_analysis",
        "tiktok_audience_profile_analysis_completion",
    } == registry.RETIRED_LANE_BASELINE

    registry.LANE_ROLES["silver__new_legacy_bypass"] = registry.LaneRole.SILVER_LINEAGE
    try:
        assert any(
            "SILVER_LINEAGE lanes drifted" in error for error in registry.validate_registry()
        )
    finally:
        del registry.LANE_ROLES["silver__new_legacy_bypass"]
