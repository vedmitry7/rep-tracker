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
        text=texts.BUTTON_EXERCISES,
        callback_data=ExerciseAction(action=ExerciseActionValue.LIST),
    )
    builder.adjust(2, 2)
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
