import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from runners.serp_phase2_decision_contract import (
    ContractError,
    evaluate_entry,
    validate_settlement,
)


RUNNER = (
    Path(__file__).resolve().parents[2]
    / "runners"
    / "serp_phase2_decision_contract.py"
)


def _source(
    source_id: str,
    *,
    entity_key: str = "brand|product|edp",
    subject_entity_key: str = "subject|product|edp",
    author_id: str | None = None,
    thread_id: str | None = None,
    venue: str | None = None,
    posture: str = "first_hand",
    stance_bearing: bool = True,
    score: int = 5,
    rank_in_thread: int = 1,
) -> dict:
    if author_id is None:
        return {
            "source_id": source_id,
            "surface_class": "serp_rendered_snippet",
            "entity_key": entity_key,
            "subject_entity_key": subject_entity_key,
        }
    return {
        "source_id": source_id,
        "surface_class": "complaint_body",
        "entity_key": entity_key,
        "subject_entity_key": subject_entity_key,
        "author_id": author_id,
        "thread_id": thread_id or "thread-1",
        "venue": venue or "r/example",
        "posture": posture,
        "stance_bearing": stance_bearing,
        "engagement": {
            "score": score,
            "rank_in_thread": rank_in_thread,
        },
    }


def _value_response() -> dict:
    return {
        "customer_gain": "similar scent at a lower entry price",
        "observed_sacrifice": "shorter full-wear performance",
        "value_lever": "proof",
        "value_action": "strengthen_proof",
        "proof_needed": "controlled full-wear comparison",
        "price_action": "none",
        "response_kind": "add_or_prove_value",
    }


def _entry(
    *,
    name: str = "Example Product",
    entity_key: str = "brand|product|edp",
    subject_entity_key: str = "subject|product|edp",
    comments: list[dict] | None = None,
    attempts: int = 0,
    action: str = "use_in_decision",
    confidence: str = "corroborated",
    decision_ready: bool = True,
    price: dict | None = None,
    value_response: dict | None = None,
) -> dict:
    comments = comments or [
        _source(
            "comment-1",
            author_id="author-1",
            thread_id="thread-1",
            entity_key=entity_key,
            subject_entity_key=subject_entity_key,
        ),
        _source(
            "comment-2",
            author_id="author-2",
            thread_id="thread-2",
            venue="r/another",
            rank_in_thread=2,
            entity_key=entity_key,
            subject_entity_key=subject_entity_key,
        ),
    ]
    entry = {
        "name": name,
        "entity_key": entity_key,
        "subject_entity_key": subject_entity_key,
        "rung": "finding_grade",
        "sources": [
            _source(
                "serp-1",
                entity_key=entity_key,
                subject_entity_key=subject_entity_key,
            ),
            *comments,
        ],
        "automatic_validation_attempts": attempts,
        "decision": {
            "action": action,
            "confidence": confidence,
            "decision_ready": decision_ready,
        },
    }
    if decision_ready:
        entry["value_response"] = value_response or _value_response()
    elif value_response is not None:
        entry["value_response"] = value_response
    if price is not None:
        entry["price"] = price
    return entry


def _summary(*, decision_ready: list[str] | None = None, **overrides) -> dict:
    result = {
        "entry_count": 1,
        "decision_ready_names": (
            ["Example Product"] if decision_ready is None else decision_ready
        ),
        "validate_once_names": [],
        "watch_names": [],
        "parked_names": [],
        "identity_correction_names": [],
    }
    result.update(overrides)
    return result


def _payload(entry: dict, *, summary: dict | None = None) -> dict:
    return {
        "schema_version": "serp_phase2_decision_settlement_v0",
        "subject": {"name": "Subject", "entity_key": "subject|product|edp"},
        "entries": [entry],
        "return_probes": [
            {
                "job_id": "return-1",
                "entry_entity_key": entry["entity_key"],
                "partial": False,
                "automatic_validation": False,
            }
        ],
        "capture_accounting": {"partial_probes": 0},
        "summary": summary or _summary(),
    }


