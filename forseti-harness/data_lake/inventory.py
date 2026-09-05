"""Deterministic Data Lake touchpoint inventory (the A1 inventory gate core).

Single source for the AST discovery the seam-coverage contract test seeds and
for the durable, checked-in touchpoint inventory record
(``lake_touchpoint_inventory_v0.json``). The record enumerates, from tracked
source only:

1. raw-packet writers (runner seams, declared orchestrators, and the recursive
   ``source_capture`` writer-function closure);
2. non-raw lake touchpoints (derived/ack/silver/catalog call sites);
3. explicit exclusions, each carrying a reason;
4. unknowns, each carrying an owner disposition (a pending unknown fails the
   gate; dispositions are owner-attributable via the human-gated PR merge,
   never self-certified);
5. the A2 serialization-fork impact tag per entry;
6. an ``identity_binding`` declaration per runner seam: how the runner binds
   SERVED content to the REQUESTED subject before a packet is committed
   (``bound`` with a mechanism), or an honest ``unbound``/``not_applicable``
   posture with a reason. Declared in ``RUNNER_IDENTITY_BINDINGS``, never
   auto-discovered; a discovered runner without a declaration fails the gate,
   so the wrong-subject-attribution question (F-01 in
   ``docs/review-outputs/youtube_rss_monitor_delegated_adversarial_code_review_v0.md``)
   is mandatory at build time for every new capture runner. The declaration
   documents the current posture; ``unbound`` is a visible acknowledged gap,
   not a pass.

The fork-impact tag is deterministic routing metadata for the deferred A2
decision (Manifest v2 vs manifest-equivalent packet index), assigned by
surface class, never per-entry judgment:

- raw-packet writers produce packet manifests -> ``manifest_shape``;
- generated catalog / Attachment Record read surfaces consume or rebuild the
  manifest-equivalent generated index -> ``packet_index``;
- derived/ack append and record-set/lane-path surfaces touch neither shape ->
  ``none``.

The checked-in record is a generated inventory of code surfaces. It is never
lake authority, never lives under the data root, and is regenerated and
diffed by ``tests/contract/test_data_lake_inventory_gate.py``; updating it is
a deliberate, reviewed edit. It does not select A2, a backend, or claim
coverage beyond source-visible discovery.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
RUNNERS_DIR = HARNESS_ROOT / "runners"
SOURCE_CAPTURE_DIR = HARNESS_ROOT / "source_capture"

INVENTORY_VERSION = 2
INVENTORY_PATH = HARNESS_ROOT / "data_lake" / "lake_touchpoint_inventory_v0.json"

DIRECT_PACKET_WRITER_TOKENS = {"write_local_source_capture_packet", "stage_and_write_packet"}
PACKET_WRITER_NAME_RE = re.compile(r"write_.*_packet$")
ENV_OUTPUT_OMITTED_TOKENS = (
    'args.output is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))',
    'output_directory is None and (os.environ.get("FORSETI_DATA_ROOT") or os.environ.get("ORCA_DATA_ROOT"))',
)
EXPLICIT_PAIR_REJECT_TOKENS = (
    "args.output is not None and args.data_root is not None",
    "output_directory is not None and args.data_root is not None",
    "add_mutually_exclusive_group",
)
# Shared runner scaffold (runners/_scaffold.py): its resolve_output_root owns
# the env-fallback read gated on --output being omitted, the explicit
# --output + --data-root rejection, and DataLakeRoot.resolve. A runner that
# imports and calls it carries those seam parts without the literal per-file
# tokens above.
SCAFFOLD_MODULE = "runners._scaffold"
SCAFFOLD_RESOLVER_NAME = "resolve_output_root"

# Packet-producing runners that intentionally do NOT route into the lake yet.
# Each MUST carry a reason; entries surface in the inventory record as
# exclusions and in the seam test as acknowledged-unsynced runners.
KNOWN_UNSYNCED: dict[str, str] = {}

# Packet-producing runners whose live-acquisition safety boundary requires an
# explicit data-root selection rather than ambient automatic admission. These
# runners still carry a real lake seam; the declaration prevents the seam
# detector from mistaking help text for a FORSETI_DATA_ROOT read.
EXPLICIT_DATA_ROOT_RUNNERS: dict[str, str] = {
    "run_source_capture_tiktok_live_batch_probe.py": (
        "live acquisition stages first; durable lake admission requires explicit --data-root"
    ),
    "run_source_capture_tiktok_creator_onboarding.py": (
        "supervised live onboarding stages first; durable lake admission requires explicit --data-root"
    ),
    "run_source_capture_tiktok_daily_heartbeat.py": (
        "live grid capture is invoked by the operator/control wrapper, which supplies an "
        "explicit output_root or resolved data_root; this adapter does not use ambient admission"
    ),
    "run_source_capture_sephora_onboarding.py": (
        "live structured Sephora acquisition consumes a committed parent packet and "
        "requires explicit append-only lake admission"
    ),
    "run_source_capture_target_onboarding.py": (
        "live structured Target acquisition consumes a committed parent packet and "
        "requires explicit append-only lake admission"
    ),
    "run_source_capture_amazon_review_onboarding.py": (
        "local Amazon review adaptation consumes a committed parent packet and "
        "requires explicit append-only lake admission"
    ),
    "run_source_capture_ulta_onboarding.py": (
        "live structured Ulta PowerReviews acquisition consumes a committed parent "
        "packet and requires explicit append-only lake admission"
    ),
}
# Orchestrator runners that forward data_root into raw-packet sub-runners
# instead of calling a packet writer directly. Declared, not auto-discovered.
BRONZE_PACKET_ORCHESTRATORS: dict[str, tuple[str, ...]] = {
    "run_fragrantica_mgt_capture.py": ("http_runner", "cloakbrowser_runner"),
    "run_ig_reels_lane_orchestrator.py": ("grid_runner",),
    "run_kohls_unattended_capture.py": ("run_source_capture_realchrome_cdp_packet",),
}

# Identity-binding declaration for every runner_seams entry (direct packet
# writers AND declared orchestrators). Answers, per runner: how is SERVED
# content bound to the REQUESTED subject before a packet is committed?
#
#   {"status": "bound", "mechanism": ...}       a real served-content identity
#                                               check gates packet write
#   {"status": "unbound", "reason": ...}        the packet asserts a subject
#                                               beyond raw request provenance
#                                               without a served-content check
#                                               (visible acknowledged gap)
#   {"status": "not_applicable", "reason": ...} no subject identity beyond the
#                                               request itself is asserted
#                                               (fetch-of-URL provenance or
#                                               operator-declared admission)
#
# Every discovered Bronze-writing runner MUST have an entry; the inventory
# gate and the seam-coverage test both fail on a missing or shape-invalid
# declaration. Backfilled 2026-07-03 from a source read of each runner
# (including the source_capture fetch/writer path it delegates to).
RUNNER_IDENTITY_BINDINGS: dict[str, dict[str, str]] = {
    "run_basenotes_mgt_capture.py": {
        "status": "bound",
        "mechanism": (
            "before packet write, the bundle metadata requested_url and final_url must equal "
            "the caller-supplied Basenotes product URL, and the rendered DOM must contain the "
            "exact caller-bound product path plus Product/review/reviewBody JSON-LD markers; "
            "challenge-only content fails closed"
        ),
    },    "run_fragrance_review_lake_packet.py": {
        "status": "unbound",
        "reason": (
            "preserved bytes must match the companion receipt's capture-time "
            "body_sha256/body_byte_count witness (_verify_capture_witness, "
            "block-don't-fake), which binds bytes to the attested capture but not to "
            "the product subject: product_url attribution comes from the receipt or "
            "the --product-url override without a served-content identity check"
        ),
    },
    "run_fragrantica_mgt_capture.py": {
        "status": "not_applicable",
        "reason": (
            "orchestrator over URL-subject sub-runners (http_runner/cloakbrowser_runner): "
            "it shape-validates the requested Fragrantica product URL and forwards it; the "
            "sub-runner packets record requested and served final URLs and assert no "
            "subject identity beyond the URL"
        ),
    },
    "run_ig_reels_lane_orchestrator.py": {
        "status": "not_applicable",
        "reason": (
            "orchestrator that performs no acquisition of its own: grid capture owns the "
            "subject seam (see run_source_capture_ig_reels_grid_packet.py) and the "
            "orchestrator only enforces that downstream lanes target the same reel "
            "(explicit-selector split-brain guard)"
        ),
    },
    "run_parfumo_mgt_capture.py": {
        "status": "unbound",
        "reason": (
            "the direct-HTTP slot records requested/served final-URL provenance only; the "
            "targeted-rendered path admits operator-supplied local Chrome-extension "
            "artifacts attributed to the requested product URL with a browser-secret scan "
            "but no served-content identity check"
        ),
    },
    "run_reddit_subreddit_registry_lake.py": {
        "status": "not_applicable",
        "reason": (
            "no served content and no remote subject: the one migration packet preserves "
            "the exact bytes of the operator-named local registry JSON, and the baseline "
            "records bind those bytes by legacy_file_sha256, so the only asserted subject "
            "is the local file the operator supplied"
        ),
    },
    "run_source_capture_antiblock_http_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself: requested_url is preserved as "
            "source_locator and the served final_url on the slice; block-shell "
            "classification explicitly refuses to certify the body as source content; no "
            "subject identity beyond the URL is asserted"
        ),
    },
    "run_source_capture_archive_packet.py": {
        "status": "bound",
        "mechanism": (
            "verify_archive_body gates body preservation: the served snapshot's "
            "original-URL identity must match the requested URL "
            "(served_url_identity_mismatch) and the served time must satisfy the cutoff; "
            "a verification-failed body is not preserved as addressable content (G-002) "
            "and surfaces as attempt_failed plus a limitation"
        ),
    },
    "run_source_capture_ats_job_posting_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested public ATS board API URL: it is preserved as "
            "source_locator and the served board response is stored verbatim, and each "
            "posting slice's locator is the served jobUrl/applyUrl copied from that "
            "response; the packet claims fetched-URL provenance only. The operator-supplied "
            "company label (from the manual board registry) is an operator declaration, "
            "not a served-content identity check against the requested company"
        ),
    },
    "run_source_capture_authenticated_browser_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself: requested_url is preserved as "
            "source_locator and the served final_url on the slice; login-wall/challenge "
            "markers surface as limitations; content sufficiency is explicitly not asserted"
        ),
    },
    "run_source_capture_browser_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself: requested_url is preserved as "
            "source_locator and the served final_url on the slice; content sufficiency is "
            "explicitly not asserted"
        ),
    },
    "run_source_capture_cloakbrowser_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself (browser_snapshot shape with "
            "proxy-category disclosure): requested_url is preserved as source_locator and "
            "the served final_url on the slice; no subject identity beyond the URL is "
            "asserted"
        ),
    },
    "run_source_capture_realchrome_cdp_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself (real-Chrome-over-CDP browser_snapshot "
            "shape): requested_url is preserved as source_locator and the served final_url "
            "on the slice; access-block classification refuses to certify a block shell; no "
            "subject identity beyond the URL is asserted (any subject/currency admission is a "
            "caller-supplied source-detail-sufficiency check, not a runner-enforced binding)"
        ),
    },
    "run_kohls_unattended_capture.py": {
        "status": "bound",
        "mechanism": (
            "the PDP capture requires rendered visible text containing LipSoftie plus "
            "product-page Offer microdata with priceCurrency=USD, and the policy capture "
            "requires Kohl's exact US/APO/FPO-only shipping statement; either missing or "
            "access-blocked surface fails the one-shot job after preserving available evidence"
        ),
    },
    "run_source_capture_historical_packet.py": {
        "status": "bound",
        "mechanism": (
            "the ladder preserves a body only when the winning rung's verification "
            "passed: archive rungs verify the served snapshot's original-URL identity and "
            "served time against the requested URL/cutoff, and the publisher-history rung "
            "verifies the served revid/sha and timestamp (PH-01/PH-02); unverified "
            "outcomes stay locate-metadata-only with attempt_failed"
        ),
    },
    "run_source_capture_http_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested URL itself: requested_url is preserved as "
            "source_locator and the served final_url on the slice; the packet claims "
            "fetched-URL provenance only"
        ),
    },
    "run_source_capture_ig_calls_packet.py": {
        "status": "unbound",
        "reason": (
            "item slices are enumerated from the served profile page (within-capture "
            "consistency) and the served profile final_url is recorded, but the served "
            "profile's identity (og fields, web_profile_info username) is never compared "
            "to the requested account, so a redirected or mis-served profile would be "
            "committed under the requested locator"
        ),
    },
    "run_source_capture_ig_reels_audio_packet.py": {
        "status": "unbound",
        "reason": (
            "the packet asserts platform_shortcode and the canonical reel URL copied from "
            "the request; the yt-dlp download is selected by largest file rather than a "
            "served-id-keyed name and the audio bytes carry no observable identity to check"
        ),
    },
    "run_source_capture_ig_reels_deep_capture.py": {
        "status": "unbound",
        "reason": (
            "the public Reel render is requested by shortcode and exact rendered comment "
            "objects plus downloaded audio bytes are preserved, but the served page does "
            "not independently expose and bind a shortcode identity before packet admission"
        ),
    },
    "run_source_capture_ig_reels_grid_packet.py": {
        "status": "bound",
        "mechanism": (
            "the normalized requested handle is compared case-insensitively with the "
            "source-visible username parsed and preserved from web_profile_info before "
            "slice/packet/lake publication; missing, invalid, or mismatched served identity "
            "fails closed with a distinct diagnostic and no packet write"
        ),
    },
    "run_source_capture_junip_review_corpus.py": {
        "status": "bound",
        "mechanism": (
            "before packet write, the products response must expose remote product identities; "
            "every review must carry an embedded product remote_id; and the complete paginated "
            "review set must expose exactly the caller-bound expected store name and URL"
        ),
    },
    "run_source_capture_media_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subjects are the explicit asset URLs: each slice preserves the served "
            "final_url and per-asset metadata; the optional --source-locator is recorded "
            "as an operator declaration, not a verified subject"
        ),
    },
    "run_source_capture_packet.py": {
        "status": "not_applicable",
        "reason": (
            "no acquisition: packages operator-supplied local files under an "
            "operator-declared source locator (which may itself be unknown-with-reason); "
            "there is no runner-fetched served content to match"
        ),
    },
    "run_source_capture_price_payload_packet.py": {
        "status": "not_applicable",
        "reason": (
            "subject is the requested pricing/announcement URL set: chunk URLs are "
            "discovered from the served page's module-preload list (structural "
            "provenance) and certify_extraction is a content-integrity discriminator, not "
            "a subject identity claim beyond the URLs"
        ),
    },
    "run_source_capture_sephora_onboarding.py": {
        "status": "bound",
        "mechanism": (
            "before acquisition, a hash-verified parent packet must be retail_pdp and its "
            "Sephora linkStore productId must match the requested product URL; every returned "
            "question row must carry that productId and every review row must carry that "
            "productId or a SKU enumerated by the same parent product before projection succeeds"
        ),
    },
    "run_source_capture_target_onboarding.py": {
        "status": "bound",
        "mechanism": (
            "before acquisition, a hash-verified retail_pdp parent must bind the Target "
            "URL TCIN to the ProductDetailWebDatasourceCore TCIN and the admitted public "
            "Bazaarvoice deployment; every returned question and review row plus the "
            "included Bazaarvoice product must carry that same TCIN"
        ),
    },
    "run_source_capture_ulta_onboarding.py": {
        "status": "bound",
        "mechanism": (
            "before acquisition, a hash-verified retail_pdp parent must carry a "
            "confirmed unblocked ulta_us_market_assertion pin and bind the Ulta URL "
            "product id to the page-declared PowerReviews page_id; every returned "
            "review and question row must carry that page_id, and review_id must "
            "equal ugc_id on every review row before the summary succeeds"
        ),
    },
    "run_source_capture_amazon_review_onboarding.py": {
        "status": "bound",
        "mechanism": (
            "a hash-verified parent binds source and served Amazon URLs to one ASIN, "
            "requires an unblocked US pin plus USD marker, and admits only unique native "
            "review row ids inside labelled Amazon top-review sections"
        ),
    },
    "run_source_capture_tiktok_batch_packet.py": {
        "status": "unbound",
        "reason": (
            "creator_handle and creator_profile_url are checked for request "
            "self-consistency and grid-enrichment items with a mismatched authorUniqueId "
            "are dropped, but the admitted cadence rows are attributed to the requested "
            "creator without a served-content author check"
        ),
    },
    "run_source_capture_tiktok_grid_packet.py": {
        "status": "unbound",
        "reason": (
            "grid-only admission validates every preserved row's canonical video URL "
            "suffix against the artifact's creator_handle and tiktok video_id, but it "
            "admits an operator-supplied artifact without independently proving that "
            "TikTok served that creator/video authorship"
        ),
    },
    "run_source_capture_tiktok_live_batch_probe.py": {
        "status": "unbound",
        "reason": (
            "live probe validates requested creator/profile/video URL shape and can admit "
            "only sanitized page-owned staging through the TikTok batch gate, but the "
            "resulting packet is still attributed to the requested creator/video without "
            "an end-to-end served author identity proof"
        ),
    },
    "run_source_capture_tiktok_creator_onboarding.py": {
        "status": "unbound",
        "reason": (
            "onboarding binds grid metrics to source-visible creator rows and reuses the "
            "validated session across selected-video capture, but admitted comment/subtitle "
            "artifacts still lack an end-to-end served author identity proof"
        ),
    },
    "run_source_capture_tiktok_daily_heartbeat.py": {
        "status": "unbound",
        "reason": (
            "the frozen plan is stably keyed by platform_account_id and the grid seam "
            "checks author/DOM URLs plus canonical creator/video URL shape against the "
            "planned handle, but the served grid does not expose and verify the numeric "
            "platform_account_id; a stale handle-to-account roster binding remains visible"
        ),
    },
    "run_source_capture_tiktok_video_packet.py": {
        "status": "unbound",
        "reason": (
            "video-id format and canonical-URL shape are enforced and profile-list rows "
            "are filtered to the requested id, but the admitted comment/subtitle "
            "artifacts are attributed to the requested video without a served-content id "
            "check"
        ),
    },
    "run_source_capture_youtube_asr_packet.py": {
        "status": "bound",
        "mechanism": (
            "yt-dlp writes the downloaded audio under the SERVED video id (%(id)s output "
            "template) and download_audio accepts only the file named exactly "
            "<requested id>.*, so a mis-served id fails closed as a download failure; no "
            "additional served-metadata check is performed"
        ),
    },
    "run_source_capture_youtube_caption_packet.py": {
        "status": "bound",
        "mechanism": (
            "yt-dlp writes the caption track under the SERVED video id (%(id)s output "
            "template) and fetch_youtube_caption_artifacts accepts only "
            "<requested id>*.json3, so a mis-served id fails closed as no-caption; "
            "extract_info metadata (title/channel_id) is recorded without an independent "
            "check"
        ),
    },
    "run_source_capture_youtube_creator_onboarding.py": {
        "status": "bound",
        "mechanism": (
            "before packet write, identity comes from a served channel page exposing an "
            "immutable UC channel id, canonical handle, and display name; the evidence-video "
            "and channel-search routes additionally require a normalized display-name match "
            "against the requested creator plus agreement between the discovering surface's "
            "channel id and the served channel page's channel id, and fail closed on "
            "ambiguity, disagreement, or a display name with no comparable normalized form; "
            "the owner-supplied --profile-url route trusts the owner's locator and records "
            "display_name_mismatch as evidence instead of failing closed"
        ),
    },
    "run_source_capture_youtube_rss_monitor.py": {
        "status": "bound",
        "mechanism": (
            "_validate_parsed_channel_identity runs immediately after parsing: the served "
            "feed-level yt:channelId must match the requested roster channel (accepting "
            "the observed no-UC-prefix variant), any entry-level yt:channelId differing "
            "from the request fails, and missing feed identity fails closed; a mismatch "
            "is a visible per-channel failure with no packet write"
        ),
    },
    "run_source_capture_youtube_watch_packet.py": {
        "status": "bound",
        "mechanism": (
            "the requested 11-character video id is compared exactly with the id parsed "
            "from the source-visible served canonical URL immediately before packet/lake "
            "publication; unavailable or mismatched served identity fails closed with a "
            "distinct diagnostic and no packet write"
        ),
    },
}

IDENTITY_BINDING_STATUSES = ("bound", "unbound", "not_applicable")
# Which detail field each status must carry (single-sourced; the gate and the
# seam-coverage test both validate through identity_binding_problems below).
IDENTITY_BINDING_DETAIL_FIELDS = {
    "bound": "mechanism",
    "unbound": "reason",
    "not_applicable": "reason",
}

NON_RAW_LAKE_TOUCHPOINT_CALLS = {
    "append_record",
    "append_record_set",
    "append_silver_record",
    "append_silver_record_set",
    "catalog_coverage_census",
    "inspect_catalog",
    "is_record_set_complete",
    "lane_dir",
    "load_attachment_record_body",
    "rebuild_catalog",
    "record_path",
    "source_surface_catalog_rows",
}

# Surfaces that consume or rebuild the manifest-equivalent generated
# catalog/AR index; the A2 fork's packet-index branch would reshape these.
PACKET_INDEX_CALLS = {
    "catalog_coverage_census",
    "inspect_catalog",
    "load_attachment_record_body",
    "rebuild_catalog",
    "source_surface_catalog_rows",
}

A2_FORK_IMPACT_VALUES = ("manifest_shape", "packet_index", "none")

# --- silver/derived reader selection postures (V3: consumer-enumerated) ---------
# Every production file that walks derived lanes (detected via its `lane_dir`
# touchpoint or a direct traversal rooted at ``data_root.path / "derived"``) must
# declare HOW it selects among sibling records.
# The reader gate (tests/contract/test_silver_reader_selection_gate.py) keeps this
# registry exact, so a NEW reader cannot appear without declaring its posture.
# Postures classify observed behavior; they are not correctness verdicts.

SILVER_READER_POSTURES = (
    "selection_rule",       # binds a defined, tested sibling-selection rule
    "set_marker_pinned",    # reads exact record ids via completion markers
    "all_siblings",         # consumes every committed record, with a stated reason
    "fail_closed_singleton",  # requires exactly one record, raises otherwise
    "infrastructure",       # seam/index machinery, not a data consumer
)

# detection: "lane_dir" entries are enforced against the mechanical touchpoint
# census; "declared_free_walk" entries are enforced against direct derived-root
# traversal plus the narrow indirect/path-based census in the contract gate.
SILVER_READER_SELECTION_POSTURES: dict[str, dict[str, str]] = {
    "capture_spine/creator_profile_current/social_metric_history_reader.py": {
        "detection": "declared_free_walk",
        "posture": "selection_rule",
        "mechanism": "local:read_social_metric_history",
        "reason": "requires an explicit policy fingerprint and deterministic per-anchor record-id function; exact-policy by-key records only, with shared physical source verification and no latest-sibling guess",
    },
    "capture_spine/creator_profile_current/silver_metric_reader.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "local:select_latest_rollup_per_account",
        "reason": "select_latest_rollup_per_account: run-order primary, fail-closed on computed_at regression and unorderable ties (AR-04)",
    },
    "capture_spine/tiktok_creator_discovery_frontier/register_lake_writer.py": {
        "detection": "lane_dir",
        "posture": "all_siblings",
        "reason": "the actionable TikTok Frontier queue intentionally consumes every validated register from every non-tombstoned committed parent; root identities and Registry accounts are deduplicated after the complete observation history is assembled, never by selecting a latest sibling",
    },
    "data_lake/consumption.py": {
        "detection": "lane_dir",
        "posture": "infrastructure",
        "reason": "ack-lane seam reader; reads every ack by contract, not a data consumer",
    },
    "data_lake/creator_audience_queue.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "the creator-audience queue fold consumes every committed job, claim, and terminal record; duplicate jobs, non-contiguous claim generations, conflicting leases, and multiple terminal heads fail closed rather than selecting a latest sibling",
    },
    "data_lake/root.py": {
        "detection": "declared_free_walk",
        "posture": "selection_rule",
        "mechanism": "local:tombstoned_packet_ids",
        "reason": "public-read filtering walks only the exact raw_packet_tombstone_silver lane under each derived anchor, validates every current Silver envelope and both raw packet refs, and excludes only the explicitly targeted packet ids; malformed or unresolved records fail closed",
    },
    "data_lake/reddit_subreddit_registry.py": {
        "detection": "lane_dir",
        "posture": "all_siblings",
        "reason": (
            "the registry row is a fold over every sibling, never a latest-sibling pick: "
            "exactly one genesis (migrated baseline or add roster change) is required, "
            "roster deltas apply in predecessor-chain order with a forked or dangling "
            "chain failing closed, and observations apply in (observed_at, "
            "provenance_pointer, record_id) order deduped by provenance pointer. Every "
            "record contributes; ambiguity raises rather than resolving to a guess"
        ),
    },
    "data_lake/product_mention_selection.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "shared:select_current_record_per_subject",
        "reason": "single exact-policy product-mention reader; all consumers bind version plus fingerprint, residuals remain visible, and ambiguous same-policy siblings fail closed",
    },
    "data_lake/creator_metric_lineage.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "lineage classification and reconciliation intentionally enumerate every creator-metric observation and rollup sibling; no latest sibling is selected",
    },
    "data_lake/derived_retrieval_cache.py": {
        "detection": "declared_free_walk",
        "posture": "infrastructure",
        "reason": "disposable index infrastructure fingerprints only the exact derived-ref address supplied by the already-enumerated Silver record; it never selects among siblings or supplies evidence authority",
    },
    "data_lake/derived_retrieval_views.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "rebuildable non-authoritative view builder intentionally enumerates every active silver_envelope record (classified by the shared authority classifier) plus every Fragrantica projection product-snapshot row; no latest sibling is selected and the views are routing caches, never evidence selection",
    },
    "data_lake/silver_census.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "read-only inventory intentionally enumerates every registered Silver record; observation-unit deduplication and policy qualification are reported separately from stored-record counts",
    },
    "data_lake/silver_record.py": {
        "detection": "declared_free_walk",
        "posture": "fail_closed_singleton",
        "reason": "physical authority verification resolves only the exact derived raw_anchor + lane + record_id address claimed by each Silver ref; it never selects among siblings",
    },
    "runners/run_capture_ecr_cleaning_smoke.py": {
        "detection": "lane_dir",
        "posture": "fail_closed_singleton",
        "reason": "exactly one transcribed transcript_asr record per anchor or raise",
    },
    "runners/run_instagram_creator_audience_triangulation.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "local:prepare_instagram_subscription_judgment",
        "reason": "the caller supplies explicit admitted comment/transcript record paths; the runner verifies data-root containment, requested lane, canonical record path, raw-anchor identity, and current source validity, while lane_dir is used only for path-shape validation and never to select an arbitrary sibling",
    },
    "runners/run_source_capture_tiktok_daily_heartbeat.py": {
        "detection": "declared_free_walk",
        "posture": "selection_rule",
        "mechanism": "local:_profile_metric_silver_fields",
        "reason": "the heartbeat computes the two deterministic profile-metric record ids for its exact admitted packet, validates both exact records, and never selects among siblings",
    },
    "runners/run_tiktok_creator_audience_triangulation.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "local:select_current_audience_silver_records",
        "reason": "selects physically resolved source-backed grid-observation and comment-attention records under the current exact policy, names unresolved refs and policy mismatches as residuals, and fails closed on ambiguous current evidence",
    },
    "runners/run_tiktok_creator_onboarding_coordinator.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "local:_validated_outcomes_for_job",
        "reason": "queue recovery enumerates the named job anchor's Judgment outcomes and accepts only the single validated outcome whose bundle id and hash exactly match the queued bundle; ambiguity fails closed",
    },
    "runners/run_youtube_creator_audience_triangulation.py": {
        "detection": "lane_dir",
        "posture": "selection_rule",
        "mechanism": "local:_selected_transcript_source",
        "reason": "explicit packet ids bind caption or ASR evidence directly, and the ASR lane walk is then confined to that named packet and accepts exactly one complete transcript record, otherwise failing closed; without explicit packet ids the runner picks one winner among the lake-wide eligible sibling sources projected by youtube_capture/behavioral_projection.py, preferring manual caption, then any caption, then ASR, then the latest capture timestamp within that rank -- a silent single-winner selection, not a fail-closed one; either way the selected source's video and channel identity is rebound against the assessment before use",
    },
    "runners/run_transcript_product_extract.py": {
        "detection": "lane_dir",
        "posture": "all_siblings",
        "reason": "consumes each transcript_asr record with exact record_id+sha256 receipts; obligation fingerprints re-trigger on record change",
    },
    "source_capture/ig_reels_behavioral_lake.py": {
        "detection": "lane_dir",
        "posture": "set_marker_pinned",
        "reason": "deep-capture lanes read pinned record ids via set markers and admit only valid source-backed envelopes whose exact packet/file/hash resolves; historical grammar-B sets remain residual-only",
    },
    "youtube_capture/behavioral_projection.py": {
        "detection": "lane_dir",
        "posture": "all_siblings",
        "reason": "labels each transcript_asr record with set-completeness status; duplicate anchors flagged, not silently merged",
    },
    "capture_spine/creator_profile_current/instagram_metric_seed.py": {
        "detection": "declared_free_walk",
        "posture": "selection_rule",
        "mechanism": "shared:select_current_record_per_subject",
        "reason": "path-based derived-tree discovery (sha-deduped) feeding data_lake.sibling_selection fail-closed per-username selection",
    },
    "capture_spine/creator_profile_current/rollup_formula_revalidation.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "independent formula audit intentionally revalidates every creator-metric observation and rollup record across all anchors; it never selects pickup authority",
    },
    "runners/run_ig_reels_product_extract.py": {
        "detection": "declared_free_walk",
        "posture": "all_siblings",
        "reason": "path-based deep-capture walk consumes only set-complete, source-backed envelope transcripts with exact packet/file/hash resolution; legacy records are emitted audit-only",
    },
}


def silver_reader_posture_problems(entry: object) -> list[str]:
    """Shape problems for one reader-posture declaration (empty = shape-valid).

    A ``selection_rule`` posture is V2's core claim and must NAME the callable
    that implements it (``shared:<callable>`` = the data_lake.sibling_selection
    rule is called; ``local:<callable>`` = the file is the declared home of an
    adjudicated rule it defines and uses). The reader gate verifies visible USE
    of the named callable, so a declared posture cannot rot when the code drops
    the rule (F-SH-001: verify use, never mere declaration).
    """
    if not isinstance(entry, dict):
        return ["reader posture must be an object with detection/posture/reason"]
    problems: list[str] = []
    if entry.get("detection") not in ("lane_dir", "declared_free_walk"):
        problems.append(f"invalid detection {entry.get('detection')!r}")
    posture = entry.get("posture")
    if posture not in SILVER_READER_POSTURES:
        problems.append(
            f"invalid posture {posture!r} (expected one of {SILVER_READER_POSTURES})"
        )
    reason = entry.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        problems.append("reader posture requires a non-empty reason")
    mechanism = entry.get("mechanism")
    if posture == "selection_rule":
        if not (
            isinstance(mechanism, str)
            and mechanism.partition(":")[0] in ("shared", "local")
            and mechanism.partition(":")[2].isidentifier()
        ):
            problems.append(
                "selection_rule posture requires mechanism 'shared:<callable>' or "
                f"'local:<callable>'; got {mechanism!r}"
            )
    elif mechanism is not None:
        problems.append(f"mechanism is only valid for selection_rule postures; got {mechanism!r}")
    return problems


def lane_dir_reader_files() -> set[str]:
    """Production files with a `lane_dir` touchpoint, from the same tracked-source
    discovery that feeds the touchpoint counter gate."""
    return {
        file_path
        for (file_path, call_name) in non_raw_lake_touchpoints()
        if call_name == "lane_dir"
    }


def derived_root_traversal_files() -> set[str]:
    """Tracked production files that traverse a directly bound derived root.

    This closes the census gap for readers that bypass ``DataLakeRoot.lane_dir``
    with ``derived = data_root.path / "derived"`` followed by ``derived.iterdir``
    (or glob/rglob). It intentionally does not infer arbitrary path dataflow.
    """
    readers: set[str] = set()
    traversal_calls = {"iterdir", "glob", "rglob"}
    for path in tracked_harness_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        root_names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if not (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Div)
                and isinstance(value.right, ast.Constant)
                and value.right.value == "derived"
            ):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            root_names.update(target.id for target in targets if isinstance(target, ast.Name))
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in traversal_calls
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in root_names
            for node in ast.walk(tree)
        ):
            readers.add(path.relative_to(HARNESS_ROOT).as_posix())
    # A reader already covered by the stricter lane_dir census keeps that
    # detection class even if the same module also performs a direct traversal.
    return readers - lane_dir_reader_files()


STRUCTURAL_EXCLUSIONS: tuple[dict[str, str], ...] = (
    {
        "target": "forseti-harness/tests/**",
        "reason": "test code is not a production lake touchpoint; discovery scans tracked non-test harness source only",
    },
    {
        "target": "non-git-tracked files",
        "reason": "discovery reads `git ls-files` output only, so untracked scratch cannot become a silent lake touchpoint",
    },
)


def a2_fork_impact_for_call(call_name: str) -> str:
    """Deterministic fork-impact class for a non-raw touchpoint call name."""
    return "packet_index" if call_name in PACKET_INDEX_CALLS else "none"


def identity_binding_problems(binding: object) -> list[str]:
    """Shape problems for one identity_binding declaration (empty = shape-valid).

    Single source for the rule; the inventory gate checks declared record
    entries through it and the seam-coverage test checks the module
    declarations through it.
    """
    if not isinstance(binding, dict):
        return ["identity_binding must be an object with a status"]
    status = binding.get("status")
    if status not in IDENTITY_BINDING_STATUSES:
        return [
            f"invalid identity_binding status {status!r} "
            f"(expected one of {list(IDENTITY_BINDING_STATUSES)})"
        ]
    problems: list[str] = []
    detail_field = IDENTITY_BINDING_DETAIL_FIELDS[status]
    if not str(binding.get(detail_field, "")).strip():
        problems.append(
            f"identity_binding status {status!r} requires a non-empty {detail_field!r}"
        )
    unexpected = sorted(set(binding) - {"status", detail_field})
    if unexpected:
        problems.append(f"identity_binding carries unexpected fields {unexpected}")
    return problems


def identity_binding_for_runner(runner: str) -> dict[str, str]:
    """Declared binding for a runner, or an explicit undeclared marker.

    The undeclared marker deliberately fails identity_binding_problems, so a
    new capture runner cannot clear the gate by regenerating the record: the
    question must be answered in RUNNER_IDENTITY_BINDINGS.
    """
    declared = RUNNER_IDENTITY_BINDINGS.get(runner)
    if declared is None:
        return {"status": "undeclared"}
    return dict(declared)


@dataclass(frozen=True)
class ProducerCall:
    name: str
    line: int
    forwards_data_root: bool


@dataclass(frozen=True)
class RunnerSeam:
    exposes_output_arg: bool
    exposes_data_root_arg: bool
    exposes_env_fallback: bool
    explicit_data_root_only: bool
    resolves_data_root: bool
    rejects_output_and_data_root: bool
    env_fallback_uses_output_omitted: bool
    producer_calls: tuple[ProducerCall, ...]

    @property
    def forwards_data_root(self) -> bool:
        return any(call.forwards_data_root for call in self.producer_calls)

    @property
    def has_seam(self) -> bool:
        return (
            self.exposes_data_root_arg
            and (self.exposes_env_fallback or self.explicit_data_root_only)
            and self.resolves_data_root
            and self.forwards_data_root
        )

    @property
    def has_exclusive_output_mode(self) -> bool:
        if not self.exposes_output_arg:
            return True
        return self.rejects_output_and_data_root and self.env_fallback_uses_output_omitted

    def missing_seam_parts(self) -> list[str]:
        missing: list[str] = []
        if not self.exposes_data_root_arg:
            missing.append("--data-root argument")
        if not self.exposes_env_fallback and not self.explicit_data_root_only:
            missing.append("FORSETI_DATA_ROOT fallback or named explicit-root-only posture")
        if not self.resolves_data_root:
            missing.append("DataLakeRoot.resolve")
        if not self.forwards_data_root:
            missing.append("data_root= forwarded into packet writer")
        return missing

    def missing_output_mode_parts(self) -> list[str]:
        if not self.exposes_output_arg:
            return []
        missing: list[str] = []
        if not self.rejects_output_and_data_root:
            missing.append("explicit --output + --data-root rejection")
        if not self.env_fallback_uses_output_omitted:
            missing.append("FORSETI_DATA_ROOT/ORCA_DATA_ROOT gated on --output being omitted")
        return missing


def has_any_token(src: str, tokens: tuple[str, ...]) -> bool:
    return any(token in src for token in tokens)


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None


def called_names(node: ast.AST) -> set[str]:
    return {
        name
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        for name in [call_name(child)]
        if name is not None
    }


def calls_named(tree: ast.AST, names: tuple[str, ...]) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and call_name(node) in names
    ]


@cache
def _packet_writer_function_index() -> tuple[frozenset[str], tuple[tuple[str, tuple[str, ...]], ...]]:
    """Recursive writer-function closure plus the files each writer is defined in."""
    function_calls: dict[str, set[str]] = {}
    definition_sites: dict[str, set[str]] = {}
    for path in sorted(SOURCE_CAPTURE_DIR.rglob("*.py")):
        relative = path.relative_to(HARNESS_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_calls[node.name] = called_names(node)
                definition_sites.setdefault(node.name, set()).add(relative)

    writers = set(DIRECT_PACKET_WRITER_TOKENS)
    changed = True
    while changed:
        changed = False
        for name, calls in function_calls.items():
            if name not in writers and calls.intersection(writers):
                writers.add(name)
                changed = True
    sites = tuple(
        (name, tuple(sorted(definition_sites.get(name, set()))))
        for name in sorted(writers)
    )
    return frozenset(writers), sites


def source_capture_packet_writer_names() -> frozenset[str]:
    """Function names in source_capture that eventually stage/write a raw packet."""
    names, _sites = _packet_writer_function_index()
    return names


def packet_writer_function_sites() -> dict[str, tuple[str, ...]]:
    """Writer-function name -> sorted defining files (empty for the seed tokens
    when they are defined outside source_capture rglob, which does not happen
    today)."""
    _names, sites = _packet_writer_function_index()
    return dict(sites)


def is_packet_writer_name(
    name: str | None, packet_writer_names: set[str] | frozenset[str]
) -> bool:
    return bool(name) and (
        name in packet_writer_names or bool(PACKET_WRITER_NAME_RE.fullmatch(name))
    )


def cli_flags(tree: ast.AST) -> set[str]:
    flags: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) != "add_argument":
            continue
        for arg in node.args:
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and arg.value.startswith("--")
            ):
                flags.add(arg.value)
    return flags


def environment_get_names(tree: ast.AST) -> set[str]:
    """Return environment-variable names read through os.environ.get.

    AST detection keeps help text and error messages from falsely certifying a
    runner as carrying an ambient production-root fallback.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = dotted_name(node.func)
        first = node.args[0]
        if (
            function == "os.environ.get"
            and isinstance(first, ast.Constant)
            and isinstance(first.value, str)
        ):
            names.add(first.value)
    return names


