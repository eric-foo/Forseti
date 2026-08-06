from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import re
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / ".agents" / "hooks" / "check_commission_signal_board_output.py"
FIXTURE_DIR = REPO_ROOT / "forseti-harness" / "tests" / "fixtures" / "commission_signal_board_outputs"
COMPANY_FIXTURE = FIXTURE_DIR / "valid_company_competitive_intelligence_output.txt"


def _load_validator():
    spec = importlib.util.spec_from_file_location("check_commission_signal_board_output", VALIDATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


@pytest.mark.parametrize(
    "fixture_name",
    [
        "valid_empty_backtest_output.txt",
        "valid_source_backed_backtest_output.txt",
        "valid_source_backed_forward_output.txt",
        "valid_adjacent_research_proof_output.txt",
        "valid_company_competitive_intelligence_output.txt",
        "valid_company_commission_stage_output.txt",
    ],
)
def test_valid_commission_signal_board_outputs_pass(fixture_name: str) -> None:
    findings = validator.validate_text((FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))
    assert findings == []


def test_commission_stage_requires_understanding_completion_profile() -> None:
    path = FIXTURE_DIR / "valid_company_commission_stage_output.txt"
    text = path.read_text(encoding="utf-8").replace(
        "  understanding_completion_profile: broad_company_understanding_v1\n",
        "",
        1,
    )

    assert (
        "missing_or_invalid_understanding_completion_profile"
        in _company_codes(text)
    )


def test_completed_company_report_retains_understanding_completion_profile() -> None:
    text = _valid_company_text().replace(
        "  understanding_completion_profile: broad_company_understanding_v1\n",
        "",
        1,
    )
    assert (
        "missing_or_invalid_understanding_completion_profile"
        in _company_codes(text)
    )


def _consumer_v4_text(*, completed: bool = False) -> str:
    if completed:
        text = _valid_company_text()
    else:
        text = (
            FIXTURE_DIR / "valid_company_commission_stage_output.txt"
        ).read_text(encoding="utf-8")
    return text.replace(
        "  understanding_completion_profile: broad_company_understanding_v1",
        "  understanding_completion_profile: broad_consumer_brand_understanding_v4",
        1,
    ).replace(
        "    subject_kind: brand_or_org_unresolved",
        "    subject_kind: brand",
        1,
    )


def test_current_consumer_v4_profile_passes_commission_and_completed_records() -> None:
    assert _company_codes(_consumer_v4_text()) == set()
    assert _company_codes(_consumer_v4_text(completed=True)) == set()
    assert validator.UNDERSTANDING_PROFILE_DEPTH_CONTRACT[
        "broad_consumer_brand_understanding_v4"
    ] == "understanding_evidence_depth_v5"


@pytest.mark.parametrize(
    "legacy_profile",
    [
        "broad_consumer_brand_understanding_v1",
        "broad_consumer_brand_understanding_v2",
        "broad_consumer_brand_understanding_v3",
    ],
)
def test_legacy_consumer_profiles_cannot_satisfy_a_current_record(
    legacy_profile: str,
) -> None:
    text = _consumer_v4_text().replace(
        "broad_consumer_brand_understanding_v4",
        legacy_profile,
        1,
    )
    assert "legacy_consumer_understanding_profile_forbidden" in _company_codes(text)


def test_consumer_v4_profile_requires_a_brand_subject() -> None:
    text = _consumer_v4_text().replace(
        "    subject_kind: brand",
        "    subject_kind: brand_or_org_unresolved",
        1,
    )
    assert (
        "consumer_understanding_profile_requires_brand_subject"
        in _company_codes(text)
    )


def _valid_company_text() -> str:
    return COMPANY_FIXTURE.read_text(encoding="utf-8")


def _company_codes(text: str) -> set[str]:
    return {finding.code for finding in validator.validate_text(text)}


def test_company_report_requires_portfolio_and_retail_architecture_section() -> None:
    text = _valid_company_text().replace(
        "### 5. Portfolio And Retail Architecture",
        "### 5. Positioning, Offerings, Markets, And Channels",
        1,
    )
    assert "invalid_company_section_contract" in _company_codes(text)


def test_company_report_requires_ordered_portfolio_retail_subsections() -> None:
    text = _valid_company_text().replace(
        "#### Qualified Retailer Corpus",
        "#### Retail Evidence",
        1,
    )
    assert "invalid_portfolio_retail_subsection_contract" in _company_codes(text)


def test_company_report_requires_portfolio_retail_completion_lens() -> None:
    text = _valid_company_text().replace(
        "    portfolio_and_retail_architecture: {status: complete, observation_ids: [OBS-001, OBS-003], rationale: owned and retailer architecture is visible}\n",
        "",
        1,
    )
    assert "invalid_required_lens_coverage" in _company_codes(text)


def _with_retailer_review_signal(text: str, block: str) -> str:
    anchor = "    consumed_by_sections: [5, 6, 8]\n"
    assert anchor in text
    head, separator, tail = text.rpartition(anchor)
    assert separator
    return head + separator + block + tail


DR_JART_RETAILER_REVIEW_SIGNAL = """\
    retailer_review_approval_signal:
      corpus_basis: complete_visible_corpus
      source_visible_total: 622
      captured_total: 622
      sample_selection: all source-visible rows at capture
      incentive_disclosure_basis: source-visible retailer incentive labels
      excluded_explicit_incentivized: 545
      excluded_unknown_or_conflicting: 0
      excluded_other: 0
      excluded_other_reason: none
      eligible_explicit_non_incentivized: 46
      eligible_not_marked_incentivized: 31
      eligible_total: 77
      eligible_positive_4_5: 44
      eligible_below_positive_1_3: 33
      approval_rate_pct: 57.1
      below_positive_rate_pct: 42.9
      explicit_non_incentivized_sensitivity:
        eligible_total: 46
        positive_4_5: 26
        below_positive_1_3: 20
        approval_rate_pct: 56.5
        below_positive_rate_pct: 43.5
"""


def _valid_retailer_review_signal() -> dict:
    return {
        "corpus_basis": "complete_visible_corpus",
        "source_visible_total": 622,
        "captured_total": 622,
        "sample_selection": "all source-visible rows at capture",
        "incentive_disclosure_basis": "source-visible retailer incentive labels",
        "excluded_explicit_incentivized": 545,
        "excluded_unknown_or_conflicting": 0,
        "excluded_other": 0,
        "excluded_other_reason": "none",
        "eligible_explicit_non_incentivized": 46,
        "eligible_not_marked_incentivized": 31,
        "eligible_total": 77,
        "eligible_positive_4_5": 44,
        "eligible_below_positive_1_3": 33,
        "approval_rate_pct": 57.1,
        "below_positive_rate_pct": 42.9,
        "explicit_non_incentivized_sensitivity": {
            "eligible_total": 46,
            "positive_4_5": 26,
            "below_positive_1_3": 20,
            "approval_rate_pct": 56.5,
            "below_positive_rate_pct": 43.5,
        },
    }


def _retailer_signal_codes(signal, source_family: str = "retail_pdp") -> set[str]:
    return {
        finding.code
        for finding in validator._validate_retailer_review_approval_signal(
            signal,
            "OBS-TEST",
            source_family,
        )
    }


def test_retailer_review_approval_signal_accepts_reconciled_reference_counts() -> None:
    text = _with_retailer_review_signal(_valid_company_text(), DR_JART_RETAILER_REVIEW_SIGNAL)
    assert _company_codes(text) == set()


def test_retailer_review_approval_signal_rejects_partition_mismatch() -> None:
    block = DR_JART_RETAILER_REVIEW_SIGNAL.replace(
        "      excluded_explicit_incentivized: 545",
        "      excluded_explicit_incentivized: 544",
    )
    assert "retailer_review_partition_mismatch" in _company_codes(
        _with_retailer_review_signal(_valid_company_text(), block)
    )


def test_retailer_review_approval_signal_rejects_wrong_rate() -> None:
    block = DR_JART_RETAILER_REVIEW_SIGNAL.replace(
        "      approval_rate_pct: 57.1",
        "      approval_rate_pct: 88.7",
        1,
    )
    assert "invalid_retailer_review_approval_rates" in _company_codes(
        _with_retailer_review_signal(_valid_company_text(), block)
    )


def test_retailer_review_approval_signal_rejects_sample_claimed_as_complete() -> None:
    block = DR_JART_RETAILER_REVIEW_SIGNAL.replace(
        "      captured_total: 622",
        "      captured_total: 77",
    ).replace(
        "      excluded_explicit_incentivized: 545",
        "      excluded_explicit_incentivized: 0",
    )
    assert "invalid_retailer_review_corpus_size" in _company_codes(
        _with_retailer_review_signal(_valid_company_text(), block)
    )


def test_retailer_review_approval_signal_allows_unknown_source_total_for_bounded_sample() -> None:
    block = DR_JART_RETAILER_REVIEW_SIGNAL.replace(
        "      corpus_basis: complete_visible_corpus",
        "      corpus_basis: reproducible_bounded_sample",
    ).replace(
        "      source_visible_total: 622",
        "      source_visible_total: unknown",
    )
    assert _company_codes(_with_retailer_review_signal(_valid_company_text(), block)) == set()


def test_retailer_review_approval_signal_uses_one_decimal_round_half_up() -> None:
    signal = _valid_retailer_review_signal()
    signal.update(
        {
            "source_visible_total": 16,
            "captured_total": 16,
            "excluded_explicit_incentivized": 0,
            "eligible_explicit_non_incentivized": 0,
            "eligible_not_marked_incentivized": 16,
            "eligible_total": 16,
            "eligible_positive_4_5": 1,
            "eligible_below_positive_1_3": 15,
            "approval_rate_pct": 6.3,
            "below_positive_rate_pct": 93.8,
        }
    )
    signal.pop("explicit_non_incentivized_sensitivity")
    assert _retailer_signal_codes(signal) == set()

    signal["approval_rate_pct"] = 6.2
    assert "invalid_retailer_review_approval_rates" in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_non_mapping() -> None:
    assert "invalid_retailer_review_approval_signal" in _retailer_signal_codes([])


def test_retailer_review_approval_signal_rejects_missing_fields() -> None:
    signal = _valid_retailer_review_signal()
    signal.pop("sample_selection")
    assert "missing_retailer_review_approval_fields" in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_wrong_source_family() -> None:
    assert "invalid_retailer_review_approval_source" in _retailer_signal_codes(
        _valid_retailer_review_signal(),
        source_family="owned_channels",
    )


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ({"corpus_basis": "unknown"}, "invalid_retailer_review_corpus_basis"),
        ({"sample_selection": ""}, "missing_retailer_review_reproducibility"),
        ({"captured_total": True}, "invalid_retailer_review_approval_counts"),
        ({"captured_total": 0}, "empty_retailer_review_approval_denominator"),
        ({"source_visible_total": 76}, "invalid_retailer_review_corpus_size"),
        ({"eligible_not_marked_incentivized": 30}, "retailer_review_eligible_mismatch"),
        (
            {"excluded_other": 1, "excluded_other_reason": "none"},
            "missing_retailer_review_other_exclusion_reason",
        ),
    ],
)
def test_retailer_review_approval_signal_rejects_invalid_primary_fields(
    mutation: dict,
    expected_code: str,
) -> None:
    signal = _valid_retailer_review_signal()
    signal.update(mutation)
    assert expected_code in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_non_mapping_sensitivity() -> None:
    signal = _valid_retailer_review_signal()
    signal["explicit_non_incentivized_sensitivity"] = []
    assert "invalid_explicit_non_incentivized_sensitivity" in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_incomplete_sensitivity() -> None:
    signal = _valid_retailer_review_signal()
    sensitivity = deepcopy(signal["explicit_non_incentivized_sensitivity"])
    sensitivity.pop("approval_rate_pct")
    signal["explicit_non_incentivized_sensitivity"] = sensitivity
    assert "missing_explicit_non_incentivized_sensitivity_fields" in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_invalid_sensitivity_counts() -> None:
    signal = _valid_retailer_review_signal()
    sensitivity = deepcopy(signal["explicit_non_incentivized_sensitivity"])
    sensitivity["eligible_total"] = True
    signal["explicit_non_incentivized_sensitivity"] = sensitivity
    assert "invalid_explicit_non_incentivized_sensitivity_counts" in _retailer_signal_codes(signal)


