"""Shared, injectable raw-HTTP model transport helpers.

This module owns provider plumbing only. It contains no audience inference,
prompt, or semantic claim logic.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlparse


class RawApiProvider(StrEnum):
    OPENAI_RESPONSES = "openai_responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"


_STANDARD_ENDPOINTS = {
    RawApiProvider.OPENAI_RESPONSES: ("api.openai.com", "/v1/responses"),
    RawApiProvider.ANTHROPIC_MESSAGES: ("api.anthropic.com", "/v1/messages"),
}
_FORBIDDEN_REQUEST_KEYS = {
    "tools", "tool", "tool_choice", "functions", "function_call", "system",
    "developer", "instructions", "web_search", "search", "retrieval", "browser",
    "file", "files", "file_ids", "attachments", "mcp_servers", "connectors",
}


class Transport(Protocol):
    def post_json(
        self, url: str, headers: dict[str, str], body: dict[str, Any], timeout_seconds: float
    ) -> str: ...


def build_request_body(
    provider: RawApiProvider, *, model: str, prompt: str, max_tokens: int = 1024
) -> dict[str, Any]:
    if not model.strip():
        raise ValueError("model id must be a non-empty string")
    if provider == RawApiProvider.ANTHROPIC_MESSAGES:
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    elif provider == RawApiProvider.OPENAI_RESPONSES:
        body = {"model": model, "input": prompt, "max_output_tokens": max_tokens}
    else:
        raise ValueError(f"unsupported provider: {provider}")
    forbidden = _FORBIDDEN_REQUEST_KEYS & set(body)
    if forbidden:
        raise ValueError(f"request body contains forbidden tool/context keys: {sorted(forbidden)}")
    return body


def build_headers(provider: RawApiProvider, api_key: str) -> dict[str, str]:
    if not api_key.strip():
        raise ValueError("api key must be non-empty")
    if provider == RawApiProvider.ANTHROPIC_MESSAGES:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    if provider == RawApiProvider.OPENAI_RESPONSES:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    raise ValueError(f"unsupported provider: {provider}")


def default_endpoint(provider: RawApiProvider) -> str:
    host, path = _STANDARD_ENDPOINTS[provider]
    return f"https://{host}{path}"


def validate_endpoint(provider: RawApiProvider, api_url: str) -> None:
    host, path = _STANDARD_ENDPOINTS[provider]
    parsed = urlparse(api_url)
    if parsed.scheme != "https" or parsed.hostname != host or parsed.path != path:
        raise ValueError(f"endpoint must be https://{host}{path} for {provider.value}")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError("endpoint must not include params, query, or fragment")


def parse_response_body(raw_response_body: str) -> dict[str, Any]:
    """Decode the provider envelope once for text extraction and usage accounting."""
    try:
        data = json.loads(raw_response_body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"provider response was not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("provider response JSON must be an object")
    return data


def extract_model_text_from_response(provider: RawApiProvider, data: dict[str, Any]) -> str:
    """Extract text from an already decoded provider envelope."""
    if provider == RawApiProvider.ANTHROPIC_MESSAGES:
        chunks = [
            item["text"]
            for item in data.get("content", [])
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
    elif provider == RawApiProvider.OPENAI_RESPONSES:
        if isinstance(data.get("output_text"), str):
            chunks = [data["output_text"]]
        else:
            chunks = [
                content["text"]
                for item in data.get("output", [])
                if isinstance(item, dict)
                for content in item.get("content", [])
                if isinstance(content, dict) and isinstance(content.get("text"), str)
            ]
    else:
        raise ValueError(f"unsupported provider: {provider}")
    text = "".join(chunks)
    if not text.strip():
        raise ValueError("provider response did not contain non-empty model text")
    return text


def extract_model_text(provider: RawApiProvider, raw_response_body: str) -> str:
    return extract_model_text_from_response(provider, parse_response_body(raw_response_body))


__all__ = [
    "RawApiProvider", "Transport", "build_headers", "build_request_body",
    "default_endpoint", "extract_model_text", "extract_model_text_from_response",
    "parse_response_body", "validate_endpoint",
]