def test_two_independent_first_hand_authors_are_decision_ready() -> None:
    receipt = validate_settlement(_payload(_entry()))

    assert receipt["summary"] == _summary()
    result = receipt["results"][0]
    assert result["decision_ready"] is True
    assert result["first_hand_authors"] == 2
    assert result["threads"] == 2
    assert result["venues"] == 2
    assert result["best_comment_rank"] == 1


def test_variant_mismatch_fails_before_an_otherwise_complete_value_response() -> None:
    entry = _entry()
    entry["sources"][0]["entity_key"] = "brand|product|intense"

    with pytest.raises(ContractError, match="identity_mismatch"):
        validate_settlement(_payload(entry))


def test_top_ranked_single_author_routes_to_one_validation_not_decision() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        action="validate_once",
        confidence="weak",
        decision_ready=False,
    )

    result = evaluate_entry(entry)

    assert result["action"] == "validate_once"
    assert result["decision_ready"] is False
    assert result["confidence"] == "weak"


def test_low_ranked_single_author_waits_for_a_new_source() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=4)],
        action="watch_for_new_source",
        confidence="weak",
        decision_ready=False,
    )

    receipt = validate_settlement(
        _payload(
            entry,
            summary=_summary(
                decision_ready=[],
                watch_names=["Example Product"],
            ),
        )
    )

    assert receipt["results"][0]["action"] == "watch_for_new_source"


def test_top_ranked_secondhand_comment_does_not_trigger_validation() -> None:
    entry = _entry(
        comments=[
            _source(
                "comment-1",
                author_id="author-1",
                posture="secondhand",
                rank_in_thread=1,
            )
        ],
        action="watch_for_new_source",
        confidence="weak",
        decision_ready=False,
    )

    result = evaluate_entry(entry)

    assert result["first_hand_authors"] == 0
    assert result["action"] == "watch_for_new_source"


def test_meta_comment_rank_cannot_promote_a_different_weak_comment() -> None:
    entry = _entry(
        comments=[
            _source(
                "meta",
                author_id="meta-author",
                posture="secondhand",
                stance_bearing=False,
                score=128,
                rank_in_thread=1,
            ),
            _source(
                "product",
                author_id="product-author",
                score=1,
                rank_in_thread=4,
            ),
        ],
        action="watch_for_new_source",
        confidence="weak",
        decision_ready=False,
    )

    result = evaluate_entry(entry)

    assert result["max_comment_score"] == 128
    assert result["best_comment_rank"] == 4
    assert result["action"] == "watch_for_new_source"


def test_same_author_repeated_does_not_create_independent_support() -> None:
    entry = _entry(
        comments=[
            _source("comment-1", author_id="author-1", thread_id="thread-1"),
            _source("comment-2", author_id="author-1", thread_id="thread-2"),
        ],
        action="validate_once",
        confidence="weak",
        decision_ready=False,
    )

    result = evaluate_entry(entry)

    assert result["first_hand_authors"] == 1
    assert result["decision_ready"] is False


def test_candidate_rung_cannot_become_decision_ready_from_comments_alone() -> None:
    entry = _entry(
        action="watch_for_new_source",
        confidence="corroborated",
        decision_ready=False,
    )
    entry["rung"] = "candidate"

    result = evaluate_entry(entry)

    assert result["surface_independent"] is True
    assert result["action"] == "watch_for_new_source"
    assert result["decision_ready"] is False


def test_unknown_variant_token_fails_identity_binding() -> None:
    entry = _entry(entity_key="brand|product|unknown")

    with pytest.raises(ContractError, match="entity_key_unbound"):
        validate_settlement(_payload(entry))


def test_source_subject_variant_mismatch_fails_closed() -> None:
    entry = _entry()
    entry["sources"][1]["subject_entity_key"] = "subject|product|extrait"

    with pytest.raises(ContractError, match="subject_identity_mismatch"):
        validate_settlement(_payload(entry))


