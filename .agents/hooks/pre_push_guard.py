#!/usr/bin/env python3
"""Forseti local Git pre-push guard.

Reads Git pre-push updates from stdin:

    <local-ref> <local-sha> <remote-ref> <remote-sha>

Blocks pushes targeting main, branch deletions, non-fast-forward updates, and
updates whose fast-forward safety cannot be verified. For allowed lane pushes
it then mirrors selected strict CI gates (SELECTED_GATES below) so a forward-only
gate miss -- e.g. a reviewer-authored docs/review-outputs report missing its
retrieval header (PR #613), or a stale JSON source-input hash after a source
ledger edit -- fails at the push boundary instead of costing a red CI round.
Same checkers, same rule owners; the mirror adds no
rule. This is a Git-bound local adapter, not a Claude/Codex tool hook. It is
bypassable with --no-verify, does not see GitHub API actions such as
`gh pr merge`, and CI remains the authoritative gate.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hooklib import repo_root  # noqa: E402  (sys.path pin must precede the import)

ZERO = "0" * 40
MAIN_REFS = {"main", "refs/heads/main"}

# Selected strict gates mirrored from .github/workflows/ci.yml. The diff-scoped
# checkers default their base to origin/main for the outgoing lane. CI uses the
# exact event base SHA instead; for normal fast-forward PR/main history both
# scopes represent the same net lane change. Rule
# authority: .agents/workflow-overlay/validation-gates.md ("Enforcement
# Placement"); each checker references its own rule owner.
SELECTED_GATES = (
    ("retrieval link check", (".agents/hooks/check_map_links.py", "--strict")),
    ("retrieval header index", (".agents/hooks/header_index.py", "--strict")),
    ("review-routing disposition", (".agents/hooks/check_review_routing.py", "--strict")),
    ("source-input hash freshness", (".agents/hooks/check_source_input_hashes.py", "--strict")),
    ("hash-pin freshness", (".agents/hooks/check_hash_pin_freshness.py", "--strict")),
    ("prompt contract shape", (".agents/hooks/check_prompt_output_mode.py", "--strict")),
    (
        "consumer-brand acquisition-start completeness",
        (
            ".agents/hooks/check_consumer_brand_maturity_scan.py",
            "--diff",
            "origin/main",
            "--strict",
        ),
    ),
    (
        "review-output provenance",
        (".agents/hooks/check_review_output_provenance.py", "--diff", "origin/main", "--strict"),
    ),
    ("handoff-pointer resolution", (".agents/hooks/check_handoff_pointers.py", "--strict")),
    ("ontology tag validity", (".agents/hooks/check_ontology_tag_validity.py", "--strict")),
    ("harness coupling contracts", (".agents/hooks/check_harness_coupling.py", "--strict")),
)

GATE_TIMEOUT_SECONDS = 120  # selected gates normally complete well below this

SELECTED_GATE_AUTHORITY = (
    ".agents/workflow-overlay/validation-gates.md (Enforcement Placement); "
    "these mirror the CI gates in .github/workflows/ci.yml."
)


def _is_ancestor(remote_sha: str, local_sha: str) -> int:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", remote_sha, local_sha],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def decide_update(local_ref: str, local_sha: str, remote_ref: str, remote_sha: str) -> str | None:
    """Return a block reason, or None to allow the update."""
    if remote_ref in MAIN_REFS:
        return f"push targets main ({remote_ref})"
    if local_sha == ZERO:
        return f"branch deletion push ({remote_ref})"
    if remote_sha != ZERO:
        rc = _is_ancestor(remote_sha, local_sha)
        if rc == 1:
            return f"non-fast-forward push to {remote_ref}"
        if rc != 0:
            return f"could not verify fast-forward safety for {remote_ref}"
    return None


def iter_updates(stdin_text: str):
    for raw in stdin_text.splitlines():
        parts = raw.split()
        if not parts:
            continue
        if len(parts) != 4:
            yield None, f"malformed pre-push update line: {raw[:160]}"
            continue
        yield parts, None


def check_stdin(stdin_text: str) -> list[str]:
    reasons: list[str] = []
    for update, parse_error in iter_updates(stdin_text):
        if parse_error:
            reasons.append(parse_error)
            continue
        reason = decide_update(*update)
        if reason:
            reasons.append(reason)
    return reasons


def run_gate(root: Path, script: str, gate_args: tuple[str, ...]) -> tuple[int, str]:
    """Run one checker; return (returncode, combined output). Never raises.

    A launch failure or timeout returns (-1, why): an unknown failure in a
    gating layer must not read as a pass (GATE FAIL bucket, validation-gates).
    Checker-owned infra behavior is preserved rather than normalized here. The
    harness coupling contracts gate deliberately fails closed on an
    unresolvable diff base or unlaunchable test, so an infra gap there blocks
    the push.
    """
    try:
        res = subprocess.run(
            [sys.executable, str(root / script), *gate_args],
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT_SECONDS,
            cwd=str(root),
        )
        return res.returncode, (res.stdout or "") + (res.stderr or "")
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return -1, f"could not run gate: {exc}"


def selected_gate_reasons(root: Path, run=run_gate) -> list[str]:
    """Block reasons from the mirrored selected strict gates (empty == all pass)."""
    reasons: list[str] = []
    for name, (script, *gate_args) in SELECTED_GATES:
        rc, output = run(root, script, tuple(gate_args))
        if rc != 0:
            reasons.append(
                f"selected gate '{name}' failed (exit {rc}):\n{output.strip()}"
            )
    return reasons


def block(reasons: list[str], authority: str | None = None) -> int:
    print("BLOCKED by Forseti local pre-push guard (.githooks/pre-push).", file=sys.stderr)
    for reason in reasons:
        print(f"Reason: {reason}", file=sys.stderr)
    if authority is None:
        authority = ".agents/workflow-overlay/safety-rules.md + dev-workflow doctrine."
    print(f"Authority: {authority}", file=sys.stderr)
    print("Boundary: local Git hook only; --no-verify can bypass it.", file=sys.stderr)
    return 1


def selftest() -> int:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    cases = [
        ("new lane branch", f"refs/heads/lane {head} refs/heads/lane {ZERO}\n", False),
        ("main target", f"refs/heads/lane {head} refs/heads/main {ZERO}\n", True),
        ("delete branch", f"refs/heads/lane {ZERO} refs/heads/lane {head}\n", True),
        ("already up to date", f"refs/heads/lane {head} refs/heads/lane {head}\n", False),
        ("malformed line", "not enough fields\n", True),
    ]
    ok = True
    for name, payload, expect_block in cases:
        got_block = bool(check_stdin(payload))
        status = "PASS" if got_block == expect_block else "FAIL"
        if got_block != expect_block:
            ok = False
        print(f"{status} {name} expect_block={expect_block} got_block={got_block}")

    # Selected-gate decision cases with injected runners (no subprocess).
    root = repo_root()

    def all_pass(_root, _script, _args):
        return 0, "OK"

    def header_fails(_root, script, _args):
        if "header_index" in script:
            return 1, "MISSING-HEADER: docs/review-outputs/x_v0.md"
        return 0, "OK"

    def launch_failure(_root, _script, _args):
        return -1, "could not run gate: [Errno 2] No such file"

    gate_cases = [
        ("selected gates all pass", all_pass, 0),
        ("one selected gate fails", header_fails, 1),
        ("gate launch failure blocks all", launch_failure, len(SELECTED_GATES)),
    ]
    for name, runner, expect_count in gate_cases:
        got = selected_gate_reasons(root, run=runner)
        status = "PASS" if len(got) == expect_count else "FAIL"
        if len(got) != expect_count:
            ok = False
        print(f"{status} {name} expect_reasons={expect_count} got_reasons={len(got)}")

    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    stdin_text = sys.stdin.read()
    reasons = check_stdin(stdin_text)
    if reasons:
        return block(reasons)
    updates = [u for u, err in iter_updates(stdin_text) if u]
    if updates:
        gate_reasons = selected_gate_reasons(repo_root())
        if gate_reasons:
            return block(gate_reasons, authority=SELECTED_GATE_AUTHORITY)
        print(f"pre-push gates: OK ({len(SELECTED_GATES)} gate(s))", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
