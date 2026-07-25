from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from data_lake.root import DataLakeRoot
from source_capture.models import known_fact
from source_capture.sephora_onboarding_capture import (
    ApiRequestSpec,
    ApiResponse,
    BazaarvoiceReadConfig,
    ParentConfigurationRefresh,
    SEPHORA_AGE_BUCKETS,
    SephoraOnboardingCaptureError,
    capture_sephora_onboarding_packet,
)
from source_capture.writer import write_local_source_capture_packet


_PRODUCT_URL = (
    "https://www.sephora.com/product/lip-sleeping-mask-P420652"
    "?country_switch=us&lang=en"
)
_REVIEW_TOKEN = "review-read-token"
_QUESTION_TOKEN = "question-read-token"


def _rendered_dom(*, link_store_product_id: str = "P420652") -> str:
    link_store = {
        "page": {
            "product": {
                "productId": link_store_product_id,
                "currentSku": {"skuId": "2961324"},
                "regularChildSkus": [
                    {"skuId": "1966258"},
                    {"skuId": "2902831"},
                ],
                # The old generic configuration is intentionally present. It is
                # not the rendered live age-filter authority.
                "reviewFilters": [
                    {
                        "id": "age",
                        "values": ["13-17", "18-24", "25-34", "35-44", "45-54", "Over54"],
                    }
                ],
            }
        }
    }
    config = {
        "bvApi_rwdRating_desktop_read": {
            "host": "api.bazaarvoice.com",
            "version": "5.4",
            "token": _REVIEW_TOKEN,
        },
        "bvApi_rwdQandA_desktop_read": {
            "host": "api.bazaarvoice.com",
            "version": "5.4",
            "token": _QUESTION_TOKEN,
        },
    }
    return (
        '<script id="linkStore" type="text/json">'
        + json.dumps(link_store, separators=(",", ":"))
        + "</script><script>Sephora.configurationSettings="
        + json.dumps(config, separators=(",", ":"))
        + ";</script>"
    )


def _parent_packet(
    root: DataLakeRoot,
    tmp_path: Path,
    *,
    link_store_product_id: str = "P420652",
) -> str:
    html = _rendered_dom(link_store_product_id=link_store_product_id)
    source = tmp_path / f"parent-{link_store_product_id}.html"
    source.write_text(html, encoding="utf-8")
    result = write_local_source_capture_packet(
        data_root=root,
        input_files=[source],
        source_family="retail_pdp",
        source_surface="cloakbrowser_snapshot",
        source_locator=known_fact(_PRODUCT_URL),
        decision_question="test Sephora parent",
        capture_context="rendered Sephora sample packet",
    )
    return result.packet.packet_id


def _content_parent_packet(root: DataLakeRoot, tmp_path: Path) -> str:
    content = {
        "record_kind": "retail_pdp_sephora_aggregate_content",
        "schema_version": "retail_pdp_sephora_aggregate_content_v4",
        "source_url": _PRODUCT_URL,
        "rows": [
            {
                "source_visible_fields": {
                    "product_id": "P420652",
                    "sku": "2961324",
                }
            },
            {
                "source_visible_fields": {
                    "product_id": "P420652",
                    "sku": "1966258",
                }
            },
        ],
    }
    source = tmp_path / "parent-content.json"
    source.write_text(json.dumps(content), encoding="utf-8")
    metadata = tmp_path / "parent-metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "pin_confirmed": True,
                "country_code_requested": "US",
                "currency_code_requested": "USD",
                "access_blocked": False,
            }
        ),
        encoding="utf-8",
    )
    result = write_local_source_capture_packet(
        data_root=root,
        input_files=[source, metadata],
        source_family="retail_pdp",
        source_surface="sephora_pdp_content",
        source_locator=known_fact(_PRODUCT_URL),
        decision_question="test canonical Sephora content parent",
        capture_context="canonical aggregate-content Sephora sample packet",
    )
    return result.packet.packet_id


