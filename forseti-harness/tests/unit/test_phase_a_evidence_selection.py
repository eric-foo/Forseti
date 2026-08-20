from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from judgment.phase_a_evidence_consumer import EvidenceConsumerError
from judgment.phase_a_evidence_selection import (
    BATCHED_QUOTE_MANIFEST_VERSION,
    DISPLAY_LABEL_BY_REASON_CODE,
    SELECTION_SPEC_VERSION,
    VALUE_REASON_RELATIONS,
    _candidate_rows,
    _bucket_priority,
    _display_label,
    _numeric_engagement,
    _policy_guidance,
    _relation_schema,
    _select_groups,
    _source_venue,
    _validate_relation_response,
    finalize_batched_relations_prepare_quotes,
    finalize_quotes,
    finalize_relations_prepare_quotes,
    prepare_evidence_selection,
    prepare_evidence_selection_batches,
)
from runners.run_semantic_evidence_integration import (
    finalize_evidence_selection_batches_run,
    finalize_evidence_selection_quotes_run,
    finalize_evidence_selection_relations_run,
    prepare_evidence_selection_batches_run,
    prepare_evidence_selection_run,
)


def _canonical_hash(value: object) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _packet_and_bundle(count: int = 14) -> tuple[dict, dict]:
    semantic_columns = [
        "semantic_unit_ref",
        "statement",
        "evidence_posture",
        "uncertainty_posture",
        "polarity",
        "subject_product_ids",
        "product_version_ids",
        "axis_ids",
        "conditions",
        "emerging_axis_labels",
    ]
    evidence_columns = [
        "evidence_id",
        "source_artifact_id",
        "source_ref",
        "container_id",
        "publication_time",
        "actor_identity",
        "independence_posture",
        "independence_key",
        "public_identity_key",
        "engagement",
        "semantic_units",
    ]
    groups = []
    bundle_units = []
    roles = [
        ("reddit_community", "community_post", "score_state", "reddit.com"),
        ("retailer_review", "retailer_review", "positive_helpful_count", "sephora.com"),
        ("retailer_review", "retailer_review", "positive_helpful_count", "amazon.com"),
        ("creator_social", "audience_comment", "comment_diggs", "tiktok.com"),
        ("creator_social", "creator_authored", "video_diggs", "tiktok.com"),
    ]
    rows_by_role: dict[tuple[str, str, str, str], list[list]] = {role: [] for role in roles}
    unmerged = []
    for index in range(count):
        role = roles[index % len(roles)]
        family, source_role, _, domain = role
        evidence_id = f"{source_role}:{index}"
        semantic_ref = f"{evidence_id}::hydration"
        condition = ["after use"] if index % 4 else ["overnight"]
        statement = (
            f"Customer report {index} says the balm feels moisturizing."
            if source_role != "creator_authored"
            else f"Creator post {index} presents the balm as moisturizing."
        )
        engagement = [
            "engagement_available",
            f"{100-index} points" if source_role == "community_post" else 100 - index,
            "2026-08-18T00:00:00Z",
            index % 3 != 0,
        ]
        semantic = [
            semantic_ref,
            statement,
            "first_hand" if source_role != "creator_authored" else "creator_claim",
            "asserted",
            "affirmed",
            ["summer-fridays-lip-butter-balm"],
            [],
            "hydration_and_moisture texture_and_skin_finish" if index == 0 else ["hydration_and_moisture"],
            condition,
            [],
        ]
        row = [
            evidence_id,
            f"artifact:{index}",
            f"https://{domain}/evidence/{index}",
            f"container:{index}",
            "2026-08-17T00:00:00Z",
            f"actor:{index}",
            "credited",
            f"origin:{index}",
            f"public:{index}",
            engagement,
            [semantic],
        ]
        rows_by_role[role].append(row)
        unmerged.append({"evidence_id": evidence_id, "semantic_unit_ref": semantic_ref, "reason": "retained"})
        bundle_units.append(
            {
                "evidence_id": evidence_id,
                "source_artifact_id": f"artifact:{index}",
                "source_ref": f"https://{domain}/evidence/{index}",
                "text": f"Opening context. This balm feels moisturizing after use number {index}. Closing context.",
            }
        )
    for (family, source_role, engagement_kind, _), rows in rows_by_role.items():
        if not rows:
            continue
        groups.append(
            {
                "source_family": family,
                "source_role": source_role,
                "engagement_kind": engagement_kind,
                "engagement_context": "source-native metric",
                "evidence_defaults": {},
                "evidence_columns": evidence_columns,
                "engagement_defaults": {},
                "engagement_columns": ["status", "raw_value", "observed_at", "material_positive"],
                "evidence_rows": rows,
            }
        )
    bundle = {
        "schema_version": "semantic_evidence_bundle_v5",
        "evidence_units": bundle_units,
    }
    bundle["bundle_sha256"] = _canonical_hash(bundle)
    packet = {
        "schema_version": "phase_a_evidence_packet_v3",
        "selection": {"mode": "axis", "axis_ids": ["hydration_and_moisture"], "proposition_ids": []},
        "source_bindings": {"bundle_sha256": bundle["bundle_sha256"], "corpus_sha256": "c" * 64},
        "catalogue_schema": {
            "semantic_unit_defaults": {},
            "semantic_unit_columns": semantic_columns,
            "relation_link_columns": ["evidence_id", "semantic_unit_refs"],
        },
        "propositions": [],
        "source_groups": groups,
        "containers": [],
        "unmerged_axis_candidates": unmerged,
        "unscoped_unmerged_candidates": [],
        "unresolved_axis_candidates": [],
        "full_evidence_resolution": {"bundle_sha256": bundle["bundle_sha256"], "body_field": "text"},
        "model_api_calls": 0,
    }
    packet["packet_sha256"] = _canonical_hash(packet)
    return packet, bundle


def _spec(count: int = 14) -> dict:
    # Nominate only evidence the fixture actually emits: an unresolvable
    # nomination is now a closed boundary, not a silently ignored line.
    protected: dict[str, list[str]] = {"safety": ["community_post:0"]}
    if count > 6:
        protected["costly_behavior"] = ["retailer_review:6"]
    return {
        "schema_version": SELECTION_SPEC_VERSION,
        "selection_id": "hydration-pilot",
        "bounded_claim": "Customers report hydration experiences with the balm.",
        "axis_ids": ["hydration_and_moisture"],
        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
        "sources": [],
        "protected_evidence_ids": protected,
    }


def _write_source(tmp_path: Path, count: int = 14) -> tuple[dict, list[dict]]:
    packet, bundle = _packet_and_bundle(count)
    packet_path = tmp_path / "packet.json"
    bundle_path = tmp_path / "bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    source = {
        "source_id": "full-corpus",
        "packet_path": packet_path,
        "bundle_path": bundle_path,
        "packet": packet,
        "bundle": bundle,
    }
    return _spec(count), [source]


def _reseal(source: dict) -> None:
    """Re-hash a source after an intentional body edit, then rewrite both files."""
    bundle = source["bundle"]
    bundle.pop("bundle_sha256", None)
    bundle["bundle_sha256"] = _canonical_hash(bundle)
    packet = source["packet"]
    packet["source_bindings"]["bundle_sha256"] = bundle["bundle_sha256"]
    packet["full_evidence_resolution"]["bundle_sha256"] = bundle["bundle_sha256"]
    packet.pop("packet_sha256", None)
    packet["packet_sha256"] = _canonical_hash(packet)
    source["packet_path"].write_text(json.dumps(packet), encoding="utf-8")
    source["bundle_path"].write_text(json.dumps(bundle), encoding="utf-8")


def _relation_response(candidates: list[dict]) -> dict:
    rows = []
    for index, candidate in enumerate(candidates):
        if candidate["layer"] == "influence_context":
            relation = "adjacent"
        elif index % 4 == 0:
            relation = "counter"
        else:
            relation = "support"
        rows.append({"candidate_id": candidate["candidate_id"], "relation": relation, "reason_code": "bounded_meaning"})
    return {"results": rows}


