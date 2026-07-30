"""Version-bump gate: derivation-policy modules cannot change silently.

Every consumption-seam obligation envelope enumerates version tokens (and
named constants) whose job is to re-surface committed packets when policy
changes. But the tokens only work if humans remember to bump them — until now
that discipline was COMMENT-BOUND (the standing residual named in every
catch-up adjudication: change ``cleaning/fragrantica.py`` internals without
bumping a version and no packet ever re-derives).

This gate makes the discipline mechanical: each derivation-policy module's
LF-normalized source hash is pinned here. Changing a pinned module fails CI
with a directed ritual instead of drifting silently:

1. Decide whether the change is OUTPUT-SHAPING (could any derived byte,
   selection, status, or ack fingerprint differ for the same committed raw?).
2. If output-shaping: bump the module's version token(s) named below — that
   re-fingerprints obligations and re-surfaces every committed packet, which
   is exactly the seam's S3 behavior.
3. Update the pin here either way, stating the decision in the commit.

Deliberately noisy: every change to these modules forces the conscious
decision that comments used to beg for. Modules pinned = the implementation
modules of every derivation whose version tokens appear in a
``_packet_obligation`` envelope (plus ``fragrance_review_lake.py`` and
``transcript_product_lake.py``, whose projection/write internals currently
ride sibling tokens — the named weak-envelope residuals).
"""
from __future__ import annotations

import hashlib

from data_lake.inventory import HARNESS_ROOT as _HARNESS_ROOT

