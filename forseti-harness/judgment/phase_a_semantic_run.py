"""Reusable, fail-closed control plane for a full-corpus Phase A semantic run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

import yaml

from harness_utils import hash_file
from judgment.semantic_evidence_integration import (
    SemanticIntegrationError,
    materialize_source_v3,
    validate_batch_responses,
    validate_reconciliation_stage,
)
from source_capture.reddit_consolidation import build_thread_content_record


RUN_SPEC_VERSION = "phase_a_semantic_integration_run_v1"
AUDIT_VERSION = "phase_a_semantic_source_audit_v1"
RUN_RECEIPT_VERSION = "phase_a_semantic_materialization_receipt_v1"
CORPUS_CENSUS_VERSION = "phase_a_customer_corpus_census_v1"
RETAILER_SOURCE_MANIFEST_VERSION = "retailer_review_source_manifest_v1"
GOOGLE_SERP_QUEUE_STATE_VERSION = "google_serp_queue_state_v1"
ROUTE_DISPOSITIONS = {
    "semantic_source",
    "structured_reference",
    "discovery_only",
    "control_only",
    "duplicate_of",
    "blocked",
}
# A duplicate route reuses evidence another route owns, so only these
# dispositions can be duplicated: an evidence route that supplies it, or a
# blocked route that visibly still owes it.
EVIDENCE_OWNING_DISPOSITIONS = {
    "semantic_source",
    "structured_reference",
    "blocked",
}
# Reddit target states that mean leaves were captured and therefore belong in
# the customer-corpus denominator.
CAPTURED_TERMINAL_STATES = {"used", "captured_excluded"}
_YAML_FENCE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_TEXT_ARTIFACT_SUFFIXES = {".json", ".md", ".yaml", ".yml"}
_REDDIT_PLACEHOLDERS = {"[deleted]", "[removed]"}
_REVOLVE_RATING_ONLY_PLACEHOLDER = (
    "This REVOLVE shopper left a rating without a review."
)


def _canonical_hash(value: Any) -> str:
    body = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _resolve(repo_root: Path, locator: str) -> Path:
    raw = Path(locator)
    if raw.is_absolute():
        return raw.resolve(strict=True)
    resolved = (repo_root / raw).resolve(strict=True)
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise SemanticIntegrationError(
            f"repository-relative locator escapes repo root: {locator}"
        ) from exc
    return resolved


def _artifact_hash(path: Path) -> str:
    if path.suffix.lower() not in _TEXT_ARTIFACT_SUFFIXES:
        return hash_file(path)
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _verified_path(
    binding: Mapping[str, Any], *, repo_root: Path, label: str
) -> Path:
    locator = binding.get("locator")
    expected = binding.get("sha256")
    if not _nonempty(locator) or not _nonempty(expected):
        raise SemanticIntegrationError(f"{label} lacks locator or sha256")
    try:
        path = _resolve(repo_root, locator)
    except OSError as exc:
        raise SemanticIntegrationError(f"{label} is unavailable: {exc}") from exc
    observed = _artifact_hash(path)
    if observed != expected:
        raise SemanticIntegrationError(
            f"{label} hash mismatch: expected {expected}, observed {observed}"
        )
    return path


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticIntegrationError(f"{label} could not be loaded: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticIntegrationError(f"{label} must be a JSON object")
    return value


def _canonical_json_file_hash(path: Path) -> str:
    value = _load_json_object(path, label=str(path))
    body = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _resolve_ledger_locator(ledger_path: Path, locator: str) -> Path:
    raw = Path(locator)
    if raw.is_absolute():
        return raw.resolve(strict=True)
    for parent in ledger_path.resolve().parents:
        candidate = (parent / raw).resolve()
        if candidate.is_file():
            return candidate
    raise SemanticIntegrationError(f"ledger artifact locator is unavailable: {locator}")


def _reddit_record_from_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = _load_json_object(manifest_path, label="Reddit packet manifest")
    preserved = manifest.get("preserved_files")
    if not isinstance(preserved, list):
        raise SemanticIntegrationError(f"Reddit manifest lacks preserved files: {manifest_path}")
    content_candidates: list[Path] = []
    html_candidates: list[Path] = []
    for row in preserved:
        if not isinstance(row, Mapping) or not _nonempty(row.get("relative_packet_path")):
            continue
        relative = row["relative_packet_path"]
        path = (manifest_path.parent / relative).resolve()
        if not path.is_file():
            raise SemanticIntegrationError(f"Reddit preserved file is missing: {path}")
        expected = row.get("sha256")
        if _nonempty(expected) and hash_file(path) != expected:
            raise SemanticIntegrationError(f"Reddit preserved file hash mismatch: {path}")
        lowered = relative.lower()
        is_source = lowered.endswith("content_record.json") or lowered.endswith(
            ("http_response_body.bin", ".html", ".htm")
        )
        # The file the census actually reads sets the captured-leaf denominator.
        # An unpinned preserved source would let substituted bytes change that
        # denominator without failing any hash check.
        if is_source and not _nonempty(expected):
            raise SemanticIntegrationError(
                f"Reddit preserved source file lacks a pinned hash: {path}"
            )
        if lowered.endswith("content_record.json"):
            content_candidates.append(path)
        elif is_source:
            html_candidates.append(path)
    if len(content_candidates) > 1 or len(html_candidates) > 1:
        raise SemanticIntegrationError(
            f"Reddit packet has ambiguous preserved source candidates: {manifest_path}"
        )
    if content_candidates:
        return _load_json_object(content_candidates[0], label="Reddit content record")
    if not html_candidates:
        raise SemanticIntegrationError(
            f"Reddit packet has neither content record nor HTML body: {manifest_path}"
        )
    source_locator = manifest.get("source_locator", {})
    source_url = source_locator.get("value") if isinstance(source_locator, Mapping) else None
    if not _nonempty(source_url):
        raise SemanticIntegrationError(f"Reddit manifest lacks source locator: {manifest_path}")
    html = html_candidates[0].read_bytes().decode("utf-8", errors="replace")
    try:
        return build_thread_content_record(html_text=html, source_url=source_url)
    except ValueError as exc:
        raise SemanticIntegrationError(
            f"Reddit HTML could not be projected for {manifest_path}: {exc}"
        ) from exc


def load_google_serp_rows(path: Path) -> list[Mapping[str, Any]]:
    """Load one Google SERP v3 record or its hash-pinned packet manifest."""
    value = _load_json_object(path, label="SERP artifact")
    if value.get("content_record_version") == "google_serp_content_v3":
        record = value
    else:
        preserved = value.get("preserved_files")
        if not isinstance(preserved, list):
            raise SemanticIntegrationError(
                "SERP artifact is neither a v3 record nor packet manifest"
            )
        candidates: list[Path] = []
        for row in preserved:
            if not isinstance(row, Mapping):
                continue
            relative = row.get("relative_packet_path")
            if not isinstance(relative, str) or not relative.lower().endswith(
                "content_record.json"
            ):
                continue
            candidate = (path.parent / relative).resolve(strict=True)
            try:
                candidate.relative_to(path.parent.resolve())
            except ValueError as exc:
                raise SemanticIntegrationError(
                    "SERP content record escapes its packet"
                ) from exc
            if row.get("sha256") != hash_file(candidate):
                raise SemanticIntegrationError("SERP content record hash mismatch")
            candidates.append(candidate)
        if len(candidates) != 1:
            raise SemanticIntegrationError(
                "SERP packet must own exactly one v3 content record"
            )
        record = _load_json_object(candidates[0], label="SERP content record")
        if record.get("content_record_version") != "google_serp_content_v3":
            raise SemanticIntegrationError(
                "SERP packet content record is not google_serp_content_v3"
            )
    rows = record.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SemanticIntegrationError("Google SERP content record has invalid rows")
    return rows


def google_serp_queue_job_packets(queue_state_path: Path) -> dict[str, list[Path]]:
    """Return every successful packet preserved in one SERP queue receipt."""
    state = _load_json_object(queue_state_path, label="Google SERP queue state")
    if state.get("schema_version") != GOOGLE_SERP_QUEUE_STATE_VERSION:
        raise SemanticIntegrationError("Google SERP queue state has wrong version")
    jobs = state.get("jobs")
    completed = state.get("completed_job_ids")
    failed = state.get("failed_job_ids")
    attempts = state.get("attempt_history")
    if (
        not isinstance(jobs, list)
        or not jobs
        or not isinstance(completed, list)
        or not isinstance(failed, list)
        or not isinstance(attempts, list)
    ):
        raise SemanticIntegrationError("Google SERP queue state has invalid accounting")
    job_ids: list[str] = []
    for row in jobs:
        if not isinstance(row, Mapping) or not _nonempty(row.get("job_id")):
            raise SemanticIntegrationError("Google SERP queue state has an invalid job")
        job_ids.append(row["job_id"])
    if len(job_ids) != len(set(job_ids)):
        raise SemanticIntegrationError("Google SERP queue state has duplicate jobs")
    if (
        any(not _nonempty(job_id) for job_id in completed)
        or len(completed) != len(set(completed))
        or not set(completed).issubset(job_ids)
        or any(not _nonempty(job_id) or job_id not in job_ids for job_id in failed)
        or set(completed).intersection(failed)
    ):
        raise SemanticIntegrationError(
            "Google SERP queue state has inconsistent terminal job accounting"
        )
    packet_paths: dict[str, list[Path]] = {job_id: [] for job_id in completed}
    for attempt in attempts:
        if not isinstance(attempt, Mapping):
            raise SemanticIntegrationError("Google SERP queue state has an invalid attempt")
        if attempt.get("outcome") != "success":
            continue
        job_id = attempt.get("job_id")
        locator = attempt.get("packet_locator")
        if job_id not in packet_paths or not _nonempty(locator):
            raise SemanticIntegrationError(
                "successful Google SERP attempt lacks a known job or packet locator"
            )
        raw = Path(locator)
        packet = raw if raw.is_absolute() else queue_state_path.parent / raw
        packet = packet.resolve(strict=True)
        manifest = (packet / "manifest.json").resolve(strict=True) if packet.is_dir() else packet
        # A successful packet is source-bearing only when its manifest remains
        # readable and owns exactly one pinned Google SERP v3 record.
        load_google_serp_rows(manifest)
        if manifest in packet_paths[job_id]:
            raise SemanticIntegrationError(
                f"Google SERP queue state repeats a successful packet: {job_id}"
            )
        packet_paths[job_id].append(manifest)
    missing = sorted(job_id for job_id, paths in packet_paths.items() if not paths)
    if missing:
        raise SemanticIntegrationError(
            f"completed Google SERP jobs lack successful packets: {missing}"
        )
    return {job_id: sorted(paths, key=str) for job_id, paths in sorted(packet_paths.items())}


def derive_serp_job_packet_inventory(
    *,
    search_surfaces: Sequence[Mapping[str, Any]],
    packet_artifact_paths: Mapping[str, Path],
    queue_state_bindings: Sequence[tuple[str, str, Path, Mapping[str, str]]],
) -> list[dict[str, Any]]:
    """Derive and exactly reconcile the producer-owned Phase 1/2 packet set."""
    surface_index: dict[tuple[str, str], Mapping[str, Any]] = {}
    for surface in search_surfaces:
        if not isinstance(surface, Mapping):
            raise SemanticIntegrationError("SERP source surface is invalid")
        phase = surface.get("phase")
        job_id = surface.get("job_id")
        artifact_ids = surface.get("artifact_ids")
        if (
            phase not in {"serp_phase1", "serp_phase2", "phase_a_adjustment"}
            or not _nonempty(job_id)
            or not isinstance(artifact_ids, list)
            or not artifact_ids
            or any(not _nonempty(artifact_id) for artifact_id in artifact_ids)
            or len(artifact_ids) != len(set(artifact_ids))
        ):
            raise SemanticIntegrationError("SERP source surface is incomplete")
        key = (phase, job_id)
        if key in surface_index:
            raise SemanticIntegrationError("SERP source surface repeats a phase job")
        surface_index[key] = surface

    inventory: list[dict[str, Any]] = []
    producer_keys: set[tuple[str, str]] = set()
    receipt_ids: set[str] = set()
    packet_owners: dict[Path, str] = {}
    for phase, receipt_id, state_path, job_id_aliases in queue_state_bindings:
        if phase not in {"serp_phase1", "serp_phase2"} or not _nonempty(receipt_id):
            raise SemanticIntegrationError("SERP producer receipt has invalid phase or id")
        if receipt_id in receipt_ids:
            raise SemanticIntegrationError("SERP producer receipt id is duplicated")
        receipt_ids.add(receipt_id)
        produced = google_serp_queue_job_packets(state_path)
        if set(job_id_aliases) - set(produced):
            raise SemanticIntegrationError(
                "SERP producer recovery aliases name jobs without successful packets"
            )
        resolved_job_ids = [job_id_aliases.get(job_id, job_id) for job_id in produced]
        if len(resolved_job_ids) != len(set(resolved_job_ids)):
            raise SemanticIntegrationError("SERP producer recovery aliases are not one-to-one")
        for producer_job_id, produced_paths in produced.items():
            job_id = job_id_aliases.get(producer_job_id, producer_job_id)
            key = (phase, job_id)
            if key in producer_keys:
                raise SemanticIntegrationError("SERP producer receipts overlap one phase job")
            producer_keys.add(key)
            surface = surface_index.get(key)
            if surface is None:
                raise SemanticIntegrationError(
                    f"successful SERP producer job lacks a source surface: {phase}:{job_id}"
                )
            artifact_ids = list(surface["artifact_ids"])
            try:
                declared_paths = [packet_artifact_paths[artifact_id].resolve() for artifact_id in artifact_ids]
            except KeyError as exc:
                raise SemanticIntegrationError(
                    f"SERP source surface cites an unknown packet artifact: {exc.args[0]}"
                ) from exc
            if set(declared_paths) != set(produced_paths) or len(declared_paths) != len(
                produced_paths
            ):
                raise SemanticIntegrationError(
                    f"SERP source surface does not exactly match producer packets: {phase}:{job_id}"
                )
            # One producer packet file carries one artifact identity. Two ids
            # over one file would enumerate that packet's rows twice and read
            # as two independent sources rather than one.
            for artifact_id, packet_path in zip(artifact_ids, declared_paths):
                owner = packet_owners.setdefault(packet_path, artifact_id)
                if owner != artifact_id:
                    raise SemanticIntegrationError(
                        "SERP producer packet is declared under two artifact "
                        f"ids: {owner} and {artifact_id}"
                    )
            inventory.append(
                {
                    "phase": phase,
                    "job_id": job_id,
                    "producer_job_id": producer_job_id,
                    "producer_queue_state_artifact_id": receipt_id,
                    "artifact_ids": artifact_ids,
                    "successful_packet_count": len(artifact_ids),
                }
            )
    expected_keys = {
        key for key in surface_index if key[0] in {"serp_phase1", "serp_phase2"}
    }
    if producer_keys != expected_keys:
        missing = sorted(expected_keys - producer_keys)
        extra = sorted(producer_keys - expected_keys)
        raise SemanticIntegrationError(
            f"SERP producer receipts and Phase 1/2 surfaces differ; missing={missing}, extra={extra}"
        )
    return sorted(inventory, key=lambda row: (row["phase"], row["job_id"]))


def eligible_serp_source_rows(
    artifact_id: str, rows: Sequence[Mapping[str, Any]]
) -> dict[tuple[str, str, int], Mapping[str, Any]]:
    """Enumerate source-bearing rows while excluding Google-only prompts."""
    eligible: dict[tuple[str, str, int], Mapping[str, Any]] = {}
    for row in rows:
        module = row.get("module_type")
        order = row.get("order_in_module")
        if module in {"people_also_ask", "related_search"}:
            continue
        source_bearing = any(
            isinstance(row.get(field), str) and bool(row[field].strip())
            for field in ("canonical_url", "displayed_domain", "displayed_source")
        )
        if not source_bearing:
            continue
        if (
            not isinstance(module, str)
            or not module
            or not isinstance(order, int)
            or isinstance(order, bool)
        ):
            raise SemanticIntegrationError(
                "source-bearing SERP row lacks stable module identity"
            )
        key = (artifact_id, module, order)
        if key in eligible:
            raise SemanticIntegrationError("duplicate source-bearing SERP row identity")
        eligible[key] = row
    return eligible


def prepare_serp_source_frontier_inventory(
    *, surface_spec_path: Path
) -> dict[str, Any]:
    """Render the complete bounded SERP row inventory for agent semantic review."""
    spec = _load_json_object(surface_spec_path, label="SERP surface spec")
    if spec.get("schema_version") != "phase_a_serp_source_surface_spec_v1":
        raise SemanticIntegrationError("SERP surface spec has wrong version")
    surfaces = spec.get("search_surfaces")
    artifacts = spec.get("source_artifacts")
    producer_receipts = spec.get("producer_queue_states")
    declared_job_packets = spec.get("producer_job_packet_inventory")
    if (
        not isinstance(surfaces, list)
        or not isinstance(artifacts, list)
        or not isinstance(producer_receipts, list)
        or not isinstance(declared_job_packets, list)
    ):
        raise SemanticIntegrationError("SERP surface spec lacks surfaces or artifacts")
    artifact_index: dict[str, Mapping[str, Any]] = {}
    artifact_ids_by_path: dict[Path, str] = {}
    row_inventory: list[dict[str, Any]] = []
    for row in artifacts:
        if not isinstance(row, Mapping) or not _nonempty(row.get("artifact_id")):
            raise SemanticIntegrationError("SERP surface spec has invalid artifact")
        artifact_id = row["artifact_id"]
        if artifact_id in artifact_index:
            raise SemanticIntegrationError("SERP surface spec has duplicate artifact id")
        path = Path(str(row.get("locator", ""))).resolve(strict=True)
        owner = artifact_ids_by_path.setdefault(path, artifact_id)
        if owner != artifact_id:
            raise SemanticIntegrationError(
                "SERP packet file is declared under two artifact ids: "
                f"{owner} and {artifact_id}"
            )
        if row.get("raw_sha256") != hash_file(path):
            raise SemanticIntegrationError(f"SERP surface artifact hash mismatch: {artifact_id}")
        artifact_index[artifact_id] = row
        eligible = eligible_serp_source_rows(
            artifact_id, load_google_serp_rows(path)
        )
        for (source_id, module, order), source_row in sorted(eligible.items()):
            row_inventory.append(
                {
                    "artifact_id": source_id,
                    "module_type": module,
                    "order_in_module": order,
                    "title": source_row.get("title"),
                    "snippet": source_row.get("snippet"),
                    "displayed_source": source_row.get("displayed_source"),
                    "displayed_domain": source_row.get("displayed_domain"),
                    "canonical_url": source_row.get("canonical_url"),
                    "canonical_url_absent_reason": source_row.get(
                        "canonical_url_absent_reason"
                    ),
                }
            )
    cited_ids = {
        artifact_id
        for surface in surfaces
        if isinstance(surface, Mapping)
        for artifact_id in surface.get("artifact_ids", [])
        if isinstance(artifact_id, str)
    }
    if cited_ids != set(artifact_index):
        raise SemanticIntegrationError(
            "SERP surfaces and source artifacts do not have exact coverage"
        )
    queue_state_bindings: list[tuple[str, str, Path, Mapping[str, str]]] = []
    for row in producer_receipts:
        if (
            not isinstance(row, Mapping)
            or not _nonempty(row.get("phase"))
            or not _nonempty(row.get("artifact_id"))
            or not _nonempty(row.get("locator"))
        ):
            raise SemanticIntegrationError("SERP surface spec has an invalid producer receipt")
        path = Path(row["locator"]).resolve(strict=True)
        if row.get("raw_sha256") != hash_file(path):
            raise SemanticIntegrationError(
                f"SERP producer receipt hash mismatch: {row['artifact_id']}"
            )
        aliases = row.get("job_id_aliases", {})
        if not isinstance(aliases, Mapping) or any(
            not _nonempty(key) or not _nonempty(value) for key, value in aliases.items()
        ):
            raise SemanticIntegrationError("SERP producer receipt has invalid job aliases")
        queue_state_bindings.append((row["phase"], row["artifact_id"], path, aliases))
    observed_job_packets = derive_serp_job_packet_inventory(
        search_surfaces=surfaces,
        packet_artifact_paths={
            artifact_id: Path(row["locator"]).resolve()
            for artifact_id, row in artifact_index.items()
        },
        queue_state_bindings=queue_state_bindings,
    )
    if observed_job_packets != declared_job_packets:
        raise SemanticIntegrationError("SERP producer job-packet inventory is stale")
    if spec.get("producer_job_packet_inventory_sha256") != _canonical_hash(
        declared_job_packets
    ):
        raise SemanticIntegrationError("SERP producer job-packet inventory hash is stale")
    result = {
        "schema_version": "phase_a_serp_source_inventory_v1",
        "surface_spec_raw_sha256": hash_file(surface_spec_path),
        "search_surfaces": surfaces,
        "producer_queue_states": producer_receipts,
        "producer_job_packet_inventory": declared_job_packets,
        "producer_job_packet_inventory_sha256": spec.get(
            "producer_job_packet_inventory_sha256"
        ),
        "source_artifact_count": len(artifact_index),
        "eligible_row_count": len(row_inventory),
        "row_inventory": row_inventory,
        "review_instruction": (
            "A capable agent reads every row by meaning and supplies exactly one "
            "routed, duplicate, or excluded classification with a reason."
        ),
        "model_api_calls": 0,
    }
    result["inventory_sha256"] = _canonical_hash(result)
    return result


def build_serp_source_surface_spec(*, surface_map_path: Path) -> dict[str, Any]:
    """Derive a producer-backed, hash-pinned bounded job-to-packet map."""
    source_map = _load_json_object(surface_map_path, label="SERP surface map")
    if source_map.get("schema_version") != "phase_a_serp_source_surface_map_v1":
        raise SemanticIntegrationError("SERP surface map has wrong version")
    surfaces = source_map.get("search_surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise SemanticIntegrationError("SERP surface map lacks search surfaces")
    artifacts: dict[str, dict[str, Any]] = {}
    artifact_paths: dict[str, Path] = {}
    artifact_ids_by_path: dict[Path, str] = {}
    rendered_surfaces: list[dict[str, Any]] = []
    for surface in surfaces:
        if (
            not isinstance(surface, Mapping)
            or not _nonempty(surface.get("phase"))
            or not _nonempty(surface.get("job_id"))
            or not isinstance(surface.get("artifacts"), list)
            or not surface["artifacts"]
        ):
            raise SemanticIntegrationError("SERP surface map has invalid surface")
        artifact_ids: list[str] = []
        for row in surface["artifacts"]:
            if (
                not isinstance(row, Mapping)
                or not _nonempty(row.get("artifact_id"))
                or not _nonempty(row.get("locator"))
            ):
                raise SemanticIntegrationError("SERP surface map has invalid artifact")
            artifact_id = row["artifact_id"]
            path = Path(row["locator"]).resolve(strict=True)
            owner = artifact_ids_by_path.setdefault(path, artifact_id)
            if owner != artifact_id:
                raise SemanticIntegrationError(
                    "SERP packet file is declared under two artifact ids: "
                    f"{owner} and {artifact_id}"
                )
            rendered = {
                "artifact_id": artifact_id,
                "locator": str(path),
                "raw_sha256": hash_file(path),
                "hash_convention": "sha256_raw_bytes",
            }
            if artifact_id in artifacts and artifacts[artifact_id] != rendered:
                raise SemanticIntegrationError(
                    f"SERP artifact id maps to conflicting files: {artifact_id}"
                )
            artifacts[artifact_id] = rendered
            artifact_paths[artifact_id] = path
            artifact_ids.append(artifact_id)
        rendered_surfaces.append(
            {
                "phase": surface["phase"],
                "job_id": surface["job_id"],
                "artifact_ids": artifact_ids,
            }
        )
    producer_rows = source_map.get("producer_queue_states")
    if not isinstance(producer_rows, list) or not producer_rows:
        raise SemanticIntegrationError("SERP surface map lacks producer queue states")
    producer_receipts: list[dict[str, Any]] = []
    queue_state_bindings: list[tuple[str, str, Path, Mapping[str, str]]] = []
    producer_ids: set[str] = set()
    for row in producer_rows:
        if (
            not isinstance(row, Mapping)
            or row.get("phase") not in {"serp_phase1", "serp_phase2"}
            or not _nonempty(row.get("artifact_id"))
            or not _nonempty(row.get("locator"))
        ):
            raise SemanticIntegrationError("SERP surface map has an invalid producer receipt")
        artifact_id = row["artifact_id"]
        if artifact_id in producer_ids or artifact_id in artifacts:
            raise SemanticIntegrationError("SERP producer receipt artifact id is duplicated")
        producer_ids.add(artifact_id)
        path = Path(row["locator"]).resolve(strict=True)
        aliases = row.get("job_id_aliases", {})
        if not isinstance(aliases, Mapping) or any(
            not _nonempty(key) or not _nonempty(value) for key, value in aliases.items()
        ):
            raise SemanticIntegrationError("SERP producer receipt has invalid job aliases")
        producer_receipts.append(
            {
                "phase": row["phase"],
                "artifact_id": artifact_id,
                "locator": str(path),
                "raw_sha256": hash_file(path),
                "hash_convention": "sha256_raw_bytes",
                "job_id_aliases": dict(sorted(aliases.items())),
            }
        )
        queue_state_bindings.append((row["phase"], artifact_id, path, aliases))
    producer_inventory = derive_serp_job_packet_inventory(
        search_surfaces=rendered_surfaces,
        packet_artifact_paths=artifact_paths,
        queue_state_bindings=queue_state_bindings,
    )
    result = {
        "schema_version": "phase_a_serp_source_surface_spec_v1",
        "surface_map_raw_sha256": hash_file(surface_map_path),
        "search_surfaces": rendered_surfaces,
        "source_artifacts": sorted(artifacts.values(), key=lambda row: row["artifact_id"]),
        "producer_queue_states": sorted(
            producer_receipts, key=lambda row: (row["phase"], row["artifact_id"])
        ),
        "producer_job_packet_inventory": producer_inventory,
        "producer_job_packet_inventory_sha256": _canonical_hash(producer_inventory),
        "model_api_calls": 0,
    }
    result["surface_spec_sha256"] = _canonical_hash(result)
    return result


def materialize_serp_source_frontier_review(
    *, inventory_path: Path, review_path: Path
) -> dict[str, Any]:
    """Apply an agent-authored semantic review and mechanically deduplicate routes."""
    inventory = _load_json_object(inventory_path, label="SERP source inventory")
    review = _load_json_object(review_path, label="SERP source semantic review")
    if inventory.get("schema_version") != "phase_a_serp_source_inventory_v1":
        raise SemanticIntegrationError("SERP source inventory has wrong version")
    if review.get("schema_version") != "phase_a_serp_source_review_v1":
        raise SemanticIntegrationError("SERP source review has wrong version")
    if review.get("inventory_sha256") != inventory.get("inventory_sha256"):
        raise SemanticIntegrationError("SERP source review has stale inventory hash")
    if (
        review.get("review_method") != "agent_semantic_judgment"
        or review.get("model_api_calls") != 0
    ):
        raise SemanticIntegrationError("SERP source review lacks no-API semantic posture")
    # A default would turn one agent judgment into an arbitrary bulk route.
    # Every external-source row must instead carry its own reviewed decision.
    if "default_semantic_decision" in review:
        raise SemanticIntegrationError("SERP source review cannot use a default semantic decision")
    decisions = review.get("row_decisions")
    if not isinstance(decisions, list):
        raise SemanticIntegrationError("SERP source review decisions must be a list")
    decision_index: dict[tuple[str, str, int], Mapping[str, Any]] = {}
    for row in decisions:
        if not isinstance(row, Mapping):
            raise SemanticIntegrationError("SERP source review has invalid decision")
        artifact_id = row.get("artifact_id")
        module_type = row.get("module_type")
        order = row.get("order_in_module")
        if (
            not _nonempty(artifact_id)
            or not _nonempty(module_type)
            or not isinstance(order, int)
            or isinstance(order, bool)
        ):
            raise SemanticIntegrationError("SERP source review decision has invalid row identity")
        key = (artifact_id, module_type, order)
        if key in decision_index:
            raise SemanticIntegrationError("SERP source review has duplicate decision")
        if row.get("disposition") not in {"routed", "excluded"} or not _nonempty(
            row.get("reason")
        ):
            raise SemanticIntegrationError("SERP source review decision is incomplete")
        decision_index[key] = row
    rows = inventory.get("row_inventory")
    if not isinstance(rows, list):
        raise SemanticIntegrationError("SERP source inventory lacks rows")
    row_keys = {
        (row.get("artifact_id"), row.get("module_type"), row.get("order_in_module"))
        for row in rows
        if isinstance(row, Mapping)
    }
    if set(decision_index) != row_keys:
        raise SemanticIntegrationError("SERP source review decisions do not exactly cover inventory rows")
    artifact_jobs: dict[str, str] = {}
    for surface in inventory.get("search_surfaces", []):
        if isinstance(surface, Mapping) and _nonempty(surface.get("job_id")):
            for artifact_id in surface.get("artifact_ids", []):
                if isinstance(artifact_id, str):
                    artifact_jobs.setdefault(artifact_id, surface["job_id"])
    owner_by_locator: dict[str, tuple[str, str, int]] = {}
    classifications: list[dict[str, Any]] = []
    targets: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise SemanticIntegrationError("SERP source inventory has invalid row")
        key = (row["artifact_id"], row["module_type"], row["order_in_module"])
        decision = decision_index[key]
        reason = decision["reason"]
        classification = {
            "artifact_id": key[0],
            "module_type": key[1],
            "order_in_module": key[2],
            "reason": reason,
        }
        if decision["disposition"] == "excluded":
            classification["disposition"] = "excluded"
            classifications.append(classification)
            continue
        locator = row.get("canonical_url")
        if not _nonempty(locator):
            locator = f"serp-locator-recovery:{key[0]}:{key[1]}:{key[2]}"
        owner = owner_by_locator.get(locator)
        if owner is not None:
            classification.update(
                {
                    "disposition": "duplicate",
                    "duplicate_of": {
                        "artifact_id": owner[0],
                        "module_type": owner[1],
                        "order_in_module": owner[2],
                    },
                }
            )
        else:
            owner_by_locator[locator] = key
            target_id = "serp_recovery_" + hashlib.sha256(
                locator.encode("utf-8")
            ).hexdigest()[:20]
            classification.update(
                {"disposition": "routed", "target_id": target_id}
            )
            targets[target_id] = {
                "target_id": target_id,
                "discovered_by_job_id": artifact_jobs.get(key[0]),
                "locator": locator,
                "terminal_state": "blocked",
                "reason": "Native capture or bounded locator recovery is still owed.",
                "source_serp_row": {
                    "artifact_id": key[0],
                    "module_type": key[1],
                    "order_in_module": key[2],
                },
            }
        classifications.append(classification)
    result = {
        "schema_version": "phase_a_serp_source_frontier_review_result_v1",
        "inventory_sha256": inventory["inventory_sha256"],
        "frontier": {
            "schema_version": "phase_a_serp_source_frontier_v1",
            "status": "complete",
            "review_method": "agent_semantic_judgment",
            "model_api_calls": 0,
            "search_surfaces": inventory["search_surfaces"],
            "producer_queue_states": inventory["producer_queue_states"],
            "producer_job_packet_inventory": inventory[
                "producer_job_packet_inventory"
            ],
            "producer_job_packet_inventory_sha256": inventory[
                "producer_job_packet_inventory_sha256"
            ],
            "row_classifications": classifications,
        },
        "locator_recovery_targets": sorted(
            targets.values(), key=lambda row: row["target_id"]
        ),
        "classification_counts": {
            disposition: sum(
                row["disposition"] == disposition for row in classifications
            )
            for disposition in ("routed", "duplicate", "excluded")
        },
        "model_api_calls": 0,
    }
    result["result_sha256"] = _canonical_hash(result)
    return result


def _retailer_review_ids(source: Mapping[str, Any]) -> tuple[str, set[str]]:
    """Return source-native review ids for the three admitted retailer formats."""
    schema = source.get("schema_version")
    if schema == "retail_pdp_amazon_aggregate_content_v1":
        rows = source.get("rows")
        if not isinstance(rows, list):
            raise SemanticIntegrationError("Amazon retailer source lacks rows")
        ids = {
            str(fields["review_id"])
            for row in rows
            if isinstance(row, Mapping)
            and row.get("row_kind") == "retail_review_row"
            and isinstance((fields := row.get("source_visible_fields")), Mapping)
            and fields.get("review_id") is not None
        }
        return "amazon_aggregate_v1", ids
    if schema == "revolve_review_corpus_recent_v1":
        ids = source.get("captured_review_ids")
        if not isinstance(ids, list) or any(value is None for value in ids):
            raise SemanticIntegrationError("Revolve retailer source lacks captured review ids")
        return "revolve_recent_v1", {str(value) for value in ids}
    results = source.get("Results")
    if isinstance(results, list):
        ids = {
            str(row["Id"])
            for row in results
            if isinstance(row, Mapping) and row.get("Id") is not None
        }
        return "bazaarvoice_results_v1", ids
    raise SemanticIntegrationError("retailer source uses an unsupported review structure")


def build_retailer_source_manifest(*, retailer_coding_path: Path) -> dict[str, Any]:
    """Pin every retailer file and the structurally located review ids it supplies."""
    retailer = _load_json_object(retailer_coding_path, label="retailer axis coding")
    rows = retailer.get("rows")
    if not isinstance(rows, list):
        raise SemanticIntegrationError("retailer coding lacks rows")
    sources: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not _nonempty(row.get("source_row_ref")):
            raise SemanticIntegrationError("retailer coding has invalid review row")
        review_id = str(row.get("review_id", ""))
        locator, separator, anchor = row["source_row_ref"].partition("#review:")
        if separator != "#review:" or not review_id or anchor != review_id:
            raise SemanticIntegrationError(
                f"invalid retailer source row ref: {row['source_row_ref']}"
            )
        path = Path(locator).resolve(strict=True)
        key = str(path)
        source_row = sources.get(key)
        if source_row is None:
            source = _load_json_object(path, label=f"retailer source {path}")
            parser_family, native_ids = _retailer_review_ids(source)
            source_row = {
                "locator": key,
                "raw_sha256": hash_file(path),
                "hash_convention": "sha256_raw_bytes",
                "parser_family": parser_family,
                "native_review_ids": native_ids,
                "referenced_review_ids": set(),
            }
            sources[key] = source_row
        if review_id not in source_row["native_review_ids"]:
            raise SemanticIntegrationError(
                f"retailer review {review_id} is absent from its source-native review rows"
            )
        source_row["referenced_review_ids"].add(review_id)
    manifest_sources = []
    for row in sources.values():
        native_ids = sorted(row.pop("native_review_ids"))
        referenced_ids = sorted(row.pop("referenced_review_ids"))
        manifest_sources.append(
            {
                **row,
                "native_review_id_count": len(native_ids),
                "native_review_ids_sha256": _canonical_hash(native_ids),
                "referenced_review_ids": referenced_ids,
            }
        )
    result = {
        "schema_version": RETAILER_SOURCE_MANIFEST_VERSION,
        "retailer_coding_raw_sha256": hash_file(retailer_coding_path),
        "hash_convention": "sha256_raw_bytes",
        "sources": sorted(manifest_sources, key=lambda row: row["locator"]),
    }
    result["source_set_sha256"] = _canonical_hash(result["sources"])
    result["manifest_sha256"] = _canonical_hash(result)
    return result


def _verify_retailer_source_manifest(
    *, retailer_coding_path: Path, manifest_path: Path
) -> tuple[dict[str, Mapping[str, Any]], dict[str, set[str]]]:
    manifest = _load_json_object(manifest_path, label="retailer source manifest")
    if manifest.get("schema_version") != RETAILER_SOURCE_MANIFEST_VERSION:
        raise SemanticIntegrationError("retailer source manifest has wrong version")
    if manifest.get("retailer_coding_raw_sha256") != hash_file(retailer_coding_path):
        raise SemanticIntegrationError("retailer source manifest has stale coding hash")
    expected_manifest_hash = manifest.get("manifest_sha256")
    unhashed = dict(manifest)
    unhashed.pop("manifest_sha256", None)
    if expected_manifest_hash != _canonical_hash(unhashed):
        raise SemanticIntegrationError("retailer source manifest hash mismatch")
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise SemanticIntegrationError("retailer source manifest lacks sources")
    if manifest.get("source_set_sha256") != _canonical_hash(sources):
        raise SemanticIntegrationError("retailer source-set hash mismatch")
    index: dict[str, Mapping[str, Any]] = {}
    native_ids_by_locator: dict[str, set[str]] = {}
    for row in sources:
        if not isinstance(row, Mapping) or not _nonempty(row.get("locator")):
            raise SemanticIntegrationError("retailer source manifest has invalid source")
        locator = str(Path(row["locator"]).resolve(strict=True))
        if locator in index:
            raise SemanticIntegrationError("retailer source manifest has duplicate locator")
        if row.get("hash_convention") != "sha256_raw_bytes":
            raise SemanticIntegrationError("retailer source uses an unknown hash convention")
        path = Path(locator)
        if row.get("raw_sha256") != hash_file(path):
            raise SemanticIntegrationError(f"retailer source hash mismatch: {locator}")
        source = _load_json_object(path, label=f"retailer source {locator}")
        parser_family, ids = _retailer_review_ids(source)
        if row.get("parser_family") != parser_family:
            raise SemanticIntegrationError(f"retailer source parser mismatch: {locator}")
        if row.get("native_review_id_count") != len(ids) or row.get(
            "native_review_ids_sha256"
        ) != _canonical_hash(sorted(ids)):
            raise SemanticIntegrationError(f"retailer native review set mismatch: {locator}")
        index[locator] = row
        native_ids_by_locator[locator] = ids
    return index, native_ids_by_locator


def census_phase_a_customer_corpus(
    *,
    evidence_ledger_path: Path,
    retailer_coding_path: Path,
    retailer_source_manifest_path: Path,
) -> dict[str, Any]:
    """Recount the captured Reddit and retailer leaves from their pinned source rows.

    This is deliberately a census, not semantic judgment. It prevents a selected
    coding subset from being mislabeled as the full customer corpus.
    """
    ledger = _load_json_object(evidence_ledger_path, label="evidence depth ledger")
    retailer = _load_json_object(retailer_coding_path, label="retailer axis coding")
    artifacts = ledger.get("artifacts")
    families = ledger.get("families")
    if not isinstance(artifacts, list) or not isinstance(families, Mapping):
        raise SemanticIntegrationError("evidence depth ledger lacks artifacts or families")
    artifact_index = {
        row.get("artifact_id"): row
        for row in artifacts
        if isinstance(row, Mapping) and _nonempty(row.get("artifact_id"))
    }
    reddit_family = families.get("reddit_forum")
    family_threads = (
        reddit_family.get("threads") if isinstance(reddit_family, Mapping) else None
    )
    if not isinstance(family_threads, list) or not family_threads:
        raise SemanticIntegrationError("evidence depth ledger lacks Reddit threads")
    target_rows = ledger.get("target_reconciliation")
    if not isinstance(target_rows, list):
        raise SemanticIntegrationError("evidence depth ledger lacks target reconciliation")
    thread_index: dict[str, dict[str, Any]] = {}
    for row in target_rows:
        if not isinstance(row, Mapping) or row.get("source_family") != "reddit_forum":
            continue
        if not _nonempty(row.get("native_artifact_id")):
            # A target that already yielded captured material owns leaves in
            # this denominator. Dropping it for a missing packet binding would
            # shrink the corpus silently instead of failing.
            if row.get("terminal_state") in CAPTURED_TERMINAL_STATES:
                raise SemanticIntegrationError(
                    "captured Reddit target lacks a native packet binding: "
                    f"{row.get('target_id')}"
                )
            continue
        thread_id = str(row.get("target_id", "")).removeprefix("reddit_")
        if not thread_id:
            raise SemanticIntegrationError("Reddit target with native packet lacks thread id")
        if thread_id in thread_index:
            raise SemanticIntegrationError(f"duplicate Reddit target thread: {thread_id}")
        thread_index[thread_id] = {
            "thread_id": thread_id,
            "artifact_id": row["native_artifact_id"],
        }
    # Historical parent packets predate target reconciliation. Their owning
    # coding artifact names them explicitly; the main family list is only the
    # 577 adjudicated-used set and therefore cannot supply this union by itself.
    coding_binding = ledger.get("community_axis_coding")
    coding_artifact_id = (
        coding_binding.get("artifact_id")
        if isinstance(coding_binding, Mapping)
        else None
    )
    coding_artifact = artifact_index.get(coding_artifact_id)
    if not isinstance(coding_artifact, Mapping) or not _nonempty(
        coding_artifact.get("locator")
    ):
        raise SemanticIntegrationError("ledger lacks community-axis coding binding")
    coding_path = _resolve_ledger_locator(
        evidence_ledger_path, coding_artifact["locator"]
    )
    expected_coding_hash = coding_artifact.get("sha256")
    if not _nonempty(expected_coding_hash) or _artifact_hash(coding_path) != expected_coding_hash:
        raise SemanticIntegrationError("community axis coding hash mismatch")
    coding = _load_json_object(coding_path, label="community axis coding")
    legacy_ids = coding.get("legacy_parent_threads_not_requalified")
    if not isinstance(legacy_ids, list) or any(
        not _nonempty(thread_id) for thread_id in legacy_ids
    ):
        raise SemanticIntegrationError("community axis coding lacks legacy parent thread ids")
    for thread_id in legacy_ids:
        if thread_id in thread_index:
            raise SemanticIntegrationError(
                f"legacy Reddit thread unexpectedly appears in target reconciliation: {thread_id}"
            )
        artifact_id = f"reddit_manifest_{thread_id}"
        if artifact_id not in artifact_index:
            raise SemanticIntegrationError(
                f"legacy Reddit thread {thread_id} lacks packet artifact"
            )
        thread_index[thread_id] = {
            "thread_id": thread_id,
            "artifact_id": artifact_id,
        }
    # The coded family cannot build the union, but it must still be inside it.
    # Reconciling the two sources is what stops the union from quietly
    # regressing to a subset the way the first census attempt did.
    family_ids: set[str] = set()
    for row in family_threads:
        if not isinstance(row, Mapping) or not _nonempty(row.get("thread_id")):
            raise SemanticIntegrationError(
                "evidence depth ledger has an invalid Reddit thread row"
            )
        family_ids.add(row["thread_id"])
    missing_family = sorted(family_ids - set(thread_index))
    if missing_family:
        raise SemanticIntegrationError(
            "coded Reddit threads are missing from the captured-corpus union: "
            f"{missing_family}"
        )
    threads = [thread_index[thread_id] for thread_id in sorted(thread_index)]
    target_states = {
        row.get("target_id", "").removeprefix("reddit_"): row.get("terminal_state")
        for row in target_rows
        if isinstance(row, Mapping)
        and row.get("source_family") == "reddit_forum"
        and _nonempty(row.get("target_id"))
    }
    reddit_counts = {
        "thread_count": len(threads),
        "root_count": 0,
        "comment_count": 0,
        "captured_leaf_count": 0,
        "readable_leaf_count": 0,
        "mechanically_excluded_leaf_count": 0,
        "captured_excluded_thread_count": 0,
        "captured_excluded_leaf_count": 0,
        "captured_excluded_readable_leaf_count": 0,
        "legacy_thread_count": 0,
    }
    manifest_hashes: list[dict[str, str]] = []
    thread_observations: dict[str, dict[str, int]] = {}
    for thread in threads:
        thread_id = thread["thread_id"]
        artifact_id = thread.get("artifact_id")
        artifact = artifact_index.get(artifact_id)
        if not isinstance(artifact, Mapping):
            raise SemanticIntegrationError(
                f"Reddit thread {thread_id} lacks its manifest artifact"
            )
        locator = artifact.get("locator")
        expected = artifact.get("sha256")
        if not _nonempty(locator) or not _nonempty(expected):
            raise SemanticIntegrationError(f"Reddit manifest binding is incomplete: {artifact_id}")
        manifest_path = Path(locator).resolve(strict=True)
        observed_manifest_hash = _canonical_json_file_hash(manifest_path)
        if observed_manifest_hash != expected:
            raise SemanticIntegrationError(
                f"Reddit manifest canonical hash mismatch for {artifact_id}"
            )
        manifest_hashes.append({"artifact_id": artifact_id, "sha256": expected})
        record = _reddit_record_from_manifest(manifest_path)
        post = record.get("post")
        comments = record.get("comments")
        thread_meta = record.get("thread")
        if not isinstance(post, Mapping) or not isinstance(comments, list):
            raise SemanticIntegrationError(f"Reddit record is malformed for {thread_id}")
        record_thread_id = thread_meta.get("thread_id") if isinstance(thread_meta, Mapping) else None
        if _nonempty(record_thread_id) and record_thread_id != thread_id:
            raise SemanticIntegrationError(
                f"Reddit record thread id mismatch: expected {thread_id}, observed {record_thread_id}"
            )
        # The title is required conversation context, not a substitute for a
        # missing author body. Counting it as a leaf would manufacture 131
        # assessable roots in the Summer Fridays corpus.
        root_text = post.get("body_text") if _nonempty(post.get("body_text")) else ""
        readable_comments = sum(
            isinstance(row, Mapping) and _nonempty(row.get("body_text"))
            for row in comments
        )
        captured = 1 + len(comments)
        readable = int(bool(root_text)) + readable_comments
        excluded = captured - readable
        reddit_counts["root_count"] += 1
        reddit_counts["comment_count"] += len(comments)
        reddit_counts["captured_leaf_count"] += captured
        reddit_counts["readable_leaf_count"] += readable
        reddit_counts["mechanically_excluded_leaf_count"] += excluded
        state = target_states.get(thread_id)
        if state == "captured_excluded":
            reddit_counts["captured_excluded_thread_count"] += 1
            reddit_counts["captured_excluded_leaf_count"] += captured
            reddit_counts["captured_excluded_readable_leaf_count"] += readable
        elif state is None:
            reddit_counts["legacy_thread_count"] += 1
        thread_observations[thread_id] = {
            "captured_leaf_count": captured,
            "readable_leaf_count": readable,
        }

    corpora = retailer.get("corpora")
    rows = retailer.get("rows")
    if not isinstance(corpora, list) or not isinstance(rows, list):
        raise SemanticIntegrationError("retailer coding lacks corpora or rows")
    source_manifest, native_review_ids = _verify_retailer_source_manifest(
        retailer_coding_path=retailer_coding_path,
        manifest_path=retailer_source_manifest_path,
    )
    review_keys: set[tuple[str, str]] = set()
    source_files: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise SemanticIntegrationError("retailer coding has invalid review row")
        corpus_id = row.get("corpus_id")
        review_id = str(row.get("review_id", ""))
        source_ref = row.get("source_row_ref")
        if not _nonempty(corpus_id) or not review_id or not _nonempty(source_ref):
            raise SemanticIntegrationError("retailer coding row lacks source identity")
        key = (corpus_id, review_id)
        if key in review_keys:
            raise SemanticIntegrationError(f"duplicate retailer review identity: {key}")
        review_keys.add(key)
        locator, separator, anchor = source_ref.partition("#review:")
        if separator != "#review:" or anchor != review_id:
            raise SemanticIntegrationError(f"invalid retailer source row ref: {source_ref}")
        source_path = Path(locator).resolve(strict=True)
        source_key = str(source_path)
        manifest_source = source_manifest.get(source_key)
        if not isinstance(manifest_source, Mapping):
            raise SemanticIntegrationError(
                f"retailer source is absent from its manifest: {source_key}"
            )
        referenced = manifest_source.get("referenced_review_ids")
        if not isinstance(referenced, list) or review_id not in referenced:
            raise SemanticIntegrationError(
                f"retailer review {review_id} is absent from its source manifest"
            )
        # `referenced_review_ids` is a manifest declaration. Membership must
        # still be proven against the source-native review rows, or a manifest
        # that names a review the file does not contain would admit it.
        if review_id not in native_review_ids[source_key]:
            raise SemanticIntegrationError(
                f"retailer review {review_id} is absent from its source-native review rows"
            )
        source_files.add(source_key)
    if source_files != set(source_manifest):
        raise SemanticIntegrationError("retailer source manifest does not exactly match coding sources")
    # A skipped, unnamed, or collapsed corpus row would silently delete one
    # corpus's excluded reviews from the captured denominator, so every corpus
    # row must be well formed and uniquely named.
    eligible_by_corpus: dict[str, Any] = {}
    excluded_by_corpus: dict[str, Any] = {}
    for row in corpora:
        if not isinstance(row, Mapping) or not _nonempty(row.get("corpus_id")):
            raise SemanticIntegrationError("retailer coding has an invalid corpus row")
        corpus_id = row["corpus_id"]
        if corpus_id in eligible_by_corpus:
            raise SemanticIntegrationError(
                f"retailer coding has a duplicate corpus id: {corpus_id}"
            )
        eligible_by_corpus[corpus_id] = row.get("eligible_text_review_count")
        excluded_by_corpus[corpus_id] = row.get("excluded_no_usable_text_count")
    undeclared = sorted(
        {corpus_id for corpus_id, _ in review_keys} - set(eligible_by_corpus)
    )
    if undeclared:
        raise SemanticIntegrationError(
            f"retailer coding rows cite corpora with no declared denominator: {undeclared}"
        )
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in eligible_by_corpus.values()
    ):
        raise SemanticIntegrationError("retailer eligible-text denominator is invalid")
    if sum(eligible_by_corpus.values()) != len(rows):
        raise SemanticIntegrationError("retailer eligible-text denominator does not match rows")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in excluded_by_corpus.values()
    ):
        raise SemanticIntegrationError("retailer excluded denominator is invalid")
    retailer_counts = {
        "captured_review_count": len(rows) + sum(excluded_by_corpus.values()),
        "readable_review_count": len(rows),
        "mechanically_excluded_review_count": sum(excluded_by_corpus.values()),
        "source_file_count": len(source_files),
        "eligible_text_by_corpus": dict(sorted(eligible_by_corpus.items())),
        "excluded_no_text_by_corpus": dict(sorted(excluded_by_corpus.items())),
    }
    result = {
        "schema_version": CORPUS_CENSUS_VERSION,
        "cycle_id": ledger.get("cycle_id"),
        "evidence_ledger_sha256": hash_file(evidence_ledger_path),
        "retailer_coding_sha256": hash_file(retailer_coding_path),
        "retailer_source_manifest_sha256": hash_file(retailer_source_manifest_path),
        "retailer_source_set_sha256": _canonical_hash(
            [source_manifest[key] for key in sorted(source_manifest)]
        ),
        "reddit_target_terminal_state_counts": {
            state: sum(value == state for value in target_states.values())
            for state in sorted(set(target_states.values()))
        },
        "reddit_projection_dependency": {
            "content_record": "source-native preserved content record",
            "html_fallback": "source_capture.reddit_consolidation.build_thread_content_record",
        },
        "reddit": reddit_counts,
        "retailer_reviews": retailer_counts,
        "selected_subset_used_as_denominator": False,
        "historical_seal_restamped": False,
        "model_api_calls": 0,
        "sentinel_threads": {
            thread_id: thread_observations[thread_id]
            for thread_id in ("1gti140",)
            if thread_id in thread_observations
        },
        "reddit_manifest_set_sha256": _canonical_hash(manifest_hashes),
    }
    result["census_sha256"] = _canonical_hash(result)
    return result


def _source_artifact(
    artifact_id: str, path: Path, *, repo_root: Path
) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    try:
        locator = resolved.relative_to(repo_root.resolve(strict=True)).as_posix()
    except ValueError:
        locator = str(resolved)
    return {
        "artifact_id": artifact_id,
        "locator": locator,
        "sha256": hash_file(resolved),
    }


def _phase_a_source_shell(spec: Mapping[str, Any]) -> dict[str, Any]:
    _validate_run_spec_shape(spec)
    return {
        "schema_version": "semantic_evidence_source_v3",
        "cycle_id": spec["cycle_id"],
        "question_id": spec["question_id"],
        "question": spec["question"],
        "corpus_profile": spec["corpus_profile"],
        "corpus_scope": spec["corpus_scope"],
        "corpus_cutoff": spec["corpus_cutoff"],
        "axes": spec["axes"],
    }


def _materialize_declared_source(source: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize source accounting before separate batch packing."""
    return materialize_source_v3(source)


