from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from judgment.phase_a_evidence_consumer import EvidenceConsumerError
from judgment.phase_a_evidence_selection import (
    SELECTION_SPEC_VERSION,
    _candidate_rows,
    _bucket_priority,
    _numeric_engagement,
    _select_groups,
    _source_venue,
    finalize_quotes,
    finalize_relations_prepare_quotes,
    prepare_evidence_selection,
)
from runners.run_semantic_evidence_integration import (
    finalize_evidence_selection_quotes_run,
    finalize_evidence_selection_relations_run,
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


def _quote_response(quote_manifest: dict, sources: list[dict]) -> dict:
    bodies = {
        row["evidence_id"]: row["text"]
        for row in sources[0]["bundle"]["evidence_units"]
    }
    return {
        "quotes": [
            {
                "selected_id": row["selected_id"],
                "quote_status": "quote_available",
                "exact_quote": bodies[row["evidence_id"]],
            }
            for row in quote_manifest["selected_rows"]
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
    if mutation == "overlength":
        for unit in sources[0]["bundle"]["evidence_units"]:
            unit["text"] = "x" * 400
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
    response = {
        "quotes": [
            {"selected_id": quote_manifest["selected_rows"][0]["selected_id"], "quote_status": "quote_unavailable", "exact_quote": None}
        ]
    }
    artifact = finalize_quotes(quote_manifest, sources, response)
    row = artifact["source_groups"][0]["rows"][0]
    assert row["quote_status"] == "quote_unavailable"
    assert row["source_body_present"] is False
    assert row["quote_unavailable_cause"] == "source_body_unavailable"
    assert row["normalized_meaning"]


def test_quote_unavailable_from_an_available_body_is_distinguishable_from_a_missing_body(tmp_path: Path) -> None:
    spec, sources = _write_source(tmp_path, 1)
    _, _, manifest = prepare_evidence_selection(spec, sources)
    _, _, quote_manifest = finalize_relations_prepare_quotes(
        manifest, sources, _relation_response(_candidate_rows(sources, spec))
    )
    response = {
        "quotes": [
            {"selected_id": quote_manifest["selected_rows"][0]["selected_id"], "quote_status": "quote_unavailable", "exact_quote": None}
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
    response = {
        "quotes": [
            {
                "selected_id": quote_manifest["selected_rows"][0]["selected_id"],
                "quote_status": "quote_available",
                "exact_quote": "My lips burn… only after this shade.",
            }
        ]
    }
    artifact = finalize_quotes(quote_manifest, sources, response)
    output_row = artifact["source_groups"][0]["rows"][0]
    assert output_row["exact_quote"] == response["quotes"][0]["exact_quote"]
    assert output_row["quote_unavailable_cause"] is None


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
    response = {
        "quotes": [
            {"selected_id": row["selected_id"], "quote_status": "quote_available",
             "exact_quote": "Body substituted after"}
            for row in quote_manifest["selected_rows"]
        ]
    }
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
    material_positive: bool | None = True,
    protected_lanes: list[str] | None = None,
    engagement_status: str = "engagement_available",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "layer": "truth_support",
        "relation": relation,
        "reason_code": "test",
        "scoped_independence_key": origin,
        "source_role": "community_post",
        "source_venue": "reddit",
        "engagement_kind": "reddit_points",
        "engagement_raw_value": 10,
        "engagement_material_positive": material_positive,
        "engagement_status": engagement_status,
        "conditions": [],
        "protected_lanes": protected_lanes or [],
    }


def test_same_origin_support_counter_and_quiet_reservations_display_three_rows_under_cap() -> None:
    rows = [
        _selection_row("support", relation="support"),
        _selection_row("counter", relation="counter"),
        _selection_row("quiet", relation="adjacent", material_positive=False),
    ]
    selected = _select_groups(rows, "truth_support", 10)
    assert {row["candidate_id"] for row in selected} == {"support", "counter", "quiet"}
    assert {"relation:support", "relation:counter", "quiet"} <= set(
        selected[0]["origin_required_display_lanes"]
    )


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
    sources[0]["bundle"]["evidence_units"][0]["text"] = f"before {quote} after"
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
    sources[0]["bundle"]["evidence_units"][0]["text"] = "The exact answer was no."
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
