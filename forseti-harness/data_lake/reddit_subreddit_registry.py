"""Lake-native Reddit Subreddit Registry authority.

Git owns this code, the taxonomy vocabularies, and the schemas.  Live registry
state is append-only under ``derived/``, anchored on the subreddit, and folds on
read.  There is deliberately no generation or ``CURRENT`` projection: the
consumers are internal and operator-run, so this takes the lighter Creator
Frontier tier rather than the Creator Registry generation machinery.

Each subreddit has exactly one genesis record -- a migrated
``reddit_subreddit_registry_baseline_v1`` or an ``add`` roster change for a
subreddit discovered after the migration.  Deltas layer on top: roster changes
apply by predecessor chain, grid observations dedupe by provenance pointer.  A
missing genesis, ambiguous roster head, capture-state downgrade, identity
mismatch, or divergent legacy hash fails closed rather than guessing.

Contract: ``forseti/product/spines/capture/core/source_families/social_media/
reddit/reddit_subreddit_registry_lake_cutover_architecture_v0.md``
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from harness_utils import utc_now_z
from data_lake.canonical_json import canonical_compact_json_bytes, canonical_record_bytes
from data_lake.root import DataLakeRoot, anchor_shard, is_inflight_record_temp

REDDIT_BASELINE_LANE = "reddit_subreddit_registry_baseline"
REDDIT_OBSERVATION_LANE = "reddit_subreddit_observation"
REDDIT_ROSTER_CHANGE_LANE = "reddit_subreddit_roster_change"

BASELINE_SCHEMA_VERSION = "reddit_subreddit_registry_baseline_v1"
OBSERVATION_SCHEMA_VERSION = "reddit_subreddit_observation_v1"
ROSTER_CHANGE_SCHEMA_VERSION = "reddit_subreddit_roster_change_v1"
REGISTRY_DOCUMENT_SCHEMA_VERSION = "reddit_subreddit_registry_v0"

DERIVED_SUBTREE = "derived"

# Mirrors the vocabulary contract in reddit_subreddit_registry_spec_v0.md.
# test_reddit_subreddit_registry_lake.py cross-checks both sets against the spec
# so a Git-side vocabulary extension cannot silently diverge from this writer.
NICHE_PATHS = frozenset(
    {
        "beauty",
        "beauty/fragrance",
        "beauty/skincare",
        "beauty/makeup",
        "beauty/hair",
        "beauty/nails",
    }
)
VENUE_ROLES = frozenset(
    {
        "hub",
        "dupe_value",
        "exchange",
        "retailer",
        "deal",
        "creator_watch",
        "counterevidence",
        "regional",
        "demographic",
        "specialist",
    }
)
# ``retired`` is the stop-tracking state: the lake is append-only, so a
# subreddit's history is never deleted, but a retired row is excluded from the
# capture roster so it stops costing a request per pass.  It is a roster
# decision, not a judgement about the subreddit and not a Reddit-side status
# (a banned or private venue is ``status``, not this).
DISCOVERY_STATES = frozenset({"known_subreddit", "candidate_new_subreddit", "retired"})
RETIRED_DISCOVERY_STATE = "retired"
STATUS_VALUES = frozenset({"active", "unverified", "private", "banned", "quarantined"})
CAPTURE_STATE_RANK = {
    "no_packet_recorded": 0,
    "grid_packets_recorded": 1,
    "thread_packets_recorded": 2,
}

# Non-grid row state a roster change may carry.  Grid-derived effects
# (observations, register_pointers, and the grid capture_state upgrade) belong
# to the observation record and are refused here.
ROSTER_CHANGE_FIELDS = frozenset(
    {
        "created_utc_or_none",
        "title_or_none",
        "public_description_or_none",
        "posting_posture_or_none",
        "descriptive_observed_at",
        "niche_paths",
        "venue_roles",
        "discovery_state",
        "source_pointers",
        "capture_state",
        "status",
        "status_observed_at",
    }
)

_ROW_TEMPLATE: dict[str, Any] = {
    "subreddit": "",
    "url": "",
    "status": "unverified",
    "status_observed_at": None,
    "created_utc_or_none": None,
    "title_or_none": None,
    "public_description_or_none": None,
    "posting_posture_or_none": None,
    "descriptive_observed_at": None,
    "descriptive_changes": [],
    "niche_paths": [],
    "venue_roles": [],
    "discovery_state": "candidate_new_subreddit",
    "capture_state": "no_packet_recorded",
    "observations": [],
    "first_seen_at": None,
    "register_pointers": [],
    "source_pointers": [],
}


class RedditSubredditRegistryLakeError(ValueError):
    """Fail-closed lake registry validation, conflict, or identity error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def normalize_subreddit(value: Any) -> str:
    """Canonical subreddit key: the bare name, casefolded.

    The registry's own rows are stored casefolded, and the anchor must be
    byte-stable because it is part of the append-only record path.
    """
    if not isinstance(value, str) or not value.strip():
        raise RedditSubredditRegistryLakeError(
            "subreddit_invalid", f"subreddit must be a non-empty string: {value!r}"
        )
    name = value.strip()
    for prefix in ("/r/", "r/"):
        if name.lower().startswith(prefix):
            name = name[len(prefix) :]
            break
    name = name.strip("/").casefold()
    if not name or not all(character.isalnum() or character == "_" for character in name):
        raise RedditSubredditRegistryLakeError(
            "subreddit_invalid", f"subreddit is not a bare subreddit name: {value!r}"
        )
    return name


