"""Coverage flag: Bronze-writing capture runners must carry the Data Lake seam.

A runner that writes a SourceCapturePacket must either route into the lake
(``--data-root`` / ``data_root`` -> commit into the lake) or be explicitly
acknowledged as not-yet-synced. This is the enforced version of the manual
"which runners route into the lake?" survey.

The detector follows imported writer behavior from ``source_capture.*`` so new
thin wrappers such as ``write_asr_transcript`` or ``write_youtube_watch_packet``
cannot bypass the seam contract just because their name does not end in
``_packet`` or because they do not call ``stage_and_write_packet`` directly.

Discovery internals are single-sourced in ``data_lake.inventory`` (which also
feeds the A1 touchpoint inventory gate in
``test_data_lake_inventory_gate.py``); this test keeps its own assertion
baselines and imports discovery from the module. ``KNOWN_UNSYNCED`` (the
acknowledged-unsynced ledger, each entry with a reason),
``BRONZE_PACKET_ORCHESTRATORS``, and ``RUNNER_IDENTITY_BINDINGS`` (the
per-runner served-content-to-requested-subject binding declarations) are
declared there.
"""
from __future__ import annotations

import ast
from collections import Counter

from data_lake.inventory import (
    BRONZE_PACKET_ORCHESTRATORS,
    EXPLICIT_DATA_ROOT_RUNNERS,
    KNOWN_UNSYNCED,
    RUNNER_IDENTITY_BINDINGS,
    HARNESS_ROOT as _HARNESS_ROOT,
    RUNNERS_DIR as _RUNNERS_DIR,
    identity_binding_problems as _identity_binding_problems,
    bronze_writer_runners as _bronze_writer_runners,
    call_name as _call_name,
    calls_named as _calls_named,
    cli_flags as _cli_flags,
    environment_get_names as _environment_get_names,
    non_raw_lake_touchpoints as _non_raw_lake_touchpoints,
    packet_producers as _packet_producers,
    producer_calls as _producer_calls,
    source_capture_imports as _source_capture_imports,
    source_capture_packet_writer_names as _source_capture_packet_writer_names,
    tracked_harness_python_files as _tracked_harness_python_files,
)

# Current Bronze writer surface. This is the explicit audit answer for "which
# runners are supposed to write raw Bronze evidence?" Direct writers call a
# SourceCapturePacket writer. Orchestrators forward data_root into raw-packet
# sub-runners and are tested separately below.
EXPECTED_BRONZE_WRITER_RUNNERS = frozenset(
    {
        "run_basenotes_mgt_capture.py",
        "run_fragrance_review_lake_packet.py",
        "run_fragrantica_mgt_capture.py",
        "run_ig_reels_lane_orchestrator.py",
        "run_kohls_unattended_capture.py",
        "run_parfumo_mgt_capture.py",
        "run_reddit_subreddit_registry_lake.py",
        "run_source_capture_antiblock_http_packet.py",
        "run_source_capture_archive_packet.py",
        "run_source_capture_amazon_review_onboarding.py",
        "run_source_capture_ats_job_posting_packet.py",
        "run_source_capture_authenticated_browser_packet.py",
        "run_source_capture_browser_packet.py",
        "run_source_capture_cloakbrowser_packet.py",
        "run_source_capture_historical_packet.py",
        "run_source_capture_http_packet.py",
        "run_source_capture_ig_calls_packet.py",
        "run_source_capture_ig_reels_audio_packet.py",
        "run_source_capture_ig_reels_deep_capture.py",
        "run_source_capture_ig_reels_grid_packet.py",
        "run_source_capture_media_packet.py",
        "run_source_capture_packet.py",
        "run_source_capture_price_payload_packet.py",
        "run_source_capture_realchrome_cdp_packet.py",
        "run_source_capture_sephora_onboarding.py",
        "run_source_capture_target_onboarding.py",
        "run_source_capture_ulta_onboarding.py",
        "run_source_capture_tiktok_batch_packet.py",
        "run_source_capture_tiktok_grid_packet.py",
        "run_source_capture_tiktok_live_batch_probe.py",
        "run_source_capture_tiktok_creator_onboarding.py",
        "run_source_capture_tiktok_daily_heartbeat.py",
        "run_source_capture_tiktok_video_packet.py",
        "run_source_capture_youtube_asr_packet.py",
        "run_source_capture_youtube_caption_packet.py",
        "run_source_capture_youtube_creator_onboarding.py",
        "run_source_capture_youtube_rss_monitor.py",
        "run_source_capture_youtube_watch_packet.py",
    }
)

