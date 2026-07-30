"""Evaluate and seal Phase-2 competitor decisions.

The Phase-2 ledger rung remains an evidence classification.  This contract
adds the decision boundary that the rung alone cannot supply:

* every source must bind to the same exact product identity;
* comment popularity is recorded but never substitutes for independent,
  first-hand support;
* a weak signal earns at most one automatic validation attempt;
* exact row values drive price multiples; and
* a decision-ready entry must recommend added/proven value, never a price cut.

The input is a normalized settlement, not raw capture data.  The caller remains
responsible for source extraction; this module makes the resulting decision
claims reproducible and fail-closed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "serp_phase2_decision_settlement_v0"
RECEIPT_VERSION = "serp_phase2_decision_receipt_v0"
JSON_SAFE_INTEGER_MAX = 9_007_199_254_740_991

POSTURES = {"first_hand", "secondhand", "unclear"}
VALUE_LEVERS = {"product", "buying_confidence", "ownership", "proof"}
VALUE_ACTIONS = {
    "product": "improve_product",
    "buying_confidence": "increase_buying_confidence",
    "ownership": "improve_ownership",
    "proof": "strengthen_proof",
}
VALUE_RESPONSE_FIELDS = {
    "customer_gain",
    "observed_sacrifice",
    "value_lever",
    "value_action",
    "proof_needed",
    "price_action",
    "response_kind",
}
COMPARISON_BASES = {
    "like_for_like",
    "cross_variant",
    "cross_concentration",
}
FLOOR_STATUSES = {
    "cross_retailer_verified",
    "single_marketplace_observation",
    "brand_list",
    "typical_price",
}
ACTIONS = {
    "use_in_decision",
    "validate_once",
    "watch_for_new_source",
    "parked_after_no_confirmation",
    "correct_identity",
}
CONFIDENCES = {"weak", "corroborated", "strong", "strongest"}
ALLOWED_SURFACE_CLASSES = {
    "complaint_body",
    "creator_transcript",
    "editorial_body",
    "retail_shelf",
    "serp_aio",
    "serp_question_layer",
    "serp_rendered_snippet",
    "serp_result_title",
}
class ContractError(ValueError):
    """Raised when a settlement cannot be sealed."""

    def __init__(self, violations: list[str] | str):
        if isinstance(violations, str):
            violations = [violations]
        self.violations = violations
        super().__init__("; ".join(violations))


def _required_text(
    value: Any,
    *,
    code: str,
    field: str,
    violations: list[str],
) -> str:
    if not isinstance(value, str) or not value.strip():
        violations.append(f"{code}:{field}")
        return ""
    return value.strip()


def _entity_key_is_bound(value: str) -> bool:
    tokens = [
        unicodedata.normalize("NFKC", token.strip()).casefold()
        for token in value.split("|")
    ]
    normalized_tokens = {
        "".join(character for character in token if character.isalnum())
        for token in tokens
    }
    return (
        len(tokens) >= 3
        and all(tokens)
        and all(normalized_tokens)
        and not any(
            marker in token
            for token in normalized_tokens
            for marker in (
                "unknown",
                "unbound",
                "unspecified",
                "notspecified",
                "tbd",
                "pending",
                "missing",
                "unset",
                "notset",
                "todo",
            )
        )
        and not normalized_tokens & {"na", "none", "null"}
    )


def _engagement(
    source: dict[str, Any],
    *,
    entry_name: str,
    violations: list[str],
) -> tuple[int | None, int | None]:
    engagement = source.get("engagement")
    source_id = source.get("source_id", "<unknown>")
    prefix = f"{entry_name}:{source_id}"
    if not isinstance(engagement, dict):
        violations.append(f"comment_engagement_missing:{prefix}")
        return None, None

    score = engagement.get("score")
    score_declared = score is not None
    if score_declared and (
        isinstance(score, bool)
        or not isinstance(score, int)
        or abs(score) > JSON_SAFE_INTEGER_MAX
    ):
        violations.append(f"comment_score_invalid:{prefix}")
        score = None
    if not score_declared:
        _required_text(
            engagement.get("score_unavailable_reason"),
            code="comment_score_missing",
            field=prefix,
            violations=violations,
        )

    rank = engagement.get("rank_in_thread")
    if (
        not isinstance(rank, int)
        or isinstance(rank, bool)
        or rank < 1
        or rank > JSON_SAFE_INTEGER_MAX
    ):
        violations.append(f"comment_rank_invalid:{prefix}")
        rank = None
    return score, rank


def _price_result(
    entry_name: str,
    price: Any,
    violations: list[str],
) -> dict[str, Any]:
    if price is None:
        return {}
    if not isinstance(price, dict):
        violations.append(f"price_invalid:{entry_name}")
        return {}

    values: dict[str, float] = {}
    for field in (
        "subject_price",
        "subject_size",
        "competitor_floor",
        "competitor_size",
        "subject_multiple",
    ):
        value = price.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            violations.append(f"price_value_invalid:{entry_name}:{field}")
            continue
        try:
            normalized_value = float(value)
        except OverflowError:
            normalized_value = math.inf
        if not math.isfinite(normalized_value) or normalized_value <= 0:
            violations.append(f"price_value_invalid:{entry_name}:{field}")
            continue
        values[field] = normalized_value

    currency = _required_text(
        price.get("currency"),
        code="price_currency_missing",
        field=entry_name,
        violations=violations,
    )
    comparison_basis = price.get("comparison_basis")
    if comparison_basis not in COMPARISON_BASES:
        violations.append(f"price_comparison_basis_invalid:{entry_name}")
    floor_status = price.get("floor_status")
    if floor_status not in FLOOR_STATUSES:
        violations.append(f"price_floor_status_invalid:{entry_name}")

    if len(values) == 5:
        exact_subject = values["subject_price"] / values["subject_size"]
        exact_competitor = (
            values["competitor_floor"] / values["competitor_size"]
        )
        expected = round(exact_subject / exact_competitor + 1e-12, 2)
        if values["subject_multiple"] != expected:
            violations.append(
                "price_multiple_mismatch:"
                f"{entry_name}:claimed={values['subject_multiple']:.2f}:"
                f"expected={expected:.2f}"
            )
        return {
            "currency": currency,
            "subject_price": values["subject_price"],
            "subject_size": values["subject_size"],
            "competitor_floor": values["competitor_floor"],
            "competitor_size": values["competitor_size"],
            "subject_multiple": expected,
            "comparison_basis": comparison_basis,
            "floor_status": floor_status,
        }
    return {
        "currency": currency,
        "comparison_basis": comparison_basis,
        "floor_status": floor_status,
    }


def _evaluate_entry(
    entry: Any,
    expected_subject_key: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    violations: list[str] = []
    if not isinstance(entry, dict):
        return {}, ["entry_invalid"]

    name = _required_text(
        entry.get("name"),
        code="entry_name_missing",
        field="name",
        violations=violations,
    )
    entity_key = _required_text(
        entry.get("entity_key"),
        code="entity_key_missing",
        field=name or "<unknown>",
        violations=violations,
    )
    if entity_key and not _entity_key_is_bound(entity_key):
        violations.append(f"entity_key_unbound:{name}")
    subject_entity_key = _required_text(
        entry.get("subject_entity_key"),
        code="subject_entity_key_missing",
        field=name or "<unknown>",
        violations=violations,
    )
    if subject_entity_key and not _entity_key_is_bound(subject_entity_key):
        violations.append(f"subject_entity_key_unbound:{name}")

    rung = entry.get("rung")
    if rung not in {"presence", "candidate", "finding_grade"}:
        violations.append(f"rung_invalid:{name}")
        rung = "presence"

    sources = entry.get("sources")
    if not isinstance(sources, list) or not sources:
        violations.append(f"sources_missing:{name}")
        sources = []

    source_ids: set[str] = set()
    surface_classes: set[str] = set()
    first_hand_authors: set[str] = set()
    threads: set[str] = set()
    venues: set[str] = set()
    comment_scores: list[int] = []
    first_hand_comment_ranks: list[int] = []
    identity_coherent = bool(entity_key)
    subject_identity_coherent = bool(subject_entity_key)
    if (
        expected_subject_key
        and subject_entity_key
        and subject_entity_key != expected_subject_key
    ):
        subject_identity_coherent = False

    for source in sources:
        if not isinstance(source, dict):
            violations.append(f"source_invalid:{name}")
            continue
        source_id = _required_text(
            source.get("source_id"),
            code="source_id_missing",
            field=name,
            violations=violations,
        )
        if source_id in source_ids:
            violations.append(f"source_id_duplicate:{name}:{source_id}")
        source_ids.add(source_id)

        surface_class = _required_text(
            source.get("surface_class"),
            code="surface_class_missing",
            field=f"{name}:{source_id}",
            violations=violations,
        )
        if surface_class and surface_class not in ALLOWED_SURFACE_CLASSES:
            violations.append(
                f"surface_class_invalid:{name}:{source_id}:{surface_class}"
            )
        elif surface_class:
            surface_classes.add(surface_class)

        source_entity = source.get("entity_key")
        if not isinstance(source_entity, str) or source_entity != entity_key:
            identity_coherent = False
        source_subject_entity = source.get("subject_entity_key")
        if (
            not isinstance(source_subject_entity, str)
            or source_subject_entity != subject_entity_key
        ):
            subject_identity_coherent = False

        if surface_class != "complaint_body":
            continue

        score, rank = _engagement(
            source,
            entry_name=name,
            violations=violations,
        )
        if score is not None:
            comment_scores.append(score)

        posture = source.get("posture")
        if posture not in POSTURES:
            violations.append(
                f"comment_posture_invalid:{name}:{source_id}"
            )
        stance_bearing = source.get("stance_bearing")
        if not isinstance(stance_bearing, bool):
            violations.append(
                f"comment_stance_missing:{name}:{source_id}"
            )
            stance_bearing = False
        author_id = _required_text(
            source.get("author_id"),
            code="comment_author_missing",
            field=f"{name}:{source_id}",
            violations=violations,
        )
        thread_id = _required_text(
            source.get("thread_id"),
            code="comment_thread_missing",
            field=f"{name}:{source_id}",
            violations=violations,
        )
        venue = _required_text(
            source.get("venue"),
            code="comment_venue_missing",
            field=f"{name}:{source_id}",
            violations=violations,
        )

        if posture != "first_hand" or not stance_bearing:
            continue
        if rank is not None:
            first_hand_comment_ranks.append(rank)
        if author_id:
            first_hand_authors.add(author_id)
        if thread_id:
            threads.add(thread_id)
        if venue:
            venues.add(venue)

    if not identity_coherent:
        violations.append(f"identity_mismatch:{name}")
    if not subject_identity_coherent:
        violations.append(f"subject_identity_mismatch:{name}")

    attempts = entry.get("automatic_validation_attempts")
    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts not in {0, 1}
    ):
        violations.append(f"automatic_validation_attempts_invalid:{name}")
        attempts = 0

    author_count = len(first_hand_authors)
    if author_count >= 3 and len(venues) >= 2:
        confidence = "strongest"
    elif author_count >= 3:
        confidence = "strong"
    elif author_count >= 2:
        confidence = "corroborated"
    else:
        confidence = "weak"

    surface_independent = len(surface_classes) >= 2
    best_comment_rank = (
        min(first_hand_comment_ranks)
        if first_hand_comment_ranks
        else None
    )
    if not identity_coherent or not subject_identity_coherent:
        action = "correct_identity"
    elif (
        rung == "finding_grade"
        and author_count >= 2
        and surface_independent
    ):
        action = "use_in_decision"
    elif rung != "finding_grade":
        action = "watch_for_new_source"
    elif attempts == 1 and author_count >= 1:
        action = "parked_after_no_confirmation"
    elif author_count == 1 and best_comment_rank == 1:
        action = "validate_once"
    else:
        action = "watch_for_new_source"
    decision_ready = action == "use_in_decision"

    price_result = _price_result(name, entry.get("price"), violations)

    value_response = entry.get("value_response")
    if not decision_ready and value_response is not None:
        violations.append(f"value_response_forbidden:{name}")
    if decision_ready:
        if not isinstance(value_response, dict):
            violations.append(f"value_response_missing:{name}")
        else:
            for field in (
                "customer_gain",
                "observed_sacrifice",
                "proof_needed",
            ):
                _required_text(
                    value_response.get(field),
                    code="value_response_field_missing",
                    field=f"{name}:{field}",
                    violations=violations,
                )
            value_lever = value_response.get("value_lever")
            if value_lever not in VALUE_LEVERS:
                violations.append(f"value_lever_invalid:{name}")
            elif value_response.get("value_action") != VALUE_ACTIONS[value_lever]:
                violations.append(f"value_action_invalid:{name}")
            if value_response.get("response_kind") != "add_or_prove_value":
                violations.append(f"response_kind_invalid:{name}")
            if value_response.get("price_action") != "none":
                violations.append(f"price_action_forbidden:{name}")
            extra_fields = sorted(
                set(value_response) - VALUE_RESPONSE_FIELDS
            )
            if extra_fields:
                violations.append(
                    f"value_response_field_forbidden:{name}:"
                    f"{','.join(extra_fields)}"
                )

    result = {
        "name": name,
        "entity_key": entity_key,
        "subject_entity_key": subject_entity_key,
        "rung": rung,
        "identity_coherent": (
            identity_coherent and subject_identity_coherent
        ),
        "surface_independent": surface_independent,
        "surface_classes": sorted(surface_classes),
        "source_ids": sorted(source_ids),
        "first_hand_authors": author_count,
        "threads": len(threads),
        "venues": len(venues),
        "best_comment_rank": best_comment_rank,
        "max_comment_score": max(comment_scores) if comment_scores else None,
        "confidence": confidence,
        "action": action,
        "decision_ready": decision_ready,
        **price_result,
    }
    if decision_ready and isinstance(value_response, dict):
        result["value_response"] = {
            field: value_response.get(field)
            for field in sorted(VALUE_RESPONSE_FIELDS)
        }
    return result, violations


def evaluate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Compute one entry's decision without checking its claimed decision."""

    result, violations = _evaluate_entry(
        entry,
        entry.get("subject_entity_key"),
    )
    structural = [
        violation
        for violation in violations
        if not (
            violation.startswith("identity_mismatch:")
            or violation.startswith("subject_identity_mismatch:")
        )
    ]
    if structural:
        raise ContractError(structural)
    return result


