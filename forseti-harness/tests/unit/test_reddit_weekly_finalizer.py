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


def test_finalizer_keeps_extract_admission_over_preliminary_manifest(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    manifest = json.loads(
        (deep_dive / "deep_dive_manifest_v1.json").read_text(encoding="utf-8")
    )
    assert manifest["existing_admitted_captures"][0]["admission"] == "borderline"
    assert manifest["pending"][0]["admission"] == "yes"

    result = _finalize(deep_dive, tmp_path / "output")

    assert [row["admission"] for row in _rows(result)] == ["yes", "no"]
    assert (result["yes"], result["no"]) == (1, 1)


def test_finalizer_catalog_content_records_resolve_outside_the_runner_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deep_dive = _fixture(tmp_path)
    for name in ("existing_11_extracts_v1.jsonl", "batch_001_extracts_v1.jsonl"):
        path = deep_dive / name
        row = json.loads(path.read_text(encoding="utf-8"))
        row["content_record"] = Path(row["content_record"]).relative_to(tmp_path).as_posix()
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = _finalize(deep_dive, tmp_path / "output")
    monkeypatch.undo()

    pointers = [Path(row["content_record"]) for row in _rows(result)]
    assert len(pointers) == result["content_records_resolved"]
    assert all(pointer.is_absolute() and pointer.is_file() for pointer in pointers)


def test_finalizer_tolerates_blank_lines_and_rejects_malformed_extract_lines(
    tmp_path: Path,
) -> None:
    deep_dive = _fixture(tmp_path)
    batch = deep_dive / "batch_001_extracts_v1.jsonl"
    batch.write_text(
        "\n   \n" + batch.read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )

    assert _finalize(deep_dive, tmp_path / "output")["threads"] == 2

    (deep_dive / "batch_002_extracts_v1.jsonl").write_text("{\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"invalid JSON in batch_002_extracts_v1\.jsonl:1"):
        _finalize(deep_dive, tmp_path / "malformed")


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


def test_finalizer_rejects_non_object_manifest_coverage(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)
    manifest_path = deep_dive / "deep_dive_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["coverage"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="deep-dive manifest coverage must be a JSON object"):
        _finalize(deep_dive, tmp_path / "output")


@pytest.mark.parametrize(
    ("reporter_count", "status"),
    [(1, "lead"), (2, "emerging"), (3, "corroborated"), (4, "corroborated"), (5, "sufficient")],
)
def test_new_read_policy_accepts_recurrence_boundaries_and_derives_sorted_reporters(
    tmp_path: Path, reporter_count: int, status: str
) -> None:
    source_handles = ["Zulu", "alpha", "Middle", "beta", "Echo"][:reporter_count]
    deep_dive = _new_policy_fixture(tmp_path, source_handles)
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("recurrence", status, reporter_count)],
    )

    result = _finalize(deep_dive, tmp_path / "output")

    run = json.loads(Path(str(result["run_path"])).read_text(encoding="utf-8"))
    rows = _rows(result)
    receipt = rows[0]["evidence_read_receipt"]
    reporters = receipt["claims"][0]["independent_reporters"]
    assert reporters == {
        "count": reporter_count,
        "handles": sorted(source_handles, key=str.casefold),
    }
    assert run["read_policy_id"] == "reddit_weekly_value_bounded_read_v1"
    assert {row["read_policy_id"] for row in rows} == {
        "reddit_weekly_value_bounded_read_v1"
    }