def source_capture_imports(tree: ast.AST) -> tuple[set[str], set[str]]:
    packet_writer_names = source_capture_packet_writer_names()
    writer_names = set(DIRECT_PACKET_WRITER_TOKENS)
    module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if not (node.module or "").startswith("source_capture"):
                continue
            for alias in node.names:
                if is_packet_writer_name(alias.name, packet_writer_names):
                    writer_names.add(alias.asname or alias.name)
                else:
                    module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("source_capture."):
                    module_aliases.add(alias.asname or alias.name)
    return writer_names, module_aliases


def is_imported_module_writer_call(node: ast.Call, module_aliases: set[str]) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if not is_packet_writer_name(node.func.attr, source_capture_packet_writer_names()):
        return False
    base_name = dotted_name(node.func.value)
    return base_name in module_aliases


def producer_calls(
    tree: ast.AST, writer_names: set[str], module_aliases: set[str]
) -> tuple[ProducerCall, ...]:
    calls: list[ProducerCall] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name not in writer_names and not is_imported_module_writer_call(node, module_aliases):
            continue
        calls.append(
            ProducerCall(
                name=name or "<unknown>",
                line=node.lineno,
                forwards_data_root=any(keyword.arg == "data_root" for keyword in node.keywords),
            )
        )
    return tuple(calls)


