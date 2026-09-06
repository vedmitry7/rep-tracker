from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, Update, User
from datetime import datetime, timezone

from bot.app.commands import register_commands
from bot.app.handlers.commands import help_command, settings_command
from bot.app.handlers.start import start
from bot.app.api.client import Exercise
from bot.app.texts import set_current_language, reset_current_language


@pytest.mark.asyncio
async def test_language_specific_command_menus():
    bot = SimpleNamespace(set_my_commands=AsyncMock())
    await register_commands(bot)
    calls = bot.set_my_commands.call_args_list
    assert [c.kwargs["language_code"] for c in calls] == ["", "ru", "en"]
    for call in calls:
        assert [c.command for c in call.args[0]] == ["menu", "settings", "help"]
        assert call.kwargs["scope"].type == "default"
    assert [c.description for c in calls[1].args[0]] == ["Главное меню", "Настройки", "Помощь"]
    assert [c.description for c in calls[2].args[0]] == ["Main menu", "Settings", "Help"]


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["ru", "en"])
async def test_commands_existing_screens_and_help(language):
    message = SimpleNamespace(from_user=SimpleNamespace(id=42, language_code=language), answer=AsyncMock())
    state = SimpleNamespace(clear=AsyncMock())
    api = SimpleNamespace(resolve_user=AsyncMock(return_value=SimpleNamespace(language=language)),
        list_exercises=AsyncMock(return_value=[Exercise(id=8, name="Pull-ups")]),
        get_user_settings=AsyncMock(return_value=SimpleNamespace(language=language, timezone="Europe/Moscow")))
    await start(message, api, "Europe/Moscow", state)
    buttons = message.answer.call_args.kwargs["reply_markup"].inline_keyboard
    assert buttons[0][0].callback_data == "exercise_open:8"
    await settings_command(message, state, api)
    assert "Москва" in message.answer.call_args.args[0] if language == "ru" else "Moscow" in message.answer.call_args.args[0]
    token = set_current_language(language)
    try:
        await help_command(message, state)
    finally:
        reset_current_language(token)
    assert "/menu" in message.answer.call_args.args[0]
    assert "/settings" in message.answer.call_args.args[0]
    assert state.clear.await_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["start", "menu", "settings", "help"])
async def test_commands_escape_active_fsm(command):
    # Fresh router instances from a tiny dispatcher would miss real registration:
    # inspect actual registered handlers through their filters instead.
    from bot.app.handlers.start import router as start_router
    from bot.app.handlers.commands import router as commands_router
    bot = Bot(token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
    message = Message(message_id=1, date=datetime.now(timezone.utc), chat=Chat(id=42,type="private"),
                      from_user=User(id=42, is_bot=False, first_name="Test"), text=f"/{command}")
    try:
        matches = []
        for router in (start_router, commands_router):
            for handler in router.message.handlers:
                matched, _ = await handler.check(message, bot=bot, raw_state="ImportData:waiting_for_file")
                if matched:
                    matches.append(handler.callback)
        assert len(matches) == 1
        assert matches[0] is {"start": start, "menu": start, "settings": settings_command, "help": help_command}[command]
    finally:
        await bot.session.close()
