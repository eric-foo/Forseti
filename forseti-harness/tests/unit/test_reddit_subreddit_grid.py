from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from capture_spine.reddit_subreddit_grid import (
    RegistryRefreshError,
    project_old_reddit_grid_html,
    read_grid_packet,
    refresh_lake_registry_from_grid_packets,
    refresh_registry_from_grid_packets,
)
from capture_spine.reddit_subreddit_grid.grid_projection import (
    GRID_PROJECTION_PARSER_VERSION,
    build_grid_content_record,
    grid_view_from_record,
    grid_view_projection_anomaly,
)
from runners import run_reddit_grid_capture as grid_runner
from runners import run_source_capture_http_packet as http_packet_runner
from runners.run_reddit_grid_capture import (
    build_grid_listing_url,
    run_reddit_grid_capture,
)
from data_lake.reddit_subreddit_registry import (
    fold_subreddit,
    known_subreddits,
    migrate_legacy_registry,
)
from data_lake.root import DataLakeRoot
from source_capture.adapters.direct_http import DirectHttpCaptureSuccess
from source_capture.content_extraction import ContentExtractionSpec


GRID_HTML = """
<html><body>
<div class="titlebox">
  <span class="subscribers"><span class="number">7,491,826</span> members</span>
  <p class="users-online"><span class="number">12,345</span> online</p>
</div>
<div id="siteTable">
  <div class="thing link" data-permalink="/r/makeupaddiction/comments/aaa111/first_post/"
       data-subreddit="MakeupAddiction" data-score="4821" data-comments-count="382">
    <a class="title" href="/r/makeupaddiction/comments/aaa111/first_post/">First look post</a>
  </div>
  <div class="thing link" data-subreddit="MakeupAddiction">
    <a class="title" href="https://old.reddit.com/r/makeupaddiction/comments/bbb222/second_post/">Second post</a>
    <div class="score unvoted">1,204</div>
    <a class="comments" href="/r/makeupaddiction/comments/bbb222/second_post/">97 comments</a>
  </div>
  <div class="thing link promoted" data-permalink="/r/makeupaddiction/comments/ccc333/promo/"
       data-score="12" data-comments-count="1">
    <a class="title" href="/r/makeupaddiction/comments/ccc333/promo/">Sponsored thing</a>
  </div>
  <div class="thing link" data-permalink="/r/makeupaddiction/comments/aaa111/first_post/"
       data-score="4821" data-comments-count="382">
    <a class="title" href="/r/makeupaddiction/comments/aaa111/first_post/">Duplicate</a>
  </div>
</div>
</body></html>
"""


