from enum import StrEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.texts import texts
from shared.support import SUPPORT_PRESET_AMOUNTS


class SupportActionValue(StrEnum):
    CONFIRM_TERMS = "confirm_terms"
    AMOUNT = "amount"
    OTHER = "other"


class SupportAction(CallbackData, prefix="support"):
    action: SupportActionValue
    amount: int = 0


def support_amount_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in SUPPORT_PRESET_AMOUNTS:
        builder.button(
            text=texts.support_amount_button(amount),
            callback_data=SupportAction(action=SupportActionValue.AMOUNT, amount=amount),
        )
    builder.button(
        text=texts.BUTTON_OTHER_AMOUNT,
        callback_data=SupportAction(action=SupportActionValue.OTHER),
    )
    builder.adjust(3, 1)
    return builder.as_markup()


def support_terms_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=texts.BUTTON_SUPPORT_CONTINUE,
        callback_data=SupportAction(action=SupportActionValue.CONFIRM_TERMS),
    )
    return builder.as_markup()
