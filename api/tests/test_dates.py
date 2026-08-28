from datetime import date, datetime, timezone

import pytest

from api.app.core import dates


@pytest.mark.parametrize(
    ("timezone_name", "expected"),
    [
        ("Europe/Moscow", date(2026, 8, 28)),
        ("America/New_York", date(2026, 8, 27)),
    ],
)
def test_get_user_today_uses_utc_and_iana_timezone(
    timezone_name: str,
    expected: date,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dates,
        "get_utc_now",
        lambda: datetime(2026, 8, 27, 22, 30, tzinfo=timezone.utc),
    )

    assert dates.get_user_today(timezone_name) == expected
