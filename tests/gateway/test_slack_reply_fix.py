import pytest
from unittest.mock import AsyncMock, patch

from gateway.config import PlatformConfig
from gateway.platforms.slack import SlackAdapter
from gateway.session import build_session_key


@pytest.mark.asyncio
async def test_top_level_mention_keys_session_per_prompt_when_reply_in_thread_false():
    """Top-level @mentions with reply_in_thread=false must:

    1. Give each top-level prompt its own session (source.thread_id == ts).
    2. Still post the reply at channel level (no thread_ts on chat.postMessage).
    """
    config = PlatformConfig(enabled=True, token="xoxb-fake", extra={"reply_in_thread": False})
    adapter = SlackAdapter(config)
    adapter._bot_user_id = "U_BOT"
    adapter._team_bot_user_ids = {"T123": "U_BOT"}
    adapter.handle_message = AsyncMock()

    event = {
        "type": "message",
        "channel": "C123",
        "ts": "12345.678",
        "text": "<@U_BOT> hello",
        "user": "U_USER",
        "team": "T123",
        "channel_type": "channel",
    }

    with patch.object(adapter, "_dedup") as mock_dedup:
        mock_dedup.is_duplicate.return_value = False
        await adapter._handle_slack_message(event)

    adapter.handle_message.assert_awaited_once()
    msg_event = adapter.handle_message.await_args.args[0]

    # Session keying: every top-level prompt gets its own session, derived
    # from the message ts. Without this, every channel @mention collapses
    # into one shared session.
    assert msg_event.source.thread_id == "12345.678"

    # Send-side routing: _resolve_thread_ts() recognises the synthetic
    # session-key ts (thread_id == reply_to) and posts at channel level.
    resolved_ts = adapter._resolve_thread_ts(
        reply_to="12345.678",
        metadata={"thread_id": msg_event.source.thread_id},
    )
    assert resolved_ts is None

    # Agent-driven sends without reply_to still route to the channel because
    # the synthetic session-key ts is not in _real_thread_parents.
    resolved_no_reply = adapter._resolve_thread_ts(
        reply_to=None,
        metadata={"thread_id": msg_event.source.thread_id},
    )
    assert resolved_no_reply is None

    # The synthetic ts must NOT be tracked as a real thread parent — otherwise
    # the reply_to=None path would mistakenly route into a thread.
    assert "12345.678" not in adapter._real_thread_parents


@pytest.mark.asyncio
async def test_two_top_level_mentions_get_distinct_session_keys():
    """Two separate top-level prompts must produce different session keys.

    This is the regression: without thread_id derived from the message ts,
    both prompts share the same session and the agent's context bleeds
    between unrelated requests.
    """
    config = PlatformConfig(enabled=True, token="xoxb-fake", extra={"reply_in_thread": False})
    adapter = SlackAdapter(config)
    adapter._bot_user_id = "U_BOT"
    adapter._team_bot_user_ids = {"T123": "U_BOT"}
    adapter.handle_message = AsyncMock()

    base_event = {
        "type": "message",
        "channel": "C123",
        "text": "<@U_BOT> hello",
        "user": "U_USER",
        "team": "T123",
        "channel_type": "channel",
    }

    with patch.object(adapter, "_dedup") as mock_dedup:
        mock_dedup.is_duplicate.return_value = False
        await adapter._handle_slack_message({**base_event, "ts": "11111.000"})
        await adapter._handle_slack_message({**base_event, "ts": "22222.000"})

    src_first = adapter.handle_message.await_args_list[0].args[0].source
    src_second = adapter.handle_message.await_args_list[1].args[0].source

    key_first = build_session_key(src_first)
    key_second = build_session_key(src_second)

    assert key_first != key_second, (
        f"Distinct top-level prompts must produce distinct session keys; "
        f"both resolved to {key_first}"
    )


@pytest.mark.asyncio
async def test_thread_reply_still_works_when_reply_in_thread_false():
    """Real thread replies (thread_ts != ts) must continue to reply in-thread."""
    config = PlatformConfig(enabled=True, token="xoxb-fake", extra={"reply_in_thread": False})
    adapter = SlackAdapter(config)
    adapter._bot_user_id = "U_BOT"
    adapter._team_bot_user_ids = {"T123": "U_BOT"}
    adapter.handle_message = AsyncMock()

    event = {
        "type": "message",
        "channel": "C123",
        "ts": "12345.999",
        "thread_ts": "12345.000",
        "text": "<@U_BOT> reply",
        "user": "U_USER",
        "team": "T123",
        "channel_type": "channel",
    }

    with patch.object(adapter, "_dedup") as mock_dedup:
        mock_dedup.is_duplicate.return_value = False
        await adapter._handle_slack_message(event)

    msg_event = adapter.handle_message.await_args.args[0]

    assert msg_event.source.thread_id == "12345.000"
    assert "12345.000" in adapter._real_thread_parents
    resolved_ts = adapter._resolve_thread_ts(
        reply_to="12345.999",
        metadata={"thread_id": "12345.000"},
    )
    assert resolved_ts == "12345.000"
