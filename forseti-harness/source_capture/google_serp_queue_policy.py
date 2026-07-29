"""Fail-closed query and block-transition policy for Google SERP queues."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Mapping


BlockRoute = Literal[
    "primary_route",
    "persistent_realchrome",
    "paused_fallback_unavailable",
    "stopped_for_cooldown",
]

_EDITORIAL_FRAGMENT = re.compile(
    r"^(?:good|bad|benefits?|better,\s*)$|"
    r"^\d+(?:\s|$)|"
    r"\breddit[- ]picked\b|"
    r"^(?:i|we|you|they|he|she)\s+",
    re.IGNORECASE,
)
_SENTENCE_DEBRIS = re.compile(r"(?:\.\s*\d|\bwhy\b|[?!].+\w)", re.IGNORECASE)


@dataclass(frozen=True)
class QueueEligibility:
    eligible: bool
    reason: str | None


@dataclass(frozen=True)
class BlockRecoveryDecision:
    route: BlockRoute
    reason: str


def competitor_name_problem(name: str | None) -> str | None:
    """Return a stable quarantine reason for obvious parser/title debris."""
    value = re.sub(r"\s+", " ", str(name or "")).strip()
    if not value:
        return "missing_competitor_name"
    if _EDITORIAL_FRAGMENT.search(value) or _SENTENCE_DEBRIS.search(value):
        return "obvious_parser_or_editorial_fragment"
    return None


def build_product_scoped_price_query(*, name: str, product_scope: str) -> str:
    """Build J5 input without collapsing a multi-product brand to `name price`."""
    clean_name = re.sub(r"\s+", " ", name).strip()
    clean_scope = re.sub(r"\s+", " ", product_scope).strip()
    if not clean_name:
        raise ValueError("competitor name is required")
    if not clean_scope:
        raise ValueError("product_scope is required for competitor J5 queries")
    return f"{clean_name} {clean_scope} price"


def evaluate_queue_job(job: Mapping[str, object]) -> QueueEligibility:
    """Gate a generated competitor job before it can spend egress."""
    if job.get("selected_type") in {"subject", "return_leg"}:
        return QueueEligibility(True, None)
    if job.get("selected_rung") == "presence":
        return QueueEligibility(False, "presence_rung_is_cite_only")
    name_problem = competitor_name_problem(str(job.get("selected_name") or ""))
    if name_problem:
        return QueueEligibility(False, name_problem)
    if str(job.get("shape") or "").startswith("j5_competitor_price"):
        explicitly_scoped = bool(job.get("product_scope")) or bool(
            job.get("product_scoped_query")
        )
        curated_override = job.get("curation_action") == "query_override"
        if not (explicitly_scoped or curated_override):
            return QueueEligibility(False, "competitor_price_query_not_product_scoped")
    return QueueEligibility(True, None)


def decide_block_recovery(
    *,
    lower_route_blocked: bool,
    realchrome_fallback_enabled: bool,
    dedicated_logged_out_cdp_ready: bool,
    operator_visible: bool,
) -> BlockRecoveryDecision:
    """Choose the only allowed next route after a lower-route Google block."""
    if not lower_route_blocked:
        return BlockRecoveryDecision("primary_route", "no lower-route block")
    if not realchrome_fallback_enabled:
        return BlockRecoveryDecision(
            "stopped_for_cooldown",
            "fallback is not enabled; preserve the block packet and stop the stream",
        )
    if not dedicated_logged_out_cdp_ready or not operator_visible:
        return BlockRecoveryDecision(
            "paused_fallback_unavailable",
            "persistent fallback requires a dedicated logged-out operator-visible Chrome",
        )
    return BlockRecoveryDecision(
        "persistent_realchrome",
        "preserve the lower-route block, then resume the exact held job in one persistent tab",
    )