def uses_scaffold_resolver(tree: ast.AST) -> bool:
    """True when the runner imports and calls the shared scaffold resolver.

    Require an unshadowed module-level import binding plus a call on a reachable
    lexical path inside ``main``. A mention in help text/comment, an unused
    helper, or a statically dead branch must not falsely certify the seam.
    """
    bound_names = {
        alias.asname or alias.name
        for node in getattr(tree, "body", ())
        if isinstance(node, ast.ImportFrom) and node.module == SCAFFOLD_MODULE
        for alias in node.names
        if alias.name == SCAFFOLD_RESOLVER_NAME
    }
    if not bound_names:
        return False

    rebound_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    rebound_names.update(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )
    bound_names -= rebound_names
    if not bound_names:
        return False

    class _MainResolverCallVisitor(ast.NodeVisitor):
        found = False

        def visit_Call(self, node: ast.Call) -> None:
            if call_name(node) in bound_names:
                self.found = True
                return
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_If(self, node: ast.If) -> None:
            if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
                branch = node.body if node.test.value else node.orelse
                for statement in branch:
                    self.visit(statement)
                return
            self.generic_visit(node)

    for node in getattr(tree, "body", ()):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != "main":
            continue
        visitor = _MainResolverCallVisitor()
        for statement in node.body:
            visitor.visit(statement)
        if visitor.found:
            return True
    return False


