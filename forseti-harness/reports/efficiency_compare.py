"""Conservative, case-stratified comparisons of completed workflow runs.

Explicit ``pair_id`` values match repeat blocks when present on every run.
Otherwise callers must supply deliberately matched order *within each case*.
These descriptive screens do not estimate significance, billed cost, or p95.
"""

from __future__ import annotations

import json
import math
from statistics import median


_METRICS = ("elapsed_seconds", "total_tokens")
_TOKEN_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens", "total_tokens",
)


def _number(value: object, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite nonnegative number")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{label} must be a finite nonnegative number")


def _usage(usage: object, label: str) -> bool:
    if usage is None:
        return False
    if not isinstance(usage, dict):
        raise ValueError(f"{label} must be an object")
    for field in _TOKEN_FIELDS:
        value = usage.get(field)
        if value is not None:
            _number(value, f"{label}.{field}")
    if usage.get("coverage") != "complete":
        return False
    if any(usage.get(field) is None for field in ("input_tokens", "output_tokens", "total_tokens")):
        raise ValueError(f"{label} complete coverage requires input/output/total tokens")
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise ValueError(f"{label}.total_tokens must equal input_tokens + output_tokens")
    for subset, parent in (("cached_input_tokens", "input_tokens"),
                           ("cache_write_input_tokens", "input_tokens"),
                           ("reasoning_output_tokens", "output_tokens")):
        if usage.get(subset) is not None and usage[subset] > usage[parent]:
            raise ValueError(f"{label}.{subset} exceeds {parent}")
    return not usage.get("issues")


def _validate(records: list[dict], seen: set[str]) -> None:
    if not isinstance(records, list):
        raise ValueError("runs must be a list")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each run must be an object")
        if type(record.get("schema_version")) is not int or record["schema_version"] != 1:
            raise ValueError("run schema_version must be 1")
        for field in ("run_id", "workflow", "workload_id"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"run {field} must be a nonempty string")
        if record["run_id"] in seen:
            raise ValueError(f"duplicate run_id: {record['run_id']}")
        seen.add(record["run_id"])
        if record.get("pair_id") is not None and (
            not isinstance(record["pair_id"], str) or not record["pair_id"].strip()
        ):
            raise ValueError("pair_id must be a nonempty string")
        if record.get("elapsed_seconds") is not None:
            _number(record["elapsed_seconds"], "elapsed_seconds")
        _usage(record.get("usage"), "usage")
        attempts = record.get("attempts", [])
        if not isinstance(attempts, list):
            raise ValueError("attempts must be a list")
        for attempt in attempts:
            if not isinstance(attempt, dict):
                raise ValueError("attempt must be an object")
            if attempt.get("elapsed_seconds") is not None:
                _number(attempt["elapsed_seconds"], "attempt.elapsed_seconds")
            _usage(attempt.get("usage"), "attempt.usage")


def _token_value(record: dict) -> int | float | None:
    if not _usage(record.get("usage"), "usage"):
        return None
    attempts = record.get("attempts", [])
    if attempts:
        if any(not _usage(attempt.get("usage"), "attempt.usage") for attempt in attempts):
            return None
        # Failed attempts are resources spent on this completed outcome too.
        total = sum(attempt["usage"]["total_tokens"] for attempt in attempts)
        if total != record["usage"]["total_tokens"]:
            raise ValueError("aggregate total_tokens does not include exactly all attempts")
    return record["usage"]["total_tokens"]


def _blocked(reason: str, status: str = "inconclusive") -> dict:
    return {"status": status, "reasons": [reason], "no_worsening": False}


def _summary(values: list[int | float]) -> dict:
    return {"median": median(values), "min": min(values), "max": max(values)}