def test_retailer_review_approval_signal_rejects_unreconciled_sensitivity() -> None:
    signal = _valid_retailer_review_signal()
    sensitivity = deepcopy(signal["explicit_non_incentivized_sensitivity"])
    sensitivity["positive_4_5"] = 25
    signal["explicit_non_incentivized_sensitivity"] = sensitivity
    assert "invalid_explicit_non_incentivized_sensitivity" in _retailer_signal_codes(signal)


def test_company_subject_defaults_to_company_competitive_intelligence() -> None:
    text = _valid_company_text().replace(
        "commission_profile: company_competitive_intelligence",
        "commission_profile: standard_signal_board",
        1,
    )
    assert "invalid_company_profile" in _company_codes(text)


def test_company_report_requires_complete_observation_traceability() -> None:
    text = _valid_company_text().replace("    exact_locator: page heading Current products\n", "", 1)
    assert "missing_observation_fields" in _company_codes(text)


def test_current_page_observation_is_not_silently_converted_to_dated_event() -> None:
    text = _valid_company_text().replace(
        "    event_or_effective_date: null\n    observation_at: \"2026-07-16T09:00:00Z\"",
        "    event_or_effective_date: \"2026-07-16\"\n    observation_at: \"2026-07-16T09:00:00Z\"",
        1,
    )
    assert "current_page_as_dated_event" in _company_codes(text)


