from __future__ import annotations

from copy import deepcopy

import pytest

from reports.efficiency_compare import compare_runs


def usage(total=100, *, coverage="complete"):
    return {"coverage": coverage, "input_tokens": total - 10, "output_tokens": 10,
            "total_tokens": total, "cached_input_tokens": 0,
            "cache_write_input_tokens": 0, "reasoning_output_tokens": 0, "issues": []}


def run(identifier, *, elapsed=100, tokens=100, case="fixture-sha", pair=None):
    record = {"schema_version": 1, "workflow": "full-workflow", "workload_id": case,
              "configuration": {"model": "same-model", "settings": {"reasoning": "high"},
                                "environment": "frozen", "semantic_case": "complete-job"},
              "revision": "baseline", "run_id": identifier,
              "elapsed_seconds": elapsed, "outcome": "success",
              "quality": {"status": "passed", "oracle": "full-output-contract-v1",
                          "output_fingerprint": "equivalent-result"},
              "usage": usage(tokens), "attempts": []}
    if pair is not None:
        record["pair_id"] = pair
    return record


def arms(*, elapsed=80, tokens=80, count=3):
    before = [run(f"before-{i}") for i in range(count)]
    after = [run(f"after-{i}", elapsed=elapsed, tokens=tokens) for i in range(count)]
    for record in after:
        record["revision"] = "candidate"
    return before, after


def test_matched_complete_improvement_permits_treatment_revision_difference():
    report = compare_runs(*arms())
    assert report["overall"] == "improved"
    assert report["metrics"]["total_tokens"]["median_case_relative_change"] == -0.2
    case = report["cases"][0]
    assert case["pairing"] == "caller_order_within_case"
    assert case["metrics"]["elapsed_seconds"]["baseline"] == {"median": 100, "min": 100, "max": 100}


def test_material_regression():
    report = compare_runs(*arms(elapsed=120, tokens=120))
    assert report["overall"] == "regressed"


@pytest.mark.parametrize("field,value", [("outcome", "failed"), ("quality", {"status": "failed", "oracle": "full-output-contract-v1"}),
                                          ("quality", {"status": "unmeasured"})])
def test_deceptively_cheap_failed_or_unjudged_output_cannot_win(field, value):
    before, after = arms(elapsed=1, tokens=10)
    after[0][field] = value
    report = compare_runs(before, after)
    assert report["overall"] == "inconclusive"
    assert "baseline" not in report["cases"][0]["metrics"]["elapsed_seconds"]


@pytest.mark.parametrize("mutation", ["configuration", "workload", "workflow", "oracle", "fingerprint"])
def test_changed_comparison_contract_cannot_win(mutation):
    before, after = arms()
    if mutation == "configuration":
        after[0][mutation]["model"] = "cheaper-model"
    elif mutation == "workload":
        after[0]["workload_id"] = "different-fixture"
    elif mutation == "workflow":
        after[0]["workflow"] = "partial-workflow"
    elif mutation == "oracle":
        after[0]["quality"]["oracle"] = "easier-oracle"
    else:
        after[0]["quality"]["output_fingerprint"] = "missing-work"
    assert compare_runs(before, after)["overall"] == "inconclusive"


def test_optional_output_fingerprint_does_not_replace_explicit_quality():
    before, after = arms()
    del after[0]["quality"]["output_fingerprint"]
    assert compare_runs(before, after)["overall"] == "improved"
    del after[0]["quality"]["oracle"]
    assert compare_runs(before, after)["overall"] == "inconclusive"


def test_unknown_usage_preserves_elapsed_evidence_but_not_full_win():
    before, after = arms()
    after[0]["usage"]["coverage"] = "unknown"
    report = compare_runs(before, after)
    assert report["metrics"]["elapsed_seconds"]["status"] == "improved"
    assert report["metrics"]["total_tokens"]["status"] == "unmeasured"
    assert report["overall"] == "unmeasured"


def test_missing_child_usage_prevents_aggregate_complete_claim():
    before, after = arms()
    after[0]["attempts"] = [{"outcome": "failed", "usage": usage(30, coverage="unknown")},
                             {"outcome": "success", "usage": usage(50)}]
    report = compare_runs(before, after)
    assert report["metrics"]["total_tokens"]["status"] == "unmeasured"
    assert report["metrics"]["elapsed_seconds"]["status"] == "improved"


def test_failed_attempt_costs_count_in_successful_final_outcome():
    before, after = arms(elapsed=100, tokens=120)
    for record in after:
        record["attempts"] = [{"outcome": "failed", "usage": usage(70)},
                              {"outcome": "success", "usage": usage(50)}]
    assert compare_runs(before, after)["overall"] == "regressed"
    after[0]["usage"] = usage(50)
    with pytest.raises(ValueError, match="all attempts"):
        compare_runs(before, after)


def test_latency_token_tradeoff_is_not_an_efficiency_win():
    report = compare_runs(*arms(elapsed=80, tokens=120))
    assert report["metrics"]["elapsed_seconds"]["status"] == "improved"
    assert report["metrics"]["total_tokens"]["status"] == "regressed"
    assert report["overall"] == "inconclusive"


def test_small_token_increase_still_blocks_full_efficiency_win():
    assert compare_runs(*arms(elapsed=80, tokens=102))["overall"] == "inconclusive"


