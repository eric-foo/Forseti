"""Supervised one-creator TikTok onboarding orchestration.

This module composes existing session-profile, page-observation, grid-selection,
and live-batch deep-capture substrate. It is deliberately bounded to one creator
and one caller-visible browser lease; it is not a scanner, scheduler, registry
writer, or CAPTCHA solver.
"""
from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

from harness_utils import hash_file
from source_capture.adapters.direct_http import (
    DirectHttpCaptureFailure,
    DirectHttpCaptureResult,
    DirectHttpCaptureSuccess,
    fetch_direct_http_capture,
)
from source_capture.adapters.browser_snapshot import (
    ActivityEventFn,
    BrowserDelayRange,
    BrowserPageObservationEngine,
    BrowserPageObservationSuccess,
    BrowserPagePointerAction,
    BrowserPagePointerTargetVariant,
    BrowserPageResponse,
    BrowserPageWheelAction,
    BrowserSnapshotFailure,
    ChromeCdpPageObservationSessionEngine,
    fetch_browser_page_observation_capture as _fetch_browser_page_observation_capture,
)
from source_capture.activity_journal import (
    SOURCE_CAPTURE_ACTIVITY_JSONL_NAME,
    SourceCaptureActivityJournal,
)
from source_capture.auth_state import validate_auth_state_provenance_requirement
from source_capture.browser_user_data import browser_user_data_path_for_label
from source_capture.cadence import CadenceMode, CadencePlan, build_cadence_plan
from source_capture.session_profiles import SourceCaptureSessionProfile
from source_capture.tiktok.admission import (
    assert_no_sensitive_tiktok_material,
    json_dumps_sanitized,
)
from source_capture.tiktok.grid_video_selection import build_tiktok_grid_video_selection
from source_capture.tiktok.live_batch_probe import (
    TIKTOK_ACCOUNT_SAFETY_STOP_MARKERS,
    TIKTOK_BROWSER_BACKEND_CHROME_CDP,
    TIKTOK_CHALLENGE_TEXT_MARKERS,
    TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
    TIKTOK_LOGGED_OUT_STRUCTURAL_STOP_RULE,
    TIKTOK_LIVE_BATCH_CADENCE_JSON_NAME,
    TIKTOK_LIVE_BATCH_GRID_JSON_NAME,
    TIKTOK_PAGE_SETTLE_DELAY_RANGE,
    TIKTOK_STATE_WAIT_1000_DELAY_RANGE,
    TIKTOK_STATE_WAIT_1500_DELAY_RANGE,
    TIKTOK_STATE_WAIT_2000_DELAY_RANGE,
    TIKTOK_STATE_WAIT_2500_DELAY_RANGE,
    TIKTOK_VIDEO_DOM_EXTRACT_SCRIPT,
    is_exact_tiktok_subtitle_response_url,
    is_tiktok_comment_list_url,
    run_tiktok_live_batch_probe,
    tiktok_subtitle_url_from_source,
)


TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION = "tiktok_creator_onboarding_v1"
TIKTOK_ONBOARDING_SUGGESTED_JSON_NAME = "tiktok_suggested_accounts_attempt.json"
TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME = "tiktok_grid_window.json"
TIKTOK_ONBOARDING_SELECTION_JSON_NAME = "tiktok_grid_video_selection.json"
TIKTOK_ONBOARDING_RECEIPT_JSON_NAME = "tiktok_creator_onboarding_receipt.json"
TIKTOK_LINK_HUB_CAPTURE_MAX_BYTES = 1_000_000
TIKTOK_LINK_HUB_SOCIAL_LINK_CAP = 50
TIKTOK_CREATOR_MARKET_ASSESSMENT_SCHEMA_VERSION = (
    "tiktok_creator_market_assessment_v2"
)
TIKTOK_PROFILE_METRIC_CAPTURE_POLICY_VERSION = "tiktok_profile_metric_capture_v0"
TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS = (
    "playCount",
    "diggCount",
    "commentCount",
)
DEFAULT_WINDOW_SIZE = 30
DEFAULT_SELECTION_COUNT = 8
DEFAULT_MAX_GRID_SCROLL_PASSES = 40
TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MIN_GAP_SECONDS = 5.0
TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MAX_GAP_SECONDS = 20.0
TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MIN_GAP_SECONDS = 20.0
TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MAX_GAP_SECONDS = 60.0
TIKTOK_ONBOARDING_LONG_TAIL_TAIL_PROBABILITY = 0.05
GRID_ENTRY_RETRY_DELAY_RANGE = BrowserDelayRange(min_ms=45_000, max_ms=75_000)
# Consecutive fresh-state-unchanged wheel passes that show the grid is not
# advancing under bounded wheel input. Reaching this cap stops the wheel bursts
# and fails loudly instead of burning the full pagination budget on no-value
# actions. It never triggers a wait: the only authorized long retry wait is after
# a failed matching-overlay materialization (creator discovery enforcement
# placement doctrine), never in the grid-pagination path.
GRID_PAGINATION_NO_PROGRESS_STALL_LIMIT = 3
GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MIN = 0.20
GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MAX = 0.35
GRID_ACQUISITION_BATCH_REVEAL_WHEEL_CAP = 4
GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT = 27
GRID_ACQUISITION_STABILITY_POLL_TARGET = 2
GRID_ACQUISITION_STABILITY_POLL_CAP = 4

SleepFn = Callable[[float], None]
MonotonicFn = Callable[[], float]
UtcNowFn = Callable[[], datetime]
LinkHubFetchFn = Callable[..., DirectHttpCaptureResult]

_LINK_HUB_HOSTS = frozenset(
    {
        "allmylinks.com",
        "beacons.ai",
        "bio.site",
        "campsite.bio",
        "link.me",
        "linktr.ee",
        "lnk.bio",
        "solo.to",
        "stan.store",
    }
)
_SOCIAL_HOST_KINDS = {
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "pinterest.com": "pinterest",
    "snapchat.com": "snapchat",
    "threads.net": "threads",
    "tiktok.com": "tiktok",
    "twitch.tv": "twitch",
    "twitter.com": "x",
    "x.com": "x",
    "youtu.be": "youtube",
    "youtube.com": "youtube",
}


class _LinkHubHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchor_hrefs: list[str] = []
        self.json_ld_texts: list[str] = []
        self._json_ld_parts: list[str] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key.lower(): value for key, value in attrs}
        if tag.lower() == "a" and attributes.get("href"):
            self.anchor_hrefs.append(str(attributes["href"]))
        if (
            tag.lower() == "script"
            and str(attributes.get("type") or "").lower() == "application/ld+json"
        ):
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._json_ld_parts is not None:
            self.json_ld_texts.append("".join(self._json_ld_parts))
            self._json_ld_parts = None


class _TemporaryPageObservationEngine:
    def __init__(self, engine: BrowserPageObservationEngine) -> None:
        self._engine = engine

    def capture_page_observation(
        self, **kwargs: object
    ) -> BrowserPageObservationSuccess:
        capture = getattr(self._engine, "capture_temporary_page_observation", None)
        if not callable(capture):
            raise RuntimeError(
                "browser engine does not support temporary-page observation"
            )
        result = capture(**kwargs)
        if not isinstance(result, BrowserPageObservationSuccess):
            raise RuntimeError("temporary-page observation returned an invalid result")
        return result

TIKTOK_PROFILE_GRID_DOM_EXTRACT_SCRIPT = r"""
(arg) => {
  const creator = String((arg && arg.creator_handle) || '')
    .trim()
    .replace(/^@/, '')
    .toLowerCase();
  const seen = new Set();
  const videos = [];
  for (const anchor of Array.from(document.querySelectorAll('a[href*="/video/"]'))) {
    const href = String(anchor.href || anchor.getAttribute('href') || '');
    const match = href.match(/\/@([^/]+)\/video\/(\d+)/);
    if (
      !creator ||
      !match ||
      match[1].toLowerCase() !== creator ||
      seen.has(match[2])
    ) continue;
    seen.add(match[2]);
    let container = anchor;
    let pinnedVisible = false;
    for (let depth = 0; container && depth < 5; depth += 1) {
      const text = String(container.innerText || container.textContent || '').toLowerCase();
      if (text.includes('pinned') || container.querySelector('[data-e2e*="pinned"]')) {
        pinnedVisible = true;
        break;
      }
      container = container.parentElement;
    }
    const style = window.getComputedStyle(anchor);
    const box = anchor.getBoundingClientRect();
    const intersectsViewport = box.bottom > 0 && box.right > 0 &&
      box.top < window.innerHeight && box.left < window.innerWidth;
    const visibleInViewport = style.visibility !== 'hidden' && style.display !== 'none' &&
      box.width > 0 && box.height > 0 && intersectsViewport;
    const viewCountFooter = anchor.querySelector('.video-count');
    const viewCountText = viewCountFooter
      ? String(viewCountFooter.innerText || viewCountFooter.textContent || '').trim()
      : '';
    videos.push({
      video_id: match[2],
      video_url: href,
      pinned_visible: pinnedVisible,
      visible_in_viewport: visibleInViewport,
      view_count_text_or_none: viewCountText || null,
      view_count_footer_present: Boolean(viewCountFooter),
      grid_position: videos.length + 1
    });
  }
  const hydration = document.querySelector('#__UNIVERSAL_DATA_FOR_REHYDRATION__');
  const profileBioNode = document.querySelector('[data-e2e="user-bio"]');
  const profileBioText = profileBioNode
    ? String(profileBioNode.innerText || profileBioNode.textContent || '').trim()
    : '';
  const linkHubHosts = [
    'linktr.ee', 'link.me', 'beacons.ai', 'bio.site', 'lnk.bio', 'stan.store',
    'allmylinks.com', 'solo.to', 'campsite.bio'
  ];
  const absoluteUrl = (raw) => {
    const value = String(raw || '').trim();
    if (!value) return '';
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(value)) return value;
    if (value.startsWith('/')) return new URL(value, location.href).href;
    return 'https://' + value.replace(/^\/+/, '');
  };
  const normalizeHubUrl = (raw) => {
    try {
      let parsed = new URL(absoluteUrl(raw));
      const host = String(parsed.hostname || '').toLowerCase().replace(/^www\./, '');
      if (host === 'tiktok.com' || host.endsWith('.tiktok.com')) {
        const params = new URLSearchParams(parsed.search);
        const target = params.get('target') || params.get('url') || params.get('redirect_url');
        if (!target) return null;
        parsed = new URL(absoluteUrl(target));
      }
      const normalizedHost = String(parsed.hostname || '').toLowerCase().replace(/^www\./, '');
      if (
        !['http:', 'https:'].includes(parsed.protocol) ||
        !linkHubHosts.some((allowed) =>
          normalizedHost === allowed || normalizedHost.endsWith('.' + allowed)
        )
      ) return null;
      return {
        url: parsed.origin + parsed.pathname,
        host: normalizedHost
      };
    } catch (_error) {
      return null;
    }
  };
  const profileExternalLinks = [];
  const seenProfileExternalLinks = new Set();
  const addProfileExternalLink = (raw, source, displayText) => {
    const normalized = normalizeHubUrl(raw);
    if (!normalized || seenProfileExternalLinks.has(normalized.url)) return;
    seenProfileExternalLinks.add(normalized.url);
    profileExternalLinks.push({
      url: normalized.url,
      host: normalized.host,
      display_text_or_none: String(displayText || '').trim() || null,
      detection_source: source
    });
  };
  for (const anchor of Array.from(document.querySelectorAll(
    'a[data-e2e="user-link"][href],[data-e2e="user-link"] a[href],'
    + '[data-e2e="user-bio"] a[href]'
  ))) {
    addProfileExternalLink(
      anchor.href || anchor.getAttribute('href') || '',
      'profile_dom',
      anchor.innerText || anchor.textContent || ''
    );
  }
  if (hydration && hydration.textContent) {
    try {
      const hydrated = JSON.parse(hydration.textContent);
      const user = hydrated && hydrated.__DEFAULT_SCOPE__ &&
        hydrated.__DEFAULT_SCOPE__['webapp.user-detail'] &&
        hydrated.__DEFAULT_SCOPE__['webapp.user-detail'].userInfo &&
        hydrated.__DEFAULT_SCOPE__['webapp.user-detail'].userInfo.user;
      const bioLink = user && user.bioLink;
      addProfileExternalLink(
        bioLink && (bioLink.link || bioLink.url),
        'profile_hydration',
        bioLink && (bioLink.displayLink || bioLink.link || bioLink.url)
      );
    } catch (_error) {
      // The raw hydration text is still retained for the existing metric parser.
    }
  }
  const profileMetric = (selector) => {
    const node = document.querySelector(selector);
    const rawText = node
      ? String(node.innerText || node.textContent || '').trim()
      : '';
    return {
      element_present: Boolean(node),
      raw_text_or_none: rawText || null
    };
  };
  return {
    ordered_videos: videos,
    hydration_json_text: hydration ? hydration.textContent : null,
    profile_bio_text_or_none: profileBioText || null,
    profile_bio_element_detected: Boolean(profileBioNode),
    profile_external_links: profileExternalLinks,
    profile_metric_dom: {
      follower_count: profileMetric('strong[data-e2e="followers-count"]'),
      profile_total_like_count: profileMetric('strong[data-e2e="likes-count"]')
    }
  };
}
""".strip()

TIKTOK_OLDEST_POST_DOM_EXTRACT_SCRIPT = r"""
(arg) => {
  const creator = String((arg && arg.creator_handle) || '')
    .trim().replace(/^@/, '').toLowerCase();
  const controls = Array.from(document.querySelectorAll(
    '#user-post-sort-control button,#user-post-sort-control [role="button"],'
    + '#user-post-sort-control [role="tab"]'
  ));
  const oldest = controls.find((node) =>
    String(node.getAttribute('aria-label') || node.innerText || node.textContent || '')
      .trim().toLowerCase() === 'oldest'
  ) || null;
  const latest = controls.find((node) =>
    String(node.getAttribute('aria-label') || node.innerText || node.textContent || '')
      .trim().toLowerCase() === 'latest'
  ) || null;
  const seen = new Set();
  const orderedVideos = [];
  for (const anchor of Array.from(document.querySelectorAll('a[href*="/video/"]'))) {
    const href = String(anchor.href || anchor.getAttribute('href') || '');
    const match = href.match(/\/@([^/]+)\/video\/(\d+)/);
    if (!match || match[1].toLowerCase() !== creator || seen.has(match[2])) continue;
    seen.add(match[2]);
    let container = anchor;
    let pinnedVisible = false;
    for (let depth = 0; container && depth < 5; depth += 1) {
      const text = String(container.innerText || container.textContent || '').toLowerCase();
      if (text.includes('pinned') || container.querySelector('[data-e2e*="pinned"]')) {
        pinnedVisible = true;
        break;
      }
      container = container.parentElement;
    }
    orderedVideos.push({
      video_id: match[2],
      video_url: href,
      pinned_visible: pinnedVisible
    });
  }
  const bodyText = String(document.body && (document.body.innerText || document.body.textContent) || '')
    .toLowerCase();
  return {
    sort_control_present: controls.length > 0,
    oldest_control_present: Boolean(oldest),
    oldest_active: Boolean(oldest && oldest.getAttribute('data-active') === 'true'),
    latest_active: Boolean(latest && latest.getAttribute('data-active') === 'true'),
    ordered_videos: orderedVideos,
    no_public_posts_visible: bodyText.includes('no videos') || bodyText.includes('no posts')
  };
}
""".strip()

TIKTOK_LINK_HUB_DOM_EXTRACT_SCRIPT = r"""
() => {
  const anchors = Array.from(document.querySelectorAll('a[href]')).map((anchor) => ({
    href: String(anchor.href || anchor.getAttribute('href') || ''),
    display_text_or_none:
      String(anchor.innerText || anchor.textContent || '').trim() || null
  }));
  const jsonLdTexts = Array.from(
    document.querySelectorAll('script[type="application/ld+json"]')
  ).map((node) => String(node.textContent || ''));
  return {
    anchors,
    json_ld_texts: jsonLdTexts,
    document_title_or_none: String(document.title || '').trim() || null
  };
}
""".strip()

TIKTOK_SUGGESTED_ACCOUNTS_DOM_EXTRACT_SCRIPT = r"""
(arg) => {
  const creator = String((arg && arg.creator_handle) || '').toLowerCase();
  const visible = (node) => {
    if (!node) return false;
    const style = window.getComputedStyle(node);
    const box = node.getBoundingClientRect();
    return style.visibility !== 'hidden' && style.display !== 'none' && box.width > 0 && box.height > 0;
  };
  const profileAnchors = (root) => Array.from(
    root.querySelectorAll('a[href^="/@"],a[href*="tiktok.com/@"]')
  );
  const exactSuggestedNodes = Array.from(document.querySelectorAll('body *')).filter((node) =>
    visible(node) && String(node.innerText || node.textContent || '').trim().toLowerCase() === 'suggested'
  );
  let dialog = null;
  let suggestedTab = null;
  for (const node of exactSuggestedNodes) {
    let current = node;
    while (current && current !== document.body) {
      const text = String(current.innerText || current.textContent || '').toLowerCase();
      if (text.includes('following') && text.includes('followers') && text.includes('suggested') && profileAnchors(current).length > 0) {
        dialog = current;
        suggestedTab = node;
        break;
      }
      current = current.parentElement;
    }
    if (dialog) break;
  }
  const rows = [];
  const seen = new Set();
  let suggestedProfileAnchorCount = dialog ? profileAnchors(dialog).length : 0;
  if (dialog) {
    const anchors = profileAnchors(dialog);
    for (const anchor of anchors) {
      const href = String(anchor.href || anchor.getAttribute('href') || '');
      const match = href.match(/\/@([^/?#]+)/);
      if (!match) continue;
      const handle = match[1].toLowerCase();
      if (!handle || handle === creator || seen.has(handle)) continue;
      seen.add(handle);
      rows.push({
        handle,
        profile_url: 'https://www.tiktok.com/@' + handle,
        display_text_or_none: String(anchor.innerText || anchor.textContent || '').trim() || null
      });
    }
  }
  const profileBioNode = document.querySelector('[data-e2e="user-bio"]');
  const profileBioText = profileBioNode
    ? String(profileBioNode.innerText || profileBioNode.textContent || '').trim()
    : '';
  const externalLinks = [];
  const seenExternal = new Set();
  for (const anchor of Array.from(document.querySelectorAll('a[href]'))) {
    try {
      const url = new URL(String(anchor.href || anchor.getAttribute('href') || ''), location.href);
      const host = String(url.hostname || '').toLowerCase();
      if (!['http:', 'https:'].includes(url.protocol) || !host || host === 'tiktok.com' || host.endsWith('.tiktok.com')) continue;
      const cleanUrl = url.origin + url.pathname;
      if (seenExternal.has(cleanUrl)) continue;
      seenExternal.add(cleanUrl);
      externalLinks.push({
        url: cleanUrl,
        host,
        display_text_or_none: String(anchor.innerText || anchor.textContent || '').trim() || null
      });
    } catch (_error) {
      continue;
    }
  }
  return {
    suggested_accounts: rows,
    profile_bio_text_or_none: profileBioText || null,
    profile_bio_element_detected: Boolean(profileBioNode),
    profile_external_links: externalLinks,
    suggested_surface_detected: Boolean(dialog && suggestedTab),
    suggested_surface_root_count: dialog && suggestedTab ? 1 : 0,
    suggested_profile_anchor_count: suggestedProfileAnchorCount,
    relationship_dialog_detected: Boolean(dialog),
    suggested_tab_detected: Boolean(suggestedTab),
    suggested_route: 'followers_dialog_suggested_tab'
  };
}
""".strip()

TIKTOK_VISIBLE_SELECTED_GRID_TILES_DOM_EXTRACT_SCRIPT = r"""
(arg) => {
  const creator = String((arg && arg.creator_handle) || '').trim().replace(/^@/, '').toLowerCase();
  const selected = new Set(Array.isArray(arg && arg.selected_video_ids)
    ? arg.selected_video_ids.map((value) => String(value))
    : []);
  const seen = new Set();
  const rows = [];
  const visibleGridPositions = [];
  let gridPosition = 0;
  for (const anchor of Array.from(document.querySelectorAll('a[href*="/video/"]'))) {
    const href = String(anchor.href || anchor.getAttribute('href') || '');
    const match = href.match(/\/@([^/]+)\/video\/(\d+)/);
    if (!match || match[1].toLowerCase() !== creator || seen.has(match[2])) continue;
    seen.add(match[2]);
    gridPosition += 1;
    const style = window.getComputedStyle(anchor);
    const box = anchor.getBoundingClientRect();
    const intersectsViewport = box.bottom > 0 && box.right > 0 &&
      box.top < window.innerHeight && box.left < window.innerWidth;
    const visible = style.visibility !== 'hidden' && style.display !== 'none' &&
      box.width > 0 && box.height > 0 && intersectsViewport;
    if (!visible) continue;
    visibleGridPositions.push(gridPosition);
    if (!selected.has(match[2])) continue;
    const clickTarget = anchor.querySelector('.video-count');
    const clickTargetText = clickTarget
      ? String(clickTarget.innerText || clickTarget.textContent || '').trim()
      : '';
    const clickTargetStyle = clickTarget ? window.getComputedStyle(clickTarget) : null;
    const clickTargetBox = clickTarget ? clickTarget.getBoundingClientRect() : null;
    const clickTargetVisible = Boolean(
      clickTarget && clickTargetStyle && clickTargetBox &&
      clickTargetStyle.visibility !== 'hidden' && clickTargetStyle.display !== 'none' &&
      clickTargetBox.width > 0 && clickTargetBox.height > 0 &&
      clickTargetBox.bottom > 0 && clickTargetBox.right > 0 &&
      clickTargetBox.top < window.innerHeight && clickTargetBox.left < window.innerWidth
    );
    if (!clickTargetVisible || !clickTargetText) continue;
    rows.push({
      video_id: match[2],
      video_url: href,
      grid_position: gridPosition,
      bounding_box: {x: box.x, y: box.y, width: box.width, height: box.height},
      click_target_kind: 'link_routed_exact_video_semantic_targets',
      click_target_text_or_none: clickTargetText,
      click_target_visible_in_viewport: true
    });
  }
  return {
    visible_selected_tiles: rows,
    loaded_grid_video_ids: Array.from(seen),
    selected_video_count: selected.size,
    tile_scroll_performed: false,
    visible_grid_position_min_or_none: visibleGridPositions.length
      ? Math.min(...visibleGridPositions) : null,
    visible_grid_position_max_or_none: visibleGridPositions.length
      ? Math.max(...visibleGridPositions) : null,
    scroll_y: Math.max(0, Math.round(window.scrollY || 0)),
    viewport_height: Math.max(0, Math.round(window.innerHeight || 0)),
    document_height: Math.max(0, Math.round(document.documentElement.scrollHeight || 0))
  };
}
""".strip()

