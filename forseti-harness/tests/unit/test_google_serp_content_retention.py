"""Google SERP content retention: extraction, tripwires, parity, rolling sample.

The SERP lane's v1 extractor shipped rows that were individually plausible while
silently mis-ranking organic results and bleeding People-Also-Ask content into
organic parsing.  Content-only retention forecloses re-extraction, so these tests
guard the three things that make the flip survivable: the extractor projects a
real SERP faithfully, a degenerate or blocked page raises instead of banking a
thin record, and the parity checker actually notices an arrangement change.

The fixture is a synthetic SERP shaped like the real captures (module headings,
URL breadcrumb lines, a PAA block that ends without a heading).  Byte-level
agreement with the lane's pre-flip corpus is measured by the parity gate runner
over real packets, not asserted here.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from source_capture.google_serp_content import (
    GOOGLE_SERP_CONTENT_RECORD_VERSION,
    GoogleSerpContentAnomaly,
    GoogleSerpRouteBlocked,
    build_google_serp_content_record,
    direct_hrefs,
    match_href,
)
from source_capture.retention_parity import (
    check_serp_invariants,
    compare_records,
    exercise_failure_path,
)
from source_capture.rolling_raw_sample import (
    CONTENT_RECORD_SAMPLE_FILENAME,
    RENDERED_DOM_SAMPLE_FILENAME,
    VISIBLE_TEXT_SAMPLE_FILENAME,
    RollingRawSampleStore,
)

_QUERY_URL = "https://www.google.com/search?q=summer+fridays+review&hl=en&gl=us&pws=0"

_VISIBLE_TEXT = """Skip to main content
Search Results

People also ask
Is Summer Fridays worth the money?
Do dermatologists recommend Summer Fridays?
Summer Fridays Lip Butter Balm Review
https://www.byrdie.com › summer-fridays-review
Byrdie
We tested the balm for six weeks. Sep 3, 2025

Reddit
https://www.reddit.com › r/SkincareAddiction › comments
Honest thoughts on Summer Fridays?
1.2K votes and 340 comments

Short videos
0:45
TikTok · @skinbyalex
Summer Fridays lip butter honest review
120K views