def test_constant_other_metric_allows_improvement():
    assert compare_runs(*arms(elapsed=80, tokens=100))["overall"] == "improved"


def test_unequal_repeats_are_not_truncated():
    before, after = arms()
    after.pop()
    report = compare_runs(before, after)
    assert report["overall"] == "inconclusive"
    assert "unequal repeat counts" in report["cases"][0]["reasons"][0]


def test_tiny_n_does_not_earn_a_win():
    assert compare_runs(*arms(count=2))["overall"] == "inconclusive"


def test_noisy_direction_is_inconclusive_despite_better_median():
    before, after = arms()
    after[-1]["elapsed_seconds"] = 120
    after[-1]["usage"] = usage(120)
    report = compare_runs(before, after)
    assert report["overall"] == "inconclusive"
    assert report["cases"][0]["metrics"]["total_tokens"]["lower_pairs"] == 2


def test_threshold_is_material_and_configurable():
    assert compare_runs(*arms(elapsed=96, tokens=96))["overall"] == "inconclusive"
    report = compare_runs(*arms(elapsed=96, tokens=96), relative_threshold=0.03)
    assert report["overall"] == "improved"
    assert report["protocol"]["relative_threshold"] == 0.03


def test_zero_baseline_retains_absolute_evidence_without_infinite_ratio():
    before, after = arms()
    for record in before:
        record["elapsed_seconds"] = 0
    metric = compare_runs(before, after)["cases"][0]["metrics"]["elapsed_seconds"]
    assert metric["status"] == "inconclusive"
    assert metric["paired_relative_change"] is None
    assert metric["paired_delta"]["median"] == 80


def test_multiple_cases_do_not_pool_easy_and_hard_workloads():
    before, after = arms()
    for i in range(3):
        before.append(run(f"hard-before-{i}", elapsed=1000, tokens=1000, case="hard"))
        after.append(run(f"hard-after-{i}", elapsed=1100, tokens=1100, case="hard"))
    report = compare_runs(before, after)
    assert len(report["cases"]) == 2
    assert report["overall"] == "inconclusive"
    assert sorted(report["metrics"]["total_tokens"]["case_median_relative_changes"]) == [-0.2, 0.1]


def test_explicit_pair_ids_override_arm_order():
    before = [run(f"b-{i}", elapsed=value, tokens=value, pair=str(i))
              for i, value in enumerate([100, 1000, 10000])]
    after = [run(f"c-{i}", elapsed=value * 0.8, tokens=value * 0.8, pair=str(i))
             for i, value in enumerate([100, 1000, 10000])]
    after.reverse()
    report = compare_runs(before, after)
    assert report["overall"] == "improved"
    assert report["cases"][0]["run_pairs"][0] == ["b-0", "c-0"]


@pytest.mark.parametrize("mode", ["mixed", "mismatch", "duplicate"])
def test_pair_id_integrity(mode):
    before, after = arms()
    for i, (left, right) in enumerate(zip(before, after)):
        left["pair_id"] = right["pair_id"] = str(i)
    if mode == "mixed":
        del after[0]["pair_id"]
    elif mode == "mismatch":
        after[0]["pair_id"] = "absent-before"
    else:
        after[0]["pair_id"] = after[1]["pair_id"]
        with pytest.raises(ValueError, match="duplicate pair_id"):
            compare_runs(before, after)
        return
    assert compare_runs(before, after)["overall"] == "inconclusive"


def test_duplicate_run_ids_across_arms_rejected():
    before, after = arms()
    after[0]["run_id"] = before[0]["run_id"]
    with pytest.raises(ValueError, match="duplicate run_id"):
        compare_runs(before, after)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), float("-inf"), True, "100"])
@pytest.mark.parametrize("field", ["elapsed_seconds", "total_tokens", "cached_input_tokens"])
def test_malformed_numeric_evidence_is_loud_even_on_failed_runs(value, field):
    before, after = arms()
    after[0]["outcome"] = "failed"
    if field == "elapsed_seconds":
        after[0][field] = value
    else:
        after[0]["usage"][field] = value
    with pytest.raises(ValueError, match="finite nonnegative"):
        compare_runs(before, after)


@pytest.mark.parametrize("kwargs", [{"minimum_pairs": value} for value in [0, 2, True, 3.0, float("nan"), float("inf")]] +
                         [{"relative_threshold": value} for value in [-0.1, 1.1, True, float("nan"), float("inf")]])
def test_invalid_protocol_rejected(kwargs):
    with pytest.raises(ValueError):
        compare_runs(*arms(), **kwargs)


def test_inconsistent_complete_usage_rejected():
    before, after = arms()
    after[0]["usage"]["total_tokens"] = 1
    with pytest.raises(ValueError, match="must equal"):
        compare_runs(before, after)


def test_empty_arms_and_missing_metric_never_win():
    assert compare_runs([], [])["overall"] == "inconclusive"
    before, after = arms()
    after[0]["elapsed_seconds"] = None
    assert compare_runs(before, after)["overall"] == "unmeasured"


def test_input_records_not_mutated():
    before, after = arms()
    expected = deepcopy((before, after))
    compare_runs(before, after)
    assert (before, after) == expected
