#!/usr/bin/env python3
"""Bidirectional retrieval link-check: repo map <-> disk, open_next <-> disk,
folder coverage, inline body links <-> disk, and live-router targets <-> disk.

WHAT THIS DOES
  Five mechanically-checkable invariants that keep the repo map, retrieval
  headers, inline markdown links, and selected live routers honest without
  reading product-authority sources:

  C1  MAP->DISK: every repo-relative path mentioned in the repo map or any
      submap must exist on disk.  Exempt: lines whose surrounding text says
      "does not exist yet" or "created on first".

  C2  OPEN_NEXT->DISK: every path listed under open_next: in any .md file
      under docs/ or .agents/ (skipping _scratch/, _inbox/, node_modules)
      must exist on disk.

  C3  FOLDER COVERAGE: every directory under docs/ (recursive) that has >=3
      .md files directly must appear as a substring in the repo map (any of
      its files or the dir path itself) OR have a map line containing the
      phrase "not retrieval-indexed".  Exempt: docs/_inbox and any dir whose
      path contains "_scratch".

  C4  INLINE-LINK->DISK: every inline markdown link or image link in the body
      of any .md file under docs/ and .agents/ (same walk, same skip rules)
      whose target is a relative/repo path must resolve to a file on disk.
      Out of scope: external URLs (http/https/mailto/ftp), protocol-relative
      (//...), pure same-file anchors (#...).  Reference-style links
      ([text][ref] + [ref]: url) are out of scope for v0 (named limitation).
      Exempt: same line-level markers as C1/C2 ("does not exist yet",
      "not retrieval-indexed").  Trailing comment "# nonresolving:<reason>"
      exempts a link and counts it as annotated debt.

  C5  LIVE-ROUTER->DISK: every live row in the authoritative-target column of
      Artifact Roles -> Role Bindings and the Doctrine Index product-spine
      table must carry a repo-rooted path that exists directly in the current
      tree. Moved-path indexes do not satisfy a live router.

WHY (enforcement placement)
  The repo map and open_next headers are written by agents and humans.  Path
  rot happens silently: a file is renamed, a folder is added, a path is
  copy-pasted wrong.  A check run in CI and pre-commit catches the rot at the
  moment the diff lands, not after the next reader is confused.  Inline body
  links carry the same rot risk.

HARD BOUNDARY
  Read-only.  No git calls.  No writes.  An unexpected internal exception is
  the GATE FAIL bucket in gating modes (validation-gates.md; EP-35 FIND-02
  class sweep): --strict/--strict-inline/--selftest exit 1 on internal error;
  advisory modes (--check, --report-orca) print the error and exit 0 so a
  checker bug never bricks the agent.  The repo-root infra-gap fail-open is
  unchanged.  --check always exits 0.

  Moved-path indexes are resolution aids, not exemptions: an old path may pass
  only when an indexed successor path resolves in the current tree.

MODES
  check_map_links.py --strict         CI gate; print findings; exit 1 if any (C1-C5), else 0
  check_map_links.py --strict-inline  alias for --strict (C4/C5 included; kept for caller compat)
  check_map_links.py --check          human-readable; always exit 0
  check_map_links.py --selftest       pure-function cases; exit per pass/fail

REGISTRATION (.github/workflows/ci.yml, after the test step)
  - name: retrieval link check
    run: python .agents/hooks/check_map_links.py --strict
"""
from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hooklib import repo_root  # noqa: E402  (sys.path pin must precede the import)


# ---------------------------------------------------------------------------
# C1 helpers: path extraction from a markdown line
# ---------------------------------------------------------------------------

# Token pattern: starts with one of the known prefixes, contains no spaces,
# optionally backtick-quoted or bare.  We also strip trailing punctuation.
_PATH_PREFIXES = (
    "docs/", ".agents/", ".github/", "forseti-harness/", "orca-harness/",
    "forseti/", "forseti/product/",
    "AGENTS.md", "CLAUDE.md",
)

_TOKEN_RE = re.compile(
    r"`([^`\s]+)`"           # backtick-quoted token
    r"|"
    r"(?<![`\w/])([\w.\-][^\s`\"'<>|,)]+)"  # bare word starting with word char or dot
)

_TRAILING_PUNCT = re.compile(r"[.,;:)\]>\"']+$")

_MOVED_INDEX_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")


@lru_cache(maxsize=8)
def load_moved_paths(root_key: str) -> tuple[dict[str, str], dict[str, str]]:
    """Load generated moved-path indexes under docs/migration/.

    Returns (exact, prefixes). Exact entries map old file paths to successor
    paths. Prefix entries come only from rows whose old/new values both end in
    "/" and let directory-level legacy paths resolve without mass-rewriting
    historical artifacts.
    """
    root = Path(root_key)
    exact: dict[str, str] = {}
    prefixes: dict[str, str] = {}
    migration_root = root / "docs" / "migration"
    if not migration_root.is_dir():
        return exact, prefixes
    for index in sorted(migration_root.glob("**/moved_paths_index.md")):
        try:
            lines = index.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            match = _MOVED_INDEX_ROW_RE.match(line)
            if not match:
                continue
            old = match.group(1).strip()
            new = match.group(2).strip()
            if not old or old == "---" or new == "---":
                continue
            if old.endswith("/") and new.endswith("/"):
                prefixes[old] = new
            else:
                exact[old] = new
    return exact, prefixes


def resolve_moved_path(path: str, root: Path) -> str | None:
    """Return an indexed successor path, following short chains, else None."""
    original = path.replace("\\", "/").lstrip("./")
    candidate = original
    exact, prefixes = load_moved_paths(str(root))
    seen: set[str] = set()
    for _ in range(8):
        if candidate in seen:
            return None
        seen.add(candidate)
        if candidate in exact:
            candidate = exact[candidate]
            continue
        matched = False
        for old, new in sorted(prefixes.items(), key=lambda item: len(item[0]), reverse=True):
            if candidate == old.rstrip("/") or candidate.startswith(old):
                suffix = "" if candidate == old.rstrip("/") else candidate[len(old):]
                candidate = new + suffix
                matched = True
                break
        if matched:
            continue
        return candidate if candidate != original else None
    return None