TIKTOK_FOLLOWERS_ACTION = BrowserPagePointerAction(
    action_name="tiktok_creator_followers_count_v0",
    candidate_selector=(
        "[data-e2e*='followers'],a[href*='/followers'],button,[role='button'],"
        "[role='link']"
    ),
    text_markers=("followers",),
    wait_after_range=TIKTOK_STATE_WAIT_1500_DELAY_RANGE,
    prefer_smallest_match=True,
)

TIKTOK_PROFILE_LATEST_SORT_ACTION = BrowserPagePointerAction(
    action_name="tiktok_profile_latest_sort_reset_v0",
    candidate_selector=(
        "#user-post-sort-control button,#user-post-sort-control [role='button'],"
        "#user-post-sort-control [role='tab']"
    ),
    text_markers=(),
    exact_text_markers=("latest",),
    wait_after_range=TIKTOK_STATE_WAIT_1500_DELAY_RANGE,
    prefer_smallest_match=True,
)

TIKTOK_PROFILE_OLDEST_SORT_ACTION = BrowserPagePointerAction(
    action_name="tiktok_profile_oldest_sort_v0",
    candidate_selector=(
        "#user-post-sort-control button,#user-post-sort-control [role='button'],"
        "#user-post-sort-control [role='tab']"
    ),
    text_markers=(),
    exact_text_markers=("oldest",),
    wait_after_range=TIKTOK_STATE_WAIT_2500_DELAY_RANGE,
    prefer_smallest_match=True,
)

TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION = BrowserPagePointerAction(
    action_name="tiktok_relationship_dialog_suggested_tab_v0",
    candidate_selector="[role='dialog'] *,[aria-modal='true'] *",
    text_markers=(),
    exact_text_markers=("suggested",),
    wait_after_range=TIKTOK_STATE_WAIT_2000_DELAY_RANGE,
    prefer_smallest_match=True,
)

TIKTOK_SUGGESTED_ACCOUNTS_FALLBACK_DOM_EXTRACT_SCRIPT = r"""
(arg) => {
  const creator = String((arg && arg.creator_handle) || '').toLowerCase();
  const profileAnchors = (root) => Array.from(
    root.querySelectorAll('a[href^="/@"],a[href*="tiktok.com/@"]')
  );
  const roots = [];
  const addSuggestedRoot = (node) => {
    let current = node;
    while (current && current !== document.body) {
      if (
        String(current.innerText || current.textContent || '').toLowerCase().includes('suggested accounts') &&
        profileAnchors(current).length > 0
      ) {
        if (!roots.includes(current)) roots.push(current);
        return;
      }
      current = current.parentElement;
    }
  };
  for (const node of Array.from(document.querySelectorAll('body *'))) {
    if (String(node.innerText || node.textContent || '').trim().toLowerCase() === 'suggested accounts') addSuggestedRoot(node);
  }
  for (const node of Array.from(document.querySelectorAll('[data-e2e*="suggest"]'))) addSuggestedRoot(node);
  const rows = [];
  const seen = new Set();
  let suggestedProfileAnchorCount = 0;
  for (const root of roots) {
    const anchors = profileAnchors(root);
    suggestedProfileAnchorCount += anchors.length;
    for (const anchor of anchors) {
      const href = String(anchor.href || anchor.getAttribute('href') || '');
      const match = href.match(/\/@([^/?#]+)/);
      if (!match) continue;
      const handle = match[1].toLowerCase();
      if (!handle || handle === creator || seen.has(handle)) continue;
      seen.add(handle);
      rows.push({
        handle,
        profile_url: 'https://www.tiktok.com/@' + handle,
        display_text_or_none: String(anchor.innerText || anchor.textContent || '').trim() || null
      });
    }
  }
  const profileBioNode = document.querySelector('[data-e2e="user-bio"]');
  const profileBioText = profileBioNode
    ? String(profileBioNode.innerText || profileBioNode.textContent || '').trim()
    : '';
  return {
    suggested_accounts: rows,
    profile_bio_text_or_none: profileBioText || null,
    profile_bio_element_detected: Boolean(profileBioNode),
    profile_external_links: [],
    suggested_surface_detected: roots.length > 0,
    suggested_surface_root_count: roots.length,
    suggested_profile_anchor_count: suggestedProfileAnchorCount,
    relationship_dialog_detected: false,
    suggested_tab_detected: false,
    suggested_route: 'profile_suggested_accounts_view_all_fallback'
  };
}
""".strip()

TIKTOK_SUGGESTED_SURFACE_CLOSED_DOM_EXTRACT_SCRIPT = r"""
() => {
  const visible = (node) => {
    if (!node) return false;
    const style = window.getComputedStyle(node);
    const box = node.getBoundingClientRect();
    return style.visibility !== 'hidden' && style.display !== 'none' &&
      box.width > 0 && box.height > 0;
  };
  const visibleThroughAncestors = (node) => {
    if (!visible(node)) return false;
    let current = node;
    while (current && current !== document.body) {
      const style = window.getComputedStyle(current);
      const box = current.getBoundingClientRect();
      if (style.display === 'none' || style.visibility === 'hidden' ||
          Number(style.opacity || '1') === 0) return false;
      const clips = ['hidden', 'clip'].includes(style.overflow) ||
        ['hidden', 'clip'].includes(style.overflowX) ||
        ['hidden', 'clip'].includes(style.overflowY);
      if (clips && (box.width <= 0 || box.height <= 0)) return false;
      current = current.parentElement;
    }
    return true;
  };
  const suggestedModals = Array.from(
    document.querySelectorAll('[role="dialog"],[aria-modal="true"]')
  ).filter((node) => {
    if (!visible(node)) return false;
    const text = String(node.innerText || node.textContent || '').toLowerCase();
    return text.includes('suggested') &&
      (text.includes('followers') || text.includes('following') || text.includes('suggested accounts'));
  });
  const exactSuggestedHeadings = Array.from(
    document.querySelectorAll('p,h1,h2,h3,h4')
  ).filter((node) => String(node.textContent || '').trim().toLowerCase() === 'suggested accounts');
  const expandedSuggestedRoots = [];
  for (const heading of exactSuggestedHeadings) {
    let root = heading;
    for (let depth = 0; depth < 6 && root; depth += 1, root = root.parentElement) {
      if (root.querySelectorAll('a[href^="/@"]').length === 0) continue;
      if (visibleThroughAncestors(root)) expandedSuggestedRoots.push(root);
      break;
    }
  }
  const bodyStyle = window.getComputedStyle(document.body);
  const htmlStyle = window.getComputedStyle(document.documentElement);
  const bodyScrollLocked = document.body.classList.contains('hidden') ||
    ['hidden', 'clip'].includes(bodyStyle.overflow) ||
    ['hidden', 'clip'].includes(bodyStyle.overflowY) ||
    ['hidden', 'clip'].includes(htmlStyle.overflow) ||
    ['hidden', 'clip'].includes(htmlStyle.overflowY);
  const blockingModals = Array.from(
    document.querySelectorAll('[role="dialog"],[aria-modal="true"]')
  ).filter(visibleThroughAncestors);
  return {
    suggested_modal_open: suggestedModals.length > 0,
    suggested_modal_count: suggestedModals.length,
    suggested_accounts_expanded: expandedSuggestedRoots.length > 0,
    suggested_accounts_expanded_root_count: expandedSuggestedRoots.length,
    body_scroll_locked: bodyScrollLocked,
    blocking_modal_count: blockingModals.length,
    grid_video_anchor_count: document.querySelectorAll('a[href*="/video/"]').length
  };
}
""".strip()

TIKTOK_SUGGESTED_VIEW_ALL_ACTION = BrowserPagePointerAction(
    action_name="tiktok_suggested_accounts_view_all_v0",
    candidate_selector="[aria-label='View All'],button,[role='button'],a",
    text_markers=("view all",),
    exact_text_markers=("view all",),
    page_text_markers=("suggested accounts",),
    wait_after_range=TIKTOK_STATE_WAIT_2000_DELAY_RANGE,
    prefer_smallest_match=True,
)

TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION = BrowserPagePointerAction(
    action_name="tiktok_relationship_dialog_close_v0",
    candidate_selector=(
        "[role='dialog'] [data-e2e='follow-popup-close'],"
        "[aria-modal='true'] [data-e2e='follow-popup-close'],"
        "[role='dialog'] [aria-label*='close' i],"
        "[aria-modal='true'] [aria-label*='close' i]"
    ),
    text_markers=("close",),
    exact_text_markers=("close", "x", "×"),
    page_text_markers=("followers", "suggested"),
    wait_after_range=TIKTOK_STATE_WAIT_1500_DELAY_RANGE,
    prefer_smallest_match=True,
    visual_top_right_x_fallback=False,
    visual_x_geometric_fallback=False,
)

TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION = BrowserPagePointerAction(
    action_name="tiktok_suggested_accounts_collapse_before_grid_v0",
    candidate_selector=(
        "button[data-e2e='show-suggested-accounts']"
        "[aria-label='Suggested accounts']"
    ),
    text_markers=(),
    exact_text_markers=("suggested accounts",),
    page_text_markers=("suggested accounts",),
    wait_after_range=TIKTOK_STATE_WAIT_1000_DELAY_RANGE,
    prefer_smallest_match=True,
    visual_top_right_x_fallback=False,
    visual_x_geometric_fallback=False,
)

TIKTOK_VIDEO_OVERLAY_CLOSE_ACTION = BrowserPagePointerAction(
    action_name="tiktok_grid_video_overlay_close_v0",
    candidate_selector=(
        "button[aria-label*='close' i],[role='button'][aria-label*='close' i],"
        "[data-e2e*='close'],button,[role='button']"
    ),
    text_markers=(),
    exact_text_markers=("close", "x", "×"),
    page_text_markers=("comments", "creator videos"),
    wait_after_range=TIKTOK_STATE_WAIT_1500_DELAY_RANGE,
    prefer_smallest_match=True,
)


class TikTokCreatorOnboardingError(RuntimeError):
    """Raised when supervised onboarding cannot produce trustworthy completion."""


def fetch_browser_page_observation_capture(
    **kwargs: object,
) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
    capture = _fetch_browser_page_observation_capture(**kwargs)  # type: ignore[arg-type]
    if isinstance(capture, BrowserPageObservationSuccess):
        attempts = capture.metadata.get("pre_action_stop_attempts")
        for attempt in attempts if isinstance(attempts, list) else ():
            if not isinstance(attempt, dict):
                continue
            if (
                attempt.get("stop_kind") == "logged_out_session"
                or attempt.get("matched_marker") in {"log in to comment", "/login"}
            ):
                raise TikTokCreatorOnboardingError("logged_out_session")
    return capture


class TikTokCreatorMarketDeferred(TikTokCreatorOnboardingError):
    """Raised after the same-read profile market gate records a reversible defer."""

    def __init__(self, assessment: dict[str, Any]) -> None:
        self.assessment = assessment
        super().__init__(
            "TikTok creator market gate deferred capture: "
            f"reason_code={assessment['reason_code_or_none']}"
        )


@dataclass(frozen=True)
class TikTokCreatorOnboardingOutputPaths:
    suggested_accounts_json_path: Path
    grid_window_json_path: Path
    selection_json_path: Path
    live_grid_json_path: Path
    live_cadence_json_path: Path
    onboarding_receipt_json_path: Path
    activity_journal_jsonl_path: Path


@dataclass(frozen=True)
class TikTokCreatorProfileRefreshOutputPaths:
    grid_window_json_path: Path
    onboarding_receipt_json_path: Path


DeepCaptureFn = Callable[..., dict[str, Any]]
ProgressFn = Callable[[str, dict[str, object]], None]
ObservationActivityEventFn = Callable[[str, dict[str, object]], None]


def _utc_now() -> datetime:
    # Not harness_utils.utc_now_z: returns an aware datetime (for injectable clocks), not a Z string.
    return datetime.now(UTC)


@dataclass(frozen=True)
class _OnboardingCadencePolicy:
    mode: CadenceMode
    min_gap_seconds: float
    max_gap_seconds: float
    window_seconds: float | None = None
    typical_min_gap_seconds: float | None = None
    typical_max_gap_seconds: float | None = None
    tail_min_gap_seconds: float | None = None
    tail_max_gap_seconds: float | None = None
    tail_probability: float | None = None

    def build_plan(
        self, *, slot_count: int, random_seed: int | None
    ) -> CadencePlan:
        window_seconds = self.window_seconds
        if self.mode == "bounded_jitter" and window_seconds is None:
            window_seconds = self.max_gap_seconds * max(0, slot_count - 1)
        return build_cadence_plan(
            slot_count=slot_count,
            mode=self.mode,
            delay_seconds=0.0,
            window_seconds=window_seconds,
            min_gap_seconds=self.min_gap_seconds,
            max_gap_seconds=self.max_gap_seconds,
            typical_min_gap_seconds=self.typical_min_gap_seconds,
            typical_max_gap_seconds=self.typical_max_gap_seconds,
            tail_min_gap_seconds=self.tail_min_gap_seconds,
            tail_max_gap_seconds=self.tail_max_gap_seconds,
            tail_probability=self.tail_probability,
            random_seed=random_seed,
        )


