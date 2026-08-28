from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.app.api.client import ApiError, Exercise, ExerciseStats, RepTrackerApi
from bot.app.handlers.common import answer_api_error
from bot.app.keyboards.exercises import (
    ExerciseAction,
    ExerciseActionValue,
    ExerciseDetailAction,
    ExerciseDetailActionValue,
    ExerciseOpen,
    ExercisePreset,
    exercise_back_keyboard,
    exercise_presets_keyboard,
    exercise_screen_keyboard,
    exercises_list_keyboard,
)
from bot.app.services.exercise_format import format_number, format_reps
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
        entries=format_number(stats.all_time_entries),
        best_day=(
            stats.best_day.date.strftime("%d.%m.%Y")
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
) -> None:
    await message.answer(
        exercise_screen_text(exercise, stats),
        reply_markup=exercise_screen_keyboard(exercise.id),
    )


@router.callback_query(ExerciseAction.filter(F.action == ExerciseActionValue.ADD))
async def choose_exercise(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            texts.CHOOSE_EXERCISE,
            reply_markup=exercise_presets_keyboard(),
        )


@router.callback_query(ExercisePreset.filter())
async def create_preset_exercise(
    callback: CallbackQuery,
    callback_data: ExercisePreset,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercise = await api_client.create_exercise(
            callback.from_user.id,
            callback_data.name,
        )
        stats = await api_client.get_exercise_stats(callback.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer(texts.EXERCISE_ADDED)
    if isinstance(callback.message, Message):
        await show_exercise(callback.message, exercise, stats)


@router.callback_query(ExerciseAction.filter(F.action == ExerciseActionValue.CUSTOM))
async def request_custom_exercise_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(CreateExercise.waiting_for_name)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(texts.REQUEST_EXERCISE_NAME)


@router.message(CreateExercise.waiting_for_name)
async def create_custom_exercise(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer(texts.EMPTY_EXERCISE_NAME)
        return
    if len(name) > MAX_EXERCISE_NAME_LENGTH:
        await message.answer(
            texts.exercise_name_too_long(MAX_EXERCISE_NAME_LENGTH)
        )
        return
    if message.from_user is None:
        return

    try:
        exercise = await api_client.create_exercise(message.from_user.id, name)
        stats = await api_client.get_exercise_stats(message.from_user.id, exercise.id)
    except ApiError as error:
        await answer_api_error(message, error)
        return

    await state.clear()
    await show_exercise(message, exercise, stats)


@router.callback_query(ExerciseAction.filter(F.action == ExerciseActionValue.LIST))
async def list_exercises(
    callback: CallbackQuery,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercises = await api_client.list_exercises(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    if exercises:
        await callback.message.answer(
            texts.EXERCISES_TITLE,
            reply_markup=exercises_list_keyboard(exercises),
        )
    else:
        await callback.message.answer(
            texts.NO_EXERCISES,
            reply_markup=exercises_list_keyboard([]),
        )


@router.callback_query(ExerciseOpen.filter())
async def open_exercise(
    callback: CallbackQuery,
    callback_data: ExerciseOpen,
    api_client: RepTrackerApi,
) -> None:
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
        await show_exercise(callback.message, exercise, stats)


@router.callback_query(
    ExerciseDetailAction.filter(F.action == ExerciseDetailActionValue.STATISTICS)
)
async def show_statistics(
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

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            stats_screen_text(exercise, stats),
            reply_markup=exercise_back_keyboard(exercise.id),
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
    return performed_on.strftime("%d.%m.%Y")
