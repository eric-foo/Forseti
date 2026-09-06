"""Offline, real-lake checks for the provider-to-persisted-output measurement boundary."""

from __future__ import annotations

import hashlib
import json

import pytest

from cleaning.raw_model_transport import RawApiProvider, extract_model_text
from cleaning.transcript_product_extractor import (
    TranscriptInput, build_extraction_prompt, extract_transcript_products, parse_mentions,
)
from cleaning.transcript_product_lake import (
    PRODUCT_MENTIONS_LANE, build_transcript_source_lineage, extract_products_into_lake,
    write_product_mentions_result_into_lake,
)
from data_lake.root import DataLakeRoot
from data_lake.silver_lineage import SilverDerivedRef


ITEM = {"brand": "Dior", "line": "Sauvage", "source_pointer": "Dior Sauvage is great",
        "concentration": "unknown", "stance_vote": 0.8, "extractor_confidence": 0.9}


class Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_json(self, url, headers, body, timeout_seconds):
        self.calls.append(body)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


@pytest.fixture
def measured(tmp_path, monkeypatch):
    directory = tmp_path / "measurements"
    monkeypatch.setenv("FORSETI_EFFICIENCY_DIR", str(directory))
    monkeypatch.setenv("FORSETI_EFFICIENCY_REVISION", "test-revision")
    return directory


def transcript(lake=None):
    anchor = "MEASUREDTRANSCRIPT01"
    body = b'{"kind":"transcript_fixture"}'
    if lake is not None:
        lake.append_record(subtree="derived", raw_anchor=anchor, lane="transcript_asr",
                           record_id="source.json", data=body)
    lineage = build_transcript_source_lineage(
        namespace="youtube", source_surface="youtube_audio", video_id="video123456",
        captured_at="2026-09-01T00:00:00Z",
        derived_ref=SilverDerivedRef(raw_anchor=anchor, lane="transcript_asr",
                                    record_id="source.json", sha256=hashlib.sha256(body).hexdigest(),
                                    hash_basis="derived_record_bytes"),
    )
    return TranscriptInput("video123456", anchor, "asr",
                           [{"text": "Dior Sauvage is great", "start_ms": 0, "end_ms": 2000}],
                           source_lineage=lineage)


def response(provider=RawApiProvider.OPENAI_RESPONSES, usage=None, model_text=None):
    text = json.dumps([ITEM]) if model_text is None else model_text
    data = ({"output_text": text} if provider == RawApiProvider.OPENAI_RESPONSES
            else {"content": [{"type": "text", "text": text}]})
    if usage is not None:
        data["usage"] = usage
    return json.dumps(data)


def record(directory):
    paths = list(directory.glob("*.json"))
    assert len(paths) == 1, "A whole extraction must emit exactly one sidecar"
    return json.loads(paths[0].read_text(encoding="utf-8"))


def extract(transcript_input, transport, **kwargs):
    return extract_transcript_products(transcript_input, transport=transport,
                                       provider=RawApiProvider.OPENAI_RESPONSES,
                                       model="test-model", api_key="private-test-key", **kwargs)


@pytest.mark.parametrize(("provider", "usage", "expected"), [
    (RawApiProvider.OPENAI_RESPONSES,
     {"input_tokens": 100, "input_tokens_details": {"cached_tokens": 40},
      "output_tokens": 30, "output_tokens_details": {"reasoning_tokens": 10}, "total_tokens": 130},
     {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 30,
      "reasoning_output_tokens": 10, "total_tokens": 130}),
    (RawApiProvider.ANTHROPIC_MESSAGES,
     {"input_tokens": 60, "cache_read_input_tokens": 40, "cache_creation_input_tokens": 20,
      "output_tokens": 30},
     {"input_tokens": 120, "cached_input_tokens": 40, "cache_write_input_tokens": 20,
      "output_tokens": 30, "total_tokens": 150}),
])
def test_full_boundary_usage_and_unchanged_persisted_payload(tmp_path, measured, provider, usage, expected):
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    source = transcript(lake)
    wire = Transport(response(provider, usage))
    paths = extract_products_into_lake(data_root=lake, transcript=source, transport=wire,
                                      provider=provider, model="test-model", api_key="private-test-key")
    actual_bytes = paths[PRODUCT_MENTIONS_LANE].read_bytes()
    # The uninstrumented writer remains the authority for every persisted payload byte.
    reference_lake = DataLakeRoot.for_test(tmp_path / "reference")
    reference_source = transcript(reference_lake)
    reference_paths = write_product_mentions_result_into_lake(
        data_root=reference_lake, transcript=reference_source,
        result=parse_mentions(json.dumps([ITEM]), reference_source, model="test-model"),
        model="test-model", extraction_backend="provider_api",
    )
    assert actual_bytes == reference_paths[PRODUCT_MENTIONS_LANE].read_bytes()
    measured_run = record(measured)
    assert measured_run["outcome"] == "success"
    assert measured_run["workflow"] == "transcript_products_into_lake"
    assert measured_run["measurement_errors"] == []
    assert not measured_run["workload_id"].startswith("unknown-")
    assert set(measured_run["stages"]) == {
        "input_identity", "input_prepare", "provider_request", "provider_response_parse",
        "mention_parse", "lake_write", "persisted_verify",
    }
    assert len(measured_run["attempts"]) == 1
    attempt = measured_run["attempts"][0]
    assert attempt["elapsed_seconds"] >= 0
    assert attempt["usage"]["coverage"] == "complete"
    for key, value in expected.items():
        assert attempt["usage"][key] == value
    assert measured_run["quality"]["status"] == "passed"
    assert measured_run["quality"]["output_fingerprint"] == hashlib.sha256(actual_bytes).hexdigest()
    assert measured_run["quality"]["oracle"] == "silver_validated_write_and_marker_sha256_v1"
    serialized = json.dumps(measured_run)
    assert "private-test-key" not in serialized
    assert ITEM["source_pointer"] not in serialized
    assert len(wire.calls) == 1
    prompt = build_extraction_prompt(source)
    assert wire.calls[0].get("input", wire.calls[0].get("messages", [{}])[0].get("content")) == prompt