def _configuration_source_packet(root: DataLakeRoot, tmp_path: Path) -> str:
    source_url = "https://www.sephora.com/brand/test?country_switch=us"
    rendered = tmp_path / "configuration-source.html"
    rendered.write_text(_rendered_dom(), encoding="utf-8")
    metadata = tmp_path / "configuration-source-metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "pin_confirmed": True,
                "country_code_requested": "US",
                "currency_code_requested": "USD",
                "access_blocked": False,
            }
        ),
        encoding="utf-8",
    )
    result = write_local_source_capture_packet(
        data_root=root,
        input_files=[rendered, metadata],
        source_family="retail_pdp",
        source_surface="sephora_brand_grid",
        source_locator=known_fact(source_url),
        decision_question="test preserved Sephora configuration source",
        capture_context="hash-verified Sephora US configuration source",
    )
    return result.packet.packet_id


def _question_document() -> dict:
    return {
        "HasErrors": False,
        "TotalResults": 1390,
        "Results": [
            {
                "Id": "q1",
                "ProductId": "P420652",
                "QuestionSummary": "First?",
                "QuestionDetails": "First question details",
                "TotalAnswerCount": 2,
                "SubmissionTime": "2026-01-01T00:00:00Z",
                "UserNickname": "one",
            },
            {
                "Id": "q2",
                "ProductId": "P429952",
                "QuestionSummary": "Second?",
                "QuestionDetails": "Second question details",
                "TotalAnswerCount": 1,
                "SubmissionTime": "2026-01-02T00:00:00Z",
                "UserNickname": "two",
            },
        ],
        "Includes": {
            "Answers": {
                "a1": {"Id": "a1", "AnswerText": "A"},
                "a2": {"Id": "a2", "AnswerText": "B"},
                "a3": {"Id": "a3", "AnswerText": "C"},
            }
        },
    }


def _review_row(
    review_id: str,
    submission_time: str,
    text: str,
    *,
    product_id: str = "P420652",
) -> dict:
    return {
        "Id": review_id,
        "ProductId": product_id,
        "Title": f"Title {review_id}",
        "ReviewText": text,
        "Rating": 5,
        "SubmissionTime": submission_time,
        "UserNickname": f"user-{review_id}",
        "IsRecommended": True,
        "IsVerifiedBuyer": False,
        "TotalFeedbackCount": 10,
        "TotalPositiveFeedbackCount": 9,
        "TotalNegativeFeedbackCount": 1,
        "ContextDataValues": {
            "IncentivizedReview": {"Value": "False"},
            "ageRange": {"Value": "30s"},
        },
        "Photos": [],
        "Videos": [],
        "UnexpectedValuableField": f"preserve-{review_id}",
    }


def _statistics_product(
    *,
    total: int = 14327,
    age_values: list[dict] | None = None,
) -> dict:
    if age_values is None:
        age_values = [
            {"Value": "20s", "Count": 244},
            {"Value": "30s", "Count": 338},
            {"Value": "40s", "Count": 130},
            {"Value": "50s", "Count": 563},
        ]
    return {
        "Id": "P420652",
        "ReviewStatistics": {
            "TotalReviewCount": 22000,
            "AverageOverallRating": 4.3,
            "RecommendedCount": 15000,
            "NotRecommendedCount": 2000,
            "RatingDistribution": [{"RatingValue": 5, "Count": 15000}],
        },
        "FilteredReviewStatistics": {
            "TotalReviewCount": total,
            "AverageOverallRating": 4.4,
            "RecommendedCount": 11000,
            "NotRecommendedCount": 1200,
            "RatingDistribution": [{"RatingValue": 5, "Count": 11000}],
            "ContextDataDistribution": {
                "ageRange": {"Values": age_values},
                "skinType": {
                    "Values": [
                        {"Value": "combination", "Count": 900},
                        {"Value": "dry", "Count": 700},
                    ]
                },
                "skinConcerns": {
                    "Values": [{"Value": "dryness", "Count": 400}]
                },
                "eyeColor": {
                    "Values": [{"Value": "brown", "Count": 100}]
                },
            },
        },
    }


