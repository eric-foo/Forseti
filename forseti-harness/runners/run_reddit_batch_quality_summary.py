from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness_utils import utc_now_z


QUALITY_SUMMARY_SCHEMA_VERSION = "reddit_batch_quality_summary_v0"

QUALITY_NON_CLAIMS = [
    "not validation",
    "not readiness",
    "not Reddit source completeness proof",
    "not live Reddit capture",
    "not Reddit monitoring",
    "not source discovery",
    "not broad crawling",
    "not proxy use",
    "not browser automation",
    "not retry escalation",
    "not commercial API behavior",
    "not ECR design",
    "not Cleaning implementation",
    "not Judgment scoring",
]


def build_reddit_batch_quality_summary(
    *,
    batch_summary_path: Path,
    output_directory: Path,
    json_name: str = "reddit_batch_quality_summary.json",
    receipt_name: str = "reddit_batch_quality_summary_receipt.md",
) -> dict[str, str]:
    batch_summary_path = batch_summary_path.resolve()
    batch_summary = _read_json(batch_summary_path)
    if not isinstance(batch_summary, dict):
        raise ValueError("batch summary must be a JSON object")
    if batch_summary.get("runner") != "reddit_old_http_batch":
        raise ValueError("quality summary accepts only reddit_old_http_batch summaries")

    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / json_name
    receipt_path = output_directory / receipt_name
    for path in (json_path, receipt_path):
        if path.exists():
            raise ValueError(f"output already exists: {path}")

    results = batch_summary.get("results")
    if not isinstance(results, list):
        raise ValueError("batch summary results must be a JSON array")

    rows = [
        _summarize_result_row(row=row, batch_summary_path=batch_summary_path)
        for row in results
        if isinstance(row, dict)
    ]
    artifact = {
        "reddit_batch_quality_summary": {
            "schema_version": QUALITY_SUMMARY_SCHEMA_VERSION,
            "generated_at": utc_now_z(),
            "batch_summary_path": str(batch_summary_path),
            "batch_runner": batch_summary.get("runner"),
            "batch_method": batch_summary.get("method"),
            "batch_non_claims": batch_summary.get("non_claims", []),
            "counts": _summarize_counts(rows),
            "results": rows,
            "non_claims": QUALITY_NON_CLAIMS,
        }
    }
    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    receipt_path.write_text(_render_receipt(artifact), encoding="utf-8", newline="\n")
    return {"json_path": str(json_path), "receipt_path": str(receipt_path)}


def _summarize_result_row(*, row: dict[str, Any], batch_summary_path: Path) -> dict[str, Any]:
    packet_dir = _resolve_maybe_relative_path(row.get("packet_dir"), base=batch_summary_path.parent)
    derived_dir = _resolve_maybe_relative_path(row.get("derived_dir"), base=batch_summary_path.parent)
    metadata = _read_optional_json(_packet_metadata_path(packet_dir))
    consolidation = _read_optional_json(_consolidation_path(row=row, derived_dir=derived_dir))
    content_record = _read_optional_json(_content_record_path(packet_dir))
    parsed_content, parsed_artifact_kind = _resolve_parsed_content(
        consolidation=consolidation,
        content_record=content_record,
    )
    counts = parsed_content.get("counts", {}) if isinstance(parsed_content, dict) else {}
    thread = parsed_content.get("thread", {}) if isinstance(parsed_content, dict) else {}
    warnings = parsed_content.get("warnings", []) if isinstance(parsed_content, dict) else []
    limitations = parsed_content.get("limitations", []) if isinstance(parsed_content, dict) else []
    comments = parsed_content.get("comments", []) if isinstance(parsed_content, dict) else []
    parser_warning_count = _parser_warning_count(comments)

    quality_flags = _quality_flags(
        capture_exit=row.get("capture_exit"),
        consolidation_exit=row.get("consolidation_exit"),
        parsed_artifact_kind=parsed_artifact_kind,
        metadata=metadata,
        title=thread.get("title") if isinstance(thread, dict) else None,
        counts=counts if isinstance(counts, dict) else {},
        warnings=warnings if isinstance(warnings, list) else [],
        parser_warning_count=parser_warning_count,
    )
    return {
        "slot_id": row.get("slot_id"),
        "url": row.get("url"),
        "capture_exit": row.get("capture_exit"),
        "consolidation_exit": row.get("consolidation_exit"),
        "parsed_artifact_kind": parsed_artifact_kind,
        "parse_success": parsed_artifact_kind is not None,
        "http_status": metadata.get("status") if isinstance(metadata, dict) else None,
        "http_reason": metadata.get("reason") if isinstance(metadata, dict) else None,
        "content_type": metadata.get("content_type") if isinstance(metadata, dict) else None,
        "byte_count": metadata.get("byte_count") if isinstance(metadata, dict) else None,
        "thread_id": thread.get("thread_id") if isinstance(thread, dict) else None,
        "subreddit": thread.get("subreddit") if isinstance(thread, dict) else None,
        "title": thread.get("title") if isinstance(thread, dict) else None,
        "comments_parsed": counts.get("comments_parsed") if isinstance(counts, dict) else None,
        "observable_comment_nodes": (
            counts.get("observable_comment_nodes") if isinstance(counts, dict) else None
        ),
        "comment_postures": counts.get("comment_postures", {}) if isinstance(counts, dict) else {},
        "warning_count": len(warnings) if isinstance(warnings, list) else None,
        "limitation_count": len(limitations) if isinstance(limitations, list) else None,
        "parser_warning_count": parser_warning_count,
        "quality_flags": quality_flags,
        "usable_for_downstream": _usable_for_downstream(quality_flags),
        "packet_dir": str(packet_dir) if packet_dir is not None else None,
        "derived_dir": str(derived_dir) if derived_dir is not None else None,
    }


