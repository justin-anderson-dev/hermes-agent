"""Tests for route-level enabled_toolsets override on webhook subscriptions.

ALF-349: webhook routes (e.g. ``kanban-completion``) need to opt into local
toolsets like ``terminal`` and ``file`` even though the platform default
``hermes-webhook`` does not include them. The route stores a list of toolset
names in its config; the adapter copies that list onto the dispatched
``MessageEvent``; the gateway honours it instead of the platform default when
spinning up the agent.
"""

import asyncio
import json
import sys
import threading
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import gateway.run as gateway_run
from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import MessageEvent
from gateway.platforms.webhook import WebhookAdapter, _INSECURE_NO_AUTH
from gateway.session import SessionSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter(routes) -> WebhookAdapter:
    return WebhookAdapter(
        PlatformConfig(
            enabled=True,
            extra={"host": "127.0.0.1", "port": 0, "routes": routes},
        )
    )


def _create_app(adapter: WebhookAdapter) -> web.Application:
    app = web.Application()
    app.router.add_post("/webhooks/{route_name}", adapter._handle_webhook)
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRouteEnabledToolsets:

    @pytest.mark.asyncio
    async def test_route_enabled_toolsets_propagate_to_message_event(self):
        """A route configured with enabled_toolsets pushes that list onto
        the MessageEvent that handle_message receives, so the gateway can
        override the platform default at agent-spawn time."""
        routes = {
            "kanban-completion": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "Kanban event: {__raw__}",
                "skills": ["kanban-completion-handler"],
                "enabled_toolsets": ["terminal", "file", "skills"],
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        captured: list[MessageEvent] = []

        async def _capture(event: MessageEvent):
            captured.append(event)

        adapter.handle_message = _capture

        app = _create_app(adapter)
        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/kanban-completion",
                json={
                    "event_type": "kanban.gave_up",
                    "board": "code-ops",
                    "task_id": "t_test_001",
                },
                headers={"X-GitHub-Delivery": "kanban-test-1"},
            )
            assert resp.status == 202

        await asyncio.sleep(0.05)
        assert len(captured) == 1
        event = captured[0]
        assert event.enabled_toolsets == ["terminal", "file", "skills"]
        assert event.disabled_toolsets is None

    @pytest.mark.asyncio
    async def test_route_disabled_toolsets_propagate_to_message_event(self):
        """A route's disabled_toolsets list also rides on the MessageEvent."""
        routes = {
            "noisy-source": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "Event: {__raw__}",
                "enabled_toolsets": ["terminal", "file"],
                "disabled_toolsets": ["web", "vision"],
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        captured: list[MessageEvent] = []

        async def _capture(event: MessageEvent):
            captured.append(event)

        adapter.handle_message = _capture

        app = _create_app(adapter)
        async with TestClient(TestServer(app)) as cli:
            await cli.post(
                "/webhooks/noisy-source",
                json={"k": "v"},
                headers={"X-GitHub-Delivery": "noisy-1"},
            )
        await asyncio.sleep(0.05)
        assert captured[0].enabled_toolsets == ["terminal", "file"]
        assert captured[0].disabled_toolsets == ["web", "vision"]

    @pytest.mark.asyncio
    async def test_route_without_toolsets_leaves_event_none(self):
        """Backward compatibility: routes that don't set the new fields
        produce events with ``enabled_toolsets`` left as ``None`` so the
        gateway falls back to the platform default."""
        routes = {
            "legacy": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "Legacy event",
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        captured: list[MessageEvent] = []

        async def _capture(event: MessageEvent):
            captured.append(event)

        adapter.handle_message = _capture

        app = _create_app(adapter)
        async with TestClient(TestServer(app)) as cli:
            await cli.post(
                "/webhooks/legacy",
                json={"k": "v"},
                headers={"X-GitHub-Delivery": "legacy-1"},
            )
        await asyncio.sleep(0.05)
        assert captured[0].enabled_toolsets is None
        assert captured[0].disabled_toolsets is None

    @pytest.mark.asyncio
    async def test_route_with_malformed_enabled_toolsets_is_ignored(self):
        """If the saved metadata is e.g. a string instead of a list, the
        adapter falls back to no override rather than crashing the request.
        Startup validation (``connect``) is responsible for surfacing this
        as an error to the operator; the per-request build path must remain
        defensive so a bad dynamic-route edit cannot 500 every webhook."""
        routes = {
            "broken": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "Broken event",
                "enabled_toolsets": "terminal,file",  # string, not list
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        captured: list[MessageEvent] = []

        async def _capture(event: MessageEvent):
            captured.append(event)

        adapter.handle_message = _capture

        app = _create_app(adapter)
        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/broken",
                json={"k": "v"},
                headers={"X-GitHub-Delivery": "broken-1"},
            )
            assert resp.status == 202
        await asyncio.sleep(0.05)
        assert captured[0].enabled_toolsets is None

    @pytest.mark.asyncio
    async def test_connect_rejects_non_list_enabled_toolsets(self):
        """A misconfigured route ('terminal,file' as a string) fails fast
        at startup with a clear message — same posture as missing secrets."""
        routes = {
            "broken": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "x",
                "enabled_toolsets": "terminal,file",
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        with pytest.raises(ValueError, match="enabled_toolsets"):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_connect_rejects_list_with_non_string_entries(self):
        """Numeric or null entries inside enabled_toolsets must reject."""
        routes = {
            "broken": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "x",
                "enabled_toolsets": ["terminal", 42],
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        with pytest.raises(ValueError, match="enabled_toolsets"):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_connect_rejects_non_list_disabled_toolsets(self):
        routes = {
            "broken": {
                "secret": _INSECURE_NO_AUTH,
                "prompt": "x",
                "disabled_toolsets": "web",
                "deliver": "log",
            }
        }
        adapter = _make_adapter(routes)
        with pytest.raises(ValueError, match="disabled_toolsets"):
            await adapter.connect()


# ---------------------------------------------------------------------------
# Gateway-side resolution: per-event toolsets must reach the AIAgent ctor.
# ---------------------------------------------------------------------------

class _CapturingAgent:
    """Records init kwargs so tests can assert on enabled/disabled_toolsets."""

    last_init: dict = None

    def __init__(self, *args, **kwargs):
        type(self).last_init = dict(kwargs)
        self.tools = []
        self.tool_progress_callback = None
        self.step_callback = None
        self.stream_delta_callback = None
        self.interim_assistant_callback = None
        self.status_callback = None
        self.reasoning_config = None
        self.service_tier = None
        self.request_overrides = {}

    def run_conversation(self, user_message, conversation_history=None, task_id=None):
        return {"final_response": "ok", "messages": [], "api_calls": 1}


def _make_runner():
    runner = object.__new__(gateway_run.GatewayRunner)
    runner.adapters = {}
    runner.session_store = None
    runner.config = None
    runner._voice_mode = {}
    runner._ephemeral_system_prompt = ""
    runner._prefill_messages = []
    runner._reasoning_config = None
    runner._show_reasoning = False
    runner._provider_routing = {}
    runner._fallback_model = None
    runner._service_tier = None
    runner._running_agents = {}
    runner._running_agents_ts = {}
    runner._background_tasks = set()
    runner._session_db = None
    runner._session_model_overrides = {}
    runner._session_reasoning_overrides = {}
    runner._pending_model_notes = {}
    runner._pending_approvals = {}
    runner._agent_cache = {}
    runner._agent_cache_lock = threading.Lock()
    runner._get_or_create_gateway_honcho = lambda session_key: (None, None)
    runner.hooks = MagicMock()
    runner.hooks.emit = AsyncMock()
    runner.hooks.loaded_hooks = []
    return runner


def _stub_runtime():
    return {
        "model": "gpt-5",
        "provider": "openai",
        "api_key": "sk-test",
        "base_url": "https://api.openai.com/v1",
        "api_mode": "chat_completions",
    }


def test_run_agent_honors_event_enabled_toolsets(monkeypatch):
    """``event_enabled_toolsets`` propagates through ``_run_agent`` into the
    spawned ``AIAgent`` instance, bypassing the platform-default resolution.

    This is the gateway-side half of the fix: the webhook adapter populates
    the per-event field, and the gateway must honour it instead of
    silently falling back to ``hermes-webhook`` (which excludes terminal/file).
    """
    monkeypatch.setattr(gateway_run, "_load_gateway_config", lambda: {})
    monkeypatch.setattr(gateway_run, "load_dotenv", lambda *args, **kwargs: None)

    def _explode(_config, _platform):
        raise AssertionError(
            "platform-default toolset resolution should be skipped when an "
            "explicit per-event toolset list is supplied"
        )

    monkeypatch.setattr(
        "hermes_cli.tools_config._get_platform_tools",
        _explode,
    )

    fake_run_agent = types.ModuleType("run_agent")
    fake_run_agent.AIAgent = _CapturingAgent
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    _CapturingAgent.last_init = None

    runner = _make_runner()
    source = SessionSource(
        platform=Platform.WEBHOOK,
        chat_id="webhook:kanban-completion:abc",
        chat_name="webhook/kanban-completion",
        chat_type="webhook",
        user_id="webhook:kanban-completion",
    )

    session_key = "agent:webhook:kanban-completion:webhook"
    runner._session_model_overrides[session_key] = _stub_runtime()

    asyncio.run(
        runner._run_agent(
            message="Handle a kanban completion event",
            context_prompt="",
            history=[],
            source=source,
            session_id="sess-1",
            session_key=session_key,
            event_enabled_toolsets=["terminal", "file", "skills"],
            event_disabled_toolsets=["web"],
        )
    )

    assert _CapturingAgent.last_init is not None
    # _run_agent sorts the override into a deterministic order.
    assert _CapturingAgent.last_init["enabled_toolsets"] == [
        "file",
        "skills",
        "terminal",
    ]
    assert _CapturingAgent.last_init["disabled_toolsets"] == ["web"]


def test_run_agent_falls_back_to_platform_default_without_event_override(monkeypatch):
    """When the event carries no override, the gateway calls
    ``_get_platform_tools`` exactly once and uses its result. This guards
    against accidentally regressing legacy webhook routes (Linear, GitHub,
    monitoring alerts) that rely on the platform default."""
    monkeypatch.setattr(gateway_run, "_load_gateway_config", lambda: {})
    monkeypatch.setattr(gateway_run, "load_dotenv", lambda *args, **kwargs: None)

    captured_platform = {}

    def _stub_get_platform_tools(_config, platform, **_kw):
        captured_platform["value"] = platform
        return {"web", "vision", "clarify"}

    monkeypatch.setattr(
        "hermes_cli.tools_config._get_platform_tools",
        _stub_get_platform_tools,
    )

    fake_run_agent = types.ModuleType("run_agent")
    fake_run_agent.AIAgent = _CapturingAgent
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    _CapturingAgent.last_init = None

    runner = _make_runner()
    source = SessionSource(
        platform=Platform.WEBHOOK,
        chat_id="webhook:linear:xyz",
        chat_name="webhook/linear",
        chat_type="webhook",
        user_id="webhook:linear",
    )
    session_key = "agent:webhook:linear:webhook"
    runner._session_model_overrides[session_key] = _stub_runtime()

    asyncio.run(
        runner._run_agent(
            message="Handle event",
            context_prompt="",
            history=[],
            source=source,
            session_id="sess-2",
            session_key=session_key,
        )
    )

    assert captured_platform.get("value") == "webhook"
    assert _CapturingAgent.last_init["enabled_toolsets"] == [
        "clarify",
        "vision",
        "web",
    ]