def _positional_relation_response(candidates: list[dict]) -> dict:
    literal = _relation_response(candidates)["results"]
    return {
        "results_by_candidate_row": {
            f"row_{index:04d}": row["relation"]
            for index, row in enumerate(literal)
        }
    }


def _batched_positional_relation_response(candidates: list[dict], batch_id: str) -> dict:
    return {**_positional_relation_response(candidates), "batch_id": batch_id}


def test_missing_packet_publication_time_is_rehydrated_from_hash_bound_reddit_source(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, count=1)
    source = sources[0]
    packet = source["packet"]
    bundle = source["bundle"]
    evidence_columns = packet["source_groups"][0]["evidence_columns"]
    evidence_row = packet["source_groups"][0]["evidence_rows"][0]
    semantic_columns = packet["catalogue_schema"]["semantic_unit_columns"]
    semantic_row = evidence_row[evidence_columns.index("semantic_units")][0]
    old_ref = semantic_row[semantic_columns.index("semantic_unit_ref")]
    new_evidence_id = "reddit:abc:post"
    new_semantic_ref = "reddit:abc:post::hydration"
    evidence_row[evidence_columns.index("evidence_id")] = new_evidence_id
    evidence_row[evidence_columns.index("source_artifact_id")] = "reddit_source_abc"
    evidence_row[evidence_columns.index("source_ref")] = (
        "https://www.reddit.com/r/test/comments/abc/example/"
    )
    evidence_row[evidence_columns.index("publication_time")] = None
    semantic_row[semantic_columns.index("semantic_unit_ref")] = new_semantic_ref
    packet["unmerged_axis_candidates"][0]["evidence_id"] = new_evidence_id
    packet["unmerged_axis_candidates"][0]["semantic_unit_ref"] = new_semantic_ref
    raw_path = tmp_path / "reddit_content_record.json"
    raw_path.write_text(
        json.dumps(
            {
                "post": {
                    "body_text": "This balm feels moisturizing after use number 0.",
                    "timestamp_state": "2026-07-29T08:17:00+0000",
                },
                "comments": [],
            }
        ),
        encoding="utf-8",
    )
    bundle["evidence_units"][0].update(
        {
            "evidence_id": new_evidence_id,
            "source_artifact_id": "reddit_source_abc",
            "source_ref": "https://www.reddit.com/r/test/comments/abc/example/",
        }
    )
    bundle["source_artifacts"] = [
        {
            "artifact_id": "reddit_source_abc",
            "locator": str(raw_path),
            "sha256": __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest(),
        }
    ]
    spec["protected_evidence_ids"] = {"safety": [new_evidence_id]}
    assert old_ref != new_semantic_ref
    _reseal(source)

    candidates = _candidate_rows(sources, spec)

    assert candidates[0]["publication_time"] == "2026-07-29T08:17:00+0000"
    raw_path.write_text("{}", encoding="utf-8")
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "publication_time_source_hash"


def test_hash_bound_unsupported_source_format_leaves_publication_time_unavailable(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, count=1)
    source = sources[0]
    packet = source["packet"]
    bundle = source["bundle"]
    evidence_columns = packet["source_groups"][0]["evidence_columns"]
    evidence_row = packet["source_groups"][0]["evidence_rows"][0]
    evidence_id = evidence_row[evidence_columns.index("evidence_id")]
    evidence_row[evidence_columns.index("publication_time")] = None
    evidence_row[evidence_columns.index("source_artifact_id")] = "legacy_binary_source"
    raw_path = tmp_path / "legacy_response.bin"
    raw_path.write_bytes(b"not a supported JSON source artifact")
    bundle["evidence_units"][0]["source_artifact_id"] = "legacy_binary_source"
    bundle["source_artifacts"] = [
        {
            "artifact_id": "legacy_binary_source",
            "locator": str(raw_path),
            "sha256": __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest(),
        }
    ]
    _reseal(source)

    candidates = _candidate_rows(sources, spec)

    assert next(row for row in candidates if row["evidence_id"] == evidence_id)[
        "publication_time"
    ] is None


def _quote_response(quote_manifest: dict, sources: list[dict]) -> dict:
    bodies = {
        row["evidence_id"]: row["text"]
        for row in sources[0]["bundle"]["evidence_units"]
    }
    provider_ids = set(
        quote_manifest.get(
            "provider_selected_ids",
            [row["selected_id"] for row in quote_manifest["selected_rows"]],
        )
    )
    return {
        "quotes": [
            {
                "selected_id": row["selected_id"],
                "quote_status": "quote_available",
                "exact_quote": bodies[row["evidence_id"]][:220],
            }
            for row in quote_manifest["selected_rows"]
            if row["selected_id"] in provider_ids
        ]
    }


def test_selection_round_trip_accounts_every_candidate_separates_creator_and_caps_origins(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path)
    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    relation_response = _relation_response(candidates)

    quote_prompt, quote_schema, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, relation_response
    )
    artifact = finalize_quotes(quote_manifest, sources, _quote_response(quote_manifest, sources))

    assert len(candidates) == 14
    assert artifact["candidate_count"] == 14
    assert len(artifact["candidate_dispositions"]) == 14
    assert artifact["truth_group_count"] <= 10
    assert artifact["influence_group_count"] <= 3
    assert all(
        row["relation"] == "adjacent"
        for group in artifact["source_groups"]
        for row in group["rows"]
        if row["layer"] == "influence_context"
    )
    assert any(group["group_key"].endswith("::amazon") for group in artifact["source_groups"])
    assert "every candidate_id exactly once" in prompt
    assert "contiguous exact substring" in quote_prompt
    assert schema["required"] == ["results"]
    assert quote_schema["required"] == ["quotes"]


def test_selection_spec_can_raise_truth_origin_cap_to_twenty_without_changing_influence_cap(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 40)
    spec["truth_group_cap"] = 20
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)

    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(candidates)
    )
    artifact = finalize_quotes(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )

    assert artifact["truth_group_cap"] == 20
    assert artifact["truth_group_count"] == 20
    assert artifact["influence_group_count"] <= 3


def test_positional_relation_mode_rehydrates_candidate_identity_without_returning_ids(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)

    assert "Do not return candidate IDs" in prompt
    assert schema["required"] == ["results_by_candidate_row"]
    row_schema = schema["properties"]["results_by_candidate_row"]
    assert row_schema["required"] == [
        f"row_{index:04d}" for index in range(len(candidates))
    ]
    assert row_schema["properties"]["row_0000"]["enum"] == [
        "support",
        "counter",
        "adjacent",
        "exclude",
    ]

    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _positional_relation_response(candidates)
    )

    assert [row["candidate_id"] for row in quote_manifest["labeled_inventory"]] == [
        row["candidate_id"] for row in candidates
    ]
    assert {
        row["reason_code"] for row in quote_manifest["labeled_inventory"]
    } <= {
        "matching_customer_experience",
        "differing_customer_experience",
        "related_customer_context",
        "wrong_scope_or_non_evidence",
    }


