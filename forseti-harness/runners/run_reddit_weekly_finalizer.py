"""Finalize one completed Reddit Top100 deep dive for agent retrieval.

The preliminary deep-dive manifest owns original listing order and context.
The extract JSONLs own final yes/no outcomes. This runner joins those sources,
verifies that every admitted thread has a matching readable content record,
and emits one deterministic catalog plus one completion manifest. It does not
change source extracts or write Judgment into the neutral Data Lake.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners._scaffold import exit_on_failure


COMPLETION_SCHEMA = "forseti.reddit.weekly_completion.v1"
CATALOG_ROW_SCHEMA = "forseti.reddit.weekly_thread_catalog_row.v1"
EVIDENCE_READ_RECEIPT_SCHEMA = "forseti.reddit.weekly_evidence_read_receipt.v1"
READ_POLICY_ID = "reddit_weekly_value_bounded_read_v1"
_BATCH_EXTRACT_RE = re.compile(r"batch_\d{3}_extracts_v1\.jsonl")
_EVIDENCE_KINDS = {
    "individual",
    "recurrence",
    "map_or_shortlist",
    "factual_or_safety",
    "dispute",
}
_STOP_REASONS = {"corpus_exhausted", "decision_relevant_novelty_plateau"}
_RECURRENCE_STATUS_BY_COUNT = {
    1: "lead",
    2: "emerging",
    3: "corroborated",
    4: "corroborated",
    5: "sufficient",
}


def finalize_reddit_weekly_run(
    *,
    deep_dive_dir: Path,
    output_dir: Path,
    as_of: dt.date,
) -> dict[str, Any]:
    deep_dive_dir = deep_dive_dir.resolve()
    output_dir = output_dir.resolve()
    source_manifest_path = deep_dive_dir / "deep_dive_manifest_v1.json"
    source_manifest = _read_json_object(source_manifest_path, "deep-dive manifest")
    if source_manifest.get("schema") != "forseti.reddit.weekly_deep_dive_manifest.v1":
        raise ValueError("unsupported deep-dive manifest schema")
    manifest_read_policy_id = source_manifest.get("read_policy_id")
    if "read_policy_id" in source_manifest and manifest_read_policy_id != READ_POLICY_ID:
        raise ValueError(
            "unsupported deep-dive manifest read_policy_id: "
            f"{manifest_read_policy_id!r}"
        )

    manifest_rows = _manifest_rows(source_manifest)
    manifest_by_id = _unique_rows_by_thread_id(manifest_rows, "deep-dive manifest")
    extract_paths = _extract_paths(deep_dive_dir)
    extract_rows = _extract_rows(extract_paths)
    extract_by_id = _unique_rows_by_thread_id(
        [row["extract"] for row in extract_rows], "extract corpus"
    )

    manifest_ids = set(manifest_by_id)
    extract_ids = set(extract_by_id)
    if manifest_ids != extract_ids:
        missing = sorted(manifest_ids - extract_ids)
        unexpected = sorted(extract_ids - manifest_ids)
        raise ValueError(
            "manifest/extract thread set mismatch: "
            f"missing_extracts={missing[:5]} unexpected_extracts={unexpected[:5]}"
        )

    coverage = _required_object(
        source_manifest.get("coverage", {}), "deep-dive manifest coverage"
    )
    declared_admitted = _required_int(
        coverage.get("admitted"),
        "deep-dive manifest coverage.admitted",
    )
    if declared_admitted != len(extract_rows):
        raise ValueError(
            "deep-dive manifest admitted count does not match final extracts: "
            f"declared={declared_admitted} extracts={len(extract_rows)}"
        )

    transcript_by_id = _transcript_paths(deep_dive_dir)
    source_by_id = {
        row["extract"]["thread_id"]: row for row in extract_rows
    }
    catalog_rows = []
    for catalog_order, manifest_row in enumerate(manifest_rows, start=1):
        thread_id = manifest_row["thread_id"]
        source = source_by_id[thread_id]
        extract = source["extract"]
        content_record_path = _required_existing_path(
            extract.get("content_record"), f"thread {thread_id} content_record"
        )
        content_record = _read_json_object(
            content_record_path, f"thread {thread_id} content record"
        )
        content_thread = content_record.get("thread")
        if not isinstance(content_thread, dict) or content_thread.get("thread_id") != thread_id:
            raise ValueError(f"thread {thread_id} content record identity mismatch")
        admission = extract.get("admission")
        if admission not in {"yes", "no"}:
            raise ValueError(f"thread {thread_id} has non-final admission {admission!r}")
        if not _has_summary(extract):
            raise ValueError(f"thread {thread_id} has no agent-readable outcome summary")
        validated_receipt = _validated_evidence_read_receipt(
            extract=extract,
            content_record=content_record,
            thread_id=thread_id,
            admission=admission,
            manifest_read_policy_id=manifest_read_policy_id,
        )
        catalog_extract = dict(extract)
        if validated_receipt is not None:
            catalog_extract["evidence_read_receipt"] = validated_receipt
        catalog_policy = (
            {"read_policy_id": manifest_read_policy_id}
            if manifest_read_policy_id is not None
            else {}
        )

        transcript_path = transcript_by_id.get(thread_id)
        catalog_rows.append(
            {
                **catalog_extract,
                "schema": CATALOG_ROW_SCHEMA,
                **catalog_policy,
                "title": content_thread.get("title"),
                # Store the pointer this run actually resolved and read, so the
                # catalog's advertised full-text field does not depend on the
                # working directory the finalizer happened to run from.
                "content_record": str(content_record_path),
                "catalog_order": catalog_order,
                "original_order": manifest_row.get("deep_dive_order"),
                "capture_wave": manifest_row.get("capture_wave"),
                "origin": manifest_row["origin"],
                "listing": {
                    "title": manifest_row.get("title_or_none") or manifest_row.get("title"),
                    "subreddit": manifest_row.get("subreddit"),
                    "url": manifest_row.get("thread_url"),
                    "score": manifest_row.get("listing_snapshot", {}).get("score"),
                    "comments": manifest_row.get("listing_snapshot", {}).get("comments"),
                },
                "captured_thread": {
                    "title": content_thread.get("title"),
                    "subreddit": content_thread.get("subreddit"),
                    "url": content_record.get("source_url") or extract.get("url"),
                },
                "source_extract": {
                    "path": source["path"],
                    "line": source["line"],
                },
                "transcript": str(transcript_path) if transcript_path is not None else None,
            }
        )

    counts = Counter(row["admission"] for row in catalog_rows)
    catalog_name = f"reddit_top100_{as_of.isoformat()}_threads.jsonl"
    catalog_text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in catalog_rows
    )
    run = {
        "schema": COMPLETION_SCHEMA,
        "run_name": f"Reddit Top100 {as_of.isoformat()}",
        "as_of": as_of.isoformat(),
        "status": "complete",
        "methodology_id": source_manifest.get("methodology_id"),
        "decision_frame": source_manifest.get("decision_frame"),
        "catalog": catalog_name,
        "source_manifest": str(source_manifest_path),
        "counts": {
            "threads": len(catalog_rows),
            "yes": counts["yes"],
            "no": counts["no"],
            "content_records_resolved": len(catalog_rows),
            "transcripts_available": sum(row["transcript"] is not None for row in catalog_rows),
        },
        "agent_usage": {
            "start_here": "Filter the catalog before opening full text.",
            "filter_fields": [
                "admission",
                "subreddit",
                "title",
                "core_problem",
                "commercial_signal",
                "reason_codes",
                "named_brands",
            ],
            "full_text_field": "content_record",
        },
        "limitations": [
            "Catalog rows are an access aid, not neutral Data Lake authority.",
            "Capture completeness and caveats remain thread-specific in each catalog row.",
            "The bundle remains only as durable as its output directory and "
            "referenced content records.",
        ],
    }
    if manifest_read_policy_id is not None:
        run["read_policy_id"] = manifest_read_policy_id
    run_text = json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / catalog_name
    run_path = output_dir / "run.json"
    _write_deterministic_pair(
        first=(catalog_path, catalog_text),
        second=(run_path, run_text),
    )
    return {"run_path": str(run_path), "catalog_path": str(catalog_path), **run["counts"]}


def _manifest_rows(source_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    existing = source_manifest.get("existing_admitted_captures")
    pending = source_manifest.get("pending")
    if not isinstance(existing, list) or not isinstance(pending, list):
        raise ValueError("deep-dive manifest must contain existing and pending thread arrays")
    return [
        {**_required_object(row, "existing manifest row"), "origin": "existing_admitted_capture"}
        for row in existing
    ] + [
        {**_required_object(row, "pending manifest row"), "origin": "deep_dive_queue"}
        for row in pending
    ]


def _extract_paths(deep_dive_dir: Path) -> list[Path]:
    batch_paths = sorted(
        path
        for path in deep_dive_dir.iterdir()
        if path.is_file() and _BATCH_EXTRACT_RE.fullmatch(path.name)
    )
    existing_path = deep_dive_dir / "existing_11_extracts_v1.jsonl"
    paths = ([existing_path] if existing_path.is_file() else []) + batch_paths
    if not paths:
        raise ValueError("no weekly deep-dive extract JSONLs found")
    return paths


def _extract_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {path.name}:{line_number}: {exc.msg}") from exc
            rows.append(
                {
                    "extract": _required_object(loaded, f"{path.name}:{line_number}"),
                    "path": str(path),
                    "line": line_number,
                }
            )
    return rows


def _transcript_paths(deep_dive_dir: Path) -> dict[str, Path]:
    transcripts: dict[str, Path] = {}
    for directory in sorted(deep_dive_dir.glob("transcripts-*")):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.txt")):
            thread_id = path.stem
            if thread_id in transcripts:
                raise ValueError(f"duplicate transcript for thread {thread_id}")
            transcripts[thread_id] = path.resolve()
    return transcripts


def _unique_rows_by_thread_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    by_id = {}
    for row in rows:
        thread_id = row.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id.strip():
            raise ValueError(f"{label} row is missing thread_id")
        if thread_id in by_id:
            raise ValueError(f"duplicate thread_id in {label}: {thread_id}")
        by_id[thread_id] = row
    return by_id


def _has_summary(row: dict[str, Any]) -> bool:
    if isinstance(row.get("core_problem"), str) and row["core_problem"].strip():
        return True
    material_addition = row.get("material_addition")
    return (
        isinstance(material_addition, dict)
        and isinstance(material_addition.get("decision_effect"), str)
        and bool(material_addition["decision_effect"].strip())
    )


def _validated_evidence_read_receipt(
    *,
    extract: dict[str, Any],
    content_record: dict[str, Any],
    thread_id: str,
    admission: str,
    manifest_read_policy_id: Any,
) -> dict[str, Any] | None:
    if "evidence_read_receipt" not in extract:
        if manifest_read_policy_id == READ_POLICY_ID:
            raise ValueError(
                f"thread {thread_id} is missing evidence_read_receipt required by "
                f"manifest read_policy_id {READ_POLICY_ID!r}"
            )
        return None
    if manifest_read_policy_id != READ_POLICY_ID:
        raise ValueError(
            f"thread {thread_id} supplies evidence_read_receipt without matching "
            f"manifest read_policy_id {READ_POLICY_ID!r}"
        )
    if "independent_reporters" in extract:
        raise ValueError(
            f"thread {thread_id} new-policy extract must not carry top-level "
            "independent_reporters; the finalizer derives it per claim"
        )

    label = f"thread {thread_id} evidence_read_receipt"
    receipt = _required_object(extract.get("evidence_read_receipt"), label)
    _require_exact_keys(
        receipt,
        {
            "schema",
            "policy_id",
            "comments_reviewed",
            "stop_reason",
            "consecutive_no_value_batches",
            "claims",
        },
        label,
    )
    if receipt.get("schema") != EVIDENCE_READ_RECEIPT_SCHEMA:
        raise ValueError(f"{label}.schema must be {EVIDENCE_READ_RECEIPT_SCHEMA!r}")
    if receipt.get("policy_id") != READ_POLICY_ID:
        raise ValueError(f"{label}.policy_id must be {READ_POLICY_ID!r}")

    comments = content_record.get("comments")
    if not isinstance(comments, list) or not all(isinstance(row, dict) for row in comments):
        raise ValueError(f"thread {thread_id} content record comments must be an array of objects")
    comments_reviewed = _required_nonnegative_int(
        receipt.get("comments_reviewed"), f"{label}.comments_reviewed"
    )
    if comments_reviewed > len(comments):
        raise ValueError(
            f"{label}.comments_reviewed exceeds captured comments: "
            f"reviewed={comments_reviewed} captured={len(comments)}"
        )
    stop_reason = receipt.get("stop_reason")
    if stop_reason not in _STOP_REASONS:
        raise ValueError(f"{label}.stop_reason is unsupported: {stop_reason!r}")
    if stop_reason == "corpus_exhausted" and comments_reviewed != len(comments):
        raise ValueError(
            f"{label} corpus_exhausted requires comments_reviewed to equal "
            f"captured comments: reviewed={comments_reviewed} captured={len(comments)}"
        )
    no_value_batches = _required_nonnegative_int(
        receipt.get("consecutive_no_value_batches"),
        f"{label}.consecutive_no_value_batches",
    )
    if stop_reason == "decision_relevant_novelty_plateau" and no_value_batches != 2:
        raise ValueError(
            f"{label} novelty plateau requires exactly two consecutive no-value batches"
        )

    claims = receipt.get("claims")
    if not isinstance(claims, list) or not all(isinstance(claim, dict) for claim in claims):
        raise ValueError(f"{label}.claims must be an array of objects")
    if admission == "yes" and not claims:
        raise ValueError(f"{label}.claims must contain at least one claim for admission yes")

    comments_by_id = _comments_by_id(comments, thread_id=thread_id)
    post = content_record.get("post")
    post_author = _visible_author(
        post.get("author_state") if isinstance(post, dict) else None
    )
    claim_ids: set[str] = set()
    validated_claims = []
    for position, claim in enumerate(claims, start=1):
        claim_label = f"{label}.claims[{position}]"
        _require_exact_keys(
            claim,
            {
                "claim_id",
                "statement",
                "evidence_kind",
                "corroboration_status",
                "support_comment_ids",
                "counter_comment_ids",
            },
            claim_label,
        )
        claim_id = _required_nonempty_string(claim.get("claim_id"), f"{claim_label}.claim_id")
        if claim_id in claim_ids:
            raise ValueError(f"{label} has duplicate claim_id {claim_id!r}")
        claim_ids.add(claim_id)
        _required_nonempty_string(claim.get("statement"), f"{claim_label}.statement")
        evidence_kind = claim.get("evidence_kind")
        if evidence_kind not in _EVIDENCE_KINDS:
            raise ValueError(f"{claim_label}.evidence_kind is unsupported: {evidence_kind!r}")
        support_ids = _required_comment_ids(
            claim.get("support_comment_ids"),
            f"{claim_label}.support_comment_ids",
            maximum=5,
        )
        counter_ids = _required_comment_ids(
            claim.get("counter_comment_ids"),
            f"{claim_label}.counter_comment_ids",
        )
        overlap = sorted(set(support_ids) & set(counter_ids))
        if overlap:
            raise ValueError(
                f"{claim_label} comment IDs cannot be both support and counter: {overlap}"
            )
        support_comments = _resolve_comment_ids(
            support_ids, comments_by_id=comments_by_id, label=f"{claim_label}.support_comment_ids"
        )
        _resolve_comment_ids(
            counter_ids, comments_by_id=comments_by_id, label=f"{claim_label}.counter_comment_ids"
        )

        status = claim.get("corroboration_status")
        if evidence_kind == "recurrence":
            expected_status = _RECURRENCE_STATUS_BY_COUNT.get(len(support_ids))
            if expected_status is None:
                raise ValueError(
                    f"{claim_label} recurrence requires one to five support comments"
                )
            if status != expected_status:
                raise ValueError(
                    f"{claim_label}.corroboration_status must be {expected_status!r} "
                    f"for {len(support_ids)} distinct reporters"
                )
            reporter_handles = _recurrence_reporter_handles(
                support_comments,
                post_author=post_author,
                label=claim_label,
            )
        else:
            if status != "not_applicable":
                raise ValueError(
                    f"{claim_label}.corroboration_status must be 'not_applicable' "
                    f"for evidence_kind {evidence_kind!r}"
                )
            reporter_handles = _structurally_eligible_reporter_handles(
                support_comments, post_author=post_author
            )

        validated_claims.append(
            {
                **claim,
                "independent_reporters": {
                    "count": len(reporter_handles),
                    "handles": reporter_handles,
                },
            }
        )
    return {**receipt, "claims": validated_claims}


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"{label} has invalid fields: missing={missing} unexpected={unexpected}"
        )


def _required_nonnegative_int(value: Any, label: str) -> int:
    result = _required_int(value, label)
    if result < 0:
        raise ValueError(f"{label} must be nonnegative")
    return result


def _required_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _required_comment_ids(
    value: Any, label: str, *, maximum: int | None = None
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    result = [
        _required_nonempty_string(comment_id, f"{label} entry")
        for comment_id in value
    ]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicate comment IDs")
    if maximum is not None and len(result) > maximum:
        raise ValueError(f"{label} may contain at most {maximum} comment IDs")
    return result


def _comments_by_id(
    comments: list[dict[str, Any]], *, thread_id: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for comment in comments:
        comment_id = comment.get("comment_id")
        if not isinstance(comment_id, str) or not comment_id.strip():
            continue
        if comment_id in result:
            raise ValueError(
                f"thread {thread_id} content record has duplicate comment_id {comment_id!r}"
            )
        result[comment_id] = comment
    return result


def _resolve_comment_ids(
    comment_ids: list[str], *, comments_by_id: dict[str, dict[str, Any]], label: str
) -> list[dict[str, Any]]:
    missing = [comment_id for comment_id in comment_ids if comment_id not in comments_by_id]
    if missing:
        raise ValueError(f"{label} contains IDs absent from the content record: {missing}")
    return [comments_by_id[comment_id] for comment_id in comment_ids]


def _visible_author(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    author = value.strip()
    lowered = author.casefold()
    if lowered in {"[deleted]", "deleted", "[removed]", "removed", "unavailable"}:
        return None
    if lowered.startswith("unknown_with_reason:"):
        return None
    return author


def _recurrence_reporter_handles(
    comments: list[dict[str, Any]], *, post_author: str | None, label: str
) -> list[str]:
    if post_author is None:
        raise ValueError(f"{label} recurrence cannot verify independence without a visible post author")
    handles: dict[str, str] = {}
    for comment in comments:
        comment_id = comment["comment_id"]
        if comment.get("comment_posture") != "present":
            raise ValueError(
                f"{label} recurrence support comment {comment_id!r} must have present posture"
            )
        author = _visible_author(comment.get("author_state"))
        if author is None:
            raise ValueError(
                f"{label} recurrence support comment {comment_id!r} has no visible author"
            )
        key = author.casefold()
        if key == post_author.casefold():
            raise ValueError(
                f"{label} recurrence support comment {comment_id!r} is authored by the OP"
            )
        if key in handles:
            raise ValueError(
                f"{label} recurrence support comments must have distinct authors: {author!r}"
            )
        handles[key] = author
    return sorted(handles.values(), key=lambda handle: (handle.casefold(), handle))


def _structurally_eligible_reporter_handles(
    comments: list[dict[str, Any]], *, post_author: str | None
) -> list[str]:
    if post_author is None:
        return []
    handles: dict[str, str] = {}
    for comment in comments:
        if comment.get("comment_posture") != "present":
            continue
        author = _visible_author(comment.get("author_state"))
        if author is None or author.casefold() == post_author.casefold():
            continue
        handles.setdefault(author.casefold(), author)
    return sorted(handles.values(), key=lambda handle: (handle.casefold(), handle))


def _write_deterministic_pair(
    *, first: tuple[Path, str], second: tuple[Path, str]
) -> None:
    outputs = (first, second)
    existing = [path for path, _ in outputs if path.exists()]
    if existing:
        if len(existing) == len(outputs) and all(
            path.read_text(encoding="utf-8") == text for path, text in outputs
        ):
            return
        raise ValueError(
            "completion output already exists with different or partial content: "
            f"{existing[0]}"
        )
    temporary = []
    try:
        for path, text in outputs:
            temp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
            temp.write_text(text, encoding="utf-8", newline="\n")
            temporary.append((temp, path))
        for temp, path in temporary:
            temp.replace(path)
    finally:
        for temp, _ in temporary:
            temp.unlink(missing_ok=True)


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} not found: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {path}: {exc}") from exc
    return _required_object(loaded, label)


def _required_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _required_existing_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is missing")
    path = Path(value)
    if not path.is_file():
        raise ValueError(f"{label} does not resolve: {path}")
    return path.resolve()


def _required_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Finalize one completed Reddit Top100 deep dive for agent retrieval."
    )
    parser.add_argument("--deep-dive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--as-of", type=dt.date.fromisoformat, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    with exit_on_failure(parser, runner_name="reddit weekly finalizer"):
        result = finalize_reddit_weekly_run(
            deep_dive_dir=args.deep_dive_dir,
            output_dir=args.output_dir or args.deep_dive_dir,
            as_of=args.as_of,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