def run_tiktok_creator_onboarding(
    *,
    creator_handle: str,
    session_profile: SourceCaptureSessionProfile,
    output_dir: Path,
    auth_state_root: Path | None = None,
    browser_user_data_root: Path | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    selection_count: int = DEFAULT_SELECTION_COUNT,
    timeout_seconds: float = 30.0,
    settle_seconds: float = 2.0,
    max_grid_scroll_passes: int = DEFAULT_MAX_GRID_SCROLL_PASSES,
    cadence_min_gap_seconds: float | None = None,
    cadence_max_gap_seconds: float | None = None,
    cadence_window_seconds: float | None = None,
    random_seed: int | None = None,
    engine: BrowserPageObservationEngine | None = None,
    progress_fn: ProgressFn | None = None,
    deep_capture_fn: DeepCaptureFn = run_tiktok_live_batch_probe,
    link_hub_fetch_fn: LinkHubFetchFn = fetch_direct_http_capture,
    sleep_fn: SleepFn = time.sleep,
    monotonic_fn: MonotonicFn = time.monotonic,
    utc_now_fn: UtcNowFn = _utc_now,
    enforce_us_market_gate: bool = False,
) -> TikTokCreatorOnboardingOutputPaths:
    """Run suggested -> grid -> select -> deep-capture in one browser context."""

    normalized_handle = _normalize_handle(creator_handle)
    run_started_monotonic = monotonic_fn()
    state = _OnboardingRunState(
        phase_chronology=[
            _phase_chronology_row(
                "onboarding_started",
                run_started_monotonic=run_started_monotonic,
                monotonic_fn=monotonic_fn,
                utc_now_fn=utc_now_fn,
            )
        ]
    )
    _validate_onboarding_inputs(
        session_profile=session_profile,
        window_size=window_size,
        selection_count=selection_count,
        max_grid_scroll_passes=max_grid_scroll_passes,
    )
    cadence_policy = _resolve_onboarding_cadence_policy(
        min_gap_seconds=cadence_min_gap_seconds,
        max_gap_seconds=cadence_max_gap_seconds,
        window_seconds=cadence_window_seconds,
    )
    cadence_policy.build_plan(
        slot_count=selection_count,
        random_seed=random_seed,
    )

    storage_state_path = validate_auth_state_provenance_requirement(
        session_profile.state_label,
        session_mode=session_profile.session_mode,
        required_harness_proxy_profile_posture=(
            session_profile.required_harness_proxy_profile_posture
        ),
        auth_state_root=auth_state_root,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _output_paths(output_dir)
    profile_url = f"https://www.tiktok.com/@{normalized_handle}"
    owned_engine = engine is None
    journal = SourceCaptureActivityJournal(
        paths.activity_journal_jsonl_path,
        run_kind="creator_onboarding",
        platform="tiktok",
        monotonic_fn=monotonic_fn,
        utc_now_fn=utc_now_fn,
    )
    activity_event_fn: ActivityEventFn = (
        lambda event_type, fields: journal.record(event_type, **fields)
    )
    original_progress_fn = progress_fn

    def journaled_progress(
        event: str, fields: dict[str, object]
    ) -> None:
        journal.record("phase", phase_name=event, details=fields)
        if original_progress_fn is not None:
            original_progress_fn(event, fields)

    progress_fn = journaled_progress
    observation_engine: BrowserPageObservationEngine | None = None

    try:
        observation_engine = _acquire_or_reuse_observation_engine(
            engine=engine,
            session_profile=session_profile,
            browser_user_data_root=browser_user_data_root,
            activity_event_fn=activity_event_fn,
        )
        _run_suggested_grid_and_selection_phase(
            state,
            profile_url=profile_url,
            creator_handle=normalized_handle,
            storage_state_path=storage_state_path,
            paths=paths,
            window_size=window_size,
            selection_count=selection_count,
            max_grid_scroll_passes=max_grid_scroll_passes,
            timeout_seconds=timeout_seconds,
            settle_seconds=settle_seconds,
            engine=observation_engine,
            progress_fn=progress_fn,
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
            enforce_us_market_gate=enforce_us_market_gate,
        )
        _run_grid_overlay_deep_capture_phase(
            state,
            profile_url=profile_url,
            creator_handle=normalized_handle,
            session_profile=session_profile,
            auth_state_root=auth_state_root,
            storage_state_path=storage_state_path,
            paths=paths,
            max_grid_scroll_passes=max_grid_scroll_passes,
            timeout_seconds=timeout_seconds,
            settle_seconds=settle_seconds,
            cadence_policy=cadence_policy,
            random_seed=random_seed,
            engine=observation_engine,
            progress_fn=progress_fn,
            deep_capture_fn=deep_capture_fn,
            sleep_fn=sleep_fn,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
            run_started_monotonic=run_started_monotonic,
            activity_event_fn=activity_event_fn,
        )
        _run_earliest_public_post_phase(
            state,
            profile_url=profile_url,
            creator_handle=normalized_handle,
            storage_state_path=storage_state_path,
            paths=paths,
            timeout_seconds=timeout_seconds,
            settle_seconds=settle_seconds,
            engine=observation_engine,
            progress_fn=progress_fn,
            utc_now_fn=utc_now_fn,
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
        )
        _run_link_hub_phase(
            state,
            storage_state_path=storage_state_path,
            paths=paths,
            timeout_seconds=timeout_seconds,
            settle_seconds=settle_seconds,
            engine=observation_engine,
            progress_fn=progress_fn,
            fetch_fn=link_hub_fetch_fn,
            utc_now_fn=utc_now_fn,
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
        )
        state.stage = "close"
        _notify_progress(progress_fn, state.stage, completed_count=state.completed_count)
    except TikTokCreatorMarketDeferred:
        state.status = "deferred"
        state.error = None
        state.error_type = None
        raise
    except Exception as exc:
        state.status = "failed"
        state.error = f"{type(exc).__name__}: {exc}"
        state.error_type = type(exc).__name__
        raise
    finally:
        if owned_engine and observation_engine is not None:
            close = getattr(observation_engine, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as exc:
                    state.close_error = f"{type(exc).__name__}: {exc}"
                    state.error = (
                        f"{state.error}; close failed: {state.close_error}"
                        if state.error
                        else f"close failed: {state.close_error}"
                    )
                    state.status = "failed"
                    state.stage = "close"
                    state.error_type = type(exc).__name__
        try:
            journal.close(
                status=state.status,
                terminal_phase=state.stage,
                error_type_or_none=state.error_type,
            )
            state.artifacts_written.append(paths.activity_journal_jsonl_path.name)
        except Exception as exc:
            state.journal_error = f"{type(exc).__name__}: {exc}"
            state.error = (
                f"{state.error}; activity journal close failed: {state.journal_error}"
                if state.error
                else f"activity journal close failed: {state.journal_error}"
            )
            state.error_type = type(exc).__name__
            state.status = "failed"
        receipt = _build_onboarding_receipt(
            state,
            observation_engine=observation_engine,
            owned_engine=owned_engine,
            creator_handle=normalized_handle,
            session_profile=session_profile,
            window_size=window_size,
            selection_count=selection_count,
        )
        _write_json(paths.onboarding_receipt_json_path, receipt)

    if state.close_error is not None:
        raise TikTokCreatorOnboardingError(
            f"browser session close failed: {state.close_error}"
        )
    if state.journal_error is not None:
        raise TikTokCreatorOnboardingError(
            f"activity journal close failed: {state.journal_error}"
        )
    return paths


def run_tiktok_creator_profile_refresh(
    *,
    creator_handle: str,
    session_profile: SourceCaptureSessionProfile,
    output_dir: Path,
    auth_state_root: Path | None = None,
    browser_user_data_root: Path | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    timeout_seconds: float = 30.0,
    settle_seconds: float = 2.0,
    max_grid_scroll_passes: int = DEFAULT_MAX_GRID_SCROLL_PASSES,
    engine: BrowserPageObservationEngine | None = None,
    progress_fn: ProgressFn | None = None,
) -> TikTokCreatorProfileRefreshOutputPaths:
    """Capture current profile evidence without opening a video or deep-capturing."""

    normalized_handle = _normalize_handle(creator_handle)
    _validate_onboarding_inputs(
        session_profile=session_profile,
        window_size=window_size,
        selection_count=1,
        max_grid_scroll_passes=max_grid_scroll_passes,
    )
    storage_state_path = validate_auth_state_provenance_requirement(
        session_profile.state_label,
        session_mode=session_profile.session_mode,
        required_harness_proxy_profile_posture=(
            session_profile.required_harness_proxy_profile_posture
        ),
        auth_state_root=auth_state_root,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = TikTokCreatorProfileRefreshOutputPaths(
        grid_window_json_path=output_dir / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        onboarding_receipt_json_path=output_dir / TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
    )
    owned_engine = engine is None
    observation_engine = _acquire_or_reuse_observation_engine(
        engine=engine,
        session_profile=session_profile,
        browser_user_data_root=browser_user_data_root,
    )
    try:
        _notify_progress(progress_fn, "collect_profile_grid")
        capture = capture_tiktok_creator_grid(
            profile_url=f"https://www.tiktok.com/@{normalized_handle}",
            creator_handle=normalized_handle,
            storage_state_path=storage_state_path,
            window_size=window_size,
            minimum_dom_video_count=1,
            timeout_seconds=timeout_seconds,
            settle_seconds=settle_seconds,
            max_grid_scroll_passes=max_grid_scroll_passes,
            engine=observation_engine,
            required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
        )
        if isinstance(capture, BrowserSnapshotFailure):
            raise TikTokCreatorOnboardingError(
                f"profile grid capture failed: {capture.failure_kind.value}"
            )
        grid_window = build_tiktok_grid_window(
            creator_handle=normalized_handle,
            capture=capture,
            window_size=window_size,
            minimum_window_size=1,
            required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
        )
        _write_json(paths.grid_window_json_path, grid_window)
        _notify_progress(progress_fn, "profile_refresh_complete", completed_count=0)
    finally:
        if owned_engine:
            close = getattr(observation_engine, "close", None)
            if callable(close):
                close()

    raw_lifecycle = getattr(observation_engine, "lifecycle_receipt", None)
    lifecycle_receipt = (
        raw_lifecycle
        if isinstance(raw_lifecycle, dict)
        else {
            "engine": type(observation_engine).__name__,
            "owned_by_onboarding_runner": owned_engine,
            "closed_or_none": True if owned_engine else None,
        }
    )
    receipt = {
        "schema_version": TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION,
        "status": "complete",
        "terminal_stage": "profile_refresh_complete",
        "capture_scope": "profile_refresh",
        "creator_handle": normalized_handle,
        "session_profile": session_profile.alias,
        "window_size": grid_window["window_size"],
        "window_cap": window_size,
        "selection_count": 0,
        "selected_count": 0,
        "completed_deep_capture_count": 0,
        "completed_deep_capture_count_source": "profile_refresh_no_deep_capture",
        "candidate_profiles_opened": 0,
        "account_mutations_taken": 0,
        "artifacts_written": [paths.grid_window_json_path.name],
        "browser_lifecycle": lifecycle_receipt,
        "error_or_none": None,
        "non_claims": [
            "not a video, comment, subtitle, or transcript recapture",
            "not Creator Registry mutation",
        ],
    }
    _write_json(paths.onboarding_receipt_json_path, receipt)
    return paths


def run_tiktok_creator_observation_activity(
    *,
    creator_handle: str,
    session_profile: SourceCaptureSessionProfile,
    grid_window: Mapping[str, object],
    auth_state_root: Path | None = None,
    browser_user_data_root: Path | None = None,
    observation_count: int = 2,
    timeout_seconds: float = 30.0,
    settle_seconds: float = 2.0,
    max_grid_scroll_passes: int = 1,
    engine: BrowserPageObservationEngine | None = None,
    rng: Any | None = None,
    sleep_fn: SleepFn = time.sleep,
    monotonic_fn: MonotonicFn = time.monotonic,
    utc_now_fn: UtcNowFn = _utc_now,
    event_fn: ObservationActivityEventFn | None = None,
) -> dict[str, object]:
    """View exact grid videos without collecting or admitting content evidence."""

    normalized_handle = _normalize_handle(creator_handle)
    _validate_onboarding_inputs(
        session_profile=session_profile,
        window_size=DEFAULT_WINDOW_SIZE,
        selection_count=observation_count,
        max_grid_scroll_passes=max_grid_scroll_passes,
    )
    observed_handle = str(grid_window.get("creator_handle") or "")
    if _normalize_handle(observed_handle) != normalized_handle:
        raise TikTokCreatorOnboardingError(
            "observation grid creator identity does not match requested handle"
        )
    selected_rows = _select_observation_activity_rows(
        grid_window=grid_window,
        creator_handle=normalized_handle,
        observation_count=observation_count,
        rng=rng or random.SystemRandom(),
    )
    run_rng = rng or random.SystemRandom()
    storage_state_path = validate_auth_state_provenance_requirement(
        session_profile.state_label,
        session_mode=session_profile.session_mode,
        required_harness_proxy_profile_posture=(
            session_profile.required_harness_proxy_profile_posture
        ),
        auth_state_root=auth_state_root,
    )
    profile_url = f"https://www.tiktok.com/@{normalized_handle}"
    selected_video_ids = [str(row["video_id"]) for row in selected_rows]
    selected_urls = [str(row["video_url"]) for row in selected_rows]
    window_by_id = {str(row["video_id"]): dict(row) for row in selected_rows}
    receipt: dict[str, object] = {
        "schema_version": "tiktok_creator_observation_activity_v0",
        "status": "in_progress",
        "creator_handle": normalized_handle,
        "observation_count": observation_count,
        "selected_video_ids": selected_video_ids,
        "selected_video_ids_in_capture_order": [],
        "capture_order_policy": (
            "random_without_replacement_from_top_visible_unpinned_grid"
        ),
        "dwell_policy": {
            "mode": "weighted_long_tail",
            "typical_min_seconds": (
                TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MIN_GAP_SECONDS
            ),
            "typical_max_seconds": (
                TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MAX_GAP_SECONDS
            ),
            "tail_min_seconds": (
                TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MIN_GAP_SECONDS
            ),
            "tail_max_seconds": (
                TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MAX_GAP_SECONDS
            ),
            "tail_probability": (
                TIKTOK_ONBOARDING_LONG_TAIL_TAIL_PROBABILITY
            ),
            "median_seconds": 12.894737,
        },
        "dwells": [],
        "direct_video_navigation_count": 0,
        "content_response_collection_enabled": False,
        "targeted_tile_scroll_performed": False,
        "grid_pagination_allowed": max_grid_scroll_passes > 0,
        "grid_pagination_input_method": "cloakbrowser.human.scroll_to_element",
        "logical_grid_positions_remembered": True,
        "absolute_pixel_positions_cached": False,
        "grid_pagination_pass_cap_per_lookup": max_grid_scroll_passes,
        "grid_pagination_total_pass_cap": max_grid_scroll_passes,
        "grid_pagination_passes_executed": 0,
        "grid_pagination_passes": [],
        "grid_pagination_stop_reason": None,
        "frozen_window_identity_drift_detected": False,
        "frozen_window_live_overlap_count_at_stop_or_none": None,
        "loaded_grid_video_count_at_stop_or_none": None,
        "attempts": [],
        "retry_waits": [],
    }
    _notify_observation_activity(
        event_fn,
        "observation_selected",
        {
            "creator_handle": normalized_handle,
            "selected_video_ids": selected_video_ids,
        },
    )
    owned_engine = engine is None
    observation_engine = _acquire_or_reuse_observation_engine(
        engine=engine,
        session_profile=session_profile,
        browser_user_data_root=browser_user_data_root,
    )
    sequence = _GridOverlayCaptureSequence(
        profile_url=profile_url,
        creator_handle=normalized_handle,
        selected_video_ids=selected_video_ids,
        window_by_id=window_by_id,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        pagination_pass_cap=max_grid_scroll_passes,
        engine=observation_engine,
        rng=run_rng,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
        utc_now_fn=utc_now_fn,
        receipt=receipt,
        collect_content_responses=False,
        pagination_total_pass_cap=max_grid_scroll_passes,
    )
    pending_urls = list(selected_urls)
    try:
        for index in range(observation_count):
            _notify_observation_activity(
                event_fn,
                "overlay_open_started",
                {"creator_handle": normalized_handle, "observation_index": index},
            )
            chosen_url, _capture = sequence(index, pending_urls)
            chosen_video_id = _video_id_from_url(chosen_url)
            _notify_observation_activity(
                event_fn,
                "overlay_open_finished",
                {
                    "creator_handle": normalized_handle,
                    "observation_index": index,
                    "video_id": chosen_video_id,
                },
            )
            dwell_seconds, dwell_band = (
                _sample_tiktok_onboarding_long_tail_delay_seconds(
                    rng=run_rng
                )
            )
            dwell_started = monotonic_fn()
            _notify_observation_activity(
                event_fn,
                "dwell_started",
                {
                    "creator_handle": normalized_handle,
                    "observation_index": index,
                    "video_id": chosen_video_id,
                    "planned_seconds": dwell_seconds,
                    "dwell_band": dwell_band,
                },
            )
            sleep_fn(dwell_seconds)
            actual_seconds = round(
                max(0.0, monotonic_fn() - dwell_started), 6
            )
            dwell_row = {
                "video_id": chosen_video_id,
                "planned_seconds": dwell_seconds,
                "actual_seconds": actual_seconds,
                "dwell_band": dwell_band,
            }
            dwells = receipt["dwells"]
            assert isinstance(dwells, list)
            dwells.append(dwell_row)
            _notify_observation_activity(
                event_fn,
                "dwell_finished",
                {
                    "creator_handle": normalized_handle,
                    "observation_index": index,
                    **dwell_row,
                },
            )
            _notify_observation_activity(
                event_fn,
                "overlay_close_started",
                {
                    "creator_handle": normalized_handle,
                    "observation_index": index,
                    "video_id": chosen_video_id,
                },
            )
            sequence.close_current_overlay()
            _notify_observation_activity(
                event_fn,
                "overlay_close_finished",
                {
                    "creator_handle": normalized_handle,
                    "observation_index": index,
                    "video_id": chosen_video_id,
                },
            )
            pending_urls = [
                url
                for url in pending_urls
                if _video_id_from_url(url) != chosen_video_id
            ]
        receipt["status"] = "complete"
        return receipt
    except Exception:
        receipt["status"] = "failed"
        raise
    finally:
        if owned_engine:
            close = getattr(observation_engine, "close", None)
            if callable(close):
                close()


def _select_observation_activity_rows(
    *,
    grid_window: Mapping[str, object],
    creator_handle: str,
    observation_count: int,
    rng: Any,
) -> list[dict[str, object]]:
    items = grid_window.get("items")
    if not isinstance(items, list):
        raise TikTokCreatorOnboardingError(
            "observation grid window has no items"
        )
    eligible: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict) or item.get("pinned_visible") is True:
            continue
        video_id = str(item.get("video_id") or "")
        video_url = str(item.get("video_url") or "")
        author_handle = str(item.get("authorUniqueId") or "").strip()
        if (
            not video_id
            or not author_handle
            or not _is_creator_video_url(
                video_url=video_url,
                creator_handle=creator_handle,
                video_id=video_id,
            )
            or _normalize_handle(author_handle)
            != creator_handle
        ):
            continue
        eligible.append(dict(item))
    eligible.sort(
        key=lambda row: (
            int(row.get("grid_position") or 10**9),
            str(row["video_id"]),
        )
    )
    visible = [
        row for row in eligible if row.get("visible_in_viewport") is True
    ]
    if len(eligible) < observation_count:
        raise TikTokCreatorOnboardingError(
            "observation grid has fewer than the required unpinned exact-creator videos"
        )
    if not visible:
        raise TikTokCreatorOnboardingError(
            "observation grid has no exact-creator video visible in the captured viewport"
        )
    if len(visible) >= observation_count:
        return list(rng.sample(visible, observation_count))
    chosen = list(visible)
    remaining = [
        row for row in eligible if row["video_id"] not in {
            selected["video_id"] for selected in chosen
        }
    ]
    chosen.extend(rng.sample(remaining, observation_count - len(chosen)))
    return chosen


def _notify_observation_activity(
    event_fn: ObservationActivityEventFn | None,
    event: str,
    fields: dict[str, object],
) -> None:
    if event_fn is not None:
        event_fn(event, fields)


def _sample_tiktok_onboarding_long_tail_delay_seconds(
    *,
    rng: Any,
) -> tuple[float, str]:
    use_tail = (
        rng.random()
        < TIKTOK_ONBOARDING_LONG_TAIL_TAIL_PROBABILITY
    )
    if use_tail:
        lower = TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MIN_GAP_SECONDS
        upper = TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MAX_GAP_SECONDS
        band = "tail"
    else:
        lower = TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MIN_GAP_SECONDS
        upper = TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MAX_GAP_SECONDS
        band = "typical"
    return round(rng.uniform(lower, upper), 3), band


@dataclass
class _OnboardingRunState:
    """Mutable per-run state shared by onboarding phases and the finally-path receipt.

    Field defaults are the values the receipt reports when a phase fails before
    assigning them; `None` optional fields stand in for the original inline
    body's single-assignment locals (still `None` == never reached).
    """

    stage: str = "acquire_session"
    status: str = "failed"
    error: str | None = None
    error_type: str | None = None
    close_error: str | None = None
    journal_error: str | None = None
    selected_video_ids: list[str] = field(default_factory=list)
    challenge_count: int = 0
    human_challenge_handoff_count: int = 0
    completed_count: int = 0
    account_safety_stop: bool = False
    suggested_status: str | None = None
    suggested_outer_ui_route: str | None = None
    suggested_receipt: dict[str, Any] | None = None
    suggested_surface_close: dict[str, object] | None = None
    initial_deep_capture_wait: dict[str, object] | None = None
    grid_deep_entry: dict[str, object] | None = None
    artifacts_written: list[str] = field(default_factory=list)
    phase_chronology: list[dict[str, Any]] = field(default_factory=list)
    grid_capture: BrowserPageObservationSuccess | None = None
    grid_window: dict[str, Any] | None = None
    selection: dict[str, Any] | None = None
    earliest_public_post_observation: dict[str, Any] | None = None
    link_hub_observation: dict[str, Any] | None = None
    window_by_id: dict[str, Any] | None = None
    captured_video_ids: list[str] | None = None
    deep_capture: dict[str, Any] | None = None
    market_assessment: dict[str, Any] | None = None


def _resolve_onboarding_cadence_policy(
    *,
    min_gap_seconds: float | None,
    max_gap_seconds: float | None,
    window_seconds: float | None,
) -> _OnboardingCadencePolicy:
    if (min_gap_seconds is None) != (max_gap_seconds is None):
        raise TikTokCreatorOnboardingError(
            "cadence min and max gap overrides must be supplied together"
        )
    if min_gap_seconds is None:
        if window_seconds is not None:
            raise TikTokCreatorOnboardingError(
                "cadence window requires explicit cadence min and max gap overrides"
            )
        return _OnboardingCadencePolicy(
            mode="weighted_long_tail",
            min_gap_seconds=TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MIN_GAP_SECONDS,
            max_gap_seconds=TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MAX_GAP_SECONDS,
            typical_min_gap_seconds=(
                TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MIN_GAP_SECONDS
            ),
            typical_max_gap_seconds=(
                TIKTOK_ONBOARDING_LONG_TAIL_TYPICAL_MAX_GAP_SECONDS
            ),
            tail_min_gap_seconds=TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MIN_GAP_SECONDS,
            tail_max_gap_seconds=TIKTOK_ONBOARDING_LONG_TAIL_TAIL_MAX_GAP_SECONDS,
            tail_probability=TIKTOK_ONBOARDING_LONG_TAIL_TAIL_PROBABILITY,
        )
    assert max_gap_seconds is not None
    return _OnboardingCadencePolicy(
        mode="bounded_jitter",
        min_gap_seconds=min_gap_seconds,
        max_gap_seconds=max_gap_seconds,
        window_seconds=window_seconds,
    )


def _derived_seed(random_seed: int | None, purpose: str) -> int | None:
    if random_seed is None:
        return None
    material = f"{random_seed}:{purpose}".encode("utf-8")
    return int(sha256(material).hexdigest()[:16], 16)


def _validate_onboarding_inputs(
    *,
    session_profile: SourceCaptureSessionProfile,
    window_size: int,
    selection_count: int,
    max_grid_scroll_passes: int,
) -> None:
    if session_profile.platform != "tiktok":
        raise TikTokCreatorOnboardingError("session profile platform must be tiktok")
    if session_profile.browser_backend != TIKTOK_BROWSER_BACKEND_CHROME_CDP:
        raise TikTokCreatorOnboardingError("TikTok onboarding requires Chrome CDP")
    if (
        isinstance(window_size, bool)
        or not isinstance(window_size, int)
        or window_size < GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT
    ):
        raise TikTokCreatorOnboardingError(
            "window_size must be an integer of at least "
            f"{GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT}"
        )
    if (
        isinstance(selection_count, bool)
        or not isinstance(selection_count, int)
        or selection_count <= 0
        or selection_count > window_size
    ):
        raise TikTokCreatorOnboardingError("selection_count must be between 1 and window_size")
    if (
        isinstance(max_grid_scroll_passes, bool)
        or not isinstance(max_grid_scroll_passes, int)
        or max_grid_scroll_passes <= 0
    ):
        raise TikTokCreatorOnboardingError(
            "max_grid_scroll_passes must be a positive integer"
        )


def _acquire_or_reuse_observation_engine(
    *,
    engine: BrowserPageObservationEngine | None,
    session_profile: SourceCaptureSessionProfile,
    browser_user_data_root: Path | None,
    activity_event_fn: ActivityEventFn | None = None,
) -> BrowserPageObservationEngine:
    if engine is not None:
        return engine
    if session_profile.browser_user_data_label is None:
        raise TikTokCreatorOnboardingError(
            "TikTok onboarding requires a retained browser_user_data_label"
        )
    user_data_dir = browser_user_data_path_for_label(
        session_profile.browser_user_data_label,
        user_data_root=browser_user_data_root,
    )
    if not user_data_dir.is_dir() or not any(user_data_dir.iterdir()):
        raise TikTokCreatorOnboardingError(
            "retained browser profile is missing or empty; bootstrap it manually before onboarding"
        )
    return ChromeCdpPageObservationSessionEngine(
        pre_action_stop_markers=TIKTOK_ACCOUNT_SAFETY_STOP_MARKERS,
        pre_action_stop_structural_rules=(TIKTOK_LOGGED_OUT_STRUCTURAL_STOP_RULE,),
        require_humanized_state_changes=True,
        protected_settle_delay_range=TIKTOK_PAGE_SETTLE_DELAY_RANGE,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        activity_event_fn=activity_event_fn,
    )


def _run_suggested_grid_and_selection_phase(
    state: _OnboardingRunState,
    *,
    profile_url: str,
    creator_handle: str,
    storage_state_path: Path,
    paths: TikTokCreatorOnboardingOutputPaths,
    window_size: int,
    selection_count: int,
    max_grid_scroll_passes: int,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    progress_fn: ProgressFn | None,
    run_started_monotonic: float,
    monotonic_fn: MonotonicFn,
    utc_now_fn: UtcNowFn,
    enforce_us_market_gate: bool,
) -> None:
    state.stage = "collect_suggested_accounts"
    _notify_progress(progress_fn, state.stage)
    suggested_capture = _capture_suggested_accounts(
        profile_url=profile_url,
        creator_handle=creator_handle,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        engine=engine,
    )
    suggested_receipt = _build_suggested_accounts_receipt(
        creator_handle=creator_handle,
        capture=suggested_capture,
    )
    state.suggested_status = str(suggested_receipt["status"])
    state.suggested_outer_ui_route = str(suggested_receipt["outer_ui_route"])
    state.suggested_receipt = suggested_receipt
    _write_json(paths.suggested_accounts_json_path, suggested_receipt)
    state.artifacts_written.append(paths.suggested_accounts_json_path.name)
    if state.suggested_status == "failed":
        raise TikTokCreatorOnboardingError("suggested-account observation failed")

    if enforce_us_market_gate:
        state.market_assessment = assess_tiktok_creator_market(
            creator_handle=creator_handle,
            profile_bio_text_or_none=suggested_receipt.get(
                "profile_bio_text_or_none"
            ),
            profile_bio_status=str(
                suggested_receipt.get("profile_bio_status") or ""
            ),
        )

    state.stage = "close_suggested_surface"
    _notify_progress(progress_fn, state.stage)
    state.suggested_surface_close = _close_suggested_surface_before_grid(
        profile_url=profile_url,
        creator_handle=creator_handle,
        suggested_status=state.suggested_status,
        suggested_outer_ui_route=state.suggested_outer_ui_route,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        engine=engine,
    )

    if state.market_assessment is not None:
        state.stage = "market_gate"
        _notify_progress(
            progress_fn,
            state.stage,
            decision=state.market_assessment["decision"],
            reason_code_or_none=state.market_assessment["reason_code_or_none"],
        )
        if state.market_assessment["decision"] != "passed_no_non_us_evidence":
            raise TikTokCreatorMarketDeferred(state.market_assessment)

    state.stage = "collect_grid"
    _notify_progress(progress_fn, state.stage)
    grid_capture = capture_tiktok_creator_grid(
        profile_url=profile_url,
        creator_handle=creator_handle,
        storage_state_path=storage_state_path,
        window_size=window_size,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        max_grid_scroll_passes=max_grid_scroll_passes,
        engine=engine,
        required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
    )
    if isinstance(grid_capture, BrowserSnapshotFailure):
        raise TikTokCreatorOnboardingError(
            f"grid capture failed: {grid_capture.failure_kind.value}"
        )
    state.grid_capture = grid_capture
    _merge_grid_profile_external_links(
        suggested_receipt=suggested_receipt,
        grid_capture=grid_capture,
    )
    _write_json(paths.suggested_accounts_json_path, suggested_receipt)

    state.stage = "freeze_window"
    _notify_progress(progress_fn, state.stage)
    grid_window = build_tiktok_grid_window(
        creator_handle=creator_handle,
        capture=grid_capture,
        window_size=window_size,
        minimum_window_size=selection_count,
        required_metric_names=TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS,
    )
    state.grid_window = grid_window
    _write_json(paths.grid_window_json_path, grid_window)
    state.artifacts_written.append(paths.grid_window_json_path.name)

    state.stage = "select"
    _notify_progress(progress_fn, state.stage)
    selection = build_tiktok_grid_video_selection(
        grid_window["items"],
        expected_item_count=len(grid_window["items"]),
        selection_count=selection_count,
    )
    state.selection = selection
    selection["onboarding_binding"] = {
        "creator_handle": creator_handle,
        "grid_window_file": paths.grid_window_json_path.name,
        "grid_window_sha256": hash_file(paths.grid_window_json_path),
    }
    _write_json(paths.selection_json_path, selection)
    state.artifacts_written.append(paths.selection_json_path.name)

    state.window_by_id = {
        str(item["video_id"]): item for item in grid_window["items"]
    }
    state.selected_video_ids = list(
        selection["selection_summary"][
            "selected_video_ids_in_review_priority_order"
        ]
    )
    state.phase_chronology.append(
        _phase_chronology_row(
            "grid_and_selection_complete",
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
        )
    )


def _run_earliest_public_post_phase(
    state: _OnboardingRunState,
    *,
    profile_url: str,
    creator_handle: str,
    storage_state_path: Path,
    paths: TikTokCreatorOnboardingOutputPaths,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    progress_fn: ProgressFn | None,
    utc_now_fn: UtcNowFn,
    run_started_monotonic: float,
    monotonic_fn: MonotonicFn,
) -> None:
    assert state.grid_window is not None
    assert state.selection is not None
    state.stage = "observe_earliest_public_post"
    _notify_progress(progress_fn, state.stage)
    observation = capture_tiktok_earliest_public_post_observation(
        profile_url=profile_url,
        creator_handle=creator_handle,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        engine=engine,
        utc_now_fn=utc_now_fn,
    )
    state.earliest_public_post_observation = observation
    state.grid_window["earliest_public_post_observation"] = observation
    _write_json(paths.grid_window_json_path, state.grid_window)
    state.selection["onboarding_binding"]["grid_window_sha256"] = hash_file(
        paths.grid_window_json_path
    )
    _write_json(paths.selection_json_path, state.selection)
    state.phase_chronology.append(
        _phase_chronology_row(
            "earliest_public_post_observation_completed",
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
        )
    )


def _run_link_hub_phase(
    state: _OnboardingRunState,
    *,
    storage_state_path: Path,
    paths: TikTokCreatorOnboardingOutputPaths,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    progress_fn: ProgressFn | None,
    fetch_fn: LinkHubFetchFn,
    utc_now_fn: UtcNowFn,
    run_started_monotonic: float,
    monotonic_fn: MonotonicFn,
) -> None:
    assert state.suggested_receipt is not None
    state.stage = "capture_profile_link_hub"
    _notify_progress(progress_fn, state.stage)
    link_hub_url = _first_link_hub_url(
        state.suggested_receipt.get("profile_external_links")
    )
    observation = capture_tiktok_profile_link_hub_observation(
        link_hub_url=link_hub_url,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        engine=engine,
        fetch_fn=fetch_fn,
        utc_now_fn=utc_now_fn,
    )
    state.link_hub_observation = observation
    state.suggested_receipt["link_hub_observation"] = observation
    state.suggested_receipt["link_hub_capture_status"] = observation["status"]
    state.suggested_receipt["link_hub_url_or_none"] = observation[
        "link_hub_url_or_none"
    ]
    _write_json(paths.suggested_accounts_json_path, state.suggested_receipt)
    state.phase_chronology.append(
        _phase_chronology_row(
            "profile_link_hub_capture_completed",
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
        )
    )


def capture_tiktok_profile_link_hub_observation(
    *,
    link_hub_url: str | None,
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    fetch_fn: LinkHubFetchFn = fetch_direct_http_capture,
    utc_now_fn: UtcNowFn = _utc_now,
) -> dict[str, Any]:
    observed_at = _utc_iso(utc_now_fn())
    if link_hub_url is None:
        return {
            "schema_version": "tiktok_profile_link_hub_observation_v1",
            "status": "none_visible",
            "link_hub_url_or_none": None,
            "capture_method_or_none": None,
            "direct_http_attempt_or_none": None,
            "browser_fallback_attempt_or_none": None,
            "outbound_social_links": [],
            "observed_at_utc": observed_at,
            "limitations": [],
            "non_claims": [
                "not proof that no external profile link exists outside the captured surface"
            ],
        }

    direct_attempt: dict[str, Any]
    direct_links: list[dict[str, str]] = []
    direct_result: DirectHttpCaptureResult | None = None
    try:
        direct_result = fetch_fn(
            url=link_hub_url,
            timeout_seconds=min(timeout_seconds, 20.0),
            max_bytes=TIKTOK_LINK_HUB_CAPTURE_MAX_BYTES,
        )
    except Exception as exc:
        direct_attempt = {
            "status": "failed",
            "failure_kind_or_none": type(exc).__name__,
            "http_status_or_none": None,
            "final_url_or_none": None,
            "body_sha256_or_none": None,
            "byte_count_or_none": None,
        }
    else:
        if isinstance(direct_result, DirectHttpCaptureSuccess):
            safe_final_url = _canonical_public_url(direct_result.final_url)
            direct_attempt = {
                "status": (
                    "captured"
                    if 200 <= direct_result.status < 300
                    else "http_error"
                ),
                "failure_kind_or_none": None,
                "http_status_or_none": direct_result.status,
                "final_url_or_none": safe_final_url,
                "body_sha256_or_none": f"sha256:{sha256(direct_result.body).hexdigest()}",
                "byte_count_or_none": len(direct_result.body),
            }
            if 200 <= direct_result.status < 300:
                direct_links = _social_links_from_html(
                    direct_result.body,
                    base_url=direct_result.final_url,
                )
        else:
            assert isinstance(direct_result, DirectHttpCaptureFailure)
            direct_attempt = {
                "status": "failed",
                "failure_kind_or_none": direct_result.failure_kind.value,
                "http_status_or_none": direct_result.status,
                "final_url_or_none": _canonical_public_url(
                    direct_result.final_url
                ),
                "body_sha256_or_none": None,
                "byte_count_or_none": None,
            }

    if direct_links:
        return _captured_link_hub_observation(
            link_hub_url=link_hub_url,
            capture_method="direct_http",
            direct_attempt=direct_attempt,
            browser_attempt=None,
            outbound_social_links=direct_links,
            observed_at=observed_at,
        )

    browser_capture = fetch_browser_page_observation_capture(
        url=link_hub_url,
        dom_extract_script=TIKTOK_LINK_HUB_DOM_EXTRACT_SCRIPT,
        dom_extract_arg=None,
        response_url_predicate=lambda _url: False,
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        engine=_TemporaryPageObservationEngine(engine),
    )
    if isinstance(browser_capture, BrowserSnapshotFailure):
        return {
            "schema_version": "tiktok_profile_link_hub_observation_v1",
            "status": "blocked",
            "link_hub_url_or_none": link_hub_url,
            "capture_method_or_none": None,
            "direct_http_attempt_or_none": direct_attempt,
            "browser_fallback_attempt_or_none": {
                "status": "failed",
                "failure_kind_or_none": browser_capture.failure_kind.value,
                "final_url_or_none": None,
            },
            "outbound_social_links": [],
            "observed_at_utc": observed_at,
            "limitations": [
                "direct HTTP exposed no supported social links and browser fallback failed"
            ],
            "non_claims": [
                "not evidence that the link hub has no public outbound accounts"
            ],
        }

    browser_links = _social_links_from_browser_capture(browser_capture)
    return _captured_link_hub_observation(
        link_hub_url=link_hub_url,
        capture_method="browser_temporary_tab",
        direct_attempt=direct_attempt,
        browser_attempt={
            "status": "captured",
            "failure_kind_or_none": None,
            "final_url_or_none": _canonical_public_url(browser_capture.final_url),
        },
        outbound_social_links=browser_links,
        observed_at=observed_at,
    )


def _captured_link_hub_observation(
    *,
    link_hub_url: str,
    capture_method: str,
    direct_attempt: dict[str, Any],
    browser_attempt: dict[str, Any] | None,
    outbound_social_links: list[dict[str, str]],
    observed_at: str,
) -> dict[str, Any]:
    limitations = []
    if not outbound_social_links:
        limitations.append("captured link hub exposed no supported public social URLs")
    return {
        "schema_version": "tiktok_profile_link_hub_observation_v1",
        "status": "captured",
        "link_hub_url_or_none": link_hub_url,
        "capture_method_or_none": capture_method,
        "direct_http_attempt_or_none": direct_attempt,
        "browser_fallback_attempt_or_none": browser_attempt,
        "outbound_social_links": outbound_social_links,
        "observed_at_utc": observed_at,
        "limitations": limitations,
        "non_claims": [
            "not private identity or contact enrichment",
            "not proof that every link-hub destination was enumerated",
            "not Creator Registry linkage mutation",
        ],
    }


def _social_links_from_html(
    body: bytes, *, base_url: str
) -> list[dict[str, str]]:
    parser = _LinkHubHtmlParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    return _canonical_social_link_rows(
        anchor_urls=parser.anchor_hrefs,
        json_ld_texts=parser.json_ld_texts,
        base_url=base_url,
    )


def _social_links_from_browser_capture(
    capture: BrowserPageObservationSuccess,
) -> list[dict[str, str]]:
    dom = capture.dom_observation
    if not isinstance(dom, dict):
        return []
    anchor_urls = [
        str(row["href"])
        for row in dom.get("anchors", [])
        if isinstance(row, dict) and isinstance(row.get("href"), str)
    ]
    json_ld_texts = [
        str(value)
        for value in dom.get("json_ld_texts", [])
        if isinstance(value, str)
    ]
    return _canonical_social_link_rows(
        anchor_urls=anchor_urls,
        json_ld_texts=json_ld_texts,
        base_url=capture.final_url,
    )


def _canonical_social_link_rows(
    *,
    anchor_urls: Sequence[str],
    json_ld_texts: Sequence[str],
    base_url: str,
) -> list[dict[str, str]]:
    candidates = [(url, "anchor") for url in anchor_urls]
    for raw_json in json_ld_texts:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        candidates.extend((url, "json_ld_same_as") for url in _same_as_urls(payload))
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_url, source in candidates:
        normalized = _canonical_social_url(raw_url, base_url=base_url)
        if normalized is None:
            continue
        platform, url = normalized
        if url in seen:
            continue
        seen.add(url)
        rows.append({"platform": platform, "url": url, "source": source})
        if len(rows) >= TIKTOK_LINK_HUB_SOCIAL_LINK_CAP:
            break
    return rows


def _same_as_urls(value: object) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "sameAs":
                if isinstance(child, str):
                    urls.append(child)
                elif isinstance(child, list):
                    urls.extend(item for item in child if isinstance(item, str))
            else:
                urls.extend(_same_as_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.extend(_same_as_urls(child))
    return urls


def _canonical_social_url(
    raw_url: str, *, base_url: str
) -> tuple[str, str] | None:
    candidate_url = raw_url.strip()
    if candidate_url and "://" not in candidate_url and not candidate_url.startswith("/"):
        candidate_url = f"https://{candidate_url}"
    try:
        parsed = urlparse(urljoin(base_url, candidate_url))
    except ValueError:
        return None
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if _host_matches(host, _LINK_HUB_HOSTS):
        query = parse_qs(parsed.query)
        target = next(
            (
                values[0]
                for key in ("url", "target", "destination", "redirect")
                if (values := query.get(key))
            ),
            None,
        )
        if target:
            return _canonical_social_url(target, base_url=base_url)
        return None
    platform = next(
        (
            kind
            for social_host, kind in _SOCIAL_HOST_KINDS.items()
            if host == social_host or host.endswith(f".{social_host}")
        ),
        None,
    )
    if (
        platform is None
        or parsed.scheme not in {"http", "https"}
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    path = parsed.path or "/"
    return platform, f"https://{host}{path}"


def _canonical_public_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    try:
        parsed = urlparse(raw_url)
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    host = parsed.hostname.lower().removeprefix("www.")
    return urlunparse((parsed.scheme, host, parsed.path or "/", "", "", ""))


def _first_link_hub_url(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for row in value:
        if not isinstance(row, dict):
            continue
        normalized = _canonical_link_hub_url(row.get("url"))
        if normalized is not None:
            return normalized
    return None


def _canonical_link_hub_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate_url = value.strip()
    if candidate_url and "://" not in candidate_url and not candidate_url.startswith("/"):
        candidate_url = f"https://{candidate_url}"
    try:
        parsed = urlparse(candidate_url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if host == "tiktok.com" or host.endswith(".tiktok.com"):
        query = parse_qs(parsed.query)
        target = next(
            (
                values[0]
                for key in ("target", "url", "redirect_url")
                if (values := query.get(key))
            ),
            None,
        )
        return _canonical_link_hub_url(target)
    if (
        parsed.scheme not in {"http", "https"}
        or not _host_matches(host, _LINK_HUB_HOSTS)
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return f"https://{host}{parsed.path or '/'}"


def _host_matches(host: str, allowed_hosts: frozenset[str]) -> bool:
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def _merge_grid_profile_external_links(
    *,
    suggested_receipt: dict[str, Any],
    grid_capture: BrowserPageObservationSuccess,
) -> None:
    existing = suggested_receipt.get("profile_external_links")
    rows = list(existing) if isinstance(existing, list) else []
    seen = {
        str(row.get("url"))
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("url"), str)
    }
    dom = grid_capture.dom_observation
    grid_rows = dom.get("profile_external_links") if isinstance(dom, dict) else None
    if isinstance(grid_rows, list):
        for row in grid_rows:
            if not isinstance(row, dict) or not isinstance(row.get("url"), str):
                continue
            if row["url"] in seen:
                continue
            rows.append(row)
            seen.add(row["url"])
    suggested_receipt["profile_external_links"] = rows
    suggested_receipt["profile_external_links_status"] = (
        "captured" if rows else "none_visible"
    )


def capture_tiktok_earliest_public_post_observation(
    *,
    profile_url: str,
    creator_handle: str,
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    utc_now_fn: UtcNowFn = _utc_now,
) -> dict[str, Any]:
    """Capture one bounded Oldest batch and retain only its earliest exact date."""

    def observe(
        actions: Sequence[BrowserPagePointerAction] = (),
    ) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
        return fetch_browser_page_observation_capture(
            url=profile_url,
            dom_extract_script=TIKTOK_OLDEST_POST_DOM_EXTRACT_SCRIPT,
            dom_extract_arg={"creator_handle": creator_handle},
            response_url_predicate=is_tiktok_profile_item_list_url,
            post_load_pointer_actions=actions,
            timeout_seconds=timeout_seconds,
            wait_until="domcontentloaded",
            settle_seconds=settle_seconds,
            storage_state_path=storage_state_path,
            headless=False,
            browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
            human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
            human_challenge_handoff_timeout_seconds=180.0,
            human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
            engine=engine,
        )

    initial = observe()
    if isinstance(initial, BrowserSnapshotFailure):
        raise TikTokCreatorOnboardingError(
            f"Oldest-sort availability observation failed: {initial.failure_kind.value}"
        )
    initial_dom = initial.dom_observation
    if not isinstance(initial_dom, dict):
        raise TikTokCreatorOnboardingError("Oldest-sort DOM observation is not an object")
    if initial_dom.get("oldest_control_present") is not True:
        return _earliest_public_post_unavailable("oldest_sort_not_exposed", utc_now_fn)

    actions = (
        (TIKTOK_PROFILE_LATEST_SORT_ACTION, TIKTOK_PROFILE_OLDEST_SORT_ACTION)
        if initial_dom.get("oldest_active") is True
        else (TIKTOK_PROFILE_OLDEST_SORT_ACTION,)
    )
    capture = observe(actions)
    if isinstance(capture, BrowserSnapshotFailure):
        raise TikTokCreatorOnboardingError(
            f"Oldest-sort capture failed: {capture.failure_kind.value}"
        )
    dom = capture.dom_observation
    oldest_receipt = _verified_oldest_sort_action_receipt(capture)
    selection_attempt_count = 1
    if not isinstance(dom, dict) or dom.get("oldest_active") is not True:
        capture = observe((TIKTOK_PROFILE_OLDEST_SORT_ACTION,))
        selection_attempt_count = 2
        if isinstance(capture, BrowserSnapshotFailure):
            raise TikTokCreatorOnboardingError(
                f"Oldest-sort verification retry failed: {capture.failure_kind.value}"
            )
        dom = capture.dom_observation
        oldest_receipt = _verified_oldest_sort_action_receipt(capture)
    if not isinstance(dom, dict) or dom.get("oldest_active") is not True:
        raise TikTokCreatorOnboardingError(
            "Oldest sort selection could not be verified after one bounded retry"
        )
    response_start = oldest_receipt.get("observed_response_count_before")
    if not isinstance(response_start, int) or isinstance(response_start, bool):
        response_start = 0
    oldest_responses = capture.responses[response_start:]
    candidates = [
        item
        for item in _metric_items_from_responses(oldest_responses, creator_handle)
        if item.get("authorUniqueId") == _normalize_handle(creator_handle)
        and type(item.get("createTime")) is int
    ]
    if not candidates:
        if dom.get("no_public_posts_visible") is True and not dom.get("ordered_videos"):
            result = _earliest_public_post_unavailable("no_public_posts", utc_now_fn)
            return result
        raise TikTokCreatorOnboardingError(
            "Oldest sort produced no exact creator-owned createTime evidence"
        )
    earliest = min(candidates, key=lambda item: int(item["createTime"]))
    video_id = str(earliest["video_id"])
    video_url = f"https://www.tiktok.com/@{_normalize_handle(creator_handle)}/video/{video_id}"
    if not _is_creator_video_url(
        video_url=video_url,
        creator_handle=creator_handle,
        video_id=video_id,
    ):
        raise TikTokCreatorOnboardingError("earliest post creator identity is unverifiable")
    result = {
        "status": "observed",
        "published_at_utc": _utc_iso(
            datetime.fromtimestamp(int(earliest["createTime"]), tz=UTC)
        ),
        "source_video_id": video_id,
        "source_video_url": video_url,
        "observed_at_utc": _utc_iso(utc_now_fn()),
        "selection_method": "tiktok_profile_oldest_sort_first_batch_min_exact_create_time_v1",
        "selection_attempt_count": selection_attempt_count,
        "timestamp_precision": "exact_source_create_time",
        "limitations": [
            "not_account_creation_time",
            "deleted_or_private_earlier_posts_not_observable",
        ],
    }
    assert_no_sensitive_tiktok_material(result)
    return result


def _verified_oldest_sort_action_receipt(
    capture: BrowserPageObservationSuccess,
) -> dict[str, Any]:
    receipts = capture.metadata.get("post_load_pointer_actions")
    if not isinstance(receipts, list) or not receipts:
        raise TikTokCreatorOnboardingError("Oldest sort action receipt is missing")
    oldest_receipt = receipts[-1]
    if (
        not isinstance(oldest_receipt, dict)
        or oldest_receipt.get("action_name")
        != TIKTOK_PROFILE_OLDEST_SORT_ACTION.action_name
        or oldest_receipt.get("clicked") is not True
    ):
        raise TikTokCreatorOnboardingError(
            "Oldest sort control was exposed but not clicked"
        )
    return oldest_receipt


def _earliest_public_post_unavailable(
    status: str, utc_now_fn: UtcNowFn
) -> dict[str, Any]:
    result = {
        "status": status,
        "published_at_utc": None,
        "source_video_id": None,
        "source_video_url": None,
        "observed_at_utc": _utc_iso(utc_now_fn()),
        "selection_method": "tiktok_profile_oldest_sort_first_batch_min_exact_create_time_v1",
        "timestamp_precision": None,
        "limitations": [
            "not_account_creation_time",
            "deleted_or_private_earlier_posts_not_observable",
        ],
    }
    assert_no_sensitive_tiktok_material(result)
    return result


def _run_grid_overlay_deep_capture_phase(
    state: _OnboardingRunState,
    *,
    profile_url: str,
    creator_handle: str,
    session_profile: SourceCaptureSessionProfile,
    auth_state_root: Path | None,
    storage_state_path: Path,
    paths: TikTokCreatorOnboardingOutputPaths,
    max_grid_scroll_passes: int,
    timeout_seconds: float,
    settle_seconds: float,
    cadence_policy: _OnboardingCadencePolicy,
    random_seed: int | None,
    engine: BrowserPageObservationEngine,
    progress_fn: ProgressFn | None,
    deep_capture_fn: DeepCaptureFn,
    sleep_fn: SleepFn,
    monotonic_fn: MonotonicFn,
    utc_now_fn: UtcNowFn,
    run_started_monotonic: float,
    activity_event_fn: ActivityEventFn | None,
) -> None:
    assert state.grid_capture is not None
    assert state.window_by_id is not None
    run_rng = (
        random.Random(random_seed)
        if random_seed is not None
        else random.SystemRandom()
    )
    initial_wait_plan = cadence_policy.build_plan(
        slot_count=2,
        random_seed=_derived_seed(random_seed, "initial_deep_capture_wait"),
    )
    planned_wait_seconds = initial_wait_plan.planned_waits_seconds[0]
    wait_observed_at_utc = _utc_iso(utc_now_fn())
    wait_started_monotonic = monotonic_fn()
    if activity_event_fn is not None:
        activity_event_fn(
            "cadence_wait_started",
            {
                "wait_kind": "initial_deep_capture",
                "policy": "completion_relative_after_grid_selection",
                "planned_seconds": planned_wait_seconds,
                "plan": initial_wait_plan.to_dict(),
            },
        )
    sleep_fn(planned_wait_seconds)
    wait_finished_monotonic = monotonic_fn()
    actual_wait_seconds = max(
        0.0, wait_finished_monotonic - wait_started_monotonic
    )
    if activity_event_fn is not None:
        activity_event_fn(
            "cadence_wait_finished",
            {
                "wait_kind": "initial_deep_capture",
                "planned_seconds": planned_wait_seconds,
                "actual_seconds": round(actual_wait_seconds, 6),
            },
        )
    state.initial_deep_capture_wait = {
        "policy": "randomized_wait_after_grid_before_first_deep_capture",
        "cadence_plan": initial_wait_plan.to_dict(),
        "minimum_seconds": cadence_policy.min_gap_seconds,
        "maximum_seconds": cadence_policy.max_gap_seconds,
        "planned_seconds": round(planned_wait_seconds, 6),
        "actual_seconds": round(
            actual_wait_seconds, 6
        ),
        "observed_at_utc": wait_observed_at_utc,
    }
    state.phase_chronology.append(
        _phase_chronology_row(
            "first_deep_capture_released",
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
        )
    )

    state.stage = "enter_grid_overlay_capture_sequence"
    _notify_progress(progress_fn, state.stage, selected_count=len(state.selected_video_ids))
    grid_deep_entry: dict[str, object] = {
        "policy": "all_selected_via_visible_grid_tile_overlay_with_bounded_pagination",
        "deep_capture_route": "grid_tile_overlay",
        "direct_video_navigation_count": 0,
        "targeted_tile_scroll_performed": False,
        "grid_pagination_allowed": True,
        "grid_pagination_input_method": (
            "cloakbrowser.human.scroll_to_element"
        ),
        "logical_grid_positions_remembered": True,
        "absolute_pixel_positions_cached": False,
        "tile_click_target_policy": (
            "randomized_exact_video_media_link_or_view_count_footer"
        ),
        "hover_preview_body_click_allowed": False,
        "click_target_safe_inset_fraction": 0.15,
        "grid_pagination_pass_cap_per_lookup": max_grid_scroll_passes,
        "grid_pagination_total_pass_cap": (
            max_grid_scroll_passes * len(state.selected_video_ids)
        ),
        "grid_pagination_passes_executed": 0,
        "grid_pagination_passes": [],
        "grid_pagination_stop_reason": None,
        "frozen_window_identity_drift_detected": False,
        "frozen_window_live_overlap_count_at_stop_or_none": None,
        "loaded_grid_video_count_at_stop_or_none": None,
        "attempts": [],
        "retry_waits": [],
        "status": "in_progress",
    }
    state.grid_deep_entry = grid_deep_entry
    selected_urls = [
        str(state.window_by_id[video_id]["video_url"])
        for video_id in state.selected_video_ids
    ]
    profile_grid_subtitle_sources = _profile_grid_subtitle_sources_from_capture(
        state.grid_capture,
        creator_handle=creator_handle,
    )
    selected_profile_grid_subtitle_sources = {
        video_id: profile_grid_subtitle_sources[video_id]
        for video_id in state.selected_video_ids
        if video_id in profile_grid_subtitle_sources
    }
    overlay_capture_sequence = _GridOverlayCaptureSequence(
        profile_url=profile_url,
        creator_handle=creator_handle,
        selected_video_ids=state.selected_video_ids,
        window_by_id=state.window_by_id,
        storage_state_path=storage_state_path,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        pagination_pass_cap=max_grid_scroll_passes,
        engine=engine,
        rng=run_rng,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
        utc_now_fn=utc_now_fn,
        receipt=grid_deep_entry,
        profile_grid_subtitle_sources_by_video_id=(
            selected_profile_grid_subtitle_sources
        ),
    )

    state.stage = "deep_capture"
    _notify_progress(progress_fn, state.stage, selected_count=len(state.selected_video_ids))
    deep_capture = deep_capture_fn(
        creator_handle=creator_handle,
        creator_profile_url=profile_url,
        video_urls=selected_urls,
        state_label=session_profile.state_label,
        session_mode=session_profile.session_mode,
        logged_out=False,
        auth_state_root=auth_state_root,
        timeout_seconds=timeout_seconds,
        settle_seconds=settle_seconds,
        browser_backend=session_profile.browser_backend,
        required_harness_proxy_profile_posture=(
            session_profile.required_harness_proxy_profile_posture
        ),
        human_challenge_handoff=True,
        cadence_min_gap_seconds=cadence_policy.min_gap_seconds,
        cadence_max_gap_seconds=cadence_policy.max_gap_seconds,
        cadence_window_seconds=cadence_policy.window_seconds,
        cadence_mode=cadence_policy.mode,
        cadence_typical_min_gap_seconds=cadence_policy.typical_min_gap_seconds,
        cadence_typical_max_gap_seconds=cadence_policy.typical_max_gap_seconds,
        cadence_tail_min_gap_seconds=cadence_policy.tail_min_gap_seconds,
        cadence_tail_max_gap_seconds=cadence_policy.tail_max_gap_seconds,
        cadence_tail_probability=cadence_policy.tail_probability,
        random_seed=random_seed,
        engine=engine,
        capture_route="grid_tile_overlay",
        page_capture_sequence_fn=overlay_capture_sequence,
        grid_candidates_by_video_id=state.window_by_id,
        profile_grid_subtitle_sources_by_video_id=(
            selected_profile_grid_subtitle_sources
        ),
        activity_event_fn=activity_event_fn,
    )
    state.deep_capture = deep_capture
    state.captured_video_ids = [
        str(row["video_id"])
        for row in deep_capture["cadence_result"].get("results", [])
        if isinstance(row, dict) and row.get("video_id")
    ]
    if grid_deep_entry.get("status") == "complete":
        state.phase_chronology.append(
            _phase_chronology_row(
                "grid_overlay_deep_capture_sequence_completed",
                run_started_monotonic=run_started_monotonic,
                monotonic_fn=monotonic_fn,
                utc_now_fn=utc_now_fn,
            )
        )
    _write_json(paths.live_grid_json_path, deep_capture["grid_result"])
    state.artifacts_written.append(paths.live_grid_json_path.name)
    _write_json(paths.live_cadence_json_path, deep_capture["cadence_result"])
    state.artifacts_written.append(paths.live_cadence_json_path.name)
    state.challenge_count = int(
        deep_capture["cadence_result"].get("challenge_count", 0)
    )
    state.human_challenge_handoff_count = int(
        deep_capture["cadence_result"].get(
            "human_challenge_handoff_count", 0
        )
    )
    state.completed_count = int(deep_capture["cadence_result"]["completed_count"])
    state.account_safety_stop = _has_account_safety_stop(
        deep_capture["cadence_result"]
    )
    state.status = (
        "complete"
        if state.completed_count == len(state.selected_video_ids)
        else "partial_failure"
    )
    if state.status != "complete":
        if state.account_safety_stop:
            raise TikTokCreatorOnboardingError("account_safety_stop")
        raise TikTokCreatorOnboardingError(
            "one or more selected video deep captures did not complete"
        )
    state.phase_chronology.append(
        _phase_chronology_row(
            "deep_capture_completed",
            run_started_monotonic=run_started_monotonic,
            monotonic_fn=monotonic_fn,
            utc_now_fn=utc_now_fn,
        )
    )


def _build_onboarding_receipt(
    state: _OnboardingRunState,
    *,
    observation_engine: BrowserPageObservationEngine | None,
    owned_engine: bool,
    creator_handle: str,
    session_profile: SourceCaptureSessionProfile,
    window_size: int,
    selection_count: int,
) -> dict[str, Any]:
    lifecycle_receipt = getattr(observation_engine, "lifecycle_receipt", None)
    grid_overlay_capture_order = (
        list(state.grid_deep_entry.get("selected_video_ids_in_capture_order", []))
        if isinstance(state.grid_deep_entry, dict)
        and isinstance(
            state.grid_deep_entry.get("selected_video_ids_in_capture_order"), list
        )
        else []
    )
    return {
        "schema_version": TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION,
        "status": state.status,
        "terminal_stage": state.stage,
        "creator_handle": creator_handle,
        "session_profile": session_profile.alias,
        "window_size": (
            len(state.grid_window["items"]) if state.grid_window is not None else 0
        ),
        "window_cap": window_size,
        "selection_count": selection_count,
        "suggested_accounts_status_or_none": state.suggested_status,
        "suggested_outer_ui_route_or_none": state.suggested_outer_ui_route,
        "suggested_surface_close_before_grid_or_none": state.suggested_surface_close,
        "candidate_profiles_opened": 0,
        "account_mutations_taken": 0,
        "selected_video_ids_in_capture_order": (
            state.captured_video_ids
            if state.captured_video_ids is not None
            else grid_overlay_capture_order
        ),
        "selected_count": len(state.selected_video_ids),
        "challenge_count": state.challenge_count,
        "human_challenge_handoff_count": state.human_challenge_handoff_count,
        "account_safety_stop": state.account_safety_stop,
        "completed_deep_capture_count": state.completed_count,
        "completed_deep_capture_count_source": (
            "cadence_result" if state.deep_capture is not None else "no_cadence_result"
        ),
        "completed_grid_overlay_capture_count": len(grid_overlay_capture_order),
        "initial_deep_capture_wait_or_none": state.initial_deep_capture_wait,
        "grid_deep_entry_or_none": state.grid_deep_entry,
        "earliest_public_post_observation_or_none": (
            state.earliest_public_post_observation
        ),
        "link_hub_observation_or_none": state.link_hub_observation,
        "market_assessment_or_none": state.market_assessment,
        "phase_chronology": state.phase_chronology,
        "artifacts_written": state.artifacts_written,
        "browser_lifecycle": (
            lifecycle_receipt
            if isinstance(lifecycle_receipt, dict)
            else {
                "engine": type(observation_engine).__name__,
                "owned_by_onboarding_runner": owned_engine,
                "closed_or_none": True if owned_engine else None,
            }
        ),
        "error_or_none": state.error,
        "activity_journal_error_or_none": state.journal_error,
        "activity_journal_role": "diagnostic_only_not_resume_or_checkpoint_state",
        "non_claims": [
            "not a standing scanner or crawler",
            "not Creator Registry mutation",
            "not an exhaustive suggested-account graph",
            "not paid or organic distribution classification",
        ],
    }


def _capture_suggested_accounts(
    *,
    profile_url: str,
    creator_handle: str,
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
    primary = fetch_browser_page_observation_capture(
        url=profile_url,
        dom_extract_script=TIKTOK_SUGGESTED_ACCOUNTS_DOM_EXTRACT_SCRIPT,
        dom_extract_arg={"creator_handle": creator_handle},
        response_url_predicate=lambda _: False,
        post_load_pointer_actions=(
            TIKTOK_FOLLOWERS_ACTION,
            TIKTOK_RELATIONSHIP_SUGGESTED_TAB_ACTION,
        ),
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        engine=engine,
    )
    if isinstance(primary, BrowserSnapshotFailure):
        return primary
    primary_dom = primary.dom_observation
    if (
        isinstance(primary_dom, dict)
        and primary_dom.get("relationship_dialog_detected") is True
        and primary_dom.get("suggested_tab_detected") is True
    ):
        primary.metadata["suggested_outer_ui_route"] = (
            "followers_dialog_suggested_tab_primary"
        )
        primary.metadata["suggested_primary_pointer_actions"] = primary.metadata.get(
            "post_load_pointer_actions"
        )
        primary.metadata["suggested_fallback_pointer_actions"] = []
        return primary

    fallback = fetch_browser_page_observation_capture(
        url=profile_url,
        dom_extract_script=TIKTOK_SUGGESTED_ACCOUNTS_FALLBACK_DOM_EXTRACT_SCRIPT,
        dom_extract_arg={"creator_handle": creator_handle},
        response_url_predicate=lambda _: False,
        post_load_pointer_actions=(
            TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION,
            TIKTOK_SUGGESTED_VIEW_ALL_ACTION,
        ),
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        engine=engine,
    )
    if isinstance(fallback, BrowserPageObservationSuccess):
        if isinstance(fallback.dom_observation, dict) and isinstance(
            primary.dom_observation, dict
        ):
            fallback.dom_observation["profile_external_links"] = (
                primary.dom_observation.get("profile_external_links", [])
            )
            primary_bio_text = primary.dom_observation.get(
                "profile_bio_text_or_none"
            )
            if isinstance(primary_bio_text, str) and primary_bio_text.strip():
                fallback.dom_observation["profile_bio_text_or_none"] = (
                    primary_bio_text
                )
            if primary.dom_observation.get("profile_bio_element_detected") is True:
                fallback.dom_observation["profile_bio_element_detected"] = True
        fallback.metadata["suggested_outer_ui_route"] = (
            "profile_suggested_accounts_view_all_fallback"
        )
        fallback.metadata["suggested_primary_pointer_actions"] = primary.metadata.get(
            "post_load_pointer_actions"
        )
        fallback.metadata["suggested_fallback_pointer_actions"] = fallback.metadata.get(
            "post_load_pointer_actions"
        )
    return fallback


def _close_suggested_surface_before_grid(
    *,
    profile_url: str,
    creator_handle: str,
    suggested_status: str,
    suggested_outer_ui_route: str,
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
) -> dict[str, object]:
    close_required = suggested_status in {"captured", "visible_empty"}
    close_action_route = "none"
    pointer_actions: tuple[BrowserPagePointerAction, ...] = ()
    if close_required:
        if suggested_outer_ui_route.startswith("followers_dialog_suggested_tab"):
            close_action_route = "relationship_dialog_close"
            pointer_actions = (TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION,)
        elif suggested_outer_ui_route == "profile_suggested_accounts_view_all_fallback":
            close_action_route = "suggested_accounts_toggle_collapse"
            pointer_actions = (TIKTOK_SUGGESTED_ACCOUNTS_COLLAPSE_ACTION,)
        else:
            raise TikTokCreatorOnboardingError(
                "unsupported suggested outer UI route before grid capture"
            )
    capture = fetch_browser_page_observation_capture(
        url=profile_url,
        dom_extract_script=TIKTOK_SUGGESTED_SURFACE_CLOSED_DOM_EXTRACT_SCRIPT,
        dom_extract_arg={"creator_handle": creator_handle},
        response_url_predicate=lambda _: False,
        post_load_pointer_actions=pointer_actions,
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        engine=engine,
    )
    if isinstance(capture, BrowserSnapshotFailure):
        raise TikTokCreatorOnboardingError(
            "suggested surface close verification failed before grid capture"
        )
    action = _first_pointer_action_receipt(capture)
    dom = capture.dom_observation if isinstance(capture.dom_observation, dict) else {}
    clicked = isinstance(action, dict) and action.get("clicked") is True
    modal_open_after = dom.get("suggested_modal_open") is True
    suggested_accounts_expanded_after = dom.get("suggested_accounts_expanded") is True
    body_scroll_locked_after = dom.get("body_scroll_locked") is True
    blocking_modal_count_after = _non_negative_int_or_zero(
        dom.get("blocking_modal_count")
    )
    route_surface_open_after = (
        modal_open_after
        if close_action_route == "relationship_dialog_close"
        else suggested_accounts_expanded_after
        if close_action_route == "suggested_accounts_toggle_collapse"
        else False
    )
    if (
        route_surface_open_after
        or body_scroll_locked_after
        or blocking_modal_count_after > 0
        or (close_required and not clicked)
    ):
        raise TikTokCreatorOnboardingError(
            "suggested surface remained open before grid capture"
        )
    return {
        "policy": "close_suggested_surface_before_any_grid_wheel_or_tile_click",
        "status": "closed" if clicked else "already_closed",
        "close_required": close_required,
        "close_clicked": clicked,
        "close_action_route": close_action_route,
        "suggested_outer_ui_route": suggested_outer_ui_route,
        "suggested_modal_open_after": modal_open_after,
        "suggested_modal_count_after": _non_negative_int_or_zero(
            dom.get("suggested_modal_count")
        ),
        "suggested_accounts_expanded_after": suggested_accounts_expanded_after,
        "suggested_accounts_expanded_root_count_after": _non_negative_int_or_zero(
            dom.get("suggested_accounts_expanded_root_count")
        ),
        "body_scroll_locked_after": body_scroll_locked_after,
        "blocking_modal_count_after": blocking_modal_count_after,
        "grid_video_anchor_count_after": _non_negative_int_or_zero(
            dom.get("grid_video_anchor_count")
        ),
        "pointer_action_or_none": action,
    }


class _GridOverlayCaptureSequence:
    """Choose every deep capture from visible selected tiles on one grid page."""

    def __init__(
        self,
        *,
        profile_url: str,
        creator_handle: str,
        selected_video_ids: Sequence[str],
        window_by_id: dict[str, dict[str, Any]],
        storage_state_path: Path,
        timeout_seconds: float,
        settle_seconds: float,
        pagination_pass_cap: int,
        engine: BrowserPageObservationEngine,
        rng: Any,
        sleep_fn: SleepFn,
        monotonic_fn: MonotonicFn,
        utc_now_fn: UtcNowFn,
        receipt: dict[str, object],
        profile_grid_subtitle_sources_by_video_id: (
            Mapping[str, dict[str, Any]] | None
        ) = None,
        collect_content_responses: bool = True,
        pagination_total_pass_cap: int | None = None,
    ) -> None:
        self.profile_url = profile_url
        self.creator_handle = creator_handle
        self.selected_video_ids = tuple(selected_video_ids)
        self.window_by_id = window_by_id
        self.storage_state_path = storage_state_path
        self.timeout_seconds = timeout_seconds
        self.settle_seconds = settle_seconds
        self.pagination_pass_cap = pagination_pass_cap
        self.engine = engine
        self.rng = rng
        self.sleep_fn = sleep_fn
        self.monotonic_fn = monotonic_fn
        self.utc_now_fn = utc_now_fn
        self.receipt = receipt
        self.profile_grid_subtitle_sources_by_video_id = dict(
            profile_grid_subtitle_sources_by_video_id or {}
        )
        self.collect_content_responses = collect_content_responses
        self.pagination_total_pass_cap = pagination_total_pass_cap
        self.current_overlay_url: str | None = None
        self.capture_order: list[str] = []
        self.last_grid_view: dict[str, object] = {}
        self.last_pagination_direction: str | None = None

    def __call__(
        self, index: int, pending_video_urls: Sequence[str]
    ) -> tuple[str, BrowserPageObservationSuccess | BrowserSnapshotFailure]:
        pending_by_id = {
            _video_id_from_url(url): url for url in pending_video_urls
        }
        if not pending_by_id or not set(pending_by_id).issubset(self.selected_video_ids):
            raise TikTokCreatorOnboardingError(
                "overlay capture sequence received an invalid pending selection"
            )
        visible_rows: list[dict[str, Any]] = []
        if self.current_overlay_url is not None:
            visible_rows = self._close_current_overlay(tuple(pending_by_id))
        if (
            not visible_rows
            and self.receipt.get("grid_pagination_stop_reason")
            != "frozen_window_identity_drift"
        ):
            visible_rows = self._visible_rows(tuple(pending_by_id))
        if (
            not visible_rows
            and self.receipt.get("grid_pagination_stop_reason")
            != "frozen_window_identity_drift"
        ):
            visible_rows = self._paginate_until_visible(tuple(pending_by_id))
        if not visible_rows:
            self.receipt["status"] = "failed"
            if (
                self.receipt.get("grid_pagination_stop_reason")
                == "frozen_window_identity_drift"
            ):
                raise TikTokCreatorOnboardingError(
                    "frozen grid window no longer matches the live grid identity"
                )
            raise TikTokCreatorOnboardingError(
                "bounded grid pagination exhausted before a selected tile became visible"
            )

        for retry_number in (0, 1):
            if not visible_rows:
                break
            chosen = self.rng.choice(visible_rows)
            chosen_video_id = str(chosen["video_id"])
            chosen_url = pending_by_id[chosen_video_id]
            subtitle_source = self.profile_grid_subtitle_sources_by_video_id.get(
                chosen_video_id
            )
            expected_subtitle_url = (
                tiktok_subtitle_url_from_source(subtitle_source)
                if subtitle_source is not None
                else None
            )
            click_target_text = str(
                chosen.get("click_target_text_or_none") or ""
            ).strip()
            if not click_target_text:
                raise TikTokCreatorOnboardingError(
                    "visible selected grid tile lacks a link-routed footer target"
                )
            click_capture = _click_visible_selected_grid_tile(
                profile_url=self.profile_url,
                creator_handle=self.creator_handle,
                selected_video_ids=tuple(pending_by_id),
                chosen_video_id=chosen_video_id,
                click_target_text=click_target_text,
                storage_state_path=self.storage_state_path,
                timeout_seconds=self.timeout_seconds,
                settle_seconds=self.settle_seconds,
                engine=self.engine,
                expected_subtitle_url=expected_subtitle_url,
                collect_content_responses=self.collect_content_responses,
            )
            attempt_receipt = self._click_attempt_receipt(
                index=index,
                retry_number=retry_number,
                chosen=chosen,
                visible_rows=visible_rows,
                capture=click_capture,
            )
            attempts = self.receipt["attempts"]
            assert isinstance(attempts, list)
            attempts.append(attempt_receipt)
            if (
                isinstance(click_capture, BrowserPageObservationSuccess)
                and attempt_receipt["outcome"] == "overlay_ready"
            ):
                self.current_overlay_url = click_capture.final_url
                self.capture_order.append(chosen_video_id)
                self.receipt["capture_order_policy"] = (
                    "random_among_visible_selected_then_bounded_grid_pagination"
                )
                self.receipt["selected_video_ids_in_capture_order"] = list(
                    self.capture_order
                )
                self.receipt["status"] = (
                    "complete"
                    if len(self.capture_order) == len(self.selected_video_ids)
                    else "in_progress"
                )
                return chosen_url, click_capture

            if retry_number == 0:
                retry_started = self.monotonic_fn()
                observed_at = _utc_iso(self.utc_now_fn())
                retry_wait_seconds = _sample_browser_delay_seconds(
                    GRID_ENTRY_RETRY_DELAY_RANGE,
                    rng=self.rng,
                )
                self.sleep_fn(retry_wait_seconds)
                retry_waits = self.receipt["retry_waits"]
                assert isinstance(retry_waits, list)
                retry_waits.append(
                    {
                        "video_attempt_index": index,
                        "configured_range_seconds": {
                            "min": GRID_ENTRY_RETRY_DELAY_RANGE.min_ms / 1000,
                            "max": GRID_ENTRY_RETRY_DELAY_RANGE.max_ms / 1000,
                        },
                        "planned_seconds": retry_wait_seconds,
                        "actual_seconds": round(
                            max(0.0, self.monotonic_fn() - retry_started), 6
                        ),
                        "observed_at_utc": observed_at,
                    }
                )
                if (
                    isinstance(click_capture, BrowserPageObservationSuccess)
                    and _is_any_creator_video_url(
                        click_capture.final_url, self.creator_handle
                    )
                ):
                    self.current_overlay_url = click_capture.final_url
                    visible_rows = self._close_current_overlay(tuple(pending_by_id))
                else:
                    visible_rows = []
                if (
                    not visible_rows
                    and self.receipt.get("grid_pagination_stop_reason")
                    != "frozen_window_identity_drift"
                ):
                    visible_rows = self._visible_rows(tuple(pending_by_id))
                if not visible_rows:
                    visible_rows = self._paginate_until_visible(
                        tuple(pending_by_id)
                    )

        self.receipt["status"] = "failed"
        raise TikTokCreatorOnboardingError(
            "grid tile did not materialize a matching overlay after one bounded retry"
        )

    def close_current_overlay(self) -> None:
        if self.current_overlay_url is None:
            raise TikTokCreatorOnboardingError(
                "video overlay close requested without an open overlay"
            )
        self._close_current_overlay(())

    def _visible_rows(self, pending_video_ids: Sequence[str]) -> list[dict[str, Any]]:
        capture = _capture_visible_selected_grid_tiles(
            profile_url=self.profile_url,
            creator_handle=self.creator_handle,
            selected_video_ids=pending_video_ids,
            storage_state_path=self.storage_state_path,
            timeout_seconds=self.timeout_seconds,
            settle_seconds=self.settle_seconds,
            engine=self.engine,
        )
        if isinstance(capture, BrowserSnapshotFailure):
            return []
        self._remember_grid_view(capture)
        if self._frozen_window_identity_drifted():
            self._record_frozen_window_identity_drift()
            return []
        return _visible_grid_rows_from_capture(capture)

    def _paginate_until_visible(
        self, pending_video_ids: Sequence[str]
    ) -> list[dict[str, Any]]:
        previous_fingerprint = self._grid_progress_fingerprint()
        observed_fingerprints = {previous_fingerprint}
        consecutive_no_progress = 0
        lookup_pass_cap = self.pagination_pass_cap
        if self.pagination_total_pass_cap is not None:
            remaining_total_passes = max(
                0,
                self.pagination_total_pass_cap
                - int(self.receipt["grid_pagination_passes_executed"]),
            )
            lookup_pass_cap = min(lookup_pass_cap, remaining_total_passes)
        for lookup_pass_number in range(1, lookup_pass_cap + 1):
            total_pass_number = int(
                self.receipt["grid_pagination_passes_executed"]
            ) + 1
            direction = self._pagination_direction(pending_video_ids)
            self.last_pagination_direction = direction
            target_video_id = self._pagination_target_video_id(
                pending_video_ids,
                direction=direction,
            )
            self.receipt["targeted_tile_scroll_performed"] = True
            capture = _capture_visible_selected_grid_tiles(
                profile_url=self.profile_url,
                creator_handle=self.creator_handle,
                selected_video_ids=pending_video_ids,
                storage_state_path=self.storage_state_path,
                timeout_seconds=self.timeout_seconds,
                settle_seconds=self.settle_seconds,
                engine=self.engine,
                pagination_direction=direction,
                pagination_target_video_id=target_video_id,
            )
            self.receipt["grid_pagination_passes_executed"] = total_pass_number
            pagination_passes = self.receipt["grid_pagination_passes"]
            assert isinstance(pagination_passes, list)
            pass_receipt: dict[str, object] = {
                "lookup_pass_number": lookup_pass_number,
                "total_pass_number": total_pass_number,
                "direction": direction,
                "target_video_id": target_video_id,
                "wheel_action_or_none": None,
            }
            if isinstance(capture, BrowserSnapshotFailure):
                pass_receipt["outcome"] = f"capture_failed:{capture.failure_kind.value}"
                pagination_passes.append(pass_receipt)
                continue
            self._remember_grid_view(capture)
            wheel_action = capture.metadata.get("post_load_wheel_action")
            pass_receipt["wheel_action_or_none"] = wheel_action
            pass_receipt["visible_grid_position_min_or_none"] = (
                self.last_grid_view.get("visible_grid_position_min_or_none")
            )
            pass_receipt["visible_grid_position_max_or_none"] = (
                self.last_grid_view.get("visible_grid_position_max_or_none")
            )
            pass_receipt["scroll_y_or_none"] = self.last_grid_view.get("scroll_y")
            pass_receipt["document_height_or_none"] = self.last_grid_view.get(
                "document_height"
            )
            pass_receipt["actual_scroll_delta_y_px_or_none"] = (
                wheel_action.get("actual_scroll_delta_y_px")
                if isinstance(wheel_action, dict)
                else None
            )
            rows = _visible_grid_rows_from_capture(capture)
            if rows:
                pass_receipt["progress_since_previous"] = "selected_tile_visible"
                pass_receipt["outcome"] = "selected_tile_visible"
                pagination_passes.append(pass_receipt)
                return rows
            if self._frozen_window_identity_drifted():
                self._record_frozen_window_identity_drift()
                pass_receipt["progress_since_previous"] = (
                    "frozen_window_identity_drift"
                )
                pass_receipt["outcome"] = (
                    "frozen_window_identity_drift_budget_stopped"
                )
                pagination_passes.append(pass_receipt)
                return []
            current_fingerprint = self._grid_progress_fingerprint()
            if current_fingerprint != previous_fingerprint:
                consecutive_no_progress = 0
                if current_fingerprint in observed_fingerprints:
                    pass_receipt["progress_since_previous"] = "progress_cycle"
                    pass_receipt["consecutive_no_progress_passes"] = 0
                    pass_receipt["outcome"] = "progress_cycle_budget_stopped"
                    self.receipt["grid_pagination_stop_reason"] = "progress_cycle"
                    pagination_passes.append(pass_receipt)
                    return []
                pass_receipt["progress_since_previous"] = "advanced"
                observed_fingerprints.add(current_fingerprint)
            else:
                consecutive_no_progress += 1
                pass_receipt["progress_since_previous"] = "no_progress"
            previous_fingerprint = current_fingerprint
            pass_receipt["consecutive_no_progress_passes"] = consecutive_no_progress
            if consecutive_no_progress >= GRID_PAGINATION_NO_PROGRESS_STALL_LIMIT:
                # The grid is not advancing under bounded humanized target scroll
                # input from its
                # fresh state; stop rather than spend the rest of the budget on
                # no-value wheel actions. Fail loud via the empty return; no
                # wait is taken here (doctrine reserves the bounded retry wait for a
                # failed matching-overlay materialization only).
                pass_receipt["outcome"] = "no_progress_stall_budget_stopped"
                self.receipt["grid_pagination_stop_reason"] = "no_progress_stall"
                pagination_passes.append(pass_receipt)
                return []
            pass_receipt["outcome"] = "no_selected_tile_visible"
            pagination_passes.append(pass_receipt)
        self.receipt["grid_pagination_stop_reason"] = (
            "total_pass_cap_reached"
            if (
                self.pagination_total_pass_cap is not None
                and int(self.receipt["grid_pagination_passes_executed"])
                >= self.pagination_total_pass_cap
            )
            else "pass_cap_reached"
        )
        return []

    def _remember_grid_view(self, capture: BrowserPageObservationSuccess) -> None:
        observation = capture.dom_observation
        self.last_grid_view = {
            "visible_grid_position_min_or_none": observation.get(
                "visible_grid_position_min_or_none"
            ),
            "visible_grid_position_max_or_none": observation.get(
                "visible_grid_position_max_or_none"
            ),
            "scroll_y": observation.get("scroll_y"),
            "document_height": observation.get("document_height"),
            "loaded_grid_video_ids": tuple(
                str(video_id)
                for video_id in observation.get("loaded_grid_video_ids", [])
                if isinstance(video_id, (str, int)) and str(video_id).strip()
            ),
        }

    def _frozen_window_identity_drifted(self) -> bool:
        loaded_video_ids = self.last_grid_view.get("loaded_grid_video_ids")
        if not isinstance(loaded_video_ids, tuple) or not loaded_video_ids:
            return False
        frozen_positions = [
            int(row["grid_position"])
            for row in self.window_by_id.values()
            if row.get("grid_position") is not None
        ]
        if not frozen_positions or len(loaded_video_ids) < max(frozen_positions):
            return False
        return not set(loaded_video_ids).intersection(self.window_by_id)

    def _record_frozen_window_identity_drift(self) -> None:
        loaded_video_ids = self.last_grid_view.get("loaded_grid_video_ids")
        loaded = set(loaded_video_ids) if isinstance(loaded_video_ids, tuple) else set()
        self.receipt["grid_pagination_stop_reason"] = (
            "frozen_window_identity_drift"
        )
        self.receipt["frozen_window_identity_drift_detected"] = True
        self.receipt["frozen_window_live_overlap_count_at_stop_or_none"] = len(
            loaded.intersection(self.window_by_id)
        )
        self.receipt["loaded_grid_video_count_at_stop_or_none"] = len(loaded)

    def _grid_progress_fingerprint(self) -> tuple[object, object, object, object]:
        """Fresh-state grid signals used to detect a non-advancing grid.

        Progress is measured from the grid's freshly observed state (scroll
        position, document height, visible logical range) rather than from the
        mere fact that a wheel burst was attempted, so a short/non-expanded grid
        that does not move under wheel input is detectable.
        """

        view = self.last_grid_view
        return (
            view.get("visible_grid_position_min_or_none"),
            view.get("visible_grid_position_max_or_none"),
            view.get("scroll_y"),
            view.get("document_height"),
        )

    def _pagination_direction(self, pending_video_ids: Sequence[str]) -> str:
        pending_positions = [
            int(self.window_by_id[video_id]["grid_position"])
            for video_id in pending_video_ids
            if video_id in self.window_by_id
            and self.window_by_id[video_id].get("grid_position") is not None
        ]
        visible_min = self.last_grid_view.get("visible_grid_position_min_or_none")
        visible_max = self.last_grid_view.get("visible_grid_position_max_or_none")
        if pending_positions and isinstance(visible_min, (int, float)) and isinstance(
            visible_max, (int, float)
        ):
            above = [position for position in pending_positions if position < visible_min]
            below = [position for position in pending_positions if position > visible_max]
            if above and below:
                up_gap = visible_min - max(above)
                down_gap = min(below) - visible_max
                return "up" if up_gap <= down_gap else "down"
            if above:
                return "up"
            if below:
                return "down"
            if self.last_pagination_direction is not None:
                return self.last_pagination_direction
        return "up" if float(self.last_grid_view.get("scroll_y") or 0) > 0 else "down"

    def _pagination_target_video_id(
        self,
        pending_video_ids: Sequence[str],
        *,
        direction: str,
    ) -> str:
        positioned = sorted(
            (
                int(self.window_by_id[video_id]["grid_position"]),
                video_id,
            )
            for video_id in pending_video_ids
            if video_id in self.window_by_id
            and self.window_by_id[video_id].get("grid_position") is not None
        )
        if not positioned:
            raise TikTokCreatorOnboardingError(
                "pending selected tiles lack frozen logical grid positions"
            )
        visible_min = self.last_grid_view.get("visible_grid_position_min_or_none")
        visible_max = self.last_grid_view.get("visible_grid_position_max_or_none")
        if direction == "down" and isinstance(visible_max, (int, float)):
            below = [row for row in positioned if row[0] > visible_max]
            if below:
                return str(below[0][1])
        if direction == "up" and isinstance(visible_min, (int, float)):
            above = [row for row in positioned if row[0] < visible_min]
            if above:
                return str(above[-1][1])
        return str(positioned[-1 if direction == "down" else 0][1])

    def _close_current_overlay(
        self, pending_video_ids: Sequence[str]
    ) -> list[dict[str, Any]]:
        assert self.current_overlay_url is not None
        capture = fetch_browser_page_observation_capture(
            url=self.current_overlay_url,
            dom_extract_script=TIKTOK_VISIBLE_SELECTED_GRID_TILES_DOM_EXTRACT_SCRIPT,
            dom_extract_arg={
                "creator_handle": self.creator_handle,
                "selected_video_ids": list(pending_video_ids),
            },
            response_url_predicate=lambda _: False,
            post_load_pointer_actions=(TIKTOK_VIDEO_OVERLAY_CLOSE_ACTION,),
            timeout_seconds=self.timeout_seconds,
            wait_until="domcontentloaded",
            settle_seconds=self.settle_seconds,
            storage_state_path=self.storage_state_path,
            headless=False,
            browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
            human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
            human_challenge_handoff_timeout_seconds=180.0,
            human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
            engine=self.engine,
        )
        action = _first_pointer_action_receipt(capture)
        if (
            isinstance(capture, BrowserSnapshotFailure)
            or not isinstance(action, dict)
            or action.get("clicked") is not True
            or not _is_creator_profile_url(capture.final_url, self.creator_handle)
        ):
            self.receipt["status"] = "failed"
            raise TikTokCreatorOnboardingError(
                "video overlay close did not return to the creator grid"
            )
        self.current_overlay_url = None
        self._remember_grid_view(capture)
        if self._frozen_window_identity_drifted():
            self._record_frozen_window_identity_drift()
            return []
        return _visible_grid_rows_from_capture(capture)

    def _click_attempt_receipt(
        self,
        *,
        index: int,
        retry_number: int,
        chosen: dict[str, Any],
        visible_rows: Sequence[dict[str, Any]],
        capture: BrowserPageObservationSuccess | BrowserSnapshotFailure,
    ) -> dict[str, object]:
        chosen_video_id = str(chosen["video_id"])
        action = _first_pointer_action_receipt(capture)
        overlay_ready = (
            isinstance(capture, BrowserPageObservationSuccess)
            and isinstance(action, dict)
            and action.get("clicked") is True
            and _overlay_capture_ready(
                capture,
                creator_handle=self.creator_handle,
                video_id=chosen_video_id,
            )
        )
        return {
            "video_attempt_index": index,
            "retry_number": retry_number,
            "observed_at_utc": _utc_iso(self.utc_now_fn()),
            "visible_selected_video_ids": [
                str(row["video_id"]) for row in visible_rows
            ],
            "chosen_video_id": chosen_video_id,
            "chosen_grid_position": chosen.get("grid_position"),
            "click_target_kind": chosen.get("click_target_kind"),
            "click_target_text_or_none": chosen.get("click_target_text_or_none"),
            "click_action_or_none": action,
            "final_url_or_none": (
                capture.final_url
                if isinstance(capture, BrowserPageObservationSuccess)
                else None
            ),
            "overlay_ready": overlay_ready,
            "item_struct_required": False,
            "outcome": (
                "overlay_ready"
                if overlay_ready
                else f"click_capture_failed:{capture.failure_kind.value}"
                if isinstance(capture, BrowserSnapshotFailure)
                else "overlay_not_ready_or_identity_mismatch"
            ),
        }


def _capture_visible_selected_grid_tiles(
    *,
    profile_url: str,
    creator_handle: str,
    selected_video_ids: Sequence[str],
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    pagination_direction: str | None = None,
    pagination_target_video_id: str | None = None,
) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
    if pagination_direction not in {None, "up", "down"}:
        raise ValueError("pagination_direction must be up, down, or None")
    if (pagination_direction is None) != (pagination_target_video_id is None):
        raise ValueError(
            "pagination direction and target video id must be configured together"
        )
    return fetch_browser_page_observation_capture(
        url=profile_url,
        dom_extract_script=TIKTOK_VISIBLE_SELECTED_GRID_TILES_DOM_EXTRACT_SCRIPT,
        dom_extract_arg={
            "creator_handle": creator_handle,
            "selected_video_ids": list(selected_video_ids),
        },
        response_url_predicate=lambda _: False,
        post_load_wheel_action=(
            BrowserPageWheelAction(
                action_name="tiktok_grid_humanized_target_scroll_v0",
                direction=pagination_direction,
                viewport_fraction_min=(
                    GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MIN
                ),
                viewport_fraction_max=(
                    GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MAX
                ),
                target_selector=(
                    f"a[href*='/video/{pagination_target_video_id}']"
                ),
            )
            if pagination_direction is not None
            else None
        ),
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        engine=engine,
    )


def _click_visible_selected_grid_tile(
    *,
    profile_url: str,
    creator_handle: str,
    selected_video_ids: Sequence[str],
    chosen_video_id: str,
    click_target_text: str,
    storage_state_path: Path,
    timeout_seconds: float,
    settle_seconds: float,
    engine: BrowserPageObservationEngine,
    expected_subtitle_url: str | None,
    collect_content_responses: bool = True,
) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
    video_anchor_selector = f"a[href*='/video/{chosen_video_id}']"
    view_count_selector = f"{video_anchor_selector} .video-count"
    action = BrowserPagePointerAction(
        action_name="tiktok_visible_selected_grid_video_v0",
        candidate_selector=view_count_selector,
        target_variants=(
            BrowserPagePointerTargetVariant(
                variant_name="media_link_surface",
                candidate_selector=video_anchor_selector,
                target_fraction_x_min=0.20,
                target_fraction_x_max=0.80,
                target_fraction_y_min=0.25,
                target_fraction_y_max=0.70,
            ),
            BrowserPagePointerTargetVariant(
                variant_name="view_count_footer",
                candidate_selector=view_count_selector,
                target_fraction_x_min=0.15,
                target_fraction_x_max=0.85,
                target_fraction_y_min=0.25,
                target_fraction_y_max=0.75,
            ),
        ),
        text_markers=(click_target_text,),
        wait_after_range=TIKTOK_STATE_WAIT_2500_DELAY_RANGE,
        prefer_smallest_match=True,
    )
    return fetch_browser_page_observation_capture(
        url=profile_url,
        dom_extract_script=TIKTOK_VIDEO_DOM_EXTRACT_SCRIPT,
        dom_extract_arg=None,
        response_url_predicate=(
            (
                lambda url: is_tiktok_comment_list_url(url)
                or (
                    expected_subtitle_url is not None
                    and is_exact_tiktok_subtitle_response_url(
                        url,
                        expected_subtitle_url=expected_subtitle_url,
                    )
                )
            )
            if collect_content_responses
            else (lambda _url: False)
        ),
        post_load_pointer_actions=(action,),
        timeout_seconds=timeout_seconds,
        wait_until="domcontentloaded",
        settle_seconds=settle_seconds,
        storage_state_path=storage_state_path,
        headless=False,
        browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
        human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
        human_challenge_handoff_timeout_seconds=180.0,
        human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
        engine=engine,
    )


def _sample_browser_delay_seconds(
    delay_range: BrowserDelayRange,
    *,
    rng: Any,
) -> float:
    return rng.randint(delay_range.min_ms, delay_range.max_ms) / 1000


def _first_pointer_action_receipt(
    capture: BrowserPageObservationSuccess | BrowserSnapshotFailure,
) -> dict[str, Any] | None:
    if isinstance(capture, BrowserSnapshotFailure):
        return None
    actions = capture.metadata.get("post_load_pointer_actions")
    if not isinstance(actions, list) or not actions or not isinstance(actions[0], dict):
        return None
    return actions[0]


def _overlay_capture_ready(
    capture: BrowserPageObservationSuccess,
    *,
    creator_handle: str,
    video_id: str,
) -> bool:
    dom = capture.dom_observation
    if not isinstance(dom, dict):
        return False
    observed_creator = str(dom.get("overlay_creator_handle_or_none") or "").lstrip("@").lower()
    return bool(
        dom.get("video_overlay_detected") is True
        and _non_negative_int_or_zero(dom.get("visible_video_element_count")) > 0
        and str(dom.get("overlay_video_id_or_none") or "") == video_id
        and (not observed_creator or observed_creator == creator_handle.lower())
        and _is_creator_video_url(
            video_url=capture.final_url,
            creator_handle=creator_handle,
            video_id=video_id,
        )
    )


def _video_id_from_url(video_url: str) -> str:
    match = re.match(r"^/@[^/]+/video/(\d+)$", urlparse(video_url).path.rstrip("/"))
    if match is None:
        raise TikTokCreatorOnboardingError("selected video URL has invalid TikTok path")
    return match.group(1)


def _is_any_creator_video_url(video_url: str, creator_handle: str) -> bool:
    try:
        video_id = _video_id_from_url(video_url)
    except TikTokCreatorOnboardingError:
        return False
    return _is_creator_video_url(
        video_url=video_url,
        creator_handle=creator_handle,
        video_id=video_id,
    )


def _is_creator_profile_url(profile_url: str, creator_handle: str) -> bool:
    parsed = urlparse(profile_url)
    host = parsed.hostname.lower() if parsed.hostname else ""
    return bool(
        parsed.scheme in {"http", "https"}
        and (host == "tiktok.com" or host.endswith(".tiktok.com"))
        and parsed.path.rstrip("/").lower()
        == f"/@{_normalize_handle(creator_handle)}".lower()
    )


def _visible_grid_rows_from_capture(
    capture: BrowserPageObservationSuccess,
) -> list[dict[str, Any]]:
    dom = capture.dom_observation
    if not isinstance(dom, dict):
        return []
    rows = dom.get("visible_selected_tiles")
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("video_id"), str)
        and isinstance(row.get("video_url"), str)
    ]


def capture_tiktok_creator_grid(
    *,
    profile_url: str,
    creator_handle: str,
    storage_state_path: Path,
    window_size: int,
    minimum_dom_video_count: int | None = None,
    timeout_seconds: float,
    settle_seconds: float,
    max_grid_scroll_passes: int,
    engine: BrowserPageObservationEngine,
    required_metric_names: Sequence[str] = (),
) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
    """Capture one sufficient grid batch without loading a second batch."""

    del max_grid_scroll_passes

    def observe(
        *,
        pointer_actions: Sequence[BrowserPagePointerAction] = (),
        wheel_action: BrowserPageWheelAction | None = None,
        force_same_url_reload: bool = False,
    ) -> BrowserPageObservationSuccess | BrowserSnapshotFailure:
        return fetch_browser_page_observation_capture(
            url=profile_url,
            dom_extract_script=TIKTOK_PROFILE_GRID_DOM_EXTRACT_SCRIPT,
            dom_extract_arg={"creator_handle": creator_handle},
            response_url_predicate=is_tiktok_profile_item_list_url,
            post_load_pointer_actions=pointer_actions,
            post_load_wheel_action=wheel_action,
            timeout_seconds=timeout_seconds,
            wait_until="domcontentloaded",
            settle_seconds=settle_seconds,
            storage_state_path=storage_state_path,
            headless=False,
            browser_backend=TIKTOK_BROWSER_BACKEND_CHROME_CDP,
            human_challenge_handoff_markers=TIKTOK_CHALLENGE_TEXT_MARKERS,
            human_challenge_handoff_timeout_seconds=180.0,
            human_challenge_handoff_prompt=TIKTOK_HUMAN_CHALLENGE_HANDOFF_PROMPT,
            engine=engine,
            force_same_url_reload=force_same_url_reload,
        )

    initial = observe(pointer_actions=(TIKTOK_RELATIONSHIP_DIALOG_CLOSE_ACTION,))
    if isinstance(initial, BrowserSnapshotFailure):
        return initial
    interaction_context_captures = [initial]
    metric_reload_attempted = False
    metric_reload_recovered = False
    if (
        not _metric_items_from_capture(initial, creator_handle)
        and _non_negative_int_or_zero(
            initial.metadata.get("same_url_navigation_suppression_count")
        )
        > 0
    ):
        metric_reload_attempted = True
        refreshed = observe(force_same_url_reload=True)
        if isinstance(refreshed, BrowserSnapshotFailure):
            return refreshed
        interaction_context_captures.append(refreshed)
        initial = refreshed
        metric_reload_recovered = bool(
            _metric_items_from_capture(initial, creator_handle)
        )
    initial_ids = _ordered_grid_video_ids(initial, creator_handle=creator_handle)

    captures = [initial]
    initial_id_set = set(initial_ids)
    prior_ids = initial_ids
    if minimum_dom_video_count is None:
        minimum_dom_video_count = GRID_ACQUISITION_SUFFICIENT_DOM_VIDEO_COUNT
    if (
        isinstance(minimum_dom_video_count, bool)
        or not isinstance(minimum_dom_video_count, int)
        or minimum_dom_video_count <= 0
        or minimum_dom_video_count > window_size
    ):
        raise TikTokCreatorOnboardingError(
            "minimum_dom_video_count must be between 1 and window_size"
        )
    sufficient_dom_video_count = min(window_size, minimum_dom_video_count)
    initial_window_sufficient = len(initial_ids) >= sufficient_dom_video_count
    required_metrics = _validated_required_grid_metric_names(required_metric_names)
    initial_metrics_sufficient = _grid_metrics_sufficient(
        captures=captures,
        creator_handle=creator_handle,
        ordered_ids=initial_ids,
        window_size=window_size,
        required_metric_names=required_metrics,
    )
    metrics_sufficient = initial_metrics_sufficient
    wheel_burst_count = 0
    if not initial_window_sufficient or not initial_metrics_sufficient:
        for _ in range(GRID_ACQUISITION_BATCH_REVEAL_WHEEL_CAP):
            if not prior_ids:
                raise TikTokCreatorOnboardingError(
                    "one grid DOM batch did not produce the minimum usable window; "
                    "humanized target scroll requires a loaded video anchor"
                )
            target_video_id = prior_ids[-1]
            wheel_capture = observe(
                wheel_action=BrowserPageWheelAction(
                    action_name="tiktok_grid_one_dom_batch_humanized_reveal_v0",
                    direction="down",
                    viewport_fraction_min=GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MIN,
                    viewport_fraction_max=GRID_PAGINATION_WHEEL_VIEWPORT_FRACTION_MAX,
                    target_selector=f"a[href*='/video/{target_video_id}']",
                )
            )
            wheel_burst_count += 1
            if isinstance(wheel_capture, BrowserSnapshotFailure):
                return wheel_capture
            captures.append(wheel_capture)
            interaction_context_captures.append(wheel_capture)
            prior_ids = _ordered_grid_video_ids(
                wheel_capture,
                creator_handle=creator_handle,
            )
            metrics_sufficient = _grid_metrics_sufficient(
                captures=captures,
                creator_handle=creator_handle,
                ordered_ids=(
                    initial_ids if initial_window_sufficient else prior_ids
                ),
                window_size=window_size,
                required_metric_names=required_metrics,
            )
            if (
                initial_window_sufficient
                and metrics_sufficient
            ) or (
                not initial_window_sufficient
                and bool(set(prior_ids) - initial_id_set)
                and metrics_sufficient
            ):
                break
        else:
            if initial_window_sufficient:
                raise TikTokCreatorOnboardingError(
                    "grid engagement metrics remained incomplete after bounded "
                    "humanized item-list pagination"
                )
            raise TikTokCreatorOnboardingError(
                "no new grid DOM batch appeared within bounded humanized target scrolls"
            )

    stable_poll_count = 0
    passive_polls_executed = 0
    for _ in range(GRID_ACQUISITION_STABILITY_POLL_CAP):
        poll = observe()
        passive_polls_executed += 1
        if isinstance(poll, BrowserSnapshotFailure):
            return poll
        captures.append(poll)
        interaction_context_captures.append(poll)
        poll_ids = _ordered_grid_video_ids(poll, creator_handle=creator_handle)
        if poll_ids == prior_ids:
            stable_poll_count += 1
        else:
            stable_poll_count = 0
        prior_ids = poll_ids
        if stable_poll_count == GRID_ACQUISITION_STABILITY_POLL_TARGET:
            break
    if stable_poll_count < GRID_ACQUISITION_STABILITY_POLL_TARGET:
        raise TikTokCreatorOnboardingError(
            "grid DOM did not stabilize after one bounded humanized batch reveal"
        )

    final = captures[-1]
    frozen_dom_capture = initial if initial_window_sufficient else final
    frozen_ids = initial_ids if initial_window_sufficient else prior_ids
    final_id_set = set(prior_ids)
    if len(frozen_ids) < sufficient_dom_video_count:
        raise TikTokCreatorOnboardingError(
            "one grid DOM batch did not produce the minimum usable window"
        )
    combined_responses = [
        response for capture in captures for response in capture.responses
    ]
    wheel_action_receipts = [
        action
        for capture in captures
        for action in [capture.metadata.get("post_load_wheel_action")]
        if isinstance(action, dict)
    ]
    pointer_action_receipts = [
        {
            "capture_index": capture_index,
            **action,
        }
        for capture_index, captured_page in enumerate(interaction_context_captures)
        for action in captured_page.metadata.get("post_load_pointer_actions", ())
        if isinstance(action, dict)
    ]
    page_interaction_context_observations = [
        {
            "capture_index": capture_index,
            **observation,
        }
        for capture_index, captured_page in enumerate(interaction_context_captures)
        for observation in captured_page.metadata.get(
            "page_interaction_context_observations", ()
        )
        if isinstance(observation, dict)
    ]
    metadata = dict(final.metadata)
    metadata.update(
        {
            "grid_acquisition_policy": "sufficient_initial_or_adaptive_first_dom_batch_then_stabilize",
            "grid_acquisition_sufficient_dom_video_count": sufficient_dom_video_count,
            "grid_acquisition_initial_window_sufficient": initial_window_sufficient,
            "grid_acquisition_initial_metrics_sufficient": (
                initial_metrics_sufficient
            ),
            "grid_acquisition_final_metrics_sufficient": metrics_sufficient,
            "grid_acquisition_wheel_burst_cap": GRID_ACQUISITION_BATCH_REVEAL_WHEEL_CAP,
            "grid_acquisition_wheel_burst_count": wheel_burst_count,
            "grid_acquisition_wheel_action_receipts": wheel_action_receipts,
            "grid_acquisition_pointer_action_receipts": pointer_action_receipts,
            "page_interaction_context_observations": (
                page_interaction_context_observations
            ),
            "grid_acquisition_initial_dom_video_count": len(initial_ids),
            "grid_acquisition_final_dom_video_count": len(prior_ids),
            "grid_acquisition_new_dom_video_count": len(final_id_set - initial_id_set),
            "grid_acquisition_new_batch_observed": bool(final_id_set - initial_id_set),
            "grid_acquisition_passive_polls_executed": passive_polls_executed,
            "grid_acquisition_consecutive_stable_polls": stable_poll_count,
            "grid_acquisition_stop_reason": (
                (
                    "initial_sufficient_window_stabilized"
                    if initial_metrics_sufficient
                    else "initial_sufficient_window_metrics_completed"
                )
                if initial_window_sufficient
                else "first_new_dom_batch_stabilized"
            ),
            "lazy_load_scroll_passes_executed": 0,
            "lazy_load_scroll_stop_reason": "not_used_dom_batch_policy",
            "lazy_load_response_stop_condition_configured": False,
            "grid_metric_reload_attempted": metric_reload_attempted,
            "grid_metric_reload_recovered": metric_reload_recovered,
        }
    )
    return BrowserPageObservationSuccess(
        requested_url=final.requested_url,
        final_url=final.final_url,
        title=final.title,
        visible_text=final.visible_text,
        dom_observation=frozen_dom_capture.dom_observation,
        responses=combined_responses,
        metadata=metadata,
        warning_notes=list(dict.fromkeys(note for capture in captures for note in capture.warning_notes)),
        limitation_notes=list(
            dict.fromkeys(note for capture in captures for note in capture.limitation_notes)
        ),
    )


# Compatibility alias for tests and callers that used the pre-public seam.
_capture_creator_grid = capture_tiktok_creator_grid


def build_tiktok_grid_window(
    *,
    creator_handle: str,
    capture: BrowserPageObservationSuccess,
    window_size: int,
    minimum_window_size: int | None = None,
    required_metric_names: Sequence[str] = (),
) -> dict[str, Any]:
    """Freeze up to the cap while requiring enough rows for selection."""

    required_minimum = window_size if minimum_window_size is None else minimum_window_size
    if (
        isinstance(required_minimum, bool)
        or not isinstance(required_minimum, int)
        or required_minimum <= 0
        or required_minimum > window_size
    ):
        raise TikTokCreatorOnboardingError("minimum_window_size must be between 1 and window_size")
    dom = capture.dom_observation
    if not isinstance(dom, dict):
        raise TikTokCreatorOnboardingError("grid DOM observation is not an object")
    ordered_videos = dom.get("ordered_videos")
    if not isinstance(ordered_videos, list):
        raise TikTokCreatorOnboardingError("grid DOM observation lacks ordered_videos")

    metric_items = _metric_items_from_capture(capture, creator_handle)
    profile_metrics = _profile_metrics_from_capture(capture, creator_handle)
    by_id = {str(item["video_id"]): item for item in metric_items}
    frozen: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in ordered_videos:
        if not isinstance(row, dict):
            continue
        video_id = str(row.get("video_id") or "").strip()
        video_url = str(row.get("video_url") or "").strip()
        if (
            not video_id
            or video_id in seen
            or not _is_creator_video_url(
                video_url=video_url,
                creator_handle=creator_handle,
                video_id=video_id,
            )
        ):
            continue
        metric_item = by_id.get(video_id)
        dom_view_count_text = row.get("view_count_text_or_none")
        dom_view_count = _parse_tiktok_compact_count(dom_view_count_text)
        if metric_item is None and dom_view_count is None:
            continue
        item = dict(metric_item or {"video_id": video_id, "stats": {}})
        stats = dict(item.get("stats") or {})
        dom_view_count_used = "playCount" not in stats and dom_view_count is not None
        if dom_view_count_used:
            stats["playCount"] = dom_view_count
        item["stats"] = stats
        item["grid_view_count"] = {
            "raw_text_or_none": dom_view_count_text if isinstance(dom_view_count_text, str) else None,
            "parsed_approximate_count_or_none": dom_view_count,
            "source": "profile_grid_dom_view_count_footer",
            "source_display_precision": "rounded_compact",
            "used_for_play_count": dom_view_count_used,
        }
        seen.add(video_id)
        frozen.append(
            {
                **item,
                "video_url": video_url,
                "pinned_visible": row.get("pinned_visible") is True,
                "visible_in_viewport": row.get("visible_in_viewport") is True,
                "grid_position": _non_negative_int_or_zero(
                    row.get("grid_position")
                ),
            }
        )
        if len(frozen) == window_size:
            break

    if len(frozen) < required_minimum:
        raise TikTokCreatorOnboardingError(
            "usable grid window unavailable: "
            f"required at least {required_minimum}, found {len(frozen)} ordered rows with metrics"
        )
    required_metrics = _validated_required_grid_metric_names(required_metric_names)
    incomplete_rows = [
        {
            "video_id": item["video_id"],
            "missing": [
                metric
                for metric in required_metrics
                if type((item.get("stats") or {}).get(metric)) is not int
            ],
        }
        for item in frozen
    ]
    incomplete_rows = [row for row in incomplete_rows if row["missing"]]
    if incomplete_rows:
        first = incomplete_rows[0]
        raise TikTokCreatorOnboardingError(
            "grid engagement metrics incomplete after bounded response reload: "
            f"{len(incomplete_rows)} of {len(frozen)} rows missing required fields; "
            f"first video_id={first['video_id']} missing={','.join(first['missing'])}"
        )
    receipt = {
        "schema_version": TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION,
        "creator_handle": creator_handle,
        "window_size": len(frozen),
        "window_cap": window_size,
        "minimum_window_size": required_minimum,
        "observed_ordered_video_count": len(ordered_videos),
        "observed_metric_video_count": len(metric_items),
        "complete": True,
        "profile_metric_capture_policy_version": (
            TIKTOK_PROFILE_METRIC_CAPTURE_POLICY_VERSION
        ),
        "profile_metrics": profile_metrics,
        "profile_bio_text_or_none": (
            dom.get("profile_bio_text_or_none").strip()
            if isinstance(dom.get("profile_bio_text_or_none"), str)
            and dom.get("profile_bio_text_or_none").strip()
            else None
        ),
        "profile_bio_status": (
            "observed"
            if dom.get("profile_bio_element_detected") is True
            else "unavailable"
        ),
        "items": frozen,
        "collection_receipt": {
            "capture_timestamp": capture.metadata.get("capture_timestamp"),
            "response_count": len(capture.responses),
            "metric_reload_attempted": capture.metadata.get(
                "grid_metric_reload_attempted"
            ),
            "metric_reload_recovered": capture.metadata.get(
                "grid_metric_reload_recovered"
            ),
            "grid_acquisition_policy": capture.metadata.get("grid_acquisition_policy"),
            "sufficient_dom_video_count": capture.metadata.get(
                "grid_acquisition_sufficient_dom_video_count"
            ),
            "initial_window_sufficient": capture.metadata.get(
                "grid_acquisition_initial_window_sufficient"
            ),
            "initial_dom_video_count": capture.metadata.get(
                "grid_acquisition_initial_dom_video_count"
            ),
            "final_dom_video_count": capture.metadata.get(
                "grid_acquisition_final_dom_video_count"
            ),
            "new_dom_video_count": capture.metadata.get(
                "grid_acquisition_new_dom_video_count"
            ),
            "new_batch_observed": capture.metadata.get(
                "grid_acquisition_new_batch_observed"
            ),
            "wheel_burst_count": capture.metadata.get(
                "grid_acquisition_wheel_burst_count"
            ),
            "wheel_burst_cap": capture.metadata.get(
                "grid_acquisition_wheel_burst_cap"
            ),
            "wheel_action_receipts": capture.metadata.get(
                "grid_acquisition_wheel_action_receipts"
            ),
            "pointer_action_receipts": capture.metadata.get(
                "grid_acquisition_pointer_action_receipts"
            ),
            "page_interaction_context_observations": capture.metadata.get(
                "page_interaction_context_observations"
            ),
            "passive_polls_executed": capture.metadata.get(
                "grid_acquisition_passive_polls_executed"
            ),
            "consecutive_stable_polls": capture.metadata.get(
                "grid_acquisition_consecutive_stable_polls"
            ),
            "stop_reason": capture.metadata.get("grid_acquisition_stop_reason"),
            "legacy_response_target_scroll_used": False,
        },
    }
    assert_no_sensitive_tiktok_material(receipt)
    return receipt


def _build_suggested_accounts_receipt(
    *,
    creator_handle: str,
    capture: BrowserPageObservationSuccess | BrowserSnapshotFailure,
) -> dict[str, Any]:
    if isinstance(capture, BrowserSnapshotFailure):
        return {
            "schema_version": TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION,
            "creator_handle": creator_handle,
            "status": "failed",
            "suggested_accounts": [],
            "suggested_surface_detected": False,
            "suggested_surface_root_count": 0,
            "suggested_profile_anchor_count": 0,
            "profile_bio_text_or_none": None,
            "profile_bio_status": "failed",
            "profile_external_links": [],
            "profile_external_links_status": "failed",
            "failure_kind_or_none": capture.failure_kind.value,
            "outer_ui_route": "unresolved_capture_failure",
            "candidate_profiles_opened": 0,
            "account_mutations_taken": 0,
            "non_claims": ["not an exhaustive suggested-account graph"],
        }
    rows: list[dict[str, Any]] = []
    profile_bio_text_or_none: str | None = None
    profile_bio_element_detected = False
    profile_external_links: list[dict[str, Any]] = []
    suggested_surface_detected = False
    suggested_surface_root_count = 0
    suggested_profile_anchor_count = 0
    relationship_dialog_detected = False
    suggested_tab_detected = False
    dom_route: str | None = None
    if isinstance(capture.dom_observation, dict):
        candidate_rows = capture.dom_observation.get("suggested_accounts")
        if isinstance(candidate_rows, list):
            rows = [row for row in candidate_rows if isinstance(row, dict)]
        raw_profile_bio = capture.dom_observation.get("profile_bio_text_or_none")
        if isinstance(raw_profile_bio, str) and raw_profile_bio.strip():
            profile_bio_text_or_none = raw_profile_bio.strip()
        profile_bio_element_detected = (
            capture.dom_observation.get("profile_bio_element_detected") is True
            or profile_bio_text_or_none is not None
        )
        external_rows = capture.dom_observation.get("profile_external_links")
        if isinstance(external_rows, list):
            profile_external_links = [
                row for row in external_rows if isinstance(row, dict)
            ]
        suggested_surface_detected = (
            capture.dom_observation.get("suggested_surface_detected") is True
        )
        suggested_surface_root_count = _non_negative_int_or_zero(
            capture.dom_observation.get("suggested_surface_root_count")
        )
        suggested_profile_anchor_count = _non_negative_int_or_zero(
            capture.dom_observation.get("suggested_profile_anchor_count")
        )
        relationship_dialog_detected = (
            capture.dom_observation.get("relationship_dialog_detected") is True
        )
        suggested_tab_detected = (
            capture.dom_observation.get("suggested_tab_detected") is True
        )
        raw_dom_route = capture.dom_observation.get("suggested_route")
        if isinstance(raw_dom_route, str) and raw_dom_route:
            dom_route = raw_dom_route
    status = (
        "captured"
        if rows
        else "visible_empty"
        if suggested_surface_detected
        else "not_visible"
    )
    receipt = {
        "schema_version": TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION,
        "creator_handle": creator_handle,
        "status": status,
        "suggested_accounts": rows,
        "suggested_surface_detected": suggested_surface_detected,
        "suggested_surface_root_count": suggested_surface_root_count,
        "suggested_profile_anchor_count": suggested_profile_anchor_count,
        "relationship_dialog_detected": relationship_dialog_detected,
        "suggested_tab_detected": suggested_tab_detected,
        "outer_ui_route": (
            capture.metadata.get("suggested_outer_ui_route")
            or dom_route
            or "not_visible_after_primary_and_fallback"
        ),
        "candidate_profiles_opened": 0,
        "account_mutations_taken": 0,
        "profile_bio_text_or_none": profile_bio_text_or_none,
        "profile_bio_status": (
            "captured"
            if profile_bio_text_or_none is not None
            else "visible_empty"
            if profile_bio_element_detected
            else "not_visible"
        ),
        "profile_external_links": profile_external_links,
        "profile_external_links_status": "captured" if profile_external_links else "none_visible",
        "attempt_receipt": {
            "primary_followers_and_suggested_actions": capture.metadata.get(
                "suggested_primary_pointer_actions",
                capture.metadata.get("post_load_pointer_actions"),
            ),
            "fallback_view_all_actions": capture.metadata.get(
                "suggested_fallback_pointer_actions", []
            ),
            "outer_ui_route": capture.metadata.get("suggested_outer_ui_route"),
            "humanized_pointer_layer": capture.metadata.get(
                "humanized_pointer_layer",
                "cloakbrowser.patch_context(resolve_config('careful'))",
            ),
            "outer_move_steps_semantics": capture.metadata.get(
                "outer_move_steps_semantics",
                "BrowserPagePointerAction routing input; not the internal "
                "CloakBrowser humanized pointer path",
            ),
            "challenge_handoff_attempts": capture.metadata.get(
                "human_challenge_handoff_attempts"
            ),
            "capture_timestamp": capture.metadata.get("capture_timestamp"),
        },
        "non_claims": ["not an exhaustive suggested-account graph"],
    }
    assert_no_sensitive_tiktok_material(receipt)
    return receipt


def _validated_required_grid_metric_names(
    required_metric_names: Sequence[str],
) -> tuple[str, ...]:
    required_metrics = tuple(dict.fromkeys(required_metric_names))
    unsupported_required_metrics = set(required_metrics) - set(
        TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS
    )
    if unsupported_required_metrics:
        raise TikTokCreatorOnboardingError(
            "unsupported required TikTok grid metrics: "
            + ", ".join(sorted(unsupported_required_metrics))
        )
    return required_metrics


def _grid_metrics_sufficient(
    *,
    captures: Sequence[BrowserPageObservationSuccess],
    creator_handle: str,
    ordered_ids: Sequence[str],
    window_size: int,
    required_metric_names: Sequence[str],
) -> bool:
    if not required_metric_names:
        return True
    metric_items = _dedupe_metric_items(
        [
            item
            for capture in captures
            for item in _metric_items_from_capture(capture, creator_handle)
        ]
    )
    by_id = {str(item["video_id"]): item for item in metric_items}
    target_ids = tuple(ordered_ids[:window_size])
    if not target_ids:
        return False
    return all(
        all(
            type((by_id.get(video_id, {}).get("stats") or {}).get(metric_name))
            is int
            for metric_name in required_metric_names
        )
        for video_id in target_ids
    )


def _non_negative_int_or_zero(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _ordered_grid_video_ids(
    capture: BrowserPageObservationSuccess,
    *,
    creator_handle: str,
) -> tuple[str, ...]:
    dom = capture.dom_observation
    if not isinstance(dom, dict):
        return ()
    rows = dom.get("ordered_videos")
    if not isinstance(rows, list):
        return ()
    ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        video_id = str(row.get("video_id") or "").strip()
        video_url = str(row.get("video_url") or "").strip()
        if (
            not video_id
            or video_id in seen
            or not _is_creator_video_url(
                video_url=video_url,
                creator_handle=creator_handle,
                video_id=video_id,
            )
        ):
            continue
        seen.add(video_id)
        ids.append(video_id)
    return tuple(ids)


def _parse_tiktok_compact_count(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    normalized = re.sub(r"\s+", "", value).replace(",", "").upper()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([KMB]?)", normalized)
    if match is None:
        return None
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[
        match.group(2)
    ]
    try:
        count = Decimal(match.group(1)) * multiplier
    except InvalidOperation:
        return None
    return int(count.to_integral_value(rounding=ROUND_HALF_UP))


def _parse_tiktok_exact_count_text(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    normalized = re.sub(r"[\s,]", "", value)
    if not normalized or re.fullmatch(r"\d+", normalized) is None:
        return None
    return int(normalized)


def is_tiktok_profile_item_list_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname.lower() if parsed.hostname else ""
    return (
        parsed.scheme in {"http", "https"}
        and (host == "tiktok.com" or host.endswith(".tiktok.com"))
        and parsed.path.rstrip("/") == "/api/post/item_list"
    )


def _metric_items_from_capture(
    capture: BrowserPageObservationSuccess,
    creator_handle: str,
) -> list[dict[str, Any]]:
    items = _metric_items_from_responses(capture.responses, creator_handle)
    dom = capture.dom_observation
    if isinstance(dom, dict):
        hydration = dom.get("hydration_json_text")
        if isinstance(hydration, str) and hydration.strip():
            try:
                payload = json.loads(hydration)
            except json.JSONDecodeError:
                pass
            else:
                items = _dedupe_metric_items(
                    [*items, *_metric_items_from_payload(payload, creator_handle)]
                )
    return items


def _profile_metrics_from_capture(
    capture: BrowserPageObservationSuccess,
    creator_handle: str,
) -> dict[str, dict[str, Any]]:
    payloads: list[tuple[str, object]] = []
    for response in capture.responses:
        if not response.body_text:
            continue
        try:
            payload = json.loads(response.body_text)
        except json.JSONDecodeError:
            continue
        payloads.append(("profile_item_list_response", payload))
    dom = capture.dom_observation
    if isinstance(dom, dict):
        hydration = dom.get("hydration_json_text")
        if isinstance(hydration, str) and hydration.strip():
            try:
                payloads.insert(0, ("profile_hydration", json.loads(hydration)))
            except json.JSONDecodeError:
                pass

    candidates: dict[str, list[tuple[str, dict[str, Any]]]] = {
        "profile_user_info_stats": [],
        "profile_author_stats": [],
    }
    for source_route, payload in payloads:
        for candidate_kind, stats in _profile_stats_candidates(
            payload,
            creator_handle=creator_handle,
        ):
            candidates[candidate_kind].append((source_route, stats))

    metric_fields = {
        "follower_count": "followerCount",
        "profile_total_like_count": "heartCount",
    }
    cells: dict[str, dict[str, Any]] = {}
    for metric_name, source_field in metric_fields.items():
        cell: dict[str, Any] | None = None
        for candidate_kind in ("profile_user_info_stats", "profile_author_stats"):
            tier = candidates[candidate_kind]
            present = [
                (source_route, stats[source_field])
                for source_route, stats in tier
                if source_field in stats
            ]
            if not present:
                continue
            exact_values = {
                value
                for _source_route, value in present
                if type(value) is int and value >= 0
            }
            if len(exact_values) == 1 and all(
                type(value) is int and value >= 0
                for _source_route, value in present
            ):
                value = next(iter(exact_values))
                cell = _profile_metric_cell(
                    source_field=source_field,
                    exact_value=value,
                    source_route=f"{present[0][0]}:{candidate_kind}",
                    raw_text=str(value),
                )
            elif len(exact_values) > 1:
                cell = _profile_metric_cell(
                    source_field=source_field,
                    reason="conflicting_exact_structured_values",
                    source_route=f"{present[0][0]}:{candidate_kind}",
                )
            else:
                cell = _profile_metric_cell(
                    source_field=source_field,
                    reason="structured_value_not_exact_non_negative_integer",
                    source_route=f"{present[0][0]}:{candidate_kind}",
                    raw_text=str(present[0][1]),
                )
            break
        if cell is None:
            dom_cell = None
            if isinstance(dom, dict):
                dom_metrics = dom.get("profile_metric_dom")
                if isinstance(dom_metrics, dict):
                    candidate = dom_metrics.get(metric_name)
                    if isinstance(candidate, dict):
                        dom_cell = candidate
            raw_text = (
                dom_cell.get("raw_text_or_none")
                if isinstance(dom_cell, dict)
                else None
            )
            exact_value = _parse_tiktok_exact_count_text(raw_text)
            if exact_value is not None:
                cell = _profile_metric_cell(
                    source_field=source_field,
                    exact_value=exact_value,
                    source_route="profile_header_dom_exact_text",
                    raw_text=raw_text,
                )
            else:
                reason = (
                    "profile_count_unavailable"
                    if raw_text in (None, "")
                    else "profile_header_dom_compact_or_non_integer"
                )
                cell = _profile_metric_cell(
                    source_field=source_field,
                    reason=reason,
                    source_route="profile_header_dom",
                    raw_text=raw_text if isinstance(raw_text, str) else None,
                )
        cells[metric_name] = cell
    return cells


def _profile_stats_candidates(
    payload: object,
    *,
    creator_handle: str,
) -> list[tuple[str, dict[str, Any]]]:
    normalized_handle = _normalize_handle(creator_handle)
    found: list[tuple[str, dict[str, Any]]] = []

    def matching_handle(value: object) -> bool:
        return (
            isinstance(value, dict)
            and isinstance(value.get("uniqueId"), str)
            and _normalize_handle(value["uniqueId"]) == normalized_handle
        )

    def visit(node: object) -> None:
        if isinstance(node, list):
            for value in node:
                visit(value)
            return
        if not isinstance(node, dict):
            return
        user_info = node.get("userInfo")
        if isinstance(user_info, dict):
            user = user_info.get("user")
            stats = user_info.get("stats")
            if matching_handle(user) and isinstance(stats, dict):
                found.append(("profile_user_info_stats", stats))
        author = node.get("author")
        author_stats = node.get("authorStats")
        if matching_handle(author) and isinstance(author_stats, dict):
            found.append(("profile_author_stats", author_stats))
        for value in node.values():
            visit(value)

    visit(payload)
    return found


def _profile_metric_cell(
    *,
    source_field: str,
    exact_value: int | None = None,
    reason: str | None = None,
    source_route: str,
    raw_text: str | None = None,
) -> dict[str, Any]:
    observed = exact_value is not None
    return {
        "source_field": source_field,
        "exact_value_or_none": exact_value,
        "posture": "observed" if observed else "unavailable_with_reason",
        "reason_or_none": None if observed else reason,
        "source_route": source_route,
        "raw_text_or_none": raw_text,
    }


def _profile_grid_subtitle_sources_from_capture(
    capture: BrowserPageObservationSuccess,
    *,
    creator_handle: str,
) -> dict[str, dict[str, Any]]:
    """Keep exact-video subtitle URLs in memory for the overlay capture only."""

    payloads: list[object] = []
    for response in capture.responses:
        if not response.body_text:
            continue
        try:
            payloads.append(json.loads(response.body_text))
        except json.JSONDecodeError:
            continue
    dom = capture.dom_observation
    if isinstance(dom, dict):
        hydration = dom.get("hydration_json_text")
        if isinstance(hydration, str) and hydration.strip():
            try:
                payloads.append(json.loads(hydration))
            except json.JSONDecodeError:
                pass

    normalized_handle = _normalize_handle(creator_handle)
    sources: dict[str, dict[str, Any]] = {}

    def consider(item: object) -> None:
        if not isinstance(item, dict):
            return
        raw_id = item.get("id")
        if not isinstance(raw_id, (str, int)):
            return
        author = item.get("author")
        author_handle = (
            str(author.get("uniqueId") or "").lstrip("@").lower()
            if isinstance(author, dict)
            else ""
        )
        if author_handle and author_handle != normalized_handle:
            return
        video = item.get("video")
        if not isinstance(video, dict):
            return
        subtitle_infos = video.get("subtitleInfos", video.get("subtitle_infos"))
        if not isinstance(subtitle_infos, list) or not subtitle_infos:
            return
        video_id = str(raw_id)
        sources.setdefault(
            video_id,
            {
                "id": video_id,
                "video": {"subtitleInfos": list(subtitle_infos)},
            },
        )

    def visit(node: object) -> None:
        if isinstance(node, list):
            for value in node:
                visit(value)
            return
        if not isinstance(node, dict):
            return
        item_list = node.get("itemList")
        if isinstance(item_list, list):
            for item in item_list:
                consider(item)
            for key, value in node.items():
                if key != "itemList":
                    visit(value)
            return
        for value in node.values():
            visit(value)

    for payload in payloads:
        visit(payload)
    return sources


def _metric_items_from_responses(
    responses: Sequence[BrowserPageResponse],
    creator_handle: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for response in responses:
        if not response.body_text:
            continue
        try:
            payload = json.loads(response.body_text)
        except json.JSONDecodeError:
            continue
        items.extend(
            _metric_items_from_payload(
                payload,
                creator_handle,
                source_response_url=response.final_url or response.requested_url,
            )
        )
    return _dedupe_metric_items(items)


def _metric_items_from_payload(
    payload: object,
    creator_handle: str,
    *,
    source_response_url: str | None = None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    normalized_handle = _normalize_handle(creator_handle)

    def consider(node: dict[str, Any]) -> None:
        stats = node.get("stats")
        raw_id = node.get("id")
        if not isinstance(stats, dict) or not isinstance(raw_id, (str, int)):
            return
        author = node.get("author")
        author_handle = (
            str(author.get("uniqueId") or "").lstrip("@").lower()
            if isinstance(author, dict)
            else ""
        )
        if author_handle and author_handle != normalized_handle:
            return

        # Bronze-facing grid evidence preserves every source-present stat and
        # every source-owned row, including a real zero-play row or a row whose
        # ranking metrics are incomplete. Selection eligibility is a separate
        # concern handled by grid_video_selection; dropping the row here would
        # make later longitudinal reconstruction impossible.
        item: dict[str, Any] = {
            "video_id": str(raw_id),
            "stats": dict(stats),
        }
        desc = node.get("desc")
        if isinstance(desc, str):
            item["desc"] = desc
        create_time = node.get("createTime", node.get("create_time"))
        if isinstance(create_time, int) and not isinstance(create_time, bool):
            item["createTime"] = create_time
        if isinstance(author, dict):
            item["author"] = {
                key: author[key]
                for key in ("id", "uid", "uniqueId", "nickname")
                if author.get(key) not in (None, "")
            }
            if author_handle:
                item["authorUniqueId"] = author_handle
        music = node.get("music")
        if isinstance(music, dict):
            item["music"] = {
                key: music[key]
                for key in ("id", "title", "authorName", "duration", "original")
                if music.get(key) is not None
            }
        challenges = node.get("challenges")
        if isinstance(challenges, list):
            item["challenges"] = [
                {
                    key: challenge[key]
                    for key in ("id", "title", "desc")
                    if challenge.get(key) not in (None, "")
                }
                for challenge in challenges
                if isinstance(challenge, dict)
            ]
        if source_response_url:
            parsed_source = urlparse(source_response_url)
            item["source_response_path"] = parsed_source.path
            item["source_response_url_sha256"] = sha256(
                source_response_url.encode("utf-8")
            ).hexdigest()
        item["field_provenance"] = {
            "video_id": "profile_grid_item_response",
            "stats": "profile_grid_item_response_exact_source_values",
            "author": "profile_grid_item_response_when_present",
            "desc": "profile_grid_item_response_when_present",
            "create_time": "profile_grid_item_response_when_present",
            "music": "profile_grid_item_response_when_present",
        }
        # Keep the two incumbent flat fields as compatibility mirrors while the
        # exact source-native stats object is the fidelity-preserving home.
        for key in ("playCount", "diggCount"):
            if key in stats:
                item[key] = stats[key]
        found.append(item)

    def visit(node: object) -> None:
        if isinstance(node, list):
            for value in node:
                visit(value)
            return
        if not isinstance(node, dict):
            return
        item_list = node.get("itemList")
        if isinstance(item_list, list):
            for item in item_list:
                if isinstance(item, dict):
                    consider(item)
            for key, value in node.items():
                if key != "itemList":
                    visit(value)
            return
        consider(node)
        for value in node.values():
            visit(value)

    visit(payload)
    return found


def _notify_progress(
    progress_fn: ProgressFn | None,
    event: str,
    **fields: object,
) -> None:
    if progress_fn is not None:
        progress_fn(event, dict(fields))


def _has_account_safety_stop(cadence_result: object) -> bool:
    if not isinstance(cadence_result, dict):
        return False
    failures = cadence_result.get("failures")
    if not isinstance(failures, list):
        return False
    for failure in failures:
        if not isinstance(failure, dict):
            continue
        triage = failure.get("blocker_triage")
        if isinstance(triage, dict) and triage.get("account_safety_stop") is True:
            return True
    return False


def _dedupe_metric_items(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        video_id = str(item["video_id"])
        if video_id in seen:
            continue
        seen.add(video_id)
        deduped.append(item)
    return deduped


def _is_creator_video_url(
    *,
    video_url: str,
    creator_handle: str,
    video_id: str,
) -> bool:
    parsed = urlparse(video_url)
    host = parsed.hostname.lower() if parsed.hostname else ""
    expected_path = f"/@{_normalize_handle(creator_handle)}/video/{video_id}"
    return (
        parsed.scheme in {"http", "https"}
        and (host == "tiktok.com" or host.endswith(".tiktok.com"))
        and parsed.path.rstrip("/").lower() == expected_path.lower()
    )


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _phase_chronology_row(
    phase: str,
    *,
    run_started_monotonic: float,
    monotonic_fn: MonotonicFn,
    utc_now_fn: UtcNowFn,
) -> dict[str, object]:
    return {
        "phase": phase,
        "observed_at_utc": _utc_iso(utc_now_fn()),
        "elapsed_seconds": round(
            max(0.0, monotonic_fn() - run_started_monotonic), 6
        ),
    }


def _output_paths(output_dir: Path) -> TikTokCreatorOnboardingOutputPaths:
    return TikTokCreatorOnboardingOutputPaths(
        suggested_accounts_json_path=output_dir / TIKTOK_ONBOARDING_SUGGESTED_JSON_NAME,
        grid_window_json_path=output_dir / TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME,
        selection_json_path=output_dir / TIKTOK_ONBOARDING_SELECTION_JSON_NAME,
        live_grid_json_path=output_dir / TIKTOK_LIVE_BATCH_GRID_JSON_NAME,
        live_cadence_json_path=output_dir / TIKTOK_LIVE_BATCH_CADENCE_JSON_NAME,
        onboarding_receipt_json_path=output_dir / TIKTOK_ONBOARDING_RECEIPT_JSON_NAME,
        activity_journal_jsonl_path=output_dir / SOURCE_CAPTURE_ACTIVITY_JSONL_NAME,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    assert_no_sensitive_tiktok_material(payload)
    path.write_bytes(json_dumps_sanitized(payload))


_REGIONAL_INDICATOR_PAIR = re.compile(
    r"[\U0001F1E6-\U0001F1FF]{2}"
)


def assess_tiktok_creator_market(
    *,
    creator_handle: str,
    profile_bio_text_or_none: object,
    profile_bio_status: str,
    source_artifact: str = TIKTOK_ONBOARDING_SUGGESTED_JSON_NAME,
) -> dict[str, Any]:
    """Classify only explicit, same-read profile-bio market evidence.

    The function deliberately ignores TikTok's generic app-context ``region``:
    historical captures show that value identifies the viewing session, not the
    creator. English-language text is likewise not geographic evidence.
    """

    normalized_handle = _normalize_handle(creator_handle)
    bio = (
        profile_bio_text_or_none.strip()
        if isinstance(profile_bio_text_or_none, str)
        and profile_bio_text_or_none.strip()
        else ""
    )
    flag_codes = sorted(
        {
            "".join(chr(ord(char) - 0x1F1E6 + ord("A")) for char in flag)
            for flag in _REGIONAL_INDICATOR_PAIR.findall(bio)
        }
    )
    non_us_flag_codes = [code for code in flag_codes if code != "US"]

    if non_us_flag_codes:
        decision = "deferred_non_us_market"
        reason_code = "non_us_market"
        reconsideration = "new_signal"
    else:
        decision = "passed_no_non_us_evidence"
        reason_code = None
        reconsideration = None

    return {
        "schema_version": TIKTOK_CREATOR_MARKET_ASSESSMENT_SCHEMA_VERSION,
        "creator_handle": normalized_handle,
        "decision": decision,
        "reason_code_or_none": reason_code,
        "reconsideration_or_none": reconsideration,
        "evidence": {
            "source_artifact": source_artifact,
            "source_route": "tiktok_profile_bio_dom_same_read",
            "profile_bio_status": profile_bio_status,
            "country_flag_codes": flag_codes,
        },
        "non_claims": [
            "not proof of creator residence",
            "not audience-geography evidence",
            "no affirmative non-US flag evidence is not proof of a US market",
            "profile language is not geographic evidence",
            "TikTok app-context region is not creator evidence",
        ],
    }


def _normalize_handle(handle: str) -> str:
    normalized = handle.strip().lstrip("@")
    if not normalized or "/" in normalized or "\\" in normalized:
        raise TikTokCreatorOnboardingError(
            "creator_handle must be a non-empty TikTok handle"
        )
    return normalized.lower()


__all__ = [
    "DEFAULT_MAX_GRID_SCROLL_PASSES",
    "DEFAULT_SELECTION_COUNT",
    "DEFAULT_WINDOW_SIZE",
    "TIKTOK_CREATOR_ONBOARDING_SCHEMA_VERSION",
    "TIKTOK_ONBOARDING_GRID_WINDOW_JSON_NAME",
    "TIKTOK_ONBOARDING_RECEIPT_JSON_NAME",
    "TIKTOK_ONBOARDING_SELECTION_JSON_NAME",
    "TIKTOK_ONBOARDING_SUGGESTED_JSON_NAME",
    "TIKTOK_CREATOR_MARKET_ASSESSMENT_SCHEMA_VERSION",
    "TikTokCreatorMarketDeferred",
    "assess_tiktok_creator_market",
    "TIKTOK_GRID_REQUIRED_ENGAGEMENT_METRICS",
    "TikTokCreatorOnboardingError",
    "TikTokCreatorOnboardingOutputPaths",
    "TikTokCreatorProfileRefreshOutputPaths",
    "build_tiktok_grid_window",
    "capture_tiktok_earliest_public_post_observation",
    "capture_tiktok_creator_grid",
    "is_tiktok_profile_item_list_url",
    "run_tiktok_creator_onboarding",
    "run_tiktok_creator_profile_refresh",
]
