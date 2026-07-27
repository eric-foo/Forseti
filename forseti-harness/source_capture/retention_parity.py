"""Extraction-parity checking for capture surfaces moving to content retention.

Content-only retention removes the ability to re-extract a capture after the
fact, so the flip is only safe if the in-flight extractor demonstrably produces
what a re-extraction of the preserved bytes produces.  This module is the cheap
local check for that: re-extract raw, field-diff against the record that was
banked, and assert the surface's structural invariants.  No model tokens, no
network, no services -- pure local compute over captures the lane already made.

Two callers share it:

* the ONE-TIME parity gate before a lane's flip, over that lane's existing raw
  packets (with the lane's pre-flip extracted records as the baseline); and
* the rolling-window regression check after any extractor edit, over the
  rolling raw sample (with the sample's banked content record as the baseline).

Both are the same operation against a different baseline source, so they stay
one code path rather than two that can drift apart.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# Row fields every SERP-family content record carries.  Compared exactly: a
# silent change in any of them is the mis-ranking / mis-pairing defect class
# that content-only retention can no longer repair after the fact.
SERP_ROW_COMPARE_FIELDS: tuple[str, ...] = (
    "module_type", "order_in_module", "title", "displayed_source",
    "displayed_domain", "displayed_path_hint", "account_or_creator",
    "canonical_url", "canonical_url_source_visible", "snippet", "visible_date",
    "engagement_snippet", "duration", "price", "rating", "rating_count",
    "sponsored_or_affiliate_label", "platform", "dependency_label",
)

SERP_TOP_LEVEL_COMPARE_FIELDS: tuple[str, ...] = (
    "modules_present", "ai_overview", "visible_text_chars", "direct_href_count",
    "rendered_query", "query_rewritten", "google_location_note",
)


@dataclass
class ParityDiff:
    """One field-level disagreement between a baseline and a re-extraction."""

    unit: str
    location: str
    field_name: str
    baseline: Any
    reextracted: Any

    def describe(self) -> str:
        return (
            f"{self.unit} {self.location} {self.field_name}: "
            f"{self.baseline!r} -> {self.reextracted!r}"
        )


@dataclass
class InvariantViolation:
    """One structural invariant a re-extracted record failed."""

    unit: str
    invariant: str
    detail: str

    def describe(self) -> str:
        return f"{self.unit} {self.invariant}: {self.detail}"


@dataclass
class ParityReport:
    """Aggregate verdict for one parity run."""

    surface: str
    units_compared: int = 0
    units_identical: int = 0
    units_without_baseline: int = 0
    units_anomalous: int = 0
    diffs: list[ParityDiff] = field(default_factory=list)
    violations: list[InvariantViolation] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    @property
    def field_diff_verdict(self) -> str:
        if self.units_compared == 0:
            return "not-run"
        return "pass" if not self.diffs else "fail"

    @property
    def invariant_verdict(self) -> str:
        if self.units_compared == 0 and self.units_without_baseline == 0:
            return "not-run"
        return "pass" if not self.violations else "fail"

    def diff_field_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for diff in self.diffs:
            counts[diff.field_name] = counts.get(diff.field_name, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "units_compared": self.units_compared,
            "units_identical": self.units_identical,
            "units_without_baseline": self.units_without_baseline,
            "units_anomalous": self.units_anomalous,
            "field_diff_verdict": self.field_diff_verdict,
            "invariant_verdict": self.invariant_verdict,
            "diff_count": len(self.diffs),
            "diff_field_counts": self.diff_field_counts(),
            "diff_samples": [diff.describe() for diff in self.diffs[:40]],
            "invariant_violations": [v.describe() for v in self.violations[:40]],
            "anomalies": self.anomalies[:40],
        }


def compare_records(
    *,
    unit: str,
    baseline: Mapping[str, Any],
    reextracted: Mapping[str, Any],
    row_fields: Sequence[str] = SERP_ROW_COMPARE_FIELDS,
    top_level_fields: Sequence[str] = SERP_TOP_LEVEL_COMPARE_FIELDS,
) -> list[ParityDiff]:
    """Field-diff a banked record against a fresh re-extraction of the same bytes.

    A top-level field absent from the baseline is skipped rather than reported:
    a pre-flip lane record and an in-flight content record legitimately carry
    different envelopes.  Row contents are compared unconditionally -- that is
    where the defect class lives.
    """
    diffs: list[ParityDiff] = []
    for name in top_level_fields:
        if name not in baseline:
            continue
        if baseline.get(name) != reextracted.get(name):
            diffs.append(
                ParityDiff(unit, "record", name, baseline.get(name), reextracted.get(name))
            )

    baseline_rows = list(baseline.get("rows") or [])
    reextracted_rows = list(reextracted.get("rows") or [])
    if len(baseline_rows) != len(reextracted_rows):
        diffs.append(
            ParityDiff(
                unit, "rows", "row_count", len(baseline_rows), len(reextracted_rows)
            )
        )
        return diffs

    for index, (baseline_row, reextracted_row) in enumerate(
        zip(baseline_rows, reextracted_rows)
    ):
        for name in row_fields:
            if baseline_row.get(name) != reextracted_row.get(name):
                diffs.append(
                    ParityDiff(
                        unit,
                        f"row[{index}]",
                        name,
                        baseline_row.get(name),
                        reextracted_row.get(name),
                    )
                )
    return diffs


def check_serp_invariants(
    *, unit: str, record: Mapping[str, Any], minimum_rows: int
) -> list[InvariantViolation]:
    """Structural invariants for a SERP-family content record.

    These do not police result-count variation -- Google's page composition
    varies legitimately.  They catch a structural break: a page that parsed to
    nothing, a module set that vanished, or module ordering that stopped being a
    faithful 1..n sequence (the arrangement defect the v1 extractor shipped).
    """
    violations: list[InvariantViolation] = []
    rows = list(record.get("rows") or [])
    modules = list(record.get("modules_present") or [])

    if not modules:
        violations.append(
            InvariantViolation(unit, "module_presence", "no known module heading parsed")
        )
    if len(rows) < minimum_rows:
        violations.append(
            InvariantViolation(
                unit,
                "row_count_band",
                f"{len(rows)} rows is below the {minimum_rows}-row floor",
            )
        )

    seen_modules = {row.get("module_type") for row in rows}
    undeclared = sorted(
        str(module) for module in seen_modules if module and module not in modules
    )
    if undeclared:
        violations.append(
            InvariantViolation(
                unit,
                "module_declaration",
                f"rows typed to undeclared modules: {', '.join(undeclared)}",
            )
        )

    per_module: dict[str, list[int]] = {}
    for row in rows:
        module = str(row.get("module_type"))
        order = row.get("order_in_module")
        if isinstance(order, int):
            per_module.setdefault(module, []).append(order)
    # Strictly ascending, NOT contiguous. `order_in_module` is assigned during
    # metadata-row merging and the later title/source pairing pass then drops
    # the merged-away twin without renumbering, so gaps are normal and carry no
    # meaning (265 of 1113 module sequences in the pre-flip v2 corpus are
    # gapped). What must never happen is a row appearing out of source order --
    # that is the arrangement defect the v1 extractor shipped, and zero of those
    # 1113 sequences violate it.
    for module, orders in sorted(per_module.items()):
        if any(later <= earlier for earlier, later in zip(orders, orders[1:])):
            violations.append(
                InvariantViolation(
                    unit,
                    "order_monotonicity",
                    f"module {module} order_in_module is {orders[:12]}, "
                    "which is not strictly ascending in source order",
                )
            )
    return violations


def exercise_failure_path(
    *,
    extractor: Callable[..., Mapping[str, Any]],
    anomaly_type: type[BaseException],
    synthetic_cases: Sequence[tuple[str, bytes, bytes, str]],
) -> tuple[str, list[str]]:
    """Run synthetic inputs that MUST raise, so raw preservation stays wired.

    Returns ``(verdict, notes)``.  A synthetic case that returns a record
    instead of raising is a gate failure: it means a degenerate page would be
    banked as content and its bytes discarded.
    """
    notes: list[str] = []
    failures = 0
    for name, rendered_dom, visible_text, final_url in synthetic_cases:
        try:
            extractor(
                rendered_dom=rendered_dom,
                visible_text=visible_text,
                final_url=final_url,
            )
        except anomaly_type as exc:
            notes.append(f"{name}: raised {type(exc).__name__} (raw preserved)")
            continue
        except Exception as exc:  # noqa: BLE001 - any raise still preserves raw
            notes.append(
                f"{name}: raised {type(exc).__name__}, not the declared anomaly type "
                "(raw still preserved, but the tripwire is mistyped)"
            )
            failures += 1
            continue
        notes.append(f"{name}: RETURNED A RECORD; degenerate page would be banked")
        failures += 1
    if not synthetic_cases:
        return "not-run", notes
    return ("pass" if failures == 0 else "fail"), notes


__all__ = [
    "SERP_ROW_COMPARE_FIELDS",
    "SERP_TOP_LEVEL_COMPARE_FIELDS",
    "InvariantViolation",
    "ParityDiff",
    "ParityReport",
    "check_serp_invariants",
    "compare_records",
    "exercise_failure_path",
]