def test_company_recency_tier_is_deterministic() -> None:
    text = _valid_company_text().replace("    recency_tier: days_0_30", "    recency_tier: days_over_180", 1)
    assert "invalid_recency_tier" in _company_codes(text)


def test_syndicated_sources_are_not_independent_corroboration() -> None:
    text = _valid_company_text().replace(
        "    independence_syndication_group: distribution_announcement_001\n    independent_corroboration_ids: []",
        "    independence_syndication_group: distribution_announcement_001\n    independent_corroboration_ids: [OBS-003]",
        1,
    )
    assert "syndicated_as_independent" in _company_codes(text)


def test_community_evidence_cannot_become_company_fact() -> None:
    text = _valid_company_text().replace(
        "    fact_domain: external_customer_evidence",
        "    fact_domain: company_fact",
        1,
    )
    assert "community_as_company_fact" in _company_codes(text)


def test_blocked_venue_remains_a_typed_gap() -> None:
    text = _valid_company_text().replace(
        "    requirement: mandatory_bounded_scout\n    status: checked\n    yield: zero_yield",
        "    requirement: mandatory_bounded_scout\n    status: blocked\n    yield: blocked",
        1,
    )
    assert "blocked_coverage_gap_unresolved" in _company_codes(text)


def test_not_applicable_venue_requires_rationale() -> None:
    text = _valid_company_text().replace(
        "    relevance_rationale: Category-aware hidden-venue discovery surfaced a relevant specialist thread.",
        "    relevance_rationale: \"\"",
        1,
    ).replace(
        "    requirement: category_aware\n    status: checked",
        "    requirement: category_aware\n    status: not_applicable",
        1,
    )
    assert "not_applicable_missing_rationale" in _company_codes(text)