FORBIDDEN_RUNNER_RAW_PUBLICATION_CALLS = {
    "allocate_raw_packet_dir",
    "publish_raw_packet",
    "record_availability",
}

EXPECTED_NON_RAW_LAKE_TOUCHPOINTS = Counter(
    {
        (
            "capture_spine/creator_profile_current/social_metric_history_reader.py",
            "record_path",
        ): 1,
        ("capture_spine/creator_profile_current/silver_metric_producer.py", "append_silver_record"): 2,
        (
            "capture_spine/creator_profile_current/silver_metric_producer.py",
            "source_surface_catalog_rows",
        ): 1,
        ("capture_spine/creator_profile_current/silver_metric_reader.py", "lane_dir"): 3,
        (
            "capture_spine/tiktok_creator_discovery_frontier/register_lake_writer.py",
            "append_record",
        ): 2,
        (
            "capture_spine/tiktok_creator_discovery_frontier/register_lake_writer.py",
            "lane_dir",
        ): 2,
        (
            "capture_spine/creator_profile_current/tiktok_comment_attention_producer.py",
            "append_silver_record",
        ): 1,
        (
            "capture_spine/creator_profile_current/tiktok_comment_attention_producer.py",
            "record_path",
        ): 1,
        (
            "capture_spine/creator_profile_current/tiktok_grid_observation_producer.py",
            "append_silver_record",
        ): 2,
        (
            "capture_spine/creator_profile_current/tiktok_grid_observation_producer.py",
            "record_path",
        ): 2,
        (
            "runners/run_source_capture_tiktok_daily_heartbeat.py",
            "record_path",
        ): 1,
        (
            "capture_spine/creator_profile_current/youtube_silver_metric_producer.py",
            "append_silver_record",
        ): 2,
        (
            "capture_spine/creator_profile_current/youtube_silver_metric_producer.py",
            "source_surface_catalog_rows",
        ): 1,
        ("cleaning/basenotes_lake.py", "append_record"): 1,
        ("cleaning/basenotes_lake.py", "append_silver_record"): 1,
        ("cleaning/fragrantica_lake.py", "append_record"): 1,
        ("cleaning/fragrantica_lake.py", "append_silver_record"): 1,
        ("cleaning/parfumo_lake.py", "append_record"): 1,
        ("cleaning/parfumo_lake.py", "append_silver_record"): 1,
        ("data_lake/catalog.py", "inspect_catalog"): 2,
        ("data_lake/company_surface.py", "append_silver_record"): 1,
        ("data_lake/consumption.py", "append_record"): 1,
        ("data_lake/consumption.py", "lane_dir"): 1,
        ("data_lake/creator_audience_queue.py", "append_record"): 3,
        ("data_lake/creator_audience_queue.py", "record_path"): 3,
        ("data_lake/creator_registry.py", "append_record"): 4,
        ("data_lake/derived_retrieval_cache.py", "record_path"): 1,
        ("data_lake/product_mention_selection.py", "lane_dir"): 1,
        # Reddit Subreddit Registry lake cut-over: four append-only derived
        # writers (baseline, grid observation, agent-read reach observation,
        # roster change) plus one keyed lane read for the fold. Derived records
        # only -- no raw packet write, no manifest, no physicalization backend
        # implication.
        ("data_lake/reddit_subreddit_registry.py", "append_record"): 4,
        ("data_lake/reddit_subreddit_registry.py", "lane_dir"): 1,
        ("data_lake/silver_census.py", "is_record_set_complete"): 1,
        ("data_lake/silver_record.py", "append_record"): 1,
        ("data_lake/silver_record.py", "append_record_set"): 1,
        ("data_lake/silver_record.py", "append_silver_record"): 1,
        ("data_lake/silver_record.py", "load_attachment_record_body"): 1,
        ("data_lake/silver_record.py", "record_path"): 1,
        ("data_lake/silver_record.py", "source_surface_catalog_rows"): 1,
        ("ecr/lake.py", "append_record_set"): 1,
        ("runners/run_capture_ecr_cleaning_smoke.py", "lane_dir"): 1,
        ("runners/run_asr_transcript_catchup.py", "is_record_set_complete"): 1,
        ("runners/run_asr_transcript_catchup.py", "record_path"): 2,
        ("runners/run_data_lake_catalog.py", "catalog_coverage_census"): 1,
        ("runners/run_data_lake_catalog.py", "inspect_catalog"): 1,
        ("runners/run_data_lake_catalog.py", "rebuild_catalog"): 1,
        ("runners/run_ig_reels_lane_orchestrator.py", "is_record_set_complete"): 1,
        ("runners/run_ig_reels_product_extract.py", "is_record_set_complete"): 3,
        ("runners/run_ig_reels_product_extract.py", "record_path"): 1,
        ("runners/run_tiktok_product_extract.py", "is_record_set_complete"): 1,
        ("runners/run_tiktok_product_extract.py", "record_path"): 1,
        ("runners/run_instagram_creator_audience_triangulation.py", "append_record"): 1,
        ("runners/run_instagram_creator_audience_triangulation.py", "lane_dir"): 1,
        ("runners/run_instagram_creator_audience_triangulation.py", "record_path"): 2,
        ("runners/run_tiktok_creator_audience_triangulation.py", "append_record"): 2,
        ("runners/run_tiktok_creator_audience_triangulation.py", "lane_dir"): 1,
        ("runners/run_tiktok_creator_audience_triangulation.py", "record_path"): 3,
        ("runners/run_tiktok_creator_onboarding_coordinator.py", "lane_dir"): 1,
        ("runners/run_youtube_creator_audience_triangulation.py", "append_record"): 1,
        (
            "runners/run_youtube_creator_audience_triangulation.py",
            "is_record_set_complete",
        ): 2,
        ("runners/run_youtube_creator_audience_triangulation.py", "lane_dir"): 1,
        ("runners/run_youtube_creator_audience_triangulation.py", "record_path"): 2,
        ("cleaning/transcript_product_lake.py", "append_silver_record_set"): 1,
        ("runners/run_transcript_product_extract.py", "is_record_set_complete"): 1,
        ("runners/run_transcript_product_extract.py", "lane_dir"): 2,
        ("runners/run_transcript_product_extract.py", "record_path"): 1,
        ("signal_content/lake.py", "append_record"): 1,
        ("source_capture/ats_job_posting_projection.py", "append_record"): 1,
        ("source_capture/fragrance_review_lake.py", "append_record"): 1,
        ("source_capture/ig_projection.py", "append_record"): 1,
        ("source_capture/ig_reels_behavioral_lake.py", "is_record_set_complete"): 2,
        ("source_capture/ig_reels_behavioral_lake.py", "lane_dir"): 1,
        ("source_capture/ig_reels_behavioral_lake.py", "record_path"): 1,
        ("source_capture/ig_reels_deep_capture_lake.py", "append_silver_record_set"): 1,
        ("source_capture/ig_reels_grid_projection.py", "append_record"): 1,
        ("source_capture/ig_reels_grid_projection.py", "load_attachment_record_body"): 1,
        ("source_capture/ig_reels_grid_projection.py", "record_path"): 1,
        ("source_capture/ig_reels_grid_projection.py", "source_surface_catalog_rows"): 1,
        ("source_capture/retail_grid_projection.py", "append_record"): 1,
        ("source_capture/retail_pdp_silver.py", "append_silver_record"): 1,
        ("source_capture/transcript/asr_packet.py", "append_record_set"): 1,
        ("source_capture/transcript/ig_reels_audio_packet.py", "append_record"): 1,
        ("youtube_capture/behavioral_projection.py", "is_record_set_complete"): 1,
        ("youtube_capture/behavioral_projection.py", "lane_dir"): 1,
    }
)


