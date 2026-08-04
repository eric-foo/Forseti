from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml

from runners.run_phase_acquisition_seal_validation import (
    CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    CONSUMER_DEPTH_LEDGER_VERSION,
    LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    LEGACY_CONSUMER_DEPTH_LEDGER_VERSION,
    PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE,
    PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION,
    _artifact_hash,
    _load_seal,
    validate_phase_acquisition_seal,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
V1_SEAL = REPO_ROOT / (
    "docs/workflows/"
    "summer_fridays_understanding_dogfood_20260801_p11r4/"
    "coordinated/acquisition_seal.md"
)
V1_LEDGER = REPO_ROOT / (
    "docs/research/"
    "summer_fridays_understanding_dogfood_20260801_p11r4/"
    "coordinated/evidence_depth_ledger.json"
)
V2_SEAL = REPO_ROOT / (
    "docs/workflows/"
    "summer_fridays_understanding_dogfood_20260802_p11r5/"
    "coordinated/acquisition_seal.md"
)
V2_LEDGER = REPO_ROOT / (
    "docs/research/"
    "summer_fridays_understanding_dogfood_20260802_p11r5/"
    "coordinated/evidence_depth_ledger.json"
)
V3_SEAL = REPO_ROOT / (
    "docs/workflows/"
    "summer_fridays_understanding_dogfood_20260802_p11r6/"
    "coordinated/acquisition_seal.md"
)
V3_LEDGER = REPO_ROOT / (
    "docs/research/"
    "summer_fridays_understanding_dogfood_20260802_p11r6/"
    "coordinated/evidence_depth_ledger.json"
)


def _write_seal(path: Path, seal: dict) -> None:
    path.write_text(
        "# Summer Fridays consumer-brand v2 shadow seal\n\n```yaml\n"
        + yaml.safe_dump(
            {"phase_acquisition_seal": seal},
            sort_keys=False,
            allow_unicode=True,
        )
        + "```\n",
        encoding="utf-8",
    )


def test_summer_fridays_v1_passes_but_v2_shadow_exposes_missing_axis_work(
    tmp_path: Path,
) -> None:
    assert validate_phase_acquisition_seal(
        seal_path=V1_SEAL,
        repo_root=REPO_ROOT,
    ) == []

    source_types = {
        "tsg_consumer_investment": "corporate_or_transaction",
        "cooley_transaction_role": "corporate_or_transaction",
        "cew_ceo_transition": "trade_press",
        "moodiedavitt_travel_retail": "trade_press",
        "beautyscene_fragrance_launch": "trade_press",
        "whowhatwear_perfume_review": "consumer_editorial",
        "dailybeast_gap_collaboration": "consumer_editorial",
        "forbes_brand_profile": "company_profile",
        "theindustry_beauty_growth": "company_profile",
        "british_vogue_brand_profile": "company_profile",
        "femfounded_company_case": "company_profile",
        "grazia_brand_profile": "company_profile",
    }
    ledger = json.loads(V1_LEDGER.read_text(encoding="utf-8"))
    ledger["schema_version"] = LEGACY_CONSUMER_DEPTH_LEDGER_VERSION
    ledger["profile_id"] = LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    external = ledger["families"].pop("outside_in")
    for row in external["units"]:
        row["source_type"] = source_types[row["unit_id"]]
        row["relationship"] = "relationship_unknown"
    ledger["families"]["external_context"] = external
    for row in ledger["families"]["native_social"]["posts"]:
        row["relationship"] = (
            "owned"
            if row["creator_id"] == "summerfridays"
            else "relationship_unknown"
        )

    shadow_ledger = tmp_path / "evidence_depth_ledger_v2_shadow.json"
    shadow_ledger.write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )
    seal = deepcopy(_load_seal(V1_SEAL))
    seal["evidence_depth_ledger"] = {
        "locator": str(shadow_ledger),
        "sha256": _artifact_hash(shadow_ledger),
    }
    shadow_seal = tmp_path / "acquisition_seal_v2_shadow.md"
    _write_seal(shadow_seal, seal)

    findings = validate_phase_acquisition_seal(
        seal_path=shadow_seal,
        repo_root=REPO_ROOT,
        allow_legacy_consumer_v1=True,
    )

    expected = {
        "missing_consumer_brand_product_axes",
        "missing_retailer_axis_coding",
        "missing_owned_social_published_at",
        "invalid_owned_social_direction_event_tags",
        "invalid_saturation_batch_new_product_axes",
        "invalid_saturation_batch_changed_axis_strengths",
        "invalid_saturation_batch_changed_axis_incidence",
        "passing_consumer_brand_seal_without_axis_closure",
        "passing_seal_without_saturation_closure",
    }
    print(
        json.dumps(
            {
                "historical_v1": "PASS",
                "consumer_v2_shadow": "BLOCKED",
                "findings": findings,
            },
            indent=2,
            sort_keys=True,
        )
    )
    assert set(findings) == expected
    assert not any(
        finding.startswith("passing_seal_below_depth_floor:")
        for finding in findings
    )