def test_unbound_top_level_subject_key_fails_closed() -> None:
    payload = _payload(_entry())
    payload["subject"]["entity_key"] = "subject|product|unknown"

    with pytest.raises(ContractError, match="subject_entity_key_unbound"):
        validate_settlement(payload)


def test_unknown_variant_suffix_fails_subject_identity_binding() -> None:
    payload = _payload(_entry())
    payload["subject"]["entity_key"] = "subject|product|unknown_variant"

    with pytest.raises(ContractError, match="subject_entity_key_unbound"):
        validate_settlement(payload)


def test_invented_surface_class_cannot_create_independence() -> None:
    entry = _entry()
    entry["sources"][0]["surface_class"] = "invented_surface"

    with pytest.raises(ContractError, match="surface_class_invalid"):
        validate_settlement(_payload(entry))


def test_second_automatic_attempt_parks_and_repeat_is_deterministic() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )

    first = evaluate_entry(entry)
    second = evaluate_entry(deepcopy(entry))

    assert first == second
    assert first["action"] == "parked_after_no_confirmation"


def test_comment_without_engagement_fails_visible() -> None:
    entry = _entry()
    del entry["sources"][1]["engagement"]

    with pytest.raises(ContractError, match="comment_engagement_missing"):
        validate_settlement(_payload(entry))


def test_price_multiple_is_recomputed_from_exact_row_values() -> None:
    entry = _entry(
        price={
            "currency": "USD",
            "subject_price": 360.0,
            "subject_size": 70.0,
            "competitor_floor": 37.25,
            "competitor_size": 105.0,
            "subject_multiple": 14.50,
            "comparison_basis": "like_for_like",
            "floor_status": "cross_retailer_verified",
        }
    )

    receipt = validate_settlement(_payload(entry))

    assert receipt["results"][0]["subject_multiple"] == 14.50


def test_wrong_price_multiple_fails_seal() -> None:
    entry = _entry(
        price={
            "currency": "USD",
            "subject_price": 360.0,
            "subject_size": 70.0,
            "competitor_floor": 37.25,
            "competitor_size": 105.0,
            "subject_multiple": 14.69,
            "comparison_basis": "like_for_like",
            "floor_status": "cross_retailer_verified",
        }
    )

    with pytest.raises(ContractError, match="price_multiple_mismatch"):
        validate_settlement(_payload(entry))


def test_cross_concentration_price_is_allowed_only_when_labelled() -> None:
    entry = _entry(
        price={
            "currency": "USD",
            "subject_price": 360.0,
            "subject_size": 70.0,
            "competitor_floor": 45.0,
            "competitor_size": 50.0,
            "subject_multiple": 5.71,
            "comparison_basis": "cross_concentration",
            "floor_status": "brand_list",
        }
    )

    receipt = validate_settlement(_payload(entry))

    assert receipt["results"][0]["comparison_basis"] == "cross_concentration"


def test_decision_ready_entry_cannot_recommend_a_price_cut() -> None:
    value = _value_response()
    value["price_action"] = "discount"
    entry = _entry(value_response=value)

    with pytest.raises(ContractError, match="price_action_forbidden"):
        validate_settlement(_payload(entry))


def test_decision_ready_entry_requires_structured_value_response_kind() -> None:
    value = _value_response()
    value["response_kind"] = "price_competition"

    with pytest.raises(ContractError, match="response_kind_invalid"):
        validate_settlement(_payload(_entry(value_response=value)))


def test_weak_entry_cannot_carry_a_value_recommendation() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=4)],
        action="watch_for_new_source",
        confidence="weak",
        decision_ready=False,
        value_response={
            **_value_response(),
            "price_action": "discount",
        },
    )

    with pytest.raises(ContractError, match="value_response_forbidden"):
        validate_settlement(
            _payload(
                entry,
                summary=_summary(
                    decision_ready=[],
                    watch_names=["Example Product"],
                ),
            )
        )


