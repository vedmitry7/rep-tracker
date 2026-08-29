from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.handlers.start import start


@pytest.mark.asyncio
async def test_start_passes_bot_instance_default_timezone() -> None:
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

    await start(message, api, "Europe/Madrid")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Madrid", "ru")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("telegram_language", "expected"),
    [
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("en", "en"),
        ("en-US", "en"),
        ("es", "en"),
        (None, "en"),
    ],
)
async def test_start_maps_telegram_language_code(
    telegram_language: str | None,
    expected: str,
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

    await start(message, api, "Europe/Moscow")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Moscow", expected)
    rendered = message.answer.await_args.args[0]
    assert "🏋️ Repka" in rendered


@pytest.mark.asyncio
async def test_existing_user_keeps_saved_language_on_start() -> None:
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

    await start(message, api, "Europe/Moscow")

    api.resolve_user.assert_awaited_once_with(42, "Europe/Moscow", "ru")
    assert message.answer.await_args.args[0] == "🏋️ Repka\n\nNo exercises yet"
