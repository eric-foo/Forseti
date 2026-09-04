#!/usr/bin/env python3
"""Validate changed consumer-brand provisional maturity scans.

This is a diff-scoped adapter around the acquisition validator. It proves only
that the early work unit names every mandatory route while remaining
non-terminal; the phase acquisition seal retains completion authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
ROOT = HOOK_DIR.parents[1]
sys.path.insert(0, str(HOOK_DIR))
sys.path.insert(0, str(ROOT / "forseti-harness"))

from _hooklib import git_out, parse_name_status, resolve_base_ref  # noqa: E402
from runners.run_phase_acquisition_seal_validation import (  # noqa: E402
    PROVISIONAL_MATURITY_SCAN_VERSION,
    validate_consumer_brand_provisional_maturity_scan,
)

SCHEMA_PREFIX = "consumer_brand_provisional_maturity_scan_"


def _is_candidate(path: Path) -> bool:
    if path.suffix.lower() != ".json" or "docs/research/" not in path.as_posix():
        return False
    if path.name == "provisional_maturity_scan.json":
        return True
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(value, dict) and str(value.get("schema_version", "")).startswith(
        SCHEMA_PREFIX
    )


def _changed_paths(root: Path, base: str) -> list[Path] | None:
    for ref in ("HEAD", base):
        if git_out(root, ["rev-parse", "--verify", "--quiet", ref])[0] != 0:
            return None
    rc, output = git_out(
        root,
        [
            "diff",
            "--name-status",
            "--diff-filter=ACMR",
            "--find-renames",
            f"{base}...HEAD",
            "--",
            "docs/research/**/*.json",
        ],
    )
    if rc != 0:
        return None
    return [root / rel for rel in parse_name_status(output.splitlines())]


def validate_paths(root: Path, paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if not _is_candidate(path):
            continue
        rel = path.resolve().relative_to(root).as_posix()
        try:
            artifact_findings = validate_consumer_brand_provisional_maturity_scan(
                scan_path=path.resolve(), repo_root=root
            )
        except Exception as exc:  # noqa: BLE001 - controlled gate diagnostic
            findings.append(f"{rel}: validator_error:{type(exc).__name__}:{exc}")
            continue
        findings.extend(f"{rel}: {finding}" for finding in artifact_findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate changed consumer-brand provisional maturity scans."
    )
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--diff", metavar="BASE")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    if not args.diff and not args.paths:
        parser.error("provide --diff BASE or one or more paths")

    if args.diff:
        paths = _changed_paths(ROOT, resolve_base_ref(args.diff))
        if paths is None:
            print(
                "check_consumer_brand_maturity_scan: diff scope unavailable; "
                "failing open outside the CI base preflight"
            )
            return 0
    else:
        paths = [
            candidate if candidate.is_absolute() else ROOT / candidate
            for candidate in map(Path, args.paths)
        ]
    findings = validate_paths(ROOT, paths)
    for finding in findings:
        print(("FAIL " if args.strict else "WARN ") + finding)
    if not findings:
        print(
            "check_consumer_brand_maturity_scan: OK -- changed acquisition scans "
            f"satisfy {PROVISIONAL_MATURITY_SCAN_VERSION}"
        )
    return 1 if findings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