# module path -> (version token(s) the changer must consider, pinned sha256 of
# LF-normalized source bytes).
POLICY_MODULE_PINS: dict[str, tuple[tuple[str, ...], str]] = {
    "capture_spine/creator_profile_current/tiktok_comment_attention_producer.py": (
        (
            "COMMENT_ATTENTION_RECIPE_VERSION",
            "COMMENT_ATTENTION_PRODUCER_SCHEMA_VERSION",
            "COMMENT_ATTENTION_POLICY_FINGERPRINT",
        ),
        # Output-shaping: temporal pairing, amplification/rank context, and the
        # cid-less mechanics fix now ride the producer's v1 recipe/schema tokens.
        "38def9d04a913acd1818be5194d23122f51c182ca0f59bfdf0859606b0e2dcd6",
    ),
    "capture_spine/creator_profile_current/tiktok_grid_observation_producer.py": (
        (
            "TIKTOK_GRID_OBSERVATION_POLICY_VERSION",
            "TIKTOK_GRID_OBSERVATION_PRODUCER_SCHEMA_VERSION",
            "TIKTOK_GRID_OBSERVATION_POLICY_FINGERPRINT",
            "TIKTOK_PROFILE_METRIC_OBSERVATION_POLICY_VERSION",
            "TIKTOK_PROFILE_METRIC_OBSERVATION_PRODUCER_SCHEMA_VERSION",
            "TIKTOK_PROFILE_METRIC_OBSERVATION_POLICY_FINGERPRINT",
        ),
        # Output-shaping profile v0 adds two deterministic exact-or-unavailable
        # account metric records; incumbent per-video set bytes remain unchanged.
        "30dae4e4fd3f51621ff6442498de89d48f5b0e7c7b064d31179fe49b8d02d905",
    ),
    "cleaning/_shared.py": (
        (
            "the cleaning method / producer schema tokens of all three cleaning "
            "lanes (fragrantica, parfumo, basenotes) -- shared helper home",
        ),
        # Initial pin: byte-identical helpers consolidated out of the three
        # cleaning adapters and *_lake modules; not output-shaping.
        # Pin bumped: raw_refs None-first sort key (bugfix -- mixed None/str ref
        # keys raised TypeError; previously-successful inputs order identically),
        # not output-shaping.
        # Output-shaping hard cut: source anchors replace raw/projection sibling
        # refs; Cleaning core/method and producer tokens are bumped below.
        "648fa0bbffa9b69fbb6d4a28e396426ddb0e69fdd5a587f42eac40cf2edf7543",
    ),
    "cleaning/basenotes.py": (
        ("BASENOTES_CLEANING_METHOD_ID (cleaning/basenotes_lake.py)",),
        # Admission-shaping v1: user-cleared persistent Chrome replaces the retired proxy surface.
        # Pin bumped: byte-identical helper dedup onto cleaning/_shared.py; not output-shaping.
        # Output-shaping: current content adapts directly under Cleaning and
        # historical raw uses the contained decoder; method token bumped to v2.
        "81e40f663c427904d44c3c78f67f7d90083c2871fce1c3bc4d7a46ff5466571b",
    ),
    "cleaning/basenotes_lake.py": (
        (
            "BASENOTES_AUDIT_PACK_PRODUCER_SCHEMA_VERSION",
            "BASENOTES_SILVER_PRODUCER_SCHEMA_VERSION",
            "BASENOTES_CLEANING_METHOD_ID",
        ),
        # Cleaning method v1 re-fingerprints obligations for the changed source admission.
        # Pin bumped: byte-identical helper dedup onto cleaning/_shared.py and
        # data_lake/canonical_json.py; not output-shaping.
        # Output-shaping lineage/handle change; audit, Silver, and Cleaning
        # method tokens are bumped.
        "6bb64954a4f7216e0ee31875d98926116bb0ee071cb1bd8b1bdd58cdfaac9089",
    ),
    "cleaning/fragrantica.py": (
        ("FRAGRANTICA_CLEANING_METHOD_ID (cleaning/fragrantica_lake.py)",),
        # Output-shaping: projection-v1 residual names change raw-pull-required output;
        # the cleaning method token is bumped to v1.
        # Output-shaping direct-content adaptation; Cleaning method bumped v2.
        "b59b41a75ea5e886f432894617012adcd1653379b97fa4d7e74debf0fe601f80",
    ),
    "cleaning/fragrantica_lake.py": (
        (
            "FRAGRANTICA_AUDIT_PACK_PRODUCER_SCHEMA_VERSION",
            "FRAGRANTICA_SILVER_PRODUCER_SCHEMA_VERSION",
            "FRAGRANTICA_SILVER_METRIC_PRODUCER_SCHEMA_VERSION",
            "FRAGRANTICA_REVIEW_VOTE_POLICY_VERSION",
            "FRAGRANTICA_CLEANING_METHOD_ID",
        ),
        # Output-shaping: FRAGRANTICA_CLEANING_METHOD_ID v1 re-fingerprints
        # obligations for the projection-v1 residual vocabulary.
        # Output-shaping lineage/handle change; audit, text, metric, and method
        # producer tokens are bumped.
        "68cbbfc04fa04ef069a770955b768fe0d7a8f9d71f35e35e9b63f3768d456aea",
    ),
    "cleaning/models.py": (
        ("CLEANING_CORE_VERSION",),
        # Output-shaping handle contract: source anchors replace raw/projection
        # sibling refs, so CLEANING_CORE_VERSION is bumped to v1.
        "5c8cbf0e8cd0becd33bac0fb99f78497b423040dd7d83c6cdc9d9bac9c579c63",
    ),
    "cleaning/parfumo.py": (
        ("PARFUMO_RATING_CARRY_RULE", "PARFUMO_CLEANING_METHOD_ID (cleaning/parfumo_lake.py)"),
        # Pin bumped: byte-identical helper dedup onto cleaning/_shared.py; not output-shaping.
        # Output-shaping direct-content adaptation; Cleaning method bumped v1.
        "4454d22c45ad9082126bcb45069166f17609120df4c8881945c9c914990a05e1",
    ),
    "cleaning/parfumo_lake.py": (
        (
            "PARFUMO_AUDIT_PACK_PRODUCER_SCHEMA_VERSION",
            "PARFUMO_SILVER_PRODUCER_SCHEMA_VERSION",
            "PARFUMO_SILVER_METRIC_PRODUCER_SCHEMA_VERSION",
            "PARFUMO_CLEANING_METHOD_ID",
        ),
        # Pin bumped: byte-identical helper dedup onto cleaning/_shared.py and
        # data_lake/canonical_json.py; not output-shaping.
        # Output-shaping lineage/handle change; audit, text, metric, and method
        # producer tokens are bumped.
        "49d7325412f50e08d964d74ab36693cd42a3417c6949a721f3c1aae6a3ba1a8d",
    ),
    "cleaning/transcript_product_extractor.py": (
        ("EXTRACTOR_RUBRIC_VERSION",),
        # Import-only transport relocation; output-shaping rubric is unchanged.
        "45a1878754192b6cab344fc11d74770851e19c49f46741947e7ac3378136054f",
    ),
    "cleaning/transcript_product_lake.py": (
        ("EXTRACTOR_RUBRIC_VERSION (cleaning/transcript_product_extractor.py)", "PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION (record-shape token; weak-envelope residual closed)"),
        # Output-shaping: the official Silver envelope is retained, while durable
        # record/completion identity now binds the full policy fingerprint; the
        # PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION bump to v2 re-surfaces V1 records.
        "6885729bc1b5bee6b250ce2d40f4b3bd7ca66e225fbbc6cc3c6c5649dd1afbef",
    ),
    "ecr/deriver.py": (
        ("ECR_DERIVER_VERSION",),
        "b94920e25627537b1cca0503cad52130982de3f5d9a53122e14978912b27b273",
    ),
    "source_capture/retail_pdp_projection.py": (
        (
            "RETAIL_PDP_PROJECTION_VERSION",
            "SEPHORA_PDP_PARSER_VERSION",
            "LUCKYSCENT_PDP_PARSER_VERSION",
            "NORDSTROM_PDP_PARSER_VERSION",
            "ULTA_PDP_PARSER_VERSION",
            "TARGET_PDP_PARSER_VERSION",
            "AMAZON_PDP_PARSER_VERSION",
        ),
        # Output-shaping: Sephora v2 adds the full product subtree, rendered UI
        # substrate, and explicit loss/residual fields; the shared projection
        # token moves to v1 so committed raw packets can re-surface. Nordstrom
        # parser v4 / content schema v2 are output-shaping: retain the exact
        # target initial product subtree, full SKU/OOS/media inventory, enriched
        # review fields, standard coverage, and an explicit omission ledger.
        # Nordstrom parser v5 is output-shaping: retain source-visible reviewed
        # size/color and fail closed on newly exposed unsupported card fields.
        # Known v1-v4 Nordstrom content packets remain readable.
        # Hard-cut plumbing only in this parser module: persisted Projection
        # writers were removed, while extracted and legacy-decoded row semantics
        # remain equivalent. Parser/projection tokens therefore stay unchanged.
        # Luckyscent source-shape admission now accepts either the current single
        # ProductGroup block or the earlier redundant ProductGroup+Product pair.
        # Both carry the same required product/offer/review semantics, so the
        # retailer parser token and shared projection token stay unchanged.
        # Ulta parser v1 adds its retailer-owned canonical content schema and
        # URL-SKU-bound offer/review extraction while omitting the unrelated
        # Apollo loader envelope. The shared projection row/Silver semantics
        # remain unchanged; historical raw decoding remains available. The
        # post-review correction restores the pre-flip raw fallback for
        # apollo_requested_sku while keeping content URL-SKU-bound, so v1 raw
        # semantics and raw/content Silver equivalence remain intact.
        # Output-shaping Sephora v3 stores duplicated product and interaction
        # fields once, proves exact source-state reconstruction, and preserves
        # unknown product-root fields automatically.
        # Output-shaping Ulta parser/schema v2 retains the target-bound Apollo
        # product module subtree (page-declared public display keys redacted),
        # every source-ordered variant state with fail-loud selected/price/
        # count/product-binding checks, and an explicit module retention
        # inventory; non-target rails and shell envelopes stay unretained. No
        # committed v1 Ulta content packets exist, so no re-surface is needed.
        # Target parser/schema v1 is purely additive: it adds the retailer-owned
        # canonical content schema, the __NEXT_DATA__ CDUI core-datasource depth
        # extractor, body-free review identity rows, a declared-module hydration
        # inventory, and a fail-loud guest-session-secret refusal. No existing
        # retailer extractor, shared projection row, or Silver semantic changes,
        # so RETAIL_PDP_PROJECTION_VERSION and the Sephora/Luckyscent/Nordstrom/
        # Ulta tokens stay unchanged and no committed packet re-surfaces.
        # Delegated-review hardening on the same Target v1: the shared
        # _target_variant_offer_fields price extractor is now scoped to Target's
        # ProductDetailPrice module instead of matching page-globally, which the
        # legacy raw decoder also reaches. Checked against every committed Target
        # PDP raw packet with a DOM (01KXR823YS3V5M9E01QXP71ETC,
        # 01KXWMXEYB58SMVSJT80XJAP9D, 01KXWMTJXN7JX775Q17D24E8NT): old and new
        # both yield 14.69, so no committed packet re-surfaces and the shared
        # projection token stays unchanged. Future captures can differ by design
        # — that is the defect being fixed, not a re-surface.
        # Amazon content schema v1 is additive. Parser v2 is output-shaping: it
        # inventories data-feature modules whose class attribute contains
        # `celwidget` instead of silently omitting class-list forms, and extends
        # the no-secret assertion to JSON-carried session/CSRF values. Historical
        # Amazon parser-v1 content records remain explicitly readable; the
        # shared Projection token and other retailer parser tokens stay unchanged.
        # Output-shaping Target parser v2: a price that renders on the page but does
        # not bind to the target's ProductDetailPrice module is now recorded as an
        # unbound-price disagreement instead of page absence, which would be a false
        # statement while the capture profile's own sufficiency gate requires a
        # visible price. Residuals reach Cleaning, so committed Target content
        # packets re-surface. Schema stays content_v1: values change, shape does
        # not. Historical parser_v1 packets remain readable via the widened Literal
        # and the current-extractor exemption. v2 final behavior: a rendered price
        # the parser cannot bind to the target's ProductDetailPrice module forces
        # raw fallback rather than a residual, so the DOM survives for diagnosis.
        # Output-shaping Sephora v4 preserves absent canonical fields as absent
        # during compaction instead of re-surfacing them as explicit null/empty
        # values. Existing v1-v3 content records remain loader-readable.
        "6008a88d86695f7f39ff828fe9d06d9be1ccc159fb3af0102675736d27ed7353",
    ),
    "source_capture/basenotes_projection.py": (
        ("BASENOTES_PROJECTION_VERSION",),
        # Projection v1 rejects the retired proxy surface and admits the proven persistent-Chrome surface.
        # Pin bumped: helper dedup onto source_capture/projection_shared.py plus adoption of the
        # containment-guarded shared packet reader (security hardening: path traversal); not output-shaping.
        # Pin bumped: family-owned content-record schema/parser and JSON-pointer packet binding.
        # Raw/legacy row semantics remain equivalent, so BASENOTES_PROJECTION_VERSION stays v1;
        # content and parser behavior carry separate version constants.
        # Removed persisted writer and unbound packet scaffolding; content and
        # historical decoded rows are unchanged, so the family token stays v1.
        "92a674be3efa82d11eb27cc005f683c7756960b31e9df9445f4746222954b46e",
    ),
    "source_capture/fragrance_review_coverage.py": (
        ("FRAGRANCE_REVIEW_COVERAGE_VERSION", "FRAGRANCE_REVIEW_RECORD_SCHEMA_VERSION (record-shape token; weak-envelope residual closed)"),
        # Output-shaping: v1 retains Yotpo's exact incentivized state, incentive
        # type, and reviewer-declared age range in the existing extensible
        # source_visible_fields envelope. The record schema remains v0 because
        # no model field or required shape changed.
        "874121d92a71dd7924586affcff31d11334fd9e8d61c90294fec1473024b549e",
    ),
    "source_capture/fragrance_review_lake.py": (
        ("FRAGRANCE_REVIEW_COVERAGE_VERSION (source_capture/fragrance_review_coverage.py; weak-envelope residual)",),
        "f5eeaf437d3e71cab942315228391a238fce923bdae4a935018f6d97508ac089",
    ),
    "source_capture/fragrantica_projection.py": (
        ("FRAGRANTICA_PROJECTION_VERSION",),
        # Output-shaping: projection v1 admits the two Fragrantica CloakBrowser
        # surfaces and tightens body selection plus residual vocabulary. The
        # family-owned content record adds parser-versioned retention and
        # JSON-pointer rebinding without another projection semantic change.
        # Removed persisted writer and unbound packet scaffolding; content and
        # historical decoded rows are unchanged, so the family token stays v1.
        "5ab86e7f97f2c80d4bb56c7b4491790c1cd2f0fb1e0d0cbbe6276fb5518125d1",
    ),
    "source_capture/ig_reels_grid_projection.py": (
        ("IG_REELS_PROJECTION_VERSION",),
        # Pin bumped: byte-identical _append_residual_once dedup onto
        # harness_utils.append_residual_once; not output-shaping.
        "cec6047919c73bc954b07ea15f3596929e511b11f851ed70177da6d58645aa11",
    ),
    "source_capture/parfumo_projection.py": (
        ("PARFUMO_PROJECTION_VERSION",),
        # Pin bumped: corrected a latent in-memory hash-basis literal; the anchor is
        # discarded before serialization, so projection outputs remain unchanged.
        # Removed persisted writer and unbound packet scaffolding; content and
        # historical decoded rows are unchanged, so the family token stays v0.
        "cc544bb46bc93d4813fc1162d3aec31daaf019011e7a013372c98d684b18cc10",
    ),
    "source_capture/projection_shared.py": (
        (
            "the projection version tokens of its adopting surfaces "
            "(basenotes, fragrantica, parfumo, ig, reddit, retail grid, "
            "retail PDP) -- shared helper home",
        ),
        # Initial pin: byte-identical helpers consolidated out of the projection
        # surfaces; not output-shaping.
        # Pin bumped: added canonical_old_reddit_thread_url, the body adopted
        # from grid_projection's byte-identical private copy; not output-shaping.
        # Pin bumped: corrected the retained-copy docstring to distinguish the
        # byte-identical candidate-intake copy from the divergent screening copy
        # (post-merge review W6-1); docstring-only, not output-shaping.
        # Pin bumped: added canonical_www_reddit_thread_url for the new-Reddit
        # listing surface, after old.reddit stopped serving this client
        # (2026-07-30). Purely additive -- no existing line changed and the new
        # function has exactly one caller, the new www projection, which carries
        # its own parser version and has no committed packets. No adopting
        # surface can emit a different byte for the same committed raw, so their
        # version tokens are deliberately NOT bumped; not output-shaping.
        "6a689ccf696712dc28a39009e97eaf3fe31824325d8b5804a79c7a33862a7910",
    ),
    "source_capture/transcript/asr_packet.py": (
        ("transcriber_policy envelope (run_asr_transcript_catchup)", "TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION (record-shape token; weak-envelope residual closed)"),
        "4d99991d5b27c82b8c22981dcddaa2ebd516249cab706e1016ea9379c44bb21e",
    ),
    "source_capture/transcript/audio_asr.py": (
        ("transcriber_policy envelope defaults (model/compute/decode params are CLI-enveloped)",),
        # Pin bumped: added a bounded yt-dlp subprocess timeout (liveness guard). NOT output-shaping
        # -- only the hang-failure path changes; a successful bestaudio download derives identically.
        "9e778b107a3e3deec7fee83c0dc06b5cb7dc5a36e71e4d8c48393564abb98b09",
    ),
    "source_capture/transcript/ig_reels_audio_packet.py": (
        ("transcriber_policy envelope (run_asr_transcript_catchup)", "TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION (record-shape token, shared from asr_packet.py; weak-envelope residual closed)"),
        # Pin bumped: added a bounded yt-dlp subprocess timeout (liveness guard). NOT output-shaping
        # -- only the hang-failure path changes; a successful Reel bestaudio download derives identically.
        "3f2bcd15d3f201fc30fe066d4ebfd0e6b2c592e7e7a85ad9209253095204ee57",
    ),
    "runners/run_tiktok_product_extract.py": (
        ("EXTRACTOR_RUBRIC_VERSION", "TikTok cue-normalization and packet-obligation policy"),
        # Output-shaping obligation change: record schema version now re-surfaces
        # packets for the envelope migration even when the extraction rubric is unchanged.
        "054645d4501ed6084197efa3e34620b54dda7bb80e22ab6dda7907e23cc5414e",
    ),
}

