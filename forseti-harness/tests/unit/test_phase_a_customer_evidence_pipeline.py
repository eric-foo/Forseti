from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from types import SimpleNamespace

import pytest

import source_capture.phase_a_customer_evidence_pipeline as pipeline
from runners import run_phase_a_customer_evidence_pipeline as pipeline_cli


ATTESTED_AT = "2026-08-04T12:28:50.331Z"


def _family(kind: str, index: int, *, query: str | None = None) -> dict:
    family_id = f"F{index:02d}-{kind}"
    query = query or f'Dieux Skin {kind.replace("_", " ")}'
    return {
        "schema_version": pipeline.FAMILY_MANIFEST_VERSION,
        "family_id": family_id,
        "family_kind": kind,
        "axis_scope": ["reaction_irritation", "strongest_delight"],
        "rationale": f"Exercise {kind} against the open Dieux axes.",
        "jobs": [
            {
                "job_id": f"G{index:03d}",
                "family_id": family_id,
                "family_kind": kind,
                "query": query,
                "url": pipeline.build_google_url(query),
                "selected_type": "subject",
                "selected_name": "Dieux Skin",
                "shape": "phase_a_customer_evidence",
            }
        ],
    }


def _config(*, families: list[dict] | None = None) -> dict:
    return {
        "schema_version": pipeline.CONFIG_VERSION,
        "run_id": "dieux-phase-a-pipeline-001",
        "commission_id": "BEAUTY-DIEUX-PHASEA-PIPELINE-DOGFOOD-001",
        "subject_id": "dieux_skin",
        "decision_question": "What pains and delights are decision-material for Dieux Skin?",
        "country": "US",
        "language": "en",
        "locale": "en-US",
        "artifact_root": "C:/tmp/dieux-phase-a",
        "rotating_ip_operator_enabled": True,
        "operator_attested_at": ATTESTED_AT,
        "query_families": families
        or [
            _family(kind, index)
            for index, kind in enumerate(pipeline.MANDATORY_FAMILY_KINDS, start=1)
        ],
        "google_route": {
            "runner": "cloakbrowser_google_serp_queue",
            "cadence_rung": 8,
            "jitter_seconds_min": -0.5,
            "jitter_seconds_max": 0.5,
            "persistent_fallback_enabled": True,
            "persistent_cdp_endpoint": "http://localhost:9222",
            "persistent_session_profile": "chowdakr_sg_tiktok",
            "persistent_tab_marker": "dieux-google",
        },
        "reddit_route": {
            "runner": "realchrome_cdp_persistent_tab",
            "cdp_endpoint": "http://localhost:9333",
            "persistent_tab_marker": "dieux-reddit",
            "pacing_seconds_min": 44,
            "pacing_seconds_max": 61,
            "first_cooldown_seconds": 1200,
        },
    }


def _init(tmp_path: Path, *, config: dict | None = None) -> Path:
    config_path = tmp_path / "input-config.json"
    config_path.write_text(json.dumps(config or _config()), encoding="utf-8")
    run_root = tmp_path / "run"
    pipeline.initialize_pipeline(config_path=config_path, run_root=run_root)
    return run_root


def test_cli_init_and_status_smoke_under_local_fixture(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config()), encoding="utf-8")
    run_root = tmp_path / "cli-run"

    assert pipeline_cli.main(
        ["init", "--config", str(config_path), "--run-root", str(run_root)]
    ) == 0
    assert pipeline_cli.main(["status", "--run-root", str(run_root)]) == 0

    output = capsys.readouterr().out
    assert pipeline.STATE_VERSION in output
    assert "dieux-phase-a-pipeline-001" in output


def test_process_guard_rejects_a_second_controller_for_same_run_root(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)

    with pipeline._process_run_guard(paths):
        with pytest.raises(
            pipeline.PipelineBlocked, match="BLOCKED_CONCURRENT_PIPELINE_PROCESS"
        ):
            with pipeline._process_run_guard(paths):
                raise AssertionError("second controller must not acquire the lock")


def _write_google_packet(output: Path, *, url: str, comments: int | None = 8) -> None:
    output.mkdir(parents=True, exist_ok=True)
    row = {
        "platform": "reddit",
        "canonical_url": url,
        "title": "Dieux discussion",
        "snippet": "source result",
    }
    if comments is not None:
        row["comments"] = comments
    query = pipeline._read_json(output.parent.parent / "jobs.json", label="jobs")["jobs"][0]["query"]
    requested = pipeline.build_google_url(query)
    (output / "content_record.json").write_text(
        json.dumps(
            {
                "content_record_version": "google_serp_content_v3",
                "requested_url": requested,
                "final_url": requested,
                "rows": [row],
            }
        ),
        encoding="utf-8",
    )