def _expected_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_action: dict[str, list[str]] = {
        action: [] for action in ACTIONS
    }
    for result in results:
        by_action[result["action"]].append(result["name"])
    for names in by_action.values():
        names.sort()
    return {
        "entry_count": len(results),
        "decision_ready_names": by_action["use_in_decision"],
        "validate_once_names": by_action["validate_once"],
        "watch_names": by_action["watch_for_new_source"],
        "parked_names": by_action["parked_after_no_confirmation"],
        "identity_correction_names": by_action["correct_identity"],
    }


def _prior_validation_entities(
    payload: dict[str, Any],
    *,
    subject_name: str,
    subject_entity_key: str,
    violations: list[str],
) -> set[str]:
    receipts = payload.get("prior_decision_receipts", [])
    if not isinstance(receipts, list):
        violations.append("prior_decision_receipts_invalid")
        return set()

    licensed_entities: set[str] = set()
    expected_subject = {
        "name": subject_name,
        "entity_key": subject_entity_key,
    }
    for index, receipt in enumerate(receipts):
        receipt_id = f"prior_receipt_{index}"
        if (
            not isinstance(receipt, dict)
            or receipt.get("schema_version") != RECEIPT_VERSION
            or receipt.get("valid") is not True
        ):
            violations.append(f"prior_decision_receipt_invalid:{receipt_id}")
            continue
        if receipt.get("subject") != expected_subject:
            violations.append(
                f"prior_decision_receipt_subject_mismatch:{receipt_id}"
            )
            continue
        results = receipt.get("results")
        if not isinstance(results, list):
            violations.append(
                f"prior_decision_receipt_results_invalid:{receipt_id}"
            )
            continue
        try:
            expected_summary = _expected_summary(results)
        except (KeyError, TypeError):
            violations.append(
                f"prior_decision_receipt_results_invalid:{receipt_id}"
            )
            continue
        if receipt.get("summary") != expected_summary:
            violations.append(
                f"prior_decision_receipt_summary_mismatch:{receipt_id}"
            )
            continue
        for result in results:
            if not isinstance(result, dict):
                continue
            entity_key = result.get("entity_key")
            if (
                isinstance(entity_key, str)
                and entity_key
                and result.get("subject_entity_key") == subject_entity_key
                and result.get("rung") == "finding_grade"
                and result.get("identity_coherent") is True
                and type(result.get("first_hand_authors")) is int
                and result.get("first_hand_authors") == 1
                and type(result.get("best_comment_rank")) is int
                and result.get("best_comment_rank") == 1
                and result.get("action") == "validate_once"
                and result.get("decision_ready") is False
            ):
                licensed_entities.add(entity_key)
    return licensed_entities


