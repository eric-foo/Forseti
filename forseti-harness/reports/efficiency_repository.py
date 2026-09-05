"""Read-only logical repository bytes at a commit, plus bounded current log growth.

Git blob sizes count every tracked path, not physical packs or deduplicated storage.
Instruction source bytes are static source size, never measured context tokens.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *arguments], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20).stdout


def _log_size(repo: Path) -> tuple[int, int, int]:
    """Only descend the default measurement directory; never follow links/junctions."""
    directory = repo
    for part in ("forseti-harness", "memory", "logs", "efficiency"):
        directory = directory / part
        if directory.is_symlink() or directory.is_junction():
            return 0, 0, 1
        if not directory.exists():
            return 0, 0, 0
    if not directory.is_dir():
        raise ValueError("default measurement log location is not a directory")
    byte_count = file_count = links = 0
    pending = [directory]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_symlink() or Path(entry.path).is_junction():
                    links += 1
                elif entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    byte_count += entry.stat(follow_symlinks=False).st_size
                    file_count += 1
    return byte_count, file_count, links


def repository_size(repo: Path, revision: str = "HEAD") -> dict:
    """Measure exact committed path bytes and separately count current measurement logs."""
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("revision must be a nonempty Git commit reference")
    repo = Path(os.fsdecode(_git(Path(repo), "rev-parse", "--show-toplevel").strip())).resolve()
    commit = _git(repo, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}").decode("ascii").strip()
    if len(commit) not in (40, 64) or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Git did not resolve a commit object id")
    result = {"revision": commit, "tracked_bytes": 0, "tracked_file_count": 0,
              "regular_file_count": 0, "symlink_count": 0, "symlink_blob_bytes": 0,
              "gitlink_count": 0, "instruction_source_bytes": 0,
              "instruction_source_file_count": 0}
    tree = _git(repo, "ls-tree", "--full-tree", "-r", "-l", "-z", commit)
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, _object_id, raw_size = metadata.split()
        if mode == b"160000" and kind == b"commit":
            result["gitlink_count"] += 1
            continue
        if kind != b"blob" or mode not in (b"100644", b"100755", b"120000"):
            raise ValueError("unexpected tracked Git entry mode or object type")
        size = int(raw_size)
        if size < 0:
            raise ValueError("negative Git blob size")
        result["tracked_bytes"] += size
        result["tracked_file_count"] += 1
        if mode == b"120000":
            result["symlink_count"] += 1
            result["symlink_blob_bytes"] += size
            continue
        result["regular_file_count"] += 1
        if (path in (b"AGENTS.md", b"CLAUDE.md") or
                (path.startswith(b".agents/workflow-overlay/") and path.endswith(b".md"))):
            result["instruction_source_bytes"] += size
            result["instruction_source_file_count"] += 1
    log_bytes, log_files, log_links = _log_size(repo)
    result.update(measurement_log_bytes=log_bytes, measurement_log_file_count=log_files,
                  measurement_log_symlink_count=log_links)
    result["notes"] = [
        "Tracked bytes are logical Git blob bytes per committed path, not physical Git pack size.",
        "Tracked file count includes symlink blobs; gitlinks are counted separately and their contents are excluded.",
        "Instruction source bytes are static source size, not measured input tokens or actual loaded context.",
        "Measurement logs describe the current default directory, independent of the selected commit; links and junctions are excluded.",
    ]
    return result