def _candidate_state(run_root: Path, *, comments: int | None = 8) -> tuple[dict, str]:
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    job = state["families"][0]["jobs"][0]
    packet = run_root / "fixture-packet"
    packet.mkdir()
    url = "https://www.reddit.com/r/SkincareAddictionLux/comments/1ovsqzr/dieuxspecific_irritation/"
    record = {
        "content_record_version": "google_serp_content_v3",
        "requested_url": job["url"],
        "final_url": job["url"],
        "rows": [{"canonical_url": url, "platform": "reddit", "comments": comments}],
    }
    (packet / "content_record.json").write_text(json.dumps(record), encoding="utf-8")
    ids = pipeline.ingest_google_packet(state=state, job=job, packet_locator=packet)
    pipeline._save_state(paths, state)
    return state, ids[0]


def _decision(candidate_id: str, url: str, *, admission: str = "yes") -> dict:
    return {
        "candidate_id": candidate_id,
        "policy_version": pipeline.POLICY_VERSION,
        "decision_frame": "Dieux Skin Phase A internal dogfood",
        "thread_url": url,
        "listing_snapshot": {"captured_at": ATTESTED_AT, "score": 4, "comments": 8},
        "admission": admission,
        "reason_codes": ["product_specific_decision_promise"],
        "priority_band": "suppressed" if admission == "no" else "high",
    }


def _import_one(run_root: Path, candidate_id: str) -> None:
    state = pipeline.inspect_pipeline(run_root=run_root)
    path = run_root.parent / "decisions.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": pipeline.DECISIONS_VERSION,
                "decisions": [_decision(candidate_id, state["candidates"][candidate_id]["canonical_url"])],
            }
        ),
        encoding="utf-8",
    )
    pipeline.import_decisions(run_root=run_root, decisions_path=path)


def test_config_requires_the_mandatory_family_order(tmp_path: Path) -> None:
    config = _config()
    config["query_families"][0], config["query_families"][1] = (
        config["query_families"][1],
        config["query_families"][0],
    )
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(pipeline.PipelineError, match="first four family kinds"):
        pipeline.load_config(path)


@pytest.mark.parametrize(
    "change,match",
    [
        (("locale", "en-GB"), "locale"),
        (("access_token", "do-not-store"), "forbidden"),
        (("vpn_server", "us-sfo-1"), "forbidden"),
    ],
)
def test_config_rejects_locale_drift_missing_attestation_and_secrets(
    tmp_path: Path, change: tuple[str, object], match: str
) -> None:
    config = _config()
    config[change[0]] = change[1]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(pipeline.PipelineError, match=match):
        pipeline.load_config(path)


def test_missing_attestation_allows_offline_init_but_blocks_before_capture(
    tmp_path: Path,
) -> None:
    config = _config()
    config["rotating_ip_operator_enabled"] = False
    config["operator_attested_at"] = None
    run_root = _init(tmp_path, config=config)
    called = False

    def capture(*_args):
        nonlocal called
        called = True
        raise AssertionError("capture must not start")

    result = pipeline.run_pipeline(run_root=run_root, capture=capture)

    assert called is False
    assert result["terminal_reason"] == "BLOCKED_ROTATING_IP_ATTESTATION_MISSING"


@pytest.mark.parametrize(
    "google_endpoint,reddit_endpoint",
    [
        # Byte-identical spellings.
        ("http://localhost:9222", "http://localhost:9222"),
        # One loopback listener reached under three equivalent spellings and
        # two schemes: still one Chrome, so still shared concurrency.
        ("http://localhost:9222", "http://127.0.0.1:9222"),
        ("http://127.0.0.1:9222", "http://localhost:9222"),
        ("http://127.0.0.1:9222", "http://[::1]:9222"),
        ("http://127.0.0.1:9222", "https://127.0.0.1:9222"),
    ],
)
def test_config_requires_distinct_browser_endpoints(
    tmp_path: Path, google_endpoint: str, reddit_endpoint: str
) -> None:
    config = _config()
    config["google_route"]["persistent_cdp_endpoint"] = google_endpoint
    config["reddit_route"]["cdp_endpoint"] = reddit_endpoint
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(pipeline.PipelineError, match="BLOCKED_SHARED_CDP_CONCURRENCY"):
        pipeline.load_config(path)


def test_config_admits_distinct_loopback_ports(tmp_path: Path) -> None:
    config = _config()
    config["google_route"]["persistent_cdp_endpoint"] = "http://localhost:9222"
    config["reddit_route"]["cdp_endpoint"] = "http://127.0.0.1:9333"
    path = tmp_path / "good.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    assert pipeline.load_config(path)["reddit_route"]["cdp_endpoint"] == (
        "http://127.0.0.1:9333"
    )