def _fake_fetcher(
    *,
    corrupt_artifact: str | None = None,
    questions_empty: bool = False,
    reviews_empty: bool = False,
):
    def fetch(
        spec: ApiRequestSpec,
        config: BazaarvoiceReadConfig,
        _timeout_seconds: float,
        _max_bytes: int,
    ) -> ApiResponse:
        assert config.host == "api.bazaarvoice.com"
        if spec.config_kind == "questions":
            assert config.token == _QUESTION_TOKEN
            document = (
                {
                    "HasErrors": False,
                    "TotalResults": 0,
                    "Results": [],
                    "Includes": {"Answers": {}},
                }
                if questions_empty
                else _question_document()
            )
        else:
            assert config.token == _REVIEW_TOKEN
            assert (
                "Filter",
                "ContextDataValue_IncentivizedReview:eq:False",
            ) in spec.parameters
            if spec.artifact_name == "reviews_non_incentivized_most_helpful_offset_000.json":
                assert ("Sort", "TotalPositiveFeedbackCount:desc") in spec.parameters
                assert ("Include", "Products") in spec.parameters
                assert ("Stats", "Reviews") in spec.parameters
                assert ("FilteredStats", "Reviews") in spec.parameters
                document = (
                    {
                        "HasErrors": False,
                        "TotalResults": 0,
                        "Results": [],
                        "Includes": {},
                    }
                    if reviews_empty
                    else {
                        "HasErrors": False,
                        "TotalResults": 14327,
                        "Results": [
                            _review_row(
                                "h1",
                                "2026-07-18T00:00:00Z",
                                "Helpful one",
                            ),
                            _review_row(
                                "h2",
                                "2026-07-01T00:00:00Z",
                                "Helpful two",
                                product_id="2901072",
                            ),
                        ],
                        "Includes": {
                            "Products": {"P420652": _statistics_product()}
                        },
                    }
                )
            else:
                assert spec.artifact_name.startswith(
                    "reviews_non_incentivized_most_recent_offset_"
                )
                assert ("Sort", "SubmissionTime:desc") in spec.parameters
                offset = int(dict(spec.parameters)["Offset"])
                pages = (
                    {0: []}
                    if reviews_empty
                    else {
                        0: [
                            _review_row(
                                "r1", "2026-07-19T00:00:00Z", "Recent one"
                            ),
                            _review_row(
                                "r2", "2026-07-10T00:00:00Z", "Recent two"
                            ),
                        ],
                        2: [
                            _review_row(
                                "r3", "2026-06-25T00:00:00Z", "Recent three"
                            ),
                            _review_row(
                                "r4", "2026-06-19T00:00:00Z", "Boundary"
                            ),
                        ],
                    }
                )
                document = {
                    "HasErrors": False,
                    "TotalResults": 0 if reviews_empty else 14327,
                    "Results": pages[offset],
                }
        if spec.artifact_name == corrupt_artifact:
            body = b"{invalid-json"
        else:
            body = json.dumps(document, separators=(",", ":")).encode("utf-8")
        return ApiResponse(
            status=200,
            reason="OK",
            body=body,
            content_type="application/json",
            captured_at="2026-07-20T00:00:00Z",
        )

    return fetch


def _artifact_json(loaded, suffix: str) -> dict:
    preserved = next(
        item
        for item in loaded.manifest["preserved_files"]
        if item["relative_packet_path"].endswith(suffix)
    )
    return json.loads(loaded.bodies[preserved["file_id"]].decode("utf-8"))