def test_positional_relation_mode_rejects_missing_row_at_identity_boundary(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"].pop("row_0007")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "missing_candidate_result"


def test_positional_relation_mode_rejects_substituted_row_key_at_identity_boundary(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"]["row_9999"] = response[
        "results_by_candidate_row"
    ].pop("row_0001")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "missing_candidate_result"


def test_batched_positional_relations_rehydrate_the_same_full_inventory(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    batch_manifest, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=7
    )
    candidates = _candidate_rows(sources, spec)
    full_response = _positional_relation_response(candidates)
    responses = {}
    for batch, (prompt, schema) in zip(
        batch_manifest["batches"], prompts_and_schemas, strict=True
    ):
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = {
            "batch_id": batch["batch_id"],
            "results_by_candidate_row": {
                f"row_{local_index:04d}": full_response[
                    "results_by_candidate_row"
                ][f"row_{start + local_index:04d}"]
                for local_index in range(len(subset))
            },
        }
        assert "Do not return candidate IDs" in prompt
        assert schema["required"] == ["results_by_candidate_row", "batch_id"]
        assert schema["properties"]["batch_id"]["enum"] == [batch["batch_id"]]

    _, _, batched_quote_manifest = finalize_batched_relations_prepare_quotes(
        batch_manifest, sources, responses
    )
    _, _, unbatched_manifest = prepare_evidence_selection(spec, sources)
    _, _, unbatched_quote_manifest = finalize_relations_prepare_quotes(
        unbatched_manifest, sources, full_response
    )

    assert [row["candidate_count"] for row in batch_manifest["batches"]] == [7, 7, 6]
    assert batched_quote_manifest["labeled_inventory"] == unbatched_quote_manifest[
        "labeled_inventory"
    ]
    assert batched_quote_manifest["selected_rows"] == unbatched_quote_manifest[
        "selected_rows"
    ]
    assert batched_quote_manifest["relation_transport"] == {
        "mode": "named_positional_batches",
        "batch_manifest_sha256": batch_manifest["manifest_sha256"],
        "batch_count": 3,
        "batch_response_sha256": {
            batch_id: _canonical_hash(response)
            for batch_id, response in responses.items()
        },
    }
    assert batched_quote_manifest["schema_version"] == BATCHED_QUOTE_MANIFEST_VERSION
    assert "relation_transport" not in unbatched_quote_manifest
    batched_artifact = finalize_quotes(
        batched_quote_manifest,
        sources,
        _quote_response(batched_quote_manifest, sources),
    )
    unbatched_artifact = finalize_quotes(
        unbatched_quote_manifest,
        sources,
        _quote_response(unbatched_quote_manifest, sources),
    )
    assert batched_artifact["source_groups"] == unbatched_artifact["source_groups"]


def test_batched_positional_relations_reject_missing_batch(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    candidates = _candidate_rows(sources, spec)
    first = batch_manifest["batches"][0]
    responses = {
        first["batch_id"]: _positional_relation_response(
            candidates[: first["candidate_count"]]
        )
    }

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "missing_relation_batch"


def test_batched_positional_relations_reject_local_row_reordering(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _batched_positional_relation_response(
            subset, batch["batch_id"]
        )
    first_rows = responses["batch_0001"]["results_by_candidate_row"]
    first_rows["row_9999"] = first_rows.pop("row_0001")

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "missing_candidate_result"


def test_batched_positional_relations_reject_tampered_manifest(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    batch_manifest["candidate_count"] = 9

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, {})

    assert caught.value.boundary == "manifest_verification"


def test_batched_positional_relations_reject_duplicate_batch_identity(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )
    batch_manifest["batches"][1]["batch_id"] = "batch_0001"
    batch_manifest.pop("manifest_sha256")
    batch_manifest["manifest_sha256"] = _canonical_hash(batch_manifest)

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, {})

    assert caught.value.boundary == "manifest_verification"


def test_batched_positional_relations_reject_transposed_same_size_batches(
    tmp_path: Path,
) -> None:
    """Two same-size batches must not accept each other's response.

    Row keys restart at row_0000 in every batch, so without a per-batch
    identity a mis-filed response file finalizes cleanly with every candidate
    still accounted exactly once and every relation silently taken from the
    wrong batch.
    """

    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    batch_manifest, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=10
    )
    candidates = _candidate_rows(sources, spec)

    assert [row["candidate_count"] for row in batch_manifest["batches"]] == [10, 10]
    first_schema, second_schema = (schema for _, schema in prompts_and_schemas)
    assert first_schema != second_schema
    assert (
        batch_manifest["batches"][0]["response_schema_sha256"]
        != batch_manifest["batches"][1]["response_schema_sha256"]
    )

    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _batched_positional_relation_response(
            subset, batch["batch_id"]
        )
    responses["batch_0001"], responses["batch_0002"] = (
        responses["batch_0002"],
        responses["batch_0001"],
    )

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "relation_batch_identity"


def test_batched_positional_relations_reject_absent_batch_identity(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    batch_manifest, _ = prepare_evidence_selection_batches(spec, sources, batch_size=6)
    candidates = _candidate_rows(sources, spec)
    responses = {}
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        responses[batch["batch_id"]] = _positional_relation_response(subset)

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_batched_relations_prepare_quotes(batch_manifest, sources, responses)

    assert caught.value.boundary == "relation_response_shape"


def test_positional_relation_mode_rejects_non_string_relation_value(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 8)
    spec["relation_response_mode"] = "positional"
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _positional_relation_response(candidates)
    response["results_by_candidate_row"]["row_0000"] = {"relation": "support"}

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)

    assert caught.value.boundary == "relation_response_shape"


def test_relation_batch_policy_guidance_is_selection_wide_not_per_batch(
    tmp_path: Path,
) -> None:
    """A batch is a transport slice, so it cannot acquire its own policy lane."""

    spec, sources = _write_source(tmp_path, 20)
    spec["relation_response_mode"] = "positional"
    candidates = _candidate_rows(sources, spec)
    selection_guidance = _policy_guidance(spec, candidates)
    _, prompts_and_schemas = prepare_evidence_selection_batches(
        spec, sources, batch_size=6
    )

    for prompt, _ in prompts_and_schemas:
        assert ("VALUE-BOX POLICY" in prompt) == ("VALUE-BOX POLICY" in selection_guidance)


@pytest.mark.parametrize("batch_size", [0, 301, "100", True])
def test_relation_batching_rejects_invalid_batch_size(
    tmp_path: Path, batch_size: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["relation_response_mode"] = "positional"

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection_batches(spec, sources, batch_size=batch_size)

    assert caught.value.boundary == "selection_spec"


def test_relation_batching_rejects_literal_id_mode(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path)

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection_batches(spec, sources, batch_size=5)

    assert caught.value.boundary == "selection_spec"


def test_relation_batch_runner_writes_and_finalizes_exact_batch_set(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 10)
    spec["relation_response_mode"] = "positional"
    spec["sources"] = [
        {
            "source_id": sources[0]["source_id"],
            "packet_path": str(sources[0]["packet_path"]),
            "bundle_path": str(sources[0]["bundle_path"]),
        }
    ]
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    batch_dir = tmp_path / "prepared"
    batch_manifest_path = tmp_path / "batch_manifest.json"

    prepared = prepare_evidence_selection_batches_run(
        spec_path=spec_path,
        batch_size=6,
        batch_dir=batch_dir,
        batch_manifest_out=batch_manifest_path,
    )
    batch_manifest = json.loads(batch_manifest_path.read_text(encoding="utf-8"))
    candidates = _candidate_rows(sources, spec)
    response_dir = tmp_path / "responses"
    response_dir.mkdir()
    for batch in batch_manifest["batches"]:
        start = batch["start_index"]
        subset = candidates[start : start + batch["candidate_count"]]
        (response_dir / f"{batch['batch_id']}_response.json").write_text(
            json.dumps(
                _batched_positional_relation_response(subset, batch["batch_id"])
            ),
            encoding="utf-8",
        )

    finalized = finalize_evidence_selection_batches_run(
        batch_manifest_path=batch_manifest_path,
        response_dir=response_dir,
        quote_prompt_out=tmp_path / "quote_prompt.txt",
        quote_schema_out=tmp_path / "quote_schema.json",
        quote_manifest_out=tmp_path / "quote_manifest.json",
    )

    assert prepared["candidate_count"] == 10
    assert prepared["batch_count"] == 2
    assert finalized["candidate_count"] == 10
    assert finalized["batch_count"] == 2
    assert (batch_dir / "batch_0001_prompt.txt").is_file()
    assert (batch_dir / "batch_0002_schema.json").is_file()


@pytest.mark.parametrize("cap", [0, 21, "15", True])
def test_selection_spec_rejects_invalid_truth_origin_cap(
    tmp_path: Path, cap: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["truth_group_cap"] = cap

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)

    assert caught.value.boundary == "selection_spec"


@pytest.mark.parametrize("mode", ["ids", "ordered", 1, True])
def test_selection_spec_rejects_invalid_relation_response_mode(
    tmp_path: Path, mode: object
) -> None:
    spec, sources = _write_source(tmp_path)
    spec["relation_response_mode"] = mode

    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)

    assert caught.value.boundary == "selection_spec"


def test_provider_prompts_are_compact_views_while_manifests_keep_full_facts(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 5)
    relation_prompt, relation_schema, manifest = prepare_evidence_selection(
        spec, sources
    )
    assert '"candidate_columns"' in relation_prompt
    assert '"independence_posture"' not in relation_prompt
    assert '"source_ref"' not in relation_prompt
    assert '"engagement_raw_value"' not in relation_prompt
    assert manifest["candidate_inventory_sha256"]
    assert relation_schema["properties"]["results"]["items"]["properties"][
        "reason_code"
    ]["pattern"]

    long_body = "One shared body. " + "x" * 300
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = long_body
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    quote_prompt, quote_schema, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    assert quote_prompt.count(long_body) == 1
    assert '"body_columns"' in quote_prompt
    assert len(quote_manifest["provider_selected_ids"]) == len(
        quote_manifest["selected_rows"]
    )
    exact_quote_schema = quote_schema["properties"]["quotes"]["items"][
        "properties"
    ]["exact_quote"]
    assert exact_quote_schema["maxLength"] == 220


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("missing", "missing_candidate_result"),
        ("duplicate", "duplicate_candidate_result"),
        ("foreign", "foreign_candidate_result"),
    ],
)
def test_relation_candidate_accounting_fails_at_intended_boundary(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 4)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    response = _relation_response(_candidate_rows(sources, spec))
    if mutation == "missing":
        response["results"].pop()
    elif mutation == "duplicate":
        response["results"].append(copy.deepcopy(response["results"][0]))
    else:
        response["results"][-1]["candidate_id"] = "candidate_foreign"
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == boundary