def test_company_report_rejects_gtm_fields() -> None:
    text = _valid_company_text().replace(
        "  commission_id: fixture_company_example_labs",
        "  commission_id: fixture_company_example_labs\n  buyer: forbidden",
        1,
    )
    assert "prohibited_company_field" in _company_codes(text)


def test_older_evidence_cannot_masquerade_as_current() -> None:
    text = _valid_company_text().replace(
        "    current_state_use: chronology_historical_baseline",
        "    current_state_use: primary_current",
        1,
    )
    assert "older_evidence_as_current" in _company_codes(text)


def test_company_completeness_has_no_arbitrary_cap_policy() -> None:
    text = _valid_company_text().replace(
        "completeness_policy: necessary_complete_no_arbitrary_caps",
        "completeness_policy: max_ten_sources",
        1,
    )
    assert "invalid_completeness_policy" in _company_codes(text)


def test_company_report_is_one_company_at_a_time() -> None:
    text = _valid_company_text().replace("  subject_count: 1", "  subject_count: 2", 1)
    assert "one_company_only" in _company_codes(text)


def test_company_surface_rows_are_candidate_only_and_not_imported() -> None:
    text = _valid_company_text().replace("    candidate_only: true", "    candidate_only: false", 1)
    assert "company_surface_import_forbidden" in _company_codes(text)


def test_company_report_has_no_classifier_handoff_packet() -> None:
    text = _valid_company_text().replace(
        "  classifier_handoff: omitted",
        "  classifier_handoff: omitted\n  classifier_handoff_packet: {}",
        1,
    )
    assert "company_classifier_handoff_forbidden" in _company_codes(text)


def test_recency_first_is_the_required_explicit_default() -> None:
    text = _valid_company_text().replace("  time_posture: recency_first\n", "", 1)
    assert "invalid_time_posture" in _company_codes(text)


def test_longitudinal_is_a_valid_declared_override() -> None:
    text = _valid_company_text().replace(
        "  time_posture: recency_first\n  longitudinal_period: null\n  longitudinal_rationale: not_applicable",
        "  time_posture: longitudinal\n  longitudinal_period:\n    start: \"2025-01-01\"\n    end: \"2026-07-16\"\n  longitudinal_rationale: Trace change and recurrence across the declared period.",
        1,
    ).replace(
        "    current_state_use: chronology_historical_baseline",
        "    current_state_use: longitudinal_primary",
        1,
    )
    assert validator.validate_text(text) == []