# Record-shape schema tokens close the weak-envelope class only if they are
# actually stamped into newly written records. The module hash pins above force a
# conscious bump/no-bump decision, but this direct guard catches a pin update that
# accidentally drops the payload field itself.
RECORD_SCHEMA_TOKEN_FIELD_SITES: dict[str, tuple[str, ...]] = {
    "cleaning/transcript_product_lake.py": (
        'PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION = "transcript_product_mentions_record_v3"',
        '"record_schema_version": PRODUCT_MENTIONS_RECORD_SCHEMA_VERSION',
    ),
    "source_capture/fragrance_review_coverage.py": (
        'FRAGRANCE_REVIEW_RECORD_SCHEMA_VERSION = "fragrance_review_coverage_record_v0"',
        'record_schema_version: Literal["fragrance_review_coverage_record_v0"]',
        "FRAGRANCE_REVIEW_RECORD_SCHEMA_VERSION",
    ),
    "source_capture/transcript/asr_packet.py": (
        'TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION = "transcript_asr_record_v0"',
        '"record_schema_version": TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION',
    ),
    "source_capture/transcript/ig_reels_audio_packet.py": (
        "from source_capture.transcript.asr_packet import TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION",
        '"record_schema_version": TRANSCRIPT_ASR_RECORD_SCHEMA_VERSION',
    ),
}

