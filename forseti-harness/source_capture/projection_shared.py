"""Shared mechanical helpers for the source_capture projection surfaces.

Owning home for helper bodies that were byte-identical across projection
modules (basenotes / parfumo / fragrantica / ig / reddit / retail grid /
retail PDP). Consolidation only: each function preserves the exact behavior
of the private copies it replaces, and per-surface POLICY (forbidden-field
token sets, surface admission, row shaping) stays in each surface module --
this module carries mechanics, never per-surface vocabulary.

Two deliberately distinct forbidden-field algorithms live here side by side
(token membership vs normalized-padding pattern). They are NOT interchangeable
and must not be merged: each adopting surface keeps the algorithm it shipped
with, parameterized by its own token set.

The shared-helper duplication gate
(``.agents/hooks/check_shared_helper_duplication.py``) names this module as
the owning home for the projection helper names it guards.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from source_capture.models import SourceCapturePacket


def is_forbidden_field_token_match(key: str, tokens: frozenset[str]) -> bool:
    """Token-membership forbidden-field check (ig / reddit / retail surfaces).

    Matches when a token equals the normalized key, is one of its ``_``-split
    parts, or is a substring of the normalized key.
    """
    normalized = key.lower().replace("-", "_")
    parts = normalized.split("_")
    return any(
        token == normalized or token in parts or token in normalized
        for token in tokens
    )


def is_forbidden_field_pattern_match(key: str, tokens: frozenset[str]) -> bool:
    """Normalized-padding forbidden-field check (fragrance trio surfaces).

    Collapses non-alphanumerics to ``_`` and matches each token only as a
    whole ``_``-delimited segment of the padded key.
    """
    normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
    padded = f"_{normalized}_"
    return any(f"_{token}_" in padded for token in tokens)


def first_match(text: str, pattern: str, *, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    return html.unescape(match.group(1)).strip() if match else None


def normalized_html_text(value: str | None) -> str | None:
    """HTML fragment -> whitespace-normalized text ('' stays '', not None)."""
    if value is None:
        return None
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</p\s*>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    normalized = re.sub(r"\s+", " ", html.unescape(value)).strip()
    return normalized


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def canonical_old_reddit_thread_url(href: str) -> str | None:
    """Canonicalize an old-reddit thread href to a trailing-slash comments URL.

    Adopted body of the private copy in
    ``capture_spine.reddit_subreddit_grid.grid_projection``. A relative
    ``/r/`` href is absolutized to ``old.reddit.com``; anything not under
    ``old.reddit.com/r/`` or without ``/comments/`` returns ``None``; the
    query/fragment is dropped and a trailing slash enforced.

    Two private copies deliberately do NOT adopt this home:
    ``capture_spine.reddit_candidate_intake.projection`` keeps a byte-identical
    body but is contract-isolated from ``source_capture`` (so it cannot import
    this module), and ``source_capture.screening_extraction`` diverges
    behaviorally (it also rewrites ``www.reddit.com`` -> ``old.reddit.com``).
    Both keep a local copy with a ``# helper-delta:`` comment.
    """
    stripped = href.strip()
    if stripped.startswith("/r/"):
        stripped = f"https://old.reddit.com{stripped}"
    if not stripped.startswith("https://old.reddit.com/r/"):
        return None
    stripped = stripped.split("#", 1)[0].split("?", 1)[0]
    if "/comments/" not in stripped:
        return None
    if not stripped.endswith("/"):
        stripped += "/"
    return stripped


def canonical_www_reddit_thread_url(href: str) -> str | None:
    """Canonicalize a new-Reddit thread href to a trailing-slash comments URL.

    Same contract as the old-Reddit sibling above, against ``www.reddit.com``.
    New-Reddit listing rows carry both a relative ``permalink`` and an absolute
    ``content-href``, and a cross-posted row's href legitimately names another
    subreddit, which is honest provenance rather than traversal.

    Deliberately NOT folded into the old-Reddit function with a host parameter:
    the two hosts are different capture surfaces with different block postures,
    and a shared host-switching helper would let a caller silently emit one
    surface's URLs from the other's capture.
    """
    stripped = href.strip()
    if stripped.startswith("/r/"):
        stripped = f"https://www.reddit.com{stripped}"
    if not stripped.startswith("https://www.reddit.com/r/"):
        return None
    stripped = stripped.split("#", 1)[0].split("?", 1)[0]
    if "/comments/" not in stripped:
        return None
    if not stripped.endswith("/"):
        stripped += "/"
    return stripped


def resolve_preserved_file_path(packet_dir: Path, file_id: str, relative_packet_path: str) -> Path:
    """Resolve a preserved file strictly INSIDE the packet directory.

    Security boundary (2026-07-17 hardening): an absolute
    ``relative_packet_path`` or one that escapes the packet root (``../``)
    is rejected with ``ValueError`` before any filesystem read. Body taken
    verbatim from the one guarded implementation (``ig_projection``); the
    other projection surfaces previously read without containment.
    """
    relative_path = Path(relative_packet_path)
    if relative_path.is_absolute():
        raise ValueError(f"preserved file path for {file_id} must be packet-relative: {relative_packet_path}")
    packet_root = packet_dir.resolve()
    raw_path = (packet_dir / relative_path).resolve()
    try:
        raw_path.relative_to(packet_root)
    except ValueError as exc:
        raise ValueError(f"preserved file path for {file_id} escapes packet directory: {relative_packet_path}") from exc
    if not raw_path.exists():
        raise FileNotFoundError(f"preserved file not found for {file_id}: {raw_path}")
    return raw_path


def read_packet_directory(packet_or_manifest_path: Path) -> tuple[SourceCapturePacket, dict[str, bytes]]:
    """Load a source-capture packet manifest plus its preserved file bytes.

    Every preserved file is resolved through
    :func:`resolve_preserved_file_path`, so reads are contained to the
    packet directory for every adopting projection surface.
    """
    manifest_path = (
        packet_or_manifest_path / "manifest.json"
        if packet_or_manifest_path.is_dir()
        else packet_or_manifest_path
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    packet_dir = manifest_path.parent
    packet = SourceCapturePacket.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    raw_file_bytes_by_file_id: dict[str, bytes] = {}
    for preserved_file in packet.preserved_files:
        raw_path = resolve_preserved_file_path(
            packet_dir,
            preserved_file.file_id,
            preserved_file.relative_packet_path,
        )
        raw_file_bytes_by_file_id[preserved_file.file_id] = raw_path.read_bytes()
    return packet, raw_file_bytes_by_file_id
