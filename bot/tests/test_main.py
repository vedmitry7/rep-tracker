from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.main import notify_admins_about_startup


@pytest.mark.asyncio
async def test_startup_notification_is_sent_to_every_administrator() -> None:
    bot = SimpleNamespace(send_message=AsyncMock())

    await notify_admins_about_startup(bot, frozenset({10, 20}))

    assert bot.send_message.await_count == 2
    bot.send_message.assert_any_await(10, "Repka bot started.")
    bot.send_message.assert_any_await(20, "Repka bot started.")


@pytest.mark.asyncio
async def test_startup_notification_failure_does_not_interrupt_other_administrators() -> None:
    bot = SimpleNamespace(
        send_message=AsyncMock(side_effect=[RuntimeError("unavailable"), None])
    )

    await notify_admins_about_startup(bot, frozenset({10, 20}))

    assert bot.send_message.await_count == 2
