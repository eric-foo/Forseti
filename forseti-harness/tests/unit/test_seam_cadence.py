"""Offline behavioral tests for the seam cadence runner (executable completion signal).

No network, no credentials, no ASR compute. Commits real packets into a temp
lake and asserts the cadence contract: cycle 1 drains the backlog, cycle 2 must
emit nothing, the final pending sweep must be zero (exit 0 = the bronze
completion signal), failures re-surface and fail the exit code, a skipped ASR
lane stays loud every cycle, and one broken entrypoint never silently aborts the
rest.
"""
from __future__ import annotations

import dataclasses
from contextlib import nullcontext
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from data_lake.root import DataLakeRoot, DataLakeRootUnavailableError
from runners import run_asr_transcript_catchup as asr_runner
from runners import run_seam_cadence as cadence
from runners.run_seam_cadence import CadenceContext, main, run_cadence, run_check
from source_capture.models import known_fact
from source_capture.writer import write_local_source_capture_packet


def _commit_packet(data_root, tmp_path: Path, name: str = "thread") -> str:
    src = tmp_path / f"{name}.json"
    src.write_text(json.dumps({"body": f"a reddit thread: {name}"}), encoding="utf-8")
    return write_local_source_capture_packet(
        data_root=data_root,
        input_files=[src],
        source_family="reddit",
        source_surface="r/test",
        source_locator=known_fact(f"https://www.reddit.com/r/test/comments/{name}/"),
        decision_question="q",
        capture_context="seam cadence test",
    ).packet.packet_id


def _ctx(data_root) -> CadenceContext:
    return CadenceContext(
        data_root=data_root,
        transcriber_policy=asr_runner.default_transcriber_policy(
            model_name="small", compute_type="int8"
        ),
        asr_model="small",
        asr_compute_type="int8",
    )