def _reddit_manifest_record(
    manifest_path: Path,
) -> tuple[dict[str, Any], Path, str, str]:
    """Return the projected record and the exact preserved bytes that own it."""
    manifest = _load_json_object(manifest_path, label="Reddit packet manifest")
    preserved = manifest.get("preserved_files")
    if not isinstance(preserved, list):
        raise SemanticIntegrationError("Reddit packet manifest lacks preserved files")
    content: list[Path] = []
    html: list[Path] = []
    for row in preserved:
        if not isinstance(row, Mapping) or not _nonempty(row.get("relative_packet_path")):
            continue
        relative = row["relative_packet_path"]
        path = (manifest_path.parent / relative).resolve(strict=True)
        lowered = relative.lower()
        if lowered.endswith("content_record.json"):
            content.append(path)
        elif lowered.endswith(("http_response_body.bin", ".html", ".htm")):
            html.append(path)
    if len(content) > 1 or len(html) > 1 or (not content and not html):
        raise SemanticIntegrationError(
            f"Reddit packet has an ambiguous or absent source record: {manifest_path}"
        )
    source_path = content[0] if content else html[0]
    record = _reddit_record_from_manifest(manifest_path)
    locator_row = manifest.get("source_locator")
    source_ref = (
        locator_row.get("value") if isinstance(locator_row, Mapping) else None
    )
    if not _nonempty(source_ref):
        raise SemanticIntegrationError(f"Reddit packet lacks source URL: {manifest_path}")
    timing = manifest.get("timing")
    capture = timing.get("capture_time") if isinstance(timing, Mapping) else None
    captured_at = capture.get("value") if isinstance(capture, Mapping) else None
    if not _nonempty(captured_at):
        captured_at = "capture_time_unavailable_in_packet"
    return record, source_path, source_ref, captured_at


