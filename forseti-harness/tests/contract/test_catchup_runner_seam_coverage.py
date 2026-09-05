"""Coverage gate: seam-consumer runners must consume the consumption seam correctly.

The consumer-side sibling of ``test_capture_runner_lake_seam_coverage.py``
(which gates Bronze producers). Everything here was previously doctrine a cold
agent had to learn from adjudication records; this test makes it mechanical:

- every runner that imports ``data_lake.consumption`` is a declared seam
  consumer (explicit audit answer, both directions);
- consumers use by-key ``pickup`` + ``append_ack``/``ack_packet`` (no bespoke discovery or
  hand-rolled completion facts);
- availability reconcile is the SHARED per-packet fail-visible helper
  (``reconcile_availability_per_packet``, F-ECR-001 adjudicated shape) — no
  local copies, no whole-batch ``rebuild_availability``, no direct
  ``record_availability`` (a swallowed or partial reconcile hides healthy
  packets because the rebuild deletes index entries first);
- the reconcile choice on ``pickup`` is explicit (``reconcile=`` keyword
  visible at the call site, per the seam contract's visible-opt-out rule);
- consumers never touch the ``derived_retrieval`` views (view-independence:
  pickup is by-key over committed availability only).
"""
from __future__ import annotations

import ast

from data_lake.inventory import RUNNERS_DIR as _RUNNERS_DIR

# The declared seam-consumer surface. This is the explicit audit answer for
# "which runners consume committed Bronze work through the seam?" A new
# consumer runner must be added here AND satisfy the structural checks below.
EXPECTED_SEAM_CONSUMER_RUNNERS = frozenset(
    {
        "run_asr_transcript_catchup.py",
        "run_basenotes_cleaning_catchup.py",
        "run_ecr_catchup.py",
        "run_fragrance_review_projection_catchup.py",
        "run_fragrantica_cleaning_catchup.py",
        "run_ig_reels_grid_projection_catchup.py",
        "run_ig_reels_product_extract.py",
        "run_parfumo_cleaning_catchup.py",
        "run_tiktok_product_extract.py",
        "run_tiktok_comment_attention_producer.py",
        "run_tiktok_grid_observation_producer.py",
        "run_transcript_product_extract.py",
    }
)

_REQUIRED_CONSUMPTION_IMPORTS = {"pickup", "reconcile_availability_per_packet"}
_FORBIDDEN_CONSUMER_CALLS = {"rebuild_availability", "record_availability"}
_RECONCILE_HELPER = "reconcile_availability_per_packet"


def _runner_trees() -> dict[str, ast.AST]:
    trees: dict[str, ast.AST] = {}
    for path in sorted(_RUNNERS_DIR.glob("*.py")):
        trees[path.name] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return trees


def _consumption_imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "data_lake.consumption":
            names.update(alias.name for alias in node.names)
    return names


def _consumption_local_names(tree: ast.AST) -> dict[str, str]:
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "data_lake.consumption":
            for alias in node.names:
                names[alias.asname or alias.name] = alias.name
    return names


