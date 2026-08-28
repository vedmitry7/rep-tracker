from enum import StrEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.texts import texts


class ResultScreen(StrEnum):
    INPUT = "input"
    CONSTRUCTOR = "constructor"


class ResultActionValue(StrEnum):
    START = "start"
    OPEN_CONSTRUCTOR = "constructor"
    CANCEL = "cancel"


class ResultAction(CallbackData, prefix="result"):
    action: ResultActionValue
    exercise_id: int


class OpenDatePicker(CallbackData, prefix="result_date"):
    return_to: ResultScreen


class DateChoiceValue(StrEnum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    DAY_BEFORE_YESTERDAY = "day_before"
    MANUAL = "manual"
    BACK = "back"


class DateChoice(CallbackData, prefix="date_choice"):
    choice: DateChoiceValue


class RepetitionActionValue(StrEnum):
    DECREMENT = "decrement"
    VALUE = "value"
    INCREMENT = "increment"


class RepetitionAction(CallbackData, prefix="result_rep"):
    action: RepetitionActionValue
    index: int


class ConstructorActionValue(StrEnum):
    ADD_SET = "add_set"
    REMOVE_SET = "remove_set"
    SAVE = "save"
    BACK = "back"


class ConstructorAction(CallbackData, prefix="result_builder"):
    action: ConstructorActionValue


def result_input_keyboard(exercise_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_CONSTRUCTOR,
        callback_data=ResultAction(
            action=ResultActionValue.OPEN_CONSTRUCTOR,
            exercise_id=exercise_id,
        ),
    )
    builder.button(
        text=texts.BUTTON_CHANGE_DATE,
        callback_data=OpenDatePicker(return_to=ResultScreen.INPUT),
    )
    builder.button(
        text=texts.BUTTON_CANCEL,
        callback_data=ResultAction(
            action=ResultActionValue.CANCEL,
            exercise_id=exercise_id,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def date_picker_keyboard(exercise_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, choice in (
        (texts.TODAY, DateChoiceValue.TODAY),
        (texts.YESTERDAY, DateChoiceValue.YESTERDAY),
        (texts.DAY_BEFORE_YESTERDAY, DateChoiceValue.DAY_BEFORE_YESTERDAY),
        (texts.BUTTON_ENTER_DATE, DateChoiceValue.MANUAL),
        (texts.BUTTON_BACK_ARROW, DateChoiceValue.BACK),
    ):
        builder.button(text=text, callback_data=DateChoice(choice=choice))
    builder.button(
        text=texts.BUTTON_CANCEL,
        callback_data=ResultAction(
            action=ResultActionValue.CANCEL,
            exercise_id=exercise_id,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def manual_date_keyboard(exercise_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_BACK_ARROW,
        callback_data=DateChoice(choice=DateChoiceValue.BACK),
    )
    builder.button(
        text=texts.BUTTON_CANCEL,
        callback_data=ResultAction(
            action=ResultActionValue.CANCEL,
            exercise_id=exercise_id,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def constructor_keyboard(
    exercise_id: int,
    repetitions: list[int],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, value in enumerate(repetitions):
        builder.row(
            _callback_button(
                "−",
                RepetitionActionValue.DECREMENT,
                index,
            ),
            _callback_button(
                str(value),
                RepetitionActionValue.VALUE,
                index,
            ),
            _callback_button(
                "+",
                RepetitionActionValue.INCREMENT,
                index,
            ),
        )
    builder.row(
        _constructor_button(texts.BUTTON_REMOVE_SET, ConstructorActionValue.REMOVE_SET),
        _constructor_button(texts.BUTTON_ADD_SET, ConstructorActionValue.ADD_SET),
    )
    builder.row(_constructor_button(texts.BUTTON_ADD, ConstructorActionValue.SAVE))
    builder.row(
        _date_button(texts.BUTTON_DATE, ResultScreen.CONSTRUCTOR),
        _constructor_button(texts.BUTTON_BACK_ARROW, ConstructorActionValue.BACK),
    )
    builder.row(
        _result_button(texts.BUTTON_CANCEL, ResultActionValue.CANCEL, exercise_id)
    )
    return builder.as_markup()


def _callback_button(
    text: str,
    action: RepetitionActionValue,
    index: int,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=RepetitionAction(action=action, index=index).pack(),
    )


def _constructor_button(
    text: str,
    action: ConstructorActionValue,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=ConstructorAction(action=action).pack(),
    )


def _date_button(text: str, return_to: ResultScreen) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=OpenDatePicker(return_to=return_to).pack(),
    )


def _result_button(
    text: str,
    action: ResultActionValue,
    exercise_id: int,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=ResultAction(
            action=action,
            exercise_id=exercise_id,
        ).pack(),
    )
