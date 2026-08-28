import re
from datetime import date, timedelta

from bot.app.texts import texts


_SHORT_DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})$")
_FULL_DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


class DateParseError(ValueError):
    """Input cannot be converted to an allowed exercise date."""


def parse_result_date(value: str, *, today: date) -> date:
    current_date = today
    text = value.strip()
    if not text:
        raise DateParseError(texts.ENTER_DATE_REQUIRED)

    parsed_date: date | None = None
    if match := _SHORT_DATE.fullmatch(text):
        parts = (current_date.year, int(match.group(2)), int(match.group(1)))
    elif match := _FULL_DATE.fullmatch(text):
        parts = (int(match.group(3)), int(match.group(2)), int(match.group(1)))
    elif match := _ISO_DATE.fullmatch(text):
        parts = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    else:
        parts = None

    if parts is not None:
        try:
            parsed_date = date(*parts)
        except ValueError:
            parsed_date = None

    if parsed_date is None:
        raise DateParseError(texts.INVALID_DATE)
    if parsed_date > current_date:
        raise DateParseError(texts.FUTURE_DATE)
    return parsed_date


def days_ago(days: int, *, today: date) -> date:
    if days not in {0, 1, 2}:
        raise ValueError("days must be 0, 1, or 2")
    return today - timedelta(days=days)


def format_result_date(value: date, *, today: date) -> str:
    if value == today:
        return texts.TODAY
    return value.strftime("%d.%m.%Y")
