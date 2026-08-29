from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import (
    Exercise,
    ExerciseStats,
    ResourceConflictError,
)
from bot.app.handlers import exercises
from bot.app.keyboards.exercises import ExerciseAction, ExerciseActionValue
from bot.app.states.exercise import CreateExercise


class FakeMessage:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(id=100)
        self.message_id = 200
        self.edit_text = AsyncMock()
        self.answer = AsyncMock()
        self.bot = SimpleNamespace(edit_message_text=AsyncMock())
        self.from_user = SimpleNamespace(id=42)
        self.text: str | None = None


class FakeCallback:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.message = FakeMessage()
        self.answer = AsyncMock()


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


@pytest.fixture(autouse=True)
def patch_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(exercises, "Message", FakeMessage)


@pytest.mark.asyncio
async def test_custom_exercise_back_clears_state_and_returns_to_add_screen(
    state: FSMContext,
) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(list_exercises=AsyncMock(return_value=[]))

    await exercises.request_custom_exercise_name(callback, state)
    assert await state.get_state() == CreateExercise.waiting_for_name.state

    await exercises.choose_exercise(callback, state, api)

    assert await state.get_state() is None
    assert callback.message.edit_text.await_args.args[0] == "➕ Добавить упражнение"


@pytest.mark.asyncio
async def test_custom_exercise_success_clears_state_and_edits_stored_ui(
    state: FSMContext,
) -> None:
    await state.set_state(CreateExercise.waiting_for_name)
    await state.set_data({"ui_chat_id": 100, "ui_message_id": 200})
    message = FakeMessage()
    message.text = "  Планка  "
    api = SimpleNamespace(
        create_exercise=AsyncMock(return_value=Exercise(id=7, name="Планка")),
        get_exercise_stats=AsyncMock(
            return_value=ExerciseStats.empty(today=date(2026, 8, 29))
        ),
    )

    await exercises.create_custom_exercise(message, state, api)

    assert await state.get_state() is None
    message.bot.edit_message_text.assert_awaited_once()
    assert message.bot.edit_message_text.await_args.kwargs["message_id"] == 200
    assert message.bot.edit_message_text.await_args.kwargs["text"].startswith(
        "🏋️ Планка"
    )


@pytest.mark.asyncio
async def test_duplicate_custom_exercise_is_localized_and_keeps_input_state(
    state: FSMContext,
) -> None:
    await state.set_state(CreateExercise.waiting_for_name)
    await state.set_data({"ui_chat_id": 100, "ui_message_id": 200})
    message = FakeMessage()
    message.text = "Подтягивания"
    api = SimpleNamespace(
        create_exercise=AsyncMock(side_effect=ResourceConflictError),
    )

    await exercises.create_custom_exercise(message, state, api)

    assert await state.get_state() == CreateExercise.waiting_for_name.state
    rendered = message.bot.edit_message_text.await_args.kwargs["text"]
    assert "Упражнение с таким названием уже существует" in rendered


@pytest.mark.asyncio
async def test_home_to_exercise_navigation_edits_current_message(
    state: FSMContext,
) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        list_exercises=AsyncMock(return_value=[Exercise(id=7, name="Планка")]),
        get_exercise_stats=AsyncMock(
            return_value=ExerciseStats.empty(today=date(2026, 8, 29))
        ),
    )

    await exercises.open_exercise(
        callback,
        SimpleNamespace(exercise_id=7),
        api,
        state,
    )

    callback.message.edit_text.assert_awaited_once()
    callback.message.answer.assert_not_awaited()
