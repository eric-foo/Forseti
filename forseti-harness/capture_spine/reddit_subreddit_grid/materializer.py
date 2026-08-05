"""Read-only Reddit Subreddit Registry materializer over committed grid packets.

Capture runners never flip registry state (creator-registry rule); this
materializer is the one writer. It scans explicitly supplied, already
committed ``reddit_subreddit_grid`` Source Capture Packets and applies the
registry spec's two-speed rule:

- observations APPEND (one per packet per subreddit, deduped by provenance
  pointer so a re-run over the same packet cannot double-append);
- descriptive facts UPDATE-ON-CHANGE. This materializer touches only
  ``status`` (a grid capture proves liveness); it deliberately does not
  touch ``public_description_or_none``, because the grid sidebar text and
  the ``about.json`` public description are different source surfaces and
  diffing across surfaces would append spurious change records.

Unknown subreddits (packet target not present in the registry) are reported,
never silently added: grid passes are expected to start FROM a registry
filter, so an unknown target is an operator signal, not new-row authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from harness_utils import hash_file
from data_lake.reddit_subreddit_registry import (
    append_grid_observation,
    known_subreddits,
    normalize_subreddit,
)
from data_lake.root import DataLakeRoot
from capture_spine.reddit_subreddit_grid.grid_projection import (
    GRID_LISTING_HOSTS,
    OLD_REDDIT_LISTING_HOST,
    WWW_REDDIT_LISTING_HOST,
    GridView,
    RedditGridProjectionError,
    grid_view_from_record,
    project_old_reddit_grid_html,
    same_grid_listing_url,
)
from source_capture.models import SOURCE_CAPTURE_MANIFEST_VERSION
from source_capture.packet_inspection import read_packet_leniently
from source_capture.source_quality import resolve_manifest_path

GRID_SOURCE_FAMILY = "reddit_subreddit_grid"
# The committed registry is frozen at the stage-3 writer cut-over; the superseded
# Git-mutating refresh below refuses to touch it.
FROZEN_COMMITTED_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3]
    / "forseti"
    / "product"
    / "spines"
    / "capture"
    / "core"
    / "source_families"
    / "social_media"
    / "reddit"
    / "reddit_subreddit_registry_v0.json"
)
GRID_OBSERVATION_SOURCE_SURFACE = "old_reddit_grid_packet"
# Weekly demand-radar listing (top/?t=week): same grid family, distinguishable
# ledger line so readers can tell a weekly consolidated pass from a live pass.
TOP_WEEK_OBSERVATION_SOURCE_SURFACE = "old_reddit_top_week_packet"
# A real-Chrome www capture is a different surface reached by a different
# transport; its observation ledger line names that surface directly (trunk
# vocabulary, PR #1424). The weekly-vs-live distinction for www packets lives
# in the packet's admitted listing URL, which admission pins to the locator.
WWW_REDDIT_REALCHROME_SOURCE_SURFACE = "www_reddit_realchrome_cdp"


def _observation_surface_for(listing_url: str) -> str:
    parsed = urlparse(listing_url)
    host = parsed.netloc.lower()
    if host == WWW_REDDIT_LISTING_HOST:
        return WWW_REDDIT_REALCHROME_SOURCE_SURFACE
    if host != OLD_REDDIT_LISTING_HOST:
        raise RegistryRefreshError(
            "grid_listing_host_unknown",
            f"cannot assign a grid observation surface to host {host!r}",
        )
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[-1] == "top" and "t=week" in (parsed.query or "").split("&"):
        return TOP_WEEK_OBSERVATION_SOURCE_SURFACE
    return GRID_OBSERVATION_SOURCE_SURFACE


class RegistryRefreshError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PacketGridRead:
    manifest_path: str
    subreddit: str
    observed_at: str
    grid_view: GridView


@dataclass
class RegistryRefreshOutcome:
    registry_path: str
    refreshed_subreddits: list[str] = field(default_factory=list)
    duplicate_observation_skips: list[str] = field(default_factory=list)
    unknown_subreddits: list[str] = field(default_factory=list)
    status_changes: list[str] = field(default_factory=list)
    registry_written: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "registry_path": self.registry_path,
            "refreshed_subreddits": self.refreshed_subreddits,
            "duplicate_observation_skips": self.duplicate_observation_skips,
            "unknown_subreddits": self.unknown_subreddits,
            "status_changes": self.status_changes,
            "registry_written": self.registry_written,
            "non_claims": [
                "not metric authority",
                "not demand proof",
                "not venue quality or fit scoring",
                "not capture authorization",
            ],
        }


def refresh_registry_from_grid_packets(
    *,
    registry_path: Path,
    packet_paths: list[Path],
    dry_run: bool = False,
) -> RegistryRefreshOutcome:
    """SUPERSEDED by ``refresh_lake_registry_from_grid_packets``; do not re-wire.

    Registry authority moved to the lake, and the checked-in JSON is frozen
    for rollback and audit.  This Git-mutating path is retained only as the
    two-speed-rule oracle its tests exercise, and is removed in the same later
    work unit that removes the frozen file.  Pointing it at the frozen committed
    registry fails closed rather than relying on a docstring to be read.
    """
    if registry_path.resolve() == FROZEN_COMMITTED_REGISTRY_PATH:
        raise RegistryRefreshError(
            "frozen_registry_write_refused",
            "the committed registry is frozen for rollback and audit; grid evidence "
            "goes to lake authority via refresh_lake_registry_from_grid_packets",
        )
    if not packet_paths:
        raise RegistryRefreshError("no_packets", "at least one grid packet path is required")

    reads = [read_grid_packet(packet_or_manifest_path=path) for path in packet_paths]

    document = json.loads(registry_path.read_text(encoding="utf-8"))
    registry = document.get("reddit_subreddit_registry")
    if not isinstance(registry, dict) or not isinstance(registry.get("subreddits"), list):
        raise RegistryRefreshError("registry_shape", f"not a reddit_subreddit_registry document: {registry_path}")
    rows_by_name = {row["subreddit"]: row for row in registry["subreddits"]}

    outcome = RegistryRefreshOutcome(registry_path=str(registry_path))
    changed = False
    for read in reads:
        row = rows_by_name.get(read.subreddit)
        if row is None:
            outcome.unknown_subreddits.append(read.subreddit)
            continue
        if _apply_two_speed_refresh(row=row, read=read, outcome=outcome):
            changed = True
            outcome.refreshed_subreddits.append(read.subreddit)

    if changed and not dry_run:
        counts = registry.setdefault("counts", {})
        counts["subreddits_total"] = len(registry["subreddits"])
        by_status: dict[str, int] = {}
        for row in registry["subreddits"]:
            by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        counts["by_status"] = dict(sorted(by_status.items()))
        with registry_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        outcome.registry_written = True
    return outcome


@dataclass
class LakeRefreshOutcome:
    """Lake-mode counterpart of ``RegistryRefreshOutcome``."""

    data_root: str
    refreshed_subreddits: list[str] = field(default_factory=list)
    duplicate_observation_skips: list[str] = field(default_factory=list)
    unknown_subreddits: list[str] = field(default_factory=list)
    record_ids: list[str] = field(default_factory=list)
    records_written: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "data_root": self.data_root,
            "authority": "lake",
            "refreshed_subreddits": self.refreshed_subreddits,
            "duplicate_observation_skips": self.duplicate_observation_skips,
            "unknown_subreddits": self.unknown_subreddits,
            "record_ids": self.record_ids,
            "records_written": self.records_written,
            "non_claims": [
                "not metric authority",
                "not demand proof",
                "not venue quality or fit scoring",
                "not capture authorization",
            ],
        }


def refresh_lake_registry_from_grid_packets(
    *,
    data_root: DataLakeRoot,
    packet_paths: list[Path],
    dry_run: bool = False,
) -> LakeRefreshOutcome:
    """Append one observation record per committed grid packet.

    The lake fold supplies the roster, so an unknown subreddit is still
    reported and never silently added: a grid pass starts FROM a registry
    filter, so an unknown target is an operator signal, not new-row authority.
    """
    if not packet_paths:
        raise RegistryRefreshError("no_packets", "at least one grid packet path is required")

    reads = [read_grid_packet(packet_or_manifest_path=path) for path in packet_paths]
    roster = set(known_subreddits(data_root))
    outcome = LakeRefreshOutcome(data_root=str(data_root.path))

    for read in reads:
        key = normalize_subreddit(read.subreddit)
        if key not in roster:
            outcome.unknown_subreddits.append(key)
            continue
        view = read.grid_view
        result = append_grid_observation(
            data_root,
            subreddit=key,
            observed_at=read.observed_at,
            subscriber_count_or_none=_normalized_count(view.visible_subscriber_count_or_none),
            active_user_count_or_none=_normalized_count(view.visible_active_user_count_or_none),
            source_surface=_observation_surface_for(view.listing_url),
            provenance_pointer=read.manifest_path,
            absent_reason_or_none=view.visible_volume_signal_absent_reason_or_none,
            # www states weekly reach; old Reddit has no equivalent and leaves
            # these None, so the same call serves both surfaces.
            weekly_visitor_count_or_none=_normalized_count(view.weekly_visitor_count_or_none),
            weekly_contribution_count_or_none=_normalized_count(
                view.weekly_contribution_count_or_none
            ),
            dry_run=dry_run,
        )
        if result["status"] == "already_current":
            outcome.duplicate_observation_skips.append(key)
            continue
        outcome.refreshed_subreddits.append(key)
        outcome.record_ids.append(result["record_id"])
        if result["written"]:
            outcome.records_written += 1
    return outcome


def read_grid_packet(*, packet_or_manifest_path: Path) -> PacketGridRead:
    manifest_path = resolve_manifest_path(packet_or_manifest_path).resolve()
    try:
        report = read_packet_leniently(manifest_path)
    except Exception as exc:
        raise RegistryRefreshError("manifest_read_failure", f"manifest could not be read: {exc}") from exc
    if not report.conforms_to_current_schema or not report.declares_current_manifest_version:
        raise RegistryRefreshError(
            "manifest_nonconforming",
            f"manifest is not a current {SOURCE_CAPTURE_MANIFEST_VERSION!r} packet: {manifest_path}",
        )
    packet = report.packet
    if packet is None:
        raise RegistryRefreshError("packet_unavailable", "no validated packet was available")
    if packet.source_family != GRID_SOURCE_FAMILY:
        raise RegistryRefreshError(
            "ineligible_source_family",
            f"packet source_family is {packet.source_family!r}, not {GRID_SOURCE_FAMILY!r}",
        )

    locator = packet.source_locator.value or ""
    expected_host = (
        "www.reddit.com"
        if packet.source_surface == WWW_REDDIT_REALCHROME_SOURCE_SURFACE
        else "old.reddit.com"
    )
    subreddit = _subreddit_from_listing_url(locator, expected_host=expected_host)
    if subreddit is None:
        raise RegistryRefreshError("locator_unparseable", f"cannot parse subreddit from locator: {locator!r}")

    metadata_file = _resolve_grid_metadata_file(
        packet,
        expected_locator=locator,
    )
    metadata_path = _resolve_packet_file_path(
        packet_dir=manifest_path.parent,
        relative_packet_path=metadata_file["relative_packet_path"],
        error_code="http_metadata_outside_packet",
        file_label="HTTP metadata",
    )
    _verify_preserved_file_hash(
        path=metadata_path,
        expected_hash=metadata_file["sha256"],
        error_code="http_metadata_hash_mismatch",
    )
    _verify_successful_grid_response(
        packet=packet,
        metadata_path=metadata_path,
        expected_locator=locator,
        expected_subreddit=subreddit,
    )

    # Content-mode packets preserve the capture-time derived record instead of
    # raw HTML (storage-and-retention doctrine, 2026-07-17); sample packets
    # carry both and the stored derived record is authoritative here (drift
    # between scratch source and content is the qualification runner's job, not the
    # registry's). Raw-only packets keep the original re-projection path.
    content_file = _resolve_preserved_file(
        packet, file_name="content_record.json", required=False
    )
    if content_file is not None:
        content_path = _resolve_packet_file_path(
            packet_dir=manifest_path.parent,
            relative_packet_path=content_file["relative_packet_path"],
            error_code="content_record_outside_packet",
            file_label="content record",
        )
        _verify_preserved_file_hash(
            path=content_path,
            expected_hash=content_file["sha256"],
            error_code="content_record_hash_mismatch",
        )
        try:
            record = json.loads(content_path.read_text(encoding="utf-8"))
            grid_view = grid_view_from_record(record)
        except (RedditGridProjectionError, ValueError) as exc:
            raise RegistryRefreshError(
                "content_record_invalid",
                f"preserved content record is not a valid grid record: {exc}",
            ) from exc
        if grid_view.subreddit != subreddit:
            raise RegistryRefreshError(
                "content_record_subreddit_mismatch",
                f"content record names subreddit {grid_view.subreddit!r}, expected {subreddit!r}",
            )
        if not same_grid_listing_url(grid_view.listing_url, locator):
            raise RegistryRefreshError(
                "content_record_listing_url_mismatch",
                "content record listing URL does not match the packet locator: "
                f"content={grid_view.listing_url!r} packet={locator!r}",
            )
    else:
        if urlparse(locator).netloc.lower() == WWW_REDDIT_LISTING_HOST:
            raise RegistryRefreshError(
                "www_content_record_required",
                "www Reddit grid packets require an admitted content record; "
                "a raw fallback remains failure evidence, not registry evidence",
            )
        raw_file = _resolve_preserved_file(packet, file_name="http_response_body.bin")
        raw_path = _resolve_packet_file_path(
            packet_dir=manifest_path.parent,
            relative_packet_path=raw_file["relative_packet_path"],
            error_code="raw_body_outside_packet",
            file_label="preserved body",
        )
        _verify_preserved_file_hash(
            path=raw_path,
            expected_hash=raw_file["sha256"],
            error_code="raw_file_hash_mismatch",
        )
        html = raw_path.read_text(encoding="utf-8", errors="replace")
        grid_view = project_old_reddit_grid_html(
            html_text=html,
            subreddit=subreddit,
            listing_url=locator,
        )
    observed_at = _observed_date(packet)
    return PacketGridRead(
        manifest_path=str(manifest_path),
        subreddit=subreddit,
        observed_at=observed_at,
        grid_view=grid_view,
    )


def _apply_two_speed_refresh(
    *,
    row: dict[str, object],
    read: PacketGridRead,
    outcome: RegistryRefreshOutcome,
) -> bool:
    observations = row.setdefault("observations", [])
    assert isinstance(observations, list)
    if any(obs.get("provenance_pointer") == read.manifest_path for obs in observations):
        outcome.duplicate_observation_skips.append(read.subreddit)
        return False

    view = read.grid_view
    observations.append(
        {
            "observed_at": read.observed_at,
            "subscriber_count_or_none": _normalized_count(view.visible_subscriber_count_or_none),
            "active_user_count_or_none": _normalized_count(view.visible_active_user_count_or_none),
            "source_surface": _observation_surface_for(view.listing_url),
            "provenance_pointer": read.manifest_path,
            "absent_reason_or_none": view.visible_volume_signal_absent_reason_or_none,
        }
    )

    if _should_apply_status_observation(row=row, observed_at=read.observed_at):
        if row.get("status") != "active":
            row.setdefault("descriptive_changes", []).append(
                {"field": "status", "changed_at": read.observed_at, "previous_value": row.get("status")}
            )
            row["status"] = "active"
            outcome.status_changes.append(read.subreddit)
        row["status_observed_at"] = read.observed_at

    if row.get("capture_state") == "no_packet_recorded":
        row["capture_state"] = "grid_packets_recorded"

    register_pointers = row.setdefault("register_pointers", [])
    assert isinstance(register_pointers, list)
    if read.manifest_path not in register_pointers:
        register_pointers.append(read.manifest_path)
    return True


def _resolve_preserved_file(packet, *, file_name: str, required: bool = True) -> dict[str, str] | None:
    matching_files = [
        {"relative_packet_path": item.relative_packet_path, "sha256": item.sha256}
        for item in packet.preserved_files
        if item.relative_packet_path.replace("\\", "/").endswith(file_name)
    ]
    if not matching_files and not required:
        return None
    if len(matching_files) != 1:
        raise RegistryRefreshError(
            "preserved_file_unresolved",
            f"expected exactly one preserved {file_name}, found {len(matching_files)}",
        )
    return matching_files[0]


def _resolve_grid_metadata_file(
    packet, *, expected_locator: str
) -> dict[str, str]:
    """Resolve the metadata transport the declared listing host requires.

    A packet may preserve additional transport metadata alongside the required
    one (trunk runner shape, PR #1424); only the declared host's metadata is
    load-bearing here, so extras are ignored rather than refused.
    """
    is_www = urlparse(expected_locator).netloc.lower() == WWW_REDDIT_LISTING_HOST
    expected_name = (
        "realchrome_snapshot_metadata.json"
        if is_www
        else "http_response_metadata.json"
    )
    expected = _resolve_preserved_file(
        packet, file_name=expected_name, required=False
    )
    if expected is None:
        raise RegistryRefreshError(
            "preserved_file_unresolved",
            f"expected exactly one preserved {expected_name}, found 0",
        )
    return expected


def _resolve_packet_file_path(
    *,
    packet_dir: Path,
    relative_packet_path: str,
    error_code: str,
    file_label: str,
) -> Path:
    packet_root = packet_dir.resolve()
    candidate = (packet_root / relative_packet_path).resolve()
    if not candidate.is_relative_to(packet_root):
        raise RegistryRefreshError(
            error_code,
            f"{file_label} path escapes packet directory: {relative_packet_path!r}",
        )
    return candidate


def _verify_preserved_file_hash(*, path: Path, expected_hash: str, error_code: str) -> None:
    actual_hash = hash_file(path)
    if actual_hash != expected_hash:
        raise RegistryRefreshError(
            error_code,
            f"stored bytes hash mismatch for {path.name}: manifest={expected_hash} actual={actual_hash}",
        )


def _verify_successful_grid_response(
    *,
    packet,
    metadata_path: Path,
    expected_locator: str,
    expected_subreddit: str,
) -> None:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RegistryRefreshError(
            "http_metadata_unreadable",
            f"preserved HTTP metadata could not be read: {exc}",
        ) from exc
    if not isinstance(metadata, dict):
        raise RegistryRefreshError(
            "http_metadata_shape",
            "preserved HTTP metadata is not a JSON object",
        )
    is_www = urlparse(expected_locator).netloc.lower() == WWW_REDDIT_LISTING_HOST
    status_key = "http_response_status" if is_www else "status"
    unexpected_status_key = "status" if is_www else "http_response_status"
    if unexpected_status_key in metadata:
        raise RegistryRefreshError(
            "http_metadata_shape",
            f"grid metadata carries unexpected status key {unexpected_status_key!r} "
            f"for its declared listing transport",
        )
    status = metadata.get(status_key)
    if type(status) is not int or not 200 <= status < 300:
        raise RegistryRefreshError(
            "grid_access_unsuccessful",
            f"grid packet {status_key} is not a successful integer status: {status!r}",
        )
    if is_www:
        access_blocked = metadata.get("access_blocked")
        classification = metadata.get("rendered_access_classification")
        if type(access_blocked) is not bool:
            raise RegistryRefreshError(
                "http_metadata_shape",
                "real-Chrome grid metadata must carry a boolean access_blocked value",
            )
        # Grafted from the trunk verifier (PR #1424): the packet must declare
        # its capture method, and the REQUESTED url must match the locator too
        # -- a redirect-to-lookalike would otherwise pass on final_url alone.
        if metadata.get("method_category") != "real_browser_cdp":
            raise RegistryRefreshError(
                "grid_access_unsuccessful",
                "real-Chrome grid packet metadata does not declare real_browser_cdp",
            )
        requested_url = metadata.get("requested_url")
        if not isinstance(requested_url, str) or not same_grid_listing_url(
            requested_url, expected_locator
        ):
            raise RegistryRefreshError(
                "grid_final_locator_mismatch",
                "real-Chrome requested URL does not match the packet locator: "
                f"{requested_url!r}",
            )
        if access_blocked or classification == "access_blocked":
            raise RegistryRefreshError(
                "grid_access_unsuccessful",
                "grid packet records an access block: "
                f"{metadata.get('access_block_reason')!r}",
            )
        # Absent classification is the trunk metadata shape (five keys); only
        # an unknown *string* is refused.
        if classification not in {
            None,
            "no_block_marker",
            "residual_challenge_marker",
        }:
            raise RegistryRefreshError(
                "http_metadata_shape",
                "real-Chrome grid metadata carries an unknown rendered access "
                f"classification: {classification!r}",
            )
    final_url = metadata.get("final_url")
    if (
        final_url is not None
        and (
            not isinstance(final_url, str)
            or not same_grid_listing_url(final_url, expected_locator)
        )
    ):
        raise RegistryRefreshError(
            "grid_final_locator_mismatch",
            "grid packet final URL does not match its declared listing locator: "
            f"final={final_url!r} declared={expected_locator!r}",
        )
    for source_slice in packet.source_slices:
        locator = source_slice.locator.value
        access_posture = source_slice.access_posture.value or ""
        successful_posture = (
            access_posture.startswith(
                "real_browser_cdp preserved rendered public page artifacts"
            )
            if is_www
            else access_posture.startswith("direct_http succeeded with HTTP 2")
        )
        if (
            isinstance(locator, str)
            and same_grid_listing_url(locator, expected_locator)
            and _subreddit_from_listing_url(
                locator,
                expected_host=(
                    WWW_REDDIT_LISTING_HOST if is_www else OLD_REDDIT_LISTING_HOST
                ),
            )
            == expected_subreddit
            and successful_posture
        ):
            return
    raise RegistryRefreshError(
        "grid_access_unsuccessful",
        "grid packet carries no successful source slice for its declared Reddit listing",
    )


def _verify_successful_realchrome_grid_response(
    *,
    packet,
    metadata_path: Path,
    expected_subreddit: str,
    expected_locator: str,
) -> None:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RegistryRefreshError(
            "realchrome_metadata_unreadable",
            f"preserved real-Chrome metadata could not be read: {exc}",
        ) from exc
    if not isinstance(metadata, dict):
        raise RegistryRefreshError(
            "realchrome_metadata_shape",
            "preserved real-Chrome metadata is not a JSON object",
        )
    status = metadata.get("http_response_status")
    if not isinstance(status, int) or not 200 <= status < 300:
        raise RegistryRefreshError(
            "grid_access_unsuccessful",
            f"real-Chrome grid packet status is not successful: {status!r}",
        )
    if metadata.get("access_blocked") is not False:
        raise RegistryRefreshError(
            "grid_access_unsuccessful",
            "real-Chrome grid packet does not prove an unblocked rendered page",
        )
    if metadata.get("method_category") != "real_browser_cdp":
        raise RegistryRefreshError(
            "grid_access_unsuccessful",
            "real-Chrome grid packet metadata does not declare real_browser_cdp",
        )
    requested_url = metadata.get("requested_url")
    final_url = metadata.get("final_url")
    for label, value in (("requested", requested_url), ("final", final_url)):
        if not isinstance(value, str) or not _same_supported_listing_url(
            value,
            expected_locator,
            expected_host="www.reddit.com",
        ):
            raise RegistryRefreshError(
                "grid_final_locator_mismatch",
                f"real-Chrome {label} URL does not match the packet locator: {value!r}",
            )
    for source_slice in packet.source_slices:
        slice_locator = source_slice.locator.value
        access_posture = source_slice.access_posture.value or ""
        if (
            isinstance(slice_locator, str)
            and _subreddit_from_listing_url(
                slice_locator, expected_host="www.reddit.com"
            )
            == expected_subreddit
            and _same_supported_listing_url(
                slice_locator,
                expected_locator,
                expected_host="www.reddit.com",
            )
            and access_posture.startswith("real_browser_cdp preserved")
        ):
            return
    raise RegistryRefreshError(
        "grid_access_unsuccessful",
        "grid packet carries no successful real-Chrome source slice for the declared subreddit",
    )


def _same_supported_listing_url(
    actual_url: str,
    expected_url: str,
    *,
    expected_host: str,
) -> bool:
    try:
        actual = urlparse(actual_url)
        expected = urlparse(expected_url)
    except (TypeError, ValueError):
        return False
    return (
        actual.scheme.lower() == expected.scheme.lower() == "https"
        and actual.netloc.lower() == expected.netloc.lower() == expected_host
        and actual.path.rstrip("/").casefold()
        == expected.path.rstrip("/").casefold()
        and sorted(parse_qsl(actual.query, keep_blank_values=True))
        == sorted(parse_qsl(expected.query, keep_blank_values=True))
    )


def _subreddit_from_listing_url(
    url: str,
    *,
    expected_host: str = "old.reddit.com",
) -> str | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme == "https"
        and parsed.netloc.lower() == expected_host
        and len(parts) >= 3
        and parts[0] == "r"
        and parts[1].isascii()
        and parts[1].replace("_", "").isalnum()
        and parts[2] in {"hot", "new", "top", "rising"}
    ):
        return parts[1].lower()
    return None


def _observed_date(packet) -> str:
    for source_slice in packet.source_slices:
        capture_time = source_slice.timing.capture_time.value
        if capture_time:
            candidate = str(capture_time)[:10]
            try:
                return date.fromisoformat(candidate).isoformat()
            except ValueError as exc:
                raise RegistryRefreshError(
                    "capture_time_invalid",
                    f"packet slice capture_time is not an ISO date: {capture_time!r}",
                ) from exc
    raise RegistryRefreshError("capture_time_missing", "packet carries no slice capture_time")


def _should_apply_status_observation(*, row: dict[str, object], observed_at: str) -> bool:
    current_value = row.get("status_observed_at")
    if not isinstance(current_value, str) or not current_value:
        return True
    try:
        current_date = date.fromisoformat(current_value)
        incoming_date = date.fromisoformat(observed_at)
    except ValueError as exc:
        raise RegistryRefreshError(
            "registry_status_date_invalid",
            f"registry row carries a non-ISO status_observed_at: {current_value!r}",
        ) from exc
    if incoming_date > current_date:
        return True
    if incoming_date < current_date:
        return False
    return row.get("status") in {None, "unverified", "active"}


def _normalized_count(value: str | None) -> str | None:
    if value is None:
        return None
    digits = value.replace(",", "").strip()
    if digits.isdigit():
        return digits
    return value
