"""Capture one complete public Junip product-review corpus into a Source Capture Packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_lake.root import DataLakeRoot
from harness_utils import utc_now_z
from source_capture import (
    CaptureModeCategory,
    PacketTiming,
    SourceCaptureSlice,
    known_fact,
    not_applicable,
    not_attempted,
    unknown_with_reason,
)
from source_capture.packet_assembly import stage_and_write_packet, staged_file_id_map


API_ORIGIN = "https://api.juniphq.com"
PRODUCTS_URL = f"{API_ORIGIN}/v2/products?page_size=50"
REVIEWS_PATH = "/v2/product_overview/reviews"
PAGE_SIZE = 50
MAX_PAGES = 100
MAX_RESPONSE_BYTES = 5_000_000


def _fetch_json(url: str, store_key: str, timeout_seconds: float) -> tuple[bytes, dict]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Junip-Store-Key": store_key,
            "User-Agent": "Forseti-Source-Capture/1.0",
        },
    )
    try:
        with build_opener(ProxyHandler({})).open(request, timeout=timeout_seconds) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError(f"Junip response exceeded {MAX_RESPONSE_BYTES} bytes: {url}")
            if response.status != 200:
                raise ValueError(f"Junip response returned HTTP {response.status}: {url}")
            document = json.loads(body)
            if not isinstance(document, dict):
                raise ValueError(f"Junip response was not a JSON object: {url}")
            return body, {
                "requested_url": url,
                "final_url": response.geturl(),
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "bytes": len(body),
            }
    except (HTTPError, URLError) as exc:
        raise ValueError(f"Junip request failed for {url}: {type(exc).__name__}: {exc}") from exc


def capture_junip_review_corpus(
    *,
    store_key: str,
    expected_store_name: str,
    expected_store_url: str,
    data_root: DataLakeRoot,
    timeout_seconds: float = 30.0,
) -> tuple[str, int, int]:
    if not store_key or any(character.isspace() for character in store_key):
        raise ValueError("store_key must be one non-empty public Junip store key")

    artifacts: list[tuple[str, bytes]] = []
    request_records: list[dict] = []
    products_body, products_request = _fetch_json(PRODUCTS_URL, store_key, timeout_seconds)
    products_document = json.loads(products_body)
    products = products_document.get("data")
    if not isinstance(products, list) or not products:
        raise ValueError("Junip products response has no product rows")
    remote_ids = {
        str(product.get("remote_id"))
        for product in products
        if isinstance(product, dict) and product.get("remote_id") is not None
    }
    if not remote_ids:
        raise ValueError("Junip products response has no remote product identities")
    artifacts.append(("01_products.json", products_body))
    request_records.append({**products_request, "role": "product_identity"})

    cursor: str | None = None
    seen_cursors: set[str] = set()
    reviews: dict[str, dict] = {}
    unlisted_review_remote_ids: set[str] = set()
    review_files: list[str] = []
    for page_number in range(1, MAX_PAGES + 1):
        query = {
            "sort_field": "created_at",
            "sort_order": "desc",
            "page_size": str(PAGE_SIZE),
        }
        if cursor is not None:
            query["page_after"] = cursor
        url = f"{API_ORIGIN}{REVIEWS_PATH}?{urlencode(query)}"
        body, request_record = _fetch_json(url, store_key, timeout_seconds)
        document = json.loads(body)
        rows = document.get("data")
        meta = document.get("meta")
        if not isinstance(rows, list) or not isinstance(meta, dict):
            raise ValueError(f"Junip review page {page_number} lacks data/meta")
        if not rows:
            raise ValueError(f"Junip review page {page_number} is unexpectedly empty")
        for row in rows:
            if not isinstance(row, dict) or row.get("id") is None:
                raise ValueError(f"Junip review page {page_number} has a row without id")
            product = row.get("product")
            if not isinstance(product, dict) or product.get("remote_id") is None:
                raise ValueError(f"Junip review {row.get('id')} lacks an embedded product identity")
            row_remote_id = str(product["remote_id"])
            if row_remote_id not in remote_ids:
                unlisted_review_remote_ids.add(row_remote_id)
            review_id = str(row["id"])
            if review_id in reviews:
                raise ValueError(f"Junip pagination duplicated review id {review_id}")
            reviews[review_id] = row
        filename = f"{page_number + 1:02d}_reviews_page_{page_number:04d}.json"
        artifacts.append((filename, body))
        review_files.append(filename)
        request_records.append(
            {
                **request_record,
                "role": "review_page",
                "page_number": page_number,
                "row_count": len(rows),
            }
        )
        next_cursor = meta.get("after")
        if next_cursor is None:
            break
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
            raise ValueError(f"Junip review page {page_number} returned an invalid/repeated cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    else:
        raise ValueError(f"Junip corpus exceeded safety ceiling of {MAX_PAGES} pages")

    store_names = {
        str(row.get("store", {}).get("name"))
        for row in reviews.values()
        if isinstance(row.get("store"), dict)
    }
    store_urls = {
        str(row.get("store", {}).get("url"))
        for row in reviews.values()
        if isinstance(row.get("store"), dict)
    }
    if store_names != {expected_store_name} or store_urls != {expected_store_url}:
        raise ValueError(
            "Junip review corpus store identity mismatch: "
            f"names={sorted(store_names)} urls={sorted(store_urls)}"
        )

    text_review_count = sum(bool(str(row.get("body") or "").strip()) for row in reviews.values())
    captured_at = utc_now_z()
    manifest = {
        "schema_version": "junip_review_corpus_capture_v1",
        "captured_at": captured_at,
        "api_origin": API_ORIGIN,
        "store_name": expected_store_name,
        "store_url": expected_store_url,
        "product_count": len(remote_ids),
        "review_count": len(reviews),
        "text_review_count": text_review_count,
        "review_page_count": len(review_files),
        "page_size": PAGE_SIZE,
        "pagination_exhausted": True,
        "product_remote_ids": sorted(remote_ids),
        "unlisted_review_remote_ids": sorted(unlisted_review_remote_ids),
        "review_files": review_files,
        "requests": request_records,
        "limitations": [
            "Public Junip store key is source-visible configuration, not a customer credential.",
            "Current API snapshot; deleted reviews and prior edits are not recoverable.",
            "Review rows for unlisted product identities remain visible but are not promoted to current catalog claims.",
            "Capture preserves review rows but does not establish reviewer independence or prevalence.",
        ],
    }
    artifacts.append(
        (
            "request_manifest.json",
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    )
    file_ids = staged_file_id_map(artifacts)
    timing = PacketTiming(
        source_publication_or_event=unknown_with_reason(
            "The corpus contains per-review timestamps rather than one publication time."
        ),
        source_edit_or_version=unknown_with_reason(
            "Junip does not expose a corpus version or review edit-history denominator."
        ),
        capture_time=known_fact(captured_at),
        recapture_time=not_applicable("one current complete pagination walk"),
        cutoff_posture=unknown_with_reason(
            f"Live API corpus pagination exhausted at {captured_at}; no historical cutoff was applied."
        ),
    )
    access = known_fact("public Junip API using the store key embedded by the retailer PDP")
    archive = not_attempted("live review-corpus capture did not query an archive")
    media = not_attempted("review JSON capture did not fetch attached media")
    relationship = not_applicable("no prior Junip corpus packet supplied")
    result = stage_and_write_packet(
        data_root=data_root,
        staged_artifacts=artifacts,
        source_slices=[
            SourceCaptureSlice(
                slice_id="junip_complete_review_corpus_01",
                locator=known_fact(PRODUCTS_URL),
                timing=timing,
                access_posture=access,
                archive_history_posture=archive,
                media_modality_posture=media,
                re_capture_relationship=relationship,
                limitations=manifest["limitations"],
                warning_notes=[],
                preserved_file_ids=[file_ids[name] for name, _ in artifacts],
                metric_observations=[],
            )
        ],
        source_family="retailer_reviews",
        source_surface="junip_public_api",
        source_locator=known_fact(PRODUCTS_URL),
        decision_question=(
            "What complete current Experiment Beauty DTC review corpus does Junip expose?"
        ),
        capture_context="Experiment Beauty consumer-brand Acquire and Seal",
        actor_audience_context=unknown_with_reason(
            "Review rows expose public customer display identities but not a representative audience frame."
        ),
        capture_mode=CaptureModeCategory.STRUCTURED_ACCESS,
        operator_category="implementation_dogfood",
        session_identity=None,
        visible_mode_changes=["junip_complete_cursor_pagination"],
        source_publication_or_event=timing.source_publication_or_event,
        source_edit_or_version=timing.source_edit_or_version,
        cutoff_posture=timing.cutoff_posture,
        recapture_time=timing.recapture_time,
        access_posture=access,
        archive_history_posture=archive,
        media_modality_posture=media,
        re_capture_relationship=relationship,
        warnings=[],
        limitations=manifest["limitations"],
        receipt_summary=(
            f"Junip corpus captured through terminal pagination: {len(reviews)} unique reviews, "
            f"{text_review_count} with usable body text across {len(remote_ids)} products."
        ),
        receipt_non_claims=[
            "not reviewer-independence proof",
            "not representative prevalence",
            "not semantic coding",
            "not product-performance validation",
        ],
    )
    return result.output_directory, len(reviews), text_review_count


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-key", required=True)
    parser.add_argument("--expected-store-name", required=True)
    parser.add_argument("--expected-store-url", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        packet, reviews, text_reviews = capture_junip_review_corpus(
            store_key=args.store_key,
            expected_store_name=args.expected_store_name,
            expected_store_url=args.expected_store_url,
            data_root=DataLakeRoot.resolve(explicit=args.data_root),
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:
        print(f"Junip review corpus capture failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    print(json.dumps({"packet": packet, "reviews": reviews, "text_reviews": text_reviews}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