def _registry(path: Path) -> Path:
    registry = path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "reddit_subreddit_registry": {
                    "schema_version": "reddit_subreddit_registry_v0",
                    "counts": {
                        "subreddits_total": 1,
                        "by_status": {"unverified": 1},
                    },
                    "subreddits": [
                        {
                            "subreddit": "makeupaddiction",
                            "url": "https://www.reddit.com/r/makeupaddiction/",
                            "status": "unverified",
                            "status_observed_at": "2026-07-16",
                            "capture_state": "no_packet_recorded",
                            "observations": [],
                            "register_pointers": [],
                        }
                    ],
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return registry


def _raw_grid_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: int = 200,
    url: str = "https://old.reddit.com/r/makeupaddiction/top/?t=day",
) -> Path:

    def fake_fetch(**_: object) -> DirectHttpCaptureSuccess:
        return DirectHttpCaptureSuccess(
            requested_url=url,
            final_url=url,
            status=status,
            reason="OK" if status == 200 else "Not Found",
            metadata={
                "capture_timestamp": "2026-07-17T05:00:00Z",
                "requested_url": url,
                "final_url": url,
                "status": status,
            },
            body=GRID_HTML.encode(),
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(http_packet_runner, "fetch_direct_http_capture", fake_fetch)
    packet_dir = tmp_path / f"packet_{status}"
    exit_code, _ = http_packet_runner.run_source_capture_http_packet(
        url=url,
        source_family="reddit_subreddit_grid",
        source_surface="old_reddit_direct_http",
        decision_question="test grid packet",
        output_directory=packet_dir,
        capture_context="test",
        operator_category="test_operator",
        capture_mode=http_packet_runner.CaptureModeCategory.STRUCTURED_ACCESS,
        session_id=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=5,
        max_bytes=1_000_000,
    )
    assert exit_code == 0
    return packet_dir


def test_grid_projection_preserves_titlebox_threads_nested_text_and_dedupes() -> None:
    nested = GRID_HTML.replace("First look post", "First <em>look</em> post")
    view = project_old_reddit_grid_html(
        html_text=nested,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )

    assert view.visible_subscriber_count_or_none == "7,491,826"
    assert view.visible_active_user_count_or_none == "12,345"
    assert len(view.thread_rows) == 3
    first, second, promoted = view.thread_rows
    assert first.visible_title_or_none == "First look post"
    assert first.visible_score_or_none == "4821"
    assert first.visible_comment_count_or_none == "382"
    assert second.visible_score_or_none == "1,204"
    assert second.visible_comment_count_or_none == "97"
    assert promoted.promoted


def test_grid_projection_reports_absent_volume_and_round_trips_content() -> None:
    empty = project_old_reddit_grid_html(
        html_text="<html><body><div id='siteTable'></div></body></html>",
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )
    assert empty.visible_subscriber_count_or_none is None
    assert (
        empty.visible_volume_signal_absent_reason_or_none
        == "visible_volume_not_present_on_declared_surface"
    )

    record = build_grid_content_record(
        html_text=GRID_HTML,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )
    assert record["parser_version"] == GRID_PROJECTION_PARSER_VERSION
    assert grid_view_from_record(record) == project_old_reddit_grid_html(
        html_text=GRID_HTML,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )


def test_materializer_updates_once_and_dedupes_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _registry(tmp_path)
    packet = _raw_grid_packet(tmp_path, monkeypatch)

    first = refresh_registry_from_grid_packets(
        registry_path=registry, packet_paths=[packet]
    )
    assert first.refreshed_subreddits == ["makeupaddiction"]
    assert first.status_changes == ["makeupaddiction"]

    second = refresh_registry_from_grid_packets(
        registry_path=registry, packet_paths=[packet]
    )
    assert second.refreshed_subreddits == []
    assert second.duplicate_observation_skips == ["makeupaddiction"]
    row = json.loads(registry.read_text(encoding="utf-8"))[
        "reddit_subreddit_registry"
    ]["subreddits"][0]
    assert row["status"] == "active"
    assert row["observations"][0]["subscriber_count_or_none"] == "7491826"
    assert len(row["observations"]) == 1


def test_materializer_rejects_off_domain_locator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = _raw_grid_packet(tmp_path, monkeypatch)
    manifest_path = packet / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_locator"]["value"] = "https://example.com/r/x/top/"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(RegistryRefreshError) as exc:
        read_grid_packet(packet_or_manifest_path=packet)
    assert exc.value.code == "locator_unparseable"


def test_materializer_rejects_preserved_body_outside_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = _raw_grid_packet(tmp_path, monkeypatch)
    manifest_path = packet / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    body = next(
        item
        for item in manifest["preserved_files"]
        if item["relative_packet_path"].endswith("http_response_body.bin")
    )
    original = packet / body["relative_packet_path"]
    escaped = tmp_path / "escaped.bin"
    shutil.copyfile(original, escaped)
    body["relative_packet_path"] = "../escaped.bin"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(RegistryRefreshError) as exc:
        read_grid_packet(packet_or_manifest_path=packet)
    assert exc.value.code == "preserved_file_unresolved"


def test_materializer_rejects_unsuccessful_raw_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = _raw_grid_packet(tmp_path, monkeypatch, status=404)
    with pytest.raises(RegistryRefreshError) as exc:
        read_grid_packet(packet_or_manifest_path=packet)
    assert exc.value.code == "grid_access_unsuccessful"


def test_grid_listing_url_and_runner_content_extraction_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert build_grid_listing_url(
        subreddit="r/fragrance", listing="rising", time_window=None
    ) == "https://old.reddit.com/r/fragrance/rising/"
    assert build_grid_listing_url(
        subreddit="MakeupAddiction", listing="top", time_window="day"
    ) == "https://old.reddit.com/r/makeupaddiction/top/?t=day"
    with pytest.raises(ValueError, match="top listing"):
        build_grid_listing_url(
            subreddit="fragrance", listing="hot", time_window="day"
        )

    calls: list[dict[str, object]] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(kwargs)
        return 0, str(kwargs["output_directory"])

    monkeypatch.setattr(grid_runner, "run_source_capture_http_packet", fake_capture)
    monkeypatch.setattr(grid_runner.time, "sleep", lambda _: None)
    code, summary_path = run_reddit_grid_capture(
        subreddits=["MakeupAddiction"],
        listing="top",
        time_window="day",
        output_root=tmp_path / "run",
        decision_question="test",
        delay_seconds=0,
    )
    assert code == 0
    spec = calls[0]["content_extraction"]
    assert isinstance(spec, ContentExtractionSpec)
    assert spec.requested_retention_mode == "content"
    assert spec.extractor_version == GRID_PROJECTION_PARSER_VERSION
    assert calls[0]["url"] == (
        "https://old.reddit.com/r/makeupaddiction/top/?t=day"
    )
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    assert summary["capture_success_count"] == 1
    assert summary["requested_retention_mode"] == "content"


def test_lake_materializer_appends_once_and_dedupes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The repointed writer appends to lake authority and never mutates a file."""
    registry = _registry(tmp_path)
    packet = _raw_grid_packet(tmp_path, monkeypatch)
    frozen = registry.read_bytes()
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)

    first = refresh_lake_registry_from_grid_packets(data_root=lake, packet_paths=[packet])
    assert first.refreshed_subreddits == ["makeupaddiction"]
    assert first.records_written == 1

    second = refresh_lake_registry_from_grid_packets(data_root=lake, packet_paths=[packet])
    assert second.refreshed_subreddits == []
    assert second.duplicate_observation_skips == ["makeupaddiction"]
    assert second.records_written == 0

    row = fold_subreddit(lake, "makeupaddiction")
    assert row["status"] == "active"
    assert row["capture_state"] == "grid_packets_recorded"
    assert len(row["observations"]) == 1
    assert row["observations"][0]["subscriber_count_or_none"] == "7491826"
    assert row["register_pointers"] == [row["observations"][0]["provenance_pointer"]]
    assert registry.read_bytes() == frozen


def test_lake_materializer_reports_unknown_subreddit_without_adding_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = _raw_grid_packet(tmp_path, monkeypatch)
    lake = DataLakeRoot.for_test(tmp_path / "lake")

    outcome = refresh_lake_registry_from_grid_packets(data_root=lake, packet_paths=[packet])
    assert outcome.unknown_subreddits == ["makeupaddiction"]
    assert outcome.records_written == 0
    assert known_subreddits(lake) == []


def test_lake_materializer_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _registry(tmp_path)
    packet = _raw_grid_packet(tmp_path, monkeypatch)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)

    outcome = refresh_lake_registry_from_grid_packets(
        data_root=lake, packet_paths=[packet], dry_run=True
    )
    assert outcome.refreshed_subreddits == ["makeupaddiction"]
    assert outcome.records_written == 0
    assert fold_subreddit(lake, "makeupaddiction")["observations"] == []


# --------------------------------------------------------------------------
# Projection v2: timestamp / stickied / flair / venue created (real markup)
# --------------------------------------------------------------------------

V2_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "reddit_subreddit_grid"
    / "skincareaddiction_top_week_v2.html"
)


def test_projection_v2_extracts_new_fields_from_real_markup() -> None:
    """Fixture is cut verbatim from a SkincareAddiction top/week page where
    flairs are confirmed present -- zero-flair extraction fails here instead of
    passing silently (the spec's flair caveat)."""
    view = project_old_reddit_grid_html(
        html_text=V2_FIXTURE.read_text(encoding="utf-8"),
        subreddit="SkincareAddiction",
        listing_url="https://old.reddit.com/r/SkincareAddiction/top/?sort=top&t=week&limit=100",
    )
    assert view.created_utc_or_none == "2012-01-05T03:08:14+00:00"
    rows = view.thread_rows
    assert len(rows) == 3
    assert all(row.timestamp_utc_ms_or_none for row in rows)
    assert all(row.timestamp_utc_ms_or_none.isdigit() for row in rows)
    flairs = [row.flair_or_none for row in rows]
    assert flairs.count(None) == 0, "flaired page must yield flairs, not silent nulls"
    assert "Acne" in flairs and "PSA" in flairs
    assert [row.stickied for row in rows] == [True, False, False]
    # v2 keeps the v1 fields working on the same real markup.
    assert rows[1].visible_score_or_none == "748"
    assert rows[1].visible_comment_count_or_none == "189"


def test_projection_v2_synthetic_page_defaults_new_fields() -> None:
    """A page without timestamps/flairs/age still projects; the new fields
    default rather than fail (30PlusSkinCare genuinely carries no flairs)."""
    view = project_old_reddit_grid_html(
        html_text=GRID_HTML,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/",
    )
    assert view.created_utc_or_none is None
    assert all(row.timestamp_utc_ms_or_none is None for row in view.thread_rows)
    assert all(row.flair_or_none is None for row in view.thread_rows)
    assert all(row.stickied is False for row in view.thread_rows)


def test_v1_content_record_still_reconstructs_without_v2_keys() -> None:
    """Content packets written under parser v1 lack the v2 keys; the read path
    must default them, not crash the materializer on old packets."""
    record = {
        "record_kind": "reddit_subreddit_grid_view_v0",
        "parser_version": "1",
        "grid_view": {
            "subreddit": "alpha",
            "listing_url": "https://old.reddit.com/r/alpha/",
            "visible_subscriber_count_or_none": None,
            "visible_active_user_count_or_none": None,
            "visible_volume_signal_absent_reason_or_none": "visible_volume_not_present_on_declared_surface",
            "thread_rows": [
                {
                    "thread_url": "https://old.reddit.com/r/alpha/comments/x1/post/",
                    "subreddit": "alpha",
                    "visible_title_or_none": "post",
                    "visible_score_or_none": "5",
                    "visible_comment_count_or_none": "2",
                    "promoted": False,
                }
            ],
        },
    }
    view = grid_view_from_record(record)
    assert view.created_utc_or_none is None
    (row,) = view.thread_rows
    assert row.timestamp_utc_ms_or_none is None
    assert row.stickied is False
    assert row.flair_or_none is None


# --------------------------------------------------------------------------
# Weekly demand radar: listing limit, retention rules, surface stamping
# --------------------------------------------------------------------------


def test_listing_url_supports_limit_and_validates_range() -> None:
    assert build_grid_listing_url(
        subreddit="alpha", listing="top", time_window="week", limit=100
    ) == "https://old.reddit.com/r/alpha/top/?t=week&limit=100"
    assert build_grid_listing_url(
        subreddit="alpha", listing="rising", time_window=None, limit=50
    ) == "https://old.reddit.com/r/alpha/rising/?limit=50"
    with pytest.raises(ValueError, match="between 1 and 100"):
        build_grid_listing_url(subreddit="alpha", listing="top", time_window="week", limit=101)


def test_projection_anomaly_predicate() -> None:
    def record(rows: list[dict]) -> dict:
        return {"grid_view": {"thread_rows": rows}}

    assert grid_runner.check_grid_projection_anomaly(record([])) == "no_thread_rows"
    assert (
        grid_runner.check_grid_projection_anomaly(
            record([{"timestamp_utc_ms_or_none": None}, {"timestamp_utc_ms_or_none": None}])
        )
        == "no_timestamps"
    )
    assert (
        grid_runner.check_grid_projection_anomaly(
            record([{"timestamp_utc_ms_or_none": "1784658368000"}, {"timestamp_utc_ms_or_none": None}])
        )
        is None
    )


def test_rotating_raw_sample_is_deterministic_within_a_week(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Content-mode multi-sub passes send exactly one rotating sub as raw; a
    re-run in the same ISO week picks the same sub (resume-safe)."""
    calls: list[dict[str, object]] = []

    def fake_capture(**kwargs: object) -> tuple[int, str]:
        calls.append(kwargs)
        return 0, "packet"

    monkeypatch.setattr(grid_runner, "run_source_capture_http_packet", fake_capture)
    monkeypatch.setattr(grid_runner.time, "sleep", lambda _: None)

    def run(root: Path) -> dict[str, str]:
        calls.clear()
        code, summary_path = run_reddit_grid_capture(
            subreddits=["alpha", "beta", "gamma"],
            listing="top",
            time_window="week",
            limit=100,
            output_root=root,
            decision_question="test",
            delay_seconds=0,
        )
        assert code == 0
        summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
        modes = {
            call["url"]: call["content_extraction"].requested_retention_mode
            for call in calls
        }
        return {"sample": summary["raw_sample_subreddit"], "modes": modes}

    first = run(tmp_path / "one")
    second = run(tmp_path / "two")
    assert first["sample"] in {"alpha", "beta", "gamma"}
    assert first["sample"] == second["sample"]
    raw_modes = [mode for mode in first["modes"].values() if mode == "raw"]
    assert len(raw_modes) == 1


def test_single_sub_content_pass_keeps_no_rotating_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        grid_runner, "run_source_capture_http_packet",
        lambda **kwargs: (calls.append(kwargs), (0, "packet"))[1],
    )
    monkeypatch.setattr(grid_runner.time, "sleep", lambda _: None)
    code, summary_path = run_reddit_grid_capture(
        subreddits=["alpha"],
        listing="hot",
        time_window=None,
        output_root=tmp_path / "run",
        decision_question="test",
        delay_seconds=0,
    )
    assert code == 0
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    assert summary["raw_sample_subreddit"] is None
    assert calls[0]["content_extraction"].requested_retention_mode == "content"


def test_lake_refresh_stamps_top_week_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A top/?t=week grid packet ledgers as old_reddit_top_week_packet so the
    weekly consolidated pass stays distinguishable from a live grid pass."""
    registry = _registry(tmp_path)
    packet = _raw_grid_packet(
        tmp_path,
        monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
    )
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)

    outcome = refresh_lake_registry_from_grid_packets(data_root=lake, packet_paths=[packet])
    assert outcome.refreshed_subreddits == ["makeupaddiction"]
    row = fold_subreddit(lake, "makeupaddiction")
    (observation,) = row["observations"]
    assert observation["source_surface"] == "old_reddit_top_week_packet"
    assert row["capture_state"] == "grid_packets_recorded"


# --------------------------------------------------------------------------
# Weekly demand read (spec section E)
# --------------------------------------------------------------------------

WEEKLY_HTML = """
<html><body>
<div class="titlebox">
  <div class="bottom"><span class="age">a community for
    <time datetime="2015-03-03T19:26:01+00:00">11 years</time></span></div>
</div>
<div id="siteTable">
  <div class="thing link stickied" data-permalink="/r/makeupaddiction/comments/st1/pinned/"
       data-score="5" data-comments-count="80" data-timestamp="1751000000000">
    <a class="title" href="/r/makeupaddiction/comments/st1/pinned/">Pinned megathread</a>
  </div>
  <div class="thing link" data-permalink="/r/makeupaddiction/comments/pr1/problem/"
       data-score="10" data-comments-count="100" data-timestamp="1784600000000">
    <a class="title" href="/r/makeupaddiction/comments/pr1/problem/">Nothing works, help</a>
    <span class="linkflairlabel " title="Help">Help</span>
  </div>
  <div class="thing link" data-permalink="/r/makeupaddiction/comments/br1/broadcast/"
       data-score="900" data-comments-count="40" data-timestamp="1784610000000">
    <a class="title" href="/r/makeupaddiction/comments/br1/broadcast/">Look at my result</a>
  </div>
</div>
</body></html>
"""


def _lake_grid_packet(
    lake: DataLakeRoot,
    monkeypatch: pytest.MonkeyPatch,
    *,
    url: str,
    html: str = WEEKLY_HTML,
    capture_timestamp: str = "2026-07-17T05:00:00Z",
) -> None:
    def fake_fetch(**_: object) -> DirectHttpCaptureSuccess:
        return DirectHttpCaptureSuccess(
            requested_url=url,
            final_url=url,
            status=200,
            reason="OK",
            metadata={
                "capture_timestamp": capture_timestamp,
                "requested_url": url,
                "final_url": url,
                "status": 200,
            },
            body=html.encode(),
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(http_packet_runner, "fetch_direct_http_capture", fake_fetch)
    exit_code, _ = http_packet_runner.run_source_capture_http_packet(
        url=url,
        source_family="reddit_subreddit_grid",
        source_surface="old_reddit_direct_http",
        decision_question="test weekly packet",
        output_directory=None,
        data_root=lake,
        capture_context="test",
        operator_category="test_operator",
        capture_mode=http_packet_runner.CaptureModeCategory.STRUCTURED_ACCESS,
        session_id=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=5,
        max_bytes=1_000_000,
    )
    assert exit_code == 0


def test_weekly_demand_read_gates_and_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import run_weekly_demand_read

    registry = _registry(tmp_path)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
    )
    # A same-family hot packet must not enter the weekly read.
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/hot/",
    )

    payload = run_weekly_demand_read(data_root=lake, as_of=dt.date(2026, 7, 17))

    assert payload["subs_read"] == 1
    assert payload["subs_missing_weekly_packet"] == []
    (health,) = payload["sub_health"]
    # Sticky excluded: totals cover the two live rows only.
    assert health["posts"] == 2
    assert health["weekly_score"] == 910
    assert health["weekly_comments"] == 140
    assert health["page1_score_floor"] == 10
    assert health["created_utc_or_none"] == "2015-03-03T19:26:01+00:00"
    assert payload["page_overflow_tripwire"] == []

    # Top half by comments selects the problem; the lower-half concrete outcome
    # title is rescued. The stickied megathread remains excluded.
    problem, outcome = payload["candidates"]
    assert problem["title_or_none"] == "Nothing works, help"
    assert problem["flair_or_none"] == "Help"
    assert problem["selection_reason"] == "engagement_head"
    assert outcome["title_or_none"] == "Look at my result"
    assert outcome["selection_reason"] == "title_explicit"
    assert payload["eligible_threads_found"] == 2
    assert payload["candidates_found"] == 2
    assert payload["selection_reason_counts"] == {
        "engagement_head": 1,
        "title_explicit": 1,
    }
    assert payload["capture_slots"] == [
        {
            "slot_id": "weekly_0001",
            "url": "https://old.reddit.com/r/makeupaddiction/comments/pr1/problem/",
        },
        {
            "slot_id": "weekly_0002",
            "url": "https://old.reddit.com/r/makeupaddiction/comments/br1/broadcast/",
        },
    ]


def test_weekly_deep_dive_selection_rescues_titles_and_audits_opaque_tail() -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import _select_deep_dive_rows

    rows = [
        {
            "subreddit": "example",
            "thread_url": f"https://old.reddit.com/r/example/comments/id{index}/post/",
            "title_or_none": title,
            "flair_or_none": None,
            "timestamp_utc_ms_or_none": None,
            "score": score,
            "comments": comments,
        }
        for index, (title, score, comments) in enumerate(
            [
                ("Opaque head A", 1, 80),
                ("Opaque head B", 5, 70),
                ("Opaque head C", 2, 60),
                ("Opaque head D", 9, 50),
                ("Opaque head E", 1, 40),
                ("This product irritated my skin", 3, 4),
                ("Retinol routine", 4, 3),
                ("Opaque tail by comments", 6, 5),
                ("Opaque tail by score", 25, 1),
                ("Opaque audit tail", 1, 0),
            ],
            start=1,
        )
    ]

    selected = _select_deep_dive_rows(
        subreddit="example",
        rows=rows,
        as_of=dt.date(2026, 7, 23),
        opaque_tail_audit_fraction=1.0,
    )

    assert [row["selection_reason"] for row in selected].count("engagement_head") == 5
    assert [row["selection_reason"] for row in selected].count("title_explicit") == 1
    assert [row["selection_reason"] for row in selected].count("title_suggestive") == 1
    assert (
        [row["selection_reason"] for row in selected].count(
            "absolute_engagement_rescue"
        )
        == 2
    )
    assert [row["selection_reason"] for row in selected].count("opaque_tail_audit") == 1
    assert len(selected) == 10


@pytest.mark.parametrize(
    ("comments", "score", "expected"),
    [
        (4, 24, False),
        (5, 0, True),
        (0, 25, True),
        (5, 25, True),
    ],
)
def test_weekly_absolute_engagement_rescue_thresholds(
    comments: int,
    score: int,
    expected: bool,
) -> None:
    from runners.run_reddit_weekly_demand_read import (
        _absolute_engagement_rescue_eligible,
    )

    assert (
        _absolute_engagement_rescue_eligible(comments=comments, score=score)
        is expected
    )


@pytest.mark.parametrize(
    ("title", "flair", "comments", "expected_score", "expected_eligible"),
    [
        ("How should I do this?", None, 12, 1, False),
        ("My current routine", "Routine", 12, 1, False),
        ("PBE haul", None, 18, 1, False),
        ("No one else will appreciate this repair", "Showoff", 8, 2, True),
        ("Alastin serum shout out", None, 5, 3, True),
        ("Review: new perfume collection", None, 3, 3, True),
        ("This burned my face", None, 3, 2, True),
        ("This burned my face", None, 0, 2, False),
        ("Review: new perfume collection", None, 0, 3, True),
    ],
)
def test_weekly_tail_rescue_requires_decision_signal_and_low_comment_context(
    title: str,
    flair: str | None,
    comments: int,
    expected_score: int,
    expected_eligible: bool,
) -> None:
    from runners.run_reddit_weekly_demand_read import (
        _classify_title_signal,
        _tail_title_rescue_eligible,
        _tail_title_rescue_score,
        _title_context_reasons,
    )

    _title_class, title_reasons = _classify_title_signal(title, flair)
    context_reasons = _title_context_reasons(title, flair)
    score = _tail_title_rescue_score(
        title_reasons=title_reasons,
        context_reasons=context_reasons,
    )

    assert score == expected_score
    assert _tail_title_rescue_eligible(comments=comments, rescue_score=score) is expected_eligible


def test_weekly_audit_names_weak_signal_titles_truthfully() -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import _select_deep_dive_rows

    rows = [
        {
            "subreddit": "example",
            "thread_url": f"https://old.reddit.com/r/example/comments/id{index}/post/",
            "title_or_none": title,
            "flair_or_none": None,
            "timestamp_utc_ms_or_none": None,
            "score": (20 - index) if index <= 3 else (5 - index),
            "comments": (20 - index) if index <= 3 else (5 - index),
        }
        for index, title in enumerate(
            [
                "Head one",
                "Head two",
                "Head three",
                "How should I do this?",
                "Opaque tail",
                "My current routine",
            ],
            start=1,
        )
    ]

    selected = _select_deep_dive_rows(
        subreddit="example",
        rows=rows,
        as_of=dt.date(2026, 7, 23),
        opaque_tail_audit_fraction=1.0,
    )

    audit_reasons = {
        row["title_or_none"]: row["selection_reason"]
        for row in selected
        if row["selection_reason"].endswith("_audit")
    }
    assert audit_reasons == {
        "How should I do this?": "weak_signal_tail_audit",
        "Opaque tail": "opaque_tail_audit",
        "My current routine": "weak_signal_tail_audit",
    }


@pytest.mark.parametrize(
    ("title", "expected_class", "expected_reason"),
    [
        ("This serum burned my face", "explicit", "pain_or_failure"),
        ("The best sunscreen I have ever used", "explicit", "praise_or_success"),
        ("Brand A vs Brand B", "explicit", "comparison_or_choice"),
        ("How do I stop foundation pilling?", "explicit", "concrete_question_or_request"),
        ("I started oral minoxidil daily", "explicit", "concrete_outcome_or_experience"),
        ("Protective styles for over 40", "explicit", "concrete_question_or_request"),
        ("Daily eyeshadow base: 2021-2026", "explicit", "concrete_outcome_or_experience"),
        ("Six month progress update", "suggestive", "review_or_update"),
        ("My current skincare routine", "suggestive", "routine_or_collection"),
        ("Plum inspired nails", "opaque", None),
    ],
)
def test_weekly_title_signal_classifier_covers_pain_praise_and_context(
    title: str, expected_class: str, expected_reason: str | None
) -> None:
    from runners.run_reddit_weekly_demand_read import _classify_title_signal

    title_class, reasons = _classify_title_signal(title)

    assert title_class == expected_class
    if expected_reason is None:
        assert reasons == []
    else:
        assert expected_reason in reasons


def test_weekly_title_signal_classifier_uses_listing_visible_flair() -> None:
    from runners.run_reddit_weekly_demand_read import _classify_title_signal

    title_class, reasons = _classify_title_signal(
        "Protective styles for mature hair",
        "Need Advice",
    )

    assert title_class == "explicit"
    assert "concrete_question_or_request" in reasons


def test_weekly_int_or_none_drops_malformed_without_crashing() -> None:
    """The signed-int parser must count a downvoted (negative) score yet drop
    any malformed cell to None. A value str.isdigit() accepts but int()
    rejects -- a double sign or a superscript digit -- must not abort the whole
    weekly read; it must fall into the unparsed-and-dropped path like any other
    junk cell."""
    from runners.run_reddit_weekly_demand_read import _int_or_none

    assert _int_or_none("-5") == -5
    assert _int_or_none("1,204") == 1204
    assert _int_or_none(None) is None
    # Regression: these previously raised ValueError from the unguarded int().
    assert _int_or_none("--5") is None
    assert _int_or_none("\N{SUPERSCRIPT TWO}") is None
    assert _int_or_none("1.2k") is None


def test_weekly_demand_read_tripwire_fires_on_high_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import run_weekly_demand_read

    registry = _registry(tmp_path)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)
    overflowing = WEEKLY_HTML.replace('data-score="10"', 'data-score="60"')
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
        html=overflowing,
    )
    payload = run_weekly_demand_read(data_root=lake, as_of=dt.date(2026, 7, 17))
    assert payload["page_overflow_tripwire"] == ["makeupaddiction"]


