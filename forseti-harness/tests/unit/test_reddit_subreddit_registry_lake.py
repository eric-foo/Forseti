from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from data_lake.reddit_subreddit_registry import (
    REDDIT_BASELINE_LANE,
    CAPTURE_STATE_RANK,
    NICHE_PATHS,
    REDDIT_OBSERVATION_LANE,
    REDDIT_ROSTER_CHANGE_LANE,
    STATUS_VALUES,
    VENUE_ROLES,
    RedditSubredditRegistryLakeError,
    append_grid_observation,
    append_reach_observation,
    append_roster_change,
    capture_roster,
    fold_subreddit,
    known_subreddits,
    load_current_registry,
    migrate_legacy_registry,
    normalize_subreddit,
    semantic_parity,
)
from data_lake.root import DataLakeRoot

REPO_ROOT = Path(__file__).resolve().parents[3]
REDDIT_LANE_ROOT = (
    REPO_ROOT
    / "forseti"
    / "product"
    / "spines"
    / "capture"
    / "core"
    / "source_families"
    / "social_media"
    / "reddit"
)
LIVE_REGISTRY = REDDIT_LANE_ROOT / "reddit_subreddit_registry_v0.json"
REGISTRY_SPEC = REDDIT_LANE_ROOT / "reddit_subreddit_registry_spec_v0.md"


def _row(subreddit: str, **overrides: object) -> dict[str, object]:
    row = {
        "subreddit": subreddit,
        "url": f"https://www.reddit.com/r/{subreddit}/",
        "status": "active",
        "status_observed_at": "2026-07-16",
        "created_utc_or_none": "2010-07-09",
        "title_or_none": subreddit.title(),
        "public_description_or_none": "desc",
        "posting_posture_or_none": None,
        "descriptive_observed_at": "2026-07-16",
        "descriptive_changes": [],
        "niche_paths": ["beauty/makeup"],
        "venue_roles": ["hub"],
        "discovery_state": "known_subreddit",
        "capture_state": "no_packet_recorded",
        "observations": [],
        "first_seen_at": "2026-07-16",
        "register_pointers": [],
        "source_pointers": [],
    }
    row.update(overrides)
    return row


def _legacy(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "reddit_subreddit_registry_v0.json"
    document = {
        "reddit_subreddit_registry": {
            "schema_version": "reddit_subreddit_registry_v0",
            "counts": {"subreddits_total": len(rows)},
            "subreddits": rows,
        }
    }
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def lake(tmp_path: Path) -> DataLakeRoot:
    return DataLakeRoot.for_test(tmp_path / "lake")


# --------------------------------------------------------------------------
# Vocabulary contract
# --------------------------------------------------------------------------


def test_vocabularies_match_the_git_spec_contract() -> None:
    """The writer's vocabulary may not silently diverge from the Git contract."""
    spec = REGISTRY_SPEC.read_text(encoding="utf-8")
    niche_block = spec.split("`niche_paths`: hierarchical slash paths")[1].split("One registry file")[0]
    role_block = spec.split("`venue_roles`: functional dimension")[1].split("Both vocabularies")[0]
    assert set(re.findall(r"`([a-z/_]+)`", niche_block)) == set(NICHE_PATHS)
    assert set(re.findall(r"`([a-z/_]+)`", role_block)) == set(VENUE_ROLES)


def test_capture_state_vocabulary_matches_spec() -> None:
    spec = REGISTRY_SPEC.read_text(encoding="utf-8")
    assert set(CAPTURE_STATE_RANK) <= set(re.findall(r"`([a-z_]+)`", spec))
    assert CAPTURE_STATE_RANK["thread_packets_recorded"] > CAPTURE_STATE_RANK["grid_packets_recorded"]


@pytest.mark.parametrize(
    "raw,expected",
    [("MakeupAddiction", "makeupaddiction"), ("/r/Beauty", "beauty"), ("r/fragrance/", "fragrance")],
)
def test_normalize_subreddit(raw: str, expected: str) -> None:
    assert normalize_subreddit(raw) == expected


@pytest.mark.parametrize("raw", ["", "  ", "has space", "../escape", "r//"])
def test_normalize_subreddit_rejects_non_names(raw: str) -> None:
    with pytest.raises(RedditSubredditRegistryLakeError):
        normalize_subreddit(raw)


# --------------------------------------------------------------------------
# Baseline migration
# --------------------------------------------------------------------------


def test_migration_dry_run_writes_nothing(lake: DataLakeRoot, tmp_path: Path) -> None:
    legacy = _legacy(tmp_path, [_row("alpha"), _row("beta")])
    result = migrate_legacy_registry(lake, registry_path=legacy, dry_run=True)
    assert result["status"] == "would_write"
    assert result["written"] is False
    assert result["subreddits_total"] == 2
    assert known_subreddits(lake) == []


def test_migration_writes_one_baseline_per_row_then_is_idempotent(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha"), _row("beta")])
    written = migrate_legacy_registry(lake, registry_path=legacy)
    assert written["status"] == "written" and written["written"] is True
    assert known_subreddits(lake) == ["alpha", "beta"]

    rerun = migrate_legacy_registry(lake, registry_path=legacy)
    assert rerun["status"] == "already_current"
    assert rerun["written"] is False


def test_migration_blocks_on_divergent_legacy_hash(lake: DataLakeRoot, tmp_path: Path) -> None:
    first = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=first)
    second = _legacy(tmp_path / "other", [_row("alpha", status="unverified")])
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        migrate_legacy_registry(lake, registry_path=second)
    assert excinfo.value.code == "baseline_legacy_hash_divergent"


def test_migration_blocks_on_partial_baseline_set(lake: DataLakeRoot, tmp_path: Path) -> None:
    partial = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=partial)
    # Same legacy hash is impossible with a different row set, so re-point at a
    # registry whose hash matches nothing already present but whose set is wider.
    wider = _legacy(tmp_path / "wider", [_row("alpha"), _row("beta")])
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        migrate_legacy_registry(lake, registry_path=wider)
    assert excinfo.value.code in {"baseline_partial", "baseline_legacy_hash_divergent"}


