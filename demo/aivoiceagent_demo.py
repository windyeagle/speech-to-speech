"""Pure configuration helper for the local S2S H5 demonstration.

The presence of a scoped AIVoiceAgent Live credential means Java is the
authoritative conversational controller. Never send the demo greeting as an
ordinary user input in that mode.
"""
from urllib.parse import parse_qsl, urlsplit


def is_aivoiceagent_live_url(s2s_url: str) -> bool:
    if not s2s_url:
        return False
    try:
        return any(name == "aivoiceagent_token" for name, _ in
                   parse_qsl(urlsplit(s2s_url).query, keep_blank_values=True))
    except ValueError:
        return False
