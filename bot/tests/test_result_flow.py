from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import Exercise, ExerciseEntry
from bot.app.handlers import results
from bot.app.keyboards.results import (
    ConstructorAction,
    ConstructorActionValue,
    DateChoice,
    DateChoiceValue,
    ResultAction,
    ResultActionValue,
    ResultScreen,
)
from bot.app.states.result import AddResult


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


def callback(user_id: int = 3) -> SimpleNamespace:
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id),
        answer=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_result_flow_defaults_to_today(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = callback()
    api_client = SimpleNamespace(
        list_exercises=AsyncMock(
            return_value=[Exercise(id=7, name="Подтягивания")]
        ),
        get_user_settings=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Madrid",
                today=date(2026, 8, 28),
            )
        ),
    )
    render = AsyncMock()
    monkeypatch.setattr(results, "_render_result_input", render)

    await results.start_result_flow(
        event,
        ResultAction(action=ResultActionValue.START, exercise_id=7),
        state,
        api_client,
    )

    data = await state.get_data()
    assert await state.get_state() == AddResult.entering_result.state
    assert data == {
        "exercise_id": 7,
        "exercise_name": "Подтягивания",
        "user_today": date(2026, 8, 28),
        "performed_on": date(2026, 8, 28),
        "reps": [],
    }
    api_client.get_user_settings.assert_awaited_once_with(3)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("choice", "offset"),
    [
        (DateChoiceValue.TODAY, 0),
        (DateChoiceValue.YESTERDAY, 1),
        (DateChoiceValue.DAY_BEFORE_YESTERDAY, 2),
    ],
)
async def test_relative_date_selection(
    choice: DateChoiceValue,
    offset: int,
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await state.set_state(AddResult.choosing_date)
    await state.set_data(
        {
            "exercise_id": 7,
            "exercise_name": "Подтягивания",
            "user_today": date.today(),
            "performed_on": date.today(),
            "reps": [10, 9],
            "return_screen": ResultScreen.CONSTRUCTOR.value,
        }
    )
    return_to_screen = AsyncMock()
    monkeypatch.setattr(results, "_return_to_previous_screen", return_to_screen)

    await results.choose_date(
        callback(),
        DateChoice(choice=choice),
        state,
    )

    data = await state.get_data()
    assert data["performed_on"] == date.today() - timedelta(days=offset)
    assert data["reps"] == [10, 9]
    returned_context = return_to_screen.await_args.args[2]
    assert returned_context.reps == [10, 9]
    assert returned_context.performed_on == data["performed_on"]


@pytest.mark.asyncio
async def test_manual_date_preserves_reps_and_return_screen(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await state.set_state(AddResult.entering_date)
    await state.set_data(
        {
            "exercise_id": 7,
            "exercise_name": "Подтягивания",
            "user_today": date.today(),
            "performed_on": date.today(),
            "reps": [10, 9],
            "return_screen": ResultScreen.CONSTRUCTOR.value,
        }
    )
    return_to_screen = AsyncMock()
    monkeypatch.setattr(results, "_return_to_previous_screen", return_to_screen)
    message = SimpleNamespace(text="25.08.2026", answer=AsyncMock())

    await results.enter_date(message, state)

    data = await state.get_data()
    assert data["performed_on"] == date(2026, 8, 25)
    assert data["reps"] == [10, 9]
    assert data["return_screen"] == ResultScreen.CONSTRUCTOR.value


@pytest.mark.asyncio
async def test_invalid_manual_date_does_not_reset_fsm(state: FSMContext) -> None:
    original_data = {
        "exercise_id": 7,
        "exercise_name": "Подтягивания",
        "user_today": date.today(),
        "performed_on": date.today(),
        "reps": [10, 9],
        "return_screen": ResultScreen.CONSTRUCTOR.value,
    }
    await state.set_state(AddResult.entering_date)
    await state.set_data(original_data)
    message = SimpleNamespace(text="31.02.2026", answer=AsyncMock())

    await results.enter_date(message, state)

    assert await state.get_state() == AddResult.entering_date.state
    assert await state.get_data() == original_data
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_return_to_constructor_keeps_selected_date(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_date = date.today() - timedelta(days=2)
    context = results.ResultContext(
        7,
        "Подтягивания",
        date.today(),
        selected_date,
        [10, 9],
    )
    await state.set_data(
        {
            **context.as_fsm_data(),
            "return_screen": ResultScreen.CONSTRUCTOR.value,
        }
    )
    render = AsyncMock()
    monkeypatch.setattr(results, "_render_constructor", render)

    await results._return_to_previous_screen(callback(), state, context)

    assert await state.get_state() == AddResult.constructor.state
    assert render.await_args.args[1].performed_on == selected_date
    assert render.await_args.args[1].reps == [10, 9]


@pytest.mark.asyncio
async def test_constructor_save_uses_fsm_reps_and_date(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_date = date.today() - timedelta(days=2)
    await state.set_state(AddResult.constructor)
    await state.set_data(
        results.ResultContext(
            7,
            "Подтягивания",
            date.today(),
            selected_date,
            [10, 9, 8, 7],
        ).as_fsm_data()
    )
    api_client = SimpleNamespace(
        create_exercise_entry=AsyncMock(
            return_value=ExerciseEntry(
                id=20,
                exercise_id=7,
                reps=[10, 9, 8, 7],
                performed_on=selected_date,
            )
        )
    )
    render = AsyncMock()
    monkeypatch.setattr(results, "_render", render)

    await results.constructor_action(
        callback(user_id=42),
        ConstructorAction(action=ConstructorActionValue.SAVE),
        state,
        api_client,
    )

    api_client.create_exercise_entry.assert_awaited_once_with(
        42,
        7,
        [10, 9, 8, 7],
        performed_on=selected_date,
    )
    assert await state.get_state() is None
    assert await state.get_data() == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "expected_reps"),
    [
        ("10", [10]),
        ("4x10", [10, 10, 10, 10]),
        ("10 9 8 7", [10, 9, 8, 7]),
    ],
)
async def test_existing_text_input_still_saves(
    text: str,
    expected_reps: list[int],
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    performed_on = date.today() - timedelta(days=1)
    await state.set_state(AddResult.entering_result)
    await state.set_data(
        results.ResultContext(
            7,
            "Подтягивания",
            date.today(),
            performed_on,
            [],
        ).as_fsm_data()
    )
    api_client = SimpleNamespace()
    save = AsyncMock(return_value=True)
    monkeypatch.setattr(results, "_save_result", save)
    message = SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(),
    )

    await results.save_text_result(message, state, api_client)

    saved_context = save.await_args.args[4]
    assert saved_context.reps == expected_reps
    assert saved_context.performed_on == performed_on
    assert (await state.get_data())["reps"] == expected_reps
