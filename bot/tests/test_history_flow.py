from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import Exercise, ExerciseEntry, ExerciseHistoryDay
from bot.app.handlers import history
from bot.app.keyboards.history import (
    HistoryDateChoice,
    HistoryDateChoiceValue,
    HistoryDayOpen,
    HistoryDeleteAction,
    HistoryDeleteValue,
    HistoryEditAction,
    HistoryEditActionValue,
    HistoryEntryAction,
    HistoryEntryActionValue,
    HistoryEntryOpen,
    delete_confirmation_keyboard,
    history_day_keyboard,
    history_days_keyboard,
)
from bot.app.states.history import EditHistoryEntry


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


class FakeMessage:
    def __init__(self) -> None:
        self.edit_text = AsyncMock()
        self.answer = AsyncMock()


class FakeCallback:
    def __init__(self, user_id: int = 42) -> None:
        self.from_user = SimpleNamespace(id=user_id)
        self.message = FakeMessage()
        self.answer = AsyncMock()


@pytest.fixture(autouse=True)
def fake_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(history, "CallbackQuery", FakeCallback)
    monkeypatch.setattr(history, "Message", FakeMessage)


def callback_values(markup: object) -> list[str]:
    return [
        button.callback_data
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.callback_data is not None
    ]


def test_history_days_keyboard_has_one_button_per_day() -> None:
    days = [
        ExerciseHistoryDay(date=date(2026, 8, 27), total_reps=74, entries_count=2),
        ExerciseHistoryDay(date=date(2026, 8, 25), total_reps=40, entries_count=1),
    ]
    markup = history_days_keyboard(7, days)

    assert [button.text for row in markup.inline_keyboard for button in row] == [
        "27.08 — 74",
        "25.08 — 40",
        "◀️ Назад",
    ]
    day_callbacks = [HistoryDayOpen.unpack(value) for value in callback_values(markup)[:2]]
    assert [(item.exercise_id, item.performed_on) for item in day_callbacks] == [
        (7, "2026-08-27"),
        (7, "2026-08-25"),
    ]


@pytest.mark.asyncio
async def test_history_screen_loads_latest_ten_days(state: FSMContext) -> None:
    days = [
        ExerciseHistoryDay(date=date(2026, 8, 27), total_reps=74, entries_count=2)
    ]
    api = SimpleNamespace(
        list_exercises=AsyncMock(
            return_value=[Exercise(id=7, name="Подтягивания")]
        ),
        get_exercise_history_days=AsyncMock(return_value=days),
    )
    callback = FakeCallback()

    await history.show_history_days(
        callback,
        SimpleNamespace(exercise_id=7),
        state,
        api,
    )

    api.get_exercise_history_days.assert_awaited_once_with(42, 7, limit=10)
    assert callback.message.edit_text.await_args.args[0] == (
        "📜 Подтягивания\n\nВыбери день:"
    )


def test_empty_history_has_clear_message() -> None:
    assert history.history_days_text(
        Exercise(id=7, name="Подтягивания"),
        [],
    ) == "📜 Подтягивания\n\nЗаписей пока нет."
@pytest.mark.parametrize("entry_count", [1, 2])
def test_day_screen_has_one_button_per_entry(entry_count: int) -> None:
    entries = [
        entry(15, [10, 10, 10, 10]),
        entry(16, [10, 9, 8, 7]),
    ][:entry_count]
    markup = history_day_keyboard(7, "2026-08-27", entries)
    entry_callbacks = [
        HistoryEntryOpen.unpack(value)
        for value in callback_values(markup)[:entry_count]
    ]

    assert [item.entry_id for item in entry_callbacks] == [item.id for item in entries]
    assert history.history_day_text(
        Exercise(id=7, name="Подтягивания"),
        date(2026, 8, 27),
        entries,
    ).endswith(f"Всего за день: {sum(sum(item.reps) for item in entries)}")


def test_delete_confirmation_has_confirm_and_cancel() -> None:
    markup = delete_confirmation_keyboard(entry(15, [10, 9, 8, 7]))
    actions = [
        HistoryDeleteAction.unpack(value).action for value in callback_values(markup)
    ]

    assert actions == [HistoryDeleteValue.CONFIRM, HistoryDeleteValue.CANCEL]


@pytest.mark.asyncio
async def test_edit_constructor_starts_with_current_entry_reps(
    state: FSMContext,
) -> None:
    api = day_api([entry(15, [10, 9, 8, 7])])
    callback = FakeCallback()

    await history.history_entry_action(
        callback,
        HistoryEntryAction(
            action=HistoryEntryActionValue.EDIT_REPS,
            exercise_id=7,
            entry_id=15,
            performed_on="2026-08-27",
        ),
        state,
        api,
    )

    assert await state.get_state() == EditHistoryEntry.editing_reps.state
    assert (await state.get_data())["reps"] == [10, 9, 8, 7]
    rendered = callback.message.edit_text.await_args.args[0]
    assert "1. 10\n2. 9\n3. 8\n4. 7" in rendered


