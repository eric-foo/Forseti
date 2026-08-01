from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from runners.run_phase_acquisition_seal_validation import (
    BROAD_UNDERSTANDING_PROFILE,
    DEPTH_LEDGER_VERSION,
    LEGACY_SEAL_VERSION,
    SEAL_VERSION,
    _artifact_hash,
    validate_phase_acquisition_seal,
)


def _artifact(tmp_path: Path, name: str, text: str | None = None) -> dict[str, str]:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or f"artifact:{name}\n", encoding="utf-8")
    return {"locator": str(path), "sha256": _artifact_hash(path)}


def _depth_ledger(tmp_path: Path) -> dict[str, str]:
    source = _artifact(tmp_path, "depth_source.md")
    artifact_id = "depth-source"
    ledger = {
        "schema_version": DEPTH_LEDGER_VERSION,
        "profile_id": BROAD_UNDERSTANDING_PROFILE,
        "subject": "Summer Fridays",
        "artifacts": [{"artifact_id": artifact_id, **source}],
        "families": {
            "outside_in": {
                "units": [
                    {
                        "unit_id": f"outside-{index}",
                        "origin_id": f"publisher-{index}.example",
                        "artifact_id": artifact_id,
                        "independence": "independent_origin",
                        "echo_group_id": f"story-{index // 2}",
                    }
                    for index in range(12)
                ]
            },
            "retailer_reviews": {
                "corpora": [
                    {
                        "corpus_id": "retailer-a:provider-a",
                        "artifact_id": artifact_id,
                        "unique_review_count": 400,
                        "cross_corpus_duplicate_count": 0,
                        "product_context_ids": ["p1", "p2", "p3"],
                        "category_ids": ["lip", "skincare"],
                        "rating_bands": ["low", "mid", "high"],
                    },
                    {
                        "corpus_id": "retailer-b:provider-b",
                        "artifact_id": artifact_id,
                        "unique_review_count": 400,
                        "cross_corpus_duplicate_count": 20,
                        "product_context_ids": ["p4", "p5", "p6"],
                        "category_ids": ["makeup", "skincare"],
                        "rating_bands": ["low", "mid", "high"],
                    },
                ]
            },
            "reddit_forum": {
                "threads": [
                    {
                        "thread_id": f"thread-{index}",
                        "community_id": f"community-{index % 4}",
                        "topic_category": f"topic-{index % 3}",
                        "artifact_id": artifact_id,
                        "independence": "independent_thread",
                    }
                    for index in range(20)
                ]
            },
            "native_social": {
                "posts": [
                    {
                        "unit_id": f"native-{index}",
                        "platform": "youtube" if index % 2 else "instagram",
                        "post_id": f"post-{index}",
                        "creator_id": f"creator-{index}",
                        "perspective": "positive" if index % 2 else "critical",
                        "artifact_id": artifact_id,
                        "independence": "independent_post",
                    }
                    for index in range(30)
                ]
            },
        },
        "closure": {
            "echo_groups_adjudicated": True,
            "material_seams": [
                {"seam_id": "value", "disposition": "bounded"}
            ],
            "batches": [
                {
                    "batch_id": "batch-1",
                    "candidate_moves_checked": 3,
                    "material_incremental_value": False,
                    "new_material_seams": 0,
                    "changed_material_dispositions": 0,
                },
                {
                    "batch_id": "batch-2",
                    "candidate_moves_checked": 2,
                    "material_incremental_value": False,
                    "new_material_seams": 0,
                    "changed_material_dispositions": 0,
                },
            ],
            "remaining_moves": [
                {
                    "move_id": "another-same-story",
                    "disposition": "dominated",
                    "material": False,
                }
            ],
            "conclusion": "complete",
        },
    }
    path = tmp_path / "evidence_depth_ledger.json"
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return {"locator": str(path), "sha256": _artifact_hash(path)}


