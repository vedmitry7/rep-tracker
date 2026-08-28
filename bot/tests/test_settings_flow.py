from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import InvalidRequestError
from bot.app.handlers import settings
from bot.app.keyboards.settings import (
    LanguageChoice,
    TimezoneChoice,
    TimezonePageChoice,
    timezone_choices_keyboard,
)
from bot.app.localization import user_languages
from bot.app.states.settings import ChangeTimezone
from bot.app.texts import reset_current_language, set_current_language
from bot.app.timezones import (
    DEFAULT_TIMEZONE_PAGE,
    TIMEZONE_PAGE_SIZE,
    timezone_page,
)


NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


class FakeMessage:
    def __init__(self) -> None:
        self.edit_text = AsyncMock()
        self.answer = AsyncMock()
        self.text: str | None = None
        self.from_user = SimpleNamespace(id=42)


class FakeCallback:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.message = FakeMessage()
        self.answer = AsyncMock()


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


@pytest.fixture(autouse=True)
def reset_language_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    user_languages.clear()
    monkeypatch.setattr(settings, "Message", FakeMessage)
    monkeypatch.setattr(settings, "CallbackQuery", FakeCallback)


def _timezone_callbacks(markup: object) -> list[TimezoneChoice]:
    return [
        TimezoneChoice.unpack(button.callback_data)
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.callback_data and button.callback_data.startswith("timezone:")
    ]


def _page_callbacks(markup: object) -> list[TimezonePageChoice]:
    return [
        TimezonePageChoice.unpack(button.callback_data)
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.callback_data
        and button.callback_data.startswith("timezone_page:")
    ]


def test_timezone_keyboard_first_page_and_navigation_boundary() -> None:
    markup = timezone_choices_keyboard(at=NOW)

    assert [item.timezone for item in _timezone_callbacks(markup)] == [
        option.timezone for option in timezone_page(0, at=NOW).options
    ]
    assert len(_timezone_callbacks(markup)) == TIMEZONE_PAGE_SIZE
    assert [item.page for item in _page_callbacks(markup)] == [0, 1]
    assert [len(row) for row in markup.inline_keyboard] == [1] * 8 + [2, 1, 1]


def test_timezone_keyboard_middle_and_last_page_boundaries() -> None:
    middle = timezone_choices_keyboard(2, at=NOW)
    last_page = timezone_page(999, at=NOW)
    last = timezone_choices_keyboard(last_page.page, at=NOW)

    assert [item.page for item in _page_callbacks(middle)] == [1, 2, 3]
    assert [item.page for item in _page_callbacks(last)] == [
        last_page.page - 1,
        last_page.page,
    ]
    assert len(_timezone_callbacks(last)) == len(last_page.options)


@pytest.mark.asyncio
async def test_pagination_callback_renders_requested_page(state: FSMContext) -> None:
    callback = FakeCallback()

    await settings.paginate_timezones(
        callback,
        TimezonePageChoice(page=3),
        state,
    )

    markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    assert [item.page for item in _page_callbacks(markup)] == [2, 3, 4]
    callback.answer.assert_awaited_once_with()


@pytest.mark.parametrize(
    ("language", "expected_title", "expected_label", "expected_other"),
    [
        ("ru", "🌍 Часовой пояс", "Амстердам", "Другой часовой пояс"),
        ("en", "🌍 Timezone", "Amsterdam", "Other timezone"),
    ],
)
@pytest.mark.asyncio
async def test_timezone_selector_is_localized(
    state: FSMContext,
    language: str,
    expected_title: str,
    expected_label: str,
    expected_other: str,
) -> None:
    callback = FakeCallback()
    token = set_current_language(language)
    try:
        await settings.choose_timezone(callback, state)
    finally:
        reset_current_language(token)

    text = callback.message.edit_text.await_args.args[0]
    markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    labels = [button.text for row in markup.inline_keyboard for button in row]
    assert expected_title in text
    assert any(expected_label in label for label in labels)
    assert any(expected_other in label for label in labels)
    assert f"{DEFAULT_TIMEZONE_PAGE + 1} / 5" in labels


