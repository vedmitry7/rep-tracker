from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.commands import register_commands
from bot.app.handlers import commands
from bot.app.states.result import AddResult
from bot.app.texts import available_locales, get_catalog


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


@pytest.mark.asyncio
async def test_menu_clears_active_flow_and_opens_menu(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await state.set_state(AddResult.entering_result)
    send_menu = AsyncMock()
    monkeypatch.setattr(commands, "send_menu_message", send_menu)
    message = SimpleNamespace()
    api_client = SimpleNamespace()

    await commands.menu(message, state, api_client, "Europe/Moscow")

    assert await state.get_state() is None
    send_menu.assert_awaited_once_with(
        message,
        api_client,
        "Europe/Moscow",
        bot=None,
    )


@pytest.mark.asyncio
async def test_settings_clears_active_flow_and_opens_settings(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await state.set_state(AddResult.entering_result)
    send_settings = AsyncMock()
    monkeypatch.setattr(commands, "send_settings_message", send_settings)
    message = SimpleNamespace()
    api_client = SimpleNamespace()

    await commands.settings(message, state, api_client)

    assert await state.get_state() is None
    send_settings.assert_awaited_once_with(message, api_client)


@pytest.mark.asyncio
async def test_help_clears_active_flow_and_sends_instructions(
    state: FSMContext,
) -> None:
    await state.set_state(AddResult.entering_result)
    message = SimpleNamespace(answer=AsyncMock())

    await commands.help_command(message, state)

    assert await state.get_state() is None
    assert "Помощь" in message.answer.await_args.args[0]
    assert "/menu" in message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_register_commands_sets_default_and_localized_menus() -> None:
    bot = SimpleNamespace(set_my_commands=AsyncMock())

    await register_commands(bot)

    calls = bot.set_my_commands.await_args_list
    assert [command.command for command in calls[0].args[0]] == [
        "menu",
        "settings",
        "help",
    ]
    assert calls[0].args[0][0].description == get_catalog("en").BOT_COMMANDS["menu"]
    assert calls[0].kwargs == {}

    locales = available_locales()
    assert len(calls) == 1 + len(locales)
    for call, locale in zip(calls[1:], locales, strict=True):
        assert [command.command for command in call.args[0]] == [
            "menu",
            "settings",
            "help",
        ]
        assert call.args[0][0].description == get_catalog(locale.code).BOT_COMMANDS["menu"]
        assert call.kwargs == {"language_code": locale.code}
