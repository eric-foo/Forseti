"""Lake persistence for validated TikTok Creator Discovery Frontier registers.

Kept as a sibling of the pure builder so `register_writer` stays network- and
lake-free. The register is appended as a derived record keyed to the raw
parent-grid packet it was built from, per the data-lake derived-layout rule
(derived records are append-only and anchored to committed raw truth).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from data_lake.canonical_json import canonical_record_bytes
from data_lake.root import DataLakeRoot
from source_capture.models import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map

from capture_spine.tiktok_creator_discovery_frontier.models import (
    TikTokCreatorDiscoveryFrontierError,
)
from capture_spine.tiktok_creator_discovery_frontier.validation import (
    validate_tiktok_creator_discovery_frontier_register,
)

FRONTIER_REGISTER_DERIVED_LANE = "tiktok_creator_discovery_frontier"
FRONTIER_DISPOSITION_DERIVED_LANE = "creator_frontier_disposition"
FRONTIER_DISPOSITION_SCHEMA = "creator_frontier_disposition_batch_v1"
FRONTIER_DISPOSITION_CURRENT_SCHEMA = "creator_frontier_disposition_current_v1"
FRONTIER_DISPOSITION_SOURCE_SURFACE = "creator_frontier_owner_actions"
_DISPOSITION_STATUSES = {"eligible", "deferred", "rejected"}
_DISPOSITION_PRIORITIES = {"super", "high", "normal", "low"}
_DISPOSITION_REASONS = {
    "non_us_market",
    "us_market_unverified",
    "low_reach",
    "low_potential",
    "duplicate_or_backup",
    "profile_unavailable",
    "self_brand_only",
    "owner_choice",
    "other",
}


def load_tiktok_creator_discovery_frontier_registers(
    data_root: Any,
) -> list[dict[str, Any]]:
    """Load every validated, non-tombstoned Frontier register from the lake."""
    if not isinstance(data_root, DataLakeRoot):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_data_root",
            "lake read requires a resolved DataLakeRoot",
        )
    registers: list[dict[str, Any]] = []
    for raw_anchor in data_root.list_committed_packet_ids():
        lane_dir = data_root.lane_dir(
            subtree="derived",
            raw_anchor=raw_anchor,
            lane=FRONTIER_REGISTER_DERIVED_LANE,
        )
        if not lane_dir.is_dir():
            continue
        for record_path in sorted(lane_dir.glob("*.json"), key=lambda path: path.name):
            try:
                register = json.loads(record_path.read_text(encoding="utf-8"))
                validate_tiktok_creator_discovery_frontier_register(register)
            except (OSError, ValueError, TikTokCreatorDiscoveryFrontierError) as exc:
                raise TikTokCreatorDiscoveryFrontierError(
                    "invalid_lake_register",
                    f"invalid Frontier register {record_path}: {exc}",
                ) from exc
            wrapper = register["tiktok_creator_discovery_frontier_register"]
            if wrapper["provenance"].get("parent_grid_packet_id_or_none") != raw_anchor:
                raise TikTokCreatorDiscoveryFrontierError(
                    "frontier_anchor_mismatch",
                    f"Frontier register is stored under the wrong raw anchor: {record_path}",
                )
            registers.append(register)
    return registers


def write_tiktok_creator_discovery_frontier_register(
    register: Mapping[str, Any],
    data_root: Any,
    *,
    record_id: str,
) -> Path:
    """Append a validated frontier register to the lake and return its path.

    ``data_root`` is a resolved ``DataLakeRoot``; the raw anchor is the
    register's parent-grid packet id, so a register built without a committed
    parent-grid packet cannot be lake-written (fail-closed -- use an explicit
    local ``--output`` escape instead).
    """
    if not isinstance(data_root, DataLakeRoot):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_data_root",
            "lake write requires a resolved DataLakeRoot (construct via "
            "resolve()/initialize()/for_test()); arbitrary root objects bypass "
            "the verified write guard",
        )
    validate_tiktok_creator_discovery_frontier_register(register)
    wrapper = register["tiktok_creator_discovery_frontier_register"]
    raw_anchor = wrapper["provenance"].get("parent_grid_packet_id_or_none")
    if not raw_anchor:
        raise TikTokCreatorDiscoveryFrontierError(
            "missing_parent_grid_packet_anchor",
            "lake write requires provenance.parent_grid_packet_id_or_none; a "
            "register without a committed parent-grid packet has no raw anchor",
        )
    if data_root.find_packet(str(raw_anchor)) is None:
        raise TikTokCreatorDiscoveryFrontierError(
            "unknown_parent_grid_packet_anchor",
            f"parent-grid packet {raw_anchor!r} is not committed in this lake "
            "root; a derived register must anchor to committed raw truth",
        )
    body = json.dumps(register, indent=2, sort_keys=True) + "\n"
    return data_root.append_record(
        subtree="derived",
        raw_anchor=str(raw_anchor),
        lane=FRONTIER_REGISTER_DERIVED_LANE,
        record_id=record_id,
        data=body.encode("utf-8"),
    )


def load_creator_frontier_dispositions(data_root: Any) -> dict[str, Any]:
    """Fold append-only owner actions into one fail-closed current Frontier view."""
    if not isinstance(data_root, DataLakeRoot):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_data_root", "Frontier disposition read requires a resolved DataLakeRoot"
        )
    by_id: dict[str, dict[str, Any]] = {}
    for raw_anchor in data_root.list_committed_packet_ids():
        lane_dir = data_root.lane_dir(
            subtree="derived", raw_anchor=raw_anchor, lane=FRONTIER_DISPOSITION_DERIVED_LANE
        )
        if not lane_dir.is_dir():
            continue
        packet = data_root.load_raw_packet(raw_anchor)
        if (
            packet.manifest.get("source_family") != "creator_frontier"
            or packet.manifest.get("source_surface") != FRONTIER_DISPOSITION_SOURCE_SURFACE
        ):
            raise TikTokCreatorDiscoveryFrontierError(
                "frontier_disposition_anchor_mismatch",
                f"Frontier disposition record has the wrong source packet: {raw_anchor}",
            )
        for record_path in sorted(lane_dir.glob("*"), key=lambda path: path.name):
            if not record_path.is_file():
                continue
            body = record_path.read_bytes()
            try:
                batch = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise TikTokCreatorDiscoveryFrontierError(
                    "invalid_frontier_disposition",
                    f"unreadable Frontier disposition record {record_path}: {exc}",
                ) from exc
            if (
                not isinstance(batch, Mapping)
                or set(batch)
                != {"record_id", "schema_version", "raw_anchor", "recorded_at", "dispositions"}
                or batch.get("schema_version") != FRONTIER_DISPOSITION_SCHEMA
                or batch.get("record_id") != record_path.name
                or batch.get("raw_anchor") != raw_anchor
            ):
                raise TikTokCreatorDiscoveryFrontierError(
                    "invalid_frontier_disposition",
                    f"Frontier disposition record identity mismatch: {record_path}",
                )
            dispositions = batch.get("dispositions")
            recorded_at = _normalize_timestamp(batch.get("recorded_at"))
            payload = {key: value for key, value in batch.items() if key != "record_id"}
            expected_record_id = "cfdb_" + hashlib.sha256(
                canonical_record_bytes(payload)
            ).hexdigest()[:24]
            if (
                batch.get("record_id") != expected_record_id
                or not isinstance(dispositions, list)
                or not dispositions
                or _load_frontier_action_packet_actions(data_root, raw_anchor) != dispositions
            ):
                raise TikTokCreatorDiscoveryFrontierError(
                    "invalid_frontier_disposition",
                    f"Frontier disposition batch failed content validation: {record_path}",
                )
            for raw in dispositions:
                entry = _validate_disposition_entry(raw)
                if entry["recorded_at"] != recorded_at:
                    raise TikTokCreatorDiscoveryFrontierError(
                        "invalid_frontier_disposition",
                        f"Frontier disposition entry timestamp differs from its batch: {record_path}",
                    )
                disposition_id = entry["disposition_id"]
                existing = by_id.get(disposition_id)
                if existing is not None and existing != entry:
                    raise TikTokCreatorDiscoveryFrontierError(
                        "frontier_disposition_id_collision",
                        f"Frontier disposition id has different bytes: {disposition_id}",
                    )
                entry["authority_record_ref"] = record_path.relative_to(data_root.path).as_posix()
                entry["authority_record_sha256"] = hashlib.sha256(body).hexdigest()
                by_id[disposition_id] = entry

    for entry in by_id.values():
        for superseded in entry["supersedes_record_ids"]:
            prior = by_id.get(superseded)
            if (
                superseded == entry["disposition_id"]
                or prior is None
                or prior["candidate_key"] != entry["candidate_key"]
            ):
                raise TikTokCreatorDiscoveryFrontierError(
                    "invalid_frontier_supersession",
                    f"Frontier disposition {entry['disposition_id']} has an invalid supersession",
                )
    superseded_ids = {
        disposition_id for entry in by_id.values()
        for disposition_id in entry["supersedes_record_ids"]
    }
    heads: dict[str, list[dict[str, Any]]] = {}
    for disposition_id, entry in by_id.items():
        if disposition_id not in superseded_ids:
            heads.setdefault(entry["candidate_key"], []).append(entry)
    candidate_keys = {entry["candidate_key"] for entry in by_id.values()}
    conflicts = sorted(key for key in candidate_keys if len(heads.get(key, [])) != 1)
    if conflicts:
        raise TikTokCreatorDiscoveryFrontierError(
            "conflicting_frontier_dispositions",
            f"multiple unsuperseded Frontier dispositions: {conflicts}",
        )
    current = [rows[0] for key, rows in sorted(heads.items())]
    history = [by_id[key] for key in sorted(by_id)]
    return {
        "creator_frontier_disposition_current": {
            "schema_version": FRONTIER_DISPOSITION_CURRENT_SCHEMA,
            "dispositions": current,
            "history": history,
            "counts": {
                "current": len(current),
                "eligible": sum(row["status"] == "eligible" for row in current),
                "deferred": sum(row["status"] == "deferred" for row in current),
                "rejected": sum(row["status"] == "rejected" for row in current),
            },
        }
    }


def write_creator_frontier_dispositions(
    *,
    data_root: Any,
    actions: Sequence[Mapping[str, Any]],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Validate a complete owner-action batch before writing one raw packet and record."""
    if not isinstance(data_root, DataLakeRoot):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_data_root", "Frontier disposition write requires a resolved DataLakeRoot"
        )
    if not actions:
        raise TikTokCreatorDiscoveryFrontierError(
            "empty_frontier_disposition_batch",
            "at least one Frontier disposition action is required",
        )
    timestamp = _normalize_timestamp(
        recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    current_doc = load_creator_frontier_dispositions(data_root)
    current_rows = current_doc["creator_frontier_disposition_current"]["dispositions"]
    current_by_key = {row["candidate_key"]: row for row in current_rows}
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    unchanged: list[str] = []
    for raw in actions:
        action = _normalize_disposition_action(raw, recorded_at=timestamp)
        key = action["candidate_key"]
        if key in seen:
            raise TikTokCreatorDiscoveryFrontierError(
                "duplicate_frontier_disposition", f"duplicate candidate in one action batch: {key}"
            )
        seen.add(key)
        prior = current_by_key.get(key)
        if prior is not None and _disposition_semantics(prior) == _disposition_semantics(action):
            unchanged.append(key)
            continue
        action["supersedes_record_ids"] = [] if prior is None else [prior["disposition_id"]]
        action["disposition_id"] = "cfd_" + hashlib.sha256(
            canonical_record_bytes(action)
        ).hexdigest()[:24]
        normalized.append(_validate_disposition_entry(action))
    if not normalized:
        return {
            "status": "already_current",
            "written": 0,
            "unchanged_candidate_keys": sorted(unchanged),
            "current": current_doc,
        }

    packet_id = _write_frontier_action_packet(
        data_root=data_root, actions=normalized, recorded_at=timestamp
    )
    payload = {
        "schema_version": FRONTIER_DISPOSITION_SCHEMA,
        "raw_anchor": packet_id,
        "recorded_at": timestamp,
        "dispositions": normalized,
    }
    record_id = "cfdb_" + hashlib.sha256(canonical_record_bytes(payload)).hexdigest()[:24]
    record = {"record_id": record_id, **payload}
    path = data_root.append_record(
        subtree="derived",
        raw_anchor=packet_id,
        lane=FRONTIER_DISPOSITION_DERIVED_LANE,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )
    return {
        "status": "written",
        "record_id": record_id,
        "record_ref": path.relative_to(data_root.path).as_posix(),
        "raw_anchor": packet_id,
        "written": len(normalized),
        "unchanged_candidate_keys": sorted(unchanged),
        "current": load_creator_frontier_dispositions(data_root),
    }


def _normalize_disposition_action(
    raw: Mapping[str, Any], *, recorded_at: str
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_disposition", "Frontier disposition action must be an object"
        )
    platform = str(raw.get("platform") or "").strip().casefold()
    if platform not in {"tiktok", "youtube"}:
        raise TikTokCreatorDiscoveryFrontierError(
            "unsupported_frontier_platform",
            "Frontier disposition v1 supports TikTok and YouTube",
        )
    handle = str(raw.get("public_handle") or raw.get("handle") or "").strip().lstrip("@").casefold()
    handle_pattern = r"[a-z0-9._]{2,64}" if platform == "tiktok" else r"[a-z0-9._-]{3,30}"
    if not re.fullmatch(handle_pattern, handle):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_handle",
            f"Frontier disposition handle must be a canonical {platform.title()} handle "
            "without URL syntax",
        )
    status = str(raw.get("status") or "").strip().casefold()
    priority_value = raw.get("priority")
    priority = (
        str(priority_value).strip().casefold()
        if priority_value is not None and str(priority_value).strip()
        else None
    )
    reason = str(raw.get("reason_code") or "").strip().casefold()
    note_value = raw.get("note")
    note = str(note_value).strip() if note_value is not None and str(note_value).strip() else None
    reconsideration_value = raw.get("reconsideration")
    reconsideration = (
        str(reconsideration_value).strip().casefold()
        if reconsideration_value is not None and str(reconsideration_value).strip()
        else None
    )
    if status not in _DISPOSITION_STATUSES:
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_status", f"invalid Frontier disposition status: {status!r}"
        )
    if (status == "eligible") != (priority in _DISPOSITION_PRIORITIES):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_priority", "priority is required only for eligible Frontier dispositions"
        )
    if reason not in _DISPOSITION_REASONS or (reason == "other" and note is None):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_reason", "reason_code is invalid or reason_code=other lacks a note"
        )
    if (status == "deferred") != (reconsideration in {"owner_reopen", "new_signal"}):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_reconsideration",
            "reconsideration is required only for deferred dispositions",
        )
    return {
        "platform": platform,
        "candidate_key": f"{platform}:@{handle}",
        "public_handle": handle,
        "public_profile_url": (
            f"https://www.tiktok.com/@{handle}"
            if platform == "tiktok"
            else f"https://www.youtube.com/@{handle}"
        ),
        "status": status,
        "priority_or_none": priority,
        "reason_code": reason,
        "note_or_none": note,
        "reconsideration_or_none": reconsideration,
        "actor_posture": "owner_assertion",
        "recorded_at": _normalize_timestamp(recorded_at),
    }