def _record_id(prefix: str, basis: Any) -> str:
    digest = hashlib.sha256(canonical_compact_json_bytes(basis)).hexdigest()
    return f"{prefix}_{digest[:24]}"


def _content_hash(record: Mapping[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "content_hash"}
    return hashlib.sha256(canonical_compact_json_bytes(body)).hexdigest()


def _seal(record: dict[str, Any]) -> dict[str, Any]:
    record["content_hash"] = _content_hash(record)
    return record


def _lane_records(data_root: DataLakeRoot, *, subreddit: str, lane: str) -> list[dict[str, Any]]:
    lane_dir = data_root.lane_dir(subtree=DERIVED_SUBTREE, raw_anchor=subreddit, lane=lane)
    if not lane_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(lane_dir.iterdir()):
        # A concurrent refresh may have a record staged but not yet linked;
        # iterdir returns its dot-prefixed temp, and reading one would fail on
        # JSON shape or content hash rather than on anything real.
        if is_inflight_record_temp(path.name):
            continue
        if not path.is_file():
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RedditSubredditRegistryLakeError(
                "record_unreadable", f"lake record is not valid JSON: {path} ({exc})"
            ) from exc
        if not isinstance(record, dict):
            raise RedditSubredditRegistryLakeError(
                "record_shape", f"lake record is not an object: {path}"
            )
        observed = _content_hash(record)
        if record.get("content_hash") != observed:
            raise RedditSubredditRegistryLakeError(
                "record_content_hash_mismatch",
                f"record content_hash does not match its bytes: {path}",
            )
        records.append(record)
    return records


def known_subreddits(data_root: DataLakeRoot) -> list[str]:
    """Enumerate every subreddit anchor carrying registry records.

    Whole-roster reads scan the derived anchor directories: ``DataLakeRoot``
    exposes keyed ``lane_dir`` access and no derived-record availability index,
    which the cut-over contract accepts explicitly for v0.
    """
    derived = data_root.path / DERIVED_SUBTREE
    if not derived.is_dir():
        return []
    lanes = (REDDIT_BASELINE_LANE, REDDIT_OBSERVATION_LANE, REDDIT_ROSTER_CHANGE_LANE)
    found: set[str] = set()
    for shard in derived.iterdir():
        if not shard.is_dir():
            continue
        for anchor in shard.iterdir():
            if not anchor.is_dir():
                continue
            if anchor.name in found:
                continue
            if any((anchor / lane).is_dir() for lane in lanes):
                # Anchors are shared with other lanes; keep only real subreddit
                # anchors whose shard actually matches this anchor name.
                if shard.name == anchor_shard(anchor.name):
                    found.add(anchor.name)
    return sorted(found)


def capture_roster(data_root: DataLakeRoot) -> list[str]:
    """The subreddits a capture pass should actually visit.

    ``known_subreddits`` is the anchor census and stays exhaustive -- the fold,
    parity, and any history read must still see retired rows.  This is the
    narrower question a runner asks: retired rows are excluded so they stop
    costing one request per pass, without deleting anything.
    """
    roster: list[str] = []
    for name in known_subreddits(data_root):
        row = fold_subreddit(data_root, name)
        if row.get("discovery_state") != RETIRED_DISCOVERY_STATE:
            roster.append(name)
    return roster


def _validate_field_values(field: str, value: Any) -> Any:
    if field in {"niche_paths", "venue_roles"}:
        allowed = NICHE_PATHS if field == "niche_paths" else VENUE_ROLES
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise RedditSubredditRegistryLakeError(
                "vocabulary_shape", f"{field} must be a list of strings: {value!r}"
            )
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise RedditSubredditRegistryLakeError(
                "vocabulary_unknown",
                f"{field} carries values absent from the Git vocabulary contract: {unknown}",
            )
        return sorted(set(value))
    if field == "discovery_state" and value not in DISCOVERY_STATES:
        raise RedditSubredditRegistryLakeError(
            "discovery_state_unknown", f"discovery_state is not a contract value: {value!r}"
        )
    if field == "status" and value not in STATUS_VALUES:
        raise RedditSubredditRegistryLakeError(
            "status_unknown", f"status is not a contract value: {value!r}"
        )
    if field == "capture_state" and value not in CAPTURE_STATE_RANK:
        raise RedditSubredditRegistryLakeError(
            "capture_state_unknown", f"capture_state is not a contract value: {value!r}"
        )
    return value


def _weekly_normalized(observation: Mapping[str, Any]) -> dict[str, Any]:
    """An omitted weekly key and an explicit null are the same observation.

    The weekly reach fields are nullable additions with no migration, so two
    observations that differ only in whether those keys are present must
    compare equal; otherwise a replay of an already-folded packet fails closed.
    """
    normalized = dict(observation)
    normalized.setdefault("weekly_visitor_count_or_none", None)
    normalized.setdefault("weekly_contribution_count_or_none", None)
    return normalized


def _apply_capture_state(row: dict[str, Any], candidate: str) -> None:
    """Assign capture_state for an operator-authored roster change.

    A roster change naming a lower state is an operator error worth refusing,
    so this stays strict.  Replayed observation effects use the floor below.
    """
    current = row.get("capture_state", "no_packet_recorded")
    if CAPTURE_STATE_RANK[candidate] < CAPTURE_STATE_RANK.get(current, 0):
        raise RedditSubredditRegistryLakeError(
            "capture_state_downgrade",
            f"capture_state may not downgrade {current!r} -> {candidate!r}",
        )
    row["capture_state"] = candidate


def _raise_capture_state_floor(row: dict[str, Any], candidate: str) -> None:
    """Apply an observation's capture_state effect as a floor, never a ceiling.

    The writer records this effect against the fold as it stood at write time,
    and the fold replays roster changes before observations regardless of which
    was written first.  A thread-driven roster upgrade written after a packet's
    observation therefore replays first, and assigning the recorded value would
    drive the row backwards on a state that is defined monotonic.  The effect
    only ever asserts "at least this much capture exists for this packet", so a
    floor is its real meaning; a strict assignment made the fold refuse to read
    at all (68 backfilled upgrades, 46 subreddits, 2026-07-30).
    """
    current = row.get("capture_state", "no_packet_recorded")
    if CAPTURE_STATE_RANK[candidate] > CAPTURE_STATE_RANK.get(current, 0):
        row["capture_state"] = candidate


def should_apply_status_observation(*, row: Mapping[str, Any], observed_at: str) -> bool:
    """The registry spec's two-speed liveness rule, evaluated against the fold.

    Mirrors ``capture_spine.reddit_subreddit_grid.materializer`` so the lake
    writer records the same decision the Git materializer would have made.
    """
    try:
        incoming_date = date.fromisoformat(observed_at)
    except (TypeError, ValueError) as exc:
        raise RedditSubredditRegistryLakeError(
            "status_date_invalid",
            f"non-ISO status date in observation: {observed_at!r}",
        ) from exc
    current_value = row.get("status_observed_at")
    if not isinstance(current_value, str) or not current_value:
        return True
    try:
        current_date = date.fromisoformat(current_value)
    except ValueError as exc:
        raise RedditSubredditRegistryLakeError(
            "status_date_invalid",
            f"non-ISO status date in fold: {current_value!r}",
        ) from exc
    if incoming_date > current_date:
        return True
    if incoming_date < current_date:
        return False
    return row.get("status") in {None, "unverified", "active"}


# --------------------------------------------------------------------------
# Fold
# --------------------------------------------------------------------------


def _genesis_row(data_root: DataLakeRoot, subreddit: str) -> tuple[dict[str, Any], str | None]:
    baselines = _lane_records(data_root, subreddit=subreddit, lane=REDDIT_BASELINE_LANE)
    roster = _lane_records(data_root, subreddit=subreddit, lane=REDDIT_ROSTER_CHANGE_LANE)
    adds = [record for record in roster if record.get("change_kind") == "add"]

    if len(baselines) > 1:
        raise RedditSubredditRegistryLakeError(
            "baseline_duplicate", f"{subreddit}: expected one baseline, found {len(baselines)}"
        )
    if baselines and adds:
        raise RedditSubredditRegistryLakeError(
            "genesis_conflict",
            f"{subreddit}: carries both a migration baseline and an add roster change",
        )
    if len(adds) > 1:
        raise RedditSubredditRegistryLakeError(
            "genesis_duplicate", f"{subreddit}: {len(adds)} add roster changes; expected one"
        )
    if baselines:
        record = baselines[0]
        if normalize_subreddit(record.get("subreddit")) != subreddit:
            raise RedditSubredditRegistryLakeError(
                "identity_mismatch", f"baseline anchored at {subreddit} names {record.get('subreddit')!r}"
            )
        return deepcopy(record["row"]), record.get("legacy_file_sha256")
    if adds:
        row = deepcopy(_ROW_TEMPLATE)
        row["subreddit"] = subreddit
        row["url"] = f"https://www.reddit.com/r/{subreddit}/"
        row["first_seen_at"] = adds[0].get("changed_at", "")[:10] or None
        # The add record carries the subreddit's initial field values; without
        # applying them the genesis row would silently drop everything the
        # operator supplied when adding it.
        _apply_roster_change(row, adds[0])
        return row, None
    raise RedditSubredditRegistryLakeError(
        "genesis_missing",
        f"{subreddit}: no migration baseline and no add roster change; refusing to fold deltas",
    )


def _chain_root_id(records: list[dict[str, Any]]) -> str | None:
    """The id every chain hangs from: the ``add`` genesis, or ``None``.

    A baseline-migrated subreddit has no roster genesis record, so its chain
    roots at ``None``.  An ``add`` genesis roots at its own record id, which
    keeps the chain self-anchoring rather than sharing an implicit root with
    the baseline case.
    """
    adds = [record for record in records if record.get("change_kind") == "add"]
    return adds[0]["record_id"] if adds else None


def _ordered_roster_chain(subreddit: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order roster deltas by their predecessor chain; ambiguity fails closed."""
    deltas = [record for record in records if record.get("change_kind") != "add"]
    if not deltas:
        return []
    root = _chain_root_id(records)
    by_predecessor: dict[str | None, list[dict[str, Any]]] = {}
    for record in deltas:
        by_predecessor.setdefault(record.get("predecessor_record_id"), []).append(record)
    for predecessor, group in by_predecessor.items():
        if len(group) > 1:
            raise RedditSubredditRegistryLakeError(
                "roster_head_ambiguous",
                f"{subreddit}: {len(group)} roster changes share predecessor {predecessor!r}; "
                "filesystem order may not decide current state",
            )
    known = {record["record_id"] for record in records}
    chain: list[dict[str, Any]] = []
    cursor: str | None = root
    seen: set[str | None] = set()
    while cursor in by_predecessor:
        if cursor in seen:
            raise RedditSubredditRegistryLakeError(
                "roster_chain_cycle", f"{subreddit}: roster predecessor chain cycles at {cursor!r}"
            )
        seen.add(cursor)
        record = by_predecessor[cursor][0]
        chain.append(record)
        cursor = record["record_id"]
    if len(chain) != len(deltas):
        dangling = sorted(
            str(record.get("predecessor_record_id"))
            for record in deltas
            if record not in chain
        )
        raise RedditSubredditRegistryLakeError(
            "roster_predecessor_missing",
            f"{subreddit}: {len(deltas) - len(chain)} roster change(s) name a predecessor that is "
            f"not in this subreddit's chain: {dangling}"
            + ("" if all(item in known for item in dangling) else " (unknown record id)"),
        )
    return chain


def _apply_roster_change(row: dict[str, Any], record: Mapping[str, Any]) -> None:
    for field, value in sorted(record.get("changes", {}).items()):
        if field not in ROSTER_CHANGE_FIELDS:
            raise RedditSubredditRegistryLakeError(
                "roster_field_forbidden",
                f"roster change may not set {field!r}; grid-derived state belongs to observations",
            )
        checked = _validate_field_values(field, value)
        if field == "capture_state":
            _apply_capture_state(row, checked)
        else:
            row[field] = checked


def _apply_observation(row: dict[str, Any], record: Mapping[str, Any]) -> None:
    observation = record["observation"]
    pointer = observation["provenance_pointer"]
    effects = record.get("row_effects", {})
    if not isinstance(effects, Mapping):
        raise RedditSubredditRegistryLakeError(
            "observation_effects_shape",
            f"observation row_effects must be an object: {effects!r}",
        )
    unknown_effects = sorted(set(effects) - {"status", "capture_state"})
    if unknown_effects:
        raise RedditSubredditRegistryLakeError(
            "observation_effect_unknown",
            f"observation carries unknown row effects: {unknown_effects}",
        )
    status = effects.get("status")
    expected_status = {
        "status": "active",
        "status_observed_at": observation["observed_at"],
    }
    if status is not None and status != expected_status:
        raise RedditSubredditRegistryLakeError(
            "observation_status_effect_invalid",
            f"grid observation status effect must equal {expected_status!r}: {status!r}",
        )
    capture_state = effects.get("capture_state")
    if capture_state not in {None, "grid_packets_recorded"}:
        raise RedditSubredditRegistryLakeError(
            "observation_capture_state_effect_invalid",
            "grid observation capture_state effect must be "
            f"'grid_packets_recorded' or None: {capture_state!r}",
        )
    status_should_apply = should_apply_status_observation(
        row=row,
        observed_at=observation["observed_at"],
    )
    for existing in row.setdefault("observations", []):
        if existing.get("provenance_pointer") == pointer:
            if existing != observation:
                raise RedditSubredditRegistryLakeError(
                    "observation_provenance_conflict",
                    f"provenance pointer {pointer} already folded with different values",
                )
            return
    row["observations"].append(deepcopy(observation))

    # Re-evaluate the two-speed rule at replay time for the same reason the
    # capture_state floor exists: the recorded decision was made against the
    # fold at write time, and a roster change written later replays earlier.
    # Applying it unconditionally would let an older observation revert a newer
    # roster-authored status and append a spurious descriptive_changes entry.
    if status is not None and status_should_apply:
        if row.get("status") != status.get("status"):
            row.setdefault("descriptive_changes", []).append(
                {
                    "field": "status",
                    "changed_at": status["status_observed_at"],
                    "previous_value": row.get("status"),
                }
            )
            row["status"] = status["status"]
        row["status_observed_at"] = status["status_observed_at"]
    if capture_state is not None:
        _raise_capture_state_floor(row, capture_state)
    register_pointers = row.setdefault("register_pointers", [])
    if pointer not in register_pointers:
        register_pointers.append(pointer)


def fold_subreddit(data_root: DataLakeRoot, subreddit: str) -> dict[str, Any]:
    """Fold one subreddit's authority records into its registry row."""
    key = normalize_subreddit(subreddit)
    row, _legacy_hash = _genesis_row(data_root, key)
    roster = _lane_records(data_root, subreddit=key, lane=REDDIT_ROSTER_CHANGE_LANE)
    for record in _ordered_roster_chain(key, roster):
        _apply_roster_change(row, record)
    observations = _lane_records(data_root, subreddit=key, lane=REDDIT_OBSERVATION_LANE)
    for record in sorted(
        observations,
        key=lambda item: (
            item["observation"]["observed_at"],
            item["observation"]["provenance_pointer"],
            item["record_id"],
        ),
    ):
        if normalize_subreddit(record.get("subreddit")) != key:
            raise RedditSubredditRegistryLakeError(
                "identity_mismatch",
                f"observation anchored at {key} names {record.get('subreddit')!r}",
            )
        _apply_observation(row, record)
    return row


def load_current_registry(data_root: DataLakeRoot) -> dict[str, Any]:
    """Fold every known subreddit into the registry document shape.

    The returned document matches the Git registry's shape so operational
    readers swap source without reshaping.  Baselines must agree on the legacy
    file hash they migrated from; divergence fails closed.
    """
    names = known_subreddits(data_root)
    legacy_hashes: set[str] = set()
    rows: list[dict[str, Any]] = []
    for name in names:
        row, legacy_hash = _genesis_row(data_root, name)
        if legacy_hash:
            legacy_hashes.add(legacy_hash)
        rows.append(fold_subreddit(data_root, name))
    if len(legacy_hashes) > 1:
        raise RedditSubredditRegistryLakeError(
            "baseline_legacy_hash_divergent",
            f"baselines bind {len(legacy_hashes)} different legacy registry hashes: {sorted(legacy_hashes)}",
        )
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    return {
        "reddit_subreddit_registry": {
            "schema_version": REGISTRY_DOCUMENT_SCHEMA_VERSION,
            "authority": "lake",
            "legacy_baseline_sha256": sorted(legacy_hashes)[0] if legacy_hashes else None,
            "counts": {
                "subreddits_total": len(rows),
                "by_status": dict(sorted(by_status.items())),
            },
            "subreddits": rows,
        }
    }


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------


def append_grid_observation(
    data_root: DataLakeRoot,
    *,
    subreddit: str,
    observed_at: str,
    subscriber_count_or_none: str | None,
    active_user_count_or_none: str | None,
    source_surface: str,
    provenance_pointer: str,
    absent_reason_or_none: str | None,
    weekly_visitor_count_or_none: str | None = None,
    weekly_contribution_count_or_none: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append one grid observation plus the row effects the same packet implies.

    The writer computes the liveness, capture-state, and register-pointer
    effects against the current fold and records the decision it made, so the
    fold replays rather than re-derives them.
    """
    key = normalize_subreddit(subreddit)
    row = fold_subreddit(data_root, key)

    observation = {
        "observed_at": observed_at,
        "subscriber_count_or_none": subscriber_count_or_none,
        "active_user_count_or_none": active_user_count_or_none,
        "source_surface": source_surface,
        "provenance_pointer": provenance_pointer,
        "absent_reason_or_none": absent_reason_or_none,
    }
    # Only surfaces that actually state weekly reach carry the keys. old Reddit
    # has no equivalent, so its observations keep the shape they have always
    # had rather than gaining two permanent nulls.
    if weekly_visitor_count_or_none is not None or weekly_contribution_count_or_none is not None:
        observation["weekly_visitor_count_or_none"] = weekly_visitor_count_or_none
        observation["weekly_contribution_count_or_none"] = weekly_contribution_count_or_none
    for existing in row.get("observations", []):
        if existing.get("provenance_pointer") == provenance_pointer:
            # Same rule as the fold: an exact replay is idempotent, but the same
            # packet yielding different values is a conflict, not a duplicate.
            # Returning already_current here would silently drop the new values
            # and leave the writer laxer than the reader that has to fold them.
            # BOTH sides are normalized because the weekly keys are nullable
            # with no migration: an omitted key and an explicit null are the
            # same observation, and comparing raw dicts would make re-feeding an
            # already-folded packet fail closed instead of being idempotent.
            if _weekly_normalized(existing) != _weekly_normalized(observation):
                raise RedditSubredditRegistryLakeError(
                    "observation_provenance_conflict",
                    f"provenance pointer {provenance_pointer} is already recorded for "
                    f"{key} with different values",
                )
            return {
                "subreddit": key,
                "status": "already_current",
                "record_id": None,
                "written": False,
            }

    effects: dict[str, Any] = {"status": None, "capture_state": None}
    if should_apply_status_observation(row=row, observed_at=observed_at):
        effects["status"] = {"status": "active", "status_observed_at": observed_at}
    if row.get("capture_state") == "no_packet_recorded":
        effects["capture_state"] = "grid_packets_recorded"

    record_id = _record_id("rso", {"subreddit": key, "provenance_pointer": provenance_pointer})
    record = _seal(
        {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "record_id": record_id,
            "subreddit": key,
            "observation": observation,
            "row_effects": effects,
            "recorded_at": utc_now_z(),
        }
    )
    if dry_run:
        return {"subreddit": key, "status": "would_write", "record_id": record_id, "written": False}
    data_root.append_record(
        subtree=DERIVED_SUBTREE,
        raw_anchor=key,
        lane=REDDIT_OBSERVATION_LANE,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )
    return {"subreddit": key, "status": "written", "record_id": record_id, "written": True}


def append_reach_observation(
    data_root: DataLakeRoot,
    *,
    subreddit: str,
    observed_at: str,
    source_surface: str,
    provenance_pointer: str,
    subscriber_count_or_none: str | None = None,
    weekly_visitor_count_or_none: str | None = None,
    weekly_contribution_count_or_none: str | None = None,
    absent_reason_or_none: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append one agent-read reach observation (SERP band or community panel).

    Same lane and dedupe rule as grid observations, different evidence class:
    the value was read off a browser surface by the agent, not projected from a
    packet.  Counts stay strings so rounded bands like ``"135.3K+"`` are legal.
    A reach read carries NO row effects -- a third-party band cannot prove
    liveness and there is no packet to advance ``capture_state``; the fold just
    gains the observation and its register pointer.
    """
    key = normalize_subreddit(subreddit)
    try:
        date.fromisoformat(observed_at)
    except ValueError as exc:
        raise RedditSubredditRegistryLakeError(
            "observed_at_invalid", f"observed_at must be an ISO date: {observed_at!r}"
        ) from exc
    if not isinstance(source_surface, str) or not source_surface.strip():
        raise RedditSubredditRegistryLakeError(
            "source_surface_missing", "reach observation requires a source_surface"
        )
    if not isinstance(provenance_pointer, str) or not provenance_pointer.strip():
        raise RedditSubredditRegistryLakeError(
            "provenance_missing", "reach observation requires a provenance_pointer"
        )
    if all(
        value is None
        for value in (
            subscriber_count_or_none,
            weekly_visitor_count_or_none,
            weekly_contribution_count_or_none,
            absent_reason_or_none,
        )
    ):
        raise RedditSubredditRegistryLakeError(
            "observation_empty",
            "reach observation carries no count and no absent reason; refusing to record nothing",
        )

    row = fold_subreddit(data_root, key)
    observation = {
        "observed_at": observed_at,
        "subscriber_count_or_none": subscriber_count_or_none,
        "active_user_count_or_none": None,
        "weekly_visitor_count_or_none": weekly_visitor_count_or_none,
        "weekly_contribution_count_or_none": weekly_contribution_count_or_none,
        "source_surface": source_surface,
        "provenance_pointer": provenance_pointer,
        "absent_reason_or_none": absent_reason_or_none,
    }
    for existing in row.get("observations", []):
        if existing.get("provenance_pointer") == provenance_pointer:
            # The weekly fields were added as nullable with no migration. A
            # legacy row that omits them is semantically equal to explicit nulls.
            comparable_existing = dict(existing)
            comparable_existing.setdefault("weekly_visitor_count_or_none", None)
            comparable_existing.setdefault("weekly_contribution_count_or_none", None)
            if comparable_existing != observation:
                raise RedditSubredditRegistryLakeError(
                    "observation_provenance_conflict",
                    f"provenance pointer {provenance_pointer} is already recorded for "
                    f"{key} with different values",
                )
            return {
                "subreddit": key,
                "status": "already_current",
                "record_id": None,
                "written": False,
            }

    record_id = _record_id("rso", {"subreddit": key, "provenance_pointer": provenance_pointer})
    record = _seal(
        {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "record_id": record_id,
            "subreddit": key,
            "observation": observation,
            "row_effects": {"status": None, "capture_state": None},
            "recorded_at": utc_now_z(),
        }
    )
    if dry_run:
        return {"subreddit": key, "status": "would_write", "record_id": record_id, "written": False}
    data_root.append_record(
        subtree=DERIVED_SUBTREE,
        raw_anchor=key,
        lane=REDDIT_OBSERVATION_LANE,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )
    return {"subreddit": key, "status": "written", "record_id": record_id, "written": True}


def append_roster_change(
    data_root: DataLakeRoot,
    *,
    subreddit: str,
    changes: Mapping[str, Any] | None = None,
    change_kind: str = "update",
    actor: str,
    note_or_none: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add a tracked subreddit or change its non-grid row state.

    This is the reviewed front door that replaces pull-request review of roster
    edits: unknown vocabulary values, duplicate genesis, and ambiguous heads
    fail closed here rather than being caught after the fact.
    """
    key = normalize_subreddit(subreddit)
    if change_kind not in {"add", "update"}:
        raise RedditSubredditRegistryLakeError(
            "change_kind_unknown", f"change_kind must be add or update: {change_kind!r}"
        )
    payload = dict(changes or {})
    for field, value in sorted(payload.items()):
        if field not in ROSTER_CHANGE_FIELDS:
            raise RedditSubredditRegistryLakeError(
                "roster_field_forbidden",
                f"roster change may not set {field!r}; grid-derived state belongs to observations",
            )
        payload[field] = _validate_field_values(field, value)

    existing = _lane_records(data_root, subreddit=key, lane=REDDIT_ROSTER_CHANGE_LANE)
    baselines = _lane_records(data_root, subreddit=key, lane=REDDIT_BASELINE_LANE)
    if change_kind == "add":
        if baselines or any(record.get("change_kind") == "add" for record in existing):
            raise RedditSubredditRegistryLakeError(
                "genesis_duplicate", f"{key}: already has a genesis record; use change_kind=update"
            )
        predecessor = None
    else:
        if not baselines and not any(record.get("change_kind") == "add" for record in existing):
            raise RedditSubredditRegistryLakeError(
                "genesis_missing", f"{key}: no genesis record; add the subreddit before updating it"
            )
        chain = _ordered_roster_chain(key, existing)
        predecessor = chain[-1]["record_id"] if chain else _chain_root_id(existing)

    changed_at = utc_now_z()
    basis = {
        "subreddit": key,
        "change_kind": change_kind,
        "changes": payload,
        "predecessor_record_id": predecessor,
        "changed_at": changed_at,
    }
    record_id = _record_id("rsr", basis)
    record = _seal(
        {
            "schema_version": ROSTER_CHANGE_SCHEMA_VERSION,
            "record_id": record_id,
            "actor": actor,
            "note_or_none": note_or_none,
            **basis,
        }
    )
    if dry_run:
        return {
            "subreddit": key,
            "status": "would_write",
            "record_id": record_id,
            "predecessor_record_id": predecessor,
            "written": False,
        }
    data_root.append_record(
        subtree=DERIVED_SUBTREE,
        raw_anchor=key,
        lane=REDDIT_ROSTER_CHANGE_LANE,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )
    return {
        "subreddit": key,
        "status": "written",
        "record_id": record_id,
        "predecessor_record_id": predecessor,
        "written": True,
    }


# --------------------------------------------------------------------------
# One-time baseline migration
# --------------------------------------------------------------------------


def _legacy_rows(registry_path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = registry_path.read_bytes()
    legacy_hash = hashlib.sha256(raw).hexdigest()
    document = json.loads(raw.decode("utf-8"))
    registry = document.get("reddit_subreddit_registry")
    if not isinstance(registry, dict) or not isinstance(registry.get("subreddits"), list):
        raise RedditSubredditRegistryLakeError(
            "legacy_shape", f"not a reddit_subreddit_registry document: {registry_path}"
        )
    return registry["subreddits"], legacy_hash


def migrate_legacy_registry(
    data_root: DataLakeRoot,
    *,
    registry_path: Path,
    migration_packet_pointer: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write one baseline per legacy row, binding the exact legacy file hash.

    A dry run proves the subreddit set, per-subreddit and total observation
    counts, and folded semantic parity without any authority write.  An
    identical rerun is ``already_current``; a differing legacy hash or a partial
    baseline set is a blocker.
    """
    rows, legacy_hash = _legacy_rows(registry_path)
    planned: list[tuple[str, str, dict[str, Any]]] = []
    for row in rows:
        key = normalize_subreddit(row.get("subreddit"))
        basis = {"subreddit": key, "legacy_file_sha256": legacy_hash}
        record_id = _record_id("rsb", basis)
        record = _seal(
            {
                "schema_version": BASELINE_SCHEMA_VERSION,
                "record_id": record_id,
                "subreddit": key,
                "legacy_file_sha256": legacy_hash,
                "legacy_registry_path": registry_path.name,
                "migration_packet_pointer": migration_packet_pointer,
                "row": deepcopy(row),
                "recorded_at": utc_now_z(),
            }
        )
        planned.append((key, record_id, record))

    existing = {
        name: _lane_records(data_root, subreddit=name, lane=REDDIT_BASELINE_LANE)
        for name in known_subreddits(data_root)
    }
    already = {name for name, records in existing.items() if records}
    for name, records in existing.items():
        for record in records:
            if record.get("legacy_file_sha256") != legacy_hash:
                raise RedditSubredditRegistryLakeError(
                    "baseline_legacy_hash_divergent",
                    f"{name}: existing baseline migrated from a different legacy registry "
                    f"({record.get('legacy_file_sha256')} != {legacy_hash})",
                )
    planned_names = {name for name, _id, _record in planned}
    if already and already != planned_names:
        raise RedditSubredditRegistryLakeError(
            "baseline_partial",
            "lake carries a partial baseline set; expected all or none "
            f"(missing {sorted(planned_names - already)}, extra {sorted(already - planned_names)})",
        )

    result = {
        "registry_path": str(registry_path),
        "legacy_file_sha256": legacy_hash,
        "subreddits_total": len(planned),
        "observations_total": sum(len(row.get("observations", [])) for row in rows),
        "observations_by_subreddit": {
            normalize_subreddit(row["subreddit"]): len(row.get("observations", []))
            for row in rows
        },
        "status": "already_current" if already == planned_names and already else "planned",
        "written": False,
        "non_claims": [
            "not validation",
            "not readiness",
            "not capture authorization",
            "not live Reddit access",
        ],
    }
    if already == planned_names and already:
        return result
    if dry_run:
        result["status"] = "would_write"
        return result

    for key, record_id, record in planned:
        data_root.append_record(
            subtree=DERIVED_SUBTREE,
            raw_anchor=key,
            lane=REDDIT_BASELINE_LANE,
            record_id=record_id,
            data=canonical_record_bytes(record),
        )
    result["status"] = "written"
    result["written"] = True
    return result


def semantic_parity(*, legacy_registry_path: Path, folded: Mapping[str, Any]) -> dict[str, Any]:
    """Compare the folded document against the legacy rows field by field.

    Parity is over the row payloads, not the file bytes: the folded document
    carries lake provenance the Git file never had.
    """
    rows, legacy_hash = _legacy_rows(legacy_registry_path)
    legacy_by_name = {normalize_subreddit(row["subreddit"]): row for row in rows}
    folded_by_name = {
        normalize_subreddit(row["subreddit"]): row
        for row in folded["reddit_subreddit_registry"]["subreddits"]
    }
    mismatches: list[dict[str, Any]] = []
    for name in sorted(set(legacy_by_name) | set(folded_by_name)):
        legacy_row = legacy_by_name.get(name)
        folded_row = folded_by_name.get(name)
        if legacy_row is None or folded_row is None:
            mismatches.append({"subreddit": name, "field": "<row>", "reason": "present in only one side"})
            continue
        for field in sorted(set(legacy_row) | set(folded_row)):
            if legacy_row.get(field) != folded_row.get(field):
                mismatches.append(
                    {
                        "subreddit": name,
                        "field": field,
                        "legacy": legacy_row.get(field),
                        "folded": folded_row.get(field),
                    }
                )
    return {
        "legacy_file_sha256": legacy_hash,
        "legacy_subreddits": len(legacy_by_name),
        "folded_subreddits": len(folded_by_name),
        "parity": not mismatches,
        "mismatches": mismatches,
    }


__all__ = [
    "REDDIT_BASELINE_LANE",
    "REDDIT_OBSERVATION_LANE",
    "REDDIT_ROSTER_CHANGE_LANE",
    "NICHE_PATHS",
    "VENUE_ROLES",
    "DISCOVERY_STATES",
    "CAPTURE_STATE_RANK",
    "RedditSubredditRegistryLakeError",
    "append_grid_observation",
    "append_roster_change",
    "fold_subreddit",
    "known_subreddits",
    "load_current_registry",
    "migrate_legacy_registry",
    "normalize_subreddit",
    "semantic_parity",
    "should_apply_status_observation",
]
