#!/usr/bin/env python3
"""Validate scan receipts, Capture handoff boundaries, and Creator Registry receipts.

This is a local/manual checker with a forward-only changed-file mode for CI.
It does not run retrieval, grade signal quality, validate candidates, bind
Capture routes, or prove a scan is good. It only checks that a CSB-first scan
artifact preserves the mechanical receipt shape needed for review: source
context, caps, broad-scout accounting, CSB-row accountability, exact-query
accounting, venue/hidden-venue accounting, observations, negatives/access notes,
capture-request accounting, bounded candidate closeout, and mechanical
engagement/resonance overclaim language. For scan artifacts that cite Creator
Registry match preflight receipts, it also checks the cited receipt file exists
and that capture-request preflight fields match receipt result rows.

For changed Markdown research artifacts, it also rejects a Capture-owned YAML
receipt that calls itself a collection-completion receipt or claims terminal
acquisition / Evidence Consolidation readiness. Capture can close a bounded
batch; only the validator-backed phase acquisition seal can close acquisition.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hooklib import repo_root  # noqa: E402  (sys.path pin must precede the import)

YAML_FENCE_RE = re.compile(r"```yaml\s*(?P<body>.*?)\s*```", re.IGNORECASE | re.DOTALL)
HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
MOVE_ID_RE = re.compile(r"\bM\d{2,}\b")
EXACT_QUERY_ID_RE = re.compile(r"\bEQ-\d{3,}\b")
CSB_ROW_ID_RE = re.compile(r"\bSBR-\d{3,}\b")

SCAN_RECEIPT_VERSION_FIELD = "scan_receipt_version"
LEGACY_SCAN_RECEIPT_VERSION = 0
CURRENT_SCAN_RECEIPT_VERSION = 1
SUPPORTED_SCAN_RECEIPT_VERSIONS = {
    LEGACY_SCAN_RECEIPT_VERSION,
    CURRENT_SCAN_RECEIPT_VERSION,
}
LEGACY_SCAN_RECEIPT_PATHS = frozenset(
    {
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_broad_scout_deep_scan_v0.md",
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_buyer_language_rerun_v0.md",
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_core_satellite_csb_v0.md",
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_csb_first_venue_eval_v0.md",
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_demand_origin_discovery_v0.md",
        "docs/research/orca_discovery_candidate_scan_imaginary_authors_mgt_v0.md",
    }
)

REQUIRED_INTAKE_FIELDS = {
    "commission_id",
    SCAN_RECEIPT_VERSION_FIELD,
    "scan_date",
    "mode",
    "subject",
    "source_context_status",
    "run_caps",
    "screening_moves_used",
    "exact_queries_used",
    "closeout_state",
}
REQUIRED_RUN_CAPS = {"max_screening_moves_total", "max_exact_queries_total"}
VALID_CLOSEOUT_STATES = {
    "candidate_ready_for_next_lane",
    "capture_preservation_only",
    "no_candidate_after_discovery",
}
VALID_SOURCE_CONTEXT_STATUS = "SOURCE_CONTEXT_READY"
VALID_SIGNAL_STAGES = {
    "venue_value",
    "precursor",
    "candidate_support",
    "contradiction",
    "negative",
    "access_note",
    "unknown",
}
VALID_GATE_ROLES = {
    "none",
    "demand_origin",
    "costly_behavior",
    "divergence",
    "org_motion",
    "decision_event",
    "influence",
}
VALID_ROUTE_BINDING_STATES = {
    "cited_current",
    "unknown",
    "blocked_outside_current_binding",
    "not_applicable",
}
AUTO_SCAN_PREFIXES = ("docs/research/",)
CAPTURE_HANDOFF_ARTIFACT_KINDS = {
    "capture_batch_handoff_receipt",
    "collection_completion_receipt",
}
CAPTURE_HANDOFF_KIND_RE = re.compile(
    r"^[ \t]*artifact_kind[ \t]*:[ \t]*['\"]?"
    r"(?:capture_batch_handoff_receipt|collection_completion_receipt)['\"]?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
FORBIDDEN_CAPTURE_TERMINAL_STATUSES = {
    "acquisition_complete",
    "collection_complete",
    "collection_complete_ready_for_consolidation",
    "material_saturation_proven",
    "ready_for_consolidation",
    "sealed_ready_for_deliver",
}
AUTO_SCAN_REQUIRED_MARKERS = (
    "commission_id:",
    "source_context_status:",
    "closeout_state:",
)
AUTO_SCAN_ROUTE_MARKERS = (
    "csb-first",
    "csb board",
    "csb_rows_consumed",
    "rows consumed as route map",
)
CREATOR_REGISTRY_PREFLIGHT_MARKERS = (
    "creator_registry_match_preflight:",
    "receipt_path:",
)
REQUIRED_OBSERVATION_FIELDS = {
    "observation_id",
    "source_move_id",
    "url",
    "retrieval_date",
    "short_quote_or_summary",
    "signal_stage",
    "claim_it_might_support",
    "gate_role",
    "independence_hypothesis",
    "uncertainty_or_limits",
}
REQUIRED_CANDIDATE_OBSERVATION_FIELDS = {
    "candidate_observation_id",
    "candidate",
    "supporting_observations",
    "why_promoted",
    "decision_window",
    "competing_or_defeating_observations",
    "capture_needed",
}
REQUIRED_CAPTURE_REQUEST_FIELDS = {
    "capture_request_id",
    "source_scan",
    "candidate_or_observation_ids",
    "urls",
    "what_capture_should_verify",
    "decision_window",
    "route_binding_state",
    "creator_registry_match_preflight",
    "screening_evidence_summary",
    "uncertainty_or_access_limits",
    "not_requested",
}
REQUIRED_CREATOR_REGISTRY_PREFLIGHT_FIELDS = {
    "required_when",
    "receipt_path",
    "intended_action",
    "decision",
    "action_status",
    "can_start_new_capture",
}
VALID_CREATOR_REGISTRY_REQUIRED_WHEN = {"new_social_creator_account_capture", "not_applicable"}
NOT_APPLICABLE_ALLOWED_PREFLIGHT_VOCAB = {"", "not_applicable"}
VALID_CREATOR_REGISTRY_INTENDED_ACTIONS = {"new_capture", "classify", "update_existing", "not_applicable"}
VALID_CREATOR_REGISTRY_DECISIONS = {"existing_match", "new_candidate", "ambiguous_match", "invalid_candidate", "not_applicable"}
VALID_CREATOR_REGISTRY_ACTION_STATUSES = {"allowed", "blocked", "not_applicable"}
CREATOR_REGISTRY_RECEIPT_ROOT = "creator_registry_match_preflight_receipt"
CREATOR_REGISTRY_RECEIPT_SCHEMA = "creator_registry_match_preflight_receipt_v0"
PLACEHOLDER_PREFLIGHT_RECEIPT_VALUES = {
    "",
    "none",
    "null",
    "null_or_path",
    "not_applicable",
    "unknown",
    "unknown_with_reason",
    "path",
    "path_to_preflight_receipt_json",
}
REQUIRED_CAPTURE_URL_FIELDS = {"url", "venue", "observation_supported", "gate_role"}
REQUIRED_NOT_REQUESTED = {
    "route_expansion",
    "packet_commitment_by_scanning",
    "ecr_cleaning_or_judgment_work",
}

SECTION_PATTERNS = {
    "broad_scout_accounting": re.compile(r"^##\s+Broad Scout\b", re.IGNORECASE | re.MULTILINE),
    "csb_row_accounting": re.compile(
        r"(csb_rows_consumed|Rows consumed as route map:)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "exact_query_accounting": re.compile(
        r"^##\s+Exact Query Discovery Ledger\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "venue_evaluation": re.compile(r"^##\s+Venue Evaluation\b", re.IGNORECASE | re.MULTILINE),
    "hidden_venue_accounting": re.compile(
        r"^##\s+Hidden Venue Pointers\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "observations": re.compile(r"^##\s+(Screen-Light Observations|Observations)\b", re.IGNORECASE | re.MULTILINE),
    "negatives_access_notes": re.compile(r"^##\s+Negatives And Access Notes\b", re.IGNORECASE | re.MULTILINE),
    "capture_request_accounting": re.compile(
        r"^##\s+(Capture Requests|Capture Triage)\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "candidate_decision": re.compile(
        r"^##\s+(Candidate Decision|Candidate Observation Decision)\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "closeout": re.compile(r"^##\s+Closeout\b", re.IGNORECASE | re.MULTILINE),
}

BROAD_SCOUT_DETAIL_PATTERNS = {
    "frontier": re.compile(r"\bfrontiers?\b", re.IGNORECASE),
    "exact_query": re.compile(r"\b(exact[-_ ]?quer(y|ies)|EQ-\d{3,})\b", re.IGNORECASE),
    "venue_eval": re.compile(r"\b(venue[_ -]?eval|venue evaluation|venues?)\b", re.IGNORECASE),
    "hidden_venue_pointer": re.compile(r"\b(hidden venue|hidden_venue_pointer)\b", re.IGNORECASE),
    "negative": re.compile(r"\bnegatives?\b", re.IGNORECASE),
    "access_note": re.compile(r"\b(access notes?|access walls?)\b", re.IGNORECASE),
    "recency_current_state": re.compile(r"\b(recency|recent|currentness|current-state|current state)\b", re.IGNORECASE),
    "main_deepening": re.compile(
        r"\b(main deepening|recommended(?: main)? deepening|recommended for deepening|targeted deepening|deepening (?:phase|path|direction|recommendation)|deepen(?:ing)?)\b",
        re.IGNORECASE,
    ),
}

ENGAGEMENT_RULE_AUTHORITY = "forseti/product/shared/engagement_registry/engagement_logic_registry_v0.md"
ENGAGEMENT_SIGNAL_RE = (
    r"(?:engagement(?:\s+counts?)?|public[- ]reaction|reaction\s+volume|"
    r"high[- ]engagement|low[- ]engagement|upvotes?|helpful\s+votes?|likes?|"
    r"views?|shares?|comments?|reply\s+counts?|source[- ]native\s+scores?|"
    r"source\s+rank|source\s+order|visible\s+sort|visible\s+rank|resonance)"
)
ENGAGEMENT_CLAIM_GAP = r"[^.\n;]{0,80}"
NEGATED_OVERCLAIM_RE = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|must\s+not|does\s+not|do\s+not|"
    r"don't|is\s+not|are\s+not|not\s+enough\s+to)\b",
    re.IGNORECASE,
)
ENGAGEMENT_OVERCLAIM_PATTERNS = {
    "engagement_as_proof": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:proves?|proof|validates?|confirms?|"
        rf"establishes|demonstrates|clears?|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:demand|buyer\s+pull|"
        rf"willingness\s+to\s+pay|market\s+pull|purchase\s+intent)\b|"
        rf"\b(?:demand|buyer\s+pull|willingness\s+to\s+pay|market\s+pull|purchase\s+intent)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is\s+)?(?:proven|proved|validated|confirmed|established|demonstrated|cleared|"
        rf"proof)\b{ENGAGEMENT_CLAIM_GAP}\b(?:by|from|because\s+of|due\s+to|through|via)\b{ENGAGEMENT_CLAIM_GAP}\b"
        rf"{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_gate_clearance_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:clears?|passes?|satisfies|unlocks?|"
        rf"establishes|justifies?|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:gate(?:\s+clearance)?|"
        rf"demand\s+gate|admissibility|candidate\s+clearance)\b|"
        rf"\b(?:gate(?:\s+clearance)?|demand\s+gate|admissibility|candidate\s+clearance)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|cleared|passed|satisfied|unlocked|established|justified|"
        rf"because\s+of|due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_route_binding_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:binds?|sets?|selects?|authorizes?|clears?|"
        rf"recommends?|establishes)\b{ENGAGEMENT_CLAIM_GAP}\b(?:Capture\s+route|capture\s+method|"
        rf"route[_ -]?binding(?:[_ -]?state)?|source[- ]access\s+route|capture[- ]owned\s+route)\b|"
        rf"\b(?:Capture\s+route|capture\s+method|route[_ -]?binding(?:[_ -]?state)?|"
        rf"source[- ]access\s+route|capture[- ]owned\s+route)\b{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|bound|set|"
        rf"selected|authorized|cleared|recommended|established|because\s+of|due\s+to|from|by|"
        rf"based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_graph_weight_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:sets?|determines|drives|raises|"
        rf"increases|justifies|supports?|becomes|is|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:graph[_ -]?weight"
        rf"(?:[_ -]?hint)?|graph\s+score|graph\s+strength)\b|"
        rf"\b(?:graph[_ -]?weight(?:[_ -]?hint)?|graph\s+score|graph\s+strength)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|becomes|sets?|determined|driven|raised|increased|justified|supported|"
        rf"because\s+of|due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_credibility_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:proves?|confirms?|establishes|"
        rf"supports?|justifies?|sets?|labels?|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:credibility|credible|"
        rf"independence|trustworthy|trust)\b|"
        rf"\b(?:credibility|credible|independence|trustworthy|trust)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|proven|confirmed|established|supported|justified|set|labeled|"
        rf"because\s+of|due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_amplification_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:proves?|confirms?|establishes|"
        rf"decides|labels?|sets?|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:artificial\s+amplification|"
        rf"amplification|manipulation|bot(?:-like)?\s+activity)\b|"
        rf"\b(?:artificial\s+amplification|amplification|manipulation|bot(?:-like)?\s+activity)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|proven|confirmed|established|decided|labeled|set|because\s+of|"
        rf"due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_action_ceiling_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:clears?|sets?|raises|supports?|"
        rf"justifies?|establishes|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\bAction\s+Ceiling\b|"
        rf"\bAction\s+Ceiling\b{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|cleared|set|raised|supported|justified|"
        rf"established|because\s+of|due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b"
        rf"{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_final_resonance_weight": re.compile(r"\bfinal\s+resonance\s+weight\b", re.IGNORECASE),
}
FORBIDDEN_TEXT_PATTERNS = {
    "recency_as_proof": re.compile(
        r"\b(recency|recent|currentness|current-state|current state)\b.{0,60}\b(proves|proof|gate clearance|clears? gate|demand verdict)\b",
        re.IGNORECASE,
    ),
    "scanning_binds_capture": re.compile(
        r"\b(scan|scanning)\b.{0,60}\b(bind|binds|sets|selects)\b.{0,40}\bCapture\b.{0,40}\b(route|method)\b",
        re.IGNORECASE,
    ),
    "capture_authorized_by_scan": re.compile(
        r"\bCapture\b.{0,40}\b(authorized|route-bound|route bound)\b.{0,40}\b(scan|scanning)\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


def _normalize_vocab(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _yaml_blocks(text: str) -> tuple[list[Any], list[Finding]]:
    blocks: list[Any] = []
    findings: list[Finding] = []
    for index, match in enumerate(YAML_FENCE_RE.finditer(text), start=1):
        try:
            blocks.append(yaml.safe_load(match.group("body")) or {})
        except yaml.YAMLError as exc:
            findings.append(Finding("invalid_yaml_fence", f"YAML fence {index} is invalid: {exc}"))
    return blocks, findings


def _find_intake(blocks: list[Any]) -> dict[str, Any] | None:
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if "commission_id" in block:
            return block
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def _has_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _is_url(value: Any) -> bool:
    return isinstance(value, str) and re.match(r"https?://", value.strip(), re.IGNORECASE) is not None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def _is_iso_date(value: Any) -> bool:
    if isinstance(value, date):
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


def _iter_dict_records(value: Any, required_key: str) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if required_key in value:
            yield value
        for child in value.values():
            yield from _iter_dict_records(child, required_key)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dict_records(child, required_key)


def _records(blocks: list[Any], required_key: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for block in blocks:
        records.extend(_iter_dict_records(block, required_key))
    return records


def _mapping_values(value: Any, key_name: str) -> Iterable[Any]:
    if isinstance(value, dict):
        for key, child in value.items():
            if _normalize_vocab(key) == key_name:
                yield child
            yield from _mapping_values(child, key_name)
    elif isinstance(value, list):
        for child in value:
            yield from _mapping_values(child, key_name)


def _section_body(text: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = HEADING_RE.search(text, start)
    end = next_heading.start() if next_heading else len(text)
    return text[start:end]


def _required_missing(record: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in record or not _has_text(record.get(field)))


def _validate_intake(intake: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []

    missing = sorted(REQUIRED_INTAKE_FIELDS - set(intake))
    if missing:
        findings.append(
            Finding("missing_intake_fields", "Scan intake receipt is missing fields: " + ", ".join(missing))
        )

    status = intake.get("source_context_status")
    if status != VALID_SOURCE_CONTEXT_STATUS:
        findings.append(
            Finding(
                "source_context_not_ready",
                f"source_context_status must be {VALID_SOURCE_CONTEXT_STATUS}, got {status or '<blank>'}.",
            )
        )

    closeout = _normalize_vocab(intake.get("closeout_state"))
    if closeout not in VALID_CLOSEOUT_STATES:
        findings.append(
            Finding(
                "invalid_closeout_state",
                "closeout_state must be one of "
                + ", ".join(sorted(VALID_CLOSEOUT_STATES))
                + f", got {intake.get('closeout_state')}.",
            )
        )

    run_caps = intake.get("run_caps")
    if not isinstance(run_caps, dict):
        findings.append(Finding("missing_run_caps", "run_caps must be a mapping."))
        return findings

    missing_caps = sorted(REQUIRED_RUN_CAPS - set(run_caps))
    if missing_caps:
        findings.append(Finding("missing_run_cap_fields", "run_caps is missing fields: " + ", ".join(missing_caps)))

    _validate_used_within_cap(
        findings,
        intake,
        run_caps,
        "screening_moves_used",
        "max_screening_moves_total",
        "screening_moves_exceed_cap",
    )
    _validate_used_within_cap(
        findings,
        intake,
        run_caps,
        "exact_queries_used",
        "max_exact_queries_total",
        "exact_queries_exceed_cap",
    )

    return findings


def _receipt_version_findings(intake: dict[str, Any] | None) -> tuple[int | None, list[Finding]]:
    if intake is None:
        return None, []
    if SCAN_RECEIPT_VERSION_FIELD not in intake:
        return None, [
            Finding(
                "missing_scan_receipt_version",
                f"Scan intake receipt must declare {SCAN_RECEIPT_VERSION_FIELD}: {CURRENT_SCAN_RECEIPT_VERSION} "
                "or an explicit supported legacy version.",
            )
        ]
    version = _as_int(intake.get(SCAN_RECEIPT_VERSION_FIELD))
    if version is None or version not in SUPPORTED_SCAN_RECEIPT_VERSIONS:
        return None, [
            Finding(
                "unsupported_scan_receipt_version",
                f"{SCAN_RECEIPT_VERSION_FIELD} must be one of "
                + ", ".join(str(item) for item in sorted(SUPPORTED_SCAN_RECEIPT_VERSIONS))
                + f", got {intake.get(SCAN_RECEIPT_VERSION_FIELD)!r}.",
            )
        ]
    return version, []


def _validate_used_within_cap(
    findings: list[Finding],
    intake: dict[str, Any],
    run_caps: dict[str, Any],
    used_field: str,
    cap_field: str,
    code: str,
) -> None:
    used = _as_int(intake.get(used_field))
    cap = _as_int(run_caps.get(cap_field))
    if used is None and used_field in intake:
        findings.append(Finding("invalid_numeric_field", f"{used_field} must be a non-negative integer."))
    if cap is None and cap_field in run_caps:
        findings.append(Finding("invalid_numeric_field", f"{cap_field} must be a non-negative integer."))
    if used is None or cap is None:
        return
    if used > cap:
        findings.append(Finding(code, f"{used_field}={used} exceeds {cap_field}={cap}."))


def _validate_required_receipt_parts(text: str, intake: dict[str, Any] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for name, pattern in SECTION_PATTERNS.items():
        if pattern.search(text):
            continue
        if name == "capture_request_accounting" and isinstance(intake, dict):
            if _as_int(intake.get("capture_requests")) == 0:
                continue
        findings.append(Finding(f"missing_{name}", f"Missing required CSB-first scan receipt part: {name}."))
    return findings


def _validate_broad_scout_detail(text: str) -> list[Finding]:
    if not SECTION_PATTERNS["broad_scout_accounting"].search(text):
        return []
    body = _section_body(text, SECTION_PATTERNS["broad_scout_accounting"])
    missing = sorted(name for name, pattern in BROAD_SCOUT_DETAIL_PATTERNS.items() if not pattern.search(body))
    if missing:
        return [Finding("missing_broad_scout_detail", "Broad Scout section is missing: " + ", ".join(missing))]
    return []


def _validate_csb_row_ids(text: str) -> list[Finding]:
    if SECTION_PATTERNS["csb_row_accounting"].search(text) and not CSB_ROW_ID_RE.search(text):
        return [Finding("missing_csb_row_ids", "CSB row accounting must cite at least one SBR-NNN row id.")]
    return []


def _validate_count_consistency(text: str, blocks: list[Any], intake: dict[str, Any] | None) -> list[Finding]:
    if not isinstance(intake, dict):
        return []
    findings: list[Finding] = []
    checks = [
        ("screening_moves_used", len(set(MOVE_ID_RE.findall(text))), "screening_moves_count_mismatch"),
        ("exact_queries_used", len(set(EXACT_QUERY_ID_RE.findall(text))), "exact_queries_count_mismatch"),
        ("hidden_venue_pointers", len(_records(blocks, "hidden_venue_pointer_id")), "hidden_venue_pointer_count_mismatch"),
        ("capture_requests", len(_records(blocks, "capture_request_id")), "capture_request_count_mismatch"),
    ]
    for field, observed, code in checks:
        declared = _as_int(intake.get(field))
        if declared is None:
            continue
        if declared != observed:
            findings.append(Finding(code, f"{field}={declared} but artifact records {observed}."))
    return findings


def _validate_observations(blocks: list[Any]) -> list[Finding]:
    observations = _records(blocks, "observation_id")
    if not observations:
        return [Finding("missing_observation_records", "Observations section must include at least one observation_id YAML record.")]

    findings: list[Finding] = []
    for observation in observations:
        obs_id = observation.get("observation_id", "<unknown>")
        missing = _required_missing(observation, REQUIRED_OBSERVATION_FIELDS)
        if missing:
            findings.append(Finding("missing_observation_fields", f"Observation {obs_id} is missing: {', '.join(missing)}."))
        if "url" in observation and not _is_url(observation.get("url")):
            findings.append(Finding("invalid_observation_url", f"Observation {obs_id} url must be http(s)."))
        if "retrieval_date" in observation and not _is_iso_date(observation.get("retrieval_date")):
            findings.append(Finding("invalid_observation_retrieval_date", f"Observation {obs_id} retrieval_date must be YYYY-MM-DD."))
        if "signal_stage" in observation:
            signal_stage = _normalize_vocab(observation.get("signal_stage"))
            if signal_stage not in VALID_SIGNAL_STAGES:
                findings.append(
                    Finding("invalid_signal_stage", f"Observation {obs_id} signal_stage must be one of {', '.join(sorted(VALID_SIGNAL_STAGES))}.")
                )
        if "gate_role" in observation:
            gate_role = _normalize_vocab(observation.get("gate_role"))
            if gate_role not in VALID_GATE_ROLES:
                findings.append(
                    Finding("invalid_gate_role", f"Observation {obs_id} gate_role must be one of {', '.join(sorted(VALID_GATE_ROLES))}.")
                )
    return findings


def _validate_candidate_observations(blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    for candidate_obs in _records(blocks, "candidate_observation_id"):
        candidate_obs_id = candidate_obs.get("candidate_observation_id", "<unknown>")
        missing = _required_missing(candidate_obs, REQUIRED_CANDIDATE_OBSERVATION_FIELDS)
        if missing:
            findings.append(
                Finding(
                    "missing_candidate_observation_fields",
                    f"Candidate observation {candidate_obs_id} is missing: {', '.join(missing)}.",
                )
            )
        capture_needed = _normalize_vocab(candidate_obs.get("capture_needed"))
        if capture_needed and capture_needed not in {"yes", "no", "unknown"}:
            findings.append(
                Finding("invalid_capture_needed", f"Candidate observation {candidate_obs_id} capture_needed must be yes/no/unknown.")
            )
    return findings


def _validate_creator_registry_match_preflight(request_id: Any, request: dict[str, Any]) -> list[Finding]:
    preflight = request.get("creator_registry_match_preflight")
    if not isinstance(preflight, dict):
        return [
            Finding(
                "invalid_creator_registry_match_preflight",
                f"Capture request {request_id} creator_registry_match_preflight must be a mapping with required_when.",
            )
        ]

    findings: list[Finding] = []
    required_when = _normalize_vocab(preflight.get("required_when"))
    if required_when not in VALID_CREATOR_REGISTRY_REQUIRED_WHEN:
        findings.append(
            Finding(
                "invalid_creator_registry_match_preflight_required_when",
                "creator_registry_match_preflight.required_when must be new_social_creator_account_capture or not_applicable.",
            )
        )
        return findings

    if required_when == "not_applicable":
        disallowed = [
            field
            for field in ("intended_action", "decision", "action_status")
            if _normalize_vocab(preflight.get(field)) not in NOT_APPLICABLE_ALLOWED_PREFLIGHT_VOCAB
        ]
        if "receipt_path" in preflight and _normalize_vocab(
            preflight.get("receipt_path")
        ) not in PLACEHOLDER_PREFLIGHT_RECEIPT_VALUES:
            disallowed.append("receipt_path")
        can_start = preflight.get("can_start_new_capture")
        if _as_bool(can_start) is True or _normalize_vocab(can_start) not in (
            NOT_APPLICABLE_ALLOWED_PREFLIGHT_VOCAB | {"false"}
        ):
            disallowed.append("can_start_new_capture")
        if disallowed:
            findings.append(
                Finding(
                    "contradictory_creator_registry_match_preflight_not_applicable",
                    f"Capture request {request_id} creator_registry_match_preflight is not_applicable but also carries: {', '.join(disallowed)}.",
                )
            )
        return findings

    missing = _required_missing(preflight, REQUIRED_CREATOR_REGISTRY_PREFLIGHT_FIELDS)
    if missing:
        findings.append(
            Finding(
                "missing_creator_registry_match_preflight_fields",
                f"Capture request {request_id} creator_registry_match_preflight is missing: {', '.join(missing)}.",
            )
        )
        return findings

    receipt_path = preflight.get("receipt_path")
    if not isinstance(receipt_path, str) or _normalize_vocab(receipt_path) in PLACEHOLDER_PREFLIGHT_RECEIPT_VALUES:
        findings.append(
            Finding(
                "invalid_creator_registry_match_preflight_receipt_path",
                f"Capture request {request_id} must cite a concrete Creator Registry preflight receipt path.",
            )
        )

    intended_action = _normalize_vocab(preflight.get("intended_action"))
    decision = _normalize_vocab(preflight.get("decision"))
    action_status = _normalize_vocab(preflight.get("action_status"))
    can_start = _as_bool(preflight.get("can_start_new_capture"))

    if intended_action not in VALID_CREATOR_REGISTRY_INTENDED_ACTIONS:
        findings.append(Finding("invalid_creator_registry_preflight_intended_action", f"Capture request {request_id} has invalid intended_action."))
    if decision not in VALID_CREATOR_REGISTRY_DECISIONS:
        findings.append(Finding("invalid_creator_registry_preflight_decision", f"Capture request {request_id} has invalid decision."))
    if action_status not in VALID_CREATOR_REGISTRY_ACTION_STATUSES:
        findings.append(Finding("invalid_creator_registry_preflight_action_status", f"Capture request {request_id} has invalid action_status."))
    if intended_action != "new_capture" or decision != "new_candidate" or action_status != "allowed" or can_start is not True:
        findings.append(
            Finding(
                "creator_registry_preflight_does_not_clear_new_capture",
                f"Capture request {request_id} new social creator/account capture requires intended_action=new_capture, decision=new_candidate, action_status=allowed, and can_start_new_capture=true.",
            )
        )
    return findings



def looks_like_creator_registry_preflight_artifact(relposix: str, text: str) -> bool:
    if not relposix.endswith(".md"):
        return False
    lower = text.lower()
    return all(marker in lower for marker in CREATOR_REGISTRY_PREFLIGHT_MARKERS)


def _safe_repo_relative_path(root: Path, raw_path: Any) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, "receipt_path must be a non-empty repo-relative path."
    cleaned = raw_path.strip().replace("\\", "/")
    if re.match(r"^[A-Za-z]:", cleaned) or cleaned.startswith("/"):
        return None, "receipt_path must be repo-relative, not absolute."
    candidate = Path(cleaned)
    if any(part == ".." for part in candidate.parts):
        return None, "receipt_path must not traverse outside the repo."
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        return None, "receipt_path must resolve inside the repo."
    return resolved, None


def _load_creator_registry_receipt(root: Path, raw_path: Any) -> tuple[dict[str, Any] | None, list[Finding]]:
    receipt_path, path_error = _safe_repo_relative_path(root, raw_path)
    if path_error:
        return None, [Finding("invalid_creator_registry_receipt_path", path_error)]
    assert receipt_path is not None
    if not receipt_path.is_file():
        return None, [Finding("missing_creator_registry_receipt_file", f"Creator Registry preflight receipt not found: {raw_path}.")]
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [Finding("invalid_creator_registry_receipt_json", f"Creator Registry preflight receipt {raw_path} is invalid JSON: {exc}.")]
    except OSError as exc:
        return None, [Finding("unreadable_creator_registry_receipt", f"Creator Registry preflight receipt {raw_path} could not be read: {exc}.")]

    receipt = data.get(CREATOR_REGISTRY_RECEIPT_ROOT) if isinstance(data, dict) else None
    if not isinstance(receipt, dict):
        return None, [Finding("invalid_creator_registry_receipt_root", f"Creator Registry preflight receipt {raw_path} must contain {CREATOR_REGISTRY_RECEIPT_ROOT}.")]
    findings: list[Finding] = []
    if receipt.get("schema_version") != CREATOR_REGISTRY_RECEIPT_SCHEMA:
        findings.append(
            Finding(
                "invalid_creator_registry_receipt_schema",
                f"Creator Registry preflight receipt {raw_path} must use schema_version={CREATOR_REGISTRY_RECEIPT_SCHEMA}.",
            )
        )
    results = receipt.get("results")
    if not isinstance(results, list):
        findings.append(Finding("invalid_creator_registry_receipt_results", f"Creator Registry preflight receipt {raw_path} results must be a list."))
    else:
        findings.extend(_validate_creator_registry_receipt_summary(raw_path, receipt, results))
    return receipt, findings


def _validate_creator_registry_receipt_summary(raw_path: Any, receipt: dict[str, Any], results: list[Any]) -> list[Finding]:
    summary = receipt.get("summary")
    if not isinstance(summary, dict):
        return [Finding("missing_creator_registry_receipt_summary", f"Creator Registry preflight receipt {raw_path} must contain a summary mapping.")]

    result_dicts = [result for result in results if isinstance(result, dict)]
    expected = {
        "total_candidates": len(result_dicts),
        "new_candidates": sum(1 for result in result_dicts if _normalize_vocab(result.get("decision")) == "new_candidate"),
        "existing_matches": sum(1 for result in result_dicts if _normalize_vocab(result.get("decision")) == "existing_match"),
        "ambiguous_matches": sum(1 for result in result_dicts if _normalize_vocab(result.get("decision")) == "ambiguous_match"),
        "invalid_candidates": sum(1 for result in result_dicts if _normalize_vocab(result.get("decision")) == "invalid_candidate"),
        "blocked_actions": sum(1 for result in result_dicts if _normalize_vocab(result.get("action_status")) == "blocked"),
        "safe_to_capture_new": sum(1 for result in result_dicts if _as_bool(result.get("can_start_new_capture")) is True),
    }
    findings: list[Finding] = []
    for field, expected_value in expected.items():
        actual = _as_int(summary.get(field))
        if actual != expected_value:
            findings.append(
                Finding(
                    "creator_registry_receipt_summary_mismatch",
                    f"Creator Registry preflight receipt {raw_path} summary.{field}={summary.get(field)!r} does not match results-derived {expected_value}.",
                )
            )
    return findings



def _validate_creator_registry_preflight_shapes(blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    for request in _records(blocks, "capture_request_id"):
        if "creator_registry_match_preflight" in request:
            findings.extend(_validate_creator_registry_match_preflight(request.get("capture_request_id", "<unknown>"), request))
    return findings


def _validate_creator_registry_receipt_rows(root: Path, blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    requests_by_receipt: dict[str, list[dict[str, Any]]] = {}
    for request in _records(blocks, "capture_request_id"):
        preflight = request.get("creator_registry_match_preflight")
        if not isinstance(preflight, dict):
            continue
        if _normalize_vocab(preflight.get("required_when")) != "new_social_creator_account_capture":
            continue
        raw_path = preflight.get("receipt_path")
        if not isinstance(raw_path, str) or _normalize_vocab(raw_path) in PLACEHOLDER_PREFLIGHT_RECEIPT_VALUES:
            continue
        requests_by_receipt.setdefault(raw_path, []).append(request)

    for raw_path, requests in requests_by_receipt.items():
        receipt, receipt_findings = _load_creator_registry_receipt(root, raw_path)
        findings.extend(receipt_findings)
        if receipt is None or not isinstance(receipt.get("results"), list):
            continue
        results_by_candidate: dict[str, dict[str, Any]] = {}
        for result in receipt["results"]:
            if not isinstance(result, dict):
                findings.append(Finding("invalid_creator_registry_receipt_result", f"Creator Registry preflight receipt {raw_path} contains a non-mapping result row."))
                continue
            candidate_id = result.get("candidate_id")
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                findings.append(Finding("invalid_creator_registry_receipt_result", f"Creator Registry preflight receipt {raw_path} contains a result without candidate_id."))
                continue
            results_by_candidate[candidate_id] = result

        for request in requests:
            request_id = request.get("capture_request_id", "<unknown>")
            preflight = request.get("creator_registry_match_preflight", {})
            candidate_ids = request.get("candidate_or_observation_ids")
            if not isinstance(candidate_ids, list) or not candidate_ids:
                findings.append(Finding("invalid_capture_request_candidate_ids", f"Capture request {request_id} candidate_or_observation_ids must be a non-empty list."))
                continue
            for candidate_id in candidate_ids:
                if not isinstance(candidate_id, str):
                    findings.append(Finding("invalid_capture_request_candidate_ids", f"Capture request {request_id} candidate_or_observation_ids must contain strings."))
                    continue
                result = results_by_candidate.get(candidate_id)
                if result is None:
                    findings.append(
                        Finding(
                            "missing_creator_registry_receipt_result",
                            f"Capture request {request_id} cites candidate {candidate_id}, but receipt {raw_path} has no matching result row.",
                        )
                    )
                    continue
                findings.extend(_compare_creator_registry_receipt_result(raw_path, request_id, candidate_id, preflight, result))
    return findings


def _compare_creator_registry_receipt_result(
    raw_path: Any,
    request_id: Any,
    candidate_id: str,
    preflight: dict[str, Any],
    result: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    for field in ("intended_action", "decision", "action_status"):
        declared = _normalize_vocab(preflight.get(field))
        observed = _normalize_vocab(result.get(field))
        if declared != observed:
            findings.append(
                Finding(
                    "creator_registry_receipt_field_mismatch",
                    f"Capture request {request_id} candidate {candidate_id} declares {field}={preflight.get(field)!r}, but receipt {raw_path} has {result.get(field)!r}.",
                )
            )
    declared_can_start = _as_bool(preflight.get("can_start_new_capture"))
    observed_can_start = _as_bool(result.get("can_start_new_capture"))
    if declared_can_start != observed_can_start:
        findings.append(
            Finding(
                "creator_registry_receipt_field_mismatch",
                f"Capture request {request_id} candidate {candidate_id} declares can_start_new_capture={preflight.get('can_start_new_capture')!r}, but receipt {raw_path} has {result.get('can_start_new_capture')!r}.",
            )
        )
    if _normalize_vocab(result.get("decision")) == "new_candidate" and result.get("matched_registry_profiles") not in ([], None):
        findings.append(
            Finding(
                "creator_registry_receipt_new_candidate_has_matches",
                f"Receipt {raw_path} candidate {candidate_id} is new_candidate but has matched_registry_profiles.",
            )
        )
    return findings


def _validate_capture_requests(blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    for request in _records(blocks, "capture_request_id"):
        request_id = request.get("capture_request_id", "<unknown>")
        missing = _required_missing(request, REQUIRED_CAPTURE_REQUEST_FIELDS)
        if missing:
            findings.append(Finding("missing_capture_request_fields", f"Capture request {request_id} is missing: {', '.join(missing)}."))

        if "creator_registry_match_preflight" in request:
            findings.extend(_validate_creator_registry_match_preflight(request_id, request))

        route_state = _normalize_vocab(request.get("route_binding_state"))
        if route_state not in VALID_ROUTE_BINDING_STATES:
            findings.append(
                Finding(
                    "invalid_capture_route_binding_state",
                    f"Capture request {request_id} route_binding_state must be one of {', '.join(sorted(VALID_ROUTE_BINDING_STATES))}.",
                )
            )

        urls = request.get("urls")
        if not isinstance(urls, list) or not urls:
            findings.append(Finding("invalid_capture_request_urls", f"Capture request {request_id} urls must be a non-empty list."))
        else:
            for index, entry in enumerate(urls, start=1):
                if not isinstance(entry, dict):
                    findings.append(
                        Finding("invalid_capture_request_urls", f"Capture request {request_id} url entry {index} must be a mapping.")
                    )
                    continue
                missing_url_fields = _required_missing(entry, REQUIRED_CAPTURE_URL_FIELDS)
                if missing_url_fields:
                    findings.append(
                        Finding(
                            "missing_capture_request_url_fields",
                            f"Capture request {request_id} url entry {index} is missing: {', '.join(missing_url_fields)}.",
                        )
                    )
                if "url" in entry and not _is_url(entry.get("url")):
                    findings.append(Finding("invalid_capture_request_url", f"Capture request {request_id} url entry {index} must be http(s)."))
                gate_role = _normalize_vocab(entry.get("gate_role"))
                if gate_role and gate_role not in VALID_GATE_ROLES:
                    findings.append(Finding("invalid_gate_role", f"Capture request {request_id} url entry {index} has invalid gate_role."))

        not_requested = request.get("not_requested")
        if isinstance(not_requested, list):
            normalized = {_normalize_vocab(item) for item in not_requested}
            missing_not_requested = sorted(REQUIRED_NOT_REQUESTED - normalized)
            if missing_not_requested:
                findings.append(
                    Finding(
                        "missing_capture_request_not_requested_boundaries",
                        f"Capture request {request_id} not_requested is missing: {', '.join(missing_not_requested)}.",
                    )
                )
        elif "not_requested" in request:
            findings.append(Finding("invalid_capture_request_not_requested", f"Capture request {request_id} not_requested must be a list."))
    return findings


def _validate_closeout(text: str, blocks: list[Any], intake: dict[str, Any] | None) -> list[Finding]:
    if not isinstance(intake, dict):
        return []
    findings: list[Finding] = []
    closeout = _normalize_vocab(intake.get("closeout_state"))
    candidate_observations = _records(blocks, "candidate_observation_id")
    capture_request_count = len(_records(blocks, "capture_request_id"))

    body = _section_body(text, SECTION_PATTERNS["closeout"])
    if closeout and closeout not in _normalize_vocab(body):
        findings.append(Finding("closeout_state_not_in_closeout_section", "Closeout section must repeat the intake closeout_state."))

    for decision in _mapping_values(blocks, "candidate_decision"):
        if isinstance(decision, dict) and "closeout_state" in decision:
            decision_closeout = _normalize_vocab(decision.get("closeout_state"))
            if closeout and decision_closeout != closeout:
                findings.append(Finding("candidate_decision_closeout_mismatch", "candidate_decision.closeout_state must match intake closeout_state."))

    if closeout == "candidate_ready_for_next_lane" and not candidate_observations:
        findings.append(
            Finding("candidate_ready_without_candidate_observation", "candidate_ready_for_next_lane requires a candidate_observation_id record.")
        )
    if closeout == "no_candidate_after_discovery" and candidate_observations:
        findings.append(Finding("no_candidate_with_candidate_observation", "no_candidate_after_discovery must not include candidate_observation_id records."))
    if closeout == "capture_preservation_only" and capture_request_count == 0:
        findings.append(Finding("preservation_without_capture_request", "capture_preservation_only requires at least one capture_request_id record."))
    if closeout == "capture_preservation_only" and candidate_observations:
        findings.append(Finding("preservation_with_candidate_observation", "capture_preservation_only must not include candidate_observation_id records."))
    return findings


def _iter_yaml_items(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, key, child
            yield from _iter_yaml_items(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, index, child
            yield from _iter_yaml_items(child, child_path)


def _validate_yaml_overclaims(blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    for block in blocks:
        for path, key, value in _iter_yaml_items(block):
            key_norm = _normalize_vocab(key)
            value_norm = _normalize_vocab(value)
            if key_norm in {"recency_status", "recency_attention", "signal_stage"} and value_norm in {
                "proof",
                "demand_proof",
                "gate_clearance",
                "candidate_authorization",
            }:
                findings.append(Finding("invalid_signal_stage_overclaim", f"{path} must not use {value!r}."))
    return findings


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _excerpt(value: str, limit: int = 120) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _is_nonclaim_context(text: str, start: int, end: int) -> bool:
    left_bounds = [text.rfind(boundary, 0, start) for boundary in (".", "\n", ";")]
    right_bounds = [idx for idx in (text.find(boundary, end) for boundary in (".", "\n", ";")) if idx != -1]
    left = max(left_bounds) + 1
    right = min(right_bounds) if right_bounds else min(len(text), end + 80)
    window = text[left:right]
    return NEGATED_OVERCLAIM_RE.search(window) is not None


def _validate_engagement_overclaims(text: str) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()
    for code, pattern in ENGAGEMENT_OVERCLAIM_PATTERNS.items():
        position = 0
        while True:
            match = pattern.search(text, position)
            if match is None:
                break
            position = match.start() + 1
            if _is_nonclaim_context(text, match.start(), match.end()):
                continue
            line = _line_number(text, match.start())
            excerpt = _excerpt(match.group(0))
            key = (code, line, excerpt)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    code,
                    "Forbidden engagement/resonance overclaim language "
                    f"near line {line}: {excerpt!r}. See {ENGAGEMENT_RULE_AUTHORITY}.",
                )
            )
    return findings

def _validate_forbidden_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for code, pattern in FORBIDDEN_TEXT_PATTERNS.items():
        for match in pattern.finditer(text):
            if _is_nonclaim_context(text, match.start(), match.end()):
                continue
            excerpt = " ".join(match.group(0).split())
            findings.append(Finding(code, f"Forbidden overclaim language found: {excerpt!r}."))
            break
    return findings


def validate_text(text: str) -> list[Finding]:
    blocks, yaml_findings = _yaml_blocks(text)
    findings = [*yaml_findings]
    intake = _find_intake(blocks)
    if intake is None:
        findings.append(
            Finding(
                "missing_scan_intake_receipt",
                "No YAML scan intake receipt with commission_id and source_context_status found.",
            )
        )
    version, version_findings = _receipt_version_findings(intake)
    findings.extend(version_findings)

    if version == CURRENT_SCAN_RECEIPT_VERSION and intake is not None:
        findings.extend(_validate_intake(intake))

        findings.extend(_validate_required_receipt_parts(text, intake))
        findings.extend(_validate_broad_scout_detail(text))
        findings.extend(_validate_csb_row_ids(text))
        findings.extend(_validate_count_consistency(text, blocks, intake))
        findings.extend(_validate_observations(blocks))
        findings.extend(_validate_candidate_observations(blocks))
        findings.extend(_validate_capture_requests(blocks))
        findings.extend(_validate_closeout(text, blocks, intake))

    # Legacy and current receipts both retain universal claim-safety checks.
    findings.extend(_validate_yaml_overclaims(blocks))
    findings.extend(_validate_engagement_overclaims(text))
    findings.extend(_validate_forbidden_text(text))
    return findings


# Kept local: returns None on git failure (callers distinguish infra gap from empty), unlike _hooklib.git_lines.
def _git_lines(root: Path, args: list[str]) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def changed_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for args in (
        ["diff", "--name-only", "--diff-filter=ACMR"],
        ["diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        lines = _git_lines(root, args)
        if lines:
            paths.extend(lines)
    return _dedupe(paths)


def resolve_base_ref(cli_base: str | None) -> str:
    ci_base = os.environ.get("FORSETI_DIFF_BASE", "").strip()
    if ci_base:
        return ci_base
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base:
        return f"origin/{github_base}"
    if cli_base:
        return cli_base
    return "origin/main"


def diff_paths(root: Path, base_ref: str) -> list[str] | None:
    lines = _git_lines(root, ["diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"])
    if lines is not None:
        return lines
    return _git_lines(root, ["diff", "--name-only", "--diff-filter=ACMR", base_ref, "HEAD"])


def looks_like_csb_first_scan_artifact(relposix: str, text: str) -> bool:
    if not relposix.endswith(".md"):
        return False
    if not any(relposix.startswith(prefix) for prefix in AUTO_SCAN_PREFIXES):
        return False
    lower = text.lower()
    route_marked = any(marker in lower for marker in AUTO_SCAN_ROUTE_MARKERS)
    current_shape_marked = all(marker in lower for marker in AUTO_SCAN_REQUIRED_MARKERS)
    explicit_version_marked = (
        f"{SCAN_RECEIPT_VERSION_FIELD}:" in lower and "commission_id:" in lower
    )
    return explicit_version_marked or (route_marked and current_shape_marked)


def _capture_handoff_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
    # A durable receipt declares its identity in the first YAML header. Limiting
    # identity to that header lets contracts and review artifacts quote receipt
    # examples in later fences without being mistaken for live Capture output.
    if not blocks or not isinstance(blocks[0], dict):
        return []
    first = blocks[0]
    if _normalize_vocab(first.get("artifact_kind")) not in CAPTURE_HANDOFF_ARTIFACT_KINDS:
        return []
    return [first]


def looks_like_capture_handoff_receipt(text: str) -> bool:
    # Raw marker detection in the first YAML header keeps malformed receipts in
    # the fail-loud path without treating later quoted examples as live output.
    first_fence = YAML_FENCE_RE.search(text)
    return first_fence is not None and CAPTURE_HANDOFF_KIND_RE.search(first_fence.group("body")) is not None


def _capture_state_fields(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for raw_key, field_value in value.items():
            key = _normalize_vocab(raw_key)
            if key == "status" or key.endswith("_status") or key.endswith("_state"):
                yield key, field_value
            yield from _capture_state_fields(field_value)
    elif isinstance(value, list):
        for item in value:
            yield from _capture_state_fields(item)


def _is_forbidden_capture_terminal_state(value: Any) -> bool:
    normalized = _normalize_vocab(value)
    return (
        normalized in FORBIDDEN_CAPTURE_TERMINAL_STATUSES
        or normalized.startswith("acquisition_complete")
        or normalized.startswith("collection_complete")
        or normalized.startswith("material_saturation_proven")
        or normalized.startswith("ready_for_consolidation")
        or normalized.startswith("sealed_ready_for_deliver")
        or normalized.endswith("_ready_for_consolidation")
    )


def _validate_capture_handoff_blocks(blocks: list[Any]) -> list[Finding]:
    findings: list[Finding] = []
    handoff_blocks = _capture_handoff_blocks(blocks)
    if not handoff_blocks:
        return findings

    owner_block = handoff_blocks[0]
    if _normalize_vocab(owner_block.get("artifact_kind")) == "collection_completion_receipt":
        findings.append(
            Finding(
                "capture_completion_artifact_kind_forbidden",
                "Capture owns bounded batch handoff, not collection or acquisition completion; use `capture_batch_handoff_receipt`.",
            )
        )

    seen_terminal_claims: set[tuple[str, str]] = set()
    for block in blocks:
        for key, value in _capture_state_fields(block):
            if not _is_forbidden_capture_terminal_state(value):
                continue
            claim = (key, _normalize_vocab(value))
            if claim in seen_terminal_claims:
                continue
            seen_terminal_claims.add(claim)
            findings.append(
                Finding(
                    "capture_handoff_claims_terminal_acquisition",
                    f"Capture handoff field {key!r}={value!r} claims a terminal state reserved to the validator-backed phase acquisition seal.",
                )
            )
    return findings


# Kept local: different contract from _hooklib.to_relposix (never None; falls back to backslash-normalized str).
def _relposix(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def auto_targets(root: Path, relpaths: Iterable[str]) -> list[Path]:
    targets: list[Path] = []
    for rel in _dedupe(relpaths):
        path = root / rel
        relposix = rel.replace("\\", "/")
        if not relposix.endswith(".md") or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        capture_targeted = any(
            relposix.startswith(prefix) for prefix in AUTO_SCAN_PREFIXES
        ) and looks_like_capture_handoff_receipt(text)
        if capture_targeted or looks_like_csb_first_scan_artifact(relposix, text) or (
            any(relposix.startswith(prefix) for prefix in AUTO_SCAN_PREFIXES)
            and looks_like_creator_registry_preflight_artifact(relposix, text)
        ):
            targets.append(path)
    return targets


def validate_artifact_path(root: Path, path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    relposix = _relposix(root, path)
    findings: list[Finding] = []
    capture_marked = looks_like_capture_handoff_receipt(text)
    scan_shaped = looks_like_csb_first_scan_artifact(relposix, text)
    preflight_shaped = looks_like_creator_registry_preflight_artifact(relposix, text)
    blocks: list[Any] = []
    if capture_marked or preflight_shaped:
        blocks, yaml_findings = _yaml_blocks(text)
        findings.extend(yaml_findings)
    if capture_marked:
        findings.extend(_validate_capture_handoff_blocks(blocks))
        # Leave the scan lane only for a document that actually parses as a
        # Capture-owned receipt and owes no other contract here. A raw marker in
        # prose or a non-YAML fence, and a marker added to an artifact that is
        # already scan- or preflight-shaped, must never suppress the checks that
        # artifact already owed.
        if (_capture_handoff_blocks(blocks) or findings) and not (scan_shaped or preflight_shaped):
            return findings
    if dispatched_receipt_version(text) == LEGACY_SCAN_RECEIPT_VERSION and relposix not in LEGACY_SCAN_RECEIPT_PATHS:
        findings.append(
            Finding(
                "legacy_scan_receipt_path_not_allowed",
                f"{SCAN_RECEIPT_VERSION_FIELD}: {LEGACY_SCAN_RECEIPT_VERSION} is frozen to the historical compatibility cohort; {relposix} is not allowed.",
            )
        )
    if scan_shaped:
        findings.extend(validate_text(text))
    elif not preflight_shaped:
        findings.extend(validate_text(text))

    if preflight_shaped:
        findings.extend(_validate_creator_registry_preflight_shapes(blocks))
        findings.extend(_validate_creator_registry_receipt_rows(root, blocks))
    return findings


def dispatched_receipt_version(text: str) -> int | None:
    """The receipt version validate_text dispatched on, or None if undetermined."""
    blocks, _ = _yaml_blocks(text)
    version, _ = _receipt_version_findings(_find_intake(blocks))
    return version


def _dispatch_note(path: Path) -> str:
    # A legacy receipt passes on claim-safety alone, so an undecorated PASS would
    # read as current-contract compliance it was never checked against.
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if dispatched_receipt_version(text) != LEGACY_SCAN_RECEIPT_VERSION:
        return ""
    return (
        f" [{SCAN_RECEIPT_VERSION_FIELD}: {LEGACY_SCAN_RECEIPT_VERSION} legacy dispatch"
        " -- claim-safety only; current-contract shape checks skipped]"
    )


def validate_paths(paths: Iterable[Path]) -> int:
    root = repo_root()
    exit_code = 0
    for path in paths:
        findings = validate_artifact_path(root, path)
        if findings:
            exit_code = 1
            print(f"FAIL {path}")
            for finding in findings:
                print(f"  {finding.code}: {finding.message}")
        else:
            print(f"PASS {path}{_dispatch_note(path)}")
    return exit_code


def _expected_from_fixture(path: Path) -> str:
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.search(r"fixture_expected:\s*(pass|fail)", first_line)
    if not match:
        return ""
    return match.group(1)


def selftest() -> int:
    root = Path(__file__).resolve().parents[2]
    fixture_dir = root / "forseti-harness" / "tests" / "fixtures" / "csb_scanning_artifacts"
    fixture_paths = sorted(fixture_dir.glob("*.md"))
    if not fixture_paths:
        print(f"SELFTEST FAILED: no fixtures found at {fixture_dir}")
        return 1

    ok = True
    for path in fixture_paths:
        expected = _expected_from_fixture(path)
        findings = validate_artifact_path(root, path)
        passed = not findings
        if expected == "pass" and passed:
            print(f"PASS {path.name}")
        elif expected == "fail" and not passed:
            print(f"PASS {path.name} expected fail: {', '.join(sorted({f.code for f in findings}))}")
        else:
            ok = False
            print(f"FAIL {path.name} expected={expected or '<missing>'} findings={findings}")
    legacy_rel = "docs/research/orca_discovery_candidate_scan_imaginary_authors_mgt_v0.md"
    if (root / legacy_rel).is_file():
        legacy_targets = auto_targets(root, [legacy_rel])
        legacy_findings = validate_artifact_path(root, root / legacy_rel)
        if legacy_targets and not legacy_findings:
            print("PASS explicit legacy receipt auto-targeted and validated by declared version")
        else:
            ok = False
            print(
                "FAIL explicit legacy receipt version dispatch: "
                f"targeted={bool(legacy_targets)} findings={legacy_findings}"
            )
    # Anchor on a receipt that actually declares the current version: targeting alone
    # is satisfied by any explicit version, including a legacy downgrade.
    current_rel = "docs/research/forseti_research_engine_p0_golden_thread_receipt_v0.md"
    if (root / current_rel).is_file():
        current_path = root / current_rel
        current_targeted = bool(auto_targets(root, [current_rel]))
        current_version = dispatched_receipt_version(current_path.read_text(encoding="utf-8"))
        current_findings = validate_artifact_path(root, current_path)
        if current_targeted and current_version == CURRENT_SCAN_RECEIPT_VERSION and not current_findings:
            print("PASS current-contract receipt auto-targeted and validated at the current version")
        else:
            ok = False
            print(
                "FAIL current-contract receipt dispatch: "
                f"targeted={current_targeted} version={current_version} findings={current_findings}"
            )

    capture_cases = {
        "batch handoff remains non-terminal": (
            """```yaml
artifact_kind: capture_batch_handoff_receipt
status: CAPTURE_BATCH_COMPLETE_MATERIAL_SATURATION_NOT_PROVEN
```""",
            set(),
        ),
        "legacy completion receipt is rejected": (
            """```yaml
artifact_kind: collection_completion_receipt
status: COLLECTION_COMPLETE_READY_FOR_CONSOLIDATION
```""",
            {
                "capture_completion_artifact_kind_forbidden",
                "capture_handoff_claims_terminal_acquisition",
            },
        ),
        "phase acquisition seal keeps terminal authority": (
            """```yaml
artifact_kind: phase_acquisition_seal
seal_state: SEALED_READY_FOR_DELIVER
```""",
            set(),
        ),
        "Capture seal_state cannot claim terminal authority": (
            """```yaml
artifact_kind: capture_batch_handoff_receipt
seal_state: SEALED_READY_FOR_DELIVER
```""",
            {"capture_handoff_claims_terminal_acquisition"},
        ),
        "Capture handoff_state cannot claim acquisition complete": (
            """```yaml
artifact_kind: capture_batch_handoff_receipt
handoff_state: ACQUISITION_COMPLETE
```""",
            {"capture_handoff_claims_terminal_acquisition"},
        ),
        "terminal claim in a sibling YAML block is rejected": (
            """```yaml
artifact_kind: capture_batch_handoff_receipt
status: CAPTURE_BATCH_COMPLETE_MATERIAL_SATURATION_NOT_PROVEN
```
```yaml
handoff_state: ACQUISITION_COMPLETE
```""",
            {"capture_handoff_claims_terminal_acquisition"},
        ),
        "later quoted Capture example is not a live receipt": (
            """```yaml
artifact_kind: delegated_review_output
status: REVIEW_COMPLETE
```
```yaml
artifact_kind: collection_completion_receipt
status: COLLECTION_COMPLETE_READY_FOR_CONSOLIDATION
```""",
            set(),
        ),
    }
    for name, (text, expected_codes) in capture_cases.items():
        blocks, yaml_findings = _yaml_blocks(text)
        codes = {finding.code for finding in [*yaml_findings, *_validate_capture_handoff_blocks(blocks)]}
        if codes == expected_codes:
            print(f"PASS {name}")
        else:
            ok = False
            print(f"FAIL {name}: expected={sorted(expected_codes)} actual={sorted(codes)}")

    malformed_capture = """```yaml
artifact_kind: capture_batch_handoff_receipt
status: [
```"""
    malformed_blocks, malformed_yaml_findings = _yaml_blocks(malformed_capture)
    malformed_codes = {
        finding.code
        for finding in [
            *malformed_yaml_findings,
            *_validate_capture_handoff_blocks(malformed_blocks),
        ]
    }
    if looks_like_capture_handoff_receipt(malformed_capture) and "invalid_yaml_fence" in malformed_codes:
        print("PASS malformed Capture handoff remains auto-targeted and fails loud")
    else:
        ok = False
        print(
            "FAIL malformed Capture handoff targeting: "
            f"targeted={looks_like_capture_handoff_receipt(malformed_capture)} "
            f"codes={sorted(malformed_codes)}"
        )

    # A Capture kind marker must divert an artifact out of the scan lane only when
    # the document really is a Capture receipt; it must never erase checks the
    # artifact already owed.
    scan_source = fixture_dir / "bad_engagement_overclaim.md"
    if scan_source.is_file():
        scan_text = scan_source.read_text(encoding="utf-8")
        owed_codes = {finding.code for finding in validate_text(scan_text)}
        lane_cases = {
            "capture kind inside a scan artifact does not erase scan findings": scan_text.replace(
                "```yaml", "```yaml\nartifact_kind: capture_batch_handoff_receipt", 1
            ),
            "capture marker in a non-YAML fence does not erase scan findings": (
                scan_text + "\n```text\nartifact_kind: capture_batch_handoff_receipt\n```\n"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            research_dir = tmp_root / "docs" / "research"
            research_dir.mkdir(parents=True)
            for index, (name, probe_text) in enumerate(lane_cases.items()):
                probe_path = research_dir / f"capture_lane_probe_{index}_v0.md"
                probe_path.write_text(probe_text, encoding="utf-8")
                probe_codes = {finding.code for finding in validate_artifact_path(tmp_root, probe_path)}
                if owed_codes and owed_codes <= probe_codes:
                    print(f"PASS {name}")
                else:
                    ok = False
                    print(f"FAIL {name}: owed={sorted(owed_codes)} actual={sorted(probe_codes)}")

            receipt_path = research_dir / "capture_batch_probe_v0.md"
            receipt_path.write_text(
                "```yaml\n"
                "artifact_kind: capture_batch_handoff_receipt\n"
                "status: CAPTURE_BATCH_COMPLETE_MATERIAL_SATURATION_NOT_PROVEN\n"
                "```\n",
                encoding="utf-8",
            )
            receipt_findings = validate_artifact_path(tmp_root, receipt_path)
            if not receipt_findings:
                print("PASS genuine Capture receipt still leaves the scan lane cleanly")
            else:
                ok = False
                print(
                    "FAIL genuine Capture receipt lane exit: "
                    f"findings={sorted({f.code for f in receipt_findings})}"
                )

            review_dir = tmp_root / "docs" / "review-outputs"
            review_dir.mkdir(parents=True)
            quoted_example_path = review_dir / "quoted_capture_example_v0.md"
            quoted_example_path.write_text(
                "```yaml\n"
                "artifact_kind: collection_completion_receipt\n"
                "status: COLLECTION_COMPLETE_READY_FOR_CONSOLIDATION\n"
                "```\n",
                encoding="utf-8",
            )
            if not auto_targets(tmp_root, ["docs/review-outputs/quoted_capture_example_v0.md"]):
                print("PASS Capture example outside the research-artifact lane is not auto-targeted")
            else:
                ok = False
                print("FAIL quoted Capture example outside research was auto-targeted")

    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate CSB-first scan receipt shape, Capture handoff boundaries, and Creator Registry preflight receipt content."
    )
    parser.add_argument("paths", nargs="*", help="explicit scan artifact paths")
    parser.add_argument("--changed", action="store_true", help="auto-check changed Capture handoffs and docs/research scan artifacts with CSB-first or Creator Registry preflight markers")
    parser.add_argument("--diff", metavar="BASE", help="auto-check Capture handoffs and docs/research scan artifacts with CSB-first or Creator Registry preflight markers changed in BASE...HEAD")
    parser.add_argument("--strict", action="store_true", help="accepted for CI readability; findings already exit 1")
    parser.add_argument("--selftest", action="store_true", help="run fixture selftest")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    root = repo_root()
    explicit_paths = [Path(path) for path in args.paths]
    auto_relpaths: list[str] = []

    if args.changed:
        auto_relpaths.extend(changed_paths(root))
    if args.diff:
        base = resolve_base_ref(args.diff)
        diff_relpaths = diff_paths(root, base)
        if diff_relpaths is None:
            print(
                f"check_csb_scanning_artifact: diff-scoping unavailable for {base}; failing open.",
                file=sys.stderr,
            )
            diff_relpaths = []
        auto_relpaths.extend(diff_relpaths)

    paths = explicit_paths + auto_targets(root, auto_relpaths)
    paths = [Path(path) for path in _dedupe(str(path) for path in paths)]

    if not paths:
        if args.changed or args.diff:
            print("check_csb_scanning_artifact: no changed Capture handoff, CSB-first, or Creator Registry preflight artifacts detected")
            return 0
        print(
            "usage: check_csb_scanning_artifact.py [--selftest] [--changed] [--diff BASE] <scan-artifact> [...]",
            file=sys.stderr,
        )
        return 2

    return validate_paths(paths)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