def repo_path_exists(path: str, root: Path) -> bool:
    """True if a repo-relative path exists directly or via moved-path index."""
    norm = path.replace("/", os.sep)
    if (root / norm).exists():
        return True
    successor = resolve_moved_path(path, root)
    return bool(successor and (root / Path(successor.replace("/", os.sep))).exists())


def extract_paths_from_line(line: str) -> list[str]:
    """Extract repo-relative path tokens from one markdown line.

    Returns only tokens that begin with a known repo-relative prefix.
    Strips trailing punctuation.  Ignores tokens with spaces.
    Skips glob patterns (containing '*') and anchor-only suffixes ('#...').
    Strips fragment anchors ('#...') so 'source-loading.md#section' checks
    the base file only.

    Pure function (testable).
    """
    results: list[str] = []
    for m in _TOKEN_RE.finditer(line):
        raw = m.group(1) or m.group(2)
        if not raw:
            continue
        token = _TRAILING_PUNCT.sub("", raw)
        if not token:
            continue
        if not any(token.startswith(p) for p in _PATH_PREFIXES):
            continue
        # Skip glob patterns (contain '*' or '?')
        if "*" in token or "?" in token:
            continue
        # Strip fragment anchor (check base file only)
        if "#" in token:
            token = token.split("#")[0]
        if not token:
            continue
        results.append(token)
    return results


def is_exempt_line(line: str) -> bool:
    """True if the line contains an exemption marker for C1."""
    lower = line.lower()
    return "does not exist yet" in lower or "created on first" in lower


# ---------------------------------------------------------------------------
# C5 helpers: selected live-router table targets
# ---------------------------------------------------------------------------

_LIVE_ROUTER_TABLES = (
    (".agents/workflow-overlay/artifact-roles.md", "## Role Bindings", 1),
    ("docs/decisions/forseti_doctrine_index_v0.md",
     "## Product-spine doctrine (`forseti/product/`)", 1),
)


def extract_router_table_rows(
    text: str, section_heading: str, target_column: int
) -> tuple[bool, list[tuple[str, list[str]]]]:
    """Return (section_found, [(row_label, repo-rooted target paths), ...]).

    Only Markdown table data rows inside the exact H2 section are returned.
    Header and separator rows are skipped. A data row with no repo-rooted path
    remains in the result with an empty target list so C5 can fail visibly.
    """
    lines = text.splitlines()
    try:
        start = lines.index(section_heading)
    except ValueError:
        return False, []

    rows: list[tuple[str, list[str]]] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if cells[0].lower() in {"role", "doctrine"}:
            continue
        row_label = cells[0] or "<unlabeled live-router row>"
        targets = (
            extract_paths_from_line(cells[target_column])
            if target_column < len(cells)
            else []
        )
        rows.append((row_label, targets))
    return True, rows


# ---------------------------------------------------------------------------
# C2 helpers: open_next parsing from header text
# ---------------------------------------------------------------------------

def parse_open_next(header_text: str) -> tuple[list[str], int]:
    """Parse path entries from the open_next: block of a YAML retrieval header.

    header_text is the first 40 lines of the file joined into a single string.
    Returns (entries, nonresolving_count) where:
      - entries: path-like entries that are NOT annotated with a "nonresolving:"
        trailing comment (contains "/" or ends with ".md").
      - nonresolving_count: number of path-like entries whose trailing comment
        (after " # ") starts with "nonresolving:" -- these are skipped from the
        existence check and counted as annotated debt.

    Strips surrounding quotes and reads trailing comments (after " # ").
    An entry with "# nonresolving: <reason>" is skipped but counted.
    An entry with "# <other comment>" is still checked.
    An entry with no comment is checked.

    Pure function (testable).
    """
    entries: list[str] = []
    nonresolving_count = 0
    in_open_next = False
    in_yaml_block = False

    for line in header_text.splitlines():
        stripped = line.strip()

        # Detect start/end of the YAML fenced block (``` yaml or ```)
        if stripped.startswith("```"):
            if not in_yaml_block and ("yaml" in stripped.lower() or stripped == "```"):
                in_yaml_block = True
                continue
            elif in_yaml_block:
                in_yaml_block = False
                in_open_next = False
                continue
            continue

        if not in_yaml_block:
            continue

        if stripped.startswith("open_next:"):
            in_open_next = True
            continue

        if in_open_next:
            # A new top-level key ends the open_next block
            if stripped and not stripped.startswith("-") and ":" in stripped and not stripped.startswith("#"):
                key = stripped.split(":")[0].strip()
                if not key.startswith("-"):
                    in_open_next = False
                    continue

            if stripped.startswith("- "):
                raw = stripped[2:].strip()
                # Extract trailing comment (after " # ")
                comment_pos = raw.find(" # ")
                comment = ""
                if comment_pos != -1:
                    comment = raw[comment_pos + 3:].strip()
                    raw = raw[:comment_pos].strip()
                # Strip surrounding quotes
                entry = raw.strip("\"'").strip()
                if not entry:
                    continue
                # Only handle path-like entries
                if not ("/" in entry or entry.endswith(".md")):
                    continue  # non-path entries like "owner decision" are skipped
                # Check for nonresolving annotation: skip existence check, count as debt
                if comment.startswith("nonresolving:"):
                    nonresolving_count += 1
                    continue
                entries.append(entry)

    return entries, nonresolving_count


# ---------------------------------------------------------------------------
# C3 helpers: folder coverage decision
# ---------------------------------------------------------------------------