Related searches
summer fridays dupe
summer fridays vs laneige
Page Navigation
"""

_RENDERED_DOM = """<html><body>
<a href="https://www.byrdie.com/summer-fridays-review"><h3>Summer Fridays Lip Butter Balm Review</h3></a>
<a href="https://www.reddit.com/r/SkincareAddiction/comments/abc123">Honest thoughts on Summer Fridays?</a>
<a href="https://www.google.com/search?q=more">Google internal</a>
<a href="https://www.tiktok.com/@skinbyalex/video/123">Summer Fridays lip butter honest review</a>
</body></html>"""


def _record(visible_text: str = _VISIBLE_TEXT, rendered_dom: str = _RENDERED_DOM) -> dict:
    return build_google_serp_content_record(
        rendered_dom=rendered_dom.encode("utf-8"),
        visible_text=visible_text.encode("utf-8"),
        final_url=_QUERY_URL,
        requested_url=_QUERY_URL,
    )


# --- extraction -------------------------------------------------------------


def test_record_types_modules_and_carries_the_version() -> None:
    record = _record()
    assert record["content_record_version"] == GOOGLE_SERP_CONTENT_RECORD_VERSION
    assert "people_also_ask" in record["modules_present"]
    assert "organic" in record["modules_present"]
    assert "video_block" in record["modules_present"]
    assert "related_search" in record["modules_present"]


def test_people_also_ask_block_exits_at_the_first_non_question_line() -> None:
    """The v1 defect: PAA swallowed the organic results that followed it."""
    record = _record()
    paa_titles = [
        row["title"] for row in record["rows"] if row["module_type"] == "people_also_ask"
    ]
    assert paa_titles == [
        "Is Summer Fridays worth the money?",
        "Do dermatologists recommend Summer Fridays?",
    ]
    organic_titles = [
        row["title"] for row in record["rows"] if row["module_type"] == "organic"
    ]
    assert "Summer Fridays Lip Butter Balm Review" in organic_titles
    assert not any(title.endswith("?") and "worth the money" in title
                   for title in organic_titles)


def test_rows_carry_displayed_domain_and_platform() -> None:
    record = _record()
    by_domain = {
        row["displayed_domain"]: row
        for row in record["rows"]
        if row["displayed_domain"]
    }
    assert by_domain["www.byrdie.com"]["module_type"] == "organic"
    assert by_domain["www.reddit.com"]["platform"] == "reddit"


def test_direct_hrefs_skips_google_internal_anchors() -> None:
    href_map = direct_hrefs(_RENDERED_DOM)
    hrefs = [href for values in href_map.values() for href in values]
    assert all("google.com" not in href for href in hrefs)
    assert any("byrdie.com" in href for href in hrefs)


def test_href_matching_uses_visible_identity_to_disambiguate_repeated_titles() -> None:
    title = "An Honest Review of Laneige Lip Sleeping Mask"
    href_map = direct_hrefs(
        f"""
        <a href="https://first.example/review"><h3>{title}</h3></a>
        <a href="https://second.example/review"><h3>{title}</h3></a>
        """
    )
    assert (
        match_href(title, href_map, displayed_domain="second.example")
        == "https://second.example/review"
    )
    assert match_href(title, href_map) is None


def test_href_matching_prefers_the_visible_platform_over_a_broad_prefix() -> None:
    title = "Laneige lip sleeping mask is it actually worth buying"
    href_map = direct_hrefs(
        f"""
        <a href="https://us.laneige.com/products/lip-sleeping-mask">
          Laneige lip sleeping mask
        </a>
        <a href="https://www.instagram.com/reel/abc/">
          {title} Instagram · creator
        </a>
        """
    )
    assert (
        match_href(title, href_map, source_label="Instagram")
        == "https://www.instagram.com/reel/abc/"
    )


def test_query_rewritten_is_false_when_the_landing_query_matches() -> None:
    assert _record()["query_rewritten"] is False


def test_query_rewritten_is_true_when_google_rewrites_the_query() -> None:
    record = build_google_serp_content_record(
        rendered_dom=_RENDERED_DOM.encode("utf-8"),
        visible_text=_VISIBLE_TEXT.encode("utf-8"),
        final_url=(
            "https://www.google.com/search?q=summer+friday+review&hl=en&gl=us&pws=0"
        ),
        requested_url=_QUERY_URL,
    )
    assert record["query_rewritten"] is True


def test_ai_overview_visible_content_survives_content_projection() -> None:
    visible_text = _VISIBLE_TEXT.replace(
        "People also ask",
        (
            "AI Overview\n"
            "Independent testing found the balm reduced visible dryness overnight.\n"
            "The result varied for fragrance-sensitive reviewers.\n"
            "Web results\n"
            "People also ask"
        ),
        1,
    )
    record = _record(visible_text=visible_text)
    assert record["ai_overview"]["present"] is True
    assert "reduced visible dryness" in record["ai_overview"]["visible_text"]


# --- tripwires --------------------------------------------------------------


def test_unusual_traffic_interstitial_raises_so_raw_is_preserved() -> None:
    """A block body carries a visible exit IP; it must never become a record."""
    with pytest.raises(GoogleSerpRouteBlocked):
        build_google_serp_content_record(
            rendered_dom=b"<html><body>unusual traffic</body></html>",
            visible_text=(
                b"Our systems have detected unusual traffic from your computer network."
            ),
            final_url="https://www.google.com/sorry/index",
        )


def test_structurally_empty_page_raises_instead_of_banking_a_thin_record() -> None:
    with pytest.raises(GoogleSerpContentAnomaly):
        build_google_serp_content_record(
            rendered_dom=b"<html><body>Google</body></html>",
            visible_text=b"Google\nSearch\n",
            final_url=_QUERY_URL,
        )


def test_page_with_text_but_no_known_module_raises() -> None:
    """An unrecognized layout is a defect signal, not an empty result page."""
    with pytest.raises(GoogleSerpContentAnomaly):
        build_google_serp_content_record(
            rendered_dom=b"<html><body>x</body></html>",
            visible_text=("some unrecognised surface. " * 40).encode("utf-8"),
            final_url=_QUERY_URL,
        )


def test_exercise_failure_path_reports_pass_when_every_tripwire_fires() -> None:
    verdict, notes = exercise_failure_path(
        extractor=build_google_serp_content_record,
        anomaly_type=GoogleSerpContentAnomaly,
        synthetic_cases=(
            (
                "block",
                b"<html/>",
                b"Our systems have detected unusual traffic",
                _QUERY_URL,
            ),
            ("thin", b"<html/>", b"Google", _QUERY_URL),
        ),
    )
    assert verdict == "pass"
    assert len(notes) == 2


def test_exercise_failure_path_fails_when_a_tripwire_returns_a_record() -> None:
    verdict, notes = exercise_failure_path(
        extractor=lambda **_kwargs: {"rows": []},
        anomaly_type=GoogleSerpContentAnomaly,
        synthetic_cases=(("block", b"", b"", _QUERY_URL),),
    )
    assert verdict == "fail"
    assert "RETURNED A RECORD" in notes[0]


# --- parity checking --------------------------------------------------------


def test_identical_reextraction_produces_no_diffs() -> None:
    assert compare_records(unit="u", baseline=_record(), reextracted=_record()) == []


def test_parity_catches_a_reordered_row() -> None:
    """The arrangement defect class: same rows, wrong order."""
    baseline = _record()
    reextracted = _record()
    rows = reextracted["rows"]
    organic = [i for i, row in enumerate(rows) if row["module_type"] == "organic"]
    first, second = organic[0], organic[1]
    rows[first], rows[second] = rows[second], rows[first]
    diffs = compare_records(unit="u", baseline=baseline, reextracted=reextracted)
    assert any(diff.field_name == "title" for diff in diffs)


def test_parity_catches_a_dropped_row() -> None:
    reextracted = _record()
    reextracted["rows"].pop()
    diffs = compare_records(unit="u", baseline=_record(), reextracted=reextracted)
    assert [diff.field_name for diff in diffs] == ["row_count"]


def test_parity_catches_a_changed_canonical_url_absence_reason() -> None:
    baseline = _record()
    reextracted = _record()
    row = next(row for row in reextracted["rows"] if not row["canonical_url"])
    row["canonical_url_absent_reason"] = "different reason"
    diffs = compare_records(unit="u", baseline=baseline, reextracted=reextracted)
    assert [diff.field_name for diff in diffs] == ["canonical_url_absent_reason"]


def test_parity_skips_top_level_fields_absent_from_the_baseline() -> None:
    """A pre-flip lane record and an in-flight record carry different envelopes."""
    baseline = {"rows": _record()["rows"]}
    assert compare_records(unit="u", baseline=baseline, reextracted=_record()) == []


def test_invariants_pass_on_a_real_shaped_record() -> None:
    assert check_serp_invariants(unit="u", record=_record(), minimum_rows=3) == []


def test_invariants_reject_gapped_but_ascending_order() -> None:
    """A monotonic gap can hide a dropped row when no baseline exists."""
    record = {
        "modules_present": ["organic"],
        "rows": [
            {"module_type": "organic", "order_in_module": 1},
            {"module_type": "organic", "order_in_module": 3},
            {"module_type": "organic", "order_in_module": 7},
        ],
    }
    violations = check_serp_invariants(unit="u", record=record, minimum_rows=3)
    assert [v.invariant for v in violations] == ["order_contiguity"]


def test_invariants_reject_non_ascending_order() -> None:
    record = {
        "modules_present": ["organic"],
        "rows": [
            {"module_type": "organic", "order_in_module": 1},
            {"module_type": "organic", "order_in_module": 5},
            {"module_type": "organic", "order_in_module": 4},
        ],
    }
    violations = check_serp_invariants(unit="u", record=record, minimum_rows=3)
    assert [v.invariant for v in violations] == ["order_contiguity"]


def test_invariants_reject_rows_typed_to_an_undeclared_module() -> None:
    record = {
        "modules_present": ["organic"],
        "rows": [
            {"module_type": "organic", "order_in_module": 1},
            {"module_type": "organic", "order_in_module": 2},
            {"module_type": "people_also_ask", "order_in_module": 1},
        ],
    }
    violations = check_serp_invariants(unit="u", record=record, minimum_rows=3)
    assert [v.invariant for v in violations] == ["module_declaration"]


def test_invariants_reject_a_url_that_contradicts_the_visible_domain() -> None:
    record = _record()
    row = next(row for row in record["rows"] if row["displayed_domain"])
    row["canonical_url"] = "https://contradictory.example/result"
    row["canonical_url_source_visible"] = True
    row["canonical_url_absent_reason"] = None
    violations = check_serp_invariants(unit="u", record=record, minimum_rows=3)
    assert "canonical_domain_match" in [v.invariant for v in violations]


# --- rolling raw sample -----------------------------------------------------


def _write_sample(store: RollingRawSampleStore, *, day: date, run_key: str | None = None):
    claim = store.claim(
        surface="google_serp_us_parameterized", capture_date=day, run_key=run_key
    )
    if claim.granted:
        store.write_sample(
            claim,
            rendered_dom=_RENDERED_DOM.encode("utf-8"),
            visible_text=_VISIBLE_TEXT.encode("utf-8"),
            content_record=json.dumps(_record()).encode("utf-8"),
            metadata={"final_url": _QUERY_URL},
        )
    return claim


def test_first_capture_of_the_day_is_sampled_and_the_rest_are_not(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    first = _write_sample(store, day=date(2026, 7, 28))
    second = _write_sample(store, day=date(2026, 7, 28))
    assert first.granted is True
    assert second.granted is False
    assert "already has a rolling raw sample" in second.reason


def test_a_new_day_earns_a_new_sample(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    assert _write_sample(store, day=date(2026, 7, 28)).granted is True
    assert _write_sample(store, day=date(2026, 7, 29)).granted is True


def test_a_batch_run_key_samples_the_first_capture_of_the_run(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    first = _write_sample(store, day=date(2026, 7, 28), run_key="megadogfood-2")
    second = _write_sample(store, day=date(2026, 7, 29), run_key="megadogfood-2")
    assert first.granted is True
    assert second.granted is False, "a batch campaign samples once per run, not per day"


def test_distinct_run_keys_that_sanitize_alike_use_distinct_directories(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    first = _write_sample(store, day=date(2026, 7, 28), run_key="campaign/a")
    second = _write_sample(store, day=date(2026, 7, 28), run_key="campaign?a")
    assert first.directory is not None and second.directory is not None
    assert first.directory != second.directory
    assert len(store.current_samples()) == 2


def test_sample_directory_holds_the_bytes_a_regression_check_needs(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    claim = _write_sample(store, day=date(2026, 7, 28))
    assert claim.directory is not None
    for name in (
        RENDERED_DOM_SAMPLE_FILENAME,
        VISIBLE_TEXT_SAMPLE_FILENAME,
        CONTENT_RECORD_SAMPLE_FILENAME,
    ):
        assert (claim.directory / name).exists()


def test_samples_outside_the_window_are_pruned_on_the_next_claim(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    old = _write_sample(store, day=date(2026, 1, 1))
    assert old.directory is not None and old.directory.exists()

    fresh = _write_sample(store, day=date(2026, 7, 28))
    assert not old.directory.exists(), "aged-out sample bytes must be deleted"
    assert fresh.pruned_keys, "the prune must be reported, not silent"
    surviving = {entry["sample_key"] for entry in store.current_samples()}
    assert surviving == {"2026-07-28"}


def test_samples_inside_the_window_survive(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    recent = _write_sample(store, day=date(2026, 7, 20))
    _write_sample(store, day=date(2026, 7, 28))
    assert recent.directory is not None and recent.directory.exists()
    assert len(store.current_samples()) == 2


def test_sample_is_pruned_only_after_it_is_older_than_the_window(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path, window_days=30)
    oldest = _write_sample(store, day=date(2026, 6, 28))
    _write_sample(store, day=date(2026, 7, 28))
    assert oldest.directory is not None and oldest.directory.exists()
    _write_sample(store, day=date(2026, 7, 29))
    assert not oldest.directory.exists()


def test_failed_sample_write_does_not_consume_the_claim(tmp_path, monkeypatch) -> None:
    store = RollingRawSampleStore(tmp_path)
    claim = store.claim(
        surface="google_serp_us_parameterized", capture_date=date(2026, 7, 28)
    )
    original_write_bytes = Path.write_bytes

    def fail_content_record(path: Path, data: bytes) -> int:
        if path.name == CONTENT_RECORD_SAMPLE_FILENAME:
            raise OSError("synthetic sample write failure")
        return original_write_bytes(path, data)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_bytes", fail_content_record)
        with pytest.raises(OSError, match="synthetic sample write failure"):
            store.write_sample(
                claim,
                rendered_dom=b"dom",
                visible_text=b"text",
                content_record=b"{}",
                metadata={},
            )

    assert store.current_samples() == []
    retry = store.claim(
        surface="google_serp_us_parameterized", capture_date=date(2026, 7, 28)
    )
    assert retry.granted is True


def test_rolling_sample_regression_check_matches_the_banked_record(tmp_path) -> None:
    """Method 3's regression check: re-extract the window, diff the banked record."""
    store = RollingRawSampleStore(tmp_path)
    claim = _write_sample(store, day=date(2026, 7, 28))
    assert claim.directory is not None

    banked = json.loads(
        (claim.directory / CONTENT_RECORD_SAMPLE_FILENAME).read_text(encoding="utf-8")
    )
    reextracted = build_google_serp_content_record(
        rendered_dom=(claim.directory / RENDERED_DOM_SAMPLE_FILENAME).read_bytes(),
        visible_text=(claim.directory / VISIBLE_TEXT_SAMPLE_FILENAME).read_bytes(),
        final_url=banked["final_url"],
        requested_url=banked["requested_url"],
    )
    assert compare_records(unit="s", baseline=banked, reextracted=reextracted) == []


