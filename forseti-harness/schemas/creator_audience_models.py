"""Media-neutral creator-audience Judgment contracts."""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Literal

from pydantic import Field, field_validator, model_validator

from schemas.case_models import StrictModel
from schemas.tiktok_audience_evidence_models import AudienceClaimAxis


class CreatorAudienceSemanticClaim(StrictModel):
    claim_key: str
    axis: AudienceClaimAxis
    statement: str
    commercial_implication: str
    relation: Literal[
        "agreement", "contradiction", "audience_emergent", "creator_only", "missing"
    ]
    representative_evidence_aliases: list[str] = Field(max_length=5)
    all_support_evidence_aliases: list[str]
    counterevidence_aliases: list[str] = []
    limitation: str | None = None
    engagement_salience_relied_on: bool = False

    @field_validator("claim_key", "statement", "commercial_implication")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("semantic claim text must be non-blank")
        return value.strip()


class CreatorAudienceSemanticProjectionPoint(StrictModel):
    statement: str
    claim_keys: list[str] = Field(min_length=1)

    @field_validator("statement")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("projection statement must be non-blank")
        return value.strip()


class CreatorAudienceSemanticProjection(StrictModel):
    hire_verdict: CreatorAudienceSemanticProjectionPoint
    product_advantage: CreatorAudienceSemanticProjectionPoint
    creator_specific_execution: CreatorAudienceSemanticProjectionPoint
    observed_audience_response: CreatorAudienceSemanticProjectionPoint
    strongest_campaign_jobs: list[CreatorAudienceSemanticProjectionPoint] = Field(
        min_length=1
    )
    briefing_instructions: list[CreatorAudienceSemanticProjectionPoint] = Field(
        min_length=1
    )
    wrong_hire_boundary: CreatorAudienceSemanticProjectionPoint
    robustness_stamp: str | None = None


class CreatorAudienceSemanticResponse(StrictModel):
    schema_version: Literal["creator_audience_semantic_response_v1"]
    generated_at: str
    claims: list[CreatorAudienceSemanticClaim] = Field(min_length=1)
    creator_signal_projection: CreatorAudienceSemanticProjection
    limitations: list[str]
    non_claims: list[str]
    actual_audience_demographics: Literal["not_estimated"] = "not_estimated"


class CreatorAudienceClaimV1(StrictModel):
    claim_id: str
    axis: AudienceClaimAxis
    statement: str
    commercial_implication: str
    modality: Literal[
        "creator_content", "observed_comments", "engagement_elevated", "fused"
    ]
    relation: Literal[
        "agreement", "contradiction", "audience_emergent", "creator_only", "missing"
    ]
    support_scope: Literal[
        "single_comment", "single_item", "multi_item", "content_only", "mixed_multi_item"
    ]
    representative_evidence_ids: list[str] = Field(max_length=5)
    all_support_evidence_ids: list[str]
    counterevidence_ids: list[str] = []
    source_item_ids: list[str]
    limitation: str | None = None

    @model_validator(mode="after")
    def evidence_presence_matches_relation(self) -> "CreatorAudienceClaimV1":
        evidence_lists = (
            self.representative_evidence_ids,
            self.all_support_evidence_ids,
            self.counterevidence_ids,
            self.source_item_ids,
        )
        if self.relation == "missing":
            if any(evidence_lists):
                raise ValueError("missing claims must not cite evidence or source items")
        elif (
            not self.representative_evidence_ids
            or not self.all_support_evidence_ids
            or not self.source_item_ids
        ):
            raise ValueError(
                "non-missing claims require representative, support, and source-item evidence"
            )
        return self


class CreatorAudienceProjectionPointV1(StrictModel):
    statement: str
    claim_ids: list[str] = Field(min_length=1)


class CreatorAudienceClaimSetV1(StrictModel):
    claims: list[CreatorAudienceClaimV1] = Field(min_length=1)
    agreements: list[str]
    contradictions: list[str]
    missing_evidence: list[str]


