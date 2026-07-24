"""Advisory selection helpers for TikTok creator discovery frontier registers.

These helpers are intentionally pure: they read already-built register mappings
and return ranking/overlap views. They do not launch TikTok, write packets,
mutate registers, authorize next runs, or infer creator quality.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from statistics import median
from typing import Any


_WRAPPER_KEY = "tiktok_creator_discovery_frontier_register"
_CANDIDATE_NODE_TYPE = "tiktok_creator_candidate"
_SUGGESTED_EDGE_TYPE = "platform_suggested_account_relation"
_EXPANDED_SECTION_MARKERS = ("view_all", "expanded")
_FRAGRANCE_TOKENS = (
    "frag",
    "fragrance",
    "scent",
    "cologne",
    "parfum",
    "perfume",
    "smell",
    "sniff",
    "nose",
    "oud",
)


TIKTOK_CREATOR_PROMOTION_SCHEMA = "tiktok_creator_promotion_decisions_v1"
_PROMOTION_POLICY = {
    "version": "tiktok_fragrance_creator_promotion_policy_v3",
    "calibration_report_sha256": "14a5a49359a7c70ed0584b61718a80ae5ae946fbd64a3daecc2e7e1f36b388fe",
    "calibration_source_set_sha256": "6d74d4f0c0f1158d4c97c1aa1dc0655bd3363fffa04af42f9d247730db034be4",
    "calibration_cohort_size": 9,
    "calibration_posture": "positive_only_candidate_admitted_excluding_owner_removed_fragrancekyle",
    "cohort_medians": {"0-2d": 5383.25, "3-7d": 6636.0, "8-14d": 7662.0, "15-30d": 11481.5, "31d+": 28600.0},
    "multipliers": {"0-2d": 2.132819, "3-7d": 1.730184, "8-14d": 1.498499, "15-30d": 1.0, "31d+": 0.401451},
    "quality_p25": 4.713114, "quality_median": 5.262225, "quality_p75": 6.808817,
    "weekly_reach_p25": 186641.046627, "weekly_reach_median": 278618.347224, "weekly_reach_p75": 295282.8891,
    "cadence_cap": 10.629303,
}
_OWNER_ONBOARDING_DISPOSITIONS = {
    "eddeparfum": {
        "action": "defer",
        "reason": "owner_observed_non_us",
        "recorded_on": "2026-07-22",
    },
}


def build_tiktok_creator_promotion_decisions(
    grids: Sequence[Mapping[str, Any]], *, sources: Sequence[Mapping[str, Any]] = ()
) -> dict[str, Any]:
    """Return deterministic pre-registry decisions from raw TikTok grids."""
    if not grids or (sources and len(sources) != len(grids)):
        raise ValueError("grids are required and sources must align one-to-one")
    rows, seen = [], set()
    for index, grid in enumerate(grids):
        handle = _clean_handle(grid.get("creator_handle"))
        key = _handle_key(handle)
        if not handle or not key or key in seen:
            raise ValueError(f"invalid or duplicate creator_handle: {handle!r}")
        seen.add(key)
        captured = _utc(_mapping_value(grid, "collection_receipt").get("capture_timestamp"))
        posts = []
        for item in _sequence_value(grid, "items"):
            if not isinstance(item, Mapping) or item.get("pinned_visible") is True:
                continue
            created, stats = item.get("createTime"), item.get("stats")
            if isinstance(created, bool) or not isinstance(created, (int, float)) or not isinstance(stats, Mapping):
                raise ValueError(f"{handle}: unpinned item lacks createTime/stats")
            age = (captured.timestamp() - float(created)) / 86400
            plays = stats.get("playCount")
            if age < 0 or isinstance(plays, bool) or not isinstance(plays, int) or plays < 0:
                raise ValueError(f"{handle}: invalid age/playCount")
            posts.append((float(created), _age_cohort(age), plays))
        if len(posts) < 2:
            raise ValueError(f"{handle}: at least two unpinned posts required")
        ratios = []
        for cohort, baseline in _PROMOTION_POLICY["cohort_medians"].items():
            plays = [post[2] for post in posts if post[1] == cohort]
            if len(plays) >= 3:
                ratios.append(float(median(plays)) / baseline)
        quality = float(median(ratios)) if ratios else None
        normalized = [play * _PROMOTION_POLICY["multipliers"][cohort] for _, cohort, play in posts]
        p25 = _percentile(normalized, .25)
        span = (max(post[0] for post in posts) - min(post[0] for post in posts)) / 86400
        cadence = ((len(posts) - 1) * 7 / span) if span > 0 else 0.0
        weekly = p25 * min(cadence, _PROMOTION_POLICY["cadence_cap"])
        followers = _followers(grid)
        weekly_per_1k = (weekly / (followers / 1000)) if followers else None
        decision = _promotion_decision_fields(
            quality=quality,
            weekly_reach=weekly,
            followers=followers,
            weekly_reach_per_1k_followers=weekly_per_1k,
        )
        promote = decision["registry_action"] == "promote_now"
        reconsider = None if promote else "new_signal_only"
        rows.append({
            "handle": handle, "registry_action": "promote_now" if promote else "do_not_promote",
            "reconsider_when_or_none": reconsider,
            "age_normalized_quality_index_or_none": round(quality, 6) if quality is not None else None,
            "reliable_weekly_reach": round(weekly, 6), "observed_posts_per_week": round(cadence, 6),
            "follower_count_or_none": followers,
            "follower_band": _follower_band(followers),
            "reliable_weekly_reach_per_1k_followers_or_none": round(weekly_per_1k, 6) if weekly_per_1k is not None else None,
            "age_normalized_median_reach_per_follower_or_none": round(float(median(normalized)) / followers, 6) if followers else None,
            "oldest_available_grid_post_utc": datetime.fromtimestamp(min(post[0] for post in posts), tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "oldest_evidence_status": "bounded_grid_proxy_not_oldest_filter",
            "unpinned_post_count": len(posts), "eligible_quality_cohort_count": len(ratios),
            "capture_timestamp_utc": captured.isoformat().replace("+00:00", "Z"),
            "source": dict(sources[index]) if sources else {},
            "decision_reason_code": decision["decision_reason_code"],
            "decision_note": decision["decision_note"],
            "cleared_thresholds": decision["cleared_thresholds"],
        })
    rows.sort(key=lambda row: (row["registry_action"] != "promote_now", -float(row["age_normalized_quality_index_or_none"] or -1), -row["reliable_weekly_reach"], row["handle"].lower()))
    for rank, row in enumerate(rows, 1):
        row["priority_rank"] = rank
    return {"tiktok_creator_promotion_decisions": {
        "schema_version": TIKTOK_CREATOR_PROMOTION_SCHEMA, "policy": dict(_PROMOTION_POLICY),
        "decisions": rows, "counts": {"creators": len(rows), "promote_now": sum(row["registry_action"] == "promote_now" for row in rows)},
        "non_claims": ["not Creator Registry or onboarding proof", "reach is play count, not unique people", "bounded oldest grid post is not account-age proof"],
    }}


def _promotion_decision_fields(
    *,
    quality: float | None,
    weekly_reach: float,
    followers: int | None,
    weekly_reach_per_1k_followers: float | None,
) -> dict[str, Any]:
    quality_cleared = (
        quality is not None and quality >= _PROMOTION_POLICY["quality_p25"]
    )
    weekly_cleared = weekly_reach >= _PROMOTION_POLICY["weekly_reach_p25"]
    cleared = [
        name
        for name, passed in (
            ("quality_p25", quality_cleared),
            ("weekly_reach_p25", weekly_cleared),
        )
        if passed
    ]
    if quality_cleared and weekly_cleared:
        reason = "cleared_both_p25"
    elif quality_cleared:
        reason = "cleared_quality_p25"
    elif weekly_cleared:
        reason = "cleared_weekly_reach_p25"
    elif quality is None:
        reason = "quality_unavailable_weekly_below_p25"
    else:
        reason = "below_both_p25"
    action = "promote_now" if cleared else "do_not_promote"
    quality_text = "unavailable" if quality is None else f"{quality:.6f}"
    followers_text = "unavailable" if followers is None else str(followers)
    weekly_per_1k_text = (
        "unavailable"
        if weekly_reach_per_1k_followers is None
        else f"{weekly_reach_per_1k_followers:.6f}"
    )
    note = (
        f"policy={_PROMOTION_POLICY['version']}; decision={action}; "
        f"quality={quality_text}; quality_p25={_PROMOTION_POLICY['quality_p25']:.8f}; "
        f"reliable_weekly_reach={weekly_reach:.6f}; "
        f"weekly_reach_p25={_PROMOTION_POLICY['weekly_reach_p25']:.6f}; "
        f"followers={followers_text}; "
        f"follower_band={_follower_band(followers)}; "
        f"weekly_reach_per_1k_followers={weekly_per_1k_text}; "
        f"cleared={','.join(cleared) if cleared else 'none'}; "
        f"reconsider={'none' if cleared else 'new_signal'}"
    )
    return {
        "registry_action": action,
        "decision_reason_code": reason,
        "decision_note": note,
        "cleared_thresholds": cleared,
    }


def promotion_decision_for_handle(document: Mapping[str, Any], handle: str) -> Mapping[str, Any] | None:
    wrapper = document.get("tiktok_creator_promotion_decisions")
    if not isinstance(wrapper, Mapping) or wrapper.get("schema_version") != TIKTOK_CREATOR_PROMOTION_SCHEMA:
        raise ValueError("unsupported TikTok promotion decisions")
    matches = [row for row in wrapper.get("decisions", []) if isinstance(row, Mapping) and _handle_key(row.get("handle")) == _handle_key(handle)]
    if len(matches) > 1:
        raise ValueError(f"duplicate promotion decision for {handle}")
    return matches[0] if matches else None


def apply_tiktok_creator_onboarding_dedupe(
    document: Mapping[str, Any],
    *,
    registry_states: Mapping[str, str],
    frontier_registers: Sequence[Mapping[str, Any]] = (),
    frontier_dispositions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Annotate promotion results with the live Registry/Frontier action gate.

    Performance decisions remain unchanged. Only Registry ``not_onboarded``
    accounts without a current deferred/rejected disposition are actionable.
    """
    wrapper = document.get("tiktok_creator_promotion_decisions")
    if not isinstance(wrapper, Mapping) or wrapper.get("schema_version") != TIKTOK_CREATOR_PROMOTION_SCHEMA:
        raise ValueError("unsupported TikTok promotion decisions")
    normalized_states = {
        key: state
        for handle, state in registry_states.items()
        if (key := _handle_key(handle)) is not None
    }
    invalid_states = sorted(
        {state for state in normalized_states.values() if state not in {"onboarded", "not_onboarded"}}
    )
    if invalid_states:
        raise ValueError(f"invalid Creator Registry onboarding states: {invalid_states}")
    _, scanned_root_keys = _collect_candidate_records(frontier_registers)
    disposition_by_handle: dict[str, dict[str, Any]] = {}
    if frontier_dispositions is not None:
        disposition_wrapper = frontier_dispositions.get("creator_frontier_disposition_current")
        if not isinstance(disposition_wrapper, Mapping) or disposition_wrapper.get(
            "schema_version"
        ) != "creator_frontier_disposition_current_v1":
            raise ValueError("unsupported Creator Frontier disposition current view")
        raw_dispositions = disposition_wrapper.get("dispositions")
        if not isinstance(raw_dispositions, list):
            raise ValueError("Creator Frontier disposition current view requires dispositions")
        for raw in raw_dispositions:
            if not isinstance(raw, Mapping):
                raise ValueError("Creator Frontier disposition rows must be objects")
            key = _handle_key(raw.get("public_handle"))
            if (
                key is None
                or key in disposition_by_handle
                or raw.get("status") not in {"eligible", "deferred", "rejected"}
            ):
                raise ValueError("duplicate or invalid Creator Frontier disposition handle")
            disposition_by_handle[key] = dict(raw)

    result = {"tiktok_creator_promotion_decisions": dict(wrapper)}
    result_wrapper = result["tiktok_creator_promotion_decisions"]
    rows: list[dict[str, Any]] = []
    actionable_handles: list[str] = []
    for source_row in wrapper.get("decisions", []):
        if not isinstance(source_row, Mapping):
            raise ValueError("promotion decision rows must be objects")
        row = dict(source_row)
        handle = _clean_handle(row.get("handle"))
        handle_key = _handle_key(handle)
        if not handle or not handle_key:
            raise ValueError("promotion decision handle is required")
        registry_state = normalized_states.get(handle_key)
        owner_disposition = disposition_by_handle.get(handle_key)
        legacy_disposition = (
            _OWNER_ONBOARDING_DISPOSITIONS.get(handle_key)
            if owner_disposition is None
            else None
        )
        if registry_state == "onboarded":
            queue_status = "already_onboarded"
        elif owner_disposition is not None and owner_disposition.get("status") == "deferred":
            queue_status = "owner_deferred"
        elif owner_disposition is not None and owner_disposition.get("status") == "rejected":
            queue_status = "owner_rejected"
        elif legacy_disposition is not None:
            queue_status = "owner_deferred"
        elif registry_state == "not_onboarded":
            queue_status = "known_not_onboarded"
        elif owner_disposition is not None and owner_disposition.get("status") == "eligible":
            queue_status = "frontier_eligible_not_registered"
        elif handle_key in scanned_root_keys:
            queue_status = "already_scanned_frontier"
        else:
            queue_status = "new_candidate"
        actionable = (
            row.get("registry_action") == "promote_now"
            and queue_status == "known_not_onboarded"
        )
        row["onboarding_queue_status"] = queue_status
        row["owner_onboarding_disposition_or_none"] = (
            dict(owner_disposition)
            if owner_disposition is not None
            else (dict(legacy_disposition) if legacy_disposition is not None else None)
        )
        row["actionable_promote_now"] = actionable
        rows.append(row)
        if actionable:
            actionable_handles.append(handle)

    result_wrapper["decisions"] = rows
    original_counts = wrapper.get("counts")
    counts = dict(original_counts) if isinstance(original_counts, Mapping) else {}
    counts["actionable_promote_now"] = len(actionable_handles)
    counts["owner_deferred_promote_now"] = sum(
        row.get("registry_action") == "promote_now"
        and row["onboarding_queue_status"] == "owner_deferred"
        for row in rows
    )
    counts["owner_rejected_promote_now"] = sum(
        row.get("registry_action") == "promote_now"
        and row["onboarding_queue_status"] == "owner_rejected"
        for row in rows
    )
    counts["frontier_eligible_not_registered_promote_now"] = sum(
        row.get("registry_action") == "promote_now"
        and row["onboarding_queue_status"] == "frontier_eligible_not_registered"
        for row in rows
    )
    counts["already_onboarded_promote_now"] = sum(
        row.get("registry_action") == "promote_now"
        and row["onboarding_queue_status"] == "already_onboarded"
        for row in rows
    )
    counts["already_scanned_frontier_promote_now"] = sum(
        row.get("registry_action") == "promote_now"
        and row["onboarding_queue_status"] == "already_scanned_frontier"
        for row in rows
    )
    result_wrapper["counts"] = counts
    result_wrapper["actionable_promote_now_handles"] = actionable_handles
    return result