# --- runner wiring ----------------------------------------------------------


def _run_serp_capture(tmp_path, monkeypatch, *, visible_text: str, **kwargs):
    """Drive the real cloakbrowser runner over a stubbed capture."""
    import runners.run_source_capture_cloakbrowser_packet as cloakbrowser_runner
    from runners.run_source_capture_cloakbrowser_packet import (
        run_source_capture_cloakbrowser_packet,
    )
    from source_capture.adapters.cloakbrowser_snapshot import (
        CloakBrowserSnapshotSuccess,
    )
    from source_capture.models import CaptureModeCategory

    def fake_capture(**call):
        return CloakBrowserSnapshotSuccess(
            requested_url=_QUERY_URL,
            final_url=_QUERY_URL,
            title="summer fridays review - Google Search",
            rendered_dom=_RENDERED_DOM,
            visible_text=visible_text,
            screenshot_png=b"\x89PNG\r\n\x1a\nserp",
            metadata={
                "requested_url": _QUERY_URL,
                "final_url": _QUERY_URL,
                "title": "summer fridays review - Google Search",
                "capture_timestamp": "2026-07-28T00:00:00Z",
                "timeout_seconds": call["timeout_seconds"],
                "wait_until": call["wait_until"],
                "viewport_width": call["viewport_width"],
                "viewport_height": call["viewport_height"],
                "screenshot_mode": "viewport",
                "method_category": "anti_blocking_browser",
                "browser_engine": "cloakbrowser",
                "cloakbrowser_backend": "playwright",
                "profile_persistence": "none",
                "storage_state_loaded": False,
                "proxy_used": False,
                "geoip_used": False,
                "extension_paths_loaded": False,
                "rendered_dom_byte_count": len(_RENDERED_DOM),
                "visible_text_byte_count": len(visible_text),
                "screenshot_byte_count": 16,
            },
            warning_notes=[],
            limitation_notes=[],
        )

    monkeypatch.setattr(
        cloakbrowser_runner, "fetch_cloakbrowser_snapshot_capture", fake_capture
    )
    output = tmp_path / "serp-packet"
    exit_code, _message = run_source_capture_cloakbrowser_packet(
        url=_QUERY_URL,
        source_family="search_discovery",
        source_surface="google_serp_us_parameterized",
        decision_question="What does this SERP surface for the subject?",
        output_directory=output,
        capture_context="SERP retention unit proof; US-parameterized logged-out route",
        operator_category="researcher",
        capture_mode=CaptureModeCategory.MULTIMODAL,
        session_id=None,
        proxy_profile=None,
        actor_audience_context=None,
        visible_mode_changes=[],
        source_publication_or_event=None,
        source_edit_or_version=None,
        cutoff_posture=None,
        recapture_time=None,
        re_capture_relationship=None,
        warnings=[],
        limitations=[],
        timeout_seconds=20,
        wait_until="load",
        viewport_width=1280,
        viewport_height=720,
        max_artifact_bytes=200_000,
        block_heavy_assets=False,
        content_extraction=cloakbrowser_runner._google_serp_content_extraction_spec(
            kwargs.pop("retention_mode", "content"), requested_url=_QUERY_URL
        ),
        **kwargs,
    )
    return exit_code, output