def test_company_report_rejects_engagement_overclaim() -> None:
    text = _valid_company_text().replace(
        "The Reddit scout yielded no attributable material.",
        "The Reddit scout yielded no attributable material. High engagement proves demand.",
        1,
    )
    assert "engagement_as_proof" in _company_codes(text)


def test_company_report_rejects_dangling_observation_reference() -> None:
    text = _valid_company_text().replace(
        "Example Labs presents Product One as its current flagship.",
        "Example Labs presents Product One as its current flagship (OBS-099).",
        1,
    )
    assert "dangling_observation_reference" in _company_codes(text)


def test_company_source_family_uses_shared_vocabulary() -> None:
    text = _valid_company_text().replace(
        "    source_family: owned_channels",
        "    source_family: official_company",
        1,
    )
    assert "invalid_company_source_family" in _company_codes(text)


def test_company_effective_time_precision_vocabulary_is_enforced() -> None:
    text = _valid_company_text().replace(
        "    effective_time_precision: current_page_observation",
        "    effective_time_precision: current_page",
        1,
    )
    assert "invalid_effective_time_precision" in _company_codes(text)


def test_unknown_effective_time_precision_cannot_bypass_dated_event_guard() -> None:
    text = _valid_company_text().replace(
        "    effective_time_precision: current_page_observation",
        "    effective_time_precision: current_page",
        1,
    ).replace(
        "    event_or_effective_date: null\n    observation_at: \"2026-07-16T09:00:00Z\"",
        "    event_or_effective_date: \"2026-07-16\"\n    observation_at: \"2026-07-16T09:00:00Z\"",
        1,
    )
    assert "invalid_effective_time_precision" in _company_codes(text)


def test_company_age_anchor_basis_vocabulary_is_enforced() -> None:
    text = _valid_company_text().replace(
        "    age_anchor_basis: current_page_observation",
        "    age_anchor_basis: currentish",
        1,
    )
    assert "invalid_age_anchor_basis" in _company_codes(text)


def test_company_run_boundary_values_are_constrained() -> None:
    text = _valid_company_text().replace(
        "  run_boundary: COMPANY_REPORT_COMPLETE_NO_DOWNSTREAM_EXECUTION",
        "  run_boundary: IMPORTED_TO_COMPANY_SURFACE_AND_RAN_CLASSIFIER",
        1,
    )
    assert "invalid_company_run_boundary" in _company_codes(text)


def test_company_completion_requires_next_authorized_step() -> None:
    text = _valid_company_text().replace(
        "  next_authorized_step: A separately commissioned Scanning or Capture run may address the typed request;"
        " no import or classifier handoff occurred.\n",
        "",
        1,
    )
    assert "missing_company_next_authorized_step" in _company_codes(text)



def test_signal_board_nonclaim_sentence_does_not_mask_later_overclaim() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(
        "Eligible for classifier handoff",
        "Engagement does not prove demand. High engagement proves demand.",
        1,
    )

    findings = validator.validate_text(text)

    assert "engagement_as_proof" in {finding.code for finding in findings}


def test_signal_board_engagement_overclaim_does_not_cross_sentence_boundary() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("Eligible for classifier handoff", "Engagement is high. Our research proves demand.", 1)

    findings = validator.validate_text(text)

    assert findings == []


def test_signal_board_zero_row_board_still_checks_engagement_overclaim() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text, replacements = re.subn(r"(\| Row ID .*?\n\| --- .*?\n)(?:\| SBR-.*?\n)+", r"\1", text, count=1)
    assert replacements == 1
    text = text.replace("relation utility only; graph weight is not signal strength", "High engagement proves demand", 1)

    findings = validator.validate_text(text)

    assert "engagement_as_proof" in {finding.code for finding in findings}

def test_signal_board_allows_engagement_nonclaim_boundary() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(
        "Eligible for classifier handoff",
        "Engagement does not prove demand, graph weight, or Commit/Scale support; eligible for classifier handoff",
        1,
    )

    findings = validator.validate_text(text)

    assert findings == []