# Structural-root prefixes too shallow to be a navigation anchor: they never
# confer coverage on their own (anti-vacuity). Coverage requires a NON-root
# ancestor area to be declared. See docs/decisions/forseti_repo_map_architecture_mgt_v0.md.
_COVERAGE_ROOT_PREFIXES = frozenset({
    "forseti", "forseti/product", "forseti/product/spines",
    "forseti/product/satellites", "forseti/product/case_families", "forseti/product/shared",
    "docs", ".agents", "forseti-harness", "orca-harness",
})
# NOTE: .agents/workflow-overlay is a *declared area* that holds docs directly
# (map row exists), so it confers coverage and is NOT a structural root.

# A canonical coverage entry is a backticked path token in the FIRST cell of a
# map/submap table row ("| `path` | ... |"). Prose, answer-cell paths, and
# "add X later" debt notes are deliberately NOT canonical entries.
_FIRST_CELL_PATH_RE = re.compile(r"^\|\s*`([A-Za-z0-9_./-]+?)/?`\s*\|")


def _canonical_map_tokens(map_text: str) -> set[str]:
    """First-cell backticked path tokens from map/submap rows (normalized, no trailing slash)."""
    return {
        m.group(1).rstrip("/")
        for line in map_text.splitlines()
        if (m := _FIRST_CELL_PATH_RE.match(line))
    }


def dir_is_covered(rel_dir: str, map_text: str) -> bool:
    """True if rel_dir is reachable from the map under the MGT reachability
    invariant: some canonical first-cell path token is an ANCESTOR-or-self of
    rel_dir and is NOT a structural root.

    Reachability semantics (docs/decisions/forseti_repo_map_architecture_mgt_v0.md):
    a folder is covered iff it or an ancestor *area* is declared. Structural roots
    (forseti/product, docs, ...) never confer coverage (else the gate is vacuous); a
    sibling, a child (child-covers-parent), prose, an answer-cell path, or a debt
    note never confer it either.

    Pure function (testable).
    """
    rel = rel_dir.rstrip("/")
    for e in _canonical_map_tokens(map_text):
        if e in _COVERAGE_ROOT_PREFIXES:
            continue
        if rel == e or rel.startswith(e + "/"):
            return True
    return False


def dir_is_exempt_coverage(rel_dir: str) -> bool:
    """True if this directory is exempt from C3 (docs/_inbox or contains _scratch)."""
    # Use forward-slash form for portability
    if rel_dir.startswith("docs/_inbox"):
        return True
    if "_scratch" in rel_dir:
        return True
    return False


# ---------------------------------------------------------------------------
# C4 helpers: inline link extraction and resolution
# ---------------------------------------------------------------------------

# Matches both image links and regular inline links:
#   ![alt](target)  or  [text](target)
# Does NOT match reference-style links ([text][ref]) -- out of scope for v0.
_INLINE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)")

# Extensions that indicate a checkable repo path even without a "/" separator.
_CHECKABLE_EXTS = (".md", ".py", ".yml", ".yaml", ".json", ".csv", ".png", ".svg")

# URL-scheme prefixes that mark external or out-of-scope targets.
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "//")


def extract_inline_links_from_line(line: str) -> list[str]:
    """Extract checkable path tokens from inline markdown links on one line.

    Handles:
      - Image links: ![alt](target)
      - Regular links: [text](target)
      - Optional title attribute: [x](path "Title") -> returns path only
        (first whitespace-delimited token inside the parens)
      - Fragment anchors: path#heading -> returns path with anchor stripped
      - Pure same-file anchors (#heading) -> skipped (out of scope)
      - External URLs (http/https/mailto/ftp) -> skipped (out of scope)
      - Protocol-relative (//...) -> skipped (out of scope)
      - Targets not containing "/" and not ending with a checkable extension
        are skipped (likely ids, colours, or other non-path tokens)

    Reference-style links ([text][ref] / [ref]: url) are out of scope for v0.

    Returns a list of raw path strings (anchor stripped, title stripped).
    Pure function (testable).
    """
    results: list[str] = []
    for m in _INLINE_LINK_RE.finditer(line):
        raw = m.group(1) or m.group(2)
        if not raw:
            continue
        # First whitespace-delimited token (strips optional title "Title" or 'T')
        tok = raw.split()[0] if raw.split() else raw
        # Skip external and protocol-relative targets
        if any(tok.startswith(p) for p in _EXTERNAL_PREFIXES):
            continue
        # Skip pure same-file anchors
        if tok.startswith("#"):
            continue
        # Strip fragment anchor (check base path only)
        path = tok.split("#")[0]
        if not path:
            continue  # pure anchor after stripping
        # Only check paths that look like repo paths:
        # must contain "/" or end with a known checkable extension
        if not ("/" in path or any(path.endswith(e) for e in _CHECKABLE_EXTS)):
            continue
        results.append(path)
    return results


def is_exempt_inline_line(line: str) -> bool:
    """True if the line carries an exemption marker for C4.

    Same markers as C1/C2: 'does not exist yet' or 'not retrieval-indexed'.
    Pure function (testable).
    """
    lower = line.lower()
    return "does not exist yet" in lower or "not retrieval-indexed" in lower


def inline_link_is_nonresolving(line: str, path_token: str) -> bool:
    """True if the line has a trailing comment '# nonresolving:' AFTER the link
    that contains path_token.  We check for the comment anywhere on the line
    since multiple links on one line are rare; the annotation covers the line.

    Pure function (testable).
    """
    # Find the link that contains this path token
    idx = line.find(path_token)
    if idx == -1:
        return False
    rest = line[idx + len(path_token):]
    # Look for trailing comment after the closing paren of the link
    comment_match = re.search(r"#\s*nonresolving\s*:", rest, re.IGNORECASE)
    return comment_match is not None