def _preserved_paths(output) -> set[str]:
    return {
        row["relative_packet_path"]
        for row in json.loads((output / "manifest.json").read_text())["preserved_files"]
    }


def test_runner_content_mode_discards_rendered_bytes_and_keeps_the_record(
    tmp_path, monkeypatch
) -> None:
    exit_code, output = _run_serp_capture(
        tmp_path, monkeypatch, visible_text=_VISIBLE_TEXT
    )
    assert exit_code == 0
    paths = _preserved_paths(output)
    assert any(path.endswith("content_record.json") for path in paths)
    assert not any(path.endswith("cloakbrowser_rendered_dom.html") for path in paths)
    assert not any(path.endswith("cloakbrowser_visible_text.txt") for path in paths)


def test_runner_records_the_content_retention_outcome(tmp_path, monkeypatch) -> None:
    _exit_code, output = _run_serp_capture(
        tmp_path, monkeypatch, visible_text=_VISIBLE_TEXT
    )
    metadata_path = next(
        path
        for path in (output / "raw").iterdir()
        if path.name.endswith("content_extraction_metadata.json")
    )
    metadata = json.loads(metadata_path.read_text())
    assert metadata["retention_outcome"] == "content"
    assert metadata["extractor_version"] == GOOGLE_SERP_CONTENT_RECORD_VERSION
    assert metadata["extraction_status"] == "succeeded"
    # The discarded bytes stay accounted for by hash even though they are gone.
    by_role = {entry["role"]: entry for entry in metadata["inputs"]}
    assert by_role["rendered_dom"]["preserved"] is False
    assert by_role["rendered_dom"]["sha256"]