def _quality_flags(
    *,
    capture_exit: object,
    consolidation_exit: object,
    parsed_artifact_kind: str | None,
    metadata: dict[str, Any] | None,
    title: object,
    counts: dict[str, Any],
    warnings: list[Any],
    parser_warning_count: int,
) -> list[str]:
    flags: list[str] = []
    if capture_exit != 0:
        flags.append("capture_failed")
    if parsed_artifact_kind is None:
        if consolidation_exit not in {None, 0}:
            flags.append("consolidation_failed")
        elif consolidation_exit == 0:
            flags.append("consolidation_content_missing")
        else:
            flags.append("content_record_missing")
    if metadata is None:
        flags.append("http_metadata_missing")
    else:
        status = metadata.get("status")
        if not isinstance(status, int) or status < 200 or status >= 300:
            flags.append("http_non_2xx")
    if not isinstance(title, str) or not title.strip():
        flags.append("title_missing")

    comments_parsed = counts.get("comments_parsed")
    observable_nodes = counts.get("observable_comment_nodes")
    if comments_parsed != observable_nodes:
        flags.append("comment_reconciliation_mismatch")
    postures = counts.get("comment_postures")
    if not isinstance(postures, dict) or int(postures.get("present", 0) or 0) == 0:
        flags.append("no_present_comments")
    if warnings:
        flags.append("thread_warnings_present")
    if parser_warning_count > 0:
        flags.append("parser_warnings_present")
    return flags


def _usable_for_downstream(flags: list[str]) -> str:
    hard_failures = {
        "capture_failed",
        "consolidation_failed",
        "consolidation_content_missing",
        "content_record_missing",
        "http_metadata_missing",
        "http_non_2xx",
        "comment_reconciliation_mismatch",
    }
    if any(flag in hard_failures for flag in flags):
        return "no"
    review_flags = {"title_missing", "no_present_comments", "thread_warnings_present", "parser_warnings_present"}
    if any(flag in review_flags for flag in flags):
        return "needs_review"
    return "yes"


def _summarize_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "slot_count": len(rows),
        "capture_success_count": sum(1 for row in rows if row["capture_exit"] == 0),
        "consolidation_success_count": sum(1 for row in rows if row["consolidation_exit"] == 0),
        "parsed_success_count": sum(1 for row in rows if row["parse_success"] is True),
        "usable_yes_count": sum(1 for row in rows if row["usable_for_downstream"] == "yes"),
        "usable_needs_review_count": sum(
            1 for row in rows if row["usable_for_downstream"] == "needs_review"
        ),
        "usable_no_count": sum(1 for row in rows if row["usable_for_downstream"] == "no"),
    }