def test_detector_follows_source_capture_module_import_packet_writer_alias() -> None:
    tree = ast.parse(
        """
import source_capture.youtube_watch_packet as ywp

def main(root):
    return ywp.write_youtube_watch_packet(fetch, data_root=root)
"""
    )

    writer_names, module_aliases = _source_capture_imports(tree)
    calls = _producer_calls(tree, writer_names, module_aliases)

    assert len(calls) == 1
    assert calls[0].name == "write_youtube_watch_packet"
    assert calls[0].forwards_data_root is True


def test_detector_follows_unaliased_source_capture_module_import_packet_writer() -> None:
    tree = ast.parse(
        """
import source_capture.youtube_watch_packet

def main(root):
    return source_capture.youtube_watch_packet.write_youtube_watch_packet(fetch, data_root=root)
"""
    )

    writer_names, module_aliases = _source_capture_imports(tree)
    calls = _producer_calls(tree, writer_names, module_aliases)

    assert len(calls) == 1
    assert calls[0].name == "write_youtube_watch_packet"
    assert calls[0].forwards_data_root is True


def test_detector_follows_from_imported_source_capture_module_packet_writer() -> None:
    tree = ast.parse(
        """
from source_capture import youtube_watch_packet

def main(root):
    return youtube_watch_packet.write_youtube_watch_packet(fetch, data_root=root)
"""
    )

    writer_names, module_aliases = _source_capture_imports(tree)
    calls = _producer_calls(tree, writer_names, module_aliases)

    assert len(calls) == 1
    assert calls[0].name == "write_youtube_watch_packet"
    assert calls[0].forwards_data_root is True


