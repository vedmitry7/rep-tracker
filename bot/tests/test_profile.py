from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.profile import configure_profile
from bot.app.texts import available_locales, get_catalog


@pytest.mark.asyncio
async def test_configure_profile_sets_default_and_localized_profile_copy():
    bot = SimpleNamespace(
        set_my_name=AsyncMock(),
        set_my_description=AsyncMock(),
        set_my_short_description=AsyncMock(),
    )

    await configure_profile(bot)

    locales = available_locales()
    assert bot.set_my_name.call_args_list[0] == ((), {"name": get_catalog("en").BOT_NAME})
    assert [call.kwargs["language_code"] for call in bot.set_my_name.call_args_list[1:]] == [
        locale.code for locale in locales
    ]
    assert [call.kwargs["name"] for call in bot.set_my_name.call_args_list[1:]] == [
        get_catalog(locale.code).BOT_NAME for locale in locales
    ]
    assert [call.kwargs["language_code"] for call in bot.set_my_description.call_args_list[1:]] == [
        locale.code for locale in locales
    ]
    assert [call.kwargs["language_code"] for call in bot.set_my_short_description.call_args_list[1:]] == [
        locale.code for locale in locales
    ]
