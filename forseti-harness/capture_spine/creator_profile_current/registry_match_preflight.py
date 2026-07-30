"""Preflight candidate creator/account matches against creator_profile_current.

This module is the deterministic turnstile between discovery and capture. It
does exact registry checks only; fuzzy identity resolution and cross-platform
creator linkage remain separate owner-reviewed workflows.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from capture_spine.creator_profile_current.validation import load_creator_profile_current_view


CANDIDATE_SCHEMA_VERSION = "creator_registry_match_preflight_candidates_v0"
RECEIPT_SCHEMA_VERSION = "creator_registry_match_preflight_receipt_v0"
CANDIDATES_WRAPPER_KEY = "creator_registry_match_preflight_candidates"
RECEIPT_WRAPPER_KEY = "creator_registry_match_preflight_receipt"

_VIEW_WRAPPER_KEY = "creator_profile_current_view"
_ALLOWED_CANDIDATE_KEYS = frozenset(
    {
        "candidate_id",
        "platform",
        "handle_or_url",
        "public_handle_or_none",
        "public_profile_url_or_none",
        "platform_account_id_or_none",
        "profile_subject_id_or_none",
        "platform_public_account_id_or_none",
        "display_name_or_none",
        "source_url_or_none",
        "intended_action",
    }
)
_ALLOWED_INTENDED_ACTIONS = frozenset({"classify", "new_capture", "update_existing"})
_ALLOWED_PLATFORMS = frozenset({"instagram", "tiktok", "youtube"})


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def load_creator_registry_match_candidates(path: str | Path) -> list[Any]:
    document = load_json(path)
    if CANDIDATES_WRAPPER_KEY in document:
        wrapper = document[CANDIDATES_WRAPPER_KEY]
        if not isinstance(wrapper, Mapping):
            raise ValueError(f"{CANDIDATES_WRAPPER_KEY} wrapper must be an object")
        if wrapper.get("schema_version") != CANDIDATE_SCHEMA_VERSION:
            raise ValueError("unexpected creator registry match candidate schema_version")
        candidates = wrapper.get("candidates")
    else:
        candidates = document.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate document must carry a non-empty candidates list")
    return list(candidates)


def dump_creator_registry_match_preflight_receipt(document: Mapping[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def build_creator_registry_match_preflight_receipt_from_files(
    *,
    candidate_path: str | Path,
    registry_path: str | Path,
    generated_at_utc: str,
) -> dict[str, Any]:
    registry_path = Path(registry_path)
    registry_document = load_creator_profile_current_view(registry_path)
    candidates = load_creator_registry_match_candidates(candidate_path)
    return build_creator_registry_match_preflight_receipt(
        candidates=candidates,
        registry_document=registry_document,
        registry_source_pointer=str(registry_path),
        registry_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        generated_at_utc=generated_at_utc,
    )


def build_creator_registry_match_preflight_receipt(
    *,
    candidates: Sequence[Any],
    registry_document: Mapping[str, Any],
    registry_source_pointer: str,
    registry_sha256: str,
    generated_at_utc: str,
) -> dict[str, Any]:
    if not candidates:
        raise ValueError("at least one candidate is required")
    wrapper = _require_mapping(registry_document.get(_VIEW_WRAPPER_KEY), _VIEW_WRAPPER_KEY)
    profiles = wrapper.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("registry document profiles must be a list")

    registry_index = _build_registry_index(profiles)
    normalized = [_normalize_candidate_row(candidate, index) for index, candidate in enumerate(candidates)]
    duplicate_candidate_keys = _duplicate_candidate_keys(normalized)
    results = [
        _build_candidate_result(
            candidate=entry,
            registry_index=registry_index,
            duplicate_keys=duplicate_candidate_keys.get(entry["candidate_id"], []),
        )
        for entry in normalized
    ]
    summary = _summarize_results(results)
    return {
        RECEIPT_WRAPPER_KEY: {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "generated_at_utc": _non_empty_str(generated_at_utc, "generated_at_utc"),
            "registry_source": {
                "source_pointer": _non_empty_str(registry_source_pointer, "registry_source_pointer"),
                "sha256": _non_empty_str(registry_sha256, "registry_sha256"),
                "schema_version": wrapper.get("schema_version"),
                "generated_at_utc": wrapper.get("generated_at_utc"),
                "profiles_total": wrapper.get("counts", {}).get("profiles_total"),
            },
            "summary": summary,
            "results": results,
            "accepted_residuals": [
                "Exact preflight does not perform fuzzy display-name matching.",
                "Exact preflight does not prove cross-platform creator identity.",
                "Exact preflight does not prove discovery search quality.",
                "Exact preflight does not refresh silver metrics or mutate capture outputs.",
            ],
            "non_claims": [
                "not fuzzy identity resolver",
                "not cross-platform linkage proof",
                "not capture authorization without receipt review",
                "not registry mutation",
                "not live social search",
                "not silver metric refresh",
            ],
        }
    }


def has_blocking_preflight_results(receipt: Mapping[str, Any]) -> bool:
    wrapper = _require_mapping(receipt.get(RECEIPT_WRAPPER_KEY), RECEIPT_WRAPPER_KEY)
    return bool(wrapper.get("summary", {}).get("blocked_actions"))


def _build_registry_index(profiles: Sequence[Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for profile in profiles:
        profile_map = _require_mapping(profile, "profile")
        profile_subject_id = _non_empty_str(profile_map.get("profile_subject_id"), "profile_subject_id")
        profile_subject_kind = _non_empty_str(profile_map.get("profile_subject_kind"), "profile_subject_kind")
        accounts = profile_map.get("platform_accounts")
        if not isinstance(accounts, list):
            raise ValueError("registry profile platform_accounts must be a list")
        for account in accounts:
            account_map = _require_mapping(account, "platform_account")
            platform = _normalize_platform(account_map.get("platform"))
            platform_account_id = _non_empty_str(account_map.get("platform_account_id"), "platform_account_id")
            public_handle = _non_empty_str(account_map.get("public_handle"), "public_handle")
            public_profile_url = _non_empty_str(account_map.get("public_profile_url"), "public_profile_url")
            match = {
                "profile_subject_kind": profile_subject_kind,
                "profile_subject_id": profile_subject_id,
                "platform_account_id": platform_account_id,
                "platform": platform,
                "public_handle": public_handle,
                "public_profile_url": public_profile_url,
                "platform_public_account_id_or_none": _optional_str(
                    account_map.get("platform_public_account_id_or_none")
                ),
                "public_display_name_or_none": _optional_str(account_map.get("public_display_name_or_none")),
            }
            for key, _reason in _registry_identity_keys(match):
                index[key].append(match)
    return dict(index)


def _registry_identity_keys(match: Mapping[str, Any]) -> list[tuple[str, str]]:
    platform = _non_empty_str(match.get("platform"), "platform")
    keys = [
        (f"profile_subject_id:{match['profile_subject_id']}", "profile_subject_id"),
        (f"platform_account_id:{match['platform_account_id']}", "platform_account_id"),
        (f"platform_handle:{platform}:{_normalize_handle(match['public_handle'])}", "same_platform_public_handle"),
        (f"profile_url:{_normalize_url(match['public_profile_url'])}", "public_profile_url"),
    ]
    display_name = _optional_str(match.get("public_display_name_or_none"))
    if display_name:
        keys.append(
            (
                f"platform_display_name:{platform}:{_normalize_display_name(display_name)}",
                "same_platform_exact_display_name",
            )
        )
    platform_public_id = _optional_str(match.get("platform_public_account_id_or_none"))
    if platform_public_id:
        keys.append((f"platform_public_account_id:{platform}:{platform_public_id}", "platform_public_account_id"))
    return keys


def _normalize_candidate_row(candidate: Any, index: int) -> dict[str, Any]:
    try:
        candidate_map = _require_mapping(candidate, "candidate")
        return _normalize_candidate(candidate_map, index)
    except ValueError as exc:
        return _invalid_candidate_shape(candidate, index, str(exc))


def _invalid_candidate_shape(candidate: Any, index: int, message: str) -> dict[str, Any]:
    candidate_map = candidate if isinstance(candidate, Mapping) else {}
    raw_candidate_id = candidate_map.get("candidate_id")
    candidate_id = (
        raw_candidate_id.strip()
        if isinstance(raw_candidate_id, str) and raw_candidate_id.strip()
        else f"candidate_index_{index}"
    )
    raw_intended_action = candidate_map.get("intended_action")
    intended_action = (
        raw_intended_action.strip()
        if isinstance(raw_intended_action, str) and raw_intended_action.strip() in _ALLOWED_INTENDED_ACTIONS
        else "classify"
    )
    return {
        "candidate_id": candidate_id,
        "input_index": index,
        "intended_action": intended_action,
        "normalized_candidate": {
            "platform_or_none": None,
            "handles": [],
            "profile_urls": [],
            "profile_subject_id_or_none": None,
            "platform_account_id_or_none": None,
            "platform_public_account_id_or_none": None,
            "display_name_or_none": None,
            "source_url_or_none": None,
        },
        "identity_keys": [],
        "errors": [
            {
                "code": "invalid_candidate_shape",
                "message": f"candidate[{index}] {candidate_id!r}: {message}",
            }
        ],
    }


def _normalize_candidate(candidate: Mapping[str, Any], index: int) -> dict[str, Any]:
    _reject_unknown_keys(candidate, _ALLOWED_CANDIDATE_KEYS, "candidate")
    candidate_id = _non_empty_str(candidate.get("candidate_id"), "candidate_id")
    intended_action = _non_empty_str(candidate.get("intended_action"), "intended_action")
    if intended_action not in _ALLOWED_INTENDED_ACTIONS:
        raise ValueError(
            f"intended_action must be one of {sorted(_ALLOWED_INTENDED_ACTIONS)!r}; got {intended_action!r}"
        )

    errors: list[dict[str, str]] = []
    platform = _optional_normalized_platform(candidate.get("platform"))
    if platform and platform not in _ALLOWED_PLATFORMS:
        errors.append({"code": "unsupported_platform", "message": "candidate platform is not supported"})
    inferred_platforms: set[str] = set()
    handles: set[str] = set()
    urls: set[str] = set()

    for field_name in ("handle_or_url", "public_handle_or_none", "public_profile_url_or_none"):
        value = _optional_str(candidate.get(field_name))
        if not value:
            continue
        if _looks_like_url(value):
            inferred = _platform_from_url(value)
            if inferred:
                inferred_platforms.add(inferred)
            else:
                errors.append({
                    "code": "unsupported_profile_url_host",
                    "message": "profile URL must be on a supported social host",
                })
            urls.add(_normalize_url(value))
            effective_platform = inferred or platform
            handle_from_url = _handle_from_url(value, effective_platform)
            if handle_from_url:
                handles.add(handle_from_url)
            elif _is_non_profile_url_shape(value, effective_platform):
                errors.append({
                    "code": "unresolvable_profile_url",
                    "message": (
                        "profile URL does not identify a specific account/profile page "
                        "(looks like a post/share/short link); provide the account profile "
                        "URL or handle instead"
                    ),
                })
        elif field_name == "public_profile_url_or_none":
            errors.append({"code": "invalid_public_profile_url", "message": "public_profile_url_or_none must be a URL"})
        else:
            handles.add(_normalize_handle(value))

    if platform and inferred_platforms and (inferred_platforms - {platform}):
        errors.append({"code": "platform_url_mismatch", "message": "candidate platform conflicts with URL platform"})
    if not platform and len(inferred_platforms) == 1:
        platform = next(iter(inferred_platforms))
    elif not platform and len(inferred_platforms) > 1:
        errors.append({"code": "ambiguous_candidate_platform", "message": "candidate URLs infer multiple platforms"})

    profile_subject_id = _optional_str(candidate.get("profile_subject_id_or_none"))
    platform_account_id = _optional_str(candidate.get("platform_account_id_or_none"))
    platform_public_account_id = _optional_str(candidate.get("platform_public_account_id_or_none"))
    identity_keys: list[tuple[str, str]] = []
    if profile_subject_id:
        identity_keys.append((f"profile_subject_id:{profile_subject_id}", "profile_subject_id"))
    if platform_account_id:
        identity_keys.append((f"platform_account_id:{platform_account_id}", "platform_account_id"))
    if platform and platform_public_account_id:
        identity_keys.append(
            (f"platform_public_account_id:{platform}:{platform_public_account_id}", "platform_public_account_id")
        )
    elif platform_public_account_id:
        errors.append(
            {
                "code": "missing_platform_for_platform_public_account_id",
                "message": "platform is required when platform_public_account_id_or_none is supplied",
            }
        )
    if platform:
        identity_keys.extend((f"platform_handle:{platform}:{handle}", "same_platform_public_handle") for handle in handles)
        display_name = _optional_str(candidate.get("display_name_or_none"))
        if display_name:
            identity_keys.append(
                (
                    f"platform_display_name:{platform}:{_normalize_display_name(display_name)}",
                    "same_platform_exact_display_name",
                )
            )
    elif handles:
        errors.append({"code": "missing_platform_for_handle", "message": "platform is required for handle matching"})
    identity_keys.extend((f"profile_url:{url}", "public_profile_url") for url in urls)

    if not identity_keys:
        errors.append({"code": "missing_identity_key", "message": "candidate must provide at least one matchable identity"})

    identity_keys = sorted(set(identity_keys))
    return {
        "candidate_id": candidate_id,
        "input_index": index,
        "intended_action": intended_action,
        "normalized_candidate": {
            "platform_or_none": platform,
            "handles": sorted(handles),
            "profile_urls": sorted(urls),
            "profile_subject_id_or_none": profile_subject_id,
            "platform_account_id_or_none": platform_account_id,
            "platform_public_account_id_or_none": platform_public_account_id,
            "display_name_or_none": _optional_str(candidate.get("display_name_or_none")),
            "source_url_or_none": _optional_str(candidate.get("source_url_or_none")),
        },
        "identity_keys": identity_keys,
        "errors": errors,
    }


def _duplicate_candidate_keys(candidates: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    key_to_candidate_ids: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        for key, _reason in candidate["identity_keys"]:
            key_to_candidate_ids[key].append(str(candidate["candidate_id"]))
    duplicate_keys_by_candidate: dict[str, list[str]] = defaultdict(list)
    for key, candidate_ids in key_to_candidate_ids.items():
        unique_ids = sorted(set(candidate_ids))
        if len(unique_ids) > 1:
            for candidate_id in unique_ids:
                duplicate_keys_by_candidate[candidate_id].append(key)
    return {candidate_id: sorted(keys) for candidate_id, keys in duplicate_keys_by_candidate.items()}


def _build_candidate_result(
    *,
    candidate: Mapping[str, Any],
    registry_index: Mapping[str, Sequence[Mapping[str, Any]]],
    duplicate_keys: Sequence[str],
) -> dict[str, Any]:
    errors = list(candidate["errors"])
    if duplicate_keys:
        errors.append(
            {
                "code": "duplicate_candidate_identity",
                "message": "candidate shares an exact identity key with another candidate in the batch",
            }
        )

    matches_by_subject: dict[str, dict[str, Any]] = {}
    for key, reason in candidate["identity_keys"]:
        for match in registry_index.get(key, ()):
            subject_id = str(match["profile_subject_id"])
            entry = matches_by_subject.setdefault(
                subject_id,
                {
                    "profile_subject_kind": match["profile_subject_kind"],
                    "profile_subject_id": subject_id,
                    "platform_account_id": match["platform_account_id"],
                    "platform": match["platform"],
                    "public_handle": match["public_handle"],
                    "public_profile_url": match["public_profile_url"],
                    "platform_public_account_id_or_none": match["platform_public_account_id_or_none"],
                    "match_reasons": [],
                },
            )
            if reason not in entry["match_reasons"]:
                entry["match_reasons"].append(reason)

    matches = sorted(matches_by_subject.values(), key=lambda item: item["profile_subject_id"])
    for match in matches:
        match["match_reasons"] = sorted(match["match_reasons"])

    if errors:
        decision = "invalid_candidate"
    elif len(matches) > 1:
        decision = "ambiguous_match"
    elif len(matches) == 1:
        decision = "existing_match"
    else:
        decision = "new_candidate"

    action_status, allowed_next_actions, action_blockers = _action_disposition(
        decision=decision,
        intended_action=str(candidate["intended_action"]),
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "input_index": candidate["input_index"],
        "intended_action": candidate["intended_action"],
        "decision": decision,
        "action_status": action_status,
        "can_start_new_capture": action_status == "allowed" and candidate["intended_action"] == "new_capture",
        "allowed_next_actions": allowed_next_actions,
        "action_blockers": action_blockers,
        "normalized_candidate": candidate["normalized_candidate"],
        "matched_registry_profiles": matches,
        "duplicate_candidate_identity_keys": list(duplicate_keys),
        "errors": errors,
    }


def _action_disposition(*, decision: str, intended_action: str) -> tuple[str, list[str], list[str]]:
    if decision == "invalid_candidate":
        return "blocked", ["fix_candidate_input"], ["invalid_candidate"]
    if decision == "ambiguous_match":
        return "blocked", ["resolve_identity"], ["ambiguous_match"]
    if intended_action == "classify":
        return "allowed", ["update_existing" if decision == "existing_match" else "new_capture"], []
    if intended_action == "new_capture":
        if decision == "new_candidate":
            return "allowed", ["new_capture"], []
        return "blocked", ["update_existing", "resolve_identity_if_not_same"], ["new_capture_existing_match"]
    if intended_action == "update_existing":
        if decision == "existing_match":
            return "allowed", ["update_existing"], []
        return "blocked", ["new_capture", "resolve_identity"], ["update_existing_without_match"]
    raise ValueError(f"unsupported intended_action: {intended_action}")


def _summarize_results(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    decisions = [str(result["decision"]) for result in results]
    blocked_actions = sum(1 for result in results if result["action_status"] == "blocked")
    return {
        "total_candidates": len(results),
        "existing_matches": decisions.count("existing_match"),
        "new_candidates": decisions.count("new_candidate"),
        "ambiguous_matches": decisions.count("ambiguous_match"),
        "invalid_candidates": decisions.count("invalid_candidate"),
        "blocked_actions": blocked_actions,
        "safe_to_capture_new": sum(1 for result in results if result["can_start_new_capture"]),
    }


def _reject_unknown_keys(value: Mapping[str, Any], allowed: frozenset[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{context} contains unknown key(s): {unknown!r}")


def _require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be an object")
    return value


def _non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("optional string field must be a string or null")
    normalized = value.strip()
    return normalized or None


def _normalize_platform(value: Any) -> str:
    return _non_empty_str(value, "platform").lower()


def _optional_normalized_platform(value: Any) -> str | None:
    raw = _optional_str(value)
    return raw.lower() if raw else None


def _normalize_handle(value: Any) -> str:
    handle = _non_empty_str(value, "handle").strip().strip("/")
    if handle.startswith("@"):
        handle = handle[1:]
    if not handle:
        raise ValueError("handle must be non-empty after normalization")
    return handle.lower()


def _normalize_display_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", value.casefold())
    if not normalized:
        raise ValueError("display_name_or_none must contain a letter or number")
    return normalized


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def _normalize_url(value: str) -> str:
    parsed = urlparse(_non_empty_str(value, "url"))
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("url must include scheme and host")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") or "/"
    return f"https://{host}{path}"


def _platform_from_url(value: str) -> str | None:
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host.endswith("instagram.com"):
        return "instagram"
    if host.endswith("youtube.com") or host.endswith("youtu.be"):
        return "youtube"
    if host.endswith("tiktok.com"):
        return "tiktok"
    return None


_INSTAGRAM_NON_PROFILE_PATH_SEGMENTS = frozenset(
    {
        "p",
        "reel",
        "reels",
        "tv",
        "stories",
        "explore",
        "accounts",
        "direct",
        "developer",
        "about",
        "legal",
        "api",
        "embed",
    }
)


def _handle_from_url(value: str, platform: str | None) -> str | None:
    if not platform:
        return None
    parsed = urlparse(value)
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        return None
    if platform == "instagram":
        if path_parts[0].lower() in _INSTAGRAM_NON_PROFILE_PATH_SEGMENTS:
            return None
        return _normalize_handle(path_parts[0])
    if platform == "tiktok":
        if not path_parts[0].startswith("@"):
            return None
        return _normalize_handle(path_parts[0])
    if platform == "youtube" and path_parts[0].startswith("@"):
        return _normalize_handle(path_parts[0])
    return None


def _is_non_profile_url_shape(value: str, platform: str | None) -> bool:
    if platform not in ("instagram", "tiktok"):
        return False
    parsed = urlparse(value)
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        return False
    if platform == "instagram":
        return path_parts[0].lower() in _INSTAGRAM_NON_PROFILE_PATH_SEGMENTS
    return not path_parts[0].startswith("@")
