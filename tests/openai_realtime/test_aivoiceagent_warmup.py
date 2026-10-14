"""AIVoiceAgent startup must not require a permanent model API token."""

from unittest.mock import MagicMock

import httpx
import pytest
from openai import AuthenticationError

from speech_to_speech.LLM.chat_completions_language_model import ChatCompletionsApiModelHandler


def _handler_without_setup(*, enabled: bool) -> ChatCompletionsApiModelHandler:
    # Model setup normally creates an OpenAI client and may perform warmup.
    # Test only the warmup contract, with a mock client and no network/model.
    handler = object.__new__(ChatCompletionsApiModelHandler)
    handler._aivoiceagent_enabled = enabled
    handler.client = MagicMock()
    handler.model_name = "aivoiceagent"
    handler._extra_body = None
    handler.request_timeout = httpx.Timeout(5.0)
    return handler


def test_java_live_mode_does_not_perform_unscoped_warmup():
    handler = _handler_without_setup(enabled=True)
    handler.warmup()
    handler.client.with_options.assert_not_called()


def test_missing_binding_env_returns_actionable_hint_when_java_rejects_warmup():
    handler = _handler_without_setup(enabled=False)
    request = httpx.Request("POST", "http://127.0.0.1:8080/v1/chat/completions")
    response = httpx.Response(401, request=request)
    handler.client.with_options.return_value.chat.completions.create.side_effect = AuthenticationError(
        "Invalid or expired Live credential",
        response=response,
        body={"code": "INVALID_LIVE_TOKEN", "message": "Invalid or expired Live credential"},
    )
    with pytest.raises(RuntimeError, match="AIVOICEAGENT_JAVA_BASE_URL") as exc:
        handler.warmup()
    assert "Do not configure a fixed model API token" in str(exc.value)


def test_other_model_auth_failures_are_not_masked():
    handler = _handler_without_setup(enabled=False)
    request = httpx.Request("POST", "https://example.org/v1/chat/completions")
    response = httpx.Response(401, request=request)
    original = AuthenticationError("invalid key", response=response, body={"code": "invalid_api_key"})
    handler.client.with_options.return_value.chat.completions.create.side_effect = original
    with pytest.raises(AuthenticationError) as raised:
        handler.warmup()
    assert raised.value is original