@pytest.mark.parametrize(
    ("phrase", "expected_code"),
    [
        ("High engagement proves demand", "engagement_as_proof"),
        ("Demand is proven by high engagement", "engagement_as_proof"),
        ("High engagement sets graph weight", "engagement_graph_weight_shortcut"),
        ("Graph weight is high because of high engagement", "engagement_graph_weight_shortcut"),
        ("High engagement clears Commit/Scale support", "engagement_commit_scale_shortcut"),
        ("Public reaction confirms credibility", "engagement_credibility_shortcut"),
        ("Reaction volume clears Action Ceiling", "engagement_action_ceiling_shortcut"),
        ("This row assigns final resonance weight", "engagement_final_resonance_weight"),
    ],
)
def test_signal_board_flags_engagement_overclaim_classes(phrase: str, expected_code: str) -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("Eligible for classifier handoff", phrase, 1)

    findings = validator.validate_text(text)

    assert expected_code in {finding.code for finding in findings}


@pytest.mark.parametrize(
    ("fixture_name", "expected_code", "expected_row_id"),
    [
        ("bad_engagement_overclaim_output.txt", "engagement_as_proof", ""),
        ("bad_uncertain_cutoff_in_handoff_output.txt", "handoff_row_cutoff_invalid", "SBR-001"),
        ("bad_aeo_future_info_in_handoff_output.txt", "handoff_row_aeo_visibility", "SBR-001"),
        ("bad_to_retrieve_in_handoff_output.txt", "handoff_row_not_source_backed", "SBR-001"),
        ("bad_mixed_case_aeo_handoff_output.txt", "handoff_row_aeo_visibility", "SBR-001"),
        ("bad_missing_handoff_mode_backtest_output.txt", "missing_handoff_mode", ""),
        ("bad_surface_cutoff_uncertain_handoff_output.txt", "handoff_row_surface_cutoff_invalid", "SBR-001"),
        ("bad_forward_excluded_future_info_handoff_output.txt", "handoff_row_future_info", "SBR-001"),
    ],
)
def test_invalid_commission_signal_board_outputs_fail(
    fixture_name: str,
    expected_code: str,
    expected_row_id: str,
) -> None:
    findings = validator.validate_text((FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))
    assert findings
    assert (expected_code, expected_row_id) in {(finding.code, finding.row_id) for finding in findings}


def test_signal_board_requires_recency_columns() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(" | Recency status | Recency attention |", " |", 1)

    findings = validator.validate_text(text)

    assert "missing_required_row_columns" in {finding.code for finding in findings}


def test_signal_board_validates_recency_vocab() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text, replacements = re.subn(
        r"(\| SBR-001 \| forums_community \| Reddit \| public thread \| dated consumer question \| consumer_language \| signal_unit \| )recent \| high( \| node_candidate \|)",
        r"\1too_new | proof\2",
        text,
        count=1,
    )
    assert replacements == 1

    findings = validator.validate_text(text)

    assert ("invalid_recency_status", "SBR-001") in {(finding.code, finding.row_id) for finding in findings}
    assert ("invalid_recency_attention", "SBR-001") in {(finding.code, finding.row_id) for finding in findings}


@pytest.mark.parametrize(
    "header_fragment",
    [" | Row purpose |", " | Graph role |", " | Graph weight hint |"],
)
def test_signal_board_requires_non_recency_shape_columns(header_fragment: str) -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(header_fragment, " |", 1)

    findings = validator.validate_text(text)

    assert "missing_required_row_columns" in {finding.code for finding in findings}


@pytest.mark.parametrize(
    ("valid_fragment", "invalid_fragment", "expected_code"),
    [
        (
            "| consumer_language | signal_unit | recent | high |",
            "| consumer_language | proof_unit | recent | high |",
            "invalid_row_purpose",
        ),
        (
            "| recent | high | node_candidate | medium |",
            "| recent | high | proof_node | medium |",
            "invalid_graph_role",
        ),
        (
            "| high | node_candidate | medium | source_backed |",
            "| high | node_candidate | proof | source_backed |",
            "invalid_graph_weight_hint",
        ),
    ],
)
def test_signal_board_validates_non_recency_vocab(
    valid_fragment: str,
    invalid_fragment: str,
    expected_code: str,
) -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(valid_fragment, invalid_fragment, 1)

    findings = validator.validate_text(text)

    assert (expected_code, "SBR-001") in {(finding.code, finding.row_id) for finding in findings}