def test_persistent_google_route_passes_session_profile_to_cold_start_runner(
    tmp_path: Path, monkeypatch
) -> None:
    commands: list[list[str]] = []

    def run(command, **_kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(pipeline.subprocess, "run", run)
    action = {
        "route": pipeline.PERSISTENT_ROUTE,
        "job": {
            "url": pipeline.build_google_url("Dieux Skin reviews"),
            "query": "Dieux Skin reviews",
            "job_id": "G001",
        },
    }

    result = pipeline._execute_capture(
        "google",
        action,
        _config(),
        tmp_path / "packet",
    )

    assert result.outcome == "success"
    assert len(commands) == 1
    command = commands[0]
    assert command[command.index("--session-profile") + 1] == "chowdakr_sg_tiktok"
    assert command[command.index("--cdp-endpoint") + 1] == "http://localhost:9222"


def test_reddit_cdp_connection_refused_is_a_transport_interruption(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        pipeline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=6,
            stdout="",
            stderr="BrowserType.connect_over_cdp: connect ECONNREFUSED 127.0.0.1:9333",
        ),
    )

    result = pipeline._execute_capture(
        "reddit",
        {"url": "https://old.reddit.com/r/Test/comments/abc123/a/"},
        _config(),
        tmp_path / "packet",
    )

    assert result.outcome == "transport_interruption"


