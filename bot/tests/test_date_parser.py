from datetime import date

import pytest

from bot.app.services.date_parser import (
    DateParseError,
    days_ago,
    format_result_date,
    parse_result_date,
)


TODAY = date(2026, 8, 27)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("25.08", date(2026, 8, 25)),
        ("25.08.2026", date(2026, 8, 25)),
        ("2026-08-25", date(2026, 8, 25)),
    ],
)
def test_parse_supported_date_formats(value: str, expected: date) -> None:
    assert parse_result_date(value, today=TODAY) == expected


def test_invalid_date_format_is_rejected() -> None:
    with pytest.raises(DateParseError, match="Не понял дату"):
        parse_result_date("25/08/2026", today=TODAY)


def test_future_date_is_rejected() -> None:
    with pytest.raises(DateParseError, match="Будущую дату"):
        parse_result_date("28.08.2026", today=TODAY)


def test_nonexistent_date_is_rejected() -> None:
    with pytest.raises(DateParseError, match="Не понял дату"):
        parse_result_date("31.02.2026", today=TODAY)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (0, date(2026, 8, 27)),
        (1, date(2026, 8, 26)),
        (2, date(2026, 8, 25)),
    ],
)
def test_relative_dates_use_local_today(offset: int, expected: date) -> None:
    assert days_ago(offset, today=TODAY) == expected


def test_today_has_a_human_readable_label() -> None:
    assert format_result_date(TODAY, today=TODAY) == "Сегодня"
    assert format_result_date(date(2026, 8, 25), today=TODAY) == "25.08.2026"