def packet_producers() -> dict[str, RunnerSeam]:
    """Map each packet-producing runner filename to its lake seam shape."""
    producers: dict[str, RunnerSeam] = {}
    for path in sorted(RUNNERS_DIR.glob("run_*.py")):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
        flags = cli_flags(tree)
        env_names = environment_get_names(tree)
        writer_names, module_aliases = source_capture_imports(tree)
        calls = producer_calls(tree, writer_names, module_aliases)
        scaffold_seam = uses_scaffold_resolver(tree)
        if calls:
            producers[path.name] = RunnerSeam(
                exposes_output_arg="--output" in flags,
                exposes_data_root_arg="--data-root" in flags,
                exposes_env_fallback=(
                    "FORSETI_DATA_ROOT" in env_names
                    or scaffold_seam
                    or (
                        "--output" not in flags
                        and "--admit-output" not in flags
                        and path.name not in EXPLICIT_DATA_ROOT_RUNNERS
                    )
                ),
                explicit_data_root_only=path.name in EXPLICIT_DATA_ROOT_RUNNERS,
                resolves_data_root="DataLakeRoot.resolve" in src or scaffold_seam,
                rejects_output_and_data_root=(
                    has_any_token(src, EXPLICIT_PAIR_REJECT_TOKENS) or scaffold_seam
                ),
                env_fallback_uses_output_omitted=(
                    has_any_token(src, ENV_OUTPUT_OMITTED_TOKENS) or scaffold_seam
                ),
                producer_calls=calls,
            )
    return producers


