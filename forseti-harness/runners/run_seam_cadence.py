"""Seam cadence runner: the executable completion signal for bronze consumption.

Captures one read-only committed-packet snapshot, executes every seam CATCH-UP
entrypoint twice against that exact set, and exits nonzero if the SECOND cycle
performs any work or emits any status — "this starting bronze batch is caught
up" becomes an executable claim instead of an agent judgment. Packets committed
after the snapshot are reported as next-run work and do not poison the current
completion signal. Census
authority: ``docs/decisions/bronze_consumer_census_closure_record_v0.md``;
seam contract: ``core_spine_v0_data_lake_consumption_seam_contract_v0.md``.

This runner is an ORCHESTRATOR, not a seam consumer: it imports the catch-up
runner modules and composes their public ``pending_packets``/``run_catchup``
entrypoints. It reads the root's committed by-key packet ids to establish the
immutable start boundary, performs one fail-loud availability reconcile for
that scope, then tells every composed runner to reuse that reconciled view.
It writes no acks and owns no pickup or acknowledgement behavior — those
semantics stay inside the composed runners (the consumer seam-coverage gate
classifies this direct reconcile-only orchestration separately;
``tests/contract/test_seam_cadence_coverage.py`` pins this registry to that
surface).

Exit semantics (``--run``): cycle 1 is allowed to work (its entries are the
backlog being drained); cycle 2 must emit ZERO entrypoint status entries, and a
final compute-free pending sweep must find ZERO remaining backlog. Failures
never satisfy the signal: a packet that failed in cycle 1 stays
unacknowledged, re-surfaces in cycle 2, and fails the exit code. An ordinary
entrypoint exception is a visible ``entrypoint_failed`` entry for that lane and
never silently aborts the remaining lanes. Verified loss of the whole data-root
identity is different: it emits one bounded cadence-abort event and stops all
remaining entrypoint runs immediately.

After and only after that completion signal passes, the cadence invokes the
contract-pinned data-lake index runner for one ``derived_retrieval`` rebuild.
Normal maintenance reads exact product-mention policy pins from the stored
``by_mention`` manifest. A fresh root uses one explicit
``--bootstrap-active-product-mention-policy`` run to bind and report this
checkout's exact active pins; bootstrap refuses an existing manifest. A rebuild
failure fails the cadence exit code loudly; no failed cadence attempts a
lake-map refresh.

ASR COST GATE: the ASR entrypoint executes local owner-operated compute on an
unskipped ``--run``. ``--skip-asr`` skips only its execution and prints a
visible ``skipped_asr_compute`` marker EVERY cycle carrying the compute-free
pending count — a skipped lane stays loud, never silent. The healthy marker is
cadence-level output and does not count as cycle-2 work (the sanctioned
compute-free cadence); remaining ASR pending work or a failed skip-path pending
check DOES count in the final pending sweep.

The three LLM extract runners are seam consumers but NOT cadence entrypoints
(``CLASSIFIED_OUT_SEAM_CONSUMERS``): their extraction is owner-gated per-turn
LLM compute, not a compute-free cadence. Their backlog is owned by their own
``--check`` surfaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.consumption import reconcile_availability_per_packet
from data_lake.root import DataLakeRootUnavailableError
from runners import run_asr_transcript_catchup as _asr
from runners import run_basenotes_cleaning_catchup as _basenotes
from runners import run_ecr_catchup as _ecr
from runners import run_fragrance_review_projection_catchup as _fragrance_review
from runners import run_fragrantica_cleaning_catchup as _fragrantica
from runners import run_ig_reels_grid_projection_catchup as _ig_reels_grid
from runners import run_parfumo_cleaning_catchup as _parfumo
from runners import run_tiktok_comment_attention_producer as _tiktok_comment_attention
from runners import run_tiktok_grid_observation_producer as _tiktok_grid_observation
from runners import run_data_lake_indexes_rebuild as _indexes_rebuild


@dataclass(frozen=True)
class CadenceContext:
    """Per-invocation state shared by every entrypoint call."""

    data_root: object
    transcriber_policy: dict
    asr_model: str
    asr_compute_type: str


@dataclass(frozen=True)
class CadenceEntrypoint:
    """One composed catch-up entrypoint: filename (the census/audit key), a
    compute-free pending count, and the cadence execution call."""

    runner: str
    pending: Callable[[CadenceContext, Sequence[str] | None], int]
    run: Callable[[CadenceContext, Sequence[str] | None], list]
    needs_asr_compute: bool = False


def _asr_transcribe_fn(ctx: CadenceContext):
    # Lazy: the ASR library loads only on an unskipped --run reaching this
    # entrypoint (mirrors run_asr_transcript_catchup.main).
    from source_capture.transcript.audio_asr import AudioTranscriber

    return AudioTranscriber(model_name=ctx.asr_model, compute_type=ctx.asr_compute_type)


def _asr_run(
    ctx: CadenceContext, scope_packet_ids: Sequence[str] | None
) -> list:
    with _asr_transcribe_fn(ctx) as transcribe_fn:
        return _asr.run_catchup(
            data_root=ctx.data_root,
            transcribe_fn=transcribe_fn,
            transcriber_policy=ctx.transcriber_policy,
            scope_packet_ids=scope_packet_ids,
            reconcile_availability=False,
        )


# The declared cadence surface: every seam catch-up entrypoint, in execution
# order. tests/contract/test_seam_cadence_coverage.py pins this registry plus
# CLASSIFIED_OUT_SEAM_CONSUMERS to the discovered seam-consumer runner surface,
# so a new seam consumer must be classified into the cadence or out of it.
CADENCE_ENTRYPOINTS: tuple[CadenceEntrypoint, ...] = (
    CadenceEntrypoint(
        runner="run_ecr_catchup.py",
        pending=lambda ctx, scope: len(
            _ecr.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _ecr.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_fragrantica_cleaning_catchup.py",
        pending=lambda ctx, scope: len(
            _fragrantica.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _fragrantica.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_basenotes_cleaning_catchup.py",
        pending=lambda ctx, scope: len(
            _basenotes.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _basenotes.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_parfumo_cleaning_catchup.py",
        pending=lambda ctx, scope: len(
            _parfumo.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _parfumo.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_fragrance_review_projection_catchup.py",
        pending=lambda ctx, scope: len(
            _fragrance_review.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _fragrance_review.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_ig_reels_grid_projection_catchup.py",
        pending=lambda ctx, scope: len(
            _ig_reels_grid.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _ig_reels_grid.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_tiktok_comment_attention_producer.py",
        pending=lambda ctx, scope: len(
            _tiktok_comment_attention.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _tiktok_comment_attention.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_tiktok_grid_observation_producer.py",
        pending=lambda ctx, scope: len(
            _tiktok_grid_observation.pending_packets(
                data_root=ctx.data_root,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=lambda ctx, scope: _tiktok_grid_observation.run_catchup(
            data_root=ctx.data_root,
            scope_packet_ids=scope,
            reconcile_availability=False,
        ),
    ),
    CadenceEntrypoint(
        runner="run_asr_transcript_catchup.py",
        pending=lambda ctx, scope: len(
            _asr.pending_packets(
                data_root=ctx.data_root,
                transcriber_policy=ctx.transcriber_policy,
                scope_packet_ids=scope,
                reconcile_availability=False,
            )
        ),
        run=_asr_run,
        needs_asr_compute=True,
    ),
)

# Seam consumers deliberately NOT driven by this cadence, with the census
# reason. Owned by the census-closure record; the coverage contract test
# enforces that these plus CADENCE_ENTRYPOINTS exactly cover the discovered
# seam-consumer surface.
CLASSIFIED_OUT_SEAM_CONSUMERS: dict[str, str] = {
    "run_ig_reels_product_extract.py": (
        "LLM extraction lane: owner-gated per-turn compute, not a compute-free "
        "cadence entrypoint; backlog visible via its own --check"
    ),
    "run_tiktok_product_extract.py": (
        "LLM extraction lane: owner-gated per-turn compute, not a compute-free "
        "cadence entrypoint; execution requires an injected provider transport"
    ),
    "run_transcript_product_extract.py": (
        "LLM extraction lane: owner-gated per-turn compute, not a compute-free "
        "cadence entrypoint; backlog visible via its own --check"
    ),
}


def _print(entry: dict) -> None:
    print(json.dumps(entry, ensure_ascii=False, sort_keys=True), flush=True)


def _start_phase(phase: str, **context: object) -> float:
    started_at = perf_counter()
    _print({"cycle": None, "phase": phase, "status": "phase_started", **context})
    return started_at


def _finish_phase(
    phase: str, started_at: float, *, succeeded: bool, **context: object
) -> None:
    _print(
        {
            "cycle": None,
            "phase": phase,
            "status": "phase_completed" if succeeded else "phase_failed",
            "elapsed_seconds": round(max(0.0, perf_counter() - started_at), 3),
            **context,
        }
    )


def _entrypoint_progress(
    *,
    phase: str,
    entrypoint: str,
    status: str,
    started_at: float | None = None,
    **context: object,
) -> float:
    now = perf_counter()
    event: dict[str, object] = {
        "cycle": None,
        "phase": phase,
        "entrypoint": entrypoint,
        "status": status,
        **context,
    }
    if started_at is not None:
        event["elapsed_seconds"] = round(max(0.0, now - started_at), 3)
    _print(event)
    return now


def run_check(ctx: CadenceContext) -> int:
    """Single compute-free pending pass. Exit 0 iff every entrypoint reports a
    zero backlog and every pending check succeeds."""
    scope_packet_ids = _capture_start_snapshot(ctx)
    if scope_packet_ids is None:
        return 1
    if not _reconcile_start_snapshot(ctx, scope_packet_ids):
        return 1
    phase = "pending_check"
    phase_started_at = _start_phase(phase)
    failures = 0
    for entrypoint in CADENCE_ENTRYPOINTS:
        entrypoint_started_at = _entrypoint_progress(
            phase=phase,
            entrypoint=entrypoint.runner,
            status="entrypoint_started",
            operation="pending_check",
        )
        try:
            count = entrypoint.pending(ctx, scope_packet_ids)
        except Exception as exc:  # noqa: BLE001 - per-entrypoint failure isolation
            _entrypoint_progress(
                phase=phase,
                entrypoint=entrypoint.runner,
                status="pending_check_failed",
                started_at=entrypoint_started_at,
                operation="pending_check",
                error=f"{type(exc).__name__}: {exc}"[:200],
            )
            failures += 1
            continue
        _print({"entrypoint": entrypoint.runner, "pending": count})
        _entrypoint_progress(
            phase=phase,
            entrypoint=entrypoint.runner,
            status="entrypoint_completed",
            started_at=entrypoint_started_at,
            operation="pending_check",
            pending=count,
        )
        if count:
            failures += 1
    _finish_phase(
        phase, phase_started_at, succeeded=failures == 0, failure_count=failures
    )
    _report_late_arrivals(ctx, scope_packet_ids)
    return 1 if failures else 0


def _abort_root_unavailable(
    *,
    cycle: int | str,
    entrypoint: str,
    entrypoint_index: int,
    exc: Exception,
    phase: str,
    started_at: float,
) -> int:
    remaining_in_cycle = max(0, len(CADENCE_ENTRYPOINTS) - entrypoint_index - 1)
    remaining_later_cycles = len(CADENCE_ENTRYPOINTS) if cycle == 1 else 0
    _print(
        {
            "cycle": cycle,
            "entrypoint": entrypoint,
            "status": "cadence_aborted_root_unavailable",
            "error": f"{type(exc).__name__}: {exc}"[:200],
            "skipped_entrypoint_runs": remaining_in_cycle + remaining_later_cycles,
            "post_cycle_pending_skipped": True,
            "phase": phase,
            "elapsed_seconds": round(max(0.0, perf_counter() - started_at), 3),
        }
    )
    return 1


def run_cadence(ctx: CadenceContext, *, skip_asr: bool) -> int:
    """Two full cycles over every entrypoint. Exit 0 iff cycle 2 emits ZERO
    entrypoint status entries and a final compute-free pending sweep finds ZERO
    remaining backlog (the executable completion signal). The healthy skip-asr
    marker is cadence-level output excluded from cycle-2 status accounting; a
    skipped ASR backlog still fails the final pending sweep."""
    scope_packet_ids = _capture_start_snapshot(ctx)
    if scope_packet_ids is None:
        return 1
    if not _reconcile_start_snapshot(ctx, scope_packet_ids):
        return 1

    second_cycle_entries = 0
    for cycle in (1, 2):
        phase = f"cycle_{cycle}"
        phase_started_at = _start_phase(phase)
        entrypoint_failures = 0
        for entrypoint_index, entrypoint in enumerate(CADENCE_ENTRYPOINTS):
            operation = (
                "pending_check"
                if skip_asr and entrypoint.needs_asr_compute
                else "run"
            )
            entrypoint_started_at = _entrypoint_progress(
                phase=phase,
                entrypoint=entrypoint.runner,
                status="entrypoint_started",
                operation=operation,
            )
            if skip_asr and entrypoint.needs_asr_compute:
                try:
                    pending = entrypoint.pending(ctx, scope_packet_ids)
                except DataLakeRootUnavailableError as exc:
                    return _abort_root_unavailable(
                        cycle=cycle,
                        entrypoint=entrypoint.runner,
                        entrypoint_index=entrypoint_index,
                        exc=exc,
                        phase=phase,
                        started_at=entrypoint_started_at,
                    )
                except Exception as exc:  # noqa: BLE001 - skipped lane must stay checkable
                    _entrypoint_progress(
                        phase=phase,
                        entrypoint=entrypoint.runner,
                        status="skipped_asr_pending_check_failed",
                        started_at=entrypoint_started_at,
                        operation=operation,
                        cycle=cycle,
                        error=f"{type(exc).__name__}: {exc}"[:200],
                    )
                    entrypoint_failures += 1
                    if cycle == 2:
                        second_cycle_entries += 1
                    continue
                # Never a silent skip: the marker prints EVERY cycle and
                # carries the live pending count for the skipped lane.
                _print(
                    {
                        "cycle": cycle,
                        "entrypoint": entrypoint.runner,
                        "status": "skipped_asr_compute",
                        "pending": pending,
                    }
                )
                _entrypoint_progress(
                    phase=phase,
                    entrypoint=entrypoint.runner,
                    status="entrypoint_completed",
                    started_at=entrypoint_started_at,
                    operation=operation,
                    pending=pending,
                )
                continue
            entrypoint_failed = False
            try:
                results = entrypoint.run(ctx, scope_packet_ids)
            except DataLakeRootUnavailableError as exc:
                return _abort_root_unavailable(
                    cycle=cycle,
                    entrypoint=entrypoint.runner,
                    entrypoint_index=entrypoint_index,
                    exc=exc,
                    phase=phase,
                    started_at=entrypoint_started_at,
                )
            except Exception as exc:  # noqa: BLE001 - per-entrypoint failure isolation
                entrypoint_failed = True
                entrypoint_failures += 1
                results = [
                    {
                        "status": "entrypoint_failed",
                        "error": f"{type(exc).__name__}: {exc}"[:200],
                        "elapsed_seconds": round(
                            max(0.0, perf_counter() - entrypoint_started_at), 3
                        ),
                    }
                ]
            for result in results:
                _print({"cycle": cycle, "entrypoint": entrypoint.runner, **result})
            if not entrypoint_failed:
                _entrypoint_progress(
                    phase=phase,
                    entrypoint=entrypoint.runner,
                    status="entrypoint_completed",
                    started_at=entrypoint_started_at,
                    operation=operation,
                    result_count=len(results),
                )
            if cycle == 2:
                second_cycle_entries += len(results)
        _finish_phase(
            phase,
            phase_started_at,
            succeeded=entrypoint_failures == 0,
            entrypoint_failure_count=entrypoint_failures,
        )
    post_phase = "post_cycle_pending_sweep"
    post_started_at = _start_phase(post_phase)
    try:
        post_cycle_pending = _post_cycle_pending_failures(ctx, scope_packet_ids)
    except DataLakeRootUnavailableError as exc:
        return _abort_root_unavailable(
            cycle="post",
            entrypoint=post_phase,
            entrypoint_index=len(CADENCE_ENTRYPOINTS) - 1,
            exc=exc,
            phase=post_phase,
            started_at=post_started_at,
        )
    _finish_phase(
        post_phase,
        post_started_at,
        succeeded=post_cycle_pending == 0,
        failure_count=post_cycle_pending,
    )
    _report_late_arrivals(ctx, scope_packet_ids)
    return 1 if second_cycle_entries or post_cycle_pending else 0


def _capture_start_snapshot(ctx: CadenceContext) -> tuple[str, ...] | None:
    phase = "snapshot"
    started_at = _start_phase(phase)
    try:
        packet_ids = tuple(ctx.data_root.list_committed_packet_ids())
    except Exception as exc:  # noqa: BLE001 - boundary failure must stay loud
        error = f"{type(exc).__name__}: {exc}"[:200]
        _print(
            {
                "cycle": "snapshot",
                "status": "cadence_snapshot_failed",
                "error": error,
                "elapsed_seconds": round(max(0.0, perf_counter() - started_at), 3),
            }
        )
        _finish_phase(phase, started_at, succeeded=False, error=error)
        return None
    digest = hashlib.sha256("\n".join(packet_ids).encode("utf-8")).hexdigest()
    _print(
        {
            "cycle": "snapshot",
            "status": "cadence_snapshot_started",
            "packet_count": len(packet_ids),
            "packet_ids_sha256": digest,
        }
    )
    _finish_phase(
        phase,
        started_at,
        succeeded=True,
        packet_count=len(packet_ids),
        packet_ids_sha256=digest,
    )
    return packet_ids


def _reconcile_start_snapshot(
    ctx: CadenceContext, scope_packet_ids: Sequence[str]
) -> bool:
    """Reconcile the immutable cadence scope once before any composed lane."""
    phase = "availability_reconcile"
    started_at = _start_phase(phase, packet_count=len(scope_packet_ids))
    try:
        failures = reconcile_availability_per_packet(
            ctx.data_root, scope_packet_ids=scope_packet_ids
        )
    except DataLakeRootUnavailableError as exc:
        _abort_root_unavailable(
            cycle=1,
            entrypoint=phase,
            entrypoint_index=-1,
            exc=exc,
            phase=phase,
            started_at=started_at,
        )
        return False
    for failure in failures:
        _print({"cycle": "snapshot", "entrypoint": phase, **failure})
    _finish_phase(
        phase,
        started_at,
        succeeded=not failures,
        failure_count=len(failures),
    )
    return not failures


def _report_late_arrivals(
    ctx: CadenceContext, scope_packet_ids: Sequence[str]
) -> None:
    phase = "late_arrival_check"
    started_at = _start_phase(phase)
    try:
        late = sorted(
            set(ctx.data_root.list_committed_packet_ids()) - set(scope_packet_ids)
        )
    except Exception as exc:  # noqa: BLE001 - informational check cannot poison snapshot
        error = f"{type(exc).__name__}: {exc}"[:200]
        _print(
            {
                "cycle": "post",
                "status": "late_arrival_check_failed",
                "error": error,
                "elapsed_seconds": round(max(0.0, perf_counter() - started_at), 3),
            }
        )
        _finish_phase(phase, started_at, succeeded=False, error=error)
        return
    if late:
        _print(
            {
                "cycle": "post",
                "status": "late_arrivals_observed",
                "packet_count": len(late),
                "packet_ids": late,
            }
        )
    _finish_phase(phase, started_at, succeeded=True, packet_count=len(late))


def _post_cycle_pending_failures(
    ctx: CadenceContext, scope_packet_ids: Sequence[str]
) -> int:
    """Final no-work proof: every pending helper must report zero backlog.

    This catches fake-pass paths where an entrypoint returned no status despite
    leaving work behind, or a later entrypoint made earlier entrypoint work after
    that earlier entrypoint's cycle-2 turn.
    """
    phase = "post_cycle_pending_sweep"
    failures = 0
    for entrypoint in CADENCE_ENTRYPOINTS:
        entrypoint_started_at = _entrypoint_progress(
            phase=phase,
            entrypoint=entrypoint.runner,
            status="entrypoint_started",
            operation="pending_check",
        )
        try:
            pending = entrypoint.pending(ctx, scope_packet_ids)
        except DataLakeRootUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - no-work claim must fail loud
            _entrypoint_progress(
                phase=phase,
                entrypoint=entrypoint.runner,
                status="post_cycle_pending_check_failed",
                started_at=entrypoint_started_at,
                operation="pending_check",
                error=f"{type(exc).__name__}: {exc}"[:200],
            )
            failures += 1
            continue
        if pending != 0:
            _print(
                {
                    "cycle": "post",
                    "entrypoint": entrypoint.runner,
                    "status": "post_cycle_pending",
                    "pending": pending,
                }
            )
            failures += 1
        _entrypoint_progress(
            phase=phase,
            entrypoint=entrypoint.runner,
            status="entrypoint_completed",
            started_at=entrypoint_started_at,
            operation="pending_check",
            pending=pending,
        )
    return failures


def _refresh_lake_map(
    ctx: CadenceContext,
    *,
    bootstrap_active_product_mention_policy: bool = False,
) -> int:
    """Invoke the sanctioned sole writer after the all-caught-up proof."""
    policy_argument = (
        "--bootstrap-active-product-mention-policy"
        if bootstrap_active_product_mention_policy
        else "--use-stored-product-mention-policy"
    )
    phase = "lake_map_rebuild"
    started_at = _start_phase(phase)
    result = _indexes_rebuild.main(
        [
            "--root",
            str(ctx.data_root.path),
            "--target",
            "derived_retrieval",
            policy_argument,
        ]
    )
    _print(
        {
            "entrypoint": "run_data_lake_indexes_rebuild.py",
            "status": "lake_map_rebuilt" if result == 0 else "lake_map_rebuild_failed",
            "exit_code": result,
            "map_scope": "live_after_snapshot_completion",
            "policy_source": (
                "active_checkout_bootstrap"
                if bootstrap_active_product_mention_policy
                else "stored_manifest"
            ),
            "elapsed_seconds": round(max(0.0, perf_counter() - started_at), 3),
        }
    )
    _finish_phase(
        phase,
        started_at,
        succeeded=result == 0,
        exit_code=result,
    )
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Seam cadence: run every seam catch-up entrypoint twice; the second "
            "cycle must perform no work and final pending checks must be zero."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print each entrypoint's pending count; exit nonzero if any backlog exists.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help=(
            "Run two full catch-up cycles; exit nonzero if the second cycle emits "
            "anything or final pending checks are nonzero."
        ),
    )
    parser.add_argument(
        "--skip-asr",
        action="store_true",
        help=(
            "With --run: skip ASR execution (local compute), printing a visible "
            "skipped marker with the pending count every cycle."
        ),
    )
    parser.add_argument(
        "--bootstrap-active-product-mention-policy",
        action="store_true",
        help=(
            "With --run only: one-time fresh-root map bootstrap using the exact "
            "active product-mention policy from this checkout; refuses an "
            "existing by_mention manifest."
        ),
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model name (part of the ASR obligation fingerprint).",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="faster-whisper compute type (part of the ASR obligation fingerprint).",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Forseti data lake root. Defaults to FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.check == args.run:
        parser.exit(status=2, message="choose exactly one of --check or --run\n")
    if args.skip_asr and args.check:
        parser.exit(
            status=2,
            message="--skip-asr applies to --run only (--check is already compute-free)\n",
        )

    if args.bootstrap_active_product_mention_policy and args.check:
        parser.exit(
            status=2,
            message="--bootstrap-active-product-mention-policy applies to --run only",
        )

    from data_lake.root import DataLakeRoot

    mode = "check" if args.check else "run"
    cadence_started_at = _start_phase("cadence", mode=mode)
    try:
        data_root = DataLakeRoot.resolve(explicit=args.data_root)
    except Exception as exc:  # noqa: BLE001 - CLI must surface root resolution failures
        error = f"{type(exc).__name__}: {exc}"
        _finish_phase(
            "cadence", cadence_started_at, succeeded=False, mode=mode, error=error[:200]
        )
        parser.exit(status=2, message=f"data root required: {error}\n")
    ctx = CadenceContext(
        data_root=data_root,
        transcriber_policy=_asr.default_transcriber_policy(
            model_name=args.model, compute_type=args.compute_type
        ),
        asr_model=args.model,
        asr_compute_type=args.compute_type,
    )
    if args.check:
        result = run_check(ctx)
    else:
        result = run_cadence(ctx, skip_asr=args.skip_asr)
        if result == 0:
            result = _refresh_lake_map(
                ctx,
                bootstrap_active_product_mention_policy=(
                    args.bootstrap_active_product_mention_policy
                ),
            )
    _finish_phase(
        "cadence",
        cadence_started_at,
        succeeded=result == 0,
        mode=mode,
        exit_code=result,
    )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