def test_summer_fridays_p11r5_requires_explicit_legacy_audit() -> None:
    assert "legacy_consumer_v1_requires_explicit_historical_audit" in (
        validate_phase_acquisition_seal(
            seal_path=V2_SEAL,
            repo_root=REPO_ROOT,
        )
    )
    assert validate_phase_acquisition_seal(
        seal_path=V2_SEAL,
        repo_root=REPO_ROOT,
        allow_legacy_consumer_v1=True,
    ) == []

    ledger = json.loads(V2_LEDGER.read_text(encoding="utf-8"))
    assert ledger["schema_version"] == LEGACY_CONSUMER_DEPTH_LEDGER_VERSION
    assert (
        ledger["profile_id"]
        == LEGACY_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    )
    assert len(ledger["product_axes"]) == 12
    assert {
        axis["axis_id"]: axis["strength"]
        for axis in ledger["product_axes"]
    } == {
        "reaction_and_breakout": "strong",
        "value_and_quantity": "strong",
        "packaging_and_dispensing": "strong",
        "wear_and_longevity": "signal",
        "hydration_and_moisture": "strong",
        "texture_and_skin_finish": "strong",
        "coverage_and_pigment": "recurring",
        "shade_and_color_fit": "strong",
        "scent_and_flavor": "strong",
        "formula_consistency_and_change": "signal",
        "application_and_tool_performance": "signal",
        "hype_originality_and_trust": "strong",
    }


def test_summer_fridays_p11r6_is_preserved_provenance_not_a_passing_seal() -> None:
    """The p11r6 dogfood stays pinned as provenance, but it may not pass.

    The expanded current-contract checks require proven Reddit
    candidate-frontier exhaustion at any thread count, per-batch usable-thread
    accounting, comment-coding-backed support-ref fields, and
    checkout-portable repo-internal locators. The p11r6 run predates those
    obligations, so the validator must reject it until the Chief Architect
    regenerates the evidence-depth ledger with the missing proofs.
    """
    findings = validate_phase_acquisition_seal(
        seal_path=V3_SEAL,
        repo_root=REPO_ROOT,
    )

    assert findings != []
    assert "passing_seal_without_reddit_frontier_exhaustion" in findings
    assert "missing_reddit_frontier_discovery_jobs" in findings
    assert "invalid_saturation_batch_new_usable_reddit_threads" in findings
    # The historical seal must never be waved through as legacy either.
    assert (
        "legacy_consumer_v1_requires_explicit_historical_audit"
        not in findings
    )

    ledger = json.loads(V3_LEDGER.read_text(encoding="utf-8"))
    assert ledger["schema_version"] == PREVIOUS_CONSUMER_DEPTH_LEDGER_VERSION
    assert ledger["schema_version"] != CONSUMER_DEPTH_LEDGER_VERSION
    assert ledger["profile_id"] == PREVIOUS_CONSUMER_BRAND_UNDERSTANDING_PROFILE
    assert ledger["profile_id"] != CONSUMER_BRAND_UNDERSTANDING_PROFILE
    assert len(ledger["families"]["reddit_forum"]["threads"]) == 40
    assert len(ledger["product_axes"]) == 12
    assert all(
        len(axis["focused_search_jobs"]) == 3
        for axis in ledger["product_axes"]
    )
    assert all(
        batch["batch_kind"] == "live_acquisition"
        and batch["material_incremental_value"] is False
        and batch["new_customer_segments"] == 0
        and batch["new_product_conditions"] == 0
        and batch["new_comparison_choices"] == 0
        and batch["new_competitor_alternatives"] == 0
        for batch in ledger["closure"]["batches"][-2:]
    )