def _blocked_seal(tmp_path: Path) -> dict:
    specialist_returns = []
    for actor in ("CO1", "CO2", "CO3"):
        artifact = _artifact(tmp_path, f"{actor.lower()}_terminal.md")
        specialist_returns.append(
            {
                "actor": actor,
                "terminal_locator": artifact["locator"],
                "sha256": artifact["sha256"],
                "status": "BLOCKED_TERMINAL",
            }
        )
    phase1 = _artifact(tmp_path, "serp_phase1.md")
    phase2 = _artifact(tmp_path, "serp_phase2.md")
    receipt = _artifact(
        tmp_path,
        "decision_receipt.json",
        json.dumps({"entries": []}, indent=2) + "\n",
    )
    phase2_jobs = [f"P2-{index:03d}" for index in range(1, 6)]
    terminals = {row["actor"]: row for row in specialist_returns}

    def completed_route(
        route_id: str, phase: str, job_id: str, actor: str
    ) -> dict:
        terminal = terminals[actor]
        return {
            "route_id": route_id,
            "phase": phase,
            "required": True,
            "material": True,
            "planned_job_ids": [job_id],
            "planned_count": 1,
            "completed_job_ids": [job_id],
            "completed_count": 1,
            "blocked_job_ids": [],
            "blocked_count": 0,
            "unrun_job_ids": [],
            "unrun_count": 0,
            "terminal_artifact_locator": terminal["terminal_locator"],
            "terminal_artifact_sha256": terminal["sha256"],
        }

    specialist_routes = [
        completed_route(
            "official_retailer_authorization", "co1", "AUTH-001", "CO1"
        ),
        completed_route(
            "google_ads_transparency", "co1", "GADS-001", "CO1"
        ),
        completed_route("meta_ads_library", "co1", "MADS-001", "CO1"),
        completed_route("retailer_full_pdp", "co2", "PDP-001", "CO2"),
        completed_route("reddit_weekly_lake", "co3", "RWL-001", "CO3"),
        completed_route("reddit_community_scout", "co3", "RCS-001", "CO3"),
    ]
    return {
        "schema_version": SEAL_VERSION,
        "cycle_id": "summer_fridays_confirmation",
        "acquisition_gate": "blocked",
        "seal_state": "BLOCKED_ACQUISITION_INCOMPLETE",
        "deliver_allowed": False,
        "controller_placement": {
            "controller_actor": "CO0",
            "placement": "top_level",
            "worker_slots_required": 3,
            "worker_slots_available": 3,
        },
        "route_capability_preflight": {
            "checked_before_network_capture": True,
            "google_serp": {
                "mode": "cooldown_only",
                "primary_route_ready": True,
                "queue_state_writable": True,
                "persistent_fallback_ready": False,
            },
            "reddit_weekly_lake": {"reader_status": "ready"},
            "paid_ad_transparency": {
                "google_ads_transparency": "ready",
                "meta_ads_library": "ready",
            },
            "tiktok_shop": {
                "trigger": "not_required",
                "route_status": "not_checked_until_trigger",
            },
            "native_social": {
                platform: {
                    "trigger": "not_required",
                    "route_status": "not_checked_until_trigger",
                }
                for platform in ("tiktok", "instagram", "youtube")
            },
        },
        "specialist_returns": specialist_returns,
        "post_phase1_continuation_mode": "bounded_salvage",
        "route_job_accounting": [
            {
                "route_id": "serp_phase1",
                "phase": "serp_phase1",
                "required": True,
                "material": True,
                "planned_job_ids": ["P1-001"],
                "planned_count": 1,
                "completed_job_ids": ["P1-001"],
                "completed_count": 1,
                "blocked_job_ids": [],
                "blocked_count": 0,
                "unrun_job_ids": [],
                "unrun_count": 0,
                "terminal_artifact_locator": phase1["locator"],
                "terminal_artifact_sha256": phase1["sha256"],
            },
            *specialist_routes,
            {
                "route_id": "serp_phase2",
                "phase": "serp_phase2",
                "required": True,
                "material": True,
                "planned_job_ids": list(phase2_jobs),
                "planned_count": 5,
                "completed_job_ids": [],
                "completed_count": 0,
                "blocked_job_ids": [],
                "blocked_count": 0,
                "unrun_job_ids": list(phase2_jobs),
                "unrun_count": 5,
                "terminal_artifact_locator": phase2["locator"],
                "terminal_artifact_sha256": phase2["sha256"],
            },
        ],
        "serp_phase2_decision_receipt": {
            **receipt,
            "entries": 0,
        },
        "evidence_depth_ledger": _depth_ledger(tmp_path),
        "resume_contract": {
            "pending_job_ids": list(phase2_jobs),
            "reusable_artifacts": [
                {
                    "locator": specialist_returns[0]["terminal_locator"],
                    "sha256": specialist_returns[0]["sha256"],
                    "invalid_if": [
                        "bound question changes",
                        "artifact hash changes",
                    ],
                }
            ],
        },
    }