def test_detector_discovers_indirect_source_capture_packet_writers() -> None:
    writers = _source_capture_packet_writer_names()

    assert "write_asr_transcript" in writers
    assert "write_ig_reels_asr_transcript" in writers
    assert "write_caption_packet" in writers
    assert "write_youtube_watch_packet" in writers


def test_current_bronze_writer_runner_surface_is_explicit() -> None:
    assert _bronze_writer_runners() == EXPECTED_BRONZE_WRITER_RUNNERS


def test_scaffold_resolver_detector_rejects_non_executable_certification() -> None:
    """The scaffold-seam detector must require a real, reachable resolver call.

    Adversarial cases from the 2026-07-17 cross-vendor review: a comment
    mention, a shadowed binding, a call under a statically dead branch, or a
    call only inside an unused helper must not certify the seam; a genuine
    module-level import plus a reachable call inside ``main`` must.
    """
    from data_lake.inventory import uses_scaffold_resolver

    cases = {
        "real": (
            "from runners._scaffold import resolve_output_root\n"
            "def main():\n    root = resolve_output_root(args, parser, runner_name='x')\n",
            True,
        ),
        "comment_only": ("# resolve_output_root mentioned\ndef main():\n    pass\n", False),
        "shadowed": (
            "from runners._scaffold import resolve_output_root\n"
            "def main():\n    resolve_output_root = None\n    resolve_output_root()\n",
            False,
        ),
        "dead_branch": (
            "from runners._scaffold import resolve_output_root\n"
            "def main():\n    if False:\n        resolve_output_root(args, parser, runner_name='x')\n",
            False,
        ),
        "unused_helper": (
            "from runners._scaffold import resolve_output_root\n"
            "def helper():\n    resolve_output_root(args, parser, runner_name='x')\n"
            "def main():\n    pass\n",
            False,
        ),
        "reachable_constant_branch": (
            "from runners._scaffold import resolve_output_root\n"
            "def main():\n    if True:\n        resolve_output_root(args, parser, runner_name='x')\n",
            True,
        ),
    }
    mismatches = {
        name: got
        for name, (source, expected) in cases.items()
        if (got := uses_scaffold_resolver(ast.parse(source))) != expected
    }
    assert not mismatches, f"scaffold-seam detector misclassified: {mismatches}"


