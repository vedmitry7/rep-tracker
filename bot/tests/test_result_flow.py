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
from bot.app.services.date_format import manual_date_formats
from bot.app.states.result import AddResult


def copy_button(markup: object):
    return next(
        button
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.copy_text is not None
    )


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
        SimpleNamespace(),
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

    await results.enter_date(message, state, SimpleNamespace())

    data = await state.get_data()
    assert data["performed_on"] == date(2026, 8, 25)
    assert data["reps"] == [10, 9]
    assert data["return_screen"] == ResultScreen.CONSTRUCTOR.value


def manual_state(today: date, *, return_screen: ResultScreen) -> dict[str, object]:
    return {
        "exercise_id": 7,
        "exercise_name": "Подтягивания",
        "user_today": today,
        "performed_on": today,
        "reps": [10],
        "return_screen": return_screen.value,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "return_screen",
    [ResultScreen.INPUT, ResultScreen.CONSTRUCTOR],
)
async def test_manual_date_shows_today_in_all_formats_and_copy_button(
    return_screen: ResultScreen,
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    today = date(2026, 10, 17)
    await state.set_state(AddResult.choosing_date)
    await state.set_data(manual_state(today, return_screen=return_screen))
    api_client = SimpleNamespace(
        get_user_settings=AsyncMock(return_value=SimpleNamespace(today=today))
    )
    render = AsyncMock()
    monkeypatch.setattr(results, "_render", render)

    await results.choose_date(
        callback(),
        DateChoice(choice=DateChoiceValue.MANUAL),
        state,
        api_client,
    )

    short, full, iso = manual_date_formats(today)
    text = render.await_args.args[1]
    markup = render.await_args.args[2]
    assert short in text and full in text and iso in text
    button = copy_button(markup)
    assert button.text == f"📋 {short}"
    assert button.copy_text.text == short
    data = await state.get_data()
    assert data["return_screen"] == return_screen.value
    assert data["reps"] == [10]
    assert await state.get_state() == AddResult.entering_date.state


@pytest.mark.asyncio
async def test_manual_date_refreshes_today_after_local_midnight(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_today = date(2026, 10, 17)
    new_today = date(2026, 10, 18)
    await state.set_state(AddResult.choosing_date)
    await state.set_data(manual_state(old_today, return_screen=ResultScreen.INPUT))
    api_client = SimpleNamespace(
        get_user_settings=AsyncMock(return_value=SimpleNamespace(today=new_today))
    )
    render = AsyncMock()
    monkeypatch.setattr(results, "_render", render)

    await results.choose_date(
        callback(),
        DateChoice(choice=DateChoiceValue.MANUAL),
        state,
        api_client,
    )

    short, full, iso = manual_date_formats(new_today)
    text = render.await_args.args[1]
    assert short in text and full in text and iso in text
    assert (await state.get_data())["user_today"] == new_today
    assert copy_button(render.await_args.args[2]).copy_text.text == short


@pytest.mark.asyncio
async def test_invalid_manual_date_error_shows_current_day_examples(
    state: FSMContext,
) -> None:
    today = date(2026, 10, 17)
    original_data = manual_state(today, return_screen=ResultScreen.INPUT)
    await state.set_state(AddResult.entering_date)
    await state.set_data(original_data)
    message = SimpleNamespace(text="31.02.2026", answer=AsyncMock())

    await results.enter_date(message, state, SimpleNamespace())

    short, full, iso = manual_date_formats(today)
    text = message.answer.await_args.args[0]
    assert short in text and full in text and iso in text
    markup = message.answer.await_args.kwargs["reply_markup"]
    assert copy_button(markup).copy_text.text == short
    assert await state.get_state() == AddResult.entering_date.state
    assert await state.get_data() == original_data


@pytest.mark.asyncio
async def test_copied_short_date_is_accepted_by_parser(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    today = date(2026, 10, 17)
    await state.set_state(AddResult.entering_date)
    await state.set_data(manual_state(today, return_screen=ResultScreen.CONSTRUCTOR))
    return_to_screen = AsyncMock()
    monkeypatch.setattr(results, "_return_to_previous_screen", return_to_screen)
    message = SimpleNamespace(
        text="17.10",
        from_user=SimpleNamespace(id=3),
        answer=AsyncMock(),
    )
    api_client = SimpleNamespace(
        get_user_settings=AsyncMock(return_value=SimpleNamespace(today=today))
    )

    await results.enter_date(message, state, api_client)

    assert (await state.get_data())["performed_on"] == today


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

    await results.enter_date(message, state, SimpleNamespace())

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


@pytest.mark.asyncio
async def test_text_result_replaces_prompt_with_new_last_bot_message(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(results, "Message", SimpleNamespace)
    performed_on = date(2026, 9, 1)
    await state.set_state(AddResult.entering_result)
    await state.set_data(
        {
            **results.ResultContext(
                7,
                "Подтягивания",
                date(2026, 9, 1),
                performed_on,
                [],
            ).as_fsm_data(),
            "ui_chat_id": 100,
            "ui_message_id": 200,
        }
    )
    bot = SimpleNamespace(delete_message=AsyncMock())
    message = SimpleNamespace(
        text="10",
        from_user=SimpleNamespace(id=42),
        bot=bot,
        answer=AsyncMock(
            return_value=SimpleNamespace(
                chat=SimpleNamespace(id=100),
                message_id=202,
            )
        ),
    )
    api_client = SimpleNamespace(
        create_exercise_entry=AsyncMock(
            return_value=ExerciseEntry(
                id=20,
                exercise_id=7,
                reps=[10],
                performed_on=performed_on,
            )
        )
    )

    await results.save_text_result(message, state, api_client)

    bot.delete_message.assert_awaited_once_with(chat_id=100, message_id=200)
    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0].startswith("✅ Добавлено\n\nПодтягивания")
    assert await state.get_state() is None


@pytest.mark.asyncio
async def test_invalid_text_result_replaces_prompt_and_tracks_new_ui_message(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(results, "Message", SimpleNamespace)
    await state.set_state(AddResult.entering_result)
    await state.set_data(
        {
            **results.ResultContext(
                7,
                "Подтягивания",
                date(2026, 9, 1),
                date(2026, 9, 1),
                [],
            ).as_fsm_data(),
            "ui_chat_id": 100,
            "ui_message_id": 200,
        }
    )
    bot = SimpleNamespace(delete_message=AsyncMock())
    message = SimpleNamespace(
        text="abc",
        from_user=SimpleNamespace(id=42),
        bot=bot,
        answer=AsyncMock(
            return_value=SimpleNamespace(
                chat=SimpleNamespace(id=100),
                message_id=202,
            )
        ),
    )

    await results.save_text_result(message, state, SimpleNamespace())

    bot.delete_message.assert_awaited_once_with(chat_id=100, message_id=200)
    assert "Не понял формат" in message.answer.await_args.args[0]
    assert "Введи результат" in message.answer.await_args.args[0]
    assert await state.get_state() == AddResult.entering_result.state
    data = await state.get_data()
    assert (data["ui_chat_id"], data["ui_message_id"]) == (100, 202)
