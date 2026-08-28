from datetime import date

import pytest

from bot.app.api.client import Exercise, ExerciseStats
from bot.app.handlers.exercises import stats_screen_text
from bot.app.handlers.history import history_days_text
from bot.app.services.date_parser import format_result_date
from bot.app.services.date_parser import DateParseError, parse_result_date
from bot.app.services.result_parser import ResultParseError, parse_result
from bot.app.texts import (
    en,
    get_text,
    normalize_language_code,
    reset_current_language,
    ru,
    set_current_language,
    texts,
)


def catalog_keys(module: object) -> set[str]:
    return {key for key in vars(module) if not key.startswith("_")}


def test_english_and_russian_catalogs_have_matching_keys() -> None:
    assert catalog_keys(en) == catalog_keys(ru)


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
