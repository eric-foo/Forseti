"""Validate acquisition accounting and evidence depth in an Understanding seal."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import hash_file, sha256_bytes  # noqa: E402


SEAL_VERSION = "phase_acquisition_seal_v3"
LEGACY_SEAL_VERSION = "phase_acquisition_seal_v2"
DEPTH_LEDGER_VERSION = "understanding_evidence_depth_v1"
BROAD_UNDERSTANDING_PROFILE = "broad_company_understanding_v1"
BROAD_UNDERSTANDING_FLOORS = {
    "outside_in_independent_units": 12,
    "outside_in_independent_origins": 12,
    "retailer_review_unique_rows": 750,
    "retailer_review_corpora": 2,
    "retailer_review_product_contexts": 5,
    "retailer_review_categories": 3,
    "reddit_forum_threads": 20,
    "reddit_forum_communities": 4,
    "reddit_forum_topic_categories": 3,
    "native_social_posts": 30,
    "native_social_creators": 20,
    "native_social_platforms": 2,
    "native_social_perspectives": 2,
}
MANDATORY_ROUTE_IDS = {
    "serp_phase1",
    "official_retailer_authorization",
    "google_ads_transparency",
    "meta_ads_library",
    "retailer_full_pdp",
    "reddit_weekly_lake",
    "reddit_community_scout",
    "serp_phase2",
}
MANDATORY_ROUTE_PHASES = {
    "serp_phase1": "serp_phase1",
    "official_retailer_authorization": "co1",
    "google_ads_transparency": "co1",
    "meta_ads_library": "co1",
    "retailer_full_pdp": "co2",
    "reddit_weekly_lake": "co3",
    "reddit_community_scout": "co3",
    "serp_phase2": "serp_phase2",
}
_YAML_FENCE = re.compile(r"```yaml\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_TEXT_ARTIFACT_SUFFIXES = {".json", ".md", ".yaml", ".yml"}


def validate_phase_acquisition_seal(
    *,
    seal_path: Path,
    repo_root: Path,
    allow_legacy_v2: bool = False,
) -> list[str]:
    seal = _load_seal(seal_path)
    findings: list[str] = []
    schema_version = seal.get("schema_version")
    if schema_version == LEGACY_SEAL_VERSION and not allow_legacy_v2:
        findings.append("legacy_v2_requires_explicit_historical_audit")
    elif schema_version not in {SEAL_VERSION, LEGACY_SEAL_VERSION}:
        findings.append("invalid_schema_version")

    gate = seal.get("acquisition_gate")
    seal_state = seal.get("seal_state")
    deliver_allowed = seal.get("deliver_allowed")
    valid_pass = (
        gate == "pass"
        and seal_state == "SEALED_READY_FOR_DELIVER"
        and deliver_allowed is True
    )
    valid_block = (
        gate == "blocked"
        and seal_state == "BLOCKED_ACQUISITION_INCOMPLETE"
        and deliver_allowed is False
    )
    if not (valid_pass or valid_block):
        findings.append("inconsistent_gate_state")

    _validate_controller_placement(seal, findings)
    conditional_routes = _validate_capability_preflight(
        seal, valid_pass=valid_pass, findings=findings
    )
    _validate_specialist_returns(
        seal, repo_root=repo_root, findings=findings
    )
    material_pending = _validate_route_accounting(
        seal,
        repo_root=repo_root,
        valid_pass=valid_pass,
        conditional_routes=conditional_routes,
        findings=findings,
    )
    _validate_decision_receipt(seal, repo_root=repo_root, findings=findings)
    _validate_resume_contract(
        seal,
        repo_root=repo_root,
        expected_pending=material_pending,
        valid_pass=valid_pass,
        findings=findings,
    )
    if schema_version == SEAL_VERSION:
        _validate_understanding_evidence_depth(
            seal,
            repo_root=repo_root,
            valid_pass=valid_pass,
            findings=findings,
        )
    continuation = seal.get("post_phase1_continuation_mode")
    if continuation not in {"full", "bounded_salvage", "stop"}:
        findings.append("invalid_post_phase1_continuation_mode")
    elif valid_pass and continuation != "full":
        findings.append("passing_seal_requires_full_continuation")
    return sorted(set(findings))


def _validate_understanding_evidence_depth(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    valid_pass: bool,
    findings: list[str],
) -> None:
    reference = seal.get("evidence_depth_ledger")
    if not isinstance(reference, dict):
        findings.append("missing_evidence_depth_ledger")
        return
    locator = reference.get("locator")
    digest = reference.get("sha256")
    before = len(findings)
    _verify_artifact(
        locator,
        digest,
        repo_root=repo_root,
        code="evidence_depth_ledger",
        findings=findings,
    )
    if len(findings) != before:
        return
    ledger_path = Path(str(locator))
    if not ledger_path.is_absolute():
        ledger_path = repo_root / ledger_path
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(
            f"invalid_evidence_depth_ledger:{type(exc).__name__}"
        )
        return
    if not isinstance(ledger, dict):
        findings.append("invalid_evidence_depth_ledger_shape")
        return
    if ledger.get("schema_version") != DEPTH_LEDGER_VERSION:
        findings.append("invalid_evidence_depth_ledger_version")
    if ledger.get("profile_id") != BROAD_UNDERSTANDING_PROFILE:
        findings.append("invalid_understanding_completion_profile")
    seal_subject = seal.get("subject")
    if not isinstance(seal_subject, str) or not seal_subject:
        findings.append("missing_seal_subject")
    elif ledger.get("subject") != seal_subject:
        findings.append("evidence_depth_ledger_subject_mismatch")
    seal_cycle_id = seal.get("cycle_id")
    if not isinstance(seal_cycle_id, str) or not seal_cycle_id:
        findings.append("missing_seal_cycle_id")
    elif ledger.get("cycle_id") != seal_cycle_id:
        findings.append("evidence_depth_ledger_cycle_id_mismatch")

    artifacts = _validate_depth_artifacts(
        ledger.get("artifacts"), repo_root=repo_root, findings=findings
    )
    families = ledger.get("families")
    if not isinstance(families, dict):
        findings.append("missing_evidence_depth_families")
        families = {}
    metrics: dict[str, int] = {}
    metrics.update(
        _validate_outside_in_depth(
            families.get("outside_in"), artifacts=artifacts, findings=findings
        )
    )
    metrics.update(
        _validate_retailer_review_depth(
            families.get("retailer_reviews"),
            artifacts=artifacts,
            require_complete=valid_pass,
            findings=findings,
        )
    )
    metrics.update(
        _validate_reddit_depth(
            families.get("reddit_forum"), artifacts=artifacts, findings=findings
        )
    )
    metrics.update(
        _validate_native_social_depth(
            families.get("native_social"), artifacts=artifacts, findings=findings
        )
    )
    closure_complete = _validate_depth_closure(
        ledger.get("closure"), require_complete=valid_pass, findings=findings
    )
    if valid_pass:
        for metric, minimum in BROAD_UNDERSTANDING_FLOORS.items():
            if metrics.get(metric, 0) < minimum:
                findings.append(f"passing_seal_below_depth_floor:{metric}")
        if not closure_complete:
            findings.append("passing_seal_without_saturation_closure")


def _validate_depth_artifacts(
    value: Any,
    *,
    repo_root: Path,
    findings: list[str],
) -> set[str]:
    if not isinstance(value, list) or not value:
        findings.append("missing_evidence_depth_artifacts")
        return set()
    artifact_ids: set[str] = set()
    for row in value:
        if not isinstance(row, dict):
            findings.append("invalid_evidence_depth_artifact")
            continue
        artifact_id = row.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            findings.append("missing_evidence_depth_artifact_id")
            continue
        if artifact_id in artifact_ids:
            findings.append("duplicate_evidence_depth_artifact_id")
            continue
        artifact_ids.add(artifact_id)
        _verify_artifact(
            row.get("locator"),
            row.get("sha256"),
            repo_root=repo_root,
            code="evidence_depth_source",
            findings=findings,
        )
    return artifact_ids


def _valid_depth_rows(
    value: Any,
    *,
    row_name: str,
    id_field: str,
    artifacts: set[str],
    findings: list[str],
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        findings.append(f"missing_{row_name}_rows")
        return []
    rows: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, dict):
            findings.append(f"invalid_{row_name}_row")
            continue
        row_id = row.get(id_field)
        if not isinstance(row_id, str) or not row_id:
            findings.append(f"missing_{row_name}_{id_field}")
            continue
        if row_id in seen:
            findings.append(f"duplicate_{row_name}_{id_field}")
            continue
        seen.add(row_id)
        artifact_id = row.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id not in artifacts:
            findings.append(f"unresolved_{row_name}_artifact")
        rows.append(row)
    return rows


def _string_set(value: Any, *, code: str, findings: list[str]) -> set[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        findings.append(code)
        return set()
    return set(value)


def _validate_outside_in_depth(
    value: Any, *, artifacts: set[str], findings: list[str]
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_outside_in_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("units"),
        row_name="outside_in",
        id_field="unit_id",
        artifacts=artifacts,
        findings=findings,
    )
    origins: set[str] = set()
    independent_units = 0
    for row in rows:
        origin = row.get("origin_id")
        if not isinstance(origin, str) or not origin:
            findings.append("missing_outside_in_origin_id")
            continue
        if row.get("independence") not in {
            "independent_origin",
            "same_origin",
            "syndicated_copy",
        }:
            findings.append("invalid_outside_in_independence")
            continue
        echo_group = row.get("echo_group_id")
        if not isinstance(echo_group, str) or not echo_group:
            findings.append("missing_outside_in_echo_group")
        if row.get("independence") == "independent_origin":
            independent_units += 1
            origins.add(origin)
    return {
        "outside_in_independent_units": independent_units,
        "outside_in_independent_origins": len(origins),
    }


def _validate_retailer_review_depth(
    value: Any,
    *,
    artifacts: set[str],
    require_complete: bool,
    findings: list[str],
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_retailer_review_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("corpora"),
        row_name="retailer_review",
        id_field="corpus_id",
        artifacts=artifacts,
        findings=findings,
    )
    total = 0
    product_contexts: set[str] = set()
    categories: set[str] = set()
    rating_bands: set[str] = set()
    for row in rows:
        unique_count = row.get("unique_review_count")
        duplicate_count = row.get("cross_corpus_duplicate_count")
        if (
            not isinstance(unique_count, int)
            or isinstance(unique_count, bool)
            or unique_count < 0
        ):
            findings.append("invalid_unique_review_count")
            unique_count = 0
        if (
            not isinstance(duplicate_count, int)
            or isinstance(duplicate_count, bool)
            or duplicate_count < 0
            or duplicate_count > unique_count
        ):
            findings.append("invalid_cross_corpus_duplicate_count")
            duplicate_count = 0
        total += unique_count - duplicate_count
        product_contexts.update(
            _string_set(
                row.get("product_context_ids"),
                code="invalid_retailer_review_product_contexts",
                findings=findings,
            )
        )
        categories.update(
            _string_set(
                row.get("category_ids"),
                code="invalid_retailer_review_categories",
                findings=findings,
            )
        )
        rating_bands.update(
            _string_set(
                row.get("rating_bands"),
                code="invalid_retailer_review_rating_bands",
                findings=findings,
            )
        )
    # Band completeness is part of the passing-seal entry floor, not a shape
    # requirement on an honestly partial blocked seal.
    if (
        require_complete
        and rows
        and not {"low", "mid", "high"}.issubset(rating_bands)
    ):
        findings.append("retailer_review_rating_bands_incomplete")
    return {
        "retailer_review_unique_rows": total,
        "retailer_review_corpora": len(rows),
        "retailer_review_product_contexts": len(product_contexts),
        "retailer_review_categories": len(categories),
    }


def _validate_reddit_depth(
    value: Any, *, artifacts: set[str], findings: list[str]
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_reddit_forum_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("threads"),
        row_name="reddit_forum",
        id_field="thread_id",
        artifacts=artifacts,
        findings=findings,
    )
    communities: set[str] = set()
    topics: set[str] = set()
    independent_threads = 0
    for row in rows:
        community = row.get("community_id")
        topic = row.get("topic_category")
        if not isinstance(community, str) or not community:
            findings.append("missing_reddit_forum_community")
        if not isinstance(topic, str) or not topic:
            findings.append("missing_reddit_forum_topic_category")
        if row.get("independence") not in {
            "independent_thread",
            "duplicate_thread",
        }:
            findings.append("invalid_reddit_forum_independence")
        elif row.get("independence") == "independent_thread":
            independent_threads += 1
            if isinstance(community, str) and community:
                communities.add(community)
            if isinstance(topic, str) and topic:
                topics.add(topic)
    return {
        "reddit_forum_threads": independent_threads,
        "reddit_forum_communities": len(communities),
        "reddit_forum_topic_categories": len(topics),
    }


def _validate_native_social_depth(
    value: Any, *, artifacts: set[str], findings: list[str]
) -> dict[str, int]:
    if not isinstance(value, dict):
        findings.append("missing_native_social_depth")
        return {}
    rows = _valid_depth_rows(
        value.get("posts"),
        row_name="native_social",
        id_field="unit_id",
        artifacts=artifacts,
        findings=findings,
    )
    creators: set[str] = set()
    platforms: set[str] = set()
    perspectives: set[str] = set()
    independent_posts = 0
    post_ids: set[tuple[str, str]] = set()
    for row in rows:
        platform = row.get("platform")
        post_id = row.get("post_id")
        creator_id = row.get("creator_id")
        perspective = row.get("perspective")
        if not isinstance(platform, str) or not platform:
            findings.append("missing_native_social_platform")
            platform = ""
        if not isinstance(post_id, str) or not post_id:
            findings.append("missing_native_social_post_id")
        elif (platform, post_id) in post_ids:
            findings.append("duplicate_native_social_post_id")
        else:
            post_ids.add((platform, post_id))
        if not isinstance(creator_id, str) or not creator_id:
            findings.append("missing_native_social_creator_id")
        if perspective not in {"positive", "neutral", "critical", "mixed"}:
            findings.append("invalid_native_social_perspective")
        if row.get("independence") not in {
            "independent_post",
            "same_creator_followup",
            "syndicated_copy",
        }:
            findings.append("invalid_native_social_independence")
        elif row.get("independence") == "independent_post":
            independent_posts += 1
            if platform:
                platforms.add(platform)
            if isinstance(creator_id, str) and creator_id:
                creators.add(creator_id)
            if perspective in {"positive", "neutral", "critical", "mixed"}:
                perspectives.add(str(perspective))
    return {
        "native_social_posts": independent_posts,
        "native_social_creators": len(creators),
        "native_social_platforms": len(platforms),
        "native_social_perspectives": len(perspectives),
    }


def _validate_depth_closure(
    value: Any, *, require_complete: bool, findings: list[str]
) -> bool:
    if not isinstance(value, dict):
        findings.append("missing_evidence_depth_closure")
        return False
    complete = True
    echo_state = value.get("echo_groups_adjudicated")
    if not isinstance(echo_state, bool):
        findings.append("invalid_echo_group_adjudication_state")
        complete = False
    elif echo_state is not True:
        if require_complete:
            findings.append("echo_groups_not_adjudicated")
        complete = False
    seams = value.get("material_seams")
    if not isinstance(seams, list) or not seams:
        findings.append("missing_material_seam_accounting")
        complete = False
    else:
        seam_ids: set[str] = set()
        for row in seams:
            if not isinstance(row, dict):
                findings.append("invalid_material_seam")
                complete = False
                continue
            seam_id = row.get("seam_id")
            if not isinstance(seam_id, str) or not seam_id or seam_id in seam_ids:
                findings.append("invalid_material_seam_id")
                complete = False
            else:
                seam_ids.add(seam_id)
            disposition = row.get("disposition")
            if disposition not in {
                "supported",
                "contradicted",
                "bounded",
                "blocked_no_remaining_path",
                "open",
                "blocked_route_available",
            }:
                findings.append("invalid_material_seam_disposition")
                complete = False
            elif disposition in {"open", "blocked_route_available"}:
                if require_complete:
                    findings.append("open_material_seam")
                complete = False
    batches = value.get("batches")
    if not isinstance(batches, list):
        findings.append("invalid_saturation_batches")
        complete = False
    elif len(batches) < 2:
        if require_complete:
            findings.append("insufficient_saturation_batches")
        complete = False
    else:
        for row in batches[-2:]:
            if not isinstance(row, dict):
                findings.append("invalid_saturation_batch")
                complete = False
                continue
            checked = row.get("candidate_moves_checked")
            if (
                not isinstance(checked, int)
                or isinstance(checked, bool)
                or checked < 1
            ):
                findings.append("saturation_batch_checked_no_moves")
                complete = False
            material_value = row.get("material_incremental_value")
            if not isinstance(material_value, bool):
                findings.append("invalid_saturation_batch_material_value")
                complete = False
            elif material_value is not False:
                if require_complete:
                    findings.append("saturation_batch_still_material")
                complete = False
            for field in ("new_material_seams", "changed_material_dispositions"):
                metric = row.get(field)
                if (
                    not isinstance(metric, int)
                    or isinstance(metric, bool)
                    or metric < 0
                ):
                    findings.append(f"invalid_saturation_batch_{field}")
                    complete = False
                elif metric != 0:
                    if require_complete:
                        findings.append(f"saturation_batch_nonzero_{field}")
                    complete = False
    remaining = value.get("remaining_moves")
    if not isinstance(remaining, list):
        findings.append("missing_remaining_move_accounting")
        complete = False
    else:
        for row in remaining:
            if not isinstance(row, dict):
                findings.append("invalid_remaining_move")
                complete = False
                continue
            disposition = row.get("disposition")
            if disposition not in {
                "dominated",
                "source_exhausted",
                "unsafe_or_prohibited",
                "blocked_no_route",
                "deferred_nonmaterial",
                "material_open",
                "blocked_route_available",
            }:
                findings.append("invalid_remaining_move_disposition")
                complete = False
            material = row.get("material")
            if not isinstance(material, bool):
                findings.append("invalid_remaining_move_material_flag")
                complete = False
            elif material is not False:
                if require_complete:
                    findings.append("material_remaining_move")
                complete = False
    conclusion = value.get("conclusion")
    if conclusion not in {"complete", "incomplete"}:
        findings.append("invalid_evidence_depth_conclusion")
        complete = False
    elif conclusion != "complete":
        complete = False
    return complete


def _load_seal(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"seal could not be read: {exc}") from exc
    for block in _YAML_FENCE.findall(text):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict) and isinstance(
            parsed.get("phase_acquisition_seal"), dict
        ):
            return parsed["phase_acquisition_seal"]
    raise ValueError("no phase_acquisition_seal YAML block found")


def _validate_controller_placement(
    seal: Mapping[str, Any], findings: list[str]
) -> None:
    value = seal.get("controller_placement")
    if not isinstance(value, dict):
        findings.append("missing_controller_placement")
        return
    if value.get("controller_actor") != "CO0" or value.get("placement") != (
        "top_level"
    ):
        findings.append("invalid_controller_placement")
    if value.get("worker_slots_required") != 3:
        findings.append("invalid_worker_slot_requirement")
    available = value.get("worker_slots_available")
    if not isinstance(available, int) or isinstance(available, bool) or available < 3:
        findings.append("blocked_controller_capacity")


def _validate_capability_preflight(
    seal: Mapping[str, Any], *, valid_pass: bool, findings: list[str]
) -> set[str]:
    conditional_routes: set[str] = set()
    value = seal.get("route_capability_preflight")
    if not isinstance(value, dict):
        findings.append("missing_route_capability_preflight")
        return conditional_routes
    if value.get("checked_before_network_capture") is not True:
        findings.append("capability_preflight_not_forefront")
    google = value.get("google_serp")
    if not isinstance(google, dict):
        findings.append("missing_google_serp_capability")
    else:
        mode = google.get("mode")
        if mode not in {"persistent_fallback", "cooldown_only"}:
            findings.append("invalid_google_recovery_mode")
        if google.get("primary_route_ready") is not True:
            findings.append("google_primary_route_not_ready")
        if google.get("queue_state_writable") is not True:
            findings.append("google_queue_state_not_writable")
        if mode == "persistent_fallback" and google.get(
            "persistent_fallback_ready"
        ) is not True:
            findings.append("google_persistent_fallback_not_ready")
    reddit = value.get("reddit_weekly_lake")
    if not isinstance(reddit, dict) or reddit.get("reader_status") not in {
        "ready",
        "blocked",
    }:
        findings.append("invalid_reddit_weekly_capability")
    elif valid_pass and reddit.get("reader_status") != "ready":
        findings.append("passing_seal_with_blocked_reddit_weekly_reader")
    paid = value.get("paid_ad_transparency")
    if not isinstance(paid, dict):
        findings.append("missing_paid_ad_capability")
    else:
        for key in ("google_ads_transparency", "meta_ads_library"):
            if paid.get(key) not in {"ready", "identity_pending", "blocked"}:
                findings.append(f"invalid_{key}_capability")
            elif valid_pass and paid.get(key) != "ready":
                findings.append(f"passing_seal_without_{key}_capability")
    shop = value.get("tiktok_shop")
    if not isinstance(shop, dict):
        findings.append("missing_tiktok_shop_capability")
    else:
        trigger = shop.get("trigger")
        route_status = shop.get("route_status")
        if trigger not in {"required", "not_required", "unknown"}:
            findings.append("invalid_tiktok_shop_trigger")
        if route_status not in {
            "ready",
            "not_checked_until_trigger",
            "EGRESS_SESSION_UNHEALTHY",
            "TTSHOP_ROUTE_BLOCKED",
            "EGRESS_COUNTRY_WRONG",
        }:
            findings.append("invalid_tiktok_shop_route_status")
        if valid_pass and trigger == "unknown":
            findings.append("passing_seal_with_unknown_tiktok_shop_trigger")
        if valid_pass and trigger == "required" and route_status != "ready":
            findings.append("passing_seal_with_blocked_required_tiktok_shop")
        if trigger == "required":
            conditional_routes.add("tiktok_shop")
    native = value.get("native_social")
    if not isinstance(native, dict):
        findings.append("missing_native_social_capability")
    else:
        for platform in ("tiktok", "instagram", "youtube"):
            row = native.get(platform)
            if not isinstance(row, dict):
                findings.append(f"missing_native_{platform}_capability")
                continue
            trigger = row.get("trigger")
            route_status = row.get("route_status")
            if trigger not in {"required", "not_required", "unknown"}:
                findings.append(f"invalid_native_{platform}_trigger")
            if route_status not in {
                "ready",
                "not_checked_until_trigger",
                "blocked",
            }:
                findings.append(f"invalid_native_{platform}_route_status")
            if valid_pass and trigger == "unknown":
                findings.append(f"passing_seal_with_unknown_native_{platform}_trigger")
            if valid_pass and trigger == "required" and route_status != "ready":
                findings.append(f"passing_seal_with_blocked_native_{platform}")
            if trigger == "required":
                conditional_routes.add(f"native_{platform}")
    return conditional_routes


def _validate_specialist_returns(
    seal: Mapping[str, Any], *, repo_root: Path, findings: list[str]
) -> None:
    rows = seal.get("specialist_returns")
    if not isinstance(rows, list):
        findings.append("missing_specialist_returns")
        return
    actors: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_specialist_return")
            continue
        actor = row.get("actor")
        actors.append(str(actor))
        _verify_artifact(
            row.get("terminal_locator"),
            row.get("sha256"),
            repo_root=repo_root,
            code="specialist_terminal",
            findings=findings,
        )
    if sorted(actors) != ["CO1", "CO2", "CO3"]:
        findings.append("specialist_returns_must_be_co1_co2_co3")


def _validate_route_accounting(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    valid_pass: bool,
    conditional_routes: set[str],
    findings: list[str],
) -> set[str]:
    rows = seal.get("route_job_accounting")
    if not isinstance(rows, list) or not rows:
        findings.append("missing_route_job_accounting")
        return set()
    route_ids: set[str] = set()
    global_jobs: set[str] = set()
    phases: set[str] = set()
    material_pending: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            findings.append("invalid_route_job_accounting_row")
            continue
        route_id = row.get("route_id")
        if not isinstance(route_id, str) or not route_id:
            findings.append("missing_route_id")
            continue
        if route_id in route_ids:
            findings.append("duplicate_route_id")
        route_ids.add(route_id)
        phase = row.get("phase")
        if isinstance(phase, str):
            phases.add(phase)
        if not isinstance(row.get("required"), bool):
            findings.append(f"invalid_route_required_flag:{route_id}")
        if not isinstance(row.get("material"), bool):
            findings.append(f"invalid_route_material_flag:{route_id}")
        lists: dict[str, list[str]] = {}
        for name in ("planned", "completed", "blocked", "unrun"):
            raw = row.get(f"{name}_job_ids")
            if not isinstance(raw, list) or any(
                not isinstance(item, str) or not item for item in raw
            ):
                findings.append(f"invalid_{name}_job_ids")
                raw = []
            if len(raw) != len(set(raw)):
                findings.append(f"duplicate_{name}_job_ids")
            lists[name] = raw
            count = row.get(f"{name}_count")
            if not isinstance(count, int) or isinstance(count, bool):
                findings.append(f"invalid_{name}_count_type")
            if count != len(raw):
                findings.append(f"{name}_count_mismatch")
        planned = set(lists["planned"])
        required_routes = MANDATORY_ROUTE_IDS | conditional_routes
        if route_id in required_routes:
            if not planned:
                findings.append(f"mandatory_route_has_no_accounting_job:{route_id}")
            if row.get("required") is not True:
                findings.append(f"mandatory_route_not_required:{route_id}")
            expected_phase = MANDATORY_ROUTE_PHASES.get(route_id, "co3")
            if phase != expected_phase:
                findings.append(
                    f"route_phase_mismatch:{route_id}:{expected_phase}"
                )
            if valid_pass and lists["unrun"]:
                findings.append(
                    f"passing_mandatory_route_has_unrun_jobs:{route_id}"
                )
        disposition_sets = [
            set(lists["completed"]),
            set(lists["blocked"]),
            set(lists["unrun"]),
        ]
        if any(
            disposition_sets[left] & disposition_sets[right]
            for left in range(3)
            for right in range(left + 1, 3)
        ):
            findings.append("job_dispositions_overlap")
        if planned != set().union(*disposition_sets):
            findings.append("planned_jobs_not_fully_accounted")
        if global_jobs & planned:
            findings.append("job_id_reused_across_routes")
        global_jobs.update(planned)
        pending = set(lists["blocked"]) | set(lists["unrun"])
        if row.get("required") is True and row.get("material") is True:
            material_pending.update(pending)
            if valid_pass and pending:
                findings.append("passing_seal_has_material_pending_jobs")
        _verify_artifact(
            row.get("terminal_artifact_locator"),
            row.get("terminal_artifact_sha256"),
            repo_root=repo_root,
            code="route_terminal_artifact",
            findings=findings,
        )
    missing_routes = sorted((MANDATORY_ROUTE_IDS | conditional_routes) - route_ids)
    if missing_routes:
        findings.append("missing_required_route_accounting:" + ",".join(missing_routes))
    for phase in ("serp_phase1", "co1", "co2", "co3", "serp_phase2"):
        if phase not in phases:
            findings.append(f"missing_{phase}_accounting")
    return material_pending


def _validate_decision_receipt(
    seal: Mapping[str, Any], *, repo_root: Path, findings: list[str]
) -> None:
    receipt = seal.get("serp_phase2_decision_receipt")
    if not isinstance(receipt, dict):
        findings.append("missing_serp_phase2_decision_receipt")
        return
    _verify_artifact(
        receipt.get("locator"),
        receipt.get("sha256"),
        repo_root=repo_root,
        code="serp_phase2_decision_receipt",
        findings=findings,
    )
    entries = receipt.get("entries")
    if not isinstance(entries, int) or isinstance(entries, bool) or entries < 0:
        findings.append("invalid_serp_phase2_decision_entry_count")


def _validate_resume_contract(
    seal: Mapping[str, Any],
    *,
    repo_root: Path,
    expected_pending: set[str],
    valid_pass: bool,
    findings: list[str],
) -> None:
    resume = seal.get("resume_contract")
    if not isinstance(resume, dict):
        findings.append("missing_resume_contract")
        return
    pending = resume.get("pending_job_ids")
    if not isinstance(pending, list) or any(
        not isinstance(item, str) or not item for item in pending
    ):
        findings.append("invalid_resume_pending_jobs")
        pending = []
    if set(pending) != expected_pending:
        findings.append("resume_pending_jobs_mismatch")
    if valid_pass and pending:
        findings.append("passing_seal_has_resume_work")
    reusable = resume.get("reusable_artifacts")
    if not isinstance(reusable, list):
        findings.append("invalid_reusable_artifacts")
        return
    for row in reusable:
        if not isinstance(row, dict):
            findings.append("invalid_reusable_artifact")
            continue
        invalid_if = row.get("invalid_if")
        if not isinstance(invalid_if, list) or not invalid_if or any(
            not isinstance(item, str) or not item for item in invalid_if
        ):
            findings.append("missing_reusable_artifact_invalidation")
        _verify_artifact(
            row.get("locator"),
            row.get("sha256"),
            repo_root=repo_root,
            code="reusable_artifact",
            findings=findings,
        )


def _verify_artifact(
    locator: Any,
    digest: Any,
    *,
    repo_root: Path,
    code: str,
    findings: list[str],
) -> None:
    if not isinstance(locator, str) or not locator:
        findings.append(f"missing_{code}_locator")
        return
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest.casefold()):
        findings.append(f"invalid_{code}_sha256")
        return
    path = Path(locator)
    if not path.is_absolute():
        path = repo_root / path
    if not path.is_file():
        findings.append(f"missing_{code}_file")
        return
    if _artifact_hash(path).casefold() != digest.casefold():
        findings.append(f"{code}_hash_mismatch")


def _artifact_hash(path: Path) -> str:
    """Hash seal text canonically while retaining exact-byte binary checks."""
    if path.suffix.lower() not in _TEXT_ARTIFACT_SUFFIXES:
        return hash_file(path)
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_bytes(content)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a phase_acquisition_seal_v3 YAML block and its hashes."
    )
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--allow-legacy-v2",
        action="store_true",
        help=(
            "Audit a historical phase_acquisition_seal_v2. Legacy v2 seals "
            "do not satisfy the current broad-Understanding completion contract."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        seal_schema_version = _load_seal(args.seal.resolve()).get("schema_version")
        findings = validate_phase_acquisition_seal(
            seal_path=args.seal.resolve(),
            repo_root=args.repo_root.resolve(),
            allow_legacy_v2=args.allow_legacy_v2,
        )
    except Exception as exc:  # noqa: BLE001 - controlled validator diagnostic
        parser.exit(
            status=2,
            message=f"phase acquisition seal validation failed: {type(exc).__name__}: {exc}\n",
        )
    payload = {
        "validator": SEAL_VERSION,
        "seal_schema_version": seal_schema_version,
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