def _utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("capture_timestamp must be ISO-8601 text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("capture_timestamp requires timezone")
    return parsed.astimezone(timezone.utc)


def _age_cohort(age: float) -> str:
    return "0-2d" if age < 3 else "3-7d" if age < 8 else "8-14d" if age < 15 else "15-30d" if age < 31 else "31d+"


def _percentile(values: Sequence[float], q: float) -> float:
    ordered, position = sorted(float(value) for value in values), (len(values) - 1) * q
    low, fraction = int(position), position - int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def _followers(grid: Mapping[str, Any]) -> int | None:
    metrics = grid.get("profile_metrics")
    follower = metrics.get("follower_count") if isinstance(metrics, Mapping) else None
    value = follower.get("exact_value_or_none") if isinstance(follower, Mapping) else None
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _follower_band(followers: int | None) -> str:
    if followers is None:
        return "unknown"
    if followers < 10_000:
        return "under_10k"
    if followers < 50_000:
        return "10k_50k"
    if followers < 250_000:
        return "50k_250k"
    return "250k_plus"


def rank_tiktok_creator_discovery_targets(
    registers: Sequence[Mapping[str, Any]],
    *,
    already_scanned_handles: Sequence[str] = (),
    exclude_root_seed_handles: bool = True,
) -> list[dict[str, Any]]:
    """Return an advisory next-target ranking from existing frontier registers.

    The rank is built from weak suggested-account edges only. It intentionally
    favors once-only, expanded-surface, fragrance-like candidates and
    deprioritizes repeated hubs. It is not a capture authorization, registry
    decision, metric, or creator-quality score.
    """
    records, root_handle_keys = _collect_candidate_records(registers)
    excluded = {_handle_key(handle) for handle in already_scanned_handles}
    excluded.discard(None)
    if exclude_root_seed_handles:
        excluded.update(root_handle_keys)

    ranked: list[dict[str, Any]] = []
    for handle_key, record in records.items():
        if handle_key in excluded:
            continue
        frequency = len(record["observed_from_root_keys"])
        expanded = _has_expanded_section(record["observed_sections"])
        fragrance_like = _is_fragrance_like(record["handle"], record["display_name_or_none"])
        tier = _recommendation_tier(frequency, expanded, fragrance_like)
        score = _score_candidate(frequency, expanded, fragrance_like)
        ranked.append(
            {
                "handle": record["handle"],
                "display_name_or_none": record["display_name_or_none"],
                "source_url_or_locator": record["source_url_or_locator"],
                "prior_suggested_frequency": frequency,
                "observed_from_roots": sorted(record["observed_from_roots"]),
                "observed_sections": sorted(record["observed_sections"]),
                "is_once_only": frequency == 1,
                "is_expanded_tail_observed": expanded,
                "fragrance_handle_or_name_match": fragrance_like,
                "score": score,
                "recommendation_tier": tier,
                "selection_rationale": _selection_rationale(
                    frequency=frequency,
                    expanded=expanded,
                    fragrance_like=fragrance_like,
                ),
            }
        )

    ranked.sort(
        key=lambda item: (
            _tier_sort_key(str(item["recommendation_tier"])),
            -int(item["score"]),
            int(item["prior_suggested_frequency"]),
            str(item["handle"]).lower(),
        )
    )
    return ranked


def summarize_tiktok_creator_discovery_overlap(
    *,
    prior_registers: Sequence[Mapping[str, Any]],
    current_register: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarize how a new register overlaps with prior frontier registers."""
    prior_records, _ = _collect_candidate_records(prior_registers)
    current_records, _ = _collect_candidate_records((current_register,))

    repeated_prior_2plus: list[str] = []
    prior_once_now_repeated: list[str] = []
    brand_new_tail: list[str] = []
    seen_before = 0

    for handle_key, record in current_records.items():
        prior = prior_records.get(handle_key)
        handle = record["handle"]
        if prior is None:
            brand_new_tail.append(handle)
            continue
        seen_before += 1
        prior_frequency = len(prior["observed_from_root_keys"])
        if prior_frequency >= 2:
            repeated_prior_2plus.append(handle)
        elif prior_frequency == 1:
            prior_once_now_repeated.append(handle)

    current_count = len(current_records)
    return {
        "current_root_handle": _current_root_handle(current_register),
        "current_candidate_count": current_count,
        "seen_before_count": seen_before,
        "not_seen_before_count": current_count - seen_before,
        "repeated_prior_2plus": sorted(repeated_prior_2plus, key=str.lower),
        "prior_once_now_repeated": sorted(prior_once_now_repeated, key=str.lower),
        "brand_new_tail": sorted(brand_new_tail, key=str.lower),
        "non_claims": [
            "overlap summary is not creator quality",
            "overlap summary is not capture authorization",
            "overlap summary is not registry identity proof",
        ],
    }


def _collect_candidate_records(
    registers: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    records: dict[str, dict[str, Any]] = {}
    root_handle_keys: set[str] = set()

    for register in registers:
        wrapper = _register_wrapper(register)
        root_handle = _clean_handle(_mapping_value(wrapper, "root_seed").get("handle"))
        root_handle_key = _handle_key(root_handle)
        if root_handle_key:
            root_handle_keys.add(root_handle_key)

        nodes = _sequence_value(wrapper, "nodes")
        edges = _sequence_value(wrapper, "edges")
        node_by_id = {
            str(node["node_id"]): node
            for node in nodes
            if isinstance(node, Mapping) and isinstance(node.get("node_id"), str)
        }
        candidates_by_id = {
            node_id: node
            for node_id, node in node_by_id.items()
            if node.get("node_type") == _CANDIDATE_NODE_TYPE
            and _handle_key(node.get("handle_or_none"))
        }
        observed_via_suggested_edge: set[str] = set()

        for edge in edges:
            if not isinstance(edge, Mapping) or edge.get("edge_type") != _SUGGESTED_EDGE_TYPE:
                continue
            candidate = candidates_by_id.get(str(edge.get("to_node_id")))
            if candidate is None:
                continue
            from_node = node_by_id.get(str(edge.get("from_node_id")), {})
            observed_root = _clean_handle(from_node.get("handle_or_none")) or root_handle
            sections = _string_values(edge.get("observed_sections"))
            handle_key = _upsert_candidate_record(records, candidate, observed_root, sections)
            if handle_key:
                observed_via_suggested_edge.add(handle_key)

        for candidate in candidates_by_id.values():
            handle_key = _handle_key(candidate.get("handle_or_none"))
            if handle_key and handle_key not in observed_via_suggested_edge:
                _upsert_candidate_record(records, candidate, root_handle, ())

    return records, root_handle_keys


def _upsert_candidate_record(
    records: dict[str, dict[str, Any]],
    candidate: Mapping[str, Any],
    observed_root: str | None,
    sections: Sequence[str],
) -> str | None:
    handle = _clean_handle(candidate.get("handle_or_none"))
    handle_key = _handle_key(handle)
    if not handle or not handle_key:
        return None

    record = records.setdefault(
        handle_key,
        {
            "handle": handle,
            "display_name_or_none": _optional_text(candidate.get("display_name_or_none")),
            "source_url_or_locator": _optional_text(candidate.get("source_url_or_locator")),
            "observed_from_roots": set(),
            "observed_from_root_keys": set(),
            "observed_sections": set(),
        },
    )
    if record["display_name_or_none"] is None:
        record["display_name_or_none"] = _optional_text(candidate.get("display_name_or_none"))
    if record["source_url_or_locator"] is None:
        record["source_url_or_locator"] = _optional_text(candidate.get("source_url_or_locator"))

    root_key = _handle_key(observed_root)
    if observed_root and root_key:
        record["observed_from_roots"].add(observed_root)
        record["observed_from_root_keys"].add(root_key)
    record["observed_sections"].update(sections)
    return handle_key


def _register_wrapper(register: Mapping[str, Any]) -> Mapping[str, Any]:
    wrapper = register.get(_WRAPPER_KEY)
    if isinstance(wrapper, Mapping):
        return wrapper
    if isinstance(register.get("nodes"), Sequence) and isinstance(register.get("edges"), Sequence):
        return register
    raise ValueError(f"{_WRAPPER_KEY} wrapper is required")


def _mapping_value(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return item


def _sequence_value(value: Mapping[str, Any], key: str) -> Sequence[Any]:
    item = value.get(key)
    if not isinstance(item, Sequence) or isinstance(item, (str, bytes, bytearray)):
        raise ValueError(f"{key} must be a sequence")
    return item


def _current_root_handle(register: Mapping[str, Any]) -> str | None:
    wrapper = _register_wrapper(register)
    return _clean_handle(_mapping_value(wrapper, "root_seed").get("handle"))


def _has_expanded_section(sections: set[str]) -> bool:
    lowered = [section.lower() for section in sections]
    return any(marker in section for marker in _EXPANDED_SECTION_MARKERS for section in lowered)


def _is_fragrance_like(handle: str, display_name: str | None) -> bool:
    haystack = f"{handle} {display_name or ''}".lower()
    return any(token in haystack for token in _FRAGRANCE_TOKENS)


def _recommendation_tier(frequency: int, expanded: bool, fragrance_like: bool) -> str:
    if frequency >= 3:
        return "deprioritize_repeated_hub"
    if frequency == 1 and (expanded or fragrance_like):
        return "prioritize"
    return "consider"


def _score_candidate(frequency: int, expanded: bool, fragrance_like: bool) -> int:
    if frequency <= 0:
        score = 0
    elif frequency == 1:
        score = 40
    elif frequency == 2:
        score = 15
    else:
        score = -25 - ((frequency - 3) * 5)
    if expanded:
        score += 20
    if fragrance_like:
        score += 15
    return score


def _selection_rationale(*, frequency: int, expanded: bool, fragrance_like: bool) -> str:
    reasons: list[str] = []
    if frequency == 1:
        reasons.append("seen from one scanned root, reducing duplicate graphing")
    elif frequency >= 3:
        reasons.append(f"seen from {frequency} scanned roots, so it may be a repeated hub")
    else:
        reasons.append(f"seen from {frequency} scanned roots")
    if expanded:
        reasons.append("observed on an expanded suggested surface")
    if fragrance_like:
        reasons.append("handle or display name contains a fragrance token")
    return "; ".join(reasons)


def _tier_sort_key(tier: str) -> int:
    order = {
        "prioritize": 0,
        "consider": 1,
        "deprioritize_repeated_hub": 2,
    }
    return order.get(tier, 3)


def _clean_handle(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    handle = value.strip().lstrip("@").strip()
    return handle or None


def _handle_key(value: Any) -> str | None:
    handle = _clean_handle(value)
    return handle.lower() if handle else None


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_values(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(str(item) for item in value if str(item).strip())
