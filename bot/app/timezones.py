"""Curated, localized timezone choices for the Telegram UI."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil
from zoneinfo import ZoneInfo


TIMEZONE_PAGE_SIZE = 8
DEFAULT_TIMEZONE_PAGE = 2


@dataclass(frozen=True, slots=True)
class TimezoneOption:
    timezone: str
    labels: dict[str, str]

    def label(self, language: str) -> str:
        return self.labels.get(language, self.labels["en"])


@dataclass(frozen=True, slots=True)
class TimezonePage:
    options: tuple[TimezoneOption, ...]
    page: int
    total_pages: int

    @property
    def has_previous(self) -> bool:
        return self.page > 0

    @property
    def has_next(self) -> bool:
        return self.page + 1 < self.total_pages


# Catalog order is the stable tie-breaker when current UTC offsets are equal.
TIMEZONE_OPTIONS = (
    TimezoneOption(
        "Etc/GMT+12",
        {"en": "International Date Line West", "ru": "Линия перемены дат (запад)"},
    ),
    TimezoneOption(
        "Pacific/Pago_Pago",
        {"en": "American Samoa", "ru": "Американское Самоа"},
    ),
    TimezoneOption("Pacific/Honolulu", {"en": "Hawaii", "ru": "Гавайи"}),
    TimezoneOption(
        "Pacific/Marquesas",
        {"en": "Marquesas Islands", "ru": "Маркизские острова"},
    ),
    TimezoneOption("America/Anchorage", {"en": "Alaska", "ru": "Аляска"}),
    TimezoneOption(
        "America/Los_Angeles",
        {"en": "Pacific Time", "ru": "Тихоокеанское время"},
    ),
    TimezoneOption(
        "America/Denver",
        {"en": "Mountain Time", "ru": "Горное время"},
    ),
    TimezoneOption(
        "America/Chicago",
        {"en": "Central Time", "ru": "Центральное время"},
    ),
    TimezoneOption(
        "America/New_York",
        {"en": "Eastern Time", "ru": "Восточное время"},
    ),
    TimezoneOption(
        "America/Halifax",
        {"en": "Atlantic Time", "ru": "Атлантическое время"},
    ),
    TimezoneOption(
        "America/St_Johns",
        {"en": "Newfoundland", "ru": "Ньюфаундленд"},
    ),
    TimezoneOption(
        "America/Sao_Paulo",
        {"en": "São Paulo, Brasília", "ru": "Сан-Паулу, Бразилиа"},
    ),
    TimezoneOption(
        "Atlantic/South_Georgia",
        {"en": "South Georgia", "ru": "Южная Георгия"},
    ),
    TimezoneOption("Atlantic/Azores", {"en": "Azores", "ru": "Азорские острова"}),
    TimezoneOption(
        "Africa/Abidjan",
        {"en": "Accra, Abidjan", "ru": "Аккра, Абиджан"},
    ),
    TimezoneOption(
        "Europe/London",
        {"en": "London, Lisbon", "ru": "Лондон, Лиссабон"},
    ),
    TimezoneOption(
        "Europe/Amsterdam",
        {"en": "Amsterdam, Berlin, Rome", "ru": "Амстердам, Берлин, Рим"},
    ),
    TimezoneOption(
        "Africa/Johannesburg",
        {"en": "Johannesburg, Cape Town", "ru": "Йоханнесбург, Кейптаун"},
    ),
    TimezoneOption(
        "Europe/Athens",
        {"en": "Athens, Bucharest, Kyiv", "ru": "Афины, Бухарест, Киев"},
    ),
    TimezoneOption(
        "Europe/Moscow",
        {"en": "Moscow, St. Petersburg", "ru": "Москва, Санкт-Петербург"},
    ),
    TimezoneOption("Asia/Tehran", {"en": "Tehran", "ru": "Тегеран"}),
    TimezoneOption("Asia/Dubai", {"en": "Dubai", "ru": "Дубай"}),
    TimezoneOption("Asia/Kabul", {"en": "Kabul", "ru": "Кабул"}),
    TimezoneOption("Asia/Karachi", {"en": "Karachi", "ru": "Карачи"}),
    TimezoneOption("Asia/Kolkata", {"en": "India", "ru": "Индия"}),
    TimezoneOption("Asia/Kathmandu", {"en": "Nepal", "ru": "Непал"}),
    TimezoneOption("Asia/Dhaka", {"en": "Dhaka", "ru": "Дакка"}),
    TimezoneOption("Asia/Yangon", {"en": "Yangon", "ru": "Янгон"}),
    TimezoneOption(
        "Asia/Bangkok",
        {"en": "Bangkok, Jakarta", "ru": "Бангкок, Джакарта"},
    ),
    TimezoneOption("Asia/Shanghai", {"en": "China", "ru": "Китай"}),
    TimezoneOption(
        "Asia/Tokyo",
        {"en": "Tokyo, Seoul", "ru": "Токио, Сеул"},
    ),
    TimezoneOption("Australia/Darwin", {"en": "Darwin", "ru": "Дарвин"}),
    TimezoneOption("Australia/Adelaide", {"en": "Adelaide", "ru": "Аделаида"}),
    TimezoneOption(
        "Australia/Brisbane",
        {"en": "Brisbane", "ru": "Брисбен"},
    ),
    TimezoneOption("Australia/Sydney", {"en": "Sydney", "ru": "Сидней"}),
    TimezoneOption(
        "Australia/Lord_Howe",
        {"en": "Lord Howe Island", "ru": "Остров Лорд-Хау"},
    ),
    TimezoneOption("Pacific/Noumea", {"en": "Nouméa", "ru": "Нумеа"}),
    TimezoneOption(
        "Pacific/Auckland",
        {"en": "Auckland, Wellington", "ru": "Окленд, Веллингтон"},
    ),
    TimezoneOption(
        "Pacific/Chatham",
        {"en": "Chatham Islands", "ru": "Острова Чатем"},
    ),
    TimezoneOption(
        "Pacific/Kiritimati",
        {"en": "Kiritimati", "ru": "Киритимати"},
    ),
)

_OPTIONS_BY_TIMEZONE = {option.timezone: option for option in TIMEZONE_OPTIONS}


def utc_offset(timezone_name: str, *, at: datetime | None = None) -> timedelta:
    """Return the zone's offset at an aware UTC instant."""
    instant = at or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("at must be timezone-aware")
    utc_instant = instant.astimezone(timezone.utc)
    offset = utc_instant.astimezone(ZoneInfo(timezone_name)).utcoffset()
    if offset is None:  # pragma: no cover - ZoneInfo always returns an offset
        raise ValueError(f"Timezone has no UTC offset: {timezone_name}")
    return offset


