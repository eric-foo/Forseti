#!/usr/bin/env python3
"""Prompt-contract SHAPE gate (EP-11 + EP-38).

Every in-scope prompt artifact must carry a recognized output-mode declaration.
Implementation-authorized Codex managed-receiver commissions that may start in
the wrong task must also carry the exact single-use receiver-creation shell.
(The former delegated-patch courier-shell gate was retired 2026-07-25 with the
lane binding: it triggered only on a self-declared target_kind token, real
courier prompts never declared it, and the who-constraint is enforced by
.agents/workflow-overlay/delegated-review-patch.md plus CA adjudication.)

RULE AUTHORITY
  .agents/workflow-overlay/prompt-orchestration.md -> "Output Modes" (the
  closed-set token list and per-token meaning) and .agents/workflow-overlay/
  validation-gates.md -> "Output-mode gate" bullet ("prompts must name exactly
  one output mode from ..."). This checker references those rules and never
  restates them. EP handle: EP-11 in
  docs/decisions/overlay_enforcement_placement_classification_v0.md, which
  scopes that check to SHAPE only: `schema: token-in-set`.
  .agents/workflow-overlay/prompt-orchestration.md -> "Implementation
  Commission Receiver-Creation Clause" and "Prompt Validation Gates", plus
  validation-gates.md -> "Worktree preflight gate", own EP-38. This checker
  verifies only the commission-visible, mechanically decidable shell; receiver
   identity, write capability, source freshness, and no-concurrent-writer truth
   remain runtime/resident checks.
   delegated-review-patch.md and prompt-orchestration.md -> "Lane-Scoped
   Delegated Patch Prompt Default" own courier-prompt semantics; vendor
   identity and direct-write truth are resident verification, not shape.

WHAT THIS ENFORCES (shape only, narrowed from the EP-11 full rule)
  A prompt artifact under docs/prompts/ must contain at least one recognized
  output-mode declaration line -- a line naming one of the five closed-set
  tokens (`chat-only`, `file-write`, `review-report`, `paste-ready-chat`,
  `patch-queue`) in either YAML-key or prose-bullet form. This is the
  mechanically checkable shell of EP-11:
    - zero declaration lines at all           -> FINDING (never declared)
    - declaration line(s) present, but every one carries zero closed-set
      tokens (empty value, legacy/typo'd token, wrong separator)
                                               -> FINDING (declared but invalid)
    - otherwise                               -> PASS

  For a prompt that declares `edit_permission: implementation-authorized` and a
  `receiver_binding` with `receiver_class: codex_managed_worktree` plus
  `binding_state: receiver_to_verify`, the checker also requires exactly one
  `receiver_creation_authorization` block whose seven values
  match the binding and the canonical single-use tokens. It rejects:
    - the missing-block + wrong-task-stop contradiction;
    - broader/repeated receiver creation;
    - positive manual `git worktree add` substitution;
    - a read-only/scoping/review-only commission carrying the block; and
     - source-load failure clauses that fall back to memory/project rules or do
       not type the failure as `SOURCE_CONTEXT_INCOMPLETE`.

WHAT THIS DOES *NOT* DO (the over-edge boundary -- PLACEMENT IS NOT AUTHORITY)
  - It does NOT verify "exactly one" output mode is declared for the artifact
    as a whole. Multiple declaration lines are common and legitimate (a
    dispatch block plus a preflight recap; a receiver-output aside), and
    deciding which one is *the* artifact's output mode -- versus a compound
    per-audience or per-phase declaration -- stays resident judgment (the
    EP-11 "exactly one" clause is COUNT judgment, not TOKEN-IN-SET shape).
    Multiple declaration lines, and a single line carrying 2+ tokens (a
    legitimate compound declaration, e.g. `file-write` for this artifact plus
    `paste-ready-chat` for a courier copy), are printed as INFO notes only in
    --check/--audit output -- never findings.
  - It does NOT decide whether the chosen token is the RIGHT one for the
    artifact's actual delivery shape, whether a `review-report` prompt really
    wrote its report, or whether output-mode exceptions in
    prompt-orchestration.md were honored. Truth of the declared mode stays
    resident judgment.
  - It does NOT parse `receiver_output_mode:` / `reviewer_output_mode:` /
    `downstream_review_output_mode:` / `terminal_output_mode:` (or any other
    qualified key) as *this* artifact's declaration, and it does NOT treat an
    "output mode for the receiving/downstream/future/reviewer/delegate/
    adjudicator" prose aside as a declaration -- those describe a DIFFERENT
    actor's output mode, not this artifact's own.

DETECTION CONTRACT (mirrors check_handoff_pointers.py / check_dcp_receipt.py)
  base ref priority: $FORSETI_DIFF_BASE (exact CI event SHA); else
  $GITHUB_BASE_REF -> origin/<ref>; else --base <ref>; else origin/main.
  Diff is three-dot `base...HEAD`, name-status; scanned files are
  the added/modified/rename-or-copy-destination `.md` paths still present in
  the tree, filtered to the in-scope set (below). NO HEAD~1 fallback. If the
  base cannot be resolved or git fails, fail OPEN (exit 0, loud warning) --
  the universal Forseti infra-gap stance; in CI the base is always present
  (fetch-depth: 0). Fail-open is for INFRASTRUCTURE GAPS ONLY: in --strict and
  --selftest an unexpected internal exception exits 1 (the GATE FAIL bucket,
  validation-gates.md); advisory modes fail open on internal error.
  Forward-only by construction: only the current diff is gated, never
  historical backlog (see --audit for that view).

IN-SCOPE FILES
  posix relpath starts with `docs/prompts/`, ends `.md`, is NOT under
  `docs/prompts/templates/` (those are examples, not filed prompt artifacts),
  basename is not `README.md`, and is not under a globally excluded dir
  (`_scratch`, `node_modules`, `docs/_inbox/` / any `_inbox/` segment --
  mirrors check_handoff_pointers.py's exclusion list).

MODES
  check_prompt_output_mode.py --strict [--base <ref>]        CI gate; exit 1 on findings
  check_prompt_output_mode.py --check  [--base <ref>] [paths] same scan, human-readable, exit 0;
                                                               explicit paths scan those files
                                                               directly instead of the base diff
  check_prompt_output_mode.py --audit                         whole-corpus backlog view
                                                               (git ls-files -- docs/prompts), exit 0
  check_prompt_output_mode.py --selftest                      pure-function cases; exit per pass/fail
  check_prompt_output_mode.py --validate-stdin                gate one rendered prompt from stdin;
                                                               exit 1 on any finding

NON-CLAIMS
  Shape only, never truth. Not validation, not readiness. A PASS means the
  recognized prompt shells are present and internally consistent -- it is not
  a claim that the output mode is correct, the recorded receiver is real, its
  preflight passed, or any source was actually loaded.

REGISTRATION (.github/workflows/ci.yml, after the output-mode-adjacent step)
  - name: prompt output-mode declaration (EP-11 shape gate)
    run: python .agents/hooks/check_prompt_output_mode.py --strict
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hooklib import (  # noqa: E402  (sys.path pin must precede the import)
    git_out,
    parse_name_status,
    repo_root,
    resolve_base_ref,
)


# ---------------------------------------------------------------------------
# Closed-set vocabulary (frozenset-constant style, mirrors check_dcp_receipt.py)
# ---------------------------------------------------------------------------

# Single-sourced from .agents/workflow-overlay/prompt-orchestration.md
# § "Output Modes". Additions or removals there are doctrine changes and must
# update this constant (see selftest case "token-drift insurance", which
# parses that section and asserts set equality against this constant).
TOKENS = frozenset({
    "chat-only",
    "file-write",
    "review-report",
    "paste-ready-chat",
    "patch-queue",
})

RULE_AUTHORITY = (
    ".agents/workflow-overlay/prompt-orchestration.md (Output Modes; "
    "Implementation Commission Receiver-Creation Clause; "
    "Prompt Validation Gates) / "
    ".agents/workflow-overlay/validation-gates.md (Output-mode gate; Worktree preflight gate)"
)

# ---------------------------------------------------------------------------
# Pure decision core (testable)
# ---------------------------------------------------------------------------

# Key form: `output_mode:` (optionally indented/bulleted), never a qualified
# key like `receiver_output_mode:` or `terminal_output_mode:` -- the negative
# lookbehind refuses a match when the character immediately before
# "output_mode" is a word character or hyphen.
_KEY_RE = re.compile(r"(?<![\w-])output_mode\s*:")

# Prose form: "Output mode:" (optionally bulleted/bolded), case-insensitive.
_PROSE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?\*{0,2}output mode\*{0,2}\s*:", re.IGNORECASE
)

# Denylist: a line otherwise matching the key or prose form is NOT this
# artifact's own declaration when it is actually describing a DIFFERENT
# actor's output mode ("output mode for the receiving CA: ...").
_DENY_RE = re.compile(
    r"output[_ ]mode\s*:?\s*for\s+(the\s+)?"
    r"(receiving|downstream|future|reviewer|receiver|delegate|adjudicator)",
    re.IGNORECASE,
)

# Closed-set token match on a declaration line.
_TOKEN_RE = re.compile(
    r"\b(chat-only|file-write|review-report|paste-ready-chat|patch-queue)\b"
)


def is_declaration_line(line: str) -> bool:
    """True if `line` is this artifact's own output-mode declaration line.

    Pure function (testable)."""
    if not (_KEY_RE.search(line) or _PROSE_RE.search(line)):
        return False
    if _DENY_RE.search(line):
        return False
    return True


def tokens_in_line(line: str) -> list[str]:
    """Closed-set output-mode tokens present on `line`, in order.

    Pure function (testable)."""
    return _TOKEN_RE.findall(line)


class Finding(NamedTuple):
    source: str              # scanned file (repo-relative, forward slashes)
    kind: str                # "no_output_mode_declaration" | "no_recognized_output_mode_token"
    lineno: int | None       # offending line number, or None for no-declaration
    detail: str              # offending line text (stripped), or "" for no-declaration


class YamlBlock(NamedTuple):
    lineno: int
    fields: dict[str, tuple[str, int]]
    duplicate_fields: tuple[tuple[str, int], ...]


_BLOCK_HEADER_RE = re.compile(
    r"^(?P<indent>\s*)(?:[-*]\s+)?(?P<key>receiver_binding|receiver_creation_authorization)\s*:\s*$",
    re.IGNORECASE,
)
_FIELD_RE = re.compile(r"^\s*(?:[-*]\s+)?([a-z_]+)\s*:\s*(.*?)\s*$", re.IGNORECASE)
def _field_re(name: str) -> re.Pattern[str]:
    """One declared-field extraction regex (optionally bulleted/bolded key,
    captured value). `name` is a regex fragment, so a key with alternate
    spellings stays expressible (e.g. "edit[_ ]permission")."""
    return re.compile(
        r"^\s*(?:[-*]\s*)?(?:\*{0,2})?" + name + r"(?:\*{0,2})?\s*:\s*(.*?)\s*$",
        re.IGNORECASE,
    )


_EDIT_PERMISSION_RE = _field_re("edit[_ ]permission")
_CURRENT_AUTH_RE = _field_re("current_turn_authorization")
_SOURCE_FAILURE_RE = re.compile(
    r"^(?=.*(?:cannot|can't|unable|unavailable|fail(?:s|ed)?\s+to|missing))"
    r"(?=.*(?:load|loaded|read|access))"
    r"(?=.*(?:prompt-orchestration|prompt\s+contract|project-owned\s+(?:prompt\s+)?rules)).*$",
    re.IGNORECASE,
)
_STALE_FALLBACK_RE = re.compile(
    r"(?:fall\s*back|fallback|proceed|continue|rely|use).{0,120}"
    r"(?:memory|remembered|cached|stale|project-owned\s+(?:prompt\s+)?rules|known\s+rules)",
    re.IGNORECASE,
)
_MANUAL_WORKTREE_RE = re.compile(
    r"\bgit\s+(?:-[A-Za-z]\s+\S+\s+)*worktree\s+add\b|"
    r"\b(?:manually\s+create|create\s+(?:a\s+)?manual)\b.{0,80}\b(?:git\s+)?worktree\b",
    re.IGNORECASE,
)
_REPEAT_RECEIVER_RE = re.compile(
    r"\bcreate\b.{0,40}\b(?:another|second|additional|more)\b.{0,60}"
    r"\b(?:codex\s+)?(?:managed[- ]worktree\s+)?(?:task|receiver)\b|"
    r"\bretry\b.{0,60}\bcreate\b.{0,60}\b(?:task|receiver)\b",
    re.IGNORECASE,
)
_WRONG_TASK_STOP_RE = re.compile(
    r"\bif\b.{0,100}\b(?:(?:this\s+)?current\s+task|this\s+task)\b.{0,80}\bnot\b.{0,40}"
    r"\breceiver\b.{0,80}\bstop\b",
    re.IGNORECASE,
)
_NEGATION_RE = re.compile(r"\b(?:do\s+not|don't|never|must\s+not|prohibit(?:ed)?|forbid(?:den)?)\b", re.IGNORECASE)
_CLAUSE_BOUNDARY_RE = re.compile(
    r"[.;!?]\s*|\b(?:but|however|instead|then)\b", re.IGNORECASE
)


def _clean_value(value: str) -> str:
    value = value.strip().strip("`").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1].strip()
    return value


def _yaml_blocks(lines: list[str], key: str) -> list[YamlBlock]:
    """Extract simple indented YAML-ish blocks used by commission receipts."""
    blocks: list[YamlBlock] = []
    for index, line in enumerate(lines):
        match = _BLOCK_HEADER_RE.match(line)
        if not match or match.group("key").lower() != key:
            continue
        header_indent = len(match.group("indent"))
        fields: dict[str, tuple[str, int]] = {}
        duplicate_fields: list[tuple[str, int]] = []
        for child_index in range(index + 1, len(lines)):
            child = lines[child_index]
            if not child.strip() or child.lstrip().startswith("```"):
                continue
            child_indent = len(child) - len(child.lstrip())
            if child_indent <= header_indent:
                break
            field_match = _FIELD_RE.match(child)
            if field_match:
                field = field_match.group(1).lower()
                if field in fields:
                    duplicate_fields.append((field, child_index + 1))
                fields[field] = (
                    _clean_value(field_match.group(2)), child_index + 1
                )
        blocks.append(YamlBlock(index + 1, fields, tuple(duplicate_fields)))
    return blocks


def _declared_values(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[str, int]]:
    values: list[tuple[str, int]] = []
    for lineno, line in enumerate(lines, 1):
        match = pattern.match(line)
        if match:
            values.append((_clean_value(match.group(1)), lineno))
    return values


def _match_is_negated(text: str, match_start: int) -> bool:
    """True when the nearest same-clause negation governs this match."""
    prefix = text[:match_start]
    negations = list(_NEGATION_RE.finditer(prefix))
    if not negations:
        return False
    last_negation = negations[-1]
    return _CLAUSE_BOUNDARY_RE.search(prefix[last_negation.end():]) is None


def _has_positive_match(text: str, pattern: re.Pattern[str]) -> bool:
    return any(
        not _match_is_negated(text, match.start())
        for match in pattern.finditer(text)
    )


def _positive_matches(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    return [
        (lineno, line.strip())
        for lineno, line in enumerate(lines, 1)
        if _has_positive_match(line, pattern)
    ]


def evaluate_managed_receiver_lines(rel_source: str, lines: list[str]) -> list[Finding]:
    """Validate the deterministic shell of managed-receiver commissions."""
    findings: list[Finding] = []
    receiver_blocks = _yaml_blocks(lines, "receiver_binding")
    authorization_blocks = _yaml_blocks(lines, "receiver_creation_authorization")
    managed_blocks = [
        block for block in receiver_blocks
        if block.fields.get("receiver_class", ("", 0))[0] == "codex_managed_worktree"
    ]
    edit_values = _declared_values(lines, _EDIT_PERMISSION_RE)
    implementation_authorized = any(value == "implementation-authorized" for value, _ in edit_values)
    read_only_authority = any(
        value in {"read-only", "read_only_scoping_only", "scoping-only", "review-only"}
        for value, _ in edit_values + _declared_values(lines, _CURRENT_AUTH_RE)
    )

    relevant_blocks = (
        receiver_blocks + authorization_blocks
        if authorization_blocks or (implementation_authorized and managed_blocks)
        else []
    )
    for block in relevant_blocks:
        for field, lineno in block.duplicate_fields:
            findings.append(Finding(
                rel_source,
                "managed_receiver_duplicate_field",
                lineno,
                "duplicate %s field makes the managed-receiver shell ambiguous" % field,
            ))

    if authorization_blocks and (not implementation_authorized or read_only_authority):
        findings.append(Finding(
            rel_source,
            "receiver_creation_authority_on_read_only_commission",
            authorization_blocks[0].lineno,
            "receiver_creation_authorization is valid only for implementation-authorized commissions",
        ))

    if authorization_blocks and (len(receiver_blocks) != 1 or len(managed_blocks) != 1):
        findings.append(Finding(
            rel_source,
            "managed_receiver_binding_count",
            authorization_blocks[0].lineno,
            "receiver_creation_authorization requires exactly one codex_managed_worktree receiver_binding "
            "(found %d receiver block(s), %d managed)"
            % (len(receiver_blocks), len(managed_blocks)),
        ))
    elif authorization_blocks and len(managed_blocks) == 1:
        binding_state, lineno = managed_blocks[0].fields.get(
            "binding_state", ("", managed_blocks[0].lineno)
        )
        if binding_state != "receiver_to_verify":
            findings.append(Finding(
                rel_source,
                "managed_receiver_binding_state",
                lineno,
                "receiver_creation_authorization requires binding_state receiver_to_verify "
                "(got %r)" % binding_state,
            ))

    wrong_task_blocks = [
        block for block in managed_blocks
        if block.fields.get("binding_state", ("", 0))[0] in {"receiver_to_verify", "receiver_to_bind"}
    ]
    if implementation_authorized and wrong_task_blocks and len(receiver_blocks) == 1:
        if len(authorization_blocks) != 1:
            full_text = " ".join(line.strip() for line in lines)
            detail = "requires exactly one receiver_creation_authorization block"
            if len(authorization_blocks) == 0 and _WRONG_TASK_STOP_RE.search(full_text):
                detail += "; wrong-task stop text cannot replace the authorized managed-task creation path"
            findings.append(Finding(
                rel_source,
                "managed_receiver_creation_authorization_count",
                wrong_task_blocks[0].lineno,
                detail + " (found %d)" % len(authorization_blocks),
            ))
        else:
            receiver = wrong_task_blocks[0]
            authorization = authorization_blocks[0]
            exact_values = {
                "authorization": "create_exactly_one_fresh_codex_managed_worktree_task",
                "condition": "current_task_not_receiver_verified",
                "initial_prompt": "this_frozen_commission_verbatim",
                "dispatch": "immediate_same_turn",
            }
            allowed_fields = set(exact_values) | {
                "managed_starting_ref", "required_revision", "revision_mode"
            }
            unexpected_fields = sorted(set(authorization.fields) - allowed_fields)
            if unexpected_fields:
                findings.append(Finding(
                    rel_source,
                    "managed_receiver_authorization_field",
                    authorization.lineno,
                    "unexpected receiver_creation_authorization field(s): %s"
                    % ", ".join(unexpected_fields),
                ))
            for field, expected in exact_values.items():
                got, lineno = authorization.fields.get(field, ("", authorization.lineno))
                if got != expected:
                    findings.append(Finding(
                        rel_source,
                        "managed_receiver_authorization_field",
                        lineno,
                        "%s must equal %s (got %r)" % (field, expected, got),
                    ))
            for field in ("managed_starting_ref", "required_revision", "revision_mode"):
                expected, _ = receiver.fields.get(field, ("", receiver.lineno))
                got, lineno = authorization.fields.get(field, ("", authorization.lineno))
                if not expected or got != expected:
                    findings.append(Finding(
                        rel_source,
                        "managed_receiver_authorization_binding_mismatch",
                        lineno,
                        "%s must match receiver_binding value %r (got %r)" % (field, expected, got),
                    ))

    if managed_blocks:
        for lineno, detail in _positive_matches(lines, _MANUAL_WORKTREE_RE):
            findings.append(Finding(
                rel_source,
                "manual_git_worktree_substitution",
                lineno,
                "Codex managed receivers must be created as managed tasks; manual Git-worktree substitution is invalid: %r" % detail,
            ))
        for lineno, detail in _positive_matches(lines, _REPEAT_RECEIVER_RE):
            findings.append(Finding(
                rel_source,
                "repeat_receiver_creation_authority",
                lineno,
                "the commission may authorize at most one managed receiver: %r" % detail,
            ))

    source_failure_lines = [
        (index, line.strip()) for index, line in enumerate(lines)
        if _SOURCE_FAILURE_RE.search(line)
    ]
    if source_failure_lines and not any("SOURCE_CONTEXT_INCOMPLETE" in line for line in lines):
        index, detail = source_failure_lines[0]
        findings.append(Finding(
            rel_source,
            "source_context_failure_not_typed",
            index + 1,
            "controlling-source load failure must declare SOURCE_CONTEXT_INCOMPLETE: %r" % detail,
        ))
    for index, detail in source_failure_lines:
        window = " ".join(lines[index:min(len(lines), index + 3)])
        if _has_positive_match(window, _STALE_FALLBACK_RE):
            findings.append(Finding(
                rel_source,
                "stale_source_fallback",
                index + 1,
                "cannot continue from memory or project-rule fallback when controlling sources are unavailable: %r" % window.strip(),
            ))
            break

    return findings


def evaluate_file_lines(rel_source: str, lines: list[str]) -> tuple[Finding | None, list[str]]:
    """Scan one file's lines for the output-mode declaration shell.

    Returns (finding_or_none, info_notes). Multiple declaration lines and a
    declaration line with 2+ tokens are INFO notes only, never findings --
    that count/compound judgment stays resident (see module docstring).
    Pure function (testable)."""
    decl_lines = [
        (i, line, tokens_in_line(line))
        for i, line in enumerate(lines, 1)
        if is_declaration_line(line)
    ]

    info: list[str] = []
    if len(decl_lines) > 1:
        info.append(
            "multiple output-mode declaration lines (%d), first at line %d"
            % (len(decl_lines), decl_lines[0][0])
        )
    for lineno, _line, toks in decl_lines:
        if len(toks) >= 2:
            info.append(
                "line %d carries %d output-mode tokens: %s"
                % (lineno, len(toks), ", ".join(toks))
            )

    if not decl_lines:
        return Finding(rel_source, "no_output_mode_declaration", None, ""), info

    if all(len(toks) == 0 for _lineno, _line, toks in decl_lines):
        first_lineno, first_line, _toks = decl_lines[0]
        return (
            Finding(rel_source, "no_recognized_output_mode_token", first_lineno, first_line.strip()),
            info,
        )

    return None, info


def is_in_scope_file(rel_path: str) -> bool:
    """True if a path is in this gate's scanned set.

    Pure function (testable)."""
    p = rel_path.replace("\\", "/")
    if not p.endswith(".md"):
        return False
    if not p.startswith("docs/prompts/"):
        return False
    if p.startswith("docs/prompts/templates/"):
        return False
    if p.rsplit("/", 1)[-1] == "README.md":
        return False
    if "_scratch" in p or "node_modules" in p:
        return False
    if p.startswith("docs/_inbox/") or "/_inbox/" in p:
        return False
    return True


def extract_authority_tokens(text: str) -> frozenset[str] | None:
    """Closed-set tokens declared in the "## Output Modes" section of
    prompt-orchestration.md (the leading backticked token of each
    `- \\`token\\`: ...` bullet, up to the next `## ` heading).

    Returns None if the section cannot be found. Pure function (testable)."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Output Modes":
            start = i + 1
            break
    if start is None:
        return None
    bullet_re = re.compile(r"^-\s*`([a-z0-9\-]+)`\s*:")
    tokens: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        m = bullet_re.match(line)
        if m:
            tokens.append(m.group(1))
    return frozenset(tokens)


