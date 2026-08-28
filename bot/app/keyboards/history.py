from enum import StrEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.api.client import ExerciseEntry, ExerciseHistoryDay
from bot.app.keyboards.exercises import (
    ExerciseDetailAction,
    ExerciseDetailActionValue,
    ExerciseOpen,
)
from bot.app.services.exercise_format import format_reps, format_number
from bot.app.texts import texts


class HistoryDayOpen(CallbackData, prefix="hd"):
    exercise_id: int
    performed_on: str


class HistoryEntryOpen(CallbackData, prefix="he"):
    exercise_id: int
    entry_id: int
    performed_on: str


class HistoryEntryActionValue(StrEnum):
    EDIT_REPS = "r"
    EDIT_DATE = "d"
    DELETE = "x"


class HistoryEntryAction(CallbackData, prefix="ha"):
    action: HistoryEntryActionValue
    exercise_id: int
    entry_id: int
    performed_on: str


class HistoryDeleteValue(StrEnum):
    CONFIRM = "y"
    CANCEL = "n"


class HistoryDeleteAction(CallbackData, prefix="hx"):
    action: HistoryDeleteValue
    exercise_id: int
    entry_id: int
    performed_on: str


class HistoryEditRepetitionValue(StrEnum):
    DECREMENT = "decrement"
    VALUE = "value"
    INCREMENT = "increment"


class HistoryEditRepetition(CallbackData, prefix="hr"):
    action: HistoryEditRepetitionValue
    index: int


class HistoryEditActionValue(StrEnum):
    ADD_SET = "add_set"
    REMOVE_SET = "remove_set"
    SAVE = "save"
    BACK = "back"


class HistoryEditAction(CallbackData, prefix="hed"):
    action: HistoryEditActionValue


class HistoryDateChoiceValue(StrEnum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    DAY_BEFORE_YESTERDAY = "day_before"
    MANUAL = "manual"
    BACK = "back"


class HistoryDateChoice(CallbackData, prefix="hdt"):
    choice: HistoryDateChoiceValue


def history_days_keyboard(
    exercise_id: int,
    days: list[ExerciseHistoryDay],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(
            text=f"{day.date.strftime('%d.%m')} — {format_number(day.total_reps)}",
            callback_data=HistoryDayOpen(
                exercise_id=exercise_id,
                performed_on=day.date.isoformat(),
            ),
        )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=ExerciseOpen(exercise_id=exercise_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def history_day_keyboard(
    exercise_id: int,
    performed_on: str,
    entries: list[ExerciseEntry],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for entry in entries:
        builder.button(
            text=format_reps(entry.reps),
            callback_data=HistoryEntryOpen(
                exercise_id=exercise_id,
                entry_id=entry.id,
                performed_on=performed_on,
            ),
        )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=ExerciseDetailAction(
            action=ExerciseDetailActionValue.HISTORY,
            exercise_id=exercise_id,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def history_entry_keyboard(entry: ExerciseEntry) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    common = {
        "exercise_id": entry.exercise_id,
        "entry_id": entry.id,
        "performed_on": entry.performed_on.isoformat(),
    }
    for text, action in (
        (texts.BUTTON_EDIT, HistoryEntryActionValue.EDIT_REPS),
        (texts.BUTTON_CHANGE_DATE, HistoryEntryActionValue.EDIT_DATE),
        (texts.BUTTON_DELETE, HistoryEntryActionValue.DELETE),
    ):
        builder.button(
            text=text,
            callback_data=HistoryEntryAction(action=action, **common),
        )
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=HistoryDayOpen(
            exercise_id=entry.exercise_id,
            performed_on=entry.performed_on.isoformat(),
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def delete_confirmation_keyboard(entry: ExerciseEntry) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    common = {
        "exercise_id": entry.exercise_id,
        "entry_id": entry.id,
        "performed_on": entry.performed_on.isoformat(),
    }
    builder.button(
        text=texts.BUTTON_CONFIRM_DELETE,
        callback_data=HistoryDeleteAction(
            action=HistoryDeleteValue.CONFIRM,
            **common,
        ),
    )
    builder.button(
        text=texts.BUTTON_CANCEL_PLAIN,
        callback_data=HistoryDeleteAction(
            action=HistoryDeleteValue.CANCEL,
            **common,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def history_constructor_keyboard(repetitions: list[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, value in enumerate(repetitions):
        builder.row(
            _repetition_button("−", HistoryEditRepetitionValue.DECREMENT, index),
            _repetition_button(str(value), HistoryEditRepetitionValue.VALUE, index),
            _repetition_button("+", HistoryEditRepetitionValue.INCREMENT, index),
        )
    builder.row(
        _edit_button(texts.BUTTON_REMOVE_SET, HistoryEditActionValue.REMOVE_SET),
        _edit_button(texts.BUTTON_ADD_SET, HistoryEditActionValue.ADD_SET),
    )
    builder.row(_edit_button(texts.BUTTON_SAVE, HistoryEditActionValue.SAVE))
    builder.row(_edit_button(texts.BUTTON_BACK, HistoryEditActionValue.BACK))
    return builder.as_markup()


def history_date_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, choice in (
        (texts.TODAY, HistoryDateChoiceValue.TODAY),
        (texts.YESTERDAY, HistoryDateChoiceValue.YESTERDAY),
        (texts.DAY_BEFORE_YESTERDAY, HistoryDateChoiceValue.DAY_BEFORE_YESTERDAY),
        (texts.BUTTON_ENTER_DATE, HistoryDateChoiceValue.MANUAL),
        (texts.BUTTON_BACK, HistoryDateChoiceValue.BACK),
    ):
        builder.button(
            text=text,
            callback_data=HistoryDateChoice(choice=choice),
        )
    builder.adjust(1)
    return builder.as_markup()


def history_manual_date_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_BACK,
        callback_data=HistoryDateChoice(choice=HistoryDateChoiceValue.BACK),
    )
    return builder.as_markup()


def _repetition_button(
    text: str,
    action: HistoryEditRepetitionValue,
    index: int,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=HistoryEditRepetition(action=action, index=index).pack(),
    )


def _edit_button(
    text: str,
    action: HistoryEditActionValue,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=HistoryEditAction(action=action).pack(),
    )