def inline_link_exists(path: str, linking_file: Path, root: Path) -> bool:
    """True if path resolves to an existing file.

    Resolution order (mirrors the spec):
      1. path relative to linking_file's directory
      2. path relative to repo root

    Pure function given that Path.exists() is the only I/O.
    """
    # Normalise to OS separators
    norm = path.replace("/", os.sep)
    # 1. Relative to the linking file's directory
    candidate_rel = linking_file.parent / norm
    if candidate_rel.exists():
        return True
    # 2. Relative to repo root, including moved-path successor indexes
    if repo_path_exists(path, root):
        return True
    return False


# ---------------------------------------------------------------------------
# Finding type
# ---------------------------------------------------------------------------

class Finding(NamedTuple):
    check: str     # "C1", "C2", "C3", "C4", "C5"
    source: str    # which file reported the finding
    detail: str    # human-readable detail


# ---------------------------------------------------------------------------
# Main scanning logic
# ---------------------------------------------------------------------------

def collect_map_files(root: Path) -> list[Path]:
    """Return the repo map and any *submap*.md files under docs/workflows/."""
    candidates: list[Path] = []
    map_path = root / "docs" / "workflows" / "forseti_repo_map_v0.md"
    if map_path.exists():
        candidates.append(map_path)
    workflows = root / "docs" / "workflows"
    if workflows.is_dir():
        for f in workflows.iterdir():
            if f.is_file() and "submap" in f.name.lower() and f.name.endswith(".md"):
                if f != map_path:
                    candidates.append(f)
    return candidates


def load_map_text(map_files: list[Path]) -> str:
    """Concatenate all map file content into one string for C3 coverage checks."""
    parts: list[str] = []
    for f in map_files:
        try:
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(parts)


def run_c1(root: Path, map_files: list[Path]) -> list[Finding]:
    """C1: every path mentioned in map files must exist on disk."""
    findings: list[Finding] = []
    for map_file in map_files:
        try:
            text = map_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel_source = map_file.relative_to(root).as_posix()
        for line in text.splitlines():
            if is_exempt_line(line):
                continue
            for token in extract_paths_from_line(line):
                if not repo_path_exists(token, root):
                    findings.append(Finding(
                        check="C1",
                        source=rel_source,
                        detail="path in map does not exist on disk: %s" % token,
                    ))
    return findings


def run_c2(root: Path, search_roots: list[Path] | None = None) -> tuple[list[Finding], int]:
    """C2: every open_next path in any .md file under docs/ and .agents/ must exist.

    Returns (findings, total_nonresolving) where total_nonresolving is the
    sum of all annotated nonresolving entries across all scanned files.

    search_roots defaults to [docs/, .agents/] -- the live strict scope, left
    byte-for-byte unchanged. The Forseti product report mode (--report-forseti, or legacy --report-orca) passes
    [forseti/] to reuse this exact predicate over the product corpus WITHOUT
    touching the strict path (frozen predicate = strict-minus-exit-0).
    """
    c2, count, _, _ = _run_markdown_checks(root, search_roots, inline=False)
    return c2, count


def _run_markdown_checks(root: Path, search_roots: list[Path] | None = None,
                         *, headers: bool = True, inline: bool = True
                         ) -> tuple[list[Finding], int, list[Finding], int]:
    """Read admitted Markdown once, keeping C2/C4 findings and debt separate."""
    c2: list[Finding] = []
    c4: list[Finding] = []
    c2_nonresolving = 0
    c4_nonresolving = 0
    if search_roots is None:
        search_roots = [root / "docs", root / ".agents"]

    for search_root in search_roots:
        if not search_root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(search_root):
            # Prune excluded directories in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in ("_scratch", "_inbox", "node_modules")
                and "_scratch" not in d
            ]
            for fname in filenames:
                if not fname.endswith(".md"):
                    continue
                fpath = Path(dirpath) / fname
                try:
                    with open(fpath, encoding="utf-8", errors="replace") as fh:
                        if inline:
                            text = fh.read()
                            # C2 counts physical newline-delimited lines; C4
                            # retains splitlines()'s broader line boundaries.
                            header_text = "\n".join(text.split("\n")[:40])
                            lines = text.splitlines()
                        else:
                            lines = []
                            for i, line in enumerate(fh):
                                if i >= 40:
                                    break
                                lines.append(line.rstrip("\n"))
                            header_text = "\n".join(lines)
                except OSError:
                    continue

                rel_source = fpath.relative_to(root).as_posix()
                if headers:
                    entries, nonresolving = parse_open_next(header_text)
                    c2_nonresolving += nonresolving
                    for entry in entries:
                        if not repo_path_exists(entry, root):
                            c2.append(Finding(
                                check="C2",
                                source=rel_source,
                                detail="open_next path does not exist on disk: %s" % entry,
                            ))
                if inline:
                    for line in lines:
                        if is_exempt_inline_line(line):
                            continue
                        for path in extract_inline_links_from_line(line):
                            if inline_link_is_nonresolving(line, path):
                                c4_nonresolving += 1
                                continue
                            if not inline_link_exists(path, fpath, root):
                                c4.append(Finding(
                                    check="C4",
                                    source=rel_source,
                                    detail="inline link target does not exist on disk: %s" % path,
                                ))
    return c2, c2_nonresolving, c4, c4_nonresolving