# --------------------------------------------------------------------------
# Delegated review regressions (RDR-01, RDR-02, RDR-04)
# --------------------------------------------------------------------------


def test_rdr01_stray_closer_does_not_corrupt_scopes() -> None:
    """A stray </div> mid-listing must not close every active scope: rows
    after it still project with their machine attributes intact."""
    stray = GRID_HTML.replace(
        '<div class="thing link" data-subreddit="MakeupAddiction">',
        '</div></div><div class="thing link" data-subreddit="MakeupAddiction">',
    )
    view = project_old_reddit_grid_html(
        html_text=stray,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )
    assert view.visible_subscriber_count_or_none == "7,491,826"
    assert len(view.thread_rows) == 3
    assert view.thread_rows[1].visible_score_or_none == "1,204"


def test_rdr01_age_span_outside_titlebox_is_ignored() -> None:
    """Only the sidebar (titlebox) age element may supply created_utc; an
    age-classed span in a listing row must not."""
    leaked = GRID_HTML.replace(
        '<a class="title" href="/r/makeupaddiction/comments/aaa111/first_post/">First look post</a>',
        '<span class="age"><time datetime="2001-01-01T00:00:00+00:00">forever</time></span>'
        '<a class="title" href="/r/makeupaddiction/comments/aaa111/first_post/">First look post</a>',
    )
    view = project_old_reddit_grid_html(
        html_text=leaked,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=day",
    )
    assert view.created_utc_or_none is None