def test_runner_preserves_raw_when_the_block_tripwire_fires(
    tmp_path, monkeypatch
) -> None:
    """The auto-fallback the whole flip depends on."""
    from runners.run_source_capture_cloakbrowser_packet import (
        CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    )

    exit_code, output = _run_serp_capture(
        tmp_path,
        monkeypatch,
        visible_text=(
            "Our systems have detected unusual traffic from your computer network."
        ),
    )
    assert exit_code == CONTENT_EXTRACTION_FAILED_EXIT_CODE
    paths = _preserved_paths(output)
    assert any(path.endswith("cloakbrowser_rendered_dom.html") for path in paths)
    assert any(path.endswith("cloakbrowser_visible_text.txt") for path in paths)
    assert not any(path.endswith("content_record.json") for path in paths)


def test_runner_preserves_raw_when_the_structural_tripwire_fires(
    tmp_path, monkeypatch
) -> None:
    from runners.run_source_capture_cloakbrowser_packet import (
        CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    )

    exit_code, output = _run_serp_capture(
        tmp_path, monkeypatch, visible_text="Google\nSearch\n"
    )
    assert exit_code == CONTENT_EXTRACTION_FAILED_EXIT_CODE
    paths = _preserved_paths(output)
    assert any(path.endswith("cloakbrowser_rendered_dom.html") for path in paths)
    assert any(path.endswith("cloakbrowser_visible_text.txt") for path in paths)
    assert not any(path.endswith("content_record.json") for path in paths)