def run_c3(root: Path, map_text: str, scan_root: Path | None = None,
           min_md: int = 3, check_label: str = "C3") -> list[Finding]:
    """C3: every docs/ subdir with >=3 .md files directly must appear in the map.

    scan_root defaults to docs/ and min_md to 3 -- the live strict predicate,
    left unchanged. The product report mode passes scan_root=forseti/product and
    min_md=1 (the HARDER-than-C3 coverage rule from W0: every product folder
    that CONTAINS a .md must be map-covered). Empty structure-ahead-of-content
    slots hold 0 .md and are skipped by the min_md floor, so they never
    false-fail.
    """
    findings: list[Finding] = []
    if scan_root is None:
        scan_root = root / "docs"
    if not scan_root.is_dir():
        return findings

    for dirpath, dirnames, filenames in os.walk(scan_root):
        # Prune _scratch from walk (don't descend, don't report)
        dirnames[:] = [d for d in dirnames if "_scratch" not in d]

        current = Path(dirpath)
        rel_dir = current.relative_to(root).as_posix()

        # The scanned root itself is not a coverable sub-folder (no ancestor
        # area can declare it); skip it so the forseti/product README root is not
        # spuriously flagged.
        if current == scan_root:
            continue

        if dir_is_exempt_coverage(rel_dir):
            continue

        md_count = sum(1 for f in filenames if f.endswith(".md"))
        if md_count < min_md:
            continue

        if not dir_is_covered(rel_dir, map_text):
            findings.append(Finding(
                check=check_label,
                source=rel_dir,
                detail=(
                    "folder has %d .md files but no map entry: %s"
                    % (md_count, rel_dir)
                ),
            ))
    return findings


def run_c4(root: Path, search_roots: list[Path] | None = None) -> tuple[list[Finding], int]:
    """C4: every inline markdown link/image-link in .md files under docs/ and
    .agents/ whose target is a relative/repo path must resolve to a file on
    disk.

    Returns (findings, total_nonresolving) where total_nonresolving counts
    links annotated with '# nonresolving:<reason>' (debt, not failures).

    Combined entrypoints share this scan with C2; standalone mode checks C4 only.
    search_roots defaults to [docs/, .agents/] (live strict scope, unchanged);
    the Forseti product report mode passes [forseti/].
    """
    _, _, c4, count = _run_markdown_checks(root, search_roots, headers=False)
    return c4, count


def run_c5(root: Path) -> list[Finding]:
    """C5: selected live-router table targets must exist directly on disk.

    This deliberately does not use repo_path_exists(): moved-path indexes are
    valid historical resolution aids for C1-C4, but a live router must name its
    current primary target directly.
    """
    findings: list[Finding] = []
    for source, section_heading, target_column in _LIVE_ROUTER_TABLES:
        source_path = root / Path(source.replace("/", os.sep))
        try:
            text = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(
                check="C5",
                source=source,
                detail="live router could not be read: %s" % exc,
            ))
            continue

        section_found, rows = extract_router_table_rows(
            text, section_heading, target_column
        )
        if not section_found:
            findings.append(Finding(
                check="C5",
                source=source,
                detail="live router section is missing: %s" % section_heading,
            ))
            continue
        if not rows:
            findings.append(Finding(
                check="C5",
                source=source,
                detail="live router section has no data rows: %s" % section_heading,
            ))
            continue

        for row_label, targets in rows:
            if not targets:
                findings.append(Finding(
                    check="C5",
                    source=source,
                    detail="live router row has no repo-rooted target: %s" % row_label,
                ))
                continue
            for target in targets:
                direct = root / Path(target.replace("/", os.sep))
                if not direct.exists():
                    findings.append(Finding(
                        check="C5",
                        source=source,
                        detail=("live router target does not exist directly: "
                                "%s -> %s" % (row_label, target)),
                    ))
    return findings


def run_all_checks(root: Path) -> tuple[list[Finding], int]:
    """Collect all checks, sharing one Markdown read pass between C2 and C4.

    Returns (findings, total_nonresolving) where total_nonresolving is the
    combined count of annotated nonresolving entries across C2 and C4
    (debt, not failures).

    All five checks feed into --strict and --check.
    """
    map_files = collect_map_files(root)
    map_text = load_map_text(map_files)
    findings: list[Finding] = []
    findings.extend(run_c1(root, map_files))
    c2_findings, c2_nonresolving, c4_findings, c4_nonresolving = _run_markdown_checks(root)
    findings.extend(c2_findings)
    findings.extend(run_c3(root, map_text))
    findings.extend(c4_findings)
    findings.extend(run_c5(root))
    total_nonresolving = c2_nonresolving + c4_nonresolving
    return findings, total_nonresolving


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def run_strict(root: Path) -> int:
    """--strict: CI gate.  Gates on C1/C2/C3/C4/C5.
    Print findings; exit 1 if any, else 0.
    """
    findings, nonresolving = run_all_checks(root)
    if findings:
        print("check_map_links --strict: %d finding(s)" % len(findings))
        for f in findings:
            print("  [%s] %s  ::  %s" % (f.check, f.source, f.detail))
        print("annotated nonresolving: %d (debt, not failures)" % nonresolving)
        return 1
    print("check_map_links --strict: OK (0 findings)")
    print("annotated nonresolving: %d (debt, not failures)" % nonresolving)
    return 0


def run_strict_inline(root: Path) -> int:
    """--strict-inline: alias for --strict (C4/C5 are already included).
    Kept for caller compatibility in case downstream automation uses this flag.
    """
    return run_strict(root)


