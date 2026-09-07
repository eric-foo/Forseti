"""CLI: scan ONE IG creator's reels grid, rank by engagement, deep-capture top-N.

Loads the creator's public ``/<handle>/reels/`` grid ONCE (the same bounded,
no-item-fan-out capture the grid-packet runner uses), ranks the joined reel rows
by engagement = (like_count or 0) + (comment_count or 0) descending, takes the
top-N shortcodes, and runs the ONE-render deep-capture (audience comments +
creator transcript) on each, persisting per reel when ``--data-root`` is set.

The render/download/transcribe/persist legs are REUSED wholesale from
``run_source_capture_ig_reels_deep_capture`` -- this runner only adds the
grid-scan + rank + select-top-N + per-reel loop on top. The orchestration core
(``rank_reels_by_engagement`` + ``select_and_capture_top_reels``) is PURE with
injected dependencies, mirroring ``run_reel_deep_capture``, so it is offline-testable.

No-LLM zone (``runners/``): imports the browser adapter, the deterministic grid
and deep-capture parsers, and the agnostic transcriber -- no LLM SDK. Public data
only, anonymous. A per-reel deep-capture failure is recorded and does NOT abort the
remaining reels; a grid-capture failure fails closed with a typed nonzero exit.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners.run_source_capture_ig_reels_deep_capture import (
    _make_downloader,
    _persist_deep_capture,
    _render,
    _resolve_optional_data_root,
)
from runners.run_source_capture_ig_reels_grid_packet import _detect_ig_block
from data_lake.root import DataLakeRootError
from source_capture.ig_reels_deep_capture import ReelDeepCaptureResult, run_reel_deep_capture
from source_capture.ig_reels_grid import (
    MEDIA_KIND_REEL,
    IgReelsJoinedRow,
    IgReelsJsonCandidate,
    iter_json_media_candidates,
    join_dom_rows_with_json_candidates,
    normalize_dom_grid_rows,
)
from source_capture.ig_reels_grid_capture import (
    DEFAULT_IG_REELS_MAX_RESPONSE_BYTES,
    DEFAULT_IG_REELS_SETTLE_SECONDS,
    DEFAULT_IG_REELS_TIMEOUT_SECONDS,
    DEFAULT_IG_REELS_VIEWPORT_HEIGHT,
    DEFAULT_IG_REELS_VIEWPORT_WIDTH,
    IgReelsGridCaptureFailure,
    IgReelsGridCaptureResult,
    IgReelsGridCaptureSuccess,
    fetch_ig_reels_grid_capture,
)
from source_capture.transcript.audio_asr import AudioTranscriber

DEFAULT_TOP_N = 3
DEFAULT_MODEL = "small"
DEFAULT_GRID_MAX_ROWS = 12


@dataclass(frozen=True)
class RankedReel:
    """One ranked reel-grid row: the shortcode plus the engagement it ranked on.

    ``engagement`` = ``(like_count or 0) + (comment_count or 0)``. When IG serves the grid
    anonymously WITHOUT any like counts (``likes_hidden`` true), that signal collapses to comments
    only, so the grid is ranked by ``view_count`` instead (IG usually still exposes views). The raw
    counts are kept for the per-reel summary line. ``rank`` is 1-based after the descending sort.
    """

    rank: int
    shortcode: str
    engagement: int
    like_count: int | None
    comment_count: int | None
    view_count: int | None = None
    likes_hidden: bool = False


@dataclass(frozen=True)
class CapturedReel:
    """The outcome of deep-capturing one ranked reel.

    Exactly one of ``result``/``error`` is set: a per-reel capture that raised is
    recorded here with ``error`` (and does NOT abort the batch). ``persisted`` is the
    persistence status line, or None when persistence was not requested.
    """

    ranked: RankedReel
    result: ReelDeepCaptureResult | None
    error: str | None = None
    persisted: str | None = None

    @property
    def ok(self) -> bool:
        return self.result is not None


# --- PURE orchestration core (all I/O injected, so offline-testable) -------------

# shortcode -> deep-capture result; may raise, which the loop records without aborting.
CaptureFn = Callable[[str], ReelDeepCaptureResult]
# captured reel + its ranked metadata -> persistence status line.
PersistFn = Callable[[ReelDeepCaptureResult, RankedReel], str]


def _best_engagement_candidate(
    candidates: Sequence[IgReelsJsonCandidate],
) -> IgReelsJsonCandidate | None:
    """Pick the candidate to rank on -- the one carrying the most engagement signal.

    A shortcode can join multiple passive-JSON surfaces (e.g. ``clips/user`` and
    ``web_profile_info``) that need not agree. Rather than hard-code a surface
    priority, rank on the candidate whose own (likes + comments) is largest, so a
    surface that simply omitted the counts never masks one that has them. None of
    the joined candidates carrying any count yields a 0-engagement reel (still
    captured if selected), not a crash.
    """
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: (
            _candidate_engagement(candidate),
            candidate.like_count is not None,  # on an engagement tie, never discard a visible like
            candidate.video_or_play_count or 0,
        ),
    )


def _candidate_engagement(candidate: IgReelsJsonCandidate) -> int:
    return (candidate.like_count or 0) + (candidate.comment_count or 0)


def rank_reels_by_engagement(joined_rows: Sequence[IgReelsJoinedRow]) -> list[RankedReel]:
    """Rank joined reel-grid rows by engagement DESCENDING.

    Engagement = ``(likes + comments)``. But IG serves the public ``/reels/`` grid anonymously
    WITHOUT like counts inconsistently; when NO reel in the grid carries a like count
    (``likes_hidden``), that signal collapses to comments only, so the grid is instead ranked by
    ``view_count`` -- the engagement signal IG usually still exposes -- rather than on near-zero
    comment counts. None counts are 0. Rows without a shortcode are dropped. The sort is STABLE, so
    ties keep grid (DOM) order -- deterministic.
    """
    # Regime is grid-level: likes are "hidden" only when NO candidate ANYWHERE in the grid carries a
    # like count. Computed across ALL joined candidates -- not the per-reel SELECTED one -- so the
    # ranking-candidate choice (which may tie-break to a no-likes surface) cannot flip the regime; a
    # visible like on an unselected candidate still counts.
    likes_hidden = not any(
        candidate.like_count is not None
        for joined in joined_rows
        for candidate in joined.source_surface_candidates
    )
    scored: list[tuple[str, int, int | None, int | None, int | None]] = []
    for joined in joined_rows:
        shortcode = (joined.dom_row.shortcode or "").strip()
        if not shortcode:
            continue
        best = _best_engagement_candidate(joined.source_surface_candidates)
        like_count = best.like_count if best is not None else None
        comment_count = best.comment_count if best is not None else None
        view_count = best.video_or_play_count if best is not None else None
        engagement = (like_count or 0) + (comment_count or 0)
        scored.append((shortcode, engagement, like_count, comment_count, view_count))
    if likes_hidden:
        scored.sort(key=lambda item: ((item[4] or 0), item[1]), reverse=True)  # views, then comments
    else:
        scored.sort(key=lambda item: item[1], reverse=True)  # likes + comments
    return [
        RankedReel(
            rank=index,
            shortcode=shortcode,
            engagement=engagement,
            like_count=like_count,
            comment_count=comment_count,
            view_count=view_count,
            likes_hidden=likes_hidden,
        )
        for index, (shortcode, engagement, like_count, comment_count, view_count) in enumerate(scored, start=1)
    ]


def select_and_capture_top_reels(
    ranked_reels: Sequence[RankedReel],
    *,
    top_n: int,
    capture_fn: CaptureFn,
    persist_fn: PersistFn | None = None,
) -> list[CapturedReel]:
    """Take the top-N ranked reels and deep-capture each, in rank order.

    Every side-effecting step is injected (``capture_fn`` renders+derives one reel;
    optional ``persist_fn`` writes it), so the control flow is deterministic and
    offline-testable; the CLI supplies the real grid-render-backed capture + lake write.

    Resilience contract: a ``capture_fn`` that RAISES is recorded as a failed
    ``CapturedReel`` and does NOT stop the batch -- later reels are still captured.
    A larger ``top_n`` than available simply captures all of them. Persistence runs
    only for successfully captured reels and its own failure is recorded per reel.
    """
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    selected = list(ranked_reels[:top_n])
    captured: list[CapturedReel] = []
    for ranked in selected:
        try:
            result = capture_fn(ranked.shortcode)
        except Exception as exc:  # noqa: BLE001 - record per-reel failure, never abort the batch
            captured.append(CapturedReel(ranked=ranked, result=None, error=f"{type(exc).__name__}: {exc}"))
            continue
        persisted: str | None = None
        if persist_fn is not None:
            try:
                persisted = persist_fn(result, ranked)
            except Exception as exc:  # noqa: BLE001 - persistence failure is recorded, not fatal
                persisted = f"persist-failed: {type(exc).__name__}: {exc}"
        captured.append(CapturedReel(ranked=ranked, result=result, persisted=persisted))
    return captured


# --- live wiring (grid scan + per-reel capture) ----------------------------------


class IgReelsGridCaptureError(RuntimeError):
    """A grid-capture failure surfaced as a typed nonzero-exit signal for the CLI."""


def _normalize_handle(handle: str) -> str:
    normalized = handle.strip().lstrip("@")
    if not normalized or "/" in normalized or "\\" in normalized:
        raise ValueError("IG handle must be a non-empty handle, not a path")
    return normalized


def _reels_url_for_handle(handle: str) -> str:
    return f"https://www.instagram.com/{handle}/reels/"


def _json_candidates_from_passive_responses(
    capture: IgReelsGridCaptureSuccess,
) -> list[IgReelsJsonCandidate]:
    candidates: list[IgReelsJsonCandidate] = []
    for response in capture.passive_json_responses:
        if not response.body_text:
            continue
        try:
            payload = json.loads(response.body_text)
        except json.JSONDecodeError:
            continue
        candidates.extend(iter_json_media_candidates(payload, source_surface=response.source_surface))
    return candidates


def scan_creator_reels_ranked(
    *,
    handle: str,
    max_rows: int = DEFAULT_GRID_MAX_ROWS,
    timeout_seconds: float = DEFAULT_IG_REELS_TIMEOUT_SECONDS,
    settle_seconds: float = DEFAULT_IG_REELS_SETTLE_SECONDS,
    capture_fetcher: Callable[..., IgReelsGridCaptureResult] = fetch_ig_reels_grid_capture,
) -> tuple[list[RankedReel], IgReelsGridCaptureSuccess]:
    """Grid-capture the creator ONCE and return the engagement-ranked reel rows.

    Mirrors the grid-packet runner's capture + normalize + join sequence (reels only),
    then ranks. Raises ``IgReelsGridCaptureError`` on a grid-capture failure so the CLI
    can fail closed with a typed nonzero exit (mirroring the grid runner's handling).
    """
    profile_handle = _normalize_handle(handle)
    reels_url = _reels_url_for_handle(profile_handle)
    capture = capture_fetcher(
        reels_url=reels_url,
        profile_handle=profile_handle,
        timeout_seconds=timeout_seconds,
        viewport_width=DEFAULT_IG_REELS_VIEWPORT_WIDTH,
        viewport_height=DEFAULT_IG_REELS_VIEWPORT_HEIGHT,
        settle_seconds=settle_seconds,
        max_response_bytes=DEFAULT_IG_REELS_MAX_RESPONSE_BYTES,
        max_rows=max_rows,
        block_heavy_assets=True,
        proxy_profile=None,
        storage_state_path=None,
        headless=True,
        browser_channel=None,
    )
    if isinstance(capture, IgReelsGridCaptureFailure):
        raise IgReelsGridCaptureError(capture.message)
    block_reason = _detect_ig_block(final_url=capture.final_url, title=capture.title, visible_text=capture.visible_text)
    if block_reason is not None:
        raise IgReelsGridCaptureError(f"profile access-blocked ({block_reason}); no reels ranked")

    dom_rows = normalize_dom_grid_rows(
        capture.dom_rows,
        final_url=capture.final_url,
        profile_handle=profile_handle,
        max_rows=max_rows,
        allowed_kinds=(MEDIA_KIND_REEL,),
    )
    candidates = _json_candidates_from_passive_responses(capture)
    joined_rows = join_dom_rows_with_json_candidates(dom_rows, candidates)
    return rank_reels_by_engagement(joined_rows), capture


def _make_capture_fn(scratch: str, *, transcribe_fn: Callable) -> CaptureFn:
    """The real per-reel deep-capture: ONE render -> comments + transcript, reusing
    the deep-capture runner's render/download legs and the agnostic transcriber."""

    def _capture(shortcode: str) -> ReelDeepCaptureResult:
        return run_reel_deep_capture(
            shortcode,
            render_fn=_render,
            download_fn=_make_downloader(scratch),
            transcribe_fn=transcribe_fn,
        )

    return _capture


def _rank_basis(ranked: RankedReel) -> str:
    """How the reel was ranked -- views (with a 'likes hidden' note) when IG hid like counts."""
    if ranked.likes_hidden:
        return f"views={ranked.view_count} (likes hidden by IG; ranked on views)"
    return f"engagement={ranked.engagement}"


def _summary_line(captured: CapturedReel) -> str:
    ranked = captured.ranked
    if not captured.ok:
        return (
            f"rank={ranked.rank} shortcode={ranked.shortcode} "
            f"{_rank_basis(ranked)} deep_capture=failed ({captured.error})"
        )
    result = captured.result
    assert result is not None
    persisted = "n/a" if captured.persisted is None else captured.persisted
    return (
        f"rank={ranked.rank} shortcode={ranked.shortcode} "
        f"{_rank_basis(ranked)} comments={len(result.comments)} "
        f"transcript_posture={result.transcript_posture} persisted={persisted}"
    )


def run_creator_deep_capture(
    *,
    handle: str,
    top_n: int = DEFAULT_TOP_N,
    model: str = DEFAULT_MODEL,
    data_root: str | None = None,
    max_rows: int = DEFAULT_GRID_MAX_ROWS,
    capture_fetcher: Callable[..., IgReelsGridCaptureResult] = fetch_ig_reels_grid_capture,
    capture_fn: CaptureFn | None = None,
    persist_fn: PersistFn | None = None,
) -> tuple[list[RankedReel], list[CapturedReel]]:
    """Run the creator grid-rank -> top-N deep-capture sequence for callers.

    The CLI keeps printing human summaries; orchestrators use this function to get structured
    outcomes while preserving the same injected/offline-testable capture core.
    """
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    resolved_data_root = _resolve_optional_data_root(data_root)
    ranked, _capture = scan_creator_reels_ranked(
        handle=handle,
        max_rows=max_rows,
        capture_fetcher=capture_fetcher,
    )
    resolved_persist_fn = persist_fn
    if resolved_persist_fn is None and resolved_data_root is not None:
        resolved_persist_fn = lambda result, _ranked: _persist_deep_capture(
            result, data_root=resolved_data_root
        )

    if capture_fn is not None:
        return ranked, select_and_capture_top_reels(
            ranked,
            top_n=top_n,
            capture_fn=capture_fn,
            persist_fn=resolved_persist_fn,
        )

    with (
        tempfile.TemporaryDirectory(prefix="forseti_creator_deepcap_") as scratch,
        AudioTranscriber(model_name=model) as transcribe_fn,
    ):
        captured = select_and_capture_top_reels(
            ranked,
            top_n=top_n,
            capture_fn=_make_capture_fn(scratch, transcribe_fn=transcribe_fn),
            persist_fn=resolved_persist_fn,
        )
    return ranked, captured

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan one IG creator's public /reels/ grid, rank reels by engagement "
            "(likes + comments), and deep-capture the top-N (comments + transcript)."
        )
    )
    parser.add_argument("--handle", required=True, help="IG handle, with or without @.")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="How many top reels to deep-capture.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="faster-whisper model size.")
    parser.add_argument(
        "--data-root",
        default=None,
        help="Forseti data lake root (or FORSETI_DATA_ROOT (legacy ORCA_DATA_ROOT)). When set, persists each reel's "
        "silver deep-capture record-set (comments + transcript); omit for stdout-only.",
    )
    parser.add_argument("--max-rows", type=int, default=DEFAULT_GRID_MAX_ROWS, help="Max grid rows to scan.")
    args = parser.parse_args(argv)

    if args.top_n < 0:
        parser.exit(status=2, message="source capture ig reels creator deep-capture failed: --top-n must be >= 0\n")

    try:
        resolved_data_root = _resolve_optional_data_root(args.data_root)
        ranked, _capture = scan_creator_reels_ranked(handle=args.handle, max_rows=args.max_rows)
    except DataLakeRootError as exc:
        parser.exit(
            status=2,
            message=(
                "source capture ig reels creator deep-capture failed: "
                f"invalid Forseti data lake root: {exc}\n"
            ),
        )
        return 2
    except IgReelsGridCaptureError as exc:
        parser.exit(status=3, message=f"source capture ig reels creator deep-capture failed: grid capture failed: {exc}\n")
        return 3
    except ValueError as exc:
        parser.exit(status=2, message=f"source capture ig reels creator deep-capture failed: {exc}\n")
        return 2

    persist_fn: PersistFn | None = None
    if resolved_data_root is not None:
        persist_fn = lambda result, _ranked: _persist_deep_capture(
            result, data_root=resolved_data_root
        )

    with (
        tempfile.TemporaryDirectory(prefix="forseti_creator_deepcap_") as scratch,
        AudioTranscriber(model_name=args.model) as transcribe_fn,
    ):
        captured = select_and_capture_top_reels(
            ranked,
            top_n=args.top_n,
            capture_fn=_make_capture_fn(scratch, transcribe_fn=transcribe_fn),
            persist_fn=persist_fn,
        )
        # capture (render + transcription) happens inside this block, while the temp audio still exists.

    print(
        f"creator={_normalize_handle(args.handle)} "
        f"reels_in_grid={len(ranked)} deep_captured={len(captured)} top_n={args.top_n}"
    )
    for item in captured:
        print(f"  {_summary_line(item)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