def test_runner_raw_mode_stays_selectable_as_an_evidence_posture(
    tmp_path, monkeypatch
) -> None:
    exit_code, output = _run_serp_capture(
        tmp_path, monkeypatch, visible_text=_VISIBLE_TEXT, retention_mode="raw"
    )
    assert exit_code == 0
    paths = _preserved_paths(output)
    assert any(path.endswith("cloakbrowser_rendered_dom.html") for path in paths)
    assert not any(path.endswith("content_record.json") for path in paths)


def test_runner_writes_the_rolling_sample_only_for_the_first_capture(
    tmp_path, monkeypatch
) -> None:
    sample_root = tmp_path / "rolling-sample"
    _exit_code, _output = _run_serp_capture(
        tmp_path / "a",
        monkeypatch,
        visible_text=_VISIBLE_TEXT,
        raw_sample_root=sample_root,
    )
    store = RollingRawSampleStore(sample_root)
    assert len(store.current_samples()) == 1

    _exit_code, second_output = _run_serp_capture(
        tmp_path / "b",
        monkeypatch,
        visible_text=_VISIBLE_TEXT,
        raw_sample_root=sample_root,
    )
    assert len(store.current_samples()) == 1, "one sample per surface per day"
    metadata_path = next(
        path
        for path in (second_output / "raw").iterdir()
        if path.name.endswith("content_extraction_metadata.json")
    )
    sample_metadata = json.loads(metadata_path.read_text())["rolling_raw_sample"]
    assert sample_metadata["granted"] is False