def test_non_raw_lake_touchpoint_inventory_is_explicit() -> None:
    actual = _non_raw_lake_touchpoints()
    added = +(actual - EXPECTED_NON_RAW_LAKE_TOUCHPOINTS)
    removed = +(EXPECTED_NON_RAW_LAKE_TOUCHPOINTS - actual)

    assert actual == EXPECTED_NON_RAW_LAKE_TOUCHPOINTS, (
        "Non-raw Data Lake touchpoint inventory changed. Classify each new or removed "
        "touchpoint before selecting Manifest v2, a manifest-equivalent index, or a "
        "physicalization backend.\n"
        f"added={dict(sorted(added.items()))}\n"
        f"removed={dict(sorted(removed.items()))}"
    )


def test_non_raw_lake_touchpoint_inventory_reads_tracked_source_only() -> None:
    relative_paths = {
        path.relative_to(_HARNESS_ROOT).as_posix() for path in _tracked_harness_python_files()
    }

    assert "data_lake/root.py" in relative_paths
    assert not any(path.startswith("tests/") for path in relative_paths)
    assert not any(path.startswith("_test_runs/") for path in relative_paths)


def test_detector_distinguishes_packet_output_from_summary_output_root() -> None:
    tree = ast.parse(
        """
def build_parser(parser):
    parser.add_argument("--output-root")
    parser.add_argument("--data-root")
"""
    )

    flags = _cli_flags(tree)

    assert "--output-root" in flags
    assert "--output" not in flags


def test_detector_requires_a_real_canonical_environment_read() -> None:
    help_text_only = ast.parse(
        'HELP = "Defaults to FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT)."'
    )
    legacy_only = ast.parse(
        'import os\nvalue = os.environ.get("ORCA_DATA_ROOT")'
    )
    canonical = ast.parse(
        'import os\nvalue = os.environ.get("FORSETI_DATA_ROOT")'
    )

    assert _environment_get_names(help_text_only) == set()
    assert _environment_get_names(legacy_only) == {"ORCA_DATA_ROOT"}
    assert _environment_get_names(canonical) == {"FORSETI_DATA_ROOT"}


def test_every_packet_runner_is_lake_wired_or_acknowledged() -> None:
    producers = _packet_producers()
    assert producers, "no packet-producing runners detected -- detection tokens are stale"

    unsynced = {name for name, seam in producers.items() if not seam.has_seam}

    new_unsynced = unsynced - set(KNOWN_UNSYNCED)
    assert not new_unsynced, (
        "Packet-producing runner(s) missing a real lake seam.\n"
        "Wire the seam (mirror run_source_capture_http_packet.py) OR add to KNOWN_UNSYNCED with a reason:\n"
        + "\n".join(
            f"  {name}: {', '.join(producers[name].missing_seam_parts())}"
            for name in sorted(new_unsynced)
        )
    )

    stale_ack = set(KNOWN_UNSYNCED) - unsynced
    assert not stale_ack, (
        "KNOWN_UNSYNCED lists runner(s) that now carry the seam (or are no longer packet producers).\n"
        "Remove them from KNOWN_UNSYNCED:\n"
        f"  {sorted(stale_ack)}"
    )


def test_packet_runner_output_modes_are_exclusive() -> None:
    producers = _packet_producers()
    ambiguous = {
        name: seam.missing_output_mode_parts()
        for name, seam in producers.items()
        if name not in KNOWN_UNSYNCED and not seam.has_exclusive_output_mode
    }

    assert not ambiguous, (
        "Packet-producing runner(s) with --output must keep local-output and lake-output modes exclusive: "
        f"{ambiguous}"
    )


def test_known_unsynced_entries_have_reasons() -> None:
    missing = [name for name, reason in KNOWN_UNSYNCED.items() if not reason.strip()]
    assert not missing, f"KNOWN_UNSYNCED entries need a reason: {missing}"