def _validate_disposition_entry(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_disposition", "Frontier disposition entry must be an object"
        )
    entry = dict(raw)
    required = {
        "disposition_id", "platform", "candidate_key", "public_handle",
        "public_profile_url", "status", "priority_or_none", "reason_code",
        "note_or_none", "reconsideration_or_none", "actor_posture",
        "recorded_at", "supersedes_record_ids",
    }
    if set(entry) != required:
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_disposition", "Frontier disposition entry fields do not match v1"
        )
    normalized = _normalize_disposition_action(
        {
            "platform": entry["platform"],
            "public_handle": entry["public_handle"],
            "status": entry["status"],
            "priority": entry["priority_or_none"],
            "reason_code": entry["reason_code"],
            "note": entry["note_or_none"],
            "reconsideration": entry["reconsideration_or_none"],
        },
        recorded_at=str(entry["recorded_at"]),
    )
    for field in (
        "platform", "candidate_key", "public_handle", "public_profile_url",
        "status", "priority_or_none", "reason_code", "note_or_none",
        "reconsideration_or_none", "actor_posture", "recorded_at",
    ):
        if entry.get(field) != normalized.get(field):
            raise TikTokCreatorDiscoveryFrontierError(
                "invalid_frontier_disposition",
                f"Frontier disposition field is not canonical: {field}",
            )
    supersedes = entry.get("supersedes_record_ids")
    if not isinstance(supersedes, list) or any(
        not isinstance(value, str) or not value for value in supersedes
    ) or len(supersedes) != len(set(supersedes)):
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_supersession",
            "supersedes_record_ids must be a unique string list",
        )
    identity_payload = {key: entry[key] for key in entry if key != "disposition_id"}
    expected_id = "cfd_" + hashlib.sha256(canonical_record_bytes(identity_payload)).hexdigest()[:24]
    if entry.get("disposition_id") != expected_id:
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_disposition", "Frontier disposition content id mismatch"
        )
    return entry


