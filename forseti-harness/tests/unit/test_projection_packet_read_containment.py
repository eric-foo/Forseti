"""Regression: projection packet reads are contained to the packet directory.

2026-07-17 hardening. Before this, only ``ig_projection`` rejected a
``relative_packet_path`` that was absolute or escaped the packet root via
``../``; basenotes/parfumo read with no containment check at all and
fragrantica checked existence only. The guard now lives once in
``source_capture.projection_shared`` and every projection surface's
``_read_packet_directory`` must BE the shared, guarded reader — the identity
tests below fail if any surface regresses to a private copy.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import source_capture.basenotes_projection as basenotes_projection
import source_capture.fragrantica_projection as fragrantica_projection
import source_capture.google_ads_transparency_projection as google_ads_transparency_projection
import source_capture.ig_projection as ig_projection
import source_capture.parfumo_projection as parfumo_projection
from source_capture import projection_shared
from source_capture.projection_shared import resolve_preserved_file_path


def test_absolute_preserved_path_rejected(tmp_path: Path) -> None:
    packet_dir = tmp_path / "pkt"
    packet_dir.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(ValueError, match="must be packet-relative"):
        resolve_preserved_file_path(packet_dir, "file_01", str(outside))


def test_parent_escaping_preserved_path_rejected(tmp_path: Path) -> None:
    packet_dir = tmp_path / "pkt"
    packet_dir.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    # The escape target EXISTS: only the containment boundary can reject it.
    with pytest.raises(ValueError, match="escapes packet directory"):
        resolve_preserved_file_path(packet_dir, "file_01", "../outside.html")


def test_contained_preserved_path_resolves(tmp_path: Path) -> None:
    packet_dir = tmp_path / "pkt"
    (packet_dir / "raw").mkdir(parents=True)
    target = packet_dir / "raw" / "page.html"
    target.write_text("page", encoding="utf-8")
    resolved = resolve_preserved_file_path(packet_dir, "file_01", "raw/page.html")
    assert resolved == target.resolve()


def test_contained_but_missing_preserved_path_raises_not_found(tmp_path: Path) -> None:
    packet_dir = tmp_path / "pkt"
    packet_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        resolve_preserved_file_path(packet_dir, "file_01", "raw/missing.html")


@pytest.mark.parametrize(
    "surface",
    [
        basenotes_projection,
        parfumo_projection,
        fragrantica_projection,
        google_ads_transparency_projection,
        ig_projection,
    ],
    ids=["basenotes", "parfumo", "fragrantica", "google_ads", "ig"],
)
def test_every_projection_surface_uses_the_contained_reader(surface) -> None:
    assert surface._read_packet_directory is projection_shared.read_packet_directory
