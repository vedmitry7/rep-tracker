from datetime import date, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.app.api.client import (
    ApiError,
    Exercise,
    ExerciseStats,
    RepTrackerApi,
    ResourceConflictError,
)
from bot.app.handlers.common import (
    answer_api_error,
    edit_or_answer,
    edit_stored_or_answer,
)
from bot.app.keyboards.exercises import (
    ExerciseAction,
    ExerciseActionValue,
    ExerciseDetailAction,
    ExerciseDetailActionValue,
    ExerciseOpen,
    exercise_name_back_keyboard,
    exercise_destructive_confirmation_keyboard,
    exercise_management_selection_keyboard,
    exercise_screen_keyboard,
    exercise_statistics_keyboard,
    exercises_list_keyboard,
)
from bot.app.keyboards.settings import exercise_management_keyboard
from bot.app.services.exercise_format import format_number, format_reps
from bot.app.services.date_format import format_user_date
from bot.app.states.exercise import CreateExercise
from bot.app.texts import texts


router = Router(name=__name__)
MAX_EXERCISE_NAME_LENGTH = 255


def exercise_screen_text(exercise: Exercise, stats: ExerciseStats) -> str:
    if stats.all_time_entries == 0 or stats.last_entry is None:
        return texts.exercise_empty(exercise.name)

    entry = stats.last_entry
    return texts.exercise_summary(
        name=exercise.name,
        last_reps=format_reps(entry.reps),
        last_date=_format_last_entry_date(entry.performed_on, stats.today),
        today_reps=format_number(stats.today_reps),
        last_7_days_reps=format_number(stats.last_7_days_reps),
        last_30_days_reps=format_number(stats.last_30_days_reps),
        total_reps=format_number(stats.total_reps),
    )


def stats_screen_text(exercise: Exercise, stats: ExerciseStats) -> str:
    return texts.statistics(
        name=exercise.name,
        today_reps=format_number(stats.today_reps),
        last_7_days_reps=format_number(stats.last_7_days_reps),
        last_30_days_reps=format_number(stats.last_30_days_reps),
        total_reps=format_number(stats.total_reps),
        active_days=format_number(stats.active_days),
        average_training_day=(
            format_number(round(stats.total_reps / stats.active_days))
            if stats.active_days
            else "—"
        ),
        best_day=(
            format_user_date(stats.best_day.date)
            if stats.best_day is not None
            else None
        ),
        best_day_reps=(
            format_number(stats.best_day.reps)
            if stats.best_day is not None
            else None
        ),
    )