def test_success_uses_three_roles_and_promotes_filtered_statistics(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=_fake_fetcher(),
    )

    assert exit_code == 0
    loaded = root.load_raw_packet(result["packet_id"])
    assert loaded.manifest["source_surface"] == "sephora_bazaarvoice_onboarding"
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    assert summary["record_kind"] == "sephora_bazaarvoice_onboarding_summary_v4"
    reviews = summary["reviews"]
    assert reviews["exact_non_incentivized_total"] == 14327
    assert reviews["statistics"]["filtered"]["AverageOverallRating"] == 4.4
    assert reviews["statistics"]["unfiltered"]["TotalReviewCount"] == 22000
    demographics = reviews["demographics"]
    assert demographics["age_display_labels"] == list(SEPHORA_AGE_BUCKETS)
    assert demographics["declared_age_subset_total"] == 1275
    assert demographics["declared_age_coverage_pct"] == 8.9
    assert demographics["without_declared_age_pct"] == 91.1
    assert demographics["age_breakdown"] == [
        {
            "bucket": "20s",
            "count": 244,
            "share_of_declared_age_subset_pct": 19.14,
            "share_of_all_non_incentivized_reviews_pct": 1.7,
        },
        {
            "bucket": "30s",
            "count": 338,
            "share_of_declared_age_subset_pct": 26.51,
            "share_of_all_non_incentivized_reviews_pct": 2.36,
        },
        {
            "bucket": "40s",
            "count": 130,
            "share_of_declared_age_subset_pct": 10.2,
            "share_of_all_non_incentivized_reviews_pct": 0.91,
        },
        {
            "bucket": "50s +",
            "count": 563,
            "share_of_declared_age_subset_pct": 44.16,
            "share_of_all_non_incentivized_reviews_pct": 3.93,
        },
    ]
    assert demographics["skin_type_distribution"] == [
        {"value": "combination", "count": 900},
        {"value": "dry", "count": 700},
    ]
    assert demographics["skin_concern_distribution"] == [
        {"value": "dryness", "count": 400}
    ]
    # Other distributions (eyeColor) stay raw-only.
    assert "eyeColor" not in json.dumps(demographics)

    assert reviews["most_helpful"]["captured_review_rows"] == 2
    assert reviews["most_helpful"]["captured_review_bodies"] == 2
    recent = reviews["most_recent_30d"]
    assert recent["last_seen_review_id"] == "r1"
    assert recent["captured_page_count"] == 2
    assert recent["captured_page_rows"] == 4
    assert recent["within_window_rows"] == 3
    assert recent["coverage_status"] == "covered_through_cutoff"
    assert recent["oldest_source_date"] == "2026-06-19T00:00:00Z"

    # Compact, body-free summary rows; bodies stay only in raw responses.
    helpful_row = reviews["most_helpful"]["review_inventory"][0]
    assert helpful_row["body_present"] is True
    assert "review_text" not in helpful_row
    assert "Helpful one" not in json.dumps(summary)
    assert "First question details" not in json.dumps(summary)
    assert reviews["raw_review_field_inventory"][
        "additional_source_fields_carried"
    ] == ["UnexpectedValuableField"]
    assert reviews["review_product_identity"][
        "historical_or_unlisted_review_product_ids"
    ] == ["2901072"]
    assert summary["questions"]["total_questions"] == 1390
    assert summary["questions"]["captured_question_rows"] == 2
    assert summary["questions"]["captured_included_answer_rows"] == 3
    assert summary["questions"]["question_product_identity"] == {
        "requested_product_group_id": "P420652",
        "observed_question_product_ids": ["P420652", "P429952"],
        "provider_collection_product_ids": [
            "2901072",
            "P420652",
            "P429952",
        ],
    }
    assert summary["row_accounting"]["answers_equal"] is True
    assert summary["row_accounting"]["most_helpful_row_order_equal"] is True
    assert summary["row_accounting"]["most_recent_row_order_equal"] is True
    qualification = summary["content_qualification"]
    assert qualification["status"] == "passed"
    assert qualification["three_response_roles_present"] is True
    assert qualification["combined_statistics_present"] is True
    assert qualification["age_bucket_vocabulary_exact"] is True
    assert qualification["recent_window_coverage_proven"] is True
    assert qualification["summary_duplicates_review_or_answer_bodies"] is False

    names = {
        Path(item["original_path"]).name
        for item in loaded.manifest["preserved_files"]
    }
    assert names == {
        "questions_most_answers_offset_000.json",
        "reviews_non_incentivized_most_helpful_offset_000.json",
        "reviews_non_incentivized_most_recent_offset_00000.json",
        "reviews_non_incentivized_most_recent_offset_00002.json",
        "sephora_request_manifest.json",
        "sephora_onboarding_summary.json",
    }
    persisted = b"".join(loaded.bodies.values())
    assert _REVIEW_TOKEN.encode() not in persisted
    assert _QUESTION_TOKEN.encode() not in persisted


