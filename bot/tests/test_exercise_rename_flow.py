from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import Exercise, ResourceConflictError
from bot.app.handlers import settings
from bot.app.keyboards.exercises import ExerciseDetailAction, ExerciseDetailActionValue
from bot.app.keyboards.settings import SettingsAction, SettingsActionValue
from bot.app.states.settings import RenameExercise


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
    monkeypatch.setattr(settings, "Message", FakeMessage)
    monkeypatch.setattr(settings, "CallbackQuery", FakeCallback)


@pytest.mark.asyncio
async def test_rename_flow_updates_selected_exercise_and_returns_to_management(
    state: FSMContext,
) -> None:
    callback = FakeCallback()
    selected = Exercise(id=7, name="Подтягивания")
    api = SimpleNamespace(
        list_exercises=AsyncMock(return_value=[selected]),
        rename_exercise=AsyncMock(return_value=Exercise(id=7, name="Турник")),
    )

    await settings.choose_managed_exercise(
        callback,
        SettingsAction(action=SettingsActionValue.RENAME_EXERCISE),
        state,
        api,
    )

    assert callback.message.edit_text.await_args.args[0].startswith(
        "✏️ Переименовать упражнение"
    )
    selection_markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    selection = ExerciseDetailAction.unpack(
        selection_markup.inline_keyboard[0][0].callback_data
    )
    assert selection.action is ExerciseDetailActionValue.RENAME
    assert selection.exercise_id == 7

    await settings.request_renamed_exercise_name(callback, selection, state, api)

    assert await state.get_state() == RenameExercise.waiting_for_name.state
    assert "Подтягивания" in callback.message.edit_text.await_args.args[0]

    message = FakeMessage()
    message.text = "  Турник  "
    await settings.rename_selected_exercise(message, state, api)

    api.rename_exercise.assert_awaited_once_with(42, 7, "Турник")
    assert await state.get_state() is None
    assert message.bot.edit_message_text.await_args.kwargs["text"] == (
        "✅ Упражнение переименовано: «Турник»"
    )


@pytest.mark.asyncio
async def test_rename_duplicate_keeps_name_input_open(state: FSMContext) -> None:
    await state.set_state(RenameExercise.waiting_for_name)
    await state.set_data(
        {
            "exercise_id": 7,
            "exercise_name": "Подтягивания",
            "ui_chat_id": 100,
            "ui_message_id": 200,
        }
    )
    message = FakeMessage()
    message.text = "Брусья"
    api = SimpleNamespace(rename_exercise=AsyncMock(side_effect=ResourceConflictError))

    await settings.rename_selected_exercise(message, state, api)

    assert await state.get_state() == RenameExercise.waiting_for_name.state
    assert "Упражнение с таким названием уже существует" in (
        message.bot.edit_message_text.await_args.kwargs["text"]
    )
