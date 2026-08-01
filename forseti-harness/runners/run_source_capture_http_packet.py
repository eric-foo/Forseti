from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
    unknown_with_reason,
)
from source_capture.cli_support import (
    add_durability_arguments,
    build_intended_cadence,
    build_optional_fact,
    require_series_identity,
)
from source_capture.content_extraction import (
    CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    CONTENT_RECORD_FILENAME,
    ContentExtractionSpec,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map
from source_capture.adapters import DirectHttpCaptureFailure, fetch_direct_http_capture
from source_capture.access_gate import detect_login_gate
from source_capture.block_shell import CaptureBodyClass, classify_capture_body
from source_capture.adapters.credo_us_market import (
    confirm_credo_us_market,
    validate_credo_us_market_url,
)
from source_capture.adapters.walmart_us_market import (
    confirm_walmart_us_market,
    validate_walmart_us_market_url,
)
from source_capture.retail_capture_profiles import (
    RetailCaptureProfile,
    get_retail_capture_profile,
    retail_capture_profile_names,
    validate_retail_capture_profile_route,
)
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
    evaluate_source_detail_sufficiency,
    source_detail_sufficiency_failure_message,
    source_detail_sufficiency_limitation,
    source_detail_sufficiency_mode_change,
)

if TYPE_CHECKING:
    from data_lake.root import DataLakeRoot


DIRECT_HTTP_NON_CLAIMS = [
    "not browser automation",
    "not API SDK use",
    "not archive retrieval",
    "not media preservation",
    "not scraper framework use",
    "not proxy or session injection",
    "not ECR design",
    "not Cleaning implementation",
    "not Judgment scoring",
    "not buyer proof",
    "not commercial-readiness logic",
]
WALMART_MARKET_PIN_FAILURE_MODE_CHANGE = "walmart_market_pin_failed"
CREDO_MARKET_PIN_FAILURE_MODE_CHANGE = "credo_market_pin_failed"


@dataclass(frozen=True)
class DirectHttpPacketOutcome:
    exit_code: int
    message: str
    http_status: int | None
    retry_after: str | None
    retry_after_disposition: str
    content_capture_allowed: bool
    body_classification: str | None
    body_classification_signal: str | None
    login_gate_signal: str | None
    access_block_reason: str | None