async def show_exercise(
    message: Message,
    exercise: Exercise,
    stats: ExerciseStats,
    *,
    edit: bool = False,
) -> None:
    text = exercise_screen_text(exercise, stats)
    markup = exercise_screen_keyboard(
        exercise.id,
    )
    if edit:
        await edit_or_answer(message, text, markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(ExerciseAction.filter(F.action == ExerciseActionValue.ADD))
async def request_exercise_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await state.set_state(CreateExercise.waiting_for_name)
    if isinstance(callback.message, Message):
        await state.update_data(
            ui_chat_id=callback.message.chat.id,
            ui_message_id=callback.message.message_id,
        )
    await callback.answer()
    if isinstance(callback.message, Message):
        await edit_or_answer(
            callback.message,
            texts.REQUEST_EXERCISE_NAME,
            exercise_name_back_keyboard(),
        )


@router.message(CreateExercise.waiting_for_name)
async def create_custom_exercise(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    data = await state.get_data()
    chat_id = data.get("ui_chat_id")
    message_id = data.get("ui_message_id")
    stored_chat_id = chat_id if isinstance(chat_id, int) else None
    stored_message_id = message_id if isinstance(message_id, int) else None
    name = (message.text or "").strip()
    if not name:
        await edit_stored_or_answer(
            message,
            f"{texts.EMPTY_EXERCISE_NAME}\n\n{texts.REQUEST_EXERCISE_NAME}",
            exercise_name_back_keyboard(),
            chat_id=stored_chat_id,
            message_id=stored_message_id,
        )
        return
    if len(name) > MAX_EXERCISE_NAME_LENGTH:
        await edit_stored_or_answer(
            message,
            (
                f"{texts.exercise_name_too_long(MAX_EXERCISE_NAME_LENGTH)}"
                f"\n\n{texts.REQUEST_EXERCISE_NAME}"
            ),
            exercise_name_back_keyboard(),
            chat_id=stored_chat_id,
            message_id=stored_message_id,
        )
        return
    if message.from_user is None:
        return

    try:
        exercise = await api_client.create_exercise(message.from_user.id, name)
        stats = await api_client.get_exercise_stats(message.from_user.id, exercise.id)
    except ResourceConflictError:
        await edit_stored_or_answer(
            message,
            f"{texts.DUPLICATE_EXERCISE_NAME}\n\n{texts.REQUEST_EXERCISE_NAME}",
            exercise_name_back_keyboard(),
            chat_id=stored_chat_id,
            message_id=stored_message_id,
        )
        return
    except ApiError as error:
        await answer_api_error(message, error)
        return

    await state.clear()
    await edit_stored_or_answer(
        message,
        exercise_screen_text(exercise, stats),
        exercise_screen_keyboard(
            exercise.id,
        ),
        chat_id=stored_chat_id,
        message_id=stored_message_id,
    )


@router.callback_query(ExerciseAction.filter(F.action == ExerciseActionValue.LIST))
async def list_exercises(
    callback: CallbackQuery,
    api_client: RepTrackerApi,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()
    try:
        exercises = await api_client.list_exercises(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    if exercises:
        await edit_or_answer(
            callback.message,
            texts.EXERCISES_TITLE,
            exercises_list_keyboard(exercises),
        )
    else:
        await edit_or_answer(
            callback.message,
            texts.NO_EXERCISES,
            exercises_list_keyboard([]),
        )


@router.callback_query(ExerciseOpen.filter())
async def open_exercise(
    callback: CallbackQuery,
    callback_data: ExerciseOpen,
    api_client: RepTrackerApi,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()
    try:
        exercise = await _find_exercise(
            api_client,
            callback.from_user.id,
            callback_data.exercise_id,
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        stats = await api_client.get_exercise_stats(callback.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer()
    if isinstance(callback.message, Message):
        await show_exercise(callback.message, exercise, stats, edit=True)


@router.callback_query(
    ExerciseDetailAction.filter(F.action == ExerciseDetailActionValue.STATISTICS)
)
async def show_statistics(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    api_client: RepTrackerApi,
    state: FSMContext | None = None,
) -> None:
    if state is not None:
        await state.clear()
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        stats = await api_client.get_exercise_stats(callback.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await api_client.track_event_safely(callback.from_user.id, "stats_opened")
    await callback.answer()
    if isinstance(callback.message, Message):
        await edit_or_answer(
            callback.message,
            stats_screen_text(exercise, stats),
            exercise_statistics_keyboard(
                exercise.id,
                weekly_report_enabled=exercise.weekly_report_enabled,
            ),
        )


@router.callback_query(
    ExerciseDetailAction.filter(
        F.action == ExerciseDetailActionValue.TOGGLE_WEEKLY_REPORT
    )
)
async def toggle_weekly_report(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        updated = await api_client.set_exercise_weekly_report_enabled(
            callback.from_user.id,
            exercise.id,
            not exercise.weekly_report_enabled,
        )
        stats = await api_client.get_exercise_stats(callback.from_user.id, updated.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer(texts.weekly_report_changed(updated.weekly_report_enabled))
    if isinstance(callback.message, Message):
        await edit_or_answer(
            callback.message,
            stats_screen_text(updated, stats),
            exercise_statistics_keyboard(
                updated.id,
                weekly_report_enabled=updated.weekly_report_enabled,
            ),
        )


@router.callback_query(
    ExerciseDetailAction.filter(
        F.action.in_(
            {
                ExerciseDetailActionValue.CLEAR_HISTORY,
                ExerciseDetailActionValue.HARD_DELETE,
            }
        )
    )
)
async def request_destructive_exercise_action(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        stats = await api_client.get_exercise_stats(callback.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    if callback_data.action is ExerciseDetailActionValue.CLEAR_HISTORY:
        if stats.all_time_entries == 0:
            try:
                exercises = await api_client.list_exercises(callback.from_user.id)
            except ApiError as error:
                await answer_api_error(callback, error)
                return
            await callback.answer()
            if isinstance(callback.message, Message):
                try:
                    await callback.message.delete()
                except TelegramBadRequest:
                    pass
                await callback.message.answer(
                    texts.clear_history_not_needed(exercise.name)
                )
                await callback.message.answer(
                    texts.CLEAR_HISTORY_CHOOSE_EXERCISE,
                    reply_markup=exercise_management_selection_keyboard(
                        exercises,
                        operation=ExerciseDetailActionValue.CLEAR_HISTORY,
                    ),
                )
            return
        text = texts.clear_history_confirmation(
            exercise.name,
            format_number(stats.all_time_entries),
            format_number(stats.total_reps),
        )
        operation = "clear_history"
    else:
        text = texts.hard_delete_confirmation(
            exercise.name,
            format_number(stats.all_time_entries),
            format_number(stats.total_reps),
        )
        operation = "hard_delete"
    await callback.answer()
    if isinstance(callback.message, Message):
        await edit_or_answer(
            callback.message,
            text,
            exercise_destructive_confirmation_keyboard(
                exercise.id, operation=operation
            ),
        )


@router.callback_query(
    ExerciseDetailAction.filter(
        F.action == ExerciseDetailActionValue.CONFIRM_CLEAR_HISTORY
    )
)
async def confirm_clear_history(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        stats = await api_client.get_exercise_stats(callback.from_user.id, exercise.id)
        if stats.all_time_entries == 0:
            await callback.answer()
            if isinstance(callback.message, Message):
                await edit_or_answer(
                    callback.message,
                    texts.clear_history_not_needed(exercise.name),
                    exercise_management_keyboard(),
                )
            return
        await api_client.clear_exercise_history(callback.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    await callback.answer()
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            texts.history_cleared(
                exercise.name,
                format_number(stats.all_time_entries),
                format_number(stats.total_reps),
            )
        )
        await callback.message.answer(
            texts.EXERCISE_MANAGEMENT,
            reply_markup=exercise_management_keyboard(),
        )


@router.callback_query(
    ExerciseDetailAction.filter(
        F.action == ExerciseDetailActionValue.CONFIRM_HARD_DELETE
    )
)
async def confirm_hard_delete(
    callback: CallbackQuery,
    callback_data: ExerciseDetailAction,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercise = await _find_exercise(
            api_client, callback.from_user.id, callback_data.exercise_id
        )
        if exercise is None:
            await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
            return
        await api_client.permanently_delete_exercise(
            callback.from_user.id, callback_data.exercise_id
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    await callback.answer()
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            texts.exercise_permanently_deleted(exercise.name)
        )
        await callback.message.answer(
            texts.EXERCISE_MANAGEMENT,
            reply_markup=exercise_management_keyboard(),
        )


async def _find_exercise(
    api_client: RepTrackerApi,
    telegram_user_id: int,
    exercise_id: int,
) -> Exercise | None:
    exercises = await api_client.list_exercises(telegram_user_id)
    return next((item for item in exercises if item.id == exercise_id), None)


def _format_last_entry_date(performed_on: date, today: date) -> str:
    if performed_on == today:
        return texts.TODAY
    if performed_on == today - timedelta(days=1):
        return texts.YESTERDAY
    return format_user_date(performed_on)
