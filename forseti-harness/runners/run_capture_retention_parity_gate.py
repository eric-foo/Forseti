"""Capture-retention parity gate: the cheap local check before a lane flips.

Run ONCE per lane before switching its default retention to content-only, and
again over the rolling raw sample after any extractor edit.  Both modes do the
same thing -- re-extract preserved rendered bytes with the current in-flight
extractor and field-diff against the record that was banked -- and both are pure
local compute over captures the lane already made.

Packet mode (the one-time gate)::

    python runners/run_capture_retention_parity_gate.py packets `
      --surface google_serp_us_parameterized `
      --packet-root "<directory of packets with raw/ preserved>" `
      --baseline-record-dir "<lane's pre-flip extracted records, optional>" `
      --output "<verdict json>"

Rolling-sample mode (the post-edit regression check)::

    python runners/run_capture_retention_parity_gate.py rolling-sample `
      --surface google_serp_us_parameterized `
      --raw-sample-root "<operator-drive rolling sample root>" `
      --output "<verdict json>"

Exit code is 0 only when every RUN check passed.  A check with no input reports
`not-run` and does not, by itself, fail the gate -- the operator decides whether
a not-run check blocks the flip, and the verdict JSON says plainly which is which.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_capture.google_serp_content import (
    GOOGLE_SERP_CONTENT_RECORD_VERSION,
    MINIMUM_ROW_COUNT,
    GoogleSerpContentAnomaly,
    build_google_serp_content_record,
)
from source_capture.retention_parity import (
    ParityReport,
    check_serp_invariants,
    compare_records,
    exercise_failure_path,
)
from source_capture.rolling_raw_sample import (
    CONTENT_RECORD_SAMPLE_FILENAME,
    RENDERED_DOM_SAMPLE_FILENAME,
    VISIBLE_TEXT_SAMPLE_FILENAME,
    RollingRawSampleStore,
)

# Per-surface binding: the in-flight extractor, its raw artifact names inside a
# packet, and the synthetic inputs whose tripwire must fire.
GOOGLE_SERP_SURFACE = "google_serp_us_parameterized"

_SERP_BLOCK_PAGE = (
    b"Our systems have detected unusual traffic from your computer network. "
    b"Please try your request again later."
)
_SERP_THIN_PAGE = b"Google\nSearch\n"

SURFACES = {
    GOOGLE_SERP_SURFACE: {
        "extractor": build_google_serp_content_record,
        "extractor_version": GOOGLE_SERP_CONTENT_RECORD_VERSION,
        "anomaly_type": GoogleSerpContentAnomaly,
        "minimum_rows": MINIMUM_ROW_COUNT,
        "rendered_dom_name": "01_cloakbrowser_rendered_dom.html",
        "visible_text_name": "02_cloakbrowser_visible_text.txt",
        "synthetic_cases": (
            (
                "unusual_traffic_interstitial",
                b"<html><body>" + _SERP_BLOCK_PAGE + b"</body></html>",
                _SERP_BLOCK_PAGE,
                "https://www.google.com/sorry/index",
            ),
            (
                "structurally_empty_page",
                b"<html><body>Google</body></html>",
                _SERP_THIN_PAGE,
                "https://www.google.com/search?q=example&hl=en&gl=us&pws=0",
            ),
        ),
    }
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reextract(surface: dict, rendered_dom: bytes, visible_text: bytes,
               final_url: str, requested_url: str | None) -> dict:
    return surface["extractor"](
        rendered_dom=rendered_dom,
        visible_text=visible_text,
        final_url=final_url,
        requested_url=requested_url,
    )


def run_packet_mode(
    *,
    surface_name: str,
    packet_root: Path,
    baseline_record_dir: Path | None,
    max_packets: int | None,
) -> ParityReport:
    surface = SURFACES[surface_name]
    report = ParityReport(surface=surface_name)
    manifests = sorted(packet_root.glob("*/manifest.json"))
    if max_packets is not None:
        manifests = manifests[:max_packets]

    for manifest_path in manifests:
        packet_dir = manifest_path.parent
        unit = packet_dir.name
        raw_dir = packet_dir / "raw"
        dom_path = raw_dir / surface["rendered_dom_name"]
        text_path = raw_dir / surface["visible_text_name"]
        if not dom_path.exists() or not text_path.exists():
            continue

        manifest = _load_json(manifest_path)
        requested_url = str(manifest.get("source_locator", {}).get("value", "")) or None
        final_url = _final_url_from_manifest(manifest) or requested_url or ""

        try:
            reextracted = _reextract(
                surface,
                dom_path.read_bytes(),
                text_path.read_bytes(),
                final_url,
                requested_url,
            )
        except surface["anomaly_type"] as exc:
            # A tripwire firing on a real capture is the DESIGNED outcome for a
            # blocked or degenerate page: that capture stays raw-preserving.
            report.units_anomalous += 1
            report.anomalies.append(f"{unit}: {type(exc).__name__}: {exc}")
            continue

        report.violations.extend(
            check_serp_invariants(
                unit=unit, record=reextracted, minimum_rows=surface["minimum_rows"]
            )
        )

        baseline = _baseline_for(packet_dir, baseline_record_dir)
        if baseline is None:
            report.units_without_baseline += 1
            continue

        report.units_compared += 1
        diffs = compare_records(unit=unit, baseline=baseline, reextracted=reextracted)
        if diffs:
            report.diffs.extend(diffs)
        else:
            report.units_identical += 1
    return report


def run_rolling_sample_mode(
    *, surface_name: str, raw_sample_root: Path
) -> ParityReport:
    surface = SURFACES[surface_name]
    report = ParityReport(surface=surface_name)
    store = RollingRawSampleStore(raw_sample_root)

    for entry in store.current_samples():
        if entry.get("surface") != surface_name:
            continue
        directory = Path(entry["directory"])
        unit = f"{entry.get('surface')}/{entry.get('sample_key')}"
        dom_path = directory / RENDERED_DOM_SAMPLE_FILENAME
        text_path = directory / VISIBLE_TEXT_SAMPLE_FILENAME
        record_path = directory / CONTENT_RECORD_SAMPLE_FILENAME
        if not (dom_path.exists() and text_path.exists() and record_path.exists()):
            report.anomalies.append(f"{unit}: sample directory is incomplete")
            continue

        banked = _load_json(record_path)
        try:
            reextracted = _reextract(
                surface,
                dom_path.read_bytes(),
                text_path.read_bytes(),
                str(banked.get("final_url", "")),
                str(banked.get("requested_url", "")) or None,
            )
        except surface["anomaly_type"] as exc:
            # A sample is only ever taken from a capture that DID extract, so a
            # tripwire firing here means the extractor edit broke this surface.
            report.units_anomalous += 1
            report.anomalies.append(
                f"{unit}: current extractor now raises {type(exc).__name__}: {exc}"
            )
            continue

        report.violations.extend(
            check_serp_invariants(
                unit=unit, record=reextracted, minimum_rows=surface["minimum_rows"]
            )
        )
        report.units_compared += 1
        diffs = compare_records(unit=unit, baseline=banked, reextracted=reextracted)
        if diffs:
            report.diffs.extend(diffs)
        else:
            report.units_identical += 1
    return report


def _final_url_from_manifest(manifest: dict) -> str:
    import re

    for warning in manifest.get("warnings", []) or []:
        match = re.search(r"landed at (\S+) from requested URL", str(warning))
        if match:
            return match.group(1)
    return ""


def _baseline_for(packet_dir: Path, baseline_record_dir: Path | None) -> dict | None:
    """Prefer the packet's own in-flight record; fall back to a lane baseline."""
    in_flight = packet_dir / "content_record.json"
    if in_flight.exists():
        return _load_json(in_flight)
    if baseline_record_dir is not None:
        candidate = baseline_record_dir / f"{packet_dir.name}.json"
        if candidate.exists():
            return _load_json(candidate)
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("packets", "rolling-sample"),
        help="packets: one-time pre-flip gate. rolling-sample: post-edit regression check.",
    )
    parser.add_argument("--surface", required=True, choices=sorted(SURFACES))
    parser.add_argument("--packet-root", type=Path, default=None)
    parser.add_argument("--baseline-record-dir", type=Path, default=None)
    parser.add_argument("--raw-sample-root", type=Path, default=None)
    parser.add_argument("--max-packets", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--skip-failure-path",
        action="store_true",
        help="Skip the synthetic tripwire exercise (reports it as not-run).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    surface = SURFACES[args.surface]

    if args.mode == "packets":
        if args.packet_root is None:
            raise SystemExit("packets mode requires --packet-root")
        report = run_packet_mode(
            surface_name=args.surface,
            packet_root=args.packet_root,
            baseline_record_dir=args.baseline_record_dir,
            max_packets=args.max_packets,
        )
    else:
        if args.raw_sample_root is None:
            raise SystemExit("rolling-sample mode requires --raw-sample-root")
        report = run_rolling_sample_mode(
            surface_name=args.surface, raw_sample_root=args.raw_sample_root
        )

    if args.skip_failure_path:
        failure_verdict, failure_notes = "not-run", []
    else:
        failure_verdict, failure_notes = exercise_failure_path(
            extractor=surface["extractor"],
            anomaly_type=surface["anomaly_type"],
            synthetic_cases=surface["synthetic_cases"],
        )

    verdicts = {
        "field_diff": report.field_diff_verdict,
        "surface_invariants": report.invariant_verdict,
        "failure_path": failure_verdict,
        "rolling_sample_integrity": (
            "fail"
            if args.mode == "rolling-sample" and report.anomalies
            else "pass"
            if args.mode == "rolling-sample" and report.units_compared > 0
            else "not-run"
        ),
    }
    gate_passed = all(verdict != "fail" for verdict in verdicts.values())
    result = {
        "gate": "capture_retention_parity_gate_v0",
        "mode": args.mode,
        "extractor_version": surface["extractor_version"],
        "verdicts": verdicts,
        "gate_passed": gate_passed,
        "failure_path_notes": failure_notes,
        "non_claims": [
            "parity with the current extractor is not a claim that the extractor "
            "is correct; it is a claim that the flip changes nothing",
            "a passing gate does not admit any capture as evidence",
        ],
        **report.as_dict(),
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