def test_rdr01_listing_diagnostics_feed_anomaly_predicate() -> None:
    view = project_old_reddit_grid_html(
        html_text=WEEKLY_HTML,
        subreddit="makeupaddiction",
        listing_url="https://old.reddit.com/r/makeupaddiction/top/?t=week",
    )
    assert view.listing_thing_count_or_none == 3
    assert view.listing_permalink_count_or_none == 3
    from capture_spine.reddit_subreddit_grid.grid_projection import (
        grid_view_projection_anomaly,
    )
    assert grid_view_projection_anomaly(view) is None


def test_rdr02_rotation_visits_every_member_at_any_roster_size() -> None:
    """The pre-review formula ((year*100+week) % size) never reaches members
    beyond index 52 at roster size 100; the absolute weekly index must visit
    all members cyclically."""
    import datetime as dt

    roster = [f"sub{i:03d}" for i in range(100)]
    seen = {
        grid_runner._rotating_raw_sample(
            roster, on_date=dt.date(2026, 1, 5) + dt.timedelta(weeks=week)
        )
        for week in range(100)
    }
    assert seen == set(roster)
    # Deterministic within a week regardless of weekday.
    monday = dt.date(2026, 7, 20)
    assert grid_runner._rotating_raw_sample(roster, on_date=monday) == (
        grid_runner._rotating_raw_sample(roster, on_date=monday + dt.timedelta(days=6))
    )


