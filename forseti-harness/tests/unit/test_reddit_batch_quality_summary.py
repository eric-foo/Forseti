from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from runners.run_reddit_batch_quality_summary import build_reddit_batch_quality_summary


@pytest.fixture
def scratch_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "_test_runs"
    path = root / f"reddit_batch_quality_summary_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_quality_summary_marks_clean_consolidated_slot_usable(scratch_dir: Path) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": {"status": 200, "reason": "OK", "content_type": "text/html", "byte_count": 123},
                "consolidation": _consolidation_fixture(
                    title="A useful thread",
                    comments_parsed=2,
                    observable_comment_nodes=2,
                    comment_postures={"present": 2},
                ),
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    artifact = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    data = artifact["reddit_batch_quality_summary"]
    assert data["counts"]["usable_yes_count"] == 1
    assert data["counts"]["usable_no_count"] == 0
    assert data["results"][0]["usable_for_downstream"] == "yes"
    assert data["results"][0]["quality_flags"] == []
    assert "not live Reddit capture" in data["non_claims"]
    receipt = Path(result["receipt_path"]).read_text(encoding="utf-8")
    assert "`slot_a`: yes" in receipt


def test_quality_summary_marks_content_retention_slot_usable(scratch_dir: Path) -> None:
    content_record = _consolidation_fixture(
        title="A retained thread",
        comments_parsed=2,
        observable_comment_nodes=2,
        comment_postures={"present": 2},
    )["reddit_thread_consolidation"]
    content_record["record_kind"] = "reddit_thread_content_v0"
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": None,
                "metadata": {
                    "status": 200,
                    "reason": "OK",
                    "content_type": "text/html",
                    "byte_count": 123,
                },
                "consolidation": None,
                "content_record": content_record,
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    data = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]
    row = data["results"][0]
    assert row["usable_for_downstream"] == "yes"
    assert row["parsed_artifact_kind"] == "reddit_thread_content_v0"
    assert row["consolidation_exit"] is None
    assert data["counts"]["consolidation_success_count"] == 0
    assert data["counts"]["parsed_success_count"] == 1


def test_quality_summary_marks_capture_or_consolidation_failures_not_usable(
    scratch_dir: Path,
) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 3,
                "consolidation_exit": None,
                "metadata": None,
                "consolidation": None,
            },
            {
                "slot_id": "slot_b",
                "url": "https://old.reddit.com/r/SaaS/comments/def/example/",
                "capture_exit": 0,
                "consolidation_exit": 3,
                "metadata": {"status": 200, "reason": "OK", "content_type": "text/html", "byte_count": 456},
                "consolidation": None,
            },
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    rows = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"]
    assert rows[0]["usable_for_downstream"] == "no"
    assert "capture_failed" in rows[0]["quality_flags"]
    assert rows[1]["usable_for_downstream"] == "no"
    assert "consolidation_failed" in rows[1]["quality_flags"]


def test_quality_summary_marks_parser_warnings_as_needs_review(scratch_dir: Path) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": {"status": 200, "reason": "OK", "content_type": "text/html", "byte_count": 123},
                "consolidation": _consolidation_fixture(
                    title="A thread with a bodyless node",
                    comments_parsed=1,
                    observable_comment_nodes=1,
                    comment_postures={"missing_dom": 1},
                    parser_warnings=["comment body carried as missing_dom"],
                ),
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    row = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"][0]
    assert row["usable_for_downstream"] == "needs_review"
    assert "parser_warnings_present" in row["quality_flags"]
    assert "no_present_comments" in row["quality_flags"]


def test_quality_summary_marks_missing_consolidation_content_as_not_usable(
    scratch_dir: Path,
) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": {"status": 200, "reason": "OK", "content_type": "text/html", "byte_count": 123},
                "consolidation": None,
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    row = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"][0]
    assert row["usable_for_downstream"] == "no"
    assert "consolidation_content_missing" in row["quality_flags"]


def test_quality_summary_marks_http_non_2xx_as_not_usable(scratch_dir: Path) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": {"status": 404, "reason": "Not Found", "content_type": "text/html", "byte_count": 0},
                "consolidation": _consolidation_fixture(
                    title="A thread",
                    comments_parsed=1,
                    observable_comment_nodes=1,
                    comment_postures={"present": 1},
                ),
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    row = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"][0]
    assert row["usable_for_downstream"] == "no"
    assert "http_non_2xx" in row["quality_flags"]