def test_content_parent_succeeds_with_injected_live_configuration_refresh(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _content_parent_packet(root, tmp_path)
    rendered_dom = _rendered_dom()
    refresh_calls: list[tuple[str, float]] = []

    def refresh(product_url: str, timeout_seconds: float) -> ParentConfigurationRefresh:
        refresh_calls.append((product_url, timeout_seconds))
        return ParentConfigurationRefresh(
            requested_url=product_url,
            final_url=product_url,
            rendered_dom=rendered_dom,
            rendered_dom_sha256=hashlib.sha256(
                rendered_dom.encode("utf-8")
            ).hexdigest(),
            pin_confirmed=True,
        )

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        timeout_seconds=7.5,
        fetcher=_fake_fetcher(),
        configuration_refresher=refresh,
    )

    assert exit_code == 0
    assert refresh_calls == [(_PRODUCT_URL, 7.5)]
    parent = root.load_raw_packet(parent_id)
    parent_file = parent.manifest["preserved_files"][0]
    parent_metadata = parent.manifest["preserved_files"][1]
    loaded = root.load_raw_packet(result["packet_id"])
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    configuration = summary["parent_packet"]["configuration"]
    assert configuration == {
        "mode": "live_target_bound_refresh",
        "requested_url": _PRODUCT_URL,
        "final_url": _PRODUCT_URL,
        "rendered_dom_sha256": hashlib.sha256(
            rendered_dom.encode("utf-8")
        ).hexdigest(),
        "pin_confirmed": True,
        "content_parent_file_id": parent_file["file_id"],
        "content_parent_file_sha256": parent_file["sha256"],
        "content_parent_market_metadata_file_id": parent_metadata["file_id"],
        "content_parent_market_metadata_sha256": parent_metadata["sha256"],
        "content_parent_market": "US/USD",
        "credential_posture": (
            "page-declared read tokens used only in memory and not persisted"
        ),
    }
    persisted = b"".join(loaded.bodies.values())
    assert _REVIEW_TOKEN.encode() not in persisted
    assert _QUESTION_TOKEN.encode() not in persisted


def test_content_parent_accepts_hash_verified_sephora_configuration_source(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _content_parent_packet(root, tmp_path)
    configuration_source_id = _configuration_source_packet(root, tmp_path)

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=_fake_fetcher(),
        configuration_source_packet_id=configuration_source_id,
    )

    assert exit_code == 0
    loaded = root.load_raw_packet(result["packet_id"])
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    configuration = summary["parent_packet"]["configuration"]
    assert configuration["mode"] == "preserved_sephora_configuration_source"
    assert configuration["configuration_source_packet_id"] == configuration_source_id
    assert configuration["configuration_scope"] == "tenant_read_configuration_only"
    assert configuration["configuration_source_market"] == "US"
    assert configuration["content_parent_market"] == "US/USD"
    persisted = b"".join(loaded.bodies.values())
    assert _REVIEW_TOKEN.encode() not in persisted
    assert _QUESTION_TOKEN.encode() not in persisted


def test_zero_question_source_result_is_preserved_as_declared_absence(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=_fake_fetcher(questions_empty=True),
    )

    assert exit_code == 0
    loaded = root.load_raw_packet(result["packet_id"])
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    assert summary["questions"]["total_questions"] == 0
    assert summary["questions"]["captured_question_rows"] == 0
    assert summary["questions"]["question_product_identity"][
        "observed_question_product_ids"
    ] == []


def test_zero_review_source_result_is_preserved_as_declared_absence(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=_fake_fetcher(questions_empty=True, reviews_empty=True),
    )

    assert exit_code == 0
    loaded = root.load_raw_packet(result["packet_id"])
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    assert summary["reviews"]["exact_non_incentivized_total"] == 0
    assert summary["reviews"]["most_helpful"]["captured_review_rows"] == 0
    assert summary["reviews"]["most_recent_30d"]["coverage_status"] == (
        "source_exhausted"
    )
    assert summary["content_qualification"]["combined_statistics_present"] is False
    assert summary["content_qualification"]["combined_statistics_status"] == (
        "not_applicable_source_declared_zero_reviews"
    )
    assert summary["content_qualification"]["age_bucket_vocabulary_exact"] is None
    assert (
        summary["reviews"]["most_recent_30d"]["pages"][0]["oldest_submission_time"]
        is None
    )


