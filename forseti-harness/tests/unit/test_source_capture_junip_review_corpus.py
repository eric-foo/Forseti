from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from runners import run_source_capture_junip_review_corpus as runner


def _review(review_id: str, *, body: str, remote_id: str = "product-1") -> dict:
    return {
        "id": review_id,
        "body": body,
        "product": {"remote_id": remote_id},
        "store": {"name": "Experiment", "url": "https://experimentbeauty.com"},
    }


def test_capture_exhausts_cursor_pagination_and_omits_store_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    requested_urls: list[str] = []
    staged: dict[str, object] = {}
    responses = [
        {"data": [{"remote_id": "product-1"}]},
        {"data": [_review("r1", body="Hydrating"), _review("r2", body="")], "meta": {"after": "next"}},
        {"data": [_review("r3", body="Soothing")], "meta": {"after": None}},
    ]

    def fake_fetch(url: str, store_key: str, timeout_seconds: float) -> tuple[bytes, dict]:
        requested_urls.append(url)
        assert store_key == "public-store-key"
        assert timeout_seconds == 12.0
        payload = responses.pop(0)
        raw = json.dumps(payload).encode()
        return raw, {
            "requested_url": url,
            "final_url": url,
            "status": 200,
            "content_type": "application/json",
            "bytes": len(raw),
        }

    def fake_stage(**kwargs: object) -> SimpleNamespace:
        staged.update(kwargs)
        return SimpleNamespace(output_directory=str(tmp_path / "packet"))

    monkeypatch.setattr(runner, "_fetch_json", fake_fetch)
    monkeypatch.setattr(runner, "stage_and_write_packet", fake_stage)
    monkeypatch.setattr(
        runner,
        "staged_file_id_map",
        lambda artifacts: {name: f"file_{index:02d}" for index, (name, _) in enumerate(artifacts, 1)},
    )

    packet, review_count, text_count = runner.capture_junip_review_corpus(
        store_key="public-store-key",
        expected_store_name="Experiment",
        expected_store_url="https://experimentbeauty.com",
        data_root=object(),  # type: ignore[arg-type]
        timeout_seconds=12.0,
    )

    assert packet == str(tmp_path / "packet")
    assert review_count == 3
    assert text_count == 2
    assert "page_after=next" in requested_urls[-1]
    artifacts = staged["staged_artifacts"]
    assert isinstance(artifacts, list)
    request_manifest = json.loads(dict(artifacts)["request_manifest.json"])
    assert request_manifest["pagination_exhausted"] is True
    assert request_manifest["review_page_count"] == 2
    assert request_manifest["review_count"] == 3
    preserved_text = b"\n".join(body for _, body in artifacts).decode(
        "utf-8", errors="replace"
    )
    assert "public-store-key" not in preserved_text


def test_capture_rejects_duplicate_review_ids_across_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {"data": [{"remote_id": "product-1"}]},
        {"data": [_review("duplicate", body="one")], "meta": {"after": "next"}},
        {"data": [_review("duplicate", body="two")], "meta": {"after": None}},
    ]

    def fake_fetch(url: str, store_key: str, timeout_seconds: float) -> tuple[bytes, dict]:
        del store_key, timeout_seconds
        raw = json.dumps(responses.pop(0)).encode()
        return raw, {"requested_url": url, "final_url": url, "status": 200}

    monkeypatch.setattr(runner, "_fetch_json", fake_fetch)

    with pytest.raises(ValueError, match="duplicated review id duplicate"):
        runner.capture_junip_review_corpus(
            store_key="public-store-key",
            expected_store_name="Experiment",
            expected_store_url="https://experimentbeauty.com",
            data_root=object(),  # type: ignore[arg-type]
        )