def run_report_orca(root: Path) -> int:
    """Product-corpus report mode. ALWAYS exits 0.

    Frozen predicate (strict-minus-exit-0): computes EXACTLY the findings a
    future product-tree strict gate will enforce -- C2 open_next resolution, C4
    inline link resolution, and the harder-than-C3 folder coverage (every
    forseti/product/ folder with >=1 .md must be map-covered) -- but never gates.
    The live docs/+.agents/ --strict scope and exit behavior are untouched; the
    ratchet flips the exit only. Header/orphan debt over forseti/product/spines/**
    is reported by header_index, not here.
    """
    product_root = root / "forseti"
    if not product_root.is_dir():
        print("check_map_links --report-forseti: no forseti/ tree present; nothing to report")
        return 0

    roots = [product_root]
    map_text = load_map_text(collect_map_files(root))
    c2_findings, c2_nr, c4_findings, c4_nr = _run_markdown_checks(root, search_roots=roots)
    cov_findings = run_c3(root, map_text, scan_root=root / "forseti" / "product",
                          min_md=1, check_label="COV")
    findings = c2_findings + c4_findings + cov_findings
    nonresolving = c2_nr + c4_nr

    by_check: dict[str, int] = {}
    for f in findings:
        by_check[f.check] = by_check.get(f.check, 0) + 1

    print("check_map_links --report-forseti (REPORT MODE, exit 0; not a gate):")
    print("  scope: forseti/  |  predicate = strict-minus-exit-0 (ratchet flips exit only)")
    print("  open_next unresolved (C2):                         %d" % by_check.get("C2", 0))
    print("  inline links unresolved (C4):                      %d" % by_check.get("C4", 0))
    print("  folders w/ >=1 .md not map-covered (COV>C3):       %d" % by_check.get("COV", 0))
    print("  annotated nonresolving:                            %d (debt, not failures)" % nonresolving)
    print("  total report findings:                             %d" % len(findings))
    for f in findings:
        print("    [%s] %s  ::  %s" % (f.check, f.source, f.detail))
    return 0


