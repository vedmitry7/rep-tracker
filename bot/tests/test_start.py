from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

import bot.app.handlers.start as start_module
from bot.app.handlers.start import start
from bot.app.texts import get_catalog


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


@pytest.mark.asyncio
async def test_start_passes_bot_instance_default_timezone(state: FSMContext) -> None:
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=42, language_code="ru-RU"),
        answer=AsyncMock(),
    )
    api = SimpleNamespace(
        resolve_user=AsyncMock(
            return_value=SimpleNamespace(created=True, language="ru")
        ),
        list_exercises=AsyncMock(return_value=[]),
    )

    await start(message, state, api, "Europe/Madrid")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Madrid", "ru")
    assert message.answer.await_args.args[0].startswith("🥬 Привет! Я Repka.")
    keyboard = message.answer.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].text == "➕ Добавить первое упражнение"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("telegram_language", "expected"),
    [
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("en", "en"),
        ("en-US", "en"),
        ("es", "es"),
        (None, "en"),
    ],
)
async def test_start_maps_telegram_language_code(
    telegram_language: str | None,
    expected: str,
    state: FSMContext,
) -> None:
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=42, language_code=telegram_language),
        answer=AsyncMock(),
    )
    api = SimpleNamespace(
        resolve_user=AsyncMock(
            return_value=SimpleNamespace(created=True, language=expected)
        ),
        list_exercises=AsyncMock(return_value=[]),
    )

    await start(message, state, api, "Europe/Moscow")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Moscow", expected)
    rendered = message.answer.await_args.args[0]
    assert rendered.startswith(get_catalog(expected).WELCOME)


@pytest.mark.asyncio
async def test_existing_user_keeps_saved_language_on_start(state: FSMContext) -> None:
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=42, language_code="ru-RU"),
        answer=AsyncMock(),
    )
    api = SimpleNamespace(
        resolve_user=AsyncMock(
            return_value=SimpleNamespace(created=False, language="en")
        ),
        list_exercises=AsyncMock(return_value=[]),
    )

    await start(message, state, api, "Europe/Moscow")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Moscow", "ru")
    assert message.answer.await_args.args[0] == "🏋️ Repka\n\nNo exercises yet"


@pytest.mark.asyncio
async def test_start_notifies_administrators_about_a_created_user(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=42, language_code="en"),
        answer=AsyncMock(),
    )
    api = SimpleNamespace(
        resolve_user=AsyncMock(return_value=SimpleNamespace(created=True, language="en")),
        list_exercises=AsyncMock(return_value=[]),
    )
    bot = SimpleNamespace()
    notify = AsyncMock()
    monkeypatch.setattr(start_module, "notify_new_user_registration", notify)
    monkeypatch.setattr(
        start_module,
        "get_settings",
        lambda: SimpleNamespace(admin_telegram_ids=frozenset({10})),
    )

    await start_module.start(message, state, api, "Europe/Moscow", bot)

    notify.assert_awaited_once_with(
        bot,
        frozenset({10}),
        api,
        message.from_user,
        "en",
    )
