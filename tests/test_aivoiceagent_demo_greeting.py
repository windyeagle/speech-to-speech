"""The Java-bound demo must never emit synthetic USER opening turns."""

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "demo" / "aivoiceagent_demo.py"
_SPEC = importlib.util.spec_from_file_location("aivoiceagent_demo_config_test", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_java_live_url_disables_bootstrap_user_prompt():
    assert _MODULE.is_aivoiceagent_live_url("ws://127.0.0.1:8765/v1/realtime?aivoiceagent_token=fake-secret")
    assert _MODULE.is_aivoiceagent_live_url("wss://localhost:8765/v1/realtime?foo=1&aivoiceagent_token=synthetic")


def test_generic_demo_remains_unchanged():
    assert not _MODULE.is_aivoiceagent_live_url("ws://127.0.0.1:8765/v1/realtime?foo=1")
    assert not _MODULE.is_aivoiceagent_live_url("")
