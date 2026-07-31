"""Validate the machine-accounting block in an Understanding acquisition seal."""

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


SEAL_VERSION = "phase_acquisition_seal_v2"
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
) -> list[str]:
    seal = _load_seal(seal_path)
    findings: list[str] = []
    if seal.get("schema_version") != SEAL_VERSION:
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
    continuation = seal.get("post_phase1_continuation_mode")
    if continuation not in {"full", "bounded_salvage", "stop"}:
        findings.append("invalid_post_phase1_continuation_mode")
    elif valid_pass and continuation != "full":
        findings.append("passing_seal_requires_full_continuation")
    return sorted(set(findings))


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
        description="Validate a phase_acquisition_seal_v2 YAML block and its hashes."
    )
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        findings = validate_phase_acquisition_seal(
            seal_path=args.seal.resolve(), repo_root=args.repo_root.resolve()
        )
    except Exception as exc:  # noqa: BLE001 - controlled validator diagnostic
        parser.exit(
            status=2,
            message=f"phase acquisition seal validation failed: {type(exc).__name__}: {exc}\n",
        )
    payload = {
        "validator": "phase_acquisition_seal_v2",
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