# ---------------------------------------------------------------------------
# Git plumbing (infra-gap fail-open)
# ---------------------------------------------------------------------------

def _git(root: Path, args: list[str], timeout: int = 15) -> tuple[int, str]:
    """Run a git command; return (returncode, stdout). Never raises.

    Thin adapter over the shared _hooklib.git_out (keeps this file's 15s
    default). git_out returns (1, "") on launch failure/timeout instead of
    (-1, ""); callers here only test rc != 0, so the distinction is inert."""
    return git_out(root, args, timeout=timeout)


def changed_scanned_files(root: Path, base_ref: str) -> list[str] | None:
    """Repo-relative in-scope .md paths changed in base...HEAD. None = infra gap."""
    if _git(root, ["rev-parse", "--verify", "--quiet", "HEAD"])[0] != 0:
        return None
    if _git(root, ["rev-parse", "--verify", "--quiet", base_ref])[0] != 0:
        return None
    code, out = _git(root, ["diff", "--name-status", "%s...HEAD" % base_ref])
    if code != 0:
        return None
    return [p for p in parse_name_status(out.splitlines()) if is_in_scope_file(p)]


def tracked_prompt_files(root: Path) -> list[str] | None:
    """All git-tracked paths under docs/prompts (for --audit). None = infra gap."""
    code, out = _git(root, ["ls-files", "--", "docs/prompts"])
    if code != 0:
        return None
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def scan_files(root: Path, rel_paths: list[str]) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    infos: list[str] = []
    for rel in rel_paths:
        norm = rel.replace("\\", "/")
        fpath = root / Path(norm)
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        finding, file_infos = evaluate_file_lines(norm, lines)
        if finding is not None:
            findings.append(finding)
        findings.extend(evaluate_managed_receiver_lines(norm, lines))
        for note in file_infos:
            infos.append("%s: %s" % (norm, note))
    return findings, infos


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def _print_findings(findings: list[Finding]) -> None:
    for f in findings:
        if f.kind == "no_output_mode_declaration":
            print("  %s  ->  no output-mode declaration found" % f.source)
        elif f.kind == "no_recognized_output_mode_token":
            print(
                "  %s:%d  ->  declaration line carries no recognized output-mode token: %r"
                % (f.source, f.lineno, f.detail)
            )
        else:
            location = "%s:%d" % (f.source, f.lineno) if f.lineno else f.source
            print("  %s  ->  %s: %s" % (location, f.kind, f.detail))


