"""Reusable, fail-closed control plane for a full-corpus Phase A semantic run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

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
ROUTE_DISPOSITIONS = {
    "evidence_source",
    "discovery_only",
    "control_only",
    "duplicate_of",
    "blocked",
}
_YAML_FENCE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_TEXT_ARTIFACT_SUFFIXES = {".json", ".md", ".yaml", ".yml"}


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
        if lowered.endswith("content_record.json"):
            content_candidates.append(path)
        elif lowered.endswith(("http_response_body.bin", ".html", ".htm")):
            html_candidates.append(path)
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


def census_phase_a_customer_corpus(
    *, evidence_ledger_path: Path, retailer_coding_path: Path
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
        if (
            not isinstance(row, Mapping)
            or row.get("source_family") != "reddit_forum"
            or not _nonempty(row.get("native_artifact_id"))
        ):
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
    review_keys: set[tuple[str, str]] = set()
    source_files: dict[str, str] = {}
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
        body = source_files.get(source_key)
        if body is None:
            body = source_path.read_text(encoding="utf-8-sig")
            source_files[source_key] = body
        if review_id not in body:
            raise SemanticIntegrationError(
                f"retailer review {review_id} is absent from its pinned source file"
            )
    eligible_by_corpus = {
        row.get("corpus_id"): row.get("eligible_text_review_count")
        for row in corpora
        if isinstance(row, Mapping)
    }
    excluded_by_corpus = {
        row.get("corpus_id"): row.get("excluded_no_usable_text_count")
        for row in corpora
        if isinstance(row, Mapping)
    }
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
        if disposition == "evidence_source" and not row_bindings:
            raise SemanticIntegrationError(f"evidence route {route_id} lacks a source binding")
        if disposition != "evidence_source" and row_bindings:
            raise SemanticIntegrationError(
                f"non-evidence route {route_id} cannot carry source bindings"
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
    unused = sorted(binding_id for binding_id, users in binding_users.items() if not users)
    if unused:
        raise SemanticIntegrationError(f"source bindings are not attached to evidence routes: {unused}")

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
