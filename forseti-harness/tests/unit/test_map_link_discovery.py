"""Map entrypoints share reads without weakening either Markdown predicate."""
from __future__ import annotations

import builtins
import importlib.util
import io
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".agents/hooks/check_map_links.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("map_links_discovery_test", HOOK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _seed(root: Path, prefix: str) -> Path:
    admitted = root / prefix / "admitted.md"
    admitted.parent.mkdir(parents=True, exist_ok=True)
    admitted.write_text(
        "```yaml\nopen_next:\n  - docs/missing_header.md\n"
        "  - docs/debt_header.md # nonresolving: historical\n```\n"
        "[debt](docs/debt_inline.md) # nonresolving: historical\n"
        "[exempt](docs/exempt.md) does not exist yet\n"
        + "filler\n" * 33
        + "```yaml\nopen_next:\n  - docs/outside_header_budget.md\n```\n"
        "[bad link after line forty](docs/missing_inline.md)\n",
        encoding="utf-8",
    )
    for excluded in ("_scratch", "_inbox", "node_modules", "nested_scratch_area"):
        hidden = admitted.parent / excluded / "hidden.md"
        hidden.parent.mkdir()
        hidden.write_text("[hidden](docs/hidden_missing.md)\n", encoding="utf-8")
    return admitted


@pytest.mark.parametrize("mode", ["run_strict", "run_strict_inline", "run_check", "run_report_orca"])
def test_entrypoints_preserve_findings_budget_debt_and_read_once(tmp_path, monkeypatch, capsys, mode):
    hook = _load_hook()
    prefix = "forseti" if mode == "run_report_orca" else "docs"
    admitted = _seed(tmp_path, prefix)
    # Isolate the C2/C4 change while exercising the real mode routing/output.
    monkeypatch.setattr(hook, "run_c1", lambda *a, **k: [])
    monkeypatch.setattr(hook, "run_c3", lambda *a, **k: [])
    monkeypatch.setattr(hook, "run_c5", lambda *a, **k: [])
    reads = []
    walks = []
    real_open, real_io_open, real_walk = builtins.open, io.open, hook.os.walk

    def counted_open(original):
        def wrapper(file, *args, **kwargs):
            if not isinstance(file, int) and Path(file) == admitted:
                reads.append(Path(file))
            return original(file, *args, **kwargs)
        return wrapper

    def counted_walk(path, *args, **kwargs):
        walks.append(Path(path))
        yield from real_walk(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counted_open(real_open))
    monkeypatch.setattr(io, "open", counted_open(real_io_open))
    monkeypatch.setattr(hook.os, "walk", counted_walk)
    rc = getattr(hook, mode)(tmp_path)
    output = capsys.readouterr().out
    assert rc == (1 if mode in {"run_strict", "run_strict_inline"} else 0)
    assert output.count("docs/missing_header.md") == 1
    assert output.count("docs/missing_inline.md") == 1
    assert output.index("docs/missing_header.md") < output.index("docs/missing_inline.md")
    assert "outside_header_budget" not in output
    assert "hidden_missing" not in output
    assert "docs/exempt.md" not in output
    debt_line = next(line for line in output.splitlines() if "annotated nonresolving:" in line)
    assert debt_line.split(":", 1)[1].strip().startswith("2 ")
    assert reads == [admitted]
    assert walks.count(tmp_path / prefix) == 1


def test_standalone_predicates_keep_separate_results(tmp_path):
    hook = _load_hook()
    _seed(tmp_path, "docs")
    c2, c2_debt = hook.run_c2(tmp_path)
    c4, c4_debt = hook.run_c4(tmp_path)
    assert [(f.check, f.detail) for f in c2] == [
        ("C2", "open_next path does not exist on disk: docs/missing_header.md")
    ]
    assert [(f.check, f.detail) for f in c4] == [
        ("C4", "inline link target does not exist on disk: docs/missing_inline.md")
    ]
    assert (c2_debt, c4_debt) == (1, 1)
