from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from runners.run_reddit_weekly_finalizer import finalize_reddit_weekly_run


def test_finalizer_writes_complete_agent_catalog_and_is_repeatable(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    output = tmp_path / "completed"

    first = finalize_reddit_weekly_run(
        deep_dive_dir=deep_dive, output_dir=output, as_of=dt.date(2026, 8, 11)
    )
    first_run_bytes = Path(first["run_path"]).read_bytes()
    first_catalog_bytes = Path(first["catalog_path"]).read_bytes()
    second = finalize_reddit_weekly_run(
        deep_dive_dir=deep_dive, output_dir=output, as_of=dt.date(2026, 8, 11)
    )

    assert Path(second["run_path"]).read_bytes() == first_run_bytes
    assert Path(second["catalog_path"]).read_bytes() == first_catalog_bytes
    run = json.loads(first_run_bytes)
    rows = [json.loads(line) for line in first_catalog_bytes.decode().splitlines()]
    assert run["run_name"] == "Reddit Top100 2026-08-11"
    assert run["status"] == "complete"
    assert run["counts"] == {
        "content_records_resolved": 2,
        "no": 1,
        "threads": 2,
        "transcripts_available": 1,
        "yes": 1,
    }
    assert [row["thread_id"] for row in rows] == ["existing", "queued"]
    assert rows[0]["original_order"] is None
    assert rows[0]["origin"] == "existing_admitted_capture"
    assert rows[1]["original_order"] == 1
    assert rows[1]["admission"] == "no"
    assert rows[1]["listing"]["title"] == "Queued listing title"
    assert rows[1]["title"] == "Queued captured title"
    assert rows[1]["source_extract"]["path"].endswith("batch_001_extracts_v1.jsonl")
    assert rows[0]["transcript"].endswith("existing.txt")


def test_finalizer_rejects_duplicate_extract_thread(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    batch = deep_dive / "batch_001_extracts_v1.jsonl"
    batch.write_text(
        batch.read_text(encoding="utf-8")
        + (deep_dive / "existing_11_extracts_v1.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate thread_id in extract corpus"):
        _finalize(deep_dive, tmp_path / "output")


def test_finalizer_rejects_missing_manifest_thread_extract(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    (deep_dive / "batch_001_extracts_v1.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="manifest/extract thread set mismatch"):
        _finalize(deep_dive, tmp_path / "output")


def test_finalizer_rejects_unresolved_or_wrong_content_record(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    row = json.loads((deep_dive / "batch_001_extracts_v1.jsonl").read_text(encoding="utf-8"))
    Path(row["content_record"]).write_text(
        json.dumps({"thread": {"thread_id": "other"}}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="content record identity mismatch"):
        _finalize(deep_dive, tmp_path / "output")


def test_finalizer_rejects_declared_count_mismatch(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    manifest_path = deep_dive / "deep_dive_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["coverage"]["admitted"] = 3
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="admitted count does not match"):
        _finalize(deep_dive, tmp_path / "output")


def _finalize(deep_dive: Path, output: Path) -> dict[str, object]:
    return finalize_reddit_weekly_run(
        deep_dive_dir=deep_dive, output_dir=output, as_of=dt.date(2026, 8, 11)
    )


def _fixture(tmp_path: Path) -> Path:
    deep_dive = tmp_path / "deep-dive-v1"
    deep_dive.mkdir()
    records = tmp_path / "records"
    records.mkdir()
    existing_record = _content_record(
        records / "existing.json", "existing", "Existing captured title"
    )
    queued_record = _content_record(records / "queued.json", "queued", "Queued captured title")
    manifest = {
        "schema": "forseti.reddit.weekly_deep_dive_manifest.v1",
        "methodology_id": "reddit_weekly_top100_per_subreddit_v0",
        "decision_frame": "weekly_latent_problem_gtm_discovery_v0",
        "coverage": {"admitted": 2},
        "existing_admitted_captures": [
            {
                "thread_id": "existing",
                "thread_url": "https://reddit.example/existing",
                "subreddit": "example",
                "title": "Existing listing title",
                "listing_snapshot": {"score": 20, "comments": 10},
            }
        ],
        "pending": [
            {
                "thread_id": "queued",
                "thread_url": "https://reddit.example/queued",
                "subreddit": "example",
                "title_or_none": "Queued listing title",
                "listing_snapshot": {"score": 10, "comments": 5},
                "deep_dive_order": 1,
                "capture_wave": "high_priority",
            }
        ],
    }
    (deep_dive / "deep_dive_manifest_v1.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_jsonl(
        deep_dive / "existing_11_extracts_v1.jsonl",
        [_extract("existing", "yes", existing_record, core_problem="Existing problem")],
    )
    _write_jsonl(
        deep_dive / "batch_001_extracts_v1.jsonl",
        [
            _extract(
                "queued",
                "no",
                queued_record,
                core_problem=None,
                decision_effect="Exclude after reading the full thread.",
            )
        ],
    )
    transcript_dir = deep_dive / "transcripts-existing-11"
    transcript_dir.mkdir()
    (transcript_dir / "existing.txt").write_text("full transcript", encoding="utf-8")
    return deep_dive


def _content_record(path: Path, thread_id: str, title: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "record_kind": "reddit_thread_content_v0",
                "source_url": f"https://reddit.example/{thread_id}/captured",
                "thread": {"thread_id": thread_id, "subreddit": "Example", "title": title},
            }
        ),
        encoding="utf-8",
    )
    return path


def _extract(
    thread_id: str,
    admission: str,
    content_record: Path,
    *,
    core_problem: str | None,
    decision_effect: str | None = None,
) -> dict[str, object]:
    return {
        "thread_id": thread_id,
        "admission": admission,
        "subreddit": "example",
        "url": f"https://reddit.example/{thread_id}",
        "core_problem": core_problem,
        "commercial_signal": "A useful commercial summary.",
        "material_addition": (
            {"decision_effect": decision_effect} if decision_effect is not None else None
        ),
        "reason_codes": ["failure_or_unmet_need"],
        "named_brands": [],
        "content_record": str(content_record),
        "comment_completeness": {"comments_captured": 1, "declared_total_comments": 1},
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
