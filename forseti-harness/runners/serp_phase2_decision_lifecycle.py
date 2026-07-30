"""Persist and consume Phase-2 automatic-validation licences.

This runner supplies the store semantics that the decision seal intentionally
cannot prove by itself. Receipts are retained byte-for-byte, validation claims
are immutable and cross-process atomic, and a claimed settlement receives its
prior receipt only from the store.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

try:
    from runners.serp_phase2_decision_contract import (
        ContractError,
        validate_settlement,
        validation_licenses_from_receipt,
    )
except ModuleNotFoundError:
    from serp_phase2_decision_contract import (  # type: ignore[no-redef]
        ContractError,
        validate_settlement,
        validation_licenses_from_receipt,
    )


CLAIM_VERSION = "serp_phase2_validation_claim_v0"
PROVENANCE_VERSION = "serp_phase2_settlement_provenance_v0"


class LifecycleError(ValueError):
    """Raised when persistent Phase-2 lifecycle state fails closed."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False).encode(
            "utf-8"
        )
        + b"\n"
    )


def _read_json(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"{label}_unreadable:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"{label}_invalid:{path}")
    return raw, value


def _write_new(path: Path, raw: bytes, *, already_exists: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags)
    except FileExistsError as exc:
        raise LifecycleError(f"{already_exists}:{path.name}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_idempotent(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _write_new(path, raw, already_exists="state_already_exists")
    except LifecycleError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise LifecycleError(f"state_unreadable:{path}:{exc}") from exc
        if existing != raw:
            raise LifecycleError(f"state_conflict:{path.name}")


def _atomic_replace(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def retain_receipt(store_root: Path, receipt_path: Path) -> dict[str, Any]:
    """Retain one exact receipt and return its durable reference."""

    raw, receipt = _read_json(receipt_path, label="receipt")
    try:
        subject, licensed_entities = validation_licenses_from_receipt(receipt)
    except ContractError as exc:
        raise LifecycleError(f"receipt_contract_invalid:{exc}") from exc
    digest = _sha256(raw)
    stored_path = store_root / "receipts" / f"{digest}.json"
    _write_idempotent(stored_path, raw)
    return {
        "receipt_sha256": digest,
        "subject": subject,
        "validation_entity_keys": sorted(licensed_entities),
    }


def _load_stored_receipt(
    store_root: Path, digest: str
) -> tuple[dict[str, Any], dict[str, str], set[str]]:
    if (
        len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise LifecycleError("prior_receipt_sha256_invalid")
    path = store_root / "receipts" / f"{digest}.json"
    raw, receipt = _read_json(path, label="stored_receipt")
    if _sha256(raw) != digest:
        raise LifecycleError(f"stored_receipt_digest_mismatch:{digest}")
    try:
        subject, licensed_entities = validation_licenses_from_receipt(receipt)
    except ContractError as exc:
        raise LifecycleError(f"stored_receipt_contract_invalid:{digest}:{exc}") from exc
    return receipt, subject, licensed_entities


def _claim_id(subject_entity_key: str, entry_entity_key: str) -> str:
    material = f"{subject_entity_key}\0{entry_entity_key}".encode("utf-8")
    return _sha256(material)


def _require_digest(value: str, *, label: str) -> None:
    if (
        len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise LifecycleError(f"{label}_invalid")


def claim_validation(
    store_root: Path,
    *,
    subject_entity_key: str,
    entry_entity_key: str,
    prior_receipt_sha256: str,
) -> dict[str, Any]:
    """Atomically consume the sole automatic-validation attempt."""

    _, subject, licensed_entities = _load_stored_receipt(
        store_root, prior_receipt_sha256
    )
    if subject["entity_key"] != subject_entity_key:
        raise LifecycleError("claim_subject_mismatch")
    if entry_entity_key not in licensed_entities:
        raise LifecycleError("claim_entry_not_licensed")
    claim_id = _claim_id(subject_entity_key, entry_entity_key)
    claim = {
        "schema_version": CLAIM_VERSION,
        "claim_id": claim_id,
        "subject_entity_key": subject_entity_key,
        "entry_entity_key": entry_entity_key,
        "prior_receipt_sha256": prior_receipt_sha256,
    }
    _write_new(
        store_root / "claims" / f"{claim_id}.json",
        _json_bytes(claim),
        already_exists="automatic_validation_already_claimed",
    )
    return claim


def _load_claim(store_root: Path, claim_id: str) -> dict[str, Any]:
    _require_digest(claim_id, label="claim_id")
    expected = store_root / "claims" / f"{claim_id}.json"
    _, claim = _read_json(expected, label="claim")
    if (
        claim.get("schema_version") != CLAIM_VERSION
        or claim.get("claim_id") != claim_id
        or not isinstance(claim.get("prior_receipt_sha256"), str)
        or _claim_id(
            str(claim.get("subject_entity_key", "")),
            str(claim.get("entry_entity_key", "")),
        )
        != claim_id
    ):
        raise LifecycleError(f"claim_invalid:{claim_id}")
    return claim


def seal_claimed_settlement(
    store_root: Path,
    settlement_path: Path,
    *,
    claim_ids: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Seal a settlement using only receipts bound to persisted claims."""

    settlement_raw, settlement = _read_json(
        settlement_path, label="settlement"
    )
    supplied_receipts = settlement.get("prior_decision_receipts")
    if supplied_receipts not in (None, []):
        raise LifecycleError("caller_prior_decision_receipts_forbidden")

    claims = [_load_claim(store_root, claim_id) for claim_id in claim_ids]
    if len({claim["claim_id"] for claim in claims}) != len(claims):
        raise LifecycleError("claim_id_duplicate")

    subject = settlement.get("subject")
    subject_entity_key = (
        subject.get("entity_key").strip()
        if isinstance(subject, dict)
        and isinstance(subject.get("entity_key"), str)
        and subject.get("entity_key").strip()
        else None
    )
    if any(
        claim["subject_entity_key"] != subject_entity_key for claim in claims
    ):
        raise LifecycleError("settlement_claim_subject_mismatch")

    automatic_entities: list[str] = []
    probes = settlement.get("return_probes")
    if isinstance(probes, list):
        for probe in probes:
            if (
                isinstance(probe, dict)
                and probe.get("automatic_validation") is True
                and isinstance(probe.get("entry_entity_key"), str)
            ):
                automatic_entities.append(probe["entry_entity_key"].strip())
    claimed_entities = [claim["entry_entity_key"] for claim in claims]
    if sorted(automatic_entities) != sorted(claimed_entities):
        raise LifecycleError(
            "settlement_claim_set_mismatch:"
            f"automatic={json.dumps(sorted(automatic_entities))}:"
            f"claimed={json.dumps(sorted(claimed_entities))}"
        )

    receipts_by_digest: dict[str, dict[str, Any]] = {}
    for claim in claims:
        digest = claim["prior_receipt_sha256"]
        receipt, receipt_subject, licensed_entities = _load_stored_receipt(
            store_root, digest
        )
        if receipt_subject["entity_key"] != claim["subject_entity_key"]:
            raise LifecycleError(f"claim_receipt_subject_mismatch:{claim['claim_id']}")
        if claim["entry_entity_key"] not in licensed_entities:
            raise LifecycleError(f"claim_receipt_license_missing:{claim['claim_id']}")
        receipts_by_digest[digest] = receipt

    settlement_for_seal = dict(settlement)
    settlement_for_seal["prior_decision_receipts"] = list(
        receipts_by_digest.values()
    )
    try:
        receipt = validate_settlement(settlement_for_seal)
    except ContractError as exc:
        raise LifecycleError(f"settlement_contract_invalid:{exc}") from exc

    receipt_raw = _json_bytes(receipt)
    receipt_digest = _sha256(receipt_raw)
    provenance = {
        "schema_version": PROVENANCE_VERSION,
        "subject_entity_key": subject_entity_key,
        "settlement_sha256": _sha256(settlement_raw),
        "receipt_sha256": receipt_digest,
        "claim_ids": sorted(claim["claim_id"] for claim in claims),
        "prior_receipt_sha256s": sorted(receipts_by_digest),
    }
    _write_idempotent(
        store_root / "outcomes" / f"{receipt_digest}.provenance.json",
        _json_bytes(provenance),
    )
    return receipt, provenance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    retain = subparsers.add_parser("retain")
    retain.add_argument("--store-root", required=True, type=Path)
    retain.add_argument("--receipt", required=True, type=Path)

    claim = subparsers.add_parser("claim")
    claim.add_argument("--store-root", required=True, type=Path)
    claim.add_argument("--subject-entity-key", required=True)
    claim.add_argument("--entry-entity-key", required=True)
    claim.add_argument("--prior-receipt-sha256", required=True)
    claim.add_argument("--output", type=Path)

    seal = subparsers.add_parser("seal")
    seal.add_argument("--store-root", required=True, type=Path)
    seal.add_argument("--settlement", required=True, type=Path)
    seal.add_argument("--claim-id", action="append", default=[])
    seal.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "retain":
            result = retain_receipt(args.store_root, args.receipt)
        elif args.command == "claim":
            result = claim_validation(
                args.store_root,
                subject_entity_key=args.subject_entity_key,
                entry_entity_key=args.entry_entity_key,
                prior_receipt_sha256=args.prior_receipt_sha256,
            )
            if args.output:
                _atomic_replace(args.output, _json_bytes(result))
        else:
            receipt, provenance = seal_claimed_settlement(
                args.store_root,
                args.settlement,
                claim_ids=args.claim_id,
            )
            _atomic_replace(args.output, _json_bytes(receipt))
            result = provenance
    except (OSError, LifecycleError) as exc:
        print(f"phase2 decision lifecycle failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
