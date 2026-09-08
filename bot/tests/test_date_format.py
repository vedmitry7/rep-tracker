from datetime import date

import pytest

from bot.app.services.date_format import format_user_date


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("ru", "7 сентября 2026"),
        ("en", "Sep 7, 2026"),
        ("es", "7 de septiembre de 2026"),
    ],
)
def test_format_user_date_is_localized(language: str, expected: str) -> None:
    assert format_user_date(date(2026, 9, 7), language=language) == expected