def run_source_capture_http_packet(
    *,
    url: str,
    source_family: str,
    source_surface: str,
    decision_question: str,
    output_directory: Path | None = None,
    data_root: "DataLakeRoot | None" = None,
    capture_context: str,
    operator_category: str,
    capture_mode: CaptureModeCategory,
    session_id: str | None,
    actor_audience_context,
    visible_mode_changes: Sequence[str],
    source_publication_or_event,
    source_edit_or_version,
    cutoff_posture,
    recapture_time,
    re_capture_relationship,
    warnings: Sequence[str],
    limitations: Sequence[str],
    retail_capture_profile: RetailCaptureProfile | None = None,
    timeout_seconds: float,
    max_bytes: int,
    session_visibility_pin=None,
    locale_pin=None,
    currency_pin=None,
    variant_pin=None,
    series_id: str | None = None,
    cold_start_at=None,
    pre_coverage_history_posture=None,
    intended_cadence: dict[str, object] | None = None,
    content_extraction: ContentExtractionSpec | None = None,
    walmart_market: str | None = None,
    credo_market: str | None = None,
    outcome_observer: Callable[[DirectHttpPacketOutcome], None] | None = None,
) -> tuple[int, str]:
    if walmart_market is not None and credo_market is not None:
        raise ValueError("--credo-market and --walmart-market are mutually exclusive")
    if retail_capture_profile is not None:
        if retail_capture_profile.source_surface != "direct_http":
            raise ValueError(
                f"retail capture profile {retail_capture_profile.name} belongs to "
                f"{retail_capture_profile.source_surface}; use the matching capture runner"
            )
        validate_retail_capture_profile_route(
            retail_capture_profile,
            url=url,
            source_family=source_family,
            source_surface=source_surface,
        )
    if walmart_market is not None:
        if walmart_market != "US":
            raise ValueError("Walmart market assertion currently supports only US/USD")
        if (
            retail_capture_profile is None
            or retail_capture_profile.name != "walmart_pdp_aggregate"
        ):
            raise ValueError(
                "--walmart-market US requires --retail-capture-profile "
                "walmart_pdp_aggregate"
            )
        if locale_pin is not None or currency_pin is not None:
            raise ValueError(
                "--walmart-market derives confirmed country/currency pins and must not "
                "be combined with manual --locale-pin or --currency-pin declarations"
            )
        validate_walmart_us_market_url(url)
    if credo_market is not None:
        if credo_market != "US":
            raise ValueError("Credo market assertion currently supports only US/USD")
        if source_family != "retail_pdp" or source_surface != "direct_http":
            raise ValueError(
                "--credo-market US requires retail_pdp/direct_http capture"
            )
        if locale_pin is not None or currency_pin is not None:
            raise ValueError(
                "--credo-market derives confirmed country/currency pins and must not "
                "be combined with manual --locale-pin or --currency-pin declarations"
            )
        validate_credo_us_market_url(url)

    timing = PacketTiming(
        source_publication_or_event=source_publication_or_event
        or unknown_with_reason("direct HTTP adapter did not infer source publication or event timing"),
        source_edit_or_version=source_edit_or_version
        or unknown_with_reason("direct HTTP adapter did not infer source edit or version timing"),
        capture_time=known_fact("1970-01-01T00:00:00Z"),
        recapture_time=recapture_time
        or not_applicable("direct HTTP packet did not model an earlier capture by default"),
        cutoff_posture=cutoff_posture
        or unknown_with_reason("direct HTTP runner did not receive cutoff posture metadata"),
    )

    capture_result = fetch_direct_http_capture(
        url=url,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
    )
    if isinstance(capture_result, DirectHttpCaptureFailure):
        return _report_outcome(
            outcome_observer,
            DirectHttpPacketOutcome(
                exit_code=3,
                message=capture_result.message,
                http_status=capture_result.status,
                retry_after=capture_result.retry_after,
                retry_after_disposition=capture_result.retry_after_disposition,
                content_capture_allowed=False,
                body_classification=None,
                body_classification_signal=None,
                login_gate_signal=None,
                access_block_reason=capture_result.failure_kind.value,
            ),
        )

    if retail_capture_profile is not None:
        capture_result.metadata["retail_capture_profile"] = retail_capture_profile.metadata()
    decoded_body = capture_result.body.decode("utf-8", errors="replace")
    login_gate = detect_login_gate(
        final_url=capture_result.final_url,
        body_text=decoded_body,
    )
    classification_headers = {}
    content_type = capture_result.metadata.get("content_type")
    if content_type is not None:
        classification_headers["Content-Type"] = str(content_type)
    content_encoding = capture_result.metadata.get("content_encoding")
    if content_encoding is not None:
        classification_headers["Content-Encoding"] = str(content_encoding)
    block_signal_header_names = capture_result.metadata.get("block_signal_header_names")
    if isinstance(block_signal_header_names, list):
        for header_name in block_signal_header_names:
            if isinstance(header_name, str):
                classification_headers[header_name] = "present"
    body_classification = classify_capture_body(
        status=capture_result.status,
        headers=classification_headers,
        body=capture_result.body,
    )
    capture_result.metadata.update(
        {
            "body_classification": body_classification.classification.value,
            "body_classification_signal": body_classification.signal,
            "body_classification_detail": body_classification.detail,
            "login_gate_signal": login_gate.signal if login_gate is not None else None,
            "login_gate_detail": login_gate.detail if login_gate is not None else None,
        }
    )
    status_ok = 200 <= capture_result.status < 300
    content_capture_allowed = (
        status_ok
        and login_gate is None
        and body_classification.classification == CaptureBodyClass.CONTENT_UNVERIFIED
        and body_classification.signal is None
    )
    if login_gate is not None:
        access_block_reason = f"{login_gate.signal}: {login_gate.detail}"
    elif body_classification.classification == CaptureBodyClass.BLOCK_SHELL:
        access_block_reason = (
            f"block_shell: {body_classification.signal or body_classification.detail}"
        )
    elif body_classification.classification == CaptureBodyClass.EMPTY:
        access_block_reason = "empty_body"
    elif body_classification.signal is not None:
        access_block_reason = (
            f"body_inspection_limited: {body_classification.signal}: "
            f"{body_classification.detail}"
        )
    elif not status_ok:
        access_block_reason = f"HTTP {capture_result.status}"
    else:
        access_block_reason = None
    capture_result.metadata.update(
        {
            "content_capture_allowed": content_capture_allowed,
            "access_block_reason": access_block_reason,
        }
    )

    walmart_pin_failure: str | None = None
    credo_pin_failure: str | None = None
    if walmart_market == "US":
        confirmation = confirm_walmart_us_market(
            decoded_body,
            requested_url=url,
            final_url=capture_result.final_url,
        )
        capture_result.metadata.update(confirmation.metadata())
        if confirmation.confirmed:
            locale_pin = known_fact("US")
            currency_pin = known_fact("USD")
        else:
            walmart_pin_failure = confirmation.detail
    if credo_market == "US":
        confirmation = confirm_credo_us_market(
            decoded_body,
            requested_url=url,
            final_url=capture_result.final_url,
        )
        capture_result.metadata.update(confirmation.metadata())
        if confirmation.confirmed:
            locale_pin = known_fact("US")
            currency_pin = known_fact("USD")
        else:
            credo_pin_failure = confirmation.detail
    sufficiency_result = evaluate_source_detail_sufficiency(
        requirements=(
            retail_capture_profile.requirements if retail_capture_profile is not None else None
        ),
        access_block_reason=access_block_reason,
        visible_text=decoded_body,
        rendered_dom=decoded_body,
    )

    packet_warnings = list(warnings) + capture_result.warning_notes
    posture_limitations: list[str] = []
    if login_gate is not None:
        posture_limitations.append(
            "visible_capture_limitation: direct_http preserved a login/sign-in access shell "
            f"({login_gate.signal}), not source content"
        )
    elif body_classification.classification == CaptureBodyClass.BLOCK_SHELL:
        posture_limitations.append(
            "visible_capture_limitation: direct_http preserved a block/challenge shell "
            f"({body_classification.signal}), not source content"
        )
    elif body_classification.classification == CaptureBodyClass.EMPTY:
        posture_limitations.append(
            "visible_capture_limitation: direct_http preserved an empty/whitespace-only body, "
            "not source content"
        )
    elif body_classification.signal is not None:
        posture_limitations.append(
            "visible_capture_limitation: direct_http preserved a body that could not be "
            f"safely inspected ({body_classification.signal}); capture not admitted as source content"
        )
    packet_limitations = (
        list(limitations) + capture_result.limitation_notes + posture_limitations
    )
    if walmart_market == "US":
        observed_postal = capture_result.metadata.get("observed_location_postal_code")
        if observed_postal is not None:
            packet_limitations.append(
                f"Walmart postal {observed_postal} is origin-derived page context, not "
                "an operator-set delivery-location pin"
            )
    if walmart_pin_failure is not None:
        packet_limitations.append(
            f"{WALMART_MARKET_PIN_FAILURE_MODE_CHANGE}: {walmart_pin_failure}; packet "
            "preserved but MUST NOT be admitted as Walmart US/USD storefront evidence"
        )
    if credo_pin_failure is not None:
        packet_limitations.append(
            f"{CREDO_MARKET_PIN_FAILURE_MODE_CHANGE}: {credo_pin_failure}; packet "
            "preserved but MUST NOT be admitted as Credo US/USD storefront evidence"
        )
    sufficiency_limitation = source_detail_sufficiency_limitation(sufficiency_result)
    if sufficiency_limitation is not None:
        packet_limitations.append(sufficiency_limitation)
    packet_visible_mode_changes = list(visible_mode_changes)
    sufficiency_mode_change = source_detail_sufficiency_mode_change(sufficiency_result)
    if sufficiency_mode_change is not None:
        packet_visible_mode_changes.append(sufficiency_mode_change)
    if walmart_pin_failure is not None:
        packet_visible_mode_changes.append(WALMART_MARKET_PIN_FAILURE_MODE_CHANGE)
    if credo_pin_failure is not None:
        packet_visible_mode_changes.append(CREDO_MARKET_PIN_FAILURE_MODE_CHANGE)

    if login_gate is not None:
        access_posture = known_fact(
            f"direct_http access_failed with HTTP {capture_result.status} "
            f"{capture_result.reason or 'without reason'}: {login_gate.signal}; "
            "login/sign-in shell preserved, not source content"
        )
    elif body_classification.classification == CaptureBodyClass.BLOCK_SHELL:
        access_posture = known_fact(
            f"direct_http access_failed with HTTP {capture_result.status} "
            f"{capture_result.reason or 'without reason'}: block_shell "
            f"({body_classification.signal}); response shell preserved, not source content"
        )
    elif body_classification.classification == CaptureBodyClass.EMPTY:
        access_posture = known_fact(
            f"direct_http access_failed with HTTP {capture_result.status}: "
            "empty/whitespace-only body preserved, not source content"
        )
    elif body_classification.signal is not None:
        access_posture = known_fact(
            f"direct_http received HTTP {capture_result.status} "
            f"{capture_result.reason or 'without reason'}, but body inspection was limited "
            f"({body_classification.signal}); capture not admitted as source content"
        )
    elif not status_ok:
        access_posture = known_fact(
            f"direct_http access_failed with HTTP {capture_result.status} "
            f"{capture_result.reason or 'without reason'}; response body preserved"
        )
    else:
        access_posture = known_fact(
            f"direct_http succeeded with HTTP {capture_result.status} "
            f"{capture_result.reason or 'without reason'}; body preserved; "
            "no known access shell detected; source content not certified"
        )

    # Extract source-visible content before disposable transport bytes are
    # released. Non-2xx and extraction failures retain raw bytes and fail loud.
    extraction_failure: str | None = None
    content_record_bytes: bytes | None = None
    if content_extraction is not None:
        raw_sha256 = hashlib.sha256(capture_result.body).hexdigest()
        if (
            content_extraction.requested_retention_mode == "content"
            and content_capture_allowed
        ):
            try:
                record = content_extraction.extractor(
                    decoded_body, capture_result.final_url
                )
                if not isinstance(record, dict):
                    raise TypeError(
                        "content extractor must return a JSON object, "
                        f"got {type(record).__name__}"
                    )
                content_record_bytes = (
                    json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
                ).encode("utf-8")
                extraction_status = "succeeded"
            except Exception as exc:
                extraction_failure = f"{type(exc).__name__}: {exc}"
                extraction_status = f"failed: {extraction_failure}"
        elif content_extraction.requested_retention_mode == "content":
            extraction_failure = (
                "access classification prevented content extraction: "
                f"{access_block_reason or 'source content not inspectable'}"
            )
            extraction_status = f"failed: {extraction_failure}"
        elif content_extraction.requested_retention_mode == "raw":
            if (
                content_extraction.validate_in_raw_mode
                and 200 <= capture_result.status < 300
            ):
                # Validity check only: raw stays the preserved artifact either
                # way, but a raising extractor must not be reported as a clean
                # capture (see ContentExtractionSpec.validate_in_raw_mode).
                try:
                    content_extraction.extractor(decoded_body, capture_result.final_url)
                    extraction_status = "not_retained: raw retention requested; projection validated"
                except Exception as exc:
                    extraction_failure = f"{type(exc).__name__}: {exc}"
                    extraction_status = f"failed: {extraction_failure}"
            else:
                extraction_status = "not_attempted: raw retention requested"
        else:
            extraction_status = (
                f"not_attempted: HTTP {capture_result.status} response; raw preserved"
            )
        retention_outcome = (
            "content"
            if content_record_bytes is not None and extraction_failure is None
            else "raw_failure"
            if extraction_failure is not None or not status_ok
            else "raw"
        )
        raw_preserved = retention_outcome != "content"
        capture_result.metadata["content_extraction"] = {
            "requested_retention_mode": content_extraction.requested_retention_mode,
            "retention_outcome": retention_outcome,
            "extractor_version": content_extraction.extractor_version,
            "raw_sha256": raw_sha256,
            "raw_byte_count": len(capture_result.body),
            "raw_preserved": raw_preserved,
            "extraction_status": extraction_status,
        }
        if extraction_failure is not None:
            packet_limitations.append(
                "content extraction failed in flight; raw response preserved as fallback: "
                + extraction_failure
            )
        elif content_record_bytes is None:
            packet_limitations.append(
                f"raw response retained with extraction status {extraction_status}"
            )
        else:
            packet_limitations.append(
                "content-retention packet: raw response discarded after hashing; "
                f"{CONTENT_RECORD_FILENAME} preserved under "
                f"extractor_version={content_extraction.extractor_version}"
            )
    include_raw_body = (
        content_extraction is None
        or capture_result.metadata["content_extraction"]["raw_preserved"]
    )

    artifacts: list[tuple[str, bytes]] = []
    if include_raw_body:
        artifacts.append(("http_response_body.bin", capture_result.body))
    if content_record_bytes is not None:
        artifacts.append((CONTENT_RECORD_FILENAME, content_record_bytes))
    artifacts.append(
        (
            "http_response_metadata.json",
            (json.dumps(capture_result.metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    )
    file_ids = staged_file_id_map(artifacts)

    timing = timing.model_copy(
        update={
            "capture_time": known_fact(str(capture_result.metadata["capture_timestamp"]))
        }
    )
    archive_posture = not_attempted("direct HTTP adapter does not query archive or history services")
    media_posture = not_attempted(
        "direct HTTP adapter preserves the response body only and does not fetch linked media assets"
    )
    recapture_posture = re_capture_relationship or not_applicable(
        "no prior source capture packet was supplied for this direct HTTP capture"
    )

    result = stage_and_write_packet(
        output_directory=output_directory,
        data_root=data_root,
        staged_artifacts=artifacts,
        source_slices=[
            SourceCaptureSlice(
                slice_id="slice_01",
                locator=known_fact(capture_result.final_url),
                timing=timing,
                access_posture=access_posture,
                archive_history_posture=archive_posture,
                media_modality_posture=media_posture,
                re_capture_relationship=recapture_posture,
                session_visibility_pin=session_visibility_pin,
                locale_pin=locale_pin,
                currency_pin=currency_pin,
                variant_pin=variant_pin,
                limitations=packet_limitations,
                warning_notes=packet_warnings,
                preserved_file_ids=[file_ids[name] for name, _content in artifacts],
            )
        ],
        source_family=source_family,
        source_surface=source_surface,
        source_locator=known_fact(capture_result.requested_url),
        decision_question=decision_question,
        capture_context=capture_context,
        actor_audience_context=actor_audience_context
        or unknown_with_reason("actor or audience context was not supplied to the direct HTTP runner"),
        capture_mode=capture_mode,
        operator_category=operator_category,
        session_identity=session_id,
        visible_mode_changes=packet_visible_mode_changes,
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access_posture,
        archive_history_posture=archive_posture,
        media_modality_posture=media_posture,
        re_capture_relationship=recapture_posture,
        series_id=series_id,
        cold_start_at=cold_start_at,
        pre_coverage_history_posture=pre_coverage_history_posture,
        intended_cadence=intended_cadence,
        warnings=packet_warnings,
        limitations=packet_limitations,
        receipt_summary=(
            f"Direct HTTP packet for {source_family} with HTTP {capture_result.status} "
            + (
                f"and {len(capture_result.body)} preserved body bytes."
                if include_raw_body
                else (
                    f"in content mode: derived {CONTENT_RECORD_FILENAME} preserved; "
                    f"{len(capture_result.body)} raw bytes hashed then discarded."
                )
            )
        ),
        receipt_non_claims=DIRECT_HTTP_NON_CLAIMS,
    )
    authoritative_outcome = DirectHttpPacketOutcome(
        exit_code=0,
        message=result.output_directory,
        http_status=capture_result.status,
        retry_after=capture_result.metadata.get("retry_after"),
        retry_after_disposition=str(
            capture_result.metadata.get("retry_after_disposition", "absent")
        ),
        content_capture_allowed=content_capture_allowed,
        body_classification=body_classification.classification.value,
        body_classification_signal=body_classification.signal,
        login_gate_signal=login_gate.signal if login_gate is not None else None,
        access_block_reason=access_block_reason,
    )
    if sufficiency_result.enabled and not sufficiency_result.passed:
        return _report_outcome(
            outcome_observer,
            replace(
                authoritative_outcome,
                exit_code=SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
                message=source_detail_sufficiency_failure_message(
                    output_directory=result.output_directory,
                    result=sufficiency_result,
                ),
            ),
        )
    if walmart_pin_failure is not None:
        return _report_outcome(
            outcome_observer,
            replace(
                authoritative_outcome,
                exit_code=SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
                message=(
                    f"{WALMART_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
                    f"{result.output_directory}: {walmart_pin_failure}"
                ),
            ),
        )
    if credo_pin_failure is not None:
        return _report_outcome(
            outcome_observer,
            replace(
                authoritative_outcome,
                exit_code=SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
                message=(
                    f"{CREDO_MARKET_PIN_FAILURE_MODE_CHANGE}: packet preserved at "
                    f"{result.output_directory}: {credo_pin_failure}"
                ),
            ),
        )
    if extraction_failure is not None:
        # The raw fallback packet was written; the failure detail lives in the
        # packet limitations and HTTP metadata. Message stays the packet path
        # so callers can still locate the preserved evidence.
        return _report_outcome(
            outcome_observer,
            replace(
                authoritative_outcome,
                exit_code=CONTENT_EXTRACTION_FAILED_EXIT_CODE,
                message=result.output_directory,
            ),
        )
    return _report_outcome(outcome_observer, authoritative_outcome)


def _report_outcome(
    outcome_observer: Callable[[DirectHttpPacketOutcome], None] | None,
    outcome: DirectHttpPacketOutcome,
) -> tuple[int, str]:
    if outcome_observer is not None:
        outcome_observer(outcome)
    return outcome.exit_code, outcome.message


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch one HTTP URL with stdlib urllib and write a Source Capture Packet when a non-empty body is returned."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-family", default="web_page")
    parser.add_argument("--source-surface", default="direct_http")
    parser.add_argument("--decision-question", required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--data-root",
        default=None,
        help="Commit into the Forseti data lake at this root; explicit --data-root is mutually exclusive with --output. FORSETI_DATA_ROOT is used only when --output is omitted; legacy ORCA_DATA_ROOT is also accepted.",
    )
    parser.add_argument(
        "--capture-context",
        default="direct HTTP source capture with stdlib urllib",
    )
    parser.add_argument("--operator-category", default="direct_http_cli_operator")
    parser.add_argument(
        "--capture-mode",
        choices=[item.value for item in CaptureModeCategory],
        default=CaptureModeCategory.STRUCTURED_ACCESS.value,
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument(
        "--retail-capture-profile",
        choices=retail_capture_profile_names(),
        default=None,
        help=(
            "Apply a named direct-HTTP retailer/page-kind profile through the existing "
            "post-capture source-detail sufficiency gate."
        ),
    )
    parser.add_argument(
        "--walmart-market",
        choices=["US"],
        default=None,
        help=(
            "Fail-closed assertion for a Walmart US/USD Direct HTTP PDP. Requires "
            "one __NEXT_DATA__ object to bind the URL item to product.usItemId, "
            "current-price currencyUnit=USD, equal page/product origin postal "
            "context, and immediate module targeting countryCode US. Accepts "
            "Walmart's scalar US or exact single-item [US] serialization. Performs "
            "no preference or delivery-location mutation."
        ),
    )
    parser.add_argument(
        "--credo-market",
        choices=["US"],
        default=None,
        help=(
            "Fail-closed assertion for a Credo US/USD Direct HTTP PDP. Requires "
            "the exact Credo product route and canonical URL, Shopify.country=US, "
            "Shopify.currency.active=USD, and one bound Product JSON-LD object "
            "with a named brand and nonempty USD offer. Performs no preference, "
            "cookie, cart, or delivery-location mutation."
        ),
    )
    parser.add_argument("--actor-audience-context", default=None)
    parser.add_argument("--actor-audience-context-unknown-reason", default=None)
    parser.add_argument("--visible-mode-change", action="append", default=[])
    parser.add_argument("--source-publication-or-event", default=None)
    parser.add_argument("--source-publication-or-event-unknown-reason", default=None)
    parser.add_argument("--source-edit-or-version", default=None)
    parser.add_argument("--source-edit-or-version-unknown-reason", default=None)
    parser.add_argument("--cutoff-posture", default=None)
    parser.add_argument("--cutoff-posture-unknown-reason", default=None)
    parser.add_argument("--recapture-time", default=None)
    parser.add_argument("--recapture-time-not-applicable-reason", default=None)
    parser.add_argument("--recapture-relationship", default=None)
    parser.add_argument("--recapture-relationship-not-applicable-reason", default=None)
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--limitation", action="append", default=[])
    add_durability_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        require_series_identity(args)
        retail_capture_profile = (
            get_retail_capture_profile(args.retail_capture_profile)
            if args.retail_capture_profile is not None
            else None
        )
        # helper-delta: vs runners/_scaffold.resolve_output_root -- unprefixed messages
        # and the exactly-one check re-runs after resolution on the derived output_directory.
        data_root = None
        output_directory = args.output
        if output_directory is not None and args.data_root is not None:
            parser.exit(
                status=2,
                message="exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
            )
        data_root_requested = args.data_root is not None or (
            output_directory is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))
        )
        if data_root_requested:
            from data_lake.root import DataLakeRoot

            data_root = DataLakeRoot.resolve(explicit=args.data_root)
            output_directory = None
        if (output_directory is None) == (data_root is None):
            parser.exit(
                status=2,
                message="exactly one of --output or --data-root/FORSETI_DATA_ROOT/ORCA_DATA_ROOT is required\n",
            )
        exit_code, message = run_source_capture_http_packet(
            url=args.url,
            source_family=args.source_family,
            source_surface=args.source_surface,
            decision_question=args.decision_question,
            output_directory=output_directory,
            data_root=data_root,
            capture_context=args.capture_context,
            operator_category=args.operator_category,
            capture_mode=CaptureModeCategory(args.capture_mode),
            session_id=args.session_id,
            actor_audience_context=build_optional_fact(
                label="actor/audience context",
                value=args.actor_audience_context,
                unknown_reason=args.actor_audience_context_unknown_reason,
            ),
            visible_mode_changes=args.visible_mode_change,
            source_publication_or_event=build_optional_fact(
                label="source publication or event timing",
                value=args.source_publication_or_event,
                unknown_reason=args.source_publication_or_event_unknown_reason,
            ),
            source_edit_or_version=build_optional_fact(
                label="source edit or version timing",
                value=args.source_edit_or_version,
                unknown_reason=args.source_edit_or_version_unknown_reason,
            ),
            cutoff_posture=build_optional_fact(
                label="cutoff posture",
                value=args.cutoff_posture,
                unknown_reason=args.cutoff_posture_unknown_reason,
            ),
            recapture_time=build_optional_fact(
                label="re-capture timing",
                value=args.recapture_time,
                not_applicable_reason=args.recapture_time_not_applicable_reason,
            ),
            re_capture_relationship=build_optional_fact(
                label="re-capture relationship",
                value=args.recapture_relationship,
                not_applicable_reason=args.recapture_relationship_not_applicable_reason,
            ),
            warnings=args.warning,
            limitations=args.limitation,
            retail_capture_profile=retail_capture_profile,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
            session_visibility_pin=build_optional_fact(
                label="session visibility pin",
                value=args.session_visibility_pin,
                unknown_reason=args.session_visibility_pin_unknown_reason,
                not_applicable_reason=args.session_visibility_pin_not_applicable_reason,
            ),
            locale_pin=build_optional_fact(
                label="locale pin",
                value=args.locale_pin,
                unknown_reason=args.locale_pin_unknown_reason,
                not_applicable_reason=args.locale_pin_not_applicable_reason,
            ),
            currency_pin=build_optional_fact(
                label="currency pin",
                value=args.currency_pin,
                unknown_reason=args.currency_pin_unknown_reason,
                not_applicable_reason=args.currency_pin_not_applicable_reason,
            ),
            variant_pin=build_optional_fact(
                label="variant pin",
                value=args.variant_pin,
                unknown_reason=args.variant_pin_unknown_reason,
                not_applicable_reason=args.variant_pin_not_applicable_reason,
            ),
            series_id=args.series_id,
            cold_start_at=build_optional_fact(
                label="cold-start timing",
                value=args.cold_start_at,
                unknown_reason=args.cold_start_at_unknown_reason,
                not_applicable_reason=args.cold_start_at_not_applicable_reason,
            ),
            pre_coverage_history_posture=build_optional_fact(
                label="pre-coverage history posture",
                value=args.pre_coverage_history_posture,
                unknown_reason=args.pre_coverage_history_posture_unknown_reason,
                not_applicable_reason=args.pre_coverage_history_posture_not_applicable_reason,
            ),
            intended_cadence=build_intended_cadence(args),
            walmart_market=args.walmart_market,
            credo_market=args.credo_market,
        )
    except ValueError as exc:
        parser.exit(status=2, message=f"source capture direct HTTP failed: {exc}\n")
    except Exception as exc:
        parser.exit(status=3, message=f"source capture direct HTTP failed: {exc}\n")

    if exit_code == 0:
        print(message)
        return 0

    parser.exit(status=exit_code, message=f"source capture direct HTTP failed: {message}\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
