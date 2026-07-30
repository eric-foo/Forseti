"""Lake-native Creator Registry authority and current views.

The legacy v3 epoch folds append-only JSON authority into generated current
views.  The v4 cutover imports that verified state once into lane-specific
SQLite authority; routine Registry mutations then touch only the affected row
and its public projection in one transaction.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from harness_utils import sha256_bytes as _sha256
from data_lake.canonical_json import canonical_record_bytes
from data_lake.root import DataLakeRoot, DataLakeRootError, _atomic_replace, raw_shard
from data_lake.creator_registry_sqlite import (
    CreatorRegistrySqliteError,
    SQLITE_POINTER_SCHEMA_VERSION,
    SQLITE_SCHEMA,
    bootstrap_database as bootstrap_sqlite_database,
    database_ref as sqlite_database_ref,
    delete_candidate as sqlite_delete_candidate,
    insert_candidate as sqlite_insert_candidate,
    load_documents as load_sqlite_documents,
    upgrade_validated_account as sqlite_upgrade_validated_account,
)
from source_capture.models import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map
from capture_spine.tiktok_creator_discovery_frontier.register_lake_writer import (
    load_creator_frontier_dispositions,
)


BASELINE_LANE = "creator_registry_baseline"
CANDIDATE_ADMISSION_LANE = "creator_registry_candidate_admission"
CANDIDATE_RETRACTION_LANE = "creator_registry_candidate_retraction"
ADMISSION_LANE = "creator_registry_account_admission"
JUDGMENT_LANE = "creator_audience_judgment_outcome"
BASELINE_SCHEMA_VERSION = "creator_registry_baseline_v1"
CANDIDATE_ADMISSION_SCHEMA_VERSION = "creator_registry_candidate_admission_v1"
CANDIDATE_RETRACTION_SCHEMA_VERSION = "creator_registry_candidate_retraction_v1"
ADMISSION_SCHEMA_VERSION = "creator_registry_account_admission_v1"
INDEX_SCHEMA_VERSION = "creator_registry_index_v1"
PUBLIC_PROFILE_SCHEMA_VERSION = "creator_profile_public_v1"
GENERATION_MANIFEST_SCHEMA_VERSION = "creator_registry_generation_v3"
CURRENT_POINTER_SCHEMA_VERSION = 3
REGISTRY_ROOT_PARTS = ("indexes", "derived_retrieval", "creator_registry")
CURRENT_FILENAME = "CURRENT"
GENERATIONS_DIRNAME = "generations"
INDEX_FILENAME = "creator_registry_index_v1.json"
PROFILE_FILENAME = "creator_profile_public_v1.json"
MANIFEST_FILENAME = "creator_registry_generation_v3.json"
LEGACY_BASELINE_SURFACE = "creator_registry_legacy_baseline"
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


class CreatorRegistryLakeError(ValueError):
    """Fail-closed lake registry validation, conflict, or freshness error."""


def deterministic_platform_account_id(platform: str, native_id: str) -> str:
    platform_key = _text(platform, "platform").casefold()
    native_key = _text(native_id, "platform native id")
    digest = hashlib.sha256(f"{platform_key}:{native_key}".encode("utf-8")).hexdigest()[:16]
    return f"acct_{platform_key}_{digest}"


def extract_tiktok_packet_identity(data_root: DataLakeRoot, packet_id: str) -> dict[str, str]:
    """Load and verify the stable account identity in one admitted TikTok grid."""
    loaded = data_root.load_raw_packet(packet_id)
    manifest = loaded.manifest
    if manifest.get("source_family") != "tiktok":
        raise CreatorRegistryLakeError(f"packet is not TikTok: {packet_id}")
    matches = []
    for preserved in manifest.get("preserved_files", []):
        if not isinstance(preserved, Mapping):
            continue
        relative = str(preserved.get("relative_packet_path") or "").replace("\\", "/")
        if relative.endswith("tiktok_grid_window.json"):
            matches.append(preserved)
    if len(matches) != 1:
        raise CreatorRegistryLakeError(
            f"TikTok onboarding packet must preserve exactly one grid window; found {len(matches)}"
        )
    preserved = matches[0]
    relative = _text(preserved.get("relative_packet_path"), "grid relative path")
    path = loaded.container.joinpath(*relative.replace("\\", "/").split("/"))
    body = path.read_bytes()
    if len(body) != preserved.get("size_bytes"):
        raise CreatorRegistryLakeError("TikTok grid window size does not match manifest")
    if hashlib.sha256(body).hexdigest() != preserved.get("sha256"):
        raise CreatorRegistryLakeError("TikTok grid window hash does not match manifest")
    grid = _object(json.loads(body.decode("utf-8-sig")), "TikTok grid window")
    handle = _normalize_handle(grid.get("creator_handle"))
    items = grid.get("items")
    if not isinstance(items, list) or not items:
        raise CreatorRegistryLakeError("TikTok grid window has no items")
    observed: set[tuple[str, str, str]] = set()
    for raw_item in items:
        item = _object(raw_item, "TikTok grid item")
        author = _object(item.get("author"), "TikTok grid author")
        observed.add(
            (
                _text(author.get("id"), "TikTok numeric account id"),
                _normalize_handle(author.get("uniqueId")),
                _text(author.get("nickname"), "TikTok display name"),
            )
        )
    if len(observed) != 1:
        raise CreatorRegistryLakeError("TikTok grid items disagree on stable account identity")
    native_id, item_handle, display_name = next(iter(observed))
    if item_handle != handle:
        raise CreatorRegistryLakeError("TikTok grid creator_handle conflicts with item author")
    receipt = grid.get("collection_receipt")
    observed_at = None
    if isinstance(receipt, Mapping):
        observed_at = receipt.get("capture_timestamp")
    if not isinstance(observed_at, str) or not observed_at.strip():
        timing = _object(manifest.get("timing"), "packet timing")
        capture_time = _object(timing.get("capture_time"), "packet capture time")
        observed_at = _text(capture_time.get("value"), "packet capture timestamp")
    rel_pointer = f"raw/{raw_shard(packet_id)}/{packet_id}/{relative.replace('\\', '/')}"
    return {
        "platform": "tiktok",
        "platform_public_account_id": native_id,
        "public_handle": handle,
        "public_display_name": display_name,
        "public_profile_url": f"https://www.tiktok.com/@{handle}",
        "observed_at": observed_at,
        "identity_source_pointer": rel_pointer,
        "handle_source_pointer": f"{rel_pointer}#/items/0/author/uniqueId",
        "display_name_source_pointer": f"{rel_pointer}#/items/0/author/nickname",
        "display_name_source_field": "items[0].author.nickname",
        "evidence_source_family": "tiktok",
        "evidence_source_surface": str(manifest.get("source_surface") or "tiktok_creator_grid"),
    }


def extract_youtube_assessment_packet_identity(
    data_root: DataLakeRoot, packet_id: str
) -> dict[str, str]:
    """Load and verify stable identity from one YouTube creator assessment packet."""
    loaded = data_root.load_raw_packet(packet_id)
    manifest = loaded.manifest
    if manifest.get("source_family") != "youtube":
        raise CreatorRegistryLakeError(f"packet is not YouTube: {packet_id}")
    if manifest.get("source_surface") != "youtube_creator_assessment":
        raise CreatorRegistryLakeError(f"packet is not a YouTube creator assessment: {packet_id}")
    matches = []
    for preserved in manifest.get("preserved_files", []):
        if not isinstance(preserved, Mapping):
            continue
        relative = str(preserved.get("relative_packet_path") or "").replace("\\", "/")
        if relative.endswith("youtube_creator_assessment.json"):
            matches.append(preserved)
    if len(matches) != 1:
        raise CreatorRegistryLakeError(
            "YouTube assessment packet must preserve exactly one assessment JSON"
        )
    preserved = matches[0]
    relative = _text(preserved.get("relative_packet_path"), "assessment relative path")
    path = loaded.container.joinpath(*relative.replace("\\", "/").split("/"))
    body = path.read_bytes()
    if len(body) != preserved.get("size_bytes"):
        raise CreatorRegistryLakeError("YouTube assessment size does not match manifest")
    if hashlib.sha256(body).hexdigest() != preserved.get("sha256"):
        raise CreatorRegistryLakeError("YouTube assessment hash does not match manifest")
    assessment = _object(json.loads(body.decode("utf-8-sig")), "YouTube creator assessment")
    if assessment.get("schema_version") != "youtube_creator_assessment_v0":
        raise CreatorRegistryLakeError("unsupported YouTube creator assessment schema")
    identity = _object(assessment.get("identity"), "YouTube assessment identity")
    channel_id = _text(identity.get("channel_id"), "YouTube channel id")
    if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        raise CreatorRegistryLakeError("YouTube assessment channel id is not canonical")
    handle = _normalize_handle(identity.get("handle"))
    display_name = _text(identity.get("display_name"), "YouTube display name")
    profile_url = _text(identity.get("profile_url"), "YouTube profile URL")
    if profile_url.casefold() != f"https://www.youtube.com/@{handle}".casefold():
        raise CreatorRegistryLakeError("YouTube assessment handle and profile URL disagree")
    observed_at = _text(assessment.get("captured_at_utc"), "YouTube capture timestamp")
    posture = _object(assessment.get("session_posture"), "YouTube session posture")
    if (
        posture.get("required") != "logged_out_fresh_browser_context"
        or posture.get("observed_logged_in") is not False
        or posture.get("context_reused") is not False
    ):
        raise CreatorRegistryLakeError("YouTube assessment lacks logged-out fresh-context proof")
    rel_pointer = f"raw/{raw_shard(packet_id)}/{packet_id}/{relative.replace('\\', '/')}"
    return {
        "platform": "youtube",
        "platform_public_account_id": channel_id,
        "public_handle": handle,
        "public_display_name": display_name,
        "public_profile_url": profile_url,
        "observed_at": observed_at,
        "identity_source_pointer": rel_pointer,
        "handle_source_pointer": f"{rel_pointer}#/identity/handle",
        "display_name_source_pointer": f"{rel_pointer}#/identity/display_name",
        "display_name_source_field": "identity.display_name",
        "evidence_source_family": "youtube",
        "evidence_source_surface": "youtube_creator_assessment",
    }


def resolve_tiktok_profile_subject_id(
    *, data_root: DataLakeRoot, packet_id: str, requested_id: str | None = None
) -> str:
    identity = extract_tiktok_packet_identity(data_root, packet_id)
    return _resolve_profile_subject_id(
        data_root=data_root, identity=identity, requested_id=requested_id
    )


def resolve_youtube_profile_subject_id(
    *, data_root: DataLakeRoot, packet_id: str, requested_id: str | None = None
) -> str:
    identity = extract_youtube_assessment_packet_identity(data_root, packet_id)
    return _resolve_profile_subject_id(
        data_root=data_root, identity=identity, requested_id=requested_id
    )


def _resolve_profile_subject_id(
    *,
    data_root: DataLakeRoot,
    identity: Mapping[str, str],
    requested_id: str | None,
) -> str:
    try:
        index = load_current_creator_registry(data_root)
    except CreatorRegistryLakeError as exc:
        if "has not been migrated" not in str(exc):
            raise
        index = None
    matches = [] if index is None else _matching_index_rows(index, identity)
    if len(matches) > 1:
        raise CreatorRegistryLakeError("TikTok identity matches multiple current registry accounts")
    expected = (
        str(matches[0]["platform_account_id"])
        if matches
        else deterministic_platform_account_id(
            identity["platform"], identity["platform_public_account_id"]
        )
    )
    if requested_id is not None and requested_id != expected:
        if matches:
            raise CreatorRegistryLakeError(
                f"requested profile subject {requested_id!r} conflicts with existing account {expected!r}"
            )
        # A previously validated Judgment may predate deterministic IDs.  Its
        # already-bound subject is retained when no current identity row exists.
        return _text(requested_id, "requested profile subject id")
    return requested_id or expected


def migrate_legacy_registry(
    *,
    data_root: DataLakeRoot,
    account_ledger_path: Path,
    registry_index_path: Path,
    profile_current_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    """Migrate one exact Git baseline, idempotently, then publish current views."""
    documents = {
        "account_ledger": _load_json(account_ledger_path),
        "registry_index": _load_json(registry_index_path),
        "profile_current": _load_json(profile_current_path),
    }
    source_paths = {
        "account_ledger": account_ledger_path,
        "registry_index": registry_index_path,
        "profile_current": profile_current_path,
    }
    source_hashes = {role: _sha256(path.read_bytes()) for role, path in source_paths.items()}
    _validate_legacy_documents(documents)
    existing = _load_authority_records(data_root, allow_missing_baseline=True)
    if existing["baselines"]:
        baseline = existing["baselines"][0]
        if baseline.get("source_hashes") != source_hashes:
            raise CreatorRegistryLakeError(
                "Creator Registry baseline already exists with different source hashes"
            )
        result = publish_creator_registry_generation(data_root, dry_run=dry_run)
        return {
            "status": "dry_run_passed" if dry_run else "already_current",
            "baseline_record_id": baseline["record_id"],
            "would_write_authority": False,
            **result,
        }
    parity = _baseline_parity(documents)
    if dry_run:
        return {
            "status": "dry_run_passed",
            "source_hashes": source_hashes,
            "parity": parity,
            "would_write_authority": True,
        }
    generated_at = _baseline_generated_at(documents)
    packet_id = _write_baseline_source_packet(
        data_root=data_root,
        source_paths=source_paths,
        source_hashes=source_hashes,
        generated_at=generated_at,
    )
    payload = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "raw_anchor": packet_id,
        "generated_at": generated_at,
        "source_hashes": source_hashes,
        "source_packet_members": {
            "account_ledger": "creator_public_handle_linkage_ledger_v0.json",
            "registry_index": "creator_registry_index_v0.json",
            "profile_current": "creator_profile_current_view_v0.json",
        },
        **documents,
    }
    record_id = "crb_" + _sha256(canonical_record_bytes(payload))[:24]
    record = {"record_id": record_id, **payload}
    data_root.append_record(
        subtree="derived",
        raw_anchor=packet_id,
        lane=BASELINE_LANE,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )
    published = publish_creator_registry_generation(data_root)
    return {
        "status": "migrated",
        "baseline_record_id": record_id,
        "raw_anchor": packet_id,
        "parity": parity,
        **published,
    }


def admit_tiktok_creator_candidate(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    frontier_disposition_id: str,
) -> dict[str, Any]:
    """Admit one grid-identified, owner-eligible TikTok account as not onboarded."""
    identity = extract_tiktok_packet_identity(data_root, packet_id)
    return _admit_creator_candidate(
        data_root=data_root,
        packet_id=packet_id,
        frontier_disposition_id=frontier_disposition_id,
        identity=identity,
        account_id=resolve_tiktok_profile_subject_id(
            data_root=data_root, packet_id=packet_id
        ),
    )


def admit_youtube_creator_candidate(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    frontier_disposition_id: str,
) -> dict[str, Any]:
    """Admit one assessed, owner-eligible YouTube channel as not onboarded."""
    identity = extract_youtube_assessment_packet_identity(data_root, packet_id)
    return _admit_creator_candidate(
        data_root=data_root,
        packet_id=packet_id,
        frontier_disposition_id=frontier_disposition_id,
        identity=identity,
        account_id=resolve_youtube_profile_subject_id(
            data_root=data_root, packet_id=packet_id
        ),
    )


def _admit_creator_candidate(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    frontier_disposition_id: str,
    identity: Mapping[str, str],
    account_id: str,
) -> dict[str, Any]:
    platform = identity["platform"]
    frontier = load_creator_frontier_dispositions(data_root)[
        "creator_frontier_disposition_current"
    ]
    matches = [
        row
        for row in frontier["dispositions"]
        if row.get("candidate_key") == f"{platform}:@{identity['public_handle']}"
    ]
    if len(matches) != 1:
        raise CreatorRegistryLakeError(
            "candidate admission requires exactly one current Frontier disposition"
        )
    disposition = matches[0]
    if (
        disposition.get("disposition_id") != frontier_disposition_id
        or disposition.get("status") != "eligible"
    ):
        raise CreatorRegistryLakeError(
            "candidate admission requires the named current eligible Frontier disposition"
        )
    try:
        current_index = load_current_creator_registry(data_root)
    except CreatorRegistryLakeError as exc:
        if "has not been migrated" in str(exc):
            raise CreatorRegistryLakeError(
                "Creator Registry baseline must be migrated before candidate admission"
            ) from exc
        raise
    existing_matches = _matching_index_rows(current_index, identity)
    if len(existing_matches) > 1:
        raise CreatorRegistryLakeError(
            f"{platform.title()} candidate identity matches multiple current Registry accounts"
        )
    account = {
        "platform_account_id": account_id,
        "platform": platform,
        "platform_public_account_id_or_none": identity["platform_public_account_id"],
        "public_handle": identity["public_handle"],
        "public_profile_url": identity["public_profile_url"],
        "handle_source_pointer": identity["handle_source_pointer"],
        "handle_observed_at": identity["observed_at"],
        "public_display_name_or_none": identity["public_display_name"],
        "display_name_source_pointer_or_none": (
            identity["display_name_source_pointer"]
        ),
        "display_name_source_field_or_none": identity["display_name_source_field"],
    }
    payload = {
        "schema_version": CANDIDATE_ADMISSION_SCHEMA_VERSION,
        "raw_anchor": packet_id,
        "admitted_at": identity["observed_at"],
        "platform_account": account,
        "onboarding": {
            "onboarding_state": "not_onboarded",
            "onboarded_at_or_none": None,
            "evidence_packet_id_or_none": packet_id,
            "evidence_source_family_or_none": identity["evidence_source_family"],
            "evidence_source_surface_or_none": identity["evidence_source_surface"],
            "policy_version": "creator_registry_candidate_admission_v1",
        },
        "frontier_disposition": {
            "disposition_id": disposition["disposition_id"],
            "candidate_key": disposition["candidate_key"],
            "record_ref": disposition["authority_record_ref"],
            "record_sha256": disposition["authority_record_sha256"],
        },
        "monitoring_eligible": False,
    }
    record_id = "crc_" + _sha256(canonical_record_bytes(payload))[:24]
    candidate = {"record_id": record_id, **payload}
    if _uses_sqlite_registry(data_root):
        try:
            write_status = sqlite_insert_candidate(
                data_root=data_root,
                row=_candidate_index_row(candidate),
                revision_id=record_id,
                generated_at=identity["observed_at"],
            )
        except CreatorRegistrySqliteError as exc:
            raise CreatorRegistryLakeError(str(exc)) from exc
        index = load_current_creator_registry(data_root)
        public = load_current_creator_profiles(data_root)
        index_matches = [
            row
            for row in index["creator_registry_index"]["platform_accounts"]
            if row.get("platform_account_id") == account_id
        ]
        public_matches = [
            row
            for row in public["creator_profile_public"]["profiles"]
            if row.get("profile_subject_id") == account_id
        ]
        if (
            len(index_matches) != 1
            or index_matches[0].get("onboarding", {}).get("onboarding_state")
            != "not_onboarded"
            or index_matches[0].get("monitoring_eligibility", {}).get("eligible") is not False
            or public_matches
        ):
            raise CreatorRegistryLakeError(
                "candidate Registry SQL readback must be internal not_onboarded, unmonitored, and non-public"
            )
        return {
            "status": write_status,
            "record_id": record_id,
            "platform_account_id": account_id,
            "public_handle": identity["public_handle"],
            **_sqlite_registry_summary(index, public),
        }
    target = (
        data_root.path
        / "derived"
        / hashlib.sha256(packet_id.encode("ascii")).hexdigest()[:3]
        / packet_id
        / CANDIDATE_ADMISSION_LANE
        / record_id
    )
    rendered = canonical_record_bytes(candidate)
    if target.exists():
        if target.read_bytes() != rendered:
            raise CreatorRegistryLakeError("existing candidate admission id has different bytes")
        write_status = "already_current"
    else:
        if existing_matches:
            raise CreatorRegistryLakeError(
                "a Registry account cannot receive a new candidate admission"
            )
        records = _load_authority_records(data_root)
        active_ids = {row["record_id"] for row in records["active_candidate_admissions"]}
        if any(
            row["platform_account"]["platform_account_id"] == account_id
            for row in records["candidate_admissions"]
            if row["record_id"] not in active_ids
        ):
            # A retracted account is absent from the current index, so the generic
            # duplicate-admission conflict below would misreport why it is blocked.
            raise CreatorRegistryLakeError(
                "a retracted candidate account cannot be re-admitted"
            )
        _validate_authority_admission_set(
            records["baselines"][0],
            [*records["candidate_admissions"], candidate],
            records["admissions"],
        )
        data_root.append_record(
            subtree="derived",
            raw_anchor=packet_id,
            lane=CANDIDATE_ADMISSION_LANE,
            record_id=record_id,
            data=rendered,
        )
        write_status = "admitted"
    published = publish_creator_registry_generation(data_root)
    index = load_current_creator_registry(data_root)
    public = load_current_creator_profiles(data_root)
    index_matches = [
        row
        for row in index["creator_registry_index"]["platform_accounts"]
        if row.get("platform_account_id") == account_id
    ]
    public_matches = [
        row
        for row in public["creator_profile_public"]["profiles"]
        if row.get("profile_subject_id") == account_id
    ]
    if (
        len(index_matches) != 1
        or index_matches[0].get("onboarding", {}).get("onboarding_state") != "not_onboarded"
        or index_matches[0].get("monitoring_eligibility", {}).get("eligible") is not False
        or public_matches
    ):
        raise CreatorRegistryLakeError(
            "candidate Registry readback must be internal not_onboarded, unmonitored, and non-public"
        )
    return {
        "status": write_status,
        "record_id": record_id,
        "platform_account_id": account_id,
        "public_handle": identity["public_handle"],
        **published,
    }


def retract_tiktok_creator_candidate(
    *,
    data_root: DataLakeRoot,
    public_handle: str,
) -> dict[str, Any]:
    """Remove one candidate-only account from current Registry authority."""
    handle = _normalize_handle(public_handle)
    pointer = _load_registry_pointer(data_root)
    if pointer.get("pointer_schema_version") == SQLITE_POINTER_SCHEMA_VERSION:
        # Removal is physical and keeps no tombstone, so bind CURRENT to the
        # database before deleting.  Every read path already refuses an unbound
        # pointer/database pair; the destructive path must refuse it first, not
        # discover it on the readback after the row is already gone.
        _load_sqlite_current(data_root, pointer)
        frontier = load_creator_frontier_dispositions(data_root)[
            "creator_frontier_disposition_current"
        ]
        matches = [
            row
            for row in frontier["dispositions"]
            if row.get("candidate_key") == f"tiktok:@{handle}"
        ]
        if len(matches) != 1 or matches[0].get("status") not in {
            "deferred",
            "rejected",
        }:
            raise CreatorRegistryLakeError(
                "candidate removal requires one current deferred or rejected Frontier disposition"
            )
        try:
            removed = sqlite_delete_candidate(
                data_root=data_root,
                normalized_public_handle=handle,
                generated_at=_text(matches[0].get("recorded_at"), "Frontier recorded_at"),
            )
        except CreatorRegistrySqliteError as exc:
            raise CreatorRegistryLakeError(str(exc)) from exc
        index = load_current_creator_registry(data_root)
        public = load_current_creator_profiles(data_root)
        account_id = removed["platform_account_id"]
        if any(
            row.get("platform_account_id") == account_id
            for row in index["creator_registry_index"]["platform_accounts"]
        ) or any(
            row.get("profile_subject_id") == account_id
            for row in public["creator_profile_public"]["profiles"]
        ):
            raise CreatorRegistryLakeError(
                "candidate removal SQL readback remains present in current Registry"
            )
        return {
            "status": "removed",
            "record_id": removed["source_revision_id"],
            "platform_account_id": account_id,
            "public_handle": handle,
            **_sqlite_registry_summary(index, public),
        }

    _require_current_retraction_epoch(data_root)
    records = _load_authority_records(data_root)
    candidates = [
        row
        for row in records["candidate_admissions"]
        if _normalize_handle(row["platform_account"]["public_handle"]) == handle
    ]
    if len(candidates) != 1:
        raise CreatorRegistryLakeError(
            "candidate retraction requires exactly one candidate admission"
        )
    candidate = candidates[0]
    account_id = candidate["platform_account"]["platform_account_id"]
    if any(
        row["platform_account"]["platform_account_id"] == account_id
        for row in records["admissions"]
    ):
        raise CreatorRegistryLakeError(
            "validated or onboarded Registry accounts cannot be candidate-retracted"
        )
    existing = [
        row
        for row in records["candidate_retractions"]
        if row["candidate_admission"]["record_id"] == candidate["record_id"]
    ]
    if len(existing) > 1:
        raise CreatorRegistryLakeError(
            "multiple retractions target the same candidate admission"
        )
    if existing:
        write_status = "already_current"
        retraction = existing[0]
    else:
        frontier = load_creator_frontier_dispositions(data_root)[
            "creator_frontier_disposition_current"
        ]
        matches = [
            row
            for row in frontier["dispositions"]
            if row.get("candidate_key") == f"tiktok:@{handle}"
        ]
        if len(matches) != 1 or matches[0].get("status") not in {
            "deferred",
            "rejected",
        }:
            raise CreatorRegistryLakeError(
                "candidate retraction requires one current deferred or rejected Frontier disposition"
            )
        disposition = matches[0]
        candidate_ref = next(
            ref
            for ref in records["authority_refs"]
            if ref["record_ref"].endswith(f"/{candidate['record_id']}")
        )
        payload = {
            "schema_version": CANDIDATE_RETRACTION_SCHEMA_VERSION,
            "raw_anchor": candidate["raw_anchor"],
            "retracted_at": disposition["recorded_at"],
            "platform_account_id": account_id,
            "public_handle": handle,
            "candidate_admission": {
                "record_id": candidate["record_id"],
                "record_ref": candidate_ref["record_ref"],
                "record_sha256": candidate_ref["sha256"],
            },
            "frontier_disposition": {
                "disposition_id": disposition["disposition_id"],
                "candidate_key": disposition["candidate_key"],
                "record_ref": disposition["authority_record_ref"],
                "record_sha256": disposition["authority_record_sha256"],
            },
        }
        record_id = "crr_" + _sha256(canonical_record_bytes(payload))[:24]
        retraction = {"record_id": record_id, **payload}
        prospective = [*records["candidate_retractions"], retraction]
        _validate_candidate_retraction_set(
            records["baselines"][0],
            records["candidate_admissions"],
            prospective,
            records["admissions"],
        )
        data_root.append_record(
            subtree="derived",
            raw_anchor=candidate["raw_anchor"],
            lane=CANDIDATE_RETRACTION_LANE,
            record_id=record_id,
            data=canonical_record_bytes(retraction),
        )
        write_status = "retracted"
    published = publish_creator_registry_generation(data_root)
    remaining = [
        row
        for row in load_current_creator_registry(data_root)["creator_registry_index"][
            "platform_accounts"
        ]
        if row.get("platform_account_id") == account_id
    ]
    public_matches = [
        row
        for row in load_current_creator_profiles(data_root)["creator_profile_public"][
            "profiles"
        ]
        if row.get("profile_subject_id") == account_id
    ]
    if remaining or public_matches:
        raise CreatorRegistryLakeError(
            "candidate retraction readback remains present in current Registry"
        )
    return {
        "status": write_status,
        "record_id": retraction["record_id"],
        "platform_account_id": account_id,
        "public_handle": handle,
        **published,
    }


def admit_tiktok_creator_account(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    judgment_outcome_path: Path,
) -> dict[str, Any]:
    """Append one validated TikTok onboarding admission and publish/read it back."""
    identity = extract_tiktok_packet_identity(data_root, packet_id)
    return _admit_creator_account(
        data_root=data_root,
        packet_id=packet_id,
        judgment_outcome_path=judgment_outcome_path,
        identity=identity,
    )


def admit_youtube_creator_account(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    judgment_outcome_path: Path,
) -> dict[str, Any]:
    """Append one validated YouTube onboarding admission and publish/read it back."""
    identity = extract_youtube_assessment_packet_identity(data_root, packet_id)
    return _admit_creator_account(
        data_root=data_root,
        packet_id=packet_id,
        judgment_outcome_path=judgment_outcome_path,
        identity=identity,
    )


def _admit_creator_account(
    *,
    data_root: DataLakeRoot,
    packet_id: str,
    judgment_outcome_path: Path,
    identity: Mapping[str, str],
) -> dict[str, Any]:
    platform = identity["platform"]
    outcome_bytes = judgment_outcome_path.read_bytes()
    outcome = _object(json.loads(outcome_bytes.decode("utf-8-sig")), "Judgment outcome")
    if outcome.get("schema_version") != "creator_audience_judgment_outcome_v1":
        raise CreatorRegistryLakeError("unsupported creator audience Judgment outcome schema")
    if outcome.get("status") != "validated" or not isinstance(outcome.get("snapshot_or_none"), Mapping):
        raise CreatorRegistryLakeError("creator audience Judgment outcome is not validated")
    if outcome.get("raw_anchor") != packet_id:
        raise CreatorRegistryLakeError("Judgment outcome raw_anchor does not match onboarding packet")
    snapshot = deepcopy(dict(outcome["snapshot_or_none"]))
    profile_subject_id = _text(outcome.get("profile_subject_id"), "Judgment profile subject id")
    if snapshot.get("profile_subject_id") != profile_subject_id:
        raise CreatorRegistryLakeError("Judgment snapshot profile subject does not match outcome")
    if snapshot.get("platform_account_id") != profile_subject_id:
        raise CreatorRegistryLakeError("Judgment snapshot platform account does not match outcome")
    expected_creator_id = f"{platform}:@{identity['public_handle']}"
    if outcome.get("creator_id") != expected_creator_id or snapshot.get("creator_id") != expected_creator_id:
        raise CreatorRegistryLakeError(
            f"Judgment creator identity does not match captured {platform.title()} identity"
        )
    if snapshot.get("platform_scope") != platform:
        raise CreatorRegistryLakeError(
            f"Judgment snapshot platform scope does not match captured {platform.title()} identity"
        )
    expected_outcome = (
        data_root.path
        / "derived"
        / hashlib.sha256(packet_id.encode("ascii")).hexdigest()[:3]
        / packet_id
        / JUDGMENT_LANE
        / _text(outcome.get("record_id"), "Judgment record id")
    )
    if judgment_outcome_path.resolve() != expected_outcome.resolve():
        raise CreatorRegistryLakeError("Judgment outcome is not the authoritative lake record path")
    if expected_outcome.read_bytes() != outcome_bytes:
        raise CreatorRegistryLakeError("Judgment outcome bytes changed during admission")
    profile_subject_id = _resolve_profile_subject_id(
        data_root=data_root,
        identity=identity,
        requested_id=profile_subject_id,
    )
    current_index = load_current_creator_registry(data_root)
    current_matches = _matching_index_rows(current_index, identity)
    if (
        len(current_matches) != 1
        or current_matches[0].get("platform_account_id") != profile_subject_id
        or current_matches[0].get("onboarding", {}).get("onboarding_state")
        not in {"not_onboarded", "onboarded"}
    ):
        raise CreatorRegistryLakeError(
            "validated onboarding requires exactly one Registry not_onboarded account"
        )
    frontier_rows = load_creator_frontier_dispositions(data_root)[
        "creator_frontier_disposition_current"
    ]["dispositions"]
    current_frontier = [
        row
        for row in frontier_rows
        if row.get("candidate_key") == f"{platform}:@{identity['public_handle']}"
    ]
    if len(current_frontier) > 1:
        raise CreatorRegistryLakeError(
            "validated onboarding found conflicting current Frontier dispositions"
        )
    if current_frontier and current_frontier[0].get("status") in {"deferred", "rejected"}:
        raise CreatorRegistryLakeError(
            "validated onboarding is blocked by the current Frontier disposition"
        )
    manifest = data_root.load_raw_packet(packet_id).manifest
    capture_time = _object(_object(manifest.get("timing"), "packet timing").get("capture_time"), "capture time")
    onboarded_at = _text(capture_time.get("value"), "capture time value")
    account = {
        "platform_account_id": profile_subject_id,
        "platform": platform,
        "platform_public_account_id_or_none": identity["platform_public_account_id"],
        "public_handle": identity["public_handle"],
        "public_profile_url": identity["public_profile_url"],
        "handle_source_pointer": identity["handle_source_pointer"],
        "handle_observed_at": identity["observed_at"],
        "public_display_name_or_none": identity["public_display_name"],
        "display_name_source_pointer_or_none": (
            identity["display_name_source_pointer"]
        ),
        "display_name_source_field_or_none": identity["display_name_source_field"],
    }
    admission_payload = {
        "schema_version": ADMISSION_SCHEMA_VERSION,
        "raw_anchor": packet_id,
        "admitted_at": snapshot.get("generated_at") or onboarded_at,
        "platform_account": account,
        "onboarding": {
            "onboarding_state": "onboarded",
            "onboarded_at_or_none": onboarded_at,
            "evidence_packet_id_or_none": packet_id,
            "evidence_source_family_or_none": manifest.get("source_family"),
            "evidence_source_surface_or_none": manifest.get("source_surface"),
            "policy_version": "creator_registry_onboarding_v1",
        },
        "judgment": {
            "record_id": outcome["record_id"],
            "record_ref": _relative_to_root(data_root, expected_outcome),
            "record_sha256": _sha256(outcome_bytes),
            "snapshot_id": outcome.get("snapshot_id_or_none"),
            "bundle_id": outcome.get("bundle_id"),
            "bundle_hash": outcome.get("bundle_hash"),
        },
        "snapshot": snapshot,
        "monitoring_eligible": True,
    }
    record_id = "cra_" + _sha256(canonical_record_bytes(admission_payload))[:24]
    admission = {"record_id": record_id, **admission_payload}
    if _uses_sqlite_registry(data_root):
        upgraded_row = _validated_index_row(current_matches[0], admission)
        public_profile = _new_public_profile(admission, generated_at=admission_payload["admitted_at"])
        try:
            write_status = sqlite_upgrade_validated_account(
                data_root=data_root,
                account_row=upgraded_row,
                public_profile=public_profile,
                revision_id=record_id,
                generated_at=admission_payload["admitted_at"],
            )
        except CreatorRegistrySqliteError as exc:
            raise CreatorRegistryLakeError(str(exc)) from exc
        index = load_current_creator_registry(data_root)
        public = load_current_creator_profiles(data_root)
        index_matches = [
            row
            for row in index["creator_registry_index"]["platform_accounts"]
            if row.get("platform_account_id") == profile_subject_id
        ]
        public_matches = [
            row
            for row in public["creator_profile_public"]["profiles"]
            if row.get("profile_subject_id") == profile_subject_id
        ]
        if len(index_matches) != 1 or len(public_matches) != 1:
            raise CreatorRegistryLakeError(
                "SQLite Registry readback did not contain exactly one account/profile"
            )
        if public_matches[0].get("audience_triangulation", {}).get(
            "snapshot_id"
        ) != outcome.get("snapshot_id_or_none"):
            raise CreatorRegistryLakeError(
                "SQLite public profile did not join the exact Judgment snapshot"
            )
        return {
            "status": write_status,
            "record_id": record_id,
            "platform_account_id": profile_subject_id,
            "public_handle": identity["public_handle"],
            **_sqlite_registry_summary(index, public),
        }
    target = (
        data_root.path
        / "derived"
        / hashlib.sha256(packet_id.encode("ascii")).hexdigest()[:3]
        / packet_id
        / ADMISSION_LANE
        / record_id
    )
    rendered = canonical_record_bytes(admission)
    if target.exists():
        if target.read_bytes() != rendered:
            raise CreatorRegistryLakeError("existing admission record id has different bytes")
        write_status = "already_current"
    else:
        _validate_admission_conflicts(data_root, admission)
        data_root.append_record(
            subtree="derived",
            raw_anchor=packet_id,
            lane=ADMISSION_LANE,
            record_id=record_id,
            data=rendered,
        )
        write_status = "admitted"
    published = publish_creator_registry_generation(data_root)
    index = load_current_creator_registry(data_root)
    public = load_current_creator_profiles(data_root)
    index_matches = [
        row
        for row in index["creator_registry_index"]["platform_accounts"]
        if row.get("platform_account_id") == profile_subject_id
    ]
    public_matches = [
        row
        for row in public["creator_profile_public"]["profiles"]
        if row.get("profile_subject_id") == profile_subject_id
    ]
    if len(index_matches) != 1 or len(public_matches) != 1:
        raise CreatorRegistryLakeError("published registry readback did not contain exactly one account/profile")
    if public_matches[0].get("audience_triangulation", {}).get("snapshot_id") != outcome.get(
        "snapshot_id_or_none"
    ):
        raise CreatorRegistryLakeError("published public profile did not join the exact Judgment snapshot")
    return {
        "status": write_status,
        "record_id": record_id,
        "platform_account_id": profile_subject_id,
        "public_handle": identity["public_handle"],
        **published,
    }


def cutover_creator_registry_sqlite(
    data_root: DataLakeRoot, *, dry_run: bool = False
) -> dict[str, Any]:
    """Import the verified v3 current view into SQLite and atomically switch readers."""
    pointer = _load_registry_pointer(data_root)
    pointer_version = pointer.get("pointer_schema_version")
    if pointer_version == SQLITE_POINTER_SCHEMA_VERSION:
        index, public = _load_sqlite_current(data_root, pointer)
        return {
            "status": "dry_run_passed" if dry_run else "already_current",
            "database_ref": pointer.get("database_ref"),
            "database_schema_version": pointer.get("database_schema_version"),
            "platform_accounts_total": index["creator_registry_index"]["counts"][
                "platform_accounts_total"
            ],
            "public_profiles_total": len(public["creator_profile_public"]["profiles"]),
            "would_write_database": False,
            "would_update_pointer": False,
        }
    if pointer_version != CURRENT_POINTER_SCHEMA_VERSION:
        raise CreatorRegistryLakeError(
            "Creator Registry must have a verified v3 CURRENT generation before SQLite cutover"
        )
    index, public, manifest = _load_current_generation(data_root)
    try:
        result = bootstrap_sqlite_database(
            data_root=data_root,
            internal_document=index,
            public_document=public,
            authority_refs=manifest["authority_refs"],
            authority_inventory_sha256=manifest["authority_inventory_sha256"],
            dry_run=dry_run,
        )
    except CreatorRegistrySqliteError as exc:
        raise CreatorRegistryLakeError(str(exc)) from exc
    sql_pointer = canonical_record_bytes(
        {
            "pointer_schema_version": SQLITE_POINTER_SCHEMA_VERSION,
            "backend": "sqlite",
            "database_ref": sqlite_database_ref(),
            "database_schema_version": SQLITE_SCHEMA,
            "migration_authority_inventory_sha256": manifest[
                "authority_inventory_sha256"
            ],
        }
    )
    pointer_path = _registry_root(data_root) / CURRENT_FILENAME
    if dry_run:
        return {
            "status": "dry_run_passed",
            **result,
            "would_update_pointer": pointer_path.read_bytes() != sql_pointer,
        }
    data_root._require_writable("switch Creator Registry CURRENT to SQLite")
    _atomic_replace(pointer_path, sql_pointer)
    loaded_index = load_current_creator_registry(data_root)
    loaded_public = load_current_creator_profiles(data_root)
    if (
        loaded_index["creator_registry_index"]["platform_accounts"]
        != index["creator_registry_index"]["platform_accounts"]
        or loaded_public["creator_profile_public"]["profiles"]
        != public["creator_profile_public"]["profiles"]
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry SQLite cutover readback differs from verified v3 current state"
        )
    return {
        "status": "cutover",
        **result,
        "would_update_pointer": True,
    }


def publish_creator_registry_generation(
    data_root: DataLakeRoot, *, dry_run: bool = False
) -> dict[str, Any]:
    pointer = _load_registry_pointer(data_root, allow_missing=True)
    if pointer.get("pointer_schema_version") == SQLITE_POINTER_SCHEMA_VERSION:
        raise CreatorRegistryLakeError(
            "Creator Registry uses SQLite current authority; routine rebuild is disabled"
        )
    records = _load_authority_records(data_root)
    authority_digest = records["authority_inventory_sha256"]
    generated_at = _generation_time(records)
    index = _build_internal_index(records, generated_at=generated_at)
    public = _build_public_profiles(records, generated_at=generated_at)
    index_bytes = canonical_record_bytes(index)
    public_bytes = canonical_record_bytes(public)
    file_hashes = {
        f"query_tables/{INDEX_FILENAME}": _sha256(index_bytes),
        f"profiles/{PROFILE_FILENAME}": _sha256(public_bytes),
    }
    generation_identity = {
        "schema_version": GENERATION_MANIFEST_SCHEMA_VERSION,
        "authority_inventory_sha256": authority_digest,
        "files": file_hashes,
    }
    generation_id = "crg_" + _sha256(
        canonical_record_bytes(generation_identity)
    )[:24]
    manifest = {
        "schema_version": GENERATION_MANIFEST_SCHEMA_VERSION,
        "generation_id": generation_id,
        "generated_at": generated_at,
        "authority_inventory_sha256": authority_digest,
        "authority_record_count": len(records["authority_refs"]),
        "authority_refs": records["authority_refs"],
        "files": file_hashes,
    }
    manifest_bytes = canonical_record_bytes(manifest)
    files = {
        f"query_tables/{INDEX_FILENAME}": index_bytes,
        f"profiles/{PROFILE_FILENAME}": public_bytes,
        f"manifests/{MANIFEST_FILENAME}": manifest_bytes,
    }
    root = _registry_root(data_root)
    generations = root / GENERATIONS_DIRNAME
    target = generations / generation_id
    target_exists = target.exists()
    if target.exists():
        for relative, expected in files.items():
            path = target / relative
            if not path.is_file() or path.read_bytes() != expected:
                raise CreatorRegistryLakeError(
                    f"creator registry generation collision with different bytes: {generation_id}"
                )
    pointer = canonical_record_bytes(
        {
            "pointer_schema_version": CURRENT_POINTER_SCHEMA_VERSION,
            "generation_id": generation_id,
        }
    )
    pointer_path = root / CURRENT_FILENAME
    pointer_is_current = pointer_path.is_file() and pointer_path.read_bytes() == pointer
    result = {
        "generation_id": generation_id,
        "generation_root": str(target),
        "authority_record_count": len(records["authority_refs"]),
        "platform_accounts_total": index["creator_registry_index"]["counts"][
            "platform_accounts_total"
        ],
        "public_profiles_total": len(public["creator_profile_public"]["profiles"]),
    }
    if dry_run:
        return {
            **result,
            "would_write_generation": not target_exists,
            "would_update_pointer": not pointer_is_current,
        }

    data_root._require_writable("publish Creator Registry generation")
    generations.mkdir(parents=True, exist_ok=True)
    if not target_exists:
        staging = generations / f".building-{generation_id}-{uuid.uuid4().hex}"
        try:
            for relative, body in files.items():
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            os.rename(staging, target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    _atomic_replace(pointer_path, pointer)
    return result


def load_current_creator_registry(data_root: DataLakeRoot) -> dict[str, Any]:
    pointer = _load_registry_pointer(data_root)
    if pointer.get("pointer_schema_version") == SQLITE_POINTER_SCHEMA_VERSION:
        index, _public = _load_sqlite_current(data_root, pointer)
        return index
    index, _public, _manifest = _load_current_generation(data_root)
    return index


def load_current_creator_profiles(data_root: DataLakeRoot) -> dict[str, Any]:
    pointer = _load_registry_pointer(data_root)
    if pointer.get("pointer_schema_version") == SQLITE_POINTER_SCHEMA_VERSION:
        _index, public = _load_sqlite_current(data_root, pointer)
        return public
    _index, public, _manifest = _load_current_generation(data_root)
    return public


def load_current_registry_preflight_view(data_root: DataLakeRoot) -> dict[str, Any]:
    """Return the existing matcher shape while keeping onboarding internal."""
    index = load_current_creator_registry(data_root)["creator_registry_index"]
    profiles = []
    for row in index["platform_accounts"]:
        account = {
            key: deepcopy(row.get(key))
            for key in (
                "platform_account_id",
                "platform",
                "platform_public_account_id_or_none",
                "public_handle",
                "public_profile_url",
                "public_display_name_or_none",
            )
        }
        profiles.append(
            {
                "profile_subject_kind": "platform_account",
                "profile_subject_id": row["platform_account_id"],
                "platform_account_id_or_none": row["platform_account_id"],
                "platform_accounts": [account],
                "onboarding": deepcopy(row["onboarding"]),
            }
        )
    return {
        "creator_profile_current_view": {
            "schema_version": "creator_profile_current_view_registry_preflight_v1",
            "generated_at_utc": index["generated_at_utc"],
            "profiles": profiles,
        }
    }


def monitoring_eligible_accounts(data_root: DataLakeRoot, *, platform: str | None = None) -> list[dict[str, Any]]:
    rows = load_current_creator_registry(data_root)["creator_registry_index"]["platform_accounts"]
    return [
        deepcopy(row)
        for row in rows
        if row.get("monitoring_eligibility", {}).get("eligible") is True
        and (platform is None or row.get("platform") == platform)
    ]


def _load_current_generation(
    data_root: DataLakeRoot,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    data_root._reverify()
    root = _registry_root(data_root)
    pointer = root / CURRENT_FILENAME
    if not pointer.is_file():
        raise CreatorRegistryLakeError("Creator Registry has not been migrated into the data lake")
    try:
        pointer_doc = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CreatorRegistryLakeError(f"Creator Registry CURRENT pointer is unreadable: {exc}") from exc
    if pointer_doc.get("pointer_schema_version") != CURRENT_POINTER_SCHEMA_VERSION:
        raise CreatorRegistryLakeError("Creator Registry CURRENT pointer schema is unsupported")
    generation_id = _text(pointer_doc.get("generation_id"), "Creator Registry generation id")
    generation = root / GENERATIONS_DIRNAME / generation_id
    manifest_path = generation / "manifests" / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise CreatorRegistryLakeError("Creator Registry CURRENT generation is incomplete")
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != GENERATION_MANIFEST_SCHEMA_VERSION:
        raise CreatorRegistryLakeError("Creator Registry generation manifest schema is unsupported")
    if manifest.get("generation_id") != generation_id:
        raise CreatorRegistryLakeError("Creator Registry manifest generation does not match CURRENT")
    paths = {
        f"query_tables/{INDEX_FILENAME}": generation / "query_tables" / INDEX_FILENAME,
        f"profiles/{PROFILE_FILENAME}": generation / "profiles" / PROFILE_FILENAME,
    }
    for relative, path in paths.items():
        if not path.is_file() or _sha256(path.read_bytes()) != manifest.get("files", {}).get(relative):
            raise CreatorRegistryLakeError(f"Creator Registry generation file failed hash validation: {relative}")
    records = _load_authority_records(data_root)
    if manifest.get("authority_inventory_sha256") != records["authority_inventory_sha256"]:
        raise CreatorRegistryLakeError(
            "Creator Registry generated view is stale relative to append-only authority; rebuild it"
        )
    return _load_json(paths[f"query_tables/{INDEX_FILENAME}"]), _load_json(
        paths[f"profiles/{PROFILE_FILENAME}"]
    ), manifest


def _load_authority_records(
    data_root: DataLakeRoot, *, allow_missing_baseline: bool = False
) -> dict[str, Any]:
    data_root._reverify()
    records: list[tuple[str, bytes, dict[str, Any]]] = []
    for lane in (
        BASELINE_LANE,
        CANDIDATE_ADMISSION_LANE,
        CANDIDATE_RETRACTION_LANE,
        ADMISSION_LANE,
    ):
        for path in sorted((data_root.path / "derived").glob(f"*/*/{lane}/*")):
            if not path.is_file():
                continue
            body = path.read_bytes()
            try:
                record = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CreatorRegistryLakeError(f"unreadable Creator Registry authority record: {path}") from exc
            if not isinstance(record, dict):
                raise CreatorRegistryLakeError(f"Creator Registry authority record is not an object: {path}")
            expected_schema = {
                BASELINE_LANE: BASELINE_SCHEMA_VERSION,
                CANDIDATE_ADMISSION_LANE: CANDIDATE_ADMISSION_SCHEMA_VERSION,
                CANDIDATE_RETRACTION_LANE: CANDIDATE_RETRACTION_SCHEMA_VERSION,
                ADMISSION_LANE: ADMISSION_SCHEMA_VERSION,
            }[lane]
            if record.get("schema_version") != expected_schema or record.get("record_id") != path.name:
                raise CreatorRegistryLakeError(f"Creator Registry authority record identity mismatch: {path}")
            records.append((_relative_to_root(data_root, path), body, record))
    baselines = [record for ref, body, record in records if record["schema_version"] == BASELINE_SCHEMA_VERSION]
    candidate_admissions = [
        record
        for ref, body, record in records
        if record["schema_version"] == CANDIDATE_ADMISSION_SCHEMA_VERSION
    ]
    candidate_retractions = [
        record
        for ref, body, record in records
        if record["schema_version"] == CANDIDATE_RETRACTION_SCHEMA_VERSION
    ]
    admissions = [record for ref, body, record in records if record["schema_version"] == ADMISSION_SCHEMA_VERSION]
    if len(baselines) > 1:
        raise CreatorRegistryLakeError("multiple Creator Registry baselines are not allowed")
    if not baselines and not allow_missing_baseline:
        raise CreatorRegistryLakeError("Creator Registry has not been migrated into the data lake")
    if baselines:
        _verify_baseline(data_root, baselines[0])
    for candidate in candidate_admissions:
        _verify_candidate_admission(data_root, candidate)
    for retraction in candidate_retractions:
        _verify_candidate_retraction(data_root, retraction)
    for admission in admissions:
        _verify_admission(data_root, admission)
    if baselines:
        _validate_authority_admission_set(baselines[0], candidate_admissions, admissions)
        _validate_candidate_retraction_set(
            baselines[0], candidate_admissions, candidate_retractions, admissions
        )
    authority_refs = [
        {"record_ref": ref, "sha256": _sha256(body)} for ref, body, _record in sorted(records)
    ]
    return {
        "baselines": baselines,
        "candidate_admissions": sorted(
            candidate_admissions, key=lambda row: row["record_id"]
        ),
        "candidate_retractions": sorted(
            candidate_retractions, key=lambda row: row["record_id"]
        ),
        "active_candidate_admissions": sorted(
            [
                row
                for row in candidate_admissions
                if row["record_id"]
                not in {
                    retraction["candidate_admission"]["record_id"]
                    for retraction in candidate_retractions
                }
            ],
            key=lambda row: row["record_id"],
        ),
        "admissions": sorted(admissions, key=lambda row: row["record_id"]),
        "authority_refs": authority_refs,
        "authority_inventory_sha256": _sha256(canonical_record_bytes(authority_refs)),
    }


def _candidate_index_row(candidate: Mapping[str, Any]) -> dict[str, Any]:
    account = candidate["platform_account"]
    row = {
        "platform_account_id": account["platform_account_id"],
        "creator_record_id_or_none": None,
        "identity_state": "single_platform_observed",
        "linkage_state": "single_platform_observed",
        "discovery_state": "known_account",
        "capture_state": "identity_observed_grid_packet_available",
        "routing_decision": "onboard_only_after_explicit_full_onboarding",
        "source_pointers": [
            candidate["frontier_disposition"]["record_ref"],
            account["handle_source_pointer"],
        ],
        "non_claims": [
            "not onboarded",
            "not monitoring eligible",
            "not public profile admission",
            "not final cross-platform identity",
            "not contact or outreach authorization",
        ],
        "platform": account["platform"],
        "platform_public_account_id_or_none": account[
            "platform_public_account_id_or_none"
        ],
        "public_handle": account["public_handle"],
        "normalized_public_handle": _normalize_handle(account["public_handle"]),
        "public_profile_url": account["public_profile_url"],
        "public_display_name_or_none": account["public_display_name_or_none"],
        "onboarding": deepcopy(candidate["onboarding"]),
        "monitoring_eligibility": {
            "eligible": False,
            "reason": "not_onboarded",
            "scheduled": False,
        },
        "freshness": {
            "identity_observed_at": account["handle_observed_at"],
            "last_capture_observed_at_or_none": account["handle_observed_at"],
        },
    }
    row["lookup_keys"] = _lookup_keys(account)
    return row


def _validated_index_row(
    current_row: Mapping[str, Any], admission: Mapping[str, Any]
) -> dict[str, Any]:
    row = deepcopy(dict(current_row))
    account = admission["platform_account"]
    row.update(
        {
            "capture_state": "identity_observed_content_packet_available",
            "routing_decision": "dedupe_exact_platform_account_then_attach_new_discovery_evidence",
            "source_pointers": [admission["judgment"]["record_ref"]],
            "non_claims": [
                "not current handle guarantee",
                "not final cross-platform identity",
                "not metric authority",
                "not audience authority",
                "not contact or outreach authorization",
            ],
            "platform": account["platform"],
            "platform_public_account_id_or_none": account[
                "platform_public_account_id_or_none"
            ],
            "public_handle": account["public_handle"],
            "normalized_public_handle": _normalize_handle(account["public_handle"]),
            "public_profile_url": account["public_profile_url"],
            "public_display_name_or_none": account["public_display_name_or_none"],
            "onboarding": deepcopy(admission["onboarding"]),
            "monitoring_eligibility": {
                "eligible": True,
                "reason": "validated_onboarding_admission",
                "scheduled": False,
            },
            "freshness": {
                **deepcopy(row.get("freshness") or {}),
                "identity_observed_at": account["handle_observed_at"],
                "last_capture_observed_at_or_none": admission["onboarding"][
                    "onboarded_at_or_none"
                ],
            },
        }
    )
    row["lookup_keys"] = _lookup_keys(account)
    return row


def _new_public_profile(
    admission: Mapping[str, Any], *, generated_at: str
) -> dict[str, Any]:
    account = deepcopy(admission["platform_account"])
    profile = {
        "profile_subject_kind": "platform_account",
        "profile_subject_id": account["platform_account_id"],
        "platform_account_id_or_none": account["platform_account_id"],
        "creator_record_id_or_none": None,
        "identity_state": "single_platform_observed",
        "link_state_or_none": None,
        "review_state_or_none": None,
        "platform_accounts": [account],
        "current_metric_rollups": [],
        "audience_triangulation": deepcopy(admission["snapshot"]),
        "wind_calling_summary": None,
        "freshness": {
            "identity_updated_at": account["handle_observed_at"],
            "audience_computed_at_or_none": admission["snapshot"].get("generated_at"),
            "profile_view_computed_at": generated_at,
            "metrics_computed_at_or_none": None,
        },
        "limitations": [
            (
                f"Profile is account-scoped to one {account['platform'].title()} platform "
                "account; it is not a linked creator record."
            ),
            "No creator metric rollup is joined yet; do not infer channel-wide influence or engagement.",
            "Audience triangulation covers the admitted evidence window only.",
        ],
        "non_claims": [
            "not channel-wide creator influence",
            "not platform-wide engagement rate",
            "not buyer proof",
            "not public person-level identity",
            "not contact or outreach authorization",
            "not cross-platform rollup",
        ],
    }
    public = _public_profile(profile)
    _assert_client_safe(public)
    return public


def _build_internal_index(records: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    baseline = records["baselines"][0]
    document = deepcopy(baseline["registry_index"])
    _object(document.get("creator_registry_index"), "legacy Creator Registry index")
    wrapper = document["creator_registry_index"]
    rows = [deepcopy(_object(row, "Creator Registry row")) for row in wrapper.get("platform_accounts", [])]
    by_id = {row["platform_account_id"]: row for row in rows}
    candidate_created_ids: set[str] = set()
    for candidate in records["active_candidate_admissions"]:
        account = candidate["platform_account"]
        account_id = account["platform_account_id"]
        row = by_id.get(account_id)
        if row is None:
            row = {
                "platform_account_id": account_id,
                "creator_record_id_or_none": None,
                "identity_state": "single_platform_observed",
                "linkage_state": "single_platform_observed",
                "discovery_state": "known_account",
                "capture_state": "identity_observed_grid_packet_available",
                "routing_decision": "onboard_only_after_explicit_full_onboarding",
                "source_pointers": [
                    candidate["frontier_disposition"]["record_ref"],
                    account["handle_source_pointer"],
                ],
                "non_claims": [
                    "not onboarded",
                    "not monitoring eligible",
                    "not public profile admission",
                    "not final cross-platform identity",
                    "not contact or outreach authorization",
                ],
            }
            rows.append(row)
            by_id[account_id] = row
            candidate_created_ids.add(account_id)
        row.update(
            {
                "platform": account["platform"],
                "platform_public_account_id_or_none": account[
                    "platform_public_account_id_or_none"
                ],
                "public_handle": account["public_handle"],
                "normalized_public_handle": _normalize_handle(account["public_handle"]),
                "public_profile_url": account["public_profile_url"],
                "public_display_name_or_none": account["public_display_name_or_none"],
                "onboarding": deepcopy(candidate["onboarding"]),
                "monitoring_eligibility": {
                    "eligible": False,
                    "reason": "not_onboarded",
                    "scheduled": False,
                },
                "freshness": {
                    **deepcopy(row.get("freshness") or {}),
                    "identity_observed_at": account["handle_observed_at"],
                    "last_capture_observed_at_or_none": account["handle_observed_at"],
                },
            }
        )
        row["lookup_keys"] = _lookup_keys(account)
    for admission in records["admissions"]:
        account = admission["platform_account"]
        account_id = account["platform_account_id"]
        row = by_id.get(account_id)
        validated_row_state = {
            "capture_state": "identity_observed_content_packet_available",
            "routing_decision": "dedupe_exact_platform_account_then_attach_new_discovery_evidence",
            "source_pointers": [admission["judgment"]["record_ref"]],
            "non_claims": [
                "not current handle guarantee",
                "not final cross-platform identity",
                "not metric authority",
                "not audience authority",
                "not contact or outreach authorization",
            ],
        }
        if row is None:
            row = {
                "platform_account_id": account_id,
                "creator_record_id_or_none": None,
                "identity_state": "single_platform_observed",
                "linkage_state": "single_platform_observed",
                "discovery_state": "known_account",
                **deepcopy(validated_row_state),
            }
            rows.append(row)
            by_id[account_id] = row
        elif account_id in candidate_created_ids:
            # A validated admission upgrades the candidate row it follows; the
            # candidate-only routing state and non-claims must not survive it.
            row.update(deepcopy(validated_row_state))
        row.update(
            {
                "platform": account["platform"],
                "platform_public_account_id_or_none": account["platform_public_account_id_or_none"],
                "public_handle": account["public_handle"],
                "normalized_public_handle": _normalize_handle(account["public_handle"]),
                "public_profile_url": account["public_profile_url"],
                "public_display_name_or_none": account["public_display_name_or_none"],
                "onboarding": deepcopy(admission["onboarding"]),
                "monitoring_eligibility": {
                    "eligible": True,
                    "reason": "validated_onboarding_admission",
                    "scheduled": False,
                },
                "freshness": {
                    **deepcopy(row.get("freshness") or {}),
                    "identity_observed_at": account["handle_observed_at"],
                    "last_capture_observed_at_or_none": admission["onboarding"]["onboarded_at_or_none"],
                },
            }
        )
        row["lookup_keys"] = _lookup_keys(account)
    for row in rows:
        if "monitoring_eligibility" not in row:
            eligible = row.get("onboarding", {}).get("onboarding_state") == "onboarded"
            row["monitoring_eligibility"] = {
                "eligible": eligible,
                "reason": "migrated_onboarding_state" if eligible else "not_onboarded",
                "scheduled": False,
            }
    rows.sort(key=lambda row: (str(row.get("platform")), str(row.get("platform_account_id"))))
    wrapper.update(
        {
            "schema_version": INDEX_SCHEMA_VERSION,
            "index_id": "creator_registry_index_v1",
            "index_mode": "lake_authority_generated_current_view",
            "generated_at_utc": generated_at,
            "platform_accounts": rows,
            "source_inputs": deepcopy(records["authority_refs"]),
            "source_policy_posture": (
                "Generated from one immutable legacy baseline plus append-only candidate admissions, candidate retractions, and validated account admissions; "
                "the generation is a rebuildable current view, not authority."
            ),
            "accepted_residuals": [
                "Onboarding makes an account eligible for monitoring; it does not schedule monitoring.",
                "Instagram and YouTube admission writers remain deferred; their migrated state stays readable.",
            ],
        }
    )
    wrapper["counts"] = _index_counts(rows, wrapper.get("creator_records", []))
    return document


def _build_public_profiles(records: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    baseline = records["baselines"][0]
    legacy_wrapper = _object(
        baseline["profile_current"].get("creator_profile_current_view"), "legacy creator profile view"
    )
    legacy_profiles = [deepcopy(_object(row, "legacy creator profile")) for row in legacy_wrapper["profiles"]]
    by_id = {row["profile_subject_id"]: row for row in legacy_profiles}
    for admission in records["admissions"]:
        account = deepcopy(admission["platform_account"])
        account_id = account["platform_account_id"]
        profile = by_id.get(account_id)
        if profile is None:
            profile = {
                "profile_subject_kind": "platform_account",
                "profile_subject_id": account_id,
                "platform_account_id_or_none": account_id,
                "creator_record_id_or_none": None,
                "identity_state": "single_platform_observed",
                "link_state_or_none": None,
                "review_state_or_none": None,
                "platform_accounts": [account],
                "current_metric_rollups": [],
                "wind_calling_summary": None,
                "limitations": [
                    (
                        f"Profile is account-scoped to one {account['platform'].title()} platform "
                        "account; it is not a linked creator record."
                    ),
                    "No creator metric rollup is joined yet; do not infer channel-wide influence or engagement.",
                    "Audience triangulation covers the admitted evidence window only.",
                ],
                "non_claims": [
                    "not channel-wide creator influence",
                    "not platform-wide engagement rate",
                    "not buyer proof",
                    "not public person-level identity",
                    "not contact or outreach authorization",
                    "not cross-platform rollup",
                ],
            }
            legacy_profiles.append(profile)
            by_id[account_id] = profile
        profile["platform_accounts"] = [account]
        profile["audience_triangulation"] = deepcopy(admission["snapshot"])
        freshness = deepcopy(profile.get("freshness") or {})
        freshness.update(
            {
                "identity_updated_at": account["handle_observed_at"],
                "audience_computed_at_or_none": admission["snapshot"].get("generated_at"),
                "profile_view_computed_at": generated_at,
            }
        )
        freshness.setdefault("metrics_computed_at_or_none", None)
        profile["freshness"] = freshness
    public_profiles = [_public_profile(row) for row in legacy_profiles]
    public_profiles.sort(key=lambda row: str(row["profile_subject_id"]))
    document = {
        "creator_profile_public": {
            "schema_version": PUBLIC_PROFILE_SCHEMA_VERSION,
            "view_id": "creator_profile_public_v1",
            "generated_at_utc": generated_at,
            "profiles": public_profiles,
            "counts": {
                "profiles_total": len(public_profiles),
                "profiles_with_audience_triangulation": sum(
                    1 for row in public_profiles if row.get("audience_triangulation") is not None
                ),
                "profiles_with_metric_rollups": sum(
                    1 for row in public_profiles if row.get("current_metric_rollups")
                ),
            },
            "limitations": [
                "This is a generated current projection over captured public evidence, not a complete creator census.",
                "Monitoring eligibility and scheduling are internal and intentionally absent from this projection.",
            ],
            "non_claims": [
                "not contact or outreach authorization",
                "not legal-name identity proof",
                "not guaranteed campaign performance",
            ],
        }
    }
    _assert_client_safe(document)
    return document


def _public_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    accounts = []
    for raw_account in profile.get("platform_accounts", []):
        account = _object(raw_account, "profile platform account")
        accounts.append(
            {
                key: deepcopy(account.get(key))
                for key in (
                    "platform_account_id",
                    "platform",
                    "platform_public_account_id_or_none",
                    "public_handle",
                    "public_profile_url",
                    "public_display_name_or_none",
                )
            }
        )
    return {
        key: deepcopy(profile.get(key))
        for key in (
            "profile_subject_kind",
            "profile_subject_id",
            "platform_account_id_or_none",
            "creator_record_id_or_none",
            "identity_state",
            "link_state_or_none",
            "review_state_or_none",
            "current_metric_rollups",
            "audience_triangulation",
            "wind_calling_summary",
            "freshness",
            "limitations",
            "non_claims",
        )
    } | {"platform_accounts": accounts}


def _validate_admission_conflicts(data_root: DataLakeRoot, candidate: Mapping[str, Any]) -> None:
    records = _load_authority_records(data_root)
    _validate_authority_admission_set(
        records["baselines"][0],
        records["candidate_admissions"],
        [*records["admissions"], candidate],
    )


def _verify_baseline(data_root: DataLakeRoot, baseline: Mapping[str, Any]) -> None:
    packet = data_root.load_raw_packet(_text(baseline.get("raw_anchor"), "baseline raw anchor"))
    if packet.manifest.get("source_surface") != LEGACY_BASELINE_SURFACE:
        raise CreatorRegistryLakeError("Creator Registry baseline anchor has the wrong source surface")
    hashes = baseline.get("source_hashes")
    if not isinstance(hashes, Mapping):
        raise CreatorRegistryLakeError("Creator Registry baseline source hashes are missing")
    for role in ("account_ledger", "registry_index", "profile_current"):
        if _sha256(canonical_record_bytes(baseline[role])) != hashes.get(role):
            # Repository files are pretty JSON but may not be canonical-key ordered.
            members = baseline.get("source_packet_members", {})
            member_name = members.get(role) if isinstance(members, Mapping) else None
            preserved = [
                row
                for row in packet.manifest.get("preserved_files", [])
                if isinstance(row, Mapping)
                and str(row.get("relative_packet_path", "")).replace("\\", "/").endswith(str(member_name))
            ]
            if len(preserved) != 1 or preserved[0].get("sha256") != hashes.get(role):
                raise CreatorRegistryLakeError(f"Creator Registry baseline hash mismatch for {role}")


def _verify_candidate_admission(
    data_root: DataLakeRoot, candidate: Mapping[str, Any]
) -> None:
    if set(candidate) != {
        "record_id",
        "schema_version",
        "raw_anchor",
        "admitted_at",
        "platform_account",
        "onboarding",
        "frontier_disposition",
        "monitoring_eligible",
    }:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate admission fields do not match v1"
        )
    identity_payload = {key: value for key, value in candidate.items() if key != "record_id"}
    expected_record_id = "crc_" + _sha256(canonical_record_bytes(identity_payload))[:24]
    if candidate.get("record_id") != expected_record_id:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate admission content id mismatch"
        )
    if candidate.get("monitoring_eligible") is not False:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate admission must not be monitoring eligible"
        )
    account = _object(candidate.get("platform_account"), "candidate platform account")
    platform = str(account.get("platform") or "").casefold()
    if platform not in {"tiktok", "youtube"} or not account.get("platform_public_account_id_or_none"):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate lacks a supported platform and stable native identity"
        )
    identity = _extract_packet_identity_for_platform(
        data_root=data_root,
        packet_id=_text(candidate.get("raw_anchor"), "candidate raw anchor"),
        platform=platform,
    )
    if candidate.get("admitted_at") != identity["observed_at"]:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate admitted_at differs from its grid packet"
        )
    expected_account = {
        "platform_account_id": deterministic_platform_account_id(
            platform, identity["platform_public_account_id"]
        ),
        "platform": platform,
        "platform_public_account_id_or_none": identity["platform_public_account_id"],
        "public_handle": identity["public_handle"],
        "public_profile_url": identity["public_profile_url"],
        "handle_source_pointer": identity["handle_source_pointer"],
        "handle_observed_at": identity["observed_at"],
        "public_display_name_or_none": identity["public_display_name"],
        "display_name_source_pointer_or_none": (
            identity["display_name_source_pointer"]
        ),
        "display_name_source_field_or_none": identity["display_name_source_field"],
    }
    if account != expected_account:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate identity differs from its grid packet"
        )
    onboarding = _object(candidate.get("onboarding"), "candidate onboarding")
    if onboarding != {
        "onboarding_state": "not_onboarded",
        "onboarded_at_or_none": None,
        "evidence_packet_id_or_none": candidate["raw_anchor"],
        "evidence_source_family_or_none": identity["evidence_source_family"],
        "evidence_source_surface_or_none": identity["evidence_source_surface"],
        "policy_version": "creator_registry_candidate_admission_v1",
    }:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate onboarding fields do not match v1"
        )
    disposition = _object(
        candidate.get("frontier_disposition"), "candidate Frontier disposition"
    )
    path = data_root.path.joinpath(
        *_text(disposition.get("record_ref"), "Frontier record ref").split("/")
    )
    if not path.is_file() or _sha256(path.read_bytes()) != disposition.get(
        "record_sha256"
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate Frontier disposition is missing or changed"
        )
    frontier = load_creator_frontier_dispositions(data_root)[
        "creator_frontier_disposition_current"
    ]
    history = [
        row
        for row in frontier["history"]
        if row.get("disposition_id") == disposition.get("disposition_id")
    ]
    if set(disposition) != {
        "disposition_id",
        "candidate_key",
        "record_ref",
        "record_sha256",
    } or (
        len(history) != 1
        or history[0].get("status") != "eligible"
        or history[0].get("candidate_key") != disposition.get("candidate_key")
        or disposition.get("candidate_key")
        != f"{platform}:@{identity['public_handle']}"
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate does not cite one eligible Frontier disposition"
        )


def _verify_candidate_retraction(
    data_root: DataLakeRoot, retraction: Mapping[str, Any]
) -> None:
    if set(retraction) != {
        "record_id",
        "schema_version",
        "raw_anchor",
        "retracted_at",
        "platform_account_id",
        "public_handle",
        "candidate_admission",
        "frontier_disposition",
    }:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction fields do not match v1"
        )
    payload = {key: value for key, value in retraction.items() if key != "record_id"}
    expected_record_id = "crr_" + _sha256(canonical_record_bytes(payload))[:24]
    if retraction.get("record_id") != expected_record_id:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction content id mismatch"
        )
    candidate_ref = _object(
        retraction.get("candidate_admission"), "retracted candidate admission"
    )
    if set(candidate_ref) != {"record_id", "record_ref", "record_sha256"}:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction has invalid admission reference"
        )
    candidate_path = data_root.path.joinpath(
        *_text(candidate_ref.get("record_ref"), "candidate admission record ref").split("/")
    )
    if (
        not candidate_path.is_file()
        or candidate_path.name != candidate_ref.get("record_id")
        or _sha256(candidate_path.read_bytes()) != candidate_ref.get("record_sha256")
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry retracted candidate admission is missing or changed"
        )
    candidate = _load_json(candidate_path)
    account = _object(candidate.get("platform_account"), "retracted candidate account")
    if (
        candidate.get("schema_version") != CANDIDATE_ADMISSION_SCHEMA_VERSION
        or candidate.get("raw_anchor") != retraction.get("raw_anchor")
        or account.get("platform_account_id") != retraction.get("platform_account_id")
        or _normalize_handle(account.get("public_handle"))
        != _normalize_handle(retraction.get("public_handle"))
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction does not bind its admission identity"
        )
    disposition_ref = _object(
        retraction.get("frontier_disposition"), "retraction Frontier disposition"
    )
    if set(disposition_ref) != {
        "disposition_id",
        "candidate_key",
        "record_ref",
        "record_sha256",
    }:
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction has invalid Frontier reference"
        )
    disposition_path = data_root.path.joinpath(
        *_text(disposition_ref.get("record_ref"), "Frontier record ref").split("/")
    )
    if (
        not disposition_path.is_file()
        or _sha256(disposition_path.read_bytes()) != disposition_ref.get("record_sha256")
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction Frontier record is missing or changed"
        )
    history = load_creator_frontier_dispositions(data_root)[
        "creator_frontier_disposition_current"
    ]["history"]
    matches = [
        row
        for row in history
        if row.get("disposition_id") == disposition_ref.get("disposition_id")
    ]
    if (
        len(matches) != 1
        or matches[0].get("status") not in {"deferred", "rejected"}
        or matches[0].get("candidate_key") != disposition_ref.get("candidate_key")
        or disposition_ref.get("candidate_key")
        != f"tiktok:@{_normalize_handle(retraction.get('public_handle'))}"
        or retraction.get("retracted_at") != matches[0].get("recorded_at")
    ):
        raise CreatorRegistryLakeError(
            "Creator Registry candidate retraction lacks one deferred or rejected Frontier disposition"
        )


def _verify_admission(data_root: DataLakeRoot, admission: Mapping[str, Any]) -> None:
    if set(admission) != {
        "record_id",
        "schema_version",
        "raw_anchor",
        "admitted_at",
        "platform_account",
        "onboarding",
        "judgment",
        "snapshot",
        "monitoring_eligible",
    }:
        raise CreatorRegistryLakeError(
            "Creator Registry validated admission fields do not match v1"
        )
    identity_payload = {key: value for key, value in admission.items() if key != "record_id"}
    expected_record_id = "cra_" + _sha256(canonical_record_bytes(identity_payload))[:24]
    if admission.get("record_id") != expected_record_id:
        raise CreatorRegistryLakeError(
            "Creator Registry validated admission content id mismatch"
        )
    if admission.get("monitoring_eligible") is not True:
        raise CreatorRegistryLakeError("Creator Registry admission must be monitoring eligible")
    account = _object(admission.get("platform_account"), "admission platform account")
    platform = str(account.get("platform") or "").casefold()
    if platform not in {"tiktok", "youtube"} or not account.get("platform_public_account_id_or_none"):
        raise CreatorRegistryLakeError(
            "Creator Registry admission lacks a supported platform and stable native identity"
        )
    identity = _extract_packet_identity_for_platform(
        data_root=data_root,
        packet_id=_text(admission.get("raw_anchor"), "admission raw anchor"),
        platform=platform,
    )
    expected_account = {
        "platform_account_id": account.get("platform_account_id"),
        "platform": platform,
        "platform_public_account_id_or_none": identity["platform_public_account_id"],
        "public_handle": identity["public_handle"],
        "public_profile_url": identity["public_profile_url"],
        "handle_source_pointer": identity["handle_source_pointer"],
        "handle_observed_at": identity["observed_at"],
        "public_display_name_or_none": identity["public_display_name"],
        "display_name_source_pointer_or_none": (
            identity["display_name_source_pointer"]
        ),
        "display_name_source_field_or_none": identity["display_name_source_field"],
    }
    if account != expected_account:
        raise CreatorRegistryLakeError(
            "Creator Registry validated admission identity differs from its grid packet"
        )
    judgment = _object(admission.get("judgment"), "admission Judgment")
    path = data_root.path.joinpath(*_text(judgment.get("record_ref"), "Judgment record ref").split("/"))
    if not path.is_file() or _sha256(path.read_bytes()) != judgment.get("record_sha256"):
        raise CreatorRegistryLakeError("Creator Registry admission Judgment record is missing or changed")
    outcome = _load_json(path)
    if outcome.get("status") != "validated" or outcome.get("record_id") != judgment.get("record_id"):
        raise CreatorRegistryLakeError("Creator Registry admission Judgment is not validated")
    if outcome.get("snapshot_or_none") != admission.get("snapshot"):
        raise CreatorRegistryLakeError("Creator Registry admission snapshot differs from Judgment authority")
    snapshot = _object(admission.get("snapshot"), "admission snapshot")
    account_id = account.get("platform_account_id")
    if (
        outcome.get("raw_anchor") != admission.get("raw_anchor")
        or snapshot.get("profile_subject_id") != account_id
        or snapshot.get("platform_account_id") != account_id
    ):
        raise CreatorRegistryLakeError("Creator Registry admission identity is not bound to Judgment authority")
    if snapshot.get("creator_id") != (
        f"{platform}:@{_normalize_handle(account.get('public_handle'))}"
    ):
        raise CreatorRegistryLakeError("Creator Registry admission handle is not bound to Judgment creator id")


def _extract_packet_identity_for_platform(
    *, data_root: DataLakeRoot, packet_id: str, platform: str
) -> dict[str, str]:
    if platform == "tiktok":
        return extract_tiktok_packet_identity(data_root, packet_id)
    if platform == "youtube":
        return extract_youtube_assessment_packet_identity(data_root, packet_id)
    raise CreatorRegistryLakeError(f"unsupported Creator Registry admission platform: {platform}")


def _validate_authority_admission_set(
    baseline: Mapping[str, Any],
    candidate_admissions: Sequence[Mapping[str, Any]],
    admissions: Sequence[Mapping[str, Any]],
) -> None:
    baseline_accounts = baseline["account_ledger"]["creator_public_handle_linkage_ledger"][
        "platform_accounts"
    ]
    by_id = {str(row["platform_account_id"]): row for row in baseline_accounts}
    native: dict[tuple[str, str], str] = {}
    handle: dict[tuple[str, str], str] = {}
    for raw in baseline_accounts:
        row = _object(raw, "baseline account")
        account_id = str(row["platform_account_id"])
        platform = str(row["platform"])
        native_id = row.get("platform_public_account_id_or_none")
        if native_id:
            native[(platform, str(native_id))] = account_id
        handle[(platform, _normalize_handle(row.get("public_handle")))] = account_id
    for role, authority_rows in (
        ("candidate admissions", candidate_admissions),
        ("validated admissions", admissions),
    ):
        admitted_ids: set[str] = set()
        for admission in authority_rows:
            account = _object(admission.get("platform_account"), f"{role} account")
            account_id = str(account["platform_account_id"])
            if account_id in admitted_ids:
                raise CreatorRegistryLakeError(
                    f"multiple {role} target the same platform account"
                )
            admitted_ids.add(account_id)
            platform = str(account["platform"])
            native_key = (platform, str(account["platform_public_account_id_or_none"]))
            handle_key = (platform, _normalize_handle(account["public_handle"]))
            native_owner = native.get(native_key)
            handle_owner = handle.get(handle_key)
            if native_owner not in {None, account_id} or handle_owner not in {None, account_id}:
                raise CreatorRegistryLakeError("admission identity conflicts with current authority")
            baseline_row = by_id.get(account_id)
            if baseline_row is not None:
                baseline_native = baseline_row.get("platform_public_account_id_or_none")
                same_handle = _normalize_handle(baseline_row.get("public_handle")) == handle_key[1]
                if baseline_native and str(baseline_native) != native_key[1]:
                    raise CreatorRegistryLakeError("admission native id conflicts with baseline account id")
                if not baseline_native and not same_handle:
                    raise CreatorRegistryLakeError("admission handle conflicts with handle-only baseline account")
            native[native_key] = account_id
            handle[handle_key] = account_id


def _validate_candidate_retraction_set(
    baseline: Mapping[str, Any],
    candidate_admissions: Sequence[Mapping[str, Any]],
    candidate_retractions: Sequence[Mapping[str, Any]],
    admissions: Sequence[Mapping[str, Any]],
) -> None:
    candidates = {row["record_id"]: row for row in candidate_admissions}
    if len(candidates) != len(candidate_admissions):
        raise CreatorRegistryLakeError("duplicate candidate admission record ids")
    baseline_ids = {
        str(row["platform_account_id"])
        for row in baseline["account_ledger"]["creator_public_handle_linkage_ledger"][
            "platform_accounts"
        ]
    }
    validated_ids = {
        str(row["platform_account"]["platform_account_id"]) for row in admissions
    }
    targeted: set[str] = set()
    for retraction in candidate_retractions:
        target_id = retraction["candidate_admission"]["record_id"]
        candidate = candidates.get(target_id)
        if candidate is None:
            raise CreatorRegistryLakeError(
                "candidate retraction targets a missing candidate admission"
            )
        if target_id in targeted:
            raise CreatorRegistryLakeError(
                "multiple retractions target the same candidate admission"
            )
        targeted.add(target_id)
        account_id = str(candidate["platform_account"]["platform_account_id"])
        if account_id in baseline_ids:
            raise CreatorRegistryLakeError(
                "candidate retraction cannot remove a baseline Registry account"
            )
        if account_id in validated_ids:
            raise CreatorRegistryLakeError(
                "candidate retraction cannot remove a validated Registry account"
            )


def _write_baseline_source_packet(
    *,
    data_root: DataLakeRoot,
    source_paths: Mapping[str, Path],
    source_hashes: Mapping[str, str],
    generated_at: str,
) -> str:
    names = {
        "account_ledger": "creator_public_handle_linkage_ledger_v0.json",
        "registry_index": "creator_registry_index_v0.json",
        "profile_current": "creator_profile_current_view_v0.json",
    }
    staged = [(names[role], source_paths[role].read_bytes()) for role in names]
    file_ids = staged_file_id_map(staged)
    timing = PacketTiming(
        source_publication_or_event=not_applicable("migration freezes current repository operational state"),
        source_edit_or_version=known_fact("source hashes: " + json.dumps(source_hashes, sort_keys=True)),
        capture_time=known_fact(generated_at),
        recapture_time=not_applicable("one baseline migration"),
        cutoff_posture=not_applicable("not a time-window source"),
    )
    access = known_fact("local repository files read for owner-authorized lake migration")
    archive = not_attempted("migration does not query an archive")
    media = not_applicable("JSON registry documents")
    relationship = not_applicable("one migration baseline")
    result = stage_and_write_packet(
        data_root=data_root,
        staged_artifacts=staged,
        source_slices=[
            SourceCaptureSlice(
                slice_id="creator_registry_baseline_01",
                locator=known_fact("forseti://creator-registry/legacy-baseline"),
                timing=timing,
                access_posture=access,
                archive_history_posture=archive,
                media_modality_posture=media,
                re_capture_relationship=relationship,
                limitations=["migration baseline; later account admissions are separate append-only records"],
                warning_notes=[],
                preserved_file_ids=[file_ids[name] for name in names.values()],
                metric_observations=[],
            )
        ],
        source_family="creator_registry",
        source_surface=LEGACY_BASELINE_SURFACE,
        source_locator=known_fact("forseti://creator-registry/legacy-baseline"),
        decision_question="What exact Creator Registry state is being migrated out of Git?",
        capture_context="Owner-authorized one-time migration of exact legacy registry documents.",
        actor_audience_context=not_applicable("registry migration, not audience capture"),
        capture_mode=CaptureModeCategory.AUTOMATED_EXTRACTION,
        operator_category="creator_registry_migration_cli_operator",
        session_identity=None,
        visible_mode_changes=["creator_registry_lake_authority_cutover_v1"],
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access,
        archive_history_posture=archive,
        media_modality_posture=media,
        re_capture_relationship=relationship,
        warnings=[],
        limitations=["one-time migration baseline"],
        receipt_summary="Creator Registry legacy baseline preserved for lake authority cutover.",
        receipt_non_claims=["not a new creator onboarding", "not client delivery"],
    )
    return Path(result.output_directory).name


def _validate_legacy_documents(documents: Mapping[str, Any]) -> None:
    ledger = _object(documents["account_ledger"].get("creator_public_handle_linkage_ledger"), "ledger")
    index = _object(documents["registry_index"].get("creator_registry_index"), "index")
    profile = _object(documents["profile_current"].get("creator_profile_current_view"), "profile")
    ledger_ids = [row.get("platform_account_id") for row in ledger.get("platform_accounts", [])]
    index_ids = [row.get("platform_account_id") for row in index.get("platform_accounts", [])]
    profile_ids = [row.get("profile_subject_id") for row in profile.get("profiles", [])]
    if len(ledger_ids) != len(set(ledger_ids)) or set(ledger_ids) != set(index_ids):
        raise CreatorRegistryLakeError("legacy ledger and registry index account sets do not match")
    if not set(ledger_ids).issubset(set(profile_ids)):
        raise CreatorRegistryLakeError("legacy profile view omits registry accounts")


def _baseline_parity(documents: Mapping[str, Any]) -> dict[str, Any]:
    index = documents["registry_index"]["creator_registry_index"]
    profile = documents["profile_current"]["creator_profile_current_view"]
    return {
        "platform_accounts_total": len(index["platform_accounts"]),
        "profiles_total": len(profile["profiles"]),
        "account_id_sets_equal": {
            row["platform_account_id"] for row in index["platform_accounts"]
        }
        == {row["profile_subject_id"] for row in profile["profiles"]},
    }


def _baseline_generated_at(documents: Mapping[str, Any]) -> str:
    values = [
        documents["registry_index"]["creator_registry_index"].get("generated_at_utc"),
        documents["profile_current"]["creator_profile_current_view"].get("generated_at_utc"),
    ]
    return max(_text(value, "baseline generated_at") for value in values)


def _generation_time(records: Mapping[str, Any]) -> str:
    values = [_text(records["baselines"][0].get("generated_at"), "baseline generated_at")]
    values.extend(
        _text(row.get("admitted_at"), "candidate admitted_at")
        for row in records["candidate_admissions"]
    )
    values.extend(
        _text(row.get("retracted_at"), "candidate retracted_at")
        for row in records["candidate_retractions"]
    )
    values.extend(_text(row.get("admitted_at"), "admission admitted_at") for row in records["admissions"])
    return max(values)


def _matching_index_rows(index: Mapping[str, Any], identity: Mapping[str, str]) -> list[dict[str, Any]]:
    wrapper = _object(index.get("creator_registry_index"), "Creator Registry index")
    matches = []
    for raw in wrapper.get("platform_accounts", []):
        row = _object(raw, "Creator Registry row")
        if row.get("platform") != identity["platform"]:
            continue
        native = row.get("platform_public_account_id_or_none")
        same_native = native is not None and str(native) == identity["platform_public_account_id"]
        same_handle = _normalize_handle(row.get("public_handle")) == identity["public_handle"]
        if same_native or same_handle:
            matches.append(row)
    return matches


def _lookup_keys(account: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            f"platform_account_id:{account['platform_account_id']}",
            f"platform:{account['platform']}:public_account_id:{account['platform_public_account_id_or_none']}",
            f"platform:{account['platform']}:handle:{_normalize_handle(account['public_handle'])}",
            f"platform:{account['platform']}:url:{str(account['public_profile_url']).casefold()}",
        }
    )


def _index_counts(rows: Sequence[Mapping[str, Any]], creator_records: Any) -> dict[str, Any]:
    platforms: dict[str, int] = {}
    onboarding: dict[str, int] = {}
    for row in rows:
        platform = str(row.get("platform"))
        state = str(row.get("onboarding", {}).get("onboarding_state"))
        platforms[platform] = platforms.get(platform, 0) + 1
        onboarding[state] = onboarding.get(state, 0) + 1
    return {
        "platform_accounts_total": len(rows),
        "creator_records_total": len(creator_records) if isinstance(creator_records, list) else 0,
        "known_account_rows_total": len(rows),
        "platform_accounts_by_platform": dict(sorted(platforms.items())),
        "platform_accounts_by_onboarding_state": dict(sorted(onboarding.items())),
        "monitoring_eligible_total": sum(
            1 for row in rows if row.get("monitoring_eligibility", {}).get("eligible") is True
        ),
    }


def _assert_client_safe(value: Any, path: str = "$") -> None:
    forbidden_keys = {
        "onboarding",
        "monitoring_eligibility",
        "routing_decision",
        "source_drill_back",
        "source_inputs",
        "response_bytes_b64",
        "preflight",
    }
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in forbidden_keys:
                raise CreatorRegistryLakeError(f"public profile contains internal field at {path}.{key}")
            _assert_client_safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_client_safe(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if _WINDOWS_ABSOLUTE.match(value) or value.startswith(("/Users/", "/home/")):
            raise CreatorRegistryLakeError(f"public profile contains a local absolute path at {path}")


def _registry_root(data_root: DataLakeRoot) -> Path:
    return data_root.path.joinpath(*REGISTRY_ROOT_PARTS)


def _load_registry_pointer(
    data_root: DataLakeRoot, *, allow_missing: bool = False
) -> dict[str, Any]:
    data_root._reverify()
    pointer = _registry_root(data_root) / CURRENT_FILENAME
    if not pointer.is_file():
        if allow_missing:
            return {}
        raise CreatorRegistryLakeError(
            "Creator Registry has not been migrated into the data lake"
        )
    try:
        value = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CreatorRegistryLakeError(
            f"Creator Registry CURRENT pointer is unreadable: {exc}"
        ) from exc
    return _object(value, "Creator Registry CURRENT pointer")


def _uses_sqlite_registry(data_root: DataLakeRoot) -> bool:
    pointer = _load_registry_pointer(data_root)
    version = pointer.get("pointer_schema_version")
    if version == SQLITE_POINTER_SCHEMA_VERSION:
        return True
    if version == CURRENT_POINTER_SCHEMA_VERSION:
        return False
    raise CreatorRegistryLakeError("Creator Registry CURRENT pointer schema is unsupported")


def _load_sqlite_current(
    data_root: DataLakeRoot, pointer: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = {
        "pointer_schema_version",
        "backend",
        "database_ref",
        "database_schema_version",
        "migration_authority_inventory_sha256",
    }
    if (
        set(pointer) != expected
        or pointer.get("pointer_schema_version") != SQLITE_POINTER_SCHEMA_VERSION
        or pointer.get("backend") != "sqlite"
        or pointer.get("database_ref") != sqlite_database_ref()
        or pointer.get("database_schema_version") != SQLITE_SCHEMA
    ):
        raise CreatorRegistryLakeError("Creator Registry SQLite CURRENT pointer is unsupported")
    try:
        index, public = load_sqlite_documents(
            data_root,
            expected_migration_authority_inventory_sha256=pointer[
                "migration_authority_inventory_sha256"
            ],
        )
    except CreatorRegistrySqliteError as exc:
        raise CreatorRegistryLakeError(str(exc)) from exc
    _assert_client_safe(public)
    return index, public


def _sqlite_registry_summary(
    index: Mapping[str, Any], public: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "database_ref": sqlite_database_ref(),
        "database_schema_version": SQLITE_SCHEMA,
        "platform_accounts_total": index["creator_registry_index"]["counts"][
            "platform_accounts_total"
        ],
        "public_profiles_total": len(public["creator_profile_public"]["profiles"]),
    }


def _require_current_retraction_epoch(data_root: DataLakeRoot) -> None:
    """Keep epoch adoption explicit while allowing stale-authority recovery."""
    data_root._reverify()
    pointer = _registry_root(data_root) / CURRENT_FILENAME
    if not pointer.is_file():
        raise CreatorRegistryLakeError(
            "Creator Registry has not been migrated into the data lake"
        )
    try:
        pointer_doc = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CreatorRegistryLakeError(
            f"Creator Registry CURRENT pointer is unreadable: {exc}"
        ) from exc
    if pointer_doc.get("pointer_schema_version") != CURRENT_POINTER_SCHEMA_VERSION:
        raise CreatorRegistryLakeError(
            "Creator Registry CURRENT pointer epoch must be upgraded with "
            "`run_creator_registry_lake.py rebuild --write` before candidate retraction"
        )


def _relative_to_root(data_root: DataLakeRoot, path: Path) -> str:
    return path.resolve().relative_to(data_root.path.resolve()).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(_object(value, str(path)))


def _object(value: Any, role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CreatorRegistryLakeError(f"{role} must be an object")
    return dict(value)


def _text(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CreatorRegistryLakeError(f"{role} must be nonblank text")
    return value.strip()


def _normalize_handle(value: Any) -> str:
    return _text(value, "public handle").lstrip("@").casefold()


__all__ = [
    "ADMISSION_LANE",
    "BASELINE_LANE",
    "CANDIDATE_ADMISSION_LANE",
    "CANDIDATE_RETRACTION_LANE",
    "CreatorRegistryLakeError",
    "admit_tiktok_creator_account",
    "admit_tiktok_creator_candidate",
    "admit_youtube_creator_account",
    "admit_youtube_creator_candidate",
    "cutover_creator_registry_sqlite",
    "deterministic_platform_account_id",
    "extract_tiktok_packet_identity",
    "extract_youtube_assessment_packet_identity",
    "load_current_creator_profiles",
    "load_current_creator_registry",
    "load_current_registry_preflight_view",
    "migrate_legacy_registry",
    "monitoring_eligible_accounts",
    "publish_creator_registry_generation",
    "retract_tiktok_creator_candidate",
    "resolve_tiktok_profile_subject_id",
    "resolve_youtube_profile_subject_id",
]