def test_reddit_zero_exit_with_access_block_metadata_opens_challenge_path(
    tmp_path: Path, monkeypatch
) -> None:
    output = tmp_path / "packet"
    raw = output / "raw"
    raw.mkdir(parents=True)
    (raw / "04_04_realchrome_snapshot_metadata.json").write_text(
        json.dumps(
            {
                "access_blocked": True,
                "access_block_reason": "reddit_network_security_block",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pipeline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=str(output), stderr=""
        ),
    )

    result = pipeline._execute_capture(
        "reddit",
        {"url": "https://old.reddit.com/r/Test/comments/abc123/a/"},
        _config(),
        output,
    )

    assert result.outcome == "challenge"
    assert result.detail == "reddit_network_security_block"
    assert result.packet_locator == str(output.resolve())


def test_reddit_zero_exit_login_redirect_opens_challenge_even_when_flag_is_false(
    tmp_path: Path, monkeypatch
) -> None:
    output = tmp_path / "packet"
    raw = output / "raw"
    raw.mkdir(parents=True)
    (raw / "04_04_realchrome_snapshot_metadata.json").write_text(
        json.dumps(
            {
                "access_blocked": False,
                "access_block_reason": None,
                "requested_url": "https://old.reddit.com/r/Test/comments/abc123/a/",
                "final_url": (
                    "https://old.reddit.com/login/?reason=lor2&dest="
                    "https%3A%2F%2Fold.reddit.com%2Fr%2FTest%2Fcomments%2Fabc123%2Fa%2F"
                ),
                "title": "Welcome to Reddit",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pipeline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=str(output), stderr=""
        ),
    )

    result = pipeline._execute_capture(
        "reddit",
        {"url": "https://old.reddit.com/r/Test/comments/abc123/a/"},
        _config(),
        output,
    )

    assert result.outcome == "challenge"
    assert result.detail == "reddit_thread_not_reached"
    assert result.packet_locator == str(output.resolve())


def _reddit_metadata_packet(output: Path, metadata: dict) -> Path:
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text("{}", encoding="utf-8")
    (raw / "04_04_realchrome_snapshot_metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )
    return output


THREAD_URL = "https://old.reddit.com/r/Test/comments/abc123/a/"


@pytest.mark.parametrize(
    "final_url,expected",
    [
        # Login wall across every permitted host and slash/query variant.
        ("https://old.reddit.com/login", "reddit_thread_not_reached"),
        ("https://old.reddit.com/login/", "reddit_thread_not_reached"),
        ("https://www.reddit.com/login/?dest=%2Fr%2FTest", "reddit_thread_not_reached"),
        ("https://reddit.com/Login", "reddit_thread_not_reached"),
        ("https://new.reddit.com/login?reason=lor2", "reddit_thread_not_reached"),
        # Any other page that is not the requested thread.
        ("https://old.reddit.com/r/Test/", "reddit_thread_not_reached"),
        ("https://old.reddit.com/", "reddit_thread_not_reached"),
        ("https://old.reddit.com/r/Test/comments/zzz999/other/", "reddit_thread_not_reached"),
        ("https://example.com/anything", "reddit_thread_not_reached"),
        # The requested thread itself, including host and slug drift, is admitted.
        (THREAD_URL, None),
        ("https://www.reddit.com/r/Test/comments/abc123/renamed_slug/", None),
    ],
)
def test_reddit_success_credit_requires_landing_on_the_requested_thread(
    tmp_path: Path, final_url: str, expected: str | None
) -> None:
    packet = _reddit_metadata_packet(
        tmp_path / "packet",
        {
            "access_blocked": False,
            "access_block_reason": None,
            "requested_url": THREAD_URL,
            "final_url": final_url,
        },
    )

    assert pipeline._packet_access_block_reason(packet, worker="reddit") == expected


@pytest.mark.parametrize(
    "metadata,expected",
    [
        ({"requested_url": THREAD_URL}, "reddit_access_verdict_unavailable"),
        ({"final_url": THREAD_URL}, "reddit_access_verdict_unavailable"),
        (
            {"requested_url": None, "final_url": THREAD_URL},
            "reddit_access_verdict_unavailable",
        ),
        (
            {"requested_url": "not-a-thread", "final_url": THREAD_URL},
            "reddit_access_verdict_unavailable",
        ),
    ],
)
def test_reddit_unreadable_access_verdict_never_earns_success_credit(
    tmp_path: Path, metadata: dict, expected: str
) -> None:
    packet = _reddit_metadata_packet(tmp_path / "packet", metadata)

    assert pipeline._packet_access_block_reason(packet, worker="reddit") == expected


def test_reddit_packet_without_snapshot_metadata_is_blocked(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    (packet / "raw").mkdir(parents=True)
    (packet / "manifest.json").write_text("{}", encoding="utf-8")

    assert pipeline._packet_access_block_reason(packet, worker="reddit") == (
        "reddit_access_verdict_unavailable"
    )


def test_reddit_packet_with_ambiguous_snapshot_metadata_is_blocked(
    tmp_path: Path,
) -> None:
    packet = tmp_path / "packet"
    raw = packet / "raw"
    raw.mkdir(parents=True)
    for name in (
        "04_04_realchrome_snapshot_metadata.json",
        "05_05_realchrome_snapshot_metadata.json",
    ):
        (raw / name).write_text(
            json.dumps(
                {
                    "access_blocked": True,
                    "access_block_reason": "reddit_network_security_block",
                }
            ),
            encoding="utf-8",
        )

    assert pipeline._packet_access_block_reason(packet, worker="reddit") == (
        "reddit_access_verdict_ambiguous"
    )


def test_google_packet_without_realchrome_metadata_stays_admissible(
    tmp_path: Path,
) -> None:
    """The automated Google route writes no RealChrome metadata; it must not block."""
    packet = tmp_path / "packet"
    packet.mkdir()
    (packet / "content_record.json").write_text("{}", encoding="utf-8")

    assert pipeline._packet_access_block_reason(packet, worker="google") is None


def test_persistent_realchrome_packet_is_normalized_offline_for_ingestion(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    job = state["families"][0]["jobs"][0]
    packet = run_root / "persistent-packet"
    raw = packet / "raw"
    raw.mkdir(parents=True)
    thread_urls = [
        "https://www.reddit.com/r/Test/comments/abc001/thread_one/",
        "https://old.reddit.com/r/Test/comments/abc002/thread_two/",
        "https://new.reddit.com/r/Test/comments/abc003/thread_three/",
    ]
    (packet / "manifest.json").write_text(
        json.dumps({"source_surface": "google_serp_us_parameterized_realchrome_cdp"}),
        encoding="utf-8",
    )
    (raw / "01_01_realchrome_rendered_dom.html").write_text(
        "<html><body>"
        + "".join(
            f'<a href="{url}"><h3>Dieux Thread {index}</h3></a>'
            for index, url in enumerate(thread_urls, start=1)
        )
        + "</body></html>",
        encoding="utf-8",
    )
    cards = []
    for index in range(1, 4):
        cards.append(
            "\n".join(
                [
                    f"Dieux Thread {index}",
                    "Reddit",
                    "https://www.reddit.com › r › Test",
                    f"{index + 3} comments",
                ]
            )
        )
    visible = (
        ("Rendered Google result context. " * 24)
        + "\nSearch Results\nWeb results\n"
        + "\n\n".join(cards)
        + "\nPage Navigation\n"
    )
    (raw / "02_02_realchrome_visible_text.txt").write_text(visible, encoding="utf-8")
    (raw / "04_04_realchrome_snapshot_metadata.json").write_text(
        json.dumps({"requested_url": job["url"], "final_url": job["url"]}),
        encoding="utf-8",
    )

    discovered = pipeline.ingest_google_packet(
        state=state, job=job, packet_locator=packet
    )

    assert len(discovered) == 3
    assert len(state["candidates"]) == 3
    assert sorted(item["visible_comment_count"] for item in state["candidates"].values()) == [4, 5, 6]
    assert all(
        item["status"] == "adjudication_pending"
        for item in state["candidates"].values()
    )


@pytest.mark.parametrize("host", ["www.reddit.com", "old.reddit.com", "new.reddit.com", "reddit.com"])
def test_thread_identity_canonicalizes_all_reddit_hosts(host: str) -> None:
    result = pipeline.canonical_reddit_thread(
        f"https://{host}/r/SkincareAddictionLux/comments/1OvSqZr/dieuxspecific_irritation/"
    )

    assert result == {
        "canonical_thread_id": "1ovsqzr",
        "canonical_url": "https://old.reddit.com/r/SkincareAddictionLux/comments/1ovsqzr/dieuxspecific_irritation/",
        "subreddit": "SkincareAddictionLux",
    }


def test_serp_ingestion_deduplicates_and_preserves_every_discovery(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    packet = run_root / "packet"
    packet.mkdir()
    first, second = state["families"][0]["jobs"][0], state["families"][1]["jobs"][0]
    record = {
        "content_record_version": "google_serp_content_v3",
        "requested_url": first["url"],
        "final_url": first["url"],
        "rows": [
            {
                "canonical_url": "https://www.reddit.com/r/Test/comments/abc123/a/",
                "platform": "reddit",
                "comments": 9,
            },
            {
                "canonical_url": "https://old.reddit.com/r/Test/comments/abc123/a/",
                "platform": "reddit",
                "comments": 9,
            },
        ],
    }
    (packet / "content_record.json").write_text(json.dumps(record), encoding="utf-8")
    pipeline.ingest_google_packet(state=state, job=first, packet_locator=packet)
    record["requested_url"] = record["final_url"] = second["url"]
    (packet / "content_record.json").write_text(json.dumps(record), encoding="utf-8")
    pipeline.ingest_google_packet(state=state, job=second, packet_locator=packet)

    assert len(state["candidates"]) == 1
    candidate = next(iter(state["candidates"].values()))
    assert [item["job_id"] for item in candidate["discoveries"]] == ["G001", "G001", "G002", "G002"]


@pytest.mark.parametrize(
    "comments,status",
    [(0, "mechanical_no"), (3, "mechanical_no"), (4, "adjudication_pending"), (None, "borderline_pending")],
)
def test_mechanical_listing_floor(comments: int | None, status: str, tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    state, candidate_id = _candidate_state(run_root, comments=comments)

    assert state["candidates"][candidate_id]["status"] == status


def test_mechanical_listing_floor_reads_google_plus_comment_lower_bound() -> None:
    assert pipeline._visible_comment_count({"engagement_snippet": "40+ comments"}) == 40


def test_decision_import_releases_capture_immediately(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    _, candidate_id = _candidate_state(run_root)

    _import_one(run_root, candidate_id)

    state = pipeline.inspect_pipeline(run_root=run_root)
    assert state["candidates"][candidate_id]["status"] == "capture_pending"
    assert state["reddit_queue"][0]["candidate_id"] == candidate_id
    assert state["reddit_queue"][0]["status"] == "pending"


def test_decision_batch_cannot_exceed_21_rows(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    path = tmp_path / "too-many.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": pipeline.DECISIONS_VERSION,
                "decisions": [{} for _ in range(22)],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(pipeline.PipelineError, match="at most 21"):
        pipeline.import_decisions(run_root=run_root, decisions_path=path)


def test_emitted_decision_batches_are_capped_at_21_rows(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    state = pipeline.inspect_pipeline(run_root=run_root)
    family_id = state["families"][0]["family_id"]
    for index in range(22):
        candidate_id = f"candidate_{index:02d}"
        state["candidates"][candidate_id] = {
            "status": "adjudication_pending",
            "discoveries": [{"family_id": family_id}],
        }

    pipeline._flush_full_adjudication_batches(state, family_id=family_id)
    assert [len(batch["candidate_ids"]) for batch in state["adjudication_batches"]] == [21]

    pipeline._flush_adjudication_batch(state, family_id=family_id)
    assert [len(batch["candidate_ids"]) for batch in state["adjudication_batches"]] == [21, 1]


def test_append_family_requires_hash_pinned_coding_receipt(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    family = _family("pain_continuation", 5)
    family["authorization_receipt"] = {
        "path": str(tmp_path / "missing.json"),
        "sha256": "0" * 64,
        "axis_scope": family["axis_scope"],
        "rationale": family["rationale"],
    }
    manifest = tmp_path / "family.json"
    manifest.write_text(json.dumps(family), encoding="utf-8")

    with pytest.raises(pipeline.PipelineError, match="missing or hash-mismatched"):
        pipeline.append_family(run_root=run_root, manifest_path=manifest)


def test_append_family_updates_google_queue_from_valid_receipt(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    receipt = tmp_path / "coding-receipt.json"
    receipt.write_text('{"axis":"reaction_irritation"}\n', encoding="utf-8")
    family = _family("pain_continuation", 5)
    family["authorization_receipt"] = {
        "path": str(receipt),
        "sha256": pipeline.hash_file(receipt),
        "axis_scope": family["axis_scope"],
        "rationale": family["rationale"],
    }
    manifest = tmp_path / "family.json"
    manifest.write_text(json.dumps(family), encoding="utf-8")

    state = pipeline.append_family(run_root=run_root, manifest_path=manifest)

    assert state["families"][-1]["family_kind"] == "pain_continuation"
    assert state["google_queue"]["jobs"][-1]["job_id"] == "G005"


def test_timing_math_uses_union_overlap_and_serial_counterfactual() -> None:
    state = {
        "timing": {
            "co3_started_at": "2026-08-04T00:00:00Z",
            "co3_finished_at": "2026-08-04T00:01:40Z",
            "google_intervals": [
                {"start": "2026-08-04T00:00:00Z", "end": "2026-08-04T00:01:00Z"},
                {"start": "2026-08-04T00:00:50Z", "end": "2026-08-04T00:01:10Z"},
            ],
            "reddit_intervals": [
                {"start": "2026-08-04T00:00:40Z", "end": "2026-08-04T00:01:20Z"},
            ],
        }
    }

    metrics = pipeline.timing_metrics(state)

    assert metrics["actual_co3_elapsed_seconds"] == 100
    assert metrics["cross_host_overlap_seconds"] == 30
    assert metrics["serial_counterfactual_seconds"] == 130
    assert metrics["reduction"] == pytest.approx(1 - 100 / 130)
    assert metrics["google_active_seconds"] == 70
    assert metrics["reddit_active_seconds"] == 40


def test_unknown_in_flight_resume_is_inspected_once_then_blocks(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    state["in_flight"]["reddit"] = {
        "capture_id": "capture_unknown",
        "candidate_id": "candidate_unknown",
        "output": str(run_root / "missing-packet"),
        "started_at": ATTESTED_AT,
    }
    pipeline._save_state(paths, state)

    with pytest.raises(pipeline.PipelineBlocked, match="BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"):
        pipeline.run_pipeline(run_root=run_root)

    blocked = pipeline.inspect_pipeline(run_root=run_root)
    assert blocked["terminal_reason"] == "BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"
    assert blocked["in_flight_inspections"]["capture_unknown"]


def test_resume_reconciles_google_packet_already_settled_by_queue(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    job = state["families"][0]["jobs"][0]
    output = paths.google_packets / job["job_id"]
    output.mkdir(parents=True)
    (output / "manifest.json").write_text("{}", encoding="utf-8")
    (output / "content_record.json").write_text(
        json.dumps(
            {
                "content_record_version": "google_serp_content_v3",
                "requested_url": job["url"],
                "final_url": job["url"],
                "rows": [
                    {
                        "canonical_url": "https://www.reddit.com/r/Test/comments/abc123/a/",
                        "platform": "reddit",
                        "engagement_snippet": "40+ comments",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    action = pipeline.next_action(
        state_path=paths.google_state,
        now=datetime(2026, 8, 4, 13, 0, tzinfo=UTC),
    )
    pipeline.report_outcome(
        state_path=paths.google_state,
        job_id=job["job_id"],
        route=action["route"],
        outcome="success",
        packet_locator=str(output),
        now=datetime(2026, 8, 4, 13, 1, tzinfo=UTC),
    )
    state["status"] = "blocked"
    state["terminal_reason"] = "worker_failure:PipelineBlocked:normalization gap"
    state["in_flight"]["google"] = {
        "job_id": job["job_id"],
        "route": action["route"],
        "output": str(output),
        "started_at": "2026-08-04T13:00:00.000000Z",
    }
    pipeline._save_state(paths, state)

    pipeline._reconcile_in_flight(paths)

    recovered = pipeline._load_state(paths)
    assert recovered["status"] == "interrupted_resumable"
    assert recovered["terminal_reason"] is None
    assert recovered["in_flight"]["google"] is None
    candidate = next(iter(recovered["candidates"].values()))
    assert candidate["visible_comment_count"] == 40
    assert recovered["timing"]["google_intervals"] == [
        {
            "start": "2026-08-04T13:00:00.000000Z",
            "end": "2026-08-04T13:01:00Z",
            "job_id": job["job_id"],
        }
    ]


def _held_reddit_capture(run_root: Path, final_url: str) -> tuple[Path, str, str]:
    """Park one admitted Reddit item in flight with a terminal packet on disk."""
    paths = pipeline.pipeline_paths(run_root)
    _, candidate_id = _candidate_state(run_root)
    _import_one(run_root, candidate_id)
    state = pipeline._load_state(paths)
    job = state["reddit_queue"][0]
    job["status"] = "in_flight"
    output = paths.reddit_packets / job["capture_id"]
    _reddit_metadata_packet(
        output,
        {
            "access_blocked": False,
            "access_block_reason": None,
            "requested_url": state["candidates"][candidate_id]["canonical_url"],
            "final_url": final_url,
        },
    )
    state["in_flight"]["reddit"] = {
        "capture_id": job["capture_id"],
        "candidate_id": candidate_id,
        "output": str(output),
        "started_at": ATTESTED_AT,
    }
    pipeline._save_state(paths, state)
    return paths.root, candidate_id, job["capture_id"]


def test_resume_refuses_to_bank_a_held_reddit_login_wall_as_captured(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    _, candidate_id, capture_id = _held_reddit_capture(
        run_root,
        "https://old.reddit.com/login/?reason=lor2&dest=%2Fr%2FSkincareAddictionLux",
    )
    paths = pipeline.pipeline_paths(run_root)

    pipeline._reconcile_in_flight(paths)

    recovered = pipeline._load_state(paths)
    candidate = recovered["candidates"][candidate_id]
    settled = next(
        item for item in recovered["reddit_queue"] if item["capture_id"] == capture_id
    )
    assert candidate["status"] == "capture_blocked"
    assert candidate["capture"] is None
    assert candidate["terminal_reason"] == "reddit_thread_not_reached"
    assert settled["status"] == "capture_blocked"
    assert settled["attempts"][-1]["outcome"] == "challenge"
    assert settled["attempts"][-1]["detail"] == "reddit_thread_not_reached"
    assert recovered["circuits"]["reddit"]["total_challenges"] == 1
    assert recovered["circuits"]["reddit"]["consecutive_challenges"] == 1
    assert recovered["circuits"]["reddit"]["state"] == "cooldown"
    assert recovered["circuits"]["reddit"]["cooldown_until"] is not None
    assert recovered["in_flight"]["reddit"] is None


def test_resume_still_banks_a_held_reddit_packet_that_reached_its_thread(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    _, candidate_id, capture_id = _held_reddit_capture(
        run_root,
        "https://old.reddit.com/r/SkincareAddictionLux/comments/1ovsqzr/dieuxspecific_irritation/",
    )

    pipeline._reconcile_in_flight(paths)

    recovered = pipeline._load_state(paths)
    candidate = recovered["candidates"][candidate_id]
    assert candidate["status"] == "captured"
    assert candidate["capture"]["resume_inspected"] is True
    assert recovered["circuits"]["reddit"]["total_challenges"] == 0
    assert recovered["in_flight"]["reddit"] is None


def test_resume_reddit_challenge_ceiling_still_opens_the_owner_ping(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    _held_reddit_capture(run_root, "https://old.reddit.com/login/")
    paths = pipeline.pipeline_paths(run_root)
    state = pipeline._load_state(paths)
    state["circuits"]["reddit"]["consecutive_challenges"] = 1
    state["circuits"]["reddit"]["total_challenges"] = 1
    pipeline._save_state(paths, state)

    pipeline._reconcile_in_flight(paths)

    recovered = pipeline._load_state(paths)
    assert recovered["circuits"]["reddit"]["state"] == "owner_ping"
    assert recovered["status"] == "owner_ping"
    assert recovered["terminal_reason"] == "reddit_challenge_ceiling"


def test_resume_blocks_a_google_queue_claim_missing_from_controller_state(
    tmp_path: Path,
) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    action = pipeline.next_action(state_path=paths.google_state)
    assert action["status"] == "capture_ready"

    with pytest.raises(
        pipeline.PipelineBlocked, match="BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"
    ):
        pipeline._reconcile_in_flight(paths)

    recovered = pipeline._load_state(paths)
    assert recovered["status"] == "blocked"
    assert recovered["terminal_reason"] == "BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"


def test_terminal_in_flight_with_unproved_binding_is_inspected_once(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    packet = run_root / "terminal-packet"
    packet.mkdir()
    (packet / "manifest.json").write_text("{}", encoding="utf-8")
    state = pipeline._load_state(paths)
    state["in_flight"]["reddit"] = {
        "capture_id": "capture_unbound",
        "candidate_id": "candidate_unbound",
        "output": str(packet),
        "started_at": ATTESTED_AT,
    }
    pipeline._save_state(paths, state)

    with pytest.raises(pipeline.PipelineBlocked, match="BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"):
        pipeline.run_pipeline(run_root=run_root)

    first = pipeline.inspect_pipeline(run_root=run_root)
    inspected_at = first["in_flight_inspections"]["capture_unbound"]
    assert first["terminal_reason"] == "BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"

    with pytest.raises(pipeline.PipelineBlocked, match="BLOCKED_IN_FLIGHT_OUTCOME_UNKNOWN"):
        pipeline.run_pipeline(run_root=run_root)

    second = pipeline.inspect_pipeline(run_root=run_root)
    assert second["in_flight_inspections"]["capture_unbound"] == inspected_at


def test_reddit_transport_interruption_retries_exact_item_once(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    _, candidate_id = _candidate_state(run_root)
    _import_one(run_root, candidate_id)
    paths = pipeline.pipeline_paths(run_root)
    google = pipeline.inspect_queue(state_path=paths.google_state)
    google["status"] = "complete"
    google["next_job_index"] = len(google["jobs"])
    google["completed_job_ids"] = [job["job_id"] for job in google["jobs"]]
    pipeline._atomic_write_json(paths.google_state, google)
    attempts = 0

    def capture(worker, action, _config, output):
        nonlocal attempts
        assert worker == "reddit"
        attempts += 1
        if attempts == 1:
            return pipeline.CaptureResult("transport_interruption", detail="connection reset")
        output.mkdir(parents=True, exist_ok=True)
        (output / "manifest.json").write_text("{}", encoding="utf-8")
        return pipeline.CaptureResult("success", str(output))

    result = pipeline.run_pipeline(run_root=run_root, capture=capture, sleep=lambda _seconds: None)

    assert attempts == 2
    assert result["reddit_queue"][0]["status"] == "captured"
    assert len(result["reddit_queue"][0]["attempts"]) == 2


def test_second_reddit_challenge_opens_owner_ping(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)
    state, candidate_id = _candidate_state(run_root)
    _import_one(run_root, candidate_id)
    state = pipeline._load_state(paths)
    duplicate = dict(state["reddit_queue"][0])
    duplicate["capture_id"] = "capture_second"
    duplicate["candidate_id"] = candidate_id
    duplicate["status"] = "pending"
    duplicate["attempts"] = []
    state["reddit_queue"].append(duplicate)
    pipeline._save_state(paths, state)
    google = pipeline.inspect_queue(state_path=paths.google_state)
    google["status"] = "complete"
    google["next_job_index"] = len(google["jobs"])
    google["completed_job_ids"] = [job["job_id"] for job in google["jobs"]]
    pipeline._atomic_write_json(paths.google_state, google)
    current = datetime(2026, 8, 4, 13, 0, tzinfo=UTC)

    def capture(_worker, _action, _config, _output):
        return pipeline.CaptureResult("challenge", detail="CAPTCHA")

    def now() -> datetime:
        nonlocal current
        value = current
        current += timedelta(minutes=21)
        return value

    result = pipeline.run_pipeline(run_root=run_root, capture=capture, sleep=lambda _seconds: None, now=now)

    assert result["status"] == "owner_ping"
    assert result["terminal_reason"] == "reddit_challenge_ceiling"
    assert result["circuits"]["reddit"]["total_challenges"] == 2


def test_reddit_worker_runs_while_google_worker_is_resting(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    _, candidate_id = _candidate_state(run_root)
    _import_one(run_root, candidate_id)
    calls: list[str] = []
    lock = Lock()

    def capture(worker, action, _config, output):
        with lock:
            calls.append(worker)
        output.mkdir(parents=True, exist_ok=True)
        if worker == "google":
            job = action["job"]
            (output / "content_record.json").write_text(
                json.dumps(
                    {
                        "content_record_version": "google_serp_content_v3",
                        "requested_url": job["url"],
                        "final_url": job["url"],
                        "rows": [],
                    }
                ),
                encoding="utf-8",
            )
        else:
            (output / "manifest.json").write_text("{}", encoding="utf-8")
        return pipeline.CaptureResult("success", str(output))

    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)

    result = pipeline.run_pipeline(run_root=run_root, capture=capture, sleep=sleep)

    assert "reddit" in calls
    assert calls.count("google") == 4
    assert result["reddit_queue"][0]["status"] == "captured"
    assert any(seconds >= 44 for seconds in slept)


def test_event_log_and_state_never_include_attestation_forbidden_fields(tmp_path: Path) -> None:
    run_root = _init(tmp_path)
    paths = pipeline.pipeline_paths(run_root)

    combined = paths.config.read_text(encoding="utf-8") + paths.state.read_text(encoding="utf-8") + paths.events.read_text(encoding="utf-8")

    assert "2026-08-04T12:28:50.331Z" in combined
    for forbidden in ("exit_ip", "vpn_server", "credential", "access_token", "cookie"):
        assert forbidden not in combined.casefold()