def test_runner_rejects_a_sample_root_without_content_extraction(tmp_path) -> None:
    """A raw-retaining capture already keeps the bytes; sampling them is a lie."""
    from runners.run_source_capture_cloakbrowser_packet import (
        run_source_capture_cloakbrowser_packet,
    )
    from source_capture.models import CaptureModeCategory

    with pytest.raises(ValueError, match="content-enabled surface or profile"):
        run_source_capture_cloakbrowser_packet(
            url=_QUERY_URL,
            source_family="search_discovery",
            source_surface="google_serp_us_parameterized",
            decision_question="q",
            output_directory=tmp_path / "packet",
            capture_context="c",
            operator_category="researcher",
            capture_mode=CaptureModeCategory.MULTIMODAL,
            session_id=None,
            proxy_profile=None,
            actor_audience_context=None,
            visible_mode_changes=[],
            source_publication_or_event=None,
            source_edit_or_version=None,
            cutoff_posture=None,
            recapture_time=None,
            re_capture_relationship=None,
            warnings=[],
            limitations=[],
            timeout_seconds=20,
            wait_until="load",
            viewport_width=1280,
            viewport_height=720,
            max_artifact_bytes=200_000,
            block_heavy_assets=False,
            content_extraction=None,
            raw_sample_root=tmp_path / "sample",
        )