def test_unknown_handoff_mode_is_rejected_before_cutoff_bypass() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text, mode_replacements = re.subn(r"(?m)^(\s{2})mode: backtest\s*$", r"\1mode: unknown", text, count=1)
    assert mode_replacements == 1
    text = text.replace(
        "| SBR-001 | forums_community | Reddit | public thread | dated consumer question | consumer_language | signal_unit | recent | high | node_candidate | medium | source_backed | URL and thread date supplied | existed_by_cutoff | in_window | Eligible for classifier handoff |",
        "| SBR-001 | forums_community | Reddit | public thread | dated consumer question | consumer_language | signal_unit | recent | high | node_candidate | medium | source_backed | URL and thread date supplied | existed_by_cutoff | uncertain | Eligible for classifier handoff |",
        1,
    )

    findings = validator.validate_text(text)

    assert "invalid_handoff_mode" in {finding.code for finding in findings}


def test_handoff_row_must_exist_in_signal_board_rows() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text, replacements = re.subn(r"(?m)^(\s*-\s*)SBR-001\s*$", r"\1SBR-999", text, count=1)
    assert replacements == 1

    findings = validator.validate_text(text)

    assert ("handoff_row_unknown", "SBR-999") in {(finding.code, finding.row_id) for finding in findings}


def test_handoff_validation_continues_with_malformed_unreferenced_row() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace(
        "| SBR-001 | forums_community | Reddit | public thread | dated consumer question | consumer_language | signal_unit | recent | high | node_candidate | medium | source_backed | URL and thread date supplied | existed_by_cutoff | in_window | Eligible for classifier handoff |",
        "| SBR-001 | forums_community | Reddit | public thread | dated consumer question | consumer_language | signal_unit | recent | high | node_candidate | medium | source_backed | URL and thread date supplied | existed_by_cutoff | uncertain | Eligible for classifier handoff |",
        1,
    )
    text = text.replace(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| SBR-BAD | malformed | row |",
        1,
    )

    findings = validator.validate_text(text)
    codes = {finding.code for finding in findings}

    assert "malformed_signal_board_row" in codes
    assert ("handoff_row_cutoff_invalid", "SBR-001") in {(finding.code, finding.row_id) for finding in findings}


def test_full_board_requires_sections_one_through_ten_in_order() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text, replacements = re.subn(
        r"(?ms)^### 9\. Visible Limitations\s+.*?(?=^### 10\.)",
        "",
        text,
        count=1,
    )
    assert replacements == 1

    findings = validator.validate_text(text)

    assert "invalid_section_contract" in {finding.code for finding in findings}


def test_row_ids_must_use_sbr_format() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("| SBR-001 | forums_community |", "| ROW-001 | forums_community |", 1)

    findings = validator.validate_text(text)

    assert ("invalid_row_id_format", "ROW-001") in {(finding.code, finding.row_id) for finding in findings}


def test_row_ids_must_be_monotonic() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("| SBR-002 | reviews |", "| SBR-004 | reviews |", 1)

    findings = validator.validate_text(text)

    assert ("non_monotonic_row_id", "SBR-004") in {(finding.code, finding.row_id) for finding in findings}


def test_row_vocab_must_use_prompt_values() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("| SBR-001 | forums_community |", "| SBR-001 | forum-ish |", 1)

    findings = validator.validate_text(text)

    assert ("invalid_source_family", "SBR-001") in {(finding.code, finding.row_id) for finding in findings}


def test_handoff_packet_requires_shape_fields() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("  classifier_mapping_status: classifier_owned\n", "", 1)

    findings = validator.validate_text(text)

    assert "missing_handoff_packet_fields" in {finding.code for finding in findings}
    assert "invalid_classifier_mapping_status" in {finding.code for finding in findings}


def test_board_status_values_are_constrained() -> None:
    text = (FIXTURE_DIR / "valid_source_backed_backtest_output.txt").read_text(encoding="utf-8")
    text = text.replace("board_status: READY_FOR_RETRIEVAL_HANDOFF", "board_status: READY_FOR_DEMAND_VERDICT", 1)
    text = text.replace("run_boundary: CHAT_ONLY_BOARD_COMPLETE", "run_boundary: RAN_CLASSIFIER", 1)

    findings = validator.validate_text(text)
    codes = {finding.code for finding in findings}

    assert "invalid_board_status" in codes
    assert "invalid_run_boundary" in codes


def test_commission_stage_company_board_passes() -> None:
    text = (FIXTURE_DIR / "valid_company_commission_stage_output.txt").read_text(encoding="utf-8")
    assert validator.validate_text(text) == []