def _packet_metadata_path(packet_dir: Path | None) -> Path | None:
    if packet_dir is None:
        return None
    candidate = packet_dir / "raw" / "02_http_response_metadata.json"
    return candidate if candidate.exists() else None


def _consolidation_path(*, row: dict[str, Any], derived_dir: Path | None) -> Path | None:
    message = row.get("consolidation_message")
    if isinstance(message, dict) and isinstance(message.get("json_path"), str):
        path = Path(message["json_path"])
        if path.exists():
            return path
    if derived_dir is None:
        return None
    candidate = derived_dir / "reddit_thread_consolidation.json"
    return candidate if candidate.exists() else None


def _content_record_path(packet_dir: Path | None) -> Path | None:
    if packet_dir is None:
        return None
    candidates = [
        packet_dir / "raw" / "01_content_record.json",
        packet_dir / "content_record.json",
    ]
    existing = [path for path in candidates if path.exists()]
    return existing[0] if len(existing) == 1 else None


def _resolve_parsed_content(
    *,
    consolidation: dict[str, Any] | None,
    content_record: dict[str, Any] | None,
) -> tuple[dict[str, Any], str | None]:
    if isinstance(consolidation, dict):
        parsed = consolidation.get("reddit_thread_consolidation")
        if isinstance(parsed, dict):
            return parsed, "reddit_thread_consolidation"
    if (
        isinstance(content_record, dict)
        and content_record.get("record_kind") == "reddit_thread_content_v0"
        and isinstance(content_record.get("thread"), dict)
        and isinstance(content_record.get("counts"), dict)
        and isinstance(content_record.get("comments"), list)
    ):
        return content_record, "reddit_thread_content_v0"
    return {}, None


def _parser_warning_count(comments: object) -> int:
    if not isinstance(comments, list):
        return 0
    total = 0
    for comment in comments:
        if isinstance(comment, dict) and isinstance(comment.get("parser_warnings"), list):
            total += len(comment["parser_warnings"])
    return total


def _resolve_maybe_relative_path(value: object, *, base: Path) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if path.exists():
        return path
    if not path.is_absolute():
        candidate = base / path
        if candidate.exists():
            return candidate
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else None


def _render_receipt(artifact: dict[str, Any]) -> str:
    data = artifact["reddit_batch_quality_summary"]
    counts = data["counts"]
    lines = [
        "# Reddit Batch Quality Summary Receipt",
        "",
        f"- Batch summary: `{data['batch_summary_path']}`",
        f"- Slots: {counts['slot_count']}",
        f"- Capture success: {counts['capture_success_count']}",
        f"- Consolidation success: {counts['consolidation_success_count']}",
        f"- Parsed content success: {counts['parsed_success_count']}",
        f"- Usable yes: {counts['usable_yes_count']}",
        f"- Usable needs_review: {counts['usable_needs_review_count']}",
        f"- Usable no: {counts['usable_no_count']}",
        "",
        "## Slot Quality",
    ]
    for row in data["results"]:
        flags = ", ".join(row["quality_flags"]) if row["quality_flags"] else "none"
        lines.extend(
            [
                f"- `{row['slot_id']}`: {row['usable_for_downstream']} "
                f"(HTTP {row['http_status']}, comments {row['comments_parsed']}/"
                f"{row['observable_comment_nodes']}, flags: {flags})",
            ]
        )
    lines.extend(["", "## Non-Claims"])
    lines.extend(f"- {item}" for item in data["non_claims"])
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize quality signals from an existing old Reddit direct-HTTP batch "
            "without fetching Reddit again."
        )
    )
    parser.add_argument("--batch-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--json-name", default="reddit_batch_quality_summary.json")
    parser.add_argument("--receipt-name", default="reddit_batch_quality_summary_receipt.md")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = build_reddit_batch_quality_summary(
            batch_summary_path=args.batch_summary,
            output_directory=args.output_dir,
            json_name=args.json_name,
            receipt_name=args.receipt_name,
        )
    except ValueError as exc:
        parser.exit(status=2, message=f"reddit batch quality summary failed: {exc}\n")
    except Exception as exc:
        parser.exit(status=3, message=f"reddit batch quality summary failed: {exc}\n")

    print(result["json_path"])
    print(result["receipt_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