def test_cli_accepts_retention_mode_for_the_serp_surface_without_a_retail_profile(
    tmp_path, monkeypatch
) -> None:
    """The gate that previously required a retail aggregate profile."""
    import runners.run_source_capture_cloakbrowser_packet as cloakbrowser_runner

    captured: dict = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return 0, "ok"

    monkeypatch.setattr(
        cloakbrowser_runner, "run_source_capture_cloakbrowser_packet", fake_run
    )
    exit_code = cloakbrowser_runner.main(
        [
            "--url", _QUERY_URL,
            "--source-family", "search_discovery",
            "--source-surface", "google_serp_us_parameterized",
            "--decision-question", "What does this SERP surface?",
            "--output", str(tmp_path / "packet"),
            "--capture-context", "US-parameterized logged-out route",
            "--retention-mode", "content",
        ]
    )
    assert exit_code == 0
    spec = captured["content_extraction"]
    assert spec is not None
    assert spec.requested_retention_mode == "content"
    assert spec.extractor_version == GOOGLE_SERP_CONTENT_RECORD_VERSION


def test_cli_defaults_the_serp_surface_to_content_retention(
    tmp_path, monkeypatch
) -> None:
    """The flip itself: content is the default, not an opt-in flag."""
    import runners.run_source_capture_cloakbrowser_packet as cloakbrowser_runner

    captured: dict = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return 0, "ok"

    monkeypatch.setattr(
        cloakbrowser_runner, "run_source_capture_cloakbrowser_packet", fake_run
    )
    cloakbrowser_runner.main(
        [
            "--url", _QUERY_URL,
            "--source-family", "search_discovery",
            "--source-surface", "google_serp_us_parameterized",
            "--decision-question", "What does this SERP surface?",
            "--output", str(tmp_path / "packet"),
            "--capture-context", "US-parameterized logged-out route",
        ]
    )
    assert captured["content_extraction"].requested_retention_mode == "content"


def test_cli_rejects_a_mislabeled_google_serp_route(tmp_path, capsys) -> None:
    import runners.run_source_capture_cloakbrowser_packet as cloakbrowser_runner

    with pytest.raises(SystemExit) as raised:
        cloakbrowser_runner.main(
            [
                "--url", "https://example.test/search?q=summer+fridays",
                "--source-family", "search_discovery",
                "--source-surface", "google_serp_us_parameterized",
                "--decision-question", "What does this SERP surface?",
                "--output", str(tmp_path / "packet"),
                "--capture-context", "mislabeled route",
            ]
        )
    assert raised.value.code == 3
    assert "exactly hl=en, gl=us, and pws=0" in capsys.readouterr().err


def test_rolling_parity_gate_fails_when_a_banked_sample_is_incomplete(
    tmp_path, capsys
) -> None:
    import runners.run_capture_retention_parity_gate as parity_runner

    store = RollingRawSampleStore(tmp_path / "samples")
    claim = _write_sample(store, day=date(2026, 7, 28))
    assert claim.directory is not None
    (claim.directory / CONTENT_RECORD_SAMPLE_FILENAME).unlink()

    exit_code = parity_runner.main(
        [
            "rolling-sample",
            "--surface", "google_serp_us_parameterized",
            "--raw-sample-root", str(store.root),
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert result["verdicts"]["rolling_sample_integrity"] == "fail"


def test_cli_still_rejects_retention_mode_on_an_unenabled_surface(tmp_path) -> None:
    import runners.run_source_capture_cloakbrowser_packet as cloakbrowser_runner

    with pytest.raises(SystemExit) as raised:
        cloakbrowser_runner.main(
            [
                "--url", "https://example.test/page",
                "--source-family", "web_page",
                "--source-surface", "cloakbrowser_snapshot",
                "--decision-question", "q",
                "--output", str(tmp_path / "packet"),
                "--capture-context", "c",
                "--retention-mode", "content",
            ]
        )
    assert raised.value.code == 2


def test_unreadable_state_fails_loud_instead_of_guessing(tmp_path) -> None:
    store = RollingRawSampleStore(tmp_path)
    _write_sample(store, day=date(2026, 7, 28))
    store.state_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not readable JSON"):
        store.claim(
            surface="google_serp_us_parameterized", capture_date=date(2026, 7, 29)
        )
