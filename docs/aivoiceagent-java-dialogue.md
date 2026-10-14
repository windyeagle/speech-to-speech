# AIVoiceAgent Java Dialogue Adapter (opt-in, direct S2S)

This feature is **disabled unless** `AIVOICEAGENT_JAVA_BASE_URL` is supplied to the S2S server. No built-in model routes or existing demo configs are changed by default.

## How it works

1. Authenticated Java API creates Chat -> Service -> Live; only the initial Live POST returns a 43-character expiring `realtimeToken`.
2. H5 starts its S2S Realtime WebSocket with `?aivoiceagent_token=<realtimeToken>` or WebRTC offer with the same query parameter (the current demo proxy preserves query strings). **Demo only**: avoid query-based credentials outside loopback HTTPS/WSS testing.
3. On connection S2S POSTs `Authorization: Bearer <token>` to Java `/api/v1/internal/live/verify`; rejects invalid sessions *before* claiming a pipeline slot.
4. S2S binds this token to the server-side Realtime RuntimeConfig (not to mutable `session.update`).
5. The Chat Completions LLM backend forwards the bound bearer + response key to Java `/v1/chat/completions`. It cannot send credentials to other LLM endpoints in this mode.
6. Java uses authoritative Chat history and final user text only, calls local Ollama and streams OpenAI Chat Completion SSE back to S2S for its unchanged TTS stage. User transcript and successfully completed answer are saved to Java.
7. Interrupting the speech closes a model response stream; Java marks incomplete/cancelled turns instead of storing incomplete assistant text. **Stopping remote Ollama compute is not fully verified yet.**

## S2S launch configuration

```bash
# First start the Java backend in 'demo' profile with AIVOICEAGENT_DEMO_USERNAME/
# PASSWORD, and create Chat, Service, Live via REST as documented in the
# private project. Ollama stays local at 127.0.0.1:11434.

export AIVOICEAGENT_JAVA_BASE_URL=http://127.0.0.1:8080
# Run the S2S server from this fork, not an older installed package.
uv run speech-to-speech serve \
  --llm_backend chat-completions \
  --model_name aivoiceagent \
  --responses_api_base_url http://127.0.0.1:8080/v1 \
  --responses_api_api_key none
```

The Chat Completions startup warmup is skipped in this explicitly enabled mode, because no authenticated Live yet exists. Disable speculative/compaction settings for the initial integrated POC if your current launch used them. Keep ASR and TTS on the original Mac MLX-Audio services via their existing flags; do not replace them.

## H5 demo

Example *single-user local* demo configuration (not production):

```bash
export SPEECH_TO_SPEECH_URL="ws://127.0.0.1:8765/v1/realtime?aivoiceagent_token=<token>"
uv run uvicorn --app-dir demo server:app --port 7860 --host 127.0.0.1
```

The demo's WebSocket connects to the configured URL and its WebRTC SDP proxy preserves the query string when constructing `/v1/realtime/calls`. `STARTUP_GREETING=` is recommended to avoid persisting hidden demo greeting instructions as a user utterance.

**Privacy caveat:** The demo exposes `SPEECH_TO_SPEECH_URL` via `/api/config`. Keep this POC bound to loopback; never use this deployment strategy on a shared host. Production requires a dedicated H5 auth integration, header/subprotocol credentials, HTTPS/WSS, token rotation, multi-device ownership checks and transport revocation.

## Unimplemented / planned

- Proper Java↔S2S media-session lifecycle callbacks, transport teardown, playback acknowledgements and end-to-end cancellation.
- Partner engines, knowledge API, Laya decisions, STACS policy approval, ticket creation and human FreeSWITCH routing.
- Production load capacity, personal data compliance, identity provider integration, on-prem Kylin ARM64.
