"""Raw-preserving Sephora Bazaarvoice companion capture.

This module is intentionally retailer-specific.  It consumes a hash-verified
rendered Sephora PDP packet, reads the API configuration declared by that page,
and captures a bounded ``Most Answers`` Q&A window, exact non-incentivized
review age counts, a non-incentivized ``Most Helpful`` snapshot, and a
source-date-bounded non-incentivized ``Most Recent`` window of at least 30 days.
Network access stays in this acquisition seam; the packet summary is derived
in flight from preserved response bytes.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import parse_qs, unquote, urlparse

from data_lake.root import DataLakeRoot, LoadedRawPacket
from harness_utils import utc_now_z
from source_capture.adapters.cloakbrowser_snapshot import (
    CloakBrowserSnapshotFailure,
    fetch_cloakbrowser_snapshot_capture,
)
from source_capture.adapters.bazaarvoice_api import (
    BAZAARVOICE_API_HOST,
    ApiFetcher,
    ApiRequestSpec,
    ApiResponse,
    BazaarvoiceReadConfig,
    fetch_bazaarvoice_api_response,
)
from source_capture.adapters.sephora_us_market import SephoraUSMarketPlugin
from source_capture.models import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_attempted,
    unknown_with_reason,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map
from source_capture.retail_capture_profiles import get_retail_capture_profile


SEPHORA_ONBOARDING_SOURCE_SURFACE = "sephora_bazaarvoice_onboarding"
SEPHORA_ONBOARDING_PARSER_VERSION = "sephora_bazaarvoice_onboarding_v4"
SEPHORA_AGE_BUCKETS: tuple[str, ...] = ("20s", "30s", "40s", "50s +")
DEFAULT_QUESTION_LIMIT = 100
DEFAULT_REVIEW_PAGE_LIMIT = 100
DEFAULT_RECENT_WINDOW_DAYS = 30


class SephoraOnboardingCaptureError(RuntimeError):
    """Fail-closed acquisition or content-qualification error."""


@dataclass(frozen=True)
class AgeBucketSpec:
    display_label: str
    api_value: str


_AGE_BUCKET_SPECS: tuple[AgeBucketSpec, ...] = (
    AgeBucketSpec("20s", "20s"),
    AgeBucketSpec("30s", "30s"),
    AgeBucketSpec("40s", "40s"),
    AgeBucketSpec("50s +", "50s"),
)

_PROJECTED_REVIEW_SOURCE_FIELDS = frozenset(
    {
        "Id",
        "ProductId",
        "Title",
        "ReviewText",
        "Rating",
        "SubmissionTime",
        "UserNickname",
        "IsRecommended",
        "IsVerifiedBuyer",
        "TotalFeedbackCount",
        "TotalPositiveFeedbackCount",
        "TotalNegativeFeedbackCount",
        "ContextDataValues",
        "AdditionalFields",
        "Badges",
        "Photos",
        "Videos",
        "TagDimensions",
    }
)


@dataclass(frozen=True)
class ParentContext:
    packet_id: str
    file_id: str
    file_sha256: str
    product_id: str
    allowed_product_ids: tuple[str, ...]
    product_url: str
    review_config: BazaarvoiceReadConfig | None
    question_config: BazaarvoiceReadConfig | None
    configuration_receipt: Mapping[str, Any]


@dataclass(frozen=True)
class ParentConfigurationRefresh:
    requested_url: str
    final_url: str
    rendered_dom: str
    rendered_dom_sha256: str
    pin_confirmed: bool


ParentConfigurationRefresher = Callable[
    [str, float], ParentConfigurationRefresh
]


def capture_sephora_onboarding_packet(
    *,
    data_root: DataLakeRoot,
    parent_packet_id: str,
    question_limit: int = DEFAULT_QUESTION_LIMIT,
    review_page_limit: int = DEFAULT_REVIEW_PAGE_LIMIT,
    recent_window_days: int = DEFAULT_RECENT_WINDOW_DAYS,
    timeout_seconds: float = 20.0,
    max_bytes: int = 8_000_000,
    fetcher: ApiFetcher | None = None,
    configuration_refresher: ParentConfigurationRefresher | None = None,
    configuration_source_packet_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """Capture and commit one Sephora review/Q&A companion packet.

    Exit 0 is a content-qualification success. Exit 4 means one or more HTTP responses
    were non-2xx. Exit 5 means raw responses were acquired but summary adaptation failed;
    those raw bytes are still committed with an explicit failure artifact.
    Pre-acquisition parent/config failures raise and write nothing.
    """
    if data_root.readonly:
        raise SephoraOnboardingCaptureError("capture requires a writable DataLakeRoot")
    if not 1 <= question_limit <= 100:
        raise ValueError("question_limit must be between 1 and 100")
    if not 1 <= review_page_limit <= 100:
        raise ValueError("review_page_limit must be between 1 and 100")
    if recent_window_days < 30:
        raise ValueError("recent_window_days must be at least 30")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")

    parent = _parent_context(data_root.load_raw_packet(parent_packet_id), parent_packet_id)
    if parent.review_config is None or parent.question_config is None:
        if configuration_source_packet_id is not None:
            parent = _configuration_from_preserved_packet(
                parent,
                loaded=data_root.load_raw_packet(configuration_source_packet_id),
                packet_id=configuration_source_packet_id,
            )
        else:
            parent = _refresh_parent_configuration(
                parent,
                refresher=configuration_refresher
                or _live_parent_configuration_refresh,
                timeout_seconds=timeout_seconds,
            )
    assert parent.review_config is not None
    assert parent.question_config is not None
    request_specs = list(
        _base_request_specs(parent.product_id, question_limit, review_page_limit)
    )
    api_fetcher = fetcher or fetch_bazaarvoice_api_response
    captured: list[tuple[ApiRequestSpec, ApiResponse]] = []
    acquisition_failure: dict[str, Any] | None = None

    for spec in request_specs:
        config = parent.question_config if spec.config_kind == "questions" else parent.review_config
        try:
            response = api_fetcher(spec, config, timeout_seconds, max_bytes)
        except Exception as exc:  # acquisition failure must be recorded without secret URLs
            acquisition_failure = {
                "artifact_name": spec.artifact_name,
                "error_type": type(exc).__name__,
                "error": _safe_error_text(exc),
            }
            break
        if config.token.encode("utf-8") in response.body:
            raise SephoraOnboardingCaptureError(
                f"{spec.artifact_name} response echoed the page-declared read token; "
                "refusing to persist secret-bearing bytes"
            )
        captured.append((spec, response))
        if not 200 <= response.status < 300:
            acquisition_failure = {
                "artifact_name": spec.artifact_name,
                "http_status": response.status,
                "reason": response.reason,
            }
            break

    if acquisition_failure is None:
        recent_offset = 0
        recent_cutoff: datetime | None = None
        while True:
            spec = _recent_request_spec(
                parent.product_id,
                review_page_limit,
                recent_offset,
            )
            request_specs.append(spec)
            try:
                response = api_fetcher(
                    spec,
                    parent.review_config,
                    timeout_seconds,
                    max_bytes,
                )
            except Exception as exc:
                acquisition_failure = {
                    "artifact_name": spec.artifact_name,
                    "error_type": type(exc).__name__,
                    "error": _safe_error_text(exc),
                }
                break
            if parent.review_config.token.encode("utf-8") in response.body:
                raise SephoraOnboardingCaptureError(
                    f"{spec.artifact_name} response echoed the page-declared read token; "
                    "refusing to persist secret-bearing bytes"
                )
            captured.append((spec, response))
            if not 200 <= response.status < 300:
                acquisition_failure = {
                    "artifact_name": spec.artifact_name,
                    "http_status": response.status,
                    "reason": response.reason,
                }
                break
            try:
                page = _recent_page_state(
                    response.body,
                    spec.artifact_name,
                    parent.allowed_product_ids,
                )
                if recent_cutoff is None:
                    recent_cutoff = _parse_timestamp(
                        response.captured_at,
                        f"{spec.artifact_name} captured_at",
                    ) - timedelta(days=recent_window_days)
            except SephoraOnboardingCaptureError:
                # The exact response is already preserved. Projection will fail
                # closed and emit the raw fallback rather than guessing how to
                # continue an unparseable or identity-ambiguous page.
                break
            next_offset = recent_offset + page["row_count"]
            if (
                page["oldest_submission_time"] <= recent_cutoff
                or next_offset >= page["total_results"]
                or page["row_count"] == 0
                or next_offset <= recent_offset
            ):
                break
            recent_offset = next_offset

    request_manifest = _request_manifest(parent, request_specs, captured)
    artifacts: list[tuple[str, bytes]] = [
        (spec.artifact_name, response.body) for spec, response in captured
    ]
    artifacts.append(
        (
            "sephora_request_manifest.json",
            _json_bytes(request_manifest),
        )
    )

    limitations: list[str] = []
    exit_code = 0
    if acquisition_failure is not None:
        exit_code = 4
        limitations.append(
            "structured API acquisition did not complete; every response body acquired "
            "before the failure is preserved and no successful summary is claimed"
        )
        summary: dict[str, Any] = {
            "record_kind": "sephora_bazaarvoice_onboarding_capture_failure_v4",
            "parser_version": SEPHORA_ONBOARDING_PARSER_VERSION,
            "parent_packet_id": parent.packet_id,
            "product_id": parent.product_id,
            "failure": acquisition_failure,
            "raw_failure_fallback": {
                "status": "preserved_partial_responses",
                "preserved_response_count": len(captured),
                "expected_response_count": len(request_specs),
            },
        }
        artifacts.append(("sephora_capture_failure.json", _json_bytes(summary)))
    else:
        try:
            summary = build_sephora_onboarding_summary(
                parent=parent,
                captured_responses=captured,
                question_limit=question_limit,
                review_page_limit=review_page_limit,
                recent_window_days=recent_window_days,
            )
            limitations.extend(entry["detail"] for entry in summary["loss_ledger"])
            artifacts.append(("sephora_onboarding_summary.json", _json_bytes(summary)))
        except Exception as exc:
            exit_code = 5
            limitations.append(
                "onboarding summary adaptation failed after acquisition; all exact raw API "
                "response bytes are preserved as the required raw fallback"
            )
            summary = {
                "record_kind": "sephora_bazaarvoice_onboarding_adaptation_failure_v4",
                "parser_version": SEPHORA_ONBOARDING_PARSER_VERSION,
                "parent_packet_id": parent.packet_id,
                "product_id": parent.product_id,
                "failure": {
                    "error_type": type(exc).__name__,
                    "error": _safe_error_text(exc),
                },
                "raw_failure_fallback": {
                    "status": "all_responses_preserved",
                    "preserved_response_count": len(captured),
                    "expected_response_count": len(request_specs),
                },
            }
            artifacts.append(("sephora_adaptation_failure.json", _json_bytes(summary)))

    written = _write_packet(
        data_root=data_root,
        parent=parent,
        artifacts=artifacts,
        captured=captured,
        limitations=limitations,
        summary=summary,
    )
    return exit_code, {
        "packet_id": written.packet.packet_id,
        "output_directory": written.output_directory,
        "summary": summary,
    }


def build_sephora_onboarding_summary(
    *,
    parent: ParentContext,
    captured_responses: Sequence[tuple[ApiRequestSpec, ApiResponse]],
    question_limit: int,
    review_page_limit: int = DEFAULT_REVIEW_PAGE_LIMIT,
    recent_window_days: int = DEFAULT_RECENT_WINDOW_DAYS,
) -> dict[str, Any]:
    """Build a capture summary exclusively from preserved response bytes."""
    by_name = {
        spec.artifact_name: _load_api_document(response.body, spec.artifact_name)
        for spec, response in captured_responses
    }
    expected_base_names = {
        spec.artifact_name
        for spec in _base_request_specs(
            parent.product_id,
            question_limit,
            review_page_limit,
        )
    }
    recent_pairs = [
        (spec, response)
        for spec, response in captured_responses
        if spec.artifact_name.startswith(
            "reviews_non_incentivized_most_recent_offset_"
        )
    ]
    if not expected_base_names.issubset(by_name) or not recent_pairs:
        raise SephoraOnboardingCaptureError(
            "summary adaptation requires the complete declared response set"
        )
    if set(by_name) != expected_base_names | {
        spec.artifact_name for spec, _response in recent_pairs
    }:
        raise SephoraOnboardingCaptureError(
            "summary adaptation received an undeclared Sephora response artifact"
        )

    questions_doc = by_name["questions_most_answers_offset_000.json"]
    question_rows = _require_list(questions_doc, "Results", "questions")
    question_total = _require_nonnegative_int(questions_doc, "TotalResults", "questions")
    if question_total == 0 and question_rows:
        raise SephoraOnboardingCaptureError(
            "questions response declares zero TotalResults but returned rows"
        )
    _validate_result_product_ids(
        question_rows,
        allowed_product_ids=(parent.product_id,),
        label="questions",
        allow_empty=question_total == 0,
        allow_provider_collection_product_ids=True,
    )
    includes = questions_doc.get("Includes", questions_doc.get("Included", {}))
    if not isinstance(includes, Mapping):
        raise SephoraOnboardingCaptureError("questions Includes must be an object")
    raw_answers = includes.get("Answers", {})
    if isinstance(raw_answers, Mapping):
        included_answers = list(raw_answers.values())
    elif isinstance(raw_answers, list):
        included_answers = raw_answers
    else:
        raise SephoraOnboardingCaptureError("questions Includes.Answers must be an object or list")
    if any(not isinstance(answer, Mapping) for answer in included_answers):
        raise SephoraOnboardingCaptureError("questions included answer rows must be objects")

    question_inventory: list[dict[str, Any]] = []
    answer_count_sum = 0
    for index, raw_row in enumerate(question_rows):
        if not isinstance(raw_row, Mapping):
            raise SephoraOnboardingCaptureError(f"question row {index} must be an object")
        answer_count = _mapping_nonnegative_int(raw_row, "TotalAnswerCount", f"question row {index}")
        answer_count_sum += answer_count
        question_summary = _optional_string(raw_row.get("QuestionSummary"))
        question_details = _optional_string(raw_row.get("QuestionDetails"))
        if question_summary is None and question_details is None:
            raise SephoraOnboardingCaptureError(
                f"question row {index} has neither QuestionSummary nor QuestionDetails"
            )
        question_inventory.append(
            {
                "rank": index + 1,
                "question_id": _optional_string(raw_row.get("Id")),
                "product_id": _required_string(
                    raw_row.get("ProductId"),
                    f"question row {index}.ProductId",
                ),
                "question_summary_present": question_summary is not None,
                "question_details_present": question_details is not None,
                "total_answer_count": answer_count,
                "submission_time": _optional_string(raw_row.get("SubmissionTime")),
                "nickname_present": _optional_string(raw_row.get("UserNickname"))
                is not None,
            }
        )

    helpful_doc = by_name["reviews_non_incentivized_most_helpful_offset_000.json"]
    helpful_rows = _require_list(
        helpful_doc,
        "Results",
        "non-incentivized Most Helpful reviews",
    )
    helpful_total = _total_results(
        helpful_doc,
        "non-incentivized Most Helpful reviews",
    )
    _validate_result_product_ids(
        helpful_rows,
        allowed_product_ids=parent.allowed_product_ids,
        label="non-incentivized Most Helpful reviews",
        allow_empty=helpful_total == 0,
        allow_provider_collection_product_ids=True,
    )
    if helpful_total == 0:
        if helpful_rows:
            raise SephoraOnboardingCaptureError(
                "Most Helpful response declares zero TotalResults but returned rows"
            )
        review_statistics: Mapping[str, Any] = {}
        filtered_statistics: Mapping[str, Any] = {}
        non_incentivized_total = 0
        age_distribution = None
        skin_type_distribution = None
        skin_concern_distribution = None
    else:
        review_statistics, filtered_statistics = _helpful_statistics(
            helpful_doc, parent.product_id
        )
        non_incentivized_total = _mapping_nonnegative_int(
            filtered_statistics,
            "TotalReviewCount",
            "FilteredReviewStatistics",
        )
        age_distribution = _context_distribution(
            filtered_statistics, "ageRange"
        )
        skin_type_distribution = _context_distribution(
            filtered_statistics, "skinType"
        )
        skin_concern_distribution = _context_distribution(
            filtered_statistics, "skinConcerns"
        )
    age_counts: dict[str, int] = {}
    api_label_by_value = {
        bucket.api_value: bucket.display_label for bucket in _AGE_BUCKET_SPECS
    }
    for entry in age_distribution or []:
        display = api_label_by_value.get(entry["value"], entry["value"])
        age_counts[display] = age_counts.get(display, 0) + entry["count"]
    declared_age_total = sum(age_counts.values())
    if declared_age_total > non_incentivized_total:
        raise SephoraOnboardingCaptureError(
            "sum of filtered age-distribution counts exceeds the "
            "non-incentivized review total"
        )
    age_breakdown = [
        {
            "bucket": display,
            "count": count,
            "share_of_declared_age_subset_pct": _percentage(
                count, declared_age_total
            ),
            "share_of_all_non_incentivized_reviews_pct": _percentage(
                count, non_incentivized_total
            ),
        }
        for display, count in age_counts.items()
    ]
    helpful_inventory = [
        _review_inventory_row(row, rank=index + 1)
        for index, row in enumerate(helpful_rows)
    ]

    recent_rows: list[Mapping[str, Any]] = []
    recent_page_receipts: list[dict[str, Any]] = []
    expected_offset = 0
    recent_total: int | None = None
    recent_capture_time: datetime | None = None
    for spec, response in recent_pairs:
        offset = _recent_offset(spec.artifact_name)
        if offset != expected_offset:
            raise SephoraOnboardingCaptureError(
                "Most Recent response offsets are not contiguous"
            )
        state = _recent_page_state(
            response.body,
            spec.artifact_name,
            parent.allowed_product_ids,
        )
        if recent_total is None:
            recent_total = state["total_results"]
            recent_capture_time = _parse_timestamp(
                response.captured_at,
                f"{spec.artifact_name} captured_at",
            )
        elif state["total_results"] != recent_total:
            raise SephoraOnboardingCaptureError(
                "Most Recent TotalResults changed during pagination"
            )
        page_rows = _require_list(
            by_name[spec.artifact_name],
            "Results",
            spec.artifact_name,
        )
        recent_rows.extend(page_rows)
        recent_page_receipts.append(
            {
                "artifact_name": spec.artifact_name,
                "offset": offset,
                "row_count": state["row_count"],
                "oldest_submission_time": (
                    _format_timestamp(state["oldest_submission_time"])
                    if state["row_count"]
                    else None
                ),
                "newest_submission_time": _format_timestamp(
                    state["newest_submission_time"]
                ),
                "source_exhausted": state["exhausted"],
            }
        )
        expected_offset += state["row_count"]

    assert recent_total is not None
    assert recent_capture_time is not None
    recent_cutoff = recent_capture_time - timedelta(days=recent_window_days)
    recent_dates = [
        _parse_timestamp(
            _required_string(
                row.get("SubmissionTime"),
                f"Most Recent row {index}.SubmissionTime",
            ),
            f"Most Recent row {index}.SubmissionTime",
        )
        for index, row in enumerate(recent_rows)
    ]
    if recent_dates != sorted(recent_dates, reverse=True):
        raise SephoraOnboardingCaptureError(
            "Most Recent rows are not in non-increasing SubmissionTime order"
        )
    recent_exhausted = len(recent_rows) >= recent_total
    recent_cutoff_reached = bool(recent_dates) and min(recent_dates) <= recent_cutoff
    if not recent_exhausted and not recent_cutoff_reached:
        raise SephoraOnboardingCaptureError(
            "Most Recent pagination ended before 30-day coverage or source exhaustion"
        )
    recent_inventory = [
        _review_inventory_row(row, rank=index + 1)
        for index, row in enumerate(recent_rows)
    ]
    within_window_inventory = [
        inventory
        for inventory, submission_time in zip(
            recent_inventory,
            recent_dates,
            strict=True,
        )
        if submission_time >= recent_cutoff
    ]
    helpful_fields = _review_field_inventory(helpful_rows)
    recent_fields = _review_field_inventory(recent_rows)
    observed_review_product_ids = sorted(
        {row["product_id"] for row in helpful_inventory + recent_inventory}
    )
    observed_question_product_ids = sorted(
        {row["product_id"] for row in question_inventory}
    )
    provider_collection_product_ids = sorted(
        set(observed_question_product_ids) | set(observed_review_product_ids)
    )
    historical_review_product_ids = sorted(
        set(observed_review_product_ids) - set(parent.allowed_product_ids)
    )
    historical_review_row_count = sum(
        row["product_id"] in historical_review_product_ids
        for row in helpful_inventory + recent_inventory
    )
    additional_review_fields = sorted(
        (helpful_fields | recent_fields) - _PROJECTED_REVIEW_SOURCE_FIELDS
    )
    questions_not_captured = max(question_total - len(question_rows), 0)
    answers_not_included = max(answer_count_sum - len(included_answers), 0)
    reviews_without_live_age_bucket = non_incentivized_total - declared_age_total

    loss_ledger = [
        {
            "field": "questions_beyond_bounded_window",
            "count": questions_not_captured,
            "detail": (
                f"Most Answers capture preserves {len(question_rows)} of {question_total} "
                f"questions; {questions_not_captured} lower-ranked questions remain outside "
                "this bounded onboarding packet"
            ),
        },
        {
            "field": "answers_not_returned_in_includes",
            "count": answers_not_included,
            "detail": (
                f"captured question rows declare {answer_count_sum} answers and the response "
                f"Includes block preserves {len(included_answers)}; difference={answers_not_included}"
            ),
        },
        {
            "field": "non_incentivized_reviews_without_declared_age",
            "count": reviews_without_live_age_bucket,
            "detail": (
                f"{reviews_without_live_age_bucket} of {non_incentivized_total} exact "
                "non-incentivized reviews declare no age in the filtered context "
                "distribution; the demographic composition is not a percentage of "
                "all reviewers"
            ),
        },
        {
            "field": "statistics_not_promoted_into_summary",
            "count": 0,
            "detail": (
                "review statistics beyond the promoted aggregates and the age, "
                "skin-type, and skin-concern distributions remain only in the raw "
                "Most Helpful response"
            ),
        },
        {
            "field": "most_helpful_reviews_beyond_snapshot",
            "count": max(helpful_total - len(helpful_rows), 0),
            "detail": (
                f"Most Helpful preserves {len(helpful_rows)} source-ordered "
                f"non-incentivized reviews of {helpful_total}; the remainder stays "
                "outside this bounded snapshot"
            ),
        },
        {
            "field": "review_bodies_and_full_fields_preserved_only_in_raw",
            "count": len(additional_review_fields),
            "fields": additional_review_fields,
            "detail": (
                "summary rows are compact and body-free; every raw review field "
                "name is inventoried here and its exact values remain only in the "
                "preserved raw responses"
            ),
        },
        {
            "field": "provider_returned_collection_product_ids",
            "count": len(provider_collection_product_ids),
            "product_ids": provider_collection_product_ids,
            "detail": (
                "the exact parent-product filters returned this provider-defined "
                "product-ID union across Q&A and review roles; the union is preserved "
                "as observed collection evidence, not promoted to a permanent tenant, "
                "syndication, or catalog identity"
            ),
        },
        {
            "field": "review_product_ids_not_in_current_parent_sku_set",
            "count": historical_review_row_count,
            "product_ids": historical_review_product_ids,
            "detail": (
                "the exact product-group filter returned review rows bound to these "
                "historical or no-longer-current SKU identifiers; rows remain captured "
                "and are not misclassified as current variants"
            ),
        },
    ]

    return {
        "record_kind": "sephora_bazaarvoice_onboarding_summary_v4",
        "parser_version": SEPHORA_ONBOARDING_PARSER_VERSION,
        "parent_packet": {
            "packet_id": parent.packet_id,
            "file_id": parent.file_id,
            "file_sha256": parent.file_sha256,
            "configuration": dict(parent.configuration_receipt),
        },
        "product": {
            "product_id": parent.product_id,
            "allowed_product_and_sku_ids": list(parent.allowed_product_ids),
            "product_url": parent.product_url,
        },
        "questions": {
            "sort": "TotalAnswerCount:desc",
            "offset": 0,
            "requested_limit": question_limit,
            "total_questions": question_total,
            "captured_question_rows": len(question_rows),
            "captured_included_answer_rows": len(included_answers),
            "captured_question_declared_answer_sum": answer_count_sum,
            "question_product_identity": {
                "requested_product_group_id": parent.product_id,
                "observed_question_product_ids": observed_question_product_ids,
                "provider_collection_product_ids": provider_collection_product_ids,
            },
            "question_inventory": question_inventory,
        },
        "reviews": {
            "filter": "ContextDataValue_IncentivizedReview:eq:False",
            "exact_non_incentivized_total": non_incentivized_total,
            "statistics": {
                "raw_file": "reviews_non_incentivized_most_helpful_offset_000.json",
                "filtered": _promoted_statistics(filtered_statistics),
                "unfiltered": _promoted_statistics(review_statistics),
            },
            "demographics": {
                "source": (
                    "FilteredReviewStatistics.ContextDataDistribution of the "
                    "combined Most Helpful response"
                    if helpful_total > 0
                    else "not_applicable_source_declared_zero_reviews"
                ),
                "age_display_labels": list(SEPHORA_AGE_BUCKETS),
                "declared_age_subset_total": declared_age_total,
                "declared_age_coverage_pct": _percentage(
                    declared_age_total, non_incentivized_total
                ),
                "without_declared_age_count": reviews_without_live_age_bucket,
                "without_declared_age_pct": _percentage(
                    reviews_without_live_age_bucket, non_incentivized_total
                ),
                "age_breakdown": age_breakdown,
                "skin_type_distribution": skin_type_distribution,
                "skin_concern_distribution": skin_concern_distribution,
            },
            "most_helpful": {
                "sort": "TotalPositiveFeedbackCount:desc",
                "offset": 0,
                "requested_limit": review_page_limit,
                "total_filtered_reviews": helpful_total,
                "captured_review_rows": len(helpful_rows),
                "captured_review_bodies": sum(
                    row["body_present"] for row in helpful_inventory
                ),
                "review_inventory": helpful_inventory,
            },
            "most_recent_30d": {
                "sort": "SubmissionTime:desc",
                "window_days": recent_window_days,
                "cutoff_inclusive": _format_timestamp(recent_cutoff),
                "total_filtered_reviews": recent_total,
                "last_seen_review_id": (
                    recent_inventory[0]["review_id"] if recent_inventory else None
                ),
                "captured_page_count": len(recent_page_receipts),
                "captured_page_rows": len(recent_rows),
                "captured_page_review_bodies": sum(
                    row["body_present"] for row in recent_inventory
                ),
                "within_window_rows": len(within_window_inventory),
                "within_window_review_bodies": sum(
                    row["body_present"] for row in within_window_inventory
                ),
                "newest_source_date": (
                    _format_timestamp(max(recent_dates)) if recent_dates else None
                ),
                "oldest_source_date": (
                    _format_timestamp(min(recent_dates)) if recent_dates else None
                ),
                "cutoff_reached": recent_cutoff_reached,
                "source_exhausted": recent_exhausted,
                "coverage_status": (
                    "source_exhausted"
                    if recent_exhausted and not recent_cutoff_reached
                    else "covered_through_cutoff"
                ),
                "pages": recent_page_receipts,
                "captured_page_review_inventory": recent_inventory,
                "within_window_review_inventory": within_window_inventory,
            },
            "raw_review_field_inventory": {
                "most_helpful_fields": sorted(helpful_fields),
                "most_recent_fields": sorted(recent_fields),
                "additional_source_fields_carried": additional_review_fields,
                "fields_preserved_only_in_raw": additional_review_fields,
            },
            "review_product_identity": {
                "requested_product_group_id": parent.product_id,
                "current_parent_product_and_sku_ids": list(parent.allowed_product_ids),
                "observed_review_product_ids": observed_review_product_ids,
                "historical_or_unlisted_review_product_ids": historical_review_product_ids,
                "historical_or_unlisted_review_rows": historical_review_row_count,
                "provider_collection_product_ids": provider_collection_product_ids,
            },
        },
        "content_qualification": {
            "status": "passed",
            "response_documents": len(by_name),
            "three_response_roles_present": True,
            "combined_statistics_present": helpful_total > 0,
            "combined_statistics_status": (
                "present"
                if helpful_total > 0
                else "not_applicable_source_declared_zero_reviews"
            ),
            "age_bucket_vocabulary_exact": (
                sorted(age_counts) == sorted(SEPHORA_AGE_BUCKETS)
                if helpful_total > 0
                else None
            ),
            "age_bucket_vocabulary_status": (
                "observed"
                if helpful_total > 0
                else "not_applicable_source_declared_zero_reviews"
            ),
            "recent_window_coverage_proven": recent_exhausted
            or recent_cutoff_reached,
            "summary_duplicates_review_or_answer_bodies": False,
        },
        "row_accounting": {
            "question_rows_raw": len(question_rows),
            "question_rows_summarized": len(question_inventory),
            "question_rows_equal": len(question_rows) == len(question_inventory),
            "answer_count_declared_by_captured_questions": answer_count_sum,
            "answer_rows_preserved_in_raw_includes": len(included_answers),
            "answers_equal": answer_count_sum == len(included_answers),
            "age_counts_source": (
                "FilteredReviewStatistics.ContextDataDistribution.ageRange of the "
                "combined Most Helpful response"
            ),
            "most_helpful_raw_rows": len(helpful_rows),
            "most_helpful_summarized_rows": len(helpful_inventory),
            "most_helpful_row_order_equal": _review_ids(helpful_rows)
            == [row["review_id"] for row in helpful_inventory],
            "most_recent_raw_rows": len(recent_rows),
            "most_recent_summarized_rows": len(recent_inventory),
            "most_recent_row_order_equal": _review_ids(recent_rows)
            == [row["review_id"] for row in recent_inventory],
            "all_raw_review_field_names_inventoried": True,
        },
        "raw_failure_fallback": {
            "status": "armed",
            "behavior": (
                "if summary adaptation raises after acquisition, commit every acquired raw response "
                "plus sephora_adaptation_failure.json and return exit 5"
            ),
        },
        "loss_ledger": loss_ledger,
    }


def _parent_context(loaded: LoadedRawPacket, packet_id: str) -> ParentContext:
    manifest = loaded.manifest
    if manifest.get("source_family") != "retail_pdp":
        raise SephoraOnboardingCaptureError(
            f"parent packet {packet_id} is not source_family=retail_pdp"
        )
    locator = manifest.get("source_locator")
    product_url = (
        str(locator.get("value"))
        if isinstance(locator, Mapping) and locator.get("status") == "known"
        else ""
    )
    product_id_from_url = _product_id_from_url(product_url)

    candidates: list[tuple[str, bytes]] = []
    for file_id, body in loaded.bodies.items():
        if b'id="linkStore"' in body and b"Sephora.configurationSettings" in body:
            candidates.append((file_id, body))
    if len(candidates) > 1:
        raise SephoraOnboardingCaptureError(
            f"parent packet {packet_id} requires exactly one rendered DOM with "
            "linkStore and Sephora.configurationSettings"
        )
    if not candidates:
        return _content_parent_context(
            loaded=loaded,
            packet_id=packet_id,
            product_url=product_url,
            product_id_from_url=product_id_from_url,
        )

    file_id, body = candidates[0]
    text = body.decode("utf-8", errors="replace")
    product = _link_store_product(text)
    product_id = _required_string(product.get("productId"), "linkStore.page.product.productId")
    if product_id != product_id_from_url:
        raise SephoraOnboardingCaptureError(
            f"parent product mismatch: URL={product_id_from_url}, linkStore={product_id}"
        )
    parent_file_sha256 = _preserved_file_sha256(manifest, file_id)
    allowed_product_ids = _sephora_product_and_sku_ids(product)
    return ParentContext(
        packet_id=packet_id,
        file_id=file_id,
        file_sha256=parent_file_sha256,
        product_id=product_id,
        allowed_product_ids=allowed_product_ids,
        product_url=product_url,
        review_config=_read_config(text, "bvApi_rwdRating_desktop_read"),
        question_config=_read_config(text, "bvApi_rwdQandA_desktop_read"),
        configuration_receipt={
            "mode": "preserved_rendered_dom",
            "parent_file_id": file_id,
            "parent_file_sha256": parent_file_sha256,
        },
    )


def _content_parent_context(
    *,
    loaded: LoadedRawPacket,
    packet_id: str,
    product_url: str,
    product_id_from_url: str,
) -> ParentContext:
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    for file_id, body in loaded.bodies.items():
        try:
            document = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(document, Mapping)
            and document.get("record_kind") == "retail_pdp_sephora_aggregate_content"
            and document.get("schema_version")
            == "retail_pdp_sephora_aggregate_content_v4"
        ):
            candidates.append((file_id, document))
    if len(candidates) != 1:
        raise SephoraOnboardingCaptureError(
            f"parent packet {packet_id} requires exactly one rendered DOM with "
            "linkStore and Sephora.configurationSettings or one canonical "
            "retail_pdp_sephora_aggregate_content_v4 record"
        )

    file_id, document = candidates[0]
    content_source_url = document.get("source_url")
    if not isinstance(content_source_url, str):
        raise SephoraOnboardingCaptureError("Sephora content parent source_url is unavailable")
    content_product_id = _product_id_from_url(content_source_url)
    if content_product_id != product_id_from_url:
        raise SephoraOnboardingCaptureError(
            "content parent product mismatch: "
            f"manifest={product_id_from_url}, content={content_product_id}"
        )

    allowed_ids: list[str] = [product_id_from_url]
    matching_variant = False
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise SephoraOnboardingCaptureError("Sephora content parent rows are unavailable")
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        fields = row.get("source_visible_fields")
        if not isinstance(fields, Mapping):
            continue
        row_product_id = fields.get("product_id")
        if row_product_id == product_id_from_url:
            matching_variant = True
        sku = fields.get("sku")
        if isinstance(sku, str) and sku.strip():
            allowed_ids.append(sku.strip())
    if not matching_variant:
        raise SephoraOnboardingCaptureError(
            "Sephora content parent has no variant bound to the requested product"
        )

    parent_file_sha256 = _preserved_file_sha256(loaded.manifest, file_id)
    market_receipt = _content_parent_market_receipt(loaded, packet_id)
    return ParentContext(
        packet_id=packet_id,
        file_id=file_id,
        file_sha256=parent_file_sha256,
        product_id=product_id_from_url,
        allowed_product_ids=tuple(dict.fromkeys(allowed_ids)),
        product_url=product_url,
        review_config=None,
        question_config=None,
        configuration_receipt={
            "mode": "live_target_bound_refresh_required",
            "content_parent_file_id": file_id,
            "content_parent_file_sha256": parent_file_sha256,
            **market_receipt,
        },
    )


def _content_parent_market_receipt(
    loaded: LoadedRawPacket,
    packet_id: str,
) -> dict[str, Any]:
    candidates: list[str] = []
    for file_id, body in loaded.bodies.items():
        try:
            document = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(document, Mapping)
            and document.get("pin_confirmed") is True
            and document.get("country_code_requested") == "US"
            and document.get("currency_code_requested") == "USD"
            and document.get("access_blocked") is False
        ):
            candidates.append(file_id)
    if len(candidates) != 1:
        raise SephoraOnboardingCaptureError(
            f"content parent {packet_id} requires exactly one preserved successful "
            "US/USD capture metadata record"
        )
    file_id = candidates[0]
    return {
        "content_parent_market_metadata_file_id": file_id,
        "content_parent_market_metadata_sha256": _preserved_file_sha256(
            loaded.manifest, file_id
        ),
        "content_parent_market": "US/USD",
    }


def _preserved_file_sha256(manifest: Mapping[str, Any], file_id: str) -> str:
    preserved = next(
        (
            item
            for item in manifest.get("preserved_files", [])
            if isinstance(item, Mapping) and item.get("file_id") == file_id
        ),
        None,
    )
    if not isinstance(preserved, Mapping) or not isinstance(preserved.get("sha256"), str):
        raise SephoraOnboardingCaptureError("parent preserved-file hash is unavailable")
    return str(preserved["sha256"])


def _refresh_parent_configuration(
    parent: ParentContext,
    *,
    refresher: ParentConfigurationRefresher,
    timeout_seconds: float,
) -> ParentContext:
    refresh = refresher(parent.product_url, timeout_seconds)
    if refresh.requested_url != parent.product_url:
        raise SephoraOnboardingCaptureError(
            "configuration refresh requested a different parent URL"
        )
    if not refresh.pin_confirmed:
        raise SephoraOnboardingCaptureError(
            "configuration refresh did not confirm the Sephora US/USD PDP route"
        )
    final_product_id = _product_id_from_url(refresh.final_url)
    if final_product_id != parent.product_id:
        raise SephoraOnboardingCaptureError(
            "configuration refresh product mismatch: "
            f"parent={parent.product_id}, final={final_product_id}"
        )
    product = _link_store_product(refresh.rendered_dom)
    refreshed_product_id = _required_string(
        product.get("productId"), "linkStore.page.product.productId"
    )
    if refreshed_product_id != parent.product_id:
        raise SephoraOnboardingCaptureError(
            "configuration refresh product mismatch: "
            f"parent={parent.product_id}, linkStore={refreshed_product_id}"
        )
    return replace(
        parent,
        allowed_product_ids=_sephora_product_and_sku_ids(product),
        review_config=_read_config(
            refresh.rendered_dom, "bvApi_rwdRating_desktop_read"
        ),
        question_config=_read_config(
            refresh.rendered_dom, "bvApi_rwdQandA_desktop_read"
        ),
        configuration_receipt={
            **dict(parent.configuration_receipt),
            "mode": "live_target_bound_refresh",
            "requested_url": refresh.requested_url,
            "final_url": refresh.final_url,
            "rendered_dom_sha256": refresh.rendered_dom_sha256,
            "pin_confirmed": refresh.pin_confirmed,
            "credential_posture": (
                "page-declared read tokens used only in memory and not persisted"
            ),
        },
    )


def _configuration_from_preserved_packet(
    parent: ParentContext,
    *,
    loaded: LoadedRawPacket,
    packet_id: str,
) -> ParentContext:
    manifest = loaded.manifest
    source_locator = manifest.get("source_locator")
    source_url = (
        source_locator.get("value")
        if isinstance(source_locator, Mapping)
        and source_locator.get("status") == "known"
        else None
    )
    if not isinstance(source_url, str):
        raise SephoraOnboardingCaptureError(
            f"configuration source packet {packet_id} has no known source locator"
        )
    parsed = urlparse(source_url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower()
        not in {"sephora.com", "www.sephora.com"}
        or not any(
            value.lower() == "us"
            for value in parse_qs(parsed.query).get("country_switch", [])
        )
    ):
        raise SephoraOnboardingCaptureError(
            f"configuration source packet {packet_id} is not a Sephora US route"
        )

    candidates: list[tuple[str, str]] = []
    for file_id, body in loaded.bodies.items():
        if (
            b"bvApi_rwdRating_desktop_read" in body
            and b"bvApi_rwdQandA_desktop_read" in body
            and b"Sephora.configurationSettings" in body
        ):
            candidates.append((file_id, body.decode("utf-8", errors="replace")))
    if len(candidates) != 1:
        raise SephoraOnboardingCaptureError(
            f"configuration source packet {packet_id} requires exactly one "
            "preserved rendered DOM with both Bazaarvoice read configurations"
        )
    file_id, rendered_dom = candidates[0]
    pin_receipt = _configuration_source_pin_receipt(loaded, packet_id)
    return replace(
        parent,
        review_config=_read_config(
            rendered_dom, "bvApi_rwdRating_desktop_read"
        ),
        question_config=_read_config(
            rendered_dom, "bvApi_rwdQandA_desktop_read"
        ),
        configuration_receipt={
            **dict(parent.configuration_receipt),
            "mode": "preserved_sephora_configuration_source",
            "configuration_source_packet_id": packet_id,
            "configuration_source_file_id": file_id,
            "configuration_source_file_sha256": _preserved_file_sha256(
                manifest, file_id
            ),
            "configuration_source_url": source_url,
            **pin_receipt,
            "configuration_scope": "tenant_read_configuration_only",
            "target_binding": (
                "hash-verified canonical content parent product ID plus exact "
                "Bazaarvoice ProductId filter"
            ),
            "credential_posture": (
                "page-declared read tokens used only in memory and not persisted"
            ),
        },
    )


def _configuration_source_pin_receipt(
    loaded: LoadedRawPacket,
    packet_id: str,
) -> dict[str, Any]:
    candidates: list[str] = []
    for file_id, body in loaded.bodies.items():
        try:
            document = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(document, Mapping)
            and document.get("pin_confirmed") is True
            and document.get("country_code_requested") == "US"
            and document.get("access_blocked") is False
        ):
            candidates.append(file_id)
    if len(candidates) != 1:
        raise SephoraOnboardingCaptureError(
            f"configuration source packet {packet_id} requires exactly one "
            "preserved successful Sephora US capture metadata record"
        )
    file_id = candidates[0]
    return {
        "configuration_source_market_metadata_file_id": file_id,
        "configuration_source_market_metadata_sha256": _preserved_file_sha256(
            loaded.manifest, file_id
        ),
        "configuration_source_market": "US",
    }


def _live_parent_configuration_refresh(
    product_url: str,
    timeout_seconds: float,
) -> ParentConfigurationRefresh:
    profile = get_retail_capture_profile("sephora_pdp_aggregate")
    capture = fetch_cloakbrowser_snapshot_capture(
        url=product_url,
        timeout_seconds=timeout_seconds,
        wait_until=profile.wait_until,
        block_heavy_assets=profile.block_heavy_assets,
        settle_seconds=profile.settle_seconds,
        pre_capture=SephoraUSMarketPlugin(
            target_url=product_url,
            country_code="US",
            page_kind="pdp",
        ),
    )
    if isinstance(capture, CloakBrowserSnapshotFailure):
        raise SephoraOnboardingCaptureError(
            "configuration refresh failed before onboarding: "
            f"{capture.failure_kind}: {capture.message}"
        )
    return ParentConfigurationRefresh(
        requested_url=capture.requested_url,
        final_url=capture.final_url,
        rendered_dom=capture.rendered_dom,
        rendered_dom_sha256=hashlib.sha256(
            capture.rendered_dom.encode("utf-8")
        ).hexdigest(),
        pin_confirmed=capture.metadata.get("pin_confirmed") is True,
    )


def _link_store_product(html: str) -> Mapping[str, Any]:
    match = re.search(
        r"<script\b[^>]*\bid=[\"']linkStore[\"'][^>]*>([\s\S]*?)</script\s*>",
        html,
        flags=re.IGNORECASE,
    )
    if match is None:
        raise SephoraOnboardingCaptureError("rendered DOM is missing linkStore")
    try:
        payload = json.loads(match.group(1).strip())
        product = payload["page"]["product"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SephoraOnboardingCaptureError(
            "rendered DOM has no valid linkStore.page.product"
        ) from exc
    if not isinstance(product, Mapping):
        raise SephoraOnboardingCaptureError("linkStore.page.product must be an object")
    return product


def _read_config(html: str, key: str) -> BazaarvoiceReadConfig:
    match = re.search(
        rf'"{re.escape(key)}"\s*:\s*(\{{[^{{}}]*\}})',
        html,
    )
    if match is None:
        raise SephoraOnboardingCaptureError(f"page-declared read config is missing: {key}")
    try:
        raw = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SephoraOnboardingCaptureError(
            f"page-declared read config is malformed: {key}"
        ) from exc
    host = _required_string(raw.get("host"), f"{key}.host")
    version = _required_string(raw.get("version"), f"{key}.version")
    token = _required_string(raw.get("token"), f"{key}.token")
    if host != BAZAARVOICE_API_HOST:
        raise SephoraOnboardingCaptureError(
            f"{key}.host must be the allowlisted {BAZAARVOICE_API_HOST}"
        )
    if not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise SephoraOnboardingCaptureError(f"{key}.version is invalid")
    return BazaarvoiceReadConfig(host=host, version=version, token=token)


def _sephora_product_and_sku_ids(product: Mapping[str, Any]) -> tuple[str, ...]:
    ids: list[str] = [_required_string(product.get("productId"), "product.productId")]
    current_sku = product.get("currentSku")
    if isinstance(current_sku, Mapping):
        sku_id = _optional_string(current_sku.get("skuId"))
        if sku_id is not None:
            ids.append(sku_id)
    for key in ("regularChildSkus", "onSaleChildSkus"):
        raw_skus = product.get(key, [])
        if not isinstance(raw_skus, list):
            continue
        for raw_sku in raw_skus:
            if not isinstance(raw_sku, Mapping):
                continue
            sku_id = _optional_string(raw_sku.get("skuId"))
            if sku_id is not None:
                ids.append(sku_id)
    return tuple(dict.fromkeys(ids))


def _base_request_specs(
    product_id: str,
    question_limit: int,
    review_page_limit: int,
) -> tuple[ApiRequestSpec, ...]:
    # The accepted low-footprint target has exactly three response roles:
    # Helpful plus combined statistics, Recent (issued separately with bounded
    # continuation), and answer-rich Q&A. Demographics are promoted from the
    # Helpful response's FilteredStats context distributions instead of
    # separate per-bucket count requests.
    return (
        ApiRequestSpec(
            artifact_name="questions_most_answers_offset_000.json",
            endpoint="questions.json",
            config_kind="questions",
            parameters=(
                ("Filter", f"ProductId:eq:{product_id}"),
                ("Include", "Answers"),
                ("Limit", str(question_limit)),
                ("Offset", "0"),
                ("Sort", "TotalAnswerCount:desc"),
            ),
        ),
        ApiRequestSpec(
            artifact_name="reviews_non_incentivized_most_helpful_offset_000.json",
            endpoint="reviews.json",
            config_kind="reviews",
            parameters=(
                ("Filter", f"ProductId:eq:{product_id}"),
                ("Filter", "ContextDataValue_IncentivizedReview:eq:False"),
                ("Include", "Products"),
                ("Stats", "Reviews"),
                ("FilteredStats", "Reviews"),
                ("Limit", str(review_page_limit)),
                ("Offset", "0"),
                ("Sort", "TotalPositiveFeedbackCount:desc"),
            ),
        ),
    )


def _recent_request_spec(
    product_id: str,
    review_page_limit: int,
    offset: int,
) -> ApiRequestSpec:
    return ApiRequestSpec(
        artifact_name=(
            f"reviews_non_incentivized_most_recent_offset_{offset:05d}.json"
        ),
        endpoint="reviews.json",
        config_kind="reviews",
        parameters=(
            ("Filter", f"ProductId:eq:{product_id}"),
            ("Filter", "ContextDataValue_IncentivizedReview:eq:False"),
            ("Limit", str(review_page_limit)),
            ("Offset", str(offset)),
            ("Sort", "SubmissionTime:desc"),
        ),
    )


def _recent_page_state(
    body: bytes,
    label: str,
    allowed_product_ids: Sequence[str],
) -> dict[str, Any]:
    document = _load_api_document(body, label)
    rows = _require_list(document, "Results", label)
    total_results = _total_results(document, label)
    if total_results == 0 and rows:
        raise SephoraOnboardingCaptureError(
            f"{label} declares zero TotalResults but returned rows"
        )
    _validate_result_product_ids(
        rows,
        allowed_product_ids=allowed_product_ids,
        label=label,
        allow_empty=total_results == 0,
        allow_provider_collection_product_ids=True,
    )
    dates = [
        _parse_timestamp(
            _required_string(
                row.get("SubmissionTime") if isinstance(row, Mapping) else None,
                f"{label}.Results[{index}].SubmissionTime",
            ),
            f"{label}.Results[{index}].SubmissionTime",
        )
        for index, row in enumerate(rows)
    ]
    if dates != sorted(dates, reverse=True):
        raise SephoraOnboardingCaptureError(
            f"{label} is not ordered by SubmissionTime descending"
        )
    return {
        "total_results": total_results,
        "row_count": len(rows),
        "newest_submission_time": max(dates) if dates else None,
        "oldest_submission_time": min(dates) if dates else datetime.min.replace(
            tzinfo=timezone.utc
        ),
        "exhausted": len(rows) >= total_results,
    }


def _recent_offset(artifact_name: str) -> int:
    match = re.fullmatch(
        r"reviews_non_incentivized_most_recent_offset_(\d+)\.json",
        artifact_name,
    )
    if match is None:
        raise SephoraOnboardingCaptureError(
            f"invalid Most Recent artifact name: {artifact_name}"
        )
    return int(match.group(1))


def _request_manifest(
    parent: ParentContext,
    specs: Sequence[ApiRequestSpec],
    captured: Sequence[tuple[ApiRequestSpec, ApiResponse]],
) -> dict[str, Any]:
    response_by_name = {spec.artifact_name: response for spec, response in captured}
    return {
        "record_kind": "sephora_bazaarvoice_request_manifest_v4",
        "parent_packet_id": parent.packet_id,
        "parent_file_id": parent.file_id,
        "parent_file_sha256": parent.file_sha256,
        "product_id": parent.product_id,
        "product_url": parent.product_url,
        "parent_configuration": dict(parent.configuration_receipt),
        "credential_posture": (
            "page-declared read tokens used in flight; tokens and secret-bearing request URLs "
            "are not persisted"
        ),
        "requests": [
            {
                "artifact_name": spec.artifact_name,
                "endpoint": f"https://{BAZAARVOICE_API_HOST}/data/{spec.endpoint}",
                "api_version": (
                    parent.question_config.version
                    if spec.config_kind == "questions"
                    else parent.review_config.version
                ),
                "parameters": [
                    {"name": name, "value": value} for name, value in spec.parameters
                ],
                "response": (
                    {
                        "status": response_by_name[spec.artifact_name].status,
                        "reason": response_by_name[spec.artifact_name].reason or None,
                        "content_type": response_by_name[spec.artifact_name].content_type,
                        "byte_count": len(response_by_name[spec.artifact_name].body),
                        "captured_at": response_by_name[spec.artifact_name].captured_at,
                    }
                    if spec.artifact_name in response_by_name
                    else None
                ),
            }
            for spec in specs
        ],
    }


def _write_packet(
    *,
    data_root: DataLakeRoot,
    parent: ParentContext,
    artifacts: Sequence[tuple[str, bytes]],
    captured: Sequence[tuple[ApiRequestSpec, ApiResponse]],
    limitations: Sequence[str],
    summary: Mapping[str, Any],
):
    file_ids = staged_file_id_map(artifacts)
    captured_at = captured[-1][1].captured_at if captured else utc_now_z()
    timing = PacketTiming(
        source_publication_or_event=unknown_with_reason(
            "Bazaarvoice responses do not declare a single source publication time"
        ),
        source_edit_or_version=unknown_with_reason(
            "Bazaarvoice responses do not declare a product-level edit version"
        ),
        capture_time=known_fact(captured_at),
        recapture_time=known_fact(captured_at),
        cutoff_posture=known_fact("post_cutoff"),
    )
    access = known_fact(
        "page-declared Bazaarvoice read API attempted; exact acquired response bytes preserved"
    )
    archive = not_attempted("structured companion capture did not query archive/history")
    media = not_attempted("structured companion capture did not fetch linked review media")
    recapture = known_fact("supplement")
    return stage_and_write_packet(
        data_root=data_root,
        staged_artifacts=artifacts,
        source_slices=[
            SourceCaptureSlice(
                slice_id="sephora_review_qa_onboarding",
                locator=known_fact(parent.product_url),
                timing=timing,
                access_posture=access,
                archive_history_posture=archive,
                media_modality_posture=media,
                re_capture_relationship=recapture,
                locale_pin=known_fact("US"),
                currency_pin=known_fact("USD"),
                limitations=list(limitations),
                warning_notes=[],
                preserved_file_ids=[file_ids[name] for name, _content in artifacts],
            )
        ],
        source_family="retail_pdp",
        source_surface=SEPHORA_ONBOARDING_SOURCE_SURFACE,
        source_locator=known_fact(parent.product_url),
        decision_question=(
            "What does Sephora expose in a bounded Most Answers Q&A window, a "
            "non-incentivized Most Helpful review snapshot, a source-date-bounded "
            "30-day Most Recent window, and its exact live age-bucket counts?"
        ),
        capture_context=(
            f"structured companion capture from hash-verified parent packet "
            f"{parent.packet_id}; parser={SEPHORA_ONBOARDING_PARSER_VERSION}"
        ),
        actor_audience_context=unknown_with_reason(
            "reviewer demographic fields are self-reported source context; audience "
            "representativeness is not established"
        ),
        capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
        operator_category="sephora_onboarding_cli_operator",
        session_identity=None,
        visible_mode_changes=[
            "questions_sort_total_answer_count_desc",
            "reviews_filter_non_incentivized_false",
            "reviews_sort_total_positive_feedback_count_desc",
            "reviews_sort_submission_time_desc",
            "reviews_recent_window_source_date_bounded_30d_minimum",
            "review_age_bucket_inventory_20s_30s_40s_50s_plus",
        ],
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access,
        archive_history_posture=archive,
        media_modality_posture=media,
        re_capture_relationship=recapture,
        warnings=[],
        limitations=list(limitations),
        receipt_summary=(
            f"Sephora onboarding companion for {parent.product_id}: "
            f"{summary.get('record_kind', 'unknown result')}; exact API response bytes "
            "and a token-free request manifest are preserved."
        ),
        receipt_non_claims=[
            "not the complete Q&A corpus",
            "not reviewer population representativeness",
            "not an age estimate for reviews without a live age bucket",
            "not proof of Sephora's proprietary helpfulness ranking algorithm",
            "not a complete historical review corpus",
            "not review-body normalization or Judgment",
            "not a replacement for the parent rendered PDP packet",
        ],
    )


def _load_api_document(body: bytes, label: str) -> Mapping[str, Any]:
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SephoraOnboardingCaptureError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(document, Mapping):
        raise SephoraOnboardingCaptureError(f"{label} JSON root must be an object")
    errors = document.get("Errors")
    if errors:
        raise SephoraOnboardingCaptureError(f"{label} declares API errors")
    return document


def _require_list(document: Mapping[str, Any], key: str, label: str) -> list[Any]:
    value = document.get(key)
    if not isinstance(value, list):
        raise SephoraOnboardingCaptureError(f"{label}.{key} must be a list")
    return value


def _require_nonnegative_int(
    document: Mapping[str, Any], key: str, label: str
) -> int:
    value = document.get(key)
    if type(value) is not int or value < 0:
        raise SephoraOnboardingCaptureError(
            f"{label}.{key} must be a nonnegative integer"
        )
    return value


def _mapping_nonnegative_int(document: Mapping[str, Any], key: str, label: str) -> int:
    value = document.get(key)
    if type(value) is not int or value < 0:
        raise SephoraOnboardingCaptureError(f"{label}.{key} must be a nonnegative integer")
    return value


def _validate_result_product_ids(
    rows: Sequence[Any],
    *,
    allowed_product_ids: Sequence[str],
    label: str,
    allow_empty: bool = False,
    allow_provider_collection_product_ids: bool = False,
) -> None:
    if not rows:
        if allow_empty:
            return
        raise SephoraOnboardingCaptureError(
            f"{label}.Results is empty; served product identity cannot be verified"
        )
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SephoraOnboardingCaptureError(f"{label}.Results[{index}] must be an object")
        product_id = _required_string(
            row.get("ProductId"),
            f"{label}.Results[{index}].ProductId",
        )
        if (
            not allow_provider_collection_product_ids
            and product_id not in allowed_product_ids
        ):
            raise SephoraOnboardingCaptureError(
                f"{label}.Results[{index}] product mismatch: "
                f"expected one of {list(allowed_product_ids)}, got {product_id}"
            )


def _total_results(document: Mapping[str, Any], label: str) -> int:
    return _require_nonnegative_int(document, "TotalResults", label)


def _review_inventory_row(row: Any, *, rank: int) -> dict[str, Any]:
    """Compact, body-free row: exact bodies stay only in the raw response."""
    if not isinstance(row, Mapping):
        raise SephoraOnboardingCaptureError(f"review row {rank} must be an object")
    review_id = _required_string(row.get("Id"), f"review row {rank}.Id")
    product_id = _required_string(
        row.get("ProductId"),
        f"review row {rank}.ProductId",
    )
    review_text = _optional_string(row.get("ReviewText"))
    badges = row.get("Badges")
    context = row.get("ContextDataValues")
    return {
        "rank": rank,
        "review_id": review_id,
        "product_id": product_id,
        "title_present": _optional_string(row.get("Title")) is not None,
        "body_present": review_text is not None,
        "rating": row.get("Rating"),
        "submission_time": _optional_string(row.get("SubmissionTime")),
        "nickname_present": _optional_string(row.get("UserNickname")) is not None,
        "is_recommended": row.get("IsRecommended"),
        "is_verified_buyer": row.get("IsVerifiedBuyer"),
        "total_feedback_count": row.get("TotalFeedbackCount"),
        "total_positive_feedback_count": row.get("TotalPositiveFeedbackCount"),
        "total_negative_feedback_count": row.get("TotalNegativeFeedbackCount"),
        "context_dimension_keys": (
            sorted(str(key) for key in context)
            if isinstance(context, Mapping)
            else []
        ),
        "badge_ids": (
            sorted(str(key) for key in badges) if isinstance(badges, Mapping) else []
        ),
        "photo_count": len(row.get("Photos") or []),
        "video_count": len(row.get("Videos") or []),
        "source_fields": sorted(str(key) for key in row),
    }


def _review_field_inventory(rows: Sequence[Any]) -> set[str]:
    fields: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SephoraOnboardingCaptureError(
                f"review field inventory row {index} must be an object"
            )
        fields.update(str(key) for key in row)
    return fields


def _review_ids(rows: Sequence[Any]) -> list[str]:
    return [
        _required_string(
            row.get("Id") if isinstance(row, Mapping) else None,
            f"review row {index}.Id",
        )
        for index, row in enumerate(rows)
    ]


def _parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SephoraOnboardingCaptureError(
            f"{label} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise SephoraOnboardingCaptureError(f"{label} lacks a timezone")
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SephoraOnboardingCaptureError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _product_id_from_url(url: str) -> str:
    match = re.search(r"-P(\d+)(?:[/?#]|$)", url, flags=re.IGNORECASE)
    if match is None:
        raise SephoraOnboardingCaptureError(
            "parent source locator is not a Sephora product URL with a product ID"
        )
    return f"P{match.group(1)}"


def _helpful_statistics(
    document: Mapping[str, Any],
    product_id: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    includes = document.get("Includes", {})
    products = includes.get("Products") if isinstance(includes, Mapping) else None
    if not isinstance(products, Mapping):
        raise SephoraOnboardingCaptureError(
            "Most Helpful response lacks the Includes.Products statistics block"
        )
    product = products.get(product_id)
    if not isinstance(product, Mapping):
        raise SephoraOnboardingCaptureError(
            f"Most Helpful Includes.Products does not include {product_id}"
        )
    statistics = product.get("ReviewStatistics")
    filtered = product.get("FilteredReviewStatistics")
    if not isinstance(statistics, Mapping) or not isinstance(filtered, Mapping):
        raise SephoraOnboardingCaptureError(
            "Most Helpful response lacks combined ReviewStatistics and "
            "FilteredReviewStatistics"
        )
    return statistics, filtered


def _context_distribution(
    statistics: Mapping[str, Any],
    dimension: str,
) -> list[dict[str, Any]] | None:
    distribution = statistics.get("ContextDataDistribution")
    if not isinstance(distribution, Mapping):
        raise SephoraOnboardingCaptureError(
            "FilteredReviewStatistics lacks a ContextDataDistribution object"
        )
    entry = distribution.get(dimension)
    if entry is None:
        return None
    if not isinstance(entry, Mapping):
        raise SephoraOnboardingCaptureError(
            f"ContextDataDistribution.{dimension} must be an object"
        )
    values = entry.get("Values")
    if not isinstance(values, list):
        raise SephoraOnboardingCaptureError(
            f"ContextDataDistribution.{dimension}.Values must be an array"
        )
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            raise SephoraOnboardingCaptureError(
                f"ContextDataDistribution.{dimension}.Values[{index}] must be an object"
            )
        rows.append(
            {
                "value": str(item.get("Value")),
                "count": _mapping_nonnegative_int(
                    item,
                    "Count",
                    f"ContextDataDistribution.{dimension}.Values[{index}]",
                ),
            }
        )
    return rows


_PROMOTED_STATISTIC_FIELDS = (
    "TotalReviewCount",
    "AverageOverallRating",
    "RecommendedCount",
    "NotRecommendedCount",
    "RatingDistribution",
    "HelpfulVoteCount",
    "FirstSubmissionTime",
    "LastSubmissionTime",
)


def _promoted_statistics(statistics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field: statistics.get(field)
        for field in _PROMOTED_STATISTIC_FIELDS
        if field in statistics
    }


def _percentage(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator * 100.0 / denominator, 2)


def _display_text(value: str) -> str:
    return " ".join(html_lib.unescape(unquote(value)).split())


def _safe_error_text(exc: Exception) -> str:
    text = str(exc)
    if "passkey=" in text or "token=" in text:
        return "secret-bearing acquisition error suppressed"
    return text[:300]


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


__all__ = [
    "ApiRequestSpec",
    "ApiResponse",
    "BazaarvoiceReadConfig",
    "DEFAULT_QUESTION_LIMIT",
    "DEFAULT_RECENT_WINDOW_DAYS",
    "DEFAULT_REVIEW_PAGE_LIMIT",
    "ParentContext",
    "SEPHORA_AGE_BUCKETS",
    "SEPHORA_ONBOARDING_PARSER_VERSION",
    "SEPHORA_ONBOARDING_SOURCE_SURFACE",
    "SephoraOnboardingCaptureError",
    "build_sephora_onboarding_summary",
    "capture_sephora_onboarding_packet",
]