def _metric(before: list, after: list, minimum: int, threshold: float) -> dict:
    if any(value is None for value in before + after):
        return _blocked("missing measurement or incomplete usage coverage", "unmeasured")
    deltas = [right - left for left, right in zip(before, after)]
    changes = [(right - left) / left if left else None for left, right in zip(before, after)]
    required = math.ceil(0.8 * len(before))
    lower = sum(delta < 0 for delta in deltas)
    higher = sum(delta > 0 for delta in deltas)
    result = {
        "status": "inconclusive", "reasons": [], "pairs": len(before),
        "baseline": _summary(before), "candidate": _summary(after),
        "paired_delta": _summary(deltas),
        "paired_relative_change": None if None in changes else _summary(changes),
        "lower_pairs": lower, "higher_pairs": higher,
        "equal_pairs": len(before) - lower - higher,
        "required_direction_pairs": required,
        "no_worsening": False,
    }
    if len(before) < minimum:
        result["reasons"].append(f"requires at least {minimum} matched pairs per case")
    elif None in changes:
        result["reasons"].append("zero baseline: relative change is undefined; absolute deltas retained")
        result["no_worsening"] = all(delta == 0 for delta in deltas)
    else:
        change = median(changes)
        result["no_worsening"] = higher == 0
        if change < 0 and change <= -threshold and lower >= required:
            result["status"] = "improved"
        elif change > 0 and change >= threshold and higher >= required:
            result["status"] = "regressed"
        else:
            result["reasons"].append("material threshold or direction consistency not met")
    return result


def _case(before: list[dict], after: list[dict], minimum: int, threshold: float) -> dict:
    result = {"baseline_runs": len(before), "candidate_runs": len(after)}
    reasons = []
    if len(before) != len(after):
        reasons.append("unequal repeat counts; no successful-run filtering or truncation")
    records = before + after
    configurations = [record.get("configuration") for record in records]
    if any(not isinstance(config, dict) or not config for config in configurations):
        reasons.append("explicit configuration is required")
    else:
        try:
            configs = {json.dumps(config, sort_keys=True, allow_nan=False) for config in configurations}
        except (ValueError, TypeError) as exc:
            raise ValueError("configuration must contain finite JSON values") from exc
        if len(configs) != 1:
            reasons.append("configuration differs across arms or repeats")
    if any(record.get("outcome") != "success" for record in records):
        reasons.append("every compared run must complete successfully")
    qualities = [record.get("quality") for record in records]
    if any(not isinstance(q, dict) or q.get("status") != "passed" or
           not isinstance(q.get("oracle"), str) or not q["oracle"].strip() for q in qualities):
        reasons.append("every run needs explicitly passed quality with a named oracle")
    elif len({q["oracle"] for q in qualities}) != 1:
        reasons.append("quality oracle differs across arms or repeats")
    explicit = [record.get("pair_id") is not None for record in records]
    result["pairing"] = "pair_id" if any(explicit) else "caller_order_within_case"
    if any(explicit):
        if not all(explicit):
            reasons.append("mixed presence of pair_id")
        else:
            before_ids = [record["pair_id"] for record in before]
            after_ids = [record["pair_id"] for record in after]
            if len(set(before_ids)) != len(before_ids) or len(set(after_ids)) != len(after_ids):
                raise ValueError("duplicate pair_id within case and arm")
            if set(before_ids) != set(after_ids):
                reasons.append("pair_id membership differs")
            else:
                by_id = {record["pair_id"]: record for record in after}
                after = [by_id[record["pair_id"]] for record in before]
    if not reasons:
        for left, right in zip(before, after):
            left_fp = left["quality"].get("output_fingerprint")
            right_fp = right["quality"].get("output_fingerprint")
            if left_fp is not None and right_fp is not None and left_fp != right_fp:
                reasons.append("matched output fingerprints differ")
                break
    result["reasons"] = reasons
    if reasons:
        result["metrics"] = {metric: _blocked("; ".join(reasons)) for metric in _METRICS}
    else:
        result["run_pairs"] = [[left["run_id"], right["run_id"]] for left, right in zip(before, after)]
        result["metrics"] = {
            "elapsed_seconds": _metric([r.get("elapsed_seconds") for r in before],
                                       [r.get("elapsed_seconds") for r in after], minimum, threshold),
            "total_tokens": _metric([_token_value(r) for r in before],
                                    [_token_value(r) for r in after], minimum, threshold),
        }
    return result