def test_rdr04_same_day_selection_uses_exact_capture_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two weekly packets on the same observed date: the reader must keep the
    later capture instant, not the larger opaque packet id, and must report
    the superseded packet instead of dropping it silently."""
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import run_weekly_demand_read

    registry = _registry(tmp_path)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)

    early = WEEKLY_HTML.replace(">Nothing works, help<", ">EARLY capture<")
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
        html=early,
        capture_timestamp="2026-07-17T18:00:00Z",
    )
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
        html=WEEKLY_HTML,
        capture_timestamp="2026-07-17T05:00:00Z",
    )

    payload = run_weekly_demand_read(data_root=lake, as_of=dt.date(2026, 7, 17))
    assert payload["subs_read"] == 1
    candidate = next(
        row
        for row in payload["candidates"]
        if row["thread_url"].endswith("/pr1/problem/")
    )
    # The 18:00Z capture wins even though it was committed first (smaller id).
    assert candidate["title_or_none"] == "EARLY capture"
    assert payload["superseded_weekly_packets"]["count"] == 1
    assert len(payload["superseded_weekly_packets"]["sample"]) == 1


def test_rdr04_disposition_reporting_is_bounded_and_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import run_weekly_demand_read

    registry = _registry(tmp_path)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
    )
    _lake_grid_packet(
        lake, monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/hot/",
    )
    payload = run_weekly_demand_read(data_root=lake, as_of=dt.date(2026, 7, 17))
    non_top = payload["packets_skipped_non_top_week"]
    assert non_top["count"] == 1
    assert len(non_top["sample"]) == 1
    assert payload["packets_skipped_outside_window"]["count"] == 0


LOGIN_WALL_HTML = """
<html><head><title>Welcome to Reddit</title></head><body>
<p>Log in or sign up to personalize your feed, join conversations, vote.</p>
</body></html>
"""

EMPTY_LISTING_HTML = """
<html>
<head><title>top scoring links : MakeupAddiction</title></head>
<body class="listing-page top-page">
<div id="siteTable" class="sitetable linklisting">
  <p id="noresults" class="error">there doesn't seem to be anything here</p>