class CreatorSignalProjectionV1(StrictModel):
    hire_verdict: CreatorAudienceProjectionPointV1
    product_advantage: CreatorAudienceProjectionPointV1
    creator_specific_execution: CreatorAudienceProjectionPointV1
    observed_audience_response: CreatorAudienceProjectionPointV1
    strongest_campaign_jobs: list[CreatorAudienceProjectionPointV1] = Field(min_length=1)
    briefing_instructions: list[CreatorAudienceProjectionPointV1] = Field(min_length=1)
    wrong_hire_boundary: CreatorAudienceProjectionPointV1
    robustness_stamp: str | None = None


class CreatorAudienceTriangulationSnapshotV1(StrictModel):
    schema_version: Literal["creator_audience_triangulation_snapshot_v1"]
    snapshot_id: str
    profile_subject_kind: Literal["platform_account"]
    profile_subject_id: str
    platform_account_id: str
    creator_id: str
    platform_scope: Literal["tiktok", "instagram", "youtube"]
    generated_at: str
    evidence_cutoff: str
    input_bundle_id: str
    input_bundle_hash: str
    method_deck_path: str
    method_deck_sha256: str
    judgment_claim_set: CreatorAudienceClaimSetV1
    creator_signal_projection: CreatorSignalProjectionV1
    limitations: list[str]
    non_claims: list[str]
    actual_audience_demographics: Literal["not_estimated"] = "not_estimated"

    @field_validator(
        "snapshot_id",
        "profile_subject_id",
        "platform_account_id",
        "creator_id",
        "generated_at",
        "evidence_cutoff",
        "input_bundle_id",
        "input_bundle_hash",
        "method_deck_path",
        "method_deck_sha256",
    )
    @classmethod
    def snapshot_text_non_blank(cls, value: str) -> str:
        # Reject-only (no strip): the compiler owns canonical bytes, and a
        # transforming validator would desynchronize snapshot_id from content.
        if not value.strip():
            raise ValueError("snapshot field must be non-blank")
        return value


class CreatorAudienceJudgmentOutcomeV1(StrictModel):
    schema_version: Literal["creator_audience_judgment_outcome_v1"]
    record_id: str
    raw_anchor: str
    creator_id: str
    profile_subject_id: str
    bundle_id: str
    bundle_hash: str
    status: Literal["validated", "blocked"]
    response_sha256: str
    response_size_bytes: int
    response_bytes_b64: str
    validation_errors: list[str]
    snapshot_id_or_none: str | None
    snapshot_sha256_or_none: str | None
    snapshot_or_none: CreatorAudienceTriangulationSnapshotV1 | None
    model_api_calls: Literal[0] = 0

    @model_validator(mode="after")
    def outcome_consistency(self) -> "CreatorAudienceJudgmentOutcomeV1":
        response_bytes = base64.b64decode(self.response_bytes_b64, validate=True)
        if len(response_bytes) != self.response_size_bytes:
            raise ValueError("Judgment outcome response size does not match exact bytes")
        if f"sha256:{hashlib.sha256(response_bytes).hexdigest()}" != self.response_sha256:
            raise ValueError("Judgment outcome response hash does not match exact bytes")
        if self.status == "validated":
            if (
                self.validation_errors
                or self.snapshot_or_none is None
                or not self.snapshot_id_or_none
                or not self.snapshot_sha256_or_none
            ):
                raise ValueError("validated Judgment outcome requires one clean snapshot")
            snapshot_bytes = (
                json.dumps(
                    self.snapshot_or_none.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
            if self.snapshot_or_none.snapshot_id != self.snapshot_id_or_none:
                raise ValueError("Judgment outcome snapshot_id does not match snapshot")
            if (
                f"sha256:{hashlib.sha256(snapshot_bytes).hexdigest()}"
                != self.snapshot_sha256_or_none
            ):
                raise ValueError("Judgment outcome snapshot hash does not match snapshot")
        elif (
            not self.validation_errors
            or self.snapshot_or_none is not None
            or self.snapshot_id_or_none is not None
            or self.snapshot_sha256_or_none is not None
        ):
            raise ValueError("blocked Judgment outcome requires errors and no snapshot")
        return self


__all__ = [
    "CreatorAudienceJudgmentOutcomeV1",
    "CreatorAudienceSemanticResponse",
    "CreatorAudienceTriangulationSnapshotV1",
]