def _combine(metrics: list[dict]) -> dict:
    statuses = {metric["status"] for metric in metrics}
    if "unmeasured" in statuses:
        return _blocked("at least one required case or metric is unmeasured", "unmeasured")
    if "improved" in statuses and "regressed" in statuses:
        return _blocked("mixed improvement and regression; no single efficiency win")
    if "improved" in statuses and all(m["status"] == "improved" or m["no_worsening"] for m in metrics):
        return {"status": "improved", "reasons": [], "no_worsening": True}
    if "regressed" in statuses and all(m["status"] == "regressed" or m["no_worsening"] for m in metrics):
        return {"status": "regressed", "reasons": [], "no_worsening": False}
    return {"status": "inconclusive", "reasons": ["no consistent material result across all required cases or metrics"],
            "no_worsening": all(m["no_worsening"] for m in metrics)}


def compare_runs(baseline: list[dict], candidate: list[dict], *, minimum_pairs: int = 3,
                 relative_threshold: float = 0.05) -> dict:
    """Compare exact case membership and matched repeats without discarding failures.

    Revision may differ (it is the treatment). Configuration, successful quality
    oracle, and workload content identity must match. Threshold is a fraction in
    [0, 1]; at least three repeats and 80% direction agreement are required.
    Unknown usage does not prevent an elapsed-time result, but prevents a full
    efficiency improvement. Zero baselines retain absolute evidence only.
    """
    if type(minimum_pairs) is not int or minimum_pairs < 3:
        raise ValueError("minimum_pairs must be an integer at least 3")
    _number(relative_threshold, "relative_threshold")
    if relative_threshold > 1:
        raise ValueError("relative_threshold must be at most 1")
    seen: set[str] = set()
    _validate(baseline, seen)
    _validate(candidate, seen)
    groups = []
    for records in (baseline, candidate):
        group: dict[tuple[str, str], list[dict]] = {}
        for record in records:
            group.setdefault((record["workflow"], record["workload_id"]), []).append(record)
        groups.append(group)
    left, right = groups
    reasons = []
    if not left or not right:
        reasons.append("both arms require recorded runs")
    if set(left) != set(right):
        reasons.append("exact workflow/workload case membership differs")
    cases = []
    for workflow, workload in sorted(set(left) & set(right)):
        cases.append({"workflow": workflow, "workload_id": workload,
                      **_case(left[(workflow, workload)], right[(workflow, workload)],
                              minimum_pairs, relative_threshold)})
    metrics = {}
    for name in _METRICS:
        parts = [case["metrics"][name] for case in cases]
        metrics[name] = _blocked("; ".join(reasons)) if reasons else _combine(parts)
        # Summarize paired effects with equal case weight only when every case
        # supplies compatible measured evidence. Never pool raw unequal work.
        if not reasons and parts and all(p.get("paired_relative_change") is not None for p in parts):
            metrics[name]["case_median_relative_changes"] = [p["paired_relative_change"]["median"] for p in parts]
            metrics[name]["median_case_relative_change"] = median(metrics[name]["case_median_relative_changes"])
    overall = _combine(list(metrics.values()))
    return {"schema_version": 1, "overall": overall["status"],
            "reasons": reasons + overall["reasons"], "metrics": metrics, "cases": cases,
            "protocol": {"minimum_pairs": minimum_pairs, "relative_threshold": relative_threshold,
                         "direction_fraction": 0.8, "case_weighting": "equal_case_paired_effects",
                         "pairing_fallback": "caller_order_within_case",
                         "scope": "descriptive observed runs; no significance, pricing, or tail estimate"}}