</div>
</body>
</html>
"""


def test_verified_empty_listing_is_valid_but_login_near_misses_fail() -> None:
    url = "https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100"

    record = grid_runner.build_validated_grid_content_record(
        html_text=EMPTY_LISTING_HTML,
        final_url=url,
        subreddit="makeupaddiction",
        listing_url=url,
    )
    view = grid_view_from_record(record)
    assert view.verified_empty_listing is True
    assert view.thread_rows == ()
    assert grid_view_projection_anomaly(view) is None

    with pytest.raises(
        grid_runner.GridProjectionAnomalyError,
        match="empty_listing_final_url_mismatch",
    ):
        grid_runner.build_validated_grid_content_record(
            html_text=EMPTY_LISTING_HTML,
            final_url="https://old.reddit.com/login/?reason=lor2",
            subreddit="makeupaddiction",
            listing_url=url,
        )

    with pytest.raises(
        grid_runner.GridProjectionAnomalyError,
        match="no_thread_rows",
    ):
        grid_runner.build_validated_grid_content_record(
            html_text=LOGIN_WALL_HTML,
            final_url=url,
            subreddit="makeupaddiction",
            listing_url=url,
        )

    mixed_page = EMPTY_LISTING_HTML.replace(
        '<p id="noresults"',
        '<div class="thing promoted"></div><p id="noresults"',
    )
    with pytest.raises(
        grid_runner.GridProjectionAnomalyError,
        match="no_thread_rows",
    ):
        grid_runner.build_validated_grid_content_record(
            html_text=mixed_page,
            final_url=url,
            subreddit="makeupaddiction",
            listing_url=url,
        )


def test_weekly_reader_counts_verified_empty_listing_as_zero_activity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import datetime as dt

    from runners.run_reddit_weekly_demand_read import run_weekly_demand_read

    registry = _registry(tmp_path)
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    migrate_legacy_registry(lake, registry_path=registry)
    _lake_grid_packet(
        lake,
        monkeypatch,
        url="https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100",
        html=EMPTY_LISTING_HTML,
    )

    payload = run_weekly_demand_read(
        data_root=lake,
        as_of=dt.date(2026, 7, 17),
    )

    assert payload["subs_read"] == 1
    assert payload["subs_missing_weekly_packet"] == []
    assert payload["projection_anomaly_packets"] == []
    assert payload["candidates_found"] == 0
    (health,) = payload["sub_health"]
    assert health["posts"] == 0
    assert health["weekly_score"] == 0
    assert health["weekly_comments"] == 0


def test_raw_sample_still_validates_the_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression for the 2026-07-22 full-roster pass: Reddit redirected every
    request to a login wall. Content-mode captures failed loud via the anomaly
    guard, but the rotating RAW sample skipped extraction entirely and banked
    the login page reporting exit 0 -- the one packet kept to audit the
    projection was the one packet nobody audited."""
    url = "https://old.reddit.com/r/makeupaddiction/top/?t=week&limit=100"

    def fake_fetch(**_: object) -> DirectHttpCaptureSuccess:
        return DirectHttpCaptureSuccess(
            requested_url=url,
            final_url="https://old.reddit.com/login/?reason=lor2&dest=" + url,
            status=200,
            reason="OK",
            metadata={"capture_timestamp": "2026-07-22T19:58:32Z", "requested_url": url,
                      "final_url": url, "status": 200},
            body=LOGIN_WALL_HTML.encode(),
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(http_packet_runner, "fetch_direct_http_capture", fake_fetch)

    def run(validate: bool) -> tuple[int, dict]:
        out = tmp_path / f"packet_validate_{validate}"
        code, _ = http_packet_runner.run_source_capture_http_packet(
            url=url, source_family="reddit_subreddit_grid",
            source_surface="old_reddit_direct_http",
            decision_question="raw sample validation", output_directory=out,
            capture_context="test", operator_category="test_operator",
            capture_mode=http_packet_runner.CaptureModeCategory.STRUCTURED_ACCESS,
            session_id=None, actor_audience_context=None, visible_mode_changes=[],
            source_publication_or_event=None, source_edit_or_version=None,
            cutoff_posture=None, recapture_time=None, re_capture_relationship=None,
            warnings=[], limitations=[], timeout_seconds=5, max_bytes=1_000_000,
            content_extraction=ContentExtractionSpec(
                requested_retention_mode="raw",
                extractor_version=GRID_PROJECTION_PARSER_VERSION,
                extractor=lambda html_text, _u: (_ for _ in ()).throw(
                    grid_runner.GridProjectionAnomalyError("no_thread_rows")
                ) if grid_runner.check_grid_projection_anomaly(
                    build_grid_content_record(
                        html_text=html_text, subreddit="makeupaddiction", listing_url=url)
                ) else build_grid_content_record(
                    html_text=html_text, subreddit="makeupaddiction", listing_url=url),
                validate_in_raw_mode=validate,
            ),
        )
        meta = json.loads(
            (out / "raw" / "02_http_response_metadata.json").read_text(encoding="utf-8")
        )
        return code, meta["content_extraction"]

    # Old behavior: raw mode skipped extraction, so a login wall passed clean.
    code_off, ce_off = run(validate=False)
    assert code_off == 0
    assert ce_off["extraction_status"] == "not_attempted: raw retention requested"

    # Fixed: the projection is checked even though raw is what gets kept.
    code_on, ce_on = run(validate=True)
    assert code_on == 4, "a login wall must not report a clean raw capture"
    assert ce_on["retention_outcome"] == "raw_failure"
    assert "no_thread_rows" in ce_on["extraction_status"]
    assert ce_on["raw_preserved"] is True, "raw must still be preserved for audit"
