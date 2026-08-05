#!/usr/bin/env python3
"""Validate Commission Signal Board classifier handoff rows.

This is a local/manual checker. It does not run retrieval, classify demand,
construct graphs, or prove a board is correct. It only checks that saved full
board outputs preserve the prompt's mechanical shape, that rows listed in the
classifier handoff are evidence-backed and cutoff-safe according to the board's
own row table, that Section 4 carries the mechanically required
recency/current-state attention fields, and that the output does not turn
engagement/resonance language into a mechanical proof or authority shortcut.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
import sys
from typing import Any

import yaml

ROW_SECTION_RE = re.compile(
    r"^###\s+4\.\s+Signal Board Rows\s*$"
    r"(?P<body>.*?)"
    r"(?=^###\s+\d+\.|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
HANDOFF_SECTION_RE = re.compile(
    r"^###\s+8\.\s+Demand-Classifier Handoff Packet\s*$"
    r"(?P<body>.*?)"
    r"(?=^###\s+\d+\.|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
BOARD_STATUS_SECTION_RE = re.compile(
    r"^###\s+10\.\s+Board Status And Run Boundary\s*$"
    r"(?P<body>.*?)"
    r"(?=^###\s+\d+\.|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
YAML_FENCE_RE = re.compile(r"```yaml\s*(?P<body>.*?)\s*```", re.IGNORECASE | re.DOTALL)

EXPECTED_SECTIONS = [
    "Commission Intake Receipt",
    "Boundary Statement",
    "Source-Family Coverage Plan",
    "Signal Board Rows",
    "Mandatory Counterevidence Paths",
    "Campaign And Duplication Risk",
    "Graph Retrieval Brief",
    "Demand-Classifier Handoff Packet",
    "Visible Limitations",
    "Board Status And Run Boundary",
]
EXPECTED_COMPANY_SECTIONS = [
    "Company Commission And Identity Receipt",
    "Decision-Neutral Boundary",
    "Source-Family And Venue Coverage Ledger",
    "Observation Ledger",
    "Portfolio And Retail Architecture",
    "Strategic And Operating Chronology",
    "Customer And Community Response",
    "Competitor Context, Contradictions, And Gaps",
    "Company Surface Candidate Ledger",
    "Completion Ledger And Run Boundary",
]
REQUIRED_PORTFOLIO_RETAIL_SUBSECTIONS = [
    "Owned Portfolio Denominator",
    "Product, Claim, And Price Architecture",
    "Qualified Retailer Corpus",
    "Evidence-Selected Product Depth",
    "Outside-In Portfolio Interpretation",
    "Strategic Positioning, Markets, And Channels",
]
REQUIRED_ROW_COLUMNS = {
    "row_id",
    "source_family",
    "signal_role",
    "row_purpose",
    "recency_status",
    "recency_attention",
    "graph_role",
    "graph_weight_hint",
    "evidence_status",
    "surface_cutoff_status",
    "cutoff_status",
}
VALID_HANDOFF_MODES = {"backtest", "forward"}
VALID_SOURCE_FAMILIES = {
    "ad_transparency",
    "forums_community",
    "reviews",
    "creator_social_video",
    "retail_pdp",
    "search_discovery",
    "aeo_answer_engines",
    "news_editorial_trade",
    "professional_org_motion",
    "owned_channels",
    "other",
}
VALID_SIGNAL_ROLES = {
    "consumer_language",
    "review_experience",
    "creator_attention",
    "retail_corroboration",
    "search_interest",
    "aeo_visibility",
    "org_motion",
    "owned_claim",
    "none",
}
VALID_ROW_PURPOSES = {
    "chronology",
    "source_route",
    "signal_unit",
    "contradiction",
    "gap",
    "classifier_handoff",
    "recency_priority",
}
VALID_RECENCY_STATUSES = {
    "current_state",
    "recent",
    "older_context",
    "stale_or_unknown",
    "not_applicable",
}
VALID_RECENCY_ATTENTIONS = {"high", "normal", "low", "unknown"}
VALID_GRAPH_ROLES = {
    "seed",
    "node_candidate",
    "edge_candidate",
    "propagation_path",
    "campaign_overlap_check",
    "counterevidence_path",
    "none",
}
VALID_GRAPH_WEIGHT_HINTS = {"high", "medium", "low", "none"}
ENGAGEMENT_RULE_AUTHORITY = (
    "forseti/product/spines/commission_signal_board/authority/"
    "forseti_commission_signal_board_prompt_structure_rules_v0.md"
)
ENGAGEMENT_SIGNAL_RE = (
    r"(?:engagement(?:\s+counts?)?|public[- ]reaction|reaction\s+volume|"
    r"high[- ]engagement|low[- ]engagement|upvotes?|helpful\s+votes?|likes?|"
    r"views?|shares?|comments?|reply\s+counts?|source[- ]native\s+scores?|"
    r"source\s+rank|source\s+order|resonance)"
)
ENGAGEMENT_CLAIM_GAP = r"[^.\n;]{0,80}"
NEGATED_OVERCLAIM_RE = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|must\s+not|does\s+not|do\s+not|"
    r"don't|is\s+not|are\s+not|not\s+enough\s+to)\b",
    re.IGNORECASE,
)
FORBIDDEN_ENGAGEMENT_OVERCLAIMS = {
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
    "engagement_graph_weight_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:sets?|determines|drives|raises|"
        rf"increases|justifies|supports?|becomes|is|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:graph[_ -]?weight"
        rf"(?:[_ -]?hint)?|graph\s+score|graph\s+strength)\b|"
        rf"\b(?:graph[_ -]?weight(?:[_ -]?hint)?|graph\s+score|graph\s+strength)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|becomes|sets?|determined|driven|raised|increased|justified|supported|"
        rf"because\s+of|due\s+to|from|by|based\s+on)\b{ENGAGEMENT_CLAIM_GAP}\b{ENGAGEMENT_SIGNAL_RE}\b)",
        re.IGNORECASE,
    ),
    "engagement_commit_scale_shortcut": re.compile(
        rf"(?:\b{ENGAGEMENT_SIGNAL_RE}\b{ENGAGEMENT_CLAIM_GAP}\b(?:clears?|supports?|justifies?|passes?|"
        rf"unlocks?|establishes|means|counts\s+as)\b{ENGAGEMENT_CLAIM_GAP}\b(?:Commit/Scale|Commit|Scale|buyer\s+proof|"
        rf"demand\s+gate)\b|"
        rf"\b(?:Commit/Scale|Commit|Scale|buyer\s+proof|demand\s+gate)\b"
        rf"{ENGAGEMENT_CLAIM_GAP}\b(?:is|was|cleared|supported|justified|passed|unlocked|established|"
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
VALID_EVIDENCE_STATUSES = {
    "provided",
    "source_backed",
    "to_retrieve",
    "gap",
    "not_authorized",
    "not_applicable",
    "excluded_future_info",
}
VALID_CUTOFF_STATUSES = {"in_window", "post_cutoff_excluded", "uncertain", "not_applicable"}
VALID_SURFACE_CUTOFF_STATUSES = {"existed_by_cutoff", "post_cutoff_surface", "uncertain", "not_applicable"}
VALID_BOARD_STATUSES = {
    "READY_FOR_RETRIEVAL_HANDOFF",
    "COLLECTION_BOARD_ONLY",
    "NEEDS_COMMISSION_INTAKE",
    "NEEDS_CUTOFF_DATE",
    "NEEDS_OWNER_DECISION",
}
VALID_RUN_BOUNDARIES = {"CHAT_ONLY_BOARD_COMPLETE", "INTAKE_ONLY", "OWNER_DECISION_NEEDED"}
REQUIRED_HANDOFF_PACKET_FIELDS = {
    "candidate_or_subject",
    "decision_context",
    "mode",
    "cutoff_date",
    "signal_rows_for_handoff",
    "counterevidence_rows_for_handoff",
    "source_family_gaps",
    "provenance_gaps",
    "cutoff_uncertainties",
    "classifier_mapping_status",
    "prohibited_claims",
}
ROW_ID_RE = re.compile(r"^SBR-(\d{3})$")
COMPANY_REPORT_MARKER_RE = re.compile(
    r"^###\s+1\.\s+Company Commission And Identity Receipt\s*$",
    re.IGNORECASE | re.MULTILINE,
)
COMPANY_SUBJECT_KINDS = {"brand", "org", "brand_or_org_unresolved"}
COMPANY_IDENTITY_STATES = {"resolved", "provisional", "ambiguous", "unresolved"}
COMPANY_TIME_POSTURES = {"recency_first", "longitudinal"}
COMPANY_RECENCY_TIERS = {
    "days_0_30",
    "days_31_90",
    "days_91_180",
    "days_over_180",
    "undated_unknown",
}
COMPANY_EFFECTIVE_TIME_PRECISIONS = {"day", "current_page_observation", "undated"}
COMPANY_AGE_ANCHOR_BASES = {
    "event_effective",
    "publication",
    "current_page_observation",
    "unknown",
}
COMPANY_RUN_BOUNDARIES = {
    "COMPANY_REPORT_COMPLETE_NO_DOWNSTREAM_EXECUTION",
    "COMMISSION_SEALED_PRE_SCAN",
    "INTAKE_ONLY",
    "OWNER_DECISION_NEEDED",
}
COMMISSION_STAGE_RUN_BOUNDARY = "COMMISSION_SEALED_PRE_SCAN"
COMMISSION_STAGE_SCOUT_STATUS = "commissioned_not_yet_run"
BROAD_COMPANY_UNDERSTANDING_PROFILE = "broad_company_understanding_v1"
BROAD_CONSUMER_UNDERSTANDING_PROFILE = "broad_consumer_brand_understanding_v3"
LEGACY_CONSUMER_UNDERSTANDING_PROFILES = {
    "broad_consumer_brand_understanding_v1",
    "broad_consumer_brand_understanding_v2",
}
UNDERSTANDING_COMPLETION_PROFILES = {
    BROAD_COMPANY_UNDERSTANDING_PROFILE,
    BROAD_CONSUMER_UNDERSTANDING_PROFILE,
}
# The CSB records the current selector. The acquisition-seal validator owns the
# hash-pinned depth ledger and enforces this selector/schema coupling in full.
UNDERSTANDING_PROFILE_DEPTH_CONTRACT = {
    BROAD_COMPANY_UNDERSTANDING_PROFILE: "understanding_evidence_depth_v1",
    BROAD_CONSUMER_UNDERSTANDING_PROFILE: "understanding_evidence_depth_v4",
}
NOT_REQUIRED_SCOUT_STATUS = "not_required_no_decision_material_job"
COMPANY_REDDIT_SCOUT_STATUSES = {
    "checked_positive_yield",
    "checked_zero_yield",
    "blocked_with_typed_gap",
    NOT_REQUIRED_SCOUT_STATUS,
    COMMISSION_STAGE_SCOUT_STATUS,
}
COMPANY_QUORA_SCOUT_STATUSES = {
    "experimental_checked_positive_yield",
    "experimental_checked_zero_yield",
    "blocked_with_typed_gap",
    NOT_REQUIRED_SCOUT_STATUS,
    COMMISSION_STAGE_SCOUT_STATUS,
}
COMPANY_SCOUT_STATUS_COVERAGE_STATES = {
    "checked_positive_yield": ("checked", "evidence_found"),
    "experimental_checked_positive_yield": ("checked", "evidence_found"),
    "checked_zero_yield": ("checked", "zero_yield"),
    "experimental_checked_zero_yield": ("checked", "zero_yield"),
    "blocked_with_typed_gap": ("blocked", "blocked"),
    COMMISSION_STAGE_SCOUT_STATUS: ("not_checked", "unknown"),
}
COMPANY_SOURCE_CLASSES = {
    "official_first_party",
    "official_regulatory",
    "independent",
    "retailer",
    "customer_community",
    "creator_social",
    "unknown",
}
COMPANY_FACT_DOMAINS = {
    "company_fact",
    "external_customer_evidence",
    "competitor_context",
    "contradiction",
    "unknown",
}
COMPANY_COVERAGE_STATUSES = {"checked", "blocked", "not_applicable", "not_checked"}
COMPANY_COVERAGE_REQUIREMENTS = {
    "required",
    "mandatory_bounded_scout",
    "experimental_initial_proving_run",
    "category_aware",
    "conditional",
}
COMPANY_LENS_KEYS = {
    "portfolio_and_retail_architecture",
    "positioning",
    "offerings_and_claims",
    "markets_and_channels",
    "strategic_and_operating_moves",
    "customer_and_community_response",
    "competitor_and_substitute_context",
    "contradictions",
    "evidence_gaps",
}
COMPANY_REQUIRED_OBSERVATION_FIELDS = {
    "observation_id",
    "subject_name",
    "subject_kind",
    "identity_state",
    "coverage_id",
    "source_url_or_packet_locator",
    "source_family",
    "source_surface",
    "publisher_or_venue",
    "source_class",
    "publication_date",
    "event_or_effective_date",
    "observation_at",
    "effective_time_precision",
    "recency_tier",
    "age_anchor_date",
    "age_anchor_basis",
    "exact_locator",
    "evidence_excerpt",
    "lawful_access_route",
    "access_limitation",
    "independence_syndication_group",
    "independent_corroboration_ids",
    "ambiguity_limitation",
    "contradiction_state",
    "fact_domain",
    "current_state_use",
    "consumed_by_sections",
}
COMPANY_PROHIBITED_GTM_KEYS = {
    "pain",
    "buyer",
    "icp",
    "priority",
    "urgency",
    "willingness_to_pay",
    "wtp",
    "outreach",
    "offer",
    "wedge",
}
COMPANY_PROHIBITED_CAP_KEYS = {
    "max_pages",
    "max_sources",
    "max_observations",
    "page_limit",
    "source_limit",
    "observation_limit",
    "report_length_limit",
}
RETAILER_REVIEW_APPROVAL_CORPUS_BASES = {
    "complete_visible_corpus",
    "reproducible_bounded_sample",
}
RETAILER_REVIEW_APPROVAL_REQUIRED_FIELDS = {
    "corpus_basis",
    "source_visible_total",
    "captured_total",
    "sample_selection",
    "incentive_disclosure_basis",
    "excluded_explicit_incentivized",
    "excluded_unknown_or_conflicting",
    "excluded_other",
    "excluded_other_reason",
    "eligible_explicit_non_incentivized",
    "eligible_not_marked_incentivized",
    "eligible_total",
    "eligible_positive_4_5",
    "eligible_below_positive_1_3",
    "approval_rate_pct",
    "below_positive_rate_pct",
}
RETAILER_REVIEW_APPROVAL_COUNT_FIELDS = {
    "captured_total",
    "excluded_explicit_incentivized",
    "excluded_unknown_or_conflicting",
    "excluded_other",
    "eligible_explicit_non_incentivized",
    "eligible_not_marked_incentivized",
    "eligible_total",
    "eligible_positive_4_5",
    "eligible_below_positive_1_3",
}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    row_id: str = ""


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _normalize_vocab(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


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
    for code, pattern in FORBIDDEN_ENGAGEMENT_OVERCLAIMS.items():
        for match in pattern.finditer(text):
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


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _extract_section(
    pattern: re.Pattern[str], text: str, missing_code: str, missing_message: str
) -> tuple[str, list[Finding]]:
    match = pattern.search(text)
    if not match:
        return "", [Finding(missing_code, missing_message)]
    return match.group("body"), []


def validate_section_contract(text: str) -> list[Finding]:
    headings = [
        (int(match.group("number")), _normalize_header(match.group("title")))
        for match in re.finditer(r"^###\s+(?P<number>\d+)\.\s+(?P<title>.+?)\s*$", text, re.MULTILINE)
    ]
    expected = [(index, _normalize_header(title)) for index, title in enumerate(EXPECTED_SECTIONS, start=1)]
    if headings == expected:
        return []
    return [
        Finding(
            "invalid_section_contract",
            "Full board output must contain Sections 1-10 in the prompt-defined order.",
        )
    ]


def _finding_for_invalid_vocab(row_id: str, field: str, value: str, valid_values: set[str]) -> Finding | None:
    normalized = _normalize_vocab(value)
    if normalized in valid_values:
        return None
    return Finding(
        f"invalid_{field}",
        f"{field} must be one of {', '.join(sorted(valid_values))}; got {value or '<blank>'}.",
        row_id,
    )


def parse_signal_rows(text: str) -> tuple[dict[str, dict[str, str]], list[Finding]]:
    section, findings = _extract_section(
        ROW_SECTION_RE,
        text,
        "missing_signal_board_rows",
        "Missing Section 4 Signal Board Rows.",
    )
    if findings:
        return {}, findings

    table_lines = [line for line in section.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return {}, [Finding("missing_signal_board_rows_table", "Section 4 has no Markdown table.")]

    headers = [_normalize_header(cell) for cell in _split_table_row(table_lines[0])]
    missing = sorted(REQUIRED_ROW_COLUMNS - set(headers))
    if missing:
        return {}, [
            Finding(
                "missing_required_row_columns",
                "Section 4 table is missing required columns: " + ", ".join(missing),
            )
        ]

    rows: dict[str, dict[str, str]] = {}
    out_findings: list[Finding] = []
    for table_index, line in enumerate(table_lines[1:], start=2):
        cells = _split_table_row(line)
        if _is_separator_row(cells):
            continue
        if len(cells) != len(headers):
            first_cell = cells[0] if cells else ""
            out_findings.append(
                Finding(
                    "malformed_signal_board_row",
                    "Row has a different cell count than the header "
                    f"(table row {table_index}, first cell {first_cell or '<blank>'}).",
                )
            )
            continue
        row = dict(zip(headers, cells, strict=True))
        row_id = row.get("row_id", "")
        if not row_id:
            out_findings.append(Finding("missing_row_id", "Signal board row is missing Row ID."))
            continue
        if not ROW_ID_RE.fullmatch(row_id):
            out_findings.append(Finding("invalid_row_id_format", "Row ID must use SBR-001 format.", row_id))
            continue
        expected_row_id = f"SBR-{len(rows) + 1:03d}"
        if row_id != expected_row_id:
            out_findings.append(
                Finding("non_monotonic_row_id", f"Expected next row ID {expected_row_id}, got {row_id}.", row_id)
            )
        if row_id in rows:
            out_findings.append(Finding("duplicate_row_id", f"Duplicate signal board row ID {row_id}.", row_id))
            continue
        rows[row_id] = row

        vocab_checks = {
            "source_family": VALID_SOURCE_FAMILIES,
            "signal_role": VALID_SIGNAL_ROLES,
            "row_purpose": VALID_ROW_PURPOSES,
            "recency_status": VALID_RECENCY_STATUSES,
            "recency_attention": VALID_RECENCY_ATTENTIONS,
            "graph_role": VALID_GRAPH_ROLES,
            "graph_weight_hint": VALID_GRAPH_WEIGHT_HINTS,
            "evidence_status": VALID_EVIDENCE_STATUSES,
            "surface_cutoff_status": VALID_SURFACE_CUTOFF_STATUSES,
            "cutoff_status": VALID_CUTOFF_STATUSES,
        }
        for field, valid_values in vocab_checks.items():
            finding = _finding_for_invalid_vocab(row_id, field, row.get(field, ""), valid_values)
            if finding:
                out_findings.append(finding)
    return rows, out_findings


def parse_classifier_handoff(text: str) -> tuple[dict[str, Any], list[Finding]]:
    section, findings = _extract_section(
        HANDOFF_SECTION_RE,
        text,
        "missing_classifier_handoff_section",
        "Missing Section 8 Demand-Classifier Handoff Packet.",
    )
    if findings:
        return {}, findings

    fence = YAML_FENCE_RE.search(section)
    if not fence:
        return {}, [Finding("missing_classifier_handoff_yaml", "Section 8 has no yaml fence.")]

    try:
        data = yaml.safe_load(fence.group("body")) or {}
    except yaml.YAMLError as exc:
        return {}, [Finding("invalid_classifier_handoff_yaml", f"Section 8 YAML is invalid: {exc}")]

    packet = data.get("classifier_handoff_packet") if isinstance(data, dict) else None
    if not isinstance(packet, dict):
        return {}, [Finding("missing_classifier_handoff_packet", "Section 8 YAML lacks classifier_handoff_packet.")]
    return packet, []


def parse_board_status(text: str) -> tuple[dict[str, Any], list[Finding]]:
    section, findings = _extract_section(
        BOARD_STATUS_SECTION_RE,
        text,
        "missing_board_status_section",
        "Missing Section 10 Board Status And Run Boundary.",
    )
    if findings:
        return {}, findings

    fence = YAML_FENCE_RE.search(section)
    if not fence:
        return {}, [Finding("missing_board_status_yaml", "Section 10 has no yaml fence.")]

    try:
        data = yaml.safe_load(fence.group("body")) or {}
    except yaml.YAMLError as exc:
        return {}, [Finding("invalid_board_status_yaml", f"Section 10 YAML is invalid: {exc}")]

    if not isinstance(data, dict):
        return {}, [Finding("invalid_board_status_yaml", "Section 10 YAML must be a mapping.")]
    return data, []


def _handoff_ids(packet: dict[str, Any], key: str) -> tuple[list[str], list[Finding]]:
    value = packet.get(key)
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [Finding("handoff_rows_not_list", f"{key} must be a list.")]
    ids: list[str] = []
    findings: list[Finding] = []
    for item in value:
        if not isinstance(item, str):
            findings.append(Finding("handoff_row_id_not_string", f"{key} contains a non-string row ID."))
            continue
        ids.append(item)
    return ids, findings


def _validate_handoff_row(row_id: str, row: dict[str, str], mode: str) -> list[Finding]:
    findings: list[Finding] = []
    evidence_status_raw = row.get("evidence_status", "")
    evidence_status = _normalize_vocab(evidence_status_raw)
    cutoff_status = _normalize_vocab(row.get("cutoff_status", ""))
    surface_cutoff_status = _normalize_vocab(row.get("surface_cutoff_status", ""))
    source_family = _normalize_vocab(row.get("source_family", ""))
    signal_role = _normalize_vocab(row.get("signal_role", ""))

    if source_family == "aeo_answer_engines" or signal_role == "aeo_visibility":
        findings.append(
            Finding(
                "handoff_row_aeo_visibility",
                "AEO / answer-engine rows are visibility annotations and must not enter classifier handoff.",
                row_id,
            )
        )

    if evidence_status == "excluded_future_info":
        findings.append(
            Finding("handoff_row_future_info", "excluded_future_info rows must not enter classifier handoff.", row_id)
        )
    elif evidence_status != "source_backed":
        findings.append(
            Finding(
                "handoff_row_not_source_backed",
                f"Classifier handoff row must be source_backed, got {evidence_status_raw or '<blank>'}.",
                row_id,
            )
        )

    if mode == "backtest":
        if surface_cutoff_status != "existed_by_cutoff":
            findings.append(
                Finding(
                    "handoff_row_surface_cutoff_invalid",
                    "Backtest handoff row must have surface_cutoff_status: existed_by_cutoff.",
                    row_id,
                )
            )
        if cutoff_status != "in_window":
            findings.append(
                Finding(
                    "handoff_row_cutoff_invalid",
                    "Backtest handoff row must have cutoff_status: in_window.",
                    row_id,
                )
            )

    return findings


def _validate_packet_shape(packet: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    missing_handoff_fields = sorted(REQUIRED_HANDOFF_PACKET_FIELDS - set(packet))
    if missing_handoff_fields:
        findings.append(
            Finding(
                "missing_handoff_packet_fields",
                "classifier_handoff_packet is missing required fields: " + ", ".join(missing_handoff_fields),
            )
        )

    mapping_status = _normalize_vocab(packet.get("classifier_mapping_status"))
    if mapping_status != "classifier_owned":
        findings.append(
            Finding(
                "invalid_classifier_mapping_status",
                "classifier_handoff_packet.classifier_mapping_status must be classifier_owned.",
            )
        )

    prohibited_claims = packet.get("prohibited_claims")
    if not isinstance(prohibited_claims, list) or not all(isinstance(item, str) for item in prohibited_claims):
        findings.append(
            Finding("invalid_prohibited_claims", "classifier_handoff_packet.prohibited_claims must be a list of strings.")
        )
    return findings


def _validate_board_status_shape(status_packet: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    board_status = str(status_packet.get("board_status", "")).strip()
    if board_status not in VALID_BOARD_STATUSES:
        findings.append(
            Finding(
                "invalid_board_status",
                "board_status must be one of " + ", ".join(sorted(VALID_BOARD_STATUSES)) + ".",
            )
        )
    run_boundary = str(status_packet.get("run_boundary", "")).strip()
    if run_boundary not in VALID_RUN_BOUNDARIES:
        findings.append(
            Finding(
                "invalid_run_boundary",
                "run_boundary must be one of " + ", ".join(sorted(VALID_RUN_BOUNDARIES)) + ".",
            )
        )
    if "next_authorized_step" not in status_packet:
        findings.append(Finding("missing_next_authorized_step", "Section 10 must include next_authorized_step."))
    return findings


def _parse_date(value: Any) -> date | None:
    if value in (None, "", "unknown", "not_applicable"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def _expected_recency_tier(as_of_date: date, anchor_date: date | None) -> str:
    if anchor_date is None:
        return "undated_unknown"
    age_days = (as_of_date - anchor_date).days
    if age_days < 0:
        return "undated_unknown"
    if age_days <= 30:
        return "days_0_30"
    if age_days <= 90:
        return "days_31_90"
    if age_days <= 180:
        return "days_91_180"
    return "days_over_180"


def _company_section_pattern(number: int, title: str) -> re.Pattern[str]:
    return re.compile(
        rf"^###\s+{number}\.\s+{re.escape(title)}\s*$"
        r"(?P<body>.*?)"
        r"(?=^###\s+\d+\.|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )


def _parse_company_yaml_section(
    text: str,
    number: int,
    title: str,
    root_key: str,
) -> tuple[Any, list[Finding]]:
    section, findings = _extract_section(
        _company_section_pattern(number, title),
        text,
        f"missing_company_section_{number}",
        f"Missing company report Section {number} {title}.",
    )
    if findings:
        return None, findings
    fence = YAML_FENCE_RE.search(section)
    if not fence:
        return None, [Finding(f"missing_company_yaml_{number}", f"Company report Section {number} has no yaml fence.")]
    try:
        data = yaml.safe_load(fence.group("body")) or {}
    except yaml.YAMLError as exc:
        return None, [Finding(f"invalid_company_yaml_{number}", f"Company report Section {number} YAML is invalid: {exc}")]
    value = data.get(root_key) if isinstance(data, dict) else None
    if value is None:
        return None, [Finding(f"missing_{root_key}", f"Company report Section {number} YAML lacks {root_key}.")]
    return value, []


def _walk_mapping_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(_normalize_vocab(key))
            keys.extend(_walk_mapping_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_mapping_keys(child))
    return keys


def _validate_company_sections(text: str) -> list[Finding]:
    headings = [
        (int(match.group("number")), _normalize_header(match.group("title")))
        for match in re.finditer(r"^###\s+(?P<number>\d+)\.\s+(?P<title>.+?)\s*$", text, re.MULTILINE)
    ]
    expected = [
        (index, _normalize_header(title))
        for index, title in enumerate(EXPECTED_COMPANY_SECTIONS, start=1)
    ]
    if headings == expected:
        return []
    return [
        Finding(
            "invalid_company_section_contract",
            "Company report must contain its conditional Sections 1-10 in the prompt-defined order.",
        )
    ]


def _validate_portfolio_retail_subsections(text: str) -> list[Finding]:
    section, findings = _extract_section(
        _company_section_pattern(5, EXPECTED_COMPANY_SECTIONS[4]),
        text,
        "missing_company_section_5",
        "Missing company report Section 5 Portfolio And Retail Architecture.",
    )
    if findings or not section:
        return []
    headings = [
        _normalize_header(match.group("title"))
        for match in re.finditer(r"^####\s+(?P<title>.+?)\s*$", section, re.MULTILINE)
    ]
    expected = [_normalize_header(title) for title in REQUIRED_PORTFOLIO_RETAIL_SUBSECTIONS]
    if headings == expected:
        return []
    return [
        Finding(
            "invalid_portfolio_retail_subsection_contract",
            "Company report Section 5 must contain the six Portfolio And Retail Architecture subsections in prompt-defined order.",
        )
    ]


def _validate_company_receipt(receipt: Any) -> tuple[dict[str, Any], list[Finding]]:
    if not isinstance(receipt, dict):
        return {}, [Finding("invalid_company_commission_receipt", "company_commission_receipt must be a mapping.")]
    findings: list[Finding] = []
    required = {
        "commission_id",
        "mode",
        "commission_profile",
        "subject_count",
        "subject_identity",
        "as_of_date",
        "time_posture",
        "longitudinal_period",
        "longitudinal_rationale",
        "initial_proving_run",
    }
    missing = sorted(required - set(receipt))
    if missing:
        findings.append(Finding("missing_company_receipt_fields", "company_commission_receipt is missing: " + ", ".join(missing)))
    if _normalize_vocab(receipt.get("mode")) not in VALID_HANDOFF_MODES:
        findings.append(Finding("invalid_company_mode", "Company report mode must remain backtest or forward."))
    if _normalize_vocab(receipt.get("commission_profile")) != "company_competitive_intelligence":
        findings.append(Finding("invalid_company_profile", "A one-company Brand/Org report must use company_competitive_intelligence."))
    if receipt.get("subject_count") != 1:
        findings.append(Finding("one_company_only", "Company reports must keep subject_count: 1."))
    identity = receipt.get("subject_identity")
    if not isinstance(identity, dict):
        findings.append(Finding("invalid_subject_identity", "subject_identity must be a mapping."))
    else:
        if _normalize_vocab(identity.get("subject_kind")) not in COMPANY_SUBJECT_KINDS:
            findings.append(Finding("invalid_company_subject_kind", "subject_identity.subject_kind must be Brand, Org, or unresolved Brand/Org."))
        if _normalize_vocab(identity.get("identity_state")) not in COMPANY_IDENTITY_STATES:
            findings.append(Finding("invalid_company_identity_state", "subject_identity.identity_state is invalid."))
        if not str(identity.get("raw_name", "")).strip():
            findings.append(Finding("missing_company_subject_name", "subject_identity.raw_name is required."))
    as_of = _parse_date(receipt.get("as_of_date"))
    if as_of is None:
        findings.append(Finding("invalid_company_as_of_date", "as_of_date must be an ISO date."))
    posture = _normalize_vocab(receipt.get("time_posture"))
    if posture not in COMPANY_TIME_POSTURES:
        findings.append(Finding("invalid_time_posture", "time_posture must be recency_first or longitudinal."))
    period = receipt.get("longitudinal_period")
    rationale = str(receipt.get("longitudinal_rationale", "")).strip()
    if posture == "longitudinal":
        if not isinstance(period, dict) or _parse_date(period.get("start")) is None or _parse_date(period.get("end")) is None:
            findings.append(Finding("missing_longitudinal_period", "longitudinal requires a declared start and end date."))
        if not rationale or _normalize_vocab(rationale) == "not_applicable":
            findings.append(Finding("missing_longitudinal_rationale", "longitudinal requires a rationale."))
    elif posture == "recency_first":
        if period not in (None, "not_applicable"):
            findings.append(Finding("unexpected_longitudinal_period", "recency_first must not declare a longitudinal period."))
    return receipt, findings


def _validate_company_coverage(
    coverage: Any,
    initial_proving_run: bool,
) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    if not isinstance(coverage, list):
        return {}, [Finding("invalid_coverage_ledger", "coverage_ledger must be a list.")]
    rows: dict[str, dict[str, Any]] = {}
    findings: list[Finding] = []
    for index, row in enumerate(coverage, start=1):
        if not isinstance(row, dict):
            findings.append(Finding("invalid_coverage_row", "Each coverage_ledger row must be a mapping."))
            continue
        coverage_id = str(row.get("coverage_id", "")).strip()
        if coverage_id != f"COV-{index:03d}":
            findings.append(Finding("invalid_coverage_id", f"Expected COV-{index:03d}, got {coverage_id or '<blank>'}."))
        if coverage_id in rows:
            findings.append(Finding("duplicate_coverage_id", f"Duplicate coverage ID {coverage_id}."))
            continue
        rows[coverage_id] = row
        required = {
            "coverage_id", "source_family", "source_surface", "venue", "relevance_rationale",
            "route_or_query", "requirement", "status", "yield", "recency", "access", "relevance", "gap_id",
        }
        missing = sorted(required - set(row))
        if missing:
            findings.append(Finding("missing_coverage_fields", "Coverage row is missing: " + ", ".join(missing), coverage_id))
        status = _normalize_vocab(row.get("status"))
        requirement = _normalize_vocab(row.get("requirement"))
        source_family = _normalize_vocab(row.get("source_family"))
        if source_family not in VALID_SOURCE_FAMILIES:
            findings.append(
                Finding(
                    "invalid_company_source_family",
                    f"Invalid source_family {source_family or '<blank>'}.",
                    coverage_id,
                )
            )
        if status not in COMPANY_COVERAGE_STATUSES:
            findings.append(Finding("invalid_coverage_status", f"Invalid coverage status {status or '<blank>'}.", coverage_id))
        if requirement not in COMPANY_COVERAGE_REQUIREMENTS:
            findings.append(Finding("invalid_coverage_requirement", f"Invalid coverage requirement {requirement or '<blank>'}.", coverage_id))
        if status == "not_applicable" and not str(row.get("relevance_rationale", "")).strip():
            findings.append(Finding("not_applicable_missing_rationale", "not_applicable coverage requires a relevance rationale.", coverage_id))
        if status == "blocked" and not str(row.get("gap_id", "")).strip():
            findings.append(Finding("blocked_coverage_missing_gap", "Blocked coverage must reference a typed gap.", coverage_id))

    reddit = [row for row in rows.values() if _normalize_vocab(row.get("venue")) == "reddit"]
    if not reddit:
        findings.append(Finding("missing_reddit_scout", "Every company report requires a bounded Reddit scout."))
    elif not any(_normalize_vocab(row.get("requirement")) == "mandatory_bounded_scout" for row in reddit):
        findings.append(Finding("invalid_reddit_scout_requirement", "Reddit must be marked mandatory_bounded_scout."))
    quora = [row for row in rows.values() if _normalize_vocab(row.get("venue")) == "quora"]
    if initial_proving_run:
        if not quora:
            findings.append(Finding("missing_quora_experimental_scout", "Initial proving runs require an explicit experimental Quora scout."))
        elif not any(_normalize_vocab(row.get("requirement")) == "experimental_initial_proving_run" for row in quora):
            findings.append(Finding("invalid_quora_scout_requirement", "Quora must be marked experimental_initial_proving_run."))
    return rows, findings


def _is_nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _rate_matches(value: Any, numerator: int, denominator: int) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or denominator <= 0:
        return False
    expected = (
        (Decimal(numerator) * Decimal(100)) / Decimal(denominator)
    ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)) == expected


def _validate_retailer_review_approval_signal(
    signal: Any,
    observation_id: str,
    source_family: str,
) -> list[Finding]:
    if not isinstance(signal, dict):
        return [
            Finding(
                "invalid_retailer_review_approval_signal",
                "retailer_review_approval_signal must be a mapping.",
                observation_id,
            )
        ]

    findings: list[Finding] = []
    missing = sorted(RETAILER_REVIEW_APPROVAL_REQUIRED_FIELDS - set(signal))
    if missing:
        findings.append(
            Finding(
                "missing_retailer_review_approval_fields",
                "retailer_review_approval_signal is missing: " + ", ".join(missing),
                observation_id,
            )
        )
        return findings

    if source_family not in {"reviews", "retail_pdp"}:
        findings.append(
            Finding(
                "invalid_retailer_review_approval_source",
                "retailer_review_approval_signal requires a reviews or retail_pdp observation.",
                observation_id,
            )
        )

    corpus_basis = _normalize_vocab(signal.get("corpus_basis"))
    if corpus_basis not in RETAILER_REVIEW_APPROVAL_CORPUS_BASES:
        findings.append(
            Finding(
                "invalid_retailer_review_corpus_basis",
                "corpus_basis must be complete_visible_corpus or reproducible_bounded_sample.",
                observation_id,
            )
        )
    for field in ("sample_selection", "incentive_disclosure_basis"):
        if not str(signal.get(field, "")).strip():
            findings.append(
                Finding(
                    "missing_retailer_review_reproducibility",
                    f"{field} must state the source-visible derivation basis.",
                    observation_id,
                )
            )

    invalid_counts = sorted(
        field
        for field in RETAILER_REVIEW_APPROVAL_COUNT_FIELDS
        if not _is_nonnegative_integer(signal.get(field))
    )
    if invalid_counts:
        findings.append(
            Finding(
                "invalid_retailer_review_approval_counts",
                "These retailer-review counts must be non-negative integers: " + ", ".join(invalid_counts),
                observation_id,
            )
        )
        return findings

    source_total_raw = signal["source_visible_total"]
    source_total = source_total_raw if _is_nonnegative_integer(source_total_raw) else None
    captured_total = signal["captured_total"]
    excluded_incentivized = signal["excluded_explicit_incentivized"]
    excluded_unknown = signal["excluded_unknown_or_conflicting"]
    excluded_other = signal["excluded_other"]
    explicit_non_incentivized = signal["eligible_explicit_non_incentivized"]
    not_marked = signal["eligible_not_marked_incentivized"]
    eligible_total = signal["eligible_total"]
    positive = signal["eligible_positive_4_5"]
    below_positive = signal["eligible_below_positive_1_3"]

    if captured_total <= 0 or eligible_total <= 0:
        findings.append(
            Finding(
                "empty_retailer_review_approval_denominator",
                "The derived approval signal requires captured rows and a non-zero eligible denominator; otherwise omit it and record the gap.",
                observation_id,
            )
        )
    if (
        (source_total is not None and source_total < captured_total)
        or (source_total is None and _normalize_vocab(source_total_raw) != "unknown")
        or (corpus_basis == "complete_visible_corpus" and source_total != captured_total)
    ):
        findings.append(
            Finding(
                "invalid_retailer_review_corpus_size",
                "source_visible_total must be an integer covering captured_total or unknown for a bounded sample; a complete corpus requires equality.",
                observation_id,
            )
        )
    if captured_total != (
        excluded_incentivized
        + excluded_unknown
        + excluded_other
        + explicit_non_incentivized
        + not_marked
    ):
        findings.append(
            Finding(
                "retailer_review_partition_mismatch",
                "Captured rows must reconcile to excluded and eligible incentive-posture partitions.",
                observation_id,
            )
        )
    if eligible_total != explicit_non_incentivized + not_marked or eligible_total != positive + below_positive:
        findings.append(
            Finding(
                "retailer_review_eligible_mismatch",
                "eligible_total must reconcile both incentive posture and 4-5 versus 1-3 star partitions.",
                observation_id,
            )
        )
    if excluded_other > 0 and _normalize_vocab(signal.get("excluded_other_reason")) in {"", "none"}:
        findings.append(
            Finding(
                "missing_retailer_review_other_exclusion_reason",
                "excluded_other > 0 requires a non-none reason.",
                observation_id,
            )
        )
    if eligible_total > 0 and (
        not _rate_matches(signal.get("approval_rate_pct"), positive, eligible_total)
        or not _rate_matches(signal.get("below_positive_rate_pct"), below_positive, eligible_total)
    ):
        findings.append(
            Finding(
                "invalid_retailer_review_approval_rates",
                "Approval rates must equal the round-half-up, one-decimal 4-5 and 1-3 star shares of eligible_total.",
                observation_id,
            )
        )

    sensitivity = signal.get("explicit_non_incentivized_sensitivity")
    if sensitivity is not None:
        if not isinstance(sensitivity, dict):
            findings.append(
                Finding(
                    "invalid_explicit_non_incentivized_sensitivity",
                    "explicit_non_incentivized_sensitivity must be a mapping.",
                    observation_id,
                )
            )
        else:
            required = {
                "eligible_total",
                "positive_4_5",
                "below_positive_1_3",
                "approval_rate_pct",
                "below_positive_rate_pct",
            }
            if required - set(sensitivity):
                findings.append(
                    Finding(
                        "missing_explicit_non_incentivized_sensitivity_fields",
                        "explicit_non_incentivized_sensitivity is incomplete.",
                        observation_id,
                    )
                )
            elif not all(
                _is_nonnegative_integer(sensitivity.get(field))
                for field in ("eligible_total", "positive_4_5", "below_positive_1_3")
            ):
                findings.append(
                    Finding(
                        "invalid_explicit_non_incentivized_sensitivity_counts",
                        "Sensitivity counts must be non-negative integers.",
                        observation_id,
                    )
                )
            else:
                sensitivity_total = sensitivity["eligible_total"]
                sensitivity_positive = sensitivity["positive_4_5"]
                sensitivity_below = sensitivity["below_positive_1_3"]
                if (
                    sensitivity_total <= 0
                    or sensitivity_total != explicit_non_incentivized
                    or sensitivity_total != sensitivity_positive + sensitivity_below
                    or not _rate_matches(
                        sensitivity.get("approval_rate_pct"),
                        sensitivity_positive,
                        sensitivity_total,
                    )
                    or not _rate_matches(
                        sensitivity.get("below_positive_rate_pct"),
                        sensitivity_below,
                        sensitivity_total,
                    )
                ):
                    findings.append(
                        Finding(
                            "invalid_explicit_non_incentivized_sensitivity",
                            "Sensitivity counts and rates must reconcile to eligible_explicit_non_incentivized.",
                            observation_id,
                        )
                    )
    return findings


def _validate_company_observations(
    observations: Any,
    receipt: dict[str, Any],
    coverage: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    if not isinstance(observations, list):
        return {}, [Finding("invalid_observation_ledger", "observation_ledger must be a list.")]
    rows: dict[str, dict[str, Any]] = {}
    findings: list[Finding] = []
    as_of = _parse_date(receipt.get("as_of_date"))
    posture = _normalize_vocab(receipt.get("time_posture"))
    period = receipt.get("longitudinal_period") if isinstance(receipt.get("longitudinal_period"), dict) else {}
    period_start = _parse_date(period.get("start"))
    period_end = _parse_date(period.get("end"))
    for index, row in enumerate(observations, start=1):
        if not isinstance(row, dict):
            findings.append(Finding("invalid_observation_row", "Each observation_ledger row must be a mapping."))
            continue
        observation_id = str(row.get("observation_id", "")).strip()
        if observation_id != f"OBS-{index:03d}":
            findings.append(Finding("invalid_observation_id", f"Expected OBS-{index:03d}, got {observation_id or '<blank>'}."))
        if observation_id in rows:
            findings.append(Finding("duplicate_observation_id", f"Duplicate observation ID {observation_id}."))
            continue
        rows[observation_id] = row
        missing = sorted(COMPANY_REQUIRED_OBSERVATION_FIELDS - set(row))
        if missing:
            findings.append(Finding("missing_observation_fields", "Observation is missing: " + ", ".join(missing), observation_id))
        coverage_id = str(row.get("coverage_id", "")).strip()
        if coverage_id not in coverage:
            findings.append(Finding("unknown_observation_coverage", f"Observation references unknown coverage {coverage_id}.", observation_id))
        elif _normalize_vocab(coverage[coverage_id].get("status")) != "checked":
            findings.append(Finding("observation_from_unchecked_coverage", "Evidence cannot come from blocked, unchecked, or not-applicable coverage.", observation_id))
        source_class = _normalize_vocab(row.get("source_class"))
        source_family = _normalize_vocab(row.get("source_family"))
        if source_family not in VALID_SOURCE_FAMILIES:
            findings.append(
                Finding(
                    "invalid_company_source_family",
                    f"Invalid source_family {source_family or '<blank>'}.",
                    observation_id,
                )
            )
        if "retailer_review_approval_signal" in row:
            findings.extend(
                _validate_retailer_review_approval_signal(
                    row.get("retailer_review_approval_signal"),
                    observation_id,
                    source_family,
                )
            )
        if source_class not in COMPANY_SOURCE_CLASSES:
            findings.append(Finding("invalid_company_source_class", f"Invalid source_class {source_class or '<blank>'}.", observation_id))
        fact_domain = _normalize_vocab(row.get("fact_domain"))
        if fact_domain not in COMPANY_FACT_DOMAINS:
            findings.append(Finding("invalid_company_fact_domain", f"Invalid fact_domain {fact_domain or '<blank>'}.", observation_id))
        if source_class == "customer_community" and fact_domain != "external_customer_evidence":
            findings.append(Finding("community_as_company_fact", "Customer/community evidence must remain external_customer_evidence.", observation_id))
        if _normalize_vocab(row.get("subject_kind")) not in COMPANY_SUBJECT_KINDS:
            findings.append(Finding("invalid_observation_subject_kind", "Observation subject_kind is invalid.", observation_id))
        if _normalize_vocab(row.get("identity_state")) not in COMPANY_IDENTITY_STATES:
            findings.append(Finding("invalid_observation_identity_state", "Observation identity_state is invalid.", observation_id))
        if not str(row.get("source_url_or_packet_locator", "")).strip() or not str(row.get("exact_locator", "")).strip():
            findings.append(Finding("unresolvable_observation_evidence", "Observation requires a source/packet locator and exact locator.", observation_id))
        if not isinstance(row.get("consumed_by_sections"), list) or not row.get("consumed_by_sections"):
            findings.append(Finding("invalid_observation_consumers", "consumed_by_sections must be a non-empty list.", observation_id))
        if not isinstance(row.get("independent_corroboration_ids"), list):
            findings.append(Finding("invalid_corroboration_ids", "independent_corroboration_ids must be a list.", observation_id))

        precision = _normalize_vocab(row.get("effective_time_precision"))
        if precision not in COMPANY_EFFECTIVE_TIME_PRECISIONS:
            findings.append(
                Finding(
                    "invalid_effective_time_precision",
                    f"effective_time_precision must be one of {', '.join(sorted(COMPANY_EFFECTIVE_TIME_PRECISIONS))}; "
                    f"got {precision or '<blank>'}.",
                    observation_id,
                )
            )
        if precision == "current_page_observation" and _parse_date(row.get("event_or_effective_date")) is not None:
            findings.append(Finding("current_page_as_dated_event", "A current-page observation must not be silently converted into a dated event.", observation_id))
        age_anchor_basis = _normalize_vocab(row.get("age_anchor_basis"))
        if age_anchor_basis not in COMPANY_AGE_ANCHOR_BASES:
            findings.append(
                Finding(
                    "invalid_age_anchor_basis",
                    f"age_anchor_basis must be one of {', '.join(sorted(COMPANY_AGE_ANCHOR_BASES))}; "
                    f"got {age_anchor_basis or '<blank>'}.",
                    observation_id,
                )
            )
        anchor = _parse_date(row.get("age_anchor_date"))
        declared_tier = _normalize_vocab(row.get("recency_tier"))
        expected_tier = _expected_recency_tier(as_of, anchor) if as_of else "undated_unknown"
        if declared_tier not in COMPANY_RECENCY_TIERS or declared_tier != expected_tier:
            findings.append(Finding("invalid_recency_tier", f"recency_tier must be {expected_tier} for the declared as_of/anchor dates, got {declared_tier or '<blank>'}.", observation_id))
        current_use = _normalize_vocab(row.get("current_state_use"))
        allowed_uses = {
            "days_0_30": {"primary_current", "current_corroboration", "supporting_or_recurrence", "contradiction"},
            "days_31_90": {"current_corroboration", "supporting_or_recurrence", "contradiction"},
            "days_91_180": {"supporting_or_recurrence", "chronology_historical_baseline", "contradiction"},
            "days_over_180": {"chronology_historical_baseline", "contradiction"},
            "undated_unknown": {"not_applicable", "contradiction"},
        }
        if current_use == "longitudinal_primary":
            if posture != "longitudinal" or anchor is None or period_start is None or period_end is None or not (period_start <= anchor <= period_end):
                findings.append(Finding("invalid_longitudinal_primary", "longitudinal_primary requires evidence inside the declared longitudinal period.", observation_id))
        elif current_use not in allowed_uses.get(declared_tier, set()):
            code = "older_evidence_as_current" if declared_tier in {"days_91_180", "days_over_180"} else "invalid_current_state_use"
            findings.append(Finding(code, "current_state_use conflicts with the deterministic recency ladder.", observation_id))

    for observation_id, row in rows.items():
        group = str(row.get("independence_syndication_group", "")).strip()
        if not group:
            findings.append(Finding("missing_syndication_group", "Every observation requires an independence/syndication group.", observation_id))
        for corroboration_id in row.get("independent_corroboration_ids", []) if isinstance(row.get("independent_corroboration_ids"), list) else []:
            other = rows.get(str(corroboration_id))
            if other is None:
                findings.append(Finding("unknown_corroboration_observation", f"Unknown corroboration observation {corroboration_id}.", observation_id))
            elif group == str(other.get("independence_syndication_group", "")).strip():
                findings.append(Finding("syndicated_as_independent", "Observations in the same syndication group are not independent corroboration.", observation_id))
    return rows, findings


def _validate_company_candidates(candidates: Any, observations: dict[str, dict[str, Any]]) -> list[Finding]:
    if not isinstance(candidates, list):
        return [Finding("invalid_company_surface_candidate_ledger", "company_surface_candidate_ledger must be a list.")]
    findings: list[Finding] = []
    for index, row in enumerate(candidates, start=1):
        if not isinstance(row, dict):
            findings.append(Finding("invalid_candidate_row", "Each candidate row must be a mapping."))
            continue
        candidate_id = str(row.get("candidate_id", "")).strip()
        if candidate_id != f"CSC-{index:03d}":
            findings.append(Finding("invalid_candidate_id", f"Expected CSC-{index:03d}, got {candidate_id or '<blank>'}."))
        if row.get("candidate_only") is not True or _normalize_vocab(row.get("import_status")) != "not_imported":
            findings.append(Finding("company_surface_import_forbidden", "Company Surface rows must be candidate_only and not_imported.", candidate_id))
        observation_ids = row.get("observation_ids")
        if not isinstance(observation_ids, list) or not observation_ids:
            findings.append(Finding("invalid_candidate_observations", "Candidate rows require observation_ids.", candidate_id))
            continue
        source_rows = [observations.get(str(item)) for item in observation_ids]
        if any(source is None for source in source_rows):
            findings.append(Finding("unknown_candidate_observation", "Candidate references an unknown observation.", candidate_id))
            continue
        if any(_normalize_vocab(source.get("source_class")) == "customer_community" for source in source_rows if source):
            if _normalize_vocab(row.get("candidate_fact_class")) != "external_customer_evidence":
                findings.append(Finding("community_candidate_as_company_fact", "Community-derived candidates must remain external_customer_evidence.", candidate_id))
    return findings


def _validate_company_observation_references(
    text: str, observations: dict[str, dict[str, Any]]
) -> list[Finding]:
    findings: list[Finding] = []
    for token in sorted(set(re.findall(r"\bOBS-\d{3}\b", text))):
        if token not in observations:
            findings.append(
                Finding(
                    "dangling_observation_reference",
                    f"Report references {token}, which has no observation_ledger row.",
                    token,
                )
            )
    return findings


def _scout_status_matches_coverage(
    rows: list[dict[str, Any]],
    scout_status: str,
) -> bool:
    if scout_status == NOT_REQUIRED_SCOUT_STATUS:
        return not rows or all(
            _normalize_vocab(row.get("status")) == "not_applicable"
            and _normalize_vocab(row.get("yield")) == "not_applicable"
            for row in rows
        )
    expected = COMPANY_SCOUT_STATUS_COVERAGE_STATES.get(scout_status)
    if expected is None:
        return False
    expected_status, expected_yield = expected
    return any(
        _normalize_vocab(row.get("status")) == expected_status
        and _normalize_vocab(row.get("yield")) == expected_yield
        for row in rows
    )


def _validate_company_completion(
    completion: Any,
    coverage: dict[str, dict[str, Any]],
    receipt: dict[str, Any],
) -> list[Finding]:
    if not isinstance(completion, dict):
        return [Finding("invalid_completion_ledger", "completion_ledger must be a mapping.")]
    findings: list[Finding] = []
    if _normalize_vocab(completion.get("completeness_policy")) != "necessary_complete_no_arbitrary_caps":
        findings.append(Finding("invalid_completeness_policy", "Company reports require necessary_complete_no_arbitrary_caps."))
    if _normalize_vocab(completion.get("hidden_venue_discovery")) != "category_aware":
        findings.append(Finding("invalid_hidden_venue_discovery", "Hidden-venue discovery must be category_aware."))
    if _normalize_vocab(completion.get("customer_community_boundary")) != "external_evidence_not_representative_demand_or_internal_fact":
        findings.append(Finding("invalid_community_boundary", "Community evidence boundary is missing or invalid."))
    if _normalize_vocab(completion.get("deep_competitor_treatment")) != "separate_named_follow_up_required":
        findings.append(Finding("invalid_competitor_boundary", "Deep competitor treatment requires a separately named follow-up."))
    if _normalize_vocab(completion.get("classifier_handoff")) != "omitted":
        findings.append(Finding("company_classifier_handoff_forbidden", "Company reports must omit classifier handoff."))
    run_boundary = str(completion.get("run_boundary", "")).strip()
    if run_boundary not in COMPANY_RUN_BOUNDARIES:
        findings.append(
            Finding(
                "invalid_company_run_boundary",
                "completion_ledger.run_boundary must be one of " + ", ".join(sorted(COMPANY_RUN_BOUNDARIES)) + ".",
            )
        )
    if "next_authorized_step" not in completion:
        findings.append(
            Finding("missing_company_next_authorized_step", "completion_ledger must include next_authorized_step.")
        )

    reddit_scout = _normalize_vocab(completion.get("reddit_scout_status"))
    quora_scout = _normalize_vocab(completion.get("quora_scout_status"))
    if reddit_scout not in COMPANY_REDDIT_SCOUT_STATUSES:
        findings.append(
            Finding(
                "invalid_reddit_scout_status",
                "reddit_scout_status must be one of "
                + ", ".join(sorted(COMPANY_REDDIT_SCOUT_STATUSES))
                + f"; got {completion.get('reddit_scout_status') or '<blank>'}.",
            )
        )
    if quora_scout not in COMPANY_QUORA_SCOUT_STATUSES:
        findings.append(
            Finding(
                "invalid_quora_scout_status",
                "quora_scout_status must be one of "
                + ", ".join(sorted(COMPANY_QUORA_SCOUT_STATUSES))
                + f"; got {completion.get('quora_scout_status') or '<blank>'}.",
            )
        )
    scout_checks = (
        ("reddit", "reddit_scout_status", reddit_scout, COMPANY_REDDIT_SCOUT_STATUSES),
        ("quora", "quora_scout_status", quora_scout, COMPANY_QUORA_SCOUT_STATUSES),
    )
    for venue, label, scout_status, valid_statuses in scout_checks:
        if scout_status not in valid_statuses:
            continue
        rows = [
            row
            for row in coverage.values()
            if _normalize_vocab(row.get("venue")) == venue
        ]
        if not _scout_status_matches_coverage(rows, scout_status):
            findings.append(
                Finding(
                    f"{label}_coverage_mismatch",
                    f"{label} {scout_status} must match the {venue.title()} coverage row status and yield.",
                )
            )
    commission_stage = run_boundary == COMMISSION_STAGE_RUN_BOUNDARY
    completion_profile = _normalize_vocab(
        receipt.get("understanding_completion_profile")
    )
    if completion_profile in LEGACY_CONSUMER_UNDERSTANDING_PROFILES:
        findings.append(
            Finding(
                "legacy_consumer_understanding_profile_forbidden",
                "Historical broad_consumer_brand_understanding_v1/v2 records are audit-only and cannot commission or complete a current company Understanding run.",
            )
        )
    elif completion_profile not in UNDERSTANDING_COMPLETION_PROFILES:
        findings.append(
            Finding(
                "missing_or_invalid_understanding_completion_profile",
                "Every current company Understanding record must carry broad_company_understanding_v1 or broad_consumer_brand_understanding_v3 from commission through completion.",
            )
        )
    elif completion_profile == BROAD_CONSUMER_UNDERSTANDING_PROFILE:
        identity = receipt.get("subject_identity")
        subject_kind = (
            _normalize_vocab(identity.get("subject_kind"))
            if isinstance(identity, dict)
            else ""
        )
        if subject_kind != "brand":
            findings.append(
                Finding(
                    "consumer_understanding_profile_requires_brand_subject",
                    "broad_consumer_brand_understanding_v3 requires subject_identity.subject_kind: brand; its acquisition seal must bind understanding_evidence_depth_v4.",
                )
            )
    if commission_stage:
        if _normalize_vocab(receipt.get("controller_placement")) != "top_level_co0":
            findings.append(
                Finding(
                    "invalid_commission_controller_placement",
                    "Commission-stage company acquisition requires controller_placement: top_level_co0.",
                )
            )
        if receipt.get("worker_slots_required") != 3:
            findings.append(
                Finding(
                    "invalid_commission_worker_slot_requirement",
                    "Commission-stage company acquisition requires exactly three CO1-CO3 worker slots.",
                )
            )
        available = receipt.get("worker_slots_available")
        if not isinstance(available, int) or isinstance(available, bool) or available < 3:
            findings.append(
                Finding(
                    "blocked_controller_capacity",
                    "CO0 must have three worker slots available before source acquisition starts.",
                )
            )
        required_surfaces = {
            "google_ads_transparency_center": (
                "missing_google_ads_transparency_commission",
                "required",
            ),
            "meta_ads_library": (
                "missing_meta_ads_library_commission",
                "required",
            ),
            "reddit_weekly_data_lake_read": (
                "missing_reddit_weekly_lake_commission",
                "required",
            ),
            "native_social_trigger_assessment": (
                "missing_native_social_trigger_assessment",
                "conditional",
            ),
            "tiktok_shop_trigger_assessment": (
                "missing_tiktok_shop_trigger_assessment",
                "conditional",
            ),
        }
        for source_surface, (code, expected_requirement) in required_surfaces.items():
            rows = [
                row
                for row in coverage.values()
                if _normalize_vocab(row.get("source_surface")) == source_surface
            ]
            if not rows:
                findings.append(
                    Finding(
                        code,
                        f"Commission-stage company acquisition must include {source_surface} coverage.",
                    )
                )
            elif not any(
                _normalize_vocab(row.get("requirement")) == expected_requirement
                for row in rows
            ):
                findings.append(
                    Finding(
                        f"invalid_{source_surface}_requirement",
                        f"{source_surface} must be marked {expected_requirement} at commission stage.",
                    )
                )
    if commission_stage and not any(
        _normalize_vocab(row.get("status")) == "not_checked" for row in coverage.values()
    ):
        findings.append(
            Finding(
                "commission_stage_without_open_coverage",
                "COMMISSION_SEALED_PRE_SCAN is valid only while the coverage ledger still contains not_checked rows.",
            )
        )
    if not commission_stage:
        for label, value in (("reddit_scout_status", reddit_scout), ("quora_scout_status", quora_scout)):
            if value == COMMISSION_STAGE_SCOUT_STATUS:
                findings.append(
                    Finding(
                        "commission_scout_status_outside_commission_stage",
                        f"{label} commissioned_not_yet_run is valid only under run_boundary COMMISSION_SEALED_PRE_SCAN.",
                    )
                )

    lens = completion.get("required_lens_coverage")
    if not isinstance(lens, dict) or set(lens) != COMPANY_LENS_KEYS:
        findings.append(Finding("invalid_required_lens_coverage", "required_lens_coverage must contain the nine company-report lenses."))
    else:
        for key, value in lens.items():
            if not isinstance(value, dict) or _normalize_vocab(value.get("status")) not in {"complete", "gap", "not_applicable_with_rationale"}:
                findings.append(Finding("invalid_lens_coverage_status", f"Lens {key} has invalid status."))

    gaps = completion.get("gaps")
    requests = completion.get("requests")
    if not isinstance(gaps, list) or not all(isinstance(item, dict) for item in gaps):
        findings.append(Finding("invalid_typed_gaps", "completion_ledger.gaps must be a list of typed mappings."))
        gaps = []
    if not isinstance(requests, list) or not all(isinstance(item, dict) for item in requests):
        findings.append(Finding("invalid_typed_requests", "completion_ledger.requests must be a list of typed mappings."))
        requests = []
    gap_ids = {str(item.get("gap_id", "")).strip() for item in gaps}
    request_ids = {str(item.get("request_id", "")).strip() for item in requests}
    for item in gaps:
        required = {"gap_id", "gap_type", "status", "description", "affected_coverage_ids", "request_ids"}
        if required - set(item):
            findings.append(Finding("invalid_typed_gap_shape", "Each typed gap requires identity, type, status, description, coverage, and request fields."))
        for request_id in item.get("request_ids", []) if isinstance(item.get("request_ids"), list) else []:
            if str(request_id) not in request_ids:
                findings.append(Finding("unknown_gap_request", f"Gap references unknown request {request_id}."))
    for item in requests:
        required = {"request_id", "request_type", "owner", "status", "description", "source_surface"}
        if required - set(item):
            findings.append(Finding("invalid_typed_request_shape", "Each typed request requires identity, type, owner, status, description, and source_surface."))
    for coverage_id, row in coverage.items():
        if _normalize_vocab(row.get("status")) == "blocked" and str(row.get("gap_id", "")).strip() not in gap_ids:
            findings.append(Finding("blocked_coverage_gap_unresolved", "Blocked coverage must resolve to completion_ledger.gaps.", coverage_id))
    return findings


def validate_company_report(text: str) -> list[Finding]:
    findings = _validate_company_sections(text)
    findings.extend(_validate_portfolio_retail_subsections(text))
    findings.extend(_validate_engagement_overclaims(text))
    section_specs = [
        (1, EXPECTED_COMPANY_SECTIONS[0], "company_commission_receipt"),
        (3, EXPECTED_COMPANY_SECTIONS[2], "coverage_ledger"),
        (4, EXPECTED_COMPANY_SECTIONS[3], "observation_ledger"),
        (9, EXPECTED_COMPANY_SECTIONS[8], "company_surface_candidate_ledger"),
        (10, EXPECTED_COMPANY_SECTIONS[9], "completion_ledger"),
    ]
    parsed: dict[str, Any] = {}
    for number, title, root_key in section_specs:
        value, parse_findings = _parse_company_yaml_section(text, number, title, root_key)
        parsed[root_key] = value
        findings.extend(parse_findings)
    if any(value is None for value in parsed.values()):
        return findings

    receipt, receipt_findings = _validate_company_receipt(parsed["company_commission_receipt"])
    findings.extend(receipt_findings)
    coverage, coverage_findings = _validate_company_coverage(
        parsed["coverage_ledger"],
        receipt.get("initial_proving_run") is True,
    )
    findings.extend(coverage_findings)
    observations, observation_findings = _validate_company_observations(
        parsed["observation_ledger"], receipt, coverage
    )
    findings.extend(observation_findings)
    findings.extend(_validate_company_observation_references(text, observations))
    findings.extend(_validate_company_candidates(parsed["company_surface_candidate_ledger"], observations))
    findings.extend(
        _validate_company_completion(
            parsed["completion_ledger"], coverage, receipt
        )
    )

    keys = _walk_mapping_keys(parsed)
    for key in sorted(set(keys) & COMPANY_PROHIBITED_GTM_KEYS):
        findings.append(Finding("prohibited_company_field", f"Company report contains prohibited GTM field: {key}."))
    for key in sorted(set(keys) & COMPANY_PROHIBITED_CAP_KEYS):
        findings.append(Finding("arbitrary_company_cap", f"Company report contains a prohibited arbitrary cap field: {key}."))
    if re.search(r"(?m)^\s*classifier_handoff_packet\s*:", text):
        findings.append(Finding("company_classifier_handoff_forbidden", "Company reports must not contain classifier_handoff_packet."))
    for number in range(5, 9):
        section, section_findings = _extract_section(
            _company_section_pattern(number, EXPECTED_COMPANY_SECTIONS[number - 1]),
            text,
            f"missing_company_section_{number}",
            f"Missing company report Section {number}.",
        )
        findings.extend(section_findings)
        if section and not re.search(r"\bOBS-\d{3}\b", section):
            findings.append(Finding("uncited_company_synthesis", f"Company report Section {number} must cite observation IDs."))
    return findings


def validate_text(text: str) -> list[Finding]:
    if COMPANY_REPORT_MARKER_RE.search(text):
        return validate_company_report(text)
    section_findings = validate_section_contract(text)
    rows, row_findings = parse_signal_rows(text)
    packet, packet_findings = parse_classifier_handoff(text)
    status_packet, status_findings = parse_board_status(text)
    findings = [*section_findings, *row_findings, *packet_findings, *status_findings]
    findings.extend(_validate_engagement_overclaims(text))
    if packet_findings or not rows:
        return findings

    findings.extend(_validate_packet_shape(packet))

    mode = _normalize_vocab(packet.get("mode"))
    if not mode:
        findings.append(Finding("missing_handoff_mode", "classifier_handoff_packet.mode is required."))
    elif mode not in VALID_HANDOFF_MODES:
        findings.append(
            Finding(
                "invalid_handoff_mode",
                f"classifier_handoff_packet.mode must be one of {', '.join(sorted(VALID_HANDOFF_MODES))}.",
            )
        )

    signal_ids, signal_findings = _handoff_ids(packet, "signal_rows_for_handoff")
    counter_ids, counter_findings = _handoff_ids(packet, "counterevidence_rows_for_handoff")
    findings.extend(signal_findings)
    findings.extend(counter_findings)

    all_ids = [*signal_ids, *counter_ids]
    seen: set[str] = set()
    for row_id in all_ids:
        if row_id in seen:
            findings.append(Finding("duplicate_handoff_row", f"Row {row_id} appears more than once.", row_id))
            continue
        seen.add(row_id)

        row = rows.get(row_id)
        if row is None:
            findings.append(Finding("handoff_row_unknown", f"Row {row_id} is not present in Section 4.", row_id))
            continue
        findings.extend(_validate_handoff_row(row_id, row, mode))

    if status_packet:
        findings.extend(_validate_board_status_shape(status_packet))

    return findings


def _expected_from_fixture(path: Path) -> str:
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.search(r"fixture_expected:\s*(pass|fail)", first_line)
    if not match:
        return ""
    return match.group(1)


def selftest() -> int:
    root = Path(__file__).resolve().parents[2]
    fixture_dir = root / "forseti-harness" / "tests" / "fixtures" / "commission_signal_board_outputs"
    fixture_paths = sorted(fixture_dir.glob("*.txt"))
    if not fixture_paths:
        print(f"SELFTEST FAILED: no fixtures found at {fixture_dir}")
        return 1

    ok = True
    for path in fixture_paths:
        expected = _expected_from_fixture(path)
        findings = validate_text(path.read_text(encoding="utf-8"))
        passed = not findings
        if expected == "pass" and passed:
            print(f"PASS {path.name}")
        elif expected == "fail" and not passed:
            print(f"PASS {path.name} expected fail: {', '.join(sorted({f.code for f in findings}))}")
        else:
            ok = False
            print(f"FAIL {path.name} expected={expected or '<missing>'} findings={findings}")
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    paths = [Path(arg) for arg in argv if not arg.startswith("-")]
    if not paths:
        print("usage: check_commission_signal_board_output.py [--selftest] <output-file> [...]", file=sys.stderr)
        return 2

    exit_code = 0
    for path in paths:
        findings = validate_text(path.read_text(encoding="utf-8"))
        if findings:
            exit_code = 1
            print(f"FAIL {path}")
            for finding in findings:
                suffix = f" row={finding.row_id}" if finding.row_id else ""
                print(f"  {finding.code}{suffix}: {finding.message}")
        else:
            print(f"PASS {path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
