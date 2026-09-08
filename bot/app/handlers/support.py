from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from bot.app.api.client import ApiError, RepTrackerApi
from bot.app.handlers.common import answer_api_error
from bot.app.keyboards.support import (
    SupportAction,
    SupportActionValue,
    support_amount_keyboard,
    support_terms_keyboard,
)
from bot.app.states.support import Support
from bot.app.support import SUPPORT_MAX_CUSTOM_AMOUNT, is_valid_support_amount
from bot.app.texts import texts
from bot.app.notifications import notify_administrators


router = Router(name=__name__)


@router.message(Command("support"))
async def support_command(message: Message, state: FSMContext) -> None:
    await state.set_state(Support.confirming_terms)
    await message.answer(
        texts.SUPPORT_TERMS_CONFIRMATION,
        reply_markup=support_terms_keyboard(),
    )


@router.message(Command("paysupport"))
async def payment_support_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.SUPPORT_PAYMENT_CONTACT)


@router.message(Command("terms"))
async def terms_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.SUPPORT_TERMS)


@router.callback_query(SupportAction.filter(F.action == SupportActionValue.OTHER))
async def request_other_amount(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Support.entering_amount)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(texts.support_enter_amount(SUPPORT_MAX_CUSTOM_AMOUNT))


@router.callback_query(
    Support.confirming_terms,
    SupportAction.filter(F.action == SupportActionValue.CONFIRM_TERMS),
)
async def confirm_support_terms(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            texts.SUPPORT_CHOOSE_AMOUNT,
            reply_markup=support_amount_keyboard(),
        )


@router.callback_query(SupportAction.filter(F.action == SupportActionValue.AMOUNT))
async def choose_preset_amount(
    callback: CallbackQuery,
    callback_data: SupportAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    if not is_valid_support_amount(callback_data.amount):
        await callback.answer(texts.support_invalid_amount(SUPPORT_MAX_CUSTOM_AMOUNT), show_alert=True)
        return
    await callback.answer()
    await _send_invoice(callback, callback_data.amount, api_client)


@router.message(Support.entering_amount, F.text)
async def receive_other_amount(
    message: Message, state: FSMContext, api_client: RepTrackerApi
) -> None:
    raw_amount = (message.text or "").strip()
    if not raw_amount.isascii() or not raw_amount.isdecimal():
        await message.answer(texts.support_invalid_amount(SUPPORT_MAX_CUSTOM_AMOUNT))
        return
    amount = int(raw_amount)
    if not is_valid_support_amount(amount):
        await message.answer(texts.support_invalid_amount(SUPPORT_MAX_CUSTOM_AMOUNT))
        return
    await state.clear()
    await _send_invoice(message, amount, api_client)


async def _send_invoice(
    event: Message | CallbackQuery, amount: int, api_client: RepTrackerApi
) -> None:
    user_id = event.from_user.id
    try:
        invoice = await api_client.create_support_invoice(user_id, amount)
    except ApiError as error:
        await answer_api_error(event, error)
        return
    message = event.message if isinstance(event, CallbackQuery) else event
    if not isinstance(message, Message):
        return
    await message.answer_invoice(
        title=texts.SUPPORT_INVOICE_TITLE,
        description=texts.SUPPORT_INVOICE_DESCRIPTION,
        payload=invoice.payload,
        currency="XTR",
        prices=[LabeledPrice(label=texts.SUPPORT_INVOICE_TITLE, amount=invoice.amount)],
    )


@router.pre_checkout_query()
async def support_pre_checkout(
    query: PreCheckoutQuery, bot: Bot, api_client: RepTrackerApi
) -> None:
    try:
        valid = await api_client.check_support_payment(
            query.from_user.id,
            query.invoice_payload,
            query.total_amount,
            query.currency,
        )
    except ApiError:
        valid = False
    await bot.answer_pre_checkout_query(
        query.id,
        ok=valid,
        error_message=None if valid else texts.SUPPORT_PAYMENT_UNAVAILABLE,
    )


@router.message(F.successful_payment)
async def successful_support_payment(
    message: Message,
    api_client: RepTrackerApi,
    bot: Bot,
    admin_telegram_ids: frozenset[int],
) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    payment = message.successful_payment
    try:
        result = await api_client.complete_support_payment(
            message.from_user.id,
            payment.invoice_payload,
            payment.total_amount,
            payment.currency,
            payment.telegram_payment_charge_id,
        )
    except ApiError:
        # Telegram has already charged the user. Keep the update retryable rather
        # than claiming success before its durable record exists.
        await message.answer(texts.SUPPORT_PAYMENT_PROCESSING)
        return
    if result.newly_completed:
        await message.answer(texts.support_thank_you(payment.total_amount))
        await notify_administrators(
            bot,
            admin_telegram_ids,
            "Voluntary Stars support received\n"
            f"Telegram user ID: {message.from_user.id}\n"
            f"Amount: {payment.total_amount} XTR\n"
            f"Charge ID: {payment.telegram_payment_charge_id}",
        )