@pytest.mark.asyncio
async def test_edit_reps_patches_same_entry_and_renders_updated_value(
    state: FSMContext,
) -> None:
    await set_edit_state(state, EditHistoryEntry.editing_reps, [11, 10, 9])
    updated = entry(15, [11, 10, 9])
    api = SimpleNamespace(update_exercise_entry=AsyncMock(return_value=updated))
    callback = FakeCallback()

    await history.edit_reps_action(
        callback,
        HistoryEditAction(action=HistoryEditActionValue.SAVE),
        state,
        api,
    )

    api.update_exercise_entry.assert_awaited_once_with(42, 15, reps=[11, 10, 9])
    assert await state.get_state() is None
    rendered = callback.message.edit_text.await_args.args[0]
    assert "11 • 10 • 9" in rendered
    assert "Всего: 30" in rendered


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("choice", "offset"),
    [
        (HistoryDateChoiceValue.TODAY, 0),
        (HistoryDateChoiceValue.YESTERDAY, 1),
    ],
)
async def test_change_date_today_and_yesterday_patch_performed_on(
    choice: HistoryDateChoiceValue,
    offset: int,
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await set_edit_state(state, EditHistoryEntry.choosing_date, [10])
    today = date(2026, 8, 27)
    monkeypatch.setattr(
        history,
        "days_ago",
        lambda value, *, today: today - timedelta(days=value),
    )
    selected = today - timedelta(days=offset)
    api = SimpleNamespace(
        update_exercise_entry=AsyncMock(return_value=entry(15, [10], selected))
    )
    callback = FakeCallback()

    await history.choose_entry_date(
        callback,
        HistoryDateChoice(choice=choice),
        state,
        api,
    )

    api.update_exercise_entry.assert_awaited_once_with(
        42,
        15,
        performed_on=selected,
    )
    assert selected.strftime("%d.%m.%Y") in callback.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_manual_date_reuses_parser_and_patches(
    state: FSMContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await set_edit_state(state, EditHistoryEntry.entering_date, [10])
    selected = date(2026, 8, 20)
    parser = Mock(return_value=selected)
    monkeypatch.setattr(history, "parse_result_date", parser)
    api = SimpleNamespace(
        update_exercise_entry=AsyncMock(return_value=entry(15, [10], selected))
    )
    message = FakeMessage()
    message.text = "20.08.2026"
    message.from_user = SimpleNamespace(id=42)

    await history.enter_entry_date(message, state, api)

    parser.assert_called_once_with("20.08.2026", today=date(2026, 8, 27))
    api.update_exercise_entry.assert_awaited_once_with(
        42,
        15,
        performed_on=selected,
    )
    assert "20.08.2026" in message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_delete_action_only_shows_confirmation(
    state: FSMContext,
) -> None:
    api = day_api([entry(15, [10, 9, 8, 7])])
    api.delete_exercise_entry = AsyncMock()
    callback = FakeCallback()

    await history.history_entry_action(
        callback,
        HistoryEntryAction(
            action=HistoryEntryActionValue.DELETE,
            exercise_id=7,
            entry_id=15,
            performed_on="2026-08-27",
        ),
        state,
        api,
    )

    api.delete_exercise_entry.assert_not_awaited()
    assert callback.message.edit_text.await_args.args[0] == (
        "Удалить запись?\n\n27.08.2026\n10 • 9 • 8 • 7"
    )


@pytest.mark.asyncio
async def test_delete_cancel_returns_to_entry_without_deleting() -> None:
    api = day_api([entry(15, [10])])
    api.delete_exercise_entry = AsyncMock()
    callback = FakeCallback()

    await history.delete_entry_action(
        callback,
        delete_action(HistoryDeleteValue.CANCEL),
        api,
    )

    api.delete_exercise_entry.assert_not_awaited()
    assert callback.message.edit_text.await_args.args[0].startswith("🏋️ Подтягивания")


@pytest.mark.asyncio
async def test_delete_returns_to_day_when_other_entries_remain() -> None:
    remaining = entry(16, [12])
    api = day_api([remaining])
    api.delete_exercise_entry = AsyncMock()
    callback = FakeCallback()

    await history.delete_entry_action(
        callback,
        delete_action(HistoryDeleteValue.CONFIRM),
        api,
    )

    api.delete_exercise_entry.assert_awaited_once_with(42, 15)
    assert "Всего за день: 12" in callback.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_delete_returns_to_history_when_day_becomes_empty() -> None:
    api = day_api([])
    api.delete_exercise_entry = AsyncMock()
    api.get_exercise_history_days = AsyncMock(return_value=[])
    callback = FakeCallback()

    await history.delete_entry_action(
        callback,
        delete_action(HistoryDeleteValue.CONFIRM),
        api,
    )

    api.get_exercise_history_days.assert_awaited_once_with(42, 7, limit=10)
    assert callback.message.edit_text.await_args.args[0] == (
        "📜 Подтягивания\n\nЗаписей пока нет."
    )


def entry(
    entry_id: int,
    reps: list[int],
    performed_on: date = date(2026, 8, 27),
) -> ExerciseEntry:
    return ExerciseEntry(
        id=entry_id,
        exercise_id=7,
        reps=reps,
        performed_on=performed_on,
    )


def day_api(entries: list[ExerciseEntry]) -> SimpleNamespace:
    return SimpleNamespace(
        list_exercises=AsyncMock(
            return_value=[Exercise(id=7, name="Подтягивания")]
        ),
        get_exercise_entries=AsyncMock(return_value=entries),
        get_user_settings=AsyncMock(
            return_value=SimpleNamespace(
                timezone="Europe/Moscow",
                today=date(2026, 8, 27),
            )
        ),
    )


def delete_action(action: HistoryDeleteValue) -> HistoryDeleteAction:
    return HistoryDeleteAction(
        action=action,
        exercise_id=7,
        entry_id=15,
        performed_on="2026-08-27",
    )


async def set_edit_state(
    state: FSMContext,
    target_state: object,
    reps: list[int],
) -> None:
    await state.set_state(target_state)  # type: ignore[arg-type]
    await state.set_data(
        history.HistoryEditContext(
            exercise_id=7,
            exercise_name="Подтягивания",
            entry_id=15,
            user_today=date(2026, 8, 27),
            performed_on=date(2026, 8, 27),
            reps=reps,
        ).as_fsm_data()
    )
