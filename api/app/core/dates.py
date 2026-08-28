from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = "Europe/Moscow"


class InvalidTimezoneError(ValueError):
    """Raised when a timezone is not present in the IANA timezone database."""


def validate_timezone_name(timezone_name: str) -> str:
    """Return a valid IANA timezone name or raise ``InvalidTimezoneError``."""
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise InvalidTimezoneError(f"Unknown IANA timezone: {timezone_name}") from error
    return timezone_name


def get_utc_now() -> datetime:
    """Return the current aware UTC datetime (a seam for deterministic tests)."""
    return datetime.now(timezone.utc)


def get_user_today(timezone_name: str) -> date:
    """Return the user's current local training day.

    Future rollover rules belong here so every consumer keeps the same day policy.
    """
    timezone_info = ZoneInfo(validate_timezone_name(timezone_name))
    return get_utc_now().astimezone(timezone_info).date()
