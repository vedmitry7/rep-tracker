from dataclasses import dataclass, replace
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.app.api.client import (
    ApiError,
    Exercise,
    ExerciseEntry,
    ExerciseHistoryDay,
    RepTrackerApi,
)
from bot.app.handlers.common import (
    answer_api_error,
    edit_or_answer,
    edit_stored_or_answer,
)
from bot.app.handlers.exercises import _find_exercise
from bot.app.keyboards.exercises import ExerciseDetailAction, ExerciseDetailActionValue
from bot.app.keyboards.history import (
    HistoryDateChoice,
    HistoryDateChoiceValue,
    HistoryDayOpen,
    HistoryDeleteAction,
    HistoryDeleteValue,
    HistoryEditAction,
    HistoryEditActionValue,
    HistoryEditRepetition,
    HistoryEditRepetitionValue,
    HistoryEntryAction,
    HistoryEntryActionValue,
    HistoryEntryOpen,
    delete_confirmation_keyboard,
    history_constructor_keyboard,
    history_date_keyboard,
    history_day_keyboard,
    history_days_keyboard,
    history_entry_keyboard,
    history_manual_date_keyboard,
)
from bot.app.services.date_parser import DateParseError, days_ago, parse_result_date
from bot.app.services.exercise_format import format_number, format_reps
from bot.app.services.result_constructor import (
    ConstructorError,
    add_set,
    change_repetition,
    remove_set,
)
from bot.app.states.history import EditHistoryEntry
from bot.app.texts import texts


router = Router(name=__name__)


@dataclass(frozen=True)
class HistoryEditContext:
    exercise_id: int
    exercise_name: str
    entry_id: int
    user_today: date
    performed_on: date
    reps: list[int]

    @classmethod
    def from_data(cls, data: dict[str, object]) -> "HistoryEditContext | None":
        exercise_id = data.get("exercise_id")
        exercise_name = data.get("exercise_name")
        entry_id = data.get("entry_id")
        user_today = data.get("user_today")
        performed_on = data.get("performed_on")
        reps = data.get("reps")
        if (
            not isinstance(exercise_id, int)
            or not isinstance(exercise_name, str)
            or not isinstance(entry_id, int)
            or type(user_today) is not date
            or type(performed_on) is not date
            or not isinstance(reps, list)
            or not reps
            or not all(type(item) is int for item in reps)
        ):
            return None
        return cls(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            entry_id=entry_id,
            user_today=user_today,
            performed_on=performed_on,
            reps=list(reps),
        )

    @classmethod
    def from_entry(
        cls,
        exercise: Exercise,
        entry: ExerciseEntry,
        user_today: date,
    ) -> "HistoryEditContext":
        return cls(
            exercise_id=exercise.id,
            exercise_name=exercise.name,
            entry_id=entry.id,
            user_today=user_today,
            performed_on=entry.performed_on,
            reps=list(entry.reps),
        )

    def as_fsm_data(self) -> dict[str, object]:
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "entry_id": self.entry_id,
            "user_today": self.user_today,
            "performed_on": self.performed_on,
            "reps": list(self.reps),
        }


def history_days_text(exercise: Exercise, days: list[ExerciseHistoryDay]) -> str:
    return texts.history_days(exercise.name, has_entries=bool(days))


def history_day_text(
    exercise: Exercise,
    performed_on: date,
    entries: list[ExerciseEntry],
) -> str:
    total_reps = sum(sum(entry.reps) for entry in entries)
    return texts.history_day(
        exercise.name,
        performed_on.strftime("%d.%m.%Y"),
        format_number(total_reps),
    )


def history_entry_text(exercise: Exercise, entry: ExerciseEntry) -> str:
    return texts.history_entry(
        exercise.name,
        entry.performed_on.strftime("%d.%m.%Y"),
        format_reps(entry.reps),
        format_number(sum(entry.reps)),
    )


def delete_confirmation_text(entry: ExerciseEntry) -> str:
    return texts.delete_confirmation(
        entry.performed_on.strftime("%d.%m.%Y"),
        format_reps(entry.reps),
    )