def test_creator_cannot_be_laundered_into_customer_support(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 5)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _relation_response(candidates)
    creator = next(index for index, row in enumerate(candidates) if row["layer"] == "influence_context")
    response["results"][creator]["relation"] = "support"
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == "creator_customer_laundering"


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("changed_character", "quote_exactness"),
        ("overlength", "quote_overlength"),
        ("inserted_ellipsis", "quote_exactness"),
    ],
)
def test_quote_mutations_fail_at_exact_boundary(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 2)
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = "Opening context. " + "x" * 400 + " Closing context."
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    row = response["quotes"][0]
    if mutation == "changed_character":
        row["exact_quote"] = row["exact_quote"].replace("Opening", "Changed", 1)
    elif mutation == "overlength":
        row["exact_quote"] = "x" * 221
    else:
        row["exact_quote"] = "Opening ... Closing context."
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == boundary


def test_missing_body_is_typed_unavailable_and_exact_but_semantically_different_text_remains_quality_visible(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"] = []
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {"quotes": []}
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["quote_status"] == "quote_unavailable"
    assert row["source_body_present"] is False
    assert row["quote_unavailable_cause"] == "source_body_unavailable"
    assert row["normalized_meaning"]


def test_quote_unavailable_from_an_available_body_is_distinguishable_from_a_missing_body(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "x" * 400
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {
        "quotes": [
            {
                "selected_id": quote_manifest["selected_rows"][0]["selected_id"],
                "quote_status": "quote_unavailable",
                "exact_quote": None,
            }
        ]
    }
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["quote_status"] == "quote_unavailable"
    assert row["source_body_present"] is True
    assert row["quote_unavailable_cause"] == "no_relevant_exact_quote_returned"


def test_source_native_ellipsis_is_preserved_when_the_quote_is_exact(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "My lips burn… only after this shade."
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {"quotes": []}
    artifact = finalize_quotes(quote_manifest, sources, response)
    output_row = artifact["source_groups"][0]["rows"][0]
    assert output_row["exact_quote"] == "My lips burn… only after this shade."
    assert output_row["quote_unavailable_cause"] is None


def test_short_source_body_cannot_be_clipped_before_material_countervailing_behavior(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    body = (
        "Do I cringe a little every time I remember the price tag? Yes. "
        "Will I be repurchasing vanilla AND vanilla beige? Also yes."
    )
    sources[0]["bundle"]["evidence_units"][0]["text"] = body
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    quote_prompt, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    assert spec["bounded_claim"] in quote_prompt
    assert body not in quote_prompt
    assert quote_manifest["provider_selected_ids"] == []
    artifact = finalize_quotes(quote_manifest, sources, {"quotes": []})
    row = artifact["source_groups"][0]["rows"][0]
    assert row["exact_quote"] == body


def test_display_label_uses_customer_facing_signal_and_preserves_source_meanings(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "x" * 400
    _reseal(sources[0])
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    for suffix, statement in (
        ("vanilla", "The author intends to repurchase the Vanilla option."),
        ("vanilla-beige", "The author intends to repurchase the Vanilla Beige shade."),
    ):
        companion = copy.deepcopy(evidence_row[10][0])
        companion[0] = f"community_post:0::{suffix}"
        companion[1] = statement
        companion[7] = ["shade_and_color_fit"]
        companion[8] = []
        evidence_row[10].append(companion)
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")

    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidate = _candidate_rows(sources, spec)[0]
    relation_response = {
        "results": [
            {
                "candidate_id": candidate["candidate_id"],
                "relation": "counter",
                "reason_code": "repurchase_despite_price",
            }
        ]
    }
    quote_prompt, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, relation_response
    )
    assert "Repurchase intent despite price" in quote_prompt
    response = _quote_response(quote_manifest, sources)
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["display_label"] == "Repurchase intent despite price"
    assert "presentation_statement" not in row
    assert [meaning["statement"] for meaning in row["same_evidence_companion_meanings"]] == [
        "The author intends to repurchase the Vanilla option.",
        "The author intends to repurchase the Vanilla Beige shade.",
    ]


@pytest.mark.parametrize(
    ("reason_code", "boundary"),
    [
        ("", "relation_response_shape"),
        ("Not a code", "relation_response_shape"),
        ("x" * 81, "relation_response_shape"),
        ("counter_to_poor_value", "reason_code_relation_leak"),
    ],
)
def test_relation_reason_code_cannot_leak_internal_relation_into_display_label(
    tmp_path: Path,
    reason_code: str,
    boundary: str,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidate = _candidate_rows(sources, spec)[0]
    response = {
        "results": [
            {
                "candidate_id": candidate["candidate_id"],
                "relation": "counter",
                "reason_code": reason_code,
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == boundary


def test_legacy_quote_manifest_retains_its_original_response_shape(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    quote_manifest["schema_version"] = "phase_a_evidence_quote_manifest_v1"
    quote_manifest.pop("provider_selected_ids")
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    response = _quote_response(quote_manifest, sources)
    artifact = finalize_quotes(quote_manifest, sources, response)
    assert "display_label" not in artifact["source_groups"][0]["rows"][0]


def test_v3_quote_manifest_remains_finalizable_with_all_selected_responses(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    quote_manifest["schema_version"] = "phase_a_evidence_quote_manifest_v3"
    quote_manifest.pop("provider_selected_ids")
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    response = _quote_response(quote_manifest, sources)
    artifact = finalize_quotes(quote_manifest, sources, response)
    assert artifact["source_groups"][0]["rows"][0]["display_label"]


def test_v4_provider_subset_is_recomputed_from_bound_body_lengths(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    selected_id = quote_manifest["selected_rows"][0]["selected_id"]
    quote_manifest["provider_selected_ids"] = [selected_id]
    quote_manifest["manifest_sha256"] = _canonical_hash(
        {key: value for key, value in quote_manifest.items() if key != "manifest_sha256"}
    )
    body = sources[0]["bundle"]["evidence_units"][0]["text"]
    response = {
        "quotes": [
            {
                "selected_id": selected_id,
                "quote_status": "quote_available",
                "exact_quote": body,
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "manifest_verification"
    assert "provider quote workload changed" in str(caught.value)


def test_candidate_exposes_same_evidence_companion_meanings_without_admitting_them(
    tmp_path: Path,
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    companion = copy.deepcopy(evidence_row[10][0])
    companion[0] = "community_post:0::repurchase"
    companion[1] = "The author intends to repurchase two named shades."
    companion[7] = ["shade_and_color_fit"]
    companion[8] = []
    evidence_row[10].append(companion)
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")

    candidates = _candidate_rows(sources, spec)
    assert len(candidates) == 1
    assert candidates[0]["same_evidence_companion_meanings"] == [
        {
            "semantic_unit_ref": "community_post:0::repurchase",
            "statement": "The author intends to repurchase two named shades.",
            "polarity": "affirmed",
            "axis_ids": ["shade_and_color_fit"],
            "conditions": [],
        }
    ]


def test_sephora_positive_helpful_votes_rank_inside_only_the_sephora_bucket() -> None:
    common = {
        "protected_lanes": [],
        "relation": "support",
        "engagement_material_positive": True,
        "engagement_kind": "sephora_helpful_votes",
    }
    higher = {**common, "candidate_id": "higher", "engagement_raw_value": {"negative": 6, "positive": 30, "total": 36}}
    lower = {**common, "candidate_id": "lower", "engagement_raw_value": {"negative": 2, "positive": 24, "total": 26}}
    assert _bucket_priority(higher) < _bucket_priority(lower)
    with pytest.raises(EvidenceConsumerError) as caught:
        _bucket_priority({**higher, "engagement_raw_value": {"negative": 6, "positive": 30, "total": 35}})
    assert caught.value.boundary == "unsupported_engagement_shape"


def test_unknown_mapping_engagement_fails_during_candidate_admission(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    evidence_row = sources[0]["packet"]["source_groups"][0]["evidence_rows"][0]
    evidence_row[9][1] = {"likes": 50}
    packet = sources[0]["packet"]
    packet["packet_sha256"] = _canonical_hash(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == "unsupported_engagement_shape"


def test_known_host_variants_group_under_one_source_venue() -> None:
    assert _source_venue("community_post", "https://reddit.com/r/x", "reddit:1")[:1] == ("reddit",)
    assert _source_venue("community_post", "https://old.reddit.com/r/x", "reddit:2")[:1] == ("reddit",)
    assert _source_venue("audience_comment", "https://m.tiktok.com/v/1", "tiktok-comment:1")[:1] == ("tiktok",)
    assert _source_venue("retailer_review", "https://www.sephora.com/product/x", "retailer:sephora:1")[:1] == ("sephora",)


@pytest.mark.parametrize(
    ("role", "source_ref", "evidence_id", "venue"),
    [
        ("community_post", "https://np.reddit.com/r/x/comments/1", "reddit:1", "reddit"),
        ("community_post", "https://new.reddit.com/r/x/comments/2", "reddit:2", "reddit"),
        ("community_post", "https://sh.reddit.com/r/x/comments/3", "reddit:3", "reddit"),
        ("community_post", "https://redd.it/abc", "reddit:4", "reddit"),
        ("audience_comment", "https://vm.tiktok.com/ZM123/", "tiktok-comment:1", "tiktok"),
        ("audience_comment", "https://vt.tiktok.com/ZS456/", "tiktok-comment:2", "tiktok"),
        ("retailer_review", "https://smile.amazon.com/dp/B0", "retailer:amazon:1", "amazon"),
        ("retailer_review", "https://community.sephora.com/t/x", "retailer:sephora:1", "sephora"),
    ],
)
def test_host_variants_and_short_links_do_not_split_one_venue(
    role: str, source_ref: str, evidence_id: str, venue: str
) -> None:
    assert _source_venue(role, source_ref, evidence_id) == (venue, "normalized_source_ref_hostname")


def test_a_lookalike_host_is_not_absorbed_into_a_known_venue() -> None:
    assert _source_venue("community_post", "https://notreddit.com/x", "x:1") == (
        "notreddit.com",
        "source_ref_hostname",
    )


def test_partial_numeric_engagement_strings_are_refused_rather_than_misread() -> None:
    common = {"protected_lanes": [], "relation": "support",
              "engagement_material_positive": True, "engagement_kind": "reddit_points"}
    # "1.2k points" must not order as 1.0 behind a genuine "5 points".
    abbreviated = {**common, "candidate_id": "a", "engagement_raw_value": "1.2k points"}
    grouped = {**common, "candidate_id": "b", "engagement_raw_value": "1,234 points"}
    plain = {**common, "candidate_id": "c", "engagement_raw_value": "5 points"}
    assert _numeric_engagement("1.2k points", "reddit_points") is None
    assert _numeric_engagement("1,234 points", "reddit_points") is None
    assert _numeric_engagement("922", "reddit_points") == 922.0
    assert _numeric_engagement("368 points", "reddit_points") == 368.0
    ordered = [row["candidate_id"] for row in sorted([abbreviated, grouped, plain], key=_bucket_priority)]
    assert ordered[0] == "c"


def test_a_negative_native_score_still_orders_above_unavailable_engagement() -> None:
    common = {"protected_lanes": [], "relation": "support",
              "engagement_material_positive": True, "engagement_kind": "reddit_points"}
    downvoted = {**common, "candidate_id": "a_downvoted", "engagement_raw_value": -30}
    unavailable = {**common, "candidate_id": "b_unavailable", "engagement_raw_value": None}
    assert _bucket_priority(downvoted) < _bucket_priority(unavailable)


def test_edited_bundle_body_without_a_resealed_hash_fails_bundle_verification(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "Fabricated body text the bundle hash never covered."
    with pytest.raises(EvidenceConsumerError) as caught:
        prepare_evidence_selection(spec, sources)
    assert caught.value.boundary == "bundle_verification"


def test_body_swapped_after_the_quote_manifest_cannot_supply_a_quote(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    for unit in sources[0]["bundle"]["evidence_units"]:
        unit["text"] = "Body substituted after the quote manifest was written."
    response = {"quotes": []}
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "body_identity_mismatch"


@pytest.mark.parametrize(
    ("mutation", "boundary"),
    [
        ("unresolved_wrong_source", "failed_rehydration_lookup"),
        ("protected_absent_evidence", "failed_rehydration_lookup"),
        ("protected_unknown_lane", "selection_spec"),
        ("nomination_row_malformed", "selection_spec"),
    ],
)
def test_operator_nominations_that_cannot_resolve_fail_closed(
    tmp_path: Path, mutation: str, boundary: str
) -> None:
    spec, sources = _write_source(tmp_path, 4)
    if mutation == "unresolved_wrong_source":
        spec["admit_unresolved"] = [{"source_id": "not-a-source", "evidence_id": "community_post:0"}]
    elif mutation == "protected_absent_evidence":
        spec["protected_evidence_ids"] = {"safety": ["community_post:404"]}
    elif mutation == "protected_unknown_lane":
        spec["protected_evidence_ids"] = {"safety_critical": ["community_post:0"]}
    else:
        spec["admit_semantic_refs"] = ["community_post:0::hydration"]
    with pytest.raises(EvidenceConsumerError) as caught:
        _candidate_rows(sources, spec)
    assert caught.value.boundary == boundary


def test_same_origin_distinct_relation_is_one_capped_group_with_two_visible_candidates(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 2)
    # Force the two semantic rows to share a scoped origin.
    for group in sources[0]["packet"]["source_groups"]:
        for row in group["evidence_rows"]:
            row[7] = "shared-origin"
    sources[0]["packet"]["packet_sha256"] = _canonical_hash(
        {key: value for key, value in sources[0]["packet"].items() if key != "packet_sha256"}
    )
    sources[0]["packet_path"].write_text(json.dumps(sources[0]["packet"]), encoding="utf-8")
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, spec)
    response = _relation_response(candidates)
    response["results"][0]["relation"] = "support"
    response["results"][1]["relation"] = "counter"
    _, _, quote_manifest = finalize_relations_prepare_quotes(manifest, sources, response)
    assert len({row["origin_group_id"] for row in quote_manifest["selected_rows"]}) == 1
    assert len(quote_manifest["selected_rows"]) == 2


def _selection_row(
    candidate_id: str,
    *,
    origin: str = "origin:shared",
    relation: str = "support",
    reason_code: str = "explicit_good_value",
    material_positive: bool | None = True,
    protected_lanes: list[str] | None = None,
    engagement_status: str = "engagement_available",
    engagement_raw_value: int | str | None = 10,
    source_role: str = "community_post",
    source_venue: str = "reddit",
    engagement_kind: str = "reddit_points",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "layer": "truth_support",
        "relation": relation,
        "reason_code": reason_code,
        "scoped_independence_key": origin,
        "source_role": source_role,
        "source_venue": source_venue,
        "engagement_kind": engagement_kind,
        "engagement_raw_value": engagement_raw_value,
        "engagement_material_positive": material_positive,
        "engagement_status": engagement_status,
        "conditions": [],
        "protected_lanes": protected_lanes or [],
    }


def _value_axis_source(tmp_path: Path, count: int = 6) -> tuple[dict, list[dict]]:
    """Build a real-entry-point value-axis source and spec."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    packet, bundle = _packet_and_bundle(count)
    for group in packet["source_groups"]:
        for row in group["evidence_rows"]:
            for semantic in row[-1]:
                axes = semantic[7]
                semantic[7] = (
                    axes.replace("hydration_and_moisture", "value_and_quantity")
                    if isinstance(axes, str)
                    else ["value_and_quantity"]
                )
    packet["selection"]["axis_ids"] = ["value_and_quantity"]
    packet.pop("packet_sha256", None)
    packet["packet_sha256"] = _canonical_hash(packet)
    packet_path = tmp_path / "packet.json"
    bundle_path = tmp_path / "bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    spec = dict(_spec(count))
    spec["axis_ids"] = ["value_and_quantity"]
    spec["bounded_claim"] = "Customers report value-for-money experiences with the balm."
    return spec, [
        {
            "source_id": "full-corpus",
            "packet_path": packet_path,
            "bundle_path": bundle_path,
            "packet": packet,
            "bundle": bundle,
        }
    ]


def _value_relation_response(
    candidates: list[dict], overrides: dict[str, tuple[str, str]] | None = None
) -> dict:
    overrides = overrides or {}
    rows = []
    for candidate in candidates:
        if candidate["evidence_id"] in overrides:
            relation, reason_code = overrides[candidate["evidence_id"]]
        elif candidate["layer"] == "influence_context":
            relation, reason_code = "adjacent", "non_value_product_experience"
        else:
            relation, reason_code = "support", "explicit_good_value"
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "relation": relation,
                "reason_code": reason_code,
            }
        )
    return {"results": rows}


def test_a_value_axis_spec_turns_on_the_value_prompt_and_schema_at_the_real_entry_point(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path)
    prompt, schema, _ = prepare_evidence_selection(spec, sources)
    assert "VALUE-BOX POLICY" in prompt
    variants = schema["properties"]["results"]["items"]["anyOf"]
    by_relation = {
        row["properties"]["relation"]["const"]: set(
            row["properties"]["reason_code"]["enum"]
        )
        for row in variants
    }
    assert "better_value_than_comparator" in by_relation["support"]
    assert "comparator_better_value" in by_relation["counter"]

    balanced_dir = tmp_path / "balanced"
    balanced_dir.mkdir(parents=True, exist_ok=True)
    non_value_prompt, non_value_schema, _ = prepare_evidence_selection(
        *_write_source(balanced_dir)
    )
    assert "VALUE-BOX POLICY" not in non_value_prompt
    assert "anyOf" not in non_value_schema["properties"]["results"]["items"]


def test_value_policy_does_not_turn_time_to_finish_into_quantity_value() -> None:
    guidance = _policy_guidance({"axis_ids": ["value_and_quantity"]})

    assert "Time to finish, pan, or empty a product is completed-use evidence" in guidance
    assert "not quantity efficiency" in guidance
    assert "explicitly says it will buy or repurchase again" in guidance


def test_explicit_only_value_refs_turn_on_value_policy_without_admitting_the_whole_axis(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path, count=3)
    all_candidates = _candidate_rows(sources, spec)
    admitted = all_candidates[:2]
    spec["axis_ids"] = []
    spec["admit_semantic_refs"] = [
        {
            "source_id": candidate["source_id"],
            "semantic_unit_ref": candidate["semantic_unit_ref"],
        }
        for candidate in admitted
    ]

    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    assert manifest["candidate_count"] == 2
    assert "VALUE-BOX POLICY" in prompt
    assert "anyOf" in schema["properties"]["results"]["items"]

    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(
            manifest,
            sources,
            _relation_response(_candidate_rows(sources, manifest["spec"])),
        )
    assert caught.value.boundary == "value_reason_code"


def test_mixed_explicit_refs_do_not_inherit_value_only_policy(tmp_path: Path) -> None:
    spec, sources = _value_axis_source(tmp_path, count=2)
    packet = sources[0]["packet"]
    semantic_rows = [
        semantic
        for group in packet["source_groups"]
        for evidence in group["evidence_rows"]
        for semantic in evidence[-1]
    ]
    semantic_rows[1][7] = ["hydration_and_moisture"]
    _reseal(sources[0])
    explicit_candidates = _candidate_rows(sources, spec)
    # The axis spec now admits only the remaining value row; explicitly nominate
    # both rows to form the mixed bounded set.
    hydration_ref = semantic_rows[1][0]
    spec["axis_ids"] = []
    spec["admit_semantic_refs"] = [
        {
            "source_id": "full-corpus",
            "semantic_unit_ref": explicit_candidates[0]["semantic_unit_ref"],
        },
        {"source_id": "full-corpus", "semantic_unit_ref": hydration_ref},
    ]

    prompt, schema, manifest = prepare_evidence_selection(spec, sources)
    assert manifest["candidate_count"] == 2
    assert "VALUE-BOX POLICY" not in prompt
    assert "anyOf" not in schema["properties"]["results"]["items"]


def test_a_value_axis_spec_keeps_a_highly_engaged_adjacent_row_out_of_the_displayed_box(
    tmp_path: Path,
) -> None:
    adjacent = {"community_post:5": ("adjacent", "non_value_product_experience")}
    spec, sources = _value_axis_source(tmp_path / "value")
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, manifest["spec"])
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _value_relation_response(candidates, adjacent)
    )
    artifact = finalize_quotes(
        quote_manifest, sources, _quote_response(quote_manifest, sources)
    )
    displayed = {row["evidence_id"] for group in artifact["source_groups"] for row in group["rows"]}
    accounted = {row["evidence_id"] for row in artifact["candidate_dispositions"]}
    assert "community_post:5" not in displayed
    assert "community_post:5" in accounted

    balanced_spec, balanced_sources = _value_axis_source(tmp_path / "balanced")
    balanced_spec["axis_ids"] = ["value_and_quantity", "hydration_and_moisture"]
    _, _, balanced_manifest = prepare_evidence_selection(balanced_spec, balanced_sources)
    balanced_candidates = _candidate_rows(balanced_sources, balanced_manifest["spec"])
    _, _, balanced_quotes = finalize_relations_prepare_quotes(
        balanced_manifest,
        balanced_sources,
        _value_relation_response(balanced_candidates, adjacent),
    )
    balanced_artifact = finalize_quotes(
        balanced_quotes,
        balanced_sources,
        _quote_response(balanced_quotes, balanced_sources),
    )
    balanced_displayed = {
        row["evidence_id"]
        for group in balanced_artifact["source_groups"]
        for row in group["rows"]
    }
    assert "community_post:5" in balanced_displayed


def test_a_value_axis_spec_rejects_an_inverted_comparator_through_the_real_finalizer(
    tmp_path: Path,
) -> None:
    spec, sources = _value_axis_source(tmp_path)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    candidates = _candidate_rows(sources, manifest["spec"])
    response = _value_relation_response(
        candidates, {"community_post:5": ("counter", "better_value_than_comparator")}
    )
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_relations_prepare_quotes(manifest, sources, response)
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_every_value_reason_code_that_can_be_displayed_has_a_curated_label() -> None:
    displayable = {
        code
        for code, relation in VALUE_REASON_RELATIONS.items()
        if relation in {"support", "counter", "adjacent"}
    }
    assert displayable <= set(DISPLAY_LABEL_BY_REASON_CODE)


def test_value_policy_keeps_positive_value_first_and_only_one_direct_complaint() -> None:
    rows = [
        _selection_row(
            "repurchase-204",
            origin="origin:repurchase",
            reason_code="repurchase_despite_price",
            engagement_raw_value="204 points",
        ),
        _selection_row(
            "appeal-10",
            origin="origin:appeal",
            reason_code="multiple_purchases_despite_price",
            engagement_raw_value="10 points",
        ),
        _selection_row(
            "value-per-ounce-514",
            origin="origin:value-per-ounce",
            reason_code="favorable_price_quantity_comparison",
            engagement_raw_value="514 points",
        ),
        _selection_row(
            "retailer-value-31",
            origin="origin:retailer-value",
            reason_code="favorable_price_quantity_comparison",
            engagement_raw_value=31,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "regret-1174",
            origin="origin:regret",
            relation="counter",
            reason_code="purchase_regret_due_cost",
            engagement_raw_value="1174 points",
        ),
        _selection_row(
            "retailer-complaint-35",
            origin="origin:retailer-complaint",
            relation="counter",
            reason_code="too_little_product_for_price",
            engagement_raw_value=35,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "formula-599",
            origin="origin:formula",
            relation="adjacent",
            reason_code="non_value_product_experience",
            engagement_raw_value="599 points",
        ),
    ]

    selected = _select_groups(rows, "truth_support", 5, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}

    assert {"repurchase-204", "appeal-10"} <= selected_ids
    assert "formula-599" not in selected_ids
    assert [row["candidate_id"] for row in selected if row["relation"] == "counter"] == [
        "regret-1174"
    ]
    assert len({row["origin_group_id"] for row in selected}) == 5


def test_value_behavior_tier_uses_native_engagement_not_behavior_subtype() -> None:
    rows = [
        _selection_row(
            f"repurchase-{engagement}",
            origin=f"origin:repurchase:{engagement}",
            reason_code="repurchase_despite_price",
            engagement_raw_value=f"{engagement} points",
        )
        for engagement in (204, 44, 11, 3)
    ]
    rows.extend(
        [
            _selection_row(
                "multiple-purchases-10",
                origin="origin:multiple-purchases",
                reason_code="multiple_purchases_despite_price",
                engagement_raw_value="10 points",
            ),
            _selection_row(
                "regret-1174",
                origin="origin:regret",
                relation="counter",
                reason_code="purchase_regret_due_cost",
                engagement_raw_value="1174 points",
            ),
        ]
    )
    selected = _select_groups(rows, "truth_support", 5, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}
    assert "multiple-purchases-10" in selected_ids
    assert "repurchase-3" not in selected_ids


def test_value_reason_codes_must_match_their_relation_lane() -> None:
    candidate = _selection_row("candidate:value")
    response = {
        "results": [
            {
                "candidate_id": "candidate:value",
                "relation": "support",
                "reason_code": "purchase_regret_due_cost",
            }
        ]
    }
    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_relation_response([candidate], response, value_policy=True)
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_high_spend_buyer_remorse_is_one_counter_meaning_without_journey_fields() -> None:
    code = "high_spend_followed_by_buyer_remorse"
    assert VALUE_REASON_RELATIONS[code] == "counter"
    assert _display_label(code) == "High spend, followed by buyer’s remorse"
    assert _display_label("purchase_regret_due_cost") == "Purchase regret due to cost"

    candidate = _selection_row("candidate:high-spend-remorse", relation="counter")
    accepted = _validate_relation_response(
        [candidate],
        {
            "results": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "relation": "counter",
                    "reason_code": code,
                }
            ]
        },
        value_policy=True,
    )
    assert accepted[0]["reason_code"] == code
    assert not ({"future_intent", "transaction_count", "post_purchase_value"} & accepted[0].keys())


def test_high_spend_buyer_remorse_cannot_be_promoted_to_value_support() -> None:
    candidate = _selection_row("candidate:high-spend-remorse")
    with pytest.raises(EvidenceConsumerError) as caught:
        _validate_relation_response(
            [candidate],
            {
                "results": [
                    {
                        "candidate_id": candidate["candidate_id"],
                        "relation": "support",
                        "reason_code": "high_spend_followed_by_buyer_remorse",
                    }
                ]
            },
            value_policy=True,
        )
    assert caught.value.boundary == "value_reason_relation_mismatch"


def test_value_response_schema_makes_comparator_direction_unambiguous() -> None:
    variants = _relation_schema(value_policy=True)["properties"]["results"]["items"][
        "anyOf"
    ]
    by_relation = {
        row["properties"]["relation"]["const"]: set(
            row["properties"]["reason_code"]["enum"]
        )
        for row in variants
    }
    assert "better_value_than_comparator" in by_relation["support"]
    assert "better_value_than_comparator" not in by_relation["counter"]
    assert "comparator_better_value" in by_relation["counter"]
    assert {
        "repurchase_intent",
        "multiple_purchases",
        "purchase_commitment",
        "product_goes_a_long_way",
    } <= by_relation["support"]


def test_value_prompt_forbids_companion_only_formula_complaints_from_value_lanes() -> None:
    guidance = _policy_guidance({"axis_ids": ["value_and_quantity"]})
    assert "formula, hydration, scent, trial-only, gift-card" in guidance
    assert "must not turn" in guidance
    assert "repurchase_despite_price" in guidance
    assert "repurchase_intent" in guidance
    assert "requires explicit source meaning about price or cost" in guidance
    assert "whole same-evidence set" in guidance
    assert "every candidate from that evidence origin counter or adjacent" in guidance
    assert "rationalizing sunk cost does not countervail" in guidance
    assert "use the corresponding `*_despite_price` code" in guidance
    assert "does not imply repurchase, a transaction count, or future intent" in guidance
    assert "Multiple units alone do not establish high spend" in guidance
    assert "regret exists without explicit substantial completed spending" in guidance
    # The buy-again / worth-the-price exceptions must still decide the lane
    # before either regret code is offered, or the regret routing sentences
    # would demote an explicit repurchase-despite-price origin to counter.
    assert "neither regret code may be used on an origin" in guidance
    assert guidance.index("Those two exceptions decide the lane") < guidance.index(
        "Use `purchase_regret_due_cost`"
    )
    assert "product_goes_a_long_way" in guidance
    assert _policy_guidance({"axis_ids": ["hydration_and_moisture"]}) == ""


def test_value_policy_does_not_compare_counter_engagement_across_venues() -> None:
    rows = [
        _selection_row(
            "reddit-value",
            origin="origin:reddit-value",
            reason_code="explicit_good_value",
            engagement_raw_value="20 points",
        ),
        _selection_row(
            "sephora-complaint",
            origin="origin:sephora-complaint",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value=200,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == ["reddit-value"]


def test_value_policy_shows_the_strongest_native_complaint_when_no_support_exists() -> None:
    rows = [
        _selection_row(
            f"regret-{points}",
            origin=f"origin:regret:{points}",
            relation="counter",
            reason_code="purchase_regret_due_cost",
            engagement_raw_value=f"{points} points",
        )
        for points in (4, 1174, 31)
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == ["regret-1174"]


def test_value_policy_anchors_the_complaint_to_the_best_signal_not_first_bucket() -> None:
    rows = [
        _selection_row(
            "reddit-weak-2",
            origin="origin:reddit-weak",
            reason_code="explicit_good_value",
            engagement_raw_value="2 points",
        ),
        _selection_row(
            "reddit-counter-1",
            origin="origin:reddit-counter",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value="1 point",
        ),
        _selection_row(
            "sephora-strong-999",
            origin="origin:sephora-strong",
            reason_code="repurchase_despite_price",
            engagement_raw_value=999,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
        _selection_row(
            "sephora-counter-900",
            origin="origin:sephora-counter",
            relation="counter",
            reason_code="explicit_poor_value",
            engagement_raw_value=900,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 4, truth_policy="value_first")
    selected_ids = {row["candidate_id"] for row in selected}
    assert "sephora-strong-999" in selected_ids
    assert "sephora-counter-900" in selected_ids
    assert "reddit-counter-1" not in selected_ids


def test_value_policy_orders_protected_origins_without_cross_venue_engagement() -> None:
    rows = [
        _selection_row(
            "reddit-protected-2",
            origin="origin:reddit-protected",
            protected_lanes=["costly_behavior"],
            engagement_raw_value="2 points",
        ),
        _selection_row(
            "sephora-protected-999",
            origin="origin:sephora-protected",
            protected_lanes=["costly_behavior"],
            engagement_raw_value=999,
            source_role="retailer_review",
            source_venue="sephora",
            engagement_kind="positive_helpful_count",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert [row["candidate_id"] for row in selected] == [
        "reddit-protected-2",
        "sephora-protected-999",
    ]


def test_value_policy_keeps_operator_protected_counter_even_without_positive_engagement() -> None:
    rows = [
        _selection_row(
            "protected-costly",
            origin="origin:protected",
            relation="counter",
            reason_code="explicit_poor_value",
            material_positive=False,
            protected_lanes=["costly_behavior"],
        ),
        _selection_row(
            "positive",
            origin="origin:positive",
            reason_code="explicit_good_value",
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10, truth_policy="value_first")
    assert {row["candidate_id"] for row in selected} == {"protected-costly", "positive"}


def test_same_origin_displays_material_support_and_counter_but_not_unprotected_quiet() -> None:
    rows = [
        _selection_row("support", relation="support"),
        _selection_row("counter", relation="counter"),
        _selection_row("quiet", relation="adjacent", material_positive=False),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"support", "counter"}
    assert {"relation:support", "relation:counter"} <= set(
        selected[0]["origin_required_display_lanes"]
    )


def test_unprotected_quiet_counter_is_retained_but_not_forced_into_presentation() -> None:
    rows = [
        _selection_row("material_support", origin="origin:support", relation="support"),
        _selection_row(
            "quiet_counter",
            origin="origin:counter",
            relation="counter",
            material_positive=False,
        ),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"material_support"}


def test_protected_quiet_behavior_remains_visible() -> None:
    rows = [
        _selection_row(
            "quiet_behavior",
            origin="origin:behavior",
            relation="counter",
            material_positive=False,
            protected_lanes=["costly_behavior"],
        )
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"quiet_behavior"}


def test_under_cap_reservation_does_not_hide_counter_behind_quiet_row() -> None:
    rows = [
        _selection_row("a_support", relation="support"),
        _selection_row("b_quiet", relation="adjacent", material_positive=False),
        _selection_row("z_counter", relation="counter"),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert "z_counter" in {row["candidate_id"] for row in selected}


def test_more_than_ten_protected_origins_fails_the_origin_cap() -> None:
    rows = [
        _selection_row(
            f"protected:{index}",
            origin=f"origin:{index}",
            protected_lanes=["safety"],
        )
        for index in range(11)
    ]
    with pytest.raises(EvidenceConsumerError) as caught:
        _select_groups(rows, "truth_support", 10)
    assert caught.value.boundary == "presentation_cap_insufficient"


def test_every_operator_protected_candidate_and_origin_is_visible() -> None:
    rows = [
        _selection_row("safety:a", origin="origin:a", protected_lanes=["safety"]),
        _selection_row("safety:b", origin="origin:b", protected_lanes=["safety"]),
        _selection_row(
            "costly:b", origin="origin:b", relation="counter", protected_lanes=["costly_behavior"]
        ),
        _selection_row("ordinary", origin="origin:c"),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    protected = {"safety:a", "safety:b", "costly:b"}
    assert protected <= {row["candidate_id"] for row in selected}
    assert {"origin:a", "origin:b"} <= {row["origin_group_id"] for row in selected}


@pytest.mark.parametrize("quote", [" ", "!", "a", "💄"])
def test_available_quote_requires_two_unicode_alphanumeric_characters(
    tmp_path: Path, quote: str
) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = (
        "x" * 221 + f" before {quote} after"
    )
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = quote
    with pytest.raises(EvidenceConsumerError) as caught:
        finalize_quotes(quote_manifest, sources, response)
    assert caught.value.boundary == "quote_substance"


def test_two_character_exact_quote_is_allowed_without_a_lexical_relevance_gate(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    sources[0]["bundle"]["evidence_units"][0]["text"] = "x" * 221 + " no"
    _reseal(sources[0])
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = _quote_response(quote_manifest, sources)
    response["quotes"][0]["exact_quote"] = "no"
    artifact = finalize_quotes(quote_manifest, sources, response)
    assert artifact["source_groups"][0]["rows"][0]["exact_quote"] == "no"


def test_runner_three_stage_round_trip_is_deterministic_and_no_provider(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 4)
    spec["sources"] = [
        {"source_id": "full-corpus", "packet_path": "packet.json", "bundle_path": "bundle.json"}
    ]
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    prompt = tmp_path / "relation-prompt.txt"
    schema = tmp_path / "relation-schema.json"
    manifest_path = tmp_path / "selection-manifest.json"
    prepared = prepare_evidence_selection_run(
        spec_path=spec_path, prompt_out=prompt, response_schema_out=schema, manifest_out=manifest_path
    )
    manifest = json.loads(manifest_path.read_text())
    candidates = _candidate_rows(sources, spec)
    relation_path = tmp_path / "relation-response.json"
    relation_path.write_text(json.dumps(_relation_response(candidates)), encoding="utf-8")
    quote_prompt = tmp_path / "quote-prompt.txt"
    quote_schema = tmp_path / "quote-schema.json"
    quote_manifest_path = tmp_path / "quote-manifest.json"
    relation_final = finalize_evidence_selection_relations_run(
        manifest_path=manifest_path,
        response_path=relation_path,
        quote_prompt_out=quote_prompt,
        quote_schema_out=quote_schema,
        quote_manifest_out=quote_manifest_path,
    )
    quote_manifest = json.loads(quote_manifest_path.read_text())
    quote_response_path = tmp_path / "quote-response.json"
    quote_response_path.write_text(json.dumps(_quote_response(quote_manifest, sources)), encoding="utf-8")
    artifact_path = tmp_path / "artifact.json"
    completed = finalize_evidence_selection_quotes_run(
        selection_manifest_path=manifest_path,
        quote_manifest_path=quote_manifest_path,
        response_path=quote_response_path,
        artifact_out=artifact_path,
    )
    assert prepared["model_api_calls"] == relation_final["model_api_calls"] == completed["model_api_calls"] == 0
    first = json.loads(artifact_path.read_text())
    second = finalize_quotes(quote_manifest, sources, _quote_response(quote_manifest, sources))
    assert first == second
