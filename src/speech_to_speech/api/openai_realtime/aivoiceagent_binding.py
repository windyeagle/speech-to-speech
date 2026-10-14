"""Optional AIVoiceAgent Live binding. Disabled unless explicitly configured.

The browser receives a scoped, expiring Live token from the authenticated Java
controller. During the WS/WebRTC handshake S2S validates it against that
controller. It is then attached only to the S2S -> Java Chat Completions call,
not sent to unrelated LLM services or echoed in session.updated.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

import httpx

TOKEN_QUERY_KEY = "aivoiceagent_token"


def java_base_url() -> str | None:
    value = os.environ.get("AIVOICEAGENT_JAVA_BASE_URL", "").strip().rstrip("/")
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RuntimeError("AIVOICEAGENT_JAVA_BASE_URL must be an absolute HTTP(S) URL")
    return value


def enabled() -> bool:
    return java_base_url() is not None


def target_is_java(base_url: str | None) -> bool:
    expected = java_base_url()
    if expected is None:
        return False
    return bool(base_url and base_url.rstrip("/") == expected + "/v1")


def normalize_token(token: str | None) -> str | None:
    if token is None or len(token) != 43:
        return None
    if not all(c.isascii() and (c.isalnum() or c in "_-") for c in token):
        return None
    return token


def bearer_from_header(header: str | None) -> str | None:
    if not header or not header.startswith("Bearer "):
        return None
    return normalize_token(header[7:].strip())


async def verify_live_token(token: str | None, client: httpx.AsyncClient | None = None) -> bool:
    token = normalize_token(token)
    endpoint = java_base_url()
    if not endpoint or not token:
        return False
    async def request_with(http: httpx.AsyncClient) -> bool:
        try:
            response = await http.post(
                endpoint + "/api/v1/internal/live/verify",
                headers={"Authorization": "Bearer " + token},
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False

    if client is not None:
        return await request_with(client)
    async with httpx.AsyncClient(timeout=3.0, trust_env=False) as http:
        return await request_with(http)


def java_turn_headers(token: str | None, response_key: str | None, base_url: str | None) -> dict[str, str]:
    if not target_is_java(base_url):
        raise RuntimeError("AIVoiceAgent mode requires Chat Completions URL to match Java /v1")
    validated = normalize_token(token)
    if validated is None:
        raise RuntimeError("AIVoiceAgent Live authentication missing on current realtime session")
    headers = {"Authorization": "Bearer " + validated}
    if response_key:
        headers["X-AIVoiceAgent-Turn-Key"] = response_key[:160]
    return headers
