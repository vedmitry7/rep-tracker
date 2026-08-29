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
    IMPORT_DATA = "import_data"
    EXERCISE_MANAGEMENT = "exercise_management"
    CLEAR_HISTORY = "clear_history"
    HARD_DELETE = "hard_delete"
    HOME = "home"


class SettingsAction(CallbackData, prefix="settings"):
    action: SettingsActionValue


class TimezoneChoice(CallbackData, prefix="timezone"):
    timezone: str


class TimezonePageChoice(CallbackData, prefix="timezone_page"):
    page: int


class LanguageChoice(CallbackData, prefix="language"):
    language: str


class ImportActionValue(StrEnum):
    MERGE = "merge"
    REPLACE = "replace"
    APPLY_MERGE = "apply_merge"
    APPLY_REPLACE = "apply_replace"
    CANCEL = "cancel"


class ImportAction(CallbackData, prefix="data_import"):
    action: ImportActionValue


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_CHANGE_LANGUAGE,
        callback_data=SettingsAction(action=SettingsActionValue.CHANGE_LANGUAGE),
    )
    builder.button(
        text=texts.BUTTON_CHANGE_TIMEZONE,
        callback_data=SettingsAction(action=SettingsActionValue.CHANGE_TIMEZONE),
    )
    builder.button(
        text=texts.BUTTON_IMPORT_DATA,
        callback_data=SettingsAction(action=SettingsActionValue.IMPORT_DATA),
    )
    builder.button(
        text=texts.BUTTON_EXERCISE_MANAGEMENT,
        callback_data=SettingsAction(
            action=SettingsActionValue.EXERCISE_MANAGEMENT
        ),
    )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=SettingsAction(action=SettingsActionValue.HOME),
    )
    builder.adjust(1)
    return builder.as_markup()


def exercise_management_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_CLEAR_HISTORY,
        callback_data=SettingsAction(action=SettingsActionValue.CLEAR_HISTORY),
    )
    builder.button(
        text=texts.BUTTON_DELETE_EXERCISE,
        callback_data=SettingsAction(action=SettingsActionValue.HARD_DELETE),
    )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=SettingsAction(action=SettingsActionValue.OPEN),
    )
    builder.adjust(1)
    return builder.as_markup()


def import_strategy_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_IMPORT_MERGE,
        callback_data=ImportAction(action=ImportActionValue.MERGE),
    )
    builder.button(
        text=texts.BUTTON_IMPORT_REPLACE,
        callback_data=ImportAction(action=ImportActionValue.REPLACE),
    )
    builder.button(
        text=texts.BUTTON_CANCEL,
        callback_data=ImportAction(action=ImportActionValue.CANCEL),
    )
    builder.adjust(1)
    return builder.as_markup()


def import_confirmation_keyboard(strategy: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if strategy == "replace":
        text = texts.BUTTON_REPLACE_AND_IMPORT
        action = ImportActionValue.APPLY_REPLACE
    else:
        text = texts.BUTTON_IMPORT
        action = ImportActionValue.APPLY_MERGE
    builder.button(
        text=text,
        callback_data=ImportAction(action=action),
        style=("danger" if strategy == "replace" else None),
    )
    builder.button(
        text=texts.BUTTON_CANCEL_PLAIN,
        callback_data=ImportAction(action=ImportActionValue.CANCEL),
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
