"""Scoped consumers read selected index keys, preserving public-read failures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_lake.consumption import ConsumptionSeamError, pickup, reconcile_availability_per_packet
from data_lake.root import DataLakeRoot, DataLakeRootError


@pytest.mark.parametrize("index_size", [100, 1000, 3000])
@pytest.mark.parametrize("operation", ["snapshot", "pickup", "reconcile"])
def test_scoped_reads_do_not_scale_with_global_index(tmp_path, monkeypatch, index_size, operation):
    root = DataLakeRoot.for_test(tmp_path / "lake")
    avail = root.path / "indexes" / "availability"
    avail.mkdir(parents=True, exist_ok=True)
    selected = f"{0:026d}"
    for n in range(index_size):
        pid = f"{n:026d}"
        (avail / f"{pid}.json").write_text(
            json.dumps({"packet_id": pid, "source_family": "reddit"}), encoding="utf-8"
        )
    reads = []
    tombstone_calls = 0
    original_read = Path.read_text
    original_tombstones = root.tombstoned_packet_ids

    def count_read(path, *args, **kwargs):
        if path.parent == avail:
            reads.append(path.name)
        return original_read(path, *args, **kwargs)

    def count_tombstones():
        nonlocal tombstone_calls
        tombstone_calls += 1
        return original_tombstones()

    original_glob = Path.glob

    def forbid_global_index_scan(path, pattern, *args, **kwargs):
        assert path != avail, "scoped operation enumerated the global availability index"
        return original_glob(path, pattern, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", count_read)
    monkeypatch.setattr(Path, "glob", forbid_global_index_scan)
    monkeypatch.setattr(root, "tombstoned_packet_ids", count_tombstones)
    scope = [selected, selected]  # duplicate requests must not duplicate reads/work
    if operation == "snapshot":
        assert [e["packet_id"] for e in root.snapshot_public_availability(scope_packet_ids=scope)] == [selected]
    elif operation == "pickup":
        assert [item.raw_anchor for item in pickup(
            root, ack_namespace="projection_ig",
            obligation_fn=lambda _: {"obligation_schema": 1, "consumer": "io-test"},
            reconcile=False, scope_packet_ids=scope,
        )] == [selected]
    else:
        # Isolate public-read cost from raw regeneration (covered by seam tests).
        monkeypatch.setattr(root, "record_availability", lambda _: None)
        assert reconcile_availability_per_packet(root, scope_packet_ids=scope) == []
    assert reads == [f"{selected}.json"]
    assert tombstone_calls == 1


@pytest.mark.parametrize("bad_entry", ["{bad json", "[]", '{"packet_id": "wrong"}'])
def test_corrupt_selected_entry_fails_before_family_filter(tmp_path, bad_entry):
    root = DataLakeRoot.for_test(tmp_path / "lake")
    avail = root.path / "indexes" / "availability"
    avail.mkdir(parents=True, exist_ok=True)
    pid = "0" * 26
    (avail / f"{pid}.json").write_text(bad_entry, encoding="utf-8")
    with pytest.raises((ValueError, DataLakeRootError)):
        list(pickup(root, ack_namespace="projection_ig", obligation_fn=lambda _: {},
                    source_family="instagram", reconcile=False, scope_packet_ids=[pid]))


def test_unrelated_corruption_does_not_poison_scope_but_unscoped_still_fails(tmp_path):
    root = DataLakeRoot.for_test(tmp_path / "lake")
    avail = root.path / "indexes" / "availability"
    avail.mkdir(parents=True, exist_ok=True)
    selected, other = "0" * 26, "1" * 26
    (avail / f"{selected}.json").write_text(json.dumps({"packet_id": selected}), encoding="utf-8")
    (avail / f"{other}.json").write_text("{broken", encoding="utf-8")
    assert root.snapshot_public_availability(scope_packet_ids=[selected]) == [{"packet_id": selected}]
    with pytest.raises(ValueError):
        root.snapshot_public_availability()
    with pytest.raises(ConsumptionSeamError, match="missing from public availability"):
        list(pickup(root, ack_namespace="projection_ig", obligation_fn=lambda _: {},
                    reconcile=False, scope_packet_ids=["2" * 26]))


@pytest.mark.parametrize("packet_id", ["../outside", "x", "0" * 25 + "/"])
def test_scoped_keys_cannot_escape_index(tmp_path, packet_id):
    root = DataLakeRoot.for_test(tmp_path / "lake")
    with pytest.raises(DataLakeRootError):
        root.snapshot_public_availability(scope_packet_ids=[packet_id])