def _imports_consumption_module(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "data_lake.consumption" for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module == "data_lake":
            if any(alias.name == "consumption" for alias in node.names):
                return True
    return False


def _uses_consumption(tree: ast.AST) -> bool:
    return bool(_consumption_imports(tree)) or _imports_consumption_module(tree)


def _call_names(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def _called_name(node: ast.Call, local_names: dict[str, str] | None = None) -> str:
    local_names = local_names or {}
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return local_names.get(func.id, func.id)
    return ""


def _contains_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id == name and isinstance(child.ctx, ast.Load)
        for child in ast.walk(node)
    )


def _visible_reconcile_lines(
    function: ast.FunctionDef | ast.AsyncFunctionDef, local_names: dict[str, str]
) -> list[int]:
    parents = {
        child: parent
        for parent in ast.walk(function)
        for child in ast.iter_child_nodes(parent)
    }
    assigned: dict[str, int] = {}
    visible: list[int] = []

    for call in [node for node in ast.walk(function) if isinstance(node, ast.Call)]:
        if _called_name(call, local_names) != _RECONCILE_HELPER:
            continue
        parent = parents.get(call)
        if isinstance(parent, ast.Call) and _called_name(parent, local_names) == "extend":
            visible.append(call.lineno)
        elif isinstance(parent, ast.Return):
            visible.append(call.lineno)
        elif isinstance(parent, ast.Assign) and parent.value is call:
            for target in parent.targets:
                if isinstance(target, ast.Name):
                    assigned[target.id] = call.lineno

    for name, line in assigned.items():
        for node in ast.walk(function):
            if getattr(node, "lineno", 0) <= line:
                continue
            if isinstance(node, (ast.If, ast.Return, ast.Raise)) and _contains_name(node, name):
                visible.append(line)
                break
            if isinstance(node, ast.Call) and _called_name(node, local_names) in {"extend", "append"}:
                if any(_contains_name(arg, name) for arg in node.args):
                    visible.append(line)
                    break
    return sorted(set(visible))


def _pickup_reconcile_false_lines(
    function: ast.FunctionDef | ast.AsyncFunctionDef, local_names: dict[str, str]
) -> list[int]:
    lines: list[int] = []
    for call in [node for node in ast.walk(function) if isinstance(node, ast.Call)]:
        if _called_name(call, local_names) != "pickup":
            continue
        for kw in call.keywords:
            if kw.arg == "reconcile" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                lines.append(call.lineno)
    return lines


def test_seam_consumer_runner_surface_is_explicit() -> None:
    discovered = {
        name
        for name, tree in _runner_trees().items()
        if _uses_consumption(tree) and name != "run_seam_cadence.py"
    }

    new_consumers = discovered - EXPECTED_SEAM_CONSUMER_RUNNERS
    assert not new_consumers, (
        "Runner(s) import data_lake.consumption but are not declared seam consumers.\n"
        "Add them to EXPECTED_SEAM_CONSUMER_RUNNERS and make them satisfy this gate:\n"
        f"  {sorted(new_consumers)}"
    )

    stale = EXPECTED_SEAM_CONSUMER_RUNNERS - discovered
    assert not stale, (
        "EXPECTED_SEAM_CONSUMER_RUNNERS lists runner(s) that no longer consume the seam.\n"
        f"Remove the stale declarations: {sorted(stale)}"
    )


def test_seam_consumers_use_pickup_ack_and_the_shared_reconcile() -> None:
    trees = _runner_trees()
    problems: dict[str, list[str]] = {}
    for name in sorted(EXPECTED_SEAM_CONSUMER_RUNNERS):
        tree = trees[name]
        issues: list[str] = []
        imported = _consumption_imports(tree)
        local_names = _consumption_local_names(tree)
        if not imported & {"append_ack", "ack_packet"}:
            issues.append("missing consumption acknowledgement import: append_ack or ack_packet")
        missing = _REQUIRED_CONSUMPTION_IMPORTS - imported
        if missing:
            issues.append(f"missing consumption imports: {sorted(missing)}")
        visible_reconciles = []
        local_defs = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if "_reconcile_availability" in local_defs:
            issues.append(
                "carries a local _reconcile_availability copy; use "
                "data_lake.consumption.reconcile_availability_per_packet"
            )
        for function in [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]:
            function_reconciles = _visible_reconcile_lines(function, local_names)
            visible_reconciles.extend(function_reconciles)
            for line in _pickup_reconcile_false_lines(function, local_names):
                if not any(reconcile_line < line for reconcile_line in function_reconciles):
                    issues.append(
                        f"pickup at line {line} opts out of reconcile without an earlier "
                        "same-function visible reconcile_availability_per_packet failure channel"
                    )
        if not visible_reconciles:
            issues.append(
                "does not visibly use reconcile_availability_per_packet return values; "
                "import-only or discarded helper calls do not surface reconcile failures"
            )
        for call in _call_names(tree):
            called = _called_name(call, local_names)
            if called in _FORBIDDEN_CONSUMER_CALLS:
                issues.append(
                    f"calls {called} directly at line {call.lineno}; availability "
                    "reconcile must go through reconcile_availability_per_packet"
                )
            if called == "pickup" and not any(kw.arg == "reconcile" for kw in call.keywords):
                issues.append(
                    f"pickup at line {call.lineno} does not make its reconcile choice "
                    "explicit (pass reconcile=... per the seam contract's visible-opt-out rule)"
                )
        if issues:
            problems[name] = issues

    assert not problems, (
        "Seam-consumer runner(s) violate the consumer seam shape "
        "(F-ECR-001 shared reconcile + by-key pickup/ack):\n"
        + "\n".join(f"  {name}: {issues}" for name, issues in sorted(problems.items()))
    )


def test_seam_consumers_never_touch_derived_retrieval_views() -> None:
    offenders = {}
    for name in sorted(EXPECTED_SEAM_CONSUMER_RUNNERS):
        source = (_RUNNERS_DIR / name).read_text(encoding="utf-8")
        if "derived_retrieval" in source:
            offenders[name] = "references derived_retrieval"
    assert not offenders, (
        "Seam consumers must stay view-independent (pickup is by-key over committed "
        f"availability; views are rebuildable caches): {offenders}"
    )