def _print_infos(infos: list[str]) -> None:
    for note in infos:
        print("  INFO  %s" % note)


def _print_rule() -> None:
    print(
        "rule: an in-scope prompt artifact must carry the applicable output-mode\n"
        "      and receiver-creation shells. Authority: %s.\n"
        "      Shape only, never runtime truth: not validation, not readiness."
        % RULE_AUTHORITY
    )


def run_strict(root: Path, cli_base: str | None) -> int:
    base_ref = resolve_base_ref(cli_base)
    rel_paths = changed_scanned_files(root, base_ref)
    if rel_paths is None:
        sys.stderr.write(
            "check_prompt_output_mode --strict: WARNING git diff vs %s unavailable; "
            "failing OPEN (infra gap, not a pass)\n" % base_ref
        )
        return 0
    findings, infos = scan_files(root, rel_paths)
    if findings:
        print(
            "check_prompt_output_mode --strict: %d finding(s) vs %s"
            % (len(findings), base_ref)
        )
        _print_findings(findings)
        _print_infos(infos)
        _print_rule()
        return 1
    print(
        "check_prompt_output_mode --strict: OK (0 findings in %d changed in-scope file(s) vs %s)"
        % (len(rel_paths), base_ref)
    )
    _print_infos(infos)
    return 0