def test_quality_summary_marks_missing_http_metadata_as_not_usable(scratch_dir: Path) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": None,
                "consolidation": _consolidation_fixture(
                    title="A thread",
                    comments_parsed=1,
                    observable_comment_nodes=1,
                    comment_postures={"present": 1},
                ),
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    row = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"][0]
    assert row["usable_for_downstream"] == "no"
    assert "http_metadata_missing" in row["quality_flags"]


def test_quality_summary_marks_reconciliation_mismatch_as_not_usable(scratch_dir: Path) -> None:
    batch_summary = _write_batch_fixture(
        scratch_dir,
        rows=[
            {
                "slot_id": "slot_a",
                "url": "https://old.reddit.com/r/SaaS/comments/abc/example/",
                "capture_exit": 0,
                "consolidation_exit": 0,
                "metadata": {"status": 200, "reason": "OK", "content_type": "text/html", "byte_count": 123},
                "consolidation": _consolidation_fixture(
                    title="A thread",
                    comments_parsed=3,
                    observable_comment_nodes=2,
                    comment_postures={"present": 3},
                ),
            }
        ],
    )

    result = build_reddit_batch_quality_summary(
        batch_summary_path=batch_summary,
        output_directory=scratch_dir / "quality",
    )

    row = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))[
        "reddit_batch_quality_summary"
    ]["results"][0]
    assert row["usable_for_downstream"] == "no"
    assert "comment_reconciliation_mismatch" in row["quality_flags"]


def test_quality_summary_rejects_non_batch_summary(scratch_dir: Path) -> None:
    batch_summary = scratch_dir / "batch_summary.json"
    batch_summary.write_text(json.dumps({"runner": "other", "results": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="reddit_old_http_batch"):
        build_reddit_batch_quality_summary(
            batch_summary_path=batch_summary,
            output_directory=scratch_dir / "quality",
        )


def _write_batch_fixture(scratch_dir: Path, *, rows: list[dict[str, object]]) -> Path:
    batch_root = scratch_dir / "batch"
    batch_root.mkdir()
    summary_rows = []
    for item in rows:
        slot_id = str(item["slot_id"])
        packet_dir = batch_root / f"{slot_id}_packet"
        derived_dir = batch_root / f"{slot_id}_derived"
        packet_dir.mkdir()
        (packet_dir / "raw").mkdir()
        if item["metadata"] is not None:
            (packet_dir / "raw" / "02_http_response_metadata.json").write_text(
                json.dumps(item["metadata"]),
                encoding="utf-8",
            )
        content_record = item.get("content_record")
        if content_record is not None:
            (packet_dir / "raw" / "01_content_record.json").write_text(
                json.dumps(content_record),
                encoding="utf-8",
            )
        consolidation_message: object = None
        if item["consolidation"] is not None:
            derived_dir.mkdir()
            json_path = derived_dir / "reddit_thread_consolidation.json"
            json_path.write_text(json.dumps(item["consolidation"]), encoding="utf-8")
            consolidation_message = {"json_path": str(json_path)}
        summary_rows.append(
            {
                "slot_id": slot_id,
                "url": item["url"],
                "capture_exit": item["capture_exit"],
                "consolidation_exit": item["consolidation_exit"],
                "packet_dir": str(packet_dir),
                "derived_dir": str(derived_dir),
                "consolidation_message": consolidation_message,
                "retry_count": 0,
            }
        )
    batch_summary = batch_root / "batch_summary.json"
    batch_summary.write_text(
        json.dumps(
            {
                "runner": "reddit_old_http_batch",
                "method": "old_reddit_direct_http",
                "non_claims": ["not crawler"],
                "results": summary_rows,
            }
        ),
        encoding="utf-8",
    )
    return batch_summary


def _consolidation_fixture(
    *,
    title: str | None,
    comments_parsed: int,
    observable_comment_nodes: int,
    comment_postures: dict[str, int],
    parser_warnings: list[str] | None = None,
) -> dict[str, object]:
    return {
        "reddit_thread_consolidation": {
            "thread": {"thread_id": "abc", "subreddit": "SaaS", "title": title},
            "counts": {
                "comments_parsed": comments_parsed,
                "observable_comment_nodes": observable_comment_nodes,
                "comment_postures": comment_postures,
            },
            "warnings": [],
            "limitations": [],
            "comments": [
                {
                    "row_id": "comment_0001",
                    "comment_posture": next(iter(comment_postures), "present"),
                    "parser_warnings": parser_warnings or [],
                }
            ],
        }
    }