def test_explicit_data_root_runner_declarations_are_current_and_reasoned() -> None:
    producers = _packet_producers()
    missing_reasons = [
        name for name, reason in EXPLICIT_DATA_ROOT_RUNNERS.items() if not reason.strip()
    ]
    stale = sorted(set(EXPLICIT_DATA_ROOT_RUNNERS) - set(producers))
    misclassified = sorted(
        name
        for name in EXPLICIT_DATA_ROOT_RUNNERS
        if name in producers
        and (
            not producers[name].explicit_data_root_only
            or producers[name].exposes_env_fallback
        )
    )

    assert not missing_reasons, (
        f"EXPLICIT_DATA_ROOT_RUNNERS entries need a reason: {missing_reasons}"
    )
    assert not stale, f"explicit-root-only declarations are stale: {stale}"
    assert not misclassified, (
        "explicit-root-only runners must not be credited with ambient "
        f"FORSETI_DATA_ROOT fallback: {misclassified}"
    )


def test_every_bronze_writer_runner_declares_identity_binding() -> None:
    runners = _bronze_writer_runners()
    missing = sorted(runners - set(RUNNER_IDENTITY_BINDINGS))
    assert not missing, (
        "Bronze-writing runner(s) without an identity_binding declaration.\n"
        "Every capture runner must answer, at build time, how it binds served content "
        "to the requested subject (F-01, docs/review-outputs/"
        "youtube_rss_monitor_delegated_adversarial_code_review_v0.md): add a "
        "bound/unbound/not_applicable entry to RUNNER_IDENTITY_BINDINGS in "
        "data_lake/inventory.py for:\n"
        f"  {missing}"
    )

    stale = sorted(set(RUNNER_IDENTITY_BINDINGS) - runners)
    assert not stale, (
        "RUNNER_IDENTITY_BINDINGS lists runner(s) that are no longer Bronze writers.\n"
        f"Remove the stale declarations: {stale}"
    )


def test_runner_identity_binding_declarations_are_shape_valid() -> None:
    problems = {
        runner: issues
        for runner, binding in sorted(RUNNER_IDENTITY_BINDINGS.items())
        for issues in [_identity_binding_problems(binding)]
        if issues
    }
    assert not problems, (
        "identity_binding declaration(s) with shape problems (bound requires a "
        f"mechanism; unbound/not_applicable require a reason): {problems}"
    )


def test_packet_runner_lake_seams_reach_packet_writers() -> None:
    producers = _packet_producers()
    missing = {
        name: [
            f"{call.name} line {call.line}"
            for call in seam.producer_calls
            if not call.forwards_data_root
        ]
        for name, seam in producers.items()
        if name not in KNOWN_UNSYNCED
    }
    missing = {name: calls for name, calls in missing.items() if calls}

    assert not missing, (
        "Packet-producing runner(s) expose a lake seam but do not forward data_root= "
        f"into every packet writer call: {missing}"
    )


def test_bronze_packet_orchestrators_forward_data_root_to_subrunners() -> None:
    missing: dict[str, list[str]] = {}
    for filename, callee_names in BRONZE_PACKET_ORCHESTRATORS.items():
        path = _RUNNERS_DIR / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls = _calls_named(tree, callee_names)
        problems = [
            f"{_call_name(call)} line {call.lineno}"
            for call in calls
            if not any(keyword.arg == "data_root" for keyword in call.keywords)
        ]
        if not calls:
            problems.append(f"no calls found for {callee_names!r}")
        if problems:
            missing[filename] = problems

    assert not missing, (
        "Bronze packet orchestrator(s) must forward data_root= to raw-packet subrunners: "
        f"{missing}"
    )


def test_bronze_writers_do_not_directly_publish_raw_packets() -> None:
    offenders: dict[str, list[str]] = {}
    for filename in sorted(_bronze_writer_runners()):
        path = _RUNNERS_DIR / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits = [
            f"{_call_name(node)} line {node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _call_name(node) in FORBIDDEN_RUNNER_RAW_PUBLICATION_CALLS
        ]
        if hits:
            offenders[filename] = hits

    assert not offenders, (
        "Bronze writer runner(s) must not publish/mark raw packets directly; "
        "route raw commits through source_capture.writer or packet_assembly: "
        f"{offenders}"
    )