def _score_value(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return None
    match = re.search(r"-?\d[\d,]*", value)
    return int(match.group(0).replace(",", "")) if match else None


def _identity_fields(prefix: str, value: Any) -> tuple[str, str | None]:
    if not _nonempty(value):
        return "unavailable", None
    normalized = value.strip()
    lowered = normalized.casefold()
    if lowered in {"[deleted]", "[removed]", "unknown"} or lowered.startswith(
        "unknown_with_reason:"
    ):
        return "unavailable", None
    return "credited", f"{prefix}:{lowered}"


def build_phase_a_reddit_source_v3(
    *, run_spec_path: Path, evidence_ledger_path: Path, repo_root: Path
) -> dict[str, Any]:
    """Build the complete packet-backed Reddit v3 fragment without model calls."""
    spec = _load_json_object(run_spec_path, label="Phase A run spec")
    source = _phase_a_source_shell(spec)
    ledger = _load_json_object(evidence_ledger_path, label="evidence depth ledger")
    if ledger.get("cycle_id") != spec["cycle_id"]:
        raise SemanticIntegrationError("Reddit ledger cycle does not match run spec")
    artifacts = ledger.get("artifacts")
    families = ledger.get("families")
    targets = ledger.get("target_reconciliation")
    if not isinstance(artifacts, list) or not isinstance(families, Mapping) or not isinstance(
        targets, list
    ):
        raise SemanticIntegrationError("Reddit ledger lacks corpus bindings")
    artifact_index = {
        row.get("artifact_id"): row
        for row in artifacts
        if isinstance(row, Mapping) and _nonempty(row.get("artifact_id"))
    }
    thread_bindings: dict[str, str] = {}
    target_axes: dict[str, list[str]] = {}
    for row in targets:
        if not isinstance(row, Mapping) or row.get("source_family") != "reddit_forum":
            continue
        thread_id = str(row.get("target_id", "")).removeprefix("reddit_")
        artifact_id = row.get("native_artifact_id")
        if _nonempty(artifact_id):
            if not thread_id or thread_id in thread_bindings:
                raise SemanticIntegrationError("Reddit target identities are duplicated")
            thread_bindings[thread_id] = artifact_id
            axis_ids = row.get("axis_ids", [])
            if not isinstance(axis_ids, list) or any(not _nonempty(v) for v in axis_ids):
                raise SemanticIntegrationError(f"Reddit target has invalid axes: {thread_id}")
            target_axes[thread_id] = list(axis_ids)
        elif row.get("terminal_state") in CAPTURED_TERMINAL_STATES:
            raise SemanticIntegrationError(
                f"captured Reddit target lacks native artifact: {thread_id}"
            )
    coding_binding = ledger.get("community_axis_coding")
    coding_id = (
        coding_binding.get("artifact_id") if isinstance(coding_binding, Mapping) else None
    )
    coding_artifact = artifact_index.get(coding_id)
    if not isinstance(coding_artifact, Mapping) or not _nonempty(
        coding_artifact.get("locator")
    ):
        raise SemanticIntegrationError("Reddit ledger lacks community coding")
    coding_path = _resolve_ledger_locator(
        evidence_ledger_path, coding_artifact["locator"]
    )
    if coding_artifact.get("sha256") != _artifact_hash(coding_path):
        raise SemanticIntegrationError("community coding hash mismatch")
    coding = _load_json_object(coding_path, label="community axis coding")
    legacy_ids = coding.get("legacy_parent_threads_not_requalified")
    coding_rows = coding.get("rows")
    if not isinstance(legacy_ids, list) or not isinstance(coding_rows, list):
        raise SemanticIntegrationError("community coding lacks rows or legacy threads")
    for thread_id in legacy_ids:
        if not _nonempty(thread_id):
            raise SemanticIntegrationError("community coding has invalid legacy thread")
        artifact_id = f"reddit_manifest_{thread_id}"
        if thread_id in thread_bindings or artifact_id not in artifact_index:
            raise SemanticIntegrationError(
                f"legacy Reddit binding is duplicated or absent: {thread_id}"
            )
        thread_bindings[thread_id] = artifact_id
    family = families.get("reddit_forum")
    family_rows = family.get("threads") if isinstance(family, Mapping) else None
    if not isinstance(family_rows, list) or not family_rows:
        raise SemanticIntegrationError("Reddit family has no coded threads")
    family_ids = {
        row.get("thread_id")
        for row in family_rows
        if isinstance(row, Mapping) and _nonempty(row.get("thread_id"))
    }
    if not family_ids <= set(thread_bindings):
        raise SemanticIntegrationError("coded Reddit family is outside captured union")
    known_axis_ids = {row["axis_id"] for row in spec["axes"]}
    coded_by_leaf: dict[tuple[str, str], dict[str, set[str]]] = {}
    for row in coding_rows:
        if not isinstance(row, Mapping) or not _nonempty(row.get("thread_id")) or not _nonempty(
            row.get("comment_id")
        ):
            raise SemanticIntegrationError("community coding has invalid row identity")
        key = (row["thread_id"], row["comment_id"])
        entry = coded_by_leaf.setdefault(key, {"products": set(), "axes": set()})
        if _nonempty(row.get("product_context")):
            entry["products"].add(row["product_context"].strip())
        axes = row.get("axis_ids", [])
        if not isinstance(axes, list) or any(axis not in known_axis_ids for axis in axes):
            raise SemanticIntegrationError(f"community coding has unknown axis: {key}")
        entry["axes"].update(axes)

    source_artifacts = [
        _source_artifact(
            "reddit_evidence_ledger", evidence_ledger_path, repo_root=repo_root
        ),
        _source_artifact(
            "reddit_community_coding", coding_path, repo_root=repo_root
        ),
    ]
    containers: list[dict[str, Any]] = []
    captured_items: list[dict[str, Any]] = []
    seen_artifact_ids = {row["artifact_id"] for row in source_artifacts}
    for thread_id in sorted(thread_bindings):
        manifest_id = thread_bindings[thread_id]
        binding = artifact_index.get(manifest_id)
        if not isinstance(binding, Mapping) or not _nonempty(binding.get("locator")):
            raise SemanticIntegrationError(f"Reddit manifest is absent: {manifest_id}")
        manifest_path = _resolve_ledger_locator(evidence_ledger_path, binding["locator"])
        if binding.get("sha256") != _canonical_json_file_hash(manifest_path):
            raise SemanticIntegrationError(f"Reddit manifest hash mismatch: {manifest_id}")
        record, record_path, source_ref, captured_at = _reddit_manifest_record(
            manifest_path
        )
        raw_artifact_id = f"reddit_source_{thread_id}"
        for artifact in (
            _source_artifact(manifest_id, manifest_path, repo_root=repo_root),
            _source_artifact(raw_artifact_id, record_path, repo_root=repo_root),
        ):
            if artifact["artifact_id"] in seen_artifact_ids:
                raise SemanticIntegrationError("Reddit source artifact id is duplicated")
            seen_artifact_ids.add(artifact["artifact_id"])
            source_artifacts.append(artifact)
        post = record.get("post")
        comments = record.get("comments")
        thread = record.get("thread")
        if not isinstance(post, Mapping) or not isinstance(comments, list):
            raise SemanticIntegrationError(f"Reddit source record is malformed: {thread_id}")
        title = thread.get("title") if isinstance(thread, Mapping) else None
        if not _nonempty(title):
            title = source_ref
        container_id = f"reddit_thread_{thread_id}"
        containers.append(
            {
                "container_id": container_id,
                "container_type": "conversation",
                "source_artifact_id": raw_artifact_id,
                "captured_leaf_count": 1 + len(comments),
                "source_visible_total": "unavailable",
                "completeness": "unavailable",
                "captured_at": captured_at,
                "capture_boundary": "exact preserved Reddit packet; title is context only",
            }
        )
        post_text = post.get("body_text") if isinstance(post.get("body_text"), str) else ""
        post_disposition = (
            "mechanically_excluded"
            if not post_text.strip() or post_text.strip() in _REDDIT_PLACEHOLDERS
            else "assess"
        )
        post_ref = source_ref
        posture, key = _identity_fields("reddit", post.get("author_state"))
        post_item: dict[str, Any] = {
            "evidence_id": f"reddit:{thread_id}:post",
            "container_id": container_id,
            "source_artifact_id": raw_artifact_id,
            "source_ref": post_ref,
            "accounting_disposition": post_disposition,
            "accounting_reason": (
                "readable source-native post body"
                if post_disposition == "assess"
                else "empty or exact Reddit deletion placeholder"
            ),
        }
        if post_disposition == "assess":
            score = _score_value(post.get("score_state"))
            post_item.update(
                {
                    "source_family": "reddit_community",
                    "source_role": "community_post",
                    "text": post_text.strip(),
                    "product_candidates": [],
                    "axis_candidates": sorted(
                        set(target_axes.get(thread_id, [])) & known_axis_ids
                    ),
                    "product_context": [
                        {
                            "context_type": "thread_title",
                            "source_artifact_id": raw_artifact_id,
                            "text": title,
                            "source_ref": source_ref,
                        }
                    ],
                    "independence_posture": posture,
                    "independence_key": key,
                    "engagement": {
                        "raw_score_state": post.get("score_state"),
                        "material_positive": score is not None and score > 1,
                        "materiality_basis": "Reddit score exceeds the one-point self-vote baseline",
                    },
                    "conversation_depth": 0,
                    "parent_context": [],
                }
            )
        captured_items.append(post_item)
        ancestor_stack: list[dict[str, str]] = []
        # Reddit reports top-level comments at depth 0, so the root post occupies
        # a fixed base frame below every reply depth. Without that offset the
        # first depth-0 comment pops the root off the stack and every reply in
        # the thread travels without the post body it answers.
        root_frames = 0
        if post_disposition == "assess":
            ancestor_stack.append({"source_ref": post_ref, "text": post_text.strip()})
            root_frames = 1
        for ordinal, comment in enumerate(comments, start=1):
            if not isinstance(comment, Mapping):
                raise SemanticIntegrationError(f"Reddit comment is malformed: {thread_id}")
            native_comment_id = comment.get("comment_id")
            if not _nonempty(native_comment_id) or native_comment_id.casefold() in {
                "deleted",
                "removed",
            }:
                native_comment_id = comment.get("row_id") or f"row_{ordinal:06d}"
            comment_id = str(native_comment_id)
            text = comment.get("body_text") if isinstance(comment.get("body_text"), str) else ""
            disposition = (
                "mechanically_excluded"
                if not text.strip() or text.strip() in _REDDIT_PLACEHOLDERS
                else "assess"
            )
            comment_ref = f"https://www.reddit.com/comments/{thread_id}/_/{comment_id}"
            item: dict[str, Any] = {
                "evidence_id": f"reddit:{thread_id}:{comment_id}",
                "container_id": container_id,
                "source_artifact_id": raw_artifact_id,
                "source_ref": comment_ref,
                "accounting_disposition": disposition,
                "accounting_reason": (
                    "readable source-native comment body"
                    if disposition == "assess"
                    else "empty or exact Reddit deletion placeholder"
                ),
            }
            raw_depth = comment.get("depth", 0)
            depth = raw_depth if isinstance(raw_depth, int) and not isinstance(raw_depth, bool) else 0
            depth = max(depth, 0)
            if disposition == "assess":
                coded = coded_by_leaf.get((thread_id, comment_id), {})
                product_candidates = sorted(coded.get("products", set()))
                axis_candidates = set(coded.get("axes", set()))
                if not axis_candidates:
                    axis_candidates.update(target_axes.get(thread_id, []))
                effective_depth = min(depth + root_frames, len(ancestor_stack))
                while len(ancestor_stack) > effective_depth:
                    ancestor_stack.pop()
                parent_context = list(ancestor_stack)
                credited, identity_key = _identity_fields(
                    "reddit", comment.get("author_state")
                )
                score = _score_value(comment.get("score_state"))
                item.update(
                    {
                        "source_family": "reddit_community",
                        "source_role": "community_post",
                        "text": text.strip(),
                        "product_candidates": product_candidates,
                        "axis_candidates": sorted(axis_candidates & known_axis_ids),
                        "product_context": [
                            {
                                "context_type": "thread_title",
                                "source_artifact_id": raw_artifact_id,
                                "text": title,
                                "source_ref": source_ref,
                            }
                        ],
                        "independence_posture": credited,
                        "independence_key": identity_key,
                        "engagement": {
                            "raw_score_state": comment.get("score_state"),
                            "material_positive": score is not None and score > 1,
                            "materiality_basis": "Reddit score exceeds the one-point self-vote baseline",
                        },
                        "conversation_depth": len(parent_context),
                        "source_reported_depth": depth,
                        "parent_context": parent_context,
                    }
                )
                ancestor = {"source_ref": comment_ref, "text": text.strip()}
                if len(ancestor_stack) == effective_depth:
                    ancestor_stack.append(ancestor)
                else:
                    ancestor_stack[effective_depth] = ancestor
            captured_items.append(item)
    source.update(
        {
            "source_artifacts": source_artifacts,
            "containers": containers,
            "captured_items": captured_items,
        }
    )
    return _materialize_declared_source(source)


def _retailer_rows(source: Mapping[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    parser_family, native_ids = _retailer_review_ids(source)
    rows: dict[str, dict[str, Any]] = {}
    if parser_family == "amazon_aggregate_v1":
        candidates = []
        for row in source["rows"]:
            if isinstance(row, Mapping) and row.get("row_kind") == "retail_review_row":
                fields = row.get("source_visible_fields")
                if isinstance(fields, Mapping):
                    candidates.append(fields)
        for row in candidates:
            review_id = str(row.get("review_id", ""))
            rows[review_id] = {
                "text": row.get("body"),
                "author": row.get("author"),
                "helpful_positive": row.get("helpful_count"),
                "raw": row,
            }
    elif parser_family == "bazaarvoice_results_v1":
        for row in source["Results"]:
            if not isinstance(row, Mapping) or row.get("Id") is None:
                continue
            review_id = str(row["Id"])
            rows[review_id] = {
                "text": row.get("ReviewText"),
                "author": row.get("AuthorId") or row.get("UserNickname"),
                "helpful_positive": row.get("TotalPositiveFeedbackCount"),
                "raw": row,
            }
    else:
        for response in source.get("responses", []):
            if not isinstance(response, Mapping) or not isinstance(response.get("body_text"), str):
                raise SemanticIntegrationError("Revolve response lacks body text")
            try:
                body = json.loads(response["body_text"])
            except json.JSONDecodeError as exc:
                raise SemanticIntegrationError("Revolve response body is invalid JSON") from exc
            reviews = body.get("reviews") if isinstance(body, Mapping) else None
            if not isinstance(reviews, list):
                raise SemanticIntegrationError("Revolve response lacks reviews")
            for row in reviews:
                if not isinstance(row, Mapping) or row.get("id") is None:
                    continue
                review_id = str(row["id"])
                normalized = {
                    "text": row.get("content"),
                    "author": (
                        row.get("user", {}).get("userId")
                        if isinstance(row.get("user"), Mapping)
                        else None
                    )
                    or (
                        row.get("user", {}).get("displayName")
                        if isinstance(row.get("user"), Mapping)
                        else None
                    ),
                    "helpful_positive": row.get("votesUp"),
                    "raw": row,
                }
                if review_id in rows and rows[review_id] != normalized:
                    raise SemanticIntegrationError(
                        f"Revolve review changes across response pages: {review_id}"
                    )
                rows[review_id] = normalized
    if set(rows) != native_ids:
        raise SemanticIntegrationError(
            f"retailer parser did not reproduce native review ids: {parser_family}"
        )
    return parser_family, rows


def build_phase_a_retailer_source_v3(
    *,
    run_spec_path: Path,
    retailer_coding_path: Path,
    retailer_source_manifest_path: Path,
    revolve_completion_receipt_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the full deduplicated retailer-review v3 fragment."""
    spec = _load_json_object(run_spec_path, label="Phase A run spec")
    source = _phase_a_source_shell(spec)
    coding = _load_json_object(retailer_coding_path, label="retailer axis coding")
    coding_rows = coding.get("rows")
    if not isinstance(coding_rows, list):
        raise SemanticIntegrationError("retailer coding lacks rows")
    manifest_sources, _ = _verify_retailer_source_manifest(
        retailer_coding_path=retailer_coding_path,
        manifest_path=retailer_source_manifest_path,
    )
    completion = _load_json_object(
        revolve_completion_receipt_path, label="Revolve completion receipt"
    )
    if completion.get("schema_version") != "revolve_review_corpus_completion_run_v1":
        raise SemanticIntegrationError("Revolve completion receipt has wrong version")
    outcomes = completion.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise SemanticIntegrationError("Revolve completion receipt lacks outcomes")
    source_paths: dict[str, dict[str, Any]] = {}
    for locator, row in manifest_sources.items():
        source_paths[locator] = {"parser_family": row["parser_family"]}
    completion_occurrences: list[str] = []
    for outcome in outcomes:
        if (
            not isinstance(outcome, Mapping)
            or outcome.get("status") != "complete"
            or outcome.get("failure") is not None
            or not _nonempty(outcome.get("receipt_path"))
            or not _nonempty(outcome.get("receipt_sha256"))
        ):
            raise SemanticIntegrationError("Revolve completion has a non-complete outcome")
        path = Path(outcome["receipt_path"]).resolve(strict=True)
        if hash_file(path) != outcome["receipt_sha256"]:
            raise SemanticIntegrationError(f"Revolve corpus hash mismatch: {path}")
        key = str(path)
        existing = source_paths.get(key)
        if existing is not None and existing["parser_family"] != "revolve_recent_v1":
            raise SemanticIntegrationError("completion receipt collides with non-Revolve source")
        source_paths[key] = {"parser_family": "revolve_recent_v1"}
        corpus = _load_json_object(path, label=f"Revolve corpus {path}")
        ids = corpus.get("captured_review_ids")
        if not isinstance(ids, list) or len(ids) != outcome.get("captured_review_count"):
            raise SemanticIntegrationError("Revolve outcome count does not match corpus")
        completion_occurrences.extend(str(value) for value in ids)
    if completion.get("completed_corpus_count") != len(outcomes):
        raise SemanticIntegrationError("Revolve completion corpus count is stale")
    if completion.get("captured_review_occurrence_count") != len(completion_occurrences):
        raise SemanticIntegrationError("Revolve completion occurrence count is stale")
    unique_revolve = set(completion_occurrences)
    if completion.get("unique_review_id_count") != len(unique_revolve):
        raise SemanticIntegrationError("Revolve completion unique-review count is stale")
    occurrence_counts: dict[str, int] = {}
    for review_id in completion_occurrences:
        occurrence_counts[review_id] = occurrence_counts.get(review_id, 0) + 1
    duplicated_ids = sorted(
        review_id for review_id, count in occurrence_counts.items() if count > 1
    )
    if completion.get("cross_corpus_duplicate_review_ids") != duplicated_ids:
        raise SemanticIntegrationError("Revolve completion duplicate count is stale")

    artifact_by_path: dict[str, str] = {}
    source_artifacts = [
        _source_artifact(
            "retailer_axis_coding", retailer_coding_path, repo_root=repo_root
        ),
        _source_artifact(
            "retailer_source_manifest",
            retailer_source_manifest_path,
            repo_root=repo_root,
        ),
        _source_artifact(
            "revolve_completion_receipt",
            revolve_completion_receipt_path,
            repo_root=repo_root,
        ),
    ]
    parsed_by_path: dict[str, tuple[str, dict[str, dict[str, Any]]]] = {}
    revolve_product_ids_by_path: dict[str, list[str]] = {}
    for locator in sorted(source_paths):
        path = Path(locator)
        artifact_id = "retailer_source_" + hashlib.sha256(
            locator.casefold().encode("utf-8")
        ).hexdigest()[:20]
        artifact_by_path[locator] = artifact_id
        source_artifacts.append(
            _source_artifact(artifact_id, path, repo_root=repo_root)
        )
        source_object = _load_json_object(path, label=f"retailer source {path}")
        parsed = _retailer_rows(source_object)
        if parsed[0] != source_paths[locator]["parser_family"]:
            raise SemanticIntegrationError(f"retailer parser family changed: {locator}")
        if parsed[0] == "revolve_recent_v1":
            source_product_ids = source_object.get("source_product_ids")
            if (
                not isinstance(source_product_ids, list)
                or not source_product_ids
                or any(not _nonempty(value) for value in source_product_ids)
            ):
                raise SemanticIntegrationError(
                    f"Revolve retailer source lacks product listing ids: {locator}"
                )
            revolve_product_ids_by_path[locator] = sorted(set(source_product_ids))
        parsed_by_path[locator] = parsed

    coded: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in coding_rows:
        if not isinstance(row, Mapping) or not _nonempty(row.get("corpus_id")):
            raise SemanticIntegrationError("retailer coding has invalid row")
        review_id = str(row.get("review_id", ""))
        locator, separator, anchor = str(row.get("source_row_ref", "")).partition(
            "#review:"
        )
        path = str(Path(locator).resolve(strict=True)) if separator else ""
        if separator != "#review:" or anchor != review_id or path not in parsed_by_path:
            raise SemanticIntegrationError("retailer coding row has invalid source binding")
        if review_id not in parsed_by_path[path][1]:
            raise SemanticIntegrationError(f"coded retailer review is absent: {review_id}")
        key = (row["corpus_id"], review_id)
        if key in coded:
            raise SemanticIntegrationError(f"retailer coding duplicates review: {key}")
        coded[key] = row

    corpus_by_parser = {
        "amazon_aggregate_v1": "amazon_rendered_reviews",
        "revolve_recent_v1": "revolve_native_reviews",
        "bazaarvoice_results_v1": "sephora_product_group_reviews",
    }
    native: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
    for locator, (parser_family, rows) in parsed_by_path.items():
        corpus_id = corpus_by_parser[parser_family]
        for review_id, row in rows.items():
            native.setdefault((corpus_id, review_id), []).append((locator, row))
    missing_native = sorted(set(coded) - set(native))
    if missing_native:
        raise SemanticIntegrationError(f"coded retailer reviews are absent: {missing_native}")
    uncoded_nonplaceholder: list[tuple[str, str]] = []
    excluded: set[tuple[str, str]] = set()
    for key, occurrences in native.items():
        if key in coded:
            continue
        texts = {
            row.get("text").strip()
            for _, row in occurrences
            if isinstance(row.get("text"), str)
        }
        if key[0] == "revolve_native_reviews" and texts == {
            _REVOLVE_RATING_ONLY_PLACEHOLDER
        }:
            excluded.add(key)
        else:
            uncoded_nonplaceholder.append(key)
    if uncoded_nonplaceholder:
        raise SemanticIntegrationError(
            "captured non-placeholder retailer reviews are uncoded: "
            f"{uncoded_nonplaceholder[:10]}"
        )

    known_axes = {row["axis_id"] for row in spec["axes"]}
    containers: list[dict[str, Any]] = []
    captured_items: list[dict[str, Any]] = []
    for corpus_id, review_id in sorted(native):
        occurrences = native[(corpus_id, review_id)]
        owner_locator, raw = sorted(occurrences, key=lambda pair: pair[0])[0]
        artifact_id = artifact_by_path[owner_locator]
        container_id = f"retailer_review_{corpus_id}_{review_id}"
        containers.append(
            {
                "container_id": container_id,
                "container_type": "retailer_review",
                "source_artifact_id": artifact_id,
                "captured_leaf_count": 1,
                "source_visible_total": 1,
                "completeness": "complete",
                # No admitted retailer source format preserves a capture
                # timestamp, so a reusable builder must not stamp one.
                "captured_at": "capture_time_unavailable_in_preserved_source",
                "capture_boundary": "one source-native retailer review, deduplicated by corpus and native review id",
            }
        )
        source_ref = f"{owner_locator}#review:{review_id}"
        if (corpus_id, review_id) in excluded:
            captured_items.append(
                {
                    "evidence_id": f"retailer:{corpus_id}:{review_id}",
                    "container_id": container_id,
                    "source_artifact_id": artifact_id,
                    "source_ref": source_ref,
                    "accounting_disposition": "mechanically_excluded",
                    "accounting_reason": "exact source-native Revolve rating-only placeholder",
                }
            )
            continue
        coding_row = coded[(corpus_id, review_id)]
        text = raw.get("text")
        if not _nonempty(text) or text.strip() in _REDDIT_PLACEHOLDERS or text.strip() == _REVOLVE_RATING_ONLY_PLACEHOLDER:
            raise SemanticIntegrationError(f"coded retailer review lacks usable text: {review_id}")
        axis_codes = coding_row.get("axis_codes", [])
        if not isinstance(axis_codes, list):
            raise SemanticIntegrationError("retailer coding has invalid axis codes")
        axis_ids = {
            row.get("axis_id")
            for row in axis_codes
            if isinstance(row, Mapping) and _nonempty(row.get("axis_id"))
        }
        if not axis_ids <= known_axes:
            raise SemanticIntegrationError(f"retailer review cites unknown axis: {review_id}")
        product_id = str(coding_row.get("product_context_id", "")).strip()
        if not product_id:
            raise SemanticIntegrationError(f"retailer review lacks product context: {review_id}")
        product_ids = [product_id]
        product_context = [
            {
                "context_type": "product_page",
                "source_artifact_id": artifact_id,
                "text": product_id,
                "source_ref": source_ref,
            }
        ]
        if corpus_id == "revolve_native_reviews":
            product_context = []
            product_ids = sorted(
                {
                    occurrence_product_id
                    for occurrence_locator, _ in occurrences
                    for occurrence_product_id in revolve_product_ids_by_path[
                        occurrence_locator
                    ]
                }
            )
            if product_id not in product_ids:
                raise SemanticIntegrationError(
                    f"coded Revolve product context is absent from source occurrences: {review_id}"
                )
            for occurrence_locator, _ in sorted(occurrences, key=lambda pair: pair[0]):
                occurrence_ref = f"{occurrence_locator}#review:{review_id}"
                for occurrence_product_id in revolve_product_ids_by_path[
                    occurrence_locator
                ]:
                    product_context.append(
                        {
                            "context_type": "product_page",
                            "source_artifact_id": artifact_by_path[occurrence_locator],
                            "text": occurrence_product_id,
                            "source_ref": occurrence_ref,
                        }
                    )
        posture, identity_key = _identity_fields(f"retailer:{corpus_id}", raw.get("author"))
        helpful = raw.get("helpful_positive")
        helpful_value = helpful if isinstance(helpful, (int, float)) and not isinstance(helpful, bool) else None
        captured_items.append(
            {
                "evidence_id": f"retailer:{corpus_id}:{review_id}",
                "container_id": container_id,
                "source_family": "retailer_review",
                "source_role": "retailer_review",
                "source_artifact_id": artifact_id,
                "source_ref": source_ref,
                "text": text.strip(),
                "accounting_disposition": "assess",
                "accounting_reason": "readable source-native retailer review text",
                "product_candidates": product_ids,
                "axis_candidates": sorted(axis_ids),
                "product_context": product_context,
                "independence_posture": posture,
                "independence_key": identity_key,
                "engagement": {
                    "raw_positive_helpful_count": helpful,
                    "material_positive": helpful_value is not None and helpful_value > 0,
                    "materiality_basis": "source-native positive helpful vote count exceeds zero",
                },
                "conversation_depth": 0,
                "parent_context": [],
            }
        )
    source.update(
        {
            "source_artifacts": source_artifacts,
            "containers": containers,
            "captured_items": captured_items,
        }
    )
    return _materialize_declared_source(source)


def _native_social_key(locator: str) -> tuple[str, str] | None:
    parsed = urlparse(locator)
    host = parsed.netloc.casefold().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if "reddit.com" in host:
        try:
            index = parts.index("comments")
            return "reddit", parts[index + 1]
        except (ValueError, IndexError):
            return None
    if host in {"youtu.be"} and parts:
        return "youtube", parts[0]
    if "youtube.com" in host:
        query = parsed.query.split("&")
        for row in query:
            if row.startswith("v=") and len(row) > 2:
                return "youtube", row[2:]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed"}:
            return "youtube", parts[1]
    if "tiktok.com" in host and "video" in parts:
        index = parts.index("video")
        if len(parts) > index + 1:
            return "tiktok", parts[index + 1]
    if "instagram.com" in host and len(parts) >= 2 and parts[0] in {"p", "reel", "tv"}:
        return "instagram", parts[1]
    return None


def reconcile_serp_frontier_targets(
    *, frontier_result_path: Path, evidence_ledger_path: Path
) -> dict[str, Any]:
    """Link reviewed SERP recovery targets to exact already-captured native objects."""
    result = _load_json_object(frontier_result_path, label="SERP frontier result")
    if result.get("schema_version") != "phase_a_serp_source_frontier_review_result_v1":
        raise SemanticIntegrationError("SERP frontier result has wrong version")
    expected_hash = result.get("result_sha256")
    unhashed = dict(result)
    unhashed.pop("result_sha256", None)
    if expected_hash != _canonical_hash(unhashed):
        raise SemanticIntegrationError("SERP frontier result hash mismatch")
    ledger = _load_json_object(evidence_ledger_path, label="evidence depth ledger")
    captured: dict[tuple[str, str], dict[str, str]] = {}
    for row in ledger.get("target_reconciliation", []):
        if not isinstance(row, Mapping) or row.get("source_family") != "reddit_forum":
            continue
        key = _native_social_key(str(row.get("locator", "")))
        if key and _nonempty(row.get("native_artifact_id")):
            captured[key] = {
                "artifact_id": row["native_artifact_id"],
                "unit_id": str(row.get("target_id", "")).removeprefix("reddit_"),
            }
    families = ledger.get("families")
    native_social = families.get("native_social") if isinstance(families, Mapping) else None
    posts = native_social.get("posts") if isinstance(native_social, Mapping) else None
    if not isinstance(posts, list):
        raise SemanticIntegrationError("evidence ledger lacks native social posts")
    for row in posts:
        if not isinstance(row, Mapping) or not _nonempty(row.get("platform")) or not _nonempty(
            row.get("post_id")
        ) or not _nonempty(row.get("artifact_id")):
            raise SemanticIntegrationError("native social row has invalid identity")
        key = (row["platform"].casefold(), row["post_id"])
        candidate = {"artifact_id": row["artifact_id"], "unit_id": row.get("unit_id")}
        if key in captured and captured[key] != candidate:
            raise SemanticIntegrationError(f"native capture identity is ambiguous: {key}")
        captured[key] = candidate
    targets = result.get("locator_recovery_targets")
    if not isinstance(targets, list):
        raise SemanticIntegrationError("SERP frontier result lacks recovery targets")
    reconciled: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in targets:
        if not isinstance(row, Mapping) or not _nonempty(row.get("target_id")) or not _nonempty(
            row.get("locator")
        ):
            raise SemanticIntegrationError("SERP recovery target is invalid")
        if row["target_id"] in seen:
            raise SemanticIntegrationError("SERP recovery target is duplicated")
        seen.add(row["target_id"])
        key = _native_social_key(row["locator"])
        match = captured.get(key) if key else None
        reconciled.append(
            {
                "target_id": row["target_id"],
                "locator": row["locator"],
                "terminal_state": (
                    "already_captured" if match else "historical_capture_unavailable"
                ),
                "evidence_ref": match,
                "reason": (
                    "exact native object id is present in the frozen evidence ledger"
                    if match
                    else "no exact native object id match exists in the frozen evidence ledger"
                ),
            }
        )
    output = {
        "schema_version": "phase_a_serp_target_reconciliation_v1",
        "frontier_result_sha256": expected_hash,
        "evidence_ledger_sha256": hash_file(evidence_ledger_path),
        "targets": reconciled,
        "terminal_state_counts": {
            state: sum(row["terminal_state"] == state for row in reconciled)
            for state in ("already_captured", "historical_capture_unavailable")
        },
        "new_source_acquisition_performed": False,
        "model_api_calls": 0,
    }
    output["reconciliation_sha256"] = _canonical_hash(output)
    return output


def _load_seal(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SemanticIntegrationError(f"acquisition seal could not be read: {exc}") from exc
    for block in _YAML_FENCE.findall(text):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict) and isinstance(
            parsed.get("phase_acquisition_seal"), dict
        ):
            return parsed["phase_acquisition_seal"]
    raise SemanticIntegrationError("no phase_acquisition_seal YAML block found")


def _verify_v3_source_artifacts(
    source: Mapping[str, Any], *, repo_root: Path, binding_id: str
) -> None:
    artifacts = source.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise SemanticIntegrationError(
            f"source binding {binding_id} lacks source_artifacts"
        )
    for row in artifacts:
        if not isinstance(row, Mapping):
            raise SemanticIntegrationError(
                f"source binding {binding_id} has invalid source artifact"
            )
        locator = row.get("locator")
        expected = row.get("sha256")
        artifact_id = row.get("artifact_id")
        if not _nonempty(locator) or not _nonempty(expected) or not _nonempty(artifact_id):
            raise SemanticIntegrationError(
                f"source binding {binding_id} has incomplete source artifact"
            )
        try:
            path = _resolve(repo_root, locator)
        except OSError as exc:
            raise SemanticIntegrationError(
                f"source artifact {artifact_id} is unavailable: {exc}"
            ) from exc
        observed = hash_file(path)
        if observed != expected:
            raise SemanticIntegrationError(
                f"source artifact {artifact_id} hash mismatch: expected {expected}, observed {observed}"
            )


def _validate_run_spec_shape(spec: Mapping[str, Any]) -> None:
    if spec.get("schema_version") != RUN_SPEC_VERSION:
        raise SemanticIntegrationError("invalid Phase A semantic run spec version")
    for field in (
        "run_id",
        "cycle_id",
        "question_id",
        "question",
        "corpus_scope",
        "corpus_cutoff",
        "external_run_root",
    ):
        if not _nonempty(spec.get(field)):
            raise SemanticIntegrationError(f"run spec lacks {field}")
    if spec.get("corpus_profile") != "phase_a_final_acquisition":
        raise SemanticIntegrationError(
            "full-corpus run spec must use phase_a_final_acquisition"
        )
    ceiling = spec.get("max_prompt_bytes")
    if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling < 1_000:
        raise SemanticIntegrationError("run spec has invalid max_prompt_bytes")
    axes = spec.get("axes")
    if not isinstance(axes, list) or not axes:
        raise SemanticIntegrationError("run spec axes must be a non-empty list")
    axis_ids = [row.get("axis_id") for row in axes if isinstance(row, Mapping)]
    if (
        len(axis_ids) != len(axes)
        or any(not _nonempty(axis_id) for axis_id in axis_ids)
        or len(set(axis_ids)) != len(axis_ids)
    ):
        raise SemanticIntegrationError("run spec axes must have unique non-empty ids")


def audit_phase_a_source(
    spec: Mapping[str, Any], *, repo_root: Path
) -> dict[str, Any]:
    """Account for every sealed route before any semantic source can be materialized."""
    _validate_run_spec_shape(spec)
    seal_path = _verified_path(
        spec.get("acquisition_seal", {}),
        repo_root=repo_root,
        label="acquisition seal",
    )
    seal = _load_seal(seal_path)
    if seal.get("cycle_id") != spec["cycle_id"]:
        raise SemanticIntegrationError("run spec cycle does not match acquisition seal")
    route_rows = seal.get("route_job_accounting")
    if not isinstance(route_rows, list) or not route_rows:
        raise SemanticIntegrationError("acquisition seal lacks route_job_accounting")
    sealed_routes: dict[str, Mapping[str, Any]] = {}
    for row in route_rows:
        if not isinstance(row, Mapping) or not _nonempty(row.get("route_id")):
            raise SemanticIntegrationError("acquisition seal has invalid route row")
        route_id = row["route_id"]
        if route_id in sealed_routes:
            raise SemanticIntegrationError("acquisition seal has duplicate route id")
        planned = row.get("planned_job_ids")
        completed = row.get("completed_job_ids")
        blocked = row.get("blocked_job_ids")
        unrun = row.get("unrun_job_ids")
        if not all(isinstance(value, list) for value in (planned, completed, blocked, unrun)):
            raise SemanticIntegrationError(f"sealed route {route_id} has invalid job accounting")
        if set(planned) != set(completed) or blocked or unrun:
            raise SemanticIntegrationError(f"sealed route {route_id} is not fully completed")
        terminal = {
            "locator": row.get("terminal_artifact_locator"),
            "sha256": row.get("terminal_artifact_sha256"),
        }
        _verified_path(terminal, repo_root=repo_root, label=f"route {route_id} terminal")
        sealed_routes[route_id] = row

    bindings = spec.get("source_bindings")
    if not isinstance(bindings, list):
        raise SemanticIntegrationError("run spec source_bindings must be a list")
    binding_index: dict[str, Mapping[str, Any]] = {}
    verified_bindings: list[dict[str, Any]] = []
    for row in bindings:
        if not isinstance(row, Mapping) or not _nonempty(row.get("binding_id")):
            raise SemanticIntegrationError("run spec has invalid source binding")
        binding_id = row["binding_id"]
        if binding_id in binding_index:
            raise SemanticIntegrationError("run spec has duplicate source binding id")
        if row.get("adapter") != "semantic_evidence_source_v3":
            raise SemanticIntegrationError(
                f"source binding {binding_id} uses unsupported adapter"
            )
        path = _verified_path(row, repo_root=repo_root, label=f"source binding {binding_id}")
        source = _load_json_object(path, label=f"source binding {binding_id}")
        if source.get("schema_version") != "semantic_evidence_source_v3":
            raise SemanticIntegrationError(
                f"source binding {binding_id} is not semantic_evidence_source_v3"
            )
        if source.get("cycle_id") != spec["cycle_id"]:
            raise SemanticIntegrationError(
                f"source binding {binding_id} has a different cycle"
            )
        _verify_v3_source_artifacts(
            source, repo_root=repo_root, binding_id=binding_id
        )
        binding_index[binding_id] = row
        verified_bindings.append(
            {
                "binding_id": binding_id,
                "locator": row["locator"],
                "sha256": row["sha256"],
            }
        )

    classifications = spec.get("route_classifications")
    if not isinstance(classifications, list):
        raise SemanticIntegrationError("run spec route_classifications must be a list")
    classified: dict[str, Mapping[str, Any]] = {}
    blocked_routes: list[str] = []
    binding_users: dict[str, set[str]] = {binding_id: set() for binding_id in binding_index}
    for row in classifications:
        if not isinstance(row, Mapping) or not _nonempty(row.get("route_id")):
            raise SemanticIntegrationError("run spec has invalid route classification")
        route_id = row["route_id"]
        if route_id in classified:
            raise SemanticIntegrationError("run spec has duplicate route classification")
        disposition = row.get("disposition")
        if disposition not in ROUTE_DISPOSITIONS:
            raise SemanticIntegrationError(f"route {route_id} has invalid disposition")
        if not _nonempty(row.get("reason")):
            raise SemanticIntegrationError(f"route {route_id} lacks classification reason")
        row_bindings = row.get("binding_ids", [])
        if not isinstance(row_bindings, list) or any(
            binding_id not in binding_index for binding_id in row_bindings
        ):
            raise SemanticIntegrationError(f"route {route_id} cites unknown source binding")
        if disposition == "semantic_source" and not row_bindings:
            raise SemanticIntegrationError(f"semantic route {route_id} lacks a source binding")
        if disposition != "semantic_source" and row_bindings:
            raise SemanticIntegrationError(
                f"non-semantic route {route_id} cannot carry semantic source bindings"
            )
        if disposition == "duplicate_of":
            duplicate_of = row.get("duplicate_of")
            if duplicate_of not in sealed_routes or duplicate_of == route_id:
                raise SemanticIntegrationError(f"route {route_id} has invalid duplicate_of")
        if disposition == "blocked":
            blocked_routes.append(route_id)
        for binding_id in row_bindings:
            binding_users[binding_id].add(route_id)
        classified[route_id] = row

    if set(classified) != set(sealed_routes):
        missing = sorted(set(sealed_routes) - set(classified))
        extra = sorted(set(classified) - set(sealed_routes))
        raise SemanticIntegrationError(
            f"route classifications do not match sealed routes; missing={missing}, extra={extra}"
        )
    # Checked after the equality above so every duplicate target is classified.
    # Duplicating a discovery, control, or duplicate route would let a route
    # that actually captured a corpus donate nothing while the audit still
    # reported a complete run.
    for route_id, row in sorted(classified.items()):
        if row["disposition"] != "duplicate_of":
            continue
        owner = row["duplicate_of"]
        if classified[owner]["disposition"] not in EVIDENCE_OWNING_DISPOSITIONS:
            raise SemanticIntegrationError(
                f"route {route_id} duplicates {owner}, which owns no evidence"
            )
    unused = sorted(binding_id for binding_id, users in binding_users.items() if not users)
    if unused:
        raise SemanticIntegrationError(f"source bindings are not attached to semantic routes: {unused}")

    audit = {
        "schema_version": AUDIT_VERSION,
        "run_id": spec["run_id"],
        "cycle_id": spec["cycle_id"],
        "acquisition_seal": dict(spec["acquisition_seal"]),
        "sealed_route_count": len(sealed_routes),
        "route_disposition_counts": {
            disposition: sum(
                row["disposition"] == disposition for row in classifications
            )
            for disposition in sorted(ROUTE_DISPOSITIONS)
        },
        "verified_source_bindings": sorted(
            verified_bindings, key=lambda row: row["binding_id"]
        ),
        "blocked_routes": sorted(blocked_routes),
        "complete": not blocked_routes,
    }
    audit["audit_sha256"] = _canonical_hash(audit)
    return audit


def materialize_phase_a_v3(
    spec: Mapping[str, Any], *, repo_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge all audited v3 fragments into one immutable final-acquisition source."""
    audit = audit_phase_a_source(spec, repo_root=repo_root)
    if audit["complete"] is not True:
        raise SemanticIntegrationError("blocked source route prevents full-corpus materialization")
    artifacts: dict[str, dict[str, Any]] = {}
    containers: dict[str, dict[str, Any]] = {}
    captured_items: dict[str, dict[str, Any]] = {}
    for binding in spec["source_bindings"]:
        path = _resolve(repo_root, binding["locator"])
        fragment = _load_json_object(path, label=f"source binding {binding['binding_id']}")
        if fragment.get("cycle_id") != spec["cycle_id"]:
            raise SemanticIntegrationError(
                f"source binding {binding['binding_id']} has a different cycle"
            )
        for field, index, key in (
            ("source_artifacts", artifacts, "artifact_id"),
            ("containers", containers, "container_id"),
            ("captured_items", captured_items, "evidence_id"),
        ):
            rows = fragment.get(field)
            if not isinstance(rows, list):
                raise SemanticIntegrationError(
                    f"source binding {binding['binding_id']} lacks {field}"
                )
            for row in rows:
                if not isinstance(row, dict) or not _nonempty(row.get(key)):
                    raise SemanticIntegrationError(f"invalid {field} row in source binding")
                row_id = row[key]
                if row_id in index and index[row_id] != row:
                    raise SemanticIntegrationError(
                        f"conflicting duplicate {key} across source bindings: {row_id}"
                    )
                index[row_id] = dict(row)
    source = {
        "schema_version": "semantic_evidence_source_v3",
        "cycle_id": spec["cycle_id"],
        "question_id": spec["question_id"],
        "question": spec["question"],
        "corpus_profile": spec["corpus_profile"],
        "corpus_scope": spec["corpus_scope"],
        "corpus_cutoff": spec["corpus_cutoff"],
        "axes": list(spec["axes"]),
        "source_artifacts": sorted(artifacts.values(), key=lambda row: row["artifact_id"]),
        "containers": sorted(containers.values(), key=lambda row: row["container_id"]),
        "captured_items": sorted(
            captured_items.values(), key=lambda row: row["evidence_id"]
        ),
    }
    materialized = materialize_source_v3(source)
    receipt = {
        "schema_version": RUN_RECEIPT_VERSION,
        "run_id": spec["run_id"],
        "cycle_id": spec["cycle_id"],
        "run_spec_sha256": _canonical_hash(spec),
        "source_audit_sha256": audit["audit_sha256"],
        "source_sha256": materialized["source_sha256"],
        "captured_item_count": len(materialized["captured_items"]),
        "captured_container_count": len(materialized["containers"]),
        "source_artifact_count": len(materialized["source_artifacts"]),
        "historical_seal_restamped": False,
        "model_api_calls": 0,
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    return materialized, receipt


def validate_one_batch_response(
    bundle: Mapping[str, Any], response: Mapping[str, Any]
) -> dict[str, Any]:
    return validate_batch_responses(bundle, [response], require_all=False)


def validate_one_reconciliation_response(
    bundle: Mapping[str, Any],
    stage: Mapping[str, Any],
    response: Mapping[str, Any],
) -> dict[str, Any]:
    return validate_reconciliation_stage(
        bundle, stage, [response], require_all=False
    )


def run_status(
    *,
    bundle: Mapping[str, Any],
    batch_responses: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return honest resumability status without compiling a partial result."""
    expected = {row["batch_id"] for row in bundle.get("batches", [])}
    valid: set[str] = set()
    invalid: list[dict[str, str]] = []
    duplicates: set[str] = set()
    for response in batch_responses:
        batch_id = response.get("batch_id") if isinstance(response, Mapping) else None
        if isinstance(batch_id, str) and batch_id in valid:
            duplicates.add(batch_id)
            continue
        try:
            receipt = validate_one_batch_response(bundle, response)
        except SemanticIntegrationError as exc:
            invalid.append({"batch_id": str(batch_id), "error": str(exc)})
            continue
        valid.update(receipt["validated_batch_ids"])
    complete = valid == expected and not invalid and not duplicates
    return {
        "schema_version": "phase_a_semantic_run_status_v1",
        "bundle_sha256": bundle.get("bundle_sha256"),
        "expected_batch_count": len(expected),
        "valid_batch_count": len(valid),
        "missing_batch_ids": sorted(expected - valid),
        "duplicate_batch_ids": sorted(duplicates),
        "invalid_responses": invalid,
        "batch_stage_complete": complete,
        "next_status": (
            "SEMANTIC_BATCH_COMPILATION_READY"
            if complete
            else "SEMANTIC_BATCH_JUDGMENT_REQUIRED"
        ),
        "model_api_calls": 0,
    }


__all__ = [
    "AUDIT_VERSION",
    "CORPUS_CENSUS_VERSION",
    "RUN_RECEIPT_VERSION",
    "RUN_SPEC_VERSION",
    "audit_phase_a_source",
    "census_phase_a_customer_corpus",
    "materialize_phase_a_v3",
    "run_status",
    "validate_one_batch_response",
    "validate_one_reconciliation_response",
]