def test_fold_reproduces_legacy_rows_exactly(lake: DataLakeRoot, tmp_path: Path) -> None:
    rows = [
        _row(
            "alpha",
            capture_state="grid_packets_recorded",
            observations=[
                {
                    "observed_at": "2026-07-17",
                    "subscriber_count_or_none": "123",
                    "active_user_count_or_none": None,
                    "source_surface": "old_reddit_grid_packet",
                    "provenance_pointer": "F:/lake/raw/aaa/manifest.json",
                    "absent_reason_or_none": None,
                }
            ],
            register_pointers=["F:/lake/raw/aaa/manifest.json"],
        ),
        _row("beta"),
    ]
    legacy = _legacy(tmp_path, rows)
    migrate_legacy_registry(lake, registry_path=legacy)
    folded = load_current_registry(lake)
    parity = semantic_parity(legacy_registry_path=legacy, folded=folded)
    assert parity["parity"] is True, parity["mismatches"]
    assert parity["legacy_subreddits"] == parity["folded_subreddits"] == 2


def test_fold_refuses_deltas_without_a_genesis_record(lake: DataLakeRoot) -> None:
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "orphan")
    assert excinfo.value.code == "genesis_missing"


# --------------------------------------------------------------------------
# Observations
# --------------------------------------------------------------------------


def _observe(lake: DataLakeRoot, subreddit: str, *, pointer: str, observed_at: str, **kwargs):
    return append_grid_observation(
        lake,
        subreddit=subreddit,
        observed_at=observed_at,
        subscriber_count_or_none=kwargs.get("subscribers"),
        active_user_count_or_none=None,
        source_surface="old_reddit_grid_packet",
        provenance_pointer=pointer,
        absent_reason_or_none=kwargs.get("absent_reason"),
    )