def run_check(root: Path, cli_base: str | None, explicit_paths: list[str]) -> int:
    if explicit_paths:
        rel_paths = [p.replace("\\", "/") for p in explicit_paths]
        rel_paths = [p for p in rel_paths if is_in_scope_file(p)]
        scope_desc = "%d explicit path(s)" % len(rel_paths)
    else:
        base_ref = resolve_base_ref(cli_base)
        changed = changed_scanned_files(root, base_ref)
        if changed is None:
            print(
                "check_prompt_output_mode --check: git diff vs %s unavailable; nothing scanned"
                % base_ref
            )
            return 0
        rel_paths = changed
        scope_desc = "%d changed file(s) vs %s" % (len(rel_paths), base_ref)
    findings, infos = scan_files(root, rel_paths)
    print(
        "check_prompt_output_mode --check (advisory, exit 0): %d finding(s) in %s"
        % (len(findings), scope_desc)
    )
    _print_findings(findings)
    _print_infos(infos)
    return 0


def run_audit(root: Path) -> int:
    tracked = tracked_prompt_files(root)
    if tracked is None:
        print(
            "check_prompt_output_mode --audit: WARNING git ls-files unavailable; "
            "nothing scanned (infra gap, exit 0)"
        )
        return 0
    rel_paths = [p for p in tracked if is_in_scope_file(p)]
    findings, infos = scan_files(root, rel_paths)
    no_decl = sum(1 for f in findings if f.kind == "no_output_mode_declaration")
    no_token = sum(1 for f in findings if f.kind == "no_recognized_output_mode_token")
    failed_sources = {finding.source for finding in findings}
    passed = len(rel_paths) - len(failed_sources)
    print(
        "check_prompt_output_mode --audit (whole-corpus backlog view, exit 0; "
        "never a gate):"
    )
    print("  scanned in-scope files: %d" % len(rel_paths))
    print("  pass: %d" % passed)
    print("  no_output_mode_declaration: %d" % no_decl)
    print("  no_recognized_output_mode_token: %d" % no_token)
    print("  prompt_contract_findings: %d" % (
        len(findings) - no_decl - no_token
    ))
    _print_findings(findings)
    _print_infos(infos)
    print(
        "  Shape only, never truth: not validation, not readiness. "
        "Authority: %s." % RULE_AUTHORITY
    )
    return 0