@router.callback_query(
    ExerciseDetailAction.filter(F.action == ExerciseDetailActionValue.HISTORY)
)
async def show_history_days(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        days = await api_client.get_exercise_history_days(
            callback.from_user.id,
            exercise.id,
            limit=10,
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer()
    await _render(
        callback,
        history_days_text(exercise, days),
        history_days_keyboard(exercise.id, days),
    )


@router.callback_query(HistoryDayOpen.filter())
async def show_history_day(
    callback: CallbackQuery,
    callback_data: HistoryDayOpen,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    performed_on = await _callback_date(callback, callback_data.performed_on)
    if performed_on is None:
        return
    try:
        loaded = await _load_day(
            api_client,
            callback.from_user.id,
            callback_data.exercise_id,
            performed_on,
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    if loaded is None:
        await callback.answer(texts.DAY_OR_EXERCISE_NOT_FOUND, show_alert=True)
        return
    exercise, entries = loaded

    await callback.answer()
    await _render_day(callback, exercise, performed_on, entries)


@router.callback_query(HistoryEntryOpen.filter())
async def show_history_entry(
    callback: CallbackQuery,
    callback_data: HistoryEntryOpen,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    loaded = await _load_callback_entry(
        callback,
        api_client,
        callback_data.exercise_id,
        callback_data.entry_id,
        callback_data.performed_on,
    )
    if loaded is None:
        return
    exercise, entry = loaded

    await callback.answer()
    await _render_entry(callback, exercise, entry)


@router.callback_query(HistoryEntryAction.filter())
async def history_entry_action(
    callback: CallbackQuery,
    callback_data: HistoryEntryAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    loaded = await _load_callback_entry(
        callback,
        api_client,
        callback_data.exercise_id,
        callback_data.entry_id,
        callback_data.performed_on,
    )
    if loaded is None:
        return
    exercise, entry = loaded
    await state.clear()

    if callback_data.action == HistoryEntryActionValue.DELETE:
        await callback.answer()
        await _render(
            callback,
            delete_confirmation_text(entry),
            delete_confirmation_keyboard(entry),
        )
        return

    try:
        settings = await api_client.get_user_settings(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    context = HistoryEditContext.from_entry(exercise, entry, settings.today)
    await state.set_data(context.as_fsm_data())
    if isinstance(callback.message, Message):
        chat = getattr(callback.message, "chat", None)
        message_id = getattr(callback.message, "message_id", None)
        chat_id = getattr(chat, "id", None)
        if isinstance(chat_id, int) and isinstance(message_id, int):
            await state.update_data(
                ui_chat_id=chat_id,
                ui_message_id=message_id,
            )
    if callback_data.action == HistoryEntryActionValue.EDIT_REPS:
        await state.set_state(EditHistoryEntry.editing_reps)
        await callback.answer()
        await _render_constructor(callback, context)
    else:
        await state.set_state(EditHistoryEntry.choosing_date)
        await callback.answer()
        await _render(callback, texts.CHOOSE_NEW_DATE, history_date_keyboard())


@router.callback_query(HistoryEditRepetition.filter())
async def edit_repetition(
    callback: CallbackQuery,
    callback_data: HistoryEditRepetition,
    state: FSMContext,
) -> None:
    context = await _get_edit_context(
        callback,
        state,
        EditHistoryEntry.editing_reps.state,
    )
    if context is None:
        return
    if callback_data.action == HistoryEditRepetitionValue.VALUE:
        await callback.answer()
        return
    delta = 1 if callback_data.action == HistoryEditRepetitionValue.INCREMENT else -1
    try:
        reps = change_repetition(context.reps, callback_data.index, delta)
    except ConstructorError as error:
        await callback.answer(str(error), show_alert=True)
        return
    if reps == context.reps:
        await callback.answer(
            texts.MIN_REPETITIONS if delta < 0 else texts.MAX_REPETITIONS
        )
        return
    context = replace(context, reps=reps)
    await state.update_data(reps=list(reps))
    await callback.answer()
    await _render_constructor(callback, context)


@router.callback_query(HistoryEditAction.filter())
async def edit_reps_action(
    callback: CallbackQuery,
    callback_data: HistoryEditAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    context = await _get_edit_context(
        callback,
        state,
        EditHistoryEntry.editing_reps.state,
    )
    if context is None:
        return

    if callback_data.action == HistoryEditActionValue.SAVE:
        try:
            entry = await api_client.update_exercise_entry(
                callback.from_user.id,
                context.entry_id,
                reps=context.reps,
            )
        except ApiError as error:
            await answer_api_error(callback, error)
            return
        await state.clear()
        await callback.answer(texts.CHANGES_SAVED)
        await _render_entry(
            callback,
            Exercise(id=context.exercise_id, name=context.exercise_name),
            entry,
        )
        return

    if callback_data.action == HistoryEditActionValue.BACK:
        await state.clear()
        await callback.answer()
        await _reload_entry(callback, api_client, context)
        return

    try:
        reps = (
            add_set(context.reps)
            if callback_data.action == HistoryEditActionValue.ADD_SET
            else remove_set(context.reps)
        )
    except ConstructorError as error:
        await callback.answer(str(error))
        return
    context = replace(context, reps=reps)
    await state.update_data(reps=list(reps))
    await callback.answer()
    await _render_constructor(callback, context)


@router.callback_query(HistoryDateChoice.filter())
async def choose_entry_date(
    callback: CallbackQuery,
    callback_data: HistoryDateChoice,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    current_state = await state.get_state()
    if current_state not in {
        EditHistoryEntry.choosing_date.state,
        EditHistoryEntry.entering_date.state,
    }:
        await callback.answer(texts.SCREEN_EXPIRED)
        return
    context = await _get_edit_context(callback, state, current_state)
    if context is None:
        return

    if callback_data.choice == HistoryDateChoiceValue.MANUAL:
        await state.set_state(EditHistoryEntry.entering_date)
        await callback.answer()
        await _render(
            callback,
            texts.ENTER_DATE,
            history_manual_date_keyboard(),
        )
        return
    if callback_data.choice == HistoryDateChoiceValue.BACK:
        await callback.answer()
        if current_state == EditHistoryEntry.entering_date.state:
            await state.set_state(EditHistoryEntry.choosing_date)
            await _render(callback, texts.CHOOSE_NEW_DATE, history_date_keyboard())
        else:
            await state.clear()
            await _reload_entry(callback, api_client, context)
        return

    offsets = {
        HistoryDateChoiceValue.TODAY: 0,
        HistoryDateChoiceValue.YESTERDAY: 1,
        HistoryDateChoiceValue.DAY_BEFORE_YESTERDAY: 2,
    }
    await _save_entry_date(
        callback,
        state,
        api_client,
        callback.from_user.id,
        context,
        days_ago(offsets[callback_data.choice], today=context.user_today),
    )


@router.message(EditHistoryEntry.entering_date)
async def enter_entry_date(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    try:
        context = await _get_edit_context(
            message,
            state,
            EditHistoryEntry.entering_date.state,
        )
        if context is None:
            return
        performed_on = parse_result_date(
            message.text or "",
            today=context.user_today,
        )
    except DateParseError as error:
        await message.answer(str(error))
        return
    if message.from_user is None:
        return
    await _save_entry_date(
        message,
        state,
        api_client,
        message.from_user.id,
        context,
        performed_on,
    )


@router.callback_query(HistoryDeleteAction.filter())
async def delete_entry_action(
    callback: CallbackQuery,
    callback_data: HistoryDeleteAction,
    api_client: RepTrackerApi,
) -> None:
    performed_on = await _callback_date(callback, callback_data.performed_on)
    if performed_on is None:
        return
    if callback_data.action == HistoryDeleteValue.CANCEL:
        loaded = await _load_callback_entry(
            callback,
            api_client,
            callback_data.exercise_id,
            callback_data.entry_id,
            callback_data.performed_on,
        )
        if loaded is None:
            return
        exercise, entry = loaded
        await callback.answer()
        await _render_entry(callback, exercise, entry)
        return

    days: list[ExerciseHistoryDay] | None = None
    try:
        await api_client.delete_exercise_entry(
            callback.from_user.id,
            callback_data.entry_id,
        )
        exercise = await _find_exercise(
            api_client,
            callback.from_user.id,
            callback_data.exercise_id,
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        entries = await _get_day_entries(
            api_client,
            callback.from_user.id,
            exercise.id,
            performed_on,
        )
        if not entries:
            days = await api_client.get_exercise_history_days(
                callback.from_user.id,
                exercise.id,
                limit=10,
            )
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer(texts.ENTRY_DELETED)
    if entries:
        await _render_day(callback, exercise, performed_on, entries)
        return
    assert days is not None
    await _render(
        callback,
        history_days_text(exercise, days),
        history_days_keyboard(exercise.id, days),
    )


async def _save_entry_date(
    event: Message | CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
    telegram_user_id: int,
    context: HistoryEditContext,
    performed_on: date,
) -> None:
    state_data = await state.get_data()
    try:
        entry = await api_client.update_exercise_entry(
            telegram_user_id,
            context.entry_id,
            performed_on=performed_on,
        )
    except ApiError as error:
        await answer_api_error(event, error)
        return
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.answer(texts.DATE_CHANGED)
    exercise = Exercise(id=context.exercise_id, name=context.exercise_name)
    if isinstance(event, Message):
        chat_id = state_data.get("ui_chat_id")
        message_id = state_data.get("ui_message_id")
        await edit_stored_or_answer(
            event,
            history_entry_text(exercise, entry),
            history_entry_keyboard(entry),
            chat_id=chat_id if isinstance(chat_id, int) else None,
            message_id=message_id if isinstance(message_id, int) else None,
        )
    else:
        await _render_entry(event, exercise, entry)


async def _reload_entry(
    callback: CallbackQuery,
    api_client: RepTrackerApi,
    context: HistoryEditContext,
) -> None:
    try:
        entries = await _get_day_entries(
            api_client,
            callback.from_user.id,
            context.exercise_id,
            context.performed_on,
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    entry = next((item for item in entries if item.id == context.entry_id), None)
    if entry is None:
        await callback.answer(texts.ENTRY_NOT_FOUND, show_alert=True)
        return
    await _render_entry(
        callback,
        Exercise(id=context.exercise_id, name=context.exercise_name),
        entry,
    )


async def _load_callback_entry(
    callback: CallbackQuery,
    api_client: RepTrackerApi,
    exercise_id: int,
    entry_id: int,
    performed_on_value: str,
) -> tuple[Exercise, ExerciseEntry] | None:
    performed_on = await _callback_date(callback, performed_on_value)
    if performed_on is None:
        return None
    try:
        loaded = await _load_day(
            api_client,
            callback.from_user.id,
            exercise_id,
            performed_on,
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return None
    if loaded is None:
        await callback.answer(texts.DAY_OR_EXERCISE_NOT_FOUND, show_alert=True)
        return None
    exercise, entries = loaded
    entry = next((item for item in entries if item.id == entry_id), None)
    if entry is None:
        await callback.answer(texts.ENTRY_NOT_FOUND, show_alert=True)
        return None
    return exercise, entry


async def _load_day(
    api_client: RepTrackerApi,
    telegram_user_id: int,
    exercise_id: int,
    performed_on: date,
) -> tuple[Exercise, list[ExerciseEntry]] | None:
    exercise = await _find_exercise(api_client, telegram_user_id, exercise_id)
    if exercise is None:
        return None
    entries = await _get_day_entries(
        api_client,
        telegram_user_id,
        exercise_id,
        performed_on,
    )
    return exercise, entries


async def _get_day_entries(
    api_client: RepTrackerApi,
    telegram_user_id: int,
    exercise_id: int,
    performed_on: date,
) -> list[ExerciseEntry]:
    return await api_client.get_exercise_entries(
        telegram_user_id,
        exercise_id,
        limit=100,
        from_date=performed_on,
        to_date=performed_on,
    )


async def _callback_date(callback: CallbackQuery, value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return None


async def _get_edit_context(
    event: Message | CallbackQuery,
    state: FSMContext,
    expected_state: str,
) -> HistoryEditContext | None:
    if await state.get_state() != expected_state:
        if isinstance(event, CallbackQuery):
            await event.answer(texts.SCREEN_EXPIRED)
        else:
            await event.answer(texts.EDIT_FINISHED)
        return None
    context = HistoryEditContext.from_data(await state.get_data())
    if context is not None:
        return context
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.answer(texts.RESTORE_ENTRY_FAILED, show_alert=True)
    else:
        await event.answer(texts.RESTORE_ENTRY_FAILED)
    return None


async def _render_day(
    event: Message | CallbackQuery,
    exercise: Exercise,
    performed_on: date,
    entries: list[ExerciseEntry],
) -> None:
    await _render(
        event,
        history_day_text(exercise, performed_on, entries),
        history_day_keyboard(exercise.id, performed_on.isoformat(), entries),
    )


async def _render_entry(
    event: Message | CallbackQuery,
    exercise: Exercise,
    entry: ExerciseEntry,
) -> None:
    await _render(
        event,
        history_entry_text(exercise, entry),
        history_entry_keyboard(entry),
    )


async def _render_constructor(
    event: Message | CallbackQuery,
    context: HistoryEditContext,
) -> None:
    sets = "\n".join(
        f"{index}. {value}" for index, value in enumerate(context.reps, start=1)
    )
    await _render(
        event,
        texts.history_constructor(context.exercise_name, sets),
        history_constructor_keyboard(context.reps),
    )


async def _render(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await edit_or_answer(event.message, text, reply_markup)
        return
    await event.answer(text, reply_markup=reply_markup)
