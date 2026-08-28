import pytest

from bot.app.services.result_constructor import (
    ConstructorError,
    add_set,
    change_repetition,
    initial_repetitions,
    remove_set,
)


def test_constructor_starts_with_ten_repetitions() -> None:
    assert initial_repetitions() == [10]


def test_increment_repetitions() -> None:
    assert change_repetition([10], 0, 1) == [11]


def test_decrement_repetitions() -> None:
    assert change_repetition([10], 0, -1) == [9]


def test_repetitions_do_not_go_below_one() -> None:
    assert change_repetition([1], 0, -1) == [1]


def test_repetitions_do_not_go_above_ten_thousand() -> None:
    assert change_repetition([10_000], 0, 1) == [10_000]


def test_add_set_copies_the_previous_value() -> None:
    assert add_set([10, 9]) == [10, 9, 9]


def test_add_set_uses_ten_if_the_list_is_unexpectedly_empty() -> None:
    assert add_set([]) == [10]


def test_remove_last_set() -> None:
    assert remove_set([10, 9]) == [10]


def test_last_set_cannot_be_removed() -> None:
    with pytest.raises(ConstructorError, match="хотя бы один"):
        remove_set([10])


def test_constructor_has_at_most_one_hundred_sets() -> None:
    with pytest.raises(ConstructorError, match="100"):
        add_set([10] * 100)