def _write_seal(tmp_path: Path, seal: dict) -> Path:
    path = tmp_path / "acquisition_seal.md"
    path.write_text(
        "# Acquisition Seal\n\n```yaml\n"
        + yaml.safe_dump(
            {"phase_acquisition_seal": seal},
            sort_keys=False,
            allow_unicode=True,
        )
        + "```\n",
        encoding="utf-8",
    )
    return path


def _validate(tmp_path: Path, seal: dict) -> list[str]:
    return validate_phase_acquisition_seal(
        seal_path=_write_seal(tmp_path, seal), repo_root=tmp_path
    )


def test_blocked_seal_accounts_for_five_unrun_phase2_jobs(
    tmp_path: Path,
) -> None:
    assert _validate(tmp_path, _blocked_seal(tmp_path)) == []


def test_empty_decision_receipt_cannot_hide_unrun_phase2_jobs_in_passing_seal(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "passing_seal_has_material_pending_jobs" in findings
    assert "passing_seal_has_resume_work" in findings


def test_passing_seal_accepts_supported_non_material_blocked_route(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    weekly = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "reddit_weekly_lake"
    )
    weekly["material"] = False
    weekly["blocked_job_ids"] = list(weekly["completed_job_ids"])
    weekly["blocked_count"] = weekly["completed_count"]
    weekly["completed_job_ids"] = []
    weekly["completed_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert _validate(tmp_path, seal) == []


def test_missing_phase2_query_id_breaks_exact_accounting(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["planned_job_ids"].pop()
    phase2["planned_count"] = 4

    assert "planned_jobs_not_fully_accounted" in _validate(tmp_path, seal)


def test_specialist_terminal_hash_drift_is_visible(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    terminal = Path(seal["specialist_returns"][0]["terminal_locator"])
    terminal.write_text("controller-edited bytes\n", encoding="utf-8")

    assert "specialist_terminal_hash_mismatch" in _validate(tmp_path, seal)


def test_text_artifact_line_endings_do_not_forge_hash_drift(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    terminal = Path(seal["specialist_returns"][0]["terminal_locator"])
    lf_content = terminal.read_bytes().replace(b"\r\n", b"\n")
    terminal.write_bytes(lf_content.replace(b"\n", b"\r\n"))

    assert _validate(tmp_path, seal) == []


def test_specialist_actor_set_cannot_be_relabelled_by_controller(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["specialist_returns"][1]["actor"] = "CO0"

    assert "specialist_returns_must_be_co1_co2_co3" in _validate(tmp_path, seal)


def test_fully_completed_seal_passes_with_no_resume_work(tmp_path: Path) -> None:
    seal = deepcopy(_blocked_seal(tmp_path))
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert _validate(tmp_path, seal) == []


def test_completed_jobs_cannot_replace_depth_ledger(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    seal.pop("evidence_depth_ledger")
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert "missing_evidence_depth_ledger" in _validate(tmp_path, seal)


def test_passing_seal_rejects_floor_count_without_independent_units(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    ledger_path = Path(seal["evidence_depth_ledger"]["locator"])
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for row in ledger["families"]["outside_in"]["units"][1:]:
        row["independence"] = "syndicated_copy"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert (
        "passing_seal_below_depth_floor:outside_in_independent_units"
        in findings
    )


def test_passing_seal_requires_two_dry_saturation_batches(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    phase2 = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "serp_phase2"
    )
    phase2["completed_job_ids"] = list(phase2["planned_job_ids"])
    phase2["completed_count"] = phase2["planned_count"]
    phase2["unrun_job_ids"] = []
    phase2["unrun_count"] = 0
    seal["resume_contract"]["pending_job_ids"] = []
    ledger_path = Path(seal["evidence_depth_ledger"]["locator"])
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["closure"]["batches"][-1]["material_incremental_value"] = True
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    seal["evidence_depth_ledger"]["sha256"] = _artifact_hash(ledger_path)
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "saturation_batch_still_material" in findings
    assert "passing_seal_without_saturation_closure" in findings


def test_legacy_v2_requires_explicit_historical_audit(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["schema_version"] = LEGACY_SEAL_VERSION
    seal.pop("evidence_depth_ledger")
    path = _write_seal(tmp_path, seal)

    assert "legacy_v2_requires_explicit_historical_audit" in (
        validate_phase_acquisition_seal(seal_path=path, repo_root=tmp_path)
    )
    assert validate_phase_acquisition_seal(
        seal_path=path,
        repo_root=tmp_path,
        allow_legacy_v2=True,
    ) == []


def test_passing_seal_cannot_omit_mandatory_specialist_route(
    tmp_path: Path,
) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_job_accounting"] = [
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] != "google_ads_transparency"
    ]

    findings = _validate(tmp_path, seal)

    assert any(
        finding.startswith("missing_required_route_accounting:")
        and "google_ads_transparency" in finding
        for finding in findings
    )


def test_triggered_native_route_requires_accounting(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_capability_preflight"]["native_social"]["youtube"] = {
        "trigger": "required",
        "route_status": "ready",
    }

    findings = _validate(tmp_path, seal)

    assert any(
        finding.startswith("missing_required_route_accounting:")
        and "native_youtube" in finding
        for finding in findings
    )


@pytest.mark.parametrize(
    "route_id",
    ["google_ads_transparency", "reddit_weekly_lake"],
)
def test_passing_mandatory_route_cannot_self_label_optional_and_unrun(
    tmp_path: Path, route_id: str
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row for row in seal["route_job_accounting"] if row["route_id"] == route_id
    )
    route["required"] = False
    route["material"] = False
    route["unrun_job_ids"] = list(route["planned_job_ids"])
    route["unrun_count"] = route["planned_count"]
    route["completed_job_ids"] = []
    route["completed_count"] = 0
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert f"mandatory_route_not_required:{route_id}" in findings
    assert f"passing_mandatory_route_has_unrun_jobs:{route_id}" in findings


def test_triggered_native_route_cannot_be_optional_and_unrun(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    seal["route_capability_preflight"]["native_social"]["youtube"] = {
        "trigger": "required",
        "route_status": "ready",
    }
    artifact = _artifact(tmp_path, "native_youtube.md")
    seal["route_job_accounting"].append(
        {
            "route_id": "native_youtube",
            "phase": "co3",
            "required": False,
            "material": False,
            "planned_job_ids": ["YT-001"],
            "planned_count": 1,
            "completed_job_ids": [],
            "completed_count": 0,
            "blocked_job_ids": [],
            "blocked_count": 0,
            "unrun_job_ids": ["YT-001"],
            "unrun_count": 1,
            "terminal_artifact_locator": artifact["locator"],
            "terminal_artifact_sha256": artifact["sha256"],
        }
    )
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    findings = _validate(tmp_path, seal)

    assert "mandatory_route_not_required:native_youtube" in findings
    assert "passing_mandatory_route_has_unrun_jobs:native_youtube" in findings


def test_mandatory_route_actor_ownership_cannot_be_swapped(tmp_path: Path) -> None:
    seal = _blocked_seal(tmp_path)
    authorization = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "official_retailer_authorization"
    )
    retailer_pdp = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "retailer_full_pdp"
    )
    authorization["phase"] = "co2"
    retailer_pdp["phase"] = "co1"

    findings = _validate(tmp_path, seal)

    assert "route_phase_mismatch:official_retailer_authorization:co1" in findings
    assert "route_phase_mismatch:retailer_full_pdp:co2" in findings


@pytest.mark.parametrize("material", [None, "false"])
def test_non_boolean_material_cannot_forge_non_material_block(
    tmp_path: Path, material: object
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "google_ads_transparency"
    )
    if material is None:
        route.pop("material")
    else:
        route["material"] = material
    route["completed_job_ids"] = []
    route["completed_count"] = 0
    route["blocked_job_ids"] = list(route["planned_job_ids"])
    route["blocked_count"] = route["planned_count"]
    seal.update(
        {
            "acquisition_gate": "pass",
            "seal_state": "SEALED_READY_FOR_DELIVER",
            "deliver_allowed": True,
            "post_phase1_continuation_mode": "full",
        }
    )

    assert "invalid_route_material_flag:google_ads_transparency" in _validate(
        tmp_path, seal
    )


@pytest.mark.parametrize("count", [True, 1.0])
def test_route_job_counts_require_exact_integers(
    tmp_path: Path, count: object
) -> None:
    seal = _blocked_seal(tmp_path)
    route = next(
        row
        for row in seal["route_job_accounting"]
        if row["route_id"] == "google_ads_transparency"
    )
    route["planned_count"] = count
    route["completed_count"] = count

    findings = _validate(tmp_path, seal)

    assert findings.count("invalid_planned_count_type") == 1
    assert findings.count("invalid_completed_count_type") == 1