def run_check(root: Path) -> int:
    """--check: human-readable; always exit 0."""
    findings, nonresolving = run_all_checks(root)
    c1 = [f for f in findings if f.check == "C1"]
    c2 = [f for f in findings if f.check == "C2"]
    c3 = [f for f in findings if f.check == "C3"]
    c4 = [f for f in findings if f.check == "C4"]
    c5 = [f for f in findings if f.check == "C5"]
    gate_findings = c1 + c2 + c3 + c4 + c5
    if not findings:
        print("check_map_links: OK -- map paths, open_next paths, folder coverage, inline links, and live-router targets passed.")
        print("annotated nonresolving: %d (debt, not failures)" % nonresolving)
        return 0
    print("check_map_links --check: %d finding(s)" % len(findings))
    print()
    if c1:
        print("C1  MAP->DISK  (%d)" % len(c1))
        for f in c1:
            print("  source: %s" % f.source)
            print("  detail: %s" % f.detail)
            print()
    if c2:
        print("C2  OPEN_NEXT->DISK  (%d)" % len(c2))
        for f in c2:
            print("  source: %s" % f.source)
            print("  detail: %s" % f.detail)
            print()
    if c3:
        print("C3  FOLDER COVERAGE  (%d)" % len(c3))
        for f in c3:
            print("  source: %s" % f.source)
            print("  detail: %s" % f.detail)
            print()
    if c4:
        c4_files = len(set(f.source for f in c4))
        print("C4  INLINE-LINK->DISK  (%d finding(s) across %d file(s))" % (len(c4), c4_files))
        for f in c4:
            print("  source: %s" % f.source)
            print("  detail: %s" % f.detail)
            print()
    if c5:
        print("C5  LIVE-ROUTER->DISK  (%d)" % len(c5))
        for f in c5:
            print("  source: %s" % f.source)
            print("  detail: %s" % f.detail)
            print()
    print("annotated nonresolving: %d (debt, not failures)" % nonresolving)
    return 0


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def selftest() -> int:
    """--selftest: pure-function cases.  Exit 0 on pass, 1 on fail."""
    ok = True

    # --- extract_paths_from_line cases ---
    epl_cases = [
        # (label, line, expected tokens)
        ("backtick path",
         "see `docs/workflows/forseti_repo_map_v0.md` for details",
         ["docs/workflows/forseti_repo_map_v0.md"]),
        ("bare path",
         "open docs/decisions/foo_v0.md before proceeding",
         ["docs/decisions/foo_v0.md"]),
        ("trailing comma",
         "see docs/product/core_spine/bar_v0.md, then decide",
         ["docs/product/core_spine/bar_v0.md"]),
        ("trailing paren",
         "see docs/product/core_spine/bar_v0.md) then decide",
         ["docs/product/core_spine/bar_v0.md"]),
        ("AGENTS.md bare",
         "see AGENTS.md for instructions",
         ["AGENTS.md"]),
        ("CLAUDE.md bare",
         "see CLAUDE.md for shim notes",
         ["CLAUDE.md"]),
        ("forseti-harness path",
         "`forseti-harness/ecr/__init__.py` is the entry",
         ["forseti-harness/ecr/__init__.py"]),
        ("legacy orca-harness path",
         "`orca-harness/ecr/__init__.py` resolves through moved-path indexes",
         ["orca-harness/ecr/__init__.py"]),
        (".agents path",
         "open `.agents/workflow-overlay/source-of-truth.md`",
         [".agents/workflow-overlay/source-of-truth.md"]),
        (".github path",
         "see `.github/workflows/ci.yml`",
         [".github/workflows/ci.yml"]),
        ("non-path line (no match)",
         "owner decision: defer to next sprint",
         []),
        ("path with spaces not matched",
         "see my folder/with space/foo.md",
         []),
        ("glob pattern skipped",
         "see `docs/decisions/*` for all decisions",
         []),
        ("glob pattern bare skipped",
         "forseti-harness/tests/unit/test_ecr_*",
         []),
        ("anchor stripped to base file",
         ".agents/workflow-overlay/source-loading.md#data-capture-spine-ca-read-pack",
         [".agents/workflow-overlay/source-loading.md"]),
        ("anchor in backtick stripped",
         "see `.agents/workflow-overlay/source-loading.md#section`",
         [".agents/workflow-overlay/source-loading.md"]),
    ]
    print("--- extract_paths_from_line ---")
    for label, line, expected in epl_cases:
        got = extract_paths_from_line(line)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-45s  expect=%s got=%s" % (status, label, expected, got))

    # --- extract_router_table_rows cases ---
    print()
    print("--- extract_router_table_rows ---")
    router_text = """# Router

## Role Bindings

| Role | Target | Notes |
| --- | --- | --- |
| Product artifact | `forseti/product/` | current |
| Broken artifact | relative/path.md | invalid live target |
| Short artifact row |

## Next Section
| Ignore | `docs/ignored/` |
"""
    router_cases = [
        ("section and rows including short data row",
         "## Role Bindings", 1, True,
         [("Product artifact", ["forseti/product/"]), ("Broken artifact", []),
          ("Short artifact row", [])]),
        ("missing section", "## Missing", 1, False, []),
    ]
    for label, heading, column, exp_found, exp_rows in router_cases:
        got_found, got_rows = extract_router_table_rows(router_text, heading, column)
        passed = got_found == exp_found and got_rows == exp_rows
        status = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        print("%s  %-45s  expect=(%s, %s) got=(%s, %s)" % (
            status, label, exp_found, exp_rows, got_found, got_rows))

    # --- is_exempt_line cases ---
    iel_cases = [
        ("exempt: does not exist yet", "see foo/bar.md -- does not exist yet", True),
        ("exempt: created on first", "foo/bar.md created on first run", True),
        ("not exempt: normal line", "see docs/product/bar_v0.md for details", False),
    ]
    print()
    print("--- is_exempt_line ---")
    for label, line, expected in iel_cases:
        got = is_exempt_line(line)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-42s  expect=%s got=%s" % (status, label, expected, got))

    # --- parse_open_next cases ---
    # Each case: (label, header_text, expected_entries, expected_nonresolving)
    def make_header(*entries: str) -> str:
        items = "".join("  - %s\n" % e for e in entries)
        return "# Title\n\n```yaml\nopen_next:\n%s```\n" % items

    pon_cases = [
        ("simple path entry",
         make_header("docs/foo/bar_v0.md"),
         ["docs/foo/bar_v0.md"], 0),
        ("backtick-quoted entry",
         make_header('"docs/foo/bar_v0.md"'),
         ["docs/foo/bar_v0.md"], 0),
        ("single-quoted entry",
         make_header("'docs/foo/bar_v0.md'"),
         ["docs/foo/bar_v0.md"], 0),
        ("entry with ordinary # comment (still checked)",
         make_header("docs/foo/bar_v0.md # load first"),
         ["docs/foo/bar_v0.md"], 0),
        ("nonresolving annotation (skipped, counted)",
         make_header("docs/foo/ephemeral_v0.md # nonresolving: ephemeral scratch"),
         [], 1),
        ("ordinary comment not confused with nonresolving",
         make_header("docs/foo/bar_v0.md # some other comment"),
         ["docs/foo/bar_v0.md"], 0),
        ("entry with no comment (checked)",
         make_header("docs/foo/nocomment_v0.md"),
         ["docs/foo/nocomment_v0.md"], 0),
        ("non-path entry (owner decision)",
         make_header("owner decision"),
         [], 0),
        ("non-path entry (plain word)",
         make_header("defer"),
         [], 0),
        ("mixed: path + non-path",
         make_header("docs/foo/bar_v0.md", "owner decision", ".agents/overlay/x.md"),
         ["docs/foo/bar_v0.md", ".agents/overlay/x.md"], 0),
        ("multiple path entries",
         make_header("docs/a/b_v0.md", "docs/c/d_v0.md"),
         ["docs/a/b_v0.md", "docs/c/d_v0.md"], 0),
        ("mixed nonresolving + normal",
         make_header(
             "docs/foo/real_v0.md",
             "docs/foo/gone_v0.md # nonresolving: operator workfile, never committed",
             "docs/foo/also_real_v0.md",
         ),
         ["docs/foo/real_v0.md", "docs/foo/also_real_v0.md"], 1),
        ("path in open_next stops at next yaml key",
         "```yaml\nopen_next:\n  - docs/a/b_v0.md\nstale_if:\n  - something\n```\n",
         ["docs/a/b_v0.md"], 0),
        ("no yaml block -> empty",
         "# Plain doc\n\nno yaml here\n",
         [], 0),
        ("yaml block no open_next -> empty",
         "```yaml\nscope: foo\n```\n",
         [], 0),
    ]
    print()
    print("--- parse_open_next ---")
    for label, header_text, exp_entries, exp_nr in pon_cases:
        got_entries, got_nr = parse_open_next(header_text)
        passed = (got_entries == exp_entries and got_nr == exp_nr)
        status = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        print("%s  %-52s  expect=(%s, nr=%d) got=(%s, nr=%d)" % (
            status, label, exp_entries, exp_nr, got_entries, got_nr))

    # --- dir_is_covered cases (MGT ancestor-area reachability) ---
    dic_cases = [
        ("exact folder in first cell",
         "docs/prompts/reviews",
         "| `docs/prompts/reviews/` | Review prompts. |", True),
        ("ancestor area covers child",
         "docs/prompts/reviews/sub",
         "| `docs/prompts/reviews/` | Review prompts. |", True),
        ("non-root spine ancestor covers",
         "forseti/product/spines/capture/core/operating_model",
         "| `forseti/product/spines/capture/` | Capture spine. |", True),
        ("sibling-prefix does NOT cover",
         "docs/foo",
         "| `docs/foobar/` | Unrelated. |", False),
        ("child does NOT cover parent",
         "docs/x",
         "| `docs/x/y/` | Child. |", False),
        ("prose mention does NOT cover",
         "docs/some/dir",
         "see docs/some/dir/ later", False),
        ("answer-cell path does NOT cover",
         "docs/x/y",
         "| Question? | `docs/x/y/foo.md` |", False),
        ("structural root does NOT confer coverage",
         "forseti/product/spines/judgment/demand_read/c2_weighting",
         "| `forseti/product/` | Product tree. |", False),
        ("not-retrieval-indexed line no longer auto-covers",
         "docs/some/random/dir",
         "| `docs/hygiene/` | Queues, not retrieval-indexed. |", False),
    ]
    print()
    print("--- dir_is_covered ---")
    for label, rel_dir, map_text, expected in dic_cases:
        got = dir_is_covered(rel_dir, map_text)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-52s  expect=%s got=%s" % (status, label, expected, got))

    # --- dir_is_exempt_coverage cases ---
    diec_cases = [
        ("docs/_inbox is exempt",          "docs/_inbox", True),
        ("docs/_inbox/subdir is exempt",   "docs/_inbox/subdir/foo", True),
        ("_scratch dir is exempt",         "docs/_scratch/foo", True),
        ("normal dir not exempt",          "docs/decisions", False),
        ("docs/hygiene not exempt",        "docs/hygiene", False),
        ("docs/prompts/reviews not exempt","docs/prompts/reviews", False),
    ]
    print()
    print("--- dir_is_exempt_coverage ---")
    for label, rel_dir, expected in diec_cases:
        got = dir_is_exempt_coverage(rel_dir)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-52s  expect=%s got=%s" % (status, label, expected, got))

    # --- extract_inline_links_from_line cases ---
    print()
    print("--- extract_inline_links_from_line ---")
    eill_cases = [
        # (label, line, expected path tokens)
        ("relative .md link",
         "see [foo](docs/decisions/foo_v0.md) for context",
         ["docs/decisions/foo_v0.md"]),
        ("image link checked",
         "![diagram](docs/assets/diagram.png)",
         ["docs/assets/diagram.png"]),
        ("link with title stripped",
         '[ref](docs/foo/bar_v0.md "Some Title")',
         ["docs/foo/bar_v0.md"]),
        ("link with anchor path-only checked",
         "[see here](docs/foo/bar_v0.md#section)",
         ["docs/foo/bar_v0.md"]),
        ("pure anchor skipped",
         "[jump](#heading)",
         []),
        ("external http skipped",
         "[ext](http://example.com/page)",
         []),
        ("external https skipped",
         "[ext](https://example.com/page)",
         []),
        ("mailto skipped",
         "[email](mailto:foo@bar.com)",
         []),
        ("protocol-relative skipped",
         "[cdn](//cdn.example.com/img.png)",
         []),
        ("no slash no ext skipped",
         "[something](OWNERS)",
         []),
        ("svg extension checked",
         "![icon](assets/icon.svg)",
         ["assets/icon.svg"]),
        ("yaml extension checked",
         "[config](config/settings.yml)",
         ["config/settings.yml"]),
    ]
    for label, line, expected in eill_cases:
        got = extract_inline_links_from_line(line)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-48s  expect=%s got=%s" % (status, label, expected, got))

    # --- is_exempt_inline_line cases ---
    print()
    print("--- is_exempt_inline_line ---")
    ieil_cases = [
        ("exempt: does not exist yet",
         "[x](docs/foo.md) -- does not exist yet", True),
        ("exempt: not retrieval-indexed",
         "see [y](docs/bar.md) -- not retrieval-indexed", True),
        ("not exempt: normal line",
         "see [z](docs/baz.md) for details", False),
    ]
    for label, line, expected in ieil_cases:
        got = is_exempt_inline_line(line)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-52s  expect=%s got=%s" % (status, label, expected, got))

    # --- inline_link_is_nonresolving cases ---
    print()
    print("--- inline_link_is_nonresolving ---")
    ilnr_cases = [
        ("nonresolving comment present",
         "[x](slot1_workfile.md) # nonresolving: operator workfile, never committed",
         "slot1_workfile.md",
         True),
        ("no trailing comment",
         "[x](docs/foo/bar_v0.md)",
         "docs/foo/bar_v0.md",
         False),
        ("other comment not nonresolving",
         "[x](docs/foo/bar_v0.md) # load first",
         "docs/foo/bar_v0.md",
         False),
        ("path not in line",
         "[x](docs/foo/bar_v0.md) # nonresolving: gone",
         "docs/other/baz_v0.md",
         False),
    ]
    for label, line, path, expected in ilnr_cases:
        got = inline_link_is_nonresolving(line, path)
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-52s  expect=%s got=%s" % (status, label, expected, got))

    print()
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    # Forced-exception probe: proves the __main__ gating handler
    # (forseti-harness/tests/unit/test_hook_internal_error_gating.py).
    if "--force-internal-error" in argv:
        raise RuntimeError("forced internal error (probe)")
    if "--selftest" in argv:
        return selftest()
    try:
        root = repo_root()
    except Exception as exc:
        sys.stderr.write("check_map_links: could not determine repo root: %s\n" % exc)
        return 0  # fail open
    if "--check" in argv:
        return run_check(root)
    if "--strict-inline" in argv:
        return run_strict_inline(root)
    if "--strict" in argv:
        return run_strict(root)
    if "--report-forseti" in argv or "--report-orca" in argv:
        return run_report_orca(root)
    # Default: print usage
    print("Usage: check_map_links.py --strict | --strict-inline | --check | --report-forseti | --report-orca | --selftest")
    print("  --strict         CI gate: exit 1 if any finding (C1/C2/C3/C4/C5)")
    print("  --strict-inline  alias for --strict (C4/C5 included; kept for caller compat)")
    print("  --check          human-readable report, always exit 0")
    print("  --report-forseti REPORT MODE over forseti/: measure debt, always exit 0 (not a gate)")
    print("  --report-orca    compatibility alias for --report-forseti")
    print("  --selftest       pure-function self-check")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:
        # GATE FAIL bucket in gating modes (validation-gates.md; EP-35
        # delegated review FIND-02 class sweep): an internal checker bug must
        # not read as a green gate. Advisory modes fail open so a bug never
        # bricks the agent.
        sys.stderr.write("check_map_links: internal error: %s\n" % exc)
        gating = ("--strict" in sys.argv[1:] or "--strict-inline" in sys.argv[1:]
                  or "--selftest" in sys.argv[1:])
        sys.exit(1 if gating else 0)