@pytest.mark.parametrize(
    ("surface", "expected_code"),
    [
        (
            "google_ads_transparency_center",
            "missing_google_ads_transparency_commission",
        ),
        ("meta_ads_library", "missing_meta_ads_library_commission"),
        (
            "reddit_weekly_data_lake_read",
            "missing_reddit_weekly_lake_commission",
        ),
        (
            "native_social_trigger_assessment",
            "missing_native_social_trigger_assessment",
        ),
        (
            "tiktok_shop_trigger_assessment",
            "missing_tiktok_shop_trigger_assessment",
        ),
    ],
)
def test_commission_stage_requires_enhanced_evidence_routes(
    surface: str, expected_code: str
) -> None:
    text = (
        FIXTURE_DIR / "valid_company_commission_stage_output.txt"
    ).read_text(encoding="utf-8")
    text = text.replace(f"source_surface: {surface}", "source_surface: omitted", 1)

    assert expected_code in _company_codes(text)


def test_commission_stage_requires_top_level_co0_with_three_worker_slots() -> None:
    text = (
        FIXTURE_DIR / "valid_company_commission_stage_output.txt"
    ).read_text(encoding="utf-8")
    text = text.replace(
        "  controller_placement: top_level_co0",
        "  controller_placement: nested_co0",
        1,
    ).replace("  worker_slots_available: 3", "  worker_slots_available: 2", 1)

    codes = _company_codes(text)
    assert "invalid_commission_controller_placement" in codes
    assert "blocked_controller_capacity" in codes


def test_commission_scout_status_requires_commission_boundary() -> None:
    text = _valid_company_text().replace(
        "  quora_scout_status: experimental_checked_zero_yield",
        "  quora_scout_status: commissioned_not_yet_run",
        1,
    )
    assert "commission_scout_status_outside_commission_stage" in _company_codes(text)


def test_bad_commission_scout_fixture_uses_current_company_report_contract() -> None:
    text = (FIXTURE_DIR / "bad_company_commission_scout_status_output.txt").read_text(encoding="utf-8")
    codes = _company_codes(text)
    assert "commission_scout_status_outside_commission_stage" in codes
    assert "invalid_company_section_contract" not in codes
    assert "invalid_portfolio_retail_subsection_contract" not in codes
    assert "invalid_required_lens_coverage" not in codes


def test_commission_boundary_requires_open_coverage() -> None:
    text = _valid_company_text().replace(
        "  run_boundary: COMPANY_REPORT_COMPLETE_NO_DOWNSTREAM_EXECUTION",
        "  run_boundary: COMMISSION_SEALED_PRE_SCAN",
        1,
    )
    assert "commission_stage_without_open_coverage" in _company_codes(text)


def test_company_scout_status_enums_are_constrained() -> None:
    text = _valid_company_text().replace(
        "  reddit_scout_status: checked_zero_yield",
        "  reddit_scout_status: probably_checked_somewhere",
        1,
    )
    assert "invalid_reddit_scout_status" in _company_codes(text)

    text = _valid_company_text().replace(
        "  quora_scout_status: experimental_checked_zero_yield",
        "  quora_scout_status: probably_checked_somewhere",
        1,
    )
    assert "invalid_quora_scout_status" in _company_codes(text)


def test_company_scout_status_fields_are_required() -> None:
    text = _valid_company_text().replace("  reddit_scout_status: checked_zero_yield\n", "", 1)
    text = text.replace("  quora_scout_status: experimental_checked_zero_yield\n", "", 1)
    codes = _company_codes(text)
    assert "invalid_reddit_scout_status" in codes
    assert "invalid_quora_scout_status" in codes


def test_company_scout_statuses_match_coverage_rows() -> None:
    text = (FIXTURE_DIR / "valid_company_commission_stage_output.txt").read_text(encoding="utf-8")
    text = text.replace(
        "    status: checked\n    yield: zero_yield\n    recency: unknown",
        "    status: not_checked\n    yield: unknown\n    recency: unknown",
        1,
    )
    assert "reddit_scout_status_coverage_mismatch" in _company_codes(text)

    text = (FIXTURE_DIR / "valid_company_commission_stage_output.txt").read_text(encoding="utf-8")
    text = text.replace(
        "    status: not_checked\n    yield: unknown\n    recency: unknown\n    access: accessible\n    relevance: mixed",
        "    status: checked\n    yield: evidence_found\n    recency: unknown\n    access: accessible\n    relevance: mixed",
        1,
    )
    assert "quora_scout_status_coverage_mismatch" in _company_codes(text)

    text = _valid_company_text().replace(
        "  reddit_scout_status: checked_zero_yield",
        "  reddit_scout_status: checked_positive_yield",
        1,
    )
    assert "reddit_scout_status_coverage_mismatch" in _company_codes(text)