def test_zero_question_total_with_rows_fails_adaptation_with_raw_fallback(
    tmp_path: Path,
) -> None:
    def fetch(
        spec: ApiRequestSpec,
        config: BazaarvoiceReadConfig,
        timeout_seconds: float,
        max_bytes: int,
    ) -> ApiResponse:
        response = _fake_fetcher()(spec, config, timeout_seconds, max_bytes)
        if spec.artifact_name == "questions_most_answers_offset_000.json":
            document = json.loads(response.body)
            document["TotalResults"] = 0
            response = ApiResponse(
                status=200,
                reason="OK",
                body=json.dumps(document).encode("utf-8"),
                content_type="application/json",
                captured_at=response.captured_at,
            )
        return response

    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)
    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=fetch,
    )
    assert exit_code == 5
    loaded = root.load_raw_packet(result["packet_id"])
    failure = _artifact_json(loaded, "sephora_adaptation_failure.json")
    assert (
        "questions response declares zero TotalResults but returned rows"
        in failure["failure"]["error"]
    )


def test_zero_recent_total_with_rows_fails_adaptation_with_raw_fallback(
    tmp_path: Path,
) -> None:
    def fetch(
        spec: ApiRequestSpec,
        config: BazaarvoiceReadConfig,
        timeout_seconds: float,
        max_bytes: int,
    ) -> ApiResponse:
        response = _fake_fetcher()(spec, config, timeout_seconds, max_bytes)
        if spec.artifact_name.startswith(
            "reviews_non_incentivized_most_recent_offset_"
        ):
            document = json.loads(response.body)
            document["TotalResults"] = 0
            response = ApiResponse(
                status=200,
                reason="OK",
                body=json.dumps(document).encode("utf-8"),
                content_type="application/json",
                captured_at=response.captured_at,
            )
        return response

    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)
    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=fetch,
    )
    assert exit_code == 5
    loaded = root.load_raw_packet(result["packet_id"])
    failure = _artifact_json(loaded, "sephora_adaptation_failure.json")
    assert (
        "declares zero TotalResults but returned rows"
        in failure["failure"]["error"]
    )


def test_content_parent_refresh_product_mismatch_fails_before_api_fetch(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _content_parent_packet(root, tmp_path)
    api_calls = 0

    def fetch(*_args, **_kwargs):
        nonlocal api_calls
        api_calls += 1
        raise AssertionError("must not fetch Bazaarvoice")

    def refresh(product_url: str, _timeout_seconds: float) -> ParentConfigurationRefresh:
        return ParentConfigurationRefresh(
            requested_url=product_url,
            final_url=product_url.replace("P420652", "P999999"),
            rendered_dom=_rendered_dom(link_store_product_id="P999999"),
            rendered_dom_sha256="mismatch-is-rejected-before-persistence",
            pin_confirmed=True,
        )

    with pytest.raises(
        SephoraOnboardingCaptureError,
        match=(
            "configuration refresh product mismatch: "
            "parent=P420652, final=P999999"
        ),
    ):
        capture_sephora_onboarding_packet(
            data_root=root,
            parent_packet_id=parent_id,
            fetcher=fetch,
            configuration_refresher=refresh,
        )

    assert api_calls == 0
    assert root.list_committed_packet_ids() == [parent_id]


def test_missing_combined_statistics_fails_adaptation_with_raw_fallback(
    tmp_path: Path,
) -> None:
    def fetch(
        spec: ApiRequestSpec,
        config: BazaarvoiceReadConfig,
        timeout_seconds: float,
        max_bytes: int,
    ) -> ApiResponse:
        response = _fake_fetcher()(spec, config, timeout_seconds, max_bytes)
        if spec.artifact_name == (
            "reviews_non_incentivized_most_helpful_offset_000.json"
        ):
            document = json.loads(response.body)
            document.pop("Includes", None)
            response = ApiResponse(
                status=200,
                reason="OK",
                body=json.dumps(document).encode("utf-8"),
                content_type="application/json",
                captured_at=response.captured_at,
            )
        return response

    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)
    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=fetch,
    )
    assert exit_code == 5
    loaded = root.load_raw_packet(result["packet_id"])
    failure = _artifact_json(loaded, "sephora_adaptation_failure.json")
    assert failure["record_kind"] == (
        "sephora_bazaarvoice_onboarding_adaptation_failure_v4"
    )
    assert "Includes.Products" in failure["failure"]["error"]