def bronze_writer_runners() -> frozenset[str]:
    return frozenset(packet_producers()).union(BRONZE_PACKET_ORCHESTRATORS)


@cache
def tracked_harness_python_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "-C", str(HARNESS_ROOT.parent), "ls-files", "--", "forseti-harness"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path = HARNESS_ROOT.parent / line
        if path.suffix != ".py" or not path.is_file():
            continue
        relative_path = path.relative_to(HARNESS_ROOT).as_posix()
        if relative_path.startswith("tests/"):
            continue
        paths.append(path)
    return tuple(sorted(paths))


def non_raw_lake_touchpoints() -> Counter[tuple[str, str]]:
    """Current non-raw lake write/read touchpoints that must be classified before GT forks."""
    touchpoints: Counter[tuple[str, str]] = Counter()
    for path in tracked_harness_python_files():
        relative_path = path.relative_to(HARNESS_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name in NON_RAW_LAKE_TOUCHPOINT_CALLS:
                touchpoints[(relative_path, name)] += 1
    return touchpoints


def build_inventory() -> dict:
    """Fresh deterministic inventory from tracked source. Pure discovery plus
    module-declared exclusions; no filesystem writes."""
    runner_entries = [
        {
            "runner": name,
            "kind": "direct_packet_writer",
            "a2_fork_impact": "manifest_shape",
            "identity_binding": identity_binding_for_runner(name),
        }
        for name in sorted(packet_producers())
    ] + [
        {
            "runner": name,
            "kind": "orchestrator",
            "a2_fork_impact": "manifest_shape",
            "identity_binding": identity_binding_for_runner(name),
        }
        for name in sorted(BRONZE_PACKET_ORCHESTRATORS)
    ]
    writer_entries = [
        {
            "function": name,
            "defined_in": list(sites),
            "a2_fork_impact": "manifest_shape",
        }
        for name, sites in sorted(packet_writer_function_sites().items())
    ]
    touchpoint_entries = [
        {
            "module": module,
            "call": call,
            "count": count,
            "a2_fork_impact": a2_fork_impact_for_call(call),
        }
        for (module, call), count in sorted(non_raw_lake_touchpoints().items())
    ]
    exclusions = [dict(entry) for entry in STRUCTURAL_EXCLUSIONS] + [
        {
            "target": runner,
            "reason": reason,
            "kind": "acknowledged_unsynced_packet_runner",
        }
        for runner, reason in sorted(KNOWN_UNSYNCED.items())
    ]
    return {
        "inventory_version": INVENTORY_VERSION,
        "authority_note": (
            "Generated inventory of code surfaces; never lake authority; "
            "regenerated and diffed by tests/contract/test_data_lake_inventory_gate.py; "
            "a2_fork_impact is routing metadata for the deferred A2 decision, not a selection; "
            "identity_binding documents each runner's served-content-to-requested-subject "
            "binding posture (unbound is a visible acknowledged gap, not a pass)."
        ),
        "raw_packet_writers": {
            "runner_seams": sorted(runner_entries, key=lambda e: e["runner"]),
            "writer_functions": writer_entries,
        },
        "non_raw_touchpoints": touchpoint_entries,
        "exclusions": exclusions,
        "unknowns": [],
    }


def serialize_inventory(inventory: dict) -> str:
    """Canonical serialization: sorted keys, two-space indent, trailing newline."""
    return json.dumps(inventory, indent=2, sort_keys=True) + "\n"


def load_declared_inventory(path: Path = INVENTORY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory_violations(declared: dict, discovered: dict) -> list[str]:
    """Gate checks: drift between declared and discovered, unreasoned
    exclusions, and unknowns without a resolved owner disposition."""
    violations: list[str] = []

    if declared.get("inventory_version") != discovered.get("inventory_version"):
        violations.append(
            "inventory_version mismatch: declared="
            f"{declared.get('inventory_version')!r} discovered={discovered.get('inventory_version')!r}"
        )

    def _entry_set(inventory: dict, family: str, subfamily: str | None = None) -> set[str]:
        node = inventory.get(family, {})
        entries = node.get(subfamily, []) if subfamily else node
        if not isinstance(entries, list):
            return set()
        return {json.dumps(entry, sort_keys=True) for entry in entries}

    for family, subfamily in (
        ("raw_packet_writers", "runner_seams"),
        ("raw_packet_writers", "writer_functions"),
        ("non_raw_touchpoints", None),
        ("exclusions", None),
    ):
        label = f"{family}.{subfamily}" if subfamily else family
        declared_set = _entry_set(declared, family, subfamily)
        discovered_set = _entry_set(discovered, family, subfamily)
        for entry in sorted(discovered_set - declared_set):
            violations.append(f"undeclared {label} entry (discovered, not in record): {entry}")
        for entry in sorted(declared_set - discovered_set):
            violations.append(f"stale {label} entry (declared, no longer discovered): {entry}")

    declared_seams = declared.get("raw_packet_writers", {})
    declared_seams = declared_seams.get("runner_seams", []) if isinstance(declared_seams, dict) else []
    for entry in declared_seams if isinstance(declared_seams, list) else []:
        if not isinstance(entry, dict):
            continue  # non-object entries already surface as declared/discovered drift
        runner = entry.get("runner")
        if "identity_binding" not in entry:
            violations.append(
                "runner seam without an identity_binding (every capture runner must declare "
                "how served content is bound to the requested subject in "
                f"RUNNER_IDENTITY_BINDINGS): {runner!r}"
            )
            continue
        for problem in identity_binding_problems(entry["identity_binding"]):
            violations.append(f"runner seam {runner!r}: {problem}")

    for exclusion in declared.get("exclusions", []):
        if not str(exclusion.get("reason", "")).strip():
            violations.append(f"exclusion without a reason: {exclusion.get('target')!r}")

    for unknown in declared.get("unknowns", []):
        disposition = unknown.get("owner_disposition") or {}
        if disposition.get("status") != "resolved":
            violations.append(
                "unknown without a resolved owner disposition (owner-attributable via the "
                f"human-gated PR merge; pending fails the gate): {unknown.get('target')!r}"
            )
            continue
        if not str(unknown.get("target", "")).strip():
            violations.append("resolved unknown without a target")
        if not str(unknown.get("question", "")).strip():
            violations.append(f"resolved unknown without a question: {unknown.get('target')!r}")
        if not str(disposition.get("disposition", "")).strip():
            violations.append(
                f"resolved unknown without a concrete disposition: {unknown.get('target')!r}"
            )
        if not str(disposition.get("recorded_by", "")).strip():
            violations.append(
                f"resolved unknown without owner-attribution evidence: {unknown.get('target')!r}"
            )

    return violations
