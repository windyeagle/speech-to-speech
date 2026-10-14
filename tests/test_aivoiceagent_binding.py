"""Offline AIVoiceAgent optional adapter tests. No S2S model download needed."""

import asyncio

import httpx
import pytest

from speech_to_speech.api.openai_realtime.aivoiceagent_binding import (
    bearer_from_header,
    enabled,
    java_base_url,
    java_turn_headers,
    normalize_token,
    target_is_java,
    verify_live_token,
)

TOKEN = "A" * 43


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AIVOICEAGENT_JAVA_BASE_URL", raising=False)
    assert not enabled()
    assert java_base_url() is None
    with pytest.raises(RuntimeError):
        java_turn_headers(TOKEN, "turn-1", "http://127.0.0.1:8080/v1")


def test_no_cross_provider_token_leak(monkeypatch):
    monkeypatch.setenv("AIVOICEAGENT_JAVA_BASE_URL", "http://127.0.0.1:8080")
    assert enabled()
    assert target_is_java("http://127.0.0.1:8080/v1/")
    assert not target_is_java("https://api.openai.com/v1")
    with pytest.raises(RuntimeError):
        java_turn_headers(TOKEN, "r-1", "https://api.openai.com/v1")
    with pytest.raises(RuntimeError):
        java_turn_headers(None, "r-1", "http://127.0.0.1:8080/v1")
    assert java_turn_headers(TOKEN, "r-1", "http://127.0.0.1:8080/v1") == {
        "Authorization": "Bearer " + TOKEN,
        "X-AIVoiceAgent-Turn-Key": "r-1",
    }


def test_token_formats():
    assert normalize_token(TOKEN) == TOKEN
    assert normalize_token("bad") is None
    assert normalize_token(" " * 43) is None
    assert bearer_from_header("Bearer " + TOKEN) == TOKEN
    assert bearer_from_header("Basic x") is None


def test_handshake_validation_is_scoped(monkeypatch):
    monkeypatch.setenv("AIVOICEAGENT_JAVA_BASE_URL", "http://127.0.0.1:8080")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.path == "/api/v1/internal/live/verify"
        return httpx.Response(200 if request.headers.get("authorization") == "Bearer " + TOKEN else 401)

    async def check():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            assert await verify_live_token(TOKEN, client=http)
            assert not await verify_live_token("B" * 43, client=http)
            assert not await verify_live_token("bad", client=http)

    asyncio.run(check())
    assert len(calls) == 2
