"""Real-Chrome CDP capture under content retention and screenshot suppression.

Drives the whole runner through an injected engine, so the capture -> retention
-> packet chain is exercised without a network request. The first test is a
CHARACTERIZATION test: it pins today's behavior for every existing caller
(TikTok, IG, retail), which is what makes "Reddit only" checkable rather than
asserted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners.run_source_capture_realchrome_cdp_packet import (
    RealChromeCDPCaptureResult,
    run_source_capture_realchrome_cdp_packet,
)
from source_capture.content_extraction import (
    CONTENT_RECORD_FILENAME,
    RenderedContentExtractionSpec,
)

URL = "https://www.reddit.com/r/testsub/top/?t=week"
DOM = "<html><body><shreddit-post permalink='/r/testsub/comments/a/b/'></shreddit-post></body></html>"
TEXT = "Created Mar 3, 2015 Public 701K7.4K"
PNG = b"\x89PNG\r\n\x1a\n" + b"pixels" * 100


class _FakeEngine:
    """Returns fixed artifacts and records whether a screenshot was asked for."""

    def __init__(self, *, dom: str = DOM, text: str = TEXT) -> None:
        self.dom = dom
        self.text = text
        self.capture_screenshot_seen: bool | None = None

    def capture(self, **kwargs) -> RealChromeCDPCaptureResult:
        self.capture_screenshot_seen = kwargs.get("capture_screenshot", True)
        return RealChromeCDPCaptureResult(
            requested_url=kwargs["url"],
            final_url=kwargs["url"],
            title="Test",
            rendered_dom=self.dom,
            visible_text=self.text,
            screenshot_png=PNG if self.capture_screenshot_seen else None,
            http_status=200,
            warm_hop_url=None,
            warm_hop_blocked=None,
            viewport_width=1280,
            viewport_height=20000,
        )


def _run(tmp_path: Path, engine: _FakeEngine, **overrides):
    kwargs = {
        "url": URL,
        "source_family": "reddit_subreddit_grid",
        "source_surface": "www_reddit_realchrome",
        "decision_question": "what is breaking out this week?",
        "output_directory": tmp_path / "packet",
        "engine": engine,
    }
    kwargs.update(overrides)
    exit_code, output = run_source_capture_realchrome_cdp_packet(**kwargs)
    return exit_code, Path(output)


def _artifact_names(packet_dir: Path) -> set[str]:
    raw_dir = packet_dir / "raw"
    return {p.name for p in raw_dir.iterdir()} if raw_dir.is_dir() else set()


def _has(names: set[str], needle: str) -> bool:
    """The packet writer prefixes staged names, so match on substring."""
    return any(needle in name for name in names)


def _spec(extractor=None, mode: str = "content") -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version="www-2",
        extractor=extractor or (lambda _dom, _text, _url: {"record_kind": "test", "rows": 1}),
    )


def test_existing_callers_are_unchanged(tmp_path: Path) -> None:
    """Characterization: no new params -> today's artifact set, screenshot taken."""
    engine = _FakeEngine()
    exit_code, packet = _run(tmp_path, engine)
    assert exit_code == 0
    assert engine.capture_screenshot_seen is True
    names = _artifact_names(packet)
    assert _has(names, "rendered_dom")
    assert _has(names, "visible_text")
    assert _has(names, "screenshot")
    assert not _has(names, CONTENT_RECORD_FILENAME)


def test_content_retention_publishes_the_record_and_drops_raw(tmp_path: Path) -> None:
    engine = _FakeEngine()
    exit_code, packet = _run(
        tmp_path, engine, content_extraction=_spec(), capture_screenshot=False
    )
    assert exit_code == 0
    names = _artifact_names(packet)
    assert _has(names, CONTENT_RECORD_FILENAME)
    assert not _has(names, "rendered_dom")
    assert not _has(names, "visible_text")
    assert not _has(names, "screenshot")


def test_suppressed_screenshot_is_not_captured_and_says_so(tmp_path: Path) -> None:
    """A packet reporting a zero-byte viewport shot would claim a false posture."""
    engine = _FakeEngine()
    _, packet = _run(
        tmp_path, engine, content_extraction=_spec(), capture_screenshot=False
    )
    assert engine.capture_screenshot_seen is False
    meta = json.loads(
        next(
            p for p in (packet / "raw").iterdir() if "snapshot_metadata" in p.name
        ).read_text(encoding="utf-8")
    )
    assert meta["screenshot_mode"] == "not_captured"
    assert meta["screenshot_byte_count"] is None


def test_dropped_raw_leaves_its_provenance_in_the_packet(tmp_path: Path) -> None:
    engine = _FakeEngine()
    _, packet = _run(
        tmp_path, engine, content_extraction=_spec(), capture_screenshot=False
    )
    manifest = (packet / "manifest.json").read_text(encoding="utf-8")
    assert "retention_outcome=content" in manifest
    assert "discarded_inputs" in manifest
    assert "www-2" in manifest


