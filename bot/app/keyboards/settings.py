from datetime import datetime, timezone
from enum import StrEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.texts import current_language, texts
from bot.app.timezones import format_timezone, timezone_page


class SettingsActionValue(StrEnum):
    OPEN = "open"
    CHANGE_TIMEZONE = "change_timezone"
    OTHER_TIMEZONE = "other_timezone"
    CHANGE_LANGUAGE = "change_language"
    HOME = "home"


class SettingsAction(CallbackData, prefix="settings"):
    action: SettingsActionValue


class TimezoneChoice(CallbackData, prefix="timezone"):
    timezone: str


class TimezonePageChoice(CallbackData, prefix="timezone_page"):
    page: int


class LanguageChoice(CallbackData, prefix="language"):
    language: str


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_CHANGE_TIMEZONE,
        callback_data=SettingsAction(action=SettingsActionValue.CHANGE_TIMEZONE),
    )
    builder.button(
        text=texts.BUTTON_CHANGE_LANGUAGE,
        callback_data=SettingsAction(action=SettingsActionValue.CHANGE_LANGUAGE),
    )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=SettingsAction(action=SettingsActionValue.HOME),
    )
    builder.adjust(1)
    return builder.as_markup()


def timezone_choices_keyboard(
    page: int = 0,
    *,
    at: datetime | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    language = current_language()
    instant = at or datetime.now(timezone.utc)
    page_data = timezone_page(page, at=instant)
    for option in page_data.options:
        builder.row(
            InlineKeyboardButton(
                text=format_timezone(option.timezone, language, at=instant),
                callback_data=TimezoneChoice(timezone=option.timezone).pack(),
            )
        )

    navigation: list[InlineKeyboardButton] = []
    if page_data.has_previous:
        navigation.append(
            InlineKeyboardButton(
                text=texts.BUTTON_PREVIOUS,
                callback_data=TimezonePageChoice(page=page_data.page - 1).pack(),
            )
        )
    navigation.append(
        InlineKeyboardButton(
            text=f"{page_data.page + 1} / {page_data.total_pages}",
            callback_data=TimezonePageChoice(page=page_data.page).pack(),
        )
    )
    if page_data.has_next:
        navigation.append(
            InlineKeyboardButton(
                text=texts.BUTTON_NEXT,
                callback_data=TimezonePageChoice(page=page_data.page + 1).pack(),
            )
        )
    builder.row(*navigation)

    builder.row(
        InlineKeyboardButton(
            text=texts.BUTTON_OTHER_TIMEZONE,
            callback_data=SettingsAction(
                action=SettingsActionValue.OTHER_TIMEZONE
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=texts.BUTTON_BACK,
            callback_data=SettingsAction(action=SettingsActionValue.OPEN).pack(),
        )
    )
    return builder.as_markup()


def settings_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=SettingsAction(action=SettingsActionValue.OPEN),
    )
    return builder.as_markup()


def language_choices_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_ENGLISH,
        callback_data=LanguageChoice(language="en"),
    )
    builder.button(
        text=texts.BUTTON_RUSSIAN,
        callback_data=LanguageChoice(language="ru"),
    )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=SettingsAction(action=SettingsActionValue.OPEN),
    )
    builder.adjust(1)
    return builder.as_markup()