def _lf_sha256(relative_path: str) -> str:
    data = (_HARNESS_ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_record_schema_tokens_are_stamped_by_writers() -> None:
    missing = {}
    for module_path, required_tokens in sorted(RECORD_SCHEMA_TOKEN_FIELD_SITES.items()):
        source = (_HARNESS_ROOT / module_path).read_text(encoding="utf-8")
        missing_tokens = [token for token in required_tokens if token not in source]
        if missing_tokens:
            missing[module_path] = missing_tokens

    assert not missing, (
        "Record-shape schema token(s) are declared in a policy-pinned module but "
        "are no longer stamped into the record payload/model field. Restore the "
        "record_schema_version write or remove the weak-envelope closure claim: "
        f"{missing}"
    )

def test_policy_modules_match_their_pins() -> None:
    drifted = {}
    for module_path, (version_tokens, pinned) in sorted(POLICY_MODULE_PINS.items()):
        actual = _lf_sha256(module_path)
        if actual != pinned:
            drifted[module_path] = {"pinned": pinned, "actual": actual, "consider": version_tokens}

    assert not drifted, (
        "Derivation-policy module(s) changed. This is not (necessarily) wrong — but the "
        "version-bump decision may no longer be skipped:\n"
        "  1. Is the change OUTPUT-SHAPING (any derived byte / selection / ack fingerprint "
        "could differ for the same committed raw)?\n"
        "  2. If yes: bump the version token(s) listed under 'consider' so committed "
        "packets re-surface (seam S3 behavior).\n"
        "  3. Update the pin here either way and state the decision in the commit body.\n"
        f"{drifted}"
    )


def test_pinned_modules_exist() -> None:
    missing = [
        module_path
        for module_path in POLICY_MODULE_PINS
        if not (_HARNESS_ROOT / module_path).is_file()
    ]
    assert not missing, (
        "POLICY_MODULE_PINS lists module(s) that no longer exist — a retired policy module "
        f"needs its pin retired deliberately, with its lane's disposition: {missing}"
    )