def test_direct_extraction_missing_usage_and_compatibility(measured):
    raw = response()
    result = extract(transcript(), Transport(raw))
    assert len(result.mentions) == 1
    assert extract_model_text(RawApiProvider.OPENAI_RESPONSES, raw) == json.dumps([ITEM])
    measured_run = record(measured)
    assert measured_run["workflow"] == "transcript_extract"
    assert measured_run["attempts"][0]["usage"]["coverage"] == "unknown"
    assert measured_run["attempts"][0]["usage"]["total_tokens"] is None


@pytest.mark.parametrize(("wire_response", "exception_type", "known_usage"), [
    (RuntimeError("provider rejected request"), RuntimeError, False),
    ("not JSON", ValueError, False),
    (response(usage={"input_tokens": 100, "output_tokens": 20}, model_text="not JSON"), ValueError, True),
    (json.dumps({"usage": {"input_tokens": 100, "output_tokens": 20}}), ValueError, True),
])
def test_provider_and_parse_failures_are_preserved(measured, wire_response, exception_type, known_usage):
    with pytest.raises(exception_type) as caught:
        extract(transcript(), Transport(wire_response))
    if isinstance(wire_response, BaseException):
        assert caught.value is wire_response
    measured_run = record(measured)
    assert measured_run["outcome"] == "failed"
    assert len(measured_run["attempts"]) == 1
    assert (measured_run["attempts"][0]["usage"]["total_tokens"] == 120) is known_usage


def test_lake_failure_retains_actual_provider_usage(tmp_path, measured):
    source = transcript()
    source.source_lineage = None
    with pytest.raises(ValueError, match="exact transcript lineage"):
        extract_products_into_lake(data_root=DataLakeRoot.for_test(tmp_path / "lake"),
                                  transcript=source, transport=Transport(response(usage={"input_tokens": 10, "output_tokens": 5})),
                                  provider=RawApiProvider.OPENAI_RESPONSES, model="test-model", api_key="key")
    measured_run = record(measured)
    assert measured_run["outcome"] == "failed"
    assert measured_run["attempts"][0]["usage"]["total_tokens"] == 15


@pytest.mark.parametrize("fails", [False, True])
def test_sidecar_write_failure_is_visible_without_replacing_result(measured, capsys, fails):
    measured.write_text("a file cannot serve as the output directory", encoding="utf-8")
    original = RuntimeError("original provider failure")
    if fails:
        with pytest.raises(RuntimeError) as caught:
            extract(transcript(), Transport(original))
        assert caught.value is original
    else:
        result = extract(transcript(), Transport(response()))
        assert len(result.mentions) == 1
    assert "efficiency measurement unavailable" in capsys.readouterr().err


def test_persisted_readback_failure_is_visible_without_fake_write_failure(tmp_path, measured, monkeypatch, capsys):
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    source = transcript(lake)
    def cannot_verify(*args, **kwargs):
        raise OSError("readback unavailable")
    monkeypatch.setattr(DataLakeRoot, "read_record_set_member_sha256", cannot_verify)
    paths = extract_products_into_lake(data_root=lake, transcript=source, transport=Transport(response()),
                                      provider=RawApiProvider.OPENAI_RESPONSES, model="test-model", api_key="key")
    assert paths[PRODUCT_MENTIONS_LANE].is_file()
    measured_run = record(measured)
    assert measured_run["outcome"] == "success"
    assert measured_run["quality"]["status"] == "failed"
    assert "efficiency measurement unavailable" in capsys.readouterr().err


def test_sidecar_failure_after_real_lake_write_preserves_written_paths(tmp_path, measured, capsys):
    lake = DataLakeRoot.for_test(tmp_path / "lake")
    source = transcript(lake)
    measured.write_text("blocked directory", encoding="utf-8")
    paths = extract_products_into_lake(data_root=lake, transcript=source, transport=Transport(response()),
                                      provider=RawApiProvider.OPENAI_RESPONSES, model="test-model", api_key="key")
    assert paths[PRODUCT_MENTIONS_LANE].is_file()
    assert "efficiency measurement unavailable" in capsys.readouterr().err


def test_unserializable_unused_input_does_not_create_product_failure(measured, capsys):
    source = transcript()
    source.cues[0]["unused"] = object()
    result = extract(source, Transport(response()))
    assert len(result.mentions) == 1
    measured_run = record(measured)
    assert measured_run["outcome"] == "success"
    assert measured_run["workload_id"].startswith("unknown-")
    assert measured_run["measurement_errors"] == ["input_identity:TypeError"]
    assert "efficiency measurement unavailable" in capsys.readouterr().err
