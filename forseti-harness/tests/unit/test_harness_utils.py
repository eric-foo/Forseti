"""Byte-exact file hashing without file-sized allocations."""
from __future__ import annotations

import hashlib
import tracemalloc
from pathlib import Path

import pytest

from harness_utils import hash_file


@pytest.mark.parametrize("size", [0, 1, 65535, 65536, 65537, 24 * 1024 * 1024])
def test_hash_file_preserves_all_bytes_with_bounded_memory(tmp_path: Path, size: int) -> None:
    payload = (bytes(range(256)) * ((size + 255) // 256))[:size]
    path = tmp_path / "bytes.bin"
    path.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    tracemalloc.start()
    try:
        actual = hash_file(path)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert actual == expected
    assert peak < 1024 * 1024


@pytest.mark.parametrize("directory", [False, True])
def test_hash_file_keeps_read_failures_visible(tmp_path: Path, directory: bool) -> None:
    path = tmp_path / "unreadable"
    if directory:
        path.mkdir()
    with pytest.raises(OSError):
        hash_file(path)
