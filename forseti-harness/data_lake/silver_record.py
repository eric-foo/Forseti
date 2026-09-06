"""Silver Vault record envelope validation + the validating write front-door.

The no-blur invariant the Silver layer depends on -- a closed ``record_kind``, the
evidence-vs-fact split (a Silver observation is a FACT, never the Cleaning transform
ledger), and the MetricObservation posture coupling -- is enforced here as CODE, not
convention. ``append_silver_record`` is the validating front-door: a producer that
routes a Silver record through it cannot persist a blurred one, because validation
raises before any bytes are written.

Scope (v0): the common record header, integrity hash, source/derived-reference
lineage, no-ledger boundary, and payload-specific observation invariants.  The
generic ``data_lake.root.append_record`` stays payload-blind; this is a
Silver-aware layer ABOVE it, so Cleaning audit packs and projection/ECR records
keep writing generically.

Validation is split into two obligations that must not be collapsed:

- ``validate_silver_vault_record_stable`` checks only permanent facts about a
  persisted record -- envelope identity, required stored identifiers, the
  original canonical content hash, the no-blur/ledger boundary, and enough
  structure to select semantics.  It never changes with semantic-rule
  tightening, so immutable stored records stay readable.
- Semantic validation is selected AFTER the stable layer: a record whose exact
  ``(producer_id, producer_schema_version, lane_namespace)`` tuple is declared
  in the closed ``data_lake.silver_compatibility`` registry is validated only
  against that profile's persisted grammar (read-only compatibility); every
  other record -- including every new write -- must satisfy the complete
  current semantic grammar and strict canonical references.

Companions that close the v0 residuals: the write-path guard
``.agents/hooks/check_silver_lane_registry.py`` (a producer writing a Silver lane
through the raw writer instead of this front-door fails CI, save the named
FRONT_DOOR_PENDING lanes), and the no-blur NEGATIVE mirror
``data_lake.non_silver_record`` (a projection / cleaning-audit / ECR / signal-content
/ transcript record must not carry ``record_kind`` or this ``schema_version``, and
must carry its own role posture). Remaining residual: that negative mirror is enforced
by a conformance test, not yet wired into every producer's write path.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from typing import TYPE_CHECKING, Any, Literal

from data_lake.canonical_json import canonical_record_bytes
from data_lake.root import DataLakeRootError
from data_lake.silver_compatibility import (
    CREATOR_METRIC_LINEAGE_INDEX,
    FRAGRANTICA_INFERRED_REFS,
    compatibility_profile_for,
)

if TYPE_CHECKING:
    from pathlib import Path

    from data_lake.root import DataLakeRoot

SILVER_VAULT_RECORD_SCHEMA_VERSION = "silver_vault_record_v0"
CLOSED_RECORD_KINDS = ("entity", "relationship", "observation")
# The closed metric-posture vocabulary -- the source-capture posture kinds a Silver
# MetricObservation may carry. Kept local here, exactly like CLOSED_RECORD_KINDS, so this
# base data_lake layer enforces the contract's "posture values must map to the live
# source-capture posture vocabulary" clause without importing the capture spine. Adding a
# kind is a deliberate edit here (mirroring a capture-spine vocabulary change).
METRIC_POSTURE_KINDS = ("observed", "unavailable_with_reason", "not_attempted")
METRIC_OBSERVATION_SET_PAYLOAD_KIND = "MetricObservationSet"
TEXT_OBSERVATION_SET_PAYLOAD_KIND = "TextObservationSet"
CONTENT_HASH_BASIS = "canonical_json_excluding_content_hash"
RAW_STORED_BYTES_HASH_BASIS = "raw_stored_bytes"
DERIVED_RECORD_BYTES_HASH_BASIS = "derived_record_bytes"
CURRENT_SOURCE_BACKED_AUTHORITY = "current_source_backed"
HISTORICAL_COMPATIBLE_AUTHORITY = "historical_compatible"
INVALID_SILVER_AUTHORITY = "invalid"
UNRESOLVED_SILVER_AUTHORITY = "unresolved"
PHYSICALLY_SOURCE_BACKED_COMPLETE_STATUS = "source_backed_complete"
RAW_PACKET_TOMBSTONE_LANE = "raw_packet_tombstone_silver"
RAW_PACKET_TOMBSTONE_PRODUCER_ID = (
    "forseti-harness.data_lake.silver_record.append_raw_packet_tombstone"
)
RAW_PACKET_TOMBSTONE_SCHEMA_VERSION = "raw_packet_tombstone_relationship_v0"
RAW_PACKET_TOMBSTONE_SOURCE_SURFACE = "operator_retention_action"
RAW_PACKET_TOMBSTONE_SCOPE = "public_consumption"


@dataclass(frozen=True)
class SilverSourceAuthority:
    status: Literal[
        "current_source_backed", "historical_compatible", "invalid", "unresolved"
    ]
    reason_code: str
    error: str | None = None


# Keys that mark Cleaning processing evidence (the transform ledger). A Silver fact
# must never carry them -- that is the evidence-vs-fact half of the no-blur invariant.
_LEDGER_KEYS = ("cleaning_packet", "transform_ledger")


class SilverRecordError(ValueError):
    """A record violates the Silver Vault envelope contract (the no-blur invariant)."""


def validate_silver_vault_record_stable(record: Mapping[str, Any]) -> None:
    """Raise ``SilverRecordError`` unless ``record`` satisfies every PERMANENT
    Silver Vault obligation: envelope identity, required stored identifiers,
    the original canonical content hash, the no-blur/ledger boundary, and
    enough structure to select either current semantics or one declared
    compatibility profile.

    This layer validates the original stored mapping without modifying it and
    must stay stable as semantic rules evolve; profile- or grammar-specific
    rules belong in the semantic layers, never here.
    """
    if not isinstance(record, Mapping):
        raise SilverRecordError("Silver record must be a mapping.")

    schema_version = record.get("schema_version")
    if schema_version != SILVER_VAULT_RECORD_SCHEMA_VERSION:
        raise SilverRecordError(
            f"Silver record schema_version must be {SILVER_VAULT_RECORD_SCHEMA_VERSION!r}; "
            f"got {schema_version!r}."
        )

    for field in (
        "record_id",
        "raw_anchor",
        "lane_namespace",
        "producer_id",
        "producer_schema_version",
        "producer_row_kind",
        "source_surface",
    ):
        _require_non_empty_string(record.get(field), f"Silver {field}")
    if "observed_at" not in record:
        raise SilverRecordError("Silver common header requires observed_at.")
    observed_at = record.get("observed_at")
    if observed_at is not None:
        _require_non_empty_string(observed_at, "Silver observed_at")
    if "captured_at" not in record:
        raise SilverRecordError("Silver common header requires captured_at.")
    captured_at = record.get("captured_at")
    if captured_at is not None:
        _require_non_empty_string(captured_at, "Silver captured_at")

    if record.get("content_hash_basis") != CONTENT_HASH_BASIS:
        raise SilverRecordError(
            f"Silver content_hash_basis must be {CONTENT_HASH_BASIS!r}."
        )
    content_hash = record.get("content_hash")
    if not isinstance(content_hash, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", content_hash) is None:
        raise SilverRecordError("Silver content_hash must be sha256: followed by 64 lowercase hex characters.")

    if not isinstance(record.get("raw_refs"), list) or not isinstance(
        record.get("derived_refs"), list
    ):
        raise SilverRecordError("Silver raw_refs and derived_refs must both be lists.")

    record_kind = record.get("record_kind")
    if record_kind not in CLOSED_RECORD_KINDS:
        raise SilverRecordError(
            f"Silver record_kind must be one of {CLOSED_RECORD_KINDS}; got {record_kind!r}."
        )

    payload_kind = record.get("payload_kind")
    if not isinstance(payload_kind, str) or not payload_kind.strip():
        raise SilverRecordError("Silver payload_kind must be a non-empty string.")

    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        raise SilverRecordError("Silver record payload must be a mapping.")

    # Evidence-vs-fact: a Silver record must not carry the Cleaning transform ledger --
    # that belongs in the processing-audit sibling, not in a fact.
    _reject_ledger(payload, where="payload")

    if record_kind == "observation":
        observation = payload.get("observation")
        if not isinstance(observation, Mapping):
            raise SilverRecordError(
                "An observation record must carry a payload.observation object."
            )
        _reject_ledger(observation, where="observation")

    expected_hash = silver_content_hash(record)
    if content_hash != f"sha256:{expected_hash}":
        raise SilverRecordError("Silver content hash mismatch: content_hash does not match canonical record content.")


def _validate_current_semantics(record: Mapping[str, Any]) -> None:
    """The complete CURRENT semantic grammar: strict canonical references,
    payload-specific observation invariants, and the observed-at contract."""
    _validate_strict_lineage_refs(record)
    record_kind = record["record_kind"]
    payload = record["payload"]
    if record_kind == "observation":
        observation = payload["observation"]
        payload_kind = record["payload_kind"]
        if payload_kind == "MetricObservation":
            _validate_metric_posture(observation)
        elif payload_kind == METRIC_OBSERVATION_SET_PAYLOAD_KIND:
            _validate_metric_observation_set(observation)
        elif payload_kind == "TextObservation":
            _validate_text_observation(observation)
        elif payload_kind == TEXT_OBSERVATION_SET_PAYLOAD_KIND:
            _validate_text_observation_set(observation)
    _validate_observed_at_contract(
        record_kind=record_kind,
        observed_at=record.get("observed_at"),
        captured_at=record.get("captured_at"),
        payload=payload,
    )


def validate_silver_vault_record(record: Mapping[str, Any]) -> None:
    """Raise ``SilverRecordError`` if ``record`` is not a well-formed Silver Vault
    record.

    Runs the stable permanent layer first (envelope, identifiers, original
    content hash, no-blur), then selects semantics on the exact producer
    tuple: a tuple declared in the closed ``data_lake.silver_compatibility``
    registry is validated only against its persisted profile; every other
    record must satisfy the complete current semantic grammar.  Validation is
    deliberately fail-closed.
    """
    validate_silver_vault_record_stable(record)
    profile = compatibility_profile_for(record)
    if profile is not None:
        profile.validate_persisted(record)
    else:
        _validate_current_semantics(record)


def validate_silver_vault_record_for_write(record: Mapping[str, Any]) -> None:
    """Validate the canonical grammar required for every newly persisted record.

    A declared compatibility profile can never become writable: any record
    whose producer tuple is in the registry is rejected here regardless of how
    well-formed it is.
    """
    validate_silver_vault_record_stable(record)
    if compatibility_profile_for(record) is not None:
        raise SilverRecordError(
            "Legacy Silver producer schemas are read-only compatibility records."
        )
    _validate_current_semantics(record)


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SilverRecordError(f"{field} must be a non-empty string.")
    return value


def _validate_strict_lineage_refs(record: Mapping[str, Any]) -> None:
    raw_refs = record.get("raw_refs")
    derived_refs = record.get("derived_refs")
    if not isinstance(raw_refs, list) or not isinstance(derived_refs, list):
        raise SilverRecordError("Silver raw_refs and derived_refs must both be lists.")
    if not raw_refs and not derived_refs:
        raise SilverRecordError("A Silver record requires at least one resolvable raw_ref or derived_ref.")
    for index, ref in enumerate(raw_refs):
        if not isinstance(ref, Mapping):
            raise SilverRecordError(f"Silver raw_refs[{index}] must be a mapping.")
        ref_type = ref.get("ref_type")
        if ref_type not in ("raw_packet", "bronze_attachment_record"):
            raise SilverRecordError(
                f"Silver raw_refs[{index}].ref_type must be 'raw_packet' or "
                f"'bronze_attachment_record'; got {ref_type!r}."
            )
        _require_non_empty_string(ref.get("packet_id"), f"Silver raw_refs[{index}].packet_id")
        sha = ref.get("sha256")
        basis = ref.get("hash_basis")
        if bool(sha) != bool(basis):
            raise SilverRecordError(
                f"Silver raw_refs[{index}] sha256 and hash_basis must travel together."
            )
        if ref.get("file_id") is not None and not sha:
            raise SilverRecordError(
                f"Silver raw_refs[{index}] names a file_id but is not hash-checkable."
            )
        if sha is not None:
            _require_non_empty_string(sha, f"Silver raw_refs[{index}].sha256")
            _require_non_empty_string(basis, f"Silver raw_refs[{index}].hash_basis")
            if basis != RAW_STORED_BYTES_HASH_BASIS:
                raise SilverRecordError(
                    f"Silver raw_refs[{index}].hash_basis must be "
                    f"{RAW_STORED_BYTES_HASH_BASIS!r}."
                )
        if ref_type == "bronze_attachment_record":
            _require_non_empty_string(
                sha, f"Silver raw_refs[{index}].sha256"
            )
            _require_non_empty_string(
                basis, f"Silver raw_refs[{index}].hash_basis"
            )
            for field in ("attachment_record_id", "source_family", "source_surface"):
                _require_non_empty_string(
                    ref.get(field), f"Silver raw_refs[{index}].{field}"
                )
            body_sha = _require_non_empty_string(
                ref.get("body_sha256"), f"Silver raw_refs[{index}].body_sha256"
            )
            if body_sha != sha:
                raise SilverRecordError(
                    f"Silver raw_refs[{index}].body_sha256 must equal sha256."
                )
    for index, ref in enumerate(derived_refs):
        if not isinstance(ref, Mapping):
            raise SilverRecordError(f"Silver derived_refs[{index}] must be a mapping.")
        lane = ref.get("lane_namespace", ref.get("lane"))
        record_id = ref.get("record_id")
        _require_non_empty_string(
            ref.get("raw_anchor"), f"Silver derived_refs[{index}].raw_anchor"
        )
        _require_non_empty_string(lane, f"Silver derived_refs[{index}].lane")
        _require_non_empty_string(record_id, f"Silver derived_refs[{index}].record_id")
        sha = ref.get("sha256")
        hash_basis = ref.get("hash_basis")
        if bool(sha) != bool(hash_basis):
            raise SilverRecordError(
                f"Silver derived_refs[{index}] sha256 and hash_basis must travel together."
            )
        if sha is not None:
            _require_non_empty_string(sha, f"Silver derived_refs[{index}].sha256")
            _require_non_empty_string(
                hash_basis, f"Silver derived_refs[{index}].hash_basis"
            )
            if hash_basis != DERIVED_RECORD_BYTES_HASH_BASIS:
                raise SilverRecordError(
                    f"Silver derived_refs[{index}].hash_basis must be "
                    f"{DERIVED_RECORD_BYTES_HASH_BASIS!r}."
                )
        content_hash = ref.get("content_hash")
        content_hash_basis = ref.get("content_hash_basis")
        if bool(content_hash) != bool(content_hash_basis):
            raise SilverRecordError(
                f"Silver derived_refs[{index}] content_hash and content_hash_basis "
                "must travel together."
            )
        if content_hash is not None:
            _require_non_empty_string(
                content_hash, f"Silver derived_refs[{index}].content_hash"
            )
            _require_non_empty_string(
                content_hash_basis,
                f"Silver derived_refs[{index}].content_hash_basis",
            )
            if content_hash_basis != CONTENT_HASH_BASIS:
                raise SilverRecordError(
                    f"Silver derived_refs[{index}].content_hash_basis must be "
                    f"{CONTENT_HASH_BASIS!r}."
                )




def verify_silver_vault_record_sources(
    data_root: "DataLakeRoot",
    record: Mapping[str, Any],
    *,
    record_path: "Path | None" = None,
    creator_metric_lineage: Any | None = None,
    verification_cache: dict[str, Any] | None = None,
) -> SilverSourceAuthority:
    """Require current physical source authority and return its classification."""
    result = classify_silver_vault_record_sources(
        data_root,
        record,
        record_path=record_path,
        creator_metric_lineage=creator_metric_lineage,
        verification_cache=verification_cache,
    )
    if result.status != CURRENT_SOURCE_BACKED_AUTHORITY:
        detail = f": {result.error}" if result.error else ""
        raise SilverRecordError(
            f"Silver source authority is {result.status} ({result.reason_code}){detail}"
        )
    return result


def classify_silver_vault_record_sources(
    data_root: "DataLakeRoot",
    record: Mapping[str, Any],
    *,
    record_path: "Path | None" = None,
    creator_metric_lineage: Any | None = None,
    verification_cache: dict[str, Any] | None = None,
) -> SilverSourceAuthority:
    """Classify current, compatible historical, invalid, and unresolved evidence.

    Read order, deliberately: the original stored envelope and content hash
    validate first; the exact producer tuple then selects either the complete
    current semantic grammar or one declared compatibility profile; physical
    source verification runs only after the selected semantics pass.  Unknown,
    contradictory, incomplete, or ambiguous legacy-looking records fail closed
    as ``invalid``.
    """
    try:
        validate_silver_vault_record_stable(record)
    except (TypeError, ValueError) as exc:
        return SilverSourceAuthority(
            INVALID_SILVER_AUTHORITY,
            "invalid_silver_envelope",
            f"{type(exc).__name__}: {exc}",
        )
    profile = compatibility_profile_for(record)
    try:
        if profile is not None:
            profile.validate_persisted(record)
        else:
            _validate_current_semantics(record)
    except (TypeError, ValueError) as exc:
        return SilverSourceAuthority(
            INVALID_SILVER_AUTHORITY,
            "invalid_silver_envelope",
            f"{type(exc).__name__}: {exc}",
        )
    if profile is not None and profile.reference_strategy == CREATOR_METRIC_LINEAGE_INDEX:
        # Status and reason pass through the cross-epoch lineage classification.
        if record_path is None:
            return SilverSourceAuthority(
                UNRESOLVED_SILVER_AUTHORITY,
                "legacy_creator_metric_record_path_required",
            )
        try:
            if creator_metric_lineage is None:
                from data_lake.creator_metric_lineage import build_creator_metric_lineage_index

                creator_metric_lineage = build_creator_metric_lineage_index(data_root)
            lineage = creator_metric_lineage.classification_for_path(record_path)
        except (OSError, TypeError, ValueError) as exc:
            return SilverSourceAuthority(
                UNRESOLVED_SILVER_AUTHORITY,
                "legacy_creator_metric_resolution_failed",
                f"{type(exc).__name__}: {exc}",
            )
        if lineage.current_source_backed_eligible:
            return SilverSourceAuthority(
                CURRENT_SOURCE_BACKED_AUTHORITY, lineage.reason_code
            )
        if lineage.status != "excluded":
            return SilverSourceAuthority(
                HISTORICAL_COMPATIBLE_AUTHORITY, lineage.reason_code
            )
        return SilverSourceAuthority(
            UNRESOLVED_SILVER_AUTHORITY, lineage.reason_code
        )
    try:
        if profile is not None and profile.reference_strategy == FRAGRANTICA_INFERRED_REFS:
            _verify_legacy_fragrantica_sources(
                data_root, record, verification_cache=verification_cache
            )
        else:
            _verify_canonical_sources(
                data_root, record, verification_cache=verification_cache
            )
    except (OSError, TypeError, ValueError, KeyError, DataLakeRootError) as exc:
        return SilverSourceAuthority(
            UNRESOLVED_SILVER_AUTHORITY,
            "source_ref_unresolved",
            f"{type(exc).__name__}: {exc}",
        )
    if profile is None:
        return SilverSourceAuthority(
            CURRENT_SOURCE_BACKED_AUTHORITY, "canonical_refs_verified"
        )
    if profile.may_classify_historical and record.get("observed_at") is None:
        return SilverSourceAuthority(
            HISTORICAL_COMPATIBLE_AUTHORITY, profile.historical_reason_code
        )
    return SilverSourceAuthority(
        CURRENT_SOURCE_BACKED_AUTHORITY, profile.current_reason_code
    )


def _verify_canonical_sources(
    data_root: "DataLakeRoot",
    record: Mapping[str, Any],
    *,
    verification_cache: dict[str, Any] | None = None,
) -> None:
    for index, ref in enumerate(record["raw_refs"]):
        try:
            if ref["ref_type"] == "raw_packet":
                _verify_raw_packet_ref(
                    data_root, ref, verification_cache=verification_cache
                )
            else:
                _verify_attachment_record_ref(
                    data_root, ref, verification_cache=verification_cache
                )
        except (OSError, TypeError, ValueError, KeyError, DataLakeRootError) as exc:
            raise SilverRecordError(
                f"Silver raw_refs[{index}] is physically unresolved or tampered: {exc}"
            ) from exc
    for index, ref in enumerate(record["derived_refs"]):
        try:
            _verify_derived_ref(
                data_root, ref, verification_cache=verification_cache
            )
        except (OSError, TypeError, ValueError, KeyError, DataLakeRootError) as exc:
            raise SilverRecordError(
                f"Silver derived_refs[{index}] is physically unresolved or tampered: {exc}"
            ) from exc


def _verify_legacy_fragrantica_sources(
    data_root: "DataLakeRoot",
    record: Mapping[str, Any],
    *,
    verification_cache: dict[str, Any] | None = None,
) -> None:
    for ref in record["raw_refs"]:
        _verify_raw_packet_ref(
            data_root,
            {**ref, "ref_type": "raw_packet"},
            verification_cache=verification_cache,
        )
    for ref in record["derived_refs"]:
        _verify_derived_ref(
            data_root,
            {**ref, "raw_anchor": record["raw_anchor"]},
            verification_cache=verification_cache,
        )

def silver_raw_refs_bound_to_own_anchor(record: Mapping[str, Any]) -> bool:
    """True iff every ``raw_ref`` names the record's own ``raw_anchor`` packet.

    ``verify_silver_vault_record_sources`` proves a ref resolves to real, unaltered
    bytes; it deliberately does NOT prove those bytes are *this* record's source,
    because lanes whose seed material legitimately lives in another packet (the
    creator-metric producers) must stay resolvable. Packet-first lanes make the
    stronger claim -- the record was captured from the packet it is anchored to --
    so they pair the shared physical gate with this binding check. Without it a
    record anchored at packet A that cites packet B's bytes verifies cleanly and
    counts as current source-backed evidence for A.
    """
    raw_anchor = record.get("raw_anchor")
    raw_refs = record.get("raw_refs")
    if not isinstance(raw_anchor, str) or not isinstance(raw_refs, list) or not raw_refs:
        return False
    return all(
        isinstance(ref, Mapping) and ref.get("packet_id") == raw_anchor
        for ref in raw_refs
    )


def _verified_raw_packet(
    data_root: "DataLakeRoot",
    packet_id: str,
    verification_cache: dict[str, Any] | None,
) -> Any:
    if verification_cache is None:
        return data_root.load_raw_packet(packet_id)
    packets = verification_cache.setdefault("raw_packets", {})
    if packet_id in packets:
        return packets[packet_id]
    loaded = data_root.load_raw_packet(packet_id)
    # A bounded cache may decline this entry; the verified read still succeeds.
    packets[packet_id] = loaded
    return loaded


def _verify_raw_packet_ref(
    data_root: "DataLakeRoot",
    ref: Mapping[str, Any],
    *,
    verification_cache: dict[str, Any] | None = None,
) -> None:
    loaded = _verified_raw_packet(
        data_root, str(ref["packet_id"]), verification_cache
    )
    file_id = ref.get("file_id")
    if file_id is None:
        claimed = ref.get("sha256")
        if claimed is not None:
            _require_exact_hash_basis(
                ref.get("hash_basis"),
                RAW_STORED_BYTES_HASH_BASIS,
                what="raw packet ref",
            )
            expected = _normalized_sha256(claimed, what="raw packet ref")
            matches = [
                row
                for row in loaded.manifest.get("preserved_files", [])
                if isinstance(row, Mapping)
                and row.get("sha256") == expected
                and row.get("hash_basis") == RAW_STORED_BYTES_HASH_BASIS
            ]
            if len(matches) != 1:
                raise SilverRecordError(
                    "packet-level sha256 did not resolve to exactly one preserved raw file"
                )
            matched_file_id = matches[0].get("file_id")
            body = loaded.bodies.get(str(matched_file_id))
            if body is None:
                raise SilverRecordError("matched preserved raw file body is unavailable")
            _verify_bytes_hash(body, claimed, what="raw packet preserved body")
        return
    body = loaded.bodies.get(str(file_id))
    if body is None:
        raise SilverRecordError(f"raw packet has no preserved file_id {file_id!r}")
    preserved = next(
        (
            row
            for row in loaded.manifest.get("preserved_files", [])
            if isinstance(row, Mapping) and row.get("file_id") == file_id
        ),
        None,
    )
    if not isinstance(preserved, Mapping):
        raise SilverRecordError(f"raw packet manifest has no file_id {file_id!r}")
    _require_exact_hash_basis(
        ref.get("hash_basis"),
        RAW_STORED_BYTES_HASH_BASIS,
        what=f"raw file {file_id!r} ref",
    )
    _require_exact_hash_basis(
        preserved.get("hash_basis"),
        RAW_STORED_BYTES_HASH_BASIS,
        what=f"raw file {file_id!r} manifest",
    )
    if preserved.get("sha256") != _normalized_sha256(
        ref.get("sha256"), what=f"raw file {file_id!r} ref"
    ):
        raise SilverRecordError(f"raw file {file_id!r} manifest sha256 mismatch")
    _verify_bytes_hash(body, ref.get("sha256"), what=f"raw file {file_id!r}")
    claimed_path = ref.get("relative_packet_path")
    if claimed_path is not None:
        if preserved.get("relative_packet_path") != claimed_path:
            raise SilverRecordError(f"raw file {file_id!r} relative_packet_path mismatch")


def _verify_attachment_record_ref(
    data_root: "DataLakeRoot",
    ref: Mapping[str, Any],
    *,
    verification_cache: dict[str, Any] | None = None,
) -> None:
    # Local import avoids coupling the payload-blind catalog module back into
    # Silver at import time while keeping the public Bronze boundary explicit.
    from data_lake.catalog import (
        load_attachment_record_body,
        source_surface_catalog_rows,
    )

    surface_key = (str(ref["source_family"]), str(ref["source_surface"]))
    surface_rows = (
        verification_cache.setdefault("attachment_surface_rows", {})
        if verification_cache is not None
        else {}
    )
    if surface_key not in surface_rows:
        surface_rows[surface_key] = source_surface_catalog_rows(
            data_root,
            source_family=surface_key[0],
            source_surface=surface_key[1],
            inspection_cache=verification_cache,
        )["attachment_record_rows"]
    rows = surface_rows[surface_key]
    matches = [
        row
        for row in rows
        if row.get("attachment_record_id") == ref["attachment_record_id"]
        and row.get("packet_id") == ref["packet_id"]
    ]
    if len(matches) != 1:
        raise SilverRecordError(
            "Bronze Attachment Record ref did not resolve to exactly one public catalog row"
        )
    attachment_record = matches[0]
    _require_exact_hash_basis(
        ref.get("hash_basis"),
        RAW_STORED_BYTES_HASH_BASIS,
        what="Bronze Attachment Record ref",
    )
    _require_exact_hash_basis(
        attachment_record.get("hash_basis"),
        RAW_STORED_BYTES_HASH_BASIS,
        what="Bronze Attachment Record catalog row",
    )
    for field in (
        "attachment_record_schema_version",
        "attachment_record_physicalization",
        "file_id",
        "relative_packet_path",
        "body_ref_kind",
        "body_ref",
        "body_sha256",
        "hash_basis",
        "payload_kind",
        "payload_schema_version",
        "replay_version_pins",
    ):
        if field in ref and ref.get(field) != attachment_record.get(field):
            raise SilverRecordError(f"Bronze Attachment Record {field} mismatch")
    body_key = (
        attachment_record.get("attachment_record_id"),
        attachment_record.get("packet_id"),
    )
    attachment_bodies = (
        verification_cache.setdefault("attachment_bodies", {})
        if verification_cache is not None
        else {}
    )
    if body_key not in attachment_bodies:
        attachment_bodies[body_key] = load_attachment_record_body(
            data_root,
            attachment_record,
            loaded_packet=_verified_raw_packet(
                data_root,
                str(attachment_record["packet_id"]),
                verification_cache,
            ),
        )
    body = attachment_bodies[body_key]
    claimed = ref.get("sha256")
    if claimed is not None:
        _verify_bytes_hash(body, claimed, what="Bronze Attachment Record body")


def _verify_derived_ref(
    data_root: "DataLakeRoot",
    ref: Mapping[str, Any],
    *,
    verification_cache: dict[str, Any] | None = None,
) -> None:
    lane = ref.get("lane_namespace", ref.get("lane"))
    path = data_root.record_path(
        subtree="derived",
        raw_anchor=str(ref["raw_anchor"]),
        lane=str(lane),
        record_id=str(ref["record_id"]),
    )
    if not path.is_file():
        raise SilverRecordError(f"derived record does not exist: {path}")
    derived_bodies = (
        verification_cache.setdefault("derived_bodies", {})
        if verification_cache is not None
        else {}
    )
    resolved_path = path.resolve()
    if resolved_path not in derived_bodies:
        derived_bodies[resolved_path] = path.read_bytes()
    body = derived_bodies[resolved_path]
    if ref.get("sha256") is not None:
        _require_exact_hash_basis(
            ref.get("hash_basis"),
            DERIVED_RECORD_BYTES_HASH_BASIS,
            what="derived record sha256",
        )
        _verify_bytes_hash(body, ref["sha256"], what="derived record bytes")
    if ref.get("content_hash") is not None:
        _require_exact_hash_basis(
            ref.get("content_hash_basis"),
            CONTENT_HASH_BASIS,
            what="derived record content_hash",
        )
        derived = json.loads(body.decode("utf-8"))
        if not isinstance(derived, Mapping) or derived.get("content_hash") != ref["content_hash"]:
            raise SilverRecordError("derived record content_hash mismatch")
        if derived.get("content_hash") != f"sha256:{silver_content_hash(derived)}":
            raise SilverRecordError("derived record content is tampered")


def _verify_bytes_hash(body: bytes, claimed: Any, *, what: str) -> None:
    expected = _normalized_sha256(claimed, what=what)
    actual = hashlib.sha256(body).hexdigest()
    if actual != expected:
        raise SilverRecordError(f"{what} sha256 mismatch")


def _normalized_sha256(claimed: Any, *, what: str) -> str:
    expected = _require_non_empty_string(claimed, f"{what} sha256")
    if expected.startswith("sha256:"):
        expected = expected.removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise SilverRecordError(f"{what} sha256 must be lowercase 64-hex")
    return expected


def _require_exact_hash_basis(value: Any, expected: str, *, what: str) -> None:
    basis = _require_non_empty_string(value, f"{what} hash_basis")
    if basis != expected:
        raise SilverRecordError(f"{what} hash_basis must be {expected!r}")


def _reject_ledger(container: Mapping[str, Any], *, where: str) -> None:
    for ledger_key in _LEDGER_KEYS:
        if ledger_key in container:
            raise SilverRecordError(
                f"A Silver fact must not carry a transform ledger (found {ledger_key!r} in "
                f"{where}); processing evidence belongs in the audit-pack sibling, not a fact."
            )


def _validate_observed_at_contract(
    *,
    record_kind: str,
    observed_at: Any,
    captured_at: Any,
    payload: Mapping[str, Any],
) -> None:
    """Keep unknown source-effective time explicit without a generic null escape hatch."""
    if record_kind == "relationship":
        return
    if record_kind != "observation":
        if observed_at is None:
            raise SilverRecordError(
                "Silver observed_at may be null only for relationships or an explicitly "
                "unknown-time observation."
            )
        return

    observation = payload.get("observation")
    if not isinstance(observation, Mapping):
        return  # The observation-shape error is raised by the caller above.
    interval = observation.get("effective_interval")
    declares_unknown_start = isinstance(interval, Mapping) and (
        interval.get("start_precision") == "unknown"
        or ("start" in interval and interval.get("start") is None)
    )
    if observed_at is not None:
        if declares_unknown_start:
            raise SilverRecordError(
                "An observation with explicitly unknown source-effective time must keep "
                "observed_at null; captured_at or recorded_at must not substitute for it."
            )
        return

    if not isinstance(interval, Mapping):
        raise SilverRecordError(
            "A null observation observed_at requires payload.observation.effective_interval."
        )
    if "start" not in interval or interval.get("start") is not None:
        raise SilverRecordError(
            "An explicitly unknown observation time requires effective_interval.start=null."
        )
    if interval.get("start_precision") != "unknown":
        raise SilverRecordError(
            "An explicitly unknown observation time requires "
            "effective_interval.start_precision='unknown'."
        )
    _require_non_empty_string(
        interval.get("unknown_reason"),
        "Unknown-time observation effective_interval.unknown_reason",
    )
    _require_non_empty_string(
        observation.get("recorded_at"), "Unknown-time observation recorded_at"
    )
    _require_non_empty_string(captured_at, "Unknown-time observation captured_at")

    evidence_refs = observation.get("evidence_refs")
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(not isinstance(ref, Mapping) or not ref for ref in evidence_refs)
    ):
        raise SilverRecordError(
            "An explicitly unknown observation time requires non-empty evidence_refs provenance."
        )
    limitations = observation.get("limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not item.strip() for item in limitations)
    ):
        raise SilverRecordError(
            "An explicitly unknown observation time requires non-empty limitations."
        )


def _validate_metric_posture(observation: Mapping[str, Any]) -> None:
    """MetricObservation posture coupling, per the Silver Vault contract's metric
    posture table: observed => value present and BOTH reason fields null; non-observed
    => value absent and A REASON present. The contract says "a reason is present" (not
    "a reason_code"), and the controlled signal is the posture ``kind`` (which maps to
    the source-capture posture vocabulary), so the reason may be carried in
    ``reason_code`` or the free-text ``reason_detail``. The posture ``kind`` itself must be
    one of the closed ``METRIC_POSTURE_KINDS`` (the source-capture posture vocabulary, kept
    local), so a looser free-text posture value cannot enter through the front-door."""
    metric_name = observation.get("metric_name")
    if not isinstance(metric_name, str) or not metric_name.strip():
        raise SilverRecordError("MetricObservation requires a non-empty metric_name.")
    posture = observation.get("metric_posture")
    if not isinstance(posture, Mapping):
        raise SilverRecordError("MetricObservation requires a metric_posture object.")
    kind = posture.get("kind")
    if kind not in METRIC_POSTURE_KINDS:
        raise SilverRecordError(
            f"MetricObservation metric_posture.kind must be one of {METRIC_POSTURE_KINDS}; "
            f"got {kind!r}. Posture values must map to the source-capture posture vocabulary."
        )
    value = observation.get("metric_value")
    has_reason = _has_posture_reason(posture)
    if kind == "observed":
        if value is None:
            raise SilverRecordError("An observed metric requires a metric_value.")
        if has_reason:
            raise SilverRecordError(
                "An observed metric must not carry a posture reason "
                "(reason_code and reason_detail must be null)."
            )
    else:
        if value is not None:
            raise SilverRecordError(
                f"A non-observed metric (kind={kind!r}) must not carry a metric_value "
                "(absence must never be stored as an observed value)."
            )
        if not has_reason:
            raise SilverRecordError(
                f"A non-observed metric (kind={kind!r}) requires a posture reason "
                "(reason_code or reason_detail)."
            )


def _validate_metric_observation_set(observation: Mapping[str, Any]) -> None:
    """Validate the packet-grain social metric observation-set envelope.

    The set is a physicalization optimization only: every nested metric retains
    the exact MetricObservation posture/value discipline.  Keeping this check in
    the Silver front door prevents a producer from gaining fewer files by
    weakening missing-vs-zero semantics or row identity.
    """
    platform = observation.get("platform")
    if not isinstance(platform, str) or not platform.strip():
        raise SilverRecordError("MetricObservationSet requires a non-empty platform.")
    policy_version = observation.get("policy_version")
    if not isinstance(policy_version, str) or not policy_version.strip():
        raise SilverRecordError("MetricObservationSet requires a non-empty policy_version.")
    fingerprint = observation.get("policy_fingerprint_sha256")
    if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
        raise SilverRecordError(
            "MetricObservationSet requires a lowercase 64-hex policy_fingerprint_sha256."
        )
    rows = observation.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SilverRecordError("MetricObservationSet requires a non-empty rows list.")
    row_count = observation.get("row_count")
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count != len(rows):
        raise SilverRecordError(
            "MetricObservationSet row_count must exactly equal the rows-list length."
        )
    subject = observation.get("subject")
    subject_ref = subject.get("ref") if isinstance(subject, Mapping) else None
    if (
        not isinstance(subject, Mapping)
        or subject.get("ref_type") != "entity_key"
        or not isinstance(subject_ref, Mapping)
        or not all(
            isinstance(subject_ref.get(key), str) and str(subject_ref.get(key)).strip()
            for key in ("namespace", "kind", "native_id")
        )
    ):
        raise SilverRecordError(
            "MetricObservationSet requires an account-level entity_key subject."
        )
    if subject_ref.get("namespace") != platform:
        raise SilverRecordError(
            "MetricObservationSet subject namespace must equal platform."
        )
    if not isinstance(observation.get("observation_set_kind"), str) or not str(
        observation.get("observation_set_kind")
    ).strip():
        raise SilverRecordError(
            "MetricObservationSet requires a non-empty observation_set_kind."
        )
    seen_subjects: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SilverRecordError(f"MetricObservationSet row {index} must be a mapping.")
        subject = row.get("subject")
        if not isinstance(subject, Mapping) or subject.get("ref_type") != "entity_key":
            raise SilverRecordError(
                f"MetricObservationSet row {index} requires an entity_key subject."
            )
        ref = subject.get("ref")
        if not isinstance(ref, Mapping):
            raise SilverRecordError(
                f"MetricObservationSet row {index} requires a subject.ref mapping."
            )
        identity = tuple(str(ref.get(key) or "").strip() for key in ("namespace", "kind", "native_id"))
        if any(not value for value in identity):
            raise SilverRecordError(
                f"MetricObservationSet row {index} requires namespace/kind/native_id identity."
            )
        if identity[0] != platform:
            raise SilverRecordError(
                f"MetricObservationSet row {index} subject namespace must equal platform."
            )
        if identity in seen_subjects:
            raise SilverRecordError(
                f"MetricObservationSet contains duplicate row subject {identity!r}."
            )
        seen_subjects.add(identity)
        metrics = row.get("metrics")
        if not isinstance(metrics, Mapping) or not metrics:
            raise SilverRecordError(
                f"MetricObservationSet row {index} requires a non-empty metrics mapping."
            )
        for metric_name, metric in metrics.items():
            if not isinstance(metric_name, str) or not metric_name.strip():
                raise SilverRecordError(
                    f"MetricObservationSet row {index} has a blank metric name."
                )
            if not isinstance(metric, Mapping):
                raise SilverRecordError(
                    f"MetricObservationSet row {index} metric {metric_name!r} must be a mapping."
                )
            if not isinstance(metric.get("unit"), str) or not str(metric.get("unit")).strip():
                raise SilverRecordError(
                    f"MetricObservationSet row {index} metric {metric_name!r} requires a unit."
                )
            if not isinstance(metric.get("source_field"), str) or not str(
                metric.get("source_field")
            ).strip():
                raise SilverRecordError(
                    f"MetricObservationSet row {index} metric {metric_name!r} requires a source_field."
                )
            _validate_metric_posture({**dict(metric), "metric_name": metric_name})


def _has_posture_reason(posture: Mapping[str, Any]) -> bool:
    """True if the posture carries a non-empty reason in either field. The Silver Vault
    contract requires 'a reason is present' for a non-observed metric without mandating
    which field carries it (the controlled signal is the posture ``kind``)."""
    for field in ("reason_code", "reason_detail"):
        value = posture.get(field)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _validate_text_observation(observation: Mapping[str, Any]) -> None:
    text_value = observation.get("text_value")
    text_ref = observation.get("text_ref")
    posture = observation.get("text_posture")
    if not isinstance(posture, Mapping) or posture.get("kind") != "observed":
        raise SilverRecordError("TextObservation currently requires text_posture.kind='observed'.")
    if not (isinstance(text_value, str) and text_value) and not (
        isinstance(text_ref, str) and text_ref.strip()
    ):
        raise SilverRecordError("Observed TextObservation requires text_value or text_ref.")
    if isinstance(text_value, str) and text_value:
        text_hash = observation.get("text_hash")
        expected = "sha256:" + hashlib.sha256(text_value.encode("utf-8")).hexdigest()
        if text_hash != expected:
            raise SilverRecordError("Inline TextObservation text_hash does not match text_value.")


def _validate_text_observation_set(observation: Mapping[str, Any]) -> None:
    _validate_entity_key_subject(observation.get("subject"), "TextObservationSet")
    _require_non_empty_string(
        observation.get("observation_set_kind"), "TextObservationSet observation_set_kind"
    )
    _require_non_empty_string(observation.get("policy_version"), "TextObservationSet policy_version")
    fingerprint = observation.get("policy_fingerprint_sha256")
    if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
        raise SilverRecordError(
            "TextObservationSet requires a lowercase 64-hex policy_fingerprint_sha256."
        )
    rows = observation.get("rows")
    if not isinstance(rows, list):
        raise SilverRecordError("TextObservationSet rows must be a list.")
    if observation.get("row_count") != len(rows):
        raise SilverRecordError("TextObservationSet row_count must equal rows-list length.")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SilverRecordError(f"TextObservationSet row {index} must be a mapping.")
        row_id = _require_non_empty_string(row.get("row_id"), f"TextObservationSet row {index} row_id")
        if row_id in seen:
            raise SilverRecordError(f"TextObservationSet contains duplicate row_id {row_id!r}.")
        seen.add(row_id)
        _validate_text_observation(row)


def _validate_entity_key_subject(value: Any, context: str) -> None:
    ref = value.get("ref") if isinstance(value, Mapping) else None
    if not isinstance(value, Mapping) or value.get("ref_type") != "entity_key" or not isinstance(ref, Mapping):
        raise SilverRecordError(f"{context} requires an entity_key subject.")
    for field in ("namespace", "kind", "native_id"):
        _require_non_empty_string(ref.get(field), f"{context} subject.ref.{field}")


def silver_content_hash(record: Mapping[str, Any]) -> str:
    canonical = dict(record)
    canonical.pop("content_hash", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_raw_packet_tombstone_record(
    *,
    retained_packet_id: str,
    tombstoned_packet_id: str,
    captured_at: str,
    reason: str,
) -> dict[str, Any]:
    """Build an append-only relationship that removes one raw packet from public reads."""
    retained = _require_non_empty_string(retained_packet_id, "retained_packet_id")
    tombstoned = _require_non_empty_string(
        tombstoned_packet_id, "tombstoned_packet_id"
    )
    recorded_at = _require_non_empty_string(captured_at, "captured_at")
    disposition_reason = _require_non_empty_string(reason, "reason")
    if retained == tombstoned:
        raise SilverRecordError("A raw packet cannot tombstone itself.")
    identity = "\0".join(
        (retained, tombstoned, recorded_at, disposition_reason)
    ).encode("utf-8")
    record_id = (
        f"raw_packet_tombstone_{hashlib.sha256(identity).hexdigest()[:24]}.json"
    )
    record: dict[str, Any] = {
        "record_id": record_id,
        "raw_anchor": retained,
        "lane_namespace": RAW_PACKET_TOMBSTONE_LANE,
        "producer_id": RAW_PACKET_TOMBSTONE_PRODUCER_ID,
        "schema_version": SILVER_VAULT_RECORD_SCHEMA_VERSION,
        "producer_schema_version": RAW_PACKET_TOMBSTONE_SCHEMA_VERSION,
        "record_kind": "relationship",
        "payload_kind": "RelationshipEdge",
        "producer_row_kind": "raw_packet_tombstone",
        "source_surface": RAW_PACKET_TOMBSTONE_SOURCE_SURFACE,
        "observed_at": None,
        "captured_at": recorded_at,
        "raw_refs": [
            {"ref_type": "raw_packet", "packet_id": retained},
            {"ref_type": "raw_packet", "packet_id": tombstoned},
        ],
        "derived_refs": [],
        "content_hash": "",
        "content_hash_basis": CONTENT_HASH_BASIS,
        "payload": {
            "relationship": {
                "edge_type": "tombstones_record",
                "from": {"ref_type": "record_id", "ref": retained},
                "to": {"ref_type": "record_id", "ref": tombstoned},
                "reason": disposition_reason,
                "recorded_at": recorded_at,
                "unavailability_scope": RAW_PACKET_TOMBSTONE_SCOPE,
                "raw_bytes_retained": True,
            }
        },
    }
    record["content_hash"] = f"sha256:{silver_content_hash(record)}"
    return record


def append_raw_packet_tombstone(
    data_root: "DataLakeRoot",
    *,
    retained_packet_id: str,
    tombstoned_packet_id: str,
    captured_at: str,
    reason: str,
) -> "Path":
    """Persist a validated public-read tombstone while retaining both raw packets."""
    record = build_raw_packet_tombstone_record(
        retained_packet_id=retained_packet_id,
        tombstoned_packet_id=tombstoned_packet_id,
        captured_at=captured_at,
        reason=reason,
    )
    return append_silver_record(
        data_root,
        raw_anchor=retained_packet_id,
        lane=RAW_PACKET_TOMBSTONE_LANE,
        record_id=record["record_id"],
        record=record,
    )


def append_silver_record(
    data_root: "DataLakeRoot",
    *,
    raw_anchor: str,
    lane: str,
    record_id: str,
    record: Mapping[str, Any],
) -> "Path":
    """Validate a Silver record against the envelope contract, then append it.

    The single sanctioned write path for Silver Vault records: a blurred record raises
    ``SilverRecordError`` BEFORE any bytes are written. The generic ``append_record``
    stays payload-blind; the Silver semantics live here, above it.
    """
    validate_silver_vault_record_for_write(record)
    _validate_write_binding(record, raw_anchor=raw_anchor, lane=lane, record_id=record_id)
    _validate_registered_silver_lane(lane)
    verify_silver_vault_record_sources(data_root, record)
    return data_root.append_record(
        subtree="derived",
        raw_anchor=raw_anchor,
        lane=lane,
        record_id=record_id,
        data=canonical_record_bytes(record),
    )


def append_silver_record_set(
    data_root: "DataLakeRoot",
    *,
    raw_anchor: str,
    record_id: str,
    records: Mapping[str, Mapping[str, Any]],
    completion_lane: str,
) -> dict[str, "Path"]:
    """Validate every Silver member before publishing a detectable record set."""
    if not records:
        raise SilverRecordError("A Silver record set requires at least one member.")
    members: dict[str, bytes] = {}
    for lane, record in records.items():
        validate_silver_vault_record_for_write(record)
        _validate_write_binding(record, raw_anchor=raw_anchor, lane=lane, record_id=record_id)
        _validate_registered_silver_lane(lane)
    _validate_registered_completion_lane(completion_lane)
    for lane, record in records.items():
        verify_silver_vault_record_sources(data_root, record)
        members[lane] = canonical_record_bytes(record)
    return data_root.append_record_set(
        subtree="derived",
        raw_anchor=raw_anchor,
        record_id=record_id,
        members=members,
        completion_lane=completion_lane,
    )


def _validate_write_binding(
    record: Mapping[str, Any], *, raw_anchor: str, lane: str, record_id: str
) -> None:
    expected = {
        "raw_anchor": raw_anchor,
        "lane_namespace": lane,
        "record_id": record_id,
    }
    for field, value in expected.items():
        if record.get(field) != value:
            raise SilverRecordError(
                f"Silver write binding mismatch: record {field}={record.get(field)!r}, "
                f"write target={value!r}."
            )


def _validate_registered_silver_lane(lane: str) -> None:
    from data_lake.lane_registry import LaneRole, role_of

    role = role_of(lane)
    if role is not LaneRole.SILVER_ENVELOPE:
        declared = role.value if role is not None else "undeclared"
        raise SilverRecordError(
            f"Silver write lane {lane!r} must be registered as silver_envelope; "
            f"got {declared!r}."
        )


def _validate_registered_completion_lane(lane: str) -> None:
    from data_lake.lane_registry import LaneRole, role_of

    role = role_of(lane)
    if role is not LaneRole.COMPLETION_MARKER:
        declared = role.value if role is not None else "undeclared"
        raise SilverRecordError(
            f"Silver completion lane {lane!r} must be registered as completion_marker; "
            f"got {declared!r}."
        )


__all__ = [
    "CLOSED_RECORD_KINDS",
    "CONTENT_HASH_BASIS",
    "METRIC_POSTURE_KINDS",
    "METRIC_OBSERVATION_SET_PAYLOAD_KIND",
    "TEXT_OBSERVATION_SET_PAYLOAD_KIND",
    "CURRENT_SOURCE_BACKED_AUTHORITY",
    "HISTORICAL_COMPATIBLE_AUTHORITY",
    "INVALID_SILVER_AUTHORITY",
    "UNRESOLVED_SILVER_AUTHORITY",
    "PHYSICALLY_SOURCE_BACKED_COMPLETE_STATUS",
    "RAW_PACKET_TOMBSTONE_LANE",
    "RAW_PACKET_TOMBSTONE_PRODUCER_ID",
    "RAW_PACKET_TOMBSTONE_SCHEMA_VERSION",
    "RAW_PACKET_TOMBSTONE_SOURCE_SURFACE",
    "RAW_PACKET_TOMBSTONE_SCOPE",
    "SilverSourceAuthority",
    "SILVER_VAULT_RECORD_SCHEMA_VERSION",
    "SilverRecordError",
    "append_raw_packet_tombstone",
    "append_silver_record",
    "append_silver_record_set",
    "build_raw_packet_tombstone_record",
    "classify_silver_vault_record_sources",
    "silver_content_hash",
    "silver_raw_refs_bound_to_own_anchor",
    "validate_silver_vault_record",
    "validate_silver_vault_record_for_write",
    "validate_silver_vault_record_stable",
    "verify_silver_vault_record_sources",
]
