"""Consumption-seam conformance suite (the contract's six obligations).

Any lane pickup implementation must pass these semantics unchanged — the
shared helper is the reference implementation. Contract:
``core_spine_v0_data_lake_consumption_seam_contract_v0.md`` (Conformance
Contract section).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_lake.consumption import (
    ConsumptionSeamError,
    PickupItem,
    ack_packet,
    ack_record_id,
    append_ack,
    find_acks,
    find_retractions,
    is_acknowledged,
    iter_all_acks,
    obligation_fingerprint,
    pickup,
    reconcile_availability_per_packet,
    retract_ack,
)
from data_lake.root import DataLakeRoot, DataLakeRootError, DataLakeRootUnavailableError
from source_capture.models import known_fact
from source_capture.writer import write_local_source_capture_packet

# A lane already declared in lane_registry.LANE_ROLES (the namespace rule).
_NS = "projection_ig"


def _commit_packet(root: DataLakeRoot, tmp_path: Path, body: str) -> str:
    src = tmp_path / f"{body}.json"
    src.write_text(f'{{"b": "{body}"}}', encoding="utf-8")
    receipt = write_local_source_capture_packet(
        data_root=root,
        input_files=[src],
        source_family="reddit",
        source_surface="s",
        source_locator=known_fact(f"https://www.reddit.com/r/test/{body}/"),
        decision_question="q",
        capture_context="consumption seam conformance",
    )
    return receipt.packet.packet_id


def _static_obligation(raw_anchor: str) -> dict:
    return {"obligation_schema": 1, "consumer": "conformance_suite", "inputs": []}


def _obligation(**over) -> dict:
    base = {"obligation_schema": 1, "consumer": "conformance_suite"}
    base.update(over)
    return base


_EVIDENCE = [{"kind": "test_marker", "ref": "r1"}]


# --- namespace rule -----------------------------------------------------------


def test_ack_namespace_must_be_registered_for_active_paths(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor="A" * 26, ack_namespace="not_a_lane",
                   obligation=_obligation(), evidence=_EVIDENCE)
    with pytest.raises(ConsumptionSeamError):
        list(pickup(root, ack_namespace="not_a_lane", obligation_fn=_static_obligation))
    # history readers are NOT registry-gated (registry evolution must not make
    # history unreadable); an unknown namespace simply has no history.
    assert find_acks(root, raw_anchor="A" * 26, ack_namespace="not_a_lane") == []
    assert find_retractions(root, raw_anchor="A" * 26, ack_namespace="not_a_lane") == []


def test_history_survives_registry_evolution(tmp_path: Path, monkeypatch) -> None:
    # Simulate a lane being retired from LANE_ROLES after acks were written:
    # history stays readable; active consumer paths fail LOUDLY (never silent).
    import data_lake.consumption as consumption

    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    obligation = _static_obligation(pid)
    append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, evidence=_EVIDENCE)

    evolved = {lane: role for lane, role in consumption.LANE_ROLES.items() if lane != _NS}
    monkeypatch.setattr(consumption, "LANE_ROLES", evolved)

    # append-only completion history remains valid and readable
    assert len(find_acks(root, raw_anchor=pid, ack_namespace=_NS)) == 1
    # the undone-view walk keeps working over retired-namespace history
    assert {(pid, _NS)} == {(a, n) for a, n, _f in iter_all_acks(root)}
    # an ACTIVE consumer using the retired namespace fails loudly at its own call
    with pytest.raises(ConsumptionSeamError):
        list(pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation))
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                   obligation=obligation, evidence=_EVIDENCE)


# --- no fake done: evidence is mandatory ---------------------------------------


def test_append_ack_requires_evidence(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation={}, evidence=[])


# --- idempotence ----------------------------------------------------------------


def test_pickup_yields_committed_then_skips_after_ack(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    first = _commit_packet(root, tmp_path, "alpha")
    second = _commit_packet(root, tmp_path, "beta")

    undone = {item.raw_anchor for item in
              pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)}
    assert undone == {first, second}

    append_ack(root, raw_anchor=first, ack_namespace=_NS,
               obligation=_static_obligation(first), evidence=_EVIDENCE)
    undone = {item.raw_anchor for item in
              pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)}
    assert undone == {second}

    append_ack(root, raw_anchor=second, ack_namespace=_NS,
               obligation=_static_obligation(second), evidence=_EVIDENCE)
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)) == []


# --- append-only acks ------------------------------------------------------------


def test_ack_overwrite_hard_fails(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=_obligation(v=1), evidence=_EVIDENCE)
    with pytest.raises(DataLakeRootError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=_obligation(v=1), evidence=_EVIDENCE)


# --- minimum obligation envelope + evidence shape (contract-validated) -----------


def test_obligation_envelope_is_enforced(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                   obligation={"inputs": []}, evidence=_EVIDENCE)  # no schema/consumer
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                   obligation={"obligation_schema": 1, "consumer": " "}, evidence=_EVIDENCE)
    with pytest.raises(ConsumptionSeamError):
        list(pickup(root, ack_namespace=_NS, obligation_fn=lambda _a: {"bare": True}))


def test_evidence_entries_require_kind(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                   obligation=_obligation(), evidence=[{"ref": "r1"}])  # no kind
    with pytest.raises(ConsumptionSeamError):
        append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                   obligation=_obligation(), evidence=["not-a-mapping"])


# --- retraction cycle (conformance obligation 7) ----------------------------------


def test_retraction_resurfaces_then_reack_is_representable(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    obligation = _static_obligation(pid)

    append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, evidence=_EVIDENCE)
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)) == []

    retract_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation,
                reason="recorded evidence cited the wrong marker")
    assert not is_acknowledged(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation)
    resurfaced = [item.raw_anchor for item in
                  pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)]
    assert resurfaced == [pid]

    # truthful re-acknowledgement lands at the next deterministic id, no overwrite
    append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, evidence=_EVIDENCE)
    assert is_acknowledged(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation)
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)) == []
    # full append-only history: two acks + one retraction
    assert len(find_acks(root, raw_anchor=pid, ack_namespace=_NS)) == 2
    assert len(find_retractions(root, raw_anchor=pid, ack_namespace=_NS)) == 1


def test_retraction_requires_reason_and_existing_ack(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    obligation = _static_obligation(pid)
    with pytest.raises(ConsumptionSeamError):
        retract_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, reason="x")
    append_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, evidence=_EVIDENCE)
    with pytest.raises(ConsumptionSeamError):
        retract_ack(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation, reason="  ")


# --- obligation growth re-pickup --------------------------------------------------


def test_obligation_growth_resurfaces_anchor(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    inputs: list[str] = []

    def obligation(_anchor: str) -> dict:
        return {"obligation_schema": 1, "consumer": "conformance_suite", "inputs": sorted(inputs)}

    append_ack(root, raw_anchor=pid, ack_namespace=_NS,
               obligation=obligation(pid), evidence=_EVIDENCE)
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=obligation)) == []

    inputs.append("late_record_1")  # a late-arriving input grows the obligation
    resurfaced = list(pickup(root, ack_namespace=_NS, obligation_fn=obligation))
    assert [item.raw_anchor for item in resurfaced] == [pid]

    append_ack(root, raw_anchor=pid, ack_namespace=_NS,
               obligation=obligation(pid), evidence=_EVIDENCE)
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=obligation)) == []
    # both completion facts remain as append-only history
    assert len(find_acks(root, raw_anchor=pid, ack_namespace=_NS)) == 2


# --- missed-event recovery (by-key backstop) ---------------------------------------


def test_missed_event_recovery_by_key(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")

    # Simulate a missed commit event: the availability entry vanishes.
    entry = root.path / "indexes" / "availability" / f"{pid}.json"
    assert entry.is_file()
    entry.unlink()

    # A visibly opted-out pickup over the stale surface misses the work — the
    # exact hazard the contract's reconcile precondition exists to prevent...
    assert list(pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation,
                       reconcile=False)) == []
    # ...while the DEFAULT pickup reconciles by key first and finds it.
    undone = [item.raw_anchor for item in
              pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)]
    assert undone == [pid]


def test_scoped_pickup_uses_one_ordered_snapshot_before_family_filter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    first = _commit_packet(root, tmp_path, "scoped-order-first")
    second = _commit_packet(root, tmp_path, "scoped-order-second")
    snapshot_calls = 0
    original_snapshot = root.snapshot_public_availability

    def counted_snapshot() -> list[dict]:
        nonlocal snapshot_calls
        snapshot_calls += 1
        return original_snapshot()

    monkeypatch.setattr(root, "snapshot_public_availability", counted_snapshot)

    available = [
        item.raw_anchor
        for item in pickup(
            root,
            ack_namespace=_NS,
            obligation_fn=_static_obligation,
            source_family="reddit",
            reconcile=False,
            scope_packet_ids=[second, first],
        )
    ]

    assert available == sorted([first, second])
    assert snapshot_calls == 1


def test_scoped_pickup_fails_loud_when_public_availability_disappears(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "scoped-missing")
    assert list(
        pickup(
            root,
            ack_namespace=_NS,
            obligation_fn=_static_obligation,
            source_family="instagram_creator",
            reconcile=False,
            scope_packet_ids=[selected],
        )
    ) == []

    (root.path / "indexes" / "availability" / f"{selected}.json").unlink()

    with pytest.raises(
        ConsumptionSeamError,
        match=f"scoped packet is missing from public availability.*{selected}",
    ):
        list(
            pickup(
                root,
                ack_namespace=_NS,
                obligation_fn=_static_obligation,
                source_family="instagram_creator",
                reconcile=False,
                scope_packet_ids=[selected],
            )
        )


def test_scoped_pickup_promotes_missing_root_to_systemic_failure(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "scoped-root-loss")
    root.path.rename(tmp_path / "disconnected-lake")

    with pytest.raises(DataLakeRootUnavailableError):
        list(
            pickup(
                root,
                ack_namespace=_NS,
                obligation_fn=_static_obligation,
                reconcile=False,
                scope_packet_ids=[selected],
            )
        )


# --- view-independence --------------------------------------------------------------


def test_view_independence(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    _commit_packet(root, tmp_path, "alpha")
    before = [item.raw_anchor for item in
              pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)]

    # A stale/lying view must not change pickup: views are caches, never authority.
    view_dir = (
        root.path / "indexes" / "derived_retrieval" / "silver_vault" / "core"
        / "query_tables"
    )
    view_dir.mkdir(parents=True, exist_ok=True)
    (view_dir / "undone.json").write_text(json.dumps({_NS: []}), encoding="utf-8")

    after = [item.raw_anchor for item in
             pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)]
    assert after == before


# --- corrupt ack: fail toward re-verification, never fake-done ------------------------


def test_corrupt_ack_treated_as_absent(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "alpha")
    obligation = _static_obligation(pid)
    path = append_ack(root, raw_anchor=pid, ack_namespace=_NS,
                      obligation=obligation, evidence=_EVIDENCE)
    assert is_acknowledged(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation)

    path.write_bytes(b"{truncated")  # integrity damage (outside normal operation)
    assert not is_acknowledged(root, raw_anchor=pid, ack_namespace=_NS, obligation=obligation)
    undone = [item.raw_anchor for item in
              pickup(root, ack_namespace=_NS, obligation_fn=_static_obligation)]
    assert undone == [pid]
    assert find_acks(root, raw_anchor=pid, ack_namespace=_NS) == []


# --- mechanics ------------------------------------------------------------------------


def test_fingerprint_is_key_order_independent() -> None:
    a = obligation_fingerprint({"x": 1, "y": [2, 3]})
    b = obligation_fingerprint({"y": [2, 3], "x": 1})
    assert a == b
    assert ack_record_id(a) == f"ack_{a[:24]}"


def test_iter_all_acks_walks_the_tree(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    first = _commit_packet(root, tmp_path, "alpha")
    second = _commit_packet(root, tmp_path, "beta")
    append_ack(root, raw_anchor=first, ack_namespace=_NS,
               obligation=_obligation(v=1), evidence=_EVIDENCE)
    append_ack(root, raw_anchor=second, ack_namespace="ecr_timing",
               obligation=_obligation(v=2), evidence=_EVIDENCE)
    # a retraction fact is history, not an ack — the walk yields ack facts only
    retract_ack(root, raw_anchor=first, ack_namespace=_NS,
                obligation=_obligation(v=1), reason="test retraction")

    seen = {(anchor, namespace) for anchor, namespace, _ack in iter_all_acks(root)}
    assert seen == {(first, _NS), (second, "ecr_timing")}


# --- shared reconcile: purge-phase concurrency isolation ------------------------


def test_scoped_reconcile_preserves_unselected_availability(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "selected")
    unselected = _commit_packet(root, tmp_path, "unselected")
    unselected_path = root.path / "indexes" / "availability" / f"{unselected}.json"
    unselected_before = unselected_path.read_bytes()

    assert reconcile_availability_per_packet(
        root, scope_packet_ids=[selected]
    ) == []
    assert unselected_path.read_bytes() == unselected_before
    assert [
        item.raw_anchor
        for item in pickup(
            root,
            ack_namespace=_NS,
            obligation_fn=lambda _packet_id: _obligation(v=1),
            reconcile=True,
            scope_packet_ids=[selected],
        )
    ] == [selected]


def test_scoped_reconcile_validates_successful_writes_with_one_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = [
        _commit_packet(root, tmp_path, "snapshot-once-a"),
        _commit_packet(root, tmp_path, "snapshot-once-b"),
    ]
    snapshot_calls = 0
    original_snapshot = root.snapshot_public_availability

    def counted_snapshot() -> list[dict]:
        nonlocal snapshot_calls
        snapshot_calls += 1
        return original_snapshot()

    monkeypatch.setattr(root, "snapshot_public_availability", counted_snapshot)
    monkeypatch.setattr(
        root,
        "read_availability",
        lambda _packet_id: pytest.fail("scoped reconcile used a per-packet read"),
    )

    assert reconcile_availability_per_packet(
        root, scope_packet_ids=selected
    ) == []
    assert snapshot_calls == 1


def test_scoped_reconcile_missing_public_write_fails_loud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "missing-after-write")
    monkeypatch.setattr(root, "snapshot_public_availability", lambda: [])

    failures = reconcile_availability_per_packet(
        root, scope_packet_ids=[selected]
    )

    assert [(row["packet_id"], row["status"]) for row in failures] == [
        (selected, "availability_reconcile_failed")
    ]
    assert "not publicly available after reconcile" in failures[0]["error"]


def test_scoped_reconcile_keeps_per_write_failure_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    failed = _commit_packet(root, tmp_path, "isolated-write-failure")
    healthy = _commit_packet(root, tmp_path, "isolated-write-healthy")
    original_record = root.record_availability

    def fail_one_write(packet_id: str) -> None:
        if packet_id == failed:
            raise PermissionError(13, "Access is denied")
        original_record(packet_id)

    monkeypatch.setattr(root, "record_availability", fail_one_write)

    failures = reconcile_availability_per_packet(
        root, scope_packet_ids=[healthy, failed]
    )

    assert [(row["packet_id"], row["status"]) for row in failures] == [
        (failed, "availability_reconcile_failed")
    ]
    assert "PermissionError" in failures[0]["error"]
    assert healthy in {
        entry["packet_id"] for entry in root.snapshot_public_availability()
    }


def test_empty_scoped_reconcile_skips_writes_and_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    monkeypatch.setattr(
        root,
        "record_availability",
        lambda _packet_id: pytest.fail("empty scope attempted a write"),
    )
    monkeypatch.setattr(
        root,
        "snapshot_public_availability",
        lambda: pytest.fail("empty scope attempted a snapshot"),
    )

    assert reconcile_availability_per_packet(root, scope_packet_ids=[]) == []


def test_scoped_reconcile_surfaces_corrupt_selected_anchor(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "selected-corrupt")
    container = root.find_packet(selected)
    assert container is not None
    (container / "manifest.json").write_text("{not-json\n", encoding="utf-8")

    failures = reconcile_availability_per_packet(
        root, scope_packet_ids=[selected]
    )
    assert [(row["packet_id"], row["status"]) for row in failures] == [
        (selected, "availability_reconcile_failed")
    ]
    assert failures[0]["error"]


def test_scoped_reconcile_snapshot_promotes_root_loss(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    selected = _commit_packet(root, tmp_path, "snapshot-root-loss")

    def disconnect_during_snapshot() -> list[dict]:
        root.path.rename(tmp_path / "disconnected-snapshot-lake")
        raise OSError(433, "A device which does not exist was specified")

    monkeypatch.setattr(
        root, "snapshot_public_availability", disconnect_during_snapshot
    )

    with pytest.raises(DataLakeRootUnavailableError) as excinfo:
        reconcile_availability_per_packet(root, scope_packet_ids=[selected])

    assert selected in str(excinfo.value)
    assert "data root is no longer a directory" in str(excinfo.value)


def test_scoped_reconcile_aborts_when_root_disappears(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    packet_ids = sorted(
        [
            _commit_packet(root, tmp_path, "root-loss-a"),
            _commit_packet(root, tmp_path, "root-loss-b"),
            _commit_packet(root, tmp_path, "root-loss-c"),
        ]
    )
    original_record = root.record_availability
    calls: list[str] = []

    def disconnect_on_second_packet(packet_id: str) -> None:
        calls.append(packet_id)
        if len(calls) == 2:
            root.path.rename(tmp_path / "disconnected-lake")
            raise OSError(433, "A device which does not exist was specified")
        original_record(packet_id)

    monkeypatch.setattr(root, "record_availability", disconnect_on_second_packet)

    with pytest.raises(DataLakeRootUnavailableError) as excinfo:
        reconcile_availability_per_packet(root, scope_packet_ids=packet_ids)

    assert calls == packet_ids[:2]
    assert packet_ids[1] in str(excinfo.value)
    assert "data root is no longer a directory" in str(excinfo.value)


def test_reconcile_purge_tolerates_concurrently_removed_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 2026-07-04 live race class: a concurrent writer removed/replaced an
    # availability entry between glob and unlink. Absent is the purged state,
    # so the reconcile stays clean and rebuilds every committed packet.
    from data_lake.consumption import reconcile_availability_per_packet

    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "healthy")

    original_unlink = Path.unlink

    def racing_unlink(self, *args, **kwargs):  # noqa: ANN001
        if self.suffix == ".json" and self.parent.name == "availability":
            original_unlink(self)  # the concurrent writer wins the race...
            raise FileNotFoundError(2, "The system cannot find the file specified")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", racing_unlink)
    failures = reconcile_availability_per_packet(root)
    monkeypatch.undo()

    assert failures == []
    assert root.read_availability(pid) is not None  # rebuilt after the purge


def test_reconcile_purge_surfaces_locked_entry_per_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A live-writer lock (Windows) or store fault on ONE entry is a visible
    # per-packet failure, never a whole-batch crash: the other committed
    # packet still purges, rebuilds, and stays available.
    from data_lake.consumption import reconcile_availability_per_packet

    root = DataLakeRoot.for_test(tmp_path / "lake")
    locked = _commit_packet(root, tmp_path, "locked")
    healthy = _commit_packet(root, tmp_path, "healthy2")

    original_unlink = Path.unlink

    def locking_unlink(self, *args, **kwargs):  # noqa: ANN001
        if self.name == f"{locked}.json" and self.parent.name == "availability":
            raise PermissionError(13, "Access is denied")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", locking_unlink)
    failures = reconcile_availability_per_packet(root)
    monkeypatch.undo()

    assert [(f["packet_id"], f["status"]) for f in failures] == [
        (locked, "availability_reconcile_failed")
    ]
    assert "PermissionError" in failures[0]["error"]
    # The healthy packet was never hostage to the locked one.
    assert root.read_availability(healthy) is not None


@pytest.mark.parametrize("namespace", ["projection_ig", "ecr_set"])
def test_ack_packet_persists_the_append_ack_record_and_tolerates_collision(
    tmp_path: Path, monkeypatch, namespace: str
) -> None:
    import data_lake.consumption as consumption

    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "ack_helper")
    obligation = _obligation(inputs=["committed-input"])
    item = PickupItem(pid, obligation, obligation_fingerprint(obligation))
    timestamp = "2026-09-05T00:00:00+00:00"

    class FixedDatetime:
        @staticmethod
        def now(tz):
            return consumption_datetime.fromisoformat(timestamp)

    consumption_datetime = consumption.datetime
    monkeypatch.setattr(consumption, "datetime", FixedDatetime)
    # The direct seam writer is the pre-refactor record-shape reference.
    expected_path = append_ack(
        root, raw_anchor=pid, ack_namespace=namespace,
        obligation=obligation, evidence=_EVIDENCE,
    )
    expected_bytes = expected_path.read_bytes()
    other_root = DataLakeRoot.for_test(tmp_path / "other_lake")
    monkeypatch.setattr("source_capture.writer.generate_ulid", lambda: pid)
    assert _commit_packet(other_root, tmp_path, "ack_helper") == pid
    assert ack_packet(other_root, item, _EVIDENCE, ack_namespace=namespace) == "acked"
    actual_path = other_root.lane_dir(
        subtree="acknowledgements", raw_anchor=pid, lane=namespace
    ) / expected_path.name
    assert actual_path.read_bytes() == expected_bytes
    # The second call hits create-only collision, rechecks this namespace, and
    # neither appends another fact nor overwrites the original completion.
    assert ack_packet(other_root, item, _EVIDENCE, ack_namespace=namespace) == "acked"
    assert actual_path.read_bytes() == expected_bytes
    assert len(find_acks(other_root, raw_anchor=pid, ack_namespace=namespace)) == 1


def test_ack_packet_failed_write_is_bounded_and_remains_unacknowledged(tmp_path: Path, monkeypatch) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    pid = _commit_packet(root, tmp_path, "failed_ack")
    item = PickupItem(pid, _obligation(), obligation_fingerprint(_obligation()))
    error = DataLakeRootError("write denied " + "x" * 250)

    def fail_write(*args, **kwargs):
        raise error

    monkeypatch.setattr(root, "append_record", fail_write)
    result = ack_packet(root, item, _EVIDENCE, ack_namespace=_NS)
    assert result == f"ack_failed: DataLakeRootError: {error}"[:200]
    assert len(result) == 200
    assert not is_acknowledged(root, raw_anchor=pid, ack_namespace=_NS, obligation=item.obligation)


@pytest.mark.parametrize("failure_site", ["append_ack", "is_acknowledged"])
def test_ack_packet_propagates_unhandled_and_recheck_failures(monkeypatch, failure_site: str) -> None:
    import data_lake.consumption as consumption

    error = OSError("unreadable acknowledgement store")

    def fail_append(*args, **kwargs):
        if failure_site == "append_ack":
            raise error
        raise DataLakeRootError("write failed")

    def fail_recheck(*args, **kwargs):
        raise error

    monkeypatch.setattr(consumption, "append_ack", fail_append)
    monkeypatch.setattr(consumption, "is_acknowledged", fail_recheck)
    item = PickupItem("A" * 26, _obligation(), obligation_fingerprint(_obligation()))
    with pytest.raises(OSError) as raised:
        ack_packet(object(), item, _EVIDENCE, ack_namespace=_NS)
    assert raised.value is error