def _disposition_semantics(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(field) for field in (
        "platform", "candidate_key", "public_handle", "public_profile_url",
        "status", "priority_or_none", "reason_code", "note_or_none",
        "reconsideration_or_none", "actor_posture",
    ))


def _normalize_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_timestamp", "Frontier disposition timestamp is required"
        )
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_timestamp", f"invalid Frontier disposition timestamp: {text!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise TikTokCreatorDiscoveryFrontierError(
            "invalid_frontier_timestamp", "Frontier disposition timestamp must include a UTC offset"
        )
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_frontier_action_packet_actions(
    data_root: DataLakeRoot, packet_id: str
) -> Any:
    packet = data_root.load_raw_packet(packet_id)
    matches = [
        row
        for row in packet.manifest.get("preserved_files", [])
        if isinstance(row, Mapping)
        and str(row.get("relative_packet_path") or "").replace("\\", "/").endswith(
            "creator_frontier_owner_actions.json"
        )
    ]
    if len(matches) != 1:
        raise TikTokCreatorDiscoveryFrontierError(
            "frontier_disposition_anchor_mismatch",
            f"Frontier disposition packet must preserve exactly one owner-action file: {packet_id}",
        )
    relative = str(matches[0]["relative_packet_path"]).replace("\\", "/")
    try:
        document = json.loads(
            packet.container.joinpath(*relative.split("/")).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TikTokCreatorDiscoveryFrontierError(
            "frontier_disposition_anchor_mismatch",
            f"Frontier disposition packet action file is unreadable: {packet_id}",
        ) from exc
    return document.get("actions") if isinstance(document, Mapping) else None


def _write_frontier_action_packet(
    *, data_root: DataLakeRoot, actions: Sequence[Mapping[str, Any]], recorded_at: str
) -> str:
    filename = "creator_frontier_owner_actions.json"
    staged = [(filename, canonical_record_bytes({"actions": list(actions)}))]
    file_ids = staged_file_id_map(staged)
    timing = PacketTiming(
        source_publication_or_event=not_applicable("owner action, not source publication"),
        source_edit_or_version=known_fact("append-only owner assertion"),
        capture_time=known_fact(recorded_at),
        recapture_time=not_applicable("owner action has explicit supersession"),
        cutoff_posture=not_applicable("not a time-window source"),
    )
    access = known_fact("owner-provided action through local CLI")
    archive = not_attempted("owner action has no external archive")
    media = not_applicable("structured JSON owner action")
    relationship = not_applicable("append-only action with explicit supersession")
    result = stage_and_write_packet(
        data_root=data_root,
        staged_artifacts=staged,
        source_slices=[SourceCaptureSlice(
            slice_id="creator_frontier_owner_actions_01",
            locator=known_fact("forseti://creator-frontier/owner-actions"),
            timing=timing,
            access_posture=access,
            archive_history_posture=archive,
            media_modality_posture=media,
            re_capture_relationship=relationship,
            limitations=["owner assertion; not a platform observation"],
            warning_notes=[],
            preserved_file_ids=[file_ids[filename]],
            metric_observations=[],
        )],
        source_family="creator_frontier",
        source_surface=FRONTIER_DISPOSITION_SOURCE_SURFACE,
        source_locator=known_fact("forseti://creator-frontier/owner-actions"),
        decision_question="What is the owner's current onboarding disposition for these creator candidates?",
        capture_context="Owner-authorized operational Frontier action.",
        actor_audience_context=not_applicable("operational routing action"),
        capture_mode=CaptureModeCategory.HUMAN_LED,
        operator_category="creator_frontier_owner_action_cli",
        session_identity=None,
        visible_mode_changes=["creator_frontier_append_only_disposition_v1"],
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access,
        archive_history_posture=archive,
        media_modality_posture=media,
        re_capture_relationship=relationship,
        warnings=[],
        limitations=["owner assertion; not platform evidence"],
        receipt_summary="Creator Frontier owner dispositions preserved.",
        receipt_non_claims=["not onboarding completion", "not monitoring eligibility"],
    )
    return Path(result.output_directory).name