def validate_settlement(payload: Any) -> dict[str, Any]:
    """Validate a normalized Phase-2 settlement and return its receipt."""

    violations: list[str] = []
    if not isinstance(payload, dict):
        raise ContractError("settlement_invalid")
    if payload.get("schema_version") != SCHEMA_VERSION:
        violations.append("schema_version_invalid")

    subject = payload.get("subject")
    subject_name = ""
    subject_entity_key = ""
    if not isinstance(subject, dict):
        violations.append("subject_missing")
    else:
        subject_name = _required_text(
            subject.get("name"),
            code="subject_name_missing",
            field="subject",
            violations=violations,
        )
        subject_entity_key = _required_text(
            subject.get("entity_key"),
            code="subject_entity_key_missing",
            field="subject",
            violations=violations,
        )
        if (
            subject_entity_key
            and not _entity_key_is_bound(subject_entity_key)
        ):
            violations.append("subject_entity_key_unbound:subject")

    prior_validation_entities = _prior_validation_entities(
        payload,
        subject_name=subject_name,
        subject_entity_key=subject_entity_key,
        violations=violations,
    )

    entries = payload.get("entries")
    if not isinstance(entries, list):
        violations.append("entries_invalid")
        entries = []

    results: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_entity_keys: set[str] = set()
    for entry in entries:
        result, entry_violations = _evaluate_entry(
            entry,
            subject_entity_key or None,
        )
        violations.extend(entry_violations)
        if not result:
            continue
        if result["name"] in seen_names:
            violations.append(f"entry_name_duplicate:{result['name']}")
        seen_names.add(result["name"])
        if result["entity_key"] in seen_entity_keys:
            violations.append(
                f"entity_key_duplicate:{result['entity_key']}:"
                f"{result['name']}"
            )
        seen_entity_keys.add(result["entity_key"])
        results.append(result)

        decision = entry.get("decision") if isinstance(entry, dict) else None
        if not isinstance(decision, dict):
            violations.append(f"decision_missing:{result['name']}")
            continue
        claimed = {
            "action": decision.get("action"),
            "confidence": decision.get("confidence"),
            "decision_ready": decision.get("decision_ready"),
        }
        expected = {
            "action": result["action"],
            "confidence": result["confidence"],
            "decision_ready": result["decision_ready"],
        }
        if claimed != expected:
            violations.append(
                f"decision_mismatch:{result['name']}:"
                f"claimed={json.dumps(claimed, sort_keys=True)}:"
                f"expected={json.dumps(expected, sort_keys=True)}"
            )

    expected_summary = _expected_summary(results)
    if payload.get("summary") != expected_summary:
        violations.append(
            "summary_mismatch:"
            f"claimed={json.dumps(payload.get('summary'), sort_keys=True)}:"
            f"expected={json.dumps(expected_summary, sort_keys=True)}"
        )

    probes = payload.get("return_probes")
    if not isinstance(probes, list):
        violations.append("return_probes_invalid")
        probes = []
    partial_ids: list[str] = []
    seen_probe_ids: set[str] = set()
    automatic_probes_by_entity: dict[str, int] = {
        result["entity_key"]: 0 for result in results
    }
    result_by_entity = {
        result["entity_key"]: result for result in results
    }
    for probe in probes:
        if not isinstance(probe, dict):
            violations.append("return_probe_invalid")
            continue
        job_id = _required_text(
            probe.get("job_id"),
            code="return_probe_id_missing",
            field="return_probe",
            violations=violations,
        )
        if job_id in seen_probe_ids:
            violations.append(f"return_probe_id_duplicate:{job_id}")
        seen_probe_ids.add(job_id)
        entry_entity_key = _required_text(
            probe.get("entry_entity_key"),
            code="return_probe_entry_missing",
            field=job_id,
            violations=violations,
        )
        if entry_entity_key not in automatic_probes_by_entity:
            violations.append(
                f"return_probe_entry_unknown:{job_id}:{entry_entity_key}"
            )
        automatic_validation = probe.get("automatic_validation")
        if not isinstance(automatic_validation, bool):
            violations.append(
                f"return_probe_automatic_validation_missing:{job_id}"
            )
        elif automatic_validation:
            licensing_action = probe.get("licensing_action")
            if licensing_action != "validate_once":
                violations.append(
                    f"automatic_validation_license_invalid:{job_id}"
                )
            if entry_entity_key not in prior_validation_entities:
                violations.append(
                    f"automatic_validation_prior_receipt_missing:{job_id}:"
                    f"{entry_entity_key}"
                )
            licensed_result = result_by_entity.get(entry_entity_key)
            if licensed_result is not None and (
                licensed_result["rung"] != "finding_grade"
                or licensed_result["first_hand_authors"] < 1
            ):
                violations.append(
                    f"automatic_validation_license_incompatible:{job_id}:"
                    f"{entry_entity_key}"
                )
            if entry_entity_key in automatic_probes_by_entity:
                automatic_probes_by_entity[entry_entity_key] += 1
        elif "licensing_action" in probe:
            violations.append(f"return_probe_license_forbidden:{job_id}")
        if not isinstance(probe.get("partial"), bool):
            violations.append(f"return_probe_partial_missing:{job_id}")
        elif probe["partial"]:
            partial_ids.append(job_id)

    accounting = payload.get("capture_accounting")
    claimed_partial = (
        accounting.get("partial_probes")
        if isinstance(accounting, dict)
        else None
    )
    if claimed_partial != len(partial_ids):
        violations.append(
            "partial_probe_count_mismatch:"
            f"claimed={claimed_partial}:expected={len(partial_ids)}:"
            f"ids={json.dumps(sorted(partial_ids))}"
        )

    entry_by_entity = {
        entry["entity_key"].strip(): entry
        for entry in entries
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("entity_key"), str)
            and entry["entity_key"].strip()
        )
    }
    for entry_entity_key, probe_count in automatic_probes_by_entity.items():
        entry_name = result_by_entity[entry_entity_key]["name"]
        if probe_count > 1:
            violations.append(
                "automatic_validation_probe_limit_exceeded:"
                f"{entry_name}:{entry_entity_key}:count={probe_count}"
            )
        claimed_entry = entry_by_entity.get(entry_entity_key)
        if claimed_entry is None:
            violations.append(
                "automatic_validation_attempts_unresolved:"
                f"{entry_name}:{entry_entity_key}"
            )
            continue
        claimed_attempts = claimed_entry.get("automatic_validation_attempts")
        if claimed_attempts != probe_count:
            violations.append(
                "automatic_validation_attempts_mismatch:"
                f"{entry_name}:{entry_entity_key}:claimed={claimed_attempts}:"
                f"named_probes={probe_count}"
            )

    if violations:
        raise ContractError(violations)
    return {
        "schema_version": RECEIPT_VERSION,
        "valid": True,
        "subject": {
            "name": subject_name,
            "entity_key": subject_entity_key,
        },
        "results": results,
        "summary": expected_summary,
        "partial_probe_ids": sorted(partial_ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate and seal a Phase-2 competitor settlement."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = validate_settlement(payload)
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"phase2 decision contract failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