def format_utc_offset(offset: timedelta) -> str:
    total_minutes = round(offset.total_seconds() / 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def format_timezone(
    timezone_name: str,
    language: str,
    *,
    at: datetime | None = None,
) -> str:
    option = _OPTIONS_BY_TIMEZONE.get(timezone_name)
    label = option.label(language) if option is not None else timezone_name
    return f"({format_utc_offset(utc_offset(timezone_name, at=at))}) {label}"


def sorted_timezone_options(*, at: datetime | None = None) -> tuple[TimezoneOption, ...]:
    instant = at or datetime.now(timezone.utc)
    return tuple(
        sorted(
            TIMEZONE_OPTIONS,
            key=lambda option: utc_offset(option.timezone, at=instant),
        )
    )


def timezone_page(page: int, *, at: datetime | None = None) -> TimezonePage:
    total_pages = ceil(len(TIMEZONE_OPTIONS) / TIMEZONE_PAGE_SIZE)
    bounded_page = min(max(page, 0), total_pages - 1)
    options = sorted_timezone_options(at=at)
    start = bounded_page * TIMEZONE_PAGE_SIZE
    return TimezonePage(
        options=options[start : start + TIMEZONE_PAGE_SIZE],
        page=bounded_page,
        total_pages=total_pages,
    )