def run_validate_stdin() -> int:
    """Gate one rendered prompt supplied on stdin (including chat couriers)."""
    text = sys.stdin.read()
    if not text.strip():
        print("check_prompt_output_mode --validate-stdin: 1 finding")
        _print_findings([Finding("<stdin>", "empty_prompt", None, "no prompt text supplied")])
        return 1
    lines = text.splitlines()
    output_finding, infos = evaluate_file_lines("<stdin>", lines)
    findings = [output_finding] if output_finding else []
    findings.extend(evaluate_managed_receiver_lines("<stdin>", lines))
    if findings:
        print(
            "check_prompt_output_mode --validate-stdin: %d finding(s)"
            % len(findings)
        )
        _print_findings(findings)
        _print_infos(infos)
        _print_rule()
        return 1
    print("check_prompt_output_mode --validate-stdin: OK (0 findings)")
    _print_infos(infos)
    return 0


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def selftest() -> int:
    ok = True

    def check(label: str, got: object, expected: object) -> None:
        nonlocal ok
        status = "PASS" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print("%s  %-58s  expect=%r got=%r" % (status, label, expected, got))

    # --- 1: YAML key + valid token -> declared, no finding ---
    print("--- declaration + token detection ---")
    f, info = evaluate_file_lines("f.md", ["output_mode: file-write"])
    check("1 key form + valid token -> no finding", f, None)

    # --- 2: indented/bulleted key form -> declared ---
    f, info = evaluate_file_lines("f.md", ["  - output_mode: chat-only"])
    check("2 indented/bulleted key form -> no finding", f, None)

    # --- 3: prose bullet -> declared ---
    f, info = evaluate_file_lines("f.md", ["- Output mode: `review-report`"])
    check("3 prose bullet -> no finding", f, None)

    # --- 4: prose plain -> declared ---
    f, info = evaluate_file_lines("f.md", ["Output mode: `chat-only`"])
    check("4 prose plain -> no finding", f, None)

    # --- 5: "output mode for the receiving CA:" -> NOT a declaration ---
    check(
        "5 'output mode for the receiving CA:' -> not a declaration",
        is_declaration_line("Output mode for the receiving CA: `chat-only`"),
        False,
    )
    f, info = evaluate_file_lines(
        "f.md", ["Output mode for the receiving CA: `chat-only`"]
    )
    check("5 file with only that line -> no_output_mode_declaration",
          f.kind if f else None, "no_output_mode_declaration")

    # --- 6: qualified keys -> NOT declarations ---
    check("6a receiver_output_mode: not a declaration",
          is_declaration_line("receiver_output_mode: file-write"), False)
    check("6b reviewer_output_mode: not a declaration",
          is_declaration_line("reviewer_output_mode: review-report"), False)
    check("6c downstream_review_output_mode: not a declaration",
          is_declaration_line("downstream_review_output_mode: review-report"), False)
    check("6d terminal_output_mode: not a declaration",
          is_declaration_line("terminal_output_mode: filed_prompt_plus_paste_ready_copy"),
          False)

    # --- 7: legacy token -> declaration with 0 valid tokens -> finding ---
    f, info = evaluate_file_lines("f.md", ["output_mode: filesystem-output"])
    check("7 legacy token -> no_recognized_output_mode_token",
          f.kind if f else None, "no_recognized_output_mode_token")

    # --- 8: empty value -> declaration, 0 tokens ---
    check("8 tokens_in_line empty value", tokens_in_line("output_mode:"), [])
    f, info = evaluate_file_lines("f.md", ["output_mode:"])
    check("8 file with only empty-value line -> finding",
          f.kind if f else None, "no_recognized_output_mode_token")

    # --- 9: compound tokens -> PASS + INFO ---
    f, info = evaluate_file_lines(
        "f.md",
        ["output_mode: file-write (this artifact) + paste-ready-chat (courier prompt)"],
    )
    check("9 compound tokens -> no finding", f, None)
    check("9 compound tokens -> INFO note present",
          any("2 output-mode tokens" in n for n in info), True)

    # --- 10: "paste-ready chat" (space, no hyphen) -> 0 tokens ---
    check("10 space-separated token variant -> 0 tokens",
          tokens_in_line("output_mode: paste-ready chat"), [])

    # --- 11: two valid declaration lines -> PASS + INFO, no finding ---
    f, info = evaluate_file_lines(
        "f.md",
        [
            "output_mode: file-write",
            "some body text",
            "- Output mode: `file-write`",
        ],
    )
    check("11 two valid declarations -> no finding", f, None)
    check("11 two valid declarations -> multiple-lines INFO note",
          any("multiple output-mode declaration lines" in n for n in info), True)

    # --- 12: no declaration at all -> finding ---
    f, info = evaluate_file_lines("f.md", ["nothing here about modes"])
    check("12 no declaration -> no_output_mode_declaration",
          f.kind if f else None, "no_output_mode_declaration")

    # --- 13: scope function ---
    print()
    print("--- is_in_scope_file ---")
    check("13a review prompt in scope",
          is_in_scope_file("docs/prompts/reviews/x_v0.md"), True)
    check("13b templates excluded",
          is_in_scope_file("docs/prompts/templates/shared/y.md"), False)
    check("13c docs/prompts/README.md excluded",
          is_in_scope_file("docs/prompts/README.md"), False)
    check("13d architecture prompt in scope",
          is_in_scope_file("docs/prompts/architecture/z.md"), True)
    check("13e docs/other excluded (wrong root)",
          is_in_scope_file("docs/other/a.md"), False)
    check("13f non-md excluded",
          is_in_scope_file("docs/prompts/reviews/x_v0.py"), False)

    # --- 14: token-drift insurance (real repo dependence) ---
    print()
    print("--- token-drift insurance (reads real authority file) ---")
    authority_path = repo_root() / ".agents" / "workflow-overlay" / "prompt-orchestration.md"
    if not authority_path.is_file():
        print("FAIL  authority file missing: %s" % authority_path)
        ok = False
    else:
        text = authority_path.read_text(encoding="utf-8")
        extracted = extract_authority_tokens(text)
        check("14 authority tokens == TOKENS constant (no drift)", extracted, TOKENS)

    # --- resolve_base_ref ---
    print()
    print("--- resolve_base_ref ---")
    saved_ci_base = os.environ.pop("FORSETI_DIFF_BASE", None)
    saved = os.environ.pop("GITHUB_BASE_REF", None)
    try:
        check("base default", resolve_base_ref(None), "origin/main")
        check("base cli", resolve_base_ref("some-branch"), "some-branch")
        os.environ["GITHUB_BASE_REF"] = "develop"
        check("base env wins", resolve_base_ref("ignored"), "origin/develop")
    finally:
        if saved is not None:
            os.environ["GITHUB_BASE_REF"] = saved
        else:
            os.environ.pop("GITHUB_BASE_REF", None)
        if saved_ci_base is not None:
            os.environ["FORSETI_DIFF_BASE"] = saved_ci_base
        else:
            os.environ.pop("FORSETI_DIFF_BASE", None)

    # --- parse_name_status ---
    print()
    print("--- parse_name_status ---")
    check(
        "A/M kept, D dropped, R keeps destination",
        parse_name_status([
            "A\tdocs/prompts/reviews/new_v0.md",
            "M\tdocs/prompts/architecture/a_v0.md",
            "D\tdocs/prompts/reviews/old_v0.md",
            "R100\tdocs/prompts/from_v0.md\tdocs/prompts/to_v0.md",
            "noise",
        ]),
        ["docs/prompts/reviews/new_v0.md", "docs/prompts/architecture/a_v0.md",
         "docs/prompts/to_v0.md"],
    )

    # --- managed receiver commission contract ---
    print()
    print("--- managed receiver commission contract ---")

    base_receiver = [
        "output_mode: paste-ready-chat",
        "edit_permission: implementation-authorized",
        "receiver_binding:",
        "  receiver_class: codex_managed_worktree",
        "  binding_state: receiver_to_verify",
        "  managed_starting_ref: origin/main",
        "  required_revision: 8cb44d080334453c384e39bc88fce510cbccfcde",
        "  revision_mode: ancestor",
    ]
    defective = base_receiver + [
        "If this current task is not the receiver, stop; do not create another worktree.",
        "If the controlling prompt contract cannot be freshly loaded, fall back to project-owned prompt rules.",
    ]
    got = evaluate_managed_receiver_lines("defective.md", defective)
    check(
        "managed defective omission/stop -> useful authorization finding",
        any(
            finding.kind == "managed_receiver_creation_authorization_count"
            and "wrong-task stop" in finding.detail
            for finding in got
        ),
        True,
    )
    check(
        "stale source fallback -> typed + fallback findings",
        {finding.kind for finding in got} >= {
            "source_context_failure_not_typed", "stale_source_fallback"
        },
        True,
    )

    corrected = base_receiver + [
        "receiver_creation_authorization:",
        "  authorization: create_exactly_one_fresh_codex_managed_worktree_task",
        "  condition: current_task_not_receiver_verified",
        "  managed_starting_ref: origin/main",
        "  required_revision: 8cb44d080334453c384e39bc88fce510cbccfcde",
        "  revision_mode: ancestor",
        "  initial_prompt: this_frozen_commission_verbatim",
        "  dispatch: immediate_same_turn",
        "If a controlling source cannot be freshly loaded, declare SOURCE_CONTEXT_INCOMPLETE and stop.",
        "Do not manually create, discover, or target a Git worktree.",
        "Do not create a second receiver.",
    ]
    check(
        "corrected managed commission -> no receiver finding",
        evaluate_managed_receiver_lines("corrected.md", corrected),
        [],
    )

    read_only = [
        "output_mode: chat-only",
        "edit_permission: read-only",
        "receiver_binding:",
        "  receiver_class: codex_managed_worktree",
        "  binding_state: receiver_to_verify",
        "  managed_starting_ref: origin/main",
        "  required_revision: 8cb44d080334453c384e39bc88fce510cbccfcde",
        "  revision_mode: ancestor",
    ]
    check(
        "read-only managed commission without creation block remains valid",
        evaluate_managed_receiver_lines("read_only.md", read_only),
        [],
    )
    check(
        "read-only commission with creation block is rejected",
        any(
            finding.kind == "receiver_creation_authority_on_read_only_commission"
            for finding in evaluate_managed_receiver_lines(
                "read_only_bad.md", read_only + corrected[8:16]
            )
        ),
        True,
    )

    manual = corrected + ["Run `git worktree add ../receiver origin/main` and continue there."]
    check(
        "manual Git-worktree substitution remains invalid",
        any(
            finding.kind == "manual_git_worktree_substitution"
            for finding in evaluate_managed_receiver_lines("manual.md", manual)
        ),
        True,
    )

    mixed_clause_manual = corrected + [
        "Do not pause; run `git worktree add ../receiver origin/main` and continue there."
    ]
    check(
        "unrelated same-line negation does not hide manual worktree creation",
        any(
            finding.kind == "manual_git_worktree_substitution"
            for finding in evaluate_managed_receiver_lines(
                "mixed_clause_manual.md", mixed_clause_manual
            )
        ),
        True,
    )

    mixed_clause_repeat = corrected + [
        "Do not wait; create another managed receiver task."
    ]
    check(
        "unrelated same-line negation does not hide repeated creation",
        any(
            finding.kind == "repeat_receiver_creation_authority"
            for finding in evaluate_managed_receiver_lines(
                "mixed_clause_repeat.md", mixed_clause_repeat
            )
        ),
        True,
    )

    orphan = [
        "output_mode: paste-ready-chat",
        "edit_permission: implementation-authorized",
        *corrected[8:16],
    ]
    check(
        "orphan creation authorization without receiver binding is rejected",
        any(
            finding.kind == "managed_receiver_binding_count"
            for finding in evaluate_managed_receiver_lines("orphan.md", orphan)
        ),
        True,
    )

    conflicting_binding = corrected + [
        "receiver_binding:",
        "  receiver_class: codex_managed_worktree",
        "  binding_state: receiver_to_verify",
        "  managed_starting_ref: other/ref",
        "  required_revision: deadbeef",
        "  revision_mode: exact",
    ]
    check(
        "multiple receiver bindings cannot hide a conflicting target",
        any(
            finding.kind == "managed_receiver_binding_count"
            for finding in evaluate_managed_receiver_lines(
                "conflicting_binding.md", conflicting_binding
            )
        ),
        True,
    )

    preparation_only_state = [
        line.replace("receiver_to_verify", "receiver_to_bind")
        for line in corrected
    ]
    check(
        "managed creation authorization rejects preparation-only binding state",
        any(
            finding.kind == "managed_receiver_binding_state"
            for finding in evaluate_managed_receiver_lines(
                "preparation_only_state.md", preparation_only_state
            )
        ),
        True,
    )

    duplicate_authorization = corrected.copy()
    duplicate_authorization.insert(
        duplicate_authorization.index(
            "  authorization: create_exactly_one_fresh_codex_managed_worktree_task"
        ),
        "  authorization: create_many_tasks",
    )
    check(
        "duplicate authorization fields cannot hide broader authority",
        any(
            finding.kind == "managed_receiver_duplicate_field"
            for finding in evaluate_managed_receiver_lines(
                "duplicate_authorization.md", duplicate_authorization
            )
        ),
        True,
    )

    broadened_authorization = corrected.copy()
    broadened_authorization.insert(
        broadened_authorization.index("  dispatch: immediate_same_turn") + 1,
        "  allow_repeat: true",
    )
    check(
        "unexpected authorization field cannot broaden the exact shell",
        any(
            finding.kind == "managed_receiver_authorization_field"
            for finding in evaluate_managed_receiver_lines(
                "broadened_authorization.md", broadened_authorization
            )
        ),
        True,
    )

    multiline_stale = corrected + [
        "If the controlling prompt contract cannot be freshly loaded,",
        "continue from remembered rules.",
    ]
    check(
        "multiline stale-memory fallback remains invalid despite typed clause",
        any(
            finding.kind == "stale_source_fallback"
            for finding in evaluate_managed_receiver_lines(
                "multiline_stale.md", multiline_stale
            )
        ),
        True,
    )

    print()
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _arg_value(argv: list[str], flag: str) -> str | None:
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return None


