import pytest

from bot.app.services.result_parser import ResultParseError, parse_result


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10", [10]),
        ("4x10", [10, 10, 10, 10]),
        ("4X10", [10, 10, 10, 10]),
        ("4×10", [10, 10, 10, 10]),
        ("4*10", [10, 10, 10, 10]),
        ("10 9 8 7", [10, 9, 8, 7]),
        ("10,9,8,7", [10, 9, 8, 7]),
        ("10, 9, 8, 7", [10, 9, 8, 7]),
    ],
)
def test_parse_supported_result_formats(value: str, expected: list[int]) -> None:
    assert parse_result(value) == expected


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_input_is_rejected(value: str) -> None:
    with pytest.raises(ResultParseError, match="Введи результат"):
        parse_result(value)


@pytest.mark.parametrize("value", ["0", "4x0", "0x10"])
def test_zero_is_rejected(value: str) -> None:
    with pytest.raises(ResultParseError):
        parse_result(value)


@pytest.mark.parametrize("value", ["-10", "4x-10", "10 -9"])
def test_negative_values_are_rejected(value: str) -> None:
    with pytest.raises(ResultParseError, match="положительным"):
        parse_result(value)


def test_more_than_one_hundred_sets_are_rejected() -> None:
    with pytest.raises(ResultParseError, match="от 1 до 100"):
        parse_result(" ".join(["1"] * 101))


def test_more_than_ten_thousand_repetitions_are_rejected() -> None:
    with pytest.raises(ResultParseError, match="10 000"):
        parse_result("10001")


@pytest.mark.parametrize("value", ["abc", "4x", "10,,8", "10, 9 8"])
def test_invalid_format_is_rejected(value: str) -> None:
    with pytest.raises(ResultParseError, match="Не понял формат"):
        parse_result(value)
