from source_capture.google_serp_queue_policy import (
    build_product_scoped_price_query,
    competitor_name_problem,
    decide_block_recovery,
    evaluate_queue_job,
)


def test_presence_and_surfaced_debris_fail_closed() -> None:
    for name in (
        "bad",
        "30 levels whiter. 7. 4. Why",
        "I brush my teeth before",
        "86 Reddit-Picked",
    ):
        assert competitor_name_problem(name)
        decision = evaluate_queue_job(
            {
                "selected_type": "rival",
                "selected_rung": "presence",
                "selected_name": name,
                "shape": "vs_harvested_rival",
            }
        )
        assert not decision.eligible


def test_competitor_price_requires_product_scope() -> None:
    decision = evaluate_queue_job(
        {
            "selected_type": "rival",
            "selected_rung": "candidate",
            "selected_name": "Amazon Basics",
            "shape": "j5_competitor_price",
            "query": "amazon basics price",
        }
    )
    assert decision.reason == "competitor_price_query_not_product_scoped"
    assert (
        build_product_scoped_price_query(
            name="Amazon Basics", product_scope="moisturizing cream"
        )
        == "Amazon Basics moisturizing cream price"
    )


def test_product_scoped_candidate_remains_eligible() -> None:
    decision = evaluate_queue_job(
        {
            "selected_type": "rival",
            "selected_rung": "candidate",
            "selected_name": "Amazon Basics",
            "shape": "j5_competitor_price",
            "product_scope": "moisturizing cream",
        }
    )
    assert decision.eligible


def test_block_transitions_to_operator_visible_persistent_chrome() -> None:
    decision = decide_block_recovery(
        lower_route_blocked=True,
        realchrome_fallback_enabled=True,
        dedicated_logged_out_cdp_ready=True,
        operator_visible=True,
    )
    assert decision.route == "persistent_realchrome"


def test_block_fails_loud_when_persistent_route_is_not_ready() -> None:
    decision = decide_block_recovery(
        lower_route_blocked=True,
        realchrome_fallback_enabled=True,
        dedicated_logged_out_cdp_ready=False,
        operator_visible=True,
    )
    assert decision.route == "paused_fallback_unavailable"
