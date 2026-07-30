"""Retention decision for rendered captures, incl. the never-raw-only boundary."""

from __future__ import annotations

import json

import pytest

from source_capture.content_extraction import RenderedContentExtractionSpec
from source_capture.rendered_retention import (
    RenderedRetentionError,
    require_content_retention,
    resolve_rendered_retention,
)

DOM = b"<html><body>rows</body></html>"
TEXT = b"visible text"
URL = "https://www.reddit.com/r/testsub/top/?t=week"


def _spec(mode: str = "content", *, extractor=None) -> RenderedContentExtractionSpec:
    return RenderedContentExtractionSpec(
        requested_retention_mode=mode,
        extractor_version="www-2",
        extractor=extractor or (lambda _dom, _text, _url: {"rows": 2}),
    )


def _resolve(**overrides):
    kwargs = {
        "spec": _spec(),
        "rendered_dom": DOM,
        "visible_text": TEXT,
        "final_url": URL,
        "admission_failed": False,
    }
    kwargs.update(overrides)
    return resolve_rendered_retention(**kwargs)


def test_successful_extraction_publishes_content_and_drops_raw() -> None:
    decision = _resolve()
    assert decision.retention_outcome == "content"
    assert decision.raw_inputs_preserved is False
    assert json.loads(decision.content_record_bytes) == {"rows": 2}


def test_dropped_raw_keeps_its_provenance() -> None:
    """Releasing raw is only acceptable while proof of what was released survives."""
    decision = _resolve()
    discarded = decision.provenance["discarded_inputs"]
    assert discarded["rendered_dom"]["byte_count"] == len(DOM)
    assert discarded["visible_text"]["byte_count"] == len(TEXT)
    assert len(discarded["rendered_dom"]["sha256"]) == 64
    assert decision.provenance["extractor_version"] == "www-2"
    assert decision.provenance["content_record"]["byte_count"] > 0


def test_audit_sample_keeps_raw_alongside_content_not_instead_of_it() -> None:
    decision = _resolve(keep_raw_audit_sample=True)
    assert decision.retention_outcome == "raw_sample"
    assert decision.raw_inputs_preserved is True
    assert decision.carries_content is True


def test_extraction_failure_falls_back_to_raw_and_names_the_failure() -> None:
    def _boom(_dom, _text, _url):
        raise ValueError("projection anomaly [no_thread_rows]")

    decision = _resolve(spec=_spec(extractor=_boom))
    assert decision.retention_outcome == "raw_failure"
    assert decision.raw_inputs_preserved is True
    assert decision.content_record_bytes is None
    assert "no_thread_rows" in decision.extraction_failure_or_none


def test_non_dict_extractor_result_is_a_failure_not_a_packet() -> None:
    decision = _resolve(spec=_spec(extractor=lambda _d, _t, _u: ["not", "a", "record"]))
    assert decision.retention_outcome == "raw_failure"
    assert "TypeError" in decision.extraction_failure_or_none


def test_admission_failure_withholds_an_otherwise_valid_record() -> None:
    """A clean projection OF A BLOCK SHELL must not ship as source content."""
    decision = _resolve(admission_failed=True)
    assert decision.retention_outcome == "raw_failure"
    assert decision.content_record_bytes is None
    assert decision.extraction_failure_or_none is None
    # The attempt stays auditable even though the record is withheld.
    assert decision.provenance["content_record"]["byte_count"] > 0
    assert decision.provenance["content_record_withheld"]


def test_no_spec_is_raw_and_is_what_the_boundary_must_refuse() -> None:
    decision = _resolve(spec=None)
    assert decision.retention_outcome == "raw"
    assert decision.raw_inputs_preserved is True


def test_require_content_retention_refuses_a_missing_spec() -> None:
    with pytest.raises(RenderedRetentionError) as excinfo:
        require_content_retention(None, lane="reddit www grid")
    assert excinfo.value.code == "content_extraction_required"


def test_require_content_retention_refuses_an_operator_raw_request() -> None:
    with pytest.raises(RenderedRetentionError) as excinfo:
        require_content_retention(_spec("raw"), lane="reddit www grid")
    assert excinfo.value.code == "raw_only_retention_refused"


def test_require_content_retention_passes_a_content_spec_through() -> None:
    spec = _spec()
    assert require_content_retention(spec, lane="reddit www grid") is spec
