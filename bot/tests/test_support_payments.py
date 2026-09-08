from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.handlers import support
from bot.app.keyboards.support import SupportAction, SupportActionValue
from bot.app.states.support import Support


class FakeMessage:
    def __init__(self, *, text: str | None = None) -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=42)
        self.answer = AsyncMock()
        self.answer_invoice = AsyncMock()


class FakeCallback:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.message = FakeMessage()
        self.answer = AsyncMock()


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(), key=StorageKey(bot_id=1, chat_id=2, user_id=42)
    )


@pytest.fixture(autouse=True)
def fake_aiogram_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(support, "Message", FakeMessage)
    monkeypatch.setattr(support, "CallbackQuery", FakeCallback)


@pytest.mark.asyncio
async def test_preset_amount_creates_stars_invoice(state: FSMContext) -> None:
    callback = FakeCallback()
    api = SimpleNamespace(
        create_support_invoice=AsyncMock(
            return_value=SimpleNamespace(payload="support:one-time", amount=25)
        )
    )
    await support.choose_preset_amount(
        callback,
        SupportAction(action=SupportActionValue.AMOUNT, amount=25),
        state,
        api,
    )
    api.create_support_invoice.assert_awaited_once_with(42, 25)
    kwargs = callback.message.answer_invoice.await_args.kwargs
    assert kwargs["currency"] == "XTR"
    assert kwargs["payload"] == "support:one-time"
    assert kwargs["prices"][0].amount == 25


@pytest.mark.asyncio
async def test_support_requires_terms_confirmation_before_amounts(state: FSMContext) -> None:
    callback = FakeCallback()
    await state.set_state(Support.confirming_terms)
    await support.confirm_support_terms(callback, state)
    assert await state.get_state() is None
    assert "Поддержать Repka" in callback.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_other_amount_requires_valid_integer(state: FSMContext) -> None:
    message = FakeMessage(text="10.5")
    api = SimpleNamespace(create_support_invoice=AsyncMock())
    await state.set_state(Support.entering_amount)
    await support.receive_other_amount(message, state, api)
    assert await state.get_state() == Support.entering_amount.state
    api.create_support_invoice.assert_not_awaited()


@pytest.mark.asyncio
async def test_pre_checkout_accepts_only_backend_verified_invoice() -> None:
    query = SimpleNamespace(
        id="checkout", from_user=SimpleNamespace(id=42), invoice_payload="support:ok",
        total_amount=10, currency="XTR"
    )
    bot = SimpleNamespace(answer_pre_checkout_query=AsyncMock())
    api = SimpleNamespace(check_support_payment=AsyncMock(return_value=True))
    await support.support_pre_checkout(query, bot, api)
    api.check_support_payment.assert_awaited_once_with(42, "support:ok", 10, "XTR")
    bot.answer_pre_checkout_query.assert_awaited_once_with("checkout", ok=True, error_message=None)


@pytest.mark.asyncio
async def test_successful_payment_thanks_once_and_duplicate_is_silent() -> None:
    payment = SimpleNamespace(
        invoice_payload="support:ok", total_amount=10, currency="XTR",
        telegram_payment_charge_id="charge-42"
    )
    message = FakeMessage()
    message.successful_payment = payment
    api = SimpleNamespace(
        complete_support_payment=AsyncMock(
            side_effect=[
                SimpleNamespace(newly_completed=True),
                SimpleNamespace(newly_completed=False),
            ]
        )
    )
    bot = SimpleNamespace(send_message=AsyncMock())
    await support.successful_support_payment(message, api, bot, frozenset({99}))
    await support.successful_support_payment(message, api, bot, frozenset({99}))
    assert api.complete_support_payment.await_count == 2
    message.answer.assert_awaited_once()
    bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_payment_support_points_to_direct_contact(state: FSMContext) -> None:
    message = FakeMessage()
    await support.payment_support_command(message, state)
    assert await state.get_state() is None
    assert "@vedmitry" in message.answer.await_args.args[0]
