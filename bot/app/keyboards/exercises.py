from enum import StrEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.api.client import Exercise
from bot.app.keyboards.results import ResultAction, ResultActionValue
from bot.app.keyboards.settings import SettingsAction, SettingsActionValue
from bot.app.texts import texts


class ExerciseActionValue(StrEnum):
    ADD = "add"
    CUSTOM = "custom"
    LIST = "list"


class ExerciseAction(CallbackData, prefix="exercise_action"):
    action: ExerciseActionValue


class ExercisePreset(CallbackData, prefix="exercise_preset"):
    name: str


class ExerciseOpen(CallbackData, prefix="exercise_open"):
    exercise_id: int


class ExerciseDetailActionValue(StrEnum):
    STATISTICS = "statistics"
    HISTORY = "history"
    CLEAR_HISTORY = "clear_history"
    CONFIRM_CLEAR_HISTORY = "confirm_clear_history"
    HARD_DELETE = "hard_delete"
    CONFIRM_HARD_DELETE = "confirm_hard_delete"


class ExerciseDetailAction(CallbackData, prefix="exercise_detail"):
    action: ExerciseDetailActionValue
    exercise_id: int


def add_exercise_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_ADD_EXERCISE,
        callback_data=ExerciseAction(action=ExerciseActionValue.ADD),
    )
    builder.button(
        text=texts.BUTTON_SETTINGS,
        callback_data=SettingsAction(action=SettingsActionValue.OPEN),
    )
    builder.adjust(1)
    return builder.as_markup()


def exercise_presets_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in texts.EXERCISE_PRESETS:
        builder.button(text=name, callback_data=ExercisePreset(name=name))
    builder.button(
        text=texts.BUTTON_CUSTOM_EXERCISE,
        callback_data=ExerciseAction(action=ExerciseActionValue.CUSTOM),
    )
    builder.adjust(1)
    return builder.as_markup()


def exercise_screen_keyboard(exercise_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_ADD_RESULT,
        callback_data=ResultAction(
            action=ResultActionValue.START,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_STATISTICS,
        callback_data=ExerciseDetailAction(
            action=ExerciseDetailActionValue.STATISTICS,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_HISTORY,
        callback_data=ExerciseDetailAction(
            action=ExerciseDetailActionValue.HISTORY,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_CLEAR_HISTORY,
        callback_data=ExerciseDetailAction(
            action=ExerciseDetailActionValue.CLEAR_HISTORY,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_DELETE_EXERCISE,
        callback_data=ExerciseDetailAction(
            action=ExerciseDetailActionValue.HARD_DELETE,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_EXERCISES,
        callback_data=ExerciseAction(action=ExerciseActionValue.LIST),
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def exercise_destructive_confirmation_keyboard(
    exercise_id: int,
    *,
    operation: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if operation == "clear_history":
        text = texts.BUTTON_CONFIRM_CLEAR_HISTORY
        action = ExerciseDetailActionValue.CONFIRM_CLEAR_HISTORY
    else:
        text = texts.BUTTON_DELETE_PERMANENTLY
        action = ExerciseDetailActionValue.CONFIRM_HARD_DELETE
    builder.button(
        text=text,
        callback_data=ExerciseDetailAction(action=action, exercise_id=exercise_id),
    )
    builder.button(
        text=texts.BUTTON_CANCEL_PLAIN,
        callback_data=ExerciseOpen(exercise_id=exercise_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def exercise_back_keyboard(exercise_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_BACK_ARROW,
        callback_data=ExerciseOpen(exercise_id=exercise_id),
    )
    return builder.as_markup()


def exercises_list_keyboard(exercises: list[Exercise]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for exercise in exercises:
        builder.button(
            text=exercise.name,
            callback_data=ExerciseOpen(exercise_id=exercise.id),
        )
    builder.button(
        text=texts.BUTTON_ADD_EXERCISE,
        callback_data=ExerciseAction(action=ExerciseActionValue.ADD),
    )
    builder.button(
        text=texts.BUTTON_SETTINGS,
        callback_data=SettingsAction(action=SettingsActionValue.OPEN),
    )
    builder.adjust(1)
    return builder.as_markup()