def _collect_check_paths(argv: list[str]) -> list[str]:
    """Positional path arguments given alongside --check (excludes recognized
    flags and the --base value). Empty when --check is used without paths."""
    known_flags = {
        "--strict", "--check", "--audit", "--selftest", "--validate-stdin",
        "--force-internal-error"
    }
    paths: list[str] = []
    skip_next = False
    for tok in argv:
        if skip_next:
            skip_next = False
            continue
        if tok == "--base":
            skip_next = True
            continue
        if tok in known_flags:
            continue
        paths.append(tok)
    return paths


def main(argv: list[str]) -> int:
    # Forced-exception probe: proves the __main__ gating handler
    # (forseti-harness/tests/unit/test_hook_internal_error_gating.py).
    if "--force-internal-error" in argv:
        raise RuntimeError("forced internal error (probe)")
    if "--selftest" in argv:
        return selftest()
    if "--validate-stdin" in argv:
        return run_validate_stdin()
    root = repo_root()
    cli_base = _arg_value(argv, "--base")
    if "--strict" in argv:
        return run_strict(root, cli_base)
    if "--check" in argv:
        return run_check(root, cli_base, _collect_check_paths(argv))
    if "--audit" in argv:
        return run_audit(root)
    print(
        "Usage: check_prompt_output_mode.py --strict [--base <ref>] | "
        "--check [--base <ref>] [paths...] | --audit | --selftest | --validate-stdin"
    )
    print("  --strict    CI gate: exit 1 if a changed in-scope prompt lacks a")
    print("              recognized output-mode declaration")
    print("  --check     same scan, human-readable, always exit 0; explicit")
    print("              paths scan those files directly instead of the diff")
    print("  --audit     whole-corpus backlog view, always exit 0 (never a gate)")
    print("  --selftest  pure-function self-check")
    print("  --validate-stdin  gate one rendered prompt supplied on stdin")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:
        # GATE FAIL bucket in gating modes (validation-gates.md): an internal
        # checker bug must not read as a green gate. Advisory modes fail open
        # so a bug never bricks the agent.
        sys.stderr.write("check_prompt_output_mode: internal error: %s\n" % exc)
        gating = any(
            flag in sys.argv[1:]
            for flag in ("--strict", "--selftest", "--validate-stdin")
        )
        sys.exit(1 if gating else 0)
