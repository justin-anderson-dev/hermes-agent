"""Tests for the kanban → webhook pub/sub bridge in the gateway notifier.

Covers the new delivery branch added to ``_kanban_notifier_watcher`` and
its helper ``_kanban_deliver_webhook_event``:

* success path — HTTP 2xx advances the subscription cursor
* failure path — non-2xx / network errors leave the cursor intact
* HMAC signature generation matches the route secret
* direct (non-webhook) platform delivery is unaffected (regression)
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform
from gateway.run import GatewayRunner


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_runner() -> GatewayRunner:
    """A bare GatewayRunner with just the bits the helper touches."""
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.adapters = {}
    return runner


def _make_webhook_adapter(
    *,
    secret: str = "test-secret",
    route_name: str = "kanban-completion",
    host: str = "127.0.0.1",
    port: int = 8645,
) -> MagicMock:
    adapter = MagicMock()
    adapter._host = host
    adapter._port = port
    adapter._global_secret = ""
    adapter._routes = {route_name: {"secret": secret}}
    adapter._reload_dynamic_routes = MagicMock(return_value=None)
    return adapter


def _make_event(
    *, ev_id: int = 42, kind: str = "completed", payload: dict | None = None,
    run_id: int | None = 7, created_at: int = 1747490000,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=ev_id, task_id="t_abc", kind=kind,
        payload=payload or {"summary": "done"},
        created_at=created_at, run_id=run_id,
    )


class _FakeResp:
    def __init__(self, status: int, body: str = ""):
        self.status = status
        self._body = body

    async def text(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    """aiohttp.ClientSession stand-in.  Records the last POST."""

    def __init__(self, *, response: _FakeResp | None = None,
                 raise_exc: Exception | None = None):
        self._response = response or _FakeResp(202, "")
        self._raise = raise_exc
        self.calls: list[dict] = []

    def post(self, url, data=None, headers=None):
        self.calls.append({"url": url, "data": data, "headers": headers})
        if self._raise:
            raise self._raise
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _patch_aiohttp(session: _FakeSession):
    """Patch ``aiohttp.ClientSession`` so the helper hits our fake."""
    aiohttp_stub = SimpleNamespace(
        ClientSession=lambda *a, **kw: session,
        ClientTimeout=lambda **kw: None,
    )
    return patch.dict("sys.modules", {"aiohttp": aiohttp_stub})


# ---------------------------------------------------------------------------
# Payload + signature
# ---------------------------------------------------------------------------


def test_payload_event_type_mapping_for_all_terminal_kinds():
    runner = _make_runner()
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}
    expected = {
        "completed": "kanban.completed",
        "blocked": "kanban.blocked",
        "gave_up": "kanban.gave_up",
        "crashed": "kanban.crashed",
        "timed_out": "kanban.timed_out",
    }
    for kind, want in expected.items():
        ev = _make_event(kind=kind)
        _, payload = runner._kanban_webhook_payload(
            sub=sub, event=ev, task=None, board="code-ops",
        )
        assert payload["event_type"] == want
        assert payload["event"]["kind"] == kind
        assert payload["task_id"] == "t_abc"
        assert payload["board"] == "code-ops"
        assert payload["run_id"] == 7


def test_payload_delivery_id_is_deterministic_sha256():
    runner = _make_runner()
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}
    ev = _make_event(ev_id=99)
    expected = hashlib.sha256(b"code-ops:t_abc:99").hexdigest()
    did_a, _ = runner._kanban_webhook_payload(
        sub=sub, event=ev, task=None, board="code-ops",
    )
    did_b, _ = runner._kanban_webhook_payload(
        sub=sub, event=ev, task=None, board="code-ops",
    )
    assert did_a == expected
    assert did_a == did_b


# ---------------------------------------------------------------------------
# _kanban_deliver_webhook_event
# ---------------------------------------------------------------------------


def test_webhook_delivery_success_returns_true_and_signs_body():
    runner = _make_runner()
    adapter = _make_webhook_adapter(secret="hush", port=8646)
    runner.adapters[Platform.WEBHOOK] = adapter
    session = _FakeSession(response=_FakeResp(202, ""))
    ev = _make_event()
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}

    with _patch_aiohttp(session):
        ok = asyncio.run(runner._kanban_deliver_webhook_event(
            sub=sub, event=ev, task=None, board="code-ops",
        ))

    assert ok is True
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "http://127.0.0.1:8646/webhooks/kanban-completion"

    sig = call["headers"]["X-Webhook-Signature"]
    expected_sig = hmac.new(b"hush", call["data"], hashlib.sha256).hexdigest()
    assert sig == expected_sig

    delivered = json.loads(call["data"].decode("utf-8"))
    assert delivered["event_type"] == "kanban.completed"
    assert delivered["board"] == "code-ops"
    assert delivered["task_id"] == "t_abc"
    assert delivered["event"]["id"] == ev.id
    assert delivered["event"]["payload"] == {"summary": "done"}
    assert call["headers"]["X-Request-ID"] == delivered["delivery_id"]


def test_webhook_delivery_returns_false_on_http_error():
    runner = _make_runner()
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()
    session = _FakeSession(response=_FakeResp(500, "boom"))
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}

    with _patch_aiohttp(session):
        ok = asyncio.run(runner._kanban_deliver_webhook_event(
            sub=sub, event=_make_event(), task=None, board="b",
        ))

    assert ok is False


def test_webhook_delivery_returns_false_on_network_exception():
    runner = _make_runner()
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()
    session = _FakeSession(raise_exc=ConnectionError("nope"))
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}

    with _patch_aiohttp(session):
        ok = asyncio.run(runner._kanban_deliver_webhook_event(
            sub=sub, event=_make_event(), task=None, board="b",
        ))

    assert ok is False


def test_webhook_delivery_returns_false_when_adapter_missing():
    runner = _make_runner()  # no Platform.WEBHOOK adapter
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}
    ok = asyncio.run(runner._kanban_deliver_webhook_event(
        sub=sub, event=_make_event(), task=None, board="b",
    ))
    assert ok is False


def test_webhook_delivery_returns_false_when_route_missing():
    runner = _make_runner()
    adapter = _make_webhook_adapter()
    adapter._routes = {}  # no kanban-completion route
    runner.adapters[Platform.WEBHOOK] = adapter
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}
    ok = asyncio.run(runner._kanban_deliver_webhook_event(
        sub=sub, event=_make_event(), task=None, board="b",
    ))
    assert ok is False


def test_webhook_delivery_rebinds_zero_host_to_loopback():
    runner = _make_runner()
    adapter = _make_webhook_adapter(host="0.0.0.0", port=8647)
    runner.adapters[Platform.WEBHOOK] = adapter
    session = _FakeSession()
    sub = {"task_id": "t_abc", "platform": "webhook", "chat_id": "kanban-completion"}

    with _patch_aiohttp(session):
        asyncio.run(runner._kanban_deliver_webhook_event(
            sub=sub, event=_make_event(), task=None, board="b",
        ))

    assert session.calls[0]["url"].startswith("http://127.0.0.1:8647/")


# ---------------------------------------------------------------------------
# Watcher branching (in-memory DB)
# ---------------------------------------------------------------------------


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    """Isolate the kanban DB to a per-test tmpdir.

    Kanban's :func:`kanban_home` uses ``HERMES_KANBAN_HOME`` as its highest-
    precedence override and otherwise falls back to ``get_default_hermes_root``
    (NOT ``HERMES_HOME``). Without the explicit override the tests would
    happily clobber the developer's real ``~/.hermes/kanban.db``.
    """
    from pathlib import Path as _Path
    from hermes_cli import kanban_db as kb
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(home))
    # The dispatcher injects HERMES_KANBAN_BOARD / HERMES_KANBAN_DB into
    # worker env; in a normal dev shell either may be set and would point
    # at the real ``~/.hermes`` kanban DB. Clear them so the test only
    # touches the tmp_path-scoped default board.
    monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
    monkeypatch.delenv("HERMES_KANBAN_DB", raising=False)
    monkeypatch.setattr(_Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def _seed_task_with_event(kind: str = "completed") -> tuple[str, int]:
    """Create a task, register a webhook notify sub, and record one event.

    Returns ``(task_id, event_id)``.
    """
    from hermes_cli import kanban_db as kb
    with kb.connect() as conn:
        task_id = kb.create_task(conn, title="bridge me", assignee="alfred")
        kb.add_notify_sub(
            conn,
            task_id=task_id,
            platform="webhook",
            chat_id="kanban-completion",
        )
        with kb.write_txn(conn):
            kb._append_event(conn, task_id, kind, {"summary": "x"})
        # Look up the event id we just recorded.
        row = conn.execute(
            "SELECT id FROM task_events WHERE task_id = ? ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
        return task_id, int(row["id"])


def _run_one_watcher_tick(runner: GatewayRunner) -> None:
    """Run the notifier loop exactly once.

    The watcher does ``await asyncio.sleep(5)`` before its main loop, then
    ``asyncio.sleep(1)`` between ticks. We patch sleep to a no-op and only
    flip ``_running`` after the second call so the first iteration body
    actually runs to completion.
    """
    async def _tick():
        runner._running = True
        sleep_calls = [0]

        async def _fake_sleep(*_a, **_kw):
            sleep_calls[0] += 1
            if sleep_calls[0] >= 2:
                runner._running = False

        with patch("asyncio.sleep", new=AsyncMock(side_effect=_fake_sleep)):
            await runner._kanban_notifier_watcher(interval=1)

    asyncio.run(_tick())


def test_watcher_advances_cursor_on_successful_webhook_delivery(kanban_home):
    from hermes_cli import kanban_db as kb

    task_id, ev_id = _seed_task_with_event(kind="completed")

    runner = _make_runner()
    runner._running = True
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()

    # Stub the helper so we don't need a real aiohttp/server.
    delivered = []

    async def _ok(*, sub, event, task, board):
        delivered.append((sub["task_id"], event.id, event.kind, board))
        return True

    runner._kanban_deliver_webhook_event = _ok  # type: ignore[method-assign]

    _run_one_watcher_tick(runner)

    assert delivered and delivered[0][0] == task_id
    assert delivered[0][1] == ev_id
    # Cursor advanced, but the subscription stays until task.status reaches
    # a truly final state (done / archived).
    with kb.connect() as conn:
        subs = kb.list_notify_subs(conn, task_id=task_id)
    assert len(subs) == 1
    assert int(subs[0]["last_event_id"]) == ev_id


def test_watcher_does_not_advance_cursor_on_failed_webhook_delivery(kanban_home):
    from hermes_cli import kanban_db as kb

    task_id, ev_id = _seed_task_with_event(kind="completed")

    runner = _make_runner()
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()

    async def _fail(*, sub, event, task, board):
        return False

    runner._kanban_deliver_webhook_event = _fail  # type: ignore[method-assign]

    _run_one_watcher_tick(runner)

    with kb.connect() as conn:
        subs = kb.list_notify_subs(conn, task_id=task_id)
    # Subscription still present + cursor not advanced.
    assert len(subs) == 1
    assert int(subs[0]["last_event_id"]) < ev_id


def test_watcher_drops_webhook_sub_after_max_failures(kanban_home):
    """Mirror the ``adapter.send`` drop-after-N behavior on the webhook lane.

    A perma-failing webhook (route deleted, secret rotated, listener gone)
    would otherwise spin every tick forever. After ``MAX_SEND_FAILURES``
    consecutive failures the watcher must drop the subscription.
    """
    from hermes_cli import kanban_db as kb

    task_id, _ = _seed_task_with_event(kind="completed")
    runner = _make_runner()
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()

    async def _fail(*, sub, event, task, board):
        return False

    runner._kanban_deliver_webhook_event = _fail  # type: ignore[method-assign]

    # MAX_SEND_FAILURES = 3 inside the watcher; run three ticks.
    for _ in range(3):
        _run_one_watcher_tick(runner)

    with kb.connect() as conn:
        subs = kb.list_notify_subs(conn, task_id=task_id)
    assert subs == []


def test_watcher_skips_webhook_branch_for_non_kanban_completion_chat(kanban_home):
    """Convention guard: only chat_id=='kanban-completion' enters the bridge.

    Other webhook chat_ids fall back to the existing platform-resolution
    flow (which currently no-ops without a connected adapter or a
    matching delivery_info entry).
    """
    from hermes_cli import kanban_db as kb

    with kb.connect() as conn:
        task_id = kb.create_task(conn, title="not-bridged")
        kb.add_notify_sub(
            conn, task_id=task_id, platform="webhook", chat_id="other-route",
        )
        with kb.write_txn(conn):
            kb._append_event(conn, task_id, "completed", {})

    runner = _make_runner()
    runner.adapters[Platform.WEBHOOK] = _make_webhook_adapter()

    bridge_calls = []

    async def _spy(*, sub, event, task, board):
        bridge_calls.append(sub["chat_id"])
        return True

    runner._kanban_deliver_webhook_event = _spy  # type: ignore[method-assign]

    _run_one_watcher_tick(runner)

    # The bridge must NOT fire for chat_id != "kanban-completion".
    assert bridge_calls == []


# ---------------------------------------------------------------------------
# Regression: direct adapter path still works
# ---------------------------------------------------------------------------


def test_watcher_still_uses_adapter_send_for_non_webhook_platform(kanban_home):
    """A non-webhook subscription must continue to go through adapter.send."""
    from hermes_cli import kanban_db as kb

    with kb.connect() as conn:
        task_id = kb.create_task(conn, title="ping me", assignee="alfred")
        kb.add_notify_sub(
            conn, task_id=task_id, platform="slack", chat_id="C12345",
        )
        with kb.write_txn(conn):
            kb._append_event(conn, task_id, "completed", {})

    sent: list[tuple[str, str]] = []

    class _StubAdapter:
        async def send(self, chat_id, content, metadata=None):
            sent.append((chat_id, content))

    runner = _make_runner()
    runner.adapters[Platform.SLACK] = _StubAdapter()

    bridge_called = False

    async def _bridge(*, sub, event, task, board):
        nonlocal bridge_called
        bridge_called = True
        return True

    runner._kanban_deliver_webhook_event = _bridge  # type: ignore[method-assign]

    _run_one_watcher_tick(runner)

    assert bridge_called is False
    assert len(sent) == 1
    chat_id, msg = sent[0]
    assert chat_id == "C12345"
    assert task_id in msg
