import re

from bot.app.texts import texts


MAX_SETS = 100
MAX_REPETITIONS = 10_000

_INTEGER = r"\d+"
_REPEATED_SETS_PATTERN = re.compile(
    rf"^({_INTEGER})\s*[xX×*]\s*({_INTEGER})$"
)
_SPACE_SEPARATED_PATTERN = re.compile(rf"^{_INTEGER}(?:\s+{_INTEGER})*$")
_COMMA_SEPARATED_PATTERN = re.compile(
    rf"^{_INTEGER}(?:\s*,\s*{_INTEGER})*$"
)


class ResultParseError(ValueError):
    """Input cannot be converted to a valid list of repetitions."""


def parse_result(value: str) -> list[int]:
    text = value.strip()
    if not text:
        raise ResultParseError(texts.ENTER_RESULT)
    if re.search(r"-\s*\d", text):
        raise ResultParseError(texts.POSITIVE_RESULT_REQUIRED)

    repeated_match = _REPEATED_SETS_PATTERN.fullmatch(text)
    if repeated_match:
        sets_count = _to_int(repeated_match.group(1))
        repetitions = _to_int(repeated_match.group(2))
        _validate_sets_count(sets_count)
        _validate_repetitions([repetitions])
        return [repetitions] * sets_count

    if _COMMA_SEPARATED_PATTERN.fullmatch(text):
        repetitions = [_to_int(part.strip()) for part in text.split(",")]
    elif _SPACE_SEPARATED_PATTERN.fullmatch(text):
        repetitions = [_to_int(part) for part in text.split()]
    else:
        raise ResultParseError(texts.INVALID_RESULT_FORMAT)

    _validate_sets_count(len(repetitions))
    _validate_repetitions(repetitions)
    return repetitions


def _validate_sets_count(sets_count: int) -> None:
    if not 1 <= sets_count <= MAX_SETS:
        raise ResultParseError(texts.sets_count_out_of_range(MAX_SETS))


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ResultParseError(texts.NUMBER_TOO_LARGE) from error


def _validate_repetitions(repetitions: list[int]) -> None:
    if any(value < 1 or value > MAX_REPETITIONS for value in repetitions):
        raise ResultParseError(texts.repetitions_out_of_range(MAX_REPETITIONS))
