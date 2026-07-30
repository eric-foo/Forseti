import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from runners.serp_phase2_decision_contract import validate_settlement
from runners.serp_phase2_decision_lifecycle import (
    LifecycleError,
    claim_validation,
    retain_receipt,
    seal_claimed_settlement,
)


RUNNER = (
    Path(__file__).resolve().parents[2]
    / "runners"
    / "serp_phase2_decision_lifecycle.py"
)
SUBJECT_KEY = "subject|product|edp"
ENTRY_KEY = "brand|product|edp"


def _source(source_id: str, *, author: bool = False) -> dict:
    source = {
        "source_id": source_id,
        "surface_class": (
            "complaint_body" if author else "serp_rendered_snippet"
        ),
        "entity_key": ENTRY_KEY,
        "subject_entity_key": SUBJECT_KEY,
    }
    if author:
        source.update(
            {
                "author_id": "author-1",
                "thread_id": "thread-1",
                "venue": "r/example",
                "posture": "first_hand",
                "stance_bearing": True,
                "engagement": {"score": 5, "rank_in_thread": 1},
            }
        )
    return source


def _weak_settlement() -> dict:
    return {
        "schema_version": "serp_phase2_decision_settlement_v0",
        "subject": {"name": "Subject", "entity_key": SUBJECT_KEY},
        "entries": [
            {
                "name": "Example Product",
                "entity_key": ENTRY_KEY,
                "subject_entity_key": SUBJECT_KEY,
                "rung": "finding_grade",
                "sources": [_source("serp-1"), _source("comment-1", author=True)],
                "automatic_validation_attempts": 0,
                "decision": {
                    "action": "validate_once",
                    "confidence": "weak",
                    "decision_ready": False,
                },
            }
        ],
        "return_probes": [
            {
                "job_id": "scout-1",
                "entry_entity_key": ENTRY_KEY,
                "automatic_validation": False,
                "partial": False,
            }
        ],
        "capture_accounting": {"partial_probes": 0},
        "summary": {
            "entry_count": 1,
            "decision_ready_names": [],
            "validate_once_names": ["Example Product"],
            "watch_names": [],
            "parked_names": [],
            "identity_correction_names": [],
        },
    }


def _postprobe_settlement() -> dict:
    payload = _weak_settlement()
    entry = payload["entries"][0]
    entry["automatic_validation_attempts"] = 1
    entry["decision"] = {
        "action": "parked_after_no_confirmation",
        "confidence": "weak",
        "decision_ready": False,
    }
    payload["return_probes"] = [
        {
            "job_id": "automatic-1",
            "entry_entity_key": ENTRY_KEY,
            "automatic_validation": True,
            "licensing_action": "validate_once",
            "partial": False,
        }
    ]
    payload["summary"]["validate_once_names"] = []
    payload["summary"]["parked_names"] = ["Example Product"]
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _retained_weak_receipt(tmp_path: Path) -> tuple[Path, str]:
    receipt_path = tmp_path / "weak-receipt.json"
    _write_json(receipt_path, validate_settlement(_weak_settlement()))
    retained = retain_receipt(tmp_path / "store", receipt_path)
    return receipt_path, retained["receipt_sha256"]


def test_lifecycle_attaches_exact_stored_receipt_and_records_provenance(
    tmp_path: Path,
) -> None:
    receipt_path, digest = _retained_weak_receipt(tmp_path)
    claim = claim_validation(
        tmp_path / "store",
        subject_entity_key=SUBJECT_KEY,
        entry_entity_key=ENTRY_KEY,
        prior_receipt_sha256=digest,
    )
    settlement_path = tmp_path / "postprobe.json"
    _write_json(settlement_path, _postprobe_settlement())

    receipt, provenance = seal_claimed_settlement(
        tmp_path / "store",
        settlement_path,
        claim_ids=[claim["claim_id"]],
    )

    assert receipt["summary"]["parked_names"] == ["Example Product"]
    assert provenance["prior_receipt_sha256s"] == [digest]
    assert (
        tmp_path / "store" / "receipts" / f"{digest}.json"
    ).read_bytes() == receipt_path.read_bytes()
    assert (
        tmp_path
        / "store"
        / "outcomes"
        / f"{provenance['receipt_sha256']}.provenance.json"
    ).is_file()


