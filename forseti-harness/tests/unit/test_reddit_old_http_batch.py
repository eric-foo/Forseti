from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners import run_reddit_old_http_batch as runner
from runners.run_reddit_old_http_batch import BatchSlot, load_slots, run_reddit_old_http_batch
from source_capture.content_extraction import (
    CONTENT_EXTRACTION_FAILED_EXIT_CODE,
    ContentExtractionSpec,
)


def test_load_slots_accepts_only_exact_old_reddit_threads(tmp_path: Path) -> None:
    path = tmp_path / "urls.json"
    path.write_text(
        json.dumps(
            [
                "https://old.reddit.com/r/SaaS/comments/abc/example/",
                {
                    "slot_id": "second",
                    "url": "https://old.reddit.com/r/fragrance/comments/def/example/",
                },
            ]
        ),
        encoding="utf-8",
    )
    assert [slot.slot_id for slot in load_slots(path)] == ["slot_001", "second"]

    path.write_text(
        json.dumps(["https://www.reddit.com/r/SaaS/comments/abc/example/"]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="old.reddit.com"):
        load_slots(path)


def test_batch_extracts_in_flight_without_post_hoc_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    def capture(**kwargs):
        calls.append(kwargs)
        packet_dir = Path(kwargs["output_directory"])
        raw_dir = packet_dir / "raw"
        raw_dir.mkdir(parents=True)
        # Mirror the packet writer's real on-disk shape: writer._copy_preserved_files
        # names every preserved file "{index:02d}_{name}" under raw/, for local packet
        # directories and lake commits alike. Staging a bare content_record.json here
        # would assert the owner-visible receipt against a shape capture never emits.
        (raw_dir / "01_content_record.json").write_text("{}\n", encoding="utf-8")
        return 0, str(packet_dir)

    monkeypatch.setattr(runner, "run_source_capture_http_packet", capture)
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    exit_code, message = run_reddit_old_http_batch(
        slots=[BatchSlot("slot_a", "https://old.reddit.com/r/SaaS/comments/abc/example/")],
        output_root=tmp_path / "out",
        decision_question="What source-visible content was present?",
        delay_seconds=0,
    )

    assert exit_code == 0
    assert len(calls) == 1
    spec = calls[0]["content_extraction"]
    assert isinstance(spec, ContentExtractionSpec)
    assert spec.requested_retention_mode == "content"
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    assert summary["capture_success_count"] == 1
    assert "consolidation_success_count" not in summary
    assert summary["results"][0]["content_record_preserved"] is True


@pytest.mark.parametrize(
    ("filenames", "expected"),
    [
        # The writer-numbered name is what every real packet carries.
        (["raw/01_content_record.json"], True),
        (["content_record.json"], True),
        # The widened glob must not accept an unrelated same-suffix artifact.
        (["raw/notes_content_record.json"], False),
        # Duplicates stay visible instead of being collapsed into a clean receipt.
        (["raw/01_content_record.json", "raw/02_content_record.json"], False),
    ],
)
def test_packet_content_record_detection_stays_bounded(
    tmp_path: Path, filenames: list[str], expected: bool
) -> None:
    packet_dir = tmp_path / "packet"
    for name in filenames:
        path = packet_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    assert runner._packet_preserves_content_record(packet_dir) is expected


def test_batch_failure_stays_visible_and_has_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def capture(**_kwargs):
        nonlocal calls
        calls += 1
        return 3, "direct HTTP failed visibly"

    monkeypatch.setattr(runner, "run_source_capture_http_packet", capture)
    exit_code, message = run_reddit_old_http_batch(
        slots=[BatchSlot("slot_a", "https://old.reddit.com/r/SaaS/comments/abc/example/")],
        output_root=tmp_path / "out",
        decision_question="What source-visible content was present?",
        delay_seconds=0,
    )
    assert exit_code == 2
    assert calls == 1
    row = json.loads(Path(message).read_text(encoding="utf-8"))["results"][0]
    assert row["capture_exit"] == 3
    assert row["retry_count"] == 0


def test_block_shell_failure_preserves_no_refetch_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def capture(**kwargs):
        packet_dir = Path(kwargs["output_directory"])
        raw_dir = packet_dir / "raw"
        raw_dir.mkdir(parents=True)
        body = b"""<html><head><title>Access check</title></head>
        <body><h1>Not a robot?</h1><p>Complete the reCAPTCHA to continue.</p></body></html>"""
        (raw_dir / "01_http_response_body.bin").write_bytes(body)
        (raw_dir / "02_http_response_metadata.json").write_text(
            json.dumps(
                {
                    "status": 200,
                    "body_classification": "block_shell",
                    "body_classification_signal": "recaptcha",
                    "body_classification_detail": "matched recaptcha signature",
                }
            ),
            encoding="utf-8",
        )
        return CONTENT_EXTRACTION_FAILED_EXIT_CODE, str(packet_dir)

    monkeypatch.setattr(runner, "run_source_capture_http_packet", capture)
    exit_code, message = run_reddit_old_http_batch(
        slots=[BatchSlot("slot_a", "https://old.reddit.com/r/SaaS/comments/abc/example/")],
        output_root=tmp_path / "out",
        decision_question="What source-visible content was present?",
        delay_seconds=0,
    )

    assert exit_code == 2
    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    row = summary["results"][0]
    assert row["capture_exit"] == CONTENT_EXTRACTION_FAILED_EXIT_CODE
    assert row["content_record_preserved"] is False
    assert row["access_diagnostic_status"] == "preserved"
    assert summary["access_diagnostic_count"] == 1
    screenshot = Path(row["access_diagnostic_screenshot"])
    receipt = json.loads(Path(row["access_diagnostic_receipt"]).read_text(encoding="utf-8"))
    assert screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert receipt["body_classification_signal"] == "recaptcha"
    assert "Not a robot?" in receipt["visible_text_excerpt"]
    assert receipt["derivation"] == "exact_preserved_response_body_no_network_refetch"
    assert receipt["non_claims"] == [
        "not a second Reddit request",
        "not browser access",
        "not CAPTCHA solving",
        "not a pixel-faithful browser rendering",
    ]


def test_non_block_shell_extraction_failure_does_not_fake_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def capture(**kwargs):
        packet_dir = Path(kwargs["output_directory"])
        raw_dir = packet_dir / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "01_http_response_body.bin").write_bytes(b"<html>thread body</html>")
        (raw_dir / "02_http_response_metadata.json").write_text(
            json.dumps(
                {
                    "status": 200,
                    "body_classification": "content_unverified",
                    "body_classification_signal": None,
                }
            ),
            encoding="utf-8",
        )
        return CONTENT_EXTRACTION_FAILED_EXIT_CODE, str(packet_dir)

    monkeypatch.setattr(runner, "run_source_capture_http_packet", capture)
    _exit_code, message = run_reddit_old_http_batch(
        slots=[BatchSlot("slot_a", "https://old.reddit.com/r/SaaS/comments/abc/example/")],
        output_root=tmp_path / "out",
        decision_question="What source-visible content was present?",
        delay_seconds=0,
    )

    summary = json.loads(Path(message).read_text(encoding="utf-8"))
    row = summary["results"][0]
    assert row["access_diagnostic_status"] == "not_applicable"
    assert row["access_diagnostic_screenshot"] is None
    assert summary["access_diagnostic_count"] == 0


@pytest.mark.parametrize(
    "slot",
    [
        BatchSlot("slot", "https://www.reddit.com/r/SaaS/comments/abc/example/"),
        BatchSlot("../escape", "https://old.reddit.com/r/SaaS/comments/abc/example/"),
    ],
)
def test_direct_api_revalidates_host_and_slot_bounds(tmp_path: Path, slot: BatchSlot) -> None:
    with pytest.raises(ValueError):
        run_reddit_old_http_batch(
            slots=[slot],
            output_root=tmp_path / "out",
            decision_question="test",
            delay_seconds=0,
        )


def test_batch_enforces_max_urls(tmp_path: Path) -> None:
    slots = [
        BatchSlot(f"slot_{index}", f"https://old.reddit.com/r/SaaS/comments/{index}/example/")
        for index in range(2)
    ]
    with pytest.raises(ValueError, match="above max_urls"):
        run_reddit_old_http_batch(
            slots=slots,
            output_root=tmp_path / "out",
            decision_question="test",
            max_urls=1,
            delay_seconds=0,
        )
