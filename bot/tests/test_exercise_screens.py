from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.api.client import BestDay, Exercise, ExerciseEntry, ExerciseStats
from bot.app.handlers.exercises import (
    exercise_screen_text,
    stats_screen_text,
)
from bot.app.handlers import exercises as exercise_handlers
from bot.app.handlers.history import history_day_text
from bot.app.keyboards.exercises import ExerciseOpen
from bot.app.services.exercise_format import format_reps


@pytest.mark.parametrize(
    ("reps", "expected"),
    [
        ([10], "10"),
        ([10, 10, 10, 10], "4 × 10"),
        ([10, 9, 8, 7], "10 • 9 • 8 • 7"),
    ],
)
def test_format_reps(reps: list[int], expected: str) -> None:
    assert format_reps(reps) == expected


def test_empty_exercise_screen() -> None:
    text = exercise_screen_text(
        Exercise(id=7, name="Подтягивания"),
        ExerciseStats.empty(today=date(2026, 8, 27)),
    )

    assert text == "🏋️ Подтягивания\n\nЗаписей пока нет."


def test_empty_stats_screen() -> None:
    text = stats_screen_text(
        Exercise(id=7, name="Подтягивания"),
        ExerciseStats.empty(today=date(2026, 8, 27)),
    )

    assert text == (
        "📊 Подтягивания\n\n"
        "Сегодня: 0\n7 дней: 0\n30 дней: 0\nЗа всё время: 0\n\n"
        "Тренировочных дней: 0\nЗаписей: 0"
    )


def test_stats_screen() -> None:
    text = stats_screen_text(
        Exercise(id=7, name="Подтягивания"),
        _stats(),
    )

    assert text == (
        "📊 Подтягивания\n\n"
        "Сегодня: 34\n"
        "7 дней: 126\n"
        "30 дней: 483\n"
        "За всё время: 1 284\n\n"
        "Тренировочных дней: 22\n"
        "Записей: 35\n\n"
        "Лучший день:\n"
        "20.08.2026 — 85"
    )


def test_history_screen() -> None:
    exercise = Exercise(id=7, name="Подтягивания")
    entries = [
        _entry(1, [10, 9, 8, 7], date(2026, 8, 27)),
        _entry(2, [10, 10, 10, 10], date(2026, 8, 27)),
    ]

    assert history_day_text(exercise, date(2026, 8, 27), entries) == (
        "🏋️ Подтягивания\n"
        "27.08.2026\n"
        "Всего за день: 74"
    )


def test_exercise_screen_shows_last_entry_and_summary() -> None:
    text = exercise_screen_text(
        Exercise(id=7, name="Подтягивания"),
        _stats(),
    )

    assert text == (
        "🏋️ Подтягивания\n\n"
        "Последняя:\n10 • 9 • 8 • 7\nСегодня\n\n"
        "Сегодня: 34\n"
        "7 дней: 126\n"
        "30 дней: 483\n"
        "Всего: 1 284"
    )


@pytest.mark.asyncio
async def test_back_open_refreshes_the_correct_exercise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMessage:
        def __init__(self) -> None:
            self.answer = AsyncMock()

    message = FakeMessage()
    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=42),
        message=message,
        answer=AsyncMock(),
    )
    stats = _stats()
    api_client = SimpleNamespace(
        list_exercises=AsyncMock(
            return_value=[
                Exercise(id=7, name="Подтягивания"),
                Exercise(id=8, name="Отжимания"),
            ]
        ),
        get_exercise_stats=AsyncMock(return_value=stats),
    )
    monkeypatch.setattr(exercise_handlers, "Message", FakeMessage)

    await exercise_handlers.open_exercise(
        callback,
        ExerciseOpen(exercise_id=7),
        api_client,
    )

    api_client.get_exercise_stats.assert_awaited_once_with(42, 7)
    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0].startswith("🏋️ Подтягивания")

def _entry(entry_id: int, reps: list[int], performed_on: date) -> ExerciseEntry:
    return ExerciseEntry(
        id=entry_id,
        exercise_id=7,
        reps=reps,
        performed_on=performed_on,
    )


def _stats() -> ExerciseStats:
    return ExerciseStats(
        today=date.today(),
        total_reps=1284,
        today_reps=34,
        last_7_days_reps=126,
        last_30_days_reps=483,
        all_time_entries=35,
        active_days=22,
        best_day=BestDay(date=date(2026, 8, 20), reps=85),
        last_entry=_entry(1, [10, 9, 8, 7], date.today()),
    )
