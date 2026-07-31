"""Retention decision for a rendered (DOM + visible text) capture.

Single home for the rule the Reddit lane binds as **never raw-only** (owner
direction, 2026-07-31): a rendered capture publishes a content record, and raw
survives only as evidence alongside it or as a fail-loud fallback.

This module owns the DECISION and its provenance, not artifact staging. Each
runner keeps its own staging, because the artifact names and packet assembly
differ per surface; what must not differ is which outcome a given situation
produces and what provenance survives when raw is dropped.

Four outcomes, and the distinction that matters is CHOSEN raw versus
FALLEN-BACK-TO raw:

``content``      extraction succeeded; raw hashed then dropped.
``raw_sample``   extraction succeeded AND raw kept as an audit sample. Content
                 is still published, so this is not raw-only.
``raw_failure``  extraction or admission failed; raw preserved so the failure is
                 diagnosable. Removing this would not achieve never-raw-only --
                 it would produce a blocked capture that preserves nothing and
                 reports nothing, which is the fake-success path the doctrine
                 exists to prevent.
``raw``          no extraction was configured. Callers that bind never-raw-only
                 must refuse this at their boundary; see
                 ``require_content_retention``.

Provenance is never dropped: when raw inputs are discarded, their sha256 and
byte counts, the extractor version, and the content-record hash remain packet
evidence, so a later reader can prove what was released.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from source_capture.content_extraction import RenderedContentExtractionSpec

RETENTION_OUTCOMES = ("content", "raw_sample", "raw_failure", "raw")


class RenderedRetentionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RenderedRetentionDecision:
    retention_outcome: str
    content_record_bytes: bytes | None
    extraction_failure_or_none: str | None
    raw_inputs_preserved: bool
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def carries_content(self) -> bool:
        return self.content_record_bytes is not None


def _digest(body: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(body).hexdigest(), "byte_count": len(body)}


def require_content_retention(
    spec: RenderedContentExtractionSpec | None, *, lane: str
) -> RenderedContentExtractionSpec:
    """Refuse a raw-only capture at a lane boundary that binds never-raw-only.

    Enforced rather than merely enabled: a lane that only *offers* content mode
    still publishes raw the moment a caller omits the spec.
    """
    if spec is None:
        raise RenderedRetentionError(
            "content_extraction_required",
            f"{lane} binds never-raw-only; a content extraction spec is required",
        )
    if spec.requested_retention_mode != "content":
        raise RenderedRetentionError(
            "raw_only_retention_refused",
            f"{lane} binds never-raw-only; refusing retention mode "
            f"{spec.requested_retention_mode!r}",
        )
    return spec


def resolve_rendered_retention(
    *,
    spec: RenderedContentExtractionSpec | None,
    rendered_dom: bytes,
    visible_text: bytes,
    final_url: str,
    admission_failed: bool,
    keep_raw_audit_sample: bool = False,
) -> RenderedRetentionDecision:
    """Classify one rendered capture's retention outcome and provenance.

    This generic classifier still represents the ``raw`` outcome. A lane that
    binds never-raw-only must call ``require_content_retention`` at its capture
    boundary before calling this function; classification alone is not
    enforcement.

    ``admission_failed`` folds every reason the packet must not be admitted as
    clean source content (access block, sufficiency failure). It forces raw
    preservation even when extraction itself succeeded, because a projection
    over a block shell is a well-formed record of the wrong thing.
    """
    inputs_provenance = {
        "rendered_dom": _digest(rendered_dom),
        "visible_text": _digest(visible_text),
    }

    if spec is None:
        return RenderedRetentionDecision(
            retention_outcome="raw",
            content_record_bytes=None,
            extraction_failure_or_none=None,
            raw_inputs_preserved=True,
            provenance={"extraction": "not_configured", "inputs": inputs_provenance},
        )

    if spec.requested_retention_mode != "content":
        return RenderedRetentionDecision(
            retention_outcome="raw",
            content_record_bytes=None,
            extraction_failure_or_none=None,
            raw_inputs_preserved=True,
            provenance={
                "extraction": "not_attempted: raw retention requested",
                "inputs": inputs_provenance,
            },
        )

    content_record_bytes: bytes | None = None
    extraction_failure: str | None = None
    try:
        record = spec.extractor(rendered_dom, visible_text, final_url)
        if not isinstance(record, dict):
            raise TypeError(
                "rendered content extractor must return a JSON object, "
                f"got {type(record).__name__}"
            )
        options: dict[str, Any] = {"sort_keys": True, "ensure_ascii": False}
        if spec.json_indent is None:
            options["separators"] = (",", ":")
        else:
            options["indent"] = spec.json_indent
        content_record_bytes = (json.dumps(record, **options) + "\n").encode("utf-8")
    except Exception as exc:  # extraction is caller code; any failure is fail-loud
        extraction_failure = f"{type(exc).__name__}: {exc}"

    failed = extraction_failure is not None or admission_failed
    if failed:
        outcome = "raw_failure"
    elif keep_raw_audit_sample:
        outcome = "raw_sample"
    else:
        outcome = "content"

    provenance: dict[str, Any] = {
        "extractor_version": spec.extractor_version,
        "extraction": "failed: " + extraction_failure if extraction_failure else "succeeded",
        "admission_failed": admission_failed,
    }
    if content_record_bytes is not None:
        provenance["content_record"] = _digest(content_record_bytes)
    if outcome == "content":
        # Raw is released here, so its provenance is the only remaining proof of
        # what was extracted from.
        provenance["discarded_inputs"] = inputs_provenance
    else:
        provenance["inputs"] = inputs_provenance

    # A successful extraction over a failed admission is a well-formed record of
    # the WRONG thing -- a projection of a block shell or an insufficient page.
    # Its hash stays in provenance so the attempt is auditable, but the record
    # itself is withheld rather than shipped inside a packet that must not be
    # admitted.
    admitted_record = None if failed else content_record_bytes
    if failed and content_record_bytes is not None:
        provenance["content_record_withheld"] = "extracted but not admitted"

    return RenderedRetentionDecision(
        retention_outcome=outcome,
        content_record_bytes=admitted_record,
        extraction_failure_or_none=extraction_failure,
        raw_inputs_preserved=outcome != "content",
        provenance=provenance,
    )


__all__ = [
    "RETENTION_OUTCOMES",
    "RenderedRetentionDecision",
    "RenderedRetentionError",
    "require_content_retention",
    "resolve_rendered_retention",
]
