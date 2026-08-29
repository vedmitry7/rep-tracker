from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.app.api.client import Exercise, ExerciseStats
from bot.app.handlers import exercises
from bot.app.keyboards.exercises import ExerciseDetailAction, ExerciseDetailActionValue
from bot.app.texts import reset_current_language, set_current_language


class FakeMessage:
    def __init__(self) -> None:
        self.answer = AsyncMock()


class FakeCallback:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.message = FakeMessage()
        self.answer = AsyncMock()


def stats() -> ExerciseStats:
    return ExerciseStats.empty(today=date(2026, 8, 29)).model_copy(
        update={"all_time_entries": 84, "total_reps": 3421}
    )


@pytest.fixture(autouse=True)
def patch_event_types(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(exercises, "Message", FakeMessage)
    token = set_current_language("en")
    yield
    reset_current_language(token)


@pytest.mark.asyncio
async def test_clear_history_preview_does_not_mutate() -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        list_exercises=AsyncMock(return_value=[Exercise(id=7, name="Pull-ups")]),
        get_exercise_stats=AsyncMock(return_value=stats()),
        clear_exercise_history=AsyncMock(),
    )

    await exercises.request_destructive_exercise_action(
        callback,
        ExerciseDetailAction(
            action=ExerciseDetailActionValue.CLEAR_HISTORY, exercise_id=7
        ),
        api,
    )

    api.clear_exercise_history.assert_not_awaited()
    assert "84 entries\n3,421 reps" in callback.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_clear_history_confirmation_calls_backend_and_refreshes() -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        list_exercises=AsyncMock(return_value=[Exercise(id=7, name="Pull-ups")]),
        clear_exercise_history=AsyncMock(),
        get_exercise_stats=AsyncMock(
            return_value=ExerciseStats.empty(today=date(2026, 8, 29))
        ),
    )

    await exercises.confirm_clear_history(
        callback,
        ExerciseDetailAction(
            action=ExerciseDetailActionValue.CONFIRM_CLEAR_HISTORY,
            exercise_id=7,
        ),
        api,
    )

    api.clear_exercise_history.assert_awaited_once_with(42, 7)
    assert "No entries yet" in callback.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_hard_delete_confirmation_returns_to_exercise_list() -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        permanently_delete_exercise=AsyncMock(),
        list_exercises=AsyncMock(return_value=[Exercise(id=8, name="Squats")]),
    )

    await exercises.confirm_hard_delete(
        callback,
        ExerciseDetailAction(
            action=ExerciseDetailActionValue.CONFIRM_HARD_DELETE,
            exercise_id=7,
        ),
        api,
    )

    api.permanently_delete_exercise.assert_awaited_once_with(42, 7)
    assert callback.message.answer.await_args.args[0] == "Your exercises:"
