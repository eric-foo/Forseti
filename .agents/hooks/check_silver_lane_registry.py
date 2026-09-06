#!/usr/bin/env python3
"""Enforce the Data Lake silver-lane write contract (the no-blur binding).

Reads the lane registry (``forseti-harness/data_lake/lane_registry.py``) and scans
producer source for raw lake writes (``append_record`` / ``append_record_set``):

- **G1 (declared).** A ``silver``-named lane written by a producer must be
  declared in the registry. An undeclared silver lane fails -- a new silver lane
  has to be registered with a role, which is also how the next agent discovers
  the contract.
- **G2 (front-door).** A raw write to a ``silver_envelope`` lane must go through
  the validating front-door ``append_silver_record`` (``data_lake/silver_record``).
  A direct ``append_record`` to an envelope lane fails, unless the lane is listed
  in the registry's ``FRONT_DOOR_PENDING`` baseline (a named, justified migration
  target -- not a silent exception). The exemption is scoped to the front-door
  *function*, not the whole module, so another raw writer added beside it is not
  blessed.

It also runs the registry's own ``validate_registry()`` invariant (the pending
allowlist may not silently grow), and under ``--strict`` it FAILS an unresolvable
single-lane argument (``lane=`` / ``completion_lane=``) on a raw write -- a write
it cannot prove is not a silver-envelope bypass. A dynamic ``members`` dict (built
by a legitimate record-set producer, e.g. a comprehension over a known lane
mapping) is reported as a coverage NOTE rather than failed; statically resolving
dynamic members is a named future hardening.

It does NOT validate record CONTENT (that is the front-door's job at write time);
it binds the WRITE PATH so the content validator cannot be silently bypassed.

Usage:
  python .agents/hooks/check_silver_lane_registry.py [--strict] [--selftest] [PATH ...]
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hooklib import repo_root  # noqa: E402  (sys.path pin must precede the import)

WRITE_METHODS = {"append_record", "append_record_set"}
LANE_KEYWORDS = {"lane", "completion_lane"}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


@dataclass(frozen=True)
class Unresolved:
    relposix: str
    lineno: int
    excerpt: str
    kind: str  # "lane" | "completion_lane" | "members"


@dataclass(frozen=True)
class WriteCall:
    call: ast.Call
    enclosing_function: str | None


def _load_registry(root: Path):
    path = root / "forseti-harness" / "data_lake" / "lane_registry.py"
    spec = importlib.util.spec_from_file_location("orca_lane_registry", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load lane registry from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _registry_findings(registry) -> list[Finding]:
    """Surface the registry's own invariant violations (e.g. a grown
    FRONT_DOOR_PENDING allowlist) as guard findings, so the hook is self-checking
    and not dependent on a separate pytest to catch a tampered baseline."""
    validate = getattr(registry, "validate_registry", None)
    if not callable(validate):
        return []
    return [Finding("invalid_lane_registry", message) for message in validate()]


# Only an unresolvable SINGLE-lane keyword (lane=/completion_lane=) is strict-failed:
# an opaque single lane on a raw write is a pointed bypass risk, and the live repo
# resolves all of them. A dynamic ``members`` dict (a variable or comprehension) is
# noted but not failed -- legitimate record-set producers (e.g. the ecr deriver's
# comprehension over a known lane mapping) build members dynamically, and the guard
# does not evaluate arbitrary dict expressions.
STRICT_FAIL_UNRESOLVED_KINDS = {"lane", "completion_lane"}


def _unresolved_findings(unresolved: list[Unresolved]) -> list[Finding]:
    return [
        Finding(
            "unresolved_lane_argument",
            f"{item.relposix}:{item.lineno} has unresolved {item.kind} argument {item.excerpt!r}; "
            "strict mode cannot prove this raw lake write is not a silver-envelope bypass.",
        )
        for item in unresolved
        if item.kind in STRICT_FAIL_UNRESOLVED_KINDS
    ]


# --- static constant resolution -------------------------------------------

def _string_constants(tree: ast.Module) -> dict[str, str]:
    consts: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    consts[target.id] = node.value.value
    return consts


def _alias_assignments(tree: ast.Module) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out.setdefault(target.id, set()).add(node.value.id)
    return out


def _build_global_consts(parsed: dict[Path, ast.Module]) -> dict[str, str]:
    """Repo-wide ``name -> str value`` from module-level literal assignments
    (resolving simple ``NAME = OTHER`` aliases). A name with conflicting literal
    values, or an alias bound to more than one source, is dropped -- treated as
    unresolvable, never guessed (so a same-named alias cannot resolve to whichever
    source was observed first)."""
    literal: dict[str, set[str]] = {}
    aliases: dict[str, set[str]] = {}
    for tree in parsed.values():
        for name, value in _string_constants(tree).items():
            literal.setdefault(name, set()).add(value)
        for name, srcs in _alias_assignments(tree).items():
            aliases.setdefault(name, set()).update(srcs)
    consts = {name: next(iter(vals)) for name, vals in literal.items() if len(vals) == 1}
    literal_conflicts = {name for name, vals in literal.items() if len(vals) > 1}
    for _ in range(3):  # resolve short alias chains
        for name, srcs in aliases.items():
            if name in consts or name in literal_conflicts or len(srcs) != 1:
                continue
            src = next(iter(srcs))
            if src in consts:
                consts[name] = consts[src]
    return consts


def _resolve(node: ast.AST, consts: dict[str, str]) -> tuple[str | None, str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, repr(node.value)
    if isinstance(node, ast.Name):
        return consts.get(node.id), node.id
    if isinstance(node, ast.Attribute):
        return consts.get(node.attr), node.attr
    return None, type(node).__name__


def _lane_args(call: ast.Call, consts: dict[str, str]) -> list[tuple[str | None, str, int, str]]:
    out: list[tuple[str | None, str, int, str]] = []
    for kw in call.keywords:
        if kw.arg in LANE_KEYWORDS:
            value, excerpt = _resolve(kw.value, consts)
            out.append((value, excerpt, call.lineno, kw.arg))
        elif kw.arg == "members":
            if isinstance(kw.value, ast.Dict):
                for key in kw.value.keys:
                    if key is None:  # **unpack -- the lane keys are not visible
                        out.append((None, "members:**unpack", call.lineno, "members"))
                        continue
                    value, excerpt = _resolve(key, consts)
                    out.append((value, excerpt, call.lineno, "members"))
            else:  # members=<variable/comprehension> -- lanes not statically known
                out.append((None, f"members:{type(kw.value).__name__}", call.lineno, "members"))
    return out


def _iter_write_calls(tree: ast.Module) -> Iterable[WriteCall]:
    """Find every ``append_record`` / ``append_record_set`` call, tagged with the
    name of its innermost enclosing function so the front-door exemption can be
    scoped to that function rather than the whole module."""

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.calls: list[WriteCall] = []
            self._function_stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._function_stack.append(node.name)
            self.generic_visit(node)
            self._function_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute) and node.func.attr in WRITE_METHODS:
                function_name = self._function_stack[-1] if self._function_stack else None
                self.calls.append(WriteCall(node, function_name))
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)
    return visitor.calls


def _subtree_value(call: ast.Call, consts: dict[str, str]) -> str | None:
    for kw in call.keywords:
        if kw.arg == "subtree":
            value, _excerpt = _resolve(kw.value, consts)
            return value
    return None


def _scan_tree(
    relposix: str, tree: ast.Module, consts: dict[str, str], registry, is_front_door_module: bool
) -> tuple[list[Finding], list[Unresolved]]:
    findings: list[Finding] = []
    unresolved: list[Unresolved] = []
    for write_call in _iter_write_calls(tree):
        call = write_call.call
        # A write whose subtree STATICALLY resolves to "acknowledgements" is an
        # acknowledgement record (consumption seam), not a silver derived record:
        # the silver envelope grammar lives under derived/, and ack namespaces
        # legitimately reuse registered lane names (seam contract namespace rule).
        # An unresolved or any other subtree keeps full scrutiny (fail-closed).
        if _subtree_value(call, consts) == "acknowledgements":
            continue
        # Exemption is scoped to the front-door FUNCTION, not the module: a raw
        # writer added elsewhere in silver_record.py is not blessed.
        front_door_functions = {
            registry.SILVER_ENVELOPE_FRONT_DOOR_FUNC,
            "append_silver_record_set",
        }
        is_front_door_call = (
            is_front_door_module
            and write_call.enclosing_function in front_door_functions
        )
        for lane, excerpt, lineno, kind in _lane_args(call, consts):
            if lane is None:
                # The front-door legitimately takes a lane parameter; only note an
                # unresolved lane elsewhere, where it is a real static-coverage gap.
                if not is_front_door_call:
                    unresolved.append(Unresolved(relposix, lineno, excerpt, kind))
                continue
            if not registry.is_silver_named(lane):
                continue
            role = registry.role_of(lane)
            if role is None:
                findings.append(
                    Finding(
                        "undeclared_silver_lane",
                        f"{relposix}:{lineno} writes silver lane {lane!r}, which is not declared "
                        "in forseti-harness/data_lake/lane_registry.py. Add it with a role.",
                    )
                )
                continue
            if role == registry.LaneRole.SILVER_ENVELOPE and not is_front_door_call:
                if lane in registry.FRONT_DOOR_PENDING:
                    continue
                findings.append(
                    Finding(
                        "envelope_lane_bypass",
                        f"{relposix}:{lineno} writes silver_envelope lane {lane!r} through a raw "
                        f"lake writer. Route it through {registry.SILVER_ENVELOPE_FRONT_DOOR_FUNC}() "
                        "(forseti-harness/data_lake/silver_record.py). If migration is genuinely "
                        "pending, add the lane to FRONT_DOOR_PENDING with a reason.",
                    )
                )
    return findings, unresolved


# --- file discovery + drivers ---------------------------------------------

_PRODUCER_DISCOVERY_EXCLUDED_DIRS = frozenset(
    {"tests", "__pycache__", "_test_runs", "_scratch"}
)


def _producer_files(root: Path) -> list[Path]:
    harness = root / "forseti-harness"
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(harness):
        dirnames[:] = [d for d in dirnames if d not in _PRODUCER_DISCOVERY_EXCLUDED_DIRS]
        if Path(dirpath) == harness:
            # uv's environment and setuptools' wheel staging contain installed
            # copies, not producer source. Restrict this exclusion to the
            # harness root so a source package's build/ directory stays covered.
            dirnames[:] = [d for d in dirnames if d not in {".venv", "build"}]
        # Keep pathlib glob's platform case matching and matching directory entries.
        out.extend(Path(dirpath) / name for name in (*dirnames, *filenames)
                   if Path(name).match("*.py"))
    return sorted(out)


def _parse(paths: Iterable[Path]) -> dict[Path, ast.Module]:
    parsed: dict[Path, ast.Module] = {}
    for path in paths:
        try:
            parsed[path] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
    return parsed


def scan(root: Path, paths: list[Path], registry) -> tuple[list[Finding], list[Unresolved]]:
    parsed = _parse(paths)
    consts = _build_global_consts(parsed)
    findings: list[Finding] = []
    unresolved: list[Unresolved] = []
    front_door = registry.SILVER_ENVELOPE_FRONT_DOOR_MODULE
    for path, tree in parsed.items():
        try:
            relposix = path.relative_to(root).as_posix()
        except ValueError:
            relposix = path.as_posix()
        f, u = _scan_tree(
            relposix, tree, consts, registry, is_front_door_module=(relposix == front_door)
        )
        findings.extend(f)
        unresolved.extend(u)
    return findings, unresolved


def _print_report(findings: list[Finding], unresolved: list[Unresolved]) -> None:
    for finding in findings:
        print(f"FAIL {finding.code}: {finding.message}")
    if unresolved:
        # No silent caps: report what was skipped so coverage is visible.
        print(f"note: {len(unresolved)} lane argument(s) not statically resolved:")
        for item in unresolved[:8]:
            print(f"  - {item.relposix}:{item.lineno} ({item.excerpt})")
        if len(unresolved) > 8:
            print(f"  - ... and {len(unresolved) - 8} more")
    if not findings:
        print("check_silver_lane_registry: OK (no silver-lane write violations)")


def selftest(root: Path | None = None) -> int:
    root = root or repo_root()
    registry = _load_registry(root)
    registry_findings = _registry_findings(registry)
    if registry_findings:
        for finding in registry_findings:
            print(f"FAIL {finding.code}: {finding.message}")
        return 1
    fixture_dir = root / "forseti-harness" / "tests" / "fixtures" / "silver_lane_guard"
    fixtures = sorted(fixture_dir.glob("*.py"))
    if not fixtures:
        print(f"SELFTEST FAILED: no fixtures at {fixture_dir}")
        return 1
    ok = True
    for path in fixtures:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        expected = "fail" if "fixture_expected: fail" in first_line else "pass"
        findings, _ = scan(root, [path], registry)
        actual = "fail" if findings else "pass"
        if actual == expected:
            print(f"PASS {path.name} ({expected})")
        else:
            ok = False
            codes = ", ".join(sorted({f.code for f in findings})) or "<none>"
            print(f"FAIL {path.name}: expected {expected}, got {actual} ({codes})")
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Enforce the Data Lake silver-lane write contract.")
    parser.add_argument("paths", nargs="*", help="explicit files to scan (default: all producers)")
    parser.add_argument("--selftest", action="store_true", help="run the fixture selftest")
    parser.add_argument(
        "--strict", action="store_true", help="also fail unresolved lane arguments (static-coverage gaps)"
    )
    args = parser.parse_args(argv)

    root = repo_root()
    if args.selftest:
        return selftest(root)

    registry = _load_registry(root)
    paths = [Path(p) for p in args.paths] if args.paths else _producer_files(root)
    findings = _registry_findings(registry)
    scan_findings, unresolved = scan(root, paths, registry)
    findings.extend(scan_findings)
    if args.strict:
        findings.extend(_unresolved_findings(unresolved))
    _print_report(findings, unresolved)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