def test_price_cut_cannot_be_smuggled_in_candidate_value_text() -> None:
    value = _value_response()
    value["candidate_value_add"] = "discount the product to win"

    with pytest.raises(ContractError, match="value_response_field_forbidden"):
        validate_settlement(_payload(_entry(value_response=value)))


def test_msrp_undercut_cannot_be_smuggled_in_candidate_value_text() -> None:
    value = _value_response()
    value["candidate_value_add"] = (
        "halve the MSRP and undercut Dossier permanently"
    )

    with pytest.raises(ContractError, match="value_response_field_forbidden"):
        validate_settlement(_payload(_entry(value_response=value)))


def test_value_action_must_match_the_value_only_lever() -> None:
    value = _value_response()
    value["value_action"] = "lower_price"

    with pytest.raises(ContractError, match="value_action_invalid"):
        validate_settlement(_payload(_entry(value_response=value)))


def test_summary_must_equal_the_computed_decisions() -> None:
    bad_summary = _summary(validate_once_names=["Example Product"])

    with pytest.raises(ContractError, match="summary_mismatch"):
        validate_settlement(_payload(_entry(), summary=bad_summary))


def test_partial_probe_count_must_name_every_partial_probe() -> None:
    payload = _payload(_entry())
    payload["capture_accounting"]["partial_probes"] = 1

    with pytest.raises(ContractError, match="partial_probe_count_mismatch"):
        validate_settlement(payload)


def test_weak_entry_cannot_receive_two_automatic_validation_probes() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            parked_names=["Example Product"],
        ),
    )
    payload["return_probes"] = [
        {
            "job_id": "return-1",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
            "licensing_action": "validate_once",
        },
        {
            "job_id": "return-2",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
            "licensing_action": "validate_once",
        },
    ]

    with pytest.raises(
        ContractError,
        match="automatic_validation_probe_limit_exceeded",
    ):
        validate_settlement(payload)


def test_attempt_count_must_match_named_automatic_probe() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            parked_names=["Example Product"],
        ),
    )

    with pytest.raises(
        ContractError,
        match="automatic_validation_attempts_mismatch",
    ):
        validate_settlement(payload)


def test_aliases_cannot_duplicate_one_product_identity() -> None:
    first = _entry(name="Product Alias One")
    second = _entry(name="Product Alias Two")
    payload = _payload(first)
    payload["entries"].append(second)
    payload["summary"] = {
        "entry_count": 2,
        "decision_ready_names": ["Product Alias One", "Product Alias Two"],
        "validate_once_names": [],
        "watch_names": [],
        "parked_names": [],
        "identity_correction_names": [],
    }

    with pytest.raises(ContractError, match="entity_key_duplicate"):
        validate_settlement(payload)


def test_missing_entry_entity_key_fails_closed_without_crashing() -> None:
    entry = _entry()
    payload = _payload(entry)
    del entry["entity_key"]

    with pytest.raises(ContractError, match="entity_key_missing"):
        validate_settlement(payload)


def test_padded_entity_key_reconciles_against_its_named_probe() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )
    entry["entity_key"] = "  brand|product|edp  "
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            parked_names=["Example Product"],
        ),
    )
    payload["return_probes"] = [
        {
            "job_id": "return-1",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
            "licensing_action": "validate_once",
        }
    ]

    receipt = validate_settlement(payload)

    assert receipt["results"][0]["entity_key"] == "brand|product|edp"
    assert receipt["results"][0]["action"] == "parked_after_no_confirmation"


def test_boolean_comment_score_is_not_a_valid_engagement_count() -> None:
    entry = _entry()
    entry["sources"][1]["engagement"]["score"] = True

    with pytest.raises(ContractError, match="comment_score_invalid"):
        validate_settlement(_payload(entry))