def test_adaptation_failure_commits_every_raw_response_as_fallback(
    tmp_path: Path,
) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=_fake_fetcher(
            corrupt_artifact=(
                "reviews_non_incentivized_most_helpful_offset_000.json"
            )
        ),
    )

    assert exit_code == 5
    loaded = root.load_raw_packet(result["packet_id"])
    names = [
        Path(item["original_path"]).name
        for item in loaded.manifest["preserved_files"]
    ]
    # 2 base + 2 recent responses + manifest + failure artifact.
    assert len([name for name in names if name.endswith(".json")]) == 6
    assert "sephora_adaptation_failure.json" in names
    failure = _artifact_json(loaded, "sephora_adaptation_failure.json")
    assert failure["raw_failure_fallback"] == {
        "expected_response_count": 4,
        "preserved_response_count": 4,
        "status": "all_responses_preserved",
    }
    assert any(
        "exact raw API response bytes are preserved"
        in limitation
        for limitation in loaded.manifest["limitations"]
    )


def test_recent_window_stops_on_cumulative_source_exhaustion(tmp_path: Path) -> None:
    """When every non-incentivized review is inside the 30-day window and the
    corpus spans more than one page, acquisition must stop on cumulative source
    exhaustion. Detecting exhaustion only per page would paginate past the end,
    capture an empty page, and misreport a complete capture as a summary
    failure."""
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path)

    recent_pages = {
        0: [
            _review_row("r1", "2026-07-19T00:00:00Z", "Recent one"),
            _review_row("r2", "2026-07-15T00:00:00Z", "Recent two"),
        ],
        2: [
            _review_row("r3", "2026-07-05T00:00:00Z", "Recent three"),
        ],
    }

    def fetch(
        spec: ApiRequestSpec,
        config: BazaarvoiceReadConfig,
        _timeout_seconds: float,
        _max_bytes: int,
    ) -> ApiResponse:
        if spec.config_kind == "questions":
            document: dict = _question_document()
        elif spec.artifact_name == "reviews_non_incentivized_most_helpful_offset_000.json":
            document = {
                "HasErrors": False,
                "TotalResults": 3,
                "Results": [_review_row("h1", "2026-07-18T00:00:00Z", "Helpful one")],
                "Includes": {
                    "Products": {
                        "P420652": _statistics_product(
                            total=3,
                            age_values=[{"Value": "30s", "Count": 2}],
                        )
                    }
                },
            }
        else:
            assert spec.artifact_name.startswith(
                "reviews_non_incentivized_most_recent_offset_"
            )
            offset = int(dict(spec.parameters)["Offset"])
            document = {
                "HasErrors": False,
                "TotalResults": 3,
                "Results": recent_pages[offset],
            }
        body = json.dumps(document, separators=(",", ":")).encode("utf-8")
        return ApiResponse(
            status=200,
            reason="OK",
            body=body,
            content_type="application/json",
            captured_at="2026-07-20T00:00:00Z",
        )

    exit_code, result = capture_sephora_onboarding_packet(
        data_root=root,
        parent_packet_id=parent_id,
        review_page_limit=2,
        fetcher=fetch,
    )

    assert exit_code == 0
    loaded = root.load_raw_packet(result["packet_id"])
    summary = _artifact_json(loaded, "sephora_onboarding_summary.json")
    recent = summary["reviews"]["most_recent_30d"]
    assert recent["captured_page_count"] == 2
    assert recent["captured_page_rows"] == 3
    assert recent["within_window_rows"] == 3
    assert recent["source_exhausted"] is True
    assert recent["coverage_status"] == "source_exhausted"
    assert summary["content_qualification"]["recent_window_coverage_proven"] is True

    names = {
        Path(item["original_path"]).name
        for item in loaded.manifest["preserved_files"]
    }
    assert "reviews_non_incentivized_most_recent_offset_00000.json" in names
    assert "reviews_non_incentivized_most_recent_offset_00002.json" in names
    # No past-the-end empty page is ever requested once the corpus is exhausted.
    assert "reviews_non_incentivized_most_recent_offset_00003.json" not in names


def test_parent_product_identity_mismatch_fails_before_fetch(tmp_path: Path) -> None:
    root = DataLakeRoot.for_test(tmp_path / "lake")
    parent_id = _parent_packet(root, tmp_path, link_store_product_id="P999999")
    calls = 0

    def fetch(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("must not fetch")

    with pytest.raises(SephoraOnboardingCaptureError, match="parent product mismatch"):
        capture_sephora_onboarding_packet(
            data_root=root,
            parent_packet_id=parent_id,
            fetcher=fetch,
        )
    assert calls == 0