def test_new_read_policy_rejects_six_support_comments(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, [f"user-{index}" for index in range(6)])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("recurrence", "sufficient", 6)],
    )

    with pytest.raises(ValueError, match="at most 5 comment IDs"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_duplicate_recurrence_authors(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["same-user", "Same-User"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("recurrence", "emerging", 2)],
    )

    with pytest.raises(ValueError, match="distinct authors"):
        _finalize(deep_dive, tmp_path / "output")


@pytest.mark.parametrize(
    ("author", "message"),
    [("OriginalPoster", "authored by the OP"), ("[deleted]", "no visible author")],
)
def test_new_read_policy_rejects_op_and_deleted_recurrence_support(
    tmp_path: Path, author: str, message: str
) -> None:
    deep_dive = _new_policy_fixture(tmp_path, [author])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("recurrence", "lead", 1)],
    )

    with pytest.raises(ValueError, match=message):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_missing_cited_comment_id(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    claim = _claim("recurrence", "lead", 1)
    claim["support_comment_ids"] = ["missing"]
    _set_new_policy_receipt(deep_dive, claims=[claim])

    with pytest.raises(ValueError, match="IDs absent from the content record"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_non_recurrence_corroboration_status(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("factual_or_safety", "corroborated", 1)],
    )

    with pytest.raises(ValueError, match="must be 'not_applicable'"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_invalid_novelty_plateau(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        stop_reason="decision_relevant_novelty_plateau",
        consecutive_no_value_batches=1,
    )

    with pytest.raises(ValueError, match="requires exactly two"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_review_count_above_captured_comments(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        comments_reviewed=2,
    )

    with pytest.raises(ValueError, match="exceeds captured comments"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_corpus_exhausted_requires_every_captured_comment_reviewed(
    tmp_path: Path,
) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter-1", "reporter-2"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        comments_reviewed=1,
    )

    with pytest.raises(ValueError, match="corpus_exhausted requires comments_reviewed to equal"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_rejects_more_distinct_citations_than_comments_reviewed(
    tmp_path: Path,
) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        comments_reviewed=0,
        stop_reason="decision_relevant_novelty_plateau",
        consecutive_no_value_batches=2,
    )

    with pytest.raises(ValueError, match="cites more distinct comments than comments_reviewed"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_read_policy_yes_requires_a_claim_but_no_may_have_none(tmp_path: Path) -> None:
    yes_deep_dive = _new_policy_fixture(tmp_path / "yes", ["reporter"])
    _set_new_policy_receipt(yes_deep_dive, claims=[])
    with pytest.raises(ValueError, match="at least one claim for admission yes"):
        _finalize(yes_deep_dive, tmp_path / "yes-output")

    no_deep_dive = _new_policy_fixture(tmp_path / "no", ["reporter"])
    _set_new_policy_receipt(no_deep_dive, claims=[], admission="no")
    result = _finalize(no_deep_dive, tmp_path / "no-output")
    assert _rows(result)[0]["evidence_read_receipt"]["claims"] == []


def test_new_read_policy_rejects_manual_top_level_independent_reporters(
    tmp_path: Path,
) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        top_level_reporters={"count": 99, "handles": ["invented"]},
    )

    with pytest.raises(ValueError, match="must not carry top-level independent_reporters"):
        _finalize(deep_dive, tmp_path / "output")


@pytest.mark.parametrize("policy_id", [None, "reddit_weekly_other_read_v1"])
def test_supplied_receipt_rejects_missing_or_mismatched_policy(
    tmp_path: Path, policy_id: str | None
) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
        policy_id=policy_id,
    )

    with pytest.raises(ValueError, match="policy_id"):
        _finalize(deep_dive, tmp_path / "output")


def test_new_policy_manifest_requires_every_extract_receipt(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])

    with pytest.raises(ValueError, match="missing evidence_read_receipt required by manifest"):
        _finalize(deep_dive, tmp_path / "output")


def test_finalizer_rejects_unknown_manifest_read_policy(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    manifest_path = deep_dive / "deep_dive_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["read_policy_id"] = "reddit_weekly_other_read_v1"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported deep-dive manifest read_policy_id"):
        _finalize(deep_dive, tmp_path / "output")


def test_finalizer_rejects_receipt_without_matching_manifest_policy(tmp_path: Path) -> None:
    deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
    _set_new_policy_receipt(
        deep_dive,
        claims=[_claim("individual", "not_applicable", 1)],
    )
    manifest_path = deep_dive / "deep_dive_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["read_policy_id"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="without matching manifest read_policy_id"):
        _finalize(deep_dive, tmp_path / "output")


def test_legacy_extract_without_receipt_remains_unchanged(tmp_path: Path) -> None:
    deep_dive = _fixture(tmp_path)

    result = _finalize(deep_dive, tmp_path / "output")

    run = json.loads(Path(str(result["run_path"])).read_text(encoding="utf-8"))
    rows = _rows(result)
    assert "read_policy_id" not in run
    assert all("read_policy_id" not in row for row in rows)
    assert all("evidence_read_receipt" not in row for row in rows)


@pytest.mark.parametrize("manifest_policy", [None, "reddit_weekly_value_bounded_read_v1"])
def test_extract_cannot_declare_its_own_read_policy(
    tmp_path: Path, manifest_policy: str | None
) -> None:
    # A legacy manifest must not be able to emit a catalog row advertising the
    # new policy without a validated receipt, and a new-policy manifest must not
    # silently rewrite a conflicting extract-level declaration.
    if manifest_policy is None:
        deep_dive = _fixture(tmp_path)
    else:
        deep_dive = _new_policy_fixture(tmp_path, ["reporter"])
        _set_new_policy_receipt(
            deep_dive, claims=[_claim("individual", "not_applicable", 1)]
        )
    extract_path = deep_dive / "existing_11_extracts_v1.jsonl"
    extract = json.loads(extract_path.read_text(encoding="utf-8"))
    extract["read_policy_id"] = "reddit_weekly_value_bounded_read_v1"
    extract_path.write_text(json.dumps(extract) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must not carry top-level read_policy_id"):
        _finalize(deep_dive, tmp_path / "output")


def _finalize(deep_dive: Path, output: Path) -> dict[str, object]:
    return finalize_reddit_weekly_run(
        deep_dive_dir=deep_dive, output_dir=output, as_of=dt.date(2026, 8, 11)
    )


def _rows(result: dict[str, object]) -> list[dict[str, object]]:
    text = Path(str(result["catalog_path"])).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


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
                # Pre-adjudication selection decision; the extract owns the final call.
                "admission": "borderline",
                "listing_snapshot": {"score": 20, "comments": 10},
            }
        ],
        "pending": [
            {
                "thread_id": "queued",
                "thread_url": "https://reddit.example/queued",
                "subreddit": "example",
                "title_or_none": "Queued listing title",
                "admission": "yes",
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


def _new_policy_fixture(tmp_path: Path, authors: list[str]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    deep_dive = _fixture(tmp_path)
    manifest_path = deep_dive / "deep_dive_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["read_policy_id"] = "reddit_weekly_value_bounded_read_v1"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    for extract_name, record_authors in (
        ("existing_11_extracts_v1.jsonl", authors),
        ("batch_001_extracts_v1.jsonl", []),
    ):
        extract_path = deep_dive / extract_name
        extract = json.loads(extract_path.read_text(encoding="utf-8"))
        content_record_path = Path(extract["content_record"])
        content_record = json.loads(content_record_path.read_text(encoding="utf-8"))
        content_record["post"] = {"author_state": "OriginalPoster"}
        content_record["comments"] = [
            {
                "comment_id": f"c{index}",
                "author_state": author,
                "comment_posture": "present",
                "body_text": f"Direct report {index}",
            }
            for index, author in enumerate(record_authors, start=1)
        ]
        content_record_path.write_text(json.dumps(content_record), encoding="utf-8")
        if extract_name == "batch_001_extracts_v1.jsonl":
            extract["evidence_read_receipt"] = {
                "schema": "forseti.reddit.weekly_evidence_read_receipt.v1",
                "policy_id": "reddit_weekly_value_bounded_read_v1",
                "comments_reviewed": 0,
                "stop_reason": "corpus_exhausted",
                "consecutive_no_value_batches": 0,
                "claims": [],
            }
            extract_path.write_text(json.dumps(extract) + "\n", encoding="utf-8")
    return deep_dive


def _set_new_policy_receipt(
    deep_dive: Path,
    *,
    claims: list[dict[str, object]],
    admission: str = "yes",
    comments_reviewed: int | None = None,
    stop_reason: str = "corpus_exhausted",
    consecutive_no_value_batches: int = 0,
    policy_id: str | None = "reddit_weekly_value_bounded_read_v1",
    top_level_reporters: dict[str, object] | None = None,
) -> None:
    extract_path = deep_dive / "existing_11_extracts_v1.jsonl"
    extract = json.loads(extract_path.read_text(encoding="utf-8"))
    content_record = json.loads(Path(extract["content_record"]).read_text(encoding="utf-8"))
    receipt = {
        "schema": "forseti.reddit.weekly_evidence_read_receipt.v1",
        "policy_id": policy_id,
        "comments_reviewed": (
            len(content_record["comments"])
            if comments_reviewed is None
            else comments_reviewed
        ),
        "stop_reason": stop_reason,
        "consecutive_no_value_batches": consecutive_no_value_batches,
        "claims": claims,
    }
    if policy_id is None:
        del receipt["policy_id"]
    extract["admission"] = admission
    extract["evidence_read_receipt"] = receipt
    if top_level_reporters is not None:
        extract["independent_reporters"] = top_level_reporters
    extract_path.write_text(json.dumps(extract) + "\n", encoding="utf-8")


def _claim(
    evidence_kind: str, corroboration_status: str, support_count: int
) -> dict[str, object]:
    return {
        "claim_id": "claim-1",
        "statement": "A bounded evidence point.",
        "evidence_kind": evidence_kind,
        "corroboration_status": corroboration_status,
        "support_comment_ids": [f"c{index}" for index in range(1, support_count + 1)],
        "counter_comment_ids": [],
    }


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