def test_automatic_validation_probe_requires_its_pre_probe_license() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            parked_names=["Example Product"],
        ),
    )
    payload["return_probes"] = [
        {
            "job_id": "return-1",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
        }
    ]

    with pytest.raises(
        ContractError,
        match="automatic_validation_license_invalid",
    ):
        validate_settlement(payload)


def test_candidate_entry_cannot_claim_an_automatic_validation_license() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=1)],
        attempts=1,
        action="watch_for_new_source",
        confidence="weak",
        decision_ready=False,
    )
    entry["rung"] = "candidate"
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            watch_names=["Example Product"],
        ),
    )
    payload["return_probes"] = [
        {
            "job_id": "return-1",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
            "licensing_action": "validate_once",
        }
    ]

    with pytest.raises(
        ContractError,
        match="automatic_validation_license_incompatible",
    ):
        validate_settlement(payload)


def test_pre_probe_license_survives_a_later_comment_rank_change() -> None:
    entry = _entry(
        comments=[_source("comment-1", author_id="author-1", rank_in_thread=4)],
        attempts=1,
        action="parked_after_no_confirmation",
        confidence="weak",
        decision_ready=False,
    )
    payload = _payload(
        entry,
        summary=_summary(
            decision_ready=[],
            parked_names=["Example Product"],
        ),
    )
    payload["return_probes"] = [
        {
            "job_id": "return-1",
            "entry_entity_key": "brand|product|edp",
            "partial": False,
            "automatic_validation": True,
            "licensing_action": "validate_once",
        }
    ]

    receipt = validate_settlement(payload)

    assert receipt["results"][0]["action"] == "parked_after_no_confirmation"


def test_nonautomatic_probe_cannot_claim_a_validation_license() -> None:
    payload = _payload(_entry())
    payload["return_probes"][0]["licensing_action"] = "validate_once"

    with pytest.raises(
        ContractError,
        match="return_probe_license_forbidden",
    ):
        validate_settlement(payload)


def test_receipt_projects_only_validated_subject_fields() -> None:
    payload = _payload(_entry())
    payload["subject"]["recommended_action"] = "undercut the rival"

    receipt = validate_settlement(payload)

    assert receipt["subject"] == {
        "name": "Subject",
        "entity_key": "subject|product|edp",
    }


def test_unattributed_complaint_body_cannot_enter_a_settlement() -> None:
    entry = _entry()
    entry["sources"].append(
        {
            "source_id": "comment-3",
            "surface_class": "complaint_body",
            "entity_key": "brand|product|edp",
            "subject_entity_key": "subject|product|edp",
            "posture": "secondhand",
            "stance_bearing": False,
            "engagement": {"score": 99, "rank_in_thread": 1},
        }
    )

    with pytest.raises(ContractError) as error:
        validate_settlement(_payload(entry))

    assert any(
        violation.startswith("comment_author_missing:")
        for violation in error.value.violations
    )
    assert any(
        violation.startswith("comment_thread_missing:")
        for violation in error.value.violations
    )
    assert any(
        violation.startswith("comment_venue_missing:")
        for violation in error.value.violations
    )


def test_null_variant_token_fails_identity_binding() -> None:
    entry = _entry(entity_key="brand|product|null")

    with pytest.raises(ContractError, match="entity_key_unbound"):
        validate_settlement(_payload(entry))


def test_cli_surfaces_a_contract_failure_and_returns_two(tmp_path: Path) -> None:
    entry = _entry()
    payload = _payload(entry)
    del entry["entity_key"]
    source = tmp_path / "settlement.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--input", str(source)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 2, completed.stderr
    assert "phase2 decision contract failed" in completed.stderr
    assert "entity_key_missing" in completed.stderr


def test_cli_writes_a_receipt_and_returns_zero(tmp_path: Path) -> None:
    source = tmp_path / "settlement.json"
    output = tmp_path / "receipt.json"
    source.write_text(json.dumps(_payload(_entry())), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--input",
            str(source),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["valid"] is True