def _lake_tree_state(data_root) -> dict[str, str]:
    return {
        str(p.relative_to(data_root.path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(data_root.path.rglob("*"))
        if p.is_file()
    }


def _corrupt_manifest(data_root, packet_id: str) -> None:
    container = data_root.find_packet(packet_id)
    assert container is not None
    (container / "manifest.json").write_text("{not-json\n", encoding="utf-8")


def _output_lines(capsys) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]


def test_structured_output_forces_an_immediate_flush(monkeypatch) -> None:
    observed: list[tuple[tuple, dict]] = []
    monkeypatch.setattr(
        "builtins.print", lambda *args, **kwargs: observed.append((args, kwargs))
    )

    cadence._print({"status": "probe"})

    assert observed[0][1]["flush"] is True


def test_progress_precedes_work_and_terminal_events_are_timed(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    observed: list[dict] = []

    def run(_ctx, _scope) -> list:
        visible = _output_lines(capsys)
        observed.extend(visible)
        assert visible[-1]["status"] == "entrypoint_started"
        return []

    monkeypatch.setattr(
        cadence,
        "CADENCE_ENTRYPOINTS",
        (
            cadence.CadenceEntrypoint(
                runner="probe.py", pending=lambda _ctx, _scope: 0, run=run
            ),
        ),
    )

    assert run_cadence(_ctx(data_root), skip_asr=False) == 0
    observed.extend(_output_lines(capsys))

    assert observed[0]["phase"] == "snapshot"
    assert observed[0]["status"] == "phase_started"
    terminals = [
        line
        for line in observed
        if line.get("status") in {"phase_completed", "entrypoint_completed"}
    ]
    assert terminals
    assert all(line["elapsed_seconds"] >= 0 for line in terminals)
    assert {
        "snapshot",
        "cycle_1",
        "cycle_2",
        "post_cycle_pending_sweep",
        "late_arrival_check",
    }.issubset({line.get("phase") for line in observed})


def test_cadence_reconciles_once_and_all_composed_calls_reuse_snapshot(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    reconcile_calls: list[tuple[object, tuple[str, ...]]] = []
    monkeypatch.setattr(
        cadence,
        "reconcile_availability_per_packet",
        lambda root, *, scope_packet_ids: reconcile_calls.append(
            (root, tuple(scope_packet_ids))
        )
        or [],
    )
    monkeypatch.setattr(cadence, "_asr_transcribe_fn", lambda _ctx: nullcontext(object()))

    modules = (
        cadence._ecr,
        cadence._fragrantica,
        cadence._basenotes,
        cadence._parfumo,
        cadence._fragrance_review,
        cadence._ig_reels_grid,
        cadence._tiktok_comment_attention,
        cadence._tiktok_grid_observation,
        cadence._asr,
    )
    calls: dict[object, dict[str, list[dict]]] = {
        module: {"run": [], "pending": []} for module in modules
    }
    for module in modules:
        monkeypatch.setattr(
            module,
            "run_catchup",
            lambda _module=module, **kwargs: calls[_module]["run"].append(kwargs) or [],
        )
        monkeypatch.setattr(
            module,
            "pending_packets",
            lambda _module=module, **kwargs: calls[_module]["pending"].append(kwargs)
            or [],
        )

    assert run_cadence(_ctx(data_root), skip_asr=False) == 0

    assert reconcile_calls == [(data_root, ())]
    for module in modules:
        assert len(calls[module]["run"]) == 2
        assert len(calls[module]["pending"]) == 1
        assert all(
            call["reconcile_availability"] is False
            for call in calls[module]["run"] + calls[module]["pending"]
        )
    events = _output_lines(capsys)
    terminals = [
        event
        for event in events
        if event.get("phase") == "availability_reconcile"
        and event.get("status") == "phase_completed"
    ]
    assert len(terminals) == 1
    assert terminals[0]["failure_count"] == 0
    assert terminals[0]["elapsed_seconds"] >= 0


def test_check_reconciles_once_and_all_pending_calls_reuse_snapshot(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    reconcile_calls = []
    monkeypatch.setattr(
        cadence,
        "reconcile_availability_per_packet",
        lambda root, *, scope_packet_ids: reconcile_calls.append(
            (root, tuple(scope_packet_ids))
        )
        or [],
    )
    calls = []
    monkeypatch.setattr(
        cadence,
        "CADENCE_ENTRYPOINTS",
        tuple(
            dataclasses.replace(
                entrypoint,
                pending=lambda _ctx, _scope, _runner=entrypoint.runner: calls.append(
                    _runner
                )
                or 0,
            )
            for entrypoint in cadence.CADENCE_ENTRYPOINTS
        ),
    )

    assert run_check(_ctx(data_root)) == 0

    assert reconcile_calls == [(data_root, ())]
    assert calls == [entrypoint.runner for entrypoint in cadence.CADENCE_ENTRYPOINTS]
    assert any(
        event.get("phase") == "availability_reconcile"
        and event.get("status") == "phase_completed"
        for event in _output_lines(capsys)
    )


def test_all_standalone_cadence_runners_default_to_reconcile_first() -> None:
    modules = (
        cadence._ecr,
        cadence._fragrantica,
        cadence._basenotes,
        cadence._parfumo,
        cadence._fragrance_review,
        cadence._ig_reels_grid,
        cadence._tiktok_comment_attention,
        cadence._tiktok_grid_observation,
        cadence._asr,
    )
    for module in modules:
        assert (
            inspect.signature(module.run_catchup)
            .parameters["reconcile_availability"]
            .default
            is True
        )
        assert (
            inspect.signature(module.pending_packets)
            .parameters["reconcile_availability"]
            .default
            is True
        )


def test_root_loss_during_shared_reconcile_aborts_before_all_lanes(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    calls = []
    monkeypatch.setattr(
        cadence,
        "reconcile_availability_per_packet",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            DataLakeRootUnavailableError("verified lake root disappeared")
        ),
    )
    monkeypatch.setattr(
        cadence,
        "CADENCE_ENTRYPOINTS",
        (
            cadence.CadenceEntrypoint(
                runner="never.py",
                pending=lambda _ctx, _scope: calls.append("pending") or 0,
                run=lambda _ctx, _scope: calls.append("run") or [],
            ),
        ),
    )

    assert run_cadence(_ctx(data_root), skip_asr=False) == 1
    assert calls == []
    aborts = [
        event
        for event in _output_lines(capsys)
        if event.get("status") == "cadence_aborted_root_unavailable"
    ]
    assert len(aborts) == 1
    assert aborts[0]["entrypoint"] == "availability_reconcile"
    assert aborts[0]["skipped_entrypoint_runs"] == 2
    assert aborts[0]["post_cycle_pending_skipped"] is True


def test_backlog_drains_in_cycle_one_and_second_cycle_is_zero(tmp_path, capsys) -> None:
    # The completion signal: cycle 1 may work; cycle 2 must emit nothing beyond
    # the sanctioned skip markers -> exit 0.
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(data_root, tmp_path)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    lines = _output_lines(capsys)

    cycle1_work = [
        l for l in lines if l["cycle"] == 1 and l.get("status") != "skipped_asr_compute"
    ]
    assert [(l["entrypoint"], l["packet_id"], l["status"]) for l in cycle1_work] == [
        ("run_ecr_catchup.py", pid, "derived")
    ]

    cycle2 = [l for l in lines if l["cycle"] == 2]
    assert all(l["status"] == "skipped_asr_compute" for l in cycle2)

    # A skipped lane stays loud EVERY cycle, carrying its pending count.
    markers = [l for l in lines if l.get("status") == "skipped_asr_compute"]
    assert [(l["cycle"], l["entrypoint"], l["pending"]) for l in markers] == [
        (1, "run_asr_transcript_catchup.py", 0),
        (2, "run_asr_transcript_catchup.py", 0),
    ]

    # A caught-up lake keeps passing byte-unchanged (idempotent signal).
    before = _lake_tree_state(data_root)
    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    assert _lake_tree_state(data_root) == before


def test_packet_committed_between_cycles_waits_for_next_snapshot(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    starting = _commit_packet(data_root, tmp_path, "starting")
    late: list[str] = []
    original_run = cadence._ecr.run_catchup

    def commit_after_first_ecr_run(**kwargs):  # noqa: ANN003
        results = original_run(**kwargs)
        if not late:
            late.append(_commit_packet(data_root, tmp_path, "late"))
        return results

    monkeypatch.setattr(cadence._ecr, "run_catchup", commit_after_first_ecr_run)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    lines = _output_lines(capsys)
    assert [
        (line["packet_id"], line["status"])
        for line in lines
        if line.get("entrypoint") == "run_ecr_catchup.py"
        and line.get("status") == "derived"
    ] == [(starting, "derived")]
    assert [
        line["packet_ids"]
        for line in lines
        if line.get("status") == "late_arrivals_observed"
    ] == [late]
    assert cadence._ecr.pending_packets(data_root=data_root) == late

    monkeypatch.setattr(cadence._ecr, "run_catchup", original_run)
    capsys.readouterr()
    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    assert any(
        line.get("packet_id") == late[0] and line.get("status") == "derived"
        for line in _output_lines(capsys)
    )


def test_undrainable_work_fails_the_signal(tmp_path, capsys) -> None:
    # A corrupt committed anchor enters the read-only snapshot, then scoped
    # reconciliation fails it loudly before the consumer can derive from it.
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(data_root, tmp_path)
    _corrupt_manifest(data_root, pid)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    lines = _output_lines(capsys)
    assert any(line.get("status") == "cadence_snapshot_started" for line in lines)
    failures = [
        line
        for line in lines
        if line.get("packet_id") == pid
        and line.get("status") == "availability_reconcile_failed"
    ]
    assert failures
    assert all(failure["error"] for failure in failures)


def test_snapshot_capture_never_rebuilds_shared_availability(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(data_root, tmp_path)

    def fail_global_rebuild() -> None:
        raise AssertionError("global rebuild called")

    monkeypatch.setattr(data_root, "rebuild_availability", fail_global_rebuild)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    lines = _output_lines(capsys)
    assert [
        line["status"] for line in lines if line.get("cycle") == "snapshot"
    ] == ["cadence_snapshot_started"]
    assert [
        (line["entrypoint"], line["packet_id"], line["status"])
        for line in lines
        if line.get("cycle") == 1 and line.get("status") != "skipped_asr_compute"
    ] == [("run_ecr_catchup.py", pid, "derived")]


def test_availability_disappearance_after_shared_reconcile_fails_cadence(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(data_root, tmp_path, "transient-availability")
    original_reconcile = cadence._reconcile_start_snapshot

    def reconcile_then_remove(ctx, scope_packet_ids):  # noqa: ANN001
        reconciled = original_reconcile(ctx, scope_packet_ids)
        assert reconciled
        (
            data_root.path / "indexes" / "availability" / f"{selected}.json"
        ).unlink()
        return True

    monkeypatch.setattr(cadence, "_reconcile_start_snapshot", reconcile_then_remove)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    failures = [
        line
        for line in _output_lines(capsys)
        if line.get("status")
        in {
            "entrypoint_failed",
            "skipped_asr_pending_check_failed",
            "post_cycle_pending_check_failed",
        }
    ]
    assert failures
    assert all(
        "scoped packet is missing from public availability" in line["error"]
        for line in failures
    )


def test_next_cadence_reconcile_catches_corruption_after_prior_run(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(data_root, tmp_path, "selected")
    original_run = cadence._ecr.run_catchup
    corrupted = False

    def corrupt_after_first_ecr_run(**kwargs):  # noqa: ANN003
        nonlocal corrupted
        results = original_run(**kwargs)
        if not corrupted:
            _corrupt_manifest(data_root, selected)
            corrupted = True
        return results

    monkeypatch.setattr(cadence._ecr, "run_catchup", corrupt_after_first_ecr_run)

    # The shared view is intentionally fixed after its one pre-cycle reconcile.
    assert run_cadence(_ctx(data_root), skip_asr=True) == 0

    monkeypatch.setattr(cadence._ecr, "run_catchup", original_run)
    capsys.readouterr()
    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    failures = [
        line
        for line in _output_lines(capsys)
        if line.get("packet_id") == selected
        and line.get("status") == "availability_reconcile_failed"
    ]
    assert len(failures) == 1
    assert failures[0]["entrypoint"] == "availability_reconcile"


def test_check_reports_per_entrypoint_backlog(tmp_path, capsys) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    _commit_packet(data_root, tmp_path)

    assert run_check(_ctx(data_root)) == 1
    by_entrypoint = {
        l["entrypoint"]: l["pending"]
        for l in _output_lines(capsys)
        if "entrypoint" in l and "status" not in l
    }
    assert len(by_entrypoint) == len(cadence.CADENCE_ENTRYPOINTS)
    assert by_entrypoint["run_ecr_catchup.py"] == 1
    assert all(
        count == 0
        for name, count in by_entrypoint.items()
        if name != "run_ecr_catchup.py"
    )

    assert run_cadence(_ctx(data_root), skip_asr=True) == 0
    capsys.readouterr()
    assert run_check(_ctx(data_root)) == 0
    assert all(
        l["pending"] == 0
        for l in _output_lines(capsys)
        if "entrypoint" in l and "status" not in l
    )


def test_one_broken_entrypoint_is_loud_and_never_aborts_the_rest(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")

    def _boom(_ctx, _scope) -> list:
        raise RuntimeError("entrypoint exploded")

    patched = tuple(
        dataclasses.replace(e, run=_boom) if e.runner == "run_ecr_catchup.py" else e
        for e in cadence.CADENCE_ENTRYPOINTS
    )
    monkeypatch.setattr(cadence, "CADENCE_ENTRYPOINTS", patched)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    lines = _output_lines(capsys)
    failures = [l for l in lines if l.get("status") == "entrypoint_failed"]
    assert [(l["cycle"], l["entrypoint"]) for l in failures] == [
        (1, "run_ecr_catchup.py"),
        (2, "run_ecr_catchup.py"),
    ]
    assert "RuntimeError" in failures[0]["error"]
    assert all(failure["elapsed_seconds"] >= 0 for failure in failures)
    # The loop continued past the broken entrypoint: the ASR skip marker (last
    # in the registry) still printed in both cycles.
    assert [l["cycle"] for l in lines if l.get("status") == "skipped_asr_compute"] == [1, 2]


def test_systemic_root_loss_aborts_remaining_cadence_work(
    tmp_path, capsys, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    calls: list[str] = []

    def root_loss(_ctx, _scope) -> list:
        calls.append("root-loss.py")
        raise DataLakeRootUnavailableError("verified lake root disappeared")

    def later(_ctx, _scope) -> list:
        calls.append("later.py")
        return []

    monkeypatch.setattr(
        cadence,
        "CADENCE_ENTRYPOINTS",
        (
            cadence.CadenceEntrypoint(
                runner="root-loss.py", pending=lambda _ctx, _scope: 0, run=root_loss
            ),
            cadence.CadenceEntrypoint(
                runner="later.py", pending=lambda _ctx, _scope: 0, run=later
            ),
        ),
    )

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    assert calls == ["root-loss.py"]
    aborts = [
        line
        for line in _output_lines(capsys)
        if line.get("status") == "cadence_aborted_root_unavailable"
    ]
    assert len(aborts) == 1
    assert aborts[0]["cycle"] == 1
    assert aborts[0]["entrypoint"] == "root-loss.py"
    assert aborts[0]["skipped_entrypoint_runs"] == 3
    assert aborts[0]["post_cycle_pending_skipped"] is True
    assert aborts[0]["elapsed_seconds"] >= 0


def test_skip_asr_visible_backlog_fails_completion_signal(
    tmp_path, capsys, monkeypatch
) -> None:
    # A skipped ASR lane stays compute-free and visible, but pending ASR work is
    # still remaining work, so it cannot produce an exit-0 completion signal.
    data_root = DataLakeRoot.for_test(tmp_path / "lake")

    patched = tuple(
        dataclasses.replace(e, pending=lambda _ctx, _scope: 3)
        if e.needs_asr_compute
        else e
        for e in cadence.CADENCE_ENTRYPOINTS
    )
    monkeypatch.setattr(cadence, "CADENCE_ENTRYPOINTS", patched)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    lines = _output_lines(capsys)
    markers = [l for l in lines if l.get("status") == "skipped_asr_compute"]
    assert [(l["cycle"], l["pending"]) for l in markers] == [(1, 3), (2, 3)]
    assert [
        (l["cycle"], l["entrypoint"], l["pending"])
        for l in lines
        if l.get("status") == "post_cycle_pending"
    ] == [("post", "run_asr_transcript_catchup.py", 3)]


def test_post_cycle_pending_sweep_catches_empty_result_fake_pass(
    tmp_path, capsys, monkeypatch
) -> None:
    # Even if a composed runner incorrectly emits no status, the cadence cannot
    # exit 0 while that runner's pending surface still reports backlog.
    data_root = DataLakeRoot.for_test(tmp_path / "lake")

    patched = tuple(
        dataclasses.replace(
            e,
            pending=lambda _ctx, _scope: 1,
            run=lambda _ctx, _scope: [],
        )
        if e.runner == "run_ecr_catchup.py"
        else e
        for e in cadence.CADENCE_ENTRYPOINTS
    )
    monkeypatch.setattr(cadence, "CADENCE_ENTRYPOINTS", patched)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    assert [
        (l["cycle"], l["entrypoint"], l["pending"])
        for l in _output_lines(capsys)
        if l.get("status") == "post_cycle_pending"
    ] == [("post", "run_ecr_catchup.py", 1)]


def test_failed_skip_pending_check_fails_the_signal(tmp_path, capsys, monkeypatch) -> None:
    # Skipping execution never skips checkability: if the skipped lane's
    # pending check cannot even run, the no-work claim is invalid.
    data_root = DataLakeRoot.for_test(tmp_path / "lake")

    def _boom(_ctx, _scope) -> int:
        raise RuntimeError("pending check exploded")

    patched = tuple(
        dataclasses.replace(e, pending=_boom) if e.needs_asr_compute else e
        for e in cadence.CADENCE_ENTRYPOINTS
    )
    monkeypatch.setattr(cadence, "CADENCE_ENTRYPOINTS", patched)

    assert run_cadence(_ctx(data_root), skip_asr=True) == 1
    failures = [
        l
        for l in _output_lines(capsys)
        if l.get("status") == "skipped_asr_pending_check_failed"
    ]
    assert [l["cycle"] for l in failures] == [1, 2]


def test_cli_check_run_check_roundtrip(tmp_path, monkeypatch, capsys) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    _commit_packet(data_root, tmp_path)

    def fake_resolve(cls, *, explicit=None, **_kwargs):  # noqa: ANN001
        assert explicit is None
        return data_root

    monkeypatch.setattr(DataLakeRoot, "resolve", classmethod(fake_resolve))
    rebuild_calls = []

    def fake_rebuild(argv):  # noqa: ANN001
        rebuild_calls.append(argv)
        return 0

    monkeypatch.setattr(cadence._indexes_rebuild, "main", fake_rebuild)

    assert main(["--check"]) == 1
    capsys.readouterr()
    assert main(["--run", "--skip-asr"]) == 0
    assert rebuild_calls == [
        [
            "--root",
            str(data_root.path),
            "--target",
            "derived_retrieval",
            "--use-stored-product-mention-policy",
        ]
    ]
    assert any(
        line.get("status") == "lake_map_rebuilt"
        and line.get("map_scope") == "live_after_snapshot_completion"
        for line in _output_lines(capsys)
    )
    assert main(["--check"]) == 0
    capsys.readouterr()


def test_cli_fresh_root_bootstrap_routes_active_policy(
    tmp_path, monkeypatch, capsys
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    _commit_packet(data_root, tmp_path)
    monkeypatch.setattr(
        DataLakeRoot,
        "resolve",
        classmethod(lambda cls, **_kwargs: data_root),
    )
    rebuild_calls = []
    monkeypatch.setattr(
        cadence._indexes_rebuild,
        "main",
        lambda argv: rebuild_calls.append(argv) or 0,
    )

    assert main(
        ["--run", "--skip-asr", "--bootstrap-active-product-mention-policy"]
    ) == 0
    assert rebuild_calls == [
        [
            "--root",
            str(data_root.path),
            "--target",
            "derived_retrieval",
            "--bootstrap-active-product-mention-policy",
        ]
    ]
    assert any(
        line.get("status") == "lake_map_rebuilt"
        and line.get("policy_source") == "active_checkout_bootstrap"
        for line in _output_lines(capsys)
    )


def test_failed_cadence_never_attempts_lake_map_rebuild(
    tmp_path, monkeypatch
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")

    monkeypatch.setattr(
        DataLakeRoot,
        "resolve",
        classmethod(lambda cls, **_kwargs: data_root),
    )
    monkeypatch.setattr(cadence, "run_cadence", lambda *_args, **_kwargs: 1)
    rebuild_calls = []
    monkeypatch.setattr(
        cadence._indexes_rebuild,
        "main",
        lambda argv: rebuild_calls.append(argv) or 0,
    )

    assert main(["--run", "--skip-asr"]) == 1
    assert rebuild_calls == []


def test_lake_map_rebuild_failure_fails_cadence(
    tmp_path, monkeypatch, capsys
) -> None:
    data_root = DataLakeRoot.for_test(tmp_path / "lake")
    monkeypatch.setattr(
        DataLakeRoot,
        "resolve",
        classmethod(lambda cls, **_kwargs: data_root),
    )
    monkeypatch.setattr(cadence, "run_cadence", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(cadence._indexes_rebuild, "main", lambda _argv: 2)

    assert main(["--run", "--skip-asr"]) == 2
    events = _output_lines(capsys)
    map_terminal = [
        event
        for event in events
        if event.get("phase") == "lake_map_rebuild"
        and event.get("status") == "phase_failed"
    ]
    assert len(map_terminal) == 1
    assert map_terminal[0]["exit_code"] == 2
    assert map_terminal[0]["elapsed_seconds"] >= 0


def test_cli_usage_errors(tmp_path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        main(["--check", "--run"])
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        main(["--check", "--skip-asr"])
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        main(["--check", "--bootstrap-active-product-mention-policy"])
    assert excinfo.value.code == 2