def test_audit_sample_keeps_raw_alongside_the_record(tmp_path: Path) -> None:
    engine = _FakeEngine()
    _, packet = _run(
        tmp_path,
        engine,
        content_extraction=_spec(),
        capture_screenshot=False,
        keep_raw_audit_sample=True,
    )
    names = _artifact_names(packet)
    assert _has(names, CONTENT_RECORD_FILENAME)
    assert _has(names, "rendered_dom")


def test_extraction_failure_preserves_raw_and_withholds_no_record(tmp_path: Path) -> None:
    def _boom(_dom, _text, _url):
        raise ValueError("grid projection anomaly [no_thread_rows]")

    engine = _FakeEngine()
    _, packet = _run(
        tmp_path, engine, content_extraction=_spec(_boom), capture_screenshot=False
    )
    names = _artifact_names(packet)
    assert not _has(names, CONTENT_RECORD_FILENAME)
    assert _has(names, "rendered_dom")
    manifest = (packet / "manifest.json").read_text(encoding="utf-8")
    assert "no_thread_rows" in manifest


def test_a_www_content_packet_reads_and_folds_end_to_end(tmp_path: Path) -> None:
    """Capture -> packet -> materializer -> registry, with no network.

    The two transports name their metadata file and success posture differently,
    so this is the test that would have caught a www packet capturing cleanly and
    then being unreadable at the fold.
    """
    from capture_spine.reddit_subreddit_grid.materializer import (
        read_grid_packet,
        refresh_lake_registry_from_grid_packets,
    )
    from capture_spine.reddit_subreddit_grid.www_grid_projection import (
        build_www_grid_content_record,
    )
    from data_lake.reddit_subreddit_registry import append_roster_change, fold_subreddit
    from data_lake.root import DataLakeRoot

    dom = (
        "<html><body>"
        "<shreddit-post permalink='/r/testsub/comments/aaa/t/' post-title='One'"
        " score='10' comment-count='5' subreddit-prefixed-name='r/testsub'"
        " created-timestamp='2026-07-24T01:11:13.173000+0000'></shreddit-post>"
        "</body></html>"
    )
    engine = _FakeEngine(dom=dom, text="Created Mar 3, 2015 Public 701K7.4K")
    spec = RenderedContentExtractionSpec(
        requested_retention_mode="content",
        extractor_version="www-2",
        extractor=lambda d, t, u: build_www_grid_content_record(
            rendered_dom=d.decode("utf-8"),
            visible_text=t.decode("utf-8"),
            subreddit="testsub",
            listing_url=URL,
        ),
    )
    _, packet = _run(tmp_path, engine, content_extraction=spec, capture_screenshot=False)

    read = read_grid_packet(packet_or_manifest_path=packet)
    assert read.subreddit == "testsub"
    assert len(read.grid_view.thread_rows) == 1

    lake = DataLakeRoot.for_test(tmp_path / "lake")
    append_roster_change(lake, subreddit="testsub", change_kind="add", actor="test")
    outcome = refresh_lake_registry_from_grid_packets(
        data_root=lake, packet_paths=[packet], dry_run=False
    )
    assert outcome.refreshed_subreddits == ["testsub"]
    assert outcome.unknown_subreddits == []

    observation = fold_subreddit(lake, "testsub")["observations"][0]
    assert observation["source_surface"] == "www_reddit_top_week_packet"
    # The www sidebar exposes weekly visitors/contributions, not subscribers, so
    # the observation carries an honest absence rather than a mislabelled count.
    assert observation["subscriber_count_or_none"] is None
    assert (
        observation["absent_reason_or_none"]
        == "www_venue_envelope_exposes_weekly_visitors_not_subscriber_counts"
    )


def test_a_blocked_www_capture_does_not_fold(tmp_path: Path) -> None:
    """Failure evidence must never become registry evidence."""
    from capture_spine.reddit_subreddit_grid.materializer import (
        RegistryRefreshError,
        read_grid_packet,
    )

    engine = _FakeEngine(
        dom="<html><body>blocked</body></html>",
        text="You've been blocked by network security. File a ticket",
    )
    _, packet = _run(
        tmp_path, engine, content_extraction=_spec(), capture_screenshot=False
    )
    with pytest.raises(RegistryRefreshError) as excinfo:
        read_grid_packet(packet_or_manifest_path=packet)
    assert excinfo.value.code in {"grid_access_unsuccessful", "www_content_record_required"}


def test_access_block_withholds_a_clean_record_and_keeps_raw(tmp_path: Path) -> None:
    """A projection of a login wall must not ship as admitted source content."""
    engine = _FakeEngine(
        dom="<html><body>blocked</body></html>",
        text="You've been blocked by network security. File a ticket",
    )
    _, packet = _run(
        tmp_path, engine, content_extraction=_spec(), capture_screenshot=False
    )
    names = _artifact_names(packet)
    assert not _has(names, CONTENT_RECORD_FILENAME)
    assert _has(names, "rendered_dom")
