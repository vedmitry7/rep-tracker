from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from bot.app.timezones import (
    TIMEZONE_OPTIONS,
    TIMEZONE_PAGE_SIZE,
    format_timezone,
    format_utc_offset,
    sorted_timezone_options,
    timezone_page,
    utc_offset,
)


NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def test_catalog_contains_unique_valid_iana_timezones() -> None:
    identifiers = [option.timezone for option in TIMEZONE_OPTIONS]

    assert len(identifiers) == len(set(identifiers))
    assert 30 <= len(identifiers) <= 40
    for identifier in identifiers:
        assert ZoneInfo(identifier).key == identifier


def test_catalog_spans_both_signs_and_fractional_offsets() -> None:
    offsets = [utc_offset(option.timezone, at=NOW) for option in TIMEZONE_OPTIONS]

    assert min(offsets) == timedelta(hours=-12)
    assert max(offsets) == timedelta(hours=14)
    assert any(offset < timedelta(0) for offset in offsets)
    assert any(offset > timedelta(0) for offset in offsets)
    assert any(offset.total_seconds() % 3600 for offset in offsets)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (timedelta(hours=3), "UTC+03:00"),
        (timedelta(hours=-5), "UTC-05:00"),
        (timedelta(hours=5, minutes=30), "UTC+05:30"),
    ],
)
def test_format_utc_offset(offset: timedelta, expected: str) -> None:
    assert format_utc_offset(offset) == expected


def test_amsterdam_offset_reflects_dst() -> None:
    winter = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    summer = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)

    assert utc_offset("Europe/Amsterdam", at=winter) == timedelta(hours=1)
    assert utc_offset("Europe/Amsterdam", at=summer) == timedelta(hours=2)
    assert format_timezone("Europe/Amsterdam", "en", at=winter).startswith(
        "(UTC+01:00)"
    )
    assert format_timezone("Europe/Amsterdam", "en", at=summer).startswith(
        "(UTC+02:00)"
    )


def test_timezone_display_uses_localized_label_or_iana_fallback() -> None:
    assert format_timezone("Asia/Kolkata", "ru", at=NOW) == (
        "(UTC+05:30) Индия"
    )
    assert format_timezone("Europe/Paris", "en", at=NOW) == (
        "(UTC+01:00) Europe/Paris"
    )


def test_timezones_are_sorted_by_current_offset_with_stable_ties() -> None:
    sorted_options = sorted_timezone_options(at=NOW)
    offsets = [utc_offset(option.timezone, at=NOW) for option in sorted_options]

    assert offsets == sorted(offsets)
    same_offset = [
        option.timezone
        for option in sorted_options
        if utc_offset(option.timezone, at=NOW) == timedelta(hours=9)
    ]
    catalog_same_offset = [
        option.timezone
        for option in TIMEZONE_OPTIONS
        if utc_offset(option.timezone, at=NOW) == timedelta(hours=9)
    ]
    assert same_offset == catalog_same_offset


def test_first_middle_last_pages_and_out_of_range_boundaries() -> None:
    sorted_options = sorted_timezone_options(at=NOW)
    first = timezone_page(0, at=NOW)
    middle = timezone_page(2, at=NOW)
    last = timezone_page(999, at=NOW)

    assert first.options == sorted_options[:TIMEZONE_PAGE_SIZE]
    assert middle.options == sorted_options[16:24]
    assert last.options == sorted_options[-TIMEZONE_PAGE_SIZE:]
    assert (first.has_previous, first.has_next) == (False, True)
    assert (middle.has_previous, middle.has_next) == (True, True)
    assert (last.has_previous, last.has_next) == (True, False)
    assert timezone_page(-10, at=NOW).page == 0
