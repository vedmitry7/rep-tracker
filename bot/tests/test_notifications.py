from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.api.client import BackendUnavailableError
from bot.app.notifications import notify_new_user_registration


@pytest.mark.asyncio
async def test_new_user_notification_includes_user_details_and_daily_count() -> None:
    bot = SimpleNamespace(send_message=AsyncMock())
    api = SimpleNamespace(
        get_analytics_summary=AsyncMock(return_value=SimpleNamespace(new_users=3))
    )
    user = SimpleNamespace(
        id=42,
        full_name="Ada Lovelace",
        username="ada",
    )

    await notify_new_user_registration(bot, frozenset({10}), api, user, "en")

    bot.send_message.assert_awaited_once_with(
        10,
        "New user registered\n"
        "Name: Ada Lovelace\n"
        "Username: @ada\n"
        "Telegram ID: 42\n"
        "Language: en\n"
        "Users today: 3",
    )


@pytest.mark.asyncio
async def test_new_user_notification_survives_unavailable_analytics() -> None:
    bot = SimpleNamespace(send_message=AsyncMock())
    api = SimpleNamespace(
        get_analytics_summary=AsyncMock(side_effect=BackendUnavailableError())
    )
    user = SimpleNamespace(id=42, full_name="Ada Lovelace", username=None)

    await notify_new_user_registration(bot, frozenset({10}), api, user, "en")

    assert "Username: not set" in bot.send_message.await_args.args[1]
    assert "Users today: unavailable" in bot.send_message.await_args.args[1]
