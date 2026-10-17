from datetime import date

import pytest

from bot.app.services.date_format import manual_date_formats
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


@pytest.mark.parametrize(
    ("value", "today", "expected"),
    [
        ("31.12", date(2026, 12, 31), date(2026, 12, 31)),
        ("01.01", date(2026, 12, 31), date(2026, 1, 1)),
        ("01.01.2027", date(2027, 1, 1), date(2027, 1, 1)),
        ("2025-12-31", date(2026, 1, 1), date(2025, 12, 31)),
    ],
)
def test_month_and_year_boundaries_are_accepted(
    value: str,
    today: date,
    expected: date,
) -> None:
    assert parse_result_date(value, today=today) == expected


def test_leading_zero_date_is_accepted() -> None:
    assert parse_result_date("05.03", today=TODAY) == date(2026, 3, 5)
    assert parse_result_date("05.03.2026", today=TODAY) == date(2026, 3, 5)
    assert parse_result_date("2026-03-05", today=TODAY) == date(2026, 3, 5)


def test_manual_date_formats_are_zero_padded() -> None:
    assert manual_date_formats(date(2026, 10, 17)) == (
        "17.10",
        "17.10.2026",
        "2026-10-17",
    )
    assert manual_date_formats(date(2026, 1, 5)) == (
        "05.01",
        "05.01.2026",
        "2026-01-05",
    )


def test_invalid_date_error_uses_current_day_examples() -> None:
    with pytest.raises(DateParseError, match="17.10.2026"):
        parse_result_date("nope", today=date(2026, 10, 17))


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
    assert format_result_date(date(2026, 8, 25), today=TODAY) == "25 августа 2026"
