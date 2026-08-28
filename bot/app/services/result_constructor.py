from bot.app.services.result_parser import MAX_REPETITIONS, MAX_SETS
from bot.app.texts import texts


class ConstructorError(ValueError):
    """The requested constructor change violates result limits."""


def initial_repetitions(repetitions: list[int] | None = None) -> list[int]:
    return list(repetitions) if repetitions else [10]


def change_repetition(
    repetitions: list[int],
    index: int,
    delta: int,
) -> list[int]:
    if not 0 <= index < len(repetitions):
        raise ConstructorError(texts.SET_NOT_FOUND)
    changed = list(repetitions)
    changed[index] = min(
        MAX_REPETITIONS,
        max(1, changed[index] + delta),
    )
    return changed


def add_set(repetitions: list[int]) -> list[int]:
    if len(repetitions) >= MAX_SETS:
        raise ConstructorError(texts.too_many_sets(MAX_SETS))
    return [*repetitions, repetitions[-1] if repetitions else 10]


def remove_set(repetitions: list[int]) -> list[int]:
    if len(repetitions) <= 1:
        raise ConstructorError(texts.LAST_SET_REQUIRED)
    return repetitions[:-1]
