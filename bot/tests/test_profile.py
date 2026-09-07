from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.profile import configure_profile


@pytest.mark.asyncio
async def test_configure_profile_sets_default_and_localized_profile_copy():
    bot = SimpleNamespace(
        set_my_name=AsyncMock(),
        set_my_description=AsyncMock(),
        set_my_short_description=AsyncMock(),
    )

    await configure_profile(bot)

    assert bot.set_my_name.call_args_list == [
        ((), {"name": "Repka · Workout Tracker"}),
        ((), {"name": "Repka · Workout Tracker", "language_code": "en"}),
        ((), {"name": "Репка · Трекер упражнений", "language_code": "ru"}),
    ]
    assert [call.kwargs["language_code"] for call in bot.set_my_description.call_args_list[1:]] == [
        "en",
        "ru",
    ]
    assert [call.kwargs["language_code"] for call in bot.set_my_short_description.call_args_list[1:]] == [
        "en",
        "ru",
    ]
