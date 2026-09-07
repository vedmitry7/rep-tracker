from datetime import date, datetime, timedelta, timezone

import pytest

from api.app.core import dates
from api.app.services.weekly_report import calculate_weekly, due_week_start, last_week


@pytest.mark.parametrize("count", [1, 2, 20])
def test_complete_history(count):
    start = date(2026, 8, 24)
    days = [(start - timedelta(weeks=i), 10 * (i + 1)) for i in range(count)]
    days += [(start + timedelta(days=7), 999)]
    result = calculate_weekly(days, start)
    assert len(result["history"]) == count
    assert result["total"] == 10
    assert result["previous"] == (20 if count > 1 else None)
    assert result["delta"] == (-10 if count > 1 else None)
    assert result["percent"] == (-50 if count > 1 else None)
    assert result["active_days"] == 1


def test_days_aggregation_gap_zero_and_tie():
    start = date(2026, 8, 24)
    result = calculate_weekly([(start, 5), (start, 5), (start + timedelta(days=6), 10),
                               (start - timedelta(weeks=2), 30)], start)
    assert result["total"] == 20
    assert result["previous"] == 0
    assert result["delta"] == 20
    assert result["percent"] is None
    assert result["active_days"] == 2
    assert result["best_day"] == {"date": "2026-08-30", "reps": 10}
    assert [w["total"] for w in result["history"]] == [20, 0, 30]


def test_empty_and_only_current_week():
    start = date(2026, 8, 24)
    assert calculate_weekly([], start) is None
    assert calculate_weekly([(start + timedelta(days=7), 50)], start) is None
    result = calculate_weekly([(start - timedelta(weeks=1), 50)], start)
    assert result["total"] == 0
    assert result["best_day"] is None
    assert result["percent"] == -100


@pytest.mark.parametrize("zone,now,expected", [
    ("Europe/Moscow", "2026-08-30T20:59:59+00:00", "2026-08-17"),
    ("Europe/Moscow", "2026-08-30T21:00:00+00:00", "2026-08-24"),
    ("America/New_York", "2026-03-09T03:59:59+00:00", "2026-02-23"),
    ("America/New_York", "2026-03-09T04:00:00+00:00", "2026-03-02"),
    ("Pacific/Kiritimati", "2026-01-04T10:00:00+00:00", "2025-12-29"),
])
def test_timezone_week_boundary(monkeypatch, zone, now, expected):
    monkeypatch.setattr(dates, "get_utc_now", lambda: datetime.fromisoformat(now))
    assert last_week(dates.get_user_today(zone)).isoformat() == expected


@pytest.mark.parametrize(
    "zone,now,expected",
    [
        ("Europe/Moscow", "2026-08-30T20:59:00+00:00", None),
        ("Europe/Moscow", "2026-08-31T05:59:00+00:00", None),
        ("Europe/Moscow", "2026-08-31T06:00:00+00:00", date(2026, 8, 24)),
        ("America/New_York", "2026-08-31T13:00:00+00:00", date(2026, 8, 24)),
    ],
)
def test_due_time_is_monday_0900_in_user_timezone(monkeypatch, zone, now, expected):
    monkeypatch.setattr(dates, "get_utc_now", lambda: datetime.fromisoformat(now))
    assert due_week_start(zone) == expected
