from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

import yaml

HARNESS_VERSION = "v0_14"
MAPPING_TABLE_VERSION = "v0_14_mvp"
LABELING_RUBRIC_VERSION = "v0_14"
SCORER_VERSION = "step_a_v0"
NON_CLAIM_NOTICE = "plumbing works only; not judgment quality"
_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def utc_now_z() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_now_z_microseconds() -> str:
    """Like utc_now_z() but keeps microsecond precision (no truncation)."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def string_or_none(value: Any) -> str | None:
    """Coerce ``value`` to a non-empty string, else ``None``.

    Contract: a ``str`` is stripped and returned, or ``None`` when the
    stripped result is empty; an ``int`` (``bool`` excluded) is rendered
    with ``str()``; every other type -- including ``bool``, ``float``, and
    ``None`` -- returns ``None``.
    """
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def int_or_none(value: Any) -> int | None:
    """Coerce ``value`` to an ``int``, else ``None``.

    Contract: ``bool`` is rejected (``None``); an ``int`` passes through;
    a ``float`` is accepted only when integral (``value.is_integer()``);
    a ``str`` has commas removed and whitespace stripped, then parses only
    when the result ``isdigit()`` (so signed, decimal, or suffixed strings
    return ``None``); every other type returns ``None``.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.replace(",", "").strip()
        return int(stripped) if stripped.isdigit() else None
    return None


def bool_or_none(value: Any) -> bool | None:
    """Return ``value`` when it is exactly a ``bool``, else ``None``.

    Contract: no coercion -- truthy/falsy strings, ``0``/``1`` ints, and
    every other non-``bool`` value (including ``None``) return ``None``.
    """
    return value if isinstance(value, bool) else None


def append_residual_once(residuals: list[str], residual: str) -> None:
    """Append ``residual`` to ``residuals`` unless it is already present.

    Contract: order-preserving, first-occurrence-wins dedup by equality;
    the list is mutated in place and nothing is returned.
    """
    if residual not in residuals:
        residuals.append(residual)


@contextmanager
def staged_directory_publish(destination: Path) -> Iterator[Path]:
    """Build a complete directory off-tree, then publish it with one rename."""

    final_directory = destination.resolve()
    _require_empty_or_absent_directory(final_directory)
    final_directory.parent.mkdir(parents=True, exist_ok=True)
    staging_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{final_directory.name}.staging-",
            dir=final_directory.parent,
        )
    )

    try:
        yield staging_directory
        _require_empty_or_absent_directory(final_directory)
        if final_directory.exists():
            final_directory.rmdir()
        os.rename(staging_directory, final_directory)
    except BaseException:
        shutil.rmtree(staging_directory, ignore_errors=True)
        raise


def _require_empty_or_absent_directory(destination: Path) -> None:
    if not destination.exists():
        return
    if not destination.is_dir():
        raise ValueError(f"output path is not a directory: {destination}")
    if any(destination.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty output directory: {destination}")


def canonical_yaml_dump(data: Any) -> str:
    normalized = _normalize_for_yaml(data)
    return yaml.safe_dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
        line_break="\n",
    )


def canonical_yaml_hash(data: Any) -> str:
    return sha256_text(canonical_yaml_dump(data))


def load_yaml_file(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to load YAML file {path}: {exc}") from exc


def load_yaml_documents(path: Path) -> list[Any]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as handle:
            return [document for document in yaml.safe_load_all(handle) if document is not None]
    except Exception as exc:
        raise ValueError(f"Failed to load YAML document stream {path}: {exc}") from exc


def write_yaml_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_yaml_dump(data), encoding="utf-8", newline="\n")


def append_yaml_document(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("---\n")
        handle.write(canonical_yaml_dump(data))


def split_frontmatter(document: str) -> tuple[dict[str, Any], str]:
    lines = document.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("participant_packet.md is missing YAML frontmatter")

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index is None:
        raise ValueError("participant_packet.md frontmatter is not closed")

    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    loaded = yaml.safe_load(frontmatter) or {}
    if not isinstance(loaded, dict):
        raise ValueError("participant_packet.md frontmatter must decode to a mapping")
    return loaded, body


def _encode_crockford(value: int, length: int) -> str:
    output = []
    for _ in range(length):
        output.append(_CROCKFORD_BASE32[value & 31])
        value >>= 5
    return "".join(reversed(output))


def generate_ulid() -> str:
    timestamp_ms = int(time.time() * 1000)
    randomness = secrets.randbits(80)
    return f"{_encode_crockford(timestamp_ms, 10)}{_encode_crockford(randomness, 16)}"


def _normalize_for_yaml(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalize_for_yaml(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_yaml(item) for item in value]
    return value
