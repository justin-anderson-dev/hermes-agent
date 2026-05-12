import pytest
from unittest.mock import AsyncMock, patch

from gateway.config import PlatformConfig
from gateway.platforms.slack import SlackAdapter


@pytest.mark.asyncio
async def test_top_level_reply_when_reply_in_thread_false():
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

    assert msg_event.source.thread_id is None
    resolved_ts = adapter._resolve_thread_ts(
        reply_to="12345.678",
        metadata={"thread_id": msg_event.source.thread_id},
    )
    assert resolved_ts is None


@pytest.mark.asyncio
async def test_thread_reply_still_works_when_reply_in_thread_false():
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