def test_caller_cannot_substitute_a_prior_receipt(tmp_path: Path) -> None:
    _, digest = _retained_weak_receipt(tmp_path)
    claim = claim_validation(
        tmp_path / "store",
        subject_entity_key=SUBJECT_KEY,
        entry_entity_key=ENTRY_KEY,
        prior_receipt_sha256=digest,
    )
    settlement = _postprobe_settlement()
    settlement["prior_decision_receipts"] = [{"valid": True}]
    settlement_path = tmp_path / "postprobe.json"
    _write_json(settlement_path, settlement)

    with pytest.raises(
        LifecycleError, match="caller_prior_decision_receipts_forbidden"
    ):
        seal_claimed_settlement(
            tmp_path / "store",
            settlement_path,
            claim_ids=[claim["claim_id"]],
        )


def test_tampered_stored_receipt_fails_before_contract_seal(
    tmp_path: Path,
) -> None:
    _, digest = _retained_weak_receipt(tmp_path)
    claim = claim_validation(
        tmp_path / "store",
        subject_entity_key=SUBJECT_KEY,
        entry_entity_key=ENTRY_KEY,
        prior_receipt_sha256=digest,
    )
    stored = tmp_path / "store" / "receipts" / f"{digest}.json"
    stored.write_bytes(stored.read_bytes() + b" ")
    settlement_path = tmp_path / "postprobe.json"
    _write_json(settlement_path, _postprobe_settlement())

    with pytest.raises(
        LifecycleError, match="stored_receipt_digest_mismatch"
    ):
        seal_claimed_settlement(
            tmp_path / "store",
            settlement_path,
            claim_ids=[claim["claim_id"]],
        )


def test_two_processes_racing_one_attempt_produce_one_claim(
    tmp_path: Path,
) -> None:
    _, digest = _retained_weak_receipt(tmp_path)
    command = [
        sys.executable,
        str(RUNNER),
        "claim",
        "--store-root",
        str(tmp_path / "store"),
        "--subject-entity-key",
        SUBJECT_KEY,
        "--entry-entity-key",
        ENTRY_KEY,
        "--prior-receipt-sha256",
        digest,
    ]
    environment = dict(os.environ, PYTHONIOENCODING="utf-8")
    contenders = [
        subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        for _ in range(2)
    ]
    results = [contender.communicate(timeout=10) for contender in contenders]

    assert sorted(contender.returncode for contender in contenders) == [0, 2]
    assert sum("automatic_validation_already_claimed" in err for _, err in results) == 1
    assert len(list((tmp_path / "store" / "claims").glob("*.json"))) == 1

    repeated = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=10,
        check=False,
    )
    assert repeated.returncode == 2
    assert "automatic_validation_already_claimed" in repeated.stderr


def test_claim_set_must_exactly_match_automatic_probes(tmp_path: Path) -> None:
    _, digest = _retained_weak_receipt(tmp_path)
    claim = claim_validation(
        tmp_path / "store",
        subject_entity_key=SUBJECT_KEY,
        entry_entity_key=ENTRY_KEY,
        prior_receipt_sha256=digest,
    )
    settlement = _postprobe_settlement()
    settlement["return_probes"][0]["automatic_validation"] = False
    settlement["return_probes"][0].pop("licensing_action")
    settlement["entries"][0]["automatic_validation_attempts"] = 0
    settlement_path = tmp_path / "postprobe.json"
    _write_json(settlement_path, settlement)

    with pytest.raises(LifecycleError, match="settlement_claim_set_mismatch"):
        seal_claimed_settlement(
            tmp_path / "store",
            settlement_path,
            claim_ids=[claim["claim_id"]],
        )


def test_claim_id_cannot_escape_the_store(tmp_path: Path) -> None:
    settlement_path = tmp_path / "postprobe.json"
    _write_json(settlement_path, _postprobe_settlement())

    with pytest.raises(LifecycleError, match="claim_id_invalid"):
        seal_claimed_settlement(
            tmp_path / "store",
            settlement_path,
            claim_ids=["..\\outside"],
        )