@pytest.mark.asyncio
async def test_settings_screen_shows_curated_timezone_label(state: FSMContext) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        get_user_settings=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Moscow",
                today=date(2026, 8, 27),
                language="ru",
            )
        )
    )

    await settings.show_settings(callback, state, api)

    rendered = callback.message.edit_text.await_args.args[0]
    assert "⚙️ Настройки" in rendered
    assert "Часовой пояс:\n(UTC+03:00) Москва, Санкт-Петербург" in rendered
    assert "Europe/Moscow" not in rendered


@pytest.mark.asyncio
async def test_settings_screen_falls_back_to_manual_iana_name(state: FSMContext) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        get_user_settings=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Paris",
                today=date(2026, 8, 27),
                language="en",
            )
        )
    )

    await settings.show_settings(callback, state, api)

    rendered = callback.message.edit_text.await_args.args[0]
    assert "Timezone:\n(UTC" in rendered
    assert ") Europe/Paris" in rendered


@pytest.mark.parametrize("page", [0, 2])
@pytest.mark.asyncio
async def test_timezone_change_from_any_page_patches_iana_and_redraws_settings(
    state: FSMContext,
    page: int,
) -> None:
    callback = FakeCallback()
    timezone_name = timezone_page(page, at=NOW).options[0].timezone
    api = SimpleNamespace(
        update_user_timezone=AsyncMock(
            return_value=SimpleNamespace(
                timezone=timezone_name,
                today=date(2026, 8, 27),
                language="ru",
            )
        )
    )

    await settings.set_popular_timezone(
        callback,
        TimezoneChoice(timezone=timezone_name),
        state,
        api,
    )

    api.update_user_timezone.assert_awaited_once_with(42, timezone_name)
    rendered = callback.message.edit_text.await_args.args[0]
    assert rendered.startswith("⚙️ Настройки")
    callback.answer.assert_awaited_once_with("Часовой пояс изменён")


@pytest.mark.asyncio
async def test_language_change_renders_new_language_immediately(
    state: FSMContext,
) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        update_user_language=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Moscow",
                today=date(2026, 8, 27),
                language="en",
            )
        )
    )

    await settings.set_language(
        callback,
        LanguageChoice(language="en"),
        state,
        api,
    )

    api.update_user_language.assert_awaited_once_with(42, "en")
    assert callback.message.edit_text.await_args.args[0] == (
        "✅ Language changed\n\nEnglish"
    )


@pytest.mark.parametrize(
    ("language", "expected_heading", "expected_zone"),
    [
        ("ru", "⚙️ Настройки", "Лондон, Лиссабон"),
        ("en", "⚙️ Settings", "London, Lisbon"),
    ],
)
@pytest.mark.asyncio
async def test_timezone_success_screen_uses_user_language(
    state: FSMContext,
    language: str,
    expected_heading: str,
    expected_zone: str,
) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        update_user_timezone=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/London",
                today=date(2026, 8, 27),
                language=language,
            )
        )
    )

    await settings.set_popular_timezone(
        callback,
        TimezoneChoice(timezone="Europe/London"),
        state,
        api,
    )

    rendered = callback.message.edit_text.await_args.args[0]
    assert expected_heading in rendered
    assert expected_zone in rendered


@pytest.mark.asyncio
async def test_valid_manual_timezone_patches_and_clears_fsm(state: FSMContext) -> None:
    await state.set_state(ChangeTimezone.entering_timezone)
    message = FakeMessage()
    message.text = "Europe/Paris"
    api = SimpleNamespace(
        update_user_timezone=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Paris",
                today=date(2026, 8, 27),
                language="en",
            )
        )
    )

    await settings.set_custom_timezone(message, state, api)

    api.update_user_timezone.assert_awaited_once_with(42, "Europe/Paris")
    assert await state.get_state() is None
    rendered = message.answer.await_args.args[0]
    assert "⚙️ Settings" in rendered
    assert ") Europe/Paris" in rendered


@pytest.mark.asyncio
async def test_invalid_custom_timezone_keeps_fsm_active(state: FSMContext) -> None:
    await state.set_state(ChangeTimezone.entering_timezone)
    message = FakeMessage()
    message.text = "UTC+3"
    api = SimpleNamespace(
        update_user_timezone=AsyncMock(side_effect=InvalidRequestError)
    )

    await settings.set_custom_timezone(message, state, api)

    assert await state.get_state() == ChangeTimezone.entering_timezone.state
    message.answer.assert_awaited_once()
