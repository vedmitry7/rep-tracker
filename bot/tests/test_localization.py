from datetime import date

import pytest

from bot.app.api.client import Exercise, ExerciseStats
from bot.app.handlers.exercises import stats_screen_text
from bot.app.handlers.history import history_days_text
from bot.app.services.date_parser import format_result_date
from bot.app.services.date_parser import DateParseError, parse_result_date
from bot.app.services.result_parser import ResultParseError, parse_result
from bot.app.texts import (
    available_locales,
    en,
    get_catalog,
    get_text,
    normalize_language_code,
    reset_current_language,
    ru,
    set_current_language,
    texts,
)


def catalog_keys(module: object) -> set[str]:
    return {key for key in vars(module) if not key.startswith("_")}


def test_all_catalogs_have_matching_keys() -> None:
    for locale in available_locales():
        assert catalog_keys(get_catalog(locale.code)) == catalog_keys(en)


def test_non_english_catalogs_do_not_inherit_english_ui_copy() -> None:
    """A complete key set is insufficient when a locale imports ``en`` wholesale."""
    english_values = vars(en)
    for locale in available_locales():
        if locale.code == "en":
            continue
        catalog_values = vars(get_catalog(locale.code))
        inherited = [
            key
            for key, value in english_values.items()
            if not key.startswith("_") and catalog_values[key] is value
        ]
        assert inherited == [], f"{locale.code} inherits English UI copy: {inherited}"


@pytest.mark.parametrize(
    ("language", "button"),
    [
        ("es", "⚙️ Ajustes"),
        ("pt", "⚙️ Configurações"),
        ("tr", "⚙️ Ayarlar"),
        ("uk", "⚙️ Налаштування"),
        ("id", "⚙️ Pengaturan"),
        ("hi", "⚙️ सेटिंग्स"),
        ("kk", "⚙️ Баптаулар"),
        ("pl", "⚙️ Ustawienia"),
        ("fr", "⚙️ Paramètres"),
    ],
)
def test_new_locales_have_localized_bot_profile_and_settings_button(
    language: str,
    button: str,
) -> None:
    catalog = get_catalog(language)
    assert catalog.BOT_NAME.startswith("Repka · ")
    assert catalog.BOT_SHORT_DESCRIPTION != en.BOT_SHORT_DESCRIPTION
    assert catalog.BOT_DESCRIPTION != en.BOT_DESCRIPTION
    assert catalog.BUTTON_SETTINGS == button


def test_language_picker_lists_requested_locales() -> None:
    assert {locale.code for locale in available_locales()} == {
        "en", "ru", "es", "pt", "tr", "uk", "id", "hi", "kk", "pl", "fr"
    }


def test_unknown_language_falls_back_to_english() -> None:
    assert get_text("de", "BUTTON_SETTINGS") == "⚙️ Settings"


def test_parameterized_text_is_formatted() -> None:
    assert get_text("en", "timezone_changed", "Europe/London") == (
        "✅ Timezone changed\n\nEurope/London"
    )
    assert get_text("ru", "exercise_name_too_long", 50).endswith("50 символов.")


def test_telegram_language_normalization() -> None:
    assert normalize_language_code("ru-RU") == "ru"
    assert normalize_language_code("en-US") == "en"
    assert normalize_language_code("zh") == "en"
    assert normalize_language_code(None) == "en"


@pytest.mark.parametrize(
    ("language", "result_label", "history_label", "stats_label"),
    [
        ("ru", "Введи результат", "Записей пока нет", "Сегодня:"),
        ("en", "Enter a result", "No entries yet", "Today:"),
    ],
)
def test_add_result_history_and_statistics_are_localized(
    language: str,
    result_label: str,
    history_label: str,
    stats_label: str,
) -> None:
    token = set_current_language(language)
    try:
        exercise = Exercise(id=7, name="Pull-ups")
        today = date(2026, 8, 27)

        assert result_label in texts.result_input(
            exercise.name,
            format_result_date(today, today=today),
        )
        assert history_label in history_days_text(exercise, [])
        assert stats_label in stats_screen_text(
            exercise,
            ExerciseStats.empty(today=today),
        )
    finally:
        reset_current_language(token)


@pytest.mark.parametrize(
    ("language", "date_error", "result_error"),
    [
        ("ru", "Не понял дату", "Не понял формат"),
        ("en", "Unrecognized date", "Unrecognized format"),
    ],
)
def test_parser_errors_are_localized(
    language: str,
    date_error: str,
    result_error: str,
) -> None:
    token = set_current_language(language)
    try:
        with pytest.raises(DateParseError, match=date_error):
            parse_result_date("invalid", today=date(2026, 8, 27))
        with pytest.raises(ResultParseError, match=result_error):
            parse_result("invalid")
    finally:
        reset_current_language(token)