def test_observation_carries_the_row_effects_the_packet_implies(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha", status="unverified", status_observed_at="2026-07-01")])
    migrate_legacy_registry(lake, registry_path=legacy)

    result = _observe(lake, "alpha", pointer="F:/lake/raw/bbb/manifest.json", observed_at="2026-07-17")
    assert result["written"] is True

    row = fold_subreddit(lake, "alpha")
    assert len(row["observations"]) == 1
    assert row["status"] == "active"
    assert row["status_observed_at"] == "2026-07-17"
    assert row["capture_state"] == "grid_packets_recorded"
    assert row["register_pointers"] == ["F:/lake/raw/bbb/manifest.json"]
    assert row["descriptive_changes"][-1]["field"] == "status"


def test_observation_dedupes_by_provenance_pointer(lake: DataLakeRoot, tmp_path: Path) -> None:
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    pointer = "F:/lake/raw/ccc/manifest.json"
    first = _observe(lake, "alpha", pointer=pointer, observed_at="2026-07-17")
    second = _observe(lake, "alpha", pointer=pointer, observed_at="2026-07-17")
    assert first["written"] is True
    assert second["status"] == "already_current" and second["written"] is False
    assert len(fold_subreddit(lake, "alpha")["observations"]) == 1


def test_observation_does_not_downgrade_thread_capture_state(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha", capture_state="thread_packets_recorded")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/ddd/manifest.json", observed_at="2026-07-17")
    assert fold_subreddit(lake, "alpha")["capture_state"] == "thread_packets_recorded"


def test_historical_grid_observation_does_not_false_downgrade_later_thread_state(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/ddd/manifest.json", observed_at="2026-07-17")
    append_roster_change(
        lake,
        subreddit="alpha",
        changes={"capture_state": "thread_packets_recorded"},
        actor="operator",
    )

    assert fold_subreddit(lake, "alpha")["capture_state"] == "thread_packets_recorded"


def test_older_observation_does_not_move_status_backwards(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha", status="active", status_observed_at="2026-07-17")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/eee/manifest.json", observed_at="2026-07-01")
    row = fold_subreddit(lake, "alpha")
    assert row["status_observed_at"] == "2026-07-17"
    assert len(row["observations"]) == 1


def test_observations_fold_in_deterministic_order(lake: DataLakeRoot, tmp_path: Path) -> None:
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/zzz/manifest.json", observed_at="2026-07-18")
    _observe(lake, "alpha", pointer="F:/lake/raw/aaa/manifest.json", observed_at="2026-07-17")
    observed = [entry["observed_at"] for entry in fold_subreddit(lake, "alpha")["observations"]]
    assert observed == ["2026-07-17", "2026-07-18"]


# --------------------------------------------------------------------------
# Roster changes
# --------------------------------------------------------------------------


def test_add_roster_change_is_its_own_genesis(lake: DataLakeRoot) -> None:
    added = append_roster_change(
        lake,
        subreddit="NewSub",
        change_kind="add",
        changes={"niche_paths": ["beauty/hair"], "discovery_state": "known_subreddit"},
        actor="operator",
    )
    assert added["written"] is True
    row = fold_subreddit(lake, "newsub")
    assert row["subreddit"] == "newsub"
    assert row["niche_paths"] == ["beauty/hair"]
    assert row["discovery_state"] == "known_subreddit"
    assert known_subreddits(lake) == ["newsub"]


def test_second_genesis_fails_closed(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    assert excinfo.value.code == "genesis_duplicate"


def test_update_without_genesis_fails_closed(lake: DataLakeRoot) -> None:
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(
            lake, subreddit="ghost", changes={"venue_roles": ["hub"]}, actor="operator"
        )
    assert excinfo.value.code == "genesis_missing"


def test_roster_updates_chain_by_predecessor(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    first = append_roster_change(
        lake, subreddit="newsub", changes={"venue_roles": ["hub"]}, actor="operator"
    )
    second = append_roster_change(
        lake, subreddit="newsub", changes={"venue_roles": ["hub", "deal"]}, actor="operator"
    )
    assert second["predecessor_record_id"] == first["record_id"]
    assert fold_subreddit(lake, "newsub")["venue_roles"] == ["deal", "hub"]


def _fork_record(lane: Path, *, predicate, record_id: str, changes: dict[str, object]) -> None:
    """Write a sibling record sharing an existing record's predecessor."""
    from data_lake.reddit_subreddit_registry import _content_hash

    source = next(
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(lane.iterdir())
        if predicate(json.loads(path.read_text(encoding="utf-8")))
    )
    source["record_id"] = record_id
    source["changes"] = changes
    source["content_hash"] = _content_hash(source)
    (lane / record_id).write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")


def test_ambiguous_roster_head_fails_closed(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    append_roster_change(lake, subreddit="newsub", changes={"venue_roles": ["hub"]}, actor="a")
    # A second delta sharing the first delta's predecessor forks the chain, so
    # no single head decides current state.
    lane = lake.lane_dir(subtree="derived", raw_anchor="newsub", lane=REDDIT_ROSTER_CHANGE_LANE)
    _fork_record(
        lane,
        predicate=lambda record: record.get("change_kind") != "add",
        record_id="rsr_forkedforkedforkedfork",
        changes={"venue_roles": ["deal"]},
    )
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "newsub")
    assert excinfo.value.code == "roster_head_ambiguous"


def test_duplicate_genesis_on_disk_fails_closed_at_fold(lake: DataLakeRoot) -> None:
    """The writer refuses a second add; the fold must refuse one that got there."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    lane = lake.lane_dir(subtree="derived", raw_anchor="newsub", lane=REDDIT_ROSTER_CHANGE_LANE)
    _fork_record(
        lane,
        predicate=lambda record: record.get("change_kind") == "add",
        record_id="rsr_duplicategenesisrecord",
        changes={"venue_roles": ["deal"]},
    )
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "newsub")
    assert excinfo.value.code == "genesis_duplicate"


def test_unknown_vocabulary_fails_closed(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(
            lake, subreddit="newsub", changes={"niche_paths": ["beauty/perfume"]}, actor="operator"
        )
    assert excinfo.value.code == "vocabulary_unknown"


def test_roster_change_may_not_write_grid_derived_state(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(
            lake, subreddit="newsub", changes={"register_pointers": ["x"]}, actor="operator"
        )
    assert excinfo.value.code == "roster_field_forbidden"


def test_roster_change_may_upgrade_capture_state_but_not_downgrade(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    append_roster_change(
        lake,
        subreddit="newsub",
        changes={"capture_state": "thread_packets_recorded"},
        actor="operator",
    )
    assert fold_subreddit(lake, "newsub")["capture_state"] == "thread_packets_recorded"
    append_roster_change(
        lake, subreddit="newsub", changes={"capture_state": "grid_packets_recorded"}, actor="operator"
    )
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "newsub")
    assert excinfo.value.code == "capture_state_downgrade"


# --------------------------------------------------------------------------
# Replay order independence
#
# The writer records row effects against the fold as it stood at write time,
# but the fold replays every roster change before every observation.  A record
# written later therefore replays earlier, so a replayed effect must not be
# applied as an absolute assignment.
# --------------------------------------------------------------------------


def test_thread_upgrade_survives_replay_of_an_earlier_observation(lake: DataLakeRoot) -> None:
    """A deep-dive upgrade written after a grid packet must still fold."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    _observe(lake, "newsub", pointer="F:/lake/raw/hhh/manifest.json", observed_at="2026-07-23")
    assert fold_subreddit(lake, "newsub")["capture_state"] == "grid_packets_recorded"

    append_roster_change(
        lake,
        subreddit="newsub",
        changes={"capture_state": "thread_packets_recorded"},
        actor="operator",
    )
    row = fold_subreddit(lake, "newsub")
    assert row["capture_state"] == "thread_packets_recorded"
    assert len(row["observations"]) == 1


def test_replayed_observation_does_not_revert_a_newer_roster_status(lake: DataLakeRoot) -> None:
    """An older observation must not walk a roster-authored status backwards."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    _observe(lake, "newsub", pointer="F:/lake/raw/iii/manifest.json", observed_at="2026-07-01")
    assert fold_subreddit(lake, "newsub")["status"] == "active"

    append_roster_change(
        lake,
        subreddit="newsub",
        changes={"status": "private", "status_observed_at": "2026-07-20"},
        actor="operator",
    )
    row = fold_subreddit(lake, "newsub")
    assert row["status"] == "private"
    assert row["status_observed_at"] == "2026-07-20"
    assert [entry["field"] for entry in row["descriptive_changes"]] == []


def test_observation_date_is_validated_before_first_status_effect(
    lake: DataLakeRoot,
) -> None:
    """A missing current date must not bypass validation of the incoming date."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        _observe(
            lake,
            "newsub",
            pointer="F:/lake/raw/invalid-date/manifest.json",
            observed_at="not-a-date",
        )
    assert excinfo.value.code == "status_date_invalid"


@pytest.mark.parametrize(
    ("effect_name", "effect_value", "expected_code"),
    [
        (
            "status",
            {"status": "private", "status_observed_at": "2026-07-01"},
            "observation_status_effect_invalid",
        ),
        (
            "status",
            {"status": "active", "status_observed_at": "1900-01-01"},
            "observation_status_effect_invalid",
        ),
        (
            "capture_state",
            "thread_packets_recorded",
            "observation_capture_state_effect_invalid",
        ),
    ],
)
def test_fold_refuses_noncanonical_grid_observation_effects(
    lake: DataLakeRoot,
    effect_name: str,
    effect_value: object,
    expected_code: str,
) -> None:
    """Content-hash-valid records still fail if their semantic effects are forged."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    _observe(
        lake,
        "newsub",
        pointer="F:/lake/raw/forged-effect/manifest.json",
        observed_at="2026-07-01",
    )
    lane = lake.lane_dir(
        subtree="derived",
        raw_anchor="newsub",
        lane=REDDIT_OBSERVATION_LANE,
    )
    record_path = next(iter(lane.iterdir()))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["row_effects"][effect_name] = effect_value
    from data_lake.reddit_subreddit_registry import _content_hash

    record["content_hash"] = _content_hash(record)
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "newsub")
    assert excinfo.value.code == expected_code


# --------------------------------------------------------------------------
# Integrity
# --------------------------------------------------------------------------


def test_tampered_record_fails_closed(lake: DataLakeRoot, tmp_path: Path) -> None:
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    lane = lake.lane_dir(subtree="derived", raw_anchor="alpha", lane=REDDIT_BASELINE_LANE)
    record_path = next(iter(lane.iterdir()))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["row"]["status"] = "banned"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "alpha")
    assert excinfo.value.code == "record_content_hash_mismatch"


def test_observation_anchored_under_another_subreddit_fails_closed(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha"), _row("beta")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "beta", pointer="F:/lake/raw/fff/manifest.json", observed_at="2026-07-17")
    lane = lake.lane_dir(subtree="derived", raw_anchor="beta", lane=REDDIT_OBSERVATION_LANE)
    record = json.loads(next(iter(lane.iterdir())).read_text(encoding="utf-8"))
    record["subreddit"] = "alpha"
    from data_lake.reddit_subreddit_registry import _content_hash

    record["content_hash"] = _content_hash(record)
    target = lake.lane_dir(subtree="derived", raw_anchor="beta", lane=REDDIT_OBSERVATION_LANE)
    (target / record["record_id"]).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        fold_subreddit(lake, "beta")
    assert excinfo.value.code == "identity_mismatch"


# --------------------------------------------------------------------------
# Dogfood: the real committed registry round-trips
# --------------------------------------------------------------------------


def test_live_committed_registry_folds_with_exact_parity(lake: DataLakeRoot) -> None:
    """The 35-row committed registry must survive migrate -> fold unchanged."""
    result = migrate_legacy_registry(lake, registry_path=LIVE_REGISTRY)
    assert result["written"] is True
    assert result["subreddits_total"] == 35

    folded = load_current_registry(lake)
    parity = semantic_parity(legacy_registry_path=LIVE_REGISTRY, folded=folded)
    assert parity["parity"] is True, parity["mismatches"][:5]
    assert parity["legacy_subreddits"] == parity["folded_subreddits"] == 35

    document = json.loads(LIVE_REGISTRY.read_text(encoding="utf-8"))
    legacy_observations = sum(
        len(row.get("observations", []))
        for row in document["reddit_subreddit_registry"]["subreddits"]
    )
    assert result["observations_total"] == legacy_observations


# --------------------------------------------------------------------------
# Delegated review findings RSR-01..RSR-04
# --------------------------------------------------------------------------


def test_rsr01_first_update_chains_to_the_add_genesis(lake: DataLakeRoot) -> None:
    """The chain is self-anchoring: it roots at the add, not at an implicit None."""
    added = append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    first = append_roster_change(
        lake, subreddit="newsub", changes={"venue_roles": ["hub"]}, actor="operator"
    )
    assert first["predecessor_record_id"] == added["record_id"]
    assert fold_subreddit(lake, "newsub")["venue_roles"] == ["hub"]


def test_rsr01_baseline_genesis_chain_still_roots_at_none(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    """A migrated subreddit has no roster genesis record, so its root stays None."""
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    first = append_roster_change(
        lake, subreddit="alpha", changes={"venue_roles": ["deal"]}, actor="operator"
    )
    assert first["predecessor_record_id"] is None
    assert fold_subreddit(lake, "alpha")["venue_roles"] == ["deal"]


def test_rsr02_same_pointer_different_values_fails_closed(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    """The writer must not be laxer than the fold that has to reconcile it."""
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    pointer = "F:/lake/raw/ggg/manifest.json"
    _observe(lake, "alpha", pointer=pointer, observed_at="2026-07-17", subscribers="100")

    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        _observe(lake, "alpha", pointer=pointer, observed_at="2026-07-17", subscribers="999")
    assert excinfo.value.code == "observation_provenance_conflict"
    assert len(fold_subreddit(lake, "alpha")["observations"]) == 1


def test_rsr02_exact_replay_is_still_idempotent(lake: DataLakeRoot, tmp_path: Path) -> None:
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    pointer = "F:/lake/raw/hhh/manifest.json"
    kwargs = dict(pointer=pointer, observed_at="2026-07-17", subscribers="100")
    _observe(lake, "alpha", **kwargs)
    replay = _observe(lake, "alpha", **kwargs)
    assert replay["status"] == "already_current" and replay["written"] is False


@pytest.mark.parametrize("bad_status", ["banana", "ACTIVE", "deleted", ""])
def test_rsr03_invalid_status_fails_closed(lake: DataLakeRoot, bad_status: str) -> None:
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(
            lake, subreddit="newsub", changes={"status": bad_status}, actor="operator"
        )
    assert excinfo.value.code == "status_unknown"


def test_rsr03_spec_status_values_are_accepted(lake: DataLakeRoot) -> None:
    spec = REGISTRY_SPEC.read_text(encoding="utf-8")
    block = spec.split("Identity and liveness")[1].split("`status_observed_at`")[0]
    assert set(re.findall(r"`([a-z]+)`", block)) >= set(STATUS_VALUES)
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    for value in sorted(STATUS_VALUES):
        append_roster_change(
            lake, subreddit="newsub", changes={"status": value}, actor="operator"
        )
    assert fold_subreddit(lake, "newsub")["status"] in STATUS_VALUES


def test_rsr03_url_is_derived_and_not_roster_writable(lake: DataLakeRoot) -> None:
    """URL follows subreddit identity; letting a roster change override it drifts identity."""
    append_roster_change(lake, subreddit="newsub", change_kind="add", actor="operator")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_roster_change(
            lake,
            subreddit="newsub",
            changes={"url": "https://www.reddit.com/r/somewhere_else/"},
            actor="operator",
        )
    assert excinfo.value.code == "roster_field_forbidden"
    assert fold_subreddit(lake, "newsub")["url"] == "https://www.reddit.com/r/newsub/"


def test_rsr04_superseded_writer_refuses_the_frozen_registry(tmp_path: Path) -> None:
    """A docstring is not a guard: the Git-mutating path must fail closed."""
    from capture_spine.reddit_subreddit_grid.materializer import (
        FROZEN_COMMITTED_REGISTRY_PATH,
        RegistryRefreshError,
        refresh_registry_from_grid_packets,
    )

    assert FROZEN_COMMITTED_REGISTRY_PATH.is_file(), "guard must point at the real committed file"
    frozen_before = FROZEN_COMMITTED_REGISTRY_PATH.read_bytes()
    with pytest.raises(RegistryRefreshError) as excinfo:
        refresh_registry_from_grid_packets(
            registry_path=FROZEN_COMMITTED_REGISTRY_PATH,
            packet_paths=[tmp_path / "irrelevant"],
        )
    assert excinfo.value.code == "frozen_registry_write_refused"
    assert FROZEN_COMMITTED_REGISTRY_PATH.read_bytes() == frozen_before


def test_inflight_write_temp_is_skipped_by_the_fold(lake: DataLakeRoot) -> None:
    """A concurrent writer's staged temp must not be folded as a record.

    DataLakeRoot._atomic_create stages every record as .<name>.<ulid>.tmp beside
    its target, and iterdir returns dot-prefixed names, so an unfiltered fold
    reads a half-written record and fails on shape or content hash.
    """
    append_roster_change(lake, subreddit="probe", change_kind="add", actor="operator")
    lane = lake.lane_dir(subtree="derived", raw_anchor="probe", lane=REDDIT_ROSTER_CHANGE_LANE)
    staged = lane / ".rsr_stagedrecord.01KYINFLIGHTULID00000000.tmp"
    staged.write_bytes(b'{"schema_version": "reddit_subreddit_roster_change_v1", "par')

    row = fold_subreddit(lake, "probe")
    assert row["subreddit"] == "probe"
    assert staged.exists(), "the fold must skip the temp, not delete it"


# --------------------------------------------------------------------------
# Reach observations (agent-read: SERP bands, community panel)
# --------------------------------------------------------------------------


def _reach(lake: DataLakeRoot, subreddit: str, *, pointer: str, **kwargs):
    return append_reach_observation(
        lake,
        subreddit=subreddit,
        observed_at=kwargs.get("observed_at", "2026-07-22"),
        source_surface=kwargs.get("surface", "agent_browser_serp_read"),
        provenance_pointer=pointer,
        subscriber_count_or_none=kwargs.get("subscribers"),
        weekly_visitor_count_or_none=kwargs.get("visitors"),
        weekly_contribution_count_or_none=kwargs.get("contributions"),
        absent_reason_or_none=kwargs.get("absent_reason"),
    )


def test_reach_observation_folds_with_band_and_panel_fields(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="reachy", change_kind="add", actor="agent")
    before = fold_subreddit(lake, "reachy")

    result = _reach(
        lake,
        "reachy",
        pointer="agent_browser_session_2026-07-22_serp_q=r/reachy",
        subscribers="135.3K+",
        visitors="702000",
        contributions="7600",
    )
    assert result["written"] is True

    row = fold_subreddit(lake, "reachy")
    (observation,) = row["observations"]
    assert observation["subscriber_count_or_none"] == "135.3K+"
    assert observation["weekly_visitor_count_or_none"] == "702000"
    assert observation["weekly_contribution_count_or_none"] == "7600"
    assert observation["source_surface"] == "agent_browser_serp_read"
    # A browser-read band proves nothing about liveness and advances no packet
    # state: the row keeps its genesis status and capture_state untouched.
    assert row["status"] == before["status"]
    assert row["status_observed_at"] == before["status_observed_at"]
    assert row["capture_state"] == before["capture_state"]
    assert observation["provenance_pointer"] in row["register_pointers"]


def test_reach_observation_refuses_to_record_nothing(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="reachy", change_kind="add", actor="agent")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        _reach(lake, "reachy", pointer="agent_browser_session_x")
    assert excinfo.value.code == "observation_empty"


def test_reach_observation_rejects_non_iso_observed_at(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="reachy", change_kind="add", actor="agent")
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        _reach(lake, "reachy", pointer="p", subscribers="1K+", observed_at="July 22")
    assert excinfo.value.code == "observed_at_invalid"


def test_reach_observation_same_pointer_conflicts_or_replays(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="reachy", change_kind="add", actor="agent")
    pointer = "agent_browser_session_2026-07-22_serp_q=r/reachy"
    first = _reach(lake, "reachy", pointer=pointer, subscribers="1M+")
    replay = _reach(lake, "reachy", pointer=pointer, subscribers="1M+")
    assert first["written"] is True
    assert replay["status"] == "already_current" and replay["written"] is False
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        _reach(lake, "reachy", pointer=pointer, subscribers="2M+")
    assert excinfo.value.code == "observation_provenance_conflict"


def test_reach_and_grid_observations_coexist_in_one_fold(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    """Old-shape grid observations (no weekly keys) and new-shape reach
    observations fold side by side; the mixed shapes must not collide."""
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/eee/manifest.json", observed_at="2026-07-21")
    _reach(lake, "alpha", pointer="agent_browser_session_serp", subscribers="2.4M+")

    row = fold_subreddit(lake, "alpha")
    assert len(row["observations"]) == 2
    grid = next(o for o in row["observations"] if o["source_surface"] == "old_reddit_grid_packet")
    reach = next(o for o in row["observations"] if o["source_surface"] == "agent_browser_serp_read")
    assert "weekly_visitor_count_or_none" not in grid
    assert reach["weekly_visitor_count_or_none"] is None


def test_rdr03_old_shape_observation_replay_is_not_a_conflict(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    """The weekly fields were added nullable with no migration: a grid
    observation recorded without them must compare equal to a reach replay of
    the same pointer carrying explicit nulls, not raise a false conflict."""
    legacy = _legacy(tmp_path, [_row("alpha")])
    migrate_legacy_registry(lake, registry_path=legacy)
    pointer = "F:/lake/raw/fff/manifest.json"
    _observe(
        lake, "alpha", pointer=pointer, observed_at="2026-07-21", subscribers="123"
    )

    replay = append_reach_observation(
        lake,
        subreddit="alpha",
        observed_at="2026-07-21",
        source_surface="old_reddit_grid_packet",
        provenance_pointer=pointer,
        subscriber_count_or_none="123",
        weekly_visitor_count_or_none=None,
        weekly_contribution_count_or_none=None,
    )
    assert replay["status"] == "already_current"
    assert replay["written"] is False
    # And a genuinely different value on the same pointer still conflicts.
    with pytest.raises(RedditSubredditRegistryLakeError) as excinfo:
        append_reach_observation(
            lake,
            subreddit="alpha",
            observed_at="2026-07-21",
            source_surface="old_reddit_grid_packet",
            provenance_pointer=pointer,
            subscriber_count_or_none="999",
        )
    assert excinfo.value.code == "observation_provenance_conflict"


# --------------------------------------------------------------------------
# Retire: stop capturing without deleting history
# --------------------------------------------------------------------------


def test_retired_row_leaves_census_intact_but_exits_capture_roster(
    lake: DataLakeRoot, tmp_path: Path
) -> None:
    legacy = _legacy(tmp_path, [_row("alpha"), _row("beta")])
    migrate_legacy_registry(lake, registry_path=legacy)
    _observe(lake, "alpha", pointer="F:/lake/raw/aaa/manifest.json", observed_at="2026-07-20")

    append_roster_change(
        lake, subreddit="alpha", change_kind="update",
        changes={"discovery_state": "retired"}, actor="operator",
        note_or_none="pruned: professional sub, low consumer demand signal",
    )

    # Census keeps it; capture roster drops it.
    assert known_subreddits(lake) == ["alpha", "beta"]
    assert capture_roster(lake) == ["beta"]

    # History survives the retirement -- the whole point of append-only.
    row = fold_subreddit(lake, "alpha")
    assert row["discovery_state"] == "retired"
    assert len(row["observations"]) == 1
    assert row["capture_state"] == "grid_packets_recorded"


def test_retirement_is_reversible(lake: DataLakeRoot) -> None:
    append_roster_change(lake, subreddit="gamma", change_kind="add", actor="operator")
    append_roster_change(
        lake, subreddit="gamma", change_kind="update",
        changes={"discovery_state": "retired"}, actor="operator",
    )
    assert capture_roster(lake) == []
    append_roster_change(
        lake, subreddit="gamma", change_kind="update",
        changes={"discovery_state": "known_subreddit"}, actor="operator",
    )
    assert capture_roster(lake) == ["gamma"]


def test_retired_is_a_roster_state_not_a_reddit_status(lake: DataLakeRoot) -> None:
    """`retired` (chosen) and `status` (observed) are independent axes: a
    retired subreddit stays 'active' on Reddit unless observed otherwise."""
    append_roster_change(lake, subreddit="delta", change_kind="add", actor="operator")
    append_roster_change(
        lake, subreddit="delta", change_kind="update",
        changes={"discovery_state": "retired", "status": "active"}, actor="operator",
    )
    row = fold_subreddit(lake, "delta")
    assert row["discovery_state"] == "retired"
    assert row["status"] == "active"
